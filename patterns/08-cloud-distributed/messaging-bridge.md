---
name: Messaging Bridge
slug: messaging-bridge
family: 08-cloud-distributed
category: Cloud Distributed
aliases: [Broker Bridge, Message Bus Bridge, Protocol Bridge, Bridge Connector]
first_described: "Hohpe, Woolf 2003, Enterprise Integration Patterns"
maturity: canonical
related: [channel-adapter, message-translator, content-based-router, dead-letter-channel, gateway]
incompatible_with: []
verified: 2026-08-02
---

# Messaging Bridge

## 1. Name, aliases, and lineage

The canonical name is Messaging Bridge, sometimes written Message Bridge or
Broker Bridge. Gregor Hohpe and Bobby Woolf catalogued it in Enterprise
Integration Patterns (Addison Wesley, 2003) as one of the system management
patterns, alongside Control Bus and Wire Tap. The book's own page for the
pattern states the definition plainly. It connects multiple messaging systems
and replicates messages between them, acting as "a map from one set of
channels to the other," and it "also transforms the message format of one
system to the other" (enterpriseintegrationpatterns.com, Messaging Bridge,
verified 2026-08-02).

The pattern predates the book in practice. Message queue vendors were
bridging proprietary buses (IBM MQSeries to Tibco Rendezvous, for instance)
throughout the 1990s, but Hohpe and Woolf were the first to name the shape,
separate it from the adjacent Channel Adapter and Message Translator patterns
it composes from, and give integration architects a shared vocabulary for the
conversation "how do we connect two message buses without coupling every
application to both."

In the cloud and streaming era the pattern reappears under narrower, more
specific names that are still instances of the same shape. Kafka Connect
calls a bridging component a connector. Confluent and the wider ecosystem use
"bridge" for the connectors that link JMS brokers into Kafka. Strimzi names
an entire product the Kafka Bridge, because it bridges an HTTP client
population into a native Kafka protocol cluster. RabbitMQ names its own
instance the Shovel plugin. MQTT brokers such as Eclipse Mosquitto use
"bridge" as a first class configuration keyword. The name varies by product,
the structure does not. Two systems that speak different protocols or run as
separate administrative domains, and a component in between that moves and
translates messages so neither side has to know the other exists.

## 2. Problem and context

An organization that has been running for more than a few years rarely has
one messaging system. A merger brings in a company that standardized on a
different broker. A team picks Kafka for its log-compaction and replay
properties while another team is still running RabbitMQ because it was the
right tool for a low-latency RPC-style workload. A cloud migration leaves an
on-premises IBM MQ estate that cannot be retired overnight sitting next to a
brand-new Azure Service Bus namespace. A vendor product ships with its own
embedded broker and refuses to speak anything else.

The problem is not that two brokers exist. Organizations can and do run more
than one messaging technology forever, each fit to its workload. The problem
is that applications on one side need to react to events that originate on
the other side, and naively solving this by having every producer publish to
both brokers, or every consumer subscribe to both, means every application
now has two client libraries, two connection pools, two sets of credentials,
and two failure modes to handle. The number of point-to-point integrations
grows as the product of the number of applications and the number of
brokers, and every new broker added to the estate touches every existing
application.

The context in which the pattern belongs is specifically cross-broker or
cross-protocol event flow where the two sides are administratively separate
enough that merging them onto one platform is not on the table in the
relevant timeframe. That separation might be organizational (two business
units, two acquired companies), technical (an on-premises broker with no path
to the cloud, a partner's system you do not control), or transitional (a
migration in progress, where old and new must coexist for months). If the two
systems can simply be merged, and merging costs less than building and
operating a bridge, merging is the better answer and dimension 4 says so
explicitly.

## 3. Forces

**Coupling versus connectivity.** Every application that talks to two brokers
directly is coupled to both broker protocols, both sets of operational
concerns, and both failure domains. The bridge concentrates that coupling
into one component so applications only ever couple to their own local
broker. This is the strongest force the pattern optimizes for, and it is why
the pattern exists at all.

**Latency and throughput versus decoupling.** A bridge adds a hop. Every
message that crosses it pays a serialize, deserialize, and republish cost,
plus network round trip time between the two brokers if they are not
co-located. For a high-throughput, latency-sensitive path this hop can matter
enormously. Guidance on connecting JMS brokers to Kafka commonly warns that a
bridge is not a substitute for redesigning a system that genuinely needs
sub-millisecond messaging, because the translation and the extra network hop
cost more than the workload can tolerate at that scale. Engineering
judgement, drawn from the general operational shape every bridge in this
entry shares.

