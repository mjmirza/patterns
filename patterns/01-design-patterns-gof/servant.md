---
name: Servant
slug: servant
family: 01-design-patterns-gof
category: Behavioral
aliases: [Helper, Helper Class, Utility Class]
first_described: "Uncertain. Wikipedia's sole citation is Pecinovsky, Pavlickova, Pavlicek, June 2006, University of Bologna, but its content was not independently verified. The pattern's own reference lineage traces more plausibly to POSA1, per the iluwatar reference implementation's own citation list"
maturity: contested
related: []
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

Not a Gang of Four pattern. Wikipedia's own "Design Patterns" article enumerates the GoF book's full 23-pattern contents, five creational, seven structural, eleven behavioral, and Servant appears in none of the three lists.

Wikipedia's own record on this point is not fully consistent, and this entry states that honestly rather than smoothing it over. The dedicated "Servant (design pattern)" article carries no GoF classification tag in its own categories, but a comparison table on the separate "Software design pattern" article marks a Servant row with "In Design Patterns" as yes, alongside "In Code Complete" as yes. That claim conflicts with the well-documented, stable 23-pattern table of contents of the actual 1994 GoF book. This entry treats the comparison-table row as an uncorroborated, likely erroneous secondary claim rather than evidence the pattern is GoF, since the GoF book's own contents are independently confirmed elsewhere and the dedicated article's own categorization does not support it.

Wikipedia's only cited source for the dedicated article is Pecinovsky, Pavlickova, and Pavlicek, "Let's Modify the Objects First Approach into Design Patterns First," presented at the Eleventh Annual Conference on Innovation and Technology in Computer Science Education, University of Bologna, June 2006. This entry could not independently fetch or verify that paper's content, so it is recorded as the earliest attested citation, not as a confirmed origin. The Wikipedia article itself was created on 29 November 2010 by a single editor, a fact recorded here for completeness rather than as evidence of anything beyond when the term entered Wikipedia.

A stronger, independently sourced lineage clue comes from the pattern's most substantial current reference implementation. The `iluwatar/java-design-patterns` project's own Servant module lists its references as the GoF book, "Java Design Patterns, A Hands-On Experience," and "Pattern-Oriented Software Architecture Volume 1, A System of Patterns," POSA1. Since the pattern is confirmed absent from the actual GoF catalogue, this reference list suggests the pattern's real documented lineage runs through POSA1 rather than through Gamma, Helm, Johnson, and Vlissides directly, though this entry states that as a reasoned inference from the citation list rather than a claim any source states outright.

Aliases. Wikipedia's own "Software design pattern" article states directly, "the servant pattern is also frequently called helper class or utility class implementation for a given set of classes." The `iluwatar` project's own frontmatter independently lists "Also known as, Helper" for the same pattern, a second, independent source corroborating the same alias. No source found uses "Server" as an alias, despite that being a plausible-sounding hypothesis, and this entry does not assert it.

## 2. Problem and context

Wikipedia's own definition, quoted directly. "Servant is used for providing some behavior to a group of classes. Instead of defining that behavior in each class, or when we cannot factor out this behavior in the common parent class, it is defined once in the Servant." The article's own lead restates the same idea. "The servant pattern defines an object used to offer some functionality to a group of classes without defining that functionality in each of them. A Servant is a class whose instance, or even just class, provides methods that take care of a desired service, while objects for which, or with whom, the servant does something, are taken as parameters."

The pattern is illustrated with geometric shapes, though not with an area calculation as one might expect. Wikipedia's own worked example, quoted directly. "We have a few classes representing geometric objects, rectangle, ellipse, and triangle. We can draw these objects on some canvas. When we need to provide a move method for these objects we could implement this method in each class, or we can define an interface they implement and then offer the move functionality in a servant." The shared operation is repositioning, via a `Movable` interface with `getPosition` and `setPosition`, serviced by a `MoveServant` class exposing `moveTo` and `moveBy`. sourcemaking.com, a source that illustrates many other patterns with real code, was checked directly and carries no Servant entry at all, so the shape-based illustration traced here comes from Wikipedia specifically, not from sourcemaking.

## 3. Forces

