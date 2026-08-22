---
name: Inversion of Control
slug: inversion-of-control
family: 04-principles-and-laws
category: Design Principle
aliases: [IoC, Hollywood Principle]
first_described: "Ralph E. Johnson and Brian Foote, Designing Reusable Classes, Journal of Object-Oriented Programming, June/July 1988"
maturity: canonical
related: [dependency-inversion-principle, template-method, observer, strategy, service-locator, event-driven-architecture]
incompatible_with: []
verified: 2026-08-22
---

# Inversion of Control

## 1. Name, aliases, and lineage

The canonical name is Inversion of Control, almost always shortened to IoC. The
common synonym is the Hollywood Principle, from the line "don't call us, we'll
call you." Martin Fowler traces that phrase to a 1983 paper on the Mesa
programming environment by Richard Sweet, quoting it directly. "Don't call us,
we'll call you (Hollywood's Law). A tool should arrange for Tajo to notify it
when the user wishes to communicate some event to the tool, rather than adopt
an ask the user for a command and execute it model." (Fowler, "InversionOfControl,"
see reference 2, quoting Sweet 1983.)

The term itself, as opposed to the colorful synonym, first appears in print in
Ralph E. Johnson and Brian Foote's paper "Designing Reusable Classes," Journal
of Object-Oriented Programming, Volume 1, Number 2, June/July 1988, pages 22
to 35, in a section titled "White-box vs. Black-box Frameworks." The authors
describe how a framework calls the methods a user defines to tailor it,
rather than the other way around, and state it plainly. "This inversion of
control gives frameworks the power to serve as extensible skeletons."
(Johnson and Foote 1988, see reference 1, verified against the primary text.)

IoC is often confused with two related but distinct ideas covered elsewhere in
this catalogue. Dependency Injection is one specific technique for achieving
IoC over how an object gets its dependencies. The Dependency Inversion
Principle is a rule about the direction of source-code dependencies, not about
who calls whom at runtime. Dimension 13 draws each line precisely.

## 2. Problem and context

In an ordinary, un-inverted call structure, application code owns the entry
point. It decides what runs, in what order, and it calls out to a library for
reusable pieces, formatting, parsing, math, and gets a return value back. The
application is always the caller.

The problem arises the moment a piece of general-purpose machinery, a UI event
loop, an object-relational mapper managing a request's lifecycle, a web
framework routing an incoming request, a test runner executing a suite, a
plugin host loading a third-party module, needs to be shared by many different
applications that each supply different specific behaviour. That machinery
cannot be copied into every application without duplicating it everywhere and
losing a single place to fix a bug in it. So the machinery is built once, as a
framework, and it takes over the entry point. The framework now owns the loop,
the lifecycle, or the dispatch, and it calls out to the pieces the application
supplies at fixed extension points. Johnson and Foote describe exactly this
shift in their own words. "One important characteristic of a framework is
that the methods defined by the user to tailor the framework will often be
called from within the framework itself, rather than from the user's
application code. The framework often plays the role of the main program in
coordinating and sequencing application activity." (Johnson and Foote 1988,
see reference 1.)

The same reversal shows up at a smaller scale whenever an object needs a
collaborator whose concrete type varies by environment, production versus
test, one region versus another, and the object should not decide which
concrete type to build. A single composition root, or a container acting as
one, decides that instead, and hands the finished dependency in.

## 3. Forces

- Reuse of shared control flow against a directly traceable call stack. A
  framework that owns the loop lets many applications reuse one piece of
  machinery, but a reader following code outward from a handler can no longer
  see every caller by reading the source alone; they need to know the
  framework's contract too.
- Extensibility against cognitive load. A fixed skeleton with many pluggable
  parts lets new behaviour be added without touching the skeleton's own code,
  the open half of the open-closed idea, but a new team member must first
  learn where the skeleton calls in before they can add anything.
