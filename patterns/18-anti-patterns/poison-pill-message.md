---
name: Poison Pill Message
slug: poison-pill-message
family: 18-anti-patterns
category: Messaging
aliases: [Poison Message, Toxic Message, Poison Event, Unprocessable Message]
first_described: "Hohpe, Woolf 2003"
maturity: established
related: [dead-letter-channel, invalid-message-channel, idempotent-receiver, retry]
incompatible_with: [infinite-retry, receive-and-delete]
verified: 2026-08-02
---

# Poison Pill Message

## 1. Name, aliases, and lineage

The canonical name in this entry is Poison Pill Message. In message broker
operations the shorter alias **poison message** is common. Azure Architecture
Center uses that term for a malformed or unexpected message that a consumer
cannot handle, and ties its treatment in Azure Service Bus to a maximum delivery
count and the dead-letter queue
(https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/messaging,
verified 2026-08-02). RabbitMQ documentation uses the broker-neutral term
dead-lettered message for messages moved after rejection, expiration, queue
length overflow, or quorum queue delivery-limit breach
(https://www.rabbitmq.com/docs/next/dlx, verified 2026-08-02). Google Cloud
Pub/Sub calls the destination a dead-letter topic and defines a bounded attempt
policy on the subscription
(https://docs.cloud.google.com/pubsub/docs/dead-letter-topics, verified
2026-08-02). Amazon SQS calls the destination a dead-letter queue and configures
movement through a redrive policy with `maxReceiveCount`
(https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html,
verified 2026-08-02).

The lineage is messaging reliability rather than object design. Gregor Hohpe
and Bobby Woolf describe Dead Letter Channel in *Enterprise Integration
Patterns*, Addison-Wesley, 2003, chapter "Messaging Channels", section "Dead
Letter Channel". The public pattern page states the core question as what a
messaging system should do with a message it cannot deliver, and names the
Dead Letter Channel as the place where such a message can be moved
(https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html,
verified 2026-08-02). This entry treats Poison Pill Message as an anti-pattern:
the bad design is allowing one unprocessable message to monopolize normal
delivery instead of routing it to a diagnostic channel after bounded attempts.

The name is overloaded. In concurrent programming, a "poison pill" can mean a
sentinel item placed on a queue to tell workers to stop. That sentinel use is a
valid termination technique when all producers and consumers agree on the
protocol. This entry is not about that sentinel. It is about a business or data
message that repeatedly crashes, rejects, or stalls a consumer because the
message and the consumer contract disagree.

## 2. Problem and context

A messaging system exists to decouple producers from consumers. Producers
publish documents, events, or commands. Consumers pull or receive them, perform
work, and acknowledge success. Most brokers assume transient failure is common:
a process crashes, a network call times out, or a database is briefly
unavailable. In those cases, redelivery is a good default because the same
message may succeed on the next attempt.

A poison pill message is different. The message cannot be processed by the
current consumer as written. The payload may violate the schema. A required
field may be absent. A version marker may be unknown. A numeric value may be
outside a domain range. The consumer may have a deterministic bug for one case.
The downstream service may reject this single business key forever. Redelivery
does not repair those causes. It repeats the same failure.

The anti-pattern appears when the system treats deterministic failure as if it
were transient. The queue redelivers the same record. The consumer reads it,
throws the same exception, refuses the same settlement, and lets the broker put
the record back. If ordering is strict, later messages wait behind the poisoned
one. If many workers compete for the queue, the poison pill consumes worker
slots and log volume while healthy messages age. If the broker hides a message
during a visibility timeout, throughput drops into a rhythm of fetch, fail,
hide, reappear.

The context is any at-least-once delivery system where a message can be retried
after a failed delivery. Azure Service Bus peek-lock mode keeps a message until
the receiver settles it, and redelivers when the lock expires
(https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-message-loss-and-duplicates,
verified 2026-08-02). Amazon SQS keeps a received message hidden during the
visibility timeout, then can redeliver it when the consumer does not delete it,
and the redrive policy can later move it to a dead-letter queue
(https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html,
verified 2026-08-02). Pub/Sub retries messages that are not acknowledged and
can forward them after a configured number of delivery attempts
(https://docs.cloud.google.com/pubsub/docs/handling-failures, verified
2026-08-02).

The key distinction is diagnosis. A normal retry path asks, "Could this work
later?" A poison-pill path asks, "Why can this message never pass this
consumer?" The first question belongs on the hot path. The second belongs in
quarantine with enough context for repair, replay, or deletion.

## 3. Forces

Engineering judgement. The exact balance depends on delivery guarantees,
ordering rules, and business risk. The forces below describe the common
pressure points.

- **Correctness.** Retrying protects against transient failure, but infinite
  retry hides deterministic failure. The pattern favors explicit classification
  over blind persistence.
- **Latency.** A poison pill at the head of an ordered queue increases latency
  for unrelated work. Quarantine favors tail latency for healthy messages.
- **Coupling.** Strict consumers are useful because they reject bad data early.
  They are risky when producer and consumer versions change independently.
- **Consistency.** Dropping a message may lose a business event. Retrying
  forever may block every later event for the same key. The choice must match
  the domain's consistency model.
- **Operability.** A dead-letter path gives operators a concrete object to
  inspect. An infinite redelivery loop gives them heat, noise, and little
  evidence.
- **Cost.** Repeated failures spend compute, broker delivery quota, log
  storage, and on-call time. Quarantine spends storage and tooling for the
  diagnostic path.
- **Team topology.** Producer teams, consumer teams, and platform teams may be
  separate. A poison pill often exposes a contract gap between them, so the
  repair process needs ownership rules.
- **Cognitive load.** Bounded retry plus quarantine is more complex than
  ack-on-success and retry-on-error. It pays off only when failures need later
  handling rather than silent loss.
- **Privacy.** Diagnostic copies can retain sensitive payloads longer than the
  primary queue. Redaction and retention rules must cover the quarantine path.

The anti-pattern sacrifices system throughput and human diagnosis to preserve a
false sense that retry will eventually heal all failure. The corrected design
sacrifices some simplicity so deterministic failure becomes visible and bounded.

## 4. Applicability and non-applicability

Reach for poison-pill handling when these conditions hold.

- A consumer can fail a message without removing it from the source queue.
- The broker or application tracks delivery attempts, receive counts, or a
  similar retry budget.
- Some failures are deterministic for a given message, such as schema
  mismatch, missing tenant state, validation failure, or unsupported version.
- Later messages should keep moving after one record is isolated, subject to
  the ordering rule of the domain.
- Operators or support engineers can inspect, repair, replay, or discard a
  quarantined message under a documented process.
- The system has at-least-once delivery, so duplicate processing and retry are
  already part of the design.

Non-applicability list.

- **No retry path exists.** If the transport is fire-and-forget and cannot
  redeliver, poison-pill handling cannot be built at the consumer alone. Use
  producer-side validation, durable logging, or a broker that supports
  settlement.
- **Loss is explicitly acceptable.** For telemetry sampling, clickstream hints,
  or cache-warming hints, recording every invalid item may cost more than it is
  worth. Engineering judgement: count and drop may be enough when the business
  has accepted loss.
- **Strict total order is non-negotiable.** If every later message is invalid
  until the earlier one is processed, moving the earlier message aside may
  violate the model. Use a stopped partition with an operator runbook rather
  than automatic skip-ahead.
- **The failure is clearly transient.** Network timeout, rate limiting, broker
  failover, or downstream maintenance belongs in retry with backoff, not in
  immediate quarantine.
- **The message is malicious input.** Treat it as a security event, not a normal
  dead-letter item. Preserve evidence, limit access, and avoid replay into
  production until reviewed.
- **The consumer cannot safely expose payloads.** If the message contains
  regulated data and no secure diagnostic store exists, quarantine the envelope
  and metadata while storing the body under stricter controls, or block the
  feature until that path exists.
- **The producer is the only place that can repair it.** If the consumer lacks
  enough context to classify or correct the record, route it back through a
  contract-test process rather than building an ad hoc consumer patch.
- **The queue already has broker-native dead lettering with correct policy.**
  Do not duplicate it in application code unless the broker lacks the metadata
  your operators need.

## 5. Structure

The anti-pattern has five participants.

- **Producer.** Publishes the message. It owns the shape and semantics of the
  payload it sends. In a mature system it also owns contract tests for that
  shape.
- **Source queue or subscription.** Holds work for the consumer. It may track
  receive count, delivery attempt, visibility timeout, lock duration, and
  expiry.
- **Consumer.** Processes the message and decides how to settle it. The consumer
  is the place where deterministic failure becomes observable.
- **Retry policy.** Defines which errors are retried, for how long, with which
  delay, and which terminal action follows exhaustion.
- **Quarantine channel.** A dead-letter queue, dead-letter topic, dead message
  queue, or error topic that receives unprocessable messages plus diagnostic
  metadata.
- **Triage worker.** Human workflow or automated process that examines
  quarantined messages, groups them by cause, repairs safe cases, replays fixed
  records, and deletes records that must not run.

The broken structure lacks a terminal path. The consumer can reject, crash, or
time out, but every route returns to the source queue. The corrected structure
adds a bounded transition from retry to quarantine. It also treats quarantine as
owned production state, not a trash bin.

## 6. ASCII structure diagram

```text
Broken structure

  +----------+       publish        +--------------+
  | Producer | -------------------> | Source queue |
  +----------+                      +------+-------+
                                          |
                                          | deliver
                                          v
                                   +------+-------+
                                   |   Consumer   |
                                   +------+-------+
                                          |
                         fail, reject, or timeout
                                          |
                                          v
                                   +------+-------+
                                   |  Redelivery  |
                                   |  same queue  |
                                   +--------------+

Corrected structure

  +----------+       publish        +--------------+
  | Producer | -------------------> | Source queue |
  +----------+                      +------+-------+
                                          |
                                          | deliver with attempt count
                                          v
                                   +------+-------+
                                   |   Consumer   |
                                   +------+-------+
                                          |
                         retryable |      | terminal
                             error |      | unprocessable
                                   v      v
                            +------+------+-+     +----------------+
                            | Retry policy  | --> | Quarantine     |
                            | bounded       |     | channel        |
                            +---------------+     +-------+--------+
                                                          |
                                                          v
                                                   +------+-------+
                                                   | Triage and   |
                                                   | replay tools |
                                                   +--------------+
```

## 7. Dynamics

The runtime dynamic is a classifier. The system must separate success,
transient failure, deterministic failure, and operator-driven replay.

```text
Producer        Queue           Consumer        Retry policy      Quarantine
   |              |                 |                 |                |
   |-- message -->|                 |                 |                |
   |              |-- deliver ----->|                 |                |
   |              |                 |-- validate ---->|                |
   |              |                 |<-- invalid -----|                |
   |              |                 |                 |                |
   |              |                 |-- classify --------------------->|
   |              |                 |   reason=schema                  |
   |              |                 |   attempts=5                     |
   |              |                 |   source=orders                  |
   |              |                 |                 |                |
   |              |<-- settle source message as terminal --------------|
   |              |                 |                 |                |
   |              |                 |                 |-- inspect ---->|
   |              |                 |                 |<-- repair -----|
   |              |<---------------- replay fixed message -------------|
   |              |                 |                 |                |
```

On a transient error the consumer should not publish to quarantine on the first
failure. It should apply the retry policy. On a deterministic error it should
either dead-letter immediately with a reason code or fail until the broker's
delivery budget moves it. Which approach is better depends on the broker. Azure
Service Bus documents automatic movement to the dead-letter queue after
`MaxDeliveryCount` is exceeded
(https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-messaging-exceptions,
verified 2026-08-02). Pub/Sub documents forwarding to a dead-letter topic after
an approximate configured number of attempts
(https://docs.cloud.google.com/pubsub/docs/handling-failures, verified
2026-08-02). RabbitMQ can dead-letter on explicit reject without requeue, on
expiry, on queue length limit, or when a quorum queue exceeds delivery-limit
(https://www.rabbitmq.com/docs/next/dlx, verified 2026-08-02).

The dangerous dynamic is a cycle where the same unprocessable record returns to
the same code path without any counter, reason, or exit. RabbitMQ documents that
dead-letter cycles can occur and says RabbitMQ detects a cycle and drops the
message if no rejection occurred in the cycle
(https://www.rabbitmq.com/docs/next/dlx, verified 2026-08-02). That is a broker
guardrail, not a substitute for application-level classification.

There is one more runtime detail that separates a useful design from a queue
console full of mystery records. The terminal move must be part of the same
settlement story as the source message. If the consumer publishes a diagnostic
copy and then crashes before acknowledging the source, the next delivery can
create a second diagnostic copy. If it acknowledges the source before the
diagnostic publish succeeds, the evidence can vanish. Broker-native
dead-lettering usually gives the cleanest atomic boundary because the broker
owns the state transition. Where the application must republish, include a
stable diagnostic key made from source, partition or queue, original message ID,
and first failure time. The quarantine writer can then upsert by that key
instead of appending an unbounded series of copies.

## 8. Implementation variants

**Broker-native maximum delivery count.** Configure the queue or subscription
to move a message after a bounded number of failed deliveries. Azure Service Bus
uses `MaxDeliveryCount` for this behavior in queues and subscriptions, with
documentation that messages can move to the dead-letter queue after too many
deliveries
(https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-messaging-exceptions,
verified 2026-08-02). This variant is simple and consistent across consumers
sharing the same source. Its weakness is coarse classification: the broker
knows attempts, not business cause.

**Application classification with explicit dead-lettering.** The consumer
catches known deterministic errors, records a stable reason code, and sends the
message to a quarantine channel or invokes broker settlement that dead-letters
it. This variant gives operators better evidence. Its weakness is that every
consumer must implement the same policy or call a shared library.

**Error topic in stream processing.** Kafka Connect can tolerate errors and
write error context to a configurable dead-letter queue Kafka topic through
`errors.deadletterqueue.topic.name`
(https://kafka.apache.org/26/kafka-connect/user-guide/, verified 2026-08-02).
This works well when source offsets matter and the diagnostic record needs
topic, partition, offset, headers, and conversion context. It can leak sensitive
payloads if message logging is enabled without care. Kafka Connect documentation
warns that including messages in logs can expose sensitive data
(https://kafka.apache.org/26/kafka-connect/user-guide/, verified 2026-08-02).

**Sidecar retry topic or delay queue.** The consumer republishes retryable work
to a delayed topic or delay queue with an incremented attempt field. After the
budget, it writes to quarantine. This variant is portable across brokers. It is
also easy to get wrong because republishing can break ordering, duplicate
headers, or lose broker-native receive counts.

**Stop-the-partition handling.** Ordered streams often cannot skip a bad record
without violating per-key semantics. The consumer pauses the partition, alerts,
and waits for operator action. This is not dead lettering in the hot path. It is
valid when processing record N plus 1 before record N would be wrong.

**Schema-gate before enqueue.** Producers validate messages before publishing,
or an ingress service rejects invalid messages before they enter the broker.
This reduces poison pills but does not remove the need for consumer-side
handling, because version skew and consumer bugs still exist.

**Replay-with-repair workflow.** Quarantine is paired with a tool that edits a
copy, records who changed it, and republishes it with a new message ID or replay
marker. This is safest for business-critical commands. Engineering judgement:
manual editing of raw JSON in a queue console is acceptable for an emergency,
but it should not be the normal repair interface.

**Two-tier quarantine.** Some systems split terminal records into a short-lived
diagnostic queue and a longer-lived case store. The queue keeps broker metadata
and supports replay. The case store groups repeated records under one incident,
links owner, status, and decision, and applies retention by business category.
This variant costs more tooling, but it prevents the dead-letter queue from
becoming both transport and ticket tracker.

## 9. Known production uses

**Azure Service Bus dead-letter queue for poison messages.** Azure Architecture
Center names poison messages as messages the consumer cannot handle because
they are malformed or contain unexpected information, and says `MaxDeliveryCount`
can be used so Service Bus moves the message to the dead-letter queue after too
many receives
(https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/messaging,
verified 2026-08-02). Microsoft Learn also documents a default movement after
ten reads in a Service Bus troubleshooting page
(https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-messaging-exceptions,
verified 2026-08-02).

**Amazon SQS redrive policy and dead-letter queue.** Amazon SQS supports a
dead-letter queue configured by redrive policy. AWS documentation defines
`maxReceiveCount` as the number of receives before a message moves from the
source queue to the dead-letter queue
(https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html,
verified 2026-08-02). This is a named production broker behavior used to keep a
single repeatedly failing message from cycling forever in the source queue.

**Google Cloud Pub/Sub dead-letter topics.** Pub/Sub lets a subscription forward
undeliverable messages to a dead-letter topic after a configured maximum number
of delivery attempts, with values documented between 5 and 100
(https://docs.cloud.google.com/pubsub/docs/dead-letter-topics, verified
2026-08-02). The handling-failures page says Pub/Sub can wrap the original
message and add attributes identifying the source subscription before sending it
to the dead-letter topic
(https://docs.cloud.google.com/pubsub/docs/handling-failures, verified
2026-08-02).

**RabbitMQ dead letter exchanges.** RabbitMQ dead-letters messages when a
consumer rejects without requeue, a message expires, a queue exceeds a length
limit, or a quorum queue exceeds delivery-limit
(https://www.rabbitmq.com/docs/next/dlx, verified 2026-08-02). RabbitMQ also
records death metadata such as first and last death queue and reason in
annotations or headers
(https://www.rabbitmq.com/docs/next/dlx, verified 2026-08-02).

**Apache Kafka Connect error topic.** Kafka Connect can write connector errors
and details of problematic records to a configured DLQ Kafka topic when
`errors.deadletterqueue.topic.name` is set and tolerance allows it
(https://kafka.apache.org/26/kafka-connect/user-guide/, verified 2026-08-02).
This is a production framework use for isolating records that fail conversion,
transforms, or sink processing.

**Solace event brokers dead message queues.** Solace queues can move messages
to a dead message queue when TTL expires, redelivery attempts exceed Max
Redelivery, or the consuming client rejects the message
(https://docs.solace.com/Messaging/Guaranteed-Msg/Queues.htm, verified
2026-08-02). Solace documentation recommends separate DMQs for endpoints that
need them because a shared default DMQ may not reveal which endpoint a message
came from
(https://docs.solace.com/Messaging/Guaranteed-Msg/Queues.htm, verified
2026-08-02).

## 10. Consequences

Engineering judgement. The consequences below follow from operating bounded
retry and quarantine in at-least-once systems.

Positive.

- Healthy messages keep moving after an unprocessable record is isolated.
- Operators get a durable diagnostic object rather than a repeating log line.
- Retry budgets become explicit. That makes incidents easier to reason about.
- Consumer code gains a place to distinguish transient errors from terminal
  validation errors.
- Producer and consumer contract gaps become measurable through reason codes.
- Repair and replay can be audited instead of performed through direct database
  edits.

Negative.

- A dead-letter channel is production state. It needs ownership, retention,
  alarms, access control, and cleanup.
- Moving a message aside can violate ordering if the domain requires strict
  per-key or total order.
- Too-low retry budgets convert transient failures into false poison pills.
- Too-high budgets waste capacity and delay diagnosis.
- A quarantine backlog can become a second queue nobody owns.
- Payload copies in diagnostic stores can expand the privacy blast radius.
- Replay can duplicate side effects unless consumers are idempotent.
- Application-level dead-letter code can diverge across services if no shared
  policy exists.

## 11. Failure modes and misuse

Engineering judgement. These triples name observable symptoms, likely causes,
and fixes that have worked in production-style message systems.

**Symptom.** Queue age rises while consumer CPU and error logs spike, but the
processed count stays flat. **Cause.** One message fails deterministically and
returns to the head of an ordered queue. **Fix.** Configure a maximum delivery
count or stop the partition with an alert, then route the record to quarantine
with source key, attempt count, exception class, and payload hash.

**Symptom.** The same message ID appears in logs every visibility timeout.
**Cause.** The consumer throws before deleting or acknowledging the message, and
no redrive policy is present. **Fix.** Add a redrive policy or broker-native
dead-letter setting, then set an alarm on dead-letter inflow.

**Symptom.** Dead-letter volume jumps after a deployment, with one reason code
dominating. **Cause.** Consumer and producer schema versions diverged, or the
new consumer rejects a field older producers still emit. **Fix.** Roll back or
ship a tolerant reader, replay safe records, and add a contract test to the
producer-consumer boundary.

**Symptom.** Operators replay dead-letter messages and the same records return
to quarantine. **Cause.** The replay tool republishes without repair or without
changing the consumer version. **Fix.** Require a replay decision record: fixed
payload, fixed consumer, or explicit discard. Add a replay count header.

**Symptom.** Dead-letter queue storage grows for weeks with no customer-visible
error after the original incident. **Cause.** Quarantine was treated as disposal
rather than a work queue. **Fix.** Assign service ownership, define retention,
and page on age of oldest quarantined message where business action is needed.

**Symptom.** Sensitive customer payload appears in connector logs and error
topics. **Cause.** Diagnostic logging includes full message bodies. Kafka
Connect documentation warns that enabling message inclusion in logs can log
sensitive information
(https://kafka.apache.org/26/kafka-connect/user-guide/, verified 2026-08-02).
**Fix.** Log identifiers, hashes, schema versions, and reason codes by default.
Gate full payload access behind stricter roles.

**Symptom.** One bad record is skipped and later records for the same account
commit, leaving aggregate state impossible to reconcile. **Cause.** Automatic
dead-lettering was applied to a strict ordering domain. **Fix.** Pause that key
or partition instead of skip-ahead, then repair and resume in order.

**Symptom.** A transient downstream outage produces thousands of dead-lettered
messages. **Cause.** Retry budget is lower than the downstream recovery time,
or terminal classification catches a retryable exception. **Fix.** Separate
error classes, use backoff for transient failures, and test retry policy under a
simulated outage.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Poison-pill quarantine | Infinite retry | Drop on error | Stop-the-partition | Producer validation |
|---|---|---|---|---|---|
| Correctness | Preserves evidence and can replay | Preserves message but blocks progress | Loses evidence unless separately logged | Preserves order and evidence | Prevents many bad records at ingress |
| Latency | Healthy work moves after isolation | Tail latency can grow without bound | Low latency for later work | Later work waits | Low latency if validation is cheap |
| Coupling | Consumer owns classification | Broker and consumer loop blindly | Consumer hides contract gaps | Operator and consumer tightly coupled | Producer and schema registry coupled |
| Consistency | Risk if order matters | Keeps order by blocking | Can violate business history | Strong for ordered domains | Strong before publish, weak for consumer bugs |
| Operability | High with reason codes and replay | Low, same failure repeats | Low unless loss is acceptable | High but labor intensive | High for rejected ingress |
| Cost | Storage plus triage workflow | Compute, logs, and broker churn | Low runtime cost, high audit risk | On-call cost and backlog | Producer CPU and schema governance |
| Team topology | Shared producer-consumer ownership | Ownership unclear during incidents | Consumer team absorbs hidden loss | Platform and domain teams coordinate | Producer team carries more burden |
| Cognitive load | Medium. More states to track | Low code, high incident load | Low code, high audit load | Medium. Requires runbook | Medium. Requires contracts |
| Privacy | Diagnostic copies need controls | Logs may still leak details | Fewer copies, less evidence | Payload remains in source | Validation may inspect payload early |

Reading of the table. Poison-pill quarantine is the default for at-least-once
business messaging where a bad record should be visible and later messages can
proceed. Infinite retry is almost never correct once failure is deterministic.
Drop on error fits disposable telemetry. Stop-the-partition fits domains where
order outranks availability. Producer validation is a companion, not a full
substitute, because consumers still fail.

## 13. Related and incompatible patterns

- **Dead Letter Channel.** The main corrective pattern. The poison pill is the
  failure condition. Dead Letter Channel is the route that removes it from the
  hot path while preserving diagnostic state. Hohpe and Woolf describe Dead
  Letter Channel in *Enterprise Integration Patterns*, Addison-Wesley, 2003,
  chapter "Messaging Channels", section "Dead Letter Channel"
  (https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html,
  verified 2026-08-02).
- **Invalid Message Channel.** Closely related but narrower. Invalid Message
  Channel is for messages that fail validation against an expected format. A
  poison pill can be invalid, but it can also be valid data that triggers a
  deterministic consumer bug.
- **Idempotent Receiver.** Required for replay safety. A quarantined message may
  be processed after partial side effects from earlier failed attempts. The
  receiver must handle duplicates by message ID, business key, or operation ID.
- **Retry with exponential backoff.** Composes before quarantine for transient
  errors. It conflicts when applied to deterministic validation errors without a
  terminal budget.
- **Circuit Breaker.** Protects downstream dependencies from repeated calls
  during an outage. It does not classify an individual message as poisonous.
- **Competing Consumers.** Can reduce the blast radius when one worker dies, but
  it can also spread the same poison pill across workers unless the broker has
  a delivery budget.
- **Receive-and-delete.** Incompatible for business messages that must not be
  lost. Azure Service Bus documentation describes receive-and-delete as removing
  a message as soon as it is delivered, with possible message loss if the
  consumer fails before processing
  (https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-message-loss-and-duplicates,
  verified 2026-08-02).
- **Infinite Retry.** The anti-pattern that keeps poison pills alive on the hot
  path. It conflicts with bounded retry and quarantine.
- **Claim Check.** Useful when quarantined payloads are large or sensitive. Store
  the payload in controlled storage and put a reference plus diagnostics in the
  dead-letter channel.

## 14. Refactoring path in and out

Introducing poison-pill handling into a system that retries forever.

1. Add logging that prints message ID, source, attempt count if available,
   exception class, and a stable reason code. Do not log full payload by
   default.
2. Measure whether repeated failures are transient or deterministic. A simple
   query by message ID and exception class is enough to find the loop.
3. Define terminal error classes. Examples: schema invalid, unsupported version,
   missing required field, forbidden tenant state, permanent downstream reject.
4. Configure broker-native dead lettering where available. For SQS that means a
   redrive policy with `maxReceiveCount`; for Pub/Sub that means a dead-letter
   topic with maximum delivery attempts; for Service Bus that means a maximum
   delivery count and dead-letter handling.
5. Add application classification for known terminal cases. Include reason
   code, source queue or topic, attempt count, original message ID, consumer
   version, schema version, and payload hash.
6. Build a triage view before the first incident. At minimum show counts by
   reason, age of oldest item, first-seen time, and replay eligibility.
7. Add replay tooling with idempotency guardrails. Replays need an operator ID,
   reason, timestamp, and replay count.
8. Add contract tests between producers and consumers for every poison reason
   seen more than once.

Removing the pattern when it stops earning its place.

1. Confirm that quarantined messages are disposable telemetry or a deprecated
   source that no longer needs repair.
2. Keep the metric and reason-code counter, but replace per-message quarantine
   with sampled logging or aggregate counts.
3. Lower retention before deleting the channel, so consumers of that diagnostic
   data have time to migrate.
4. Remove replay tooling only after no operational runbook refers to it.
5. For strict-order domains, replace automatic quarantine with partition pause
   and a repair runbook.

The named refactorings are Extract Function for classification, Replace
Conditional with Polymorphism when each message type has its own validator, and
Introduce Parameter Object for the diagnostic envelope. Engineering judgement:
do the broker policy first if it is a one-line setting, but do not stop there.
A dead-letter queue without reason codes is hard to operate.

## 15. Testing and verification

Engineering judgement. The test target is not the broker alone. It is the
consumer's settlement decision under repeatable failure.

Test the classifier with table-driven cases. Given a message and an exception,
the policy should return one of success, retry, quarantine, pause, or drop. The
test should cover unknown schema version, malformed JSON, missing field,
transient timeout, downstream 429, downstream permanent reject, and replay
attempt.

Test attempt budgets with a fake broker or in-memory queue. Deliver the same
message more times than the configured budget and assert that it leaves the
source and appears in quarantine once. Assert that transient errors retry with
delay and do not dead-letter on the first failure.

Test observability as part of behavior. A quarantined message should carry a
reason code, source, attempt count, original message ID, exception class,
consumer version, and timestamp. Tests should reject a quarantine write that
lacks those fields.

Test replay idempotency. Process a message, simulate a crash after the side
effect but before acknowledgement, then replay it. The second run should not
duplicate the side effect. If the operation cannot be idempotent, replay should
require manual approval and a compensating plan.

Test privacy controls. Full payload access in quarantine should be role-gated.
Unit tests can cover redaction functions, but integration tests should verify
that normal metrics and logs contain only IDs, hashes, and reason codes.

Test broker configuration with a small live environment when possible. SQS,
Pub/Sub, Service Bus, RabbitMQ, Kafka Connect, and Solace have behavior that
depends on queue policy, subscription policy, routing, permissions, and
consumer settlement. A mocked queue will not catch an IAM permission missing on
a Pub/Sub dead-letter topic or a RabbitMQ dead-letter exchange with no routable
queue.

Add one regression test per historical poison reason. The test name should use
the reason code, not the incident number alone. That makes the suite explain
the contract it protects: `missing_order_id_goes_to_quarantine`,
`unknown_schema_version_pauses_partition`, or
`downstream_timeout_retries_before_dead_letter`. When the same reason appears
again after a fix, the failure tells the team which boundary regressed.

## 16. Observability signals

Engineering judgement. A poison-pill design is only healthy when the bad path
is visible, owned, and bounded.

Record these signals.

- Source queue age, depth, and oldest message age.
- Consumer success count, retry count, terminal quarantine count, and drop
  count.
- Repeated failure count grouped by message ID, reason code, exception class,
  schema version, producer, and consumer version.
- Delivery attempt or receive count distribution.
- Dead-letter inflow, outflow, age of oldest quarantined item, and count by
  owner.
- Replay count, replay success count, replay return-to-quarantine count, and
  replay actor.
- Payload redaction failures and unauthorized quarantine access attempts.

A healthy dashboard shows rare quarantine events, clear reason distribution,
short triage age, and no repeated replay loops. It also shows source queue age
recovering after a poison pill is moved aside.

A failing dashboard shows source age rising while the same message ID or payload
hash dominates errors. Another failure shape is a quiet source queue paired with
a dead-letter queue whose oldest item is weeks old. That means the hot path is
protected, but the business problem has been abandoned.

Alerting should use both rate and age. Rate catches a bad deployment. Age
catches forgotten work. Engineering judgement: page on dead-letter rate only
when business work is blocked or loss risk exists. Use tickets or daily review
for low-rate invalid telemetry.

Dashboards should also separate first failures from terminal failures. A high
first-failure count with low terminal count means retry is doing useful work. A
low first-failure count with high terminal count means the same small set of
messages is burning through the budget. That distinction prevents teams from
tuning retry delay when the real problem is a contract break.

## 17. Security and privacy implications

Poison-pill handling opens a second data path. The same payload that entered the
source queue may now be stored in a dead-letter queue, error topic, log entry,
ticket, export file, or replay tool. That copy can outlive the original
retention window unless policy says otherwise.

Access to quarantine should be narrower than access to metrics. Operators often
need reason codes, counts, IDs, schema versions, and hashes. They do not always
need full payload bodies. Where payload inspection is required, record who
viewed it and why.

Replay is a privileged action. A replay can repeat a payment, send another
email, reopen an order, or overwrite state. Use idempotency keys, replay
markers, and approval for high-risk message types. A replay tool should never
let an operator edit a payload without retaining the original, the change, and
the actor.

Malformed messages can be attack input. A parser crash, decompression bomb,
oversized field, or path traversal string should not be treated as ordinary
business invalidity. The consumer should bound payload size, parse with safe
libraries, and route suspicious cases into a security process rather than
automatic replay.

Dead-letter routing itself can lose data if misconfigured. RabbitMQ documents
that dead-lettering republishes messages and can fail in clustered scenarios,
and that quorum queues support at-least-once dead-lettering with publisher
confirms
(https://www.rabbitmq.com/docs/next/dlx, verified 2026-08-02). Pub/Sub
requires permissions for its service account to publish to the dead-letter topic
and acknowledge messages from the source subscription
(https://docs.cloud.google.com/pubsub/docs/dead-letter-topics, verified
2026-08-02). Those are security controls and reliability controls at the same
time.

## Code examples

Three languages are shown because the pattern is less about syntax than about a
settlement decision. TypeScript shows a web-service style classifier. Python
shows table-driven processing with clear reason codes. Go shows typed errors
and explicit message movement. Java, Rust, and Swift are omitted because these
three examples cover the broker-independent mechanics with less ceremony.

### TypeScript

```typescript
type Message = {
  id: string;
  attempts: number;
  body: unknown;
};

type Outcome =
  | { kind: "ack" }
  | { kind: "retry"; delayMs: number }
  | { kind: "quarantine"; reason: string };

function classify(message: Message): Outcome {
  if (typeof message.body !== "object" || message.body === null) {
    return { kind: "quarantine", reason: "body_not_object" };
  }
  const body = message.body as Record<string, unknown>;
  if (typeof body.orderId !== "string") {
    if (message.attempts < 5) {
      return { kind: "retry", delayMs: 1000 };
    }
    return { kind: "quarantine", reason: "missing_order_id" };
  }
  return { kind: "ack" };
}

const messages: Message[] = [
  { id: "m1", attempts: 1, body: { orderId: "o-1" } },
  { id: "m2", attempts: 1, body: { total: 10 } },
  { id: "m3", attempts: 5, body: { orderId: "o-3" } },
];

for (const message of messages) {
  const outcome = classify(message);
  console.log(message.id, outcome.kind);
}
```

### Python

```python
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Message:
    message_id: str
    attempts: int
    body: dict[str, Any]


def classify(message: Message) -> tuple[str, str | None]:
    if "order_id" not in message.body:
        return ("quarantine", "missing_order_id")
    if message.attempts >= 5:
        return ("quarantine", "retry_budget_exhausted")
    if message.body.get("transient") is True:
        return ("retry", "downstream_timeout")
    return ("ack", None)


queue = [
    Message("m1", 1, {"order_id": "o-1"}),
    Message("m2", 2, {"transient": True, "order_id": "o-2"}),
    Message("m3", 1, {"total": 10}),
]

for item in queue:
    action, reason = classify(item)
    print(item.message_id, action, reason or "ok")
```

### Go

```go
package main

import (
	"errors"
	"fmt"
)

type Message struct {
	ID       string
	Attempts int
	Body     map[string]string
}

var ErrMissingOrderID = errors.New("missing_order_id")

func process(message Message) error {
	if message.Body["order_id"] == "" {
		return ErrMissingOrderID
	}
	return nil
}

func settle(message Message) string {
	err := process(message)
	if err == nil {
		return "ack"
	}
	if errors.Is(err, ErrMissingOrderID) || message.Attempts >= 5 {
		return "quarantine"
	}
	return "retry"
}

func main() {
	messages := []Message{
		{ID: "m1", Attempts: 1, Body: map[string]string{"order_id": "o-1"}},
		{ID: "m2", Attempts: 1, Body: map[string]string{}},
		{ID: "m3", Attempts: 5, Body: map[string]string{"order_id": "o-3"}},
	}
	for _, message := range messages {
		fmt.Println(message.ID, settle(message))
	}
}
```

## 18. References

1. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns*. Addison-Wesley,
   2003. Chapter "Messaging Channels", section "Dead Letter Channel". Public
   pattern page:
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html
   Verified 2026-08-02. Source for Dead Letter Channel lineage and messaging
   terminology.
2. Microsoft. *Asynchronous messaging options*. Azure Architecture Center.
   Section "Dead-letter queue".
   https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/messaging
   Verified 2026-08-02. Source for the Azure poison message definition and
   Service Bus DLQ handling description.
3. Microsoft. *Prevent message loss and duplicate processing in Azure Service
   Bus*. Section "Where missing messages actually go".
   https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-message-loss-and-duplicates
   Verified 2026-08-02. Source for peek-lock and receive-and-delete behavior.
4. Microsoft. *Messaging exceptions*. Azure Service Bus.
   https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-messaging-exceptions
   Verified 2026-08-02. Source for default dead-letter movement after repeated
   reads and Service Bus troubleshooting signals.
5. Amazon Web Services. *Using dead-letter queues in Amazon SQS*. Amazon Simple
   Queue Service Developer Guide.
   https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
   Verified 2026-08-02. Source for SQS redrive policy and `maxReceiveCount`.
6. Google Cloud. *Dead-letter topics*. Pub/Sub documentation.
   https://docs.cloud.google.com/pubsub/docs/dead-letter-topics
   Verified 2026-08-02. Source for Pub/Sub dead-letter topic configuration,
   delivery attempt limits, and permissions.
7. Google Cloud. *Handle message failures*. Pub/Sub documentation.
   https://docs.cloud.google.com/pubsub/docs/handling-failures
   Verified 2026-08-02. Source for Pub/Sub forwarding behavior and wrapped
   dead-letter message attributes.
8. Broadcom. *RabbitMQ Dead Letter Exchanges*. RabbitMQ documentation.
   https://www.rabbitmq.com/docs/next/dlx
   Verified 2026-08-02. Source for RabbitMQ dead-letter triggers, cycle
   behavior, headers, and safety notes.
9. Apache Software Foundation. *Kafka Connect User Guide*, version 2.6,
   section "Error Reporting in Connect".
   https://kafka.apache.org/26/kafka-connect/user-guide/
   Verified 2026-08-02. Source for Kafka Connect DLQ topic configuration and
   sensitive logging warning.
10. Solace. *Queues*. Solace documentation, section "Dead Message Queues".
    https://docs.solace.com/Messaging/Guaranteed-Msg/Queues.htm
    Verified 2026-08-02. Source for Solace DMQ behavior, Max Redelivery, and
    endpoint-specific DMQ guidance.
