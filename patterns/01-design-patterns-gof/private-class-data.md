---
name: Private Class Data
slug: private-class-data
family: 01-design-patterns-gof
category: Structural
aliases: [Data Hiding, Encapsulation]
first_described: "Uncertain. Earliest attestation is SourceMaking.com, active since 2006-2007, plus a now-deleted English Wikipedia article a 2021 deletion discussion places around 2004"
maturity: contested
related: []
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

Not a Gang of Four pattern. Wikipedia's own "Design Patterns" article enumerates the GoF book's full contents, five creational patterns, seven structural, eleven behavioral, and Private Class Data appears in none of the three lists. Wikipedia's "List of software design patterns" article carries a table with an explicit "In Design Patterns" column distinguishing GoF-catalogued patterns from later community-contributed ones, and its own Structural-patterns section, which does list several other post-GoF entries such as Extension Object and Twin, still has no Private Class Data row.

The pattern's own history on Wikipedia is itself the most telling lineage evidence available. An article titled "Private class data pattern" existed and was formally deleted. The deletion log records the page removed at 14:27 UTC on 21 August 2021 by administrator Explicit, citing the "Articles for deletion" discussion as the reason. That discussion shows the article nominated for deletion on 7 August 2021 by editor Boleyn, whose stated rationale was that it did not meet Wikipedia's notability guideline, and who noted "a previous suggestion of a merge or redirect to Opaque pointer." Editor StarryGrandma commented during the discussion that the article "may have been original research on the creator's part back in 2004," which is the only source, an editor's own recollection rather than a verified timestamp, for placing the article's origin around that year. The discussion was relisted for broader input on 14 August and closed as delete exactly one week later. A live query against Wikipedia's own search API today returns zero hits for the term, and the direct article URL returns a 404, both consistent with that 2021 deletion.

The most-cited surviving source for the pattern by name is SourceMaking.com, a design-pattern reference site whose own About page states it "was created back in 2006," and whose current page footer reads "2007-2026." SourceMaking catalogues Private Class Data as a Structural pattern alongside two other well-known post-GoF community patterns it also carries, Object Pool and Null Object, which is itself a signal that the wider pattern-reference community treats all three the same way, as later additions to the canon rather than original GoF entries. SourceMaking's own page opens with a line it attributes to "Wikipedia says," a definition closely matching the phrasing preserved secondhand in the iluwatar/java-design-patterns project's own README, which quotes the identical "Wikipedia says" framing. Because the underlying Wikipedia article no longer exists, that attribution cannot be checked against the primary text today, and this entry states that gap plainly rather than treating the quoted fragment as independently verified.

The name is kept alive today mainly by iluwatar/java-design-patterns, a large, actively maintained open-source teaching repository, 94,605 GitHub stars and 27,398 forks at the time of research, whose private-class-data module has commit history on that path reaching back to at least 25 August 2020 and continuing maintenance through at least 2025. That same README lists "Data Hiding" and "Encapsulation" as alternate names, though this entry flags that framing as loosely sourced, a single source's list, and both terms are general object-oriented goals rather than precise synonyms for this one structural technique. No second, independent source was found corroborating either as a formal alias.

## 2. Problem and context

SourceMaking's own "Problem" section states the target of the pattern directly. "A class may expose its attributes, class variables, to manipulation when manipulation is no longer desirable, for example after construction. Using the private class data design pattern prevents that undesirable manipulation," and separately, "a class may have one-time mutable attributes that cannot be declared final. Using this design pattern allows one-time setting of those class attributes." The crux is that ordinary field-level access control in a language like Java, C#, or C++ only restricts callers outside the class. A field marked private is still fully writable by every method the class itself defines, so nothing stops a later maintainer from adding a setter, or from a method carelessly reassigning a field that was only ever meant to be set once, at construction.

SourceMaking's own worked example makes this concrete. A Circle class holds three fields, radius, color, and origin, and the page's own framing states plainly that these "should not change after the Circle constructor," yet marking them private alone does nothing to stop Circle's own methods from doing exactly that. final, const, and readonly keywords solve this cleanly for a field set to a single value in one place at construction, but they do not help when construction logic needs several statements to compute or validate a value before it is locked, or when a class wants to expose a coherent bundle of related fields, radius plus color plus origin, as one protected unit rather than as several separate final fields declared individually.

The `iluwatar/java-design-patterns` project's own worked example takes a different, equally concrete shape. A Stew class holds four ingredient counts as ordinary mutable fields, and its own taste method decrements those counts directly, the "before" picture of a class whose own behavior corrupts state nobody meant to be corrupted after the stew was assembled. The "after" picture, ImmutableStew, moves the same four counts into a separate StewData holder that ImmutableStew's own methods can only read, never reassign.

