---
name: Message Bus
slug: message-bus
family: 07-integration
category: Integration
aliases: [Enterprise Service Bus, ESB, Event Bus, Command Bus (specialization), Bus Architecture]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [publish-subscribe-channel, message-channel, message-router, message-broker, mediator, observer, dead-letter-channel]
incompatible_with: []
verified: 2026-08-02
---

# Message Bus

## 1. Name, aliases, and lineage

The canonical name is Message Bus. It is catalogued as an integration pattern in
Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003. The pattern
page for it states the definition directly. a Message Bus is "a combination of a
common data model, a common command set, and a messaging infrastructure to
allow different systems to communicate through a shared set of interfaces"
(https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageBus.html,
verified 2026-08-02). The same page frames the driving question as "what is an
architecture that enables separate applications to work together, but in a
decoupled fashion such that applications can be easily added or removed without
affecting the others."

The alias Enterprise Service Bus, almost always shortened to ESB, is the
commercial and product name the same idea took on through the 2000s, sold by
vendors such as IBM, TIBCO, and MuleSoft as a piece of centralized middleware
that combines the bus abstraction with routing, transformation, orchestration,
and often a rules engine. The GoF-era Message Bus pattern and the ESB product
category share the connectivity idea but diverge sharply on where intelligence
lives, which is discussed in dimension 11.

Event Bus is the alias used inside a single process or a single service
boundary, where the bus is an in-memory dispatcher rather than networked
middleware. The structural shape, a set of named channels with many publishers
and many subscribers decoupled by a shared dispatch point, is identical to the
distributed Message Bus, just collapsed to one address space. This is the shape
built and run in dimension 8's code samples.

Command Bus is a specialization that restricts the bus to point-to-point
delivery of one command to exactly one handler, in contrast with the
one-to-many delivery a Message Bus and an Event Bus both default to. A Command
Bus is closer in shape to the Mediator pattern with a routing table, and it is
listed here as related rather than as an alias because the cardinality
guarantee is a different contract, not a naming variant.

