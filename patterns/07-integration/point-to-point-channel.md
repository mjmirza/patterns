---
name: Point-to-Point Channel
slug: point-to-point-channel
family: 07-integration
category: Messaging Channels
aliases: [PTP Channel, Queue Channel, Point-to-Point Messaging Domain]
first_described: "Hohpe and Woolf 2003"
maturity: canonical
related: [publish-subscribe-channel, competing-consumers, message-queue, dead-letter-channel, guaranteed-delivery, message-dispatcher, selective-consumer, request-reply, correlation-identifier]
incompatible_with: []
verified: 2026-08-02
---

# Point-to-Point Channel

## 1. Name, aliases, and lineage

The canonical name is Point-to-Point Channel. It is documented as one of the
Message Channel patterns in Gregor Hohpe and Bobby Woolf, *Enterprise
Integration Patterns. Designing, Building, and Deploying Messaging Solutions*,
Addison-Wesley, 2003, in the Messaging Channels chapter. The book states the
intent as sending the message on a Point-to-Point Channel so that only one
receiver will receive a particular message
(https://www.enterpriseintegrationpatterns.com/patterns/messaging/PointToPointChannel.html,
verified 2026-08-02).

The pattern is older than the book's naming of it. The Java Message Service
specification, which predates the EIP book by several years, already called the
same idea the "point-to-point (PTP) messaging domain" and built it around a
first-class `Queue` destination type, distinct from the `Topic` destination
used for publish-subscribe. The current successor specification, Jakarta
Messaging 3.1, still uses this exact vocabulary. It defines PTP messaging as
allowing "a client to send a message to another client via an intermediate
abstraction called a queue," and states that "the client that receives the
message extracts it from that queue"
(https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1,
verified 2026-08-02). This is why the pattern is interchangeably called a
Queue Channel in messaging-vendor documentation and a Point-to-Point Channel in
integration-pattern literature. They name the same structural idea from two
different angles, JMS names it by the destination type, Hohpe and Woolf name it
by the delivery guarantee that destination type provides.

Hohpe and Woolf explicitly frame the pattern as the answer to a question posed
one level up, in the general Message Channel pattern. A channel connects a
sender and a receiver, and more than one receiver might be listening on it, so
the open question is how the sender can guarantee that a single logical unit
of work, a single command or a single document, is not picked up and
processed twice. Point-to-Point Channel is their answer for the case where
"exactly one" is the requirement. Publish-Subscribe Channel, described
immediately alongside it in the same chapter, is their answer for the case
where "every subscriber" is the requirement. Reading one without the other is
reading half the picture, because the pattern's entire reason for existing is
the contrast between them.

## 2. Problem and context

A system decouples a producer of work from a consumer of work using
asynchronous messaging instead of a direct call, for the usual reasons. The
producer should not block waiting for the consumer, the consumer should be
able to scale independently, and a spike in production should not overload the
consumer if a buffer sits between them.

The moment more than one consumer process exists, a new problem appears that a
synchronous call never had. A synchronous call has an implicit one-to-one
relationship built into the call stack itself, the caller invokes a function,
one function body runs, one caller gets the return value back. A message
channel with two or more listeners has no such implicit guarantee. If the
channel behaves like a broadcast, both listeners see the message and both act
on it. For a log line or a metrics event that duplication is harmless or even
desired. For a payment capture, an inventory decrement, or an order placement,
the same duplication corrupts the system, the customer is charged twice, the
stock count goes negative, two identical shipments are dispatched.

The context in which this problem specifically arises is a work-distribution
scenario, not an event-notification scenario. The producer has emitted a
single, atomic unit of work, and it needs exactly one worker to perform it,
and it does not particularly care which worker, only that precisely one does.
This is the RPC-over-messaging and command-dispatch case, and the EIP book
names it directly, asking "how can the caller be sure that exactly one
receiver will receive the document or perform the call"
(https://www.enterpriseintegrationpatterns.com/patterns/messaging/PointToPointChannel.html,
verified 2026-08-02). A second, closely related context is horizontal scale-out
of a single logical consumer. Many worker processes are started for
throughput, but the unit of work must still land on exactly one of them, never
on all of them at once. Both contexts share the same shape, many possible
consumers, exactly one actual consumer per message.

## 3. Forces

**Delivery exclusivity versus throughput.** Guaranteeing that only one
consumer processes a message means the channel must coordinate consumers so
they never both grab the same item. That coordination, whatever its
implementation, costs something, a lock, a lease, a broker-side dequeue
operation. A design that skipped the coordination could in principle deliver
faster, but it would also deliver twice, which defeats the point.

**Scalability of consumers versus ordering.** A queue that lets any of N
worker processes pull the next message gives near-linear throughput scaling as
workers are added. That same latitude is what breaks strict message ordering,
because two workers pulling concurrently can finish out of the order they
received. A system that needs both exclusive-per-message delivery and strict
ordering, such as a per-account event stream, has to give something up, and
that trade-off is exactly why partitioned or FIFO variants of Point-to-Point
Channel exist as a separate, stricter sub-case.

