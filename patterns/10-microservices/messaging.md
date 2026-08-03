---
name: Messaging
slug: messaging
family: 10-microservices
category: Communication Style
aliases: [Asynchronous Messaging, Message-Based Communication]
first_described: "Hohpe and Woolf 2003, applied to microservices by Richardson 2018"
maturity: canonical
related: [domain-event, transactional-outbox, idempotent-consumer, polling-publisher, api-gateway, remote-procedure-invocation]
incompatible_with: []
verified: 2026-08-02
---

# Messaging

## 1. Name, aliases, and lineage

The canonical name in the microservices literature is Messaging, and it names
the family of inter-process communication styles built on exchanging messages
over a channel rather than calling a remote procedure directly. Chris
Richardson catalogs it as a communication-style pattern in the microservices.io
pattern language, stating the problem as "How do services in a microservice
architecture communicate?" and the solution as "Use asynchronous messaging for
inter-service communication. Services communicating by exchanging messages over
messaging channels" (Chris Richardson, [Messaging pattern entry](https://microservices.io/patterns/communication-style/messaging.html),
microservices.io, verified 2026-08-02). Richardson's book gives the same
pattern a full chapter treatment, Chris Richardson, *Microservices Patterns*,
Manning, 2018, chapter 3, "Interprocess communication in a microservice
architecture".

The underlying vocabulary, message, channel, message endpoint, publish
subscribe channel, point to point channel, predates the microservices era by
more than a decade. Gregor Hohpe and Bobby Woolf catalog the individual
messaging building blocks in *Enterprise Integration Patterns. Designing,
Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003. Richardson
cites this book directly as the source of the vocabulary his own pattern reuses
(Richardson, *Microservices Patterns*, chapter 3). "Asynchronous Messaging" and
"Message-Based Communication" are the two aliases in common use for the same
idea, both describing the same underlying mechanism, a producer places a
message on a channel and a consumer reads it later, with no requirement that
the producer block waiting for a reply.

A useful boundary to draw at the outset, because catalogs and blog posts blur
it constantly. Messaging is the transport and coordination style. Kafka,
RabbitMQ, Amazon SQS and SNS, Google Cloud Pub/Sub, and Azure Service Bus are
implementations of that style, not the pattern itself. Domain Event and
Transactional Outbox, cataloged separately in this repository, are patterns
that answer narrower questions, what shape of message to send, and how to send
it reliably from a database transaction, and both patterns depend on Messaging
already being the chosen communication style for the services involved.

## 2. Problem and context

A microservice architecture splits one application into many independently
deployable services, and Richardson is explicit that this decomposition alone
does not remove the need for those services to collaborate, it only changes
how they must do it, because a single business operation now spans process
boundaries that used to be in-process method calls (Richardson,
*Microservices Patterns*, chapter 3, section 3.1). The concrete situation looks
like this in a real system. An order service accepts a new order. Before it can
report success to the customer, or shortly after, a payment must be authorized,
inventory must be reserved, and a shipping label must eventually be requested.
Each of those steps now lives in a separate deployable unit, on its own
schedule, on its own infrastructure, and possibly written by a different team.

The context in which Messaging is the right answer has three recurring shapes.
First, a step in the workflow does not need to complete before the caller can
proceed, the caller only needs to know the request was accepted, so blocking on
a synchronous reply wastes latency budget the business does not require.
Second, the receiving service may be temporarily unavailable, mid deployment,
recovering from a crash, or overloaded, and the business requirement is that
the request is never lost, only delayed. Third, more than one service needs to
react to the same fact, an order was placed, without the producing service
knowing in advance the full list of interested parties, which a direct
request-response call would force it to know.

Outside that context, particularly when the caller genuinely needs an
immediate answer to decide its own next step, a synchronous call answers the
question more simply, see dimension 4.

## 3. Forces

