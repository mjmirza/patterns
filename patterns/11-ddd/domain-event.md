---
name: Domain Event
slug: domain-event
family: 11-ddd
category: Tactical
aliases: [Business Event, Domain Notification]
first_described: "Evans 2003, formalized by Fowler 2005 and Vernon 2013"
maturity: canonical
related: [entity, aggregate, bounded-context, ubiquitous-language, published-language, open-host-service]
incompatible_with: []
verified: 2026-08-02
---

# Domain Event

## 1. Name, aliases, and lineage

The canonical name is Domain Event. Eric Evans, *Domain-Driven Design. Tackling
Complexity in the Heart of Software*, Addison-Wesley, 2003, does not name Domain
Event as one of the tactical building blocks. The 2003 catalog covers Entity,
Value Object, Service, Aggregate, Factory, and Repository. Domain Event was
added to the DDD vocabulary afterward, a fact Vaughn Vernon states directly.
"Domain Events were not formally introduced by Eric Evans as part of DDD until
after his book was published" (Vaughn Vernon, *Implementing Domain-Driven
Design*, Addison-Wesley, 2013, ISBN 9780321834577, Chapter 8, "Domain Events").

The name and the concrete definition trace to Martin Fowler's essay, published
12 December 2005 as part of his Enterprise Application Architecture writing.
Fowler describes a Domain Event as capturing "the memory of something
interesting which affects the domain," and treats it as a way to funnel varied
system inputs, a user click, a message off a queue, a database trigger, into
one uniform representation that the rest of the system can process the same
way (Martin Fowler, "Domain Event," martinfowler.com,
<https://martinfowler.com/eaaDev/DomainEvent.html>, verified 2026-08-02).

Eric Evans himself later folded the pattern into the DDD canon. The community
consensus captured by Vernon and by Alberto Brandolini's EventStorming
practice treats Domain Event as a fourth tactical building block alongside
Entity, Value Object, and Aggregate. Vernon places it explicitly there. "The
book places Domain Events alongside Entities and Value Objects as the building
blocks of a model" (Vernon, *Implementing Domain-Driven Design*, Chapter 8).

Two aliases circulate. Business Event is used interchangeably in enterprise
integration writing to stress that the event corresponds to something a
business stakeholder would recognize and name, not a technical occurrence like
a row update. Domain Notification appears in older .NET DDD sample code
(notably the Microsoft eShopOnContainers reference architecture) as a synonym
for the in-process, pre-publication form of the event, the object an aggregate
raises before an infrastructure layer turns it into a message. This entry uses
Domain Event throughout and treats Business Event and Domain Notification as
the same concept viewed from, respectively, the stakeholder side and the
in-process side.

Domain Event must not be confused with three neighboring but distinct ideas
that share vocabulary. Event Sourcing is a persistence strategy that uses a
stream of domain events as the system of record for an aggregate's state, and
it depends on Domain Event existing but is a separate pattern with its own
concerns (replay, snapshotting, versioning). Event-Driven Architecture is an
integration style built from events crossing service boundaries, and a Domain
Event only becomes an integration event once it is translated across a
bounded context, a distinction covered in dimension 4 below. A CDC record,
change data capture, such as those Debezium produces from a database
write-ahead log, is a technical event about a row change, not a Domain Event,
because it carries no ubiquitous-language name and no business meaning of its
own. It must be interpreted or transformed before it can stand in as one.

## 2. Problem and context

A codebase modeling a real domain accumulates behavior that has to happen
"because something else happened," and that dependency keeps landing in the
wrong place. An `Order.markPaid()` method also has to notify the shipping
subsystem, decrement inventory, and update a customer loyalty balance. The
straightforward move is to call all three from inside `markPaid`, directly, by
injecting the shipping service, the inventory service, and the loyalty service
into the Order aggregate or into the application service that orchestrates the
transaction.

This works for a while and then breaks down in a specific, recognizable way.
The aggregate, or the transaction script sitting above it, accumulates
dependencies on every subsystem that might ever need to react to an order
being paid. Adding a fourth reaction, say a fraud-check trigger, means editing
code that already shipped and is already tested, and it means the Order
aggregate, whose job is to enforce the invariants of an order, now also knows
about shipping, inventory, and loyalty, none of which are its concern. Worse,
these reactions frequently belong to a genuinely different bounded context
with its own transactional boundary, so calling them synchronously inside the
same database transaction that pays the order either forces a distributed
transaction, which is expensive and fragile, or silently couples the payment
outcome to the availability of three unrelated services.

The context in which Domain Event is the right answer has three properties
present together. First, something has happened inside one part of the model
that is genuinely significant to the ubiquitous language, not merely a state
change a database ORM would emit on any field write. "The order was paid" is
domain-significant. "The `status` column changed from 3 to 4" is not, even
though they are the same fact. Second, the reaction to that fact belongs to a
different part of the model, often a different aggregate, sometimes a
different bounded context entirely, and that reaction does not need to
complete inside the same transaction as the fact itself. Third, more than one
interested party may exist now, or may be added later, and the aggregate that
raised the fact should not need to know their names or their count.

Domain Event names the fact, in past tense, in the ubiquitous language, and
publishes it as a value, so the code that generates the fact is decoupled from
the code that reacts to it. The aggregate says `OrderPaid` happened. It does
not say who cares.

## 3. Forces

**Coupling versus locality.** Calling three services directly from inside
`markPaid` keeps the whole causal chain visible in one method, which is easy
to read once but grows brittle as reactions accumulate. Domain Event trades
that locality for decoupling. Nobody reading `markPaid` can tell, from the
method alone, everything that eventually happens because of it, and that
opacity is a real cost paid to get independent evolution of the reactions.

**Consistency versus availability.** A synchronous, same-transaction call
guarantees the reaction either commits with the cause or the whole transaction
rolls back, strong consistency at the price of coupling the availability of
the cause to the availability of every reaction. Publishing a Domain Event
after the transaction commits, and letting handlers run asynchronously,
buys availability and independent failure but introduces eventual consistency,
a window in which the fact is true but not every consequence has happened yet.
Vernon's Chapter 8 spends real space on exactly this trade, distinguishing "in
the same process, same transaction," "in the same process, different
transaction," and "different process entirely," each with a different
consistency guarantee (Vernon, *Implementing Domain-Driven Design*, Chapter 8).

**Auditability versus payload minimalism.** An event that carries a full
snapshot of the aggregate is convenient for a naive subscriber and
self-describing years later, but it grows the payload, risks leaking fields a
subscriber should not see, and tempts subscribers into treating the event as a
free read-replica rather than reacting to the fact. An event that carries only
identifiers and the changed values is smaller and more private, but forces
every subscriber to call back for context it needs, adding coupling of a
different kind, a runtime dependency on the publisher's query API. Fowler's
distinction between a fact's immutable "source data" and its separately
mutable "processing data" bears directly on this. The source data is what the
event should carry, kept small and permanent, and processing data belongs to
the handler, not the event (Fowler, "Domain Event," verified 2026-08-02).

**Cognitive load of an implicit call graph.** A synchronous call graph can be
stepped through in a debugger. A published event fans out to an unknown, and
possibly unbounded, set of handlers discovered only by grepping for
subscriptions or reading a message broker's routing table. This is the primary
sacrifice of the pattern, and it is discussed at length in dimension 11.

**Operability and cost.** In-process publication (an internal mediator, an
observer list, a synchronous dispatcher inside one application) costs nothing
beyond the object allocation and is trivial to operate. Out-of-process
publication through a broker (Kafka, EventStoreDB, an outbox with a message
relay) buys durability, replay, and cross-service delivery, and costs a piece
of infrastructure that must be run, monitored, and paid for, plus a
serialization contract that now has to be versioned across services that
deploy independently.

The pattern deliberately favors decoupling, independent evolution of
reactions, and eventual consistency, and it deliberately sacrifices a linear,
debuggable call graph and strict transactional consistency between cause and
every effect. A pattern is described wrongly if it claims to sacrifice
nothing. Domain Event sacrifices traceability for decoupling, and any
adoption decision that ignores that trade will regret it in incident response.

## 4. Applicability and non-applicability

Reach for Domain Event when at least one of these holds.

- A fact inside one aggregate must trigger behavior in a different aggregate,
  and that behavior does not have to complete inside the same transaction as
  the fact. This is the paradigm case. Paying an order should not require the
  Order aggregate to know how shipping works.
- A fact needs to cross a bounded context boundary, so a different team's
  service can react to it without that team polling the source system or
  reading its database directly. Once the event crosses the boundary it
  becomes what dimension 13 calls an integration event, and Published
  Language and Open Host Service govern the contract it must honor.
- The system needs a durable, ordered record of what happened, independent of
  the current-state model, for audit, for replay, for building read models, or
  for reconstructing an aggregate's history (the specific case Event Sourcing
  builds on).
