# Family 07. Enterprise Integration

Origin. Hohpe and Woolf

54 entries, 386,315 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Enterprise Integration

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Aggregator](aggregator.md) | canonical | 5,820 | A system receives several messages that only make sense together, and no single message carries enough information to act on. |
| [Composed Message Processor](composed-message-processor.md) | canonical | 6,057 | A message arrives that logically represents one unit of work, but different parts of that unit of work belong to different, independent systems, and none of those systems can ... |
| [Message History](message-history.md) | canonical | 7,353 | A message-driven or event-driven system is built, on purpose, so that a producer does not know who its consumers are and a consumer does not know who produced the message it just ... |
| [Message Store](message-store.md) | canonical | 8,479 | A messaging system built well is, by design, hard to see into from any one place. |
| [Messaging Bridge](messaging-bridge.md) | canonical | 6,431 | An enterprise settles on messaging as the way applications talk to each other, and that decision solves the coupling problem inside one messaging technology. |
| [Selective Consumer](selective-consumer.md) | canonical | 8,256 | A consuming application is attached to a message channel that carries a heterogeneous stream. |
| [Smart Proxy](smart-proxy.md) | canonical | 9,666 | A team wants the same operational visibility into a Request-Reply exchange that a Wire Tap already gives them on any ordinary point-to-point channel, a copy of every message going ... |
| [Wire Tap](wire-tap.md) | canonical | 6,408 | A message flows from a producer, through a channel, to a consumer, and the system needs visibility into that traffic for a purpose that has nothing to do with the business logic ... |

## Enterprise Integration Pattern

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Scatter-Gather](scatter-gather.md) | canonical | 6,934 | A caller needs an answer that no single system holds in full. |

## Enterprise Integration Pattern, System Management

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Control Bus](control-bus.md) | canonical | 7,416 | Picture an order processing system built from a dozen independently deployed services, connected by message queues, spread across two data centers and a handful of partner ... |
| [Detour](detour.md) | canonical | 7,931 | A production messaging pipeline is already carrying real traffic, and something about that traffic now needs closer inspection without stopping the pipeline to redeploy it. |

## Enterprise Integration, Messaging Channels

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Datatype Channel](datatype-channel.md) | canonical | 7,432 | A consumer reads a message off a channel and must decide how to process it before it can do anything with the payload. |

## Integration

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Canonical Data Model](canonical-data-model.md) | canonical | 7,249 | An enterprise with N independently developed systems that must exchange data pairwise needs, in the worst case, N times (N minus one) point-to-point translators if each system ... |
| [Channel Purger](channel-purger.md) | canonical | 6,634 | A messaging system accumulates state on its channels in the form of undelivered or unconsumed messages sitting in a queue, a topic partition, or a durable subscription. |
| [Claim Check](claim-check.md) | canonical | 8,731 | A component in a message-based system needs to communicate a large amount of data, an image, a video, a document, a bulk export, a machine learning feature vector, a full customer ... |
| [Command Message](command-message.md) | canonical | 6,027 | An application wants another application, or another component in the same system, to perform a specific piece of work. |
| [Content Enricher](content-enricher.md) | canonical | 6,852 | A message arrives at an integration point carrying less data than the next step needs. |
| [Content Filter](content-filter.md) | canonical | 8,476 | A consumer receives a message that is far larger, richer, or more deeply nested than anything it needs, and forwarding or storing that full message creates real cost. |
| [Correlation Identifier](correlation-identifier.md) | canonical | 7,434 | A process sends a message and does not receive its answer over the same connection it used to send it. |
| [Document Message](document-message.md) | canonical | 7,030 | Two systems need to exchange a structured record, such as a customer record, a purchase order, a lab result, or a shipment manifest. |
| [Dynamic Router](dynamic-router.md) | canonical | 7,677 | A message-routing component in a system needs to send a message onward, and the set of places it might send that message to is not fixed at the time the router is built, deployed ... |
| [Event Message](event-message.md) | canonical | 7,047 | An application performs an action that other applications, possibly ones the first application has never heard of and will never know about, need to react to. |
| [Event-Driven Consumer](event-driven-consumer.md) | canonical | 6,051 | A service needs to react when something happens elsewhere in the system, a payment is captured, an order is placed, a file lands in a bucket, a row is updated in another team's ... |
| [Format Indicator](format-indicator.md) | canonical | 6,141 | A message travels from a producer to a consumer, and at some point the consumer must decide how to parse the bytes it received. |
| [Message](message.md) | canonical | 6,912 | Two applications need to exchange information without either one blocking on the other's availability, without either one dictating the other's internal data model, and without a ... |
| [Message Bus](message-bus.md) | canonical | 7,681 | A system starts with two applications that need to exchange data, and a direct point-to-point integration, a script that reads from one database and writes to another, or a ... |
| [Message Channel](message-channel.md) | canonical | 5,993 | Two independently deployed pieces of software need to exchange information, and the team building them does not want a synchronous, point-to-point network call between them. |
| [Message Dispatcher](message-dispatcher.md) | canonical | 7,095 | A single logical stream of work needs to be processed by more capacity than one consumer thread can provide, and the team wants that capacity applied without breaking three ... |
| [Message Expiration](message-expiration.md) | canonical | 6,910 | A message carries a request or a piece of data across an asynchronous boundary. |
| [Message Filter](message-filter.md) | canonical | 7,490 | A component sits on a message channel and receives every message that flows past, but it only knows how to handle a subset of them. |
| [Message Sequence](message-sequence.md) | canonical | 6,969 | A producer has one logical unit of data to move across a messaging channel, and the unit is larger than the channel, the broker, or the receiving application can accept as a ... |
| [Messaging Gateway](messaging-gateway.md) | canonical | 7,420 | An application needs to send and receive messages through a messaging system, a message queue, an event bus, a Kafka topic, an AMQP exchange, but the team does not want every part ... |
| [Normalizer](normalizer.md) | canonical | 6,921 | A system receives messages that all describe the same real-world fact, an order was placed, a patient was admitted, a trade was executed, but the messages arrive in several ... |
| [Routing Slip](routing-slip.md) | canonical | 7,740 | A message needs to pass through a chain of processing steps, and the exact membership and order of that chain differs per message, per tenant, or per business rule, rather than ... |

