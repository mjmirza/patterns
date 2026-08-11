---
name: Layered Architecture
slug: layered-architecture
family: 11-domain-driven-design
category: Architectural
aliases: [N-tier Architecture, Multilayer Architecture, Tiered Architecture, Presentation-Domain-Data Layering]
first_described: "Buschmann, Meunier, Rohnert, Sommerlad, Stal 1996 (Pattern-Oriented Software Architecture, Volume 1)"
maturity: canonical
related: [application-service, domain-service, repository, anticorruption-layer, module, bounded-context]
incompatible_with: []
verified: 2026-08-02
---

# Layered Architecture

## 1. Name, aliases, and lineage

The canonical name is Layered Architecture, sometimes written as Layers. It is
catalogued as an architectural pattern in Frank Buschmann, Regine Meunier, Hans
Rohnert, Peter Sommerlad, and Michael Stal, *Pattern-Oriented Software
Architecture, Volume 1. A System of Patterns*, John Wiley and Sons, 1996,
chapter 2, the Layers pattern. That book states the pattern helps structure
applications that can be decomposed into groups of subtasks in which each
group of subtasks is at a particular level of abstraction, and formalises the
idea that had already been informal practice for a decade before the book
named it, going back to network protocol stacks such as OSI and TCP/IP and to
early operating system designs such as THE multiprogramming system.

Eric Evans gave the pattern its most cited domain-driven treatment in *Domain-
Driven Design. Tackling Complexity in the Heart of Software*, Addison-Wesley,
2003, chapter 4, "Isolating the Domain," where he names four layers, User
Interface, Application, Domain, and Infrastructure, and states the purpose
plainly. isolate the expression of the domain model, so that the model
carries its own logic uncontaminated by the concerns of displaying it,
storing it, or coordinating application tasks. Evans is explicit that what
makes the pattern useful in a DDD context is not the layering by itself,
which the older POSA and N-tier literature already had, but the specific
placement of a Domain layer that has no dependency on Infrastructure or User
Interface, so that model logic can be reasoned about and tested in
isolation.

Martin Fowler documents a closely related, narrower three-layer split under
the name Presentation Domain Data Layering, describing it as one of the most
common ways to modularize an information-rich program, separating a system
into presentation, or UI, domain logic, also called business logic, and data
access, with the stated benefit of allowing a reader to reduce the scope of
attention to one of the three topics at a time
(<https://martinfowler.com/bliki/PresentationDomainDataLayering.html>,
verified 2026-08-02). Fowler's article is explicit that this is a *logical*
separation of concerns, not a statement about physical deployment, and that
the layers frequently end up in different deployment tiers in practice
without that being required by the pattern itself.

**N-tier** is the deployment-oriented alias, used when the layers are also
physically separated onto different processes or machines. Microsoft's Azure
Architecture Center defines an N-tier architecture as one that divides an
application into logical layers and physical tiers, and is explicit that a
layer is a way to separate responsibilities and manage dependencies, while a
tier is a physical unit where code executes, and that you can host several
layers on the same tier
(<https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/n-tier>,
verified 2026-08-02). That same source distinguishes a closed layer
architecture, where a layer may call only the layer immediately below it,
from an open layer architecture, where a layer may call any layer beneath it,
and states that a closed architecture limits dependencies at the cost of
extra pass-through calls when a layer has nothing to add to a request.

Two further aliases are worth naming because they are used loosely and
sometimes wrongly as synonyms. **Multilayer Architecture** is a plain
restatement of Layered Architecture with no additional meaning. **Tiered
Architecture** is frequently used interchangeably with N-tier, and the
looseness of that usage is itself a documented source of confusion, which is
why the Azure Architecture Center source above goes out of its way to define
layer and tier as two different axes rather than one.

## 2. Problem and context

A system has several kinds of work happening inside it at once, work that
talks to a person through a screen or an API, work that decides what the
business rules say should happen, and work that reads and writes durable
state. Left unstructured, these three kinds of work end up interleaved in
the same functions. A controller method validates an HTTP body, computes a
discount, and issues a SQL update, all in twenty lines, because that was the
fastest way to make the feature work on the day it was written.

The problem this creates surfaces later, not immediately. A change to how
discounts are computed requires touching a file that also handles HTTP
parsing, so the change risks breaking request handling by accident. A change
to the database schema requires touching the same file that computes
discounts, so a schema migration and a business rule change compete for the
same diff and the same reviewer's attention. Writing a test for the discount
rule requires standing up an HTTP server and a real database, because the
rule cannot be reached any other way, so the test suite is slow and the
rule's behaviour under edge cases is under-tested because writing a new test
case costs minutes rather than seconds.

Layered Architecture responds by drawing a small number of horizontal
divisions through the codebase, each one owning one kind of concern, each one
depending only on the layer or layers immediately below it, and by making
that dependency direction the one architectural rule that every other design
decision in the system must respect. In a DDD-flavoured application the
concrete question the pattern answers is where the code lives that enforces
"an order cannot ship before payment clears," and the answer must be a
single place that a HTTP framework upgrade, a database vendor swap, or a
new client, mobile app, batch job, or another service, cannot force to
change.

The context in which the pattern earns its keep has a recognisable shape.
There is a genuine, non-trivial domain, meaning rules that are not simply
create, read, update, delete against a table. There is more than one way the
domain is invoked, a web UI today, an API tomorrow, a scheduled job next
quarter. And the team is large enough, or the codebase long-lived enough,
that consistent placement of code matters more than the marginal
indirection cost of an extra function call between layers.

## 3. Forces

- **Coupling.** Favoured, and this is the entire point of the pattern. Each
  layer depends only downward, so the domain layer can be changed, tested,
  and reasoned about without pulling in a web framework or a database
  driver. Evans's argument in *Domain-Driven Design*, chapter 4, is
  specifically that decoupling the domain from infrastructure and
  presentation is what allows the domain model to remain expressive rather
  than accreting persistence and display concerns.
- **Cognitive load, locally.** Favoured. A developer working on presentation
  code does not need to hold the persistence mapping in their head, and a
  developer working on the domain does not need to know which web framework
  renders it. Fowler's article states this directly, describing the benefit
  as letting a reader think about one of the three topics relatively
  independently.
