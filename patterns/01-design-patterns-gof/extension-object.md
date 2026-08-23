---
name: Extension Object
slug: extension-object
family: 01-design-patterns-gof
category: Structural
aliases: [Extension Interface, Interface Extensions]
first_described: "Erich Gamma, The Extension Objects Pattern, published as chapter 6, Extension Object, in Martin, Riehle, Buschmann (editors), Pattern Languages of Program Design 3, Addison-Wesley, 1997"
maturity: established
related: [visitor, decorator, adapter]
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

Extension Object was first sketched informally by Erich Gamma and Richard Helm in "Designing Objects for Extensions," Dr. Dobb's Sourcebook issue 236, pages 56 to 59, May or June 1995, a citation Gamma himself gives in the later, formal paper's own Evolution section. That formal paper, "The Extension Objects Pattern," is written entirely by Gamma and published as chapter 6, titled "Extension Object," in Pattern Languages of Program Design 3, edited by Robert Martin, Dirk Riehle, and Frank Buschmann, Addison-Wesley, 1997.

An honest correction belongs here, since the working assumption behind this entry's own research brief was wrong until it was checked. Extension Object is not documented in Pattern-Oriented Software Architecture Volume 1, the 1996 POSA1 book by Buschmann, Meunier, Rohnert, Sommerlad, and Stal, despite the surface similarity of the acronym and Buschmann's presence on both projects. Gamma states plainly, in a 2009 interview conducted by Larry O'Brien, that Extension Object is one of several patterns proposed as new material after the original 1994 Gang of Four catalogue, alongside Null Object, Type Object, and Dependency Injection, which places it outside the 23 GoF patterns even though this repository's family folder groups it with them by convention.

Two aliases are independently sourced. "Extension Interface" and "Extension Object/Extension Interface" appear in Erich Gamma and Kent Beck's own book Contributing to Eclipse, Addison-Wesley, 2003, in the table of contents heading for chapter 31. "Interface Extensions" appears as an alternate name in the iluwatar/java-design-patterns open source catalogue's own README for its extension-objects module.

No standalone Wikipedia article exists for this pattern under any of its names, confirmed by a direct request that returns a not found response, and by a Wikipedia site search that surfaces only unrelated pattern articles. One further note worth stating for anyone researching this pattern independently. the iluwatar catalogue's README attributes a definition to "Wikipedia" that is, on inspection, the opening sentence of Wikipedia's real article on the unrelated concept of extension methods, a compile time language feature in C sharp and similar languages, with the word "methods" swapped for "objects pattern" throughout except in one sentence where the swap was missed. This entry treats that as a documented source of confusion in the wild, not as a citation.

## 2. Problem and context

Some abstractions cannot have their full, final interface anticipated at design time, because different clients of the same class genuinely need different views onto it. Gamma's own Motivation section states the problem directly, that combining every operation different clients need into one interface "results in a bloated interface," that such interfaces "are difficult to maintain and understand," and that a change made for one client's part of the interface "can affect other clients that use the same abstraction."

Gamma's worked example, restated here rather than quoted, is a compound document architecture in the style of OLE 2 or OpenDoc, where a generic `Component` abstraction, representing anything from a text block to a spreadsheet to a movie clip, must expose a common interface so a document can arrange heterogeneous components together. A spelling checker, added later, needs to enumerate the words inside any component that happens to contain text. Adding a text enumeration method directly to `Component` would force every component, including a spreadsheet or a movie, to carry an interface it has no use for, contradicting the abstraction's own stable identity, and it would need to be revisited every time a new client brought a new, equally narrow need.

## 3. Forces

Most of the reasoning below is engineering judgement drawn from Gamma's own Consequences and Implementation sections, stated as judgement rather than dressed as settled fact.

The dominant tension is interface stability against extensibility. Gamma's paper states the benefit plainly, that adding a new interface "doesn't require any change to the existing subject interface," and contrasts this with the alternative of subclassing for every new capability, which "results in a class hierarchy that can be difficult to manage" because "inheritance is static and requires creating a new class for each additional interface." Extension Object trades a static, compiler checked hierarchy for a dynamic, runtime queried one, and Gamma's own paper names the resulting cost directly, that "a client has to query for the interface and check whether it exists," which "introduces additional tests and control paths in your program."

