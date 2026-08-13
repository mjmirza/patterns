---
name: Event-Driven Consumer
slug: event-driven-consumer
family: 07-integration
category: Integration
aliases: [Message-Driven Consumer, Asynchronous Receiver, Consumer Endpoint]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [competing-consumers, polling-consumer, publish-subscribe-channel, message-endpoint, dead-letter-channel, saga]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Event-Driven Consumer, set by Gregor Hohpe and Bobby
Woolf in Enterprise Integration Patterns (Addison-Wesley, 2003), the catalog
that gave a common vocabulary to asynchronous integration. The book's chapter
on Message Endpoints frames it as one half of a pair, the other half being the
Polling Consumer. An Event-Driven Consumer is invoked automatically when a
message arrives on the channel it listens to, rather than pulling for work on
a schedule.

In application frameworks the same idea usually goes by Message-Driven
Consumer, which is the term the Java EE specification and later Jakarta EE
used for a Message-Driven Bean, and in the Spring ecosystem it appears as a
listener container invoking an annotated method, for example `@KafkaListener`
or `@RabbitListener`. Confluent's own consumer documentation calls the
underlying mechanism the client library's poll loop, but the application code
written against it is still event-driven from the developer's point of view
because the framework, not the developer, decides when to call the handler
(Confluent, Kafka Consumer, docs.confluent.io/platform/current/clients/consumer.html,
verified 2026-08-02). AWS names the equivalent construct an event source
mapping when a Lambda function is invoked by a queue or stream. The pattern is
the same shape wearing different vendor names, a piece of code that reacts to
an event rather than asking for one.

## 2. Problem and context

A service needs to react when something happens elsewhere in the system, a
payment is captured, an order is placed, a file lands in a bucket, a row is
updated in another team's database. The naive first implementation is a loop
that asks a queue or a database whether there is anything new on a fixed
interval. That loop wastes CPU when nothing is happening, adds latency equal
to half the polling interval on average, and gets harder to reason about the
moment two or three services all poll the same source. Each additional
poller multiplies load on the source and multiplies the chance that two
pollers race for the same row.

The Event-Driven Consumer inverts the control. The messaging infrastructure,
not the consumer's own code, decides when the handler runs. The consumer
registers interest in a channel or topic once, at startup, and from that
point forward the runtime delivers messages to it as they arrive. Hohpe and
Woolf describe this explicitly as trading the consumer's control over timing
for lower latency and less wasted work, and note that the event-driven model
is usually the default choice unless the consumer specifically needs to
control its own pace, for example to throttle against a downstream system
that cannot absorb bursts.

The context in which this pattern belongs is any integration where messages
arrive at an unpredictable rate, more than one producer or consumer may
exist, and the business does not need synchronous confirmation that the work
is finished before the producer continues. It does not belong inside a
request-response call where the caller is blocked waiting for an answer,
that is a different problem with a different pattern, see the
non-applicability list below.

## 3. Forces

Latency versus resource cost. An event-driven consumer notified the instant a
message lands has near-zero added latency, but the runtime that delivers
that notification, whether it is a broker's push protocol, an operating
system's I/O completion port, or a cloud provider's event source mapping,
has to hold a live connection or a registered callback open. A polling
consumer trades that idle cost for periodic wasted work.

Backpressure versus throughput. An event-driven consumer that accepts every
delivery the instant it arrives has no natural brake. If the source can push
faster than the consumer can process, the consumer either buffers
unboundedly, drops work, or crashes. Almost every production event-driven
system therefore reintroduces a form of pull inside the push, Kafka's own
consumer client polls internally even though the application code looks
event-driven, and reactive streams libraries implement `request(n)` so the
subscriber still controls how many events are in flight. This is judgement.
In practice the forces of latency and backpressure are never fully
independent, an event-driven consumer that ignores backpressure is only
event-driven until the first traffic spike.

Ordering versus parallelism. A single event-driven consumer processing one
partition or one queue in order gives strict ordering but limits throughput
to one message at a time. Adding more consumers for parallelism, the
Competing Consumers pattern, breaks ordering across consumers unless the
source partitions work by a key, as Kafka does by producing all messages for
one key to the same partition, which is one consumer's job.

Coupling versus autonomy. The Event-Driven Consumer decouples the producer
from knowing who consumes its events, the producer publishes and moves on.
The cost is that the producer has weaker guarantees about what happens to
the event afterward, and debugging a chain of five event-driven consumers
reacting to one root event is materially harder than tracing a synchronous
call stack.

