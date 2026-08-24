---
name: Event-Driven Architecture
slug: event-driven-architecture
family: 05-architectural
category: Architectural
aliases: [EDA, Event-Based Architecture, Reactive Event Architecture]
first_described: "Widely attributed usage from the late 1990s and early 2000s complex event processing literature; the term itself has no single named originator the way GoF patterns do"
maturity: canonical
related: [publish-subscribe, mediator, observer, cqrs, event-sourcing, saga, pipe-and-filter, layered-architecture]
incompatible_with: [strict-two-phase-commit, layered-architecture-with-synchronous-only-calls]
verified: 2026-08-02
---

# Event-Driven Architecture

## 1. Name, aliases, and lineage

The canonical name in industry use is Event-Driven Architecture, abbreviated EDA.
Unlike the Gang of Four patterns, EDA has no single named originator and no
single founding publication. It grew out of decades of independent practice.
mainframe transaction monitors reacting to interrupts, SCADA and industrial
control systems reacting to sensor signals, GUI toolkits reacting to input
events, and message-oriented middleware in the 1990s. The term crystallised as
a named architectural style through the complex event processing (CEP)
literature of the early 2000s and through vendor and analyst usage soon after.

Martin Fowler's 2017 talk and companion article, "What do you mean by 'Event
Driven'", is the most cited modern reference point for practitioners, because
it does the thing most vendor material does not. it splits the single label
into four distinct sub-styles with different consequences (Martin Fowler,
"What do you mean by 'Event-Driven'",
https://martinfowler.com/articles/201701-event-driven.html, verified
2026-08-02). Fowler names Event Notification, Event-Carried State Transfer,
Event Sourcing, and CQRS as four things people conflate under one label, and
this entry treats his taxonomy as the load-bearing vocabulary for dimension 5
and dimension 8, because most confusion about EDA in practice is confusion
about which of these four a given system actually is.

Two closely related terms are worth separating from EDA itself, because
catalogs routinely blur them.

- **Publish-Subscribe (pub-sub).** A messaging pattern where publishers emit
  messages to a named channel or topic without knowledge of subscribers, and
  subscribers register interest in a topic without knowledge of publishers.
  Pub-sub is the most common MECHANISM used to implement EDA, but EDA is the
  architectural style (how services are decomposed and how they communicate as
  a system-wide default), while pub-sub is one messaging pattern among several
  that can carry events. A system can use pub-sub for a single feature without
  being event-driven as a whole, and a system can be event-driven using
  point-to-point queues or streaming logs instead of a broadcast topic.
- **Complex Event Processing (CEP).** A technique for detecting patterns
  across streams of events in near real time, such as "three failed logins
  within one minute from the same account." CEP is a consumer-side
  capability that can sit on top of an event-driven system; it is not itself
  an architectural style for decomposing an application.

The name is not contested in the way some pattern names are, but its scope is
loosely defined in the literature. AWS treats event-driven architecture as "a
style of building loosely coupled software systems that work together by
emitting and responding to events" (Amazon Web Services, "What Is Amazon
EventBridge?", AWS documentation,
https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html,
verified 2026-08-02), and this entry adopts that framing as the working
definition, narrowed by Fowler's four sub-styles for precision.

## 2. Problem and context

A system built from several independently deployable components needs to
react to things that happen elsewhere in the system, without each component
knowing the internal state, schema, or availability of every other component
it depends on.

The situation appears concretely like this. An order service accepts a new
order. Three other things must now happen. inventory must be reserved,
a confirmation email must be sent, and a fraud check must run. The naive
approach has the order service call each of those three services directly,
synchronously, in sequence, inside the request that placed the order. This
works until any one of the three downstream services is slow, unavailable, or
gains a fourth or fifth consumer that also needs to know about new orders. At
that point the order service has become a hub that must know the address, the
contract, and the availability of every consumer of "an order was placed,"
and a single slow or down downstream service blocks the customer's checkout.

Chris Richardson frames the underlying problem for microservices specifically
as consistency across services that each own their own data. "How to maintain
data consistency across services?" is his stated problem statement for the
event-driven data pattern, and his proposed solution is that "each service
publishes an event whenever it updates its data" while other services
subscribe (Chris Richardson, microservices.io, "Pattern. Event-driven
architecture", https://microservices.io/patterns/data/event-driven-architecture.html,
verified 2026-08-02). This framing matters because it exposes the two distinct
problems EDA is regularly reached for, which are usually solved together but
are conceptually separable.

- **Decoupling of producers from consumers.** The order service should not
  need to know who currently cares about new orders, and new consumers should
  be addable without modifying the producer.
- **Consistency across independently owned data stores.** When a microservice
  architecture forbids shared databases and distributed two-phase commit is
  ruled out for availability and latency reasons, events plus eventual
  consistency become the mechanism by which state changes propagate.

The context that makes EDA the right answer combines three conditions. the
number of interested parties in a state change is unknown at design time or
expected to grow, near-real-time reaction is acceptable in place of immediate
consistency, and the cost of a temporarily stale read in a downstream system
is tolerable to the business. Where any of those three does not hold, see
dimension 4.

## 3. Forces

The pattern balances the following competing pressures. This dimension is
partly engineering judgement, drawn from the trade-offs documented across the
sources cited in dimension 9 and from the consequences of the mechanism itself
(fan-out messaging, at-least-once delivery, no shared transaction).

- **Coupling.** Strongly favoured. Producers depend only on an event schema,
  never on a consumer's address, protocol, or existence. New consumers arrive
  with zero changes to the producer.
- **Temporal coupling.** Favoured, with a caveat. A producer does not block
  waiting for a consumer to process an event, so a slow or down consumer no
  longer stalls the producer's request path. The caveat is that if the
  workflow genuinely requires the consumer's answer before the producer can
  proceed, decoupling delivery does not remove the need for a response,
  it only changes the shape of waiting for one (see dimension 11, the
  distributed monolith failure mode).
- **Consistency.** Sacrificed, deliberately. There is no single transaction
  spanning producer and consumer. The system is eventually consistent, and a
  reader of the consumer's state can observe a window where the producer's
  change has not yet been reflected.
- **Operability and debuggability.** Sacrificed. A single business
  transaction that used to be one stack trace is now scattered across several
  independently deployed services connected only by a message and a
  correlation identifier, and there is no single log to read top to bottom.
  See dimension 16.
- **Scalability and throughput.** Favoured. Producers and consumers scale
  independently, and a broker can buffer bursts that a synchronous call chain
  cannot.
- **Resilience to partial failure.** Favoured, again with a caveat. A down
  consumer does not take the producer down with it, because the event sits in
  the broker until the consumer recovers. The caveat is that the broker itself
  becomes a new single point of failure and a new operational dependency that
  did not previously exist.
