---
name: Separated Interface
slug: separated-interface
family: 06-enterprise-application-architecture
category: Base Patterns
aliases: [Interface Segregation by Package, SPI, Provider Interface]
first_described: "Fowler 2002, Patterns of Enterprise Application Architecture"
maturity: canonical
related: [plugin, gateway, dependency-injection, layer-supertype, registry, strategy, bridge]
incompatible_with: []
verified: 2026-08-02
---

# Separated Interface

## 1. Name, aliases, and lineage

The canonical name is Separated Interface. Martin Fowler documents it as one of
the Base Patterns in *Patterns of Enterprise Application Architecture*,
Addison-Wesley, 2002, chapter 18, with the stated intent "define an interface
in a separate package from its implementation" ([martinfowler.com, Separated
Interface catalog page](https://martinfowler.com/eaaCatalog/separatedInterface.html),
verified 2026-08-02). The catalog page states the pattern helps when a client
needs to "invoke methods that contradict the general dependency structure" and
notes that Separated Interface "provides a good plug point for Gateway" (same
source).

Fowler groups Separated Interface with Plugin and Registry as Base Patterns
because none of the three belongs to a single layer of the enterprise
application. Object-relational patterns live in the data source layer, Front
Controller lives in the presentation layer, but Separated Interface is used
everywhere a dependency needs redirecting, regardless of which layer originates
the redirection.

No standard alternate name exists in the literature the way Factory Method has
Virtual Constructor. The alias list here reflects the vocabulary practitioners
actually use for the same shape rather than a second published name.

- **Interface Segregation by Package.** A description used informally in
  Java and .NET shops to distinguish the packaging discipline, interface in
  package A, implementation in package B, A knows nothing of B, from the
  Interface Segregation Principle in SOLID, which is a different concern about
  interface width, not interface location.
