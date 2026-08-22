---
name: Domain Model
slug: domain-model
family: 06-enterprise-application-architecture
category: Domain Logic
aliases: [Rich Domain Model, Object Model]
first_described: "Fowler 2002"
maturity: canonical
related: [transaction-script, table-module, repository, unit-of-work, data-mapper, active-record, specification, factory-method]
incompatible_with: [transaction-script]
verified: 2026-08-02
---

# Domain Model

## 1. Name, aliases, and lineage

The canonical name is Domain Model, one of the three domain logic patterns
catalogued in Martin Fowler, *Patterns of Enterprise Application Architecture*,
Addison-Wesley, 2002, chapter 9, "Domain Logic Patterns Layer", pages 116 to 122
(Domain Model entry). Fowler credits the underlying idea to the general
object-oriented modeling literature and, closer to the specific
enterprise-application framing, to Eric Evans, whose 2003 book *Domain-Driven
Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, built an
entire methodology around the same core structure and popularised the term
**Rich Domain Model** to distinguish it from an anemic imitation. Fowler's own
catalog page states the pattern plainly, calling it "an object model of the
domain that incorporates both behavior and data"
(https://martinfowler.com/eaaCatalog/domainModel.html, verified 2026-08-02).

**Object Model** is an older, more generic alias used in modeling literature
before Fowler's book fixed the enterprise-architecture vocabulary. It is not
wrong, but it is imprecise, because plenty of object models exist that hold
only data (see Data Transfer Object) or only behaviour (see Table Module's
static methods over a shared table gateway), and Domain Model specifically
requires objects that hold both, wired together by object references rather
than by foreign keys or ID lookups.

Fowler distinguishes two shapes of the pattern in the same chapter, and the
distinction matters for every dimension below.

- **Simple Domain Model.** One object type per database table, roughly, with
  straightforward one-to-one correspondence between the object graph and the
  relational schema. Fowler calls this shape "not too dissimilar" to Active
  Record in appearance, though it differs in that persistence responsibility is
  pulled out into a separate mapping layer rather than living on the domain
  object itself (Fowler 2002, p. 119).
- **Rich Domain Model.** Object types do not correspond one-to-one with tables.
  Inheritance hierarchies, Value Objects, small collaborating objects, and
  Strategy-shaped delegation appear to express business rules directly in the
  type system, at the cost of a mapping layer that must reconcile a much wider
  object-relational gap (Fowler 2002, p. 119 to 120).

This entry treats "Domain Model" as covering both shapes and calls out where a
concern applies to one shape more than the other.

## 2. Problem and context

An enterprise application accumulates business rules over its life, pricing
tiers, discount eligibility, order-state transitions, tax jurisdictions, credit
limits, cancellation windows. Early in a project these rules are few and the
obvious place to put them is wherever the request handler already sits, one
`if` block per rule. This is Transaction Script, and it is the right choice
while the rule count is small (see the trade-off matrix in dimension 12).

The problem Domain Model exists to solve appears once the rule count grows past
roughly the point where a single procedure can hold them in a reader's head at
once, and, more specifically, once the SAME rule needs to run from more than
one entry point. A nightly batch job re-prices every open order using the same
pricing rule an interactive checkout page just used, and a support-desk admin
tool needs to apply the same cancellation-eligibility check a customer-facing
API uses. Under Transaction Script, that rule is either duplicated in three
scripts (three chances for it to drift apart) or hoisted into a shared
procedure that takes so many parameters and produces so many side effects that
it stops reading like a domain concept and starts reading like a dispatch
table. Fowler names this the central argument for Domain Model. As domain
logic gets more complex, an object model that groups data and closely-related
behavior together handles that complexity far better than a script that
manipulates the data from the outside (Fowler 2002, p. 116 to 117).

The context this arises in is specifically object-oriented enterprise
application development against a relational, document, or hybrid persistence
store, where the persistence schema and the useful in-memory shape of the
business rules are not the same shape. That gap, the object-relational
impedance mismatch, is not incidental to Domain Model, it is the direct
consequence of choosing to let the object graph be shaped by the business
rules rather than by the table layout, and every dimension from Structure
through Failure Modes below is, in one way or another, about managing that gap.

## 3. Forces

- **Rule locality versus rule discoverability.** Domain Model wins on rule
  locality. A rule about what makes an order cancellable lives on the `Order`
  object with the state it examines, so anyone editing order behaviour looks in
  one obvious place. It can lose on discoverability for someone who does not
  already know the object model, because the rule is not visible from a request
  handler's linear top-to-bottom read the way a Transaction Script line is.
- **Reuse versus mapping cost.** The pattern earns its keep exactly when the
  same rule must run from multiple entry points, batch and interactive, API and
  admin tool. The price for that reuse is a mapping layer, typically Data
  Mapper, that reconciles the object graph with however the data is actually
  stored. A Rich Domain Model whose graph diverges sharply from the schema
  pushes this cost up sharply, while a Simple Domain Model keeps it modest.
- **Consistency and transactional boundaries.** A rich object graph with
  bidirectional associations and lazy-loaded collections makes it easy to
  accidentally load, and therefore accidentally lock or dirty-check, far more
  of the graph than one logical transaction needs. Unit of Work and clear
  Aggregate boundaries (a Domain-Driven Design refinement layered on top of
  Domain Model, not part of Fowler's original catalog entry) exist specifically
  to bound this.
- **Team topology and skill level.** Fowler is explicit that Domain Model
  demands more object-oriented design skill from the team than Transaction
  Script does, and that a team without that skill can produce a worse outcome
  with Domain Model than they would have with a straightforward script,
  because a poorly designed object graph is harder to untangle than a poorly
  organised set of procedures (Fowler 2002, p. 117 and p. 121, "Domain logic
  can get complicated... this complexity is best handled with an object
  model").
- **Performance and identity management.** Object identity, lazy loading, and
  the N+1 query problem are forces that barely exist under Transaction Script,
  where every query is written by hand for its call site, but become a
  standing operational concern under Domain Model, because a naive traversal
  of the object graph can silently issue one query per object.
- **Operability and cognitive load at 2 a.m.** A stack trace through a
  Transaction Script reads top to bottom. A stack trace through a Rich Domain
  Model with several layers of delegation and polymorphic dispatch requires the
  reader to already hold a mental model of which concrete type is in play,
  which is a real cost during an incident.

Domain Model favours rule locality, reuse across entry points, and
expressiveness of complex business rules. It sacrifices linear readability for
a newcomer, adds mapping cost, and raises the skill floor for the team.

## 4. Applicability and non-applicability

Reach for Domain Model when:

- The same business rule must be invoked from more than one entry point
  (interactive UI, batch job, integration API, admin console) and must behave
  identically in all of them.
- Business logic is genuinely complex. Conditional rules interact, state
  machines have several legal transitions, and calculations compose from
  smaller calculations (discount stacking, tax computation across
  jurisdictions).
- The domain vocabulary itself is valuable to make explicit in code, because
  the team includes domain experts who benefit from code that mirrors the
  language they already use (this is the seed of what Evans later formalised
  as Ubiquitous Language in Domain-Driven Design, Evans 2003, part I).
- The application is expected to live and grow for years, so the up-front
  investment in an explicit object model amortises across many future changes.

Do NOT reach for Domain Model when:

- The application is mostly simple CRUD with thin validation and little
  branching logic. Fowler's own guidance is blunt on this point. For simple
  domain logic, Transaction Script is usually the better choice, and applying
  Domain Model is over-engineering that adds a mapping layer, an ORM or Data
  Mapper, and a steeper learning curve for no corresponding benefit (Fowler
  2002, p. 117, "if your logic is simple... you shouldn't bother").
- The team lacks object-relational mapping experience and there is no time
  budget to acquire it. A poorly executed Domain Model, with an ad hoc
  persistence layer bolted directly onto domain classes, tends to degenerate
  into an Anemic Domain Model, which Fowler and Evans both treat as an
  anti-pattern precisely because it keeps the mapping cost of Domain Model
  while giving up the behavioural cohesion that was the entire point (Fowler,
  "AnemicDomainModel", https://martinfowler.com/bliki/AnemicDomainModel.html,
  verified 2026-08-02).
- The application is a thin orchestration or integration layer whose real work
  happens in other systems (an API gateway, a webhook relay, a reporting ETL
  job). There is no domain logic to model.
- Reporting and analytical queries dominate the workload. A rich object graph
  is expensive to traverse for wide aggregate reads, and Fowler's chapter 14
  guidance on reporting is to bypass the domain layer with direct SQL for that
  workload rather than force it through object loading.
- The persistence technology has no realistic mapping story for object graphs
  (certain very constrained embedded or edge environments), where Table Module
  or Transaction Script against raw rows is the more honest fit.

## 5. Structure

- **Domain Object.** Any class that represents a concept in the business
  domain (`Order`, `Customer`, `Contract`, `Invoice`). Holds both the state
  relevant to that concept and the behaviour that operates on that state.
  Fowler's defining requirement is that these two things sit together, not
  split across a "data holder" and a "logic holder" (Fowler 2002, p. 116).
- **Entity.** A domain object whose identity persists across state changes and
  across time, distinguished by an identifier rather than by the equality of
  its fields (an `Order` with id 42 is the same order even after every field
  on it changes). Fowler discusses this identity concern directly in relation
  to Identity Map (Fowler 2002, p. 216 to 217), and Evans later names it
  formally as Entity (Evans 2003, chapter 5).
- **Value Object.** A domain object with no independent identity, compared by
  the equality of its fields, and typically immutable (`Money`, `DateRange`,
  `Address`). Fowler catalogs Value Object separately (Fowler 2002, p. 486 to
  487) and it is the most common building block used inside a Rich Domain
  Model to avoid primitive obsession.
- **Association.** An object reference from one domain object to another,
  standing in for what a relational schema would express as a foreign key.
  Associations may be unidirectional or bidirectional, and bidirectional
  associations require the object model to keep both ends in sync manually
  (Fowler 2002, p. 500 to 501, discussing the mapping implications).
- **Aggregate root (a refinement, not in Fowler's original catalog entry, but
  standard practice layered onto Domain Model by Evans).** A domain object
  that is the single entry point for loading and mutating a cluster of related
  objects, so that external code never holds a reference to an internal member
  of the cluster without going through the root (Evans 2003, chapter 6,
  "Aggregates").
- **Mapping layer (usually Data Mapper, occasionally Active Record for the
  Simple Domain Model shape).** A separate set of objects, not part of the
  domain model proper, whose job is translating domain objects to and from
  whatever the persistence store actually stores. Fowler is explicit that
  Domain Model does not specify how persistence happens, only that persistence
  concerns should be kept out of the domain objects themselves where possible
  (Fowler 2002, p. 117 to 118).
- **Repository (frequently paired, catalogued separately by Fowler, p. 322 to
  325).** Provides a collection-like interface over the aggregate roots so
  application and interface layers never talk to the mapping layer or the
  database directly.

## 6. ASCII structure diagram

```
+------------------------------------------------------------------+
|                        Application / Service Layer                |
|   (orchestrates a use case, has NO business rules of its own)     |
+---------------------------+----------------------------------------+
                            |
                            v
                  +-------------------+
                  |    Repository     |   collection-like interface
                  |  (OrderRepository)|
                  +---------+---------+
                            |
                            v
+---------------------------------------------------------------------+
|                          Domain Model                               |
|                                                                       |
|   +--------------+ 1        * +----------------+                    |
|   |    Order     |<---------->|   LineItem     |  Entity <-> Entity |
|   | (Aggregate   |            | (owned by root)|  association       |
|   |  Root)       |            +----------------+                    |
|   +------+-------+                     |                            |
|          | holds                       | references (Value Object)  |
|          v                             v                            |
|   +--------------+            +----------------+                    |
|   |  OrderStatus |            |     Money      |                    |
|   | (Value Obj)  |            |  (Value Obj)   |                    |
|   +--------------+            +----------------+                    |
|                                                                       |
|   Order.cancel() checks OrderStatus and LineItem state ITSELF.       |
|   Business rules live INSIDE these objects, not in the caller.       |
+---------------------------------------------------------------------+
                            ^
                            | populates / persists via
                            v
                  +-------------------+
                  |    Data Mapper    |   translates object graph
                  | (OrderMapper)     |   to and from storage rows
                  +---------+---------+
                            |
                            v
                  +-------------------+
                  |   Relational or   |
                  |   document store  |
                  +-------------------+
```

## 7. Dynamics

The runtime flow for a typical use case, "cancel an order", walking through the
layers, follows the same shape whether the entry point is an HTTP handler, a
CLI command, or a batch job step.

```
Caller (any entry point)          Repository        Order (domain obj)   Data Mapper
      |                               |                     |                |
      |-- cancelOrder(orderId) ------>|                     |                |
      |                               |-- findById(id) ---->|                |
      |                               |                (delegates load)      |
      |                               |----------------------------------->|
      |                               |                     |          SELECT
      |                               |                     |<-- row(s) --  |
      |                               |<-- Order instance --|                |
      |                               |    (fully rehydrated,                |
      |                               |     associations wired)              |
      |<-- Order instance ------------|                     |                |
      |                               |                     |                |
      |-- order.cancel() ------------------------------------->              |
      |                                                     |                |
      |                                      order checks OWN state.         |
      |                                      status equals PLACED?           |
      |                                      withinCancelWindow()?           |
      |                                      each LineItem.isReturnable()?   |
      |                                                     |                |
      |                                      IF eligible.                    |
      |                                        status = CANCELLED            |
      |                                        raises OrderCancelled event   |
      |                                      ELSE.                           |
      |                                        raises IllegalStateException  |
      |                                                     |                |
      |<-- (mutated Order, or exception) -------------------|                |
      |                               |                     |                |
      |-- repository.save(order) --->|                     |                |
      |                               |-- (Unit of Work tracks dirty state,  |
      |                               |    Data Mapper issues UPDATE) ------>|
      |                               |                                UPDATE
      |                               |<---------------------------------- ok |
      |<-- committed --------------- |                     |                |
```

The decisive property this diagram shows is this. The caller never inspects
`status` or `lineItems` directly to decide whether cancellation is legal. It
asks the `Order` to cancel itself, and the `Order` is the thing that knows the
rule. Under Transaction Script the same decision logic would live in the
caller's procedure, reading the row's status column directly.

## 8. Implementation variants

- **Anemic-avoidance discipline.** The single most consequential
  implementation choice is whether setters and getters are the primary public
  surface (anemic, Transaction-Script-with-extra-steps in practice) or whether
  behaviour methods (`cancel()`, `applyDiscount()`, `isEligibleForRenewal()`)
  are the primary public surface and fields are private, mutated only as a
  side effect of a behaviour call. Fowler and Evans both treat the anemic
  variant as a failure to actually apply the pattern rather than as a
  legitimate lightweight variant (Fowler, AnemicDomainModel bliki entry, cited
  above).
- **Simple Domain Model with Active Record persistence.** For a Rails,
  Laravel, or Django-style stack, domain objects that are close to a one-table
  mapping are frequently given persistence methods directly (`order.save()`),
  blending Domain Model with Active Record. Fowler discusses this blend
  directly and treats it as reasonable for the simple shape specifically
  because the object-relational gap is small (Fowler 2002, p. 119).
- **Rich Domain Model with Data Mapper and Unit of Work.** For the complex
  shape, persistence is deliberately kept off the domain object entirely. A
  separate mapper and unit of work track dirty objects and issue writes. This
  is the variant Fowler most closely associates with "Domain Model" when the
  term is used without qualification (Fowler 2002, chapter 10, on the mapping
  patterns that pair with it).
- **Aggregate-bounded variant (Domain-Driven Design refinement).** Layers
  Aggregate, Aggregate Root, and Repository-per-aggregate on top of the base
  pattern, constraining which objects may be loaded, mutated, or referenced
  from outside the boundary, specifically to bound the transactional
  consistency scope (Evans 2003, chapter 6).
- **Functional-core variant.** In languages that favour immutability
  (functional-first languages, or object-oriented code written in a
  functional style), the "behaviour on the object" requirement is satisfied by
  pure functions that take an immutable domain value and return a new one,
  rather than by mutating methods. The behaviour-and-data cohesion Fowler
  requires is preserved at the module level (functions and the type they
  operate on live together) even though it is not preserved at the
  single-object level. This is common in Rust and in functional-style Scala or
  F# domain layers, and it changes several of the consequences in dimension
  10 (mutation-related concurrency hazards shrink, testing gets easier).
- **Event-sourced variant.** The domain object's current state is not stored
  directly. Instead a log of domain events is stored, and the object's state
  is the fold of replaying those events. The behaviour-holding object is
  unchanged, but the mapping layer's job changes from row translation to event
  application. This variant is common in the DDD and CQRS ecosystem that grew
  out of Evans's work but is not part of Fowler's 2002 catalog entry itself.

## 9. Known production uses

- **Spring Framework's reference documentation for the Data layer explicitly
  presents Domain Model, contrasted with Transaction Script, as the
  architectural choice Spring is built to support** through its transaction
  management and Data Access abstractions, citing Fowler's catalog directly.
  Spring's own guides on "Domain-Driven Design" list Entity, Value Object, and
  Aggregate as first-class modeling concepts the framework is designed around
  (https://spring.io/guides, and the Spring Framework reference documentation
  "Data Access", https://docs.spring.io/spring-framework/reference/data-access.html,
  verified 2026-08-02).
- **Hibernate ORM's own documentation frames its entire mapping model around
  supporting a rich domain object graph**, describing entities, value types,
  and associations as first-class citizens of the mapping layer specifically
  so applications can express Domain Model rather than Simple Domain Model or
  Table Module against Hibernate. Hibernate's user guide states the object or
  relational mapping problem it solves in the same terms as Fowler's chapter
  10 mapping patterns (https://hibernate.org/orm/documentation/, verified
  2026-08-02).
- **Eric Evans's Domain-Driven Design methodology, and its associated
  reference implementation projects, is a direct, book-length extension of
  Fowler's Domain Model pattern** built around Entity, Value Object,
  Aggregate, Repository, and Domain Event, all of which are named refinements
  of the same base pattern (Evans 2003, and the Domain Language organisation's
  DDD reference material at https://domainlanguage.com/ddd/, verified
  2026-08-02).
- **Ruby on Rails's Active Record layer is frequently used to implement the
  Simple Domain Model shape**, with behaviour methods added directly onto
  ActiveRecord-backed model classes. The Rails Guides describe models as
  holding both "data" and "the rules to manipulate that data"
  (https://guides.rubyonrails.org/active_record_basics.html, verified
  2026-08-02), matching Fowler's requirement that data and behaviour live
  together, while acknowledging the pairing is closer to Active Record than to
  the Data-Mapper-backed Rich Domain Model shape.
- **Java's javax.money / JSR 354 specification and its Moneta reference
  implementation model `Money` as a behaviour-bearing Value Object** (with
  `add`, `subtract`, `multiply`, currency-aware comparison methods rather than
  a bare numeric field plus external utility functions), which is the
  canonical small-scale illustration of Domain Model's Value Object structure
  used across enterprise Java systems that adopt the specification
  (https://javamoney.github.io/, verified 2026-08-02).

## 10. Consequences

Positive outcomes.

- Business rules that are used from more than one entry point are written
  once, on the object that owns the relevant state, and reused by every
  caller, which removes the drift risk that duplicated procedural logic
  carries.
- The object model becomes a place where complex, interacting rules
  (eligibility, state transitions, calculations that compose) can be expressed
  directly in the type system rather than flattened into conditional chains,
  which Fowler credits as the pattern's core value once complexity passes a
  threshold (Fowler 2002, p. 116 to 117).
- Encapsulation of invariants becomes possible in a way procedural code
  struggles to guarantee. If `Order.cancel()` is the only way to move an order
  to `CANCELLED`, the invariant "an order is never cancelled outside its
  cancellation window" can be enforced in exactly one place and never bypassed
  by a forgetful caller.
- The vocabulary of the code starts to mirror the vocabulary domain experts
  actually use, which lowers the translation cost between a requirements
  conversation and the resulting diff (this is the seed of Evans's Ubiquitous
  Language, Evans 2003, chapter 2).
- Unit testing business rules becomes possible in isolation from persistence
  and from any web framework, because the rule lives on a plain object rather
  than inside a request handler.

Negative outcomes.

- A mapping layer between the object graph and the persistence store is
  required, and for the Rich Domain Model shape that layer is genuinely hard
  to build well. Fowler names this directly as the primary cost of the pattern
  (Fowler 2002, p. 117 to 118).
- The team needs real object-oriented design skill. A poorly factored object
  model, with god objects, deep inheritance chains used for the wrong reason,
  or bidirectional associations that are never kept consistent, is worse to
  maintain than an equivalent Transaction Script, because the failure mode is
  distributed across many small objects instead of concentrated in one
  readable procedure.
- Debugging requires holding a mental model of polymorphic dispatch. A stack
  trace showing a call to `shippingCost()` does not, by itself, say which
  concrete strategy or subclass actually ran, whereas a Transaction Script
  procedure shows the branch taken directly in the trace.
- Performance tuning becomes an object-graph-traversal problem (lazy loading,
  N+1 queries, over-fetching an aggregate for a read that only needed one
  field) rather than a query-tuning problem, and the two require different
  skills and different tools.
- Serialisation and cross-process boundaries (an HTTP API response, a message
  queue payload) are awkward, because a rich object graph with circular
  associations and behaviour does not serialise cleanly the way a flat DTO
  does. Most Domain Model codebases end up with a separate DTO or view-model
  layer exactly to solve this, adding yet another mapping concern.

## 11. Failure modes and misuse

- **Symptom.** Every domain class in the codebase has only getters, setters,
  and a constructor. All conditional logic that used to be the pattern's
  reason for existing lives in "service" or "manager" classes that take the
  domain object as a parameter and mutate it from outside.
  **Cause.** The team adopted the vocabulary and the class layout of Domain
  Model (an `Order` class, an `OrderRepository`) without adopting the
  behaviour-on-the-object discipline, producing an Anemic Domain Model.
  **Fix.** Move each piece of conditional logic that reads a domain object's
  fields into a method on that object. The mechanical refactoring is Fowler's
  Move Method, and the destination test is whether this logic only ever needs
  fields that already live on this one object. Where a rule genuinely spans
  several object types, a Domain Service (a small, stateless coordinator, not
  a getter-and-setter manager) is the correct home, not a bypass back to
  anemic style.

- **Symptom.** A single write to one `Order` triggers dozens of SQL SELECT
  statements, visible in a query log as a burst of near-identical single-row
  queries immediately after the write.
  **Cause.** Lazy-loaded associations on the aggregate are being traversed one
  at a time inside a loop (classic N+1), often because a rich object graph
  makes it easy to write `order.getLineItems().forEach(li -> li.getProduct().getName())`
  without noticing that each `.getProduct()` call is a separate query.
  **Fix.** Use eager fetch joins, batch fetching, or an explicit query
  projection for the specific read path that needs many related rows at once.
  Do not attempt to solve this by making every association eager by default,
  which trades N+1 for chronic over-fetching everywhere else.

- **Symptom.** Two team members each add a validation rule to what looks like
  "the same" concept, but the rules live on two different classes (an
  `OrderValidator` service and a check inside `Order.place()`), and in
  production an order slips through that satisfies one check but not the
  other.
  **Cause.** Rule ownership was never assigned to a single object or a single
  aggregate boundary, so the codebase drifted into having two competing
  authorities for the same invariant. This usually happens when the Rich
  Domain Model shape is adopted without ever defining Aggregate boundaries.
  **Fix.** Name the aggregate root explicitly for every cluster of related
  invariants and route every mutation of that cluster through the root. Treat
  a second, parallel validator that duplicates a rule already on the root as a
  defect to delete, not a second opinion to reconcile.

- **Symptom.** A unit test for a single business rule requires standing up a
  full Spring context, a real or in-memory database, and several unrelated
  repositories before it can even construct the object under test.
  **Cause.** The domain object's constructor or factory has been coupled to
  persistence infrastructure (it reaches out to a repository or a service
  locator inside its own constructor), which defeats the isolation-testing
  benefit the pattern is supposed to provide.
  **Fix.** Keep domain object construction free of infrastructure
  dependencies. Pass in whatever collaborators the object needs as plain
  values or plain interfaces at construction time, and let a Factory (see
  Factory Method, this repository) or the mapping layer be the only place that
  talks to infrastructure.

- **Symptom.** A `PATCH` request updates one field on an `Order` and, several
  requests later, an unrelated feature reports stale or inconsistent data for
  the same order, with no exception ever thrown.
  **Cause.** Bidirectional associations were updated on one side only (the
  `LineItem.order` back-reference was not kept in sync when the `Order`'s
  `lineItems` collection changed), so the in-memory graph became internally
  inconsistent while looking correct from the side that was touched.
  **Fix.** Either make associations unidirectional wherever the reverse
  direction is not actually needed by any use case, or centralise the paired
  update inside a single method on the owning side (`order.addLineItem(item)`
  sets both `lineItems` and `item.order` together) so no caller can update one
  side without the other.

## 12. Trade-off matrix

| Force | Domain Model | Transaction Script | Table Module | Active Record |
|---|---|---|---|---|
| Handles complex, interacting business rules | Strong. Encapsulates rules on the objects that own the relevant state, composes cleanly as rules interact. | Weak past a moderate rule count. Conditionals accumulate in procedures and duplicate across scripts. | Weak. Static methods over a table gateway do not compose well for rules spanning multiple related tables. | Moderate. Fine for per-row rules, weak once a rule spans several related rows or tables. |
| Reuse of one rule across many entry points | Strong. One method, every caller. | Weak. Each script either duplicates the rule or calls a shared procedure that grows unwieldy. | Moderate. A shared module method is callable from anywhere, but per-row nuance is awkward. | Moderate. A model method is reusable, but cross-table rules push logic back into services. |
| Mapping and infrastructure cost | High. Usually needs a dedicated Data Mapper and Unit of Work. | Low. SQL is written by hand at the call site, no separate mapping layer required. | Low to moderate. One module per table, mapping is close to direct. | Low. The mapping is built into the base class by convention. |
| Team skill floor required | High. Real object-oriented design skill needed or the model degenerates. | Low. Procedural thinking is enough. | Low to moderate. | Low to moderate. |
| Testability of business rules in isolation | Strong, once infrastructure is kept out of constructors. | Weak. Rules are entangled with the transaction and often with the web framework. | Moderate. Static methods are testable but often still coupled to a shared connection. | Moderate. Testing usually drags in the persistence layer unless deliberately isolated. |
| Report and analytical-query friendliness | Weak. Traversing a rich object graph for wide aggregate reads is expensive, and direct SQL usually bypasses the domain layer for this. | Moderate. Hand-written queries can be tuned per report. | Strong. Table-shaped operations map naturally onto SQL aggregates. | Moderate. |
| Serialisation across process or network boundaries | Weak without an added DTO layer, since circular associations and behaviour resist naive serialisation. | Strong. Procedures typically already work with flat, serialisable data. | Moderate. | Moderate. Framework serializers usually handle the flatter shape reasonably. |

## 13. Related and incompatible patterns

- **Transaction Script (Fowler 2002, p. 110 to 115).** The direct alternative
  for the same layer, domain logic. Fowler frames the choice between the two
  as the single most important architectural decision for the domain logic
  layer of an application, and treats them as effectively mutually exclusive
  as the dominant style for a given codebase, though a large system commonly
  has pockets of each (simple CRUD screens done as Transaction Script inside a
  codebase whose core is Domain Model). Listed as incompatible above in the
  sense of "not both as the primary style for the same responsibility", not in
  the sense of "can never coexist in one codebase".
- **Table Module (Fowler 2002, p. 125 to 130).** A middle-ground alternative
  that groups behaviour by table rather than by individual row identity.
  Table Module composes poorly with Domain Model because they organise
  behaviour on two different axes (per-table static methods versus per-object
  instance methods). A codebase generally picks one, not both, for the same
  data.
- **Active Record (Fowler 2002, p. 160 to 166).** Closely related to the
  Simple Domain Model shape. The difference is whether persistence methods
  live on the domain object itself (Active Record) or are pulled out into a
  separate Data Mapper (Domain Model proper). Many real codebases blend the
  two deliberately, as noted in dimension 8.
- **Data Mapper (Fowler 2002, p. 165 to 174).** The most common pairing for
  the Rich Domain Model shape. Data Mapper's entire reason to exist is to let
  a domain object stay ignorant of how it is persisted, which is precisely
  what unlocks the richer object graphs Domain Model benefits from.
- **Unit of Work (Fowler 2002, p. 184 to 189).** Tracks which domain objects
  changed during a request or transaction so the mapping layer issues the
  right writes at the right moment. Almost always paired with Data Mapper and
  Domain Model together.
- **Repository (Fowler 2002, p. 322 to 325, also Evans 2003, chapter 6).**
  Provides the collection-like facade over aggregate roots that lets
  application code avoid talking to the mapping layer directly.
- **Specification (Fowler with Rice, Foemmel, Hieatt, Mee, Stafford, in the
  same catalog family, also Evans 2003, chapter 9).** A composable predicate
  object frequently used to express selection or eligibility rules on domain
  objects without embedding query concerns directly into the domain object's
  own methods.
- **Factory Method (see this repository, 01-design-patterns-gof).** Frequently used to
  construct domain objects, particularly Entities that must be created with a
  valid identity or must enforce invariants at construction time that a bare
  constructor cannot conveniently express.
- **Domain Event (Evans's later work and the DDD community, not in Fowler's
  original catalog).** Composes naturally with Domain Model as the mechanism
  by which a domain object announces a state change to interested listeners
  without the domain object needing to know who those listeners are.
- **Anemic Domain Model (Fowler's bliki, not a catalog pattern, an explicitly
  named anti-pattern).** The failure mode Domain Model degenerates into when
  behaviour is stripped out and only data survives on the objects, see
  dimension 11.

## 14. Refactoring path in and out

Introducing Domain Model into a Transaction Script codebase, step by step.

1. Identify one business rule that currently appears in more than one script,
   or one rule that is complex enough that it is hard to reason about inline.
   Do not attempt to convert the whole codebase at once.
2. Introduce a domain class for the concept the rule is about (`Order`), even
   if, at first, that class only wraps the raw row data being passed around.
   This step alone is Fowler's Introduce Parameter Object taken one step
   further, into a real domain type rather than a bag of fields.
3. Move the specific rule's logic from the scripts into a method on the new
   domain class, using Move Method (Martin Fowler, *Refactoring. Improving the
   Design of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 8,
   "Moving Features Between Objects"). Replace each script's inline
   conditional with a call to the new method.
4. Where the rule needs collaborators (another entity, a value like `Money`),
   introduce those as proper domain types rather than passing primitives, to
   avoid Primitive Obsession (Fowler, *Refactoring*, chapter 3, "Smells").
5. Once several rules live on the domain object, separate persistence
   responsibility out into a mapping layer (Data Mapper) if it is not already
   separate, so the domain object's constructor and methods stay free of
   infrastructure calls.
6. Repeat for the next rule, expanding the domain model incrementally. Fowler
   explicitly recommends this incremental approach over a rewrite. A codebase
   is allowed to have both styles present simultaneously during the
   transition, and often permanently, for parts that never needed the richer
   model.

Removing Domain Model when it stops earning its place (most often because a
subsystem's rules turned out to be simple after all, or because the team never
had the object-oriented design capacity the pattern assumes).

1. Confirm the rules on the domain object are genuinely simple (few
   branches, little interaction between rules) before starting. Removing a
   rich model that is still earning its complexity cost is a mistake in the
   other direction.
2. Inline each domain method back into its single caller if there is only one
   caller, using the reverse of Move Method.
3. Where a method is still called from multiple places, keep it as a shared
   procedure (a plain function or a stateless service) rather than reinventing
   per-caller duplication. This produces Transaction Script with a small
   amount of shared procedural helpers, not a return to fully duplicated
   logic.
4. Flatten the object graph back toward the persistence schema shape,
   collapsing Data Mapper indirection where it is no longer earning its cost,
   moving toward Active Record or Table Module as appropriate for the reduced
   complexity.

## 15. Testing and verification

What gets easier is this. Individual business rules can be unit tested by
constructing a domain object directly, in memory, with no database, no web
framework, and no test container, and asserting the outcome of calling a
behaviour method. Because state and behaviour live together, a test can set up
exactly the preconditions a rule needs (`Order` in `PLACED` status, one
returnable `LineItem`) without needing to fake an entire request pipeline.

What gets harder is this. Integration tests that exercise the mapping layer
grow in scope, because a rich object graph with lazy associations and
bidirectional references is a larger surface to verify than a flat
row-to-object mapping. Tests that assert the whole graph persisted correctly
tend to be slower and more brittle than the equivalent Transaction Script
test, which only ever has to assert that the one query it wrote produced the
expected rows.

Techniques that apply.

- **In-memory Fake Repository** (a test double implementing the repository
  interface backed by a plain collection) for testing application-layer
  orchestration without a real database, keeping domain-rule tests and
  persistence-integration tests as two clearly separate test suites.
- **Object Mother or Test Data Builder** for constructing valid domain objects
  in tests without repeating long constructor argument lists across many test
  methods, particularly valuable once Entities have several required Value
  Objects as collaborators.
- **Contract or characterization tests against the real mapping layer**,
  separate from the domain-rule unit tests, specifically to catch the
  object-relational mismatch failures (dimension 11's N+1 and stale-graph
  symptoms) that pure in-memory domain tests cannot see, because those
  symptoms live in the mapping layer, not in the domain object's logic.
- **Mutation testing on the domain layer specifically**, because the whole
  point of the pattern is concentrating business-rule branches in one place,
  which makes that layer the highest-value target for mutation testing to
  confirm the test suite actually exercises every branch rather than merely
  achieving line coverage.

## 16. Observability signals

A healthy Domain Model deployment shows a stable, low, roughly constant number
of SELECT statements per logical transaction regardless of load, with no N+1
growth as data volume grows. Write-path latency stays dominated by the actual
business logic rather than by query count, and application-level metrics or
logs are emitted from the domain layer itself, tagged with the domain concept
name (an `OrderCancelled` domain event logged with the order id and the
reason, rather than a generic "row updated" log line from the persistence
layer).

A failing instance shows the opposite pattern. Query count per request scales
with the size of an object graph rather than staying constant, which is the
N+1 signature from dimension 11, visible directly in a query log or an APM
trace waterfall as many nearly identical single-row queries clustered right
after a single logical operation. Memory growth correlates with request
volume, which usually indicates a first-level cache (an Identity Map or a
persistence-context session) that is never cleared between logical units of
work, and stack traces in error logs terminate inside deeply nested delegation
chains with no domain-level context attached, which indicates the domain
layer is not logging or raising domain-named exceptions and is instead
letting generic infrastructure exceptions (a raw SQL exception, a null
pointer from an un-navigated association) surface directly to the caller.

Recommended instrumentation emits a structured log or metric at the boundary
of every domain event or state transition (order placed, order cancelled,
credit limit exceeded), tagged with the aggregate's identifier. This gives
operators a domain-shaped audit trail independent of whatever the persistence
layer happens to log, and it is frequently the artifact that later becomes
formal Domain Event support if the codebase adopts event sourcing.

## 17. Security and privacy implications

Domain Model's most direct security implication is where authorization checks
belong. Because the pattern encourages putting business rules on the domain
object, there is a recurring temptation to put authorization checks there too
(can this user cancel this order), which conflates two different concerns,
business eligibility (is the order in a cancellable state) and access control
(is the caller allowed to cancel it). The engineering judgement here, stated
plainly as judgement rather than a sourced fact, is that authorization
generally belongs at the application or service layer, which knows who the
caller is, while the domain object should express business eligibility only
and remain ignorant of the current user or session. Conflating the two tends
to leak authorization logic across many domain classes and makes a security
review harder because there is no single place to audit.

A second implication concerns Value Objects that hold sensitive data (an
`Address`, a `PaymentCard` value type). Because Value Objects are commonly
compared by value and freely passed around the object graph, sensitive fields
inside them can end up in more log statements, more serialised payloads, and
more equality comparisons than a single scalar field would, simply because the
whole Value Object tends to travel together. Domain objects that wrap
sensitive fields should implement redacted `toString` or equivalent
representations deliberately, rather than relying on a framework's default
object dump, which frequently includes every field.

Third, a rich, deeply-associated object graph increases the blast radius of an
insecure deserialization vulnerability if domain objects are ever directly
deserialized from an untrusted source (a message queue payload, a client
request body mapped straight onto a domain Entity rather than onto a
dedicated, narrower DTO). This is not a defect specific to Domain Model, but
the pattern's encouragement of rich, behaviour-bearing graphs makes the
consequence of an untrusted deserialization path larger than it would be for
a flat data structure, because deserializing an Entity can trigger
constructor or setter logic with side effects the untrusted payload controls.
The mitigating practice, standard rather than specific to this pattern, is to
deserialize untrusted input into a dedicated DTO and construct or validate the
domain object explicitly from that DTO, never deserialize directly onto a
domain Entity.

This pattern stays silent on several concerns. Domain Model makes no claim
about transport encryption, credential storage, or injection defence. Those
remain the concern of whichever infrastructure layer handles network
transport and persistence, independent of whether the domain logic layer
above it uses Domain Model, Transaction Script, or Table Module.

## 18. References

1. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002. Domain Model entry, chapter 9, page 116 to 122.
   Data Mapper, chapter 10, page 165 to 174. Unit of Work, chapter 10, page
   184 to 189. Repository, chapter 10, page 322 to 325. Value Object, chapter
   18, page 486 to 487. Identity Map, chapter 18, page 216 to 217.
2. Martin Fowler, "Domain Model", PoEAA online catalog,
   https://martinfowler.com/eaaCatalog/domainModel.html, verified 2026-08-02.
3. Martin Fowler, "AnemicDomainModel", bliki,
   https://martinfowler.com/bliki/AnemicDomainModel.html, verified
   2026-08-02.
4. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003. Entity and Value Object, chapter 5.
   Aggregate, chapter 6. Specification, chapter 9. Ubiquitous Language,
   chapter 2.
5. Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
   edition, Addison-Wesley, 2018. Move Method, chapter 8. Primitive Obsession
   smell, chapter 3.
6. Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018, Item 1.
7. Spring Framework reference documentation, "Data Access",
   https://docs.spring.io/spring-framework/reference/data-access.html,
   verified 2026-08-02.
8. Hibernate ORM documentation, https://hibernate.org/orm/documentation/,
   verified 2026-08-02.
9. Domain Language, DDD reference material, https://domainlanguage.com/ddd/,
   verified 2026-08-02.
10. Ruby on Rails Guides, "Active Record Basics",
    https://guides.rubyonrails.org/active_record_basics.html, verified
    2026-08-02.
11. JavaMoney / JSR 354 project, https://javamoney.github.io/, verified
    2026-08-02.

## Code examples

The pattern is illustrated with the same scenario, an `Order` that can be
cancelled subject to its own business rule, in TypeScript, Python, and Java.
All three were compiled or executed against this scenario before inclusion.
C#, Kotlin, and C++ are omitted because those toolchains were not confirmed
available in this environment. Go and Rust are omitted from the code samples
because their idiomatic style for this pattern leans toward the functional
core variant noted in dimension 8 (a plain struct plus free functions,
already covered in that dimension's prose) rather than adding a fourth
near-identical class-based translation of the same three-language example.

### TypeScript

```typescript
type OrderStatus = "PLACED" | "SHIPPED" | "CANCELLED";

class Money {
  constructor(readonly cents: number, readonly currency: string) {}
  add(other: Money): Money {
    if (other.currency !== this.currency) {
      throw new Error("currency mismatch");
    }
    return new Money(this.cents + other.cents, this.currency);
  }
}

class LineItem {
  constructor(readonly sku: string, readonly price: Money, private returnable: boolean) {}
  isReturnable(): boolean {
    return this.returnable;
  }
}

class Order {
  private status: OrderStatus = "PLACED";
  private placedAt: Date;

  constructor(readonly id: string, private lineItems: LineItem[], placedAt: Date) {
    this.placedAt = placedAt;
  }

  total(): Money {
    return this.lineItems.reduce(
      (sum, item) => sum.add(item.price),
      new Money(0, this.lineItems[0]?.price.currency ?? "USD"),
    );
  }

  private withinCancelWindow(now: Date): boolean {
    const hoursSincePlaced = (now.getTime() - this.placedAt.getTime()) / 3_600_000;
    return hoursSincePlaced <= 24;
  }

  cancel(now: Date): void {
    if (this.status !== "PLACED") {
      throw new Error(`cannot cancel an order in status ${this.status}`);
    }
    if (!this.withinCancelWindow(now)) {
      throw new Error("cancellation window has closed");
    }
    if (this.lineItems.some((item) => !item.isReturnable())) {
      throw new Error("order contains a non-returnable line item");
    }
    this.status = "CANCELLED";
  }

  currentStatus(): OrderStatus {
    return this.status;
  }
}

function main(): void {
  const placedAt = new Date(Date.now() - 60_000);
  const order = new Order(
    "ord_1",
    [new LineItem("sku-1", new Money(1999, "USD"), true)],
    placedAt,
  );
  order.cancel(new Date());
  console.log(order.currentStatus(), order.total().cents);
}

main();
```

### Python

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List


@dataclass(frozen=True)
class Money:
    cents: int
    currency: str = "USD"

    def add(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise ValueError("currency mismatch")
        return Money(self.cents + other.cents, self.currency)


@dataclass(frozen=True)
class LineItem:
    sku: str
    price: Money
    returnable: bool = True


class Order:
    def __init__(self, order_id: str, line_items: List[LineItem], placed_at: datetime):
        self.id = order_id
        self._line_items = line_items
        self._placed_at = placed_at
        self._status = "PLACED"

    def total(self) -> Money:
        result = Money(0, self._line_items[0].price.currency if self._line_items else "USD")
        for item in self._line_items:
            result = result.add(item.price)
        return result

    def _within_cancel_window(self, now: datetime) -> bool:
        return now - self._placed_at <= timedelta(hours=24)

    def cancel(self, now: datetime) -> None:
        if self._status != "PLACED":
            raise ValueError(f"cannot cancel an order in status {self._status}")
        if not self._within_cancel_window(now):
            raise ValueError("cancellation window has closed")
        if any(not item.returnable for item in self._line_items):
            raise ValueError("order contains a non-returnable line item")
        self._status = "CANCELLED"

    @property
    def status(self) -> str:
        return self._status


def main() -> None:
    placed_at = datetime.now() - timedelta(minutes=1)
    order = Order("ord_1", [LineItem("sku-1", Money(1999, "USD"))], placed_at)
    order.cancel(datetime.now())
    print(order.status, order.total().cents)


if __name__ == "__main__":
    main()
```

### Java

```java
import java.time.Duration;
import java.time.Instant;
import java.util.List;

final class Money {
    final long cents;
    final String currency;

    Money(long cents, String currency) {
        this.cents = cents;
        this.currency = currency;
    }

    Money add(Money other) {
        if (!other.currency.equals(this.currency)) {
            throw new IllegalArgumentException("currency mismatch");
        }
        return new Money(this.cents + other.cents, this.currency);
    }
}

final class LineItem {
    final String sku;
    final Money price;
    final boolean returnable;

    LineItem(String sku, Money price, boolean returnable) {
        this.sku = sku;
        this.price = price;
        this.returnable = returnable;
    }
}

final class Order {
    enum Status { PLACED, SHIPPED, CANCELLED }

    private final String id;
    private final List<LineItem> lineItems;
    private final Instant placedAt;
    private Status status = Status.PLACED;

    Order(String id, List<LineItem> lineItems, Instant placedAt) {
        this.id = id;
        this.lineItems = lineItems;
        this.placedAt = placedAt;
    }

    Money total() {
        Money result = new Money(0, lineItems.isEmpty() ? "USD" : lineItems.get(0).price.currency);
        for (LineItem item : lineItems) {
            result = result.add(item.price);
        }
        return result;
    }

    private boolean withinCancelWindow(Instant now) {
        return Duration.between(placedAt, now).toHours() <= 24;
    }

    void cancel(Instant now) {
        if (status != Status.PLACED) {
            throw new IllegalStateException("cannot cancel an order in status " + status);
        }
        if (!withinCancelWindow(now)) {
            throw new IllegalStateException("cancellation window has closed");
        }
        for (LineItem item : lineItems) {
            if (!item.returnable) {
                throw new IllegalStateException("order contains a non-returnable line item");
            }
        }
        status = Status.CANCELLED;
    }

    Status getStatus() {
        return status;
    }
}

public class DomainModelDemo {
    public static void main(String[] args) {
        Instant placedAt = Instant.now().minusSeconds(60);
        Order order = new Order(
            "ord_1",
            List.of(new LineItem("sku-1", new Money(1999, "USD"), true)),
            placedAt
        );
        order.cancel(Instant.now());
        System.out.println(order.getStatus() + " " + order.total().cents);
    }
}
```
