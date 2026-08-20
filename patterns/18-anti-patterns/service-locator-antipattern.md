---
name: Service Locator Antipattern
slug: service-locator-antipattern
family: 18-anti-patterns
category: Anti-pattern
aliases: [Service Locator, Locator Pattern, Registry Lookup, Container Lookup, Ambient Container]
first_described: "Alur, Crupi, Malks 2001 (pattern); Seemann 2010 (anti-pattern criticism)"
maturity: contested
related: [dependency-injection, inversion-of-control, singleton-abuse, abstract-factory, factory-method, service-provider-interface]
incompatible_with: [dependency-injection, explicit-dependencies-principle]
verified: 2026-08-02
---

# Service Locator Antipattern

## 1. Name, aliases, and lineage

The canonical name in this entry is Service Locator Antipattern. The shorter
name Service Locator is older and more neutral, so this entry keeps the
antipattern label explicit. In older enterprise Java writing, the name referred
to a central object that hid the mechanics of looking up JNDI resources,
Enterprise JavaBeans, JMS factories, and similar container resources. Deepak
Alur, John Crupi, and Dan Malks cataloged Service Locator in *Core J2EE
Patterns. Best Practices and Design Strategies*, first edition, 2001, chapter
8, "Service Locator". The original setting matters. J2EE clients had to perform
verbose, exception-heavy lookups against infrastructure APIs, and a shared
lookup helper reduced duplicated platform code. That historical source is a
book citation, not a claim that the design is good for current application
objects.

Martin Fowler later framed Service Locator beside Dependency Injection in
"Inversion of Control Containers and the Dependency Injection pattern". Fowler
describes a locator as an object that knows how to obtain the services an
application needs, and contrasts that with injection, where the application
class receives the service without asking the locator itself (Martin Fowler,
"Inversion of Control Containers and the Dependency Injection pattern",
https://martinfowler.com/articles/injection.html, verified 2026-08-02). Fowler
also says the decision depends on whether the dependency on the locator itself
is a problem. That conditional stance is one reason the classification remains
contested rather than canonical.

The hard antipattern classification became widely associated with Mark Seemann.
In "Service Locator is an Anti-Pattern", Seemann argues that Service Locator
hides dependencies, converts compile-time feedback into runtime errors, and
makes API evolution harder to reason about (Mark Seemann, "Service Locator is
an Anti-Pattern",
https://blog.ploeh.dk/2010/02/03/ServiceLocatorisanAnti-Pattern/, verified
2026-08-02). In *Dependency Injection Principles, Practices, and Patterns*,
Steven van Deursen and Mark Seemann define the anti-pattern as supplying
application components outside the composition root with access to an unbounded
set of dependencies, quoted in Manning's excerpt "The Service Locator
Anti-Pattern" (Steven van Deursen and Mark Seemann, *Dependency Injection
Principles, Practices, and Patterns*, Manning, 2019, chapter 5; Manning
excerpt, https://freecontent.manning.com/the-service-locator-anti-pattern/,
verified 2026-08-02).

Common aliases include Locator Pattern, Registry Lookup, Container Lookup, and
Ambient Container. The alias Ambient Container is used here for the common
variant where a framework container is stored in a process global,
thread-local, request-local, or module global and can be asked for arbitrary
services from ordinary business code. Java's `ServiceLoader` is deliberately
not treated as the same thing. The Java SE API describes `ServiceLoader` as a
facility for loading providers of one known service type, where application
code refers to the service interface rather than to provider implementations
(Oracle, Java SE 17 API, `java.util.ServiceLoader`,
https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ServiceLoader.html,
verified 2026-08-02). That is Service Provider Interface discovery, not an
unbounded dependency bag.

## 2. Problem and context

A component needs collaborators to perform its work. It may need a repository,
a cache, a clock, a payment gateway, a message publisher, a feature flag reader,
or a logger. In explicit dependency design, those collaborators appear in the
constructor, function parameters, or fields initialized by a small assembly
layer. In Service Locator design, the component asks a shared locator for them
inside the method that happens to need them.

The code often begins with a convenience argument. A constructor already has
five parameters, and adding a sixth makes the class look worse. A method is far
from the composition root, and threading a dependency down through three call
layers feels tedious. A framework callback creates an object without giving the
team a constructor hook. A static helper needs a collaborator, and converting it
to an instance would touch several files. The locator offers an immediate escape:
register the collaborator once, then call `get`, `resolve`, `make`, or
`getBean` anywhere.

The problem is that the class's public shape no longer states what the class
requires. A reader sees a constructor that accepts no repository, yet a method
will fail if no repository is registered. A test instantiates the class without
arguments, then discovers a missing payment gateway only after the tested path
enters a branch that performs the lookup. An operator sees a production failure
from a missing registration, but the deployment diff changed a class whose
constructor did not mention the dependency at all. The locator did not remove
the dependency. It moved the dependency from an inspectable contract to an
implicit runtime precondition.

