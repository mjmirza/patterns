---
name: Message Dispatcher
slug: message-dispatcher
family: 07-integration
category: Integration
aliases: [Dispatcher, Worker Pool Dispatcher, Load-Balancing Consumer]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [competing-consumers, polling-consumer, event-driven-consumer, message-channel, point-to-point-channel, claim-check, transactional-client, datatype-channel]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Message Dispatcher. Gregor Hohpe and Bobby Woolf catalogued
it in "Enterprise Integration Patterns" (Addison-Wesley, 2003), in the Messaging
Endpoints chapter, alongside Polling Consumer and Event-Driven Consumer. The
Enterprise Integration Patterns website mirrors the book's text and states the
problem plainly. An application uses messaging, and needs multiple consumers on
a single channel to work in a coordinated fashion, and asks how those consumers
can coordinate their message processing (verified 2026-08-02,
https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageDispatcher.html).
The pattern is described as having two participant roles, a Dispatcher that
consumes from the channel and a set of Performers that each process one
message.

In everyday engineering conversation the same shape goes by several other
names. This is judgement rather than a sourced claim. Worker pool dispatcher
is the term used when the emphasis is on the fixed-size pool of workers
rather than on message coordination. Load-balancing consumer is the term used
when the emphasis is on spreading work evenly. And simply dispatcher is what
codebases call it when they never adopted Hohpe and Woolf's messaging
vocabulary but arrived at the same structure by building a queue plus a pool
of goroutines, threads, or processes around it. The pattern predates the book
by decades in operating-systems literature, where the identical shape appears
as a work-queue or thread-pool executor, but the EIP catalog is the first
place the shape was named specifically for message-oriented middleware and
given a place among the other endpoint patterns.

## 2. Problem and context

A single logical stream of work needs to be processed by more capacity than
one consumer thread can provide, and the team wants that capacity applied
without breaking three properties the naive fix destroys.

Picture an order-processing service that receives one order message per
customer checkout on a queue. At low volume a single consumer thread reading
one message at a time, processing it, and reading the next, is fine. At
Black-Friday volume the queue backs up because each order requires a payment
authorization call that takes a few hundred milliseconds. The team's first
instinct is usually one of two moves, and both create a new problem instead of
solving the old one.

The first move is to start several independent consumer processes, each with
its own connection to the queue, and let the broker's own delivery mechanism
spread messages across them. This is the Competing Consumers pattern, and it
works, but it multiplies broker connections, multiplies the cost of any setup
each consumer must do (database pools, TLS handshakes, warmed caches), and
makes per-message coordination, such as strict draining before a graceful
shutdown, or applying a global concurrency ceiling that spans consumer
instances, awkward because no single process sees the whole picture.

The second move is to process messages on whatever thread pumps the receive
loop, using a language-level construct such as a thread-per-message spawn.
This removes the backlog for a while but loses backpressure. Nothing bounds
how many concurrent workers exist, so a burst of ten thousand messages spawns
ten thousand workers, exhausting memory, file descriptors, or downstream
connection pools before any of them finish.