- **Runtime coupling.** Strongly favoured. Richardson names this directly as
  the deciding force, "synchronous communication results in tight runtime
  coupling, both the client and service must be available" for the interaction
  to succeed (Richardson, [Messaging pattern entry](https://microservices.io/patterns/communication-style/messaging.html),
  Forces section, verified 2026-08-02). Messaging breaks that coupling because
  the broker, not the consumer, is the thing the producer must find available.
- **Availability.** Favoured. A message sitting in a durable channel survives a
  consumer outage. A synchronous call made during that same outage fails
  outright, unless the caller adds its own retry and circuit-breaker logic.
- **Latency for the caller.** Favoured for fire-and-forget and notification
  styles, neutral to worsened for request-asynchronous-response, where the
  caller still waits for an eventual reply but now pays broker hop latency on
  top of the handler's own processing time.
- **Consistency.** Sacrificed relative to a single local transaction. A message
  published successfully does not guarantee the consumer has processed it yet,
  so the system as a whole is only eventually consistent across the services
  touched by one business operation, and this drives the need for the Saga
  pattern to coordinate a multi-step workflow without a distributed
  transaction (Richardson, *Microservices Patterns*, chapter 3, section 3.1).
- **Operational complexity.** Sacrificed. A message broker is a new piece of
  infrastructure to run, monitor, back up, and capacity-plan, on top of the
  services themselves, and every consumer must now be built to tolerate
  redelivery, ordering surprises, and poison messages, none of which a direct
  method call ever has to consider.
- **Debuggability.** Sacrificed. A request that used to be one visible call
  stack is now a chain of asynchronous handlers connected only by a message
  ID, so tracing a failure across the chain needs distributed tracing
  infrastructure that a synchronous call chain gets closer to for free.
- **Cost of adding a new consumer.** Favoured, and this is the force that
  publish-subscribe optimizes hardest for. A new service can subscribe to an
  existing topic and start reacting to events without the producing service
  changing a single line, which a point-to-point RPC integration cannot offer
  without the producer explicitly adding a new outbound call.

## 4. Applicability and non-applicability

Reach for Messaging when any of these hold.

- The caller does not need the result of the operation to proceed with its own
  work, a notification or fire-and-forget interaction is sufficient.
- More than one consumer must react to the same event, and the producer should
  not need to know who they are or how many there are.
- The receiving service, or the network path to it, is expected to be
  unavailable at times, and the business requirement is that no request is
  lost during that window.
- A multi-step business transaction spans services and needs the Saga pattern
  to coordinate compensating actions, which itself depends on asynchronous
  messaging as its transport (Richardson, *Microservices Patterns*, chapter 4).
- The workload benefits from load leveling, a burst of incoming work can queue
  and drain at the consumer's own sustainable rate instead of overwhelming it.

Do NOT reach for Messaging in these cases, and reaching anyway is a common
misapplication.

- The caller genuinely needs the result before it can respond to its own
  caller, for example a query the user is waiting on synchronously in a web
  request. Wrapping that in async messaging with a correlation ID and a poll
  loop adds real latency and complexity for no consistency benefit, use Remote
  Procedure Invocation instead.
- The team has no operational capacity to run and monitor a message broker,
  and no managed offering is acceptable for the organization's constraints. An
  under-resourced broker is a worse single point of failure than the
  synchronous calls it replaced.
- The interaction is a simple internal call inside a single deployable unit. A
  monolith or a single service does not need a message broker between its own
  modules, an in-process function call or an in-process event bus is enough.
- Strong, immediate read-after-write consistency across the two services is a
  hard business requirement that cannot tolerate any eventual-consistency
  window, for example a synchronous funds-availability check gating an
  irreversible action in the same request.
- The message payload must be enormous, well beyond a broker's practical
  message-size limit, in which case the payload should be stored elsewhere and
  the message should carry a reference to it, not the payload itself.

## 5. Structure

- **Message.** A self-contained unit of data with a header, including at
  minimum a message ID, and a body carrying either a command, an event, or a
  document. It is immutable once sent.
- **Message channel.** The virtual pipe a producer writes to and a consumer
  reads from. It exists as either a Point-to-Point Channel, where exactly one
  consumer receives any given message, even when several consumer instances
  compete for it, or a Publish-Subscribe Channel, where every active
  subscriber receives its own copy of every message.
- **Message producer.** The service that constructs and sends a message onto a
  channel, without knowledge of who, if anyone, will consume it.
- **Message consumer, also message endpoint.** The service, or a competing
  instance of it, that reads from a channel and acts on each message it
  receives.
- **Message broker.** The infrastructure component, Kafka, RabbitMQ, Amazon
  SQS and SNS, that physically stores and routes messages between producers
  and consumers, and is responsible for durability, ordering guarantees within
  its own model, and delivery.
- **Correlation identifier.** A header value threading a request message to
  its eventual reply message, used in the request-asynchronous-response style
  so the original caller can match an incoming reply to the request it sent.

## 6. ASCII structure diagram

```
                    +-------------------------+
                    |     Message Broker      |
                    |  (Kafka / RabbitMQ /     |
                    |   SQS+SNS / Pub/Sub)     |
                    +-------------------------+
                       ^        |        |
         publish       |        | deliver| deliver
                       |        v        v
   +--------------+    |   +--------+  +--------+
   | Order Service|----+   | Billing|  |Shipping|
   | (producer)   |        |Service |  |Service |
   +--------------+        |(consumer)|(consumer)|
                            +--------+  +--------+

   Point-to-Point Channel (competing consumers, one winner per message)

   +-----------+      queue      +----------+     +----------+
   | Producer  | ---------------> | Worker A | or  | Worker B |
   +-----------+                  +----------+     +----------+
                                   only one instance receives each message

   Publish-Subscribe Channel (fan-out, every subscriber gets its own copy)

   +-----------+      topic      +----------+
   | Producer  | ---------------> | Sub A    |
   +-----------+        \         +----------+
                          \        +----------+
                           +-----> | Sub B    |
                                   +----------+
```

## 7. Dynamics

The most common runtime shape is publish and forget, followed by
consumer-side idempotent processing.

```
Order Service        Message Broker         Billing Service
     |                     |                        |
     | 1. place order      |                        |
     |--(local commit)-----|                        |
     | 2. publish OrderCreated(evt-1)                |
     |-------------------->|                        |
     |                     | 3. deliver evt-1        |
     |                     |----------------------->|
     |                     |                         | 4. handle
     |                     |                         |    (checks evt-1
     |                     |                         |     not yet seen)
     |                     | 5. ack                  |
     |                     |<------------------------|
     | (order service is never blocked past step 2)  |
```

Request-asynchronous-response adds a correlation identifier so the original
caller, itself an asynchronous handler, can match a later reply to the request
it made.

```
Caller               Reply Channel      Broker         Responder
  |                        |               |                |
  | 1. send Request(cid=abc123)            |                |
  |------------------------------------------------------->|
  |                        |               |    2. process   |
  |                        |               |<----------------|
  |                        | 3. deliver Reply(cid=abc123)    |
  |<------------------------                                |
  | 4. look up pending request by cid=abc123, resolve it    |
```

At-least-once delivery is the default guarantee most brokers provide, which
means a consumer must expect and tolerate redelivery of the same message,
handled at the consumer via the Idempotent Consumer pattern rather than at the
broker.

## 8. Implementation variants

- **Point-to-point with competing consumers.** A single logical queue, several
  consumer instances pulling from it, used for work distribution where each
  unit of work should be handled exactly once by exactly one worker. RabbitMQ
  documents this directly as "distributing tasks among workers, the competing
  consumers pattern" in its own tutorial series (RabbitMQ, [Getting Started tutorials](https://www.rabbitmq.com/tutorials),
  verified 2026-08-02).
