---
name: Singleton
slug: singleton
family: 01-design-patterns-gof
category: Creational
aliases: [Highlander, Single Instance, Solitaire]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: contested
related: [factory-method, abstract-factory, monostate, object-pool, flyweight, facade]
incompatible_with: [dependency-injection, service-locator]
verified: 2026-08-02
---

# Singleton

## 1. Name, aliases, and lineage

The canonical name is Singleton. It appears in the Gang of Four catalog as one of
the five creational patterns, described in Erich Gamma, Richard Helm, Ralph
Johnson and John Vlissides, *Design Patterns. Elements of Reusable
Object-Oriented Software*, Addison-Wesley, 1994, chapter 3 (Creational Patterns),
Singleton. The stated intent has two halves that are worth separating, because
almost every argument about the pattern turns on which half a given design
actually wanted. The first half is a guarantee that a class has one instance. The
second half is a global access point to it.

Aliases in real use are thin. **Solitaire** shows up in older literature on
single-instance objects. **Highlander** is folklore, from the film tagline about
there being only one, and appears in code review shorthand rather than in
publications. **Single Instance** is a plain-language restatement used in
specification documents.

The lineage matters more than the aliases, because this is the only GoF pattern
one of its own authors has publicly disowned. In the 2009 InformIT interview
*Design Patterns 15 Years Later*, Erich Gamma, asked which patterns he would
remove from the catalog, answers "I'm in favor of dropping Singleton. Its use is
almost always a design smell" (InformIT, "Design Patterns 15 Years Later. An
Interview with Erich Gamma, Richard Helm, and Ralph Johnson",
https://www.informit.com/articles/article.aspx?p=1404056 verified 2026-08-02).
Attributing the anti-pattern position to a diffuse crowd of developers is a
weaker and less honest framing than attributing it to Gamma, who wrote it down.

Three separate things get called Singleton in day-to-day speech, and conflating
them produces most of the bad arguments on both sides.

- **Singleton the pattern (GoF).** A class that hides its own constructor and
  hands out one instance through a static accessor it owns. The class enforces
  the one-instance rule itself. Callers reach for the instance by naming the
  class.
- **Singleton lifetime in a dependency injection container.** A registration that
  tells the container to build one instance and hand the same reference to every
  requester. The class is a plain class with a public constructor and knows
  nothing about how many of it should exist. The Spring Framework documentation
  is explicit that these are different things and states that "Spring's concept
  of a singleton bean differs from the singleton pattern as defined in the Gang
  of Four (GoF) patterns book", describing the Spring scope as "per-container and
  per-bean" (Spring Framework reference, Bean Scopes,
  https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html
  verified 2026-08-02). Section 4 treats this distinction as the single most
  useful thing to know before adopting either.
- **A module-level or process-level value.** A Python module attribute, a Go
  package variable, a Kotlin `object` declaration. One instance is a property of
  the language runtime rather than of any code the author wrote. Section 8 covers
  where this makes the pattern unnecessary.

## 2. Problem and context

A resource exists once in the running process, and code scattered across the
program needs to reach it without threading a reference through every call.

In a codebase the situation reads like this. There is an object that owns
something the operating system or the process owns once. A connection pool that
must cap total sockets. A registry of loaded plugins that all lookups must agree
on. A logging hierarchy that must route every message through the same handler
set. An in-memory cache whose whole value is that everyone hits the same copy.
Creating a second one is not merely wasteful, it is wrong. Two connection pools
each capped at fifty sockets open a hundred. Two plugin registries disagree about
what is installed.

Passing the object down through constructors from the composition root would
work, and in most programs it is the better answer. The pattern earns its place
when passing it down is genuinely impractical. The classic cases are a library
whose callers must not be forced to hold a handle, a runtime facility that
predates any application object, and code paths that are entered by the platform
rather than by the application, such as a signal handler, a static initializer,
or a serialization hook.

The context that makes Singleton defensible has three parts.

- The single instance is a property of the process or the environment, not a
  policy choice the application might want to change per test or per tenant.
- The object is stateless, or its state is a cache whose contents do not change
  observable behaviour.
- No composition root exists that could own the instance instead.

Remove any one of those three and the pattern turns into the design smell Gamma
named. Section 4 says why, case by case.

## 3. Forces

The pattern balances the following competing pressures.

- **Access convenience.** Favoured, strongly. Any code anywhere reaches the
  instance with one static call and no plumbing. This is the whole appeal and the
  root of every problem below.
- **Coupling.** Sacrificed, badly. Every caller names the concrete class. There
  is no seam at the call site, so substitution requires editing the caller or
  reaching into the class. This is the force the pattern trades away hardest.
- **Testability.** Sacrificed. State that outlives a test method leaks between
  tests, and the dependency is invisible in the constructor signature. Section 11
  covers the observable symptoms.
- **Cognitive load.** Mixed. A single call site reads simply. Reasoning about the
  program as a whole gets harder, because any method might mutate shared state
  without saying so in its signature.
- **Consistency.** Favoured. Everyone sees the same instance by construction,
  which is the point when the object is a registry or a cache.
- **Latency.** Slightly sacrificed in naive forms. A synchronised accessor puts a
  lock on a hot path. Correct lazy forms reduce this to an acquire read, and
  eager forms to a static field load. Section 8 compares them.
- **Operability.** Sacrificed. A process-wide mutable object is a process-wide
  blast radius. One poisoned cache entry affects every request until restart, and
  there is no per-request isolation to fall back on.
- **Cost.** Favoured for expensive resources. One pool, one thread group, one
  parsed configuration, amortised over the process lifetime.
- **Team topology.** Sacrificed. A shared mutable instance is a shared point of
  contention between teams, with no interface boundary to negotiate across. The
  class becomes an edit hotspot.
- **Concurrency correctness.** Sacrificed by default. The instance is reachable
  from every thread, so every mutable field on it is a data race until proven
  otherwise, and the lazy construction itself is a memory-model problem in its
  own right. Section 11 covers the broken double-checked locking idiom in full.

A pattern that sacrifices nothing is described wrongly. Singleton sacrifices
coupling and testability to buy access convenience, and the exchange rate is
poor in most application code.

## 4. Applicability and non-applicability