**Coupling of sender and receiver count.** Point-to-Point Channel decouples
the sender from any specific receiver instance, the sender does not address a
process, it addresses a queue, but it deliberately does not decouple the
sender from the receiver's count expectation. The sender is implicitly
promising "exactly one of you will act on this," and every receiver on the
channel is implicitly promising "if I take it, I own it." Changing that
count contract later, from one consumer to many independent consumers each
needing their own copy, is not a configuration change, it is a change of
pattern, to Publish-Subscribe Channel.

**Operability versus simplicity.** A point-to-point queue that offers only
first-in-first-out delivery with no visibility into what happens after a
worker takes a message is simple to reason about but operationally blind, a
crashed worker silently drops the work it had claimed. Real implementations
add acknowledgement, redelivery, and a dead-letter path to make failure
observable and recoverable, and each of those additions is more moving parts
that must themselves be monitored. The pattern favours reliability over
minimalism once it leaves the whiteboard.

**Consistency across a network partition.** Because the channel typically
lives in a broker process separate from both sender and receiver, the queue's
state, whether a given message has been delivered and whether it has been
acknowledged, can diverge from the true state of the world during a network
partition. Most production implementations resolve this by favouring
at-least-once delivery over exactly-once, accepting that a receiver might see
a message a second time after a partition heals, rather than risking that it
sees it zero times. This is a deliberate, judgement-based trade, correctness
under partition weighed against the operational cost of building true
exactly-once semantics, and the industry consensus, reflected for example in
Amazon SQS standard queues defaulting to at-least-once delivery rather than
exactly-once
(https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-standard-queues.html,
verified 2026-08-02), is that at-least-once plus idempotent consumers is
cheaper to operate correctly than distributed exactly-once.

## 4. Applicability and non-applicability

Reach for a Point-to-Point Channel in these situations.

- A single unit of work, a command, a job, an order, a payment capture, must
  be acted on by exactly one consumer, never zero and never more than one.
- Multiple consumer processes exist for throughput or availability, and any
  one of them is an acceptable handler for any given message, so the choice of
  which one handles which message can be left to whichever worker is free.
- The sender needs the ability to add or remove consumer instances without
  changing anything about how it sends, because the channel, not the sender,
  is responsible for distributing work across whatever consumers currently
  exist.
- Buffering between producer and consumer is wanted, so a burst of incoming
  work does not have to be handled synchronously and can instead queue up
  until a worker is free.
- The unit of work benefits from at-least-once delivery with retry, meaning
  the consumer's processing can be made idempotent or the work is naturally
  safe to repeat.

Do NOT reach for a Point-to-Point Channel in these situations.

- Every interested party needs its own independent copy of the message. That
  is Publish-Subscribe Channel's job, not this pattern's. Forcing fan-out
  through a point-to-point queue means either duplicating the message onto N
  separate queues by hand, which is reinventing Publish-Subscribe Channel, or
  accepting that only one of N interested consumers will ever see any given
  message, which silently breaks the other N minus one.
- Strict, global ordering across the entire channel must be preserved while
  also scaling out to many concurrent consumers. A plain point-to-point queue
  with multiple competing consumers gives up ordering the moment two workers
  process concurrently. If ordering matters more than parallel throughput, a
  single consumer, or a partitioned queue keyed so that all messages for one
  ordering key land on one partition and hence one consumer, is required
  instead of a naive multi-consumer queue.
- The interaction is genuinely synchronous, a request that must complete
  before the caller can do anything useful with the result, and there is no
  benefit to buffering or decoupling. A direct call, or Request-Reply layered
  on top of two point-to-point channels, fits that case better than treating
  every RPC as fire-and-forget messaging.
- The system cannot tolerate any duplicate processing and cannot make the
  consumer idempotent. Because most real point-to-point implementations are
  at-least-once rather than exactly-once, a consumer that is not idempotent
  and a business rule that forbids any duplicate, such as an unrepeatable
  one-time discount code redemption, needs an additional guard, such as
  Idempotent Receiver keyed on a deduplication identifier, layered on top of
  this pattern, not this pattern alone.
- Extremely low, single-digit-millisecond, latency is required end to end and
  a broker hop is unacceptable. A point-to-point queue introduces at least one
  network round trip to the broker and one from the broker to the consumer,
  while a direct synchronous call avoids both.

## 5. Structure

- **Sender.** The application or component that produces a unit of work and
  places it on the channel. The sender addresses the channel itself, never a
  specific receiver process, and has no visibility into which receiver
  instance will ultimately consume the message.
- **Point-to-Point Channel, the queue.** The channel abstraction, most often
  realised as a broker-managed queue destination. It buffers messages that
  have been sent but not yet consumed, and it enforces the exclusivity
  guarantee. Once one receiver has begun consuming a given message, no other
  receiver on the same channel can also consume that same message.
