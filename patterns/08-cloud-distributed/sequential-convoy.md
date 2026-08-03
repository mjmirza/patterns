---
name: Sequential Convoy
slug: sequential-convoy
family: 08-cloud-distributed
category: Messaging and Integration
aliases: [Convoy Pattern, Session-Based FIFO Processing, Partitioned Sequential Processing, Key-Ordered Consumer Pattern]
first_described: "Microsoft Azure Architecture Center cloud design pattern catalog; earliest confirmed public documentation April 21, 2020 (docs.microsoft.com, Internet Archive capture); the mechanism it names was already in production use through Azure Service Bus message sessions before the catalog entry existed, and its problem framing descends from Hohpe and Woolf's Resequencer, Enterprise Integration Patterns, Addison-Wesley, 2003"
maturity: established
related: [competing-consumers, queue-based-load-leveling, priority-queue, publisher-subscriber, sharding, bulkhead, retry, throttling]
incompatible_with: []
verified: 2026-08-02
---

# Sequential Convoy

## 1. Name, aliases, and lineage

The canonical name in current use is Sequential Convoy, and its home is the
Microsoft Azure Architecture Center's cloud design pattern catalog. The
Internet Archive's earliest capture of the pattern's page, taken from the
`docs.microsoft.com` domain the catalog used before it moved to
`learn.microsoft.com`, is dated April 21, 2020
([Wayback Machine capture of the Sequential Convoy pattern page](http://web.archive.org/web/20200421154247/https://docs.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02). That is the earliest point at which this repository can
independently confirm the name existed in a public catalog entry, and it is
offered here as a lower bound, not as a claim about when the mechanism was
first built. The current text of the entry states the intent plainly. Group
related messages by a category key and process each group sequentially, one
message at a time, while processing different groups in parallel
([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02).

The pattern's problem framing is older than its catalog name. Gregor Hohpe and
Bobby Woolf described the Resequencer in 2003 as a stateful filter that
collects messages arriving out of order and republishes them in the correct
sequence, precisely because a Message Router or a set of Competing Consumers
had already scattered a naturally ordered stream across multiple paths
([Enterprise Integration Patterns, Resequencer](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Resequencer.html),
verified 2026-08-02; Hohpe, G. and Woolf, B., *Enterprise Integration Patterns.
Designing, Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
ISBN 0-321-20068-3, Message Routing chapter, Resequencer). Sequential Convoy
answers the same tension between order and parallelism, but it inverts the
Resequencer's strategy. The Resequencer lets order break and then repairs it
downstream with a buffer. Sequential Convoy prevents order from ever breaking
by routing every message that must stay in order to the same lane before any
consumer touches it, so there is nothing left to repair.

The word convoy deserves a warning before it is used for anything else,
because it already carries an established and unrelated meaning in operating
systems and database literature, the lock convoy or convoy effect, where
threads queue up behind a mutex and end up serialized far more than the
workload requires, degrading throughput as a pathology rather than a design
choice. Sequential Convoy is the deliberate, bounded version of that idea. A
lock convoy is an accident that happens to an entire system. A Sequential
Convoy is a boundary drawn on purpose around one category key, so that the
serialization is confined to the messages that actually need it and every
other category keeps moving. Readers coming from a systems-programming
background should hold onto that distinction, because the rest of this entry
depends on it. The pattern's entire value proposition is that it converts an
uncontrolled convoy into a controlled one.

No alternate name for this pattern carries an independent lineage of its own.
Session-Based FIFO Processing and Key-Ordered Consumer Pattern are descriptive
phrases used in vendor documentation and engineering blog posts to name the
same shape without invoking the catalog term, most visibly around Azure
Service Bus's session feature, which is the most literal implementation of
the pattern available on any major cloud platform
([Azure Service Bus message sessions](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-sessions),
verified 2026-08-02). Partitioned Sequential Processing is the phrase this
entry uses when describing the Kafka-style realization of the same idea,
where a partition key rather than a broker-managed session lock is the unit
that carries the ordering guarantee.

## 2. Problem and context

A system receives a stream of messages, and a subset of those messages must be
applied in the order they were produced because applying them out of sequence
corrupts the state they describe. The canonical illustration, and the one the
Azure catalog entry itself uses, is an order-tracking ledger. a create
operation, a transaction add, a transaction edit, and a delete, all for the
same order, arriving as separate messages
([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02). Apply the delete before the create and there is nothing
to delete. Apply the edit before the add and the edit targets a transaction
that does not exist yet. The correctness of the downstream state depends on
the order in which these specific messages are applied, even though the
system as a whole is also expected to process many orders' worth of messages
per second.

This is not a rare shape. Every domain built around an event log for a single
aggregate hits it. a shopping cart accumulating item-added and item-removed
events, a chat thread accumulating message-sent and message-edited events, an
IoT device accumulating firmware-state transitions, a financial ledger
accumulating debits and credits against one account. In each case the
aggregate, the cart, the thread, the device, the account, defines a natural
grouping key, and the correctness requirement is scoped to that key. Two
different carts, two different accounts, two different devices, have no
ordering relationship to each other at all. That last fact is what makes the
problem interesting rather than merely a case for a single global queue.

The context in which the tension becomes sharp is horizontal scale. A single
consumer reading one queue in strict arrival order trivially preserves
ordering, because there is only ever one thing happening at a time, but its
throughput ceiling is the inverse of one message's processing latency, and
that ceiling does not move no matter how much compute a team is willing to
add. The instinctive fix, adding more consumers pulling from the same queue,
is the Competing Consumers pattern, and it breaks the ordering guarantee on
contact. nothing stops consumer two from picking up message four for account
A while consumer one is still holding message two for the same account,
because a shared queue has no concept of which messages are related to each
other ([Microsoft Learn, Competing Consumers pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers),
verified 2026-08-02). The system is left with two knobs that each solve half
the problem and break the other half. a single consumer that is correct but
slow, or many consumers that are fast but wrong. Sequential Convoy exists
because neither knob is acceptable and the actual requirement, once stated
precisely, does not need either extreme. The requirement is order within a
key and parallelism across keys, and that is a narrower, achievable target
than global order or unconstrained concurrency.

## 3. Forces

**Ordering correctness versus throughput.** A processing pipeline that must
guarantee order pays for it with reduced parallelism at the point where the
guarantee is enforced, because a guarantee about sequence is, definitionally,
a guarantee that step two waits for step one. The pattern's entire design is
an attempt to shrink the surface over which that wait applies, from the whole
system down to one category key, but the wait inside a category never goes
away, and per-category throughput stays bounded by single-message processing
latency ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02).

**Coupling to a category key.** The pattern needs a key with two properties
that pull in opposite directions. cardinality high enough to give the system
real parallelism, and correlation strong enough that everything sharing a key
genuinely has an ordering relationship. Pick the key too coarse, one value for
an entire tenant instead of one value per order, and the system inherits most
of the single-consumer bottleneck under a different name. Pick it too fine, a
key that changes on every message, and the pattern degenerates into
unconstrained Competing Consumers because nothing shares a lane with anything
else. The key choice is a design decision that cannot be revisited casually
once producers depend on it.

**Consumer stickiness versus elasticity.** Once a consumer holds a lock, lease,
or partition assignment for a category, moving that work to a different
consumer instance requires releasing and reacquiring the lock, which
introduces latency and, on some brokers, a window where messages queue
without being drained. This works against the usual cloud-native assumption
that any instance can absorb any unit of work at any moment. The pattern
trades some of that elasticity for the ordering guarantee.

**Availability of a head-of-line blocker.** A message that a consumer cannot
process, because of a bug, a downstream outage, or a malformed payload, sits
at the front of its category's lane and blocks every message behind it,
because release-and-retry-in-order is exactly what the pattern is built to
enforce. Poison-message handling is not an edge case to bolt on later. It is
load-bearing, because the coupling that gives the pattern its correctness
guarantee is the same coupling that turns one bad message into an outage for
its entire category ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02).

**Cost of the coordination layer.** Whatever mechanism enforces per-key
ordering, a broker session lock, a partition assignment protocol, a
distributed lock service, is itself a piece of stateful infrastructure with
its own availability characteristics, its own cost, and its own failure
modes. A system that adopts this pattern is choosing to depend on that layer
being correct and available, on top of the correctness and availability
requirements it already had for the messages themselves.

## 4. Applicability and non-applicability

Reach for Sequential Convoy when a stream of messages carries a natural
grouping key, when messages sharing that key have a genuine ordering
dependency on one another such that applying them out of turn produces an
incorrect result, and when the number of distinct key values is large enough
relative to the required throughput that per-key sequential processing is not
itself the bottleneck. The Azure catalog states this directly. use the
pattern when messages must be processed in the order they arrive, and when
messages can be categorized so each category becomes an independent unit of
scale ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02). It fits well where a domain aggregate already implies
the key, an order ID, an account number, a device serial, a conversation ID,
because the key is not something the team invents for the messaging layer, it
is something the domain already has.

The pattern is not applicable, and reaching for it anyway is a mistake, in the
following situations.

- **No ordering dependency exists.** If messages are independent of one
  another, applying them in any order produces the same correct result, and
  the pattern only adds coordination cost for no benefit. Competing Consumers
  is the correct and simpler tool, and the Azure catalog says so explicitly.
  when order is not required, Competing Consumers gives simpler horizontal
  scaling without the session-locking overhead
  ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
  verified 2026-08-02).
