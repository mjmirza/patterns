---
name: Anemic Domain Model
slug: anemic-domain-model
family: 18-anti-patterns
category: Anti-pattern
aliases: [Anaemic Domain Model, Data-Only Model, Bag of Getters and Setters, Naked Data Object]
first_described: "Fowler 2003"
maturity: canonical
related: [entity-service, active-record, repository, domain-model, transaction-script, value-object, aggregate, layered-architecture]
incompatible_with: [domain-model, aggregate]
verified: 2026-08-02
---

# Anemic Domain Model

## 1. Name, aliases, and lineage

The canonical name is Anemic Domain Model, spelled Anaemic Domain Model in
British sources. Martin Fowler named it in a short bliki entry, dated by his
own site metadata to 2003 and still hosted at its original address (Martin
Fowler, "AnemicDomainModel", https://martinfowler.com/bliki/AnemicDomainModel.html
verified 2026-08-02). Fowler opens the entry by describing objects "connected
with rich relationships and structure much like a real domain model" that on
closer inspection have "hardly any behavior," making them "little more than
bags of getters and setters," a phrase confirmed verbatim on the live page
(same source, verified 2026-08-02). He states the verdict directly, "The
fundamental horror of this anti-pattern," calling it "so contrary to the basic
idea of object-oriented design, which is to combine data and process
together" (same source, verified 2026-08-02).

Fowler credits the pattern's naming, in the same short piece, to a conversation
with Eric Evans, and both writers treat the anemic model as the thing Evans's
own book argues against. Eric Evans, *Domain-Driven Design. Tackling Complexity
in the Heart of Software*, Addison-Wesley, 2003, ISBN 0-321-12521-5, part 2,
chapter 5, "A Model Expressed in Software," pushes the opposite shape, a model
where the important logic sits with the objects it governs rather than in a
thin coordinating layer, and where a healthy domain layer keeps rules with the
objects that own the data those rules constrain.

