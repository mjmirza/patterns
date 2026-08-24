---
name: Dependency Inversion Principle
slug: dependency-inversion-principle
family: 04-principles-and-laws
category: Design Principle
aliases: [DIP, Dependency Inversion, "the D in SOLID"]
first_described: "Robert C. Martin, C++ Report, June 1996"
maturity: canonical
related: [strategy, factory-method, adapter, interface-segregation-principle, open-closed-principle, single-responsibility-principle, liskov-substitution-principle]
incompatible_with: []
verified: 2026-08-02
---

# Dependency Inversion Principle

## 1. Name, aliases, and lineage

The Dependency Inversion Principle, almost always shortened to DIP, is the D in
the SOLID acronym. It was first written down by Robert C. Martin in an article
titled "The Dependency Inversion Principle", published in the C++ Report in
June 1996 (verified against a summary of the original article, see references).
Martin later folded the same material into his 2002 book Agile Software
Development, Principles, Patterns, and Practices, as chapter 11, and again into
the 2017 book Clean Architecture, where the principle is generalized into the
architectural boundary rule that gives that book its structure.

The principle is sometimes conflated with two things it is not. It is not
Dependency Injection, and it is not an Inversion of Control container. Martin
Fowler drew this distinction explicitly in his January 2004 article "Inversion
of Control Containers and the Dependency Injection pattern", where he argues
that "Inversion of Control" is too generic a term and proposes "Dependency
Injection" as the more precise name for the wiring technique (martinfowler.com,
verified 2026-08-02, see references). Dependency Injection is one mechanical
technique for satisfying DIP. It is neither necessary nor sufficient for DIP on
its own, a point developed in dimension 8 below.

No alternate name for the principle itself is in common circulation. "Dependency
inversion" is occasionally shortened in conversation to "inversion", which
invites confusion with Inversion of Control, a related but broader idea about
who calls whom in a system, first named by Martin Fowler and others in the
early 2000s in the context of frameworks calling application code rather than
the reverse.

## 2. Problem and context

A codebase grows outward from a small number of policy decisions, what the
system does, in what order, and why. Around those decisions accumulate the
mechanical details that make the policy actually run, which database driver
writes the row, which HTTP client makes the call, which file system API reads
the config. In a naive design, the policy code names the mechanical code
directly. `OrderProcessor` imports `MySqlConnection`. `PaymentService`
constructs a `StripeClient`. `ReportGenerator` calls `SmtpMailer` by name.

This reads as natural, because it is how most people first learn to write
software, start with the concrete tool, then build the behavior that uses it.
The problem surfaces later, when one of three things happens. The mechanical
detail needs to change, a new database vendor, a different email provider. The
policy needs to be tested without the mechanical detail actually running, no
real database in the unit test suite. Or the mechanical detail needs to be
reused by a second policy that should not care which detail it got. In each
case, the direct import from policy to detail is the obstacle. The policy
class cannot be recompiled, retested, or reused independently of the concrete
class it named, because the source-code dependency runs from the thing that
should be stable toward the thing that changes most often.

The context in which DIP applies is specifically this. A codebase that has, or
will have, a boundary between a policy layer and a mechanism layer, where the
mechanism is expected to vary across environments, deployments, or time, and
where the policy layer's stability is worth protecting. A single-file script
that reads one file and writes one line of output has no such boundary and no
such problem. DIP applied there is ceremony without a payoff, a point revisited
in dimension 4.

## 3. Forces

Compile-time and source-level coupling versus runtime flexibility. A direct
import from policy to a concrete implementation is fast to write and easy to
read in a single file. It also means the policy's object file, or its compiled
module, cannot exist without the concrete implementation's object file
existing too. DIP trades a small amount of upfront indirection, defining an
interface, wiring an instance, for the ability to substitute the
implementation without touching or recompiling the policy.

Stability of the abstraction versus the volatility of the detail. The
principle's own second half states that abstractions should not depend on
details, and details should depend on abstractions. This only pays off when
the abstraction is genuinely more stable than the concrete implementations
behind it. If the abstraction changes exactly as often as its one
implementation, introducing an interface adds a layer of indirection with no
stability gain, which is judgement, not something DIP proves for any given
interface.

Testability versus directness. Code that depends on an abstraction can be
exercised in a test with a fake or a stub standing in for the concrete
implementation, without a real database, network call, or file system. Code
that depends on a concrete class directly forces the test to either accept the
real dependency's cost and flakiness, or resort to fragile techniques such as
monkey-patching a class at runtime. This is one of the principle's most
concrete, measurable payoffs and is developed further in dimension 15.

Cognitive load of indirection. Every interface introduced is another name a
reader must hold in their head, another file to open to find out what a call
actually does, and one more level the debugger has to step through. A
codebase that inverts every dependency, including ones that will never
plausibly change, imposes a permanent navigation tax on every future reader in
exchange for a flexibility that may never be used. This is the principle's
most commonly cited cost and is discussed in dimension 10.

