---
name: Twin
slug: twin
family: 01-design-patterns-gof
category: Structural
aliases: []
first_described: "Hanspeter Moessenboeck, Twin, A Design Pattern for Modeling Multiple Inheritance, University of Linz, presented at PSI 99, published in Perspectives of System Informatics, LNCS volume 1755, Springer, 2000, pages 358 to 369"
maturity: contested
related: [adapter, bridge, decorator]
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

Twin has no alternative name in real use. The pattern was described by Hanspeter Moessenboeck of the University of Linz in a 1999 paper titled "Twin, A Design Pattern for Modeling Multiple Inheritance," presented at the Third International Andrei Ershov Memorial Conference (PSI 99) in Novosibirsk and later published in the conference proceedings, Lecture Notes in Computer Science volume 1755, pages 358 to 369, DOI 10.1007/3-540-46562-6_31. The paper's own abstract states its intent plainly, that it introduces "an object-oriented design pattern called Twin that allows us to model multiple inheritance in programming languages that do not support this feature (e.g. Java, Modula-3, Oberon-2)."

An honest note the family folder for this entry cannot avoid stating. Twin is not one of the twenty three patterns catalogued by Gamma, Helm, Johnson, and Vlissides in Design Patterns, published in 1994 to 1995. Moessenboeck's own abstract says his paper deliberately follows "the form of the design pattern catalogue" from that book, meaning Twin imitates the GoF documentation structure, Intent, Motivation, Applicability, Structure, and so on, without being one of the GoF book's own patterns. It sits in this repository's family 01 folder because that folder groups patterns written in the classic GoF catalogue style, not because Twin was one of the original twenty three.

Maturity is judged here as contested rather than canonical or established. Semantic Scholar records only four citations of the original paper across more than two decades, a low number for a design-pattern paper this old. Three widely used secondary pattern catalogues, SourceMaking, Refactoring Guru, and OODesign, list the Gang of Four patterns plus a handful of well known extras such as Null Object and Object Pool, and none of the three lists Twin at all. Against that, the pattern does have a real, peer reviewed, DOI bearing origin, a standalone Wikipedia article, and a maintained reference implementation in the iluwatar/java-design-patterns catalogue, a project with more than ninety thousand stars on GitHub. The honest read is a real, named, sourced technique that never reached mainstream adoption in the pattern literature, closer to a documented curiosity than to a pattern every senior engineer would recognise by name.

## 2. Problem and context

A designer working in a single inheritance language sometimes needs one conceptual object to behave as two unrelated, already existing base types at once, each carrying its own real state, not just its own method signatures. Moessenboeck's own motivating example, restated here in different words rather than quoted, is a simple video game. A `GameItem` base class provides the drawing and collision behaviour every visible object on screen shares. A `Ball` needs that behaviour. It also needs to run on its own independent schedule, checking for collisions and moving itself every few milliseconds, which in Java means it needs to be a `Thread`. Java allows a class to extend exactly one class. `Ball` cannot extend both `GameItem` and `Thread`.

The problem only bites when both parent types are concrete classes carrying their own fields, not interfaces. If the shared code were pure behaviour with no stored state, a Java interface, or later a default method, would settle the question without any pattern at all. The problem context for Twin is specifically two already fixed, already stateful base classes that a single new type needs simultaneously, in a language whose class hierarchy allows only one parent per class.

## 3. Forces

Most of the reasoning here is engineering judgement about which pressure the pattern favours, stated plainly as judgement rather than as settled fact.

The dominant tension is reuse against language constraint. The designer wants one conceptual entity to answer to two separate protocols, but the language permits inheriting the implementation of only one. Twin resolves this by trading inheritance for composition, and Moessenboeck's own paper names the resulting cost directly, that message forwarding between the two halves "is less efficient than inheritance," offset in the same sentence by the observation that multiple inheritance itself already carries overhead relative to single inheritance, citing Bjarne Stroustrup's 1989 paper on multiple inheritance in C++.

A second force is encapsulation against necessary coupling. The two halves of a twin pair are not really independent objects, they are one logical unit that has been split into two files to satisfy the compiler. Moessenboeck's paper states the two partner classes "have to access each other's private fields and methods," which in Java is resolved by placing both classes in a shared package and using package private visibility, deliberately relaxing the encapsulation that would otherwise separate two unrelated classes.

