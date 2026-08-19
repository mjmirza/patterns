---
name: Work Queue
slug: work-queue
family: 09-concurrency
category: Concurrency
aliases: [Task Queue, Job Queue, Message Queue Worker Pool]
first_described: "Hohpe, Woolf 2003 (Competing Consumers); popularized as a decoupled job system by RabbitMQ, Celery, Sidekiq documentation, mid-2000s to 2010s"
maturity: canonical
related: [producer-consumer, thread-pool, leader-followers, pipeline-parallelism, future-promise, competing-consumers]
incompatible_with: []
verified: 2026-08-14
---

# Work Queue

## 1. Name, aliases, and lineage

The canonical name in this catalog is Work Queue. The same idea is called Task
Queue in Python and JavaScript ecosystems (Celery, Bull, BullMQ), Job Queue in
Ruby and PHP ecosystems (Sidekiq, Laravel Queues, Resque), and Message Queue
Worker Pool when the emphasis is on the transport rather than the work unit.
Enterprise integration literature calls the same shape Competing Consumers.
Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, the
Competing Consumers pattern, chapter on Message Endpoints. Hohpe and Woolf
describe the problem as a single channel with multiple consumers competing to
process each message, exactly the arrangement this entry documents.

The pattern is not attributed to a single named inventor the way Gang of Four
patterns are. It is a direct descendant of the classical Producer-Consumer
pattern (see the `producer-consumer` entry in this catalog) specialised for a
distributed or multi-process setting. Where Producer-Consumer usually describes
an in-process bounded buffer shared by threads, Work Queue describes the same
shape stretched across process and machine boundaries, backed by a durable or
semi-durable broker rather than an in-memory queue. RabbitMQ's own tutorial
series, first published around 2010, uses "Work Queues" as the literal title of
its second tutorial and frames it explicitly as distributing time-consuming
tasks among multiple workers
(<https://www.rabbitmq.com/tutorials/tutorial-two-python>, verified 2026-08-14,
title "Work Queues," with the opening line explaining that the main idea
behind a work queue, also called a task queue, is to avoid doing a
resource-intensive job immediately and having the caller wait for it). That
RabbitMQ page is one of the most widely cited sources for the name in
production engineering writing, which is why the popularization date sits with
RabbitMQ, Celery, and Sidekiq rather than with a single paper.

A separate but related lineage is the queueing-theory sense of "work queue,"
meaning any FIFO structure fed by arrivals and drained by servers, studied
since Erlang's 1909 telephone-traffic work and formalised in Kendall's
notation (A/S/c queues). This entry is about the software engineering
pattern, which borrows the theory's vocabulary (arrival rate, service rate,
backlog) but adds the engineering concerns of durability, acknowledgment,
retry, and worker scaling that queueing theory alone does not address.

## 2. Problem and context

A system receives units of work that are independent of each other, and the
rate at which work arrives does not match the rate at which any single
processor can do it. The work might arrive from an HTTP request that must
return in milliseconds while the actual job takes seconds or minutes (send an
email, transcode a video, generate a PDF, run a machine learning inference).
It might arrive from a batch import that produces ten thousand rows to
validate. It might arrive from a scheduled trigger that fires the same job on
a cadence. In every case the caller that produces the work item should not,
and often cannot, block until the work is finished.

The pattern's context has three recognisable features. First, work items are
discrete and roughly independent, so they can be processed by any available
worker in any order without coordination between items, which is what
distinguishes Work Queue from a strictly ordered pipeline, see dimension 4.
Second, the number of producers and the number of consumers can each vary
independently and the two counts are usually different, often by orders of
magnitude, one web server producing jobs for a fleet of background workers.
Third, the system needs some resilience property beyond "it worked once,"
typically at-least-once delivery, so that a worker crashing mid-job does not
silently lose the job.

The concrete symptom that tells an engineer they are looking at a Work Queue
problem is a request handler doing something slow and then returning a
success response before the slow thing is actually confirmed done, or a
codebase with a `jobs` or `tasks` table, or an operations runbook that says
add more workers once the queue depth crosses a threshold. The pattern is the
answer to the question of how to decouple accepting work from performing it,
across process boundaries, without losing work when a worker dies.

## 3. Forces

The ranking of which force matters most in a given system is engineering
judgement, drawn from operational experience rather than a citable source.

- **Latency versus throughput.** The producer wants to return immediately,
  low latency for the caller. The queue trades that immediate response for
  eventual completion, and the system as a whole optimises for total
  throughput of jobs processed per second, not for the latency of any single
  job's actual execution.
- **Durability versus cost and complexity.** A queue backed by a durable
  broker (a database table, Kafka, SQS, RabbitMQ with persistent queues)
  survives a broker restart, but durable writes cost more than in-memory
  ones and add operational surface (disk, replication, retention policy). A
  purely in-memory queue is cheap and fast but loses everything on crash.
- **Ordering versus parallelism.** Processing jobs in strict arrival order
  requires a single consumer per ordering domain, which caps parallelism.
  Allowing multiple workers to compete for jobs maximises parallelism but
  gives up any guarantee about the order jobs complete in, and often gives up
  the guarantee about the order they even start in.
- **At-least-once versus exactly-once semantics.** Acknowledging a job only
  after it succeeds means a crash before acknowledgment causes redelivery, so
  the job handler must be idempotent or the system must tolerate duplicate
  side effects. Acknowledging before processing, or auto-ack, risks losing
  jobs on crash. True exactly-once processing at the queue layer is not
  achievable without a transactional outbox or an idempotency key scheme
  layered on top, a well known limit discussed further in dimension 17.