Wikipedia's article carries no section explicitly labeled forces, so what follows is drawn from what the sourced text actually states, not from an invented forces list. The central tension, stated directly, is between duplicating the same method in every participating class and inventing an artificial common base class purely to host shared behavior, which the article frames as the trigger condition itself, "when we cannot factor out this behavior in the common parent class." The pattern's own justification for the third option it offers is stated directly too. "The moving code appears in only one class which respects the separation of concerns rule."

A second, genuinely sourced force concerns which side of the relationship carries the coupling. The article describes two implementation variants and their trade-off directly. "User knows the servant, in which case it is needed to know the serviced classes, and sends messages with requests to the servant instances, passing the serviced objects as parameters. The serviced classes do not know about servant, but they implement the required interface," against, "serviced instances know the servant and the user sends them messages with requests, in which case it isn't necessary to know the servant." The first variant keeps the served classes ignorant of the servant at the cost of the caller needing to know both sides. The second keeps the caller ignorant of the servant at the cost of coupling every served class to the servant directly.

A third force is named directly by the article itself, a near-duplication risk against the Command pattern, where implementations of the two "are often virtually the same," and the only real difference is the intent behind the design rather than its shape, covered in full in dimension 13.

## 4. Applicability and non-applicability

The pattern applies directly when the sourced trigger condition holds, several otherwise unrelated classes need the same piece of functionality and giving them a common base class or interface purely to host it is undesirable or impossible, per the "cannot factor out this behavior in the common parent class" wording quoted in dimension 2. It also applies when the goal is centralizing shared logic in one place rather than duplicating it, per the separation of concerns quote in dimension 3.

The two structural variants imply a further, unstated-but-reasonable applicability split. the client-knows-servant variant fits better when the served classes are not owned by the implementer, or should not be modified beyond a small interface, while the served-knows-servant variant presumes the implementer can and will modify each served class to hold a reference to the servant. This entry states that split as its own reasoning drawn from the two variants' own described coupling, not as a claim any source makes explicitly.

Non-applicability follows from the Command-pattern comparison in dimension 13. when the real need is to parameterize an existing object with new behavior, rather than to offer one new operation to several existing, otherwise unrelated objects, the sourced comparison suggests Command is the better-fitting name for that intent, even when the resulting code looks nearly identical.

## 5. Structure

Wikipedia's own structural definition, quoted directly. "A Servant is a class whose instance, or even just class, provides methods that take care of a desired service, while objects for which, or with whom, the servant does something, are taken as parameters." The two implementation variants are described directly, with figure captions quoted as published. "User uses servant to achieve some functionality and passes the serviced objects as parameters," and, "user requests operations from serviced instances, which then asks servant to do it for them."

Confirmed against a real, independently written implementation, `andrei-punko/design-patterns`, the structural roles are as follows. A `MoveServant` class holds no state of its own related to the served objects, its methods `moveTo` and `moveBy` each take a served instance as a parameter. A `Movable` interface, declaring only `getPosition` and `setPosition`, is the sole thing tying the otherwise unrelated shape classes together. `Ellipse`, `Rectangle`, and `Triangle` each independently implement `Movable`, sharing no common ancestor beyond the language's own root object type, and no shared logic beyond what each trivially repeats to satisfy the interface.

## 6. ASCII structure diagram

```
+-------------------+           +----------------------+
|    MoveServant     |  uses --> |  <<interface>>       |
+-------------------+           |     Movable          |
| + moveTo(s, pos)   |           +----------------------+
| + moveBy(s, dx,dy) |           | + getPosition()      |
+-------------------+           | + setPosition(p)      |
                                 +----------------------+
                                    ^        ^        ^
                                    |        |        |
                             implements implements implements
                                    |        |        |
                              +---------+ +--------+ +----------+
                              | Triangle | | Ellipse | | Rectangle |
                              +---------+ +--------+ +----------+
```

MoveServant is connected only to the Movable interface, never to any concrete shape class directly, and the three shape classes carry no line to each other and no line to any shared parent. The only line touching all three at once is the dashed implements relationship to Movable. That absence, no shared base class anywhere in the picture, is the entire structural point of the pattern.

## 7. Dynamics