A second force is discipline against convenience. Gamma's fifth consequence names this outright, a "tension to abuse extensions for concepts that should be explicitly modeled," warning that when extensions are reached for beyond genuinely unanticipated cases, "the understandability of a system suffers."

A third force, specific to non garbage collected environments and stated directly in the paper's Implementation section, is ownership. "The Subject hands out a reference to an extension object and therefore has no control over the lifetime of the extension," which forces an explicit choice between reference counting the extension or having the subject own and destroy it, a cost that a language with automatic memory management does not eliminate so much as hide.

## 4. Applicability and non-applicability

Gamma's own Applicability section, quoted directly, gives three cases. Use Extension Objects "when you need to support the addition of new or unforeseen interfaces to existing classes and you don't want to impact clients that don't need this new interface." Use it "when a class representing a key abstraction plays different roles for different clients," where "the number of roles the class can play should be open ended" and the key abstraction itself must stay intact, his own example being that "a customer object is still a customer object even if different subsystems view it differently." Use it "when a class should be extensible with new behavior without subclassing from it."

The paper gives no direct non-applicability list of its own, an honest gap worth naming rather than filling with an invented one. What follows is reasoned from Gamma's own Related Patterns comparisons, stated here as judgement.

Prefer Visitor instead when the class hierarchy being extended is small, closed, and known in advance, and the priority is catching a missed case at compile time rather than at runtime. Gamma's own words draw this line, that Visitor "has similar benefits" but "requires a stable class hierarchy and introduces a dependency cycle" back onto that hierarchy, which Extension Object avoids by design.

Prefer Decorator instead when the goal is to transparently augment an already known, narrow interface rather than to expose a genuinely separate, separately queried one. Gamma states Decorator "works best in situations when the interface is narrow and some existing operations should be augmented," and that decorated objects are "more transparent" to the client than extension objects are, since a decorator answers to the same interface the client already expects rather than a newly queried one.

Avoid Extension Object when the set of client specific needs is actually small, fixed, and already known, since the pattern's own second consequence, added client complexity, is a cost paid on every call site for a flexibility that an unchanging, closed set of needs does not require. In that narrower case, adding the operations directly to the class, or reaching for Visitor, is the simpler and more honestly stated design.

## 5. Structure

Gamma's Participants section, quoted directly, with his own worked class names given in parentheses.

Subject (Component). "Defines the identity of an abstraction. It declares the interface to query whether an object has a particular extension. In the simplest case an interface is identified by a string."

Extension (ComponentExtension). "The base class for all extensions. It defines some support for managing extensions themselves. Extension knows its owning subject."

ConcreteSubject (StandardTextComponent). "Implement the GetExtension operation to return a corresponding extension object when the client asks for it."

AbstractExtension (TextAccessor). "Declares the interface for a specific extension."

ConcreteExtension (StandardTextAccessor). "Implement the extension interface for a particular component. Store the state associated with a specific extension."

The Collaborations section, also quoted directly, states the runtime protocol in three steps. "A client asks a Subject for a specific extension." "When the extension exists the Subject returns a corresponding extension object. The client subsequently uses the extension object to access additional functionality." "If the Subject doesn't support an extension it returns nil to signal that it doesn't support it."

Gamma's own Implementation section describes two structural variants for how a subject comes to hold its extensions, and states plainly that they "don't exclude each other." The internal or accessor variant has the concrete subject privately hold and lazily create each extension inside its own override of the query method, which he notes keeps the cost of adding support small but does not let an outside party attach a new extension after the fact. The external or dictionary variant has the subject itself carry an add and remove operation over a name keyed collection, which he states "enables clients to add new external extensions on demand and doesn't require that the ConcreteSubject knows all its extensions beforehand."

## 6. ASCII structure diagram

```
+--------------------+          +------------------------+
|      Subject        |--owns-->|       Extension          |
+--------------------+          +------------------------+
| +GetExtension(name)  |          | (knows its owning       |
+--------------------+          |  subject)                |
         ^                       +------------------------+
         |                                 ^
+--------------------+                     |
|  ConcreteSubject     |          +------------------------+
+--------------------+          |   AbstractExtension       |
| +GetExtension(name)  |o------->+------------------------+
+--------------------+          | (declares the extension-  |
                                 |  specific interface)      |
                                 +------------------------+
                                            ^
                                            |
                                 +------------------------+
                                 |    ConcreteExtension      |
                                 +------------------------+

  Client --asks Subject for a named extension-->  Subject
  Subject --returns matching Extension, or nil-->  Client
```