- Decoupling from one concrete implementation against error timing. Handing a
  dependency in from outside, rather than constructing it inside, lets the
  concrete type change without touching the consumer. A container that
  resolves that graph at startup can also fail loudly and early, before a
  single request is served, when the graph does not resolve. A container that
  waits and resolves lazily instead defers that same failure to first use.
- Substitutability for tests against the size of that gain. A dependency
  supplied from outside can be swapped for a test double without changing the
  consumer's code. Fowler is direct that this specific gain does not
  distinguish Dependency Injection from Service Locator. He writes plainly
  that "there is really no difference here between dependency injection and
  service locator." Both, in his own words, "are very amenable to stubbing."
  (Fowler, "InversionOfControl Containers," see reference 3.) What actually
  earns the gain is supplying the dependency from outside at all, not the
  particular wiring technique chosen.
- A shared container as team cost against the wiring it removes. A reflection
  driven container removes the chore of writing every `new` call by hand, but
  a class instantiated by reflection with no visible constructor call in the
  calling code is harder for a person under time pressure to trace than a
  plain function call. James Shore states the concern in stark terms. He
  wants to "start at main() and trace through the code" and "look at callers
  and find where every parameter came from," and calls a container that
  hides that "magic." (Shore, "The Problem With Dependency Injection
  Frameworks," see reference 17.)

IoC favours reuse, extensibility, and a swappable dependency graph. It gives up
a directly traceable, single-file call stack in the pieces it inverts, in
exchange for a contract the reader must learn once.

## 4. Applicability and non-applicability

Reach for IoC when building or using machinery meant to be extended by many
different callers with different specific behaviour. a UI toolkit's event
loop, an ORM's row-to-object lifecycle, a web framework's request routing, a
test runner calling setUp and tearDown around every test, a plugin host, a
serverless platform invoking one handler per request. Reach for it at the
smaller, object-wiring scale when several objects in a system share a
dependency whose concrete type varies by environment or needs a test double,
and scattering `new` calls for it across the codebase would mean changing many
places every time that concrete type changes.

Do not reach for it when a script or a small tool has one fixed dependency for
its entire life, never varies by environment, and never needs a test double.
The container's reflection and configuration cost buys nothing there, a plain
constructor call is both faster and easier to trace. Do not reach for a
reflection based container on a path where instantiation cost is measured on
every call, a compile-time approach exists for exactly that reason (dimension
8). Do not reach for it as the only way to get a testable design, a manually
written composition root, one function that calls constructors directly and
passes the results down, gives the same swap-a-test-double benefit at a lower
cost and with a fully traceable call stack, which is Fowler's own point about
Service Locator and Dependency Injection sharing that benefit. Do not build a
container-based plugin host at all when a small, fixed, closed set of
implementations is all that will ever exist, a plain conditional or a `switch`
does the job with nothing to learn.

## 5. Structure

At the framework scale, the participants are the host, which owns the flow of
control, the loop, the lifecycle, or the request dispatch, and decides when to
call out; the extension point, an interface, an abstract method, a callback
slot, or a subscribed event, that marks exactly where the host will call in;
and the supplied component, the concrete piece of behaviour the application
hands the host to run at that point.

At the object-wiring scale, the participants are the dependency, the concrete
or abstract collaborator a consumer needs; the consumer, the object that uses
the dependency without constructing it; and the composition root, the one
place, hand written or delegated to a container, that decides which concrete
dependency backs which consumer and hands it in.

## 6. ASCII structure diagram

```
Framework-scale IoC (the host owns the loop)

  +------------------+          registers/implements          +--------------------+
  |  Application code |  -------------------------------->     | Extension point     |
  |  (a handler, a     |                                        | (interface, abstract|
  |   listener, a step)|                                        |  method, event slot) |
  +---------+----------+                                        +----------+----------+
            ^                                                              |
            | calls in at the extension point                             |
            |                                                              v
  +---------+-------------------------------------------------------------+---------+
  |                              Host / framework                                    |
  |  owns the loop, the lifecycle, or the request dispatch. never calls main().      |
  +------------------------------------------------------------------------------------+


Object-wiring IoC (a composition root decides who gets what)

  +----------------+       resolves and injects        +----------------+
  | Composition root| ---------------------------------> |   Consumer      |
  | (hand written or |                                     | (constructor    |
  |  a container)     |                                     |  parameter of an|
  +--------+---------+                                     |  interface type) |
           |                                               +--------+---------+
           | constructs                                             |
           v                                                        | uses through
  +------------------+                                              v the interface
  |  Concrete          |  <-----------------------------------------+
  |  dependency         |
  +------------------+
```

## 7. Dynamics

At the framework scale, the sequence runs in this order. The application
registers or implements a handler at startup and returns control to the host.
The host starts its own loop, or waits for its own trigger, a request, an
event, a test invocation. When a trigger fires, the host calls the registered
handler, passing whatever context that extension point defines. The handler
runs, returns a result or raises an error, and control returns to the host,
never to the application's own main function.

At the object-wiring scale, run through a reflection-driven container, the
sequence is different. At startup, the container reads its configuration,
annotations, a module class, or an external file, and builds a dependency
graph. When a consumer is requested, the container resolves each of its
declared dependencies first, recursively, constructing the graph from the
leaves inward, then constructs the consumer and hands the finished
dependencies in. If, while resolving, the container finds it is already in the
middle of constructing a bean it needs again lower in the same chain, it
cannot decide an order and fails immediately rather than looping. Spring
surfaces this as `BeanCurrentlyInCreationException` (see reference 11 and
reference 6 style documentation), thrown while the application context is
loading, before a single request is served.

## 8. Implementation variants

- Template Method. A base class owns the fixed steps of an algorithm and calls
  out to abstract or overridable methods a subclass fills. JUnit's own test
  lifecycle is the standard example. "The framework code calls setUp and
  tearDown methods for you to create and clean up your test fixture." (Fowler,
  "InversionOfControl," see reference 2.)
