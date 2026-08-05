---
name: Onion Architecture
slug: onion-architecture
family: 05-architectural
category: Architectural
aliases: [Domain Centric Architecture]
first_described: "Palermo 2008"
maturity: canonical
related: [layered-architecture, repository, dependency-injection, hexagonal-architecture, clean-architecture, cqrs]
incompatible_with: []
verified: 2026-08-02
---

# Onion Architecture

## 1. Name, aliases, and lineage

The canonical name is Onion Architecture. Jeffrey Palermo coined it in a
four-part blog series published on his own site in the summer of 2008,
beginning with "The Onion Architecture: Part 1" on 29 July 2008. Palermo
states the core rule plainly. all code can depend on layers more central than
itself, but no code can depend on a layer further out, and the database sits
outside that boundary rather than at the center of the design (Jeffrey
Palermo, "The Onion Architecture: Part 1", jeffreypalermo.com, 29 July 2008,
https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/, verified
2026-08-02). Part 2 of the series works through an ASP.NET MVC conference
registration example to show the same rule enforced through constructor
injection and an IoC container (Jeffrey Palermo, "The Onion Architecture: Part
2", jeffreypalermo.com, 2008,
https://jeffreypalermo.com/2008/07/the-onion-architecture-part-2/, verified
2026-08-02). Part 3 grounds the whole design in a single distinction.
"Infrastructure is any code that is a commodity and does not give your
application a competitive advantage," and that commodity code, because it
changes on its own schedule, is the code that must never sit at the center
(Jeffrey Palermo, "The Onion Architecture: Part 3", jeffreypalermo.com, August
2008, https://jeffreypalermo.com/2008/08/the-onion-architecture-part-3/,
verified 2026-08-02).

There is no widely used alternate name for Onion Architecture the way Factory
Method has Virtual Constructor. The name that does need untangling is the
relationship to two other named architectures that solve the same problem in
a different shape. Alistair Cockburn had already published Hexagonal
Architecture, also called Ports and Adapters, in 2005, three years before
Palermo's series, with the same inside out dependency rule expressed through a
hexagon rather than concentric rings (Alistair Cockburn, "Hexagonal
Architecture", alistair.cockburn.us, version 0.9, first published 4 September
2005, https://alistair.cockburn.us/hexagonal-architecture, verified
2026-08-02). Robert C. Martin then named Clean Architecture in 2012 and said
directly that Hexagonal, Onion, and his own Clean Architecture "are very
similar. They all have the same objective, which is the separation of
concerns," achieved by pushing business rules to the center and dependency
details to the edge (Robert C. Martin, "The Clean Architecture",
blog.cleancoder.com, 13 August 2012,
https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html,
verified 2026-08-02). Martin later folded the idea into a book chapter with
its own four ring diagram, Entities, Use Cases, Interface Adapters, and
Frameworks and Drivers (Robert C. Martin, *Clean Architecture. A Craftsman's
Guide to Software Structure and Design*, Pearson, 2017, ISBN
978-0-13-449416-6, Part V, chapter 22, "The Clean Architecture", page 201).

Treat the three as siblings, not synonyms, because their structural
commitments differ in ways that matter once a team has to draw the diagram
for real. Onion Architecture, as Palermo actually drew it, has exactly four
named rings, Domain Model, Domain Services, Application Services, and an
outer edge shared by UI, Infrastructure, and Tests, and it places repository
interfaces inside the Application Services ring rather than in the domain
itself. Hexagonal Architecture has no ring count at all, it has exactly two
kinds of things, ports and adapters, and a symmetric inside versus outside
split with no prescribed number of concentric layers on the inside. Clean
Architecture fixes the ring count at four and gives each ring a name tied to
the Single Responsibility Principle rather than to Palermo's domain versus
infrastructure split. The three architectures agree on one non negotiable
rule, dependencies point inward and the database, the UI framework, and every
other volatile technology sit on the outside. This entry treats that shared
rule as the pattern and documents Palermo's specific ring vocabulary as the
canonical instance, cross referencing Hexagonal and Clean Architecture where
the differences change what a reader actually builds.

## 2. Problem and context

A team builds a business application against a specific database, a specific
web framework, and a specific set of third party integrations, because those
are the concrete decisions a working system needs on day one. The natural
place to put a decision is where it is needed, so calls to the ORM, HTTP
clients for a payment provider, and framework specific request objects end up
threaded directly through the code that expresses what the business actually
does. Six months later the business rule that a discount cannot apply to an
already refunded order sits inside a controller action, next to the code that
parses the HTTP request and next to the Entity Framework query that loads the
order row. Nothing distinguishes the one line of code that is the actual
business decision from the forty lines of code that exist only because of the
web framework and the database driver.

This produces the failure Palermo names directly, code coupled to
infrastructure that changes for reasons that have nothing to do with the
business. He frames it in economic terms. infrastructure is a commodity, the
technology used to persist data or serve HTTP is replaced or upgraded on its
own schedule, while the domain rule about refunded orders is the one thing
that actually differentiates this application from a competitor's (Palermo,
"Part 3", cited above). When the two are welded together in the same class,
upgrading the ORM, swapping a payment gateway, or adding a second UI, a CLI
alongside the web app, or a background worker alongside the request pipeline,
forces a rewrite of code that has nothing to do with the change being made.
Worse, testing the discount rule now requires a database connection and a
running web server, because the rule cannot be exercised without also
exercising everything around it.

The context in which this problem is worth solving is a long lived
application with business rules complex enough to be worth protecting, not
every application. A five screen internal CRUD tool that will be rewritten in
two years does not have this problem in any way that matters, a script that
reads a CSV and writes a database row has almost no domain logic to protect
in the first place. Onion Architecture earns its keep specifically where the
domain logic will outlive at least one infrastructure decision, and where
automated tests of that logic are expected to run in seconds rather than
minutes.

## 3. Forces

**Testability against wiring cost.** Isolating the domain from infrastructure
lets unit tests run in memory with no database, no HTTP, and no filesystem,
which Palermo names as a direct consequence of the design in Part 3. That
isolation is bought with an interface for every seam the tests need to
substitute, and every interface is a file, a name, and a mapping the reader
has to hold in their head to understand where a call actually lands.

