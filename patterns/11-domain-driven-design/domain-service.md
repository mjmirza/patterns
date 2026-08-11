---
name: Domain Service
slug: domain-service
family: 11-domain-driven-design
category: Domain-Driven Design
aliases: [Service Object, Stateless Domain Operation]
first_described: "Evans 2003"
maturity: canonical
related: [aggregate, repository, factory, application-service, strategy, specification]
incompatible_with: []
verified: 2026-08-02
---

# Domain Service

## 1. Name, aliases, and lineage

The canonical name is Domain Service. Eric Evans introduced it as one of the
building blocks of Domain-Driven Design in *Domain-Driven Design. Tackling
Complexity in the Heart of Software*, Addison-Wesley, 2003, chapter 5,
"A Model Expressed in Software," section "Services." Evans states plainly that
some domain concepts are not natural to model as things and that forcing them
into an Entity or a Value Object produces a distorted model. The book's
definition of a Service holds three properties. the operation refers to a
domain concept that is not a natural part of an Entity or Value Object, the
interface is defined in terms of other elements of the domain model, and the
operation is stateless (Evans 2003, chapter 5, page 106 in the first
Addison-Wesley printing).

Evans distinguishes three layers of Service in the same chapter, and the
distinction is the single most important thing to get right when naming this
pattern in a codebase.

Domain Service. A stateless operation expressed in the ubiquitous language of
the domain, coordinating one or more Entities, Value Objects, Aggregates, or
Repositories to answer a question or perform a calculation that does not
belong to any single one of them. A funds transfer between two Account
aggregates is Evans's own example, because the transfer is not a property of
either account alone (Evans 2003, chapter 5, "Services", page 105).

Application Service. Sits above the domain layer, orchestrates a use case,
talks to Repositories and the outside world (a database transaction, a
message bus, an authentication check), and contains no business rule of its
own. Vaughn Vernon separates this explicitly from Domain Service in
*Implementing Domain-Driven Design*, Addison-Wesley, 2013, chapter 14,
"Application," where he states the Application Service's job is to
"orchestrate tasks" and delegate all business logic downward
(Vernon 2013, chapter 14, page 583).