- **Cognitive load.** Sacrificed for a reader tracing one business flow, and
  favoured for a reader working inside a single service, because that
  service's boundary shrinks to "consume this event type, produce that event
  type."
- **Testability.** Mixed. Unit testing one consumer against a known event is
  simple. End-to-end testing an entire business flow across several
  asynchronous hops is materially harder than testing a synchronous call
  chain. See dimension 15.
- **Ordering and exactly-once semantics.** Sacrificed by default. Most
  broadly deployed brokers offer at-least-once delivery and only
  partition-scoped ordering, not global ordering or exactly-once processing,
  so idempotency becomes the consumer's problem to solve, not the broker's.

No pattern that solves the coupling and scalability problem does so for free.
The price here is paid in consistency, operability, and idempotency
discipline, which is why dimension 4's non-applicability list is as long as
its applicability list.

## 4. Applicability and non-applicability

Reach for event-driven architecture when the following hold.

- The set of parties interested in a state change is not fully known at
  design time, or is expected to grow, and the producer should not need
  editing every time a new consumer appears.
- The business process tolerates eventual consistency between the moment a
  fact becomes true in one service and the moment every interested service
  has reacted to it, on the order of milliseconds to seconds for most
  systems, occasionally longer.
- Multiple independently deployed services each own a slice of data derived
  from the same underlying facts, and keeping those slices synchronised via
  distributed transactions is unacceptable for latency or availability
  reasons.
- Burst absorption matters. traffic spikes should be buffered by a durable log
  or queue rather than propagated synchronously to every downstream system at
  peak rate.
- Auditability of "what happened, in what order, and why" is valuable, and an
  append-only event log can double as that audit trail.
- The workload is naturally reactive. sensor readings, user interface input,
  webhooks from a third party, database change capture, none of which the
  system controls the timing of.

Do NOT reach for event-driven architecture in these cases, and the reason
matters more than the rule.