- Callback and event binding. The application passes a function or a closure
  the host stores and calls later when a matching event happens, rather than
  the application polling for that event itself.
- Event subscription. The host defines a fixed set of events and the
  application subscribes handlers to the ones it cares about, the
  publish-subscribe shape.
- Interface implementation host. The host defines an interface the
  application must implement, and calls the application only through that
  interface, the shape Fowler cites in Enterprise JavaBeans.
- Dependency Injection through a reflection-driven container. Constructor,
  setter, or field injection, resolved and handed in by a container built for
  the purpose. Spring's own docs state the relationship precisely.
  "Dependency injection (DI) is a specialized form of IoC, whereby objects
  define their dependencies... The IoC container then injects those
  dependencies when it creates the bean." (Spring Framework Reference, see
  reference 5.) Spring and Microsoft's own .NET docs both name constructor
  injection the default. Spring calls it a way to "implement application
  components as immutable objects" and confirms "required dependencies
  are not null" (see reference 7), reserving setter injection for genuinely
  optional dependencies, and warning that "a large number of constructor
  arguments is a bad code smell" pointing at a class with too many
  responsibilities.
- Service Locator. The consumer asks a locator object for a dependency by name
  or type at the point of use, instead of having it handed in through a
  constructor. Microsoft's own DI guidance names this a pattern to avoid.
  "Avoid using the service locator pattern... don't invoke GetService to
  obtain a service instance when you can use DI instead." (Microsoft Learn,
  see reference 9.) This catalogue treats it as a separate, contested entry,
  see dimension 13.
- Compile-time Dependency Injection. The dependency graph is generated at
  build time instead of resolved by reflection at runtime, Dagger is the
  standard example on the JVM and Android, described on its own site as "a
  fully static, compile-time dependency injection framework for Java, Kotlin,
  and Android." (Dagger, see reference 14.) This trades some runtime
  flexibility for a compile error instead of a runtime exception when a
  dependency graph does not resolve, and removes reflection cost from every
  construction.