## 3. Forces

SourceMaking's "Discussion" section names the trade-off directly. "The private class data design pattern seeks to reduce exposure of attributes by limiting their visibility. It reduces the number of class attributes by encapsulating them in single Data object. It allows the class designer to remove write privilege of attributes that are intended to be set only during construction, even from methods of the target class." The iluwatar README states the same trade-off in its own words, under an explicit "Benefits and Trade-offs" heading. Benefits, "enhanced security, reduces the risk of unintended data corruption by encapsulating the data," "ease of maintenance, changes to the internal representation of data do not affect external code," and "improved abstraction, users interact with a simplified interface without worrying about the complexities of data management." Trade-offs, "performance overhead, additional method calls, getters and setters, can introduce slight performance overhead," and "complexity, may increase the complexity of the class design due to the additional layer of methods for data access."

Three named forces follow directly from those quotes. Encapsulation strength against boilerplate, the pattern buys a genuinely stronger guarantee, not even the owning class's own methods can mutate the data after construction, at the cost of an extra class and getter methods for every field. Immutability guarantee against flexibility, once the data object is built, changing its contents means constructing a new one, or explicitly exposing a setter for the specific fields SourceMaking's own checklist calls out as needing one, "expose each attribute that will change in further through a setter," its own published wording, quoted exactly rather than smoothed over. Performance and design complexity against safety, the added indirection and the added type are the acknowledged cost of the stronger guarantee, named plainly by iluwatar's own trade-offs list above.

## 4. Applicability and non-applicability

The iluwatar README states its own applicability guidance directly, under "When to Use the Private Class Data Pattern in Java." "When you want to protect the integrity of an object's state," "when you need to limit the visibility of the internal data of an object to prevent unintended modification," and "in scenarios where multiple classes need to share access to some common data without exposing it directly."

Neither iluwatar nor SourceMaking states an explicit list of when to skip the pattern, and this entry states that gap plainly rather than inventing one. A second, secondary reference source, softwarepatternslexicon.com, does offer concrete negative guidance, that the pattern should be avoided when a class has only one or two simple private fields, when the holder class would simply duplicate an ordinary constructor, or when a surrounding framework, an ORM or a serialization layer, requires direct field access and the extra indirection causes mapping complications. That source states outright, "this pattern is not a requirement for every class." Because this source carries less authority than SourceMaking or the iluwatar repository, this entry flags it as secondary rather than presenting it with equal weight.

A separate, directly observed signal on language fit comes from reading the iluwatar reference implementation's own code rather than from any source's stated argument. Its StewData holder is written as a Java record, a language feature that was finalized in Java 16 and gives a "final after construction, exposed only through generated accessors, no setters" shape for free, with none of the hand-written boilerplate the pattern was designed to justify. That the flagship reference implementation of this exact pattern now leans on a record for its data holder is concrete, sourced evidence that in a language with native immutable or algebraic data types, much of the pattern's manual scaffolding becomes redundant. This entry states plainly that this is its own inference from the code fetched, not a claim any source states in words, since no source located argues this point explicitly.

## 5. Structure

SourceMaking's own "Check list" lays out the structural build in five published steps, quoted exactly. "Create data class. Move to data class all attributes that need hiding." "Create in main class instance of data class." "Main class must initialize data class through the data class's constructor." "Expose each attribute, variable or property, of data class through a getter." "Expose each attribute that will change in further through a setter," the source's own wording, including its slightly non-native phrasing, reproduced as published rather than smoothed over.

Two structural roles follow from that checklist and from the real code fetched from both SourceMaking and iluwatar. The data class holds the fields that need protecting, each declared at the tightest visibility the language allows, and exposes each through a getter only, for anything meant to stay fixed after construction, with a getter plus a setter reserved for the fields the checklist's own fifth step says genuinely need to keep changing. The owner class holds a single reference to one instance of the data class, confirmed directly from iluwatar's own source, a private final StewData field, created exactly once, inside the owner's own constructor, and never reassigned afterward. This is a composition relationship, the owner holds and exclusively created the data instance, not inheritance and not a reference supplied from outside, which SourceMaking's own rendered structure description confirms directly, describing "the main class holding a reference to the extracted data class object, establishing a composition relationship."

## 6. ASCII structure diagram

