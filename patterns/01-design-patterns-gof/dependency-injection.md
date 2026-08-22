---
name: Dependency Injection
slug: dependency-injection
family: 01-design-patterns-gof
category: Structural
aliases: [DI, Constructor Injection, Setter Injection, Interface Injection, IoC Container Injection]
first_described: "Martin Fowler, Inversion of Control Containers and the Dependency Injection pattern, martinfowler.com, January 2004, which coined and popularized the specific term Dependency Injection as a more precise replacement for the vaguer, older term Inversion of Control. The underlying practice predates the essay, visible in the PicoContainer and Spring frameworks Fowler cites as already active projects at the time of writing, and the closely related design principle it most often serves, the Dependency Inversion Principle, was published by Robert C. Martin in The C++ Report in 1996, eight years earlier"
maturity: canonical
related: [factory-method, abstract-factory, strategy, inversion-of-control]
verified: 2026-08-23
---

# Dependency Injection

## 1. Name, aliases, and lineage

Dependency Injection is not one of the original twenty three Gang of Four patterns, but it sits inside this family because it is the direct descendant of the same object oriented design tradition, and because it is one of the most consequential patterns to enter the vocabulary since 1994. Its name and its precise modern definition come from a single, dateable source, Martin Fowler's essay Inversion of Control Containers and the Dependency Injection pattern, published on martinfowler.com in January 2004.

