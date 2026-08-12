---
name: Guaranteed Delivery
slug: guaranteed-delivery
family: 07-integration
category: Messaging
aliases: [Persistent Messaging, Store and Forward Messaging, Durable Messaging]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [message-channel, point-to-point-channel, dead-letter-channel, transactional-outbox, idempotent-receiver, retry, circuit-breaker]
incompatible_with: []
verified: 2026-08-12
---

# Guaranteed Delivery

## 1. Name, aliases, and lineage

The canonical name is Guaranteed Delivery. It is catalogued as a messaging
pattern by Gregor Hohpe and Bobby Woolf in *Enterprise Integration Patterns.
Designing, Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
in the Messaging Systems chapter. The book poses the pattern's problem
statement plainly, "How can the sender make sure that a message will be
delivered, even if the messaging system fails?", and answers it with "Use
Guaranteed Delivery to make messages persistent so that they are not lost even
if the messaging system crashes" (Enterprise Integration Patterns website,
Guaranteed Delivery page, https://www.enterpriseintegrationpatterns.com/patterns/messaging/GuaranteedMessaging.html,
verified 2026-08-12, which mirrors the printed catalog entry).

The name is used loosely across the industry and that looseness is worth
naming up front. Message-broker vendors use the phrase for different things.
JMS calls its equivalent capability PERSISTENT delivery mode on a message, set
via `Message.setJMSDeliveryMode`, a point-level knob rather than an end-to-end
pattern (Oracle Java EE 8 API, `javax.jms.DeliveryMode`, verified against
Oracle's javadoc archive, 2026-08-12). AMQP 0-9-1 and its RabbitMQ
implementation call the equivalent mechanism publisher confirms combined with
message and queue durability, and consumer acknowledgements on the receiving
side (RabbitMQ documentation, Confirms, https://www.rabbitmq.com/docs/confirms,
verified 2026-08-12). Apache Kafka does not use the phrase at all and instead
describes delivery semantics as at-most-once, at-least-once, and
exactly-once, controlled by the producer `acks` setting and consumer offset
commit strategy (Apache Kafka documentation, Design, Message Delivery
Semantics section, kafka.apache.org/documentation, publicly documented Kafka
behaviour, verified against the Apache Kafka project site 2026-08-12).

Aliases in circulation, and what each emphasises. **Persistent Messaging**
emphasises the mechanism, disk persistence. **Store and Forward Messaging**
emphasises the topology, a chain of local stores each handing off to the next.
**Durable Messaging** is the adjective JMS and most brokers actually attach to
the queue or topic object, as in a durable subscription. All four names point
at the same underlying guarantee. A message, once accepted by the sender's
local infrastructure, survives any single process or machine crash between
sender and receiver.

## 2. Problem and context

A service publishes an event or sends a command onto a channel and then
proceeds as if the message is on its way. If the message broker, the network
link, or the receiving service crashes a millisecond after the sender's call
returns, the message can vanish, and nothing downstream will ever know the
event happened. In a request-response system this failure is visible, the
caller gets an exception and retries. In an asynchronous messaging system
built on a channel with no persistence, the failure is silent. Money that
should have moved does not move, an order that should have shipped never
ships, and the only trace is the absence of a downstream side effect that
nobody is watching for.

The context that raises this problem is any system that has already adopted
asynchronous messaging (Message Channel, Point-to-Point Channel, or
Publish-Subscribe Channel) as the integration style between two or more
services, and where the business consequence of a lost message is worse than
the operational cost of storing and possibly redelivering it. It shows up
acutely in payment processing, order fulfillment, inventory reservation,
audit logging, and any workflow where "the event that started this business
process" and "the record that the process happened" must be the same
artifact. It does not show up as a problem in systems where a lost message is
cheap to shrug off, for example a live cursor-position broadcast in a
collaborative editor, where the next update supersedes the lost one anyway.

Guaranteed Delivery sits downstream of a decision that has already been
made, that the system is asynchronous and message-based. It does not argue
for that decision. It answers the narrower question of what happens to a
message between the moment the sender hands it off and the moment the
receiver has durably acted on it, across every process boundary and machine
in between.

## 3. Forces

This section is largely engineering judgement about which forces dominate in
practice, not a sourced claim about the pattern's intrinsic properties.

- **Durability versus latency.** Writing a message to disk, or to a
  replicated broker log, before acknowledging the sender adds a write and, in
  a replicated system, a network round trip to at least one follower before
  the send call returns. A system with a hard sub-millisecond latency budget
  cannot casually add fsync-and-replicate to every hop.
- **Delivery guarantee versus idempotency burden.** The mechanisms that make
  redelivery safe, acknowledge only after durable processing, retry on
  timeout, can produce a message being delivered more than once, because the
  producer or broker cannot always tell "the consumer processed this and the
  ack was lost" apart from "the consumer never got it." Guaranteed Delivery
  in practice buys at-least-once semantics, not exactly-once, unless it is
  paired with an idempotent receiver or a deduplication mechanism at the
  consumer.
- **Storage cost and operability versus loss risk.** Every hop that persists
  a message needs storage, monitoring for that storage filling up, a
  retention and purge policy, and usually a dead letter path for messages
  that can never be delivered. That is real operational surface area that a
  fire-and-forget, in-memory channel does not have.
- **Ordering versus parallel redelivery.** A store that retries failed
  deliveries independently per message, to maximise throughput, can deliver
  messages out of the order they were produced. A store that retries strictly
  in order protects ordering at the cost of head-of-line blocking, where one
  stuck message stalls everything behind it.
- **Coupling to infrastructure versus portability.** The pattern is usually
  implemented by leaning on capabilities the messaging middleware already
  provides, durable queues, publisher confirms, a replicated commit log.
  That is efficient, but it ties the guarantee's actual behaviour to the
  specific broker's configuration and failure modes, which makes migrating
  brokers a behavioural change, not just a wiring change.

The pattern favours correctness and auditability over raw throughput and
simplicity. It sacrifices some latency and a meaningful amount of
operational surface area, and it does not, by itself, sacrifice ordering,
though a naive implementation can.

## 4. Applicability and non-applicability

Applicability. Reach for Guaranteed Delivery when these conditions hold.

- A lost message represents a real, hard-to-detect business defect, an
  unshipped order, an unbilled invoice, an unrecorded inventory movement.
- The sender and receiver are not both up and reachable at the same instant,
  so a synchronous call that fails cannot simply be retried by the caller in
  the moment.
- The channel crosses a process or machine boundary where a crash between
  send and receive is a realistic event, not a theoretical one, for example
  any broker-mediated channel, any queue with more than a handful of items in
  flight, or any channel with a consumer that can be slower than the
  producer.
- The system already tolerates at-least-once delivery elsewhere, or is
  willing to add idempotent receivers, so the redelivery this pattern implies
  does not itself become a correctness bug.
- Regulatory or audit requirements demand that "the event was durably
  recorded" and "the event was processed" be independently verifiable.

Non-applicability, with the reason for each.

- **High-frequency, latest-value-wins data.** A stock ticker tick, a live
  GPS position, a mouse-cursor broadcast. The next update makes the lost one
  irrelevant, so paying for persistence buys nothing the business cares
  about, and it slows down every message for a guarantee nobody needed.
- **In-process, single-machine event dispatch.** If the producer and
  consumer share a process and a crash of that process takes both down
  together, there is no failure window a persisted channel protects against
  that a synchronous call handler does not already cover more simply.
  Observer inside one process does not need this pattern.
- **Systems where exactly-once, not at-least-once, is the actual
  requirement, and no idempotency layer exists or is planned.** Guaranteed
  Delivery on its own produces at-least-once semantics under failure. Adding
  it without an idempotent receiver or dedup key trades "silently lost" for
  "silently duplicated," which is a different bug, not a smaller one.
- **Extremely latency-sensitive control loops**, for example a real-time
  bidding auction with a single-digit-millisecond deadline, where a message
  that cannot be durably persisted and acknowledged inside the deadline is
  worthless whether or not it survives a crash. Here Guaranteed Delivery's
  cost model is simply incompatible with the requirement.
- **A single-node prototype or throwaway script** where the operational cost
  of running a durable broker, monitoring its disk, and building a dead
  letter path is disproportionate to the risk of losing a message during
  development.

## 5. Structure

Participants and their responsibilities.

- **Sender.** The producing application. Its responsibility ends when it has
  received confirmation that the message is durably stored somewhere outside
  its own process, not merely that a network write returned.
- **Local store (send-side).** A durable append point, typically the
  message broker's own persistent log or a database table (see
  Transactional Outbox). Its responsibility is to hold the message until it
  has been handed off to, and durably accepted by, the next hop.
