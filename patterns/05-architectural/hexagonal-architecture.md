---
name: Hexagonal Architecture
slug: hexagonal-architecture
family: 05-architectural
category: Architectural
aliases: [Ports and Adapters, Ports & Adapters]
first_described: "Cockburn 2005"
maturity: canonical
related: [adapter, dependency-injection, repository, strategy, onion-architecture, clean-architecture, anti-corruption-layer]
incompatible_with: []
verified: 2026-08-02
---

# Hexagonal Architecture

## 1. Name, aliases, and lineage

The canonical name is Hexagonal Architecture. Alistair Cockburn coined it and,
in the same publication, renamed it to what most practitioners now say instead,
**Ports and Adapters**. Cockburn's own site states the pattern's intent in one
sentence, quoted directly. "Allow an application to equally be driven by users,
programs, automated test or batch scripts, and to be developed and tested in
isolation from its eventual run-time devices and databases." Alistair Cockburn,
"Hexagonal architecture", https://alistair.cockburn.us/hexagonal-architecture/,
originally published 2005, verified 2026-08-02. Cockburn later co-authored a
book-length treatment with Juan Manuel Garrido de Paz, published April 2024,
which formalizes the terminology this entry uses. Wikipedia contributors,
"Hexagonal architecture (software)",
https://en.wikipedia.org/wiki/Hexagonal_architecture_(software), verified
2026-08-02, cross-checked against Cockburn's own page for the book date.

Cockburn is explicit, on the same page, that the hexagon itself carries no
technical meaning. "The hexagon is not a hexagon because the number six is
important, but rather to allow the people doing the drawing to have room to
insert ports and adapters as they need, not being constrained by a
one-dimensional layered drawing." (Cockburn, cited above, verified
2026-08-02.) Anyone who spends time arguing over why the diagram has six sides
rather than five or eight has misread the source. The shape is a drawing
convention that buys horizontal space for an arbitrary number of ports around
a circle, nothing more.

Two names, and two audiences. "Hexagonal Architecture" is the name people
reach for in conversation and in search engines, because the shape is
memorable. "Ports and Adapters" is the name Cockburn actually prefers, because
it names the two structural elements a reader has to build. This entry treats
the two as one pattern with two labels, in line with how the source itself
treats them, and uses "Ports and Adapters" wherever the prose benefits from
the more literal name.

The vocabulary is precise and worth fixing before anything else, because most
of the pattern's failure modes, dimension 11, come from blurring it.

- **Port.** A contract the application core declares, in the core's own
  language, independent of any technology that will eventually satisfy it.
  Cockburn's page puts it this way. "The word 'port' is supposed to evoke
  thoughts of ports in an operating system, where any device that adheres to
  the protocols of a port can be plugged into it." A port is an interface, a
  trait, a protocol, or in a language with structural typing, an implicit
  shape. It is never a concrete class.
- **Adapter.** A technology-specific implementation that satisfies a port, or
  that calls through one. Cockburn again, describing the same idea. "For each
  external device there is an adapter that converts the API definition to the
  signals needed by that device and vice versa." One port can have many
  adapters. A `PaymentPort` might be satisfied in production by a Stripe
  adapter, in a second market by a Adyen adapter, and in a test suite by an
  in-memory adapter that never leaves the process.
- **Primary (driving) actor and adapter.** An actor that starts a use case.
  Cockburn defines it plainly. "A primary actor is an actor that drives the
  application (takes it out of quiescent state to perform one of its
  advertised functions)." An HTTP controller, a CLI command, a scheduled job
  trigger, and an automated test are all primary adapters, because each one
  calls into the application, the application never calls them.
- **Secondary (driven) actor and adapter.** An actor the application calls
  out to. Cockburn again. "A secondary actor is one that the application
  drives, either to get answers from or to merely notify." A database, a
  message broker, an external payment gateway, and a filesystem are secondary
  adapters, reached through secondary, driven ports the application core
  declares.

The most common naming confusion in production code is worth naming here so
dimension 11 can point back at it. People often say "the API layer" for what
is really a primary adapter and "the persistence layer" for what is really a
secondary adapter, and then wonder why their layered diagram and their
hexagonal diagram never quite agree. They agree on direction of control, not
on vocabulary, and reconciling the two vocabularies is dimension 13's job.

## 2. Problem and context

A codebase reaches a specific, recognizable moment. The business logic, the
rules that decide whether an order can ship, whether a subscription renews,
whether a claim is approved, is written directly against a web framework's
request object on one side and an ORM's query builder on the other. The
logic reads correctly. It also cannot be exercised without a running HTTP
server and a live database connection, because the framework types and the
ORM types are woven through every function signature. A unit test that wants
to check one business rule has to first stand up infrastructure that has
nothing to do with the rule.

This shows up as three separate, compounding symptoms. First, the test suite
is slow, because "unit" tests are secretly integration tests wearing a unit
test's file name, and a developer avoids running them, which means they run
less often and catch less. Second, a technology swap, moving from a SQL
database to a document store, replacing a payment provider, migrating from a
monolith's in-process call to a network call, touches the business logic
files even though the business rule did not change, because the framework
types leaked into the rule. Third, and least visible until it bites, the
application accretes a second, informal API as more entry points arrive. The
web API says one thing, the CLI import script says something slightly
different, because each entry point re-implements pieces of the same rule
against its own concerns, and the two drift.

The context in which this problem is worth solving has a specific shape too.
The application has, or will soon have, more than one way in, a web API and
a batch job, a web API and a gRPC service, a UI and an admin CLI, or more
than one way out, a primary datastore and a read replica, a payment provider
that will be swapped for regulatory reasons, an external service the team
does not control the uptime of. If an application genuinely has exactly one
entry point, one exit point, one team, and a short life, the cost this
pattern asks for buys little, and dimension 4's non-applicability list says
so directly. The pattern earns its place when the number of technologies
touching the business logic, counted honestly, is more than one on either
side of it, or is expected to grow past one within the application's
realistic lifetime.

## 3. Forces

- **Testability against speed of feedback.** Isolating the core from
  infrastructure buys tests that run in milliseconds with no network and no
  disk. The price is an extra layer of indirection between "click run" and
  "see the assertion fail" that a developer new to the codebase has to learn
  to navigate.
- **Technology independence against directness.** A port hides which
  database, queue, or HTTP client sits behind it, which is the entire point
  when that choice is expected to change. For a rule that will genuinely
  never move off one database, the same hiding is a layer of ceremony with
  no payoff, and a direct call reads better.
- **Team boundaries against a single mental model.** When a platform team
  owns the ports and several feature teams write adapters against them, the
  contract at the boundary is a real coordination tool, and each team can
  ship independently as long as the contract holds. In a single small team
  working in one repository, the same boundary is one more place to keep two
  files in agreement for no organizational benefit.
- **Consistency at the boundary against flexibility inside it.** A driven
  port that returns a small, stable, core-owned type keeps every adapter
  honest about what the core actually needs. The same discipline means every
  new capability an adapter could offer, a database transaction, a specific
  index hint, a provider-specific retry policy, has to earn its way through
  the port's contract before the core can use it, which is friction by
  design, not an oversight.