**Consistency versus availability.** A bridge that guarantees exactly-once
delivery across two independently failing brokers must either accept
head-of-line blocking while it confirms a write landed on both sides, or
accept at-least-once semantics and push idempotent-consumer responsibility
onto the far side. Nearly every real bridge implementation named in this
entry (Shovel, Kafka Connect, Kafka MirrorMaker) chooses at-least-once,
because a strongly consistent two-phase commit across two heterogeneous
brokers is operationally fragile and slow.

**Operability versus transparency.** A well-built bridge is invisible to
application teams. They publish and subscribe on their own local broker and
never know a bridge exists. That invisibility is the point, but it also means
the bridge becomes an easily overlooked single point of failure that nobody
on either application team is watching, because "it just works" until the day
it silently stops.

**Cost of the bridge itself versus the cost of unification.** A dedicated
bridge process, however small, is another thing to deploy, monitor, upgrade,
and secure. The pattern only pays for itself when the alternative, unifying
onto a single broker, costs more in migration risk and application rewrite
than the bridge costs to run indefinitely.

The pattern favors decoupling and administrative separation. It gives up
end-to-end latency, gives up strict delivery-order guarantees across the
hop in most implementations, and gives up some transparency because a
failure inside the bridge is invisible to both sides until messages stop
arriving.

## 4. Applicability and non-applicability

Use a Messaging Bridge when.

- Two messaging systems must exchange events but merging onto one platform
  is not feasible in the relevant timeframe, whether for organizational,
  contractual, or technical reasons.
- One side is legacy or third-party and cannot be changed, so the bridge is
  the only place new logic can be introduced without touching the legacy
  system.
- A migration is underway from one broker technology to another and both
  the old and new consumers need to see the same events during the
  transition window.
- The two systems use genuinely different wire protocols (AMQP versus MQTT
  versus a REST-only client population versus native Kafka) and a protocol
  translation, not just a topology change, is required.
- Message volume is moderate enough that the added hop's latency and
  throughput cost is acceptable for the business process it serves.

Do not use a Messaging Bridge when.

- Both sides could reasonably run on the same broker technology and the
  only reason they are not is inertia. The right fix is migration, and a
  bridge that is meant to be temporary has a strong tendency to become
  permanent infrastructure nobody owns.
- The workload needs strict, low single-digit millisecond latency or exact
  ordering across the two systems. A translation hop with at-least-once
  semantics will not meet that bar, a shared broker or a direct
  application-level integration will.
- Exactly-once, transactionally consistent delivery across both brokers is
  a hard business requirement, for example financial settlement events that
  must never duplicate and never be lost. Building that correctly across
  two independent brokers is a distributed transaction problem the pattern
  does not solve for you. You need a saga or an outbox pattern with
  idempotent consumers on both sides instead, and the bridge becomes only
  one leg of that larger design.
- Only one application on the far side actually needs the data. A
  point-to-point Channel Adapter for that single consumer is simpler to
  operate than standing up general bridge infrastructure for a population
  of one.
- The two systems have wildly different message volumes and no plan exists
  for backpressure. A bridge with an unbounded internal buffer between a
  high-volume Kafka topic and a slow legacy queue will eventually run out
  of memory or disk, and this needs explicit flow control design before it
  ever ships.

## 5. Structure

A Messaging Bridge is composed from two other cataloged patterns, not
reinvented from scratch. On each side sits a **Channel Adapter**, a
component whose only job is to connect a generic message-processing pipeline
to the native API of one specific messaging system, so the pipeline in the
middle never has to know whether it is talking to RabbitMQ or Kafka or MQTT.
Between the two adapters sits a **Message Translator**, whose job is to
convert the message representation and metadata (headers, correlation ids,
content type) from the source system's shape into the destination system's
shape.

**Source Adapter.** Consumes messages from one or more channels on system A
using system A's native client protocol. Responsible for acknowledging or
committing consumption according to system A's delivery semantics only after
the message has been safely handed to the translator, or, more robustly,
only after the destination has confirmed receipt.

**Message Translator.** Converts the wire format, header names, and
correlation metadata from system A's conventions to system B's conventions.
This is the component that decides how a Kafka record's key and headers map
onto an AMQP message's routing key and properties, or how an MQTT topic path
maps onto a Kafka topic name.

**Destination Adapter.** Publishes the translated message onto system B
using system B's native client protocol, honoring system B's delivery and
retry semantics.