Idempotency versus simplicity. Because most transports guarantee
at-least-once delivery rather than exactly-once, as AWS documents explicitly
for SQS (AWS, Amazon SQS visibility timeout,
docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html,
verified 2026-08-02), the handler code must tolerate redelivery. That is
extra code the consumer author must write, in exchange for a transport that
never silently drops a message under normal operation.

## 4. Applicability and non-applicability

Reach for an Event-Driven Consumer when the producer does not need the
consumer's answer before continuing, when the rate and timing of events is
unpredictable, when more than one consumer may need the same event, when low
latency between event and reaction matters, and when the transport already
provides at-least-once or exactly-once delivery guarantees the application
can build on rather than reinvent.

Do not reach for it in these cases.

When the caller needs a synchronous answer to proceed. A checkout flow that
must show the customer a confirmation number in the same HTTP response has
no use for an asynchronous consumer on the critical path, use a direct call
or a request-reply pattern with a correlation identifier instead, and treat
any event-driven side effects as strictly secondary.

When strict global ordering across all events is required and the source
cannot partition work by a key. A single event-driven consumer on an
unpartitioned stream can give ordering, but the moment you add a second
consumer for throughput you lose it, and there is no way around this
without a partitioning key. This is not a defect in the pattern, it is a
structural limit of parallel consumption.

When the consumer needs precise control over its own processing rate for
reasons the transport cannot express, for example a downstream system with a
hard concurrency limit of five in-flight requests that the messaging layer's
prefetch or concurrency settings cannot model cleanly. A Polling Consumer
that pulls exactly as much work as it can currently handle is often simpler
to reason about here than tuning push-based flow control.

When the operational and cost overhead of running message infrastructure,
brokers, dead letter queues, retry policies, monitoring, is not justified by
the volume or asynchrony of the work. A cron job calling a database query
directly is a better fit than a Kafka topic for a report that runs once a
night.

When exactly-once, in the strict sense of the event never being observed
twice by any downstream system, is a hard business requirement and the team
is not prepared to either build idempotent handlers or adopt a transactional
outbox and an exactly-once-capable transport such as Kafka's transactional
producer and consumer isolation level. Reaching for Event-Driven Consumer
without also solving this is the single most common production failure mode
for the pattern, covered in dimension 11.

## 5. Structure

The pattern has four participants.

**Producer.** The component that raises the event. It does not know who, if
anyone, is listening. In Hohpe and Woolf's vocabulary, the producer talks to
a Channel, never directly to a consumer.

**Channel.** The transport that carries the message from producer to
consumer, a queue, a topic, a stream, or an in-process event bus. The
channel is responsible for the delivery guarantee, at-most-once,
at-least-once, or exactly-once, and, where partitioned, for the ordering
guarantee within a partition.

**Message Endpoint, the Event-Driven Consumer itself.** The piece of code
registered against the channel. It exposes no public method a caller
invokes directly, its only interface is the handler function the runtime
calls back with a message. Hohpe and Woolf's Message Endpoint chapter treats
this as an adapter between the messaging system and the application's own
domain code, so the domain code stays free of transport-specific concerns.

**Runtime, the listener container.** The piece of infrastructure that
actually does the polling or the socket-level listening on the consumer's
behalf and turns raw bytes into a call to the handler. In Spring this is the
`ConcurrentMessageListenerContainer`, in AWS Lambda it is the event source
mapping, in raw Kafka client code it is the `poll()` loop the application
itself must write, which is why plain `KafkaConsumer` code looks
event-driven to the business logic even though, underneath, it is a hidden
polling consumer.

A fifth, optional but load-bearing participant appears in almost every real
deployment, the **Dead Letter Channel**, a side channel the runtime routes a
message to after it has failed processing some fixed number of times, so a
poison message cannot block the main channel forever.

## 6. ASCII structure diagram

```
+----------+        publish        +---------+
| Producer | ---------------------> | Channel |
+----------+                        +----+----+
                                          |
                                  deliver | (push or hidden poll)
                                          v
                              +--------------------+
                              |  Runtime / Listener |
                              |     Container       |
                              +----------+-----------+
                                         |
                                calls    | handler(message)
                                         v
                              +--------------------+
                              |  Message Endpoint   |
                              |  (Event-Driven      |
                              |   Consumer)         |
                              +----------+-----------+
                                         |
                            on repeated  | failure
                                         v
                              +--------------------+
                              |  Dead Letter        |
                              |  Channel             |
                              +--------------------+
```

## 7. Dynamics

The sequence below shows the successful path, then the failure path, for a
single message on a transport with at-least-once delivery and explicit
acknowledgement, the shape shared by SQS, RabbitMQ, and manually-acknowledged
Kafka consumers.