- **Cognitive load against precision of intent.** Once a reader knows the
  vocabulary, "primary port" and "secondary port" say exactly which side of
  the application a type belongs to, at a glance. Before that vocabulary is
  learned, a codebase organized this way reads as unfamiliar indirection,
  interfaces that appear to have one implementation apiece, layers a
  newcomer has to be walked through.
- **Operability against uniformity of logging.** A thin adapter is a natural
  place to attach a timeout, a retry policy, a circuit breaker, and
  structured logging that is specific to the technology it wraps, dimension
  16. The cost is that operational behavior now lives at the edge, in
  several small files, rather than in one place a reader can scan.

Reach this weighing as engineering judgement, informed by the sources above,
not as a sourced fact. For a team of two shipping a short-lived internal
tool against one database with one entry point, testability and
technology independence are forces that do not fire, and the pattern's cost
in class count and indirection dominates. For a team maintaining a payment
or ordering core that several channels depend on and that will, at some
point, migrate a dependency, the same forces fire hard, and the pattern
usually pays for itself inside the first migration it survives cleanly.

## 4. Applicability and non-applicability

Reach for Hexagonal Architecture when the following hold.

- The application has, or will realistically soon have, more than one entry
  point, a web API and a background worker, a UI and an admin tool, an
  event consumer and a synchronous API, that must trigger the same business
  rule.
- The application has, or will realistically soon have, more than one
  external dependency of the same kind that could plausibly be swapped, a
  primary database that might migrate, a payment provider chosen per
  market, a notification channel that might move from email to a queue.
- The team wants to run the business logic's tests without booting a
  database, a web server, or a network stub, and wants that property to
  hold as the codebase grows rather than to erode over a year of shortcuts.
- The core domain logic is genuinely non-trivial, meaning a rule change
  requires more than editing one `if` statement, so isolating it from
  infrastructure churn earns back the up-front cost of drawing the
  boundary.
- A platform or core team owns shared business logic that several product
  teams build channels on top of, and the port is the contract those teams
  agree to build against.
- The system is expected to outlive at least one of its current
  infrastructure choices, which is the honest way of asking whether the
  application will exist for more than one framework major version or one
  database engine's realistic service life.

Do NOT reach for Hexagonal Architecture in these cases, and the reason
matters more than the rule.

- **A short-lived script, a prototype, or a proof of concept.** If the code
  is not expected to survive the demo, the ports buy isolation the project
  will never need and never gets tested by a second implementation. Write
  it directly against the one technology it uses.
- **A single-purpose CRUD service with one client and one datastore, and no
  credible plan to add either.** When there is exactly one way in and
  exactly one way out, and both are expected to stay that way, a port
  around each is an interface with one implementation forever, which is the
  specific smell dimension 11 names as premature abstraction. A layered
  structure without the extra indirection is the honest shape here.
- **The team has not learned the vocabulary yet and there is schedule
  pressure.** A team applying "primary" and "secondary" adapters for the
  first time under deadline pressure tends to produce the confusion
  dimension 11 calls the primary and secondary mix-up, which is worse for
  the codebase than a plain layered design that the team actually
  understands. Teach the pattern on a lower-stakes piece of work first.
- **The bottleneck is genuinely the data access pattern, not the business
  logic's independence from infrastructure.** If the real problem is query
  performance, N+1 loading, or a schema that fights the domain model,
  Hexagonal Architecture does not touch any of that. It relocates the
  problem behind a port without solving it, and a team that reaches for
  this pattern here mistakes reorganization for optimization.
- **The application is a thin proxy or a pure transformation pipeline with
  no domain rule to protect.** A service whose entire job is to reshape one
  wire format into another has no core worth isolating. The transformation
  logic is the whole application, and wrapping it in ports adds files
  without adding a boundary that protects anything.
- **A framework already enforces the same separation more cheaply for the
  team's actual need.** Some frameworks, a strict Model-View-Presenter
  stack, certain event-sourced frameworks, already keep domain logic clear
  of I/O by construction. Hand-rolling ports and adapters on top duplicates
  a guarantee the framework already gives, for the specific need at hand,
  and the honest move is to confirm that overlap before adding a second
  mechanism.
- **The organization cannot commit to keeping the core free of framework
  types over time.** The pattern is only as strong as the discipline that
  keeps a request object or an ORM entity out of the core. A team that will
  not enforce that boundary in code review gets the cost of extra files
  with none of the isolation benefit, because the framework leaks back in
  through the first adapter someone was in a hurry to finish.

## 5. Structure

Five participants, named by the role each plays, matching the vocabulary
fixed in dimension 1.

- **Application Core.** The business logic and domain model, written in
  plain language types with no import from a web framework, an ORM, an HTTP
  client library, or a message broker SDK. It is the one part of the system
  every port and adapter exists to protect.
- **Driving (primary) port.** An interface the core exposes for the outside
  world to call in through. It describes a use case in the core's own
  vocabulary. `OrderPlacer.placeOrder(customerId, sku, qty)` names a
  business action, never an HTTP verb or a database call.
- **Driven (secondary) port.** An interface the core declares for
  capabilities it needs from the outside world. `InventoryPort.reserve(sku,
  qty)` and `OrderRepository.save(order)` are declared by, and belong to,
  the core. The core owns both the interface and the decision of what
  belongs in it, which is the Dependency Inversion Principle applied at an
  architectural boundary rather than a single class.
- **Driving (primary) adapter.** Code that translates an external trigger,
  an HTTP request, a CLI invocation, a scheduled tick, a test assertion,
  into a call on a driving port. It owns the mapping between wire format
  and the core's method signature, and nothing else.
- **Driven (secondary) adapter.** Code that implements a driven port using
  a specific technology, a SQL database, an in-memory map for tests, a
  third-party payment SDK. It owns the mapping between the core's port
  contract and that technology's own API.

Relationships. The core depends on its own ports, and on nothing outside
itself. Driving adapters depend on driving ports. Driven adapters depend on
driven ports, they implement them. No adapter depends on another adapter
directly, and no adapter depends on the core's concrete implementation
class, only on the interface the core published. A sixth, unnamed
participant does real work in every hexagonal codebase and is worth naming
here rather than leaving implicit, the **composition root**, the place,
commonly a `main` function, a dependency injection container's
configuration, or a test's setup block, where concrete adapters are chosen
and wired into the core's constructor. The composition root is deliberately
outside the hexagon. It is the one place in the system permitted to know
about every adapter at once, because wiring is not business logic.

## 6. ASCII structure diagram

```
        DRIVING SIDE                                     DRIVEN SIDE
     (primary adapters)                             (secondary adapters)

  +----------------+                                   +------------------+
  |  CLI adapter   |--+                             +->| InMemoryInventory|
  +----------------+  |                             |  +------------------+
                       |     +-------------------+   |
  +----------------+   +---->|    OrderPlacer    |   |
  |  HTTP adapter  |-------->|   (driving port)   |   |
  +----------------+   +---->|                   |---+
                       |     |    OrderService    |
  +----------------+   |     | (application core) |---+
  |  Test harness  |--+      |                   |   |
  +----------------+         | uses InventoryPort|   |  +------------------+
                              | uses OrderRepo    |   +->| InMemoryOrderRepo|
                              +-------------------+      +------------------+

     Arrows into OrderPlacer are calls IN, through a driving port.
     Arrows out of OrderService are calls OUT, through a driven port.
     The core depends on the ports only, never on a concrete adapter.
```