## 7. Dynamics

A client that wants behaviour beyond a subject's core interface calls the subject's query method with a name or a type token identifying the extension it wants. The base `Subject` implementation of this method returns nil by default. Each `ConcreteSubject` overrides it, checks the incoming request against the extensions it actually supports, and either returns an existing extension object, lazily constructing one on first request, or falls through to the base class's nil.

The client receives a reference typed as the general `Extension` base, or in the dictionary variant a value out of the subject's own collection, and narrows it to the concrete extension type it expected before calling any of that extension's own methods, using a language appropriate downcast. Nothing in the protocol enforces at compile time that this cast will succeed. a missing extension surfaces as nil rather than as a compiler error, and Gamma's own paper treats this deferred check, "a client has to query for the interface and check whether it exists," as a direct, named cost of the pattern rather than an incidental detail.

In the external, dictionary based variant, a fourth participant enters the runtime picture that the internal variant never needs. code outside the concrete subject class itself can call an add operation, handing the subject a new extension object under a chosen name, before any client ever queries for it, which is how a subject can be extended by code that did not exist when the subject's own class was written.

## 8. Implementation variants

The most extensively documented, real production implementation of this pattern's shape is the Eclipse Platform's `org.eclipse.core.runtime.IAdaptable` mechanism, and Eclipse's own naming choices confirm the lineage directly, since Gamma and Beck's own book Contributing to Eclipse titles the relevant chapter section "Extension Object/Extension Interface." Eclipse's javadoc for `IAdaptable` states it is "an interface for an adaptable object," where "adaptable objects can be dynamically extended to provide different interfaces (or adapters)," through a single generic method, `<T> T getAdapter(Class<T> adapter)`, documented to return "an object which is an instance of the given class associated with this object," or "null if no such object can be found." Where Gamma's own paper keys extension lookup by string name, Eclipse's method is generic over a `Class<T>` token, letting the compiler infer and check the return type at the call site without an explicit downcast, a real, sourced refinement over the pattern's originally described string keyed lookup.

Eclipse layers two further pieces on top of the base `getAdapter` call. `IAdapterFactory`, whose javadoc states it "defines behavioral extensions for one or more classes that implement the IAdaptable interface," lets an extension be contributed by code that does not own the class being extended, matching the external, dictionary style variant Gamma's own paper describes but implemented as a registered factory rather than a per instance collection. `IAdapterManager` sits above that as a registry, and its javadoc states factories can be registered "programmatically" or "declaratively" through Eclipse's own extension point mechanism, an XML based registration layer with no equivalent named in Gamma's original paper.

The iluwatar/java-design-patterns open source catalogue carries a module named `extension-objects`, whose worked example uses a `Unit` base class with an abstract `getUnitExtension(String extensionName)` method and concrete subclasses, for example `SoldierUnit`, that check the requested name and return a matching extension or null, a direct, working restatement of Gamma's own string keyed, internal variant.

Microsoft's Component Object Model, predating both of the above, implements a closely related idea through `QueryInterface`, documented by Microsoft as the mechanism that lets a caller "determine at run time whether a COM object supports a particular interface," returning a pointer to that interface if supported or null otherwise, keyed by an interface identifier rather than a class token or a string name, and governed by formally specified rules of interface set stability and object identity that neither Gamma's paper nor Eclipse's javadoc states as explicitly. C sharp's `IServiceProvider.GetService(Type serviceType)` shares the same call shape, a single method keyed by a type token, returning null on a miss, though Microsoft's own documentation frames it as service location rather than naming it as an Extension Object instance, a structural resemblance this entry notes as inference rather than as a sourced claim.

## 9. Known production uses

Gamma's own paper lists three systems in its Known Uses section, quoted directly. "In OpenDoc the common base ODObject provides the interface for accessing extensions." "OLE builds on top of the Component Object Model (COM). In COM all interfaces of an object are accessed by the QueryInterface mechanism." "In the user interface framework of Taligent's CommonPoint the class TView is responsible for managing a visual portion of screen real estate... TView provides so called Attributes." OpenDoc and Taligent CommonPoint are both long discontinued platforms from the mid 1990s, so their listing here is historical record rather than evidence of current use, stated honestly rather than implied otherwise.