```
Producer          Channel           Runtime            Endpoint
   |                 |                 |                   |
   |--publish msg--->|                 |                   |
   |                 |--(msg becomes   |                   |
   |                 |   invisible or  |                   |
   |                 |   in-flight)--->|                   |
   |                 |                 |--call handler---->|
   |                 |                 |                   |--process
   |                 |                 |                   |  business
   |                 |                 |                   |  logic
   |                 |                 |<--ack/commit------|
   |                 |<--delete or-----|                   |
   |                 |   advance       |                   |
   |                 |   offset        |                   |
   |                 |                 |                   |

Failure path, handler throws or times out:

   |                 |                 |--call handler---->|
   |                 |                 |                   |--throws
   |                 |                 |<--no ack----------|
   |                 |                 |                   |
   |          (visibility timeout / redelivery timer expires)
   |                 |                 |                   |
   |                 |--message visible again-------------->|
   |                 |                 |--call handler---->| (retry N)
   |                 |                 |                   |--throws again
   |                 |                 |                   |
   |          (retry count exceeds threshold)
   |                 |                 |                   |
   |                 |==> Dead Letter Channel               |
```

AWS documents exactly this redelivery mechanism for SQS. If a consumer does
not process and delete a message before the visibility timeout expires, the
message becomes visible again in the queue and can be retrieved by the same
or a different consumer for another processing attempt (AWS, Amazon SQS
visibility timeout, verified 2026-08-02, URL above). This is the mechanical
reason at-least-once delivery, not exactly-once, is the default guarantee
almost every event-driven consumer must design for.

## 8. Implementation variants

**Framework-managed listener.** Spring's `@KafkaListener` and
`@RabbitListener` annotations, and Jakarta EE's `@MessageDriven` beans, are
the most common production shape. The framework owns the poll loop or the
socket connection, manages a thread pool, and calls the annotated method
with a deserialized payload. Spring's own reference documentation states
that the annotation wraps the bean method in a
`MessagingMessageListenerAdapter` configured with features such as type
conversion, and that enabling it requires `@EnableKafka` plus a registered
`ConcurrentKafkaListenerContainerFactory` (Spring, Receiving Messages,
Spring for Apache Kafka reference,
docs.spring.io/spring-kafka/reference/kafka/receiving-messages/listener-annotation.html,
verified 2026-08-02). This variant trades some control over polling
internals for a large reduction in boilerplate.

**Serverless event source mapping.** AWS Lambda, Azure Functions, and
Cloudflare Queues consumers all offer a shape where the platform itself is
the runtime participant, the developer writes only the handler function and
declares which queue or stream triggers it. The platform manages scaling the
number of concurrent invocations, batching, and, for AWS Lambda consuming
SQS, partial batch failure reporting so only the failed items in a batch are
retried rather than the whole batch.

**Reactive streams subscriber.** In systems built on Project Reactor,
RxJava, or the Java Flow API, the consumer implements `Subscriber.onNext`,
which the runtime calls per event, but the subscriber also calls
`request(n)` to tell the publisher how many events it is prepared to receive
next, folding explicit backpressure into the event-driven shape rather than
treating it as an afterthought.

**Raw client poll loop wrapped to look event-driven.** Hand-written Kafka
consumer code using the plain `KafkaConsumer` client calls `poll()` in an
explicit loop, which is technically a Polling Consumer at the wire level,
but application teams almost always wrap that loop in a small class exposing
an `onMessage(record)` callback to the rest of the codebase, so from every
other part of the system's point of view it behaves as an Event-Driven
Consumer. This is the honest middle ground, many real systems described as
event-driven are event-driven at the application boundary and polling at
the transport boundary.

**Database change stream, CDC consumer.** Debezium and native database
change-data-capture streams, Postgres logical replication, DynamoDB Streams,
turn row-level writes into an event stream a consumer subscribes to, which
is structurally identical to a message-queue Event-Driven Consumer, the
channel is simply a replication log rather than a broker topic.

## 9. Known production uses

**Confluent's Kafka client documentation** describes the consumer group
mechanism used to build event-driven consumption at scale across thousands
of production Kafka deployments. A consumer group is defined as a set of
consumers that cooperate to consume data from some topics, and when
consumers join a group, the partitions of all the topics are divided among
the consumers in the group, a rebalancing mechanism coordinated by a broker
acting as group coordinator (Confluent, Kafka Consumer,
docs.confluent.io/platform/current/clients/consumer.html, verified
2026-08-02). This is the reference implementation most engineers who have
touched Kafka have interacted with directly.