Common aliases seen in practice are Data-Only Model, Bag of Getters and
Setters (drawn directly from Fowler's own phrasing above), and Naked Data
Object, used in some C# and Java shops for the same shape. The alias Anemic
Microservice appears in the sibling entry on Entity Service in this
repository, describing the same underlying failure at the scale of a whole
deployable service rather than a single class.

A distinction worth drawing at the outset. Anemic Domain Model is a
*structural* diagnosis, are behavior and the data it governs kept in the same
type or not. It is not the same complaint as a class with too many
responsibilities, that is God Object, and it is not the same complaint as
logic scattered across nested conditionals, that is Spaghetti Code. An anemic
model can be perfectly well organized, cleanly layered, and read easily front
to back, and still be an anemic model, because the organizing principle is
data first rather than behavior first.

## 2. Problem and context

A codebase reaches for persistence early. A relational table, a document
collection, or an external API schema defines the shape of a `Customer`, an
`Order`, an `Invoice`. An object-relational mapper, a serialization library,
or a code generator produces a class with one field per column and a getter
and a setter for each, because that mapping is mechanical and the tooling does
it well. The team then writes the actual business rules, an order cannot ship
without a valid address, a subscription cannot renew past its cancellation
date, an invoice total must equal the sum of its line items after tax,
somewhere else, typically in a class whose name ends in `Service` or
`Manager`. The domain object is passed into that service, its getters are
called to read state, its setters are called to write the result back, and it
never sees the rule itself.

This context recurs anywhere persistence-first thinking runs ahead of
behavior-first thinking. Three concrete triggers show up again and again.

- A framework's official tutorial, or its idiomatic path of least resistance,
  generates a POJO, a Plain Old CLR Object, or a struct from a schema, and the
  fastest way to add a feature is to add a method to a service that already
  exists rather than a method to the object the feature is actually about.
- The team is organized around a database-first workflow, a DBA or a data
  architect owns the schema, and application developers are handed generated
  entity classes they are not expected, or in some shops not permitted, to
  extend with behavior.
- A prior architecture decision, often unstated, treats "the domain objects"
  and "the business logic" as two different concerns that different layers or
  different people own, so a rule that touches two entities has no natural
  home on either one and lands in a coordinating service by default.

None of these triggers is malicious and none is stupid. Judgement. the anemic
shape is often the fastest thing to write on day one, which is exactly why it
recurs so reliably, and exactly why the cost only shows up later, once the
rule count grows past what a handful of service methods can hold cleanly. The
context in dimension 4 explains where that trade genuinely favours the anemic
shape and where it does not.

## 3. Forces

- **Persistence simplicity.** Favoured. A class that is only fields and
  accessors maps to a table, a JSON document, or a protobuf message with no
  friction, and every ORM, serializer, and schema generator on the market is
  built to produce and consume exactly that shape first.
- **Encapsulation.** Sacrificed. A public setter on every field means any
  caller anywhere in the codebase can put the object into a state its own
  rules would have forbidden, because the rules do not live on the object to
  forbid anything.
- **Discoverability of behavior.** Sacrificed. A reader who wants to know what
  can happen to an `Order` cannot open the `Order` class and find out. the
  answer is scattered across every service that happens to take an `Order` as
  a parameter, and there is no fixed place to look first.
- **Testability of pure logic in isolation.** Mixed. Judgement, not a sourced
  claim. A rule sitting in a stateless service with no framework dependency
  can be trivial to unit test, which is the strongest honest argument for the
  anemic shape, see dimension 4. The same rule sitting on a domain object with
  no framework dependency is exactly as easy to test, so the advantage
  disappears once the service is genuinely free of infrastructure concerns,
  and only survives where the service artificially avoids depending on the
  entity's own methods.
- **Consistency and invariants.** Sacrificed, and this is the sharpest edge.
  When a rule that must always hold, a total that must always equal its
  parts, lives in a service rather than the object, every new service that
  touches the object is a new opportunity to forget the rule, because nothing
  in the type system or the object's own contract stops a caller from
  skipping it.
- **Team topology and framework fit.** Favoured in specific organizations. A
  team split along a persistence-layer boundary, or a framework whose
  idiomatic style pushes logic outward, gets less friction from an anemic
  model, at the price of the encapsulation and consistency forces above.
- **Onboarding speed for a small, short-lived system.** Favoured. Judgement.
  A prototype, a short-lived reporting tool, or a CRUD admin panel over a
  handful of tables rarely benefits from the discipline a rich model imposes,
  and paying that cost early is itself a form of waste, see dimension 4.

An anemic model gives up almost everything a rich model buys, encapsulation,
discoverability, protected invariants, in exchange for mapping simplicity and
a shallow learning curve. That trade is a genuine win in a narrow context and
a genuine liability everywhere else, which is why this entry treats it as an
anti-pattern rather than as one option among equals.

## 4. Applicability and non-applicability

There is no context in which "Anemic Domain Model" is the name of a deliberate
choice a team should reach for and be proud of, the way a team reaches for
Strategy or Builder. It is named as an anti-pattern because it is what happens
by default when nobody chooses anything. That said, the shape it describes,
plain data objects with logic held elsewhere, is a legitimate and often
correct choice under a different name, and drawing the line honestly matters
more than repeating the anti-pattern label everywhere data and behavior are
separate.

The shape is acceptable, and arguably correct, when the following hold.

- The object genuinely has no invariants to protect. a read-only projection,
  a DTO crossing a network boundary, a row in a reporting table nobody ever
  mutates through the domain. There is nothing to encapsulate because there
  is no rule that could be violated.
- The "logic" that would otherwise live on the object is pure orchestration
  across several unrelated objects, not a rule that belongs to any one of
  them. Coordinating three independent aggregates in one business transaction
  is honestly a service's job, not any one entity's job, and forcing that
  coordination onto one of the participants produces a different anti-pattern,
  an entity pretending to own logic it does not actually own.
- The system is short-lived, small, or explicitly a script, and the cost of
  richer encapsulation, more types, more discipline about where a setter is
  called from, is not going to be repaid before the system is retired.
- CQRS query-side read models, described independently in this repository's
  Command Query Responsibility Segregation entry, where read models exist
  purely to be shaped for a query and are recreated wholesale, never mutated
  in place. Calling a pure read projection anemic is a category error, it was
  never meant to carry behavior.
- The team has deliberately chosen a Transaction Script organization for a
  genuinely simple domain, described in this repository's Transaction Script
  entry, and is not also paying for the machinery of a domain model, an ORM
  mapping layer, a repository per aggregate, on top of it. Anemic Domain
  Model is specifically the anti-pattern of paying domain-model overhead
  while getting transaction-script benefit, see dimension 10, so a genuine,
  consistently applied Transaction Script is not this anti-pattern at all.

Do NOT let the anemic shape stand, and treat it as the anti-pattern it is
named for, when any of these hold.

- **The object has invariants that more than one caller must respect.** If
  two different services can independently set an `Order`'s status, and only
  one of the two remembers to check that a cancelled order cannot be marked
  shipped, the anemic shape has already produced a live bug, not a
  theoretical risk.
- **The rule is intrinsic to the entity's own state, not a coordination
  between entities.** A total that must equal the sum of line items, a date
  range that must not overlap another date range on the same resource, a
  balance that must never go negative, these belong on the object whose
  fields they constrain, not in a service that happens to be the one place
  someone remembered to write the check.
- **The team is paying full domain-model overhead already.** A repository per
  aggregate, an ORM with change tracking, a unit-of-work per request, event
  sourcing or domain events, and the entities that machinery moves around
  carry no logic. This is precisely the case Fowler names when he writes that
  the anemic model "incurs all of the costs of a domain model, without
  yielding any of the benefits" (Fowler, cited above, verified 2026-08-02).
  If the mapping machinery is being paid for, the behavior should be too, or
  a cheaper Transaction Script over plain rows would have done the same job
  for less.
- **The framework's official guidance is being followed uncritically as a
  reason not to add a method.** A framework encouraging plain, mappable
  objects is a real and legitimate constraint on a persisted entity's shape,
  see dimension 8 for how Aggregate Roots handle this without going anemic.
  It is not, by itself, a reason to also strip every rule the entity should
  own out of the class and into a service.

## 5. Structure

An anemic model has, in effect, only one participant instead of the usual
two or three a rich alternative would show. Naming the missing participants
by the role they fail to play is the clearest way to see the shape.

- **Data Holder.** The class most people mean when they say "the domain
  model." Carries every field the persistence layer needs, exposes a public
  getter and a public setter for each, and declares no method that changes
  more than one field together or enforces a relationship between fields. Its
  invariants, if it has any on paper, exist only as comments or as validation
  that runs somewhere else, never as code the type itself refuses to violate.
- **Anemic Service (the missing home for behavior).** A stateless class, one
  per use case or per aggregate, holding every method that reads or writes
  more than one field of a Data Holder, or that coordinates several Data
  Holders. This is where the "fundamental horror" that Fowler names actually
  lives, not inside the Data Holder itself. The service both knows the rule
  and is the only thing capable of enforcing it, which means the rule holds
  exactly as often as every caller remembers to go through this particular
  service rather than mutating the Data Holder directly.
- **The missing Rich Domain Object.** What a Factory Method or a plain
  constructor would produce in a healthy design, an object that owns its
  fields as private state and exposes only the operations that are valid to
  perform on it, each one keeping its own invariants intact. Naming this
  participant even though it is absent is the point of listing it here. the
  anti-pattern is precisely the gap where this object should exist and does
  not.
- **Direct Callers.** Any code, a controller, a batch job, a test, another
  service, that reaches a Data Holder's setters directly rather than through
  a behavior-carrying method. In an anemic model every caller is, by
  definition, a Direct Caller, because there is no other kind of access
  available.

## 6. ASCII structure diagram

```
ANEMIC SHAPE, the anti-pattern

+-----------------+
| OrderController |
| BatchJob        |
| AnyOtherCaller  |
+-----------------+
     | called by
     v
+----------------------------+
| OrderService               |
| + placeOrder(order)        |
| + cancelOrder(order)       |
| + addLineItem(order, item) |
| + recalculateTotal(order)  |
+----------------------------+
     | reads/writes every field via getters/setters,
     | no encapsulation enforced by Order
     v
+-----------------------------------------------+
| Order (Data Holder)                           |
| - id                                          |
| - lineItems                                   |
| - status                                      |
| - total                                       |
| + getId(), getLineItems(), setLineItems(list) |
| + getStatus(), setStatus(status)              |
| + getTotal(), setTotal(amount)                |
+-----------------------------------------------+

Any caller can also mutate a field directly, bypassing
OrderService entirely, since no rule is enforced.

RICH ALTERNATIVE, what dimension 14 refactors toward

+---------------------------------------------------+
| Order (Rich Entity)                               |
| - id                                              |
| - lineItems  (private)                            |
| - status     (private)                            |
| + addLineItem(item)   enforces: not after shipped |
| + cancel()            enforces: not after shipped |
| + total(): Money      always derived, never stale |
+---------------------------------------------------+
```

## 7. Dynamics

The runtime story of an anemic model is the story of state that changes
outside the object's own control. Two callers acting on the same object with
no shared coordination, other than remembering to call the right service, is
the situation that produces the class of bug this anti-pattern is most often
blamed for.

```
Caller A (Controller)      OrderService                Order (Data Holder)
     |                          |                              |
     |-- cancelOrder(order) --->|                              |
     |                          |-- order.getStatus() -------->|
     |                          |<-- "PENDING" ----------------|
     |                          |-- checks: PENDING can cancel |
     |                          |-- order.setStatus(CANCELLED)>|
     |                          |                              |
     |                          |                              |
Caller B (BatchJob)              |                              |
     |                                                          |
     |-- order.setStatus(SHIPPED) directly, no service call --->|
     |    (compiles fine, the setter is public, nothing on      |
     |     Order itself objects to a CANCELLED order becoming   |
     |     SHIPPED, because Order enforces no rule at all)      |
     |                                                          |
     |<-- order.getStatus() now reports "SHIPPED" --------------|
     |    (the cancellation Caller A performed a moment earlier |
     |     has been silently overwritten, and nothing in the    |
     |     system noticed, because the invariant "a cancelled   |
     |     order cannot ship" was never anyone's job to check   |
     |     except OrderService.cancelOrder's own caller)        |
```

Contrast that with the rich alternative. Caller B would have had to call
`order.ship()`, and a rich `ship()` method is exactly the place a status
transition guard belongs, so the same mistake becomes a thrown exception at
the point of the mistake rather than a silent overwrite discovered later, if
it is discovered at all.

## 8. Implementation variants

**The textbook anemic form.** Every field public through a getter and a
setter, one class per table, zero domain methods. Rare in its purest form in
real code, because most teams add at least a handful of convenience methods
over time, but it is the form every framework tutorial's first example takes.

**The "almost rich" form, the most common real variant.** The class has a
few methods that look like behavior, `isOverdue()`, `getDisplayName()`, but
every method that would need to *change* more than one field, the ones that
actually enforce a rule, is still missing, and setters remain public for
every field regardless. This is the form most production Java, C#, and Ruby
on Rails codebases with a Service or Manager layer actually converge on, and
it is worth naming separately because it is easy to mistake for a rich model
on a quick read, since it does have some methods.

**Framework-imposed anemia.** Some persistence frameworks require a
no-argument constructor and public setters for every mapped field to build
an instance from a result set or a deserialized payload, which historically
pushed teams toward public setters even when they wanted encapsulation.
Modern ORMs largely lift this constraint. Hibernate and JPA can populate
private fields through reflection without exposing a public setter, and
constructor binding in frameworks such as Spring Data JDBC and Micronaut Data
builds an entity through its constructor directly, so the framework
justification for public setters is considerably weaker today than it was in
the mid-2000s Java EE era Fowler was writing about, though it is still cited
as a reason in Spring tutorials, as discussed in dimension 9.

**The service-layer split by responsibility rather than by entity.** Some
teams that produce anemic entities are careful to give each service a single
responsibility, `OrderPricingService`, `OrderShippingService`, rather than
one giant `OrderService` doing everything. This mitigates the God Object risk
that anemic models otherwise invite, since logic is at least organized by
concern, but it does not address the underlying anti-pattern, because the
`Order` object still enforces none of its own invariants and every service
can still mutate it directly.

**Value Object islands inside an otherwise anemic entity.** A partial and
genuinely useful middle ground. The entity's identity fields and lifecycle
stay anemic, plain getters and setters for `id`, `createdAt`, and similar,
while a specific piece of state that has real invariants, a `Money` amount, an
`EmailAddress`, a `DateRange`, is pulled out into its own immutable Value
Object that validates itself on construction. This does not fix the entity's
missing lifecycle rules, but it does close the specific class of bug where an
invalid or inconsistent value gets assigned to a single field, and it is
often the cheapest first step described in dimension 14.

## 9. Known production uses

Naming a production system as anemic is naming a criticism of that system,
not a recommendation, and the sources below are documented critiques of real,
widely deployed shapes rather than praise for a good design.

**J2EE Entity Beans (EJB 2.x), cited by Fowler as an originating cause.**
Fowler's own bliki entry names the technology directly. "Some technologies
encourage it; such as J2EE's Entity Beans which is one of the reasons I
prefer POJO domain models" (Fowler, "AnemicDomainModel," cited above,
verified 2026-08-02). Entity Beans required a container-managed persistence
contract with abstract getter and setter pairs and forbade meaningful
constructor logic, which pushed application logic for the entity's rules
into separate Session Bean classes across a large share of early 2000s
enterprise Java systems.