- **Backpressure versus data loss.** An unbounded queue absorbs any burst but
  can grow without limit, exhausting memory or disk, and hides the fact that
  producers are outrunning consumers until the operator notices a huge
  backlog. A bounded queue applies backpressure to producers, reject, block,
  or drop, but requires the producer to have a sane behaviour for that case.
- **Operational visibility versus simplicity.** A production-grade queue
  needs metrics for depth, age of oldest item, processing rate, and error
  rate, plus dead-letter handling and retry policy. A minimal queue is a list
  and a loop, and adding the operational machinery is real engineering cost
  that a prototype often skips and a production system cannot.
- **Cognitive load and team topology.** A synchronous call is one thing to
  reason about. A queue splits the system into a producer half and a
  consumer half that can be developed, deployed, and scaled by different
  people or teams, which is valuable at scale and pure overhead for a small
  team building a small system.

The pattern favours throughput, resilience to failure, and decoupled scaling
over latency of any individual job and over strict ordering. Where a system
needs low latency for every item, or strict global ordering, Work Queue is
either the wrong tool or must be constrained heavily, see dimension 4.

## 4. Applicability and non-applicability

Reach for a work queue when:

- The unit of work takes long enough, or is unreliable enough, that a caller
  should not wait synchronously for it, typically anything from tens of
  milliseconds of unpredictable external I/O up to hours of batch
  computation.
- Work arrives in bursts that exceed steady-state processing capacity, and
  smoothing the burst by buffering is acceptable to the business (an order
  confirmation email five seconds late is fine, a fraud check that blocks
  checkout is not).
- Producers and consumers should scale independently, for example a fleet of
  API servers producing jobs for a separately scaled fleet of GPU workers.
- The work must survive a process restart. Durable queues turn in-flight
  work into recorded work, so a crashed worker's jobs are recovered rather
  than lost.
- Retrying a failed unit of work is a meaningful and safe operation, meaning
  the handler can be made idempotent or the retry cost is acceptable.
- The work items are independent of one another, so any worker can pick up
  any item without needing to know what other workers are doing.

Do not reach for a work queue, or constrain it heavily, when:

- **The caller genuinely needs the result before it can proceed**, and there
  is no acceptable way to poll or be notified later. A queue turns a
  request-response interaction into a request-then-poll or
  request-then-push interaction, and if the caller has no polling or
  callback mechanism, the queue has just added latency and complexity
  without buying decoupling.
- **Strict global ordering across all items is required.** A work queue with
  competing consumers offers no ordering guarantee once more than one worker
  is active. Item B can finish before item A even though A was enqueued
  first. Systems that need a strict global sequence, an event log other
  systems replay in order, or a ledger, need a single-partition,
  single-consumer design or a genuinely ordered log such as a Kafka
  partition consumed by exactly one consumer in the group, which is closer
  to Pipeline than to Work Queue.
- **The work is a tight sequence of dependent stages**, where stage two
  needs the output of stage one from the same item before starting. That is
  Pipeline Parallelism (see the `pipeline-parallelism` entry), not Work
  Queue. Forcing dependent stages through one flat queue with re-enqueueing
  between stages is a common and painful misuse, covered in dimension 11.
- **The system is small and a synchronous call is fast and reliable
  enough.** Adding a broker, a worker process, retry logic, and dead-letter
  handling to process a job that reliably completes in ten milliseconds is
  pure overhead. The rule of thumb from operational experience is that the
  queueing and retry machinery earns its cost once job latency,
  unreliability, or volume makes synchronous handling operationally
  painful, not before.
- **Exactly-once, no-duplicate-side-effect semantics are mandatory and the
  handler cannot be made idempotent.** A queue that gives at-least-once
  delivery and a non-idempotent handler, charge a credit card, send a
  single physical shipment, will eventually double-execute. Either make the
  handler idempotent, dimension 17, or do not put that exact operation
  behind a competing-consumer queue.
- **The workload is CPU-bound and single-machine**, where a language-native
  thread pool or fork/join structure (see `thread-pool`, `fork-join`)
  already solves the scheduling problem without the operational cost of a
  broker.

## 5. Structure

- **Producer.** The component that creates a unit of work and enqueues it. It
  knows what needs doing but not who will do it or when. It typically
  returns to its own caller immediately after enqueueing, often with an
  identifier the caller can use to poll for status later.
- **Work item.** Also called a job, task, or message. A self-contained,
  serialisable description of one unit of work, including whatever data the
  consumer needs to perform it without a synchronous callback to the
  producer. A well-formed work item carries an identifier, a payload, and
  enough metadata, attempt count, enqueue time, priority, for the queue and
  the consumer to make correct decisions.
- **Queue.** The channel, the medium that holds enqueued items until a
  consumer claims them. Concretely this is a broker such as RabbitMQ, Amazon
  SQS, or a Redis list or stream, a database table used as a queue, or a
  distributed log such as a Kafka topic-partition read by a consumer group.
  The queue is responsible for at least two things. Making an item visible
  to exactly one consumer at a time while it is being processed, a
  visibility timeout or lock, and either removing the item on acknowledgment
  or making it visible again on failure or timeout.
- **Consumer.** Also called a worker, one of a pool of processes or threads
  that claims an item, performs the work described by it, and acknowledges
  success or failure. Workers are typically homogeneous and interchangeable.
  Any worker in the pool can process any item, which is the defining
  feature that separates competing consumers from a routed or sharded
  design.
- **Acknowledgment mechanism.** The protocol by which a worker tells the
  queue that it finished a job and the queue should remove it, an ack, or
  that it could not finish and the queue should make the item available
  again, a nack or timeout. This is the component that turns a worker taking
  a job into a job being durably done, and its absence is the difference
  between at-most-once and at-least-once systems.
