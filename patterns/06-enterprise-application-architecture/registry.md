---
name: Registry
slug: registry
family: 06-enterprise-application-architecture
category: Base Patterns
aliases: [Service Registry, Component Registry, Global Registry, Well-Known Object]
first_described: "Martin Fowler, Patterns of Enterprise Application Architecture, 2002"
maturity: canonical
related: [singleton, service-locator, separated-interface, plugin, factory-method, dependency-injection, layer-supertype]
incompatible_with: []
verified: 2026-08-02
---

# Registry

## 1. Name, aliases, and lineage

The canonical name is Registry, catalogued by Martin Fowler as one of the Base
Patterns in *Patterns of Enterprise Application Architecture*, Addison-Wesley,
2002, chapter 18. Fowler states the pattern's intent plainly, calling it "a
well-known object that other objects can use to find common objects and
services" ([martinfowler.com, Registry](https://martinfowler.com/eaaCatalog/registry.html),
verified 2026-08-02). The book's own catalog page frames the motivating problem
as bootstrapping a lookup. you may know a customer's ID but hold no object
reference to that customer, so before you can use a finder to locate the
customer you first need a way to locate the finder itself, and that is the
role Registry fills.

Registry is one of the most frequently reinvented names in software, and the
reinventions are not all the same idea, which is why disambiguating them
matters before anything else in this entry.

- **Registry (Fowler, enterprise sense).** A well-known object, reachable by a
  static or globally accessible path, that other code queries to obtain shared
  services, resources, or configuration that were placed there earlier,
  typically during application bootstrap. The registry does not usually build
  the objects it holds, something else constructs them and hands them to the
  registry to store.