The strongest currently verifiable production evidence is the Eclipse Platform itself. `IAdaptable`, `IAdapterFactory`, and `IAdapterManager` are first party classes inside Eclipse's own core runtime package, `org.eclipse.core.runtime`, documented in Eclipse's official platform API reference rather than in a third party add on, which is direct evidence the mechanism is load bearing infrastructure for the Eclipse SDK and its plug in ecosystem, since it is precisely how a plug in can attach a new capability to a core Eclipse type, such as a resource or a file, that it did not write and cannot subclass.

Microsoft's COM, and the `QueryInterface` mechanism specifically, underlies a documented family of long lived Microsoft technologies including OLE, ActiveX, and the Windows Shell's own context menu handler mechanism, where Microsoft's own documentation states that a shell extension DLL is discovered and activated by Windows Explorer through COM interfaces the operating system queries for at the point of use, without the shell needing advance knowledge of any particular extension's capabilities, precisely the motivation Gamma's paper states for the pattern generally.

## 10. Consequences

Positive.

Gamma's own first consequence, quoted directly, states that the pattern "facilitates adding interfaces," since "adding a new interface to a subject is simplified since this doesn't require any change to the existing subject interface," while the subject's "key abstraction" is preserved intact for clients that never ask for the extension.

His second consequence states there are "no bloated class interfaces for key abstractions," since "a key abstraction doesn't become polluted with operations that are specific for a client," a benefit he contrasts directly against subclassing, calling the resulting hierarchy from that alternative "difficult to manage" because "inheritance is static and requires creating a new class for each additional interface."

His third consequence states the pattern supports "modeling different roles of a key abstraction in different subsystems," since "when an abstraction is used across subsystems it often plays different roles," and keeping each role in its own extension object means "one subsystem doesn't have to know the roles used in other subsystems."

Negative.

Gamma's fourth consequence states plainly that "clients become more complex," since "an extended interface is more complicated to use than one which is provided by the subject itself," requiring "a client to query for the interface and check whether it exists," which "introduces additional tests and control paths."

His fifth consequence names a discipline cost, a "tension to abuse extensions for concepts that should be explicitly modeled," warning that reaching for an extension where a real, first class abstraction was called for leaves "the understandability of a system" worse off.

His Implementation section adds two further, concrete costs presented alongside the numbered consequences rather than inside them. identifying extensions safely, avoiding a collision between two unrelated extensions that happen to choose the same string name, which the paper treats as a real design problem needing either a naming convention or a runtime type identification mechanism, and, in a language without garbage collection, the ownership question of who frees an extension object once the subject that handed it out no longer needs it, which the paper states explicitly is not automatically solved by the pattern itself.

## 11. Failure modes and misuse

The clearest, most directly sourced failure mode is a weakly typed lookup key producing a silent miss instead of a compile error. The iluwatar catalogue's own worked example keys its lookup by a bare string, `getUnitExtension(String extensionName)`, so a typo in the requested name is invisible to the compiler and surfaces only as a null returned at runtime, which the caller must remember to check. Eclipse's generic `getAdapter(Class<T> adapter)` narrows this risk at the call site, since the compiler infers and checks the returned type from the class token, but it does not remove the deeper problem, that a caller can still request a perfectly valid class for which no adapter happens to be registered, and still receives null rather than a compile time guarantee.

Both of the two most heavily documented real implementations checked for this entry return null on a miss rather than raising an error. Eclipse's `IAdaptable.getAdapter` javadoc states it returns "null if no such object can be found," and C sharp's `IServiceProvider.GetService` documentation states it returns "null if there is no service object of type serviceType." Neither the Java nor the C sharp compiler forces a caller to check that result, so a caller who forgets produces a null reference exception at the point the extension is actually used, not at the point it was requested, which is a well known, hard to trace category of bug in code built on this pattern.

A specific, sourced failure mode inside Eclipse's own registry layer is worth naming precisely, because it shows the null result can mean two different things that are indistinguishable to the caller. Eclipse's `IAdapterManager` javadoc states plainly that `getAdapter` "will never cause plug-ins to be loaded," and that "if the only suitable factory is not yet loaded, this method will return null," a return value identical to the case where no such extension genuinely exists. Eclipse's own answer is a second, heavier method, `loadAdapter`, documented to force the providing plug in to load if necessary, an explicit acknowledgment that the plain lookup alone cannot be trusted to distinguish absence from mere unavailability.