A third force, confirmed independently by both the pattern's own Wikipedia article and by a working implementation of the pattern in the logic language Logtalk, is that the mutual reference between the two twins forms a genuine reference cycle. Wikipedia's article states plainly that some languages "may require such cyclic references to be handled specially to avoid a memory leak," and Logtalk's own official example notes that the same cycle "prevents some static binding optimizations." Twin favours getting the multiple inheritance effect at all, and it sacrifices the clean, acyclic object graph a single object would have had.

## 4. Applicability and non-applicability

Reach for Twin when a single design honestly needs the fields and behaviour of two already existing, already concrete base classes at once, in a language that permits only one parent class per type, and when the two protocols are addressed independently by different callers, for example a game loop calling an object as a `GameItem` while a scheduler calls the same conceptual object as a `Thread`. Moessenboeck's own Applicability section, quoted directly from the paper, names two uses. "To simulate multiple inheritance in a language that does not support this feature," and "to avoid certain problems of multiple inheritance such as name clashes."

Do not reach for Twin in several situations the pattern's own literature and its surrounding language ecosystem make clear.

Do not use it when the shared behaviour carries no state of its own. A Java interface, and since Java 8 a default method on that interface, gives multiple inheritance of behaviour without any of Twin's mutual reference cost, because interfaces carry no fields. Oracle's own Java Tutorials state that default methods "introduce one form of multiple inheritance of implementation," precisely the case where Twin is unnecessary.

Do not use it when the language already offers native, purpose built delegation to an interface. Kotlin's own documentation for its `by` keyword states that "the compiler will generate all the methods" that forward to a delegated implementation, "requiring zero boilerplate code," which is exactly the hand written forwarding logic Twin requires the author to write by hand in Java or C#.

Do not use it in a language whose idiomatic answer to inheritance is composition rather than a class hierarchy at all. The Rust Programming Language book states outright that Rust "has chosen a different set of trade offs by not offering inheritance," which means the situation that motivates Twin, one class needing to extend two others, never arises in idiomatic Rust in the first place.

Do not use it when a single, one directional delegation would satisfy the actual requirement. If the second type never needs to be independently addressed by an outside caller under its own name, plain composition with no back reference is simpler and carries none of Twin's cyclic reference cost.

## 5. Structure

The pattern splits what would be one multiply inheriting class into two sibling classes, each with a single, ordinary parent, connected by a mutual reference.

Participant, first parent. The first already existing base class the design needs to inherit from, for example `GameItem`.

Participant, second parent. The second already existing base class the design needs to inherit from, for example `Thread`.

Participant, first twin. A new subclass of the first parent. It carries a reference field pointing at the second twin, implements the behaviour that genuinely belongs to the first parent's protocol, and forwards any call that belongs to the second parent's protocol to its twin through that reference.

Participant, second twin. A new subclass of the second parent, structured the same way in reverse, carrying a reference back to the first twin.

Moessenboeck's paper names this pair, in the worked example, `Child1` and `Child2`, each linked to the other "via fields." The iluwatar reference implementation names the same shape `BallItem`, extending `GameItem`, and `BallThread`, extending `Thread`, each holding a `twin` field pointing at the other, wired together after construction by two separate setter calls.

## 6. ASCII structure diagram

```
        Parent1                    Parent2
       (GameItem)                  (Thread)
           ^                           ^
           |  extends                  |  extends
           |                           |
       Child1 (BallItem) <---twin---> Child2 (BallThread)
           |                           |
     handles GameItem            handles Thread
     protocol calls,             protocol calls,
     forwards Thread             forwards GameItem
     calls to twin               calls to twin
```

## 7. Dynamics

Construction happens in two steps, always outside the two twin classes themselves, because neither twin can be fully built without a reference to a partner that does not exist yet at its own construction time. First both twins are constructed independently, each as an ordinary instance of its own single parent. Second, the two references are wired together, one call setting the first twin's reference to the second, a separate call setting the second twin's reference back to the first. Moessenboeck's own paper mitigates the resulting risk of wiring only one side by recommending a single static factory method that constructs both halves and links them in one place, rather than leaving two separate setter calls to whichever code assembles the pair.