Team topology and ownership boundaries. When a policy module and a mechanism
module are owned by different teams, or ship on different release cadences,
an abstraction at the seam between them lets each team change its own side
without coordinating a simultaneous deploy. Where policy and mechanism are
owned by the same person in the same commit, this force is absent and the
abstraction earns its keep purely on testability and future volatility, not
organizational separation.

DIP favors long-term stability of the parts of a system that encode business
policy, at the cost of an extra indirection layer and additional up-front
design work. It sacrifices the immediate simplicity of calling the class that
does the thing, for the ability to change what does the thing later without
touching the code that decided the thing needed doing.

## 4. Applicability and non-applicability

Reach for DIP when the following hold.

- A module that encodes business rules or orchestration logic currently
  imports a concrete class that talks to an external system, a database
  driver, an HTTP client, a message queue client, a file system API, a clock,
  or a random number source.
- The concrete implementation is genuinely expected to vary, either across
  environments (a fake in tests, a real client in production), across
  deployments (on-premises versus cloud storage), or over the life of the
  product (swapping payment providers, swapping email vendors).
- Unit tests for the policy logic currently require a live external
  dependency, or resort to patching a concrete class at runtime, and that cost
  is measurably slowing the team down.
- Two or more concrete implementations of the same mechanical role already
  exist, or are clearly coming, and the policy code should not need to change
  when a third one is added.
- The module sits at, or is being designed to sit at, an architectural
  boundary, such as the edge between an application's core logic and its
  infrastructure, as described in Martin's 2017 book Clean Architecture.

Do NOT reach for DIP in these situations.

- The concrete class is a value type or a pure data structure with no
  external effects and no plausible alternative implementation, such as a
  language's own string, list, or date type. Inverting a dependency on a
  built-in value type adds indirection with no corresponding stability gain.
- There is exactly one implementation, no second implementation is planned,
  and the code is not being tested in isolation. Introducing an interface
  here is what Martin Fowler and others in the DI-container ecosystem have
  called premature abstraction. the interface becomes a maintenance burden
  that tracks its single implementation one-for-one, with every change to the
  implementation forcing a matching change to the interface.
- The module is a short-lived script, a one-off migration, or throwaway
  prototype code whose entire purpose is to be deleted after a single run.
  The cost of building and wiring an abstraction exceeds the code's own
  lifetime.
- The language or runtime already provides a built-in seam for the exact
  volatility in question, such as a language's ambient allocator or a
  platform's already-virtualized file system layer, where adding a second,
  hand-rolled abstraction on top duplicates a capability the platform gives
  for free.
- Applying DIP would require inverting a dependency on a genuinely stable,
  standardized, cross-cutting library, such as a language's own logging
  facade or its arithmetic operators, where the volatility the principle
  guards against does not exist in practice.
- The team cannot yet articulate what the second implementation would be.
  Speculative interfaces built for an imagined future variant, sometimes
  called a YAGNI violation in the wider literature, cost real design and
  maintenance effort against a benefit that may never materialize. This is
  judgement, drawn from the accumulated experience the SOLID literature
  itself warns about, not a rule DIP states.

## 5. Structure

DIP names three participants and constrains the direction of the relationships
between them.

- High-level module. The part of the system that encodes policy, business
  rules, orchestration, or decision-making. It is called high-level because
  it operates at a higher level of abstraction than the mechanism it needs,
  and because changes to it are meant to be driven by changes in business
  requirements rather than by changes in infrastructure.
- Low-level module. The part of the system that performs a mechanical,
  reusable operation, reading a row from a database, sending bytes over a
  socket, writing a file, reading the system clock. It is called low-level
  because it is closer to the operating system, network, or hardware and
  further from business meaning.
- Abstraction. An interface, protocol, or abstract base type owned by, or
  logically belonging to, the high-level module's layer. It states what the
  high-level module needs, in terms the high-level module's own vocabulary
  understands, without naming how the need is fulfilled.

The relationships DIP constrains are these. The high-level module depends
only on the abstraction, never directly on the low-level module. The
low-level module depends on, and implements, the abstraction. Ownership of
the abstraction sits with the high-level side of the boundary, not the
low-level side. this is the detail that gives the principle its name, because
in a naive design the natural ownership would run the other way, with the
low-level library defining an interface and the high-level module importing
it.

A common structural error is defining the interface in the same package as
the concrete implementation and calling this DIP because an interface now
exists. If both the interface and its one implementation live in the
low-level module's package, and the high-level module imports that package to
reach the interface, the compile-time dependency still points from
high-level to low-level, and the principle's second rule is unmet even though
an interface exists. This distinction is the most frequently missed part of
the structure and is revisited in dimension 11.

## 6. ASCII structure diagram

