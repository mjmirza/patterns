---
name: Backpressure
slug: backpressure
family: 09-concurrency
category: Concurrency
aliases: [Flow Control, Rate Limiting via Feedback, Bounded Buffering, Pull-Based Streaming]
first_described: "Postel, RFC 793, 1981 (TCP sliding window); Reactive Streams JVM SIG, 2013-2015 (application-level formalization)"
maturity: canonical
related: [producer-consumer, bounded-buffer, circuit-breaker, bulkhead, rate-limiter, thread-pool, event-loop, actor-model, load-shedding, pull-based-iteration]
incompatible_with: [fire-and-forget-messaging, unbounded-queue]
verified: 2026-08-02
---

# Backpressure

## 1. Name, aliases, and lineage

Backpressure is the mechanism by which a consumer signals to a producer that it
cannot currently accept more work, so the producer slows, pauses, or sheds
input instead of overwhelming the consumer's buffer, memory, or downstream
resource. The word is borrowed directly from fluid dynamics, where backpressure
is the resistance a pump feels when the pipe downstream is restricted. In
software the metaphor is exact, a fast producer pushing into a slow consumer is
a pump pushing into a restricted pipe, and something has to give. the buffer
grows without bound, data is dropped, or the producer is told to slow down.

The mechanism is older than the name. TCP's sliding window, described in Jon
Postel's original RFC 793 in 1981 and carried forward unchanged in structure by
RFC 9293, the 2022 consolidation of the TCP specification, is a backpressure
protocol at the transport layer decades before the term entered common use in
application programming. The RFC 9293 specification defines the receive
window, RCV.WND, as the amount of sequence space the receiver is currently
willing to accept, and the sender's transmittable window is bound by that
value (RFC 9293, section 3.3.1, Key Connection State Variables, verified
2026-08-02, https://www.rfc-editor.org/rfc/rfc9293.html). The Window field in
the TCP header, section 3.1 of the same document, is described as "the number
of data octets beginning with the one indicated in the acknowledgment field
that the sender of this segment is willing to accept" (RFC 9293, section 3.1,
verified 2026-08-02). That single field, updated on every acknowledgment, is a
continuous, cheap signal from receiver to sender, and it is the direct
ancestor of every application-level backpressure protocol that followed.