- **Cognitive load, globally.** Sacrificed in one specific way. A new
  contributor must learn the layering convention itself before any single
  layer's code is legible in context, and a change that is conceptually one
  idea, for example adding a new field to an order, now touches four files
  across four layers instead of one.
- **Latency and throughput.** Mildly sacrificed when layers are also
  physically separated tiers. The Azure Architecture Center source states
  plainly that physical separation of tiers improves scalability and
  resiliency but adds latency from the extra network communication, and
  that a strict tier-to-tier communication model, where a request must pass
  through every intervening tier, has greater latency and overhead than a
  relaxed model that allows tiers to be skipped, at the cost of more
  coupling in the relaxed model. When layers stay in a single process, this
  force is closer to neutral, paid only in extra function calls and object
  allocation for data-transfer objects crossing layer boundaries.
- **Testability.** Strongly favoured. The domain layer, isolated from
  infrastructure, is unit-testable without a running database or web
  server, which is one of the most frequently cited practical benefits in
  DDD literature and is the reason the pattern recurs across almost every
  book on maintainable enterprise software design.
- **Consistency of placement.** Favoured. Once the convention is
  established and enforced, a reader can predict where a given kind of code
  lives without having to search for it, which becomes valuable exactly in
  proportion to codebase size and team size.
- **Cost of cross-cutting change.** Sacrificed. A field that must appear in
  the UI, the domain model, and the persisted record requires an edit in
  each layer's representation of that field, and keeping those
  representations synchronised by hand is a maintenance tax that grows with
  the number of fields and the number of layers.
- **Operability.** Neutral to mildly favoured. Clear layer boundaries make
  it straightforward to instrument each layer separately, for example
  measuring database layer latency independently of application layer
  latency, which is difficult when the concerns are interleaved.

A layering that gave up nothing would not be a design decision, it would be
a tautology. The price paid here is indirection, some duplication of shape
across layer boundaries, and a learning curve for the convention itself.

## 4. Applicability and non-applicability

Reach for Layered Architecture when the following hold.

- The application has domain logic worth protecting, meaning business rules
  that are more than validation of individual fields, rules that combine
  several pieces of state and decide an outcome.
- More than one delivery mechanism exists or is plausible within the
  system's lifetime, a web UI and an API, a UI and a batch importer, a
  synchronous API and an asynchronous event consumer, all needing to invoke
  the same business rules without duplicating them.
- The persistence technology is expected to change, or the team wants the
  option to change it, over the application's lifetime, whether that
  is a database vendor swap, a move from a relational store to a document
  store, or the introduction of caching in front of a slow store.
- The team is large enough, or the codebase long-lived enough, that a
  predictable place for each kind of code reduces onboarding time and
  review friction more than the added indirection costs.
- The system needs independent testability of business rules without
  standing up infrastructure, because the test suite's speed and coverage
  depend on being able to exercise the domain layer alone.

Do NOT reach for Layered Architecture, or reach for a much thinner version of
it, in the following situations.

- A small script, a one-off data migration, or a prototype whose expected
  lifetime is measured in days. The ceremony of separate layers costs more
  than any benefit it returns before the code is thrown away.
- A pure CRUD application with no business rules beyond field validation and
  referential integrity, where the domain layer would contain nothing but
  pass-through calls to the data layer. The Azure Architecture Center source
  names this directly as a documented challenge of N-tier systems, stating
  that a middle tier might only perform basic create, read, update, delete
  operations, which adds latency and complexity without delivering
  meaningful value.
- A system whose primary complexity is in data flow and transformation
  topology rather than business rule complexity, where a pipeline or
  event-streaming style of architecture fits the actual shape of the problem
  better than a request-response layered stack.
- A system that genuinely needs independent scaling, independent
  deployment, and independent technology choice per capability, where
  Layered Architecture's single-deployable, shared-database default shape
  works against the goal and a services-oriented or microservices style,
  itself often internally layered per service, is the better fit at the
  system level.
- A team of one or two people building something whose main risk is not
  getting the idea shipped fast enough to learn whether it is wanted at
  all, where a lighter, more tangled first version, later refactored once
  the domain rules stabilise, is a legitimate and common choice, not a
  mistake to eliminate on day one.
- A domain layer that would end up depending on a single Infrastructure
  detail so completely, for example an in-memory graph traversal algorithm
  operating over structures the database driver itself hands back, that
  the isolation the pattern promises cannot honestly be delivered, and the
  layering becomes a paper boundary that a change on either side breaks
  anyway.

## 5. Structure

The canonical four-layer DDD arrangement, following Evans, chapter 4, names
the layers and their responsibilities as follows.

- **Presentation, also called User Interface.** Responsible for showing
  information to the user and interpreting the user's commands. Includes
  both a human-facing UI and, in modern systems, an API surface that another
  program calls on the user's behalf. Depends on the Application layer, and
  must not contain business rules.
- **Application.** Thin. Coordinates the work the system is asked to do,
  delegates to the Domain layer for anything resembling a decision, and
  does not itself hold business logic. Evans describes this layer's tasks as
  meaningful to the business, or at least necessary for interaction with
  the application layers of other systems, but not carrying business rules
  or knowledge, only coordinating tasks and delegating work to
  collaborations of domain objects. Owns transaction boundaries and
  application-level concerns such as authorization checks that are about
  the use case rather than the domain model itself.
- **Domain, also called Model.** Represents concepts of the business, the
  situation of the business, and business rules. State that reflects the
  business situation is controlled and used here, even though the
  technical detail of storing it is delegated to the Infrastructure layer.
  This layer is the heart of business software, in Evans's own words, and
  it depends on nothing above or below it, only, at most, on shared
  low-level utilities.
- **Infrastructure.** Provides generic technical capabilities that support
  the higher layers, message sending, persisting objects for the Domain
  layer, drawing widgets for the User Interface layer, and so on. This
  layer may also support a pattern of collaboration between the
  Application and Domain layers, for example through Repository
  implementations.

Participants inside a fully-layered request path, using naming common across
Evans, Vaughn Vernon's *Implementing Domain-Driven Design*, Addison-Wesley,
2013, chapter 4, and mainstream framework convention.