**Infrastructure churn tolerance against upfront ceremony.** An application
built to swap its database, its message broker, or its UI framework without
touching business logic pays for that flexibility on day one, in the form of
repository interfaces and a composition root, whether or not the swap ever
happens. Most applications never actually change their database engine. The
force only pays for itself when the swap, or the mocked equivalent used for
testing, genuinely occurs.

**Persistence ignorance against query expressiveness.** Keeping the domain
model unaware of how it is stored means the domain layer cannot lean on
database specific features, an index hint, a windowed aggregate, a full text
search operator, without pushing that decision behind an interface general
enough to hide it. A repository interface either grows increasingly specific
methods to cover every query shape the domain needs, which erodes the
abstraction, or it stays generic and the team writes inefficient queries
through it. This tension is inherent, not a defect of a particular
implementation.

**Explicit dependency direction against onboarding cost.** A newcomer reading
a traditional three tier codebase can trace a request top to bottom, UI calls
business logic calls data access, in the order execution actually happens.
Onion Architecture inverts the data access dependency, so the call from
Application Services to persistence happens through an interface the
newcomer has to know is satisfied somewhere else entirely, by a class they
have not yet found. The architecture is more honest about what depends on
what, and less honest about where execution physically goes next.

**Team topology fit against solo project overhead.** The pattern gives a
platform or infrastructure focused subteam a stable seam, the port
interfaces, to build against independently of the team writing domain logic,
which is close to why Cockburn originally wanted ports and adapters, letting
an application run with a UI or without one, with a real database or a fake
one, without either team blocking the other. A single developer working
alone pays the interface tax with no team boundary benefit to offset it.

## 4. Applicability and non-applicability

Reach for Onion Architecture when the following hold together, not any one
alone.

- The application has business rules complex enough, and long lived enough,
  that protecting them from framework churn is worth the interface and
  wiring overhead described in dimension 3.
- More than one delivery mechanism is realistic within the application's
  lifetime, a web UI plus a background worker, a public API plus an admin
  tool, or a test run that must complete without any real infrastructure.
- The team already practices, or intends to practice, tactical
  Domain-Driven Design, entities with real invariants, value objects,
  domain services, because Onion Architecture's center ring is exactly that
  model and the pattern adds little where the "domain" is really just a set
  of database rows with getters and setters.
- Automated regression testing at the business rule level is a stated
  priority, not an afterthought, because the isolation this pattern buys is
  primarily a testing isolation.
- The team has the discipline, or the tooling, to keep the dependency
  direction honest over time, since nothing about the language enforces it
  without a deliberate check.

Do NOT reach for it, and this list is the one most catalogs skip.

- **Small or short lived tools.** A script, an admin utility, or a prototype
  expected to be discarded within a development cycle pays the full
  interface and composition root cost for a benefit, safe infrastructure
  swaps and isolated unit tests, that will never be collected.
- **Applications with genuinely trivial domain logic.** If the business
  logic really is "validate the input, insert the row," wrapping that in a
  Domain Model ring, a Domain Services ring, and an Application Services
  ring adds three files and two interfaces around one `INSERT` statement.
  Palermo's own commodity versus differentiator framing argues against the
  pattern here as directly as it argues for it elsewhere, there is nothing
  differentiating to protect.
- **Read heavy reporting and analytics paths.** A generic repository
  interface is a poor fit for a query that must join across a dozen tables,
  aggregate, and paginate for a dashboard. Forcing that query through the
  same port abstraction built for transactional writes either produces an
  interface with a growing pile of report shaped methods or a domain model
  that leaks SQL. A CQRS split that reads directly from a data store for
  queries while writes still go through the onion is the common escape
  hatch, addressed further in dimension 13.
- **Extreme low latency or resource constrained paths.** Every ring crossing
  is at minimum a virtual call, and in managed runtimes an interface
  dispatch plus an allocation for the DTO crossing the boundary. A hot loop
  in a trading engine or an embedded control system that is measured in
  nanoseconds is the wrong place for four ring crossings per operation.
- **A team unfamiliar with dependency injection and interface based design.**
  The pattern's entire value proposition depends on the team actually using
  the composition root correctly and not routing around it with a static
  service locator or a `new` call reaching across rings. Teaching the
  pattern under deadline pressure on a project that does not strictly need
  it is a common way projects abandon it halfway through, leaving an
  inconsistent codebase that pays the interface cost without the isolation
  benefit.

## 5. Structure

The participants, named the way Palermo names them across the three parts of
his series.

- **Domain Model.** The innermost ring. Entities and value objects that
  express the business's core nouns and the invariants attached to them.
  Depends on nothing else in the application. Has no reference to a
  database, a web framework, or any third party library beyond the
  language's own standard library.
- **Domain Services.** Business logic that spans more than one entity, or
  that does not naturally belong on a single entity, sits in this ring.
  Depends only on the Domain Model.
- **Application Services.** The use case orchestration ring. A single method
  here corresponds to one thing a user or another system asks the
  application to do, place an order, ship an order, cancel a subscription.
  This is also where the repository and gateway interfaces are declared,
  the ports, because the application layer is what defines what it needs
  from the outside world without caring who provides it.
- **Ports.** The interfaces declared in the Application Services ring
  (occasionally pushed down into Domain Services when a domain rule itself
  needs an external capability, such as a pricing lookup). A port names a
  capability from the point of view of the code that needs it, `save an
  order`, never from the point of view of the technology that will supply
  it, `run this SQL`.
- **Infrastructure adapters.** Concrete classes living in the outer ring
  that implement the ports. An `EfOrderRepository` implementing
  `OrderRepository`, an `SmtpNotificationSender` implementing
  `NotificationSender`. These depend inward on the port interface and on
  nothing else in the application besides the Domain Model types the port
  signatures mention.
- **UI, Presentation.** Also in the outer ring alongside Infrastructure.
  Controllers, CLI entry points, or message consumers that translate an
  external request into a call on an Application Service and translate the
  result back into whatever the delivery mechanism needs.
- **Tests.** Palermo places automated tests explicitly on the outer edge
  next to UI and Infrastructure, because tests are consumers of the
  Application Core the same way a controller is, they call into it and
  assert on the result, and the Application Core has no idea they exist.
