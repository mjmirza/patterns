# Family 07. Enterprise Integration

Origin. Hohpe and Woolf

41 entries, 288,435 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Enterprise Integration

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Aggregator](aggregator.md) | canonical | 5,808 | A system receives several messages that only make sense together, and no single message carries enough information to act on. |
| [Composed Message Processor](composed-message-processor.md) | canonical | 6,044 | A message arrives that logically represents one unit of work, but different parts of that unit of work belong to different, independent systems, and none of those systems can ... |
| [Messaging Bridge](messaging-bridge.md) | canonical | 6,489 | An enterprise settles on messaging as the way applications talk to each other, and that decision solves the coupling problem inside one messaging technology. |

## Enterprise Integration Pattern

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Scatter-Gather](scatter-gather.md) | canonical | 6,922 | A caller needs an answer that no single system holds in full. |

## Enterprise Integration, Messaging Channels

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Datatype Channel](datatype-channel.md) | canonical | 7,421 | A consumer reads a message off a channel and must decide how to process it before it can do anything with the payload. |

## Integration

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Canonical Data Model](canonical-data-model.md) | canonical | 7,238 | An enterprise with N independently developed systems that must exchange data pairwise needs, in the worst case, N times (N minus one) point-to-point translators if each system ... |
| [Claim Check](claim-check.md) | canonical | 8,722 | A component in a message-based system needs to communicate a large amount of data, an image, a video, a document, a bulk export, a machine learning feature vector, a full customer ... |
| [Command Message](command-message.md) | canonical | 6,014 | An application wants another application, or another component in the same system, to perform a specific piece of work. |
| [Content Enricher](content-enricher.md) | canonical | 6,840 | A message arrives at an integration point carrying less data than the next step needs. |
| [Content Filter](content-filter.md) | canonical | 8,464 | A consumer receives a message that is far larger, richer, or more deeply nested than anything it needs, and forwarding or storing that full message creates real cost. |
| [Correlation Identifier](correlation-identifier.md) | canonical | 7,467 | A process sends a message and does not receive its answer over the same connection it used to send it. |
| [Document Message](document-message.md) | canonical | 7,022 | Two systems need to exchange a structured record, such as a customer record, a purchase order, a lab result, or a shipment manifest. |
| [Dynamic Router](dynamic-router.md) | canonical | 7,649 | A message-routing component in a system needs to send a message onward, and the set of places it might send that message to is not fixed at the time the router is built, deployed ... |
| [Event Message](event-message.md) | canonical | 7,042 | An application performs an action that other applications, possibly ones the first application has never heard of and will never know about, need to react to. |
| [Event-Driven Consumer](event-driven-consumer.md) | canonical | 6,039 | A service needs to react when something happens elsewhere in the system, a payment is captured, an order is placed, a file lands in a bucket, a row is updated in another team's ... |
| [Format Indicator](format-indicator.md) | canonical | 6,130 | A message travels from a producer to a consumer, and at some point the consumer must decide how to parse the bytes it received. |
| [Message](message.md) | canonical | 6,901 | Two applications need to exchange information without either one blocking on the other's availability, without either one dictating the other's internal data model, and without a ... |
| [Message Bus](message-bus.md) | canonical | 7,686 | A system starts with two applications that need to exchange data, and a direct point-to-point integration, a script that reads from one database and writes to another, or a ... |
| [Message Channel](message-channel.md) | canonical | 6,008 | Two independently deployed pieces of software need to exchange information, and the team building them does not want a synchronous, point-to-point network call between them. |
| [Message Expiration](message-expiration.md) | canonical | 6,898 | A message carries a request or a piece of data across an asynchronous boundary. |
| [Message Filter](message-filter.md) | canonical | 7,478 | A component sits on a message channel and receives every message that flows past, but it only knows how to handle a subset of them. |
| [Message Sequence](message-sequence.md) | canonical | 6,955 | A producer has one logical unit of data to move across a messaging channel, and the unit is larger than the channel, the broker, or the receiving application can accept as a ... |
| [Messaging Gateway](messaging-gateway.md) | canonical | 7,408 | An application needs to send and receive messages through a messaging system, a message queue, an event bus, a Kafka topic, an AMQP exchange, but the team does not want every part ... |
| [Normalizer](normalizer.md) | canonical | 6,910 | A system receives messages that all describe the same real-world fact, an order was placed, a patient was admitted, a trade was executed, but the messages arrive in several ... |
| [Routing Slip](routing-slip.md) | canonical | 7,757 | A message needs to pass through a chain of processing steps, and the exact membership and order of that chain differs per message, per tenant, or per business rule, rather than ... |

## Integration (Message Routing)

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Resequencer](resequencer.md) | canonical | 7,556 | A producer emits a series of related units, each carrying an explicit position in a sequence, a timestamp, or an ordinal, and the units are meant to be consumed, displayed, or ... |

## Message Construction

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Envelope Wrapper](envelope-wrapper.md) | canonical | 6,361 | An application was built to produce and consume data in its own native format, a flat file, a fixed-width record, a plain XML document with no messaging-specific fields, a CSV row. |

## Message Endpoint

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Messaging Mapper](messaging-mapper.md) | canonical | 7,462 | An application has a domain model, the classes that hold its business state and enforce its business rules, an Order, a Customer, a ShipmentPlan. |

## Message Routing

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Splitter](splitter.md) | canonical | 6,605 | A message arrives that is a container for several logically independent units of work, and the downstream processing needs to happen per unit, not per container. |

## Messaging

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Content-Based Router](content-based-router.md) | canonical | 6,816 | A single logical message stream must be handled by more than one downstream consumer, and which consumer handles a given message depends on data inside that message, not on which ... |
| [Guaranteed Delivery](guaranteed-delivery.md) | canonical | 6,068 | A service publishes an event or sends a command onto a channel and then proceeds as if the message is on its way. |
| [Recipient List](recipient-list.md) | canonical | 7,463 | A single message must reach more than one downstream consumer at once, and the exact SET of consumers that should receive a given message is not fixed at design time. |
| [Request-Reply](request-reply.md) | canonical | 6,624 | A component needs an answer from another component before it can continue, and the two components do not share a process, a thread, or a call stack. |
| [Return Address](return-address.md) | canonical | 7,269 | A requestor sends a message into an asynchronous channel and needs an answer back. |
| [Transactional Client](transactional-client.md) | canonical | 7,869 | A client sends or receives several messages that belong together as one unit of work, and the messaging system offers no help unless the client asks for it explicitly. |

## Messaging Channels

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Dead Letter Channel](dead-letter-channel.md) | canonical | 8,100 | A message oriented system moves work between components through channels rather than through direct calls. |
| [Invalid Message Channel](invalid-message-channel.md) | canonical | 8,163 | A receiver on a messaging channel is written against an expectation. |
| [Point-to-Point Channel](point-to-point-channel.md) | canonical | 6,697 | A system decouples a producer of work from a consumer of work using asynchronous messaging instead of a direct call, for the usual reasons. |

## Messaging Endpoints

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Channel Adapter](channel-adapter.md) | canonical | 7,811 | An application was written to be called, to poll a database, to read a file, or to raise an in-process event. |
| [Polling Consumer](polling-consumer.md) | canonical | 5,802 | An application needs to consume messages from a channel, a queue, a topic partition, or any buffered source of work items, but it needs to control the timing and the volume of ... |

## System Management

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Process Manager](process-manager.md) | canonical | 6,457 | Picture an order fulfillment system built from independently owned services. |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