- **Controller, or Presenter, or API endpoint.** Presentation-layer
  participant. Receives an inbound request, translates it into a call
  against an Application Service, and translates the result back into a
  view or an HTTP response. Owns no business rules.
- **Application Service.** Application-layer participant. Coordinates one
  use case, loads the necessary aggregates through Repositories, invokes
  Domain layer behaviour, manages the transaction, and returns a result or
  a Data Transfer Object. See the `application-service` entry in this
  catalogue for its own full treatment.
- **Aggregate, Entity, Value Object, Domain Service.** Domain-layer
  participants. Carry the actual business rules. An Aggregate enforces its
  own invariants and is the unit that a Repository loads and saves whole.
  See the `entity`, `value-object`, `aggregate-root`, and `domain-service`
  entries.
- **Repository interface.** Declared in the Domain layer, so that Domain
  code can ask for and persist Aggregates using domain language, without
  the Domain layer depending on a concrete database technology. See the
  `repository` entry.
- **Repository implementation, Data Mapper, DAO, ORM configuration.**
  Infrastructure-layer participant. Implements the Repository interface
  against a concrete store, and is the only place in the system that knows
  the physical schema, the SQL dialect, or the document store's query
  language.
- **Gateway, or Anticorruption Layer, to external systems.**
  Infrastructure-layer participant when the external system is a plain
  data source, Domain-layer-adjacent when translation logic protects the
  Domain model from a foreign model's concepts. See the
  `anticorruption-layer` entry.

## 6. ASCII structure diagram

```
+-----------------------------------------------------------+
|                    Presentation Layer                     |
|   Controllers, API endpoints, view templates, CLI parsers |
+---------------------------|--------------------------------+
                            | calls
                            v
+-----------------------------------------------------------+
|                     Application Layer                     |
|   Application Services, use-case coordination,            |
|   transaction boundaries, DTO assembly                    |
+---------------------------|--------------------------------+
                            | calls
                            v
+-----------------------------------------------------------+
|                       Domain Layer                        |
|   Aggregates, Entities, Value Objects, Domain Services,    |
|   Repository interfaces (declared here, not implemented)   |
+---------------------------|--------------------------------+
                            | is implemented by, at runtime,
                            | dependency-inverted
                            v
+-----------------------------------------------------------+
|                   Infrastructure Layer                    |
|   Repository implementations, ORM, message bus adapters,   |
|   external gateways, file system, email, third-party APIs  |
+-----------------------------------------------------------+

Compile-time dependency direction. Presentation -> Application -> Domain
Runtime call into Infrastructure happens ONLY through an interface that
the Domain layer owns. Infrastructure depends on Domain, never the reverse.
This inversion is what keeps the arrow of compile-time dependency pointing
the same direction as the arrow of business importance.
```

## 7. Dynamics

A single "place an order" request, traced through all four layers, in a
closed-layer arrangement where each layer calls only the layer immediately
below it.

```
Client            Presentation      Application       Domain            Infrastructure
  |                    |                 |               |                    |
  | POST /orders       |                 |               |                    |
  |------------------->|                 |               |                    |
  |                    | parse + map to  |               |                    |
  |                    | PlaceOrderCmd   |               |                    |
  |                    |---------------->|               |                    |
  |                    |                 | begin tx      |                    |
  |                    |                 |-------------------------------->   |
  |                    |                 | load Customer, Inventory          |
  |                    |                 | via Repository interface          |
  |                    |                 |------------------------------->   |
  |                    |                 |               |   SELECT ...       |
  |                    |                 |               |<-------------------|
  |                    |                 | Customer, Inventory objects       |
  |                    |                 |<-------------------------------   |
  |                    |                 | order.place(items, customer)      |
  |                    |                 |-------------->|                    |
  |                    |                 |               | check credit limit |
  |                    |                 |               | check stock        |
  |                    |                 |               | raise OrderPlaced  |
  |                    |                 |               | domain event       |
  |                    |                 | Order (new)   |                    |
  |                    |                 |<--------------|                    |
  |                    |                 | save Order via Repository          |
  |                    |                 |------------------------------->    |
  |                    |                 |               |   INSERT ...       |
  |                    |                 |               |<-------------------|
  |                    |                 | commit tx     |                    |
  |                    |                 |-------------------------------->   |
  |                    | OrderDTO        |               |                    |
  |                    |<----------------|               |                    |
  | 201 Created + JSON |                 |               |                    |
  |<-------------------|                 |               |                    |
```

The Domain layer never sees the HTTP request shape, and the Presentation
layer never sees a SQL statement. The Application Service is the only
participant that knows both "this came from an HTTP POST" indirectly, via
the command object it was handed, and "this needs a transaction and two
repository calls."

## 8. Implementation variants

- **Closed layers, strict.** Every call passes through the layer
  immediately below, no skipping. The Azure Architecture Center source
  describes this as the strict tier communication model, with greater
  latency and overhead than the alternative, and, at the layer level rather
  than the physical tier level, this is the variant most textbook DDD
  diagrams show. It gives the greatest ability to swap out any single
  layer's implementation without ripple effects.
- **Open layers, relaxed.** A layer may call any layer beneath it, not
  only the one immediately below. A Presentation layer might read directly
  from a query-optimised read model in Infrastructure for a display-only
  screen, bypassing the Application and Domain layers entirely, because
  that screen has no business rule to enforce, only data to show. This is
  the shape behind CQRS-flavoured systems that keep a rich, layered write
  side and a thin, open, read-optimised query side. Reduces pass-through
  boilerplate at the cost of more numerous, less uniform dependency paths.
- **Physically separated N-tier.** Each layer, or a group of layers, runs
  in its own process or on its own machine, communicating over the network,
  typically HTTP or a message queue. This variant is common when migrating
  an on-premises multi-tier application into a cloud environment with
  minimal rearchitecting, which the Azure Architecture Center source names
  explicitly as one of the primary scenarios for choosing N-tier on Azure.
- **Single-process, in-memory layering.** All layers run in one process,
  and the "call" between layers is a plain function or method call, not a
  network hop. This is the common shape for a modular monolith and is the
  variant Fowler's Presentation Domain Data Layering article is describing,
  where the separation is entirely logical.
