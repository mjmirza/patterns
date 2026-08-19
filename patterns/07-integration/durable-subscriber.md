---
name: Durable Subscriber
slug: durable-subscriber
family: 07-integration
category: Messaging
aliases: [Durable Subscription, Persistent Subscriber, Retained Subscription]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [publish-subscribe-channel, message-store, competing-consumers, guaranteed-delivery, idempotent-receiver, dead-letter-channel]
incompatible_with: [fire-and-forget-notification]
verified: 2026-08-02
---

# Durable Subscriber

## 1. Name, aliases, and lineage

The canonical name is Durable Subscriber, catalogued by Gregor Hohpe and Bobby
Woolf in *Enterprise Integration Patterns. Designing, Building, and Deploying
Messaging Solutions*, Addison-Wesley, 2003, in the Messaging Channels chapter,
under the umbrella of Publish-Subscribe Channel. The companion site for the
book states the pattern plainly. "A durable subscription saves messages for an
inactive subscriber and delivers these saved messages when the subscriber
reconnects" ([EnterpriseIntegrationPatterns.com, Durable Subscriber](https://www.enterpriseintegrationpatterns.com/patterns/messaging/DurableSubscription.html),
verified 2026-08-02). The page frames the driving question directly. "How can
a subscriber avoid missing messages while it's not listening for them?"

The name in the book is Durable Subscriber, describing the role, and the
mechanism it depends on is usually called a durable subscription, describing
the registration that persists. Practitioners use the two names
interchangeably, and this entry does too, but the distinction matters once you
read vendor documentation. A durable SUBSCRIBER is the consuming application.
A durable SUBSCRIPTION is the standing record the broker keeps on that
consumer's behalf, tying a name and, in some systems, a client identifier, to
a filtered copy of every message published on a topic since the subscription
was created.

The pattern reached its widest audience through the Java Message Service
specification, where `createDurableSubscriber` and later `createDurableConsumer`
became the concrete API surface most working engineers first met the idea
through, well before most of them had heard of the Hohpe and Woolf catalog. The
Jakarta Messaging 3.1 specification, the modern continuation of JMS under the
Eclipse Foundation, still uses the same vocabulary and still requires a client
identifier to disambiguate one durable subscriber from another on the same
topic when the subscription is unshared, loosening that requirement only for
the newer shared durable subscriptions introduced in JMS 2.0 ([Jakarta
Messaging 3.1 Specification, section 8.3, Jakarta EE](https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1.html),
verified 2026-08-02).

Since 2003 the same durability guarantee has reappeared under different local
names in nearly every messaging platform that offers publish-subscribe
semantics. Azure Service Bus calls the standing registration a "subscription"
on a "topic" and states outright that Service Bus supports "durable
publish/subscribe messaging" as one of its two core communication patterns
([Microsoft Learn, Azure Service Bus Queues, Topics, and Subscriptions](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-queues-topics-subscriptions),
verified 2026-08-02). Apache Kafka does not use the word subscriber at the
protocol level, but a consumer group achieves the identical outcome by a
different mechanism, tracked offsets against a retained log rather than a
per-message copy queue, discussed under dimension 8 below. This entry treats
Durable Subscriber as the intent, and treats the JMS client identifier plus
subscription name pairing, the broker-side per-consumer queue, and the
tracked-offset log as three differently shaped but behaviorally
equivalent implementation families.

## 2. Problem and context

A publisher broadcasts events on a topic. Multiple independent parts of the
system care about different subsets of those events, and none of them wants to
poll the publisher, none of them wants a direct dependency on the others, and
none of them wants to be the reason the publisher blocks. Publish-Subscribe
Channel already solves the fan-out half of that problem, letting any number of
subscribers register interest and receive a copy of every matching message.

The gap Publish-Subscribe Channel leaves open is time. An ordinary,
non-durable subscription only exists while the subscriber's connection exists.
The moment the subscriber process stops, whether from a deploy, a crash, a
scheduled maintenance window, or a simple restart, the broker forgets that
subscriber ever asked to listen. Every message published while the subscriber
is down is delivered to nobody, because the broker has no standing record to
deliver it to later. When the subscriber comes back, it resumes hearing new
messages, but the gap during the outage is permanently lost.

That loss is invisible in a demo and expensive in production. A billing
service that misses three minutes of order-completed events during a rolling
deploy does not throw an exception. It simply never bills those orders, and
nobody notices until a reconciliation job or a customer complaint surfaces the
gap days later. The context in which Durable Subscriber becomes necessary,
rather than merely convenient, is any topic where a subscriber's downtime is
expected to happen, whether from routine deploys, autoscaling churn, network
partition, or the honest fact that no process runs with one hundred percent
uptime, and where every message on that topic represents a fact the business
cannot afford to silently drop. The pattern turns "the subscriber must never
go offline" into "the subscriber may go offline, and the broker will hold its
mail until it returns."

## 3. Forces

**Delivery completeness against storage cost.** Holding every unread message
for every registered subscriber, potentially for a subscriber that never comes
back, consumes broker disk and memory in direct proportion to the size of the
backlog and the number of durable subscriptions. A topic with ten durable
subscribers and one slow consumer multiplies the retained volume of every
message by the number of subscribers still behind, because each subscriber
has an independent read position. This is the central cost of the pattern and
the reason it is never the default for every subscriber on every topic.