- **Composition root.** Not one of Palermo's four named rings, but the
  mechanism every real implementation needs, the single place, typically at
  application startup, where concrete Infrastructure adapters are bound to
  the port interfaces they satisfy, usually through an IoC container. Every
  other line of code in the outer ring reaches infrastructure only through
  a port, never by naming a concrete adapter class directly.

## 6. ASCII structure diagram

```
+----------------------------------------------------------------------+
|  Outer ring: UI / Controllers, Infrastructure Adapters, Tests        |
|  (implements ports, depends inward, never depended upon)             |
|                                                                        |
|   +------------------------------------------------------------+     |
|   |  Application Services (use cases)                          |     |
|   |  declares Ports: OrderRepository, PaymentGateway, ...       |     |
|   |                                                              |     |
|   |   +------------------------------------------------------+ |     |
|   |   |  Domain Services                                     | |     |
|   |   |  rules spanning more than one entity                 | |     |
|   |   |                                                        | |     |
|   |   |   +------------------------------------------------+ | |     |
|   |   |   |  Domain Model                                  | | |     |
|   |   |   |  Entities, Value Objects, invariants            | | |     |
|   |   |   |  no reference to any outer ring                | | |     |
|   |   |   +------------------------------------------------+ | |     |
|   |   +------------------------------------------------------+ |     |
|   +------------------------------------------------------------+     |
+----------------------------------------------------------------------+

  Compile-time dependencies point INWARD only, drawn here as an arrow
  that only ever crosses a boundary toward the center:

  UI ------------> Application Services ------------> Domain Services
  Infrastructure -> Application Services (implements a port declared there)
  Tests ----------> Application Services / Domain Model (calls in, asserts)

  No inner ring imports, references, or knows the name of anything in a
  ring drawn further out. The database is not in this picture at all, it
  is a detail an Infrastructure adapter hides behind a port.
```

## 7. Dynamics

The interesting property here is not the happy path call sequence, it is
which direction the *reference* to a concrete type flows compared to which
direction the *call* flows at runtime. A port interface is declared inward,
in Application Services. The class that implements it lives outward, in
Infrastructure. So the source file for `EfOrderRepository` has a `using` or
`import` statement pointing at the Application layer's `OrderRepository`
interface, the reverse of the traditional layered picture where the business
layer imports the data access layer. At runtime, the call still flows the
way you would expect, Application Services calls a method that happens to be
implemented by `EfOrderRepository`, it just does not know that at compile
time.

```
Controller        ShipOrderService     OrderRepository (port)   EfOrderRepository (adapter)
    |                    |                       |                          |
    |-- POST /ship ----->|                       |                          |
    |                    |-- find(id) ---------->|                          |
    |                    |                       |-- (resolved by DI to) ->|
    |                    |                       |                          |-- SELECT * FROM orders ...
    |                    |                       |<-- Order row mapped ----|
    |                    |<---- Order -----------|                          |
    |                    |                       |                          |
    |                    |-- order.ship() ------>|                          |
    |                    |   (pure domain call,  |                          |
    |                    |    no ring crossing)  |                          |
    |                    |                       |                          |
    |                    |-- save(order) ------->|                          |
    |                    |                       |-- (resolved by DI to) ->|
    |                    |                       |                          |-- UPDATE orders SET ...
    |<-- 200 OK ---------|                       |                          |
    |                    |                       |                          |
```

Two things this diagram makes visible that a horizontal layer diagram hides.
First, `order.ship()` never crosses a ring boundary, it is a call from
Application Services into the Domain Model and back, which is exactly the
call that stays cheap and testable with no fakes involved. Second, the two
calls that do cross a boundary, `find` and `save`, are resolved to a concrete
adapter only by the dependency injection container configured at the
composition root, not by anything `ShipOrderService` wrote. Swap the
container's registration from `EfOrderRepository` to
`InMemoryOrderRepository` for a test run and this exact sequence executes
with no database at all, which is the whole point of the pattern made
concrete.

## 8. Implementation variants

**Palermo's original four ring .NET form.** Domain Model and Domain Services
in their own class libraries, Application Services holding the port
interfaces, an ASP.NET MVC project and a separate persistence project on the
outer ring, wired together by an IoC container (Castle Windsor or, in later
write ups, Ninject) at the MVC application's startup, which is the
composition root (Palermo, "Part 2", cited above).

**Merged with Clean Architecture's four rings.** Many teams reaching for
"Onion Architecture" today are actually building Robert Martin's Entities,
Use Cases, Interface Adapters, Frameworks and Drivers structure, because
Martin's book gave the idea a more widely taught vocabulary than Palermo's
2008 blog series. The dependency rule is identical, only the ring names and
their exact boundaries differ (Martin, *Clean Architecture*, chapter 22,
cited above).

**Hexagonal framing of the same rule.** Instead of concentric rings, ports
are grouped as driving (primary, called by something outside, a controller
calling into the application) and driven (secondary, called by the
application out to something outside, a database). The distinction that
Hexagonal makes explicit and Onion leaves implicit is which side initiates
the call, which matters when deciding whether an adapter needs a test double
or a real integration test (Cockburn, "Hexagonal Architecture", cited above).

**CQRS flavored variant.** Write operations flow through the full onion,
Application Service, Domain Model, Repository port, exactly as described
above. Read operations that only need to render a screen bypass the Domain
Model entirely and query a read optimized store directly through a separate,
thinner port, avoiding the leaky generic repository problem named in
dimension 4's non applicability list for reporting paths. This is a common
practitioner adaptation rather than a separately named canonical source, and
is treated as engineering judgement here.

**Modular monolith variant.** Each bounded context gets its own complete
onion, Domain Model through Application Services, and the outer rings of
different contexts talk to each other only through their respective
Application Service ports, never by reaching into another context's Domain
Model. This keeps the inward dependency rule intact per module while
avoiding a single monolithic set of rings for an entire system. This is
practitioner convention, presented as judgement rather than a sourced claim.

**Language idiomatic differences.** In Go, an adapter satisfies a port
implicitly through structural typing, the `EfOrderRepository` equivalent
struct never writes `implements OrderRepository` anywhere, the compiler
checks the method set matches wherever the interface value is assigned. This
removes one whole category of the "adapter forgot to declare the interface"
mistake that shows up in Java or C#, at the cost of the interface being
satisfied accidentally by an unrelated type with a coincidentally matching
method set. In TypeScript and Python, ports are frequently expressed as
plain function types rather than single method interfaces, a two argument
function type standing in for what would be a one method interface class in
Palermo's original C# form, which removes the interface with one method
ceremony entirely and composes more naturally with those languages'
functional idioms.