**Typical Spring plus JPA or Hibernate enterprise applications, documented
across multiple independent sources.** Petri Kainulainen, in "The Biggest
Flaw of Spring Web Applications," argues that "Spring enforces an anaemic
domain model" in the way its official tutorials are written, because
"official Spring tutorials teach us that domain objects shouldn't have any
methods except getters and setters, and they should be POJOs"
(Petri Kainulainen, https://www.petrikainulainen.net/software-development/design/the-biggest-flaw-of-spring-web-applications/
verified 2026-08-02). A separate, independently authored DZone article,
"Anemic Domain Model in Typical Spring Projects," documents the same shape
recurring across many Spring codebases it surveys, tying the recurrence
directly to how JPA entities are conventionally written as bags of getters
and setters (DZone, "Anemic Domain Model in Typical Spring Projects (Part 1),"
https://dzone.com/articles/anemic-domain-model-in-typical-spring-projects-1
verified 2026-08-02).

**Rails applications that push all logic into service objects, documented
across the Ruby community's own corrective literature.** The widely
circulated Rails guidance "Fat Model, Skinny Controller" exists specifically
because a large share of real Rails codebases push business logic out of
`ActiveRecord::Base` subclasses and into controllers or standalone service
objects, leaving the model itself, despite ActiveRecord's own design
supporting rich behavior, effectively anemic in practice. The corrective
pattern is well enough established that it has its own name in Rails
community writing and forms the basis of the "service object" debate that
recurs across Ruby conference talks and style guides, independent of any
single named production system.

