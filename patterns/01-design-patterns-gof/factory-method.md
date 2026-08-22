---
name: Factory Method
slug: factory-method
family: 01-design-patterns-gof
category: Creational
aliases: [Virtual Constructor, Factory Hook]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [abstract-factory, template-method, prototype, builder, strategy]
incompatible_with: []
verified: 2026-08-02
---

# Factory Method

## 1. Name, aliases, and lineage

The canonical name is Factory Method. It appears in the Gang of Four catalog as
one of the five creational patterns, described in Erich Gamma, Richard Helm,
Ralph Johnson and John Vlissides, *Design Patterns. Elements of Reusable
Object-Oriented Software*, Addison-Wesley, 1994, chapter 3 (Creational
Patterns), Factory Method. The book states the intent as defining an interface
for creating an object while letting subclasses decide which class to
instantiate ([Wikipedia summary of the GoF intent](https://en.wikipedia.org/wiki/Factory_method_pattern),
verified 2026-08-02).

The book itself records **Virtual Constructor** as the alias, borrowed from C++
practice where a base class cannot have a virtual constructor and a virtual
creation method stands in for one. **Factory Hook** shows up in framework
documentation for the same idea, because the overridable creation method is a
hook the framework calls and the application supplies.

Three different things are called a factory in day-to-day speech, and confusing
them is the most common source of bad Factory Method code.

- **Factory Method (GoF, subclass-based).** An instance method on a type,
  declared abstract or given a default body, that returns a product. The
  *subclass* of the creator overrides it. Selection of the concrete product is
  bound by inheritance, resolved at runtime through dynamic dispatch, and there
  is no conditional over a type code anywhere. The creator has other work to do
  besides creating, and calls its own creation method as part of that work.
- **Simple Factory (an idiom, not a GoF pattern).** A single function or class
  with a switch or map over a string, enum or config value, returning one of
  several concrete types. It appears nowhere in the GoF catalog. It has no
  polymorphism at the creator level. Adding a product means editing the switch,
  which is the exact edit Factory Method exists to avoid.
- **Static Factory Method (Bloch).** A public static method that returns an
  instance of its own class or a subtype, presented as an alternative to a
  public constructor. Joshua Bloch, *Effective Java*, 3rd edition,
  Addison-Wesley, 2018, Item 1, "Consider static factory methods instead of
  constructors". Bloch is explicit that this is not the GoF pattern. It cannot
  be overridden, because static methods do not dispatch, so it solves naming,
  instance caching and return-type flexibility, not subclass extension.

A useful test. If removing the inheritance relationship breaks the design, it is
Factory Method. If it does not, it is one of the other two.

## 2. Problem and context

A class does real work that involves an object it must create, and it cannot
name the concrete class of that object at the point where the work is written.

The situation reads like this in a codebase. There is a class that orchestrates
a process, a document editor, a job runner, a connection pool, a report writer.
Somewhere in the middle of a long method there is a `new` of a concrete type.
Later, a second flavour of the process is needed, identical in every step except
that it operates on a different concrete product. The obvious move is to copy
the orchestrating class and change one line, which duplicates the process. The
second obvious move is to add a flag parameter and branch on it at the `new`,
which grows a branch for every future flavour and forces the orchestrator to
import every product it might ever create.

The context that makes Factory Method the right answer has three parts.

- The creator has real behaviour of its own, not only creation.
- The set of products varies along the same axis as the set of creators, so a
  subclass that specialises the behaviour naturally also specialises the product.
- The library or framework author cannot know the concrete products, because
  they live in code written later by somebody else.

Outside that context the pattern is a liability, see dimension 4.

## 3. Forces

The pattern balances the following competing pressures.

- **Coupling.** Favoured. The creator depends only on the product abstraction,
  so new products arrive without editing the creator.
- **Cognitive load.** Sacrificed. A reader tracing where an object comes from
  must now resolve a virtual call and find the subclass at runtime, rather than
  reading a literal type name at the allocation site.
- **Class count.** Sacrificed. Every product variation costs one creator
  subclass, even when that subclass carries a single method.
- **Consistency.** Favoured within a creator instance. A creator subclass always
  produces the matching product family member, so mismatched pairings become
  hard to express.
- **Latency.** Close to neutral. One extra virtual dispatch per creation is
  irrelevant against allocation cost in a managed runtime, and can matter in a
  tight allocation loop in C++ or Rust where the call resists inlining.
- **Operability.** Mildly sacrificed. The type that actually got created is not
  visible in the source, so an operator diagnosing a production incident needs a
  log line or a trace attribute to know which product was in play.
- **Team topology.** Favoured. The pattern draws a clean seam between a platform
  team that owns the creator and product abstractions, and product teams that
  own concrete subclasses in their own modules and on their own release
  schedule.
- **Cost of change.** Favoured for adding a product, sacrificed for changing the
  product interface, which now ripples to every subclass in every downstream
  repository.

A pattern that gave up nothing would be a language feature, not a pattern. The
price here is paid in indirection and class count.

## 4. Applicability and non-applicability

Reach for Factory Method when the following hold.

- A class cannot anticipate the class of objects it must create, and the answer
  is supplied later by a subclass.
- A framework must delegate one specific creation decision to application code
  while keeping the surrounding algorithm under framework control.
- A creator hierarchy already exists for other reasons, and the product varies
  along the same axis, so the subclass is free.
- Object construction takes several steps and should be specialised per variant
  without leaking that logic to every call site.
- Products must be pooled, cached or recycled, and the creation method is the
  place to decide between handing back an existing instance and allocating.

Do NOT reach for Factory Method in these cases, and the reason matters more than
the rule.

- **There is only one product and no plausible second.** The subclass hierarchy
  is speculative generality. A plain constructor call reads better and deletes
  cleanly. Cross reference the code smell family entry on speculative
  generality.
- **The selection is data-driven, not type-driven.** If the concrete type is
  chosen from a config string, a database column or an HTTP header, subclass
  dispatch cannot express that. A registry or map keyed by the value, or a
  Simple Factory, is the honest shape. Bolting Factory Method on top produces a
  subclass per config value and a lookup that picks the subclass, which is the
  original switch with more files.
- **The creator has no behaviour besides creating.** A creator whose only method
  is the creation method is a Simple Factory wearing an inheritance costume. It
  produces a parallel class hierarchy that carries no information.
- **The language already gives you first-class construction.** In Python, Go,
  TypeScript, Rust and Kotlin a constructor is a value that can be passed as a
  parameter or held in a field. Passing the constructor is the whole pattern
  with none of the classes, see dimension 8.
- **You need families of related products created together.** One creation
  method cannot keep several products consistent with each other. Abstract
  Factory is the pattern for that, and Factory Method is usually how each of its
  operations is implemented.
- **The goal is naming, caching or hiding the concrete return type.** That is
  Bloch Item 1 territory. A static factory method costs one method and no
  hierarchy.
- **The creator subclass would be produced by a dependency injection
  container.** Constructor injection of a supplier or provider gives the same
  substitution with configuration rather than inheritance, and the wiring is
  visible in one place.

## 5. Structure

Four participants, named by the role they play.

- **Product.** The interface or abstract type the creator's algorithm is written
  against. It is the only product-side type the creator knows.
- **ConcreteProduct.** An implementation of Product. It normally lives in the
  same module as the ConcreteCreator that makes it, and often in a module the
  Creator's author has never seen.
- **Creator.** Declares the factory method returning Product, and contains the
  algorithm that consumes the product. The factory method is abstract when the
  creator has no sensible default, or concrete when a default product exists and
  subclasses override selectively. The concrete-default form is the one that
  makes the pattern cheap to adopt, because existing subclasses keep working.
- **ConcreteCreator.** Overrides the factory method to return a ConcreteProduct.
  It may also specialise the surrounding algorithm, and usually should, since a
  ConcreteCreator that overrides nothing else is the degenerate case warned about
  in dimension 4.

Relationships. Creator holds an association to Product, never to
ConcreteProduct. ConcreteCreator inherits from Creator and depends on
ConcreteProduct. The dependency arrow from the abstraction to the concrete type
is therefore reversed compared to the naive design, which is the dependency
inversion payoff, see the principles family entry on the Dependency Inversion
Principle.

A parameterised variant adds a discriminator argument to the factory method, so
one ConcreteCreator can produce several ConcreteProducts. That form trades some
of the polymorphism back for fewer classes, see dimension 8.

## 6. ASCII structure diagram

```
   +---------------------------+                +-------------------+
   |         Creator           |  creates       |     Product       |
   |---------------------------|  - - - - - ->  |-------------------|
   | + doWork()                |   (abstract)   | + operation()     |
   | # createProduct(): Product|                +-------------------+
   +---------------------------+                          ^
                 ^                                        |
                 | extends                                | implements
                 |                                        |
   +---------------------------+                +-------------------+
   |     ConcreteCreatorA      |  creates       | ConcreteProductA  |
   |---------------------------|  ----------->  |-------------------|
   | # createProduct(): Product|                | + operation()     |
   +---------------------------+                +-------------------+
                 ^
                 | extends
                 |
   +---------------------------+                +-------------------+
   |     ConcreteCreatorB      |  creates       | ConcreteProductB  |
   |---------------------------|  ----------->  |-------------------|
   | # createProduct(): Product|                | + operation()     |
   +---------------------------+                +-------------------+

   doWork() is written once in Creator and calls createProduct().
   Only the dashed arrow crosses the abstraction boundary at compile time.
```

## 7. Dynamics

The runtime flow has one property worth stating plainly. The call to the factory
method originates inside the Creator's own code, not from the client. The client
never calls the factory method. That is what separates this from a factory
object the client consults.

```
Client           ConcreteCreatorA      (inherited doWork)    ConcreteProductA
  |                      |                        |                     |
  |-- new ConcreteCreatorA() ------------------->|                     |
  |                      |                        |                     |
  |-- doWork() --------->|                        |                     |
  |                      |-- runs Creator.doWork()|                     |
  |                      |                        |                     |
  |                      |   createProduct()      |                     |
  |                      |<-----------------------|                     |
  |                      |   (virtual dispatch    |                     |
  |                      |    reaches subclass)   |                     |
  |                      |-- new ConcreteProductA() ------------------->|
  |                      |                        |                     |
  |                      |-- returns Product ---->|                     |
  |                      |                        |-- operation() ----->|
  |                      |                        |<-- result ----------|
  |<-- result -----------|                        |                     |
  |                      |                        |                     |
```

Two timing notes. First, the factory method must not be called from the
Creator's constructor in languages where subclass fields are uninitialised
during base construction, which covers Java, C#, Kotlin and Swift. The override
will run against a half-built subclass. Call it lazily on first use instead.
Second, when the factory method caches, the second call returns without
allocating, so the sequence above collapses to a lookup.

## 8. Implementation variants

**Abstract creation method.** The Creator declares the method with no body and
cannot be instantiated. Strongest form. The compiler rejects any subclass that
forgets to supply a product. Costs the ability to use Creator directly.

**Default creation method.** The Creator returns a sensible default product and
subclasses override only when they differ. Weakest coupling for adopters,
because adding the hook to an existing class breaks nothing. The risk is that
the default quietly stays in place in a subclass that meant to override, which
is a silent behaviour bug rather than a compile error.

**Parameterised factory method.** The method takes a discriminator and returns
one of several products. Fewer classes, and the subclass can extend the parent's
switch by handling its own cases and delegating the rest upward. It reintroduces
a conditional, so it earns its place only when the product set is closed and
small.

**Template Method pairing.** The Creator's algorithm is a template method and the
factory method is one of its hooks. This is the shape most frameworks ship,
because it lets the framework own sequencing while the application owns types.
See the Template Method entry.

**Constructor or function as a parameter.** In languages with first-class
functions, the creator holds a `() => Product` field supplied at construction.
Same substitutability, zero subclasses, and the product choice becomes visible
in the wiring code. This is the idiomatic form in Go, TypeScript, Python, Rust
and Kotlin, and the one to prefer unless the creator hierarchy already exists.
The cost is that the creation logic is no longer a named, documented, overridable
member of a published type, which matters for a library with external
implementors.

**Generic or reified type parameter.** C# `where T : new()` and similar
constructs let the creator instantiate a type argument directly. It removes the
subclass but restricts products to a parameterless constructor and cannot decide
anything at runtime.

**Registry-backed creation.** The factory method body consults a registry
populated at startup by product modules. Common in plugin systems. It is Factory
Method at the type level and Simple Factory inside, and it moves failures from
compile time to first call, so registration coverage needs a test.

**Language note on Rust.** Rust has no inheritance, so the classical shape does
not translate. The equivalent is a trait with an associated type and a method
returning it, which is exactly the shape of `IntoIterator`, see dimension 9. The
trait implementor plays ConcreteCreator and the associated type plays
ConcreteProduct.

## 9. Known production uses

**Java Collections Framework, `Collection.iterator()`.** `Collection` declares
`Iterator<E> iterator()` and every concrete collection returns its own private
iterator implementation. Algorithms written against `Collection` and enhanced
`for` loops consume the product without naming it. Java SE 21 API
documentation, `java.util.Collection`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collection.html
verified 2026-08-02.

**Django model fields, `Field.formfield()`.** A model field subclass overrides
`formfield()` to return the form field that a `ModelForm` should use for it.
Django's form-building algorithm calls the method on whatever field subclass is
present, and third-party field packages supply their own. Django 5.2
documentation, "How to create custom model fields", section "Specifying the form
field for a model field", https://docs.djangoproject.com/en/5.2/howto/custom-model-fields/
verified 2026-08-02.

**.NET logging, `ILoggerProvider.CreateLogger(string)`.** Each provider
implementation returns its own `ILogger` for a category name. The logging
factory calls the method on every registered provider without knowing any
concrete logger type. Microsoft .NET API documentation,
`Microsoft.Extensions.Logging.ILoggerProvider.CreateLogger`,
https://learn.microsoft.com/en-us/dotnet/api/microsoft.extensions.logging.iloggerprovider.createlogger
verified 2026-08-02.

**Rust standard library, `IntoIterator::into_iter()`.** The trait declares an
associated type `IntoIter` and a method `fn into_iter(self) -> Self::IntoIter`.
Every implementor chooses its own concrete iterator, and the `for` loop is
written against the trait. Rust standard library documentation,
`std::iter::IntoIterator`, https://doc.rust-lang.org/std/iter/trait.IntoIterator.html
verified 2026-08-02.

**Spring Framework, `FactoryBean.getObject()`.** A bean implementing
`FactoryBean` is treated by the container as a factory for the object it
exposes, and the container calls `getObject()` rather than injecting the
`FactoryBean` itself. Spring Framework Javadoc,
`org.springframework.beans.factory.FactoryBean`,
https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/beans/factory/FactoryBean.html
verified 2026-08-02.

## 10. Consequences

Positive.

- The creator's algorithm is written once against the product abstraction and
  reused by every variant without copying.
- New products arrive without editing existing code, which is the Open Closed
  Principle applied to construction.
- Construction logic for a variant lives in one named, overridable member rather
  than scattered across call sites.
- Product creation becomes an extension point a library can publish and version,
  with a documented contract for external implementors.
- The creation method is a natural place for pooling, caching and instrumentation
  because every product passes through it.

Negative.

- One creator subclass per product variation, even when the subclass carries a
  single method. On a large product set this doubles the type count.
- Indirection makes the code harder to read for someone new. No source line
  names the concrete product.
- A parallel class hierarchy appears, and the two hierarchies must be kept in
  step by convention, since no compiler checks the pairing.
- Changing the Product interface is expensive once external code implements it.
- The pattern cannot express selection driven by runtime data without adding a
  conditional back, which partially undoes the benefit.

## 11. Failure modes and misuse

**The subclass explosion.** Symptom. A directory holding thirty creator classes
with a single one-line method each, and no other behaviour, and a factory that
picks between them by name. Cause. Factory Method applied to a data-driven
choice. Fix. Replace with a registry keyed by the discriminator, or with
constructor references held in a map.

**Override called during construction.** Symptom. A `NullPointerException` in
the overridden factory method on a field the subclass sets in its own
constructor, or a Kotlin or Swift crash on an unset property, that only happens
for some subclasses. Cause. The base constructor calls the factory method before
subclass fields exist. Fix. Move the call to a lazy accessor or an explicit
`init()` step.

**The default that was meant to be overridden.** Symptom. A production tenant
silently gets the default product, discovered when a customer reports the wrong
behaviour weeks later rather than at deploy. Cause. Default creation method plus
a subclass that forgot the override. Fix. Make the method abstract, or add a
test that asserts each ConcreteCreator returns its expected product type.

**Static method mistaken for the pattern.** Symptom. A "factory method" declared
`static` that a subclass tries to override, and the base version keeps running.
Cause. Static members are hidden, not overridden. Fix. Make it an instance
method, or accept that the design is Bloch Item 1 and drop the subclass
hierarchy.

**Creation with hidden side effects.** Symptom. A retry loop or a test helper
that calls the creator twice produces duplicate database rows or two open
sockets. Cause. The factory method registers, connects or writes as well as
allocating. Fix. Make creation pure and move the side effect to an explicit
step, or document the method as non-idempotent and guard it.

**Abstraction leak at the call site.** Symptom. Casts from Product back to a
concrete type appear in the creator's algorithm, followed by `instanceof`
branches. Cause. The Product interface is too narrow for what the algorithm
needs. Fix. Push the missing operation into the Product interface, or admit the
algorithm is not generic and drop the pattern.

**Unbounded caching in the creation method.** Symptom. Steadily growing heap in
a long-running process, retained by a map inside a creator. Cause. Caching added
to the factory method without an eviction policy. Fix. Bound the cache or use
weak references.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Factory Method | Abstract Factory | Simple Factory idiom | Static Factory Method (Bloch Item 1) | Constructor passed as a parameter | Builder |
|---|---|---|---|---|---|---|
| Coupling to concrete types | Low. Creator sees Product only | Low. Client sees the factory interface only | High. The factory names every product | Medium. Caller names the owning class | Low. Only the wiring site names the type | Medium. Builder names its product |
| Adding a new product | New subclass, no edits | New factory implementation, no edits | Edit the switch | New static method on the class | New wiring, no edits | Not the concern |
| Cognitive load | Medium. Indirection through dispatch | High. Two interfaces and a family | Low. One readable switch | Low. A named call | Low. Choice visible in wiring | Medium. Fluent chain |
| Class or type count | Plus one creator per variant | Plus one factory per family | No new types | No new types | No new types | Plus one builder per product |
| Runtime data-driven choice | Poor. Needs a conditional back | Poor. Family chosen elsewhere | Good. That is its job | Good. Branch inside the method | Good. Pick the function at wiring | Not applicable |
| Family consistency across products | Not addressed | Strong. That is its purpose | Not addressed | Not addressed | Not addressed | Not addressed |
| Latency | One virtual call | One virtual call | One branch | Direct call, inlinable | One indirect call | Several calls, one allocation |
| Operability | Concrete type hidden, log it | Same, plus which family | Concrete type at the branch | Concrete type near the caller | Concrete type at wiring | Concrete type visible |
| Team topology | Good. Platform owns the seam | Good for whole families | Poor. Shared file becomes a hotspot | Neutral | Good | Neutral |
| Multi-step assembly of one product | Not addressed | Not addressed | Not addressed | Partially, with overloads | Not addressed | Strong. That is its purpose |

Reading of the table. Factory Method wins where the axis of variation is a type
hierarchy that already exists. Simple Factory wins where the axis is a value.
Abstract Factory wins where several products must agree. A static factory method
wins where the problem is naming and instance control rather than extension. A
constructor passed as a parameter wins in every language where functions are
values and no published extension point is needed.

## 13. Related and incompatible patterns

- **Abstract Factory.** Composes above it. An Abstract Factory declares several
  creation operations for a product family, and each of those operations is
  normally implemented as a Factory Method in the concrete factory. Reach for
  Abstract Factory when consistency between two or more products matters,
  otherwise the extra interface is unearned.
- **Template Method.** The natural host. The factory method is one hook in a
  template method, and the two together are how most frameworks expose an
  extension point while keeping control of sequencing. Factory Method is
  described in the GoF catalog as being called from within a template method for
  exactly this reason.
- **Prototype.** A substitute. Where Factory Method varies the product by
  subclassing the creator, Prototype varies it by cloning a registered instance.
  Prototype avoids the creator hierarchy entirely and suits products configured
  at runtime, at the price of correct deep-copy semantics.
- **Builder.** Solves an orthogonal problem and composes cleanly. Factory Method
  decides *which* class. Builder handles *how* an instance with many optional
  parts is assembled. A factory method returning a partly configured builder is
  a common and sound combination.
- **Strategy.** Frequently confused with it. Both use polymorphism behind an
  interface, but Strategy substitutes an algorithm and Factory Method
  substitutes a construction decision. A creator whose subclasses differ only in
  the product they return is usually better modelled as a Strategy holding a
  supplier.
- **Singleton.** Conflicts in practice rather than in principle. A factory method
  that returns a process-wide singleton removes the substitutability the pattern
  was adopted for, and makes tests order-dependent. If a single instance is
  genuinely required, scope it to the creator instance rather than to the
  process.
- **Dependency injection with a container.** Largely replaces the pattern in
  application code. The container supplies the concrete product or a provider,
  so the creator needs no subclass. Factory Method keeps its place in library
  code that must run without a container, and inside container-managed factories
  such as Spring's `FactoryBean`.
- **Service Locator.** Actively conflicts. A creator that reaches into a global
  locator inside its factory method hides its dependency, which reverses the
  explicitness the pattern buys. See the anti-patterns family entry.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The named refactoring
is Replace Constructor with Factory Method, see the refactoring family entry.
Ordered steps.

1. Find the `new` of the concrete type inside the class that also consumes it.
   Confirm the consuming code touches only members that could live on an
   abstraction.
2. Extract that abstraction from the concrete product. Start with only the
   members the creator actually calls, not everything the product offers.
3. Extract the allocation into a private method returning the new abstraction.
   Nothing else changes. Run the tests.
4. Widen the method to protected and change every internal use so the algorithm
   depends on the abstraction rather than on the concrete type. Run the tests.
5. Create the subclass for the second variant and override the method. At this
   point the pattern exists and pays for itself, because there are two variants.
   Do not stop at step 4 with a single variant, that is the speculative case
   warned about in dimension 4.
6. Decide between abstract and default. Make the base method abstract when
   every variant must choose, and leave a default when adopters would otherwise
   break.
7. Add the type-assertion test from dimension 15 so a forgotten override fails
   at build time rather than in production.

Removing the pattern when it stops earning its place. Signals that it should go
include a creator hierarchy where subclasses override nothing but the factory
method, or a product set that is now chosen by a config value.

1. Confirm the creator subclasses carry no other behaviour. If they do, the
   pattern is still earning something and only the creation part should move.
2. Add a constructor parameter to the base creator that holds a supplier of the
   product, defaulting to the current default product.
3. Change every construction site of a ConcreteCreator to construct the base
   creator with the matching supplier. Run the tests after each site.
4. Inline the factory method into a call through the supplier field.
5. Delete the now-empty subclasses. This is Inline Class plus Replace Subclass
   with Delegate, see the refactoring family entries for both.
6. If the choice is genuinely data-driven, replace the suppliers with a map from
   the discriminator to a constructor reference and delete the abstraction if
   nothing else depends on it.

## 15. Testing and verification

Easier because of the pattern.

- The creator's algorithm can be tested against a fake product supplied by a
  test-only creator subclass, with no mocking framework and no partial mocks.
  This is the main testability payoff, and it works because the seam is a normal
  virtual method.
- A stub creator can return a product that records calls, giving a spy without
  bytecode manipulation.
- Because construction is behind a method, a test can count allocations by
  overriding the method and incrementing a counter, which makes pooling and
  caching behaviour directly assertable.

Harder because of the pattern.

- Knowing which concrete product a running system produced requires either a
  type assertion in the test or a log line in production, since the source does
  not say.
- The contract that the Product interface imposes on implementors now needs its
  own test, because external subclasses will be written against it.

Techniques that apply.

- **Contract test, sometimes called an abstract test case.** Write one test
  class against the Product interface with an abstract creation hook, then
  subclass it once per ConcreteProduct. Every implementation gets the same suite.
  This is Factory Method applied to the test code itself.
- **Type-assertion test per ConcreteCreator.** One test per subclass asserting
  the runtime class of the returned product. Cheap, and it catches the forgotten
  override from dimension 11.
- **Test-only ConcreteCreator over a mock.** Prefer a small handwritten subclass
  to a mocking framework partial mock. Partial mocks that stub a method on the
  class under test hide constructor-ordering bugs, because the mock has no real
  base constructor behaviour.
- **Property test on the registry variant.** When creation is registry-backed,
  assert that every registered key produces a product satisfying the contract,
  which covers the failure that otherwise appears only on first call in
  production.

## 16. Observability signals

The pattern hides the concrete type from the source, so the concrete type has to
appear in telemetry or nobody can diagnose it.

What to record.

- On each creation, a log line or span attribute holding the creator class, the
  product class, and the correlation identifier of the work in progress. Do this
  at debug level for high-frequency creation and at info for expensive products
  such as connections.
- A counter of created products, labelled by concrete product type. This is the
  single most useful signal, because the label distribution answers which
  variants are actually in use.
- A histogram of creation duration, labelled the same way, when creation does
  input or output such as opening a socket or reading a file.
- For caching or pooling creation methods, a hit and miss counter, plus a gauge
  of live instances.
- A counter of creation failures, labelled by product type and error class.

A healthy instance on a dashboard. The per-type creation counter shows the
expected mix for the tenants and configuration in play, and the mix moves only
when a deployment or a configuration change explains it. Creation duration is
flat and well under the surrounding operation. For a pooled creator the hit rate
is high and stable, and the live gauge is flat.

A failing instance. A product type appears that should not exist in this
environment, which usually means a default creation method was not overridden or
a plugin registered itself twice. Or one product type's counter climbs while the
others flatline, which points at a routing or configuration fault upstream. Or
the live-instance gauge climbs monotonically with no matching close counter,
which is the unbounded-cache leak from dimension 11. Or creation duration
develops a long tail on one label only, which localises a slow product without
reading any code.

## 17. Security and privacy implications

The pattern is close to silent on security in its classical, closed form, where
every ConcreteCreator ships in the same build as the Creator. Saying otherwise
would be inventing a concern. Three genuine implications appear once the
extension point is open.

**Untrusted implementors.** A published factory method is an interface that
third-party code implements and the framework then calls. The returned product
runs inside the framework's own algorithm with the framework's privileges. If
plugins are loaded from disk or from a package registry, the creation method is
part of the supply-chain attack surface, and the product should be treated as
untrusted input. Validate the returned object rather than assuming the declared
type implies the expected behaviour, and run plugin code under the least
privilege the runtime allows.

**Registry poisoning.** In the registry-backed variant, whichever code registers
last wins for a key. An attacker who can influence load order or add a module to
the classpath can substitute a product that the creator will then use for every
subsequent request. Fix by making registration fail loudly on a duplicate key
rather than overwriting, and by pinning the registered set at build time where
the plugin set is known.

**Denial of service through creation cost.** Because creation is behind an
abstraction, the creator cannot know that one implementation allocates a large
buffer or opens a network connection per call. A request path that creates one
product per item in an attacker-controlled list turns a cheap request into an
expensive one. Bound the number of creations per request and apply a timeout
inside the calling algorithm, not inside the product.

On privacy the pattern is neutral in itself, with one practical caveat. The
observability advice in dimension 16 says to log the concrete product type. A
class name can encode a customer, a region or a data-residency tier. Where names
carry that, treat the log field as attributable data and apply the same
retention and access rules as any other identifier.

## Code examples

Three languages where the pattern is genuinely idiomatic in different ways.
Java shows the classical inheritance form. TypeScript shows the same shape plus
the function-valued variant that usually replaces it. Python shows the
class-attribute form, which is how the pattern actually appears in Python
libraries. Go is omitted because it has no inheritance, so the pattern
degenerates to a constructor function held in a struct field, which is the
parameter variant already shown in TypeScript rather than the pattern proper.

### Java

```java
interface Export {
    String render(java.util.List<String> rows);
}

final class CsvExport implements Export {
    public String render(java.util.List<String> rows) {
        return String.join("\n", rows);
    }
}

final class JsonExport implements Export {
    public String render(java.util.List<String> rows) {
        return "[\"" + String.join("\",\"", rows) + "\"]";
    }
}

abstract class ReportJob {
    // The algorithm lives here once. Subclasses supply only the product.
    protected abstract Export createExport();

    public final String run(java.util.List<String> rows) {
        if (rows.isEmpty()) {
            return "";
        }
        return createExport().render(rows);
    }
}

final class CsvReportJob extends ReportJob {
    protected Export createExport() {
        return new CsvExport();
    }
}

final class JsonReportJob extends ReportJob {
    protected Export createExport() {
        return new JsonExport();
    }
}

public final class Demo {
    public static void main(String[] args) {
        java.util.List<String> rows = java.util.List.of("a", "b");
        System.out.println(new CsvReportJob().run(rows));
        System.out.println(new JsonReportJob().run(rows));
    }
}
```

### TypeScript

Classical form first.

```typescript
interface Export {
  render(rows: string[]): string;
}

class CsvExport implements Export {
  render(rows: string[]): string {
    return rows.join("\n");
  }
}

class JsonExport implements Export {
  render(rows: string[]): string {
    return JSON.stringify(rows);
  }
}

abstract class ReportJob {
  protected abstract createExport(): Export;

  run(rows: string[]): string {
    if (rows.length === 0) return "";
    return this.createExport().render(rows);
  }
}

class CsvReportJob extends ReportJob {
  protected createExport(): Export {
    return new CsvExport();
  }
}

console.log(new CsvReportJob().run(["a", "b"]));
```

The function-valued variant, which removes both subclasses.

```typescript
type ExportFactory = () => Export;

class ParameterisedReportJob {
  constructor(private readonly createExport: ExportFactory) {}

  run(rows: string[]): string {
    if (rows.length === 0) return "";
    return this.createExport().render(rows);
  }
}

const csvJob = new ParameterisedReportJob(() => new CsvExport());
const jsonJob = new ParameterisedReportJob(() => new JsonExport());
console.log(csvJob.run(["a", "b"]), jsonJob.run(["a", "b"]));
```

### Python

```python
from abc import ABC, abstractmethod


class Export(ABC):
    @abstractmethod
    def render(self, rows: list[str]) -> str: ...


class CsvExport(Export):
    def render(self, rows: list[str]) -> str:
        return "\n".join(rows)


class JsonExport(Export):
    def render(self, rows: list[str]) -> str:
        import json
        return json.dumps(rows)


class ReportJob(ABC):
    @abstractmethod
    def create_export(self) -> Export: ...

    def run(self, rows: list[str]) -> str:
        if not rows:
            return ""
        return self.create_export().render(rows)


class CsvReportJob(ReportJob):
    def create_export(self) -> Export:
        return CsvExport()


class JsonReportJob(ReportJob):
    def create_export(self) -> Export:
        return JsonExport()


if __name__ == "__main__":
    print(CsvReportJob().run(["a", "b"]))
    print(JsonReportJob().run(["a", "b"]))
```

The Python form seen most often in libraries binds the class rather than
overriding a method, which reads as a declaration and keeps the subclass empty
of logic.

```python
class TypedReportJob(ReportJob):
    export_class: type[Export] = CsvExport

    def create_export(self) -> Export:
        return self.export_class()


class JsonTypedReportJob(TypedReportJob):
    export_class = JsonExport
```

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 3, Creational Patterns, section Factory Method.
   Source of the intent, the Virtual Constructor alias, the four participants,
   and the pairing with Template Method.
2. Joshua Bloch. *Effective Java*, 3rd edition. Addison-Wesley, 2018.
   ISBN 978-0-13-468599-1. Item 1, "Consider static factory methods instead of
   constructors". Source of the static factory method distinction in dimension 1.
3. Oracle. *Java SE 21 API Specification*, `java.util.Collection`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collection.html
   Verified 2026-08-02. Source for the `iterator()` production use.
4. Django Software Foundation. *Django 5.2 documentation*, "How to create custom
   model fields", section "Specifying the form field for a model field".
   https://docs.djangoproject.com/en/5.2/howto/custom-model-fields/
   Verified 2026-08-02. Source for the `formfield()` production use.
5. Microsoft. *.NET API documentation*,
   `Microsoft.Extensions.Logging.ILoggerProvider.CreateLogger(String)`.
   https://learn.microsoft.com/en-us/dotnet/api/microsoft.extensions.logging.iloggerprovider.createlogger
   Verified 2026-08-02. Source for the .NET logging production use.
6. Rust project. *Rust standard library documentation*,
   `std::iter::IntoIterator`.
   https://doc.rust-lang.org/std/iter/trait.IntoIterator.html
   Verified 2026-08-02. Source for the associated-type variant and the Rust
   production use.
7. VMware Tanzu. *Spring Framework API documentation*,
   `org.springframework.beans.factory.FactoryBean`.
   https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/beans/factory/FactoryBean.html
   Verified 2026-08-02. Source for the `getObject()` production use.
8. Wikipedia contributors. "Factory method pattern".
   https://en.wikipedia.org/wiki/Factory_method_pattern
   Verified 2026-08-02. Used only to confirm the wording of the GoF intent and
   the attribution, not as a source of explanation.