- **The workflow requires an immediate, synchronous answer before it can
  proceed.** A checkout flow that must know within the same request whether a
  payment authorised or declined cannot be modelled as fire-and-forget
  events without either blocking the response on a reply-event (which
  reintroduces synchronous coupling with none of the mechanism's benefits) or
  giving the user a misleading immediate success. Use a synchronous call, or
  a request-response pattern layered on top of messaging, not bare
  publish-and-forget.
- **There are only two services and their relationship is genuinely stable.**
  Introducing a broker, a schema registry, and eventual consistency to
  connect two services that will only ever be two services is unearned
  complexity. A direct call, ideally behind a well-defined interface, is
  cheaper to build, test, and operate.
- **Strong consistency is a hard business or regulatory requirement.** Double-
  entry ledger postings, seat reservation systems that must never oversell,
  and similar domains where "eventually correct" is not an acceptable
  substitute for "always correct" need transactional guarantees that EDA does
  not provide on its own. A saga or transactional outbox can bridge this gap,
  but the requirement should be recognised explicitly rather than discovered
  in production. See dimension 11.
- **The team cannot yet operate a message broker.** A durable, partitioned,
  replicated event log is a genuine distributed system with its own failure
  modes, upgrade cadence, and on-call burden. Adopting EDA without the
  operational maturity to run its infrastructure trades one class of problem
  for a worse one.
- **The workflow's steps have a natural, fixed, linear order that rarely
  changes, and only one team owns all of it.** A choreographed event chain
  across many consumers can be harder to reason about than the same steps
  expressed as an explicit orchestrated workflow (a Saga orchestrator or a
  simple sequential function) inside one deployable unit. Event-driven
  choreography earns its complexity when the steps are owned by different
  teams or must be independently extensible, not merely because "events feel
  more modern."
- **The event volume and schema evolution rate will outpace the team's
  ability to version and document event contracts.** An event schema is a
  public contract with every current and future consumer. Undisciplined,
  frequently changing event shapes are more damaging than an undisciplined
  internal function signature, because consumers are decoupled in time and
  cannot be found and updated in one atomic change the way call sites in a
  monolith can.
- **You need to know, at the moment a state change happens, whether all
  consumers agree to allow it.** Events model "this already happened."
  Validating whether something IS ALLOWED to happen, with the ability to
  reject it, is a synchronous concern (a command, a request), not an event.
  Conflating the two is a common and costly design error, covered in
  dimension 11.

## 5. Structure

Following Fowler's four-style taxonomy (dimension 1), the participants differ
by style, but a common vocabulary covers all of them.

- **Event.** An immutable fact describing something that already happened,
  named in the past tense ("OrderPlaced", not "PlaceOrder"). Carries a
  timestamp, an identifier, and either a reference to the changed entity
  (Event Notification) or a copy of the relevant state (Event-Carried State
  Transfer).
- **Producer (Event Source).** The component whose internal state change
  causes the event to be emitted. Owns the event schema and its versioning.
  Does not know, and should not need to know, who consumes the event.
- **Event Channel (Broker, Topic, Log, or Queue).** The infrastructure that
  receives events from producers and makes them available to consumers,
  decoupling them in time and in address. Its delivery, ordering, and
  retention guarantees are load-bearing design decisions, covered in
  dimension 8.
- **Consumer (Event Handler, Event Processor).** A component that reacts to
  one or more event types. May itself become a producer of new events
  derived from what it consumed, chaining reactions (event choreography).
- **Event Schema / Contract.** The versioned structure of an event's payload,
  shared as a contract between producer and every consumer, analogous to an
  API contract but consumed asynchronously and by parties the producer
  cannot enumerate.
- **In Event Sourcing specifically, the Event Store** additionally serves as
  the SYSTEM OF RECORD, not merely a transport mechanism. an entity's current
  state is derived by replaying its full event history rather than stored
  directly, which is a materially different structural commitment from the
  other three styles and is treated as a distinct pattern with its own entry
  in this catalog (see the Event Sourcing entry under
  `related`).
- **In CQRS specifically**, events (or the write model's changes) are the
  mechanism by which one or more read-optimised projections are kept in sync
  with a separately optimised write model; the read side and write side are
  structurally distinct components connected by the event flow.

## 6. ASCII structure diagram

```
EVENT NOTIFICATION / EVENT-CARRIED STATE TRANSFER
the two most common styles in service integration

+----------------------+
| Producer (Order Svc) |
+----------------------+
     | emits Order Placed
     v
+-------------------------------------+
| Event Channel (topic / queue / log) |
+-------------------------------------+
     | delivers to all subscribers
     v
+------------------+
| Consumer (Stock) |
+------------------+
+------------------+
| Consumer (Email) |
+------------------+
+------------------+
| Consumer (Fraud) |
+------------------+

Consumer (Stock) may itself emit a derived event.

+-------------------------------+
| Event Channel, Stock Reserved |
+-------------------------------+
     |
     v
+-----------------+
| Consumer (Ship) |
+-----------------+

Producer has NO reference to any Consumer. Consumers
have NO reference to Producer or to each other. Only
the Event Channel and the shared event schema couple
them.

EVENT SOURCING, the state IS the event log

+-----------------+
| Command Handler |
+-----------------+
     | append event(s)
     v
+-------------------------------------------------+
| Event Store, append-only, ordered per aggregate |
+-------------------------------------------------+
     | replay
     v
current state, derived, not stored

CQRS, read and write are separately optimised

+--------+
| Client |
+--------+
     | command
     v
+-------------+
| Write Model |
+-------------+
     | event(s)
     v
+-----------+
| Projector |
+-----------+
     |
     v
+-----------------------------------------+
| Read Model(s), denormalised, fast reads |
+-----------------------------------------+

Client also queries the Read Model(s) directly, never
through the Write Model.
```

## 7. Dynamics

The dynamics vary meaningfully by which of the four styles is in play, which
is exactly why conflating them causes real design mistakes. Two flows are
shown. the common Event Notification flow used for service integration, and
the choreography-versus-orchestration distinction that governs multi-step
business processes.

```
Event Notification, single hop, at-least-once delivery

Producer          Broker              Consumer
   |                  |                    |
   |-- publish("Order |                    |
   |    Placed", id123)                    |
   |----------------->|                    |
   |   (producer's    |                    |
   |    work is done  |                    |
   |    here; it does |                    |
   |    NOT wait)     |                    |
   |                  |-- deliver -------->|
   |                  |                    |-- process event
   |                  |                    |-- (idempotency
   |                  |                    |    check first)
   |                  |<-- ack ------------|
   |                  |   (broker may      |
   |                  |    re-deliver if   |
   |                  |    ack is lost or  |
   |                  |    delayed, hence  |
   |                  |    at-least-once,  |
   |                  |    hence idempotent|
   |                  |    consumers are   |
   |                  |    mandatory)      |
```

```
Choreography (each service reacts independently, no central coordinator)
versus Orchestration (one component directs the sequence)

Choreography.                          Orchestration.

Order --OrderPlaced--> Stock            Order --command--> Saga
  |                       |                                Orchestrator
  |                       v                                    |
  |                  StockReserved                    +--------+--------+
  |                       |                            |        |        |
  |                       v                            v        v        v
  |                     Shipping                     Stock    Payment  Shipping
  |                       |                          (command)(command)(command)
  |                       v                             |        |        |
  +---> ShipmentCreated <-+                             +--------+--------+
                                                          replies flow back
  No component owns the whole sequence;                  to the orchestrator,
  the sequence emerges from each                         which decides the
  service reacting to the last one's                     next step and owns
  event. Cheap to extend with a new                      compensation on
  consumer, hard to see the whole flow                    failure.
  in one place or one log.
```

The two timing properties that most influence correctness in practice.
First, delivery is at-least-once in the overwhelming majority of production
brokers, meaning a consumer must expect and correctly handle the same event
arriving twice, which is the idempotency requirement covered throughout this
entry. Second, ordering is typically only guaranteed within a partition or a
single stream, not globally across all events of all types, so a consumer
that needs "OrderPlaced before OrderShipped for the same order" must rely on
partitioning by order identifier, not on wall-clock arrival order.

## 8. Implementation variants

**Publish-subscribe with a broker.** A message broker (RabbitMQ, Google
Cloud Pub/Sub, Azure Service Bus) accepts publishes to a named topic and fans
out a copy to every subscribed consumer or consumer group. Simplest mental
model, widely supported, but typically offers shorter retention and less
built-in replay capability than a log-based broker.

**Durable log-based streaming.** A distributed, partitioned, replicated,
append-only log (Apache Kafka, Amazon Kinesis, Redpanda) retains events for a
configured period (often days to indefinitely) and lets consumers read at
their own offset, independently, at their own pace, including replaying from
an earlier point. This is the variant most associated with the term
"event-driven architecture" in current large-scale practice, because it
combines pub-sub fan-out with durable, replayable history. Confluent's
developer documentation describes a Kafka topic as "a log of events" that is
"append only," partitioned "into multiple logs, each of which can live on a
separate node," with consumers tracking their own read position
independently rather than the broker destroying a message once one consumer
reads it (Confluent, "What is Apache Kafka?", Confluent Developer,
https://developer.confluent.io/what-is-apache-kafka/, verified 2026-08-02).
This pull-based, offset-tracked read model is the defining mechanical
difference from a classic push-based message queue, where a consumed
message is typically removed from the queue for everyone.

**Serverless managed event bus / router.** A managed service (Amazon
EventBridge, Azure Event Grid) provides rule-based routing from many event
sources to many targets without the team operating broker infrastructure
directly. AWS documents EventBridge as using "event buses" that "are routers
that receive events and deliver them to zero or more targets," suited "for
routing events from many sources to many targets, with optional
transformation of events prior to delivery" (Amazon Web Services, "What Is
Amazon EventBridge?", AWS documentation,
https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html,
verified 2026-08-02). This variant trades operational control for reduced
undifferentiated infrastructure work, and suits organisations already
committed to a specific cloud provider.

**Webhooks (HTTP push, cross-organisation).** Instead of a shared broker,
the producer makes an outbound HTTP request directly to a URL the consumer
registered in advance, carrying the event as the request body. This is the
dominant variant for cross-organisation integration where operating a shared
broker is not possible, because the two parties do not share infrastructure.
GitHub documents webhooks as letting a party "subscribe to events happening
in a software system and automatically receive a delivery of data to your
server whenever those events occur" (GitHub, "About webhooks",
GitHub Docs, https://docs.github.com/en/webhooks/about-webhooks, verified
2026-08-02). The consumer, not a broker, is responsible for durability. a
missed delivery (the consumer's endpoint was down) requires the producer to
implement its own retry and dead-letter handling, since there is no shared
log to replay from.

**Database change data capture (CDC).** Rather than the application code
explicitly publishing an event, a CDC tool reads the database's transaction
or write-ahead log and turns each row insert, update, or delete into an
event automatically. This variant guarantees the event stream matches
exactly what was actually committed to the database (no risk of the
application forgetting to publish, or publishing before the commit
succeeds), at the cost of coupling the event schema to the database schema.

**In-process event bus (single-process, non-distributed).** Inside one
process, a lightweight publish-subscribe mechanism (Node.js's built-in
`EventEmitter`, a synchronous or async dispatcher, a domain-event collection
pattern in domain-driven design) decouples modules from each other without
crossing a process or network boundary. This is architecturally the same
Event Notification style at a much smaller radius, and is a legitimate,
lower-risk way to get the decoupling benefit of EDA before committing to
distributed infrastructure, or as a stepping stone toward it.

**Reply-event / request-response over messaging.** When a workflow needs an
answer, not just a notification, a request event carries a correlation
identifier and is met with a corresponding reply event on a dedicated
channel, letting the requester correlate replies to requests
asynchronously. This recovers request-response semantics on top of
asynchronous infrastructure at the cost of added complexity, and should only
be reached for when dimension 4's synchronous-answer case genuinely cannot
be served by a direct call.

## 9. Known production uses

**LinkedIn built and open-sourced Apache Kafka to solve exactly this class of
integration problem at scale, and Kafka is now the de facto reference
implementation of the durable log-based EDA variant industry-wide.** Kafka
models a topic as an append-only log and lets independent consumer groups
each track their own read offset. Confluent, "What is Apache Kafka?",
Confluent Developer, https://developer.confluent.io/what-is-apache-kafka/
verified 2026-08-02.

**Amazon EventBridge is AWS's managed event router**, used across AWS
customer architectures to connect first-party AWS services, third-party
SaaS products, and custom applications without the customer operating
broker infrastructure. AWS states it is "a serverless service that uses
events to connect application components together, making it easier for you
to build scalable event-driven applications." Amazon Web Services, "What Is
Amazon EventBridge?", AWS documentation,
https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html
verified 2026-08-02.

**Stripe's platform notifies every integrating merchant's backend of account
activity, such as a successful charge or a disputed payment, via webhooks
rather than requiring merchants to poll the API.** Stripe's documentation
states that after a webhook endpoint is registered, "Stripe kann
Ereignisdaten in Echtzeit an den Webhook-Endpoint Ihrer Anwendung senden,
wenn in Ihrem Stripe-Konto Ereignisse stattfinden" (Stripe can send event
data in real time to your application's webhook endpoint when events
happen in your Stripe account), explicitly framed as helping the
integrating application "auf asynchrone Ereignisse zu reagieren" (react to
asynchronous events). Stripe, "Registrieren Sie Stripe-Ereignisse in Ihrem
Webhook-Endpoint" ("Register Stripe events at your webhook endpoint"),
Stripe Docs, https://docs.stripe.com/webhooks verified 2026-08-02.

**GitHub notifies third-party integrations (CI systems, chat platforms,
project trackers) of repository activity such as pushes, pull requests, and
issue comments via webhooks**, the same HTTP-push variant described in
dimension 8. GitHub states webhooks "let you subscribe to events happening
in a software system and automatically receive a delivery of data to your
server whenever those events occur." GitHub, "About webhooks", GitHub Docs,
https://docs.github.com/en/webhooks/about-webhooks verified 2026-08-02.

**LMAX, a UK-based financial exchange, built the LMAX Disruptor as a
high-performance, single-process ring-buffer messaging component specifically
to move events between processing stages inside their exchange with lower
latency than a conventional bounded queue could offer.** The project's own
technical paper describes it as "a high performance alternative to bounded
queues for exchanging data between concurrent threads," built after finding
that "the latency costs...were in the same order of magnitude as the cost of
IO operations to disk." LMAX, "The LMAX Disruptor. High Performance,
Low-Latency, and Simple Too", technical paper,
https://lmax-exchange.github.io/disruptor/disruptor.html verified
2026-08-02. This use case demonstrates the in-process implementation variant
from dimension 8 at the opposite end of the scale spectrum from Kafka.

**Microservices architectures broadly use event-driven data propagation as
the recommended alternative to distributed transactions across independently
owned service databases**, documented by Chris Richardson (author of
*Microservices Patterns*, Manning, 2018) as a named pattern. "each service
publishes an event whenever it updates its data" so that other services can
subscribe and keep their own derived data in sync, in place of two-phase
commit. Chris Richardson, microservices.io, "Pattern. Event-driven
architecture",
https://microservices.io/patterns/data/event-driven-architecture.html
verified 2026-08-02.

## 10. Consequences

Positive.

- Producers and consumers are decoupled in address, in availability, and in
  time. a consumer can be added, removed, or briefly unavailable without any
  change to, or outage of, the producer.
- The system absorbs bursts. a durable channel buffers a spike in producer
  activity rather than propagating it synchronously to every downstream
  system at once.
- New capabilities are added by adding a new consumer of an existing event
  stream, frequently with zero changes to any existing component, which is
  the Open Closed Principle applied at the system level rather than the
  class level.
- A durable, replayable event log (in the log-based streaming variant)
  doubles as an audit trail and, in some designs, as the mechanism to
  rebuild a derived read model from scratch after a bug is fixed.
- Independent services can be independently deployed, scaled, and owned by
  different teams, because the only shared artifact is the event schema, not
  a shared database or a shared deployment.

Negative.

- The system is only eventually consistent. There is a genuine window, from
  milliseconds to much longer under load or failure, during which different
  parts of the system disagree about the current state of the world, and the
  application's user-facing behaviour must be designed to tolerate that
  honestly rather than hide it.
- Tracing one business transaction across several asynchronous hops, run by
  different services, deployed independently, is materially harder than
  reading one call stack, and requires deliberate correlation-identifier
  discipline (dimension 16) that does not happen automatically.
- The event schema is a public, long-lived contract with every current and
  future consumer, and changing it is a coordination problem, not a
  refactor.
- At-least-once delivery is the default in most infrastructure, which pushes
  the responsibility for correctness under duplicate delivery onto every
  single consumer, forever.
- The message broker or event router becomes new, critical, shared
  infrastructure that the team must operate, monitor, secure, and upgrade,
  where none previously existed.
- Debugging "why didn't X happen" is harder than debugging "why did this
  function throw," because the absence of a reaction can mean the event was
  never published, was published to the wrong topic, was delivered but
  silently failed processing, or is simply delayed.

## 11. Failure modes and misuse

**The distributed monolith.** Symptom. Deploying any one service requires
coordinating a deployment window with several other teams, because a change
to one event's shape breaks three downstream consumers simultaneously, and
the system as a whole cannot tolerate any single service being briefly
unavailable without cascading failures. Cause. Services were split
along organisational lines, but the events between them still encode a tight,
synchronous-in-spirit sequential workflow, so the loose coupling that events
promise never materialised, it was merely relocated into runtime message
flow instead of compile-time function calls. Fix. Either genuinely decouple
the event contracts (each event stands alone as a fact, versioned
independently, tolerant of unknown fields) or admit the workflow is
tightly coupled and merge the services, rather than paying distributed-system
costs for monolith-strength coupling.

**Missing idempotency causing duplicate side effects.** Symptom. A customer
is charged twice, or receives the same confirmation email three times, and
the incident report says "the event was only published once." Cause. The
consumer performed a non-idempotent side effect (charge a card, send an
email) without a deduplication check, and the broker's at-least-once
delivery guarantee (which is the default for the overwhelming majority of
production message infrastructure) redelivered the same event, which the
team had implicitly and incorrectly assumed could not happen. Fix. Every
consumer records the identifiers of events it has already fully processed
(an idempotency key, an event identifier plus a processed-events table with
a unique constraint) and short-circuits on a repeat before performing any
side effect.

**Lost update / silently dropped event with no alerting.** Symptom. A
customer's order status is permanently stuck in "processing" because the
event that would have advanced it was published to a topic no consumer was
listening to at the time, or was rejected by a schema validator and silently
discarded, and nobody noticed for days. Cause. No dead-letter queue, no
monitoring on consumer lag, no alert on schema-validation rejection rate.
Fix. Route unprocessable events to a dead-letter channel rather than
discarding them, alert on consumer lag exceeding a threshold, and alert on
any non-zero validation-rejection rate rather than treating "zero events for
a while" as inherently healthy.

**Choosing choreography for a process that needed a single owner.** Symptom.
A new engineer asks "what actually happens when a customer cancels an
order?" and the honest answer is "read the code of six services and
reconstruct the chain of events by hand," because no single artifact
describes the end-to-end sequence. Cause. A business process with clear
sequential steps and clear failure/compensation semantics was implemented as
pure choreography (each service reacts to the last one's event with no
coordinator), which is cheap to extend but expensive to understand and to
recover correctly on partial failure. Fix. Introduce an explicit orchestrator
(a saga coordinator, or a simple stateful workflow) for processes with
well-defined steps and compensation logic, reserving pure choreography for
genuinely open-ended fan-out (dimension 8, dimension 12).

**Using an event where a command was needed.** Symptom. A "PaymentRequested"
event is published, three services react to it, and later it turns out one
of them silently rejected the payment, but nothing in the flow ever asked
"is this payment allowed" BEFORE proceeding, because events cannot be
vetoed once emitted. Cause. Confusing a command (an instruction that can be
accepted or rejected, "please charge this card") with an event (an
immutable statement that something already happened, "this card was
charged"), and modelling the former as the latter. Fix. Use a synchronous or
request-response call for anything that must be validated or can be refused
before it takes effect; reserve events strictly for facts that have already,
irreversibly, happened.

**Fan-out amplification / thundering herd on a downstream dependency.**
Symptom. A batch job publishes ten thousand events in one second, and every
one of them triggers a call from several consumers to the same downstream
database or third-party API, which then falls over under the combined load,
even though no single consumer was individually misbehaving. Cause. The
decoupling that events provide hides the AGGREGATE load multiple consumers
place on a shared downstream resource, because no single component sees the
combined rate. Fix. Rate-limit or batch consumer-side calls to shared
downstream dependencies, and load-test the full fan-out topology, not just
individual consumers in isolation.

**Schema drift breaking a consumer nobody remembered existed.** Symptom. A
producer team removes a field from an event they believe is unused, deploys
on schedule, and a consumer team's system silently starts failing, days
later, because a batch report that ran monthly finally hit the missing
field. Cause. There was no registry, no contract test, and no ownership
record of who consumes a given event type, so the producer had no way to
know the true blast radius of a schema change. Fix. Maintain a schema
registry with backward-compatibility enforcement, and require producer-side
consumer-driven contract tests (see dimension 15) before a breaking change
can ship.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Event-Driven Architecture | Synchronous REST/RPC calls | Layered architecture with a shared database | Distributed transaction (2PC / XA) | Event Sourcing (as the persistence model) | Batch ETL / nightly sync |
|---|---|---|---|---|---|---|
| Coupling between components | Low. Only the event schema is shared | High. Caller must know callee's address and contract | Very high. All layers share one schema | High. All participants must implement the transaction protocol | Low, same as EDA, plus the store is the contract | Low at read time, high at schema-mapping time |
| Consistency model | Eventual | Strong, within the call | Strong, within the database transaction | Strong, across services | Strong per aggregate stream, eventual for read projections | Stale by up to the batch interval |
| Failure isolation | Strong. A down consumer does not block the producer | Weak. A down callee blocks or fails the caller's request | Weak. A locked or slow table affects every layer reading it | Weak. Any participant's failure can block the whole transaction (blocking protocol) | Strong for writes, depends on projector health for reads | Strong, but staleness itself is the cost |
| Latency for the initiating request | Low. Producer returns as soon as the event is durably accepted | Depends entirely on the callee's latency, fully additive in a chain | Low, single transaction | High. Coordination overhead across all participants | Low, same as EDA | Not applicable, no request waits |
| Auditability | Strong, if events are retained. the log is the history | Weak, unless explicitly logged | Weak, unless change-tracked | Weak, unless explicitly logged | Very strong. the event log is the sole source of truth | Moderate, depends on ETL logging |
| Operational complexity | High. broker, schema registry, monitoring, dead-letter handling | Low. no additional infrastructure beyond the services themselves | Low, for a single database | Very high, distributed coordinator, participant recovery | Very high, plus snapshotting and projection rebuild strategy | Moderate, scheduler and mapping logic |
| Correctness under duplicate/partial failure | Requires deliberate idempotency in every consumer | Simpler, but still needs retry-safety on the client | Handled by the database's own transaction guarantees | Handled by the protocol, at a steep availability cost | Requires idempotency in projectors, same discipline as EDA | Simplified by re-running the whole batch |
| Team/organisational fit | Good for many independently owned services | Good for a small number of tightly related services | Good for a single team owning one deployable | Poor. rarely used in modern microservice practice for this reason | Good where full history and replay have real business value | Good where near-real-time reaction is not required |

Reading of the table. EDA and synchronous calls sit at opposite ends of the
coupling-versus-consistency trade-off, and most real systems use both,
choosing synchronous calls for anything that must be validated or answered
before it can proceed, and events for anything that is a downstream reaction
to a fact that already happened. Distributed transactions solve the same
cross-service consistency problem EDA solves for eventual consistency, but at
an availability and complexity cost that has made them rare in modern
practice outside specific regulated domains. Event Sourcing is not an
alternative to EDA so much as a stricter, persistence-level commitment that
frequently sits underneath an event-driven system, and batch ETL is the
correct choice precisely when the business does not need the near-real-time
reactivity EDA is built to provide.

## 13. Related and incompatible patterns

- **Publish-Subscribe.** The primary MECHANISM used to implement Event
  Notification style EDA. Every pub-sub system embodies EDA at the messaging
  layer, but EDA as an architectural style is broader, encompassing schema
  ownership, service boundaries, and system-wide reactive decomposition, not
  merely the messaging primitive.
- **Observer.** The single-process, object-oriented ancestor of EDA. Where
  Observer couples a subject to a fixed, in-memory list of observer objects
  within one process, EDA generalises the same "notify interested parties of
  a change" idea across process and network boundaries with durable,
  addressable channels instead of direct object references.
- **Mediator.** A partial substitute at the in-process scale. A Mediator
  centralises interaction logic between a fixed set of known colleagues
  inside one component, whereas EDA deliberately has no mediator and no
  fixed, known set of consumers. Choosing Mediator over an in-process event
  bus is the right call when the set of interacting parties is small,
  known, and stable.
- **Event Sourcing.** Composes tightly, and is frequently confused with EDA
  itself despite being a distinct commitment. EDA describes how components
  communicate; Event Sourcing describes how a single aggregate's state is
  PERSISTED, as a sequence of events rather than as current-state rows. A
  system can be event-driven without using Event Sourcing for its
  persistence (most are), and, less commonly, a system can use Event
  Sourcing for one aggregate's persistence without the surrounding system
  being broadly event-driven.
- **CQRS (Command Query Responsibility Segregation).** Frequently paired
  with EDA, because the mechanism that keeps a CQRS read model synchronised
  with the write model is, in almost every real implementation, an event.
  CQRS is about separating read and write models; EDA is about how the
  write side's changes propagate to the read side (and to any other
  interested party). They compose well and are often adopted together, but
  neither requires the other.
- **Saga.** The named pattern for coordinating a multi-step business
  transaction across several services WITHOUT distributed transactions,
  using either choreography (a chain of events, dimension 7) or
  orchestration (a central coordinator issuing commands and handling
  compensation). Saga is the answer to the "distributed monolith" and
  "choreography needed a single owner" failure modes in dimension 11 when
  the business process genuinely has ordered steps and failure
  compensation requirements.
- **Pipe and Filter.** A structural cousin. Pipe and Filter typically
  implies a linear or DAG-shaped sequence of transformation stages
  connected by explicit pipes, often synchronous or in-process, whereas EDA
  implies an open-ended, potentially many-to-many fan-out where the
  producer does not enumerate its consumers. A log-based streaming
  platform used to chain several transformation stages can look like Pipe
  and Filter implemented on event-driven infrastructure, and the two
  concepts blend at that boundary.
- **Layered Architecture (with synchronous-only inter-layer calls) is
  incompatible in spirit**, not in the sense that the two cannot coexist in
  one codebase, but in the sense that a component genuinely committed to
  event-driven decoupling from its consumers cannot simultaneously assume a
  strict, synchronous, layered call chain governs how it is invoked; the two
  represent opposite defaults for coupling and timing, and mixing them in
  one component's contract (sometimes it is called synchronously and must
  answer immediately, sometimes it merely observes an event and may answer
  whenever) is a common source of the "distributed monolith" failure mode.