Judgement, not sourced. these three cases share a pattern worth naming, in
each one the *framework itself* is not the cause, all three, EJB 2.x's
successor JPA, plain Spring, and ActiveRecord, support rich entities today.
The anemic shape persists because it is the path of least resistance the
tutorials and the generated scaffolding show first, and because the cost of
the anti-pattern stays invisible until the invariant it fails to protect is
actually violated in production.

## 10. Consequences

Positive, and genuinely positive within the narrow context of dimension 4.

- Mapping to and from a relational table, a wire format, or a document store
  is close to free, since the object's shape already matches the schema.
- A new team member with no domain knowledge can read and modify a Data
  Holder immediately, because there is nothing to learn about invariants, the
  object enforces none.
- Serialization libraries, reflection-based frameworks, and code generators
  work with zero customization, since public getters and setters are exactly
  what they expect.
- A pure, framework-free service method is trivially easy to unit test in
  isolation, which is a real strength when the alternative would have coupled
  the same logic to a framework-heavy entity base class.

Negative, and these compound as the system grows.

- **Invariants are advisory, not enforced.** Any caller with a reference to
  the object can put it into a state its own business rules would forbid,
  because the object has no code that would refuse.
- **Rules duplicate or drift.** When the same check needs to happen in two
  different services, and the object cannot enforce it once for everyone, the
  two copies are written independently and, over the life of the system,
  independently edited, until they disagree.
- **The domain knowledge is invisible from the type.** A reader who wants to
  know everything an `Order` can legally do cannot answer that question by
  reading `Order`, they must find every service that happens to reference it,
  which does not show up in an IDE's "find usages" on the class in any
  organized way.
- **Fowler's stated cost applies literally.** "They incur all of the costs of
  a domain model, without yielding any of the benefits" (Fowler, cited above,
  verified 2026-08-02). the ORM mapping complexity, the change-tracking
  machinery, the aggregate boundary discipline are all still being paid for,
  while the actual payoff of a domain model, safety by construction, is not
  being collected.
- **Procedural design under an object-oriented label.** The system reads as
  object-oriented, classes, methods, an ORM, while behaving as a procedural
  system organized around top-level functions that happen to be attached to
  a `Service` class rather than a module. Fowler names this directly, calling
  it "so contrary to the basic idea of object-oriented design" (same source,
  verified 2026-08-02), and the practical cost is that the object-oriented
  tooling, polymorphism, encapsulation, inheritance where it genuinely helps,
  is present in the language but unused in the design.

## 11. Failure modes and misuse

**Silent invariant violation across two callers.** Symptom. A record in
production is found in a state that should be impossible, a shipped order
with zero line items, a cancelled subscription that still shows an active
renewal date, and no single code path is obviously at fault. Cause. Two
different services independently mutate the same Data Holder's fields, and
neither one is aware the other exists or that a rule connects the two
fields. Fix. Move the rule onto the entity as a method that changes both
fields together and refuses the change when the precondition fails, per
dimension 14.

**God Service accumulating unrelated behavior.** Symptom. A single
`OrderService`, `UserManager`, or `AccountHelper` class grows to thousands of
lines and hundreds of methods, none of which fit together conceptually
except that they all take the same entity type as a parameter. Cause. Every
rule about the entity has exactly one legal home, since the entity itself
refuses none of them, so all of them accumulate in whichever service class
was created first. Fix. Split behavior back onto the entities it actually
concerns, and where genuine cross-entity coordination remains, keep it in a
narrowly scoped Application Service or Domain Service rather than one
catch-all class, per the Related Patterns section below.

**Validation duplicated at every entry point.** Symptom. The same
"quantity must be positive" or "email must contain an at-sign" check appears
in a controller, in a service, and in a database constraint, written three
separate times by three separate people, and at some point one of the three
gets updated for a new rule while the other two are missed. Cause. Because
the entity itself accepts any value through its setter, every caller that
wants correctness has to defend itself independently, since none of them can
rely on the entity having already refused an invalid value. Fix. Push
validation into the constructor or a factory method on the entity itself, so
an invalid instance cannot exist at all, per dimension 14.

**Anemic entities mistaken for a rich domain model in a design review.**
Symptom. A codebase reviewer sees a well-factored, cleanly layered
architecture, repositories, services, entities, DTOs, and concludes the
design is a proper Domain-Driven Design implementation, when in fact none of
the entities carry any behavior and the "domain layer" is Transaction Script
wearing DDD's file structure. Cause. Layering discipline and behavior
richness are two different axes, and good organization on one axis is easy
to mistake for the other. Fix. Ask the specific question from dimension 4,
does any entity refuse an invalid state through its own code, and treat "no"
as the honest answer regardless of how clean the folder structure looks.