- **Hexagonal or Ports and Adapters framing of the same idea.** Alistair
  Cockburn's Hexagonal Architecture, and the closely related Onion
  Architecture from Jeffrey Palermo, restate the Domain-at-the-centre idea
  from a different geometric metaphor, concentric rings instead of
  horizontal bands, with the same dependency-inversion rule, outer rings
  depend on inner rings, never the reverse. The practical effect on where
  code lives is close to identical to a well-drawn four-layer DDD stack.
  The difference is largely how the boundary is drawn and named, plus a
  sharper insistence, in the hexagonal framing, that the Domain layer
  defines "ports" that any number of interchangeable "adapters" can satisfy,
  which maps directly onto the Repository-interface-in-Domain,
  Repository-implementation-in-Infrastructure split described in dimension
  5 above.
- **Vertical slice, feature-folder organisation with a horizontal layering
  discipline preserved inside each slice.** Instead of one Presentation
  folder holding every controller and one Domain folder holding every
  entity, code is grouped by feature, and within each feature folder the
  same Presentation, Application, Domain, Infrastructure split is
  preserved. This variant trades the ease of seeing "everything the
  Domain layer contains" at a glance for the ease of seeing "everything
  the Orders feature touches" at a glance, and is increasingly common in
  large single-repository systems where cross-feature navigation happens
  more often than cross-layer navigation.

## 9. Known production uses

- **Java EE and Jakarta EE reference architecture.** The Jakarta EE
  platform's own architectural guidance groups application code into a
  web tier, an EJB or business tier, and an Enterprise Information System
  tier for persistence and external systems, a structure documented across
  the Jakarta EE tutorial's architecture overview and inherited from the
  earlier J2EE Blueprints, and it is the layering that the vast majority of
  Spring-based enterprise Java applications also follow in practice, with a
  `@Controller` / `@Service` / `@Repository` split that is a near-literal
  restatement of Presentation, Application-plus-Domain, and Infrastructure.
- **ASP.NET Core and the .NET reference architectures published by
  Microsoft.** The Azure Architecture Center's own N-tier style guide,
  cited in dimension 1 above, is itself the documentation of a pattern
  Microsoft ships as a first-class supported architecture style for Azure
  workloads, with named reference implementations for VM-hosted and
  managed-service-hosted variants
  (<https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/n-tier>,
  verified 2026-08-02).
- **The OSI and TCP/IP networking stacks.** Cited by Buschmann et al. in the
  original POSA description of the Layers pattern as one of the two
  motivating real-world examples, alongside operating system kernels, and
  remaining, decades later, the most widely deployed instance of strict
  closed-layer architecture in computing, where the Transport layer never
  calls directly into the Application layer above it or the Physical layer
  two levels below without passing through the intervening layer.
- **Domain-Driven Design reference implementations distributed with the
  DDD community's own tooling.** Vaughn Vernon's companion code for
  *Implementing Domain-Driven Design*, and the widely referenced
  "IDDD Samples" repository that accompanies it, structure each bounded
  context's code into the same Presentation, Application, Domain,
  Infrastructure split described in dimension 5, and that repository is
  itself cited by name as a canonical worked example throughout later DDD
  community material, including conference talks and follow-on books that
  build on Vernon's structure.

## 10. Consequences

Positive.

- The Domain layer becomes independently testable, and Evans's central
  argument in *Domain-Driven Design*, chapter 4, is that this isolation is
  precisely what allows a rich, expressive domain model to survive contact
  with a real system's infrastructure concerns instead of decaying into an
  anaemic set of data holders wrapped around SQL calls.
- Persistence technology becomes swappable behind the Repository interface
  boundary without touching Domain or Application code, which matters
  concretely when a team migrates from one database engine to another, or
  introduces a cache in front of a slow store.
- New delivery mechanisms, a second API version, a batch job, an event
  consumer, can reuse the same Application and Domain layers without
  duplicating business rules, because those layers were never written to
  assume a particular caller.
- Code review and onboarding benefit from predictable placement. A reviewer
  looking at a pull request that only touches the Infrastructure layer
  knows immediately that business rules are not in scope for that review.
- Instrumentation and monitoring can be layer-scoped, timing database
  layer calls separately from application layer coordination time, which
  is difficult to do cleanly when the concerns are interleaved in one
  function.

Negative.

- Indirection cost. A trivial change, adding a field, threading a new
  parameter through a use case, touches every layer it passes through, and
  the amount of boilerplate this generates is a commonly cited complaint
  against the pattern, especially in systems whose domain logic turns out
  to be genuinely thin.
- The "middle tier does nothing but CRUD" failure mode, named directly by
  the Azure Architecture Center source, where an Application layer or a
  Domain layer ends up as a pass-through that adds latency and review
  overhead without adding any actual decision-making, because the
  underlying problem never had enough business logic to justify the split.
- A closed-layer discipline, strictly enforced, can force pass-through
  calls that exist purely to satisfy the layering rule rather than to do
  useful work, and Buschmann et al.'s original POSA treatment of Layers
  names this tension explicitly as a trade-off of the pattern rather than
  a defect in any one implementation of it.
- Physical tier separation, the N-tier variant, adds real network latency
  and a new class of partial-failure modes, timeouts, retries, and network
  partitions between tiers, that a single-process layered system does not
  have to contend with, and the Azure Architecture Center source lists
  this cost directly.
- The convention itself must be actively maintained. Nothing in a
  dynamically typed language, and not much in a statically typed one
  without additional tooling, stops a developer from reaching straight
  from a Presentation-layer controller into an Infrastructure-layer
  database client, and once that shortcut exists once, it tends to recur,
  eroding the boundary the pattern exists to draw.

## 11. Failure modes and misuse

- **Symptom.** The Application layer contains `if` statements branching on
  business state, discount tiers, credit checks, shipping eligibility, and
  the Domain layer contains almost nothing besides plain data classes.
  **Cause.** The team wrote the layering shape without internalising Evans's
  actual point, that the Application layer coordinates and the Domain layer
  decides, so business rules leaked upward into the layer that was supposed
  to be thin. **Fix.** Move each conditional that expresses a business rule,
  not a use-case-sequencing decision, down into the Domain layer, onto the
  Aggregate or Domain Service whose state the rule actually depends on, and
  leave the Application layer holding only orchestration, transaction
  boundaries, and calls out to the Domain and Infrastructure layers.