- **Dead-letter queue.** A secondary queue that receives items which failed
  processing beyond a configured retry limit, so a poison message does not
  loop forever and does not silently vanish. Present in essentially every
  production-grade implementation. RabbitMQ, SQS, and Sidekiq all name this
  concept explicitly in their own documentation.
- **Result store.** Optional. A place, separate from the queue itself, where
  a worker writes the outcome of a job so a producer or a caller can look it
  up later, a status column, a Redis key, a callback webhook. Celery calls
  this the result backend. The queue and the result backend are commonly
  different pieces of infrastructure because the access patterns differ,
  one is write once and read many times briefly, the other is a rapid claim
  and acknowledge cycle.

## 6. ASCII structure diagram

```text
        enqueue                          claim / lock
Producer ------->  +---------------+  <------------------  Worker 1
                    |     Queue     |                        |
Producer ------->   |  (durable or  |  <------------------  Worker 2
                    |  in-memory)   |                        |
Producer ------->   +---------------+  <------------------  Worker 3
                            |                                 |
                            |  items exceed retry limit        | ack / nack
                            v                                 v
                    +---------------+                  +---------------+
                    | Dead-letter   |                  | Result store  |
                    |    queue      |                  | (status, out) |
                    +---------------+                  +---------------+
```

## 7. Dynamics

```text
Happy path, one item

Producer                Queue                    Worker
   |  enqueue(job)         |                         |
   |---------------------->|                         |
   |  <-- job_id           |                         |
   |                       |   claim (visibility      |
   |                       |    timeout starts)       |
   |                       |<------------------------|
   |                       |------ job payload ------>|
   |                       |                         |  do work
   |                       |                         |------+
   |                       |                         |<-----+
   |                       |         ack(job_id)      |
   |                       |<------------------------|
   |                       | (item removed / marked   |
   |                       |   done, DLQ untouched)    |

Worker crash mid-job, at-least-once redelivery

Producer                Queue                   Worker A         Worker B
   |  enqueue(job)         |                        |                |
   |---------------------->|                        |                |
   |                       |   claim, lock starts     |                |
   |                       |<-----------------------|                |
   |                       |                        |  X crash       |
   |                       |                        |                |
   |                       | visibility timeout      |                |
   |                       | expires, lock released  |                |
   |                       |                        |                |
   |                       |          claim (redelivered as attempt 2)|
   |                       |<--------------------------------------- |
   |                       |                                         | do work
   |                       |                    ack(job_id)          |
   |                       |<----------------------------------------|

Repeated failure past retry limit

  attempt 1 fails, requeued, attempt 2 fails, requeued,
  attempt 3 fails, retry limit reached, moved to dead-letter queue,
  producer or operator notified out of band
```

## 8. Implementation variants

- **Polling queue on a relational database.** A `jobs` table with columns
  such as `status`, `locked_by`, `locked_at`, `attempts`. Workers poll with a
  `SELECT ... FOR UPDATE SKIP LOCKED` (PostgreSQL, MySQL 8+) to atomically
  claim a row without two workers racing on the same job. This is the
  lowest-infrastructure variant, needs no separate broker, and is common in
  small to mid-size systems and in libraries such as `pg-boss` for
  PostgreSQL and Rails' `Solid Queue`. `SKIP LOCKED` is documented in the
  PostgreSQL manual as a way to avoid blocking on rows already locked by a
  concurrent transaction, exactly the queue-claim use case
  (<https://www.postgresql.org/docs/current/sql-select.html>, section on the
  `FOR UPDATE/SHARE` locking clause and `SKIP LOCKED`, verified 2026-08-14).
- **Broker-backed AMQP queue, RabbitMQ.** Producers publish messages to an
  exchange routed to a queue. Workers open a channel, set a prefetch count
  to bound how many unacknowledged messages a single worker holds, and ack
  or nack explicitly. RabbitMQ's own Work Queues tutorial documents exactly
  this shape and calls out `basic_qos(prefetch_count=1)` as the mechanism
  that gives fair, round-robin-avoiding dispatch instead of blind round
  robin (<https://www.rabbitmq.com/tutorials/tutorial-two-python>, section
  "Fair dispatch," verified 2026-08-14).
- **Managed queue service, Amazon SQS.** A hosted queue with a visibility
  timeout instead of an explicit lock. A consumer receives a message, has
  until the visibility timeout expires to delete it, its ack, and if it
  does not, the message becomes visible to other consumers again. SQS
  documents this visibility-timeout mechanism as the core of its
  at-least-once delivery model
  (<https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html>,
  verified 2026-08-14).
- **Redis-backed queue, Sidekiq, Bull, BullMQ, RQ.** Uses a Redis list or
  stream as the queue data structure. Workers use `BRPOPLPUSH` or Redis
  Streams consumer groups, `XREADGROUP`, to atomically move an item into an
  in-flight set while working on it, then acknowledge with `XACK`. Redis
  Streams consumer groups are documented as providing per-consumer delivery
  tracking and a pending-entries list for exactly this pattern
  (<https://redis.io/docs/latest/develop/data-types/streams/>, section on
  consumer groups, verified 2026-08-14). Sidekiq's own documentation
  describes workers as a pool of threads each polling a Redis queue and
  processing jobs from a Ruby class
  (<https://github.com/sidekiq/sidekiq/wiki/Getting-Started>, verified
  2026-08-14).
- **Distributed log as queue, Kafka consumer groups.** A Kafka topic split
  into partitions, consumed by a consumer group where each partition is
  assigned to exactly one consumer in the group at a time. This gives
  ordering within a partition, unlike the other variants, at the cost of
  parallelism being capped by the partition count, and offset commits,
  rather than per-message ack, mark progress. Apache Kafka's documentation
  describes consumer groups as dividing partitions among group members so
  that each partition is consumed by exactly one consumer in the group
  (<https://kafka.apache.org/documentation/#intro_consumers>, verified
  2026-08-14). This variant sits between classic Work Queue and Pipeline,
  because it can offer ordering guarantees the others cannot.
