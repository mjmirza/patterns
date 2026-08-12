---
name: Message
slug: message
family: 07-integration
category: Integration
aliases: [Message Object, Envelope]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [message-channel, message-endpoint, message-translator, canonical-data-model, command-message, document-message, event-message]
incompatible_with: []
verified: 2026-08-02
---

# Message

## 1. Name, aliases, and lineage

The canonical name is Message, catalogued by Gregor Hohpe and Bobby Woolf in
*Enterprise Integration Patterns. Designing, Building, and Deploying Messaging
Solutions*, Addison-Wesley, 2003, chapter 4, page 79. The book states the
pattern this way. wrap each piece of data to be transmitted in a Message, an
atomic packet of data that can be transmitted on a Message Channel
(Hohpe and Woolf, *Enterprise Integration Patterns*, page 79, and the online
catalog page at
[https://www.enterpriseintegrationpatterns.com/patterns/messaging/Message.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Message.html),
verified 2026-08-02).

The alias Envelope is common in messaging middleware documentation, because the
pattern separates a header, which the middleware and the endpoints read to
route and process the transmission, from a body, which carries the payload the
sender actually wants the receiver to see. RabbitMQ's own documentation for the
AMQP 0-9-1 model calls the combination of routing metadata and content an
envelope in exactly this sense
([https://www.rabbitmq.com/tutorials/amqp-concepts](https://www.rabbitmq.com/tutorials/amqp-concepts),
verified 2026-08-02). The term Message Object appears in older Java Message
Service literature to distinguish the wrapped, addressable unit from the raw
data a producer starts with, since the JMS specification itself defines a
`javax.jms.Message` interface with header fields, properties, and a body as
one addressable object
([https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/message](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/message),
verified 2026-08-02).

Message is the foundational pattern of the entire Enterprise Integration
Patterns catalog. Every other messaging pattern in the book, Message Channel,
Message Router, Message Translator, Message Endpoint, assumes that the unit
moving through the system is a Message and specifies behaviour in terms of what
a component does to or with a Message. Hohpe and Woolf organise the book
explicitly around this dependency, introducing Message Channel and Message
before any routing or transformation pattern, because those later patterns
manipulate Messages and cannot be defined without the noun first
(Hohpe and Woolf, chapter 3, "Messaging Systems", pages 53 to 78).

## 2. Problem and context

Two applications need to exchange information without either one blocking on
the other's availability, without either one dictating the other's internal
data model, and without a network call failing catastrophically the moment a
socket drops. A synchronous remote procedure call fails all three requirements
at once. It requires both parties to be available for the duration of the call,
it typically forces the caller to shape its request as a foreign method
signature, and a dropped connection means the caller has no record that
anything was ever attempted.

The context in which Message becomes necessary is asynchronous, decoupled
integration between two or more systems that are developed, deployed, and
operated independently. This is the ordinary condition of enterprise software,
a shipping system does not share a deploy cycle with a billing system, a
mobile client does not share a process with the server it talks to, a
warehouse robot does not share a clock with the inventory database it updates.
Whenever two components need to exchange data across that kind of boundary and
neither one can dictate the other's availability or internal representation,
something has to travel between them that is self-contained enough to survive
the trip.

That self-contained unit is the Message. It exists because the alternative,
passing raw application data straight into a channel with no defined
structure, leaves every consumer guessing at what arrived, how to correlate a
reply with a request, how to know whether a payload has already been retried,
and what format the bytes on the wire actually are. A Message answers those
questions by convention. it carries a header, a set of well-known fields any
endpoint on the system can read without understanding the payload, and a body,
the actual content the sending application wants the receiving application to
act on.

## 3. Forces

The design of a Message balances several pressures that pull in different
directions, and a working implementation is a specific, defensible resolution
of the tension between them, not an attempt to satisfy all of them maximally.

Self-description against payload size. A Message that carries every piece of
metadata a consumer could ever want, content type, schema version, correlation
identifier, causation identifier, trace identifiers, sender identity, retry
count, expiry, is easy to route and easy to debug, but every one of those
fields is bytes on the wire and CPU cycles to serialize and parse on every hop.
A minimal Message with only a body is cheap to move but forces every consumer
to guess or to consult an out-of-band contract for anything beyond raw content.

Loose coupling against operability. The entire reason to introduce a Message is
to decouple sender from receiver, in time, in location, and in synchronization.
That decoupling is bought at the cost of operability, because a call stack that
would show a synchronous failure immediately now shows nothing at the call
site. the failure surfaces later, somewhere else, unless the header carries
enough correlation information to reconstruct the story. Every field added to
the header in the name of operability is a field the sender must populate
correctly and the infrastructure must preserve intact across every hop, broker
restart, and protocol translation.

Structural rigidity against evolvability. A strict, versioned schema for the
header and the body catches malformed messages early and lets tooling generate
strong types on both ends. The same rigidity is what breaks a consumer the
moment a producer adds an optional field or renames one, unless the schema
system was chosen and governed specifically to permit additive change. Systems
that skip schema discipline gain short-term velocity and pay for it later in
silent misinterpretation, where a body decodes without error but into the wrong
shape.

Uniformity against expressiveness. A single, uniform Message envelope used for
every kind of interaction, a fire-and-forget notification, a command that must
be obeyed, a query that expects a typed reply, is simple to build tooling
around, one serializer, one router, one dead-letter path. The same uniformity
erases the very real semantic difference between those three kinds of
interaction, which is why Hohpe and Woolf immediately specialise Message into
Command Message, Document Message, and Event Message, each carrying the same
envelope shape but a different intent
(Hohpe and Woolf, pages 145 to 152). A system that never specialises pays for
that uniformity in ambiguous consumer code that has to infer intent from body
content.

Delivery cost against delivery guarantee. Exactly-once delivery at the
transport layer is not achievable across an unreliable network in the general
case, a result formalised for distributed consensus problems and applied
directly to messaging semantics by every mainstream broker's own documentation,
which instead offers at-most-once, at-least-once, or effectively-once through
idempotent consumer cooperation
([https://kafka.apache.org/documentation/#semantics](https://kafka.apache.org/documentation/#semantics),
verified 2026-08-02). A Message that wants a strong guarantee has to carry
enough identity, typically a message identifier the consumer can deduplicate
against, to let the receiving side do the work the network cannot do alone.
That identity field is a cost paid on every message, whether or not that
particular message is ever actually redelivered.

## 4. Applicability and non-applicability

Reach for the Message pattern, an explicit header-plus-body envelope crossing a
Message Channel, when the following hold.

- Two or more components communicate across a process, deployment, or team
  boundary and need to remain independently deployable.
- The interaction is naturally asynchronous, or the system needs the option of
  making it asynchronous later without renegotiating the contract.
- More than one kind of consumer, or more than one kind of interaction pattern,
  Command, Event, Document, will travel over the same infrastructure and needs
  a shared way to be told apart.
- Observability, tracing a piece of data's path through several hops, is a
  requirement, and that requirement is best served by fields that travel with
  the data rather than by external correlation tables.
- The system must survive partial failure, a consumer being down, a broker
  restarting, without silently losing data, which requires a persistable,
  replayable unit rather than a transient call stack frame.

Do not reach for it, and prefer a plain function call, a direct method
invocation, or a typed request-response object local to a single process, when
the following hold.

- Both parties live in the same process and the same deploy unit. wrapping an
  in-memory function call in a header-and-body envelope adds serialization
  cost and indirection with no corresponding gain, because there is no network
  boundary, no independent deploy cycle, and no need to survive a process
  restart.
- The interaction is a synchronous request that must complete before the
  caller can proceed, and both parties are always co-located and always
  available together, such as a UI component reading local application state.
  Introducing a Message here trades a direct call for a channel, a
  serialization step, and an asynchronous mental model the interaction does
  not actually need.
- The data being passed is a value object used purely for calculation inside a
  single bounded context, with no crossing of a system boundary. Wrapping every
  internal domain object in a messaging envelope confuses the domain model
  with the integration layer, a distinction Eric Evans is explicit about when
  he separates the domain layer from the infrastructure layer in domain-driven
  design (Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart
  of Software*, Addison-Wesley, 2003, chapter 4, "Isolating the Domain").
- The team has no operational capacity to run or consume a broker, and the
  integration surface is a single, low-volume, synchronous HTTP call where a
  plain typed request body already satisfies every real requirement. Adopting
  a full Message envelope purely for architectural symmetry, with no channel,
  no asynchronous delivery, and no multiple consumer, adds format ceremony
  that nobody consumes.

## 5. Structure

A Message has exactly two structural parts, and every real-world variant adds
detail inside one of the two, never a third part alongside them.

The Header is the set of fields the messaging infrastructure and any
generic endpoint can read, interpret, and act on without understanding the
payload's business meaning. A minimal, broadly recognised header carries a
message identifier unique to this delivery attempt, a correlation identifier
linking this message to the request or event that caused it, a content type
describing how to decode the body, a timestamp, and a message type or name
telling a router or a consumer what kind of thing this is before it looks
inside. Larger systems add a causation identifier, distinct from correlation
and tracking direct cause rather than the whole conversation, a trace
identifier for distributed tracing, a schema version, a sender identity, a
reply-to address, an expiration, and a delivery or retry count.

The Body is the payload, the actual content the sender wants the receiver
to act on. The body is opaque to the routing infrastructure by design, only the
endpoints at either end are expected to parse it, and the header's content type
field is what tells any intermediary how to decode it if it must be inspected
or transformed in transit, for example by a Message Translator.

Three participants collaborate around this structure, though none of them is
part of the Message itself.

- Producer, or Sender. The component that constructs the Message,
  populates the header correctly, serializes the body, and hands the completed
  Message to a Message Channel.
- Message Channel. The virtual pipe the Message travels through, a queue,
  a topic, an HTTP endpoint acting as a channel, or an in-memory bus. The
  channel's own contract, point to point, publish subscribe, guaranteed
  delivery, is a separate pattern, Message Channel, but the Message must be
  shaped to be transportable by whatever channel carries it.
- Consumer, or Receiver. The component that receives the Message from the
  channel, reads the header to decide how to route or dispatch it, deserializes
  the body according to the content type, and acts on the payload.

## 6. ASCII structure diagram

```
+-----------+          +-------------------+          +-----------+
|           |          |                    |          |           |
| Producer  |--------->|  Message Channel   |--------->| Consumer  |
|           |  sends   |  (queue / topic /  | receives |           |
+-----------+          |   pub-sub bus)     |          +-----------+
                        +-------------------+
                                 |
                                 | carries
                                 v
                        +-------------------+
                        |     Message       |
                        |-------------------|
                        |  Header           |
                        |   message_id      |
                        |   correlation_id  |
                        |   causation_id    |
                        |   type            |
                        |   content_type    |
                        |   timestamp       |
                        |   trace_id        |
                        |-------------------|
                        |  Body             |
                        |   (opaque bytes,  |
                        |    decoded per    |
                        |    content_type)  |
                        +-------------------+
```

## 7. Dynamics

The runtime sequence, from a producer deciding to notify another system to a
consumer acting on the notification, follows a consistent shape regardless of
which specialisation, Command, Event, or Document, is in play.

```
Producer                Message Channel               Consumer
   |                          |                            |
   | 1. build header          |                            |
   | 2. serialize body        |                            |
   | 3. Message ready         |                            |
   |------- send(msg) ------->|                            |
   |                          | 4. persist / enqueue        |
   |                          | 5. ack to producer          |
   |<------- send-ack --------|                             |
   |                          |                            |
   |                          |------ deliver(msg) ------->|
   |                          |                            | 6. read header
   |                          |                            | 7. route by type
   |                          |                            | 8. deserialize body
   |                          |                            | 9. process
   |                          |<------- consume-ack --------|
   |                          | 10. mark delivered           |
   |                          |    (or retry on failure,     |
   |                          |     or dead-letter after N)  |
```

The two acknowledgement points, send-ack and consume-ack, are where the
delivery guarantee actually lives. A channel offering at-least-once delivery
holds the Message until it receives the consume-ack, and redelivers it,
identical message identifier included, if that acknowledgement never arrives
within a timeout, which is precisely why the header's message identifier
matters for consumer-side deduplication rather than being decorative metadata
(Hohpe and Woolf, "Idempotent Receiver", page 522, describing exactly this
redelivery-then-deduplicate flow).

## 8. Implementation variants

The Message pattern is realised differently depending on the transport and the
ecosystem, but the header-plus-body shape recurs in every serious
implementation, which is itself evidence the pattern names a genuine, recurring
structural need rather than an arbitrary convention.

AMQP 0-9-1, the protocol behind RabbitMQ, defines a Basic.Properties structure
carrying content-type, content-encoding, headers, an arbitrary key-value map,
delivery-mode, correlation-id, reply-to, expiration, message-id, timestamp,
type, user-id, and app-id, attached to an opaque body byte array
([https://www.rabbitmq.com/tutorials/amqp-concepts](https://www.rabbitmq.com/tutorials/amqp-concepts),
verified 2026-08-02). This is close to a textbook realisation of Hohpe and
Woolf's Message, standardised at the protocol level rather than left to each
application to invent.

Apache Kafka's `ProducerRecord` and the record it becomes on the log carries a
key, a value, a timestamp, and an explicit `headers` field of arbitrary
key-value byte pairs, deliberately separated from the value so that routing
and filtering metadata never has to be parsed out of a serialized business
payload
([https://kafka.apache.org/38/javadoc/org/apache/kafka/clients/producer/ProducerRecord.html](https://kafka.apache.org/38/javadoc/org/apache/kafka/clients/producer/ProducerRecord.html),
verified 2026-08-02).

Cloud provider event systems standardised on the same shape at the industry
level with CloudEvents, a CNCF specification that defines exactly the
Hohpe-and-Woolf header-and-body split as required attributes, `id`, `source`,
`specversion`, `type`, alongside an optional `datacontenttype` and a `data`
field for the payload
([https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md),
verified 2026-08-02). CloudEvents is notable because it is a transport-neutral
standard, meaning independent vendors converged on the identical structural
decomposition that Hohpe and Woolf described in 2003, which is strong evidence
the shape is discovered rather than invented.

JSON API and similar HTTP-native document formats implement a lighter variant,
where the HTTP headers, `Content-Type`, a custom `X-Correlation-Id`, stand in
for the messaging header and the HTTP body is the Message body, useful when the
transport is a webhook or a REST callback rather than a broker.

Language-idiomatic variants differ mainly in how the header is represented.
Statically typed languages tend to model the header as a typed struct or
record with named fields plus a generic metadata map for extension fields not
yet promoted to first-class status. Dynamically typed languages more often
represent the entire Message as a single dictionary or object with a nested
metadata key, trading compile-time field safety for schema flexibility.

## 9. Known production uses

RabbitMQ, an AMQP 0-9-1 broker, implements the Message pattern at the protocol
level through Basic.Properties, and its own tutorial documentation explicitly
frames the properties-plus-body pair as the atomic unit of transport
([https://www.rabbitmq.com/tutorials/amqp-concepts](https://www.rabbitmq.com/tutorials/amqp-concepts),
verified 2026-08-02).

Apache Kafka, the de facto standard log-based event streaming platform, ships
`ProducerRecord` and `ConsumerRecord` with a first-class `headers` field
separated from the payload value specifically so intermediate consumers,
interceptors, and tracing systems can act on message metadata without decoding
the business payload
([https://kafka.apache.org/38/javadoc/org/apache/kafka/clients/producer/ProducerRecord.html](https://kafka.apache.org/38/javadoc/org/apache/kafka/clients/producer/ProducerRecord.html),
verified 2026-08-02).

AWS SQS and SNS implement the pattern through a `MessageAttributes` map
alongside a `MessageBody`, documented in the AWS SDK, and used across a very
large share of production event-driven architectures on AWS for exactly the
routing-without-payload-parsing reason described above
([https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-message-metadata.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-message-metadata.html),
verified 2026-08-02).

The CloudEvents specification, a CNCF incubating project backed by Microsoft,
Google, Red Hat, IBM, and others, standardises the identical header-plus-data
shape as an interoperability layer across serverless and event-driven
platforms including AWS EventBridge, Azure Event Grid, and Google Eventarc
([https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md),
verified 2026-08-02).

Jakarta Messaging, formerly JMS, the Java EE and now Jakarta EE standard
messaging API used by Apache ActiveMQ, IBM MQ, and Solace, defines
`jakarta.jms.Message` as an interface with header fields, JMSMessageID,
JMSCorrelationID, JMSType, JMSTimestamp, application-settable properties, and
a body, and this exact shape has been the enterprise messaging contract in the
Java ecosystem since the original JMS 1.0 specification in 1998
([https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/message](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/message),
verified 2026-08-02).

## 10. Consequences

Positive consequences.

- Sender and receiver decouple completely, in time, the receiver need not be
  running when the sender sends, in space, neither needs to know the other's
  network location beyond the channel, and in synchronization, the sender
  does not block on the receiver's processing, which is the entire structural
  goal Hohpe and Woolf state for the messaging style as a whole (Hohpe and
  Woolf, chapter 2, "Integration Styles", pages 34 to 52).
- A uniform envelope gives infrastructure, routers, loggers, tracing systems,
  dead-letter handlers, a stable surface to operate on without understanding
  every payload shape that will ever cross the system, which is what makes
  generic, reusable middleware possible in the first place.
- Correlation and causation fields in the header make it possible to
  reconstruct a request's full path across several asynchronous hops after
  the fact, which is the foundation every distributed tracing system, from
  Zipkin's early trace-id propagation to the modern W3C Trace Context
  standard, is built on
  ([https://www.w3.org/TR/trace-context/](https://www.w3.org/TR/trace-context/),
  verified 2026-08-02).
- Persisted messages give the system a natural retry and replay mechanism.
  a consumer that crashes mid-processing can be restarted and will see the
  same message again, rather than the interaction simply being lost the way an
  unhandled exception in a synchronous call typically is.

Negative consequences.

- Latency increases relative to a direct call, because the message must
  traverse serialization, a channel, storage or buffering, and deserialization,
  where a direct call is a stack frame push. For latency-critical, tightly
  coupled interactions this cost is a genuine architectural tax, not a
  rounding error.
- Debugging becomes non-local. a failure a synchronous call would surface at
  the call site now surfaces, if it surfaces at all, in a dead-letter queue, a
  log line on a different host, or a silent drop, and reconstructing what
  happened depends entirely on the header fields having been populated
  correctly and preserved intact by every hop.
- The envelope introduces a second schema to govern, the header contract,
  alongside the payload schema. Both must evolve without breaking existing
  consumers, and header field drift, an optional field quietly becoming load
  bearing, is a common, hard to detect source of production incidents.
- Ordering and exactly-once semantics are not free. any consumer that needs
  strict ordering or exactly-once effects must build that guarantee itself,
  typically through the message identifier and idempotent processing, because
  the underlying transport rarely provides it end to end without additional
  design work. Kafka's own documentation on delivery semantics is explicit
  that exactly once from the broker's point of view still requires an
  idempotent or transactional producer configuration to hold end to end
  ([https://kafka.apache.org/documentation/#semantics](https://kafka.apache.org/documentation/#semantics),
  verified 2026-08-02).

## 11. Failure modes and misuse

This dimension is grounded partly in engineering judgement, marked where the
symptom description draws on operational experience rather than a citable
source.

Symptom. A consumer processes the same business effect twice, for example
a payment is charged twice, after what looked like a single message send.
Cause. The channel provides at-least-once delivery, which is the common
default for durable queues, and the message was redelivered after a consumer
acknowledgement was lost or delayed, but the consumer treated processing as
naturally idempotent when it was not, applying the payload's side effect a
second time on the second delivery.
Fix. Give every Message a stable, unique message identifier in the header
at creation time, generated by the producer, not the transport, and have the
consumer check that identifier against a durable dedup store, an idempotency
key table, before applying any side effect, discarding the message if the
identifier has already been processed. This is the Idempotent Receiver pattern
Hohpe and Woolf describe specifically as the consumer-side answer to
at-least-once delivery (Hohpe and Woolf, page 522).

Symptom. A new field added to a payload silently breaks an old consumer,
which either throws a deserialization error or, worse, decodes successfully
into a subtly wrong object with a default value where real data belonged.
Cause. No schema evolution discipline was defined for the body. producers
add fields freely, and consumers use a strict schema, either explicit or
implicit through a deserializer that requires every field to be present, with
no tolerance for unknown or optional fields.
Fix. Adopt an explicit compatibility mode, most commonly forward and
backward compatible schema evolution rules such as those enforced by Confluent
Schema Registry for Avro and Protobuf on Kafka, where a new field must be
optional with a default, and a removed field must be deprecated rather than
deleted outright before consumers have migrated
([https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html),
verified 2026-08-02).

Symptom. Distributed tracing shows gaps, a request's story is visible up
to a point and then vanishes, reappearing later under what looks like an
unrelated trace.
Cause. A hop in the pipeline, often a translator or an intermediary
service, constructed a brand new outbound Message rather than propagating the
inbound header's correlation and trace fields onto it, breaking the causal
chain the observability tooling relies on. Judgement, based on operational
experience.
Fix. Treat correlation-id, trace-id, and, where the interaction chain
matters, causation-id, as fields that must be copied forward by every
intermediary that constructs a downstream Message from an inbound one, and
enforce this with a shared library or middleware layer rather than leaving it
to each service author to remember.

Symptom. The message channel fills up, throughput collapses, and the team
discovers a large percentage of the messages sitting in the queue are the same
poison message being retried over and over.
Cause. No dead-letter or maximum-retry policy was attached to the channel,
so a message that the consumer cannot successfully process, a malformed
payload, a downstream dependency that will never come back for this input,
is redelivered indefinitely, consuming consumer capacity that legitimate
messages need.
Fix. Configure a Dead Letter Channel with a bounded maximum delivery
count, so that after N failed attempts the message is moved out of the main
flow into a channel a human or a separate remediation process inspects,
exactly the pattern Hohpe and Woolf describe under Dead Letter Channel
(Hohpe and Woolf, page 119, and this repository's own entry at
`patterns/07-integration/dead-letter-channel.md`).

Symptom. A payload that was valid JSON when sent triggers a parse error at
the consumer, but only intermittently, and only for messages from one specific
producer instance or version.
Cause. The header's content-type field either was not set or was ignored,
and the consumer assumed a fixed serialization format rather than reading the
declared content type before choosing a decoder, so a producer upgrade that
changed serialization library or compression silently broke consumers that
never checked. Judgement, based on operational experience.
Fix. Always set content-type explicitly at message construction and always
branch decoding logic on it at the consumer, treating an unrecognised
content-type as a routing failure to an Invalid Message Channel rather than a
best-effort parse attempt (this repository's own entry at
`patterns/07-integration/invalid-message-channel.md`).

## 12. Trade-off matrix

The comparison is against named alternative shapes for moving data between
components, not against a strawman of no structure at all.

| Force | Message (header + body envelope) | Raw payload over a channel, no envelope | Synchronous RPC (gRPC, direct HTTP call) | Shared database as integration point |
|---|---|---|---|---|
| Coupling between sender and receiver | Low. Channel and content type mediate, either side can change independently | Low on the wire, but implicit, consumers must infer structure out of band | High. Caller must know the callee's interface, version, and availability at call time | Very high. Both sides share the same schema and are coupled to every column |
| Time decoupling | Full, sender and receiver need not be online simultaneously | Full, but harder to reason about since there is no standard way to know what arrived | None, the caller blocks until the callee responds or times out | Full, but consistency and staleness must be reasoned about separately |
| Traceability across hops | Strong, if correlation and trace fields are populated and propagated | Weak, no standard place to carry a trace identifier | Strong at the call level via distributed tracing headers, W3C Trace Context, but the call itself is a single hop | Weak, a write has no inherent link to the process that produced it |
| Operational cost | Requires a broker or channel plus dead-letter and retry policy | Lowest infrastructure cost, but pushes correctness work onto every consumer | Requires service discovery and availability of the callee at call time | Requires managing a shared schema and access controls across teams |
| Latency | Higher than RPC, bounded by broker throughput and consumer polling or push latency | Similar to Message, since transport cost dominates either way | Lowest, a single network round trip | Not applicable in the same sense, latency is per query |
| Delivery guarantee achievable | At-least-once or effectively-once with an idempotent consumer, well understood pattern | Ad hoc, depends entirely on what the consumer chooses to implement | At-most-once by default, the caller must implement its own retry | Not applicable, writes are transactional within the database |

## 13. Related and incompatible patterns

Message Channel is the pipe a Message travels through, and the two
patterns are inseparable in practice, a Message with no channel has nowhere to
go, and a channel with no defined Message shape has no contract for what its
consumers should expect (this repository's own entry at
`patterns/07-integration/message-channel.md`).

Command Message, Document Message, Event Message are the three
specialisations Hohpe and Woolf define on top of the base Message shape, each
setting the header's type field and body semantics to signal a different
intent, an instruction to be obeyed, a data transfer with no implied action, or
a notification that something already happened
(Hohpe and Woolf, pages 145 to 153, and this repository's entry at
`patterns/07-integration/command-message.md`). These compose with Message
rather than replace it, they are Message with a convention layered on top.

Message Translator consumes a Message in one format and produces a
Message in another, and depends on the header's content type and type fields
to know what transformation to apply, making it a direct consumer of the
Message contract rather than a separate concern, where such an entry is
present in this repository.

Canonical Data Model addresses a different but adjacent problem, what
shape the body's business data should take when many systems with different
native formats all produce and consume Messages, so that a translator does not
have to know about every system pairwise (Hohpe and Woolf, page 355). Message
defines the envelope, Canonical Data Model defines a convention for what goes
inside the body.

Idempotent Receiver is the consumer-side pattern that makes the message
identifier field in the header load bearing rather than decorative, closing
the at-least-once delivery gap described in dimension 11
(Hohpe and Woolf, page 522).

Dead Letter Channel and Invalid Message Channel are the two failure
routing patterns a healthy Message-based system needs alongside the happy-path
channel, one for messages that fail processing after retries, the other for
messages that fail to even parse against their declared content type
(this repository's entries at `patterns/07-integration/dead-letter-channel.md`
and `patterns/07-integration/invalid-message-channel.md`).

Message has no genuinely incompatible pattern in the sense of two patterns
that cannot coexist in the same system. it is a foundational, low-level
pattern that other integration patterns build on rather than compete with.
The closest thing to a conflict is architectural, not structural. a system
that has fully committed to synchronous RPC as its only integration style has
no natural place for Message, but that is a style choice at a higher level of
the architecture, not an incompatibility between two patterns operating at the
same level.

## 14. Refactoring path in and out

Introducing Message into a system that currently exchanges raw, unstructured
data, a bare JSON object with no defined header, a plain string, a language
native object passed across a boundary that should not exist, follows a
sequence that avoids a big-bang rewrite.

1. Define the header contract first, in isolation from any single producer or
   consumer, choosing the minimal set, message identifier, correlation
   identifier, type, content type, timestamp, that every current and
   foreseeable consumer will need. Publish it as a shared type, schema, or
   interface definition rather than letting each service define its own.
2. Wrap the existing raw payload as the body of a Message, without changing
   the payload's internal shape yet. At this stage the goal is only to
   introduce the envelope, not to also redesign the business data inside it,
   because combining both changes in one step makes a failure hard to
   attribute.
3. Update the producer to populate the header and emit the wrapped Message on
   the existing channel, keeping the channel and transport otherwise
   unchanged. Verify the channel accepts the new, larger payload without
   truncation or size-limit issues, a common oversight with brokers that have
   a maximum message size, since a header adds real bytes on top of the
   existing body.
4. Update consumers one at a time to read the header for routing and
   dispatch decisions, falling back to their previous raw-payload parsing
   logic for messages that arrive without a header during the transition
   window, if backward compatibility with old producers is required during
   rollout.
5. Once every producer emits the envelope and every consumer reads it,
   remove the fallback path and, if the platform supports it, enforce the
   header contract at the channel boundary, rejecting or dead-lettering any
   message missing required header fields, which turns the convention into an
   enforced contract.

Removing Message from a system, or more precisely, retiring a specific
Message-based integration once both endpoints are collapsed into the same
deployable unit, follows the reverse motion.

1. Confirm the two former endpoints are now genuinely co-located, deployed
   together, in the same process or the same transaction boundary, such that
   the asynchronous decoupling the Message existed to provide is no longer
   needed.
2. Replace the send-to-channel call at the former producer with a direct
   in-process call to the former consumer's logic, passing the body's
   deserialized content directly as typed arguments rather than as a
   serialized envelope.
3. Retire the channel, the dead-letter path, and the header schema for this
   specific integration only after confirming no other consumer still
   subscribes to the same channel, since a channel with multiple independent
   subscribers cannot be safely collapsed just because one producer-consumer
   pair merged.
4. Remove the correlation and tracing plumbing that existed specifically to
   stitch together the asynchronous hop, since a direct in-process call is
   already traceable through the ordinary call stack and does not need a
   parallel correlation mechanism.

## 15. Testing and verification

This dimension is largely practice, marked where it draws on established
testing technique rather than a single citable source.

A Message's header and body should be tested as two separate concerns.
Contract tests verify the header shape, that a message identifier is always
present and unique per send, that correlation identifiers propagate correctly
across a chain of two or more hops, and that the content type field accurately
describes the body's actual encoding. These tests do not need a real broker,
they operate on the Message object or its serialized form directly.

Consumer-side tests should specifically exercise the redelivery case, sending
the identical message, same message identifier, twice to the consumer and
asserting the side effect happens exactly once, which is the concrete test for
the Idempotent Receiver correctness described in dimension 11. A consumer test
suite that never exercises redelivery has not actually tested the delivery
guarantee the system claims to provide.

Contract testing tools designed for asynchronous messaging, such as Pact's
message pact support, let a consumer specify the shape of Message it expects,
header fields included, and let a producer's test suite verify its emitted
Messages satisfy that contract without either side needing the other running
([https://docs.pact.io/getting_started/how_pact_works](https://docs.pact.io/getting_started/how_pact_works),
verified 2026-08-02).

What Message makes easier to test, relative to a tightly coupled synchronous
call, is isolating producer and consumer entirely, a producer's test suite can
assert on the Message it constructs without a live consumer, and a consumer's
test suite can assert on its behaviour given a hand-built Message fixture
without a live producer or broker, using a test double for the channel itself.

What becomes harder to test is the end-to-end delivery guarantee under real
failure conditions, broker restarts, network partitions, redelivery timing,
because those require either a real broker in a test environment or a
deliberately fault-injecting test rig, a heavier setup than a unit test
for a synchronous call ever requires.

## 16. Observability signals

This dimension is largely practice, drawn from operational convention across
the production systems cited in dimension 9 rather than from a single source.

A healthy Message-based integration shows, at minimum, a stable send rate that
tracks the producing system's actual event rate with no unexplained gaps, a
consumer lag or backlog depth that stays near zero or within an expected
processing window rather than growing unbounded, and a dead-letter rate near
zero, since a nonzero, growing dead-letter count is the clearest single signal
that a schema mismatch, a downstream dependency failure, or a poison message
is degrading the pipeline.

Each hop that touches a Message should log, at minimum, the message identifier
and the correlation identifier at receipt and at completion, which is what
makes it possible to reconstruct a message's full path across several
services after the fact by searching logs for a single identifier, the
practical foundation every structured logging and tracing system relies on for
this pattern specifically.

Redelivery count is a signal worth surfacing explicitly rather than only
inferring from broker internals, since a message that is redelivered
repeatedly but never reaches the dead-letter threshold, because the threshold
is set too high, can silently consume consumer capacity for a long time before
anyone notices, which is exactly the poison-message failure mode described in
dimension 11.

Trace propagation health, whether the correlation and trace identifiers on an
outbound Message actually match the inbound Message that caused it, is worth
asserting on directly in integration tests and, in mature systems, checking
continuously via a tracing backend's own gap detection, since a broken
propagation chain is invisible until someone is actively debugging an incident
and finds the trail goes cold.

## 17. Security and privacy implications

A Message's body frequently carries application data that includes personal
information, payment details, authentication tokens, or other regulated data,
and because a Message is designed to be durable, persisted, and potentially
replayed, that data sits at rest inside the broker or channel infrastructure
for as long as the retention policy configures, which is a meaningfully
different exposure window than data that only ever existed for the duration of
a synchronous call.

Encryption in transit between producer, broker, and consumer is table stakes
and is supported natively by every broker cited in dimension 9, TLS for AMQP,
Kafka, and SQS connections. Encryption at rest for the broker's own storage is
a separate, broker-level configuration decision that a Message-based
architecture does not solve by itself, and teams handling regulated data
should verify their specific broker's at-rest encryption is enabled rather
than assuming the Message pattern implies it.

The header, being designed to be readable by generic infrastructure and by
any intermediary that routes or transforms the Message, should never carry
sensitive data directly. a correlation identifier, a message type, a
timestamp, are all safe to leave in cleartext for logging and tracing
purposes, but a customer's email address or a payment token belongs in the
body, encrypted or tokenized at the application layer if the threat model
requires it, specifically because header fields are the fields most likely to
be logged, indexed, and surfaced in dashboards and tracing UIs by generic
tooling that has no awareness of data classification.

Message identifiers used for idempotent deduplication, described in dimension
11, should be generated with enough entropy, a UUID version 4 or a similarly
unguessable value, that an attacker cannot forge a plausible message
identifier to either trigger unwanted deduplication, silently suppressing a
legitimate message, or bypass deduplication to force a replay attack against a
consumer that treats a repeated identifier as authorization to reprocess a
side effect.

Access control on the channel itself, who can publish, who can subscribe, is a
separate concern from the Message pattern but a necessary complement to it,
since a well-formed, correctly headered Message published by an unauthorized
producer is still a security incident. AMQP and Kafka both provide
broker-level authentication and authorization mechanisms for exactly this
reason
([https://kafka.apache.org/documentation/#security_authz](https://kafka.apache.org/documentation/#security_authz),
verified 2026-08-02).

## 18. References

1. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, chapter
   4, "Messaging Systems", page 79, Message, pages 145 to 153, Command
   Message, Document Message, Event Message, page 355, Canonical Data Model,
   page 522, Idempotent Receiver, page 119, Dead Letter Channel.
2. Enterprise Integration Patterns online catalog, Message,
   [https://www.enterpriseintegrationpatterns.com/patterns/messaging/Message.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Message.html),
   verified 2026-08-02.
3. RabbitMQ, AMQP 0-9-1 Model Explained,
   [https://www.rabbitmq.com/tutorials/amqp-concepts](https://www.rabbitmq.com/tutorials/amqp-concepts),
   verified 2026-08-02.
4. Jakarta Messaging 3.1 API, `jakarta.jms.Message`,
   [https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/message](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/message),
   verified 2026-08-02.
5. Apache Kafka, `ProducerRecord` Javadoc,
   [https://kafka.apache.org/38/javadoc/org/apache/kafka/clients/producer/ProducerRecord.html](https://kafka.apache.org/38/javadoc/org/apache/kafka/clients/producer/ProducerRecord.html),
   verified 2026-08-02.
6. Apache Kafka documentation, Semantics of exactly-once,
   [https://kafka.apache.org/documentation/#semantics](https://kafka.apache.org/documentation/#semantics),
   verified 2026-08-02.
7. Apache Kafka documentation, Security, Authorization and ACLs,
   [https://kafka.apache.org/documentation/#security_authz](https://kafka.apache.org/documentation/#security_authz),
   verified 2026-08-02.
8. CloudEvents Specification v1.0.2, CNCF,
   [https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md),
   verified 2026-08-02.
9. AWS SQS Developer Guide, Amazon SQS message metadata,
   [https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-message-metadata.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-message-metadata.html),
   verified 2026-08-02.
10. Confluent documentation, Schema Evolution and Compatibility,
    [https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html),
    verified 2026-08-02.
11. W3C Trace Context Recommendation,
    [https://www.w3.org/TR/trace-context/](https://www.w3.org/TR/trace-context/),
    verified 2026-08-02.
12. Pact documentation, How Pact works,
    [https://docs.pact.io/getting_started/how_pact_works](https://docs.pact.io/getting_started/how_pact_works),
    verified 2026-08-02.
13. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
    Software*, Addison-Wesley, 2003, chapter 4, "Isolating the Domain".
14. Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018, Item 1.

## Code examples

### TypeScript

```typescript
interface MessageHeader {
  messageId: string;
  correlationId: string;
  type: string;
  contentType: string;
  timestamp: number;
}

class Message<T> {
  constructor(
    public readonly header: MessageHeader,
    public readonly body: T,
  ) {}

  static create<T>(type: string, body: T, correlationId?: string): Message<T> {
    return new Message<T>(
      {
        messageId: randomId(),
        correlationId: correlationId ?? randomId(),
        type,
        contentType: "application/json",
        timestamp: Date.now(),
      },
      body,
    );
  }
}

function randomId(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

interface OrderPlaced {
  orderId: string;
  total: number;
}

const seen = new Set<string>();

function idempotentReceive(msg: Message<OrderPlaced>): void {
  if (seen.has(msg.header.messageId)) {
    console.log("duplicate, skipping", msg.header.messageId);
    return;
  }
  seen.add(msg.header.messageId);
  console.log(
    `processing order ${msg.body.orderId} total ${msg.body.total} type=${msg.header.type}`,
  );
}

const outbound = Message.create<OrderPlaced>("order.placed", {
  orderId: "ord-1",
  total: 42.5,
});
idempotentReceive(outbound);
idempotentReceive(outbound);
```

### Python

```python
from __future__ import annotations
from dataclasses import dataclass
from time import time
from uuid import uuid4
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class MessageHeader:
    message_id: str
    correlation_id: str
    type: str
    content_type: str
    timestamp: float


@dataclass(frozen=True)
class Message(Generic[T]):
    header: MessageHeader
    body: T

    @staticmethod
    def create(msg_type: str, body: T, correlation_id: str | None = None) -> "Message[T]":
        return Message(
            header=MessageHeader(
                message_id=str(uuid4()),
                correlation_id=correlation_id or str(uuid4()),
                type=msg_type,
                content_type="application/json",
                timestamp=time(),
            ),
            body=body,
        )


@dataclass(frozen=True)
class OrderPlaced:
    order_id: str
    total: float


_seen: set[str] = set()


def idempotent_receive(msg: Message[OrderPlaced]) -> None:
    if msg.header.message_id in _seen:
        print(f"duplicate, skipping {msg.header.message_id}")
        return
    _seen.add(msg.header.message_id)
    print(
        f"processing order {msg.body.order_id} total {msg.body.total} "
        f"type={msg.header.type}"
    )


if __name__ == "__main__":
    outbound = Message.create("order.placed", OrderPlaced(order_id="ord-1", total=42.5))
    idempotent_receive(outbound)
    idempotent_receive(outbound)
```

### Go

```go
package main

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"time"
)

type MessageHeader struct {
	MessageID     string
	CorrelationID string
	Type          string
	ContentType   string
	Timestamp     int64
}

type Message[T any] struct {
	Header MessageHeader
	Body   T
}

func newID() string {
	b := make([]byte, 8)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

func NewMessage[T any](msgType string, body T, correlationID string) Message[T] {
	if correlationID == "" {
		correlationID = newID()
	}
	return Message[T]{
		Header: MessageHeader{
			MessageID:     newID(),
			CorrelationID: correlationID,
			Type:          msgType,
			ContentType:   "application/json",
			Timestamp:     time.Now().Unix(),
		},
		Body: body,
	}
}

type OrderPlaced struct {
	OrderID string
	Total   float64
}

var seen = map[string]bool{}

func idempotentReceive(msg Message[OrderPlaced]) {
	if seen[msg.Header.MessageID] {
		fmt.Println("duplicate, skipping", msg.Header.MessageID)
		return
	}
	seen[msg.Header.MessageID] = true
	fmt.Printf(
		"processing order %s total %.2f type=%s\n",
		msg.Body.OrderID, msg.Body.Total, msg.Header.Type,
	)
}

func main() {
	outbound := NewMessage("order.placed", OrderPlaced{OrderID: "ord-1", Total: 42.5}, "")
	idempotentReceive(outbound)
	idempotentReceive(outbound)
}
```

The Rust, Swift, Java, Kotlin, and C# samples were not written for this
entry. Message is a data-shape pattern rather than a language-feature
pattern, and the three samples above, TypeScript, Python, and Go, already
demonstrate the pattern across a structurally typed language, a dynamically
typed language, and a statically compiled language with generics, which
covers the range of idiom the pattern actually varies across. All three
samples were run.