- Multiple, potentially unknown-in-advance subscribers need to react to the
  same fact. Notification lists, analytics pipelines, and cache invalidation
  are common examples where the publisher genuinely should not need to know
  who is listening.
- The team practices EventStorming or a similar collaborative modeling
  technique and has already identified named domain events as the vocabulary
  the business uses to describe what happens. In that case the events already
  exist conceptually and the pattern gives them a code-level home.

Do NOT reach for Domain Event, or reach for it only very carefully, when any
of these hold, because each is a documented failure mode in production
systems, not a hypothetical caution.

- The reaction must happen inside the same transaction as the cause, and
  failure of the reaction must roll back the cause. A double-entry ledger
  posting where the debit and credit legs must be atomic is not helped by
  publishing an event and hoping a handler runs before commit. It needs a
  direct call inside the transaction, full stop. Publishing an event and
  treating "eventually the balance will be right" as acceptable is a
  correctness bug wearing an architecture pattern's clothes.
- There is exactly one caller and exactly one reaction, both inside the same
  module, and no plausible future subscriber. A direct method call is
  simpler, is traceable in a debugger, and costs nothing to understand six
  months later. Introducing an event bus for a single, permanent
  caller-to-callee relationship is the over-engineering critique the pattern
  most often earns, and it is a fair critique when the relationship really is
  one-to-one and will stay that way.
- The "event" is really a command in disguise, an instruction telling a
  specific downstream system exactly what to do, phrased in the imperative
  ("ChargeCustomer") rather than the past tense ("CustomerCharged"). A command
  has one intended recipient and an expectation of a specific outcome.
  Naming it as an event and broadcasting it to potential many subscribers
  hides that it is really a targeted request, and a subscriber that ignores
  it has silently broken the intended workflow.
- The team cannot yet answer, for a candidate event, what changes in the
  ubiquitous language when this happens, and is only naming database row
  changes with a past-tense verb glued on. `UserRowUpdated` is not a domain
  event. It is a database trigger with a costume.
- The team has no operational capacity to run and monitor whatever
  publication mechanism the event needs (a broker, an outbox relay, a
  dead-letter queue), because an event silently dropped or silently stuck in
  a retry loop is worse than a direct call that fails loudly at the call
  site. Dimension 11 covers the specific failure modes this produces.

## 5. Structure

- **Domain Event.** An immutable value object, named in the past tense in the
  ubiquitous language ("OrderPaid," never "PayOrder" or "OrderPayment"),
  carrying the identifiers and the changed data needed to describe what
  happened, plus an occurred-at timestamp and, where the domain requires it, a
  version or sequence number. It has no behavior beyond simple accessors. It
  is never mutated after construction.