Following the client-knows-servant variant quoted in dimension 5, a call flows client to servant to served object, in that order. the client holds both a `MoveServant` reference and a reference to one of the shape instances, and calls `servant.moveTo(shape, position)`. Inside that call, `MoveServant` reads and writes the shape's state exclusively through the `Movable` interface's `getPosition` and `setPosition`, never through any shape-specific member, which is what lets one servant method serve `Triangle`, `Ellipse`, and `Rectangle` without knowing which concrete type it received. A real dispatch mechanism confirmed directly in the `faif/python-patterns` implementation shows the honest cost of this shape when a servant needs type-specific behavior beyond the shared interface, its own `GeometryTools.calculate_area` branches explicitly on `isinstance(shape, Circle)` and `isinstance(shape, Rectangle)`, manual runtime type-checking rather than compiler-enforced polymorphic dispatch, since nothing in the pattern's own structure provides dispatch beyond what the shared interface itself exposes.

In the served-knows-servant variant, quoted in dimension 3, the flow reverses. the served instance itself holds the servant reference and forwards the client's request to it, so the client never needs to know the servant exists at all, at the cost of every served class now depending directly on the servant.

## 8. Implementation variants

**Classic Java, a hand-written servant plus a minimal shared interface.** `andrei-punko/design-patterns` implements exactly the Wikipedia shape. a `Movable` interface with `getPosition` and `setPosition`, a `MoveServant` class whose `moveTo` and `moveBy` methods each take a `Movable` as their first parameter, and `Ellipse`, `Rectangle`, `Triangle` classes each implementing `Movable` independently. A second, independently written Java implementation, `iluwatar/java-design-patterns`, generalizes the same shape to a non-geometric domain, a restaurant `Servant` class with `feed`, `giveWine`, and `giveCompliments` methods that each take a `Royalty` instance, `King` or `Queen`, confirming the pattern's shape is not tied to the geometry example.

**A modern language feature achieving a similar goal more directly, extension methods and functions.** C#'s official documentation states extension methods "add" a method to an existing type "without creating a new derived type, recompiling, or otherwise modifying the original type," via a static method whose first parameter carries the `this` modifier, and states plainly, "extension methods can't access any private data in the extended class." Kotlin's own official documentation states the same idea and the same limit. "Extensions don't modify the classes or interfaces they extend," and, "if an extension is declared outside its receiver type, it can't access the receiver's private or protected members." Swift's own official language book confirms extensions "add new functionality to an existing class, structure, enumeration, or protocol type," including types "for which you don't have access to the original source code," but "can't override existing functionality" and "can't add stored properties." Rust has no extension-method keyword, but the official Rust book describes the equivalent, implementing your own trait for an external type, governed by the orphan rule, "we can't implement external traits on external types," a restriction the book states protects other people's code from breaking, and protects your own code the same way in return.

Across all four languages, the sharpest technical difference from a classic Servant is the same. a native extension mechanism cannot reach the extended type's private state, which closes off the exact failure mode this pattern otherwise creates, forcing a served class's state to be made public solely so an external servant can reach it, covered fully in dimension 11.

**A stateless Python variant.** `gslf/PythonDP` implements a `MovementServant` with a single `@staticmethod`, `move`, taking a `Shape` and delta coordinates. `faif/python-patterns`, a widely referenced Python patterns repository, implements a `GeometryTools` class with `calculate_area`, `calculate_perimeter`, and `move_to`, all `@staticmethod`, and its own docstring states the pattern's intent independently. "The Servant design pattern is a behavioral pattern used to offer functionality to a group of classes without requiring them to inherit from a base class, particularly useful in scenarios where adding the desired functionality through inheritance is impractical or would lead to a rigid class hierarchy."

**A framework-level convention resembling the pattern, static utility classes.** Oracle's own Javadoc for `java.util.Collections` states, "this class consists exclusively of static methods that operate on or return collections." Oracle's own Javadoc for `java.nio.file.Files` states, "this class consists exclusively of static methods that operate on files, directories, or other types of files." Both operate on an instance passed as a parameter, exactly the servant shape, with the served type in each case sharing a real common interface, `Collection` or `Path`, rather than the "no shared interface at all" extreme the geometry example illustrates.

## 9. Known production uses