Martin Fowler and James Lewis, in their 2014 article on microservices, use the
phrase "smart endpoints and dumb pipes" to describe the architectural stance
that later reacted against the ESB reading of this pattern, and they quote Jim
Webber's description of an ESB as an "Erroneous Spaghetti Box"
(https://martinfowler.com/articles/microservices.html, verified 2026-08-02).
That reaction is a central part of this pattern's history and is treated fully
in the consequences and failure modes dimensions below, not glossed over here.

## 2. Problem and context

A system starts with two applications that need to exchange data, and a direct
point-to-point integration, a script that reads from one database and writes to
another, or a synchronous API call, solves it well enough. The problem this
pattern addresses appears once that count grows past two or three. Each new
application that needs to participate multiplies the number of point-to-point
connections that must be built, tested, and kept working, because a fully
connected mesh of N applications needs on the order of N times N minus one
divided by two direct links. Every new participant is not one integration, it
is potentially every existing participant re-integrated with the new one.

The context in which the problem is felt most sharply is an organization with
many independently owned systems, often on different platforms, different data
formats, and different release schedules, where a business event in one system
is relevant to several others. An order placed in an e-commerce system needs to
trigger billing, trigger inventory reservation, trigger a shipping label
request, and trigger a fraud check, and none of those four downstream systems
should need to know about the other three, and the order system should not need
to know how many downstream systems exist or hold a network address for each
one.

The pattern addresses this by introducing a single logical channel that every
participant connects to exactly once. A producer publishes a message onto the
bus addressed to a topic or a common data model, and any number of consumers
that have registered interest in that topic receive a copy, without the
producer or the consumers holding a direct reference to each other. The N
squared connection problem collapses to N connections into one shared
infrastructure. This is the same underlying shape as the Observer pattern from
the Gang of Four catalog, but stretched across process and network boundaries
and formalized with a canonical message format, which is why the two patterns
are related rather than identical.

## 3. Forces

Coupling versus discoverability. The bus reduces coupling between
producer and consumer to almost nothing, they never share a network address, a
deployment schedule, or knowledge of each other's existence. The cost is that
the set of consumers for any given message becomes invisible from the
producer's code, and tracing "who reacts to this event" requires searching bus
configuration or subscription registries rather than reading a call graph.

Latency versus decoupling. A direct call is one hop and its latency is
bounded by the receiving service alone. A bus adds at minimum one serialize,
one network hop to the broker, one persist and acknowledge if the delivery
guarantee requires durability, and one network hop out to each subscriber.
Decoupling in time and in space is bought with latency, and for a use case that
needs a synchronous answer within a fixed budget, this force alone often rules
the pattern out.

Consistency versus availability. A bus with at-least-once delivery and no
transactional outbox can deliver the same event twice, or can deliver an event
describing a database write that was later rolled back, if the write and the
publish are not part of one atomic operation. Consumers therefore need to be
idempotent or need the producer to adopt a pattern such as the transactional
outbox to keep publish and commit atomic. The bus itself does not solve this,
it only creates the shared surface on which the problem becomes visible to
every consumer at once instead of to one.

Operability versus centralization. A single bus is one thing to monitor,
one place to see throughput, and one place to enforce a schema. It is also one
thing whose outage or slow-down affects every participant at once, and one
piece of infrastructure that a platform team now owns on behalf of every
consuming team, with everything that implies about on-call rotation, capacity
planning, and the blast radius of a bad configuration change.

Cognitive load versus flexibility. Adding a new consumer to an existing
event costs nothing on the producer side, which is the entire point of the
pattern. The cost that force sacrifices is that a reader of the producer's code
can no longer see the full set of consequences of an action by reading the
call stack, they have to know the bus exists and go find the subscriber list,
which is a genuine loss of local reasoning that shows up repeatedly in the
failure modes dimension below as the "who is listening" problem.

Cost versus reach. Running a shared broker, whether that is Kafka,
RabbitMQ, or a managed cloud service, is infrastructure with its own cost,
against the alternative of N direct HTTP calls that cost nothing extra beyond
the compute already running. For a system with three participants the direct
calls are cheaper in every dimension. For a system with thirty participants the
bus amortizes across all of them and the direct-call mesh becomes the more
expensive option, in engineering time if not in literal infrastructure spend.

The pattern favors decoupling, discoverability at the infrastructure level, and
horizontal extensibility. It sacrifices call-graph traceability, adds latency
and at least one new failure domain, and requires the organization to accept a
shared piece of centralized infrastructure with real operational weight.

## 4. Applicability and non-applicability

Reach for a Message Bus when the following hold.

- More than a handful of independently deployed systems need to react to the
  same business events, and the set of reactors is expected to grow over time
  without the event producer needing to change.
- The producer of an event genuinely should not know or care who consumes it,
  because the reactions are a separate concern owned by separate teams, for
  example billing reacting to an order placed event that the order service
  owns.
- Eventual consistency between producer and consumer is acceptable for the
  business process in question, because the bus introduces asynchronous
  delivery by default.
- The organization already has, or is willing to operate, shared messaging
  infrastructure, and that infrastructure's failure modes and on-call burden
  are an accepted cost against the alternative of N direct integrations.
- The message payloads for a given topic have or can be given a stable,
  versioned schema that many independent consumers can agree to evolve
  against, because a bus with no schema discipline degrades into the failure
  mode described in dimension 11 as "the undocumented contract."

Do NOT reach for a Message Bus in the following situations, and use the
alternative named instead.

- A caller needs an answer within the current request to return a response
  to a user. Use a direct synchronous call, RPC, or a request-response
  pattern instead of asynchronous fan-out. Forcing a request-response
  interaction through a publish-subscribe bus adds latency and a correlation
  problem the direct call never had.
- Exactly two systems talk to each other and no third party is realistically
  expected to join. A point-to-point integration or a direct API call is
  simpler to build, simpler to trace, and simpler to secure than standing up
  or extending shared bus infrastructure for a pair that will likely stay a
  pair. See Point-to-Point Channel as the named alternative.
- The team has no operational capacity to run or pay for a message broker,
  and the organization has no existing one. Introducing a bus purely to gain
  its decoupling benefits, without the operational maturity to run it, trades
  a well-understood coupling problem for a poorly understood infrastructure
  problem, which is a worse trade for a small team.
- The interaction is a single command that must be handled by exactly one
  owner, never zero, never more than one. A Message Bus's natural cardinality
  is publish-subscribe with zero or many consumers. Forcing single-owner
  command semantics onto a fan-out bus needs extra machinery, a claim check, a
  competing-consumers queue with one logical group, that a dedicated
  Point-to-Point Channel or Command Bus already models directly and honestly.
- The data crossing the boundary needs strict, low-latency transactional
  consistency with the source of truth, for example a funds transfer that
  must be atomically consistent across two ledgers in the same operation. A
  bus is fundamentally an asynchronous, eventually-consistent mechanism, and
  layering distributed transaction coordination on top of it to force strong
  consistency is fighting the pattern rather than using it.
- A single team owns both ends of the integration and the two ends deploy
  together. The whole benefit of the bus is independent evolution across
  organizational boundaries. When there is no boundary, the extra
  infrastructure and indirection buy nothing and only add operational surface.

## 5. Structure

- Producer. The application or service that has knowledge of a business
  event or command and publishes a message describing it. It knows the shared
  data model and command set of the bus, and nothing about which consumers, if
  any, exist.
- Message. The unit of communication, carrying a payload conforming to the
  bus's common data model, plus routing metadata such as a topic or message
  type, a correlation identifier, and often a schema version.
- Bus, the shared channel or set of channels. The infrastructure that
  accepts a published message from any producer and makes it available to
  every registered consumer. In the canonical pattern this is logically a
  single channel. In real deployments it is usually implemented as a set of
  named topics, each behaving as its own publish-subscribe channel, unified
  under one broker, one schema registry, and one operational surface.
- Consumer, the subscriber. An application or service that registers interest
  in one or more topics or message types and receives a copy of every matching
  message. Consumers are independent of each other. The failure or slowness of
  one consumer does not, in a correctly built bus, block delivery to the
  others.
- Common data model. The agreed-upon canonical representation for the
  entities the bus carries, for example a canonical Order or Customer shape
  that every participant maps into and out of at the boundary. This is what
  distinguishes a true Message Bus from a bare set of unrelated
  Publish-Subscribe Channels, per the Hohpe and Woolf definition cited in
  dimension 1. the shared model plus the shared command set plus the
  infrastructure together are what make it "a bus" rather than a pile of
  independent queues.
- Adapter at the edge, optional but common. A translation layer at each
  participant's boundary that converts between that system's native
  representation and the bus's common data model, so no participant's internal
  types leak onto the bus and no bus type leaks into a participant's domain
  model. This role corresponds to the Channel Adapter and Messaging Bridge
  patterns catalogued alongside this one.

## 6. ASCII structure diagram

```
                          +-----------------------+
                          |     Message Bus        |
                          |  (common data model,   |
                          |   command set, infra)  |
                          |                         |
        publish           |  +-------------------+  |     deliver
   Order Service --------->  | topic  order.*    |  ---------> Billing Service
                          |  +-------------------+  |
                          |                         |     deliver
                          |  +-------------------+  ---------> Inventory Service
                          |  | topic  payment.*  |  |
   Payment Service ------->  +-------------------+  |     deliver
        publish           |                         ---------> Fraud Check Service
                          |  +-------------------+  |
                          |  | topic  shipment.* |  ---------> Shipping Service
                          |  +-------------------+  |     deliver
                          +-----------------------+
                          | Channel Adapter layer  |
                          | (per-system format     |
                          |  translation, at edge)  |
                          +-----------------------+

  Producers know only. the bus address, the common data model.
  Consumers know only. the topic(s) they subscribe to.
  Neither side holds a reference to the other.
```

## 7. Dynamics

```
Order Service        Message Bus            Billing Sub.    Inventory Sub.
     |                    |                       |               |
     | 1. build Order     |                       |               |
     |    Placed event    |                       |               |
     |    (common model)  |                       |               |
     |------------------->|                       |               |
     |   publish(topic=    |                       |               |
     |    "order.placed") |                       |               |
     |                    | 2. persist + ack       |               |
     |<-------------------|    to producer         |               |
     |   ack (durable)    |                       |               |
     |                    | 3. fan out copy 1      |               |
     |                    |----------------------->|               |
     |                    |   handle(msg)          |               |
     |                    |                        | 4. process,   |
     |                    |                        |    ack/commit |
     |                    |<-----------------------|               |
     |                    |   offset committed      |               |
     |                    |                        |               |
     |                    | 5. fan out copy 2       |               |
     |                    |------------------------------------->  |
     |                    |   handle(msg)                          |
     |                    |                                        | 6. process,
     |                    |                                        |    ack/commit
     |                    |<---------------------------------------|
     |                    |   offset committed                     |

Notes.
- Steps 3 and 5 are independent and, on a real broker, concurrent. One
  subscriber's slowness or crash does not delay the other's delivery.
- Step 2's ack to the producer happens once the bus has durably accepted the
  message, before any subscriber has necessarily processed it. This is what
  "decoupled in time" means concretely.
- If Billing's handler in step 4 throws, a correctly configured bus retries
  delivery to Billing alone, per its own retry and dead-letter policy, and
  Inventory in step 5 to 6 is entirely unaffected.
```

## 8. Implementation variants

In-process event bus. A single dispatcher object inside one application
address space, holding an in-memory map from topic or event type to a list of
handler functions, with no network hop and no persistence. This is the shape
of dimension 6's code samples below, and it is the correct starting point when
the goal is decoupling modules inside one deployable, not decoupling separate
deployables. .NET's `MediatR` notification pipeline and simple DOM-style
`EventTarget` dispatch inside a browser are both instances of this variant.

Broker-backed distributed bus, topic-partitioned log. Apache Kafka
implements the bus as an append-only, partitioned, replicated commit log per
topic, where consumers track their own read offset rather than the broker
tracking delivery per consumer. The official introduction describes Kafka as
combining publish and subscribe, durable storage of event streams "for as long
as you want," and stream processing in one platform
(https://kafka.apache.org/intro, verified 2026-08-02). This variant favors very
high throughput, replay from an arbitrary historical offset, and
consumer-group-based competing-consumers scaling, at the cost of a heavier
operational footprint than a simple queue-based broker.

Broker-backed distributed bus, exchange and queue model. RabbitMQ and other
AMQP-based brokers separate the routing concern, an exchange that a producer
publishes to, from the storage concern, a queue that a consumer reads from,
joined by a binding rule. RabbitMQ's own tutorials describe this exchange,
queue, and binding vocabulary directly in terms of the AMQP 0-9-1 protocol
(https://www.rabbitmq.com/tutorials, verified 2026-08-02). This variant favors
flexible routing topologies, per-message acknowledgment and redelivery
semantics, and lower operational weight than a log-based broker, at the cost of
weaker built-in support for long-term replay compared with Kafka's retained
log.

Managed cloud fan-out. Amazon SNS paired with Amazon SQS implements the
bus as a managed topic that fans a published notification out to any number of
subscribed queues, each queue then delivering to its own consumer at its own
pace with its own durability guarantees. AWS's own SNS product page advertises
the capability to "capture and fan out events from over 60 AWS services"
(https://aws.amazon.com/sns/, verified 2026-08-02). Azure Service Bus offers the
equivalent shape natively inside one service, where a topic can have many
subscriptions, each subscription behaving as an independent virtual queue with
its own filter, and Microsoft's own documentation states this is a "one-to-many
form of communication in a publish and subscribe pattern... useful for scaling
to large numbers of recipients"
(https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-queues-topics-subscriptions,
verified 2026-08-02). This variant favors near-zero operational burden in
exchange for vendor lock-in and, for SNS plus SQS, two managed services to
reason about instead of one.

Lightweight subject-based bus. NATS models the bus as hierarchical subjects
with no durable storage by default, described in its own documentation as "a
simple, secure and high-performance open source messaging system for cloud
native applications, IoT messaging, and microservices architectures"
(https://docs.nats.io/nats-concepts/overview, verified 2026-08-02). This variant
favors extremely low latency and a minimal operational footprint, at the cost
of at-most-once delivery by default unless the JetStream persistence layer is
explicitly enabled on top of it.

Enterprise Service Bus product. Commercial and open-source ESB products
such as MuleSoft, IBM App Connect, and Apache ServiceMix bundle the bus
transport together with a canonical data model editor, a visual routing and
transformation engine, protocol adapters for legacy systems, and often an
orchestration or business-rules layer, all centrally deployed and centrally
owned. This variant maximizes reuse of integration logic across many
participants at the cost of concentrating business logic into shared
middleware, which is precisely the concentration Fowler and Lewis critique in
dimension 1 and dimension 11.

## 9. Known production uses

- LinkedIn built and open-sourced Apache Kafka specifically to serve as the
  company's central nervous system for activity and operational data,
  replacing a tangle of point-to-point pipelines with one durable log-based
  bus that every consuming team, from search indexing to monitoring to the
  data warehouse, reads from independently. This origin and role are
  described in Kafka's own project documentation, which frames the platform
  around exactly the publish, subscribe, and durable-storage combination this
  pattern requires (https://kafka.apache.org/intro, verified 2026-08-02).
- Amazon Web Services runs Amazon SNS as a managed publish-subscribe bus
  that customers use to fan a single published notification out to many
  independent subscribers, including SQS queues, Lambda functions, and HTTP
  endpoints, described on AWS's own product page as capturing and fanning out
  events across services (https://aws.amazon.com/sns/, verified 2026-08-02).
- Microsoft Azure Service Bus provides topics and subscriptions as a
  first-class managed implementation of this pattern inside Azure, explicitly
  documented as a one-to-many publish and subscribe communication pattern used
  for event broadcasting and fan-out at scale
  (https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-queues-topics-subscriptions,
  verified 2026-08-02).
- RabbitMQ, built on the AMQP protocol, is used as the transport-level
  message bus underneath a very large share of the open-source and commercial
  .NET and Java messaging ecosystem, with its own tutorials documenting the
  exchange, queue, and binding model that gives producers and consumers a
  shared bus abstraction without direct knowledge of each other
  (https://www.rabbitmq.com/tutorials, verified 2026-08-02).

## 10. Consequences

Positive.

- New consumers can be added to an existing event stream with zero change to
  the producer, which is the central value proposition and the reason the
  pattern exists at all.
- The number of point-to-point integrations an organization must build and
  maintain collapses from a number that grows quadratically with participant
  count to one that grows linearly.
- Producers and consumers can be developed, deployed, and scaled on
  independent schedules, because the bus decouples them in both space, no
  direct network reference, and time, the producer does not block waiting for
  every consumer to process the message.
- A slow or failing consumer's problems are, when the bus and its retry and
  dead-letter policy are configured correctly, isolated to that one consumer
  and do not propagate back to the producer or to sibling consumers.
- The bus becomes a single, real-time record of what is happening across an
  organization's systems, which is genuinely valuable for observability,
  auditing, and building new capabilities such as a data warehouse or an
  analytics pipeline that simply subscribes to the existing stream.

Negative.

- Every hop through the bus adds latency compared to a direct call, and for a
  chain of several bus-mediated steps that latency compounds, which rules the
  pattern out for any interaction that needs a synchronous answer within a
  tight budget.
- The set of consumers for a given message is invisible from the producer's
  source code, so understanding the full consequence of publishing an event
  requires searching the bus's subscription configuration or a service
  registry rather than reading a call graph, which is a real and repeatedly
  reported cost to onboarding and debugging.
- The bus itself becomes a new, shared point of failure and a new operational
  responsibility. An outage, a misconfiguration, or a capacity problem in the
  bus can degrade every participant at once, in contrast to a point-to-point
  failure that is contained to the two systems involved.
- Delivery guarantees are rarely free of edge cases. At-least-once delivery
  means consumers must be idempotent, and achieving exactly the producer's
  committed state and the published event atomically usually requires an
  additional pattern such as a transactional outbox, which the bus itself does
  not provide.
- When an organization lets the bus accumulate routing rules, data
  transformation, and business logic, rather than keeping the bus a dumb pipe
  and pushing that logic into the endpoints, the bus becomes a single,
  hard-to-test, hard-to-deploy chokepoint for the entire organization's
  integration logic, which is the specific failure the ESB backlash targeted
  and which is documented in the next dimension.

## 11. Failure modes and misuse

The undocumented contract. Symptom. A producer changes a field's meaning or
removes a field it believed nothing used, and three unrelated services break in
production with no warning, because nobody who owned the producer knew those
three services subscribed. Cause. The bus was adopted without a schema
registry, a contract testing discipline, or even a lightweight subscriber
directory, so the "shared data model" from the pattern's definition existed
only informally, in people's heads. Fix. Enforce a schema registry with
backward-compatibility checks on every published change, per topic, and treat
a breaking schema change as a new topic version rather than a silent mutation
of the old one.

The smart bus, dumb endpoints inversion. Symptom. Adding a new field of
business logic, a new routing rule, or a new transformation requires editing a
central integration platform maintained by a separate team, and every team
that wants a change queues behind that team's backlog, turning what should be
independent deployments into a shared, contended bottleneck. Cause. Business
logic, routing decisions, and data transformation that properly belong to a
domain service were pushed into the bus or ESB layer instead, following the
pattern that Fowler and Lewis describe as SOA implementations that put
"significant smarts into the communication mechanism itself"
(https://martinfowler.com/articles/microservices.html, verified 2026-08-02).
Fix. Keep the bus limited to transport, routing by topic, and format
translation at the edge. Move any conditional business logic, orchestration
decision, or transformation that encodes a business rule into the owning
service, following the "smart endpoints, dumb pipes" principle the same source
recommends.

Silent message loss on consumer crash. Symptom. A background job that
subscribes to an event topic occasionally, and apparently randomly, misses
events, and there is no error anywhere because nothing failed loudly. Cause.
The consumer is configured for at-most-once delivery, commits its read offset
or acknowledges the message before finishing processing, and a crash between
the acknowledgment and the actual side effect loses the message permanently
with no trace. Fix. Acknowledge or commit only after the side effect has
durably completed, which trades a small risk of duplicate processing, handled
by idempotency, for the much worse risk of silent loss.

Poison message stalling an entire partition or queue. Symptom. Throughput
on one topic drops to zero, and the consumer's logs show the same message
being retried over and over with no progress. Cause. A single malformed or
unprocessable message is retried indefinitely by the consumer's retry policy,
and on a partitioned, ordered log like Kafka, that retry loop blocks every
later message on the same partition from being processed, because ordering
guarantees prevent skipping ahead. Fix. Cap the retry count and route the
message to a Dead Letter Channel after the cap is reached, so one bad message
can never indefinitely block the healthy ones behind it.

Treating the bus as a database. Symptom. A new consumer needs historical
data that predates its subscription and the answer, in the worst version of
this misuse, is "replay the last two years of the topic," which either exceeds
the broker's retention window or takes hours and floods the bus with traffic
unrelated to real-time processing. Cause. The bus was used as the durable
system of record instead of as a transport for change notifications, with no
separate queryable store maintained for historical or point-in-time reads.
Fix. Pair the bus with a durable, queryable read model, built by a consumer
that projects the event stream into a database, and serve historical queries
from that read model, never from replaying the raw bus.

Unbounded fan-out amplifying an incident. Symptom. One producer's bug
publishes ten times its normal message volume for an hour, and instead of
degrading one system, every one of the twelve subscribed downstream systems
degrades simultaneously. Cause. The decoupling the bus provides is decoupling
of knowledge, not decoupling of blast radius. A burst on a shared topic is a
burst delivered to every subscriber at once. Fix. Apply backpressure and rate
limiting at the bus or at each consumer's ingestion point, and treat a shared
topic's traffic characteristics as a capacity-planning input for every
subscriber, not only for the producer.

## 12. Trade-off matrix

| Force | Message Bus (pub-sub, many consumers) | Point-to-Point Channel (direct queue) | Direct synchronous API call | Message Broker as a generic term (routing only, no shared model) |
|---|---|---|---|---|
| Coupling between producer and consumer | Near zero, producer never knows consumer count | Low, producer targets one logical queue but usually one consumer group | High, caller must know callee's address and be available together in time | Low, but shared data model discipline is not implied by the term itself |
| Latency | Higher, network hop plus broker persist plus fan-out | Higher than a direct call, similar to bus for a single hop | Lowest, one network hop bounded by callee | Comparable to the bus, depends on implementation |
| Delivery cardinality | One producer, many consumers by default | One producer, effectively one logical consumer (or one from a competing group) | One caller, one callee, always exactly one | Configurable per channel, not guaranteed many-to-many |
| Consistency model | Eventual, asynchronous by default | Eventual, asynchronous by default | Strong, synchronous, immediate | Eventual, asynchronous by default |
| Operational weight | Highest, shared infra plus schema governance plus subscriber tracking | Medium, one broker but simpler topology | Lowest, no extra infra beyond the services themselves | Medium to high, infra without the shared-model governance overhead |
| Best fit | Many independent reactors to one business event, growing over time | Exactly one consumer must handle each unit of work, load leveled | Caller needs an answer now, within the current request | Ad hoc routing between systems with no formal shared vocabulary |

## 13. Related and incompatible patterns

Publish-Subscribe Channel is the mechanism a Message Bus is built out of.
Every named topic on a bus is, structurally, one Publish-Subscribe Channel. The
Message Bus adds the organizing idea of a common data model and command set
spanning many such channels, plus the expectation that the whole collection is
operated as one piece of shared infrastructure rather than as unrelated
one-off channels.

Message Channel is the more general parent abstraction, covering both
point-to-point and publish-subscribe delivery. A Message Bus specifically
composes many Publish-Subscribe Channels, a specialization of Message Channel,
under one shared governance layer.

Message Router commonly sits on or beside the bus to inspect message
content or headers and direct a message to one of several possible downstream
channels based on that inspection, which is how a bus implements
content-based routing without every consumer needing to filter every message
itself.

Channel Adapter and Messaging Bridge are the edge components that
translate between a participant's native format and the bus's common data
model, and between two otherwise incompatible messaging technologies,
respectively. A real Message Bus deployment almost always has at least one of
these at every legacy system's boundary.

Dead Letter Channel is the companion pattern that receives messages the
bus could not deliver or a consumer could not process after exhausting
retries, and it is what closes the poison-message failure mode from dimension
11.

Observer from the Gang of Four catalog is the single-process ancestor of
this idea. A Message Bus is what Observer becomes once the subject and the
observers are allowed to live in different processes, on different machines,
possibly written in different languages, joined by a shared, serializable
message format instead of an in-memory method call.

Mediator, also from the Gang of Four catalog, shares the goal of reducing
direct references between many collaborating objects, but a Mediator typically
knows all its colleagues explicitly and coordinates them with direct method
calls, while a bus's producers and consumers are mutually unaware of each
other and communicate only through published messages. A bus is a Mediator
whose knowledge of participants has been replaced entirely by a subscription
registry.

Command Bus is a narrower, incompatible-by-cardinality specialization. It
enforces exactly one handler per command, which contradicts the fan-out
default this pattern assumes, so a system that needs both shapes typically runs
two separate infrastructures, or two clearly separated topic naming
conventions, one for events with many subscribers and one for commands with
exactly one handler, rather than trying to force one bus to honor both
contracts at once.

## 14. Refactoring path in and out

Introducing a bus into a system built on direct calls. Start by picking
the single highest-value case, usually the business event with the most actual
or anticipated downstream reactors, for example an order-placed notification
that billing, inventory, and shipping all currently poll for or receive via
separate ad hoc webhooks. Define the canonical event shape for that one case
first, resisting the urge to design the full common data model up front. Stand
up the broker and publish the event alongside the existing direct calls,
without removing them yet, so the bus is additive and low-risk. Migrate one
consumer at a time from its direct integration to a bus subscription, verifying
parity in a staging environment before cutting the direct call. Only after
every planned consumer has migrated, remove the old direct integration code
from the producer. Expand the common data model to a second event type only
once the first has proven its shape holds up under real schema evolution
pressure, rather than designing five topics speculatively.

Removing a bus that has stopped earning its place. This is the harder
direction and it happens most often when a bus was introduced for
two systems that never grew a third consumer, or when an ESB accumulated so
much business logic that removing it means first extracting that logic. Start
by inventorying every producer and every consumer of every topic, because this
inventory is frequently the first time anyone has a complete picture, which is
itself evidence the coupling was already too invisible. For a topic with
exactly one producer and one consumer that will not realistically grow a
second, replace the bus subscription with a direct call or a Point-to-Point
Channel, and delete the topic once traffic on it is zero for a full
observation window covering the slowest expected retry or reconciliation
cycle. For an ESB carrying transformation or routing logic that belongs to a
specific service, extract that logic into the owning service's own codebase
first, under test, before touching the bus configuration, so the behavior is
never lost mid-migration. Never remove the bus infrastructure itself until
every topic on it has been individually retired through this process. A bus
retirement is a sequence of independent topic retirements, not one atomic cut.

## 15. Testing and verification

Testing code that publishes to a bus is easier for the producer's own logic in
isolation. Because the producer holds no reference to any consumer, a unit test
can substitute a fake bus that simply records what was published and assert on
the shape and content of that recorded message, with no network, no broker,
and no consumer involved.

Testing the full, integrated behavior of a topic, given a real message,
consumers actually react correctly, is harder and is where most of the added
testing cost of this pattern lives. Consumer contract tests, in the Pact or
similar consumer-driven contract testing style, let each subscribing team
publish an expectation of the message shape they depend on, which the
producer's build then verifies against before any schema change ships, closing
the undocumented-contract failure mode from dimension 11 with an automated
gate rather than a hope.

For the consumer side, test the handler function in isolation against a
constructed message, exactly as this entry's own code samples in dimension 8
do, by calling the handler directly with a synthetic message rather than
standing up a real broker for every unit test. Reserve a small number of true
end-to-end tests, publish a real message to a real or embedded broker instance
such as an embedded Kafka test cluster or a local RabbitMQ container, and
assert the consumer's observable side effect, for the handful of critical
paths where the wiring itself, not just the handler logic, needs verification.

Idempotency, the property most consumers need because of at-least-once
delivery, is tested by publishing the identical message twice, in sequence,
against a fresh consumer state, and asserting the observable side effect
occurred exactly once, not that the handler was merely called twice
successfully. A handler that runs twice and produces two side effects is
failing this test even if neither run threw an error.

## 16. Observability signals

Per-topic publish rate and per-consumer-group consume rate, graphed together,
reveal the health of the bus at a glance. A growing gap between the two over
time is consumer lag, meaning a consumer is falling behind and will eventually
either catch up under reduced load or need remediation before it hits a
retention limit and loses messages it never got to.

Consumer lag itself, whether measured as Kafka's offset lag or as queue depth
on a broker like RabbitMQ or SQS, is the single most load-bearing metric for
this pattern. A healthy bus shows lag oscillating near zero under normal load
and returning to zero shortly after any burst, and an unhealthy one shows lag
climbing without bound.

Dead-letter queue depth and dead-letter arrival rate, tracked per topic and per
consumer, surface the poison-message failure mode from dimension 11 before it
becomes a full outage. A healthy system has a dead-letter rate near zero, and
any sustained non-zero rate on a specific topic is a signal to investigate that
producer's schema or that consumer's handler logic immediately.

End-to-end latency, from the timestamp a message was published to the
timestamp each consumer group finished processing it, distinguishes the
bus's own transport latency from a specific consumer's processing latency.
Without this split metric, a slow business process downstream of the bus is
indistinguishable from a slow bus, which sends the wrong team chasing the
wrong root cause.

A correlation identifier propagated through every message and logged at
publish time and at every consumer's handle time is what makes distributed
tracing across the bus possible at all. Without it, who reacted to this one
specific event, and how long each reaction took, is unanswerable from logs
alone, which is exactly the call-graph-invisibility cost named in the
consequences dimension, made partially recoverable by disciplined
instrumentation.

A healthy dashboard for a bus in production shows near-zero consumer lag
across every subscribed consumer group, a dead-letter rate close to zero, and
a stable ratio between published volume and total consumed volume across all
subscribers. A failing one shows lag climbing on one or more consumer groups,
a rising dead-letter count on a specific topic, or a published-to-consumed
ratio that drifts away from the expected fan-out factor, meaning some
subscriber has silently stopped receiving or stopped processing.

## 17. Security and privacy implications

A Message Bus is, structurally, a single shared surface that every
participating system's data flows through, which makes it a natural place to
concentrate the organization's most sensitive cross-system data in transit. A
compromise of the broker or of its access controls is a compromise of every
topic on it, not just one integration, so the blast radius of a broker-level
credential leak is materially larger than the blast radius of a single
point-to-point integration's credential leak.

Authorization at the topic level, not merely at the broker connection level,
is the control that prevents a service that legitimately needs to publish to
one topic from also being able to read every other topic on the same shared
infrastructure. Without per-topic access control lists, a bus with many topics
becomes a lateral-movement opportunity for any credential compromise, however
minor.

Personal data placed on a shared bus is, by the nature of the pattern,
replicated to every current and every future subscriber automatically, with no
further action from the producer. This means a data protection review must
happen at the moment a field is added to a shared topic's schema, not
retroactively after subscribers have already begun consuming it, because
retracting personal data that many independent consumers may have already
persisted into their own stores is, in general, not possible from the bus
side alone.

Message payload encryption in transit, and at rest where the broker persists
messages durably as Kafka does by design, needs to be an explicit
configuration choice rather than an assumption, because a broker's default
configuration in several widely used systems does not encrypt data at rest
out of the box, and a bus carrying, for example, an order event with a
customer's address and payment status is carrying regulated personal data
regardless of how internal the infrastructure feels.

Replay capability, one of the pattern's genuine strengths for onboarding a new
consumer against historical data, is also a genuine risk if retention windows
are set generously without an accompanying data retention and deletion policy
review, because a long-retained topic containing personal data can quietly
become a long-lived, broadly accessible copy of data that the source system
itself is obligated to delete on request.

## 18. References

1. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, the
   Message Bus pattern page,
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageBus.html,
   verified 2026-08-02.
2. Apache Kafka project, introduction and documentation,
   https://kafka.apache.org/intro, verified 2026-08-02.
3. RabbitMQ tutorials, exchange, queue, and AMQP 0-9-1 and AMQP 1.0 protocol
   references, https://www.rabbitmq.com/tutorials, verified 2026-08-02.
4. Amazon Web Services, Amazon SNS product page, fan-out messaging capability,
   https://aws.amazon.com/sns/, verified 2026-08-02.
5. Microsoft Learn, Azure Service Bus, Queues, Topics, and Subscriptions,
   https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-queues-topics-subscriptions,
   verified 2026-08-02.
6. NATS documentation, core concepts overview,
   https://docs.nats.io/nats-concepts/overview, verified 2026-08-02.
7. Martin Fowler and James Lewis, "Microservices," martinfowler.com, 2014, the
   "Smart endpoints and dumb pipes" section and the ESB criticism quoting Jim
   Webber, https://martinfowler.com/articles/microservices.html, verified
   2026-08-02.
8. Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides, *Design
   Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley,
   1994, chapter 5, Behavioral Patterns, Observer, for the single-process
   ancestor of this pattern's fan-out shape.

## Code examples

The following four implementations are the in-process Event Bus variant from
dimension 8, kept intentionally small and dependency-free so the pattern's
structure, a topic-keyed subscription map, publish fans out to every matching
handler, is visible without framework scaffolding. Every sample was compiled
or run directly against the toolchain versions noted below.

### Python (3.14.6, ran with `python3`)

```python
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Any

@dataclass
class Message:
    topic: str
    payload: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict)

class MessageBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Message], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[Message], None]) -> Callable[[], None]:
        self._subscribers[topic].append(handler)
        def unsubscribe() -> None:
            self._subscribers[topic].remove(handler)
        return unsubscribe

    def publish(self, message: Message) -> int:
        handlers = self._subscribers.get(message.topic, [])
        delivered = 0
        for handler in list(handlers):
            handler(message)
            delivered += 1
        return delivered

def main() -> None:
    bus = MessageBus()
    received: list[str] = []

    def billing_handler(msg: Message) -> None:
        received.append(f"billing saw order {msg.payload['order_id']}")

    def shipping_handler(msg: Message) -> None:
        received.append(f"shipping saw order {msg.payload['order_id']}")

    bus.subscribe("order.placed", billing_handler)
    bus.subscribe("order.placed", shipping_handler)

    delivered = bus.publish(Message(topic="order.placed", payload={"order_id": 42}))
    assert delivered == 2
    for line in received:
        print(line)

if __name__ == "__main__":
    main()
```

Ran with `python3 bus.py` and printed both handler lines. The subscription map
is a plain `dict` from topic string to a list of callables, and `publish`
iterates a copy of that list so a handler that unsubscribes mid-dispatch never
mutates the collection being iterated.

### Go (go1.26.4)

```go
package main

import (
	"fmt"
	"sync"
)

type Message struct {
	Topic   string
	Payload map[string]any
}

type Handler func(Message)

type MessageBus struct {
	mu          sync.RWMutex
	subscribers map[string][]Handler
}

func NewMessageBus() *MessageBus {
	return &MessageBus{subscribers: make(map[string][]Handler)}
}

func (b *MessageBus) Subscribe(topic string, h Handler) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.subscribers[topic] = append(b.subscribers[topic], h)
}

func (b *MessageBus) Publish(msg Message) int {
	b.mu.RLock()
	handlers := append([]Handler(nil), b.subscribers[msg.Topic]...)
	b.mu.RUnlock()
	for _, h := range handlers {
		h(msg)
	}
	return len(handlers)
}

func main() {
	bus := NewMessageBus()
	var received []string

	bus.Subscribe("order.placed", func(m Message) {
		received = append(received, fmt.Sprintf("billing saw order %v", m.Payload["order_id"]))
	})
	bus.Subscribe("order.placed", func(m Message) {
		received = append(received, fmt.Sprintf("shipping saw order %v", m.Payload["order_id"]))
	})

	delivered := bus.Publish(Message{Topic: "order.placed", Payload: map[string]any{"order_id": 42}})
	if delivered != 2 {
		panic("expected 2 deliveries")
	}
	for _, line := range received {
		fmt.Println(line)
	}
}
```

Ran with `go run bus.go` and printed both handler lines. This variant adds a
`sync.RWMutex` around the subscription map because Go's zero-value
concurrency story means a bus meant to be published to from multiple
goroutines needs its own explicit locking, unlike the single-threaded Python
and TypeScript samples here.

### Rust (rustc 1.97.1)

```rust
use std::collections::HashMap;

struct Message {
    topic: String,
    order_id: u32,
}

struct MessageBus {
    subscribers: HashMap<String, Vec<Box<dyn Fn(&Message) -> String>>>,
}

impl MessageBus {
    fn new() -> Self {
        MessageBus { subscribers: HashMap::new() }
    }

    fn subscribe(&mut self, topic: &str, handler: Box<dyn Fn(&Message) -> String>) {
        self.subscribers.entry(topic.to_string()).or_insert_with(Vec::new).push(handler);
    }

    fn publish(&self, msg: &Message) -> Vec<String> {
        let mut results = Vec::new();
        if let Some(handlers) = self.subscribers.get(&msg.topic) {
            for handler in handlers {
                results.push(handler(msg));
            }
        }
        results
    }
}

fn main() {
    let mut bus = MessageBus::new();

    bus.subscribe("order.placed", Box::new(|m: &Message| {
        format!("billing saw order {}", m.order_id)
    }));
    bus.subscribe("order.placed", Box::new(|m: &Message| {
        format!("shipping saw order {}", m.order_id)
    }));

    let msg = Message { topic: "order.placed".to_string(), order_id: 42 };
    let results = bus.publish(&msg);
    assert_eq!(results.len(), 2);
    for line in &results {
        println!("{}", line);
    }
}
```

Compiled with `rustc bus.rs -o bus` and ran the resulting binary, which printed
both handler lines. Handlers here are boxed trait objects, `Box<dyn Fn(&Message)
-> String>`, because Rust needs a concrete, heap-allocated type to store a
heterogeneous collection of closures in one `Vec`.

### TypeScript (tsc 7.0.2, run on node v23.11.0)

```typescript
type Message = { topic: string; payload: Record<string, unknown> };
type Handler = (msg: Message) => void;

class MessageBus {
  private subscribers = new Map<string, Handler[]>();

  subscribe(topic: string, handler: Handler): () => void {
    const list = this.subscribers.get(topic) ?? [];
    list.push(handler);
    this.subscribers.set(topic, list);
    return () => {
      const remaining = (this.subscribers.get(topic) ?? []).filter((h) => h !== handler);
      this.subscribers.set(topic, remaining);
    };
  }

  publish(msg: Message): number {
    const handlers = this.subscribers.get(msg.topic) ?? [];
    for (const handler of handlers) handler(msg);
    return handlers.length;
  }
}

function main(): void {
  const bus = new MessageBus();
  const received: string[] = [];

  bus.subscribe("order.placed", (m) => received.push(`billing saw order ${m.payload.orderId}`));
  bus.subscribe("order.placed", (m) => received.push(`shipping saw order ${m.payload.orderId}`));

  const delivered = bus.publish({ topic: "order.placed", payload: { orderId: 42 } });
  if (delivered !== 2) throw new Error("expected 2 deliveries");
  received.forEach((line) => console.log(line));
}

main();
```

Compiled with `npx tsc bus.ts --target ES2020 --module commonjs --strict` and
ran the emitted JavaScript with `node`, which printed both handler lines. Java
was on the toolchain list in the entry template but this machine has no Java
runtime installed, so a Java sample was not attempted rather than presented as
compiled when it was not.

All four samples deliberately share one shape, a topic-keyed collection of
handler functions and a `publish` that iterates and invokes each match, so a
reader can see the same structural idea, dimension 5's Producer, Message, Bus,
and Consumer roles, expressed in four different type systems and concurrency
models.