```
+-------------------+          1  +-------------------+
|       Circle       |------------|     CircleData      |
+-------------------+   (owns)    +-------------------+
| - data: CircleData |             | - radius: double    |
+-------------------+             | - color: Color      |
| + area()           |             | - origin: Point     |
| + circumference()  |             +-------------------+
+-------------------+             | + getRadius()       |
                                   | + getColor()        |
                                   | + getOrigin()        |
                                   +-------------------+
```

Circle holds exactly one CircleData, created once inside its own constructor and never replaced. The composition arrow points from Circle toward CircleData, meaning CircleData's lifetime is bound to the one Circle that created it, and nothing else in the diagram holds a reference to that same instance. The asymmetry that matters visually sits inside CircleData's own method compartment, every entry is a getter, with no matching setter for radius, color, or origin, which is what separates this from an ordinary extract-a-helper-class refactor that happens to also move some fields.

## 7. Dynamics

The build sequence follows SourceMaking's own checklist step three, "main class must initialize data class through the data class's constructor," confirmed directly against iluwatar's ImmutableStew source, where the constructor's single statement, data equals new StewData with the four incoming parameters, is the only place in the whole class a StewData instance is ever created. Every later call into an ImmutableStew method, mix in the real example, reads through that one reference, data.numPotatoes, data.numCarrots, and so on, and has no assignment path back into those fields, because the fields live in a separate object whose own class exposes no mutators for them.

The one place this dynamic can be broken silently, rather than through the compiler catching it, is if the owner class's own field holding the data reference is not itself declared final or readonly. Nothing in SourceMaking's own C# example stops Circle from later replacing its circleData field with a brand new CircleData instance built from different values, since the example marks the fields inside CircleData as protected from mutation but never states that circleData itself, the reference on Circle, is locked. This entry states this observation as its own reading of the published code, not a claim SourceMaking's text itself makes, since the source never discusses this failure path directly. A defensively complete implementation declares the owner's own reference field final or readonly too, closing that specific gap.

## 8. Implementation variants

**Classic Java or C# style, a hand-written data holder with only getters.** SourceMaking's own C# example shows the full before and after. Before, Circle holds radius, color, and origin as ordinary private fields set in its constructor, with nothing stopping its own later methods from reassigning them. After, a CircleData class holds the same three fields, exposes each through a read-only property, and Circle holds a single CircleData reference built once in its constructor, reading circleData.Radius wherever it previously read the field directly. A near-identical, independently written variant on GitHub, Finickyflame slash DesignPatterns, uses C# 12 primary constructors to write the same shape far more tersely, a one-line CircleData class with an auto-implemented, get-only Radius property.

**Python, a descriptor-based variant.** SourceMaking's own Python example uses the descriptor protocol rather than a held reference. A DataClass defines get and set methods, allowing the value to be set exactly once, since its own set only assigns when the current value is None, and MainClass declares the descriptor as a class attribute, assigning through it once in its own constructor.

**A modern language feature achieving the same shape directly, Java records.** iluwatar's ImmutableStew holds a private final StewData field, where StewData itself is declared as a Java record, public record StewData with the four ingredient counts as its components, giving compiler-generated, get-only accessors with no hand-written getter methods at all. A second, independent secondary source, softwarepatternslexicon.com, goes further and recommends nesting the record privately inside the owner class itself for a cleaner modern implementation, "a private nested record is often the cleanest immutable implementation" of this pattern in current Java.

**C# readonly record struct, achieving the same goal without a wrapper class for simple value semantics.** Microsoft's own official C# documentation shows the one-line declaration, public readonly record struct Point with X, Y, and Z components, whose positional properties are compiler-generated as init-only, meaning they can be set only during construction, matching this pattern's own intent without a separate held reference at all.

**Rust, private-by-default struct fields.** The official Rust Programming Language book states the rule directly. "If we use pub before a struct definition, we make the struct public, but the struct's fields will still be private. We can make each field public or not on a case-by-case basis," and, more generally, "struct fields follow the general rule of everything being private by default unless annotated with pub." A struct with a private field forces every caller through a public constructor function, the language-native version of controlling write access to internal state.

**TypeScript readonly, with a documented enforcement caveat.** The official TypeScript Handbook confirms that a readonly field modifier "prevents assignments to the field outside of the constructor," but is explicit that TypeScript's own private keyword, unlike readonly, is not enforced at runtime, calling it "soft private," bypassable through bracket notation, unlike native JavaScript hash-prefixed private fields, which the Handbook calls "hard private." An implementation relying only on TypeScript's compile-time private carries a real, documented, and different failure mode from the languages above.

**Kotlin data class with val, and a documented shallow-copy caveat covered fully in dimension 11.** Kotlin's own official documentation confirms the concise syntax, data class User with val name and val age, but the same documentation, and a 2022 discussion on Kotlin's own official forum, both flag that this convenience does not by itself deliver the pattern's full guarantee, detailed in the failure modes below.