```
  Before DIP (source-level dependency points downward)

    +-------------------+
    |  OrderProcessor    |   high-level module
    |  (policy)          |
    +---------+---------+
              |
              | imports, constructs, calls directly
              v
    +-------------------+
    |  StripePayments    |   low-level module
    |  (mechanism)       |
    +-------------------+


  After DIP (both sides depend on an abstraction owned by the high-level side)

    +-------------------+          +---------------------------+
    |  OrderProcessor    | -------> |  PaymentGateway            |
    |  (high-level,      |  uses    |  (abstraction, owned by    |
    |   policy)          |          |   the high-level layer)    |
    +-------------------+          +---------------------------+
                                                  ^
                                                  | implements
                                                  |
                                   +---------------------------+
                                   |  StripePayments             |
                                   |  (low-level, mechanism)     |
                                   +---------------------------+

                                   +---------------------------+
                                   |  FakePaymentGateway          |
                                   |  (low-level, test double)   |
                                   +---------------------------+
```

The direction of the "implements" arrow, running from the low-level module up
to the abstraction, is the inversion the principle names. Before, the arrow of
compile-time dependency ran downward, high-level to low-level. After, the
low-level module's dependency arrow runs upward, toward an abstraction the
high-level layer owns.

## 7. Dynamics

At composition time, something outside both the high-level and low-level
modules decides which concrete low-level implementation to bind to the
abstraction. This composition step can be as small as a single constructor
call in a program's entry point, or as elaborate as a dependency injection
container resolving a graph of bindings from configuration.

```
  1. Composition root runs first (main(), a bootstrap function, or a DI
     container's configuration phase).

       composition root
             |
             | new StripePayments()      concrete instance created
             v
       concrete: StripePayments  implements  PaymentGateway
             |
             | passed as PaymentGateway   reference upcast to the abstraction
             v
       new OrderProcessor(paymentGateway) high-level module receives the
             |                            abstraction, never the concrete type
             v
       OrderProcessor instance ready, holding a PaymentGateway reference

  2. At runtime, the high-level module calls only through the abstraction.

       OrderProcessor.placeOrder()
             |
             | this.gateway.charge(amount)      dispatches through the
             v                                   interface
       runtime dispatch resolves to the
       concrete StripePayments.charge()          the low-level detail runs,
             |                                    but OrderProcessor's source
             v                                    code never named it
       charge completed, control returns
       to OrderProcessor

  3. In a test, the composition root substitutes a different concrete type.

       test setup: new OrderProcessor(fakeGateway)
             |
             v
       OrderProcessor.placeOrder() calls fakeGateway.charge()
             |
             v
       no network call occurs; the test asserts against the fake's
       recorded state
```

The core dynamic is that the high-level module's own source code and
compiled artifact are unaffected by which concrete type is bound at the
composition root. Swapping `StripePayments` for `FakePaymentGateway`, or for a
future `AdyenPayments`, changes only the binding at step 1. steps 2 and 3
happen through the same interface call, unmodified.

## 8. Implementation variants

Constructor injection is the most common mechanical technique. The high-level
module declares the abstraction as a constructor parameter and stores it. the
composition root supplies a concrete instance when it constructs the
high-level object. This is the variant used in the code examples below
because it makes the dependency visible in the type signature and produces
objects that are either fully valid or fail to construct at all, a property
Mark Seemann and Steven van Deursen discuss at length in Dependency Injection
Principles, Practices, and Patterns (Manning, 2019), where constructor
injection is presented as the default choice specifically because it prevents
an object existing in a partially wired state.

Setter or property injection supplies the abstraction through a mutable
property after construction, rather than through the constructor. This
variant is used when a dependency is genuinely optional, or when the
platform's own object lifecycle does not allow constructor parameters, such
as certain UI framework base classes that require a parameterless
constructor. The cost is that an object can exist in a state where the
dependency has not yet been set, and a call made before the setter runs fails
at a point disconnected from the missing wiring.

Interface injection has the abstraction define a method whose sole purpose is
to receive the dependency, and any class wanting the dependency implements
that method. This is the least common of the three in current practice. it
was more prominent in early Java frameworks and is described alongside the
other two by Martin Fowler in the January 2004 article already cited.

Manual composition with no container uses ordinary code, typically near a
program's entry point, that constructs concrete implementations and passes
them into high-level constructors. This variant requires no additional
library. It scales well for small to moderate object graphs and is the
variant every code example in this entry uses, because it demonstrates the
principle without an additional framework's vocabulary obscuring it.

A dependency injection container is a library, such as Spring's IoC container
for Java (docs.spring.io, verified 2026-08-02, see references), .NET's
built-in `IServiceCollection` and `IServiceProvider` (learn.microsoft.com,
verified 2026-08-02, see references), or Angular's hierarchical injector
(angular.dev, verified 2026-08-02, see references), that reads a set of
registrations, either in code or in configuration, and constructs the object
graph automatically, resolving each constructor's abstraction parameters to a
registered concrete type. This variant is warranted once the object graph
grows large enough that manual wiring becomes its own maintenance burden, a
threshold that is judgement rather than a fixed number.