The diagram is deliberately asymmetric left to right even though the usual
hexagon drawing is not, to keep the direction of control legible in plain
text. Every arrow on the left points rightward into the core. Every arrow on
the right points rightward out of the core. Nothing points from a
right-hand box back into a left-hand box, because a secondary adapter never
calls a primary adapter, and the two sides never talk to each other except
through the core.

## 7. Dynamics

```
   HTTP        OrderPlacer     OrderService     InventoryPort   OrderRepo
   adapter     (driving port)  (core)           (driven port)   (driven port)
     |               |               |                 |               |
     | POST /orders  |               |                 |               |
     |-------------->|               |                 |               |
     |               | placeOrder()  |                 |               |
     |               |-------------->|                 |               |
     |               |               | reserve(sku,qty)|               |
     |               |               |---------------->|               |
     |               |               |    ok           |               |
     |               |               |<----------------|               |
     |               |               |          save(order)            |
     |               |               |--------------------------------->
     |               |               |          ok                     |
     |               |               |<---------------------------------
     |               |    Order      |                                 |
     |               |<--------------|                                 |
     |  201 Created  |               |                                 |
     |<--------------|               |                                 |

   If reserve() returns InsufficientStockError, OrderService never calls
   save(), and the driving adapter maps the domain error to its own
   vocabulary. 409 for HTTP, a non-zero exit for a CLI, a NACK for a
   queue consumer. The core returns a domain error, never an HTTP status
   code or a SQL error code.
```

Two properties of this flow are worth stating in prose, because they are
easy to lose in a diagram. First, `OrderService` never knows it is being
called from HTTP. It receives typed arguments and returns a typed `Order` or
raises a typed domain error, full stop. Everything HTTP-specific, the verb,
the route, the status code mapping, lives entirely in the HTTP adapter, on
both the way in and the way out. Second, the two driven calls in the middle
are sequential and both belong to the core's own control flow, which is a
design decision, not an accident of the diagram. The core decides that
reserving stock happens before persisting the order, and that decision is
readable in `OrderService` without opening either adapter. A different
core implementation could call the two ports in the other order, or wrap
both in a single transactional port, and that choice is exactly the kind of
business rule the pattern exists to keep visible in one place instead of
scattered across whichever adapter happened to be written first.

## 8. Implementation variants

**Classical object-oriented ports as interfaces.** Java, C#, and Kotlin
favor this form, because the language wants an explicit `interface` keyword
and explicit `implements` declaration. A driven port is an interface owned
by the core package; a driven adapter is a class in an infrastructure
package that implements it and is wired in at the composition root through
constructor injection. This is the form most tutorials show, and it is the
form Tom Hombergs demonstrates end to end, with a full Spring Boot example,
in the companion repository to his book. Tom Hombergs, *Get Your Hands Dirty
on Clean Architecture*, 2nd edition, and the accompanying `buckpal`
repository, https://github.com/thombergs/buckpal, verified 2026-08-02. Read
as a reference implementation rather than as a claim of production use. The
repository itself is a teaching companion to the book, not a company's live
system, and this entry cites it only for the classical Java and Spring
implementation shape shown in dimension 9's real examples.

**Structural typing, no explicit interface keyword.** TypeScript and Go both
let a type satisfy a port by shape rather than by declared inheritance. In
Go this is idiomatic to the point of being the language's dominant pattern
for testable code. A small interface declared by the consuming package, the
"accept interfaces, return structs" convention, satisfied implicitly by
anything with matching method signatures, with no `implements` keyword at
all. In TypeScript, an object literal or a class satisfies an interface
purely by having the right method shapes, which means a driven adapter does
not even need to name the port it satisfies in its own file, only in the
composition root where it is assigned to a variable of that interface type.
This variant removes ceremony at the cost of a compiler that will not
immediately tell a reader every implementor of a port; an IDE's "find
implementations" feature closes that gap in practice.

**Duck typing and `Protocol` in Python.** Python has no compile-time
interface check, so a driven port is conventionally either an
`abc.ABC` with `@abstractmethod`, runtime-enforced, closer to the classical
form and useful when the team wants `isinstance` checks and explicit
subclassing to fail loudly, or a `typing.Protocol`, structural, checked
only by a static type checker such as mypy or pyright, and satisfied by any
object with matching methods, with no inheritance relationship required at
all. Django-adjacent codebases lean toward the ABC form because Django's
own conventions favor explicit base classes; framework-light Python
services increasingly favor `Protocol` for the same reason Go favors
implicit interfaces, less coupling between the port's definition and every
adapter that will ever satisfy it.

**Functional core, imperative shell.** A cousin variant, common in
functional-leaning codebases, Clojure, Elixir, and functional-style Rust or
TypeScript, replaces "a port is an interface" with "a port is a function
signature, and the core is a pure function or a small set of pure
functions with no side effects at all." Adapters become the only place I/O
happens; the core takes data in, returns data or a description of an
effect to perform, and never calls out itself. This is functionally
equivalent to Ports and Adapters, the core still has no infrastructure
dependency, described using functions instead of implementations behind
interfaces, and it is the natural shape when the host language treats
functions as first-class values, so passing a function in place of an
adapter object needs no interface declaration at all.

**Hexagonal Architecture combined with Domain-Driven Design.** Vaughn
Vernon's treatment of implementing a bounded context leans on exactly this
combination. The domain model and its aggregates form the application core,
repositories are driven ports, and application services form the layer that
driving adapters call into. Vaughn Vernon, *Implementing Domain-Driven
Design*, Addison-Wesley, 2013, ISBN 978-0-321-83457-7, part III on
implementing the domain model and its repositories. This combination is
common enough that many engineers meet the two ideas together and assume
they are one pattern; they are not. Hexagonal Architecture says nothing
about aggregates, bounded contexts, or ubiquitous language, and a codebase
can use ports and adapters around a purely procedural core with no
Domain-Driven Design vocabulary at all.

**Port granularity, one big port versus many small ones.** A team can
declare one `OrderGateway` port with every persistence and inventory
operation the order flow needs, or split it into `InventoryPort` and
`OrderRepository` as this entry's example does. The finer split follows the
Interface Segregation Principle and lets a test double implement only the
port it exercises; the coarser split reduces the number of files and
constructor parameters at the cost of forcing every adapter to implement
methods it may not need. Dimension 11 names the failure mode at the finer
end of this spectrum taken too far.

## 9. Known production uses

**Netflix Studio Workflows.** Netflix's Studio Engineering team built a
production application that had to integrate data from several sources,
gRPC, a JSON API, and later GraphQL, behind one consistent domain model.
They organized the code into entities, repositories as driven ports, and
interactors as the application core's use cases, following Hexagonal
Architecture explicitly. When a read-scaling constraint forced a swap from
their monolithic JSON API data source to a GraphQL source, the change was,
in their own account, a single-line change at the composition root because
the interactors depended only on the repository interface, not on either
concrete data source. The same isolation let them run roughly three thousand
specs in about a hundred seconds with no external dependencies booted.
Damir Svrtan and Sergii Makagon, "Ready for changes with Hexagonal
Architecture", Netflix Technology Blog, March 10, 2020,
https://netflixtechblog.com/ready-for-changes-with-hexagonal-architecture-b315ec967749
verified 2026-08-02.