**Identity persistence against deployment flexibility.** A durable subscription
in the JMS family is bound to a durable name and, for unshared subscriptions,
a client identifier that must be stable across restarts of that exact logical
subscriber. If a rolling deploy spins up a replacement instance under a new
identifier, the broker treats it as a brand new subscriber with no history,
silently defeating the pattern. This pushes identity out of the process and
into deployment configuration, which is a real operational cost the pattern
imposes on everything downstream of it.

**Ordering and redelivery against throughput.** Guaranteeing that a returning
subscriber sees messages in the order they were published, and sees each one
at least once, generally requires acknowledgment tracking per message or per
batch, which adds a round trip the broker would not need for fire-and-forget
delivery. Systems that relax ordering, batch acknowledgments, or use offset
commits at an interval trade a small window of redelivery risk for meaningfully
higher throughput. Dimension 12 compares these trade-offs against named
alternatives directly.

**Backlog growth against consumer catch-up rate.** If a subscriber's outage
outlasts its ability to drain the backlog once it returns, using a normal
message rate, the retained queue grows without bound until an operator
intervenes, a retention limit discards the oldest messages, or the broker
itself runs out of storage. The pattern assumes the subscriber's downtime is
bounded and its catch-up throughput exceeds the publish rate. When that
assumption fails, Durable Subscriber alone does not save the system, and it
needs to be paired with backpressure or a retention policy, discussed under
dimension 11.

**Simplicity against exactly-once semantics.** The pattern by itself delivers
at-least-once. Achieving exactly-once on top of it requires either a broker
that supports transactional or idempotent producers and consumers, or an
idempotent receiver on the subscriber side (see Idempotent Receiver under
dimension 13). Treating the durable delivery guarantee alone as if it removed
duplicate risk is a common and costly misreading of the pattern, covered under
dimension 11.

## 4. Applicability and non-applicability

Reach for Durable Subscriber when all of the following hold.

- The subscriber's downtime is expected and routine, not exceptional, such as
  during rolling deploys, autoscaling scale-to-zero, or planned maintenance.
- Every message on the topic represents a business fact whose loss has a real
  cost, such as a financial transaction, an inventory adjustment, an audit
  event, or a state transition a downstream system must react to.
- The subscriber can be given a stable identity across restarts, whether a
  fixed durable subscription name, a fixed JMS client identifier, or a fixed
  Kafka consumer group id, so the broker can recognize a returning instance
  as the same logical subscriber rather than a new one.
- The publisher genuinely does not know, and should not need to know, who is
  listening, which is the underlying justification for choosing
  publish-subscribe over point-to-point in the first place.

Do NOT reach for Durable Subscriber in these situations.

- **The message is only valuable in the instant it is published**, such as a
  live cursor position, a typing indicator, or a stock ticker update where a
  stale value is worse than no value. Persisting and redelivering a backlog of
  superseded state wastes storage and can actively confuse the subscriber when
  it replays hundreds of outdated positions on reconnect. A non-durable, or
  best-effort, subscription is correct here.
- **The subscriber count is unbounded or anonymous**, such as browser tabs
  watching a public dashboard. Durable subscriptions require a stable identity
  per subscriber, and a broker cannot durably track millions of anonymous
  browser sessions without a storage cost that dwarfs the value of the
  guarantee. Use ephemeral push channels, such as WebSocket broadcast with a
  best-effort delivery guarantee, and let the client re-fetch current state on
  reconnect instead of replaying history.
- **The consumer is a single, always-on process with no realistic downtime
  window**, and simple in-memory or in-process delivery already suffices. Adding
  a durable subscription here is pure operational overhead for a guarantee the
  situation never actually calls on.
- **A point-to-point relationship with exactly one intended consumer is what
  you actually need.** If there is only ever one logical receiver, a durable
  queue, not a durable subscription on a topic, is the simpler and cheaper
  primitive, because you do not need the fan-out machinery of
  Publish-Subscribe Channel at all.
- **The team cannot operationally guarantee a stable subscriber identity
  across deploys.** If your deployment pipeline routinely rotates identifiers,
  container names, or connection parameters that the broker uses to recognize
  the subscriber, the durable subscription silently becomes a fresh one on
  every deploy and the pattern provides no real protection while still paying
  its storage cost. Fix the identity problem first, or the pattern will fail
  silently in exactly the way it exists to prevent.

## 5. Structure

- **Publisher.** Sends a message once to a Publish-Subscribe Channel, unaware
  of who is subscribed or how many of them are currently connected.
- **Publish-Subscribe Channel (Topic).** The logical broadcast point. Fans a
  single published message out to every currently registered subscription,
  durable or not, that matches the message.
- **Durable Subscription registration.** A broker-side record, keyed by a
  stable subscriber identity (a durable subscription name, sometimes paired
  with a client identifier, or a consumer group id), that the broker
  maintains independently of any live network connection. This is the
  participant that turns an ordinary subscription into a durable one.
- **Subscription-scoped Message Store.** The retained backlog of unread
  messages for that specific durable subscription. Every durable subscriber on
  the same topic has its own independent store and its own independent read
  position, so ten durable subscribers on one topic maintain ten separate
  backlogs, not one shared one.
- **Durable Subscriber (the consuming application).** Connects using its
  stable identity, receives any backlog accumulated while it was offline,
  acknowledges or commits its progress as it consumes, and disconnects again
  without losing its place.
- **Broker (or log storage layer).** The system of record that owns the
  subscription-scoped stores, persists them across restarts of the broker
  itself, and enforces whatever retention policy bounds how long an unread
  message, or an unconsumed segment of log, is kept.

## 6. ASCII structure diagram

