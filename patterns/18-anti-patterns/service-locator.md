---
name: Service Locator
slug: service-locator
family: 18-anti-patterns
category: Anti-pattern
aliases: [Locator Pattern, Registry-Based Lookup, Central Service Registry]
first_described: "Alur, Crupi, Malks 2001 (Core J2EE Patterns)"
maturity: contested
related: [dependency-injection, singleton-abuse, factory-method, abstract-factory, layered-architecture, facade]
incompatible_with: [dependency-injection, inversion-of-control]
verified: 2026-08-02
---

# Service Locator

## 1. Name, aliases, and lineage

The canonical name is Service Locator. It entered wide circulation through
Deepak Alur, John Crupi, and Dan Malks, *Core J2EE Patterns. Best Practices and
Design Strategies*, Prentice Hall, first edition 2001, where it is catalogued
among the J2EE patterns as a way to encapsulate the lookup of Enterprise
JavaBeans, JMS connection factories, and other JNDI-registered resources
behind a single class, so that the expensive `InitialContext` lookup and its
verbose exception handling did not have to be repeated in every client that
needed a resource. The pattern's original problem was concrete and dated. JNDI
lookups in J2EE were slow, the lookup API threw checked exceptions, and the
lookup code was near-identical everywhere it appeared, so a single object that
performed the lookup once and cached the result was a genuine improvement over
copy-pasted `InitialContext` calls scattered through every servlet and
session bean.

Common aliases include Locator Pattern, used interchangeably in older J2EE
literature, Registry-Based Lookup, used in general architecture writing when
the pattern is being discussed without the J2EE-specific vocabulary, and
Central Service Registry, used when the emphasis is on the single shared
object rather than the lookup call itself.

Martin Fowler gave the pattern its most widely read modern definition in "Inversion
of Control Containers and the Dependency Injection pattern", stating plainly, "The
basic idea behind a service locator is to have an object that knows how to get
hold of all of the services that an application might need" (Martin Fowler,
"Inversion of Control Containers and the Dependency Injection pattern",
https://martinfowler.com/articles/injection.html, section "Using a Service
Locator", verified 2026-08-02). Fowler treats Service Locator and Dependency
Injection as the two competing answers to the same underlying problem, how a
component acquires the collaborators it depends on without constructing them
itself, and he is explicit about the axis that separates them. "The important
difference between the two patterns is about how that implementation is
provided to the application class. With service locator the application class
asks for it explicitly by a message to the locator. With injection there is no
explicit request, the service appears in the application class" (same source,
verified 2026-08-02).

A naming collision worth resolving up front, because it causes real confusion
in code review. The Java platform ships `java.util.ServiceLoader`, described in
its own Javadoc as "A facility to load implementations of a service" (Oracle,
Java SE 17 API documentation, `java.util.ServiceLoader`,
https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ServiceLoader.html,
verified 2026-08-02). `ServiceLoader` discovers *provider implementations of an
interface a caller already depends on statically* through a manifest file
under `META-INF/services`, it does not hold a general-purpose bag of unrelated
services keyed by name or type, and application code never asks it for
something outside the one interface it was constructed against. That is a
service-provider discovery mechanism, the Service Provider Interface idiom,
not the Service Locator anti-pattern this entry describes, and the two should
never be conflated in a code review comment. The distinction matters for
dimension 4 below.

## 2. Problem and context

A component needs a collaborator to do its work, a repository, a logger, a
payment gateway client, a feature-flag reader, and it does not want to be
handed a concrete instance by whoever constructs it. Two shapes solve this.
One is to declare the dependency as a constructor or method parameter and let
whatever assembles the object graph supply it. The other is to give the
component a reference to a shared, globally reachable object and let the
component ask that object, by name or by type, for what it needs, at the
moment it needs it, inside its own method bodies.

The context that produces Service Locator, historically, was a platform where
constructor injection was awkward or unavailable. Early J2EE containers
managed component lifecycles themselves, an EJB's home interface was obtained
through JNDI, and there was no dependency-injection container standing between
the platform and the component to wire constructor arguments. A class that
needed three EJB references either repeated the JNDI lookup boilerplate three
times, wrapped it in a static helper once and called that helper three times,
or built a full inversion-of-control container, which in 2001 did not yet
exist as a mainstream J2EE option. The middle option, a single class holding a
cache of already-looked-up resources, reachable from anywhere via a static
method or a well-known registry entry, was the Service Locator, and for the
JNDI-lookup problem specifically it was a real improvement.

