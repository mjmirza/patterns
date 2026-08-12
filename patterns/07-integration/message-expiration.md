---
name: Message Expiration
slug: message-expiration
family: 07-integration
category: Integration
aliases: [Time to Live, TTL Messaging, Message TTL]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [dead-letter-channel, guaranteed-delivery, invalid-message-channel, publish-subscribe-channel, request-reply, transactional-client]
incompatible_with: []
verified: 2026-08-02
---

# Message Expiration

## 1. Name, aliases, and lineage

The canonical name is Message Expiration. It is documented as one of the
messaging patterns in Gregor Hohpe and Bobby Woolf, *Enterprise Integration
Patterns. Designing, Building, and Deploying Messaging Solutions*,
Addison-Wesley, 2003, in the Messaging Channels chapter. The pattern's own
reference page states the problem plainly. "If a Message's data or request is
not received by a certain time, it is useless and should be ignored"
([enterpriseintegrationpatterns.com, Message Expiration](https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageExpiration.html),
verified 2026-08-02). The solution the page states is equally direct. "Set the
Message Expiration to specify a time limit how long the message is viable",
after which the messaging system should stop delivering an unconsumed message
(same source, verified 2026-08-02).

The pattern is widely known by the name of the mechanism that implements it
rather than by its catalog name. Practitioners say Time to Live or TTL far more
often than they say Message Expiration, because every mainstream broker
exposes the concept as a TTL property on either the message or the destination.
AMQP 0-9-1 (the protocol RabbitMQ implements) names the per-message field
`expiration`, JMS names the concept `JMSExpiration`, Azure Service Bus names it
`TimeToLive`, and Amazon SQS names the queue-level version
`MessageRetentionPeriod`. None of these vendor names appear in the original
1994-2003 pattern literature. Message TTL is the informal alias used across
almost all broker documentation and is treated here as fully interchangeable
with the catalog name.

The pattern sits in a small family with Guaranteed Delivery, Dead Letter
Channel, and Invalid Message Channel, all of which are concerned with what
happens to a message that the receiver cannot, or should not, act on normally.
Message Expiration is the only one of that family that is driven by a clock
rather than by a delivery outcome or a content defect.

## 2. Problem and context

A message carries a request or a piece of data across an asynchronous boundary.
The sender does not know, and generally cannot know, exactly when the receiver
will process it. In a synchronous call the caller blocks and the request either
completes or the caller gives up and moves on. In an asynchronous, queued
system there is no caller sitting on a stack frame waiting. The message sits in
a channel, potentially for seconds, potentially for hours, until a consumer
becomes available and reads it.

For a large class of messages that delay is harmless. A row inserted into a
warehouse export queue is just as correct an hour late as it is a second late.
For another class of messages the delay changes the request's meaning
entirely. A stock quote is a statement about the market at the instant it was
produced. A one time login code is only useful for the few minutes a person is
expected to still be looking at their phone. A cache invalidation event that
arrives after the cache entry has already been overwritten by a newer value
does nothing useful and can actively cause a stale write if applied blindly. A
saga step that times out on the business side but whose compensating action
message is still sitting in a queue an hour later would, if delivered, run a
compensation against a saga that already finished successfully through a
different path.

The context in which this problem is real, not hypothetical, is any system
where consumers can fall behind. A single slow consumer, a partition outage, a
downstream dependency degradation, a deployment that drains a consumer group
for several minutes, or simple backpressure under load, all produce the same
symptom. a growing backlog of messages whose age keeps increasing. Once a
backlog exists, the question of whether an old message is still worth
processing stops being academic. Processing every message in a backlog exactly
as if it had just arrived is often the wrong choice, and it is frequently the
choice that turns a brief outage into a much longer one, because the consumer
spends its recovered capacity working through stale, low value work instead of
current, high value work.

## 3. Forces

**Freshness versus completeness.** Every message dropped for being stale is a
message that will never be processed. The pattern trades completeness of
delivery for freshness of what does get delivered. A system that cannot
tolerate any data loss, financial ledger postings being the sharpest example,
must not apply expiration to those messages, or must route expired instances to
a durable holding area rather than discard them.

**Consumer relief versus silent loss.** A short TTL protects a struggling
consumer from working through an ever growing backlog of work whose value has
already decayed. Set too aggressively, the same TTL silently discards requests
that a slightly slower but still correct consumer would have handled fine. The
forces pull against each other. more protection for the consumer means less
tolerance for its own slowness.

**Producer knowledge versus broker uniformity.** The producer usually knows
best how long its own message stays useful, a login code, a quote, a
partial page render fragment. Setting TTL per message respects that knowledge
but pushes a decision, and a maintenance burden, onto every producer. Setting
TTL uniformly per queue or per topic is simpler to operate and reason about but
forces every message type flowing through that channel into one expiration
policy, which is wrong for at least some of them.

**Latency of expiry checking versus throughput.** Checking a message's
expiration on every dequeue is a per message cost. Broker implementations that
prioritize throughput, notably Kafka's segment based deletion described in
dimension 8, accept much coarser expiry granularity, whole segment files at a
time, in exchange for avoiding a per message check entirely.

