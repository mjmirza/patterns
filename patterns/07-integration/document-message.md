---
name: Document Message
slug: document-message
family: 07-integration
category: Integration
aliases: [Data Message, Data Transfer Message]
first_described: "Hohpe, Woolf 2003, Enterprise Integration Patterns"
maturity: canonical
related: [command-message, message, datatype-channel, guaranteed-delivery, invalid-message-channel, dead-letter-channel, messaging-bridge, point-to-point-channel]
incompatible_with: []
verified: 2026-08-02
---

# Document Message

## 1. Name, aliases, and lineage

The canonical name is Document Message. Gregor Hohpe and Bobby Woolf catalogued
it in *Enterprise Integration Patterns. Designing, Building, and Deploying
Messaging Solutions* (Addison-Wesley, 2003), in the Message Construction
chapter, as one of three message-type patterns, alongside Command Message and
Event Message. The book's companion reference site states the intent in one
sentence. "Use a Document Message to reliably transfer a data structure
between applications" (enterpriseintegrationpatterns.com, Document Message,
verified 2026-08-02,
https://www.enterpriseintegrationpatterns.com/patterns/messaging/DocumentMessage.html).
The same page draws the distinguishing line against its sibling patterns. A
Document Message differs from a Command Message because it carries data and
leaves the receiver to decide what to do with it, rather than instructing a
specific action, and it differs from an Event Message in what matters about
the message. "The important part of a Document Message is its content, the
document," where an Event Message is judged by when it arrived and what
happened, not by the shape of its payload.