**A framework-level convention resembling the pattern.** iluwatar's own README names Java Beans, "properties are accessed via getters and setters," as a real-world application. This entry treats that as a loosely related convention rather than a confirmed instance of this specific pattern, since the JavaBeans getter and setter convention predates and is broader in intent than this one named pattern.

## 9. Known production uses

Honest headline. No concrete, named, dated example of this pattern being deliberately applied inside a large production application, server, or framework was found, in either research pass. That absence is itself consistent with the pattern's own thin evidentiary history traced in dimension 1, a Wikipedia article a 2021 editor judged as possibly failing to meet the notability bar.

What was found, reported precisely so the distinction from a production instance stays clear. The `iluwatar/java-design-patterns` teaching repository's own `private-class-data` module, Stew, StewData, ImmutableStew, is the single most prominent, currently maintained, named, dated implementation, with commit history reaching back to 25 August 2020 and continuing through at least 2025, but it is a pattern catalogue's own reference implementation, built to demonstrate the pattern, not a case of the pattern being found inside an unrelated production system. The same README's own "Real-World Applications" section names only generic, unnamed categories, "Java Beans," "many Java libraries," and "enterprise applications," none naming an actual library or product, and this entry does not upgrade any of those into a confirmed named instance.

A genuinely interesting, dated signal for ongoing professional use as teaching material, distinct from production use, comes from a Polish IT training company, Altkom, whose GitHub account carries three separate course-cohort repositories, dated December 2024 through January 2025, May 2021, and June 2025, each containing its own copy of a PrivateClassData.cs file under a DesignPatterns Structural path. The recurrence across 2021, 2024, and June 2025 cohorts is direct, dated evidence that the pattern is still actively taught in a professional training curriculum as of mid-2025, distinct from any claim of production adoption. A number of student and course-assignment repositories implementing the pattern in isolation, across Python, Java, and Ruby, were also found, confirming it as a common design-patterns exercise rather than a production idiom.

One further, genuinely related JavaScript project deserves an honest mention. darkobits slash private-data, described in its own README as "a stopgap solution for private class data in JavaScript," uses WeakMap-based closures, a different technique from the separate-data-class shape this pattern otherwise describes, but directly on point for hiding private class data by name. Its own README states plainly, "this project is intended for academic purposes only and should not be used in production," and the repository is now archived, with its last push on 23 June 2022, close to when native ES2022 private class fields shipped broadly. This entry treats it as suggestive evidence that a language-specific workaround for the same underlying goal was retired once the language gained a native mechanism, not as proof about this pattern's own production use.

## 10. Consequences

Positive, quoted directly from iluwatar's own README. "Enhanced security, reduces the risk of unintended data corruption by encapsulating the data." "Ease of maintenance, changes to the internal representation of data do not affect external code." "Improved abstraction, users interact with a simplified interface without worrying about the complexities of data management." SourceMaking's own framing adds the mechanism behind the first of those, that the pattern "allows the class designer to remove write privilege of attributes that are intended to be set only during construction, even from methods of the target class," a guarantee stronger than a bare private field gives.

Negative, converging across the same two sources plus a third, secondary one. "Performance overhead, additional method calls, getters and setters, can introduce slight performance overhead," and "complexity, may increase the complexity of the class design due to the additional layer of methods for data access," both iluwatar's own words. softwarepatternslexicon.com's own guidance, treated here as secondary rather than a top-tier source, states the pattern "is not a requirement for every class" and should be skipped for one or two simple fields, where the holder class would only duplicate an ordinary constructor.

## 11. Failure modes and misuse

**Shallow immutability mistaken for the pattern's full guarantee.** This is the best-sourced failure mode found, and it recurs identically across three independent official language documentation sources, meaning it is not specific to this pattern by name, it is a documented, cross-language limit of "a final reference is not the same thing as deep immutability." Java records, per reflectoring.io, "if a record contains a mutable object, for example an ArrayList, this object itself can be modified," even though the record's own reference field stays final. C# records, per Microsoft's own official documentation, carry "shallow immutability. After initialization, you can't change the value of value-type properties or the reference of reference-type properties. However, the data that a reference-type property refers to can be changed," again with a worked example of a supposedly immutable record being mutated through a nested list. Kotlin's own official documentation states its data class copy method "performs a shallow copy," and a January 2022 thread on Kotlin's own official discussion forum has a participant arguing data classes cannot fully enforce encapsulation because of their auto-generated copy and componentN methods, recommending a hand-written class for objects that genuinely need invariant protection, an argument for something like this pattern's own hand-rolled shape over a bare native data class specifically because that shape leaks this failure mode. The lesson generalizes directly to Private Class Data itself, an implementation that stops at a final or readonly reference without also defensively copying or freezing any mutable field it holds has achieved only shallow protection, not the guarantee the pattern claims to provide.