The context that turns Service Locator from a mild convenience into a
liability is different from the context that produced it. Modern platforms,
Spring, ASP.NET Core, Angular, most current dependency-injection containers in
every mainstream language, construct the object graph for you and hand each
component exactly the collaborators its constructor declares. In that context
a service locator is not solving a lookup-cost problem, because the container
already solved that. It is instead being reached for out of habit, out of a
desire to avoid changing a constructor signature, or because a piece of code
runs somewhere the container's own injection machinery does not reach, and in
every one of those cases it reintroduces the exact hidden-dependency problem
the container was built to remove. Dimension 4 draws the line between the
narrow cases where the pattern is still defensible and the much larger set of
cases where reaching for it is a regression to 2001.

## 3. Forces

**Discoverability of dependencies against convenience of not changing a
signature.** A constructor parameter list is a contract a reader can see
without running the program. A call to `Locator.get(PaymentGateway.class)`
buried in a method body is invisible from the outside, and it is exactly this
invisibility that Service Locator trades for the convenience of never having
to touch a constructor when a new collaborator is needed.

**Compile-time safety against runtime flexibility.** Constructor injection
fails to compile if a required dependency is missing from the graph.
A locator lookup by string key or by an unregistered type fails at runtime,
often deep inside a call stack, often only on the code path that exercises
that particular branch. The locator wins when the set of implementations
genuinely cannot be known until runtime, plugin architectures being the clear
case, and loses everywhere the set is knowable at wiring time, which is most
application code.

**Testability against setup ceremony.** A component wired through constructor
injection is trivially testable, pass a test double as the argument. A
component that pulls a collaborator from a locator is testable only if the
locator itself is swappable, and every existing analysis of the pattern
converges on this as the sharpest cost. Wikipedia's summary states it plainly,
"The registry makes code harder to test, since all tests need to interact
with the same global service locator class to set the fake dependencies of a
class under test" (Wikipedia, "Service locator pattern",
https://en.wikipedia.org/wiki/Service_locator_pattern, verified 2026-08-02).
A shared, often static, locator state leaking between test cases is a
recurring source of order-dependent test flakiness that a genuinely isolated
constructor-injected test never has to guard against.

**Coupling to the locator itself against coupling to individual
dependencies.** Removing individual dependency imports from a class's
signature does not remove coupling, it relocates it. Every class that calls
the locator is now coupled to the locator's own type and lifecycle, and Fowler
names this cost directly, "The key difference is that with a Service Locator
every user of a service has a dependency to the locator" (Fowler, same source
as above, verified 2026-08-02). A codebase with a hundred classes calling one
locator has not reduced its coupling, it has concentrated it into a single
class that every other class now depends on, which is itself a coupling
concern worth naming, even though Fowler's own conclusion in the piece is
comparatively mild toward Service Locator for this reason. See dimension 10.

**Migration cost against long-term health.** A codebase already built around
a service locator is expensive to migrate away from precisely because the
dependency graph is invisible in the code, which means the migration itself
requires reading every call site to reconstruct the graph that constructor
injection would have made visible for free. This is a force that argues for
never adopting the pattern in new code even when its short-term convenience is
real, because the debt compounds with every class added.

## 4. Applicability and non-applicability

Reach for a locator-shaped lookup only in these cases, and treat every one of
them as narrow.

- The set of implementations is genuinely unknown at compile time and is
  discovered from the environment, a plugin directory, a classpath scan, an
  installed extension list, where the caller cannot enumerate the interface's
  implementors in a constructor signature because the whole point is that new
  ones arrive without a rebuild. This is the Service Provider Interface case,
  and `java.util.ServiceLoader` and equivalents in other platforms are the
  correct tool for it, not a hand-rolled service locator.
- The calling code lives entirely outside the reach of any injection
  container and there is no realistic way to route it through one, most
  commonly a static factory method, an ORM entity's lifecycle callback, or a
  legacy framework's own object-construction hook that predates the
  application's dependency-injection setup and cannot be changed. Even here,
  the locator call should be isolated to the single seam where the framework
  hands control to your code, a "composition root" adjacent boundary, never
  scattered through ordinary business logic.
- A short-lived script or a one-off tool with a single entry point, where the
  entire notion of an object graph is overkill and a small registry read once
  at the top of `main` is simpler than any container.

Do NOT reach for it in any of these cases, which cover the overwhelming
majority of application code written on a platform with a real
dependency-injection container.