Reach for Singleton when the following hold.

- The single instance is enforced by something outside the program, such as one
  hardware device, one file lock, or one process-wide runtime facility, so a
  second instance would be incorrect rather than merely redundant.
- The type is a library entry point whose callers cannot be asked to hold a
  handle, and where the object is immutable or thread-safe by construction.
- The object must be reachable from a context that has no injected scope, such as
  a static initializer, a shutdown hook, a signal handler, or a deserialization
  callback.
- The object is a pure lookup table or a memoised pure function, where sharing is
  observably identical to copying.
- The language provides the guarantee for free, in which case the pattern is a
  language feature and none of the machinery below is written by hand. Section 8
  covers Kotlin `object`, a Python module, and Rust `OnceLock`.

Non-applicability. Do NOT reach for Singleton in these cases. The reason matters
more than the rule, and this list is the reason the entry carries a `contested`
maturity.

- **What you actually wanted was one instance per container, not one per
  process.** This is the most common misuse and it is the conflation named in
  section 1. If a dependency injection container is in play, register the class
  with a singleton lifetime and give it an ordinary public constructor. The
  container owns the instance count, the class stays substitutable, tests build
  their own instance directly, and a second container in an integration test gets
  a second instance without a reset hook. The Spring documentation draws exactly
  this line, calling its scope per-container and per-bean rather than one per
  ClassLoader (see section 1 for the citation). Writing a GoF Singleton inside a
  container-managed application gives up every one of those properties and buys
  nothing the container was not offering.
- **The object holds mutable state that tests care about.** A process-wide
  mutable object destroys test isolation. Section 15 covers the mechanics. The
  symptom arrives as tests that pass alone and fail in a suite, which is the
  single most expensive class of test failure to diagnose.
- **The dependency should be visible.** A constructor parameter documents what a
  class needs. A static call inside a method body hides it. Misko Hevery's
  "Singletons are Pathological Liars" makes this argument directly, that a class
  which reaches for global instances "hides required dependencies" so a caller
  reading the API cannot see what the object will touch (Google Testing Blog,
  Misko Hevery, 17 August 2008,
  https://testing.googleblog.com/2008/08/by-miko-hevery-so-you-join-new-project.html
  verified 2026-08-02).
- **You are using it to avoid passing a parameter.** That is a convenience
  argument, not a correctness argument, and it converts a local plumbing cost
  into a global coupling cost. The plumbing cost is paid once. The coupling cost
  is paid on every future change.
- **You need per-tenant, per-request, or per-connection scoping later.** Singleton
  hard-codes the one-instance rule into the class. Widening it later touches
  every call site, because callers named the class rather than an abstraction.
  Assume multi-tenancy arrives.
- **One instance per process is not actually what the runtime gives you.** In
  Java the guarantee is per defining class loader, not per machine and not even
  per process. Section 11 covers this in full.
- **You want lazy initialization and nothing else.** Laziness and instance count
  are separate concerns. `Lazy<T>` in .NET, `lazy` in Kotlin, and `OnceLock` in
  Rust give deferred construction on an ordinary field with no global access
  point attached.
- **The class is a namespace for stateless helpers.** A Singleton holding only
  pure functions is a module wearing an object costume. Use a module, a package,
  or static methods, and skip the instance entirely.
- **Serialization or reflection can reach the class and you did not plan for it.**
  Both defeat a hand-rolled private constructor. Section 11 covers both, and
  section 8 covers the enum form that closes them.

## 5. Structure

The pattern has one participant, which is unusual and is part of why it attracts
criticism. There is no collaboration to describe, only a class enforcing a rule
about itself.

- **Singleton.** The class that owns both the sole instance and the policy that
  there is exactly one. It carries three members. A private static field holding
  the instance, a non-public constructor so no caller can allocate a second, and
  a public static accessor that returns the instance. The class also carries
  whatever real behaviour justified its existence, and that behaviour is the part
  a reviewer should look at hardest, because a Singleton with no behaviour of its
  own is a global variable with extra steps.
- **Client.** Not a participant in any structural sense, which is exactly the
  problem. The client has no declared relationship to the Singleton. It reaches
  for the class by name from inside a method body, so the dependency exists at
  runtime and is absent from every signature, every constructor, and every
  interface. A reader of the client's public surface cannot see the edge.

Relationships. The Singleton has an association to itself through the static
field. Every client has a hidden compile-time dependency on the concrete class,
never on an abstraction. The dependency arrow points from the client at a
concrete type, which is the reverse of the direction the Dependency Inversion
Principle asks for, and is why section 13 lists dependency injection as a
replacement rather than a collaborator.

A variant introduces an interface the Singleton implements, so the accessor
returns the abstraction. This buys substitutability for the type but not for the
lookup, because clients still call the static accessor. To gain a real seam the
accessor itself has to become replaceable, at which point the design has become
a Service Locator, with the problems the anti-patterns family entry describes.

## 6. ASCII structure diagram

```
                +--------------------------------------+
                |             Singleton                |
                |--------------------------------------|
                | - instance   (static, private)       |
                |--------------------------------------|
                | - Singleton()            (private)   |
                | + getInstance()          (static)    |
                | + doWork()                           |
                +--------------------------------------+
                       |                      ^
                       |  holds the only      |
                       +----------------------+
                            instance of itself

     +-----------+      +-----------+      +-----------+
     | ClientA   |      | ClientB   |      | ClientC   |
     +-----------+      +-----------+      +-----------+
           .                  .                  .
           .  Singleton       .  Singleton       .  Singleton
           .  .getInstance()  .  .getInstance()  .  .getInstance()
           .                  .                  .
           +------------------+------------------+
                              |
                              v
                   the one Singleton instance

   Dotted edges are static calls made from inside method bodies.
   No client declares the dependency in a field or a parameter,
   which is why no solid arrow is drawn from a client.
```

## 7. Dynamics

The runtime flow has one property worth stating plainly. The first caller pays
for construction and every later caller does not, so the identity of the first
caller decides when initialization side effects happen. In a lazy Singleton that
opens a socket or reads a file, the timing of that work is decided by whichever
code path happens to run first, which can differ between production and a test
run.