At runtime, each twin receives calls addressed to its own parent type and answers them directly using its own state. When a caller invokes something that belongs to the other parent's protocol, the twin that received the call forwards it through its reference field to its partner, which answers using its own, separately held state. In the canonical worked example, a caller treating the object as a `GameItem` calls `click()` on the `BallItem` twin, which toggles a suspended flag and calls `suspendMe()` or `resumeMe()` on its `BallThread` twin through the reference. Separately, the scheduler drives the `BallThread` twin as an ordinary `Thread`, and inside its own run loop that twin calls `draw()` and `move()` back on the `BallItem` twin through the same reference, in the opposite direction. Nothing in the language enforces that both directions of forwarding stay correct, the discipline is entirely the responsibility of whoever wrote the two twin classes.

## 8. Implementation variants

The reference implementation almost everyone points to is the `twin` module of iluwatar/java-design-patterns, a catalogue with more than ninety thousand GitHub stars. `BallItem` extends the abstract `GameItem`, `BallThread` extends `java.lang.Thread`, each holds a private `twin` field set through a plain setter, and the two are wired together in the sample application's own `main` method with two separate calls, `ballItem.setTwin(ballThread)` followed by `ballThread.setTwin(ballItem)`.

An independently written C sharp example, in a small personal study repository by the GitHub user kurtosmate, applies the same shape to an unrelated domain, a `BananaFloweringPlant` twin extending a `FloweringPlant` base and a `BananaFruit` twin extending a `Fruit` base, each holding a typed property pointing at the other and forwarding a `Ripe` or `Flowering` call across. The repository is small and unmaintained, worth noting honestly as a study example rather than a production one, but it confirms the pattern's shape is not tied to Java or to the original game example, since C sharp shares Java's single class inheritance constraint.

The most structurally different variant found is in Logtalk, an object oriented language layered on Prolog that, unlike Java, already supports native multiple inheritance. Logtalk's own official example implements Twin using dynamic message forwarding rather than hand written delegate methods, an object declares `implements(forwarding)` and defines a single `forward(Message)` predicate that redirects any message it does not itself handle to its twin, with no per method boilerplate at all. The example's own notes state a reason to still reach for Twin even in a language with real multiple inheritance, that "with categories, each category protocol adds to the protocol of the object" while "this pattern each object must use message forwarding to its twin object," a genuine, sourced, alternative trade off rather than a language limitation being worked around.

Three modern language features narrow, without eliminating, the case for Twin. Java's own default methods, added in Java 8, give a class the ability to inherit method bodies from more than one interface, but Oracle's own tutorial is explicit that this covers "multiple inheritance of implementation," never of state, so it does not help when the two parents genuinely carry their own fields, as `Thread` does. Kotlin's `by` keyword removes the hand written forwarding methods entirely when delegating to a single interface, the compiler generating every forwarding method itself, but it still delegates to an interface implementation held in one field, it does not let a class extend two concrete classes at once, so it answers a narrower version of the problem than the one Twin was built for. C plus plus supports genuine multiple inheritance directly, so the base case needs no pattern at all, but Microsoft's own C plus plus documentation shows the cost has not disappeared, only moved, into name ambiguities that require an explicit `Base::member()` call to resolve and into duplicated subobjects that require declaring a base class `virtual` to avoid.

## 9. Known production uses

The honest finding here is that no real production system was found using Twin by name. This is stated plainly rather than smoothed over with a vague claim, because the template's own standard for this dimension rejects exactly that kind of vagueness.

Moessenboeck's own paper describes two applications of the pattern, and labels the first of them himself as a teaching exercise, not production code, that the ball game example "was implemented as a teaching exercise in Oberon-2." His second example applies Twin to a Java `Applet` needing behaviour from both `Applet` and a hypothetical mouse listener base class, presented as the author's own demonstration of the technique, not as evidence that any real applet codebase, or Sun's own AWT team, used Twin internally. The same section of the paper goes on to compare this demonstration against an alternative solution using Java inner classes, and finds the inner class approach preferable in part of the comparison, which is itself a sign the paper's own author did not consider Twin the obviously superior real world answer to that specific case.