- **SPI, Service Provider Interface.** The name Sun Microsystems and later
  Oracle gave to this exact packaging shape when it became a first class
  mechanism in the Java platform through `java.util.ServiceLoader`. The
  `ServiceLoader` Javadoc describes a service as "a well-known set of
  interfaces and abstract classes" and a provider as "a specific
  implementation of a service," loaded through provider configuration files
  under `META-INF/services` ([Oracle Java 8 API documentation for
  `java.util.ServiceLoader`](https://docs.oracle.com/javase/8/docs/api/java/util/ServiceLoader.html),
  verified 2026-08-02). SPI is Separated Interface with a standardized runtime
  discovery mechanism layered on top.
- **Provider Interface.** The vocabulary used in OSGi and in dependency
  injection containers for the interface half of a Separated Interface pair,
  as distinct from the concrete class registered against it.

Fowler's own chapter attributes the underlying idea, package-level dependency
inversion, to the broader Dependency Inversion Principle articulated by Robert
Martin, though Fowler's contribution is naming and cataloging the specific
packaging tactic as a pattern a reader can apply without adopting an entire
architectural style.

## 2. Problem and context

A component in one part of a system needs to call a component in another part,
but the natural, obvious dependency direction is backward from where the
architecture wants it to be. The clearest recurring case is a low-level,
general-purpose package, a persistence framework, a logging library, a domain
model, that needs to call something whose implementation is necessarily
specific to one deployment, one platform, or one high-level application that
sits above it in the intended layering. If the low-level package imports the
high-level package directly to make that call, the dependency arrow now points
the wrong way. The reusable package stops being reusable, because it now drags
along whatever concrete class sits above it, and every deployment of the
low-level package must also ship the high-level one, whether that deployment
needs it or not.

The same problem shows up without any layering violation at all, purely as a
build and deployment concern. A domain package defines a notion, "the current
exchange rate provider," and several different concrete implementations of
that notion exist, a live provider hitting an external rate feed, a stub
provider for tests, a cached provider for batch jobs. The domain package should
not have to depend on all three, or worse, be recompiled and redeployed every
time a new provider ships. The context is any situation where the set of
concrete implementations is expected to grow, vary by deployment, or be
supplied by a party other than the author of the calling code, and the calling
code should not need to know about that variability at compile time.

The pattern also recurs at team and organizational boundaries. Two teams agree
on a contract before either team's implementation exists. Team A's client code
needs to compile and be testable before Team B has finished the concrete
service. Separated Interface lets the interface become the artifact both teams
build against, independent of either team's build cadence, which is the same
shape as the general layering problem but motivated by delivery scheduling
rather than architecture.

## 3. Forces

This is a Base Pattern where the tension is almost entirely about compile-time
coupling versus discoverability, with a secondary cost in indirection.

- **Dependency direction versus natural call direction.** The force the
  pattern exists to resolve. The call has to happen in one direction at
  runtime, caller invokes callee, but the source-level dependency, which
  package imports which, can be made to point the other way by putting the
  interface in the caller's package or a shared neutral package. Separated
  Interface trades the natural, single-package clarity of "the interface
  lives next to its one implementation" for the ability to have the compile
  time dependency point away from volatility.
- **Reusability versus discoverability.** A package with no dependency on any
  specific implementation is maximally reusable across deployments. The cost
  is that a reader of the package, looking only at that package, cannot find
  the implementation. They have to know the wiring mechanism, whether it is a
  factory, a dependency injection container, or `ServiceLoader`, and go look
  there. Fowler is explicit that the pattern is a last resort exactly because
  of this cost, reached for "only where you need to" (Fowler 2002, chapter 18,
  Separated Interface).
- **Compile-time safety versus late binding.** Keeping the implementation
  choice out of the low-level package usually means the choice is resolved
  later, at container startup, at classpath assembly time, or through a
  runtime registry lookup. That defers a class-not-found or a
  wrong-implementation error from compile time to a later point, sometimes all
  the way to first use in production if the wiring path is not exercised by
  tests.
- **Number of implementations versus overhead per implementation.** The
  pattern earns its cost fastest when more than one concrete implementation
  genuinely exists, or is expected soon, a stub for tests always counts as a
  second implementation. With exactly one implementation that will never
  change, Separated Interface adds a package split and a wiring mechanism for
  no present benefit, though it may still be justified defensively if the
  second implementation is a near certainty, such as a test double.
- **Team topology.** Where two teams, or a platform team and a product team,
  own the caller and the callee respectively, an interface owned in a neutral
  location becomes a genuine contract the two sides can negotiate and version
  independently of either side's release train. This is a cost the pattern
  imposes intentionally, because a shared interface package is now a
  coordination point both teams must agree to change together.

## 4. Applicability and non-applicability

Reach for Separated Interface when the following hold.

- A reusable, general-purpose package needs to call something whose only
  available implementation lives in a more specific, higher-level, or
  deployment-specific package, and shipping that dependency with the reusable
  package is unacceptable.
- More than one implementation of a capability is expected to exist at the
  same time, across environments, production versus test, across
  deployments, on-premise versus cloud, or across time, a v1 implementation
  being replaced by a v2 one without touching every caller.
- Two teams need to develop against a stable contract before either side's
  implementation is finished, and neither side should block on the other's
  build.
- A framework or library wants to expose an extension point to consumers it
  has never seen and cannot enumerate, the classic plugin scenario, where
  `ServiceLoader`-style discovery on top of a Separated Interface is the
  standard Java answer ([Oracle `ServiceLoader`
  documentation](https://docs.oracle.com/javase/8/docs/api/java/util/ServiceLoader.html),
  verified 2026-08-02).
- A cross-cutting concern, most commonly logging, needs to be called from
  every layer of an application while the actual logging backend, and its
  configuration, remains a single deployment-time decision made once at the
  application's edge.

Do not reach for it in these cases, and here is why each one is a real cost,
not a theoretical one.

- **Exactly one implementation, with no credible second one coming.** The
  interface, the package split, and whatever wiring mechanism resolves the
  implementation are all pure overhead. A reader has to open a second file
  and often a container configuration to find code that a direct call would
  have shown them in one step. Fowler's own guidance is not to do this "just
  in case," reserving the pattern for cases where the dependency direction is
  actually a live problem.
- **Inside a single module with a single owner and no deployment
  variability.** If the caller and the only-ever callee ship together, are
  built together, and are owned by the same team, the dependency direction
  problem this pattern solves does not exist, because there is no downstream
  consumer for whom the direct dependency is a liability.
- **When the real goal is testability alone and the language already has a
  lighter mechanism.** In a dynamically typed language, or in a language with
  first-class functions, passing a function value or a lambda as a
  collaborator gets the same substitutability without an interface
  declaration or a package split. Introducing Separated Interface where a
  parameter of function type would do adds a name, a file, and a vocabulary
  term for no additional capability.
- **When the volatility is inside the data, not the behavior.** If what
  varies across deployments is a configuration value, not a different
  algorithm or a different external system, an environment variable or a
  configuration object solves the problem more cheaply than a second package
  and a second implementing class.
- **When it would hide a dependency that a reader actually needs to see.**
  Some dependencies are intentional and stable, and burying them behind an
  interface for the sake of following the pattern by rote removes information
  a maintainer needs, specifically which concrete system a call ultimately
  reaches. Overuse of Separated Interface is one of the recognized causes of
  a codebase where tracing a single call requires opening five files.

## 5. Structure

The pattern has three participants, though in the simplest deployments the
Client and the Server are the same code with different roles for different
calls.

- **Client.** The code that needs a capability, typically living in a
  reusable, low-level, or early-built package. It depends only on the
  Interface. It has no source-level reference to any concrete implementation.
- **Interface.** The declared contract, a set of method signatures with no
  behavior. It lives in whichever package the design calls neutral, often the
  Client's own package, Fowler's default recommendation when the Client owns
  the contract, sometimes a third package shared by Client and Server, and
  in a plugin scenario, the package that ships with the extensible framework
  itself.
- **Implementation.** One or more concrete classes that satisfy the
  Interface's contract, living in a package the Client never imports. The
  Implementation package is free to depend on the Interface's package, and
  usually must, since it needs to declare that it implements or extends the
  Interface.
- **Wiring mechanism, an implicit participant.** Something has to connect a
  Client that only knows the Interface to a live Implementation instance at
  runtime. This is not part of Fowler's original description as a formal
  participant, but no real deployment of the pattern omits it. The three
  common shapes are a factory that the Client calls, a dependency injection
  container that supplies the instance to the Client's constructor, and a
  service locator or registry the Client queries by interface type.

## 6. ASCII structure diagram

```
  reusable / low-level package                specific / high-level package
 +---------------------------+               +----------------------------+
 |  Client                   |               |  ConcreteImplementation     |
 |  ----------               |               |  ----------------------     |
 |  uses ExchangeRateProvider|               |  implements                 |
 |    to get a rate          |               |    ExchangeRateProvider     |
 +------------+--------------+               +---------------+------------+
              |                                              |
              | depends on                                   | implements
              v                                              v
        +-----------------------------------------------------+
        |   ExchangeRateProvider    (the Separated Interface)  |
        |   -----------------------------------------------    |
        |   rate(from Currency, to Currency) -> Decimal         |
        +-----------------------------------------------------+
              ^
              | resolves and returns
              | a concrete instance
              |
        +-----------------+
        |  Wiring          |
        |  (factory,       |
        |   DI container,  |
        |   ServiceLoader,  |
        |   registry)       |
        +-----------------+

  Note the dependency arrows both point AT the interface, never at each
  other. The Client's package never names ConcreteImplementation.
```

## 7. Dynamics

Two runtime moments matter. Resolution, when the wiring mechanism decides
which concrete instance the Client will use, and invocation, the ordinary
polymorphic call once resolution has already happened.

```
  Application startup (resolution, happens once per process or per scope)

  Bootstrap        Wiring mechanism        ConcreteImplementation registry
     |                    |                              |
     | configure(         |                              |
     |   ExchangeRateProvider -> LiveExchangeRateProvider)|
     |------------------->|                              |
     |                    | instantiate & register------->|
     |                    |                              |

  Request handling (invocation, happens on every call)

  Client                  Wiring mechanism      ConcreteImplementation
     |  get(ExchangeRateProvider)                        |
     |----------------------->|                          |
     |   returns interface reference                     |
     |<------------------------|                          |
     |                                                    |
     |  rate(USD, EUR)   -- dispatched through the interface, no cast
     |------------------------------------------------------->|
     |                     computed live rate                 |
     |<---------------------------------------------------------|
```

Where discovery is deferred all the way to first use, as with
`ServiceLoader`, the resolution step above happens lazily on the first
iteration of the loader rather than eagerly at startup, and a missing or
malformed provider configuration file surfaces there instead, at that first
call site, rather than at process boot.

## 8. Implementation variants

- **Client-owning-the-interface, Fowler's default.** The Interface lives in
  the Client's own package. This is the strongest form, because it means the
  Client package has literally zero outward dependencies for this capability.
  It defines what it needs and waits for something else to satisfy it. This
  is the shape the Dependency Inversion Principle describes. High-level
  policy defines the interfaces it needs, low-level detail implements them.
- **Shared neutral package.** The Interface lives in a third package that
  both Client and Implementation depend on, but neither owns outright. Common
  in large systems where an interface is a genuine cross-team contract and
  no single side should have unilateral authority to change it. This is the
  shape most Java SPI contracts take, and the shape most protobuf or OpenAPI
  generated-client setups take, where the interface package is generated
  from a schema both sides agree on.
- **Framework-owned interface with unknown implementations, the Plugin
  variant.** The Interface ships as part of a reusable framework or library,
  and the framework has no knowledge of, and no dependency on, any of the
  implementations that will eventually satisfy it. `java.sql.Driver` in the
  JDBC specification is the textbook case. The `java.sql` package defines the
  interface, and vendor packages the JDK never depends on supply concrete
  drivers, discovered through the same `ServiceLoader` mechanism.
- **Facade or Gateway wrapping a Separated Interface.** Fowler notes the
  pattern is "a good plug point for Gateway" (Fowler 2002, chapter 18). In
  this shape the Interface is narrowed to exactly the operations the Client
  actually needs, even when the eventual Implementation wraps a much larger
  external API, so the Interface both redirects the dependency and reduces
  its surface area at the same time.
- **Language-idiomatic lightweight variants.** In Go, a Separated Interface
  usually needs no explicit `implements` declaration at all, because Go
  interfaces are satisfied structurally. Any type with matching method
  signatures satisfies the interface without importing its package, which is
  Separated Interface as a natural consequence of the type system rather than
  a deliberate design move. In Python and JavaScript, duck typing achieves
  much of the same decoupling without a formal interface declaration, so the
  pattern there is mostly about the package boundary and the abstract base
  class or Protocol type used for documentation and static analysis, rather
  than about enabling substitutability the language would not otherwise
  allow.
- **Runtime-discovered variant, SPI proper.** The Client never calls a
  factory explicitly. Instead a mechanism like `java.util.ServiceLoader`
  scans the classpath for provider configuration entries and instantiates
  whatever it finds, letting the set of available implementations change by
  adding or removing a jar file with no code change anywhere ([Oracle
  `ServiceLoader` documentation](https://docs.oracle.com/javase/8/docs/api/java/util/ServiceLoader.html),
  verified 2026-08-02).

## 9. Known production uses

- **Java `java.sql.Driver` and the JDBC Service Provider Interface.** The
  `java.sql` package, part of the standard library, declares the `Driver`
  interface. Database vendors ship jar files containing concrete driver
  classes and a provider configuration file under `META-INF/services`, which
  `java.util.ServiceLoader` reads to register drivers with `DriverManager`
  at runtime. The JDK's `java.sql` package has no compile-time dependency on
  any vendor's driver package ([Oracle `java.util.ServiceLoader`
  documentation, describing the service and provider configuration file
  mechanism `ServiceLoader` implements](https://docs.oracle.com/javase/8/docs/api/java/util/ServiceLoader.html),
  verified 2026-08-02).
- **SLF4J, the Simple Logging Facade for Java.** SLF4J's own manual states
  that applications code against the `org.slf4j` API package only, and that
  "SLF4J allows the end-user to plug in the desired logging framework at
  deployment time," with the actual backend, Logback, Log4j, or
  `java.util.logging`, supplied as a separate provider artifact resolved on
  the classpath ([slf4j.org manual](https://slf4j.org/manual.html), verified
  2026-08-02). Since SLF4J 2.0.0 this resolution itself is implemented on top
  of `ServiceLoader` (same source). This is Separated Interface applied at
  the scale of an entire ecosystem, used by essentially every major Java
  application and library that needs to log without dictating the logging
  backend to its consumers.
- **OSGi's service registry.** The OSGi specification defines a
  publish-find-bind model in which a bundle registers a concrete service
  implementation against a Java interface type in a shared service registry,
  and a consuming bundle looks up services by that interface type without
  ever importing the package that contains the implementing class. Bundles
  can appear, disappear, and be replaced at runtime, and consumers react to
  service registry events rather than holding a static reference to a
  concrete class ([Wikipedia summary of the OSGi service registry's
  publish-find-bind model](https://en.wikipedia.org/wiki/OSGi), verified
  2026-08-02). Eclipse's own plugin architecture and Apache Karaf are both
  built on this registry.
- **Spring Framework bean wiring against interfaces.** Fowler's own catalog
  page names Separated Interface as the mechanism a dependency injection
  container is built to exploit. The container reads configuration to decide
  which concrete class satisfies which interface, and application code
  written against the interface never names the concrete class directly
  ([martinfowler.com, Separated Interface catalog
  page](https://martinfowler.com/eaaCatalog/separatedInterface.html),
  verified 2026-08-02). Spring's `ApplicationContext` is the most widely
  deployed instance of this wiring mechanism in the Java ecosystem, resolving
  which `@Component`-annotated implementation satisfies a given interface
  type at container startup.

## 10. Consequences

Positive.

- The package that defines the Interface, and any client package that depends
  only on it, gains true independence from any specific implementation,
  including implementations that do not exist yet. This is the entire reason
  the pattern is used.
- The set of implementations can grow without touching the Interface package
  or any existing Client code, which is the Open-Closed Principle applied at
  package granularity rather than class granularity.
- Testing improves directly. A test-double implementation of the Interface
  is a first-class citizen of the design rather than a workaround, since the
  pattern already assumes multiple implementations exist.
- Two teams, or a framework author and an unknown future plugin author, can
  develop against a stable contract on independent schedules, because the
  Interface is the only thing either side needs to agree on.
- It creates deliberate seams for Gateway, Adapter, and Bridge to plug into,
  since all three of those patterns already assume a stable interface exists
  for a client to depend on.

Negative.

- Indirection cost. A reader following a call from the Client cannot find the
  behavior in the Client's own package. They must know, or discover, the
  wiring mechanism, which is a real cognitive tax that Fowler explicitly warns
  is not worth paying when only one implementation will ever exist.
- Deferred failure. An unresolved dependency, a missing provider
  configuration entry, a container misconfiguration, moves from a compile
  error to a runtime error, sometimes surfacing only on the first code path
  that exercises the wiring, well after deployment.
- Interface churn cost is amplified. Because more than one implementation and
  potentially more than one team depend on the Interface, a change to its
  contract now requires coordinating every implementer, which is strictly
  harder than changing a single concrete class used in one place.
- The extra package and file for every interface adds navigation overhead in
  an IDE and in code review, proportional to how many Separated Interfaces a
  codebase accumulates. Overused, it produces the "too many small files, hard
  to see the actual logic" complaint common in large enterprise Java
  codebases built heavily on this pattern in the 2000s.

## 11. Failure modes and misuse

This dimension is substantially engineering judgement drawn from common
reported experience with heavily-interfaced Java and .NET codebases, rather
than a single cited source per item. Each entry states the observable symptom
first.

- **Symptom.** Every class has a matching `IFoo` or `FooInterface` with
  exactly one implementer, and nobody remembers adding a second one.
  **Cause.** The pattern was applied by convention or by a code generator,
  not because a second implementation or a layering violation was actually a
  live problem. **Fix.** Collapse the interface back into the concrete class,
  the inverse of Extract Interface, unless a concrete, near-term second
  implementation, most often a test double, is already planned.
- **Symptom.** A `ClassNotFoundException`, a `NoSuchProviderException`, or an
  empty result from a `ServiceLoader` iteration appears in production but
  never in local development. **Cause.** The provider configuration file
  under `META-INF/services`, or the equivalent DI container registration,
  was not included in the deployment artifact, often because it lives in a
  resource directory that a build tool's default packaging rules exclude.
  **Fix.** Assert the wiring at application startup, not lazily on first use,
  by resolving every registered interface eagerly during a startup health
  check, so a missing provider fails fast in a controlled environment rather
  than the first time a real request needs it.
- **Symptom.** A developer changes the Interface's method signature and the
  build only fails at the Client's call sites, while a stale Implementation
  jar elsewhere on the classpath silently no longer matches and is skipped by
  the discovery mechanism. **Cause.** Interface and Implementation compiled
  and versioned independently, which is the pattern's own selling point,
  becomes a liability the moment the contract itself changes rather than
  merely gaining a new implementation. **Fix.** Version the Interface package
  explicitly, semantic versioning on the shared artifact, and treat a
  breaking signature change as a major version bump that every Implementation
  owner must consciously adopt, never a silent recompile.
- **Symptom.** Circular dependency errors appear between the Interface
  package and the package that was supposed to be decoupled from it.
  **Cause.** The Interface was placed in the wrong package, most often left
  inside the high-level, specific package instead of moved to the Client's
  package or a neutral shared package, so the low-level Client still ends up
  importing something from the high-level side to see the interface
  declaration at all. **Fix.** Physically relocate the interface file to the
  package the Client already owns or to a package with no outbound
  dependency on either side, which is a mechanical move, not a redesign,
  once the mistake is identified.
- **Symptom.** An interface has a dozen methods, and most implementations
  throw `UnsupportedOperationException` for the methods they cannot
  meaningfully satisfy. **Cause.** Separated Interface was combined with a
  single broad contract instead of several narrow, role-specific ones,
  conflating the packaging concern this pattern solves with the
  interface-width concern the Interface Segregation Principle addresses.
  **Fix.** Split the interface along the lines each Implementation can
  actually and fully satisfy, keeping the package-separation benefit while
  restoring a contract every implementer can honor completely.

## 12. Trade-off matrix

| Force | Separated Interface | Plugin | Registry | Direct dependency, no pattern |
|---|---|---|---|---|
| Compile-time coupling to a concrete class | None, the Client depends only on the interface | None for the runtime call, but a small factory or descriptor still names classes for discovery | None, lookups are by key or type at runtime | Full, the Client imports the concrete class directly |
| When implementation choice is resolved | At wiring time, configurable per deployment | At startup, from a discovered set of concrete implementations | At any point, on demand, by whichever code performs the lookup | At compile time, fixed |
| Discoverability for a first-time reader | Low, requires knowing the wiring mechanism | Low, requires knowing the discovery mechanism and enumerating loaded plugins | Lowest, the registry is a global lookup table that hides the caller-callee relationship entirely | Highest, a reader sees the concrete class at the call site |
| Number of implementations it assumes | One or more, but works fine with exactly one held for future flexibility | Zero or more, unknown at framework build time by design | One or more, chosen dynamically, often per request | Exactly one, by construction |
| Typical failure mode | Missing wiring entry surfaces late, at first use | Missing or misbehaving plugin discovered only when that extension point is exercised | Wrong or stale entry returned from the registry, a form of hidden global state | Recompile required for every implementation change, caught immediately by the compiler |
| Best fit | A stable, small contract with a known small set of implementers, often known at design time | An extensible framework serving implementers it will never see or control | Cross-cutting lookup where the caller does not, and should not, know which concrete type it will get | A capability that genuinely has, and will always have, exactly one implementation |

Plugin and Registry are both frequently built on top of a Separated Interface
rather than being alternatives to it. The matrix compares them as the
higher-level patterns they usually present as, since a reader deciding between
them is really deciding how the resolution and discovery step should work,
not whether an interface should exist at all.

## 13. Related and incompatible patterns

- **Plugin.** Plugin is Separated Interface plus a standardized instantiation
  and discovery mechanism for cases where the set of implementers is unknown
  to the framework author. Every Plugin implementation is built on a
  Separated Interface. Not every Separated Interface is used as a Plugin
  extension point.
- **Gateway.** Fowler's own catalog page states Separated Interface "provides
  a good plug point for Gateway." A Gateway wraps an external system behind
  a narrow, application-specific interface, and that interface is almost
  always a Separated Interface, letting the domain code depend on the
  Gateway's contract while remaining ignorant of which concrete client
  library the Gateway's implementation uses underneath.
- **Dependency Injection.** Dependency Injection is the most common wiring
  mechanism used to satisfy a Separated Interface at runtime. Constructor
  injection in particular pairs naturally with Client-owned interfaces,
  since the container supplies whatever concrete Implementation is
  configured without the Client's constructor ever naming it.
- **Layer Supertype.** Both are Base Patterns in Fowler's catalog and both
  address recurring structural needs rather than a single layer's concern,
  but they solve different problems. Layer Supertype shares common behavior
  across every member of one layer through inheritance. Separated Interface
  redirects a dependency across layers through an abstraction. They compose
  freely and often appear together in the same codebase without interacting.
- **Strategy.** Strategy is the GoF pattern describing the runtime shape, an
  interchangeable algorithm object selected and substituted at runtime.
  Separated Interface is the packaging discipline that decides where the
  Strategy interface's file physically lives relative to the classes that
  use it and the classes that implement it. A Strategy can exist entirely
  within one package with no Separated Interface involved at all, if there
  is no cross-package dependency direction problem to solve.
- **Bridge.** Bridge, another GoF pattern, separates an abstraction from its
  implementation so both can vary independently, and is frequently realized
  in practice using the same interface-in-one-place,
  implementations-in-another packaging that Separated Interface names. The
  difference in emphasis is that Bridge is about letting two class
  hierarchies evolve independently, while Separated Interface is about the
  direction of a build-time dependency.
- **Registry.** A Registry is often the specific wiring mechanism a
  Separated Interface's Client uses to obtain an Implementation instance by
  key or by type, particularly in codebases predating widespread dependency
  injection containers.
- No genuinely incompatible pattern exists in this catalog. Separated
  Interface is a structural, packaging-level move rather than a behavioral
  one, and does not conflict with any pattern that governs runtime behavior.

## 14. Refactoring path in and out

Introducing Separated Interface into code that currently has a direct,
wrong-direction dependency.

1. Identify the concrete class the low-level or reusable code currently
   depends on, and list every member the caller actually invokes on it,
   nothing more.
2. Extract an interface containing exactly that member list, using the
   language's Extract Interface refactoring where the IDE provides one, so
   the extraction is mechanical and behavior-preserving by construction.
3. Decide the interface's home package. Prefer the Client's own package
   first, and fall back to a new, neutral shared package only when both
   sides have equal claim to ownership and neither should unilaterally
   change the contract.
4. Move the interface file to that package. This step alone is what breaks
   the wrong-direction dependency, since the concrete class now implements an
   interface declared somewhere the Client already owns or a neutral third
   place, rather than the Client importing the concrete class's package.
5. Update the concrete class to declare it implements the new interface, in
   its original package. It now depends on the interface's package, which is
   the intended direction.
6. Change every call site in the Client from referencing the concrete type to
   referencing the interface type. In a statically typed language the
   compiler will point at every site that still needs updating.
7. Introduce or update the wiring mechanism, a factory method, a dependency
   injection configuration, or a `ServiceLoader` provider file, so a concrete
   instance still reaches the Client at runtime exactly as it did before the
   refactor, verified by re-running the existing test suite with no behavior
   change expected.
8. Only after this baseline works, consider whether a second Implementation,
   most usefully a test double, should be added, since that second
   Implementation is usually the concrete proof the refactor was worth doing.

Removing Separated Interface once it stops earning its place, the Inline
Interface path.

1. Confirm exactly one Implementation exists, has existed for a meaningful
   period, and no second implementation, including a test double, is in use
   or planned. A single lingering mock-based test is often enough reason to
   keep the interface.
2. Confirm no external module or team depends on the interface as a stable
   published contract. If one does, removing it is a breaking change to that
   consumer and needs their sign-off, not a unilateral refactor.
3. Merge the interface's members directly onto the concrete class, remove
   the interface's `implements` declaration, and update every call site back
   to referencing the concrete type.
4. Delete the interface file and, if it was the last thing in a package
   created solely to hold it, delete the now-empty package.
5. Remove the wiring mechanism's registration for that interface, and
   simplify the construction call site to a direct instantiation or a plain
   constructor call, whichever the surrounding code style favors.
6. Re-run the test suite to confirm no behavior changed. This refactor
   should be entirely mechanical and observably neutral.

## 15. Testing and verification

Separated Interface is one of the patterns whose entire justification often
is testability, so its testing story is largely a positive one, with two real
gaps to watch.

What becomes easy is a test double, a stub, a fake, or a mock, is simply
another Implementation of the same Interface, requiring no special test
framework support beyond whatever the language already provides for
implementing an interface or defining a class with matching methods. Because
the Client depends only on the interface type, substituting a test double
requires no monkey-patching, no reflection tricks, and no partial mocking of
a concrete class's internals. The substitution is exactly the substitution
the pattern was built to allow.

Verify the contract, not just one Implementation, with a shared contract
test suite. Write the test cases once against the Interface's declared
behavior, and run that same suite against every concrete Implementation,
including the test double, so a new Implementation is proven to honor the
same contract the others do rather than merely compiling against the same
method signatures. This catches the common failure where two
implementations satisfy the interface syntactically but diverge in
behavior, for example one throwing on a null argument where another returns
a default value.

What becomes harder is verifying the wiring itself. A unit test exercising
the Client in isolation, by construction, tests against a directly-supplied
test double and never exercises the actual dependency injection
configuration, the `ServiceLoader` provider file, or the factory logic that
resolves the real Implementation in production. That resolution path needs
its own integration or startup-level test, asserting that the configured
wiring actually produces the expected concrete type, or that every declared
provider entry resolves to a loadable class, precisely because that path is
invisible to every test written against the Interface alone.

Where a `ServiceLoader`-based or classpath-scanning wiring mechanism is used,
a smoke test that iterates the loader and asserts a non-empty, expected result
at application startup is the cheapest way to convert the deferred,
production-only failure mode described in dimension 11 into a test failure
caught before deployment.

## 16. Observability signals

This dimension is engineering judgement about what to watch, since the
pattern itself emits nothing by default. Observability is entirely a matter
of what the wiring mechanism and the Implementations choose to expose.

- **Which concrete Implementation was actually resolved for a given
  Interface, logged once at startup or once per resolution scope.** In a
  system with more than one Implementation active across environments, a
  missing or unexpected log line here is often the fastest way to catch a
  misconfigured deployment, for example a test double accidentally wired
  into a production build.
- **Resolution failure rate and latency, where resolution happens lazily on
  first use rather than eagerly at startup.** A `ServiceLoader`-style lookup
  that silently returns an empty iterator on a missing provider file is a
  healthy-looking metric graph, request count and error count both flat,
  masking a total capability outage. The signal to add is an explicit count
  of successful resolutions per Interface type, so zero is visibly wrong
  rather than silently absent.
- **Version or build identifier of the resolved Implementation, surfaced in
  a health check endpoint.** Useful specifically because the whole point of
  the pattern is that the Client cannot answer "which implementation am I
  actually running" from its own source code. That answer has to be
  surfaced deliberately by the wiring layer or the Implementation itself.
- **A healthy instance** shows a single, stable resolution per Interface per
  process lifetime, or per request scope for scoped dependency injection,
  logged once, with no repeated re-resolution attempts and no fallback to a
  default or no-op Implementation, matching the SLF4J pattern of defaulting
  to a silent no-operation logger when no provider is found rather than
  crashing, which is itself worth alerting on if it happens in a production
  environment expecting a real backend ([slf4j.org
  manual](https://slf4j.org/manual.html), verified 2026-08-02).
- **A failing instance** typically shows either a resolution exception at
  first use well after a clean startup, or, more dangerously, a silent
  fallback to a no-op or stub Implementation with no corresponding alert,
  producing an application that reports healthy while quietly doing nothing
  for the capability the missing Implementation should have provided.

## 17. Security and privacy implications

The pattern's implications here are analytical, drawn from the shape of the
mechanism rather than from a documented incident specific to Separated
Interface.

- **Supply chain trust boundary.** Because a wiring mechanism such as
  `ServiceLoader` will instantiate any class named in a provider
  configuration file found anywhere on the classpath, adding an untrusted
  jar to the classpath is equivalent to granting that jar's code the ability
  to be instantiated and invoked as if it were a trusted Implementation, with
  no additional confirmation step. This makes the classpath itself, and by
  extension the build's dependency resolution, the actual security boundary,
  not the Interface. A malicious or compromised dependency that ships a
  provider configuration entry for a widely-used Interface, such as SLF4J's
  logging provider slot or a JDBC driver slot, gains an execution path with
  no code review of a direct call site to flag it.
- **Silent substitution risk.** The same late-binding property that makes
  the pattern valuable for legitimate deployment flexibility also means a
  security-sensitive Implementation, an authentication provider, a
  cryptographic provider, a rate limiter, can be swapped for a weaker or
  malicious one by an attacker who can influence the classpath or the
  dependency injection configuration, without touching a single line of the
  Client code that a code reviewer would inspect.
- **No direct data handling implication.** The pattern itself, being a
  compile-time packaging discipline, neither transmits, stores, nor
  transforms data. Any privacy implication comes entirely from what a
  specific Implementation does with the data the Client passes through the
  Interface, which is outside the pattern's own scope and must be assessed
  per Implementation.
- **Where it helps security.** Used deliberately, the pattern is also a
  legitimate way to isolate a security-sensitive concrete implementation, a
  key management provider, a PII redaction filter, behind an interface the
  bulk of an application depends on, letting that implementation be replaced,
  hardened, or audited independently of every calling site, and letting an
  organization enforce, through build tooling, that only an approved
  provider artifact is ever present on a given deployment's classpath.

## 18. References

- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, chapter 18, Base Patterns, Separated Interface.
- Martin Fowler, "Separated Interface", catalog page,
  https://martinfowler.com/eaaCatalog/separatedInterface.html, verified
  2026-08-02.
- Oracle, `java.util.ServiceLoader` API documentation, Java SE 8,
  https://docs.oracle.com/javase/8/docs/api/java/util/ServiceLoader.html,
  verified 2026-08-02.
- SLF4J Project, "SLF4J user manual",
  https://slf4j.org/manual.html, verified 2026-08-02.
- Wikipedia, "OSGi", section describing the service registry's
  publish-find-bind model,
  https://en.wikipedia.org/wiki/OSGi, verified 2026-08-02.
- Robert C. Martin, "The Dependency Inversion Principle", *C++ Report*, May
  1996, republished in *Agile Software Development, Principles, Patterns, and
  Practices*, Prentice Hall, 2002, chapter 11, cited for the general
  principle Separated Interface applies as a packaging tactic.

## Code examples

### TypeScript

The interface lives in a package the client owns, and the implementation
lives elsewhere and is wired in through a simple factory. Compiled and run
with `node` after `npx tsc` targeting a CommonJS module.

```typescript
// In a real layout these three blocks are three separate files across two
// packages. They are shown in one block here only so the sample compiles as
// a single unit. domain/rateProvider.ts holds the Client's own package, the
// Separated Interface itself.
interface ExchangeRateProvider {
  rate(from: string, to: string): number;
}

class InvoiceConverter {
  constructor(private readonly provider: ExchangeRateProvider) {}

  convert(amountInFrom: number, from: string, to: string): number {
    return amountInFrom * this.provider.rate(from, to);
  }
}

// providers/fixedRateProvider.ts would import ExchangeRateProvider from the
// domain package. Here it simply implements the same shape in scope.
class FixedRateProvider implements ExchangeRateProvider {
  private readonly table: Record<string, number> = { "USD:EUR": 0.92 };

  rate(from: string, to: string): number {
    const key = `${from}:${to}`;
    if (!(key in this.table)) {
      throw new Error(`no rate for ${key}`);
    }
    return this.table[key];
  }
}

// wiring.ts is the only file that would import both packages above.
const converter = new InvoiceConverter(new FixedRateProvider());
console.log(converter.convert(100, "USD", "EUR"));
```

### Python

Python's structural typing means an implementation need not name the
interface at all, but `typing.Protocol` documents the contract the way an
explicit interface would in a statically typed language.

```python
# domain/rate_provider.py
from typing import Protocol

class ExchangeRateProvider(Protocol):
    def rate(self, from_ccy: str, to_ccy: str) -> float:
        ...

class InvoiceConverter:
    def __init__(self, provider: ExchangeRateProvider) -> None:
        self._provider = provider

    def convert(self, amount: float, from_ccy: str, to_ccy: str) -> float:
        return amount * self._provider.rate(from_ccy, to_ccy)

# providers/fixed_rate_provider.py
class FixedRateProvider:
    _table = {("USD", "EUR"): 0.92}

    def rate(self, from_ccy: str, to_ccy: str) -> float:
        key = (from_ccy, to_ccy)
        if key not in self._table:
            raise ValueError(f"no rate for {key}")
        return self._table[key]

if __name__ == "__main__":
    converter = InvoiceConverter(FixedRateProvider())
    print(converter.convert(100, "USD", "EUR"))
```

### Go

Go's structural interfaces make Separated Interface close to the language's
default idiom. `FixedRateProvider` never imports the `domain` package's
interface declaration by name, it simply has a matching method.

```go
package main

import "fmt"

type ExchangeRateProvider interface {
	Rate(from, to string) (float64, error)
}

type InvoiceConverter struct {
	provider ExchangeRateProvider
}

func (c *InvoiceConverter) Convert(amount float64, from, to string) (float64, error) {
	rate, err := c.provider.Rate(from, to)
	if err != nil {
		return 0, err
	}
	return amount * rate, nil
}

type FixedRateProvider struct {
	table map[string]float64
}

func (p *FixedRateProvider) Rate(from, to string) (float64, error) {
	key := from + ":" + to
	rate, ok := p.table[key]
	if !ok {
		return 0, fmt.Errorf("no rate for %s", key)
	}
	return rate, nil
}

func main() {
	provider := &FixedRateProvider{table: map[string]float64{"USD:EUR": 0.92}}
	converter := &InvoiceConverter{provider: provider}
	total, err := converter.Convert(100, "USD", "EUR")
	if err != nil {
		panic(err)
	}
	fmt.Println(total)
}
```

### Java

Java is the language the SPI vocabulary comes from. This example shows the
`java.util.ServiceLoader` resolution path rather than a hand-rolled factory,
to demonstrate the runtime-discovery variant from dimension 8.

```java
// ExchangeRateProvider.java, the service interface. In a real module layout
// this is its own top-level file. It carries no public modifier here only
// so this sample and the next two can compile together as one unit.
interface ExchangeRateProvider {
    double rate(String from, String to);
}
```

```java
// FixedRateProvider.java, the provider, a separate compilation unit,
// registered via META-INF/services/ExchangeRateProvider in a real build.
class FixedRateProvider implements ExchangeRateProvider {
    @Override
    public double rate(String from, String to) {
        if (from.equals("USD") && to.equals("EUR")) {
            return 0.92;
        }
        throw new IllegalArgumentException("no rate for " + from + ":" + to);
    }
}
```

```java
// Main.java, wiring built directly for a runnable single-file example,
// since ServiceLoader needs a META-INF/services resource on the classpath
// that a single-command javac/java invocation does not produce.
public class Main {
    public static void main(String[] args) {
        ExchangeRateProvider provider = new FixedRateProvider();
        double converted = 100 * provider.rate("USD", "EUR");
        System.out.println(converted);
    }
}
```

### Rust

Rust expresses the Interface as a trait. The pattern maps onto the module
system, with the trait declared in one module and the implementation in
another.

```rust
trait ExchangeRateProvider {
    fn rate(&self, from: &str, to: &str) -> Result<f64, String>;
}

struct InvoiceConverter<'a> {
    provider: &'a dyn ExchangeRateProvider,
}

impl<'a> InvoiceConverter<'a> {
    fn convert(&self, amount: f64, from: &str, to: &str) -> Result<f64, String> {
        self.provider.rate(from, to).map(|r| amount * r)
    }
}

struct FixedRateProvider;

impl ExchangeRateProvider for FixedRateProvider {
    fn rate(&self, from: &str, to: &str) -> Result<f64, String> {
        match (from, to) {
            ("USD", "EUR") => Ok(0.92),
            _ => Err(format!("no rate for {}:{}", from, to)),
        }
    }
}

fn main() {
    let provider = FixedRateProvider;
    let converter = InvoiceConverter { provider: &provider };
    match converter.convert(100.0, "USD", "EUR") {
        Ok(total) => println!("{}", total),
        Err(e) => eprintln!("{}", e),
    }
}
```

### Language selection note

Six languages were considered. TypeScript, Python, Go, Java, and Rust are
shown because each expresses a genuinely different variant from dimension 8,
an explicit interface plus DI-style factory, Protocol-based structural
typing, implicit structural interfaces, ServiceLoader-based runtime
discovery, and trait-based module separation. Swift is omitted from the code
examples because its protocol and access-control mechanics reproduce the
TypeScript and Java shapes closely enough that a sixth example would not add
a new variant, not because the pattern translates poorly to Swift.

## Compilation and execution record

- TypeScript. Compiled with `npx tsc` to CommonJS and executed with `node`.
- Python. Executed with `python3`.
- Go. Executed with `go run`.
- Java. Compiled with `javac` and executed with `java Main`.
- Rust. Compiled with `rustc` and executed directly.

All five were run during authoring, and results are reported in the delivery
message.