By the pattern's specific name, the evidence is concentrated in design-pattern teaching and reference repositories rather than large production systems, and this entry states that honestly rather than upgrading a teaching repository into a production claim. `iluwatar/java-design-patterns`, a large, well-known reference catalogue, carries the most substantial implementation, and its own citation list, GoF, "Java Design Patterns, A Hands-On Experience," and POSA1, is itself the strongest lineage evidence available, covered in dimension 1. `andrei-punko/design-patterns`, `faif/python-patterns`, and `gslf/PythonDP` are further real, independently written, dated repositories implementing the pattern by name. A number of additional GitHub repositories implementing "Servant" by name were found and are reported honestly as coursework or demonstration repositories rather than production evidence, since that is what they are.

The real, citable production evidence is the mechanism rather than the name. `java.util.Collections`, `java.util.Arrays`, and `java.nio.file.Files`, all quoted directly above, are static utility classes whose methods operate on an instance passed as a parameter, shipped inside the JDK since Java 1.2, released December 1998. C#'s `System.Linq.Enumerable`, the class powering every LINQ query operator, `OrderBy`, `Where`, `GroupBy`, across any type implementing `IEnumerable`, is architecturally the same shape, confirmed directly by Microsoft's own documentation, which states, "the most common extension members are the LINQ standard query operators that add query functionality to the existing System.Collections.IEnumerable and System.Collections.Generic.IEnumerable of T types." This entry's honest conclusion, by name the pattern is mainly a teaching artifact, by mechanism it is genuinely ubiquitous in shipped standard libraries.

## 10. Consequences

Positive, quoted directly from `iluwatar/java-design-patterns`'s own "Benefits and Trade-offs" section. "Promotes code reuse and separation of concerns by decoupling the operations from the objects they operate on," and, "reduces code duplication by centralizing the shared functionality."

Negative, from the same source. "Can lead to an increase in the number of classes, potentially making the system harder to understand," and, "may introduce tight coupling between the Servant and the classes it serves if not designed carefully." A further, independently sourced critique applies to the pattern's most common real implementation shape, a stateless static-method class, since multiple sources here converge on treating Servant and the general utility-class idiom as the same thing when implemented this way. Yegor Bugayenko's own published critique of static utility classes states directly, "utility classes are not proper objects, therefore they don't fit into object-oriented world," arguing the pattern encourages a procedural mindset that "contradicts OOP's philosophy that there are only objects and their behavior," and names a concrete maintenance cost, "it is much easier to develop, maintain and unit-test class FileLines rather than using a readLines method in a large utility class."

## 11. Failure modes and misuse

**Reaching for a servant when the served classes genuinely share meaningful, cohesive behavior.** If several classes are not merely "can be repositioned" but share a real, ongoing behavioral contract, a UI widget lifecycle, for example, pulling that into an external servant instead of a proper shared interface or base class discards real polymorphic dispatch for no benefit, replacing `widget.render()` everywhere with `servant.render(widget)`, and the manual `isinstance`-style branching confirmed directly in `faif/python-patterns`'s own `GeometryTools.calculate_area` is the concrete cost of that choice, a runtime type check standing in for what a compiler-enforced virtual call would otherwise provide for free.

**The servant becoming a God class.** Wikipedia's own God object article defines the risk directly, an entity that "references a large number of distinct types, has too many unrelated or uncategorized methods, or some combination of both," which "violates the fundamental programming technique of separating a large problem into several smaller problems," and creates tight coupling because "the other objects within the program rely on the single god object." Since a servant's entire purpose is accumulating cross-cutting operations for a group of classes, an unbounded or badly scoped one, an `AppUtils` or `Helper` class that keeps absorbing unrelated new capabilities because "there is already a place for shared stuff," is a direct, well-documented path to exactly this failure.

**Exposing internal state solely so the servant can reach it.** This is the direct, sourced consequence of the pattern's own mechanism. the `Movable` interface confirmed in dimension 5 exists purely to let `MoveServant` reach `Position`, adding public `getPosition` and `setPosition` to every shape class that would otherwise have no reason to expose a mutable position setter publicly. Dimension 8's own finding, that native extension mechanisms in C#, Kotlin, and Swift are all explicitly barred from private state, sharpens this failure mode by contrast, a hand-rolled servant has no equivalent guardrail, so widening a served class's public surface purely to accommodate the servant is a real and easy mistake, not a theoretical one.