- **Receiver.** One of potentially several processes or threads listening on
  the same channel. Each receiver competes with every other receiver on the
  channel for the next available message. A receiver that successfully claims
  a message becomes the sole owner of processing it.
- **Delivery coordination mechanism, inside the channel.** The internal logic
  that decides which waiting receiver gets the next message and prevents a
  second receiver from also getting it. In a JMS-style queue this is the
  broker's dequeue-and-lock operation. In a lease-based queue like Amazon SQS
  it is the visibility timeout mechanism, which hides a message from other
  receivers for a configurable period after it has been handed to one
  receiver, and only reveals it again if that receiver fails to acknowledge
  completion in time
  (https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-standard-queues.html,
  verified 2026-08-02).
- **Acknowledgement.** The signal, explicit or implicit depending on the
  implementation, that tells the channel a receiver has finished with a
  message so it can be permanently removed. Without acknowledgement the
  channel cannot distinguish "still being processed" from "lost, redeliver
  it," which is why almost every production implementation of this pattern
  includes some acknowledgement step even though the abstract EIP definition
  does not require one explicitly.

## 6. ASCII structure diagram

```
                          Point-to-Point Channel
                       (single logical queue, FIFO buffer)
   +---------+        +----------------------------------+
   |         |        |  [msg1][msg2][msg3][msg4]...      |
   | Sender  |------->|                                    |
   |         |  send  |  Delivery coordination:            |
   +---------+        |  hands each message to exactly     |
                       |  one waiting receiver, hidden      |
                       |  from the rest until ack/timeout   |
                       +----------------------------------+
                              |            |            |
                        claims msg1   claims msg2   waiting, idle
                              v            v            v
                       +-----------+ +-----------+ +-----------+
                       | Receiver A| | Receiver B| | Receiver C|
                       +-----------+ +-----------+ +-----------+
                       msg3, msg4 remain queued for the next
                       receiver that becomes free
```

## 7. Dynamics

```
Sender                Channel (Queue)          Receiver A        Receiver B
  |                          |                       |                 |
  |--send(msg1)------------>|                        |                 |
  |                          |--offer msg1----------->|                 |
  |                          |   (locked/invisible    |                 |
  |                          |    to Receiver B)       |                 |
  |--send(msg2)------------>|                        |                 |
  |                          |----------------------- offer msg2 ------>|
  |                          |                       |                 |
  |                          |                  process msg1      process msg2
  |                          |                       |                 |
  |                          |<--ack(msg1)-----------|                 |
  |                          |  (msg1 permanently                      |
  |                          |   removed)                              |
  |                          |<---------------------- ack(msg2) -------|
  |                          |                       |                 |
  |                    [failure case]                |                 |
  |--send(msg3)------------>|                        |                 |
  |                          |--offer msg3----------->|                 |
  |                          |                  Receiver A crashes,
  |                          |                  no ack arrives
  |                          |  visibility timeout expires
  |                          |----------------------- offer msg3 ------>|
  |                          |                       |            process msg3
  |                          |<---------------------- ack(msg3) -------|
```

The failure case at the bottom is the operationally important half of the
diagram. A well-implemented Point-to-Point Channel does not lose a message
merely because the receiver that claimed it died mid-processing. It eventually
re-offers the message to a still-living receiver, which is precisely the
mechanism that yields at-least-once delivery instead of at-most-once.

## 8. Implementation variants

- **Broker-managed queue, lock-on-receive.** The classic JMS `Queue`
  destination. A receiver's `receive()` call, or an asynchronous
  `MessageListener` callback, removes the message from the broker's storage as
  part of the receive operation, inside a transaction if transacted sessions
  are used, so a failed consumer that rolls back its transaction puts the
  message back for redelivery
  (https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1,
  verified 2026-08-02). This is the strongest-consistency variant, because the
  broker itself participates in the transaction boundary.
- **Lease-based queue, visibility timeout.** Amazon SQS is the prototypical
  example. A `ReceiveMessage` call does not delete the message, it makes the
  message invisible to other consumers for a configurable visibility timeout,
  and the consumer must explicitly call `DeleteMessage` before that timeout
  expires or the message becomes visible again for another consumer to claim
  (https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-standard-queues.html,
  verified 2026-08-02). This variant tolerates a consumer that crashes without
  ever contacting the broker again, at the cost of a window, the timeout
  duration, during which a slow but alive consumer can be mistaken for a dead
  one and have its work reassigned, producing a duplicate.
- **Database-backed queue table.** The channel is a relational table with a
  status column. A receiver claims a row with `SELECT ... FOR UPDATE SKIP
  LOCKED` (PostgreSQL) or an equivalent row-locking read, processes it, and
  updates its status. This variant is common when a team wants transactional
  consistency between the queue state and other application data in the same
  database, at the cost of the queue competing for the same connection pool
  and storage engine as the rest of the application.