- **Store-and-forward relay.** The component, often part of the broker
  itself, that moves a message from one local store to the next. It is
  responsible for not deleting a message from its own store until the next
  hop has durably accepted it, and for retrying the handoff on failure.
- **Receiver-side store.** The final durable resting place before the
  consumer acts on the message, typically the broker's queue or partition.
- **Receiver / consumer.** The consuming application. Its responsibility is
  to acknowledge the message only after it has durably completed its own
  work, never merely after it has read the bytes off the wire.
- **Dead letter channel (supporting participant).** Receives a message that
  has exceeded its redelivery attempts, so a permanently unprocessable
  message does not loop forever and does not silently vanish either.

## 6. ASCII structure diagram

```
+----------+   durable write    +-------------------+
|  Sender  | ------------------>|  Send-side store   |
+----------+   (ack only after  |  (broker log /     |
                 durable write)  |   outbox table)    |
                                 +---------+----------+
                                           |
                                  relay forwards only
                                  after next hop confirms
                                           |
                                           v
                                 +---------+----------+
                                 | Receiver-side store |
                                 |  (durable queue /   |
                                 |     partition)      |
                                 +---------+----------+
                                           |
                                  delivered, held until
                                  consumer explicitly acks
                                           |
                                           v
                                    +------+------+
                                    |  Receiver   |
                                    +------+------+
                                           |
                              ack only after durable
                              side effect completes
                                           |
                        +------------------+------------------+
                        |                                     |
                 ack received,                        redeliveries exhausted
              message purged from store                       |
                                                                v
                                                       +--------+--------+
                                                       | Dead Letter      |
                                                       | Channel          |
                                                       +-------------------+
```