- **Symptom.** Domain-layer classes import an ORM's base class, or carry
  annotations that reference a specific database's column types, and
  changing database vendor requires editing Domain-layer files.
  **Cause.** The Repository pattern was only half applied, the interface
  exists, but the Domain-layer Entity or Aggregate was allowed to also
  serve as the ORM's mapped class, collapsing the Domain representation and
  the persistence representation into one type. **Fix.** Separate the
  persisted record shape from the Domain object shape, and have the
  Infrastructure-layer Repository implementation do the mapping between
  them, even when the two shapes are, for now, identical field for field,
  because the point is the seam, not the current divergence.
- **Symptom.** A single feature change touches five files across four
  layers for what the product description called "one small tweak," and the
  team starts treating layering as a productivity tax to be minimised or
  routed around. **Cause.** The domain, on inspection, never had enough real
  business logic to justify the split, and the layering was applied by
  default rather than by need, see dimension 4's non-applicability list.
  **Fix.** Either collapse layers that are pure pass-through, merging
  Application and Domain when the Application layer's coordination work is
  trivial, or accept the cost as the price of keeping optionality, adding
  new delivery mechanisms and swapping infrastructure later, and make that
  trade-off explicit to the team rather than silent.
- **Symptom.** A UI screen that only ever needs to display a denormalised
  read model takes several hundred milliseconds because it routes through
  Application-layer orchestration and Domain-layer Aggregate reconstruction
  to answer what is fundamentally a query. **Cause.** A closed-layer
  discipline was applied uniformly to both commands, which need the
  Domain layer's rule enforcement, and queries, which do not.
  **Fix.** Adopt an open-layer or CQRS-flavoured read path for
  display-only queries, letting the Presentation layer read directly from
  an Infrastructure-layer read model or projection, while keeping the
  closed, Domain-enforced path for anything that changes state, as
  discussed in dimension 8's open-layers variant.
- **Symptom.** Two teams working on the same layered monolith regularly
  produce merge conflicts and cross-team review dependencies on the same
  files inside the Domain layer, even though their features are otherwise
  unrelated. **Cause.** The system was layered horizontally at the whole-
  application scale, so every feature's Domain code lives in one shared
  folder, and feature boundaries do not align with layer boundaries.
  **Fix.** Move to the vertical-slice variant from dimension 8, preserving
  the same horizontal layering discipline within each feature folder while
  giving each feature, and each team, its own namespace to work in without
  touching unrelated code, or, if the coupling is deep enough, treat it as
  a signal that the bounded context itself is drawn too widely, see
  `bounded-context`.

## 12. Trade-off matrix

Compared against three named architectural alternatives that address the
same underlying problem, separating concerns in a non-trivial application,
from a different angle.

| Force | Layered Architecture (closed, DDD-flavoured) | Hexagonal / Ports and Adapters | Microservices | Big Ball of Mud |
|---|---|---|---|---|
| Domain isolation from infrastructure | Strong, by explicit layer rule | Strong, by explicit port and adapter rule, arguably stricter about symmetry between inbound and outbound boundaries | Strong at the service boundary, but each service internally may or may not be layered | None, by definition, see `big-ball-of-mud` |
| Independent testability of business rules | High, Domain layer unit-testable without infrastructure | High, same underlying property, framed as testing against ports with fake adapters | High within a service, but cross-service behaviour needs integration or contract tests | Very low, business rules entangled with I/O throughout |
| Cost of adding a new delivery mechanism | Low, reuse existing Application and Domain layers | Low, add a new inbound adapter against the same ports | Requires either a new service or a new endpoint in an existing one, plus its own operational surface | High, delivery mechanism and business logic are the same code |
| Independent deployability of parts of the system | None, one deployable, unless combined with a services split | None, same limitation, hexagonal architecture governs a single component's internal structure | High, this is the primary benefit microservices offer over layering alone | None, and often worse, since even internal seams do not exist |
| Latency overhead | Low in-process, moderate to high if tiers are physically separated | Low, same as layered when kept in-process | Higher, network calls between services replace what would be in-process calls in a layered monolith | Lowest, direct calls, but at the cost of every other force |
| Cognitive load to navigate | Moderate, predictable but requires learning the convention | Moderate, similar, plus the port and adapter vocabulary itself | Higher at the system level, lower per service, since each service is smaller | Lowest to start, highest over time as the system grows |
| Operational complexity | Low to moderate, one deployable to operate, or a handful of tiers | Low to moderate, same as layered | High, service discovery, distributed tracing, network reliability, independent versioning | Low nominally, but incidents are hard to diagnose because causes are not localised |
| Fit for a small or short-lived system | Poor, ceremony outweighs benefit, see dimension 4 | Poor, same reason | Very poor, operational overhead alone rules it out | Arguably the honest default for a genuinely disposable prototype |

## 13. Related and incompatible patterns

- **Application Service.** The Application layer's primary participant.
  See `application-service` for the full treatment of what belongs here
  versus what belongs one layer down.
- **Domain Service, Entity, Value Object, Aggregate Root.** The Domain
  layer's participants. Layered Architecture is the container. These
  patterns are what actually lives inside the Domain layer's box. See
  `domain-service`, `entity`, `value-object`, and `aggregate-root`.
- **Repository.** The pattern that makes the Domain-to-Infrastructure
  boundary concrete, an interface owned by the Domain layer and
  implemented by the Infrastructure layer. Composes directly with Layered
  Architecture and is close to meaningless without a layering discipline
  to sit inside. See `repository`.
- **Anticorruption Layer.** Composes at the Infrastructure boundary when
  the "outside" being integrated with is another bounded context or an
  external system with its own, foreign model. Where a Repository
  translates between the Domain layer and a technology, an
  Anticorruption Layer translates between the Domain layer and a
  different domain model. See `anticorruption-layer`.
- **Module.** Layered Architecture describes a horizontal decomposition.
  Module, in the DDD sense, describes a complementary vertical or
  topical grouping inside a layer, or across layers in the vertical-slice
  variant from dimension 8. See `module`.