The context that makes the shape an antipattern is modern application code with
an available composition root. Spring, ASP.NET Core, Angular, Guice, Dagger,
FastAPI dependency callables, and many smaller containers already provide a
place where object construction is configured separately from business logic.
Calling the container from inside a component managed by that container mixes
two control styles. Microsoft's DI guidance states this directly by advising
against invoking `GetService` to obtain a service instance when DI can be used
instead, and against factories that resolve dependencies at runtime (Microsoft,
".NET dependency injection guidelines",
https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/guidelines,
section "Recommendations", verified 2026-08-02).

The narrow context where the locator shape can still be defensible is different.
It is framework infrastructure, plugin discovery, or a legacy callback where the
caller cannot be constructed by the application's composition root. In that
case the lookup belongs at the boundary, and the object produced at that
boundary should receive ordinary explicit dependencies from then on.

The practical diagnostic is simple. Ask whether a new reader can instantiate
the component correctly by reading its type signature and imports. If the
answer is no because the reader must also know which keys are present in an
ambient registry, the component is carrying hidden preconditions. Ask also
whether the component could be moved into another application without bringing
the original container API along. If the answer is no, the component has become
less portable than its interface suggests. Those two questions expose the
antipattern earlier than runtime failures do.

## 3. Forces

This dimension is engineering judgement, supported by the cited descriptions
but not by a single controlled benchmark.

- **Convenience.** Favored in the smallest edit. A new dependency can be added
  to a method body without changing the constructor or each construction site.
- **Dependency discoverability.** Sacrificed. A class's collaborators are now
  found by searching method bodies, not by reading the public constructor or
  function signature. Fowler names this distinction when he says injection lets
  a reader see dependencies in the constructor or setter, while Service Locator
  requires searching for calls to the locator (Fowler, same article, verified
  2026-08-02).
- **Compile-time feedback.** Sacrificed. Missing or wrong registrations appear
  at runtime, usually on the path that performs the lookup. Seemann's critique
  centers on this shift from compile-time errors to runtime errors (Seemann,
  "Service Locator is an Anti-Pattern", verified 2026-08-02).
- **Test isolation.** Sacrificed when the locator is global or mutable. Tests
  must configure shared state, reset it afterward, and protect themselves from
  order dependence. Injection turns the same substitution into a local argument.
- **Local class size.** Favored superficially. Constructors stay short because
  dependencies disappear from the signature. That is often false simplicity,
  because the real dependency count still exists in the implementation.
- **Cognitive load.** Sacrificed for maintainers. A reader must know both the
  class and the locator registration graph to know whether a method can run.
- **Operability.** Sacrificed unless lookups are instrumented. A failed lookup
  says which key was absent, but not which higher-level dependency contract was
  broken unless the locator records the consumer and call path.
- **Team topology.** Sacrificed in shared libraries. A library that calls an
  application-specific locator forces every application to provide that locator
  or an adapter. Fowler calls this out when discussing components that may be
  used by applications outside the author's control (same article, verified
  2026-08-02).
- **Runtime flexibility.** Favored in plugin or framework infrastructure. A
  caller can ask for a type discovered at runtime. The same force is a weakness
  in business logic where the set of collaborators is known during assembly.
- **Security review.** Sacrificed. A broad locator can become an ambient
  privilege surface, because code that receives the locator may resolve more
  than the one collaborator it was meant to use.

There is also a versioning force. Constructor Injection makes an added
dependency an explicit breaking change for callers that construct the class.
That sounds painful, but the pain occurs at the edit site that must respond.
Service Locator lets the same change look source-compatible while adding a new
registration requirement elsewhere. For a public library, that is worse
developer experience. The caller learns about the new requirement when a path
is exercised, not when the dependency was introduced. For internal application
code, the same issue appears as deployment risk. A class can be merged with a
new hidden lookup while the environment that registers services is not updated.
The build may still pass because no constructor or factory signature changed.

## 4. Applicability and non-applicability

Reach for a locator-shaped mechanism only when one of these conditions is true.

- A framework provides a container object to infrastructure code that is itself
  part of the composition root. Resolving during startup, request pipeline
  construction, or handler dispatch can be appropriate when the resolved object
  is then invoked with explicit contracts.
- A plugin mechanism discovers implementations after the application is built.
  Java's `ServiceLoader` is an example of type-scoped provider discovery rather
  than a general service locator, and it is preferable when the problem is
  discovery of implementations for one service interface.
- A legacy framework constructs objects through callbacks that cannot receive
  constructor parameters. Use one adapter at that boundary, then pass explicit
  dependencies into the domain object it creates.
- A short script has one entry point and no meaningful object graph. A local map
  in `main` is not worth converting into a container, provided it does not
  migrate into shared application code.
