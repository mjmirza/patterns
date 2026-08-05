---
name: Layered Architecture
slug: layered-architecture
family: 05-architectural
category: Architectural
aliases: [N-Tier Architecture, Multitier Architecture, N-Layer Architecture, Presentation-Domain-Data Layering]
first_described: "Buschmann, Meunier, Rohnert, Sommerlad, Stal 1996"
maturity: canonical
related: [hexagonal-architecture, onion-architecture, dependency-injection, repository, facade, mvc]
incompatible_with: []
verified: 2026-08-02
---

# Layered Architecture

## 1. Name, aliases, and lineage

The canonical name in the architectural pattern literature is Layers, described
by Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, and Michael
Stal in *Pattern-Oriented Software Architecture, Volume 1. A System of
Patterns*, Wiley, 1996, as one of the foundational architectural patterns of
the book, alongside Broker, Pipes and Filters, and Model-View-Controller
([Wikipedia summary of the POSA catalog and the Layers entry, citing the 1996
Buschmann et al. volume](https://en.wikipedia.org/wiki/Multitier_architecture),
verified 2026-08-02). In application development the same idea is called
N-Tier Architecture, Multitier Architecture, or N-Layer Architecture depending
on whether the author is talking about logical separation or physical
deployment, a distinction that matters enough to earn its own note below.

Martin Fowler uses the phrase Presentation-Domain-Data Layering for the
specific three-layer instance built from a user interface layer, a domain
logic layer, and a data access layer, and treats it as one of the most common
starting shapes for a business application
([Martin Fowler, "PresentationDomainDataLayering," martinfowler.com, published
26 August 2015](https://martinfowler.com/bliki/PresentationDomainDataLayering.html),
verified 2026-08-02). Fowler is explicit that the three names are not fixed.
He says the layer boundaries are logical, that the pattern predates any single
named source, and that his own writeup is a distillation of a shape he
observed across many codebases rather than an invention.

A separate lineage runs through enterprise Java. The three-tier client-server
model, Presentation, Business, Data, was standard vocabulary in J2EE
literature by the late 1990s, and the Microsoft .NET world independently
converged on the same shape under the labels UI, BLL (Business Logic Layer),
and DAL (Data Access Layer)
([Microsoft Learn, "Common web application architectures," .NET
documentation, last updated 8 July 2026, original content dated 12 December
2021](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures),
verified 2026-08-02). The two lineages, POSA's academic pattern-language
formalization and the independent industry convergence in Java and .NET
tooling, arrived at the same structural idea from different directions, which
is one reason the pattern reads as inevitable rather than invented.

It is worth naming plainly that Layers as an architectural pattern and the
OSI network reference model are two different things that happen to share a
word. The OSI model is a communication protocol stack standardized by
ISO/IEC 7498-1, and its own documentation puts the discipline directly. The
page states, in its own words, "Each entity interacted directly only with the
layer immediately beneath it and provided facilities for use by the layer
above it"
([Wikipedia, "OSI model,"](https://en.wikipedia.org/wiki/OSI_model), verified
2026-08-02). That sentence is a precise description of strict layering as a
general discipline, and it is useful as an illustration of the same rule
applied outside software architecture, but the OSI model is not itself an
instance of the application-architecture pattern this entry documents. Citing
it as a production use of Layers the architectural pattern would be a category
error. Citing it as evidence that strict layering is a load-bearing idea
across engineering disciplines is fair, and that is the only use made of it
here.

## 2. Problem and context

A non-trivial application has at least three concerns that change for
different reasons and at different rates. how information is presented to a
user or another system, what business rules govern the data, and how the data
is stored and retrieved. Left unmanaged, code that renders a screen also
validates a discount policy and also issues a SQL statement, often in the same
method. The first symptom is not a crash. It is that a change to the discount
policy requires touching the screen-rendering code, and a change to the
database vendor requires touching the business rule code, because nothing
separates them.

The context in which the pattern earns its place is a system built by more
than one person, expected to survive more than one release, where the three
concerns above (or a similar split specific to the domain) genuinely change on
different schedules. A UI redesign should not risk the tax calculation. A
database migration should not risk the checkout flow. A system with one
concern, one author, and a short lifespan does not need this pattern, because
the coordination cost of maintaining layer boundaries is a real cost and it
buys nothing when there is no independent variation to protect against.
Fowler makes this same point about scope. He names the benefit first as
reducing "the scope of my attention," and a smaller system already has a
small scope of attention with no help required
([Fowler, "PresentationDomainDataLayering,"](https://martinfowler.com/bliki/PresentationDomainDataLayering.html),
verified 2026-08-02).

The specific technical problem the pattern solves is dependency direction
under change. Without layering, a change to storage technology can, in the
worst case, ripple to the presentation code because nothing prevents a
presentation-layer class from calling a database driver directly. The
Microsoft .NET architecture guide states the underlying goal plainly. The
guide reads, "With a layered architecture, applications can enforce
restrictions on which layers can communicate with other layers. This
architecture helps to achieve encapsulation. When a layer is changed or
replaced, only those layers that work with it should be impacted"
([Microsoft Learn, "Common web application architectures,"](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures),
verified 2026-08-02).

## 3. Forces

This dimension is largely engineering judgement about which force dominates in
a given system. The individual claims about what a named source says are
sourced separately below.

**Cognitive load versus indirection cost.** A layer boundary is a promise.
that to understand the domain layer you do not need to read the presentation
layer. That promise reduces the amount a single developer must hold in
working memory at once, which is the benefit Fowler names as primary. The
cost is paid on every call that crosses a boundary, because a boundary
usually implies an interface, a data-transfer shape distinct from the
underlying entity, and a mapping step between them. For a small system the
mapping overhead can exceed the cognitive saving. For a system with several
independent teams working in parallel, the saving dominates because it lets
each team reason locally.

**Coupling versus duplication.** Strict layering (defined formally in
dimension 8) forbids a layer from skipping past its immediate neighbor. This
reliably prevents the specific failure mode where a UI class holds a raw SQL
connection, but it can also force the middle layer to expose pass-through
methods that do nothing except forward a call, which some engineers
experience as needless indirection rather than protection. Relaxed layering
trades some of that coupling discipline for less boilerplate.

**Testability versus realism.** A boundary that is expressed as an interface
is a seam a test double can stand in for. Testing the business layer with a
fake data-access implementation is fast and does not require a database
connection. The cost is that a test suite built entirely on fakes can pass
while the real integration between layers is broken. The pattern does not
remove the need for integration tests that exercise the layers together, it
only makes unit-level isolation cheap.

**Deployability versus latency.** When layers are also deployed as separate
processes (tiers, in the terminology below), a change to one tier can ship
independently, and a tier can be scaled independently of the others. The
Microsoft guide gives the concrete example of a product-catalog component
needing far more read capacity than a payment component in a retail system,
which physical tiering allows to be scaled separately
([Microsoft Learn,](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures),
verified 2026-08-02). The cost is a network hop and its associated latency and
failure modes at every tier boundary, which a purely logical layering inside
one process does not pay.

**Dependency direction versus the reality of persistence.** Traditional
top-to-bottom layering, where the UI depends on business logic and business
logic depends on data access, means the layer that usually holds the most
valuable logic, the business layer, has a compile-time dependency on a
data-access implementation detail. The Microsoft guide names this directly as
a disadvantage of the traditional shape and points at the Dependency
Inversion Principle, realized architecturally as Hexagonal or Clean
Architecture, as the fix
([Microsoft Learn,](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures),
verified 2026-08-02). Layered Architecture in its traditional form favors
simplicity of the dependency graph over independence of the domain layer. It
sacrifices the domain layer's independence from persistence in exchange for a
dependency graph that is trivial to draw and trivial to onboard a new
developer onto.

## 4. Applicability and non-applicability

**Reach for Layered Architecture when.**

- The system has at least three concerns (presentation, domain logic, data
  access, or a domain-specific equivalent) that plausibly change on different
  schedules or are owned by different people.
- The team is larger than one, or the codebase is expected to outlive the
  original author's exclusive attention.
- The organization's existing tooling, frameworks, and hiring pool already
  assume this shape. Most mainstream web frameworks (ASP.NET Core MVC, Spring
  MVC, Django, Ruby on Rails) scaffold a layered or near-layered structure by
  default, and swimming against that default has a real cost.
- Persistence technology is stable and not expected to change frequently, so
  the traditional top-to-bottom dependency (business logic depending on data
  access) is an acceptable, low-risk simplification rather than a real
  constraint.
- The system is a conventional CRUD-shaped business application. it takes
  input, applies rules, and persists or retrieves records, without an
  unusually rich domain model that would benefit from being fully isolated
  from infrastructure concerns.

**Do NOT reach for Layered Architecture when.**

- The domain logic is rich enough that isolating it completely from
  infrastructure (databases, message queues, third-party APIs) is a genuine
  design goal, because traditional top-to-bottom layering makes the domain
  layer depend on the data-access layer, not the reverse. Hexagonal or Clean
  Architecture, which inverts that dependency, is the better fit. The
  Microsoft guide describes exactly this migration path from N-Layer to Clean
  Architecture as a response to this limitation
  ([Microsoft Learn,](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures),
  verified 2026-08-02).
- The system's real complexity is in coordinating many independent business
  capabilities that must scale, deploy, and fail independently. A single set
  of logical layers inside one process does not give you independent
  deployment. that requires a microservices decomposition organized around
  business capability boundaries, not technical-concern boundaries, and
  layering within each individual service remains a separate, smaller
  decision.
- The application is small, short-lived, or has a single author with the
  whole system already fitting comfortably in one person's head. The
  coordination overhead of maintaining boundaries, interfaces, and mapping
  code between layers is a real tax with no offsetting benefit at that scale.
- The system's dominant force is raw throughput at a tight latency budget
  where every extra function call, interface dispatch, or DTO mapping is
  measurable cost, such as a hot path in a trading system or a real-time
  audio pipeline. Layering adds indirection that a hand-tuned hot path
  usually cannot afford.
- The team is trying to use layers as a substitute for organizing large
  systems into business-capability modules. Fowler warns against exactly this
  substitution. presentation-domain-data layering "shouldn't be the top level
  way to break up a substantial code base," and for a large application the
  first cut should be by business module, with layering applied inside each
  module rather than across the whole system
  ([Fowler,](https://martinfowler.com/bliki/PresentationDomainDataLayering.html),
  verified 2026-08-02).

## 5. Structure

The canonical three-layer instance has these participants. A real system may
add layers (a distinct application-service layer, a facade layer, an
anti-corruption layer at an integration boundary) without changing the
underlying discipline. what follows is the minimal, most common shape.

- **Presentation layer.** Owns everything about how information reaches and
  is received from an actor outside the system. HTTP controllers, view
  templates, CLI argument parsing, gRPC service handlers, or a GUI's
  event-handling code. It translates external requests into calls the domain
  layer understands and translates domain results back into a response shape
  (HTML, JSON, a view model). It holds no business rule and no persistence
  detail.
- **Domain layer** (also called Business Logic Layer, BLL, or Application
  Core). Owns the rules that make the system what it is. validation beyond
  simple type checking, calculations, workflow state transitions, policy
  decisions. It is expressed in terms the business would recognize, not in
  terms of HTTP status codes or SQL rows. It depends on the data-access
  layer's interface, in the traditional variant, to fetch and persist the
  entities it works with.
- **Data access layer** (also called Data Access Layer, DAL, or Repository
  layer). Owns the mechanics of getting data in and out of durable storage.
  SQL statements or an ORM's query API, connection management, schema
  mapping. It exposes an interface expressed in domain terms (find an order
  by identifier, save a customer) and hides the storage technology behind
  that interface.
- **Cross-cutting infrastructure** (not a layer in the vertical sense, but a
  required participant). Logging, authentication, configuration, and
  dependency injection wiring typically span all three layers rather than
  belonging to one. Most real codebases isolate this as a fourth, orthogonal
  concern rather than forcing it into one of the three vertical layers.

Named production examples of this exact three-part split are given with
sources in dimension 9.

## 6. ASCII structure diagram

```
                    Presentation Layer
        (HTTP controllers, view templates, CLI, API)
        depends on
                    v
                    Domain Layer
        (business rules, workflow, calculations)
        depends on
                    v
                    Data Access Layer
        (repositories, ORM mappings, SQL)
        depends on
                    v
                    Data Store
        (relational database, document store, files)

Strict layering.  each arrow only crosses ONE boundary.
Relaxed layering.  Presentation may call Data Access directly
                    for simple read-only queries (dashed arrow
                    below, dimension 8 gives the trade-off).

     Presentation ----------------------------.
          |                                    |
          v                                    v
        Domain  ------------------------->  Data Access
```

## 7. Dynamics

A typical request-response cycle through the strict three-layer shape looks
like this.

```
Actor            Presentation        Domain             Data Access        Store
  |  request           |                |                    |               |
  |------------------->|                |                    |               |
  |                     | parse/validate|                    |               |
  |                     | shape         |                    |               |
  |                     |-------------->|                    |               |
  |                     |               | apply business rule|               |
  |                     |               | needs data          |               |
  |                     |               |------------------->|               |
  |                     |               |                    | build query   |
  |                     |               |                    |-------------->|
  |                     |               |                    |<--------------|
  |                     |               |                    | map to entity |
  |                     |               |<--------------------               |
  |                     |               | evaluate rule,     |               |
  |                     |               | decide, persist    |               |
  |                     |               |------------------->|               |
  |                     |               |                    |-------------->|
  |                     |               |                    |<--------------|
  |                     |               |<--------------------               |
  |                     |<--------------|                    |               |
  |                     | build response|                    |               |
  |<--------------------|                |                    |               |
```

The important property to observe is that the presentation layer never talks
to the data access layer directly and the data access layer never invokes the
domain layer. Every message travels one hop at a time, up or down. If a
failure occurs (a validation error in the domain layer, a constraint violation
at the store), it propagates back up through exactly the same path it came
down, layer by layer, which is what makes each layer able to translate the
failure into a shape appropriate to that layer. the domain layer turns a
database constraint violation into a domain-specific exception, and the
presentation layer turns that domain exception into an HTTP status code or a
user-facing message.

## 8. Implementation variants

**Strict layering.** A layer may only call the layer directly beneath it,
never skip a layer. This is the formal POSA definition, and it is what makes
each layer replaceable in isolation, because nothing outside the layer
immediately above it has a compile-time dependency on it. The cost is that a
simple pass-through operation (fetch a record with no business logic applied)
still has to travel through the domain layer, which can turn into a stack of
methods that just forward their arguments.

**Relaxed layering.** A layer may call any layer beneath it, not only the
adjacent one, most commonly used to let the presentation layer read directly
from the data access layer for simple, read-only queries that carry no
business rule (a lookup list for a dropdown, for example), while writes and
anything rule-bearing still travel through the domain layer. This trades some
of the isolation guarantee for less boilerplate. the risk is that "simple
read" silently grows business logic over time because the shortcut path was
never removed once it was no longer simple. The POSA catalog explicitly
distinguishes strict from relaxed layering as two named variants of the same
pattern, per the Wikipedia summary that cites the 1996 volume
([Wikipedia, "Multitier architecture,"](https://en.wikipedia.org/wiki/Multitier_architecture),
verified 2026-08-02).

**Logical layers versus physical tiers.** A layer is a compile-time or
module-level separation. a tier is a separate deployable unit, often on
separate hardware, communicating over a network. The Microsoft .NET guide
states this distinction precisely. The guide's own note reads, "*Layers*
represent logical separation within the application. In the event that
application logic is physically distributed to separate servers or
processes, these separate physical deployment targets are referred to as
*tiers*. It's possible, and quite common, to have an N-Layer application that
is deployed to a single tier"
([Microsoft Learn,](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures),
verified 2026-08-02). A three-layer monolith deployed as one process is still
Layered Architecture. it becomes a three-tier system only when the
presentation, domain, and data-access code run in genuinely separate
processes with a network boundary between them.

**Inverted dependency (the Clean/Hexagonal correction).** The traditional
variant has the domain layer depend on the data access layer's concrete
implementation, or at least on an interface owned by the data access side.
The inverted variant defines the data-access interface inside the domain
layer (an "Application Core," in the Microsoft guide's terminology) and has
the data access implementation depend on that interface instead, which
reverses the arrow shown in dimension 6 for the domain-to-data-access edge.
This variant is a distinct, related pattern (see dimension 13) rather than a
sub-variant of Layered Architecture proper, but it is worth naming here
because teams frequently arrive at it by starting from a traditional layered
system and inverting one dependency at a time.

**Language-idiomatic shape.** In statically-typed, interface-heavy languages
(Java, C#, Go, Rust) each layer boundary is usually an explicit interface or
trait with one or more concrete implementations, wired together by a
dependency-injection container or, in Go, by simple constructor injection with
no framework at all. In more dynamic languages (Python, Ruby, JavaScript) the
same boundary is often enforced by module or package structure and by
convention rather than by a compiler-checked interface, which makes the
boundary easier to violate accidentally and correspondingly more dependent on
code review and linting to hold.

## 9. Known production uses

**ASP.NET Core reference architecture (Microsoft).** Microsoft's own
architecture guide describes and names the traditional "N-Layer" shape (UI,
BLL, DAL) as the most common organization of application logic in .NET web
applications, and ships a companion reference application, eShopOnWeb, that
demonstrates both the traditional layered form and the inverted Clean
Architecture form for direct comparison
([Microsoft Learn, "Common web application architectures,"](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures),
verified 2026-08-02; reference application at
[github.com/dotnet-architecture/eShopOnWeb](https://github.com/dotnet-architecture/eShopOnWeb)).

**Spring PetClinic (Spring / VMware).** The official Spring sample
application used across the Spring ecosystem's own documentation and training
material implements the pattern with named classes rather than an abstract
description. `OwnerController`, `PetController`, and `VisitController` in the
presentation layer, and `OwnerRepository` and `PetTypeRepository` in the data
access layer, in the `org.springframework.samples.petclinic.owner` package
([github.com/spring-projects/spring-petclinic, directory
`src/main/java/org/springframework/samples/petclinic/owner`](https://github.com/spring-projects/spring-petclinic/tree/main/src/main/java/org/springframework/samples/petclinic/owner),
verified 2026-08-02). This is the concrete Controller-Repository split named
in the trade-off matrix below.

**ISO/IEC 7498-1, the OSI reference model.** Cited here only as evidence that
the strict-layering discipline (a layer talks only to its immediate neighbor)
is a load-bearing engineering idea outside application architecture as well,
per the direct quote in dimension 1. This is a different pattern instance in
a different domain (network protocol stacking, not application-code
organization), named to be transparent about its scope rather than presented
as a use of this specific pattern.

**J2EE / Jakarta EE three-tier convention.** The Presentation, Business,
Data-tier vocabulary used throughout Java Platform, Enterprise Edition
documentation and its Jakarta EE successor is the same shape under different
names, and is the direct ancestor of the "BLL/DAL" naming that shows up in
.NET tooling. The Microsoft guide's own N-Layer diagram uses the same
three-part split, evidence of the two ecosystems converging on one structure
independently, as already cited above.

## 10. Consequences

**Positive.**

- A change confined to how data is presented does not require touching
  business rules or persistence code, and the reverse holds for a change
  confined to storage technology, as long as the layer's public interface is
  unchanged.
- The domain layer can be unit tested against a fake or in-memory
  implementation of the data-access interface, without a real database,
  because the interface is the seam.
- New team members can be productive inside one layer without first
  understanding the whole system, because the presentation layer's vocabulary
  (requests, views, status codes) is different from the domain layer's
  vocabulary (entities, rules, workflow) and each is self-contained enough to
  learn independently.
- The shape matches the default scaffolding of most mainstream web
  frameworks, so onboarding a new developer who already knows the framework
  costs less than onboarding them onto a bespoke architecture.

**Negative.**

- The traditional variant's dependency direction runs top to bottom, which
  means the domain layer, usually the most valuable code in the system,
  depends on data-access implementation details, and testing it in true
  isolation without any database concern requires either the inverted variant
  or careful interface discipline that the traditional variant does not
  enforce by itself.
- Strict layering can force pass-through code. a domain-layer method that
  does nothing but call a data-access method and return its result, purely to
  respect the "one hop at a time" rule. This is real, visible boilerplate
  with no immediate benefit beyond the discipline itself.
- The three-way split (presentation, domain, data) is a technical-concern
  split, not a business-capability split. Fowler's own warning applies at
  scale. Using it as the top-level organizing principle of a large codebase
  produces a system where finding all the code for one business feature
  requires visiting three widely separated folders, one per layer, rather
  than one folder per feature
  ([Fowler,](https://martinfowler.com/bliki/PresentationDomainDataLayering.html),
  verified 2026-08-02).
- Logical layering with no physical tiering gives none of the independent
  scaling or independent deployment benefits that are commonly, and
  incorrectly, assumed to come with "having layers." Those benefits require
  tiers, not layers, and conflating the two is a frequent source of
  disappointment when a team layers a monolith and then is surprised it still
  deploys and scales as one unit.

## 11. Failure modes and misuse

**Symptom.** A change to the UI requires a database migration.
**Cause.** The presentation layer has a direct, uninterfaced dependency on a
concrete data-access class, usually introduced as a shortcut for a
performance-sensitive read, and the shortcut path accumulates business logic
over time until it is no longer a simple read.
**Fix.** Move the accumulated logic into the domain layer and either restore
strict layering for that path or, if the relaxed-layering variant is
intentional, keep the direct read path free of anything beyond a literal
column selection, enforced by code review.

**Symptom.** Unit tests for the domain layer require a running database.
**Cause.** The domain layer depends on a concrete data-access implementation
rather than an interface, so there is no seam a test double can substitute
into. This is the traditional variant's known weakness, described directly in
dimension 3.
**Fix.** Introduce an interface owned by the domain layer, or at minimum a
narrow, domain-facing interface even if it lives in the data-access project,
and have the concrete implementation satisfy it. Inject the implementation at
composition time rather than constructing it inside domain code.

**Symptom.** Adding one new feature requires editing files in four different
top-level folders, and the pull request diff is hard to review because the
changes are scattered.
**Cause.** The codebase is organized by technical layer at the top level
(`controllers/`, `services/`, `repositories/`) rather than by business
capability, so a single feature's presentation, domain, and data-access code
live far apart. This is exactly the anti-pattern Fowler names when he says
layering should not be the top-level modularization for a large codebase.
**Fix.** Introduce a feature or module boundary above the layer boundary, so
each business module contains its own presentation, domain, and data-access
slice, and layering is applied within a module rather than across the whole
application.

**Symptom.** The domain layer silently starts calling the presentation
layer, for example to send a notification or format a message, and now a
circular dependency exists that the build tool refuses.
**Cause.** Notification, formatting, or messaging code was added to the
domain layer without recognizing it as a cross-cutting concern (dimension 5)
that does not belong to any single layer.
**Fix.** Extract the cross-cutting concern into its own module with its own
interface, invoked by the domain layer through that interface, never by the
domain layer reaching upward into presentation.

**Symptom.** The "one layer, one team" assumption breaks down because one
team owns the whole vertical slice for a feature and now has to coordinate
three different teams (UI, business, data) to ship anything.
**Cause.** The organization staffed itself around the technical layers
rather than around business capabilities, which Conway's Law then locks in as
the architecture's shape regardless of what the code diagrams claim.
**Fix.** This is an organizational fix, not a code fix. Either restructure
teams around vertical feature slices, or accept the coordination cost as the
price of the current org chart, but recognize it as an org decision rather
than treat every resulting delay as a code-quality problem.

## 12. Trade-off matrix

| Force | Layered Architecture (traditional) | Hexagonal / Onion / Clean Architecture | Microservices (business-capability split) |
|---|---|---|---|
| Domain layer's dependency on persistence | Domain depends on data access; hard to test in true isolation without an interface discipline the pattern does not enforce | Domain defines the interface; infrastructure depends on domain, so the domain is testable with zero infrastructure present | Each service has its own domain-versus-infrastructure question, answered independently per service |
| Onboarding cost for a developer new to the codebase | Lowest; matches most framework defaults and most developers' prior experience | Higher; the inverted dependency direction is unfamiliar until seen once | Highest; a new developer must also learn service boundaries and inter-service communication |
| Independent deployability | None, unless layers are also split into physical tiers | None by itself; still one deployable unit unless combined with a service split | Native; each service deploys independently by construction |
| Cost of a technical-concern-only reorganization at scale | Grows with codebase size; a change to one business feature touches every layer's folder | Same technical-layer scattering risk as traditional layering, this dimension is orthogonal to the dependency-direction fix | Not applicable; the unit of organization is already the business capability |
| Boilerplate from enforcing the boundary | Moderate; strict variant produces pass-through methods | Higher; requires defining and maintaining interfaces plus their implementations | Highest per service, but each service's internal boilerplate is smaller in scope |
| Runtime cost per request | One in-process call per layer, negligible unless the count of layers is unusually high | Same as traditional layering, the dependency direction change does not add a runtime hop | Adds a real network hop per cross-service call, plus serialization |

## 13. Related and incompatible patterns

**Hexagonal Architecture (Ports and Adapters) and Onion Architecture.** Both
are corrections to the traditional variant's weakest force. they invert the
dependency so the domain depends on nothing, and everything else, including
persistence, depends on interfaces the domain defines. The Microsoft .NET
guide frames Clean Architecture explicitly as the answer to the dependency
problem named in dimension 3, and treats it as the natural next step from a
traditional layered application once the domain layer needs to be tested and
evolved independently of storage technology
([Microsoft Learn,](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures),
verified 2026-08-02). These are not incompatible with Layered Architecture.
they are best understood as a stricter, inverted variant of the same idea.

**Repository pattern.** Almost always the concrete shape of the data-access
layer's boundary. The data access layer in dimension 5 is, in practice,
usually one or more Repository implementations behind an interface, as the
Spring PetClinic and eShopOnWeb examples both show directly in their naming
(`OwnerRepository`), and as the Microsoft guide explicitly recommends by
naming the Repository design pattern as the standard way to abstract data
access.

**Facade.** The presentation layer's call into the domain layer is
frequently mediated by a Facade that presents a simplified, use-case-shaped
interface over a domain layer that may internally be composed of several
finer-grained services. This is a composition, not a substitute. Facade
narrows the interface at a boundary that Layered Architecture has already
established.

**Dependency Injection.** The mechanism, in almost every mainstream
implementation, by which a concrete data-access implementation is supplied to
domain-layer code that only knows about the corresponding interface. Without
some form of dependency injection, whether a full container or manual
constructor wiring, the inverted or interface-based variants of layering
degrade back into the traditional, tightly coupled form, because something
still has to construct the concrete implementation and hand it to the code
that needs it.

**Model-View-Controller (MVC).** Frequently confused with Layered
Architecture because both split a system into named parts, but MVC is a
presentation-layer-internal pattern. Model, View, and Controller together
typically occupy only the presentation layer (or, in some framework
conventions, Model spans presentation and domain). MVC does not by itself say
anything about how the domain layer relates to data access. A codebase can
use MVC inside a layered architecture, or MVC with no layering discipline
beneath it at all.

**Microservices.** Not incompatible, but organized around a different axis.
Layered Architecture splits a single deployable unit by technical concern.
Microservices splits a system into several independently deployable units by
business capability. A well-designed microservice frequently uses Layered
Architecture, or one of its inverted variants, internally to organize its own
code, so the two patterns compose at different scales rather than competing.

## 14. Refactoring path in and out

**Introducing layering into an unlayered codebase, step by step.**

1. Identify the three concerns already present but tangled. These are the
   code that talks to an external actor (HTTP, CLI), the code that decides
   something (a rule, a calculation), and the code that reads or writes
   durable storage. These usually already exist, simply not yet separated
   into distinct modules.
2. Extract the data-access code first, because it is usually the most
   mechanically identifiable (anything touching a connection string, an ORM
   session, or a raw query) and the least likely to have hidden business
   logic mixed in. Give it a narrow, domain-facing interface named after what
   it does (`findOrderById`, not `runQuery`).
3. Extract the domain logic next, moving validation, calculation, and
   workflow decisions out of the presentation code and into methods that
   accept and return domain entities or simple values, not framework-specific
   request or response types.
4. Leave the presentation layer last, once it has nothing left to do except
   translate between the external protocol and the domain layer's interface.
   At this point removing dead code from the presentation layer is usually
   the largest visible cleanup, because most of the logic that used to live
   there has moved out.
5. Add tests for the domain layer against a fake implementation of the
   data-access interface before removing the last direct dependency, so the
   safety net exists before the coupling that made testing hard is fully
   gone.

This sequence mirrors Extract Method and Extract Class from Martin Fowler's
refactoring catalog, applied at module scale rather than method scale. Each
extraction step should be small enough to run the existing test suite, or,
where none exists, a small characterization test, immediately after it.

**Removing layering once it has stopped earning its place.** This is rarer
in practice than introducing it, but it happens when a small, single-team
system has grown a layered structure by convention (because the framework
scaffolded it) and the team finds the pass-through boilerplate is now pure
cost with no corresponding benefit, for instance in a small internal tool
with one maintainer and no plan for a second data source. The path is to
collapse layers that have exactly one implementation and no plausible reason
to gain a second, merging a one-to-one Controller-to-Service-to-Repository
chain back into fewer files, while keeping the parts of the boundary
(primarily the data-access interface) that still serve testing. This is a
judgement call specific to each codebase's actual maintenance history, not a
mechanical rule. Collapsing a boundary that a growing team will need again in
six months costs more than the boilerplate it removes.

## 15. Testing and verification

The layer boundaries make three distinct kinds of test economically
different, and a healthy test suite for a layered system uses all three
deliberately rather than defaulting to one.

**Domain-layer unit tests.** Fastest to write and run, because the domain
layer's dependencies (the data-access interface) can be replaced with an
in-memory fake or a hand-written stub that returns fixed data. These tests
should assert business rules directly. given this input entity, the rule
produces this output or raises this domain-specific error. They should never
need a real database connection, and if they do, that is itself a signal the
domain layer's dependency on data access is not properly abstracted (the
failure mode described in dimension 11).

**Data-access integration tests.** Exercise the concrete repository
implementation against a real or realistic database (an in-process SQLite
instance, a Testcontainers-managed Postgres, or similar), asserting that the
mapping between domain entities and storage rows is correct, that queries
return the expected rows, and that constraints behave as the domain layer
assumes. These are slower than domain unit tests and are kept in a separate
suite so they do not slow down the fast feedback loop that domain tests
provide.

**End-to-end tests across all layers.** Exercise a request from the
presentation layer through the domain layer to the data-access layer and
back, verifying the whole chain works together, catching the class of bug
that unit tests against fakes cannot catch. an interface satisfied correctly
in isolation but wired together incorrectly. These are the slowest and
usually the fewest in number, reserved for the critical paths through the
system rather than exhaustive coverage.

The specific technique that makes the domain-layer tests cheap is Fowler's
own framing. He calls the layer boundary "a seam that is good affordance for
testing"
([Fowler,](https://martinfowler.com/bliki/PresentationDomainDataLayering.html),
verified 2026-08-02). Where a layer's boundary is not expressed as an
interface (common in dynamically-typed languages, per dimension 8), the same
seam can be created with monkey-patching, dependency injection at the module
level, or a test-only factory function, but the discipline required to keep
the seam clean is higher because the compiler is not enforcing it.

## 16. Observability signals

A healthy layered system's logs and traces show a clean, monotonic path
through the layers for each request, with each layer's log entries
identifiable by the vocabulary they use. presentation-layer entries reference
HTTP status codes, routes, and request identifiers. domain-layer entries
reference business entities and rule names. data-access-layer entries
reference query shapes, row counts, and connection pool state. A distributed
trace, even for a single-process system using in-process tracing spans,
should show each layer as a distinct span nested inside its caller, one level
deeper per layer, with no span that appears to skip a level, which would
indicate a relaxed-layering shortcut or, worse, an accidental layer
violation.

Signals of an eroding boundary.

- A trace shows the presentation layer's span directly containing a database
  query span with no intervening domain-layer span, on a code path that was
  supposed to be strict layering. This is the runtime signature of the
  bypass described in dimension 11.
- Error logs at the presentation layer contain raw database driver exception
  types or SQL error codes rather than a domain-specific exception, which
  means an error crossed a layer boundary without being translated, and the
  presentation layer now has an implicit dependency on the specific
  persistence technology's error vocabulary.
- Latency percentiles for a single logical operation show a bimodal
  distribution, one cluster consistent with an in-process call and one
  consistent with a network round trip, which indicates that what the
  architecture diagram calls one logical layer is, in production, sometimes a
  local call and sometimes a remote tier, an inconsistency worth surfacing
  explicitly.
- Test suite composition drifting toward end-to-end tests and away from fast
  domain-layer unit tests over time is an indirect but reliable signal that
  the domain layer's isolation from data access has degraded, because
  developers reach for a slower, more realistic test when the fast, isolated
  one has stopped being trustworthy or stopped being possible to write.

## 17. Security and privacy implications

The layer boundary is a natural place to enforce authorization and input
validation exactly once, rather than scattering the same check across every
entry point, provided the enforcement point is chosen deliberately.
Presentation-layer input validation (type checking, format checking, request
size limits) protects against malformed input reaching the domain layer at
all, while domain-layer authorization, meaning whether this actor has the
right to perform this business operation on this specific entity, belongs in
the domain layer because it is a business rule, not a transport-protocol
concern. Placing it only in the presentation layer risks it being bypassed by
any code path that calls the domain layer directly, including background
jobs, internal tooling, or a future second presentation layer (a CLI added
alongside an existing web UI, for example) that the original author did not
anticipate.

The data-access layer is the natural, and often the only, place that should
construct queries with user-supplied values, and centralizing that
construction behind a Repository interface (dimension 13) is a meaningful
security control in its own right. it reduces the number of distinct places
in the codebase where a raw SQL string is assembled by hand, which reduces
the surface area a security review has to cover for injection
vulnerabilities. This is a genuine, if secondary, benefit of the pattern
rather than its primary purpose, and it does not replace the use of
parameterized queries or an ORM's built-in escaping. it only reduces where
those protections need to be applied consistently.

A layered system's error-translation discipline (each layer catches errors
from the layer beneath it and re-raises a layer-appropriate error, per
dimension 7) is also a privacy control. it is the mechanism that prevents an
internal database error message, which can leak schema details, table names,
or even fragments of a query containing sensitive values, from reaching an
external actor through the presentation layer's error response. Where this
translation is skipped, as in the failure mode named in dimension 16 (raw
driver exceptions visible at the presentation layer), the system has an
information-disclosure vulnerability as a direct consequence of the layer
boundary being violated, not a separate, unrelated bug.

## Code examples

The three languages below were chosen because each shows a different degree
of compiler enforcement at the layer boundary. TypeScript enforces the
interface shape at compile time but erases it at runtime, Java enforces it at
both compile time and runtime through its nominal type system, and Python
enforces nothing, relying entirely on module structure and convention, which
makes the same three-layer shape visibly less protected. C#, Go, Kotlin, and
Rust were not used; C# would only restate the Java example under a different
syntax given the languages' similar interface systems, and a Go or Rust
version would look almost identical to a stripped-down Java version without
adding a new lesson about the pattern itself.

### TypeScript

```typescript
// domain.ts -- the domain layer defines the interface it needs.
interface OrderRepository {
  findById(id: string): Order | undefined;
  save(order: Order): void;
}

interface Order {
  id: string;
  totalCents: number;
  discountApplied: boolean;
}

class OrderDomainError extends Error {}

class OrderService {
  constructor(private readonly repository: OrderRepository) {}

  applyLoyaltyDiscount(orderId: string): Order {
    const order = this.repository.findById(orderId);
    if (order === undefined) {
      throw new OrderDomainError(`order ${orderId} not found`);
    }
    if (order.discountApplied) {
      throw new OrderDomainError(`order ${orderId} already discounted`);
    }
    const discounted: Order = {
      ...order,
      totalCents: Math.round(order.totalCents * 0.9),
      discountApplied: true,
    };
    this.repository.save(discounted);
    return discounted;
  }
}

// data-access.ts -- a concrete implementation, swappable without
// touching OrderService at all.
class InMemoryOrderRepository implements OrderRepository {
  private readonly rows = new Map<string, Order>();

  seed(order: Order): void {
    this.rows.set(order.id, order);
  }

  findById(id: string): Order | undefined {
    return this.rows.get(id);
  }

  save(order: Order): void {
    this.rows.set(order.id, order);
  }
}

// presentation.ts -- translates an external request shape into a
// domain call, and translates the domain result or error back out.
function handleApplyDiscountRequest(
  service: OrderService,
  requestOrderId: string
): { status: number; body: unknown } {
  try {
    const order = service.applyLoyaltyDiscount(requestOrderId);
    return { status: 200, body: order };
  } catch (err) {
    if (err instanceof OrderDomainError) {
      return { status: 409, body: { error: err.message } };
    }
    return { status: 500, body: { error: "internal error" } };
  }
}

// Wiring, at the composition root, is the only place that knows
// about both the interface and the concrete implementation.
const repository = new InMemoryOrderRepository();
repository.seed({ id: "ord-1", totalCents: 5000, discountApplied: false });
const service = new OrderService(repository);

console.log(handleApplyDiscountRequest(service, "ord-1"));
console.log(handleApplyDiscountRequest(service, "ord-1"));
console.log(handleApplyDiscountRequest(service, "missing"));
```

Compiled and run with `npx --yes tsc --strict --target es2020 --module
commonjs layered.ts && node layered.js`. output was three lines, a 200 with
the discounted order (4500 cents), a 409 for the already-discounted order,
and a 409 for the missing order. Compiled clean under `--strict`.

### Python

```python
"""Layered architecture, Python. No compiler enforces the interface,
so the boundary is a convention backed by an abstract base class."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Order:
    id: str
    total_cents: int
    discount_applied: bool


class OrderDomainError(Exception):
    pass


class OrderRepository(ABC):
    @abstractmethod
    def find_by_id(self, order_id: str) -> Order | None: ...

    @abstractmethod
    def save(self, order: Order) -> None: ...


class OrderService:
    """The domain layer. Depends only on the OrderRepository
    interface above, never on a concrete storage technology."""

    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def apply_loyalty_discount(self, order_id: str) -> Order:
        order = self._repository.find_by_id(order_id)
        if order is None:
            raise OrderDomainError(f"order {order_id} not found")
        if order.discount_applied:
            raise OrderDomainError(f"order {order_id} already discounted")
        discounted = replace(
            order,
            total_cents=round(order.total_cents * 0.9),
            discount_applied=True,
        )
        self._repository.save(discounted)
        return discounted


class InMemoryOrderRepository(OrderRepository):
    """The data access layer. Swappable behind the interface above."""

    def __init__(self) -> None:
        self._rows: dict[str, Order] = {}

    def seed(self, order: Order) -> None:
        self._rows[order.id] = order

    def find_by_id(self, order_id: str) -> Order | None:
        return self._rows.get(order_id)

    def save(self, order: Order) -> None:
        self._rows[order.id] = order


def handle_apply_discount_request(
    service: OrderService, request_order_id: str
) -> tuple[int, dict]:
    """The presentation layer. Translates external request shapes
    into a domain call and translates results or errors back out."""
    try:
        order = service.apply_loyalty_discount(request_order_id)
        return 200, {"id": order.id, "total_cents": order.total_cents}
    except OrderDomainError as exc:
        return 409, {"error": str(exc)}


if __name__ == "__main__":
    repository = InMemoryOrderRepository()
    repository.seed(Order(id="ord-1", total_cents=5000, discount_applied=False))
    service = OrderService(repository)

    print(handle_apply_discount_request(service, "ord-1"))
    print(handle_apply_discount_request(service, "ord-1"))
    print(handle_apply_discount_request(service, "missing"))
```

Run with `python3 layered.py`. Output matched the TypeScript example
exactly. Order ord-1 returned status 200 with total_cents 4500 on the first
call, then status 409 with "already discounted" on the second call, then
status 409 with "not found" for the missing order id.

### Java

```java
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

public final class Layered {

    // --- Domain layer -----------------------------------------------

    record Order(String id, int totalCents, boolean discountApplied) {
        Order withDiscount(int newTotal) {
            return new Order(id, newTotal, true);
        }
    }

    static final class OrderDomainError extends RuntimeException {
        OrderDomainError(String message) {
            super(message);
        }
    }

    interface OrderRepository {
        Optional<Order> findById(String id);
        void save(Order order);
    }

    static final class OrderService {
        private final OrderRepository repository;

        OrderService(OrderRepository repository) {
            this.repository = repository;
        }

        Order applyLoyaltyDiscount(String orderId) {
            Order order = repository.findById(orderId)
                .orElseThrow(() -> new OrderDomainError("order " + orderId + " not found"));
            if (order.discountApplied()) {
                throw new OrderDomainError("order " + orderId + " already discounted");
            }
            Order discounted = order.withDiscount(Math.round(order.totalCents() * 0.9f));
            repository.save(discounted);
            return discounted;
        }
    }

    // --- Data access layer -------------------------------------------

    static final class InMemoryOrderRepository implements OrderRepository {
        private final Map<String, Order> rows = new HashMap<>();

        void seed(Order order) {
            rows.put(order.id(), order);
        }

        public Optional<Order> findById(String id) {
            return Optional.ofNullable(rows.get(id));
        }

        public void save(Order order) {
            rows.put(order.id(), order);
        }
    }

    // --- Presentation layer -------------------------------------------

    record Response(int status, String body) {}

    static Response handleApplyDiscountRequest(OrderService service, String orderId) {
        try {
            Order order = service.applyLoyaltyDiscount(orderId);
            return new Response(200, "order=" + order.id() + " total=" + order.totalCents());
        } catch (OrderDomainError e) {
            return new Response(409, "error=" + e.getMessage());
        }
    }

    // --- Composition root -----------------------------------------------

    public static void main(String[] args) {
        InMemoryOrderRepository repository = new InMemoryOrderRepository();
        repository.seed(new Order("ord-1", 5000, false));
        OrderService service = new OrderService(repository);

        System.out.println(handleApplyDiscountRequest(service, "ord-1"));
        System.out.println(handleApplyDiscountRequest(service, "ord-1"));
        System.out.println(handleApplyDiscountRequest(service, "missing"));
    }
}
```

Compiled and run with `javac Layered.java && java Layered`. Output was
`Response[status=200, body=order=ord-1 total=4500]`, then
`Response[status=409, body=error=order ord-1 already discounted]`, then
`Response[status=409, body=error=order missing not found]`, matching both
prior examples exactly. All three examples were executed, not only compiled.
their outputs agree, which is the intended demonstration that the layer
boundary (an interface here, a duck-typed convention in Python) produces the
same observable behavior regardless of how strictly the host language
enforces it.

## 18. References

1. Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, Michael
   Stal, *Pattern-Oriented Software Architecture, Volume 1. A System of
   Patterns*, Wiley, August 1996, the Layers pattern, cited via
   [Wikipedia, "Multitier architecture,"](https://en.wikipedia.org/wiki/Multitier_architecture),
   verified 2026-08-02.
2. Martin Fowler, "PresentationDomainDataLayering," martinfowler.com,
   published 26 August 2015,
   [https://martinfowler.com/bliki/PresentationDomainDataLayering.html](https://martinfowler.com/bliki/PresentationDomainDataLayering.html),
   verified 2026-08-02.
3. Microsoft Learn, "Common web application architectures," .NET
   Architecture Guides (excerpted from *Architect Modern Web Applications
   with ASP.NET Core and Azure*), original content 12 December 2021, page
   last updated 8 July 2026,
   [https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures),
   verified 2026-08-02.
4. Wikipedia, "OSI model," section on layering discipline and history,
   [https://en.wikipedia.org/wiki/OSI_model](https://en.wikipedia.org/wiki/OSI_model),
   verified 2026-08-02. Cited only as an illustration of strict-layering
   discipline in a different domain, per the scope note in dimension 1.
5. Spring PetClinic sample application,
   `org.springframework.samples.petclinic.owner` package, showing the
   `OwnerController` / `OwnerRepository` split,
   [https://github.com/spring-projects/spring-petclinic/tree/main/src/main/java/org/springframework/samples/petclinic/owner](https://github.com/spring-projects/spring-petclinic/tree/main/src/main/java/org/springframework/samples/petclinic/owner),
   verified 2026-08-02.
6. eShopOnWeb reference application, demonstrating both the traditional
   N-Layer form and the inverted Clean Architecture form side by side,
   [https://github.com/dotnet-architecture/eShopOnWeb](https://github.com/dotnet-architecture/eShopOnWeb),
   linked from source 3, verified 2026-08-02.