- **Bounded Context.** Layered Architecture is typically applied within
  one Bounded Context. A system with several Bounded Contexts commonly
  has several independently layered stacks, one per context, rather than
  one shared set of layers spanning all of them, because sharing a Domain
  layer across contexts is close to a definition of not actually having
  separate contexts. See `bounded-context`.
- **Hexagonal Architecture, Onion Architecture, Clean Architecture.**
  Closely related restatements of the same dependency-inversion idea using
  concentric rings instead of horizontal bands, discussed as an
  implementation variant in dimension 8 rather than as a separate entry in
  this family, since the practical placement of code is close to
  identical.
- **CQRS, Command Query Responsibility Segregation.** Frequently combined
  with an open-layers variant of Layered Architecture, keeping a fully
  layered, Domain-enforced write path while allowing the read path to
  bypass layers for performance, as discussed in dimensions 8 and 11.
- **Incompatible with, in the strict sense.** Nothing in this pattern
  family is structurally incompatible with Layered Architecture, since it
  operates at a different axis, horizontal separation of concerns, from
  patterns describing how a single layer's internal objects collaborate.
  The closest thing to a genuine incompatibility is architectural rather
  than a named pattern conflict. a system committed to a shared-nothing,
  independently-deployed microservices style at the whole-system level
  will still, almost always, apply Layered Architecture inside each
  individual service, so the two are complementary at different scopes
  rather than competing at the same scope.

## 14. Refactoring path in and out

Introducing Layered Architecture into code that does not have it, in a
codebase where a Presentation-layer file currently talks straight to a
database.

1. Identify the business rules hiding inside the existing controller or
   handler function, the parts that decide something, as distinct from
   the parts that parse input or issue a query. This is the same
   recognition step Martin Fowler describes generally for extracting
   behaviour, and it is the hardest step, because the rule is often not
   written as an obvious `if` statement but is implicit in the sequence of
   database calls.
2. Extract the identified rules into a new Domain-layer type, an Entity,
   Value Object, or Aggregate, following the guidance in the `entity` and
   `value-object` entries, and give that type a test suite that exercises
   the rule directly, without a database or HTTP layer in the loop. This
   step alone, done even without the remaining steps, already delivers
   most of the testability benefit named in dimension 10.
3. Introduce a Repository interface, owned by the new Domain layer, whose
   method signatures speak in Domain terms, `findOrdersForCustomer`, not
   `SELECT * FROM orders WHERE customer_id = ?`. Implement it, for now,
   with the exact SQL the original code already had, moved verbatim into
   an Infrastructure-layer class.
4. Introduce a thin Application layer, an Application Service per use
   case, that loads what the Domain layer needs through the new
   Repository, calls the Domain-layer behaviour extracted in step 2, and
   persists the result. Leave the original controller in place for now,
   but have it call the new Application Service instead of the database
   directly.
5. Repeat steps 1 through 4 use case by use case. Do not attempt a
   big-bang rewrite of the whole system into layers at once. The pattern's
   value is realised incrementally, one isolated, tested Domain concept at
   a time, and a partially layered system with the highest-value rules
   already isolated is strictly better than an unfinished rewrite that
   never ships.

Removing Layered Architecture, when the domain has turned out to be thin
enough that the layering cost, named in dimensions 4, 10, and 11, exceeds
its benefit.

1. Confirm, honestly, that the Domain layer's classes contain little beyond
   getters, setters, and pass-through validation, and that the Application
   layer's methods are one-line delegations to a Repository with no
   additional coordination. If either layer still carries real behaviour,
   this is a warning sign to stop, not a reason to proceed.
2. Collapse the Application and Domain layers into one, keeping whichever
   layer's naming convention the team prefers, and keep the Repository
   interface boundary if persistence technology genuinely might still
   change, since that boundary alone is cheap to retain and expensive to
   reintroduce later.
3. If the Presentation layer's needs are now purely read-oriented for the
   collapsed area, consider whether the remaining structure is closer to a
   simple Transaction Script per use case than to any layered pattern at
   all, and name that honestly in the codebase rather than leaving a
   layered-looking folder structure around code that no longer behaves
   like layers.

## 15. Testing and verification

Layered Architecture's central testing benefit is that the Domain layer
becomes reachable without infrastructure, which changes what is easy and
what becomes comparatively harder.

Easier because of the pattern.

- Unit tests against Domain-layer Entities, Value Objects, and Domain
  Services run in-process, with no database, no HTTP server, and no
  network, so a large domain rule test suite can run in a few seconds
  rather than minutes, which in turn makes test-driven development on
  business rules practical.
- Application Service tests can substitute a fake or in-memory
  implementation of the Repository interface, testing the coordination
  logic, transaction sequencing, and error handling, without touching a
  real database, because the Repository is an interface the Domain layer
  owns and the Application layer depends on the interface, not the
  concrete implementation.
- Contract tests against the Repository interface itself, run once against
  the real Infrastructure-layer implementation and once against any fake
  used elsewhere, catch drift between the fake's behaviour and the real
  implementation's behaviour, which is the specific risk that fakes
  introduce.

Harder or newly necessary because of the pattern.

- End-to-end tests that exercise Presentation through Infrastructure become
  more valuable, not less, because the layering hides genuine wiring
  mistakes, an Application Service that never actually gets called by the
  Presentation layer, a Repository implementation that is registered for
  the wrong interface, until an end-to-end test exercises the whole path.
- Mapping code, translating between the Domain-layer Entity shape and the
  persisted record shape, and between the Domain-layer result and the
  Presentation-layer response shape, is new code that did not exist in an
  unlayered version, and it needs its own tests, since a subtle field
  mapping error is otherwise invisible to both the Domain-layer unit tests
  and a naive end-to-end happy-path test.
- Over-mocking the Repository interface in Application layer tests can
  produce tests that pass while the real Repository implementation is
  broken, a documented risk with any interface-substitution testing
  strategy, and the discipline that avoids it is keeping at least one
  suite of tests that exercises the real Infrastructure-layer
  implementation against a real, even if disposable, database.

## 16. Observability signals

This dimension is largely engineering judgement, drawn from operating
layered systems in production rather than from a single citable source.

