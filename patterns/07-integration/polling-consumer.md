---
name: Polling Consumer
slug: polling-consumer
family: 07-integration
category: Messaging Endpoints
aliases: [Pull Consumer, Synchronous Receiver, Polled Endpoint]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [event-driven-consumer, message-channel, competing-consumers, guaranteed-delivery, dead-letter-channel, throttling, circuit-breaker]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Polling Consumer. Gregor Hohpe and Bobby Woolf named and
catalogued it in *Enterprise Integration Patterns* (Addison-Wesley, 2003) as
one of the two message consumer patterns, the other being Event-Driven
Consumer. The book's companion site states the pattern plainly, calling a
Polling Consumer "an object that an application uses to receive messages by
explicitly requesting them" (Hohpe and Woolf, Enterprise Integration Patterns,
"Polling Consumer", verified 2026-08-02,
https://www.enterpriseintegrationpatterns.com/patterns/messaging/PollingConsumer.html).

The pattern is also called Pull Consumer in queueing literature that
distinguishes push delivery from pull retrieval, and Synchronous Receiver in
older messaging texts because the calling thread blocks on the receive call
until a message arrives or a timeout expires. Spring Integration ships a
concrete class named `PollingConsumer` that implements exactly this role
against a `PollableChannel` (Spring Integration Reference Documentation,
"Message Endpoints", section on `PollingConsumer`, verified 2026-08-02,
https://docs.spring.io/spring-integration/reference/endpoint.html). Apache
Kafka's client API applies the same idea at the protocol level through its
`poll()` method on `KafkaConsumer`, and the Kafka project explicitly frames
consumer liveness around how often that method is called (Apache Kafka 4.0
Javadoc, `KafkaConsumer`, verified 2026-08-02,
https://kafka.apache.org/40/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html).
Amazon SQS's `ReceiveMessage` API is a third, independent lineage of the same
pattern, arriving from cloud queueing rather than from the EIP book (AWS SQS
Developer Guide, "Amazon SQS short and long polling", verified 2026-08-02,
https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html).

The name is not contested. Every source above agrees on what distinguishes a
Polling Consumer from an Event-Driven Consumer. the consumer, not the
messaging system, decides when a receive attempt happens.

## 2. Problem and context

An application needs to consume messages from a channel, a queue, a topic
partition, or any buffered source of work items, but it needs to control the
timing and the volume of consumption rather than being driven by the
producer's rate. A naive Event-Driven Consumer, where the messaging
infrastructure invokes a callback the instant a message arrives, hands timing
control to whichever component happens to be fastest at producing work. That
is fine when the consumer's processing cost is small and uniform. It becomes a
liability the moment the consumer's processing cost varies, the consumer needs
to batch several messages into one unit of work, the consumer needs to pause
entirely during a maintenance window or a downstream outage, or the consumer
runs on a platform (a cron job, a serverless function invocation, a
batch-oriented worker fleet) that has no long-lived thread available to sit in
a callback and cannot register an inbound listener at all.

The concrete situation a reader will recognize. a nightly batch job needs to
drain a queue of pending exports and stop, a mobile client wants to check for
new notifications every 30 seconds while backgrounded rather than hold an open
socket that drains battery, a serverless function on a platform that bills per
invocation and has no persistent process cannot host an event-driven listener
at all so it must be invoked on a schedule and pull whatever work exists, and a
consumer group in Kafka needs to control exactly how many records it accepts
per pass so it can commit offsets in bounded batches rather than being flooded
by the broker. In each case the context is the same. work exists in a
retrievable, addressable channel, and the consumer, not the producer or the
broker, needs the authority over when and how much it takes.

## 3. Forces

- **Control versus responsiveness.** The consumer gains full control over
  timing, batch size, and backpressure, at the cost of latency between a
  message arriving and the consumer noticing it. An Event-Driven Consumer
  notices immediately, a Polling Consumer notices only at its next poll.
- **Resource efficiency versus wasted work.** A poll that finds nothing is a
  round trip that accomplished nothing. Poll too often and the consumer spends
  cycles, network calls, and, on metered infrastructure such as SQS, real
  money on empty responses. Poll too rarely and messages sit unprocessed,
  inflating end-to-end latency.
- **Thread and connection cost versus simplicity.** A Polling Consumer built
  on a dedicated polling thread ties up a thread or a scheduled task slot for
  the life of the consumer. An Event-Driven Consumer can, depending on the
  transport, avoid that dedicated thread by relying on the transport's own
  I/O event loop. This is a real cost at scale, since a thousand polling
  consumers is a thousand blocked or scheduled threads unless the polling
  loop is written asynchronously.
- **Batch efficiency versus fairness and staleness.** Pulling many messages
  per poll amortizes the fixed cost of a round trip across more work, which is
  why Kafka's `max.poll.records` and Spring Integration's
  `maxMessagesPerPoll` both exist as knobs (Spring Integration Reference
  Documentation, "Message Endpoints", verified 2026-08-02,
  https://docs.spring.io/spring-integration/reference/endpoint.html). Large
  batches also mean a single slow consumer holds a large chunk of work
  without visibility into individual message age, and a crash mid-batch can
  lose or duplicate more work than a smaller batch would.
- **Operability and cognitive load.** A polling loop with a fixed interval is
  trivial to reason about and to test deterministically, since advancing a
  clock and asserting a poll happened is enough. An event-driven callback
  chain is harder to test deterministically because the trigger is external
  and asynchronous. This favors Polling Consumer for testability and for
  on-call operators who need to predict exactly when the next attempt to
  notice new work will occur.
- **Coupling to transport capability.** Not every channel technology supports
  push delivery at all. A polling loop is the only option against a plain
  database table used as a queue, a filesystem directory, or an HTTP resource
  with no webhook support, so in that context the choice of Polling Consumer
  is really the absence of an alternative.

The pattern favors control, testability, and universality across transports.
It sacrifices best-case latency and, when implemented carelessly, wastes
resources on empty polls. Long polling, covered under implementation
variants, is the classic mitigation for the latency and waste sacrifice
without abandoning consumer-side control.

## 4. Applicability and non-applicability

Reach for Polling Consumer when.

- The channel technology has no push mechanism, such as a database table, a
  filesystem drop folder, an HTTP resource with no webhook, or a legacy
  mainframe queue accessed only through a synchronous API.
- The runtime has no facility to host a long-lived listener, such as a
  scheduled serverless function, a cron-triggered batch job, or a CLI tool
  invoked on demand.
- The consumer must control batch size and cadence deliberately, for example
  draining exactly N records per invocation to bound memory or to match a
  downstream system's rate limit.
- The consumer needs to be paused, throttled, or backed off dynamically
  without unregistering and re-registering a listener, which is often more
  awkward with an event-driven transport than simply not calling `poll()`.
- Deterministic, clock-driven testing matters more than shaving milliseconds
  of latency, because a polling loop is trivially simulated with a fake
  clock while a push-based callback chain usually requires a real or
  simulated transport.

Do NOT reach for Polling Consumer when.

- The channel supports efficient push delivery and the workload is latency
  sensitive, for example a user-facing chat message or a trading signal,
  where even a short polling interval introduces avoidable delay that an
  Event-Driven Consumer would not have.
- The expected message rate is low relative to the polling interval, because
  most polls will find nothing and the pattern becomes almost pure waste.
  An Event-Driven Consumer or a push notification is strictly cheaper here.
- The platform bills per API call or per poll round trip and messages are
  infrequent. This is the exact case Amazon SQS built long polling to
  mitigate, because unmitigated short polling against a lightly loaded queue
  produces many billed, empty `ReceiveMessage` calls (AWS SQS Developer
  Guide, verified 2026-08-02,
  https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html).
- The consumer needs sub-second reactivity across a fleet with hundreds of
  independent sources, where the aggregate polling traffic itself becomes a
  scalability problem better solved by a push-based fan-out or a message
  broker's own subscription mechanism.
- The team cannot tune the polling interval independently per environment,
  and a single hardcoded interval is either too aggressive for a low-traffic
  staging environment or too slow for a high-traffic production one. This is
  a maintenance trap rather than a hard non-applicability, but it recurs
  often enough to name here.

## 5. Structure

- **Source** is the addressable location that holds pending work, whether a
  message channel, a queue, a topic partition, a database table, or an HTTP
  resource. It does not initiate contact with the consumer, it only answers
  when asked.
- **Polling Consumer** is the active participant. It owns the decision of
  when to call the source, how many items to request per call, how long to
  wait for a response before giving up, and what to do when the source
  returns nothing.
- **Trigger** decides the cadence between poll attempts. This can be a fixed
  interval, a cron expression, an adaptive backoff schedule, or an external
  scheduler invoking the consumer as a whole, as with a serverless function
  triggered on a timer. Spring Integration names this participant
  explicitly as the `org.springframework.scheduling.Trigger` interface, with
  `PeriodicTrigger` and `CronTrigger` as the two built-in implementations
  (Spring Integration Reference Documentation, verified 2026-08-02,
  https://docs.spring.io/spring-integration/reference/endpoint.html).
- **Receive Timeout** bounds how long a single poll call is willing to block
  waiting for at least one item before returning empty. A timeout of zero is
  a non-blocking check, a large timeout implements long polling.
- **Batch Limit** bounds how many items a single successful poll may return,
  protecting the consumer from being handed more work in one call than it can
  safely process before the next liveness checkpoint.
- **Offset or Acknowledgment Tracker** records how far into the source the
  consumer has progressed, so a restarted consumer resumes rather than
  reprocessing or skipping. This participant is what turns a bare polling
  loop into a reliable one, and it composes directly with Guaranteed Delivery.

## 6. ASCII structure diagram

```
+-----------------------------------+
| Trigger (interval, cron, backoff) |
+-----------------------------------+
     | schedules next call
     v
+------------------+
| Polling Consumer |
+------------------+
     | poll(timeout, limit)
     v
+---------------------------------------+
| Source (Channel, Queue, Topic, Table) |
+---------------------------------------+
     | returns items[0..limit], or empty
     v
(back to Polling Consumer)

Polling Consumer also updates, after each successfully
handled batch:

+---------------------------------------------+
| Offset / Ack Tracker (last processed index) |
+---------------------------------------------+
```

## 7. Dynamics

```
Trigger        PollingConsumer          Source            Handler         Tracker
  |                  |                     |                  |              |
  |--fires---------->|                     |                  |              |
  |                  |--poll(timeout,limit)>|                  |              |
  |                  |                     |--check items------>|             |
  |                  |<--items[0..n] or----|                  |              |
  |                  |    empty            |                  |              |
  |                  |                     |                  |              |
  |    [items empty] |                     |                  |              |
  |                  |--no-op, wait for next trigger---------->|             |
  |                  |                     |                  |              |
  |    [items present]                     |                  |              |
  |                  |--dispatch item(s)------------------------>|            |
  |                  |                     |                  |--process---->|
  |                  |                     |                  |<--result-----|
  |                  |<---handler result---------------------|              |
  |                  |--record progress-------------------------------------->|
  |                  |                     |                  |              |
  |<--schedule next--|                     |                  |              |
  |    poll          |                     |                  |              |
```

At runtime the loop is straightforward. the Trigger fires, the consumer
issues one poll call bounded by a timeout and a batch limit, the source
either returns nothing, in which case the consumer idles until the next
trigger, or returns one or more items, in which case the consumer dispatches
them to a handler, waits for the outcome, and only then commits the progress
marker. The critical ordering decision, visible in the diagram, is that
progress is recorded after successful handling, never before. Recording
progress before handling risks silently dropping a message on a crash between
poll and processing. Recording it after risks reprocessing the same message
on a crash between processing and commit, which is why Polling Consumer
implementations are almost always paired with an idempotent handler or an
at-least-once delivery contract rather than an exactly-once guarantee by
default.

## 8. Implementation variants

**Fixed-interval short polling.** The consumer sleeps for a constant duration
between calls regardless of whether the previous call found work. Simple to
reason about, wasteful when traffic is bursty or sparse, and the default
behavior of Amazon SQS's `ReceiveMessage` when `WaitTimeSeconds` is zero (AWS
SQS Developer Guide, verified 2026-08-02,
https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html).

**Long polling.** The consumer's poll call itself blocks on the server side
for up to a bounded maximum, returning as soon as at least one item is
available or the timeout elapses, whichever comes first. This narrows the gap
between polling and event-driven latency while keeping the consumer in
control. Amazon SQS caps this at 20 seconds and documents it as reducing both
empty responses and cost (AWS SQS Developer Guide, verified 2026-08-02,
https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html).
Spring Integration achieves the same effect by combining a short trigger
interval with a long `receive-timeout`, and its own documentation frames this
explicitly as a technique to emulate event-driven behavior on polled sources
(Spring Integration Reference Documentation, verified 2026-08-02,
https://docs.spring.io/spring-integration/reference/endpoint.html).

**Batch-bounded polling.** The consumer requests up to N items per call and
processes the whole batch before polling again. Kafka's `KafkaConsumer.poll()`
is the canonical example. a single call can return many records, and the
consumer is expected to finish handling that batch and call `poll()` again
within `max.poll.interval.ms` or the broker will consider it dead and trigger
a rebalance, according to the client's own Javadoc, which states that "if you
don't call poll at least as frequently as the configured max interval, then
the client will proactively leave the group so that another consumer can take
over its partitions" (Apache Kafka 4.0 Javadoc, `KafkaConsumer`, verified
2026-08-02,
https://kafka.apache.org/40/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html).
This turns the batch size into a direct control point over liveness. a larger
batch gives the consumer more processing time per rebalance risk window, but
a slow handler on a large batch is exactly what trips the timeout.

**Adaptive or exponential backoff polling.** The interval between polls grows
when consecutive polls return nothing and shrinks back toward a minimum once
work reappears. This trades a small amount of added latency on the first
message after an idle period for a large reduction in wasted polls during
genuinely idle stretches, and it is the pattern most schedulers implicitly
recommend pairing with long polling rather than replacing it.

**Language-idiomatic shapes.** In languages with first-class async runtimes,
such as TypeScript with `async`/`await`, Go with goroutines and channels, or
Rust with `tokio`, the polling loop is usually written as an async task that
awaits a timer or a blocking receive call rather than a dedicated OS thread,
which removes the thread-cost force named in dimension 3 without changing the
pattern's shape. In a purely synchronous language or a scheduled-invocation
platform, the loop degenerates to a single poll-and-return per invocation,
with the external scheduler acting as the Trigger participant.

## 9. Known production uses

- **Amazon SQS `ReceiveMessage` with long polling.** SQS's own consumer API is
  a Polling Consumer by construction. clients call `ReceiveMessage`
  explicitly, and AWS documents both the default short-polling behavior and
  the long-polling variant with `WaitTimeSeconds` up to 20 seconds (AWS SQS
  Developer Guide, "Amazon SQS short and long polling", verified 2026-08-02,
  https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html).
- **Apache Kafka's `KafkaConsumer.poll()`.** The entire Kafka consumer client
  is built around an explicit poll loop. the client library does not push
  records to the application, and consumer liveness within a group is
  literally defined by how often the application calls `poll()` relative to
  `max.poll.interval.ms` (Apache Kafka 4.0 Javadoc, `KafkaConsumer`, verified
  2026-08-02,
  https://kafka.apache.org/40/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html).
- **Spring Integration's `PollingConsumer` endpoint.** Spring Integration
  ships a concrete `org.springframework.integration.endpoint.PollingConsumer`
  class that wraps a `PollableChannel` and a `Trigger`, distinct from its
  `EventDrivenConsumer` counterpart for `SubscribableChannel`, and its
  reference documentation describes the trigger, `maxMessagesPerPoll`, and
  `receiveTimeout` configuration surface in detail (Spring Integration
  Reference Documentation, "Message Endpoints", verified 2026-08-02,
  https://docs.spring.io/spring-integration/reference/endpoint.html).
- **RSS and Atom feed readers.** Feed aggregators poll a publisher's feed URL
  on a fixed or conditional-GET-driven interval because RSS and Atom are
  pull-only formats with no native push mechanism. This predates and is
  independent of the EIP catalog naming but is the same structural pattern
  applied over HTTP.

## 10. Consequences

Positive consequences.

- The consumer holds full authority over pacing, batch size, and pause or
  resume behavior, which makes backpressure and throttling straightforward to
  implement because they reduce to "poll less often" or "request fewer
  items", with no coordination required from the source.
- The pattern works against any source that can answer a request, including
  sources that have no push capability at all, which makes it the only
  option for many legacy and file- or table-based integrations.
- Polling loops are deterministic to test. advance a simulated clock, assert
  a poll happened, feed a canned response, assert the handler ran. No real
  transport or asynchronous callback registration is required in a unit test.
- Batch-bounded variants amortize fixed per-call overhead, such as network
  round trip, authentication, and serialization, across many items,
  improving throughput per unit of infrastructure cost compared to one round
  trip per message.

Negative consequences.

- Latency between a message's arrival and its first observation is bounded
  below by the polling interval, or, for long polling, by the maximum wait
  time, and no amount of consumer-side tuning removes this minimum entirely.
- A poorly tuned interval wastes resources. too short and most calls return
  nothing, incurring cost on metered platforms and needless load on the
  source, too long and messages queue up, inflating end-to-end latency and,
  in bounded-capacity queues, risking overflow or throttling upstream.
- The offset or acknowledgment tracker becomes a second piece of state that
  must be kept consistent with actual processing outcomes. a bug in ordering
  commit-before-process versus process-before-commit is a direct path to
  silent message loss or unbounded reprocessing.
- Fleet-wide polling traffic scales linearly with the number of independent
  consumers, which can become the dominant load on a shared source well
  before the actual message volume would justify it, a cost that a
  subscription-based push model does not carry in the same way.

## 11. Failure modes and misuse

**Consumer repeatedly drops out of its Kafka group and triggers rebalances
under normal load.** Symptom. The consumer group logs show a steady stream of
rebalance events even though no new instances are joining or leaving.
Cause. The handler takes longer to process a batch than
`max.poll.interval.ms` allows, so the client proactively leaves the group
before the next `poll()` call, exactly the behavior the Kafka Javadoc
documents (Apache Kafka 4.0 Javadoc, verified 2026-08-02,
https://kafka.apache.org/40/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html).
Fix. Reduce `max.poll.records` so each batch is smaller and faster to finish,
move slow processing off the polling thread with careful attention to not
exceeding the interval before the next poll, or raise `max.poll.interval.ms`
deliberately with the understanding that this also delays how quickly a
genuinely dead consumer is detected and its partitions reassigned.

**A metered polling API shows a high proportion of empty responses.**
Symptom. The billing or metrics dashboard for a service such as SQS shows
most `ReceiveMessage` calls returning no messages. Cause. Short polling, a
zero or near-zero wait time, against a queue that receives messages
sporadically, so most calls arrive between messages and return nothing.
Fix. Switch to long polling by setting a non-zero `WaitTimeSeconds`, which
AWS documents as directly reducing empty responses (AWS SQS Developer Guide,
verified 2026-08-02,
https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html).

**Messages are processed twice after a restart, or a message vanishes
entirely after a crash.** Symptom. Duplicate side effects, such as a
double-sent email or a duplicate database row, or a work item that
disappears with no trace after an outage. Cause. The offset or
acknowledgment marker is committed either before the handler runs, risking
loss on crash-before-processing, or is committed without atomicity relative
to the side effect of processing, risking duplication on
crash-after-processing-before-commit. Fix. Commit progress only after the
handler has durably completed, and design the handler to be idempotent so an
occasional at-least-once redelivery is harmless rather than corrupting
state, the same discipline named under Guaranteed Delivery.

**Fixed-interval polling produces a visible sawtooth in observed message
latency.** Symptom. Most messages wait close to a full interval and a few
wait almost none, visible as a sawtooth pattern on a latency chart.
Cause. A fixed poll interval, by construction, makes average latency roughly
half the interval and worst-case latency the full interval. This is not a
bug but a frequently misunderstood property that surprises teams moving from
an event-driven system. Fix. Either accept it as an inherent property and
size the interval to the acceptable worst case, or switch to long polling,
which bounds worst-case latency by the shorter of the timeout and the actual
message arrival.

**The polling loop silently stops making progress with no crash and no
error in the logs.** Symptom. Consumer lag or poll-count metrics flatline
with no corresponding error or restart event. Cause. An unhandled exception
inside the handler propagates up through the polling loop and terminates the
loop's thread or task without the loop's own exception boundary catching it,
so the loop simply never fires again. Fix. Wrap each poll-and-handle cycle in
its own exception boundary that logs, optionally routes the offending item to
a Dead Letter Channel, and reschedules the next poll regardless of the
previous cycle's outcome.

## 12. Trade-off matrix

| Force | Polling Consumer | Event-Driven Consumer | Competing Consumers (push, pool) |
|---|---|---|---|
| Best-case latency | Bounded below by interval or long-poll timeout | Near-immediate, driven by transport push | Near-immediate, same as event-driven |
| Resource cost when idle | Recurring poll calls, some wasted on empty responses, mitigated by long polling | Near zero, transport delivers only on arrival | Near zero when using push-based delivery |
| Works with no push-capable transport | Yes, this is its core strength | No, requires the transport to support push | No, requires push or a shared pull loop |
| Backpressure and pacing control | Direct and simple, reduce poll frequency or batch size | Indirect, usually requires separate flow-control signaling | Indirect, shared across the consumer pool |
| Deterministic unit testing | Straightforward, simulate the clock and canned responses | Harder, requires simulating async callback delivery | Harder, same as event-driven plus pool coordination |
| Scales to many independent consumers | Poll traffic scales linearly with consumer count | Subscription cost typically scales better | Depends on pool sizing versus source partitioning |

Competing Consumers is not an alternative delivery mechanism on its own, it is
usually layered on top of either a Polling Consumer or an Event-Driven
Consumer to add horizontal scale-out, which is why it is included here as a
named alternative shape rather than a strict substitute.

## 13. Related and incompatible patterns

Event-Driven Consumer is the direct sibling and the pattern most often
compared against Polling Consumer, sharing the same Message Channel and
Message abstractions but differing only in who initiates the receive
operation. A system frequently uses both, an event-driven consumer for the
low-latency path and a periodic polling consumer as a reconciliation sweep
that catches anything the event-driven path missed, which composes cleanly
because the polling sweep can simply skip anything already marked processed.

Competing Consumers composes with Polling Consumer when multiple worker
instances each run their own polling loop against a shared source, and the
source itself, whether a database row lock, a Kafka partition assignment, or
an SQS visibility timeout, provides the mutual exclusion that prevents two
consumers from processing the same item. Guaranteed Delivery is the pattern
that governs the offset or acknowledgment tracker participant named in
dimension 5. Polling Consumer without a Guaranteed Delivery discipline
degenerates into at-most-once delivery with silent loss on crash. Dead Letter
Channel composes as the destination for items a Polling Consumer's handler
cannot process after retries, keeping a poisoned message from blocking the
loop forever. Circuit Breaker composes as a guard in front of the source
call itself, so a consumer facing a failing source backs off rather than
hammering it with poll after poll.

Polling Consumer is not incompatible with any cataloged pattern in this
family, though it is in tension with patterns that assume push-driven
immediacy, such as a naive Wire Tap intended to observe messages the instant
they transit a channel. A Polling Consumer observing the same channel will
only see them at its next poll, which is a latency consideration rather than
a structural incompatibility.

## 14. Refactoring path in and out

To introduce Polling Consumer into code that currently uses an ad hoc,
unstructured retrieval loop, such as a `while(true)` block with a raw sleep
call and no timeout or batch discipline. first extract the source access
into a single named method with an explicit timeout and an explicit
batch-size parameter, so the two knobs named in dimension 5 exist as real
arguments rather than implicit constants buried in the loop body. Next,
extract the scheduling decision, when to call that method again, into a
separate Trigger-shaped component, whether that is a `PeriodicTrigger`
equivalent or simply a named function that computes the next delay, so the
cadence can be tuned or made adaptive without touching the retrieval logic.
Finally, introduce the offset or acknowledgment tracker as its own
persisted, testable component, and move the commit call to strictly after
the handler completes, per the ordering established in dimension 7.

To remove Polling Consumer once a channel gains genuine push capability, for
example migrating from a polled database table to a message broker with
native subscriptions. first run the two consumers side by side with the
event-driven path handling new traffic and the polling path running at a
reduced frequency purely as a reconciliation sweep, to build confidence that
the event-driven path is not silently dropping messages. Once metrics confirm
parity, remove the primary polling schedule and either delete the Polling
Consumer entirely or retain it at a much longer interval as a permanent
safety net, which is a common and defensible end state rather than a
half-finished migration.

## 15. Testing and verification

Polling Consumer is one of the easier consumption patterns to test
deterministically precisely because the consumer, not an external transport,
owns the timing. A unit test can construct a fake source that returns a
scripted sequence of responses, empty, then a batch, then empty again, inject
a fake or manually advanced clock in place of the real Trigger, and assert
exactly which poll calls occurred and what the handler received, without
needing a real queue, broker, or network connection. This is substantially
easier than testing an Event-Driven Consumer, where the test usually needs
either a real transport, an embedded broker, or a nontrivial mock of an
asynchronous callback registration mechanism.

What becomes easy. verifying batch-size and timeout behavior in isolation, by
asserting that a poll requesting a limit of 5 against a source containing 12
items returns exactly 5, verifying idle-interval and backoff behavior by
advancing a fake clock and counting poll invocations, and verifying the
commit-after-handle ordering by injecting a handler that throws partway
through a batch and asserting the tracker was not advanced past the last
successfully handled item.

What becomes harder. verifying true end-to-end latency behavior, because unit
tests that fake the clock cannot exercise the real interaction between a
long-poll timeout and actual network round-trip variance, which requires an
integration test against a real or embedded instance of the source. Testing
concurrent access when Competing Consumers is layered on top also requires
either a real shared source with real locking semantics or a carefully
constructed fake that models the mutual exclusion behavior, since a naive
fake source shared across concurrently run unit tests can hide races that
only appear against the real transport.

## 16. Observability signals

Log or emit a metric for every poll cycle recording whether the call
returned zero or more items, the count returned, the elapsed time of the call
itself, and, for a long-polling source, how much of the wait budget was
consumed before a result arrived. A healthy Polling Consumer shows a poll
count roughly proportional to the observation window divided by the interval
or timeout, a low proportion of zero-item responses when long polling is
enabled and traffic is steady, and a batch-count histogram that rarely sits
at the configured maximum, because consistently maxing out the batch limit
is an early signal that the consumer is falling behind the source's arrival
rate.

A failing or degraded instance shows one of a few distinct signatures, a poll
count that drops to zero, meaning the loop has stopped, likely from the
unhandled exception failure mode in dimension 11, a rising gap between
message arrival timestamp, if carried in the message, and the poll timestamp
that retrieved it, meaning rising consumer lag, or, specifically for
Kafka-shaped consumers, a rising rate of consumer group rebalances correlated
with slow batch processing, which is directly observable through the
client's own rebalance and commit-latency metrics. The offset or
acknowledgment tracker should be observable independently of the poll loop
itself, exposing the last committed position as its own gauge, so an
operator can distinguish a consumer that is polling but not committing from
one that has stopped polling entirely, which are different failures
requiring different responses.

## 17. Security and privacy implications

This dimension is largely engineering judgement rather than sourced fact,
stated plainly per the template's labelling convention. A Polling Consumer's
credentials to the source, such as an access key, a broker certificate, or a
database connection string, are held by the consumer and used on every poll
call, which means a compromised consumer process has standing, repeated
access to the source rather than a one-time credential presented at message
delivery time as some push-based webhook patterns use. This is a modest but
real difference in blast radius if the consumer process itself is
compromised. Long-polling connections that hold a request open for an
extended duration, up to the maximum the source allows, can also make
certain network-level attacks, such as slow-loris style resource exhaustion
against the source, a consideration for the source's own operators, though
this is a property of long-lived HTTP connections generally rather than
something unique to this pattern. Where the source is a queue containing
personal data, the polling consumer's own logs and observability signals
from dimension 16 must be reviewed to confirm message payloads or identifying
fields are not written into poll-cycle logs, since a verbose habit of
logging every item in the batch is a common, avoidable source of
sensitive-data leakage in otherwise well-built polling loops. No source
consulted for this entry makes a specific security claim about Polling
Consumer as a named pattern, the points above are this entry's own analysis
and should be weighed as such.

## 18. References

1. Hohpe, Gregor and Woolf, Bobby. *Enterprise Integration Patterns.
   Designing, Building, and Deploying Messaging Solutions*. Addison-Wesley,
   2003. "Polling Consumer" pattern page, verified 2026-08-02,
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/PollingConsumer.html
2. Spring Integration Reference Documentation, "Message Endpoints" chapter,
   sections on `PollingConsumer`, `Trigger`, `PollerMetadata`,
   `maxMessagesPerPoll`, and `receiveTimeout`, verified 2026-08-02,
   https://docs.spring.io/spring-integration/reference/endpoint.html
3. AWS Documentation, Amazon SQS Developer Guide, "Amazon SQS short and long
   polling", verified 2026-08-02,
   https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html
4. Apache Kafka 4.0 Javadoc, `org.apache.kafka.clients.consumer.KafkaConsumer`,
   `poll()` method documentation and `max.poll.interval.ms` behavior,
   verified 2026-08-02,
   https://kafka.apache.org/40/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html

## Code examples

Polling Consumer is demonstrated below in TypeScript, Python, and Go. Each
example implements the same shape, a source with a bounded `poll` call, a
Trigger-equivalent scheduling loop, a batch limit, and an offset tracker that
advances only after successful handling. Each sample is self-contained and
was compiled or run against the local toolchain noted after the block.

### TypeScript

```typescript
interface Item {
  id: number;
  payload: string;
}

interface Source {
  poll(limit: number): Item[];
}

class InMemoryQueue implements Source {
  private items: Item[] = [];

  enqueue(payload: string): void {
    this.items.push({ id: this.items.length + 1, payload });
  }

  poll(limit: number): Item[] {
    return this.items.splice(0, limit);
  }
}

class PollingConsumer {
  private lastProcessedId = 0;

  constructor(
    private readonly source: Source,
    private readonly batchLimit: number,
    private readonly handler: (item: Item) => void,
  ) {}

  pollOnce(): number {
    const items = this.source.poll(this.batchLimit);
    for (const item of items) {
      this.handler(item);
      this.lastProcessedId = item.id;
    }
    return items.length;
  }

  getLastProcessedId(): number {
    return this.lastProcessedId;
  }
}

const queue = new InMemoryQueue();
queue.enqueue("order-1");
queue.enqueue("order-2");
queue.enqueue("order-3");

const handled: string[] = [];
const consumer = new PollingConsumer(queue, 2, (item) => {
  handled.push(item.payload);
});

const firstBatch = consumer.pollOnce();
const secondBatch = consumer.pollOnce();
const thirdBatch = consumer.pollOnce();

console.log(`first poll returned ${firstBatch} items`);
console.log(`second poll returned ${secondBatch} items`);
console.log(`third poll returned ${thirdBatch} items`);
console.log(`handled in order, ${handled.join(", ")}`);
console.log(`last processed id, ${consumer.getLastProcessedId()}`);
```

### Python

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class Item:
    id: int
    payload: str


class InMemoryQueue:
    def __init__(self) -> None:
        self._items: list[Item] = []

    def enqueue(self, payload: str) -> None:
        self._items.append(Item(id=len(self._items) + 1, payload=payload))

    def poll(self, limit: int) -> list[Item]:
        batch, self._items = self._items[:limit], self._items[limit:]
        return batch


class PollingConsumer:
    def __init__(
        self,
        source: InMemoryQueue,
        batch_limit: int,
        handler: Callable[[Item], None],
    ) -> None:
        self._source = source
        self._batch_limit = batch_limit
        self._handler = handler
        self.last_processed_id = 0

    def poll_once(self) -> int:
        items = self._source.poll(self._batch_limit)
        for item in items:
            self._handler(item)
            self.last_processed_id = item.id
        return len(items)


def main() -> None:
    queue = InMemoryQueue()
    queue.enqueue("order-1")
    queue.enqueue("order-2")
    queue.enqueue("order-3")

    handled: list[str] = []
    consumer = PollingConsumer(queue, batch_limit=2, handler=lambda i: handled.append(i.payload))

    first = consumer.poll_once()
    second = consumer.poll_once()
    third = consumer.poll_once()

    print(f"first poll returned {first} items")
    print(f"second poll returned {second} items")
    print(f"third poll returned {third} items")
    print(f"handled in order, {', '.join(handled)}")
    print(f"last processed id, {consumer.last_processed_id}")


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import "fmt"

type Item struct {
	ID      int
	Payload string
}

type Source interface {
	Poll(limit int) []Item
}

type InMemoryQueue struct {
	items []Item
}

func (q *InMemoryQueue) Enqueue(payload string) {
	q.items = append(q.items, Item{ID: len(q.items) + 1, Payload: payload})
}

func (q *InMemoryQueue) Poll(limit int) []Item {
	if limit > len(q.items) {
		limit = len(q.items)
	}
	batch := q.items[:limit]
	q.items = q.items[limit:]
	return batch
}

type PollingConsumer struct {
	source          Source
	batchLimit      int
	handler         func(Item)
	lastProcessedID int
}

func NewPollingConsumer(source Source, batchLimit int, handler func(Item)) *PollingConsumer {
	return &PollingConsumer{source: source, batchLimit: batchLimit, handler: handler}
}

func (c *PollingConsumer) PollOnce() int {
	items := c.source.Poll(c.batchLimit)
	for _, item := range items {
		c.handler(item)
		c.lastProcessedID = item.ID
	}
	return len(items)
}

func main() {
	queue := &InMemoryQueue{}
	queue.Enqueue("order-1")
	queue.Enqueue("order-2")
	queue.Enqueue("order-3")

	var handled []string
	consumer := NewPollingConsumer(queue, 2, func(item Item) {
		handled = append(handled, item.Payload)
	})

	first := consumer.PollOnce()
	second := consumer.PollOnce()
	third := consumer.PollOnce()

	fmt.Printf("first poll returned %d items\n", first)
	fmt.Printf("second poll returned %d items\n", second)
	fmt.Printf("third poll returned %d items\n", third)
	fmt.Printf("handled in order, %v\n", handled)
	fmt.Printf("last processed id, %d\n", consumer.lastProcessedID)
}
```

Java, Rust, and Swift are omitted from this entry. the three languages above
already cover a garbage-collected object-oriented shape, a dynamically typed
scripting shape, and a statically compiled systems shape, and the pattern
does not gain a materially different idiom in the remaining languages beyond
the async-task framing already described in dimension 8.