**A held reference that is itself swappable.** Named directly in dimension 7. When the owner class's own field pointing at the data object is not itself declared final or readonly, nothing stops the owner from later replacing the whole data object with a differently built one, quietly breaking the "locked after construction" promise the pattern exists to make. This is this entry's own reading of the published SourceMaking example rather than a claim the source states, and it is stated as such.

**Reaching for the pattern where a language's native immutability already suffices.** No source found calls the named pattern itself an anti-pattern or explicitly overkill in this exact framing. The closest sourced guidance is the secondary softwarepatternslexicon.com list already quoted in dimension 4 and dimension 10, skip it for one or two simple fields, and do not duplicate what a plain constructor already gives you. This entry states plainly that a stronger, source-backed critique of over-application to every class in a codebase was searched for and not found, rather than inventing one to fill the gap.

## 12. Trade-off matrix

| Force | Plain private final or readonly fields on the class | A full immutable record used as the class itself | Private Class Data, a separate held data object | Builder pattern for immutable construction |
|---|---|---|---|---|
| Construction cost | Lowest, one constructor, no extra allocation | Low, one allocation, compiler-generated constructor | Slightly higher, one extra allocation for the data holder | Higher, a separate builder is constructed, mutated, then discarded |
| Encapsulation strength | Blocks external mutation, but the class's own methods can still reassign a field set outside a constructor context | Strong for the record's own fields, but only shallow, a mutable field inside it stays mutable | Strongest of the four for the "not even my own methods can mutate this" guarantee, since the owner class has no direct field access at all | Strong for the finished product, but the builder itself is explicitly mutable during assembly |
| Boilerplate | Lowest | Very low in a modern language with native records | Moderate, one extra type plus wiring in the constructor | Highest for simple cases, a dedicated builder class with per-field setters and a build method |
| Best language fit | Older languages or versions with no native immutable-record construct | Any language shipping a native immutable-record primitive, Java 16 plus records, C# 9 plus records, Kotlin data classes with val | When the language lacks a native record, or when even the owning class's own methods must be denied write access, a stronger bar than a bare record gives, per softwarepatternslexicon.com | Objects with many optional or combinable constructor parameters, or where step-by-step validation during assembly matters |

No source found builds this exact four-way comparison. It is assembled here from the individually sourced facts quoted throughout this entry plus ordinary engineering reasoning, and is presented as such rather than as a single source's own table.

## 13. Related and incompatible patterns

**Value Object.** Martin Fowler's own bliki entry defines value objects by equality based on their properties rather than identity, and states plainly, "value objects should be immutable." No source found explicitly relates Value Object to Private Class Data by name, and this entry declines to assert a sourced connection beyond the obvious structural point, both care about locking state after construction, which is offered as this entry's own reasoning, not a citation.

**Data Transfer Object.** Wikipedia's own DTO article describes DTOs as bundling data to reduce the number of remote calls, and states directly, "a value object is not a DTO. The two terms have been conflated by Sun slash Java community in the past." No source found connects DTO to Private Class Data specifically.

**Builder.** iluwatar's own README lists its "Related Java Design Patterns" explicitly as Proxy, Singleton, and Decorator, and does not name Builder. A secondary source, softwarepatternslexicon.com, does connect the two, framing Builder as handling complex multi-step assembly while this pattern protects the resulting, already-assembled state, complementary rather than competing. This entry reports both findings honestly rather than picking the more convenient one.

**The pimpl idiom, opaque pointer, in C++.** A genuinely contested relationship. One informal source, a single Reddit comment found only as a search snippet, lists "PIMPL, Opaque Pointer, Compiler Firewall, Cheshire Cat, or Private Class Data Pattern" as synonyms, a personal list rather than an authoritative citation. English Wikipedia's own "Opaque Pointer" article, fetched directly, does not mention Private Class Data anywhere, names the technique's actual alternate names as "handle classes," "compiler firewall idiom," "d-pointer," and "Cheshire Cat," and states the technique "is documented in the GoF Design Patterns book as the Bridge pattern," not as Private Class Data. This entry's honest conclusion, the two ideas are related in spirit, both hide internal representation behind an indirection layer, and are informally conflated by some practitioners, but the more authoritative source available associates the underlying C++ technique with Bridge rather than with this pattern, and that distinction is kept rather than smoothed over.