```
ClientA            Singleton (class)          instance
   |                      |                      |
   |-- getInstance() ---->|                      |
   |                      |  instance is null    |
   |                      |-- acquire lock ----->|
   |                      |  re-check null       |
   |                      |-- construct -------->|  <-- side effects run here
   |                      |-- publish field ---->|
   |                      |-- release lock       |
   |<-- reference --------|                      |
   |-- doWork() -------------------------------->|
   |                      |                      |
ClientB (other thread)    |                      |
   |-- getInstance() ---->|                      |
   |                      |  instance is present |
   |                      |  (no lock taken)     |
   |<-- same reference ---|                      |
   |-- doWork() -------------------------------->|
   |                      |                      |
```

The unsafe publication window is the gap between construct and publish. If the
field write becomes visible to ClientB before the constructor's writes to the
object's own fields become visible, ClientB receives a reference to a partly
built object and reads default values from it. Section 11 covers why that
reordering is permitted and what closes it.

A second timing note. Eager initialization moves the whole sequence into class
initialization, which the runtime already serialises, so the diagram collapses to
a single static field read with no lock and no window. That is why section 8
recommends the eager and holder forms over hand-written locking.

## 8. Implementation variants

**Eager static field.** The instance is built during class initialization. The
runtime's own class initialization locking supplies thread safety, so no
application-level synchronisation exists and every access is a plain field read.
Costs the ability to defer expensive construction, and ties construction failure
to class loading, where the resulting error is harder to attribute.

**Initialization-on-demand holder.** A private nested class holds the static
field, and the outer accessor touches the nested class only when called. Class
initialization of the nested type happens on first use, so the form is lazy and
lock-free, using the same runtime guarantee as the eager form. This is the
strongest hand-written form in Java for a lazily built instance.

**Synchronised accessor.** The whole accessor takes a lock. Correct and simple.
The lock is taken on every read forever, not only during construction, so it
becomes a contention point on a hot path. Acceptable when the accessor is called
rarely.

**Double-checked locking with a volatile field.** The accessor reads the field
without a lock, takes the lock only when it reads null, and re-checks inside the
lock. The field must be declared `volatile` or the idiom is broken. Section 11
explains why, and why the fix depends on a specific memory model revision.
Without laziness being genuinely needed, prefer the holder form, which achieves
the same result with no reasoning about memory ordering at all.

**Single-element enum.** The language runtime supplies the instance, the private
constructor, the serialization behaviour, and the defence against reflective
construction. Joshua Bloch recommends this as the preferred approach in
*Effective Java*, 3rd edition, Addison-Wesley, 2018, Item 3, "Enforce the
singleton property with a private constructor or an enum type", noting that a
single-element enum gives a guarantee against multiple instantiation that holds
even against serialization and reflection attacks. Section 11 covers both attack
routes. The cost is that an enum cannot extend a class, so the form is unusable
where the Singleton must inherit an implementation.

**Language-level object declaration.** In Kotlin an `object` declaration is the
pattern as a language feature. The Kotlin documentation states that "the
initialization of an object declaration is thread-safe and done on first access"
and that object declarations "are initialized lazily, when accessed for the first
time" (Kotlin documentation, Object declarations and expressions,
https://kotlinlang.org/docs/object-declarations.html verified 2026-08-02).
Writing the classical form in Kotlin by hand is redundant.

**Module as the instance.** In Python a module is created once and cached, so
module-level state is a Singleton the language already built. The language
reference states that the import system checks `sys.modules` first, "a cache of
all modules that have been previously imported", and that when the name is
present "the associated value is the module satisfying the import, and the
process completes" without re-executing the module body (Python 3 language
reference, The import system,
https://docs.python.org/3/reference/import.html verified 2026-08-02). Writing a
metaclass or a `__new__` override to force one instance in Python is work the
runtime already did, with the added drawback that the resulting object cannot be
reset between tests as easily as a module attribute can be reassigned.