**Half-migrated rich model that reintroduces the setter it just removed.**
Symptom. A refactor toward a rich model adds a well-designed `cancel()`
method to `Order`, and three months later a bug report traces back to a new
feature that called `order.setStatus(CANCELLED)` directly, because the
public setter was never actually removed and a new contributor did not know
the rich method existed. Cause. Dimension 14's refactoring path was started
but not finished, specifically its final step of removing the now-redundant
public setter. Fix. Complete the migration by making the setter private or
removing it, so the compiler, not code review vigilance, prevents the
regression.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Anemic Domain Model | Rich Domain Model | Transaction Script | Active Record | CQRS read model |
|---|---|---|---|---|---|
| Mapping to persistence | Trivial, matches schema directly | More friction, private fields need mapper support | Trivial, often raw rows | Trivial, the object is the row | Trivial, purpose-built for the query shape |
| Encapsulation of invariants | None, every field publicly settable | Strong, invariants enforced by construction | Not applicable, no persistent entity to protect | Moderate, methods can guard state but Rails convention rarely enforces this | Not applicable, read-only by design |
| Where the rule lives | In a service, disconnected from the data | On the entity, next to the data it governs | In a top-level procedure, explicit and linear | On the Active Record subclass itself | Nowhere, there is no rule, only a projection |
| Discoverability of behavior | Poor, scattered across every service | Good, read the class, see the operations | Good for a single script, poor across many scripts | Good, one class per table holds both data and behavior | Not applicable |
| Cost for a simple, short-lived system | Low, matches the effort the system deserves | High relative to the payoff | Lowest, no domain-model machinery paid for at all | Low to moderate | Low, purpose-built |
| Cost for a complex, long-lived system | High, invariant bugs accumulate silently | Moderate, paid once, amortized over the system's life | High, duplicated logic across scripts with no shared enforcement point | Moderate, risks becoming God Object as the table grows more responsibilities | Not applicable, this row only covers write-side complexity |
| Testability of business rules in isolation | Good if the service has no framework dependency | Good, test the entity directly with no framework | Good, test the procedure directly | Moderate, often requires the persistence framework to construct a valid instance | Not applicable |

Reading of the table. Anemic Domain Model loses to Rich Domain Model on every
force that matters once a system has real, multi-caller invariants, and it
loses to Transaction Script on honesty, a Transaction Script never pretends
to be paying for domain-model machinery it does not use. Its one genuine
advantage, low cost for a short-lived or invariant-free system, is exactly
the applicability case in dimension 4, and it stops being an advantage the
moment the system outgrows that case.

## 13. Related and incompatible patterns

- **Domain Model (Fowler's own, and the Gang of Four's object-oriented
  design generally).** The direct opposite. Anemic Domain Model is what
  Domain Model becomes when behavior is stripped out while the object
  structure is kept. Fixing the anti-pattern means moving toward this
  pattern, not abandoning objects altogether.
- **Aggregate, from Domain-Driven Design.** Composes with the fix. An
  Aggregate Root is precisely the entity that should carry the invariants an
  anemic model fails to protect, and the Aggregate's boundary tells a
  refactor exactly which fields belong on which object and which rules span
  more than one object, which answers the question dimension 14's first step
  asks.
- **Active Record.** A partial cousin, not a fix. Active Record puts
  persistence methods on the same class as the data, `save()`, `find()`,
  which superficially looks like the opposite of anemic, but the convention
  in most Active Record frameworks still favours public attribute writers
  with no invariant enforcement, so an Active Record class is very often
  anemic with respect to business rules even while it is rich with respect to
  persistence operations. See the sibling entry in this repository's Active
  Record entry for the full distinction.
- **Transaction Script.** A legitimate alternative, not a fix, when the
  applicability conditions in dimension 4 hold and the team commits to it
  consistently rather than paying for domain-model machinery on top of it.
  See dimension 12 for the direct comparison.
- **Entity Service.** The same anti-pattern one architectural layer up, an
  anemic entity exposed as its own network service rather than its own
  class, described in this repository's Entity Service entry, which lists
  Anemic Microservice as one of its own aliases.
- **God Object.** A frequent co-occurrence rather than a synonym. The
  service layer that accumulates every rule an anemic entity refuses to hold
  is a common route into God Object, described in the failure modes section
  above, though a God Object can arise without any anemic entity nearby.
- **Value Object.** Composes as a partial, incremental fix. Extracting a
  single invalid-state-impossible Value Object out of an otherwise anemic
  entity, per the Value Object islands variant in dimension 8, closes one
  slice of the problem without requiring a full rewrite.
- **Repository.** Neutral, neither cause nor cure. A Repository's job is to
  load and persist an aggregate, and it works identically well whether the
  aggregate it loads is anemic or rich, so the presence of a well-designed
  Repository layer says nothing about whether the entities behind it carry
  their own behavior.
- **Incompatible with a genuine Domain Model or a genuine Aggregate in the
  same codebase for the same entity.** the two are mutually exclusive
  descriptions of the same class, an `Order` cannot simultaneously be an
  anemic bag of setters and a rich aggregate root enforcing its own
  invariants. A codebase can, and often does, contain both a healthy rich
  model for one bounded context and an anemic model for a different, simpler
  one, which is not a contradiction, only two different applicability
  judgements made in two different places.

## 14. Refactoring path in and out

Because Anemic Domain Model is itself the anti-pattern, "refactoring in" is
not something to teach, it is what happens when nobody actively pushes
behavior onto the entity as features are added. The refactoring path worth
detailing runs the other direction, from an existing anemic model toward a
rich one, and it is deliberately incremental, since a big-bang rewrite of a
production entity's public surface is its own source of regressions.

1. **Find the invariant, not the method.** Before moving any code, list the
   rules an `Order` should never be allowed to violate, a shipped order
   cannot gain new line items, a cancelled order cannot ship, the total
   always equals the sum of its line items. This list, not the existing
   service methods, is the actual scope of the refactor.