The name is not seriously contested inside the messaging literature that
descends from the EIP catalog, but the underlying idea is older than the book
and is called by different names in the communities that use it without
citing Hohpe and Woolf directly. In electronic data interchange, the oldest
and largest deployment of this exact pattern, the unit exchanged is called a
transaction set (ASC X12) or a message type (UN/EDIFACT, HL7), and the
vocabulary of "document" is used informally to describe the same thing, a
self-contained structured record handed from one system to another with no
instruction attached. In the .NET messaging frameworks NServiceBus and
MassTransit, which both explicitly separate Commands from Events as first
class message categories, a reply message returned from a request or a plain
data payload that is neither a command nor an event is treated as a third,
unlabelled category. NServiceBus's own documentation states this directly.
"In a request and response pattern, reply messages are neither a command nor
an event," and the framework provides the `NServiceBus.IMessage` marker
interface specifically "for any other message type (e.g., a reply in a
request/response pattern)" (Particular Software, NServiceBus documentation,
Messages, Events, and Commands, verified 2026-08-02,
https://docs.particular.net/nservicebus/messaging/messages-events-commands).
MassTransit follows the same shape with its Request/Response contract, where
the response carries the requested data back to the caller without asking the
caller to do anything with it beyond consuming the payload (MassTransit
documentation, Messages, verified 2026-08-02,
https://masstransit.io/documentation/concepts/messages). Neither framework
uses the words "Document Message," but both implement the same distinction
Hohpe and Woolf named. An instruction is addressed and specific, a fact is
broadcast and timed, and a document is neither, it is a payload whose value is
its content.

## 2. Problem and context

Two systems need to exchange a structured record, such as a customer record,
a purchase order, a lab result, or a shipment manifest. Neither system needs
the other to perform an action right now, and neither system is reporting
that something happened. What is needed is simpler and older than either of
those ideas. A reliable, well-typed transfer of data from a producer that
holds it to a consumer that needs it, decoupled from any synchronous call,
any shared database, and any assumption about what the receiver will do with
the record once it arrives.

This problem shows up first in the batch-integration world that predates
message queues entirely. A retailer sends nightly inventory files to its
suppliers. A hospital sends a lab result to the ordering physician's system.
A bank sends a payment instruction to a correspondent bank. In every one of
these cases the sending system does not know, and does not need to know, what
logic the receiving system will run against the data. It only needs the data
to arrive intact, in a shape the receiver can parse, without loss and without
corruption. The context that produces this pattern is precisely the
combination of three constraints, taken together. The data has structure
that matters, so a raw byte stream will not do. The sender and receiver are
decoupled in time and ownership, so a synchronous RPC call is the wrong
shape. The receiver's behaviour is out of the sender's scope, so the payload
cannot be phrased as an instruction.

The pattern also appears inside a single organisation's own services whenever a producing service needs to hand a data structure to a downstream
service through a message channel rather than a shared database or a direct
call, and the two services deliberately avoid coupling on behaviour. A
pricing service that publishes updated price records for a catalog service to
ingest is issuing Document Messages even though both services live in the
same deployment.

## 3. Forces

**Coupling versus behavioural specificity.** A Command Message couples the
sender to a specific action name and, usually, a specific receiver's
capability. A Document Message avoids that coupling entirely, because the
sender publishes a fact-shaped payload and the receiver decides what it means
to consume it. This buys flexibility, since the same document can feed
multiple consumers with different interpretations, at the cost of losing the
guarantee that anything will actually happen when the document arrives.

**Content integrity versus timing.** The EIP reference page states this
directly for Document Message. Successful transfer of the content is the
priority, and timing is comparatively unimportant, in contrast to an Event
Message, where staleness can make the message meaningless. This changes which
reliability mechanisms matter. Guaranteed Delivery is usually needed for a
Document Message because a lost purchase order or a lost lab result is a real
business failure, but Message Expiration is usually not needed, because an
old but intact document is still often useful (an old price list is stale but
not garbage; an old command to cancel an order that arrives after the order
shipped is actively wrong).

**Schema stability versus evolution.** Because the receiver interprets the
document independently of the sender, the schema of the document is a
contract in itself, arguably a stronger contract than a command's parameter
list, because more consumers depend on it and depend on it for longer. This
pushes toward strict typing (see Datatype Channel) and versioned schemas, and
against loose, ad hoc payload shapes that would be tolerable for a one-off
command between two systems that deploy together.

**Idempotency and reprocessing versus simplicity.** A document that is
delivered twice, whether through at-least-once delivery, a retried batch job,
or a redelivered dead letter, must not corrupt the receiver's state if
processed twice. Building idempotent document ingestion, keyed by a document
identifier or a natural business key, adds engineering cost that a naive
implementation skips, at the cost of duplicate records or duplicate side
effects in production.

**Cardinality of consumers.** A Document Message often has more than one
consumer, because the data itself, not an instruction to one owner, is the
valuable thing. This pushes toward publish-subscribe channels or file drops
that multiple systems can read, in contrast to Command Message's typical
point-to-point addressing to a single, specific handler.

## 4. Applicability and non-applicability

Use a Document Message when:

- Two systems need to exchange a structured record and neither one needs to
  instruct the other's behaviour, only supply data.
- The payload's content is what matters, and exact delivery timing is
  secondary, so long as the content eventually arrives intact.
- Multiple, possibly unrelated consumers might read the same data
  independently, each interpreting it in their own domain terms.
- The two systems are owned by different teams, organisations, or vendors, so
  behavioural coupling, in the form of a Command Message naming a specific
  operation, would be brittle or organisationally inappropriate, as in
  supplier-to-retailer EDI or bank-to-bank payment instructions.
- The data has a natural, stable shape that both sides can agree on as a
  schema, independent of any single interaction (a customer record, an
  invoice, a shipment manifest).
- Batch or file-based transfer is acceptable or preferred, because a document
  transfer does not require synchronous acknowledgement of an action being
  taken.

Do not use a Document Message when:

- The sender needs the receiver to perform a specific, named action right
  now. That is a Command Message, and disguising an instruction as a document
  (an order with a status field set to cancelled, hoping the receiver acts on
  it) forces every consumer to reverse-engineer intent from data, which is
  fragile and hides the real contract. Send a Command Message instead and let
  its name state the intent plainly.
- The receiver needs to know precisely when something happened, and stale
  information is actively harmful, such as a stock price feed, a fraud
  alert, or a sensor reading that only matters within a tight window. That is
  closer to an Event Message, where recency and correlation to a moment in
  time outweigh the payload's raw content.
- The interaction is fundamentally synchronous and the caller needs an
  immediate return value to continue its own logic. A blocking call or a
  Command Message paired with a reply channel and an explicit timeout fits
  that need better than a fire-and-forget document drop.
- The payload has no independent value outside the specific interaction that
  produced it, such as an internal correlation token or a lock-acquisition
  request. Wrapping ephemeral, interaction-scoped state in a Document Message
  format adds schema overhead the data does not need.
- The two systems already share a transactional boundary, such as the same
  database or the same process, and messaging would introduce eventual
  consistency where strong consistency is available and cheaper. Passing
  data through a shared table or a direct method call is simpler and does not
  need this pattern's channel, schema, and delivery-guarantee machinery.

## 5. Structure

**Producer.** The system, service, or process that holds the data and is the
authoritative source for it at the moment of transfer. The producer decides
what to publish and when, but does not decide, and should not encode, what
the consumer will do with it.

**Document Message.** The message itself. Its defining characteristic is that
its body is the data structure being transferred, in a schema both sides
agree on, with no imperative verb or specific action encoded in the message
type. The message may carry metadata, such as a correlation identifier, a
document identifier, a version stamp, or a timestamp of production, as
headers, but the payload is the document.

**Message Channel.** The transport the Document Message travels over, either
a point-to-point queue when there is exactly one consumer that owns the
record's next step, or a publish-subscribe topic when multiple independent
consumers each need their own copy of the same document. See Point-to-Point
Channel and the Message Bus pattern in this family for the channel shapes
this typically rides on.

**Datatype Channel.** In practice, Document Messages of one type are almost
always segregated onto a channel dedicated to that document type, so
consumers can subscribe by schema without inspecting every message's content
to find the ones they care about. This is the Datatype Channel pattern
applied to a Document Message stream.

**Consumer(s).** One or more systems that read the document and decide,
independently, how to interpret and act on it. A consumer's logic is entirely
its own; the producer has no visibility into it and no dependency on it. This
is the structural feature that distinguishes Document Message from Command
Message, where the receiver's action is effectively part of the contract.

**Schema or Contract.** The agreed shape of the document, whether an XSD, a
JSON Schema, a protobuf definition, an X12 transaction set definition, or an
HL7 segment structure. The schema is the load-bearing artifact in this
pattern; it is what lets producer and consumer evolve independently while
still agreeing on meaning.

## 6. ASCII structure diagram

```
+---------------------------+
| Producer (holds the data) |
+---------------------------+
           | Document Message
           | { schema-typed data payload }
           v
+---------------------------------------+
| Message Channel                       |
| (point-to-point or publish-subscribe) |
+---------------------------------------+
           |
     +-----+-----+
     |           |
+---------------------+ +---------------------+
| Consumer A          | | Consumer B          |
| interprets the      | | interprets the      |
| document in its     | | document in its     |
| own domain          | | own domain          |
+---------------------+ +---------------------+

Producer knows only that a well-formed <Type> document was
published. Producer does NOT know or care what A or B do with it.
```

## 7. Dynamics

```
Producer                Channel                  Consumer A            Consumer B
  |                        |                          |                     |
  |-- publish Document --->|                          |                     |
  |   (schema: Invoice)    |                          |                     |
  |                        |-- deliver copy --------->|                     |
  |                        |-- deliver copy ------------------------------->|
  |                        |                          |                     |
  |                        |               [validate against schema]        |
  |                        |               [assign meaning locally.         |
  |                        |                A files it in ledger,           |
  |                        |                B triggers a reconciliation     |
  |                        |                job, neither tells the other]   |
  |                        |                          |                     |
  |                        |<-- ack / commit ----------|                     |
  |                        |<-- ack / commit ------------------------------|
  |                        |                          |                     |
  |         [Producer receives NO signal about what A or B did with it.     |
  |          Only delivery/consumption acknowledgement, never an outcome.]  |
```

The critical dynamic to notice is the asymmetry of knowledge after delivery.
In a request-reply interaction the caller learns the outcome of its request.
In a Document Message flow the producer typically learns only that the
channel accepted or delivered the message, via Guaranteed Delivery's
acknowledgement mechanics, not what any consumer chose to do with the
document's content. If the producer needs to know the outcome, that is a
separate, explicit interaction, often implemented as the consumer publishing
its own Document Message or Event Message back, never as an implicit return
value of the original transfer.

## 8. Implementation variants

**Point-to-point document drop.** A single, known consumer owns the next
processing step for the document, for example a specific downstream system
that ingests purchase orders. Implemented over a point-to-point queue, one
document per message, with the consumer removing the message from the queue
once processed. This is the shape most EDI-over-AS2 and EDI-over-VAN, value
added network, integrations still use today, where the transport delivers a
file that is functionally a batched Document Message.

**Publish-subscribe document broadcast.** Multiple consumers each need an
independent copy of the same document, and the producer does not know or
enumerate them in advance. Implemented over a topic, such as a Kafka topic,
an AMQP fanout exchange, or an SNS topic, with each consumer maintaining its
own offset or subscription, so one consumer's processing speed or failure
does not affect another's.

**Batched or file-based document transfer.** Rather than one message per
document, many documents are grouped into a single file or batch
transmission, such as a nightly EDI 850 purchase-order batch or an HL7 v2
message file. The "message" in the messaging sense is the file transfer
event; the individual documents inside it are logically still Document
Messages, aggregated for transport efficiency. This variant trades
per-document latency for throughput and simpler reconciliation, one file, one
acknowledgement, thousands of records.

**Schema-first, contract-tested transfer.** The document's schema is
published and versioned independently of any single producer or consumer,
such as an X12 implementation guide, an HL7 conformance profile, or a shared
protobuf or Avro schema registry. Producers and consumers are each
contract-tested against the schema in isolation, which is what lets Document
Message scale to many independent organisations exchanging the same document
type without a central coordinator.

**Enveloped document with routing metadata.** The document payload is
wrapped in an envelope carrying routing and correlation metadata, a Message
Header in the EIP sense, holding sender identity, document type, correlation
ID, and timestamp, separate from the business payload itself, so
infrastructure such as routers, dead letter handling, and audit logging can
inspect the envelope without parsing or depending on the document's internal
schema. This is close to universal in production EDI, HL7, and
financial-messaging (SWIFT MT/MX) implementations, because the
envelope-payload separation is what lets the transport layer evolve
independently of the business document format.

## 9. Known production uses

**ASC X12 electronic data interchange.** ASC X12, chartered by the American
National Standards Institute, "develops and maintains EDI standards which
drive business processes globally," and "defines and maintains transaction
sets that establish the data content exchanged for specific business
purposes," supporting "billions of daily transactions" across supply chain,
transportation, healthcare, insurance, finance, and government (ASC X12,
About X12, verified 2026-08-02, https://x12.org/about). Each X12 transaction
set, such as an 850 purchase order, an 810 invoice, or a 997 functional
acknowledgement, is a Document Message in the literal sense the EIP catalog
describes. A structured data record transferred between trading partners,
with the receiver responsible for its own interpretation of the content, and
no instruction embedded in the transfer itself.

**NServiceBus, plain messages distinct from Commands and Events.** Particular
Software's NServiceBus documentation explicitly separates message categories,
stating "a command tells a service to do something" and "an event signifies
that something has happened," while reserving a third, unnamed category,
implemented via the `NServiceBus.IMessage` marker interface, "for any other
message type (e.g., a reply in a request/response pattern)," and states
directly that "in a request and response pattern, reply messages are neither
a command nor an event" (Particular Software, NServiceBus documentation,
Messages, Events, and Commands, verified 2026-08-02,
https://docs.particular.net/nservicebus/messaging/messages-events-commands).
That third category, a payload transferred for its content rather than to
instruct or announce, is the Document Message concept implemented as a
concrete framework construct in a widely deployed .NET service bus.

**MassTransit request/response payloads.** MassTransit's documentation
likewise separates Commands, "a command tells a service to do something, and
typically a command should only be consumed by a single consumer," and
Events, "an event signifies that something has happened," from
request/response messages, where "requests initiate a message from a client
to a service expecting a reply, while responses return results back to the
requesting client," with response messages carrying the requested data back
without instructing further action (MassTransit documentation, Messages,
verified 2026-08-02,
https://masstransit.io/documentation/concepts/messages). The response side of
that exchange is a Document Message. Its value is the data it carries, not an
imperative attached to it, matching the EIP definition that the important
part of a Document Message is its content.

## 10. Consequences

Positive.

- Decouples producer and consumer completely from each other's behaviour, so
  the producer can add or remove consumers without any change to what it
  publishes, and consumers can independently evolve how they interpret the
  same document.
- Well suited to many-to-many integration across organisational boundaries,
  where no single party can or should dictate another's internal processing
  logic, which is why it is the main choice for EDI, HL7, and financial
  messaging.
- Supports batching and file-based transport naturally, because the pattern
  does not assume per-message synchronous handling, which keeps throughput
  high for bulk transfers.
- Makes the schema, not the interaction, the primary contract, which is
  easier to version, document, and test in isolation than a behavioural
  contract tied to a specific RPC-style call.
- Plays well with Guaranteed Delivery and at-least-once transports, since a
  document's value does not degrade the way an Event Message's timeliness
  does, so retried or delayed delivery is rarely catastrophic on its own.

Negative.

- The producer has no visibility into, and typically no feedback about, what
  any consumer did with the document. If the business process needs a
  confirmed outcome, this pattern alone cannot provide it, and an additional
  explicit interaction, such as a return document or a status query, has to
  be designed in.
- Because multiple, independently evolving consumers may depend on the same
  document schema, a breaking schema change becomes expensive to coordinate;
  the coupling that was removed from behaviour reappears as coupling on data
  shape, and it can be equally brittle if the schema is not versioned
  deliberately.
- At-least-once or batched redelivery means consumers must handle duplicate
  documents; a naive consumer that is not idempotent will double-process,
  double-book, or double-charge on a redelivered document.
- Because the pattern deliberately avoids embedding intent, a reader
  inspecting a Document Message in isolation cannot tell what will happen to
  it; understanding the system's behaviour requires reading every consumer,
  which is a real cost in operational and onboarding terms compared to a
  self-describing Command Message.
- Large or high-volume documents, such as bulk EDI batches or large HL7
  files, put pressure on channel throughput, storage, and validation cost in
  a way a small, focused Command Message rarely does.

## 11. Failure modes and misuse

Judgement note. This dimension draws on operational experience with
document-oriented integration (EDI, HL7, message-bus payload exchange) and is
stated as practice, not as a sourced claim about any single named system.

**Symptom.** A downstream consumer silently drops or ignores fields it does
not recognise, and months later a business report is quietly missing data.
**Cause.** The consumer deserialises the document with a permissive parser
that tolerates unknown or extra fields without alerting anyone, so a
producer's schema addition, intended to be backward compatible, is invisible
to a consumer that actually needed the new field. **Fix.** Treat schema
evolution as a contract change requiring explicit acknowledgement from known
consumers where the field is load-bearing, and add monitoring on unexpected
or unused fields rather than assuming silent tolerance is safe.

**Symptom.** The same invoice, order, or record appears twice in the
receiving system after a network blip or a redeploy of the messaging
infrastructure. **Cause.** The transport provides at-least-once delivery, a
normal and correct choice for reliability, and the consumer processes the
document as if it were guaranteed to arrive exactly once, with no
deduplication key. **Fix.** Give every document a stable, producer-assigned
identifier and make the consumer's processing idempotent against it,
typically an upsert keyed on that identifier rather than a blind insert.

**Symptom.** A Document Message channel becomes the accidental place where
teams stuff imperative logic, such as a status field meaning please cancel
this, and nobody can find where the actual cancellation is triggered because
it is buried in a consumer's interpretation of a data field. **Cause.** The
boundary between Document Message and Command Message eroded over time as
teams reused an existing document schema and channel instead of introducing
a proper Command Message, because the channel was already there and adding a
field felt cheaper than wiring a new one. **Fix.** Treat any field whose sole
purpose is to instruct behaviour as a signal that a Command Message is the
correct pattern, and split it out, even at the short-term cost of a new
channel.

**Symptom.** Schema validation passes but the document is functionally
garbage, for example every amount field is zero because an upstream currency
conversion step failed silently. **Cause.** Schema validation only checks
structure and type, never business-level correctness, and teams conflate
parsing successfully with being valid. **Fix.** Add domain-level validation
as a distinct step after schema validation, and route documents that fail
domain validation to an Invalid Message Channel, never silently accept them
into the happy path.

**Symptom.** A large batch file transfer, such as an EDI 850 batch or an HL7
file with thousands of segments, partially fails, and operators cannot tell
which individual documents inside the batch succeeded and which did not.
**Cause.** The batch is treated as a single unit of delivery at the
transport level, but individual documents inside it have independent
business validity, and the processing pipeline does not track per-document
status inside the batch. **Fix.** Assign and track a status per logical
document inside the batch, not only per batch file, and surface partial
failure explicitly rather than succeed-or-fail-the-whole-file.

## 12. Trade-off matrix

| Force | Document Message | Command Message | Event Message | Shared Database |
|---|---|---|---|---|
| Coupling on receiver behaviour | None, receiver interprets freely | High, sender names the action | Low, but implies something happened | High, shared schema and transaction boundary |
| Coupling on data shape | High, schema is the contract | Moderate, parameters are the contract | Low to moderate, event shape often smaller | Very high, physical schema shared directly |
| Sensitivity to delivery timing | Low, content matters more than timing | Moderate to high, stale commands can be wrong | High, stale events can be meaningless | Not applicable, always current within a transaction |
| Number of independent consumers | Naturally many | Typically one, the addressed handler | Naturally many | Many, but reading the same live state |
| Feedback to sender about outcome | None by default | Often, via reply or acknowledgement | None by default | Immediate, via the same transaction |
| Fit for cross-organisation integration | Strong, most common real-world use | Weak, implies operational authority over another org | Moderate | Weak, requires shared ownership of the database |
| Fit for at-least-once, batched transport | Strong | Moderate, duplicate commands can be dangerous | Weak, duplicates confuse what happened when | Not applicable |

## 13. Related and incompatible patterns

**Command Message.** The direct sibling pattern in the EIP Message
Construction chapter. The two are best understood as opposite ends of the
same spectrum. A Command Message asks for behaviour, a Document Message
supplies data. A single integration often uses both, for example a Command
Message triggers a process that later emits a Document Message carrying the
result.

**Message (the base pattern).** Document Message is a specialisation of the
general Message pattern in this family; every Document Message is a Message,
but not every Message is a Document Message, since a Message may equally be
a Command Message or an Event Message.

**Datatype Channel.** Document Messages of a given type are almost always
routed over a channel dedicated to that type, so this pattern composes
directly with Datatype Channel to let consumers subscribe by schema rather
than by filtering message content.

**Guaranteed Delivery.** Because the content of a Document Message is
typically what matters, and losing a document is a real business failure,
such as a lost invoice or a lost lab result, Document Message integrations
very commonly pair with Guaranteed Delivery so the transport does not
silently drop messages.

**Invalid Message Channel and Dead Letter Channel.** A document that fails
schema or domain validation needs somewhere to go that is not the normal
processing path. Invalid Message Channel and Dead Letter Channel are the
standard destinations for a Document Message that a consumer cannot or will
not process, and pairing them is close to mandatory in any production-grade
document integration.

**Messaging Bridge.** Document Message content frequently needs to cross
between two different messaging infrastructures, such as an internal message
bus and an external EDI VAN, which is exactly the job of Messaging Bridge;
the bridge typically preserves the document's schema while translating the
envelope and transport.

**Point-to-Point Channel and Publish-Subscribe Channel.** The channel shape a
Document Message rides on is chosen based on cardinality of consumers, as
described in dimension 5; Document Message does not mandate one channel type
over the other, unlike some patterns that assume a specific channel
cardinality by definition.

Incompatible with. No pattern is fundamentally incompatible with Document
Message at the structural level; the closest tension is with patterns that
assume synchronous, immediate feedback to the caller, such as a direct RPC
call pattern or a blocking read-your-writes access pattern, because Document
Message's default dynamics provide no return value to the producer, and
retrofitting synchronous feedback onto a Document Message flow usually means
introducing a separate reply mechanism rather than treating the pattern
itself as request-reply.

## 14. Refactoring path in and out

**Introducing a Document Message into code that currently shares a
database.** Start by identifying the data structure two systems both need,
independent of any specific interaction; this is usually easier than it
sounds because the structure already exists as a table, a DTO, or an API
response shape. Define an explicit schema for that structure separate from
the internal representation either system uses, such as an XSD, a JSON
Schema, or a versioned class, so the two systems are not coupled to each
other's internal storage format, only to the published schema. Introduce a
Message Channel, a queue or topic, and have the producing system publish the
structure onto it whenever the underlying data changes or on the cadence the
business process requires, using Guaranteed Delivery if the loss of a
document would be a real problem. Have the consumer read from the channel and
build its own internal representation from the schema, deliberately not
sharing code or types with the producer beyond the published contract. Once
the consumer's read path works off the channel, remove its direct read access
to the producer's database, completing the decoupling; this final step is
where most of the actual coupling reduction lands, and it should not be
skipped merely because the messaging path works.

**Refactoring a misused Command Message into a proper Document Message.**
When a Command Message has accumulated so many optional, mutually exclusive
fields that it is really carrying data for several different receiver-decided
outcomes rather than one clear instruction, this is the sign the message
should be split. Identify which fields are the actual instruction, the verb,
the intended action, and which are supporting data the receiver needs to
carry out or interpret that instruction. Extract the supporting data into a
separate Document Message schema referenced by the Command Message, by
identifier or by embedding, and reduce the Command Message itself back to a
small, clearly named instruction. Confirm each existing consumer can still
distinguish what it is being asked to do from what data it needs to do it,
which is the property that was eroding before the refactor.

**Removing a Document Message when it stops earning its place.** If a
Document Message channel has, over time, collapsed to exactly one producer
and exactly one consumer, both owned by the same team, with no cross-team or
cross-organisation boundary left to warrant the decoupling, consider
collapsing the channel into a direct call or a shared data access path.
Verify first that no other consumer has quietly subscribed to the same
channel, a common surprise in publish-subscribe deployments; if the
verification confirms single ownership on both ends, replace the
publish/consume pair with a direct function call or a Domain Event within
the same bounded context, and retire the channel, its schema versioning, and
its dead-letter handling as dead operational weight.

## 15. Testing and verification

Judgement note. This dimension is drawn from practice testing document-based
and message-bus integrations and is stated as engineering reasoning, not as
a sourced claim.

Schema conformance is the first and cheapest test layer. Validate that a
producer's output and a consumer's expected input both conform to the same
published schema version, ideally as an automated contract test that runs in
CI against the schema registry or schema file directly, independent of any
running instance of the other system. This catches the most common
production failure, schema drift, before it ever reaches a real channel.

Consumer-driven contract testing, in the style popularised by tools such as
Pact, is a natural fit for Document Message because the pattern already
separates producer and consumer; a consumer can publish the shape of the
document it actually depends on, and the producer's test suite verifies it
still satisfies every registered consumer's contract before deploying a
schema change, catching breaking changes before they reach a shared channel
in production rather than after.

Idempotency must be tested explicitly, not assumed. Replay the exact same
document, same identifier, same content, into a consumer twice in a test and
assert the resulting state is identical to a single delivery, which is the
concrete test for the duplicate-delivery failure mode described in dimension
11.

Invalid and malformed document handling should be tested as a first-class
case, not an afterthought. Feed a consumer a document that fails schema
validation and one that passes schema validation but fails a business rule,
and assert both are routed to the correct handling path, such as an Invalid
Message Channel, rather than either crashing the consumer or being silently
accepted.

For channel-level testing, a test double for the Message Channel itself, an
in-memory queue, a local broker instance, or a broker's official test kit where one exists, lets the producer's publishing logic and the consumer's
receiving logic each be tested against a realistic channel contract without
needing the full production broker, while still exercising serialization and
deserialization of the actual document schema, which is the part most likely
to break silently if it is mocked away entirely.

## 16. Observability signals

A healthy Document Message integration shows a small, boring set of signals.
Publish rate roughly matching expected business volume with no unexplained
spikes or drops, consumption lag, the age of the oldest unprocessed document
on the channel, staying within an agreed bound, and a near-zero rate of
messages landing on an Invalid Message Channel or Dead Letter Channel.

Track publish count and consume count per document type separately, not only
per channel, because a channel carrying multiple document types can mask a
single type silently failing to be produced or consumed while the channel's
aggregate throughput still looks normal.

Track schema validation failure rate as its own metric, distinct from
downstream business validation failure rate, since a rising trend in schema
failures usually points to a producer that deployed a breaking change, while
a rising trend in business validation failures usually points to a data
quality problem upstream of the schema, and conflating the two in one metric
hides which team needs to act.

Track end-to-end latency from document production to consumer acknowledgement
per document type, since a Document Message that is meant to be near-real-time,
such as a price update, and one that is meant to be batched, such as a
nightly reconciliation file, have very different healthy baselines, and a
single alerting threshold across both will either be too noisy or too blind.

For batch or file-based variants, track documents-per-batch alongside
batch-level success or failure, since a batch that succeeded at the transport
level can still have failed for a meaningful fraction of the individual
documents inside it, the exact failure mode described in dimension 11;
per-document status inside a batch is the signal that exposes this rather
than hides it.

A failing Document Message pipeline typically shows one of two shapes on a
dashboard. A growing backlog on the channel with flat or falling consume
rate, indicating a stuck or crashed consumer, or a flat publish rate that has
dropped to zero while upstream business activity has not, indicating a
producer that has stopped publishing, often silently, because the failure is
in the publish call itself rather than in the business logic that would
otherwise be monitored directly.

## 17. Security and privacy implications

Document Messages frequently carry the most sensitive payloads in an
integration environment precisely because their whole purpose is transferring
data, not instructions, whether customer records, financial transaction
details, health records, or payment instructions. This makes the pattern a
natural target for data classification and encryption controls that a small
Command Message, which may carry only an identifier and a verb, does not need
to the same degree.

Payload-level encryption, not only transport-level encryption such as TLS on
the channel connection, is often warranted for Document Messages carrying
regulated data, for example health records under HL7 or payment data under
financial messaging standards, because the message may be persisted at rest
on a broker, in a dead letter queue, or in an audit log for a period after
transport, and transport encryption alone does not protect data at rest in
those locations.

Because Document Messages are often delivered to multiple independent
consumers (dimension 5), access control has to be enforced per consumer at
the channel or topic level, not assumed from the producer's original intent;
a publish-subscribe topic that was set up for one legitimate consumer can
silently become readable by a second subscriber with different data-handling
obligations if topic-level authorisation is not explicit.

Schema validation, in addition to its correctness role (dimension 15), is a
security control in its own right. An unvalidated document is a plausible
injection vector into downstream systems, particularly when the document's
fields are later used to construct queries, file paths, or commands in a
consumer's processing logic, so schema and input validation at the boundary
where a document is deserialised is the correct place to stop this rather
than in each individual consumer's business logic.

Audit and retention requirements attach directly to the document's content
in many regulated domains, such as financial transaction messages or health
records, which means dead-letter and invalid-message handling for a Document
Message pipeline needs to satisfy the same retention and access controls as
the primary channel, not be treated as an operational side path exempt from
compliance scope; a document that failed processing and landed in a dead
letter queue is still the same regulated data it was before it failed.

## 18. References

1. Hohpe, Gregor, and Bobby Woolf. *Enterprise Integration Patterns.
   Designing, Building, and Deploying Messaging Solutions.* Addison-Wesley,
   2003. Message Construction chapter, Document Message pattern.
2. Enterprise Integration Patterns companion site, Document Message. Verified
   2026-08-02.
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/DocumentMessage.html
3. Enterprise Integration Patterns companion site, Command Message. Verified
   2026-08-02.
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/CommandMessage.html
4. ASC X12, About X12. Verified 2026-08-02. https://x12.org/about
5. Particular Software, NServiceBus documentation, Messages, Events, and
   Commands. Verified 2026-08-02.
   https://docs.particular.net/nservicebus/messaging/messages-events-commands
6. MassTransit documentation, Messages. Verified 2026-08-02.
   https://masstransit.io/documentation/concepts/messages

## Code examples

Three languages follow the same shape: a producer validates an
`InvoiceDocument` against a schema, publishes it once on a `DocumentChannel`,
and two independent consumers, a ledger and a reconciliation total, each
interpret the same document their own way. Publishing the same document
twice demonstrates the idempotent-consumption fix from dimension 11, since
both consumers deduplicate by `documentId` and the second publish changes
neither the ledger count nor the reconciliation total.

```typescript
interface InvoiceDocument {
  documentId: string;
  invoiceNumber: string;
  amountCents: number;
  currency: string;
}

function validate(doc: InvoiceDocument): string[] {
  const errors: string[] = [];
  if (!doc.documentId) errors.push("documentId is required");
  if (!doc.invoiceNumber) errors.push("invoiceNumber is required");
  if (doc.amountCents < 0) errors.push("amountCents must not be negative");
  if (!doc.currency) errors.push("currency is required");
  return errors;
}

class DocumentChannel<T> {
  private subscribers: Array<(doc: T) => void> = [];

  subscribe(handler: (doc: T) => void): void {
    this.subscribers.push(handler);
  }

  publish(doc: T): void {
    for (const handler of this.subscribers) {
      handler(doc);
    }
  }
}

class LedgerConsumer {
  private seen = new Set<string>();
  private ledger: InvoiceDocument[] = [];

  handle(doc: InvoiceDocument): void {
    if (this.seen.has(doc.documentId)) {
      return;
    }
    this.seen.add(doc.documentId);
    this.ledger.push(doc);
  }

  count(): number {
    return this.ledger.length;
  }
}

class ReconciliationConsumer {
  private totalCents = 0;
  private seen = new Set<string>();

  handle(doc: InvoiceDocument): void {
    if (this.seen.has(doc.documentId)) {
      return;
    }
    this.seen.add(doc.documentId);
    this.totalCents += doc.amountCents;
  }

  total(): number {
    return this.totalCents;
  }
}

function main(): void {
  const channel = new DocumentChannel<InvoiceDocument>();
  const ledger = new LedgerConsumer();
  const reconciliation = new ReconciliationConsumer();

  channel.subscribe((doc) => ledger.handle(doc));
  channel.subscribe((doc) => reconciliation.handle(doc));

  const invoice: InvoiceDocument = {
    documentId: "inv-2026-0001",
    invoiceNumber: "INV-1001",
    amountCents: 15000,
    currency: "EUR",
  };

  const errors = validate(invoice);
  if (errors.length > 0) {
    throw new Error(`invalid document: ${errors.join(", ")}`);
  }

  channel.publish(invoice);
  channel.publish(invoice);

  if (ledger.count() !== 1) {
    throw new Error(`expected ledger count 1, got ${ledger.count()}`);
  }
  if (reconciliation.total() !== 15000) {
    throw new Error(`expected total 15000, got ${reconciliation.total()}`);
  }

  console.log(`ledger entries: ${ledger.count()}, reconciliation total: ${reconciliation.total()}`);
}

main();
```

```python
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class InvoiceDocument:
    document_id: str
    invoice_number: str
    amount_cents: int
    currency: str


def validate(doc: InvoiceDocument) -> list[str]:
    errors: list[str] = []
    if not doc.document_id:
        errors.append("document_id is required")
    if not doc.invoice_number:
        errors.append("invoice_number is required")
    if doc.amount_cents < 0:
        errors.append("amount_cents must not be negative")
    if not doc.currency:
        errors.append("currency is required")
    return errors


class DocumentChannel:
    def __init__(self) -> None:
        self._subscribers: list[Callable[[InvoiceDocument], None]] = []

    def subscribe(self, handler: Callable[[InvoiceDocument], None]) -> None:
        self._subscribers.append(handler)

    def publish(self, doc: InvoiceDocument) -> None:
        for handler in self._subscribers:
            handler(doc)


class LedgerConsumer:
    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._ledger: list[InvoiceDocument] = []

    def handle(self, doc: InvoiceDocument) -> None:
        if doc.document_id in self._seen:
            return
        self._seen.add(doc.document_id)
        self._ledger.append(doc)

    def count(self) -> int:
        return len(self._ledger)


class ReconciliationConsumer:
    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._total_cents = 0

    def handle(self, doc: InvoiceDocument) -> None:
        if doc.document_id in self._seen:
            return
        self._seen.add(doc.document_id)
        self._total_cents += doc.amount_cents

    def total(self) -> int:
        return self._total_cents


def main() -> None:
    channel = DocumentChannel()
    ledger = LedgerConsumer()
    reconciliation = ReconciliationConsumer()

    channel.subscribe(ledger.handle)
    channel.subscribe(reconciliation.handle)

    invoice = InvoiceDocument(
        document_id="inv-2026-0001",
        invoice_number="INV-1001",
        amount_cents=15000,
        currency="EUR",
    )

    errors = validate(invoice)
    if errors:
        raise ValueError(f"invalid document: {', '.join(errors)}")

    channel.publish(invoice)
    channel.publish(invoice)

    assert ledger.count() == 1, f"expected ledger count 1, got {ledger.count()}"
    assert reconciliation.total() == 15000, f"expected total 15000, got {reconciliation.total()}"

    print(f"ledger entries: {ledger.count()}, reconciliation total: {reconciliation.total()}")


if __name__ == "__main__":
    main()
```

```go
package main

import (
	"errors"
	"fmt"
)

type InvoiceDocument struct {
	DocumentID    string
	InvoiceNumber string
	AmountCents   int
	Currency      string
}

func validate(doc InvoiceDocument) error {
	if doc.DocumentID == "" {
		return errors.New("documentId is required")
	}
	if doc.InvoiceNumber == "" {
		return errors.New("invoiceNumber is required")
	}
	if doc.AmountCents < 0 {
		return errors.New("amountCents must not be negative")
	}
	if doc.Currency == "" {
		return errors.New("currency is required")
	}
	return nil
}

type DocumentChannel struct {
	subscribers []func(InvoiceDocument)
}

func (c *DocumentChannel) Subscribe(handler func(InvoiceDocument)) {
	c.subscribers = append(c.subscribers, handler)
}

func (c *DocumentChannel) Publish(doc InvoiceDocument) {
	for _, handler := range c.subscribers {
		handler(doc)
	}
}

type LedgerConsumer struct {
	seen   map[string]bool
	ledger []InvoiceDocument
}

func NewLedgerConsumer() *LedgerConsumer {
	return &LedgerConsumer{seen: make(map[string]bool)}
}

func (l *LedgerConsumer) Handle(doc InvoiceDocument) {
	if l.seen[doc.DocumentID] {
		return
	}
	l.seen[doc.DocumentID] = true
	l.ledger = append(l.ledger, doc)
}

func (l *LedgerConsumer) Count() int {
	return len(l.ledger)
}

type ReconciliationConsumer struct {
	seen       map[string]bool
	totalCents int
}

func NewReconciliationConsumer() *ReconciliationConsumer {
	return &ReconciliationConsumer{seen: make(map[string]bool)}
}

func (r *ReconciliationConsumer) Handle(doc InvoiceDocument) {
	if r.seen[doc.DocumentID] {
		return
	}
	r.seen[doc.DocumentID] = true
	r.totalCents += doc.AmountCents
}

func (r *ReconciliationConsumer) Total() int {
	return r.totalCents
}

func main() {
	channel := &DocumentChannel{}
	ledger := NewLedgerConsumer()
	reconciliation := NewReconciliationConsumer()

	channel.Subscribe(ledger.Handle)
	channel.Subscribe(reconciliation.Handle)

	invoice := InvoiceDocument{
		DocumentID:    "inv-2026-0001",
		InvoiceNumber: "INV-1001",
		AmountCents:   15000,
		Currency:      "EUR",
	}

	if err := validate(invoice); err != nil {
		panic(err)
	}

	channel.Publish(invoice)
	channel.Publish(invoice)

	if ledger.Count() != 1 {
		panic(fmt.Sprintf("expected ledger count 1, got %d", ledger.Count()))
	}
	if reconciliation.Total() != 15000 {
		panic(fmt.Sprintf("expected total 15000, got %d", reconciliation.Total()))
	}

	fmt.Printf("ledger entries: %d, reconciliation total: %d\n", ledger.Count(), reconciliation.Total())
}
```