**Spring for Apache Kafka's `@KafkaListener`** is documented and shipped as
part of the Spring ecosystem, one of the most widely deployed enterprise
Java integration layers, and its reference page shows the exact
annotation-driven Event-Driven Consumer shape, including manual
acknowledgement via an `Acknowledgment` parameter set to
`ackMode = "MANUAL"` (Spring, Receiving Messages, Spring for Apache Kafka
reference, URL above, verified 2026-08-02).

**Amazon SQS with AWS Lambda event source mappings** is a named, documented
serverless Event-Driven Consumer used across AWS's own guidance for
decoupled architectures, where the visibility timeout mechanism AWS
documents is the concrete redelivery guarantee the pattern's failure path
in dimension 7 depends on (AWS, Amazon SQS visibility timeout, URL above,
verified 2026-08-02).

**Enterprise Integration Patterns' own worked example**, the Competing
Consumers pattern page, illustrates the pattern's relative, Event-Driven
Consumer plus multiple listeners on one channel, using Apache Kafka as its
modern reference example, noting that the example using Apache Kafka
illustrates how modern implementations partition channels across consumers
to manage distribution and maintain ordering guarantees where needed (Hohpe
and Woolf, Competing Consumers,
enterpriseintegrationpatterns.com/patterns/messaging/CompetingConsumers.html,
verified 2026-08-02).

## 10. Consequences

Positive. Lower latency between an event occurring and a reaction to it,
compared to any fixed-interval polling consumer, because delivery is pushed
or triggered rather than waited for. Decoupling of producer from consumer,
the producer does not need to know how many consumers exist or what they
do. Natural fit for horizontal scaling via Competing Consumers, adding a
consumer instance increases throughput without any code change on the
producer side. Resource efficiency at idle, an event-driven consumer that is
not receiving events does not burn CPU cycles asking, unlike a tight
polling loop.

Negative. At-least-once delivery is the default guarantee on almost every
mainstream transport, which pushes the burden of idempotency onto every
handler, a cost that is easy to forget until duplicate processing causes a
real incident. Debugging is harder, a stack trace for a synchronous call
shows the whole call chain, an event-driven chain across three services
shows three separate stack traces in three separate logs that a human has
to correlate by request or trace identifier. Backpressure has to be
designed in explicitly, an event-driven consumer with no concurrency limit
will accept work faster than it can process it the moment traffic spikes,
and without a limit that shows up as unbounded memory growth or cascading
failure in downstream calls. Operational surface area grows, a message
broker, a dead letter queue, retry policy, and monitoring for consumer lag
are all now part of what the team runs and pages on, where a plain function
call had none of that.

## 11. Failure modes and misuse

**Poison message loop.** Symptom. Consumer lag on one partition grows
unbounded, CPU on the consumer stays high, and the same message ID
reappears in logs every few seconds. Cause. A message that always throws on
processing, a malformed payload or a bug triggered only by that message's
specific data, gets redelivered every time its visibility timeout or
redelivery interval expires, reprocessed, and thrown again, forever,
because no maximum retry count routes it to a dead letter channel. Fix.
Configure a maximum receive count with a dead letter queue, the standard
mitigation AWS documents for managing messages that fail multiple
processing attempts (AWS, Amazon SQS visibility timeout, URL above,
verified 2026-08-02), or the equivalent max delivery attempts setting on
any other transport.

**Duplicate side effects from at-least-once redelivery.** Symptom. A
customer is charged twice, or receives two identical emails, for one
logical event. Cause. The handler performed a non-idempotent side effect,
for example an unconditional insert or an unconditional call to a payment
gateway, and the same message was delivered twice because the first
delivery's acknowledgement was lost, delayed past the visibility timeout,
or the consumer crashed after completing work but before acking. Fix. Make
the handler idempotent, typically by recording a processed-message
identifier in the same transaction as the side effect, an idempotency key
check before charging a card, an upsert instead of an insert, rather than
trying to eliminate redelivery, which is not eliminable on an
at-least-once transport by design.