- **In-memory queue with a bounded channel.** For single-process fan-out
  where durability across a process restart is not required, a bounded
  channel, a Go `chan` with a fixed buffer, a Java `ArrayBlockingQueue`, a
  Python `queue.Queue(maxsize=N)`, plays the role of the queue and provides
  natural backpressure by blocking the producer when full. This is closer
  in spirit to Producer-Consumer but is frequently what people mean by a
  work queue inside a single service.
- **Priority and delayed variants.** Many implementations add a priority
  field so higher-priority items are claimed first, a priority heap or
  multiple queues polled in order, and a delay or `visibility_at` field so
  an item is not claimable until a future time, used for scheduled and
  retry-with-backoff jobs. Sidekiq's scheduled-job set and SQS's
  `DelaySeconds` parameter are both concrete instances of the delayed
  variant.

## 9. Known production uses

- **Celery**, the Python distributed task queue, is used to run background
  jobs decoupled from the web request cycle for a very large share of
  production Django and Flask applications. Celery's own documentation
  describes it as an open source asynchronous task queue that is used in
  production systems to process millions of tasks a day
  (<https://docs.celeryq.dev/en/stable/getting-started/introduction.html>,
  verified 2026-08-14). It supports RabbitMQ, Redis, and Amazon SQS as
  interchangeable broker backends, which is itself evidence that Work Queue
  is a shape independent of any one broker implementation.
- **Sidekiq** is the standard background job processor for Ruby on Rails
  applications. Sidekiq's own site describes it as used by thousands of
  companies to process background jobs efficiently using threads inside
  Ruby processes against a shared Redis queue
  (<https://sidekiq.org/>, verified 2026-08-14, and
  <https://github.com/sidekiq/sidekiq>, verified 2026-08-14, which describes
  it as simple, efficient background processing for Ruby).
- **Amazon Simple Queue Service, SQS**, is AWS's managed implementation of
  exactly this pattern and is documented as designed to let a system
  decouple and scale microservices, distributed systems, and serverless
  applications, with visibility timeouts, dead-letter queues, and
  at-least-once delivery as first-class features
  (<https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html>,
  verified 2026-08-14). SQS's own developer guide names the multi-consumer
  polling pattern this entry describes.
- **RabbitMQ**, the widely deployed open source AMQP broker, ships a
  tutorial literally titled "Work Queues" that walks through exactly the
  competing-consumer shape with round-robin dispatch and manual
  acknowledgment
  (<https://www.rabbitmq.com/tutorials/tutorial-two-python>, verified
  2026-08-14). RabbitMQ is used in production messaging infrastructure
  across e-commerce, fintech, and telecom, and its core tutorial framing is
  the direct namesake for this pattern entry's title.
- **Apache Kafka consumer groups** power event-driven and background
  processing pipelines at large scale at organizations including LinkedIn,
  where Kafka originated specifically to handle high-throughput log and
  event processing. Kafka's own documentation frames consumer groups as the
  mechanism for scaling consumption across multiple processes while
  preserving partition-level ordering
  (<https://kafka.apache.org/documentation/#intro_consumers>, verified
  2026-08-14).

## 10. Consequences

Positive.

- Producers return quickly and are insulated from the latency and failure
  modes of the actual work, improving perceived responsiveness for
  interactive callers.
- Producer and consumer capacity scale independently. A burst of enqueued
  work can be absorbed by adding workers without touching the producing
  service at all.
- A crashed or restarted worker does not lose in-flight work when the queue
  is durable and acknowledgment is explicit, which is a meaningful
  reliability improvement over a synchronous call that simply fails on
  crash.
- Work becomes retryable as a first-class operation. A job that failed due
  to a transient dependency outage can be reprocessed automatically without
  the caller ever knowing there was a problem.
- The system gains a natural place to apply backpressure, rate limiting,
  and prioritisation, none of which are straightforward to bolt onto a
  purely synchronous call chain.

Negative, and the degree of cost here is judgement drawn from operational
experience rather than a citable measurement.

- The system becomes eventually consistent with respect to the queued work.
  The caller no longer knows, at the moment of the original request,
  whether the work actually succeeded, and must be given a separate
  mechanism, polling, webhook, notification, to find out.
- Ordering guarantees are weak or absent by default. Reasoning about what
  happened before what across items becomes materially harder once multiple
  competing consumers are involved.
- At-least-once delivery pushes the idempotency burden onto every job
  handler. A handler written assuming exactly-once execution will
  eventually double-execute in production, and that failure mode is often
  invisible until it causes a real incident, a double charge or a duplicate
  email.
- Debugging becomes harder. A failure that would previously be a stack
  trace in a request log is now split across an enqueue event, a broker,
  and a worker log, often on different machines, and correlating them needs
  deliberate tracing, dimension 16.
- New operational surface. Queue depth, broker health, worker pool sizing,
  and dead-letter handling all need monitoring and runbooks that a purely
  synchronous system does not need.
- Poorly bounded queues can hide the fact that the system is falling
  behind. An unbounded queue growing silently is a common cause of an
  outage that looks sudden but was actually building for hours.

## 11. Failure modes and misuse

The symptoms below are drawn from operational experience rather than a single
citable source.

**Symptom.** Jobs process twice, causing duplicate emails or double charges.
**Cause.** At-least-once delivery combined with a non-idempotent handler. A
worker finished the job, crashed or lost network before sending the ack, and
the queue redelivered it to another worker which ran it again. **Fix.** Make
the handler idempotent, typically with an idempotency key stored alongside
the side effect, a `processed_job_ids` table checked before acting, or a
natural idempotency key the downstream system itself honours.