A language-idiomatic variant swaps interfaces for closures and plain
functions. In languages with first-class functions, a single-method
abstraction is often better expressed as a function type than as a named
interface with one method. A `PaymentGateway` interface with a single
`charge` method can be replaced by a `charge: (amount: number) =>
Promise<void>` function parameter in TypeScript, or a `func(amount int)
error` parameter in Go, with the composition root passing a closure or a
bound method instead of constructing an object. This reduces ceremony for the
single-method case while preserving the same inversion. the high-level module
still depends on a shape it owns, not on a concrete function it named by
import. This is engineering judgement about idiom, not a claim from the
original 1996 article, which predates widespread closures in mainstream
object-oriented languages.

## 9. Known production uses

- The Spring Framework's IoC container is the canonical, widely deployed
  Java implementation of dependency inversion at framework scale. Spring's own
  reference documentation states that a typical enterprise application does
  not consist of a single object, and describes how bean definitions are
  wired together so that collaborating objects receive their dependencies
  through constructor or setter injection rather than constructing them
  directly (docs.spring.io/spring-framework/reference/core/beans/dependencies.html,
  verified 2026-08-02).
- .NET's built-in dependency injection container,
  `Microsoft.Extensions.DependencyInjection`, ships as part of the .NET
  runtime itself rather than as a third-party add-on. Microsoft's own
  documentation defines dependency injection as a technique for achieving
  Inversion of Control between classes and their dependencies, and walks
  through registering an `IMessageWriter` abstraction with `AddSingleton`,
  then resolving it via constructor injection into a `Worker` class that
  never names the concrete `MessageWriter` type directly
  (learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection,
  verified 2026-08-02).
- Angular's hierarchical dependency injection system is built into the
  framework and is the default way Angular components and services obtain
  their collaborators. Angular's own guide describes DI as a pattern used to
  organize and share code across an application by supplying dependencies to
  a class instead of creating them inside it (angular.dev/guide/di, verified
  2026-08-02).
- The Java Database Connectivity API, JDBC, is a long-running, older example
  of the same inversion applied at a platform level. Application code written
  against `java.sql.Connection` and `java.sql.DriverManager` depends only on
  interfaces defined by the Java standard library. a specific database
  vendor's driver, loaded at runtime, supplies the concrete implementation.
  The application module never names the vendor's driver class directly in
  its business logic, which is the same structural shape DIP describes,
  predating the SOLID acronym's popularization and demonstrating the pattern
  was already in wide industrial use in the 1990s.

## 10. Consequences

Positive.

- The high-level, policy-carrying module can be compiled, tested, and
  reasoned about without the concrete low-level implementation existing or
  running, which is the direct enabler of fast, isolated unit tests described
  in dimension 15.
- A new implementation of the abstraction, such as a new payment provider or
  a new storage backend, can be added without modifying the high-level module
  at all, satisfying the Open-Closed Principle at the seam where the
  abstraction lives.
- The high-level module's stability is protected from churn in the low-level
  module. A change to how a detail is implemented, such as switching HTTP
  libraries, does not force a recompile or retest of the business logic that
  merely calls through the abstraction.
- Multiple high-level modules can share one low-level implementation through
  the same abstraction without any of them depending on each other or on the
  concrete class directly, improving reuse without coupling.

Negative.

- Every inverted dependency adds at least one more named type to the
  codebase, and the reader tracing a call must now open the abstraction, then
  find which concrete type is bound to it at the composition root, a hop that
  a direct call does not require. This is the principal cost cited across the
  SOLID literature and is why dimension 4's non-applicability list exists.
- A codebase that inverts dependencies indiscriminately produces what is
  informally called interface-itis in the wider practitioner literature, a
  large number of interfaces with exactly one implementation each, none of
  which is ever actually swapped, each one still requiring a matching edit
  whenever its single implementation's contract changes.
- Debugging becomes harder when the concrete type bound at runtime is not
  obvious from reading the high-level module's source alone, particularly
  once a dependency injection container resolves bindings from configuration
  rather than from code visible at the call site.
- The composition root itself becomes a concentration point of low-level
  knowledge. something, somewhere, must still name every concrete type. DIP
  moves this knowledge to one place rather than removing it, and a poorly
  organized composition root can become its own maintenance burden as the
  object graph grows.

## 11. Failure modes and misuse

The first failure mode is an interface that exists on paper while the
compile-time dependency still points the wrong way. The symptom is that a
consumer can point at an abstraction and claim DIP is satisfied, yet the
high-level module still imports the low-level module's own package to reach
the interface. The cause is that the abstraction was placed in the low-level
module's own package or library instead of the high-level side. The fix is
to move the interface's definition into the high-level module's own package
or a package the high-level side owns, so the low-level module is the one
importing across the boundary to implement it, not the high-level module
importing across the boundary to find the interface.