- A container must resolve its own internals. This is a framework implementor
  concern, not an application component pattern.

Non-applicability list.

- Do not use it inside a class that the DI container already creates. That
  component can ask for its collaborators through constructor injection,
  property injection where the framework demands it, or a typed factory.
- Do not use it to hide a long constructor. A long constructor is feedback that
  the class may have too many responsibilities. Hiding dependencies makes the
  design harder to repair.
- Do not use it to avoid updating tests. A test that passes a fake collaborator
  as a constructor argument is simpler than one that mutates global locator
  state and cleans it up afterward.
- Do not use it for lazy initialization. Inject `Lazy<T>`, a provider of one
  specific type, or a typed factory. The dependency stays visible and creation
  can still be deferred.
- Do not use it as a service registry for business data. User carts, tenant
  context, request data, or feature flag values are not services. Store them in
  explicit request context or pass them as values.
- Do not inject `IServiceProvider`, `ApplicationContext`, `Injector`, or a
  similar container into ordinary domain services so they can resolve whatever
  they need. That is the most common modern form of the antipattern.
- Do not use a string-keyed locator when a typed interface can be passed. A
  string key gives up both refactoring support and type checking.
- Do not use it to cross module boundaries in a shared library. The library
  should not assume the host application's container API.

## 5. Structure

The participants are named by role.

- **Consumer.** The class or function that needs one or more collaborators. In
  the antipattern, its public constructor does not list those collaborators.
- **Locator.** A registry or adapter that accepts a key and returns an object.
  The key may be a string, a type token, an interface class, a symbol, or a
  framework-specific token.
- **Registration Source.** The startup code, module import, configuration file,
  plugin scanner, or test setup that fills the locator with mappings.
- **Service.** The collaborator returned from the locator. It may be a concrete
  singleton, a scoped object, a transient instance, or a proxy that will create
  another object later.
- **Composition Root.** The place where application wiring should live. In the
  acceptable boundary variant, the composition root uses the locator and then
  hands explicit dependencies to consumers. In the antipattern variant, the
  consumer reaches back into the composition root during normal work.

Two structural details distinguish the antipattern from legitimate provider
discovery. First, the locator is broad. It can return unrelated services. Second,
the consumer controls the lookup. The object that uses the dependency asks for
it, rather than receiving it as part of construction.

## 6. ASCII structure diagram

```text
Antipattern structure.

  +------------------+       get("repo")        +------------------+
  |     Consumer     | -----------------------> |     Locator      |
  |------------------|                          |------------------|
  | + handle(cmd)    |                          | + get(key): any  |
  |                  |                          | + set(key, obj)  |
  +------------------+                          +------------------+
          |                                               ^
          | uses returned object                          |
          v                                               |
  +------------------+                         registers  |
  |     Service      | <-----------------------------------+
  |------------------|              +----------------------+
  | + operation()    |              |
  +------------------+              |
                                    |
                         +----------------------+
                         |  Registration Source |
                         |----------------------|
                         | startup, test, plugin|
                         +----------------------+

Preferred boundary.

  +------------------+      constructs       +------------------+
  | Composition Root | --------------------> |     Consumer     |
  |------------------|                       |------------------|
  | resolve services |                       | repo in ctor     |
  +------------------+                       +------------------+
             |                                      |
             v                                      v
       +-----------+                          +-----------+
       | Locator   |                          | Service   |
       +-----------+                          +-----------+
```

## 7. Dynamics

In the faulty runtime flow, the dependency failure is delayed until the consumer
enters the method that performs the lookup.

```text
Startup              Locator             Consumer              Service
  |                    |                    |                    |
  |-- register Cache ->|                    |                    |
  |                    |                    |                    |
  |-- register Repo -->|                    |                    |
  |                    |                    |                    |
  |-- new Consumer ----------------------->|                    |
  |                    |                    |                    |
  |                    |<-- handle(cmd) ----|                    |
  |                    |                    |                    |
  |                    |<-- get("Repo") ----|                    |
  |-- Repo instance -->|------------------->|                    |
  |                    |                    |-- save() --------->|
  |                    |                    |<-- ok -------------|
  |                    |                    |                    |
  |                    |<-- get("Gateway") -|                    |
  |-- missing key -----|------------------->|                    |
  |                    |                    |-- throws ----------|
  |                    |                    |                    |

The constructor did not communicate that Gateway was required.
The missing dependency appears only after the late lookup is reached.
```

The repair changes the direction of the flow. Startup resolves or constructs
collaborators once, then passes them into the consumer. If a dependency is
missing, the system fails during assembly rather than during a request.

## 8. Implementation variants

**Static global locator.** A class or module holds a process-wide map. Consumers
call it directly. This is the most harmful variant because every test and every
request shares mutable resolution state unless the implementation adds scoping.