- Platform-invoked handler, no wiring involved. A serverless platform calls a
  fixed function on every incoming request; there is no dependency graph at
  all, only a host that owns invocation. Cloudflare Workers describes this as
  the runtime invoking "the fetch() handler defined in your Worker code with
  the given request" whenever a request reaches the platform. (Cloudflare
  Workers docs, see reference 15.)

## 9. Known production uses

- Spring Framework's IoC container, the `org.springframework.beans` and
  `org.springframework.context` packages, backs dependency management across
  the large majority of Java enterprise applications. (Spring Framework
  Reference, see reference 5.)
- .NET's built-in dependency injection, `Microsoft.Extensions.DependencyInjection`,
  ships as part of the framework itself and is the default wiring mechanism
  for ASP.NET Core applications. (Microsoft Learn, see reference 8 and
  reference 10.)
- Dagger, and Hilt built on top of it, provide compile-time dependency
  injection across Android application code, documented in Android's own
  developer guides. (Android Developers, see reference 13; Dagger, see
  reference 14.)
- JUnit's test lifecycle calls a subclass's setUp and tearDown methods, the
  canonical named example of Template Method as IoC, cited directly by
  Fowler. (Fowler, "InversionOfControl," see reference 2.)
- Cloudflare Workers invokes a developer-supplied fetch() handler on every
  incoming request, a serverless platform example of the general principle
  with no object-wiring aspect at all. (Cloudflare Workers docs, see
  reference 15.)

## 10. Consequences

Positive. Shared control-flow machinery is written once and reused by many
different applications instead of being copied into each one. New behaviour
can be added at an extension point without changing the host's own code.
Wiring decisions for which concrete type backs which dependency live in one
place, a composition root or a container's configuration, instead of
scattered across every constructor call site. A dependency supplied from
outside can be swapped for a test double without changing the consumer.

Negative. A reader can no longer find every caller of a piece of code by
reading the source alone; some callers live inside the host and only show up
by knowing its contract. A reflection-driven container adds real cost, in
build-up time and in the debugging effort needed when wiring fails, described
by practitioners as feeling like "magic" when it works and difficult to trace
when it does not. (Shore, see reference 17; Scott Logic, see reference 18.) A
container does not fix a class that takes too many constructor parameters,
Spring's own docs call that a smell pointing at a class with too many
responsibilities, it only makes constructing that class easier, which can hide
the underlying design problem for longer. A circular dependency in a
constructor-graph fails at startup with a specific runtime exception rather
than a compile error in a statically typed language without the container.

## 11. Failure modes and misuse

Circular dependency between two beans that both need each other through their
constructors. Spring cannot decide a construction order and throws
`BeanCurrentlyInCreationException` while loading the application context, the
observable symptom is a startup crash naming the two beans, not a subtle
runtime bug. (Baeldung, see reference 11.)

Overusing field or setter injection everywhere instead of constructor
injection to sidestep that failure. It works, but it defers the circular
dependency to first use instead of catching it at startup, since a field can
be left temporarily null while the container resolves it lazily, and it
prevents the field from ever being made immutable. Baeldung documents both
costs directly. Field injection "creates a risk of NullPointerException if
dependencies aren't correctly initialized" and, in the same article's own
words, "using the field injection, we are unable to create immutable
classes." (Baeldung, see reference 12.)

Reaching for Service Locator lookups by default instead of an explicit
constructor parameter. A dependency looked up at the point of use, rather than
declared in a signature, is invisible to a reader and to any static analysis
that only reads constructors. Microsoft's own guidelines name this and the
closely related pattern of injecting a factory that resolves at runtime as
patterns to avoid, on the grounds that both "mix Inversion of Control
strategies." (Microsoft Learn, see reference 9.)

Confusing IoC, Dependency Injection, and the Dependency Inversion Principle as
one idea. Fowler's own summary draws the line precisely. "DI is about wiring,
IoC is about direction, and DIP is about shape." (Schuchert, "DIP in the
Wild," see reference 4.) Treating them as interchangeable leads to claims like
"this class follows DIP because it uses a container," which does not follow;
a container can wire two concrete classes together with no abstraction
between them at all.