The second failure mode is interface-itis. The symptom is that every class in
the codebase has a matching one-method interface with exactly one
implementation, and changing a method's signature always means editing two
files instead of one. The cause is that DIP was applied mechanically to every
class rather than at genuine volatility boundaries, following the
non-applicability guidance in dimension 4 in reverse. The fix is to identify
interfaces with a single implementation and no plausible second one, and
collapse them back to a concrete class, reserving interfaces for the
boundaries where a second implementation genuinely exists or is genuinely
planned.

The third failure mode is a test that looks isolated but is not. The symptom
is that a unit test for the high-level module still makes a real network call
or touches a real database, even though the module depends on an interface.
The cause is that the composition root used in the test still wires the real
concrete implementation instead of a fake or a stub, often because the test
was written by copying the production wiring code rather than constructing
the high-level module directly with a test double. The fix is to give the
test its own composition step that constructs the high-level module with a
test double bound to the abstraction, bypassing the production wiring
entirely.

The fourth failure mode is a fat, mechanically extracted interface. The
symptom is that the abstraction has grown to expose every method the
concrete implementation happens to have, rather than only what the
high-level module actually calls. The cause is that the interface was
generated mechanically from the concrete class's public surface, sometimes by
an IDE's extract-interface tool run without editing the result, rather than
designed from the high-level module's actual needs. The fix is the concern
the Interface Segregation Principle addresses directly. trim the abstraction
to the methods the consuming high-level module calls, and split it if two
high-level modules use disjoint subsets.

The fifth failure mode is a substitution that compiles but breaks behavior.
The symptom is that swapping the concrete implementation bound at the
composition root changes the high-level module's observable behavior in a
way that breaks existing callers. The cause is that the new implementation
does not honor the contract the abstraction implies, most often around
exception behavior, null handling, or ordering guarantees that the
interface's type signature does not capture. The fix is that this is a
Liskov Substitution Principle violation riding on top of a correctly
structured DIP boundary. the fix is documenting and testing the
abstraction's behavioral contract, not merely its method signatures, and
holding every implementation to that contract.

The sixth failure mode is an unmanageable composition root. The symptom is
that the composition root has grown into a large, tangled block of manual
object construction that is itself hard to change safely. The cause is that
the object graph outgrew what manual wiring can comfortably express, without
the team introducing a dependency injection container or another organizing
technique to manage it. The fix is to adopt a container once the manual
wiring's own maintenance cost exceeds the cost of learning the container, or
to split the composition root into smaller, named composition functions
grouped by subsystem.

## 12. Trade-off matrix

| Force | Dependency Inversion Principle | Service Locator pattern | Direct concrete coupling (no abstraction) |
|---|---|---|---|
| Compile-time coupling of high-level module to low-level detail | None. high-level module depends only on the abstraction it owns | None on the concrete type, but the module still depends on the locator itself, which is a form of coupling to an infrastructure-wide singleton | Full. the high-level module names the concrete type directly |
| Visibility of a module's real dependencies | High. every dependency appears in the constructor or a designated injection point | Low. a module can call the locator for anything, so its true dependencies are hidden inside its method bodies, a criticism Martin Fowler raises directly against Service Locator in the January 2004 article cited in the references | High in one sense, the import is visible, but the dependency is on a specific implementation, not an abstraction the caller can vary |
| Ease of unit testing in isolation | High. a test double is passed at construction, no global state to configure | Lower. a test must configure or reset the locator's global registry before and after each test to avoid cross-test contamination | Low. the concrete dependency runs for real unless the test resorts to runtime patching |
| Up-front design cost | Moderate. requires designing and placing an abstraction at each genuine seam | Low to moderate. requires a locator but no per-dependency interface design discipline | Lowest. write the call, done |
| Risk of hidden or spooky-action-at-a-distance bugs | Low, because the dependency graph is explicit | Higher, because any code with locator access can silently start depending on a new service without changing the module's declared interface | Not applicable in the same sense. the coupling is visible, and fixed |

## 13. Related and incompatible patterns

Strategy. The Strategy pattern is one of the most common concrete shapes DIP
takes at the object level. a high-level context object holds a reference to a
strategy interface, and concrete strategies implement it. Where DIP is the
principle describing the direction dependencies should point, Strategy is the
object-oriented pattern that most directly implements it for interchangeable
algorithms or policies.

Factory Method and Abstract Factory. Both patterns exist to solve a problem
DIP creates. something has to construct the concrete implementation that gets
bound to the abstraction, and a factory is a common place to put that
construction so the high-level module still never names the concrete type. A
factory used this way is frequently part of, or adjacent to, the composition
root described in dimension 7.

Adapter. When an existing, unmodifiable third-party class does not already
implement the abstraction a high-level module needs, an Adapter class wraps
it to satisfy that abstraction. The adapter is the low-level module in DIP's
structure. it depends on and implements the abstraction, while internally
depending on the third-party class it wraps.