Microsoft's own formal rules for implementing `QueryInterface` are, read carefully, a warning about what breaks without them. the specification requires that "the set of interfaces accessible on an object through QueryInterface must be static, not dynamic," and that "for any given object instance, a call to QueryInterface with IID_IUnknown must always return the same physical pointer value." The fact that Microsoft had to specify object identity and interface set stability as formal rules is evidence that a naive implementation of this pattern's shape, in a language without automatic memory management to hide the bookkeeping, can otherwise produce an object whose available extensions silently change depending on which reference the caller happens to be holding, an inconsistency no source document names outright but which the specification exists to prevent.

## 12. Trade-off matrix

Every row below is grounded in the sources cited across dimensions 8 through 11. The comparison itself, placing all four approaches side by side, is this entry's own construction, built by combining separately sourced facts, and is stated here as synthesis rather than as a single quoted source.

| Approach | Adding a new capability | Client compile time safety | Discoverability | Runtime cost |
|---|---|---|---|---|
| Extension Object | New extension class, no change to the core subject class, per Gamma's own first consequence | Low with a string key (iluwatar), higher with a generic class token (Eclipse's getAdapter), never fully checked at compile time | Poor without added tooling. Eclipse's getAdapterList lets a factory declare its supported types up front, mitigating but not eliminating this | Extra indirection through a lookup, and in Eclipse's registry variant, a possible plug in load |
| Visitor | New visitor subclass, no change to element classes, but every existing visitor must be updated whenever an element class is added | High, resolved through compiler checked double dispatch | Good, every supported operation is a visible visitor subclass | One extra virtual dispatch per visit |
| Decorator | New decorator subclass wrapping the component | High, the decorator answers to the same already known interface | Good, decorators are visible, named types | One extra layer of delegation per wrap |
| Direct subclassing | New subclass per combination of added capability | High, ordinary virtual dispatch | Good, capability lives directly on the type | None beyond normal dispatch |

## 13. Related and incompatible patterns

Visitor is the pattern Gamma's own paper compares most directly. His Related Patterns section states Visitor "centralizes behavior and enables to add new behavior to a class hierarchy without having to change it," calling this "similar benefits" to Extension Object, but draws the dividing line precisely, that Visitor, unlike Extension Object, "requires a stable class hierarchy" and "introduces a dependency cycle" back onto that hierarchy, since every element class must implement an `accept` method aware of the visitor abstraction. Extension Object accepts a weaker compile time guarantee in exchange for never requiring the hierarchy itself to know about its own extensions.

Decorator is the second pattern Gamma names directly. His paper states Decorator "is another pattern to extend the behaviour of an object," and that "for the client the use of decorated objects is more transparent than extension objects," since a decorator answers to the interface the client already expects rather than a newly, separately queried one, adding that "decorators work best in situations when the interface is narrow and some existing operations should be augmented," a narrower fit than the genuinely new, unforeseen interfaces Extension Object targets.

Adapter is the third pattern Gamma names, and he draws a clean line between the two rather than treating them as competitors. "Adapter supports to adapt an existing interface. The Extension Objects pattern supports additional interfaces," and the two "can work together in situations where an object needs to be adapted to an extension interface," meaning Adapter reshapes one known interface into another known interface, while Extension Object adds an interface that was not part of the subject's contract at all.

Martin Fowler's Role Interface, described on his own site, is a closely adjacent but distinct idea worth naming even though Gamma's original paper predates it. Fowler's own worked example has one core object implement several small, narrow interfaces directly and statically, each interface shaped by "a specific interaction between suppliers and consumers," which achieves a similar goal, several typed views onto one object, but at compile time rather than through Extension Object's runtime lookup, trading dynamic extensibility for a design that the compiler can fully check.

## 14. Refactoring path in and out

Refactoring in. The trigger Gamma's own Motivation section names is a class whose interface has grown to serve several unrelated clients, each needing a different narrow slice of behaviour that the others do not. The refactor pulls each client specific slice out into its own extension type, matching Gamma's AbstractExtension and ConcreteExtension roles, replaces the corresponding methods on the core class with a single query method, and, following his own worked internal variant, has the core class privately hold and lazily create each extension it supports. Where the set of extensions must be open to code outside the core class entirely, the refactor goes one step further and adds the external, dictionary variant, an add and remove operation over a name or type keyed collection, mirroring Eclipse's separate `IAdapterFactory` layer for extensions contributed by code that does not own the core class. No source found for this entry names a general purpose refactoring, such as Martin Fowler's catalogue, as the specific technique for this move, so the steps above are this entry's own construction from Gamma's described structure, not a citation of a named refactoring.