- **Throughput requirements approach millions of messages per minute across
  the whole system, with a key space too small to spread that load.** The
  per-category sequential bound does not move regardless of consumer count,
  so a workload that genuinely needs uniformly high aggregate throughput and
  cannot decompose it into enough independent categories will hit a wall the
  pattern cannot remove ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
  verified 2026-08-02).
- **The ordering requirement is really a causal dependency between a small,
  fixed number of steps, not an open-ended sequence.** A three-step saga with
  a known start, middle, and end is better served by a Saga orchestrator or a
  Process Manager that models the steps explicitly, because those tools give
  compensating actions and visibility into where a specific instance stands,
  which a bare ordered queue does not provide.
- **The messages are already ordered by construction and merely need to be
  read in that order, not processed with side effects that depend on order.**
  A plain sequence number is enough to detect gaps or replay history. adding
  session locking or partition-based consumer pinning is unneeded weight when
  nothing downstream mutates shared state as each message is handled.
- **The broker or platform in use has no mechanism for exclusive, ordered
  delivery within a group, and the team is unwilling to build and operate
  that coordination themselves.** Rolling a custom distributed lock to
  simulate what Service Bus sessions or Kafka partitions already provide
  natively is a large amount of new failure surface to take on, and the
  pattern's own documentation flags this as a real risk. without native
  broker support, consumers must implement their own coordination, which adds
  complexity and risks duplicate processing or out-of-order execution
  ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
  verified 2026-08-02).
- **A single global total order across every message in the system is
  required, not merely order within independent groups.** That is a different
  and much harder problem, closer to a total order broadcast or a single
  append-only log with one writer, and Sequential Convoy's entire value comes
  from deliberately not solving that harder problem.

## 5. Structure

The pattern has four participants, and naming each one by its role rather than
by a generic class name keeps the structure legible across the different
brokers that implement it.

- **Producer.** Emits messages and is responsible for attaching the correct
  category key to each one, using whatever field the broker calls it.
  `SessionId` on Azure Service Bus, `MessageGroupId` on Amazon SQS FIFO
  queues, the record key on Apache Kafka, or an ordering key on Google Cloud
  Pub/Sub. The producer does not know or care which consumer will eventually
  handle the message. Producer key correctness is a hard dependency the whole
  pattern rests on. a mislabeled key routes a message into the wrong lane and
  corrupts that lane's state exactly as if two categories had been merged by
  accident ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
  verified 2026-08-02).

- **Broker (the demultiplexing layer).** Accepts messages tagged with a key
  and is responsible for two guarantees at once. within any one key, messages
  are delivered in the order they were enqueued, and across keys, delivery to
  different consumers can proceed independently and concurrently. This
  participant is where the pattern's implementations diverge the furthest,
  because the mechanism used to give this guarantee, a session lock on Azure
  Service Bus, a partition on Kafka or SQS, an ordering key on Pub/Sub, is a
  first-class broker concept on some platforms and something a team must
  approximate on others.

- **Lane (the logical sub-queue).** Not always a literal, separately
  provisioned structure, but always a real concept. the ordered subsequence
  of messages that share one category key. Azure Service Bus calls this a
  session and states plainly that a session acts in many ways like a sub
  queue ([Azure Service Bus message sessions](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-sessions),
  verified 2026-08-02). On Kafka the lane is the partition. On SQS FIFO
  queues, Amazon documents that the queue itself stores data across
  partitions determined by a hash of the message group ID, so the lane again
  maps onto a partition, this time chosen by the broker rather than declared
  by the producer ([Amazon SQS high throughput for FIFO queues, partitions
  and data distribution](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html),
  verified 2026-08-02).

- **Category consumer.** Holds an exclusive claim, a lock, a lease, or a
  partition assignment, on exactly one lane at a time, and processes that
  lane's messages one at a time, in order, never starting message N+1 until
  message N has been acknowledged or otherwise settled. A consumer process
  can, and typically does, hold claims on several different lanes
  simultaneously, each lane processed by its own logical worker loop, which
  is how the pattern achieves parallelism without allowing any single lane to
  run out of order.

A fifth, optional participant matters enough to name separately when it is
present. the fan-out stage. Many real deployments of this pattern begin with
a single ordered intake queue that a Sequential Convoy is layered on top of,
because the events that need per-key ordering do not arrive pre-tagged with
their category key. The Azure catalog's own worked example puts a ledger
processor in front of the pattern. it reads a single ledger stream in
sequence, and for each entry it sets the category key to the order ID before
forwarding the entry into the session-enabled queue that the real Sequential
Convoy operates on ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02). That single-threaded fan-out stage is worth calling out
in the structure because it becomes, honestly, the new bottleneck once the
downstream lanes are parallelized, a point this entry returns to under
Consequences.