- Any class managed by Spring, ASP.NET Core, Angular, Dagger, Guice, or an
  equivalent container. The container already builds the graph. Calling
  `context.getBean(X.class)`, `serviceProvider.GetService<X>()`, or
  `Injector.get(X)` from inside a component the container itself constructed
  is not a workaround for a missing feature, it is bypassing the feature that
  is already present. The .NET dependency-injection guidelines state this
  directly under "Recommendations", "Avoid using the service locator pattern.
  For example, don't invoke GetService to obtain a service instance when you
  can use DI instead. Another service locator variation to avoid is injecting
  a factory that resolves dependencies at runtime. Both of these practices mix
  Inversion of Control strategies" (Microsoft, ".NET dependency injection
  guidelines",
  https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection-guidelines,
  section "Recommendations", verified 2026-08-02).
- Avoiding a constructor signature change because a class already has too many
  parameters. That is a signal the class violates the Single Responsibility
  Principle, not a justification for hiding a new dependency in a locator
  call. The fix is to split the class, not to make its true dependency count
  invisible.
- Testing convenience, the temptation to have the test configure the locator
  instead of passing a mock. This inverts the actual cost, because it now
  requires global mutable state to be reset between tests, which is strictly
  harder than passing a constructor argument.
- Lazily deferring an expensive dependency's construction. That is the
  `Lazy<T>` or provider-injection problem, and it has a dedicated, narrower
  answer, injecting a factory or a lazy wrapper of the specific type, which
  keeps the dependency visible in the constructor signature while deferring
  its instantiation. A general-purpose locator is a much blunter tool for this
  than a typed lazy provider.

## 5. Structure

**Service Locator.** The central lookup object. Holds, or knows how to obtain,
a mapping from a key, most often a type or an interface, sometimes a string
name, to a concrete service instance. Exposes a `get` or `locate` operation
that returns the instance, constructing or fetching it on first use and
caching the result for later calls. Reachable from application code either as
a process-wide singleton or as an object handed down through an ambient
context.

**Service.** The interface or abstract type the application code programs
against. In a healthy design this is the same interface a well-formed
constructor-injected dependency would have, the anti-pattern here is not in
the interface, it is in how the caller obtains an implementation of it.

**Concrete service implementation.** The class registered against the service
key, resolved lazily on first lookup or eagerly at startup, depending on the
locator's own policy.

**Registry entry, initializer.** Whatever mechanism populates the locator
with mappings before any caller can successfully resolve anything, a static
initializer block, a bootstrap function run at process start, a
configuration file parsed at startup, or, in the JNDI-era original, the
container's own deployment descriptor.

**Client.** Any class that calls the locator, by name or by type, instead of
declaring the dependency as a constructor or method parameter. Every client is
now coupled to the locator's own API and lifecycle, which is the structural
fact dimension 3 and dimension 10 both return to.

## 6. ASCII structure diagram

```
+----------------------+
|        Client         |
|  (a component that     |
|   needs a Logger,       |
|   a Repository, etc.)  |
+-----------+-----------+
            |
            | calls  Locator.get(Repository.class)
            v
+----------------------+          registered against
|    Service Locator    |<-------------------------------+
|  Map<Key, Instance>   |                                 |
|  + get(key): Instance |                                 |
|  + register(key, impl)|                                 |
+-----------+-----------+                                 |
            |                                              |
            | returns a cached or freshly built instance    |
            v                                              |
+----------------------+     +----------------------+      |
|  ConcreteRepositoryA   |     |  ConcreteRepositoryB  |------+
|  implements Repository |     |  implements Repository|
+----------------------+     +----------------------+

Contrast with Dependency Injection, no lookup step exists at the call site.

+----------------------+          +----------------------+
|      Assembler /       | wires    |        Client          |
|   Composition Root     |--------->|  constructor(Repository)|
|  new Client(new RepoA())|          |  (no lookup, no locator)|
+----------------------+          +----------------------+
```

The structural difference the diagram is meant to make visible is this. In
Service Locator the arrow of control at the call site points FROM the client
TO the locator, an explicit pull. In Dependency Injection the arrow points
FROM an external assembler INTO the client, a push the client never
initiates and, in the healthy case, never even imports the assembler to know
it exists.

## 7. Dynamics

