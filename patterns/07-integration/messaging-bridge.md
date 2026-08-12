---
name: Messaging Bridge
slug: messaging-bridge
family: 07-integration
category: Enterprise Integration
aliases: [Message Bridge, Bus Bridge, Broker Bridge]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [channel-adapter, message-translator, point-to-point-channel, publish-subscribe-channel, dead-letter-channel]
incompatible_with: []
verified: 2026-08-02
---

# Messaging Bridge

## 1. Name, aliases, and lineage

The canonical name is Messaging Bridge. It is cataloged as one of the messaging
system patterns in Gregor Hohpe and Bobby Woolf, *Enterprise Integration
Patterns. Designing, Building, and Deploying Messaging Solutions*,
Addison-Wesley, 2003, in the Messaging Systems chapter, alongside Message
Channel, Message Endpoint, and Channel Adapter
([Enterprise Integration Patterns, Messaging Bridge](https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessagingBridge.html),
verified 2026-08-02). Hohpe and Woolf state the intent plainly, to connect two
messaging systems so applications on either side can communicate without
knowing the other system exists.

In vendor documentation the same idea shows up under several names, and a
reader coming from a specific product needs to know they map to the same
pattern.

- **Message Bridge**, the name Apache ActiveMQ and several JMS providers use
  for the component that forwards messages between two brokers or two
  destinations.
- **Bus Bridge**, used in service-bus literature (WSO2, MuleSoft) for a bridge
  that spans two enterprise service buses rather than two raw brokers.
- **Broker Bridge**, the generic vendor-neutral phrase used when the two sides
  are peer brokers of the same or different technology rather than a broker
  and an application.

Two adjacent ideas are commonly conflated with a Messaging Bridge and are worth
separating before reading further, because the failure modes differ.