## 7. Dynamics

```
Sender          Send-store       Relay        Receive-store      Receiver
  |                 |              |                |                |
  |--send(msg)----->|              |                |                |
  |                 |--fsync------>|                |                |
  |<--ack (durable)-|              |                |                |
  |  (send() returns only here)    |                |                |
  |                 |--forward---->|--write-------->|                |
  |                 |              |<--confirm------|                |
  |                 |<--confirm----|                |                |
  |                 |--delete------|                |                |
  |                 | (local copy freed only after   |                |
  |                 |  next hop durably confirmed)    |                |
  |                 |              |                |--deliver------>|
  |                 |              |                |                |--process
  |                 |              |                |                |  (durable
  |                 |              |                |                |   side effect)
  |                 |              |                |<---ack---------|
  |                 |              |                |--delete-------|
  |                 |              |                | (purged only  |
  |                 |              |                |  after ack)   |
```

If the receiver crashes after `deliver` and before `ack`, the message
remains in the receive-store, unacknowledged, and is redelivered once a
visibility timeout or lock expires. If the redelivery count exceeds a
configured threshold, the message is routed to the Dead Letter Channel
instead of retried indefinitely, which is why Dead Letter Channel is a
required companion, not an optional extra, in a production Guaranteed
Delivery implementation.

## 8. Implementation variants

- **Broker-native durable queue plus consumer ack.** The most common
  variant. The broker persists the message to disk (and, in a clustered
  broker, replicates it) before returning a publish confirmation, and the
  consumer explicitly acknowledges after finishing its work rather than on
  receipt. RabbitMQ's publisher confirms plus manual consumer
  acknowledgements is a direct implementation of this variant. A `basic.ack`
  for a persistent message routed to a durable queue is sent only "after
  persisting the message to disk" (RabbitMQ documentation, Confirms,
  https://www.rabbitmq.com/docs/confirms, verified 2026-08-12).
- **Replicated commit log with quorum acknowledgement.** Kafka's approach.
  A producer setting `acks=all` waits for the message to be written to the
  leader and replicated to enough in-sync replicas, governed by
  `min.insync.replicas` on the topic, before the produce call is considered
  successful, and the consumer tracks its own committed offset as the
  acknowledgement of having processed a message, independent of delivery.
  This trades a broker-side queue-and-ack model for a log-and-offset model,
  which additionally gives replay, a consumer can rewind its offset and
  reprocess messages that were, from the broker's point of view, already
  "delivered." Publicly documented Kafka producer and consumer behaviour,
  Apache Kafka project documentation, kafka.apache.org, verified 2026-08-12.
- **Transactional Outbox.** Rather than trusting a network call to a
  broker at all inside the same transaction as a database write, the sender
  writes the outgoing message into an outbox table in the same database
  transaction that updates its own business entities. "Messages are
  guaranteed to be sent if and only if the database transaction commits"
  (Chris Richardson, microservices.io, Transactional Outbox,
  https://microservices.io/patterns/data/transactional-outbox.html, verified
  2026-08-12). A separate relay process, often a Change Data Capture reader
  on the outbox table, forwards rows to the broker and marks them sent. This
  variant solves the specific problem of a message being sent without a
  corresponding committed database change, or vice versa, which broker-only
  durability does not address on its own.
- **Cloud queue with visibility timeout.** Amazon SQS stores every message
  redundantly across availability zones on receipt. "Amazon SQS stores all
  message queues and messages within a single, highly-available AWS region
  with multiple redundant Availability Zones (AZs), so that no single
  computer, network, or AZ failure can make messages inaccessible" (AWS,
  Amazon SQS FAQs, https://aws.amazon.com/sqs/faqs/, verified 2026-08-12).
  Instead of an explicit ack channel, a consumer that receives a message is
  granted an exclusive visibility timeout, during which the message is
  hidden from other consumers; deleting the message within that window is
  the acknowledgement, and failing to delete it before the timeout expires
  makes it visible again for redelivery.