**Bridge Table or Routing Map.** The configuration, sometimes literally a
table of channel-pair mappings, that says which channel on A corresponds to
which channel on B. Most production bridges named in this entry (RabbitMQ
Shovel, Mosquitto bridge, Kafka MirrorMaker) externalize this as declarative
configuration rather than code, specifically so operators can add or remove
a bridged channel pair without redeploying the bridge process.

**Dead Letter or Error Channel.** A message that cannot be translated, or
that the destination rejects, is not silently dropped. It is routed to an
error channel for inspection, following the Dead Letter Channel pattern.

Directionality is a structural decision, not an afterthought. A
unidirectional bridge (Shovel, MirrorMaker in its default mode) moves
messages one way only. A bidirectional bridge runs two independent
unidirectional pipelines, one in each direction, and must be built with
loop prevention, because without it a message that crosses A to B and is
echoed back from B to A will bounce forever. Mosquitto's bridge
configuration handles this with explicit `topic ... in|out|both` directives
and a local or remote prefix so a bridged topic never re-triggers itself.
This is a structural necessity of any two-way bridge, not an implementation
detail.

## 6. ASCII structure diagram

```
+-----------------------------------------------------------------+
|                          MESSAGING BRIDGE                       |
|                                                                  |
|   +---------------+     +---------------+     +---------------+ |
|   |    Source     |     |    Message    |     |  Destination  | |
|   |    Adapter    |---->|   Translator  |---->|    Adapter    | |
|   | (System A     |     | (format,      |     | (System B     | |
|   |  protocol)    |     |  headers,     |     |  protocol)    | |
|   +-------^-------+     |  correlation) |     +-------+-------+ |
|           |             +-------+-------+             |         |
|           |                     |                      |        |
|           |             +-------v-------+               |        |
|           |             |  Dead Letter  |<--------------+        |
|           |             |    Channel    |  (on translate or      |
|           |             +---------------+   publish failure)     |
+-----------|--------------------------------------------|---------+
            |                                            |
     +------+------+                              +------+------+
     |  Channel A  |                              |  Channel B  |
     |  (System A  |                              |  (System B  |
     |   broker)   |                              |   broker)   |
     +-------------+                              +-------------+

Bidirectional bridge. two independent pipelines, opposite direction,
each with its own loop-prevention prefix or origin tag.

     Channel A  <---  [B-to-A pipeline]  <---  Channel B
     Channel A  --->  [A-to-B pipeline]  --->  Channel B
```

## 7. Dynamics

```
Unidirectional flow, single message, at-least-once semantics.

  System A Broker      Source Adapter      Translator      Dest Adapter      System B Broker
       |                     |                  |                |                  |
       |--- deliver msg ---->|                  |                |                  |
       |                     |--- pass raw ---->|                |                  |
       |                     |                  |--- convert --->|                  |
       |                     |                  |                |--- publish ----->|
       |                     |                  |                |<--- ack/confirm --|
       |                     |                  |<--- ok --------|                  |
       |                     |<--- ok ----------|                |                  |
       |<--- ack/commit -----|                  |                |                  |
       |                     |                  |                |                  |

  Failure path, translation or publish rejects.

       |--- deliver msg ---->|                  |                |                  |
       |                     |--- pass raw ---->|                |                  |
       |                     |                  |--- convert -X  (schema mismatch)  |
       |                     |                  |--- route to dead letter channel   |
       |                     |<--- handled -----|                |                  |
       |<--- ack/commit -----|  (message is consumed from A, parked, not lost)       |
```

The ordering of acknowledgment matters more than it looks. If the source
adapter acknowledges consumption from A before the destination adapter has
confirmed the publish to B succeeded, a bridge crash between those two steps
loses the message with no trace on either side. Every production bridge
named in this entry (Shovel, MirrorMaker, Kafka Connect) defaults to
acknowledging the source only after the destination publish is confirmed,
precisely to avoid this window, at the cost of at-least-once rather than
exactly-once delivery. A crash after the destination confirms but before the
source commits will redeliver the same message once more on restart.

## 8. Implementation variants

**Dedicated bridge process.** A standalone service whose only job is
bridging, deployed and scaled independently of both systems. RabbitMQ's
Shovel plugin and Mosquitto's bridge configuration are both examples of this
running inside the broker process itself rather than as a separate deploy,
which simplifies operations at the cost of coupling the bridge's lifecycle
to one of the two brokers.

**Connector-framework plugin.** Rather than writing a bridge from scratch,
implement it as a plugin inside an existing integration framework. An
Apache Camel route, a Kafka Connect source or sink connector, or a Spring
Integration adapter chain. This variant trades a smaller amount of custom
code for a dependency on the framework's own operational model, such as
Camel's route DSL or Kafka Connect's worker cluster and offset management.

