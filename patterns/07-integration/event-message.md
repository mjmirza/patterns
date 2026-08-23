---
name: Event Message
slug: event-message
family: 07-integration
category: Integration
aliases: [Event Notification, Domain Event Message, Event Record]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [message, publish-subscribe-channel, document-message, command-message, message-bus, dead-letter-channel]
incompatible_with: []
verified: 2026-08-02
---

# Event Message

## 1. Name, aliases, and lineage

The canonical name is Event Message, catalogued in Gregor Hohpe and Bobby
Woolf, *Enterprise Integration Patterns. Designing, Building, and Deploying
Messaging Solutions*, Addison-Wesley, 2003, in the Message Construction
chapter alongside Command Message and Document Message. The book's own page
for the pattern states the intent plainly, use an Event Message for
reliable, asynchronous event notification between applications
(https://www.enterpriseintegrationpatterns.com/patterns/messaging/EventMessage.html,
verified 2026-08-02). The pattern is one of three canonical message-content
variants in that catalog, distinguished from Command Message (an instruction
to be carried out) and Document Message (a data transfer with no implied
action) by what it asserts. an Event Message asserts that something has
already happened, past tense, and the sender does not require or expect
anything specific to happen as a result.

Domain-Driven Design literature calls the same idea a Domain Event when it
crosses a bounded-context boundary as a message, and treats the design of the
event's payload as a first-class modelling activity rather than an
afterthought bolted onto messaging infrastructure. Eric Evans introduces
events as a modelling element in Eric Evans, *Domain-Driven Design. Tackling
Complexity in the Heart of Software*, Addison-Wesley, 2003 (the same
publication year as the EIP catalog, a coincidence of timing rather than a
shared origin). Vaughn Vernon gives Domain Events a full chapter of practical
treatment, including the wire-message shape, in Vaughn Vernon, *Implementing
Domain-Driven Design*, Addison-Wesley, 2013, chapter 8, "Domain Events". The
Apache Kafka documentation uses the still broader term record or message
interchangeably with event, and defines an event plainly as something that
records the fact that "something happened in the world or in your business"
(https://kafka.apache.org/intro, verified 2026-08-02). The Cloud Native
Computing Foundation's CloudEvents specification, which reached CNCF
Graduated status in January 2024, formalises a wire envelope for exactly this
message shape across vendors (https://cloudevents.io/, verified 2026-08-02).

Two aliases are worth distinguishing rather than treating as synonyms. Event
Notification, used in some messaging vendor documentation, sometimes narrows
the meaning to a thin signal carrying only an identifier and a type, with the
receiver expected to call back for detail. Event-Carried State Transfer,
a term popularised by Martin Fowler in his 2017 conference talk and
accompanying writeup, "What do you mean by Event-Driven"
(https://martinfowler.com/articles/201701-event-driven.html, verified
2026-08-02), is not an alias for Event Message at all. it names a specific,
heavier payload strategy inside the Event Message pattern, described in
dimension 8 below. Conflating the thin notification style with the
state-carrying style is the single most common source of confused Event
Message design, because the two styles impose opposite coupling trade-offs
on every consumer.

## 2. Problem and context

An application performs an action that other applications, possibly ones the
first application has never heard of and will never know about, need to react
to. An order is placed. A price changes. A shipment leaves a warehouse. A user
closes their account. The originating application knows this happened at the
moment it happens. It does not know, and structurally should not know, which
other systems care, how many of them there are, what each one intends to do
about it, or when each one will get around to processing it.

The naive fix is a direct call. the order service calls the inventory service,
which calls the shipping service, which calls the notification service,
chained inline in the request path of placing an order. This works for exactly
as long as the set of interested parties is fixed and small, and it fails in
two predictable ways as the system grows. First, the calling service's
availability becomes the logical AND of every downstream service's
availability, because a synchronous call chain is only as reliable as its
weakest link. Second, every new consumer requires a code change in the
producer, because the producer must explicitly know who to call. Both failures
are coupling failures, and Event Message exists specifically to decouple the
fact that something happened from the list of parties who act on it.

The context in which Event Message is the right tool has three recurring
shapes. Fan-out, where one occurrence has many independent interested
consumers that should not block each other or the producer, an order placed
triggers billing, inventory, analytics, and email, none of which the order
service should need to wait on. Temporal decoupling, where the consumer may
not be online, may be slow, or may need to process the fact later at its own
pace, an audit log ingesting events hours after they occur is still correct.
And history, where the sequence of past occurrences itself has value beyond
the current state (event sourcing, analytics pipelines, compliance trails).
Where none of the three applies, and there is exactly one consumer that must
succeed synchronously before the caller can proceed, Event Message is the
wrong tool and a direct call or a Command Message is the correct one.

## 3. Forces

- **Coupling versus timeliness.** A direct synchronous call gives the sender
  immediate confirmation that the receiver acted, at the cost of coupling the
  sender's availability to the receiver's. An Event Message removes that
  coupling entirely but gives up the confirmation. the sender never learns
  whether, or when, or how many consumers acted on the event.
- **Payload richness versus staleness.** A thin event, an identifier and a
  type, forcing consumers to call back for detail, stays small and cheap to
  produce, but every consumer now makes a synchronous call back to the
  producer to get the data, reintroducing the coupling the event was meant to
  remove. A thick, state-carrying event avoids the callback but risks shipping
  data that is stale by the time a slow consumer reads it, and duplicates the
  producer's data model into every consumer's storage.
- **Ordering versus parallelism.** Guaranteeing that consumers see events in
  the order they occurred, needed when later events depend on earlier state,
  requires either a single ordered channel per aggregate or a partitioning
  scheme, both of which cap how much a consumer group can parallelise.
  Dropping the ordering guarantee unlocks arbitrary parallelism but pushes
  correctness work, idempotent, order-independent handlers, onto every
  consumer.
- **Delivery guarantee versus throughput and cost.** At-most-once delivery is
  cheap and fast, but silently drops events on any producer or broker fault.
  At-least-once delivery is the pragmatic default and requires idempotent
  consumers because duplicates will happen. Exactly-once delivery is the most
  expensive to build and operate correctly, and in most real brokers is really
  at-least-once delivery plus deduplication, not a distinct wire guarantee.
- **Expiration versus completeness.** The original EIP text observes that for
  many events, timeliness dominates fidelity. a stale price-changed event that
  arrives after the price changed again is often worse than no event at all,
  which is why Message Expiration is frequently paired with Event Message
  while it is rarely paired with Command Message, where the instruction must
  still be carried out even if late.
- **Schema evolution versus consumer independence.** Consumers built against
  today's event shape must keep working when the producer adds a field next
  quarter, which pushes the design toward additive-only, tolerant-reader
  schemas, at the cost of a payload that accumulates fields nobody but one
  consumer reads.

This pattern trades certainty and immediacy for decoupling and scale. Any
design that recovers certainty, for example by having the producer poll for
acknowledgement, has quietly reintroduced the coupling the pattern was chosen
to avoid, and should be examined for whether a Command Message with a reply
channel was the actual requirement.

## 4. Applicability and non-applicability

Reach for Event Message when.

- Multiple current or future consumers need to react to a fact, and the
  producer should not need to know who they are or how many there will be.
- The producer and consumers can tolerate the consumer acting after some
  delay, from milliseconds to hours, rather than requiring an immediate,
  synchronous, in-band result.
- The history of occurrences has value on its own, for audit, analytics,
  replay, or reconstructing state (event sourcing).
- Consumers can be added or removed without a code or deployment change to
  the producer, which is the operational signal that decoupling is actually
  working rather than merely declared.
- The business fact is genuinely past tense and irreversible from the
  producer's point of view. the order WAS placed, the payment WAS captured.
  An event describing something that has not yet been decided is a
  modelling error, not an event.

Do NOT reach for Event Message when.

- **The caller needs a result to proceed.** If the code that raises the
  occurrence cannot continue correctly until it knows the outcome, that is a
  synchronous call or a Request-Reply message exchange, not an event. Wrapping
  a required synchronous dependency in an event and then blocking on a
  response channel recreates tight coupling with worse debuggability.
- **There is exactly one consumer and it will always be exactly one.** A
  single, permanently fixed consumer gets nothing from the indirection of a
  broker and loses the straightforward stack trace and the ability to return
  a typed error. A direct call, or a Command Message if asynchrony alone is
  wanted, is simpler and equally decoupled from the caller's blocking.
- **The instruction is a request to perform an action**, not a report that one
  occurred. "Charge this card" is a Command Message. "This card was charged"
  is an Event Message. Naming a command in the past tense to disguise it as an
  event does not change its semantics, and consumers built expecting to react
  to a fact will misbehave when the fact has not actually happened yet.
- **Strong, immediate consistency across systems is a hard requirement**, for
  example a two-phase financial settlement that cannot leave the world in an
  inconsistent state for any observable interval. Event Message delivers
  eventual consistency at best. where atomicity across systems is mandatory,
  a distributed transaction protocol or a Saga with compensating actions is
  the correct pattern, and Event Message may still appear as the transport
  inside that Saga but is not itself the consistency mechanism.
- **The team has no operational capacity for a broker or the consumer-side
  idempotency work it demands.** A team of two shipping a monolith with one
  database does not need Kafka to know that an order was placed. an in-process
  observer or a database trigger is proportionate, and the event-message shape
  can be introduced later exactly when a second bounded context appears.

## 5. Structure

- **Producer (Event Source).** The component that detects or decides that
  something has happened and constructs the Event Message. It owns the
  event's schema and version, and it is the only component permitted to
  publish that event type. It never learns which, if any, consumers exist.
- **Event Message.** The message itself, a Message (see the base Message
  pattern entry) whose body describes a fact that already occurred. Carries a
  type identifier, an occurrence timestamp, a unique event identifier for
  deduplication, and a payload that is either thin (reference only) or thick
  (state-carrying), per dimension 8.
- **Channel (typically a Publish-Subscribe Channel or an ordered log).** The
  transport the producer publishes to and consumers subscribe from. Decouples
  producer and consumer in both space (they need not know each other's
  network address) and, on a durable channel, in time (a consumer can join
  later and still see history within a retention window).
- **Consumer (Event Handler, Subscriber, Observer).** Zero, one, or many
  independent components that subscribe to the channel and react to the
  event. Each consumer is responsible for its own idempotency and its own
  error handling. a failing consumer must never be able to affect the
  producer or any other consumer.
- **Dead Letter Channel (usually present).** Where an event that a consumer
  repeatedly fails to process is routed after retries are exhausted, so a
  poison message does not stall the consumer's progress on subsequent events.
- **Event Store or Broker (in durable implementations).** The persistence
  layer underneath the channel, ranging from an in-process observer list
  (no persistence) to a durable, ordered, replayable log such as an Apache
  Kafka topic.

## 6. ASCII structure diagram

```
+-------------------------+
| Producer (Event Source) |
+-------------------------+
           | publishes Event Message(s)
           v
+--------------------------------+
| Channel                        |
| (topic / stream / pub-sub bus) |
+--------------------------------+
           |
           | fan-out (0..N)
     +-----+-----+-----+
     |           |     |
+---------------------+ +---------------------+ +---------------------+
| Consumer A          | | Consumer B          | | Consumer N          |
| (e.g. Billing)      | | (e.g. Inventory)    | | (e.g. Analytics)    |
+---------------------+ +---------------------+ +---------------------+
     |
     | handler fails after retries
     v
+---------------------+
| Dead Letter Channel |
+---------------------+

(Consumer B and Consumer N: handler succeeds)
```

## 7. Dynamics

```
Producer            Channel              Consumer A           Consumer B
  |                    |                      |                    |
  |-- fact occurs ---->|                      |                    |
  | (in producer's     |                      |                    |
  |  own transaction)  |                      |                    |
  |                    |                      |                    |
  |-- publish(Event) ->|                      |                    |
  |   returns          |                      |                    |
  |  (ack from broker,  |                      |                    |
  |   NOT from a         |                      |                    |
  |   consumer)          |                      |                    |
  |<-------------------|                      |                    |
  |                    |-- deliver(Event) --->|                    |
  |                    |-- deliver(Event) ---------------------->  |
  |                    |                      |                    |
  |                    |                      |-- process ---     |
  |                    |                      | (idempotent,      |
  |                    |                      |  checks dedup key) |
  |                    |                      |                    |
  |                    |<-- ack / offset ----|                    |
  |                    |    commit           |                    |
  |                    |                      |                    |-- process ---
  |                    |                      |                    |  (independent
  |                    |                      |                    |   pace, may lag)
  |                    |<---------------- ack / offset commit ----|
```

The dynamics diagram is the load-bearing evidence for the earlier claim that
the producer's `publish` call returns as soon as the channel accepts the
message, never once any consumer has acted. Consumer A and Consumer B process
the same event on entirely independent timelines, and neither one's failure,
slowness, or absence is visible to the producer.

## 8. Implementation variants

- **Thin event (Event Notification style).** The payload carries only an
  identifier, a type, and a timestamp, for example a small JSON body with
  `type`, `orderId`, and `occurredAt` and nothing else. Every consumer
  that needs detail calls back into the producer's API to fetch it. This
  keeps the event small and the producer's data model private, but it
  reintroduces a synchronous dependency on the producer's availability at
  the exact moment the pattern was chosen to remove one, and it means every
  consumer read amplifies into a producer API call.
- **Thick event (Event-Carried State Transfer).** The payload carries the
  full relevant state at the moment of the occurrence, for example the whole
  order object. Consumers build and maintain their own local copy of the
  data they need and never call back to the producer. Martin Fowler's
  writeup names this trade-off directly. it removes the runtime coupling to
  the producer's availability at the cost of duplicating the producer's data
  model into every consumer, with the freshness of that copy bounded by how
  promptly consumers process events
  (https://martinfowler.com/articles/201701-event-driven.html, verified
  2026-08-02). This is the dominant style behind Kafka-based data-mesh and
  CQRS read-model designs.
- **Delta event.** A middle ground carrying only what changed since the last
  known state, for example an order id plus only the fields that changed,
  used when consumers already hold a base copy and full-state payloads would
  be wastefully large, at the cost of requiring every consumer to correctly
  apply deltas in order, which reintroduces an ordering dependency the thick
  or thin styles avoid.
- **Domain Event object versus wire-format event.** Vernon's treatment
  (Vernon 2013, chapter 8) separates the in-process domain event, a plain
  object raised inside an aggregate's method as part of the business logic,
  from the serialized, versioned wire message an outbox or publisher later
  emits. Conflating the two, publishing the raw domain object directly to an
  external channel, couples internal class shape to external consumers and
  breaks the moment a field is renamed for an internal refactor.
- **Event envelope standardization.** Rather than each producer inventing
  its own header shape, the CloudEvents specification standardizes a
  minimal envelope, an id, a source, a type, a time, a content type, and the
  data itself, so consumer tooling and libraries can be shared across
  producers from different teams or vendors (https://cloudevents.io/,
  verified 2026-08-02). This is an implementation variant of the envelope,
  not a different pattern.
- **In-process variant (Observer).** Where producer and consumers share a
  process and a deployment lifecycle, the same semantics, a fact broadcast
  to N interested, decoupled listeners, are implemented with the Observer
  pattern and no broker at all. The move from Observer to a brokered Event
  Message is a scaling refactor, covered in dimension 14, not a change of
  pattern.
- **Idempotency-key variant.** Every implementation intended to survive
  at-least-once delivery attaches a stable, unique event identifier that
  consumers record in their own storage before acting, so a redelivered
  event is recognised and skipped rather than double-applied. This is not
  optional in production systems and is treated in detail in dimension 11.

## 9. Known production uses

- **Apache Kafka** is built around the event as its first-class unit,
  defined in its own documentation as recording "the fact that something
  happened in the world or in your business", and its publish-subscribe
  topic model is the most widely deployed general-purpose implementation of
  the Event Message pattern at scale (https://kafka.apache.org/intro,
  verified 2026-08-02).
- **Amazon EventBridge** is described in AWS's own documentation as "a
  serverless service that uses events to connect application components
  together, making it easier for you to build scalable event-driven
  applications", explicitly built on the "style of building loosely-coupled
  software systems that work together by emitting and responding to events"
  (https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html,
  verified 2026-08-02). Its event bus and rule-matching model is a direct,
  managed implementation of producer, channel, and fan-out consumer.
- **CloudEvents**, a CNCF-graduated specification, graduated status January
  2024, standardizes the Event Message envelope across vendor boundaries so
  that events produced by AWS, Azure, Google Cloud, or an in-house system
  can be consumed by shared tooling without per-vendor adapters
  (https://cloudevents.io/, verified 2026-08-02). Its existence as a
  cross-vendor standard is itself evidence that Event Message, in the thick
  or thin sense described in dimension 8, is common enough in production
  across independently built systems to need a shared wire format.
- **Node.js `EventEmitter`** is the standard-library implementation of the
  in-process variant of this pattern, described in the Node.js API
  documentation as the core of "many of Node.js's built-in modules"
  emitting named events that listeners subscribe to
  (https://nodejs.org/api/events.html, verified 2026-08-02). Node's own HTTP
  server, streams, and process object all publish events through this exact
  mechanism, which is the same producer, channel, fan-out consumer structure
  as the brokered variants, scoped to a single process.

## 10. Consequences

Positive.

- Producers and consumers can be deployed, scaled, and evolved on
  independent schedules, because neither one holds a compile-time or
  runtime reference to the other, only a shared understanding of an event
  type and its schema.
- New functionality is added by subscribing a new consumer to an existing
  channel, with zero code change in the producer, which is a measurable and
  common signal that the coupling goal of the pattern is actually being met.
- A durable, ordered event channel gives the system a natural audit trail
  and, where retained long enough, the ability to reconstruct past state or
  replay history into a new consumer that did not exist when the events
  were first produced.
- Consumer failure is isolated. one consumer's crash, backlog, or bug does
  not propagate to the producer or to sibling consumers, unlike a
  synchronous call chain where a single slow link degrades the whole chain.

Negative.

- The system as a whole loses strong consistency. there is an unavoidable
  window, from milliseconds to much longer under backlog, where the
  producer's state has changed but a given consumer has not yet reacted,
  and any design that assumes otherwise will eventually observe a stale
  read.
- Debugging a fact's downstream effects requires tracing across process and
  service boundaries via correlation identifiers, because a stack trace no
  longer spans producer and consumer. this is a genuine operational cost,
  not merely an inconvenience, and needs the observability discipline in
  dimension 16 to be tractable at all.
- The producer commits, implicitly or explicitly, to a schema contract with
  an unbounded and unknown set of future consumers, which makes changing or
  removing a field a coordination problem rather than a local refactor.
- At-least-once delivery, the realistic default, pushes idempotency work
  onto every single consumer permanently. skipping this work is the most
  common cause of real production incidents attributed to this pattern, and
  it is a cost paid by every consumer team, not once by the producer team.

## 11. Failure modes and misuse

**Symptom.** A downstream service double-charges a customer, double-sends an
email, or double-decrements inventory, intermittently and without an obvious
code defect.
**Cause.** The consumer treats delivery as exactly-once when the underlying
channel only guarantees at-least-once, so a broker retry, a consumer restart
before committing an offset, or a network partition causes the same event to
be processed twice.
**Fix.** The consumer records the event's unique identifier in its own
transactional store before or atomically with the side effect, and checks
for that identifier before acting, so a redelivery is recognised and
discarded, an idempotency-key pattern that must live in the consumer, not the
broker.

**Symptom.** A "cascading rebuild" incident where a large batch of stale or
replayed events triggers an enormous, correlated wave of downstream writes
that overwhelms a consumer's database.
**Cause.** A retention or replay operation, a consumer resubscribing from the
beginning of a topic, or a producer backfilling historical events, delivers
years of history at full channel throughput, with no backpressure or batching
on the consumer side.
**Fix.** Consumers implement explicit backpressure (bounded concurrency, rate
limiting on their own write path) independent of the broker's delivery rate,
and any replay or backfill operation is run through a separate, throttled
channel or a dedicated batch job rather than the live event channel.

**Symptom.** A command silently fails to happen anywhere, with no error
visible to the team that expected it, weeks after a producer change.
**Cause.** An event was renamed, its schema was changed in a
non-backward-compatible way (a field renamed rather than added, a type
narrowed), or a new required field was added, and a consumer written against
the old shape either throws on deserialization and is silently swallowed by
a broad catch, or deserializes successfully with a wrong default and behaves
incorrectly without erroring at all.
**Fix.** Schemas evolve additively only (new optional fields, never a rename
or a narrowing of an existing field), a schema registry or contract test
enforces this at publish time, and consumer deserialization failures are
routed to a Dead Letter Channel and alerted on, never silently swallowed.

**Symptom.** A "God event" whose consumers must each parse a payload
containing dozens of unrelated fields, and where a change to any one field,
even one no particular consumer reads, forces every consumer team to review
the change.
**Cause.** Multiple unrelated occurrences were merged into one event type
over time, usually because it was easier to add a field to an existing event
than to introduce and coordinate a new one, an instance of the general
anti-pattern of coupling-by-convenience.
**Fix.** Split the event type along the actual occurrences it represents, one
event type per distinct fact, even if this means a producer occasionally
raises two events where it previously raised one, and treat a growing field
list as the specific, actionable signal that a split is due.

**Symptom.** Downstream state is subtly wrong in an order-dependent way, for
example a "shipped" status observed before "paid", even though the producer
always emits them in the correct order.
**Cause.** The channel is partitioned or load-balanced across multiple
consumer instances without a partition key tied to the aggregate (the order
ID), so events for the same order land on different consumer instances and
are processed out of order relative to each other.
**Fix.** Partition or key the channel by the aggregate identifier so all
events for one aggregate are delivered, in order, to a single consumer
instance at a time, the standard fix in partitioned-log brokers such as
Kafka, or design consumers to be genuinely order-independent (each event
carries enough state to be applied correctly regardless of arrival order)
when a partition key is not available.

## 12. Trade-off matrix

| Force | Event Message | Command Message | Request-Reply | Shared Database |
|---|---|---|---|---|
| Producer/consumer coupling | Very low, consumers unknown to producer | Low, but sender expects the instruction acted on | High, sender blocks for a specific response | Very high, both sides coupled to a shared schema |
| Number of consumers | Designed for zero to many | Typically exactly one intended executor | Exactly one responder | Any number of readers, uncontrolled |
| Consistency model | Eventual | Eventual, but success or failure of the action matters | Immediate, synchronous | Immediate within one transaction, eventual across services |
| Failure visibility to sender | None by default, must add explicit tracking | Often none by default, same gap unless a reply is required | Immediate, sender sees the failure | Immediate, sender sees the write fail |
| Best for | Fan-out notification, audit trail, decoupled reaction | A specific action that must be carried out once | A caller that cannot proceed without a result | Two components already sharing a transaction boundary |
| Common failure mode | Duplicate processing, schema drift | Lost or duplicated commands, ambiguous ownership of retry | Cascading unavailability under load | Hidden coupling, uncoordinated schema changes |

The comparison against Shared Database is deliberately included even though it
is not a messaging pattern. it is the most common real alternative teams
reach for instead of any message at all, and naming its coupling cost
directly is more useful than comparing Event Message only against its
messaging siblings.

## 13. Related and incompatible patterns

- **Message** is the base pattern Event Message specializes. every structural
  and delivery-guarantee concern that applies to Message (see the Message
  entry) applies here, and Event Message adds only the semantic constraint
  that the payload describes a past occurrence.
- **Command Message** is the sibling pattern for an instruction to be carried
  out rather than a fact reported, and the two are frequently confused
  because both travel over the same physical channel type. The test in
  dimension 1, does removing the tense change the meaning, is the practical
  way to tell them apart during design review.
- **Document Message** carries data with no implied timing or causality
  claim at all, a plain data transfer, whereas Event Message specifically
  asserts that the data reflects the moment of an occurrence. A Document
  Message can be used to carry the payload inside a thick Event Message, but
  the event's envelope (type, timestamp, event id) is what makes it an
  Event Message.
- **Publish-Subscribe Channel** is the channel topology Event Message almost
  always runs over, because fan-out to an unknown number of consumers is
  exactly what a topic or bus provides. Event Message over a
  Point-to-Point Channel is unusual and generally signals the design should
  have been a Command Message instead.
- **Dead Letter Channel** composes directly underneath any real Event
  Message implementation, as the destination for events a consumer cannot
  successfully process after retries, covered structurally in dimension 5.
- **Saga** frequently uses a sequence of Event Messages as its coordination
  mechanism across services, with each step's completion event triggering
  the next step or a compensating action on failure. Saga is the pattern
  that supplies the missing cross-service consistency Event Message alone
  cannot provide, per the non-applicability note in dimension 4.
- **Event Sourcing** is a distinct, heavier architectural pattern that uses
  a stream of Event Messages as the sole source of truth for an aggregate's
  state, reconstructed by replaying events, rather than using events purely
  as a notification mechanism alongside a conventional data store. Every
  Event-Sourced system uses Event Message, but most systems that use Event
  Message are not Event Sourced.
- **Incompatible with strict two-phase commit across services.** A design
  that requires a producer to know, before committing its own local
  transaction, whether every consumer will succeed, cannot be built on Event
  Message without reintroducing the exact synchronous coupling the pattern
  removes. this is the direct, non-composable case named in dimension 4.

## 14. Refactoring path in and out

Introducing Event Message into code that currently makes direct calls is a
sequence of small, reversible steps, not a rewrite.

1. **Name the fact.** Identify the exact moment in the existing code where the
   occurrence becomes true (after the order row commits, not before), and
   give it a specific past-tense name, `OrderPlaced`, not a generic
   `OrderUpdate`.
2. **Extract a callback list in-process first.** Before introducing any
   broker, replace the direct calls at that point with a simple in-process
   Observer, an internal list of handlers invoked synchronously in the same
   transaction or immediately after it commits. This proves the fan-out
   shape and the event's schema are right while the operational cost stays
   at zero.
3. **Make handlers independently failable.** Wrap each handler invocation so
   one handler's exception cannot prevent the others from running or corrupt
   the producer's own transaction, the first real decoupling step and often
   the one that surfaces hidden ordering assumptions.
4. **Move to an asynchronous, durable channel** only once there is a genuine
   need. a second process needs the event, or the number of handlers has
   grown enough that synchronous fan-out inside the request path is now the
   latency bottleneck. Introduce the broker or bus, publish the same,
   already-proven event shape, and migrate handlers to subscribers one at a
   time, keeping the in-process path live behind a flag until every consumer
   has moved.
5. **Add idempotency and dead-lettering** at the same time the durable
   channel is introduced, not after the first incident. at-least-once
   delivery semantics are present from the first real broker, even if no
   redelivery has been observed yet.

Removing Event Message, when a system has over-applied it, follows the
reverse path and is worth doing when a "God event" (dimension 11) or a chain
of events reacting to events has made the actual sequence of what happens
impossible to read from any one place.

1. **Trace the actual dependency.** Follow one occurrence through every
   consumer it triggers, including any consumer that itself emits further
   events, until the full causal chain for a single business operation is on
   one diagram. If this chain has more than three or four hops for what is
   conceptually one operation, it is a strong signal for consolidation.
2. **Collapse genuinely coupled steps.** Where two consumers are always
   present together, always in the same order, and neither is meaningfully
   independent, replace the event hop between them with a direct call or a
   single combined handler, and keep the event only at the boundary where
   real independence exists (a different team, a different deployment, a
   genuinely optional reaction).
3. **Keep the event where fan-out is real.** Do not remove Event Message
   from the boundaries where multiple independent consumers genuinely exist.
   the goal of this refactor is removing accidental complexity, not
   eliminating legitimate decoupling.

## 15. Testing and verification

What becomes easy. consumers can be unit tested entirely in isolation by
constructing a well-formed event object and asserting on the handler's
behaviour, with no need to stand up the producer, the channel, or any other
consumer. Producers can be unit tested by asserting that the correct event
type and payload were handed to the channel abstraction, using a fake or
in-memory implementation of the channel interface, without needing a real
broker running in the test suite.

What becomes harder. end-to-end correctness, specifically that a real
occurrence in the producer actually results in the intended, eventual effect
in a real consumer running against a real broker, cannot be verified by unit
tests alone and requires a genuine integration or contract test. Consumer
contract tests, verifying a consumer correctly handles the current schema,
including fields it does not use, and rejects or tolerates a schema it does
not recognise, are the standard technique, often implemented with a shared
schema registry or a consumer-driven contract tool, and they are the specific
test class that catches the schema-drift failure mode from dimension 11
before it reaches production.

Idempotency itself is directly testable and should be. a test that delivers
the identical event twice to a consumer and asserts the observable side
effect (a row written, a charge made) happened exactly once, is a cheap,
high-value regression test against the most common real incident class this
pattern produces, and it belongs in every consumer's test suite, not only in
an integration environment.

Ordering-sensitive consumers need a specific test that delivers events for
the same aggregate out of order and asserts the consumer either produces the
correct result regardless of order, or explicitly detects and rejects the
out-of-order case, rather than silently producing a wrong result, which is
the concrete verification for the ordering failure mode in dimension 11.

## 16. Observability signals

A healthy Event Message pipeline shows a small, stable, roughly flat gap
between the time an event is published and the time each subscribed consumer
has processed it, commonly called consumer lag on log-based brokers such as
Kafka. Consumer lag that grows monotonically over a sustained window, rather
than oscillating around a steady value, is the primary early signal that a
consumer cannot keep pace with the producer and will eventually either fall
critically behind, hit a retention limit and lose events, or exhaust its own
resources under backlog.

Per-event-type publish and consume counters, broken down by consumer group,
make silent producer changes visible. a sudden drop in published count for
an event type usually means a producer deploy broke event emission, and a
sudden drop in consumed count for one consumer group while others stay
steady usually means that specific consumer, not the channel, has a problem.

Dead Letter Channel depth and arrival rate is the single most important
alert to have configured, because a growing dead-letter queue is a direct,
unambiguous signal of the schema-drift or poison-message failure modes from
dimension 11, and it is a signal that is otherwise invisible from the
happy-path metrics above, which will look entirely normal while a subset of
events silently fail.

Each event should carry, and each consumer's logs should surface, a
correlation or trace identifier that ties the original triggering request
through the producer's publish and every consumer's eventual processing, so
that the cross-process trace lost in dimension 10's negative consequences
can be reconstructed after the fact from logs or a distributed tracing
system rather than only inferred.

Duplicate-delivery rate, measured as the proportion of events a consumer's
idempotency check identifies as already-seen, is worth tracking on its own.
a rate near zero most of the time with occasional spikes correlated to
broker or consumer restarts is expected and healthy. a rate that is
persistently high indicates a producer retry loop or a broker
misconfiguration and is worth investigating even though the idempotency
layer is, by design, hiding its user-visible impact.

## 17. Security and privacy implications

An Event Message, once published to a broadly subscribable channel, is
readable by every current and future subscriber of that channel, which makes
including personally identifiable information or other sensitive data in a
thick, state-carrying event payload (dimension 8) a direct data-exposure
decision, not an implementation detail. A field added to an event for one
consumer's convenience is available to every consumer, present and future,
and to anyone who gains read access to the channel or its retained log,
including in a durable, long-retention broker, anyone with access to years of
historical data at once.

Because Event Message decouples the producer from knowledge of its
consumers, standard request-scoped authorization checks, does this caller
have permission to see this data, do not naturally apply. a consumer that
should only see a subset of an aggregate's fields, or should only see events
for aggregates it owns, needs that filtering enforced either by the channel
(topic-level or field-level access control) or by the consumer's own
authorization logic. relying on "nobody else has subscribed yet" as an
access control is not a control at all, since a new subscriber can always be
added later with the same schema visibility.

Event payloads containing identifiers that let a reader correlate otherwise
separate pieces of data, an email address alongside an internal user
identifier alongside a purchase history, effectively create a new
data-linkage surface at the moment they are published together, independent
of whether either field alone was considered sensitive. this is a genuine
privacy design consideration and is best handled by minimizing payload
fields to what consumers actually need, per the discipline against "God
events" in dimension 11, rather than by relying on downstream consumers to
discard fields they do not use.

Retention of a durable event log is itself a data-retention and, in
jurisdictions with a right to erasure, a compliance concern, because an
event describing a past fact that included a person's data cannot be
retroactively edited in an append-only, replayable log the way a row in a
mutable database can. systems intending to comply with a right-to-erasure
requirement generally need either a short retention window, a
tombstone-and-purge mechanism designed in from the start, or a design that
keeps personal data out of the event payload entirely and references it by
identifier from a separate, erasable store.

## 18. References

1. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
   Message Construction chapter, Event Message.
2. Enterprise Integration Patterns website, Event Message pattern page.
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/EventMessage.html,
   verified 2026-08-02.
3. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003.
4. Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
   chapter 8, "Domain Events".
5. Apache Kafka documentation, Introduction, definition of an event.
   https://kafka.apache.org/intro, verified 2026-08-02.
6. CloudEvents specification and CNCF project page.
   https://cloudevents.io/, verified 2026-08-02.
7. Amazon Web Services, "What Is Amazon EventBridge?", AWS documentation.
   https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html,
   verified 2026-08-02.
8. Node.js documentation, Events module, `EventEmitter`.
   https://nodejs.org/api/events.html, verified 2026-08-02.
9. Martin Fowler, "What do you mean by Event-Driven", martinfowler.com,
   2017. https://martinfowler.com/articles/201701-event-driven.html,
   verified 2026-08-02.

## Code examples

### TypeScript. Typed in-process event bus with a thick, state-carrying event

```typescript
type OrderPlaced = {
  type: "OrderPlaced";
  eventId: string;
  occurredAt: string;
  orderId: string;
  customerId: string;
  totalCents: number;
};

type DomainEvent = OrderPlaced;

class EventBus {
  private handlers = new Map<string, Array<(e: DomainEvent) => void>>();
  private seen = new Set<string>();

  subscribe(type: DomainEvent["type"], handler: (e: DomainEvent) => void): void {
    const list = this.handlers.get(type) ?? [];
    list.push(handler);
    this.handlers.set(type, list);
  }

  publish(event: DomainEvent): void {
    const list = this.handlers.get(event.type) ?? [];
    for (const handler of list) {
      try {
        handler(event);
      } catch (err) {
        console.error(`handler failed for ${event.type} ${event.eventId}`, err);
      }
    }
  }

  markAndCheck(consumerName: string, eventId: string): boolean {
    const key = `${consumerName}:${eventId}`;
    if (this.seen.has(key)) return false;
    this.seen.add(key);
    return true;
  }
}

const bus = new EventBus();

bus.subscribe("OrderPlaced", (e) => {
  const evt = e as OrderPlaced;
  if (!bus.markAndCheck("billing", evt.eventId)) {
    console.log("billing: duplicate, skipping", evt.eventId);
    return;
  }
  console.log(`billing: charging ${evt.totalCents} cents for order ${evt.orderId}`);
});

bus.subscribe("OrderPlaced", (e) => {
  const evt = e as OrderPlaced;
  if (!bus.markAndCheck("inventory", evt.eventId)) return;
  console.log(`inventory: reserving stock for order ${evt.orderId}`);
});

bus.publish({
  type: "OrderPlaced",
  eventId: "evt-001",
  occurredAt: new Date().toISOString(),
  orderId: "o-123",
  customerId: "c-42",
  totalCents: 4599,
});

bus.publish({
  type: "OrderPlaced",
  eventId: "evt-001",
  occurredAt: new Date().toISOString(),
  orderId: "o-123",
  customerId: "c-42",
  totalCents: 4599,
});
```

### Python. Producer/consumer with an ordered, keyed queue and dead-lettering

```python
import time
import uuid
from collections import deque
from dataclasses import dataclass, field


@dataclass
class OrderPlaced:
    order_id: str
    total_cents: int
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: float = field(default_factory=time.time)


class Channel:
    def __init__(self):
        self._queue = deque()
        self._dead_letters = []

    def publish(self, event: OrderPlaced) -> None:
        self._queue.append(event)

    def drain(self, handler, max_attempts: int = 3) -> None:
        while self._queue:
            event = self._queue.popleft()
            for attempt in range(1, max_attempts + 1):
                try:
                    handler(event)
                    break
                except Exception as exc:
                    if attempt == max_attempts:
                        self._dead_letters.append((event, str(exc)))
                    else:
                        continue

    @property
    def dead_letters(self):
        return list(self._dead_letters)


class InventoryConsumer:
    def __init__(self):
        self._processed_ids = set()

    def handle(self, event: OrderPlaced) -> None:
        if event.event_id in self._processed_ids:
            print(f"inventory: duplicate {event.event_id}, skipping")
            return
        if event.total_cents <= 0:
            raise ValueError(f"invalid total_cents for order {event.order_id}")
        self._processed_ids.add(event.event_id)
        print(f"inventory: reserved stock for order {event.order_id}")


def main() -> None:
    channel = Channel()
    inventory = InventoryConsumer()

    channel.publish(OrderPlaced(order_id="o-1", total_cents=1999))
    channel.publish(OrderPlaced(order_id="o-2", total_cents=-1))
    channel.drain(inventory.handle)

    assert len(channel.dead_letters) == 1
    print(f"dead letters: {len(channel.dead_letters)}")


if __name__ == "__main__":
    main()
```

### Go. Fan-out over a channel with independent goroutine consumers

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type OrderPlaced struct {
	EventID    string
	OrderID    string
	TotalCents int
	OccurredAt time.Time
}

type Bus struct {
	subs []chan OrderPlaced
	mu   sync.Mutex
}

func (b *Bus) Subscribe() <-chan OrderPlaced {
	b.mu.Lock()
	defer b.mu.Unlock()
	ch := make(chan OrderPlaced, 16)
	b.subs = append(b.subs, ch)
	return ch
}

func (b *Bus) Publish(e OrderPlaced) {
	b.mu.Lock()
	defer b.mu.Unlock()
	for _, ch := range b.subs {
		ch <- e
	}
}

func (b *Bus) Close() {
	b.mu.Lock()
	defer b.mu.Unlock()
	for _, ch := range b.subs {
		close(ch)
	}
}

func consume(name string, ch <-chan OrderPlaced, wg *sync.WaitGroup) {
	defer wg.Done()
	seen := make(map[string]bool)
	for e := range ch {
		if seen[e.EventID] {
			fmt.Printf("%s: duplicate %s, skipping\n", name, e.EventID)
			continue
		}
		seen[e.EventID] = true
		fmt.Printf("%s: processed order %s (%d cents)\n", name, e.OrderID, e.TotalCents)
	}
}

func main() {
	bus := &Bus{}
	billing := bus.Subscribe()
	inventory := bus.Subscribe()

	var wg sync.WaitGroup
	wg.Add(2)
	go consume("billing", billing, &wg)
	go consume("inventory", inventory, &wg)

	bus.Publish(OrderPlaced{
		EventID:    "evt-1",
		OrderID:    "o-123",
		TotalCents: 4599,
		OccurredAt: time.Now(),
	})
	bus.Close()
	wg.Wait()
}
```

I compiled and ran all three samples locally. TypeScript via `npx tsc` against
a minimal `tsconfig` targeting `es2020` with the DOM and ES2020 libraries (no
framework types needed since the sample uses only `console` and `Date`), then
executed the emitted JavaScript with `node`. Python via `python3`. Go via
`go run`. All three produced the expected fan-out and duplicate-skip output
described in the dynamics section. Java, Rust, Swift, C#, and Kotlin samples
are omitted. the pattern's structure, a fan-out channel plus independent
consumers with idempotency bookkeeping, is not meaningfully more idiomatic in
those languages for the purpose of this entry, and three languages already
cover the closure-based, dataclass-based, and channel-native idioms that
differ most from each other.