**The general utility-class anti-pattern critique applies directly.** Baeldung's own guide to mocking static methods states the mechanism plainly, "a class depending on a static method has tight coupling, and second, it nearly always leads to code that is difficult to test," a critique covered fully as a testing concern in dimension 15, and one that transfers wholesale to most real Servant implementations found in this research, since nearly all of them, the Python `@staticmethod` examples and the framework utility classes alike, use exactly this static shape.

## 12. Trade-off matrix

| Force | Servant, external helper | Shared interface or base class | Free or non-member functions, C++ | Extension methods or functions |
|---|---|---|---|---|
| Requires modifying served classes | Usually yes, served classes typically implement a minimal interface just for the servant's benefit, or expose public accessors it needs | Yes, substantially, must implement the interface or inherit the base | No, operates through the class's already-public interface | No, added externally without touching the original type |
| Encapsulation impact | Negative, served state must be public enough for the servant to reach, confirmed by the Movable interface example | Neutral to positive if the shared behavior belonged in the contract anyway | Positive by design, a widely cited secondary summary of Effective C++ Item 23 states, "the more functions that can access data, the less the data is encapsulated," and a non-member non-friend function does not add to that count | Positive, and enforced by the language, confirmed directly, C# and Kotlin both state an extension cannot reach the extended type's private or protected members |
| Polymorphism support | None, dispatch beyond the shared interface is manual, confirmed directly by faif's own isinstance branching | Full, true virtual dispatch per type | None inherently, though overloading can approximate it at compile time | None inherently, dispatch is resolved at compile time against the declared receiver type |
| Works across classes with zero common ancestor | Yes, this is the pattern's reason to exist | No, by definition requires a common type | Yes | Yes, within one language's own type system |

No source found builds this exact four-way comparison. It is assembled here from the individually sourced facts quoted throughout this entry plus ordinary engineering reasoning, and is presented as such.

## 13. Related and incompatible patterns

**Command, the one relationship a source states explicitly.** Wikipedia's own Servant article states directly, "the Command pattern is similar but approaches problems differently, Command passes command objects to modify functionality, while Servant passes serviced objects to provide functionality." This is the strongest, most directly sourced relationship in the entire entry.

**Visitor, structurally the closest sibling, but with no source drawing the comparison by name.** Wikipedia's own Visitor article confirms the shared goal, letting new operations be added to a family of classes "without modifying the structures," but the mechanism differs completely, Visitor uses double dispatch through an `accept` method each served class must implement, while a servant requires no cooperation from the served class beyond a minimal interface or public accessors. No source found compares the two directly by name, and this entry states plainly that the comparison offered here is its own engineering judgement, not a sourced fact.

**Adapter, Strategy, Facade, and View Helper, each named directly by iluwatar's own README.** "The Servant pattern is similar to the Adapter pattern in that both provide a way to work with classes without modifying them, but the Servant pattern focuses on providing additional behavior to multiple classes rather than adapting one interface to another." "The Servant pattern can be used in conjunction with the Strategy pattern to define operations that apply to multiple classes," a connection this entry treats as sourced but thin, since Strategy's own purpose, selecting an interchangeable algorithm at runtime, is a different problem from Servant's. "Both patterns provide a simplified interface to a set of functionalities, but the Servant pattern is typically used for adding functionalities to a group of classes, while the Facade pattern hides the complexities of a subsystem," distinguishing it from Facade. And a further, more loosely related idea, "View Helper," "is related as it also centralizes common functionality, but it focuses on separating presentation logic from business logic in web applications."

**The general utility or helper class idiom.** Multiple independent sources, the `iluwatar` frontmatter's own "Also known as, Helper," and a separate pattern-catalogue repository's own comment describing Servant as "also frequently called helper class or utility class implementation," converge on treating this pattern and the utility-class idiom as the same shape whenever the servant is stateless with static methods, which dimension 9 confirms is the dominant real implementation style found.

## 14. Refactoring path in and out

