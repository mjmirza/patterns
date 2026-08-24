---
name: Clean Architecture
slug: clean-architecture
family: 05-architectural
category: Architectural
aliases: []
first_described: "Martin 2012"
maturity: canonical
related: [hexagonal-architecture, onion-architecture, layered-architecture, dependency-injection, repository, use-case]
incompatible_with: []
verified: 2026-08-02
---

# Clean Architecture

## 1. Name, aliases, and lineage

The canonical name is Clean Architecture, coined by Robert C. Martin, known
widely as Uncle Bob, in a blog post titled "The Clean Architecture," published
13 August 2012 and still hosted at blog.cleancoder.com
([Robert C. Martin, "The Clean Architecture," blog.cleancoder.com, published 13
August 2012](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html),
verified 2026-08-02). Martin later expanded the post into a full book, Robert C.
Martin, *Clean Architecture. A Craftsman's Guide to Software Structure and
Design*, Pearson, published 10 September 2017, ISBN 978-0134494166
(publication record confirmed via [Open Library, ISBN
9780134494166](https://openlibrary.org/isbn/9780134494166), verified
2026-08-02).

Unlike Layers, which carries a long list of true synonyms (N-Tier, Multitier,
N-Layer), Clean Architecture has no independently attested alternate name of
its own. What it does have is a family of prior architectures that Martin's
original post names explicitly as sharing the same objective before he wrote a
single word of the post. The post states that Hexagonal Architecture, also
called Ports and Adapters, DCI (Data, Context, Interaction), and BCE
(Boundary, Control, Entity) all achieve the same separation, and it draws the
same concentric-circle picture for all of them. The Ardalis Clean Architecture
template for ASP.NET Core, a widely adopted implementation of the pattern in
the .NET ecosystem, states this directly in its own README. "Clean Architecture
is just the latest in a series of names for the same loosely-coupled,
dependency-inverted architecture" ([ardalis/CleanArchitecture, GitHub
repository README](https://github.com/ardalis/CleanArchitecture), verified
2026-08-02). That sentence is not a claim Martin made about his own work being
derivative. It is a later author's honest framing of a lineage Martin himself
pointed at.

