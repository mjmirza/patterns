---
name: Factory
slug: factory
family: 11-domain-driven-design
category: Domain-Driven Design
aliases: [Domain Factory, Aggregate Factory, Factory Method on Aggregate Root]
first_described: "Evans 2003"
maturity: canonical
related: [aggregate-root, entity, value-object, repository, factory-method, abstract-factory, builder]
incompatible_with: []
verified: 2026-08-02
---

# Factory

## 1. Name, aliases, and lineage

The canonical name inside Domain-Driven Design is simply Factory. It was named
and given a chapter-length treatment by Eric Evans in *Domain-Driven Design.
Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003, Chapter 6,
"The Life Cycle of a Domain Object", in the section titled Factories. Evans
places Factory alongside Aggregate and Repository as the three complementary
patterns that govern how a domain object is created, held together, and later
retrieved, and he is explicit that Factory borrows its name and much of its
shape from the Gang of Four's creational family rather than inventing a new
mechanism (Domain-Driven Design notes summarizing Chapter 6, GitHub wiki,
rudradixit/domain-driven-design-notes, verified 2026-08-02,
https://github.com/rudradixit/domain-driven-design-notes/wiki/Chapter-6-The-Lifecycle-Of-A-Domain-Object).
A second independent summary of the same chapter reaches the same reading. it
describes the Factory section as covering three concrete forms, a Factory
Method living on the Aggregate Root, an Abstract Factory Class chosen when the
client must pick between concrete subtypes, and a Builder Class chosen when
the manufactured object's assembly is itself complicated (Herberto Graca,
"DDD.6, The lifecycle of a domain object", verified 2026-08-02,
https://herbertograca.com/2015/10/04/domain-driven-design-by-eric-evans-chap-6-the-lifecycle-of-a-domain-object/).

Vaughn Vernon revisits and sharpens the pattern a decade later in
*Implementing Domain-Driven Design*, Addison-Wesley, 2013. Chapter 11,
"Factories", opens on page 389 and its central section, "Factory Method on
Aggregate Root", begins on page 391. Vernon's worked example has a Product
Aggregate expose a `planBacklogItem()` method that builds and returns a new
BacklogItem, a separate Aggregate, so that the method reads as a command from
the outside but behaves as a query-shaped construction contract underneath,
each call producing one new Aggregate instance and handing back a reference to
it (InformIT excerpt, "Implementing Domain-Driven Design, Aggregates", and the
O'Reilly table of contents for the same book, both verified 2026-08-02,
https://www.informit.com/articles/article.aspx?p=2020371 and
https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/ch10.html).
Vernon's contribution is not a new pattern, it is a naming discipline. he shows
that the overwhelming majority of real Factories in a DDD codebase are not
free-standing Factory objects, they are ordinary methods that already live on
an Aggregate Root and happen to construct another Aggregate as one of their
side effects.

Three aliases circulate for the same idea, and each names a different shape
that Evans and Vernon both classify under the single word Factory.

- **Domain Factory.** The umbrella term used to distinguish a
  domain-model-owned creation object from a general-purpose Abstract Factory
  or Factory Method as described in the Gang of Four catalog. The DDD Factory
  always speaks in the Ubiquitous Language and always returns something that
  satisfies the invariants of the Aggregate it builds, which is a stronger
  contract than the GoF pattern makes on its own.
- **Aggregate Factory.** The specific case where the thing being constructed
  is a whole Aggregate, not a single Value Object or a plain Entity. This is
  the most common shape in event-sourced systems, where a dedicated
  reconstitution Factory replays an event stream into a live Aggregate
  instance, distinct from the creation Factory that builds a brand-new one.
- **Factory Method on Aggregate Root.** Vernon's name for the case where the
  Factory is not a separate class at all, it is a method that already exists
  on a neighboring Aggregate Root because that root already holds most of the
  data the new object needs.

A short test separates a genuine DDD Factory from an ordinary constructor
call. if the object being produced has invariants that span more than one
field, or the choice of concrete type depends on runtime data, or producing
the object requires data that the caller should not have to assemble by hand,
the construction belongs behind a Factory. If none of those hold, a public
constructor is the correct and simpler choice, and wrapping it in a Factory
only adds a layer that does no protective work.

## 2. Problem and context

A domain model accumulates two kinds of complexity as it grows. business rule
complexity, which lives inside the behavior of Entities and Value Objects
once they exist, and construction complexity, which lives in the moment an
object first comes into being. The two are easy to conflate because they both
live in the same class file, but they pull in opposite directions. Behavior
wants a rich, focused object with a small, well-defended public surface.
Construction, left unmanaged, wants every caller to know the object's internal
shape well enough to assemble it correctly, which is precisely the kind of
knowledge a rich domain model exists to hide.

The trouble shows up first in the constructor of an Aggregate Root. An Order
Aggregate that must never exist without at least one OrderLine, a consistent
currency across every line, and a computed total that matches its lines,
cannot honestly expose a constructor that takes an empty list and a total of
zero and calls itself valid. Either the constructor grows a wall of validation
logic that has nothing to do with what an Order does once it exists, or the
validation is skipped and invalid Orders leak into the system through some
code path nobody audited. Evans frames this directly. Factories exist because
object creation can become "a major operation in its own right", and when it
does, "delegating creation of a complex object or Aggregate to a separate
object" keeps the constructed object's own behavior "clear and clean" of
assembly logic that belongs to a different concern entirely (rudradixit wiki
summary of Chapter 6, verified 2026-08-02,
https://github.com/rudradixit/domain-driven-design-notes/wiki/Chapter-6-The-Lifecycle-Of-A-Domain-Object).

The problem sharpens further in three recurring situations that a plain
constructor structurally cannot solve.

- **Post-construction setup.** Some objects are not usable the instant their
  fields are populated. A Value Object representing money needs its currency
  and minor-unit precision resolved before arithmetic on it is safe. An
  Aggregate that participates in event sourcing needs every prior event
  replayed before its invariants can be trusted. A constructor that finishes
  before this setup completes hands the caller a half-built object with no
  signal that it is unsafe to use.
- **Aggregate-owned object creation.** When an Order creates its own
  OrderLine, the OrderLine's identity, its parent reference, and its position
  inside the collection are all facts the Order already knows and the caller
  should never have to supply. Pushing that responsibility onto the caller
  duplicates knowledge the Aggregate Root already holds and invites the two
  copies to drift apart.
- **Type selection from runtime data.** A PaymentMethod might need to become a
  CreditCardPayment, a BankTransferPayment, or a WalletPayment depending on a
  string read from a request body. A constructor cannot decide its own class.
  Something upstream of the constructor has to hold that decision, and a
  Factory is the object DDD assigns to hold it.

The context in which Factory earns its place is therefore never "every object
needs one." It is specifically the context where construction has become a
place where invalid states could otherwise be born, where the caller is being
asked to know more about the object's internals than its role in the domain
warrants, or where the decision of which concrete type to build cannot be made
until the moment of construction.

## 3. Forces

The forces below are the author's synthesis of Evans's stated design rules,
read against how those rules trade off against one another in practice. This
is engineering judgement, not a direct quotation, except where marked.

- **Invariant safety versus caller convenience.** A Factory that refuses to
  hand back an invalid object protects every future reader of that object from
  ever having to re-check its validity. Evans states the rule plainly. "each
  creation method is atomic and enforces all invariants of the created object
  or Aggregate" (rudradixit wiki, verified 2026-08-02, same URL as above). The
  cost is that the Factory's parameter list has to be wide enough to satisfy
  the whole invariant in one call, which can make the call site verbose
  compared to a constructor plus a handful of setters. DDD accepts the
  verbosity because the alternative, letting an object exist briefly in an
  invalid intermediate state, is the exact failure mode Aggregates are meant
  to prevent.
- **Abstraction versus discoverability.** Evans's second rule is that "the
  Factory should be abstracted to the type desired, rather than the concrete
  class or classes" (same source). Hiding the concrete class behind an
  interface or a return type keeps callers decoupled from an implementation
  that might later change. The force pulling the other way is that an
  IDE-driven reader who wants to know which concrete class will actually be
  built now has to trace through the Factory's internals rather than reading
  a constructor call directly. DDD accepts the indirection because the
  alternative, callers importing every concrete product type, is the coupling
  the pattern exists to remove.
- **Coupling to arguments versus reuse.** A Factory is, in Evans's words,
  "coupled to its arguments," and the coupling stays healthy so long as the
  Factory plugs those arguments into the product without dissecting them into
  pieces the product itself did not ask for (same source). The moment a
  Factory starts pulling apart its own arguments to redistribute them across
  several downstream calls, the Factory has quietly grown into an application
  service, which is a different pattern with a different set of
  responsibilities and a different place in the layering.
- **Locality versus generality.** A Factory Method sitting on an existing
  Aggregate Root is cheap to write and cheap to find, because a reader
  already looking at the Order class will see `addLine` sitting next to
  `createShipment`. A dedicated, free-standing Factory class is more general
  and easier to test in isolation, but it adds a file, a name, and a decision
  about where that file lives that a Factory Method never has to make. Vernon
  observes that the majority of real Factories in his sample Bounded Contexts
  are Factory Methods for exactly this reason, they cost less to introduce
  (InformIT excerpt, verified 2026-08-02,
  https://www.informit.com/articles/article.aspx?p=2020371).
- **Failure signaling versus null tolerance.** Evans is explicit that a
  Factory must never silently return a broken object. if the interface makes
  it possible to request an object that cannot be created correctly, an
  exception should be raised, or some other mechanism invoked, so that no
  improper return value is possible at all (rudradixit wiki, verified
  2026-08-02, same URL as above). Raising forces every caller to
  handle failure explicitly, which is more code at every call site, weighed
  against the alternative of a null or half-valid return silently propagating
  a broken Aggregate into persistence.

## 4. Applicability and non-applicability

Reach for a Factory when at least one of these holds.

- The object being constructed is an Aggregate, and its invariants span more
  than one field or more than one child object, so no single-field validation
  inside a plain constructor could enforce them alone.
- The object needs post-construction work before it is safe to use, replaying
  an event stream, resolving a currency table, computing a derived value from
  several inputs, that a bare constructor call cannot express.
- The concrete type of the object to build is not known until runtime, and
  depends on a value the caller supplies rather than on which class the
  caller happened to import.
- The object being built is owned by, and only ever created through, another
  Aggregate, so pushing identity and parent-reference assignment onto the
  caller would duplicate information the owning Aggregate already has.
- A Repository needs to reconstitute a persisted Aggregate from stored
  primitives or a stored event stream, and the reconstitution path has
  different obligations than the creation path, most obviously that
  reconstitution must not re-emit domain events the first construction would
  have raised.

Do not reach for a Factory in these cases. this list is deliberately the
larger and more specific of the two, because a Factory introduced where it
is not needed adds indirection with no invariant to protect.

- **The class has no invariants beyond its own field types, and every field
  is independently valid on its own.** A Value Object like a PostalCode that
  merely wraps a validated string does not need a Factory. its own
  constructor, or a private constructor paired with a single static
  validating method, already does the whole job.
- **The class is not polymorphic and never will be.** If there is exactly one
  concrete implementation and no plan to add a second, a Factory's core
  benefit, hiding a type decision, has nothing to hide. A public constructor
  is simpler and equally safe.
- **The caller already legitimately knows the concrete type and needs to.**
  Test fixtures, database mapping code, and serialization adapters routinely
  need to construct a concrete class by name. Forcing that code through a
  domain Factory adds a layer that provides no protection, because that code
  is not a domain client in the sense the pattern is meant to guard.
- **The object is a simple data holder crossing a layer boundary, not a
  domain object.** A DTO, a view model, or a wire-format record has no
  domain invariant to enforce, so a Factory around it only wraps a constructor
  call in ceremony.
- **The class already exposes all the state a caller would need to assemble
  it correctly, and assembling it is not complicated.** Evans's own guidance
  is that a plain constructor is preferable in exactly this situation, "when
  the class is not part of a hierarchy...when the client cares about the
  implementation, perhaps because it wants to choose an implementation for
  performance reasons" (rudradixit wiki, verified 2026-08-02, same URL as
  above).
- **The object is transient application state, not a persisted domain
  object.** A request-scoped filter, a UI view state, or an in-memory cache
  entry has no domain life cycle for a Factory to govern.

## 5. Structure

Four roles recur across every real Factory in a DDD codebase, though the same
class often plays more than one role at once.

- **Client.** The code that needs a new domain object and does not want to,
  or should not, know how to assemble it. Typically an Application Service
  method handling a command, or another Aggregate Root's own method.
- **Factory.** The object or method that owns the assembly logic. It may be a
  static or class method on the Aggregate Root being built, a free-standing
  class dedicated to one Aggregate, or a shared class that produces several
  related concrete types.
- **Product.** The Aggregate, Entity, or Value Object that comes out of the
  Factory. The Product's own constructor is often made private or
  package-visible so the Factory is the only legitimate entry point into it,
  which is the mechanism that turns "please use the Factory" from a
  convention into an enforced rule.
- **Reconstitution path (optional but common).** A second entry point,
  distinct from the creation Factory, used by a Repository to rebuild a
  Product from already-persisted data. Evans keeps this separate from
  creation because reconstitution must skip work that creation performs,
  most notably raising domain events for facts that already happened in the
  past.

```
 +------------------+          creates          +------------------+
 |      Client       | ------------------------> |      Factory      |
 | (Application       |                           | (static method,   |
 |  Service or a       |                           |  factory class,   |
 |  neighboring         |                           |  or Factory       |
 |  Aggregate Root)      |                           |  Method on the    |
 +------------------+          checks              |  owning Aggregate) |
                                invariants,          +--------+---------+
                                selects type                   |
                                                                | returns
                                                                v
                                                     +------------------+
                                                     |      Product      |
                                                     | (Aggregate Root,   |
                                                     |  Entity, or Value  |
                                                     |  Object, private   |
                                                     |  constructor)      |
                                                     +--------+---------+
                                                                ^
                                                                | rebuilds from
                                                                | stored state,
                                                                | skips events
                                                     +--------+---------+
                                                     |   Repository      |
                                                     | (calls a separate  |
                                                     |  reconstitution     |
                                                     |  Factory method)    |
                                                     +------------------+
```

## 6. ASCII structure diagram

```
        Order Aggregate creation, Factory Method on Aggregate Root
        ------------------------------------------------------------

   ApplicationService.placeOrder(cmd)
              |
              | 1. build lines from cmd
              v
   +--------------------------+
   |   OrderFactory.create()   |   <-- dedicated Factory class
   |   - validates currency     |       (used when creation logic
   |   - validates >= 1 line    |        is too large for a single
   |   - computes total          |        Aggregate Root method)
   +------------+-------------+
                | new Order(...)   private constructor
                v
       +------------------+
       |   Order (root)    |
       |  - id             |
       |  - lines[]        |
       |  - total          |
       |  - status         |
       +---------+--------+
                 |
                 | order.addLine(product, qty)
                 v                              <-- Factory Method
       +------------------+                          on Aggregate Root,
       |   OrderLine        |                         Order builds its
       |  (owned Entity)     |                         own child Entity
       +------------------+
```

## 7. Dynamics

Two runtime flows matter, and they are frequently confused with each other
because they touch the same classes. creating a brand-new Aggregate, and
reconstituting an existing one from storage.

```
   Creation flow
   --------------
   Client            Factory              Product              EventStream
     |                  |                    |                       |
     |--create(args)--->|                    |                       |
     |                  |--validate invariants|                      |
     |                  |  (raise if invalid) |                      |
     |                  |--new Product(...)-->|                       |
     |                  |                    |--raise DomainEvent----->|
     |<--Product--------|                    |                       |
     |                  |                    |                       |

   Reconstitution flow
   ---------------------
   Repository        Factory (reconstitute)   Product              EventStream
     |                  |                        |                     |
     |--load(id)------->|                        |                     |
     |                  |--fetch stored events    |                     |
     |                  |  or stored snapshot      |                    |
     |                  |--new Product(...)------->|                    |
     |                  |  (bypasses invariant       |                   |
     |                  |   raise, replays state,     |                  |
     |                  |   never re-raises past        |                |
     |                  |   DomainEvents)                 |              |
     |<--Product--------|                        |                     |
```

The distinction matters because the same class of bug appears repeatedly when
teams skip it. an Order reconstituted from ten years of stored events that
naively calls the same constructor path as a brand-new Order will re-publish
every one of those ten years of events to every subscriber the moment it
loads, which is almost never the intended behavior and is exactly the kind of
mistake a clean separation between the two Factory paths prevents.

## 8. Implementation variants

- **Factory Method on Aggregate Root.** The most common shape in practice.
  the Factory is not a separate class at all, it is a method on an existing
  Aggregate Root, most often the one that owns or naturally supplies most of
  the new object's data. Vernon's `planBacklogItem()` example on the Product
  Aggregate is the canonical illustration, one method call that both reads as
  a command from the caller's side and behaves as a Factory underneath
  (InformIT, verified 2026-08-02,
  https://www.informit.com/articles/article.aspx?p=2020371).
- **Static factory method on the Product itself.** A named static method,
  often paired with a private constructor, that replaces `new Order(...)`
  with `Order.create(...)`. This buys a readable call site and a single
  chokepoint for validation without introducing a separate class, at the cost
  that the Product class now carries both its own behavior and its own
  construction logic in one file.
- **Dedicated Factory class.** A free-standing class, `OrderFactory`, so that
  the constructor of Order is not visible to anyone else, used when the
  construction logic is large enough on its own to deserve a name, a test
  file, and a place in the dependency graph separate from Order's runtime
  behavior. This is the shape closest to the Gang of Four's Abstract Factory,
  and DDD reaches for it specifically when the decision of which concrete
  subtype to build genuinely depends on runtime data rather than on which
  neighboring Aggregate happens to be calling.
- **Reconstitution factory, separate from the creation factory.** A method,
  frequently named `reconstitute`, `fromEvents`, or `rehydrate`, that a
  Repository calls instead of the creation path. It exists precisely so that
  loading an Aggregate from storage never re-triggers the side effects,
  domain events, ID generation, timestamp stamping, that creating a genuinely
  new Aggregate would trigger.
- **Builder-backed Factory.** When even a single Factory method's parameter
  list becomes unmanageable, DDD literature points to composing Factory with
  Builder rather than growing the Factory's own signature further (Herberto
  Graca, verified 2026-08-02, same URL as above). The Factory still owns
  invariant enforcement and still returns the finished Product, but delegates
  the step-by-step accumulation of arguments to a Builder that the Factory
  consumes internally, or exposes to advanced callers who genuinely need
  staged construction.
- **Prototype-backed Factory.** Less common but real in template-heavy
  domains, a Factory that clones a pre-configured template Aggregate and then
  applies the caller's overrides, rather than assembling every field from
  scratch. Useful when most instances of a Product share the bulk of their
  configuration and only a small delta varies per call.

## 9. Known production uses

- **Axon Framework, `AggregateFactory` interface (Java).** Axon is an
  open-source Java framework for building CQRS and event-sourced
  applications, and it ships `AggregateFactory` as a first-class extension
  point. The interface "describes objects capable of creating instances of
  aggregates to be initialized with an event stream", and its
  `createAggregate(Object aggregateIdentifier, DomainEventMessage<?>
  firstEvent)` method exists specifically to run the reconstitution path
  distinct from ordinary creation. Axon ships a default
  `GenericAggregateFactory` implementation and documents that a custom
  implementation should extend `AbstractAggregateFactory` when snapshotting
  is in play (AxonIQ API docs, verified 2026-08-02,
  https://apidocs.axoniq.io/2.0/org/axonframework/eventsourcing/AggregateFactory.html).
- **EventFlow, `IAggregateFactory` interface (.NET).** EventFlow is an
  async-first, open-source CQRS and event-sourcing framework for .NET,
  published at github.com/eventflow/EventFlow. Its own documentation states
  that `IAggregateFactory` "is a factory for creating instances of
  aggregates" and that the default implementation resolves every
  constructor dependency except the Aggregate identifier through the
  application's IoC container, while the identifier itself is supplied
  directly by the caller, exactly the split Evans describes between what the
  Factory must be given and what it may resolve on the caller's behalf
  (EventFlow documentation, geteventflow.net, verified 2026-08-02,
  https://geteventflow.net/basics/aggregates/, and the EventFlow GitHub
  repository, verified 2026-08-02,
  https://github.com/eventflow/EventFlow).
- **Broadway, `AggregateFactory` component (PHP).** Broadway is an
  open-source PHP framework, originally built at Qandidate, providing
  infrastructure for CQRS and event-sourced applications with Symfony
  integration. Its documentation states that Broadway was itself designed
  after studying prior CQRS and event-sourcing frameworks including
  AggregateSource, Axon Framework, and Ncqrs, and it ships its own
  `AggregateFactory` component whose job is to reconstitute an Aggregate from
  a stored domain event stream, the same reconstitution responsibility Axon
  and EventFlow assign to their own factories (Broadway GitHub repository,
  verified 2026-08-02, https://github.com/broadway/broadway).

These three are independent implementations, in three different languages, of
the same DDD-literature idea, a dedicated object whose sole responsibility is
producing a correctly initialized Aggregate, kept separate from the Aggregate
Root's own runtime behavior and further split into a distinct reconstitution
path. That convergence across unrelated codebases is itself evidence that the
pattern names a real, recurring structural need rather than an academic
abstraction.

## 10. Consequences

**Positive.**

- Invalid Aggregates become structurally difficult to create, because the
  only public path into the Product is the Factory, and the Factory refuses
  to return anything that fails its invariant checks.
- Construction logic that has nothing to do with an object's runtime
  behavior moves out of that object's file and into a place a reader can
  choose to ignore when they only care about behavior, and choose to read
  when they only care about how the object is built.
- Adding a new concrete type behind an existing Factory interface, a new
  PaymentMethod subtype, for example, touches the Factory and the new
  subtype, and does not touch every call site that already constructs a
  PaymentMethod, because those call sites depend on the Factory's interface,
  not on the concrete class.
- Reconstitution and creation can diverge cleanly. an Aggregate loaded from
  ten years of stored events does not accidentally re-fire ten years of
  domain events, because the reconstitution Factory is a genuinely separate
  code path from the creation Factory rather than the same constructor
  reused for both purposes.
- Tests that exercise invariant enforcement have exactly one place to target.
  every "must reject an Order with zero lines" test can call the Factory
  directly and never has to construct an intentionally-broken Order by
  bypassing validation, because there is no such bypass exposed.

**Negative.**

- An extra class, method, or file exists that would not otherwise exist, and
  every extra name is a name a new team member has to learn, per Evans's own
  caution that a Factory should only be introduced where its protective work
  earns that cost.
- The Factory becomes tightly coupled to its Product's constructor signature,
  so any change to what the Product needs to be valid usually requires a
  matching change to the Factory, doubling the edit surface for what is
  conceptually a single change.
- A poorly scoped Factory that reaches past assembling its arguments into
  actually deriving new business decisions from them quietly becomes an
  Application Service wearing a Factory's name, which blurs the layering the
  pattern was meant to keep clean.
- A separate reconstitution path is one more code path to keep in sync with
  the creation path as the Aggregate's shape evolves, and a team that adds a
  field to the creation Factory but forgets the reconstitution Factory ships
  an Aggregate that loads from storage in a subtly different state than one
  freshly created.
- For a genuinely simple Value Object, wrapping a one-line validating
  constructor in a Factory class adds indirection that returns no invariant
  protection the constructor did not already provide on its own.

## 11. Failure modes and misuse

- **Symptom.** A production incident traces back to an Aggregate that exists
  in the database with an invariant violated, an Order with zero lines, a
  negative total, a status that skipped a required transition.
  **Cause.** The Aggregate has more than one construction path, and only one
  of them runs through the Factory's validation. A second path, often an ORM
  hydration hook, a test helper that got promoted into production code, or a
  bulk-import script that calls the constructor directly, bypassed the
  Factory entirely.
  **Fix.** Make the Product's constructor genuinely inaccessible outside the
  Factory, package-private, private with a friend accessor, or an internal
  visibility modifier depending on the language, so the compiler, not
  convention, is what enforces "only the Factory constructs this."

- **Symptom.** Loading an old Aggregate from storage re-triggers integration
  side effects, an email gets re-sent, a webhook fires again, a downstream
  system re-processes an order that shipped years ago.
  **Cause.** The reconstitution path reuses the same constructor, or the same
  Factory method, that creation uses, and that constructor always raises the
  Aggregate's domain events as part of building it, with no branch that
  skips that step for the reconstitution case.
  **Fix.** Split reconstitution into its own Factory method that populates
  state directly without invoking the event-raising code path that creation
  uses, matching the separation Axon's own `AggregateFactory` interface
  exists to enforce (AxonIQ API docs, verified 2026-08-02, same URL as
  dimension 9).

- **Symptom.** A code review flags that the "Factory" for an Order has grown
  to call three other services, look up a customer's credit limit, and decide
  whether to apply a discount, none of which is about assembling an Order
  object.
  **Cause.** The Factory absorbed responsibilities that belong to an
  Application Service, because it was the first object in the call chain
  that had access to the raw command data.
  **Fix.** Move the business decisions, credit checks, discount rules, out to
  an explicit Application Service that gathers what the Factory needs and
  passes only that, restoring the Factory to pure assembly and invariant
  enforcement.

- **Symptom.** Two Factories for related Aggregates duplicate the same
  currency-consistency check, and a bug fix applied to one is not applied to
  the other, so one Aggregate type silently accepts mismatched currencies
  again a month later.
  **Cause.** The invariant logic was copy-pasted between Factories instead of
  extracted into a shared Value Object or a shared validation function both
  Factories call.
  **Fix.** Pull the shared rule into a Value Object whose own constructor
  enforces it, `Money` refusing to add two different currencies, for
  instance, so every Factory that composes a Money value inherits the check
  automatically instead of re-implementing it.

- **Symptom.** A Factory method's parameter list has grown past ten
  positional arguments, and callers routinely pass the wrong value into the
  wrong slot because two adjacent parameters are both strings.
  **Cause.** The Factory kept absorbing new optional configuration instead of
  being paired with a Builder once its signature outgrew a single readable
  call.
  **Fix.** Introduce a Builder that the Factory consumes, or that advanced
  callers use directly, and reduce the Factory's own public signature to the
  handful of arguments that are always required, per the Builder-backed
  Factory variant described in dimension 8.

## 12. Trade-off matrix

| Force | Factory | Plain constructor | Abstract Factory (GoF) | Builder (GoF) |
|---|---|---|---|---|
| Enforces cross-field invariants at creation | Yes, by design | Only if hand-written into the constructor body | Not by itself, delegates to the concrete product | Only at the final `build()` call, not per field |
| Hides concrete type from the caller | Yes, when abstracted to an interface | No, caller names the class directly | Yes, this is its primary purpose | Not typically, the built type is usually known |
| Fits construction owned by another Aggregate | Yes, via Factory Method on Aggregate Root | Awkward, forces the caller to supply parent references | No native concept of aggregate ownership | No native concept of aggregate ownership |
| Handles reconstitution from storage separately from creation | Yes, as a distinct named path | No, one constructor serves both, risking re-fired events | No native distinction | No native distinction |
| Cost when the product has one simple, non-polymorphic shape | Unjustified indirection | Cheapest, correct choice | Unjustified, no type variation to hide | Unjustified, no staged assembly needed |
| Speaks the domain's Ubiquitous Language in its method names | Yes, expected, `planBacklogItem` not `create` | N/A | Rarely, GoF naming is generic, `createProduct` | Rarely, GoF naming is generic, `build` |

## 13. Related and incompatible patterns

- **Aggregate Root.** The most common Product a DDD Factory builds, and the
  most common home for a Factory Method. Factory and Aggregate Root are so
  frequently the same class wearing two hats that Vernon treats "Factory
  Method on Aggregate Root" as close to the default shape rather than the
  exception (InformIT, verified 2026-08-02, same URL as dimension 1).
- **Entity.** A plain, non-root Entity owned by an Aggregate is typically
  built through the owning Aggregate Root's own Factory Method rather than
  through any Factory of its own, because the owning root already holds the
  identity and parent-reference data the child Entity needs.
- **Value Object.** Simple Value Objects usually skip a dedicated Factory
  entirely in favor of a private constructor plus a single static validating
  method, per the non-applicability list in dimension 4. Only Value Objects
  whose construction genuinely branches by runtime type, a Money type that
  must pick a rounding strategy per currency, for example, earn a real
  Factory.
- **Repository.** Evans places Factory and Repository on opposite ends of the
  same life cycle. a Factory brings a new object into existence, a Repository
  brings an existing, previously-persisted object back into memory. A
  Repository's `load` or `findById` method typically calls a reconstitution
  Factory internally rather than duplicating the assembly logic itself.
- **Factory Method (GoF).** The Gang of Four's original pattern, described in
  Gamma, Helm, Johnson, and Vlissides, *Design Patterns*, Addison-Wesley,
  1994, Chapter 3, is the direct ancestor of the DDD Factory Method variant.
  The GoF version is a subclass-overridable method with no domain-specific
  invariant obligation. the DDD version borrows the shape and adds Evans's
  atomicity and invariant rules on top. See the separate `factory-method`
  entry in this repository's `01-gof` family for the ancestor pattern in
  full.
- **Abstract Factory (GoF).** The DDD Dedicated Factory Class variant,
  described in dimension 8, is structurally the same idea as the GoF Abstract
  Factory when the DDD Factory must choose between several concrete product
  subtypes at runtime. See the separate `abstract-factory` entry in this
  repository's `01-gof` family.
- **Builder (GoF).** Composes with Factory rather than competing with it, per
  the Builder-backed Factory variant in dimension 8, whenever a single
  Factory method's parameter list has grown too large to stay readable.
- **Domain Event.** A creation Factory typically raises one or more Domain
  Events as part of building a new Aggregate, `OrderPlaced`, for instance,
  while a reconstitution Factory deliberately does not, which is the central
  distinction covered in dimension 7's two runtime flows.
- **Incompatible with nothing structurally**, but Factory is redundant, and
  therefore effectively incompatible in the sense of adding no value, with
  any Product that already satisfies every clause of the non-applicability
  list in dimension 4.

## 14. Refactoring path in and out

**Introducing a Factory into code that does not have one.**

1. Identify the constructor whose call sites all repeat the same validation,
   the same currency check, the same "must have at least one line" guard,
   copy-pasted or nearly copy-pasted at every call site.
2. Write a single static method, or a new class if the logic is large, that
   performs that validation once and then calls the constructor internally.
   Name the method in the Ubiquitous Language, `place`, `open`, `schedule`,
   not the generic `create`.
3. Make the constructor itself inaccessible from outside the file or package,
   using whichever visibility modifier the language offers, so the new method
   becomes the only legitimate entry point.
4. Update every existing call site to call the new method instead of the
   constructor directly, and delete the duplicated validation that used to
   live at each call site.
5. If the Aggregate is also loaded from storage, add a second, explicitly
   named reconstitution method, `reconstitute` or `fromSnapshot`, that
   populates the same fields without re-running the event-raising code path
   that the creation method runs, and point the Repository at this second
   method instead of the first.
6. Add a test that asserts the old, unsafe path is actually gone, attempting
   to construct the invalid case directly should now fail to compile, not
   merely fail at runtime.

**Removing a Factory once it stops earning its place.**

1. Confirm the Product has settled into a single concrete shape with no
   remaining runtime type decision, and confirm every invariant the Factory
   enforces is expressible inside the constructor's own parameter validation
   without external lookups.
2. Inline the Factory's validation logic directly into the constructor body.
3. Reopen the constructor's visibility to whatever level the domain actually
   requires.
4. Update call sites to call the constructor directly, and delete the now
   redundant Factory method or class.
5. Confirm the reconstitution path, if one existed, still has a distinct
   entry point from creation even after the simplification, because that
   split protects against the re-fired-events failure mode regardless of how
   simple construction has become.

## 15. Testing and verification

A Factory is one of the easiest constructs in a domain model to test in
isolation, precisely because its entire job is to answer one question, valid
in, Product out, invalid in, exception out, with no side effects beyond the
Product's own domain events.

- **Invariant rejection tests.** For every invariant the Factory is supposed
  to enforce, one test that supplies input violating exactly that invariant
  and asserts the Factory raises rather than returning a Product. An Order
  Factory earns one test for zero lines, one for mismatched currencies
  between lines, and one for a negative unit price, each isolated so a
  future change that breaks only one of the three shows up as one failing
  test, not a vague general failure.
- **Happy-path construction tests.** A smaller number of tests confirming
  that valid input produces a Product whose fields match what was supplied,
  and, separately, that the correct Domain Events were raised as a
  side effect of creation.
- **Reconstitution parity tests.** A test that constructs an Aggregate
  through the creation Factory, serializes it exactly the way the real
  persistence layer would, reconstitutes it through the reconstitution
  Factory, and asserts the two are equal in every field a domain rule cares
  about. This is the test most teams skip and the one that catches the
  re-fired-event failure mode from dimension 11 before it reaches
  production, by additionally asserting that the reconstituted instance
  raised zero new Domain Events.
- **Test doubles for the Factory itself.** Because Application Services
  should depend on a Factory through an interface rather than a concrete
  class where a domain has more than one implementation of a Product, a
  hand-written or generated stub Factory that always returns a fixed,
  pre-built Product is the standard way to keep Application Service tests
  from having to satisfy every real invariant only to reach the code under
  test.
- **Property-based construction tests**, where the toolchain supports them,
  generating a wide range of otherwise-valid inputs and asserting the
  invariant the Factory is meant to protect holds for every generated
  Product, are a stronger check than a fixed table of examples because they
  are far more likely to surface an edge case, a currency the hand-written
  test table never considered, a quantity of exactly zero, that a
  hand-picked example set would miss.

## 16. Observability signals

- **Construction rejection rate.** A counter, tagged by which invariant
  failed, incremented every time a Factory raises rather than returning a
  Product. A healthy system shows this near zero in steady state, and a
  sudden spike after a deploy is one of the fastest signals that an upstream
  caller started sending malformed commands, often because a client and
  server drifted out of sync on a validation rule.
- **Reconstitution latency and event-stream length.** For event-sourced
  Aggregates, the time the reconstitution Factory spends replaying events,
  and the number of events replayed per load, are both worth tracking. A
  steadily climbing replay count per Aggregate over time is the standard
  early signal that snapshotting needs to be introduced before load latency
  becomes a user-visible problem.
- **Domain events raised per creation call.** A count of how many events a
  single Factory call emitted. this number should be stable for a given
  Aggregate type, and an unexpected change, a creation call suddenly emitting
  three events where it used to emit one, is a fast way to catch an
  accidental behavior change during a refactor before it reaches production.
- **Zero-events-on-reconstitution assertion in production, not only in
  tests.** Because the failure mode described in dimension 11 is silent, a
  production-side alert that fires if the reconstitution path ever raises a
  Domain Event at all is a cheap, high-value guard that catches a regression
  the moment it first happens rather than after a downstream system has
  already reacted to the incorrectly re-fired event.
- **Factory call site count per Product type.** Not a runtime metric but a
  static one, worth tracking over time in code review, because a Product
  whose constructor is called from more than one Factory, or worse, from
  outside any Factory at all, is the structural precondition for the
  invalid-state-in-production failure mode in dimension 11.

## 17. Security and privacy implications

The Factory pattern is largely neutral with respect to security in the sense
that it introduces no new attack surface of its own, but two implications are
real and worth naming rather than inventing beyond them.

Concentrating every construction path for an Aggregate through one Factory
means that any input-validation rule needed for security purposes, a length
limit on a free-text field that would otherwise enable a denial-of-service
through unbounded storage, a check that a supplied identifier belongs to the
tenant making the request, has exactly one place to be added and exactly one
place to audit. A domain with several unguarded constructors scattered across
call sites has, correspondingly, several places an auditor has to check to
confirm the same rule is actually enforced everywhere, and several places a
future change can quietly reintroduce the gap in one of them while fixing it
in another.

The reconstitution path deserves specific privacy attention in
event-sourced systems, because it, by design, replays historical data. a
reconstitution Factory that logs its inputs for debugging, or that passes
replayed event payloads through a generic tracing middleware, can leak
personal data that a later deletion request believed had been removed from
the live Aggregate but that still exists inside the historical event stream
the reconstitution Factory continues to read on every load. Where a system
carries a right-to-erasure obligation, the reconstitution Factory, not only
the creation Factory, is where a crypto-shredding or event-payload-redaction
strategy has to be implemented, because it is the one code path guaranteed to
touch every historical record of the affected Aggregate on its way back into
memory.

## Code examples

TypeScript, Factory Method on Aggregate Root, matching Vernon's shape where an
existing Aggregate builds another Aggregate through one of its own methods,
plus a dedicated Factory class for the case where construction logic has
outgrown a single method.

```typescript
class Money {
  private constructor(
    readonly amountMinorUnits: number,
    readonly currency: string
  ) {}

  static of(amountMinorUnits: number, currency: string): Money {
    if (amountMinorUnits < 0) {
      throw new Error("amount cannot be negative");
    }
    if (!/^[A-Z]{3}$/.test(currency)) {
      throw new Error("currency must be a 3 letter ISO code");
    }
    return new Money(amountMinorUnits, currency);
  }

  add(other: Money): Money {
    if (other.currency !== this.currency) {
      throw new Error("cannot add mismatched currencies");
    }
    return Money.of(this.amountMinorUnits + other.amountMinorUnits, this.currency);
  }
}

interface OrderLineInput {
  productId: string;
  unitPrice: Money;
  quantity: number;
}

class OrderLine {
  private constructor(
    readonly id: string,
    readonly productId: string,
    readonly unitPrice: Money,
    readonly quantity: number
  ) {}

  static forOrder(parentOrderId: string, index: number, input: OrderLineInput): OrderLine {
    if (input.quantity <= 0) {
      throw new Error("quantity must be positive");
    }
    return new OrderLine(`${parentOrderId}-line-${index}`, input.productId, input.unitPrice, input.quantity);
  }

  lineTotal(): Money {
    return Money.of(this.unitPrice.amountMinorUnits * this.quantity, this.unitPrice.currency);
  }
}

class Order {
  private readonly _lines: OrderLine[] = [];
  private readonly events: string[] = [];

  private constructor(readonly id: string, readonly currency: string) {}

  // Factory Method on Aggregate Root, matching Vernon's Chapter 11 shape.
  // The caller supplies the raw command data, Order owns its own assembly.
  static open(id: string, currency: string, firstLine: OrderLineInput): Order {
    const order = new Order(id, currency);
    order.addLine(firstLine);
    order.events.push(`OrderOpened:${id}`);
    return order;
  }

  addLine(input: OrderLineInput): void {
    if (input.unitPrice.currency !== this.currency) {
      throw new Error("line currency must match order currency");
    }
    const line = OrderLine.forOrder(this.id, this._lines.length, input);
    this._lines.push(line);
  }

  get lines(): readonly OrderLine[] {
    return this._lines;
  }

  total(): Money {
    if (this._lines.length === 0) {
      throw new Error("an order must have at least one line to have a total");
    }
    return this._lines.reduce((sum, l) => sum.add(l.lineTotal()), Money.of(0, this.currency));
  }

  // Reconstitution, separate from creation. Never pushes to `events`.
  static reconstitute(id: string, currency: string, rawLines: OrderLineInput[]): Order {
    const order = new Order(id, currency);
    for (const raw of rawLines) {
      order.addLine(raw);
    }
    return order;
  }

  raisedEvents(): readonly string[] {
    return this.events;
  }
}

// Dedicated Factory class, used when creation needs a lookup the Aggregate
// itself should not perform, choosing a payment method from a runtime string.
interface PaymentMethod {
  authorize(amount: Money): void;
}

class CreditCardPayment implements PaymentMethod {
  constructor(private readonly cardToken: string) {}
  authorize(amount: Money): void {
    if (this.cardToken.length === 0) throw new Error("missing card token");
  }
}

class BankTransferPayment implements PaymentMethod {
  constructor(private readonly iban: string) {}
  authorize(amount: Money): void {
    if (this.iban.length < 15) throw new Error("iban too short");
  }
}

class PaymentMethodFactory {
  static create(kind: "card" | "bank", credential: string): PaymentMethod {
    switch (kind) {
      case "card":
        return new CreditCardPayment(credential);
      case "bank":
        return new BankTransferPayment(credential);
    }
  }
}

// exercise the two paths
const created = Order.open("order-1", "EUR", {
  productId: "sku-1",
  unitPrice: Money.of(1999, "EUR"),
  quantity: 2,
});
created.addLine({ productId: "sku-2", unitPrice: Money.of(500, "EUR"), quantity: 1 });
console.log("total minor units:", created.total().amountMinorUnits, "events:", created.raisedEvents());

const reloaded = Order.reconstitute("order-1", "EUR", [
  { productId: "sku-1", unitPrice: Money.of(1999, "EUR"), quantity: 2 },
  { productId: "sku-2", unitPrice: Money.of(500, "EUR"), quantity: 1 },
]);
console.log("reconstituted events (should be empty):", reloaded.raisedEvents());

const payment = PaymentMethodFactory.create("card", "tok_live_abc");
payment.authorize(created.total());
console.log("payment authorized ok");
```

Python, the Entity Factory versus Value Object Factory distinction, plus a
reconstitution classmethod separate from creation, showing the same split as
the TypeScript example in an idiomatic Pythonic shape using classmethods
instead of a dedicated static-method style.

```python
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    amount_minor_units: int
    currency: str

    @classmethod
    def of(cls, amount_minor_units: int, currency: str) -> "Money":
        if amount_minor_units < 0:
            raise ValueError("amount cannot be negative")
        if len(currency) != 3 or not currency.isupper():
            raise ValueError("currency must be a 3 letter ISO code")
        return cls(amount_minor_units, currency)

    def add(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise ValueError("cannot add mismatched currencies")
        return Money.of(self.amount_minor_units + other.amount_minor_units, self.currency)


@dataclass
class BacklogItem:
    id: str
    title: str
    story_points: int


class Product:
    """Aggregate Root. Owns BacklogItem, mirroring Vernon's
    Product.planBacklogItem() Factory Method on Aggregate Root."""

    def __init__(self, product_id: str, name: str) -> None:
        self.id = product_id
        self.name = name
        self._backlog_items: list[BacklogItem] = []
        self._events: list[str] = []

    def plan_backlog_item(self, title: str, story_points: int) -> BacklogItem:
        if story_points <= 0:
            raise ValueError("story points must be positive")
        item = BacklogItem(
            id=f"{self.id}-item-{len(self._backlog_items)}",
            title=title,
            story_points=story_points,
        )
        self._backlog_items.append(item)
        self._events.append(f"BacklogItemPlanned:{item.id}")
        return item

    @property
    def backlog_items(self) -> list[BacklogItem]:
        return list(self._backlog_items)

    @property
    def raised_events(self) -> list[str]:
        return list(self._events)


class ProductFactory:
    """Entity Factory. Product is an Entity (has identity, mutable state
    over time), so its Factory enforces creation invariants and raises
    a creation event. Contrast with Money above, a Value Object Factory,
    which enforces its rule and raises nothing, because Value Objects
    have no life cycle event to announce."""

    @staticmethod
    def create(product_id: str, name: str) -> Product:
        if not name.strip():
            raise ValueError("product name cannot be blank")
        product = Product(product_id, name)
        product._events.append(f"ProductCreated:{product_id}")
        return product

    @staticmethod
    def reconstitute(product_id: str, name: str, backlog: list[dict]) -> Product:
        product = Product(product_id, name)
        for raw in backlog:
            item = BacklogItem(id=raw["id"], title=raw["title"], story_points=raw["points"])
            product._backlog_items.append(item)
        # deliberately does not touch product._events, matching the
        # TypeScript reconstitute() above, no re-raised creation events
        return product


if __name__ == "__main__":
    p = ProductFactory.create("prod-1", "Checkout Redesign")
    backlog_item = p.plan_backlog_item("Add one-click reorder", 5)
    print("created events:", p.raised_events)
    print("backlog item id:", backlog_item.id)

    reloaded = ProductFactory.reconstitute(
        "prod-1",
        "Checkout Redesign",
        [{"id": "prod-1-item-0", "title": "Add one-click reorder", "points": 5}],
    )
    print("reconstituted events (should be empty):", reloaded.raised_events)

    m1 = Money.of(1000, "EUR")
    m2 = Money.of(250, "EUR")
    print("money total:", m1.add(m2))
```

Go, an Abstract-Factory-shaped Dedicated Factory selecting between concrete
implementations of a domain interface from runtime data, the shape Evans
describes as choosing "what concrete subtype of object the client needs."

```go
package main

import (
	"errors"
	"fmt"
)

type Notifier interface {
	Notify(recipient string, message string) error
}

type EmailNotifier struct {
	fromAddress string
}

func (e EmailNotifier) Notify(recipient string, message string) error {
	if e.fromAddress == "" {
		return errors.New("email notifier missing from address")
	}
	fmt.Printf("email to %s from %s: %s\n", recipient, e.fromAddress, message)
	return nil
}

type SmsNotifier struct {
	senderId string
}

func (s SmsNotifier) Notify(recipient string, message string) error {
	if len(s.senderId) == 0 {
		return errors.New("sms notifier missing sender id")
	}
	fmt.Printf("sms to %s from %s: %s\n", recipient, s.senderId, message)
	return nil
}

// NotifierFactory is a Dedicated Factory. The concrete Notifier type is
// chosen from a runtime string, matching Evans's rule that the Factory
// should be abstracted to the type desired, Notifier, not the concrete
// EmailNotifier or SmsNotifier the caller never has to import.
type NotifierFactory struct {
	defaultEmailFrom string
	defaultSmsSender string
}

func (f NotifierFactory) Create(channel string) (Notifier, error) {
	switch channel {
	case "email":
		return EmailNotifier{fromAddress: f.defaultEmailFrom}, nil
	case "sms":
		return SmsNotifier{senderId: f.defaultSmsSender}, nil
	default:
		return nil, fmt.Errorf("unknown notification channel: %s", channel)
	}
}

// OrderConfirmation is an Aggregate whose own Factory Method builds a
// Notifier through the injected NotifierFactory rather than importing a
// concrete notifier type directly, keeping the Aggregate decoupled from
// infrastructure choices.
type OrderConfirmation struct {
	orderId  string
	notifier Notifier
}

func NewOrderConfirmation(orderId string, channel string, factory NotifierFactory) (*OrderConfirmation, error) {
	if orderId == "" {
		return nil, errors.New("orderId is required")
	}
	notifier, err := factory.Create(channel)
	if err != nil {
		return nil, err
	}
	return &OrderConfirmation{orderId: orderId, notifier: notifier}, nil
}

func (c *OrderConfirmation) Send(recipient string) error {
	return c.notifier.Notify(recipient, fmt.Sprintf("order %s confirmed", c.orderId))
}

func main() {
	factory := NotifierFactory{defaultEmailFrom: "orders@example.com", defaultSmsSender: "ORDERS"}

	confirmation, err := NewOrderConfirmation("order-42", "email", factory)
	if err != nil {
		panic(err)
	}
	if err := confirmation.Send("customer@example.com"); err != nil {
		panic(err)
	}

	smsConfirmation, err := NewOrderConfirmation("order-43", "sms", factory)
	if err != nil {
		panic(err)
	}
	if err := smsConfirmation.Send("+15551234567"); err != nil {
		panic(err)
	}

	if _, err := factory.Create("carrier-pigeon"); err != nil {
		fmt.Println("expected rejection:", err)
	}
}
```

## 18. References

- Eric Evans. *Domain-Driven Design. Tackling Complexity in the Heart of
  Software*. Addison-Wesley, 2003. Chapter 6, "The Life Cycle of a Domain
  Object", section "Factories". Original source for the pattern, its
  placement alongside Aggregate and Repository, and the atomicity and
  invariant-enforcement rules quoted in dimensions 3 and 4.
- rudradixit, "Chapter 6, The Lifecycle Of A Domain Object", GitHub wiki
  summary of Evans's chapter, used here for verified direct-quote wording of
  Evans's Factory rules. Verified 2026-08-02.
  https://github.com/rudradixit/domain-driven-design-notes/wiki/Chapter-6-The-Lifecycle-Of-A-Domain-Object
- Herberto Graca. "DDD.6, The lifecycle of a domain object". Independent
  summary of Evans's Chapter 6, used here for the three-way Factory Method,
  Abstract Factory Class, Builder Class classification in dimensions 1 and
  8. Verified 2026-08-02.
  https://herbertograca.com/2015/10/04/domain-driven-design-by-eric-evans-chap-6-the-lifecycle-of-a-domain-object/
- Vaughn Vernon. *Implementing Domain-Driven Design*. Addison-Wesley, 2013.
  Chapter 11, "Factories", page 389. Section "Factory Method on Aggregate
  Root", page 391, `Product.planBacklogItem()` example. Source for the
  naming discipline that most real Factories are methods on an existing
  Aggregate Root, used in dimensions 1, 3, and 13.
- InformIT. "Implementing Domain-Driven Design, Aggregates, Using Aggregates
  in the Scrum Core Domain". Excerpt corroborating the
  `planBacklogItem()` example and its Factory Method characterization.
  Verified 2026-08-02.
  https://www.informit.com/articles/article.aspx?p=2020371
- O'Reilly. "Chapter 10. Aggregates", table of contents for *Implementing
  Domain-Driven Design*, used to confirm chapter and page numbering.
  Verified 2026-08-02.
  https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/ch10.html
- Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design
  Patterns. Elements of Reusable Object-Oriented Software*. Addison-Wesley,
  1994. Chapter 3, Creational Patterns. Source for the ancestor Factory
  Method and Abstract Factory patterns referenced in dimensions 1 and 13.
  See this repository's `01-gof/factory-method.md` and
  `01-gof/abstract-factory.md` entries for full treatment.
- AxonIQ. "AggregateFactory (Axon Framework 2.0.6 API)". Java framework API
  documentation, used as a named production use in dimension 9 and a failure
  mode source in dimension 11. Verified 2026-08-02.
  https://apidocs.axoniq.io/2.0/org/axonframework/eventsourcing/AggregateFactory.html
- EventFlow. "Aggregates", official documentation for the open-source
  EventFlow CQRS and event-sourcing framework for .NET. Used as a named
  production use in dimension 9. Verified 2026-08-02.
  https://geteventflow.net/basics/aggregates/
- EventFlow. GitHub repository, github.com/eventflow/EventFlow. Confirms the
  framework's identity, purpose, and open-source status cited in dimension
  9. Verified 2026-08-02.
  https://github.com/eventflow/EventFlow
- Broadway. GitHub repository, github.com/broadway/broadway. Open-source PHP
  CQRS and event-sourcing framework, confirms its `AggregateFactory`
  component and its stated lineage from Axon Framework and prior CQRS
  frameworks, used as a named production use in dimension 9. Verified
  2026-08-02.
  https://github.com/broadway/broadway