Interface Segregation Principle. ISP governs the shape of the abstraction DIP
requires. A DIP boundary built around a fat interface that exposes far more
than any single high-level module needs invites the failure mode described in
dimension 11. ISP's guidance to keep interfaces narrow and client-specific is
what keeps a DIP abstraction healthy over time.

Open-Closed Principle. OCP's promise, that a module can be extended without
modifying its existing source, is realized at a DIP boundary. Adding a new
concrete implementation of the abstraction is the extension. the high-level
module that depends only on the abstraction is the part that remains closed
to modification.

Liskov Substitution Principle. DIP arranges the direction of dependencies
correctly, but says nothing about whether every implementation actually
behaves the way the abstraction's contract implies. LSP is the principle that
governs correctness of substitution once DIP has made substitution
structurally possible, and a DIP boundary with an LSP violation underneath it
produces the failure mode described in dimension 11's fifth entry.

Single Responsibility Principle. SRP and DIP are not the same axis but
frequently co-occur. a module that has been split along SRP's lines, so that
it has one reason to change, is also the natural place to apply DIP, because a
single-responsibility module has a small, coherent set of dependencies that
are easy to name in one abstraction rather than a sprawling one.

No pattern in this catalog is structurally incompatible with DIP. The
principle constrains a relationship's direction rather than prescribing a
specific structure, so it composes with nearly any pattern that involves
one module depending on another.

## 14. Refactoring path in and out

Introducing DIP into code that lacks it follows this sequence.

1. Identify a high-level module that currently constructs or directly calls a
   concrete low-level class, and confirm against dimension 4 that a genuine
   volatility, testing, or reuse need exists. do not proceed on ceremony
   alone.
2. List only the methods the high-level module actually calls on the
   concrete class. This list becomes the initial shape of the abstraction,
   keeping it narrow from the start rather than extracting the concrete
   class's full public surface.
3. Define the abstraction, an interface, protocol, or abstract base type, in
   a package or module the high-level side owns, not inside the low-level
   module's own package.
4. Make the existing concrete class implement the new abstraction. In most
   languages this requires no change to the concrete class's behavior, only a
   declaration that it satisfies the interface's shape.
5. Change the high-level module's constructor, or an equivalent injection
   point, to accept the abstraction instead of constructing or directly
   naming the concrete type. Remove the direct import of the concrete class
   from the high-level module.
6. Introduce, or extend, a composition root that constructs the concrete
   implementation and passes it into the high-level module's constructor.
   For an existing codebase this is often as small as one line near the
   program's existing entry point.
7. Add or update a unit test for the high-level module that passes a fake or
   stub implementation of the abstraction at step 5, and delete any
   workaround the tests previously used, such as an in-memory test database
   or a runtime patch of the concrete class, that this abstraction now makes
   unnecessary.

This sequence mirrors the Extract Interface refactoring, described by Martin
Fowler in Refactoring, Improving the Design of Existing Code, 2nd edition,
Addison-Wesley, 2018, combined with a change to the constructor signature that
some catalogs describe separately as Introduce Parameter or Change Function
Declaration.

Removing DIP when it stops earning its place follows this sequence.

1. Confirm the abstraction genuinely has, and has had for some time, exactly
   one implementation, with no second implementation planned and no test
   currently substituting a fake for it.
2. Search the codebase for every place the abstraction's type is referenced
   and confirm each one only ever receives the single concrete type at its
   composition root.
3. Inline the concrete type into every place that previously referenced the
   abstraction, replacing the abstraction's type in constructor parameters
   and field declarations with the concrete type directly.
4. Remove the interface or abstract type declaration itself, and remove the
   implements or equivalent declaration from the concrete class.
5. Re-run the module's tests. If a test relied on substituting a fake
   implementation for genuine isolation value, this step is the signal that
   the removal was premature. restore the abstraction and address the actual
   design problem the fake was solving instead.

## 15. Testing and verification

Code built around a DIP boundary is easier to test in exactly one specific
way. the high-level module's tests can substitute a test double for the
low-level dependency at construction time, without any change to the
high-level module's source and without any interception, patching, or mocking
framework operating on a concrete class the module did not declare a
dependency on. This is the payoff described in the forces section, made
concrete.

The test double substituted at the abstraction can be a hand-written fake
that records calls and returns canned results, a stub that returns a fixed
value regardless of input, or a mock generated by a library that asserts
specific calls occurred, depending on what the test needs to verify. Because
the high-level module depends only on the abstraction's declared methods,
any of these three kinds of double can satisfy the same interface without
the high-level module's code changing at all.

What becomes harder is verifying that a given concrete implementation
actually satisfies the abstraction's full behavioral contract, not merely its
method signatures. A compiler or type checker confirms the signatures match.
it does not confirm that a new payment gateway implementation throws the same
exception type on a declined charge that the abstraction's existing
implementations do, or that it honors the same ordering guarantee. This is
the concern the Liskov Substitution Principle addresses, and the standard
technique for verifying it at a DIP boundary is a shared contract test suite.
one set of behavioral tests, written once against the abstraction, that every
concrete implementation must pass. Each new implementation runs the same
suite, catching a substitution violation before it reaches production rather
than after.