- **Event Source (Aggregate Root or Domain Service).** The part of the model
  that detects the fact and constructs the event. In the common tactical
  pattern the aggregate root itself both enforces the invariant that makes
  the fact true (an order cannot be marked paid twice) and produces the event
  describing that it became true, in the same method.
- **Event Collector / Registrar.** A mechanism, often on a base aggregate
  class, that accumulates events raised during a unit of work without
  publishing them immediately. This exists because publishing before the
  triggering transaction commits risks a subscriber acting on a fact that
  then gets rolled back.
- **Event Publisher / Dispatcher.** The infrastructure component, usually
  invoked after the unit of work commits successfully, that hands each
  collected event to every interested handler. It may be a simple in-process
  mediator, or it may serialize the event onto a message broker for delivery
  to other processes.
- **Event Handler / Subscriber.** A piece of behavior, registered against one
  or more event types, that performs the reaction. A handler does not return
  a value the publisher depends on. Its contract is "do the side effect, or
  fail and be retried," never "compute an answer the caller needs right now."
- **Event Store (optional).** When the system uses Event Sourcing, a durable,
  append-only log keyed by aggregate identity that is the system of record.
  Current state is derived by replaying the stream. This participant exists
  only in the event-sourced variant, not in the baseline pattern, and is
  called out explicitly in dimension 8.
- **Outbox (optional, cross-process variant).** A table in the same database
  and the same transaction as the aggregate's own write, holding events not
  yet relayed to the broker, closing the gap between "the fact is committed"
  and "the fact is guaranteed to reach the broker." Covered in dimension 8
  and dimension 11.

## 6. ASCII structure diagram

```
+-------------------------+        raises        +-------------------+
|   Aggregate Root         |---------------------->|   Domain Event     |
|   (Order)                 |                       |   (OrderPaid)       |
|   markPaid()               |                       |   orderId          |
|   enforces invariants      |                       |   amount           |
+------------+--------------+                       |   occurredAt        |
             |                                        +----------+---------+
             | collects into                                    |
             v                                                    | published to
+-------------------------+                                       v
|   Event Registrar         |     after commit      +--------------------+
|   (pendingEvents list)    |----------------------->|  Event Publisher    |
+-------------------------+                          |  / Dispatcher        |
                                                       +----------+-----------+
                                                                  |
                                        fan out to N handlers      |
                              +-----------------------+-----------+-----------+
                              v                        v                       v
                    +-------------------+   +-------------------+   +-------------------+
                    | ShippingHandler     |   | InventoryHandler    |   | LoyaltyHandler       |
                    | (different agg.)    |   | (different agg.)    |   | (different context)  |
                    +-------------------+   +-------------------+   +-------------------+
```

## 7. Dynamics

The in-process, transactional-boundary-respecting sequence is the shape that
avoids the most common defects, and it runs in five steps.

```
1. Application service loads the Order aggregate from the repository.
2. Application service calls order.markPaid(paymentRef).
   - Order validates the invariant (not already paid, amount matches).
   - Order mutates its own state (status -> Paid).
   - Order constructs OrderPaid(orderId, amount, occurredAt=now) and
     appends it to its internal pendingEvents list. It does NOT publish yet.
3. Application service persists the Order (repository.save(order)) inside
   the same database transaction that will also, if using an outbox,
   insert the pendingEvents into the outbox table.
4. Transaction commits. Only now, after commit succeeds, does the
   application service (or a transaction-commit hook) hand the collected
   events to the publisher.
5. Publisher dispatches OrderPaid to every registered handler.
   - In-process handlers run synchronously, in an order that must be
     assumed unspecified unless the publisher documents otherwise.
   - Out-of-process handlers receive the event via the broker, whenever
     their own consumer next polls or is pushed to, with no guarantee of
     "soon."
```

The critical ordering fact, responsible for a large share of real production
bugs discussed in dimension 11, sits at step 4. Publication happens after
commit, never before and never inside the same transaction as an unresolved
write. Publishing before commit means a handler can act on a fact that a
subsequent rollback undoes, a defect Vernon calls out directly as a reason to
prefer collecting events and publishing them from application-service or
infrastructure code, not from deep inside the aggregate's own method, which
has no reliable way to know whether its enclosing transaction will succeed
(Vernon, *Implementing Domain-Driven Design*, Chapter 8).

For the cross-process variant using an outbox, step 3 and step 5 change
shape. The events are written into an outbox table in the SAME database
transaction as the aggregate's own row changes, guaranteeing they are never
lost if the process crashes right after commit, and a separate relay process
polls that table and forwards each row to the broker, deleting or marking it
sent only after a successful publish. This is the mechanism behind Debezium's
outbox event router and the general Transactional Outbox pattern documented
in the microservices.io catalog by Chris Richardson
(<https://microservices.io/patterns/data/transactional-outbox.html>, verified
2026-08-02).

## 8. Implementation variants

**In-process synchronous dispatch.** The simplest variant. An aggregate base
class exposes `registerEvent`/`pullEvents`, an application service calls
`publish` on each pulled event after the unit of work commits, and a
dispatcher (an observer list, a mediator, or a language-native event bus)
calls every subscriber's handler method directly, synchronously, in the
calling thread. Failures in a handler either propagate to the caller
(dangerous, because a broken loyalty handler can now break order payment)
or are caught and logged (safer, but silent unless monitored). This is what
Spring Data Commons implements with `AbstractAggregateRoot`, `@DomainEvents`,
and `@AfterDomainEventPublication`. `registerEvent` collects, the
repository's `save` call triggers publication via Spring's
`ApplicationEventPublisher` after the entity is persisted, and
`@AfterDomainEventPublication` clears the list (Spring Data Commons
reference documentation, "Publishing Events from Aggregate Roots,"
<https://docs.spring.io/spring-data/commons/reference/repositories/core-domain-events.html>,
verified 2026-08-02).