Refactoring out. Two separate directions apply depending on why the pattern is no longer earning its cost. If the set of extensions a class actually supports has stopped growing and settled to a small, known, closed set, the dynamic lookup and its associated null checking and casting can be collapsed back into ordinary typed methods or into Fowler's Role Interface, a set of small interfaces the core class implements directly, trading the pattern's runtime flexibility for compile time safety once that flexibility is no longer needed. If, instead, the real underlying need was adding new operations across a fixed, stable set of core classes rather than attaching new capabilities discovered at runtime, Gamma's own comparison to Visitor applies in reverse. once the class hierarchy being extended has stopped changing, the dependency cycle Visitor introduces stops being a cost, and collapsing several extension lookups that only ever resolve to one of a small number of concrete extension types into visitor subclasses removes the pattern's own second and fourth named consequences, added client complexity and the discipline risk of overuse, in exchange for Visitor's own, differently shaped cost of touching every visitor when a new core class appears.

## 15. Testing and verification

No source found for this entry discusses testing strategy for Extension Object specifically, and this dimension is engineering reasoning drawn from the structure Gamma's own paper describes, stated here as judgement rather than as a sourced claim.

The pattern's single method contract, a query that returns either an extension object or nil, is itself a natural seam for a test double. code that consumes an extensible object can be tested against a fake subject implementing only that one query method, with no real concrete subject or registry behind it, letting a test assert the consumer's behaviour for a present extension and its behaviour for an absent one without constructing the whole object graph the real subject would otherwise require.

The absent case deserves its own explicit test, and not only as a matter of good practice. both of the two most heavily documented real implementations checked for this entry, Eclipse's `IAdaptable.getAdapter` and C sharp's `IServiceProvider.GetService`, document null as a normal, expected outcome of a miss rather than an exceptional one, so any code built on this pattern's shape has a documented contract obligation to handle that outcome, and a test suite that never exercises it is leaving a documented, sourced contract path unverified.

Eclipse's own two method split, `getAdapter` against `loadAdapter`, is itself a concrete testing hazard worth naming. a test written against `getAdapter` alone inside a plug in host cannot tell "this extension genuinely does not exist" apart from "the plug in that would provide it has not been activated in this test environment," per Eclipse's own javadoc for `IAdapterManager`, so an integration test relying on that method needs to guarantee the providing plug in is already active, or use `loadAdapter` instead, or it risks a false negative whose outcome depends on test ordering rather than on the code under test.

Each individual extension implementation, being its own small class answering to a narrow, focused interface, is naturally testable in isolation from the core subject that hands it out, the same way any small, single purpose class is, which is a direct structural consequence of Gamma's own participant design rather than a claim from a source discussing testing.

## 16. Observability signals

No source found for this entry addresses observability for Extension Object directly, and this dimension is entirely engineering judgement, stated as such rather than as a sourced fact.

The signal most specific to this pattern is a count of extension lookups that return nil against the total number of lookups performed, broken down by the requested extension name or type. A healthy system shows this ratio stable and low, since a query for a genuinely supported extension should almost always succeed. A rising rate against one particular requested type points at either a real capability gap, code asking for something no concrete subject in the running system actually provides, or, in a system built on Eclipse's lazy plug in loading shape, a provider that has not yet activated, the exact ambiguity named in dimension 11, which is itself a reason to log the requested type alongside every miss rather than only a bare count.

A second, cheaper signal, available with no pattern specific instrumentation at all, is simply watching for null reference or null pointer exceptions whose stack trace originates at a call site immediately following a query for an extension. because both of the heavily documented real implementations checked for this entry return nil on a miss rather than raising an error, any code that forgets to check produces this exact, traceable failure shape at the point of use, and a cluster of such exceptions around one extension type is a direct, observable symptom of the unchecked lookup failure mode named in dimension 11.

## 17. Security and privacy implications

No source found for this entry addresses security or privacy for Extension Object directly, and the reasoning here is analytical rather than sourced.

