---
name: Publisher-Subscriber
slug: publisher-subscriber
family: 08-cloud-distributed
category: Messaging and Integration
aliases: [Pub-Sub, Publish-Subscribe, Publish-Subscribe Channel, Topic-Based Messaging]
first_described: "Hohpe and Woolf 2003 (Enterprise Integration Patterns, Publish-Subscribe Channel); cloud realization documented in the Azure Architecture Center"
maturity: canonical
related: [observer, event-sourcing, cqrs, saga, retry, circuit-breaker, competing-consumers, transactional-outbox]
incompatible_with: []
verified: 2026-08-02
---

# Publisher-Subscriber

## 1. Name, aliases, and lineage

The canonical name in the messaging literature is **Publish-Subscribe Channel**,
recorded by Gregor Hohpe and Bobby Woolf in *Enterprise Integration Patterns.
Designing, Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
in the Messaging Channels chapter. Their statement of the pattern is compact.
"How can the sender broadcast an event to all interested receivers?" is
answered by sending the event on a Publish-Subscribe Channel, which delivers a
copy of a particular event to each receiver
([Enterprise Integration Patterns, Publish-Subscribe Channel](https://www.enterpriseintegrationpatterns.com/patterns/messaging/PublishSubscribeChannel.html),
verified 2026-08-02). In everyday engineering speech the pattern is almost
always shortened to **Pub-Sub** or **Publish-Subscribe**, and cloud vendors
name their products after the shortened form directly, Google Cloud Pub/Sub
and the AWS Simple Notification Service being the clearest examples.

The name is contested in one specific way that this entry exists partly to
settle. The Gang of Four book records **Publish-Subscribe** as an alias for
the *Observer* pattern, a design-time, in-process, single-language-runtime
relationship between a subject and its dependents (Erich Gamma, Richard Helm,
Ralph Johnson, and John Vlissides, *Design Patterns. Elements of Reusable
Object-Oriented Software*, Addison-Wesley, 1994, chapter 5, Behavioral
Patterns, Observer). Hohpe and Woolf's Publish-Subscribe Channel is a
different animal entirely, a runtime, cross-process, broker-mediated
relationship between components that may never share a language, a machine,
or a deployment lifecycle. The two ideas share only a shape, one sender and
many independent receivers who did not have to be named in advance, and the
messaging community's Publish-Subscribe Channel is the pattern this entry
covers. Dimension 13 resolves the confusion with a table, and the
`observer.md` entry in this same repository carries the mirror image of the
same comparison from the Observer side.

Other names attach to specific mechanisms rather than the pattern itself.
**Topic-based messaging** describes the common implementation where the
broker routes by a named channel, as opposed to **content-based routing**
where the broker inspects message fields. **Fan-out** describes the effect
from the publisher's point of view, one message becoming many deliveries, and
Amazon names an entire usage scenario after it (Amazon Web Services,
[What is Amazon SNS, Fanout scenario](https://docs.aws.amazon.com/sns/latest/dg/welcome.html),
verified 2026-08-02). None of these are separate patterns. They are all
Publisher-Subscriber wearing a different hat depending on which corner of the
pattern the speaker is standing in.

## 2. Problem and context

A component in a system needs to tell other components that something
happened, and it does not know, and should not need to know, who those other
components are. The order was placed. The temperature crossed a threshold.
The build finished. In a small system the publishing component could call
every interested party directly, but that couples it to the identity, the
location, and the availability of every consumer that exists today, and it
requires the publisher's code to change every time a new consumer is added.

Microsoft's Azure Architecture Center frames the failure of the direct
approach precisely. "When a sender communicates directly with its consumers,
it must know the identity and endpoint of every consumer, deliver messages to
each consumer, and manage failures individually. Adding or removing a
consumer requires changes to the sender, which limits how independently teams
can develop and deploy components"
([Publisher-Subscriber pattern, Context and problem](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
verified 2026-08-02, page updated 2026-06-03). A point-to-point queue does
not fix this either. A standard queue creates a direct relationship between a
sender and a single consumer, so supporting several independent consumers
means the sender must fan out into a separate queue per consumer by hand,
which is exactly the coupling the pattern exists to remove.

The context in which Publish-Subscribe is the right tool has three
recognisable features. The publisher genuinely does not know its audience in
advance, or the audience changes over the system's lifetime without the
publisher redeploying. The consumers are independently owned, often by
different teams, sometimes running different languages and different release
schedules. And the interaction can tolerate being asynchronous, because the
publisher moves on immediately after handing the event to the broker rather
than waiting for every subscriber to finish processing it. Where any of those
three is false, reach for a different pattern first, as dimension 4 makes
explicit.

## 3. Forces

Publisher-Subscriber is a trade of certainty for flexibility, and every
serious implementation choice inside the pattern is a re-negotiation of that
same trade along one specific axis.

**Coupling against visibility.** Decoupling the publisher from the
subscriber's identity is the entire point of the pattern, but the cost is
that nobody standing at the publisher can answer "who reads this and what do
they do with it" by reading the publisher's source code. That answer now
lives in the broker's subscription list, which changes independently and is
frequently under-documented. The pattern trades a compile-time guarantee for
a deployment-time flexibility, and teams that never build the tooling to
answer that question inherit an invisible dependency graph.

**Latency against throughput.** A direct call is the fastest possible
notification, one stack frame. A broker in the middle adds a network hop on
publish and another on delivery, and Google's own overview states the
resulting latency is "typically on the order of 100 milliseconds" for Cloud
Pub/Sub
([Google Cloud Pub/Sub overview](https://docs.cloud.google.com/pubsub/docs/overview),
verified 2026-08-02). What the broker buys back is throughput and
resilience, because the broker can batch, buffer, and retry on the
subscriber's behalf, work a direct call could never do.

**Ordering against parallelism.** A single unordered stream of independent
events lets every subscriber process every message with full parallelism.
The instant two events must be applied in the order they were produced,
something has to serialize delivery, and that something either becomes a
scaling bottleneck or requires partitioning, which trades global ordering for
ordering within a partition. This exact trade is why Apache Kafka's ordering
guarantee is scoped the way it is, discussed at length in dimension 8.

**Delivery guarantee against cost and complexity.** At-most-once is nearly
free, at-least-once needs acknowledgment and redelivery machinery, and
anything called exactly-once needs deduplication state that costs storage and
coordination. This is not a binary choice the pattern makes for you, and
dimension 8 treats it as its own axis because conflating it with the pattern
itself is the most common source of production incidents.

**Consistency against availability.** A publisher that must know a
subscriber received a message before it continues is really doing
Request-Reply with extra steps, and the Azure guidance names this directly, a
subscriber that needs to acknowledge or communicate status back to the
publisher should use a Request-Reply pattern on a separate reply channel
rather than repurpose the publish channel
([Publisher-Subscriber pattern, Problems and considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
verified 2026-08-02). Publisher-Subscriber, used as intended, gives up
synchronous confirmation in exchange for availability, both the publisher's
and the subscribers'.

**Operability against simplicity.** A broker is an additional piece of
infrastructure with its own failure modes, its own capacity planning, its own
on-call rotation. For two collaborating services this cost dwarfs the benefit.
For fifteen independently deployed services it is the only sane way to keep
the dependency graph from becoming an unmaintainable mesh.

## 4. Applicability and non-applicability

Reach for Publisher-Subscriber when the following hold.

- An event needs to reach a number of consumers that is not fixed and not
  known to the publisher at build time, and the count is expected to grow.
- The consuming systems are independently developed, deployed, or owned,
  possibly in different languages or on different release cadences.
- The publisher can move on without waiting for a response, because the
  interaction is naturally asynchronous.
- The system already accepts eventual consistency between the event and its
  effects downstream, rather than requiring one atomic transaction across
  publisher and every subscriber.
- Consumers have different availability windows than the publisher, and the
  broker's retained messages let a consumer that was offline catch up later.

Azure's own "when to use this pattern" guidance lists broadcasting to a
significant number of consumers, communicating across independently
developed applications, tolerating asynchronous delivery, accepting eventual
consistency, and supporting consumers with different uptime requirements than
the publisher, as the five situations the pattern targets
([Publisher-Subscriber pattern, When to use this pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
verified 2026-08-02).

Do NOT reach for Publisher-Subscriber in these cases, and the reason
matters more than the rule. This is the non-applicability list.

- **There are only a few consumers and their needs diverge sharply.** The
  broker's overhead buys nothing here. A direct call or a handful of
  dedicated queues is simpler to reason about and to operate. Azure states
  this plainly, an application with only a few consumers that need
  significantly different information gets no scaling benefit from a broker,
  only added complexity
  ([Publisher-Subscriber pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
  verified 2026-08-02).
- **The caller needs a near real-time response from the consumer.** Pub-Sub
  introduces broker latency on top of network latency, and it has no notion
  of a return value at all. Use Request-Reply, or a direct synchronous call,
  when the caller genuinely needs an answer before it can proceed.
- **Consumers must process messages in one specific, guaranteed order across
  the whole stream.** The same Azure guidance is explicit that "pub/sub
  systems generally don't guarantee ordering across subscribers, and
  maintaining order adds significant constraints to the broker and consumer
  design"
  ([Publisher-Subscriber pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
  verified 2026-08-02). Partitioned, key-scoped ordering is achievable, as
  dimension 8 shows, but total ordering across every subscriber is not what
  this pattern offers.
- **The operation must be one atomic transaction across the publisher and
  every consumer.** Publish-Subscribe is inherently asynchronous and
  eventually consistent. A distributed transaction spanning publisher and
  subscribers belongs to the Saga pattern or to a direct database
  transaction, never to a fire-and-forget broadcast.
- **The publisher and the single, known consumer are stable and unlikely to
  change.** If removing the broker and replacing it with a direct function
  call or a single dedicated queue leaves the design working exactly as
  well, the broker is a cost with no offsetting benefit, and it should not be
  there.

## 5. Structure

Three participants, named for the role each plays rather than for a generic
class name.

- **Publisher.** The component that detects a state change or a completed
  action and packages it as a message, addressed to a channel rather than to
  any specific receiver. The publisher's only responsibility is to hand the
  message to the input channel and continue. It never knows the number of
  subscribers, their identity, or whether they exist at all.
- **Broker (or event bus, or messaging infrastructure).** The intermediary
  that owns the input channel, replicates each incoming message across every
  matching output channel, and typically also owns subscription management,
  retry policy, retention, and delivery guarantees. Hohpe and Woolf describe
  this as splitting one input channel into multiple output channels, one per
  subscriber
  ([Enterprise Integration Patterns, Publish-Subscribe Channel](https://www.enterpriseintegrationpatterns.com/patterns/messaging/PublishSubscribeChannel.html),
  verified 2026-08-02).
- **Subscriber (or consumer).** A component that registers interest in a
  channel, or in a filtered subset of that channel's messages, and receives
  its own copy of every matching message. Subscribers act independently, and
  the pattern makes no promise that any two subscribers process a message at
  the same time, in the same order relative to each other, or even at all if
  one subscriber is offline and configured to not retain a backlog.

A fourth participant appears in almost every real deployment even though it
is absent from the textbook diagram. The **subscription** is a durable
record, owned by the broker, that binds one subscriber's output channel to a
selection of the input channel's messages, whether that selection is a whole
topic, a content filter, or a wildcard pattern. Google Cloud Pub/Sub and
Azure Service Bus both treat the subscription, not the subscriber process, as
the thing that accumulates backlog while a consumer is offline, which is why
a subscriber can crash and restart without losing messages published during
the outage, provided the subscription itself was never deleted.

## 6. ASCII structure diagram

```
                         +--------------------+
                         |      BROKER        |
                         |  (event bus, topic  |
                         |   or exchange)      |
                         +--------------------+
                          ^                  |
                          |                  | fan-out, one
    publish(event)        |                  | copy per match
                          |                  v
   +-----------+          |         +------------------+
   | PUBLISHER | ---------+         | SUBSCRIBER A      |
   +-----------+                    | (subscription. on |
                                     |  topic "orders")  |
                                     +------------------+
                                              |
                                     +------------------+
                                     | SUBSCRIBER B      |
                                     | (subscription.    |
                                     |  filtered, VIP)    |
                                     +------------------+
                                              |
                                     +------------------+
                                     | SUBSCRIBER C      |
                                     | (offline, backlog  |
                                     |  held by broker)   |
                                     +------------------+

  Publisher knows only the broker's input channel.
  Broker knows every live subscription and its filter.
  Subscribers know only the broker, never each other,
  never the publisher.
```

## 7. Dynamics

At runtime, four things happen in sequence for a single published event,
and the fourth is the one most implementations get wrong.

1. The publisher constructs a message, an envelope around the event payload,
   and sends it to the broker's input channel, typically identified by a
   topic name. The publisher's send call returns as soon as the broker has
   durably accepted the message, not when any subscriber has processed it.
2. The broker matches the message against every live subscription. Matching
   is by exact topic name, by a wildcard pattern such as `orders.*`, or by
   inspecting the message's own content, depending on what the broker
   supports. Redis Pub/Sub, for example, supports pattern matching through
   `PSUBSCRIBE`, and a client subscribed to `news.*` receives every message
   published to `news.art.figurative` or `news.music.jazz` without
   enumerating either channel by name
   ([Redis Pub/Sub, Pattern-matching subscriptions](https://redis.io/docs/latest/develop/pubsub/),
   verified 2026-08-02).
3. The broker copies the message onto each matching subscriber's output
   channel. This is a genuine copy, not a shared reference, which is the
   property that makes subscriber processing order irrelevant to correctness
   in a way in-process Observer notification cannot guarantee without
   deliberate cloning.
4. Each subscriber consumes at its own pace, independent of every other
   subscriber. What happens after a subscriber finishes, or fails to finish,
   processing a message is where the delivery guarantee chosen for that
   subscription takes over, acknowledgment for at-least-once, no
   acknowledgment for at-most-once, and idempotency tracking for anything
   presented as exactly-once. This is expanded fully in dimension 8.

```
Publisher      Broker (topic. orders)     Sub A          Sub B          Sub C
   |                    |                   |               |              |
   |--publish(evt)----->|                   |               |              |
   |<--ack(accepted)----|                   |               |              |
   |                    |--copy(evt)------->|               |              |
   |                    |--copy(evt)------------------------>|              |
   |                    |     (Sub C offline, queued at      |              |
   |                    |      the subscription until it     |              |
   |                    |      reconnects)                   |              |
   |                    |                   |--ack---------->|              |
   |                    |                   |               |--ack-------->|
   |                    |<..............reconnect(Sub C)..................|
   |                    |--copy(evt, held)------------------------------->|
   |                    |                   |               |              |--ack-->|
```

The key observation the diagram is built to make visible. The publisher's
timeline ends after the first two arrows. Everything after that is entirely
between the broker and each subscriber, on that subscriber's own schedule,
which is the whole reason the publisher never has to change when a new
subscriber, or a slow subscriber, or a temporarily offline subscriber,
appears.

## 8. Implementation variants

**Topic-based fan-out.** The most common shape, one named channel per
category of event, subscribers pick channels or channel wildcards. This is
what Redis Pub/Sub, MQTT, and the simplest use of Kafka topics all implement,
and it is the shape the EIP diagram itself depicts.

**Content-based routing.** The broker inspects message headers or the
payload itself and delivers only to subscriptions whose filter matches. The
Azure guidance calls this out directly as an alternative to topics when
subscriber interest cuts across topic boundaries, letting each subscriber
specify the content it needs rather than filtering a broad topic client-side
([Publisher-Subscriber pattern, Subsets of messages](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
verified 2026-08-02).

**Log-based streaming with consumer groups.** Apache Kafka generalizes both
a point-to-point queue and a broadcast Publish-Subscribe Channel through one
abstraction, the consumer group. "When all the consumer instances have the
same consumer group" the behaviour mirrors a traditional queue balancing
load across the group, and when instances belong to different consumer
groups the system behaves like publish-subscribe and every message is
broadcast to every group
([Apache Kafka, Introduction, Unified messaging model](https://kafka.apache.org/082/getting-started/introduction/),
verified 2026-08-02). Within this model, ordering is scoped to a single
partition. Kafka states plainly that it "only provides a total order over
messages within a partition, not between different partitions," and that a
consumer instance sees messages in the order they are stored in that
partition's log
([Apache Kafka, Introduction](https://kafka.apache.org/082/getting-started/introduction/),
verified 2026-08-02). To preserve the relative order of related events, the
producer supplies a partition key, and every message carrying the same key
is routed to the same partition, which is the mechanism the Go example in
this section reproduces in miniature. This is the practical resolution to
the ordering force from dimension 3, ordering is available, but only within
the scope of a key, never globally across the topic.

**Per-message parallel leasing, no partitions.** Google Cloud Pub/Sub takes
a different design. Rather than binding order and parallelism to a fixed
partition count, it leases individual messages to subscriber clients and
tracks each message's processing state independently, which the
documentation frames as "per-message parallelism, rather than partition-based
messaging," intended to maximize subscriber-side parallelism
([Google Cloud Pub/Sub overview](https://docs.cloud.google.com/pubsub/docs/overview),
verified 2026-08-02). The trade is the mirror image of Kafka's, Cloud
Pub/Sub achieves high default parallelism at the cost of ordering, and only
offers ordering when a publisher explicitly opts into an ordering key on a
region-scoped subscription, a narrower guarantee than a Kafka partition.

**Sharded channels for horizontal scale.** Redis introduced sharded
Pub/Sub in version 7.0 specifically so that channel traffic could be
confined to the cluster shard that owns the channel's slot, rather than
propagating every published message to every node in the cluster, which
Redis states "restricts the propagation of messages to be within the shard
of a cluster," letting Pub/Sub scale horizontally by adding shards rather
than by growing every node's fan-out cost
([Redis Pub/Sub, Sharded Pub/Sub](https://redis.io/docs/latest/develop/pubsub/),
verified 2026-08-02).

**Push versus pull delivery.** A push subscription has the broker deliver
each message to a subscriber-supplied endpoint, commonly an HTTP webhook, the
moment it arrives. A pull subscription has the subscriber actively fetch
messages on its own schedule. Google Cloud Pub/Sub supports both, describing
push delivery as messages sent "as HTTP POST requests to webhooks" while pull
leaves the fetch cadence to the subscriber
([Google Cloud Pub/Sub overview](https://docs.cloud.google.com/pubsub/docs/overview),
verified 2026-08-02). Push is simpler to wire up and gives the broker
control over back pressure by throttling delivery. Pull gives the subscriber
control over its own concurrency and is the natural fit for a worker pool
that wants to fetch a batch at a time.

**Delivery guarantees, and the honest scope of "exactly once."** Every real
broker offers one of three delivery contracts, and the choice is orthogonal
to which fan-out mechanism is used above it.

- **At-most-once.** The broker attempts delivery once and does not retry on
  failure. Redis Pub/Sub is explicit about this, "if the subscriber is unable
  to handle the message, for example due to an error or a network
  disconnect, the message is forever lost"
  ([Redis Pub/Sub, Delivery semantics](https://redis.io/docs/latest/develop/pubsub/),
  verified 2026-08-02). MQTT names the equivalent its Quality of Service
  level zero, "a fire and forget mechanism where the sender does not expect
  an acknowledgment or guarantee of message delivery"
  ([HiveMQ, MQTT Essentials Part 6, QoS](https://www.hivemq.com/blog/mqtt-essentials-part-6-mqtt-quality-of-service-levels/),
  verified 2026-08-02).
- **At-least-once.** The broker retains the message until the subscriber
  acknowledges it, redelivering on timeout or failure, which guarantees
  delivery at the cost of possible duplicates. MQTT's QoS 1 matches this
  exactly, the sender stores the message until it receives a PUBACK
  acknowledgment and retransmits automatically on timeout
  ([HiveMQ, MQTT Essentials Part 6, QoS](https://www.hivemq.com/blog/mqtt-essentials-part-6-mqtt-quality-of-service-levels/),
  verified 2026-08-02). Azure's guidance recommends designing subscribers to
  handle messages idempotently precisely because at-least-once is the
  practical default for most production brokers
  ([Publisher-Subscriber pattern, Delivery guarantees](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
  verified 2026-08-02).
- **Exactly-once, and why the claim needs its scope inspected before you
  trust it.** MQTT's QoS 2 implements a four-part handshake, PUBLISH,
  PUBREC, PUBREL, PUBCOMP, with a stored packet identifier on both ends to
  prevent duplicate processing
  ([HiveMQ, MQTT Essentials Part 6, QoS](https://www.hivemq.com/blog/mqtt-essentials-part-6-mqtt-quality-of-service-levels/),
  verified 2026-08-02), and Kafka achieves an analogous result through an
  idempotent producer, where "each batch of messages sent to Kafka will
  contain a sequence number that the broker will use to dedupe any
  duplicate send," combined with a transactions API for atomic writes across
  partitions
  ([Confluent, Exactly-once semantics are possible](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/),
  verified 2026-08-02). In both cases the same source that makes the claim
  also states its boundary. Confluent's own documentation warns that "the
  exactly-once guarantee is scoped within Kafka Streams' internal processing
  only; if the event streaming app makes an RPC call to update some remote
  store, or uses a customized client to directly read or write to a Kafka
  topic, the resulting side effects would not be guaranteed exactly once"
  ([Confluent, Exactly-once semantics are possible](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/),
  verified 2026-08-02). Judgement, not a sourced fact, from here on. Every
  time a system claims exactly-once delivery, the correct engineering
  response is to ask exactly-once between which two points, because the
  guarantee is real inside the messaging fabric and almost never survives a
  side effect on an external system, a database write, an email send, a
  webhook call, unless that side effect is itself made idempotent or wrapped
  in the same transactional boundary.

## 9. Known production uses

- **Apache Kafka at LinkedIn.** Kafka was built at LinkedIn starting in
  2010 by Jay Kreps, Neha Narkhede, and Jun Rao specifically to move member
  activity events, page views, search queries, and ad impressions, through a
  single durable, high-throughput channel that fed both offline batch
  analytics and online services, rather than maintaining a separate
  point-to-point pipe per consuming team (Jay Kreps, Neha Narkhede, and Jun
  Rao, "Kafka. a Distributed Messaging System for Log Processing," NetDB
  Workshop, 2011,
  [paper PDF via Apache Confluence](https://cwiki.apache.org/confluence/download/attachments/27822226/Kafka-netdb-06-2011.pdf?version=1&modificationDate=1311164782000&api=v2),
  verified 2026-08-02, accessible). Activity tracking, one publisher stream
  reaching an unbounded and evolving set of independent downstream consumer
  groups, is the textbook Publisher-Subscriber problem from dimension 2, and
  it is the exact reason the consumer-group abstraction was designed to
  subsume both queuing and pub-sub in a single system
  ([Apache Kafka, Introduction](https://kafka.apache.org/082/getting-started/introduction/),
  verified 2026-08-02).
- **Google Cloud Pub/Sub.** Google's managed offering is described as "an
  asynchronous and scalable messaging service that decouples services
  producing messages from services processing those messages," where
  "publishers send events to the Pub/Sub service, without regard to how or
  when these events are to be processed"
  ([Google Cloud Pub/Sub overview](https://docs.cloud.google.com/pubsub/docs/overview),
  verified 2026-08-02). This is Publisher-Subscriber offered as a first
  class managed cloud primitive rather than a pattern applied on top of a
  general purpose queue.
- **Amazon Simple Notification Service.** AWS documents SNS as "a fully
  managed service that provides message delivery from publishers, producers,
  to subscribers, consumers," where publishers send to a topic that acts as
  "a logical access point and communication channel"
  ([What is Amazon SNS](https://docs.aws.amazon.com/sns/latest/dg/welcome.html),
  verified 2026-08-02). AWS's own worked example demonstrates the fan-out
  scenario directly, a single message published when an order is placed is
  replicated to multiple SQS queues, one processed by an order fulfillment
  service, another feeding a data warehouse for analysis, with each
  consumer added by subscribing a new queue rather than modifying the
  publisher
  ([What is Amazon SNS, Application integration](https://docs.aws.amazon.com/sns/latest/dg/welcome.html),
  verified 2026-08-02).
- **Redis Pub/Sub in real-time chat and presence systems.** Redis implements
  the `SUBSCRIBE`, `UNSUBSCRIBE`, and `PUBLISH` commands as a direct
  realization of "the Publish/Subscribe messaging paradigm where senders,
  publishers, are not programmed to send their messages to specific
  receivers, subscribers. Rather, published messages are categorized into
  channels, without knowledge of what, if any, subscribers there may be"
  ([Redis Pub/Sub](https://redis.io/docs/latest/develop/pubsub/),
  verified 2026-08-02), and the documentation itself points to a worked
  multi-user web chat example built on exactly this primitive.
- **MQTT across the Internet of Things.** MQTT's broker-mediated topic model
  and its three explicit quality-of-service levels are the standard
  transport for constrained IoT devices, precisely because a device can
  publish a sensor reading without knowing, or caring, how many downstream
  systems, a dashboard, an alerting service, a data lake ingester, are
  subscribed to that topic at any given moment
  ([HiveMQ, MQTT Essentials Part 6](https://www.hivemq.com/blog/mqtt-essentials-part-6-mqtt-quality-of-service-levels/),
  verified 2026-08-02).

## 10. Consequences

**Positive.**

- Publishers and subscribers can be developed, deployed, and scaled on
  independent schedules, because neither side holds a reference to the
  other, only to the broker, which is the coupling reduction Azure names as
  the pattern's headline benefit
  ([Publisher-Subscriber pattern, Solution](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
  verified 2026-08-02).
- A subscriber's failure is isolated. One consumer crashing, or falling
  behind, does not block the publisher or any other subscriber, since each
  subscriber reads from its own copy of the stream.
- New consumers are added at zero cost to the publisher. Subscribing a new
  team's service to an existing topic requires no change anywhere upstream.
- Consumers that are temporarily offline can catch up later, because most
  production brokers retain unconsumed messages against a durable
  subscription rather than discarding them the instant the publisher sends.
- The broker becomes a natural integration point across languages,
  platforms, and even on-premises and cloud environments, since every party
  only needs to speak the broker's wire protocol.

**Negative.**

- The dependency graph becomes invisible from source code alone. Answering
  "who consumes this event and what happens if I change its shape" now
  requires querying the broker's subscription list or a service catalog,
  not reading a call site.
- Ordering across the whole stream is generally not available, and where it
  is available it is scoped to a partition or an ordering key, never global,
  a constraint every subscriber's processing logic must be written to
  tolerate.
- The broker becomes a new operational dependency with its own capacity
  limits, its own failure modes, and its own on-call burden, and a broker
  outage now affects every publisher and subscriber that depends on it
  simultaneously.
- Debugging a message's path end to end is harder than debugging a
  direct call stack, because the flow crosses process and often machine
  boundaries and there is no single stack trace to read.
- Message schema changes ripple to every subscriber independently, and a
  breaking change discovered late is discovered separately, and often
  painfully, by each downstream team rather than caught at compile time by
  a shared interface.

## 11. Failure modes and misuse

**Poison message stalling a consumer group.** Symptom. One subscriber's
processing rate drops to near zero, its lag metric climbs steadily, and logs
show the same message identifier being retried repeatedly. Cause. A
malformed message, or a message whose processing depends on a resource that
is permanently unavailable, causes the handler to fail every single time,
and an at-least-once broker keeps redelivering it because a failed handler
looks identical to a slow one. Fix. Route messages that exceed a bounded
retry count to a dead-letter queue rather than retrying indefinitely. AWS
SQS implements this through a redrive policy where a `maxReceiveCount`
threshold determines how many times a message can be received before it
moves to the configured dead-letter queue, and AWS is explicit that DLQs
exist "for debugging your application because you can isolate unconsumed
messages to determine why processing did not succeed"
([Amazon SQS, Using dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
verified 2026-08-02). The Python example in the code section implements
exactly this bound, routing a message to a `dead_letters` list after three
failed attempts rather than retrying forever.

**Assumed global ordering.** Symptom. A downstream projection ends up in a
state that contradicts the sequence of business events, for example a
cancellation event applied before the creation event it was meant to
cancel, even though the publisher sent them in the correct order. Cause.
The consumer, or the team that wrote it, assumed the broker preserves the
order in which the publisher sent messages across the whole topic, when the
broker in fact only orders messages within a partition, or does not order
them at all. Fix. Route causally related events under the same partition
key, verify the specific broker's documented ordering scope rather than
assuming it, and where cross-key ordering genuinely matters, include a
sequence number or a causal timestamp in the payload and let the consumer
enforce order itself.

**Fan-out amplification overwhelming a downstream dependency.** Symptom. A
single publish causes a sudden spike in load on a shared downstream system,
a database, a third-party API, an email provider, because every one of many
subscribers reacted to the same event at the same moment. Cause. The number
of subscribers on a topic grew over time, exactly as the pattern intends,
but nobody revisited the assumption that each subscriber's reaction is cheap
and independent. A topic with genuinely one publisher and few subscribers
scales differently once it accumulates twenty. Fix. Rate limit or stagger
subscriber-side processing against the shared dependency, and treat the
number of live subscriptions on a hot topic as a capacity number that is
tracked and alerted on, not an assumption that holds forever.

**Subscriber lag becoming an unbounded backlog.** Symptom. Broker disk usage
or memory climbs continuously, and eventually the broker either evicts
messages early, breaking the retention guarantee subscribers were relying
on, or runs out of storage entirely. Cause. One subscriber consistently
processes messages slower than the publisher produces them, and the broker
faithfully retains everything that subscriber has not yet acknowledged. This
is the same failure the Azure guidance names directly, "when subscribers
can't keep up, unprocessed messages accumulate in the broker and can deplete
its resources"
([Publisher-Subscriber pattern, Backpressure and scaling](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
verified 2026-08-02). Fix. Configure broker-side flow control to cap the
number of unacknowledged messages outstanding for a subscriber, and scale
out that subscriber horizontally using the Competing Consumers pattern once
flow control alone is not enough
([Publisher-Subscriber pattern, Backpressure and scaling](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
verified 2026-08-02).

**Duplicate side effects from at-least-once delivery.** Symptom. A customer
receives the same confirmation email twice, or a payment is charged twice,
for a single logical event. Cause. The broker retried delivery after a
subscriber crashed immediately after completing its side effect but before
sending the acknowledgment, which is indistinguishable, from the broker's
point of view, from a subscriber that never processed the message at all.
Fix. Make every subscriber handler idempotent, keyed on a message
identifier the broker guarantees is stable across redeliveries, so applying
the same message twice produces the same result as applying it once, rather
than trying to make the broker deliver exactly once, which dimension 8
shows is a narrower guarantee than it sounds.

**Treating the publish channel as a request-reply channel.** Symptom. A
publisher's code grows a wait loop, or a polling call, checking whether a
subscriber has finished processing an event it recently published, and that wait
occasionally times out under load with no clean recovery path. Cause. The
interaction actually needs a response, and Publish-Subscribe channels are
unidirectional by design. Fix. Recognise the need for a response as a
different pattern. Use Request-Reply on a dedicated reply channel, exactly
as Azure's own guidance recommends when a subscriber must communicate status
back to the publisher
([Publisher-Subscriber pattern, Bidirectional communication](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
verified 2026-08-02), rather than bolting a synchronous expectation onto an
asynchronous channel.

## 12. Trade-off matrix

Compared against named alternatives across the forces named in dimension 3.

| Force | Publisher-Subscriber (broker) | Observer (GoF, in-process) | Point-to-point queue | Request-Reply | Direct synchronous call |
|---|---|---|---|---|---|
| Coupling to receiver identity | None, publisher knows only the topic | None, but subject holds live references | None, but sender addresses one queue per logical consumer | Sender addresses one reply channel | Total, caller names the callee |
| Process and language boundary | Crosses freely | Same process, same runtime | Crosses freely | Crosses freely | Same process usually |
| Fan-out to many independent receivers | Native, one input channel splits to many | Native within a process, list of observers | Requires one queue per consumer, manual fan-out | Not applicable, one reply target | Not applicable, one callee |
| Ordering across all receivers | Not guaranteed, scoped to a partition or key at best | Undefined by the pattern, dispatch order only | Preserved per queue, single consumer sees producer order | Not applicable | Caller's own call order |
| Delivery on process crash | Broker dependent, commonly durable and retained | Lost, in-memory only | Broker dependent, commonly durable | Broker dependent | Not applicable |
| Back pressure when a receiver is slow | Broker queue plus flow control policy | None, subject blocks on every observer | Broker queue plus consumer scaling | Caller blocks or times out | Caller blocks |
| Response available to sender | No, unidirectional by design | Return value possible if the interface allows it | No, unless paired with a reply queue | Yes, that is its purpose | Yes, immediate |
| New consumer added without touching sender | Yes | No, subject's registration list still needs the new reference added at runtime, but no redeploy of the subject's logic | Requires a new queue and routing change | Not applicable | No, requires a new call site |
| Operability and observability | Broker exposes topics, subscriptions, lag | Poor, registry lives in process memory | Queue depth and consumer lag visible per queue | Standard RPC tracing applies | Ordinary stack trace |

Reading of the table. Publisher-Subscriber wins decisively the moment the
receiver set is large, independently owned, or expected to grow, because
every alternative in this table either requires the sender to change when a
receiver is added, or gives up the cross-process reach entirely. A
point-to-point queue is the right choice instead when there really is
exactly one logical consumer per message, since it keeps ordering and
delivery guarantees simpler without paying for fan-out machinery nobody
uses. Observer wins when everything stays inside one process and the
interaction is genuinely synchronous and cheap, since a broker's network
hop and durability guarantees are pure overhead in that context. Request-
Reply and a direct call both win the instant the caller actually needs an
answer, because Publish-Subscribe has no channel back, and trying to fake
one on top of a publish channel produces the failure mode documented in
dimension 11.

## 13. Related and incompatible patterns

**Publisher-Subscriber versus Observer, resolved.** These two are
conflated constantly, in part because the Gang of Four book itself lists
Publish-Subscribe as an alias for Observer. They are different in every
property that governs how a system actually fails in production. Observer
is a subject holding direct references to its dependents, calling their
update method synchronously, in the same process, with no delivery
guarantee beyond "the call happened or it threw." Publisher-Subscriber is a
broker holding subscription records, copying a message to each matching
output channel, asynchronously, commonly across processes, with an explicit
delivery contract the broker documents and enforces. The practical test from
dimension 3 restated here. If removing the network and the broker leaves
the behaviour intact, the code is Observer wearing a Publish-Subscribe name.
If the design needs a component that neither the sender nor the receiver
owns, and that survives either side restarting, it is genuinely
Publisher-Subscriber.

**Competing Consumers.** When one subscriber alone cannot keep pace with a
topic's publish rate, Competing Consumers scales that single logical
subscriber out into a pool of worker processes that share the same
subscription, each message still delivered once to the subscription as a
whole. Azure names this explicitly as the escalation path once flow control
alone cannot absorb subscriber lag
([Publisher-Subscriber pattern, Backpressure and scaling](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
verified 2026-08-02). The two patterns compose cleanly, Publish-Subscribe
decides how many independent subscriptions exist, Competing Consumers decides
how many workers serve each one.

**Event Sourcing and CQRS.** A system built on Event Sourcing frequently
publishes each committed event onto a Publisher-Subscriber channel so that
read-model projections, in a CQRS split, can update independently and
asynchronously from the write side. Publish-Subscribe is the transport most
often chosen to carry those events from the event store to the projections,
but the two are not the same pattern, Event Sourcing is about how state is
persisted and CQRS is about how reads and writes are separated, while
Publisher-Subscriber is only about how the resulting notifications reach
independent listeners.

**Saga.** A long-running distributed transaction coordinated through a
choreography-style Saga is commonly implemented as a chain of publishers and
subscribers, each service publishing the event that represents its
completed step and subscribing to the events that trigger its own next
step. Publisher-Subscriber supplies the transport, Saga supplies the
compensation logic when a step fails partway through the chain, and neither
pattern is sufficient on its own to build reliable distributed transactions.

**Transactional Outbox.** Publishing a message and committing a database
change are two separate operations against two separate systems, and doing
them as two independent calls risks a crash between them leaving the
database updated with no corresponding event ever published, or an event
published for a transaction that later rolled back. The Transactional Outbox
pattern writes the outgoing message to a table in the same local database
transaction as the business change, then a separate process reads that
table and performs the actual publish, closing exactly this gap. Any
production Publisher-Subscriber deployment whose publish step is triggered by
a database write should treat Transactional Outbox as the default, not an
optional extra.

**Circuit Breaker and Retry.** Both apply on the subscriber side of a
Publisher-Subscriber deployment, not to the pattern itself. A subscriber
handler that calls an external, occasionally failing dependency as part of
processing a message should wrap that call in Retry for transient failures
and Circuit Breaker to stop hammering a dependency that is down, exactly as
those two entries in this repository describe. Neither pattern is
incompatible with Publisher-Subscriber, they simply operate one layer
inward, inside the handler that consumes each delivered message.

**Incompatible with, none recorded.** Publisher-Subscriber has no pattern
that it structurally cannot coexist with. The closer question is always
whether a given interaction is asynchronous and broadcast enough to deserve
the pattern at all, which dimension 4's non-applicability list already
answers directly.

## 14. Refactoring path in and out

**Introducing Publisher-Subscriber into code that has none, step by step.**

1. Identify a component making direct calls into more than one downstream
   collaborator purely to notify them that something happened, with no
   expectation of a return value from any of them. This is the seam.
2. Introduce a broker, starting with the smallest one that satisfies the
   actual requirement, an in-process event bus if everything still lives in
   one process, a managed cloud broker the moment two independently
   deployed services need to communicate.
3. Replace the direct calls with a single publish call to a named topic,
   carrying an immutable, versioned event payload rather than a mutable
   object reference, so future subscribers never depend on an object the
   publisher might change shape later.
4. Convert each existing direct call site into a subscriber, registered
   against the new topic, and verify each one still receives every event it
   previously received directly, using the same integration test that
   covered the direct-call behaviour before the refactor.
5. Only after every existing consumer is confirmed working through the
   broker, remove the publisher's direct references to the old collaborator
   types entirely. This ordering matters, removing the direct references
   before the subscriber side is proven correct turns a refactor into a
   regression with no fallback.
6. Add the delivery guarantee and idempotency handling the new consumers
   actually need, at-least-once with idempotent handlers is the safe
   default absent a specific reason to choose otherwise, per dimension 8.

**Removing Publisher-Subscriber when it stops earning its place.**

1. Confirm the topic genuinely has one stable consumer, or a small, fixed
   consumer set that has not changed in a long time and shows no sign of
   growing. A topic that once needed broadcast flexibility but has settled
   into a single-consumer relationship no longer needs a broker in the
   middle.
2. Inline the subscriber's logic back into a direct call, or, if crossing a
   process boundary is still required, replace the broker with a direct
   point-to-point call or a dedicated queue that carries a simpler,
   narrower delivery contract than a full pub-sub broker offers.
3. Remove the topic and its subscriptions only after the direct path has
   run in parallel and produced identical results for a monitored period,
   never as the very first step, since a broker being removed prematurely
   silently drops any consumer nobody remembered still existed.
4. Retire the broker infrastructure itself, its retention, its monitoring,
   its on-call runbook, only once no topic on it has any live subscription
   left, confirmed from the broker's own subscription listing rather than
   from application source code, exactly because dimension 10 names that
   source code is the wrong place to look for the true consumer list.

## 15. Testing and verification

Testing a Publisher-Subscriber system splits cleanly along the same seam the
pattern itself introduces, the publisher side and the subscriber side can,
and should, be tested independently, which is one of the pattern's genuine
gifts to a test suite.

**Testing the publisher.** Replace the real broker with a fake or an
in-memory double that records every message published, its topic, and its
payload, then assert against that recording rather than against any
subscriber's behaviour. A publisher test should never need a running broker
or a real subscriber to pass, because the publisher's only contract is
"I handed this message to the channel," not "someone eventually acted on
it."

**Testing a subscriber in isolation.** Construct the message payload by
hand, invoke the subscriber's handler directly with it, and assert on the
subscriber's own observable effects, a database row written, a downstream
call made, a metric incremented. This test needs no broker at all, and it
is the cheapest, fastest layer of the suite, so the bulk of subscriber logic
should be covered here rather than through an end-to-end broker round trip.

**Testing delivery-guarantee behaviour specifically.** This is the layer
most suites skip, and it is exactly the layer that catches the failure
modes in dimension 11. Write a test that delivers the same message to the
subscriber's handler twice in a row and asserts the resulting state is
identical to delivering it once, which directly proves the idempotency
dimension 8 and dimension 11 both require for at-least-once delivery. Write
a second test that has the handler fail deterministically on every attempt
and asserts the message reaches the dead-letter path after exactly the
configured retry count, never fewer and never indefinitely, which is the
concrete regression test for the poison-message failure mode.

**Testing the whole broker round trip, sparingly.** A small number of
integration tests should run against a real broker, or a faithful
containerised equivalent, publishing a message and asserting a subscriber
actually receives it, to catch configuration errors, a topic name typo, a
missing subscription, an authentication misconfiguration, that a pure unit
test on either side cannot see. This layer is deliberately kept small
because it is slow and because the publisher-subscriber contract itself,
tested at the unit level on both sides, already covers the majority of
behaviour that matters.

**Consumer-driven contract testing across teams.** Where publisher and
subscriber are owned by different teams, a shared, versioned schema for
each event, checked in continuous integration on both sides, catches a
breaking payload change before it reaches production rather than after a
subscriber starts failing silently on an unrecognised field.

## 16. Observability signals

A healthy Publisher-Subscriber deployment is legible from a small set of
numbers per subscription, and a struggling one shows exactly which of
dimension 11's failure modes is in progress before it becomes an incident.

- **Publish rate and publish latency.** How many messages per second the
  publisher is sending, and how long the broker takes to accept each one.
  A sudden drop in publish rate with no corresponding drop in upstream
  traffic points at a publisher-side problem, not a broker one.
- **Subscription backlog, commonly called lag.** The count of messages a
  subscription has received but not yet acknowledged. A backlog that grows
  monotonically over time, rather than oscillating around a steady baseline,
  is the earliest visible sign of the subscriber-lag failure mode in
  dimension 11, and it should be alerted on well before the broker itself
  starts shedding load.
- **Redelivery and dead-letter counts.** How many times messages are being
  retried, and how many are landing in the dead-letter queue. A dead-letter
  count that is anything other than near zero, sustained, is the direct
  signal of a poison message, and AWS's own guidance frames the DLQ
  explicitly as a debugging surface for exactly this, isolating unconsumed
  messages to determine why processing failed
  ([Amazon SQS, Using dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
  verified 2026-08-02).
- **End-to-end latency via a correlation identifier.** Because a message's
  path crosses process boundaries with no shared call stack, every
  message should carry a correlation identifier that a tracing system can
  follow from the publisher's send through every subscriber's processing, or
  end-to-end latency across the system becomes unmeasurable the moment the
  broker is introduced.
- **Subscription count per topic, tracked as a capacity number.** Since
  fan-out amplification is a function of how many subscriptions exist on a
  hot topic, that count belongs on the same dashboard as downstream
  dependency load, not buried in a broker admin console nobody checks
  routinely.

A healthy dashboard shows publish rate and consumption rate moving together,
backlog oscillating around a small, bounded value rather than climbing, and
dead-letter counts near zero. A failing one shows exactly one of those four
diverging while the others stay flat, which is usually enough on its own to
name which failure mode from dimension 11 is in progress.

## 17. Security and privacy implications

Publisher-Subscriber widens the attack surface in a specific, nameable way,
because it introduces a shared intermediary that both an unauthorized
publisher and an unauthorized subscriber can abuse, and Azure's own guidance
states this directly, "authenticate and authorize both publishers and
subscribers on a per-topic basis. Unauthorized publishers that inject
messages can damage a system as much as unauthorized subscribers that read
them"
([Publisher-Subscriber pattern, Security](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
verified 2026-08-02). Judgement from here, informed by that stated
requirement rather than sourced as a separate fact. An unauthorized
publisher on a trusted topic is a message injection vector into every
subscriber at once, a single compromised credential becomes a fan-out
attack rather than a point attack. An unauthorized subscriber on a sensitive
topic is a data exfiltration channel that scales with how many topics that
credential can read, and because subscriptions are broker state rather than
application code, a rogue subscription can sit unnoticed for a long time if
nobody audits the subscription list regularly.

Encryption in transit between every publisher, the broker, and every
subscriber should be the default, and where message content is sensitive,
encryption at rest inside the broker matters too, since the broker now holds
a durable copy of every message it has not yet delivered to every
subscription, precisely the retention behaviour that makes the pattern
useful for offline consumers in the first place. That same retention is
itself a privacy consideration, a message containing personal data that sits
in a subscription's backlog for days because a subscriber is offline is
personal data at rest for that entire period, and retention policy for the
broker needs to account for that rather than treating the broker as a
transient pipe.

Because the broker decouples publisher from subscriber identity, tracing an
audit question such as "who read this event containing a customer's data"
requires the broker's own access logs and subscription history, not the
publisher's code, which means an organisation adopting this pattern for
anything touching regulated data needs the broker's audit logging turned on
and retained from the start, not added after an incident makes the gap
obvious.

## 18. References

1. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
   Messaging Channels chapter, Publish-Subscribe Channel.
   [enterpriseintegrationpatterns.com](https://www.enterpriseintegrationpatterns.com/patterns/messaging/PublishSubscribeChannel.html),
   verified 2026-08-02.
2. Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides, *Design
   Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley,
   1994, chapter 5, Behavioral Patterns, Observer, on the Publish-Subscribe
   alias.
3. Microsoft, "Publisher-Subscriber pattern," Azure Architecture Center,
   page dated 2026-03-04, updated 2026-06-03.
   [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber),
   verified 2026-08-02.
4. Jay Kreps, Neha Narkhede, and Jun Rao, "Kafka. a Distributed Messaging
   System for Log Processing," NetDB Workshop, 2011.
   [PDF via Apache Confluence](https://cwiki.apache.org/confluence/download/attachments/27822226/Kafka-netdb-06-2011.pdf?version=1&modificationDate=1311164782000&api=v2),
   verified 2026-08-02.
5. Apache Software Foundation, "Introduction," Apache Kafka documentation.
   [kafka.apache.org](https://kafka.apache.org/082/getting-started/introduction/),
   verified 2026-08-02.
6. Confluent, "Exactly-Once Semantics Are Possible. Here's How Apache Kafka
   Does It."
   [confluent.io](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/),
   verified 2026-08-02.
7. Google, "Pub/Sub overview," Google Cloud documentation.
   [docs.cloud.google.com](https://docs.cloud.google.com/pubsub/docs/overview),
   verified 2026-08-02.
8. Amazon Web Services, "What is Amazon SNS," Amazon SNS Developer Guide.
   [docs.aws.amazon.com](https://docs.aws.amazon.com/sns/latest/dg/welcome.html),
   verified 2026-08-02.
9. Amazon Web Services, "Using dead-letter queues in Amazon SQS," Amazon SQS
   Developer Guide.
   [docs.aws.amazon.com](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html),
   verified 2026-08-02.
10. Redis, "Redis Pub/sub," Redis documentation.
    [redis.io](https://redis.io/docs/latest/develop/pubsub/),
    verified 2026-08-02.
11. HiveMQ, "MQTT Essentials Part 6. MQTT Quality of Service Levels."
    [hivemq.com](https://www.hivemq.com/blog/mqtt-essentials-part-6-mqtt-quality-of-service-levels/),
    verified 2026-08-02.

## Code examples

Three implementations, each isolating a different dimension of the pattern
discussed above. All three were run against the toolchain listed for this
entry, TypeScript 7.0.2 via `tsc`, Python 3.14.6, and Go 1.26.4, and each
produced the expected output shown in its comment. A fourth, Swift 6.3.2 via
`swiftc`, was also compiled and run to confirm the in-process broker shape
translates directly, and is described in a closing note rather than listed
in full, since it repeats the TypeScript variant's structure rather than
illustrating a new dimension.

### TypeScript, topic and wildcard matching

Demonstrates a broker that matches a publish against multiple subscriptions,
including a wildcard subscription, and delivers a distinct copy to each.

```typescript
type Handler<T> = (payload: T) => void;

class TopicBroker {
  private subscribers = new Map<string, Set<Handler<unknown>>>();

  subscribe<T>(topicPattern: string, handler: Handler<T>): () => void {
    const set = this.subscribers.get(topicPattern) ?? new Set();
    set.add(handler as Handler<unknown>);
    this.subscribers.set(topicPattern, set);
    return () => set.delete(handler as Handler<unknown>);
  }

  publish<T>(topic: string, payload: T): number {
    let delivered = 0;
    for (const [pattern, handlers] of this.subscribers) {
      if (this.matches(pattern, topic)) {
        for (const handler of handlers) {
          (handler as Handler<T>)(payload);
          delivered += 1;
        }
      }
    }
    return delivered;
  }

  // Only a prefix wildcard is supported, enough to show the shape.
  private matches(pattern: string, topic: string): boolean {
    if (pattern === topic) return true;
    if (!pattern.includes("*")) return false;
    const prefix = pattern.slice(0, pattern.indexOf("*"));
    return topic.startsWith(prefix);
  }
}

const broker = new TopicBroker();
const received: string[] = [];

broker.subscribe<{ orderId: string }>("orders.created", (p) => {
  received.push(`billing saw ${p.orderId}`);
});
broker.subscribe<{ orderId: string }>("orders.*", (p) => {
  received.push(`audit saw ${p.orderId}`);
});

const count = broker.publish("orders.created", { orderId: "A-100" });
console.log(`delivered to ${count} subscribers`);
received.forEach((line) => console.log(line));

// Output, run via `tsc broker.ts && node broker.js`.
// delivered to 2 subscribers
// billing saw A-100
// audit saw A-100
```

### Python, at-least-once delivery with a bounded dead-letter path

Demonstrates the retry-then-dead-letter mechanism described in dimension 8
and the poison-message failure mode from dimension 11.

```python
from dataclasses import dataclass
from collections import defaultdict
from typing import Callable

MAX_ATTEMPTS = 3


@dataclass
class Message:
    topic: str
    payload: dict
    attempts: int = 0


class AtLeastOnceBroker:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Message], bool]]] = defaultdict(list)
        self.dead_letters: list[Message] = []

    def subscribe(self, topic: str, handler: Callable[[Message], bool]) -> None:
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, payload: dict) -> None:
        self._deliver(Message(topic=topic, payload=payload))

    def _deliver(self, message: Message) -> None:
        message.attempts += 1
        for handler in self._subscribers[message.topic]:
            ok = handler(message)
            if not ok:
                if message.attempts >= MAX_ATTEMPTS:
                    self.dead_letters.append(message)
                else:
                    self._deliver(message)
                return


if __name__ == "__main__":
    # A poison handler that always fails lands in the dead-letter list
    # after MAX_ATTEMPTS, never retried forever.
    broker = AtLeastOnceBroker()
    broker.subscribe("orders.created", lambda m: False)
    broker.publish("orders.created", {"orderId": "A-101"})
    print(f"dead letters after permanent failure: {len(broker.dead_letters)}")
    assert len(broker.dead_letters) == 1
    assert broker.dead_letters[0].attempts == MAX_ATTEMPTS

# Output, run via `python3 broker.py`.
# dead letters after permanent failure: 1
```

### Go, per-key partition ordering under concurrency

Demonstrates the partition-key ordering variant from dimension 8, where
messages sharing a key are preserved in order even though the broker
processes different keys concurrently across separate channels.

```go
package main

import (
	"fmt"
	"hash/fnv"
	"sync"
)

type Message struct {
	Key     string
	Payload string
}

type PartitionedBroker struct {
	partitions int
	channels   []chan Message
	wg         sync.WaitGroup
	mu         sync.Mutex
	received   map[string][]string
}

func NewPartitionedBroker(partitions int) *PartitionedBroker {
	b := &PartitionedBroker{
		partitions: partitions,
		channels:   make([]chan Message, partitions),
		received:   make(map[string][]string),
	}
	for i := 0; i < partitions; i++ {
		b.channels[i] = make(chan Message, 16)
		b.wg.Add(1)
		go b.consume(i)
	}
	return b
}

// Same key always maps to the same partition, which is what
// preserves per-key order across a concurrent set of consumers.
func (b *PartitionedBroker) partitionFor(key string) int {
	h := fnv.New32a()
	h.Write([]byte(key))
	return int(h.Sum32()) % b.partitions
}

func (b *PartitionedBroker) Publish(m Message) {
	b.channels[b.partitionFor(m.Key)] <- m
}

func (b *PartitionedBroker) consume(idx int) {
	defer b.wg.Done()
	for m := range b.channels[idx] {
		b.mu.Lock()
		b.received[m.Key] = append(b.received[m.Key], m.Payload)
		b.mu.Unlock()
	}
}

func (b *PartitionedBroker) Close() {
	for _, ch := range b.channels {
		close(ch)
	}
	b.wg.Wait()
}

func main() {
	broker := NewPartitionedBroker(4)
	for i := 1; i <= 5; i++ {
		broker.Publish(Message{Key: "order-42", Payload: fmt.Sprintf("event-%d", i)})
	}
	broker.Close()

	for i, v := range broker.received["order-42"] {
		expected := fmt.Sprintf("event-%d", i+1)
		if v != expected {
			panic("ordering violated within partition key")
		}
	}
	fmt.Println("ordering preserved per key across concurrent partitions")
}

// Output, run via `go run main.go`.
// ordering preserved per key across concurrent partitions
```