**Container injected as locator.** A consumer receives `IServiceProvider`,
`ApplicationContext`, Angular `Injector`, or an equivalent object, then calls
`get` inside methods. This looks more disciplined than a static global because
the container arrives through the constructor, but the dependency contract is
still unbounded. The constructor says "I need the world" rather than "I need a
repository and a clock".

**String-keyed registry.** The locator maps textual names to services. It is
flexible and language-neutral, but refactoring support is weak. A renamed
service can leave a runtime miss instead of a compiler error.

**Type-keyed registry.** The locator maps type tokens or interface classes to
instances. This improves type safety in languages that can express the key and
return type together, but it still hides the dependency from the consumer's
public contract.

**Scoped locator.** The locator is tied to a request, thread, actor, transaction,
or task. ASP.NET Core's `HttpContext.RequestServices` exposes the scoped service
provider for the current request, and the docs describe it as the scoped service
provider whose scoped services are valid for the request lifetime (Microsoft,
"Dependency injection in ASP.NET Core",
https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection,
section "Request Services", verified 2026-08-02). Scope reduces lifetime bugs,
but it does not make arbitrary resolution inside business logic explicit.

**Service provider interface discovery.** Java `ServiceLoader` and similar
mechanisms discover implementations of one known interface from deployment
metadata. This is adjacent, not identical. It is acceptable when the caller's
dependency on that single service interface is explicit and discovery is the
actual problem.

**Abstract factory replacement.** A consumer receives a narrow factory such as
`PaymentGatewayFactory` or `ReportHandlerFactory`. It can still create objects
at runtime, but the factory interface advertises the permitted dependency
family. This is the usual replacement when runtime selection is real.

**Provider or lazy replacement.** A consumer receives `Provider<Cache>`,
`() => Cache`, `Lazy<Cache>`, or another type-specific delayed supplier. This
keeps the dependency visible while deferring construction.

**Thread-local or context-local locator.** Some systems hide a locator in a
thread-local, async-local, request context, or task context. This removes a
parameter from every intermediate call, but it couples code to an execution
model. A function that works in a request thread may fail in a background job,
test runner, worker pool, or continuation where the local context was not set.
Use context-local storage for values that are truly part of the execution
context, such as a trace identifier, and be cautious about storing general
collaborators there.

**Fallback locator.** Another variant tries constructor injection first and then
falls back to a locator for missing dependencies. This is especially confusing
because the signature partly communicates the contract while the fallback hides
the rest. It also makes tests lie. A test can omit a dependency and still pass
because a process-wide fallback provides one. Prefer one assembly rule per
class. Either the dependency is required and appears in the constructor, or it
is optional and appears as an explicit optional parameter with documented
behavior when absent.

## 9. Known production uses

These are named production APIs that expose locator-shaped lookup. Their
existence is not presented as proof that application code should use the shape
freely. The interpretation is engineering judgement.

**Spring Framework, `ApplicationContext.getBean`.** Spring documents
`ApplicationContext` as an advanced factory with a registry of beans and shows
`getBean(String, Class<T>)` retrieving a configured instance. The same page says
application code should ideally have no calls to `getBean()` and no dependency
on Spring APIs, because Spring integration can inject dependencies into web
components (Spring Framework Reference, "Container Overview",
https://docs.spring.io/spring-framework/reference/core/beans/basics.html,
verified 2026-08-02). This is a production use of a locator API and an official
warning about where not to use it.

**ASP.NET Core, `HttpContext.RequestServices`.** ASP.NET Core exposes request
services through `HttpContext.RequestServices`, and Microsoft documents it as an
`IServiceProvider` for the request's service container (Microsoft Learn,
`HttpContext.RequestServices`,
https://learn.microsoft.com/en-us/dotnet/api/microsoft.aspnetcore.http.httpcontext.requestservices,
verified 2026-08-02). ASP.NET Core's DI page also says to prefer constructor
parameters over resolving services from `RequestServices` (Microsoft,
"Dependency injection in ASP.NET Core", section "Request Services", verified
2026-08-02).

**Angular, `Injector.get`.** Angular's `Injector` API defines `get` overloads
that retrieve values by provider token, and the page states that concrete
injectors are configured with providers associating dependency types with
tokens (Angular API, `Injector`, https://angular.dev/api/core/Injector,
verified 2026-08-02). Angular's normal component model favors declarative
injection, but the API is a real locator-shaped mechanism for framework and
advanced application code.