- **Strict two-phase commit (2PC/XA) across autonomous services is
  incompatible with EDA's core value proposition.** EDA exists in large part
  as the accepted alternative to distributed transactions for cross-service
  consistency (dimension 2, dimension 9); adopting both simultaneously for
  the same consistency boundary is contradictory, though a single service
  may still use a local ACID transaction internally before publishing an
  event, which is not the same thing and is in fact the recommended pattern
  (see the Transactional Outbox pattern, cross-referenced in the messaging
  family).

## 14. Refactoring path in and out

Introducing event-driven architecture into a system that currently
communicates synchronously.

1. Identify one specific fan-out point. a place where a producer's state
   change currently triggers two or more synchronous downstream calls, and
   at least one of those calls does not need to complete before the
   producer's own request can return successfully to its caller.
2. Confirm the downstream effect is genuinely a REACTION to a fact, not a
   validation the producer needs an answer to before proceeding (dimension
   4, dimension 11). If it is a validation, stop, this is not a candidate.
3. Define the event schema first, independently of any implementation. name
   it in the past tense, include only the data a consumer plausibly needs,
   version it explicitly from the start.
4. Stand up the channel (an in-process event bus is an acceptable first
   step, dimension 8, before committing to distributed infrastructure).
5. Change the producer to publish the event in addition to its existing
   synchronous calls, without removing the synchronous calls yet. Verify the
   event is actually published, with the correct shape, under real traffic.
