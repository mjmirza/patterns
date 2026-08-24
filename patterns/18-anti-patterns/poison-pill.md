---
name: Poison Pill
slug: poison-pill
family: 18-anti-patterns
category: Anti-pattern (Messaging and Concurrency)
aliases: [Poison Message, Poisoned Message, Toxic Message, Kill Pill]
first_described: "informal industry term, no single canonical origin"
maturity: established
related: [dead-letter-channel, circuit-breaker, bulkhead, retry, guarded-suspension, active-object]
incompatible_with: []
verified: 2026-08-02
---

# Poison Pill

## 1. Name, aliases, and lineage

Poison Pill is not a single pattern with one inventor and one publication behind
it. It is a plain-language term that grew up independently inside two separate
communities, concurrent programming and enterprise messaging, and both
communities kept the same words for two related but distinct situations. This
entry treats the term honestly rather than inventing a tidy origin story, and
that honesty is itself the first thing a reader needs to understand about it.

In the concurrent programming sense, a poison pill is a deliberately chosen
sentinel value placed onto the same channel or queue that carries ordinary work
items, whose only job is to tell a consumer thread or goroutine to stop pulling
work and exit. This usage is a legitimate, sanctioned technique. Standard
libraries have grown first-class support for it over time. Python 3.13 added a
`queue.ShutDown` exception raised by `Queue.get()` and `Queue.put()` once a
queue has been explicitly shut down, which the official documentation frames as
a controlled termination mechanism distinct from the older folk technique of
pushing a sentinel object (Python Software Foundation, *queue, A synchronized
queue class*, [docs.python.org/3/library/queue.html](https://docs.python.org/3/library/queue.html),
verified 2026-08-02). The .NET Base Class Library exposes the same idea through
`BlockingCollection<T>.CompleteAdding()`, whose documented remark states that
"after a collection has been marked as complete for adding, adding to the
collection is not permitted and attempts to remove from the collection will not
wait when the collection is empty" (Microsoft, *BlockingCollection\<T\>.CompleteAdding
Method*, [learn.microsoft.com/en-us/dotnet/api/system.collections.concurrent.blockingcollection-1.completeadding](https://learn.microsoft.com/en-us/dotnet/api/system.collections.concurrent.blockingcollection-1.completeadding),
verified 2026-08-02). Go's official blog describes the same idea at the
language level, not as a library feature but as an idiom built from closing a
channel. The article states plainly, "we can do this by closing a channel...
this close is effectively a broadcast signal to the senders" (Sameer Ajmani,
*Go Concurrency Patterns. Pipelines and cancellation*,
[go.dev/blog/pipelines](https://go.dev/blog/pipelines), verified 2026-08-02).

In the enterprise messaging sense, the same two words describe something
nobody chose on purpose. A message enters a durable queue, a subscriber
attempts to process it, the handler throws, the broker's at-least-once
guarantee redelivers the exact same message, the handler throws again, and the
cycle repeats without bound. The message has effectively poisoned the consumer.
This is the anti-pattern this entry is filed under. It is not that a shutdown
sentinel is bad design, it is that an ordinary business message, malformed by
accident, corrupted in transit, built against a schema the consumer no longer
understands, or exercising a genuine bug in the handler, behaves exactly like a
poison pill nobody wrote on purpose, and unless the system was built to
recognize and quarantine that behavior, it will crash-loop every consumer that
ever tries to read it. Gregor Hohpe and Bobby Woolf's Enterprise Integration
Patterns catalog names the architectural answer to this failure mode Dead
Letter Channel, defined by the question "what will the messaging system do
with a message it cannot deliver", with the solution that the system "may
elect to move the message to a Dead Letter Channel" once it determines it
cannot or should not deliver the message
([enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html),
verified 2026-08-02). Hohpe and Woolf never use the words "poison pill" or
"poison message" in that page's definition, which is itself worth recording,
the catalog term is Dead Letter Channel, and Poison Pill is the practitioner
slang for the failure the channel exists to catch.

The two senses share a structural shape, a value travels down the same path as
ordinary data and terminates ordinary processing when it arrives, which is why
practitioners reach for the same metaphor for both. This entry is filed as an
anti-pattern because the second sense, the accidental, unbounded, quarantine
free crash loop, is the one that actually damages production systems, and
because the first sense degrades into the second the moment its guardrails are
missing. A reader who only knows the benign sentinel technique and ships it
into a distributed, multi-producer, at-least-once environment without a
dead-letter path has, without realizing it, built the anti-pattern.

## 2. Problem and context

Every worker-pool or message-consumer system faces two separate but related
questions that get answered by the same mechanism if the designer is not
careful. First, how does a consumer that reads from a shared queue know when
there is no more work and it is time to stop, as opposed to simply waiting
because the queue happens to be temporarily empty. Second, what happens when a
message the consumer pulls off that queue cannot be processed, not because the
queue is empty or the consumer is slow, but because the message itself is
defective, whether through a malformed payload, a schema mismatch, a bug that
only that particular input triggers, or a business rule that can never be
satisfied for that record.

The context in which the anti-pattern arises is any system where a producer
and a consumer are decoupled by a queue, channel, mailbox, or topic, and the
delivery contract is at-least-once rather than at-most-once. At-least-once is
a common contract in production messaging, because losing a message
silently is almost always worse than delivering it twice, so brokers like
Amazon SQS, Azure Service Bus, RabbitMQ, and Kafka consumer groups all default
to redelivering a message that was not acknowledged within some window. That
default is exactly the mechanism that turns one bad message into repeated
damage. The broker is not misbehaving, it is honoring its contract, put the
message back if nobody confirmed it was handled. The anti-pattern is not in
the broker's redelivery, it is in a consumer and a system architecture that
has no distinct path for "this will never succeed no matter how many times you
redeliver it" versus "this failed because of a transient network blip, try
again in a moment."

The same problem shows up one level down inside a single process. A
thread-pool or goroutine-pool worker that pulls jobs from an in-memory queue
faces the identical shutdown question, but without a broker's redelivery
semantics, the risk instead is a leaked or hung worker if the shutdown signal
is designed poorly, for example if the code assumes a fixed, known number of
producers and sends exactly that many sentinel values, and the number of
producers later becomes dynamic. Go's own blog documents this exact failure
and its fix, describing the earlier explicit-signal approach as having "a
problem, each downstream receiver needs to know the number of possibly
blocked upstream senders and arrange to signal those senders on early return"
(Ajmani, *Go Concurrency Patterns. Pipelines and cancellation*,
[go.dev/blog/pipelines](https://go.dev/blog/pipelines), verified 2026-08-02).

## 3. Forces

- Delivery guarantee versus consumer safety. At-least-once redelivery
  guarantees no message is silently dropped, but the same guarantee is what
  repeatedly hands a malformed message back to a consumer that cannot process
  it. Choosing at-least-once for correctness pulls directly against the need
  to isolate a single bad record from destroying throughput.
- Ordering versus isolation. A partitioned or FIFO queue preserves the
  sequence a downstream consumer depends on, but preserving order means the
  system cannot simply skip a poisoned message without either violating that
  order or accepting a permanent stall at the head of the partition. Isolating
  the bad record by skipping it is often the only way to keep the healthy
  ninety nine percent of traffic flowing, and it directly threatens ordering
  guarantees.
- Fast, loud failure versus availability. A crash loop is, in one light, the
  system doing exactly what a naive on-call engineer would want, screaming
  until someone looks. It is also, in a second light, an outage that takes
  every healthy message in the same queue down with it. The tension is
  between visibility of the defect and continued service to unrelated
  traffic.
- Control plane versus data plane purity. The sentinel-shutdown technique
  smuggles a control signal, stop now, through the exact same channel that
  carries ordinary data. This is efficient and requires no second channel, but
  it means the channel's type or value space must be able to distinguish
  control from data unambiguously, or a legitimate data value can be
  misread as the shutdown signal.
- Cost of quarantine infrastructure versus cost of an outage. Building a
  dead-letter path, a bounded retry counter, an alarm on dead-letter depth,
  and a redrive tool is nontrivial engineering effort for a code path that,
  by design, is meant to be rarely exercised. Skipping that effort is cheap
  until the first poisoned message reaches production, at which point the
  cost is an incident, not a code review comment.
- Resource cleanup versus fast exit. A worker that receives a shutdown
  sentinel must still release whatever it was holding, open connections,
  locks, partially written buffers, before it actually stops. A poorly
  designed shutdown path that treats the sentinel as an unconditional early
  return can leak exactly the resources the shutdown was meant to free.

## 4. Applicability and non-applicability

Apply the sentinel-shutdown technique, the benign sense of this term, when the
following hold.

- A bounded, in-process producer-consumer relationship where the number of
  producers and consumers is either known up front or can be tracked reliably
  by a synchronization primitive such as a `sync.WaitGroup` or a reference
  count, so the shutdown signal reaches every consumer exactly once.
- The channel or queue type can represent the sentinel with a value that
  cannot collide with any legitimate payload, for example a distinct object
  identity in Python, a closed channel state in Go, or a dedicated exception
  such as `queue.ShutDown` rather than an in-band value like `None` or `-1`.
- Termination is a normal, expected, and controlled part of the program's
  lifecycle, not a response to an unrecoverable error in a specific unit of
  work.

Do not treat the poison-pill technique as sufficient, and instead build
explicit dead-letter handling, when any of these hold, because this is where
the benign technique curdles into the anti-pattern this entry documents.

- The system spans process or machine boundaries and uses a durable broker
  with at-least-once delivery. A crashed consumer does not remove the message,
  it returns the message, so a defective payload will be handed to the next
  consumer that starts, and the one after that, indefinitely, unless the
  broker or the application tracks a bounded delivery count.
- Multiple, unbounded, or dynamically scaling producers exist. A design that
  requires exactly N sentinels for N known consumers breaks the moment
  consumer count is elastic, which is precisely the scenario the Go pipelines
  article calls out as the reason to prefer closing a channel over counted
  sentinels (Ajmani, *Go Concurrency Patterns. Pipelines and cancellation*,
  [go.dev/blog/pipelines](https://go.dev/blog/pipelines), verified
  2026-08-02).
- The payload and the sentinel share an untyped or loosely typed channel where
  a legitimate business value could be confused with the termination signal,
  for example a system that uses `null` both as "no more work" and as a valid
  field value somewhere upstream.
- A single ordered or partitioned stream serves many independent logical
  work items, so one malformed item can block every item behind it,
  regardless of whether those later items are perfectly healthy.
- The failure that a given message triggers is deterministic rather than
  transient. Retrying a message that failed because of a five second network
  timeout is reasonable. Retrying a message that fails because its JSON body
  cannot be parsed at all will fail identically on every attempt, and no
  amount of redelivery changes that outcome.

## 5. Structure

The structure is the same shape in both the benign and the pathological
sense, only the intent and the surrounding guardrails differ.

- **Producer.** The party that writes values onto the shared channel. In the
  distributed anti-pattern sense, this is any upstream service, client, or
  another queue's consumer acting as a relay, and it may be malicious,
  buggy, or simply out of date with the schema the downstream consumer
  expects.
- **Shared channel or queue.** The medium both ordinary payloads and the
  sentinel or poisoned value travel through. In a single process this is an
  in-memory channel, blocking queue, or bounded buffer. Across processes it
  is a durable broker such as a message queue or a topic partition.
- **Sentinel or poisoned value.** In the benign sense, a value deliberately
  constructed by the shutdown-issuing code, ideally with a type or identity
  that cannot be confused with real data. In the anti-pattern sense, an
  ordinary payload that happens to be unprocessable, with no distinguishing
  marker at all until a consumer discovers the fact by failing.
- **Consumer or worker.** The party that reads values off the channel and
  either does the requested work or, on encountering the sentinel, exits
  cleanly. In the anti-pattern sense, this party has no branch for "the
  payload itself is defective" and treats every failure as retryable.
- **Delivery tracking (present only in the remediated architecture).** A
  counter, either broker-native such as SQS's `ApproximateReceiveCount` and
  Azure Service Bus's delivery count, or application-managed, that records how
  many times a given message has been attempted.
- **Dead-letter channel or quarantine store (present only in the remediated
  architecture).** A secondary channel that a message is moved to once its
  delivery count exceeds a configured threshold, removing it from the main
  flow so healthy messages are not blocked behind it, while preserving the
  message for later inspection.

## 6. ASCII structure diagram

```
  BENIGN SENSE. sentinel shutdown, single process, known consumer count

     Producer(s)
         |
         v
   +-----------------+
   |  shared channel  |   payload, payload, payload, ..., SENTINEL
   +-----------------+
         |         |          |
         v         v          v
    Consumer1  Consumer2  Consumer3
         |         |          |
      exits     exits      exits
    on sentinel on sentinel on sentinel


  PATHOLOGICAL SENSE. unmarked poison message, distributed, at-least-once

     Producer
         |
         v
   +------------------+
   |  durable  queue   |  msg1, msg2, POISONED_MSG, msg4, ...
   +------------------+
         |
         v
     Consumer  --- handle(POISONED_MSG) --> throws
         |
   (not acknowledged, broker redelivers)
         |
         v
     Consumer  --- handle(POISONED_MSG) --> throws  <-- crash loop
         |
         v
      ... repeats until an external actor intervenes ...


  REMEDIATED. delivery-count-bounded dead-letter quarantine

     Producer
         |
         v
   +------------------+          delivery_count > max?
   |  durable  queue   | -------------------------------+
   +------------------+                                  |
         |                                                v
         v                                    +-----------------------+
     Consumer --- handle(msg) --> throws       |  dead-letter channel   |
         |                                     |  (quarantine store)   |
   delivery_count++                            +-----------------------+
         |                                                |
   (redeliver while count <= max)                          v
                                              operator inspects, fixes,
                                              redrives, or discards
```

## 7. Dynamics

The benign shutdown sequence, drawn from the close-channel idiom Go documents
(Ajmani, *Go Concurrency Patterns. Pipelines and cancellation*,
[go.dev/blog/pipelines](https://go.dev/blog/pipelines), verified 2026-08-02),
runs as follows. The controlling goroutine spins up a fixed number of worker
goroutines, each reading from a shared jobs channel in a loop. The controller
sends every job it has, then closes the jobs channel rather than sending a
counted number of sentinel values. Each worker's range loop over the channel
exits automatically the instant the channel is both closed and drained, which
is a language-level guarantee, a receive on a closed channel returns
immediately once the channel is empty, so the broadcast reaches every worker
regardless of how many workers exist. Each worker then signals a
`sync.WaitGroup` that it is done, the controller waits on the group, and once
every worker has exited, the controller closes the downstream results channel
so anything reading results also terminates cleanly. No worker needs to know
how many siblings it has, and no sentinel value needs to be distinguishable
from real data because the channel's closed state, not a value on the
channel, carries the signal.

The pathological sequence runs differently. A producer places a message on a
durable queue that a consumer will pull from at-least-once. A consumer
receives the message under a visibility timeout or a peek-lock, attempts to
process it, and the handler throws an unhandled exception because the payload
cannot be parsed, or because a downstream dependency the handler calls rejects
the payload outright, or because of a genuine defect in the handler logic
that only this particular input exercises. Because the consumer never calls
the broker's acknowledge or complete operation, the broker's timeout expires
and the message becomes visible again. A consumer, possibly the same one,
possibly a freshly restarted one, receives the identical message and repeats
the identical failure. If nothing tracks how many times this has happened,
the cycle has no natural end. Microsoft's own guidance on Azure Service Bus
frames one concrete instance of exactly this loop, describing a message that
is "repeatedly received but never settled" as one that "is eventually moved
to the dead-letter queue with the reason MaxDeliveryCountExceeded" only once a
delivery count threshold intervenes (Microsoft, *Service Bus dead-letter
queues*,
[learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
verified 2026-08-02), which is precisely the intervention absent in the
unmitigated anti-pattern.

The remediated sequence layers a delivery-count check onto the pathological
sequence. Each redelivery increments a counter, whether that counter is
broker-native, as with SQS's redrive policy where "the maxReceiveCount is the
number of times a consumer can receive a message from a source queue before
it is moved to a dead-letter queue" (Amazon Web Services, *Using dead-letter
queues in Amazon SQS*,
[docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
verified 2026-08-02), or application-managed. Once the count exceeds the
threshold, the broker or the application diverts the message to a dead-letter
channel instead of redelivering it to a consumer again. The main queue's
throughput for every other message is preserved, the poisoned message is
preserved for forensic inspection rather than silently dropped, and an
operator or an automated alert can decide whether to fix and redrive the
message or discard it permanently.

## 8. Implementation variants

- **Counted sentinel per consumer.** The producer sends exactly N sentinel
  values for N known consumers. Simple to reason about when N is fixed and
  small, but breaks the moment consumer count changes at runtime, which is
  the specific failure the Go pipelines article warns against (Ajmani,
  *Go Concurrency Patterns. Pipelines and cancellation*,
  [go.dev/blog/pipelines](https://go.dev/blog/pipelines), verified
  2026-08-02).
- **Close-channel broadcast (Go).** Rather than sending a value, the
  controlling code closes the channel itself. Every blocked or future
  receive on that channel unblocks immediately with the channel's zero
  value, which functions as a broadcast to an unbounded number of receivers
  with no counting required.
- **Distinguished sentinel object (Python, pre-3.13 idiom).** A module-level
  `object()` instance, whose identity, not its value, is compared with `is`
  rather than `==`, so it can never collide with a legitimate payload,
  including `None`, `0`, or an empty string.
- **Native shutdown exception (Python 3.13, `queue.ShutDown`).** The standard
  library's `queue.Queue` gained an explicit `shutdown()` method whose effect
  is documented as causing `put()` to raise `queue.ShutDown` and `get()` to
  raise `queue.ShutDown` "if the queue has been shut down and is empty, or if
  the queue has been shut down immediately" (Python Software Foundation,
  *queue, A synchronized queue class*,
  [docs.python.org/3/library/queue.html](https://docs.python.org/3/library/queue.html),
  verified 2026-08-02), replacing the ad hoc sentinel object with a
  first-class, unambiguous control-flow signal.
- **CompleteAdding on a bounded collection (.NET).** `BlockingCollection<T>`
  exposes `CompleteAdding()`, after which "adding to the collection is not
  permitted and attempts to remove from the collection will not wait when
  the collection is empty" (Microsoft, *BlockingCollection\<T\>.CompleteAdding
  Method*,
  [learn.microsoft.com/en-us/dotnet/api/system.collections.concurrent.blockingcollection-1.completeadding](https://learn.microsoft.com/en-us/dotnet/api/system.collections.concurrent.blockingcollection-1.completeadding),
  verified 2026-08-02), which a `GetConsumingEnumerable()` loop observes as a
  natural end of iteration.
- **Disconnect-as-signal (Rust `std::sync::mpsc`).** Rather than an explicit
  sentinel value, dropping every `Sender` clone causes a blocked or future
  `recv()` call on the corresponding `Receiver` to return an `Err`, which the
  standard library documents directly, "the send and receive operations on
  channels will all return a Result... an unsuccessful operation is normally
  indicative of the other half of a channel having hung up by being dropped"
  (Rust Project, *std, sync, mpsc*,
  [doc.rust-lang.org/std/sync/mpsc/index.html](https://doc.rust-lang.org/std/sync/mpsc/index.html),
  verified 2026-08-02). Ownership itself becomes the shutdown mechanism.
- **Delivery-count-bounded dead-letter quarantine (the remediated messaging
  variant).** The receiving side of a durable broker, rather than a single
  in-process channel, tracks how many times a message has been delivered
  without being acknowledged, and moves the message to a separate channel
  once that count crosses a threshold, as implemented by Amazon SQS's redrive
  policy (Amazon Web Services, *Using dead-letter queues in Amazon SQS*,
  [docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
  verified 2026-08-02) and Azure Service Bus's maximum delivery count
  (Microsoft, *Service Bus dead-letter queues*,
  [learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
  verified 2026-08-02).
- **Application-level explicit dead-lettering.** A handler that can classify
  a failure as permanent, a validation error, a schema mismatch, rather than
  transient, calls the broker's explicit dead-letter operation immediately on
  the first attempt rather than waiting for a delivery count to expire,
  which Azure Service Bus exposes directly as
  `ServiceBusReceiver.DeadLetterMessageAsync` (Microsoft, *Service Bus
  dead-letter queues*,
  [learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
  verified 2026-08-02).

## 9. Known production uses

- **.NET Base Class Library, `System.Collections.Concurrent.BlockingCollection<T>`.**
  Ships `CompleteAdding()` as the sanctioned sentinel-shutdown mechanism for
  producer-consumer collections, documented as changing the behavior of
  `GetConsumingEnumerable()` for every consumer of the collection (Microsoft,
  *BlockingCollection\<T\>.CompleteAdding Method*,
  [learn.microsoft.com/en-us/dotnet/api/system.collections.concurrent.blockingcollection-1.completeadding](https://learn.microsoft.com/en-us/dotnet/api/system.collections.concurrent.blockingcollection-1.completeadding),
  verified 2026-08-02).
- **Go standard library and official pipelines idiom.** The Go project's own
  blog documents closing a channel as the recommended broadcast mechanism for
  telling an unbounded number of goroutines to stop, contrasting it directly
  with the brittler counted-sentinel approach (Ajmani, *Go Concurrency
  Patterns. Pipelines and cancellation*,
  [go.dev/blog/pipelines](https://go.dev/blog/pipelines), verified
  2026-08-02).
- **CPython standard library, `queue` module.** As of Python 3.13, `Queue`
  exposes a native `shutdown()` method and a corresponding `queue.ShutDown`
  exception, replacing the community's older ad hoc sentinel-object idiom
  with a language-provided mechanism (Python Software Foundation, *queue, A
  synchronized queue class*,
  [docs.python.org/3/library/queue.html](https://docs.python.org/3/library/queue.html),
  verified 2026-08-02).
- **Rust standard library, `std::sync::mpsc`.** Channel disconnection,
  triggered by dropping every `Sender`, is the documented, idiomatic
  replacement for an explicit sentinel value in Rust's ownership-based
  concurrency model (Rust Project, *std, sync, mpsc*,
  [doc.rust-lang.org/std/sync/mpsc/index.html](https://doc.rust-lang.org/std/sync/mpsc/index.html),
  verified 2026-08-02).
- **Amazon Simple Queue Service.** Implements the remediated,
  quarantine-based answer to the pathological sense of this anti-pattern
  through its dead-letter queue feature and `maxReceiveCount` redrive policy,
  explicitly built so that "the dead-letter queue is useful for debugging your
  application because you can isolate unconsumed messages" (Amazon Web
  Services, *Using dead-letter queues in Amazon SQS*,
  [docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
  verified 2026-08-02).
- **Microsoft Azure Service Bus.** Implements the same remediation with a
  per-entity dead-letter sub-queue and a configurable `MaxDeliveryCount`,
  documenting the exact crash-loop symptom this entry describes and the
  mechanism that ends it, moving the message to the dead-letter queue "with
  the reason MaxDeliveryCountExceeded" (Microsoft, *Service Bus dead-letter
  queues*,
  [learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
  verified 2026-08-02).

## 10. Consequences

Positive consequences, present when the sentinel technique and the
dead-letter remediation are both applied correctly.

- Clean, deterministic shutdown of a worker pool without polling a flag
  variable or relying on external interrupt signals, because the termination
  condition is expressed in the same primitive, a channel or queue state,
  that the workers already block on.
- Healthy messages keep flowing even when one message is permanently
  unprocessable, because the delivery-count threshold isolates the bad
  message from the rest of the stream rather than letting it stall
  everything behind it.
- Forensic visibility. A dead-lettered message is preserved rather than
  silently dropped, letting an operator inspect exactly what failed and why,
  which the AWS documentation frames as one of the primary reasons to use the
  feature at all, to "examine logs for exceptions that might have caused
  messages to be moved to a dead-letter queue" and to "analyze the contents of
  messages moved to the dead-letter queue to diagnose application issues"
  (Amazon Web Services, *Using dead-letter queues in Amazon SQS*,
  [docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
  verified 2026-08-02).
- Decoupling of the termination signal from the number of participants. The
  close-channel and disconnect-based variants scale to an unbounded number
  of consumers or producers without any code change, because the signal is
  a state transition rather than a counted set of values.

Negative consequences, present whenever the pattern is applied without its
guardrails, or even when applied correctly but under-monitored.

- Type confusion risk. If the sentinel shares the same value space as
  legitimate data on an untyped or loosely typed channel, a real business
  value can be misread as the shutdown signal, draining the queue early and
  silently dropping real work.
- Ordering violation risk. Skipping or quarantining a poisoned message inside
  an ordered or partitioned stream necessarily changes the order the rest of
  the messages are delivered in relative to what a strict FIFO contract
  promised, which is a real cost even when it is the lesser evil compared to
  a permanent stall.
- Silent data accumulation. A dead-letter queue is, by design, not
  automatically drained. Azure's own documentation states plainly, "there's
  no automatic cleanup of the DLQ, messages remain in the DLQ until you
  explicitly retrieve them" (Microsoft, *Service Bus dead-letter queues*,
  [learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
  verified 2026-08-02), which means an unmonitored dead-letter path quietly
  becomes an unbounded, unmanaged data store rather than a fixed cost.
  Amazon's documentation gives the identical warning in a different form, by
  cautioning readers to "set the retention period of a dead-letter queue to
  be longer than the retention period of the original queue" (Amazon Web
  Services, *Using dead-letter queues in Amazon SQS*,
  [docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
  verified 2026-08-02), because the alternative is the dead-letter queue
  expiring the very evidence it was meant to preserve.
- Resource leak on ungraceful exit. A worker that treats the sentinel as an
  unconditional early return without running its cleanup path can leak
  connections, locks, or partially buffered writes, converting a clean
  shutdown mechanism into a slow resource drain.
- False positives from operational rather than payload causes. A message can
  be dead-lettered for a reason that has nothing to do with the payload
  itself, for example the settlement-after-close scenario Azure documents,
  where a message is repeatedly received but never settled because "the
  service closes an idle connection after 10 minutes, which also releases the
  lock", causing a perfectly healthy message to be misclassified and
  quarantined alongside genuinely poisoned ones (Microsoft, *Service Bus
  dead-letter queues*,
  [learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
  verified 2026-08-02).

## 11. Failure modes and misuse

The observable symptom is listed first in each triple, because that is what a
reader actually sees before they know the cause.

- **Symptom.** Consumer fleet CPU and error-log volume spike sharply while
  throughput across the whole pipeline drops toward zero, and the same exception message
  repeats every few seconds across restarts.
  **Cause.** At-least-once redelivery of a message the handler deterministically
  fails on, with no bounded retry count and no dead-letter path, so the
  broker keeps handing the same message back indefinitely.
  **Fix.** Configure a bounded delivery count and a dead-letter destination,
  as SQS's `maxReceiveCount` redrive policy and Azure Service Bus's
  `MaxDeliveryCount` both provide as a built-in feature (Amazon Web Services, *Using
  dead-letter queues in Amazon SQS*,
  [docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
  verified 2026-08-02).

- **Symptom.** Worker goroutines or threads hang forever after a shutdown was
  supposedly triggered, or the process panics on a nil channel access during
  shutdown.
  **Cause.** A counted-sentinel shutdown design that assumed a fixed number
  of producers, and the actual number of producers changed at runtime,
  leaving some workers never receiving their sentinel and others receiving
  one from a channel that no longer exists.
  **Fix.** Replace the counted sentinel with a close-channel broadcast, which
  Go's own documentation recommends for exactly this reason (Ajmani, *Go
  Concurrency Patterns. Pipelines and cancellation*,
  [go.dev/blog/pipelines](https://go.dev/blog/pipelines), verified
  2026-08-02).

- **Symptom.** The queue drains and every worker exits far earlier than
  expected, while a legitimate item of work is missing from the output.
  **Cause.** The sentinel value collides with a legitimate payload value on
  an untyped channel, for example a `None` or `null` used both as "no more
  work" and as a genuine, valid business value produced upstream.
  **Fix.** Use a distinguished value whose identity, not its equality, marks
  it as the sentinel, such as a module-level `object()` in Python compared
  with `is`, or migrate to a language-level shutdown signal such as Python
  3.13's `queue.ShutDown` that, by construction, cannot collide with a
  payload value (Python Software Foundation, *queue, A synchronized queue
  class*, [docs.python.org/3/library/queue.html](https://docs.python.org/3/library/queue.html),
  verified 2026-08-02).

- **Symptom.** A dead-letter queue that nobody has looked at in months has
  grown to a size that shows up on a storage or compliance report before
  anyone on the engineering team notices it.
  **Cause.** No alarm or dashboard was wired to the dead-letter queue's depth
  or age, so it accumulates silently, a direct consequence of the documented
  fact that "there's no automatic cleanup of the DLQ" (Microsoft, *Service
  Bus dead-letter queues*,
  [learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
  verified 2026-08-02).
  **Fix.** Alarm on dead-letter queue depth and message age as a first-class
  operational metric, and review the queue on a fixed schedule rather than
  reactively, following AWS's own guidance to configure "an alarm for any
  messages moved to a dead-letter queue" (Amazon Web Services, *Using
  dead-letter queues in Amazon SQS*,
  [docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
  verified 2026-08-02).

- **Symptom.** Consumer lag on one ordered partition or FIFO queue grows
  without bound while every other partition or queue in the same system
  looks completely healthy.
  **Cause.** Head-of-line blocking, a strict-order consumer that will not
  skip a message it cannot process, because skipping would violate the
  ordering contract the downstream depends on, and the message can never
  succeed no matter how many times it is retried.
  **Fix.** Combine bounded retry with explicit, audited skip-and-quarantine
  for ordered streams, and treat the ordering-versus-progress trade-off as a
  deliberate design decision rather than an accident, noting that Amazon
  explicitly warns against using a dead-letter queue with a FIFO queue in
  scenarios where reordering breaks downstream context, for example an "Edit
  Decision List for a video editing suite, where changing the order of edits
  changes the context of subsequent edits" (Amazon Web Services, *Using
  dead-letter queues in Amazon SQS*,
  [docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
  verified 2026-08-02).

- **Symptom.** Messages that were, in fact, processed correctly show up in
  the dead-letter queue anyway, confusing the team investigating a genuine
  payload defect because the sample now contains false positives.
  **Cause.** Settlement, the acknowledge or complete call, happened after the
  receiver or its connection had already closed, so the broker never learned
  the message succeeded, incremented the delivery count on redelivery, and
  eventually dead-lettered a message with no payload problem at all.
  **Fix.** Settle every message before closing the receiver or the
  connection, matching the pattern Microsoft documents directly, complete
  the message "while the receiver is still open" inside the same `await
  using` scope that created it (Microsoft, *Service Bus dead-letter queues*,
  [learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
  verified 2026-08-02).

## 12. Trade-off matrix

Named alternatives, all of which address some slice of the same problem,
either termination signaling or fault isolation, without being the poison
pill technique itself.

| Force | Poison Pill (sentinel / unmitigated poisoned message) | Dead Letter Channel | Circuit Breaker | Bulkhead | Context or Cancellation Token |
|---|---|---|---|---|---|
| Latency to terminate consumers | Low, one shared state transition reaches every consumer at once | Not applicable, this is a fault-isolation pattern, not a shutdown pattern | Higher, waits for a failure threshold before opening | Not applicable to shutdown | Low, propagated through call graph, similar to closing a channel |
| Coupling between producer and consumer count | Low for close-broadcast variants, high for counted-sentinel variants | Low, the broker mediates without either side knowing the other's identity | Low, breaker sits between caller and callee | Low, isolation is structural, not identity based | Low, a token is passed down an arbitrary call depth |
| Consistency and ordering | Skipping a poisoned message risks violating order in a partitioned stream | Same risk, but the risk is deliberate and bounded by a delivery-count threshold rather than unbounded | Does not touch message ordering, it protects a downstream dependency from overload | Isolates failure domains but does not itself reorder anything | Does not touch data ordering, purely a cancellation signal |
| Operability and visibility | Poor in the unmitigated case, a crash loop with no distinct failure category | Strong, a dedicated inspectable destination for failed items | Strong, an explicit open, half-open, closed state is directly observable | Moderate, isolation boundaries are visible but individual failures within a bulkhead are not automatically surfaced | Weak on its own, cancellation is a control signal, not a diagnostic one |
| Cost to implement | Low for in-process shutdown, effectively free with modern language support | Moderate, requires a delivery-count mechanism and a secondary destination | Moderate, requires a failure-rate window and state machine | Moderate to high, requires partitioning resources, threads, or connection pools per domain | Low, most modern runtimes provide this as a built-in feature |
| Team topology fit | Any team, this is a low-level concurrency primitive | Teams operating a shared broker or queue that multiple services depend on | Teams with a downstream dependency that can be overwhelmed | Teams sharing infrastructure across multiple tenants or workloads | Any team using a language runtime with native cancellation support |
| Cognitive load | Low when the sentinel is a distinct type, high when it shares a value space with real data | Moderate, requires the team to build and monitor a second data path | Moderate, requires reasoning about three states and thresholds | Moderate to high, requires reasoning about resource partitioning up front | Low, most developers already understand cancellation as a concept |

## 13. Related and incompatible patterns

- **Dead Letter Channel.** The direct architectural remedy for the
  pathological sense of this anti-pattern. Where the poison pill anti-pattern
  is the absence of a distinct path for unprocessable messages, Dead Letter
  Channel is that distinct path made explicit, giving the system somewhere
  to move a message once it has proven, through a bounded number of
  attempts, that it cannot be processed (Hohpe and Woolf, definition sourced
  from
  [enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html),
  verified 2026-08-02). The two are almost always discussed together, one
  names the failure, the other names the fix.
- **Circuit Breaker.** A complementary rather than competing mechanism.
  Circuit Breaker protects a consumer from calling an already-failing
  downstream dependency repeatedly, which reduces the blast radius of a
  poisoned message that fails specifically because of a downstream outage
  rather than a defect in the message itself. The two compose, a bounded
  delivery count catches a message that can never succeed by its own nature,
  while a circuit breaker catches a healthy message that is temporarily
  unprocessable because something it depends on is down.
- **Bulkhead.** Isolates the resources one class of message or one tenant
  consumes from another, so a crash loop triggered by one poisoned message
  in one partition does not exhaust the thread pool or connection pool that
  healthy traffic in another partition also depends on.
- **Retry (with bounded backoff).** The mechanism that decides how many
  times, and with what delay, a failed message gets another attempt before
  it is considered permanently failed and handed to a dead-letter channel.
  Retry without a bound is the mechanical cause of the unmitigated
  anti-pattern, retry with a bound is one half of its remedy.
- **Guarded Suspension and Active Object.** Both describe a consumer that
  blocks on an empty work queue until work arrives, the exact structural
  setting the sentinel-shutdown technique operates inside. The mailbox in
  Active Object is a natural place for a shutdown sentinel to live, because
  the mailbox already serializes all messages, including a poison pill,
  through one processing loop.
- **Context or Cancellation Token propagation.** An alternative shutdown
  mechanism that some languages and runtimes prefer over a sentinel value on
  the data channel itself, because it keeps the control signal entirely out
  of the data channel's type. Go's `context.Context` and .NET's
  `CancellationToken` both let a caller signal cancellation down an
  arbitrary call graph without touching the payload channel at all, which
  sidesteps the type-confusion risk this entry's failure modes describe.
- **Incompatible relationship, strict exactly-once processing claims.** A
  system that claims exactly-once semantics is in tension with a dead-letter
  path that silently retries a message multiple times before quarantining
  it, unless the handler is also idempotent, because the multiple delivery
  attempts that precede a dead-letter move are, by definition, at-least-once
  behavior at the transport layer even if the application layer later
  deduplicates.

## 14. Refactoring path in and out

Introducing the benign sentinel technique into code that currently tears down
a worker pool by killing threads or setting an unsynchronized boolean flag.

1. Identify every place a worker thread or goroutine reads from the shared
   queue in a loop, and confirm the loop's exit condition today.
2. Choose a shutdown mechanism appropriate to the language, a distinguished
   sentinel object compared by identity, a native shutdown primitive such as
   `queue.ShutDown` or `BlockingCollection.CompleteAdding`, or a
   close-channel broadcast.
3. Change the producer's teardown code to issue that single, unambiguous
   signal rather than a counted set of sentinel values or an external kill
   signal.
4. Change each worker's loop to detect the signal through the language's
   native mechanism, a raised exception, a closed-channel receive, or an
   identity comparison, and to run its resource cleanup before returning.
5. Add a test that starts an arbitrary, varying number of workers, issues the
   shutdown signal exactly once, and asserts every worker exits and no
   worker hangs.
6. Remove the old kill-thread or unsynchronized-flag mechanism entirely
   rather than leaving both in place, because two competing shutdown paths
   are themselves a source of the type-confusion and leaked-resource
   failure modes described above.

Removing the pathological, unmitigated poison-pill failure mode from an
existing distributed consumer that currently has no dead-letter path.

1. Confirm the crash-loop symptom exists by inspecting logs for a repeating
   exception against the same message identifier, rather than assuming it is
   present.
2. Split the handler's error handling into two explicit categories,
   transient failures that are worth retrying, such as a network timeout or
   a downstream 503, and terminal failures that will never succeed no matter
   how many times they are retried, such as a payload that fails schema
   validation.
3. Wire a broker-native or application-managed delivery-count threshold, and
   configure the broker's dead-letter destination, following the mechanisms
   AWS SQS's `maxReceiveCount` redrive policy and Azure Service Bus's
   `MaxDeliveryCount` document (Amazon Web Services, *Using dead-letter
   queues in Amazon SQS*,
   [docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
   verified 2026-08-02).
4. For terminal failures identified in step 2, call the broker's explicit
   dead-letter operation immediately rather than waiting for the delivery
   count to expire, so a message that can never succeed is quarantined on
   the first attempt instead of consuming N redundant retries.
5. Add an alarm on the dead-letter destination's depth and oldest-message
   age, so an unmonitored quarantine path does not silently accumulate.
6. Build or adopt a redrive tool that lets an operator inspect a
   dead-lettered message, fix the root cause if one exists upstream, and
   resubmit the message to the main queue once the fix is confirmed.
7. Load-test the remediated path with a deliberately malformed message
   injected into the queue, and confirm it reaches the dead-letter
   destination within the configured delivery count rather than crash
   looping the consumer fleet.

## 15. Testing and verification

- **Deliberate poison injection.** In an integration test, publish one
  well-formed message and one deliberately malformed message into the same
  queue, and assert that the well-formed message is processed successfully
  while the malformed one lands in the dead-letter destination within the
  configured delivery count, rather than blocking or crashing the consumer
  under test.
- **Shutdown-signal correctness under varying participant counts.** Because
  the counted-sentinel failure mode only appears when the number of
  producers or consumers changes, a property-based test that runs the
  worker pool with a randomized number of producers and consumers on every
  iteration, then asserts every item submitted is processed exactly once and
  every worker exits, catches the brittleness a fixed-count test would miss.
- **Resource-leak assertion on shutdown.** After the shutdown signal is
  issued and every worker has exited, assert that every resource the worker
  acquired, connections, file handles, locks, has been released, since a
  worker that treats the sentinel as an unconditional early return can leak
  exactly these resources while still passing a naive "did it exit" test.
- **Settlement-before-close ordering.** For distributed consumers, write a
  test that deliberately closes the receiver immediately after receiving a
  message but before settling it, and assert the system's behavior matches
  the documented outcome, the message becomes visible again and its
  delivery count increments, rather than being silently lost, verifying the
  application correctly distinguishes this operational cause from a genuine
  payload defect (Microsoft, *Service Bus dead-letter queues*,
  [learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
  verified 2026-08-02).
- **Ordering-violation assertion for partitioned streams.** For any consumer
  that skips or quarantines a poisoned message inside an ordered partition,
  write a test that asserts the exact ordering guarantee the downstream
  depends on either still holds for the remaining messages, or that the
  violation is explicitly logged and expected, so an ordering regression is
  caught at test time rather than discovered by a downstream consumer in
  production.
- **Sentinel value collision test.** For the in-process sentinel technique,
  write a test that submits a legitimate payload equal in value, though not
  in identity, to whatever the sentinel's underlying representation is, and
  assert the worker still treats it as ordinary data rather than as a
  shutdown signal, which specifically guards against the type-confusion
  failure mode described above.

## 16. Observability signals

- **Dead-letter or quarantine depth.** The count of messages currently sitting
  in the dead-letter destination is the single most direct signal that the
  system is encountering poisoned messages, and both AWS and Azure treat it
  as a first-class metric worth alarming on, with AWS specifically
  documenting how to configure "an alarm for any messages moved to a
  dead-letter queue using Amazon CloudWatch" (Amazon Web Services, *Using
  dead-letter queues in Amazon SQS*,
  [docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
  verified 2026-08-02).
- **Age of the oldest dead-lettered message.** A healthy operational posture
  keeps this age low, meaning the team is actively triaging quarantined
  messages, while a growing age indicates the dead-letter path has become a
  place things go to be forgotten rather than fixed.
- **Delivery or receive count distribution per message.** Tracking how many
  attempts a message needed before either succeeding or being dead-lettered
  distinguishes a system where most failures are transient, a distribution
  clustered near one or two attempts, from one where most failures are
  permanently poisoned messages, a distribution clustered near the maximum
  threshold.
- **Consumer restart or crash-loop counter.** In the unmitigated case, a
  spike in consumer process restarts correlated with a specific message
  identifier is the earliest and most direct evidence that a poison message
  is present, often visible well before a dead-letter metric would even
  exist to alert on.
- **Dead-letter reason code, where the broker exposes one.** Azure Service
  Bus, for instance, attaches a `DeadLetterReason` such as
  `MaxDeliveryCountExceeded` or `TTLExpiredException` to every dead-lettered
  message, letting an operator distinguish a payload-caused poison message
  from an unrelated operational cause such as an expired time-to-live
  without opening the message body at all (Microsoft, *Service Bus
  dead-letter queues*,
  [learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
  verified 2026-08-02).
- **Correlation identifier propagation.** Tagging every message with a
  correlation identifier that survives the move to the dead-letter channel
  lets an operator trace a poisoned message back to the specific producer,
  request, or upstream event that generated it, turning quarantine from a
  dead end into a concrete starting point for a root-cause fix.

## 17. Security and privacy implications

A deliberately crafted, malformed message that reliably crashes every
consumer that attempts to process it is a denial-of-service vector in any
system that lacks a bounded delivery count and a dead-letter path, because an
attacker who can inject even one message onto a shared queue can degrade or
halt processing for every legitimate message behind it. Systems that accept
untrusted input onto a queue an internal consumer fleet processes should
treat the poison-pill failure mode as a security property, not only a
reliability one, and validate that a bounded delivery count and quarantine
destination exist before the queue is exposed to any untrusted producer.

A dead-letter destination is, by design, a durable store of message content
that failed processing, and its content is not automatically expired. Azure's
documentation states this plainly, "there's no automatic cleanup of the DLQ.
Messages remain in the DLQ until you explicitly retrieve them from the DLQ"
(Microsoft, *Service Bus dead-letter queues*,
[learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
verified 2026-08-02). If the original queue's messages carry personally
identifiable or otherwise sensitive data, that same data lands in the
dead-letter destination unchanged, and the dead-letter destination must
receive the same encryption, access control, and retention governance as the
primary queue rather than being treated as a lower-sensitivity debugging
scratch space. Microsoft's own recommendation to include exception detail and
stack trace in the dead-letter reason and description fields (Microsoft,
*Service Bus dead-letter queues*,
[learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
verified 2026-08-02) is genuinely useful for debugging, and it is also worth
noting, as engineering judgement rather than a claim the source itself makes,
that a stack trace can incidentally capture fragments of the very payload
that triggered the exception, so teams should confirm their exception
handling does not log or attach raw sensitive payload content into a field
with weaker access controls than the original message.

The sentinel value itself, in the benign in-process sense, carries no data
and is not ordinarily a security surface. The risk that does exist there is
the same type-confusion failure mode described under failure modes and
misuse, if a sentinel is a plain value rather than a distinct object
identity or a language-level control signal, and an attacker or a buggy
upstream component can produce a value equal to the sentinel, that collision
can be used to trigger an unintended early shutdown of a consumer pool, which
is itself a narrow denial-of-service angle worth closing by using a
distinguished sentinel type rather than an in-band value.

## 18. References

- Amazon Web Services. *Using dead-letter queues in Amazon SQS*.
  [docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
  verified 2026-08-02.
- Microsoft. *Service Bus dead-letter queues*.
  [learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues),
  verified 2026-08-02.
- Microsoft. *BlockingCollection\<T\>.CompleteAdding Method*.
  [learn.microsoft.com/en-us/dotnet/api/system.collections.concurrent.blockingcollection-1.completeadding](https://learn.microsoft.com/en-us/dotnet/api/system.collections.concurrent.blockingcollection-1.completeadding),
  verified 2026-08-02.
- Ajmani, Sameer. *Go Concurrency Patterns. Pipelines and cancellation*. The
  Go Blog. [go.dev/blog/pipelines](https://go.dev/blog/pipelines), verified
  2026-08-02.
- Python Software Foundation. *queue, A synchronized queue class*, Python 3
  documentation. [docs.python.org/3/library/queue.html](https://docs.python.org/3/library/queue.html),
  verified 2026-08-02.
- Rust Project. *std, sync, mpsc*, The Rust Standard Library documentation.
  [doc.rust-lang.org/std/sync/mpsc/index.html](https://doc.rust-lang.org/std/sync/mpsc/index.html),
  verified 2026-08-02.
- Hohpe, Gregor, and Woolf, Bobby. *Dead Letter Channel*, Enterprise
  Integration Patterns.
  [enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html),
  verified 2026-08-02.

## Code examples

Three languages are shown, each compiled or run to completion during
authoring. Python and Go use the queue-consumer shape most commonly meant by
the term. Rust shows the disconnect-based variant, where dropping every
sender plays the role a sentinel value plays in the other two languages. Every
comment is kept to two lines or fewer per the repository's comment policy.

### Python, distinguished sentinel object

```python
import queue
import threading

_SENTINEL = object()  # identity-only marker, never compared with ==


def worker(q: "queue.Queue[object]", results: list) -> None:
    while True:
        item = q.get()
        if item is _SENTINEL:
            q.task_done()
            break
        results.append(item * 2)
        q.task_done()


def run(n_workers: int, n_items: int) -> list:
    q: "queue.Queue[object]" = queue.Queue()
    results: list = []
    threads = [
        threading.Thread(target=worker, args=(q, results))
        for _ in range(n_workers)
    ]
    for t in threads:
        t.start()
    for i in range(n_items):
        q.put(i)
    for _ in threads:
        q.put(_SENTINEL)  # one sentinel per known worker
    for t in threads:
        t.join()
    return results


if __name__ == "__main__":
    out = run(3, 10)
    assert sorted(out) == [i * 2 for i in range(10)]
    print("ok", sorted(out))
```

Run and verified during authoring.

```
$ python3 pp.py
ok [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
```

This example deliberately shows the counted-sentinel variant, since consumer
count is fixed and known here, and marks the sentinel by object identity so it
can never collide with a legitimate integer payload. A production system
targeting Python 3.13 or later would prefer `queue.Queue.shutdown()` and
catching `queue.ShutDown`, which removes the need to reason about sentinel
identity at all (Python Software Foundation, *queue, A synchronized queue
class*, [docs.python.org/3/library/queue.html](https://docs.python.org/3/library/queue.html),
verified 2026-08-02).

### Go, close-channel broadcast

```go
package main

import (
	"fmt"
	"sync"
)

func worker(jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
	defer wg.Done()
	for j := range jobs {
		results <- j * 2
	}
}

func main() {
	jobs := make(chan int, 10)
	results := make(chan int, 10)
	var wg sync.WaitGroup

	for w := 0; w < 3; w++ {
		wg.Add(1)
		go worker(jobs, results, &wg)
	}

	for i := 0; i < 10; i++ {
		jobs <- i
	}
	close(jobs) // broadcast, no sentinel value or count needed

	go func() {
		wg.Wait()
		close(results)
	}()

	sum, count := 0, 0
	for r := range results {
		sum += r
		count++
	}
	fmt.Println("count", count, "sum", sum)
}
```

Run and verified during authoring.

```
$ go run main.go
count 10 sum 90
```

Unlike the Python example, no worker here needs to know how many siblings
exist, and no producer needs to send a counted number of terminating values.
Closing `jobs` is a single state transition every blocked or future receive
on that channel observes at once, which is the specific mechanism Go's own
blog recommends over the counted-sentinel approach (Ajmani, *Go Concurrency
Patterns. Pipelines and cancellation*, [go.dev/blog/pipelines](https://go.dev/blog/pipelines),
verified 2026-08-02).

### Rust, disconnect-as-signal

```rust
use std::sync::mpsc;
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel::<i32>();
    let rx = Arc::new(Mutex::new(rx));
    let (result_tx, result_rx) = mpsc::channel::<i32>();

    let mut handles = Vec::new();
    for _ in 0..3 {
        let rx = Arc::clone(&rx);
        let result_tx = result_tx.clone();
        handles.push(thread::spawn(move || loop {
            let item = { rx.lock().unwrap().recv() };
            match item {
                Ok(v) => result_tx.send(v * 2).unwrap(),
                Err(_) => break, // every Sender dropped, channel disconnected
            }
        }));
    }
    drop(result_tx);

    for i in 0..10 {
        tx.send(i).unwrap();
    }
    drop(tx); // dropping the last sender is the shutdown signal

    for h in handles {
        h.join().unwrap();
    }

    let sum: i32 = result_rx.iter().sum();
    println!("sum {}", sum);
}
```

Run and verified during authoring.

```
$ rustc -O src/main.rs -o pp && ./pp
sum 90
```

There is no sentinel value written into this example at all. Dropping the
last `Sender` is itself the termination signal, which the standard library
documents as the source of the `Err` a blocked `recv()` returns once "the
other half of a channel" has "hung up by being dropped" (Rust Project,
*std, sync, mpsc*, [doc.rust-lang.org/std/sync/mpsc/index.html](https://doc.rust-lang.org/std/sync/mpsc/index.html),
verified 2026-08-02). Rust's ownership model makes the counted-sentinel and
type-confusion failure modes unreachable by construction here, there is no
payload value that could ever be mistaken for a dropped sender.