The Message Dispatcher solves a narrower problem than either of those two
moves. It asks how ONE consuming process, with ONE connection to the channel
and full visibility into everything it currently has in flight, applies a
BOUNDED and COORDINATED amount of concurrency to the messages it receives.
The context this pattern belongs to has three conditions holding at once.
There is already a Message Channel (dimension 13's cross-reference). A single
logical receiver already owns that channel, so this is not a fan-out across
processes, which is Competing Consumers. And the unit of work per message is
small enough, or independent enough, that parallel processing inside one
process is worth the coordination cost.

## 3. Forces

**Throughput versus per-message latency.** A dispatcher exists to raise
aggregate throughput by running more than one message at a time, and that
choice trades away the guarantee that message N finishes before message N+1
starts. If message ordering matters, the dispatcher either has to route
related messages to the same performer, using a Recipient List keyed on a
correlation field, or the pattern is simply the wrong tool and a strictly
ordered Polling Consumer is correct instead.

**Concurrency versus resource exhaustion.** Every performer that is running
holds resources, a thread's stack, a database connection, an open file, a
downstream HTTP connection. The dispatcher must cap how many performers run at
once, because an unbounded pool degrades from a throughput improvement into
the same resource-exhaustion failure the naive thread-per-message approach
produces, only with a queue in front of it delaying when the failure shows up
rather than preventing it.

**Coordination versus simplicity.** A dispatcher that only round-robins
messages to identical performers is simple to reason about. A dispatcher that
must route by message type to specialized performers, or must apply
backpressure signals upstream when its internal queue is full, or must
preserve partial ordering per correlation key, is doing genuine coordination
work, and every one of those responsibilities is a place a bug can hide. The
pattern favors coordination that lives in one process's memory, which is
simpler to reason about than coordination spread across independent consumer
processes, but that simplicity is bought by making the dispatcher itself a
single point of failure for the whole consuming side of the channel.

**Failure isolation versus shared fate.** Because all performers run inside
one process, a fault that takes down the process, an unhandled panic that
escapes a worker's recovery boundary, a memory leak that accumulates across
thousands of dispatched messages, takes every in-flight message down with it.
Competing Consumers, by contrast, isolates a crash to the one process that
crashed. The dispatcher pattern favors resource efficiency and coordination
control over that process-level fault isolation, and a production system
using it needs its own answer for what happens to in-flight, un-acknowledged
messages when the dispatcher process itself dies mid-batch.

**Operability versus footprint.** One process with an internal pool is
cheaper to deploy, monitor, and scale than a fleet of independent consumer
processes, and it gives an operator one place to look at queue depth versus
active workers. That operability gain is real, but it means the dispatcher
process becomes the one thing that must be watched closely, because scaling
it means changing pool size and restarting rather than adding another
identical instance behind a load balancer.

## 4. Applicability and non-applicability

Reach for a Message Dispatcher when.

- A single logical consumer owns a channel and needs to process several
  messages concurrently, but the per-message unit of work is small enough
  that spinning up a whole separate process per message, or per burst, is the
  wrong grain of parallelism.
- The team wants one place to apply a global concurrency ceiling, a shared
  connection pool, or a warmed cache, across everything currently being
  processed from that channel, rather than duplicating that state across N
  independent consumer processes.
- The workload benefits from routing to SPECIALIZED performers based on a
  property of the message, for example routing image-resize messages to a
  pool sized for CPU-bound work and routing notification-send messages to a
  differently sized pool for I/O-bound work, both fed from the same channel.
- The deployment environment makes horizontal process scaling expensive or
  slow relative to simply widening an in-process pool, for example a single
  large machine or a container with a fixed and generous CPU allocation.
- Backpressure needs to be visible and controllable in one place. The
  dispatcher can refuse to pull the next message, or can push back on an
  upstream Recipient List, the moment its own in-flight count reaches a
  ceiling, without needing a cluster-wide coordination mechanism.

Do NOT reach for it when.

- Fault isolation across the consuming side matters more than throughput.
  Competing Consumers puts each unit of concurrency in its own process, so
  one crash costs one worker's in-flight messages, not the whole consumer
  fleet's. A dispatcher trades that isolation away for coordination.
- Messages within the stream must be processed in strict global order and the
  workload cannot be partitioned by a correlation key. Any dispatcher that
  runs more than one performer at a time breaks strict ordering; if ordering
  is non-negotiable, a single-threaded Polling Consumer or Event-Driven
  Consumer, or a partitioned dispatcher keyed by ordering key, is the correct
  shape instead.
- The consuming logic is itself the resource bottleneck, for example a
  process that is already CPU-bound on a single core doing the message
  processing. Adding a dispatcher on top of one CPU core adds coordination
  overhead without adding real parallelism; scale by adding processes across
  cores or machines instead.
- The team needs horizontal elastic scaling driven by an external autoscaler
  reacting to queue depth. Competing Consumers scales by adding or removing
  whole processes, which maps cleanly onto container or VM autoscaling.
  Scaling a single dispatcher's internal pool size in response to load
  usually means a restart or a runtime reconfiguration path that most
  autoscalers are not built to drive.
- The messaging infrastructure already provides broker-side load balancing
  with per-consumer prefetch limits, for example a competing-consumers group
  on a durable queue, and the team has no additional coordination need beyond
  spreading load. Layering an in-process dispatcher on top of broker-side
  balancing is two mechanisms doing the same job and is extra complexity for
  no benefit.

## 5. Structure

| Participant | Responsibility |
|---|---|
| Message Channel | The Point-to-Point Channel the dispatcher consumes from. The dispatcher is the sole consumer registered on this channel, whether it reads by polling or by an event-driven callback from the messaging client. |
| Dispatcher | Owns the receive loop or callback registration on the channel. Decides which performer instance handles the next message, applies the concurrency ceiling, and tracks in-flight work so it can drain gracefully or apply backpressure. |
| Performer | A worker that receives one message from the dispatcher and processes it to completion, independently of every other performer. Performers hold no shared mutable state with each other; anything they must share, a connection pool, a cache, lives above them, owned by the dispatcher or by the process. |
| Performer Pool | The bounded set of performer slots the dispatcher may use concurrently. Bounded either by a fixed count of long-lived worker threads or goroutines waiting on an internal queue, or by a semaphore that gates how many performer invocations may run at once. |
| Acknowledgment Boundary | The point at which a message is confirmed as durably handled to the broker. This must be tied to performer completion, not to dispatch, or a crash between dispatch and completion silently loses the message; see dimension 17 for the security and data-integrity consequence of getting this wrong. |
| Routing Rule (optional) | When performers are specialized rather than identical, a rule the dispatcher consults, typically a message-type or header lookup, to decide which pool a given message goes to. This is the point where Message Dispatcher composes with Content-Based Router (see dimension 13). |

## 6. ASCII structure diagram

```
                         +----------------------------+
                         |     Message Channel         |
                         |  (Point-to-Point Channel)    |
                         +--------------+---------------+
                                        |
                                        | single consumer
                                        v
                         +----------------------------+
                         |         Dispatcher          |
                         |  - receive loop / callback   |
                         |  - concurrency ceiling        |
                         |  - in-flight tracking         |
                         |  - optional routing rule       |
                         +---+-----------+-----------+---+
                             |           |           |
                     dispatch|   dispatch|   dispatch|
                             v           v           v
                     +-----------+ +-----------+ +-----------+
                     | Performer | | Performer | | Performer |
                     |    #1     | |    #2     | |    #N     |
                     +-----------+ +-----------+ +-----------+
                             |           |           |
                             +-----+-----+-----+-----+
                                   |           |
                                   v           v
                          +-----------------------+
                          |  downstream resource    |
                          |  (DB, API, next channel) |
                          +-----------------------+
```

## 7. Dynamics

The sequence below shows the steady-state flow, including the acknowledgment
boundary. The message is only confirmed to the broker after the performer
finishes, never at dispatch time, or a crash between the two points loses
work silently.

```
Channel        Dispatcher              Performer(k)         Downstream
   |                |                       |                    |
   |--- message --->|                       |                    |
   |                | (has free slot? yes)   |                    |
   |                |---- dispatch(msg) ---->|                    |
   |                |  (mark in-flight++)     |                    |
   |                |                        |--- process ------->|
   |                |                        |<-- result ---------|
   |                |<--- completion(msg) ---|                    |
   |                | (mark in-flight--)      |                    |
   |--- ack(msg) <--|                        |                    |
   |                |                        |                    |
```

When the pool is saturated, the dispatcher stops pulling from the channel
until a slot frees up, which is the backpressure path.

```
Channel        Dispatcher (pool full)       Performer(k)
   |                |                             |
   |    (dispatcher does not poll/receive)          |
   |                |                             |
   |                |<---- completion(msg) --------|
   |                | (slot freed, in-flight--)     |
   |--- next msg -->|                             |
   |                |---- dispatch(next msg) ------>|
```

A failure path matters as much as the happy path. If a performer raises an
unhandled exception, the dispatcher must catch it at the performer boundary,
never let it propagate up through the receive loop, and must still release
the pool slot and decide, based on the messaging system's retry contract,
whether to nack the message for redelivery, route it to a Dead Letter
Channel, or apply a Guaranteed Delivery retry policy.

## 8. Implementation variants

**Fixed worker-pool with an internal buffered queue.** The dispatcher owns a
pool of N long-lived worker threads (or goroutines, or async tasks) that each
loop reading from a shared internal queue. The receive loop reads from the
external channel and pushes onto that internal queue. This decouples the
external receive rate from the internal processing rate up to the queue's
capacity, at the cost of holding messages in memory that have already been
removed from the broker but are not yet acknowledged, which is a durability
risk if the process crashes with a full internal queue. This is the shape
Apache Camel's Threads EIP implements. Inserting `.threads(n)` into a route
submits the message to a thread pool that carries out the continued routing,
decoupling the thread that first received the message from the thread that
processes it further (verified 2026-08-02,
https://camel.apache.org/components/latest/eips/threads-eip.html).

**Semaphore-gated dispatch with no internal buffer.** The dispatcher acquires
a permit from a counting semaphore sized to the pool limit before pulling the
next message from the channel at all, so nothing is ever removed from the
broker without an available performer slot already reserved. This variant has
a smaller durability blast radius than the buffered-queue variant, since
there is no window where messages sit acknowledged-but-unprocessed in an
internal buffer, but it can leave the channel's own prefetch or receive
mechanism idle for a moment between a permit being released and the next
receive call, a small throughput cost most systems accept for the durability
benefit.

**Type-routed dispatch to specialized pools.** The dispatcher inspects a
routing property, usually a message-type header, before choosing which of
several independently sized pools to dispatch into. This is the composition
with Content-Based Router described in dimension 13. A video-transcode pool
sized to CPU core count sits alongside a webhook-delivery pool sized much
larger, because I/O-bound work tolerates far more concurrency per core than
CPU-bound work does.

**Dataflow-block dispatch.** In the .NET Task Parallel Library Dataflow
namespace, `ActionBlock<TInput>` is constructed with a delegate to invoke per
message and an `ExecutionDataflowBlockOptions.MaxDegreeOfParallelism`, and
callers post messages to it with `Post` or `SendAsync`; the block internally
buffers, dispatches to its configured degree of parallelism, and exposes a
`Completion` task for graceful drain (verified 2026-08-02,
https://learn.microsoft.com/en-us/dotnet/api/system.threading.tasks.dataflow.actionblock-1).
This is the fixed worker-pool variant expressed as a reusable, off-the-shelf
primitive rather than hand-rolled.

**Channel-fan-out dispatch (Go idiom).** Rather than an explicit dispatcher
object, Go code commonly expresses the same structure as a single reader
goroutine that reads from an inbound channel and writes to a second,
worker-owned channel that N worker goroutines all read from concurrently.
This fan-out shape, where several functions read from the same channel until
it closes, spreads work across a group of workers so CPU-bound and I/O-bound
work run in parallel, and it is documented directly in the Go blog's
pipelines article (verified 2026-08-02, https://go.dev/blog/pipelines). The
dispatcher role in this idiom is implicit. It is whichever goroutine owns
the channel that the workers all read from, and the pool bound is simply the
number of worker goroutines started.

**Executor-service dispatch (Java idiom).** `java.util.concurrent.ExecutorService`,
backed by a fixed thread pool from `Executors.newFixedThreadPool(n)`, plays
the dispatcher role when a message-receiving loop calls `submit()` for each
message it pulls off a channel; the executor's internal work queue and
worker-thread set are the performer pool, and back-pressure is achieved by
using a bounded queue implementation (such as `ArrayBlockingQueue`) paired
with a rejection policy, rather than the default unbounded queue.

## 9. Known production uses

**Apache Camel's Threads EIP.** Camel, the open-source integration framework
originally from the Apache Software Foundation, implements Message Dispatcher
directly as a routing DSL construct. Inserting `.threads(n)` into a route
definition hands subsequent processing off to a configurable thread pool,
decoupling the thread that consumed the message from the thread that
continues routing it, with the pool's core size, max size, and queue capacity
all independently configurable (verified 2026-08-02,
https://camel.apache.org/components/latest/eips/threads-eip.html).

**.NET's TPL Dataflow `ActionBlock<TInput>`.** Shipped by Microsoft as part
of the `System.Threading.Tasks.Dataflow` package, `ActionBlock<TInput>`
implements `ITargetBlock<TInput>`, buffers posted items, and invokes a
supplied delegate for each one with a configurable
`MaxDegreeOfParallelism`, which is the dispatcher's concurrency ceiling
expressed as a first-class constructor option (verified 2026-08-02,
https://learn.microsoft.com/en-us/dotnet/api/system.threading.tasks.dataflow.actionblock-1).
Microsoft's own worked example in that same documentation demonstrates timing
several computations run through an `ActionBlock` with a specified degree of
parallelism, which is the pattern's throughput trade-off made explicit and
measurable.

**Go's bounded worker-pool idiom in the standard toolchain's own
documentation.** The Go project's official blog, under go.dev, documents the
fan-out and bounded-parallelism idioms as the recommended way to distribute
work across goroutines reading from a shared channel, spreading CPU-bound
and I/O-bound work across a group of workers reading a common channel
(verified 2026-08-02, https://go.dev/blog/pipelines). This is not a single
library but a language-idiom pattern that the Go team itself publishes as
canonical guidance, which is why goroutine worker pools reading from a
shared channel are the default way Go services implement a message
dispatcher rather than reaching for an external library.

**MassTransit's concurrency-limited consumer configuration.** MassTransit, a
widely used open-source service bus abstraction for .NET running on top of
RabbitMQ, Azure Service Bus, and Amazon SQS, exposes `ConcurrentMessageLimit`
on its receive-endpoint configuration, which bounds how many messages a
single receive endpoint processes concurrently in-process, the dispatcher's
concurrency ceiling exposed as a configuration knob rather than requiring the
application author to hand-write a pool. This is engineering judgement about
a well-known open-source project's naming convention rather than a claim
independently re-verified against the live docs in this session, and a
reader building on it should confirm the exact configuration surface against
the current MassTransit documentation before depending on it.

## 10. Consequences

Positive:

- Raises throughput on a single logical consumer without multiplying the
  number of broker connections, database pools, or process-startup costs that
  Competing Consumers would multiply.
- Centralizes the concurrency ceiling and in-flight tracking in one place, so
  the whole consuming side of a channel can be paused, drained, or resized by
  changing one number rather than coordinating across a fleet of processes.
- Enables specialization. Different message types can be routed to
  differently sized or differently configured performer pools from the same
  physical channel, which Competing Consumers cannot do without splitting the
  channel itself.
- Makes backpressure a local, synchronous decision, whether or not to pull
  the next message, rather than a distributed decision requiring coordination
  across independent consumer processes.

Negative:

- Collapses fault isolation to the process boundary. A crash, an
  out-of-memory condition, or a deployment restart of the dispatcher process
  takes every currently in-flight performer down with it, which Competing
  Consumers, spread across independent processes, does not suffer.
- Adds a coordination surface, the pool, the ceiling, the in-flight tracking,
  the acknowledgment boundary, that is new code with its own bugs. A pool
  that leaks a permit on an exception path silently shrinks its own capacity
  over the process's lifetime until it deadlocks.
- Scaling beyond one machine's practical concurrency ceiling requires either
  running multiple dispatcher processes, which reintroduces Competing
  Consumers on top of the dispatcher pattern, or a much larger single
  machine.
- Strict global message ordering is lost the moment more than one performer
  can run at a time, and restoring it requires partitioning by a correlation
  key, adding real design complexity back into the pattern.

## 11. Failure modes and misuse

**Symptom.** The process's memory grows without bound over hours and
eventually OOM-kills. **Cause.** The dispatcher variant uses an unbounded
internal queue between the receive loop and the worker pool, so a sustained
burst where the arrival rate exceeds the processing rate accumulates
in-memory backlog instead of applying backpressure to the channel. **Fix.**
Switch to a bounded internal queue, or to the semaphore-gated variant with no
internal buffer at all, and size the bound to the memory budget the process
is actually allotted.

**Symptom.** Messages are occasionally lost entirely after a crash or a pod
restart, with no trace in a dead-letter destination. **Cause.** The
acknowledgment is issued to the broker at dispatch time rather than at
performer completion time, so a message that was pulled off the channel and
handed to a performer, but not yet finished, is already durably removed from
the broker when the process dies; nobody redelivers it. **Fix.** Move the
acknowledgment call to the performer's completion callback, on both the
success and the failure path, so a crash before completion leaves the
message unacknowledged and eligible for broker redelivery.

**Symptom.** Throughput plateaus far below the configured pool size, and CPU
usage on the consuming process stays low. **Cause.** The performer's actual
bottleneck is a shared downstream resource with its own concurrency limit,
commonly a database connection pool smaller than the dispatcher's pool size,
so most performers spend their time blocked waiting for a connection rather
than doing work; the dispatcher pool is not the bottleneck the operator
assumed it was. **Fix.** Size every shared downstream resource pool to be at
least as large as the dispatcher's concurrency ceiling, or size the ceiling
down to match the smallest downstream pool in the call path.

**Symptom.** A single malformed or unusually large message causes the whole
pool to stall, and healthy messages sitting behind it in the channel are
delayed even though the pool has free performer slots. **Cause.** No
per-message timeout is applied inside the performer, so a message that
triggers an unbounded retry loop, a hung downstream call, or an infinite
parse loop occupies its performer slot forever, and repeating this across
enough malformed messages exhausts the pool even though most in-flight work
would otherwise finish quickly. **Fix.** Wrap every performer invocation in a
hard timeout, and route anything that exceeds it to a Dead Letter Channel
rather than letting it hold a slot indefinitely.

**Symptom.** During a rolling deployment, some percentage of in-flight
messages are processed twice, visible as duplicate downstream side effects.
**Cause.** The process receives a shutdown signal and exits before the
in-flight performers finish and their completions reach the acknowledgment
boundary, so the broker redelivers those messages to the next instance,
which processes them again from the start. **Fix.** Implement a graceful
drain on shutdown signal. Stop pulling new messages from the channel
immediately, wait for currently in-flight performers to reach their
completion callback up to a bounded grace period, and only then exit; pair
this with idempotent performer logic as a second line of defense, since a
drain deadline that is exceeded will still redeliver.

## 12. Trade-off matrix

| Force | Message Dispatcher | Competing Consumers | Polling Consumer (single-threaded) |
|---|---|---|---|
| Throughput ceiling | Bounded by one process's practical concurrency; raise it by widening the pool, up to the machine's resource limits | Bounded by however many independent consumer processes are run; raises with horizontal scale | Bounded by one message at a time; lowest of the three |
| Fault isolation | Weak; one process crash takes down every in-flight performer at once | Strong; a crash in one consumer process only loses that process's in-flight messages | Strongest; only ever one message in flight to lose |
| Coordination cost | Low; the pool, ceiling, and in-flight tracking live in one process's memory | Higher; requires the broker's own competing-consumer delivery semantics and per-consumer prefetch tuning to avoid one slow consumer hogging messages | None; there is nothing to coordinate |
| Message ordering | Broken across performers unless partitioned by a correlation key | Broken across consumer instances the same way | Preserved, by construction |
| Operational footprint | One process to deploy and monitor per logical consumer | N processes to deploy, monitor, and keep configuration-consistent | One process, but under-provisioned for any real throughput need |
| Specialization by message type | Native; route to differently sized pools from the routing rule | Requires splitting into separate channels or separate consumer groups per type | Not applicable; there is no concurrency to specialize |

## 13. Related and incompatible patterns

**Competing Consumers** is the horizontal-scaling sibling. Where Message
Dispatcher applies concurrency inside one process, Competing Consumers
applies it across several independent processes on the same channel. The EIP
catalog lists them side by side as the two answers to the same coordination
question, and Hohpe and Woolf's own related-patterns list for Message
Dispatcher names Competing Consumers first (verified 2026-08-02,
https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageDispatcher.html).
The two compose. A fleet of dispatcher processes, each internally running a
worker pool, is Competing Consumers of Message Dispatchers, and this is a
common production shape for genuinely high-throughput systems that need both
horizontal scale and per-process resource efficiency.

**Content-Based Router** composes with the type-routed dispatch variant from
dimension 8. The dispatcher's routing rule, deciding which specialized
performer pool a message goes to, is a small, in-process instance of the
Content-Based Router pattern, evaluated once per message rather than sitting
as a separate messaging-infrastructure hop.

**Claim Check** is named directly in the Enterprise Integration Patterns
site's related-patterns list for Message Dispatcher (verified 2026-08-02,
https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageDispatcher.html),
and the relationship is practical. When performers process large message
bodies concurrently, holding the full payload in memory for every in-flight
performer multiplies memory pressure by the pool size, so a dispatcher
processing large payloads commonly combines with Claim Check, storing the
body externally and dispatching only a lightweight reference.

**Transactional Client** is the other pattern the Enterprise Integration
Patterns site lists alongside Message Dispatcher, and it addresses the
acknowledgment-boundary failure mode from dimension 11 directly. A dispatcher
whose performer work and message acknowledgment must be atomic with a
database write needs the Transactional Client pattern's guidance on
coordinating the local transaction with the broker's acknowledgment, rather
than treating them as two independent steps that can diverge on a crash.

**Polling Consumer and Event-Driven Consumer** describe the two ways the
dispatcher itself can be fed. A dispatcher's receive loop is either a Polling
Consumer, actively calling receive in a loop, or the dispatcher is wired as
the callback target of an Event-Driven Consumer, invoked by the messaging
client whenever a message arrives. Both appear in the Enterprise Integration
Patterns site's related list for Message Dispatcher (verified 2026-08-02,
https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageDispatcher.html),
and the choice between them is orthogonal to the dispatcher pattern itself;
it determines how messages enter the dispatcher, not how the dispatcher
distributes them once they arrive.

**Incompatible with strict FIFO ordering guarantees at the pattern level**,
in the specific sense that using more than one performer at a time, which is
the entire point of the pattern, structurally breaks a guarantee that
message N always completes before message N+1 begins. This is not a
composition failure with a named alternative pattern so much as a direct
tension. A system that needs both concurrency and strict ordering must
partition its work by an ordering key first, so that ordering is only
guaranteed within a partition, and dispatch each partition to a single
performer while other partitions run concurrently on other performers.

## 14. Refactoring path in and out

**Introducing it.** Start from a working single-threaded Polling Consumer or
Event-Driven Consumer that is falling behind its channel's arrival rate.
First, measure. Confirm the bottleneck is genuinely per-message processing
time and not, for example, a downstream resource limit that adding
concurrency would only shift the queueing to. Second, extract the per-message
processing logic into a pure function or method that takes a message and
returns a result, with no dependency on being called from a specific thread;
this is a prerequisite, because the extraction surfaces any hidden shared
mutable state that the single-threaded version was implicitly protected from
by never running concurrently. Third, introduce the bounded pool, sized
conservatively, for example to the number of available CPU cores for CPU-bound
work, or to a small multiple of that for I/O-bound work, and wire the receive
loop to dispatch into it rather than calling the processing function
directly. Fourth, move the acknowledgment call from immediately after receive
to the performer's completion callback, per the failure mode in dimension 11.
Fifth, add a graceful-shutdown drain and confirm the process handles a
shutdown signal cleanly under load, before it takes real traffic. Sixth,
load-test at the target throughput and watch downstream resource pools for
saturation before widening the dispatcher pool further.

**Removing it.** A dispatcher earns removal when the coordination it
provides is no longer needed, most often because the workload moved to a
platform, a serverless function invoked per message, or a managed queue
consumer with autoscaling, that already provides bounded concurrency at the
infrastructure layer, making the in-process pool redundant. To remove it,
first confirm the platform's own concurrency control matches what the
dispatcher was providing, most importantly the acknowledgment-on-completion
guarantee and any ordering-by-partition-key behavior the dispatcher had
implemented. Then collapse the dispatcher and its pool back to a single
per-invocation call, since the platform is now the pool. Finally, verify that
any downstream resource pools that were sized to the old in-process
dispatcher's ceiling are re-sized to whatever concurrency ceiling the
platform now provides, since removing the dispatcher does not remove the
need to think about that ceiling; it only moves where it lives.

## 15. Testing and verification

Judgement. The specific techniques below reflect established practice for
testing concurrent dispatch code rather than a single canonical source, and
some tool availability is stack-specific.

Test the dispatcher's routing and pooling logic separately from the
performer's business logic. Give the dispatcher a fake or in-memory channel
that yields a controlled sequence of messages, and a set of performer stubs
that record which messages they received and when, and assert on the
dispatcher's behavior, whether it respects the concurrency ceiling, whether
it stops pulling from the channel when the pool is saturated, and whether it
routes to the correct performer pool when the routing rule is exercised with
each message type. This isolates the coordination logic, which is where the
pattern's own bugs live, from the performer logic, which is ordinary business
logic testable the same way it would be tested if it were called directly.

For the concurrency ceiling specifically, write a test that submits more
messages than the pool size at once and asserts, using a counter of
currently-active performer invocations guarded by an atomic or a mutex, that
the observed concurrent count never exceeds the configured ceiling at any
point during the test, not merely that the total count is eventually
correct; a race that only shows up under a specific interleaving will not be
caught by asserting final state alone. Where the language's toolchain
supports it, run this test under a data-race detector, for example Go's
`-race` flag or a similar sanitizer, to catch data races on the shared
in-flight counter that a single passing run would not expose.

Test the acknowledgment boundary by simulating a performer that fails or
throws partway through, and asserting that the message is nacked or routed
to a dead-letter destination, never silently acknowledged as successful and
never left in an ambiguous state. Test the graceful-shutdown drain by
starting a dispatch, sending the shutdown signal mid-flight, and asserting
that the in-flight performer is allowed to finish before the process reports
itself stopped, up to the configured grace period, and that a performer
still running past the grace period is handled per whatever policy the code
defines for it, whether that is a forced cancellation or a logged warning.

Use property-based testing where the language's ecosystem supports it to
generate random message-arrival orderings, random performer processing
durations, and random failure injections, and assert the invariant that the
concurrency ceiling is never exceeded and that every dispatched message is
eventually either acknowledged or routed to a dead-letter destination, never
lost silently.

## 16. Observability signals

A healthy dispatcher exposes several signals at minimum. The current
in-flight performer count sits against the configured ceiling, so an
operator can see at a glance whether the pool is running hot. The depth of
any internal buffering queue should sit near zero in steady state and only
grow during a burst, returning to zero once the burst clears, since a queue
depth that trends upward over time under steady load is the leading
indicator of the unbounded-growth failure mode from dimension 11. The rate of
messages dispatched per second should track the rate of messages completed
per second, where a sustained gap between the two signals the pool is
falling behind. And the distribution of per-performer processing latency
matters on its own, since a rightward shift in the tail of that distribution,
even while the median stays flat, is often the first sign of the
shared-downstream-resource-contention failure mode also described in
dimension 11.

Log, at debug level in steady state and at warn level when it happens, every
time the dispatcher declines to pull the next message because the pool is
saturated, with the current in-flight count attached, so a burst that
triggers sustained backpressure is visible in logs even before it shows up
as a queue-depth alert. Log, always, every message that is nacked or routed
to a dead-letter destination, with the message's identifier and the reason,
since this is the audit trail an operator needs to answer "what happened to
message X" after the fact.

Trace each dispatched message with a span that starts at dispatch and ends
at the acknowledgment boundary, carrying the performer's identifier or index
as an attribute, so that a distributed tracing system can show, per message,
how long it waited in the dispatcher before a performer slot was free versus
how long the performer itself took, which distinguishes a dispatcher-side
bottleneck from a performer-side one at a glance in the trace waterfall.

A failing instance looks like a widening gap between dispatch rate and
completion rate on the dashboard described above, paired with either a
climbing in-flight count pinned at the ceiling, which means the pool is
saturated and the bottleneck is downstream, or a climbing internal queue
depth with the in-flight count well below the ceiling, which means the
performers are keeping up but the receive rate is outpacing them, and the
ceiling itself needs raising if resources allow, or the upstream producer
needs throttling if they do not.

## 17. Security and privacy implications

Judgement. The concerns below are analytical, drawn from the pattern's
structure, rather than citations of a specific published security review of
the dispatcher pattern by name.

Concurrency multiplies the blast radius of any per-message vulnerability. If
a single malformed message can trigger a resource-exhaustion condition in
one performer, running many performers concurrently means an attacker who
controls message content, directly or via a compromised upstream producer,
can trigger that condition on every performer slot simultaneously with a
single burst, turning a per-message denial-of-service bug into a
whole-process outage far faster than a single-threaded consumer would allow.
The per-message timeout described in dimension 11's failure modes is also a
security control for this reason, not only a resilience one.

Shared state across performers is the second concern. Because performers
run inside one process by design, anything they share, a connection pool, an
in-memory cache, a rate limiter, becomes a place where one message's
processing can influence another's outcome or leak data across message
boundaries if that shared state is not carefully scoped. A cache keyed
incorrectly, for example keyed on a value that is not actually unique per
tenant in a multi-tenant system, can leak one tenant's data to another
tenant's concurrently running performer, a failure mode that a fully isolated
per-process Competing Consumers architecture makes structurally harder to
introduce because there is no shared in-process cache to key incorrectly in
the first place.

Message content that flows through a dispatcher and its performer pool
should be treated as though it will, at some point, be inspected in logs,
traces, or dead-letter storage for debugging purposes, since the
observability guidance in dimension 16 explicitly recommends logging message
identifiers and failure reasons; if messages carry sensitive payloads, the
identifiers logged should be opaque correlation identifiers rather than
fields that themselves carry personal or sensitive data, and any dead-letter
destination the dispatcher routes failed messages to needs the same access
controls and retention policy as the primary channel, since a message that
fails processing has not thereby become less sensitive.

Finally, the acknowledgment-boundary discipline from dimension 11 has a
data-integrity dimension that borders on a security concern in regulated
contexts. Acknowledging a message before its processing is durably complete
means a crash can silently drop data that a downstream audit or compliance
process assumed was processed, which in a payments or healthcare context is
not merely a bug but a real compliance gap, making the correct
acknowledgment-on-completion implementation a control worth naming explicitly
in any security or compliance review of a system built on this pattern.

## 18. References

- Hohpe, Gregor and Woolf, Bobby. "Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions." Addison-Wesley, 2003. Messaging
  Endpoints chapter, Message Dispatcher pattern.
- Enterprise Integration Patterns website, Message Dispatcher pattern page.
  https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageDispatcher.html
  Verified 2026-08-02.
- Apache Camel, Threads EIP documentation, current version.
  https://camel.apache.org/components/latest/eips/threads-eip.html
  Verified 2026-08-02.
- Microsoft Learn, `System.Threading.Tasks.Dataflow.ActionBlock<TInput>` Class
  reference. https://learn.microsoft.com/en-us/dotnet/api/system.threading.tasks.dataflow.actionblock-1
  Verified 2026-08-02.
- The Go Blog, "Go Concurrency Patterns. Pipelines and cancellation."
  https://go.dev/blog/pipelines
  Verified 2026-08-02.
- MassTransit documentation, receive-endpoint concurrency configuration.
  Cited as engineering judgement about a known open-source project's
  configuration surface; not independently re-verified against the live
  documentation in this session, and should be confirmed against the current
  MassTransit docs before being relied on for exact API names.

## Code examples

### TypeScript, semaphore-gated dispatcher with a bounded worker pool

```typescript
type Handler<T> = (message: T) => Promise<void>;

class Dispatcher<T> {
  private inFlight = 0;
  private readonly waiters: Array<() => void> = [];

  constructor(
    private readonly capacity: number,
    private readonly handler: Handler<T>,
  ) {
    if (capacity <= 0) {
      throw new Error("capacity must be positive");
    }
  }

  async dispatch(message: T): Promise<void> {
    await this.acquireSlot();
    this.inFlight += 1;
    try {
      await this.handler(message);
    } finally {
      this.inFlight -= 1;
      this.releaseSlot();
    }
  }

  private acquireSlot(): Promise<void> {
    if (this.inFlight < this.capacity) {
      return Promise.resolve();
    }
    return new Promise((resolve) => this.waiters.push(resolve));
  }

  private releaseSlot(): void {
    const next = this.waiters.shift();
    if (next) {
      next();
    }
  }

  get activeCount(): number {
    return this.inFlight;
  }
}

async function demo(): Promise<void> {
  const processed: number[] = [];
  const dispatcher = new Dispatcher<number>(2, async (id) => {
    await new Promise((r) => setTimeout(r, 20));
    processed.push(id);
  });

  const messages = [1, 2, 3, 4, 5];
  await Promise.all(messages.map((m) => dispatcher.dispatch(m)));

  console.log("processed order", processed.length, "messages, all done");
  console.log("active in-flight after drain", dispatcher.activeCount);
}

demo();
```

### Python, thread-pool dispatcher with a bounded internal queue

```python
import queue
import threading
import time
from dataclasses import dataclass


@dataclass
class Message:
    id: int
    payload: str


class Dispatcher:
    def __init__(self, worker_count: int, handler):
        self._queue: "queue.Queue[Message | None]" = queue.Queue(maxsize=worker_count * 2)
        self._handler = handler
        self._workers = [
            threading.Thread(target=self._run_worker, daemon=True)
            for _ in range(worker_count)
        ]
        for w in self._workers:
            w.start()

    def _run_worker(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                self._queue.task_done()
                return
            try:
                self._handler(item)
            finally:
                self._queue.task_done()

    def dispatch(self, message: Message) -> None:
        self._queue.put(message)

    def drain_and_stop(self) -> None:
        self._queue.join()
        for _ in self._workers:
            self._queue.put(None)
        for w in self._workers:
            w.join()


def main() -> None:
    results: list[int] = []
    lock = threading.Lock()

    def handle(msg: Message) -> None:
        time.sleep(0.02)
        with lock:
            results.append(msg.id)

    dispatcher = Dispatcher(worker_count=3, handler=handle)
    for i in range(6):
        dispatcher.dispatch(Message(id=i, payload=f"order-{i}"))

    dispatcher.drain_and_stop()
    print(f"processed {len(results)} messages, ids={sorted(results)}")


if __name__ == "__main__":
    main()
```

### Go, channel-based worker-pool dispatcher

```go
package main

import (
	"fmt"
	"sync"
)

type Message struct {
	ID      int
	Payload string
}

type Dispatcher struct {
	inbox   chan Message
	handler func(Message) int
	wg      sync.WaitGroup
}

func NewDispatcher(workerCount int, handler func(Message) int) *Dispatcher {
	d := &Dispatcher{
		inbox:   make(chan Message, workerCount*2),
		handler: handler,
	}
	for i := 0; i < workerCount; i++ {
		d.wg.Add(1)
		go d.worker()
	}
	return d
}

func (d *Dispatcher) worker() {
	defer d.wg.Done()
	for msg := range d.inbox {
		d.handler(msg)
	}
}

func (d *Dispatcher) Dispatch(msg Message) {
	d.inbox <- msg
}

func (d *Dispatcher) DrainAndStop() {
	close(d.inbox)
	d.wg.Wait()
}

func main() {
	var mu sync.Mutex
	processed := make([]int, 0, 6)

	handler := func(msg Message) int {
		mu.Lock()
		processed = append(processed, msg.ID)
		mu.Unlock()
		return msg.ID
	}

	dispatcher := NewDispatcher(3, handler)
	for i := 0; i < 6; i++ {
		dispatcher.Dispatch(Message{ID: i, Payload: fmt.Sprintf("order-%d", i)})
	}
	dispatcher.DrainAndStop()

	fmt.Printf("processed %d messages\n", len(processed))
}
```

Code was run and verified during authoring. The TypeScript sample compiled
with `npx tsc --strict --target es2020 --module commonjs` and ran under
`node`, printing `processed order 5 messages, all done` and
`active in-flight after drain 0`. The Python sample ran under `python3`,
printing `processed 6 messages, ids=[0, 1, 2, 3, 4, 5]`. The Go sample was
built and run with `go run`, printing `processed 6 messages`.

Swift and Rust are omitted for this entry. The pattern's structural core, a
bounded pool consuming from a shared source, is not idiomatically different
in either language from the Go or TypeScript async shapes already shown
(Swift's `AsyncStream` plus a `TaskGroup` limited by a semaphore, or Rust's
`tokio::sync::Semaphore` paired with `mpsc::channel`, both reproduce the same
structure as the samples above with only syntax differing), and adding them
would not surface a new idiomatic variant worth the reader's time; Java is
omitted because `ExecutorService` with a fixed thread pool, described in
dimension 8, is a direct off-the-shelf implementation of this exact pattern
and reproducing it as a hand-written sample would only restate the JDK's own
API rather than demonstrate a distinct idiom.