- **Redis list or stream as a queue.** `BLPOP`/`BRPOP` on a Redis list gives a
  simple point-to-point queue where each popped element goes to exactly one
  blocking client. Redis Streams with consumer groups (`XREADGROUP`) gives a
  richer variant with per-consumer pending-entry lists and explicit
  acknowledgement (`XACK`), closer in shape to the JMS model than the plain
  list variant.
- **Partitioned point-to-point, key-ordered.** Apache Kafka is not, by
  default, a point-to-point channel in the JMS sense. A topic can have many
  independent consumer groups, each seeing every message, which is
  publish-subscribe behaviour across groups. Within a single consumer group,
  however, Kafka behaves as a point-to-point channel, each partition is
  consumed by exactly one member of the group at a time, giving exclusive,
  ordered delivery per partition key while still allowing horizontal scale-out
  by adding partitions and consumers. This is the variant to reach for when
  both exclusivity and per-key ordering are required simultaneously.
- **Language-native channel, single consumer group.** Go's unbuffered or
  buffered `chan T` consumed by a fixed pool of goroutines is a point-to-point
  channel inside a single process, a value sent on the channel is received by
  exactly one goroutine among however many are calling `<-ch`. This is the
  in-process analogue of the distributed pattern and shares its core
  guarantee, exactly one consumer per item, without any broker.

## 9. Known production uses

- **Jakarta Messaging (formerly Java Message Service), the `Queue`
  destination type.** The specification defines the point-to-point domain as
  a first-class concept distinct from the publish-subscribe `Topic` domain,
  and every JMS-compliant broker, including Apache ActiveMQ, IBM MQ, and
  Solace, implements this exact distinction
  (https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1,
  verified 2026-08-02).
- **Amazon Simple Queue Service (SQS).** AWS's managed queueing service
  implements point-to-point delivery through the visibility timeout mechanism.
  A message received by one consumer is hidden from all others until it is
  deleted or the timeout expires, which is a lease-based realisation of
  exactly the exclusivity guarantee Hohpe and Woolf describe
  (https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-standard-queues.html,
  verified 2026-08-02).
- **RabbitMQ queues (AMQP 0-9-1).** RabbitMQ's core queue type delivers each
  message to exactly one of the consumers subscribed to that queue when
  multiple consumers are attached, the competing consumers configuration,
  which is RabbitMQ's realisation of the same point-to-point semantics. A
  message is only fanned out to multiple independent queues if the producer
  explicitly routes it through an exchange configured to do so, which is the
  boundary between RabbitMQ's point-to-point queue behaviour and its
  publish-subscribe exchange behaviour.
- **Apache Kafka consumer groups.** Within one consumer group, each partition
  of a topic is assigned to exactly one consumer instance in that group at a
  time, so a message on that partition is processed by exactly one member of
  the group, the partitioned point-to-point variant described in dimension 8.
- **Sidekiq (Ruby background jobs) and Celery (Python distributed task
  queue).** Both are worker-pool systems built directly on a point-to-point
  queue, Redis for Sidekiq by default, a broker such as Redis or RabbitMQ for
  Celery. A job enqueued once is picked up and executed by exactly one worker
  process among the running pool, which is the textbook work-distribution use
  case the pattern exists for.

## 10. Consequences

Positive.

- Exactly one consumer acts on each unit of work, which is precisely the
  guarantee a command, a job, or a financial operation needs, without the
  sender or the consumer having to implement their own mutual-exclusion
  logic.
- Consumers can be added or removed purely for capacity reasons, with zero
  change to the sender and zero coordination required between consumer
  instances, because the channel itself arbitrates which consumer gets which
  message.
- The sender and receiver are decoupled in time as well as in address. The
  sender does not need any receiver to be running at the moment it sends, and
  a receiver does not need the sender to still be running when it consumes.
- Failure isolation improves. A crashed receiver's in-flight message is, in
  every production-grade implementation, eventually redelivered rather than
  silently lost, so a single consumer crash does not lose work, only delays
  it.

Negative.

- Ordering is not guaranteed once more than one consumer is active, because
  two consumers processing concurrently can finish, and thus have their
  side effects observed, out of send order. A system that needs exclusivity
  and ordering together must adopt a stricter variant, such as a partitioned
  point-to-point channel, and cannot get both from a naive multi-consumer
  queue.
- Most implementations are at-least-once, not exactly-once, so the consumer
  must be written to be safely idempotent, or a separate deduplication
  mechanism must be layered on top, or the system will occasionally process
  the same unit of work twice.
- The channel becomes a single point of coordination and, depending on the
  implementation, a single point of failure or a capacity bottleneck. A
  broker outage or a maxed-out queue depth stalls every sender and every
  receiver that depends on it.