Choosing a reflection-based container on a path where construction happens on
every call and the cost is measured. Reflection-driven resolution is not free;
compile-time dependency injection exists specifically to remove that cost
(dimension 8), and picking the reflective style where the compile-time style
would do is a real, measurable misuse rather than a style preference.

## 12. Trade-off matrix

| Approach | Traceability of the call stack | Startup or build cost | Circular dependency caught | Swappable for a test double |
|---|---|---|---|---|
| Manual composition root, hand written constructors | High, every call is a plain function call a reader can grep for | None beyond normal object construction | A compile error in most statically typed languages | Fully, pass a stub in by hand |
| Reflection-driven container (Spring, .NET DI) | Low for field injection, moderate for constructor injection | Reflection and graph resolution at startup | A runtime exception at startup, for constructor-style graphs | Fully, override a registration |
| Compile-time dependency injection (Dagger) | Moderate, the generated wiring code can be read directly | Build time only, no runtime reflection | A compile error | Fully |
| Service Locator | Low, the dependency is looked up at the point of use, not visible in any signature | Low per lookup | No fixed graph exists to walk, so nothing is caught this way | Supported, but requires swapping the locator's own registered instance globally |

## 13. Related and incompatible patterns

Dependency Inversion Principle (see `dependency-inversion-principle.md` in
this family) is a separate rule about the direction of source-code
dependencies, high-level and low-level modules both depending on an
abstraction, and it says nothing about who calls whom at runtime. An IoC
container commonly helps a codebase satisfy DIP by supplying the concrete
class from outside, but DIP can be satisfied with no container at all, by a
single hand-written composition root, and a container can wire two concrete
classes together with no abstraction present, which satisfies neither DIP nor
the spirit of IoC's own decoupling. Fowler's line, cited in dimension 11,
draws this exactly. DI is about wiring, IoC is about direction, and DIP is
about shape.

Template Method (see `template-method.md` in family 01) is the simplest,
framework-free way to get IoC inside a single class hierarchy, no container or
event system required.

Observer and Strategy (see `observer.md` and `strategy.md` in family 01) are
the event-subscription and pluggable-behaviour implementation variants of the
same direction-of-control reversal, described at the level of a single object
relationship rather than a whole application's wiring.

Service Locator (see `service-locator.md` and `service-locator-antipattern.md`
in family 18) is a competing technique for supplying a dependency that this
catalogue records separately as contested, because it hides the dependency
behind a runtime lookup instead of making it visible in a constructor
signature, the opposite of what most uses of IoC are trying to achieve.

Event-Driven Architecture (see `event-driven-architecture.md` in family 05) is
the same "the platform calls you" reversal applied at the level of a whole
system rather than a single class or container.

There is no pattern IoC is flatly incompatible with at the level of the
general principle; it is a direction-of-control idea, not a single concrete
mechanism. A specific implementation choice can conflict with a specific
goal, heavy field-injection wiring conflicts with a goal of fully immutable
objects, but that is a choice within IoC, not an incompatibility with it.

## 14. Refactoring path in and out

In. Find a class that builds its own dependency inside a method body,
`new ConcreteThing()` called directly. Extract an interface for that
dependency's contract. Add a constructor parameter of the interface type in
place of the internal construction. Move the concrete construction to the
call site, or to a composition root, or to a container registration. Update
every caller to pass the dependency in. This is the same shape Microsoft's own
docs walk through directly. A hard-coded concrete `MessageWriter` becomes an
`IMessageWriter` interface parameter, with the concrete choice made once at
registration and never again inside the consumer.

For a framework-level Template Method extraction, move the fixed steps of an
algorithm into a base class, and turn the steps that vary between callers into
abstract or overridable methods a subclass fills.

Out. When a dependency is truly fixed for the whole life of the application,
never varies by environment, and never needs a test double, remove the
indirection and construct it directly at the point of use. The abstraction has
stopped earning its place, and removing it restores a directly traceable call
a reader can follow without knowing a container's contract.