**Symptom.** Queue depth grows without bound and workers never seem to catch
up, even though nothing looks broken. **Cause.** Consumer throughput is lower
than producer throughput, either because there are too few workers, a worker
is slower than expected under load, or a poison message is being retried in
a tight loop and consuming worker capacity without a retry limit or backoff.
**Fix.** Alert on queue depth and oldest-item age, not just on error rate.
Add a maximum retry count with exponential backoff and a dead-letter queue
so a poison message cannot monopolise a worker forever.

**Symptom.** The same job appears to run forever, or the queue reports the
job as in progress long after the worker that claimed it has died.
**Cause.** The visibility timeout or lock duration is set shorter than the
job's actual processing time, so the lock expires and another worker claims
the same item while the first worker is still legitimately working, or
conversely it is set far too long so a genuinely crashed worker's job sits
invisible and unprocessed until the timeout finally expires. **Fix.** Set the
visibility timeout to comfortably exceed the p99 processing time, and use a
heartbeat extension mechanism, many brokers support extending visibility
mid-job, for jobs with highly variable duration rather than guessing a
single static timeout.

**Symptom.** Two workers both start processing what looks like the same
logical unit of work, corrupting shared state. **Cause.** The queue's claim
mechanism is not actually atomic for the storage backend in use, a common
mistake being a hand-rolled polling query without `SKIP LOCKED` or an
equivalent atomic claim, so two workers' select then update race and both
believe they claimed the row. **Fix.** Use the broker's or database's native
atomic claim primitive, `SKIP LOCKED`, a broker's native claim and ack API,
or a Redis `BRPOPLPUSH` or consumer-group read, instead of a read-then-write
pattern with no locking.

**Symptom.** A downstream stage's output silently disappears or arrives in
the wrong order relative to a related item. **Cause.** Work Queue was used
for a workload that actually needed strict ordering or dependency between
stages, for example re-enqueueing stage two items onto the same flat queue
as stage one items with no partitioning key, so two competing consumers
process related items out of order. **Fix.** This is a pattern mismatch, not
a bug to patch. Move to a partitioned or ordered transport, a Kafka
partition keyed by the entity's identifier, or to an explicit Pipeline
Parallelism structure with a dependency graph, rather than trying to force
ordering guarantees onto a competing-consumer queue.

**Symptom.** Memory or disk usage on the broker climbs steadily and
eventually the broker itself falls over, taking every queue down at once.
**Cause.** An unbounded queue with no consumer keeping pace, often
discovered only when the broker process itself runs out of resources.
**Fix.** Bound the queue, a max length with a rejection or backpressure
policy, and treat a queue growing unboundedly as a first-class alert rather
than something only the broker's own resource exhaustion reveals.

**Symptom.** Local development and testing become extremely painful, tests
are flaky, and engineers start disabling the queue in tests entirely.
**Cause.** Treating the queue as invisible infrastructure rather than a
designed seam, so tests either need a real broker running, slow and flaky,
or the queue is bypassed entirely in test mode, which then hides bugs that
only appear with real asynchronous execution. **Fix.** Design an explicit
synchronous or in-memory test double for the queue, dimension 15, rather
than either running a real broker in every test or bypassing the
abstraction.

## 12. Trade-off matrix

| Force | Work Queue (competing consumers) | Producer-Consumer (in-process) | Pipeline Parallelism | Actor Model |
|---|---|---|---|---|
| Ordering guarantee | None across items by default; per-partition ordering only in log-based variants (Kafka) | Typically FIFO within one bounded buffer, single process | Strict order within a stage, sequential across stages | Per-mailbox order only, none across actors |
| Durability across restart | Yes, when the broker or table is durable | No, buffer is in-memory and process-local | Depends on transport between stages | Depends on implementation, usually none by default |
| Cross-process / cross-machine scaling | Native, this is the point of the pattern | No, confined to one process | Yes, stages can be separate services | Yes, actors can be distributed |
| Latency for a single item | Higher, item waits for a free worker and network round trips to the broker | Lowest, in-memory handoff | Depends on slowest stage | Low for in-process actors, higher when distributed |
| Coupling between producer and consumer | Loose, they need only agree on the item schema | Tight, share process and memory | Loose between stages, tight within a stage's contract | Loose, mediated entirely by messages |
| Handling of dependent, ordered sub-tasks | Poor fit, needs external partitioning to preserve order | Poor fit, same limitation | Native fit, this is what it is for | Workable via ordered per-actor mailboxes |
| Operational complexity | High, needs a broker, retry policy, DLQ, monitoring | Low, language runtime primitives suffice | Medium to high, needs stage coordination and backpressure between stages | Medium to high, needs supervision and mailbox management |

## 13. Related and incompatible patterns

- **Producer-Consumer.** Work Queue is Producer-Consumer stretched across
  process or machine boundaries with a durable transport substituted for
  the in-memory bounded buffer. The core coordination problem, avoiding an
  overwhelmed producer and avoiding two consumers claiming the same item, is
  identical. Only the mechanism differs. See the `producer-consumer` entry.
- **Thread Pool.** A single worker in a work queue system is very often
  itself implemented as, or backed by, a thread pool inside that worker
  process, so the worker can hold multiple items in flight concurrently
  rather than one at a time. Thread Pool answers how one process uses its
  CPUs efficiently, Work Queue answers how work gets distributed across
  many processes. See the `thread-pool` entry.
- **Leader-Followers.** A specialisation where the pool of consumers takes
  turns being the one thread that waits on the queue, handing off the
  leader role after claiming work, to reduce context switching and lock
  contention compared to every worker independently polling. See the
  `leader-followers` entry. It composes with Work Queue rather than
  replacing it.