6. Migrate one consumer at a time from being called synchronously by the
   producer to instead subscribing to the event. After each migration,
   verify the consumer still produces the same observable outcome, then
   remove the now-redundant synchronous call from the producer.
7. Add idempotency handling to each migrated consumer before removing the
   synchronous call it replaces, never after, since the synchronous call
   was the only thing guaranteeing at-most-once execution up to that point.
8. Add the monitoring from dimension 16 (consumer lag, dead-letter volume,
   correlation-identifier propagation) before declaring the migration
   complete, not as a follow-up task.

Removing event-driven architecture when it stops earning its place. Signals
include a system where every consumer of a given event type turns out to be
owned by the same team as the producer, or a business process that has
calcified into a strict linear sequence that is never independently
extended by another team, or an event type with exactly one consumer that
has had exactly one consumer for a long time with no plan to add more.

1. Confirm the consuming service genuinely has no other reason to remain a
   separate deployable (data ownership boundary, independent scaling need,
   independent team ownership). If any of those still hold, do not merge
   the services merely because the messaging feels like overhead; replace
   the broker hop with a direct call instead, keeping the services
   separate.
2. Replace the asynchronous publish with a direct, synchronous call,
   carrying the same payload the event carried, and delete the topic or
   queue for that event type once no other consumer depends on it.