## 15. Testing and verification

Constructor injection makes substituting a test double for a real dependency
a normal part of building the object under test, no framework or container
required to run the test itself. Microsoft's own docs make the contrast
directly. A class holding a concrete, self-constructed dependency "is
difficult to unit test... isn't possible with this approach," while the same
class taking the dependency as an interface parameter lets a test pass a mock
or stub in its place with no other change. (Microsoft Learn, see reference 8.)

Fowler's honest caveat still applies here. This specific gain is not unique
to Dependency Injection. Service Locator is, in his own words, "very amenable
to stubbing" too. The requirement that actually earns the testability, in
either technique, is only that the dependency be supplied from outside the
object rather than constructed inside it.

For framework-level IoC, Template Method or event subscription, test the
concrete subclass or handler directly by calling its own methods, without
running the host's loop at all. The host's own dispatch logic, separately, is
tested by exercising the extension point contract with a minimal, known
implementation and checking that the host calls it at the right time with the
right arguments.

## 16. Observability signals

At container startup, a log line per component created, in dependency order,
is the normal health signal. A healthy startup runs this pass exactly once and
finishes. A repeated or retried resolution attempt for the same component, a
`BeanCurrentlyInCreationException` or its equivalent, or a startup that spends
most of its time on reflection-based construction, visible in a startup
trace, are the failing signals.

For request-scoped or session-scoped components, track the created-instance
count against the expected request or session count. A scope misconfigured
one level too broad silently shares one instance across many requests; one
misconfigured too narrow builds a fresh instance far more often than the
design intended, both of which show up as an instance-count mismatch rather
than an error.

## 17. Security and privacy implications

IoC itself has no direct data-handling behaviour; it changes who calls whom,
not what data moves between them, and is silent on data handling where the
wiring is fixed at compile time or from a trusted configuration source.

Where it opens surface is a host that resolves and instantiates a class named
by external or dynamically supplied configuration, a plugin host loading a
third-party assembly by name, or a container wired from configuration a user
can edit. If that configuration source is not trusted, an attacker who can
influence it can potentially cause the host to instantiate a class of their
choosing. This makes the trust boundary of the wiring configuration matter
more than it would in a directly called, statically compiled call graph,
because the point of construction is no longer visible or fixed at the call
site.

## 18. References

1. Ralph E. Johnson, Brian Foote, "Designing Reusable Classes," Journal of
   Object-Oriented Programming, Volume 1, Number 2, June/July 1988, pages 22
   to 35. https://www.laputan.org/drc/drc.html, verified 2026-08-22.
2. Martin Fowler, "InversionOfControl," bliki.
   https://martinfowler.com/bliki/InversionOfControl.html, verified
   2026-08-22.
3. Martin Fowler, "Inversion of Control Containers and the Dependency
   Injection pattern." https://martinfowler.com/articles/injection.html,
   verified 2026-08-22.
4. Brett L. Schuchert, "DIP in the Wild," martinfowler.com.
   https://martinfowler.com/articles/dipInTheWild.html, verified 2026-08-22.
5. Spring Framework Reference, "IoC Container," core/beans/introduction.
   https://docs.spring.io/spring-framework/reference/core/beans/introduction.html,
   verified 2026-08-22.
6. Spring Framework Reference, "Bean Scopes."
   https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html,
   verified 2026-08-22.
7. Spring Framework Reference, "Dependency Injection."
   https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html,
   verified 2026-08-22.
8. Microsoft Learn, ".NET dependency injection."
   https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection,
   verified 2026-08-22.
9. Microsoft Learn, "Dependency injection guidelines."
   https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/guidelines,
   verified 2026-08-22.
10. Microsoft Learn, "Dependency injection in ASP.NET Core."
    https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection,
    verified 2026-08-22.
11. Baeldung, "Circular Dependencies in Spring."
    https://www.baeldung.com/circular-dependencies-in-spring, verified
    2026-08-22.