```
                    Publish-Subscribe Channel ("orders.completed")
                    +-----------------------------------------+
   Publisher  ----->|                Topic                    |
                    +-----------------------------------------+
                       |               |                |
                       v               v                v
          +------------------+ +------------------+ +------------------+
          | Durable Sub A     | | Durable Sub B     | | Non-durable Sub  |
          | name: "billing"   | | name: "audit"     | | (live dashboard) |
          | +--------------+  | | +--------------+  | +------------------+
          | | Backlog store|  | | | Backlog store|  |    (no store,
          | | msg4 msg5    |  | | | msg3 msg4    |  |     dropped when
          | | (B offline)  |  | | | msg5 (draining|  |     unattached)
          | +--------------+  | | +--------------+  |
          +--------^----------+ +--------^----------+
                    |                    |
              (offline right       Billing Service B
               now, no consumer     currently connected
               attached; backlog    and draining its
               keeps accumulating)  own backlog
```

## 7. Dynamics

```
Time -->

Billing Service (durable subscriber "billing")   Topic "orders.completed"

  t0: connect, createDurableSubscriber("billing") ---> broker creates or
                                                          reuses subscription
                                                          record "billing"
  t1: receive msg1, ack                            <--- msg1 published
  t2: receive msg2, ack                             <--- msg2 published
  t3: process crashes / deploy begins
       (connection drops; subscription record
        for "billing" stays alive on the broker)
                                                     <--- msg3 published
                                                          stored in "billing"
                                                          backlog (no live
                                                          consumer to send to)
                                                     <--- msg4 published
                                                          stored in "billing"
                                                          backlog
  t4: new instance starts, reconnects using the
       SAME durable name "billing"
                                                     ---> broker recognizes
                                                          "billing", delivers
                                                          retained msg3, msg4
  t5: receive msg3, ack                             <--- (redelivered from
                                                          the backlog)
  t6: receive msg4, ack                             <--- (redelivered from
                                                          the backlog, backlog
                                                          now empty)
  t7: receive msg5, ack                              <--- msg5 published
                                                          (delivered live,
                                                          no backlog needed)
```

A second durable subscriber, "audit", registered on the same topic, runs this
exact sequence independently and on its own schedule. If "audit" never
disconnects, its backlog never grows past the messages it has not yet
acknowledged in flight, while "billing" accumulates a backlog during its
outage. The two subscriptions do not affect or block each other.

## 8. Implementation variants

**Client identifier plus subscription name (classic JMS/Jakarta Messaging).**
The subscriber calls a method such as `createDurableSubscriber(topic, "billing")`
after setting a client identifier on its connection. The broker keys the
retained store on the pair of client identifier and subscription name for an
unshared subscription. Reconnecting with the same pair resumes the same
backlog. The Jakarta Messaging 3.1 specification notes that "setting client ID
remains mandatory when creating an unshared durable subscription" but became
"optional when creating a shared durable subscription" in the version that
introduced shared durable subscriptions ([Jakarta Messaging 3.1 Specification,
section 8.3](https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1.html),
verified 2026-08-02), which is the variant below.

**Shared durable subscription.** Introduced in JMS 2.0 and carried forward into
Jakarta Messaging, this lets several consumer processes attach to the same
named durable subscription simultaneously, splitting its backlog between them
the way competing consumers split a queue. This combines Durable Subscriber
with Competing Consumers, trading strict per-message ordering within the
subscription for horizontal scale-out of the recovery work after an outage. It
directly answers a real operational problem with the classic variant, a single
consumer instance draining a large backlog alone, slowly, after a long outage.

**Broker-native topic subscription queue.** RabbitMQ, and AMQP-based brokers
generally, do not have a first-class durable subscriber concept in the JMS
sense. Instead, an operator declares a durable queue bound to an exchange, and
that queue behaves like a durable subscription as long as the binding and the
published messages are both marked persistent. RabbitMQ's own documentation
states that "durable queues will be recovered on node boot, including
messages in them published as persistent," but warns explicitly that
"messages published as transient will be discarded during recovery, even if
they were stored in durable queues" ([RabbitMQ Documentation, Queues](https://www.rabbitmq.com/docs/queues),
verified 2026-08-02). This is a variant where durability is composed from two
independent flags, queue durability and message persistence, rather than one
subscription-level guarantee, and forgetting the second flag is the single
most common way teams believe they have Durable Subscriber and do not.

**Fanout to per-subscriber durable queues (SNS to SQS, and equivalents).**
Amazon SNS has no retained backlog of its own. Durability is achieved by
fanning each published notification out to one Amazon SQS queue per
subscriber, and each queue is independently durable and independently
consumed. AWS's own documentation describes exactly this composition. "Using
Amazon SNS and Amazon SQS together, messages can be delivered to applications
that require immediate notification of an event, and also persisted in an
Amazon SQS queue for other applications to process at a later time" ([AWS
Documentation, Fanout Amazon SNS notifications to Amazon SQS queues](https://docs.aws.amazon.com/sns/latest/dg/sns-sqs-as-subscriber.html),
verified 2026-08-02). This is Durable Subscriber implemented as a deliberate
composition of Publish-Subscribe Channel plus a separate durable queue per
subscriber, rather than a single integrated primitive.