3. If merging services entirely, inline the consumer's logic as a function
   call within the producer's own transaction boundary, and delete the now
   fully unused event schema, consumer, and channel configuration.
4. Remove the associated dead-letter queue, consumer-lag alerting, and
   schema-registry entries for the retired event type; leftover monitoring
   for a channel nobody publishes to any more is a common source of alert
   fatigue.

## 15. Testing and verification

Easier because of the pattern.

- Each consumer can be unit tested in complete isolation by constructing a
  known event payload and asserting the consumer's resulting side effect or
  state change, with no need to stand up the producer, the broker, or any
  other consumer.
- A producer's responsibility can be tested by asserting only that the
  correct event, with the correct shape, was published, without needing any
  consumer to exist at test time at all.
- Because events are immutable, recorded facts, a captured stream of
  production events (with sensitive fields redacted) makes an excellent,
  realistic fixture set for replay-based testing of a new or changed
  consumer.

Harder because of the pattern.

- An end-to-end business flow that used to be one synchronous call chain,
  testable with one integration test, is now scattered across several
  asynchronous hops, each of which may complete at a different, unspecified
  time, which makes naive "call the API and immediately assert the result"
  integration tests flaky by construction.
- Proving that a consumer correctly handles duplicate delivery, out-of-order
  delivery, and a temporarily unavailable downstream dependency requires
  deliberately injecting those conditions, which most synchronous
  integration tests never need to consider.
- Verifying that a schema change does not silently break a consumer the
  producing team does not own or have visibility into requires a mechanism
  that spans team boundaries, not just spans test suites within one
  repository.

Techniques that apply.

- **Consumer-driven contract testing.** Each consumer publishes a small,
  versioned set of example event payloads it depends on being able to
  parse and act on correctly. The producer's build runs every registered
  consumer's contract against any candidate event schema change, and a
  breaking change fails the producer's own build before it can ship,
  turning an asynchronous, hard-to-detect breakage into a synchronous,
  immediate build failure.
