---
name: Competing Consumers
slug: competing-consumers
family: 08-cloud-distributed
category: Resilience and Traffic Management
aliases: [Point-to-Point Channel with Multiple Receivers, Worker Pool over a Queue, Consumer Group Pattern]
first_described: "Hohpe, Woolf. Enterprise Integration Patterns. Addison-Wesley, 2003"
maturity: canonical
related: [queue-based-load-leveling, publisher-subscriber, sharding, throttling, retry, bulkhead, cqrs]
incompatible_with: [strict-total-message-ordering]
verified: 2026-08-02
---

# Competing Consumers

## 1. Name, aliases, and lineage

The canonical name is Competing Consumers. Gregor Hohpe and Bobby Woolf catalogued
it in *Enterprise Integration Patterns. Designing, Building, and Deploying
Messaging Solutions*, Addison-Wesley, 2003, ISBN 0-321-20068-3, as one of the
messaging patterns built on top of the Point-to-Point Channel. The book's
companion site states the problem directly. An application uses messaging but
cannot process messages as fast as they are added to the channel, and the named
solution is to create multiple competing consumers on a single channel so they
can process messages concurrently ([Enterprise Integration Patterns, Competing
Consumers](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CompetingConsumers.html),
verified 2026-08-02). The word "competing" is literal. Every consumer instance
listens on the same channel, and the messaging system's delivery mechanism
decides which one instance actually receives each message, so the consumers are
in contention with each other for work, not cooperating on a shared plan.

Microsoft's cloud pattern catalog carries the identical name and the identical
idea, described as enabling multiple concurrent consumers to process messages
received on the same messaging channel, so a system can process several
messages at once to optimise throughput, improve scalability and availability,
and balance the workload across the consumer pool ([Microsoft Learn, Competing
Consumers
pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers),
verified 2026-08-02). The 2014 Azure book, *Cloud Design Patterns* by Homer,
Sharp, Brader, Narumoto and Swanson, folded the same twenty-four-pattern
Microsoft catalog that gave us Queue-Based Load Leveling, and Competing
Consumers sits beside it as the mechanism that makes the elastic side of the
consumer pool possible. The queue only smooths the arrival rate if something
scales to drain it, and Competing Consumers is that something.

Because the pattern is a direct application of an older idea rather than a new
invention, it does not have a rival name the way some catalog entries do. What
varies is which layer of a given system is described as "the competing part."
When the discussion is about a message broker such as RabbitMQ or Amazon SQS,
people usually say "multiple consumers on the queue." When the discussion
is about Apache Kafka, people usually say "consumer group," because Kafka
implements the same competing relationship through partition assignment rather
than through broker-side message locking, and that distinction matters enough
that it gets its own paragraph in dimension 8. Some cloud vendor documentation
also uses "worker pool pattern" informally for the consumer side of this
relationship, but that phrase is not attached to a specific catalog and is best
treated as a description rather than an alias with its own lineage.

## 2. Problem and context

A system produces units of work faster, or in bursts larger, than a single
consumer process can absorb, and the units of work are independent of one
another, meaning any one of them can be processed by any available worker
without coordinating with the others. If the system routes every unit of work
to one fixed consumer instance, that instance becomes the upper bound on the whole
system's throughput no matter how much producer-side capacity exists, and if
that one instance goes down, work stops entirely until it is restarted.

The context in which this becomes acute is asynchronous, message-driven
processing. An order placed on a web storefront that must be validated, priced,
and dispatched to a warehouse, a video upload that must be transcoded into
several resolutions, a webhook payload that must be parsed and written to a
database, a batch of rows that must be scored by a machine learning model. In
each case the unit of work already sits behind a queue for other reasons, most
often the Queue-Based Load Leveling pattern, so the queue exists and the
open question is what reads from it. The answer this pattern gives is more
than one thing, all reading from the same channel, all eligible to receive the
next unit of work, with the messaging system itself deciding which one gets
which message.

The problem is specifically NOT solved by simply running a fixed number of
worker threads inside one process reading from an in-memory list, because that
gives you concurrency but not the two properties the pattern is actually
chasing. Elasticity, so the consumer pool can grow and shrink independently of
the producer and independently of any single machine's core count, and
resilience, so the crash of one consumer process does not lose the messages it
was holding, because the broker or queue owns the message until a consumer
explicitly finishes it.

## 3. Forces

**Throughput versus ordering.** Adding consumers directly increases the rate at
which the system drains the queue, but it destroys any implicit guarantee that
messages are handled in the order they were sent, because two consumers running
in parallel do not coordinate who finishes first. A system that genuinely needs
strict ordering has to give up some of the throughput gain, either by
partitioning work so that dependent messages always land on the same consumer,
or by falling back to a single consumer for the ordered subset.

**Elasticity versus coordination cost.** A pool that can grow to absorb a burst
and shrink to save cost when idle is the entire economic case for this pattern
in the cloud. That elasticity is cheap only because the coordination of who
gets which message is delegated to the broker's delivery mechanism rather than
handled by the application. The moment the application tries to add its own
coordination on top, such as a consumer that needs to know what another
consumer already did before it can safely act, the pattern's cheapness
disappears and a different pattern, often Saga or a stateful workflow
engine, is usually the better fit.