**Shopify's App Store Ads team.** Shopify engineer Jay Shrivastava describes
the team's own commitment in plain terms. "We're committed to following a
Hexagonal Structure with dependency injection." The team composes tasks by
injecting the ports and adapters a request needs at the point where it
enters the system, and credits the approach with letting components be
developed and tested in isolation from each other. Jay Shrivastava, "Writing
Better, Type-safe Code with Sorbet", Shopify Engineering Blog, June 24, 2020,
https://shopify.engineering/writing-better-type-safe-code-with-sorbet
verified 2026-08-02.

**AWS's own guidance for production Lambda services.** Amazon Web Services
publishes Hexagonal Architecture as its recommended pattern for building
evolvable, testable business logic on AWS Lambda, a pattern its own
architects hand to customers building production serverless systems, worked
through with a stock-value conversion service as the running example, and
explicitly framed around swapping infrastructure, adding a caching layer,
changing compute platform, without touching the domain logic. Luca
Mezzalira, Principal Solutions Architect for Media and Entertainment,
"Developing evolutionary architecture with AWS Lambda", AWS Compute Blog,
July 8, 2021,
https://aws.amazon.com/blogs/compute/developing-evolutionary-architecture-with-aws-lambda/
verified 2026-08-02.

## 10. Consequences

Positive.

- The application core's business rules can be exercised by fast, in-process
  tests with zero network calls, zero database connections, and zero test
  containers, because every port a test needs is satisfied by a small
  hand-written or generated in-memory adapter.
- A technology behind a driven port, a database engine, a payment provider,
  a message broker, can be replaced, or run alongside its predecessor during
  a migration, without changing a single line of the business rule that uses
  it, provided the port's contract did not need to change.
- Several entry points, a web API, a CLI, a scheduled job, an event
  consumer, can share one core implementation of a use case instead of each
  reimplementing the rule against its own concerns, closing the drift
  described in dimension 2.
- The boundary gives a team a concrete, reviewable contract to negotiate
  across, the port's method signatures and types, instead of an informal
  agreement about how the database layer works.
- Adapters become natural, isolated homes for cross-cutting operational
  concerns, a timeout, a retry policy, structured logging specific to one
  technology, that would otherwise be scattered through business logic.

Negative.

- A working single-technology application gains an interface, a
  constructor parameter, and a composition-root wiring line for every
  capability it needs, even when exactly one implementation will ever
  exist. Martin Fowler observes that this approach "obscures the asymmetry"
  a straightforward layered design more directly represents between a
  service and the clients that use it, which is a real cost when the
  asymmetry was never a problem to begin with. Martin Fowler,
  "PresentationDomainDataLayering", martinfowler.com bliki, August 26, 2015,
  https://martinfowler.com/bliki/PresentationDomainDataLayering.html
  verified 2026-08-02.
- Readers new to a codebase, and new to the pattern's vocabulary, have to
  learn "driving" versus "driven" and "primary" versus "secondary" before
  the file layout makes sense, which is a real, if temporary, cost paid by
  every engineer who onboards.
- The core's types have to be translated at every boundary crossing, a
  request DTO to a domain type on the way in, a domain type to a response
  DTO on the way out, a domain type to a persistence model on the way to
  storage, and that translation code is genuine, if usually mechanical,
  extra code to write and keep in step with the domain model.
- A port that is drawn too coarse hides which operations an adapter
  actually needs to support; a port drawn too fine multiplies interfaces
  and constructor parameters. Getting the granularity right is a judgement
  call the pattern does not make for the team, and getting it wrong in
  either direction is a common source of churn.
- Nothing in the pattern prevents a team from building a technically
  correct hexagon around a core that still has the wrong domain model. The
  pattern isolates infrastructure from the domain; it has no opinion at all
  about whether the domain model is the right one.

## 11. Failure modes and misuse

**The leaky port.** Symptom. A "driven port" interface whose method
signatures take a `SqlConnection`, an `HttpRequestMessage`, or an
ORM-specific query object as a parameter or return type. Cause. The
interface was extracted after the fact from one concrete adapter, by
copying that adapter's signature, instead of being designed from what the
core actually needs to say. Fix. Rewrite the port in the core's own
vocabulary first, `reserve(sku, qty)`, not `execute(sqlStatement)`, then
make every adapter satisfy that vocabulary, translating internally.

**Anemic core, fat adapter.** Symptom. The `OrderService` class is a thin
pass-through that calls one adapter method and returns its result
unchanged, while the actual business rule, a discount calculation, an
eligibility check, is written inside the HTTP controller or the database
adapter because that was the fastest place to add it under deadline
pressure. Cause. The team drew the boxes correctly but did not enforce
where logic gets written, and the path of least resistance during a rush
is editing the file already open. Fix. Move the misplaced rule into the
core in the same change that is touched next, and treat a pull request
that adds business logic to an adapter file as a defect in code review,
not a style preference.

**Testing only through the primary adapter.** Symptom. The test suite spins
up an in-process HTTP server, or an equivalent full-stack rig, for every
test, even tests whose entire purpose is to check one business rule, because
"that's how we test this service." Cause. The team built the ports correctly
but never wrote a driving adapter, a plain function call, or a thin test
double satisfying the driving port directly, that bypasses the HTTP layer
for tests. Fix. Add a test-only driving adapter, or simply call the core's
constructor and its driving port method directly from the test, which is
exactly what the pattern was adopted to make possible in the first place.

**Port explosion from over-eager segregation.** Symptom. A single use case's
constructor takes nine single-method interfaces as parameters, and adding
any new capability means touching the composition root, the constructor
signature, and a new interface file. Cause. The Interface Segregation
Principle applied past the point where it earns its cost; the team split a
port every time a new method was added instead of when a genuinely
different set of adapters needed genuinely different subsets of the
contract. Fix. Group operations that always change and get adapted together
into one port, and only split further when two consumers demonstrably need
different subsets.

**The primary and secondary mix-up.** Symptom. A "repository" class that
both exposes a public method an HTTP controller calls directly, acting as a
driving entry point, and implements a driven port the core calls into,
acting as a driven adapter, so the direction of control through that one
class runs both ways depending on which caller you trace. Cause. The team
learned the boxes, "port," "adapter," without internalizing the
direction-of-control vocabulary from dimension 1, and merged two roles for
convenience. Fix. Split the class along the direction of control, one type
per role, even when the underlying technology, the same database
connection, say, is shared underneath.

**Adapter-to-adapter shortcuts.** Symptom. A driving HTTP adapter calls a
driven database adapter directly, bypassing the core entirely, because "it
was just a simple read" and going through the use case felt like ceremony.
Cause. Under time pressure, the shortest path between two boxes on the
diagram is a straight line that skips the middle box, and nothing in most
languages stops that call from compiling. Fix. Treat any import of a driven
adapter type from inside a driving adapter as a lint-level or code-review
level defect; the core is the only permitted path between the two sides.

**Domain types leaking through the wire boundary unchanged.** Symptom. A
JSON API response is generated by serializing a domain entity directly, so
every field the domain model happens to carry, an internal audit flag, a
soft-delete timestamp, a field added for an unrelated feature, is now part
of a public contract, and removing or renaming a domain field silently
breaks external clients. Cause. Skipping the DTO translation step at the
driving adapter boundary to save a file and a mapping function. Fix.
Introduce an explicit response type at the adapter boundary, even when it
is, for now, a field-for-field copy of the domain type; the two types are
allowed to diverge later precisely because they were never the same type
to begin with.