2. **Introduce one new behavior-carrying method per invariant, alongside the
   existing setters, without removing anything yet.** Add `Order.cancel()`
   that checks the current status and throws or returns a result type on an
   invalid transition, while the old `setStatus()` setter is left in place.
   This is Extract Method plus Introduce Guard Clause, applied at the boundary
   between the entity and the service that used to own the rule, and it is
   the classic Encapsulate Field refactoring described in Martin Fowler,
   *Refactoring. Improving the Design of Existing Code*, 2nd edition,
   Addison-Wesley, 2019, ISBN 978-0134757599, chapter 11, in reverse, turning a
   field access back into a guarded operation.
3. **Move the calling service's logic into the new method's body, then
   replace the service's call site with a call to the new method.** The
   service that used to check `if (order.getStatus() == PENDING)` before
   calling `order.setStatus(CANCELLED)` now just calls `order.cancel()`
   and the check moves inside `Order` where it will be enforced for every
   future caller too, not only this one. Run the tests after this step for
   every rule migrated, not once at the end.
4. **Repeat step 2 and step 3 for every caller of the setter, across the
   whole codebase, before touching the setter itself.** A grep for
   `.setStatus(` across the repository is the honest way to confirm every
   caller has been migrated to the guarded method, not an assumption that the
   obvious call sites are the only ones.
5. **Once no caller uses the raw setter, remove it, or make it private.** This
   is the step the failure mode in dimension 11, "half-migrated rich model
   that reintroduces the setter it just removed," is warning against skipping.
   A setter that still exists, even unused, is a standing invitation for the
   next contributor to call it instead of the guarded method, since nothing
   stops them.
6. **Repeat for the next invariant on the list from step 1, one at a time,
   rather than attempting the whole entity in one change.** An entity with
   twelve invariants does not need to become fully rich in one pull request,
   and a partially migrated entity, where the highest-risk invariants are
   already enforced and the rest are still setter-based, is a strictly better
   state than the fully anemic starting point.

Refactoring out, when the applicability conditions in dimension 4 genuinely
hold, moving deliberately toward the anemic shape for a component that does
not need richness, is the reverse and considerably shorter.

1. Confirm the object truly has no multi-caller invariant, that every rule
   that currently exists on it is either read-only derivation or single-field
   validation that a constructor can still enforce.
2. Flatten any behavior-carrying method that does nothing but read and return
   a computed value back into a getter, if the computation is cheap and the
   method added no protective value beyond what a plain field would.
3. Keep the constructor or factory function as the single validation point
   even after flattening the rest, since dropping validation at construction
   time reopens the "invalid instance can exist" problem this whole entry is
   about, only at object-creation time instead of mutation time.

## 15. Testing and verification

An anemic model and its rich alternative are tested very differently, and the
difference is itself diagnostic. if a team cannot write a real unit test
against the entity class alone, without constructing a service, that is
direct evidence the entity carries no behavior worth testing, which is the
anemic shape confirmed from the test suite's own shape.

Testing the anemic model as it stands.

- Tests exist against the service class, constructing a Data Holder with a
  handful of setters, calling the service method, then asserting on the
  Data Holder's fields afterward through getters. This is a legitimate and
  necessary test, but note what it is testing, the service's procedure, not
  any guarantee the entity itself makes, because the entity makes none.
- A test that constructs the Data Holder directly and calls a setter with an
  invalid value, a negative quantity, an empty required field, and asserts
  nothing happens, no exception, no rejection, is not a bug in the test. it
  is an accurate demonstration that the anti-pattern is present, and such a
  test is worth writing explicitly during a design review as living proof of
  the gap, then deleting once the refactor in dimension 14 closes it.

Testing the rich alternative, and what changes as the refactor in dimension
14 proceeds.

- Each guarded method gets a direct, framework-free test. construct the
  entity in a valid starting state, call the method, assert either the new
  state or the thrown exception on an invalid transition. No service, no
  mock, no database is needed for this class of test, which is a genuine
  testability improvement, not a wash, contrary to the common claim that
  anemic models are equally testable, since the anemic version's "test" of
  the rule can only ever be an indirect test of whichever service happens to
  enforce it that day.
- A property-based test is a strong fit for the total-equals-sum-of-line-items
  class of invariant. generate a random sequence of `addLineItem` and
  `removeLineItem` calls and assert the invariant holds after every single
  one, rather than after one hand-picked sequence, which is exactly the kind
  of check an anemic model's scattered validation cannot express, because
  there is no single object whose state the property could be asserted
  against consistently.
- Golden-master or characterization tests over the service layer, run before
  the refactor begins and kept running throughout, are the safety net that
  makes the incremental migration in dimension 14 safe. every step from
  "call the setter" to "call the guarded method" should leave the service's
  observable behavior unchanged from the outside, which the characterization
  suite confirms without needing to know anything about the internal
  refactor.

## 16. Observability signals

An anemic model does not itself emit anything distinctive at runtime, since
by definition it has no behavior to instrument. The signals worth watching
are indirect, evidence of the consequences named in dimension 10 rather than
evidence of the pattern itself.

What to record and watch.

- A count, tagged by entity type and by the specific invariant, of times an
  invalid state was detected after the fact, a reconciliation job finding a
  shipped order with a mismatched total, a nightly integrity check finding a
  cancelled subscription still billing. A rising count here, for an entity
  that was recently confirmed to have no domain-level guard against exactly
  that state, is the clearest production-visible symptom this anti-pattern
  produces.
- A count of distinct call sites that mutate a given entity's fields directly,
  gathered statically rather than at runtime, is a useful one-time or
  periodic audit signal rather than a live metric, and is exactly what the
  grep in dimension 14 step 4 produces as a byproduct. Tracking this number
  over time, per entity, shows whether the migration toward a rich model is
  actually shrinking the anemic surface or merely adding new guarded methods
  alongside a setter surface that keeps growing too.