- **Federation** (as in RabbitMQ Federation, or MQTT broker federation) links
  brokers so a topic or queue is transparently shared, typically pulling
  messages only when a local consumer exists downstream. A bridge, by
  contrast, moves messages unconditionally in a declared direction, whether or
  not anyone is listening on the far side yet
  ([RabbitMQ Shovel documentation, contrasting Shovel with Federation](https://www.rabbitmq.com/docs/shovel),
  verified 2026-08-02).
- **API Gateway** and **Enterprise Service Bus routing** operate on
  request-response HTTP or RPC traffic. A Messaging Bridge operates on
  asynchronous message channels, queues, or topics, and its unit of transfer
  is a message, not a request.

## 2. Problem and context

An enterprise settles on messaging as the way applications talk to each other,
and that decision solves the coupling problem inside one messaging technology.
The trouble starts the moment a second messaging technology enters the
picture, and in any organization beyond a small one it always does. A merger
brings in a company running IBM MQ while the acquirer standardized on Kafka.
A cloud migration adds AWS SQS and EventBridge next to an on-premises
ActiveMQ install that nobody has budget to retire. A partner integration
requires MQTT because the counterpart is an IoT vendor, while the internal
estate runs AMQP. Regulatory or geographic isolation splits one logical
system into two physically separate broker clusters that are not allowed to
share a network path, yet applications on both sides still need to exchange
events.

Hohpe and Woolf frame the problem as ambiguity. Their own description states
that "an enterprise is using Messaging to enable applications to
communicate" but "the enterprise uses more than one messaging system, which
confuses the issue of which messaging system an application should connect
to"
([Enterprise Integration Patterns, Messaging Bridge](https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessagingBridge.html),
verified 2026-08-02). Forcing every application to pick a side and connect
directly to both systems means every application absorbs two client
libraries, two connection-management strategies, two failure modes, and two
sets of credentials. Multiply that by dozens of applications and the
integration surface grows quadratically instead of linearly.

The context in which the pattern belongs is specific. The two systems being
joined already work, each has its own consumers that must keep working
unmodified, and the requirement is to move a defined subset of traffic
between them without either side becoming aware of the other's existence.
That last clause is what separates a Messaging Bridge from simply picking one
technology and migrating everyone to it. A bridge is an integration strategy
for systems that are staying separate, by choice or by constraint, not a step
toward consolidation, though it is sometimes used as a temporary measure
during a longer migration.

## 3. Forces

**Coupling versus consolidation.** The cheapest long-term answer is often to
get everyone onto one broker. That is rarely available on the timeline the
business needs, because of vendor lock-in on one side, a partner's fixed
protocol requirement, sunk investment in queue-based transaction handling, or
a regulatory boundary that forbids merging two networks. A bridge accepts the
duplication of infrastructure in exchange for not forcing a migration.

**Latency versus decoupling.** A bridge adds a hop. Every message crosses an
extra network boundary and, if any format translation happens, an extra
serialize-deserialize cycle. The pattern trades a small, roughly constant
latency tax for not coupling either side's client code to the other side's
protocol.

**Delivery guarantee mismatch.** The two systems being bridged rarely offer
identical delivery semantics. One might be at-least-once with broker-side
acknowledgment, the other might be at-most-once fire-and-forget over a
lightweight transport such as MQTT QoS 0. The bridge has to decide, and state
explicitly, which guarantee it can honor end to end, because it cannot invent
a guarantee neither side provides.

**Operability.** A bridge is a new operational entity. It has its own
liveness, its own backlog, its own restart semantics, and its own failure
mode when either side is unreachable. Every extra bridge instance is another
thing that pages someone at 3 a.m. The pattern favors a small number of
well-monitored bridges over ad hoc point-to-point bridging sprawled across
many teams.

**Consistency and ordering.** A bridge that fans a single source queue out to
multiple consumers on the destination side, or that reads from multiple
source partitions, has to decide whether to preserve per-key ordering across
the hop. Preserving it usually means giving up some parallelism in the
bridge itself.

**Cost.** Every bridged message consumes bandwidth and, on managed cloud
messaging services, is billed per operation on both the consuming and the
publishing side. A bridge that blindly forwards a firehose topic can produce
a bill nobody planned for. The pattern favors bridging a filtered, named
subset of traffic over bridging entire exchanges wholesale.

This pattern favors decoupling and system autonomy above raw throughput.
It sacrifices a small amount of latency and adds one more component that
must be kept alive, in exchange for letting two systems that were never
designed to know about each other exchange messages safely.

## 4. Applicability and non-applicability

Reach for a Messaging Bridge when the situation matches this list.

- Two messaging systems already exist independently, each with active
  consumers, and neither can be retired or replaced on the required
  timeline.
- A specific, identifiable subset of traffic needs to cross from one system
  to the other, and that subset is stable enough to name (a queue, a topic
  pattern, an exchange).
- The two systems differ in protocol, vendor, network zone, or
  organizational ownership, so a direct multi-protocol client on every
  application is undesirable.
- The bridging requirement is expected to be long lived, or at minimum
  long enough that a dedicated, monitored component is worth building
  rather than a one-off script.
- Message format translation, if needed, is bounded and expressible as a
  Message Translator sitting inside or beside the bridge.

Do NOT reach for a Messaging Bridge in these cases.

- Only one system will exist going forward. If the real goal is
  consolidation, build a one-time migration or batch ETL job instead of a
  standing bridge. A bridge that nobody plans to retire tends to become
  permanent infrastructure debt.
- The interaction is synchronous request-response rather than asynchronous
  messaging. That need is served by an API Gateway, a reverse proxy, or a
  remote procedure invocation pattern, not a Messaging Bridge.
- The two systems are actually the same broker technology and the real
  requirement is scaling or high availability across regions. That is
  Federation or the broker's own clustering, and Federation's
  consumer-driven pull semantics are usually the better fit than a bridge's
  unconditional push
  ([RabbitMQ Shovel documentation](https://www.rabbitmq.com/docs/shovel),
  verified 2026-08-02).
- Every message from one system needs to reach the other verbatim with zero
  filtering. At that scale, a full replication or mirroring feature built
  into the broker (cross-region replication in Kafka via MirrorMaker, or a
  managed replica) is usually cheaper to operate correctly than a
  hand-rolled bridge doing the same job with weaker guarantees.
- Strict exactly-once, cross-system transactional delivery is required and
  neither broker supports distributed transactions or idempotent
  consumption. A bridge cannot manufacture a two-phase commit that the
  underlying systems do not offer. Forcing one in causes silent duplicate
  or lost messages under failure, which is worse than admitting the
  constraint up front.
- The volume is a handful of messages a day exchanged between two teams who
  could just as well use a shared file drop or a manual export. Building a
  bridge for negligible traffic is solving a problem that does not exist
  yet.

## 5. Structure

A Messaging Bridge is composed of a small, fixed set of participants, though
implementations vary in how tightly they are packaged into one process.

- **Source system.** The messaging system, broker, or channel the message
  originates from. It is unaware that a bridge exists. It simply has a
  consumer attached like any other consumer.
- **Bridge consumer (inbound Channel Adapter).** Reads messages from the
  source system using that system's native protocol and client library.
- **Message Translator (optional).** Converts the message from the source
  system's wire format, headers, and addressing scheme into the destination
  system's expected shape. Present only when the two systems disagree on
  format, absent when both speak, for example, plain AMQP and only the
  broker identity differs.
- **Bridge producer (outbound Channel Adapter).** Publishes the translated
  message onto the destination system using that system's native protocol.
- **Destination system.** The messaging system that receives the forwarded
  message. Like the source, it is unaware the message did not originate
  natively there. It simply has a producer attached.
- **Bridge coordinator.** The logic that ties the consumer and producer
  together, covering acknowledgment sequencing, retry policy on either leg,
  backlog and dead-letter handling, and the running state of the bridge
  (connected, reconnecting, stopped).

Spring Integration's own documentation describes the minimal case plainly. It
states that "a messaging bridge is a relatively trivial endpoint that
connects two message channels or channel adapters"
([Spring Integration Reference, Bridge](https://docs.spring.io/spring-integration/reference/bridge.html),
verified 2026-08-02). The word trivial there is doing real work. When both
sides already speak the same format, the bridge coordinator reduces to a
subscribe-and-republish loop with no translation step, which is exactly the
`<int:bridge>` element Spring Integration ships. The complexity in a
production bridge lives almost entirely in the coordinator's failure
handling, not in the happy-path forwarding logic.

## 6. ASCII structure diagram

```
+--------------------+       +---------------------------------------+       +------------------------+
|   Source System     |       |            Messaging Bridge            |       |  Destination System     |
| (Broker A / Bus A)   |       |                                       |       |  (Broker B / Bus B)      |
|                      |       |  +---------+   +------------------+   |       |                          |
|  [ Queue / Topic ]   |------>|  |  Inbound  |-->| Message Translator |-->  |       |  [ Queue / Topic ]       |
|                      |  ack  |  |  Adapter  |   |     (optional)     |   |       |                          |
|                      |<------|  +---------+   +------------------+   |------>|                          |
|                      |       |        \                /             |  ack  |                          |
|                      |       |         \              /              |<------|                          |
|                      |       |          v            v               |       |                          |
|                      |       |     +---------------------+           |       |                          |
|                      |       |     | Bridge Coordinator    |          |       |                          |
|                      |       |     | retry / DLQ / state    |         |       |                          |
|                      |       |     +---------------------+           |       |                          |
|                      |       |               |                       |       |                          |
|                      |       |               v                       |       |                          |
|                      |       |     +---------------------+           |       |                          |
|                      |       |     |  Outbound Adapter      |         |       |                          |
|                      |       |     +---------------------+           |       |                          |
+----------------------+       +---------------------------------------+       +--------------------------+
```

## 7. Dynamics

The bridge behaves as a persistent, unidirectional (or, when built as two
mirrored halves, bidirectional) pump. The sequence for one message crossing
from source to destination is shown below.

```
Source Broker    Inbound Adapter    Translator     Outbound Adapter    Destination Broker
     |                  |                |                 |                    |
     |--message-------->|                |                 |                    |
     |                  |--raw payload-->|                 |                    |
     |                  |                |--mapped payload>|                    |
     |                  |                |                 |--publish---------->|
     |                  |                |                 |<--broker ack-------|
     |                  |<--publish ack--|                 |                    |
     |<--consumer ack---|                |                 |                    |
     |                  |                |                 |                    |
```

The order of the two acknowledgments at the end is the single most important
detail in the whole diagram. The bridge must not acknowledge receipt from the
source broker until it has confirmed the destination broker accepted the
publish. Acknowledging early and then failing to publish loses the message
silently. Acknowledging late but retrying the publish on failure gives
at-least-once delivery across the hop, at the cost of possible duplicates on
the destination side if the bridge crashes between a successful publish and
the source acknowledgment.

Failure-path dynamics, which occupy far more of real bridge code than the
happy path above, follow this shape.

```
State CONNECTED    ---publish fails, destination unreachable--->  State BACKING_OFF
State BACKING_OFF  ---retry succeeds within window--------------->  State CONNECTED
State BACKING_OFF  ---retry budget exhausted---------------------->  State DEAD_LETTERED (message)
State CONNECTED    ---source connection drops---------------------->  State RECONNECTING (does not ack)
State RECONNECTING ---source connection restored-------------------->  State CONNECTED (resumes from last unacked offset)
```

A well-built bridge never advances the message off the unacked-at-the-source
state until it has a durable confirmation from the destination, or until it
has explicitly routed the message to a dead-letter destination and only then
acknowledged the source. This is the same discipline the
[Dead Letter Channel](../07-integration/dead-letter-channel.md) pattern
formalizes for any consumer, applied specifically to the bridge's two-leg
transfer.

## 8. Implementation variants

**Native broker feature.** Several brokers ship a bridge as a first-class
configuration object rather than requiring custom code. RabbitMQ's Shovel
plugin is described in its own documentation as "a minimalistic message pump"
that moves messages "reliably and continually" from a source queue "in one
cluster to a destination (an exchange, topic, etc) in another cluster," and
explicitly "uses acknowledgements on both ends to cope with failures"
([RabbitMQ Shovel documentation](https://www.rabbitmq.com/docs/shovel),
verified 2026-08-02). Mosquitto, the MQTT broker, has bridge configuration
built directly into its config file grammar. A `connection` block names the
remote broker's `address`, and per-topic direction (in, out, or both) is
declared for each bridged topic pattern, with `start_type automatic`, `lazy`,
or `once` controlling reconnection behavior
([Mosquitto configuration manual page, bridge section](https://mosquitto.org/man/mosquitto-conf-5.html),
verified 2026-08-02). Both are examples of the pattern implemented entirely
as broker configuration, with no application code at all.

**Integration-framework component.** Frameworks built specifically for
message routing expose the bridge as a first-class endpoint type rather than
a broker feature. Spring Integration's `<int:bridge>` element connects two
`MessageChannel` instances or channel adapters, and its own reference lists
three purposes. It adapts a `PollableChannel` to a `SubscribableChannel` (or
the reverse) so subscribing endpoints do not need to know about polling. It
throttles message flow by inserting a poller with a bounded
`max-messages-per-poll` between the two channels. And it simply connects two
different systems where no format translation is needed
([Spring Integration Reference, Bridge](https://docs.spring.io/spring-integration/reference/bridge.html),
verified 2026-08-02). Apache Camel ships the equivalent idea as a route with
a `from()` endpoint on one component and a `to()` endpoint on another,
letting any two of Camel's roughly three hundred component endpoints (JMS,
Kafka, AMQP, file, HTTP) be bridged by declaring a single route.

**Hand-rolled dual-client process.** The most portable but highest-maintenance
variant is a small standalone service that opens a consumer connection to
system A using its native SDK and a producer connection to system B using its
native SDK, with a coordinator loop written by hand. This is common when
bridging a proprietary or legacy system that has no Camel component and no
broker-native bridge feature, for example an on-premises IBM MQ queue manager
feeding a cloud-native event bus. The trade is full control over
acknowledgment ordering and retry policy, at the cost of writing and testing
the failure-path state machine from scratch instead of relying on a
maintained framework.

**Serverless or managed-cloud bridge.** Cloud providers offer the same pattern
as a managed integration, where the bridge is a rule or a function binding
rather than a long-running process the team operates. AWS EventBridge's
cross-account and cross-Region event bus rules, and Azure Service Bus's
topic-to-Event-Grid integration, are both instances of the pattern where the
provider operates the coordinator and the consumer only declares the
mapping. The variant trades operational control for near-zero maintenance,
and is appropriate when both endpoints are already inside the same cloud
provider's ecosystem.

**Language-idiomatic notes.** In languages with strong async runtimes (Go,
Rust, Kotlin coroutines, Node.js), the bridge coordinator is naturally
expressed as two concurrent loops joined by a bounded channel that provides
backpressure between the consuming and producing side, rather than a class
hierarchy. In more object-oriented codebases (Java, C#), the coordinator is
commonly a small state machine class with explicit CONNECTED, BACKING_OFF,
and RECONNECTING states, matching the dynamics diagram in dimension 7
directly.

## 9. Known production uses

- **RabbitMQ Shovel.** A core RabbitMQ plugin that unidirectionally moves
  messages between a source queue and a destination exchange, within or
  across clusters, across different RabbitMQ versions, and across AMQP 0.9.1
  and AMQP 1.0 protocol versions, described in RabbitMQ's own documentation
  as designed specifically for the case where brokers "operate in different
  geographic or administrative domains" or "use different messaging
  products or protocols"
  ([RabbitMQ Shovel documentation](https://www.rabbitmq.com/docs/shovel),
  verified 2026-08-02).
- **Mosquitto MQTT broker bridging.** Mosquitto's `bridge_` configuration
  directives connect one Mosquitto instance to another (or to a third-party
  MQTT-compatible broker), forwarding a declared set of topics in one or
  both directions, with TLS and pre-shared-key authentication options for
  crossing an untrusted network boundary
  ([Mosquitto configuration manual page](https://mosquitto.org/man/mosquitto-conf-5.html),
  verified 2026-08-02). This is the standard mechanism IoT deployments use
  to relay a subset of edge-gateway telemetry topics up to a central cloud
  broker without exposing every edge device directly to the internet.
- **Spring Integration Bridge component.** Ships as a documented, first-class
  endpoint (`<int:bridge>` in XML configuration, `.bridge()` in the Java
  DSL) used across Spring-based enterprise applications to connect a
  `PollableChannel` to a `SubscribableChannel`, to throttle message flow
  with a bounded poller, or to connect two otherwise-unrelated channel
  adapters
  ([Spring Integration Reference, Bridge](https://docs.spring.io/spring-integration/reference/bridge.html),
  verified 2026-08-02).

## 10. Consequences

Positive.

- Neither side of the integration needs to know the other system's
  protocol, vendor, or network location. Both keep their existing client
  code and consumer semantics unchanged.
- The blast radius of a messaging-technology decision is contained. A team
  can adopt Kafka for new services while a legacy queue-based system keeps
  running, with the bridge as the single, auditable seam between them.
- Filtering and translation live in one place. Every consumer downstream of
  the bridge sees a consistent, already-translated message shape, instead
  of each consumer independently handling two formats.
- Operationally, a single bridge is easier to monitor and secure than N
  applications each independently authenticating to two separate messaging
  systems. Credentials for the far side of the bridge are held by one
  component, not scattered across every producer and consumer.

Negative.

- Added latency and an additional point of failure on every crossing
  message. If the bridge itself is down, all cross-system traffic stops
  even though both source and destination systems are individually
  healthy.
- Ordering guarantees are easy to lose silently across the hop unless the
  bridge is explicitly built to preserve per-key ordering, which usually
  costs some parallelism.
- A bridge that is meant to be temporary during a migration frequently
  becomes permanent, because removing it requires coordinated change on
  both sides and nobody owns that coordination once the original migration
  project has wound down. This is a judgement drawn from common
  integration-team experience rather than a cited source, and it is the
  practical reason many organizations end up with more standing bridges
  than they intended to build.
- Delivery-guarantee mismatch between the two systems can produce silent
  duplication or silent loss if the bridge's acknowledgment ordering (see
  dimension 7) is not implemented carefully, and that failure mode is not
  visible in normal operation, only under a crash or network partition.

## 11. Failure modes and misuse

**Symptom.** Messages vanish under a bridge restart, with no error logged.
**Cause.** The bridge acknowledges the source message immediately on dequeue,
before confirming the destination publish, so a crash between those two
steps loses the message with no trace. **Fix.** Reorder acknowledgment so
the source is only acknowledged after a durable publish confirmation from
the destination, matching the sequence in dimension 7, and add a metric that
counts unacknowledged in-flight messages so a stuck bridge is visible before
it drops anything.

**Symptom.** Duplicate messages appear on the destination side after any
bridge restart or network blip. **Cause.** The bridge publishes to the
destination, then crashes or loses connectivity before acknowledging the
source, so on restart it redelivers and republishes the same message.
**Fix.** Either accept at-least-once semantics and make the destination
consumer idempotent, using an idempotency key derived from the source
message ID and checked by the destination consumer, or, where the
destination supports it, use a deterministic message ID on republish so the
destination broker can deduplicate. This is the same trade-off the
[Dead Letter Channel](../07-integration/dead-letter-channel.md) and
[Point-to-Point Channel](../07-integration/point-to-point-channel.md)
entries in this catalog cover for a single consumer, applied here at the
seam between two systems.

**Symptom.** The bridge silently stops forwarding and nobody notices for
days. **Cause.** The bridge process is alive and its health check passes
because the health check only pings the process, not the actual
consumer-producer loop, but its consumer connection to the source silently
dropped and never reconnected. **Fix.** Health checks must assert on the
bridge's actual state machine (dimension 7), not merely process liveness,
and alerting must fire on a growing backlog on the source side, which is
the earliest external signal that a bridge has stalled.

**Symptom.** The destination system is flooded and its own consumers start
falling behind. **Cause.** The bridge was configured to forward an entire
exchange or an unfiltered topic wildcard, rather than a scoped subset, and
traffic on the source side grew without anyone revisiting the bridge
configuration. **Fix.** Scope every bridge to a named, reviewed list of
topics or routing keys, and treat adding a new bridged topic as a change
that needs the same review as adding a new consumer, since it changes the
load profile on the destination system.

**Symptom.** Two teams each build their own bridge between the same two
systems, doing slightly different filtering, and nobody can explain which
messages actually cross. **Cause.** No ownership was assigned to the
cross-system integration point, so each team solved their own narrow need
independently. **Fix.** Treat a Messaging Bridge as shared infrastructure
with a single owning team, the same governance discipline applied to a
shared database or a shared API gateway, not a thing any team can stand up
unilaterally.

**Misuse.** Using a bridge as a permanent substitute for choosing one
messaging technology, indefinitely, with no plan to retire it. This is not
a bug in the pattern. A long-lived bridge is a legitimate outcome when the
two systems genuinely need to stay separate. It becomes a misuse when the
bridge was originally scoped as a temporary migration aid and the migration
itself silently stalled, leaving the bridge as the de facto permanent
architecture without anyone consciously deciding that was acceptable.

## 12. Trade-off matrix

| Force | Messaging Bridge | Federation (broker-native) | Direct dual-client in every app | Single-broker migration |
|---|---|---|---|---|
| Coupling between systems | Low, neither side knows the other exists | Low, but ties both sides to the same broker technology | High, every app carries two client libraries and two credential sets | None, once migration completes |
| Operational surface added | One new component to run and monitor | Broker configuration only, no new process | None new, but multiplied across every app | Temporary, during migration only |
| Handles heterogeneous protocols | Yes, by design | No, requires same broker technology on both sides | Yes, but the cost lands on every application team | Not applicable, only one protocol remains |
| Delivery guarantee across the hop | Explicit, must be engineered (dimension 7) | Inherited from the single broker's own guarantee | Each app decides independently, inconsistently | Not applicable |
| Cost of removing it later | Moderate, one component to retire, one seam to audit | Low, configuration change | High, every app's dual-client code must be touched | Not applicable, already removed by definition |
| Fit for temporary migration aid | Good, if consciously time-boxed | Poor, not designed for cross-vendor cases | Poor, adds work exactly opposite of the migration goal | The actual end state, not an alternative to it |

## 13. Related and incompatible patterns

**Channel Adapter.** A Messaging Bridge is, structurally, a pair of Channel
Adapters (one inbound, one outbound) joined by a coordinator. Every bridge
implementation is built from two adapters. The bridge adds the coordination,
acknowledgment ordering, and failure handling on top.

**Message Translator.** When the two bridged systems disagree on message
format, headers, or addressing scheme, a Message Translator sits inside the
bridge between the inbound and outbound adapters, as shown in dimension 6.
A bridge with no translator is the degenerate, and very common, case where
both sides already agree on wire format and only the broker identity
differs.

**Point-to-Point Channel and Publish-Subscribe Channel.** The source and
destination sides of a bridge are each, independently, an instance of one of
these two channel patterns. A bridge does not change which channel type
either side uses. It only connects instances of those channel types that
live in different messaging systems.

**Dead Letter Channel.** A production-grade bridge routes messages it
cannot forward, after exhausting retries, to a Dead Letter Channel on the
source side rather than dropping them silently or blocking the entire
bridge indefinitely on one poisoned message.

**Content-Based Router.** Sometimes composed just before the bridge's
inbound adapter, when only a subset of a source channel's traffic should
cross to the destination. The router decides which messages reach the
bridge. The bridge does not itself perform routing decisions beyond the
topic or queue it was configured to consume.

Nothing in this catalog is structurally incompatible with a Messaging
Bridge, because the pattern is a composition point rather than a competing
strategy for the same problem. The closest thing to an incompatibility is
architectural rather than pattern-level. A Messaging Bridge and a shared
database integration approach are two different answers to the same
question of how two systems share state, and combining them for the same
data flow is redundant and a source of divergence between the two copies of
that data.

## 14. Refactoring path in and out

Introducing a bridge into an existing point-to-point integration follows
these steps.

1. Identify every application currently connecting directly to both
   messaging systems for the purpose of crossing traffic between them. This
   is usually discoverable by finding client code or configuration that
   holds credentials for both systems.
2. Name the exact set of queues, topics, or routing keys that need to
   cross, in each direction. Resist the temptation to bridge everything for
   now, since scope creep here is the direct cause of the flooding failure
   mode in dimension 11.
3. Stand up the bridge as a new, independently deployed component (or
   broker-native configuration, per dimension 8), consuming from the source
   and publishing to the destination for the named subset only, running
   alongside the existing direct connections rather than replacing them
   yet.
4. Verify the bridge produces the same effective traffic on the
   destination side that the direct connections were producing, using a
   shadow period where both paths run and are compared, or a checksum or
   count reconciliation over a fixed window.
5. Cut each direct-connecting application over to consume only from its own
   native system, relying on the bridge for the cross-system leg, one
   application at a time rather than all at once, so a regression is
   attributable to a single cutover.
6. Once every direct connection is retired, decommission the credentials
   and network access those applications held for the far-side system. The
   bridge is now the sole cross-system credential holder, which is the
   security benefit described in dimension 10.

Removing a bridge that has become unnecessary follows a mirrored path.

1. Confirm, with the reconciliation technique from step 4 above run in
   reverse, that traffic volume through the bridge has genuinely dropped to
   zero, or to a level the business has agreed no longer justifies the
   bridge, rather than assuming it from a stale mental model of who still
   depends on it.
2. Find every remaining downstream consumer of the destination-side
   messages the bridge produces, and confirm each either no longer needs
   that data or has been migrated to consume it natively from the true
   source.
3. Stop the bridge's inbound adapter first, leaving the outbound side idle,
   and watch for any alert or complaint over an agreed observation window
   before fully decommissioning. This catches a forgotten consumer more
   cheaply than a full teardown would.
4. Decommission the bridge component and its credentials, and update
   architecture documentation and the on-call runbook so the retired
   integration point is not rediscovered as a mystery months later.

## 15. Testing and verification

A bridge is easy to unit test on its translation logic in isolation. Feed a
representative source-format message into the Message Translator and assert
the destination-format output, with no live broker involved. That part of
the pattern is exactly as testable as any other pure function.

What is genuinely hard, and is where most of the value of testing a bridge
lives, is the failure-path state machine from dimension 7. The bridge's
correctness claim is entirely about what happens under partial failure, so
the test suite has to exercise partial failure directly rather than only the
happy path. The following approach follows from that.

- Use in-memory or embedded test brokers on both sides, an embedded
  ActiveMQ, a Testcontainers-managed RabbitMQ, or an in-process fake for a
  cloud queue SDK, so failure injection is controllable and fast, rather
  than relying on a shared staging environment where failure is
  unpredictable.
- Test the case where the destination publish fails after the source
  message has been dequeued but before it is acknowledged, and assert the
  message is not lost, that is, it is either retried or dead-lettered, but
  never silently dropped.
- Test the case where the bridge crashes (simulated as an abrupt process
  kill, not a graceful shutdown) between a successful destination publish
  and the source acknowledgment, and assert the resulting duplicate on
  redelivery is either acceptable under the documented at-least-once
  contract or is caught by the destination's own deduplication.
- Test reconnection behavior on both the source and destination side
  independently, since the two connections fail independently in
  production. A bridge that only handles simultaneous failure of both
  legs will surprise operators the first time only one side blinks.
- For a bridge with topic filtering, add a test that asserts messages
  outside the configured scope are never forwarded, catching the
  configuration drift described in the flooding failure mode.

Contract or consumer-driven tests are appropriate between the bridge and
each side's native message schema, so a schema change on either system is
caught before it silently breaks translation in production.

## 16. Observability signals

A healthy bridge, on a dashboard, shows a low and stable consumer lag on the
source side (messages are being drained roughly as fast as they arrive), a
near-zero count of messages currently in the unacknowledged, in-flight
state described in dimension 7, a near-zero and non-growing dead-letter
count, and a connection-state metric on both legs reading connected.

Signals worth logging and tracing explicitly include the following.

- Per-message trace correlation ID, propagated from the source message's
  headers through to the destination publish, so a message can be followed
  across the hop during incident investigation. Without this, diagnosing
  whether a message actually crossed the bridge requires manually
  correlating timestamps and payloads.
- Source-side consumer lag, or backlog depth, as the earliest indicator
  that the bridge has stalled, per the stall failure mode in dimension 11.
- Publish latency to the destination, distinguished from source consume
  latency, so operators can tell which leg of the bridge is slow.
- Reconnection events on each leg, counted and timestamped separately,
  because a bridge that is flapping its source connection but has a stable
  destination connection points at a different root cause than the
  reverse.
- Dead-letter rate and, critically, the reason each message was
  dead-lettered (translation failure versus destination rejection versus
  retry-budget exhaustion), since those three causes need different
  remediation.

A failing bridge, on the same dashboard, typically shows one of two
patterns. Either source lag climbs steadily while destination publish rate
is flat, which means the bridge has stalled or lost its destination
connection, or destination publish rate spikes while source lag is flat,
which means the bridge is in a retry-and-republish loop, usually from a
duplication bug, and is producing far more destination traffic than the
source is generating.

## 17. Security and privacy implications

A Messaging Bridge, by construction, is a component that holds valid
credentials for two separate systems, which makes it a concentrated target.
Compromising the bridge process compromises the ability to read from one
system and write to another, so it should be held to at least the same
credential-hygiene standard as a database connection pooler. Credentials
should be scoped only to the named channels being bridged, never
administrative access to either broker, and secrets should live in the same
managed-secret mechanism the rest of the estate uses rather than in bridge
configuration files.

When the bridge crosses a network or organizational boundary, as in the
Mosquitto bridge case where an edge gateway connects to a cloud broker over
an untrusted network, transport encryption and mutual authentication are not
optional. Mosquitto's own bridge configuration explicitly supports
certificate-based and pre-shared-key TLS for this reason
([Mosquitto configuration manual page](https://mosquitto.org/man/mosquitto-conf-5.html),
verified 2026-08-02). A bridge that forwards plaintext across an untrusted
network defeats whatever access controls exist on either individual broker.

Data-handling and privacy implications follow directly from what is being
forwarded. If the source system carries personal data and the destination
system operates under a different data-residency jurisdiction or a
different retention policy, the bridge is the point where that data
crosses a boundary the organization's data-governance policy may not
anticipate, because governance reviews frequently focus on the two systems
individually and miss the bridge connecting them. Any bridge carrying
regulated data should be an explicit, named entry in the organization's data
flow inventory, not an implicit side effect of an integration project.

Because the bridge is a natural point to apply policy, it is also a natural
point to apply message-level filtering for compliance, for example
stripping a field that must not leave a jurisdiction before the message
crosses. Where this filtering happens, it should be treated as
security-relevant code, reviewed and tested with the same rigor as an
authorization check, since a filtering bug at the bridge silently leaks
data that individual-system access controls were never designed to catch.

## 18. References

1. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
   Messaging Systems chapter, Messaging Bridge. Online summary at
   [enterpriseintegrationpatterns.com/patterns/messaging/MessagingBridge.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessagingBridge.html),
   verified 2026-08-02.
2. RabbitMQ documentation, "Shovel Plugin",
   [rabbitmq.com/docs/shovel](https://www.rabbitmq.com/docs/shovel),
   verified 2026-08-02.
3. Spring Integration Reference Documentation, "Bridge",
   [docs.spring.io/spring-integration/reference/bridge.html](https://docs.spring.io/spring-integration/reference/bridge.html),
   verified 2026-08-02.
4. Mosquitto project, `mosquitto.conf` manual page, bridge configuration
   section,
   [mosquitto.org/man/mosquitto-conf-5.html](https://mosquitto.org/man/mosquitto-conf-5.html),
   verified 2026-08-02.

## Code examples

Three languages are shown below. Each implements the same minimal bridge, a
`pumpOnce` (or `pump_once`, or `PumpOnce`) step that polls one message from a
fake source queue, translates it, retries a bounded number of times against
a fake destination queue, and either acknowledges the source on success or
routes to a dead-letter list on exhausted retries, matching the acknowledgment
ordering from dimension 7 (never acknowledge the source until the
destination publish is confirmed, or the message has been explicitly
dead-lettered). Java, Rust, and Swift are omitted here because a faithful
translation adds ceremony (interfaces, traits, or protocols) without showing
anything the three languages below do not already demonstrate; the pattern
does not have a genuinely idiomatic variant unique to those three that a
reader would learn from seeing repeated.

All three samples below were compiled or run directly and passed. TypeScript
was compiled with `tsc --strict` (TypeScript 7.0.2) and executed with Node.
Python was run directly with `python3`. Go was run with `go run`.

```typescript
type SourceMessage = { id: string; body: string; headers: Record<string, string> };
type DestMessage = { messageId: string; payload: string; attributes: Record<string, string> };

interface SourceQueue {
  poll(): SourceMessage | null;
  ack(id: string): void;
}

interface DestQueue {
  publish(msg: DestMessage): boolean;
}

function translate(src: SourceMessage): DestMessage {
  return { messageId: src.id, payload: src.body, attributes: src.headers };
}

type BridgeState = "CONNECTED" | "BACKING_OFF" | "DEAD_LETTERED";

class MessagingBridge {
  private state: BridgeState = "CONNECTED";
  private deadLetters: DestMessage[] = [];
  private forwarded = 0;

  constructor(private source: SourceQueue, private dest: DestQueue, private maxRetries: number) {}

  pumpOnce(): BridgeState {
    const msg = this.source.poll();
    if (!msg) return this.state;

    const translated = translate(msg);
    let attempt = 0;
    let published = false;

    while (attempt < this.maxRetries && !published) {
      published = this.dest.publish(translated);
      attempt += 1;
    }

    if (published) {
      this.source.ack(msg.id);
      this.forwarded += 1;
      this.state = "CONNECTED";
    } else {
      this.deadLetters.push(translated);
      this.source.ack(msg.id);
      this.state = "DEAD_LETTERED";
    }
    return this.state;
  }

  stats() {
    return { forwarded: this.forwarded, deadLettered: this.deadLetters.length };
  }
}
```

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SourceMessage:
    id: str
    body: str
    headers: dict


@dataclass
class DestMessage:
    message_id: str
    payload: str
    attributes: dict


def translate(msg: SourceMessage) -> DestMessage:
    return DestMessage(message_id=msg.id, payload=msg.body, attributes=dict(msg.headers))


@dataclass
class MessagingBridge:
    source: object
    dest: object
    max_retries: int
    forwarded: int = 0
    dead_letters: list = field(default_factory=list)
    state: str = "CONNECTED"

    def pump_once(self) -> str:
        msg = self.source.poll()
        if msg is None:
            return self.state

        translated = translate(msg)
        attempt = 0
        published = False
        while attempt < self.max_retries and not published:
            published = self.dest.publish(translated)
            attempt += 1

        if published:
            self.source.ack(msg.id)
            self.forwarded += 1
            self.state = "CONNECTED"
        else:
            self.dead_letters.append(translated)
            self.source.ack(msg.id)
            self.state = "DEAD_LETTERED"
        return self.state
```

```go
package main

type SourceMessage struct {
	ID      string
	Body    string
	Headers map[string]string
}

type DestMessage struct {
	MessageID  string
	Payload    string
	Attributes map[string]string
}

func translate(m SourceMessage) DestMessage {
	return DestMessage{MessageID: m.ID, Payload: m.Body, Attributes: m.Headers}
}

type SourceQueue interface {
	Poll() (SourceMessage, bool)
	Ack(id string)
}

type DestQueue interface {
	Publish(msg DestMessage) bool
}

type BridgeState string

const (
	StateConnected    BridgeState = "CONNECTED"
	StateDeadLettered BridgeState = "DEAD_LETTERED"
)

type MessagingBridge struct {
	Source      SourceQueue
	Dest        DestQueue
	MaxRetries  int
	Forwarded   int
	DeadLetters []DestMessage
	State       BridgeState
}

func (b *MessagingBridge) PumpOnce() BridgeState {
	msg, ok := b.Source.Poll()
	if !ok {
		return b.State
	}

	translated := translate(msg)
	published := false
	for attempt := 0; attempt < b.MaxRetries && !published; attempt++ {
		published = b.Dest.Publish(translated)
	}

	if published {
		b.Source.Ack(msg.ID)
		b.Forwarded++
		b.State = StateConnected
	} else {
		b.DeadLetters = append(b.DeadLetters, translated)
		b.Source.Ack(msg.ID)
		b.State = StateDeadLettered
	}
	return b.State
}
```