The most concrete implication follows from Microsoft's own formal specification for `QueryInterface`, since a system that fails to enforce a stable, identity consistent set of exposed interfaces on an object opens a narrow but real trust boundary problem. code that has obtained one interface pointer to an object could, in a naive implementation, be denied or granted a different, sensitive interface depending on which reference it happens to query through, which is precisely why the specification requires the exposed interface set to be static per object rather than dynamic. Extension Object's Java and Eclipse style implementations, keyed by string name or by class token and mediated through ordinary object references rather than opaque cross process pointers, do not carry this exact cross process trust concern, but the underlying principle still applies inside a single process. an extension query is effectively a capability check, and any concrete subject whose query method makes an access control decision, granting a sensitive extension only to some callers, is a security relevant surface that deserves the same scrutiny as any other authorization code, even though the pattern's own literature never frames it that way.

Extension Object carries no data handling implications of its own beyond whatever the extension objects and the core subject they are attached to already carry. it introduces no new storage, no new network surface, and no new serialization boundary on its own. Where the pattern's own sources are silent on a security concern, that silence is recorded here rather than an invented one supplied in its place.

## 18. References

Erich Gamma and Richard Helm. "Designing Objects for Extensions." Dr. Dobb's Sourcebook, issue 236, pages 56 to 59, May or June 1995. Cited from Gamma's own later paper's References section, not independently located as a standalone source. Verified 2026-08-23.

Erich Gamma. "The Extension Objects Pattern." Chapter 6, "Extension Object," in Robert C. Martin, Dirk Riehle, Frank Buschmann (editors), Pattern Languages of Program Design 3. Addison-Wesley, 1997. https://ecs.syr.edu/faculty/fawcett/handouts/cse776/PatternPDFs/ExtensionObject.pdf. Verified 2026-08-23.

InformIT. Product listing and table of contents for Pattern Languages of Program Design 3, confirming chapter 6, "Extension Object," Erich Gamma, and publication date. https://www.informit.com/store/pattern-languages-of-program-design-3-9780201310115. Verified 2026-08-23.

Larry O'Brien. "Design Patterns 15 Years Later, An Interview with Erich Gamma, Richard Helm, and Ralph Johnson." InformIT, October 22, 2009. https://www.informit.com/articles/article.aspx?p=1404056. Verified 2026-08-23.

Erich Gamma and Kent Beck. Contributing to Eclipse, Principles, Patterns, and Plug-Ins. Addison-Wesley, 2003. Table of contents, chapter 31 heading "Extension Object/Extension Interface," confirmed via InformIT's product page. https://www.informit.com/store/contributing-to-eclipse-principles-patterns-and-plug-9780321205759. Verified 2026-08-23.

Iluwatar. "Extension Objects Pattern." java-design-patterns catalogue, reference implementation. https://github.com/iluwatar/java-design-patterns/tree/master/extension-objects. Verified 2026-08-23.

Eclipse Foundation. "IAdaptable." Eclipse Platform API reference. https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/IAdaptable.html. Verified 2026-08-23.

Eclipse Foundation. "IAdapterFactory." Eclipse Platform API reference. https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/IAdapterFactory.html. Verified 2026-08-23.

Eclipse Foundation. "IAdapterManager." Eclipse Platform API reference. https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/IAdapterManager.html. Verified 2026-08-23.

Microsoft. "COM Technical Overview." https://learn.microsoft.com/en-us/windows/win32/com/com-technical-overview. Verified 2026-08-23.

Microsoft. "Rules for Implementing QueryInterface." https://learn.microsoft.com/en-us/windows/win32/com/rules-for-implementing-queryinterface. Verified 2026-08-23.

Microsoft. "Creating Shortcut Menu Handlers." https://learn.microsoft.com/en-us/windows/win32/shell/context-menu-handlers. Verified 2026-08-23.

Microsoft. "IServiceProvider.GetService Method." https://learn.microsoft.com/en-us/dotnet/api/system.iserviceprovider.getservice. Verified 2026-08-23.

Martin Fowler. "RoleInterface." Bliki. https://martinfowler.com/bliki/RoleInterface.html. Verified 2026-08-23.

SourceMaking. "Visitor Design Pattern." https://sourcemaking.com/design_patterns/visitor. Verified 2026-08-23.