```
Startup / bootstrap phase
--------------------------
main() or container bootstrap
   |
   |--> Locator.register(Logger.class, new FileLogger())
   |--> Locator.register(Repository.class, new SqlRepository(dataSource))
   |--> Locator.register(PaymentGateway.class, new StripeGateway(apiKey))
   v
Locator is now populated. Application enters its normal request-handling
lifecycle.

Per-request / per-call phase
-----------------------------
OrderController.placeOrder(request)
   |
   |--> repo = ServiceLocator.get(Repository.class)      // hidden dependency #1
   |--> gateway = ServiceLocator.get(PaymentGateway.class) // hidden dependency #2
   |--> order = repo.save(request.toOrder())
   |--> gateway.charge(order.total())
   v
Returns response.

Failure dynamics, the point that most catalogs skip
------------------------------------------------------
Test harness constructs OrderController() with no arguments (compiles fine,
signature reveals nothing)
   |
   |--> test calls controller.placeOrder(request)
   |--> controller calls ServiceLocator.get(PaymentGateway.class)
   |--> locator was never populated for this test process
   v
Runtime exception, "No registration for PaymentGateway", thrown from deep
inside placeOrder, at a line the test author did not know existed, instead of
a compile error at the point the test constructs the object.
```

The dynamics make the central cost concrete. Dependency Injection pushes a
missing-dependency failure to compile time, or at worst to a single,
predictable point, container startup. Service Locator defers the same failure
to whichever call site happens to exercise the missing registration first,
which in a large codebase is frequently a production request path that no
test ever reached.

## 8. Implementation variants

**Type-keyed locator, the common modern shape.** `get<T>(Class<T>)` or its
generic-language equivalent, returning an instance registered against the
requested type. Slightly safer than string-keyed lookup because a typo in a
class reference is caught by the compiler, but the presence or absence of a
registration for that type is still a runtime fact.

**String-keyed locator, the original JNDI shape.** `get(String name)`,
matching the original JNDI `lookup("java:comp/env/jdbc/OrderDB")` idiom.
Weakest variant, a misspelled key is invisible until the call executes.

**Ambient-context locator.** The locator is not passed to the client
explicitly, it is reached through a static accessor,
`ServiceLocator.current()`, or an implicit thread-local. This is the variant
most often paired with, and easily confused with, plain Singleton abuse, see
dimension 13, because the mechanism for reaching the locator is itself a
global.

**Container-as-locator, the disguised variant.** A dependency-injection
container is present and correctly builds most of the object graph, but some
code paths call the container's own resolution API directly,
`applicationContext.getBean(...)`, `serviceProvider.GetService<T>()`,
`Injector.get(T)`, instead of letting the container inject the dependency
through a constructor. This is functionally identical to Service Locator even
though a real dependency-injection container sits underneath it, because
the client is still pulling rather than being pushed to, and it is the most
common way the anti-pattern reappears in codebases that otherwise believe
they use dependency injection correctly.

**Factory-of-services locator.** The locator returns not the service itself
but a factory or provider for it, deferring construction. This softens the
eager-construction cost but does not soften the hidden-dependency cost, the
call site still pulls rather than declares.

## 9. Known production uses

- **The J2EE platform itself, the pattern's origin.** Documented and named in
  Deepak Alur, John Crupi, Dan Malks, *Core J2EE Patterns. Best Practices and
  Design Strategies*, Prentice Hall, 2001, as a formal catalog entry
  addressing the cost of repeated JNDI `InitialContext` lookups across EJB
  clients. This is the pattern's canonical, historically legitimate
  production use, arising from a platform constraint, the absence of a
  container-managed dependency-injection mechanism, that no longer holds on
  most current platforms.
- **`java.util.ServiceLoader` and the broader Service Provider Interface
  family** in the Java platform, JDBC driver discovery being the most visible
  example, where `ServiceLoader.load(CodecFactory.class)` walks
  `META-INF/services` entries to find registered implementations (Oracle,
  Java SE 17 API documentation, `java.util.ServiceLoader`,
  https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ServiceLoader.html,
  verified 2026-08-02). Listed here explicitly as a named counter-example. the
  Javadoc's own framing, "locates and loads service providers deployed in the
  run time environment", describes a scoped, single-interface discovery
  mechanism, not the general multi-service anti-pattern this entry is about.
  See dimension 1 and dimension 4.
- **ASP.NET Core's `IServiceProvider` when misused directly by application
  code**, rather than through constructor injection. Microsoft's own
  dependency-injection guidelines name this exact usage, calling `GetService`
  or an injected resolving factory a service-locator variation and
  recommending against both under the "Recommendations" section of the
  official guidance (Microsoft, ".NET dependency injection guidelines",
  https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection-guidelines,
  verified 2026-08-02). The framework ships the exact machinery that enables
  the anti-pattern, `IServiceProvider` is a first-class, documented type, and
  the same official document simultaneously documents the composition-root
  pattern as the correct alternative, which is a useful, citable case of a
  platform vendor naming the anti-pattern inside its own reference
  documentation.

## 10. Consequences

**Positive.**