- **Pipeline Parallelism.** Explicitly incompatible in intent, not in
  coexistence. Pipeline is for a sequence of dependent stages that must run
  in order on each item. Using a flat competing-consumer queue for
  dependent stages breaks the ordering the pipeline needs, as covered in
  dimensions 4 and 11. The two do compose when each pipeline stage is
  itself internally implemented as a work queue feeding a pool of workers
  for that stage, provided ordering between stages is preserved by a
  separate mechanism, partitioning, sequence numbers, or a barrier.
- **Future/Promise.** A common companion, not a substitute. When a producer
  needs to know the outcome of a queued item later, the enqueue call often
  returns a Future or a job identifier that resolves once the worker
  finishes and writes to the result store, letting the caller either poll
  or await the eventual result without blocking the queue itself. See the
  `future-promise` entry.
- **Circuit Breaker, resilience family.** Frequently placed around the
  external calls a worker makes inside a job handler, so a struggling
  downstream dependency does not cause every worker in the pool to hang
  simultaneously and starve the queue's throughput.
- **Saga.** When a queued job is one step of a longer multi-step business
  transaction spanning services, the queue is the transport that carries
  each saga step, and the saga's own compensation logic is what handles a
  step that ultimately lands in the dead-letter queue.

## 14. Refactoring path in and out

Introducing a work queue into code that currently does the work
synchronously.

1. Identify the boundary. Find the point in the synchronous call chain
   where the caller does not actually need the result immediately, or
   where immediately can become eventually with a status the caller can
   check. This is usually the smallest safe seam, not the largest possible
   one.
2. Extract the work into a standalone, serialisable unit. Turn the function
   call's arguments into a plain data structure, the job payload, that does
   not depend on any in-memory state from the caller, because the worker
   that eventually runs it will be a separate process.
3. Introduce the queue and a no-op or synchronous worker first. Wire the
   producer to enqueue and a trivial consumer to dequeue and call the
   original function directly, still within the same deploy, to prove the
   plumbing works before adding real asynchrony. This mirrors the general
   discipline of strangling an old path incrementally, used when
   introducing any structural pattern into working code.
4. Split the consumer into its own deployable process or pool, add
   acknowledgment, and pick a redelivery policy, retry count, backoff, dead
   letter. Only now does the system gain the durability and independent
   scaling that is the actual point of the pattern.
5. Give the producer's original caller a way to observe eventual state,
   poll an endpoint keyed by job id, subscribe to a webhook, or simply
   accept fire-and-forget if nothing downstream needs to know. Skipping
   this step is the most common way an introduction of Work Queue quietly
   breaks a caller that used to get a definitive answer synchronously.
6. Add idempotency to the handler before shipping the durable, retryable
   version to production. Retrofit an idempotency key or a
   check-before-act guard rather than discovering the double-execution bug
   in production.

Removing a work queue once it no longer earns its place, job volume dropped,
latency requirement changed, or the operational cost outweighs the benefit.

1. Confirm the assumption the queue exists to protect no longer holds.
   Check actual production job latency and volume rather than trusting a
   memory of why it was added.
2. Inline the consumer's logic back into the producer's call path behind a
   feature flag, so both paths exist simultaneously and can be compared.
3. Remove the asynchronous status-polling machinery from callers only after
   the synchronous path has been the default in production for long enough
   to be confident it will not need the eventual-consistency escape hatch
   again.
4. Decommission the broker or table last, once nothing enqueues to it and
   the dead-letter queue is confirmed empty of anything that still matters.

## 15. Testing and verification

What becomes easier is that the handler logic itself is a plain function
taking a job payload, and it can be unit tested in complete isolation from
the broker, the network, and timing, exactly like testing any pure function.
The producer side can be tested by asserting that an item with the right
shape was enqueued without needing the consumer to actually run.

What becomes harder is that end-to-end behaviour now spans two processes and
an asynchronous boundary, so a test that wants to assert the job actually
ran and had a given effect needs either a real broker, slower and more
realistic but prone to flakiness from timing, or a fake or in-memory queue
implementation that runs the handler inline and synchronously for the
purpose of the test. Both Celery and Sidekiq document exactly this
trade-off in their own testing guides, offering an eager or inline
execution mode specifically so tests do not need a real broker.

Recommended techniques:

- **Test double for the queue itself**, an in-memory implementation of the
  same enqueue, claim, ack interface used in production, so the producer
  and consumer can be tested together without network or broker
  dependency. This is the queue-specific instance of the general Test
  Double technique described in Gerard Meszaros, *xUnit Test Patterns.
  Refactoring Test Code*, Addison-Wesley, 2007, chapter 15.
- **Contract tests for the job payload schema**, since the producer and
  consumer are separate deployables that can drift. A schema or contract
  test that runs against both sides catches a producer that starts sending
  a payload shape the consumer no longer understands, before it reaches
  production.
- **Idempotency tests**, explicitly running the same job handler twice with
  the same input and asserting the observable side effect happened exactly
  once, directly testing the property that dimension 11's most common
  failure mode violates.
- **Chaos or fault-injection tests for redelivery**, deliberately killing a
  worker mid-job in a staging environment, or simulating it by not
  acknowledging, and confirming the item is redelivered and eventually
  processed, rather than assuming the broker's documented behaviour will
  hold under the specific configuration in use.
- **Load and backlog tests**, enqueueing at a rate above sustained consumer
  throughput and confirming the system's chosen backpressure or bounded
  behaviour actually triggers, rather than the queue growing silently, the
  actual production failure mode described in dimension 11.

## 16. Observability signals