## Integration (Message Routing)

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Resequencer](resequencer.md) | canonical | 7,568 | A producer emits a series of related units, each carrying an explicit position in a sequence, a timestamp, or an ordinal, and the units are meant to be consumed, displayed, or ... |

## Message Construction

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Envelope Wrapper](envelope-wrapper.md) | canonical | 6,373 | An application was built to produce and consume data in its own native format, a flat file, a fixed-width record, a plain XML document with no messaging-specific fields, a CSV row. |

## Message Endpoint

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Messaging Mapper](messaging-mapper.md) | canonical | 7,501 | An application has a domain model, the classes that hold its business state and enforce its business rules, an Order, a Customer, a ShipmentPlan. |

## Message Routing

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Splitter](splitter.md) | canonical | 6,617 | A message arrives that is a container for several logically independent units of work, and the downstream processing needs to happen per unit, not per container. |

## Messaging

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Competing Consumers](competing-consumers.md) | canonical | 6,378 | A producer or a set of producers places units of work onto a channel faster, or in bursts faster, than a single consumer can process them. |
| [Content-Based Router](content-based-router.md) | canonical | 6,836 | A single logical message stream must be handled by more than one downstream consumer, and which consumer handles a given message depends on data inside that message, not on which ... |
| [Durable Subscriber](durable-subscriber.md) | canonical | 6,847 | A publisher broadcasts events on a topic. |
| [Guaranteed Delivery](guaranteed-delivery.md) | canonical | 6,080 | A service publishes an event or sends a command onto a channel and then proceeds as if the message is on its way. |
| [Recipient List](recipient-list.md) | canonical | 7,476 | A single message must reach more than one downstream consumer at once, and the exact SET of consumers that should receive a given message is not fixed at design time. |
| [Request-Reply](request-reply.md) | canonical | 6,636 | A component needs an answer from another component before it can continue, and the two components do not share a process, a thread, or a call stack. |
| [Return Address](return-address.md) | canonical | 7,280 | A requestor sends a message into an asynchronous channel and needs an answer back. |
| [Transactional Client](transactional-client.md) | canonical | 7,881 | A client sends or receives several messages that belong together as one unit of work, and the messaging system offers no help unless the client asks for it explicitly. |

## Messaging Channels

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Dead Letter Channel](dead-letter-channel.md) | canonical | 8,113 | A message oriented system moves work between components through channels rather than through direct calls. |
| [Invalid Message Channel](invalid-message-channel.md) | canonical | 8,175 | A receiver on a messaging channel is written against an expectation. |
| [Point-to-Point Channel](point-to-point-channel.md) | canonical | 6,709 | A system decouples a producer of work from a consumer of work using asynchronous messaging instead of a direct call, for the usual reasons. |

## Messaging Endpoint

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Service Activator](service-activator.md) | canonical | 7,397 | A piece of business logic already exists as an ordinary method call, a pricing calculator, an order validator, a shipment scheduler, written and tested with no idea that a message ... |

## Messaging Endpoints

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Channel Adapter](channel-adapter.md) | canonical | 7,823 | An application was written to be called, to poll a database, to read a file, or to raise an in-process event. |
| [Polling Consumer](polling-consumer.md) | canonical | 5,793 | An application needs to consume messages from a channel, a queue, a topic partition, or any buffered source of work items, but it needs to control the timing and the volume of ... |

## System Management

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Process Manager](process-manager.md) | canonical | 6,463 | Picture an order fulfillment system built from independently owned services. |
| [Test Message](test-message.md) | canonical | 7,706 | A messaging system is built from components that receive a message, do work on it, and emit a message. |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