- Removes duplicated, verbose lookup boilerplate for a genuinely
  slow or ceremony-heavy resource-acquisition API, the JNDI case being the
  historically real instance.
- Provides one place to change how a service is obtained or swapped, without
  touching every call site, useful when the alternative was truly hand-rolled
  duplication rather than a proper container.
- Handles genuinely runtime-discovered plugin sets, where the caller cannot
  enumerate implementors at compile time, better than a static constructor
  parameter list ever could.

**Negative.**

- Hides a class's true dependencies from its public API, exactly the
  criticism Mark Seemann leads with, "the problem with Service Locator is
  that it hides a class' dependencies, causing run-time errors instead of
  compile-time errors" (Mark Seemann, "Service Locator is an Anti-Pattern",
  https://blog.ploeh.dk/2010/02/03/ServiceLocatorisanAnti-Pattern/, verified
  2026-08-02).
- Converts a missing-dependency bug from a compile error into a runtime
  exception, frequently discovered far from the code that actually has the
  problem, and often only on a code path a test suite failed to exercise.
- Concentrates coupling into a single locator class that every client now
  depends on, trading many small, visible dependencies for one large, mostly
  invisible one, per Fowler's own framing in dimension 3.
- Makes unit testing materially harder, because isolating a class under test
  now requires configuring shared, often global or static, locator state
  instead of passing a constructor argument, and that shared state is a
  recurring source of test-order-dependent flakiness.
- Actively resists refactoring toward proper dependency injection later,
  because the very thing that would make the true dependency graph visible,
  reading constructor signatures, is exactly what the pattern removes.

## 11. Failure modes and misuse

**Symptom.** A `NoSuchElementException`, `NullPointerException`, or an
equivalent no-registration-found-for-type-X runtime error appears in
production, on a request path that the automated test suite passes cleanly.
**Cause.** The locator was registered with every service needed by the tested
code paths, but a newer code path added a lookup for a service nobody
remembered to register in every environment the code runs in, staging, a
background worker process, a new deployment target. Because the dependency
was never declared anywhere a compiler or a static analyzer could check it,
nothing caught the gap before runtime. **Fix.** Migrate the offending call
site to constructor injection so the missing registration becomes a container
startup failure instead of a request-time failure, and if full migration is
not immediately possible, add an explicit startup-time self-check that resolves
every type the locator is expected to serve and fails fast at boot rather than
at first use.

**Symptom.** Unit tests pass individually but fail intermittently when run as
a full suite, or fail only in a particular run order. **Cause.** Multiple
tests mutate the same process-wide locator state, registering test doubles
under the same keys, and a test that runs after another test without
resetting the locator inherits stale or wrong registrations. **Fix.** Either
reset the locator's full registration map in a setup hook before every test,
which papers over the symptom without removing the design flaw, or, the
durable fix, replace the locator dependency in the class under test with a
constructor parameter so each test can pass an isolated instance with no
shared global state at all.

**Symptom.** A code reviewer cannot answer the question of what a class
depends on by reading its constructor, and has to grep the entire method body,
and sometimes the bodies of private helper methods it calls, to find every
`Locator.get(...)` call before understanding what the class needs to run.
**Cause.** The pattern has, by design, moved the dependency declaration from
the signature into the implementation. **Fix.** Treat this specific
reviewer friction as the signal to migrate, not as a documentation gap to
patch with a comment. A comment describing hidden dependencies is a symptom
that a constructor parameter should exist instead.

**Symptom.** A God locator accumulates hundreds of registrations across
unrelated subsystems, logging, persistence, payments, notifications, and a
change to how one subsystem is wired forces a rebuild or redeploy that
touches the shared locator class, even though the change has nothing to do
with the other subsystems it now sits beside. **Cause.** The locator started
as a small convenience for two or three lookups and grew, uncontrolled,
because adding a new registration to an existing global object is always the
path of least resistance compared to threading a new constructor parameter
through several layers of the call graph. **Fix.** Split the locator along
the same seams a proper dependency-injection module system would use, or,
better, replace it with that module system. Most current containers support
scoped or named registration sets precisely so a God locator never has to
exist.

## 12. Trade-off matrix