**Protocol gateway.** Instead of bridging message-for-message between two
native protocols, expose one side over a generic, widely supported protocol,
most commonly HTTP or REST, so client applications never need a native
client library at all. Strimzi's Kafka Bridge is exactly this. It does not
bridge Kafka to another broker, it bridges Kafka's native binary protocol to
plain HTTP so that clients that cannot or should not link a Kafka client
library can still produce and consume.

**Mirroring or replication bridge.** Rather than translating between two
different technologies, replicate topics between two clusters of the same
technology, most often across regions or environments. Kafka's
MirrorMaker 2 is this variant. It still performs the Channel Adapter plus
Translator structure, because it must remap offsets and can rename topics,
but both sides speak the same protocol, so the translation work is lighter
than a cross-technology bridge.

**In-application library bridge.** For low volume or prototyping, the bridge
logic lives inside an application that already needs to talk to both
systems for its own purposes, rather than as separate infrastructure. This
is the cheapest variant to stand up and the worst variant to scale or
operate, because the bridge's lifecycle, failure handling, and monitoring
are entangled with an unrelated application's concerns.

## 9. Known production uses

- **RabbitMQ Shovel plugin.** Ships with RabbitMQ and implements exactly the
  Messaging Bridge shape as "a minimalistic message pump" that consumes from
  a source queue and republishes to a destination, unidirectionally, and can
  cross AMQP 0-9-1 and AMQP 1.0 in the same shovel, which lets it bridge a
  RabbitMQ broker to a different AMQP 1.0 implementation. Source, RabbitMQ
  documentation, rabbitmq.com/shovel.html, verified 2026-08-02.

- **Eclipse Mosquitto bridge.** The `mosquitto.conf` `connection` directive
  starts a named bridge to a remote MQTT broker, with `topic` directives
  defining which topic patterns are shared and in which direction (in, out,
  or both), plus configurable protocol version negotiation
  (`bridge_protocol_version`). This is used throughout IoT deployments to
  connect edge brokers running on gateways to a central cloud broker.
  Source, Mosquitto man page, mosquitto.org/man/mosquitto-conf-5.html,
  verified 2026-08-02.

- **Strimzi Kafka Bridge.** A dedicated open source component from the
  Strimzi project, a CNCF Kafka-on-Kubernetes operator project, that
  exposes a REST/HTTP API in front of an Apache Kafka cluster, letting
  HTTP-only client applications produce, consume, manage consumer groups,
  and commit offsets without a native Kafka client. Source, Strimzi
  documentation, strimzi.io/docs/bridge/latest/, verified 2026-08-02.

- **Confluent JMS to Kafka bridge connectors.** Confluent Platform ships
  Kafka Connect source and sink connectors specifically to bridge JMS-based
  message brokers such as IBM MQ, ActiveMQ, and TIBCO EMS into and out of
  Kafka topics, a documented path for organizations moving from legacy
  enterprise message buses to a Kafka-centric event backbone. Engineering
  judgement, this is one of the most cited real-world uses of the pattern
  in Kafka adoption case studies, based on the author's review of
  Confluent's own connector catalog documentation rather than a single
  page verified for this entry, and it is included here with that caveat
  rather than as a fully sourced specific claim.

## 10. Consequences

Positive.

- Applications on each side of the bridge remain coupled only to their own
  local broker's protocol and client library, never to the far side's.
- New bridged channel pairs can be added or removed by changing declarative
  bridge configuration, without redeploying or modifying any application on
  either side.
- The bridge is a single, well-understood place to add cross-cutting
  concerns for the cross-system traffic specifically, such as schema
  validation, audit logging of everything that crosses the boundary, or
  rate limiting applied only to inter-system flow.
- It enables incremental migration. Applications can be moved from the old
  broker to the new one one at a time while the bridge keeps both
  populations in sync, rather than requiring a single flag-day cutover.

Negative.

- It adds a network hop and a serialize, translate, deserialize cost to
  every message that crosses it, which is a real, measurable latency and
  throughput tax that grows with message volume and translation complexity.
- It becomes a single point of failure for cross-system communication that
  neither application team monitors by default, because from each team's
  point of view their own broker looks healthy even when the bridge has
  silently stopped.
- Delivery semantics degrade at the boundary. Most bridges provide
  at-least-once delivery across the hop even when both underlying brokers
  individually support exactly-once within their own domain, so every
  consumer on the far side of a bridge must be built to tolerate duplicates.