The iluwatar catalogue's own "Real World Applications" section for Twin names no system at all, listing only generic categories such as "User interfaces where different frameworks are used for rendering and logic." By this repository's own rule that unnamed production usage does not count as evidence, that line is recorded here as an absence, not as a citation.

A search of GitHub code for the exact phrase "twin design pattern" returns almost exclusively direct copies of the iluwatar catalogue entry itself, plus a large volume of unrelated results for the different, unrelated concept of a digital twin in Internet of Things and simulation contexts, a genuine term collision worth naming so it is not mistaken for evidence of this pattern's use. Baeldung, a major Java reference site that covers most Gang of Four patterns and a number of non GoF ones, has no page on Twin at all, confirmed by a direct request to the URL its own naming convention would predict, which returns a not found response. Twin should be read, honestly, as a documented, named technique with a real academic origin and a real teaching catalogue entry, and no verified production system carrying its name.

## 10. Consequences

Positive.

The pattern gets the effect of multiple inheritance in a language that forbids it, without the name clash problem that true multiple inheritance introduces when two parents declare a member with the same name, a problem Moessenboeck's own abstract names as one of the things Twin specifically avoids.

Each twin can be developed, and as covered in dimension 15, tested, largely independently of its partner, since the only thing one twin needs to know about the other is the shape of the reference it forwards calls through.

The mechanism extends past two parents. Moessenboeck's own Consequences section states that "the Twin pattern can be extended to more than two parent classes in a straightforward way," each additional parent gaining its own child class mutually linked to the others, though the same section adds that this is "considerably more complex than multiple inheritance" and notes it is rare in practice for a class to need more than two parents at once.

Negative.

Moessenboeck's own paper states the efficiency cost directly, that composition and forwarding "is less efficient than inheritance." The same paper offsets this by noting multiple inheritance itself already carries overhead, citing Stroustrup's 1989 paper on C plus plus, so the added cost of Twin specifically is smaller than the total cost of multiple inheritance would have been.

The two twin classes cannot stay properly encapsulated from each other. Moessenboeck states they "have to access each other's private fields and methods," resolved in Java by placing both in a shared package with relaxed, package private visibility, meaning the two classes are, in truth, one logical unit split across two files rather than genuinely independent units.

The mutual reference forms a real cycle. Wikipedia's article on the pattern states that some languages "may require such cyclic references to be handled specially to avoid a memory leak," for example by making one of the two references weak so the cycle can break during garbage collection.

Subclassing a twin pair is awkward. Moessenboeck's own Consequences section addresses this directly, stating that if a twin needs to be subclassed further, "it is often sufficient to subclass just one of the partners," but that solution leaves the resulting subclass compatible with only that one partner's protocol, not both, and making the subclass compatible with both again requires reapplying Twin one level deeper.

## 11. Failure modes and misuse

The failure mode with the strongest direct sourcing is a memory leak from the mutual reference cycle. Wikipedia's article states the risk in general terms, that the pattern "causes a cyclic reference scenario" some languages "may require" special handling to avoid a leak. In a language with a reference counting garbage collector, two objects that reference only each other, and nothing else, can hold each other alive indefinitely even after every outside reference to the pair is gone, because each object still counts as referenced by its partner. The symptom a reader would actually see is a twin pair that is logically dead, no longer reachable from application code, that nonetheless never gets collected.

A second, more subtle failure comes from state drift between the two twins. Nothing in the pattern's own mechanism keeps a twin's mirrored copy of shared state synchronised with its partner's. In the canonical implementation, `BallItem` tracks its own suspended flag and `BallThread` tracks its own suspended and running flags separately, kept consistent only by the discipline of always going through the paired forwarding calls. Nothing stops a caller from mutating one side directly and bypassing the forwarding call entirely, which desynchronises the pair. This is stated here as engineering judgement drawn from reading the reference implementation's own source, not as a claim any source states outright in this vocabulary.

A third failure is incomplete wiring at construction time. Both twin references are set through two separate, ordinary calls, with nothing in the type system checking that both sides actually got linked, or linked to the correct partner. Moessenboeck's own paper anticipates exactly this risk by recommending a single factory method that constructs and links both halves together, rather than leaving the wiring to whatever code happens to assemble the pair.