**Silent rebalance storms.** Symptom. Kafka consumer group throughput drops
sharply and intermittently, with log lines showing repeated group joins and
partition revocations, sometimes correlated with garbage collection
pauses. Cause. A consumer's processing time between polls exceeds
`max.poll.interval.ms`, so the broker's group coordinator considers the
consumer dead and triggers a rebalance, which stops all consumers in the
group briefly while partitions are reassigned, and if the slow consumer is
still alive it rejoins and triggers another rebalance shortly after. Fix.
Either shorten per-poll processing time by moving heavy work off the poll
thread, or raise `max.poll.interval.ms` and lower `max.poll.records` so
each poll batch fits comfortably inside the interval, and where the client
library supports it, adopt the cooperative sticky assignor rather than the
eager range assignor, since Confluent documents the sticky and cooperative
strategies as specifically reducing the disruption of rebalancing
(Confluent, Kafka Consumer, URL above, verified 2026-08-02).

**Unbounded concurrency under a traffic spike.** Symptom. Downstream
database connection pool exhaustion or a spike in 5xx errors from a
rate-limited third-party API, correlated exactly with a burst of inbound
events. Cause. An event-driven consumer configured with no concurrency
ceiling, or a serverless event source mapping with reserved concurrency set
too high, scales the number of simultaneous handler invocations to match
the burst rather than the downstream system's real capacity. Fix. Bound
consumer concurrency explicitly, matched to the downstream system's tested
capacity, and prefer a transport or platform feature that supports this
directly, for example Lambda's reserved concurrency on an SQS event source
mapping, over trying to throttle inside application code after the runtime
has already started N concurrent invocations.

**Ordering assumed but not guaranteed.** Symptom. A state machine
transitions into an impossible state, for example an order-shipped event is
processed before the corresponding order-placed event for the same order.
Cause. The events were produced to an unpartitioned topic, or to a topic
partitioned by a key other than order ID, so two related events landed on
different partitions and were processed by different consumer instances
with no ordering relationship between them. Fix. Partition the channel by
the business key whose events must stay ordered relative to each other, and
treat ordering as a property that exists only within a single partition,
never across the whole topic. This fix is judgement grounded directly in
how Kafka's own partition assignment works (Confluent, Kafka Consumer, URL
above).

## 12. Trade-off matrix

| Force | Event-Driven Consumer | Polling Consumer | Request-Reply |
|---|---|---|---|
| Latency to first reaction | Low, near-immediate on push transports | Bounded by poll interval, adds up to one interval of delay | Lowest, synchronous |
| Idle resource cost | Low, no wasted cycles when quiet | Higher, fixed poll cost regardless of traffic | None, no standing connection needed between calls |
| Caller blocking | Never, producer continues immediately | Never, but consumer itself is busy-waiting | Always, caller waits for the response |
| Backpressure control | Must be added explicitly, easy to omit | Naturally self-limited by poll rate | Naturally limited by concurrent call count |
| Ordering guarantee | Only within a partition or single queue | Same as event-driven, transport-dependent | Trivial, one call at a time per caller |
| Operational overhead | High, broker, DLQ, lag monitoring, retry policy | Moderate, still needs a scheduler and idempotency | Low, standard HTTP or RPC tooling covers most needs |
| Fit for fan-out to many consumers | Strong, Publish-Subscribe Channel or Competing Consumers layer naturally on top | Weak, each poller independently queries the source | Weak, one caller talks to one callee |

## 13. Related and incompatible patterns

**Competing Consumers.** The scaling layer on top of Event-Driven Consumer,
several consumer instances all listening on the same channel so that
throughput increases without changing the producer, at the cost of ordering
across instances (Hohpe and Woolf, Competing Consumers, URL above).

**Polling Consumer.** The sibling pattern from the same Message Endpoint
chapter, used instead of Event-Driven Consumer specifically when the
consumer needs to control the pace of its own work rather than accept
delivery on the transport's schedule.

**Publish-Subscribe Channel.** Often paired with Event-Driven Consumer when
more than one distinct consumer, doing different work, needs to react to
the same event, as opposed to Competing Consumers where many identical
consumer instances share one workload.

**Message Endpoint.** The parent abstraction, Event-Driven Consumer is one
concrete kind of Message Endpoint, the other being the Polling Consumer.

**Dead Letter Channel.** A near-mandatory companion, not optional in
practice, since without it a poison message misuse case, dimension 11, has
no mechanism to stop retrying.

**Saga.** Chains of Event-Driven Consumers reacting to each other's events
are the most common implementation shape for a choreography-based Saga,
where each service's event-driven consumer both reacts to a prior step's
event and publishes the event for the next step, with no central
orchestrator.

**Transactional Outbox.** Frequently required alongside Event-Driven
Consumer on the producer side, to guarantee the event that triggers the
consumer is actually published if and only if the producer's own database
transaction committed, closing the dual-write gap that would otherwise let
a producer commit its own state change while failing to publish the event,
or the reverse.