**Laravel, service container `make`.** Laravel documents the container's `make`
method as resolving a class instance from the container by class or interface
name (Laravel 10.x documentation, "Service Container", section "Resolving",
https://laravel.com/docs/10.x/container, verified 2026-08-02). This is a
production container lookup API. Whether a call belongs in application logic or
at an assembly boundary is a design judgement, not something the method name
can decide.

## 10. Consequences

Positive consequences.

- It removes repeated platform lookup code where a legacy container API is noisy
  or expensive.
- It provides one place to cache expensive infrastructure resources that are
  genuinely identified by a platform registry.
- It gives framework code a uniform way to resolve implementations when the
  concrete type is not known until runtime.
- It can reduce constructor churn during a narrow migration, provided there is
  a plan to replace it with explicit dependencies afterward.
- It can serve as an adapter around a legacy API so the rest of the system does
  not import that API directly.

Negative consequences.

- It hides a consumer's real dependency contract.
- It moves missing-dependency errors from assembly time to runtime.
- It makes tests mutate shared registry state unless the locator is scoped and
  substitutable.
- It couples consumers to the locator API, often a framework API, which makes
  shared libraries less portable.
- It weakens refactoring support, especially in string-keyed variants.
- It hides lifetime relationships. A singleton consumer can accidentally pull a
  request-scoped dependency unless the container detects and blocks it.
- It makes security review harder because receiving a broad locator grants
  access to more services than the consumer's role may require.
- It encourages classes with too many responsibilities by making their growing
  dependency set less visible.

The most costly consequence is social rather than mechanical. Once a team
accepts locator calls as normal, constructor growth stops acting as design
feedback. Reviewers no longer see that a class now talks to persistence,
messaging, payment, scheduling, and configuration. A dependency list that would
have triggered a split becomes a handful of ordinary method calls. The class can
therefore drift for months before anyone sees the shape plainly. Engineering
judgement. This is why Service Locator often travels with God Object and
Anemic Domain Model symptoms. It lets coordination code collect more duties
without making the duty count obvious at the boundary.

## 11. Failure modes and misuse

**Symptom.** A unit test passes when run alone but fails after another test.
**Cause.** Both tests mutate the same static locator registry, and the first
test leaves a fake or missing registration behind. **Fix.** Replace locator
calls in the class under test with constructor parameters. If the locator cannot
be removed yet, add scoped registration objects and reset them in fixture
teardown.

**Symptom.** A request fails with "service not registered" in the middle of a
business operation, although object construction completed earlier. **Cause.**
The dependency is looked up lazily from a method body, so startup never proved
that the object graph was complete. **Fix.** Move the dependency into the
constructor or into a narrow typed factory injected at construction time.

**Symptom.** A shared library works in one host application but not another,
because it expects a particular container or locator class. **Cause.** The
library depends on the host's service location mechanism. **Fix.** Define a
small library-owned interface for the collaborator and let the host inject an
implementation.

**Symptom.** A class grows behavior across several domains while its constructor
still looks small. **Cause.** New collaborators are resolved from the locator
instead of appearing as constructor growth, so Single Responsibility Principle
pressure is hidden. **Fix.** Inventory every locator lookup, group them by
reason for change, and split the class before replacing lookups.

**Symptom.** A production incident involves the wrong implementation for a
tenant or request. **Cause.** A broad locator key was overwritten or resolved
from the wrong scope. **Fix.** Make duplicate registrations fail, use typed
keys, and move tenant-specific values into explicit request context.

**Symptom.** A singleton object captures a scoped dependency and later uses it
after the request is over. **Cause.** The locator allowed a long-lived consumer
to resolve a shorter-lived service. **Fix.** Use scope validation where the
container supports it, inject factories that create scoped work inside a scope,
and avoid storing resolved scoped objects on singletons.

**Symptom.** A code search for a repository interface misses half its consumers.
**Cause.** Some callers request the repository by string key, by base type, or
through a generic container method. **Fix.** Replace textual keys with typed
interfaces during migration, then make the dependency explicit.

## 12. Trade-off matrix

| Force | Service Locator | Constructor Injection | Abstract Factory | ServiceLoader or SPI | Direct Singleton |
|---|---|---|---|---|---|
| Dependency visibility | Poor. Calls hide in method bodies | Strong. Constructor is the contract | Medium. Factory is visible, products may vary | Strong for one service type | Poor. Import hides lifetime and substitution |
| Missing dependency feedback | Runtime lookup failure | Assembly or compile-time feedback | Assembly-time for factory, runtime for product choice | Runtime discovery failure | Runtime global state failure |
| Test isolation | Weak with global state | Strong with local test doubles | Strong if factory is passed | Medium. Provider metadata may need test setup | Weak. Global replacement leaks |
| Runtime selection | High but broad | Low unless paired with factory | High within a named family | High for one interface | Low |
| Coupling | Consumer couples to locator API | Consumer couples to collaborator interfaces | Consumer couples to a narrow factory | Consumer couples to service interface and discovery API | Consumer couples to concrete global |
| Lifetime control | Easy to misuse | Explicit in composition root | Explicit in factory implementation | Controlled by loader semantics | Often implicit process lifetime |
| Cognitive load | Low at edit time, high during maintenance | Higher upfront, lower later | Medium | Medium | Low upfront, high later |
| Security review | Broad ambient access | Narrow granted access | Narrow family access | Narrow service type access | Broad global access |
| Library portability | Poor if locator API is host-specific | Strong | Strong | Strong where SPI is platform idiom | Poor |

The judgement from the table is direct. Service Locator wins when framework
infrastructure needs late binding across a broad runtime registry. Constructor
Injection wins for ordinary object collaboration. Abstract Factory wins when the
consumer needs runtime creation but the family of possible collaborators is
bounded and named. SPI discovery wins when providers are deployed outside the
application build. Direct Singleton is a worse substitute for almost every
force except small-script convenience.

## 13. Related and incompatible patterns

- **Dependency Injection.** The main replacement. It separates configuration
  from use while keeping the consumer's dependency contract visible.
- **Composition Root.** The proper home for container lookups. A composition
  root may call a container, but objects below it should receive collaborators
  through explicit parameters.
- **Abstract Factory.** A narrow replacement for runtime creation. It keeps the
  "I may need one of these" dependency visible without granting access to every
  registered service.
- **Factory Method.** Often polluted by Service Locator. A factory method that
  reaches into a global locator hides the same dependency it was supposed to
  abstract. The Factory Method entry in this repository names that conflict.
- **Service Provider Interface.** Adjacent but different. SPI discovery locates
  providers for one declared service contract. Service Locator exposes broad
  lookup across unrelated services.
- **Singleton Abuse.** Frequently combined. A static locator is a singleton that
  owns a mutable registry, so it inherits global-state test and lifecycle costs.
- **Facade.** Sometimes confused with it. A Facade presents a purposeful
  operation over a subsystem. A locator returns arbitrary objects and does not
  model a domain action.
- **Explicit Dependencies Principle.** Incompatible as a design norm. A locator
  makes a dependency implicit unless the locator interface is narrowed to the
  exact role the consumer needs, at which point it has become a factory or role
  interface rather than a general locator.

## 14. Refactoring path in and out

Refactoring into the pattern is rarely the goal, but it can be a temporary
migration bridge around a legacy platform lookup.

1. Find the repeated platform lookup code, not ordinary collaborator access.
2. Wrap that platform API in one adapter near the composition root.
3. Give the adapter a small interface for each boundary use rather than a broad
   `get(any)` method if possible.
4. Add logging for misses and duplicate registrations before any caller uses it.
5. Keep new business code from importing the adapter directly. The bridge should
   shrink over time.

Refactoring out is the common path.

1. Inventory locator calls with code search. Group them by consumer class and by
   resolved service.
2. For each consumer, add constructor parameters for the services it always
   needs. Keep the old locator path as a default adapter only if construction
   sites cannot be updated in one commit.
3. Update construction sites at the composition root to pass the dependencies.
   Run tests after each cluster of call sites.
4. Replace lazy lookup with an injected `Lazy<T>`, provider, or typed factory
   only when there is a measured reason to delay construction.
5. For runtime choice, introduce an Abstract Factory or Strategy map with a
   named interface. Do not pass the broad container downward.
6. Delete unused registrations and add a test that builds the production object
   graph.
7. Remove static global access last. A locator with no direct consumers is a
   dead adapter and should be deleted.

During migration, do not try to replace every lookup in one sweep unless the
codebase is small. Start with the classes that have the highest operational
blast radius, such as checkout, billing, authentication, authorization, and
message consumers. These are the places where a missing registration or wrong
lifetime hurts users fastest. Next, migrate shared libraries, because each
hidden locator call there exports the host application's container assumptions
to every caller. Leave low-risk administration scripts and test-only helpers
for last.

One useful intermediate step is a locator facade with one method per remaining
service. That does not finish the repair, but it converts string or type-token
lookups into a searchable interface. After that, each facade method can be
replaced by one constructor parameter in the consumers that call it. This
sequence makes progress visible in code review. The facade should have a
deletion ticket or a failing test that lists remaining consumers, because
otherwise the temporary adapter becomes the new normal.

Named refactorings that apply include Introduce Parameter Object when several
values travel together, Extract Class when a hidden dependency cluster reveals a
separate responsibility, Replace Singleton with Dependency Injection for static
locators, and Replace Conditional with Polymorphism when the locator hides a
manual type switch.

## 15. Testing and verification

Testing code with Service Locator must make hidden dependencies visible.

- Add a characterization test before migration that configures the locator the
  same way production does and exercises the consumer path. This protects the
  behavior while dependencies are moved into the constructor.
- Add a test that builds the production object graph without serving a request.
  The goal is to catch missing registrations at startup rather than in a method
  body.
- For a remaining scoped locator, test that each scope receives its own scoped
  dependency and that no singleton stores it after the scope ends.
- For a string-keyed locator, test every key in one table-driven suite. Include
  duplicate key behavior and missing key behavior.
- Prefer handwritten fakes passed to constructors over mutating locator state.
  That keeps tests parallel-safe and local.
- When a locator must remain for a legacy framework callback, wrap it in a thin
  adapter and test the adapter separately from the domain object it creates.

The pattern makes one thing easier to test: the registry itself can be tested as
a map from keys to providers. It makes consumer tests harder because every
consumer's dependency list must be reconstructed by reading implementation code.
That is the reason tests should drive migration toward explicit parameters.

## 16. Observability signals

This dimension is engineering judgement.

Instrument remaining locators as infrastructure, because otherwise they hide
too much of the runtime graph.

- Count lookups by consumer, key, scope, and outcome. Outcome should include
  hit, miss, wrong type, duplicate registration, and disposed scope.
- Record lookup failures with the consumer class and key. A missing key without
  a consumer field sends responders back to code search.
- Emit a startup inventory of registered keys and lifetimes. Redact values.
- Track late first lookup time. A service first resolved minutes after startup
  is a candidate for a hidden branch that object graph validation did not cover.
- Track singleton-to-scoped resolution attempts if the container exposes that
  signal.
- For tests, fail on leaked registrations after each test case where possible.

A healthy remaining locator has low lookup variety, almost all lookups happen at
startup or at clear framework boundaries, duplicate registration count is zero,
and runtime misses are zero. A failing locator shows misses during request
handling, lookup keys that grow across releases, or consumers resolving many
unrelated services from the same broad container.

An especially useful dashboard is a top-N table of consumers by distinct lookup
keys. A composition root may appear near the top, and that is expected. A domain
service, controller, presenter, job handler, or entity callback near the top is
repair work waiting to happen. Another useful graph is "first lookup after
startup" grouped by key. A service first looked up during a rare incident path
is exactly the kind of hidden precondition that constructor injection would have
made visible earlier.

## 17. Security and privacy implications

Service Locator can widen access. A constructor parameter grants a consumer one
capability: this repository, this gateway, this clock. A broad locator grants
the consumer the ability to ask for any service that the locator can return. In
trusted application code that may be a maintainability issue rather than an
attack. In plugin, script, template, or extension code, it becomes a privilege
boundary issue.

Security review should ask four questions. Can untrusted code obtain the
locator? Can it enumerate keys? Can it resolve services that carry secrets,
network clients, filesystem access, database handles, or tenant context? Can it
replace registrations? If any answer is yes, the locator is part of the attack
surface and should be narrowed to a role interface or moved behind an allowlist.

Privacy risks appear when request or tenant data is put into the container as if
it were a service. A locator lookup then becomes a hidden data-flow edge. Logs
that include locator keys may also reveal tenant names, region names, feature
names, or provider names if those are encoded into keys. Treat locator telemetry
as operational metadata that can still carry sensitive business meaning.

The pattern is silent on cryptography, authentication, and transport security.
It neither encrypts data nor exposes a network port by itself. Its real security
effect is capability spread through ambient access.

## Code examples

The examples are intentionally small and runnable. They show the antipattern and
the replacement. TypeScript, Python, and Rust were chosen because a registry can
be expressed in each without framework scaffolding.

### TypeScript

```typescript
type Token<T> = string & { readonly type?: T };

class Locator {
  private services = new Map<string, unknown>();

  register<T>(token: Token<T>, service: T): void {
    this.services.set(token, service);
  }

  get<T>(token: Token<T>): T {
    const found = this.services.get(token);
    if (found === undefined) {
      throw new Error(`missing service ${token}`);
    }
    return found as T;
  }
}

interface Gateway {
  charge(cents: number): string;
}

const gatewayToken = "gateway" as Token<Gateway>;

class CheckoutWithLocator {
  constructor(private readonly locator: Locator) {}

  pay(cents: number): string {
    const gateway = this.locator.get(gatewayToken);
    return gateway.charge(cents);
  }
}

class CheckoutExplicit {
  constructor(private readonly gateway: Gateway) {}

  pay(cents: number): string {
    return this.gateway.charge(cents);
  }
}

const gateway: Gateway = { charge: (cents) => `charged ${cents}` };
const locator = new Locator();
locator.register(gatewayToken, gateway);

console.log(new CheckoutWithLocator(locator).pay(1200));
console.log(new CheckoutExplicit(gateway).pay(1200));
```

### Python

```python
from typing import Protocol, TypeVar


T = TypeVar("T")


class Locator:
    def __init__(self) -> None:
        self._services: dict[type[object], object] = {}

    def register(self, key: type[T], service: T) -> None:
        self._services[key] = service

    def get(self, key: type[T]) -> T:
        try:
            return self._services[key]  # type: ignore[return-value]
        except KeyError as exc:
            raise LookupError(f"missing service {key.__name__}") from exc


class Gateway(Protocol):
    def charge(self, cents: int) -> str: ...


class StripeGateway:
    def charge(self, cents: int) -> str:
        return f"charged {cents}"


class CheckoutWithLocator:
    def __init__(self, locator: Locator) -> None:
        self.locator = locator

    def pay(self, cents: int) -> str:
        gateway = self.locator.get(StripeGateway)
        return gateway.charge(cents)


class CheckoutExplicit:
    def __init__(self, gateway: Gateway) -> None:
        self.gateway = gateway

    def pay(self, cents: int) -> str:
        return self.gateway.charge(cents)


if __name__ == "__main__":
    locator = Locator()
    gateway = StripeGateway()
    locator.register(StripeGateway, gateway)
    print(CheckoutWithLocator(locator).pay(1200))
    print(CheckoutExplicit(gateway).pay(1200))
```

### Rust

```rust
use std::any::{Any, TypeId};
use std::collections::HashMap;
use std::sync::Arc;

trait Gateway: Send + Sync {
    fn charge(&self, cents: u64) -> String;
}

struct StripeGateway;

impl Gateway for StripeGateway {
    fn charge(&self, cents: u64) -> String {
        format!("charged {cents}")
    }
}

struct Locator {
    services: HashMap<TypeId, Arc<dyn Any + Send + Sync>>,
}

impl Locator {
    fn new() -> Self {
        Self { services: HashMap::new() }
    }

    fn register<T: Any + Send + Sync>(&mut self, service: Arc<T>) {
        self.services.insert(TypeId::of::<T>(), service);
    }

    fn get<T: Any + Send + Sync>(&self) -> Result<Arc<T>, String> {
        let found = self
            .services
            .get(&TypeId::of::<T>())
            .ok_or_else(|| "missing service".to_string())?;
        Arc::clone(found)
            .downcast::<T>()
            .map_err(|_| "wrong service type".to_string())
    }
}

fn checkout_with_locator(locator: &Locator, cents: u64) -> Result<String, String> {
    let gateway = locator.get::<StripeGateway>()?;
    Ok(gateway.charge(cents))
}

fn checkout_explicit(gateway: &dyn Gateway, cents: u64) -> String {
    gateway.charge(cents)
}

fn main() {
    let gateway = Arc::new(StripeGateway);
    let mut locator = Locator::new();
    locator.register(Arc::clone(&gateway));

    println!("{}", checkout_with_locator(&locator, 1200).unwrap());
    println!("{}", checkout_explicit(gateway.as_ref(), 1200));
}
```

## 18. References

1. Deepak Alur, John Crupi, Dan Malks. *Core J2EE Patterns. Best Practices and
   Design Strategies*. Prentice Hall, 1st edition, 2001. Chapter 8, "Service
   Locator". Source for the original J2EE lineage.
2. Martin Fowler. "Inversion of Control Containers and the Dependency Injection
   pattern", sections "Using a Service Locator" and "Service Locator vs
   Dependency Injection". https://martinfowler.com/articles/injection.html
   Verified 2026-08-02.
3. Mark Seemann. "Service Locator is an Anti-Pattern".
   https://blog.ploeh.dk/2010/02/03/ServiceLocatorisanAnti-Pattern/
   Verified 2026-08-02.
4. Steven van Deursen, Mark Seemann. *Dependency Injection Principles,
   Practices, and Patterns*. Manning, 2019. Chapter 5, anti-patterns. Manning
   excerpt, "The Service Locator Anti-Pattern".
   https://freecontent.manning.com/the-service-locator-anti-pattern/
   Verified 2026-08-02.
5. Microsoft. ".NET dependency injection guidelines", section
   "Recommendations".
   https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/guidelines
   Verified 2026-08-02.
6. Microsoft. "Dependency injection in ASP.NET Core", section
   "Request Services".
   https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection
   Verified 2026-08-02.
7. Microsoft. `Microsoft.AspNetCore.Http.HttpContext.RequestServices` API.
   https://learn.microsoft.com/en-us/dotnet/api/microsoft.aspnetcore.http.httpcontext.requestservices
   Verified 2026-08-02.
8. Spring Framework Reference. "Container Overview", section
   "Using the Container".
   https://docs.spring.io/spring-framework/reference/core/beans/basics.html
   Verified 2026-08-02.
9. Angular. `Injector` API reference.
   https://angular.dev/api/core/Injector
   Verified 2026-08-02.
10. Oracle. Java SE 17 API Specification, `java.util.ServiceLoader`.
    https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ServiceLoader.html
    Verified 2026-08-02.
11. Laravel. "Service Container", section "Resolving".
    https://laravel.com/docs/10.x/container
    Verified 2026-08-02.