The clearest misuse case is reaching for Twin when the actual requirement did not need two independently addressable, dual identity objects at all. Kotlin's own delegation feature exists precisely because the far more common real case, one class reusing another's interface shaped behaviour with no requirement that the result be two separately typed objects, is served far more simply by ordinary one directional delegation. Standing up a full Twin pair, with its manual bidirectional wiring and its permanent reference cycle, for a problem that plain composition would have solved, is over engineering the solution to a simpler problem than the one the pattern was built for.

## 12. Trade-off matrix

Every underlying fact in this table traces to a citation already given above. The comparative ratings, low, medium, and high, are this entry's own synthesis of those facts into a single comparison, not independently sourced numbers, stated here so the reader can weigh the table accordingly.

| Approach | Language support needed | Cyclic reference cost | Testability | Forwarding boilerplate |
|---|---|---|---|---|
| Twin | Any single inheritance language, works even by dynamic message forwarding in Logtalk | High, a genuine mutual reference cycle, may need a weak reference to avoid a leak | Each twin mockable in isolation through its reference field, integration behaviour across both sides is harder to verify | Low, every forwarding method is hand written on both sides |
| Native multiple inheritance, for example C plus plus | A language with real multiple inheritance | None from Twin's cycle, but real diamond problem costs, name clashes needing explicit disambiguation, duplicated subobjects needing virtual base classes | A single object, single lifecycle, but disambiguated member access can itself complicate isolating one parent's behaviour | None at the call site, but declaration side complexity grows with virtual bases |
| Interface default methods, Java 8 and later | Any language with default methods, does not cover shared state, only shared behaviour | None, no back reference required | Standard interface mocking | High, no forwarding code at all, but only for the stateless subset of the problem |
| Delegation, Kotlin's `by` keyword | Kotlin or an equivalent compiler generated delegation feature, delegates to one interface, not two concrete classes | Low, a single one directional reference, no forced cycle | Substitute a fake for the delegated interface | High, the compiler writes every forwarding method itself |
| Plain one directional composition, no twin | Any object oriented language | None, no back reference at all | Simplest possible case | Highest, this is very often the correct answer instead of Twin |

## 13. Related and incompatible patterns

Adapter, specifically the two way adapter variant described in the original Gang of Four book, is the pattern Moessenboeck himself names as Twin's closest relative. His own Related Patterns section states plainly, "the Twin pattern is related to the Adapter pattern, especially to the Two-Way-Adapter described in [GHJV95], which is recommended when two different clients need to view an object differently," adding that the two way adapter "is implemented with multiple inheritance while the Twin avoids this feature." Twin can be read as a two way adapter re engineered specifically to avoid the multiple inheritance the original two way adapter relies on. This is sourced to Moessenboeck's own paraphrase of the GoF book, not independently checked against the book's own text in this entry.

Bridge shares Twin's instinct to split one design across two collaborating objects rather than one deep inheritance chain, but the two patterns solve different problems. The iluwatar catalogue's own related patterns note for Twin states, in a single line, that Bridge is "similar in decoupling abstraction from implementation, but Twin specifically avoids inheritance." Bridge deliberately separates an abstraction hierarchy from an implementation hierarchy so each can vary on its own, a design time choice, while Twin exists to let one object answer to two already fixed, already concrete parent contracts it cannot otherwise inherit from at once, a workaround forced by a language limitation.

Decorator is not directly compared to Twin in any source found for this entry, so the distinction here is reasoning, not a citation. Decorator wraps a single object to add behaviour while the wrapped object keeps its own identity and interface, whereas Twin creates two objects, each with its own distinct type and its own contract, related only by a mutual reference, with no wrapping relationship between them.

Mixin composition, as in Scala's `with` keyword, achieves a similar end through a different mechanism entirely, composing behaviour directly into one object's own type at compile time through linearization, confirmed by Scala's own tour documentation, which states that "classes can only have one superclass but many mixins." Twin achieves an equivalent effect by keeping the second protocol's behaviour in a genuinely separate object connected only by a reference, at the ordinary single inheritance level the language already supports, requiring no special language feature at all.

## 14. Refactoring path in and out