12. Baeldung, "Why Is Field Injection Not Recommended?"
    https://www.baeldung.com/java-spring-field-injection-cons, verified
    2026-08-22.
13. Android Developers, "Hilt and Dependency Injection."
    https://developer.android.com/training/dependency-injection/hilt-android,
    verified 2026-08-22.
14. Dagger, official site. https://dagger.dev/, verified 2026-08-22.
15. Cloudflare Workers docs, "How Workers works."
    https://developers.cloudflare.com/workers/reference/how-workers-works/,
    verified 2026-08-22.
16. Wikipedia, "Inversion of control."
    https://en.wikipedia.org/wiki/Inversion_of_control, verified 2026-08-22.
17. James Shore, "The Problem With Dependency Injection Frameworks."
    https://www.jamesshore.com/v2/blog/2023/the-problem-with-dependency-injection-frameworks,
    verified 2026-08-22.
18. Scott Logic, "Spring Autowiring, It's a Kind of Magic, Part 1."
    https://blog.scottlogic.com/2020/02/25/spring-autowiring-its-a-kind-of-magic.html,
    verified 2026-08-22.

**Evidence grade.** high

**Most solid findings.** The term's origin, Johnson and Foote 1988, is
confirmed against the primary paper text itself, not only against a secondary
citation of it. The claim that Dependency Injection is a specific technique
for achieving the broader IoC principle is confirmed independently by two
competing framework maintainers, Spring and Microsoft, in their own official
documentation, not asserted from a single source.

**Unverified or unclear.** The "amount of magic" complaint against
reflection-based, annotation-driven containers is well attested as a common
practitioner concern, Baeldung, Scott Logic, and James Shore each raise it
independently, but no official framework document states it as their own
reason for recommending constructor injection over field injection; their
stated reasoning is immutability and catching a circular dependency at
startup instead.

## Code examples

### TypeScript, constructor injection through a hand-written composition root

```typescript
interface MessageWriter {
  write(message: string): void;
}

class ConsoleWriter implements MessageWriter {
  write(message: string): void {
    console.log(message);
  }
}

class RecordingWriter implements MessageWriter {
  readonly messages: string[] = [];
  write(message: string): void {
    this.messages.push(message);
  }
}

class GreetingService {
  constructor(private readonly writer: MessageWriter) {}
  greet(name: string): void {
    this.writer.write("Hello, " + name);
  }
}

function buildProductionService(): GreetingService {
  return new GreetingService(new ConsoleWriter());
}

const testWriter = new RecordingWriter();
const testService = new GreetingService(testWriter);
testService.greet("Ada");
console.log(testWriter.messages[0] === "Hello, Ada");
```

### Python, a plugin host that owns the loop and calls into registered handlers

```python
from typing import Callable

class TickHost:
    def __init__(self) -> None:
        self._handlers: list[Callable[[int], None]] = []

    def register(self, handler: Callable[[int], None]) -> None:
        self._handlers.append(handler)

    def run(self, ticks: int) -> None:
        for tick in range(ticks):
            for handler in self._handlers:
                handler(tick)

def log_tick(tick: int) -> None:
    print("tick", tick)

seen: list[int] = []

def record_tick(tick: int) -> None:
    seen.append(tick)

host = TickHost()
host.register(log_tick)
host.register(record_tick)
host.run(3)
assert seen == [0, 1, 2]
```

### Go, interface-based constructor injection with an idiomatic test double

```go
package main

import "fmt"

type Clock interface {
	Now() string
}

type FixedClock struct {
	value string
}

func (c FixedClock) Now() string {
	return c.value
}

type Greeter struct {
	clock Clock
}

func NewGreeter(clock Clock) Greeter {
	return Greeter{clock: clock}
}

func (g Greeter) Greeting(name string) string {
	return name + " arrived at " + g.clock.Now()
}

func main() {
	greeter := NewGreeter(FixedClock{value: "09:00"})
	result := greeter.Greeting("Ada")
	fmt.Println(result)
	if result != "Ada arrived at 09:00" {
		panic("unexpected greeting")
	}
}
```