- Debugging is harder than a direct call, because the causal chain from
  "sender sent this" to "receiver B happened to process it" is no longer
  visible in a stack trace, and reconstructing it after the fact requires
  correlation identifiers and centralised tracing that a synchronous call
  gets for free.

## 11. Failure modes and misuse

**Symptom.** The same order is fulfilled twice.
**Cause.** The consumer processed the message and performed its side effect,
charging a card or decrementing stock, but crashed, or the network dropped,
before the acknowledgement reached the channel, so the channel treated the
message as unconsumed and redelivered it to another consumer, which then
performed the side effect a second time.
**Fix.** Make the consumer's processing idempotent, typically by recording a
processed-message identifier in the same transaction as the side effect and
checking that identifier before acting, or by using an operation that is
naturally idempotent, such as an upsert keyed on order ID rather than a plain
insert.

**Symptom.** A small number of messages are never processed and quietly pile
up, invisible in normal monitoring.
**Cause.** A message that repeatedly fails processing, because the payload is
malformed or triggers a bug, is redelivered on every visibility-timeout
expiry or every failed-transaction rollback, forever, without ever being
removed from the healthy retry path, a pattern usually called a poison
message.
**Fix.** Configure a maximum-redelivery count and a Dead Letter Channel that
receives a message once it has exceeded that count, so the poison message is
quarantined for inspection instead of endlessly cycling and consuming worker
capacity.

**Symptom.** Throughput does not improve, or gets worse, after adding more
consumer processes.
**Cause.** The receivers are contending for a resource outside the channel
itself, most often a shared database connection pool or a shared downstream
API rate limit, so adding consumers increases contention on that resource
rather than increasing useful parallelism. Alternatively the channel's own
locking mechanism, row-level locks in a database-backed queue for instance,
becomes the bottleneck under high consumer concurrency.
**Fix.** Profile the actual bottleneck before adding consumers. Scale the
downstream resource or move to a partitioned channel design that spreads lock
contention across partitions instead of a single shared queue.

**Symptom.** Messages are processed in a wildly different order than they
were sent, and a downstream process that assumed FIFO ordering produces wrong
results.
**Cause.** More than one consumer is active on the channel, so message N+1 can
finish before message N if consumer A is momentarily slower than consumer B,
and the code assumed a point-to-point queue with multiple consumers preserves
global order, which it does not.
**Fix.** Either restrict the channel to a single consumer, accepting the
throughput cost, or move to a partitioned point-to-point variant keyed so that
all messages requiring relative order share a partition and therefore a
consumer, or redesign the downstream logic to be order-independent using
sequence numbers or version checks instead of relying on arrival order.

**Symptom.** A message that a receiver claimed appears to vanish, and there is
no trace of it ever being processed.
**Cause.** A consumer acknowledged the message, deleted it or committed the
transaction, before it actually finished the side effect, often because a
framework's default is to auto-acknowledge on receipt rather than on
completion, and the process crashed between the premature acknowledgement and
the real work finishing.
**Fix.** Acknowledge only after the side effect is durably committed, never on
receipt, which usually means switching from an auto-acknowledge mode to an
explicit, client-controlled acknowledge mode.

**Misuse.** Using a point-to-point channel to fan a message out to several
independent subscribers, by having several consumer processes read from the
same queue and expecting each to see every message.
**Symptom.** Each subscriber only sees roughly one out of every N messages,
seemingly at random, because the channel is doing exactly what it is designed
to do, giving each message to exactly one of the competing receivers.
**Fix.** This is not a bug in the queue, it is the wrong pattern. Switch to
Publish-Subscribe Channel, which is designed to give every subscriber its own
independent copy.

## 12. Trade-off matrix

| Force | Point-to-Point Channel | Publish-Subscribe Channel | Direct synchronous call |
|---|---|---|---|
| Receivers per message | Exactly one consumer per message | Every subscriber gets a copy | Exactly one callee, chosen at compile or config time |
| Sender/receiver decoupling in time | High, receiver need not be running when sent | High, same as point-to-point | None, both must be up simultaneously |
| Horizontal scale-out of processing | Native, add more competing consumers | Requires per-subscriber scaling, not shared work | Requires a load balancer in front of the callee |
| Ordering under concurrency | Not guaranteed once multiple consumers are active | Not guaranteed across subscribers, though each subscriber's own stream can be ordered | Guaranteed by the caller's own sequencing |
| Failure visibility to the caller | Indirect, caller does not learn of failure without a reply channel | Indirect, same | Immediate, an exception or error return |
| Fit for command dispatch, do this once | Very good, this is the core use case | Poor, every subscriber would perform the command | Very good, but blocks the caller |
| Fit for event notification, tell everyone interested | Poor, only one interested party would see it | Very good, this is the core use case | Poor, requires the caller to know and call every interested party |

## 13. Related and incompatible patterns

