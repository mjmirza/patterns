---
name: Composition over Inheritance
slug: composition-over-inheritance
family: 04-principles-and-laws
category: Principle
aliases: [Favor Object Composition over Class Inheritance, Has-A over Is-A, Delegation over Subclassing]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [strategy, decorator, bridge, template-method, dependency-injection]
incompatible_with: []
verified: 2026-08-02
---

# Composition over Inheritance

## 1. Name, aliases, and lineage

The canonical name is Composition over Inheritance, stated in the Gang of Four
catalog as the guideline "favor object composition over class inheritance."
Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides, *Design Patterns.
Elements of Reusable Object-Oriented Software*, Addison-Wesley, 1994, Chapter 1,
in the section on class versus interface inheritance and again in the section
titled "Composition versus Inheritance", state the guideline directly and give
it roughly a page and a half of justification, weighing white-box reuse
(subclassing, which exposes a parent's internals to a child) against black-box
reuse (composition through a reference, which exposes only a public interface)
([summarized with the page-20 location by the Wikipedia article "Composition
over inheritance"](https://en.wikipedia.org/wiki/Composition_over_inheritance),
verified 2026-08-02).

The GoF text names two costs of inheritance that the guideline exists to avoid.
Subclassing breaks encapsulation, because a subclass depends on the internal
implementation details of its parent, not only its interface, so a change to
the parent can force every subclass to change even when the parent's public
contract did not move. And inheritance is fixed at compile time in most
statically typed languages, so a class cannot swap its parent's behaviour while
the program runs, while an object holding a reference to a collaborator can
have that reference reassigned at any point ([Wikipedia summary of the same
GoF passage](https://en.wikipedia.org/wiki/Composition_over_inheritance),
verified 2026-08-02).

Alias one, **Has-A over Is-A**, names the same choice from the relationship a
reader draws on a whiteboard. Inheritance models "a Manager is-a Employee".
Composition models "a Notifier has-a DeliveryChannel". Alias two, **Delegation
over Subclassing**, is the mechanism-level name, because composition on its own
only gives an object a reference to a collaborator, and the object must then
forward calls to that collaborator to actually reuse its behaviour, which is
delegation. Kotlin's language designers use exactly this framing when
describing why the language ships a `by` keyword for interface delegation,
calling the Delegation pattern "a good alternative to implementation
inheritance" ([Kotlin documentation, "Delegation"](https://kotlinlang.org/docs/delegation.html),
verified 2026-08-02).

Joshua Bloch gives the same guideline its most cited restatement for a single
language. Item 18 of *Effective Java*, 3rd edition, Addison-Wesley, 2018,
Chapter 4 ("Classes and Interfaces"), is titled "Favor composition over
inheritance," and it narrows the guideline to a specific, checkable claim.
Avoid extending a concrete class across a package boundary unless it was
designed and documented for extension, and reach instead for a private field
holding an instance of the existing class plus a set of forwarding methods
([confirmed live against the item's chapter placement, a course-hosted excerpt
titled "ITEM 18. FAVOR COMPOSITION OVER INHERITANCE"](https://cs108.epfl.ch/archive/19/c/i/EffectiveJava_Item18.pdf),
verified 2026-08-02; the exact starting page differs slightly between printed
editions, so treat the chapter and item number, 4 and 18, as the stable
citation rather than a single page number).

Bloch's contribution to the lineage matters because it separates the general
GoF guideline from an operational rule. The rule is not "never subclass," it is
"never subclass across a trust boundary you do not control," which is the
precise condition under which the fragile base class problem below actually
bites.

## 2. Problem and context

A designer needs an object to have several independent, combinable behaviours,
and reaches for a single class hierarchy to express all of them. The first
behaviour fits cleanly as a base class. The second behaviour does not vary
along the same axis as the first, so it gets bolted on as another level of
subclassing, or as a second interface the subclass also implements with
duplicated logic. The third behaviour needs to combine with either the first or
the second independently of which concrete leaf class is chosen, and single
inheritance offers no way to express "any combination of A and B" without one
subclass per combination.

The concrete shape a reader will recognise follows a familiar arc. A
notification system starts with a `Notifier` base class and an
`EmailNotifier` subclass. Someone needs SMS, so `SmsNotifier` appears. Someone
needs an HTML-formatted email, and the fastest path is `HtmlEmailNotifier
extends EmailNotifier`. Someone needs an HTML-formatted SMS for a device that
renders it, and there is no clean place in the tree for `HtmlSmsNotifier` to
inherit from, because HTML formatting and SMS delivery are two orthogonal
decisions the tree can only express by multiplying. Two formats times two
channels demands four classes, three formats times three channels demands
nine, and the growth is the product of the axes, not their sum. This is the
textbook symptom the GoF guideline is answering, independent of which language
hosts it.

The context in which the problem arises has three conditions, and the
guideline is a response to their conjunction, not to inheritance in the
abstract. First, the behaviour genuinely varies along more than one independent
axis. Second, the class doing the varying is reused by code the original author
does not control, so a later change to a base class can silently break a
subclass the base class's author never saw, which is the fragile base class
problem named in dimension 11. Third, the reuse the hierarchy is trying to
achieve is implementation reuse, code borrowed for convenience, rather than a
genuine is-a relationship where every operation defined for the supertype is
substitutable by the subtype in every context, which is the condition Barbara
Liskov's substitutability requirement states for when subtyping is sound in the
first place. When all three conditions hold at once, a hierarchy is the wrong
tool, and an object built from smaller, independently replaceable parts is the
right one.

## 3. Forces

**Reuse mechanism versus reuse scope.** Inheritance reuses an implementation by
placing a class inside another class's compile-time type, which reuses
everything the parent defines, including behaviour the child never asked for.
Composition reuses an implementation by holding a reference and calling through
an interface, which reuses exactly the operations the interface exposes and
nothing else. The guideline favours the narrower, more deliberate scope.

**Coupling tightness.** A subclass is coupled to its superclass's
implementation, not merely its interface, because the subclass inherits
protected state, calls protected methods, and can be broken by an internal
refactor of the parent that never touches the parent's public contract. A
composed object is coupled only to the collaborator's public interface, so the
collaborator's internals can change freely as long as the interface holds.

**Flexibility in time.** A class hierarchy is fixed once the program is
compiled or, in a dynamic language, once the class is defined. An object
composed from other objects can have those collaborators swapped at runtime by
reassigning a field, which is the mechanism the Strategy pattern relies on and
the reason the two patterns are frequently discussed together.

**Number of axes of variation.** A single-inheritance hierarchy expresses at
most one axis of variation cleanly. Composition expresses any number of axes,
because each axis becomes its own interface and its own field, and the number
of concrete combinations never needs its own class.

**Discoverability and directness.** Inheritance is, for a reader who already
knows the language, extremely direct for a single, genuinely nested
is-a relationship, one level deep, with no orthogonal variation. Reading `class
Square extends Rectangle` costs nothing to understand. Composition costs an
extra hop, because the reader must open the collaborator's type to see what it
actually does, and a codebase that reaches for composition even where a single
clean is-a relationship would have sufficed pays a real readability tax for no
flexibility it will ever use.

**Team and package boundary.** Extending a class you do not own and cannot see
change is a different risk than extending a class in the same file you can
review in the same pull request. The GoF and Bloch guidance both weigh this
force explicitly. The risk of inheritance rises sharply the moment the
superclass sits across a trust boundary the subclass's author cannot audit or
influence.

The guideline favours composition on coupling, flexibility in time, and number
of axes. It sacrifices some directness for the single-level, single-axis case,
which is exactly why dimension 4 lists genuine is-a relationships as a case
where inheritance remains the better tool.

## 4. Applicability and non-applicability

Reach for composition when any of these hold.

- The object needs two or more independently varying behaviours, so a single
  hierarchy would otherwise require one class per combination of behaviours.
- The relationship between the two types is has-a or uses-a, not is-a. A
  `Car` has-a `Engine`. A `Car` is not an `Engine`.
- The behaviour must change at runtime, for example a payment processor
  swapping fraud-check strategies per transaction without redeploying.
- The base type sits outside your control, in a library or another team's
  package, so you cannot audit or predict future changes to its internals.
- You want to test the behaviour in isolation, by substituting a fake or a
  stub collaborator, without instantiating an entire concrete subclass tree.
- The language has no implementation inheritance at all, which describes Go
  and Rust, so composition through interfaces or traits is the only available
  mechanism and the guideline is not really a choice in those languages.

Do NOT reach for composition, and prefer inheritance instead, when the
following hold.

- The relationship is a genuine, narrow is-a relationship with no orthogonal
  variation, the type will never need a second independent axis of behaviour,
  and Liskov substitutability actually holds, meaning every client of the
  supertype can use the subtype without knowing the difference. A `Circle`
  extending a `Shape` that only ever adds a radius and an area calculation is
  a case where a single level of inheritance is simpler and cheaper than a
  `ShapeBehaviour` interface plus a field, for no flexibility gain.
- The framework or language demands inheritance as its extension point, for
  example a UI toolkit whose lifecycle hooks are only reachable by overriding
  a specific base class method, or an ORM whose entity mapping is driven by
  subclassing a base entity type. Fighting the framework's own extension
  mechanism to satisfy a general design guideline produces worse code than
  following the framework.
- You need to reuse implementation across a small, closed, single-team
  hierarchy where every subclass is visible in the same code review and the
  base class was explicitly designed to be extended, which is the exact
  carve-out Bloch gives in Item 18 for classes documented for inheritance.
- The performance cost of an extra virtual dispatch through a delegated
  interface is measured and material, which is rare but real in some
  allocation-hot inner loops in systems languages, and a direct inherited
  method call avoids one indirection.
- Composition would require duplicating the same three-line forwarding method
  across a dozen thin wrapper classes with no behavioural difference between
  them, and no language feature like Kotlin's `by` is available to remove the
  boilerplate. In that specific case, the composition guideline is correct in
  principle but the concrete cost in that codebase, in that language, may not
  be worth paying, and a documented, narrow inheritance is a defensible trade.

## 5. Structure

**Client.** The code that wants a behaviour, and depends only on the
behaviour's abstract interface, never on a concrete implementation.

**Composite** (also called the Host or the Context in Strategy-adjacent
literature). The object being built from parts. It holds one or more
references to Component types as fields, and it forwards, or delegates, calls
to those fields rather than implementing the behaviour itself.

**Component interface.** The abstract contract for one axis of behaviour, for
example `DeliveryChannel` or `MessageFormatter`. There is one Component
interface per independent axis of variation, which is the structural feature
that lets composition express n axes where single inheritance expresses one.

**Concrete Component.** A specific implementation of a Component interface,
for example `EmailChannel` or `HtmlFormatter`. Concrete Components are
interchangeable with any other implementation of the same interface, and the
Composite is written against the interface, never against a specific Concrete
Component.

**Assembler** (implicit, sometimes a Factory or a dependency-injection
container). The code that decides which Concrete Component instances a given
Composite instance receives. This role is easy to overlook, and its absence is
the most common reason a composition-based design still ends up hard to wire
by hand.

## 6. ASCII structure diagram

```
        depends on interfaces only
   +-----------+           +--------------------------+
   |  Client   |---------->|         Notifier          |
   +-----------+           |----------------------------
                            | - formatter: Formatter    |
                            | - channel:   Channel      |
                            |----------------------------
                            | + notify(event, payload)  |
                            +--------------------------+
                                  |             |
                            has-a |             | has-a
                                  v             v
                    +----------------+   +------------------+
                    |   Formatter    |   |     Channel      |
                    |----------------|   |------------------|
                    | + format(...)  |   | + deliver(msg)   |
                    +----------------+   +------------------+
                          ^      ^              ^      ^
                          |      |              |      |
              implements  |      | implements   |      | implements
                          |      |              |      |
              +-----------+  +---+--------+  +--+------+  +----------+
              | PlainFmt  |  | HtmlFmt    |  | Email   |  | Sms      |
              +-----------+  +------------+  +---------+  +----------+

   Any Formatter combines with any Channel. Adding a third axis, for example
   Retry, adds one interface and one field, never a new leaf class.
```

## 7. Dynamics

```
Assembler          Notifier             Formatter (Html)     Channel (Email)
   |                   |                      |                     |
   |-- new(fmt, ch) -->|                       |                     |
   |                   |  (fields set once,    |                     |
   |                   |   or reassigned       |                     |
   |                   |   later at runtime)   |                     |
   |                   |                       |                     |
Client                 |                       |                     |
   |-- notify(event, payload) --------------->|                     |
   |                   |                       |                     |
   |                   |-- format(event, payload) ------------------>|
   |                   |                       |-- runs, returns html
   |                   |<---------------------|                     |
   |                   |                                             |
   |                   |-- deliver(formatted message) -------------->|
   |                   |                                             |-- sends email
   |                   |<--------------------------------------------|
   |<-- returns -------|                                             |
```

Two properties are visible in the sequence that a hierarchy-based design could
never show. First, the field holding the `Formatter` and the field holding the
`Channel` are set independently, so the same `Notifier` instance can be
reconfigured to swap only the formatter, keeping the channel, by reassigning
one field, with no new class and no recompilation of the `Notifier` type
itself in a dynamically typed language, or a single constructor call in a
statically typed one. Second, the `Notifier` never inherits from `Formatter` or
`Channel`. It calls through the interface, so a test double substituted for
either field is indistinguishable, from the `Notifier`'s point of view, from
the real implementation, which is the property dimension 15 relies on.

## 8. Implementation variants

**Constructor injection.** The Composite receives its Component instances
through its constructor and stores them as immutable fields. This is the
default variant in every language shown in this entry's code examples, because
it makes the dependency visible at the call site and makes the Composite
impossible to construct in a half-wired state.

**Setter or property injection.** The Composite exposes a mutable field or
setter for a Component, allowing the collaborator to change after
construction. This is strictly more flexible than constructor injection and
strictly less safe, because the Composite can exist, briefly or permanently, in
a state where the field is unset, so it is worth the extra flexibility only
when runtime reconfiguration is a real requirement, not a hypothetical one.

**Interface delegation with language support.** Some languages remove the
forwarding boilerplate mechanically. Kotlin's `class Notifier(c: Channel):
Channel by c` generates the forwarding methods for the delegated interface at
compile time, which is the language feature the Kotlin documentation
introduces explicitly as an alternative to implementation inheritance
([Kotlin documentation, "Delegation"](https://kotlinlang.org/docs/delegation.html),
verified 2026-08-02).

**Struct or interface embedding, a partial mechanism, not the pattern
proper.** Go has no implementation inheritance, and its struct embedding is
often mistaken for a shortcut to it. Embedding promotes an embedded type's
methods to the outer struct so they can be called without an explicit field
access, but the receiver of a promoted method remains the embedded value, not
the outer struct, which is exactly the distinction the Go project's own
documentation draws. "There's an important way in which embedding differs from
subclassing. When we embed a type, the methods of that type become methods of
the outer type, but when they are invoked the receiver of the method is the
inner type, not the outer one" ([The Go Programming Language, "Effective
Go", section "Embedding"](https://go.dev/doc/effective_go#embedding), verified
2026-08-02). Embedding is composition with automatic method forwarding, never
subclassing with dynamic dispatch, and treating it as the latter is a common
source of confusion for readers coming from a class-based language.

**Trait or protocol composition.** Rust traits and Swift protocols let a type
declare conformance to several independent behaviours without any type
inheriting from another type at all, since neither language has implementation
inheritance for structs. The pattern collapses into "define one trait or
protocol per axis, implement each on the concrete piece, hold the pieces as
fields or generic parameters" in both languages, which is structurally
identical to the interface-based variant shown in the Go and TypeScript
examples.

**Function-valued fields, the degenerate case.** When a Component interface
has exactly one method, the interface itself can be replaced by a function
type, and the Composite holds a function reference instead of an object
reference. This is common in JavaScript, Go, and modern Java using functional
interfaces, and it removes a layer of interface declaration for the single-
method case at the cost of losing a named type a reader can search for.

## 9. Known production uses

**Unity's GameObject and Component system.** Unity's entire scene-object model
is built on composition instead of a class hierarchy of game object types.
Unity's own manual states that "GameObjects are the building blocks for scenes
in Unity and act as a container for functional components which determine how
the GameObject looks and what it does" ([Unity Manual, "GameObject"](https://docs.unity3d.com/Manual/class-GameObject.html),
verified 2026-08-02). A game object gains physics, rendering, or audio
behaviour by attaching a `Rigidbody`, a `MeshRenderer`, or an `AudioSource`
component, rather than by inheriting from a `PhysicsGameObject` or an
`AudibleGameObject` base class, which is the same avoid-the-combinatorial-
explosion motivation named in dimension 2, applied at the scale of an entire
engine.

**Kotlin's built-in interface delegation.** The Kotlin language ships a `by`
keyword specifically so that composition-based reuse does not carry a
boilerplate cost relative to inheritance. The language reference states that
"the Delegation pattern has proven to be a good alternative to implementation
inheritance, and Kotlin supports it natively requiring zero boilerplate code"
([Kotlin documentation, "Delegation"](https://kotlinlang.org/docs/delegation.html),
verified 2026-08-02). This is a case of a language designer treating the
guideline as important enough to build a dedicated syntax feature around it.

**React's official guidance to component authors.** React's documentation
states the guideline as a direct recommendation to every developer using the
framework. "React has a powerful composition model, and we recommend using
composition instead of inheritance to reuse code between components" ([React
documentation, "Composition vs Inheritance"](https://legacy.reactjs.org/docs/composition-vs-inheritance.html),
verified 2026-08-02). React components share behaviour by nesting and passing
props and children, never by one component class extending another, and
React's own class-component base type, `React.Component`, is the one and only
inheritance relationship the framework asks a developer to use, precisely to
avoid the fragility a multi-level component hierarchy would introduce across
an application with many independent authors.

**The `java.io` stream decorator family.** The Java standard library's
`BufferedInputStream` reuses another stream's byte-reading behaviour by holding
a reference to it, not by extending its concrete class. The class
documentation states plainly that "a `BufferedInputStream` adds functionality
to another input stream, namely the ability to buffer the input and to support
the `mark` and `reset` methods... as bytes from the stream are read or
skipped, the internal buffer is refilled as necessary from the contained input
stream" ([Java SE 17 API, `java.io.BufferedInputStream`](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/BufferedInputStream.html),
verified 2026-08-02). Any `InputStream` implementation can be wrapped, so
buffering composes freely with file streams, network streams, or another
decorator, which is exactly the combinatorial flexibility a hierarchy of
`BufferedFileInputStream`, `BufferedSocketInputStream`, and so on could not
offer without one class per combination.

**Go's standard library `bufio` and `io` packages.** Because Go has no
implementation inheritance at all, its entire standard library is built on
composing small interfaces, most famously `io.Reader` and `io.Writer`, each a
single method. `bufio.NewReader` takes any `io.Reader` and returns a
`*bufio.Reader` that holds it as a field and adds buffering, the same shape as
the Java example above, achieved through composition because the language
provides no other mechanism, which the language's own documentation frames as
a deliberate design choice rather than a missing feature ([The Go Programming
Language, "Effective Go", section "Embedding"](https://go.dev/doc/effective_go#embedding),
verified 2026-08-02).

## 10. Consequences

Positive.

- Behaviour composes along independent axes without a combinatorial explosion
  of concrete classes, which is the primary force the guideline optimises for.
- A collaborator can be swapped at runtime by reassigning a reference, which
  inheritance, fixed at compile time or class-definition time, cannot offer.
- Coupling is limited to the collaborator's public interface, so the
  collaborator's internal implementation can be refactored freely, which
  directly removes the fragile base class exposure named in dimension 11.
- Testing improves, because any Component interface can be satisfied by a
  fake, a stub, or a mock, letting the Composite's own logic be tested with
  zero real collaborators instantiated.
- The design documents its own extension points. A new axis of variation is a
  new interface, which is a visible, reviewable addition, rather than a new
  branch inserted somewhere into an existing hierarchy where its placement is
  a judgement call.

Negative.

- More types are declared for the same behaviour, one interface plus one or
  more implementations per axis, versus one subclass in a hierarchy. For a
  design with a single, genuinely simple is-a relationship, this is pure
  overhead with no offsetting benefit.
- Forwarding, delegating a call from the Composite to a Component, must be
  written explicitly in every language without a delegation feature, which is
  boilerplate that inheritance's automatic method promotion never requires.
- Wiring the Composite, choosing which Concrete Components it receives,
  becomes a separate concern the codebase must solve, whether by hand, by a
  factory, or by a dependency-injection container. A hierarchy has no
  equivalent wiring step, because the choice of behaviour is baked into which
  concrete subclass was instantiated.
- Reading the full behaviour of an object requires opening every Component
  interface it holds, whereas a shallow, single-level inheritance chain can be
  read top to bottom in one file for the simple case.
- Excess indirection through many thin, one-method Component interfaces can
  make a debugger's call stack harder to read than a direct virtual call, a
  cost that is small per call and real in aggregate in a very deeply composed
  system.

## 11. Failure modes and misuse

**Symptom.** A one-line behavioural change to a base class, made in one
package, causes test failures in a subclass in a completely different part of
the codebase, or in a different team's module, with no obvious connection
visible from the diff.
**Cause.** The fragile base class problem. The subclass's correctness depended
on an implementation detail of the base class, not on its documented contract,
so any change to that detail, even one that leaves the base class's public
behaviour unchanged, can silently break every subclass. Mikhajlov and
Sekerinski formalise this as a violation of a flexibility property. A base
class revision is safe to substitute for its original only under restrictions
on how inheritance is used, restrictions that most inheritance-heavy codebases
do not actually enforce ([Leonid Mikhajlov and Emil Sekerinski, "A Study of The
Fragile Base Class Problem", Proceedings of the 12th European Conference on
Object-Oriented Programming, ECOOP '98, pages 355 to 382](https://link.springer.com/chapter/10.1007/BFb0054099),
verified 2026-08-02).
**Fix.** Replace the inheritance relationship with a Component interface plus
a held reference. The subclass's dependency on the base class's internals is
now a dependency on an explicit, documented interface, and a change to the
concrete implementation behind that interface can no longer silently break the
consumer unless the interface's contract itself changes, which is a visible,
reviewable event.

**Symptom.** A new requirement forces a new leaf class whose name is a
concatenation of two existing class names, for example `HtmlSmsNotifier`, and
the team notices the number of classes for a given feature area growing
roughly as the product, not the sum, of the number of options along each axis.
**Cause.** Composition over inheritance was needed from the start, because the
behaviour genuinely varies along two or more independent axes, and the design
used a single hierarchy to express what needed two or more separate,
composable interfaces.
**Fix.** Identify the independent axes, extract one interface per axis, and
replace the hierarchy leaves with a single Composite class parameterised by
one field per axis, exactly as shown in dimension 6.

**Symptom.** A team adopts composition everywhere on principle, and a simple,
one-level, genuinely nested is-a relationship, for example a `PremiumUser`
that really is a `User` in every operation a client performs, gets rewritten
as a `UserBehaviour` interface plus a field, adding a file, an interface
declaration, and a wiring step for zero behavioural gain.
**Cause.** Treating the guideline as an absolute rule rather than a response
to the three conditions named in dimension 2, multiple independent axes, an
untrusted base class, or a violated substitutability requirement. When none of
those three conditions hold, the guideline's own justification does not apply.
**Fix.** Apply dimension 4's non-applicability list before reaching for
composition. A single, well-understood, in-package is-a relationship with no
orthogonal variation is exactly the case inheritance was designed for, and the
GoF guideline itself never claims otherwise.

**Symptom.** A Composite class accumulates a growing constructor parameter
list, one parameter per Component, and callers start passing `null` for
Components they do not need, which then requires null checks scattered through
every method that might use them.
**Cause.** Composition was applied to a set of behaviours that are not
actually independent axes but a single coherent responsibility that keeps
splitting further than it should, or the Composite itself is taking on too
many unrelated responsibilities and should be split into two Composites, each
with fewer Components.
**Fix.** Group Components that are always supplied together into a single,
smaller interface, or split the Composite along its actual responsibility
boundary rather than adding a nullable field for a rarely used axis.

## 12. Trade-off matrix

| Force | Composition over Inheritance | Template Method | Simple type-code Factory / switch |
|---|---|---|---|
| Number of independent axes expressed cleanly | Any number, one interface per axis | One, the axis the template's abstract steps vary along | One, the axis the switch branches on |
| Runtime reconfigurability | Yes, reassign the held reference | No, the concrete subclass is fixed at construction | No, the branch taken is fixed at the call that built the object |
| Coupling to collaborator internals | Interface only | Base class internals, via protected members and call order | None, the switch itself has no dependency on the branches' internals |
| Boilerplate for a single simple case | Extra interface plus field, real cost for one axis | None, a single override | None, a single case label |
| Testability in isolation | High, substitute a fake per Component | Lower, must instantiate the subclass to exercise the overridden step | High, but only if the created object's own type is itself testable in isolation |
| Best fit | Multiple independent, combinable, or swappable behaviours | One fixed algorithm skeleton with one varying step, no runtime swap needed | A small, closed, rarely changing set of concrete types selected by a known code |

## 13. Related and incompatible patterns

**Strategy.** Strategy is the specific, named pattern that composition over
inheritance most directly produces when the varying behaviour is a single
interchangeable algorithm. Every Strategy instance is a Component in this
entry's terms, held by a Context that plays the Composite role. Reaching for
composition over inheritance for a single axis of algorithmic variation and
reaching for Strategy by name are, in practice, the same design decision
described at two levels of specificity.

**Decorator.** Decorator layers additional behaviour around an object of the
same interface it decorates, and is composition applied recursively along a
single axis, where each layer both implements and holds a reference to the
same Component type. The `java.io` stream family in dimension 9 is a Decorator
built from composition, not a separate mechanism from it.

**Bridge.** Bridge splits an abstraction from its implementation into two
separate, independently varying hierarchies connected by composition, which is
composition over inheritance applied specifically to the case where both the
abstraction side and the implementation side each have their own, separate
sub-variation, rather than one side being a fixed Component interface.

**Template Method.** Template Method is the inheritance-based alternative this
entry's guideline recommends replacing when the varying step needs to change
at runtime or needs to combine with a second independent axis. When the
varying step is genuinely fixed for the lifetime of the object and there is
exactly one axis, Template Method remains a legitimate, simpler choice, so the
two patterns are complementary alternatives rather than one obsoleting the
other.

**Dependency Injection.** Dependency Injection is the assembly mechanism that
answers the Assembler role named in dimension 5. Composition over inheritance
says an object should hold its collaborators through interfaces, and
dependency injection is the disciplined practice of deciding, in one place,
which concrete collaborators a given object receives, so the two are
frequently adopted together, with DI supplying the wiring composition needs
and lacks on its own.

**Mixin and multiple inheritance, a genuinely incompatible alternative in some
languages.** In languages that support mixins or multiple inheritance, a
designer has a third option beyond single inheritance and composition, which
is to compose behaviour at the type-definition level instead of the object
level. This is not a variant of composition over inheritance, it is a
different resolution of the same underlying force, and it carries its own
version of the fragile base class problem across the diamond of multiple
parents, which is out of this entry's scope.

## 14. Refactoring path in and out

**Introducing composition where a hierarchy already exists.** Extract each
independent axis of variation the hierarchy is trying to express into its own
interface. Name it for the behaviour, not the current subclass, for example
`Formatter`, not `EmailNotifierFormatting`. Give the interface one
implementation per current leaf class's behaviour along that axis. Add a field
of the interface type to the class that will become the Composite, and change
every call site that referenced the old subclass's overridden method into a
call through the new field. Delete the leaf subclasses only after every call
site compiles and every existing test passes against the new field-based path,
never before, since the leaf classes are the safety net during the migration.
This is the same shape as the refactoring literature's "Replace Inheritance
with Delegation," and the mechanical steps above are a specialisation of it for
the case where the hierarchy has more than one leaf class per parent.

**Removing composition when it stops earning its place.** The signal that a
composed design has outlived its justification is a Component interface with
exactly one implementation, that implementation has had no second
implementation added in a long, stable period of the codebase's life, and the
axis it represents has never varied at runtime in production. When all three
hold, inline the single implementation's behaviour directly into the Composite,
delete the interface, and delete the Assembler wiring for that one field. Do
this only after confirming, not assuming, that no test double substitutes a
fake for that interface, since a test-only second implementation is still a
real, load-bearing use of the interface even if production code never varies
it.

## 15. Testing and verification

Composition makes unit testing the Composite in isolation direct. Construct
the Composite with a hand-written fake or a mocking framework's stub for each
Component interface, assert on the calls the Composite made to those fakes,
and never instantiate a real `EmailChannel` or a real `HtmlFormatter` to test
that `Notifier.notify` calls `format` before `deliver`. This is the specific
testing benefit that motivates dependency injection as the natural partner
practice named in dimension 13, because constructor injection is exactly the
point at which the test supplies fakes instead of real collaborators.

What becomes harder to test is the wiring itself, the Assembler's decision
about which concrete Components a given Composite receives in production. A
suite of Composite unit tests that all pass proves the Composite's own logic
is correct given whatever it was handed, and proves nothing about whether
production wiring hands it the right concrete implementations, which needs a
separate integration or wiring test that exercises the real Assembler and
asserts on the concrete types it produces, or a smoke test that runs the
assembled object end to end at least once.

Contract tests are the right tool for verifying that every Concrete Component
implementing a shared interface actually honours that interface's behavioural
contract, not merely its method signatures. A single shared contract-test suite,
parameterised over every implementation of `Formatter`, catches the case where
a new `MarkdownFormatter` returns an empty string on an empty payload while
`PlainFormatter` and `HtmlFormatter` both return a non-empty header, an
inconsistency that per-implementation unit tests, written independently by
different authors, are prone to miss.

## 16. Observability signals

Log or trace which concrete Component instance a given Composite is holding at
the moment of a call, tagged with a stable identifier for the interface it
implements, for example a `formatter.type=html` field on the log line emitted
by `Notifier.notify`. Because composition permits runtime reconfiguration, an
incident where a Composite is behaving unexpectedly is frequently explained by
discovering which concrete Component it was actually holding at the time,
which a stack trace from a purely inheritance-based design would already show
implicitly in the object's own runtime type, but a composed design must
surface explicitly since the type of the Composite itself never changes.

A healthy composed system, viewed on a dashboard, shows a small, stable set of
distinct Component-type combinations in production traffic, matching the
combinations the Assembler is actually configured to produce. A failing or
misconfigured one shows either a combination that should be structurally
impossible given the Assembler's own configuration, which points at a wiring
bug, or a single Component type dominating unexpectedly, which points at a
configuration default silently overriding an intended per-request choice.

Count how many distinct Component implementations exist per interface over
time. A steadily growing count for an interface that was expected to stay
small is the metric-level version of the failure mode named in dimension 11
where axes were not truly independent, and it is worth surfacing on a
dashboard the same way a growing cyclomatic complexity metric is surfaced for
a single function.

## 17. Security and privacy implications

Composition changes where an authorisation or input-validation check lives,
and getting this placement wrong is the concrete security risk the pattern
introduces. If two Concrete Components implementing the same interface, for
example two `DeliveryChannel` implementations, each duplicate their own
authorisation check rather than the check living once in the Composite or in a
Decorator layer wrapping every Channel, a third implementation added later can
easily omit the check, silently reintroducing a vulnerability the other two
implementations closed. The fix is structural. Put the cross-cutting check in
a Decorator that wraps the Component interface, so every implementation,
present and future, passes through it, rather than trusting every future
implementer to remember to duplicate the check.

Composition also changes the audit surface for what data a given object can
touch. A subclass inherits, and therefore has direct field access to, every
protected member of its base class, which an auditor reviewing the base class
alone cannot fully enumerate without reading every subclass. A Composite
declares its collaborators as typed fields with a narrow interface, which is
directly enumerable from the Composite's own source, without reading any
Component's implementation, making a data-flow or capability audit strictly
easier to perform mechanically for a composed design than for a deep
inheritance chain.

Where a Component interface is satisfied by plugin or third-party code loaded
at runtime, for example a `DeliveryChannel` supplied by an external
integration, the Composite is implicitly trusting that implementation with
whatever data it passes through the interface's method calls, and the
interface boundary is exactly where a least-privilege review should focus,
since it is the single, enumerable point every implementation, trusted or not,
must pass through.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides, *Design
   Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley,
   1994, Chapter 1, guideline "Favor object composition over class
   inheritance."
2. Wikipedia, "Composition over inheritance," https://en.wikipedia.org/wiki/Composition_over_inheritance,
   verified 2026-08-02, for the page-20 location and the encapsulation and
   compile-time-fixed-inheritance summary of the GoF passage, and for the
   citation to Eric Freeman, Elisabeth Robson, Bert Bates, and Kathy Sierra,
   *Head First Design Patterns*, O'Reilly, 2004, page 23.
3. Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018, Chapter
   4, Item 18, "Favor composition over inheritance."
4. Course excerpt confirming Item 18's chapter and item number,
   https://cs108.epfl.ch/archive/19/c/i/EffectiveJava_Item18.pdf, verified
   2026-08-02.
5. Leonid Mikhajlov and Emil Sekerinski, "A Study of The Fragile Base Class
   Problem," Proceedings of the 12th European Conference on Object-Oriented
   Programming, ECOOP '98, pages 355 to 382, https://link.springer.com/chapter/10.1007/BFb0054099,
   verified 2026-08-02.
6. Unity Technologies, "GameObject," Unity Manual, https://docs.unity3d.com/Manual/class-GameObject.html,
   verified 2026-08-02.
7. JetBrains, "Delegation," Kotlin documentation, https://kotlinlang.org/docs/delegation.html,
   verified 2026-08-02.
8. Meta, "Composition vs Inheritance," React documentation, https://legacy.reactjs.org/docs/composition-vs-inheritance.html,
   verified 2026-08-02.
9. Oracle, "BufferedInputStream," Java SE 17 API documentation, https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/BufferedInputStream.html,
   verified 2026-08-02.
10. The Go Authors, "Effective Go," section "Embedding," https://go.dev/doc/effective_go#embedding,
    verified 2026-08-02.

## Code examples

Three languages, chosen to show the pattern under three different type
systems. TypeScript shows the classical, explicitly interfaced form most
readers will recognise first. Python shows the same shape using `Protocol`,
which is structural, not nominal, so a class satisfies an interface by shape
alone with no `implements` declaration. Go shows the form that is not a
stylistic choice in that language but the only mechanism available, since Go
has no implementation inheritance at all.

The domain is the notification example from dimension 2 and dimension 6, a
`Notifier` composed from a message `Formatter` and a delivery `Channel`, with
the naive inheritance alternative, `HtmlEmailNotifier`, `PlainSmsNotifier`, and
so on, deliberately avoided.

### TypeScript

```typescript
interface Channel {
  deliver(message: string): void;
}

class EmailChannel implements Channel {
  deliver(message: string): void {
    console.log(`EMAIL: ${message}`);
  }
}

class SmsChannel implements Channel {
  deliver(message: string): void {
    console.log(`SMS: ${message}`);
  }
}

interface Formatter {
  format(event: string, payload: Record<string, string>): string;
}

class PlainFormatter implements Formatter {
  format(event: string, payload: Record<string, string>): string {
    return `${event}: ${JSON.stringify(payload)}`;
  }
}

class HtmlFormatter implements Formatter {
  format(event: string, payload: Record<string, string>): string {
    const rows = Object.entries(payload)
      .map(([key, value]) => `<li>${key}: ${value}</li>`)
      .join("");
    return `<b>${event}</b><ul>${rows}</ul>`;
  }
}

class Notifier {
  constructor(
    private formatter: Formatter,
    private channel: Channel,
  ) {}

  notify(event: string, payload: Record<string, string>): void {
    this.channel.deliver(this.formatter.format(event, payload));
  }

  // Runtime reconfiguration. No new class, no recompilation of Notifier.
  useFormatter(next: Formatter): void {
    this.formatter = next;
  }
}

const htmlEmail = new Notifier(new HtmlFormatter(), new EmailChannel());
htmlEmail.notify("order.shipped", { orderId: "42" });

const plainSms = new Notifier(new PlainFormatter(), new SmsChannel());
plainSms.notify("order.shipped", { orderId: "42" });

htmlEmail.useFormatter(new PlainFormatter());
htmlEmail.notify("order.shipped", { orderId: "42" });
```

### Python

```python
from dataclasses import dataclass
from typing import Protocol


class Channel(Protocol):
    def deliver(self, message: str) -> None: ...


class EmailChannel:
    def deliver(self, message: str) -> None:
        print(f"EMAIL: {message}")


class SmsChannel:
    def deliver(self, message: str) -> None:
        print(f"SMS: {message}")


class Formatter(Protocol):
    def format(self, event: str, payload: dict[str, str]) -> str: ...


class PlainFormatter:
    def format(self, event: str, payload: dict[str, str]) -> str:
        return f"{event}: {payload}"


class HtmlFormatter:
    def format(self, event: str, payload: dict[str, str]) -> str:
        rows = "".join(f"<li>{k}: {v}</li>" for k, v in payload.items())
        return f"<b>{event}</b><ul>{rows}</ul>"


@dataclass
class Notifier:
    formatter: Formatter
    channel: Channel

    def notify(self, event: str, payload: dict[str, str]) -> None:
        self.channel.deliver(self.formatter.format(event, payload))


if __name__ == "__main__":
    html_email = Notifier(HtmlFormatter(), EmailChannel())
    html_email.notify("order.shipped", {"orderId": "42"})

    plain_sms = Notifier(PlainFormatter(), SmsChannel())
    plain_sms.notify("order.shipped", {"orderId": "42"})

    # Runtime reconfiguration. Dataclass fields are plain attributes.
    html_email.formatter = PlainFormatter()
    html_email.notify("order.shipped", {"orderId": "42"})
```

Note the shape difference from TypeScript. `Formatter` and `Channel` are
`Protocol` classes, so `EmailChannel` and `PlainFormatter` satisfy them purely
by having the right method signature, with no `implements` or inheritance
declaration anywhere. This is structural typing applied to the same pattern,
and it is the reason composition costs almost nothing extra to declare in
Python compared to just writing a class with the right method.

### Go

```go
package main

import "fmt"

type Channel interface {
	Deliver(message string)
}

type EmailChannel struct{}

func (EmailChannel) Deliver(message string) {
	fmt.Printf("EMAIL: %s\n", message)
}

type SmsChannel struct{}

func (SmsChannel) Deliver(message string) {
	fmt.Printf("SMS: %s\n", message)
}

type Formatter interface {
	Format(event string, payload map[string]string) string
}

type PlainFormatter struct{}

func (PlainFormatter) Format(event string, payload map[string]string) string {
	return fmt.Sprintf("%s: %v", event, payload)
}

type HtmlFormatter struct{}

func (HtmlFormatter) Format(event string, payload map[string]string) string {
	rows := ""
	for key, value := range payload {
		rows += fmt.Sprintf("<li>%s: %s</li>", key, value)
	}
	return fmt.Sprintf("<b>%s</b><ul>%s</ul>", event, rows)
}

type Notifier struct {
	Formatter Formatter
	Channel   Channel
}

func (n *Notifier) Notify(event string, payload map[string]string) {
	n.Channel.Deliver(n.Formatter.Format(event, payload))
}

func main() {
	htmlEmail := &Notifier{Formatter: HtmlFormatter{}, Channel: EmailChannel{}}
	htmlEmail.Notify("order.shipped", map[string]string{"orderId": "42"})

	plainSms := &Notifier{Formatter: PlainFormatter{}, Channel: SmsChannel{}}
	plainSms.Notify("order.shipped", map[string]string{"orderId": "42"})

	// Runtime reconfiguration. A struct field, reassigned directly.
	htmlEmail.Formatter = PlainFormatter{}
	htmlEmail.Notify("order.shipped", map[string]string{"orderId": "42"})
}
```

Go has no `class` keyword and no `extends`, so there is no naive inheritance
alternative to contrast against in this language. Every Go type that reuses
another type's behaviour does so either by holding a field and calling through
it, as shown above, or by embedding, described in dimension 8, which is
itself a form of composition with automatic call forwarding rather than a
separate mechanism.