**In-process async dispatch.** The same collection mechanism, but the
dispatcher hands each event to a thread pool, an actor mailbox, or a
language-native async queue instead of calling handlers synchronously. This
decouples handler latency from the request path (a slow loyalty-points
recalculation no longer slows the checkout response) at the cost of losing
the guarantee that "handled" means "handled before this function returns,"
which callers relying on read-after-write consistency will notice.

**Outbox plus broker relay (cross-process, at-least-once).** Covered above in
dimension 7. This is the standard shape for events that must leave the
process boundary reliably. Debezium's outbox event router reads a
conventionally-shaped outbox table via change data capture and republishes
each row to Kafka, which is why teams frequently pair Domain Event with
Debezium even though CDC itself, as noted in dimension 1, is not the same
concept (Debezium documentation, "Outbox Event Router,"
<https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html>,
verified 2026-08-02).

**Event-sourced variant.** Instead of persisting current state and
separately raising events about changes to it, the aggregate's sequence of
domain events IS the system of record. Current state is a fold (a left
reduce) over the event stream, recomputed on load or cached via periodic
snapshots. Every command produces one or more events, those events are
appended to a stream keyed by aggregate identity, and the append is the only
write. This variant needs a purpose-built store. EventStoreDB is the
best-known open-source example, built specifically around appending and
reading ordered event streams per aggregate
(<https://www.eventstore.com/eventstoredb>, verified 2026-08-02). Axon
Framework implements the same idea on the JVM. `AggregateLifecycle.apply()`
raises a domain event, an `@EventSourcingHandler`-annotated method on the
aggregate mutates in-memory state from that event, and the framework persists
the event, not the state, to an event store, replaying the stream to
reconstruct the aggregate on every load unless a snapshot short-circuits it
(AxonIQ, `EventSourcingHandler` API documentation and framework guide,
<https://apidocs.axoniq.io/4.4/org/axonframework/eventsourcing/EventSourcingHandler.html>,
verified 2026-08-02).

**Version-tolerant envelope.** Regardless of transport, production systems
wrap the event's business payload in an envelope carrying an event type name,
a schema version, a correlation identifier tying it back to the originating
command or request, and a causation identifier tying it to whatever event or
command caused this one. This envelope is what lets consumers upgrade
independently of producers, a concern covered further in dimension 11 and
dimension 17.

**Language-idiomatic shapes.** In languages with closures, a lightweight
variant replaces the formal Observer-style subscriber interface with a plain
function or lambda registered against an event type, removing the
boilerplate of a named handler class without changing the underlying
publish/subscribe shape. This is the common shape in TypeScript, Go, and
Python code shown below in the Code section; a formal `interface
OrderEventHandler` is only worth the ceremony in a language, or a team
convention, where discoverability of "who handles this" matters more than
terseness.

## 9. Known production uses

- **Spring Data Commons, `AbstractAggregateRoot`.** Ships in the core Spring
  Data library used across Spring Boot applications on the JVM. An aggregate
  root extends `AbstractAggregateRoot<T>`, calls `registerEvent(Object)` from
  inside a domain method, and Spring's repository `save`, `saveAll`,
  `delete`, and `deleteAll` operations trigger publication of the collected
  events via the framework's `ApplicationEventPublisher` after the
  persistence operation completes (Spring Data Commons reference,
  "Publishing Events from Aggregate Roots,"
  <https://docs.spring.io/spring-data/commons/reference/repositories/core-domain-events.html>,
  verified 2026-08-02).
- **Axon Framework.** A JVM framework purpose-built around CQRS and event
  sourcing that treats the domain event as the primary unit of both state
  change and integration. Aggregates call `AggregateLifecycle.apply()` to
  raise an event, `@EventSourcingHandler` methods fold events into aggregate
  state, and the same events can be republished to other bounded contexts
  through Axon's event bus abstraction (AxonIQ, Axon Framework
  documentation and API reference,
  <https://apidocs.axoniq.io/4.4/org/axonframework/eventsourcing/EventSourcingHandler.html>,
  verified 2026-08-02).