**The general Immutable Object idea.** No dedicated source draws an explicit "this pattern is an instance of, or is distinct from, the general Immutable Object pattern" comparison. This entry's own framing, offered as engineering judgement rather than sourced fact, is that Private Class Data is a structural technique, move fields into a companion object, commonly used in service of achieving immutability, but not itself synonymous with the broader idea, since nothing in the SourceMaking example stops the owner class from later exposing a method that replaces the whole data object wholesale.

## 14. Refactoring path in and out

**Refactoring in, from a class whose own methods mutate fields nobody meant them to touch.** SourceMaking's own checklist is written as exactly this refactor, move the fields that need protecting into a new data class, give that new class only getters for anything meant to stay fixed, construct one instance of it inside the original class's constructor, and replace every direct field read inside the original class with a read through the held reference. iluwatar's own before-and-after pair, the mutable Stew class next to the protected ImmutableStew class, is a second, independently written instance of the identical refactor.

**Refactoring out, toward a native immutable record when the host language has one.** Dimension 8 already showed iluwatar's own reference implementation making this exact move, StewData is written as a Java record rather than a hand-written class with manually written getters. softwarepatternslexicon.com's own recommendation, a private nested record, is the same refactor taken one step further, folding the whole data holder inside the owner class since the language's own record syntax removes the boilerplate reason to keep it as a separate top-level type. This refactor is only safe once the shallow-immutability caveat from dimension 11 has been checked, if any field held by the record is itself a mutable collection or object, the refactor needs a defensive copy added at the record's own construction point, or the swap from a hand-rolled data class to a bare record silently weakens the guarantee rather than preserving it.

## 15. Testing and verification

No source found discusses testing this specific pattern by name, and this entry states that gap plainly rather than filling it with an invented citation. What follows is this entry's own reasoning from the pattern's own structure, offered explicitly as reasoning rather than as a sourced finding.

Because the data object's fields are fixed once its constructor returns, a test fixture built from one instance can be reused safely across multiple assertions in the same test without needing to guard against an earlier assertion having silently mutated shared state, since SourceMaking's own checklist step three places construction, and only construction, as the single place values ever enter the object. Equality-style assertions against an expected value are correspondingly simpler to write, since there is no method on the data class itself capable of changing what the test is checking after the fact. The one thing worth testing directly, given dimension 11's failure modes, is that the pattern's own guarantee actually holds, a test that obtains a reference to a mutable field the data object exposes, for example a collection component on a record, mutates it through that reference, and then asserts the change is not visible back through the owner class, is the concrete way to catch the shallow-immutability failure mode before it ships rather than discover it later.

## 16. Observability signals

No source found discusses runtime observability for this specific pattern by name, and this entry again states that gap directly. The pattern's own mechanism, however, suggests one concrete, low-cost signal worth naming. Because the data object is meant to be built exactly once per owner instance and never replaced, a debug-only assertion or a logged warning that fires if a second construction of the same data type is ever observed for the same owner instance, for example by counting constructor calls in a test or a debug build, is a direct way to surface a violation of dimension 7's own "constructed once, in the owner's constructor" dynamic before it reaches production. Beyond that, this entry does not claim any pattern-specific monitoring practice exists in the wild, since none was found.

## 17. Security and privacy implications

The strongest, most directly sourced angle here is not about this pattern by name, it is about immutability as a design property generally, and this entry is careful to keep that distinction visible rather than overstate it. A 2024 academic paper, Kinsbruner, Itzhaky, and Peleg, Technion, "Constrictor. Immutability as a Design Concept," published at ECOOP 2024, presents an SMT-based tool for verifying that an object's externally observable behavior stays immutable even when some of its internal fields are not, tested against 51 real design-violation examples. This entry could not confirm from the fetched abstract that the paper itself discusses thread safety or security explicitly, only that genuine, recent academic interest in mechanically verifying immutability claims exists, and states that limit honestly rather than stretching the citation to cover a claim it did not verify.

No source found ties this named pattern to a specific security advisory, CVE, or an incident caused by an unexpectedly mutated configuration object. What can be said, grounded in general, well-established immutability reasoning rather than a pattern-specific source, is that an object whose state cannot change after construction needs no synchronization to guard concurrent readers against a writer, since there is no writer once construction completes, and the shallow-immutability failure mode from dimension 11 is the one place that reasoning breaks down, a mutable field nested inside an otherwise "locked" data object is still a live, unsynchronized write surface for any code holding a reference to it.

## 18. References