A second thing to verify explicitly is the composition root itself. Because
the wiring code is where every concrete type is finally named, an integration
or smoke test that exercises the fully wired object graph, using the real
concrete implementations, at least once, catches wiring mistakes, such as an
abstraction bound to the wrong concrete type, that a unit test using a fake
would never surface, because the unit test never touches the composition root
at all.

## 16. Observability signals

A DIP boundary itself produces no runtime signal distinct from whatever the
concrete implementation behind it emits. the abstraction is a compile-time and
design-time construct, not a runtime one, so observability at a DIP boundary
is really observability of the composition root's decisions and of the
concrete implementation currently bound.

What is worth logging or tracing at the composition root is which concrete
implementation was bound to each abstraction at startup, particularly in
systems where the binding is chosen from configuration rather than fixed in
code, such as choosing a storage backend by an environment variable. A
misconfigured binding, where the wrong concrete type is wired in a given
environment, is a class of production incident that is invisible from the
high-level module's own logs, because the high-level module correctly calls
through the abstraction regardless of which concrete type answers. the
binding decision is the only place the mistake is visible.

A healthy system exhibits a small, stable, and well-understood number of
concrete bindings per abstraction, visible in a single composition root or a
small number of well-organized composition functions, with each binding's
choice traceable to an explicit configuration value or an explicit code path
rather than to implicit ordering or a reflection-based scan that could pick
up an unintended implementation. A failing or degrading system shows signs
such as an abstraction unexpectedly resolving to a different concrete type
than the one a runbook or deployment manifest expects, or a dependency
injection container throwing a resolution error at startup because no
concrete type was registered for an abstraction a high-level module requires,
both of which should surface as loud, early failures at process start rather
than as a silent fallback or a null reference deep inside a request path.

## 17. Security and privacy implications

DIP itself is a structural principle about the direction of source-level
dependencies and carries no inherent data-handling behavior, so it neither
opens nor closes an attack surface by itself. Its security-relevant effect is
indirect, through the composition root, and is analytical rather than a
sourced claim.

Because the composition root is the single place every concrete
implementation is named and bound, it is also the natural place to enforce
which concrete implementations are permitted to be wired at all in a given
deployment, for example so a production environment can never accidentally
bind a debug or in-memory implementation of a credential store in place of
the real one. Concentrating this decision in one reviewable
location is a benefit for security review, compared to a codebase where
concrete security-sensitive classes could be constructed from many scattered
call sites.

The same concentration is a risk if the composition root resolves bindings
from untrusted or externally influenced configuration, such as a
plugin-loading mechanism that reads a class name from a request parameter or
an unauthenticated configuration source and instantiates it as the concrete
implementation for an abstraction. This is a form of insecure deserialization
or arbitrary object instantiation risk, and it exists at the composition
root regardless of whether DIP is in use. DIP does not introduce this risk,
but a codebase that inverts many dependencies and resolves many bindings from
configuration has more surface area where this class of misconfiguration
could occur, simply because there are more bindings to get wrong.

Dependency injection containers that use reflection to scan an assembly or
package for classes implementing an abstraction, rather than requiring an
explicit registration, can silently pick up an unintended implementation
placed anywhere in the scanned scope, including a test double or a malicious
class introduced through a compromised dependency. Explicit registration at
the composition root, naming each concrete type rather than relying on a
scan, closes this specific risk at a small cost in verbosity.

## 18. References

- Robert C. Martin. "The Dependency Inversion Principle." C++ Report, June
  1996. Original article date and the principle's two rules confirmed via
  "Dependency inversion principle." Wikipedia.
  https://en.wikipedia.org/wiki/Dependency_inversion_principle (verified
  2026-08-02).
- Robert C. Martin. Agile Software Development, Principles, Patterns, and
  Practices. Prentice Hall, 2002. Chapter 11, "The Dependency-Inversion
  Principle."
- Robert C. Martin. Clean Architecture, A Craftsman's Guide to Software
  Structure and Design. Prentice Hall, 2017. The Dependency Rule, chapters 22
  through 23.
- Martin Fowler. "Inversion of Control Containers and the Dependency
  Injection pattern." martinfowler.com, 23 January 2004.
  https://martinfowler.com/articles/injection.html (verified 2026-08-02).
- Martin Fowler. Refactoring, Improving the Design of Existing Code, 2nd
  edition. Addison-Wesley, 2018.
- Mark Seemann and Steven van Deursen. Dependency Injection Principles,
  Practices, and Patterns. Manning Publications, 2019.
- Spring Framework Reference Documentation. "Dependencies." docs.spring.io.
  https://docs.spring.io/spring-framework/reference/core/beans/dependencies.html
  (verified 2026-08-02).
- Microsoft Learn. "Dependency injection, .NET." learn.microsoft.com.
  https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection
  (verified 2026-08-02, page last updated per page metadata 2026-04-23).