A healthy work queue, viewed on a dashboard, looks like this. Queue depth
oscillates around a low baseline rather than trending upward. The age of the
oldest unprocessed item stays within an expected bound, seconds to low
minutes depending on the SLA. Processing rate tracks the enqueue rate over
any sustained window. Error and retry rate stay near zero. The dead-letter
queue stays empty or only receives items that genuinely need human
attention.

A failing instance shows one or more of the following signs. Queue depth
trends steadily upward with no corresponding drop in enqueue rate, meaning
consumers cannot keep pace. Oldest-item age grows without bound, meaning
some items are starved even if average throughput looks fine. There is a
spike in retry count or nack rate, meaning jobs are failing and being
requeued. Dead-letter queue depth increases, meaning jobs are exhausting
their retry budget. Or worker process count and CPU or memory look healthy
while throughput is flat, which usually points to a downstream dependency
the workers are blocked on rather than the queue itself being at fault.

Concrete signals to log, trace, or measure:

- Queue depth, the current count of unacknowledged or unclaimed items,
  sampled continuously, not just at enqueue time.
- Age of the oldest unprocessed item, which surfaces starvation that a raw
  depth count can hide if throughput looks superficially fine.
- Per-job attempt count at completion, to distinguish jobs that succeed on
  the first try from jobs limping through several retries, a leading
  indicator of a flaky downstream dependency.
- End-to-end latency from enqueue timestamp to acknowledgment timestamp,
  distinct from the handler's own execution time, because it captures time
  spent waiting for a free worker.
- A trace correlation id propagated from the producer's original request,
  through the enqueued payload, into the worker's logs, so a single
  distributed trace can be reconstructed across the asynchronous boundary.
  OpenTelemetry's messaging semantic conventions document propagating trace
  context through message headers for exactly this purpose
  (<https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/>,
  verified 2026-08-14).
- Dead-letter queue depth and the reason code attached to each dead-lettered
  item, so a human triaging the DLQ does not have to reconstruct the
  failure from raw logs.

## 17. Security and privacy implications

The queue is an additional durable store of data that previously existed
only transiently in a request's memory, and that has direct privacy and
data-handling consequences. If a job payload contains personal data, an
email address, a document, a payment token, that data now sits at rest in
the broker or the database backing the queue, potentially for as long as
the retry window or the dead-letter retention period, and is subject to
whatever access control and encryption-at-rest policy the broker has,
separately from whatever policy governs the original request. A payload
containing a raw payment card number or an unencrypted access token in a
queue that an operator can browse, RabbitMQ's management UI or a database
admin panel, is a materially different exposure than the same value living
only in a request handler's stack frame for milliseconds. The general
guidance in production systems is to enqueue references, an object id or a
pointer to encrypted storage, rather than sensitive payloads directly, and
to apply the same encryption-in-transit and encryption-at-rest standards to
the queue's storage as apply to the primary datastore.

At-least-once delivery is itself a data-handling concern beyond the
double-charge example in dimension 11. A job that sends a notification,
writes an audit log entry, or calls a third-party API with side effects can
leak information twice, a duplicate email revealing internal retry
behaviour to an end user, or a duplicate webhook call to a partner system.
Idempotency keys, covered in dimension 11 as a correctness fix, are equally
a privacy and trust fix.

A dead-letter queue is a place where failed, and sometimes malformed or
adversarial, payloads accumulate for human review, which makes it a
plausible target and a plausible source of a data leak if it is not subject
to the same access controls as the primary queue. An operator with DLQ
access effectively has access to every payload that failed processing,
which may be a superset of what that operator is otherwise authorised to
see.

A queue that accepts jobs from an untrusted or lower-trust boundary, a
public API endpoint that enqueues a job directly from unauthenticated
input, inherits an injection and resource-exhaustion attack surface. A
malicious or malformed payload can be crafted to make the handler behave
unexpectedly, classic deserialization vulnerabilities have historically
targeted exactly this seam, when a queue payload is deserialised into an
object graph with insufficient validation, or an attacker can flood the
queue to exhaust worker capacity, a denial-of-service vector that a bounded
queue and a per-source rate limit on the producer side both mitigate.
Validating and authenticating at the producer boundary, rather than
trusting the payload once it reaches the worker, is the standard
mitigation.

Where the pattern is silent on security is worth stating plainly. The queue
mechanism itself does not define an authorization model for who may
enqueue what kind of job, or who may claim and process which jobs. That is
left entirely to the implementation, and its absence in a naive
implementation, any authenticated service can enqueue any job type, any
worker can claim any job, is a design choice that needs explicit review
rather than an inherent property of the pattern.

## 18. References

1. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, the
   Competing Consumers pattern.
2. RabbitMQ, "Work Queues" tutorial,
   <https://www.rabbitmq.com/tutorials/tutorial-two-python>, verified
   2026-08-14.
3. Amazon Web Services, "Amazon SQS visibility timeout," AWS SQS Developer
   Guide,
   <https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html>,
   verified 2026-08-14.
4. Amazon Web Services, "What is Amazon Simple Queue Service," AWS SQS
   Developer Guide,
   <https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html>,
   verified 2026-08-14.
5. Redis, "Redis Streams," section on consumer groups,
   <https://redis.io/docs/latest/develop/data-types/streams/>, verified
   2026-08-14.
6. Sidekiq, "Getting Started" wiki page,
   <https://github.com/sidekiq/sidekiq/wiki/Getting-Started>, verified
   2026-08-14, and Sidekiq repository README,
   <https://github.com/sidekiq/sidekiq>, verified 2026-08-14, and
   <https://sidekiq.org/>, verified 2026-08-14.
7. Celery Project, "Introduction to Celery,"
   <https://docs.celeryq.dev/en/stable/getting-started/introduction.html>,
   verified 2026-08-14.