| Force | Service Locator | Constructor Dependency Injection | Abstract Factory (injected) | Direct singleton import |
|---|---|---|---|---|
| Dependency visible in the class's own signature | No, hidden inside method bodies | Yes, listed as constructor parameters | Yes, the factory itself is a declared parameter | No, hidden inside a static import |
| Missing dependency detected | At runtime, at the call site | At compile time, or at container startup | At compile time for the factory, at runtime for what it produces | Never, the import always resolves. A missing configured target fails inside the singleton |
| Ease of unit testing | Hard, requires configuring shared or global state | Easy, pass a test double as an argument | Easy, pass a fake factory | Hard, requires swapping the singleton's internal state |
| Handles runtime-discovered plugin sets | Yes, its strongest legitimate case | No, requires the full set known at wiring time | Partially, the factory can branch on runtime data | No |
| Coupling shape | Many-to-one, every client couples to the locator | None beyond the declared interfaces | Client couples to the factory interface only | Every client couples to the concrete singleton type |
| Startup cost visibility | Hidden until first lookup fails | Explicit, container reports missing bindings at startup | Explicit for the factory wiring itself | None, no startup wiring step exists |

## 13. Related and incompatible patterns

**Dependency Injection.** The direct alternative and, per Fowler, the pattern
Service Locator is most often contrasted against. Where Service Locator has
the client pull a dependency from a shared object, Dependency Injection has an
external assembler push the dependency to the client, and the two are
philosophically close enough, the shared question of how a component gets its
collaborators without constructing them, that most architecture discussions
treat them as a single decision axis rather than as unrelated patterns.

**Singleton, and its abuse form, see the sibling entry
`singleton-abuse.md`.** A locator is almost always itself reached as a
process-wide singleton, so any critique of Singleton's testability and
global-state costs applies doubly to a locator built on top of one. The two
patterns compound each other's downsides rather than canceling them.

**Factory Method and Abstract Factory.** A factory that a client is genuinely
handed as a declared constructor parameter is not a service locator, because
the dependency on a thing that can produce X is visible in the signature. The
same factory reached through a static, ambient accessor collapses back into
the Service Locator shape. The structural difference is entirely about how
the factory itself arrives at the client, not about what the factory does
once it is there.

**Facade.** A Facade simplifies a complex subsystem's interface behind a
single entry point, and a locator superficially resembles a facade over
generic lookup. The distinction is intent and scope. A Facade wraps a
bounded, coherent subsystem and its dependency is declared like any other. A
locator wraps an unbounded, growing set of unrelated services and is reached
ambiently, not declared.

**Inversion of Control containers, general.** Any real IoC container,
Spring's `ApplicationContext`, .NET's built-in container, Dagger, Guice,
already solves the problem Service Locator originally solved, and calling the
container's own resolution method directly from inside a component it manages
is the container-as-locator variant from dimension 8, functionally the
anti-pattern wearing the container's clothing.

## 14. Refactoring path in and out

Refactoring a locator-based class into constructor injection, step by step.

1. Read every `Locator.get(...)` or equivalent call inside the class,
   including private helper methods, and list the distinct types requested.
   This list is the class's true, previously hidden, dependency set.
2. Add each type as a constructor parameter, store it in a field with the same
   name the local variable already had, so the diff at call sites stays
   minimal.
3. Replace every `Locator.get(X.class)` call inside the class body with a
   read of the corresponding field.
4. Update every place that constructs this class, most often the assembler,
   container configuration, or another factory, to supply the newly required
   constructor arguments. If the container already manages the class, this
   step is frequently free, because the container resolves constructor
   parameters automatically once they are declared.
5. Delete the locator import from the class. Its absence from the import list
   is now a compiler-verifiable proof that the migration is complete for this
   class.
6. Repeat per class, starting with the classes nearest the edges of the call
   graph, controllers and entry points, and working inward, so that each step
   shrinks the set of classes still reaching for the locator rather than
   requiring one large, coordinated rewrite.

Introducing a locator into code that does not have one is rare, and only
belongs in the narrow legitimate cases from dimension 4.

1. Confirm the case is genuinely one of the three legitimate applicability
   cases, most commonly a runtime-discovered plugin set, before proceeding.
   This step exists specifically to stop the refactor from being applied by
   habit.
2. Prefer a platform-native service-provider mechanism,
   `java.util.ServiceLoader`, .NET's `MEF`, or an equivalent, over a
   hand-rolled registry, because the platform mechanism already solves the
   registration-population problem correctly.
3. If a hand-rolled locator is unavoidable, scope it as narrowly as possible,
   to the exact plugin interface, never as a general-purpose multi-service
   registry, and isolate every call to it inside the single seam where the
   framework hands control to your code, never inside ordinary business
   logic several layers deep.

## 15. Testing and verification

Testing a class that reaches into a service locator requires either
configuring the shared locator state before the test runs, which couples the
test to global process state and risks order-dependent flakiness across the
whole suite, or wrapping the locator itself behind an interface the test can
substitute, which pushes the class most of the way back toward ordinary
dependency injection without actually declaring the dependency in the
constructor.