## 12. Trade-off matrix

Compared against named alternatives that address the same layering problem.

| Force | Hexagonal (Ports and Adapters) | Onion Architecture | Clean Architecture | Traditional N-Layer (UI, BLL, DAL) | Active Record / framework-coupled |
|---|---|---|---|---|---|
| Dependency direction | Inward, core owns every port | Inward, concentric rings toward a domain center | Inward, four labeled rings with a strict dependency rule | Downward only, UI depends on BLL depends on DAL | Outward from the framework, the model often is the ORM row |
| Testability of core logic | High, in-process, no infrastructure needed | High, same mechanism as Hexagonal | High, same mechanism as Hexagonal | Medium, BLL still often needs a real or faked DAL | Low, business logic is entangled with database calls |
| Naming and vocabulary | Ports, adapters, driving, driven | Rings, application services, domain services | Entities, use cases, interface adapters, frameworks and drivers | Presentation, business logic, data access | Model, view, controller, the framework's own names |
| Number of interfaces for a single-implementation case | One per capability, even with one adapter | Same as Hexagonal | Same as Hexagonal, plus the interactor and presenter roles | Usually none, DAL is called concretely | None, framework does not ask for one |
| Onboarding cost for a team new to the idea | Medium, two-word vocabulary to learn | Medium to high, ring metaphor needs a diagram to click | Medium to high, four named rings plus the dependency rule | Low, matches how most engineers were taught layering | Lowest, matches the framework's own tutorial |
| Swapping a driven technology | Cheap if the port was drawn from the core's needs | Cheap, same mechanism | Cheap, same mechanism | Possible but the DAL interface is often an afterthought | Expensive, the ORM's types are the domain types |
| Multiple entry points sharing one core | Direct fit, that is the driving-port idea | Direct fit | Direct fit, use cases are explicitly framework-agnostic | Awkward, BLL is usually written assuming one UI | Awkward, logic is often duplicated per controller |
| Framework buy-in required | None, the pattern is framework-agnostic by design | None | None | None | Total, the pattern only exists inside the framework's model |
| Team topology fit | Good for platform-plus-channel-teams organizations | Same as Hexagonal | Same as Hexagonal, slightly heavier ceremony | Good for a single team owning the whole stack | Good for a small team moving fast in one framework |

Reading of the table. Hexagonal, Onion, and Clean Architecture are, in
practice, the same dependency-direction idea described with three different
vocabularies and diagrams; the Microsoft .NET architecture documentation
states this directly. "This architecture has gone by many names over the
years. One of the first names was Hexagonal Architecture, followed by
Ports-and-Adapters. More recently, it's been cited as the Onion
Architecture or Clean Architecture." Microsoft, "Common web application
architectures", .NET Architecture documentation,
https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures
verified 2026-08-02. The real choice for most teams is not between these
three, it is between adopting any one of the three and staying inside a
traditional N-Layer or an Active Record style that couples the domain to
one framework's types. N-Layer wins when a team already understands it and
has one UI and one datastore for the application's realistic lifetime.
Active Record wins for speed of initial delivery in a framework built
around it, at the cost of everything dimension 10's negative list names.

## 13. Related and incompatible patterns

- **Adapter (GoF).** Not a cousin, the same word doing the same job at a
  smaller scale. Every secondary adapter in this pattern is, structurally,
  a GoF Adapter converting one interface, a third-party SDK's API, into
  another, the driven port the core declared. Hexagonal Architecture is,
  in one honest reading, a discipline for applying the Adapter pattern
  systematically at every technology boundary of an application rather than
  ad hoc at a few of them.
- **Dependency Inversion Principle.** The mechanism, not a separate
  pattern. A driven port exists because the core, the higher-level policy,
  must not depend on the lower-level detail, a database. The port is the
  abstraction both sides depend on, which is the Dependency Inversion
  Principle stated architecturally rather than at the level of one class.
- **Repository (Fowler, and Evans).** A specific, named instance of a
  driven port, specialized to persistence. Any codebase using both patterns
  together simply has a `Repository` interface playing the role of a
  driven port, with the same rules, own it from the core, translate at the
  boundary, applying.
- **Onion Architecture and Clean Architecture.** Composable in the loose
  sense that all three describe the same dependency direction with
  different vocabularies and different diagrams, as dimension 12
  establishes with a primary source. A codebase rarely needs more than one
  of the three vocabularies at once; picking one and being consistent about
  it matters more than which of the three is chosen.
- **Anti-Corruption Layer (Domain-Driven Design).** A close cousin, aimed
  specifically at the boundary with an external or legacy system whose
  model the team does not control. Where a driven port and adapter isolate
  the core from a technology choice, an Anti-Corruption Layer isolates the
  core from a foreign domain model, translating its concepts into the
  core's own, which is frequently implemented as exactly one more driven
  port and adapter pair with unusually rich translation logic inside the
  adapter.
- **Strategy (GoF).** Similar shape, different purpose, and worth
  distinguishing explicitly because both substitute one interface
  implementation for another at runtime. Strategy substitutes an
  *algorithm* the core chooses among as part of its own logic, which
  discount calculation to run. A driven port substitutes an
  *infrastructure* dependency the core needs but does not choose between as
  a business decision, which database happens to be running today. A
  `DiscountStrategy` selected by business rule is a Strategy; a
  `PaymentGateway` implementation selected by deployment configuration is a
  driven adapter.
- **Dependency injection and its container.** The delivery mechanism most
  teams use to wire adapters into the core at the composition root, but not
  a requirement of the pattern itself. Manual constructor wiring in a small
  `main` function satisfies the pattern exactly as well as a full container;
  a container simply automates the wiring at scale.
- **CQRS.** Composes cleanly and is frequently paired with Hexagonal
  Architecture in the same codebase, because CQRS's separate read and write
  models each get their own driving ports, a command handler port and a
  query handler port, without changing anything about how the pattern
  itself works.
- **Active Record.** Conflicts in practice. Active Record's premise is that
  the domain object *is* the persistence row, with save and load methods on
  the object itself. Hexagonal Architecture's premise is that the domain
  object must not know persistence exists. A codebase that adopts Active
  Record for its models has already made the incompatible choice, and
  wrapping Active Record objects in a hexagon afterward produces the leaky
  port failure mode from dimension 11, because the "port" ends up shaped
  by the ORM regardless of intent.
- **Service Locator.** Conflicts for the same reason it conflicts with
  Factory Method and most other explicit-dependency patterns. A core class
  that reaches into a global locator to find its own adapters hides the
  dependency the port was meant to make visible in the constructor, and
  reverses the direction of control the composition root exists to make
  explicit in one place.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it, in order, on a
single use case first rather than the whole codebase at once.

1. Pick one use case whose business rule currently reads directly against a
   web framework's request object and an ORM. Do not attempt the whole
   application in one change.
2. Write down, in plain language, the inputs and outputs that use case
   actually needs, what values come in, what value or error goes out. This
   becomes the signature of the driving port.