**Silent discard versus dead lettering.** Simply dropping an expired message is
cheap and keeps the operational picture clean, nothing to look at, nothing left
behind. Routing it to a Dead Letter Channel instead preserves an audit trail
and lets an operator or a batch job decide later whether the message still has
value, at the cost of a channel that itself needs monitoring, and a discipline
to keep it from becoming an unbounded, ignored graveyard.

**Cost and coupling.** A retained, undelivered message occupies broker storage
and, in cloud managed services, is billed for that storage. Enterprise
Integration Patterns frames this pattern's relevance explicitly around load,
and vendor documentation for Amazon SQS and Azure Service Bus both foreground
the storage and cost angle alongside the correctness angle.

## 4. Applicability and non-applicability

Reach for Message Expiration when:

- The value of a message decays measurably with time, and processing it after
  that decay point is either useless or actively wrong. Stock quotes,
  one-time codes, live location updates, cache invalidation events.
- A slow or recovering consumer needs protection from a backlog of stale
  requests so it can spend its capacity on current work rather than working
  chronologically through everything that piled up.
- The system already has a correctness backstop, most often idempotent
  processing or Guaranteed Delivery on the messages that must not be lost, so
  that expiring the ones that can safely be dropped does not put the whole
  system at risk.
- A request-reply exchange needs a bound on how long the requester will wait
  for a reply before treating the request as failed and freeing whatever
  resource, a correlation table entry, a lock, a UI spinner, was held open
  waiting for it.
- Development and test environments accumulate stranded messages from partial
  runs, and an automatic cleanup is cheaper than manual queue purging. Azure
  Service Bus documentation names exactly this as a first class use case
  ([Message Expiration and TTL, Microsoft Learn](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-expiration),
  verified 2026-08-02).

Do NOT reach for it when:

- The message represents an action that must eventually happen regardless of
  delay, a financial transaction, an order fulfillment step, an audit log
  entry. Expiring these converts a delay into permanent data loss, and the
  pattern's own reference page is explicit that expired messages should
  usually go to a Dead Letter Channel or be discarded, neither of which is
  "still eventually delivered".
- The receiver has no way to detect, and no business process to handle, the
  fact that a message never arrived. A silently dropped expired message that
  nothing downstream ever notices or compensates for is a correctness bug
  wearing the pattern's clothing.
- The real problem is a slow or under-provisioned consumer and the correct fix
  is scaling the consumer, adding partitions, or fixing a downstream
  dependency. Expiration hides consumer capacity problems by discarding the
  evidence of them rather than fixing them.
- The TTL value cannot be chosen with any confidence, because nobody actually
  knows how long a message stays useful. A guessed TTL is worse than no TTL,
  because it produces unpredictable, hard to reproduce loss under exactly the
  load conditions, a backlog, where correctness matters most.
- A regulatory or audit requirement mandates that every request be retained or
  logged regardless of outcome. Expiration that silently discards a message
  can conflict directly with that requirement unless every expired message is
  captured elsewhere first.

## 5. Structure

- **Producer.** Sets an expiration value on the message it sends, or relies on
  a destination-level default it does not control per message. The producer is
  the participant with the best knowledge of how long the message's content
  stays valid.
- **Message.** Carries the expiration value as metadata, either an absolute
  timestamp after which it is invalid, or a duration relative to the time it
  was accepted by the broker, from which the broker computes the absolute
  instant.
- **Channel or destination (queue, topic, partition).** Optionally carries a
  destination-level default expiration that applies to any message that does
  not set its own, and optionally a maximum expiration bound that caps
  whatever the producer requested.
- **Message broker or expiry enforcer.** The component that actually decides a
  message is expired and acts on that decision. This can be the broker's
  delivery path (checked at the moment of dequeue or delivery attempt), a
  background reaper process that periodically sweeps the channel, or, in
  Kafka's case, the log cleaner that deletes whole segment files once every
  message in the segment is past the retention window.
- **Consumer.** Never sees a genuinely expired message under correct broker
  behavior, because the broker's contract is that it will not deliver a
  message past its expiration. The consumer's role in the pattern is passive.
  it benefits from never being handed stale work, but it does not implement
  any of the expiration logic itself.
- **Dead Letter Channel (optional participant).** Receives messages the broker
  determined were expired, when the deployment chooses to preserve rather than
  silently discard them. This is the same Dead Letter Channel used for
  malformed or undeliverable messages, and a consumer of that channel usually
  needs to inspect a reason code to tell an expired message apart from other
  kinds of dead letter.

## 6. ASCII structure diagram

```
+-----------+        +--------------------------+        +-----------+
| Producer  |------->| Channel / Destination     |------->| Consumer  |
|           |  msg + |  - holds messages         |  msg   |           |
|           |  TTL   |  - default/max TTL policy |        | (never   |
+-----------+        +-----------+--------------+        |  sees an  |
                                  |                        |  expired  |
                                  | expiry check            |  message) |
                                  v                        +-----------+
                      +--------------------------+
                      | Expiry Enforcer           |
                      |  - checked at delivery, or |
                      |  - swept by a reaper, or   |
                      |  - segment-deleted (Kafka) |
                      +-----------+--------------+
                                  |
                        expired?  | yes
                                  v
                      +--------------------------+
                      | discard  OR route to      |
                      | Dead Letter Channel        |
                      +--------------------------+
```