No pattern in this catalog is structurally incompatible with Event-Driven
Consumer, it composes with almost everything in the Messaging family, the
tension in dimension 3 and 4 is about when to choose it, not about it
conflicting with another named pattern.

## 14. Refactoring path in and out

**Introducing it.** Start from a synchronous call or a polling loop that
already works. First, identify the exact business event the call
represents, name it precisely, an OrderPlaced event, not a generic
OrderUpdated. Second, introduce a channel, a topic or queue, and change the
producer to publish that named event after its own transaction commits,
ideally via a transactional outbox so publishing cannot silently fail
relative to the producer's own state change. Third, write the consumer's
handler as a small, pure function of the event payload, with no hidden
dependency on the order events arrive in unless that order is guaranteed by
the channel's partitioning. Fourth, make the handler idempotent before the
consumer goes live, not after the first duplicate-processing incident, by
recording a processed-event identifier as part of the same transaction as
the handler's side effect. Fifth, wire the consumer into a listener
container or event source mapping rather than hand-writing a poll loop,
unless the team has a specific reason the framework's container does not
fit. Sixth, configure a maximum retry count and a dead letter channel
before the first production deployment, this is not a later hardening
step, a poison message misuse case is common enough in the first weeks
that skipping this is a near-certain incident.

**Removing it.** An Event-Driven Consumer earns its place through
decoupling and throughput. It stops earning its place when the consumer has
become the only consumer of the event, will remain the only consumer, and
the added latency of a broker round trip is now pure overhead compared to
a direct call. To remove it, first confirm via the broker's own metrics,
not assumption, that no other consumer group is subscribed to the topic.
Second, replace the publish-and-forget call with a direct synchronous call
or a simple in-process function call. Third, decommission the topic and its
dead letter queue only after a monitoring window confirms no consumer lag
remains and no unexpected downstream system was silently relying on the
event. Do not skip the monitoring window, an event topic that looks unused
from the producer's side can still have an operational or analytics
consumer nobody on the current team remembers.

## 15. Testing and verification

Event-Driven Consumer code separates cleanly into two testable halves. The
handler function itself, taking a deserialized message and producing side
effects, is a pure enough unit that it should be tested with ordinary unit
tests, no broker required, feeding it hand-constructed message payloads
including malformed ones, and asserting on the side effects it produces or
the exceptions it raises. This is the majority of the useful test coverage
and it is easy to write because the handler has no dependency on the
transport once it has been handed a message.

The harder half is the wiring, does the listener container actually invoke
the handler for a real message on a real or embedded broker, does
acknowledgement happen at the right point, does a thrown exception actually
trigger redelivery rather than silently swallowing the message. For this,
prefer an embedded or ephemeral broker over mocking the client library,
Kafka's `EmbeddedKafkaBroker`, used by Spring Kafka's own test support, and
LocalStack's SQS emulation are the standard tools, because a mock of a
`KafkaConsumer` or an SQS client can silently drift from the real client's
actual acknowledgement and redelivery semantics, which is exactly the
behavior this half of the test exists to verify.

Idempotency deserves its own explicit test. Publish the same message twice,
or deliver it to the handler twice, and assert the observable side effect
happened exactly once, this test should exist for every handler with a
non-idempotent-looking side effect, and its absence is one of the most
common gaps found in a code review of event-driven consumer code.

Contract or schema tests on the message payload itself, checked against a
schema registry where one exists, catch the class of failure where a
producer changes a field's shape and every consumer breaks at runtime
instead of at build or deploy time. This is a test double concern worth
naming separately from the handler unit tests above, because a passing
handler unit test tells you nothing about whether the payload shape it was
tested against still matches what production actually sends.

## 16. Observability signals

Consumer lag, the difference between the latest offset or sequence number
produced and the offset the consumer has committed, is the single most
important signal, and it should be alerted on, not only dashboarded,
because a consumer that is up but falling behind looks healthy on a naive
liveness check while silently accumulating a growing backlog. Confluent's
own consumer documentation frames the committed offset as the tracked
position a consumer has processed up to, which is exactly the number lag is
computed from (Confluent, Kafka Consumer, URL above, verified 2026-08-02).

Dead letter queue depth and dead letter arrival rate, a nonzero but flat
DLQ depth over a long window usually means a handful of genuinely bad
messages that need manual triage, a rising DLQ arrival rate usually means a
code regression in the handler and should page someone, not wait for a
weekly report.

Redelivery count per message, or an equivalent retry counter, surfaces the
poison message failure mode from dimension 11 before it reaches the dead
letter threshold, a message redelivered three times is a leading indicator,
a message redelivered thirty times and still in the main queue is an
incident.