A healthy layered system, observed through instrumentation, shows a clean
separation in where time is spent. Presentation-layer time is spent mostly
on serialization and network I/O to the client. Application-layer time is
spent mostly on the sum of its Domain and Infrastructure calls, with little
overhead of its own. Domain-layer time is spent mostly on CPU-bound rule
evaluation with near-zero I/O wait. Infrastructure-layer time is spent
mostly on external I/O, database round trips, message broker
acknowledgements, third-party API latency.

Signals worth logging or tracing per layer.

- A trace span per layer boundary crossing, so that a slow request can be
  attributed to a specific layer rather than only to the request as a
  whole, which is the direct observability payoff of having clean
  boundaries to instrument in the first place.
- Repository call counts per Application Service invocation, since a
  steadily rising count over time, for a use case whose business logic has
  not changed, is a reliable early signal of an accidental N+1 query
  pattern creeping into the Infrastructure-layer implementation.
- Domain-layer exception rates, specifically counted separately from
  Infrastructure-layer exceptions such as connection timeouts, because a
  rising rate of Domain-layer business-rule rejections, an order rejected
  for insufficient credit, for example, is a product or data-quality signal,
  while a rising rate of Infrastructure-layer exceptions is an
  operational-reliability signal, and conflating the two in one error
  counter hides which team should respond.
- Time spent in mapping code between layers, which is normally negligible
  but, when it is not, indicates either an unusually large payload or a
  mapping implementation that has grown accidentally expensive, both of
  which are worth a dashboard line of their own precisely because mapping
  code is otherwise easy to overlook when reasoning about performance.

A failing instance typically shows either an Application layer whose
self-time, time not spent waiting on Domain or Infrastructure calls, has
grown large, which is the trace-level signature of business logic having
leaked upward out of the Domain layer as described in dimension 11's first
failure mode, or a Presentation layer whose latency tracks Infrastructure
layer latency almost one-to-one, which is the signature of an open-layers
shortcut having been taken informally, without the team having decided to
adopt the open-layers variant on purpose.

## 17. Security and privacy implications

This dimension is largely analytical judgement about where the pattern
opens or closes attack surface, rather than a set of independently sourced
claims.

Layered Architecture closes off one specific, common attack surface by
construction, when the discipline is actually maintained. Because the
Presentation layer cannot reach the Infrastructure layer directly, a
vulnerability in request parsing, an injection attempt embedded in a form
field, cannot reach a raw SQL statement unless it first passes through the
Application and Domain layers, both of which are natural, and expected,
places to apply input validation and business-rule-driven authorization
checks before anything touches persistence. This is not a guarantee, an
Application layer that blindly forwards untrusted input to a Repository
call with string-built SQL is still vulnerable, but the layering creates an
obvious, single place to audit for that class of bug, rather than
requiring an audit of every Presentation-layer handler individually.

The pattern also creates a natural place to apply authorization
consistently. An authorization check placed in the Application layer, at
the entry to each use case, is harder to bypass accidentally than one
scattered across individual Presentation-layer routes, because every route
into a given use case necessarily passes through the same Application
Service.

The pattern introduces its own, specific risk when the layering is
violated informally rather than by deliberate, documented decision, as
described in dimension 11. A Presentation-layer shortcut that reaches into
Infrastructure directly, taken once under deadline pressure, bypasses
whatever authorization or validation logic the team assumed every request
passed through at the Application layer, and because the bypass is
informal, it is unlikely to be caught by a review checklist that assumes
the layering is intact.

Data privacy has one specific implication worth naming. Data Transfer
Objects crossing from Infrastructure up through Domain and Application to
Presentation are a natural place for over-fetching to occur, an
Infrastructure-layer query that returns every column of a customer record,
including fields with no business need to reach the Presentation layer,
because it was the query already on hand. Deliberately shaping the DTO at
each layer boundary, rather than passing the same wide object straight
through, is the practical mitigation, and it is a mitigation the pattern
makes easy to apply, precisely because each layer boundary is already a
natural place to transform the shape of the data crossing it.

## Code examples

Three languages, all showing the identical use case, a place order
operation, split across the four layers so the boundaries are visible in
real code rather than only in prose. TypeScript and Python both express the
Repository as a structural interface, a `Protocol` in Python and an
`interface` in TypeScript, satisfied by any type with the right shape. Go
has no exceptions, so the Application layer returns an error value instead
of throwing, which is the idiomatic Go shape for the same Domain-layer
rejection.

### Python

```python
from dataclasses import dataclass
from typing import Protocol


class InsufficientCreditError(Exception):
    pass


@dataclass
class Order:
    customer_id: str
    total_cents: int
    placed: bool = False

    def place(self, credit_limit_cents: int) -> None:
        if self.total_cents > credit_limit_cents:
            raise InsufficientCreditError(
                f"order {self.total_cents} exceeds credit limit {credit_limit_cents}"
            )
        self.placed = True


class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...
    def credit_limit_for(self, customer_id: str) -> int: ...


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders: list[Order] = []
        self._credit_limits: dict[str, int] = {"cust-1": 5000}

    def save(self, order: Order) -> None:
        self._orders.append(order)

    def credit_limit_for(self, customer_id: str) -> int:
        return self._credit_limits.get(customer_id, 0)


@dataclass
class PlaceOrderCommand:
    customer_id: str
    total_cents: int


class PlaceOrderService:
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def handle(self, command: PlaceOrderCommand) -> Order:
        limit = self._repository.credit_limit_for(command.customer_id)
        order = Order(customer_id=command.customer_id, total_cents=command.total_cents)
        order.place(limit)
        self._repository.save(order)
        return order


def handle_place_order_request(service: PlaceOrderService, customer_id: str, total_cents: int) -> str:
    order = service.handle(PlaceOrderCommand(customer_id=customer_id, total_cents=total_cents))
    return f"order placed for {order.customer_id}, total {order.total_cents}"


if __name__ == "__main__":
    repo = InMemoryOrderRepository()
    service = PlaceOrderService(repo)
    print(handle_place_order_request(service, "cust-1", 1200))
    try:
        handle_place_order_request(service, "cust-1", 9000)
    except InsufficientCreditError as exc:
        print(f"rejected: {exc}")
```

Run and verified. Output is `order placed for cust-1, total 1200` then
`rejected: order 9000 exceeds credit limit 5000`.

### TypeScript