1. Wikipedia, Design Patterns, https://en.wikipedia.org/wiki/Design_Patterns, verified 2026-08-23.
2. Wikipedia, List of software design patterns, https://en.wikipedia.org/wiki/List_of_software_design_patterns, verified 2026-08-23.
3. Wikipedia, the deletion log entry recording the removal of the Private class data pattern article, https://en.wikipedia.org/wiki/Special:Log/delete, verified 2026-08-23.
4. Wikipedia, the Articles for deletion discussion for the Private class data pattern article, https://en.wikipedia.org/wiki/Wikipedia:Articles_for_deletion/Private_class_data_pattern, verified 2026-08-23.
5. Wikipedia, Opaque pointer, https://en.wikipedia.org/wiki/Opaque_pointer, verified 2026-08-23.
6. Wikipedia, Data transfer object, https://en.wikipedia.org/wiki/Data_transfer_object, verified 2026-08-23.
7. SourceMaking, Private Class Data design pattern, https://sourcemaking.com/design_patterns/private_class_data, verified 2026-08-23.
8. SourceMaking, Private Class Data, C sharp dot net example, https://sourcemaking.com/design_patterns/private_class_data/c-sharp-dot-net, verified 2026-08-23.
9. SourceMaking, Private Class Data, Python example, https://sourcemaking.com/design_patterns/private_class_data/python/1, verified 2026-08-23.
10. SourceMaking, About Us, https://sourcemaking.com/about-us, verified 2026-08-23.
11. iluwatar, java-design-patterns, private-class-data module README, https://github.com/iluwatar/java-design-patterns/blob/master/private-class-data/README.md, verified 2026-08-23.
12. iluwatar, java-design-patterns, ImmutableStew.java, https://raw.githubusercontent.com/iluwatar/java-design-patterns/master/private-class-data/src/main/java/com/iluwatar/privateclassdata/ImmutableStew.java, verified 2026-08-23.
13. iluwatar, java-design-patterns, StewData.java, https://raw.githubusercontent.com/iluwatar/java-design-patterns/master/private-class-data/src/main/java/com/iluwatar/privateclassdata/StewData.java, verified 2026-08-23.
14. Finickyflame, DesignPatterns, PrivateClassData.cs, https://raw.githubusercontent.com/Finickyflame/DesignPatterns/master/DesignPatterns/Structural/PrivateClassData.cs, verified 2026-08-23.
15. Microsoft Learn, C sharp language reference, built-in types, record, https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/record, verified 2026-08-23.
16. Microsoft Learn, C sharp record types, init-only and shallow immutability, https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/records, verified 2026-08-23.
17. The Rust Programming Language, Paths for Referring to an Item in the Module Tree, https://doc.rust-lang.org/book/ch07-03-paths-for-referring-to-an-item-in-the-module-tree.html, verified 2026-08-23.
18. TypeScript Handbook, Classes, readonly and private, https://www.typescriptlang.org/docs/handbook/2/classes.html, verified 2026-08-23.
19. Kotlin documentation, Data classes, https://kotlinlang.org/docs/data-classes.html, verified 2026-08-23.
20. Kotlin Discussions, forum thread on data class encapsulation, January 2022, https://discuss.kotlinlang.org, verified 2026-08-23.
21. reflectoring.io, A Beginner Friendly Guide to Java Records, https://reflectoring.io/beginner-friendly-guide-to-java-records/, verified 2026-08-23.
22. softwarepatternslexicon.com, Private Class Data pattern in Java, https://softwarepatternslexicon.com/java/structural-patterns/private-class-data-pattern/, verified 2026-08-23.
23. Martin Fowler, bliki, Value Object, https://martinfowler.com/bliki/ValueObject.html, verified 2026-08-23.
24. darkobits, private-data, GitHub, https://github.com/darkobits/private-data, verified 2026-08-23.
25. Kinsbruner, Itzhaky, Peleg, "Constrictor, Immutability as a Design Concept," ECOOP 2024, https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ECOOP.2024.22, verified 2026-08-23.
26. dev.to, mspilari, Builder pattern trade-offs, January 2025, https://dev.to/mspilari, verified 2026-08-23.

**Evidence grade.** thin

**Most solid findings.** The GoF exclusion, confirmed directly against Wikipedia's own contents listing and its list-of-patterns table. The full deletion history of the English Wikipedia article, sourced from the deletion log and the archived AfD discussion themselves, both fetched directly. SourceMaking's own problem, discussion, and checklist sections, and its full before-and-after C sharp code, all quoted directly from the live page. iluwatar's own README, benefits, trade-offs, applicability guidance, and related-patterns list, plus its real ImmutableStew and StewData source files, all fetched and quoted directly. The shallow-immutability caveat, independently confirmed across three separate official language documentation sources, Java, C sharp, and Kotlin, plus a Kotlin community forum thread.