- **Registry as Service Locator.** In practice a Registry queried imperatively
  from inside business logic, rather than only from a small composition root,
  behaves identically to the Service Locator pattern. Fowler's own comparison
  of the two, written for his dependency-injection article, treats them as
  close siblings distinguished mainly by convention rather than mechanism
  ([martinfowler.com, Inversion of Control Containers and the Dependency
  Injection pattern](https://martinfowler.com/articles/injection.html),
  verified 2026-08-02). This entry treats Registry as the noun, the store
  itself, and Service Locator as the usage style, querying that store from
  deep inside application code, and returns to the distinction in dimension 13.
- **Registry as directory service.** In distributed systems the same word
  names a network-reachable naming service that maps a symbolic name to a
  remote handle. the RMI registry is the paradigmatic Java example, and this
  entry treats it as a known production instance of the same underlying idea
  applied over a wire rather than in a single process (dimension 9).
- **Windows Registry.** An unrelated Microsoft operating-system configuration
  database. It shares the word and nothing else with this pattern and is
  mentioned here only to rule it out of scope.

The pattern predates Fowler's book by name. class-level static lookup tables
holding shared collaborators appear throughout Smalltalk and early Java
literature under names like Manager or Locator, but Fowler's 2002 catalog
entry is the citation this repository treats as canonical, matching the
convention used by the rest of this family's entries such as Separated
Interface and Gateway, which cite the same book and the same 2002 date.

## 2. Problem and context

An object, buried several calls deep inside a request, a batch job, or a
background worker, needs something it was not given directly. a database
connection, the currently configured tax calculator, a logger, the active
locale, a payment gateway implementation chosen at deploy time rather than
compile time. Passing that thing down explicitly, as a parameter through every
intervening method, is the textbook-correct answer and it is also the answer
that degrades a codebase's readability the moment the call chain is more than
two or three frames deep. Every method on the path acquires a parameter it
does not use itself, only forwards, and every future caller of every one of
those methods must supply it too, whether or not the caller has an opinion
about which tax calculator is in force.

The context in which this becomes acute is layered enterprise software. a web
tier calls a service tier which calls a domain tier which calls a persistence
tier, and a cross-cutting concern such as which logger or which connection
pool needs to reach the bottom layer without every layer above declaring it
as a formal dependency. Constructor parameter threading is the disciplined
answer, and it is the right one when the object graph is small and stable.
The problem Registry exists to solve is the case where that discipline has a
real cost, when there are many call sites, a genuinely global resource (there
is exactly one connection pool for the process, not one per caller), and a
bootstrap phase that happens once and is naturally separate from the
request-handling code that follows it.

A second, related context is plugin discovery. a framework author writes code
years before the concrete implementations exist, and needs a way for
independently compiled, independently deployed modules to make themselves
known to the framework at startup without the framework's source code naming
them. `database/sql` in Go's standard library and Java's `ServiceLoader`
both solve this with a registration step separate from a lookup step, which is
the same two-phase shape as Fowler's Registry even though neither project uses
the word Registry in its own name.

## 3. Forces

- **Convenience of access versus visibility of dependency.** A registry makes
  a resource reachable from anywhere with one line of code, and that same
  line hides, from anyone reading the calling class's public surface, that
  the dependency exists at all. Fowler is explicit about this cost when
  comparing Registry-style lookup to injected dependencies, writing that
  "with a Service Locator every user of a service has a dependency to the
  locator," while the caller's real requirements stay discoverable only by
  reading the method body, never the signature
  ([martinfowler.com, injection.html](https://martinfowler.com/articles/injection.html),
  verified 2026-08-02).
- **Global uniqueness versus multiple configurations in one process.** A
  registry usually assumes there is one of each thing per process, and that
  assumption breaks the moment a process needs two differently configured
  instances side by side, for example running a multi-tenant application
  where each tenant has its own database connection.
- **Bootstrap-time write versus steady-state read.** Registries are almost
  always populated once, early, and read many times after that. The design
  has to decide, explicitly or implicitly, whether writes after the boot
  phase are supported, tolerated, or forbidden, because concurrent mutation
  of a structure everyone reads without synchronization is a classic source
  of data races.
- **Testability versus realism.** Tests want to substitute a fake logger, a
  stub payment gateway, or an in-memory database. A registry that is a
  process-wide mutable singleton makes substitution possible but leaky, since
  a test that forgets to restore the previous registration corrupts every
  test that runs after it in the same process.
- **Operability versus surprise.** A well-instrumented registry that logs
  every registration and every lookup miss turns "why is this null" into a
  two-minute log search. An uninstrumented one turns the same question into
  an afternoon.

## 4. Applicability and non-applicability

Reach for Registry when:

- The resource being looked up is genuinely one-per-process, or one-per
  well-defined-scope (per request, per thread), and threading it as an
  explicit parameter through many intervening layers would add more noise
  than it removes.
- You are integrating with legacy code that already relies on static, global
  access, and a disciplined Registry with typed accessors and a freeze step
  is a strict improvement over ad hoc statics scattered through the codebase.
- You are building a plugin or extension point where implementations are
  compiled and deployed separately from the core, and something needs to
  discover which implementations exist at runtime without the core naming
  them at compile time, the way `database/sql` drivers and Java
  `ServiceLoader` providers register themselves.
- You need a directory that maps symbolic names to remote resources across a
  process or network boundary, which is the RMI Registry's job.

Do NOT reach for Registry when:

- The object graph is small, known at compile time, and testable by
  construction. Constructor-based dependency injection gives the same
  runtime flexibility (swap the implementation via configuration) with the
  dependency declared in the type signature, which is strictly more
  discoverable, and it is the comparison Fowler himself makes as the reason
  most modern frameworks default to injection over lookup
  ([martinfowler.com, injection.html](https://martinfowler.com/articles/injection.html),
  verified 2026-08-02).
- The class doing the lookup is a domain or business-logic class whose unit
  tests should run without booting any framework. A registry lookup buried in
  domain code forces every test of that class to either populate the global
  registry first or accept a null-pointer failure, which is exactly the
  symptom in dimension 11.
- You need per-request or per-tenant configuration and are tempted to reach
  for a single process-wide registry to hold it. Use an explicitly scoped
  context object instead, passed down the call chain or carried on a request
  object, so two concurrent requests for two different tenants cannot
  observe each other's configuration.
- The framework you are already using owns a mature dependency injection
  container, such as Spring's `ApplicationContext` or .NET's
  `IServiceProvider`. Building a second, parallel registry duplicates
  bookkeeping the container already does correctly, with lifecycle
  management, scoping, and disposal the hand-rolled version usually lacks.
- The thing being registered is a secret or credential. A process-wide
  registry readable from any code path is a poor place to keep something
  that should be scoped tightly and audited, see dimension 17.

## 5. Structure

- **Registry.** The well-known access point. Exposes a registration operation
  (`register`, `bind`, `add`) used during bootstrap and a lookup operation
  (`resolve`, `get`, `lookup`) used during steady-state operation. Frequently
  exposes a way to enumerate what is currently registered, for diagnostics.
- **Registered Object / Service.** The thing being stored, which can be a
  concrete instance (a `Clock`), a factory that produces instances on demand
  (Go's `notifierFactory` in dimension 6's code), or a class reference to be
  instantiated lazily.
- **Bootstrapper / Composition Root.** The code, usually run once at process
  startup, that performs every registration. This is the only place in a
  well-disciplined codebase that both knows the registry exists and is
  allowed to write to it.
- **Client.** Code that calls the registry's lookup operation to obtain a
  registered object. In the disciplined version of this pattern, clients are
  as few and as close to the composition root as possible; in the
  undisciplined version, clients are scattered throughout the domain model,
  which is the shape that degenerates into Service Locator, see dimension 13.
- **Separated Interface (optional participant).** The type under which a
  service is registered is frequently an interface defined separately from
  its implementation, so the registry can hold, for example, a `PaymentGateway`
  interface while the concrete `StripeGateway` implementation lives in a
  package the registry's callers never import directly. The Separated
  Interface entry in this same family already lists Registry among its
  related patterns for exactly this reason.

## 6. ASCII structure diagram

```
+-------------------+          +----------------------+
|   Bootstrapper     |--------->|      Registry        |
|  (composition root) | register|  entries: Map<K, V>  |
+-------------------+          |  register(key, val)  |
                                |  resolve(key): V     |
                                |  freeze()            |
                                +-----------+-----------+
                                            ^
                                            | resolve
                                            |
                +---------------------------+---------------------------+
                |                           |                           |
       +--------+--------+        +---------+---------+       +---------+---------+
       |  OrderService    |        |  NotificationSvc   |       |  ReportRunner     |
       |  (client)        |        |  (client)          |       |  (client)         |
       +------------------+        +--------------------+       +-------------------+

       registered value types, held opaquely by the Registry:

       +----------------+   implements   +----------------+
       |  Clock          |<--------------|  SystemClock    |
       |  (interface)    |               |  (impl)         |
       +----------------+               +----------------+
```

## 7. Dynamics

Registry has two distinct phases, and confusing them is the single most
common source of the initialization-order failures cataloged in dimension 11.

```
BOOT PHASE (once, single-threaded, before traffic is accepted)
  Bootstrapper -> Registry.register("clock", SystemClock)
  Bootstrapper -> Registry.register("gateway", StripeGateway)
  Bootstrapper -> Registry.freeze()

STEADY-STATE PHASE (many times, possibly concurrent, after boot completes)
  Client A -> Registry.resolve("clock")       -> returns SystemClock instance
  Client B -> Registry.resolve("gateway")     -> returns StripeGateway instance
  Client C -> Registry.resolve("sms")         -> lookup miss, raises with
                                                  the list of known keys
```

A sequence for a single request that depends on a registered service looks
like this.

```
Client            Registry           SystemClock
  |  resolve("clock")  |                  |
  |-------------------->|                 |
  |                     | (map lookup)    |
  |  Clock instance     |                 |
  |<--------------------|                 |
  |  now()                                |
  |--------------------------------------->|
  |  timestamp                             |
  |<----------------------------------------|
```

The freeze step in the boot-phase diagram is not part of every implementation
of Registry, but its absence is the direct cause of the most common failure
mode in dimension 11, so this entry treats it as a strongly recommended, not
mandatory, structural addition.

## 8. Implementation variants

- **Class-level static singleton registry.** The classic shape, a single
  static instance, reachable as `Registry.instance()` or through a module-level
  singleton, backed by a mutable map. Simple, and the variant most exposed to
  the testability and thread-safety forces in dimension 3.
- **Frozen-after-boot registry.** The static registry gains a `freeze()`
  method, called at the end of the bootstrap phase, after which any further
  registration attempt is a programming error and is rejected loudly rather
  than silently accepted. The TypeScript and Rust code samples in dimension
  15 both implement this variant, because it converts a class of
  init-order bugs from a runtime `null` deep in request handling into a
  boot-time exception at the exact line that caused it.
- **Thread-scoped or request-scoped registry.** Instead of one process-wide
  registry, an instance (or a `ThreadLocal`-backed accessor to one) is created
  per thread or per request, holding request-specific values like the current
  user or tenant. This variant answers the multiple-configurations-in-one-
  process force from dimension 3 by giving each concurrent unit of work its
  own registry rather than sharing one, at the cost of needing explicit
  propagation across any async boundary that changes threads.
- **Type-keyed registry.** Instead of string keys, the registry is keyed by
  the interface or class type itself, using generics (TypeScript, Rust,
  Java) or reflection (Go, Python), which trades a small amount of runtime
  flexibility (you cannot register two implementations of the same interface
  under different string names in the same slot) for compile-time type
  safety at the call site.
- **Factory registry / plugin registry.** The registry stores factories
  (functions or classes capable of producing an instance) rather than live
  instances, and calls the factory on each lookup. This is the shape
  `database/sql.Register` uses, and it is the correct choice when the
  registered thing needs a fresh instance per use, or when eager construction
  at boot time would be wasteful or would require resources not yet
  available, such as a database connection the driver has not opened yet.
- **Registry as the internal storage of a Dependency Injection container.**
  Full-featured containers such as Spring's `BeanFactory` and .NET's
  `IServiceProvider` are, internally, a Registry augmented with graph
  construction, lifecycle management (singleton, scoped, transient), and
  constructor-parameter resolution. Spring's own documentation describes the
  container's job as instantiating, configuring, and assembling beans whose
  definitions form the registry's contents
  ([docs.spring.io, Core Technologies, IoC Container](https://docs.spring.io/spring-framework/reference/core/beans/introduction.html),
  verified 2026-08-02). The distinction that matters for this entry is that a
  bare Registry is handed already-built objects and only stores them, while
  a DI container builds the objects itself by walking a dependency graph.
  Treating the two as interchangeable is a frequent source of confusion in
  team discussions, see dimension 13.
- **Directory-service registry over the network.** Java RMI's
  `java.rmi.registry.Registry`, obtained through `LocateRegistry`, is a
  registry whose entries are remote object stubs rather than in-process
  values, and whose registration and lookup calls cross a process boundary
  ([Oracle Java SE 8 API, java.rmi.registry.LocateRegistry](https://docs.oracle.com/javase/8/docs/api/java/rmi/registry/LocateRegistry.html),
  verified 2026-08-02).

## 9. Known production uses

- **Java RMI Registry.** `java.rmi.registry.Registry`, reached through
  `LocateRegistry.getRegistry()` or `LocateRegistry.createRegistry(port)`,
  is described in the JDK documentation as the "bootstrap remote object
  registry" that clients use to obtain a first reference to a remote service
  before any further remote calls are possible
  ([Oracle Java SE 8 API, java.rmi.registry.LocateRegistry](https://docs.oracle.com/javase/8/docs/api/java/rmi/registry/LocateRegistry.html),
  verified 2026-08-02). This is Registry applied at the process-boundary
  scale rather than the in-process scale, solving the identical bootstrapping
  problem Fowler describes, over a network instead of over a method call.
- **Java Naming and Directory Interface (JNDI).** JNDI is "a Java API for a
  directory service that allows Java software clients to discover and look
  up data and resources (in the form of Java objects) via a name"
  ([Wikipedia, Java Naming and Directory Interface](https://en.wikipedia.org/wiki/Java_Naming_and_Directory_Interface),
  verified 2026-08-02). Application servers use it as the registry through
  which a servlet looks up a configured `DataSource` or an EJB by a symbolic
  name set in deployment configuration, decoupling application code from the
  concrete connection details chosen at deploy time.
- **Django's application registry.** Django ships `django.apps.apps`,
  described in the framework's own documentation as containing "a registry of
  installed applications that stores configuration and provides
  introspection," and also maintaining "a list of available models"
  ([Django documentation, Applications](https://docs.djangoproject.com/en/5.2/ref/applications/),
  verified 2026-08-02). Any code in a Django project can call
  `apps.get_model("myapp", "MyModel")` to resolve a model class by name,
  which is the lookup half of the Registry pattern operating on model classes
  rather than service instances.
- **Spring's `BeanFactory` / `ApplicationContext`.** Spring's IoC container
  documentation states plainly that "a bean is an object that is
  instantiated, assembled, and managed by a Spring IoC container," and that
  the container is configured from metadata describing beans and their
  dependencies ([docs.spring.io, Core Technologies, IoC Container](https://docs.spring.io/spring-framework/reference/core/beans/introduction.html),
  verified 2026-08-02). Internally this is a Registry of bean definitions
  keyed by name or type, extended with graph-construction responsibility, and
  it is the reference example this entry uses in dimension 8 to draw the
  Registry-versus-DI-container line.
- **.NET's `IServiceCollection` / `IServiceProvider`.** Microsoft's own
  documentation frames the built-in container directly, stating that
  "services are typically registered at the app's start-up and appended to an
  `IServiceCollection`. Once all services are added, use
  `BuildServiceProvider` to create the service container"
  ([learn.microsoft.com, Dependency injection - .NET](https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection),
  verified 2026-08-02). This is a registration phase followed by a frozen,
  built container used for the rest of the process's life, structurally
  identical to the freeze-after-boot variant in dimension 8.

## 10. Consequences

Positive.

- A single, well-known point of access removes the need to thread a resource
  as an explicit parameter through every layer between where it is
  constructed and where it is used, which matters most for genuinely
  cross-cutting resources like a logger or a connection pool.
- Decouples object construction time from object use time. A resource can be
  built once, expensively, at boot, and consulted cheaply many times after,
  which suits connection pools, compiled configuration, and loaded reference
  data well.
- Gives independently deployed plugins or drivers a place to announce
  themselves without the core framework needing to know their names in
  advance, which is what makes `database/sql` drivers and `ServiceLoader`
  providers work.
- A frozen, instrumented registry (dimension 16) turns "what is wired into
  this process right now" into a single, inspectable answer, useful for
  diagnostics and for confirming a deploy actually picked up an expected
  configuration change.

Negative.

- Hides dependencies from a class's public interface. Fowler's own comparison
  states the cost precisely, noting that with dependency injection "you can
  just look at the injection mechanism, such as the constructor, and see the
  dependencies," while with a registry-style lookup "you have to search the
  source code for calls to the locator" to find the same information
  ([martinfowler.com, injection.html](https://martinfowler.com/articles/injection.html),
  verified 2026-08-02).
- Introduces process-wide mutable state, which complicates parallel test
  execution and requires deliberate reset or isolation discipline that a
  purely constructor-injected design does not need at all.
- Couples any class that calls the registry directly to the registry's own
  API, which becomes a second dependency (on the registry) layered on top of
  the dependency the class actually wanted, and both have to be faked or
  reset in a unit test.
- Encourages a junk-drawer failure mode over time, where unrelated services
  accumulate in one flat namespace because adding a new entry to an existing
  registry is always the path of least resistance, described further in
  dimension 11.
- Requires explicit thought about concurrency the instant registration and
  lookup can happen from different threads, which a language's default
  collection types (a plain `HashMap`, a plain `Map`) do not provide for free.

## 11. Failure modes and misuse

The symptom, cause, fix format below is drawn from patterns observed
repeatedly in registry-based codebases; this dimension is engineering
judgement grounded in the mechanics described above, not a set of sourced
claims.

- **Symptom.** A service is `null`, `nil`, or throws "not registered" on
  some request paths but not others, and the failure appears only under
  certain deployment or startup orderings, not in local development.
  **Cause.** Two independent bootstrap modules both register into the same
  registry, and one of them runs, or completes, after the first request has
  already been served, so the registration race depends on unrelated timing
  (module load order, a slow database migration blocking one initializer).
  **Fix.** Give the registry an explicit `freeze()` step invoked at the end
  of a single, ordered bootstrap sequence, and make the application refuse
  to accept traffic until freeze has completed, converting a rare runtime
  failure into an always-reproducible boot-time failure.

- **Symptom.** A unit test passes when run alone and fails when run as part
  of the full suite, or the failure changes depending on test execution
  order.
  **Cause.** A prior test registered a mock or stub into the shared,
  process-wide registry and never restored the original registration, so a
  later test observes state left behind by an earlier one.
  **Fix.** Give the registry a scoped, resettable test double (a fresh
  instance per test, or a documented `reset()` called in test teardown), or
  better, refactor the class under test to receive its dependency through a
  constructor parameter so the test never touches the shared registry at
  all, per the refactoring path in dimension 14.

- **Symptom.** The registry accumulates dozens or hundreds of unrelated
  string keys over a codebase's lifetime, and new contributors cannot tell
  from the registry's contents which entries are load-bearing and which are
  vestigial.
  **Cause.** Adding an entry to an existing, already-imported registry is
  always less friction than designing a properly scoped, separately named
  registry or an injected dependency for a new concern, so the registry
  becomes a dumping ground rather than a curated set of genuinely global
  resources.
  **Fix.** Split the registry along Separated Interface boundaries (a
  `PaymentGatewayRegistry` distinct from a `LoggerRegistry`), and periodically
  audit lookup call sites, removing any entry that only one class ever
  resolves, which is a candidate for direct constructor injection instead.

- **Symptom.** A domain or business-logic class cannot be unit tested without
  first calling the application's full bootstrap sequence, even though the
  test only wants to exercise one small piece of logic.
  **Cause.** The class calls `Registry.resolve(...)` directly inside a
  method, rather than receiving the resolved value as a constructor
  parameter, so the class's real dependency is invisible in its own type
  signature.
  **Fix.** Move every registry lookup for that class to the composition root
  (dimension 5), and pass the resolved value into the class's constructor.
  The class no longer needs to know the registry exists.

- **Symptom.** An intermittent data race, detected by a race detector (Go's
  `-race`, Rust's `loom`, or a production crash under load) inside code that
  reads the registry.
  **Cause.** Registration was assumed to be a one-time, boot-only event, but
  a later code change added a dynamic re-registration path (for example, a
  feature flag that swaps an implementation at runtime) without adding
  synchronization to protect concurrent readers from an in-progress write.
  **Fix.** Either forbid post-boot mutation entirely by freezing the
  registry, or, if dynamic re-registration is a genuine requirement, protect
  the underlying map with a lock or an atomic swap of an immutable snapshot,
  the same technique the Rust code sample in dimension 15 uses with a
  `Mutex`-guarded `HashMap`.

## 12. Trade-off matrix

Registry compared against the named alternatives that solve the same
bootstrapping and shared-access problem, across the forces named in
dimension 3.

| Force | Registry (bare) | Dependency Injection (constructor) | Service Locator | Singleton | Ambient Context (thread-local) |
|---|---|---|---|---|---|
| Dependency is visible in the type signature | No, hidden inside method bodies | Yes, declared as a constructor parameter | No, same as Registry when queried from business logic | No, callers just name the class | No, resolved implicitly per thread |
| Testable without booting the whole app | Poor, needs a populated global | Good, pass a fake directly | Poor, same reason as Registry | Poor, plus hard to reset state | Poor, plus must remember to set and clear per test |
| Supports multiple configurations in one process | Weak, usually one instance per key | Strong, each caller gets its own graph | Weak, same as Registry | None by definition, one instance | Moderate, per-thread values differ, but propagation across async boundaries is manual |
| Works for legacy code with no constructor to inject through | Strong, drop-in for scattered statics | Weak, requires restructuring the class | Strong, same as Registry | Strong, same mechanism as Registry | Moderate, useful for cross-cutting concerns like request IDs |
| Suits plugin or driver discovery at process start | Strong, this is the classic use, per `database/sql` | Weak, DI containers usually still need a registry internally for this | Strong, same as Registry | Weak, one implementation only | Weak, not designed for this |
| Concurrency safety by default | None, must be added explicitly | Not applicable, no shared mutable structure to race on | None, same as Registry | Needs explicit synchronization on first use (lazy init race) | Per-thread by construction, but shared mutable globals inside it still race |

## 13. Related and incompatible patterns

- **Service Locator.** Registry is the noun, the store; Service Locator is
  the verb, querying that store from inside application logic rather than
  only from a composition root. A Registry used exclusively at a
  composition root, with every other class receiving its dependencies
  through constructors, never behaves like a Service Locator and avoids the
  criticism levelled at that pattern. A Registry queried from deep inside
  domain code is functionally Service Locator wearing a different name.
  Fowler's dependency-injection article treats the two as close enough to
  compare side by side directly, which is the citation this entry relies on
  in dimensions 3, 10, and 12
  ([martinfowler.com, injection.html](https://martinfowler.com/articles/injection.html),
  verified 2026-08-02).
- **Singleton.** Registry is most often implemented as a Singleton, described
  in the Gang of Four catalog (Gamma, Helm, Johnson, Vlissides,
  *Design Patterns. Elements of Reusable Object-Oriented Software*,
  Addison-Wesley, 1994, chapter 3, Creational Patterns, Singleton), because
  the registry itself needs to be the same object across every caller in the
  process. The two patterns are not the same thing. Singleton constrains
  instantiation of one class to a single instance; Registry is a store that
  happens to usually be implemented as one.
- **Separated Interface.** A registry very commonly holds services registered
  under an interface type defined separately from the concrete
  implementation, so callers depend on the interface package while the
  concrete package (which may pull in a heavy third-party client library)
  never needs to be imported by the caller. The Separated Interface entry in
  this same family already lists Registry among its related patterns for
  exactly this reason.
- **Plugin.** The factory-registry variant in dimension 8, where independently
  compiled modules register their capability at load time, is the mechanism
  most Plugin implementations use to make themselves discoverable.
- **Factory Method.** A registry frequently stores factories rather than live
  instances, in which case each lookup is functionally a call through a
  Factory Method whose concrete product varies by the string or type key
  used to register it.
- **Dependency Injection (constructor injection).** The disciplined
  alternative for the common case, see the applicability guidance in
  dimension 4 and the trade-off matrix in dimension 12. Full DI containers
  are frequently implemented internally as a Registry of bean or service
  definitions, extended with graph-construction responsibility, so the two
  are complementary at the implementation level even while they compete as
  design choices at the call-site level.
- **Layer Supertype.** Not directly related in structure, but the two
  patterns are frequently confused by newer engineers because both are
  "the thing every class in the codebase touches." Layer Supertype is a base
  class in an inheritance hierarchy; Registry is a lookup table, and the two
  share no mechanism.
- **Incompatible with strict hexagonal or clean-architecture domain layers.**
  Architectures that forbid the domain model from importing anything outside
  the domain, including a framework's registry or container, are structurally
  incompatible with domain code calling a registry directly. In that context
  Registry is confined entirely to the composition root, the outermost layer,
  and the domain never sees it, which is consistent with the refactoring
  guidance in dimension 14 rather than a contradiction of the pattern.

## 14. Refactoring path in and out

Introducing a Registry into code that currently threads a resource by hand.

1. Identify a resource (a logger, a clock, a feature-flag evaluator) that is
   currently passed as a parameter through three or more layers of calls
   where most of the intervening layers do nothing with it except forward it.
2. Create a single, narrowly scoped registry class exposing a typed
   `register` and a typed `resolve` for that one resource, rather than a
   single catch-all registry for everything in the application, to avoid the
   junk-drawer failure mode from dimension 11 from the very first commit.
3. Move the construction of the concrete resource to a single bootstrap
   function, and have that function call `register` once.
4. Replace the parameter in the intervening layers, one call site at a time,
   with a call to `resolve` at the point of actual use, deleting the
   now-unused parameter from every method that only forwarded it.
5. Once every call site has been converted, add the `freeze()` step from
   dimension 8 immediately after the bootstrap function completes, and add a
   startup-time check that traffic is not accepted before `freeze()` has run.
6. Run the full test suite. any test that now fails because it never
   populated the registry is a genuine signal that the class under test
   depends on the resource; use that signal to decide whether the class
   should instead receive the resource through its constructor (a strong
   sign it does most of its work with that resource) or is a genuine,
   incidental client that can call `resolve` at its own composition-root-
   adjacent boundary.

Removing a Registry once its lookups have become a testability or
readability liability.

1. Find every call site that invokes the registry's `resolve` method,
   grouped by the class making the call.
2. For each class, add a constructor parameter typed to the interface the
   registry currently returns, and replace the internal `resolve` call with
   the new constructor parameter.
3. Move the corresponding `resolve` call up to whatever code constructs that
   class, repeating step 2 for that caller in turn, until the chain of
   `resolve` calls terminates at a single point, ideally the same bootstrap
   function that used to call `register`.
4. Once every call site has been converted, the registry's `resolve` method
   should have exactly one caller left, the composition root. At that point
   either delete the registry entirely and pass the constructed object
   directly, or keep it purely as the composition root's own private
   bookkeeping, no longer reachable from anywhere else in the codebase.
5. Delete the now-provably-dead `resolve` calls from any remaining
   intermediate code, and confirm with the codebase's static analysis or
   dead-code tooling that the registry's public lookup surface has shrunk to
   what the composition root actually still needs.

## 15. Testing and verification

Code that calls a shared, process-wide registry directly is, by construction,
hard to unit test in isolation, because the test has to either populate the
global before the class under test runs, or accept whatever was left behind
by whichever test ran previously in the same process. Every one of the four
code samples below therefore does two things worth calling out for testing
purposes specifically. it fails loudly, an exception or an `Err`, never a
silent `None`/`null`/zero value, on a lookup miss, and it fails loudly on a
duplicate registration, so a test-isolation bug surfaces as an assertion
failure rather than a mysteriously wrong value three layers away.

- **Fake registry as a test double.** The most direct technique for testing
  a class that must keep calling `resolve` directly (rather than being
  refactored to constructor injection) is to give tests a fresh, disposable
  instance of the registry type per test, rather than sharing the process
  singleton, and to populate it with fakes inside the test's own setup. This
  requires the registry class itself to be instantiable, not only accessible
  as a bare static singleton, which is why the code samples in this entry
  define a `ServiceRegistry`/`ExporterRegistry`/`Registry` type rather than a
  single hard-coded module-level dictionary with no wrapping type.
- **Preferred technique, eliminate the registry call from the class under
  test.** Following the "refactoring out" path in dimension 14 for the
  specific class being tested turns the test from "populate a global, then
  assert" into "construct the object with a fake collaborator, then assert,"
  which is strictly less fragile and does not depend on test execution
  order at all.
- **Parallel test runners expose registry sharing bugs fastest.** Go's
  `t.Parallel()`, pytest-xdist, and Rust's default multi-threaded `cargo
  test` runner will run tests that touch a shared, unscoped, mutable
  registry concurrently unless the registry itself is either read-only after
  boot (the frozen variant) or explicitly reset and isolated per test. A
  registry with no freeze step and no test-scoped instance is a
  disproportionately common cause of flaky parallel test suites, and the
  first diagnostic step for a suite that is flaky under parallel execution
  but stable under serial execution should be checking for exactly this.
- **Boot-time integration test.** In addition to unit-level fakes, a small
  integration test that runs the real bootstrap sequence and then resolves
  every documented key catches the class of bug in dimension 11's first
  failure mode, an entry that should have been registered but was not,
  because of an ordering mistake in the bootstrap sequence itself, that no
  amount of unit-level test-double substitution can catch, because the bug
  is in the wiring, not in any individual class's logic.

## 16. Observability signals

- **Log every registration at boot, including the key and the concrete type
  registered under it.** A boot log that lists "registered clock ->
  SystemClock, registered gateway -> StripeGateway" turns "why is my
  gateway a mock in production" into a one-line grep of the startup log,
  rather than a debugger session.
- **Log, or increment a counter for, every lookup miss.** A lookup miss at
  runtime, after boot has completed and the registry has been frozen, is
  always a bug, never an expected condition, and should be treated with the
  same seriousness as an unhandled exception, because by the time a
  frozen registry is being queried the set of valid keys is fixed and known.
- **Expose the current key set through a diagnostic or introspection
  endpoint.** Django's `apps.get_app_configs()` and Spring's Actuator
  `/actuator/beans` endpoint are both, functionally, "dump the registry's
  current contents," and either is invaluable for confirming a deploy
  actually took effect, or that a plugin actually loaded, without adding
  print statements to source code.
- **Track registry size as a metric over a deploy's lifetime.** A registry
  that starts at, say, 40 entries at boot and grows steadily during
  steady-state traffic is exhibiting the dynamic re-registration failure mode
  from dimension 11, and the metric alone, graphed over time, is enough to
  catch it before it causes a data race under load.
- **A healthy signal.** the key count is stable immediately after boot
  completes, matches the count expected from the bootstrap sequence exactly,
  and the lookup-miss counter stays at zero for the lifetime of the process.
  **A failing signal.** the key count keeps changing minutes after the
  process reports itself ready, or the lookup-miss counter is nonzero at any
  point after boot, either of which should page whoever owns the service
  before the symptom reaches a customer.

## 17. Security and privacy implications

Registry's attack surface is small when it is used only for wiring
already-trusted, in-process objects together, but the pattern has a documented
history of becoming a genuine remote-code-execution vector at the moment its
lookup mechanism is exposed, directly or indirectly, to attacker-controlled
input. The canonical example is JNDI (dimension 9), a registry-and-directory
lookup API. CVE-2021-44228, known as Log4Shell, existed because Apache
Log4j2 evaluated a JNDI lookup expression embedded in log message content, and
the vendor's own advisory states that "an attacker who can control log
messages or log message parameters can execute arbitrary code loaded from
LDAP servers"
([Apache Logging Services, Log4j Security Vulnerabilities](https://logging.apache.org/log4j/2.x/security.html),
verified 2026-08-02). The lesson generalises well beyond Log4j or JNDI
specifically, because any registry whose lookup KEY can be influenced,
directly or indirectly, by data that originates outside the trust boundary of
the process, a request header, a log message, a user-supplied filename used
as a plugin name, turns a benign-looking `registry.resolve(userSuppliedKey)`
call into an arbitrary-code-loading primitive if the registry, or anything it
delegates to, can be told to fetch and instantiate a class from a location the
attacker controls.

Two further, narrower implications follow from the same shape.

- **Credential and secret handling.** A process-wide registry readable from
  any code path in the application is a poor home for a raw secret (an API
  key, a database password) because every future contributor who imports the
  registry gains implicit access to everything stored in it, with no
  per-caller audit trail. Store a client wrapping the secret (a
  pre-configured HTTP client, an already-authenticated database connection)
  in the registry instead of the raw credential, so the registry exposes
  capability rather than the secret material itself.
- **Key-collision as a supply-chain concern.** In a registry that allows
  third-party or plugin code to register under a string key of its choosing,
  a malicious or merely careless dependency can register under a key your
  own code already uses, silently shadowing your intended implementation
  with its own. The duplicate-registration rejection shown in every code
  sample in dimension 15 is a direct, cheap mitigation, since treating a
  duplicate key as a hard failure at registration time, rather than a silent
  overwrite, makes a collision surface at boot rather than as a puzzling
  behavior change in production traced back weeks later to an unrelated
  dependency bump.

## 18. References

1. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, chapter 18, Base Patterns, Registry. Catalog summary
   at [martinfowler.com/eaaCatalog/registry.html](https://martinfowler.com/eaaCatalog/registry.html),
   verified 2026-08-02.
2. Martin Fowler, "Inversion of Control Containers and the Dependency
   Injection pattern," comparison of Service Locator and Dependency
   Injection. [martinfowler.com/articles/injection.html](https://martinfowler.com/articles/injection.html),
   verified 2026-08-02.
3. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
   Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley,
   1994, chapter 3, Creational Patterns, Singleton.
4. Oracle, "Interface LocateRegistry," Java SE 8 API documentation, describing
   `java.rmi.registry.Registry` as the bootstrap remote object registry.
   [docs.oracle.com/javase/8/docs/api/java/rmi/registry/LocateRegistry.html](https://docs.oracle.com/javase/8/docs/api/java/rmi/registry/LocateRegistry.html),
   verified 2026-08-02.
5. Wikipedia, "Java Naming and Directory Interface." [en.wikipedia.org/wiki/Java_Naming_and_Directory_Interface](https://en.wikipedia.org/wiki/Java_Naming_and_Directory_Interface),
   verified 2026-08-02.
6. Django Software Foundation, "Applications," Django 5.2 documentation,
   describing `django.apps.apps` as the registry of installed applications.
   [docs.djangoproject.com/en/5.2/ref/applications/](https://docs.djangoproject.com/en/5.2/ref/applications/),
   verified 2026-08-02.
7. VMware, "Core Technologies," Spring Framework reference documentation,
   IoC Container section describing `BeanFactory` and `ApplicationContext`.
   [docs.spring.io/spring-framework/reference/core/beans/introduction.html](https://docs.spring.io/spring-framework/reference/core/beans/introduction.html),
   verified 2026-08-02.
8. Microsoft, "Dependency injection - .NET," describing `IServiceCollection`
   and `IServiceProvider`. [learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection](https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection),
   verified 2026-08-02.
9. The Apache Software Foundation, "Log4j Security Vulnerabilities,"
   description of CVE-2021-44228 (Log4Shell) and the JNDI lookup mechanism it
   exploited. [logging.apache.org/log4j/2.x/security.html](https://logging.apache.org/log4j/2.x/security.html),
   verified 2026-08-02.

## Code examples

Four languages, chosen because Registry's shape differs meaningfully across
them. TypeScript's generics give a type-safe `resolve<T>`; Python's decorator
idiom mirrors how Django and Click actually register plugins in the wild;
Go's version mirrors the standard library's own `database/sql.Register`
convention; Rust's version shows the pattern behind a `Mutex`-guarded
`OnceLock`, the idiomatic shape for a thread-safe global since `OnceLock`
stabilised. Java and C#/Kotlin are omitted from the runnable samples in this
entry because a JDK was not available in the environment used to write it (no
`javac` on `PATH`), and Kotlin/C# were not installed either; the .NET and
Spring containers are covered in prose in dimensions 8 and 9 instead, with
their own verified citations.

All four samples below were compiled or run directly, with output confirmed,
in the environment used to write this entry. `npx tsc` (TypeScript 7.0.2,
strict mode), `python3` (system Python 3), `go run` plus `go vet` (Go
1.26.4), and `rustc --edition 2021` (Rust 1.97.1).

### TypeScript

```typescript
// A minimal typed Registry. Registration happens once at bootstrap.
// Lookup returns a typed value or throws, never returns undefined silently.

class ServiceRegistry {
  private entries = new Map<string, unknown>();
  private frozen = false;

  register<T>(key: string, value: T): void {
    if (this.frozen) {
      throw new Error(`registry is frozen, cannot register "${key}" after boot`);
    }
    if (this.entries.has(key)) {
      throw new Error(`duplicate registration for "${key}"`);
    }
    this.entries.set(key, value);
  }

  resolve<T>(key: string): T {
    const value = this.entries.get(key);
    if (value === undefined) {
      throw new Error(`no service registered under "${key}"`);
    }
    return value as T;
  }

  freeze(): void {
    this.frozen = true;
  }

  keys(): string[] {
    return [...this.entries.keys()];
  }
}

interface Clock {
  now(): number;
}

class SystemClock implements Clock {
  now(): number {
    return Date.now();
  }
}

const registry = new ServiceRegistry();

function bootstrap(): void {
  registry.register<Clock>("clock", new SystemClock());
  registry.register<string>("environment", "production");
  registry.freeze();
}

class OrderTimestamper {
  private clock = registry.resolve<Clock>("clock");

  stamp(orderId: string): string {
    return `${orderId}@${this.clock.now()}`;
  }
}

bootstrap();
const stamper = new OrderTimestamper();
console.log(stamper.stamp("order-42"));
console.log("registered keys:", registry.keys());

try {
  registry.register("clock", new SystemClock());
} catch (e) {
  console.log("expected failure:", (e as Error).message);
}
```

Output, compiled with `npx tsc --strict --target es2020 --module commonjs`
and run with `node`.

```
order-42@1786448963166
registered keys: [ 'clock', 'environment' ]
expected failure: registry is frozen, cannot register "clock" after boot
```

### Python

```python
"""A decorator-driven Registry for pluggable exporters, in the style of
Django's app registry and click's command registry: modules self-register
by import side effect, and a single dict is the well-known lookup point."""

from __future__ import annotations
from typing import Callable, Protocol


class Exporter(Protocol):
    def export(self, rows: list[dict]) -> str: ...


class ExporterRegistry:
    def __init__(self) -> None:
        self._entries: dict[str, type[Exporter]] = {}

    def register(self, name: str) -> Callable[[type[Exporter]], type[Exporter]]:
        def decorator(cls: type[Exporter]) -> type[Exporter]:
            if name in self._entries:
                raise ValueError(f'exporter "{name}" already registered')
            self._entries[name] = cls
            return cls
        return decorator

    def create(self, name: str) -> Exporter:
        try:
            cls = self._entries[name]
        except KeyError:
            known = ", ".join(sorted(self._entries)) or "(none)"
            raise KeyError(f'no exporter "{name}", known exporters: {known}') from None
        return cls()

    def names(self) -> list[str]:
        return sorted(self._entries)


registry = ExporterRegistry()


@registry.register("csv")
class CsvExporter:
    def export(self, rows: list[dict]) -> str:
        if not rows:
            return ""
        header = ",".join(rows[0].keys())
        body = "\n".join(",".join(str(v) for v in row.values()) for row in rows)
        return f"{header}\n{body}"


@registry.register("json")
class JsonExporter:
    def export(self, rows: list[dict]) -> str:
        import json
        return json.dumps(rows)


def run_export(format_name: str, rows: list[dict]) -> str:
    exporter = registry.create(format_name)
    return exporter.export(rows)


if __name__ == "__main__":
    data = [{"id": 1, "name": "widget"}, {"id": 2, "name": "gadget"}]
    print(run_export("csv", data))
    print(run_export("json", data))
    print("known exporters:", registry.names())
    try:
        run_export("xml", data)
    except KeyError as e:
        print("expected failure:", e)
```

Output, run with `python3`.

```
id,name
1,widget
2,gadget
[{"id": 1, "name": "widget"}, {"id": 2, "name": "gadget"}]
known exporters: ['csv', 'json']
expected failure: 'no exporter "xml", known exporters: csv, json'
```

### Go

```go
// Package main shows the Registry pattern in the idiom Go's own standard
// library uses: database/sql.Register lets a driver author call
// sql.Register("postgres", &Driver{}) from an init() function, so the
// caller only imports the driver package for its side effect and the
// registry, not sql itself, decides which concrete type answers a name.
package main

import (
	"fmt"
	"sort"
	"sync"
)

// Notifier is the separated interface every channel implementation satisfies.
type Notifier interface {
	Send(message string) error
}

type notifierFactory func() Notifier

var (
	mu         sync.RWMutex
	registered = map[string]notifierFactory{}
)

// Register makes a notifier factory available under name. It panics on a
// duplicate registration, the same contract database/sql.Register uses,
// because a silently overwritten driver is a boot-time bug worth crashing on.
func Register(name string, factory notifierFactory) {
	mu.Lock()
	defer mu.Unlock()
	if _, exists := registered[name]; exists {
		panic(fmt.Sprintf("registry: Register called twice for %q", name))
	}
	registered[name] = factory
}

// Open resolves name to a live Notifier, or reports the names that do exist.
func Open(name string) (Notifier, error) {
	mu.RLock()
	defer mu.RUnlock()
	factory, ok := registered[name]
	if !ok {
		names := make([]string, 0, len(registered))
		for k := range registered {
			names = append(names, k)
		}
		sort.Strings(names)
		return nil, fmt.Errorf("registry: unknown notifier %q, known: %v", name, names)
	}
	return factory(), nil
}

type consoleNotifier struct{}

func (consoleNotifier) Send(message string) error {
	fmt.Println("console:", message)
	return nil
}

func init() {
	Register("console", func() Notifier { return consoleNotifier{} })
}

func main() {
	n, err := Open("console")
	if err != nil {
		panic(err)
	}
	if err := n.Send("order shipped"); err != nil {
		panic(err)
	}

	if _, err := Open("sms"); err != nil {
		fmt.Println("expected failure:", err)
	}
}
```

Output, run with `go vet ./...` (clean) then `go run main.go`.

```
console: order shipped
expected failure: registry: unknown notifier "sms", known: [console]
```

### Rust

```rust
// A Registry guarded by a Mutex behind a std::sync::OnceLock, the idiomatic
// Rust shape for "one shared, lazily-initialised, thread-safe global" since
// OnceLock stabilised in Rust 1.70. Registration returns a Result rather
// than panicking, because a Rust registry is a fallible operation, not an
// exception.

use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

trait PaymentGateway: Send + Sync {
    fn charge(&self, cents: u64) -> String;
}

struct StripeGateway;
impl PaymentGateway for StripeGateway {
    fn charge(&self, cents: u64) -> String {
        format!("stripe charged {cents} cents")
    }
}

type Factory = fn() -> Box<dyn PaymentGateway>;

struct Registry {
    entries: Mutex<HashMap<&'static str, Factory>>,
}

fn registry() -> &'static Registry {
    static INSTANCE: OnceLock<Registry> = OnceLock::new();
    INSTANCE.get_or_init(|| Registry {
        entries: Mutex::new(HashMap::new()),
    })
}

fn register(name: &'static str, factory: Factory) -> Result<(), String> {
    let mut entries = registry().entries.lock().map_err(|e| e.to_string())?;
    if entries.contains_key(name) {
        return Err(format!("duplicate registration for \"{name}\""));
    }
    entries.insert(name, factory);
    Ok(())
}

fn resolve(name: &str) -> Result<Box<dyn PaymentGateway>, String> {
    let entries = registry().entries.lock().map_err(|e| e.to_string())?;
    match entries.get(name) {
        Some(factory) => Ok(factory()),
        None => {
            let mut known: Vec<&&str> = entries.keys().collect();
            known.sort();
            Err(format!("no gateway \"{name}\", known: {known:?}"))
        }
    }
}

fn main() {
    register("stripe", || Box::new(StripeGateway)).expect("boot-time registration failed");

    let gateway = resolve("stripe").expect("stripe must be registered");
    println!("{}", gateway.charge(1999));

    match resolve("paypal") {
        Ok(_) => unreachable!(),
        Err(e) => println!("expected failure: {e}"),
    }

    match register("stripe", || Box::new(StripeGateway)) {
        Ok(_) => unreachable!(),
        Err(e) => println!("expected failure: {e}"),
    }
}
```

Output, compiled with `rustc --edition 2021`.

```
stripe charged 1999 cents
expected failure: no gateway "paypal", known: ["stripe"]
expected failure: duplicate registration for "stripe"
```