- **Stripe, the Events API.** Every state change to a Stripe object (a
  payment succeeding, a subscription being created, a dispute being opened)
  produces an immutable Event object with a fixed envelope (`id`, `type`,
  `created`, `api_version`, and a `data` payload holding the resource that
  changed), delivered to subscribers via webhook or via Amazon EventBridge.
  This is a textbook Domain Event shape used at very large production scale
  as the integration contract between Stripe and every merchant's backend
  (Stripe API Reference, "Events,"
  <https://docs.stripe.com/api/events>, verified 2026-08-02; Stripe
  Documentation, "Receive Stripe events in your webhook endpoint,"
  <https://docs.stripe.com/webhooks>, verified 2026-08-02).
- **Debezium's outbox event router, used across CDC-based microservice
  deployments.** Debezium implements the Transactional Outbox pattern
  directly. It reads a conventionally-shaped outbox table via change data
  capture from the database's write-ahead log and republishes each row as a
  correctly-typed event onto Kafka, which is the standard mechanism teams use
  to publish domain events reliably out of a service whose primary datastore
  is a relational database (Debezium documentation, "Outbox Event Router,"
  <https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html>,
  verified 2026-08-02).

## 10. Consequences

Positive.

- Decouples the code that detects a fact from the code that reacts to it.
  New reactions are added by registering a new handler, never by editing the
  aggregate that raised the event.
- Produces a natural audit trail in the ubiquitous language, because each
  event is a named, timestamped record of something the business recognizes,
  independent of the current-state representation.
- Enables read models and analytics to be built by subscribing to the event
  stream instead of querying the transactional database directly, isolating
  reporting load from operational load.
- Allows cross-bounded-context integration without direct, synchronous
  coupling between services, letting each side deploy and scale
  independently once the event contract is agreed.
- In the event-sourced variant, gives a complete, replayable history of an
  aggregate for free, which supports temporal queries ("what was this
  order's state last Tuesday") that a current-state-only model cannot answer
  without extra machinery.

Negative.

- Introduces an implicit call graph. Understanding everything that happens
  when an order is paid now requires knowing every current subscriber to
  `OrderPaid`, which is not visible from reading `markPaid` alone and drifts
  out of sync with documentation over time.
- Trades strict consistency for eventual consistency between the cause and
  its consequences whenever handlers run outside the triggering transaction,
  a trade that is wrong for invariants that must be atomic (see dimension 4).
- Adds a real operational surface. a publisher that must not silently drop
  events, handlers that must be idempotent against redelivery, and, in the
  cross-process case, a broker and an outbox relay that must themselves be
  monitored, upgraded, and paid for.
- Event schemas become a long-lived public contract the moment a second
  service subscribes. Changing a field's meaning or removing a field becomes
  a breaking change across a team boundary, with all the versioning
  discipline that implies (dimension 17 elaborates).
- In the event-sourced variant specifically, replay cost grows with stream
  length until snapshotting is introduced, and schema evolution of the
  events themselves becomes harder because the store cannot simply migrate
  in place. Old event versions must remain readable forever, or an explicit
  upcasting step must be maintained.

## 11. Failure modes and misuse

- **Symptom.** A downstream service processes the same order-paid effect
  twice, double-shipping an order or double-crediting loyalty points.
  **Cause.** The publication mechanism guarantees at-least-once delivery
  (the honest guarantee any durable broker or outbox relay can make without
  a distributed transaction), and the handler was written assuming
  exactly-once. **Fix.** Make every handler idempotent, typically by keying
  a "have I already processed event ID X" check against a durable store
  before applying the side effect, or by designing the side effect itself to
  be naturally idempotent (an upsert keyed by the event's identifier rather
  than an increment).

- **Symptom.** A fact appears to have happened (the aggregate committed) but
  no subscriber ever reacted, and there is no error anywhere to explain why.
  **Cause.** The event was published before the enclosing transaction
  committed and the transaction later rolled back, so no fact ever truly
  existed. Or the publisher failed to relay the event to the broker after a
  successful local commit, with no outbox pattern to guarantee retry.
  **Fix.** Always collect events during the unit of work and publish only
  after commit succeeds (dimension 7), and for cross-process delivery always
  write to the outbox in the same transaction as the state change, never
  publish-then-write or write-then-publish as two separate steps.

- **Symptom.** Adding a fourth subscriber to `OrderPaid` breaks the checkout
  flow, even though the new handler only reads data and never touches the
  order. **Cause.** The dispatcher calls handlers synchronously in the same
  thread and propagates a handler's exception up to the caller, so a bug or
  a slow dependency in the new handler now fails the original transaction it
  had nothing to do with. **Fix.** Isolate handler failures from the
  publishing call site, catching and logging per-handler exceptions rather
  than letting one handler's failure abort the publish loop, and consider
  moving non-critical handlers to asynchronous dispatch so their latency and
  failure modes cannot touch the request path at all.

- **Symptom.** Two teams' services disagree about what an event means. One
  reads a field as "the amount charged in cents" and the other reads the
  same field name as "the amount charged in the major currency unit," and
  the discrepancy is discovered in production reconciliation, not in review.
  **Cause.** The event was treated as an internal implementation detail and
  never given an explicit, versioned, documented schema once a second team
  started consuming it, which silently converted a Domain Event into an
  integration event without the governance an integration event needs.
  **Fix.** The moment an event crosses a bounded context, treat its schema
  as a Published Language contract (dimension 13). Version it explicitly,
  document field semantics and units, and change it only in
  backward-compatible ways or through an announced, dual-write migration.

- **Symptom.** The event log for one aggregate grows into millions of rows
  and loading that aggregate now takes seconds. **Cause.** Event-sourced
  systems replay the full stream on every load with no snapshotting, a
  workable choice at low event counts that degrades as the aggregate's
  lifetime and event rate grow. **Fix.** Introduce periodic snapshots of
  aggregate state at a known event sequence number, load the most recent
  snapshot plus only the events after it, and treat the snapshot purely as a
  performance optimization the aggregate's logic never depends on for
  correctness.

- **Symptom.** A named event ("InventoryReservationRequested") is published,
  and the system silently breaks whenever the one intended handler is
  temporarily unavailable, because nobody realizes it was never really
  meant to have more than one subscriber. **Cause.** A command was disguised
  as an event, as warned against in dimension 4. The publisher expected an
  outcome ("inventory gets reserved") that only makes sense if exactly the
  right handler runs, which is a command's contract, not an event's.
  **Fix.** Rename and re-model it as a command sent directly to the specific
  service responsible, with its own delivery and failure-handling guarantees
  appropriate to a command, and reserve the event name and shape for the
  fact that inventory reservation later succeeded or failed.

## 12. Trade-off matrix

| Force | Domain Event (published, decoupled) | Direct synchronous call | Full Event Sourcing of the aggregate |
|---|---|---|---|
| Coupling between cause and reaction | Low. Publisher does not know subscribers. | High. Caller names every callee explicitly. | Low for external reactions. State itself is fully coupled to event history. |
| Consistency guarantee | Eventual, unless handler runs in the same transaction. | Strong, atomic with the cause. | Strong for the aggregate's own state (it is derived from the events). Eventual for projections built from the stream. |
| Debuggability of "what happens next" | Low. Requires knowing the current subscriber list. | High. A stack trace shows the whole chain. | Medium. The stream itself is a debuggable audit log, but derived projections add their own indirection. |
| Operational cost | Medium to high with a broker and outbox. Low for pure in-process dispatch. | Near zero. No extra infrastructure. | High. Needs a dedicated event store, snapshotting, and stream-versioning discipline. |
| Schema evolution burden | Real, once any subscriber exists outside the publishing module. | None. Call signatures are checked by the compiler and can change freely inside one codebase. | Highest. Old event shapes must remain readable forever, or upcasting must be maintained indefinitely. |
| Fit for cross-bounded-context integration | Strong, the pattern's primary purpose once paired with Published Language. | Poor. Forces synchronous coupling across a team or service boundary. | Strong for the source of truth, but external consumers still need an explicit published contract, not the raw internal event shape. |

The direct-call column is not a strawman. It is the correct choice whenever
dimension 4's non-applicability list applies, and Domain Event should never be
adopted reflexively where a direct call is simpler and sufficient.

## 13. Related and incompatible patterns

- **Aggregate and Entity.** Domain Event is the mechanism by which an
  Aggregate announces that one of its invariant-preserving state transitions
  has completed. The Aggregate stays the authority on whether the transition
  is valid. The event is a record that it happened, produced only after the
  Aggregate itself has already decided the transition is legal.
- **Bounded Context and Published Language.** A Domain Event stays a purely
  internal implementation detail until a second Bounded Context subscribes to
  it, at which point it becomes an integration event and must be governed as
  a Published Language, with the versioning and backward-compatibility
  discipline that implies. Conflating the internal event's shape with the
  external contract is the root cause of the schema-disagreement failure
  mode in dimension 11.
- **Open Host Service.** When many external consumers need the same events,
  an Open Host Service is frequently the mechanism that translates internal
  domain events into the stable, documented Published Language those
  consumers rely on, rather than exposing internal event shapes directly.
- **Anticorruption Layer.** On the consuming side, an Anticorruption Layer
  translates an inbound event from another Bounded Context's vocabulary into
  the consumer's own model, so the consumer's domain language is never
  polluted by the publisher's terms.
- **Event Sourcing.** Builds directly on Domain Event by making the event
  stream itself the system of record, rather than a side effect of a
  separately persisted current state. Every event-sourced system uses
  Domain Event. Not every system that uses Domain Event is event-sourced.
- **CQRS, Command Query Responsibility Segregation.** Frequently paired with
  Domain Event because the write side's events are the natural feed for
  building the read side's query-optimized projections, but the two patterns
  are independent. CQRS can be implemented with synchronous projection
  updates and no published events at all.
- **Observer.** The GoF Observer pattern is the classic in-process
  implementation mechanism underneath many in-process Domain Event
  dispatchers. Domain Event adds the domain-modeling discipline (past-tense
  naming, ubiquitous-language meaning, immutability, unit-of-work-aware
  publication timing) that plain Observer does not require.
- **Incompatibilities.** Domain Event does not sit well inside a design that
  insists on strict, synchronous, single-transaction consistency for every
  cross-aggregate effect. Forcing it into that context either produces the
  rolled-back-fact bug in dimension 11 or degenerates into a synchronous call
  wearing an event's name, which is the disguised-command misuse also
  covered there.

## 14. Refactoring path in and out

Introducing Domain Event into code that currently calls collaborators
directly proceeds in five steps, matching the shape Martin Fowler's broader
refactoring catalog uses for extracting an indirection (Martin Fowler,
*Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, the "Move Function" and "Extract Function" family of
refactorings apply to isolating the reaction, though Fowler's book does not
name Domain Event itself).

1. Identify the direct calls inside the aggregate method that represent
   reactions to a fact rather than enforcement of the aggregate's own
   invariant. In `Order.markPaid`, the invariant check ("not already paid")
   stays. The calls to `shippingService.notify`, `inventoryService.decrement`,
   and `loyaltyService.credit` are candidates to extract.
2. Define the event type as an immutable value carrying exactly what a
   handler needs, named in the past tense in the ubiquitous language, and
   have `markPaid` construct and collect it instead of calling the three
   services.
3. Move each extracted call into its own handler, registered against the new
   event type, so `shippingService.notify` now lives inside a
   `ShippingHandler` subscribed to `OrderPaid` rather than being invoked
   inline.
4. Insert publication at the correct point in the unit of work, after commit
   succeeds, per dimension 7, and remove the direct service dependencies from
   the aggregate or the application service that previously wired them
   together.
5. Verify with the technique from dimension 15. Write a test that asserts the
   aggregate raised the expected event with the expected payload, independent
   of whether any handler runs, and a separate test per handler that feeds it
   a hand-built event and asserts the reaction, without spinning up the
   aggregate at all.

Removing Domain Event, when a relationship that once looked like it might
need many subscribers turns out to have exactly one, permanent caller,
reverses the same steps. Fold the handler's logic back into a direct call,
delete the event type and its registration, and delete the collection and
publication machinery if nothing else in the codebase still uses it. The
signal that removal is overdue is dimension 4's non-applicability case
becoming true after the fact, not a stylistic preference. If grepping the
codebase shows one publisher and one permanent subscriber, and no plausible
second subscriber has appeared in the pattern's lifetime, the indirection is
pure cost.

## 15. Testing and verification

Domain Event splits a single behavior into two independently testable parts,
and that split is the pattern's biggest testing benefit. The fact-detection
logic and the reaction logic can be verified without either one running the
other.

Testing the event source is a pure, synchronous unit test. Construct the
aggregate in a known starting state, call the method under test, and assert
two things separately. First, that the aggregate's own state changed
correctly (the invariant side). Second, that the expected event, with the
expected field values, was collected in its pending-events list. No
publisher, no handler, and no infrastructure need to exist for this test to
run, which is exactly the isolation the pattern is meant to buy.

Testing a handler is a second pure, synchronous unit test, run in complete
isolation from the aggregate. Construct an event value directly, by hand,
with the fields the test needs, call the handler with it, and assert the
side effect (a call was made to a mocked collaborator with the right
arguments, a row was inserted with the right values). Because the handler's
contract is "given this event, do this," and never "go fetch more context
from wherever the event came from," a well-designed handler needs no more
than the event itself and its own collaborators to test.

Testing publication and delivery is a narrower, separate concern from testing
either side's logic, and it should stay narrow. Assert that raised events are
actually handed to the dispatcher after a successful unit of work and are NOT
handed to it after a failed one (this is the specific regression the
rolled-back-fact bug from dimension 11 represents, and it deserves its own
test using a fake repository or an in-memory transaction boundary rather than
a real database). For the outbox variant, an integration test that commits a
change, inspects the outbox table directly, and confirms the row is present
and correctly shaped is more valuable than mocking the relay process, because
the exact contents of the outbox row are the actual contract with the relay.

End-to-end tests that exercise the full publish-to-handler path across a real
broker are appropriate at low volume, as a small number of "the wiring
actually works" smoke tests, not as the primary way individual handler logic
gets verified. Broker-based tests are slow, flaky under CI load, and poor at
localizing a failure to the specific line of logic that broke.

## 16. Observability signals

A healthy Domain Event pipeline shows a small, stable set of signals. The
count of events published per event type per unit time should track the rate
of the business activity it represents (order payments should track checkout
volume, not diverge from it), and a sudden drop to zero on one event type
while the rest of the system looks normal is the single most useful early
warning that a publisher, a serializer, or a specific handler registration
silently broke. The lag between an event's occurred-at timestamp and the
timestamp at which each subscriber actually processed it (consumer lag, in
broker terms) should stay bounded and should be alerted on when it grows,
because unbounded growth means a handler is falling behind its input rate,
not merely running slower.

For the outbox variant specifically, the size of the unrelayed-rows queue in
the outbox table is a direct, cheap-to-query health signal. It should hover
near zero in steady state, and sustained growth means the relay process has
stalled or lost its connection to the broker, an incident distinct from, and
upstream of, any handler-side problem.

Every published event should be traceable end to end via a correlation
identifier that ties it back to the request or command that caused it, and a
causation identifier that ties a downstream event to the specific upstream
event that produced it, so an incident responder can reconstruct "checkout
request X caused OrderPaid, which caused InventoryDecremented, which caused
the negative-stock alert" as a single traceable chain rather than as three
unrelated log lines that must be correlated by hand from timestamps alone.

Per-handler failure counts and retry counts, broken out by handler and by
event type, are what actually localizes the second failure mode in dimension
11 (a poison message that one handler cannot process and keeps retrying)
before it exhausts a dead-letter queue or, worse, blocks an ordered partition
behind it.

## 17. Security and privacy implications

An event's payload is data at rest and in transit the moment it leaves the
process that raised it, and every subscriber that receives it becomes a place
that data now lives, whether or not that subscriber needed the full payload.
Fowler's own distinction between source data and processing data, discussed
in dimension 3, is directly a privacy control. Putting only the identifiers
and the minimum necessary fields into the event, rather than a full aggregate
snapshot, limits the blast radius of a compromised or over-permissioned
subscriber and reduces how many places a piece of personal data ends up
copied into. An event carrying a customer's full profile because it was
convenient to include "just in case a handler needs it later" turns every
future subscriber, including ones added by a different team years later with
no data-protection review, into a new place that data is stored.

Because events are frequently retained durably, in a broker's log, in an
outbox archive, or permanently in an event-sourced store, they inherit
whatever data-retention and right-to-erasure obligations apply to their
payload, and an event-sourced store is specifically difficult to reconcile
with a legal erasure request, because the event log is meant to be
append-only and immutable while a request such as GDPR's right to erasure
demands that specific personal data actually stop existing. Production
event-sourced systems commonly handle this by never putting directly
identifying personal data into the event payload at all, storing only a
reference (a customer identifier) and keeping the personal data itself in a
separately erasable store, so erasing the referenced record renders the
historical events meaningless without needing to rewrite an immutable log.
This is engineering judgement rather than a sourced universal requirement,
because the correct pattern varies by jurisdiction and by the specific legal
basis for retention.

Access control on a message broker or event store needs to be topic- or
stream-scoped, not all-or-nothing, because the natural shape of the pattern
fans one event out to many subscribers, and a subscriber with broader access
than its actual handler needs (subscribing to every event on a broker because
it was easier to configure than a narrow subscription) silently expands who
can read sensitive fact data. Event envelopes that carry a correlation
identifier, as recommended in dimension 16, should be checked for whether
that identifier itself is sensitive (a session token, an internal user
identifier that could be correlated with other leaked data) before it is
logged or shipped to a third-party observability vendor.

## 18. References

- Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
  Software*, Addison-Wesley, 2003. Establishes the tactical building blocks
  (Entity, Value Object, Aggregate, Service, Repository, Factory) that Domain
  Event was later added alongside.
- Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
  ISBN 9780321834577, Chapter 8, "Domain Events." Verified via the book's
  publisher chapter description and O'Reilly's hosted preface,
  <https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/pref03lev2sec8.html>,
  verified 2026-08-02.
- Martin Fowler, "Domain Event," martinfowler.com, published 12 December
  2005, <https://martinfowler.com/eaaDev/DomainEvent.html>, verified
  2026-08-02.
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018. General refactoring vocabulary used in
  dimension 14.
- Spring Data Commons reference documentation, "Publishing Events from
  Aggregate Roots," <https://docs.spring.io/spring-data/commons/reference/repositories/core-domain-events.html>,
  verified 2026-08-02.
- AxonIQ, `EventSourcingHandler` API documentation, Axon Framework 4.4,
  <https://apidocs.axoniq.io/4.4/org/axonframework/eventsourcing/EventSourcingHandler.html>,
  verified 2026-08-02.
- Stripe API Reference, "Events," <https://docs.stripe.com/api/events>,
  verified 2026-08-02, and Stripe Documentation, "Receive Stripe events in
  your webhook endpoint," <https://docs.stripe.com/webhooks>, verified
  2026-08-02.
- Debezium documentation, "Outbox Event Router,"
  <https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html>,
  verified 2026-08-02.
- Chris Richardson, microservices.io, "Pattern. Transactional outbox,"
  <https://microservices.io/patterns/data/transactional-outbox.html>,
  verified 2026-08-02.
- EventStoreDB product documentation, <https://www.eventstore.com/eventstoredb>,
  verified 2026-08-02. Named as the reference open-source event-sourcing
  store in dimension 8.

## Code

### TypeScript

```typescript
interface DomainEvent {
  readonly eventType: string;
  readonly occurredAt: Date;
}

class OrderPaid implements DomainEvent {
  readonly eventType = "OrderPaid";
  readonly occurredAt: Date;
  constructor(
    readonly orderId: string,
    readonly amountCents: number,
  ) {
    this.occurredAt = new Date();
  }
}

class Order {
  private pending: DomainEvent[] = [];
  private paid = false;

  constructor(private readonly id: string, private readonly totalCents: number) {}

  markPaid(): void {
    if (this.paid) {
      throw new Error("order already paid");
    }
    this.paid = true;
    this.pending.push(new OrderPaid(this.id, this.totalCents));
  }

  pullEvents(): DomainEvent[] {
    const events = this.pending;
    this.pending = [];
    return events;
  }
}

type Handler = (event: DomainEvent) => void;

class Dispatcher {
  private handlers = new Map<string, Handler[]>();

  on(eventType: string, handler: Handler): void {
    const list = this.handlers.get(eventType) ?? [];
    list.push(handler);
    this.handlers.set(eventType, list);
  }

  publish(events: DomainEvent[]): void {
    for (const event of events) {
      for (const handler of this.handlers.get(event.eventType) ?? []) {
        handler(event);
      }
    }
  }
}

function main(): void {
  const dispatcher = new Dispatcher();
  dispatcher.on("OrderPaid", (e) => {
    const paid = e as OrderPaid;
    console.log(`shipping notified for order ${paid.orderId}, ${paid.amountCents} cents`);
  });

  const order = new Order("ord-1", 4200);
  order.markPaid();
  dispatcher.publish(order.pullEvents());
}

main();
```

### Python

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable


@dataclass(frozen=True)
class OrderPaid:
    order_id: str
    amount_cents: int
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class OrderAlreadyPaidError(Exception):
    pass


class Order:
    def __init__(self, order_id: str, total_cents: int):
        self._id = order_id
        self._total_cents = total_cents
        self._paid = False
        self._pending: list[object] = []

    def mark_paid(self) -> None:
        if self._paid:
            raise OrderAlreadyPaidError(self._id)
        self._paid = True
        self._pending.append(OrderPaid(self._id, self._total_cents))

    def pull_events(self) -> list[object]:
        events, self._pending = self._pending, []
        return events


class Dispatcher:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[object], None]]] = {}

    def on(self, event_type: type, handler: Callable[[object], None]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, events: list[object]) -> None:
        for event in events:
            for handler in self._handlers.get(type(event), []):
                handler(event)