**Unverified or unclear.** The exact original creation date and author of the deleted Wikipedia article rests on a single editor's stated recollection during the 2021 deletion discussion, not an independently confirmed timestamp, and this entry treats it as likely rather than settled. The pimpl and opaque-pointer connection rests mainly on one informal, unauthoritative source, a Reddit comment found only as a search snippet, and the more authoritative source checked, Wikipedia's own Opaque Pointer article, associates that C++ technique with Bridge instead, a genuine unresolved tension this entry reports honestly rather than picking a side. No source was found discussing testing or observability practice for this pattern by name, so those two dimensions are this entry's own reasoning from the pattern's structure, labeled as such throughout. No source was found arguing this pattern is now obsolete given modern native immutability features, in either direction, despite a deliberate search for exactly that claim. The trade-off matrix in dimension 12 is this entry's own synthesis, no single source builds that comparison.

## Code

```typescript
// The data class holds the fields that must stay fixed after construction,
// exposed only through getters. No setter exists for radius, color, or
// origin, following SourceMaking's own C# CircleData example.
class CircleData {
  private readonly radius: number;
  private readonly color: string;
  private readonly origin: { x: number; y: number };

  constructor(radius: number, color: string, origin: { x: number; y: number }) {
    this.radius = radius;
    this.color = color;
    this.origin = origin;
  }

  getRadius(): number {
    return this.radius;
  }

  getColor(): string {
    return this.color;
  }

  getOrigin(): { x: number; y: number } {
    return this.origin;
  }
}

// The owner class holds exactly one CircleData reference, built once inside
// its own constructor. The reference field itself is readonly, closing the
// gap named in Dynamics, a swappable held reference, that the classic
// example leaves open.
class Circle {
  private readonly data: CircleData;

  constructor(radius: number, color: string, origin: { x: number; y: number }) {
    this.data = new CircleData(radius, color, origin);
  }

  circumference(): number {
    return 2 * Math.PI * this.data.getRadius();
  }

  describe(): string {
    return this.data.getColor() + " circle, radius " + this.data.getRadius();
  }
}

const circle = new Circle(4, "blue", { x: 0, y: 0 });
console.log(circle.describe());
console.log(circle.circumference());
```

```python
# The same shape in Python, using a frozen dataclass as the modern
# equivalent of a hand-written getter-only data class. frozen=True raises
# on any attempted attribute assignment after construction, giving the
# pattern's own guarantee natively rather than through hand-written getters.
from dataclasses import dataclass


@dataclass(frozen=True)
class CircleData:
    radius: float
    color: str
    origin: tuple[float, float]


class Circle:
    def __init__(self, radius: float, color: str, origin: tuple[float, float]) -> None:
        self._data = CircleData(radius, color, origin)

    def circumference(self) -> float:
        return 2 * 3.14159265 * self._data.radius

    def describe(self) -> str:
        return f"{self._data.color} circle, radius {self._data.radius}"


circle = Circle(4.0, "blue", (0.0, 0.0))
print(circle.describe())
print(circle.circumference())

try:
    circle._data.radius = 10.0
except Exception as exc:
    print("blocked", type(exc).__name__)
```

```go
package main

import (
	"fmt"
	"math"
)

// The data holder. unexported fields plus getter-only methods give the same
// "no setter" guarantee as SourceMaking's C# CircleData, using Go's own
// package-level export rules instead of a private/readonly keyword pair.
type circleData struct {
	radius float64
	color  string
}

func newCircleData(radius float64, color string) circleData {
	return circleData{radius: radius, color: color}
}

func (d circleData) Radius() float64 {
	return d.radius
}

func (d circleData) Color() string {
	return d.color
}

// The owner type holds one circleData value, built once inside its own
// constructor function. Go has no reference-reassignment gap here since
// circleData is held by value, not by pointer, so there is nothing to
// swap out from underneath the caller.
type Circle struct {
	data circleData
}

func NewCircle(radius float64, color string) Circle {
	return Circle{data: newCircleData(radius, color)}
}

func (c Circle) Circumference() float64 {
	return 2 * math.Pi * c.data.Radius()
}

func (c Circle) Describe() string {
	return c.data.Color() + " circle, radius " + fmt.Sprintf("%.1f", c.data.Radius())
}

func main() {
	circle := NewCircle(4.0, "blue")
	fmt.Println(circle.Describe())
	fmt.Println(circle.Circumference())
}
```
