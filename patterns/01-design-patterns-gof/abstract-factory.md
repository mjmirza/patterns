---
name: Abstract Factory
slug: abstract-factory
family: 01-design-patterns-gof
category: Creational
aliases: [Kit, Toolkit, Factory of Factories, Product Family Factory]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [factory-method, builder, prototype, singleton, bridge, facade]
incompatible_with: []
verified: 2026-08-02
---

# Abstract Factory

## 1. Name, aliases, and lineage

The canonical name is Abstract Factory. It was published among the creational
patterns of the Gang of Four catalog, where the pattern write-up begins at page 87
and the stated intent is to provide an interface for creating families of related
or dependent objects without specifying their concrete classes (Gamma, Helm,
Johnson, Vlissides, *Design Patterns. Elements of Reusable Object-Oriented
Software*, Addison-Wesley, 1994, Chapter 3 Creational Patterns, Abstract Factory,
page 87. The intent wording and the five participant names AbstractFactory,
ConcreteFactory, AbstractProduct, ConcreteProduct, and Client are reproduced in
the publisher's authorized excerpt at
https://www.informit.com/articles/article.aspx?p=1398599, verified 2026-08-02).

Aliases in real use.

- **Kit**, listed as the alternative name in the original catalog entry and still
  seen in older C++ and Smalltalk windowing code.
- **Toolkit**, used in the AWT lineage where the abstract factory type is
  literally named `Toolkit`
  (https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Toolkit.html,
  verified 2026-08-02).
- **Factory of Factories**, a colloquial teaching name that describes the shape
  rather than the intent, and which misleads readers into thinking the pattern
  returns factories. It returns products.

The name is contested in one specific way. Many developers use "abstract factory"
loosely for any type with a static `create` method that hides a concrete class.
That is Factory Method, or a plain static creation function, and it lacks the
defining property of this pattern, which is a **family** of several product types
produced consistently by one object.

## 2. Problem and context

You have several product types that must vary together. A rendering layer needs a
Button, a Checkbox, and a ScrollBar. A persistence layer needs a Connection, a
Command, and a Parameter. A payment layer needs an AuthorizationClient, a
RefundClient, and a WebhookVerifier.

Two properties turn this into a real problem.

First, the concrete types come in **matched sets**. A macOS Button paired with a
Windows ScrollBar produces a broken window. A PostgreSQL `DbCommand` handed to a
SQL Server `DbConnection` throws at runtime rather than at compile time. The
combinations are not free, and nothing in a plain constructor call prevents a
caller from mixing them.

Second, the choice of set is made **once, far from the call sites**. It is read
from configuration, from a build flag, from a detected operating system, or from a
tenant record. The hundreds of places that construct products should never repeat
that decision, and should not carry a conditional for every set.

The context in which this matters is a system where the number of product types in
a family is small and stable, and the number of families is expected to grow.
Outside that context the pattern is an anti-pattern, because the whole cost of
Abstract Factory is paid to make new families cheap, and it is charged even when
no second family ever ships.

You can recognise the problem in your own code by these symptoms.

- A `switch` on a platform, driver, or tenant value repeated in more than three
  files.
- A bug report reading "works on Postgres, blows up on MySQL" that traces to one
  object built with the wrong concrete class.
- A constructor call chain where an object of family A is passed into a method
  that silently expects family B.

## 3. Forces

| Force | Effect of Abstract Factory |
|---|---|
| Coupling | Favoured. Client code depends on abstract product interfaces and on one factory interface, never on concrete product classes. |
| Family consistency | Favoured, and this is the pattern's reason to exist. One factory instance can only emit one family, so a mismatched pair is unrepresentable. |
| Extensibility along families | Favoured. Adding a new family means adding one concrete factory and its products, with no edit to client code. |
| Extensibility along products | Sacrificed. Adding a new product type to the family changes the factory interface and forces an edit in every concrete factory. This asymmetry is the pattern's defining cost. |
| Cognitive load | Sacrificed. A reader tracing "where does this Button come from" now walks through an interface, a wiring point, and a concrete factory. |
| Latency | Neutral to mildly negative. One virtual dispatch per creation, plus one indirection at wiring time. Negligible outside allocation-heavy inner loops. |
| Cost and operability | Mildly favoured. The set of supported families becomes an explicit, listable, testable artifact rather than scattered conditionals. |
| Team topology | Favoured. Each family can be owned end to end by a separate team behind a stable interface, which is why database drivers and cloud SDK backends ship this way. |
| Consistency of configuration | Mildly sacrificed. The family selection becomes a runtime value, so a typo in configuration surfaces at startup rather than at compile time unless the selection is validated eagerly. |

## 4. Applicability and non-applicability

Reach for it when all of the following hold.

- Two or more product types must always come from the same family, and mixing them
  is a defect rather than a feature.
- The family is selected once, at composition time, and every later creation must
  respect that choice.
- The set of product types in the family is small and expected to stay small.
- You expect to add families over time, or a third party is expected to add them.
- Client code should compile without a reference to any concrete family.

Do NOT reach for it when any of the following holds.

- **There is exactly one family and no second one is planned.** You are paying the
  full interface cost for an indirection with one implementation. Construct
  directly and extract the factory later, when the second family arrives.
- **The product types do not need to vary together.** If a Button and a Logger can
  be chosen independently, one factory that produces both wrongly couples two
  unrelated decisions. Use two separate Factory Methods or plain dependency
  injection.
- **New product types are added often.** Every addition breaks the factory
  interface and every implementor of it. Prefer a registry keyed by product type,
  a Service Locator, or a Prototype registry that clones a configured exemplar.
- **The family is one product.** That is Factory Method, and calling it Abstract
  Factory adds a name and an interface for nothing.
- **The language gives you first-class modules or functions that already do the
  job.** In Go, a struct of function fields, and in Python a module object or a
  frozen dataclass of callables, express the same guarantee with far less
  ceremony. See dimension 8.
- **Products need constructor arguments that differ per call site.** The factory
  interface then grows a parameter list that leaks the concrete needs of one family
  into the abstraction. Builder handles per-instance configuration better.
- **You are chasing testability alone.** Constructor injection of the already built
  collaborators is simpler, and does not force a family abstraction on code that
  has no families.

## 5. Structure

Participants named by the role each plays.

- **FamilyFactory** (the AbstractFactory role). Declares one creation operation per
  product type in the family. It declares no operation that reveals which family it
  belongs to, because the client must not branch on that.
- **ConcreteFamilyFactory** (the ConcreteFactory role). One per family. Implements
  every creation operation, and is the only place in the system that names the
  concrete product classes of its family. Frequently a stateless singleton, because
  it holds no per-call state.
- **ProductRole** (the AbstractProduct role). One abstract type per product slot in
  the family. It is the only type a client sees. The family's identity is
  deliberately absent from it.
- **FamilyProduct** (the ConcreteProduct role). One implementation per product role
  per family. Members of one family may know about each other and may rely on
  family-specific invariants, which is exactly the guarantee the factory buys.
- **Client**. Holds a FamilyFactory reference and calls creation operations. It is
  written once against the abstract types and never edited when a family is added.
- **Selector** (not in the original catalog, universal in practice). The code that
  decides which ConcreteFamilyFactory to hand to the Client. Reads configuration, a
  service loader entry, an operating system probe, or a tenant record. Isolating
  the Selector is what keeps the family decision to a single place.

The relationships. Client holds one FamilyFactory. FamilyFactory declares
operations returning ProductRole types. Each ConcreteFamilyFactory implements
FamilyFactory and instantiates only the FamilyProduct types of its own family. Each
FamilyProduct implements exactly one ProductRole. The Selector creates exactly one
ConcreteFamilyFactory and hands it to the Client.

## 6. ASCII structure diagram

```
                   +-------------------------+
   Selector ------>|     FamilyFactory       |<-------- Client
   (config,        |  (interface)            |          (depends only
    OS probe,      |-------------------------|           on the abstract
    tenant row)    | createButton()          |           types)
        |          | createScrollBar()       |
        |          +-------------------------+
        |                     ^
        |          implements | implements
        |          +----------+----------+
        |          |                     |
        v   +--------------------+  +--------------------+
   creates  | AquaFactory        |  | Win32Factory       |
   exactly  |--------------------|  |--------------------|
   one ---->| createButton()     |  | createButton()     |
            | createScrollBar()  |  | createScrollBar()  |
            +--------------------+  +--------------------+
                 |         |             |         |
        creates  |         | creates     |         |
                 v         v             v         v
        +-----------+ +-------------+ +-----------+ +-------------+
        | AquaButton| |AquaScrollBar| |Win32Button| |Win32ScrollBr|
        +-----------+ +-------------+ +-----------+ +-------------+
              |             |               |             |
              v             v               v             v
        +-----------+ +-------------+ +-----------+ +-------------+
        |  Button   | | ScrollBar   | |  Button   | | ScrollBar   |
        | (abstract)| | (abstract)  | | (abstract)| | (abstract)  |
        +-----------+ +-------------+ +-----------+ +-------------+
              ^                             ^
              |   the Client sees only      |
              +-----------------------------+
                     these two types

   Vertical axis, product roles. Horizontal axis, families.
   Adding a family adds a column, cheap. Adding a product role adds
   a row, and that row must be filled in every existing column.
```

## 7. Dynamics

Two flows matter. The wiring flow runs once. The creation flow runs many times and
never re-decides the family.

```
  Wiring, once at startup
  ----------------------------------------------------------------
  Bootstrap        Selector          AquaFactory        Client
     |                |                   |               |
     |-- start() ---->|                   |               |
     |                |-- read config --> |               |
     |                |   "aqua"          |               |
     |                |-- new() --------->|               |
     |                |<-- factory -------|               |
     |<-- factory ----|                   |               |
     |------------------ new Client(factory) ------------>|
     |                |                   |               |

  Creation, many times per second
  ----------------------------------------------------------------
  Caller           Client           AquaFactory      AquaButton
     |                |                   |               |
     |-- render() --->|                   |               |
     |                |-- createButton()->|               |
     |                |                   |-- new() ----->|
     |                |                   |<-- instance --|
     |                |<-- Button --------|               |
     |                |                                   |
     |                |-- createScrollBar() -> AquaFactory |
     |                |<-- ScrollBar ---------------------|
     |                |                                   |
     |   The Client never learns that the concrete types
     |   are Aqua. No branch on family exists past the
     |   Selector. The two products are guaranteed to be
     |   from the same family because they came from the
     |   same factory instance.
     |<-- rendered ---|
```

The invariant that carries the whole pattern. Family consistency is enforced by
**object identity of the factory**, not by a check. One factory instance cannot
produce a member of a family it does not implement, so no validation code is
needed and no test can exercise the mismatch case, because it is unrepresentable.

## 8. Implementation variants

**Interface plus concrete classes.** The catalog form. One interface, one class per
family. Best when families are compiled in and known ahead of time. Cost is class
count, which is families multiplied by product roles plus the interfaces.

**Factory as a record of closures.** Replace the interface with a struct or a
record whose fields are functions returning each product role. In Go this is the
idiomatic shape, because there is no implementation inheritance and an interface
holding only constructors reads as ceremony. In TypeScript and Python it removes a
class per family. Trade-off, you lose the family name a debugger would print, and a
partially built record is a valid value, so a missing field becomes a nil
dereference at first use rather than a compile error unless the language checks
exhaustiveness.

**Prototype-backed factory.** The concrete factory holds one fully configured
exemplar per product role and clones it on each request, rather than calling a
constructor. This is the variant the original catalog suggests when the number of
families would otherwise explode, because a single generic factory parameterised by
its exemplars replaces N concrete factory classes. Trade-off, clone semantics must
be correct and deep enough, and the exemplars become mutable shared state if a
clone is shallow.

**Reflective or service-loaded factory.** One generic factory reads a class name or
a provider identifier at runtime and instantiates the family through reflection or
a service loader. This is how JAXP and ADO.NET ship, because third parties must add
families without recompiling the platform. It is the only variant that supports
families the original author never saw. Trade-off, every error moves from compile
time to startup time, ahead-of-time compilation and tree shaking cannot see the
dependency edge, and the .NET API documents this explicitly by attributing
`DbProviderFactory` with `DynamicallyAccessedMembers` so the trimmer preserves what
reflection needs
(https://learn.microsoft.com/en-us/dotnet/api/system.data.common.dbproviderfactory,
verified 2026-08-02).

**Generic or type-parameterised factory.** In Rust, a trait with associated types
lets one trait describe the whole family, and the compiler enforces that a given
implementor's products belong together, because the associated types are fixed per
implementor. This is the strongest static form of the pattern, and it is why Rust
code often does not name the pattern at all. Trade-off, monomorphisation means the
family must be known at compile time unless you erase to trait objects, and
associated types cannot be used behind a `dyn` reference without extra work.

**Abstract class with defaults.** The factory is an abstract class rather than an
interface, and supplies a default implementation for the product roles that most
families share. Reduces duplication when families differ in only two of six
products. Trade-off, a default that is wrong for a new family is inherited
silently, which is the classic fragile base class problem.

**Configured single factory.** One concrete factory holds a small enum or table and
switches internally. This is not the pattern, it is the conditional the pattern
replaces, moved to one file. It is the right answer for exactly two families that
will never grow, and it is worth naming so that a reviewer can choose it
deliberately rather than drift into it.

## 9. Known production uses

**JAXP `DocumentBuilderFactory` in the Java SE platform.** The class is documented
as defining a factory API that lets applications obtain a parser producing DOM
trees, `newInstance()` resolves the implementation through the JAXP lookup
mechanism, and `newDocumentBuilder()` returns a parser built from the currently
configured parameters. The configuration state carried on the factory, for example
namespace awareness and validation, is what makes every product it emits a
consistent member of one family
(https://docs.oracle.com/en/java/javase/21/docs/api/java.xml/javax/xml/parsers/DocumentBuilderFactory.html,
verified 2026-08-02).

**ADO.NET `System.Data.Common.DbProviderFactory`.** Documented as representing a
set of methods for creating instances of a provider's implementation of the data
source classes. The family is explicit in the method list, `CreateConnection`,
`CreateCommand`, `CreateParameter`, `CreateDataAdapter`,
`CreateConnectionStringBuilder`, `CreateBatch`, and the concrete families ship as
`SqlClientFactory`, `OdbcFactory`, `OleDbFactory`, and `OracleClientFactory`. The
`CanCreateBatch` and `CanCreateDataAdapter` properties are a real-world admission
of the row-addition cost described in dimension 3, because a product role added
later cannot be required of every existing family
(https://learn.microsoft.com/en-us/dotnet/api/system.data.common.dbproviderfactory,
verified 2026-08-02).

**`java.awt.Toolkit` in the Java SE desktop module.** Documented as the abstract
superclass of all actual implementations of the Abstract Window Toolkit, whose
subclasses bind the various components to particular native toolkit
implementations, and whose methods are the glue joining the platform-independent
`java.awt` classes to their `java.awt.peer` counterparts. This is the windowing
example from the original catalog shipped as a platform API, one family per native
windowing system
(https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Toolkit.html,
verified 2026-08-02).

## 10. Consequences

Positive.

- Concrete product classes are named in exactly one file per family, so swapping a
  family is a wiring change rather than a code change.
- Mismatched product combinations become unrepresentable rather than merely
  discouraged, which removes a whole defect class without a runtime check.
- A family becomes a unit of ownership, review, and release. A driver team ships a
  factory and its products without touching the platform.
- Client code becomes testable against a fake family that is a peer of the real
  ones, not a special case.
- The supported family set is enumerable, which makes capability reporting,
  documentation, and compatibility matrices mechanical.

Negative.

- Adding a product role is expensive and breaking. Every concrete factory must be
  edited, including ones owned by third parties. Real platforms respond with
  capability flags or default implementations, both of which weaken the guarantee.
- Class and file count grows as families multiplied by product roles.
- The construction path gains indirection, which lengthens stack traces and makes
  "which concrete type is this" a debugger question rather than a reading question.
- Reflective and service-loaded variants defer all binding errors to startup and
  defeat static analysis, dead code elimination, and ahead-of-time compilation.
- The abstraction constrains every family to the least capable one. A product role
  that one family could expose richly must be narrowed to what all families can
  honour, or the client starts downcasting, which destroys the pattern.

## 11. Failure modes and misuse

**Downcasting at the call site.** A caller needs a family-specific capability, so it
writes a type test on the returned product. The symptom is a chain of `if x is
SqlCommand` branches drifting back into client code, and a new family failing at
runtime because none of the branches match. The pattern has been reduced to a
verbose conditional. The fix is to move the capability behind a product role
operation, or to accept that the families are not substitutable and stop pretending
they are.

**The exploding interface.** Every new feature adds a creation method. The symptom
is a factory interface with twenty methods and concrete factories that throw
`NotSupportedException` from half of them. Visible directly in the .NET API, which
added `CanCreateBatch` and similar probes rather than break implementors. The fix is
to split the family, or to move to a registry keyed by product type.

**Two factories in flight.** A refactor introduces a second injection point, and one
component receives family A while its collaborator receives family B. The symptom is
an error deep in a product interaction, for example a parameter object rejected by a
command object, with a message that names neither factory. This is the exact failure
the pattern exists to prevent, reintroduced by wiring. The fix is a single
composition root and a startup assertion that all factory-derived singletons share
one factory identity.

**Family selected per call rather than per composition.** A helper reads
configuration inside the creation method, so the family can change between two calls
in one request. The symptom is intermittent mismatched pairs under configuration
reload, unreproducible in test. The fix is to snapshot the factory for the lifetime
of the unit of work.

**Singleton factory holding mutable state.** A shared factory instance caches a
product or a connection. The symptom is a data race or a leaked authentication
context between tenants. Concrete factories should be stateless, or their state
should be immutable configuration set before publication.

**Premature abstraction.** One family, one implementation, a full interface, and a
Selector reading a configuration key that only ever has one legal value. The symptom
is a code review comment asking what the second implementation is, and no answer.
The cost was paid, the benefit never arrived.

**Reflection plus trimming.** A service-loaded factory works in development and
fails in a trimmed or ahead-of-time compiled build with a missing type error. The
symptom is an exception naming a class that is present in source and absent from the
artifact. The fix is the annotation the .NET API applies, or an explicit
registration table that the compiler can see.

## 12. Trade-off matrix

Alternatives are named patterns and named language mechanisms, each of which a
competent engineer would genuinely consider for the same problem.

| Force | Abstract Factory | Factory Method | Builder | Prototype registry | Service Locator | Dependency Injection container |
|---|---|---|---|---|---|---|
| Family consistency guarantee | Enforced by factory identity | None, each method is independent | None, per-object | Conventional, depends on registry discipline | None, keys are independent | Configurable, enforced by container scope rules |
| Cost of adding a family | One class per family | One override per product | Not applicable | One exemplar set | One registration set | One module or profile |
| Cost of adding a product role | High, breaks the interface and every implementor | Low, one new method on the creator | Low | Low, one more exemplar key | Low, one more key | Low |
| Coupling of client to concrete types | None | None | None for the product, some for the builder | None | None at compile time, high at runtime by key | None |
| Static checkability | High in the interface form, low in the reflective form | High | High | Low, keys are strings or types | Low, a missing key fails at runtime | Medium, container graph validated at startup |
| Per-instance configuration | Poor, arguments leak into the interface | Poor | The reason it exists | Good, via exemplar variation | Poor | Good |
| Cognitive load | Medium to high | Low | Medium | High, clone semantics are subtle | Low to write, high to debug | High, wiring is implicit |
| Latency at creation | One virtual call | One virtual call | Multiple calls, one object | Clone cost, may exceed construction | Map lookup plus virtual call | Resolution cost, often cached |
| Operability, listing what is supported | Trivial, enumerate factories | Hard, scattered | Not applicable | Trivial, enumerate registry | Trivial, enumerate keys | Trivial, dump the graph |
| Suits third-party extension | Yes, the main reason platforms pick it | Weakly | No | Yes | Yes | Yes |

Reading the table. Abstract Factory wins on exactly one axis that no alternative
matches, the family consistency guarantee carried by factory identity, and loses on
the product role axis to every alternative. Choose it when the first column is worth
the third row, and choose something else otherwise.

## 13. Related and incompatible patterns

**Factory Method.** Not an alternative so much as a component. Concrete factories
are very often implemented by making each creation operation a Factory Method on a
subclass, which is how the original catalog presents the relationship. The
distinction to hold is scope, one product for Factory Method, a family for Abstract
Factory. A single-product Abstract Factory should be renamed.

**Prototype.** Composes as an implementation strategy. A concrete factory that
clones configured exemplars rather than calling constructors collapses N concrete
factory classes into one parameterised class. Use this when family count grows
faster than product role count.

**Singleton.** Composes almost always. Concrete factories carry no per-call state,
so one instance per family is the natural lifetime. This is a composition, not a
requirement, and it becomes a failure mode the moment the factory caches anything
mutable, per dimension 11.

**Builder.** Complementary and frequently confused. Abstract Factory answers which
family, Builder answers how this particular instance is configured. They compose
cleanly, a factory operation returning a family-specific Builder, and they conflict
when a team tries to make one type answer both questions, at which point the factory
interface grows per-instance parameters and stops being an abstraction.

**Bridge.** Solves an adjacent problem with a different shape. Bridge separates an
abstraction from its implementation so both vary, and it is the better answer when
there is one product type with two independent axes of variation. Abstract Factory
is the better answer when there are several product types with one shared axis.
Systems often carry both, with a factory producing the implementation side of a
Bridge.

**Facade.** Frequently sits in front of an Abstract Factory so that the Selector and
the factory itself are hidden from application code entirely.

**Dependency Injection container.** Overlaps enough to replace the pattern in many
applications. A container can hold the family selection as a scope or a profile and
inject already built products, which removes the factory interface. It does not
replace it in a **library** whose consumers use different containers or none, which
is why platform APIs keep the explicit factory. Using both, a container that
resolves an Abstract Factory, is a common and reasonable arrangement.

**Service Locator.** Actively conflicts. Both centralise creation, but Service
Locator keys products independently, so a locator sitting inside a concrete factory
reintroduces the possibility of a mismatched family and destroys the one guarantee
the pattern provides. If a locator is present, the family must be part of the key,
at which point the locator is a reflective Abstract Factory and should be named as
one.

**Static factory functions on the concrete types.** Actively conflicts. Every static
`SqlCommand.Create()` a caller can reach is a bypass of the factory, and the
guarantee holds only if concrete product constructors are not reachable from client
code. Language visibility, internal or package-private constructors, is the
mechanism that makes the conflict impossible rather than discouraged.

## 14. Refactoring path in and out

Introducing the pattern into code that lacks it. Each step compiles and passes tests
on its own.

1. Find the branch. Locate every conditional on the family value, the platform flag,
   the driver name, or the tenant type. Their union defines the product roles.
2. Extract interfaces for the products. For each concrete type constructed inside
   those branches, introduce an abstract product role and change local variable and
   parameter types to the role. This is Extract Interface, and it is the step that
   does the real work. See `02-refactoring/extract-interface`.
3. Replace direct construction with a creation method. Move each `new` into a method
   on a new class per family, one class per branch arm. This is Replace Constructor
   with Factory Method. See
   `02-refactoring/replace-constructor-with-factory-method`.
4. Extract the factory interface. Pull the union of creation methods into a
   FamilyFactory interface, implemented by each per-family class from step 3.
5. Push the branch to the edge. Delete every conditional except one, the Selector,
   and hoist it to the composition root. This is Replace Conditional with
   Polymorphism applied to construction. See
   `02-refactoring/replace-conditional-with-polymorphism`.
6. Close the bypass. Reduce the visibility of every concrete product constructor so
   the factory becomes the only route. Without this step the guarantee is a
   convention, not a structure.
7. Add a family that did not exist before, even a fake one for tests, before
   declaring the refactor finished. A pattern with one implementation is not yet
   proven to be an abstraction.

Removing the pattern when it stops earning its place. The trigger is a family count
that has fallen back to one and is not expected to rise, or a product role count
that keeps growing and makes every addition a breaking change.

1. Confirm there is one live family. Search for implementors of the factory
   interface and count the ones reachable in production wiring. Test fakes do not
   count as families, they are a testing technique and are cheaper to keep than the
   interface.
2. Inline the Selector. Replace the configuration read with a direct construction of
   the single concrete factory.
3. Inline the factory. Apply Inline Method to each creation operation so callers
   construct the concrete product directly, then delete the interface and the
   concrete factory. See `02-refactoring/inline-method`.
4. Collapse the product hierarchies where each has one implementation, using Collapse
   Hierarchy, and restore concrete constructor visibility. See
   `02-refactoring/collapse-hierarchy`.
5. If instead the trigger was product role growth, do not remove the pattern, change
   it. Replace the wide interface with a registry keyed by product role and family,
   which turns a breaking interface change into a registration, and accept that the
   consistency guarantee weakens from compiler-enforced to conventional.

## 15. Testing and verification

What becomes easy.

- A test family is a first-class implementation, not a mock. Writing a
  `TestFactory` that returns in-memory products gives deterministic tests without
  any mocking framework, and the test doubles are ordinary objects rather than
  configured stubs.
- Client logic can be tested once and asserted to be family-independent, by running
  the same test body against every registered factory. A parameterised test over the
  factory set is the highest-value test this pattern enables.
- Contract tests belong on the product roles. One shared test suite that any
  FamilyProduct must pass turns "does this driver behave" into a mechanical check,
  and it is the standard way database drivers are validated.

What becomes harder.

- Asserting which concrete type was produced requires a type test, which is the same
  downcast the pattern forbids in production code. Prefer asserting behaviour over
  identity, and where identity genuinely matters, assert it at the Selector rather
  than at the client.
- Reflective and service-loaded variants are hard to test for the negative case,
  because a missing provider surfaces as a class loading failure whose message
  depends on the runtime. Test the Selector with an explicitly empty provider set.
- Coverage tooling reports every concrete factory as separate code, so a family that
  is present but not exercised in continuous integration silently rots. Gate on
  running the shared contract suite against every family, not on line coverage.

Techniques that apply. Parameterised tests over the factory set. A shared contract
test suite per product role. A startup assertion, exercised by a test, that every
factory-derived singleton in the object graph shares one factory identity, which is
the mechanical guard against the two-factories-in-flight failure mode.
Property-based testing fits the contract suite well, because the property under test
is "every family behaves identically for this operation", and that is checkable
against generated inputs across all families at once.

## 16. Observability signals

What to emit.

- **One startup log line naming the selected family**, its version, and the source
  of the decision, for example the configuration key and its value. This single line
  answers most production questions about the pattern and costs nothing.
- **A gauge or startup-time metric of registered family count**, tagged by family
  identifier. In a service-loaded variant this is the only way to notice that a
  provider jar or assembly failed to load, because the absence is otherwise silent
  until first use.
- **A creation counter per product role, tagged with the family.** Two tag values
  appearing on the same instance is the alarm condition for the
  two-factories-in-flight failure. In a single-tenant process the family tag should
  carry exactly one distinct value.
- **A span attribute carrying the family identifier** on any trace that touches a
  product. This makes "slow only on the MySQL family" a filter rather than an
  investigation.
- **Creation latency histogram** only for the Prototype-backed variant, where clone
  cost is real and can exceed construction. For plain constructor factories this is
  noise and should not be instrumented.

A healthy instance on a dashboard. One family tag value, constant since process
start. Registered family count equal to the expected number and stable across
deploys. Creation counters tracking request volume with a flat ratio between product
roles.

A failing instance. Two or more family tag values on one process, which is the
mismatch defect in progress. Registered family count dropping after a deploy, which
means a provider is no longer being resolved. A creation counter for one product
role diverging from its siblings, which usually means a caller has started
constructing that product directly and bypassing the factory.

## 17. Security and privacy implications

The pattern opens one real attack surface and closes one real defect class, and it
is silent on most other security concerns.

Opened. In the reflective and service-loaded variants, the family selection is a
runtime string that names a class to load. If that string can be influenced by
untrusted input, by an environment variable an attacker controls, by a user-writable
configuration file, or by a provider entry on a mutable class path, the result is
arbitrary type loading and code execution in the process. Treat the selector value
as a trusted input. Validate it against a fixed allow list of known family
identifiers rather than passing it to a class loader, keep provider registration
paths write-protected, and prefer an explicit registration table over class path
scanning in any process handling untrusted data. This is why the JAXP factory
documents an explicit lookup order rather than an open search.

A second opened surface is configuration inheritance. A factory that carries
security-relevant configuration, for example the XML factory's validation and
external entity settings, applies that configuration to every product it emits. A
factory configured once at startup with an insecure setting silently produces
insecure products for the life of the process, and no individual call site shows the
defect. Set security-relevant factory state at construction, make the factory
immutable afterwards, and assert the setting in a startup test.

Closed. The mismatched-family defect class is a genuine security benefit where
families correspond to trust or tenancy boundaries. If each tenant has a family,
factory identity makes it impossible by construction to hand a tenant A parameter
object to a tenant B command object, which is a stronger guarantee than any runtime
check, because there is no code path to audit. This works only if concrete
constructors are unreachable, per step 6 of dimension 14.

Silent. The pattern has no direct effect on data at rest, data in transit,
authentication, authorisation, or logging content. Products may carry all of those
concerns, and the factory neither helps nor hinders. A concrete factory should not
hold credentials, because it is usually a long-lived shared singleton and a
credential on it outlives every reasonable rotation window. Pass credentials to the
product per call or per scope.

## 18. References

1. Gamma, Erich; Helm, Richard; Johnson, Ralph; Vlissides, John. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley Professional
   Computing Series, first edition, 1994. Chapter 3, Creational Patterns, Abstract
   Factory, page 87. Intent, participants, and the Kit alias are taken from this
   entry.
2. Addison-Wesley authorized chapter excerpt, Abstract Factory, Object Creational.
   https://www.informit.com/articles/article.aspx?p=1398599
   Verified 2026-08-02. Used to confirm the intent wording and the five participant
   names AbstractFactory, ConcreteFactory, AbstractProduct, ConcreteProduct, Client.
3. Oracle. *Java SE 21 API Specification*, class
   `javax.xml.parsers.DocumentBuilderFactory`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.xml/javax/xml/parsers/DocumentBuilderFactory.html
   Verified 2026-08-02. Source for the JAXP factory API description, the
   `newInstance()` lookup mechanism, and `newDocumentBuilder()`.
4. Microsoft. *.NET API reference*, class `System.Data.Common.DbProviderFactory`,
   System.Data.Common namespace.
   https://learn.microsoft.com/en-us/dotnet/api/system.data.common.dbproviderfactory
   Verified 2026-08-02. Source for the class summary, the `Create*` method family,
   the derived provider factory list, the `CanCreate*` capability properties, and the
   `DynamicallyAccessedMembers` trimming attribute.
5. Oracle. *Java SE 21 API Specification*, class `java.awt.Toolkit`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Toolkit.html
   Verified 2026-08-02. Source for the AWT peer binding description quoted in
   dimension 9.

## Code examples

Four languages are shown. Java is the platform form matching the production uses in
dimension 9. TypeScript shows the closure-record variant. Go shows why a language
without inheritance reshapes the pattern. Rust shows the associated-type form where
the compiler enforces family membership. Python is omitted from the examples not
because the pattern fails there, but because the Python form is identical to the
TypeScript closure record, with the class-based form identical to Java, so it would
add length without adding insight.

### Java, the platform form

```java
interface Button { String render(); }
interface ScrollBar { String render(); }

interface WidgetFactory {
    Button createButton();
    ScrollBar createScrollBar();
}

final class AquaButton implements Button {
    public String render() { return "[aqua button]"; }
}
final class AquaScrollBar implements ScrollBar {
    public String render() { return "[aqua scrollbar]"; }
}

final class AquaFactory implements WidgetFactory {
    public Button createButton() { return new AquaButton(); }
    public ScrollBar createScrollBar() { return new AquaScrollBar(); }
}

final class Win32Button implements Button {
    public String render() { return "[win32 button]"; }
}
final class Win32ScrollBar implements ScrollBar {
    public String render() { return "[win32 scrollbar]"; }
}

final class Win32Factory implements WidgetFactory {
    public Button createButton() { return new Win32Button(); }
    public ScrollBar createScrollBar() { return new Win32ScrollBar(); }
}

final class Window {
    private final Button button;
    private final ScrollBar scrollBar;

    Window(WidgetFactory factory) {
        this.button = factory.createButton();
        this.scrollBar = factory.createScrollBar();
    }

    String render() { return button.render() + " " + scrollBar.render(); }
}

public final class Demo {
    static WidgetFactory select(String platform) {
        return "aqua".equals(platform) ? new AquaFactory() : new Win32Factory();
    }

    public static void main(String[] args) {
        String platform = args.length > 0 ? args[0] : "aqua";
        System.out.println(new Window(select(platform)).render());
    }
}
```

### TypeScript, the closure-record variant

```typescript
interface Button { render(): string }
interface ScrollBar { render(): string }

interface WidgetFactory {
  createButton(): Button
  createScrollBar(): ScrollBar
}

const aquaFactory: WidgetFactory = {
  createButton: () => ({ render: () => "[aqua button]" }),
  createScrollBar: () => ({ render: () => "[aqua scrollbar]" }),
}

const win32Factory: WidgetFactory = {
  createButton: () => ({ render: () => "[win32 button]" }),
  createScrollBar: () => ({ render: () => "[win32 scrollbar]" }),
}

// The record is checked for completeness at compile time, so a
// missing product role is a type error rather than a runtime nil.
const families = { aqua: aquaFactory, win32: win32Factory } as const
type FamilyName = keyof typeof families

function select(name: string): WidgetFactory {
  if (name in families) return families[name as FamilyName]
  throw new Error(`unknown widget family: ${name}`)
}

function renderWindow(factory: WidgetFactory): string {
  return `${factory.createButton().render()} ${factory.createScrollBar().render()}`
}

console.log(renderWindow(select(process.argv[2] ?? "aqua")))
```

### Go, the struct-of-constructors form

```go
package main

import (
	"fmt"
	"os"
)

type Button interface{ Render() string }
type ScrollBar interface{ Render() string }

// No implementation inheritance, so the family is a value holding
// its constructors rather than a type hierarchy.
type WidgetFactory struct {
	NewButton    func() Button
	NewScrollBar func() ScrollBar
}

type aquaButton struct{}

func (aquaButton) Render() string { return "[aqua button]" }

type aquaScrollBar struct{}

func (aquaScrollBar) Render() string { return "[aqua scrollbar]" }

type win32Button struct{}

func (win32Button) Render() string { return "[win32 button]" }

type win32ScrollBar struct{}

func (win32ScrollBar) Render() string { return "[win32 scrollbar]" }

var families = map[string]WidgetFactory{
	"aqua": {
		NewButton:    func() Button { return aquaButton{} },
		NewScrollBar: func() ScrollBar { return aquaScrollBar{} },
	},
	"win32": {
		NewButton:    func() Button { return win32Button{} },
		NewScrollBar: func() ScrollBar { return win32ScrollBar{} },
	},
}

func Select(name string) (WidgetFactory, error) {
	f, ok := families[name]
	if !ok {
		return WidgetFactory{}, fmt.Errorf("unknown widget family %q", name)
	}
	return f, nil
}

func main() {
	name := "aqua"
	if len(os.Args) > 1 {
		name = os.Args[1]
	}
	f, err := Select(name)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println(f.NewButton().Render(), f.NewScrollBar().Render())
}
```

### Rust, the associated-type form

```rust
trait Button { fn render(&self) -> String; }
trait ScrollBar { fn render(&self) -> String; }

// Associated types tie the two products to one implementor, so the
// compiler rejects a mixed family without any runtime check.
trait WidgetFactory {
    type B: Button;
    type S: ScrollBar;
    fn create_button(&self) -> Self::B;
    fn create_scroll_bar(&self) -> Self::S;
}

struct AquaButton;
impl Button for AquaButton {
    fn render(&self) -> String { "[aqua button]".into() }
}
struct AquaScrollBar;
impl ScrollBar for AquaScrollBar {
    fn render(&self) -> String { "[aqua scrollbar]".into() }
}
struct Aqua;
impl WidgetFactory for Aqua {
    type B = AquaButton;
    type S = AquaScrollBar;
    fn create_button(&self) -> AquaButton { AquaButton }
    fn create_scroll_bar(&self) -> AquaScrollBar { AquaScrollBar }
}

struct Win32Button;
impl Button for Win32Button {
    fn render(&self) -> String { "[win32 button]".into() }
}
struct Win32ScrollBar;
impl ScrollBar for Win32ScrollBar {
    fn render(&self) -> String { "[win32 scrollbar]".into() }
}
struct Win32;
impl WidgetFactory for Win32 {
    type B = Win32Button;
    type S = Win32ScrollBar;
    fn create_button(&self) -> Win32Button { Win32Button }
    fn create_scroll_bar(&self) -> Win32ScrollBar { Win32ScrollBar }
}

fn render_window<F: WidgetFactory>(f: &F) -> String {
    format!("{} {}", f.create_button().render(), f.create_scroll_bar().render())
}

fn main() {
    let name = std::env::args().nth(1).unwrap_or_else(|| "aqua".into());
    let out = match name.as_str() {
        "win32" => render_window(&Win32),
        _ => render_window(&Aqua),
    };
    println!("{}", out);
}
```
