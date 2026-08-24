---
name: Queue-Based Load Leveling
slug: queue-based-load-leveling
family: 08-cloud-distributed
category: Resilience and Traffic Management
aliases: [Load Leveling, Elastic Queue, Queue-Based Buffering, Smoothing Buffer]
first_described: "Homer, Sharp, Brader, Narumoto, Swanson. Cloud Design Patterns. Microsoft patterns & practices, 2014"
maturity: canonical
related: [rate-limiting, bulkhead, circuit-breaker, retry, publisher-subscriber, dead-letter-queue, backpressure, load-shedding, cqrs]
incompatible_with: [synchronous-request-response]
verified: 2026-08-02
---

# Queue-Based Load Leveling

## 1. Name, aliases, and lineage

The canonical name is Queue-Based Load Leveling. It was catalogued by Microsoft's
patterns & practices team in Alex Homer, John Sharp, Larry Brader, Masashi
Narumoto and Trent Swanson, *Cloud Design Patterns. Prescriptive Architecture
Guidance for Cloud Applications*, Microsoft patterns & practices, 2014, ISBN
978-1-62114-036-8, as one of twenty four patterns for building on Windows Azure.
The catalog entry migrated to the Azure Architecture Center and is maintained
there today, described as using a queue that acts as a buffer between a task and
the service that it invokes, to smooth intermittent heavy loads that might cause
the service to fail or the task to time out ([Microsoft Learn, Queue-Based Load
Leveling
pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling),
verified 2026-08-02).

The most common alias is simply **Load Leveling**, used interchangeably in the
same Microsoft documentation and in most engineering blog posts on the topic.
**Elastic Queue** appears in some AWS-oriented writing, emphasising that the
consumer fleet is expected to scale against the queue rather than stay fixed.
**Queue-Based Buffering** and **Smoothing Buffer** describe the same mechanism
from the angle of the queue's function rather than its position in the
architecture, and both show up in vendor documentation for message brokers such
as Amazon SQS and Azure Service Bus when they describe their own role in a
system.

The pattern did not originate the underlying idea. Task queues, job queues and
message-oriented middleware predate the 2014 catalog entry by decades, and the
messaging-channel vocabulary that queue-based buffering builds on was already
formalised in Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns.
Designing, Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
ISBN 0-321-20068-3, in the Point-to-Point Channel and Competing Consumers
patterns (see dimension 13). What the Microsoft catalog contributes is a name
and a frame specific to the cloud era: an elastic, pay-for-what-you-use consumer
fleet that scales against a durable, managed queue, rather than a fixed pool of
on-premises worker processes reading from a self-hosted broker. That framing is
why the pattern is filed under cloud and distributed patterns here rather than
under the older enterprise integration family, even though its ancestry runs
directly through that family.

A naming note worth stating plainly, because it causes real confusion. "Load
leveling" is not "load balancing". A load balancer spreads concurrent requests
across a set of servers at the moment they arrive, so the total arrival rate
into the whole server pool is exactly the total rate offered by the clients.
Queue-Based Load Leveling changes the arrival rate the *consumer* actually
experiences by inserting a buffer in front of it, so a burst that hits the queue
in one second can be drained by the consumer over the following minute. The two
techniques work together rather than replace each other, and a system commonly
uses both, a load balancer in front of the API layer that accepts requests and
enqueues work, and a queue behind it that levels what the workers see.

## 2. Problem and context

A system accepts work at a rate that varies over time, sometimes sharply, while
the component that actually performs the work has a roughly fixed processing
capacity per unit time. The mismatch between the two is the whole problem.

The situation is recognisable from the outside without knowing the pattern's
name. A checkout service gets slammed for ninety seconds during a flash sale and
then goes quiet for twenty minutes. A photo-sharing app gets a burst of uploads
every evening between seven and nine as people finish their day. A batch import
job drops ten thousand records into a system at once, once a day, at a time
nobody controls precisely. A downstream dependency, a payment gateway, an
inventory database, a third-party API with its own rate limit, has a hard
ceiling on how many operations per second it can sustain, and that ceiling is
well below the peak rate at which the upstream system generates work.

Two responses to that mismatch are the ones teams reach for first, and both
break under real load. The first is to size the consuming service for the peak,
provisioning enough capacity that even the worst burst is absorbed without
delay. This works until the peak grows past the provisioned ceiling, which it
eventually does, and in the meantime the excess capacity sits idle outside the
burst window, which is most of the time, so it is expensive. The second is to
let the producer call the consumer directly and synchronously, request in,
response out, and simply add more consumer instances when load rises. This
couples the producer's success to the consumer's availability and current
saturation. When the consumer is briefly overwhelmed, the producer's requests
queue up inside TCP connection backlogs, thread pools and load balancer
timeouts, invisibly and without any policy governing how that queueing behaves,
until something starts returning errors or timing out. The queue exists in that
second scenario regardless: it is just hidden inside infrastructure that was
never designed to be a queue, has no depth limit anyone chose on purpose, and
gives an operator no number to look at.

Queue-Based Load Leveling makes the buffering explicit and gives it a policy. A
message queue sits between the producer and the consumer. The producer's job
becomes "durably record that this work needs to happen", which is a fast,
cheap, and highly available operation when the queue technology is chosen well.
The consumer's job becomes "pull work from the queue at whatever rate the
consumer's own current capacity allows", entirely decoupled in time from when
the work arrived. The context that makes this the right answer, not merely an
available one, has three properties together.

- The producer does not need an immediate, synchronous answer containing the
  result of the work. It needs an acknowledgement that the work was accepted.
- The work is idempotent, or can be made idempotent, because most queue
  technologies deliver at least once rather than exactly once (see dimension
  4 and dimension 11).
- The arrival rate of work is bursty or unpredictable relative to a downstream
  system's sustainable processing rate, so a buffer genuinely earns its cost.

## 3. Forces

The pattern trades one problem for a different, and usually more tractable,
one. This section is stated as judgement, weighing which pressure the pattern
favours and which it costs, grounded in the mechanism rather than in a single
citable source.

**The central trade, stated plainly.** Queue-Based Load Leveling converts a
*capacity problem* into a *latency problem*. Before the queue, an overloaded
consumer either rejects work outright or degrades in ways that are hard to
predict: memory pressure, connection exhaustion, cascading timeouts across
whatever else shares the consumer's resources. After the queue, the consumer
never sees more concurrent work than it was designed to handle, because the
queue absorbs the excess. But that absorbed excess does not vanish, it sits in
the queue as backlog, and every message sitting in that backlog is a unit of
work whose completion the producer, and whoever is waiting on the producer, has
to wait longer for. The cost the pattern removes from the consumer's
availability is paid instead by the producer's end-to-end latency. A system
that adopts this pattern without accounting for that shift is trading one
failure mode people notice right away, the consumer falling over, for one
they do not, requests silently taking minutes instead of milliseconds, and
the second one is worse precisely because nothing pages anyone until a
customer complains.