Fowler wrote the essay specifically to fix a vocabulary problem. Frameworks of the time, PicoContainer and Spring among them, were marketing themselves around the older, vaguer term Inversion of Control, and Fowler found the label unhelpfully generic, writing that "inversion of control is a common characteristic of frameworks, so saying that these lightweight containers are special because they use inversion of control is like saying my car is special because it has wheels" (Martin Fowler, Inversion of Control Containers and the Dependency Injection pattern, martinfowler.com, January 2004, https://martinfowler.com/articles/injection.html, verified 2026-08-23). His own account of the rename is that it was a collective decision, not a solo coinage, "as a result with a lot of discussion with various IoC advocates we settled on the name Dependency Injection."

The same essay names the three classic forms the technique takes. Constructor Injection, demonstrated in the essay via PicoContainer, hands the dependency to the client as a constructor argument at the moment of construction. Setter Injection, demonstrated via Spring, constructs the client with a no argument constructor and then calls a setter method to supply the dependency afterward. Interface Injection has the client implement a defined injection interface that the assembler calls to hand over the dependency, the least adopted of the three in the frameworks that followed.

The underlying practice is older than the name. Fowler's own essay treats PicoContainer as an already active project at the time of writing, noting that "several of my colleagues at Thoughtworks are very active in the development of PicoContainer," and treats Spring as an established framework with its own existing developer preference for setter injection, both signs the practice predates the essay that named it, even where an exact founding date for either project could not be independently confirmed here.

The technique is frequently confused with a related but distinct design principle, the Dependency Inversion Principle, the D in SOLID, published by Robert C. Martin in The C++ Report in 1996, eight years before Fowler's essay. Martin's own definition, quoted directly from the original paper, states that "high level modules should not depend upon low level modules, both should depend upon abstractions," and that "abstractions should not depend upon details, details should depend upon abstractions" (Robert C. Martin, The Dependency Inversion Principle, The C++ Report, 1996, https://condor.depaul.edu/dmumaugh/OOT/Design-Principles/dip.pdf, verified 2026-08-23). The precise, sourced distinction is this. the 1996 paper never once uses the word inject or injection, and its own worked example, a Button class taking a ButtonClient reference through its constructor, is textbook Constructor Injection in Fowler's later vocabulary, described by Martin only as isolating an abstraction from its detail. Dependency Inversion is the older, higher level design principle about depending on abstractions rather than concretions. Dependency Injection is the newer, lower level implementation technique, one of several ways, alongside Service Locator, to satisfy that principle at runtime. Wikipedia's own summary of the principle corroborates this framing directly, stating that "plugin, Service Locator, or Dependency injection are employed to facilitate the run time provisioning of the chosen low level component implementation to the high level component" (Dependency inversion principle, Wikipedia, https://en.wikipedia.org/wiki/Dependency_inversion_principle, verified 2026-08-23).

## 2. Problem and context

Fowler's own running example names the problem precisely. a MovieLister class needs a MovieFinder to look up movies, and "the problem is how can I make that link so that my lister class is ignorant of the implementation class, but can still talk to an instance to do its work" (Martin Fowler, martinfowler.com, verified 2026-08-23). The two competing paths are the ones this pattern always balances. the client constructs or looks up its own collaborator directly, coupling it to a concrete implementation, or a third party hands the client its collaborator from outside, leaving the client aware only of an abstraction.

Testability is the reason most commonly given for preferring the second path, and Fowler's own treatment of that reason is more careful than the common retelling. He writes that "a common reason people give for preferring dependency injection is that it makes testing easier," but immediately qualifies it, "there is really no difference here between dependency injection and service locator, both are very amenable to stubbing," adding that the belief DI is uniquely testable usually comes from projects where the team never made the effort to keep their service locator easily substitutable in the first place (Martin Fowler, martinfowler.com, verified 2026-08-23). Microsoft's own ASP.NET Core documentation states the practical consequence of NOT following either path plainly, that constructing a dependency directly inside a class means "the implementation is difficult to unit test" and any change to a dependency propagates through every class that constructs it by hand (Microsoft Learn, Dependency injection in ASP.NET Core, https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection, verified 2026-08-23).

## 3. Forces

Coupling versus discoverability is the first and most persistent tension. Injecting a dependency reduces coupling to a concrete implementation, but Mark Seemann, author of Dependency Injection in .NET, names the cost directly when contrasting manual wiring against a container, describing manual, container free Dependency Injection as giving "the fastest feedback about correctness that you can get" precisely because "there is no magical behavior" hiding how a class was actually wired (Mark Seemann, When to use a DI Container, blog.ploeh.dk, 2012-11-06, https://blog.ploeh.dk/2012/11/06/WhentouseaDIContainer/, verified 2026-08-23).

Container magic versus explicitness is the second. Seemann's own later post coined a term for the manual alternative, writing that "Pure DI is when you use the DI principles and patterns, but not a DI Container," and that manual wiring is, in his own words, "in many cases, better than DI with a DI Container" (Mark Seemann, Pure DI, blog.ploeh.dk, 2014-06-10, https://blog.ploeh.dk/2014/06/10/pure-di/, verified 2026-08-23), a direct rejection of the assumption that an automated container is always the more mature choice.

Startup performance is the third force, and it is the specific reason Dagger, the compile time DI framework for Java, Kotlin, and Android, exists at all. Dagger's own documentation states its guiding principle is to generate code that mimics what a developer would have hand written, so dependency injection stays "as simple, traceable and performant as it can be," positioned explicitly to "address many of the development and performance issues that have plagued reflection based solutions" (Dagger Developer Guide, https://dagger.dev/dev-guide/, verified 2026-08-23). Android's own developer documentation is more concrete about the mechanism, that Dagger's compile time approach means dependency graphs are validated at build time so "there are no runtime exceptions" and "no dependency cycles exist, so there are no infinite loops" (Dagger basics, Android Developers, https://developer.android.com/training/dependency-injection/dagger-basics, verified 2026-08-23), a benefit reflection based containers cannot offer until the application actually runs.

## 4. Applicability and non-applicability

The pattern earns its place wherever a class has a genuine need for substitutable implementations, a real test double in place of a real collaborator, or an architectural layer that should stay ignorant of a concrete type. Fowler's own essay, and every framework surveyed in section 9, treats this as the default case worth solving for.

It is overkill where none of those needs are real, and Fowler says so about his own pattern directly. He writes plainly that the inversion of control a container provides "comes at a price, it tends to be hard to understand and leads to problems when you are trying to debug," concluding "so on the whole I prefer to avoid it unless I need it" (Martin Fowler, martinfowler.com, verified 2026-08-23). In a smaller scenario he walks through in the same essay, a case where a caller simply wants to choose which finder implementation to use without a full plugin architecture, he states outright, "in this kind of scenario I don't see the injector's inversion as providing anything compelling." Seemann's Pure DI reasoning reaches the same conclusion from the container side specifically, that a container's convention based wiring pays for itself only at a scale where hand written wiring becomes unwieldy, and a small script or a class with no meaningful alternate implementation is simpler served by a direct constructor call.

## 5. Structure

Service, also called Dependency, is the object being depended upon, declared as an interface or abstraction rather than a concrete type. In Fowler's own running example this is the MovieFinder interface, chosen specifically so that swapping an implementation never touches the class that uses it.

Client, also called Consumer or Dependent, is the object that needs the Service to do its work while staying ignorant of which concrete implementation it received. Fowler's own MovieLister plays this role, and his stated goal for it is that it stays "ignorant of the implementation class" it is handed (Martin Fowler, martinfowler.com, verified 2026-08-23).

Injector, also called Assembler, Container, or Provider, is the third party responsible for constructing the Service and handing it to the Client. Fowler's own term for this role is "a separate object, an assembler, that populates a field in the lister class with an appropriate implementation."

Interface or Abstraction is the contract the Client depends on instead of a concrete implementation, the structural link back to the Dependency Inversion Principle from section 1. Fowler notes that because the essay's example defines a MovieFinder interface, "this won't alter my moviesDirectedBy method" when the concrete implementation changes underneath it.

Constructor Injection, Setter Injection, and Interface Injection, the three forms named in section 1, are structural mechanisms in their own right, the concrete means by which the Injector actually hands the Service to the Client. Spring's own documentation states a clear preference among the first two, that "the Spring team generally advocates constructor injection, as it lets you implement application components as immutable objects" whose required dependencies are guaranteed never to be null, reserving setter injection "primarily only... for optional dependencies that can be assigned reasonable default values" (Spring Framework Documentation, Dependency Injection, https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html, verified 2026-08-23).

## 6. ASCII structure diagram

```
  WITH DEPENDENCY INJECTION              WITHOUT INJECTION (tight coupling)
  --------------------------             ----------------------------------

  +-------------------+                  +-------------------------+
  |     Injector        |                 |      OrderService         |
  |  (Container /        |                |                            |
  |   Assembler)          |               |  constructor() {           |
  +----------+-----------+                |    this.gateway =          |
             |                            |      new                    |
             | 1. constructs               |      ConcretePaymentGateway|
             |    ConcretePaymentGateway    |      ();                   |
             v                            |  }                          |
  +----------------------------+           |                            |
  | ConcretePaymentGateway       |          |  Knows the CONCRETE class  |
  | implements PaymentGateway    |          |  directly. Cannot be       |
  +----------------------------+           |  swapped without editing   |
             |                            |  this file.                 |
             | 2. injects it into          +--------------+-------------+
             |    the constructor                        |
             v                                            v
  +----------------------------+           +----------------------------+
  |       OrderService           |          |   ConcretePaymentGateway     |
  |                               |          |   (hard wired, no interface  |
  |  constructor(                |          |    needed)                   |
  |    PaymentGateway gateway)    |          +----------------------------+
  |  { this.gateway = gateway; }  |
  |                               |
  |  Knows only the ABSTRACTION.  |
  |  The Injector decided WHICH   |
  |  concrete class to use.       |
  +---------------+---------------+
                  |
                  | depends on (interface)
                  v
  +----------------------------+
  |   <<interface>>               |
  |   PaymentGateway               |
  +----------------------------+
                  ^
                  | implements
                  |
  +----------------------------+
  |  ConcretePaymentGateway       |
  +----------------------------+

  For a test, the Injector could instead construct a FakePaymentGateway,
  also implementing PaymentGateway, and hand THAT to OrderService.
  OrderService's own code never changes.
```

## 7. Dynamics

```
1  Application start (or test setup) begins.
2  The Injector determines which concrete Service implementation
   the current context needs (e.g. ConcretePaymentGateway in
   production, FakePaymentGateway in a test).
3  The Injector constructs that Service.
4  The Injector constructs the Client, passing the Service in
   through the constructor (Constructor Injection), OR
4b The Injector constructs the Client with a no-argument
   constructor, then calls a setter to hand over the Service
   (Setter Injection).
5  The Client is now fully wired and never itself decided which
   concrete Service it received.

At runtime, when the Client needs the Service's behavior:
6  The Client calls a method on the Service through the interface
   it depends on, with no knowledge of the concrete type behind it.
7  The Service performs the real work (or, in a test, the fake
   returns a controlled result the test set up in advance).

If the container is reflection-based (Spring, Guice):
8a Wiring mistakes (a missing dependency, a circular reference
   between two beans) surface as an exception at container
   load-time, when the application actually starts.

If the container is compile-time (Dagger):
8b The identical class of mistake is caught as a build failure,
   before the application ever runs, because the dependency graph
   is validated and code-generated at compile time.
```

## 8. Implementation variants

Reflection-based containers wire dependencies at runtime by inspecting annotations and constructor signatures. Spring's own documentation for annotation-driven wiring names the mechanism directly, that Spring registers a set of `BeanPostProcessors`, including `AutowiredAnnotationBeanPostProcessor`, that inspect annotated fields, methods, and constructors "to make the core IOC container aware of specific annotations" (Spring Framework Documentation, Annotation-based Container Configuration, https://docs.spring.io/spring-framework/reference/core/beans/annotation-config.html, verified 2026-08-23). Google Guice takes the same reflection-based approach for Java, inspecting an `@Inject`-annotated constructor at runtime and looking up a value for each parameter.

Compile-time or code-generation-based DI avoids reflection entirely by generating the wiring code ahead of time. Dagger is the clearest example, described in Android's own documentation as walking the code "at build time" to validate the dependency graph and generate the classes used to construct objects at runtime (Dagger basics, Android Developers, verified 2026-08-23). The same idea appears outside the JVM. Rust's shaku crate describes itself as "a compile time dependency injection library," where "by implementing traits such as HasComponent on a module, service dependencies are checked at compile time" (shaku documentation, docs.rs, https://docs.rs/shaku/latest/shaku/, verified 2026-08-23). Go took a different path. Google's own Wire tool is "a code generation tool that automates connecting components using dependency injection," built explicitly so it "operates without runtime state or reflection" (Wire, GitHub, https://github.com/google/wire, verified 2026-08-23), though Wire's own README now carries a maintenance notice that the project is no longer actively developed, itself evidence that Go's broader community culture leans toward fully manual constructor wiring over any DI framework, compile-time or otherwise.

Service Locator is a related but explicitly different alternative, and Fowler's own essay compares the two directly rather than treating Service Locator as simply inferior. His mechanical distinction is precise, "with service locator the application class asks for it explicitly by a message to the locator, with injection there is no explicit request, the service appears in the application class, hence the inversion of control" (Martin Fowler, martinfowler.com, verified 2026-08-23). His stated preference is more nuanced than a blanket rule, he favors avoiding the added indirection of either pattern unless he needs it, but singles out one case where Dependency Injection specifically wins, "if you are building classes to be used in multiple applications then Dependency Injection is a better choice," because "you can just look at the injection mechanism, such as the constructor, and see the dependencies."

## 9. Known production uses

Spring Framework and Spring Boot define dependency injection in their own documentation in terms nearly identical to Fowler's essay, stating that "objects define their dependencies... only through constructor arguments, arguments to a factory method, or properties," and that "the container then injects those dependencies when it creates the bean," explicitly naming the mechanism "the inverse... of the bean itself controlling the instantiation or location of its dependencies" (Spring Framework Documentation, Dependency Injection, verified 2026-08-23).

ASP.NET Core states in its own documentation that it "supports the dependency injection (DI) software design pattern, which is a technique for achieving Inversion of Control (IoC) between classes and their dependencies," and explicitly recommends against the Service Locator alternative, advising developers to "prefer requesting dependencies as constructor parameters over resolving services from RequestServices" (Microsoft Learn, Dependency injection in ASP.NET Core, verified 2026-08-23).

Angular's own documentation defines it in near identical language to Fowler's original coinage, "Dependency Injection (DI) is a design pattern you use to organize and share code across your application by supplying dependencies to a class instead of creating them inside it" (Angular Documentation, Dependency injection, https://angular.dev/guide/di, verified 2026-08-23).

Google Guice frames the pattern's testability benefit in stronger, more affirmative terms than Fowler's own careful hedging in section 2, stating "whenever we add or remove dependencies, the compiler will remind us what tests need to be fixed, the dependency is exposed in the API signature" (Guice Motivation, GitHub Wiki, https://github.com/google/guice/wiki/Motivation, verified 2026-08-23).

NestJS states plainly that "Nest is built around the powerful design pattern known as Dependency Injection," implemented through a "built-in inversion of control (IoC) container that manages the relationships between providers," where an `@Injectable()` decorator "signals that a class... can be managed by the Nest container" (NestJS Documentation, Providers, https://docs.nestjs.com/providers, verified 2026-08-23).

Every framework surveyed here uses the exact phrase Dependency Injection in its own official documentation, direct, current, live confirmation of how completely Fowler's 2004 coinage was adopted across the industry, independent of language or ecosystem.

## 10. Consequences

Positive. A Client stays ignorant of the concrete type it depends on, letting a real implementation and a test double be swapped with zero change to the Client's own code. Every framework surveyed in section 9 treats this as the default architectural posture rather than an opt-in extra. Constructor Injection specifically, Spring's own preferred form, produces immutable objects whose required dependencies can never be null, per Spring's own documented rationale. A compile-time implementation like Dagger turns a whole class of wiring mistakes into a build failure instead of a runtime one, moving the feedback loop as early as it can go.

Negative. Fowler's own words carry the clearest statement of the cost, the inversion of control a container provides "tends to be hard to understand and leads to problems when you are trying to debug." A reflection-based container hides the actual wiring decision somewhere outside the Client's own source, the discoverability cost Seemann names directly when he calls manual DI "strongly typed" and a container "weakly typed" in comparison. Reflection itself carries a measurable startup and memory cost relative to compile-time generation, the entire stated rationale behind Dagger, Micronaut, and Quarkus existing as separate projects rather than everyone simply using Spring.

## 11. Failure modes and misuse

Constructor over-injection is the most commonly named misuse, and Mark Seemann is precise about what it actually signals, "Constructor Over-injection is a code smell, not an anti-pattern," and specifically "a symptom that a class is doing too much, that it's violating the Single Responsibility Principle" (Mark Seemann, On Constructor Over-injection, blog.ploeh.dk, 2018-08-27, https://blog.ploeh.dk/2018/08/27/on-constructor-over-injection/, verified 2026-08-23). The observable symptom is a constructor whose parameter list keeps growing, and the fix Seemann names is not abandoning Constructor Injection, it is splitting the class.

Circular dependencies are the most common reflection-based wiring failure, and Spring's own documentation states the exact failure mode by name, "if you configure beans for classes A and B to be injected into each other, the Spring IoC container detects this circular reference at runtime, and throws a BeanCurrentlyInCreationException" (Spring Framework Documentation, Dependency Injection, verified 2026-08-23). Spring's own recommended fix is to break the cycle by moving one side from constructor injection to setter injection, though the same documentation calls this a workaround rather than a preferred design, "although it is not recommended, you can configure circular dependencies with setter injection."

Over-mocking is a documented risk on the testing side, where DI's own ease of substitution is used to replace so many real collaborators that a test no longer exercises any genuine logic. Fowler's own writing on mock-based testing warns that "expectations on mockist tests can be incorrect, resulting in unit tests that run green but mask inherent errors" (Martin Fowler, Mocks Aren't Stubs, martinfowler.com, https://martinfowler.com/articles/mocksArentStubs.html, verified 2026-08-23), and a more pointed, contested critique from Ruby on Rails creator David Heinemeier Hansson argues some architectural abstraction is introduced purely to make mocking convenient rather than because the design calls for it, describing this as "test-induced design damage" (David Heinemeier Hansson, Test-induced design damage, dhh.dk, 2014, https://dhh.dk/2014/test-induced-design-damage.html, verified 2026-08-23), a genuinely contested position worth presenting as a named counter-viewpoint rather than settled consensus.

Treating Dependency Injection as automatically more testable than Service Locator, without doing the same work to make a locator substitutable, is the misuse Fowler himself calls out directly in section 2, the naive belief collapses under his own scrutiny once a locator is built to be equally substitutable.

## 12. Trade-off matrix

| Force | Dependency Injection | Service Locator | Direct construction (new) |
|---|---|---|---|
| Coupling to concrete type | None, Client depends only on an interface | None, but Client is coupled to the locator itself | Full, Client names the concrete class directly |
| Discoverability of wiring | Constructor signature shows every dependency at a glance | Hidden behind whatever the locator call resolves at runtime | Fully visible, no indirection to trace at all |
| Testability | High, when the container or manual wiring substitutes a test double | Equally high, per Fowler, if the locator itself is built to be substitutable | Low, a hard-coded concrete type cannot be swapped without editing the class |
| Startup cost | Reflection-based containers add measurable startup and memory overhead, compile-time containers add none | Similar to a reflection-based container if resolution happens via reflection | None, no container or graph to resolve |
| Best fit | A class built for reuse across multiple applications, or a project already at a scale where manual wiring is unwieldy | A single application where a well-built locator is already in place | A small script, or a class with no meaningful alternate implementation |

## 13. Related and incompatible patterns

Factory Method and Abstract Factory, two classic Gang of Four patterns in this same family, solve an adjacent problem, deciding which concrete class to instantiate, by hand-writing a dedicated factory class. A DI container can be understood as a generalized, configuration-driven version of the same idea, resolving an entire object graph declaratively rather than through a purpose-built factory for each type, though this comparison is offered here as the reasoned architectural relationship between the two rather than a claim traceable to a single source stating it explicitly.

Strategy, another classic Gang of Four pattern in this family, shares Dependency Injection's core mechanism at the structural level, a client receiving an interchangeable implementation of an interface from outside rather than choosing it internally. The distinction commonly drawn is one of intent and scope rather than mechanism, Strategy is usually framed around swapping one runtime-interchangeable algorithm, often via a setter the client itself calls, while Dependency Injection is framed as the broader, often container-managed practice of wiring an object's entire dependency graph, typically once at construction time.

Inversion of Control is the older, broader principle Dependency Injection is one concrete technique for satisfying, alongside Service Locator, the Plugin pattern, and event-driven callback registration. Fowler's own essay is explicit that the container's use of inversion of control is not itself the special or novel part, "a common characteristic of frameworks" generally, and that Dependency Injection is the name for the specific, more precise technique within that broader family.

Incompatible with, or a poor match for, a class or module with no genuine need for a substitutable implementation and no meaningful testing burden, where the added indirection buys nothing beyond what Fowler himself, in his own words, calls a price paid for a benefit that was never needed.

## 14. Refactoring path in and out

Refactoring in starts by identifying a class that constructs its own collaborator directly, then extracting the collaborator's type into an interface the class depends on instead of the concrete class. The construction of the real implementation moves out of the class and into a caller, a factory, or a container, and is handed in through the constructor wherever possible, per Spring's own stated preference for Constructor Injection over Setter Injection, since a constructor argument makes a required dependency impossible to forget. A container is introduced only once the number of collaborators being wired by hand becomes genuinely unwieldy, following Seemann's own Pure DI guidance that manual wiring is often the better choice at smaller scale.

Refactoring out applies when a class's dependencies were never genuinely substitutable in practice, no test double was ever needed, and no second implementation was ever written. At that point the interface and the injection point add indirection with no offsetting benefit, and collapsing back to a direct constructor call inside the class, per Fowler's own admission that he prefers to avoid the pattern when it "doesn't provide anything compelling," is the correct direction to move.

## 15. Testing and verification

Dependency Injection's most direct testing benefit is substitution, a test constructs the Client with a mock, stub, or fake Service injected in place of the real one. Mockito's own documentation names the mechanism plainly through its `@InjectMocks` annotation, which automatically wires fields annotated `@Mock` or `@Spy` into the class under test (Mockito, site.mockito.org, https://site.mockito.org/, verified 2026-08-23), letting a test control the Service's behavior or assert on how the Client interacted with it, without needing the real implementation at all.

The container's own wiring is verified with a different technique, loading the real application context in a test to catch a broken graph early rather than discovering it in production. Spring Boot's own documentation describes `@SpringBootTest` as bootstrapping the same `ApplicationContext` the running application would use, "creating the ApplicationContext used in your tests through SpringApplication" (Spring Boot Documentation, Testing Spring Boot Applications, https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html, verified 2026-08-23), and Spring's own reference documentation confirms wiring problems surface at this point, "Spring detects configuration problems, such as references to non-existent beans and circular dependencies, at container load-time" (Spring Framework Documentation, Dependency Injection, verified 2026-08-23).

Over-mocking, covered as a failure mode in section 11, is also a testing-specific risk worth naming here directly, a test built around so many substituted dependencies that it stops exercising any real logic, becoming brittle without becoming meaningful, the concern both Fowler's own writing on mockist testing and DHH's more pointed critique raise from different angles.

## 16. Observability signals

Spring Boot Actuator's beans endpoint is the clearest, most directly documented way to introspect a running container's wiring, described in Spring's own documentation as displaying "a complete list of all the Spring beans in your application," exposed by default over HTTP at `/actuator/beans` (Spring Boot Documentation, Actuator Endpoints, https://docs.spring.io/spring-boot/reference/actuator/endpoints.html, verified 2026-08-23), letting an operator see exactly what got wired into what without reading source code.

Circular dependency errors are the most common wiring failure to watch for, and Spring names the exact exception class to look for in logs, `BeanCurrentlyInCreationException`, thrown at container load-time per section 11.

The clearest structural observability difference between implementation variants is when a wiring mistake becomes visible at all. A reflection-based container like Spring or Guice surfaces a broken graph only when the application actually starts, per Spring's own "at container load-time" language. A compile-time system like Dagger surfaces the identical class of mistake as a build failure, before the application ever runs, per Android's own documentation that dependency graphs are validated so "there are no runtime exceptions." This is a genuine, sourced difference in feedback loop length between the two families of implementation, not merely a matter of taste.

## 17. Security and privacy implications

The dependency injection mechanism itself, the code that resolves and wires an interface to a concrete implementation, shows a clean security record across the major frameworks checked directly. GitHub's own Security Advisories pages for Google Guice, Google Dagger, and the Spring Framework repository each report no published advisories against those repositories (GitHub Security Advisories, google/guice, https://github.com/google/guice/security/advisories, verified 2026-08-23, google/dagger, https://github.com/google/dagger/security/advisories, verified 2026-08-23, and spring-projects/spring-framework, https://github.com/spring-projects/spring-framework/security/advisories, verified 2026-08-23).

Spring's own most famous security incident, widely discussed alongside its dependency injection mechanism, is CVE-2022-22965, known as Spring4Shell, and precision matters here. the vulnerability sits in Spring MVC and Spring WebFlux's data binding subsystem, "a Spring MVC or Spring WebFlux application running on JDK 9 or later may be vulnerable to remote code execution via data binding" (GitHub Security Advisory GHSA-36p3-wjmg-h94x, Remote Code Execution in Spring Framework, https://github.com/advisories/GHSA-36p3-wjmg-h94x, verified 2026-08-23), not in the IoC container's own bean-wiring mechanism described throughout this entry. Conflating the two overstates the finding, the core dependency injection machinery was not the vulnerable component in that incident.

Where a DI container's configuration source, an XML file, an annotation, or a property driving which bean gets selected, is itself attacker-influenced or untrusted, the container will faithfully wire in whatever it is told to construct, a structural, reasoned observation rather than a claim traceable to any single named source or documented incident found during this entry's research, and it is stated here with that honest caveat rather than as settled fact.

## 18. References

1. Martin Fowler, Inversion of Control Containers and the Dependency Injection pattern, martinfowler.com, January 2004, https://martinfowler.com/articles/injection.html, verified 2026-08-23.
2. Robert C. Martin, The Dependency Inversion Principle, The C++ Report, 1996, https://condor.depaul.edu/dmumaugh/OOT/Design-Principles/dip.pdf, verified 2026-08-23.
3. Dependency inversion principle, Wikipedia, https://en.wikipedia.org/wiki/Dependency_inversion_principle, verified 2026-08-23.
4. Spring Framework Documentation, Dependency Injection, https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html, verified 2026-08-23.
5. Spring Framework Documentation, Annotation-based Container Configuration, https://docs.spring.io/spring-framework/reference/core/beans/annotation-config.html, verified 2026-08-23.
6. Microsoft Learn, Dependency injection in ASP.NET Core, https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection, verified 2026-08-23.
7. Angular Documentation, Dependency injection, https://angular.dev/guide/di, verified 2026-08-23.
8. Guice Motivation, GitHub Wiki, https://github.com/google/guice/wiki/Motivation, verified 2026-08-23.
9. Dagger Developer Guide, https://dagger.dev/dev-guide/, verified 2026-08-23.
10. Dagger basics, Android Developers, https://developer.android.com/training/dependency-injection/dagger-basics, verified 2026-08-23.
11. NestJS Documentation, Providers, https://docs.nestjs.com/providers, verified 2026-08-23.
12. Wire, GitHub repository, https://github.com/google/wire, verified 2026-08-23.
13. shaku documentation, docs.rs, https://docs.rs/shaku/latest/shaku/, verified 2026-08-23.
14. Micronaut Framework User Guide, https://docs.micronaut.io/latest/guide/, verified 2026-08-23.
15. Quarkus, Contexts and Dependency Injection, https://quarkus.io/guides/cdi-reference, verified 2026-08-23.
16. Mark Seemann, When to use a DI Container, blog.ploeh.dk, 2012-11-06, https://blog.ploeh.dk/2012/11/06/WhentouseaDIContainer/, verified 2026-08-23.
17. Mark Seemann, Pure DI, blog.ploeh.dk, 2014-06-10, https://blog.ploeh.dk/2014/06/10/pure-di/, verified 2026-08-23.
18. Mark Seemann, On Constructor Over-injection, blog.ploeh.dk, 2018-08-27, https://blog.ploeh.dk/2018/08/27/on-constructor-over-injection/, verified 2026-08-23.
19. Mockito, site.mockito.org, https://site.mockito.org/, verified 2026-08-23.
20. Martin Fowler, Mocks Aren't Stubs, martinfowler.com, https://martinfowler.com/articles/mocksArentStubs.html, verified 2026-08-23.
21. David Heinemeier Hansson, Test-induced design damage, dhh.dk, 2014, https://dhh.dk/2014/test-induced-design-damage.html, verified 2026-08-23.
22. Spring Boot Documentation, Testing Spring Boot Applications, https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html, verified 2026-08-23.
23. Spring Boot Documentation, Actuator Endpoints, https://docs.spring.io/spring-boot/reference/actuator/endpoints.html, verified 2026-08-23.
24. Spring Boot 3.3.0 available now, spring.io blog, 2024-05-23, https://spring.io/blog/2024/05/23/spring-boot-3-3-0-available-now, verified 2026-08-23.
25. Spring Boot Documentation, GraalVM Native Image Support, https://docs.spring.io/spring-boot/reference/packaging/native-image/introducing-graalvm-native-images.html, verified 2026-08-23.
26. GitHub Security Advisory GHSA-36p3-wjmg-h94x, Remote Code Execution in Spring Framework, https://github.com/advisories/GHSA-36p3-wjmg-h94x, verified 2026-08-23.
27. GitHub Security Advisories, google/guice, https://github.com/google/guice/security/advisories, verified 2026-08-23.
28. GitHub Security Advisories, google/dagger, https://github.com/google/dagger/security/advisories, verified 2026-08-23.
29. GitHub Security Advisories, spring-projects/spring-framework, https://github.com/spring-projects/spring-framework/security/advisories, verified 2026-08-23.
30. NestJS, GitHub Releases, https://github.com/nestjs/nest/releases, verified 2026-08-23.

**Evidence grade.** high

**Most solid findings.** Fowler's own essay, read directly, is unambiguous about both his rationale for coining the term and his own nuanced, non-absolute position on Dependency Injection versus Service Locator, a nuance many secondary sources flatten. Robert Martin's original 1996 paper, read in full, provides direct primary-source proof that the Dependency Inversion Principle predates and never uses the vocabulary of Dependency Injection, closing a distinction the software literature frequently blurs. The universal adoption of the exact phrase Dependency Injection across five unrelated, independently maintained frameworks, Spring, ASP.NET Core, Angular, Guice, and NestJS, is about as strong a confirmation of terminology adoption as this catalogue is likely to find for any entry.

**Unverified or unclear.** Exact founding dates for PicoContainer and the earliest Spring Framework releases could not be independently confirmed, PicoContainer's own site is unreachable and web archive access was unavailable during research, so the claim that the practice predates 2004 rests on Fowler's own contemporaneous language rather than a dated founding record. A single source explicitly connecting the Strategy pattern and Dependency Injection as structurally similar mechanisms could not be located, and that comparison in section 13 is presented as reasoned architectural analysis rather than a cited claim. Comparative, independently measured startup latency numbers between Spring Boot and a compile-time framework like Micronaut or Quarkus could not be found, so this entry states the vendors' own qualitative rationale rather than inventing a benchmark figure.

## Code

### TypeScript

```typescript
interface PaymentGateway {
  charge(amountCents: number): string;
}

class ConcretePaymentGateway implements PaymentGateway {
  charge(amountCents: number): string {
    return "charged " + amountCents + " cents via real gateway";
  }
}

class FakePaymentGateway implements PaymentGateway {
  public lastCharged: number | null = null;

  charge(amountCents: number): string {
    this.lastCharged = amountCents;
    return "fake charge recorded";
  }
}

class OrderService {
  private gateway: PaymentGateway;

  constructor(gateway: PaymentGateway) {
    this.gateway = gateway;
  }

  placeOrder(amountCents: number): string {
    return this.gateway.charge(amountCents);
  }
}

function main(): void {
  const production = new OrderService(new ConcretePaymentGateway());
  console.log(production.placeOrder(4200));

  const fakeGateway = new FakePaymentGateway();
  const test = new OrderService(fakeGateway);
  test.placeOrder(4200);

  if (fakeGateway.lastCharged !== 4200) {
    throw new Error("OrderService did not call the injected gateway");
  }
  console.log("test passed, OrderService never knew which gateway it used");
}

main();
```

### Python

```python
class PaymentGateway:
    def charge(self, amount_cents):
        raise NotImplementedError


class ConcretePaymentGateway(PaymentGateway):
    def charge(self, amount_cents):
        return "charged " + str(amount_cents) + " cents via real gateway"


class FakePaymentGateway(PaymentGateway):
    def __init__(self):
        self.last_charged = None

    def charge(self, amount_cents):
        self.last_charged = amount_cents
        return "fake charge recorded"


class OrderService:
    def __init__(self, gateway):
        self.gateway = gateway

    def place_order(self, amount_cents):
        return self.gateway.charge(amount_cents)


def main():
    production = OrderService(ConcretePaymentGateway())
    print(production.place_order(4200))

    fake_gateway = FakePaymentGateway()
    test = OrderService(fake_gateway)
    test.place_order(4200)

    if fake_gateway.last_charged != 4200:
        raise RuntimeError("OrderService did not call the injected gateway")
    print("test passed, OrderService never knew which gateway it used")


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import "fmt"

type PaymentGateway interface {
	Charge(amountCents int) string
}

type ConcretePaymentGateway struct{}

func (g *ConcretePaymentGateway) Charge(amountCents int) string {
	return fmt.Sprintf("charged %d cents via real gateway", amountCents)
}

type FakePaymentGateway struct {
	LastCharged int
}

func (g *FakePaymentGateway) Charge(amountCents int) string {
	g.LastCharged = amountCents
	return "fake charge recorded"
}

type OrderService struct {
	Gateway PaymentGateway
}

func NewOrderService(gateway PaymentGateway) *OrderService {
	return &OrderService{Gateway: gateway}
}

func (s *OrderService) PlaceOrder(amountCents int) string {
	return s.Gateway.Charge(amountCents)
}

func main() {
	production := NewOrderService(&ConcretePaymentGateway{})
	fmt.Println(production.PlaceOrder(4200))

	fakeGateway := &FakePaymentGateway{}
	test := NewOrderService(fakeGateway)
	test.PlaceOrder(4200)

	if fakeGateway.LastCharged != 4200 {
		panic("OrderService did not call the injected gateway")
	}
	fmt.Println("test passed, OrderService never knew which gateway it used")
}
```