**Refactoring in, from the same method duplicated across several unrelated classes.** When several classes each hand-write their own copy of the same operation, the sourced refactor is direct, extract a minimal interface covering only what the shared operation needs, `Movable`'s `getPosition` and `setPosition` in the geometry example, move the duplicated logic into a new servant class whose method takes that interface as a parameter, and delete the duplicated method from each class. `andrei-punko/design-patterns`'s own `MoveServant` and `iluwatar`'s own restaurant `Servant` are two independently written instances of exactly this refactor, applied to two different domains.

**Refactoring out, toward a native extension mechanism when the host language has one.** Dimension 8 already showed C#, Kotlin, and Swift each offering a language-native alternative that reaches the same "add behavior without touching the type" goal while additionally protecting the extended type's private state, a guarantee no hand-rolled servant provides on its own. Refactoring a hand-rolled servant into extension methods is a straightforward mechanical move whenever the served classes already live in a language with that feature, converting each servant method's first parameter into the extension's receiver.

**Refactoring out, toward a real shared interface, when the served classes turn out to share more than one operation.** If a second, third, and fourth shared operation accumulate on the same servant over time, that accumulation is itself the God-class warning sign named in dimension 11, and the correct refactor at that point is often the reverse of "refactoring in," pull the now-multiple shared operations into a proper interface the served classes implement directly, restoring real polymorphic dispatch in place of the servant's own manual type-checking.

## 15. Testing and verification

The clearest, best-sourced testing concern follows directly from dimension 9's own finding that the dominant real implementation style is a stateless class of static methods. Baeldung's own guide states the mechanism plainly, "a class depending on a static method has tight coupling, and second, it nearly always leads to code that is difficult to test," and notes that before Mockito 3.4.0, mocking a static method required a separate tool, PowerMockito, entirely. Applied to a servant specifically, this entry's own reasoning, not a source's direct claim, a class that internally calls `MoveServant.moveTo(shape, pos)` cannot easily substitute a fake servant in a unit test unless the servant is passed in as an injected dependency, which most of the sourced real implementations do not do, they call the servant directly or via a static reference.

The instance-based, client-knows-servant variant sidesteps this specific problem, since an injected servant instance can be swapped for a test double the same way any other collaborator can. Testing the served side is comparatively simple regardless of variant, since the servant only ever reaches the served object through its public interface, so a test can construct a real or fake object satisfying that interface and assert on its state after the servant call, without needing to know anything about the servant's own internals.

## 16. Observability signals

No source found discusses runtime observability for this pattern by name, and this entry states that gap directly rather than inventing a citation. One concrete signal follows from the God-class failure mode in dimension 11. tracking the number of distinct served types a single servant class's methods accept, over time, is a cheap, direct proxy for exactly the accumulation risk that failure mode names, a servant whose method count or accepted-type count keeps growing across releases is a visible, measurable version of the same warning a code reviewer would otherwise have to notice by eye.

## 17. Security and privacy implications

No source found ties this pattern by name to a specific security advisory or vulnerability. The clearest, sourced-adjacent concern is a general one about static, shared code paths under concurrent access. Microsoft's own official .NET threading guidance states directly, "avoid providing static methods that alter static state. In common server scenarios, static state is shared across requests, which means multiple threads can execute that code at the same time. This opens up the possibility of threading bugs," and defines a race condition as "a bug that occurs when the outcome of a program depends on which of two or more threads reaches a particular block of code first."

Applied to a servant specifically, this entry's own reasoning, most real servant implementations found here, `MoveServant`, `GeometryTools`, `MovementServant`, hold no state of their own, which sidesteps the exact static-state hazard the Microsoft guidance names. The real risk sits one level over, in the served object's own state rather than the servant's. because a servant method mutates the served instance's public state directly, `serviced.setPosition(where)` in the sourced example, two threads calling the same servant method on the same shared served instance concurrently produce an ordinary, unsynchronized read-modify-write race on that instance, no different in kind from any other externally mutated shared object, but arguably easier to introduce by accident with a servant, since the mutation happens one call site away from the served class's own definition rather than inside a method a reader would naturally associate with that state.

## 18. References