Refactoring in. Moessenboeck's own paper is itself a narrative of how a designer discovers the need for Twin, restated in different words here. The starting point is an existing inheritance hierarchy already providing shared behaviour, for example `GameItem` with concrete subclasses handling drawing and collision. A new requirement then appears, that one specific subclass also needs to behave as a `Thread` so a scheduler can drive it independently, and the two base classes it now needs are both already concrete and already fixed. The refactor splits the would be single subclass into two ordinary subclasses, one per parent, adds a mutual reference field to each, moves each responsibility to whichever side already owns the state that responsibility needs, and adds forwarding calls to reach across for anything else. Moessenboeck's paper mitigates the risk of an incomplete wiring by recommending a single factory method that builds and links both halves in one place. Martin Fowler's Extract Class refactoring, described on his own refactoring catalogue site, is the closest named, general purpose refactoring for the first part of this move, pulling a cohesive slice of a class's fields and methods into a new class, though Fowler's own worked example produces one directional delegation, not the mutual, bidirectional reference and dual concrete inheritance Twin specifically requires.

Refactoring out. Three separate paths apply depending on why the pair is no longer needed. If the split was only ever needed to reuse shared behaviour with no real shared state, migrate the shared logic onto an interface with a default method, or in Kotlin onto an interface used with the `by` keyword, and delete the forwarding class once nothing depends on it holding its own separate identity. Fowler's own catalogue names the general direction of this move Replace Superclass with Delegate, its own worked example converting a `Stack` that extends `List` into a `Stack` that holds a `List` field instead. If, on inspection, the pair never needed two separately addressable identities at all, collapse to plain one directional composition, keeping a forward reference only on the side that outside callers still need to address under its own type, and deleting the back reference entirely, which also removes the reference cycle named in dimension 11. Fowler's catalogue names Inline Class as the general inverse of Extract Class, the closest named refactoring for this direction.

## 15. Testing and verification

The iluwatar reference implementation's own test suite demonstrates the standard technique directly, and this dimension is grounded in reading that suite rather than in a source discussing Twin's testability in the abstract.

Each twin's own forwarding logic is tested in isolation by mocking its counterpart. The `BallItem` test constructs a real `BallItem`, sets a Mockito mock `BallThread` as its twin, and asserts, through an in order verification, that clicking the ball calls `suspendMe()` and `resumeMe()` on the mock in the correct sequence. This tests exactly what the pattern makes easy to test, whether one side correctly translates its own incoming calls into the right outgoing calls, without needing its partner's real, possibly slow or non deterministic behaviour.

The reverse direction is tested the same way, and here the pattern's cost shows up directly in the test itself. `BallThread`'s own test constructs a real `BallThread`, which genuinely extends `java.lang.Thread`, mocks `BallItem` as its twin, starts the real thread, and then verifies, using an "at least once" matcher rather than an exact count, that the mocked twin's `draw()` and `move()` methods were called during a fixed sleep window. Because one side of this particular pair has real, independent concurrency, the test degrades from a fast, purely logical unit test into a timing sensitive test with an explicit timeout budget and a real thread join for cleanup, a direct, sourced cost of testing a twin pair whose two halves do not share a single, simple lifecycle.

A separate integration test wires both real objects together and asserts only that the whole thing runs without throwing, deliberately shallow, since the mock based unit tests already cover the forwarding logic precisely and the integration test's only remaining job is confirming the real wiring works end to end. None of the tests in the reference implementation directly verify that the two twins' separately held state, for example their independent suspended flags, actually stay consistent under concurrent access, a real, observed gap in the canonical implementation's own coverage rather than a theoretical concern.

## 16. Observability signals

No source discussing Twin addresses observability directly, so this dimension is entirely engineering judgement, stated as such rather than dressed as a sourced fact.

The signal most specific to this pattern is a count of live twin pairs whose two halves have drifted, meaning each twin's own copy of shared state, such as a suspended or running flag, no longer agrees with its partner's. A healthy system shows this count at zero at all times, since nothing about a correctly operating pair should ever let the two sides disagree. A rising count points directly at the state drift failure mode named in dimension 11, most often a caller mutating one twin's state directly instead of going through the paired forwarding call.