8. Apache Kafka, "Consumers" section of the official documentation,
   <https://kafka.apache.org/documentation/#intro_consumers>, verified
   2026-08-14.
9. PostgreSQL, "SELECT" reference page, locking clause and `SKIP LOCKED`,
   <https://www.postgresql.org/docs/current/sql-select.html>, verified
   2026-08-14.
10. OpenTelemetry, "Semantic Conventions for Messaging Spans,"
    <https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/>,
    verified 2026-08-14.
11. Gerard Meszaros, *xUnit Test Patterns. Refactoring Test Code*,
    Addison-Wesley, 2007, chapter 15, Test Double.

## Code examples

### TypeScript, an in-memory work queue with a bounded worker pool

```typescript
type Job<T> = { id: string; payload: T; attempts: number };

class WorkQueue<T> {
  private items: Job<T>[] = [];
  private waiters: Array<() => void> = [];

  enqueue(payload: T): string {
    const job: Job<T> = { id: crypto.randomUUID(), payload, attempts: 0 };
    this.items.push(job);
    const waiter = this.waiters.shift();
    if (waiter) waiter();
    return job.id;
  }

  private async claim(): Promise<Job<T>> {
    while (this.items.length === 0) {
      await new Promise<void>((resolve) => this.waiters.push(resolve));
    }
    return this.items.shift()!;
  }

  async runWorkers(count: number, handler: (payload: T) => Promise<void>, maxAttempts = 3) {
    const worker = async () => {
      for (;;) {
        const job = await this.claim();
        job.attempts += 1;
        try {
          await handler(job.payload);
        } catch (err) {
          if (job.attempts < maxAttempts) {
            this.items.push(job);
          } else {
            console.error(`dead-letter job ${job.id}`, err);
          }
        }
      }
    };
    return Promise.all(Array.from({ length: count }, worker));
  }
}

async function main() {
  const queue = new WorkQueue<number>();
  for (let i = 0; i < 5; i++) queue.enqueue(i);

  const workers = queue.runWorkers(2, async (n) => {
    console.log(`processing ${n}`);
    await new Promise((r) => setTimeout(r, 5));
  });

  await Promise.race([workers, new Promise((r) => setTimeout(r, 100))]);
}

main();
```

### Python, a database-style work queue using `queue.Queue` and a thread pool

```python
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Job:
    payload: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    attempts: int = 0


class WorkQueue:
    def __init__(self, max_attempts: int = 3) -> None:
        self._q: "queue.Queue[Job]" = queue.Queue()
        self._dead_letter: list[Job] = []
        self._max_attempts = max_attempts
        self._lock = threading.Lock()

    def enqueue(self, payload: int) -> str:
        job = Job(payload=payload)
        self._q.put(job)
        return job.id

    def run_workers(self, count: int, handler) -> None:
        def worker() -> None:
            while True:
                try:
                    job = self._q.get(timeout=0.2)
                except queue.Empty:
                    return
                job.attempts += 1
                try:
                    handler(job.payload)
                except Exception:
                    if job.attempts < self._max_attempts:
                        self._q.put(job)
                    else:
                        with self._lock:
                            self._dead_letter.append(job)
                finally:
                    self._q.task_done()

        threads = [threading.Thread(target=worker) for _ in range(count)]
        for t in threads:
            t.start()
        self._q.join()
        for t in threads:
            t.join(timeout=1)

    @property
    def dead_letter_count(self) -> int:
        return len(self._dead_letter)


def process(n: int) -> None:
    time.sleep(0.01)
    print(f"processed {n}")


if __name__ == "__main__":
    wq = WorkQueue()
    for i in range(6):
        wq.enqueue(i)
    wq.run_workers(3, process)
    print("dead-lettered", wq.dead_letter_count)
```

### Go, a bounded channel work queue with backoff-based retry

```go
package main

import (
	"errors"
	"fmt"
	"sync"
	"time"
)

type Job struct {
	ID       int
	Attempts int
}

type WorkQueue struct {
	items chan Job
}

func NewWorkQueue(capacity int) *WorkQueue {
	return &WorkQueue{items: make(chan Job, capacity)}
}

func (q *WorkQueue) Enqueue(id int) {
	q.items <- Job{ID: id}
}

func (q *WorkQueue) Close() {
	close(q.items)
}

func processFlaky(j Job) error {
	if j.ID%3 == 0 && j.Attempts < 2 {
		return errors.New("transient failure")
	}
	return nil
}

func (q *WorkQueue) RunWorkers(n int, maxAttempts int) {
	var wg sync.WaitGroup
	deadLetter := make(chan Job, n)
	var dlWg sync.WaitGroup
	dlWg.Add(1)
	dead := []Job{}
	go func() {
		defer dlWg.Done()
		for j := range deadLetter {
			dead = append(dead, j)
		}
	}()

	for w := 0; w < n; w++ {
		wg.Add(1)
		go func(worker int) {
			defer wg.Done()
			for job := range q.items {
				job.Attempts++
				if err := processFlaky(job); err != nil {
					if job.Attempts < maxAttempts {
						time.Sleep(time.Millisecond)
						q.items <- job
					} else {
						deadLetter <- job
					}
					continue
				}
				fmt.Printf("worker %d processed job %d\n", worker, job.ID)
			}
		}(w)
	}
	wg.Wait()
	close(deadLetter)
	dlWg.Wait()
	fmt.Printf("dead-lettered %d\n", len(dead))
}

func main() {
	q := NewWorkQueue(10)
	for i := 1; i <= 6; i++ {
		q.Enqueue(i)
	}
	go func() {
		time.Sleep(50 * time.Millisecond)
		q.Close()
	}()
	q.RunWorkers(2, 3)
}
```