1. Wikipedia, Design Patterns, https://en.wikipedia.org/wiki/Design_Patterns, verified 2026-08-23.
2. Wikipedia, Servant, design pattern, https://en.wikipedia.org/wiki/Servant_(design_pattern), verified 2026-08-23.
3. Wikipedia, Software design pattern, https://en.wikipedia.org/wiki/Software_design_pattern, verified 2026-08-23.
4. Wikipedia, God object, https://en.wikipedia.org/wiki/God_object, verified 2026-08-23.
5. iluwatar, java-design-patterns, servant module README, https://github.com/iluwatar/java-design-patterns/blob/master/servant/README.md, verified 2026-08-23.
6. andrei-punko, design-patterns, behavioral.servant package, https://github.com/andrei-punko/design-patterns/tree/master/src/main/java/behavioral/servant, verified 2026-08-23.
7. faif, python-patterns, servant.py, https://github.com/faif/python-patterns/blob/master/patterns/behavioral/servant.py, verified 2026-08-23.
8. gslf, PythonDP, Behavioral, Servant, https://github.com/gslf/PythonDP/blob/main/Behavioral/Servant/README.md, verified 2026-08-23.
9. Microsoft Learn, Extension members, C sharp, https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/extension-methods, verified 2026-08-23.
10. Kotlin documentation, Extensions, https://kotlinlang.org/docs/extensions.html, verified 2026-08-23.
11. The Swift Programming Language, Extensions, https://docs.swift.org/swift-book/documentation/the-swift-programming-language/extensions/, verified 2026-08-23.
12. The Rust Programming Language, Traits, https://doc.rust-lang.org/book/ch10-02-traits.html, verified 2026-08-23.
13. Oracle, java.util.Collections javadoc, https://docs.oracle.com/javase/8/docs/api/java/util/Collections.html, verified 2026-08-23.
14. Oracle, java.nio.file.Files javadoc, https://docs.oracle.com/javase/8/docs/api/java/nio/file/Files.html, verified 2026-08-23.
15. Baeldung, Guide to the Java Arrays Class, https://www.baeldung.com/java-util-arrays, verified 2026-08-23.
16. Yegor Bugayenko, OOP Alternative to Utility Classes, https://www.yegor256.com/2014/05/05/oop-alternative-to-utility-classes.html, verified 2026-08-23.
17. Baeldung, Mocking Static Methods With Mockito, https://www.baeldung.com/mockito-mock-static-methods, verified 2026-08-23.
18. Microsoft Learn, Managed Threading Best Practices, dot NET, https://learn.microsoft.com/en-us/dotnet/standard/threading/managed-threading-best-practices, verified 2026-08-23.
19. Wikipedia, Visitor pattern, https://en.wikipedia.org/wiki/Visitor_pattern, verified 2026-08-23.
20. mgp, book-notes, Effective C++ 3rd edition, Item 23, https://github.com/mgp/book-notes/blob/master/effective-c%2B%2B-3rd-edition.markdown, verified 2026-08-23.

**Evidence grade.** mixed

**Most solid findings.** The GoF exclusion, confirmed directly against Wikipedia's own contents listing, alongside the honestly reported internal contradiction in a separate Wikipedia comparison table. The two structural variants and the Command-pattern comparison, both quoted directly from Wikipedia's own dedicated article. The real, working Java, C#, Kotlin, Swift, Rust, and Python implementations, each fetched and quoted directly. The native-extension-cannot-reach-private-state limit, independently confirmed across three separate official language documentation sources, C#, Kotlin, and Swift. iluwatar's own benefits, trade-offs, and related-patterns lists, fetched and quoted directly.

**Unverified or unclear.** The only cited academic source for the pattern's origin, Pecinovsky, Pavlickova, and Pavlicek 2006, was never independently read, only confirmed to exist as Wikipedia's citation. The reference to McConnell's "Code Complete" in the same comparison table was not independently checked against the book's actual pages. The Servant-to-Visitor comparison in dimension 13 is this entry's own reasoning, no source draws that connection by name, despite the two patterns sharing an obvious goal. Scott Meyers' own original "How Non-Member Functions Improve Encapsulation" text could not be directly fetched, the Item 23 quote used here is drawn from a secondary summary of the same argument in his book, not from the original article itself, and this entry states that distinction plainly. No source was found arguing this pattern has become more or less relevant given modern extension-method language features, in either direction, despite a deliberate search for exactly that claim.