**Once-cell in a static.** Rust has no inheritance and discourages global mutable
state, so the classical shape does not translate. The equivalent is a `OnceLock`
in a `static`, documented as "a thread-safe OnceCell" that "can be used in
statics", with the guarantee that when many threads call `get_or_init`
concurrently "only one function will be executed if the function doesn't panic"
(Rust standard library documentation, `std::sync::OnceLock`,
https://doc.rust-lang.org/std/sync/struct.OnceLock.html verified 2026-08-02).
The type system then forces the shared value to be `Sync`, so the data race that
section 3 flags as an unproven risk in other languages becomes a compile error.

**Once-guarded package function.** In Go the same shape uses `sync.OnceValue`,
documented as returning "a function that invokes f only once and returns the
value returned by f", where "the returned function may be called concurrently"
(Go standard library documentation, package `sync`,
https://pkg.go.dev/sync verified 2026-08-02).

**Lazy wrapper.** In .NET, `Lazy<T>` separates deferred construction from
instance count. The documentation states that "by default, all public and
protected members of the Lazy<T> class are thread safe and may be used
concurrently from multiple threads", and that the default mode uses locking so
only one thread initializes the value (Microsoft .NET API documentation,
`System.Lazy<T>`,
https://learn.microsoft.com/en-us/dotnet/api/system.lazy-1 verified 2026-08-02).
Holding a `Lazy<T>` in an injected field gives laziness without a global
accessor, which is the recommended shape when only laziness was wanted.

**Monostate.** Not a variant of Singleton so much as its inverse. Every instance
shares static state, so callers construct freely and still see one logical
object. It preserves the normal construction syntax and substitutability, and
gives up the ability to reason about identity. Section 13 covers when to prefer
it.

## 9. Known production uses

**Java standard library, `java.lang.Runtime`.** The class documentation states
that "Every Java application has a single instance of class Runtime that allows
the application to interface with the environment in which the application is
running. The current runtime can be obtained from the getRuntime method." The
constructor is not public and `getRuntime()` is the accessor, which is the
classical form applied to a facility the process genuinely owns once. Oracle,
Java SE 21 API Specification, `java.lang.Runtime`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Runtime.html
verified 2026-08-02.

**Python standard library, the `logging` logger registry.** The module keeps one
logger per name and one root logger for the process. The documentation states
that "Multiple calls to getLogger() with the same name will always return a
reference to the same Logger object", and that calling it with no name returns
"the root logger of the hierarchy", of which "all loggers are descendants". This
is the registry-of-singletons variant, where the accessor is keyed rather than
nullary. Python Software Foundation, Python 3 documentation, `logging`,
https://docs.python.org/3/library/logging.html verified 2026-08-02.

**Spring Framework, the singleton bean scope.** Included here as a named
production use of the *lifetime*, and as the reference for why it is not the
pattern. The documentation states that "Spring's concept of a singleton bean
differs from the singleton pattern as defined in the Gang of Four (GoF) patterns
book", explains that the GoF form hard-codes the scope so exactly one instance of
a given class exists per ClassLoader, and states that "the scope of the Spring
singleton is best described as being per-container and per-bean". VMware Tanzu,
Spring Framework reference documentation, Bean Scopes,
https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html
verified 2026-08-02.

**Kotlin standard language feature, `object` declarations.** Shipped as a
first-class declaration form rather than a library type, with thread-safe lazy
initialization on first access, per the citation in section 8. Its existence as a
keyword is the strongest available evidence that the pattern is common enough to
absorb into a language.

## 10. Consequences

Positive.

- The one-instance rule is enforced by the class itself, so no caller can violate
  it by accident, which is the property that matters when a second instance would
  be incorrect rather than merely wasteful.
- Expensive construction happens at most once per process, amortised across every
  caller, with no coordination between callers required.
- Callers reach the instance without any plumbing, which keeps deep call stacks
  free of a parameter that only the leaf needs.
- Lazy forms defer construction until something actually needs the object, so an
  unused facility costs nothing at startup.
- The accessor is one place to add instrumentation, initialization ordering, or a
  readiness check, because every use passes through it.

Negative.

- The dependency is invisible. It appears in no constructor, no field, and no
  interface, so static analysis of a class's requirements is incomplete and code
  review cannot see the edge.
- Substitution requires editing either the caller or the Singleton, because
  callers name the concrete class. There is no seam.
- State outlives every scope smaller than the process, which is the mechanism
  behind the test-isolation damage in section 15.
- The instance count is fixed at the class, so a later requirement for per-tenant
  or per-request instances is a wide refactor rather than a configuration change.
- Correct lazy construction requires reasoning about the memory model, and the
  most widely circulated fast idiom for it was wrong for years.
- The guarantee is weaker than it reads. Section 11 covers class loaders,
  serialization, and reflection, each of which produces a second instance without
  touching the constructor.
- Ordering between multiple Singletons is implicit and fragile. Two lazy
  Singletons that reference each other during construction deadlock or observe a
  half-built peer, depending on the runtime.

## 11. Failure modes and misuse

**The broken double-checked locking idiom.** Symptom. A rare, unreproducible
failure on a multiprocessor machine where a caller receives a Singleton whose
fields hold default values, a null collection or a zero count, followed by a
downstream null dereference far from the accessor. It never reproduces under a
debugger and never on a single-core box. Cause. The idiom reads the instance
field without a lock, locks only when it sees null, and re-checks inside the
lock. Without a memory barrier the write that publishes the field and the writes
that initialize the object may be reordered or may become visible to another
processor in a different order. The signed declaration on this, "The
Double-Checked Locking is Broken Declaration", signed by David Bacon, Joshua
Bloch, Cliff Click, Doug Lea, Bill Pugh, Jeremy Manson and others, states that
"the writes that initialize the Helper object and the write to the helper field
can be done or perceived out of order", and that reordering may come from the
compiler, which "can prove the constructor won't throw exceptions or
synchronize", or from the hardware, because "on a multiprocessor the processor or
the memory system may reorder those writes, as perceived by a thread running on
another processor". The declaration also rules out the common half-fix of a
writer-side barrier alone, noting that "the thread which sees a non-null value
for the helper field also needs to perform memory barriers". Fix. The same
document records that the memory model revision changed the answer. Under the
heading "Under the new Java Memory Model" it states "With this change, the
Double-Checked Locking idiom can be made to work by declaring the helper field to
be volatile. This does not work under JDK4 and earlier", because "JDK5 and later
extends the semantics for volatile" so that a volatile write cannot be reordered
with the writes that precede it and a volatile read cannot be reordered with the
reads that follow. That revision is JSR-133, delivered in Java 5. Bill Pugh,
University of Maryland, "The 'Double-Checked Locking is Broken' Declaration",
https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html verified
2026-08-02. The practical advice is unchanged by the fix. Prefer the holder form,
which needs no reasoning about ordering at all, and reach for volatile
double-checked locking only when the accessor is measurably hot and laziness is
genuinely required.

**Serialization creates a second instance.** Symptom. A configuration or registry
Singleton that behaves correctly until an object graph containing it is written
and read back, after which two instances exist and updates made through one are
invisible through the other. Cause. Deserialization allocates a new object
without calling the declared constructor, so the private constructor guards
nothing. Bloch's Item 3 states that merely adding a serializable declaration is
not sufficient, and that maintaining the guarantee requires declaring every
instance field transient and providing a `readResolve` method that returns the
existing instance. Fix. Supply `readResolve`, or use the single-element enum form
where the runtime supplies serialization behaviour that preserves identity.
Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018,
ISBN 978-0-13-468599-1, Item 3.

**Reflection creates a second instance.** Symptom. A second instance appears in a
process that runs a dependency injection framework, a mocking library, or a
plugin loader, none of which the author expected to construct the class. Cause. A
private constructor is reachable through the reflection API once accessibility is
suppressed. Bloch's Item 3 describes the defence for the hand-rolled form as
making the private constructor throw when it is asked to build a second instance,
and describes the single-element enum as the approach that is well defended
against reflection without the author writing that check. Fix. Prefer the enum
form. Where inheritance forces the hand-rolled form, add the guard in the
constructor, and treat it as a load-bearing check with a test rather than as a
defensive nicety. Same citation as above.

**The guarantee is per class loader, not per machine.** Symptom. A Singleton
holding a cache or a counter behaves as though there are several of it inside one
process, most often in an application server, an OSGi container, a plugin host,
or a hot-reloading development server. Restarting fixes it, which sends
investigation down the wrong path. Cause. Runtime type identity in the Java
Virtual Machine is not the class name alone. The specification states that after
creation, a class or interface is "determined not by its name alone, but by a
pair", that pair being its binary name together with its defining loader, so the
same class file loaded by two loaders yields two distinct runtime types, each
with its own static fields and therefore its own instance. Oracle, *The Java
Virtual Machine Specification, Java SE 21 Edition*, section 5.3, Creation and
Loading, https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-5.html verified
2026-08-02. Fix. Stop treating one instance per process as the contract. Where
the guarantee must hold across loaders, hold the instance in a class loaded by a
shared parent loader, or move the shared state out of the process entirely into a
database row or a distributed lock. The same reasoning extends outward. One
instance per process is not one per host, one per host is not one per cluster,
and any design that reads "there can be only one" and means it across machines
needs a coordination service, not a static field.

**Test pollution from process-wide mutable state.** Symptom. A test that passes
when run alone and fails when the suite runs, or a suite whose result depends on
file ordering or on the shard a test lands in. The failure often lands in a test
that never mentions the Singleton. Cause. The instance and its state outlive the
test method, so mutations made by one test are visible to the next. Because the
dependency is invisible in signatures, the polluted test gives no clue about
which earlier test caused it. This is the mechanism behind the argument in
"Singletons are Pathological Liars", which shows a class that appears simple
while quietly reaching for global instances, so that a test attempting a single
operation triggers real database and payment work the test never asked for
(Google Testing Blog, Misko Hevery, 17 August 2008, citation in section 4). Fix.
Section 15 covers the options in order of preference.

**Singleton the pattern used where singleton lifetime was wanted.** Symptom. A
class inside a container-managed application that has both a private constructor
with a static accessor and a container registration, or a test that cannot build
the class because its constructor is private, so the test reaches for a reset
hook or a reflection hack. Cause. The conflation from section 1. The author
wanted one instance per application and reached for a pattern that gives one
instance per class loader. Fix. Delete the static accessor and the private
constructor, register the plain class with the container's singleton lifetime,
and inject it. The container keeps the one-instance guarantee and the class
regains substitutability, direct construction in tests, and the ability to have a
second instance in a second container. The Spring documentation's own framing of
its scope as per-container and per-bean is the statement of what is being gained
(citation in section 1).

**The accessor with side effects.** Symptom. Start-up ordering bugs that move
when unrelated code changes, or a deadlock at boot between two Singletons whose
lazy constructors reference each other. Cause. Construction inside the accessor
opens sockets, reads files, spawns threads, or touches another Singleton, so the
first caller decides when that happens and the call graph decides the ordering.
Fix. Make construction cheap and pure, move connection and thread work behind an
explicit `start()` that the composition root calls in a known order, and refuse
to reference another Singleton from inside a constructor.

**Singleton as a bag of unrelated globals.** Symptom. A class named for the
application or the configuration that has grown past a thousand lines and is
edited in most merge requests, producing constant conflicts. Cause. The static
accessor made it the cheapest place in the codebase to put anything, so
everything went there. Fix. Split by responsibility first, then inject the
resulting pieces. The convenience of the accessor is what caused the growth, so
keeping the accessor while splitting the class only delays the recurrence.

**Mutable shared state assumed to be safe because construction was made safe.**
Symptom. Corrupted collections, lost counter increments, or an infinite loop
inside a hash map, appearing under load only. Cause. Effort went into making the
accessor thread-safe, and the fields on the returned object were left unguarded.
Thread-safe publication of a reference says nothing about thread-safe use of the
object. Fix. Make the Singleton's state immutable, or guard every field with the
same discipline any shared object requires.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from section 3.

| Force | Singleton (GoF) | Singleton lifetime in a DI container | Monostate | DI with per-instance scope | Static class or module | Object Pool |
|---|---|---|---|---|---|---|
| One-instance guarantee | Strong within one class loader | Strong within one container | Strong for state, not for identity | None. Caller decides | Strong. No instance exists | Bounded count, not one |
| Coupling to the concrete type | High. Every caller names it | Low. Callers name an abstraction | High. Callers name the class | Low. Wiring names the type once | High | Medium. Callers name the pool |
| Dependency visible in the API | No. Hidden in method bodies | Yes. Constructor parameter | No | Yes. Constructor parameter | No | Yes, when injected |
| Test isolation | Poor. State crosses tests | Good. New container per test | Poor. Static state crosses tests | Good. New object per test | Poor if any state exists | Good if the pool is injected |
| Substitutability for a fake | Poor. Needs a reset or a seam | Good. Register a different type | Poor | Good | None | Good |
| Lazy construction | Available, needs care | Container handles it | Not addressed | Caller decides | Class initialization only | Pool decides |
| Concurrency correctness | Author's problem, publication and state | Container handles publication, state still the author's | Author's problem | Confined per instance when not shared | Author's problem | Pool handles handout, state still the author's |
| Cost of adding per-tenant scope later | High. Every call site | Low. Change the registration | High | None. Already scoped | Very high | Low. One pool per tenant |
| Cognitive load at the call site | Low. One static call | Low. A field read | Low | Low | Lowest | Medium. Acquire and release |
| Operability blast radius | Whole process | Whole container | Whole process | One request or one tenant | Whole process | Pool members only |

Reading of the table. Singleton wins on the one-instance guarantee and loses on
almost everything else, so it earns its place only where the guarantee is the
requirement. Container-managed singleton lifetime keeps the guarantee at the
scope that applications actually want and gives back visibility, substitutability
and test isolation, which is why section 4 treats it as the default answer
whenever a container is present. Monostate preserves ordinary construction syntax
at the cost of identity semantics. Per-instance injection wins wherever the
sharing was a convenience rather than a constraint. A static class or module wins
where there is no state to share. Object Pool wins where the real requirement was
a bound on concurrent instances rather than exactly one.

## 13. Related and incompatible patterns

- **Factory Method and Abstract Factory.** Compose with it and are frequently
  confused with it. A factory decides *which* class to build. Singleton decides
  *how many* exist. A factory is often itself a Singleton, and that combination
  is where the pattern does the most damage, because it removes the
  substitutability the factory was adopted to provide and makes tests order
  dependent. Scope such a factory to the composition root instead.
- **Monostate.** A substitute with the same effect and different ergonomics. All
  instances share static state, so callers construct normally and the type stays
  substitutable, while identity comparison stops meaning anything. Prefer it when
  the goal is shared state and the private constructor is causing friction in
  tests or in frameworks that need to construct the type.
- **Object Pool.** The right pattern when the requirement is a bound on the
  number of live instances rather than exactly one. Reaching for Singleton and
  then adding a counter inside it is a pool implemented badly.
- **Flyweight.** Related through instance sharing and different in intent.
  Flyweight shares many immutable instances to save memory and is keyed by
  intrinsic state. Singleton shares one instance to enforce uniqueness. A
  Flyweight factory holding an interned pool is not a Singleton unless the
  factory itself is one.
- **Facade.** Often built as a Singleton for convenience and rarely improved by
  it. A Facade is a stateless entry point, so injecting it costs nothing and
  keeps it replaceable in tests.
- **Dependency injection.** Replaces the pattern in application code, and the
  replacement is the recommendation of section 4. The container owns the instance
  count, the class stays ordinary, and the dependency appears in the constructor.
  Singleton keeps a place in library code that must run with no container, and in
  runtime facilities that predate any application object.
- **Service Locator.** Actively conflicts, and is the shape a Singleton drifts
  into when someone adds a setter to make it testable. Both hide dependencies
  behind a global lookup. Swapping one for the other trades a compile-time hidden
  dependency for a runtime hidden dependency and gains nothing. See the
  anti-patterns family entry.
- **Borg idiom.** The Python spelling of Monostate, sharing instance dictionaries
  across objects. Mentioned because Python code that wants a Singleton usually
  wants a module instead, per section 8.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. This direction should be
rare, and the honest first step is to check whether the container-managed
lifetime from section 4 solves the problem instead.

1. Confirm the one-instance requirement is real. Write down what breaks if a
   second instance exists. If the answer is only wasted memory, stop and use
   Object Pool or plain injection.
2. Confirm no composition root can own the instance. If one exists, build the
   instance there and pass it. Stop.
3. Make the class's state immutable, or move mutable state out of it. This
   removes most of the cost the pattern imposes before the pattern is adopted.
4. Add the static accessor, keeping the public constructor for now, so nothing
   breaks and tests keep building instances directly. Run the tests.
5. Migrate call sites to the accessor one at a time. Run the tests after each.
6. Restrict the constructor. In Java, prefer converting to a single-element enum
   at this step, which closes the serialization and reflection routes from
   section 11 without extra code.
7. Add the initialization-order test and the concrete-type test from section 15.

Removing the pattern when it stops earning its place. The signals are a reset
hook that exists only for tests, a test suite whose result depends on ordering,
or a new requirement for per-tenant or per-request instances.

1. Add a public or internal constructor alongside the existing accessor. Nothing
   else changes. Run the tests. This alone recovers most testability, because
   tests can now build their own instance.
2. Change the accessor to return a field held by the composition root rather than
   a static field it owns. The static call still works, so no call site changes
   yet.
3. Introduce the instance as a constructor parameter on one caller, defaulting to
   the accessor. Run the tests. Repeat per caller, innermost first, so the
   parameter does not have to be threaded through code that has not been
   converted.
4. When no caller uses the accessor, delete it and the static field. This is
   Replace Global Reference with Parameter, and where a seam is needed before the
   caller can be changed, Michael Feathers' Introduce Static Setter is the
   documented interim step. See the refactoring family entries.
5. Register the class with the container's singleton lifetime, or build it once
   in `main`. The one-instance guarantee survives, at a scope that tests can
   control.
6. Where the class had grown into a bag of globals, split it before step 3, not
   after. Injecting a thousand-line object into twenty constructors makes the
   next split harder.

## 15. Testing and verification

Easier because of the pattern. The list is short and honest.

- Fixture setup is trivial, because no test has to build or wire the object. For
  a genuinely immutable Singleton this is a real saving.
- The accessor is one place to install a test hook, if one is added deliberately.

Harder because of the pattern.

- State crosses test boundaries, so tests stop being independent. The failure
  arrives as order dependence, which is expensive to diagnose because the failing
  test and the polluting test are different tests.
- Substituting a fake requires either a static setter, which is a mutable global
  in itself, or a class-loader trick, or a mocking framework that rewrites static
  members, all of which are heavier than a constructor parameter.
- The dependency is invisible, so a reader of a test cannot tell from the class
  under test which external systems the test will touch.
- Parallel test execution becomes unsafe where the Singleton is mutable, which
  caps suite speed.

Techniques that apply, in order of preference.

- **Do not test through the accessor.** Give the class an ordinary constructor
  and have tests build their own instance. The accessor stays for production
  callers and the tests ignore it. This removes the whole problem and costs one
  visible constructor.
- **Fresh container per test.** Where a container owns the lifetime, build a new
  container in setup. The one-instance rule holds inside each test and no state
  crosses the boundary. This is the payoff of the section 4 recommendation.
- **Explicit reset hook, package private, with a guard.** A `resetForTests()`
  that tests call in teardown. It works and it is a mutable global, so keep it
  package private, keep it out of the published surface, and treat any production
  call to it as a defect.
- **Fresh class loader per test.** Reloading the class in a new loader yields a
  new static field, per the identity rule cited in section 11. It works and it is
  slow, so reserve it for the cases where nothing else is available.
- **Order-dependence detector.** Run the suite in a randomised order in
  continuous integration. This converts the intermittent order-dependent failure
  into a reproducible one with a recorded run order, which is the difference
  between a bug that gets fixed and a bug that gets retried.
- **Concurrent construction test.** Start many threads that call the accessor at
  once and assert every returned reference is identical and fully initialized.
  This is the test that catches an unsafe publication bug, and it should assert on
  the object's fields rather than on the reference alone, because the reference
  arrives before the fields in exactly the failure section 11 describes.
- **Serialization round-trip test.** Serialize and deserialize the instance and
  assert reference equality with the accessor's result. One test, and it catches
  the failure that otherwise appears only after a cache is persisted.

## 16. Observability signals

The pattern hides the dependency from the source, so telemetry has to carry what
the code does not say. The signals worth recording are about initialization,
identity, and contention, in that order.

What to record.

- A single info-level log line at construction, carrying the class name, the
  identity hash of the instance, the thread that constructed it, and the elapsed
  construction time. This line should appear exactly once per process. Two of
  them is the class-loader or serialization failure from section 11 announcing
  itself, and it is the cheapest possible detector for both.
- A counter of accessor calls where the instance was constructed, labelled by
  class. In a healthy process this counter reaches one and stays there for the
  lifetime of the process.
- Time spent waiting on the accessor's lock, for the synchronised variant. A
  histogram here answers whether the lock is a hot-path cost or noise, which is
  the measurement that decides whether the holder form is worth adopting.
- For a Singleton holding a cache or a pool, a gauge of entries or live members
  and a hit and miss counter. Because the object outlives every request, an
  unbounded collection inside it grows for the life of the process.
- For a Singleton holding a connection or a thread group, a gauge of live
  connections or threads, so the process-wide bound the pattern was adopted to
  enforce is visible rather than assumed.

A healthy instance on a dashboard. Exactly one construction line per process
start, with construction time flat across deploys. The construction counter at
one. Accessor lock wait at or near zero. Cache and pool gauges flat after warm
up, with a stable hit rate. Live connection count at or under the configured
bound on every node.

A failing instance. Two or more construction lines in one process, which is the
duplicate-instance failure and should page rather than warn, because every cache
and counter in the object is now split. A construction line appearing hours after
start, meaning a lazily built facility was reached for the first time on a
production path that was expected to be warm. Accessor lock wait developing a
tail under load, which is the synchronised accessor becoming a contention point.
A memory gauge inside the object climbing monotonically with no eviction counter
moving, which is the unbounded collection above. Live connections above the bound
across the fleet, which usually means the guarantee is holding per class loader
rather than per process, exactly as section 11 predicts.

## 17. Security and privacy implications

The pattern is close to silent on security in a closed program that loads one
copy of the class and never deserializes it. Claiming otherwise would be
inventing a concern. Four genuine implications appear once the object holds
anything sensitive or once untrusted input can reach it.

**Process-wide blast radius on any state corruption.** Because one instance
serves every request, any attacker-influenced value written into it is visible to
every subsequent request from every user. A Singleton cache keyed carelessly,
where the key omits the tenant or the authenticated principal, turns a cache into
a cross-tenant data leak, and the leak persists until restart because nothing
smaller than the process bounds the object's lifetime. Key every entry in a
shared cache by the full security context, and treat any per-user value stored on
a process-wide object as a defect rather than an optimisation.

**Long-lived secrets in memory.** A Singleton holding credentials, a decryption
key, or a session token keeps those bytes resident for the whole process
lifetime, which widens the window for a memory disclosure bug, a core dump, or a
heap snapshot taken for debugging to expose them. Where the runtime allows it,
hold a key in a form that can be zeroed after use and rebuilt on demand, and keep
it out of any object whose lifetime the code does not control.

**Reflection and deserialization as instance-forging routes.** Both routes in
section 11 are correctness failures first and security failures second. An
attacker who can influence a deserialized object graph can produce a second
instance of a class the program treats as unique, which defeats any invariant the
program derived from uniqueness, including a rate limiter, a nonce store, or an
access-decision cache. The enum form closes both routes at the language level,
per Bloch's Item 3, and is the reason section 8 recommends it wherever
inheritance does not forbid it.

**Initialization ordering as a denial-of-service surface.** A lazily built
Singleton whose constructor performs expensive or network-bound work runs that
work on whichever request arrives first. An unauthenticated endpoint that
triggers the construction lets an attacker choose the moment and pay none of the
cost, and if construction is behind a lock, concurrent requests queue behind it.
Build such objects eagerly at start-up, behind the health check, so the process
is not marked ready until the work is done.

On privacy the pattern is neutral in itself, with one practical caveat that
follows from section 16. The recommended construction log line carries an
identity hash and a thread name, neither of which is attributable data. The cache
and pool gauges are aggregate and equally safe. What is not safe is the tempting
next step of logging cache keys to diagnose a duplicate-instance problem, because
a cache key on a process-wide object frequently contains a user or tenant
identifier. Log key counts and hit rate rather than keys.

## Code examples

Six languages, chosen to make three different points. Java shows the classical
hand-written forms, the memory-model trap, and the enum form that closes the
serialization and reflection routes. TypeScript shows the module-scoped form that
is idiomatic there, and the injected alternative that replaces it. Python, Kotlin,
Rust and Go each show that the language already supplies the guarantee, so the
classical machinery is redundant.

### Java

The holder form. Lazy, thread-safe, and free of any reasoning about memory
ordering, because class initialization is already serialised by the runtime.

```java
public final class ConnectionRegistry {

    private ConnectionRegistry() {
    }

    // The nested class is initialized on first touch, not with the outer class.
    private static final class Holder {
        static final ConnectionRegistry INSTANCE = new ConnectionRegistry();
    }

    public static ConnectionRegistry getInstance() {
        return Holder.INSTANCE;
    }

    public int openCount() {
        return 0;
    }
}
```

Double-checked locking. Correct only because the field is `volatile`, and only on
Java 5 or later. Prefer the holder form above unless the accessor is measurably
hot and laziness is a hard requirement.

```java
public final class LazyRegistry {

    // Removing volatile here reintroduces the unsafe publication bug.
    private static volatile LazyRegistry instance;

    private LazyRegistry() {
    }

    public static LazyRegistry getInstance() {
        LazyRegistry local = instance;
        if (local == null) {
            synchronized (LazyRegistry.class) {
                local = instance;
                if (local == null) {
                    instance = local = new LazyRegistry();
                }
            }
        }
        return local;
    }
}
```

The single-element enum. The runtime supplies the instance, the constructor
restriction, the serialization identity, and the defence against reflective
construction.

```java
public enum Settings {
    INSTANCE;

    private final java.util.Map<String, String> values = new java.util.HashMap<>();

    public String get(String key) {
        return values.getOrDefault(key, "");
    }

    public void put(String key, String value) {
        values.put(key, value);
    }
}
```

### TypeScript

A module body runs once per module specifier, so a module-scoped constant is the
idiomatic form and no class-level machinery is required.

```typescript
class Clock {
  private started = Date.now();

  uptimeMs(): number {
    return Date.now() - this.started;
  }
}

export const clock = new Clock();
```

The injected alternative, which keeps the same production wiring and lets a test
build its own instance with no reset hook.

```typescript
interface Clocklike {
  uptimeMs(): number;
}

class Report {
  constructor(private readonly clock: Clocklike) {}

  render(): string {
    return `up ${this.clock.uptimeMs()}ms`;
  }
}

const fixed: Clocklike = { uptimeMs: () => 1000 };
console.log(new Report(fixed).render());
```

### Python

The module is the instance. Writing a metaclass to force one instance duplicates
what the import system already does.

```python
# registry.py
_plugins: dict[str, object] = {}


def register(name: str, plugin: object) -> None:
    _plugins[name] = plugin


def get(name: str) -> object | None:
    return _plugins.get(name)
```

Where a real object is wanted rather than module functions, build it once at
module scope and let the import cache do the work.

```python
class Registry:
    def __init__(self) -> None:
        self._plugins: dict[str, object] = {}

    def register(self, name: str, plugin: object) -> None:
        self._plugins[name] = plugin


registry = Registry()
```

### Kotlin

The pattern is a keyword. Initialization is lazy and thread-safe by the language
definition, so the classical form written by hand adds nothing.

```kotlin
object FeatureFlags {
    private val enabled = mutableSetOf<String>()

    fun enable(name: String) {
        enabled.add(name)
    }

    fun isEnabled(name: String): Boolean = name in enabled
}

fun main() {
    FeatureFlags.enable("beta")
    println(FeatureFlags.isEnabled("beta"))
}
```

### Rust

There is no inheritance and no implicit global constructor, so the classical form
does not translate. A `OnceLock` in a `static` gives one lazily built value, and
the type system forces the shared value to be safe to share.

```rust
use std::sync::OnceLock;

struct Config {
    retries: u32,
}

static CONFIG: OnceLock<Config> = OnceLock::new();

fn config() -> &'static Config {
    CONFIG.get_or_init(|| Config { retries: 3 })
}

fn main() {
    println!("{}", config().retries);
}
```

### Go

A package-level function guarded by `sync.OnceValue`. The value is built on first
call and the guard is safe under concurrent calls.

```go
package config

import "sync"

type Config struct {
	Retries int
}

var Get = sync.OnceValue(func() *Config {
	return &Config{Retries: 3}
})
```

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 3, Creational Patterns, section Singleton. Source
   of the two-part intent, the single participant, and the structure.
2. Bill Pugh (maintainer), signed by David Bacon, Joshua Bloch, Cliff Click,
   Doug Lea, Jeremy Manson and others. "The 'Double-Checked Locking is Broken'
   Declaration". University of Maryland.
   https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html
   Verified 2026-08-02. Source for the reordering failure, the insufficiency of a
   writer-side barrier alone, and the statement that a volatile field makes the
   idiom work under the revised memory model delivered in Java 5 and not under
   JDK 4 or earlier.
3. Joshua Bloch. *Effective Java*, 3rd edition. Addison-Wesley, 2018.
   ISBN 978-0-13-468599-1. Item 3, "Enforce the singleton property with a private
   constructor or an enum type". Source for the serialization defence with
   transient fields and `readResolve`, the reflective construction defence, and
   the recommendation of the single-element enum.
4. InformIT, with Erich Gamma, Richard Helm, Ralph Johnson. "Design Patterns 15
   Years Later. An Interview with Erich Gamma, Richard Helm, and Ralph Johnson",
   2009. https://www.informit.com/articles/article.aspx?p=1404056
   Verified 2026-08-02. Source for Gamma's own position that he favours dropping
   Singleton and that its use is almost always a design smell.
5. Misko Hevery. "Singletons are Pathological Liars". Google Testing Blog,
   17 August 2008.
   https://testing.googleblog.com/2008/08/by-miko-hevery-so-you-join-new-project.html
   Verified 2026-08-02. Source for the hidden-dependency argument and the test
   that unexpectedly reaches real systems.
6. Oracle. *The Java Virtual Machine Specification, Java SE 21 Edition*,
   section 5.3, Creation and Loading.
   https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-5.html
   Verified 2026-08-02. Source for runtime type identity being the pair of binary
   name and defining loader, which is why the guarantee is per class loader.
7. VMware Tanzu. *Spring Framework reference documentation*, Core Technologies,
   Bean Scopes.
   https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html
   Verified 2026-08-02. Source for the explicit distinction between the GoF
   pattern and container singleton scope, and for the per-container and per-bean
   wording.
8. Oracle. *Java SE 21 API Specification*, `java.lang.Runtime`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Runtime.html
   Verified 2026-08-02. Source for the single-instance-per-application statement
   and the `getRuntime` accessor.
9. Python Software Foundation. *Python 3 documentation*, `logging`.
   https://docs.python.org/3/library/logging.html
   Verified 2026-08-02. Source for `getLogger` returning the same object per name
   and for the root logger.
10. Python Software Foundation. *Python 3 language reference*, The import system.
    https://docs.python.org/3/reference/import.html
    Verified 2026-08-02. Source for `sys.modules` acting as the module cache, so a
    module is a Singleton the runtime supplies.
11. JetBrains. *Kotlin documentation*, Object declarations and expressions.
    https://kotlinlang.org/docs/object-declarations.html
    Verified 2026-08-02. Source for object declarations being lazily and
    thread-safely initialized on first access.
12. Rust project. *Rust standard library documentation*, `std::sync::OnceLock`.
    https://doc.rust-lang.org/std/sync/struct.OnceLock.html
    Verified 2026-08-02. Source for the thread-safe once-cell usable in statics
    and the single-execution guarantee of `get_or_init`.
13. Go project. *Go standard library documentation*, package `sync`.
    https://pkg.go.dev/sync
    Verified 2026-08-02. Source for `Once.Do` and `OnceValue` semantics.
14. Microsoft. *.NET API documentation*, `System.Lazy<T>`.
    https://learn.microsoft.com/en-us/dotnet/api/system.lazy-1
    Verified 2026-08-02. Source for `Lazy<T>` being thread safe by default and for
    the separation of laziness from instance count.