Handler processing time distribution, specifically the tail, p99 and p999,
correlated against `max.poll.interval.ms` or the equivalent visibility
timeout, because the rebalance storm failure mode in dimension 11 is caused
precisely by processing time exceeding that configured window, and a
dashboard that only shows the median hides the exact tail behavior that
triggers it.

A healthy instance on a dashboard shows lag near zero and stable, DLQ depth
flat at or near zero, redelivery counts mostly at zero with rare small
nonzero spikes, and p99 processing time comfortably inside the configured
poll interval or visibility timeout with headroom. A failing instance shows
lag trending upward without recovering, a DLQ depth that is climbing
rather than flat, and a processing time p99 that is close to or exceeding
the timeout window.

## 17. Security and privacy implications

An Event-Driven Consumer widens the blast radius of a compromised message
producer, because the consumer's handler will execute for anything
published to a channel it trusts, so authentication and authorization at
the channel level, who is allowed to publish to this topic, matters as much
as authorization on any API endpoint, and is easy to under-invest in
precisely because there is no HTTP request to point an API gateway at.

Message payloads containing personal data inherit every obligation the
organization already has around that data, and a dead letter queue is a
frequently overlooked storage location for that same sensitive payload, a
DLQ retaining a message with personal data for weeks while nobody looks at
it is a real and common data-retention gap, since DLQ retention policy is
often set once at creation and never revisited.

Deserialization of an untrusted or attacker-influenced payload is a
concrete attack surface, a consumer that deserializes a message into a
class using a polymorphic or type-based deserializer without an allowlist
of expected types is vulnerable to the same class of deserialization
attacks documented for other RPC and serialization mechanisms. This is
analytical judgement, not a claim about any specific transport, and applies
regardless of which broker or queue is used.

Where the pattern is genuinely quiet, the pattern itself does not encrypt
or fail to encrypt anything, transport-level encryption in transit and
at-rest encryption of the underlying broker storage are properties of the
specific broker deployment, not of the Event-Driven Consumer pattern, and
should be verified against that broker's own security documentation rather
than assumed from this entry.

## 18. References

Hohpe, Gregor and Woolf, Bobby. Enterprise Integration Patterns, Designing,
Building, and Deploying Messaging Solutions. Addison-Wesley, 2003. Message
Endpoints chapter, Event-Driven Consumer and Polling Consumer sections.

Hohpe, Gregor and Woolf, Bobby. Competing Consumers.
https://www.enterpriseintegrationpatterns.com/patterns/messaging/CompetingConsumers.html,
verified 2026-08-02.

Confluent. Kafka Consumer.
https://docs.confluent.io/platform/current/clients/consumer.html, verified
2026-08-02.

Amazon Web Services. Amazon SQS visibility timeout.
https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html,
verified 2026-08-02.

Spring. Receiving Messages, Spring for Apache Kafka reference documentation.
https://docs.spring.io/spring-kafka/reference/kafka/receiving-messages/listener-annotation.html,
verified 2026-08-02.

## Code examples

### TypeScript, a bounded-concurrency SQS-style consumer

```typescript
type Message = { id: string; body: string; receiveCount: number };

interface Queue {
  receive(max: number): Promise<Message[]>;
  ack(id: string): Promise<void>;
  deadLetter(id: string, body: string): Promise<void>;
}

const MAX_RETRIES = 3;
const CONCURRENCY = 4;

async function handle(msg: Message): Promise<void> {
  if (msg.body === "boom") {
    throw new Error("simulated failure");
  }
  console.log(`processed ${msg.id}, body ${msg.body}`);
}

async function runConsumer(queue: Queue): Promise<void> {
  const messages = await queue.receive(10);
  const lanes: Promise<void>[][] = Array.from({ length: CONCURRENCY }, () => []);
  messages.forEach((m, i) => {
    lanes[i % CONCURRENCY].push(processOne(queue, m));
  });
  await Promise.all(lanes.map((lane) => Promise.all(lane)));
}

async function processOne(queue: Queue, msg: Message): Promise<void> {
  try {
    await handle(msg);
    await queue.ack(msg.id);
  } catch (err) {
    if (msg.receiveCount >= MAX_RETRIES) {
      await queue.deadLetter(msg.id, msg.body);
    }
    // no ack, message becomes visible again for redelivery
  }
}

class InMemoryQueue implements Queue {
  private items: Message[] = [
    { id: "1", body: "order-placed", receiveCount: 1 },
    { id: "2", body: "boom", receiveCount: 4 },
  ];
  async receive(max: number) {
    return this.items.splice(0, max);
  }
  async ack(id: string) {
    console.log(`ack ${id}`);
  }
  async deadLetter(id: string, body: string) {
    console.log(`dead-lettered ${id}, body ${body}`);
  }
}

runConsumer(new InMemoryQueue());
```