- Angular documentation. "Dependency injection in Angular." angular.dev.
  https://angular.dev/guide/di (verified 2026-08-02).

## Code examples

Every example implements the same scenario. an `OrderProcessor` that needs to
send a notification when an order is placed, without depending on how the
notification is actually delivered. Two concrete senders, email and SMS, both
satisfy the same abstraction. All three examples were compiled or run
directly. output is shown after each listing.

### TypeScript

```typescript
interface NotificationSender {
  send(recipient: string, message: string): void;
}

class EmailSender implements NotificationSender {
  send(recipient: string, message: string): void {
    console.log(`EMAIL to ${recipient}: ${message}`);
  }
}

class SmsSender implements NotificationSender {
  send(recipient: string, message: string): void {
    console.log(`SMS to ${recipient}: ${message}`);
  }
}

class OrderProcessor {
  constructor(private readonly sender: NotificationSender) {}

  placeOrder(customer: string, orderId: string): void {
    this.sender.send(customer, `Order ${orderId} confirmed.`);
  }
}

const byEmail = new OrderProcessor(new EmailSender());
byEmail.placeOrder("jane@example.com", "A1001");

const bySms = new OrderProcessor(new SmsSender());
bySms.placeOrder("+15551234", "A1002");
```

Compiled with `npx tsc` (version 7.0.2) targeting ES2020 with CommonJS
modules, then run under Node.js. Output.

```
EMAIL to jane@example.com: Order A1001 confirmed.
SMS to +15551234: Order A1002 confirmed.
```

`OrderProcessor` never imports `EmailSender` or `SmsSender`. It depends only
on the `NotificationSender` interface, which it owns. both senders are
low-level modules that implement it. A test can substitute a third class,
never shown here, that implements `NotificationSender` and records calls
instead of printing them, with no change to `OrderProcessor` at all.

### Python

```python
from abc import ABC, abstractmethod


class NotificationSender(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> None:
        raise NotImplementedError


class EmailSender(NotificationSender):
    def send(self, recipient: str, message: str) -> None:
        print(f"EMAIL to {recipient}: {message}")


class SmsSender(NotificationSender):
    def send(self, recipient: str, message: str) -> None:
        print(f"SMS to {recipient}: {message}")


class OrderProcessor:
    def __init__(self, sender: NotificationSender) -> None:
        self._sender = sender

    def place_order(self, customer: str, order_id: str) -> None:
        self._sender.send(customer, f"Order {order_id} confirmed.")


if __name__ == "__main__":
    OrderProcessor(EmailSender()).place_order("jane@example.com", "A1001")
    OrderProcessor(SmsSender()).place_order("+15551234", "A1002")
```

Run directly with `python3`. Output.

```
EMAIL to jane@example.com: Order A1001 confirmed.
SMS to +15551234: Order A1002 confirmed.
```

Python's `abc.ABC` and `@abstractmethod` give `NotificationSender` a
structural, enforced abstraction rather than a purely conventional one. a
class that inherits from `NotificationSender` without implementing `send`
cannot be instantiated. `OrderProcessor` accepts a `NotificationSender` in
its constructor and stores nothing about which concrete class was supplied.

### Go

```go
package main

import "fmt"

type NotificationSender interface {
	Send(recipient, message string)
}

type EmailSender struct{}

func (EmailSender) Send(recipient, message string) {
	fmt.Printf("EMAIL to %s: %s\n", recipient, message)
}

type SmsSender struct{}

func (SmsSender) Send(recipient, message string) {
	fmt.Printf("SMS to %s: %s\n", recipient, message)
}

type OrderProcessor struct {
	sender NotificationSender
}

func NewOrderProcessor(sender NotificationSender) *OrderProcessor {
	return &OrderProcessor{sender: sender}
}

func (p *OrderProcessor) PlaceOrder(customer, orderID string) {
	p.sender.Send(customer, fmt.Sprintf("Order %s confirmed.", orderID))
}

func main() {
	NewOrderProcessor(EmailSender{}).PlaceOrder("jane@example.com", "A1001")
	NewOrderProcessor(SmsSender{}).PlaceOrder("+15551234", "A1002")
}
```

Run with `go run main.go`. Output.

```
EMAIL to jane@example.com: Order A1001 confirmed.
SMS to +15551234: Order A1002 confirmed.
```

Go has no `implements` keyword. `EmailSender` and `SmsSender` satisfy
`NotificationSender` structurally, purely by having a matching `Send` method,
which is Go's own idiomatic expression of the same inversion. `OrderProcessor`
is constructed through `NewOrderProcessor`, a small factory function that
plays the role of part of the composition root described in dimension 7.

Java and Rust were not included as a fourth example here. the pattern is not
meaningfully different in either language from the Go and TypeScript
listings above, an interface or trait plus constructor injection, and a
fourth near-identical listing would not add depth beyond what the three
languages above already demonstrate.