3. Extract the business rule itself into a plain class or function with no
   framework or ORM import, taking exactly the inputs from step 2. This is
   the first draft of the application core.
4. For each piece of infrastructure the extracted logic still calls, a
   database query, an external API call, write a driven port interface
   in the core's own vocabulary, matching what the logic actually needs,
   not what the current implementation happens to expose.
5. Write one driven adapter per port that wraps the existing infrastructure
   call unchanged, just moved behind the new interface. Nothing about the
   runtime behavior should change in this step; only the seam has moved.
6. Write a thin driving adapter, the original controller, now reduced to
   parsing the request, calling the driving port, and formatting the
   response, and wire the driven adapters into the core at a composition
   root.
7. Add an in-memory or fake driven adapter and a test that exercises the
   core directly through the driving port, with no framework and no real
   infrastructure running. This is the payoff step, and skipping it means
   the refactor bought file reorganization without buying the property the
   pattern exists for.
8. Repeat for the next use case, refactoring toward a shared core module
   and a shared set of driven ports as the second and third use cases reveal
   which capabilities are genuinely common.

Removing the pattern when it stops earning its place, which happens most
often when a service has settled onto one and only one technology on each
side of a port and shows no credible sign of changing either.

1. Confirm, honestly, that the driving side has exactly one adapter and the
   driven side has exactly one adapter per port, with no second
   implementation anywhere in the codebase, including tests, that would be
   lost by the removal.
2. Inline each single-implementation driven port. Replace calls to the
   interface with direct calls to the one concrete adapter's methods, and
   delete the interface.
3. Fold the driving adapter and the core's use case method together if the
   separation no longer buys a second entry point or a faster test path.
4. Keep any port that is still doing real work, most often a persistence
   port that a test suite depends on for an in-memory fake, even after
   every other port in the service has been inlined; removing a port used
   for testability trades a real, ongoing cost, test suite speed, for a
   one-time simplification, and that trade is usually the wrong direction.
5. Re-run the full test suite after every inlining step, because this
   direction of refactoring is exactly where the leaky-port failure mode in
   dimension 11 tends to surface retroactively, an interface that looked
   removable turns out to have been hiding a second, forgotten caller.

## 15. Testing and verification

This is substantially engineering practice rather than a sourced claim, and
is presented as such.

The core is tested with plain unit tests that construct it directly and
call its driving port method, with no test framework beyond the language's
own testing library, no HTTP client, no test container, and no real
database or queue. Every driven port the core depends on is satisfied by a
hand-written test double, a fake with real, if simplified, behavior, an
in-memory map standing in for a database, an in-memory list standing in for
a message broker, rather than a mock that only records calls. A fake that
actually reserves and releases inventory catches bugs a call-recording mock
cannot, because the fake enforces the same invariants, stock cannot go
negative, the real adapter would. This is the single largest testability
win the pattern exists to buy, and it is what the Netflix account in
dimension 9 is describing when it reports roughly three thousand specs
running in about a hundred seconds.

Each driven adapter gets a small, separate integration test suite that runs
against the real technology it wraps, a real database in a test container,
a sandbox account for a real payment provider, and that suite's job is
narrow. Prove the adapter correctly satisfies its port's contract, not
re-test the business rule the core already covers. A useful discipline
here is a shared contract test suite, one set of assertions written against
the port's interface, run once per adapter that claims to satisfy it, the
in-memory fake, the real database adapter, and any other implementation,
which catches the case where a fake and its real counterpart have quietly
drifted apart in behavior.

Driving adapters get their own thin tests too, but of a different kind.
Does the HTTP adapter parse a malformed request body correctly, does it map
each domain error to the right status code, does the CLI adapter print the
expected message on success and failure. These tests deliberately do not
re-test the business rule; they use a fake driving port implementation, a
stub that returns a canned `Order` or a canned error, so a failure in this
suite always means the adapter's own translation logic broke, never that
the business rule changed.

Genuine end-to-end tests, the ones that boot the real HTTP server against a
real or containerized database, still belong in the suite, kept
deliberately small in number, because they are the only tests that verify
the composition root wired the right concrete adapters together. Their job
is to catch wiring mistakes, not to re-verify business logic the fast core
tests already cover in depth.

## 16. Observability signals

Health, in a codebase organized this way, is visible at the seams rather
than inside the core, because that is precisely where the system meets the
outside world.

A healthy instance shows a small, stable set of driven-port call durations
in tracing, a `reserve` span, a `save` span, each one attributable to a
named adapter, so a latency spike can be pinned to "the payment adapter" or
"the inventory adapter" without needing to read code. Log lines tagged with
the port name and the adapter's concrete implementation name at startup,
logging which adapter was wired to which port at the composition root,
make it possible to confirm, from logs alone and without reading a config
file, which concrete technology a given deployment is actually running
against, which matters a great deal during a migration where two adapters
for the same port coexist behind a feature flag.

A failing instance shows a specific, recognizable pattern worth watching
for directly. A spike in errors thrown by one named adapter while every
other adapter's error rate stays flat is exactly the signal a
technology-specific outage, one payment provider down, one database
replica unreachable, should produce if the isolation the pattern promises
is actually holding. If, instead, an outage in one adapter causes errors to
appear inside the core's own logic, a null reference where a domain object
should be, a business rule throwing an exception whose stack trace bottoms
out in a driven adapter's internals rather than at the port boundary, that
is itself an observability signal that the leaky-port failure mode from
dimension 11 is present, because a well-drawn port should turn any
adapter-level failure into a typed domain error before it reaches the core.

The composition root is worth its own log line at process start, listing
every port and the concrete adapter chosen for it, because that single log
line is frequently the fastest way to answer which implementation a
deployment is actually using during an incident, faster than reading
environment variables or deployment manifests.

## 17. Security and privacy implications

The port boundary is a natural, and frequently underused, place to enforce
that sensitive data does not travel further than it needs to. A driven port
whose return type is a small, explicit value object, an `Order` with the
fields the core genuinely needs, rather than a raw response from a
third-party API forces a decision, at the adapter, about which fields cross
the boundary into the core and, from there, potentially into logs, caches,
or a response body. An adapter that passes through an entire third-party
API response unfiltered because "the interface said `Any`" reintroduces the
exact risk the boundary exists to prevent. A field a payment provider adds
to its response next year, a card's full number in a debug field, say,
flows straight through into wherever the core's return value ends up
without anyone having decided that it should.

The composition root is also the natural, single place to reason about
credential handling, because it is the one place in the system that
constructs every adapter and therefore the one place that must hold every
credential, a database connection string, an API key for a payment
provider, needed to do so. A codebase that keeps this wiring in one file or
one small module makes a credential audit tractable; a codebase that lets
individual adapters reach into environment variables or a secrets store
directly, scattered across many files, makes the same audit require
searching the whole codebase.

Where this pattern is silent, stated plainly rather than invented, it has
no opinion about authentication or authorization placement, which is a
judgement call left to the team, commonly enforced at the driving adapter,
before the driving port is called, though some teams push authorization
decisions into the core when the decision depends on domain state, no
opinion about encryption at rest or in transit, which remains entirely the
concern of whichever adapter talks to storage or the network, and no
opinion about input validation depth, which is frequently split between a
shallow, format-level check at the driving adapter and a deeper,
business-rule-level check inside the core, and the pattern does not decide
where that split should fall for a given application.

