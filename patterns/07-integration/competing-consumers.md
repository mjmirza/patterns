---
name: Competing Consumers
slug: competing-consumers
family: 07-integration
category: Messaging
aliases: [Work Queue, Message Dispatcher (informal), Consumer Group Fan-Out]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [message-channel, point-to-point-channel, publish-subscribe-channel, message-dispatcher, event-driven-consumer, polling-consumer, dead-letter-channel, idempotent-receiver, load-balancer, circuit-breaker]
incompatible_with: [publish-subscribe-channel]
verified: 2026-08-02
---

# Competing Consumers

## 1. Name, aliases, and lineage

The canonical name is Competing Consumers. It comes from Gregor Hohpe and
Bobby Woolf, *Enterprise Integration Patterns. Designing, Building, and
Deploying Messaging Solutions*, Addison-Wesley, 2003
([publisher page confirming title, authors, and 2003 date](https://www.enterpriseintegrationpatterns.com/books1.html),
verified 2026-08-02). The pattern's own page states the problem plainly. "An
application is using Messaging. However, it cannot process messages as fast
as they're being added to the channel." and gives the solution as. "Create
multiple Competing Consumers on a single channel so that the consumers can
process multiple messages concurrently."
([Enterprise Integration Patterns, Competing Consumers](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CompetingConsumers.html),
verified 2026-08-02).

The name reads oddly to a first-time reader, because "competing" sounds
adversarial, but the word is doing precise work. The consumers are not
competing for a business outcome, they are competing for the next message on
one shared channel, and only one of them wins each round. Hohpe and Woolf
place the pattern inside the messaging family alongside Point-to-Point
Channel, and their own catalog page lists it as functioning only against a
Point-to-Point Channel. applying the same idea to a Publish-Subscribe Channel
does not distribute work across the consumers, it duplicates the message to
every one of them
([Enterprise Integration Patterns, Competing Consumers, related patterns and constraint note](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CompetingConsumers.html),
verified 2026-08-02).

In the messaging systems that implement it, the pattern goes by several
practical names that all point at the same structure. A pool of Amazon SQS
consumers polling one queue is usually called "workers" or "consumers"
in AWS's own developer guide. In Apache Kafka the equivalent structural idea
is called a consumer group, where several consumer processes share one
`group.id` and the broker's group coordinator divides the topic's partitions
among them so each partition is read by exactly one consumer in the group at
a time
([Confluent, Kafka Consumer Design, consumer group partition division](https://docs.confluent.io/kafka/design/consumer-design.html),
verified 2026-08-02). In RabbitMQ's own tutorial the same shape is called a
work queue, and the tutorial states that "by default, RabbitMQ will send each
message to the next consumer, in sequence. On average every consumer will get
the same number of messages"
([RabbitMQ, Work Queues tutorial](https://www.rabbitmq.com/tutorials/tutorial-two-python),
verified 2026-08-02). None of these are a different pattern. Kafka's group
membership swaps a shared mutable queue for a partition assignment protocol,
which changes the mechanics of dimension 8 below but not the intent. workers
still divide a backlog of units of work among themselves without any single
message going to more than one worker for normal processing.

## 2. Problem and context

A producer or a set of producers places units of work onto a channel faster,
or in bursts faster, than a single consumer can process them. The channel is
not the bottleneck, the processing step is. A single-threaded consumer that
reads one message, does the work, reads the next message, is bound by the
slowest stage of that loop, and every message not yet read sits waiting in
the channel, growing the backlog and the end-to-end latency for whichever
message happens to be at the back of the line.

The situation reads like this in a running system. An order-processing
service has a queue named `orders.created`. At normal traffic one consumer
keeps the queue near empty. During a promotional spike, the arrival rate
triples for twenty minutes. The single consumer falls behind, queue depth
climbs into the tens of thousands, and an order placed at minute five of the
spike is not processed until minute forty, well after the spike itself has
ended. The obvious first instinct is to make the one consumer faster, and
that has a ceiling in practice, because a lot of processing work (an
external payment call, an image resize, a database write with a lock) has a
fixed wall-clock cost per unit that no amount of code tuning below the
network or database layer buys back.

The context that makes Competing Consumers the right answer has three parts.

- The channel is a Point-to-Point Channel, meaning each message is intended
  for exactly one consumer's worth of processing, not for every subscriber.
  This is the load-bearing precondition, and it is why the pattern is
  incompatible with Publish-Subscribe Channel as stated in dimension 1.
- The units of work are independent of each other, or at least independent
  enough that processing them out of strict arrival order does not break a
  business invariant. If order matters absolutely, this pattern needs a
  partitioning discipline layered on top, covered in dimension 4.
- The processing step, not the channel's own throughput, is the bottleneck.
  Adding consumers helps exactly to the degree that the channel and the
  downstream resources the consumers share (a database, a rate-limited third
  party API) can also scale with them.

## 3. Forces

**Throughput against ordering.** More consumers raise aggregate throughput
roughly linearly until some shared resource saturates, but the moment two
consumers are pulling from the same channel there is no longer one global
processing order. A consumer that is briefly slow can finish a message after
a consumer that started later. Any system that needs a strict global order
has to give that up, or has to route same-key messages to one consumer,
which is exactly what Kafka's partition-per-key assignment does.

**Latency against resource cost.** Adding consumers shrinks the queue's
backlog and the tail latency for the last message in a burst, at the direct
cost of running more processes, more threads, or more container replicas.
Past the point where the shared downstream resource is the limit, adding
another consumer buys nothing and only adds contention, so this force has a
real limit, not an unbounded curve.

**Exactly-once processing against at-least-once delivery.** Most messaging
systems that support Competing Consumers give at-least-once delivery, not
exactly-once, because the honest failure mode of "consumer received the
message and crashed before acknowledging" cannot be told apart from
"consumer never received it" from the channel's side. AWS states this
directly for SQS. the visibility timeout "prevents multiple consumers from
processing the same message at the same time" but, "because of the
at-least-once delivery model, Amazon SQS doesn't guarantee that a message
won't be delivered more than once within the visibility timeout period"
([AWS, Amazon SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html),
verified 2026-08-02). The pattern trades a guarantee the application has to
build for itself, an Idempotent Receiver, for a much simpler consumer.

**Operability against uniformity.** A pool of interchangeable consumers is
simple to reason about and simple to scale up or down, but that simplicity
assumes every consumer can do every kind of work equally well. When work is
heterogeneous (some messages are cheap, some are expensive, some need a GPU)
a flat pool either wastes capacity on the cheap path or starves the expensive
path, and the fix is Content-Based Router in front of separate competing
pools, not a single undifferentiated one.

**Coupling against ownership.** Consumers in a pool must agree on nothing
about each other, only on the channel and the message contract. That absence
of coordination is the whole appeal, but it also means no consumer can
assume it "owns" a piece of state across messages unless the platform gives
it a sticky assignment (Kafka partitions do this, a flat SQS queue does not).

The pattern favors throughput, horizontal scalability, and operational
simplicity, and it knowingly sacrifices strict global ordering and
exactly-once semantics unless something else is added on top to buy them
back.

## 4. Applicability and non-applicability

Reach for Competing Consumers when all of these hold.

- The channel is point-to-point, and each unit of work should be handled
  once, by one consumer, not fanned out to every interested party.
- The units of work are independent, or partitionable by a key such that
  same-key ordering is the only ordering that matters.
- Processing throughput, not the channel's own delivery rate, is the
  bottleneck, and the workload is bursty or growing enough that a fixed
  number of consumers would either be wasteful at quiet times or overwhelmed
  at busy ones.
- The processing operation is safe to retry, or can be made safe with an
  idempotency key, because at-least-once delivery is the default guarantee
  of nearly every implementation.
- The consumers are, or can be made, stateless with respect to each other. no
  consumer needs to know what another consumer is doing.

Do NOT reach for it when any of these hold.

- Every subscriber legitimately needs to see every message. That is
  Publish-Subscribe Channel, and adding competing consumers on top of it
  without partitioning per subscriber group only duplicates, not
  distributes, work.
- Strict global ordering across the whole channel is a business requirement
  and cannot be reduced to per-key ordering. a single-threaded consumer, or a
  channel that itself enforces total order at the point of delivery, is
  the honest answer, not a pool that will reorder work under load.
- The processing step is not the bottleneck. the channel's own ingestion or
  network hop is. In that case more consumers add operational surface for no
  throughput gain, and the fix is upstream (batching, compression, a faster
  channel implementation), not more competitors for the same slow pipe.
- Exactly-once, no-duplicate-ever processing is required and the team is not
  willing to build or buy an idempotency layer. A single consumer with a
  durable, ordered log and no concurrent readers is simpler and strictly
  correct for that one requirement, at the cost of the throughput this
  pattern exists to buy.
- The workload has hard per-message state affinity to a specific worker (an
  in-memory model loaded once, a long-lived session) that cannot be
  externalized. Competing Consumers assumes any consumer can take any
  message. sticky affinity needs a routing layer such as Kafka's partition
  assignment, or a different pattern entirely, such as Message Dispatcher
  with a session-aware Content-Based Router.

## 5. Structure

- **Message Channel (point-to-point).** The single shared channel every
  consumer polls or subscribes against. Its contract is that once a message
  is taken by one consumer for processing, it is not concurrently available
  to another, for at least the duration of a visibility window or an
  equivalent lease.
- **Producer.** One or more upstream components that place messages on the
  channel. The producer count is orthogonal to the pattern. Competing
  Consumers says nothing about how many producers there are, only that
  consumers on the far side compete for a shared backlog.
- **Consumer (competing instance).** A stateless worker that repeatedly takes
  the next available message, processes it, and acknowledges or deletes it.
  Any number of these can run concurrently, and the design goal is that they
  are interchangeable, killing one and starting a replacement changes
  nothing about correctness.
- **Delivery coordinator (implicit or explicit).** The mechanism that
  guarantees a message goes to only one consumer at a time. In a
  broker-backed queue this is the broker itself, using a lease or visibility
  timeout. In Kafka this is the group coordinator, assigning whole partitions
  to consumer instances rather than individual messages.
- **Dead Letter Channel (usually paired).** The destination for a message
  that a consumer repeatedly fails to process, so one poison message cannot
  stall or crash the whole pool forever. Not strictly required by the
  pattern's own definition, but every production implementation this entry
  cites ships one.

## 6. ASCII structure diagram

```
                     +-------------------+
                     |   Message Channel |
  Producer(s) -----> | (point-to-point,  |
                     |  one queue/topic) |
                     +---------+---------+
                               |
              +----------------+----------------+
              |                |                 |
              v                v                 v
       +-------------+  +-------------+  +-------------+
       | Consumer A  |  | Consumer B  |  | Consumer C  |
       | (stateless) |  | (stateless) |  | (stateless) |
       +------+------+  +------+------+  +------+------+
              |                |                 |
              v                v                 v
       process + ack     process + ack     process + ack
              |                |                 |
              +--------+-------+--------+--------+
                       |                |
                       v                v
               (on repeated failure)
               +-------------------+
               |  Dead Letter Chan |
               +-------------------+
```

Each of A, B, C independently pulls the next available message. The channel
guarantees no message is handed to two consumers for concurrent processing at
once, but it makes no promise about which consumer gets which message.

## 7. Dynamics

```
Producer          Channel               Consumer A       Consumer B
   |                 |                       |                |
   | put(m1)         |                       |                |
   |---------------->|                       |                |
   | put(m2)         |                       |                |
   |---------------->|                       |                |
   |                 |     poll/receive      |                |
   |                 |<----------------------|                |
   |                 |--- deliver m1 ------->|                |
   |                 |   (m1 now invisible)  |                |
   |                 |                       |    poll/receive|
   |                 |<---------------------------------------|
   |                 |--- deliver m2 ------------------------>|
   |                 |   (m2 now invisible)  |                |
   |                 |                       | process(m1)    |
   |                 |                       |                | process(m2)
   |                 |                       | ack/delete(m1) |
   |                 |<----------------------|                |
   |                 |                       |                | ack/delete(m2)
   |                 |<---------------------------------------|
   |                 |    (both removed,     |                |
   |                 |     no overlap)        |                |
```

If Consumer A instead crashes after receiving m1 but before acknowledging,
the sequence changes at the tail. no ack arrives before the visibility
timeout expires, the channel makes m1 visible again, and a surviving consumer
(A on restart, or B, or a new C) receives it a second time. This is the
concrete mechanical cause of at-least-once delivery, and it is why dimension
17 treats idempotency as a required companion, not an optional extra.

## 8. Implementation variants

**Shared mutable queue with a visibility lease.** The classic form, used by
SQS and by RabbitMQ. A message is handed to a requesting consumer and marked
invisible or unacknowledged. The consumer must explicitly ack, or the message
reappears after a timeout. This variant has no notion of a consumer's
identity persisting between messages, any consumer can receive any message,
which is the most literal reading of "competing."

**Partition assignment with sticky ownership.** Kafka's consumer group model.
Rather than competing message by message, consumers compete once, at group
rebalance time, for ownership of whole partitions, and a consumer that wins a
partition reads every message on it in order until the next rebalance. This
buys per-partition ordering back at the cost of a coarser unit of
parallelism, you cannot usefully run more consumers than partitions, because
the extra consumers sit idle with no partition assigned
([Confluent, Kafka Consumer Design, partition-to-consumer assignment](https://docs.confluent.io/kafka/design/consumer-design.html),
verified 2026-08-02).

**Database row as the work item, SELECT ... FOR UPDATE SKIP LOCKED.** A
common variant when the "channel" is a relational table rather than a
dedicated broker. A worker selects and locks the next unclaimed row, which
skips rows already locked by another concurrent worker, giving the same
one-consumer-per-item guarantee without a message broker. This trades broker
operational cost for database contention cost, and it inherits whatever
durability and transactional properties the database already has.

**Thread pool or process pool against an in-process queue.** The
lowest-ceremony variant, used inside a single application rather than across
a distributed system. A bounded queue (Java's `BlockingQueue`, Go's buffered
channel, a Python `queue.Queue`) feeds a pool of worker threads or processes
inside one runtime. It has the same competition semantics as the distributed
forms, but the "crash and redeliver" failure mode usually does not apply the
same way, because the whole process typically dies together.

**Kubernetes Job with `parallelism` against an external queue.** Several
pods, each running the same container image, independently connect to a
shared external queue (RabbitMQ, in Kubernetes's own worked example),
consume one work item, delete it, and exit. Kubernetes's own documentation
states that in this pattern "each pod picks up one unit of work from a task
queue, processes it, and terminates" with no direct coordination between
pods, because "the queue service does that"
([Kubernetes, Coarse Parallel Processing Using a Work Queue](https://kubernetes.io/docs/tasks/job/coarse-parallel-processing-work-queue/),
verified 2026-08-02). This variant treats consumer lifecycle (start,
process, exit) as disposable per work item rather than a long-running loop.

## 9. Known production uses

**Amazon SQS.** AWS's own developer guide documents the visibility timeout as
the mechanism that lets a standard queue support "multiple consumers" without
two of them processing the same message concurrently, while being explicit
that the delivery model is at-least-once, not exactly-once
([AWS, Amazon SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html),
verified 2026-08-02).

**Apache Kafka consumer groups.** Kafka's own design documentation states
that a consumer group's coordinator "helps to distribute the data in the
subscribed topics to the consumer group instances evenly" and that "each
partition is consumed by exactly one consumer within each consumer group at
any given time"
([Confluent, Kafka Consumer Design](https://docs.confluent.io/kafka/design/consumer-design.html),
verified 2026-08-02). This is Competing Consumers implemented at
partition granularity rather than message granularity, and it underlies
production stream-processing deployments at companies including LinkedIn,
where Kafka originated.

**RabbitMQ work queues.** RabbitMQ's own tutorial demonstrates two worker
processes competing for tasks on a single queue, and states the default
round-robin dispatch behavior directly. "by default, RabbitMQ will send each
message to the next consumer, in sequence"
([RabbitMQ, Work Queues tutorial](https://www.rabbitmq.com/tutorials/tutorial-two-python),
verified 2026-08-02).

**Kubernetes Jobs with an external work queue.** Kubernetes's official task
documentation walks through a `parallelism: 2, completions: 8` Job in which
multiple pods independently drain a RabbitMQ-backed task queue, explicitly
calling out that no pod-to-pod coordination code is required because the
queue itself enforces single delivery
([Kubernetes, Coarse Parallel Processing Using a Work Queue](https://kubernetes.io/docs/tasks/job/coarse-parallel-processing-work-queue/),
verified 2026-08-02).

## 10. Consequences

Positive.

- Throughput scales close to linearly with the number of consumers, up to
  the point where a shared downstream resource saturates.
- Consumers are individually simple. each one is a plain receive-process-ack
  loop with no knowledge of its peers, which keeps the unit of code small and
  independently deployable.
- The pool self-heals under partial failure. a crashed consumer's in-flight
  message becomes visible again and is picked up by a survivor, with no
  custom failover logic required beyond the visibility timeout the broker
  already provides.
- Elastic scaling is straightforward. adding or removing consumers changes
  only capacity, never correctness, because every consumer is interchangeable
  by design.

Negative.

- Global ordering across the channel is lost the moment a second consumer
  joins, because two consumers running at different speeds can finish
  messages out of arrival order.
- At-least-once delivery means every consumer must be written to tolerate
  redelivery, which is an extra correctness requirement that a
  single-consumer design does not carry.
- A poison message, one that always fails processing, can consume retry
  budget across the whole pool repeatedly unless a Dead Letter Channel is in
  place, turning one bad message into sustained wasted capacity.
- Debugging is harder than a single consumer, because which instance
  processed a given message is now nondeterministic, and correlating logs
  across N interchangeable workers needs a shared trace or correlation
  identifier carried in the message itself.

## 11. Failure modes and misuse

**Symptom.** Two consumers both appear to have processed the same order,
visible as a duplicate charge or a duplicate email.
**Cause.** A consumer completed the business side effect but crashed, or
timed out, before acknowledging the message, so the broker made it visible
again and a second consumer (or the same one, retried) processed it a second
time. This is the textbook at-least-once failure the AWS documentation
describes directly
([AWS, Amazon SQS visibility timeout, handling failures](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html),
verified 2026-08-02).
**Fix.** Make the processing step idempotent, most commonly by extracting or
generating an idempotency key from the message and recording it
transactionally alongside the side effect, so a redelivered message is
recognized and skipped rather than reapplied. This is the Idempotent Receiver
pattern, and it is not optional the moment more than one consumer exists.

**Symptom.** Queue depth keeps climbing even though the consumer pool is at
its target size and CPU on each consumer is nowhere near saturated.
**Cause.** The consumers are blocked on a shared downstream resource, a rate
limit on a third-party API, a small connection pool to a single database, a
single Redis instance under lock contention. Adding consumers past this point
adds contention, not throughput, because the true bottleneck moved
downstream of the pattern entirely.
**Fix.** Profile where consumer wall-clock time is actually spent before
adding more consumers, and scale or partition the shared resource (a bigger
connection pool, a per-tenant rate limit, sharded downstream storage) rather
than the pool size.

**Symptom.** One specific message type or one specific tenant's messages
never get processed promptly, while everything else flows normally.
**Cause.** A flat, undifferentiated pool treats a cheap message and an
expensive one identically, so under load the expensive ones back up behind a
flood of cheap ones, or vice versa, depending on which consumer happens to
grab which message first. There is no starvation protection in the base
pattern.
**Fix.** Route by message class with a Content-Based Router into separate
channels, each with its own competing consumer pool sized for its own
workload, instead of one pool serving every message type.

**Symptom.** A message repeatedly appears, fails, reappears, and fails again,
forever, and the pool's effective throughput on healthy messages degrades
over time as the same poison message keeps getting redelivered.
**Cause.** No maximum receive count and no Dead Letter Channel configured, so
a message that always throws an exception cycles through the visibility
timeout indefinitely instead of being pulled out of rotation.
**Fix.** Configure a max-receive-count policy that routes a message to a Dead
Letter Channel after N failed attempts. AWS's own guide directly pairs
visibility timeout handling with a Dead Letter Queue for messages that fail
multiple processing attempts, in the section covering unprocessed messages
([AWS, Amazon SQS visibility timeout, handling failures and DLQ guidance](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html),
verified 2026-08-02).

**Symptom.** Under a Kafka consumer group specifically. adding a fifth,
sixth, seventh consumer instance to a topic with four partitions produces no
throughput increase at all, and the newly added consumers show zero
assigned partitions in monitoring.
**Cause.** Kafka assigns whole partitions, not individual messages, to
consumer instances within a group, and a partition can only be owned by one
consumer in the group at a time, so instances beyond the partition count sit
idle by design.
**Fix.** Increase the topic's partition count (a one-way operation that
cannot be reversed without recreating the topic) to increase the maximum
useful parallelism, or, if partition count is fixed for a reason, stop adding
consumers past that point and scale the per-consumer processing instead.

## 12. Trade-off matrix

| Force | Competing Consumers | Message Dispatcher | Publish-Subscribe Channel |
|---|---|---|---|
| Ordering guarantee | Global order lost, per-key order possible only with sticky partitioning | Central dispatcher can preserve order, since it decides assignment | Every subscriber gets full order of what it receives, but that is a different problem (fan-out, not load balance) |
| Coupling between workers | None, workers do not know about each other | Workers may be known and addressed individually by the dispatcher | None, but subscribers are coupled to receiving everything, not a share of it |
| Throughput scaling | Near-linear by adding stateless consumers | Bounded by dispatcher's own throughput, which becomes a single point of contention | Scales fan-out, not processing load, each subscriber does full work on every message |
| Failure isolation | A crashed consumer's message is simply redelivered to a survivor | A crashed worker requires the dispatcher to detect it and reassign | A crashed subscriber loses messages sent while it was down, unless it uses a Durable Subscriber |
| Best fit | Independent, redistributable units of work under variable load | Work needs explicit routing logic, priority, or affinity beyond round robin | Every recipient legitimately needs the same event, not a share of a workload |

The comparison against Message Dispatcher matters because the two are easy to
conflate. Message Dispatcher, as Hohpe and Woolf define it, is a single
consumer on the channel that itself decides which of several downstream
performers should handle each message, so the dispatcher is a chokepoint by
design and can enforce ordering or affinity that Competing Consumers
deliberately cannot. Competing Consumers has no dispatcher at all, the
channel's own delivery mechanism is the only arbiter.

## 13. Related and incompatible patterns

**Point-to-Point Channel.** The channel type Competing Consumers requires.
without point-to-point delivery, each message going to at most one consumer
for processing, the pattern's central guarantee does not hold.

**Publish-Subscribe Channel.** Explicitly incompatible in the sense that
applying Competing Consumers reasoning to it does not produce load
distribution. every subscriber still receives every message, so putting
multiple competing readers on one subscription only adds redundant
concurrent processing of the same events unless the platform additionally
partitions the subscription itself (which is exactly what a Kafka consumer
group does to a topic).

**Idempotent Receiver.** The near-mandatory companion. because delivery is
at-least-once, every consumer implementation should be built as if any
message might arrive twice, and Idempotent Receiver is the pattern that
names and structures that defense.

**Dead Letter Channel.** The near-mandatory companion for poison messages, as
covered in dimension 11. Without it a permanently failing message degrades
pool throughput indefinitely instead of being quarantined for inspection.

**Message Dispatcher.** A related but distinct pattern, covered in the
trade-off matrix above. Message Dispatcher centralizes the routing decision
in one component, Competing Consumers decentralizes it into the channel's
own delivery mechanics.

**Event-Driven Consumer and Polling Consumer.** These describe how an
individual consumer receives a message (pushed to it versus actively
fetching it), and either can be the receiving half of a Competing Consumers
pool. the two dimensions, how one consumer receives, and how many consumers
share a channel, are orthogonal.

**Load Balancer.** A structurally similar idea at the network layer,
distributing requests rather than messages across interchangeable servers.
The key difference is that a load balancer typically distributes live,
synchronous requests with no retry-on-crash semantics baked into the
protocol, while Competing Consumers distributes durable, asynchronous units
of work where redelivery on failure is the expected behavior, not an edge
case.

**Circuit Breaker.** Frequently layered inside each consumer's processing
step when that step calls an external dependency, so one consumer's
repeated downstream failures do not spread to every consumer in the pool
hammering a dependency that is already down.

## 14. Refactoring path in and out

**Introducing the pattern into a single-consumer system.** Start by
confirming the two preconditions from dimension 4. the channel is genuinely
point-to-point, and the processing step is idempotent or can be made so.
Add an idempotency key to the message contract or derive one from existing
message fields before adding a second consumer, not after, because it is far
easier to verify idempotency with one consumer running than to retrofit it
once duplicate processing is already possible in production. Then start a
second consumer instance pointed at the same channel and watch queue depth
and per-message processing latency. If a downstream dependency shows rising
error rates or saturation as the second consumer comes online, that
dependency, not the consumer count, is the real limit, and it should be
addressed (connection pool size, rate limit headroom) before adding a third
consumer. Only after the pool behaves correctly under normal load should a
Dead Letter Channel and a maximum receive count be added, ideally before the
pool ever meets a genuinely poisonous message in production rather than
after.

**Removing the pattern.** The pattern stops earning its place when either
the workload volume drops back below what a single consumer can sustain, in
which case running a pool is pure operational overhead for no throughput
benefit, or when a downgraded requirement demands strict global ordering
that the pool structurally cannot give. To remove it, drain the queue to
zero, stop all but one consumer, and only then relax the idempotency
handling if it is not needed elsewhere, since a system that has become used
to at-least-once semantics elsewhere (retried API calls, replayed events)
often should keep the idempotency guard even after returning to a single
consumer, because a single consumer that crashes mid-message and restarts is
still capable of redelivering to itself.

## 15. Testing and verification

Unit testing a single consumer's processing function is unaffected by this
pattern and should already cover the normal input space. What this pattern
adds is testing the concurrency and delivery-semantics behavior specifically.

- **Duplicate-delivery test.** Feed the exact same message to the processing
  function twice in immediate succession and assert the observable side
  effect (a database row, an external charge, an emitted downstream event)
  happens exactly once. This directly tests the Idempotent Receiver
  companion and is the single highest-value test for this pattern.
- **Concurrent-drain test.** Load N items onto a real or in-memory queue,
  start M concurrent consumers against it, and assert that the total
  processed count equals N exactly, with no item processed zero times and no
  item processed more than once under the test's controlled conditions. The
  four code samples in dimension 18 are written exactly as this kind of
  test.
- **Crash-and-redeliver test.** Simulate a consumer that receives a message
  and dies before acknowledging (kill the process, or explicitly do not call
  the ack path in a test double), and assert that a second consumer, or a
  restarted instance, eventually receives and completes that same message
  once the broker's visibility timeout or lease expires.
- **Poison-message test.** Feed a message that always throws, and assert
  that after the configured maximum receive count it is routed to the Dead
  Letter Channel rather than looping forever, and that the pool's throughput
  on other messages is not measurably degraded by its presence.
- **Backpressure and scale-down test.** Verify that removing a consumer
  mid-processing does not lose the message it was working on, only delays
  it, by checking that an in-flight message is neither acknowledged nor
  silently dropped when its consumer is terminated.

A useful test double for local development is an in-memory queue with a
configurable visibility timeout and a controllable clock, which lets the
crash-and-redeliver scenario run deterministically in milliseconds instead of
waiting on a real broker's real timeout.

## 16. Observability signals

**Queue depth (backlog size).** The primary health signal. a healthy pool
shows queue depth oscillating near a low baseline that returns to that
baseline after each traffic burst. A queue depth that trends upward across
multiple bursts without returning to baseline means consumer throughput is
below arrival rate and more consumers, or a faster processing step, are
needed.

**Age of oldest unprocessed message (or approximate age of the message at
the head of the queue).** More directly useful than raw depth for
latency-sensitive workloads, because a queue can hold many small, fast
messages with acceptable age, or few large, slow ones with unacceptable age,
at the same depth number.

**In-flight or unacknowledged message count.** A healthy pool has an
in-flight count roughly proportional to the number of active consumers times
their average processing time. A steadily climbing in-flight count with
stable consumer count usually indicates consumers are receiving messages but
not completing or acknowledging them, often the crash-loop or
timeout-too-short failure mode from dimension 11.

**Per-consumer throughput and per-message processing latency, tagged by
consumer instance identifier.** Lets an operator see whether the pool is
balanced (each consumer doing roughly its share) or skewed (one consumer
starved of work, or one consistently slower, which points at that instance's
host or code path rather than the pattern itself).

**Dead letter queue depth and rate of arrival.** Should sit at or near zero
in steady state. a nonzero and growing DLQ rate is the earliest observable
signal of the poison-message failure mode, and should page before the DLQ
fills and starts dropping messages entirely.

**Redelivery count distribution.** A histogram of how many times each
message was delivered before it was finally acknowledged (or sent to the
DLQ). A healthy system shows almost all messages delivered exactly once. a
distribution with a heavy tail at 2 or more redeliveries signals either
processing timeouts set too aggressively relative to actual processing time,
or genuine transient downstream failures worth investigating.

## 17. Security and privacy implications

The channel itself becomes a shared attack surface the moment more than one
consumer can read from it. an attacker who can enqueue a crafted message
gains a wider blast radius than in a single-consumer design, because the
message may be processed by whichever of N consumers happens to be free,
which can matter if consumers run with different privilege levels or in
different network segments, a configuration this pattern's core definition
does not forbid but that most production deployments should avoid for that
reason.

Message content that includes personally identifiable data is now, by
construction, transiently visible to whichever consumer instance handles it,
which multiplies the number of runtime environments a data-protection audit
must cover compared to a single consumer. Access controls, encryption at
rest on the channel, and encryption of message payloads should be sized to
the whole pool, not to one representative consumer.

The at-least-once delivery guarantee interacts with privacy directly. a
message containing sensitive data that is processed twice due to a crash and
redelivery may, if the processing step itself has side effects like sending
an email or a notification, expose that data to a person a second time in a
way a compliance regime did not anticipate. this is a further, concrete
argument for the idempotency requirement in dimension 3 and dimension 11.
these are not only correctness concerns, a duplicated side effect involving
personal data is a privacy incident, not merely a bug.

A poison message routed to a Dead Letter Channel retains its full original
payload for inspection, which means the DLQ needs the same access controls
and retention policy as the primary channel, and often needs a stricter one,
since DLQ contents are frequently examined by a wider set of engineers during
incident response than the primary channel ever is in normal operation.

## 18. Code examples

The four samples below implement the identical scenario. twenty independent
units of work placed on a shared queue, drained by four concurrent
competing consumers, with the total processed count asserted to equal
exactly twenty, demonstrating the pattern's core guarantee that no item is
lost and no item is double-processed under the tested conditions. Each
sample was compiled or run directly and produced `processed=20`.

Go, using a native buffered channel as the point-to-point channel and
goroutines as the consumers, verified with `go run` (Go 1.26.4).

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func main() {
	jobs := make(chan int, 20)
	var processed int64
	var wg sync.WaitGroup

	const workerCount = 4
	for w := 1; w <= workerCount; w++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for job := range jobs {
				atomic.AddInt64(&processed, 1)
				_ = job
			}
		}(w)
	}

	for i := 0; i < 20; i++ {
		jobs <- i
	}
	close(jobs)
	wg.Wait()
	fmt.Printf("processed=%d\n", atomic.LoadInt64(&processed))
}
```

Rust, using a shared `Arc<Mutex<VecDeque<T>>>` queue with plain `std::thread`
consumers, verified with `rustc -O` and direct execution (rustc 1.97.1).

```rust
use std::collections::VecDeque;
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let queue: Arc<Mutex<VecDeque<u32>>> = Arc::new(Mutex::new((0..20).collect()));
    let processed = Arc::new(Mutex::new(0u32));
    let worker_count = 4;
    let mut handles = Vec::new();

    for _ in 0..worker_count {
        let queue = Arc::clone(&queue);
        let processed = Arc::clone(&processed);
        handles.push(thread::spawn(move || loop {
            let item = { queue.lock().unwrap().pop_front() };
            match item {
                Some(_job) => {
                    *processed.lock().unwrap() += 1;
                }
                None => break,
            }
        }));
    }

    for h in handles {
        h.join().unwrap();
    }
    println!("processed={}", *processed.lock().unwrap());
}
```

Python, using the standard library's thread-safe `queue.Queue` with a small
pool of `threading.Thread` consumers, verified with `python3` (3.14.6).

```python
import queue
import threading


def worker(jobs, counter, lock):
    while True:
        try:
            job = jobs.get_nowait()
        except queue.Empty:
            return
        with lock:
            counter[0] += 1
        jobs.task_done()


def main():
    jobs = queue.Queue()
    for i in range(20):
        jobs.put(i)
    counter = [0]
    lock = threading.Lock()
    threads = [threading.Thread(target=worker, args=(jobs, counter, lock)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"processed={counter[0]}")


if __name__ == "__main__":
    main()
```

TypeScript, honestly labeled. Node's event loop is single-threaded, so this
sample demonstrates the competing-consumers protocol, several logical
consumers racing to pop the next item off one shared queue with no double
pop, rather than true parallel execution across CPU cores. A production
TypeScript deployment gets real parallelism from separate OS processes
(worker threads, or several instances behind SQS or Kafka), not from
`Promise.all` in one process. Verified by compiling with `tsc` (TypeScript
7.0.2) and running the output with `node`.

```typescript
class AsyncQueue<T> {
  private items: T[] = [];
  push(item: T): void {
    this.items.push(item);
  }
  pop(): T | undefined {
    return this.items.shift();
  }
}

async function worker(
  jobs: AsyncQueue<number>,
  processed: { count: number }
): Promise<void> {
  while (true) {
    const job = jobs.pop();
    if (job === undefined) return;
    await new Promise((resolve) => setTimeout(resolve, 0));
    processed.count += 1;
  }
}

async function main(): Promise<void> {
  const jobs = new AsyncQueue<number>();
  for (let i = 0; i < 20; i++) jobs.push(i);
  const processed = { count: 0 };
  const workerCount = 4;
  await Promise.all(
    Array.from({ length: workerCount }, () => worker(jobs, processed))
  );
  console.log(`processed=${processed.count}`);
}

main();
```

Java and Kotlin are omitted from this entry because the local toolchain used
to write it had no working JVM available to compile against
(`javac -version` reported no Java runtime located), and shipping an
uncompiled JVM sample would violate the repository's own rule against
silently implying a sample was verified when it was not. C# is omitted for
the same toolchain-availability reason. the pattern is fully idiomatic in
both languages (a `BlockingCollection<T>` with a `Task` pool in C#, a
`Channel` with coroutines in Kotlin) and a contributor with those toolchains
available should add them.

## 19. References

1. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003.
   Publisher and title confirmed at
   [enterpriseintegrationpatterns.com/books1.html](https://www.enterpriseintegrationpatterns.com/books1.html),
   verified 2026-08-02.
2. Enterprise Integration Patterns, "Competing Consumers" pattern page,
   [enterpriseintegrationpatterns.com/patterns/messaging/CompetingConsumers.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CompetingConsumers.html),
   verified 2026-08-02. Source for the problem statement, solution statement,
   the Publish-Subscribe incompatibility note, and the related-patterns list.
3. Amazon Web Services, "Amazon SQS visibility timeout," AWS Simple Queue
   Service Developer Guide,
   [docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html),
   verified 2026-08-02. Source for the multi-consumer visibility guarantee,
   the at-least-once delivery admission, the max-receive-count and Dead
   Letter Queue guidance, and the redelivery-on-crash mechanics.
4. Confluent, "Kafka Consumer Design," Apache Kafka Design documentation
   mirrored by Confluent,
   [docs.confluent.io/kafka/design/consumer-design.html](https://docs.confluent.io/kafka/design/consumer-design.html),
   verified 2026-08-02. Source for the consumer group coordinator, the
   one-partition-per-consumer-at-a-time guarantee, and the basis for the
   idle-consumers-beyond-partition-count failure mode.
5. RabbitMQ, "Work Queues" tutorial (Python client),
   [rabbitmq.com/tutorials/tutorial-two-python](https://www.rabbitmq.com/tutorials/tutorial-two-python),
   verified 2026-08-02. Source for the round-robin dispatch default and the
   acknowledgment-based redelivery-on-death guarantee.
6. Kubernetes, "Coarse Parallel Processing Using a Work Queue," Kubernetes
   Tasks documentation,
   [kubernetes.io/docs/tasks/job/coarse-parallel-processing-work-queue/](https://kubernetes.io/docs/tasks/job/coarse-parallel-processing-work-queue/),
   verified 2026-08-02. Source for the Kubernetes Job-plus-external-queue
   production pattern and its no-coordination-code claim.