The practical technique for a test that must exercise legacy locator-based
code without a full migration is to reset the locator's registrations in a
setup hook immediately before each test and to register only the specific
test doubles that test needs, tearing the registrations back down in a
teardown hook so no state survives into the next test. This is defensive
scaffolding around a design flaw, not a fix for it, and it is measurably more
setup ceremony than a constructor-injected equivalent, where passing the mock
as an argument is the entire cost.

A useful automated verification signal, once a codebase has decided to move
away from the pattern, is a static grep-based check in CI that fails a build
introducing a new call to the locator's `get` method outside an explicitly
allow-listed set of legacy files, which prevents the anti-pattern from
spreading into new code even while an incremental migration of existing code
is still in progress.

## 16. Observability signals

A healthy dependency-injection-based system reports its wiring problems once,
at startup. the container either builds successfully or fails with a clear
message naming the exact missing binding. A locator-based system has no
equivalent single moment, and instead its wiring problems surface as
scattered runtime exceptions across whatever request paths happen to
exercise an unregistered lookup, so the useful observability signal is the
absence of one. No single wiring-complete log line exists to alert on, and
this absence is itself a diagnostic sign worth treating as a code smell
during an architecture review.

Where a locator is deliberately kept, log every successful and failed
resolution with the requested key and the calling class, so that a
production incident caused by a missing registration can at minimum be traced
to the exact lookup that failed rather than only to the downstream
`NullPointerException` it produced several stack frames later. A rising count
of unresolved-lookup log entries in a metrics dashboard is the signal that
the locator's registration set has drifted out of sync with what the running
code actually asks for, most often after a deployment that added a new call
site without updating every environment's bootstrap configuration.

## 17. Security and privacy implications

This is largely engineering judgement rather than a sourced concern, offered
because the pattern's structure does create one narrow, real surface. A
string-keyed locator that resolves a service name coming from anywhere
outside a fixed, compiled-in set, a configuration file an operator can edit,
a request parameter, an environment variable read at runtime, opens a
lookup-injection surface, where an attacker who can influence the key can
cause the locator to resolve and invoke an unintended registered service.
This mirrors the general class of insecure deserialization and
reflection-based instantiation risks, and the mitigation follows the same
principle, never resolve a locator key that traces back to untrusted input,
and prefer type-keyed lookup, which at minimum constrains resolution to
already-compiled types, over string-keyed lookup, which does not. Beyond
this narrow case, the pattern has no privacy implications distinct from
whatever the services it locates themselves handle, and it neither
strengthens nor weakens data-handling guarantees on its own.

## 18. References

1. Deepak Alur, John Crupi, Dan Malks, *Core J2EE Patterns. Best Practices and
   Design Strategies*, Prentice Hall, 1st edition, 2001. Catalog origin of the
   Service Locator pattern within the J2EE pattern language.
2. Martin Fowler, "Inversion of Control Containers and the Dependency
   Injection pattern", section "Using a Service Locator",
   https://martinfowler.com/articles/injection.html, verified 2026-08-02.
3. Wikipedia, "Service locator pattern",
   https://en.wikipedia.org/wiki/Service_locator_pattern, verified
   2026-08-02.
4. Mark Seemann, "Service Locator is an Anti-Pattern",
   https://blog.ploeh.dk/2010/02/03/ServiceLocatorisanAnti-Pattern/, dated 03
   February 2010, verified 2026-08-02.
5. Microsoft, ".NET dependency injection guidelines", section
   "Recommendations",
   https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection-guidelines,
   verified 2026-08-02.
6. Oracle, Java SE 17 API documentation, `java.util.ServiceLoader`,
   https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ServiceLoader.html,
   verified 2026-08-02.

## Code examples

The anti-pattern first, then the constructor-injection alternative it is
compared against, in each of three languages. All three samples were run
against a real toolchain during authoring.

### TypeScript, compiled with tsc, executed with node