- **Write-ahead log at the application layer.** Where no broker is in the
  path at all, an application can implement the same idea itself, append the
  outbound message to a local durable log or table before attempting to send
  it over the wire, and only remove it from the log once the remote side has
  confirmed durable receipt. This is the pattern's structure with the broker
  role folded into application code, common in embedded and edge systems
  that cannot depend on an external message broker being reachable.

## 9. Known production uses

- **Apache Kafka**, as used by LinkedIn (its originating organisation) and
  widely elsewhere, implements the replicated commit log variant. Producers
  configuring `acks=all` combined with a topic's `min.insync.replicas`
  setting get an acknowledgement only after the message is replicated to
  enough brokers to survive a leader failure, which is Kafka's documented
  mechanism for at-least-once, durable delivery (Apache Kafka documentation,
  kafka.apache.org/documentation, verified 2026-08-12).
- **RabbitMQ**, used across a very wide range of enterprise messaging
  deployments, implements the durable-queue-plus-publisher-confirms variant
  directly, and its own documentation states the guarantee in exactly the
  Guaranteed Delivery terms, that a persistent message routed to a durable
  queue is confirmed only "after persisting the message to disk" (RabbitMQ
  documentation, Confirms, https://www.rabbitmq.com/docs/confirms, verified
  2026-08-12).