**Publish-Subscribe Channel.** The direct sibling and the pattern most often
confused with this one. Both are Message Channel patterns solving the same
underlying question, how many receivers get each message, with opposite
answers, exactly one receiver here, every subscriber there. They are not
composable into one channel, a channel is one or the other. A system that
needs both behaviours for the same logical event stream typically implements
Point-to-Point Channel for the work-distribution consumers and layers a
separate Publish-Subscribe fan-out, often by having one point-to-point
consumer republish onto a topic, rather than trying to make one channel do
both jobs.

**Competing Consumers.** This is the pattern name for the deployment shape
that Point-to-Point Channel enables, multiple consumer instances pulling from
the same queue to share the load. Point-to-Point Channel is the channel-level
guarantee, exclusivity per message, Competing Consumers is the receiver-side
pattern, a pool of interchangeable workers, that relies on that guarantee.
They are described together in Hohpe and Woolf's book because neither is very
useful without the other.

**Dead Letter Channel.** Composes on top of Point-to-Point Channel to handle
the poison-message failure mode described in dimension 11. A message that
exceeds its redelivery limit is moved from the primary point-to-point channel
to a separate dead-letter point-to-point channel for manual or automated
inspection, rather than being silently dropped or endlessly retried.

**Guaranteed Delivery.** A stronger requirement layered on top of Point-to-Point
Channel, not only should exactly one consumer eventually process the message,
the message should also survive a broker crash. This is typically achieved by
persisting the queue's contents to durable storage before acknowledging the
send, which is orthogonal to, and compatible with, every implementation
variant listed in dimension 8.

**Idempotent Receiver.** Compensates for the at-least-once delivery weakness
described in dimension 10. Point-to-Point Channel guarantees at most one
active consumer per message, not exactly-once processing. Idempotent Receiver
on the consumer side is what actually closes the gap when a message is
redelivered after a crash.

**Message Dispatcher.** A related but distinct pattern where a single
consumer thread reads from the channel and then dispatches the message to one
of several internal handler threads, in-process, rather than having several
independent receiver processes compete directly on the channel. This is
sometimes used when the broker connection itself should have a single
consumer for ordering or licensing reasons, and the fan-out to worker threads
happens after the message leaves the channel rather than as part of the
channel's own delivery.

**Correlation Identifier and Request-Reply.** These compose with Point-to-Point
Channel to build synchronous-feeling request/response semantics over two
one-way point-to-point channels, a request channel and a reply channel, with a
correlation ID tying a given reply back to the request that produced it. There
is no incompatibility here, Request-Reply is simply two Point-to-Point
Channels used together with a matching identifier.

There is no pattern in this catalog that is directly incompatible with Point-
to-Point Channel at the structural level. The closest thing to an
incompatibility is the misuse described in dimension 11, attempting to use it
for a fan-out requirement that only Publish-Subscribe Channel actually solves.

## 14. Refactoring path in and out

**Introducing the pattern into a synchronous system.** Start from a direct
call, `caller.doWork(request)`, that blocks until the callee finishes. First,
identify the unit of work that genuinely needs to happen exactly once but does
not need its result immediately, and extract it into its own function or
method with a clear input and no return value the caller waits on. Second,
introduce a queue, whichever variant fits the existing infrastructure, a
managed broker if one is already in the stack, a lightweight one such as Redis
if not. Third, change the caller to enqueue the request instead of calling the
function directly, and start a separate consumer process, or a small pool of
them, that dequeues and calls the original function body. Fourth, if the
caller genuinely needs the result back, add a reply channel and a correlation
identifier rather than reintroducing a blocking wait. This is the point at
which the refactor completes into a full Request-Reply built on two Point-to-
Point Channels. Verify at each step that exactly one worker processes each
enqueued item under load, not merely under a single-threaded local test, by
running the consumer pool with more than one instance and checking for
duplicate side effects before calling the migration done.

**Removing the pattern when it no longer earns its place.** The pattern stops
earning its place when the queue has effectively only ever had one consumer,
was never actually decoupling in time, the caller always waits synchronously
for a reply anyway, defeating the entire benefit, and the operational cost of
running and monitoring a broker is not buying anything the caller cannot get
from a direct call. To remove it, confirm there is truly one consumer instance
and it is always running whenever the sender runs, replace the
enqueue-and-poll-for-reply pattern with a direct function call or a
synchronous RPC call, and delete the queue infrastructure only after
confirming, via monitoring over a full traffic cycle, that nothing else has
quietly come to depend on the queue's buffering behaviour during traffic
spikes.

## 15. Testing and verification

What becomes easy to test because of this pattern, the sender and the
receiver can be tested in complete isolation from each other, because the only
contract between them is the shape of the message on the channel. A test for
the sender only needs to assert that the correct message was placed on the
channel, using an in-memory fake queue or a test double. A test for the
receiver only needs to place a message on that same fake queue and assert the
correct side effect happened.