```typescript
// Anti-pattern: a type-keyed global service locator.
class ServiceLocator {
  private static registry = new Map<Function, unknown>();

  static register<T>(key: new (...args: never[]) => T, instance: T): void {
    ServiceLocator.registry.set(key, instance);
  }

  static get<T>(key: new (...args: never[]) => T): T {
    const found = ServiceLocator.registry.get(key);
    if (!found) {
      throw new Error(`No registration for ${key.name}`);
    }
    return found as T;
  }
}

interface PaymentGateway {
  charge(cents: number): string;
}

class StripeGateway implements PaymentGateway {
  charge(cents: number): string {
    return `charged ${cents} cents via stripe`;
  }
}

// OrderController's constructor reveals nothing about what it needs.
// The real dependency is discovered only by reading placeOrder's body.
class OrderController {
  placeOrder(totalCents: number): string {
    const gateway = ServiceLocator.get(StripeGateway);
    return gateway.charge(totalCents);
  }
}

// Constructor-injection alternative: the dependency is visible, testable,
// and fails to compile if the caller forgets to supply it.
class OrderControllerInjected {
  constructor(private readonly gateway: PaymentGateway) {}

  placeOrder(totalCents: number): string {
    return this.gateway.charge(totalCents);
  }
}

ServiceLocator.register(StripeGateway, new StripeGateway());
console.log(new OrderController().placeOrder(1500));
console.log(new OrderControllerInjected(new StripeGateway()).placeOrder(1500));
```

### Python, executed with python3

```python
# Anti-pattern: a global registry reached by type.
class ServiceLocator:
    _registry: dict[type, object] = {}

    @classmethod
    def register(cls, key: type, instance: object) -> None:
        cls._registry[key] = instance

    @classmethod
    def get(cls, key: type):
        try:
            return cls._registry[key]
        except KeyError:
            raise LookupError(f"No registration for {key.__name__}") from None


class PaymentGateway:
    def charge(self, cents: int) -> str:
        raise NotImplementedError


class StripeGateway(PaymentGateway):
    def charge(self, cents: int) -> str:
        return f"charged {cents} cents via stripe"


class OrderController:
    """__init__ takes nothing; the real dependency is buried in place_order."""

    def place_order(self, total_cents: int) -> str:
        gateway = ServiceLocator.get(StripeGateway)
        return gateway.charge(total_cents)


class OrderControllerInjected:
    """The dependency is a constructor parameter, visible and swappable."""

    def __init__(self, gateway: PaymentGateway) -> None:
        self.gateway = gateway

    def place_order(self, total_cents: int) -> str:
        return self.gateway.charge(total_cents)


if __name__ == "__main__":
    ServiceLocator.register(StripeGateway, StripeGateway())
    print(OrderController().place_order(1500))
    print(OrderControllerInjected(StripeGateway()).place_order(1500))
```

### Rust, compiled and executed with rustc

Rust has no reflection-based type-keyed lookup in its standard library, so a
service locator here is necessarily string-keyed and trait-object based,
which sharpens the anti-pattern's weakest variant from dimension 8.

```rust
use std::collections::HashMap;

trait PaymentGateway {
    fn charge(&self, cents: u64) -> String;
}

struct StripeGateway;

impl PaymentGateway for StripeGateway {
    fn charge(&self, cents: u64) -> String {
        format!("charged {} cents via stripe", cents)
    }
}

// Anti-pattern: a string-keyed registry of boxed trait objects.
struct ServiceLocator {
    registry: HashMap<&'static str, Box<dyn PaymentGateway>>,
}

impl ServiceLocator {
    fn new() -> Self {
        ServiceLocator { registry: HashMap::new() }
    }

    fn register(&mut self, key: &'static str, service: Box<dyn PaymentGateway>) {
        self.registry.insert(key, service);
    }

    fn get(&self, key: &str) -> &dyn PaymentGateway {
        self.registry
            .get(key)
            .unwrap_or_else(|| panic!("no registration for {key}"))
            .as_ref()
    }
}

// place_order's signature reveals nothing about the payment dependency.
fn place_order(locator: &ServiceLocator, total_cents: u64) -> String {
    let gateway = locator.get("payment_gateway");
    gateway.charge(total_cents)
}

// Constructor-injection alternative: the dependency is an explicit parameter.
fn place_order_injected(gateway: &dyn PaymentGateway, total_cents: u64) -> String {
    gateway.charge(total_cents)
}

fn main() {
    let mut locator = ServiceLocator::new();
    locator.register("payment_gateway", Box::new(StripeGateway));
    println!("{}", place_order(&locator, 1500));

    let gateway = StripeGateway;
    println!("{}", place_order_injected(&gateway, 1500));
}
```

All three samples were compiled and run during authoring, `npx tsc` against
the TypeScript sample followed by `node` on the emitted JavaScript, `python3`
directly against the Python sample, and `rustc` followed by direct execution
of the resulting binary for the Rust sample. Each produced the expected
"charged 1500 cents via stripe" output twice, once from the locator-based
call path and once from the constructor-injected call path, demonstrating
that both shapes are behaviourally identical at the leaf and differ only in
how the dependency arrives at the call site, which is the entire point this
entry makes.