Two siblings deserve their own citation because this entry treats them as
related patterns, not as synonyms, in dimension 13. Alistair Cockburn
introduced Hexagonal Architecture, and renamed it Ports and Adapters in 2005,
to describe a system whose core talks to the outside world only through
exposed ports, with adapters translating between a port and a specific
technology on the other side of it
([Wikipedia, "Hexagonal architecture
(software)"](https://en.wikipedia.org/wiki/Hexagonal_architecture_(software)),
verified 2026-08-02). Jeffrey Palermo published "The Onion Architecture, Part
1" on 29 July 2008, describing a design where all code depends only on layers
more central than itself, with the domain model at the absolute center and
infrastructure, including the database, at the outside edge
([Jeffrey Palermo, "The Onion Architecture, Part
1," jeffreypalermo.com, 29 July
2008](https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/),
verified 2026-08-02). Clean Architecture, Hexagonal, and Onion each drew the
same underlying rule independently or semi-independently across roughly a
decade, and Martin's contribution in the 2012 post and the 2017 book was to
name the shared rule plainly, draw one canonical picture of it, and give the
four rings names that stuck across the industry. That underlying rule is a
direct application of the Dependency Inversion Principle, which Martin himself
had already formulated years earlier in "Object Oriented Design Quality
Metrics. an analysis of dependencies," October 1994, and restated in "The
Dependency Inversion Principle," C++ Report, June 1996, stating that high level
modules should not depend on low level modules and that both should depend on
abstractions ([Wikipedia, "Dependency inversion
principle,"](https://en.wikipedia.org/wiki/Dependency_inversion_principle),
verified 2026-08-02). Clean Architecture is the Dependency Inversion Principle
applied at the scale of an entire application's package structure rather than
at the scale of one class and its collaborator.

## 2. Problem and context

A non-trivial application accumulates business rules that answer questions no
framework, database, or user interface technology can answer for it. what
counts as a valid order, when a subscription is allowed to renew, how a
discount stacks with a coupon. Left unmanaged, those rules end up living inside
a web controller method, an ORM entity's setter, or a database trigger,
because those are the places code naturally gets written first and nobody
draws a boundary around them later.

The failure this produces is not visible on day one. It surfaces the first time
somebody tries to change something that should have been cheap. A team wants to
add a batch job that places orders without going through the web layer, and
discovers the order validation logic is inside an HTTP controller and cannot be
called any other way. A team wants to swap the ORM for a lighter data mapper,
and discovers the domain objects are the ORM's own entity classes, annotated
with framework attributes, so every business rule test needs a live database
connection to run. A team wants to write a unit test for a discount
calculation, and the only way to construct the object under test is through a
repository method that hits a real database. None of these are database
problems, UI problems, or framework problems by themselves. They are all the
same problem. business rules and delivery mechanisms were never separated, so
every change to one drags the other along with it.

Clean Architecture answers this by drawing a hard line, called the Dependency
Rule, between what a system knows on its own and what it merely talks to.
Business rules belong in the center, they know nothing about databases, web
frameworks, or message queues, and everything on the outside of that boundary
exists to serve the center rather than the reverse. The context in which this
line is worth drawing is a system expected to survive multiple framework
versions, multiple delivery mechanisms, or a database migration, and a system
whose business rules are worth testing in isolation from infrastructure. A
short-lived prototype, a single-purpose script, or a system with genuinely
trivial business logic does not have this problem badly enough to justify the
answer, which is the subject of dimension 4.

## 3. Forces

- **Coupling.** Favoured hardest. The stated objective, in Martin's own words,
  is a system independent of frameworks, independent of the user interface,
  independent of the database, and independent of any external agency, so that
  business rules can be tested and changed without touching any of them.
- **Testability.** Favoured. Testability is one of the five properties Martin's
  post names directly as the payoff of following the Dependency Rule. business
  rules can be exercised with plain objects and no test double for a database,
  a web server, or a queue.
- **Cognitive load and onboarding cost.** Sacrificed. A new engineer opening
  the codebase meets four rings, at least two interfaces for every meaningful
  operation, an input boundary and an output boundary, and a mapping step at
  every crossing. Finding where a single feature lives means walking through
  several files instead of one.
- **File and class count.** Sacrificed. A single CRUD operation that would be
  three methods in a thin controller becomes an entity, a use case interactor,
  an input boundary interface, an output boundary interface, a presenter, a
  view model, and a gateway implementation, seven artifacts for one operation.
- **Delivery mechanism flexibility.** Favoured. Because the use case layer
  depends on no delivery technology, the same interactor can be driven from a
  web controller, a CLI command, a message consumer, or a test driver with no
  change to the interactor itself.
- **Persistence flexibility.** Favoured, at a cost. The repository or gateway
  interface lives in the use case ring, so swapping a relational database for a
  document store means writing a new adapter behind an unchanged interface,
  but only if the interface was designed generically enough in the first
  place, which is a real design skill this pattern does not supply for free.
- **Latency and allocation.** Mildly sacrificed. Every crossing between rings
  is, by the pattern's own rule, a translation into a plain data structure,
  which means an extra allocation and an extra mapping step at every boundary
  a request crosses. In most business applications this cost is irrelevant
  next to a network call or a database round trip. In a tight, high-throughput
  hot path it is a real and measurable cost.
- **Team topology.** Favoured for large, long-lived systems with distinct
  ownership of business rules versus infrastructure, sacrificed for small
  teams where one person owns the whole vertical slice and the ring boundaries
  add process overhead with no corresponding organizational boundary to match.

No pattern gives up nothing. Clean Architecture buys independence from
delivery mechanisms and persistence technology, and the price is a larger
number of files, more indirection at every operation, and a real up front cost
in interface design that a thin, framework-coupled application never pays.

## 4. Applicability and non-applicability

Reach for Clean Architecture when the following hold.

- The system is expected to outlive the specific web framework, ORM, or UI
  technology it launches with, and a future framework or database migration is
  a real, planned possibility rather than a hypothetical one.
- Business rules are complex enough, and change often enough, that testing
  them without spinning up a database or an HTTP server has real value, and
  that value recurs across many test runs per day.
- More than one delivery mechanism needs to drive the same business logic, for
  example a REST API and a scheduled batch job and an admin CLI all placing
  the same kind of order.
- A team is large enough, or will grow large enough, that a hard seam between
  "people who own business rules" and "people who own infrastructure adapters"
  matches how the organization is actually structured, echoing Conway's Law.
- Long term maintainability is worth more than short term velocity, and the
  team accepts paying the interface design tax up front in exchange for a
  system whose core can be tested and changed without touching its edges.

Do NOT reach for Clean Architecture when any of the following hold. This list
is deliberately as long as the first one, because the failure to draw it
honestly is the single most common misuse of the pattern.

- The application is a short-lived script, a small internal tool, or a
  prototype whose business rules are simple enough that the framework and the
  business logic are never going to diverge in practice.
- The team is small, expects to stay small, and the person writing the web
  controller is the same person who would otherwise be writing the use case
  interactor and the gateway, so the ring boundary formalizes a distinction
  nobody in the room actually needs enforced.
- The business logic is genuinely thin, mostly a pass-through of user input
  into a database write with light validation, so the "independence from the
  database" payoff has nothing meaningful to protect.
- There is no realistic plan, ever, to change the delivery mechanism or the
  persistence technology, and the team is honest with itself that this is
  true rather than treating "someday we might" as a justification.
- The performance budget is tight enough that the extra allocation and
  mapping cost at every ring boundary is a measured, material problem, and no
  amount of care in interface design removes that cost, because the cost is
  structural to the pattern itself.
- The team has not yet internalized the Dependency Inversion Principle at the
  class level. Clean Architecture is that principle applied at a larger scale,
  and a team that fights it inside one class will produce a Clean
  Architecture skeleton with the Dependency Rule violated everywhere inside
  it, which is worse than a smaller, honestly coupled system, because it
  carries the file count of the pattern without any of its actual benefit.

## 5. Structure

Clean Architecture names four concentric rings, each depending only on the
ring inside it, never on the ring outside it. This ordering is drawn directly
from Martin's original post and restated in the book.

- **Entities.** The enterprise-wide business rules, the ones least likely to
  change because a delivery mechanism or a framework was swapped. An Entity in
  this sense is a plain object encapsulating the most general and
  high-level rules, and it can be, but does not have to be, a traditional
  object-oriented class with methods. It could equally be a set of data
  structures and functions.
- **Use Cases.** The application-specific business rules. This ring
  orchestrates the flow of data to and from the Entities, and directs those
  Entities to use their enterprise-wide business rules to achieve the goal of
  the use case. This ring also defines two kinds of interface, called
  boundaries. an input boundary that the outer ring calls to trigger the use
  case, and an output boundary that the use case calls to report a result,
  implemented by something outside this ring.
- **Interface Adapters.** A set of adapters that convert data from the format
  most convenient for the Use Cases and Entities into the format most
  convenient for an external agency such as a database or a web framework, and
  back. This is where Model-View-Controller style code lives. presenters,
  controllers, and gateway implementations that satisfy the persistence
  interfaces declared one ring inward.
- **Frameworks and Drivers.** The outermost ring, where all the detail lives.
  the web framework itself, the database driver, the dependency injection
  container's wiring code, and the composition root that constructs concrete
  objects and hands them to the inner rings through their interfaces. Very
  little code lives here beyond glue that connects the outside world to the
  interface adapters.

The Dependency Rule governs every relationship among these four rings. source
code dependencies can only point inward. A name declared in an outer ring must
never be mentioned by any code in an inner ring, including the name of a
function, a class, a variable, or any other named software entity. When an
inner ring needs to call outward, for example a use case reporting its result
to a presenter, the inner ring defines an interface and the outer ring
implements it, so the source code dependency still points inward even though
the runtime call flows outward. This is Dependency Inversion applied at the
ring boundary, and it is the single mechanical device that makes the whole
structure work.

## 6. ASCII structure diagram

```
              +-----------------------------------------------+
              | Frameworks and Drivers                        |
              |   web framework, ORM driver, DI container,     |
              |   composition root (main)                      |
              |  +-------------------------------------------+ |
              |  | Interface Adapters                         | |
              |  |   controllers, presenters, gateways         | |
              |  |  +---------------------------------------+  | |
              |  |  | Use Cases                              |  | |
              |  |  |   interactors, input/output boundaries |  | |
              |  |  |  +-----------------------------------+ |  | |
              |  |  |  | Entities                          | |  | |
              |  |  |  |   enterprise business rules       | |  | |
              |  |  |  +-----------------------------------+ |  | |
              |  |  +---------------------------------------+  | |
              |  +-------------------------------------------+ |
              +-----------------------------------------------+

  Source code dependencies point inward only, drawn left to right below.

  Frameworks and Drivers --> Interface Adapters --> Use Cases --> Entities
```

## 7. Dynamics

A request enters at the outermost ring and its data crosses inward through
each boundary as a plain data structure, never as a framework type and never
as an Entity or a database row passed by reference. Martin states this
constraint directly in the original post, writing "We don't want to cheat and
pass Entities or Database rows. We don't want the data structures to have any
kind of dependency that violates The Dependency Rule."

```
Web request arrives at a controller (Frameworks and Drivers / Interface Adapters)
  |
  v
Controller builds a plain request model, calls the Input Boundary (Use Cases)
  |
  v
Interactor (Use Cases) loads and mutates Entities through a Gateway interface
  it declares itself, implemented one ring outward by a concrete repository
  |
  v
Interactor calls the Output Boundary (Use Cases) with a plain result
  |
  v
Presenter (Interface Adapters), which implements the Output Boundary,
  formats a View Model for whatever delivery mechanism is in play
  |
  v
Frameworks and Drivers ring serializes the View Model to JSON, HTML,
  a CLI printout, or whatever the delivery mechanism requires
```

The interactor never imports the presenter's concrete type, and never imports
the concrete gateway's type. It is handed both through its constructor,
typed as the two interfaces it declared, by the composition root in the
outermost ring at startup. This is the mechanical reason a use case can be
unit tested with a fake gateway and a fake presenter and never touch a real
database or a real web server.

## 8. Implementation variants

- **Package by ring versus package by feature.** The literal, textbook variant
  organizes source folders by ring name, `entities/`, `usecases/`, `adapters/`,
  `frameworks/`, so the Dependency Rule is visible in the folder tree itself. A
  more common variant in practice organizes folders by feature, `orders/`,
  `billing/`, with each feature folder internally split into the same four
  rings. The second variant scales better as a codebase grows, because a
  reader working on one feature does not have to search four top level
  folders to find everything related to it, at the cost of the ring
  boundaries being less visually obvious from the folder tree alone.
- **Explicit boundary interfaces versus a single dependency container.** Some
  implementations declare an explicit input boundary interface for every use
  case, exactly as described in dimension 5. A common simplification skips
  the input boundary interface, since most languages let a controller call a
  concrete interactor class directly without genuinely needing a swappable
  implementation of "how a use case is triggered," and reserves the interface
  discipline for the output boundary and the persistence gateway, where
  swappability is the actual point.
- **Synchronous return versus output boundary callback.** Martin's original
  design has the interactor call an output boundary rather than returning a
  value, so the same interactor can drive a synchronous web response or an
  asynchronous notification without changing its own signature. A simpler,
  widely used variant has the interactor return a plain result object
  directly, and lets the calling controller decide how to present it. This
  trades some of the callback flexibility for a signature that reads more
  naturally in languages with strong return-value idioms.
- **CQRS split at the use case boundary.** Rather than one interactor per
  operation regardless of whether it reads or writes, a variant splits
  interactors into commands, which mutate Entities and return little, and
  queries, which read through a separate, often more direct, read path that
  may bypass the full Entity graph for performance. This variant composes
  with the Command Query Responsibility Segregation pattern rather than
  contradicting Clean Architecture, because the Dependency Rule still governs
  both the command and the query paths independently.
- **Language-idiomatic boundary shape.** In languages with first class
  functions, a boundary interface with one method is frequently replaced by a
  bare function type or a closure, which removes a class declaration without
  weakening the Dependency Rule, since a function type is still an
  abstraction the inner ring owns and the outer ring satisfies.

## 9. Known production uses

- **Ardalis Clean Architecture template for ASP.NET Core.** A GitHub template
  repository, maintained by Steve Smith (Ardalis) with backing from
  NimblePros, structured into a Core project, a UseCases project, an
  Infrastructure project, and a Web project, directly matching the four
  rings, and adopted widely enough to carry 18.4 thousand stars and 3.1
  thousand forks at time of verification ([ardalis/CleanArchitecture, GitHub
  repository](https://github.com/ardalis/CleanArchitecture), verified
  2026-08-02).
- **Microsoft eShopOnWeb reference application.** Microsoft's own ASP.NET Core
  reference architecture repository, tagged with the topic "clean-architecture"
  on GitHub alongside "ddd-architecture" and "clean-code," structured as a
  layered, single-process application separating a Core domain project from
  Infrastructure and a Web presentation project along the same lines the
  Ardalis template formalizes
  ([dotnet-architecture/eShopOnWeb, GitHub
  repository](https://github.com/dotnet-architecture/eShopOnWeb), verified
  2026-08-02).
- **Google's official Android app architecture guidance.** Google's own
  developer documentation for Android recommends a UI layer, an optional
  domain layer, and a data layer, and states plainly that the domain layer
  depends on data layer classes, establishing an inward-only dependency
  direction that matches the Dependency Rule at application scale, in
  guidance last updated 14 April 2026 ([Android Developers, "Guide to app
  architecture,"](https://developer.android.com/topic/architecture), verified
  2026-08-02). Google's own Now in Android sample application states in its
  README that it follows the official architecture guidance and structures
  its data layer components as interfaces bound to concrete implementations
  through dependency injection, the same inversion Clean Architecture relies
  on at its persistence boundary ([android/nowinandroid, GitHub
  repository](https://github.com/android/nowinandroid), verified 2026-08-02).

These three are independent implementations from different ecosystems, .NET
open source tooling, a Microsoft reference application, and Google's own
first party Android guidance, each arriving at the same inward-only
dependency shape either citing Clean Architecture by name or converging on it
without naming it, which is the same pattern of independent convergence
documented for the sibling architectures in dimension 1.

## 10. Consequences

**Positive.**

- Business rules can be unit tested with plain objects, no database
  connection, no HTTP server, and no test container, which shortens the
  feedback loop for the most valuable tests in the system.
- A framework, database, or UI technology migration touches the outer two
  rings and the adapters that satisfy the persistence interface, while the
  Entities and Use Cases rings are, by construction, untouched.
- The same use case can be driven from more than one delivery mechanism, a
  REST endpoint, a message consumer, a CLI command, with no duplication of
  business logic, because the delivery mechanisms differ only in how they
  build a request and present a result.
- The boundary between business rules and infrastructure is enforceable in
  code review and, with the right lint or architecture test tooling, in a
  build pipeline, rather than relying on developer discipline alone.
- New team members can be handed a single ring to work in, adapters or use
  cases, with a narrower surface of concepts to learn than the whole system
  at once.

**Negative.**

- The number of files and interfaces per operation grows substantially
  compared to a framework-coupled equivalent, and every one of them has to be
  written, named, and kept consistent.
- Every ring crossing is a mapping step, from a request model to a domain
  call, from a domain result to a view model, which is both an allocation
  cost and a place where a mapping bug can silently drop or mistranslate a
  field.
- The pattern gives no guidance on where a genuinely cross-cutting concern,
  such as authorization or a distributed transaction spanning two use cases,
  is supposed to live, and teams frequently improvise inconsistent answers to
  that question independently.
- A team that adopts the ring structure without genuinely internalizing the
  Dependency Rule produces a system with the appearance of Clean Architecture
  and none of its benefit, because a single import in the wrong direction,
  an Entity importing an ORM attribute, a use case importing a web framework
  type, silently reintroduces the exact coupling the rings exist to prevent.
- Onboarding cost is real and paid by every new engineer, because
  understanding where a feature lives requires understanding four rings and
  the interface at every crossing between them, before a single line of
  feature code can be written or found.

## 11. Failure modes and misuse

This dimension draws on engineering judgement built from the pattern's own
stated purpose and its widely documented misapplications, rather than a single
citable source for each symptom.

- **Symptom.** The codebase has entities, use cases, adapters, and gateways
  laid out in separate folders, but a use case interactor imports a concrete
  ORM entity class or a web framework's request type directly.
  **Cause.** The team copied the ring folder structure without enforcing the
  Dependency Rule as a real constraint, usually because nothing in the build
  checks import direction.
  **Fix.** Add an architecture test, using a tool such as ArchUnit for the
  JVM or a custom static check for other ecosystems, that fails the build
  when a file in an inner ring imports a type from an outer ring. Treat this
  test with the same seriousness as a compile error.

- **Symptom.** Every use case interactor takes an ever-growing constructor
  parameter list of ten or more collaborators, most of them unused by most
  callers of that interactor.
  **Cause.** The team is putting too much unrelated responsibility into one
  interactor instead of splitting it into several narrower use cases, often
  because the original design mirrored a single, large controller action
  rather than the actual business capabilities involved.
  **Fix.** Split the interactor along the actual use case boundaries the
  business describes, so each interactor's dependency list reflects only what
  that one operation genuinely needs.

- **Symptom.** A view model class defined in the Interface Adapters ring is
  reused, unmodified, as the return type of a use case interactor, because it
  was convenient and the two shapes happened to match at the time.
  **Cause.** Skipping the boundary crossing described in dimension 7 to save
  one mapping step, treating "it compiles" as sufficient evidence the
  boundary was respected.
  **Fix.** Keep the use case output type and the adapter's view model type
  as two distinct types even when their fields are identical today, because
  the moment a delivery mechanism needs a field the use case does not, or the
  use case needs to add an internal field the delivery mechanism should never
  see, the shared type has to be split under time pressure, which is a worse
  time to do it than up front.

- **Symptom.** Introducing Clean Architecture to a genuinely small
  application produces a pull request with forty new files and no new
  functionality, and the team's delivery velocity visibly drops for the
  following several sprints.
  **Cause.** The pattern was applied outside its applicability window,
  described in dimension 4, on a system whose business rules were never
  complex enough or long lived enough to justify the structural cost.
  **Fix.** Recognize this as a scoping mistake rather than an execution
  mistake, and consider collapsing back toward a simpler layered structure
  for the parts of the system that do not carry meaningful business logic,
  reserving the full ring structure for the parts that do.

- **Symptom.** A team reports that adding a single new field to a form takes
  a full day, touching an Entity, a use case input model, a use case output
  model, a presenter, a view model, and a database migration, for a field
  with no business rule attached to it at all.
  **Cause.** Every field, including purely presentational or purely
  persistence-only fields with zero business meaning, was routed through the
  full four ring structure regardless of whether it needed the protection
  that structure provides.
  **Fix.** Reserve the full boundary crossing discipline for fields that
  participate in an actual business rule, and allow simpler, more direct
  pass-through paths for fields that do not, rather than treating every
  field in the system as equally deserving of architectural ceremony.

## 12. Trade-off matrix

| Force | Clean Architecture | Layered Architecture | Hexagonal Architecture | Transaction Script |
|---|---|---|---|---|
| Framework independence | Strongest, an explicit stated goal | Weak, layers commonly reference framework types directly | Strong, ports isolate the core the same way | None, business logic is inline in the delivery handler |
| Testability of business rules | High, plain objects, no infrastructure needed | Moderate, depends on how strictly layers are respected | High, same mechanism as Clean Architecture, fewer named rings | Low, tests usually exercise the whole handler |
| File and class count per operation | Highest of the four | Moderate | Moderate to high, similar to Clean Architecture | Lowest |
| Learning curve for new team members | Steep, four rings plus boundary interfaces | Gentle, three familiar layers | Steep, ports and adapters terminology, fewer named rings than Clean Architecture | Gentle, one file to read per operation |
| Best fit team size and lifespan | Large, long lived systems | Small to large, any lifespan | Large, long lived systems, especially with multiple delivery mechanisms | Small teams, short lived or simple systems |
| Explicit named ring for enterprise-wide rules | Yes, the Entities ring | No, business rules typically sit in a single service or domain layer | No, the core is undivided, called the domain or application core | No |

## 13. Related and incompatible patterns

Clean Architecture composes with, rather than competes against, several other
patterns named elsewhere in this catalog.

- **Hexagonal Architecture.** A close sibling rather than a competitor. both
  enforce the same inward dependency rule, and the Interface Adapters ring in
  Clean Architecture plays the same role as an adapter in Hexagonal
  Architecture, translating between a port's interface and a specific outside
  technology. Teams frequently borrow Hexagonal's port and adapter
  vocabulary while drawing Clean Architecture's four named rings, and the two
  are commonly treated as interchangeable in practice, a conflation Martin's
  own post invites by listing Hexagonal as one of the architectures pursuing
  the identical objective.
- **Onion Architecture.** Another close sibling, with the same inward only
  dependency rule and the domain model at the exact center. Onion
  Architecture does not name a separate Use Cases ring the way Clean
  Architecture does, folding application-specific orchestration into what it
  calls Domain Services or Application Services layers, so Clean
  Architecture can be read as Onion Architecture with the orchestration
  responsibility pulled out into its own explicitly named ring.
- **Layered Architecture.** The direct structural ancestor. every ring in
  Clean Architecture is a layer in the Layered Architecture sense, related by
  strict dependency direction. Clean Architecture differs from a generic
  layered system by naming exactly four layers with specific responsibilities
  and by insisting the Dependency Rule is enforced through interfaces at
  every crossing, not merely by convention.
- **Repository.** The standard implementation of the Use Cases ring's
  persistence port. an interface declared inside the Use Cases ring,
  implemented by a concrete gateway in the Interface Adapters or Frameworks
  and Drivers ring. Clean Architecture depends on the Repository pattern, or
  something functionally equivalent to it, to keep persistence detail out of
  the inner two rings.
- **Dependency Injection.** The mechanical delivery vehicle for the
  Dependency Rule at runtime. because an inner ring must never construct a
  concrete outer ring object directly, something outside every ring, the
  composition root, has to build the object graph and hand concrete
  implementations to interfaces the inner rings declared. Clean Architecture
  without dependency injection, in some form, whether a container or plain
  manual constructor wiring, is not really Clean Architecture.
- **Command Query Responsibility Segregation.** A compatible, orthogonal
  split, described in dimension 8, that partitions use case interactors along
  the read versus write axis rather than replacing the ring structure.
- **Transaction Script.** The pattern Clean Architecture is most often chosen
  instead of, and the pattern this entry names as the correct alternative
  when the applicability list in dimension 4 favours simplicity over
  independence. The two are not compatible within the same operation, since
  Transaction Script deliberately collapses the rings Clean Architecture
  insists on keeping separate.

## 14. Refactoring path in and out

Introducing Clean Architecture into a codebase that does not have it is a
sequence of extractions, not a rewrite, and each step should leave the system
working.

1. Identify one business rule currently embedded directly inside a controller,
   a handler, or a database entity's method, and extract it into a plain
   object with no framework or persistence dependency. This is the first
   Entity.
2. Extract the orchestration logic around that rule, the part that loads
   data, calls the rule, and decides what happens next, into a single class
   or function with a narrow, explicit input and output. This is the first
   use case interactor, even before any interface exists around it.
3. Define an interface for whatever the interactor currently calls directly
   to load or save data, and change the interactor to depend on that
   interface rather than the concrete database call. Write one concrete
   implementation of the interface that simply wraps the existing database
   code. Nothing about the runtime behaviour changes at this step, only the
   direction of the source dependency.
4. Define an output interface for however the interactor currently returns or
   reports its result, and move the original controller or handler code that
   consumed that result into an implementation of the new interface. The
   original controller now becomes a thin adapter that constructs the
   interactor, calls it, and lets the new presenter format the answer.
5. Repeat steps one through four for the next business rule, letting the
   Entities and Use Cases rings grow one extraction at a time rather than
   attempting to draw the full ring structure across the whole codebase in a
   single change.
6. Once several use cases exist, extract a genuine composition root, a single
   place, at the very edge of the Frameworks and Drivers ring, responsible
   for constructing every concrete gateway and presenter and wiring them into
   interactors. Before this step, wiring is usually scattered across
   individual controllers.

Removing Clean Architecture, when the applicability list in dimension 4 no
longer favours it, for example after a large system is broken into small,
single-purpose services, follows the reverse path. collapse a use case
interactor and its single presenter back into the controller that calls it
when there is genuinely only one delivery mechanism left and no plan to add
another, then inline the gateway interface's single implementation directly
into the interactor once no second implementation of it has existed for a
long time. The Entities ring is the layer most worth preserving even when the
rest of the structure is collapsed, because the business rules it holds
remain valuable independent of how many rings surround them.

## 15. Testing and verification

The property Clean Architecture is built to deliver is that the Entities and
Use Cases rings can be tested with plain objects, so the corresponding tests
should never need a database connection, an HTTP client, or a running web
server to pass.

- **Entities.** Test with direct construction and plain assertions, no test
  double needed for anything, since an Entity by definition depends on
  nothing outside itself.
- **Use case interactors.** Test with a hand written or generated fake
  implementation of every port the interactor depends on. a fake repository
  backed by an in-memory map, and a fake output boundary that simply records
  what it was called with, so the assertion checks the exact result the
  interactor reported rather than a side effect several rings away.
- **Presenters.** Test in isolation by calling the presenter's method
  directly with plain values and asserting on the resulting view model,
  without ever constructing a real interactor.
- **Gateways.** Test against a real or a realistic in-process database, for
  example an in-memory or containerized instance of the actual database
  technology, since a gateway's entire job is to correctly translate to and
  from that real technology, and a fake here would only be testing the fake.
- **Architecture tests.** A distinct and often skipped test category that
  verifies the Dependency Rule itself. a static check, run as part of the
  build, that fails when a file in the Entities or Use Cases ring imports
  from the Interface Adapters or Frameworks and Drivers ring. Without this
  category of test, every other test passing gives no signal about whether
  the Dependency Rule is actually being respected, only that the code
  currently compiles and behaves as written, violations included.
- **Controllers and end to end paths.** Reserve a smaller number of broader
  tests that exercise a real request through the full stack, controller
  through interactor through a real gateway, to catch wiring mistakes at the
  composition root that no isolated unit test can see, since the composition
  root itself is the one piece of the system with no smaller unit to test in
  isolation.

## 16. Observability signals

Clean Architecture is a source-level, compile-time structure, so it produces
few runtime signals of its own, but the ring boundaries are a natural place to
attach tracing and logging, and their absence is itself diagnostic.

- Emit a trace span, or a structured log entry, at the input boundary of
  every use case interactor, tagged with the use case name and a correlation
  identifier, so a single request's path through the system is visible even
  though it now crosses several object boundaries instead of executing
  inline in one handler.
- Emit a second span or log entry at the gateway, tagged with which concrete
  persistence technology handled the call, so an operator can see how much of
  a request's latency belongs to the use case's own logic versus the
  persistence adapter underneath it.
- A healthy system shows most latency concentrated in the gateway span, since
  that is where real I/O happens, with the interactor's own logic contributing
  a small, stable fraction of total time across requests.
- A failing or degrading system often shows the opposite. rising latency
  inside the interactor span itself, which usually means a business rule
  started doing work it should not be doing directly, for example iterating
  a large in-memory collection that should have been filtered by the gateway
  before the data ever reached the use case ring.
- Because a use case never constructs its own gateway or presenter, a missing
  or misconfigured dependency shows up loudly at the composition root, at
  startup, as a construction failure, rather than quietly at request time
  deep inside business logic. Treat a composition root startup failure as a
  configuration or wiring problem to fix immediately, never as something to
  work around inside a use case.

## 17. Security and privacy implications

Clean Architecture is largely neutral on security, but two implications
follow directly from where it puts logic.

- **Authorization placement is genuinely ambiguous and needs an explicit team
  decision.** The pattern gives no ring a clear mandate for deciding whether
  an actor is allowed to perform an operation. Some implementations put the
  check inside the use case interactor, treating it as a business rule,
  which keeps it testable with the rest of the use case but means every
  interactor has to remember to perform it. Others put it in the controller,
  at the Interface Adapters ring, before the use case is even invoked, which
  centralizes the check but means the use case has no guarantee it will
  never be called with an unauthorized actor if a second delivery mechanism
  forgets to perform the same check. Whichever ring a team picks, the
  decision should be written down and enforced consistently, since silent
  disagreement between different features about which ring owns
  authorization is a realistic path to an authorization bypass.
- **Sensitive data is easier to keep out of logs and outer layers precisely
  because it must cross an explicit boundary.** Since every ring crossing
  requires deliberately constructing a plain data structure rather than
  passing an Entity by reference, a team gets a natural, code-visible
  checkpoint at which to decide whether a sensitive field, for example a
  password hash or a full payment card number, is copied into the outward
  facing view model at all. A system without this boundary discipline more
  easily leaks a sensitive Entity field into a log statement or an API
  response simply because the whole object was in scope and convenient to
  serialize. This is a structural affordance the pattern provides, not a
  guarantee. a team can still choose to copy a sensitive field across the
  boundary carelessly, and the pattern does nothing on its own to stop that
  choice.

## 18. References

1. Robert C. Martin, "The Clean Architecture," blog.cleancoder.com, published
   13 August 2012, https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html, verified 2026-08-02.
2. Robert C. Martin, *Clean Architecture. A Craftsman's Guide to Software
   Structure and Design*, Pearson, published 10 September 2017, ISBN
   978-0134494166, publication record confirmed via Open Library,
   https://openlibrary.org/isbn/9780134494166, verified 2026-08-02.
3. Alistair Cockburn's Hexagonal Architecture, also called Ports and
   Adapters, renamed 2005, summarized in Wikipedia, "Hexagonal architecture
   (software)," https://en.wikipedia.org/wiki/Hexagonal_architecture_(software), verified 2026-08-02.
4. Jeffrey Palermo, "The Onion Architecture, Part 1," jeffreypalermo.com,
   published 29 July 2008, https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/, verified 2026-08-02.
5. Robert C. Martin's formulation of the Dependency Inversion Principle,
   "Object Oriented Design Quality Metrics. an analysis of dependencies,"
   October 1994, and "The Dependency Inversion Principle," C++ Report, June
   1996, summarized in Wikipedia, "Dependency inversion principle,"
   https://en.wikipedia.org/wiki/Dependency_inversion_principle, verified
   2026-08-02.
6. ardalis/CleanArchitecture, GitHub repository README,
   https://github.com/ardalis/CleanArchitecture, verified 2026-08-02.
7. dotnet-architecture/eShopOnWeb, GitHub repository,
   https://github.com/dotnet-architecture/eShopOnWeb, verified 2026-08-02.
8. Android Developers, "Guide to app architecture," last updated 14 April
   2026, https://developer.android.com/topic/architecture, verified
   2026-08-02.
9. android/nowinandroid, GitHub repository,
   https://github.com/android/nowinandroid, verified 2026-08-02.

## Code examples

Each example implements the same small scenario, placing an order with a
maximum item count enforced as a business rule, laid out through all four
rings, entities first, then the use case and its two boundaries, then the
interface adapters, then a composition root in the frameworks and drivers
ring. All three were compiled or run directly.

### TypeScript

```typescript
// Entities: enterprise business rules, no dependency on anything outer.
class Order {
  private readonly items: string[] = [];
  constructor(private readonly maxItems: number = 10) {}

  addItem(sku: string): void {
    if (this.items.length >= this.maxItems) {
      throw new Error(`order cannot exceed ${this.maxItems} items`);
    }
    this.items.push(sku);
  }

  itemCount(): number {
    return this.items.length;
  }
}

// Use Cases ring: input boundary, output boundary, the interactor.
// The interactor depends only on interfaces declared in this same file.
interface OrderRepository {
  save(order: Order): string;
}

interface PlaceOrderOutputBoundary {
  present(orderId: string, itemCount: number): void;
}

interface PlaceOrderInputBoundary {
  execute(skus: string[]): void;
}

class PlaceOrderUseCase implements PlaceOrderInputBoundary {
  constructor(
    private readonly repository: OrderRepository,
    private readonly output: PlaceOrderOutputBoundary
  ) {}

  execute(skus: string[]): void {
    const order = new Order();
    for (const sku of skus) {
      order.addItem(sku);
    }
    const orderId = this.repository.save(order);
    this.output.present(orderId, order.itemCount());
  }
}

// Interface Adapters ring: a presenter and a gateway, each implementing
// a Use Cases port. Neither the entity nor the interactor knows these
// concrete types exist.
interface OrderViewModel {
  orderId: string;
  itemCount: number;
}

class OrderPresenter implements PlaceOrderOutputBoundary {
  public viewModel: OrderViewModel | null = null;

  present(orderId: string, itemCount: number): void {
    this.viewModel = { orderId, itemCount };
  }
}

class InMemoryOrderGateway implements OrderRepository {
  private counter = 0;
  private readonly rows = new Map<string, Order>();

  save(order: Order): string {
    this.counter += 1;
    const id = `order-${this.counter}`;
    this.rows.set(id, order);
    return id;
  }
}

// Frameworks and Drivers ring: the composition root. The only place
// allowed to import every concrete type from every inner ring at once.
function main(): void {
  const gateway = new InMemoryOrderGateway();
  const presenter = new OrderPresenter();
  const useCase = new PlaceOrderUseCase(gateway, presenter);
  useCase.execute(["sku-1", "sku-2"]);
  console.log(presenter.viewModel);
}

main();
```

### Python

```python
"""Entities ring first, then Use Cases, then Interface Adapters,
then Frameworks and Drivers, in strict dependency order top to bottom."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


class Order:
    def __init__(self, max_items: int = 10) -> None:
        self._max_items = max_items
        self._items: list[str] = []

    def add_item(self, sku: str) -> None:
        if len(self._items) >= self._max_items:
            raise ValueError(f"order cannot exceed {self._max_items} items")
        self._items.append(sku)

    def item_count(self) -> int:
        return len(self._items)


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> str: ...


class PlaceOrderOutputBoundary(ABC):
    @abstractmethod
    def present(self, order_id: str, item_count: int) -> None: ...


class PlaceOrderInputBoundary(ABC):
    @abstractmethod
    def execute(self, skus: list[str]) -> None: ...


class PlaceOrderUseCase(PlaceOrderInputBoundary):
    def __init__(
        self, repository: OrderRepository, output: PlaceOrderOutputBoundary
    ) -> None:
        self._repository = repository
        self._output = output

    def execute(self, skus: list[str]) -> None:
        order = Order()
        for sku in skus:
            order.add_item(sku)
        order_id = self._repository.save(order)
        self._output.present(order_id, order.item_count())


@dataclass
class OrderViewModel:
    order_id: str
    item_count: int


class OrderPresenter(PlaceOrderOutputBoundary):
    view_model: OrderViewModel | None = None

    def present(self, order_id: str, item_count: int) -> None:
        self.view_model = OrderViewModel(order_id, item_count)


class InMemoryOrderGateway(OrderRepository):
    def __init__(self) -> None:
        self._counter = 0
        self._rows: dict[str, Order] = {}

    def save(self, order: Order) -> str:
        self._counter += 1
        order_id = f"order-{self._counter}"
        self._rows[order_id] = order
        return order_id


def main() -> None:
    gateway = InMemoryOrderGateway()
    presenter = OrderPresenter()
    use_case = PlaceOrderUseCase(gateway, presenter)
    use_case.execute(["sku-1", "sku-2"])
    print(presenter.view_model)


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import "fmt"

// Entities ring. Nothing in this block imports outward.
type Order struct {
	maxItems int
	items    []string
}

func NewOrder() *Order {
	return &Order{maxItems: 10}
}

func (o *Order) AddItem(sku string) error {
	if len(o.items) >= o.maxItems {
		return fmt.Errorf("order cannot exceed %d items", o.maxItems)
	}
	o.items = append(o.items, sku)
	return nil
}

func (o *Order) ItemCount() int {
	return len(o.items)
}

// Use Cases ring. Two ports and one interactor, depending only on the
// Order entity above and on each other's interfaces.
type OrderRepository interface {
	Save(order *Order) string
}

type PlaceOrderOutputBoundary interface {
	Present(orderID string, itemCount int)
}

type PlaceOrderUseCase struct {
	repository OrderRepository
	output     PlaceOrderOutputBoundary
}

func NewPlaceOrderUseCase(r OrderRepository, o PlaceOrderOutputBoundary) *PlaceOrderUseCase {
	return &PlaceOrderUseCase{repository: r, output: o}
}

func (uc *PlaceOrderUseCase) Execute(skus []string) error {
	order := NewOrder()
	for _, sku := range skus {
		if err := order.AddItem(sku); err != nil {
			return err
		}
	}
	orderID := uc.repository.Save(order)
	uc.output.Present(orderID, order.ItemCount())
	return nil
}

// Interface Adapters ring. Each type here implements a Use Cases port.
type OrderViewModel struct {
	OrderID   string
	ItemCount int
}

type OrderPresenter struct {
	ViewModel *OrderViewModel
}

func (p *OrderPresenter) Present(orderID string, itemCount int) {
	p.ViewModel = &OrderViewModel{OrderID: orderID, ItemCount: itemCount}
}

type InMemoryOrderGateway struct {
	counter int
	rows    map[string]*Order
}

func NewInMemoryOrderGateway() *InMemoryOrderGateway {
	return &InMemoryOrderGateway{rows: make(map[string]*Order)}
}

func (g *InMemoryOrderGateway) Save(order *Order) string {
	g.counter++
	id := fmt.Sprintf("order-%d", g.counter)
	g.rows[id] = order
	return id
}

// Frameworks and Drivers ring. The composition root, the only place
// that imports every concrete type from every inner ring at once.
func main() {
	gateway := NewInMemoryOrderGateway()
	presenter := &OrderPresenter{}
	useCase := NewPlaceOrderUseCase(gateway, presenter)
	if err := useCase.Execute([]string{"sku-1", "sku-2"}); err != nil {
		panic(err)
	}
	fmt.Printf("%+v\n", *presenter.ViewModel)
}
```