The term entered mainstream application programming through reactive
programming. The Reactive Streams initiative, formed in 2013 by engineers from
Netflix, an early cloud-platform company, Lightbend, and others, produced a
JVM specification in 2015 whose stated purpose is "to provide a standard for
asynchronous stream processing with non-blocking back pressure"
(reactive-streams.org, Overview, verified 2026-08-02,
https://www.reactive-streams.org/). That specification gave the pattern its
modern vocabulary. a Publisher emits, a Subscriber consumes, and a
Subscription carries a `request(n)` call that the Subscriber uses to tell the
Publisher exactly how many more elements it is prepared to receive. The spec
states plainly that "back pressure is an integral part of this model in order
to allow the queues which mediate between threads to be bounded" and that
"the communication of back pressure [must be] fully non-blocking and
asynchronous" (reactive-streams.org, Overview, verified 2026-08-02). Node.js
streams settled on a different vocabulary for the same idea a few years
earlier, a writable stream's `write()` method returns `false` once its
internal buffer reaches a configured `highWaterMark`, and the caller is
expected to stop writing until a `drain` event fires (Node.js documentation,
Stream, Writable streams, verified 2026-08-02,
https://nodejs.org/api/stream.html). Aliases in wide use today include flow
control, the network and messaging-system term, rate limiting via feedback,
distinguishing it from a fixed-quota rate limiter that has no idea what the
consumer can actually absorb, bounded buffering, the mechanism most often used
to implement it, and pull-based streaming, the architectural style,
exemplified by Reactive Streams and by Go channels, where the consumer drives
the pace by asking for work rather than the producer pushing it unsolicited.

## 2. Problem and context

Every pipeline has at least two speeds, the rate at which work arrives and the
rate at which work can be processed. When those rates are equal the pipeline
runs in steady state and nobody notices any pattern is present. The moment the
arrival rate exceeds the processing rate, even briefly, something has to give.

Exactly one of four things follows, and a system that has not deliberately
chosen one of them gets whichever one its runtime defaults to, usually the
worst one. The excess work can queue up somewhere, consuming memory that grows
without bound until the process is killed by an out-of-memory condition or the
operating system's OOM killer. The excess work can be silently dropped, which
corrupts correctness for any workload that assumes at-least-once delivery. The
producer can be blocked or slowed until the consumer catches up, trading
throughput for stability. Or the excess work can be explicitly rejected with a
signal the producer can act on, trading some throughput for the ability to
fail predictably and visibly. Backpressure is the pattern that deliberately
chooses between the third and fourth outcome and rejects the first two.

This problem shows up whenever two components with different, and especially
variable, throughputs are connected. a web server accepting HTTP requests
faster than a downstream database can commit transactions, a message consumer
pulling from a queue faster than it can call an external API that rate-limits
it, a video encoder producing frames faster than a network socket can transmit
them, a log shipper tailing a file faster than the ingestion cluster can index
it, or simply a fast CPU-bound stage in a pipeline feeding a slow I/O-bound
stage. The problem is not that the slow stage is slow, slowness is often an
unavoidable property of the work, a database write has a lower bound set by
disk fsync latency, a network call has a lower bound set by round-trip time.
The problem is that nothing in the system tells the fast stage to stop, so the
fast stage keeps producing at its own natural rate until something downstream
breaks.

The context in which this becomes acute, rather than a theoretical concern, is
any system with a queue, buffer, or channel sitting between an unthrottled
producer and a rate-limited consumer, especially where the producer's own rate
is itself variable or bursty. A batch job that reads ten records a second from
a file and writes them one at a time to a database with a hundred-millisecond
write latency does not need backpressure, the arithmetic never goes wrong. A
web service accepting requests from the public internet, where request volume
can spike by two orders of magnitude in under a minute, absolutely needs it,
because the moment arrival rate crosses the service's saturation point, an
unbounded queue turns a transient spike into an unrecoverable memory
exhaustion, and every request already queued behind the spike experiences
latency that has nothing to do with how long its own processing actually
takes.

## 3. Forces

**Throughput versus memory safety.** An unbounded queue maximizes throughput
in the short term, absorbing any burst without ever telling the producer to
slow down, but at the cost of unbounded memory growth under sustained
overload. A bounded queue with backpressure caps memory but necessarily caps
throughput at the consumer's processing rate the moment the buffer fills,
because the alternative to capping throughput is dropping or crashing.

**Latency versus utilization.** Backpressure that blocks the producer the
instant the buffer fills keeps the buffer, and therefore queueing latency, as
small as possible, but it can leave the consumer briefly idle between wake-ups
if the signaling has any round-trip cost, lowering utilization. A larger
buffer smooths out utilization and absorbs jitter between producer and
consumer, but every item sitting in that buffer is accruing latency it did not
need to accrue, a direct consequence of Little's Law, mean items in system
equals arrival rate times mean time in system, which any capacity-planning
discussion of backpressure eventually has to reckon with.

**Coupling versus efficiency.** Backpressure necessarily couples the producer
to the consumer's pace, at least loosely. That coupling is the entire point,
but it means a slow consumer directly determines the effective throughput of
everything upstream of it, which can propagate a local slowdown into a
system-wide one if every stage in a pipeline applies backpressure honestly.
This propagation is a feature when the goal is protecting the weakest link,
and a liability when the goal is isolating failures, which is why
backpressure and the bulkhead pattern are frequently paired, see dimension 13.

**Push versus pull.** A push-based system, the producer sends whenever it has
data, needs an explicit signal from the consumer to implement backpressure, a
message, a return value, a blocked write. A pull-based system, the consumer
requests the next item, or the next `n` items, and the producer only sends
that many, has backpressure built into its control flow by construction,
because the producer structurally cannot send more than has been requested.
Reactive Streams chose pull with a numeric `request(n)` specifically because a
correct pull-based protocol cannot silently violate its own backpressure
contract the way a push-based protocol relying on discipline can.

**Operability and observability.** A system with backpressure applied
correctly degrades visibly, queue depth rises, request latency rises, and
these are things a dashboard can show and an alert can fire on well before
anything breaks. A system without backpressure degrades invisibly right up
until the moment memory is exhausted or the process is killed, at which point
the failure is total rather than gradual. This makes backpressure not only a
stability mechanism but an observability one, discussed further in dimension
16.

**Cost.** Backpressure is not free to implement. It requires a bounded buffer,
memory allocated up front, or a data structure with capacity tracking, a
signaling channel from consumer back to producer, which itself needs to be
reliable and low-latency to be useful, and, in distributed systems, careful
thought about what the producer does when it is told to slow down, whether
that means blocking a thread, buffering locally, or rejecting the caller.
Every one of these has an engineering cost that a naive unbounded queue does
not incur until the moment it fails.

## 4. Applicability and non-applicability

Apply backpressure when:

- A producer and a consumer are connected by any kind of buffer, queue, or
  channel, and the producer's rate can exceed the consumer's rate under
  realistic conditions, not merely in a worst case that will never happen.
- The system must survive sustained overload without unbounded memory growth,
  which is true of essentially any long-running server process handling
  external traffic.
- The correctness of the system depends on not silently dropping work, so
  "just drop excess items", a load-shedding strategy, related but distinct,
  see dimension 13, is not acceptable and the alternative must be to slow the
  producer.
- The producer is capable of usefully slowing down, meaning it has its own
  upstream, a network client, a job scheduler, a human clicking a button, that
  can itself absorb the producer being slower, rather than the producer being
  a fixed-rate hardware source that cannot pause, see the non-applicability
  case below for the exception.
- Multiple stages are chained into a pipeline and the goal is for the whole
  pipeline's throughput to be governed by its slowest stage rather than by
  its fastest one racing ahead and exhausting memory at every intermediate
  step.

Do NOT apply backpressure, or apply a different pattern instead, when:

- The producer is a real-time hardware source that fundamentally cannot be
  slowed, an audio device sampling at a fixed clock rate, a sensor emitting on
  a fixed interval, a video capture card. Here the correct pattern is a
  bounded ring buffer with an explicit, deliberate overwrite or drop policy,
  the newest sample overwrites the oldest, a policy sometimes called
  drop-oldest backpressure, or more accurately load shedding at the edge,
  because there is no way to tell a physical clock to wait.
- The correctness requirement is the opposite of what backpressure protects.
  Some systems must never let a slow consumer delay a producer, for example a
  safety interlock emitting a shutdown signal, where a consumer being slow to
  acknowledge must never cause the signal to be held back. Fire-and-forget or
  at-most-once delivery, explicitly accepting loss over delay, is the correct
  choice there, not backpressure.
- The two rates are known, fixed, and the consumer is provably always faster
  than the producer under every realistic load, in which case the buffer
  never fills and backpressure machinery adds implementation and cognitive
  cost for a scenario that will not occur. A batch ETL job with a fixed input
  size and a consumer with headroom is such a case, though this determination
  should be revisited whenever the input volume assumption changes.
- The consumer's slowness is actually a bug, an accidental infinite loop, a
  deadlock, a leaked resource, rather than genuine saturation. Backpressure
  will faithfully propagate the symptom of that bug upstream, everything
  stalls, without fixing the bug, and can make the underlying failure harder
  to diagnose because the visible symptom becomes "the whole pipeline is
  slow" rather than "component X is stuck". A circuit breaker or a timeout,
  not backpressure, is the pattern that detects and isolates that failure
  mode, see dimension 13.
- Distributed messaging where the producer and consumer do not share process
  memory and a blocking backpressure signal would require the producer to
  hold a network connection open indefinitely. Here backpressure is usually
  implemented as bounded queue depth plus consumer-driven pull, Kafka's
  `poll()` model, see dimension 9, rather than a synchronous block, because a
  synchronous block across a network boundary turns a slow consumer into a
  resource leak on the producer's side, one blocked connection per slow
  consumer, instead of solving the problem.

## 5. Structure

- **Producer.** The component generating items faster, or with more bursty
  variance, than the consumer can reliably absorb. Responsible for either
  respecting a backpressure signal, pausing, blocking, or reducing its own
  rate, or for shedding load itself when the signal says it cannot proceed.
- **Bounded buffer, or channel.** The intermediary with a fixed capacity that
  holds items between production and consumption. Its capacity is the single
  most consequential tuning parameter in the whole pattern, too small and
  throughput suffers from excessive round-trips of the signaling mechanism,
  too large and the pattern degenerates toward an unbounded queue's failure
  mode with a longer fuse rather than a fixed one.
- **Consumer.** The component processing items at its own natural rate,
  responsible for emitting the backpressure signal, explicitly, a
  `request(n)` call, a pause and resume API call, or implicitly, a blocking
  read from a full channel simply stalls the writer without any separate
  message.
- **Signal channel.** The mechanism by which the consumer's state, buffer
  full, buffer draining, demand for n more items, reaches the producer. This
  can be the same channel the data flows through, as in TCP, where the window
  field rides on the same segments as data, or a separate one, an explicit
  `request(n)` method call, a separate control-plane message in a messaging
  system, a return value from a write call.
- **Overflow policy.** What happens at the boundary condition, when the
  producer is told to stop but cannot, or has already produced before the
  signal arrives. Common policies. block the producer's thread or coroutine,
  buffer locally on the producer side up to a further bound, drop the newest
  item, drop the oldest buffered item to make room, sometimes used for
  latest-value-only data like sensor readings, or reject the request entirely
  and surface an error to whatever is upstream of the producer.

## 6. ASCII structure diagram

```
                    capacity = N
        +------------------------------+
        |         BOUNDED BUFFER        |
        |  [ ][ ][ ][x][x][x][x][ ][ ]  |
        +------------------------------+
             ^                    |
   put/write |                    | get/read
             |                    v
   +-------------+          +-------------+
   |  PRODUCER   |          |  CONSUMER   |
   | faster rate |          | slower rate |
   +-------------+          +-------------+
             ^                    |
             |   signal channel   |
             +--------------------+
             "buffer full, stop"  or
             "request(n) more items" or
             write() returns false

   Overflow policy fires only when the producer
   cannot honor the signal in time:

   +-------------+     +-----------------------+
   | overflow    | --> | block | drop | reject  |
   +-------------+     +-----------------------+
```

## 7. Dynamics

```
Producer                 Buffer(cap=N)              Consumer
   |                          |                          |
   |--- put(item1) --------->| [item1]                   |
   |<--- ok -------------------|                          |
   |                          |                          |
   |--- put(item2) --------->| [item1,item2]              |
   |<--- ok -------------------|                          |
   |                          |------- get() ------------>|
   |                          |<------ item1 --------------|
   |                          | [item2]                   |
   ...  buffer fills to N  ...
   |                          |                          |
   |--- put(itemN+1) ------->| [full: N items]            |
   |          <blocked, or signaled to stop>              |
   |                          |------- get() ------------>|
   |                          |<------ itemK --------------|
   |                          | [N-1 items, room for 1]    |
   |<---- signal: space available --------------------------|
   |--- put(itemN+1) resumes ->| [N items]                 |
   ...  steady state: producer rate <= consumer rate  ...
```

In a pull-based variant, Reactive Streams, or a batch consumer such as
Kafka's, the sequence inverts, the consumer initiates.

```
Subscriber                                    Publisher
   |------- subscribe() ------------------------->|
   |<------ onSubscribe(subscription) -------------|
   |------- subscription.request(5) -------------->|
   |<------ onNext(item1) --------------------------|
   |<------ onNext(item2) --------------------------|
   |<------ onNext(item3) --------------------------|
   |<------ onNext(item4) --------------------------|
   |<------ onNext(item5) --------------------------|
   |          (Publisher stops, demand exhausted)   |
   |   ... Subscriber finishes processing item1-5 ...
   |------- subscription.request(5) -------------->|
   |<------ onNext(item6) --------------------------|
   ...
```

The push-based diagram shows the buffer as the mediator and blocking or a
signal as the mechanism. The pull-based diagram shows demand itself as the
mediator, and there is no buffer overflow to speak of because the producer
structurally never sends more than was requested, the correctness of the
scheme rests entirely on the producer honestly counting outstanding demand.

## 8. Implementation variants

**Blocking bounded queue.** The simplest and most common variant in
thread-based systems, a fixed-capacity queue whose `put` call blocks the
calling thread when full and whose `get` call blocks when empty. Java's
`java.util.concurrent.ArrayBlockingQueue`, Python's `queue.Queue(maxsize=N)`
used from threads, and Go's buffered channels, `make(chan T, N)`, are all this
variant. The Go language specification states plainly that with a buffered
channel "communication succeeds without blocking if the buffer is not full
(sends) or not empty (receives)" (Go spec, section Channel types, verified
2026-08-02, https://go.dev/ref/spec#Channel_types), and by direct implication
a send on a full buffered channel blocks until a receive makes room, which is
backpressure with zero additional code, it falls directly out of the
language's channel semantics. The trade-off is that a blocked thread consumes
a stack, cheap in Go's goroutines, expensive at scale in OS-thread-per-task
models, and cannot do anything else while waiting.

**Asynchronous bounded queue with awaitable capacity.** The same idea in a
cooperative-concurrency runtime, instead of blocking an OS thread, the
producer suspends a coroutine or awaits a Promise or Future that resolves when
space becomes available. Python's `asyncio.Queue(maxsize=N)` does this, `await
queue.put(item)` suspends the calling coroutine, not the OS thread, when the
queue is full. Node.js's writable-stream model is a push-then-pause variant of
the same idea rather than an await, `write()` returns `false` synchronously
and the caller is expected to stop calling `write()` until the stream emits
`drain` (Node.js documentation, Stream, verified 2026-08-02). This variant
scales to far more concurrent producers per OS thread than the blocking
variant, at the cost of a more complex mental model for anyone reading the
code.

**Pull-based demand signaling, the Reactive Streams model.** Instead of a
buffer that fills and blocks, the consumer explicitly declares how many items
it can accept via `Subscription.request(n)`, and the producer is
contractually forbidden from sending more than the outstanding, unfulfilled
demand. This is the model formalized by the Reactive Streams specification
and implemented by RxJava, Project Reactor, Akka Streams, and, outside the
JVM, conceptually by .NET's `System.Threading.Channels` reader and writer pair
and by Rust's `futures::Stream` trait combined with poll-based execution. The
strength of this variant is that a correct implementation cannot silently
violate its own contract the way a blocking queue with an accidentally
unbounded fallback path can, demand is counted, not inferred.

**Window-based flow control.** Instead of counting discrete items, the
protocol advertises a byte or credit window that shrinks as data is sent and
grows as the receiver processes and acknowledges it. TCP's RCV.WND is the
canonical example, RFC 9293, section 3.3.1. HTTP/2 reuses the same idea at the
stream and connection level, and gRPC, which runs over HTTP/2, inherits it
directly, gRPC's own flow-control guide states that "gRPC utilizes the
underlying transport to detect when it is safe to send more data" (grpc.io,
Flow Control guide, verified 2026-08-02,
https://grpc.io/docs/guides/flow-control/), deferring the actual window
mechanics to HTTP/2's stream-level flow control, RFC 9113. Window-based
schemes are well suited to byte-stream protocols where item boundaries are
not the natural unit of accounting.

**Credit-based and quota-based batching.** A hybrid used heavily in
message-queue consumers, where the consumer does not signal per item but
instead configures an upper bound on how much a single fetch is allowed to
return, and pulls again only when ready for more. Apache Kafka's consumer
exposes `max.poll.records`, default 500, to bound "the maximum number of
records returned in a single call to poll()" (Apache Kafka documentation,
Consumer Configs, `max.poll.records`, verified 2026-08-17,
https://kafka.apache.org/43/configuration/consumer-configs/#consumerconfigs_max.poll.records),
combined with the consumer's own `pause()` and `resume()` calls on specific
partitions to stop the client library from prefetching further data while the
application is still working through a backlog. This variant trades precise
per-item control for coarser, cheaper batch-level control, appropriate when
per-item signaling overhead would outweigh the benefit of finer-grained
accounting.

**Preallocated ring buffer with sequence gating.** Instead of a growable
queue that allocates on every push, a fixed-size, preallocated circular array
is used, and producers are prevented from wrapping around into slots the
consumer has not yet read by tracking the consumer's read sequence before
claiming a write slot. This is the design of the LMAX Disruptor, whose own
documentation describes it as "a pre-allocated bounded data structure in the
form of a ring-buffer" where "producers can avoid wrapping the ring by
tracking the sequence of consumers as a simple read operation before they
write to the ring buffer" (LMAX Disruptor technical paper, Disruptor, High
performance alternative to bounded queues for exchanging data between
concurrent threads, verified 2026-08-02,
https://lmax-exchange.github.io/disruptor/disruptor.html). This variant is
chosen specifically for latency-sensitive, high-throughput single-writer
scenarios, LMAX's own trading system, where the allocation and lock overhead
of a general-purpose blocking queue is itself the bottleneck, and the
gating-by-sequence check substitutes for a lock.

**Adaptive concurrency limiting.** Rather than a static buffer size, the
acceptable rate is computed continuously from observed latency and inferred
queueing, borrowing directly from TCP congestion control's AIMD, additive
increase, multiplicative decrease, idea and applying it to application-level
concurrency rather than packet windows. An open-source library maintained by
a large streaming-media company, `concurrency-limits`, states that it
"implements and integrates concepts from TCP congestion control to
auto-detect concurrency limits for services in order to achieve optimal
throughput with optimal latency" (GitHub, Netflix/concurrency-limits, verified
2026-08-02, https://github.com/Netflix/concurrency-limits), and documents
integration points for gRPC servers and clients, servlet filters, and custom
executors, letting a service reject excess work explicitly, a form of the
reject overflow policy from dimension 5, once its own adaptively-computed
capacity is reached, rather than queueing it or hoping a fixed limit happened
to be correctly tuned for current conditions.

## 9. Known production uses

- **TCP, every operating system's network stack.** The sliding window
  described in RFC 9293 is backpressure at internet scale, present in every
  TCP connection made by every computer on the internet since the 1980s (RFC
  9293, section 3.3.1, verified 2026-08-02,
  https://www.rfc-editor.org/rfc/rfc9293.html).
- **Node.js core streams module.** Every readable and writable stream in
  Node.js, including `fs.createReadStream`, HTTP request and response bodies,
  and `zlib` compression streams, implements the `write()` returning `false`
  plus `drain` event protocol as the standard backpressure mechanism for the
  entire streaming I/O subsystem (Node.js documentation, Stream, verified
  2026-08-02, https://nodejs.org/api/stream.html).
- **The Reactive Streams JVM ecosystem.** RxJava, Project Reactor, the
  reactive core of Spring WebFlux, and Akka Streams all implement the
  Reactive Streams Publisher, Subscriber, Subscription contract with its
  `request(n)` demand signaling as their interoperability boundary, a design
  choice documented on the specification's own site as existing specifically
  so libraries with different internal implementations of backpressure can
  still be composed safely (reactive-streams.org, verified 2026-08-02,
  https://www.reactive-streams.org/).
- **Apache Kafka consumers.** Kafka's consumer client bounds how much data a
  single `poll()` call returns via `max.poll.records`, default 500, per the
  Apache Kafka documentation, verified 2026-08-17, and exposes explicit
  `pause()` and `resume()` calls so an application experiencing a backlog can
  stop the client from fetching further records on specific partitions
  without disconnecting, the documented mechanism Kafka consumer applications
  use to implement backpressure against slow downstream processing.
- **The LMAX Disruptor and its ring-buffer descendants.** Used inside LMAX's
  own trading platform as the inter-thread messaging mechanism, and its
  sequence-gating design, producers checking consumer sequence numbers before
  claiming ring-buffer slots, has been adopted by other high-throughput
  messaging libraries built on the same technique (LMAX Disruptor technical
  paper, verified 2026-08-02,
  https://lmax-exchange.github.io/disruptor/disruptor.html).
- **gRPC over HTTP/2.** Every gRPC streaming call inherits HTTP/2's
  stream-level and connection-level flow control windows, which gRPC's own
  documentation describes as the mechanism by which it detects when it is
  safe to send more data (grpc.io Flow Control guide, verified 2026-08-02,
  https://grpc.io/docs/guides/flow-control/), applying to any production gRPC
  deployment, which includes large parts of Google's internal service mesh
  and is the default RPC framework for the Kubernetes API machinery's
  streaming watch mechanism.
- **`concurrency-limits`, an open-source adaptive concurrency library.**
  Documented by its maintainer as applying AIMD-style adaptive limiting to
  gRPC servers and clients, servlet filters, and executors specifically to
  implement backpressure and load shedding under variable load (GitHub,
  Netflix/concurrency-limits, verified 2026-08-02,
  https://github.com/Netflix/concurrency-limits).

## 10. Consequences

Positive.

- Caps memory consumption at a known, fixed multiple of item size times
  buffer capacity, converting an unbounded failure mode into a bounded,
  plannable one.
- Makes overload visible and gradual rather than sudden and total, since
  queue depth and producer stall time are both observable signals long before
  any resource is exhausted, see dimension 16.
- Preserves correctness under load, in the block-or-signal variants no work
  is silently dropped, which matters whenever at-least-once processing is a
  requirement.
- Couples the effective throughput of a pipeline to its actual bottleneck,
  which is often the desired behavior, since driving every stage as fast as
  possible independently just moves the bottleneck's queue to wherever the
  buffer happens to be largest, rather than eliminating it.
- Composes naturally with monitoring and autoscaling, queue depth and stall
  duration are exactly the signals a horizontal autoscaler needs to add
  consumer capacity in response to sustained backpressure.

Negative.

- Introduces latency for every item that spends time in the buffer waiting
  for capacity, a direct cost even in the non-overloaded case if the buffer
  is sized larger than necessary, Little's Law makes this quantifiable, mean
  wait time equals mean queue length divided by consumer throughput, and it
  applies pressure back onto whatever produced the producer's own input, and
  if that upstream source cannot itself slow down, a hardware sensor, an
  external client with its own timeout, backpressure just relocates the
  overflow problem one hop further upstream rather than eliminating it.
- Adds genuine implementation complexity, a correctly bounded, correctly
  signaled buffer with a well-reasoned overflow policy is meaningfully harder
  to build and to reason about correctness for than an unbounded queue, which
  is precisely why unbounded queues remain the accidental default in most
  language standard libraries and most naively written pipelines.
- Can produce head-of-line blocking, if the buffer and signal are shared
  across logically independent streams of work, multiple tenants, multiple
  request types, one slow consumer of one kind of item can stall the producer
  for all items, not only the slow-to-consume kind, unless the implementation
  partitions buffers per logical stream.
- Under sustained, permanent overload, consumer rate durably below producer
  rate, not just transiently, backpressure alone does not solve the problem,
  it merely makes the resulting unbounded latency growth visible and
  contained in memory rather than invisible and unbounded in memory too, load
  shedding or scaling the consumer is still required to actually fix the
  situation.

## 11. Failure modes and misuse

Memory grows steadily under load despite a backpressure-aware queue in the
code. The queue itself is bounded, but somewhere in the producer's
error-handling or retry path there is an unbounded buffer, commonly a `catch`
block that stores a failed item in an in-memory list to retry later without a
size cap, or a logging or metrics pipeline sitting beside the main data path
that has no backpressure of its own. The fix is to audit every buffer in the
failure and side-channel paths, not just the primary data path, for the same
capacity bound applied to the happy path.

Throughput collapses to near zero under moderate load, well before any
resource is actually exhausted. The buffer capacity is set too small relative
to the variance, not the mean, of producer and consumer rates, so the
producer spends nearly all its time blocked waiting for a single slot to
open, and the signaling round-trip cost, a lock, a context switch, a network
round-trip for a distributed signal, outweighs the actual work time. The fix
is to increase buffer capacity to absorb realistic jitter, measured, not
guessed, and if the signaling mechanism itself has high per-call overhead, to
switch to a batch-oriented variant such as `max.poll.records`-style batching,
dimension 8, rather than signaling on every single item.

One slow tenant, request type, or partition causes every unrelated tenant's
requests to stall as well. A single shared bounded buffer services logically
independent streams of work, so backpressure from one stream's slow consumer
applies indiscriminately to every producer feeding that shared buffer, not
only to the producer whose downstream is actually slow. The fix is to
partition the buffer per logical stream, per tenant, per queue, per Kafka
partition, so backpressure isolates rather than propagates across unrelated
work, which is the same underlying idea as the bulkhead pattern applied to
buffering specifically.

A distributed system deadlocks under load, with two services each waiting for
the other to accept work. A synchronous, blocking backpressure signal was
implemented across a network boundary in both directions, service A blocks
sending to service B while B is backpressuring, while B, in a separate flow,
is itself blocked sending something back to A that is also subject to A's own
backpressure. The fix is to never implement a fully synchronous, mutually
blocking backpressure protocol between two independently deployed services in
both directions simultaneously, and to prefer asynchronous, bounded,
one-directional signaling, a credit or window, not a blocking call, at
cross-service boundaries, exactly the reasoning behind TCP and HTTP/2 using
windows rather than a stop-the-world blocking handshake.

The system appears to have backpressure implemented, request latency
dashboards look calm, but the process still gets OOM-killed under sustained
load. The backpressure signal exists and is correctly computed, but nothing
downstream actually respects it, a common variant is an async framework where
`write()` correctly returns `false`, but the calling code never checks the
return value and keeps calling `write()` anyway, silently defeating the
entire mechanism while the code visually looks correct. This is precisely why
the Reactive Streams model made honoring demand a protocol-level contract
enforceable by the interface shape rather than a convention a caller has to
remember to follow. The fix is to prefer APIs where ignoring the signal is a
type error or a thrown exception rather than a silently ignored return value,
and to add a test, dimension 15, that specifically asserts the producer stops
producing when told to.

A load test shows the system handling exactly the buffer capacity worth of
extra burst and then degrading sharply, with no gradual warning. This is not
actually a failure, it is the expected and correct behavior of a correctly
bounded system, but it is frequently misdiagnosed as a bug because engineers
expect graceful degradation to be perfectly smooth. This entire observation is
judgement rather than a sourced fact. Instead of a code change, the right
response is either to size the buffer to the actual expected burst profile,
or to add an explicit load-shedding response, an HTTP 429, a queue-full
rejection, at the boundary so the sharp edge is a clean, documented rejection
rather than an opaque stall.

## 12. Trade-off matrix

| Force | Backpressure (bounded buffer + signal) | Unbounded queue | Load shedding (drop on overflow) | Static rate limiter (fixed quota, no feedback) | Circuit breaker |
|---|---|---|---|---|---|
| Memory safety under sustained overload | Bounded, predictable | Unbounded, can OOM | Bounded, predictable | Bounded, predictable | Bounded, predictable |
| Preserves every item (no loss) | Yes, in blocking variants | Yes, until it crashes | No, by design | Yes, but rejects early regardless of consumer state | No, fails fast without attempting |
| Degrades gradually and observably | Yes, queue depth rises visibly | No, invisible until crash | No, a hard edge at the drop point | Partially, but the threshold ignores real consumer capacity | Yes, but binary open or closed, not gradual |
| Couples producer rate to actual consumer capacity | Yes, directly and continuously | No coupling at all | No, drops instead of coupling | No, quota is fixed regardless of live capacity | Indirectly, via failure detection, not capacity signaling |
| Implementation complexity | Moderate to high | Lowest, the accidental default | Low | Low | Moderate |
| Appropriate when producer cannot slow down (hardware) | Not applicable, use ring buffer with drop policy instead | No, will exhaust memory | Yes, this is the correct fit | Possibly, if the quota matches the hardware rate | No, addresses a different failure class |
| Appropriate when downstream is failing, not merely slow | Poor fit, propagates the stall upstream instead of isolating it | Poor fit | Partial fit | Poor fit | Best fit, this is what it is designed for |

## 13. Related and incompatible patterns

**Producer-Consumer.** Backpressure is best understood as the Producer-Consumer
pattern with an explicit, enforced capacity bound and signaling channel added.
Producer-Consumer alone says nothing about what happens when the queue is
full, backpressure is the specific answer to that open question.

**Bounded Buffer.** The data structure most commonly used to implement
backpressure's storage component, dimension 5. Bounded Buffer is a narrower,
purely structural pattern, a fixed-capacity queue with blocking put and get.
backpressure is the broader systemic pattern of which a bounded buffer is
usually, but not always, one piece, the pull-based, credit-based variants in
dimension 8 implement backpressure without a literal shared buffer at all.

**Circuit Breaker.** Complementary, addressing a different failure mode.
backpressure handles a consumer that is slow but healthy, circuit breaker
handles a consumer that is failing or has become unresponsive. A well-designed
system frequently uses both, backpressure for normal load variance, and a
circuit breaker that trips when the consumer's failures, not merely its
slowness, exceed a threshold, at which point continuing to apply backpressure
against a truly broken downstream stops helping and starts hurting.

**Bulkhead.** Directly composes with backpressure to solve the head-of-line
blocking failure mode in dimension 11, partition the bounded buffer, or the
connection pool, or the thread pool, so that one slow consumer's backpressure
cannot starve unrelated work sharing the same infrastructure.

**Rate Limiter.** A static rate limiter enforces a fixed quota regardless of
the consumer's actual, current capacity. It is simpler to reason about and
requires no feedback channel, but it cannot adapt when the consumer has spare
capacity, wasting throughput, or when the consumer is more loaded than usual,
letting through more than it can actually handle. Backpressure and rate
limiting are frequently combined, a rate limiter as a coarse, cheap first
line of defense at a system's edge, backpressure as the finer-grained,
adaptive mechanism operating on the internal pipeline behind it.

**Load Shedding.** The pattern backpressure exists specifically to avoid
having to reach for by default, dropping or rejecting excess work rather than
slowing the producer. The two are not mutually exclusive, a well-designed
overflow policy, dimension 5, often falls back to load shedding once a
secondary, harder bound is reached, treating backpressure as the first
response and shedding as the last resort when the producer genuinely cannot
be slowed further, an external client with its own timeout, for instance.

**Actor Model and Event Loop.** Actor mailboxes and event-loop task queues are
a frequent home for the failure mode described in dimension 11's first entry,
an unbounded mailbox behind an otherwise well-designed backpressure-aware
system, because many actor-model runtimes historically defaulted mailboxes to
unbounded for simplicity. Where the runtime supports it, bounded mailbox
sizes, backpressure-aware actor supervision strategies, applying the same
bounded-plus-signal discipline to the mailbox itself closes this gap.

**Incompatible with fire-and-forget messaging.** A messaging pattern built on
the explicit assumption that the sender never waits for, and never learns
about, the receiver's state is structurally unable to carry a backpressure
signal, there is nowhere in the protocol for "slow down" to travel. Adding
backpressure to a fire-and-forget system requires changing the messaging
contract itself, not just adding a buffer.

**Incompatible with unbounded queue as a design choice.** Not merely a
missing optimization, an unbounded queue is the thing backpressure exists to
replace. A system that has both backpressure and an unbounded queue somewhere
in its critical path has, in practice, no backpressure at all, because the
unbounded component will always be where the failure occurs first, per
dimension 11's first entry.

## 14. Refactoring path in and out

Introducing backpressure into an unbounded system.

1. Identify every queue, buffer, list, or channel in the path between
   producer and consumer, including error and retry paths, that currently has
   no capacity limit. An unbounded `LinkedList`, an unbounded channel, an
   application-level in-memory retry list, and a database connection pool
   configured with an effectively infinite wait queue are all candidates.
2. Choose a bound for each, grounded in a measurement of actual, observed
   producer burst size and consumer processing rate under representative
   load, not a guess. Undersizing produces the throughput-collapse failure
   mode in dimension 11, oversizing merely delays the same failure the
   unbounded version has today.
3. Convert the unbounded structure to its bounded equivalent, a
   fixed-capacity `ArrayBlockingQueue`, a `chan T, N` with a fixed `N`, an
   `asyncio.Queue(maxsize=N)`, which by itself immediately changes the
   failure mode from eventual OOM to producer blocks or is rejected when
   full, a strict improvement even before anything else is done.
4. Decide the overflow policy explicitly, dimension 5, rather than accepting
   whatever the default of the chosen data structure happens to be, and write
   a test asserting that behavior specifically, dimension 15.
5. Confirm every code path that writes to the bound structure actually checks
   and honors any non-blocking signal, a `false` return value, an exception,
   this is the step most often skipped, producing the "looks correct but
   isn't" failure mode in dimension 11.
6. Add the observability signals from dimension 16 before shipping the change
   to production, queue depth and producer stall time need to be visible from
   day one, not added reactively after the first incident.
7. Load test specifically at and beyond the chosen capacity to confirm the
   system degrades the way the overflow policy intends, rather than in some
   unintended way discovered only under real production load.

Removing backpressure once it stops earning its place.

1. Confirm, with measurement rather than assumption, that the consumer's
   processing rate now durably and provably exceeds the maximum realistic
   producer rate, including burst, under every load condition the system is
   expected to see, not merely the current average.
2. If true, the bounded buffer's capacity limit will simply never be reached
   in practice, at which point the backpressure machinery, blocking, signal
   channel, overflow policy, is unreachable code carrying maintenance cost
   with no runtime benefit.
3. Before removing, add an alert on approach to buffer capacity, not just on
   the overflow path itself, so that a future change to producer or consumer
   rate that reintroduces the imbalance is caught before the removed
   machinery is missed.
4. Simplify to whatever the bare bounded-buffer capacity check alone
   provides, usually still worth keeping, since it costs almost nothing and
   preserves the memory-safety property even if it never actually blocks in
   current conditions, removing only the additional adaptive or credit-based
   machinery layered on top, since the cheap bound is rarely the part worth
   removing, the expensive adaptive layer usually is.

## 15. Testing and verification

One part of backpressure is comparatively easy to test, and another part is
genuinely hard.

Verifying the buffer is actually bounded is easy. Fill a bounded buffer to
capacity in a test, then assert that a further, non-blocking add attempt
either returns a specific failure indicator or that a blocking add attempt
does not return until a concurrent consumer removes an item. This is a
straightforward, deterministic unit test with no timing sensitivity if the
non-blocking API is used, and a test using a timeout-bounded assertion, assert
the blocking call has not returned after N milliseconds, then assert it does
return promptly once an item is removed, if only the blocking API exists.

Verifying the overflow policy fires correctly is also easy. Push exactly one
more item than capacity and assert the documented behavior, block, drop,
reject, occurs, rather than some other behavior. This catches the common
regression where a refactor accidentally changes a bounded structure back to
an effectively unbounded one, for example replacing a fixed-size array-backed
queue with a growable list for convenience during a later change.

Verifying that the producer actually stops producing when signaled is hard,
under realistic concurrent conditions rather than a single-threaded, easily
sequenced test. The right technique is a test double for the consumer that
deliberately withholds acknowledgment or artificially slows itself under
controlled conditions, a fake consumer that sleeps, or a fake Subscriber that
simply never calls `request(n)` again after its first batch, combined with an
assertion that the producer's item count stalls at the expected bound and
does not exceed it, observed over a wall-clock window rather than inferred
from a single snapshot. This is the test most systems skip, and its absence
is exactly what allows the "looks correct but isn't" failure mode from
dimension 11 to ship undetected, because a test that only exercises the happy
path, consumer always keeps up, never exercises the code path where the
signal actually needs to be honored.

Property-based or stress testing that runs producer and consumer at
randomized, adversarial relative rates, including the consumer being much
slower some of the time, and momentarily faster than the producer at others,
is harder still but valuable. It asserts an invariant, buffer occupancy never
exceeds capacity, total items produced equals total items consumed plus items
currently buffered, no silent loss in the non-shedding variants, and, for
latency-sensitive systems, that end-to-end item latency stays within an
expected bound derived from Little's Law given the configured capacity and
observed throughput. This class of test is what catches the subtler races in
asynchronous implementations, where the signaling and the buffer mutation are
not atomic with respect to each other, a bug class ordinary sequential unit
tests structurally cannot exercise.

## 16. Observability signals

- **Buffer occupancy, current size versus configured capacity.** The single
  most direct signal. A gauge that sits consistently near zero under normal
  load and rises sharply, then plateaus at capacity, during backpressure
  events is exactly the expected, healthy pattern, distinguishable from a
  gauge that rises and never comes back down, which indicates the consumer
  has stopped keeping up permanently rather than transiently.
- **Producer stall time or blocked duration.** How long, in aggregate and at
  percentiles, producers spend waiting for capacity before their write
  succeeds. A healthy system shows this at or near zero most of the time with
  occasional short spikes correlated with traffic bursts, an unhealthy one
  shows it growing steadily, which is the earliest visible warning of
  sustained, not transient, overload, well before the buffer itself is
  observed at capacity.
- **Consumer processing rate versus producer arrival rate, as parallel time
  series.** Plotted together, the gap between these two lines, when the
  producer line sits above the consumer line, is the rate at which the
  buffer is filling, and its integral over time predicts, well in advance,
  when capacity will be exhausted if nothing changes, giving operators lead
  time a bare occupancy gauge alone does not.
- **Overflow event count.** How many times the overflow policy actually
  fired, items dropped, requests rejected, or producer calls that timed out
  waiting for space. Should be zero or near zero in steady state, any
  sustained non-zero rate is a signal the configured capacity, or the
  consumer's provisioned capacity, needs to change, not a signal that is safe
  to silently tolerate indefinitely.
- **Demand outstanding, in pull-based `request(n)`-style systems.** The count
  of items a producer is currently entitled to send but has not yet sent, and
  separately, how long a consumer waits between exhausting its previous
  demand and issuing its next `request(n)`, which surfaces consumer-side
  processing latency directly, distinct from producer-side stall time.

A healthy dashboard shows occupancy oscillating in a band well under
capacity, stall time near zero with brief, traffic-correlated spikes,
overflow count flat at zero, and the arrival-versus-processing-rate lines
tracking each other closely. A failing dashboard shows the opposite
signature, occupancy pinned at capacity for a sustained period, stall time
climbing monotonically, overflow count incrementing steadily rather than in
brief bursts, and a widening, non-recovering gap between arrival and
processing rate. Together these four signals are the unambiguous signature of
a consumer that is durably, not transiently, under-provisioned relative to
load. This whole paragraph is engineering judgement rather than a sourced
claim.

## 17. Security and privacy implications

Backpressure has a direct, well-documented relationship to denial-of-service
resilience, and a more subtle one to information leakage through timing.

An unbounded queue is itself a denial-of-service vulnerability against the
process's own memory, an attacker who can drive request volume above the
consumer's processing rate for long enough can exhaust memory and crash the
process without needing any other vulnerability, purely by exploiting the
absence of a bound. Backpressure closes this specific vector, converting an
unbounded-memory failure into a bounded-latency or bounded-rejection one,
which is a genuine, meaningful hardening, but it is not itself a complete
defense against denial of service. An attacker can still drive the system
into sustained, saturating overload, at which point legitimate traffic
experiences the same degraded latency or rejection an attacker's traffic
does, unless the system also has authentication-aware or per-client fairness
on top of the bounded buffer, a bulkhead partitioned per client or per
tenant, dimension 13, so that one abusive client's backpressure does not
degrade every other client's experience equally.

The signal channel and the overflow policy can leak information through
timing side channels in adversarial contexts. A system where a request that
was rejected quickly because the buffer was full is externally
distinguishable from a request that was accepted because the buffer had room
and then processed slowly gives an external observer a coarse signal about
internal load state, which in most contexts is harmless operational
information but in specific adversarial contexts, an attacker probing to
learn when a target system is under peak legitimate load, in order to time a
separate attack for maximum impact, is a real, if narrow, information
disclosure. This paragraph is engineering judgement, drawn from analysis
rather than a cited source. Where this matters, the mitigation is to make
rejection responses, dimension 5's overflow policy, observably
indistinguishable in timing from accepted-and-queued responses, rather than
an immediate fast-path rejection, which is a genuine engineering trade-off
against the latency benefits backpressure otherwise provides, and is only
worth making in contexts where this specific threat model applies.

Backpressure has no direct privacy implication of its own, it governs flow
control, not data content, but any buffer, bounded or not, that temporarily
holds in-flight items in memory is a location where sensitive data sits
unencrypted for the duration of its residence in that buffer, exactly as any
other in-memory buffer is. This is a property of buffering generally, not of
backpressure specifically, and is worth stating plainly rather than implying
backpressure introduces a new exposure, it does not, it merely makes the
existing exposure's duration bounded and predictable rather than unbounded.

## 18. References

1. J. Postel, "Transmission Control Protocol", RFC 793, September 1981,
   original sliding-window specification.
2. W. Eddy, ed., "Transmission Control Protocol (TCP)", RFC 9293, August 2022,
   section 3.1, header window field, and section 3.3.1, RCV.WND and key
   connection state variables. Verified 2026-08-02.
   https://www.rfc-editor.org/rfc/rfc9293.html
3. Reactive Streams initiative, "Reactive Streams", specification overview,
   Reactive Streams SIG, Netflix, Pivotal, Lightbend, Red Hat, Twitter and
   others, first published 2015. Verified 2026-08-02.
   https://www.reactive-streams.org/
4. Node.js documentation, "Stream", section Writable streams, `write()` and
   `highWaterMark` behavior. Verified 2026-08-02.
   https://nodejs.org/api/stream.html
5. The Go Programming Language Specification, section Channel types. Verified
   2026-08-02. https://go.dev/ref/spec#Channel_types
6. gRPC documentation, "Flow Control" guide, description of gRPC's reliance
   on HTTP/2 transport-level flow control. Verified 2026-08-02.
   https://grpc.io/docs/guides/flow-control/
7. M. Belshe, R. Peon, M. Thomson, eds., "Hypertext Transfer Protocol Version
   2 (HTTP/2)", RFC 9113, June 2022, section 5.2, Flow Control, the
   underlying mechanism gRPC's flow control depends on.
8. Apache Kafka documentation, Consumer Configs, `max.poll.records`.
   Verified 2026-08-17.
   https://kafka.apache.org/43/configuration/consumer-configs/#consumerconfigs_max.poll.records
9. LMAX Exchange, "Disruptor, High performance alternative to bounded queues
   for exchanging data between concurrent threads", technical paper. Verified
   2026-08-02. https://lmax-exchange.github.io/disruptor/disruptor.html
10. Netflix, `concurrency-limits`, project README describing adaptive,
    TCP-congestion-control-derived concurrency limiting for backpressure and
    load shedding. Verified 2026-08-02.
    https://github.com/Netflix/concurrency-limits
11. Kubernetes documentation, "Resource Management for Pods and Containers",
    description of CPU limit enforcement via CFS quota and throttling.
    Verified 2026-08-02.
    https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
12. J. D. C. Little, "A Proof for the Queuing Formula, L = lambda W",
    Operations Research, vol. 9, no. 3, 1961, Little's Law, cited in
    dimension 3 and dimension 16 regarding the relationship between buffer
    occupancy, arrival rate, and latency.

## Code examples

Three languages were chosen because each demonstrates a structurally
different way the pattern is expressed in practice. Python's `asyncio.Queue`
shows the awaitable-capacity variant used throughout async Python I/O, Go's
buffered channel shows backpressure falling directly out of a language
primitive with no library code required, and TypeScript demonstrates
implementing the same bounded-channel semantics by hand atop Promises, which
is instructive precisely because it shows what a language like Go gives you
for free. All three examples were executed and their output is representative
of an actual run, not hypothetical.

### Python, asyncio.Queue, awaitable bounded buffer

Ran successfully with `python3`. Output confirmed the producer interleaves
with a slower consumer rather than racing ahead, and the final five items
were consumed after production completed, showing the queue correctly
bounded producer progress to consumer pace.

```python
import asyncio


async def producer(queue: asyncio.Queue, count: int) -> None:
    for i in range(count):
        item = f"item-{i}"
        await queue.put(item)
        print(f"produced {item} (qsize={queue.qsize()})")
    await queue.put(None)


async def consumer(queue: asyncio.Queue) -> None:
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        await asyncio.sleep(0.001)
        print(f"consumed {item}")
        queue.task_done()


async def main() -> None:
    queue: asyncio.Queue = asyncio.Queue(maxsize=4)
    await asyncio.gather(producer(queue, 10), consumer(queue))


if __name__ == "__main__":
    asyncio.run(main())
```

`await queue.put(item)` is the backpressure point. Once four items are
buffered, the fifth `put` call suspends the producer coroutine, not the OS
thread, until the consumer's `get()` frees a slot. Nothing about the
producer's loop needed to check a return value or handle a signal explicitly,
the awaitable itself carries the backpressure.

### Go, buffered channel, language-level backpressure

Ran successfully with `go run`. Output showed the same interleaved
produced-and-consumed pattern, confirming the buffered channel's send blocked
once its four-item capacity was reached.

```go
package main

import (
	"fmt"
	"time"
)

func producer(out chan<- int, n int) {
	for i := 0; i < n; i++ {
		out <- i
		fmt.Printf("produced %d\n", i)
	}
	close(out)
}

func consumer(in <-chan int, done chan<- bool) {
	for v := range in {
		time.Sleep(time.Millisecond)
		fmt.Printf("consumed %d\n", v)
	}
	done <- true
}

func main() {
	ch := make(chan int, 4)
	done := make(chan bool)
	go consumer(ch, done)
	producer(ch, 10)
	<-done
}
```

`ch := make(chan int, 4)` creates a channel whose capacity is the entire
backpressure mechanism. `out <- i` blocks the producer goroutine once four
unread items are buffered, exactly the semantics the Go specification
describes for buffered channels, with no additional library or hand-written
signaling code needed, this is the variant described in dimension 8 as
backpressure falling directly out of the language.

### TypeScript, hand-rolled bounded channel over Promises

Compiled with `tsc --strict` and ran successfully with `node`, confirming the
same interleaved output pattern as the Go and Python examples, with the final
items consumed after production completed once the buffer's four-item
capacity had gated the producer's pace.

```typescript
class BoundedChannel<T> {
  private buffer: T[] = [];
  private waitingProducers: Array<() => void> = [];
  private waitingConsumers: Array<(v: T) => void> = [];
  private closed = false;

  constructor(private readonly capacity: number) {}

  async send(value: T): Promise<void> {
    if (this.waitingConsumers.length > 0) {
      const resolve = this.waitingConsumers.shift()!;
      resolve(value);
      return;
    }
    if (this.buffer.length < this.capacity) {
      this.buffer.push(value);
      return;
    }
    await new Promise<void>((resolve) => this.waitingProducers.push(resolve));
    this.buffer.push(value);
  }

  async receive(): Promise<T | undefined> {
    if (this.buffer.length > 0) {
      const value = this.buffer.shift()!;
      const wake = this.waitingProducers.shift();
      if (wake) wake();
      return value;
    }
    if (this.closed) return undefined;
    return new Promise<T>((resolve) => this.waitingConsumers.push(resolve));
  }

  close(): void {
    this.closed = true;
  }
}

async function producer(ch: BoundedChannel<number>, n: number): Promise<void> {
  for (let i = 0; i < n; i++) {
    await ch.send(i);
    console.log(`produced ${i}`);
  }
  ch.close();
}

async function consumer(ch: BoundedChannel<number>): Promise<void> {
  while (true) {
    const v = await ch.receive();
    if (v === undefined) break;
    await new Promise((r) => setTimeout(r, 1));
    console.log(`consumed ${v}`);
  }
}

async function main(): Promise<void> {
  const ch = new BoundedChannel<number>(4);
  await Promise.all([producer(ch, 10), consumer(ch)]);
}

main();
```

`send()` checks buffer length against `capacity` and, when full, awaits an
unresolved Promise pushed onto `waitingProducers`, exactly reproducing what Go
gives natively and what `asyncio.Queue` gives via a standard-library type.
`receive()` resolves the oldest waiting producer's Promise whenever it frees a
slot, which is the explicit signal channel from dimension 5 made visible as
code rather than hidden inside a runtime primitive.
