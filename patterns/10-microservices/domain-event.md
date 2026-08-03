---
name: Domain Event
slug: domain-event
family: 10-microservices
category: Behavioral
aliases: [Application Event, Domain Notification]
first_described: "Evans 2003, Fowler eaaDev catalog"
maturity: canonical
related: [event-sourcing, transactional-outbox, saga, cqrs, aggregate, mediator, observer]
incompatible_with: []
verified: 2026-08-02
---

# Domain Event

## 1. Name, aliases, and lineage

The canonical name is Domain Event. The term was popularized inside the
domain-driven design community through Eric Evans, *Domain-Driven Design.
Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003, where an
Aggregate is described as the unit that spans a transaction and rules crossing
Aggregate boundaries are resolved through event processing rather than a single
atomic write. Evans states the underlying tension plainly, that a rule spanning
Aggregates "will not be expected to be up-to-date at all times. Through event
processing, batch processing, or other update mechanisms, other dependencies
can be resolved within some specific time" (Evans, *Domain-Driven Design*,
page 128, quoted at
[Microsoft Learn, Domain events. Design and implementation](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation),
verified 2026-08-02).

Martin Fowler catalogued Domain Event as a named pattern in his enterprise
application architecture development notes, defining its intent in one line.
"Captures the memory of something interesting which affects the domain"
([Martin Fowler, DomainEvent](https://martinfowler.com/eaaDev/DomainEvent.html),
verified 2026-08-02). Fowler's page frames the pattern as a way to fold many
different input streams, a user click, an incoming message, a scheduled job,
into one uniform sequence of event objects the rest of the system can react to
and record, which is what gives Domain Event its dual identity as both a
behavioral trigger and an audit trail.

The alias Application Event appears where a codebase wants to distinguish an
event raised purely for in-process side effects from one that crosses a service
boundary. The alias Domain Notification appears in older .NET and Java
enterprise codebases that predate the DDD vocabulary becoming mainstream and
built the same mechanism under the Observer name before the DDD community gave
it a settled term.

A separate and frequently confused term is Integration Event, used
specifically in the Microsoft .NET microservices reference architecture to name
the cross-boundary counterpart of a Domain Event. The distinction matters
enough that it is its own dimension below, because conflating the two is the
single most common structural mistake made with this pattern.

## 2. Problem and context

An operation on one part of a domain model needs to trigger a reaction in
another part of the model, or in another bounded context entirely, and the
class performing the operation should not need to know the reaction exists.
Consider an order-placement flow. Placing an order needs to reserve inventory,
create a shipping record, notify a loyalty program, and update a fraud-scoring
model. If the code that creates the order also calls the inventory service,
the shipping service, the loyalty service, and the fraud service directly, the
order-creation class grows a dependency on every consumer of the fact that an
order was created, and every new consumer means editing and redeploying the
order-creation class again.

The context in which Domain Event applies is a system organized around
Aggregates, in the DDD sense, where a single write transaction is scoped to one
Aggregate instance and any rule that needs a second Aggregate, or a second
bounded context, or an external system, to react must do so outside that
transaction, or in a way that does not couple the writer to the reader.
Domain Event solves this by having the Aggregate record a fact, expressed as an
immutable, past-tense-named event object, rather than calling out to anyone.
Some other part of the system, a dispatcher, an event bus, or a handler
registry, is responsible for finding the interested parties and delivering the
event to them. The Aggregate that raised the event has no reference to, and no
knowledge of, who consumes it.

This context also explains why the pattern is filed under microservices
patterns in this repository even though its origin is a single-process DDD
technique. In a microservice architecture, the same shape, a service records
"a fact happened here," and everyone downstream who cares reacts to it, becomes
the primary mechanism for keeping services autonomous while their data stays
eventually consistent, which is why Chris Richardson's microservices.io catalog
lists Domain Event as one of the core data-management patterns for services,
alongside Saga and CQRS
([microservices.io, Pattern. Domain event](https://microservices.io/patterns/data/domain-event.html),
verified 2026-08-02).

## 3. Forces

Coupling versus knowledge. The writer must not know its readers, which favors
Domain Event over a direct method call, but total ignorance means the writer
also cannot know whether the reaction actually happened, which pushes some
systems toward a synchronous call anyway when the reaction is business-critical
and must be confirmed before the writer proceeds.

Consistency versus availability. A synchronous, same-transaction dispatch of a
domain event keeps every side effect inside one atomic commit, at the cost of
locking every Aggregate touched by every handler for the duration of that
transaction. An asynchronous dispatch releases the lock immediately and lets
each handler fail or retry independently, at the cost of a window in which the
system is observably inconsistent, the order exists but the loyalty points do
not yet.

Auditability versus storage cost. Because a domain event is, by definition, a
record of something that already happened and therefore never changes, keeping
every event ever raised produces a complete, replayable history of the system.
That history is valuable for debugging, compliance, and rebuilding read models,
but every event kept forever is also a byte that stays paid for, and a
schema that must stay readable for as long as the oldest kept event exists.

Cognitive load versus explicitness. A codebase with domain events makes side
effects visible as named handler classes rather than buried inline in a service
method, which several practitioners argue is the pattern's primary value
independent of any distribution concern, because "using domain events makes the
concept explicit, because there's a `DomainEvent` and at least one
`DomainEventHandler` involved" rather than a rule "coupled, implicitly, to the
code," where a reader has to trace execution to discover it exists
([Microsoft Learn, Domain events](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation),
verified 2026-08-02). The cost is indirection. A reader following one method
call now has to know a dispatcher exists and go looking for every handler
subscribed to that event type before understanding the full effect of one line
of code.

Team topology. Domain events favor teams that own a bounded context end to end
and want other teams to depend on published facts rather than on shared code or
shared tables, which is exactly the coupling reduction that makes independent
service deployment possible, but it requires the publishing team to treat the
event's shape as a versioned public contract, not an internal implementation
detail they can rename at will.

This dimension is engineering judgement. The weighting between these forces is
a design decision made per system, not a fact recorded anywhere.

## 4. Applicability and non-applicability

Reach for Domain Event when a change to one Aggregate needs to trigger a rule
that belongs to a different Aggregate or a different bounded context, when the
list of things that must react to a given business fact is expected to grow
over time and should grow without modifying the code that produced the fact,
when the system needs a durable, ordered record of what happened for audit,
debugging, or read-model rebuilding, and when the writer and the reader can
tolerate the reaction happening a moment after the fact, not necessarily in the
same instruction.

Do not reach for Domain Event when the caller needs an immediate answer before
it can proceed. If placing an order must know synchronously whether payment
authorization succeeded before it can return a success response to the user,
that is a direct call or a synchronous command, not a fire-and-forget event,
because a domain event has no return value and no guaranteed single consumer.

Do not reach for Domain Event to communicate between two classes inside the
same small module where a direct method call is perfectly readable. The pattern
earns its indirection cost only when the decoupling it buys is real, meaning
the number or identity of consumers genuinely varies or is genuinely unknown to
the producer. Wrapping every internal call in an event object because the
pattern exists produces a codebase where following a single business operation
requires jumping through a dispatcher and back, with no decoupling benefit to
show for it.

Do not reach for Domain Event as a substitute for a database transaction when
strict, immediate consistency between two pieces of state is a hard business
requirement, for example debiting one account and crediting another must never
be observably split. In that specific case the correct tool is a single
transaction across both writes, not an event and a handler that might run
seconds later, might fail, and might run twice.

Do not reach for Domain Event when the event volume is extremely high and every
event genuinely needs the same, uniform, synchronous handling with no variation
by consumer, for example a high-frequency telemetry stream feeding one
aggregator. A dedicated streaming pipeline, not a domain-event dispatcher
designed around aggregate boundaries and named handlers, is the better tool for
that volume and shape.

Do not conflate Domain Event with Integration Event and reach for the same
mechanism at both scopes. An event meant only to keep two Aggregates in the
same bounded context consistent should never be serialized straight onto a
message broker for external services to consume, because that exposes an
internal implementation detail as a public API and removes the option to
reshape that internal event later without breaking someone else's service.

## 5. Structure

**Domain Event.** An immutable value object named in the past tense, carrying
every piece of data a handler could need without having to reload the
Aggregate that raised it. It has no behavior beyond exposing its data.

**Aggregate (event source).** The entity or aggregate root whose state change
the event describes. It is responsible for constructing the event and adding
it to its own pending-events collection. It has no reference to any handler,
dispatcher, or event bus.

**Event collection (per Aggregate instance).** A list, owned by the Aggregate
or its base class, that accumulates events raised during the current unit of
work. It exists so raising an event and dispatching it are two separate steps,
which is what lets the framework decide when dispatch happens relative to the
transaction boundary.

**Dispatcher (or mediator, or event bus).** The component that, at a defined
point, typically just before or just after the unit of work commits, walks
every Aggregate that raised events during that unit of work, and for each
event, finds every handler registered for that event's type and invokes them.

**Event handler.** A class or function registered for exactly one event type.
It performs the side effect, updating another Aggregate, calling an external
system, or publishing an Integration Event outward. A single event type may
have zero, one, or many handlers, and the producer never knows the count.

**Unit of work / transaction boundary.** The scope, usually one database
transaction, that determines whether the raising of the event and the handling
of the event are atomic with each other or eventually consistent with each
other. This participant is what makes the difference between an in-process
domain event and a distributed integration event a deliberate architectural
choice rather than an accident of implementation.

## 6. ASCII structure diagram

```text
+----------------------+         raises          +------------------+
|  Aggregate (Order)    |------------------------>| DomainEvent       |
|  - state               |                         | (OrderPlaced)     |
|  - pendingEvents[]      |<----- appended to ----- | - orderId          |
+----------------------+                          | - occurredAt       |
          |                                        | - payload          |
          | reads on commit                        +------------------+
          v                                                  |
+----------------------+     for each event, find    matched by type
|  Dispatcher /         |---------------------------------->|
|  Mediator              |                                    v
+----------------------+                          +------------------+
          |                                        | EventHandler A    |
          | invokes zero, one, or many              | (ReserveStock)     |
          v                                        +------------------+
+----------------------+                          +------------------+
|  EventHandler B        |                          | EventHandler C     |
|  (AwardLoyaltyPoints)   |                          | (PublishIntegration|
+----------------------+                          |  Event to bus)     |
                                                    +------------------+
```

The Aggregate never points down toward the Dispatcher or the handlers. Every
arrow that reaches a handler originates at the Dispatcher, not at the
Aggregate, which is the structural feature that makes the coupling one-way.

## 7. Dynamics

The sequence below follows the deferred-dispatch approach, which is the shape
recommended by both the eShop reference architecture and Jimmy Bogard's widely
cited post, because it keeps the raising of the event, a pure in-memory
operation, cleanly separated from the dispatching of the event, which may touch
infrastructure ([Jimmy Bogard, "A better domain events pattern," 2014,
quoted at Microsoft Learn](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation),
verified 2026-08-02).

```text
Caller           Order (Aggregate)      pendingEvents[]     UnitOfWork          Dispatcher        Handler(s)
  |                     |                      |                 |                  |                 |
  |--place(command)---->|                      |                 |                  |                 |
  |                     |--validate state------|                 |                  |                 |
  |                     |--mutate state --------|                 |                  |                 |
  |                     |--new OrderPlaced------------------------>|                 |                 |
  |                     |  (append event)                          |                 |                 |
  |<--returns-----------|                      |                 |                  |                 |
  |                                                                 |                  |                 |
  |----------commit()--------------------------------------------->|                  |                 |
  |                                                                 |--drain events--->|                 |
  |                                                                 |                  |--find handlers->|
  |                                                                 |                  |--invoke each--->|
  |                                                                 |                  |<--complete------|
  |                                                                 |<--events cleared-|                 |
  |<----------------------------commit result----------------------|                  |                 |
```

The key timing decision is whether the Dispatcher runs inside the same database
transaction that persists the Aggregate's state change, or after that
transaction has already committed. Running inside the same transaction gives
atomicity, every handler's writes commit or roll back together with the
Aggregate's write, at the cost of holding locks on every Aggregate a handler
touches for the whole duration. Running after the commit gives each handler its
own transaction and releases the original lock immediately, at the cost of a
window where the order exists and the loyalty points do not yet, which the
Microsoft reference architecture calls out explicitly as "eventual consistency
across aggregates," contrasted with "single transaction across aggregates," and
states plainly that both are valid choices depending on the domain's actual
consistency requirement, not a universal rule
([Microsoft Learn, Domain events](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation),
verified 2026-08-02).

## 8. Implementation variants

**Immediate dispatch, static registry.** Udi Dahan's original 2008 formulation
raises and dispatches an event in one call through a static `DomainEvents`
class, so a handler runs the instant the event is raised, inline in the same
call stack ([Udi Dahan, "Domain Events. Take 2," 2008](https://udidahan.com/2008/08/25/domain-events-take-2/),
referenced at [Microsoft Learn, Domain events](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation),
verified 2026-08-02). This variant is the simplest to reason about but is
hardest to test, because a unit test of the Aggregate's method now also
executes every handler's side effect unless the test explicitly swaps the
static registry for a fake.

**Deferred dispatch, collected on the entity.** The Aggregate accumulates
events into its own list, and a unit-of-work or ORM save-changes hook drains
that list at commit time. This is the variant used by the eShop reference
architecture and recommended in Bogard's 2014 follow-up post specifically to
decouple raising from dispatching for testability
([Jimmy Bogard, "A better domain events pattern"](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation),
verified 2026-08-02). A pure unit test of the Aggregate can assert that the
correct event was appended to the list without any handler ever running.

**Event sourcing as the persistence mechanism itself.** Rather than the
Aggregate's current state being the source of truth and events being a side
channel, the sequence of domain events IS the source of truth, and current
state is a projection computed by replaying every event for that Aggregate.
This variant merges Domain Event with the Event Sourcing pattern, and it is
covered as its own entry in this repository because the consequences, storage
model, and failure modes diverge sharply from the two variants above.

**Language-idiomatic closures instead of handler classes.** In languages with
first-class functions, a handler is often a plain function or lambda registered
against an event type in a map, rather than a class implementing a handler
interface. This changes nothing structurally but removes the ceremony of a
one-method interface implementation, and is the idiomatic shape in Go, Python,
and TypeScript, versus the interface-based shape common in Java and C#.

**Outbox-backed dispatch for cross-service delivery.** When a domain event
must also become an Integration Event delivered to another service, the
handler that would publish to a message broker instead writes a row to an
outbox table in the same local transaction as the Aggregate's state change,
and a separate relay process reads that table and publishes to the broker
afterward. This is the Transactional Outbox pattern, and it exists specifically
to close the gap between "the local write committed" and "the message was
published," a gap that two-phase commit across a database and a broker is
usually too costly or unavailable to close directly
([microservices.io, Pattern. Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html),
verified 2026-08-02).

## 9. Known production uses

**eShop, the Microsoft .NET microservices reference architecture.** The
Ordering microservice raises an `OrderStartedDomainEvent` from the `Order`
aggregate when a user begins checkout, and a registered handler,
`ValidateOrAddBuyerAggregateWhenOrderStartedDomainEventHandler`, reacts by
creating or updating the `Buyer` aggregate and then constructing a separate
Integration Event to notify other microservices, with the source visible in
the public repository
([dotnet/eShop, `Order.cs`](https://github.com/dotnet/eShop/blob/main/src/Ordering.Domain/AggregatesModel/OrderAggregate/Order.cs),
and [the handler](https://github.com/dotnet/eShop/blob/main/src/Ordering.API/Application/DomainEventHandlers/ValidateOrAddBuyerAggregateWhenOrderStartedDomainEventHandler.cs),
both cited via the Microsoft Learn documentation page that walks through this
exact code, verified 2026-08-02).

**MediatR, the in-process mediator library used by eShop and a large share of
production .NET codebases for domain-event dispatch.** MediatR's `INotification`
and `INotificationHandler<T>` interfaces are the concrete registry-and-dispatch
mechanism the eShop code above builds on. Its README states its purpose as
supporting "request/response, commands, queries, notifications and events,
dispatched via mediator pattern," where notifications are the one-to-many,
fire-and-forget shape domain events require
([jbogard/MediatR](https://github.com/jbogard/MediatR), verified 2026-08-02).

**Amazon EventBridge.** AWS documents EventBridge as "a serverless service
that uses events to connect application components together" for building
event-driven applications, with an event bus that
"receives events and delivers them to zero or more targets," which is the same
producer-does-not-know-its-consumers structure this pattern describes, applied
at the scale of an entire cloud account rather than one process
([AWS documentation, What is Amazon EventBridge](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html),
verified 2026-08-02). Teams that implement Domain Event inside a service and
then need the fact to leave that service commonly route the outward-facing
Integration Event through EventBridge, or an equivalent broker, rather than
calling downstream services directly.

## 10. Consequences

Positive.

- Producers of a fact are decoupled from every current and future consumer of
  that fact, so adding a new reaction to an existing business event means
  writing a new handler, not modifying the code that raises the event.
- The system gains an explicit, named vocabulary for what happens, expressed
  as classes a reader can find by searching for the past-tense verb, rather
  than a rule buried inline inside an unrelated method.
- Because an event is immutable and represents something that already
  happened, the sequence of events a system has raised is naturally a
  replayable, auditable log, which several teams reuse to rebuild read models
  or debug production incidents after the fact.
- Handlers can be added, removed, or reordered independently, which lets
  different teams own different reactions to the same underlying fact without
  coordinating a shared change to the producing code.

Negative.

- Indirection cost. Following what a single business operation actually does
  now requires knowing a dispatcher exists and searching for every handler
  registered for the events it raises, which is genuinely harder to trace than
  a direct call chain, especially for a reader new to the codebase.
- A domain event has no return value, so the producer cannot learn whether a
  handler succeeded, failed, or even ran, unless the design deliberately adds a
  separate mechanism, for example a saga, to track and report on completion.
- When handlers run in the same transaction as the write that raised the
  event, the transaction now holds locks on every Aggregate any handler
  touches, which can turn a fast single-Aggregate write into a slow
  multi-Aggregate one, exactly the database-lock cost the Microsoft reference
  architecture flags as the reason some teams choose eventual consistency
  instead ([Microsoft Learn, Domain events](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation),
  verified 2026-08-02).
- When handlers run after the transaction commits, the system has a genuine
  window of observable inconsistency, and any handler failure in that window
  needs its own retry and compensation story, which is nontrivial engineering
  effort that a direct synchronous call would not have required.

## 11. Failure modes and misuse

**Symptom.** A handler runs twice for the same business fact, producing a
duplicate side effect such as two loyalty-point awards for one order.
**Cause.** The dispatcher retried delivery after a transient failure, or the
consumer process crashed and restarted after handling the event but before
acknowledging it, and the event was redelivered. Domain events dispatched
through a message broker or a retrying job runner are, in practice, delivered
at-least-once, not exactly-once, unless the handler itself is made idempotent.
**Fix.** Give every event a stable identifier and have each handler record
which event identifiers it has already processed, rejecting a repeat before it
performs the side effect a second time, the idempotent-consumer technique.

**Symptom.** The write that raised an event committed successfully, but the
event never reaches its consumers, and nothing downstream ever happens, with no
error anywhere in the logs. **Cause.** The event was held only in memory, in
the Aggregate's pending-events list, and the process crashed, or an
unhandled exception was thrown, between the transaction commit and the
dispatcher draining the list, so the event was silently lost. **Fix.** Persist
the event durably in the same transaction that changes the Aggregate's state,
for example via the Transactional Outbox pattern, so the event's existence is
guaranteed once the transaction commits, independent of process lifetime.

**Symptom.** A domain event meant only for internal, same-bounded-context
consistency shows up as a field in another team's public API contract, and
renaming an internal event breaks a service that team does not own. **Cause.**
The domain event object itself was serialized directly onto a shared message
broker and treated as the Integration Event, collapsing the distinction
between the two. **Fix.** Construct a separate, deliberately versioned
Integration Event from inside the domain-event handler, and never let the
internal domain-event's shape leak past the process boundary.

**Symptom.** A single business action, for example placing an order, ends up
touching five, ten, or more Aggregates synchronously inside one transaction,
and write latency on that action climbs steadily as more handlers are added
over time. **Cause.** Every handler for the raised event was wired to run
inside the original transaction by default, without anyone deciding, per
handler, whether that handler's side effect genuinely needs atomic consistency
with the write or can tolerate eventual consistency. **Fix.** Split handlers
explicitly into same-transaction handlers, reserved for rules the domain
experts say must never be observably inconsistent, and after-commit handlers
for everything else, per the deliberate choice the Microsoft reference
architecture recommends making per handler rather than defaulting one way for
the entire system.

**Symptom.** Tests of a single Aggregate method are slow, flaky, or require an
entire application context to be booted, even though the method under test
only mutates in-memory state. **Cause.** The codebase uses immediate,
static-registry dispatch, so calling the Aggregate's method also executes every
registered handler, including handlers that call a database or an external
system, as a side effect of the unit test. **Fix.** Switch to deferred
dispatch, where raising an event only appends to a list, so a unit test of the
Aggregate can assert on the contents of that list without triggering any
handler at all.

## 12. Trade-off matrix

| Force | Domain Event | Direct method call | Event Sourcing | Saga (choreography) |
|---|---|---|---|---|
| Producer/consumer coupling | Producer unaware of consumers | Producer must know every consumer | Producer unaware, events ARE the state | Producer unaware, but participants must agree on the event sequence |
| Consistency model | Chosen per handler, sync or async | Always immediate and atomic | Eventual for projections, event append is atomic | Eventual across the whole workflow, by design |
| Traceability of one flow | Requires searching for handlers | Trivial, one call chain | Requires replaying the event stream | Requires reconstructing the choreography across services |
| Testability of the producer alone | High with deferred dispatch | High, mock the callee | High, assert appended events | Lower, one service's behavior implies others |
| Storage growth | Optional, only if events are kept | None beyond current state | Unbounded by design, must be managed | None beyond current state per service |
| Best fit | One Aggregate's side effects need to fan out or grow over time | A tightly scoped, unchanging dependency | Full history and time-travel state are required | A multi-step business process spans several services with no orchestrator |

The alternatives are named patterns, not strawmen. A direct method call is the
baseline every author of this pattern explicitly argues against for the
fan-out case. Event Sourcing and Domain Event are close cousins that are
frequently, and incorrectly, treated as the same thing, so the comparison row
by row is deliberately included to make the actual differences explicit rather
than assumed.

## 13. Related and incompatible patterns

**Event Sourcing.** A superset relationship, not a rival. Event Sourcing uses
domain events as the sole persistence mechanism for an Aggregate's state, so
every event-sourced system contains Domain Event, but not every system that
uses Domain Event is event sourced. A system can raise and dispatch domain
events while still persisting current state directly in a table, which is the
far more common combination in practice.

**Transactional Outbox.** A composition partner that solves the specific
reliability gap dimension 11 describes above, guaranteeing that a raised
domain event that must leave the process boundary is not lost if the process
crashes between commit and publish. Domain Event answers "what happened and who
should react," Transactional Outbox answers "how do we guarantee delivery of
that fact across a process boundary."

**CQRS.** A frequent companion where a domain-event handler is specifically
responsible for updating a denormalized read model, so queries never touch the
write-side Aggregates at all. The event is the mechanism that keeps the read
model in sync with the write model.

**Saga (orchestration or choreography).** A saga coordinates a multi-step
business process across several services, and choreography-based sagas are
built directly on domain events, or their cross-boundary counterpart
integration events, where each service reacts to the previous step's event and
raises its own event in turn, with no central coordinator.

**Mediator.** The in-process dispatcher described in dimension 5 is frequently
implemented as an instance of the Mediator pattern from the original GoF
catalog, where the mediator's job is specifically to decouple a set of
colleague objects, here the Aggregate that raises the event and the handlers
that consume it, from knowing about each other directly.

**Observer.** Domain Event and Observer solve structurally similar
producer-does-not-know-consumer problems, and the difference is largely one of
vocabulary and intent rather than mechanism. Observer, as GoF describe it, is a
general subject-observer relationship with no requirement that the notification
represent an immutable, named, past-tense business fact, while Domain Event
specifically constrains the notification to carry that DDD-flavored meaning and
typically adds the deferred-dispatch, transaction-aware machinery this entry
describes.

No incompatible patterns are recorded for this entry. Domain Event is
deliberately additive, it changes how a fact is communicated, not how state is
structured, so it composes with essentially every structural and creational
pattern in this catalog without conflict.

## 14. Refactoring path in and out

Introducing Domain Event into code that currently calls its collaborators
directly proceeds in small, reversible steps.

1. Identify the Aggregate method whose side effects should be decoupled, and
   list every direct call it currently makes to another Aggregate, service, or
   external system as a result of its own state change.
2. Define an immutable event class, named in the past tense, carrying every
   piece of data the current direct calls need, so a handler will not have to
   reload the Aggregate to get that data.
3. Add a pending-events collection to the Aggregate, or its base class, and
   change the method to append the new event object instead of making the
   direct calls, leaving the direct calls commented out or covered by a
   feature flag during the transition, not deleted outright.
4. Write one handler per direct call that was removed, moving that exact logic
   into the handler unchanged, and register each handler for the new event
   type.
5. Wire a dispatcher into the unit-of-work commit path, so the pending events
   are drained and dispatched at a single, well-defined point.
6. Run the existing test suite for the Aggregate and for each moved side
   effect, confirming behavior is identical, then remove the old direct calls
   and any feature flag entirely.
7. Decide explicitly, per handler, whether it must run inside the same
   transaction as the state change or may run after commit, rather than
   leaving every handler on whatever the dispatcher's default happens to be.

Removing Domain Event, when the fan-out it was built for never materialized and
only one handler has ever existed for a given event type, proceeds in reverse.
Confirm the event genuinely has exactly one consumer and no plan exists to add
a second. Inline the single handler's logic back into the Aggregate's method as
a direct call, or a direct call to a well-named collaborator method. Delete the
event class and its registration. Re-run the same tests to confirm no
observable behavior changed. This reversal is rarely undertaken in the DDD
Aggregate case because the decoupling is usually worth keeping even with a
single handler, but it is common in the outward-facing Integration Event case,
where an event published for a consumer that has since been decommissioned
should be retired rather than left to be dispatched into the void.

## 15. Testing and verification

Testing is largely engineering practice rather than a sourced claim, this
dimension is engineering judgement.

With deferred dispatch, testing the producer is straightforward. Call the
Aggregate method under test, then assert on the contents of its pending-events
collection, checking the event's type and its data, without invoking any
handler or any infrastructure. This is the single biggest testability argument
for choosing deferred dispatch over immediate dispatch, and it is why the fix
for the flaky-test failure mode in dimension 11 is exactly this change.

Testing a handler is a unit test like any other, given an event instance,
assert on the handler's observable effect, with every collaborator the handler
calls, a repository, an external client, replaced by a test double. Because a
handler is registered against a single event type and has one job, these tests
tend to be small and fast.

Testing the dispatcher itself, the wiring that finds and invokes handlers for a
given event type, is an integration test, not a unit test, because its entire
purpose is to prove that registration actually resolves to the correct
handlers at runtime, which a unit test with a fake registry cannot verify.

Testing end-to-end delivery reliability, specifically that an event raised
during a transaction that later rolls back is never dispatched, and that an
event raised during a transaction that commits is dispatched exactly once or
is safely retryable, requires a test that exercises the real transaction
boundary, typically against a real or embedded database rather than an
in-memory fake, because the timing relationship between commit and dispatch is
exactly the thing under test.

For the Transactional Outbox composition described in dimension 13, a contract
test on the outbox table itself, asserting that a row is written in the same
transaction as the Aggregate's state change and never written if that
transaction rolls back, is the test that actually protects the reliability
guarantee, and it is easy to accidentally skip because it requires deliberately
forcing a rollback mid-test rather than only testing the happy path.

## 16. Observability signals

A healthy domain-event system exposes, at minimum, a count of events raised per
event type per unit of time, a count of events successfully dispatched per
event type, and the difference between those two counts, which should trend
toward zero and never grow without bound. A growing gap between raised and
dispatched is the earliest observable sign of the lost-event failure mode
described in dimension 11.

Per-handler latency and per-handler error rate, tagged by both event type and
handler name, let a team see which specific reaction to a given fact is slow or
failing, rather than only seeing that "something downstream of order placement
is degraded." Without this per-handler breakdown, a single misbehaving handler
can be invisible inside an aggregate metric that looks acceptable on average.

For any handler that must be idempotent because delivery is at-least-once, per
dimension 11, a duplicate-detection counter, how many times a handler saw an
event identifier it had already processed and correctly skipped, is worth
exposing directly. A duplicate rate that suddenly spikes usually indicates a
consumer crash-loop or a broker-level redelivery storm rather than a normal
retry pattern, and is worth alerting on separately from the plain error rate.

For a deferred-dispatch implementation specifically, the time between an
event's creation timestamp and its actual dispatch timestamp is the signal that
reveals whether the eventual-consistency window described in dimension 7 is
staying within the bound the business actually agreed to, or silently growing
as load increases.

A healthy dashboard shows dispatched count tracking raised count closely, a
flat or near-zero duplicate rate, and per-handler latency stable under load. A
failing instance shows a widening gap between raised and dispatched, a rising
duplicate rate, or one handler's latency climbing while its siblings stay flat,
each of which points at a different one of the failure modes in dimension 11.

## 17. Security and privacy implications

A domain event's data field frequently carries personal or otherwise sensitive
information directly, because the whole point of the pattern is giving a
handler everything it needs without a second lookup, and the eShop example in
this entry's own code sample carries a payment card number and card security
number inside the event object. Any event that is persisted, whether in an
in-memory list awaiting dispatch, an outbox table, or a durable event store for
event sourcing, inherits every data-retention, encryption-at-rest, and
access-control obligation that the underlying data itself carries, and it is a
real and easy mistake to apply those controls to the primary entity table while
forgetting they also apply to the event log sitting beside it.

Because a domain event is immutable by design, and because event sourcing in
particular treats the full event history as the permanent source of truth, a
"right to erasure" or similar data-subject deletion request is structurally
awkward to satisfy for any event that recorded that person's data, since the
pattern's core guarantee is that a past fact never changes. Systems that must
support deletion commonly resolve this by never putting directly identifying
data in the event payload at all, storing only a reference identifier in the
event and keeping the actual personal data in a separate, mutable, deletable
store the handler looks up when it needs it.

Where a domain event crosses a trust boundary as an Integration Event,
published to a message broker that other services, potentially other teams, or
in a multi-tenant system potentially other customers' infrastructure, can
subscribe to, the event's payload becomes the attacker's or the accidental
over-sharer's easiest source of information leakage, because a broker
subscription is frequently broader than the set of people who should actually
see that data. The construction of a deliberately separate, minimized
Integration Event described in dimension 13, rather than serializing the
internal domain event directly onto the broker, is as much a security boundary
as it is an API-versioning boundary, and treating it only as the latter misses
half the reason it matters.

## 18. References

1. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, page 128, quoted at
   [Microsoft Learn, Domain events. Design and implementation](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation),
   verified 2026-08-02.
2. Martin Fowler, "DomainEvent," enterprise application architecture
   development notes,
   [martinfowler.com/eaaDev/DomainEvent.html](https://martinfowler.com/eaaDev/DomainEvent.html),
   verified 2026-08-02.
3. Chris Richardson, "Pattern. Domain event,"
   [microservices.io/patterns/data/domain-event.html](https://microservices.io/patterns/data/domain-event.html),
   verified 2026-08-02, referencing Chris Richardson, *Microservices Patterns*,
   Manning, 2018.
4. Chris Richardson, "Pattern. Transactional outbox,"
   [microservices.io/patterns/data/transactional-outbox.html](https://microservices.io/patterns/data/transactional-outbox.html),
   verified 2026-08-02.
5. Vaughn Vernon, "Effective Aggregate Design. Part II. Making Aggregates Work
   Together," 2011,
   [dddcommunity.org PDF](https://dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_2.pdf),
   URL confirmed reachable 2026-08-02, passage quoted via
   [Microsoft Learn, Domain events](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation),
   verified 2026-08-02.
6. Jimmy Bogard, "Strengthening your domain. Domain Events," 2010, and "A
   better domain events pattern," 2014, both quoted and linked at
   [Microsoft Learn, Domain events](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation),
   verified 2026-08-02.
7. Udi Dahan, "Domain Events. Take 2," 2008,
   [udidahan.com/2008/08/25/domain-events-take-2](https://udidahan.com/2008/08/25/domain-events-take-2/),
   referenced at Microsoft Learn as above, verified 2026-08-02.
8. Microsoft Learn, "Domain events. Design and implementation,"
   [learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation),
   verified 2026-08-02.
9. dotnet/eShop reference application, `Order.cs`,
   [github.com/dotnet/eShop/blob/main/src/Ordering.Domain/AggregatesModel/OrderAggregate/Order.cs](https://github.com/dotnet/eShop/blob/main/src/Ordering.Domain/AggregatesModel/OrderAggregate/Order.cs),
   and `ValidateOrAddBuyerAggregateWhenOrderStartedDomainEventHandler.cs`,
   [github.com/dotnet/eShop/blob/main/src/Ordering.API/Application/DomainEventHandlers/ValidateOrAddBuyerAggregateWhenOrderStartedDomainEventHandler.cs](https://github.com/dotnet/eShop/blob/main/src/Ordering.API/Application/DomainEventHandlers/ValidateOrAddBuyerAggregateWhenOrderStartedDomainEventHandler.cs),
   both cited via the Microsoft Learn page above, verified 2026-08-02.
10. Jimmy Bogard, MediatR, jbogard/MediatR,
    [github.com/jbogard/MediatR](https://github.com/jbogard/MediatR),
    verified 2026-08-02.
11. Amazon Web Services, "What Is Amazon EventBridge?"
    [docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html),
    verified 2026-08-02.

## Code examples

Three languages, three idiomatic shapes for the same deferred-dispatch
mechanism from dimension 8. Each example models an `Order` aggregate that
raises an `OrderPlaced` event, a dispatcher that resolves handlers by event
type, and two handlers to demonstrate the one-to-many fan-out.

### TypeScript

```typescript
type DomainEvent = { readonly kind: string; readonly occurredAt: Date };

class OrderPlaced implements DomainEvent {
  readonly kind = "OrderPlaced";
  readonly occurredAt = new Date();
  constructor(readonly orderId: string, readonly total: number) {}
}

class Order {
  private pending: DomainEvent[] = [];
  private constructor(readonly id: string, private total: number) {}

  static place(id: string, total: number): Order {
    const order = new Order(id, total);
    order.pending.push(new OrderPlaced(id, total));
    return order;
  }

  drainEvents(): DomainEvent[] {
    const events = this.pending;
    this.pending = [];
    return events;
  }
}

type Handler = (event: DomainEvent) => void;

class Dispatcher {
  private handlers = new Map<string, Handler[]>();

  register(kind: string, handler: Handler): void {
    const list = this.handlers.get(kind) ?? [];
    list.push(handler);
    this.handlers.set(kind, list);
  }

  dispatch(events: DomainEvent[]): void {
    for (const event of events) {
      for (const handler of this.handlers.get(event.kind) ?? []) {
        handler(event);
      }
    }
  }
}

const dispatcher = new Dispatcher();
const reserved: string[] = [];
const notified: string[] = [];

dispatcher.register("OrderPlaced", (event) => {
  const placed = event as OrderPlaced;
  reserved.push(placed.orderId);
});
dispatcher.register("OrderPlaced", (event) => {
  const placed = event as OrderPlaced;
  notified.push(`loyalty:${placed.orderId}`);
});

const order = Order.place("order-1", 129.5);
dispatcher.dispatch(order.drainEvents());

console.log(reserved);
console.log(notified);
```

### Python

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable


@dataclass(frozen=True)
class OrderPlaced:
    order_id: str
    total: float
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class Order:
    def __init__(self, order_id: str, total: float) -> None:
        self.id = order_id
        self.total = total
        self._pending: list[object] = []

    @classmethod
    def place(cls, order_id: str, total: float) -> "Order":
        order = cls(order_id, total)
        order._pending.append(OrderPlaced(order_id, total))
        return order

    def drain_events(self) -> list[object]:
        events, self._pending = self._pending, []
        return events


class Dispatcher:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[object], None]]] = {}

    def register(self, event_type: type, handler: Callable[[object], None]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def dispatch(self, events: list[object]) -> None:
        for event in events:
            for handler in self._handlers.get(type(event), []):
                handler(event)


if __name__ == "__main__":
    dispatcher = Dispatcher()
    reserved: list[str] = []
    notified: list[str] = []

    dispatcher.register(OrderPlaced, lambda e: reserved.append(e.order_id))
    dispatcher.register(OrderPlaced, lambda e: notified.append(f"loyalty:{e.order_id}"))

    order = Order.place("order-1", 129.5)
    dispatcher.dispatch(order.drain_events())

    print(reserved)
    print(notified)
```

### Go

```go
package main

import (
	"fmt"
	"reflect"
)

type OrderPlaced struct {
	OrderID string
	Total   float64
}

type Order struct {
	ID      string
	Total   float64
	pending []interface{}
}

func PlaceOrder(id string, total float64) *Order {
	order := &Order{ID: id, Total: total}
	order.pending = append(order.pending, OrderPlaced{OrderID: id, Total: total})
	return order
}

func (o *Order) DrainEvents() []interface{} {
	events := o.pending
	o.pending = nil
	return events
}

type Handler func(event interface{})

type Dispatcher struct {
	handlers map[reflect.Type][]Handler
}

func NewDispatcher() *Dispatcher {
	return &Dispatcher{handlers: make(map[reflect.Type][]Handler)}
}

func (d *Dispatcher) Register(sample interface{}, handler Handler) {
	t := reflect.TypeOf(sample)
	d.handlers[t] = append(d.handlers[t], handler)
}

func (d *Dispatcher) Dispatch(events []interface{}) {
	for _, event := range events {
		t := reflect.TypeOf(event)
		for _, handler := range d.handlers[t] {
			handler(event)
		}
	}
}

func main() {
	dispatcher := NewDispatcher()
	var reserved []string
	var notified []string

	dispatcher.Register(OrderPlaced{}, func(e interface{}) {
		placed := e.(OrderPlaced)
		reserved = append(reserved, placed.OrderID)
	})
	dispatcher.Register(OrderPlaced{}, func(e interface{}) {
		placed := e.(OrderPlaced)
		notified = append(notified, fmt.Sprintf("loyalty:%s", placed.OrderID))
	})

	order := PlaceOrder("order-1", 129.5)
	dispatcher.Dispatch(order.DrainEvents())

	fmt.Println(reserved)
	fmt.Println(notified)
}
```