What becomes harder, the end-to-end, exactly-once-under-concurrency guarantee
is the one property that a single-threaded unit test structurally cannot
observe, because the exclusivity claim only means anything when more than one
consumer is racing for the same message. Verifying it requires an integration
test that starts at least two real, or realistically simulated, consumer
instances against a real or embedded broker, sends N messages, and asserts
that exactly N side effects occurred with no message processed by more than
one consumer and no message dropped. Embedded broker libraries, an in-memory
ActiveMQ broker for JMS-based systems or the LocalStack SQS emulator for
AWS-based systems, are the usual way to run this kind of test in CI without a
real network dependency.

A second class of test specific to this pattern is a fault-injection test for
the failure-mode table in dimension 11, kill a consumer mid-processing, before
it acknowledges, and assert the message is eventually redelivered and
processed exactly once end to end, which exercises both the redelivery
mechanism and the consumer's idempotency guard in the same test.

Contract testing between sender and receiver, verifying that the message
schema the sender produces matches the schema the receiver expects, is also
disproportionately valuable here, because unlike a compile-time-checked direct
call, a schema mismatch across a point-to-point channel is only discovered at
runtime, often long after the sender's own deploy, when the receiver finally
consumes a message it cannot parse.

## 16. Observability signals

The single most important metric is queue depth, the count of messages sent
but not yet acknowledged, tracked over time. A queue depth that is flat near
zero under normal load and climbs steadily is the earliest and clearest signal
that consumers are falling behind producers, before any user-visible symptom
appears.

Age of the oldest unacknowledged message, sometimes exposed as approximate age
of oldest message in managed queue services, is a more useful companion
metric than raw depth alone, because it directly measures how long a sender's
request has been waiting, which is what actually matters to end-to-end
latency.

Redelivery count per message, or its aggregate, the rate of messages being
redelivered rather than delivered for the first time, is the direct signal
for the poison-message and premature-crash failure modes in dimension 11. A
healthy channel shows a redelivery rate close to zero. A rising redelivery
rate means either consumers are crashing or a subset of messages cannot be
processed.

Dead-letter queue depth, where one exists, should be treated as an alerting
metric with a low threshold, ideally alerting on any nonzero value, because
every message that lands there represents work that is genuinely not
happening without human intervention.

Consumer lag or consumer count relative to queue depth exposes the capacity
side of the picture. A channel can look healthy on depth alone while actually
being one consumer crash away from an unbounded backlog if the active
consumer count has silently dropped to one.

A healthy dashboard for this pattern shows near-zero steady-state depth,
near-zero oldest-message age, a redelivery rate near zero, an empty dead-letter
queue, and a consumer count matching the deployed and expected worker fleet
size. A failing instance typically shows one of two shapes, either a slowly
and steadily climbing depth with a stable low redelivery rate, a throughput
problem where consumers cannot keep up, or a flat, low depth with a rising
redelivery rate and a growing dead-letter queue, a correctness problem where
the messages being sent are triggering consumer failures.

## 17. Security and privacy implications

Because a Point-to-Point Channel is very often implemented by a broker process
that sits outside both the sender's and the receiver's own trust boundary, the
message payload traverses and rests, however briefly, inside a third-party
service's storage. Any personal or regulated data carried in the payload
inherits whatever access-control and encryption-at-rest guarantees that broker
provides, or fails to provide, which is a separate concern from the access
control the sending and receiving applications themselves enforce. A system
handling regulated data over a managed queue service should confirm the
provider's at-rest encryption and access-policy model rather than assuming the
queue is as private as an in-process function call.

Authorization at the channel level matters independently of authorization
inside the message handler. If any process that can reach the queue endpoint
can enqueue a message, and the receiver trusts every message it dequeues as
already-authorized, the queue itself becomes the enforcement gap, an attacker
who can reach the broker network can inject a message that the receiver will
process with full trust. Point-to-point queues typically need their own
producer-side authorization, deciding who is allowed to send to this queue,
separate from whatever authorization gated the original request that led to
the send.

The at-least-once delivery characteristic discussed throughout this entry has
a security-adjacent consequence. A receiver that is not idempotent is not only
a correctness bug, it is also a resource-exhaustion or double-spend risk if an
attacker can trigger redelivery deliberately, for example by intentionally
delaying acknowledgement past the visibility timeout to force a message to be
reprocessed. Idempotency, covered as a correctness concern in dimensions 10
and 11, is therefore also a defensive control against this class of abuse.

Message payloads that include a correlation identifier or other tracing data
for the Request-Reply pattern described in dimension 13 should avoid encoding
sensitive information directly into that identifier, since correlation IDs are
frequently logged in plaintext across multiple systems, sender, broker, and
receiver, for debugging purposes, and are therefore effectively less protected
than the payload body itself.

## 18. References

- Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, Messaging
  Channels chapter, Point-to-Point Channel pattern,
  https://www.enterpriseintegrationpatterns.com/patterns/messaging/PointToPointChannel.html,
  verified 2026-08-02.