Wikipedia. "Visitor pattern." https://en.wikipedia.org/wiki/Visitor_pattern. Verified 2026-08-23.

Wikipedia. Absence check confirming no dedicated Extension Object pattern article exists on this site, verified by requesting both plausible article titles, each returning a not found response. https://en.wikipedia.org. Verified 2026-08-23.

**Evidence grade.** mixed

**Most solid findings.** The corrected lineage to Erich Gamma's own 1997 PLoPD3 paper, rather than POSA1, is independently corroborated across the primary paper itself, InformIT's table of contents, and Gamma's own 2009 interview, and the participant structure, consequences, and applicability in dimensions 4, 5, 10, and part of 7 are drawn from direct quotation of that paper. Eclipse's IAdaptable, IAdapterFactory, and IAdapterManager mechanism, covered in dimensions 8, 9, and 11, is sourced to Eclipse's own first party API documentation and is the strongest production evidence in the entry.

**Unverified or unclear.** The 1995 Dr. Dobb's Sourcebook citation is quoted from Gamma's own paper and was not independently located as a standalone bibliographic record. Exact page numbers for the chapter within the 632 page PLoPD3 volume were not obtained. The comparison of Extension Object to Visitor, while grounded in Gamma's own Related Patterns section, is not independently corroborated by a second primary source discussing both patterns together. Whether C sharp's IServiceProvider.GetService is properly characterized as an Extension Object instance rather than a merely structurally similar service locator is this entry's own inference, not a claim Microsoft's documentation makes.

## Code

TypeScript, Python, and Go each model the core subject-and-extension shape directly, following Gamma's own internal, accessor style variant. Kotlin and Swift are omitted, since both languages offer a native protocol extension or interface delegation mechanism that solves the same underlying need more directly, as covered in dimension 8.

### TypeScript

```typescript
interface Extension {
  readonly kind: string;
}

interface TextAccessor extends Extension {
  wordCount(): number;
}

abstract class Component {
  abstract getExtension(kind: string): Extension | null;
}

class TextComponent extends Component {
  private text: string;
  private accessor?: TextAccessor;

  constructor(text: string) {
    super();
    this.text = text;
  }

  getExtension(kind: string): Extension | null {
    if (kind === "textAccessor") {
      if (!this.accessor) {
        const words = this.text;
        this.accessor = {
          kind: "textAccessor",
          wordCount: () => words.split(" ").filter(Boolean).length,
        };
      }
      return this.accessor;
    }
    return null;
  }
}

const component = new TextComponent("the quick brown fox");
const extension = component.getExtension("textAccessor") as TextAccessor | null;
if (extension) {
  console.log(extension.wordCount());
}
```

### Python

```python
class Extension:
    pass


class TextAccessor(Extension):
    def __init__(self, text: str) -> None:
        self._text = text

    def word_count(self) -> int:
        return len(self._text.split())


class Component:
    def get_extension(self, name: str) -> Extension | None:
        return None


class TextComponent(Component):
    def __init__(self, text: str) -> None:
        self._text = text
        self._accessor: TextAccessor | None = None

    def get_extension(self, name: str) -> Extension | None:
        if name == "text_accessor":
            if self._accessor is None:
                self._accessor = TextAccessor(self._text)
            return self._accessor
        return None


component = TextComponent("the quick brown fox")
extension = component.get_extension("text_accessor")
if isinstance(extension, TextAccessor):
    print(extension.word_count())
```

### Go

```go
package main

import (
	"fmt"
	"strings"
)

type Extension interface {
	Kind() string
}

type TextAccessor struct {
	text string
}

func (t *TextAccessor) Kind() string {
	return "textAccessor"
}

func (t *TextAccessor) WordCount() int {
	return len(strings.Fields(t.text))
}

type Component interface {
	GetExtension(name string) Extension
}

type TextComponent struct {
	text     string
	accessor *TextAccessor
}

func (c *TextComponent) GetExtension(name string) Extension {
	if name == "textAccessor" {
		if c.accessor == nil {
			c.accessor = &TextAccessor{text: c.text}
		}
		return c.accessor
	}
	return nil
}

func main() {
	var component Component = &TextComponent{text: "the quick brown fox"}
	extension := component.GetExtension("textAccessor")
	if accessor, ok := extension.(*TextAccessor); ok {
		fmt.Println(accessor.WordCount())
	}
}
```