## 7. Dynamics

The two dynamics that matter are how a message gets marked and how the broker
decides, at each point of contact, whether that mark still holds.

```
Producer                 Channel                    Consumer
   |                        |                           |
   |--publish(msg, ttl=T)-->|                           |
   |                        | expires_at = now() + T   |
   |                        | (or use msg's absolute    |
   |                        |  expiration if set)       |
   |                        |                           |
   |                        |<---- time passes -------->|
   |                        |                           |
   |                        |--poll()------------------>|
   |                        | if now() > expires_at:    |
   |                        |   do NOT deliver           |
   |                        |   discard OR DLQ           |
   |                        | else:                      |
   |                        |   deliver(msg)------------>|
   |                        |                           | process(msg)
```

A second, subtler dynamic governs systems that check expiration only at
enqueue time or only periodically, rather than at every delivery attempt. This
is the shape RabbitMQ and Azure Service Bus both document explicitly.

```
time -->

t0: message enqueued, TTL = 30s, expires_at = t0 + 30s
t5: consumer polls, message age 5s, delivered normally
t35: message age 35s, PAST expiry, but consumer has not polled
     since t30 -- the broker has NOT yet acted on the expiry
t40: reaper sweep (or next poll attempt) runs
     broker checks: now() > expires_at? yes.
     message removed / routed to DLQ at t40, not at t35.
```

This lag between the logical expiry instant and the moment the broker actually
acts on it is not a bug. it is a deliberate throughput trade-off that RabbitMQ,
Azure Service Bus, and Kafka all make in different ways, documented in
dimension 8.

## 8. Implementation variants