**Tracked-offset log (Kafka consumer groups).** Kafka retains every message on
a topic-partition for a configured window regardless of who has read it, and
each consumer group independently tracks how far it has read by committing an
offset. A consumer group that stops reading simply falls behind. When it
returns under the same group id, "it will send an OffsetFetchRequest to the
group coordinator to retrieve the last committed offset for its assigned
partition. Once it has the offset, it will resume the consumption from that
point" ([Confluent Developer, Consumer Group Protocol](https://developer.confluent.io/courses/architecture/consumer-group-protocol/),
verified 2026-08-02). This is the differently shaped but behaviorally
equivalent family named under dimension 1. Instead of one retained store per
subscriber, there is one shared retained log and N independent cursors into
it, which is both cheaper at high subscriber counts, because the message is
stored once rather than N times, and riskier at long retention windows,
because a very slow consumer group can fall behind the log's retention limit
and lose messages that a per-subscriber store would have kept regardless of
age.

**Language-idiomatic shape.** None of the mainstream languages change the
shape of this pattern the way, for example, a closure changes Strategy.
Durable Subscriber is a protocol-and-broker-level contract, not a language
construct, so the client code in every language reduces to the same three
steps regardless of syntax. establish a connection carrying a stable identity,
open or attach to the named durable subscription, and enter a receive-process-
acknowledge loop. The samples under Code Examples show this identical shape in
four languages against the two most common concrete APIs, an SQS-backed
per-subscriber queue and a Kafka consumer group, because those two are
reachable in this environment without a running broker to connect to.

## 9. Known production uses

- **Java Message Service and Jakarta Messaging, implemented by Apache
  ActiveMQ Artemis.** Artemis's own JMS usage guide states that the JMS client
  identifier "represents the client id for a JMS client and is needed for
  creating durable subscriptions" ([Apache ActiveMQ Artemis Documentation,
  Using JMS](https://artemis.apache.org/components/artemis/documentation/latest/using-jms.html),
  verified 2026-08-02), confirming Artemis as a broker that implements the
  classic durable subscriber contract from the JMS specification, the same
  API family Hohpe and Woolf's book cites as the pattern's most familiar
  concrete realization.