- Eclipse Foundation and Jakarta EE, *Jakarta Messaging Specification, version
  3.1*, point-to-point messaging domain and `Queue` destination semantics,
  https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1,
  verified 2026-08-02.
- Amazon Web Services, *Amazon Simple Queue Service Developer Guide*,
  standard queues, at-least-once delivery, and visibility timeout,
  https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-standard-queues.html,
  verified 2026-08-02.

## Code

### TypeScript, an in-memory point-to-point queue with competing consumers

```typescript
type Handler<T> = (message: T) => Promise<void>;

class PointToPointChannel<T> {
  private queue: T[] = [];
  private workers: Handler<T>[] = [];
  private nextWorker = 0;

  registerConsumer(handler: Handler<T>): void {
    this.workers.push(handler);
  }

  async send(message: T): Promise<void> {
    if (this.workers.length === 0) {
      this.queue.push(message);
      return;
    }
    const worker = this.workers[this.nextWorker % this.workers.length];
    this.nextWorker += 1;
    await worker(message);
  }
}

async function demo(): Promise<void> {
  const channel = new PointToPointChannel<string>();
  const processed: string[] = [];

  channel.registerConsumer(async (msg) => {
    processed.push(`workerA:${msg}`);
  });
  channel.registerConsumer(async (msg) => {
    processed.push(`workerB:${msg}`);
  });

  await channel.send("order-1");
  await channel.send("order-2");
  await channel.send("order-3");

  if (processed.length !== 3) {
    throw new Error("expected exactly one consumer per message");
  }
  console.log(processed.join(", "));
}

demo();
```

### Python, a queue-backed point-to-point channel with a worker pool

```python
import queue
import threading
from dataclasses import dataclass


@dataclass
class WorkItem:
    order_id: str


class PointToPointChannel:
    def __init__(self) -> None:
        self._queue: "queue.Queue[WorkItem]" = queue.Queue()

    def send(self, item: WorkItem) -> None:
        self._queue.put(item)

    def receive(self, timeout: float = 1.0) -> WorkItem:
        return self._queue.get(timeout=timeout)

    def acknowledge(self) -> None:
        self._queue.task_done()


def worker(channel: PointToPointChannel, name: str, results: list, lock: threading.Lock) -> None:
    while True:
        try:
            item = channel.receive(timeout=0.5)
        except queue.Empty:
            return
        with lock:
            results.append(f"{name}:{item.order_id}")
        channel.acknowledge()


def main() -> None:
    channel = PointToPointChannel()
    for order_id in ["A1", "A2", "A3", "A4"]:
        channel.send(WorkItem(order_id))

    results: list = []
    lock = threading.Lock()
    threads = [
        threading.Thread(target=worker, args=(channel, f"worker{i}", results, lock))
        for i in range(2)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    processed_ids = {r.split(":")[1] for r in results}
    assert len(results) == 4, "each message must be processed exactly once"
    assert processed_ids == {"A1", "A2", "A3", "A4"}
    print(sorted(results))


if __name__ == "__main__":
    main()
```

### Go, a point-to-point channel using competing goroutine consumers

```go
package main

import (
	"fmt"
	"sync"
)

type WorkItem struct {
	OrderID string
}

func main() {
	channel := make(chan WorkItem, 10)
	var mu sync.Mutex
	var processed []string
	var wg sync.WaitGroup

	worker := func(name string) {
		defer wg.Done()
		for item := range channel {
			mu.Lock()
			processed = append(processed, name+":"+item.OrderID)
			mu.Unlock()
		}
	}

	wg.Add(2)
	go worker("workerA")
	go worker("workerB")

	orders := []string{"O1", "O2", "O3", "O4", "O5"}
	for _, id := range orders {
		channel <- WorkItem{OrderID: id}
	}
	close(channel)
	wg.Wait()

	if len(processed) != len(orders) {
		panic("expected exactly one consumer per message")
	}
	fmt.Println(processed)
}
```

Java and Rust samples were not written for this entry. Java is the most
idiomatic language for this pattern via JMS `Queue`, but a runnable JMS sample
requires a running broker or an embedded broker dependency that is not
available in this environment. A hand-written thread-pool `BlockingQueue`
sample would not demonstrate anything the Go and Python samples above do not
already show more clearly. Rust was skipped for the same reason of marginal
added value at the cost of environment setup, given `rustc` alone, without
`crossbeam` or `tokio`, does not add anything to the demonstration beyond what
`std::sync::mpsc` already covers identically to the Go channel example.

## Verification of code samples

The TypeScript sample was compiled with `npx tsc --strict` targeting ES2020
and executed with `node`. The Python sample was executed with `python3` and
its two assertions passed. The Go sample was built and executed with `go run`
and its panic condition was confirmed not to trigger on a normal run.