## 18. References

1. Alistair Cockburn. "Hexagonal architecture."
   https://alistair.cockburn.us/hexagonal-architecture/
   Originally published 2005. Verified 2026-08-02. Source of the pattern's
   stated intent, the port and adapter definitions, the primary and
   secondary actor definitions, and the explanation of why the diagram is a
   hexagon.
2. Wikipedia contributors. "Hexagonal architecture (software)."
   https://en.wikipedia.org/wiki/Hexagonal_architecture_(software)
   Verified 2026-08-02. Used only to confirm the 2005 renaming date and the
   April 2024 book publication with Juan Manuel Garrido de Paz, cross-checked
   against Cockburn's own site, not as a source of explanation.
3. Jeffrey Palermo. "The Onion Architecture. part 1." July 29, 2008.
   https://jeffreypalermo.com/blog/the-onion-architecture-part-1/
   Verified 2026-08-02. Source for the Onion Architecture's publication date
   and its stated shared premise with Hexagonal Architecture, cited in
   dimensions 1 and 13.
4. Robert C. Martin. "The Clean Architecture." August 13, 2012.
   https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
   Verified 2026-08-02. Primary source naming Hexagonal Architecture, Onion
   Architecture, and DCI as convergent approaches to the same
   dependency-direction idea, cited in dimensions 12 and 13.
5. Microsoft. "Common web application architectures." .NET Architecture
   documentation.
   https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures
   Verified 2026-08-02. Source for the direct statement that Hexagonal
   Architecture, Ports-and-Adapters, Onion Architecture, and Clean
   Architecture are the same idea under different names, cited in
   dimension 12.
6. Martin Fowler. "PresentationDomainDataLayering." martinfowler.com bliki.
   August 26, 2015.
   https://martinfowler.com/bliki/PresentationDomainDataLayering.html
   Verified 2026-08-02. Source for the observation that a hexagonal or
   mapper-based layering obscures the provider and consumer asymmetry a
   plainer layered design shows directly, cited in dimension 10.
7. Damir Svrtan and Sergii Makagon. "Ready for changes with Hexagonal
   Architecture." Netflix Technology Blog. March 10, 2020.
   https://netflixtechblog.com/ready-for-changes-with-hexagonal-architecture-b315ec967749
   Verified 2026-08-02. Source for the Netflix Studio Workflows production
   use in dimension 9.
8. Jay Shrivastava. "Writing Better, Type-safe Code with Sorbet." Shopify
   Engineering Blog. June 24, 2020.
   https://shopify.engineering/writing-better-type-safe-code-with-sorbet
   Verified 2026-08-02. Source for the Shopify App Store Ads team production
   use in dimension 9.
9. Luca Mezzalira. "Developing evolutionary architecture with AWS Lambda."
   AWS Compute Blog. July 8, 2021.
   https://aws.amazon.com/blogs/compute/developing-evolutionary-architecture-with-aws-lambda/
   Verified 2026-08-02. Source for AWS's official production guidance in
   dimension 9.
10. Tom Hombergs. *Get Your Hands Dirty on Clean Architecture*, 2nd
    edition. Self-published and traditionally published editions, and the
    accompanying `buckpal` reference repository.
    https://github.com/thombergs/buckpal
    Verified 2026-08-02. Source for the classical Java and Spring
    implementation shape discussed in dimension 8, cited as a teaching
    reference implementation, not as a claim of production use.
11. Vaughn Vernon. *Implementing Domain-Driven Design*. Addison-Wesley,
    2013. ISBN 978-0-321-83457-7. Part III, on implementing the domain
    model, its aggregates, and its repositories. Source for the
    Domain-Driven Design combination discussed in dimension 8.

## Code examples

Three languages, chosen for how differently each expresses a port. Go shows
the language's dominant, fully implicit interface-satisfaction style. Python
shows the `abc.ABC` explicit-inheritance style most Django-adjacent Python
services use for a driven port. TypeScript shows the same shape checked by
a structural type system, which needs no `implements` keyword at all for a
port to be satisfied. Java, Rust, and Swift are omitted here for length, not
because the pattern translates poorly to them. Java's shape matches the
classical interface form shown in dimension 8's Buckpal reference, Rust's
matches the trait-based shape of `IntoIterator` cited in the companion
Factory Method entry, and Swift's `protocol` type plays the identical role
to a Go or TypeScript port.

All three examples model the same use case. Placing an order requires
reserving stock through one driven port and persisting the order through a
second, separate driven port, and both are called from behind one driving
port so that a CLI adapter, an HTTP adapter, or a test can trigger the same
rule identically.

### Go

```go
package main

import (
	"errors"
	"fmt"
)

type Order struct {
	ID         string
	CustomerID string
	SKU        string
	Quantity   int
}

var ErrInsufficientStock = errors.New("insufficient stock")

// InventoryPort is a driven port. The core defines the contract; the
// outside world supplies an adapter that satisfies it.
type InventoryPort interface {
	Reserve(sku string, qty int) error
}

// OrderRepository is a second driven port, kept separate from
// InventoryPort so a caller can swap persistence without touching stock
// rules, and vice versa.
type OrderRepository interface {
	Save(o Order) error
}

// OrderPlacer is the driving port. Anything that wants to place an
// order, an HTTP handler, a CLI command, a scheduled job, calls
// through this interface and never touches OrderService directly.
type OrderPlacer interface {
	PlaceOrder(customerID, sku string, qty int) (Order, error)
}

// OrderService is the application core. It knows the business rule
// (reserve before you persist) and nothing about HTTP, SQL, or queues.
type OrderService struct {
	inventory InventoryPort
	orders    OrderRepository
	nextID    int
}

func NewOrderService(inv InventoryPort, repo OrderRepository) *OrderService {
	return &OrderService{inventory: inv, orders: repo}
}

func (s *OrderService) PlaceOrder(customerID, sku string, qty int) (Order, error) {
	if err := s.inventory.Reserve(sku, qty); err != nil {
		return Order{}, fmt.Errorf("place order: %w", err)
	}
	s.nextID++
	order := Order{ID: fmt.Sprintf("ord-%d", s.nextID), CustomerID: customerID, SKU: sku, Quantity: qty}
	if err := s.orders.Save(order); err != nil {
		return Order{}, fmt.Errorf("place order: %w", err)
	}
	return order, nil
}

// inMemoryInventory is a secondary adapter for InventoryPort. A
// production adapter would call a warehouse system instead.
type inMemoryInventory struct{ stock map[string]int }

func (a *inMemoryInventory) Reserve(sku string, qty int) error {
	if a.stock[sku] < qty {
		return ErrInsufficientStock
	}
	a.stock[sku] -= qty
	return nil
}

// inMemoryOrders is a secondary adapter for OrderRepository. A
// production adapter would write to a database instead.
type inMemoryOrders struct{ saved []Order }

func (a *inMemoryOrders) Save(o Order) error {
	a.saved = append(a.saved, o)
	return nil
}

// cliPlaceOrder is a primary adapter. It translates a command line
// call into a call on the driving port, then formats the result.
func cliPlaceOrder(placer OrderPlacer, customerID, sku string, qty int) {
	order, err := placer.PlaceOrder(customerID, sku, qty)
	if err != nil {
		fmt.Println("order rejected:", err)
		return
	}
	fmt.Printf("order %s placed for %s\n", order.ID, order.CustomerID)
}

func main() {
	// Composition root: wiring lives at the edge, never inside the core.
	inventory := &inMemoryInventory{stock: map[string]int{"sku-1": 5}}
	repo := &inMemoryOrders{}
	service := NewOrderService(inventory, repo)

	cliPlaceOrder(service, "cust-1", "sku-1", 2)
	cliPlaceOrder(service, "cust-2", "sku-1", 10)
}
```