### Python, an idempotent event-driven handler with a processed-id guard

```python
from dataclasses import dataclass
from typing import Callable

processed_ids: set[str] = set()


@dataclass
class Event:
    event_id: str
    kind: str
    payload: dict


def charge_card_once(order_id: str, amount: int) -> None:
    print(f"charged order {order_id} for {amount} cents")


def handle_order_placed(event: Event) -> None:
    if event.event_id in processed_ids:
        print(f"skipping duplicate delivery of {event.event_id}")
        return
    charge_card_once(event.payload["order_id"], event.payload["amount"])
    processed_ids.add(event.event_id)


def run_consumer(events: list[Event], handler: Callable[[Event], None]) -> None:
    for event in events:
        try:
            handler(event)
        except Exception as exc:
            print(f"handler failed for {event.event_id}, error {exc}")


if __name__ == "__main__":
    stream = [
        Event("evt-1", "order.placed", {"order_id": "o-1", "amount": 4200}),
        Event("evt-1", "order.placed", {"order_id": "o-1", "amount": 4200}),
    ]
    run_consumer(stream, handle_order_placed)
```

### Go, a partitioned worker pool preserving per-key order

```go
package main

import (
	"fmt"
	"sync"
)

type Event struct {
	Key     string
	ID      string
	Payload string
}

func hashKey(key string) int {
	h := 0
	for _, c := range key {
		h = h*31 + int(c)
	}
	if h < 0 {
		h = -h
	}
	return h
}

func handle(e Event) {
	fmt.Printf("processed key=%s id=%s payload=%s\n", e.Key, e.ID, e.Payload)
}

func runConsumer(events []Event, laneCount int) {
	lanes := make([]chan Event, laneCount)
	for i := range lanes {
		lanes[i] = make(chan Event, 16)
	}

	var wg sync.WaitGroup
	for i, lane := range lanes {
		wg.Add(1)
		go func(id int, ch chan Event) {
			defer wg.Done()
			for e := range ch {
				handle(e)
			}
		}(i, lane)
	}

	for _, e := range events {
		lane := hashKey(e.Key) % laneCount
		lanes[lane] <- e
	}
	for _, lane := range lanes {
		close(lane)
	}
	wg.Wait()
}

func main() {
	events := []Event{
		{Key: "order-1", ID: "e1", Payload: "placed"},
		{Key: "order-1", ID: "e2", Payload: "shipped"},
		{Key: "order-2", ID: "e3", Payload: "placed"},
	}
	runConsumer(events, 2)
}
```

### Rust, a bounded-channel consumer with a dead-letter path

```rust
use std::sync::mpsc;
use std::thread;

#[derive(Clone)]
struct Message {
    id: String,
    body: String,
}

fn handle(msg: &Message) -> Result<(), String> {
    if msg.body == "boom" {
        return Err(format!("simulated failure for {}", msg.id));
    }
    println!("processed {} body {}", msg.id, msg.body);
    Ok(())
}

fn run_consumer(messages: Vec<Message>) {
    let (dlq_tx, dlq_rx) = mpsc::channel::<Message>();

    let dlq_handle = thread::spawn(move || {
        for dead in dlq_rx {
            println!("dead-lettered {} body {}", dead.id, dead.body);
        }
    });

    for msg in messages {
        match handle(&msg) {
            Ok(()) => {}
            Err(reason) => {
                println!("handler error, routing to dead letter, reason {}", reason);
                dlq_tx.send(msg).expect("dlq channel closed");
            }
        }
    }

    drop(dlq_tx);
    dlq_handle.join().expect("dlq thread panicked");
}

fn main() {
    let messages = vec![
        Message { id: "1".into(), body: "order-placed".into() },
        Message { id: "2".into(), body: "boom".into() },
    ];
    run_consumer(messages);
}
```

All four samples were run locally against the toolchains listed below and
produced the expected output, including the expected dead-letter and
duplicate-skip lines.

Java and Swift are omitted for this entry. The pattern is not meaningfully
more idiomatic in either language than in the four above, an Event-Driven
Consumer in Java is the same `@KafkaListener` or `@JmsListener` shape shown
in dimension 8, and in Swift there is no dominant production messaging
client whose idioms differ enough from the general shape to be worth a
fifth sample here.