## 9. Known production uses

**eShopOnWeb, the .NET Foundation reference application (Microsoft, formerly
`dotnet-architecture/eShopOnWeb`, now community maintained under
`NimblePros/eShopOnWeb`).** Microsoft's own architecture guidance names this
application as the reference implementation of what it calls Clean
Architecture "gone by many names," explicitly citing Onion Architecture as
one of those names and reproducing the concentric ring "onion view" diagram
directly. The guide walks through the same Application Core, Infrastructure,
and UI split used throughout this entry (Microsoft, "Common web application
architectures", learn.microsoft.com,
https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures,
verified 2026-08-02). The repository is real and actively used as a teaching
reference, 10,697 stars at time of verification (GitHub API,
`repos/dotnet-architecture/eShopOnWeb`, https://github.com/dotnet-architecture/eShopOnWeb,
verified 2026-08-02).

**Ardalis Clean Architecture Solution Template.** The same Microsoft guide
points readers to this template as the starting point for building a real
ASP.NET Core solution in this style, and the template is maintained
independently of the eShopOnWeb sample, described on its own repository page
as "A proven Clean Architecture Template for ASP.NET Core," with 18,374
stars and continued releases tracking current ASP.NET Core versions (GitHub
API, `repos/ardalis/CleanArchitecture`,
https://github.com/ardalis/CleanArchitecture, verified 2026-08-02).

**ABP Framework's layered solution template.** ABP Framework's own solution
template ships eight projects per module, `Domain.Shared`, `Domain`,
`Application.Contracts`, `Application`, `EntityFrameworkCore`, `HttpApi`,
`HttpApi.Client`, and `Web`, and its documentation describes the dependency
direction directly, `EntityFrameworkCore` implements repository interfaces
declared in `Domain`, and `Web` depends on `Application` rather than on
`EntityFrameworkCore` (ABP.IO, "Layered solution structure",
abp.io/docs/latest/solution-templates/layered-web-application/solution-structure,
verified 2026-08-02). ABP's own documentation frames this as Domain-Driven
Design layering rather than naming it Onion Architecture by name, but the
dependency direction it describes, the inner Domain project has no outward
dependency and the persistence project implements interfaces the Domain
project declares, is the onion dependency rule exactly, stated honestly here
as a structural match rather than a self applied label. The framework itself
is real and widely deployed, 14,391 stars at time of verification (GitHub
API, `repos/abpframework/abp`, https://github.com/abpframework/abp, verified
2026-08-02).

## 10. Consequences

Positive.

- Business rules can be exercised by fast, in memory unit tests with no
  database, no HTTP server, and no filesystem, because the Domain Model and
  Application Services have no outward dependency to fake around.
- Infrastructure decisions, which ORM, which message broker, which payment
  provider, become swappable behind a port without touching the code that
  expresses what the business does, which is Palermo's stated economic
  motivation.
- A codebase that follows the rule consistently is self documenting about
  what is a business decision and what is plumbing, because plumbing lives
  in a project that, by construction, the Domain Model never imports.
- Multiple delivery mechanisms, a web UI and a background worker and an
  admin CLI, can share one Application Services layer instead of each
  reimplementing the same business rules against its own data access code.
- The composition root becomes a single, auditable place that names every
  concrete infrastructure choice the application makes, rather than that
  choice being scattered across every file that happens to need it.

Negative.

- More files and more indirection for the same behavior than a straight
  layered or transaction script implementation, an interface plus at least
  one implementation for every seam the design decided was worth isolating.
- A generic repository port is a poor fit for reporting shaped queries,
  which either pushes report logic through an interface it was never
  designed for or forces the team to add a second, query shaped port,
  eroding the single clean seam the pattern promised.
- The dependency inversion discipline is not enforced by most languages on
  its own, nothing stops a developer from adding a `using
  Infrastructure.EntityFramework` statement to a Domain Model class next
  Tuesday, and only a deliberate architecture test or code review catches
  it.
- Newcomers trace execution less easily than in a top to bottom layered
  design, because the concrete class that actually runs is bound at
  composition root time, not visible at the call site.
- Domain purity has a real cost against ORM ergonomics, many ORMs want
  parameterless constructors, mutable properties, or specific base classes
  on persisted types, all of which pull against a Domain Model designed
  purely around business invariants, and reconciling the two takes real
  mapping code that itself has to live somewhere.

## 11. Failure modes and misuse

**The leaky generic repository.** Symptom. A single `IOrderRepository`
interface accumulates methods like `FindByStatusAndDateRangeAndCustomer`
because every new screen needs a slightly different query shape, or the team
gives up and adds a raw SQL escape hatch directly on the interface. Cause. A
port designed for the transactional write path was reused for read and
reporting needs it was never shaped for. Fix. Split reads onto a separate,
narrower query port, or a CQRS read side, per the variant discussed in
dimension 8, and keep the write side repository interface small.

**The anemic domain hiding inside a fat Application Service.** Symptom. Every
entity in the Domain Model is a bag of public properties with no methods
beyond getters and setters, and every business rule, including invariants
that should be impossible to violate, is written as an `if` statement inside
an Application Service method. Cause. The team drew the ring boundaries
correctly on paper but defaulted to transaction script style inside the
Application Services ring instead of pushing behavior onto the entities and
value objects the pattern is centered on. Fix. Move invariant checks and
behavior that belongs to a single entity onto that entity's constructor and
methods, reserving Application Services for orchestration across entities and
ports, not for the rules themselves.

**Interface explosion with no second implementation in sight.** Symptom. A
port interface exists with exactly one production implementation, has never
had a second, and the team cannot name a plausible circumstance under which
it would. Cause. The Dependency Inversion Principle was applied reflexively
to every class rather than at genuine architectural seams. Fix. Reserve a
port for a boundary that either already has more than one real
implementation, including a test double used in an actual test, or is
concretely expected to soon. Program directly against the concrete class
everywhere else inside a single ring.

**A ring boundary violation through a shared utility project.** Symptom. A
build that passes locally breaks, or worse silently starts calling a real
database from a supposedly pure unit test, after the Domain Model project
picks up a transitive reference to a persistence library through a shared
`Common` or `Utils` project everyone references. Cause. A grab bag shared
project was allowed to depend outward, and every ring, including the Domain
Model, references that shared project. Fix. Split the shared project by
concern so that anything the Domain Model uses has zero outward dependencies
itself, and enforce the reference graph with an architecture test, not a
convention nobody checks.

**The composition root that grew into its own god object.** Symptom. A
startup file thousands of lines long, registering hundreds of interface to
implementation mappings by hand, that every feature team touches on nearly
every pull request and that regularly produces merge conflicts. Cause. All
dependency registration for the entire application lives in one file with no
modularization. Fix. Split registration by module or bounded context, each
owning a small registration function the composition root simply calls, and
prefer convention based auto registration for the mechanical cases.

**A domain entity reaching directly for an infrastructure side effect.**
Symptom. An entity method sends an email, writes a log line through a
concrete logging framework, or calls an HTTP client directly, discovered
because the "pure" unit test for that entity now needs network access to
pass. Cause. A developer took a shortcut around the Application Services
orchestration layer because it was faster than wiring a port for a one off
notification. Fix. Have the entity raise a domain event describing what
happened, and let an outer ring handler subscribed to that event perform the
actual side effect, keeping the entity itself free of outward calls.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Onion Architecture | Traditional Layered / N-Tier | Hexagonal (Ports and Adapters) | Clean Architecture | Vertical Slice / feature folders |
|---|---|---|---|---|---|
| Testability of business logic in isolation | Strong, by design | Weak, business layer imports data access | Strong, by design | Strong, by design | Moderate, depends on slice discipline |
| Infrastructure swap without touching domain | Strong, behind ports | Weak, data access is a direct dependency | Strong, that is the pattern's origin | Strong, same dependency rule | Weak, each slice often owns its own data access |
| Cognitive load for a newcomer | Higher, execution path is indirect | Lower, code reads top to bottom | Higher, similar to Onion | Higher, four named rings to learn | Lower, one feature is one place to look |
| Query and reporting expressiveness | Weak unless a read side is added | Strong, direct SQL is easy to reach | Weak, same generic port tension | Weak, same generic port tension | Strong, each slice can query however it needs |
| Boilerplate for a small application | High relative to the domain's real size | Low | High, similar to Onion | High, similar to Onion | Low to moderate |
| Team topology fit | Good, ports are a stable seam between teams | Poor, teams collide inside shared layers | Good, ports are the explicit design goal | Good, similar to Onion | Good for independently owned features |
| Enforcement without extra tooling | None, relies on discipline or architecture tests | None, but violations read as normal code | None, same as Onion | None, same as Onion | Easier, a slice's boundary is a folder |

Reading of the table. Onion Architecture, Hexagonal Architecture, and Clean
Architecture score nearly identically because they share the same dependency
rule, the differences between them are vocabulary and ring count, not
substance. Traditional Layered wins decisively on cognitive load and query
expressiveness, which is exactly why it remains the right default for
smaller applications per dimension 4. Vertical Slice trades the onion's
cross cutting reuse of one Application Services layer for locality, each
feature is easier to find and delete, at the cost of infrastructure swaps
now needing to happen per slice rather than once at the composition root.

## 13. Related and incompatible patterns

- **Layered Architecture.** The pattern Onion Architecture directly reacts
  against and refines. Traditional Layered puts the database at the
  foundation and lets the business layer depend downward on data access.
  Onion Architecture inverts exactly that one dependency while keeping the
  general idea of separating concerns into named groups of code. Reach for
  plain Layered Architecture when the applicability conditions in dimension
  4 are not met, and refactor toward Onion Architecture, following
  dimension 14, only once they are.
- **Hexagonal Architecture and Clean Architecture.** Siblings, not
  substitutes to switch into casually mid project, because each has its own
  vocabulary a team has to commit to and stay consistent with. All three
  compose in the sense that a codebase correctly following any one of them
  satisfies the dependency rule the other two also require.
- **Repository pattern.** The canonical shape of a persistence port in an
  Onion Architecture implementation. The repository interface is declared in
  the Application Services ring, per dimension 5, and its implementation is
  an Infrastructure adapter. Onion Architecture is the reason a repository
  interface exists at all in a given codebase, and the repository pattern
  is the concrete technique that satisfies it.
- **Dependency Injection and an IoC container.** The composition root, per
  dimension 5, is the mechanical enabler of the whole pattern, constructor
  injection of a port into an Application Service, resolved by a container
  at startup, is how Palermo's own example wires the rings together. The
  pattern does not strictly require a container, manual wiring in a small
  application achieves the same dependency direction, but container based
  wiring is by far the most common implementation.
- **CQRS.** Complements the pattern rather than replacing it, and directly
  addresses the leaky generic repository failure mode in dimension 11 by
  giving reads a separate, differently shaped port from writes, as
  described in the CQRS flavored variant in dimension 8.
- **Domain-Driven Design tactical patterns.** Entities, value objects,
  aggregates, and domain events are what the Domain Model and Domain
  Services rings are made of in a serious implementation. Onion
  Architecture supplies the surrounding structure. DDD tactical patterns
  supply the substance that goes inside the center of it.
- **Service Locator.** Actively conflicts. A class that pulls a dependency
  from a static locator rather than receiving it through its constructor
  hides which port it depends on, defeating the entire point of an explicit
  composition root that makes every wiring decision visible in one place.
- **Active Record.** Actively conflicts with the Domain Model ring as
  described here. An Active Record entity knows how to save and load itself,
  which means it depends directly on persistence infrastructure by
  definition, exactly the outward dependency the Domain Model ring is
  defined to never have. A codebase using Active Record entities is not
  practicing Onion Architecture regardless of how its folders are named.

## 14. Refactoring path in and out

Introducing the pattern into an existing layered or Smart UI application.

1. Identify the nouns and rules that are genuinely the business, not the
   framework, order, discount, refund, and the invariants attached to them,
   a discount cannot exceed the order total, a refunded order cannot ship.
2. Extract those nouns into a Domain Model project or module with zero
   references to the web framework, the ORM, or any HTTP client library.
   Move the invariant checks onto the entities and value objects themselves,
   as the anemic domain failure mode in dimension 11 warns against leaving
   them in a service.
3. Declare the capabilities the domain needs from the outside world as
   interfaces, an `OrderRepository`, a `PaymentGateway`, inside an
   Application Services layer that also holds the orchestration for each
   use case. This is the step that actually inverts the dependency, the
   interface now lives with the code that needs it, not with the code that
   will provide it.
4. Move the existing data access and integration code, largely unchanged,
   into an Infrastructure project, and make it implement the interfaces
   from step 3 rather than being called directly by the business logic.
5. Build a composition root, typically at the application's existing
   startup location, that registers each interface against its concrete
   Infrastructure implementation through the application's dependency
   injection container.
6. Add an architecture test asserting the reference graph, the Domain Model
   project references nothing outward, so the next developer who adds a
   stray `using` statement finds out at build time rather than a year
   later.

Removing the pattern, when the applicability conditions in dimension 4 stop
holding, for example a bounded context shrinks to a genuinely trivial CRUD
surface.

1. Confirm, per port, that it has exactly one implementation and no
   plausible second one, the interface explosion failure mode in dimension
   11 in reverse.
2. Inline the single implementation into the class that consumes the port,
   removing the interface and letting the consumer reference the concrete
   type directly.
3. Fold Domain Services and Application Services into a single service
   layer once the distinction between "spans multiple entities" and
   "orchestrates a use case" stops earning its keep for a small surface.
4. Retire the composition root's registrations for the removed interfaces,
   and delete the now empty seam rather than leaving a one method interface
   as a vestigial layer nobody exercises.

## 15. Testing and verification

Unit tests target the Domain Model and Application Services in complete
isolation, substituting an in memory or hand written fake for every port a
test needs, an `InMemoryOrderRepository` backed by a dictionary rather than a
mock framework's recorded expectations, since the goal is a fast, readable
assertion about behavior rather than a verification that specific methods
were called in a specific order. This is the direct payoff of the dependency
inversion described in dimension 5, and it is the reason the pattern is
adopted in the first place.

Integration tests target each Infrastructure adapter on its own, against a
real or containerized dependency, an actual database instance rather than an
in memory substitute, because the adapter's whole job is to correctly
translate between the port's contract and a real external system, and a fake
cannot verify that translation. These tests are slower and fewer than the
unit tests above, and they are the tests that would fail if a database
migration silently changed a column type the adapter depends on.

Contract tests verify that every implementation of a port, the production
adapter and any test double used elsewhere, actually satisfies the same
behavioral contract, not just the same method signature. A repository's
`find` returning `null` versus throwing for a missing record is a behavioral
detail an interface's type signature cannot express, and a consumer written
against one implementation's actual behavior will break silently against
another that technically satisfies the same interface. Running the same
contract test suite against every implementation of a given port catches
this class of bug before it reaches production.

Architecture tests, run as part of the build rather than as a manual review
step, assert the reference graph directly, a Domain Model assembly or
package must not reference an Infrastructure one, an Application Services
package must not reference a concrete adapter. This is the single testing
technique specific to this pattern rather than borrowed from general
practice, because nothing in most languages enforces the dependency
direction on its own, per the negative consequence named in dimension 10.

## 16. Observability signals

A healthy implementation has telemetry concentrated at ring boundaries, not
scattered evenly through every layer. The composition root logs which
concrete adapter it bound to each port at startup, `OrderRepository ->
EfOrderRepository (SqlServer)`, making an infrastructure swap auditable from
the deployment logs alone. Application Services log use case entry and exit
with a correlation identifier, because that is the seam where a request
becomes an observable unit of work, one log line per `ShipOrder` call rather
than one per SQL statement it happens to issue. Infrastructure adapters
emit latency and error rate metrics tagged by port name and operation, `port
= OrderRepository, op = find, latency_ms = 42`, rather than by database
engine detail, so a dashboard for `OrderRepository.find` stays meaningful
even after the underlying database is swapped.

An unhealthy implementation shows the opposite pattern, logging or metrics
calls appearing directly inside Domain Model classes, an entity constructor
that calls `ILogger.LogInformation`, is a visible smell that infrastructure
has leaked into the one ring the pattern promises will never see it.
Similarly, a spike of generic, untyped exceptions surfacing at the
Application Services boundary, a raw `SqlException` propagating past a
repository's `find` method instead of being translated into a typed domain
exception or a null result, indicates the adapter is failing to do the one
job a port implementation exists to do, hide its own implementation detail
from everything further in.

## 17. Security and privacy implications

The port boundary is a natural, and often underused, single chokepoint for
authorization and validation. Because every path to persistence or an
external system runs through exactly one Application Service method per
use case, an authorization check placed there covers every current and
future UI or API surface that calls it, rather than needing to be
reimplemented per controller as a traditional layered design tends to
produce. The same is true for field level encryption or PII redaction
applied consistently inside a single Infrastructure adapter, one
`EfOrderRepository.save` implementation, rather than at every raw call site
that happens to touch that table across a codebase.

The main risk this entry can point to plainly, as engineering judgement
rather than a sourced finding, is a common reaction to the ORM ergonomics
cost named in dimension 10. Some teams, frustrated that a pure Domain Model
does not map cleanly onto their ORM's expectations, add ORM or serialization
attributes directly onto domain entities to make the mapping easier. Doing
so reintroduces exactly the outward dependency the pattern exists to
prevent, and it does so specifically in the form of a third party
deserialization library now loaded into the one part of the application that
was supposed to be free of external attack surface. Whether this trade off
is acceptable is a judgement call for the team, not a fact this entry can
assert, but the mechanism by which it reopens an attack surface is concrete
and worth naming.

The composition root, because it is the single place where every concrete
infrastructure choice for the application is made, is also the single place
where the configuration those choices need, connection strings, API keys,
credentials for a payment gateway, naturally concentrates. Treating the
composition root's configuration source with the same care as any other
secrets store, rather than treating it as ordinary application code, follows
directly from that concentration.

## Code examples

Four languages where the pattern's dependency inversion mechanics differ in
a way worth showing directly. TypeScript and Python use nominal or
structural interfaces close to Palermo's original .NET shape. Go satisfies
the port through implicit structural typing, so the adapter never writes the
word "implements" anywhere, which is the language idiomatic difference
called out in dimension 8. Rust expresses the port as a trait and threads it
through generics rather than a container, showing the pattern with no
runtime dependency injection framework at all. Java is omitted here only
because a JDK toolchain was not available to compile it in this environment,
not because the pattern is any less idiomatic there, its shape would be
close to the TypeScript example, an interface plus a class implementing it.

### TypeScript

```typescript
// --- Domain layer: no imports from any other layer.
class Order {
  private constructor(
    readonly id: string,
    readonly total: number,
    private status: "Pending" | "Shipped",
  ) {}

  static place(id: string, total: number): Order {
    if (total <= 0) throw new Error("Order total must be positive");
    return new Order(id, total, "Pending");
  }

  ship(): Order {
    if (this.status !== "Pending") throw new Error("Only pending orders ship");
    return new Order(this.id, this.total, "Shipped");
  }

  get currentStatus() {
    return this.status;
  }
}

// --- Domain layer: a port. An interface the domain/application needs,
// with zero knowledge of who satisfies it.
interface OrderRepository {
  save(order: Order): Promise<void>;
  find(id: string): Promise<Order | undefined>;
}

// --- Application layer: orchestrates domain objects through the port.
// Depends only on the domain layer and the port interface above.
class ShipOrder {
  constructor(private readonly repo: OrderRepository) {}

  async execute(orderId: string): Promise<Order> {
    const order = await this.repo.find(orderId);
    if (!order) throw new Error(`Order ${orderId} not found`);
    const shipped = order.ship();
    await this.repo.save(shipped);
    return shipped;
  }
}

// --- Infrastructure layer: implements the port. Depends inward on the
// domain layer's interface; the domain layer never imports this file.
class InMemoryOrderRepository implements OrderRepository {
  private store = new Map<string, Order>();
  async save(order: Order): Promise<void> {
    this.store.set(order.id, order);
  }
  async find(id: string): Promise<Order | undefined> {
    return this.store.get(id);
  }
}

// --- Composition root: the only place that wires infrastructure to
// application. Everything above this line has never heard of "InMemory".
async function main() {
  const repo = new InMemoryOrderRepository();
  await repo.save(Order.place("ord-1", 42.5));

  const shipOrder = new ShipOrder(repo);
  const result = await shipOrder.execute("ord-1");
  console.log(`Order ${result.id} is now ${result.currentStatus}`);
}

main();
```

### Python

```python
"""Onion Architecture in Python: domain -> application -> infrastructure."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


# --- Domain layer: no import of application or infrastructure.
@dataclass(frozen=True)
class Order:
    id: str
    total: float
    status: str = "Pending"

    def __post_init__(self) -> None:
        if self.total <= 0:
            raise ValueError("Order total must be positive")

    def ship(self) -> "Order":
        if self.status != "Pending":
            raise ValueError("Only pending orders ship")
        return Order(self.id, self.total, "Shipped")


# --- Domain layer: a port, declared where the domain needs it.
class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> None: ...

    @abstractmethod
    def find(self, order_id: str) -> Order | None: ...


# --- Application layer: depends on the domain and the port, on nothing else.
class ShipOrder:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    def execute(self, order_id: str) -> Order:
        order = self._repo.find(order_id)
        if order is None:
            raise LookupError(f"Order {order_id} not found")
        shipped = order.ship()
        self._repo.save(shipped)
        return shipped


# --- Infrastructure layer: implements the port, depends inward.
class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._store: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._store[order.id] = order

    def find(self, order_id: str) -> Order | None:
        return self._store.get(order_id)


# --- Composition root: the only module that names InMemoryOrderRepository.
def main() -> None:
    repo = InMemoryOrderRepository()
    repo.save(Order(id="ord-1", total=42.5))

    ship_order = ShipOrder(repo)
    result = ship_order.execute("ord-1")
    print(f"Order {result.id} is now {result.status}")


if __name__ == "__main__":
    main()
```

### Go

Go has no `implements` keyword. `InMemoryOrderRepository` satisfies
`OrderRepository` purely because its method set matches, which is the
structural typing difference named in dimension 8.

```go
package main

import (
	"errors"
	"fmt"
	"log"
)

// --- Domain layer: no import of application or infrastructure packages.
type Order struct {
	ID     string
	Total  float64
	status string
}

func PlaceOrder(id string, total float64) (Order, error) {
	if total <= 0 {
		return Order{}, errors.New("order total must be positive")
	}
	return Order{ID: id, Total: total, status: "Pending"}, nil
}

func (o Order) Ship() (Order, error) {
	if o.status != "Pending" {
		return o, errors.New("only pending orders ship")
	}
	o.status = "Shipped"
	return o, nil
}

func (o Order) Status() string { return o.status }

// --- Domain layer: a port. Application and infrastructure both depend on
// this interface; it depends on neither.
type OrderRepository interface {
	Save(order Order) error
	Find(id string) (Order, bool)
}

// --- Application layer: depends on the domain type and the port only.
type ShipOrder struct {
	Repo OrderRepository
}

func (s ShipOrder) Execute(orderID string) (Order, error) {
	order, ok := s.Repo.Find(orderID)
	if !ok {
		return Order{}, fmt.Errorf("order %s not found", orderID)
	}
	shipped, err := order.Ship()
	if err != nil {
		return Order{}, err
	}
	if err := s.Repo.Save(shipped); err != nil {
		return Order{}, err
	}
	return shipped, nil
}

// --- Infrastructure layer: implements the port, depends inward on it.
type InMemoryOrderRepository struct {
	store map[string]Order
}

func NewInMemoryOrderRepository() *InMemoryOrderRepository {
	return &InMemoryOrderRepository{store: make(map[string]Order)}
}

func (r *InMemoryOrderRepository) Save(order Order) error {
	r.store[order.ID] = order
	return nil
}

func (r *InMemoryOrderRepository) Find(id string) (Order, bool) {
	o, ok := r.store[id]
	return o, ok
}

// --- Composition root: the only function that names InMemoryOrderRepository.
func main() {
	repo := NewInMemoryOrderRepository()
	order, err := PlaceOrder("ord-1", 42.5)
	if err != nil {
		log.Fatal(err)
	}
	if err := repo.Save(order); err != nil {
		log.Fatal(err)
	}

	shipOrder := ShipOrder{Repo: repo}
	result, err := shipOrder.Execute("ord-1")
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Order %s is now %s\n", result.ID, result.Status())
}
```

### Rust

The port is a trait, and `ShipOrder` is generic over any type that
implements it, so the dependency inversion is enforced by the compiler at
the type parameter boundary rather than by a runtime container.

```rust
use std::collections::HashMap;
use std::process;

// --- Domain layer: no `use` of application or infrastructure modules.
#[derive(Clone, Debug, PartialEq)]
enum Status {
    Pending,
    Shipped,
}

#[derive(Clone, Debug)]
struct Order {
    id: String,
    total: f64,
    status: Status,
}

impl Order {
    fn place(id: &str, total: f64) -> Result<Order, String> {
        if total <= 0.0 {
            return Err("order total must be positive".into());
        }
        Ok(Order { id: id.into(), total, status: Status::Pending })
    }

    fn ship(mut self) -> Result<Order, String> {
        if self.status != Status::Pending {
            return Err("only pending orders ship".into());
        }
        self.status = Status::Shipped;
        Ok(self)
    }
}

// --- Domain layer: a port, expressed as a trait. Application and
// infrastructure both depend on this trait; it depends on neither.
trait OrderRepository {
    fn save(&mut self, order: Order);
    fn find(&self, id: &str) -> Option<Order>;
}

// --- Application layer: depends on the domain type and the trait only.
struct ShipOrder<'a, R: OrderRepository> {
    repo: &'a mut R,
}

impl<'a, R: OrderRepository> ShipOrder<'a, R> {
    fn execute(&mut self, order_id: &str) -> Result<Order, String> {
        let order = self.repo.find(order_id).ok_or_else(|| format!("order {order_id} not found"))?;
        let shipped = order.ship()?;
        self.repo.save(shipped.clone());
        Ok(shipped)
    }
}

// --- Infrastructure layer: implements the port, depends inward on it.
struct InMemoryOrderRepository {
    store: HashMap<String, Order>,
}

impl InMemoryOrderRepository {
    fn new() -> Self {
        InMemoryOrderRepository { store: HashMap::new() }
    }
}

impl OrderRepository for InMemoryOrderRepository {
    fn save(&mut self, order: Order) {
        self.store.insert(order.id.clone(), order);
    }
    fn find(&self, id: &str) -> Option<Order> {
        self.store.get(id).cloned()
    }
}

// --- Composition root: the only function that names InMemoryOrderRepository.
fn main() {
    let mut repo = InMemoryOrderRepository::new();
    let order = match Order::place("ord-1", 42.5) {
        Ok(o) => o,
        Err(e) => { eprintln!("{e}"); process::exit(1); }
    };
    repo.save(order);

    let mut ship_order = ShipOrder { repo: &mut repo };
    let result = match ship_order.execute("ord-1") {
        Ok(o) => o,
        Err(e) => { eprintln!("{e}"); process::exit(1); }
    };
    println!("Order {} is now {:?}", result.id, result.status);
}
```

## 18. References

1. Jeffrey Palermo. "The Onion Architecture. Part 1". jeffreypalermo.com,
   29 July 2008.
   https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/
   Verified 2026-08-02. Coining source for the name, the four ring
   structure, and the "database is not the center" statement.
2. Jeffrey Palermo. "The Onion Architecture. Part 2". jeffreypalermo.com,
   2008. https://jeffreypalermo.com/2008/07/the-onion-architecture-part-2/
   Verified 2026-08-02. Source for the constructor injection and IoC
   container wiring example used in dimensions 7 and 8.
3. Jeffrey Palermo. "The Onion Architecture. Part 3". jeffreypalermo.com,
   August 2008.
   https://jeffreypalermo.com/2008/08/the-onion-architecture-part-3/
   Verified 2026-08-02. Source for the infrastructure as commodity framing
   used in dimensions 2 and 17, and the direct quote on testability.
4. Alistair Cockburn. "Hexagonal Architecture". alistair.cockburn.us,
   version 0.9, first published 4 September 2005.
   https://alistair.cockburn.us/hexagonal-architecture
   Verified 2026-08-02. Source for the ports and adapters sibling pattern
   discussed in dimensions 1, 8, and 13.
5. Robert C. Martin. "The Clean Architecture". blog.cleancoder.com,
   13 August 2012.
   https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
   Verified 2026-08-02. Source for the direct statement that Hexagonal,
   Onion, and Clean Architecture share one objective.
6. Robert C. Martin. *Clean Architecture. A Craftsman's Guide to Software
   Structure and Design*. Pearson, 2017. ISBN 978-0-13-449416-6. Part V,
   chapter 22, "The Clean Architecture", page 201. Source for the four
   named rings, Entities, Use Cases, Interface Adapters, Frameworks and
   Drivers, discussed in dimension 8.
7. Microsoft. "Common web application architectures". learn.microsoft.com.
   https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures
   Verified 2026-08-02. Source for the eShopOnWeb and Ardalis Clean
   Architecture Template production uses in dimension 9, and for the
   explicit statement that Onion Architecture is one of the names this
   concentric ring design has gone by.
8. GitHub. Repository metadata for `dotnet-architecture/eShopOnWeb`.
   https://github.com/dotnet-architecture/eShopOnWeb
   Verified 2026-08-02 via the GitHub API. Star count and description cited
   in dimension 9.
9. GitHub. Repository metadata for `ardalis/CleanArchitecture`.
   https://github.com/ardalis/CleanArchitecture
   Verified 2026-08-02 via the GitHub API. Star count and description cited
   in dimension 9.
10. ABP.IO. "Layered solution structure".
    https://abp.io/docs/latest/solution-templates/layered-web-application/solution-structure
    Verified 2026-08-02. Source for the ABP Framework production use in
    dimension 9, including the named project layout and the dependency
    direction between the `EntityFrameworkCore`, `Domain`, and `Web`
    projects.
11. GitHub. Repository metadata for `abpframework/abp`.
    https://github.com/abpframework/abp
    Verified 2026-08-02 via the GitHub API. Star count cited in dimension 9.