A second, cheaper signal is simply the count of twin pairs currently allocated against the count of twin pairs actually reachable from application roots, which a profiler or a heap dump can surface. A persistent gap between the two, pairs that are allocated but no longer reachable except through their own mutual reference, is the direct, observable symptom of the memory leak risk named in dimensions 10 and 11, and it can be traced without any pattern specific instrumentation at all, using whatever cycle detection the runtime's own garbage collector or heap analysis tools already provide.

## 17. Security and privacy implications

No source discussing Twin addresses security or privacy, and the reasoning here is analytical rather than sourced.

The most concrete implication is the relaxed visibility the pattern forces. Moessenboeck's own paper states the two twin classes "have to access each other's private fields and methods," resolved in Java by placing both in a shared package with package private visibility. That relaxation is scoped to the pair itself, not to the wider codebase, so it does not on its own widen the attack surface beyond the two twin classes, but it does mean a reviewer auditing one twin class in isolation cannot reason about its state guarantees without also reading its partner, since the two together, not either alone, define the invariants that actually hold.

Twin carries no data handling implications of its own beyond whatever the two parent classes it wraps already carry. It introduces no new storage, no new network surface, and no new serialization boundary. Where the pattern is genuinely silent on a security concern, that silence is recorded here rather than an invented one being supplied in its place.

## 18. References

Hanspeter Moessenboeck. "Twin, A Design Pattern for Modeling Multiple Inheritance." University of Linz, Institute for Practical Computer Science. Presented at the Third International Andrei Ershov Memorial Conference, PSI 99, Novosibirsk, July 1999. Published in Perspectives of System Informatics, Lecture Notes in Computer Science volume 1755, Springer, 2000, pages 358 to 369. DOI 10.1007/3-540-46562-6_31. https://ssw.jku.at/Research/Papers/Moe99/Paper.pdf. Verified 2026-08-23.

Semantic Scholar. Paper record for DOI 10.1007/3-540-46562-6_31, citation count and bibliographic metadata. https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/3-540-46562-6_31. Verified 2026-08-23.

Wikipedia. "Twin pattern." https://en.wikipedia.org/wiki/Twin_pattern. Verified 2026-08-23.

Iluwatar. "Twin Pattern." java-design-patterns catalogue, reference implementation and accompanying test suite. https://github.com/iluwatar/java-design-patterns/tree/master/twin. Verified 2026-08-23.

Kurtosmate. "DesignPatterns," Twin module, C sharp implementation. https://github.com/kurtosmate/DesignPatterns/tree/master/DesignPatterns/Twin. Verified 2026-08-23.

LogtalkDotOrg. "logtalk3," Twin pattern example and accompanying notes. https://github.com/LogtalkDotOrg/logtalk3/tree/master/examples/design_patterns/structural/twin. Verified 2026-08-23.

Oracle. "Multiple Inheritance of State, Implementation, and Type." The Java Tutorials. https://docs.oracle.com/javase/tutorial/java/IandI/multipleinheritance.html. Verified 2026-08-23.

Kotlin. "Delegation." Kotlin documentation. https://kotlinlang.org/docs/delegation.html. Verified 2026-08-23.

Microsoft. "Multiple Base Classes." C plus plus Language Reference, Microsoft Learn. https://learn.microsoft.com/en-us/cpp/cpp/multiple-base-classes. Verified 2026-08-23.

Steve Klabnik and Carol Nichols. "What Does Object Oriented Mean," The Rust Programming Language. https://doc.rust-lang.org/book/ch18-01-what-is-oo.html. Verified 2026-08-23.

Scala documentation. "Mixin Class Composition." Tour of Scala. https://docs.scala-lang.org/tour/mixin-class-composition.html. Verified 2026-08-23.

Martin Fowler. "Extract Class." Refactoring catalogue. https://refactoring.com/catalog/extractClass.html. Verified 2026-08-23.

Martin Fowler. "Replace Superclass with Delegate." Refactoring catalogue. https://refactoring.com/catalog/replaceSuperclassWithDelegate.html. Verified 2026-08-23.

Baeldung. https://www.baeldung.com. Absence check confirming this major Java reference site carries no Twin pattern article, verified by requesting the URL its own naming convention would predict for the topic, which returns a not found response. Verified 2026-08-23.

**Evidence grade.** mixed