- Service-layer method duration and error-rate metrics, the standard ones any
  service already emits, are worth reading with an extra question in mind
  during triage. is this error a genuine external failure, or is it a
  business-rule violation that a rich entity would have refused before the
  service ever reached the point of failing. A high proportion of the second
  kind is itself a signal that logic belongs closer to the data than it
  currently sits.

A healthy state on a dashboard, once a migration per dimension 14 is under
way. the count of static call sites mutating an entity's raw fields trends
down release over release, the count of after-the-fact invalid states found
by reconciliation jobs trends toward zero for the invariants already migrated
to guarded methods, and it stays flat, rather than rising, for the invariants
not yet migrated, which at least confirms the anti-pattern is not actively
getting worse while the fix is in progress.

## 17. Security and privacy implications

The pattern is not itself a security control or a security hole, saying so
would invent a concern the anti-pattern does not directly create, but two
genuine implications follow from the missing encapsulation.

**Business-rule bypass as a privilege or authorization bug.** An invariant
that happens to double as an authorization boundary, a discount that must
never exceed a role-specific maximum, a balance that must never be
transferred below zero, a status transition that only a specific actor is
allowed to trigger, gets the same treatment as any other invariant in an
anemic model, unenforced by the object itself. Where the missing check
happens to be the only thing standing between a normal action and a
privilege escalation, the class of bug in dimension 11, "silent invariant
violation across two callers," becomes a security bug rather than merely a
data-integrity bug. The practical implication is that any invariant with a
security dimension is precisely the highest-priority candidate for the
refactor in dimension 14, since it is the one where "eventually consistent
with the rule" is not an acceptable failure mode.

**Broad, undifferentiated mutability widening the blast radius of an
injection or deserialization bug.** A Data Holder with a public setter for
every field is exactly as easy for an attacker-controlled deserialization
payload, a mass-assignment vulnerability, or a crafted API request to
overwrite as it is for legitimate application code, because nothing in the
object's own contract distinguishes a legitimate mutation from an
illegitimate one. A rich entity whose only mutation paths are guarded,
narrow methods narrows this same attack surface as a side effect of the
refactor in dimension 14, not because the refactor targets security
specifically, but because a guarded method that only accepts a valid status
transition cannot be tricked into accepting an arbitrary field value the way
a public setter can.

On privacy the pattern is neutral in itself. it neither widens nor narrows
what personal data an entity holds or exposes, and any privacy control, field
level access rules, redaction on serialization, needs to be layered on
independently of whether the entity is anemic or rich.

## Code examples

Three languages, each showing the anemic shape first and the fix it earns
second, since the anti-pattern is best illustrated as a before-and-after
rather than as a single static snippet. Go is included specifically because
its lack of classical inheritance and its convention of small, focused types
make the anemic-versus-rich distinction easy to see without any framework
noise. Java is left out of the runnable set here in favour of Python and Go
alongside TypeScript, because the Java example would repeat the same shape as
the TypeScript one with more ceremony and no new information, and Python
covers the dynamic-language, no-static-typing angle the other two do not.

### TypeScript

The anemic version, then the fix.

```typescript
// ANEMIC: every field publicly settable, no rule enforced by Order itself.
class Order {
  id: string;
  lineItems: { quantity: number; unitPrice: number }[] = [];
  status: "PENDING" | "SHIPPED" | "CANCELLED" = "PENDING";
  total = 0;

  constructor(id: string) {
    this.id = id;
  }
}

class OrderService {
  cancel(order: Order): void {
    if (order.status === "SHIPPED") {
      throw new Error("cannot cancel a shipped order");
    }
    order.status = "CANCELLED"; // enforced here, and only here
  }
}

// Nothing stops this from bypassing OrderService entirely:
const o = new Order("o1");
o.status = "SHIPPED";
o.status = "CANCELLED"; // silently violates the rule OrderService encodes
console.log("anemic bypass produced status:", o.status);
```

```typescript
// RICH: the rule lives on Order, every caller goes through it.
class RichOrder {
  private status: "PENDING" | "SHIPPED" | "CANCELLED" = "PENDING";
  private lineItems: { quantity: number; unitPrice: number }[] = [];

  constructor(private readonly id: string) {}

  addLineItem(item: { quantity: number; unitPrice: number }): void {
    if (this.status !== "PENDING") {
      throw new Error("cannot add a line item after the order left PENDING");
    }
    this.lineItems.push(item);
  }

  cancel(): void {
    if (this.status === "SHIPPED") {
      throw new Error("cannot cancel a shipped order");
    }
    this.status = "CANCELLED";
  }

  total(): number {
    return this.lineItems.reduce((sum, i) => sum + i.quantity * i.unitPrice, 0);
  }

  currentStatus(): string {
    return this.status;
  }
}

const rich = new RichOrder("o2");
rich.addLineItem({ quantity: 2, unitPrice: 9.5 });
rich.cancel();
try {
  rich.addLineItem({ quantity: 1, unitPrice: 3 });
} catch (e) {
  console.log("rich model refused:", (e as Error).message);
}
console.log("rich total:", rich.total(), "status:", rich.currentStatus());
```

### Python

```python
# ANEMIC: a plain dataclass with public attributes, no guard anywhere.
from dataclasses import dataclass, field


@dataclass
class Order:
    id: str
    status: str = "PENDING"
    line_items: list[tuple[int, float]] = field(default_factory=list)


class OrderService:
    def cancel(self, order: Order) -> None:
        if order.status == "SHIPPED":
            raise ValueError("cannot cancel a shipped order")
        order.status = "CANCELLED"


order = Order(id="o1")
order.status = "SHIPPED"
order.status = "CANCELLED"  # bypasses OrderService, no error, rule violated
print("anemic bypass produced status:", order.status)
```