```typescript
class InsufficientCreditError extends Error {}

class Order {
  placed = false;
  constructor(readonly customerId: string, readonly totalCents: number) {}

  place(creditLimitCents: number): void {
    if (this.totalCents > creditLimitCents) {
      throw new InsufficientCreditError(
        `order ${this.totalCents} exceeds credit limit ${creditLimitCents}`
      );
    }
    this.placed = true;
  }
}

interface OrderRepository {
  save(order: Order): void;
  creditLimitFor(customerId: string): number;
}

class InMemoryOrderRepository implements OrderRepository {
  private orders: Order[] = [];
  private creditLimits = new Map<string, number>([["cust-1", 5000]]);

  save(order: Order): void {
    this.orders.push(order);
  }

  creditLimitFor(customerId: string): number {
    return this.creditLimits.get(customerId) ?? 0;
  }
}

interface PlaceOrderCommand {
  customerId: string;
  totalCents: number;
}

class PlaceOrderService {
  constructor(private readonly repository: OrderRepository) {}

  handle(command: PlaceOrderCommand): Order {
    const limit = this.repository.creditLimitFor(command.customerId);
    const order = new Order(command.customerId, command.totalCents);
    order.place(limit);
    this.repository.save(order);
    return order;
  }
}

function handlePlaceOrderRequest(
  service: PlaceOrderService,
  customerId: string,
  totalCents: number
): string {
  const order = service.handle({ customerId, totalCents });
  return `order placed for ${order.customerId}, total ${order.totalCents}`;
}

const repo = new InMemoryOrderRepository();
const service = new PlaceOrderService(repo);
console.log(handlePlaceOrderRequest(service, "cust-1", 1200));
try {
  handlePlaceOrderRequest(service, "cust-1", 9000);
} catch (err) {
  if (err instanceof InsufficientCreditError) {
    console.log(`rejected: ${err.message}`);
  }
}
```

Compiled with `tsc --strict` and run with `node`. Same output as the
Python version above.

### Go

Go has no inheritance and no exceptions, so the Application layer's
error path is an explicit return value rather than a raised type, which is
the idiomatic Go shape for the same Domain-layer rejection shown above.

```go
package main

import "fmt"

type InsufficientCreditError struct {
	total int
	limit int
}

func (e *InsufficientCreditError) Error() string {
	return fmt.Sprintf("order %d exceeds credit limit %d", e.total, e.limit)
}

type Order struct {
	CustomerID string
	TotalCents int
	Placed     bool
}

func (o *Order) Place(creditLimitCents int) error {
	if o.TotalCents > creditLimitCents {
		return &InsufficientCreditError{total: o.TotalCents, limit: creditLimitCents}
	}
	o.Placed = true
	return nil
}

type OrderRepository interface {
	Save(order *Order)
	CreditLimitFor(customerID string) int
}

type InMemoryOrderRepository struct {
	orders       []*Order
	creditLimits map[string]int
}

func NewInMemoryOrderRepository() *InMemoryOrderRepository {
	return &InMemoryOrderRepository{
		creditLimits: map[string]int{"cust-1": 5000},
	}
}

func (r *InMemoryOrderRepository) Save(order *Order) {
	r.orders = append(r.orders, order)
}

func (r *InMemoryOrderRepository) CreditLimitFor(customerID string) int {
	return r.creditLimits[customerID]
}

type PlaceOrderCommand struct {
	CustomerID string
	TotalCents int
}

type PlaceOrderService struct {
	repository OrderRepository
}

func NewPlaceOrderService(repository OrderRepository) *PlaceOrderService {
	return &PlaceOrderService{repository: repository}
}

func (s *PlaceOrderService) Handle(command PlaceOrderCommand) (*Order, error) {
	limit := s.repository.CreditLimitFor(command.CustomerID)
	order := &Order{CustomerID: command.CustomerID, TotalCents: command.TotalCents}
	if err := order.Place(limit); err != nil {
		return nil, err
	}
	s.repository.Save(order)
	return order, nil
}

func HandlePlaceOrderRequest(service *PlaceOrderService, customerID string, totalCents int) (string, error) {
	order, err := service.Handle(PlaceOrderCommand{CustomerID: customerID, TotalCents: totalCents})
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("order placed for %s, total %d", order.CustomerID, order.TotalCents), nil
}

func main() {
	repo := NewInMemoryOrderRepository()
	service := NewPlaceOrderService(repo)

	result, _ := HandlePlaceOrderRequest(service, "cust-1", 1200)
	fmt.Println(result)

	_, err := HandlePlaceOrderRequest(service, "cust-1", 9000)
	if err != nil {
		fmt.Printf("rejected: %s\n", err)
	}
}
```

Run with `go run`. Same output as the Python and TypeScript versions above.
Java, Rust, and Swift are omitted from this entry not because the pattern
does not translate, it translates directly, an interface-based Repository
and a class-based Application Service work the same way in all three, but
because the three languages shown already demonstrate the pattern's full
range, an exception-based rejection path, a structural interface, and an
explicit error-value rejection path, without repeating the same shape a
fourth and fifth time.

## 18. References

1. Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, Michael
   Stal, *Pattern-Oriented Software Architecture, Volume 1. A System of
   Patterns*, John Wiley and Sons, 1996, chapter 2, the Layers pattern.
2. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, chapter 4, "Isolating the Domain."
3. Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley,
   2013, chapter 4, "Architecture," the section discussing layered,
   hexagonal, and related architectural styles for a bounded context.
4. Martin Fowler, "PresentationDomainDataLayering,"
   <https://martinfowler.com/bliki/PresentationDomainDataLayering.html>,
   verified 2026-08-02.
5. Microsoft Learn, Azure Architecture Center, "N-tier architecture
   style,"
   <https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/n-tier>,
   verified 2026-08-02.
6. Alistair Cockburn, "Hexagonal architecture," description of Ports and
   Adapters, referenced in dimension 8 and dimension 13 as the concentric-
   ring restatement of the same dependency-inversion principle. Cited here
   for attribution of the pattern name and its author rather than for a
   specific quoted claim.
7. Jeffrey Palermo, description of Onion Architecture, referenced in
   dimension 8 for attribution of the pattern name and author, in the same
   context as the Cockburn citation above.