def notify_shipping(event: object) -> None:
    assert isinstance(event, OrderPaid)
    print(f"shipping notified for order {event.order_id}, {event.amount_cents} cents")


def main() -> None:
    dispatcher = Dispatcher()
    dispatcher.on(OrderPaid, notify_shipping)

    order = Order("ord-1", 4200)
    order.mark_paid()
    dispatcher.publish(order.pull_events())


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import (
	"fmt"
	"time"
)

type DomainEvent interface {
	EventType() string
}

type OrderPaid struct {
	OrderID     string
	AmountCents int
	OccurredAt  time.Time
}

func (OrderPaid) EventType() string { return "OrderPaid" }

type Order struct {
	id      string
	total   int
	paid    bool
	pending []DomainEvent
}

func NewOrder(id string, total int) *Order {
	return &Order{id: id, total: total}
}

func (o *Order) MarkPaid() error {
	if o.paid {
		return fmt.Errorf("order %s already paid", o.id)
	}
	o.paid = true
	o.pending = append(o.pending, OrderPaid{
		OrderID:     o.id,
		AmountCents: o.total,
		OccurredAt:  time.Now(),
	})
	return nil
}

func (o *Order) PullEvents() []DomainEvent {
	events := o.pending
	o.pending = nil
	return events
}

type Handler func(DomainEvent)

type Dispatcher struct {
	handlers map[string][]Handler
}

func NewDispatcher() *Dispatcher {
	return &Dispatcher{handlers: make(map[string][]Handler)}
}

func (d *Dispatcher) On(eventType string, h Handler) {
	d.handlers[eventType] = append(d.handlers[eventType], h)
}

func (d *Dispatcher) Publish(events []DomainEvent) {
	for _, e := range events {
		for _, h := range d.handlers[e.EventType()] {
			h(e)
		}
	}
}

func main() {
	dispatcher := NewDispatcher()
	dispatcher.On("OrderPaid", func(e DomainEvent) {
		paid := e.(OrderPaid)
		fmt.Printf("shipping notified for order %s, %d cents\n", paid.OrderID, paid.AmountCents)
	})

	order := NewOrder("ord-1", 4200)
	if err := order.MarkPaid(); err != nil {
		panic(err)
	}
	dispatcher.Publish(order.PullEvents())
}
```