- **Idempotency tests as a first-class requirement, not an afterthought.**
  For every consumer, a test asserts that processing the same event twice
  produces the same observable outcome as processing it once, directly
  exercising the failure mode from dimension 11.
- **Await-based (polling) assertions instead of fixed sleeps in
  integration tests.** Rather than `sleep(2)` and hope the asynchronous
  consumer has finished, poll the consumer's observable state (a database
  row, a metric, a downstream call) with a bounded timeout, which is both
  faster on the common path and more reliable under load than a fixed
  delay.
- **Chaos-style fault injection at the broker or network boundary.**
  Deliberately delaying, duplicating, or dropping a percentage of test
  traffic between producer and consumer during integration testing surfaces
  ordering and idempotency bugs that a happy-path test will never find.
- **Replay testing against captured production event streams.** Running a
  changed consumer against a redacted, representative sample of real
  historical events before deploying it catches schema-edge-case bugs that
  synthetic test fixtures, written by the same engineer who wrote the
  consumer, tend to systematically miss.

## 16. Observability signals

Event-driven systems make the "what happened, top to bottom" narrative
invisible by default, so the telemetry has to reconstruct it deliberately or
nobody can diagnose a production incident that spans more than one service.

What to record.

- A correlation identifier (sometimes called a trace identifier or a
  causation chain) generated at the point a business transaction begins and
  propagated on every event derived from it, so that every downstream
  effect of one customer action can be found with a single query across
  every service's logs.
- Consumer lag, per consumer group, per topic or channel. the gap between
  the latest published offset and the offset a given consumer has actually
  processed. This is the single most useful health signal for a log-based
  streaming system, because rising lag is almost always the first visible
  sign of a struggling or stuck consumer, well before any error is thrown.
- Dead-letter queue depth and rate, labelled by event type and failure
  reason. a healthy system's dead-letter queue is empty or near-empty;
  any sustained non-zero rate is an active incident, not background noise.
- Event publish rate and consumer processing rate, per event type,
  compared against each other. a sustained gap between the two (publishing
  outpacing processing) is the earliest leading indicator of an incident
  that has not yet become visible as user-facing lag or errors.
- Schema-validation rejection rate at both the producer and consumer side,
  so a breaking schema change is caught the moment it starts rejecting real
  traffic rather than being discovered from a downstream symptom days
  later.
- End-to-end latency from event publish to consumer completion, per event
  type, not merely per-hop latency, because a chain of individually fast
  hops can still add up to an unacceptable end-to-end delay.

A healthy instance on a dashboard. Consumer lag for every consumer group sits
near zero and does not trend upward over a shift. The dead-letter queue is
empty. Publish rate and processing rate track each other closely across
normal daily and weekly traffic patterns. Schema-validation rejections are
zero. A correlation identifier picked at random from production logs can be
followed, end to end, across every service that reacted to it, with no gaps.

A failing instance. Consumer lag climbs steadily and does not recover on its
own, which usually means a consumer is stuck, crashing, or too slow for the
current traffic rate, not merely "busy." Dead-letter queue depth rises for
one specific event type, which localises the failure to one producer-consumer
contract rather than the whole system. Publish rate holds steady while
processing rate drops, which is the aggregate fan-out effect from dimension
11 becoming visible as a single graph rather than requiring each consumer to
be checked individually. A correlation identifier that stops appearing in any
downstream service's logs after a certain point in the chain marks exactly
where the reaction silently died, which is the fastest way to localise the
failing hop in a system that otherwise has no single stack trace to read.

## 17. Security and privacy implications

Event-driven architecture is not silent on security the way a purely
structural pattern can be, because events are, by design, data that crosses
service and often organisational boundaries and is frequently retained,
sometimes indefinitely, in a durable log.

**Event payloads become a durable, replicated copy of whatever data they
carry, often for far longer than the original database row would be
retained.** A log-based streaming platform commonly retains events for days,
weeks, or indefinitely by configuration, meaning any personal or sensitive
data included in an event payload is now durably copied into infrastructure
that may have different access controls, different encryption posture, and
different retention policy than the system of record. Treat event payload
design as a data classification decision, not merely a convenience decision
about what a consumer might find useful, and prefer carrying an identifier
plus a "go fetch the current state" reference over embedding sensitive
fields directly in the event, unless the specific consumer's use case
genuinely requires Event-Carried State Transfer's full-payload approach.

**A broadly subscribable topic widens the blast radius of a data exposure
far beyond what a single API endpoint's access control list would allow.**
Where a synchronous API can enforce authorization per caller, per field, per
request, a topic that many services subscribe to often applies one
coarse-grained access policy to the whole event stream, meaning a new
consumer added later, potentially by a different team with different
authorization needs than the original consumers, may gain access to fields
it should never see. Apply field-level or event-type-level access control at
the channel, not merely trust that "only internal services subscribe to
this," and review the actual subscriber list on any topic carrying sensitive
data on a recurring basis, not just at design time.

**Cross-organisation webhook delivery is a live attack surface that requires
active verification, not implicit trust in the sender.** Because webhooks
are delivered as ordinary inbound HTTP requests to a publicly reachable
endpoint, an attacker can attempt to forge an event by simply POSTing a
crafted payload to the same URL. Every webhook consumer must verify a
cryptographic signature or shared secret supplied by the legitimate sender,
reject payloads without a valid signature, and treat an unauthenticated
inbound webhook request as untrusted input in exactly the same way an
unauthenticated API request would be treated, never as a trusted internal
message merely because it arrived on the expected URL.

**Broker and topic access control is a distinct, easily overlooked
permission surface from application-level authorization.** A service
account with publish rights to a topic can inject fabricated events that
every downstream consumer will treat as fact, and a service account with
subscribe rights to a topic gains read access to every field of every
event that topic ever carries, for as long as retention allows, including
events published before that consumer existed if replay is supported.
Broker-level access control (who may publish to, and who may subscribe to,
each specific topic) needs the same rigor as database access control, and
is frequently under-audited precisely because it sits in infrastructure
configuration rather than in application code where security reviews
usually focus.

**Idempotency keys and correlation identifiers, if not chosen carefully,
can themselves leak information.** A correlation identifier derived
predictably from a customer's account number or email address, propagated
across every log line in every consuming service, effectively creates a
cross-system tracking identifier for that customer that persists well beyond
the lifetime of any single request, with retention and access implications
of its own. Prefer opaque, randomly generated correlation and idempotency
identifiers over identifiers derived from personal data, and apply the same
retention and access discipline to correlation identifiers in log
infrastructure as to any other piece of data that can be used to track an
individual across systems.

## 18. References