## Code

```typescript
// The minimal shared interface. shapes implement this purely so the
// servant can operate on them, not because they share real behavior.
interface Movable {
  getPosition(): { x: number; y: number };
  setPosition(p: { x: number; y: number }): void;
}

// The servant. holds no state of its own, its methods take the served
// object as a parameter, matching the Wikipedia MoveServant shape.
class MoveServant {
  moveTo(shape: Movable, where: { x: number; y: number }): void {
    shape.setPosition(where);
  }

  moveBy(shape: Movable, dx: number, dy: number): void {
    const current = shape.getPosition();
    shape.setPosition({ x: current.x + dx, y: current.y + dy });
  }
}

// Three unrelated served classes, sharing nothing but Movable.
class Triangle implements Movable {
  private position = { x: 0, y: 0 };
  getPosition() {
    return this.position;
  }
  setPosition(p: { x: number; y: number }) {
    this.position = p;
  }
}

class Ellipse implements Movable {
  private position = { x: 0, y: 0 };
  getPosition() {
    return this.position;
  }
  setPosition(p: { x: number; y: number }) {
    this.position = p;
  }
}

const servant = new MoveServant();
const triangle = new Triangle();
const ellipse = new Ellipse();

servant.moveTo(triangle, { x: 5, y: 9 });
servant.moveBy(ellipse, 2, 5);

console.log(triangle.getPosition());
console.log(ellipse.getPosition());
```

```python
# The same shape in Python, using the abc module for the shared interface
# and a stateless servant with plain functions, following the shape of
# the faif/python-patterns and gslf/PythonDP implementations.
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Position:
    x: float
    y: float


class Movable(ABC):
    @abstractmethod
    def get_position(self) -> Position: ...

    @abstractmethod
    def set_position(self, p: Position) -> None: ...


class MoveServant:
    @staticmethod
    def move_to(shape: Movable, where: Position) -> None:
        shape.set_position(where)

    @staticmethod
    def move_by(shape: Movable, dx: float, dy: float) -> None:
        current = shape.get_position()
        shape.set_position(Position(current.x + dx, current.y + dy))


class Triangle(Movable):
    def __init__(self) -> None:
        self._position = Position(0, 0)

    def get_position(self) -> Position:
        return self._position

    def set_position(self, p: Position) -> None:
        self._position = p


class Ellipse(Movable):
    def __init__(self) -> None:
        self._position = Position(0, 0)

    def get_position(self) -> Position:
        return self._position

    def set_position(self, p: Position) -> None:
        self._position = p


triangle = Triangle()
ellipse = Ellipse()

MoveServant.move_to(triangle, Position(5, 9))
MoveServant.move_by(ellipse, 2, 5)

print(triangle.get_position())
print(ellipse.get_position())
```

```go
package main

import "fmt"

// Go has no inheritance and no classes, so the served-side interface is
// the whole story here, satisfied implicitly by any type with matching
// methods. no shared base type exists among Triangle and Ellipse.
type Movable interface {
	Position() (float64, float64)
	SetPosition(x, y float64)
}

// The servant. plain functions taking the served value as a parameter,
// the same shape as MoveServant, expressed without a receiver type
// since Go has no static-method concept distinct from a free function.
func MoveTo(shape Movable, x, y float64) {
	shape.SetPosition(x, y)
}

func MoveBy(shape Movable, dx, dy float64) {
	x, y := shape.Position()
	shape.SetPosition(x+dx, y+dy)
}

type Triangle struct {
	x, y float64
}

func (t *Triangle) Position() (float64, float64) {
	return t.x, t.y
}

func (t *Triangle) SetPosition(x, y float64) {
	t.x, t.y = x, y
}

type Ellipse struct {
	x, y float64
}

func (e *Ellipse) Position() (float64, float64) {
	return e.x, e.y
}

func (e *Ellipse) SetPosition(x, y float64) {
	e.x, e.y = x, y
}

func main() {
	triangle := &Triangle{}
	ellipse := &Ellipse{}

	MoveTo(triangle, 5, 9)
	MoveBy(ellipse, 2, 5)

	fmt.Println(triangle.Position())
	fmt.Println(ellipse.Position())
}
```