- **Amazon SQS** implements the pattern as a managed cloud queue, with
  redundant storage across availability zones and a visibility-timeout-based
  acknowledgement model, documented in AWS's own FAQ as protecting against
  "single computer, network, or AZ failure" causing message loss (AWS,
  Amazon SQS FAQs, https://aws.amazon.com/sqs/faqs/, verified 2026-08-12).
- **The Java Message Service (JMS) specification** standardises the pattern
  at the API level through `DeliveryMode.PERSISTENT`, a per-message flag that
  every JMS-compliant broker (ActiveMQ, IBM MQ, and others) must honour by
  writing the message to stable storage before acknowledging the producer
  (Oracle Java EE 8, `javax.jms.DeliveryMode` API documentation, verified
  against the archived Oracle javadoc 2026-08-12).
- **The Transactional Outbox pattern**, documented and named by Chris
  Richardson as part of the microservices.io pattern catalog and adopted in
  practice by teams using Debezium-based Change Data Capture to relay outbox
  rows into Kafka, is a widely cited production technique specifically for
  combining a database commit with guaranteed message delivery
  (https://microservices.io/patterns/data/transactional-outbox.html, verified
  2026-08-12; Debezium project, an open-source CDC platform commonly paired
  with this exact outbox-to-Kafka relay role, debezium.io, referenced as the
  standard tooling for this variant).

## 10. Consequences

Positive.

- A message, once accepted by the sender's local store, survives the crash
  of any single process or machine on its path to the receiver, which is a
  materially stronger guarantee than an in-memory or unbuffered channel
  provides.
- It decouples the sender's and receiver's uptime. The sender does not need
  the receiver to be reachable at send time, and the receiver does not need
  to be running when the message is produced.
- It creates a natural, inspectable audit trail. A queue or log of durable
  messages is a record that can be replayed, counted, and reconciled against
  business outcomes, which is valuable independent of the delivery guarantee
  itself.
- Combined with Transactional Outbox, it closes the specific dual-write gap
  between "the database was updated" and "the event was published," which is
  otherwise a routinely underestimated source of production incidents.

Negative.

- It converts exactly-once intuition into at-least-once reality. Every
  consumer of a guaranteed-delivery channel must be written to tolerate
  redelivery, and a codebase that forgets this will eventually double-charge
  a customer or double-ship an order.
- It adds real, ongoing operational load. Disk or replicated storage must be
  sized and monitored, a dead letter path must itself be watched or
  messages pile up invisibly, and a visibility timeout or lock duration
  must be tuned against how long processing actually takes, or messages
  either redeliver too eagerly or hang too long after a genuine consumer
  crash.
- It adds latency on the send path, because the sender's call cannot return
  until at least one durable write, and in a replicated system a quorum
  write, has completed.
- A poorly bounded retry policy on the store-and-forward relay can turn one
  poison message into a queue-wide stall, particularly in variants that
  preserve strict per-partition ordering.

## 11. Failure modes and misuse

This section draws on operational experience and is labelled as judgement
rather than sourced claim, except where a specific mechanism is named.

- Symptom, duplicate business effects (double charges, double shipments)
  under normal operation, not just during an incident.
  Cause, the team implemented durable delivery and assumed it implied
  exactly-once, so the consumer's side effect is not idempotent and every
  redelivery, which is expected and routine under at-least-once semantics,
  reapplies the effect.
  Fix, make the consumer's write idempotent, keyed on a message ID or
  business idempotency key, so redelivery is a safe no-op (see Idempotent
  Receiver).

- Symptom, the queue depth graph climbs steadily and consumers appear
  idle or crash-looping, but nobody notices until a customer complains
  about a very late order.
  Cause, a poison message, one that always fails processing, is retried
  indefinitely with no dead letter routing, and depending on the broker's
  ordering guarantee it can block every message behind it in the same
  partition or queue.
  Fix, configure a maximum redelivery count with a Dead Letter Channel as
  the terminal destination, and alert on non-empty dead letter queues as a
  first-class operational signal, not an afterthought.

- Symptom, messages are occasionally lost despite the team believing
  delivery is guaranteed, and the loss correlates with deploys or broker
  restarts.
  Cause, the producer is acknowledging locally, on a successful network
  write to the broker's TCP connection, rather than waiting for the
  broker's durable confirmation. The "guarantee" exists in the broker's
  design but was never actually invoked by the client code, for example a
  Kafka producer left at the default `acks=1` (leader-only, not
  `acks=all`) or a RabbitMQ publisher not using confirm mode at all.
  Fix, audit the client configuration against the broker's actual
  durability API, not against the broker's marketing description of what it
  is capable of.

- Symptom, a message is durably stored and eventually delivered, but
  arrives to the consumer with a payload that reflects a database state
  the sender rolled back moments after publishing.
  Cause, the sender published the message to the broker and committed its
  database transaction as two separate, non-atomic steps, so a crash or a
  rollback between them leaves the message durably queued for a state that
  never actually became true, or a committed change with no message sent
  at all.
  Fix, adopt Transactional Outbox so the message write and the business
  data write share one database transaction, and let a separate relay
  process own the actual broker publish.

- Symptom, the system is described as using Guaranteed Delivery, but
  under a full data-center outage, in-flight messages are lost anyway.
  Cause, the pattern was implemented with single-node persistence, write to
  local disk with no replication, which survives a process crash and even
  an OS reboot but not the loss of the disk or the machine itself.
  Fix, be explicit, in the design and in the SLA communicated to
  stakeholders, about which failure domain the durability actually covers.
  Single-node fsync survives a crash, not a lost disk. Only a replicated
  store, as Kafka's `min.insync.replicas` or SQS's multi-AZ storage
  provides, survives loss of the machine itself.

## 12. Trade-off matrix

| Concern | Guaranteed Delivery | Fire-and-forget channel | Synchronous request/response with client retry | Transactional Outbox alone (no broker durability) |
|---|---|---|---|---|
| Message survives broker or receiver crash | Yes, by design | No | N/A, no message exists until the call is made | Survives the outbox table, not the downstream broker hop unless combined |
| Latency added to producer | Moderate, one durable write or quorum write | None | Depends on callee availability | Low, one local database write |
| Requires idempotent consumer | Yes, effectively mandatory | Not applicable, no delivery guarantee to duplicate | Yes, if the client retries on timeout | Yes, for the same reason once combined with a broker |
| Decouples sender and receiver uptime | Yes | Partially, until the buffer overflows | No, both must be reachable at call time | Yes for the write, no for the relay's own uptime |
| Solves the database-plus-message dual write problem | Not by itself | No | Not applicable | Yes, this is its specific job |
| Operational surface added | Durable storage, retention, dead letter monitoring | Minimal | Minimal beyond retry and timeout tuning | Outbox table growth, relay process health |

## 13. Related and incompatible patterns

- **Message Channel and Point-to-Point Channel** are the substrate
  Guaranteed Delivery is applied to. The pattern is a durability property
  layered onto an already-chosen channel, not a channel type of its own.
- **Dead Letter Channel** is a required companion for any production
  Guaranteed Delivery implementation, because a durable retry mechanism with
  no terminal failure path will retry a permanently broken message forever,
  consuming resources and hiding the failure from anyone who should see it.
- **Transactional Outbox** composes with Guaranteed Delivery to close the
  specific gap between a database commit and a broker publish. Guaranteed
  Delivery alone protects a message once it is in the broker, while
  Transactional Outbox protects the moment before that, when the message
  and the business data must agree.
- **Idempotent Receiver** is functionally required wherever Guaranteed
  Delivery is used, because the pattern produces at-least-once delivery,
  and a consumer without idempotent handling will double-apply redelivered
  messages.
- **Retry and Circuit Breaker** govern the relay's own behaviour when the
  next hop is unreachable. Guaranteed Delivery specifies that the message is
  held until confirmed, while retry and circuit breaker specify how
  aggressively and how long the relay keeps attempting the handoff.
- **Incompatibility.** Guaranteed Delivery is not compatible with a design
  goal of strict exactly-once, fire-and-forget simplicity at the same time.
  A team that wants both minimal latency and zero possibility of duplicate
  processing without any idempotency layer has picked requirements that
  this pattern, on its own, cannot satisfy. Something has to give, usually
  the idempotency layer being added rather than the guarantee being
  dropped.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently uses a non-durable or
best-effort channel.

1. Identify the specific channel where message loss is a real business
   risk, rather than applying the pattern uniformly across every channel in
   the system; not every message needs it, and applying it everywhere adds
   cost without proportional benefit.
2. Turn on the broker's durability primitives for that channel, durable
   queues plus persistent messages and publisher confirms in a broker like
   RabbitMQ, or `acks=all` with an appropriate `min.insync.replicas` on the
   relevant Kafka topic.
3. Change the consumer from auto-acknowledge-on-receipt to
   acknowledge-after-durable-processing, and verify this by killing the
   consumer process mid-processing in a test environment and confirming the
   message is redelivered rather than lost.
4. Add a maximum redelivery count and route exhausted messages to a Dead
   Letter Channel, with monitoring on that channel's depth.
5. Audit the consumer's side effect for idempotency. If it is not
   idempotent, add a deduplication key, typically the message ID stored
   alongside the effect it produced, checked before the effect is reapplied.
6. If the producer's message content depends on data written to its own
   database in the same operation, migrate the producer to Transactional
   Outbox rather than publishing directly, to close the dual-write gap.

Removing the pattern, when the operational cost stops being justified.

1. Confirm the actual business tolerance for message loss has changed, in
   writing, with whoever owns the downstream business process; do not
   remove durability because it is inconvenient without that confirmation.
2. Switch the channel's persistence and consumer acknowledgement mode back
   to a lighter-weight setting, for example auto-ack, or `acks=1` instead
   of `acks=all`, one channel at a time.
3. Remove or repurpose the dead letter monitoring and idempotency
   deduplication logic only after confirming the channel is no longer
   redelivering messages, since idempotency logic left in place is
   harmless, while removed idempotency logic on a channel that still
   redelivers is not.
4. Re-measure end-to-end latency and confirm the expected improvement
   materialised, to validate the removal was worth the reduced guarantee.

## 15. Testing and verification

- **Crash injection between store and forward.** The single most valuable
  test for this pattern is deliberately killing the receiver process after
  it has read a message but before it acknowledges, then asserting the
  message is redelivered rather than lost. Most message broker test
  harnesses, for example testcontainers-managed RabbitMQ or Kafka
  instances, support this directly by stopping the consumer container
  mid-test.
- **Idempotency verification.** Deliver the same message twice,
  deliberately, in a test, and assert the observable business state after
  the second delivery is identical to the state after the first, not
  doubled. This is the test that catches the "guaranteed delivery implies
  exactly-once" misconception directly.
- **Poison message and dead letter routing.** Publish a message the
  consumer will always fail to process, and assert it is routed to the
  dead letter channel after the configured retry count rather than retried
  forever; assert the dead letter channel's depth metric increments.
- **Ordering verification, where ordering matters.** Publish a sequence of
  messages with a monotonic sequence number in the payload and assert the
  consumer observes them in order, or, if the implementation uses
  parallel redelivery, assert explicitly that out-of-order delivery is
  expected and tolerated by the consumer's logic.
- **Test doubles.** An in-memory fake broker that mimics the durable store,
  ack, and redelivery-on-timeout behaviour is more useful here than a plain
  mock, because the behaviour under test is precisely the store-ack-retry
  state machine, not just whether send was called. A mock that only asserts
  a method was called cannot catch a missing acknowledgement bug.

## 16. Observability signals

- **Queue or partition depth**, both in absolute count and rate of change.
  A healthy system shows depth oscillating near zero as consumers keep
  pace; a failing consumer shows monotonically increasing depth.
- **Dead letter channel depth**, which should be at or near zero in steady
  state. Any sustained non-zero value is a signal that some class of
  message is permanently unprocessable and needs human attention.
- **Redelivery count per message**, or the distribution of ack latency
  across the fleet, to distinguish "consumers are healthy but briefly slow"
  from "a specific message or consumer type is consistently failing and
  retrying."
- **Producer acknowledgement latency**, since a sudden increase often means
  the broker's durability write path, disk, replication, is degraded
  before it becomes an outright outage.
- **In-sync replica count** for a replicated log implementation like Kafka,
  because a topic falling below its configured `min.insync.replicas`
  changes the actual durability guarantee being delivered even while the
  producer's `acks=all` setting has not changed.
- **Oldest unacknowledged message age**, which directly answers how long
  the slowest in-flight message has been stuck, a metric that a raw queue
  depth number does not surface on its own.

## 17. Security and privacy implications

Persisting a message to disk or to a replicated log, which is the mechanism
this pattern depends on, extends the message's data retention footprint
beyond the instant of transmission that a non-durable channel would have.
That has two direct consequences that are analytical rather than sourced
from a specific document.

- Any personally identifiable or sensitive payload that flows through a
  Guaranteed Delivery channel is now at rest, potentially for a
  configurable retention period, on the broker's storage, its replicas, and
  any dead letter store it is eventually routed to if unprocessable. That
  data is now in scope for the same encryption-at-rest, access control, and
  data retention policy that applies to any other durable store in the
  system, and treating a message queue as transient when it is actually
  durable is a common gap in a data protection audit.
- A dead letter channel in particular tends to be under-monitored from a
  security standpoint precisely because it is operationally a backwater. A
  message containing sensitive data that fails processing and lands there
  can sit, readable by anyone with dead-letter-queue access, for far longer
  than the same data would have lived in the primary happy path.
- The store-and-forward relay is a component with read access to every
  message in flight, which makes it a natural target for an attacker
  seeking a single point of interception. The access control on the relay
  process and its credentials deserves the same scrutiny as the broker
  itself, not less, because it is often deployed as merely infrastructure
  glue.

## 18. References

- Gregor Hohpe, Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
  Messaging Systems chapter, Guaranteed Delivery. Problem and solution
  statements corroborated at
  https://www.enterpriseintegrationpatterns.com/patterns/messaging/GuaranteedMessaging.html,
  verified 2026-08-12.
- RabbitMQ documentation, Confirms,
  https://www.rabbitmq.com/docs/confirms, verified 2026-08-12.
- Apache Kafka project documentation, kafka.apache.org/documentation,
  producer `acks` configuration and consumer offset commit behaviour,
  verified against the publicly available Apache Kafka project
  documentation site, 2026-08-12.
- Amazon Web Services, Amazon SQS FAQs,
  https://aws.amazon.com/sqs/faqs/, verified 2026-08-12.
- Chris Richardson, microservices.io, Transactional Outbox,
  https://microservices.io/patterns/data/transactional-outbox.html,
  verified 2026-08-12.
- Oracle, Java EE 8 API specification, `javax.jms.DeliveryMode`, JMS
  persistent delivery mode, verified against the archived Oracle Java EE 8
  javadoc, 2026-08-12.
- Debezium project documentation, debezium.io, referenced for its common
  role as the Change Data Capture relay in Transactional-Outbox-to-broker
  deployments; general project description, not a specific quoted claim.

## Code examples

Three languages, TypeScript, Python, and Go. All three are common
implementation languages for message-driven services and each idiom below
maps directly to a real client library shape, a RabbitMQ-style
confirm-and-ack channel, an SQS-style receive-and-delete queue, and a
Kafka-style produce-with-acks-all plus commit-on-process consumer, reduced
to an in-memory simulation so the sample is runnable without a live broker.
Java, Rust, and Swift are omitted here because the pattern's structure does
not change across those languages, it is entirely a broker and protocol
concern rather than a language-idiom concern, so a fourth or fifth restating
of the same state machine would not add anything the three below do not
already show.

### TypeScript. Durable store with ack-after-process and redelivery

```typescript
type Msg = { id: string; payload: string; attempts: number };

class DurableQueue {
  private store = new Map<string, Msg>();
  private deadLetter: Msg[] = [];
  private readonly maxAttempts = 3;

  send(payload: string): string {
    const id = crypto.randomUUID();
    // The send call does not "complete" until the message is in the
    // durable store, simulated here by the synchronous Map write.
    this.store.set(id, { id, payload, attempts: 0 });
    return id;
  }

  async deliverOnce(process: (m: Msg) => Promise<boolean>): Promise<void> {
    for (const [id, msg] of Array.from(this.store.entries())) {
      msg.attempts += 1;
      const succeeded = await process(msg);
      if (succeeded) {
        // Ack. only now is the message purged from the durable store.
        this.store.delete(id);
      } else if (msg.attempts >= this.maxAttempts) {
        this.store.delete(id);
        this.deadLetter.push(msg);
      }
      // else, left in the store, will be redelivered on the next pass.
    }
  }

  pendingCount(): number {
    return this.store.size;
  }

  deadLetterCount(): number {
    return this.deadLetter.length;
  }
}

async function main() {
  const q = new DurableQueue();
  q.send("order-42-created");
  q.send("order-43-created");

  let calls = 0;
  await q.deliverOnce(async (m) => {
    calls += 1;
    if (m.payload === "order-42-created" && m.attempts < 2) return false;
    return true;
  });
  await q.deliverOnce(async (m) => {
    calls += 1;
    return true;
  });

  console.log("pending", q.pendingCount(), "deadLetter", q.deadLetterCount(), "processCalls", calls);
}

main();
```

### Python. Transactional outbox plus a relay that forwards only after confirmation

```python
import uuid
from dataclasses import dataclass


@dataclass
class OutboxRow:
    id: str
    payload: str
    sent: bool = False


class Database:
    """Simulates a single ACID transaction covering the business write
    and the outbox insert together."""

    def __init__(self):
        self.orders: list[str] = []
        self.outbox: dict[str, OutboxRow] = {}

    def create_order_with_event(self, order_id: str, event_payload: str) -> None:
        # Both writes happen in the same simulated transaction. either
        # both land, or (on an exception before this point) neither does.
        self.orders.append(order_id)
        row_id = str(uuid.uuid4())
        self.outbox[row_id] = OutboxRow(id=row_id, payload=event_payload)


class Broker:
    def __init__(self):
        self.durable_log: list[str] = []

    def publish_durably(self, payload: str) -> bool:
        # A durable write, only after which is the publish confirmed.
        self.durable_log.append(payload)
        return True


def relay(db: Database, broker: Broker) -> int:
    """The separate process that forwards outbox rows to the broker and
    marks them sent only after the broker durably confirms receipt."""
    forwarded = 0
    for row in db.outbox.values():
        if row.sent:
            continue
        confirmed = broker.publish_durably(row.payload)
        if confirmed:
            row.sent = True
            forwarded += 1
    return forwarded


def main() -> None:
    db = Database()
    broker = Broker()

    db.create_order_with_event("order-42", "order-42-created")
    db.create_order_with_event("order-43", "order-43-created")

    forwarded = relay(db, broker)

    assert forwarded == 2
    assert all(row.sent for row in db.outbox.values())
    assert broker.durable_log == ["order-42-created", "order-43-created"]

    print(f"orders={len(db.orders)} outbox_rows={len(db.outbox)} "
          f"forwarded={forwarded} broker_log={broker.durable_log}")


if __name__ == "__main__":
    main()
```

### Go. Visibility-timeout queue, modelling the Amazon SQS receive-and-delete idiom

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type message struct {
	id       int
	payload  string
	hiddenAt time.Time
	deleted  bool
}

// visibilityQueue models the SQS-style pattern. a message is not removed on
// delivery, only hidden for a visibility window, and becomes redeliverable
// again if the consumer never deletes it within that window.
type visibilityQueue struct {
	mu         sync.Mutex
	messages   []*message
	nextID     int
	visibility time.Duration
}

func newVisibilityQueue(visibility time.Duration) *visibilityQueue {
	return &visibilityQueue{visibility: visibility}
}

func (q *visibilityQueue) send(payload string) int {
	q.mu.Lock()
	defer q.mu.Unlock()
	q.nextID++
	q.messages = append(q.messages, &message{id: q.nextID, payload: payload})
	return q.nextID
}

func (q *visibilityQueue) receive(now time.Time) *message {
	q.mu.Lock()
	defer q.mu.Unlock()
	for _, m := range q.messages {
		if m.deleted {
			continue
		}
		if now.After(m.hiddenAt) {
			m.hiddenAt = now.Add(q.visibility)
			return m
		}
	}
	return nil
}

func (q *visibilityQueue) delete(id int) {
	q.mu.Lock()
	defer q.mu.Unlock()
	for _, m := range q.messages {
		if m.id == id {
			m.deleted = true
		}
	}
}

func (q *visibilityQueue) pendingCount() int {
	q.mu.Lock()
	defer q.mu.Unlock()
	n := 0
	for _, m := range q.messages {
		if !m.deleted {
			n++
		}
	}
	return n
}

func main() {
	visibility := 5 * time.Millisecond
	q := newVisibilityQueue(visibility)
	q.send("inventory-reserved")

	t0 := time.Now()
	m := q.receive(t0)
	if m == nil {
		panic("expected a message on first receive")
	}
	// Simulate a consumer crash. it never calls delete before the
	// visibility window expires, so the message must become receivable
	// again rather than being lost.

	tAfterTimeout := t0.Add(visibility + time.Millisecond)
	redelivered := q.receive(tAfterTimeout)
	if redelivered == nil || redelivered.id != m.id {
		panic("expected the same message to be redelivered after the visibility timeout")
	}

	// This time the consumer succeeds and deletes it. the acknowledgement.
	q.delete(redelivered.id)

	fmt.Println("pending after successful processing:", q.pendingCount())
}
```