**Most solid findings.** The origin, author, venue, and DOI of the original paper are independently corroborated across Semantic Scholar, the primary PDF itself, and the iluwatar catalogue's own citation of the same paper, giving very high confidence in dimension 1. The consequences and applicability claims in dimensions 4 and 10 are drawn from direct quotation of the primary paper and are correspondingly solid. The absence of named production usage, dimension 9, is a well corroborated negative finding across the primary paper's own honest labelling of its examples as a teaching exercise, the iluwatar catalogue's unnamed usage list, and a direct check confirming no Baeldung coverage exists.

**Unverified or unclear.** The comparison to the Gang of Four book's own description of the Two-Way-Adapter, in dimension 13, is sourced only to Moessenboeck's paraphrase of that book, not to the book's own text directly. The judgement dimensions, forces, failure modes, observability, and security, are reasoning grounded in the sourced material rather than independently citable claims, and are labelled as such at the top of each section rather than left implicit.

## Code

TypeScript, Python, and Go each lack true single class inheritance the way Java does, but the pattern still demonstrates cleanly by modeling two base "protocols" as classes and connecting two subclass instances through a mutual reference, the same shape as the canonical Java example. Kotlin and Swift are omitted because their native delegation features, `by` and protocol extensions, solve the pattern's original motivating problem more directly than a hand rolled Twin would, as covered in dimension 8.

### TypeScript

```typescript
abstract class GameItem {
  abstract draw(): string;
}

abstract class Runner {
  abstract tick(): void;
}

class BallItem extends GameItem {
  private twin!: BallRunner;
  setTwin(twin: BallRunner): void {
    this.twin = twin;
  }
  draw(): string {
    return this.twin.isSuspended() ? "ball paused" : "ball drawn";
  }
  click(): void {
    this.twin.toggle();
  }
}

class BallRunner extends Runner {
  private twin!: BallItem;
  private suspended = false;
  setTwin(twin: BallItem): void {
    this.twin = twin;
  }
  isSuspended(): boolean {
    return this.suspended;
  }
  toggle(): void {
    this.suspended = !this.suspended;
  }
  tick(): void {
    if (!this.suspended) {
      this.twin.draw();
    }
  }
}

const item = new BallItem();
const runner = new BallRunner();
item.setTwin(runner);
runner.setTwin(item);
console.log(item.draw());
item.click();
console.log(item.draw());
```

### Python

```python
class GameItem:
    def draw(self) -> str:
        raise NotImplementedError


class Runner:
    def tick(self) -> None:
        raise NotImplementedError


class BallItem(GameItem):
    def set_twin(self, twin: "BallRunner") -> None:
        self.twin = twin

    def draw(self) -> str:
        return "ball paused" if self.twin.is_suspended() else "ball drawn"

    def click(self) -> None:
        self.twin.toggle()


class BallRunner(Runner):
    def __init__(self) -> None:
        self.suspended = False

    def set_twin(self, twin: BallItem) -> None:
        self.twin = twin

    def is_suspended(self) -> bool:
        return self.suspended

    def toggle(self) -> None:
        self.suspended = not self.suspended

    def tick(self) -> None:
        if not self.suspended:
            self.twin.draw()


item = BallItem()
runner = BallRunner()
item.set_twin(runner)
runner.set_twin(item)
print(item.draw())
item.click()
print(item.draw())
```

### Go

```go
package main

import "fmt"

type BallItem struct {
	twin *BallRunner
}

func (b *BallItem) SetTwin(r *BallRunner) {
	b.twin = r
}

func (b *BallItem) Draw() string {
	if b.twin.suspended {
		return "ball paused"
	}
	return "ball drawn"
}

func (b *BallItem) Click() {
	b.twin.suspended = !b.twin.suspended
}

type BallRunner struct {
	twin      *BallItem
	suspended bool
}

func (r *BallRunner) SetTwin(b *BallItem) {
	r.twin = b
}

func (r *BallRunner) Tick() {
	if !r.suspended {
		r.twin.Draw()
	}
}

func main() {
	item := &BallItem{}
	runner := &BallRunner{}
	item.SetTwin(runner)
	runner.SetTwin(item)
	fmt.Println(item.Draw())
	item.Click()
	fmt.Println(item.Draw())
}
```