**Per-message expiration, checked at delivery.** The producer stamps each
message with its own TTL or absolute expiry. The broker checks this stamp at
the moment it is about to hand the message to a consumer, and skips delivery,
discarding or dead-lettering the message, if the check fails. This is JMS's
`JMSExpiration` field and RabbitMQ's per-message `expiration` property.
RabbitMQ's own documentation states that the server guarantees expired
messages "will not be delivered using `basic.deliver`" to a consumer or
returned to a polling client
([RabbitMQ TTL Extensions](https://www.rabbitmq.com/docs/ttl), verified
2026-08-02), while also noting the actual removal happens "at or shortly after"
the TTL based expiry, not necessarily at the exact instant, because RabbitMQ
only guarantees non-delivery, not immediate physical removal.

**Per-destination default expiration.** The queue, topic, or subscription
carries a default TTL applied to any message that does not set its own,
frequently paired with a maximum that bounds whatever a producer requests.
Azure Service Bus implements exactly this shape. its documentation states the
entity-level default also functions as an upper bound on the time-to-live
value, and that a longer per-message TTL is silently reduced to the entity
default before the message is enqueued
([Azure Service Bus, Message Expiration and TTL](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-expiration),
verified 2026-08-02). RabbitMQ has the mirror image policy. when both a
per-queue and a per-message TTL are present, "the lower value between the two
will be chosen" (same RabbitMQ source as above).

**Retention-window expiration on the destination as a whole.** Rather than
tracking each message's own clock, the channel simply discards anything older
than a fixed window, uniformly, regardless of what the producer asked for.
Amazon SQS implements this as `MessageRetentionPeriod`, configurable from one
minute to fourteen days with a four day default, after which "the message is
automatically deleted" from the queue with no notification sent
([AWS SQS message lifecycle, AWS Documentation](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-message-lifecycle.html),
verified 2026-08-02). This variant sacrifices per-message granularity
entirely, trading it for a much simpler, uniformly enforceable policy.

**Segment based, batch expiration (Kafka).** Kafka's log based model makes
per-message expiration prohibitively expensive at the throughput Kafka targets,
so it does not check individual messages at all. It deletes entire immutable
log segment files once every record in that segment is older than the
configured `retention.ms`, whose documented default is 604,800,000
milliseconds, seven days
([Confluent, Kafka topic configuration reference](https://docs.confluent.io/platform/current/installation/configuration/topic-configs.html),
verified 2026-08-02). Deletion is deliberately coarse. "retention and cleaning
is always done a file at a time" rather than message at a time (same source).
This is the same underlying pattern, a time boundary past which a message is no
longer delivered, implemented with a batch granularity appropriate to a log
structured, append only storage engine rather than a per-message queue.

**Language and framework idiomatic shapes.** In practice this pattern rarely
needs bespoke application code, because it is implemented as broker
configuration or a header field rather than a control flow structure. Where
application code does participate, it is almost always in one of two shapes.
setting the TTL header when constructing an outbound message (a producer side
concern, shown for TypeScript, Python, and Go below), or checking a received
message's own embedded expiry timestamp before acting on it, which matters
whenever a message can sit in an application level queue, retry buffer, or
outbox table after the broker has already delivered it once.

## 9. Known production uses

1. **RabbitMQ, per-message and per-queue TTL.** RabbitMQ implements both a
   `x-message-ttl` queue argument and a per-message `expiration` property,
   with documented interaction rules for when both are present, and supports
   routing expired messages to a dead letter exchange for both classic and
   quorum queue types
   ([RabbitMQ TTL Extensions documentation](https://www.rabbitmq.com/docs/ttl),
   verified 2026-08-02).
2. **Amazon SQS, MessageRetentionPeriod.** Every standard and FIFO SQS queue
   enforces a configurable retention period, one minute to fourteen days, four
   days by default, past which a message is deleted from the queue with no
   further notice
   ([AWS SQS message lifecycle documentation](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-message-lifecycle.html),
   verified 2026-08-02).
3. **Azure Service Bus, TimeToLive.** Azure Service Bus supports both a
   per-message `TimeToLive` and an entity-level default that acts as a
   maximum, with an explicit, documented option to move expired messages to a
   dead-letter queue instead of dropping them, distinguishable from other
   dead-lettered messages by a dead-letter reason property
   ([Azure Service Bus, Message Expiration and TTL Explained, Microsoft Learn](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-expiration),
   verified 2026-08-02).
4. **Apache Kafka, retention.ms and segment deletion.** Kafka enforces message
   lifetime through topic level `retention.ms`, defaulting to seven days, by
   deleting whole log segment files once every record in them has aged past
   the window, an approach the documentation explicitly frames as more
   efficient than message-by-message deletion
   ([Confluent, Kafka topic configuration reference](https://docs.confluent.io/platform/current/installation/configuration/topic-configs.html),
   verified 2026-08-02).
5. **Amazon EventBridge.** Event Bridge event buses support time-based and
   retry-attempt-based expiration for events routed through rules, per the
   Enterprise Integration Patterns reference page's own listing of modern
   implementations of this pattern
   ([enterpriseintegrationpatterns.com, Message Expiration](https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageExpiration.html),
   verified 2026-08-02).
6. **Google Cloud Pub/Sub.** Pub/Sub subscriptions support a configurable
   message retention duration, documented by the same Enterprise Integration
   Patterns reference page as offering retention windows up to 31 days
   (same source as above, verified 2026-08-02).

## 10. Consequences

**Positive.**

- Bounds the amount of stale work a consumer can be handed, so recovery from a
  backlog spends capacity on current work rather than working through a
  chronologically ordered queue of increasingly irrelevant messages.
- Bounds resource holding time on the producer or requester side in
  request-reply exchanges, freeing correlation table entries, locks, and
  in-memory state that would otherwise wait indefinitely for a reply that will
  never usefully arrive.
- Bounds storage cost and, in managed cloud brokers, the billed cost of
  retaining undelivered messages indefinitely.
- Gives operators an automatic cleanup mechanism for stranded messages in
  development, test, and demo environments, avoiding manual queue purging.
- When paired with a Dead Letter Channel, produces a visible, inspectable
  signal that something is systemically too slow, rather than a silent,
  invisible backlog that only shows up as vague complaints of staleness.

**Negative.**

- Introduces silent, permanent data loss for any message class where that loss
  was not deliberately acceptable. This is the single most common misuse of
  the pattern, applying a convenient default TTL to a message type where
  losing it is actually a correctness bug.
- Makes system behavior time and load dependent in a way that is hard to
  reproduce. a bug that only manifests when a consumer falls more than N
  seconds behind is difficult to catch in normal testing and often first shows
  up in production during exactly the incident where correct behavior matters
  most.
- Shifts a design decision, how stale is too stale, onto whichever engineer
  configures the TTL, often without the business context to make that call
  correctly, and rarely revisited once set.
- Adds an operational surface, expiration counts, dead letter volume from
  expiry, that must itself be monitored, or the pattern degrades from "protects
  the consumer" to "silently and invisibly drops requests" with nobody
  watching.
- The delivery-time check variant (RabbitMQ, JMS style) and the batch segment
  variant (Kafka) diverge in latency between logical expiry and actual
  removal in a way that surfaces as confusing behavior, an "expired" message
  still returned by a peek or browse operation, if that distinction is not
  understood by whoever is debugging it.

## 11. Failure modes and misuse

This dimension is largely engineering judgement drawn from the documented
broker behaviors above and from the general shape of production incidents
involving time-bounded messaging.

- **Symptom.** A consumer reports processing far fewer messages than the
  producer reports sending, with no errors logged anywhere.
  **Cause.** Expired messages are being silently discarded rather than
  dead-lettered, and nothing is monitoring the discard count, so the loss is
  invisible until someone reconciles counts across the two ends.
  **Fix.** Route expired messages to a Dead Letter Channel, even if only for a
  short retention window, and alert on a nonzero or rising expiry rate rather
  than only on hard delivery failures.

- **Symptom.** A message is delivered to a consumer, the consumer processes
  it, and only afterward someone notices the message's own embedded timestamp
  was already stale by the time it was acted on.
  **Cause.** The broker's TTL was set generously, or was not set at all, and
  the application never independently checked the message's own business
  timestamp before acting on it. Broker level TTL protects against the broker
  holding a message too long. it does nothing about a message that was already
  stale the instant it was produced, or that took an unusually slow path
  through several intermediate hops before reaching the final consumer.
  **Fix.** When staleness genuinely matters to correctness, check it in
  application code against the message's own embedded production timestamp,
  do not rely on broker TTL alone as the only guard.

- **Symptom.** A `peek` or browse operation on a queue returns a message that
  the application believes has already expired, or a message count that does
  not match what is actually deliverable.
  **Cause.** The broker enforces expiration lazily, at delivery time or via a
  periodic sweep, not the instant the clock crosses the expiry threshold.
  RabbitMQ documents removal happening "at or shortly after" expiry, not
  exactly at expiry, and Azure Service Bus documents that the broker "might
  choose to lazily expire" messages and that peek operations can surface
  already-expired messages before the broker has acted on them.
  **Fix.** Treat expiry as a guarantee about non-delivery to a consumer, not a
  guarantee about immediate physical removal or an accurate live count. Do not
  build logic that depends on the exact instant of removal.

- **Symptom.** Setting a TTL on an existing, already-populated RabbitMQ queue
  via a policy change does not immediately shrink the queue depth the way an
  operator expected.
  **Cause.** RabbitMQ's documented behavior is that when TTL is retroactively
  applied via a policy change, expired messages are only actually discarded
  once they reach the head of the queue, which can be arbitrarily delayed if
  the queue is not being actively consumed.
  **Fix.** Do not rely on a retroactive TTL policy change to free space on a
  stalled queue quickly. actively drain or purge the queue if immediate space
  recovery is the goal.

- **Symptom.** A producer sets a generous, application-appropriate TTL, and
  messages still expire far sooner than expected.
  **Cause.** A destination-level maximum silently reduced it. Azure Service
  Bus explicitly documents that a per-message TTL longer than the entity's
  default is silently adjusted down to the entity default before enqueueing,
  with no error raised to the producer.
  **Fix.** Check the destination's own default and maximum TTL settings before
  assuming a per-message value will be honored as requested, and treat a
  silent downgrade as something to surface in monitoring, not assume away.

- **Symptom.** An idempotent-looking retry or saga compensation message
  arrives and is processed long after the original transaction already
  completed successfully through another path, producing a duplicate or
  conflicting effect.
  **Cause.** No expiration was applied to time-sensitive workflow or saga
  messages at all, on the (often unstated) assumption that guaranteed delivery
  alone was sufficient, when what was actually needed was guaranteed delivery
  bounded by a business-relevant deadline.
  **Fix.** For saga and workflow steps with a real business deadline, pair
  Message Expiration with a check on the receiving end for whether the
  workflow instance the message references is still in a state where the
  message applies, do not assume delivery within any TTL means the
  message is still actionable.

## 12. Trade-off matrix

| Concern | Message Expiration | Guaranteed Delivery alone | Dead Letter Channel alone | Consumer-side manual staleness check |
|---|---|---|---|---|
| Correctness under backlog | Protects consumer from stale work automatically | No protection, consumer works through everything in order regardless of age | Captures failures but does not prevent stale processing before failure | Protects correctness but only if every consumer implements the check consistently |
| Risk of silent data loss | Real, unless paired with dead lettering | None, by definition | None, by definition, that is its purpose | None, decision stays explicit in application code |
| Operational complexity | Low, broker-native configuration in most systems | Low, broker-native, but does not address staleness | Medium, needs its own monitoring and eventual disposition process | Higher, must be implemented and kept consistent per consumer, per message type |
| Granularity | Per-message or per-destination, broker dependent | Not applicable to this concern | Not applicable to this concern | Fully custom, whatever the application checks |
| Timeliness of enforcement | Broker enforced, consistent across all consumers automatically | Not applicable | Reactive, after delivery already failed for another reason | Only as timely as every consumer's own implementation |
| Best fit | Freshness-sensitive messages where some loss is acceptable | Messages that must never be lost regardless of age | Any undeliverable message, expired or otherwise malformed | Business-critical staleness rules too specific for a generic broker TTL to express |

## 13. Related and incompatible patterns

- **Dead Letter Channel.** The natural companion when discarding an expired
  message silently is unacceptable. Expired messages route there instead of
  vanishing, and Azure Service Bus and RabbitMQ both implement this pairing
  natively with a distinguishable reason code so an operator can tell an
  expired message apart from a malformed or rejected one.
- **Guaranteed Delivery.** These two patterns are in genuine tension and must
  be applied deliberately, never by accident, to the same message. Guaranteed
  Delivery promises a message will eventually be delivered. Message
  Expiration promises the opposite, that it will stop being delivered past a
  point. A system applying both to the same message class needs an explicit
  decision about which one wins, usually resolved by scoping Guaranteed
  Delivery to the messages that must never be lost and Message Expiration to
  the messages where staleness is the bigger risk.
- **Invalid Message Channel.** A close sibling in the sense that both are
  routes for a message the normal consumer should not process, one because its
  content is malformed, the other because its timing is wrong. Systems that
  already have an Invalid Message Channel frequently reuse the same
  destination, or the same Dead Letter Channel, for both, distinguished by
  reason code.
- **Request-Reply.** Message Expiration is how a Request-Reply exchange
  implements a request timeout in an asynchronous, queue based setting. the
  requester's own local timeout on waiting for a reply is the mirror image of
  the broker's TTL on the request message itself, and a well designed
  Request-Reply implementation coordinates the two rather than letting them
  drift independently.
- **Publish-Subscribe Channel.** Retention windows on a topic (Kafka's
  `retention.ms`, Pub/Sub's retention duration) are a topic-scoped instance of
  this pattern, determining how long a late-joining or slow subscriber can
  still catch up on messages it has not yet consumed.
- **Transactional Client.** Expiration interacts with transactional or
  lock-based consumption in a way both Azure Service Bus and RabbitMQ document
  explicitly. a message currently locked for delivery is not pulled back
  merely because it crossed its expiry instant while locked, the transaction
  or lock is allowed to resolve normally first.
- **Incompatible with none directly**, but is actively dangerous when combined
  carelessly with any pattern whose contract assumes eventual, unconditional
  delivery, most notably an audit log or ledger append pattern where every
  message must be recorded regardless of age.

## 14. Refactoring path in and out

**Introducing Message Expiration into a system that has none.**

1. Classify message types flowing through the channel by whether staleness
   actually changes their meaning. Do this per message type, not per channel,
   because a single channel frequently mixes message classes with very
   different tolerance for delay.
2. For message types where staleness is genuinely harmless, do nothing. adding
   a TTL there is pure risk with no benefit.
3. For message types where staleness matters, determine the real decay window
   from the business process the message serves, not from an arbitrary round
   number. A one-time code's decay window comes from how long a person is
   reasonably expected to still be entering it. A quote's decay window comes
   from how fast the underlying price actually moves.
4. Decide whether an expired message should be silently discarded or routed to
   a Dead Letter Channel. Default to dead lettering unless there is a specific,
   stated reason silent discard is acceptable, since the cost of adding a
   monitored dead letter destination is low relative to the cost of an
   undetected silent loss.
5. Apply the TTL at the narrowest scope that correctly expresses the decision,
   per message where the decay window genuinely varies per message, per
   destination where every message in that channel shares the same window.
   Do not default straight to per-message expiration everywhere out of
   caution, since it pushes a maintenance burden onto every producer for no
   benefit when a per-destination default would have expressed the same
   policy.
6. Add monitoring on the expiry or dead-letter-from-expiry rate before this
   goes live, not after. A rate that starts at zero and later climbs is the
   single clearest signal that a consumer has fallen behind, and that signal
   is worthless if nobody is watching it from day one.

**Removing Message Expiration from a system that already has it.**

1. Confirm, before removing anything, whether any downstream process has come
   to depend on the fact that stale messages are already being filtered out.
   this is the most common reason a removal causes an incident, some
   downstream consumer was never built to handle stale input because
   expiration had always quietly filtered it out first.
2. If a dependency on the filtering behavior exists, move the staleness check
   into application code at the consumer before removing the broker-level
   expiration, so the property, no stale messages reach business logic,
   survives the refactor.
3. Remove or widen the TTL only after that replacement check is verified in
   place and tested against the same scenarios, a slow consumer, a backlog
   drain, that originally motivated adding expiration.
4. Watch the dead letter or discard rate drop to, and stay at, zero after
   removal, as confirmation nothing downstream is still silently relying on
   expiration to shield it.

## 15. Testing and verification

This dimension is largely practice drawn from how the documented broker
behaviors constrain what is actually testable.

Message Expiration is easy to get functionally wrong in a way ordinary tests
never surface, because a naive test simply never waits long enough for
anything to expire. The correct approach is to make the clock a test seam.

- Test with an injected or mockable clock rather than the wall clock wherever
  the expiration check lives in application code, so a test can assert both
  "not yet expired, delivered normally" and "past expiry, not delivered"
  deterministically and quickly, without a real sleep.
- Where the broker itself performs the expiration check, as with RabbitMQ,
  Azure Service Bus, and SQS, integration tests should use the shortest
  practical TTL, often the broker's documented minimum, RabbitMQ and SQS both
  support sub-minute TTLs, rather than trying to fast-forward a broker's
  internal clock, which is rarely possible from outside.
- Assert on the observable contract, the message is not delivered, or is
  delivered to the dead letter destination, rather than on internal broker
  state that the documentation explicitly says is not immediately consistent,
  RabbitMQ's own documentation warns that removal timing is "at or shortly
  after" expiry, so asserting an exact queue depth immediately at the expiry
  instant is testing an implementation detail the broker does not promise.
- Specifically test the interaction between per-message and per-destination
  TTL where both exist, since both RabbitMQ and Azure Service Bus document
  non-obvious precedence rules, the lower of the two on RabbitMQ, a silent
  downgrade to the entity maximum on Azure Service Bus, and a test that only
  covers one of the two settings will not catch a regression in that
  precedence logic.
- For request-reply exchanges, test the requester's own local timeout
  independently from the message TTL, and test the case where the two are
  misaligned, a request TTL longer than the requester's own patience, and the
  reverse, to confirm the system degrades in the intended way in either
  mismatch.
- Load test the backlog-protection benefit directly. artificially stall a
  consumer, let a backlog with a range of message ages accumulate, resume
  consumption, and confirm the consumer spends its recovered capacity on
  still-valid messages rather than working strictly in arrival order through
  everything, including messages that expired hours earlier.

## 16. Observability signals

This dimension is largely practice.

- **Expiry rate.** The count, and ideally the rate, of messages expiring per
  channel per unit time. A rate that is consistently zero suggests the TTL may
  be set too generously to ever matter, worth questioning whether it is doing
  anything. A rate that climbs is the clearest early signal that a consumer is
  falling behind, well before a generic queue-depth alert would fire, because
  it directly measures the symptom expiration exists to protect against.
- **Dead-letter-from-expiry volume, distinguished by reason.** Where expired
  messages are routed to a Dead Letter Channel, the reason code, Azure Service
  Bus's dead-letter reason property is a documented example, should be tracked
  separately from other dead letter causes, malformed content, consumer
  exceptions, so an operator can tell at a glance whether the dead letter
  queue is filling because of timing or because of a content or processing
  defect. These require different responses.
- **Age distribution at consumption time.** A histogram of how old messages
  actually are at the moment they are successfully consumed, not only at the
  moment they expire, reveals whether the chosen TTL sits comfortably above
  normal consumption latency or whether it is close enough to normal latency
  that ordinary jitter risks expiring perfectly valid messages.
- **Queue or topic depth alongside expiry rate, read together.** Depth alone
  cannot distinguish a healthy, momentarily busy consumer from one that is
  falling behind badly enough that expiration is actively discarding work. The
  two signals read together tell that story. rising depth with a flat expiry
  rate is normal load. rising depth with a rising expiry rate is a consumer
  that has genuinely fallen behind.
- **Lag between logical expiry instant and observed removal, where the broker
  exposes it.** Since RabbitMQ, Azure Service Bus, and Kafka's segment based
  model all document non-instant enforcement, a growing gap here indicates the
  reaper or segment cleaner itself is falling behind, a distinct operational
  problem from consumer backlog, worth its own alert.

## 17. Security and privacy implications

The security surface here is real but narrow, and largely an analytical
consequence of what the pattern does rather than a documented vulnerability
class of its own.

- **Denial of service via forced expiry.** An attacker who can influence
  producer-set TTL values, in a system that trusts client-supplied TTL without
  bounds, could deliberately set extremely short TTLs on legitimate other
  users' messages if the system allows cross-tenant TTL manipulation, causing
  silent, hard to diagnose loss of legitimate work. The mitigation is the same
  as for any client supplied value that affects system behavior. validate and
  bound it server side, do not trust a client to self-limit.
- **Data minimization benefit.** Automatic, time bounded deletion of
  undelivered messages is a genuine privacy positive when message payloads
  contain personal data, since it bounds how long that data sits in broker
  storage if no consumer ever picks it up, which can be relevant to data
  retention obligations under privacy regulation. This is an analytical
  benefit, not a documented compliance guarantee, since expiration alone says
  nothing about how long a message's data persists once a consumer has
  actually processed and stored it elsewhere.
- **Silent loss as a security-relevant failure mode, not only a correctness
  one.** A security relevant event, a revocation notice, an access grant
  withdrawal, delivered as an expiring message and then silently dropped under
  load is a genuinely dangerous instance of the general misuse described in
  dimension 11. the failure mode is identical, but the consequence, a stale
  authorization decision continuing to be honored, is a security incident
  rather than a data quality one. Any message whose loss changes a security
  decision belongs firmly in the non-applicability list of dimension 4.
- **Dead letter destinations as a data exposure surface.** Where expired
  messages are preserved rather than discarded, the Dead Letter Channel now
  holds a copy of message content, including any personal or sensitive data
  the original message carried, for as long as that channel itself retains
  data. it needs the same access control and its own retention policy as the
  primary channel, not an implicit assumption that "it is just dead letters"
  makes it lower risk.

## 18. References

- Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
  Messaging Channels chapter, Message Expiration pattern.
- [Enterprise Integration Patterns, Message Expiration reference page](https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageExpiration.html),
  verified 2026-08-02.
- [RabbitMQ documentation, TTL Extensions to AMQP 0-9-1](https://www.rabbitmq.com/docs/ttl),
  verified 2026-08-02.
- [AWS documentation, Amazon SQS message lifecycle](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-message-lifecycle.html),
  verified 2026-08-02.
- [Microsoft Learn, Azure Service Bus Message Expiration and TTL Explained](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-expiration),
  verified 2026-08-02.
- [Confluent documentation, Kafka topic configuration reference, retention.ms](https://docs.confluent.io/platform/current/installation/configuration/topic-configs.html),
  verified 2026-08-02.

## Code examples

### TypeScript, per-message TTL against an AMQP-style publish API

```typescript
interface ExpiringMessage<T> {
  payload: T;
  producedAt: number;
  ttlMs: number;
}

function makeExpiringMessage<T>(payload: T, ttlMs: number): ExpiringMessage<T> {
  return { payload, producedAt: Date.now(), ttlMs };
}

function isExpired<T>(msg: ExpiringMessage<T>, now: number = Date.now()): boolean {
  return now - msg.producedAt > msg.ttlMs;
}

class ExpiringChannel<T> {
  private queue: ExpiringMessage<T>[] = [];
  private deadLetters: ExpiringMessage<T>[] = [];

  publish(payload: T, ttlMs: number): void {
    this.queue.push(makeExpiringMessage(payload, ttlMs));
  }

  poll(now: number = Date.now()): T | undefined {
    while (this.queue.length > 0) {
      const msg = this.queue.shift() as ExpiringMessage<T>;
      if (isExpired(msg, now)) {
        this.deadLetters.push(msg);
        continue;
      }
      return msg.payload;
    }
    return undefined;
  }

  deadLetterCount(): number {
    return this.deadLetters.length;
  }
}

const channel = new ExpiringChannel<string>();
const t0 = Date.now();
channel.publish("one-time-code:482913", 2000);
console.log(channel.poll(t0 + 500));
console.log(channel.poll(t0 + 3000));
console.log("dead letters:", channel.deadLetterCount());
```

### Python, request-reply with an expiring correlation table

```python
import time
from dataclasses import dataclass


@dataclass
class PendingRequest:
    correlation_id: str
    sent_at: float
    ttl_seconds: float

    def is_expired(self, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        return (now - self.sent_at) > self.ttl_seconds


class RequestReplyRouter:
    def __init__(self) -> None:
        self._pending: dict[str, PendingRequest] = {}

    def send(self, correlation_id: str, ttl_seconds: float, now: float | None = None) -> None:
        now = time.time() if now is None else now
        self._pending[correlation_id] = PendingRequest(correlation_id, now, ttl_seconds)

    def receive_reply(self, correlation_id: str, now: float | None = None) -> bool:
        pending = self._pending.pop(correlation_id, None)
        if pending is None:
            return False
        if pending.is_expired(now):
            return False
        return True

    def sweep_expired(self, now: float | None = None) -> list[str]:
        now = time.time() if now is None else now
        expired = [cid for cid, req in self._pending.items() if req.is_expired(now)]
        for cid in expired:
            del self._pending[cid]
        return expired


if __name__ == "__main__":
    router = RequestReplyRouter()
    t0 = time.time()
    router.send("req-1", ttl_seconds=5, now=t0)
    print("reply within window:", router.receive_reply("req-1", now=t0 + 2))

    router.send("req-2", ttl_seconds=5, now=t0)
    print("reply past window:", router.receive_reply("req-2", now=t0 + 10))

    router.send("req-3", ttl_seconds=5, now=t0)
    print("swept before reply:", router.sweep_expired(now=t0 + 6))
```

### Go, a bounded backlog that drops or dead-letters past a deadline

```go
package main

import (
	"fmt"
	"time"
)

type expiringMessage struct {
	payload   string
	expiresAt time.Time
}

type expiringQueue struct {
	items       []expiringMessage
	deadLetters []expiringMessage
}

func (q *expiringQueue) publish(payload string, ttl time.Duration, now time.Time) {
	q.items = append(q.items, expiringMessage{payload: payload, expiresAt: now.Add(ttl)})
}

func (q *expiringQueue) poll(now time.Time) (string, bool) {
	for len(q.items) > 0 {
		msg := q.items[0]
		q.items = q.items[1:]
		if now.After(msg.expiresAt) {
			q.deadLetters = append(q.deadLetters, msg)
			continue
		}
		return msg.payload, true
	}
	return "", false
}

func main() {
	q := &expiringQueue{}
	t0 := time.Now()

	q.publish("price-quote:AAPL:189.42", 2*time.Second, t0)

	if v, ok := q.poll(t0.Add(500 * time.Millisecond)); ok {
		fmt.Println("delivered:", v)
	}

	q.publish("price-quote:AAPL:190.10", 2*time.Second, t0)
	if _, ok := q.poll(t0.Add(5 * time.Second)); !ok {
		fmt.Println("not delivered, expired")
	}

	fmt.Println("dead letters:", len(q.deadLetters))
}
```

All three languages express the same three collaborating decisions. a producer
stamps a message with how long it stays valid, the channel checks that stamp
at the moment of delivery rather than at the moment of receipt, and a message
that fails the check is routed away from the normal delivery path rather than
handed to the consumer. Java, Rust, and Swift were not included because the
pattern is expressed identically in those languages, a struct or record
carrying a timestamp and a duration checked at dequeue time, and including all
six would not surface any additional idiomatic variation worth documenting.