## 6. ASCII structure diagram

```
                    +--------------+
                    |   Producer   |
                    | (sets key)   |
                    +------+-------+
                           |
                           v
              +------------------------------+
              |            Broker             |
              |  demultiplexes by category key |
              +---+-----------+-----------+---+
                  | key=A     | key=B     | key=C
                  v           v           v
             +--------+  +--------+  +--------+
             | Lane A |  | Lane B |  | Lane C |
             | [1,2,3]|  | [1,2]  |  | [1]    |
             +---+----+  +---+----+  +---+----+
                 |            |            |
                 v            v            v
          +-------------+ +-------------+ +-------------+
          | Consumer A  | | Consumer B  | | Consumer C  |
          | holds lock  | | holds lock  | | holds lock  |
          | on Lane A   | | on Lane B   | | on Lane C   |
          +-------------+ +-------------+ +-------------+

  Within one lane. strictly FIFO, one message in flight at a time.
  Across lanes.    fully concurrent, no ordering relationship at all.
```

The three vertical channels below the broker are drawn as separate lanes to
make the demultiplexing explicit, but on most real brokers they are not three
physically separate queues. On Azure Service Bus, all three sessions live in
one queue entity, and the broker itself routes each accepted receiver to the
session it has claimed ([Azure Service Bus message sessions](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-sessions),
verified 2026-08-02). On Kafka, the three lanes are three partitions of one
topic. The diagram draws them apart because that is the guarantee a reader
needs to understand, not because it is the physical layout.

## 7. Dynamics

At runtime the pattern's behavior is best read as two independent state
machines running side by side. the producer's send loop, which has no
knowledge of consumers at all, and each lane's claim-and-drain cycle, which
has no knowledge of any other lane.

A category consumer's lifecycle for a single lane looks like this on any
platform that gives native support for the pattern.

1. The consumer requests a lane to work on, either by asking the broker for
   the next available unclaimed session (Azure Service Bus's accept-next-session
   call) or by being assigned a set of partitions by a group-coordination
   protocol (Kafka consumer groups).
2. The broker grants an exclusive claim on that lane to this consumer and
   this consumer alone. No other consumer instance can receive a message from
   this lane while the claim is held.
3. The consumer receives the next unconsumed message in the lane, processes
   it to completion, including any side effects, and then explicitly settles
   it, acknowledges it as complete, or explicitly abandons it back to the
   lane for retry.
4. The consumer repeats step three until the lane is empty or its claim lock
   expires, whichever comes first.
5. When the lane empties, or when the consumer voluntarily releases the
   claim, the lane becomes available for a fresh accept-next-session call,
   possibly from a different consumer instance entirely, which is exactly how
   the pattern rebalances work across instances over time.

The following diagram traces two lanes running concurrently against one
shared broker, which is the behavior that distinguishes this pattern from
both a single global consumer and unconstrained Competing Consumers.

```
time -->

Producer:   sendA1  sendA2  sendB1  sendA3  sendB2
              |       |       |       |       |
              v       v       v       v       v
Broker:     [route to Lane A/B by key, preserve per-lane arrival order]

Consumer A                Consumer B
(holds Lane A lock)        (holds Lane B lock)
  |                          |
  recv A1                    recv B1
  process A1 ------.         process B1 ------.
                    | (A2 waits, cannot start  |
                    |  until A1 settles)       |
  settle A1         |                          settle B1
  recv A2 <---------'                          recv B2 <-'
  process A2                                   process B2
  settle A2                                    settle B2
  recv A3
  process A3
  settle A3

  Never observed.  A2 starting before A1 settles.
  Freely observed. B1 processing while A1 is still in flight.
```