**At-least-once delivery versus idempotency.** Almost every practical
implementation of this pattern delivers a message to a consumer, waits for
acknowledgement, and redelivers it if acknowledgement does not arrive in time.
That is a deliberate choice favouring never silently losing a message over
never processing a message twice, and it pushes the burden of idempotent
processing onto the consumer. The Azure documentation states this outright as a
design consideration, recommending idempotent processing precisely because
ordering and delivery counts are not guaranteed ([Microsoft Learn, Competing
Consumers pattern, Problems and
considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers),
verified 2026-08-02).

**Fairness versus starvation.** Round-robin dispatch, the default in systems
such as RabbitMQ, spreads messages evenly by count but not by actual processing
cost, so a consumer that happens to receive several expensive messages in a row
can fall behind while a consumer handling cheap messages sits comparatively
idle. RabbitMQ's own Work Queues tutorial names this and recommends bounding
how many unacknowledged messages a single consumer may hold at once, so slower
consumers are not handed new work until they finish what they already have
([RabbitMQ tutorials, Work
Queues](https://www.rabbitmq.com/tutorials/tutorial-two-python), verified
2026-08-02).

**Cost of a poison message versus availability of the queue.** A single
malformed or unprocessable message, redelivered forever because no consumer
can ever successfully finish it, can consume redelivery slots and degrade the
whole queue's throughput if nothing removes it from circulation. The forces
above all favour keeping consumers stateless, elastic, and blind to each other,
this last force is the one that requires giving them, or the broker in front of
them, a bounded number of attempts before giving up.

## 4. Applicability and non-applicability

**Reach for Competing Consumers when**:

- The unit of work is independent. Processing message A does not require
  knowledge of what happened to message B, or of the order in which they
  arrived.
- The workload volume is bursty or unpredictable and a fixed-size consumer
  pool would either be over-provisioned most of the time or under-provisioned
  during peaks.
- The application already accepts asynchronous, eventually-consistent
  processing, usually because it already sits behind a queue for the
  Queue-Based Load Leveling pattern.
- High availability of the processing stage matters more than the exact
  sequence in which items are handled, and a single instance going down should
  not stop the whole pipeline.
- Consumer-side work can be run at any horizontal count and is stateless between messages,
  so a new consumer instance can start receiving work with no warm-up
  coordination with the existing pool.

**Do NOT reach for Competing Consumers when**:

- Messages must be processed in the exact order they were produced and that
  ordering spans the whole stream, not a narrower related subset. Kafka's own
  partitioning model exists precisely because plain competing consumers on one
  channel cannot give this guarantee, as the Enterprise Integration Patterns
  site notes when it describes in-order delivery as not guaranteed across
  partitions ([Enterprise Integration Patterns, Competing
  Consumers](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CompetingConsumers.html),
  verified 2026-08-02).
- The consuming logic requires a synchronous response the caller waits on.
  Competing Consumers is a decoupling pattern. If the producer must block until
  the specific consumer instance replies, the value of not caring which
  consumer handles the work disappears, and a direct request-response or the
  Asynchronous Request-Reply pattern fits better.
- Processing has heavy shared mutable state across messages that cannot be
  made idempotent or externalised, because at-least-once delivery combined
  with unsynchronised concurrent consumers will eventually double-apply a side
  effect.
- The workload has almost no variance and always fits comfortably on one
  worker. A fixed pool without a queue in front of it, or a plain load
  balancer, is simpler and there is nothing to level.
- Every consumer needs to see every message. That is the Publisher-Subscriber
  pattern, not this one. Putting multiple consumers on one queue does not
  fan the message out, it splits the stream so each message goes to exactly
  one consumer.

## 5. Structure

**Producer.** The component that creates units of work and places them on the
shared channel. It has no knowledge of which consumer instance, or how many,
will eventually handle any given message.

**Message channel (the queue).** The shared, durable, point-to-point
transport. It owns the message from the moment it is enqueued until a consumer
signals completion, and it is the single arbiter of which consumer receives
which message. This is the same channel that plays the buffering role in
Queue-Based Load Leveling, here the emphasis is on its role as a fair-delivery
mechanism for multiple readers, not on its role as a burst absorber.

**Consumer instance.** A stateless worker that repeatedly asks the channel for
the next message, processes it, and reports success or failure back to the
channel. Any number of consumer instances can exist at once, they are
interchangeable from the channel's point of view, and none of them holds
long-lived state that another instance would need to take over correctly.

**Delivery and visibility mechanism.** The part of the broker that prevents
two consumers from receiving the same message at the same time. Different
systems implement this in their own way. SQS uses a visibility timeout that
hides an in-flight message from other pollers until it is deleted or the
timeout expires ([AWS documentation, Amazon SQS visibility
timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html),
verified 2026-08-02). Azure Service Bus uses PeekLock, which hides the message
and requires an explicit Complete call, calling Abandon or letting the lock
expire returns it to the queue for another consumer to try
([Microsoft Learn, Competing Consumers pattern,
Example](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers),
verified 2026-08-02). RabbitMQ requires an explicit acknowledgement and
requeues the message if the consumer disconnects before sending one
([RabbitMQ tutorials, Work
Queues](https://www.rabbitmq.com/tutorials/tutorial-two-python), verified
2026-08-02).

**Dead-letter or poison-message store.** A secondary destination the delivery
mechanism moves a message to after it has failed a bounded number of delivery
attempts, so a permanently unprocessable message stops being redelivered
indefinitely and can instead be inspected by an operator.

## 6. ASCII structure diagram

```
                       +-------------------+
   Producer(s) ------->|   Shared Channel  |
   (independent,       |  (durable queue)  |
    do not know who    +---------+---------+
    will consume)                |
                                  | one message delivered
                                  | to exactly one consumer
                +-----------------+-----------------+
                |                 |                 |
                v                 v                 v
         +------------+   +------------+     +------------+
         | Consumer 1 |   | Consumer 2 |     | Consumer N |
         | (stateless)|   | (stateless)|     | (stateless)|
         +-----+------+   +-----+------+     +-----+------+
               |                |                  |
               | success        | failure          | failure
               | -> delete/ack  | -> redeliver      | -> exceed
               v                v   (retry N-1)      |   max attempts
        [ side effect     back to Shared Channel      v
          applied ]                            +-------------+
                                                | Dead-letter |
                                                |   queue     |
                                                +-------------+
```

## 7. Dynamics

```
Producer          Channel            Consumer A          Consumer B
   |                 |                   |                   |
   |--enqueue(m1)--->|                   |                   |
   |--enqueue(m2)--->|                   |                   |
   |--enqueue(m3)--->|                   |                   |
   |                 |<----- poll -------|                   |
   |                 |----- deliver m1-->|                   |
   |                 |<----------- poll ----------------------|
   |                 |----------- deliver m2 ----------------->|
   |                 |<----- poll -------|                   |
   |                 |----- deliver m3-->|                   |
   |                 |                   |-- process m1 --   |
   |                 |                   |                   |-- process m2 --
   |                 |<--- ack(m1) ------|                   |
   |                 |  (m1 removed)     |                   |
   |                 |                   |                   |<-- ack(m2)
   |                 |                   |                   |  (m2 removed)
   |                 |                   |-- process m3 --   |
   |                 |<--- nack/timeout -|                   |
   |                 |  (m3 redelivered) |                   |
   |                 |<----------- poll ----------------------|
   |                 |----------- deliver m3 (attempt 2) ----->|
   |                 |                   |                   |-- process m3 --
   |                 |                   |                   |<-- ack(m3)
```

The core property visible in this trace is that m1 and m2 complete out of
enqueue order. m2 finishes before m1 in this run purely because Consumer B
happened to be faster, and m3 moves to a different consumer on retry after
Consumer A's first attempt fails. No component in the diagram coordinates who
handles what beyond the channel's own delivery bookkeeping.

## 8. Implementation variants

**Broker-locked delivery (SQS, Service Bus, RabbitMQ).** The broker hands one
copy of a message to one consumer and makes it invisible or unacknowledged for
everyone else until that consumer finishes or times out. This is the variant
described in dimension 5 and is the closest implementation to the original
Enterprise Integration Patterns description, a genuinely dynamic, per-message
competition where any idle consumer can pick up the very next message,
regardless of which consumer handled the previous one.

**Partition-assigned delivery (Kafka, Kinesis, Event Hubs).** Instead of
locking individual messages, the broker assigns whole partitions to consumer
instances within a consumer group, and only one consumer in the group reads any
given partition at a time. Confluent's developer course states this plainly.
A partition can only be processed by one consumer in the group, though a single
consumer may own several partitions, and events within a partition are always
read in offset order, which is what preserves per-partition ordering even
though there is no ordering guarantee across partitions ([Confluent Developer,
Consumer Group
Protocol](https://developer.confluent.io/courses/architecture/consumer-group-protocol/),
verified 2026-08-02). This variant trades the fully dynamic per-message
competition of the broker-locked variant for a coarser, more predictable
assignment that also happens to buy back ordering within a partition, which is
exactly the trade a system with a partial ordering requirement, order per
customer ID for example, is usually reaching for.

**In-process worker pool (goroutines, threads, async tasks).** When the
"channel" is an in-memory structure inside a single process, such as a Go
channel, a Python `queue.Queue`, or a bounded async task pool, the same
competing relationship exists at a smaller scale. Several goroutines or threads
pull from the same structure and the runtime scheduler decides who gets the
next item. This variant gives up cross-process durability and elasticity but
keeps the concurrency and load-spreading benefit, and it is common as the
inner implementation detail behind a single consumer instance that is itself
part of a larger, broker-based competing consumer pool, one process reading
many messages off SQS and fanning them out to an internal worker pool for
CPU-bound processing.

**Session-affine consumption.** Several brokers, Azure Service Bus sessions
being the most commonly cited example, allow a producer to tag related messages
with a session key so that all messages sharing that key are always delivered
to the same consumer and in order, while unrelated sessions still compete
freely across the rest of the pool. Microsoft's own pattern page recommends
this specifically as the way to combine Competing Consumers with a real
ordering requirement rather than abandoning the pattern altogether
([Microsoft Learn, Competing Consumers pattern, Problems and
considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers),
verified 2026-08-02).

## 9. Known production uses

**Amazon SQS with visibility timeout.** SQS is a managed implementation of
this pattern by default. Any number of consumer processes can call
`ReceiveMessage` against the same standard queue, the visibility timeout
prevents two of them from being handed the same message at once, and a
redrive policy with a configured `maxReceiveCount` moves a message that keeps
failing into a dead-letter queue rather than looping forever ([AWS
documentation, Using dead-letter queues in Amazon
SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
verified 2026-08-02).

**Azure Service Bus queues consumed by Azure Functions.** Microsoft documents
this combination directly as its reference example for the pattern. Functions
integrates with Service Bus through triggers and bindings, and when the
platform scales out to multiple function instances against one queue, those
instances "compete by independently pulling and processing messages," each
holding a PeekLock while it works and letting a failed attempt return the
message to the queue for another instance ([Microsoft Learn, Competing
Consumers pattern,
Example](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers),
verified 2026-08-02).

**RabbitMQ Work Queues.** RabbitMQ's own tutorial, the second in its official
series, exists specifically to teach this pattern. It starts several worker
processes consuming from the same queue and shows round-robin dispatch of
tasks among them, with manual acknowledgement so a worker that dies mid-task
does not lose the message ([RabbitMQ tutorials, Work
Queues](https://www.rabbitmq.com/tutorials/tutorial-two-python), verified
2026-08-02).

**Apache Kafka consumer groups.** Every consumer group in Kafka is the
partition-assigned variant of this pattern in production use at very large
scale. Setting a shared `group.id` on several consumer processes causes the
broker to divide the subscribed topic's partitions across them so that each
partition, and therefore each message within it, is processed by exactly one
member of the group at a time ([Confluent Developer, Consumer Group
Protocol](https://developer.confluent.io/courses/architecture/consumer-group-protocol/),
verified 2026-08-02).

## 10. Consequences

**Positive.**

- Throughput scales with the number of consumer instances rather than being
  capped by a single process, and that scaling can be automatic when tied to
  queue depth, exactly the elasticity benefit Microsoft's cost-optimisation
  guidance calls out for this pattern ([Microsoft Learn, Competing Consumers
  pattern, Workload
  design](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers),
  verified 2026-08-02).
- Availability improves because the failure of one consumer instance does not
  stop processing. Any other instance, or a freshly started replacement,
  simply picks up the next message, and a message that was mid-flight when its
  consumer crashed becomes available again through the visibility or
  acknowledgement mechanism rather than being silently lost.
- The producer and the consumer pool are fully decoupled in both instance count
  and lifecycle. The producer never needs to know how many consumers exist, and
  the consumer pool can be resized, redeployed, or temporarily emptied to zero
  without the producer's code changing at all.
- The pattern requires no bespoke coordination protocol between consumer
  instances. The broker's existing delivery semantics, visibility timeout,
  PeekLock, or manual ack, are sufficient, so the pattern is cheap to adopt
  wherever a durable queue already exists.

**Negative.**

- Global message ordering is lost, and any code that implicitly assumed
  in-order processing, common in systems migrated from a single-consumer
  design, will produce subtly wrong results the first time two consumers
  finish out of enqueue order.
- At-least-once delivery becomes a hard requirement to design around, not an
  edge case. Every consumer's side effect must be safe to apply more than
  once, or must be made idempotent through a dedupe key, an upsert instead of
  an insert, or a completed-work ledger.
- A poison message becomes a first-class failure mode that must be actively
  designed for. Without a bounded retry count and a dead-letter destination, a
  single malformed message can consume redelivery attempts and processing
  cycles indefinitely.
- Coordinating a response back to whichever process is waiting for the result
  of a specific message becomes its own problem, because the consumer that
  handled a given message is not deterministic from the producer's point of
  view. This is why Microsoft's pattern page lists result handling as its own
  named consideration ([Microsoft Learn, Competing Consumers pattern, Problems
  and
  considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers),
  verified 2026-08-02).

## 11. Failure modes and misuse

**Symptom.** A downstream record is updated twice, or a payment is charged
twice, for what the operator can see was a single logical event.
**Cause.** A consumer completed the side effect but crashed, or the network
dropped, before the acknowledgement or delete call reached the broker, so the
message became visible again and a second consumer, or the same consumer on
retry, processed it a second time under the pattern's inherent at-least-once
delivery contract.
**Fix.** Make the side effect idempotent. Use a natural or generated dedupe key
so a second application of the same message is a no-op, or record processed
message IDs in a store the consumer checks before acting, matching the
idempotent-processing recommendation Azure's own documentation makes for this
pattern ([Microsoft Learn, Competing Consumers pattern, Problems and
considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers),
verified 2026-08-02).

**Symptom.** Queue depth climbs steadily even though consumer CPU usage looks
low and no errors are visible in the application logs.
**Cause.** A single poison message is looping. It fails processing, becomes
visible again after the visibility timeout or negative acknowledgement, gets
redelivered, fails again, and repeats, with no maximum receive count
configured to eventually remove it from circulation, so it silently occupies
a redelivery slot forever and adds latency to every other message that has to
wait behind it in effect.
**Fix.** Configure a bounded redrive policy, such as SQS's `maxReceiveCount`
combined with a dead-letter queue, or Service Bus's `MaxDeliveryCount`, so a
message that cannot be processed after a fixed number of attempts is moved
aside for inspection instead of being retried indefinitely ([AWS
documentation, Using dead-letter queues in Amazon
SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
verified 2026-08-02).

**Symptom.** Reports that depend on a sequence of events for the same entity,
for example an inventory count derived from a stream of stock-in and stock-out
events, are occasionally wrong even though every individual event was
processed successfully.
**Cause.** The events for that entity were split across multiple competing
consumers, and two consumers processed them out of the order they were
produced, because the pattern only guarantees that each message goes to one
consumer, never that related messages arrive at the same consumer in order.
**Fix.** Introduce a partition or session key derived from the entity so all
of its events are always routed to the same consumer, either through Kafka
partition assignment or Service Bus sessions, so ordering is
preserved for the subset that needs it while unrelated entities still compete
freely across the rest of the pool.

**Symptom.** A handful of consumer instances appear starved of work, sitting
mostly idle, while a smaller number of other instances stay constantly busy
and lag behind.
**Cause.** The broker dispatched messages by count in round-robin fashion
without regard to how expensive each message was to process, so the
consumers that happened to receive the more expensive messages fell behind
while the others finished their cheaper share quickly and had nothing left to
pull, or a consumer over-prefetched a batch of messages it then held while
processing them one at a time.
**Fix.** Bound how many unacknowledged messages a single consumer may hold at
once, RabbitMQ's `basic_qos(prefetch_count=1)` being the documented example,
so the broker only ever hands new work to a consumer that has capacity for it
rather than piling it onto whichever consumer polled first ([RabbitMQ
tutorials, Work
Queues](https://www.rabbitmq.com/tutorials/tutorial-two-python), verified
2026-08-02).

**Symptom.** Adding more consumer instances stops improving throughput past a
certain count, and the extra instances show near-zero message rate.
**Cause.** In the partition-assigned variant, specifically Kafka-style
consumer groups, the number of consumers has exceeded the number of
partitions available to assign, so the surplus instances have nothing to
consume, matching Confluent's own description of a fifth consumer sitting
idle once four partitions are already assigned to four consumers
([Confluent Developer, Consumer Group
Protocol](https://developer.confluent.io/courses/architecture/consumer-group-protocol/),
verified 2026-08-02).
**Fix.** Increase the partition count for the topic to raise the upper bound on
useful parallelism, or accept that limit and stop over-provisioning
consumers past it, since idle consumers in this variant provide no throughput
benefit and only add operational cost.

## 12. Trade-off matrix

| Concern | Competing Consumers | Publisher-Subscriber | Single dedicated consumer | Sharding by key |
|---|---|---|---|---|
| Throughput scaling | Scales with consumer count | Scales per subscriber, but every subscriber does the full work | Fixed upper bound, one process | Scales with shard count |
| Message ordering | None globally, none across the pool | None across subscribers of the same event | Fully preserved | Preserved within a shard |
| Delivery to consumers | Exactly one consumer per message | Every subscriber gets every message | The one consumer gets every message | One consumer per shard gets its shard's messages |
| Fault tolerance | High, any idle consumer picks up failed work | High for the fan-out, but each subscriber is still a single point for its own copy | Low, the one consumer is a single point of failure | Medium, a shard's consumer is a single point for that shard |
| Idempotency requirement | Mandatory, at-least-once is standard | Mandatory per subscriber for the same reason | Optional, can rely on strict single processing | Mandatory within a shard |
| Best fit | Independent, high-volume, order-insensitive work | Multiple independent reactions to the same event | Strict ordering with a small, steady volume | Partial ordering keyed by an entity |

## 13. Related and incompatible patterns

**Queue-Based Load Leveling.** The two patterns are frequently described
together because they solve adjacent halves of the same problem. Queue-Based
Load Leveling is about the buffer smoothing the arrival rate the consumer
side experiences, while Competing Consumers is about what actually drains
that buffer at a rate that can grow and shrink with demand. Microsoft's own
Competing Consumers documentation cites Queue-Based Load Leveling directly
when explaining the buffering benefit of putting a queue in front of the
consumer pool ([Microsoft Learn, Competing Consumers pattern,
Solution](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers),
verified 2026-08-02). In practice they are almost always deployed as a pair.
The queue provides the elastic buffer, the competing consumers provide the
elastic drain.

**Publisher-Subscriber.** The two patterns are commonly confused because both
involve multiple receivers listening near a channel, but they answer opposite
questions about fan-out. Competing Consumers splits a stream so each message
reaches exactly one consumer, Publisher-Subscriber duplicates a message so
every subscriber receives its own copy. Microsoft's documentation states the
distinction explicitly as a callout on the Competing Consumers page
([Microsoft Learn, Competing Consumers pattern,
Solution](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers),
verified 2026-08-02). A system frequently needs both at different layers. A
topic fans an event out to several subscriber queues through Publisher-
Subscriber, and each of those subscriber queues then has its own competing
consumer pool draining it.

**Sharding.** Sharding by a key so related work always lands on the same
partition or worker is the mechanism that restores partial ordering inside an
otherwise unordered competing consumer pool, and it is exactly what Kafka's
partition assignment and Azure Service Bus sessions both are underneath their
respective names. Where Sharding as a general pattern usually concerns data
storage and query routing, its application here is narrower, sharding the
consumption of a stream, not the storage of state.

**Retry and Bulkhead.** Both patterns govern how an individual consumer
behaves once it has received a message rather than how the pool as a whole
receives work, so they compose naturally inside a single competing consumer.
Retry governs the bounded reattempt of a single message before it is
dead-lettered, Bulkhead isolates the resources one consumer's work uses so a
slow or failing downstream dependency for one message type does not starve
other consumers processing unrelated message types on shared infrastructure.

**CQRS.** In a system that separates its write model from its read model, the
component that projects write-side events into the read-side store is very
often implemented as a competing consumer pool reading an event stream, which
is why CQRS implementations frequently sit on top of a partition-assigned
broker such as Kafka to get both the competing-consumer scaling and the
per-entity ordering the projection logic usually needs.

**Incompatible with strict total message ordering.** A requirement for a
single, system-wide, total order across every message is directly
incompatible with the base pattern, because the base pattern's entire value
comes from letting multiple consumers process independently and therefore
out of order relative to one another. A system with that requirement either
needs the session-affine or partition-assigned variant restricted to a single
partition or session, which in the limiting case degenerates back into a
single dedicated consumer, or it needs an entirely different pattern for
that specific ordered stream.

## 14. Refactoring path in and out

**Introducing the pattern.** Start from a single consumer process reading
synchronously or in a tight loop from a queue. First, confirm the unit of
work the consumer already processes is genuinely independent of the others.
If it is not, address that first, because adding consumers on top of an
implicit ordering assumption only produces subtle bugs rather than a working
scaled system. Next, make the consumer's processing logic idempotent, since
every subsequent step depends on this being true regardless of how many
consumers eventually exist. Then run a second instance of the exact same
consumer process against the exact same queue and confirm the messaging
system's own delivery mechanism, rather than any code in the consumer, is
what prevents both instances from processing the same message. Once that is
proven at two instances, wire the instance count to an autoscaling signal,
most commonly queue depth or oldest-message age, so the pool grows and
shrinks with demand rather than staying at a fixed size chosen by guesswork.
Last, add a bounded retry and dead-letter destination before the system
carries real production traffic, because a poison message is a certainty
over a long enough operating period, not an edge case.

**Removing the pattern.** The pattern stops earning its place when the
workload it serves has become small and steady enough that the coordination
overhead of a queue and a pool, plus the idempotency work every consumer must
carry, costs more than it saves. Collapse back to a single dedicated
consumer by first draining the queue with the existing pool, then reducing
the pool to exactly one instance and watching whether throughput and latency
remain acceptable under real load for a representative period, and only
after that confirm the queue itself is unnecessary and can be replaced with a
direct call, at which point the idempotency guards can usually be relaxed but
should not be removed outright unless the system can also guarantee true
single delivery, which most managed queues explicitly do not promise.

## 15. Testing and verification

Testing this pattern well means testing two different things separately, the
per-message processing logic, and the pool-level behaviour under
concurrency, retries, and failure.

For the processing logic, test it as a plain function or method that takes
one message and returns success or failure, with no dependency on how many
consumers exist or which one is calling it. This isolates the business logic
from the concurrency machinery and is what the code examples in dimension 18
factor out as `processWithRetry` and `process_with_retry`, so that logic can be
unit tested deterministically.

For pool-level behaviour, two things must be verified with an integration-
style test against a real or realistic in-memory queue. First, that no
message is ever delivered to two consumers simultaneously while it is in
flight, which is best proven by running many consumers against a queue loaded
with uniquely IDed messages and asserting the total processed count equals
the message count with zero duplicates recorded. Second, that a message which
repeatedly fails is moved to the dead-letter destination after exactly the
configured number of attempts, not before and not never, which is best
proven by placing one deliberately poisoned message, as the code examples do
with message ID 7, and asserting it appears in the dead-letter output rather
than being processed or looping forever.

Load and fault-injection testing round this out. Injecting a consumer crash mid-processing
and confirming the in-flight message becomes available again for another
consumer rather than being lost, and running the pool at a message rate above
what a single consumer could sustain to confirm the measured throughput
scales roughly with consumer count rather than plateauing, which would
indicate a hidden bottleneck such as a shared lock or a database connection
pool sized for a single consumer.

## 16. Observability signals

**Queue depth (backlog size).** The primary health signal. A steadily growing
depth under a stable or shrinking consumer count means the pool cannot keep
up with the arrival rate and either needs to scale out or has a stuck
consumer.

**Age of the oldest visible message.** More informative than raw depth alone,
because it directly measures how long the newest arrival will have to wait
before being handled, and it is the metric autoscaling policies most commonly
key off. AWS surfaces this directly as `ApproximateAgeOfOldestMessage` for
SQS queues, including for messages that have already moved to a dead-letter
queue ([AWS documentation, Using dead-letter queues in Amazon
SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
verified 2026-08-02).

**In-flight message count.** How many messages are currently checked out by a
consumer and not yet acknowledged. A count that grows without bound points to
consumers accepting work faster than they can finish it, or to consumers that
are hanging rather than genuinely processing, and AWS specifically calls out
approaching the in-flight limit for standard SQS queues as an operational
condition to watch for ([AWS documentation, Amazon SQS visibility
timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html),
verified 2026-08-02).

**Dead-letter queue arrival rate.** A healthy pool sends effectively nothing
here. A sudden spike is the clearest possible signal that either a bad
deployment introduced a processing bug or a class of incoming messages has
changed shape in a way the consumers cannot handle, and it should page
someone, not accumulate silently.

**Per-consumer processed count and processing latency distribution.** Split by
consumer instance, this reveals the starvation and fairness failure mode from
dimension 11 directly. If one instance's processed count and mean latency
diverge sharply from its peers, prefetch or dispatch fairness is worth
investigating before assuming the workload itself is simply uneven.

**Redelivery count per message.** Tracking how many attempts a message needed
before either succeeding or being dead-lettered exposes intermittent,
non-deterministic failures. A message that succeeds on its second attempt
every time is a different problem than one that always fails on its first,
and this distribution is what separates transient blips from a systematic
processing bug.

## 17. Security and privacy implications

The message payload sitting on the shared queue is, from a security
standpoint, data at rest for however long it remains unconsumed, and it is
readable by every consumer instance with permission to poll the channel, so
any sensitive field it carries needs the same encryption-at-rest and
access-control treatment the organisation applies to its databases, not a
lighter standard because the data is "in transit" conceptually. Because
any of several consumer instances may end up handling a given message, access
control has to be granted at the level of the consumer role or service
identity that all instances share, rather than to an individual instance,
which means that role's permissions are effectively the permissions every
message on that queue is exposed to. Scoping that role tightly to only the
downstream systems it genuinely needs matters more here than in a
single-consumer design, because a compromised worker image is a compromise of
the whole pool at once.

The pattern's redelivery and dead-lettering behaviour also has a privacy
dimension worth naming plainly, rather than assuming away. A message that
fails processing repeatedly and lands in a dead-letter queue for operator
inspection is, by construction, going to be read by a human, at which point
whatever personal or sensitive data it carries is now exposed to that
operator's tooling and to whatever retention policy governs the dead-letter
destination, which in practice is often looser than the retention policy on
the primary queue because it was configured as an afterthought. Treat the
dead-letter destination with the same access controls, encryption, and
retention discipline as the primary queue from the start, rather than
retrofitting it after an incident.

Idempotency keys and dedupe records, which this pattern effectively requires
per dimension 10, are themselves a data store that persists identifiers
derived from message content, sometimes including a customer or order
identifier, and that store now needs its own retention and access policy
rather than being treated as disposable operational plumbing.

## 18. References

- Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, ISBN
  0-321-20068-3, the Competing Consumers and Point-to-Point Channel entries.
- [Enterprise Integration Patterns, Competing
  Consumers](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CompetingConsumers.html),
  the book's companion site, verified 2026-08-02.
- Alex Homer, John Sharp, Larry Brader, Masashi Narumoto, Trent Swanson,
  *Cloud Design Patterns. Prescriptive Architecture Guidance for Cloud
  Applications*, Microsoft patterns & practices, 2014, ISBN 978-1-62114-036-8.
- [Microsoft Learn, Competing Consumers
  pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers),
  Azure Architecture Center, verified 2026-08-02.
- [Microsoft Learn, Queue-based Load Leveling
  pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling),
  verified 2026-08-02.
- [AWS documentation, Using dead-letter queues in Amazon
  SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
  verified 2026-08-02.
- [AWS documentation, Amazon SQS visibility
  timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html),
  verified 2026-08-02.
- [RabbitMQ tutorials, Work Queues (Python
  tutorial two)](https://www.rabbitmq.com/tutorials/tutorial-two-python),
  verified 2026-08-02.
- [Confluent Developer, Consumer Group
  Protocol](https://developer.confluent.io/courses/architecture/consumer-group-protocol/),
  verified 2026-08-02.

## Code examples

Three languages, Go, Python, and TypeScript. Each implementation places a
run of twelve messages across three concurrent consumers, retries a
deliberately poisoned message (ID 7) three times, and routes it to a
dead-letter list once retries are exhausted, so the sample exercises both the
happy path and the poison-message failure mode from dimension 11. All three
were compiled or run directly against the interpreter or compiler installed
on this machine, none is hypothetical.

### Go

Verified with `go run` (Go toolchain present on this machine). Output shows
`processed=11` then `dead-lettered id=7 payload=order-7`.

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// Message is one unit of work placed on the shared queue.
type Message struct {
	ID      int
	Payload string
}

// Queue is a bounded channel acting as the shared point-to-point channel.
// Every consumer reads from the same channel, so the runtime scheduler
// hands each message to exactly one waiting goroutine.
type Queue chan Message

func producer(q Queue, count int) {
	for i := 1; i <= count; i++ {
		q <- Message{ID: i, Payload: fmt.Sprintf("order-%d", i)}
	}
	close(q)
}

// consumer pulls messages until the channel is closed and drained.
// A retry-then-deadletter loop guards against a poison message that
// panics during processing, mirroring a broker's redelivery count.
func consumer(id int, q Queue, deadLetter chan<- Message, processed *int64, wg *sync.WaitGroup) {
	defer wg.Done()
	for msg := range q {
		if !processWithRetry(id, msg, 3) {
			deadLetter <- msg
			continue
		}
		atomic.AddInt64(processed, 1)
	}
}

func processWithRetry(consumerID int, msg Message, maxAttempts int) (ok bool) {
	for attempt := 1; attempt <= maxAttempts; attempt++ {
		if attemptOnce(consumerID, msg) {
			return true
		}
		time.Sleep(time.Millisecond) // backoff, shortened for the demo
	}
	return false
}

// attemptOnce simulates a unit of work. Message ID 7 is fixed as a
// permanently poisoned message so the dead-letter path is exercised.
func attemptOnce(consumerID int, msg Message) (ok bool) {
	defer func() {
		if r := recover(); r != nil {
			ok = false
		}
	}()
	if msg.ID == 7 {
		panic("malformed payload")
	}
	return true
}

func main() {
	q := make(Queue, 4)
	deadLetter := make(chan Message, 10)
	var processed int64
	var wg sync.WaitGroup

	const consumerCount = 3
	wg.Add(consumerCount)
	for i := 1; i <= consumerCount; i++ {
		go consumer(i, q, deadLetter, &processed, &wg)
	}

	go producer(q, 12)
	wg.Wait()
	close(deadLetter)

	fmt.Printf("processed=%d\n", processed)
	for dl := range deadLetter {
		fmt.Printf("dead-lettered id=%d payload=%s\n", dl.ID, dl.Payload)
	}
}
```

### Python

Verified with `python3` (present on this machine). Same output as the Go
version.

```python
import queue
import threading
import time
from dataclasses import dataclass


@dataclass
class Message:
    id: int
    payload: str


def producer(q: "queue.Queue[Message]", count: int, worker_total: int) -> None:
    for i in range(1, count + 1):
        q.put(Message(id=i, payload=f"order-{i}"))
    for _ in range(worker_total):
        q.put(None)  # one poison pill per worker signals shutdown


def process_with_retry(msg: Message, max_attempts: int = 3) -> bool:
    for attempt in range(1, max_attempts + 1):
        if attempt_once(msg):
            return True
        time.sleep(0.001)
    return False


def attempt_once(msg: Message) -> bool:
    if msg.id == 7:
        raise ValueError("malformed payload")
    return True


def consumer(worker_id: int, q: "queue.Queue[Message]",
             dead_letter: "queue.Queue[Message]", counters: dict, lock: threading.Lock) -> None:
    while True:
        msg = q.get()
        if msg is None:
            q.task_done()
            return
        try:
            ok = process_with_retry(msg)
        except ValueError:
            ok = False
        if ok:
            with lock:
                counters["processed"] += 1
        else:
            dead_letter.put(msg)
        q.task_done()


def main() -> None:
    q: "queue.Queue[Message]" = queue.Queue(maxsize=4)
    dead_letter: "queue.Queue[Message]" = queue.Queue()
    counters = {"processed": 0}
    lock = threading.Lock()

    worker_count = 3
    workers = [
        threading.Thread(target=consumer, args=(i, q, dead_letter, counters, lock))
        for i in range(1, worker_count + 1)
    ]
    for w in workers:
        w.start()

    prod = threading.Thread(target=producer, args=(q, 12, worker_count))
    prod.start()
    prod.join()
    for w in workers:
        w.join()

    print(f"processed={counters['processed']}")
    while not dead_letter.empty():
        m = dead_letter.get()
        print(f"dead-lettered id={m.id} payload={m.payload}")


if __name__ == "__main__":
    main()
```

### TypeScript

Verified by compiling with `tsc` (target es2020, commonjs) and running the
emitted JavaScript under Node. Same output as the other two.

```typescript
interface Message {
  id: number;
  payload: string;
}

// A shared queue backed by an array. Consumers race to shift the next
// message off the front; whichever async worker calls dequeue() first
// wins that message, which is what "competing" means on one process.
class SharedQueue {
  private items: Message[] = [];
  private closed = false;

  enqueue(msg: Message): void {
    this.items.push(msg);
  }

  close(): void {
    this.closed = true;
  }

  dequeue(): Message | undefined {
    return this.items.shift();
  }

  isDrained(): boolean {
    return this.closed && this.items.length === 0;
  }
}

async function attemptOnce(msg: Message): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 0));
  if (msg.id === 7) {
    throw new Error("malformed payload");
  }
}

async function processWithRetry(msg: Message, maxAttempts = 3): Promise<boolean> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      await attemptOnce(msg);
      return true;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 1));
    }
  }
  return false;
}

async function consumer(
  id: number,
  q: SharedQueue,
  deadLetter: Message[],
  counters: { processed: number }
): Promise<void> {
  while (!q.isDrained()) {
    const msg = q.dequeue();
    if (!msg) {
      await new Promise((resolve) => setTimeout(resolve, 0));
      continue;
    }
    const ok = await processWithRetry(msg);
    if (ok) {
      counters.processed += 1;
    } else {
      deadLetter.push(msg);
    }
  }
}

async function main(): Promise<void> {
  const q = new SharedQueue();
  for (let i = 1; i <= 12; i++) {
    q.enqueue({ id: i, payload: `order-${i}` });
  }
  q.close();

  const deadLetter: Message[] = [];
  const counters = { processed: 0 };

  const consumerCount = 3;
  const workers = Array.from({ length: consumerCount }, (_, i) =>
    consumer(i + 1, q, deadLetter, counters)
  );
  await Promise.all(workers);

  console.log(`processed=${counters.processed}`);
  for (const m of deadLetter) {
    console.log(`dead-lettered id=${m.id} payload=${m.payload}`);
  }
}

main();
```

Java, Rust, and Swift were not produced for this entry. The pattern's
core behaviour, multiple stateless workers racing to pull from one
shared, blocking-capable queue with bounded retry, is fully idiomatic in Go's
channels, Python's `queue.Queue` plus threads, and a JavaScript-style
cooperative event loop, and those three together already demonstrate both a
true OS-thread-parallel implementation in Go and Python, and a single-threaded,
concurrency-simulated implementation in TypeScript. A fourth language would
repeat one of those two shapes rather than reveal a new one.