- **Publish-subscribe with a durable topic log.** Consumers each maintain
  their own read position, offset in Kafka's terminology, into an
  append-only, replayable log, so a new subscriber can join later and, subject
  to retention, read history it missed. RabbitMQ's own tutorials name the
  contrasting mode as "sending messages to many consumers at once", its
  publish-subscribe exchange type (RabbitMQ, [Getting Started tutorials](https://www.rabbitmq.com/tutorials),
  verified 2026-08-02).
- **Notification, fire-and-forget.** The producer sends a one-way message and
  expects no reply of any kind. Used for events nobody needs to acknowledge
  back to the sender, an audit log entry, a metrics counter increment.
- **Request-asynchronous-response.** The producer sends a request carrying a
  correlation ID and a reply-to channel, then continues other work, later
  matching an incoming reply message on that same ID. Used when a synchronous
  wait is unacceptable but the caller still ultimately needs an answer.
- **Managed cloud queue plus fan-out topic.** Amazon SQS paired with Amazon
  SNS is a common combination, SNS fans a single publish out to many SQS
  queues, giving each subscribing service its own private, durable,
  competing-consumer queue fed from one shared topic. AWS documents SQS as
  providing "a simple and reliable way for customers to decouple and connect
  components, microservices, together using queues" (Amazon Web Services,
  [Amazon SQS](https://aws.amazon.com/sqs/), verified 2026-08-02).
- **Transactional outbox as the reliable send path.** Rather than publishing
  directly inside the business transaction, which risks a message sent for a
  transaction that later rolls back, the message is written to an outbox
  table in the same local transaction, and a separate relay reads that table
  and publishes to the broker, the approach cataloged separately in this
  repository as Transactional Outbox.

## 9. Known production uses

- **LinkedIn built Apache Kafka to move activity and operational data at the
  scale a traditional message queue could not sustain**, and Kafka remains
  an Apache Software Foundation top-level project used as the durable log
  underlying event-driven and streaming architectures at large scale (Apache
  Software Foundation, [Apache Kafka introduction](https://kafka.apache.org/intro),
  verified 2026-08-02, which documents real-time payment processing at banks
  and exchanges, logistics fleet tracking, IoT sensor ingestion, and retail
  order and interaction processing as current production use categories).
- **RabbitMQ implements the AMQP messaging protocol and is used as the broker
  underneath the competing-consumers and publish-subscribe patterns** across
  a very wide range of production systems, documented directly in its own
  tutorial series covering work queues, publish-subscribe, routing, topics,
  and RPC over messaging (RabbitMQ, [Getting Started tutorials](https://www.rabbitmq.com/tutorials),
  verified 2026-08-02).
- **Amazon SQS and Amazon SNS are AWS's managed point-to-point and
  publish-subscribe messaging services**, marketed and documented explicitly
  for decoupling microservices, distributed systems, and serverless
  applications in production, stating that SQS "lets you send, store, and
  receive messages between software components at any volume, without losing
  messages or requiring other services to be available" (Amazon Web Services,
  [Amazon SQS](https://aws.amazon.com/sqs/), verified 2026-08-02).
- **The Saga pattern, as cataloged by Chris Richardson for coordinating a
  multi-step business transaction across services, is built directly on top
  of asynchronous messaging as its transport**, and Richardson names
  messaging explicitly as the mechanism a saga's participants use to
  exchange commands and replies (Richardson, [Messaging pattern entry](https://microservices.io/patterns/communication-style/messaging.html),
  Related patterns section, verified 2026-08-02, and Richardson,
  *Microservices Patterns*, chapter 4).

## 10. Consequences

Positive.

- Producer and consumer are decoupled at runtime, neither needs the other to
  be available at the moment the message is sent, which directly improves
  overall system availability during partial outages and deployments.
- A new consumer can subscribe to an existing topic without the producer
  changing anything, which lowers the cost of extending the system with new
  reactive behavior over time.
- The broker buffers bursts of traffic, giving consumers a chance to drain
  work at their own sustainable rate rather than being overwhelmed by a spike.
- A durable, replayable log, where the broker supports one, gives the system
  an audit trail of everything that happened, and lets a newly added consumer
  catch up on history rather than only seeing events from the moment it joins.

Negative.

- The system becomes only eventually consistent across the services involved
  in one business operation, and the application must be designed to tolerate
  and communicate that, rather than assuming a single atomic outcome.
- A message broker is new, genuinely complex infrastructure that must be deployed,
  secured, monitored, capacity-planned, and kept highly available, and its
  outage now becomes a system-wide availability risk rather than a
  single-service one.
- At-least-once delivery, the practical default across most brokers, forces
  every consumer to be written as an idempotent handler, adding real
  implementation and testing burden that a plain synchronous handler does
  not carry.
- Tracing a single business operation across several asynchronous hops
  requires distributed tracing tooling and message-ID propagation discipline
  that a synchronous call stack provides for free.
- Message schemas become a long-lived, cross-team contract that must be
  versioned carefully, since a producer cannot always see or control every
  consumer of a topic before changing the message shape.

## 11. Failure modes and misuse

- **Symptom.** A consumer occasionally processes the same business effect
  twice, for example a customer is charged twice for one order.
  **Cause.** The consumer treats delivery as exactly-once when the broker only
  guarantees at-least-once, so a redelivered message after a crash or a
  network blip during acknowledgment runs the handler's side effect again.
  **Fix.** Implement the Idempotent Consumer pattern, tracking processed
  message IDs and skipping a handler body for an ID already seen, exactly the
  technique this entry's own code examples in dimension 19 demonstrate.

- **Symptom.** Messages pile up in a queue and consumer lag grows without
  bound, eventually exhausting broker storage or hitting retention limits.
  **Cause.** Consumers are provisioned for average load, not peak, or a
  downstream dependency the consumer calls has slowed or failed, so the
  consumer's own throughput has dropped below the producer's publish rate.
  **Fix.** Alert on consumer lag as a first-class production metric,
  autoscale consumer instances against that lag, and add a dead-letter path
  so a poison message that a handler cannot process does not block the rest
  of the queue behind it.

- **Symptom.** A downstream service silently never learns that an upstream
  event happened, even though the upstream service's logs show the publish
  call succeeded.
  **Cause.** The publish call was made inside the same business transaction as
  the database write, but the transaction later rolled back, or the publish
  itself succeeded to the broker but the surrounding database transaction
  failed after it, leaving the two out of sync, the dual-write problem.
  **Fix.** Use the Transactional Outbox pattern so the message write and the
  business data write share one local transaction, and a separate relay
  process, or change-data-capture via Transaction Log Tailing, is the only
  thing that actually talks to the broker.

- **Symptom.** Consumers process events wildly out of the order they actually
  happened, causing a state machine to reach an invalid state, for example an
  order-shipped event handled before the corresponding order-created event.
  **Cause.** The channel does not guarantee ordering across partitions or
  shards, or messages for the same logical entity were published without a
  shared partition or routing key, so the broker legitimately delivered them
  to different consumer instances that raced each other.
  **Fix.** Route all messages for the same aggregate to the same partition or
  routing key, so ordering is guaranteed within that key, and design consumer
  logic to be tolerant of, or explicitly reject and reorder, cross-key
  ordering surprises rather than assuming global order.

- **Symptom.** The message broker becomes a giant, undocumented, implicit
  integration contract, and nobody can safely change a message's shape
  because nobody knows which services actually consume it.
  **Cause.** Publish-subscribe's own decoupling strength, the producer never
  needing to know its subscribers, is misused as an excuse to skip contract
  ownership entirely, so message schemas evolve with no consumer-facing
  compatibility discipline.
  **Fix.** Version message schemas explicitly, publish a schema registry or
  equivalent contract catalog, and treat a message shape the same way a
  public API endpoint is treated, with additive-only changes as the default
  and a deprecation window before removing a field.

## 12. Trade-off matrix

| Force | Messaging | Remote Procedure Invocation | Domain Event over messaging |
|---|---|---|---|
| Runtime coupling | Loose, broker mediates availability | Tight, both sides must be up at call time | Loose, same as Messaging |
| Immediate result to caller | No, or only via request-async-response | Yes, direct in the response | No, consumers react later |
| Consistency model | Eventual across consumers | Immediate at the call site | Eventual, and semantically the event IS the fact being distributed |
| New-consumer cost | Low, subscribe to an existing topic | High, producer must add a new outbound call | Low, same broker mechanism as Messaging |
| Operational footprint | A broker to run and monitor | None beyond the network itself | Same broker footprint as Messaging |
| Failure visibility | Async, needs tracing and correlation IDs | Synchronous stack trace, immediate | Async, same tracing burden as Messaging |
| Best fit | Cross-service workflow steps, fan-out reactions | A caller that truly needs an answer now | Broadcasting a state change as a first-class fact for others to react to |

Remote Procedure Invocation is the pattern cataloged separately in this
repository as the direct alternative for the case where a synchronous answer
is required. Domain Event is not a competing alternative to Messaging, it is a
message-shape pattern that usually rides on top of Messaging as its
transport, included here to make that relationship explicit rather than
implied.

## 13. Related and incompatible patterns

- **Domain Event.** Domain Event defines the shape and semantics of the
  message payload, a fact that already happened, phrased in past tense.
  Messaging is the transport that carries a Domain Event from producer to
  consumer. They compose directly and are usually adopted together.
- **Transactional Outbox.** Solves the dual-write problem inherent to
  Messaging, guaranteeing a message is published if and only if the local
  database transaction that produced it committed. Messaging without this
  pattern, or an equivalent, risks the failure mode described in dimension 11.
- **Polling Publisher.** An implementation technique for reading the outbox
  table and forwarding its rows onto the message broker, one concrete way to
  build the relay half of Transactional Outbox.
- **Transaction Log Tailing.** An alternative relay technique to Polling
  Publisher, reading the database's own commit log via change data capture
  instead of polling a table, still ultimately publishing onto the same
  messaging channel this entry describes.
- **Idempotent Consumer.** The mandatory consumer-side counterpart to
  at-least-once delivery, without which Messaging's default delivery
  guarantee produces the duplicate-processing failure mode in dimension 11.
- **Saga.** Coordinates a multi-step, cross-service business transaction using
  a sequence of messages, commands and replies, exchanged over the channels
  Messaging defines, making Messaging a structural dependency of any Saga
  implementation.
- **Remote Procedure Invocation.** The synchronous alternative communication
  style, incompatible in the sense that a given interaction is built one way
  or the other, though a real system commonly uses both styles for different
  interactions depending on which one's forces fit better.
- **API Gateway.** Sits at the system's edge for external client requests,
  usually synchronous, and does not replace internal service-to-service
  Messaging, the two operate at different boundaries of the same system.

## 14. Refactoring path in and out

Introducing Messaging into a system currently built on direct, synchronous
calls proceeds in stages, never as a single cutover.

1. Identify one interaction where the caller does not actually need to block
   on the result, usually a side effect the caller currently waits for but
   does not use the return value of beyond a success acknowledgment.
2. Stand up a message broker as new infrastructure, sized and monitored before
   any production traffic depends on it, and prove it end to end with a
   throwaway topic first.
3. Change the producer to publish a message describing the fact or command
   instead of making the direct call, guarded behind a feature flag so the old
   synchronous path can still be used if the new one misbehaves.
4. Build the new consumer as an idempotent handler from the very first
   version, per dimension 11, rather than adding idempotency later once a
   duplicate-processing incident has already happened.
5. Run producer and consumer in parallel with the old synchronous path for a
   verification window, comparing outcomes, before removing the synchronous
   call entirely.
6. Once confidence is established, delete the now-unused synchronous call and
   its retry and timeout logic, since the broker now absorbs the
   availability concern that logic used to handle.

Removing Messaging, reverting a specific interaction back to a synchronous
call, is warranted when the eventual-consistency window it introduces is
causing real business friction, customer support tickets, race conditions
end users notice, that outweigh the availability benefit it was chosen for.
The path out mirrors the path in, run both paths in parallel, confirm the
synchronous path meets the caller's actual latency and availability
requirements, then remove the asynchronous producer and consumer and the now
unnecessary topic.

## 15. Testing and verification

- **Contract tests against the message schema**, not only the code, so a
  producer change that breaks the agreed message shape is caught before it
  reaches a consumer that has no way to negotiate the schema at runtime.
  Consumer-driven contract testing tools verify a producer's actual output
  against expectations each known consumer has published.
- **In-process broker test doubles for fast unit tests.** An in-memory
  channel implementation, of the shape shown in dimension 19's code examples,
  lets a producer or consumer be unit tested without a real broker running,
  while still exercising the actual publish and subscribe interfaces the
  production code uses.
- **A real, ephemeral broker instance for integration tests**, using a
  container-based test broker started and torn down per test run, is
  necessary at least once in the pipeline, because in-memory doubles cannot
  verify serialization, partitioning, or broker-specific delivery semantics.
- **Explicit redelivery tests.** Deliberately deliver the same message twice
  to a consumer under test and assert the observable side effect happened
  exactly once, which is the single most important test an idempotent
  consumer needs and the one most commonly skipped.
- **Out-of-order delivery tests** for any consumer whose correctness depends
  on ordering, sending events for the same aggregate in a shuffled sequence
  and asserting the consumer either handles it correctly or explicitly
  rejects the out-of-order case rather than silently corrupting state.
- **Fault-injection testing the broker connection itself**, killing the consumer mid
  processing and confirming the message is redelivered rather than lost, and
  killing the broker connection from the producer side and confirming the
  producer either retries or surfaces a clear failure rather than silently
  dropping the message.

## 16. Observability signals

- **Consumer lag per topic or queue**, the gap between the latest published
  offset and a consumer group's current read position, is the single most
  important health signal for any messaging system, since a healthy consumer
  keeps this near zero and a struggling one shows it growing unbounded.
- **Publish and consume rate**, messages per second on each side of a channel,
  graphed together so a growing gap between them is visible before it becomes
  an incident.
- **Dead-letter queue depth.** A non-zero and growing count here means
  messages are failing processing repeatedly and being routed aside, which
  needs alerting distinct from ordinary consumer lag.
- **Publish-to-acknowledgment message latency**, timestamped from publish to successful
  consumer acknowledgment, distributed as a histogram so p50, p95, and p99
  are all visible, since a broker can look healthy on throughput while
  individual messages take unacceptably long to be processed.
- **Redelivery count per message ID**, surfaced as a metric or a log field,
  is the direct signal an idempotency implementation is actually being
  exercised in production, not only assumed necessary.
- **Broker cluster health**, disk usage, partition or queue count, replica
  status, is infrastructure-level but must be on the same dashboard as
  application-level metrics, since a broker running low on disk degrades
  every producer and consumer simultaneously.
- **Distributed trace propagation**, a correlation or trace ID carried in
  message headers and threaded through every hop, so one business operation's
  path across producer, broker, and every consumer can be reconstructed after
  the fact from logs and traces alone.

## 17. Security and privacy implications

A message channel is a data-flow path like any network call, and its content
carries the same obligations as any other data at rest and in transit. A
message published to a topic is, by design, potentially readable by every
current and future subscriber of that topic, which is a materially different
exposure surface than a direct point-to-point RPC call the producer
controls the destination of. This has two direct consequences. First, a
message must never carry a secret, a raw credential, or unredacted
personally identifiable data that a future, unknown subscriber should not
see, and any field that is sensitive should be tokenized or referenced by ID
rather than included in the message body directly. Second, broker-level
authorization, which principal may publish to a topic and which may
subscribe to it, is a control the team must actively configure, since most
brokers default to permissive access within a cluster and do not enforce
per-message field-level access control on their own. Message payloads in
transit and at rest on the broker should be encrypted using the broker's
supported transport and storage encryption, and retention policy for a topic
carrying personal data should be set deliberately rather than left at a
broker's default, since an unbounded retention window on a durable log is
itself a data-retention and regulatory exposure the team must account for.

## 18. References

- Chris Richardson, [Messaging pattern entry](https://microservices.io/patterns/communication-style/messaging.html),
  microservices.io, verified 2026-08-02.
- Chris Richardson, *Microservices Patterns. With Examples in Java*, Manning
  Publications, 2018, chapter 3, "Interprocess communication in a
  microservice architecture", and chapter 4, "Managing transactions with
  sagas".
- Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, the
  originating catalog for Message Channel, Point-to-Point Channel, and
  Publish-Subscribe Channel.
- Apache Software Foundation, [Apache Kafka introduction](https://kafka.apache.org/intro),
  verified 2026-08-02.
- RabbitMQ, [Getting Started tutorials](https://www.rabbitmq.com/tutorials),
  verified 2026-08-02.
- Amazon Web Services, [Amazon SQS](https://aws.amazon.com/sqs/), verified
  2026-08-02.

## 19. Code examples

Three languages, each demonstrating a different variant from dimension 8.
The Go example shows publish-subscribe fan-out with per-consumer idempotency.
The TypeScript example shows the same idempotent-consumer discipline against
a redelivered message. The Python example shows a point-to-point channel with
competing consumers.

Go, publish-subscribe with per-consumer idempotency.

```go
package main

import (
	"fmt"
	"sync"
)

type Message struct {
	ID      string
	Payload string
}

// Channel fans a published message out to every subscriber. All Subscribe
// calls complete before Publish runs, so no synchronization is needed here.
type Channel struct {
	subs []chan Message
}

func (c *Channel) Subscribe() <-chan Message {
	ch := make(chan Message, 10)
	c.subs = append(c.subs, ch)
	return ch
}

func (c *Channel) Publish(m Message) {
	for _, sub := range c.subs {
		sub <- m
	}
}

type Broker struct {
	topics map[string]*Channel
	checks chan checkRequest
}

type checkRequest struct {
	consumer string
	id       string
	reply    chan bool
}

// idempotencyGate owns the seen-message state in its own goroutine and
// answers isNew requests over a channel, avoiding any shared-memory guard.
func idempotencyGate() chan checkRequest {
	requests := make(chan checkRequest)
	go func() {
		seen := make(map[string]map[string]bool)
		for req := range requests {
			if seen[req.consumer] == nil {
				seen[req.consumer] = make(map[string]bool)
			}
			isNew := !seen[req.consumer][req.id]
			seen[req.consumer][req.id] = true
			req.reply <- isNew
		}
	}()
	return requests
}

func NewBroker() *Broker {
	return &Broker{topics: make(map[string]*Channel), checks: idempotencyGate()}
}

func (b *Broker) topic(name string) *Channel {
	c, ok := b.topics[name]
	if !ok {
		c = &Channel{}
		b.topics[name] = c
	}
	return c
}

func (b *Broker) Publish(topic string, m Message) {
	b.topic(topic).Publish(m)
}

func (b *Broker) Subscribe(topic string) <-chan Message {
	return b.topic(topic).Subscribe()
}

// idempotentHandle skips a message a given consumer already processed.
func (b *Broker) idempotentHandle(consumer string, m Message, handler func(Message)) {
	reply := make(chan bool)
	b.checks <- checkRequest{consumer: consumer, id: m.ID, reply: reply}
	if <-reply {
		handler(m)
	}
}

func main() {
	broker := NewBroker()
	var wg sync.WaitGroup

	orderCreated := broker.Subscribe("order.created")
	billing := broker.Subscribe("order.created")

	wg.Add(2)
	go func() {
		defer wg.Done()
		for m := range orderCreated {
			broker.idempotentHandle("shipping", m, func(m Message) {
				fmt.Printf("shipping consumed %s: %s\n", m.ID, m.Payload)
			})
			return
		}
	}()
	go func() {
		defer wg.Done()
		for m := range billing {
			broker.idempotentHandle("billing", m, func(m Message) {
				fmt.Printf("billing consumed %s: %s\n", m.ID, m.Payload)
			})
			return
		}
	}()

	broker.Publish("order.created", Message{ID: "evt-1", Payload: "order 42 placed"})
	wg.Wait()
}
```

TypeScript, idempotent consumer rejecting a redelivered message.

```typescript
type Message<T> = { id: string; payload: T };
type Handler<T> = (m: Message<T>) => Promise<void>;

class Channel<T> {
  private subscribers: Handler<T>[] = [];

  subscribe(handler: Handler<T>): void {
    this.subscribers.push(handler);
  }

  async publish(m: Message<T>): Promise<void> {
    await Promise.all(this.subscribers.map((h) => h(m)));
  }
}

class IdempotentConsumer<T> {
  private processed = new Set<string>();

  constructor(private name: string, private next: Handler<T>) {}

  handle: Handler<T> = async (m) => {
    if (this.processed.has(m.id)) {
      console.log(`${this.name} skipped duplicate ${m.id}`);
      return;
    }
    this.processed.add(m.id);
    await this.next(m);
  };
}

async function main(): Promise<void> {
  const orderCreated = new Channel<{ orderId: number }>();

  const shipping = new IdempotentConsumer<{ orderId: number }>("shipping", async (m) => {
    console.log(`shipping consumed ${m.id}: order ${m.payload.orderId}`);
  });
  const billing = new IdempotentConsumer<{ orderId: number }>("billing", async (m) => {
    console.log(`billing consumed ${m.id}: order ${m.payload.orderId}`);
  });

  orderCreated.subscribe(shipping.handle);
  orderCreated.subscribe(billing.handle);

  const event = { id: "evt-1", payload: { orderId: 42 } };
  await orderCreated.publish(event);
  await orderCreated.publish(event);
}

main();
```

Python, point-to-point channel with competing consumers.

```python
from __future__ import annotations

import queue
import threading
from dataclasses import dataclass


@dataclass
class Message:
    id: str
    payload: dict


class WorkQueue:
    """Point-to-point channel with competing consumers."""

    def __init__(self) -> None:
        self._q: "queue.Queue[Message]" = queue.Queue()

    def send(self, m: Message) -> None:
        self._q.put(m)

    def receive(self, timeout: float = 1.0) -> Message | None:
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None


def worker(name: str, channel: WorkQueue, results: list, lock: threading.Lock) -> None:
    m = channel.receive()
    if m is None:
        return
    with lock:
        results.append(f"{name} consumed {m.id}: {m.payload}")


def main() -> None:
    channel = WorkQueue()
    results: list[str] = []
    lock = threading.Lock()

    channel.send(Message(id="evt-1", payload={"order_id": 42}))
    channel.send(Message(id="evt-2", payload={"order_id": 43}))

    threads = [
        threading.Thread(target=worker, args=(f"worker-{i}", channel, results, lock))
        for i in range(2)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for line in sorted(results):
        print(line)


if __name__ == "__main__":
    main()
```

Java and Rust are omitted here, not because the pattern does not translate,
Kafka's own client libraries are Java-first and RabbitMQ's official driver
list includes a mature Rust client, but because a fourth and fifth
in-memory demonstration of the same publish-subscribe and competing-consumer
mechanics shown above in Go, TypeScript, and Python would repeat the same
idempotency and channel logic without teaching anything the first three
examples do not already cover clearly.