1. Martin Fowler. "What do you mean by 'Event-Driven'". martinfowler.com,
   2017. https://martinfowler.com/articles/201701-event-driven.html
   Verified 2026-08-02. Source of the four-style taxonomy (Event
   Notification, Event-Carried State Transfer, Event Sourcing, CQRS) used
   throughout dimensions 1, 5, and 8.
2. Amazon Web Services. "What Is Amazon EventBridge?". AWS documentation.
   https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html
   Verified 2026-08-02. Source of the working definition of event-driven
   architecture and the EventBridge event-bus production use in dimensions
   1, 8, and 9.
3. Chris Richardson. microservices.io, "Pattern. Event-driven architecture".
   https://microservices.io/patterns/data/event-driven-architecture.html
   Verified 2026-08-02. Source of the cross-service data consistency
   problem framing in dimension 2, and the named microservices production
   use in dimension 9. See also Chris Richardson, *Microservices Patterns*,
   Manning Publications, 2018, for the extended treatment of this pattern.
4. Confluent. "What is Apache Kafka?". Confluent Developer documentation.
   https://developer.confluent.io/what-is-apache-kafka/ Verified 2026-08-02.
   Source of the append-only log, partitioning, and consumer-offset model
   described in dimensions 8 and 9.
5. Stripe. "Registrieren Sie Stripe-Ereignisse in Ihrem Webhook-Endpoint".
   Stripe Docs. https://docs.stripe.com/webhooks Verified 2026-08-02.
   Source of the Stripe webhook production use in dimension 9. Page served
   in German at time of verification; quoted text translated in the entry
   with the original German preserved alongside it.
6. GitHub. "About webhooks". GitHub Docs.
   https://docs.github.com/en/webhooks/about-webhooks Verified 2026-08-02.
   Source of the webhook implementation variant description in dimension 8
   and the GitHub production use in dimension 9.
7. LMAX. "The LMAX Disruptor. High Performance, Low-Latency, and Simple
   Too". Technical paper.
   https://lmax-exchange.github.io/disruptor/disruptor.html Verified
   2026-08-02. Source of the in-process, single-machine implementation
   variant and the LMAX production use in dimensions 8 and 9.

## Code examples

Three languages, chosen because each demonstrates a genuinely different
implementation variant from dimension 8 rather than the same shape three
times. TypeScript demonstrates an in-process, synchronous event bus using
Node's built-in `EventEmitter`, the smallest possible entry point into the
style. Python demonstrates an asyncio-based publish-subscribe bus with
idempotent, at-least-once-tolerant consumers, closer to how a real service
integration is built. Go demonstrates a minimal durable, replayable,
in-memory event log with per-consumer offsets, structurally modelling the
Kafka-style log variant from dimension 8 without any external broker
dependency, so the example runs standalone. Rust and Swift are omitted
because the pattern does not meaningfully change shape in either beyond what
the three examples already show (a channel plus a callback registry), and
including them would add repetition rather than new information; the
publish-subscribe mechanism in both languages follows the same channel
and callback shape shown in TypeScript and Python.

### TypeScript, in-process Event Notification with EventEmitter

```typescript
import { EventEmitter } from "node:events";

interface OrderPlaced {
  orderId: string;
  total: number;
  occurredAt: string;
}

class OrderService extends EventEmitter {
  placeOrder(orderId: string, total: number): void {
    const event: OrderPlaced = {
      orderId,
      total,
      occurredAt: new Date().toISOString(),
    };
    this.emit("OrderPlaced", event);
  }
}

const seenOrderIds = new Set<string>();

function reserveStock(event: OrderPlaced): void {
  if (seenOrderIds.has(event.orderId)) {
    return;
  }
  seenOrderIds.add(event.orderId);
  console.log(`stock reserved for order ${event.orderId}`);
}

function sendConfirmation(event: OrderPlaced): void {
  console.log(`confirmation sent for order ${event.orderId}, total ${event.total}`);
}

const orders = new OrderService();
orders.on("OrderPlaced", reserveStock);
orders.on("OrderPlaced", sendConfirmation);

orders.placeOrder("order-1", 42.5);
orders.placeOrder("order-1", 42.5);
```

### Python, asyncio publish-subscribe with idempotent consumers

```python
import asyncio
from dataclasses import dataclass
from typing import Callable, Awaitable


@dataclass(frozen=True)
class OrderPlaced:
    order_id: str
    total: float


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[OrderPlaced], Awaitable[None]]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[OrderPlaced], Awaitable[None]]) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    async def publish(self, event_type: str, event: OrderPlaced) -> None:
        for handler in self._subscribers.get(event_type, []):
            await handler(event)


class StockReserver:
    def __init__(self) -> None:
        self._processed: set[str] = set()

    async def handle(self, event: OrderPlaced) -> None:
        if event.order_id in self._processed:
            return
        self._processed.add(event.order_id)
        print(f"stock reserved for {event.order_id}")


async def send_confirmation(event: OrderPlaced) -> None:
    print(f"confirmation sent for {event.order_id}, total {event.total}")


async def main() -> None:
    bus = EventBus()
    reserver = StockReserver()
    bus.subscribe("OrderPlaced", reserver.handle)
    bus.subscribe("OrderPlaced", send_confirmation)

    event = OrderPlaced(order_id="order-1", total=42.5)
    await bus.publish("OrderPlaced", event)
    await bus.publish("OrderPlaced", event)


if __name__ == "__main__":
    asyncio.run(main())
```

### Go, minimal durable log with per-consumer offsets

```go
package main

import (
	"fmt"
	"sync"
)

type Event struct {
	Type string
	Data string
}

type EventLog struct {
	mu     sync.Mutex
	events []Event
}

func (l *EventLog) Append(e Event) int {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.events = append(l.events, e)
	return len(l.events) - 1
}

func (l *EventLog) ReadFrom(offset int) []Event {
	l.mu.Lock()
	defer l.mu.Unlock()
	if offset >= len(l.events) {
		return nil
	}
	out := make([]Event, len(l.events)-offset)
	copy(out, l.events[offset:])
	return out
}

type Consumer struct {
	name   string
	offset int
	log    *EventLog
}

func (c *Consumer) Poll() {
	batch := c.log.ReadFrom(c.offset)
	for _, e := range batch {
		fmt.Printf("[%s] processed %s. %s\n", c.name, e.Type, e.Data)
		c.offset++
	}
}

func main() {
	log := &EventLog{}
	log.Append(Event{Type: "OrderPlaced", Data: "order-1"})
	log.Append(Event{Type: "OrderPlaced", Data: "order-2"})

	stockConsumer := &Consumer{name: "stock", log: log}
	emailConsumer := &Consumer{name: "email", log: log}

	stockConsumer.Poll()
	emailConsumer.Poll()

	log.Append(Event{Type: "OrderPlaced", Data: "order-3"})

	stockConsumer.Poll()
	emailConsumer.Poll()
}
```