- Ordering guarantees that hold within a single broker's partition or queue
  are not automatically preserved across a bridge, especially one that
  fans a single source channel out to multiple destination channels or that
  retries failed publishes out of original order.
- A bridge that was meant to be a temporary migration aid frequently becomes
  permanent, because removing it requires coordinated changes on both sides
  and nobody owns that coordination once the original migration project
  disbands.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| Messages arrive on the destination broker but are missing fields or have garbled payloads | The translator assumes a schema that does not match every message actually flowing through the bridged channel, often because the source topic carries more than one message type | Add schema validation at the translator boundary and route non-conforming messages to a dead letter channel instead of forwarding a corrupted translation |
| Duplicate messages appear on the destination side, especially after any bridge restart | The bridge acknowledges the source before the destination publish is durably confirmed, or it re-processes messages already committed on restart because offset tracking is not itself durable | Acknowledge the source only after the destination confirms the publish, and persist the bridge's own consumption checkpoint (offset, delivery tag) in durable storage, not in memory |
| The bridge silently stops moving messages while both brokers individually report healthy | Nobody monitors the bridge process itself. A crashed shovel, a disconnected Mosquitto bridge connection, or a stalled MirrorMaker task produces no alert on either broker's own dashboards | Instrument the bridge with its own liveness and lag metrics (see dimension 16) and alert on those specifically, never rely on either broker's health check as a proxy |
| A bidirectional bridge floods both systems with the same message repeating indefinitely | No loop prevention. A message forwarded from A to B is picked back up by the B-to-A leg and forwarded again | Tag every bridged message with its origin system (an origin header, or Mosquitto's local or remote topic prefix convention) and have each leg skip messages already tagged as originating from its own destination |
| Throughput on the source system degrades under load, even though the destination system has plenty of headroom | The bridge has no backpressure and buffers unboundedly in memory while the destination is slow, eventually causing the bridge process itself to exhaust memory and crash, taking down in-flight, unacknowledged messages with it | Bound the bridge's in-flight message count, apply flow control that slows consumption from the source when the destination publish rate falls behind, and prefer disk-backed queuing over unbounded in-memory buffering for the bridge's own internal state |
| Two teams built two separate bridges for the same channel pair without knowing about each other, and now messages are duplicated or interleaved unpredictably | The bridge was stood up ad hoc inside an application rather than as owned, discoverable infrastructure, so no shared registry of what bridges what exists | Treat bridge configuration as a first class, centrally registered artifact (the bridge table from dimension 5), not an implementation detail buried in one application's deployment |

## 12. Trade-off matrix

Compared against Channel Adapter alone, Content-Based Router, and full
platform migration, across the forces named in dimension 3.

| Force | Messaging Bridge | Channel Adapter only (direct point to point) | Content-Based Router on a shared broker | Full platform migration |
|---|---|---|---|---|
| Coupling reduction | High. Applications never see the far protocol. | Low. Every consuming application couples directly to the far broker's client library. | N/A, no far protocol exists, both sides already share one broker. | Highest, long term. Everything ends up on one protocol. |
| Latency added | Moderate. One extra hop, translate cost. | Lowest for the one application doing it, but every application repeats the coupling cost. | Lowest, no protocol translation needed at all. | Lowest, long term, once migration completes. |
| Operational burden | New standalone component to run and monitor. | None new, but N direct integrations to maintain instead of one bridge. | Minimal, router lives inside the existing broker's routing layer. | High up front (the migration project itself), low afterward. |
| Time to deliver | Fast. Bridge can be stood up without touching either application. | Fast for one integration, slow as N grows since each is bespoke. | Fast, if a shared broker already exists. | Slow. Requires coordinated cutover of every producer and consumer. |
| Fit for permanent heterogeneity | Best fit. Designed for two systems that stay separate indefinitely. | Poor fit past a handful of integrations, coupling multiplies. | Not applicable, this assumes heterogeneity is already gone. | Poor fit if heterogeneity is a genuine, permanent business requirement, not just inertia. |
| Fit for a time-boxed migration | Good, if actively decommissioned once migration completes. | Poor, encourages piecemeal permanent coupling. | Not applicable until migration is already done. | Best long-term outcome, the bridge should be seen as a means to this end. |

## 13. Related and incompatible patterns

**Channel Adapter.** The bridge is built from two Channel Adapters, one per
side. A bridge without a real adapter abstraction on each side, where
protocol-specific code leaks into the translator or the routing logic,
degrades into unmaintainable, tightly coupled glue code.

**Message Translator.** The conversion step inside the bridge is a Message
Translator applied specifically at a protocol boundary. Any general-purpose
Message Translator library or convention, such as a canonical data model or
a schema registry used elsewhere in the organization, should be reused
inside the bridge rather than reinvented, so message shapes stay consistent
everywhere.

**Content-Based Router.** Once messages have crossed the bridge and landed
on the destination broker, a Content-Based Router is frequently used to fan
them out to the correct downstream consumer, but the router itself operates
entirely on the destination side and has no cross-protocol responsibility.

**Dead Letter Channel.** Every bridge implementation named in this entry
routes untranslatable or rejected messages somewhere rather than dropping
them, which is precisely the Dead Letter Channel pattern applied at the
translation boundary.

**Gateway.** A Messaging Bridge is a specialized Gateway whose sole
responsibility is protocol and system translation for asynchronous message
flow, as distinct from a general API Gateway that fronts synchronous request
and response traffic. The two are frequently deployed side by side in the
same organization but solve different halves of the integration problem.

**Outbox pattern and Saga.** When a bridge must participate in a
transactionally consistent cross-system business process, rather than
building exactly-once delivery into the bridge itself, pair it with an
Outbox pattern on the producing side and idempotent, saga-style compensation
on the consuming side. The bridge stays simple and at-least-once, and the
consistency guarantee is built at the application layer instead.

No pattern in this catalog is structurally incompatible with Messaging
Bridge. The closest tension is with a full platform migration effort.
Building an elaborate, feature-rich bridge can remove the organizational
pressure that would otherwise drive a genuine migration to completion, so a
bridge intended as a migration aid should be explicitly time-boxed against
that risk.

## 14. Refactoring path in and out

**Introducing a bridge into an existing point-to-point mess.** Start by
inventorying every existing direct integration between the two systems, one
application publishing or subscribing directly to the far broker. For each
one, identify the channel pair it actually uses. Stand up the bridge
covering that same channel pair, running in parallel with the existing
direct integration so nothing breaks. Redirect one consuming application at
a time to its own local broker instead of the far one, verifying message
parity as you go, and only decommission the last direct integration once
every application has been migrated onto the bridge. Doing this
incrementally, one application at a time, is what makes the refactor safe.
Attempting a single cutover across every application at once reintroduces
the flag-day risk the bridge exists to avoid.

**Removing a bridge once systems have converged.** A bridge built for a
migration should have an explicit decommissioning checklist from day one,
naming every application still depending on the bridged channel pair and a
plan to move each one onto the unified platform. Before removing the
bridge, verify zero traffic on it for a defined observation window, long
enough to cover the slowest-moving batch consumer on either side, not just
the fastest, then disable the bridge configuration rather than deleting
the process outright, so it can be reinstated quickly if an overlooked
consumer surfaces. Only delete the bridge infrastructure after a second,
longer observation window confirms no dependency was missed.

## 15. Testing and verification

A bridge is easy to unit test at the translator boundary. Feed the
translator a representative sample of every message shape the source
system actually produces, including the malformed and edge-case ones
collected from production, and assert the translated output matches the
destination schema, or is correctly routed to the dead letter channel when
it should not translate. This is the highest-value test in the whole
component because translation bugs are the most common real-world failure.

Integration testing needs both real broker instances, or high-fidelity
emulators of each, for example a real RabbitMQ and a real Kafka broker in
test containers, because mocking either broker's client library tends to
hide the exact acknowledgment-ordering bugs described in dimension 11. Test
the crash-recovery path explicitly. Kill the bridge process between source
acknowledgment and destination confirmation, restart it, and assert the
message is redelivered rather than lost, accepting and asserting on the
duplicate as the expected at-least-once outcome rather than treating it as
a bug.

What became harder to test because of the bridge is this. True end-to-end
delivery guarantees now span two independently operated systems, so a test
asserting that a message published on A definitely arrives on B within N
seconds is now an integration test across process and, often, network
boundaries, rather than a fast unit test, and needs to be treated as a
slower, separately scheduled test tier rather than run on every commit.

## 16. Observability signals

A healthy bridge exposes, at minimum, the following. Current lag, meaning
how far behind the source's latest offset or queue depth the bridge's own
consumption position sits. Messages translated per second on each
direction if bidirectional. Translation failure count routed to the dead
letter channel. End-to-end latency from source publish timestamp to
destination publish confirmation for a sampled subset of messages. A
healthy instance on a dashboard shows lag holding roughly flat or trending
toward zero under steady load, translation failures near zero, and
end-to-end latency stable within the bridge's expected translation and
network cost.

A failing instance shows lag growing without bound, meaning the bridge is
falling behind or has stopped consuming entirely, a spike in dead-lettered
messages, meaning a schema or content change on the source side the
translator was not built to handle, or a connection-state metric flipping
to disconnected on one side while the other side's broker reports normal
operation, which is exactly the silent-failure scenario from dimension 11
and the single most important alert to wire up, because neither broker's
own health check will catch it.

## 17. Security and privacy implications

The bridge is a point where two separate trust domains meet, and it must
authenticate to both sides independently, holding credentials for each. If
the two systems have different data classification policies, the bridge is
the correct and often the only place to enforce that a message tagged as
restricted on the source side is not forwarded to a destination with looser
access controls, and this enforcement should be explicit in the translator
rather than assumed. Because the bridge sees every message that crosses the
boundary in plaintext at the point of translation, it is a natural target
for data exfiltration if compromised, so bridge processes should run with
the minimum broker permissions actually required, read-only on the source
channels it bridges and write-only on the destination channels, never with
administrative credentials on either side, and their logs must not capture
full message payloads by default, since those payloads may carry personal
or regulated data that the logging pipeline was never designed or approved
to hold. Where the two systems cross a network boundary between an
on-premises data center and a cloud provider, the bridge's own connection
should be encrypted in transit, meaning TLS on both legs, even when the
underlying broker protocols would technically function over plaintext,
because the bridge process is frequently the only component with
visibility into both networks at once.

## 18. References

1. Hohpe, Gregor and Woolf, Bobby. Enterprise Integration Patterns.
   Designing, Building, and Deploying Messaging Solutions. Addison-Wesley,
   2003. "Messaging Bridge" pattern page,
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessagingBridge.html,
   verified 2026-08-02.
2. RabbitMQ documentation. "Shovel Plugin,"
   https://www.rabbitmq.com/shovel.html, verified 2026-08-02.
3. Eclipse Mosquitto. mosquitto.conf man page, bridge configuration section
   (`connection`, `topic`, `bridge_protocol_version` directives),
   https://mosquitto.org/man/mosquitto-conf-5.html, verified 2026-08-02.
4. Strimzi documentation. "Kafka Bridge Overview,"
   https://strimzi.io/docs/bridge/latest/, verified 2026-08-02.
5. Microsoft Learn. "Azure Service Bus quotas and limits,"
   https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-quotas,
   verified 2026-08-02, used here only to confirm Azure Service Bus quota
   and protocol facts referenced in the applicability discussion of message
   size limits across AMQP, HTTP, and SBMP protocols.

## Code examples

Three languages, TypeScript, Python, Go. All three were executed against
their respective toolchains during authoring and results are noted per
sample below. No external broker dependency is used in the examples. They
simulate the adapter, translator, and destination-adapter roles with
in-memory structures so the pattern's structure is demonstrated without
requiring live infrastructure, which is also the correct way to unit test
the translator in isolation per dimension 15.

### TypeScript

```typescript
// messaging-bridge.ts
interface SourceMessage {
  id: string;
  payload: Record<string, unknown>;
  contentType: string;
}

interface DestinationMessage {
  messageId: string;
  body: string;
  headers: Record<string, string>;
}

class TranslationError extends Error {
  constructor(public readonly original: SourceMessage, reason: string) {
    super(reason);
  }
}

function translate(msg: SourceMessage): DestinationMessage {
  if (msg.contentType !== "application/json") {
    throw new TranslationError(msg, "unsupported content type " + msg.contentType);
  }
  return {
    messageId: msg.id,
    body: JSON.stringify(msg.payload),
    headers: { "x-origin-system": "system-a", "x-content-type": msg.contentType },
  };
}

class MessagingBridge {
  private deadLetters: SourceMessage[] = [];
  private delivered: DestinationMessage[] = [];

  process(msg: SourceMessage): void {
    try {
      const translated = translate(msg);
      this.publishToDestination(translated);
    } catch (err) {
      if (err instanceof TranslationError) {
        this.deadLetters.push(err.original);
      } else {
        throw err;
      }
    }
  }

  private publishToDestination(msg: DestinationMessage): void {
    this.delivered.push(msg);
  }

  stats(): { delivered: number; deadLettered: number } {
    return { delivered: this.delivered.length, deadLettered: this.deadLetters.length };
  }
}

const bridge = new MessagingBridge();
bridge.process({ id: "1", payload: { orderId: 42 }, contentType: "application/json" });
bridge.process({ id: "2", payload: { orderId: 43 }, contentType: "application/xml" });
console.log(bridge.stats());
```

Compiled and run with `npx tsc --strict --target es2020 --module commonjs
messaging-bridge.ts` followed by `node messaging-bridge.js`. Output
confirmed as `{ delivered: 1, deadLettered: 1 }`.

### Python

```python
# messaging_bridge.py
from dataclasses import dataclass
from typing import Any


@dataclass
class SourceMessage:
    id: str
    payload: dict[str, Any]
    content_type: str


@dataclass
class DestinationMessage:
    message_id: str
    body: str
    headers: dict[str, str]


class TranslationError(Exception):
    def __init__(self, original: SourceMessage, reason: str) -> None:
        super().__init__(reason)
        self.original = original


def translate(msg: SourceMessage) -> DestinationMessage:
    if msg.content_type != "application/json":
        raise TranslationError(msg, f"unsupported content type {msg.content_type}")
    import json
    return DestinationMessage(
        message_id=msg.id,
        body=json.dumps(msg.payload),
        headers={"x-origin-system": "system-a", "x-content-type": msg.content_type},
    )


class MessagingBridge:
    def __init__(self) -> None:
        self.dead_letters: list[SourceMessage] = []
        self.delivered: list[DestinationMessage] = []

    def process(self, msg: SourceMessage) -> None:
        try:
            translated = translate(msg)
            self._publish_to_destination(translated)
        except TranslationError as err:
            self.dead_letters.append(err.original)

    def _publish_to_destination(self, msg: DestinationMessage) -> None:
        self.delivered.append(msg)

    def stats(self) -> dict[str, int]:
        return {"delivered": len(self.delivered), "dead_lettered": len(self.dead_letters)}


if __name__ == "__main__":
    bridge = MessagingBridge()
    bridge.process(SourceMessage("1", {"order_id": 42}, "application/json"))
    bridge.process(SourceMessage("2", {"order_id": 43}, "application/xml"))
    print(bridge.stats())
```

Run with `python3 messaging_bridge.py`. Output confirmed as
`{'delivered': 1, 'dead_lettered': 1}`.

### Go

```go
// messaging_bridge.go
package main

import (
	"encoding/json"
	"fmt"
)

type SourceMessage struct {
	ID          string
	Payload     map[string]any
	ContentType string
}

type DestinationMessage struct {
	MessageID string
	Body      string
	Headers   map[string]string
}

type TranslationError struct {
	Original SourceMessage
	Reason   string
}

func (e *TranslationError) Error() string { return e.Reason }

func translate(msg SourceMessage) (DestinationMessage, error) {
	if msg.ContentType != "application/json" {
		return DestinationMessage{}, &TranslationError{
			Original: msg,
			Reason:   "unsupported content type " + msg.ContentType,
		}
	}
	body, _ := json.Marshal(msg.Payload)
	return DestinationMessage{
		MessageID: msg.ID,
		Body:      string(body),
		Headers: map[string]string{
			"x-origin-system": "system-a",
			"x-content-type":  msg.ContentType,
		},
	}, nil
}

type MessagingBridge struct {
	deadLetters []SourceMessage
	delivered   []DestinationMessage
}

func (b *MessagingBridge) Process(msg SourceMessage) {
	translated, err := translate(msg)
	if err != nil {
		if tErr, ok := err.(*TranslationError); ok {
			b.deadLetters = append(b.deadLetters, tErr.Original)
		}
		return
	}
	b.publishToDestination(translated)
}

func (b *MessagingBridge) publishToDestination(msg DestinationMessage) {
	b.delivered = append(b.delivered, msg)
}

func (b *MessagingBridge) Stats() (delivered, deadLettered int) {
	return len(b.delivered), len(b.deadLetters)
}

func main() {
	bridge := &MessagingBridge{}
	bridge.Process(SourceMessage{ID: "1", Payload: map[string]any{"orderId": 42}, ContentType: "application/json"})
	bridge.Process(SourceMessage{ID: "2", Payload: map[string]any{"orderId": 43}, ContentType: "application/xml"})
	delivered, deadLettered := bridge.Stats()
	fmt.Printf("delivered %d deadLettered %d\n", delivered, deadLettered)
}
```

Run with `go run messaging_bridge.go`. Output confirmed as
`delivered 1 deadLettered 1`.

Java, Rust, and Swift are omitted from this entry. The pattern is a system
integration and network I/O pattern, not one where a specific language
runtime changes its idiomatic shape the way, for example, a closure changes
Strategy in a functional language. The three languages above already show
the pattern's structural core, meaning the adapter, the translator, and the
dead letter routing, in a statically typed, a dynamically typed, and a
compiled systems language, and a fourth or fifth language would repeat the
same shape without adding new insight into the pattern itself.