Go declares no `implements` relationship anywhere in this file.
`inMemoryInventory` satisfies `InventoryPort` purely because it has a
matching `Reserve` method; the compiler checks this the moment
`NewOrderService` is called with it. A production adapter for a real
warehouse system would satisfy the same interface with no change at all to
`OrderService`.

### Python

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


class InsufficientStockError(Exception):
    pass


@dataclass
class Order:
    order_id: str
    customer_id: str
    sku: str
    quantity: int


class InventoryPort(ABC):
    """Driven port. The core owns this contract; adapters implement it."""

    @abstractmethod
    def reserve(self, sku: str, qty: int) -> None: ...


class OrderRepository(ABC):
    """A second driven port, separate from InventoryPort on purpose."""

    @abstractmethod
    def save(self, order: Order) -> None: ...


class OrderPlacer(ABC):
    """Driving port. Every entry point calls through this, never
    through OrderService directly."""

    @abstractmethod
    def place_order(self, customer_id: str, sku: str, qty: int) -> Order: ...


class OrderService(OrderPlacer):
    """Application core. Holds the reserve-then-persist rule and no
    knowledge of HTTP, SQL, or message queues."""

    def __init__(self, inventory: InventoryPort, orders: OrderRepository) -> None:
        self._inventory = inventory
        self._orders = orders
        self._next_id = 0

    def place_order(self, customer_id: str, sku: str, qty: int) -> Order:
        self._inventory.reserve(sku, qty)
        self._next_id += 1
        order = Order(f"ord-{self._next_id}", customer_id, sku, qty)
        self._orders.save(order)
        return order


class InMemoryInventory(InventoryPort):
    """Secondary adapter. A production adapter would call a warehouse
    system through this same port."""

    def __init__(self, stock: dict[str, int]) -> None:
        self._stock = stock

    def reserve(self, sku: str, qty: int) -> None:
        if self._stock.get(sku, 0) < qty:
            raise InsufficientStockError(sku)
        self._stock[sku] -= qty


class InMemoryOrderRepository(OrderRepository):
    """Secondary adapter. A production adapter would write to a
    database through this same port."""

    def __init__(self) -> None:
        self.saved: list[Order] = []

    def save(self, order: Order) -> None:
        self.saved.append(order)


def cli_place_order(placer: OrderPlacer, customer_id: str, sku: str, qty: int) -> None:
    """Primary adapter. Translates a CLI style call into a call on the
    driving port, then formats the result."""
    try:
        order = placer.place_order(customer_id, sku, qty)
    except InsufficientStockError as exc:
        print(f"order rejected: insufficient stock for {exc}")
        return
    print(f"order {order.order_id} placed for {order.customer_id}")


if __name__ == "__main__":
    # Composition root: wiring lives at the edge, never inside the core.
    inventory = InMemoryInventory({"sku-1": 5})
    orders = InMemoryOrderRepository()
    service = OrderService(inventory, orders)

    cli_place_order(service, "cust-1", "sku-1", 2)
    cli_place_order(service, "cust-2", "sku-1", 10)
```

The Python `ABC` form is the closer of the two Python variants to the
classical Java shape from dimension 8. `InventoryPort(ABC)` fails loudly at
instantiation time if an adapter forgets a method, which most teams prefer
for a driven port whose contract is expected to change rarely and whose
adapters are written by several different engineers over time. A
`typing.Protocol` version of the same file would drop the `ABC` base class
and the `@abstractmethod` decorators entirely and rely on a static type
checker instead of a runtime check.

### TypeScript

```typescript
interface Order {
  orderId: string;
  customerId: string;
  sku: string;
  quantity: number;
}

class InsufficientStockError extends Error {
  constructor(sku: string) {
    super(`insufficient stock for ${sku}`);
  }
}

// InventoryPort is a driven port. The core defines the contract; an
// adapter at the edge supplies the implementation.
interface InventoryPort {
  reserve(sku: string, qty: number): void;
}

// A second driven port, kept separate from InventoryPort so stock
// rules and persistence can change independently.
interface OrderRepository {
  save(order: Order): void;
}

// OrderPlacer is the driving port. Every entry point calls through
// this interface, never through OrderService directly.
interface OrderPlacer {
  placeOrder(customerId: string, sku: string, qty: number): Order;
}

// OrderService is the application core. It holds the reserve-then-save
// rule and knows nothing about HTTP, SQL, or a message broker.
class OrderService implements OrderPlacer {
  private nextId = 0;

  constructor(
    private readonly inventory: InventoryPort,
    private readonly orders: OrderRepository,
  ) {}

  placeOrder(customerId: string, sku: string, qty: number): Order {
    this.inventory.reserve(sku, qty);
    this.nextId += 1;
    const order: Order = { orderId: `ord-${this.nextId}`, customerId, sku, quantity: qty };
    this.orders.save(order);
    return order;
  }
}

// Secondary adapter for InventoryPort. A production adapter would
// call a warehouse system through this same interface.
class InMemoryInventory implements InventoryPort {
  constructor(private readonly stock: Record<string, number>) {}

  reserve(sku: string, qty: number): void {
    if ((this.stock[sku] ?? 0) < qty) {
      throw new InsufficientStockError(sku);
    }
    this.stock[sku] -= qty;
  }
}

// Secondary adapter for OrderRepository. A production adapter would
// write to a database through this same interface.
class InMemoryOrderRepository implements OrderRepository {
  saved: Order[] = [];

  save(order: Order): void {
    this.saved.push(order);
  }
}

// Primary adapter. Translates a CLI style call into a call on the
// driving port, then formats the result.
function cliPlaceOrder(placer: OrderPlacer, customerId: string, sku: string, qty: number): void {
  try {
    const order = placer.placeOrder(customerId, sku, qty);
    console.log(`order ${order.orderId} placed for ${order.customerId}`);
  } catch (err) {
    if (err instanceof InsufficientStockError) {
      console.log(`order rejected: ${err.message}`);
      return;
    }
    throw err;
  }
}

// Composition root: wiring lives at the edge, never inside the core.
const inventory = new InMemoryInventory({ "sku-1": 5 });
const orders = new InMemoryOrderRepository();
const service = new OrderService(inventory, orders);

cliPlaceOrder(service, "cust-1", "sku-1", 2);
cliPlaceOrder(service, "cust-2", "sku-1", 10);
```

Even here, where `OrderService` writes `implements OrderPlacer` explicitly,
`InMemoryInventory` and `InMemoryOrderRepository` would still satisfy their
respective ports without the `implements` keyword at all, because
TypeScript checks the shape, not the declaration. A test double built as a
plain object literal with a matching `reserve` method needs no class and no
`implements` clause to be accepted anywhere `InventoryPort` is expected.