Infrastructure Service. A technical capability, an email sender, a payment
gateway adapter, a clock, exposed through a domain-defined interface so the
domain layer can depend on the abstraction rather than the concrete
technology (Evans 2003, chapter 5, page 107, "Services and the Isolated
Domain Layer").

The alias Service Object is common in Ruby and Rails communities, where it
frequently names something closer to an Application Service, a callable
object that wraps one controller action's worth of orchestration
(confirmed by cross-reading the Rails community's own usage on
[the RailsGuides Active Record Callbacks page's cautionary note about
extracting complex logic into "plain old Ruby objects"](https://guides.rubyonrails.org/active_record_callbacks.html),
verified 2026-08-02, which does not use the term Domain Service but describes
the same extraction pressure that produces one). The naming looseness across
communities is real and is addressed directly in dimension 4 below.

## 2. Problem and context

A team modeling a domain in an object-oriented style eventually meets an
operation that genuinely spans more than one object and does not belong to
either. A transfer moves money out of one account and into another. A pricing
engine combines a product, a customer's tier, a currently active promotion,
and today's date to produce a price. A route planner takes two addresses and
a fleet of vehicles and returns an assignment. None of these operations is a
property of a single Entity, and forcing one in produces a familiar smell.
either the Entity grows a method that reaches out and mutates a second Entity
it should not know about, tightening coupling between aggregates that DDD
otherwise wants kept apart, or the operation lands in a controller or a
transaction script, where the business rule quietly leaves the domain layer
and the ubiquitous language stops describing what the code does.

This happens most often at the seam between two Aggregates, because an
Aggregate's consistency boundary is deliberately narrow (Evans 2003, chapter
6, "Aggregates"), and a rule that spans two boundaries has, by definition, no
single home. It also happens when the operation genuinely needs a stateless
calculation, a currency conversion, a tax rule, a shipping-cost formula, that
reads from several objects but owns no state of its own and would be an odd
fit as a method on any one of them.

The context that makes Domain Service the right answer, rather than a
symptom of a modeling failure, is one where the team has already tried
placing the behavior on an Entity or Value Object and found that doing so
either requires one object to depend on a type it should not know about, or
smears one cohesive business concept across two classes so that no single
class expresses it. The domain concept itself is a verb, not a noun, an
operation the domain performs rather than a thing the domain contains.

## 3. Forces

**Where does behavior belong versus where is state owned.** An Entity that
gains a method for every cross-cutting concern accretes responsibilities it
was never meant to hold, which is the drift toward a God Object. A Domain
Service that absorbs every stray method becomes a dumping ground with no
cohesion of its own, which is the opposite failure, the Anemic Domain Model,
where the Entities are bags of getters and setters and all logic lives
outside them (Martin Fowler names this failure directly, describing a design
where services hold all the behavior while the domain objects hold only
state and have almost no real business logic left, see
[Martin Fowler, "AnemicDomainModel," martinfowler.com bliki, 25 November
2003](https://martinfowler.com/bliki/AnemicDomainModel.html), verified
2026-08-02). Domain Service resolves this only when it is reserved for the
narrow class of operations that truly have no single-object home, and is not
a general escape valve for placing logic somewhere convenient.

**Statelessness versus convenience.** A Domain Service that starts holding a
field to cache a lookup, remember the last customer it priced, or accumulate
a batch, is drifting toward being an Entity in disguise, and its lifecycle
and identity questions (who owns it, is it thread-safe, does one instance
serve one request or the whole process) become the same questions an Entity
answers explicitly. Evans's stateless requirement is a real constraint that
keeps this pattern simple, not a stylistic preference.

**Coupling between Aggregates versus a single source of truth for a rule.**
Domain Service is frequently the mechanism DDD recommends specifically so
that two Aggregates do not hold direct references to each other and do not
each implement half of a shared rule. The cost is a third participant that
both Aggregates, and every caller, must know about, more moving pieces than
a single Entity method, traded for a boundary that keeps the two Aggregates
independently consistent (Evans 2003, chapter 6, "Aggregates," combined with
chapter 5's Services discussion).

**Discoverability versus honesty about coordination.** Placing a rule inside
an Entity method makes it discoverable from the Entity, which many
developers expect. Placing it in a Domain Service makes the coordination
explicit and testable in isolation, at the cost of one more place to look
when reading the code. Vernon argues for reaching for the Entity or Value
Object first and choosing a Domain Service only once that option is
genuinely exhausted, favouring discoverability on the object unless the
operation truly does not fit there (Vernon 2013, chapter 5, "Entities," and
chapter 7, "Services," pages 111 and 231).

## 4. Applicability and non-applicability

Reach for a Domain Service when all of the following hold.

- The operation is a real domain concept, nameable in the ubiquitous
  language with a verb a domain expert would recognize, such as "transfer
  funds," "calculate shipping cost," or "assign driver to route."
- The operation genuinely spans more than one Aggregate, Entity, or Value
  Object, and no single one of them is the natural owner.
- The operation is stateless, computing a result or coordinating a change
  from its inputs without needing to remember anything between calls.
- The operation would otherwise force one Aggregate to depend directly on
  another Aggregate's internals, breaking the intended isolation between
  Aggregate boundaries.
- The team can name the Service in the ubiquitous language, not as a
  technical noun like "Manager," "Helper," or "Processor." Evans is explicit
  that Services should be named from the domain, not from implementation
  concerns (Evans 2003, chapter 5, "Services," page 106, discussing naming
  discipline).

Do NOT reach for a Domain Service in these cases, and the reason each one is
a rejection is as important as the applicability list above.

- The behavior belongs naturally to a single Entity or Value Object.
  Extracting it into a Service anyway is the direct path to the Anemic
  Domain Model, where the Entity becomes a data holder and every rule about
  it lives somewhere else, defeating the point of an object model
  (Fowler, martinfowler.com, "AnemicDomainModel," verified 2026-08-02).
- The operation is really orchestration, opening a database transaction,
  calling two Repositories in sequence, publishing an integration event,
  checking an authorization policy, none of which is itself a business
  rule. That belongs in an Application Service, one layer up, and mixing
  the two collapses a useful architectural seam (Vernon 2013, chapter 14,
  "Application," page 583).
- The operation is really infrastructure, sending an email, calling a
  payment gateway, reading the system clock. If the domain layer needs the
  capability, define an interface for it in the domain layer and let
  infrastructure implement it. calling the concrete infrastructure code a
  Domain Service merely because it is stateless is a category error (Evans
  2003, chapter 5, "Services and the Isolated Domain Layer," page 107).
- The operation needs to remember state across calls, own an identity, or
  be looked up and reconstituted from storage. that is an Entity or an
  Aggregate, not a Service, however convenient a stateless-sounding facade
  might seem.
- The rule is a validation or matching predicate over a single object or
  a collection, best expressed as a composable boolean, such as "is this
  order eligible for free shipping." Evans introduced the Specification
  pattern for exactly this shape in the same book, and forcing predicate
  logic into a Domain Service loses the composability a Specification gives
  (Evans 2003, chapter 9, "Making Implicit Concepts Explicit," Specification
  section, page 224).
- The team cannot name it in the ubiquitous language and instead reaches
  for a generic technical suffix. "OrderManager," "UserProcessor," and
  "DataHelper" are the classic tell that a class is a dumping ground rather
  than a modeled domain concept.

## 5. Structure

**Domain Service.** A stateless class, module, or function that exposes one
or a small cohesive set of operations named in the ubiquitous language. It
takes domain objects, Entities, Value Objects, or Aggregate roots, as
parameters, or is given a narrow domain-defined interface to fetch them, and
returns a domain-defined result, a new Value Object, a mutated Entity, or a
decision.

**Collaborating Aggregates or Entities.** The objects the Domain Service
coordinates. They keep their own invariants and do not know about the
Service, and the dependency points from the Service to them, never the
reverse. This one-directional dependency is what keeps the Aggregates
independently testable and independently deployable in a modular or
microservice split.

**Domain-defined Repository interface (optional participant).** When the
Domain Service needs to look up objects it was not handed directly, for
example a pricing service that must look up the currently active
Promotion, it depends on a Repository interface defined in the domain
layer, never on a concrete data-access implementation (Evans 2003, chapter
6, "Repositories," combined with the Isolated Domain Layer discussion in
chapter 5).

**Calling Application Service or use case handler.** The layer above that
invokes the Domain Service as one step inside a larger use case, wraps the
call in a transaction if one is needed, and translates the result into a
response, an event, or a persistence call. The Application Service owns the
transaction boundary. the Domain Service does not.

## 6. ASCII structure diagram

```
+-------------------------------+
|      Application Service       |
|  (use case orchestration,      |
|   transaction boundary)        |
+---------------+-----------------+
                |
                | calls
                v
+-------------------------------------------+
|             Domain Service                 |
|  TransferService.transfer(from, to, amt)   |
|  - stateless                                |
|  - named in ubiquitous language             |
+---------+----------------------+-----------+
          |                      |
          | reads/mutates        | reads/mutates
          v                      v
+------------------+     +------------------+
|  Account (Agg A)  |     |  Account (Agg B)  |
|  - balance         |     |  - balance         |
|  - withdraw()      |     |  - deposit()       |
|  - invariant:      |     |  - invariant:      |
|    balance >= 0    |     |    balance >= 0    |
+------------------+     +------------------+
          ^
          | looked up via
          |
+------------------------+
|  AccountRepository       |   (domain-defined
|  (interface)              |    interface,
+------------------------+    infra implements)
```

## 7. Dynamics

```
Client (Application Service)
   |
   | 1. transferService.transfer(fromId, toId, amount)
   v
Domain Service
   |
   | 2. account = accountRepository.findById(fromId)
   v
AccountRepository -----> loads Account (Aggregate A)
   |
   | 3. account.withdraw(amount)   [enforces A's own invariant]
   v
Account (A)  -- raises DomainError if insufficient funds, stops here

   | 4. toAccount = accountRepository.findById(toId)
   v
AccountRepository -----> loads Account (Aggregate B)
   |
   | 5. toAccount.deposit(amount)  [enforces B's own invariant]
   v
Account (B)

   | 6. accountRepository.save(account); accountRepository.save(toAccount)
   v
Domain Service returns TransferResult (a Value Object)
   |
   v
Application Service commits the transaction, publishes FundsTransferred event
```

The critical property visible in this flow. the Domain Service never reaches
directly into either Account's internal state. it calls public methods that
each Account exposes and that each Account uses to protect its own
invariant. The Service coordinates the sequence and the cross-cutting rule
("both sides must succeed or the transfer did not happen"), the Aggregates
still own their own consistency rules ("balance cannot go negative"). This
division is the entire point of the pattern, not an implementation detail.

## 8. Implementation variants

**Class with instance methods, dependency-injected collaborators.** The
mainstream Java, C#, and Kotlin shape. a class implementing a
`TransferService` interface, constructed with an `AccountRepository`
dependency, registered in a DI container, and injected into the calling
Application Service. This is the shape Vernon demonstrates throughout
*Implementing Domain-Driven Design* (Vernon 2013, chapter 7, "Services").

**Static or module-level function, no class at all.** In Go and in much
functional-leaning TypeScript, a Domain Service is frequently a plain
function or a small set of functions in a package, taking the collaborating
objects and any needed Repository as explicit parameters. There is no
instance to construct because there is no state to hold, which is a direct
consequence of Evans's statelessness requirement, the language simply makes
the absence of state visible in the absence of a class.

**Domain event-driven variant.** Instead of directly mutating a second
Aggregate, the Domain Service raises a domain event after the first
Aggregate's change succeeds, and a second handler, in the same process or
across a service boundary, reacts by mutating the second Aggregate. This
trades synchronous consistency for eventual consistency and is common in a
microservice split, where the two Aggregates live in different services and
cannot share a transaction. The Domain Service's role narrows to validating
the operation and emitting the event, the coordination itself moves to an
event choreography (this shape is described generally in the eventual
consistency discussion of DDD-in-microservices architecture guidance, see
[Microsoft, ".NET Microservices. Architecture for Containerized .NET
Applications," "Microservice Domain Model,"
learn.microsoft.com](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-domain-model),
verified 2026-08-02).

**Double dispatch variant.** In languages with strong static typing and a
desire to keep the Domain Service thin, some teams implement the Service as
a thin dispatcher that calls a method on one participant, passing the other
participant as an argument, so the actual rule still lives partly on the
Entity, "account.transferTo(otherAccount, amount)", with the Service
existing mainly to look up the two Accounts and wrap the call in error
handling. This blurs the line toward an Entity method and is defensible
only when the two Aggregates are of the same type and the rule is
genuinely symmetric, otherwise it tends to smuggle logic back into a single
Entity that should not own it, undermining the reason the Service was
introduced.

**Specification-composed variant.** A pricing or eligibility Domain Service
composes one or more Specification objects internally to decide the answer,
keeping each predicate independently testable and reusable while the
Service supplies the orchestration and stateless calculation shell around
them (Evans 2003, chapter 9, Specification, page 224, combined with chapter
5's Service definition).

## 9. Known production uses

**eShopOnContainers, the Ordering microservice.** Microsoft's reference
DDD-and-microservices sample implements domain services in the
Ordering.Domain project that coordinate operations spanning the Order
aggregate and Buyer aggregate, following the layering Microsoft's own
architecture guide documents (source repository,
[dotnet-architecture/eShopOnContainers,
github.com](https://github.com/dotnet-architecture/eShopOnContainers),
verified 2026-08-02, cross-referenced against [Microsoft's own written
guidance describing domain services in the Ordering
microservice](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-domain-model),
verified 2026-08-02, which states domain services coordinate several
domain objects, entities, and value objects as the definition it follows).

**Vaughn Vernon's IDDD Samples repository.** The companion code to
*Implementing Domain-Driven Design* ships explicit Domain Service
implementations, including an `AuthenticationService` in the
identity-and-access bounded context, matching the book's own worked
examples of Domain Services in chapter 7 (source repository,
[VaughnVernon/IDDD_Samples,
github.com](https://github.com/VaughnVernon/IDDD_Samples), verified
2026-08-02).

**Axon Framework's documented distinction between Aggregate command
handling and Domain Services.** Axon, a Java framework for building CQRS
and event-sourced applications with an explicit DDD building-block
vocabulary, documents that logic spanning several Aggregates that cannot be
resolved through the standard command dispatch to one Aggregate should be
placed in an external, stateless component rather than on the Aggregate,
matching Evans's Service definition (see [AxonIQ Reference Guide,
docs.axoniq.io](https://docs.axoniq.io/reference-guide/), verified
2026-08-02, general framework documentation for its DDD-modeled command
handling; the specific "Domain Service" terminology is Evans's, applied by
Axon's users to the cross-aggregate coordination the framework's saga and
external-command-gateway mechanisms are built to support).

**Spring Modulith's module boundary guidance.** Spring Modulith, an
official Spring project for structuring modular monoliths along DDD-style
module (bounded-context) boundaries, documents that cross-module
coordination should happen through explicitly exposed, stateless
application-facing components rather than by modules reaching into each
other's internals, the same boundary-preserving motivation that produces a
Domain Service between two Aggregates (source repository,
[spring-projects/spring-modulith,
github.com](https://github.com/spring-projects/spring-modulith), verified
2026-08-02).

## 10. Consequences

Positive.

- Keeps a cross-cutting business rule in exactly one place, in the
  ubiquitous language, instead of duplicated or split across two Entities.
- Preserves the independence of each Aggregate's invariants, since neither
  Aggregate needs to know the other exists.
- Keeps Entities and Value Objects focused, free of methods that do not
  belong to their own responsibility.
- Is easy to unit test in isolation, since it is stateless and its
  dependencies are explicit constructor or function arguments.
- Makes cross-Aggregate coordination visible and searchable in the
  codebase, a developer looking for "how does a transfer happen" finds one
  class, not a trail through two Entities.

Negative.

- Adds a class or module that owns no data of its own, which some
  developers read as procedural code wearing an object-oriented shape,
  and if overused it becomes exactly that, a transaction script dressed up
  as DDD (this is the specific risk Fowler's Anemic Domain Model critique
  targets, martinfowler.com, "AnemicDomainModel," verified 2026-08-02).
- Introduces an extra dependency edge for every caller and for every
  Aggregate it touches, more moving pieces than a single Entity method for
  the reader to trace.
- Easy to misuse as a dumping ground once a team learns the name, any
  behavior that is inconvenient to place gets routed to "some Service"
  rather than genuinely evaluated against the applicability list in
  dimension 4.
- Can silently become an Application Service in disguise if transaction
  management, event publishing, or authorization checks creep into it,
  eroding the intended layering (Vernon 2013, chapter 14).
- If used to work around a poorly drawn Aggregate boundary, rather than a
  genuinely cross-cutting concern, it hides a modeling problem instead of
  fixing it. the correct fix in that case is often to reconsider where the
  Aggregate boundary should sit.

## 11. Failure modes and misuse

**Symptom.** A `*Service` class grows to dozens of unrelated public methods
over a project's lifetime, with names spanning several unrelated domain
concepts.
**Cause.** The team adopted "put it in a Service" as the default answer to
"where does this go," without applying the applicability test from
dimension 4 each time, so every stray piece of logic accumulates in the
first Service that happened to be nearby.
**Fix.** Split the class along the ubiquitous-language boundaries it is
actually serving, one cohesive Service per real domain concept, and move
back to the relevant Entity or Value Object any method that genuinely
belongs to a single object.

**Symptom.** Every business rule in the codebase lives in a Service layer,
and every Entity has only getters, setters, and no method that enforces an
invariant.
**Cause.** The Anemic Domain Model. behavior was extracted into Services by
default rather than only when genuinely cross-cutting, defeating the
purpose of the object model (Fowler, "AnemicDomainModel," verified
2026-08-02).
**Fix.** For each Service method, ask whether it reads and mutates the
state of exactly one Entity. if so, move it onto that Entity and delete it
from the Service. keep the Service only for what genuinely spans more than
one object.

**Symptom.** Unit tests for a Domain Service require standing up a
database, an HTTP client, or a message broker before the test can run.
**Cause.** The Domain Service was given a concrete infrastructure
dependency, a database connection, an SDK client, instead of a
domain-defined interface, breaking the isolated-domain-layer principle
(Evans 2003, chapter 5, page 107).
**Fix.** Introduce a Repository or Gateway interface in the domain layer,
have the Domain Service depend on the interface, and inject a fake or
in-memory implementation in tests.

**Symptom.** A transfer half-completes in production. money leaves one
account but never arrives in the other, and the team discovers the failure
only from a support ticket, not from the code's own error handling.
**Cause.** The Domain Service coordinated two Aggregates without any
transaction or compensation strategy, assuming both saves would succeed or
fail together when the underlying storage does not guarantee that (for
example, two Aggregates persisted through two separate repositories backed
by two different databases, or a distributed system with no two-phase
commit).
**Fix.** Either wrap both saves in a single database transaction when both
Aggregates share a data store, or, when they do not, adopt the domain-event
variant from dimension 8, publish an event after the first change commits,
and implement an idempotent, retriable handler for the second change, with
explicit compensation logic for the case where the second change
ultimately cannot succeed.

**Symptom.** A Domain Service accepts a raw dictionary, a generic map, or a
loosely typed DTO instead of the domain's own Entities and Value Objects,
and callers pass in primitive strings and numbers directly.
**Cause.** The Service was written against a technical, not a domain,
vocabulary, often because it was extracted from a controller or a
transaction script without translating the inputs into domain types first.
**Fix.** Change the Service's method signature to accept the actual domain
types, an `AccountId` Value Object rather than a raw string, an `Amount`
Value Object rather than a raw decimal, pushing input validation to the
boundary where the Value Object is constructed.

## 12. Trade-off matrix

| Force | Domain Service | Entity method (put it on one object) | Application Service | Domain Event choreography |
|---|---|---|---|---|
| Where the rule lives | Explicit, named, own class | Implicit inside one Entity's API | Explicit but layered above domain rules | Implicit across handlers, harder to trace as one flow |
| Coupling between Aggregates | Low, mediated through the Service | High, one Aggregate depends on another directly | Low, but pushes coordination logic out of the domain layer entirely | Lowest, Aggregates never call each other directly |
| Consistency | Can be strict, within one transaction | Strict, within one Aggregate's boundary | Delegates consistency decision to whatever it calls | Eventual, requires idempotency and compensation |
| Testability | High, stateless, dependencies explicit | High for the single object, but hides the cross-object rule from its own test | Requires mocking orchestration concerns, transactions, events | Requires testing the event contract and each handler separately |
| Cognitive load to find the rule | Medium, one more class to know about | Low if the rule genuinely fits one object, high if it does not | Medium, mixed with orchestration concerns | High, the rule is distributed across time and handlers |
| Fit across service or process boundaries | Poor, needs both Aggregates in one process and one transaction | Same limitation as Domain Service | Same limitation | Best fit, this is the standard microservice answer |

## 13. Related and incompatible patterns

**Aggregate.** The Domain Service's most frequent collaborator and the
pattern it exists to protect. an Aggregate defines a consistency boundary,
and Domain Service is the mechanism DDD recommends for rules that cross
that boundary without collapsing it (Evans 2003, chapter 6).

**Repository.** A Domain Service commonly depends on one or more
Repository interfaces to look up the Aggregates it coordinates when the
caller has not already supplied them, keeping the dependency domain-defined
rather than infrastructure-defined (Evans 2003, chapter 6, "Repositories").

**Factory.** Where a Domain Service coordinates existing objects, a Factory
constructs a new Aggregate, often a complex one assembled from several
parts. The two are frequently confused because both are stateless helper
classes. the test is whether the operation creates a new Aggregate
(Factory) or coordinates existing ones (Domain Service) (Evans 2003,
chapter 5, "Factories," and chapter 5, "Services," discussed in the same
chapter as complementary building blocks).

**Application Service.** Sits directly above Domain Service in a layered
DDD architecture and calls into it. The two are frequently conflated in
smaller codebases that skip the distinction, which is acceptable only as
long as the team is explicit that they made that simplification rather
than believing there was never a distinction (Vernon 2013, chapter 14).

**Specification.** A Domain Service that makes a decision, is this order
eligible, does this customer qualify, often composes one or more
Specification objects internally rather than encoding the predicate logic
directly, keeping each predicate independently reusable (Evans 2003,
chapter 9, "Specification").

**Strategy (GoF).** A Domain Service that must vary its calculation
algorithm at runtime, a different shipping-cost formula per carrier, a
different pricing rule per market, frequently composes the classic GoF
Strategy pattern internally, injecting the varying algorithm rather than
branching on a type code inside the Service itself.

**Saga or Process Manager.** When the coordination a Domain Service would
perform needs to span multiple steps over time, potentially with
compensation on failure, and especially across service or process
boundaries, a Saga or Process Manager replaces the single synchronous
Domain Service call with a longer-running, explicitly stateful
coordination, which is precisely the case the stateless requirement in
dimension 3 rules out for a plain Domain Service.

**Incompatible with.** None recorded as flatly incompatible. Domain
Service is designed to compose with the surrounding DDD building blocks
rather than to compete with any one of them, so this entry's
`incompatible_with` field is empty.

## 14. Refactoring path in and out

**Introducing a Domain Service into code that lacks one.** Start from the
smell, a method on Entity A that reaches out to mutate Entity B directly, or
a rule duplicated in two places because it needs to apply to both A and B.
First write a failing test that expresses the cross-cutting rule as a
single behavior, "transferring more than the balance from A to B should
raise an error and change neither balance." Then extract a new stateless
class or function, name it from the ubiquitous language, move the
coordination logic into it, and have it call the existing public methods on
A and B rather than reaching into their internals. Delete the direct
dependency A previously had on B. Finally, update every caller to invoke
the new Service instead of calling A's now-removed cross-object method
directly. This sequence mirrors Martin Fowler's general Extract Class
refactoring, applied specifically to separate a cross-cutting rule from an
Entity that should not own it, the refactoring's mechanics are the standard
Extract Class steps, the domain-modeling judgement of what belongs where is
the DDD-specific addition this entry contributes.

**Removing a Domain Service once it stops earning its place.** This
happens in two directions. First, if a Domain Service's method turns out,
after the model matures, to read and mutate only one Aggregate, inline it
back onto that Aggregate as a method and delete the Service, this is Extract
Class run in reverse, sometimes called Inline Class. Second, if the
coordination the Service performs has outgrown a single synchronous call,
for example the two Aggregates it coordinates have moved to separate
microservices, replace the direct call with the domain-event
choreography variant from dimension 8, keeping the original business rule
intact but changing how the two sides communicate, from a direct method
call to a published event and a handler.

## 15. Testing and verification

A Domain Service is close to the easiest thing in a DDD codebase to unit
test, precisely because it is stateless and its dependencies are explicit.
Construct the Aggregates or Entities it needs directly in the test, in
whatever state the scenario requires, pass them (or a fake Repository that
returns them) into the Service, call the operation, and assert on the
resulting state of the Aggregates and on the Service's return value. no
database, no HTTP server, no container is required if the Service depends
only on domain-defined interfaces, per the isolation the Applicability
section requires.

What becomes easy because of the pattern. testing the cross-cutting rule in
complete isolation from persistence and from any single Aggregate's other
concerns, and testing edge cases, insufficient funds, a missing second
Aggregate, an invalid amount, as pure unit tests with no setup beyond
constructing the objects involved.

What becomes harder. verifying the two Aggregates were actually persisted
together correctly, in the same transaction or via the correct event flow,
is a concern the Domain Service's own unit tests will not catch, since the
Service itself does not manage the transaction. that verification belongs
to an integration test around the Application Service layer that calls the
Domain Service, or, in the event-driven variant, a contract test on the
event schema plus an integration test of the handler.

Test doubles that apply. a fake, in-memory implementation of any Repository
interface the Service depends on, is the standard technique, since the
interface is domain-defined and small, an in-memory Map-backed
implementation is usually simpler and more reliable than a mock framework
here. Reserve mocking frameworks for verifying that a specific interaction
occurred, for example asserting the Service called `save` exactly once on
each Aggregate, when that interaction itself is part of the behavior under
test.

## 16. Observability signals

A Domain Service is not itself an infrastructure component, so what to
observe is largely about making its business outcome visible, not about
technical health.

Log the Service's outcome, not its internal steps, at the point where it
completes, one structured log entry per invocation, naming the domain
concept and its result, "transfer completed, from=acct-123, to=acct-456,
amount=42.00, result=success" or "transfer rejected, from=acct-123,
reason=insufficient_funds," rather than a line per internal step, which
tends to leak implementation detail into logs that should read like the
domain.

Emit a domain event, or increment a domain-specific metric, for both the
success and the important failure paths, "transfers.completed" and
"transfers.rejected.insufficient_funds" as separate counters, since the two
outcomes usually need different alerting thresholds and different
downstream consumers.

A healthy Domain Service, viewed on a dashboard, shows the success-to-
rejection ratio holding steady within its expected business range (a
transfer service should reject roughly the same small fraction of attempts
week over week if the traffic mix has not changed) and latency for the
call, including the cost of its Repository lookups, staying within the
budget the calling Application Service's transaction can afford. A failing
instance shows either a spike in a specific rejection reason, which points
at an upstream data or business-rule problem, not the Service itself, or a
spike in exceptions that are not one of the domain's own named failure
outcomes, which points at an infrastructure or bug problem inside the
Service or one of its collaborators.

Trace the Service's invocation as a single span inside the calling
Application Service's larger transaction trace, tagging the span with the
domain concept's identifiers, account IDs, order IDs, so that a slow or
failing cross-Aggregate operation can be found by searching for the domain
entities involved, not merely by a generic class or method name.

## 17. Security and privacy implications

A Domain Service that spans two Aggregates is a natural place for an
authorization check to be skipped, because each Aggregate individually may
assume its caller has already been authorized, and the Service, sitting
between them, may assume the same of its own caller. State explicitly, at
the Application Service layer that invokes the Domain Service, whether the
caller is authorized to perform the cross-cutting operation, a transfer
between two specific accounts is a stronger authorization question, "is
this caller allowed to move money FROM this account," than either
Account's own invariants can answer alone, and Evans's own separation
places authorization concerns in the Application layer, not inside the
Domain Service, precisely so the check is not silently assumed away by
either layer (Vernon 2013, chapter 14, discusses authorization as an
Application Service concern).

Because a Domain Service commonly holds the two or more identifiers
involved in a cross-cutting operation in memory during its call, for
example two account numbers and a monetary amount, it is a point where
sensitive data briefly exists in a combined form that neither Aggregate
alone exposes. Log entries emitted from inside the Service, per dimension
16, should be reviewed against the same data classification and retention
policy that governs the underlying data, a transfer log line naming both
account numbers and an amount can itself be sensitive even if each
individual Account's own audit log is not.

Where the Domain Service's operation is financial or otherwise
irreversible, idempotency deserves explicit design attention, a retried
call to the Service, whether from a network retry, a duplicate message
delivery in the event-driven variant, or a user double-click that reached
the Application Service twice, should not execute the operation twice. this
is usually solved with an idempotency key supplied by the caller and
checked before the Service's core logic runs, and it is a security-adjacent
concern because an idempotency failure in a funds-transfer Domain Service
is directly exploitable as a double-spend.

## 18. References

- Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
  Software*, Addison-Wesley, 2003, chapter 5, "A Model Expressed in
  Software," section "Services," pages 104 to 107. Chapter 6, "The Life
  Cycle of a Domain Object," Aggregates and Repositories sections. Chapter
  9, "Making Implicit Concepts Explicit," Specification section, page 224.
- Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
  chapter 7, "Services," pages 229 to 246. Chapter 5, "Entities," page 111.
  Chapter 14, "Application," page 583.
- Martin Fowler, "AnemicDomainModel," martinfowler.com bliki, 25 November
  2003, [https://martinfowler.com/bliki/AnemicDomainModel.html](https://martinfowler.com/bliki/AnemicDomainModel.html),
  verified 2026-08-02.
- Microsoft, ".NET Microservices. Architecture for Containerized .NET
  Applications," "Design a microservice domain model," Microsoft Learn,
  [https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-domain-model](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-domain-model),
  verified 2026-08-02.
- Microsoft Architecture, eShopOnContainers reference application source,
  [https://github.com/dotnet-architecture/eShopOnContainers](https://github.com/dotnet-architecture/eShopOnContainers),
  verified 2026-08-02.
- Vaughn Vernon, IDDD_Samples companion source code repository,
  [https://github.com/VaughnVernon/IDDD_Samples](https://github.com/VaughnVernon/IDDD_Samples),
  verified 2026-08-02.
- AxonIQ, Axon Framework Reference Guide,
  [https://docs.axoniq.io/reference-guide/](https://docs.axoniq.io/reference-guide/),
  verified 2026-08-02.
- Spring Modulith project source repository,
  [https://github.com/spring-projects/spring-modulith](https://github.com/spring-projects/spring-modulith),
  verified 2026-08-02.
- Wikipedia, "Domain-driven design,"
  [https://en.wikipedia.org/wiki/Domain-driven_design](https://en.wikipedia.org/wiki/Domain-driven_design),
  verified 2026-08-02, used only as a cross-check of the general vocabulary,
  not as a primary source for any specific claim above.

## Code examples

### TypeScript

```typescript
type AccountId = string;

class Money {
  constructor(private readonly cents: number) {
    if (cents < 0) throw new Error("Money cannot be negative");
  }
  add(other: Money): Money { return new Money(this.cents + other.cents); }
  subtract(other: Money): Money {
    if (other.cents > this.cents) throw new Error("Insufficient funds");
    return new Money(this.cents - other.cents);
  }
  get value(): number { return this.cents; }
}

class Account {
  constructor(public readonly id: AccountId, private balance: Money) {}
  withdraw(amount: Money): void { this.balance = this.balance.subtract(amount); }
  deposit(amount: Money): void { this.balance = this.balance.add(amount); }
  get currentBalance(): Money { return this.balance; }
}

interface AccountRepository {
  findById(id: AccountId): Account;
  save(account: Account): void;
}

class TransferResult {
  constructor(public readonly success: boolean, public readonly reason?: string) {}
}

class TransferService {
  constructor(private readonly accounts: AccountRepository) {}

  transfer(fromId: AccountId, toId: AccountId, amount: Money): TransferResult {
    const from = this.accounts.findById(fromId);
    const to = this.accounts.findById(toId);
    try {
      from.withdraw(amount);
    } catch (e) {
      return new TransferResult(false, "insufficient_funds");
    }
    to.deposit(amount);
    this.accounts.save(from);
    this.accounts.save(to);
    return new TransferResult(true);
  }
}

class InMemoryAccountRepository implements AccountRepository {
  private store = new Map<AccountId, Account>();
  add(account: Account): void { this.store.set(account.id, account); }
  findById(id: AccountId): Account {
    const a = this.store.get(id);
    if (!a) throw new Error("Account not found");
    return a;
  }
  save(account: Account): void { this.store.set(account.id, account); }
}

const repo = new InMemoryAccountRepository();
repo.add(new Account("acct-1", new Money(10000)));
repo.add(new Account("acct-2", new Money(500)));
const service = new TransferService(repo);
const result = service.transfer("acct-1", "acct-2", new Money(2500));
console.log(result.success, repo.findById("acct-1").currentBalance.value, repo.findById("acct-2").currentBalance.value);
```

### Python

```python
from dataclasses import dataclass
from typing import Dict, Optional


class InsufficientFundsError(Exception):
    pass


@dataclass
class Money:
    cents: int

    def __post_init__(self):
        if self.cents < 0:
            raise ValueError("Money cannot be negative")

    def add(self, other: "Money") -> "Money":
        return Money(self.cents + other.cents)

    def subtract(self, other: "Money") -> "Money":
        if other.cents > self.cents:
            raise InsufficientFundsError()
        return Money(self.cents - other.cents)


@dataclass
class Account:
    account_id: str
    balance: Money

    def withdraw(self, amount: Money) -> None:
        self.balance = self.balance.subtract(amount)

    def deposit(self, amount: Money) -> None:
        self.balance = self.balance.add(amount)


class AccountRepository:
    def __init__(self):
        self._store: Dict[str, Account] = {}

    def add(self, account: Account) -> None:
        self._store[account.account_id] = account

    def find_by_id(self, account_id: str) -> Account:
        return self._store[account_id]

    def save(self, account: Account) -> None:
        self._store[account.account_id] = account


@dataclass
class TransferResult:
    success: bool
    reason: Optional[str] = None


class TransferService:
    def __init__(self, accounts: AccountRepository):
        self._accounts = accounts

    def transfer(self, from_id: str, to_id: str, amount: Money) -> TransferResult:
        from_account = self._accounts.find_by_id(from_id)
        to_account = self._accounts.find_by_id(to_id)
        try:
            from_account.withdraw(amount)
        except InsufficientFundsError:
            return TransferResult(success=False, reason="insufficient_funds")
        to_account.deposit(amount)
        self._accounts.save(from_account)
        self._accounts.save(to_account)
        return TransferResult(success=True)


if __name__ == "__main__":
    repo = AccountRepository()
    repo.add(Account("acct-1", Money(10000)))
    repo.add(Account("acct-2", Money(500)))
    service = TransferService(repo)
    result = service.transfer("acct-1", "acct-2", Money(2500))
    print(result.success, repo.find_by_id("acct-1").balance.cents, repo.find_by_id("acct-2").balance.cents)
```

### Go

```go
package main

import (
	"errors"
	"fmt"
)

var ErrInsufficientFunds = errors.New("insufficient funds")

type Money struct {
	Cents int
}

func NewMoney(cents int) (Money, error) {
	if cents < 0 {
		return Money{}, errors.New("money cannot be negative")
	}
	return Money{Cents: cents}, nil
}

func (m Money) Add(other Money) Money { return Money{Cents: m.Cents + other.Cents} }

func (m Money) Subtract(other Money) (Money, error) {
	if other.Cents > m.Cents {
		return Money{}, ErrInsufficientFunds
	}
	return Money{Cents: m.Cents - other.Cents}, nil
}

type Account struct {
	ID      string
	Balance Money
}

func (a *Account) Withdraw(amount Money) error {
	newBalance, err := a.Balance.Subtract(amount)
	if err != nil {
		return err
	}
	a.Balance = newBalance
	return nil
}

func (a *Account) Deposit(amount Money) {
	a.Balance = a.Balance.Add(amount)
}

type AccountRepository interface {
	FindByID(id string) (*Account, error)
	Save(a *Account) error
}

type InMemoryAccountRepository struct {
	store map[string]*Account
}

func NewInMemoryAccountRepository() *InMemoryAccountRepository {
	return &InMemoryAccountRepository{store: make(map[string]*Account)}
}

func (r *InMemoryAccountRepository) Add(a *Account) { r.store[a.ID] = a }

func (r *InMemoryAccountRepository) FindByID(id string) (*Account, error) {
	a, ok := r.store[id]
	if !ok {
		return nil, errors.New("account not found")
	}
	return a, nil
}

func (r *InMemoryAccountRepository) Save(a *Account) error {
	r.store[a.ID] = a
	return nil
}

type TransferResult struct {
	Success bool
	Reason  string
}

type TransferService struct {
	Accounts AccountRepository
}

func (s *TransferService) Transfer(fromID, toID string, amount Money) TransferResult {
	from, err := s.Accounts.FindByID(fromID)
	if err != nil {
		return TransferResult{Success: false, Reason: "from_not_found"}
	}
	to, err := s.Accounts.FindByID(toID)
	if err != nil {
		return TransferResult{Success: false, Reason: "to_not_found"}
	}
	if err := from.Withdraw(amount); err != nil {
		return TransferResult{Success: false, Reason: "insufficient_funds"}
	}
	to.Deposit(amount)
	_ = s.Accounts.Save(from)
	_ = s.Accounts.Save(to)
	return TransferResult{Success: true}
}

func main() {
	repo := NewInMemoryAccountRepository()
	m1, _ := NewMoney(10000)
	m2, _ := NewMoney(500)
	repo.Add(&Account{ID: "acct-1", Balance: m1})
	repo.Add(&Account{ID: "acct-2", Balance: m2})
	service := &TransferService{Accounts: repo}
	amount, _ := NewMoney(2500)
	result := service.Transfer("acct-1", "acct-2", amount)
	from, _ := repo.FindByID("acct-1")
	to, _ := repo.FindByID("acct-2")
	fmt.Println(result.Success, from.Balance.Cents, to.Balance.Cents)
}
```

### Swift

```swift
struct InsufficientFundsError: Error {}
struct NegativeMoneyError: Error {}
struct NotFoundError: Error {}

struct Money {
    let cents: Int
    init(_ cents: Int) throws {
        if cents < 0 { throw NegativeMoneyError() }
        self.cents = cents
    }
    func add(_ other: Money) -> Money { try! Money(cents + other.cents) }
    func subtract(_ other: Money) throws -> Money {
        if other.cents > cents { throw InsufficientFundsError() }
        return try Money(cents - other.cents)
    }
}

final class Account {
    let id: String
    private(set) var balance: Money
    init(id: String, balance: Money) { self.id = id; self.balance = balance }
    func withdraw(_ amount: Money) throws { balance = try balance.subtract(amount) }
    func deposit(_ amount: Money) { balance = balance.add(amount) }
}

protocol AccountRepository {
    func findById(_ id: String) throws -> Account
    func save(_ account: Account)
}

final class InMemoryAccountRepository: AccountRepository {
    private var store: [String: Account] = [:]
    func add(_ account: Account) { store[account.id] = account }
    func findById(_ id: String) throws -> Account {
        guard let a = store[id] else { throw NotFoundError() }
        return a
    }
    func save(_ account: Account) { store[account.id] = account }
}

struct TransferResult {
    let success: Bool
    let reason: String?
}

final class TransferService {
    private let accounts: AccountRepository
    init(accounts: AccountRepository) { self.accounts = accounts }

    func transfer(fromId: String, toId: String, amount: Money) -> TransferResult {
        guard let from = try? accounts.findById(fromId) else {
            return TransferResult(success: false, reason: "from_not_found")
        }
        guard let to = try? accounts.findById(toId) else {
            return TransferResult(success: false, reason: "to_not_found")
        }
        do {
            try from.withdraw(amount)
        } catch {
            return TransferResult(success: false, reason: "insufficient_funds")
        }
        to.deposit(amount)
        accounts.save(from)
        accounts.save(to)
        return TransferResult(success: true, reason: nil)
    }
}

let repo = InMemoryAccountRepository()
repo.add(Account(id: "acct-1", balance: try! Money(10000)))
repo.add(Account(id: "acct-2", balance: try! Money(500)))
let service = TransferService(accounts: repo)
let result = service.transfer(fromId: "acct-1", toId: "acct-2", amount: try! Money(2500))
let from = try! repo.findById("acct-1")
let to = try! repo.findById("acct-2")
print(result.success, from.balance.cents, to.balance.cents)
```

Java and Rust are omitted from the runnable set for this entry. the pattern
is not language-idiomatically different in either, it repeats the same
dependency-injected stateless class shape shown in TypeScript and Go, and
adding two more nearly identical translations would not add distinct
insight into the pattern itself, unlike, for example, a pattern where a
language's closures or coroutines genuinely change the shape of the
solution.