- **Amazon SNS fanning out to Amazon SQS.** AWS documents this as the
  recommended pattern for delivering the same notification both to
  time-critical subscribers and to subscribers "that require... persisted in
  an Amazon SQS queue for other applications to process at a later time"
  ([AWS Documentation, sns-sqs-as-subscriber](https://docs.aws.amazon.com/sns/latest/dg/sns-sqs-as-subscriber.html),
  verified 2026-08-02), which is the fanout implementation variant from
  dimension 8 running in production across a very large share of AWS-hosted
  event-driven systems.
- **Azure Service Bus topics and subscriptions.** Microsoft's own product
  description states that "Azure Service Bus supports reliable message
  queuing and durable publish/subscribe messaging," and separately documents
  that Service Bus additionally exposes "shared durable subscriptions" and
  "unshared durable subscriptions" through its JMS 2.0-compatible entity model
  ([Microsoft Learn, Azure Service Bus Queues, Topics, and Subscriptions](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-queues-topics-subscriptions),
  verified 2026-08-02), making it a broker that offers both the classic
  broker-native variant and a JMS-compatible variant side by side.
- **Apache Kafka consumer groups**, as the tracked-offset log variant, are the
  delivery mechanism behind a very large fraction of event-driven
  architectures built since roughly 2015, with the specific catch-up
  mechanics, an `OffsetFetchRequest` retrieving the group's last committed
  offset on reconnect, documented by Confluent's own architecture course
  ([Confluent Developer, Consumer Group Protocol](https://developer.confluent.io/courses/architecture/consumer-group-protocol/),
  verified 2026-08-02). This is judgement, not a sourced claim about
  prevalence, based on Kafka's well-documented adoption as the default
  streaming backbone at a large number of technology companies, but the
  mechanics quoted above are sourced directly.

## 10. Consequences

Positive.

- **No message is silently lost during an expected subscriber outage**, which
  is the entire reason the pattern exists, and it converts an availability
  problem for the subscriber into a storage and catch-up problem for the
  broker, which is almost always the easier problem to operate.
- **The publisher stays completely decoupled from subscriber lifecycle.** It
  never needs to know whether zero, one, or ten subscribers are currently
  connected, and it never blocks on a slow or offline subscriber, because the
  broker absorbs that variance on the subscriber's behalf.
- **Each durable subscriber can catch up at its own pace**, independent of
  every other subscriber on the same topic, because each one owns its own
  backlog and its own read position.
- **The pattern composes cleanly with Competing Consumers** through shared
  durable subscriptions or consumer groups, letting a team add horizontal
  catch-up capacity after a long outage without changing the publisher at
  all.

Negative.

- **Storage cost scales with both subscriber count and outage duration.** A
  topic with many durable subscribers, several of which are frequently
  offline for long windows, can accumulate retained volume that dwarfs the
  live message rate, and this cost is easy to underestimate at design time
  because it is invisible until the first real outage.
- **Identity management becomes a hard operational requirement, not an
  implementation detail.** A subscriber that cannot reliably present the same
  durable name or client identifier on every restart silently loses the
  guarantee, and the failure mode is quiet, not a crash, which makes it
  dangerous.
- **The pattern only guarantees delivery, not exactly-once processing.** A
  subscriber that crashes after processing a message but before
  acknowledging it will see that message again on reconnect, and any
  subscriber logic that is not idempotent will double-process it.
- **A subscriber that never returns leaves an orphaned, growing backlog
  forever**, unless the operator explicitly deletes the subscription or
  applies a retention policy, which means the pattern needs a companion
  operational process, not the messaging configuration alone, to be
  production-safe.

## 11. Failure modes and misuse

**Symptom.** A subscriber that was redeployed under a new pod name, container
id, or connection string appears to receive zero backlog after an outage, as
if the durable subscription never existed.
**Cause.** The deployment changed the durable subscription name or client
identifier the subscriber presents, so the broker created a brand new,
empty subscription instead of reattaching to the existing one, and the old
subscription with its accumulated backlog is now orphaned and invisible to
the new instance.
**Fix.** Pin the durable identity, subscription name, client identifier, or
consumer group id, to something that survives redeploys, such as a value in
configuration or an environment variable set by the deployment pipeline,
never a value derived from the pod or container's own runtime identity.

**Symptom.** The broker's disk usage on a topic grows continuously and never
levels off, even though the publish rate is stable.
**Cause.** One or more durable subscribers were removed from the fleet, at the
application level, without their broker-side subscription being explicitly
unregistered, so the broker keeps retaining and accumulating messages for a
subscriber that will never return.
**Fix.** Treat unregistering a durable subscription as a mandatory step in the
decommissioning process for any subscriber, and alert on subscriptions whose
backlog is growing while their last-connected timestamp ages past an expected
threshold.

**Symptom.** Downstream records show duplicate side effects, a payment
charged twice, an email sent twice, correlated with subscriber restarts or
broker failovers.
**Cause.** The subscriber processed a message and performed its side effect,
but crashed, or the broker failed over, before the acknowledgment or offset
commit was recorded, so on reconnect the broker redelivers a message the
subscriber already actually finished.
**Fix.** Pair Durable Subscriber with Idempotent Receiver, keying
deduplication on a stable message identifier the subscriber persists
alongside the effect it produced, never assuming at-least-once delivery is
exactly-once in disguise.

**Symptom.** A single durable subscriber's catch-up after a multi-hour outage
takes so long that it falls permanently further behind rather than closing
the gap, and its consumer lag graph only ever rises.
**Cause.** The subscriber's processing throughput is lower than the topic's
sustained publish rate, so a single serial consumer can never fully drain
what accumulated, and every additional minute of catch-up time adds more
new messages than it removes old ones.
**Fix.** Move to a shared durable subscription, or a consumer group with
multiple partitions and multiple consumer instances, so catch-up work can be
parallelized, and set an alert on consumer lag growth rate, not absolute
lag, so this condition is caught long before it becomes unrecoverable.

**Symptom.** A retained backlog exceeds a configured retention window or
storage quota, and the broker silently truncates or expires messages the
subscriber has not yet read.
**Cause.** The system was operated as if durability were unconditional,
without an explicit, monitored retention policy, so the eventual and entirely
predictable moment the backlog outgrew its bound arrived as a silent data loss
event instead of a controlled decision.
**Fix.** Set an explicit retention limit, time-based, size-based, or both,
treat crossing it as an incident, not a background broker behavior, and
decide in advance, as a business decision, whether an unrecoverable
subscriber should fall back to a full-state resync rather than a message
replay.

## 12. Trade-off matrix

| Force | Durable Subscriber | Publish-Subscribe Channel (non-durable) | Competing Consumers on a shared queue | Event Sourcing replay |
|---|---|---|---|---|
| Survives subscriber downtime | Yes, by design | No, messages during downtime are lost | Yes, undelivered messages stay on the queue | Yes, and for far longer, potentially forever |
| Number of independent read positions | One per subscriber | None retained at all | One shared position across all consumers on the queue | One per subscriber, same as Durable Subscriber, but against a full immutable log |
| Storage cost profile | Grows with subscriber count times backlog | None | Grows with backlog only, shared by all consumers | Grows unbounded, retained forever by design |
| Ordering guarantee per subscriber | Preserved per subscription, unless shared | Preserved while connected | Not preserved across the pool, one message per consumer, order across consumers is undefined | Fully preserved, replay is deterministic |
| Fan-out to many independent subscribers | Yes, native strength | Yes | No, one logical consumer group only, without layering topics on top | Yes, any number of independent readers of the same log |
| Typical operational cost | Moderate, identity plus retention management | Low, nothing to manage beyond the channel | Low to moderate, mainly queue depth monitoring | High, storage and schema evolution discipline |

## 13. Related and incompatible patterns

- **Publish-Subscribe Channel.** Durable Subscriber is not a standalone
  pattern. It is Publish-Subscribe Channel plus a persistence guarantee on
  the subscription side, and it cannot exist without a working
  publish-subscribe channel underneath it.
- **Message Store.** The retained, subscription-scoped backlog described
  under dimension 5 is a Message Store in miniature, one per durable
  subscriber, and any broker implementing Durable Subscriber is implementing
  a Message Store internally whether it exposes that vocabulary or not.
- **Competing Consumers.** Shared durable subscriptions and Kafka consumer
  groups compose Durable Subscriber directly with Competing Consumers, using
  multiple parallel processes to drain one logical subscriber's backlog
  faster than a single process could.
- **Guaranteed Delivery.** Durable Subscriber is one specific application of
  the broader Guaranteed Delivery pattern, scoped to the publish-subscribe
  case rather than point-to-point messaging.
- **Idempotent Receiver.** Not composed automatically. Durable Subscriber
  guarantees at-least-once delivery, and Idempotent Receiver is what turns
  that into effectively-once processing on the subscriber's side. Omitting it
  is the single most common misuse documented under dimension 11.
- **Dead Letter Channel.** A companion pattern for the case where a message
  in the backlog cannot be successfully processed after retries. Durable
  Subscriber alone has no opinion on poison messages, and pairing it with a
  Dead Letter Channel prevents one unprocessable message from blocking an
  entire subscription's backlog behind it.
- **Incompatible with fire-and-forget notification semantics.** A design that
  deliberately wants stale updates discarded, such as a live cursor or a
  presence indicator, is actively harmed by wrapping it in Durable
  Subscriber, because the subscriber would replay a backlog of superseded
  state on every reconnect, which is the opposite of the intended behavior.
  This is not a compatibility gap to be worked around. it is a sign the
  message semantics and the pattern do not belong together.

## 14. Refactoring path in and out

**Introducing Durable Subscriber into an existing non-durable subscription.**

1. Confirm the subscriber can be given a stable identity, a fixed
   subscription name and, where the broker requires it, a fixed client
   identifier or consumer group id, that survives every redeploy path the
   subscriber goes through, including the very first deploy after this
   change ships.
2. Switch the subscriber's connection code from a non-durable subscribe call
   to the broker's durable equivalent, `createDurableSubscriber` in JMS, a
   named consumer group in Kafka, or a bound durable queue in an AMQP broker,
   using that stable identity.
3. Deploy the subscriber once with the new durable registration, and verify
   in the broker's management interface that the subscription now persists
   across a deliberate restart of the subscriber process, with zero manual
   intervention.
4. Set an explicit retention policy on the new durable subscription before
   the next planned outage, not after, so the very first real test of the
   change is not also the first time anyone thought about the storage bound.
5. Add monitoring on that subscription's backlog depth and last-connected
   time, so a subscriber that stops returning is caught by an alert rather
   than by disk pressure on the broker weeks later.
6. If the subscriber's own processing is not already idempotent, add
   Idempotent Receiver in the same change, because the redelivery this step
   introduces was not previously possible under the non-durable subscription.

**Removing Durable Subscriber once it stops earning its place.**

1. Confirm the subscriber genuinely no longer needs delivery guarantees
   across downtime, commonly because it moved to an always-on, highly
   available deployment topology where downtime windows against this topic
   are no longer expected.
2. Drain the existing backlog to zero deliberately, rather than deleting the
   subscription with unread messages still in it, so no in-flight business
   fact is silently discarded as part of a cleanup.
3. Switch the subscriber's connection code to the broker's non-durable
   subscribe call.
4. Explicitly unregister the now-unused durable subscription record on the
   broker, `unsubscribe` in JMS terms, so it stops occupying storage and stops
   appearing as an orphaned subscription in the failure mode described under
   dimension 11.
5. Remove any monitoring or alerting that was specific to that subscription's
   backlog depth, so the on-call rotation is not left watching a metric that
   no longer means anything.

## 15. Testing and verification

Testing code that depends on Durable Subscriber has one genuinely hard part,
and it is the part most test suites skip. verifying that a message published
while the subscriber was disconnected is actually delivered once the
subscriber reconnects, in order, exactly the scenario the pattern exists for.

A useful three-tier approach.

- **Unit level.** Test the subscriber's message handler in isolation from any
  broker at all, feeding it a sequence of messages, including deliberately
  duplicated ones, and asserting the resulting side effects are correct and
  idempotent. This tier never needs a broker and should be the bulk of the
  test suite.
- **Integration level, against a real or embedded broker.** Start a broker,
  such as an embedded ActiveMQ Artemis instance or a Testcontainers-managed
  Kafka broker, create the durable subscription, publish messages, then
  explicitly disconnect and reconnect the subscriber using the same durable
  identity, asserting the disconnected-window messages arrive on reconnect.
  This is the tier that actually exercises the pattern's core guarantee, and
  a suite that never disconnects and reconnects the subscriber is not testing
  Durable Subscriber at all, only Publish-Subscribe Channel.
- **Failure-injection level.** Kill the subscriber process mid-batch, after
  processing but before acknowledging a subset of messages, and assert the
  redelivered subset on restart is handled idempotently rather than
  double-applied. This tier is what actually validates the pairing with
  Idempotent Receiver described under dimension 13, and it is engineering
  judgement, not a sourced technique, that this specific failure window,
  processed but not yet acknowledged, is the highest-value one to inject
  deliberately, because it is exactly the window every at-least-once system
  is statistically most likely to hit in production.

Test doubles that apply. an in-memory fake broker that models subscription
backlogs as a simple append-only list keyed by subscription name is usually
sufficient for unit-level tests of subscriber logic, while integration tests
should avoid mocking the broker entirely and use a real or embedded one,
because the exact redelivery and offset-tracking behavior on reconnect is
broker-specific and easy to model incorrectly by hand.

## 16. Observability signals

A healthy durable subscriber shows, per subscription, a backlog depth that
oscillates near zero and returns to zero shortly after any planned outage
ends, a last-acknowledged, or last-committed-offset, timestamp that advances
continuously during normal operation, and a consumer lag, the gap between the
newest published message and the subscriber's current read position, that is
bounded and does not trend upward over any multi-day window.

Log and trace at minimum. every durable subscription creation and
unsubscription event, tagged with the subscription's stable identity, so an
unexpected new subscription name in the logs is immediately visible as a
likely identity-pinning failure from the first failure mode under dimension
11. Every reconnect event for an existing durable subscription, with the size
of the backlog delivered on that reconnect, which turns an invisible recovery
into a visible, alertable number. Every redelivery, distinct from a first
delivery, so the idempotency path in the subscriber's handler can be traced
and its frequency measured over time, because a redelivery rate that
suddenly spikes is usually the first visible symptom of a broker failover or
a subscriber crash loop, well before anyone notices the downstream effect.

A dashboard built around this pattern should put backlog depth per
subscription and consumer lag per subscription side by side, because the two
metrics answer different questions. backlog depth answers "is this
subscriber currently behind", while lag trend over time answers "is this
subscriber capable of ever catching up", and the second question is the one
that actually predicts an incident before it happens.

## 17. Security and privacy implications

A durable subscription's retained backlog is, functionally, a copy of every
message the subscriber has not yet consumed, sitting on the broker for a
potentially unbounded window. This has two concrete implications, both
engineering judgement drawn from the pattern's mechanics rather than sourced
claims.

First, the backlog inherits whatever sensitivity the original message
carries, and it keeps that sensitivity for the length of the subscriber's
downtime, which is exactly the property that makes it valuable for delivery
and exactly the property that makes it a data-at-rest concern for anything
containing personal or regulated data. A broker holding durable subscriptions
for personal data needs the same encryption-at-rest, retention-limit, and
access-control posture as any other data store in the system, not a lighter
one, because "it is only a message queue" is not a reason regulators or
attackers treat it differently from a database.

Second, because a durable subscription's identity, a name and sometimes a
client identifier, is a standing credential of sorts, that if compromised or
spoofed lets an attacker attach to an existing subscription and read its
entire retained backlog, including everything published during the real
subscriber's downtime, subscription names and identifiers deserve the same
access-control discipline as any other authentication credential, never treated
as a mere routing label that can be guessed or reused across environments.
Where the broker supports per-subscription access control, apply it, and
where it does not, restrict who can create or attach to durable subscriptions
at the network or application layer instead.

Where the pattern is silent. Durable Subscriber makes no statement about
message confidentiality in transit, message-level encryption, or
authentication of the publisher, all of which are the concern of whatever
transport and authorization layer sits underneath the messaging channel, not
of this pattern itself.

## 18. References

- Gregor Hohpe, Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
  Messaging Channels chapter, Durable Subscriber. Companion page. [EnterpriseIntegrationPatterns.com,
  Durable Subscriber](https://www.enterpriseintegrationpatterns.com/patterns/messaging/DurableSubscription.html),
  verified 2026-08-02.
- Eclipse Foundation, *Jakarta Messaging Specification, version 3.1*, section
  8.3, durable subscriptions and client identifiers. [jakarta.ee](https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1.html),
  verified 2026-08-02.
- Apache Software Foundation, *Apache ActiveMQ Artemis Documentation, Using
  JMS*, client identifier and durable subscription creation. [artemis.apache.org](https://artemis.apache.org/components/artemis/documentation/latest/using-jms.html),
  verified 2026-08-02.
- Amazon Web Services, *Fanout Amazon SNS notifications to Amazon SQS queues
  for asynchronous processing*. [docs.aws.amazon.com](https://docs.aws.amazon.com/sns/latest/dg/sns-sqs-as-subscriber.html),
  verified 2026-08-02.
- Microsoft, *Azure Service Bus Queues, Topics, and Subscriptions*, Microsoft
  Learn. [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-queues-topics-subscriptions),
  verified 2026-08-02.
- Confluent, *Consumer Group Protocol*, Confluent Developer architecture
  course, offset commit and fetch behavior on reconnect. [developer.confluent.io](https://developer.confluent.io/courses/architecture/consumer-group-protocol/),
  verified 2026-08-02.
- Broadcom (VMware), *RabbitMQ Documentation, Queues*, durable queues and
  persistent message recovery on node boot. [rabbitmq.com](https://www.rabbitmq.com/docs/queues),
  verified 2026-08-02.

## Code examples

The samples below model the two production-verified variants from dimension
8 that can be exercised without a running broker in this environment. an
SQS-style, per-subscriber durable queue (the fanout variant), and a
Kafka-style, tracked-offset consumer group. Both show the identical
three-step shape from dimension 8. connect with a stable identity, attach to
the durable subscription, and receive-process-acknowledge in a loop, with a
backlog surviving a simulated disconnect.

### TypeScript. per-subscriber durable queue (SQS-style fanout)

```typescript
type Message = { id: number; payload: string };

class DurableSubscription {
  private backlog: Message[] = [];
  private lastAcked = -1;

  constructor(public readonly name: string) {}

  deliver(msg: Message): void {
    this.backlog.push(msg);
  }

  drain(process: (msg: Message) => void): void {
    while (this.backlog.length > 0) {
      const msg = this.backlog.shift()!;
      process(msg);
      this.lastAcked = msg.id;
    }
  }
}

class Topic {
  private subscriptions = new Map<string, DurableSubscription>();

  subscribe(name: string): DurableSubscription {
    if (!this.subscriptions.has(name)) {
      this.subscriptions.set(name, new DurableSubscription(name));
    }
    return this.subscriptions.get(name)!;
  }

  publish(msg: Message): void {
    for (const sub of this.subscriptions.values()) {
      sub.deliver(msg);
    }
  }
}

const seen = new Set<number>();
function idempotentHandler(msg: Message): void {
  if (seen.has(msg.id)) {
    console.log(`skip duplicate ${msg.id}`);
    return;
  }
  seen.add(msg.id);
  console.log(`processed ${msg.id}: ${msg.payload}`);
}

const orders = new Topic();

const billing = orders.subscribe("billing");
orders.publish({ id: 1, payload: "order-completed-1" });
billing.drain(idempotentHandler);

orders.publish({ id: 2, payload: "order-completed-2" });
orders.publish({ id: 3, payload: "order-completed-3" });

const billingReconnected = orders.subscribe("billing");
billingReconnected.drain(idempotentHandler);
```

### Python. tracked-offset consumer group (Kafka-style)

```python
class PartitionLog:
    def __init__(self):
        self.messages = []

    def append(self, payload):
        self.messages.append(payload)
        return len(self.messages) - 1


class ConsumerGroup:
    def __init__(self, group_id, log):
        self.group_id = group_id
        self.log = log
        self.committed_offset = -1

    def poll(self):
        start = self.committed_offset + 1
        return list(enumerate(self.log.messages[start:], start=start))

    def commit(self, offset):
        self.committed_offset = offset


def idempotent_process(seen, offset, payload):
    if offset in seen:
        print(f"skip duplicate offset {offset}")
        return
    seen.add(offset)
    print(f"processed offset {offset}: {payload}")


log = PartitionLog()
seen = set()

group = ConsumerGroup("billing", log)

log.append("order-completed-1")
for offset, payload in group.poll():
    idempotent_process(seen, offset, payload)
    group.commit(offset)

log.append("order-completed-2")
log.append("order-completed-3")

reconnected = ConsumerGroup("billing", log)
reconnected.committed_offset = group.committed_offset
for offset, payload in reconnected.poll():
    idempotent_process(seen, offset, payload)
    reconnected.commit(offset)
```

### Go. per-subscriber durable queue with explicit disconnect and reconnect

```go
package main

import "fmt"

type Message struct {
	ID      int
	Payload string
}

type DurableSubscription struct {
	Name    string
	backlog []Message
}

func (s *DurableSubscription) Deliver(m Message) {
	s.backlog = append(s.backlog, m)
}

func (s *DurableSubscription) Drain(process func(Message)) {
	for len(s.backlog) > 0 {
		m := s.backlog[0]
		s.backlog = s.backlog[1:]
		process(m)
	}
}

type Topic struct {
	subs map[string]*DurableSubscription
}

func NewTopic() *Topic {
	return &Topic{subs: make(map[string]*DurableSubscription)}
}

func (t *Topic) Subscribe(name string) *DurableSubscription {
	if s, ok := t.subs[name]; ok {
		return s
	}
	s := &DurableSubscription{Name: name}
	t.subs[name] = s
	return s
}

func (t *Topic) Publish(m Message) {
	for _, s := range t.subs {
		s.Deliver(m)
	}
}

func main() {
	seen := make(map[int]bool)
	handler := func(m Message) {
		if seen[m.ID] {
			fmt.Printf("skip duplicate %d\n", m.ID)
			return
		}
		seen[m.ID] = true
		fmt.Printf("processed %d: %s\n", m.ID, m.Payload)
	}

	orders := NewTopic()

	billing := orders.Subscribe("billing")
	orders.Publish(Message{ID: 1, Payload: "order-completed-1"})
	billing.Drain(handler)

	// subscriber disconnects here, the broker keeps the "billing"
	// subscription record and its backlog alive.
	orders.Publish(Message{ID: 2, Payload: "order-completed-2"})
	orders.Publish(Message{ID: 3, Payload: "order-completed-3"})

	billingReconnected := orders.Subscribe("billing")
	billingReconnected.Drain(handler)
}
```

### Java. JMS-shaped durable subscriber (the canonical API family)

```java
import java.util.*;

class MessageJ {
    final int id;
    final String payload;
    MessageJ(int id, String payload) { this.id = id; this.payload = payload; }
}

class DurableSubscription {
    final String clientId;
    final String subscriptionName;
    final Deque<MessageJ> backlog = new ArrayDeque<>();

    DurableSubscription(String clientId, String subscriptionName) {
        this.clientId = clientId;
        this.subscriptionName = subscriptionName;
    }

    String key() { return clientId + ":" + subscriptionName; }

    void deliver(MessageJ m) { backlog.addLast(m); }

    void drain(java.util.function.Consumer<MessageJ> process) {
        while (!backlog.isEmpty()) {
            process.accept(backlog.pollFirst());
        }
    }
}

class TopicBroker {
    private final Map<String, DurableSubscription> subs = new HashMap<>();

    DurableSubscription createDurableSubscriber(String clientId, String subscriptionName) {
        String key = clientId + ":" + subscriptionName;
        return subs.computeIfAbsent(key, k -> new DurableSubscription(clientId, subscriptionName));
    }

    void publish(MessageJ m) {
        for (DurableSubscription s : subs.values()) {
            s.deliver(m);
        }
    }
}

public class DurableSubscriberDemo {
    public static void main(String[] args) {
        Set<Integer> seen = new HashSet<>();
        java.util.function.Consumer<MessageJ> handler = m -> {
            if (seen.contains(m.id)) {
                System.out.println("skip duplicate " + m.id);
                return;
            }
            seen.add(m.id);
            System.out.println("processed " + m.id + ": " + m.payload);
        };

        TopicBroker orders = new TopicBroker();

        DurableSubscription billing = orders.createDurableSubscriber("billing-service-1", "billing");
        orders.publish(new MessageJ(1, "order-completed-1"));
        billing.drain(handler);

        orders.publish(new MessageJ(2, "order-completed-2"));
        orders.publish(new MessageJ(3, "order-completed-3"));

        DurableSubscription billingReconnected = orders.createDurableSubscriber("billing-service-1", "billing");
        billingReconnected.drain(handler);
    }
}
```