One dynamic that does not show up in a clean diagram but shapes real
deployments is out-of-order arrival at the broker itself, before any lane
ordering has taken effect. Network retries, client-side batching, and
multi-path delivery can all reorder messages in transit before the broker
ever assigns them to a lane, so the Azure catalog recommends attaching
explicit sequence numbers, and optionally an end-of-sequence marker on the
final message of a logical unit, so a consumer can detect and react to a gap
rather than silently trusting arrival order
([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02).

## 8. Implementation variants

**Broker-native session locking (Azure Service Bus).** A producer sets the
`SessionId` property on each message. at the AMQP 1.0 protocol level this maps
to the `group-id` field. A consumer creates a session receiver, accepts a
session, and receives an exclusive lock covering every message currently in
that session and every message that arrives in it later, service-side, so the
lock holds even across multiple consumer machines coordinating through the
broker rather than through each other
([Azure Service Bus message sessions](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-sessions),
verified 2026-08-02). The documentation draws a sharp and useful distinction
here between two related but different guarantees. a bare sequence number
guarantees the order messages were enqueued and can be retrieved in, but not
the order they are actually processed in, because two competing receivers can
still interleave completion. only a session lock guarantees processing order,
by making it impossible for two receivers to hold the same session at once
([Azure Service Bus message sessions](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-sessions),
verified 2026-08-02). Service Bus also attaches an application-defined,
broker-held session state blob to each session, up to 256 KB on the Standard
tier and 100 MB on Premium, which lets a workflow handler record its progress
inside the broker itself so that if the process holding the session dies, a
new process accepting the same session can resume from where the last one
left off rather than replaying from the beginning
([Azure Service Bus message sessions](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-sessions),
verified 2026-08-02).

**Partition-keyed ordering (Apache Kafka).** Kafka has no session concept.
ordering is a property of the partition, and the partition is chosen by
hashing a producer-supplied key. Kafka's own introduction states the
guarantee directly. any consumer of a given topic-partition always reads that
partition's events in exactly the order they were written, and events sharing
a key are written to the same partition
([Apache Kafka, Introduction](https://kafka.apache.org/intro), verified
2026-08-02). The default partitioner documented by Confluent guarantees that
every message carrying the same non-empty key lands on the same partition,
using a hash of the key modulo the partition count, but the ordering
guarantee this produces at the producer client is conditional. it holds for
messages as they arrive at the producer, and it can be broken by retry
behavior unless `max.in.flight.requests.per.connection` is set to one, a
setting that trades away some producer-side pipelining specifically to keep
retries from reordering messages ahead of an earlier, still-in-flight one
([Confluent, Kafka Producer configuration and partitioning](https://docs.confluent.io/platform/current/clients/producer.html),
verified 2026-08-02). Consumer-side, "processing in order" on Kafka is a
convention enforced by the consumer group protocol assigning at most one
consumer instance per partition at a time, not a broker-held exclusive lock.
it is functionally the same shape as Service Bus sessions but arrived at
through partition assignment rather than through claim-and-release
semantics.

**Message-group queues (Amazon SQS FIFO).** A producer sets `MessageGroupId`
on every message sent to a FIFO queue. Amazon documents that FIFO queue data
is stored across internal partitions, and that the message group ID is hashed
to decide which partition a given message lands in, with items retained in
the order they were added within that partition
([Amazon SQS high throughput for FIFO queues, partitions and data
distribution](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html),
verified 2026-08-02). Each partition supports up to 3,000 messages per second
with batching, or 300 messages per second for unbatched send, receive, and
delete operations in supported regions, and AWS is explicit that a large,
well-distributed set of distinct group ID values is what lets a FIFO queue
spread load across many partitions rather than concentrating it on one
([Amazon SQS high throughput for FIFO queues, partitions and data
distribution](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html),
verified 2026-08-02). SQS does not give a consumer an exclusive claim
comparable to a Service Bus session. ordering within a group depends on the
consumer's own polling and processing discipline, which is a real difference
worth naming, because it means the correctness guarantee this variant gives
is narrower than the other two unless the application layer adds its own
single-consumer-per-group discipline on top.

**Ordering keys (Google Cloud Pub/Sub).** A publisher attaches an ordering key,
a string up to 1 KB, to each message. messages sharing a key are delivered
in the order they were published, provided they originate from the same
region, and messages with an empty ordering key carry no ordering guarantee
at all ([Google Cloud, Pub/Sub message ordering](https://docs.cloud.google.com/pubsub/docs/ordering),
verified 2026-08-02). The publish-side throughput on any single ordering key
is capped at 1 MBps by default, a hard, documented, per-key ceiling that
makes the pattern's core trade-off, per-category throughput bounded by a
fixed limit regardless of overall system capacity, into an explicit number
rather than an emergent property, and the subscriber side enforces the same
constraint from the other direction. with Pull or Push delivery, only one
message batch per ordering key can be outstanding at a time, and with
StreamingPull, callbacks for one key execute sequentially even though the
client library still has to be told, by the application, not to fan work for
that key out onto other threads asynchronously
([Google Cloud, Pub/Sub message ordering](https://docs.cloud.google.com/pubsub/docs/ordering),
verified 2026-08-02).

**Single active consumer over a plain FIFO queue (RabbitMQ).** RabbitMQ's
queues are natively ordered, first in, first out, by definition, but that
guarantee alone only holds when exactly one consumer drains the queue,
because message priorities and multiple concurrent consumers on the same
queue are both documented as things that change effective delivery order
away from strict FIFO ([RabbitMQ, Queues](https://www.rabbitmq.com/docs/queues),
verified 2026-08-02). RabbitMQ's Single Active Consumer feature turns this
into a genuine Sequential Convoy building block. several consumer processes
can subscribe to one queue for failover purposes, but the broker delivers
messages to exactly one of them at a time, so a team gets ordered delivery
with automatic failover to a standby consumer, at the cost of building the
category-to-queue mapping itself, because RabbitMQ has no native concept of a
category key inside a single queue the way Service Bus sessions or Kafka
partitions do.

**Application-level distributed lock, on a broker with no native support.**
When the messaging platform gives none of the above, teams sometimes build
their own version. a shared key-value store, a Redis instance, a database
row, holds a per-category lock or a per-category cursor, and a fleet of
otherwise-Competing-Consumers workers cooperate by acquiring that lock before
touching a category's messages. This is the variant the Azure catalog warns
about directly, because a home-grown coordination layer takes on the full
distributed-locking problem, expiry, fencing tokens, split-brain during a
network partition, as new surface area rather than inheriting it, already
solved, from the broker ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02).

## 9. Known production uses

**Azure Service Bus, message sessions.** This is the reference implementation
the catalog entry is written around, and it is documented as the primary
mechanism for the pattern on Azure, used through either an Azure Functions
Service Bus trigger configured for sessions or a Logic Apps peek-lock
connector consuming a session-enabled queue
([Microsoft Learn, Sequential Convoy pattern, Supporting technologies](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02). Sessions are unavailable on the Basic tier of Service
Bus and require Standard or Premium, which is itself evidence that the
feature is treated as a distinct, cost-relevant capability rather than an
incidental side effect of the messaging service
([Azure Service Bus message sessions](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-sessions),
verified 2026-08-02).

**Amazon SQS FIFO queues.** Amazon's own high-throughput FIFO documentation
frames its target workloads in terms this pattern would recognize directly.
real-time data streams such as telemetry ingestion, e-commerce order
processing where transactions for one customer must stay in sequence, and
financial systems processing market data and trades under ordering
constraints ([Amazon SQS high throughput for FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html),
verified 2026-08-02). AWS's explicit guidance to increase the cardinality of
message group IDs in order to raise achievable throughput is the SQS-specific
restatement of this pattern's central force, category granularity as the
knob that trades correctness for scale, described in AWS's own vocabulary
rather than the Azure catalog's.

**Apache Kafka, key-partitioned topics.** Kafka does not brand this a named
pattern the way Microsoft does, but the mechanism, keying events to a
partition specifically to preserve per-entity order while allowing the topic
as a whole to be consumed in parallel across many partitions, is the
documented, intended use of Kafka's partitioning model, stated in Kafka's own
introduction as the reason a customer ID or a vehicle ID is chosen as an
event key in the first place ([Apache Kafka, Introduction](https://kafka.apache.org/intro),
verified 2026-08-02). This is worth naming as an independent production use
rather than folding it into the Azure entry, because it demonstrates the
pattern is not an Azure-specific idea dressed up in vendor language. it is a
convergent solution that a completely different messaging architecture,
built around an immutable, partitioned commit log rather than a
session-locked queue, arrived at for the identical problem.

**Google Cloud Pub/Sub, ordering keys.** Google's documentation for ordering
keys states the mechanism exists specifically so that messages describing
updates to one entity, its own examples name a customer ID or a database
row's primary key, are delivered to subscribers in the order they were
published, which is the same entity-scoped ordering guarantee Service Bus
sessions and Kafka partition keys provide, implemented as a third distinct
mechanism on a third distinct platform ([Google Cloud, Pub/Sub message
ordering](https://docs.cloud.google.com/pubsub/docs/ordering), verified
2026-08-02).

Four independent platforms, built by three different vendors with three
different underlying architectures, a broker with session objects, an
immutable partitioned log, and a managed pub-sub service, converging on the
same shape, a category key that scopes an ordering guarantee to a group while
leaving groups free to run in parallel, is itself evidence that this is
solving a real, recurring problem rather than a pattern invented to justify a
catalog entry.

## 10. Consequences

**Positive.**

- Ordering correctness is preserved exactly where it is needed and nowhere
  else, so the system does not pay a global serialization tax to protect a
  guarantee that only a subset of its data actually requires.
- Throughput scales with the number of active, independent category keys, so
  adding consumer capacity increases real parallelism instead of merely
  adding workers that then race each other for the same locks.
- Producers stay decoupled from consumers. a producer never needs to know
  which physical instance, or how many instances, exist on the consuming
  side, which preserves the elasticity benefits a message broker exists to
  provide in the first place.
- The pattern composes cleanly with retry, dead-lettering, and monitoring
  primitives that most message brokers already expose per queue or per
  partition, so a team is not required to invent new observability tooling
  purely because ordering has been added to the requirements.

**Negative.**

- A poison message inside one category blocks every subsequent message in
  that category until it is resolved or moved aside, and the pattern's own
  documentation names this directly as a required design concern, not an
  edge case to defer ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
  verified 2026-08-02).
- Per-category throughput has a hard ceiling set by single-message processing
  latency, and no amount of horizontal scale-out removes that ceiling for any
  one category. it only adds more categories running in parallel.
- The choice of category key is close to permanent once producers depend on
  it. Changing the key's granularity later means a coordinated migration
  across every producer and consumer, not a configuration change in one
  place.
- Operational visibility gets harder. Monitoring one queue's depth is a
  familiar, well-understood metric. monitoring hundreds or thousands of
  active sessions, each with its own backlog, its own lock state, and its own
  potential to be dead-lettered, is qualitatively more work, and Microsoft's
  documentation calls this out as added operational overhead above ordinary
  queue consumption ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
  verified 2026-08-02).
- If the design includes a serial fan-out stage in front of the parallel
  lanes, and Microsoft's own worked example does exactly this by routing
  every ledger entry through one single-threaded processor before it reaches
  a session, that fan-out stage becomes the true throughput ceiling for the
  entire pipeline, and the elegant parallelism downstream cannot compensate
  for it ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
  verified 2026-08-02).

## 11. Failure modes and misuse

**Symptom.** One order, customer, or device silently stops receiving updates
while the rest of the system continues normally.
**Cause.** A message for that specific category has failed processing
repeatedly and now sits at the head of its lane, blocking everything queued
behind it, while every other category's lane is unaffected because lanes are
independent.
**Fix.** Configure and monitor a maximum delivery count with an automatic
dead-letter transition, which Azure Service Bus provides by default with a
value of ten, after which the poisoned message moves to the dead-letter
queue and the receiver resumes processing the rest of the session
([Azure Service Bus message sessions, Maximum delivery count in sessions](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-sessions),
verified 2026-08-02). Build a dashboard that alerts on lane age or backlog
depth, not merely on aggregate queue depth, because aggregate metrics can
look perfectly healthy while one specific lane is completely stalled.

**Symptom.** The same logical operation appears to have been applied twice, or
state briefly appears in an order that should have been impossible.
**Cause.** Two consumer instances momentarily believed they each held the claim
for the same category, most often because a lock or session lease expired
while the original holder was still mid-processing, most typically during a
slow downstream call, garbage collection pause, or network blip, and the
broker handed the lock to a second consumer before the first one finished.
**Fix.** Tune the lock or lease duration against realistic worst-case processing
latency rather than typical latency, and use the platform's lock-renewal
mechanism for genuinely long-running work instead of extending a single fixed
lease. Microsoft frames this exact trade-off directly. too short a lock
duration causes reprocessing from expiration, too long a duration delays
recovery from a stalled consumer, and renewal is the intended mechanism for
resolving the tension ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02).

**Symptom.** Order-dependent business logic occasionally corrupts state for a
specific customer, and the corruption is not reproducible on demand.
**Cause.** The category key was chosen too coarsely, several unrelated logical
sequences share one key, so unrelated messages are forced through the same
lane and a message from sequence B is delivered between two messages of
sequence A that had no actual ordering relationship with B at all, or the key
was set incorrectly by a producer bug and a message was misrouted into the
wrong lane entirely.
**Fix.** Audit key assignment at the producer boundary with schema validation or
an explicit allowlist of valid key patterns, add a lightweight consumer-side
sanity check, such as confirming a sequence number is contiguous with the
last one seen for that key, and treat any gap or discontinuity as a signal to
alert rather than silently proceeding. The pattern's own documentation lists
this as producer key correctness and recommends adding key-validation logic
at the consumer specifically because the blast radius of a misrouted message
is severe ([Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02).

**Symptom.** Overall system throughput plateaus well below what the consumer
fleet's compute budget should allow, even as more consumer instances are
added.
**Cause.** The number of distinct, concurrently active category keys is smaller
than the number of consumer instances available, so additional instances
have no lane to claim and sit idle, or a small number of hot keys dominate
the traffic and their per-key throughput ceiling, not aggregate compute, is
the actual bottleneck.
**Fix.** Measure active-lane count directly rather than inferring it from
throughput, and, if a small number of keys are genuinely hot, consider
whether the granularity of the key can be safely increased for those specific
keys, for example splitting one very active account into sub-periods or
sub-shards if the domain allows it without breaking the correctness guarantee
that motivated the pattern in the first place.

**Symptom.** A session that had been working for months suddenly starts
dead-lettering every message the moment a specific message is reintroduced
after a manual fix.
**Cause.** A message that was previously dead-lettered was manually moved back
into the original queue for reprocessing, and Service Bus documents this as
losing the message's original position relative to the rest of the session,
because the resubmitted message receives a new enqueue time and sequence
number on re-entry ([Azure Service Bus message sessions, Maximum delivery
count in sessions](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-sessions),
verified 2026-08-02).
**Fix.** Never blindly replay a dead-lettered message back into the live session.
Replay it through a path that re-derives its correct position, for example
by re-running it through the same fan-out or sequencing stage that produced
it originally, or by handling it out of band with explicit compensating
logic, rather than assuming the broker will restore its place in line.

## 12. Trade-off matrix

| Force | Sequential Convoy | Competing Consumers | Single global consumer | Resequencer (EIP) |
|---|---|---|---|---|
| Ordering scope | Per category key, strict | None guaranteed | Global, strict | Global, restored after the fact |
| Aggregate throughput | Scales with active key count | Scales with consumer count | Fixed, single-message bound | Scales like Competing Consumers upstream, bounded by buffer size downstream |
| Coordination overhead | Moderate, one lock or partition per active key | Minimal | None | High, must buffer and detect complete sequences |
| Failure blast radius | One category, on a poison message | One message, on a poison message | Entire system, on a poison message | Entire buffer, on a missing message in a sequence |
| Elasticity | Bounded by key cardinality | High | None | High upstream, constrained by buffer memory downstream |
| Implementation cost on a broker with native support | Low | Low | Trivial | High, custom buffering logic is usually hand-built |
| Implementation cost with no native support | High, must build locking | Low | Trivial | High regardless of broker |
| Best fit | Ordering matters per entity, throughput matters in aggregate | Ordering does not matter at all | Small systems, correctness dominates every other concern | Order was broken by an upstream router and cannot be prevented, only repaired |

The comparison against a single global consumer is worth stating plainly in
prose, not only in the table. a single consumer is not a strawman here, it is
the honest zero-parallelism baseline the pattern exists to beat, and any team
evaluating whether the added coordination cost of Sequential Convoy is worth
paying should first confirm that a single consumer genuinely cannot meet
throughput requirements, because a single consumer's operational simplicity
is real and should not be discarded for a category cardinality that turns out
to be one or two values in practice.

## 13. Related and incompatible patterns

**Competing Consumers.** This is the pattern Sequential Convoy exists to fix
without abandoning. The Azure catalog states the relationship directly.
Competing Consumers scales throughput but removes per-message ordering, and
Sequential Convoy addresses that gap by partitioning messages into
category-keyed sessions and processing each session sequentially
([Microsoft Learn, Sequential Convoy pattern, Related resources](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02). In practice, Sequential Convoy is best understood as
Competing Consumers with an additional constraint layered on top, not as a
competing alternative to it. every lane inside a Sequential Convoy is, on its
own, a single consumer, and the pattern's parallelism comes entirely from
running many such single consumers, one per lane, concurrently.

**Queue-Based Load Leveling.** The two compose rather than conflict. Load
leveling absorbs bursty producer traffic into a buffer so consumers are not
overwhelmed by spikes. Sequential Convoy adds the per-category ordering
constraint on top of that same buffer. Microsoft describes this explicitly.
Sequential Convoy builds on the buffering that load leveling provides, adding
session-based partitioning so the queue both levels load across categories
and preserves ordering within each one ([Microsoft Learn, Sequential Convoy
pattern, Related resources](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02).

**Priority Queue.** These two constraints, ordering and priority, are
orthogonal and can be combined when both matter at once. a workload might
need every message for one order processed in sequence, and also need
premium customers' orders processed ahead of standard customers' orders. The
Azure catalog names this combination directly and treats it as a natural
composition rather than a conflict ([Microsoft Learn, Sequential Convoy
pattern, Related resources](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy),
verified 2026-08-02).

**Publisher-Subscriber.** A Sequential Convoy is frequently the consumer side
sitting behind a fan-out that Publisher-Subscriber performs, particularly
when different downstream systems need the same ordered event stream but each
maintains its own independent processing cursor. The two are complementary
layers rather than substitutes for each other. Publisher-Subscriber decides
who receives a copy of a message, Sequential Convoy decides in what order
each recipient is allowed to act on the messages it receives.

**Sharding.** The category key that drives a Sequential Convoy's lanes is
frequently the same key a data layer uses to shard storage for the same
entities. When both layers key on the same field, an order ID for example,
the messaging tier's ordering guarantee and the storage tier's partitioning
scheme reinforce each other, and a consumer processing one lane can often
write to exactly one storage shard without any cross-shard coordination at
all, which is a meaningful simplification worth designing toward
deliberately rather than discovering by accident.

**Bulkhead.** Sequential Convoy's per-category isolation is a specific
instance of the Bulkhead pattern's general principle, that failures in one
partition of a system should not consume the resources or availability of
other partitions. A stalled or poisoned lane behaves exactly like a
compartment that has taken on water in a ship's bulkhead design. it is
contained, and the rest of the vessel keeps moving, provided the bulkhead was
actually sized and monitored correctly.

**Resequencer (Enterprise Integration Patterns).** These two patterns solve
the identical problem, ordering that a Message Router or set of Competing
Consumers threatens to break, with opposite strategies, and they are worth
naming as alternatives to each other rather than as complements. Resequencer
lets messages arrive out of order and repairs the sequence with a buffer
after the fact. Sequential Convoy prevents the disorder from occurring by
routing same-category messages to the same lane before any consumer sees
them. A team should pick one, not both, for a given ordering requirement,
because running both at once means paying the coordination cost of
Sequential Convoy's lanes and still needing Resequencer's buffer to handle
whatever the lanes failed to prevent, which defeats the purpose of adopting
either.

No pattern in this catalog is flagged as strictly incompatible with Sequential
Convoy in the sense of being impossible to combine. the closest thing to an
incompatibility is architectural rather than mechanical, adopting Sequential
Convoy where a true single global total order is required, discussed under
Applicability and non-applicability, is a design mistake rather than a
technical conflict, because nothing prevents the code from compiling or the
system from running, it merely fails to deliver the guarantee the team
actually needed.

## 14. Refactoring path in and out

**Introducing the pattern into a system that currently uses a single global
consumer.** Start by confirming a genuine category key exists in the domain
and that it is already present, or can be cheaply derived, on every message
that needs ordering. if it is not present, add it at the point of message
creation before touching any consumer code. Stand up the broker-native
mechanism, sessions, partition keys, ordering keys, alongside the existing
single-consumer path rather than replacing it outright, and route a small,
low-risk slice of traffic, one category or one percentage of categories, into
the new path first. Confirm order is preserved for that slice under load,
including under a simulated consumer restart, before widening the rollout.
Only after the new path is proven should the single global consumer be
retired, and it should be retired by simply stopping its deployment once
traffic has been fully migrated, not by deleting its code immediately,
because it is a useful rollback target for a longer period than teams
usually expect.

**Introducing the pattern into a system that currently uses unconstrained
Competing Consumers.** This direction is more delicate, because Competing
Consumers by design has already accepted messages without any ordering
contract, and existing consumer code may implicitly, and perhaps
unknowingly, depend on being allowed to process messages out of order. Audit
consumer logic first for any place that would silently produce a wrong
result under reordering. these are frequently the exact bugs the migration is
meant to fix, but they must be found before the migration, not discovered
after it in production. Add the category key to the message schema as a new,
optional field, backfilled from existing message content wherever possible,
before switching any consumer over. Migrate consumers to the session- or
partition-aware receive API incrementally, one category range at a time, and
monitor for the classic symptom of an incomplete migration. a category whose
messages are being drained by two different consumer generations
simultaneously, old and new, which briefly recreates the exact ordering bug
the migration exists to remove.

**Removing the pattern once it has stopped earning its place.** This
happens most often when a domain's data model changes such that the ordering
dependency the pattern was protecting no longer exists, for example when an
event-sourced aggregate is replaced by a system that stores current state
directly and no longer needs to replay an ordered history to reconstruct it.
Confirm the ordering dependency is genuinely gone, not merely rare, by
auditing recent traffic for cases where two messages for the same category
arrived close enough in time that reordering was a real possibility. if such
cases still occur even occasionally, the dependency has not gone away, it has
only become less visible. Once confirmed, migrate consumers back onto a
Competing Consumers model incrementally, in the same category-range-at-a-time
manner used for the introduction, and retire the session or partition
configuration on the broker only after consumer-side migration is complete
and verified, because a broker still enforcing ordering that no consumer
relies on is harmless overhead, while a consumer relying on ordering the
broker no longer enforces is a silent correctness bug waiting to happen.

## 15. Testing and verification

Ordering bugs are notoriously difficult to catch with ordinary unit tests,
because a test that submits one message at a time and asserts on the result
never exercises the interleaving that produces the bug. Verification for this
pattern needs to be organized around three distinct levels.

**Unit level, the lane state machine in isolation.** Test the drain loop
directly, without any real broker, by feeding it a deterministic, in-memory
queue of messages for a single category and asserting that the handler is
invoked strictly in submission order, that a handler which raises or rejects
does not cause the next message to be dequeued, and that the lane correctly
reports itself empty and releasable once drained. This is straightforward,
fast, and should be the majority of the pattern's automated test coverage,
because it isolates the one property the pattern exists to guarantee from
everything else the system does.

**Property level, order is preserved under adversarial interleaving.**
Generate a randomized set of messages across several category keys with
randomized submission timing, randomized handler latency, including some
handlers that intentionally fail on the first attempt and succeed on retry,
and assert, after everything settles, that within every single category the
final observed processing order exactly matches submission order, while
placing no constraint whatsoever on the relative order between different
categories. This is precisely the property the code examples in this entry
demonstrate directly with a fixed two-lane scenario. a production test suite
should generalize that scenario to randomized keys, randomized counts, and
randomized failure injection, run across many seeds, so that a race condition
which only manifests one time in a thousand executions has a real chance of
being caught before it reaches production.

**Integration level, the real broker's guarantee, not a mock of it.** A mock
message broker in a test suite is nearly guaranteed to model ordering more
strictly than the real broker actually provides, because the mock's author
naturally builds the deterministic version they wish existed. Run integration
tests against a genuine broker instance, whether that is a local Service Bus
emulator, a local Kafka broker, or a containerized RabbitMQ instance, and
specifically test the boundary conditions the platform's own documentation
warns about. a lock or lease expiring mid-processing and being reacquired by
a second consumer, which the test should assert results in at-least-once
delivery combined with idempotent handling rather than data corruption, and a
consumer crash mid-session, which the test should assert leaves the session
state, if the broker supports one, intact for the next consumer to resume
from rather than lost.

Chaos testing earns its keep specifically on the poison-message failure
mode identified in dimension 11. deliberately inject a message engineered to
fail processing every time, submit it into the middle of an otherwise healthy
category's message stream, and confirm that the dead-lettering and
maximum-delivery-count configuration actually unblocks the rest of that
category within the expected time bound, rather than trusting that the
configuration is correct because it looks correct in a settings file.

## 16. Observability signals

Aggregate queue depth, the metric most teams already collect for any message
system, is close to useless on its own for this pattern, because it can
report a perfectly healthy number while one specific, business-critical
category is completely stalled behind a poison message. The signals worth
collecting specifically for Sequential Convoy are as follows.

- **Active lane count.** How many categories currently have an active,
  claimed consumer, tracked over time. A sudden drop when producer traffic
  has not dropped is a strong signal that consumers are failing to accept
  new lanes, often because of a lock or lease acquisition problem on the
  broker side.
- **Per-lane backlog depth and age of the oldest unprocessed message in each
  lane.** This is the metric that actually surfaces a stalled category,
  because a stalled lane's oldest message age grows without bound while every
  healthy lane's oldest message age stays near zero. Alert on age, not on
  count, since a legitimately busy but healthy lane can have real depth
  without being stuck.
- **Dead-letter rate, broken out per category where the broker supports it.**
  A spike concentrated in one category is a data or logic bug specific to
  that category's messages, while a spike spread evenly across many
  categories usually indicates a systemic problem in the shared consumer
  code itself.
- **Lock or lease renewal failures and lock reacquisition events.** These
  directly surface the classic false-duplicate-claim failure mode from
  dimension 11 before it manifests as a data-corruption incident downstream,
  and they are usually available as native broker metrics rather than
  something the application must compute itself.
- **Distribution of messages across category keys.** A small number of hot
  keys dominating overall traffic is the direct, measurable signal for the
  throughput-plateau failure mode. without this metric, the plateau is easy
  to misattribute to insufficient consumer compute rather than to key
  cardinality, which sends an operations team chasing the wrong fix.
- **End-to-end per-category latency, from message enqueue to settlement,**
  distinct from per-message processing time, because a lane that is
  individually fast but has a long backlog will show fast per-message
  processing alongside unacceptably slow end-to-end latency for messages
  near the back of that lane, and only the end-to-end number reveals the
  gap.

A useful operational habit is to build a dashboard sorted by oldest-message
age across all currently active lanes, descending, rather than one sorted by
raw backlog count. the lanes at the top of that view are, almost without
exception, the ones that need immediate attention, while a lane with a
hundred messages that are all seconds old is not actually in trouble.

## 17. Security and privacy implications

The category key itself is frequently a piece of business-identifying data,
an order ID, a customer account number, a device serial, and it is often
placed directly into broker-level routing metadata, a session ID field, a
partition key, an ordering key, rather than into the encrypted message
payload. Depending on the broker and the deployment, that metadata can be
visible to infrastructure operators, appear in broker-side logs and metrics,
or be exposed through management APIs used for operational monitoring, even
when the message body itself is encrypted end to end. Teams working under
data-minimization or pseudonymization requirements should evaluate whether
the raw domain identifier can be routed through a derived, non-reversible key
instead, a keyed hash of the order ID rather than the order ID itself, while
still preserving the property the pattern actually needs, that the same
logical entity always maps to the same category key.

The head-of-line blocking failure mode has a security dimension beyond
availability. a malicious actor who can inject even one message per category
that reliably fails processing gains the ability to selectively deny service
to specific categories at low cost, without needing to overwhelm the system
with volume the way a conventional denial-of-service attempt would. Input
validation at the point where a producer accepts a message, and where a
category key is assigned to it, deserves the same rigor as input validation
anywhere else user- or partner-supplied data enters the system, precisely
because this pattern converts a single malformed message into a targeted,
sustained outage rather than a single failed request.

Access control around who can accept, claim, or otherwise take ownership of a
given lane matters more here than for an ordinary shared queue, because
holding a lane's claim grants exclusive visibility into every message queued
for it, potentially including sensitive business data for one specific
customer or account concentrated into a single stream that a broader,
unpartitioned queue would have interleaved with everyone else's traffic. A
broker configuration that grants broad, unscoped receive permissions across
every session or partition on a queue effectively grants broad read access
to every category's data at once, and access policies should be scoped as
narrowly as the broker platform allows, down to specific sessions or
partitions where that capability exists.

Where a session state facility is in use, Azure Service Bus's is the
documented example, that state is an opaque, application-controlled blob held
inside the broker itself, and it inherits the broker's storage and retention
posture rather than the application's, which matters for any workload
subject to data residency, retention limits, or right-to-erasure obligations,
because deleting the application's own database record for a customer does
not automatically clear session state a workflow left behind inside the
message broker.

## Code examples

The following implementation demonstrates the pattern's core mechanical
property directly, without depending on any specific cloud broker. messages
sharing a category key are processed strictly in submission order, messages
in different categories run fully concurrently, and each language's version
proves both properties at the end of its own run. All four samples were
compiled and executed for this entry. each run printed `true` for sequence
preservation in both demonstrated categories and `true` for concurrent
execution across categories.

### TypeScript

```typescript
type Handler<T> = (message: T) => Promise<void>;

interface Lane<T> {
  queue: T[];
  draining: boolean;
}

class SequentialConvoyDispatcher<T> {
  private lanes = new Map<string, Lane<T>>();

  constructor(private readonly handler: Handler<T>) {}

  submit(key: string, message: T): void {
    let lane = this.lanes.get(key);
    if (lane === undefined) {
      lane = { queue: [], draining: false };
      this.lanes.set(key, lane);
    }
    lane.queue.push(message);
    if (!lane.draining) {
      lane.draining = true;
      void this.drain(key, lane);
    }
  }

  private async drain(key: string, lane: Lane<T>): Promise<void> {
    while (lane.queue.length > 0) {
      const next = lane.queue.shift() as T;
      // per-lane order is the contract this dispatcher exists to hold
      await this.handler(next);
    }
    lane.draining = false;
    this.lanes.delete(key);
  }

  activeLaneCount(): number {
    return this.lanes.size;
  }
}
```

Compiled with `tsc --target es2020 --module commonjs --strict` and run under
Node.js. A driver script submitted four messages for category `order-A` and four
for `order-B`, with a five millisecond artificial handler delay, and printed
`true` for per-category sequence preservation, `true` for cross-category
concurrency, and `0` for active lanes once both were fully drained.

### Python

```python
import asyncio
from collections import deque
from dataclasses import dataclass
from typing import Awaitable, Callable, Deque, Dict


@dataclass
class Lane:
    queue: Deque[object]
    draining: bool = False


class SequentialConvoyDispatcher:
    def __init__(self, handler: Callable[[object], Awaitable[None]]) -> None:
        self._handler = handler
        self._lanes: Dict[str, Lane] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    def submit(self, key: str, message: object) -> None:
        lane = self._lanes.get(key)
        if lane is None:
            lane = Lane(queue=deque())
            self._lanes[key] = lane
        lane.queue.append(message)
        if not lane.draining:
            lane.draining = True
            self._tasks[key] = asyncio.ensure_future(self._drain(key, lane))

    async def _drain(self, key: str, lane: Lane) -> None:
        while lane.queue:
            message = lane.queue.popleft()
            await self._handler(message)
        lane.draining = False
        del self._lanes[key]

    async def join(self) -> None:
        while self._tasks:
            tasks, self._tasks = self._tasks, {}
            await asyncio.gather(*tasks.values())

    def active_lane_count(self) -> int:
        return len(self._lanes)
```

Run directly with `python3` (3.14). The same eight-message, two-category
scenario as the TypeScript sample produced identical output. order preserved
within each category, overlapping execution across categories, zero active
lanes after `join()` returned.

### Go

```go
import "sync"

type message struct{ key string }

type lane struct {
	mu     sync.Mutex
	queue  []message
	active bool
}

type dispatcher struct {
	mu      sync.Mutex
	lanes   map[string]*lane
	wg      sync.WaitGroup
	handler func(message)
}

func (d *dispatcher) submit(m message) {
	d.mu.Lock()
	ln, ok := d.lanes[m.key]
	if !ok {
		ln = &lane{}
		d.lanes[m.key] = ln
	}
	d.mu.Unlock()

	ln.mu.Lock()
	ln.queue = append(ln.queue, m)
	shouldStart := !ln.active
	if shouldStart {
		ln.active = true
	}
	ln.mu.Unlock()

	if shouldStart {
		d.wg.Add(1)
		go d.drain(m.key, ln)
	}
}

func (d *dispatcher) drain(key string, ln *lane) {
	defer d.wg.Done()
	for {
		ln.mu.Lock()
		if len(ln.queue) == 0 {
			ln.active = false
			ln.mu.Unlock()
			d.mu.Lock()
			delete(d.lanes, key)
			d.mu.Unlock()
			return
		}
		next := ln.queue[0]
		ln.queue = ln.queue[1:]
		ln.mu.Unlock()

		d.handler(next)
	}
}
```

Built and run with `go run` (go1.26.4, darwin/arm64). Each lane runs on its
own goroutine, guarded by a per-lane mutex protecting the queue and a
dispatcher-level mutex protecting the lane registry. the same two-category
scenario confirmed strict per-category order and genuine goroutine-level
concurrency across categories, with both mutexes held only for the brief
critical section around queue manipulation, never across the handler call
itself.

### Rust

```rust
use std::collections::{HashMap, VecDeque};
use std::sync::{Arc, Mutex};

struct Msg;

struct Lane {
    queue: VecDeque<Msg>,
    active: bool,
}

struct Dispatcher<F: Fn(&Msg) + Send + Sync + 'static> {
    lanes: Mutex<HashMap<String, Arc<Mutex<Lane>>>>,
    handler: Arc<F>,
}

impl<F: Fn(&Msg) + Send + Sync + 'static> Dispatcher<F> {
    fn drain(self: &Arc<Self>, key: String, lane: Arc<Mutex<Lane>>) {
        loop {
            let next = {
                let mut guard = lane.lock().expect("lane mutex poisoned");
                match guard.queue.pop_front() {
                    Some(m) => m,
                    None => {
                        guard.active = false;
                        drop(guard);
                        let mut lanes = self.lanes.lock().expect("lane registry mutex poisoned");
                        lanes.remove(&key);
                        return;
                    }
                }
            };
            // strict per-lane order is the pattern's contract, the next
            // message in this lane never starts until the handler for this
            // one returns.
            (self.handler)(&next);
        }
    }
}
```

Compiled with `rustc -O` against the standard library only, no external
crates, using one operating-system thread per active lane and a `Mutex`
guarding each lane's queue plus a second `Mutex` guarding the lane registry
itself. The same two-category, eight-message scenario, run with a real five
millisecond `thread::sleep` inside the handler to make concurrent execution
observable, printed `true` for both per-category order checks and `true` for
the cross-category concurrency check, confirming the guarantee holds under
genuine OS-level thread parallelism, not only under a single-threaded async
runtime's cooperative scheduling.

All four dispatchers share one deliberate limitation worth stating rather
than hiding. none of them is a message broker. Each is an in-process,
single-machine simulation of the guarantee a real broker like Azure Service
Bus, Kafka, or SQS provides across a fleet of machines, and none of them
handles the distributed concerns, lock expiry across a network partition,
consumer crash recovery, at-least-once redelivery, that a production
deployment of this pattern must handle using the specific broker's own
mechanisms documented in dimension 8.

## 18. References

- [Microsoft Learn, Sequential Convoy pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy), Azure Architecture Center, verified 2026-08-02.
- [Wayback Machine capture of the Sequential Convoy pattern page](http://web.archive.org/web/20200421154247/https://docs.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy), Internet Archive, capture dated April 21, 2020, verified 2026-08-02.
- [Microsoft Learn, Competing Consumers pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers), Azure Architecture Center, verified 2026-08-02.
- [Azure Service Bus message sessions](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-sessions), Microsoft Learn, verified 2026-08-02.
- [Amazon SQS high throughput for FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html), AWS Documentation, verified 2026-08-02.
- [Apache Kafka, Introduction](https://kafka.apache.org/intro), Apache Software Foundation, verified 2026-08-02.
- [Confluent, Kafka Producer configuration and partitioning](https://docs.confluent.io/platform/current/clients/producer.html), Confluent Documentation, verified 2026-08-02.
- [Google Cloud, Pub/Sub message ordering](https://docs.cloud.google.com/pubsub/docs/ordering), Google Cloud Documentation, verified 2026-08-02.
- [RabbitMQ, Queues](https://www.rabbitmq.com/docs/queues), RabbitMQ Documentation, verified 2026-08-02.
- [Enterprise Integration Patterns, Resequencer](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Resequencer.html), verified 2026-08-02.
- Hohpe, G. and Woolf, B., *Enterprise Integration Patterns. Designing, Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, ISBN 0-321-20068-3, Message Routing chapter, Resequencer.