```python
# RICH: the entity owns the rule, private state, guarded transitions.
class RichOrder:
    def __init__(self, order_id: str) -> None:
        self._id = order_id
        self._status = "PENDING"
        self._line_items: list[tuple[int, float]] = []

    def add_line_item(self, quantity: int, unit_price: float) -> None:
        if self._status != "PENDING":
            raise ValueError("cannot add a line item after the order left PENDING")
        self._line_items.append((quantity, unit_price))

    def cancel(self) -> None:
        if self._status == "SHIPPED":
            raise ValueError("cannot cancel a shipped order")
        self._status = "CANCELLED"

    def total(self) -> float:
        return sum(q * p for q, p in self._line_items)

    @property
    def status(self) -> str:
        return self._status


rich = RichOrder("o2")
rich.add_line_item(2, 9.5)
rich.cancel()
try:
    rich.add_line_item(1, 3.0)
except ValueError as e:
    print("rich model refused:", e)
print("rich total:", rich.total(), "status:", rich.status)
```

### Go

Go has no classical inheritance and no public/private field distinction
beyond package boundaries, which makes it a clean language to show the same
distinction with, since unexported fields plus exported methods are the
idiomatic Go shape for exactly this fix.

```go
package main

import (
	"errors"
	"fmt"
)

// ANEMIC: an exported struct with exported fields, callable from any package,
// with a Cancel function living outside the type and enforcing nothing that
// the struct itself would refuse if bypassed.
type AnemicOrder struct {
	ID     string
	Status string
	Total  float64
}

func CancelAnemicOrder(o *AnemicOrder) error {
	if o.Status == "SHIPPED" {
		return errors.New("cannot cancel a shipped order")
	}
	o.Status = "CANCELLED"
	return nil
}

// RICH: unexported fields, exported guarded methods. A caller in another
// package cannot reach status directly at all, the compiler enforces it.
type richOrder struct {
	id        string
	status    string
	lineItems []lineItem
}

type lineItem struct {
	quantity  int
	unitPrice float64
}

func NewRichOrder(id string) *richOrder {
	return &richOrder{id: id, status: "PENDING"}
}

func (o *richOrder) AddLineItem(quantity int, unitPrice float64) error {
	if o.status != "PENDING" {
		return errors.New("cannot add a line item after the order left PENDING")
	}
	o.lineItems = append(o.lineItems, lineItem{quantity, unitPrice})
	return nil
}

func (o *richOrder) Cancel() error {
	if o.status == "SHIPPED" {
		return errors.New("cannot cancel a shipped order")
	}
	o.status = "CANCELLED"
	return nil
}

func (o *richOrder) Total() float64 {
	sum := 0.0
	for _, li := range o.lineItems {
		sum += float64(li.quantity) * li.unitPrice
	}
	return sum
}

func main() {
	anemic := &AnemicOrder{ID: "o1", Status: "SHIPPED"}
	anemic.Status = "CANCELLED" // compiles fine, rule silently violated
	fmt.Println("anemic bypass produced status:", anemic.Status)

	rich := NewRichOrder("o2")
	_ = rich.AddLineItem(2, 9.5)
	_ = rich.Cancel()
	if err := rich.AddLineItem(1, 3.0); err != nil {
		fmt.Println("rich model refused:", err)
	}
	fmt.Println("rich total:", rich.Total())
}
```

All three examples were run locally. `npx tsc --strict --target es2020 --module commonjs anemic.ts && node anemic.js` compiled and ran the TypeScript sample with no errors, printing the expected bypass and refusal lines. `python3 anemic.py` and `python3 rich.py` ran the Python sample directly with no errors. `go run main.go` compiled and ran the Go sample with no errors, printing the expected bypass and refusal lines. Java was not compiled for this entry, since the TypeScript sample already covers the same static-typing, class-based shape the Java version would show, and the pattern's contrast is not tied to one language.

## 18. References

1. Martin Fowler. "AnemicDomainModel". Bliki, 2003.
   https://martinfowler.com/bliki/AnemicDomainModel.html
   Verified 2026-08-02. Source of the pattern name, the "bags of getters and
   setters" quote, the "fundamental horror" quote, the "incur all of the
   costs" quote, and the direct reference naming J2EE Entity Beans.
2. Eric Evans. *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*. Addison-Wesley, 2003. ISBN 0-321-12521-5. Part 2, chapter 5,
   "A Model Expressed in Software." Source for the healthy alternative this
   anti-pattern is defined against, and the naming conversation Fowler credits
   in his own entry.
3. Vaughn Vernon. *Implementing Domain-Driven Design*. Addison-Wesley, 2013.
   ISBN 978-0-321-83457-7. Chapter 5, "Entities," and chapter 7, "Services."
   Source for the discussion of Entities as "merely containers with getter and
   setter methods" and the link between Domain Service overuse and the anemic
   result.
4. Petri Kainulainen. "The Biggest Flaw of Spring Web Applications."
   https://www.petrikainulainen.net/software-development/design/the-biggest-flaw-of-spring-web-applications/
   Verified 2026-08-02. Source for the claim that Spring's own tutorials teach
   domain objects as POJOs with only getters and setters.
5. DZone. "Anemic Domain Model in Typical Spring Projects (Part 1)."
   https://dzone.com/articles/anemic-domain-model-in-typical-spring-projects-1
   Verified 2026-08-02. Source for the documented recurrence of the pattern
   across surveyed Spring codebases.
6. Wikipedia contributors. "Anemic domain model."
   https://en.wikipedia.org/wiki/Anemic_domain_model
   Verified 2026-08-02. Used only to confirm the general definition and the
   attribution to Fowler, not as a primary source of explanation.
7. Martin Fowler. *Refactoring. Improving the Design of Existing Code*, 2nd
   edition. Addison-Wesley, 2019. ISBN 978-0134757599. Chapter 11,
   "Encapsulate Field," and the surrounding Move Function catalog entries.
   Source for the refactoring vocabulary used in dimension 14.
8. This repository. `patterns/18-anti-patterns/entity-service.md`. Sibling
   entry describing the same failure at the granularity of a whole network
   service, and the source of the Anemic Microservice alias cross-referenced
   in dimension 1.