- **Availability.** Strongly favoured for the consumer. The consumer is
  shielded from concurrency spikes it did not provision for, and a consumer
  outage does not propagate back to the producer as a failed call, because the
  producer's write to the queue already succeeded.
- **Latency.** Sacrificed, and this is the pattern's defining cost. Every
  message waits in the queue for a nonzero amount of time before a consumer
  picks it up, and that wait time grows without bound if the arrival rate ever
  exceeds the sustained drain rate for long enough (see dimension 11's
  treatment of Little's Law).
- **Cost.** Favoured. The consumer fleet can be sized for the average or a
  modestly generous percentile of load rather than the absolute peak, because
  the queue absorbs the difference between average and peak over time. This is
  the economic argument Microsoft's own catalog leads with, framed as helping
  control costs because you only need enough service instances to meet the
  requirements for an average load rather than the peak load ([Microsoft
  Learn, Queue-Based Load Leveling
  pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling),
  verified 2026-08-02).
- **Ordering.** Sacrificed, or at best made expensive to preserve. Once
  several consumers pull concurrently from the same queue, or a single
  consumer retries a message that failed and it lands behind newer arrivals,
  strict submission order is not guaranteed without a feature such as FIFO
  message groups, which itself caps throughput per group.
- **Operability.** Mixed. A queue is a genuinely useful thing to look at on a
  dashboard: backlog depth and oldest-message age are honest indicators of
  system health in a way that a synchronous call graph rarely is. But it is a
  new thing to monitor, a new failure mode class (poison messages, dead
  letters, visibility timeout tuning), and a new piece of durable state that
  must be provisioned, monitored, and paid for.
- **Consistency.** Sacrificed for anything that expects read-your-write
  behaviour. The producer's write returns before the work is done, so a client
  that immediately checks whether the work completed will usually find that it
  has not, and the system needs a separate mechanism, polling, a webhook, a
  status endpoint, to communicate completion.
- **Idempotency burden.** Shifted onto the consumer. Because most queue
  technologies deliver at least once, the consumer must tolerate processing
  the same message more than once without a different outcome, which is a real
  engineering cost that a purely synchronous design does not impose.

## 4. Applicability and non-applicability

Reach for Queue-Based Load Leveling when the following hold together, not in
isolation.

- The producer's demand is bursty, spiky, or unpredictable relative to a
  downstream service's sustainable throughput, and the downstream service is
  expensive, slow to scale, or has a hard external rate limit that cannot be
  raised: a payment processor, a legacy database, a third-party API.
- The work can be completed asynchronously from the caller's point of view:
  the caller needs "accepted" now and "done" later, not "done" now.
- The work is naturally idempotent, or can be made idempotent cheaply with an
  idempotency key or a deduplication check, because at-least-once delivery is
  the default across nearly every managed queue technology.
- Cost matters more than absolute end-to-end latency for this workload, so
  sizing consumer capacity for the average rather than the peak is a good
  trade.
- The team is willing to own the operational surface a queue adds: dead letter
  handling, message retention policy, poison message quarantine, monitoring
  for backlog age.

Do NOT reach for Queue-Based Load Leveling in the following cases. This list is
the more valuable half of this dimension, because the pattern is easy to reach
for reflexively once a team has adopted a message broker for one workload, and
it is wrong for most of what that broker gets asked to carry afterward.

- **The caller needs a synchronous, low-latency response.** A user-facing
  request such as "log me in" or "show me this page" cannot tolerate an
  unbounded queue wait, and putting it behind a queue converts a fast failure
  into a slow, silent one. Handle these with capacity planning, caching,
  request hedging, or, when overload is genuinely unavoidable, load shedding
  at the edge, which rejects excess work immediately rather than deferring it
  (see the load-shedding discussion at the end of this dimension and in
  dimension 12).
- **The work is not idempotent and cannot be made so cheaply.** A queue that
  delivers a "charge this card" message twice, with no deduplication and no
  idempotency key at the payment processor, will eventually double-charge a
  customer. If idempotency genuinely cannot be added, this pattern is
  disqualified regardless of how attractive the load-smoothing benefit looks.
- **The workload is steady and predictable.** A system that processes a
  constant, well-understood rate of work all day does not have a burst problem
  to solve, and adding a queue only adds latency, operational overhead, and
  cost for no offsetting benefit. Provision the consumer for the known rate
  instead.
- **Strict, cross-message ordering is a hard requirement and cannot be scoped
  to a partition key.** Multiple consumers, or even a single consumer with
  retries, will not preserve arrival order by default. FIFO features exist,
  but they trade away most of the pattern's throughput benefit per ordering
  group.
- **The downstream failure is capacity exhaustion at the shared resource the
  queue drains into, not merely a spike in request count.** Autoscaling the
  consumer fleet against queue depth without bounding the total downstream
  rate simply relocates the overload from the queue to whatever the consumer
  writes to next: a database connection pool, a rate-limited API. the
  Microsoft catalog states this directly. autoscaling without bounding
  consumers' total downstream rate only moves the overload to downstream
  dependencies ([Microsoft Learn, Queue-Based Load Leveling
  pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling),
  verified 2026-08-02). Pair the queue with a rate limiter or a bulkhead at
  the true bottleneck, not just at the queue's front door.
- **The producer's own request already carries a bounded, tight latency
  budget that the business genuinely cannot relax.** In that situation the
  honest answer is load shedding, not load leveling. Google's Site
  Reliability Engineering book describes load shedding as dropping some
  proportion of load as the server approaches overload conditions, with the
  goal of keeping the server from running out of memory, failing health
  checks, or serving with extremely high latency while still doing as much
  useful work as it can ([Google, *Site Reliability Engineering*, "Handling
  Overload"
  chapter](https://sre.google/sre-book/handling-overload/), verified
  2026-08-02). A queue defers overload into higher latency for everyone,
  shedding rejects a bounded fraction of it immediately so that the rest
  keeps its latency budget. Dimension 11 returns to this distinction with the
  Little's Law reasoning that makes it precise.

## 5. Structure

Four participants, named by the role each plays rather than by a generic
class name, because this pattern is as much an infrastructure and operational
shape as it is a code shape.

- **Producer (or Task).** The component that discovers work needs to happen
  and writes a message describing it. In the classical framing this is a web
  application instance, but it is equally a scheduled job, an event handler,
  or another service's own consumer that fans work out further.
- **Message.** The unit of durable, serialisable state describing one piece
  of work. It must carry everything the consumer needs, or a reference to
  where that data lives, because the consumer that eventually reads it may run
  long after, and on a different machine from, the producer that wrote it.
- **Queue (the Buffer).** A durable, ordered or best-effort-ordered channel
  that stores messages until a consumer retrieves them. This is the
  participant that does the actual leveling, converting an irregular arrival
  process into a stored backlog a consumer can drain at its own pace. It is
  also the sole participant that owns the trade-off in dimension 3: its
  current depth and its oldest unprocessed message age are the two numbers
  that describe how much latency the pattern is currently costing.
- **Consumer (or Service, or Worker Fleet).** One or more processes that pull
  messages from the queue, perform the work, and acknowledge or delete the
  message on success. The consumer fleet's size is the pattern's primary
  scaling lever, and in a fully realised implementation it scales
  automatically against a number derived from the queue, not against the
  arrival rate of producer requests directly, because the queue is precisely
  what decouples the two.

Relationships. Producer writes to Queue and returns, holding no reference to
any particular Consumer. Consumer polls or subscribes to Queue and holds no
reference to any particular Producer. Neither side is aware of the other's
identity, count, or health at any given moment, only of the Queue, which is
the entire point: a producer instance can be replaced, restarted, or scaled
independently of the consumer fleet, and vice versa.

## 6. ASCII structure diagram

```
        (bursty, unpredictable arrival rate)
   +----------+   +----------+   +----------+
   | Producer |   | Producer |   | Producer |
   |    A     |   |    B     |   |    C     |
   +----+-----+   +----+-----+   +----+-----+
        |               |               |
        | enqueue       | enqueue       | enqueue
        v               v               v
   +--------------------------------------------+
   |                    QUEUE                    |
   |  [msg7][msg6][msg5][msg4][msg3][msg2][msg1]  |
   |          (durable, ordered buffer)           |
   +--------------------------------------------+
        |               |               |
        | dequeue       | dequeue       | dequeue
        v               v               v
   +----------+   +----------+   +----------+
   | Consumer |   | Consumer |   | Consumer |
   |    1     |   |    2     |   |    3     |
   +----+-----+   +----+-----+   +----+-----+
        |               |               |
        +-------+-------+-------+-------+
                v
   +--------------------------------------------+
   |     Downstream dependency (fixed capacity)   |
   |     database, API, payment processor         |
   +--------------------------------------------+

   Consumer fleet size scales against queue depth / oldest-message age,
   never directly against producer request rate.
```

## 7. Dynamics

The runtime flow separates cleanly into two phases that run at their own,
independent pace, which is the whole mechanism made visible.

```
Producer               Queue                 Consumer          Downstream
   |                      |                       |                  |
   |-- enqueue(msg) ----->|                       |                  |
   |                      |-- persist durably --->|                  |
   |<-- ack (accepted) ---|                       |                  |
   |                      |                       |                  |
   | (producer returns to caller here, does not   |                  |
   |  wait for the work itself to finish)          |                  |
   |                      |                       |                  |
   .                      | <-- poll/receive ------|                  |
   .                      |-- deliver msg -------->|                  |
   .                      |   (becomes invisible   |                  |
   .                      |    for visibility      |                  |
   .                      |    timeout window)     |                  |
   .                      |                       |-- process ------>|
   .                      |                       |<-- result --------|
   .                      |                       |                  |
   .                      |<-- delete/ack ---------|                  |
   .                      |   (msg permanently     |                  |
   .                      |    removed on success) |                  |
   .                      |                       |                  |
   .                      | (on failure: message becomes visible      |
   .                      |  again after timeout, or moves to a       |
   .                      |  dead letter queue after N attempts)      |
```

The gap marked by the dots is the property that defines the pattern:
enqueue-to-ack for the producer is fast and independent of consumer state.
poll-to-process-to-delete for the consumer runs on its own schedule, gated
only by the consumer's own current capacity, and the elapsed wall-clock time
between a message's enqueue and its eventual delete is exactly the latency
tax described in dimension 3. When the queue is empty or nearly so, that tax
is negligible. When a burst has filled the queue faster than consumers can
drain it, that tax grows, message by message, and dimension 11 makes that
growth precise with Little's Law.

## 8. Implementation variants

**Managed cloud queue plus autoscaled compute.** The reference shape: a
managed durable queue, Amazon SQS, Azure Service Bus or Storage Queues, Google
Cloud Pub/Sub or Cloud Tasks, paired with a consumer fleet that an autoscaler
resizes against a queue-derived metric. This is the variant the Azure catalog
describes and the one most production deployments of this pattern actually
run.

**Serverless, poll-based invocation.** Instead of a long-running consumer
fleet, a function-as-a-service platform polls the queue on the platform's own
behalf and invokes a stateless function per batch of messages, scaling the
number of concurrent function invocations up and down automatically. AWS
Lambda's Amazon SQS event source mapping is the clearest example, batching
multiple messages per invocation and hiding them from other pollers for the
queue's visibility timeout while the function runs (see dimension 9). This
variant removes fleet management entirely at the cost of per-invocation
pricing and a platform-imposed concurrency ceiling.

**In-process bounded queue.** Within a single process or a small cluster, an
in-memory bounded queue, a Go buffered channel, a Java `BlockingQueue`, a
Python `queue.Queue`, plays the same structural role without external
infrastructure. This variant loses durability: a process crash drops
in-flight and queued work, so it suits workloads where losing a burst's tail
is acceptable, or where the queue is a local shock absorber in front of a
downstream call that is itself durable, rather than the system of record for
the work.

**Distributed task queue with a broker.** Celery over RabbitMQ or Redis is the
best-known open source instance of this shape in the Python community, and
equivalents exist across most language communities: Sidekiq over Redis in
Ruby, BullMQ over Redis in Node.js. The broker plays the Queue role, and a
pool of worker processes plays the Consumer role, typically started and
stopped by the operator or an external autoscaler rather than by the broker
itself.

**Priority and multi-queue leveling.** A single flat queue treats all
messages identically, which is often wrong. multiple named queues, or a
single queue with a priority attribute the consumer sorts on, let urgent work
skip ahead of bulk work even while both are being leveled against the same
downstream dependency. This adds real complexity around starvation of the
low-priority queue and is worth its cost only when message classes genuinely
have different urgency.

**Buffered event stream as a load leveler.** A log-structured stream such as
Apache Kafka or Amazon Kinesis is not a queue in the point-to-point sense
(each message is a competing-consumer delivery, see dimension 13), but a
partition consumed by a single reader group behaves as a durable, ordered
buffer with the same leveling effect, and consumer lag, the stream analogue
of queue depth, is monitored the same way. Teams already running a stream for
other reasons often reuse it for load leveling rather than standing up a
second broker.

## 9. Known production uses

**Azure Functions with a Service Bus queue trigger, target-based scaling.**
Microsoft's own reference implementation of this pattern has an Azure
Functions app read messages from a Service Bus queue and perform reads and
writes to a data store that would otherwise be overwhelmed by concurrent web
app instances, with the Functions runtime scaling worker instances based on
the Service Bus backlog through target-based scaling, within configured
scaling bounds. Microsoft Learn, Azure Architecture Center, "Queue-Based Load
Leveling pattern", example
section, https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling
verified 2026-08-02.

**Amazon EC2 Auto Scaling, backlog-per-instance target tracking against
Amazon SQS.** AWS's documented pattern for scaling a worker fleet against SQS
computes a *backlog per instance* metric, the queue's `ApproximateNumberOfMessages`
divided by the Auto Scaling group's in-service instance count, and an
*acceptable backlog per instance* target derived from the tolerable latency
divided by the average per-message processing time, explicitly because the
raw `ApproximateNumberOfMessagesVisible` metric does not scale proportionally
to fleet size on its own. Amazon Web Services, EC2 Auto Scaling User Guide,
"Scaling policy based on Amazon SQS", https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-using-sqs-queue.html
verified 2026-08-02.

**AWS Lambda, Amazon SQS event source mapping.** Lambda polls a standard or
FIFO SQS queue on the caller's behalf, invokes the function synchronously
with a batch of messages, hides those messages from other pollers for the
queue's visibility timeout, and deletes them from the queue only once the
function successfully processes the batch, with an optional provisioned mode
that scales dedicated pollers up to 100,000 concurrent invocations for
strict-latency workloads such as market data feeds. Amazon Web Services,
AWS Lambda Developer Guide, "Using Lambda with Amazon SQS", https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
verified 2026-08-02.

**Celery, distributed Python task queue over RabbitMQ or Redis.** Celery
documents itself as a task queue in which a client adds a message to the
queue, a broker mediates between clients and workers, and dedicated worker
processes constantly monitor task queues for new work, supporting multiple
workers and brokers for high availability and horizontal scaling. Celery
Project, Celery Documentation, "Task Queues" introduction, https://docs.celeryq.dev/en/stable/getting-started/introduction.html
verified 2026-08-02.

**KEDA, Kubernetes Event-driven Autoscaling, Amazon SQS scaler.** KEDA
computes a queue's in-flight message count as `ApproximateNumberOfMessages`
plus `ApproximateNumberOfMessagesNotVisible`, divides it by a configured
`queueLength` target, and scales the number of Kubernetes pod replicas
accordingly, for example scaling to three replicas when thirty messages are
outstanding against a `queueLength` of ten. KEDA Authors, KEDA Documentation,
"AWS SQS Queue trigger", https://keda.sh/docs/2.16/scalers/aws-sqs/
verified 2026-08-02.

## 10. Consequences

Positive.

- Downstream services are protected from concurrency spikes they were never
  sized for, because the queue absorbs the excess rather than passing it
  through as a wave of simultaneous calls.
- Consumer capacity can be sized to average or near-average demand rather
  than worst-case peak demand, which is a direct infrastructure cost saving,
  stated explicitly by the Microsoft catalog as helping control costs.
- Producer availability improves for the duration of a consumer-side outage
  or slowdown, because a producer's write to a durable queue succeeds
  independently of whether the consumer fleet is currently healthy.
- The queue becomes a natural, honest place to observe system health.
  backlog depth and oldest-message age are truthful indicators in a way that
  request-level success metrics on an overloaded synchronous system are not,
  because a synchronous system under load often still reports fast responses
  right up until the moment it falls over.
- Retries, dead lettering, and poison message quarantine can be built once,
  at the queue boundary, rather than reimplemented per call site throughout
  the producer's code.

Negative.

- End-to-end latency for a unit of work becomes variable and, under
  sustained overload, unbounded, which is the central cost described in
  dimension 3 and made mathematically precise in dimension 11.
- The system now has a durable piece of infrastructure state, the queue
  itself, that must be provisioned, monitored, secured, and paid for, and
  whose own outage or misconfiguration (a full queue, a lost dead letter
  queue, an expired retention policy) becomes a new class of production
  incident that did not exist before.
- At-least-once delivery, the default for nearly every managed queue, forces
  every consumer to be written as idempotent, which is a real design and
  testing cost, not a minor caveat.
- Strict message ordering is difficult and expensive to guarantee once more
  than one consumer, or one consumer with retries, is involved.
- Autoscaling a consumer fleet against queue depth can simply relocate an
  overload problem to whatever the consumers write to next, unless that
  downstream dependency's own capacity is independently bounded.

## 11. Failure modes and misuse

**Unbounded queue growth under sustained overload.** Symptom. Backlog depth
climbs steadily for hours, oldest-message age climbs in lockstep, and nothing
else in the system looks obviously broken: no errors, no crashed instances,
just a slowly worsening delay that eventually turns into a support ticket
about "my order from yesterday still hasn't processed". Cause. The average
producer arrival rate has quietly exceeded the average consumer drain rate for
long enough that the queue's stored backlog is growing without bound, and
nothing in the system is scaling the consumer fleet, or bounding the
producer, to correct it. This is where Little's Law earns its place in this
entry, stated exactly as the theorem, not paraphrased: **L = lambda W**, where
L is the long-run average number of items in a stable system, lambda is the
average arrival rate, and W is the average time each item spends in the
system, a relationship John Little proved formally in 1961 in the journal
*Operations Research* after it had circulated as an unproven assumption since
a 1954 paper (Wikipedia contributors, "Little's law",
https://en.wikipedia.org/wiki/Little%27s_law verified 2026-08-02, drawing on
Little's original 1961 proof). The law holds only for a stable queue, one
where the long-run average arrival rate does not exceed the long-run average
service rate. When arrival rate persistently exceeds drain rate, the queue is
not stable, L grows without bound over time, and by the same relationship W,
the wait each message experiences, grows without bound alongside it. This is
engineering judgement built directly on that theorem, not a separate citable
claim: once a queue is observed to be unstable rather than merely deep, the
correct response is not "wait, it will catch up", it is "scale the consumer,
or shed load at the producer, because the arithmetic guarantees it will not
catch up on its own". Fix. Alert on sustained backlog growth and
oldest-message age, not merely on absolute depth, and pair the queue with
either consumer autoscaling that is fast enough to restore lambda at or below
the service rate, or a producer-side rate limit, or explicit load shedding
when the queue is not the right tool for this particular burst (see
dimension 4's non-applicability list and dimension 12).

**Queue depth alone as the autoscaling signal, ignored age.** Symptom. The
consumer fleet scales up correctly during a genuine burst, but during a
different incident, a small trickle of slow, expensive messages, backlog
depth stays low, perhaps five or ten messages, so the autoscaler never fires,
while those five or ten messages individually sit unprocessed for twenty
minutes each. Cause. Depth alone is a count of items, not a measure of
whether items are aging. a queue can hold a small, stable number of messages
that are each taking far too long to drain, and a depth-only autoscaling
policy cannot tell the difference, because five slow messages and five
fast ones look identical on a depth chart. This is exactly the reasoning AWS
gives for why raw `ApproximateNumberOfMessagesVisible` is the wrong metric to
target directly, because the number of messages in the queue does not
solely define the number of instances needed, since instance count also
depends on per-message processing time and tolerable latency (Amazon Web
Services, EC2 Auto Scaling User Guide, "Scaling policy based on Amazon SQS",
https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-using-sqs-queue.html
verified 2026-08-02). Fix. Track oldest-message age as a first-class number
alongside depth, and where the platform supports it, scale on a derived
metric such as backlog-per-instance against an explicit acceptable-latency
target, exactly as AWS's own worked example computes it, rather than on raw
depth.

**The idempotency gap.** Symptom. A customer is charged twice for one order,
or a report is emailed twice, or a downstream record is duplicated, and the
incident review finds no code path that should have produced two writes.
Cause. The queue redelivered the message, most commonly because the consumer
took longer to process it than the queue's visibility timeout allowed, so the
message became visible again and a second worker picked it up while the
first was still finishing, or because a network blip caused the delete
acknowledgement to fail to reach the broker after the work had already
completed. At-least-once delivery is the default, explicitly, across the
platforms cited in dimension 9. AWS's Lambda documentation states this
plainly, that event source mappings process each event at least once and
duplicate processing can occur, and strongly recommends idempotent function
code (Amazon Web Services, AWS Lambda Developer Guide, "Using Lambda with
Amazon SQS", https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
verified 2026-08-02). Fix. Design consumers around an idempotency key, a
deduplication table keyed on message ID with a short retention window, or a
downstream operation that is naturally idempotent, such as an upsert keyed on
a business identifier rather than an insert.

**Poison message loop.** Symptom. A single message is processed, fails, becomes
visible again after the timeout, is processed, fails again, in a cycle that
consumes worker capacity indefinitely and, on some platforms, blocks other
messages behind it in the same partition or ordering group. Cause. The
message contains malformed data, references a resource that no longer
exists, or triggers a deterministic bug, so retrying it never succeeds, and no
maximum-attempt policy exists to remove it from the healthy path. Fix. Configure
a dead letter queue with a bounded maximum receive count, route messages that
exceed it there automatically, and alert on dead letter queue depth so an
operator investigates and either fixes the underlying cause or discards the
message deliberately, rather than letting it cycle silently forever.

**Downstream overload disguised as queue health.** Symptom. The queue itself
looks perfectly healthy, low depth, low age, consumers scaled appropriately,
while the database or third-party API the consumers write to is timing out
and erroring under load. Cause. The consumer fleet was autoscaled purely
against queue depth with no cap tied to the true bottleneck's own capacity,
so scaling the fleet simply moved the point of overload one hop downstream,
exactly the failure the Microsoft catalog warns about directly (Microsoft
Learn, Queue-Based Load Leveling pattern, https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling
verified 2026-08-02). Fix. Bound consumer concurrency against the downstream
dependency's known sustainable rate, using a rate limiter or a bulkhead
(cross reference dimension 13), not only against the queue's backlog, so the
leveling effect is enforced at both ends of the pipeline.

**Ordering assumed but not guaranteed.** Symptom. An update message arrives
and applies before the create message it logically depends on, or a
cancellation is processed before the order it cancels, producing an
inconsistent downstream state that a synchronous system would never have
allowed. Cause. Multiple consumers drained the queue concurrently, or a
retried message was redelivered out of its original sequence relative to
newer messages, and the workload's correctness silently depended on FIFO
ordering that the chosen queue technology, or the chosen consumer
concurrency, did not actually provide. Fix. Use a FIFO queue feature with
message group IDs scoped to the entity that requires ordering, accepting the
per-group throughput ceiling that comes with it, or design the consumer to
be order-independent by carrying a version or sequence number in the message
and discarding stale updates on arrival.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Queue-Based Load Leveling | Rate Limiting at the producer | Load Shedding at the edge | Bulkhead (resource isolation) | Direct synchronous call, fixed fleet |
|---|---|---|---|---|---|
| Protects downstream from bursts | Strong. Excess work is stored, not delivered | Strong. Excess requests are rejected before they start | Strong. Excess requests are dropped before they start | Partial. Isolates one caller's failures, does not smooth its own volume | None. Full burst reaches the downstream directly |
| End-to-end latency under burst | Grows, potentially unbounded, per Little's Law | Stays low for accepted requests, rejected requests fail fast | Stays low for accepted requests, rejected requests fail immediately | Stays low if isolation holds, degrades if the pool itself saturates | Grows or fails as the fixed fleet saturates |
| Caller experience under burst | Accepted now, result deferred | Some callers get an explicit rejection now | Some callers get an explicit rejection now | Callers on other pools unaffected, this pool's callers see saturation | All callers experience growing latency together |
| Suits synchronous, low-latency callers | Poor. Adds deferred completion by design | Good. Fast accept or fast reject | Good. Fast accept or fast reject | Good, within the isolated pool's own capacity | Only while capacity holds |
| Cost of consumer capacity | Low. Sized for average demand | Same as unshielded, sized for accepted peak | Same as unshielded, sized for accepted peak | Same as unshielded, per isolated pool | High. Sized for absolute peak to avoid failure |
| New durable infrastructure required | Yes, a queue or broker | No, typically an in-process or edge counter | No, typically an in-process or edge counter | No, typically thread pools or semaphores | No |
| Ordering guarantees | Weak by default, expensive to strengthen | Not applicable, requests are synchronous | Not applicable, requests are synchronous | Not applicable | Strong, requests complete in call order naturally |
| Idempotency requirement on the receiver | Mandatory, at-least-once delivery is the norm | Not required, request either succeeds once or is rejected | Not required, request either succeeds once or is rejected | Not required | Not required |
| Best combined with | Rate limiting or a bulkhead at the true downstream bottleneck | Queue-based leveling for the accepted subset | A queue for the accepted subset when async is acceptable | Queue-based leveling per isolated pool | Autoscaling, which only pushes the ceiling higher, never removes it |

Reading of the table. Queue-Based Load Leveling and load shedding are not
competitors so much as two answers to the same overload question aimed at
different callers: leveling suits work the caller can wait for, shedding
suits work the caller cannot. A mature system typically runs both: queue the
work that tolerates deferred completion, shed or rate-limit the work that
does not, and never let queue-depth-driven autoscaling alone stand in for a
hard cap on the downstream dependency's true sustainable rate, which is the
bulkhead's job.

## 13. Related and incompatible patterns

- **Rate Limiting.** Complements rather than substitutes. Rate limiting caps
  the rate at which work is *admitted* into the system in the first place,
  typically synchronously and at the producer's edge. Queue-Based Load
  Leveling accepts a burst of already-admitted work and smooths its delivery
  to a downstream consumer over time. A well-designed pipeline often uses
  rate limiting to reject or defer clearly excessive volume before it ever
  reaches the queue, then uses the queue to smooth the remainder.
- **Bulkhead.** Complements directly. A bulkhead caps how much of a shared
  resource, a thread pool, a connection pool, a downstream rate limit, one
  workload is allowed to consume, which is exactly the missing piece in the
  downstream-overload failure mode in dimension 11. Pairing a queue's
  consumer fleet with a bulkhead on the true bottleneck is how autoscaling
  the fleet against backlog stops relocating overload rather than absorbing
  it.
- **Circuit Breaker.** Composes at the consumer's outbound call. If the
  downstream dependency a consumer calls starts failing, a circuit breaker on
  that call stops the consumer from hammering an already-struggling
  dependency with retries drawn straight from the queue's backlog, which
  would otherwise turn a queue-fed retry storm into the exact overload the
  queue was meant to prevent.
- **Retry.** Frequently layered on top of message redelivery. Most queue
  technologies already provide message-level retry through visibility
  timeouts and receive counts, described in dimension 7 and dimension 11, so
  an additional application-level retry inside a consumer should be scoped
  carefully to avoid stacking retry-on-retry delays that make a poison
  message's failure loop even slower to detect.
- **Publisher-Subscriber.** A close cousin, and easy to confuse with this
  pattern. Publisher-Subscriber fans one message out to every interested
  subscriber, broadcast semantics. Queue-Based Load Leveling, built on the
  Point-to-Point Channel pattern from Hohpe and Woolf, guarantees exactly one
  consumer processes any given message, competing-consumer semantics
  (Enterprise Integration Patterns website, "Point-to-Point Channel",
  https://www.enterpriseintegrationpatterns.com/patterns/messaging/PointToPointChannel.html
  verified 2026-08-02, describing the same guarantee, that a Point-to-Point
  Channel limits delivery of any given message to exactly one receiver even
  when the channel has multiple receivers). A system can use both together:
  a topic that fans a work item out to several independently load-leveled
  queues, one per downstream concern.
- **Dead Letter Queue.** A required companion, not an optional add-on, once
  this pattern is in production: it is the mechanism that stops the poison
  message failure mode in dimension 11 from consuming worker capacity
  indefinitely.
- **CQRS.** Frequently paired at a larger architectural scale: the command
  side of a CQRS system commonly writes commands onto a leveled queue for
  asynchronous processing, decoupling the write path's acceptance latency
  from its processing latency, while the query side reads from a separately
  maintained, eventually consistent read model.
- **Synchronous Request-Response (incompatible in intent, not in
  coexistence).** This is not a named pattern in this catalog so much as the
  default shape queue-based leveling replaces for a given call. The two are
  not incompatible as architectures, most systems run both for different
  endpoints, but they are incompatible as a promise to a single caller: a
  caller cannot be told simultaneously "your response is ready now" and
  "your work has been queued for later processing" about the same operation.
  Choosing this pattern for an endpoint is an explicit decision to give up
  the synchronous promise for that endpoint, worth stating here because it is
  the single most common design mistake this pattern's misuse produces:
  applying it to an endpoint whose callers actually needed the synchronous
  answer.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently calls a downstream
dependency synchronously and directly.

1. Identify the call site where a producer, typically a request handler,
   invokes the downstream dependency synchronously and confirm the caller
   genuinely does not need the result before it can respond, only an
   acknowledgement that the work will happen. If the caller does need the
   result, stop here, this pattern is the wrong fix, see dimension 4.
2. Introduce a durable queue and change the call site to serialise the
   necessary inputs into a message and enqueue it, returning an
   acknowledgement to the original caller instead of the downstream result.
   Keep the old synchronous call path available behind a flag during the
   transition.
3. Build a consumer that dequeues a message, performs the previously
   synchronous call, and acknowledges the message on success. Run it as a
   single instance first, deliberately under-scaled, specifically to observe
   backlog behaviour under real traffic before trusting it with production
   load.
4. Add idempotency to the downstream operation, an idempotency key, a
   deduplication check, or a natural upsert, before removing the old
   synchronous path, because at-least-once delivery starts the moment the
   consumer goes live.
5. Add the dead letter queue and a bounded maximum receive count before
   removing the old synchronous path, so a malformed message during the
   transition cannot loop indefinitely and mask other problems.
6. Wire the observability numbers from dimension 16, backlog depth and
   oldest-message age at minimum, and set an alert threshold before removing
   the fallback, so a stability regression is visible immediately rather than
   discovered from a support ticket.
7. Scale the consumer fleet, manually at first, then via an autoscaling
   policy against backlog-per-instance as described in dimension 9, and only
   then remove the old synchronous fallback path.

Removing the pattern when it stops earning its place. The clearest signal is a
workload whose arrival rate has become steady and well below the consumer
fleet's provisioned capacity, so the queue is nearly always empty and is
adding pure latency and operational overhead for no smoothing benefit.

1. Confirm backlog depth has stayed near zero and oldest-message age has
   stayed near the minimum for a representative period, including known peak
   times, before concluding the burst problem this pattern solved no longer
   exists.
2. Reintroduce, or keep, a synchronous call path behind a flag, calling the
   downstream dependency directly.
3. Shift traffic to the synchronous path gradually, monitoring the
   downstream dependency's own error rate and latency closely, since the
   queue was, among other things, quietly protecting it.
4. Once fully shifted and stable, decommission the consumer fleet and the
   queue, but retain the dead letter queue's contents and the queue's access
   logs for the standard retention period, in case an in-flight message from
   the old path needs investigation after the cutover.

## 15. Testing and verification

Easier because of the pattern.

- The producer and the consumer can be tested in complete isolation from
  each other, because the queue is the only contract between them: a
  producer test asserts the correct message shape was enqueued, a consumer
  test asserts the correct behaviour given a message, and neither test needs
  the other component running.
- Load and burst behaviour becomes directly testable by pre-loading a test
  queue with a known number of messages and observing drain rate, backlog
  age, and downstream call rate, without needing to generate the original
  bursty traffic pattern that would have produced that backlog in
  production.
- Failure injection is straightforward and safe: a test can push a malformed
  message onto the queue and assert it reaches the dead letter queue within
  the configured receive count, without risking a real downstream side
  effect from a genuinely bad payload.

Harder because of the pattern.

- End-to-end correctness now spans an asynchronous boundary, so a test that
  merely asserts "the message was enqueued" is not a complete test of the
  feature: it must also assert the consumer eventually processed it, which
  usually means the test suite needs a poll-with-timeout assertion rather
  than a synchronous return value to check.
- Idempotency is a property that only shows up under duplicate delivery, which
  does not happen reliably in a single, non-adversarial test run, so it must
  be tested deliberately by delivering the same message twice and asserting
  identical downstream state, not left to be caught incidentally.
- Ordering bugs, described in dimension 11, are often invisible in a
  single-consumer test environment and only appear once real concurrency is
  introduced, so a test suite that runs one consumer instance can pass while
  the production fleet, running several, has an ordering defect.

Techniques that apply.

- **Contract test on the message schema.** Both producer and consumer test
  suites validate their messages against one shared schema definition, so a
  producer change that would silently break every consumer is caught at
  build time rather than discovered by a poison message in production.
- **Idempotency replay test.** Deliver the identical message to the consumer
  twice, or N times, in a test, and assert the observable downstream state
  is identical to delivering it once. This is the single highest-value test
  this pattern adds that a purely synchronous design would not need.
- **Delay and outage injection test.** In a staging environment, deliberately
  hold a fraction of messages past their normal processing time, or force a
  temporary consumer outage, and assert the backlog grows and later drains
  as expected, and that the alerting from dimension 16 actually fires during
  the growth window, not only after the fact.
- **Dead letter path test.** Enqueue a message engineered to fail
  deterministically, N times, where N is the configured maximum receive
  count, and assert it lands in the dead letter queue rather than cycling
  indefinitely or being silently dropped.

## 16. Observability signals

Everything about this pattern's health is visible at the queue, which is
precisely why it is a better operability story than a hidden, ad hoc buffer
inside a load balancer's connection backlog. This dimension is largely
practice and judgement, drawn from the failure modes in dimension 11.

What to record.

- **Queue depth**, the count of messages currently available for retrieval.
  The primary, most commonly monitored number, and, per dimension 11, an
  insufficient one on its own.
- **Oldest-message age**, the elapsed time since the longest-waiting message
  was enqueued. This is the number that catches the "low depth but stale
  messages" failure mode dimension 11 describes, and it is the value that
  most directly answers "how much latency is this pattern currently costing
  a real caller".
- **Enqueue rate and dequeue rate**, both labelled per queue, ideally
  plotted on the same chart so a gap opening between the two, arrival
  outpacing drain, is visible as soon as it begins rather than only after it
  has compounded into a large backlog.
- **In-flight message count**, messages currently delivered to a consumer
  but not yet acknowledged, which distinguishes "waiting to be picked up"
  from "currently being processed", and a growing in-flight count with a flat
  or shrinking available-depth count usually points at slow or stuck
  consumers rather than an arrival-side burst.
- **Dead letter queue depth**, which should sit at or near zero in a healthy
  system, and any nonzero, growing value warrants investigation, per the
  poison message failure mode.
- **Receive count distribution**, how many attempts messages typically take
  to succeed, which surfaces a rising rate of transient failures before it
  turns into an actual outage.
- **Consumer fleet size over time**, alongside the metric it is scaled
  against, so an operator can confirm the autoscaling policy is actually
  responding to backlog rather than silently stalled at a floor or ceiling.

A healthy instance on a dashboard. queue depth tracks the expected daily or
event-driven pattern of the workload and returns to a low baseline between
bursts. oldest-message age stays within the latency budget the team has
committed to, even during a burst, because the consumer fleet scales fast
enough to keep pace. enqueue and dequeue rate lines sit close together,
spreading apart briefly during a burst and coming back together afterward
rather than drifting apart indefinitely. dead letter queue depth is flat at
or near zero.

A failing instance. oldest-message age climbs steadily with no
corresponding climb in queue depth, pointing at a small number of stuck or
very slow messages rather than a volume problem, which is the depth-without-age
failure mode from dimension 11. Or depth and age both climb together and keep
climbing well past the point where a burst should have subsided, which is the
unstable-queue signature Little's Law predicts, and the fix is consumer
capacity or producer-side shedding, not patience. Or dead letter queue depth
starts climbing, which is a poison message loop or a genuine, recurring data
quality problem upstream. Or consumer fleet size is pinned at its configured
maximum while backlog keeps growing, which means the autoscaling ceiling
itself, not the policy, is now the bottleneck and needs to be raised or
paired with load shedding at the producer.

## 17. Security and privacy implications

The pattern introduces genuine, non-trivial security exposure, because it
adds a piece of durable storage, often reachable over a network API, that
holds the payload of every unit of work the system defers. Saying otherwise
would understate a real concern.

**Message content at rest and in transit.** A queue is, by construction, a
store of application data that persists for some retention window, and that
data is exactly as sensitive as whatever the message carries. If a message
carries personal data, payment details, or any other regulated category,
that data is now sitting in a broker's storage, potentially for hours or
days, subject to the broker's own encryption-at-rest and encryption-in-transit
guarantees, access controls, and audit logging, which may be weaker or
differently scoped than the guarantees the primary application database
provides. This is a judgement call teams should make explicitly: encrypt
sensitive fields at the application layer before enqueueing, so the broker
never sees plaintext, or pass a reference to the sensitive data, an object
storage key or a database row identifier, rather than the data itself.

**Access control on the queue.** Whoever can write to the queue can inject
work the consumer will execute with the consumer's own privileges, and
whoever can read from the queue can see, and in some broker configurations
alter or delete, every pending unit of work in the system, which for a
payment or fulfilment workload is itself sensitive metadata even before
considering message content. Scope producer write permissions and consumer
read permissions as narrowly as the platform allows, per queue rather than
per account, and treat overly broad queue access as equivalent in severity
to overly broad database access, because functionally it often is one.

**Denial of service through queue flooding.** Because enqueueing is
deliberately cheap and fast, exactly the property that makes producer
availability good under this pattern, an attacker who can reach the enqueue
path can flood the queue with a very large number of low-cost writes,
growing backlog and oldest-message age for legitimate work far faster than
the consumer fleet can respond, and, depending on the broker's pricing
model, driving cost directly. This is engineering judgement, not a sourced
claim, drawn from the mechanism itself: rate limit the enqueue path (cross
reference dimension 13), authenticate producers where the enqueue path is
externally reachable, and set a maximum queue size or a cost alert so an
attack is bounded and visible rather than open ended.

**Replay and duplicate-processing side effects.** Because at-least-once
delivery is the norm, and dimension 11 covers the correctness implications of
that directly, the security-relevant version of the same issue is that a
captured or replayed message, whether by an attacker or by an ordinary broker
redelivery, can trigger a real-world side effect a second time: a duplicate
charge, a duplicate shipment, a duplicate notification. The idempotency
mechanisms dimension 11's fix already recommends for correctness are also,
directly, the mitigation for this security-adjacent replay risk, so this is
one instance where the reliability fix and the security fix are the same
piece of engineering work.

On privacy specifically, beyond the message-content concern above, one
practical caveat from dimension 16's observability advice: logging message
identifiers, sender identifiers, or payload summaries for monitoring
purposes can itself constitute personal data handling if those identifiers
are traceable to an individual, and should be governed by the same
retention and access rules the rest of the system applies to identifying
data, rather than treated as exempt because it lives in operational
telemetry rather than the primary data store.

## 18. References

1. Alex Homer, John Sharp, Larry Brader, Masashi Narumoto, Trent Swanson.
   *Cloud Design Patterns. Prescriptive Architecture Guidance for Cloud
   Applications*. Microsoft patterns & practices, 2014. ISBN
   978-1-62114-036-8. Source of the pattern's origin and its economic
   framing.
2. Microsoft Learn, Azure Architecture Center. "Queue-Based Load Leveling
   pattern".
   https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling
   Verified 2026-08-02. Source for the current pattern definition, the
   autoscaling-without-bounding-downstream-rate warning, and the Azure
   Functions and Service Bus production example.
3. Amazon Web Services. *Amazon EC2 Auto Scaling User Guide*. "Scaling
   policy based on Amazon SQS".
   https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-using-sqs-queue.html
   Verified 2026-08-02. Source for the backlog-per-instance and acceptable-
   backlog-per-instance formulas, and the reason raw queue depth is an
   insufficient scaling number.
4. Amazon Web Services. *AWS Lambda Developer Guide*. "Using Lambda with
   Amazon SQS".
   https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
   Verified 2026-08-02. Source for the SQS event source mapping production
   use, at-least-once delivery, and provisioned mode scaling figures.
5. Celery Project. *Celery Documentation*. "Task Queues" introduction.
   https://docs.celeryq.dev/en/stable/getting-started/introduction.html
   Verified 2026-08-02. Source for the Celery production use and the
   broker-mediated producer and worker description.
6. KEDA Authors. *KEDA Documentation*. "AWS SQS Queue trigger".
   https://keda.sh/docs/2.16/scalers/aws-sqs/
   Verified 2026-08-02. Source for the KEDA queue-length scaling formula and
   worked example.
7. Wikipedia contributors. "Little's law".
   https://en.wikipedia.org/wiki/Little%27s_law
   Verified 2026-08-02. Source for the formula L = lambda W, the stability
   precondition, and the 1961 proof by John Little in Operations Research.
8. Google. *Site Reliability Engineering*. "Handling Overload" chapter.
   https://sre.google/sre-book/handling-overload/
   Verified 2026-08-02. Source for the load shedding definition and its
   distinction from deferred, queued work.
9. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*. Addison-Wesley, 2003. ISBN
   0-321-20068-3. Source for the Point-to-Point Channel and Competing
   Consumers ancestry this pattern builds on.
10. Enterprise Integration Patterns website. "Point-to-Point Channel".
    https://www.enterpriseintegrationpatterns.com/patterns/messaging/PointToPointChannel.html
    Verified 2026-08-02. Source for the exact competing-consumer delivery
    guarantee referenced in dimension 13.

## Code examples

Three languages, each chosen because the pattern's mechanism, a bounded
buffer decoupling a bursty producer from a fixed-rate consumer, has a
different natural expression in each. Go is included because its buffered
channel IS a queue-based load leveler as a first-class language primitive,
which makes the pattern unusually explicit. TypeScript shows the managed
cloud queue shape with an async worker pool honouring a concurrency limit
independent of arrival rate. Python shows a threaded producer-consumer
simulation that also computes the backlog-per-instance metric from dimension
9, tying the code directly back to the AWS worked example cited there. Java
and Rust are omitted from this entry, not because the pattern does not
translate, `java.util.concurrent.BlockingQueue` and Rust's
`std::sync::mpsc` or `tokio::sync::mpsc` are entirely idiomatic hosts for it,
but because Go's channel already demonstrates the same bounded-buffer
mechanism as a language primitive and a second demonstration would not add a
materially different lesson.

### Go

A worker pool draining a bounded, buffered channel at a fixed rate while
producers burst far faster than the workers can keep up, demonstrating
backpressure, backlog growth, and drain once the burst ends.

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type job struct {
	id int
}

func main() {
	const queueCapacity = 20
	const workerCount = 3
	const processingDelay = 15 * time.Millisecond

	queue := make(chan job, queueCapacity)
	var processed sync.WaitGroup
	var wg sync.WaitGroup

	for w := 0; w < workerCount; w++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := range queue {
				time.Sleep(processingDelay)
				processed.Done()
				_ = j
			}
		}(w)
	}

	const burstSize = 60
	processed.Add(burstSize)
	start := time.Now()
	go func() {
		for i := 0; i < burstSize; i++ {
			queue <- job{id: i}
			fmt.Printf("enqueued job %d, depth now %d\n", i, len(queue))
		}
		close(queue)
	}()

	processed.Wait()
	wg.Wait()
	fmt.Printf("drained %d jobs with %d workers in %v\n", burstSize, workerCount, time.Since(start))
}
```

### TypeScript

An in-memory bounded async queue standing in for a managed cloud queue, with
a producer that bursts and a fixed-size worker pool that drains at its own
pace, reporting depth and oldest-message age the way dimension 16 describes.

```typescript
type Message = { id: number; enqueuedAt: number };

class LoadLevelingQueue {
  private items: Message[] = [];
  private waiters: Array<(m: Message) => void> = [];

  enqueue(id: number): void {
    const msg: Message = { id, enqueuedAt: Date.now() };
    const waiter = this.waiters.shift();
    if (waiter) {
      waiter(msg);
    } else {
      this.items.push(msg);
    }
  }

  dequeue(): Promise<Message> {
    const msg = this.items.shift();
    if (msg) return Promise.resolve(msg);
    return new Promise((resolve) => this.waiters.push(resolve));
  }

  depth(): number {
    return this.items.length;
  }

  oldestAgeMs(): number {
    if (this.items.length === 0) return 0;
    return Date.now() - this.items[0].enqueuedAt;
  }
}

async function worker(id: number, queue: LoadLevelingQueue, processMs: number): Promise<void> {
  for (let i = 0; i < 10; i++) {
    const msg = await queue.dequeue();
    await new Promise((r) => setTimeout(r, processMs));
    console.log(`worker ${id} finished message ${msg.id}, waited ${Date.now() - msg.enqueuedAt}ms`);
  }
}

async function main(): Promise<void> {
  const queue = new LoadLevelingQueue();
  const workerCount = 3;
  const workers = Array.from({ length: workerCount }, (_, i) => worker(i, queue, 15));

  for (let i = 0; i < 30; i++) {
    queue.enqueue(i);
  }
  console.log(`burst enqueued, depth=${queue.depth()}, oldest age=${queue.oldestAgeMs()}ms`);

  await Promise.all(workers);
}

main();
```

### Python

A threaded producer-consumer simulation using the standard library `queue`
module, computing the backlog-per-instance metric exactly as AWS's worked
example does it in dimension 9: backlog divided by in-service consumer
count.

```python
import queue
import threading
import time

work_queue: "queue.Queue[int]" = queue.Queue()
processed_count = 0
lock = threading.Lock()
CONSUMER_COUNT = 4
PROCESSING_SECONDS = 0.01


def consumer(worker_id: int) -> None:
    global processed_count
    while True:
        item = work_queue.get()
        if item is None:
            work_queue.task_done()
            break
        time.sleep(PROCESSING_SECONDS)
        with lock:
            processed_count += 1
        work_queue.task_done()


def backlog_per_instance(depth: int, instances: int) -> float:
    return depth / instances if instances else float("inf")


def main() -> None:
    workers = [threading.Thread(target=consumer, args=(i,)) for i in range(CONSUMER_COUNT)]
    for w in workers:
        w.start()

    burst_size = 200
    for i in range(burst_size):
        work_queue.put(i)

    depth_snapshot = work_queue.qsize()
    print(
        f"burst enqueued: {burst_size} messages, "
        f"depth={depth_snapshot}, "
        f"backlog per instance={backlog_per_instance(depth_snapshot, CONSUMER_COUNT):.1f}"
    )

    work_queue.join()

    for _ in workers:
        work_queue.put(None)
    for w in workers:
        w.join()

    print(f"processed {processed_count} of {burst_size} messages with {CONSUMER_COUNT} consumers")


if __name__ == "__main__":
    main()
```
