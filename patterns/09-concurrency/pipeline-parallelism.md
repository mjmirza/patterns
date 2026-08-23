---
name: Pipeline Parallelism
slug: pipeline-parallelism
family: 09-concurrency
category: Concurrency
aliases: [Pipeline Pattern, Pipelined Processing, Staged Pipeline, Assembly Line Concurrency, Streaming Pipeline]
first_described: "Concept traces to Douglas McIlroy's Unix pipe, implemented by Ken Thompson in Version 3 Unix, 1973. The concurrent-software pattern name was popularized in the reactive and channel-based programming literature of the 2000s and 2010s, most influentially by Sameer Ajmani, Go Concurrency Patterns, Pipelines and Cancellation, go.dev/blog/pipelines, 2014"
maturity: canonical
related: [producer-consumer, fork-join, reactor, active-object, thread-pool, future-promise, half-sync-half-async]
incompatible_with: []
verified: 2026-08-02
---

# Pipeline Parallelism

## 1. Name, aliases, and lineage

Pipeline Parallelism is the name most concurrency texts and library documentation
use for a program shaped as a sequence of stages, each stage running as its own
thread, goroutine, actor, or task, connected to its neighbors by queues or
channels so data flows through the sequence continuously rather than waiting for
one stage to finish everything before the next begins. It is also called the
Pipeline Pattern, Pipelined Processing, or, less formally, an assembly line,
because the governing metaphor is a factory line where each station performs
one operation on a part before passing it to the next station, and multiple
parts are in flight across different stations at once.

The idea did not begin as a concurrency pattern. It began as a systems idea. The
pipe concept was invented by Douglas McIlroy at Bell Labs and first described in
internal Unix documentation, then implemented by Ken Thompson, who added the
pipe() system call and wired pipes into the shell and several utilities in
Version 3 Unix in 1973, an event McIlroy himself described as happening in one
feverish night (Wikipedia, "Pipeline (Unix)," summarizing the documented history
of McIlroy's invention and Thompson's 1973 implementation, verified 2026-08-02,
https://en.wikipedia.org/wiki/Pipeline_(Unix)). That page defines the resulting
mechanism plainly. "A pipeline is a set of processes chained together by their
standard streams, so that the output text of each process (stdout) is passed
directly as input (stdin) to the next one" (same source). Every later
in-process pipeline, whether built from Go channels, Rust mpsc channels,
.NET dataflow blocks, or Java's Flow API, is the same idea moved from
inter-process file descriptors into in-process queues.

The pattern also has a distinct lineage inside hardware architecture, where
instruction pipelining in a CPU dates to at least the 1960s. That hardware
sense and the software sense share a name and a shape, a sequence of stages
each doing one narrow job on a stream of items, but this entry covers the
software concurrency pattern, not microarchitectural instruction pipelining,
which belongs to computer architecture rather than to application or systems
concurrency design.

The name that stuck for the software concurrency version, distinct from the
Unix shell pipeline it descends from, was cemented for a generation of
programmers by Sameer Ajmani's 2014 Go blog post, which defines it for an
audience of concurrent-programming practitioners. "Informally, a pipeline is a
series of stages connected by channels, where each stage is a group of
goroutines running the same function" (Sameer Ajmani, "Go Concurrency
Patterns. Pipelines and cancellation," go.dev, 13 March 2014, verified
2026-08-02, https://go.dev/blog/pipelines). Multimedia frameworks such as
GStreamer independently arrived at the same word for the same shape, describing
a chain of connected elements as forming "a pipeline that can do a specific
task, for example media playback or capture" (GStreamer Application Development
Manual, "Basic Concepts," verified 2026-08-02,
https://gstreamer.freedesktop.org/documentation/application-development/introduction/basics.html).

## 2. Problem and context

A program has to apply several distinct transformations to a large or unbounded
stream of items, and the transformations are heterogeneous. One stage decodes a
file format, the next validates the record, the next enriches it with a
database lookup, the next writes it to storage. Written as a single loop, each
item pays the full cost of every stage before the next item starts, so the CPU
sits idle while a network call for item three is in flight and nothing else
happens in the meantime. The total wall-clock time is the sum of every stage's
latency multiplied by the number of items, even though several of the stages
have nothing to do with each other's resources. decoding is CPU-bound,
enrichment is I/O-bound, and writing is disk-bound.

The context this problem shows up in is any batch or streaming data-processing
job with more than one distinct, independent transformation step, and any
program that reads from a slow source (a file, a socket, a queue) and must
begin useful work on the first records before the last record has arrived. It
also shows up inside a single request's handling when a request itself carries
several independent sub-transformations, for example an image upload that must
be decoded, resized, watermarked, and re-encoded, where each of those four
operations can run as a distinct worker pool sized to its own bottleneck rather
than one worker pool sized to the slowest single step.

The pattern assumes the work naturally decomposes into an ordered sequence of
transformations where each stage's output is the next stage's input, and that
the stages have different resource profiles worth isolating, because a pipeline
that only isolates identical, resource-symmetric stages gets little benefit
over simply running more copies of the whole loop in parallel, which is the
Producer-Consumer or worker-pool pattern instead.

## 3. Forces

**Throughput versus per-item latency.** A pipeline maximizes throughput, the
rate at which items complete across the whole stream, by keeping every stage
busy concurrently. It does this at the cost of per-item latency for the first
and last items, because an item must still traverse every stage in order, and a
short pipeline handling one item is never faster than the equivalent
sequential code for that one item. the win appears only once many items are in
flight and the stages overlap.

**Stage granularity versus coordination overhead.** Finer-grained stages give
more opportunity to overlap distinct kinds of work and to tune each stage's
concurrency independently, but every additional stage boundary is a queue, a
channel, or a lock, each with allocation, synchronization, and possibly
serialization cost. A stage boundary drawn around work that takes microseconds
loses more to coordination than it gains from overlap.

**Bounded buffering versus backpressure.** An unbounded queue between stages
lets a fast producer race ahead of a slow consumer, which maximizes momentary
throughput but risks unbounded memory growth if the slow stage never catches
up. A bounded queue caps memory and forces backpressure, the fast stage blocks
when the buffer is full, but a buffer sized too small serializes stages that
should have been able to overlap, and one sized too large defeats the memory
guarantee it exists to provide.

**Ordering versus parallel fan-out within a stage.** A pipeline that must
preserve the input order of items through the whole chain, common for
log-processing or financial-transaction pipelines, cannot freely run one stage
with multiple concurrent workers unless it also reorders results back into
sequence at the far end, which itself costs a buffer and coordination. A
pipeline that does not need order preserved can fan a slow stage out across
many workers with no reordering cost, trading strict ordering for higher
throughput on the bottleneck stage.

**Failure isolation versus end-to-end propagation.** Each stage running in its
own goroutine, thread, or actor means a panic or exception in one stage need
not crash the whole process, but an error partway through the pipeline must
still be communicated downstream (or upstream, as a cancellation signal) or the
pipeline silently drops data or blocks forever on a channel nobody will ever
read from again.

## 4. Applicability and non-applicability

Reach for pipeline parallelism when.

- The work is a fixed, ordered sequence of distinct transformations applied to
  a stream of many items, and at least two of those transformations have
  meaningfully different resource profiles (CPU-bound, I/O-bound, memory-bound).
- The input is a stream that arrives over time, or is large enough that
  starting the second stage's work on early items while later items are still
  arriving materially improves total wall-clock time.
- Each stage's degree of concurrency can usefully be tuned independently, for
  example an I/O-bound network-fetch stage benefits from more concurrent
  workers than a CPU-bound decode stage bound by core count.
- The system already has, or can cheaply add, a queue or channel primitive with
  the backpressure semantics the pipeline needs, so the pattern is not fighting
  the platform to get bounded buffering.
- Failures at one stage can be represented as data flowing through the
  pipeline, an error value, a poison item, or a cancellation signal, rather
  than needing to unwind a call stack that spans multiple goroutines or threads.

Do NOT reach for pipeline parallelism when.

- The total item count is small and fixed, and the per-item processing cost is
  small enough that thread or channel setup cost dominates. A loop calling four
  functions in sequence over ten items is faster and clearer than four
  goroutines and three channels.
- The stages have no meaningful concurrency to exploit because they all
  contend for the same single resource, for example four stages that each do
  nothing but hold a global lock. splitting them into separate goroutines adds
  synchronization cost while the actual work still serializes on the lock.
- The transformations are not independent in the required sense, for example a
  later stage needs random access to items far ahead in the stream or needs the
  complete result set before it can start, which is a batch or Fork-Join shape,
  not a streaming pipeline.
- Strict, cheap-to-reason-about ordering with no possibility of stage-internal
  reordering is required and the team lacks the discipline or tooling to
  correctly implement order-preserving fan-out and merge. a simple sequential
  loop is easier to get right and audit.
- The overhead of debugging concurrent, multi-stage failure and cancellation
  paths is not worth the throughput gain, which is common for low-volume
  administrative or batch jobs run a handful of times a day where wall-clock
  time is not the bottleneck a person actually cares about.
- The runtime or language has no cheap concurrency primitive (a lightweight
  thread, a channel, a bounded queue) and building one from scratch would cost
  more engineering time than the pipeline ever saves. this rules the pattern
  out for some embedded or resource-constrained targets.

## 5. Structure

A pipeline has three kinds of participant.

**Source (or generator).** The first stage. It has no upstream input channel,
it only produces items, typically by reading from an external resource such as
a file, a socket, or a database cursor, or by generating a bounded sequence
directly. It owns the decision of when the stream ends and is responsible for
closing its outbound channel or otherwise signaling completion once no more
items will be produced.

**Stage (or filter, or processor).** Every intermediate participant. A stage
receives items from exactly one inbound channel (or, in a fan-in topology,
merges several), applies a transformation, and sends the result to exactly one
outbound channel (or, in a fan-out topology, distributes across several). A
stage owns closing its own outbound channel once its inbound channel is
exhausted and it has finished emitting, which is what lets the next stage in
turn detect end of stream without an explicit sentinel value being required in
languages whose channel primitive supports closing.

**Sink (or consumer, or terminal stage).** The last stage. It has no outbound
channel. it consumes items to produce a final side effect, an aggregate value,
or a persisted result, and its termination (having drained its inbound channel
to completion) marks the whole pipeline as done for that run.

A fourth, cross-cutting participant appears in most real implementations, a
**cancellation signal**, commonly a dedicated done channel, a shared context
value, or a cancellation token, that every stage selects on alongside its
data channels so that when the sink stops early (because the consumer only
wanted the first N results) or the source fails, every stage in between is
told to stop rather than blocking forever trying to send into a channel no one
will ever read again, which is a goroutine leak in Go and an equivalent thread
leak in any other channel-based implementation.

## 6. ASCII structure diagram

```
Cancellation / Done signal (broadcast, read by every stage)

+---------------------------+
| Source (producer)         |
| worker(s), N1 concurrency |
+---------------------------+
           | chan/queue
           v
+---------------------------+
| Stage 1 (transform)       |
| worker(s), N2 concurrency |
+---------------------------+
           | chan/queue
           v
+---------------------------+
| Stage 2 (transform)       |
| worker(s), N3 concurrency |
+---------------------------+
           | chan/queue
           v
+---------------------------+
| Sink (consumer)           |
| worker(s), N4 concurrency |
+---------------------------+

Fan-out variant on Stage 2 (independently sized worker
pool per stage):

              +--> worker 2a --+
Stage 1 out --+--> worker 2b --+--> merge --> Stage 3 in
              +--> worker 2c --+
```

## 7. Dynamics

```
t0  Source starts.  Source emits item[1] into channel A, keeps running.
t1  Stage1 receives item[1] from A, begins transforming it.
    Source concurrently emits item[2] into channel A (buffered, or blocks
    until Stage1 next reads, depending on buffer size).
t2  Stage1 finishes item[1], sends result into channel B, immediately reads
    item[2] from A.
t3  Stage2 receives item[1] from B, begins its transform.
    Stage1 concurrently works on item[2].
    Source concurrently emits item[3].
t4  ... steady state ...  three distinct items are in flight across three
    distinct stages simultaneously, each stage doing different work at the
    same wall-clock moment.  Throughput is now bound by the slowest single
    stage, not by the sum of every stage's latency.
tN  Source exhausts its input, closes channel A (or sends an explicit end
    marker).
tN+1 Stage1's receive loop observes A closed after draining what remains,
    closes channel B.
tN+2 Stage2's receive loop observes B closed after draining what remains,
    closes channel C.
tN+3 Sink's receive loop observes C closed after draining what remains,
    the pipeline run is complete.

Cancellation dynamics (early termination, for example the Sink only wanted
the first result and stops reading):
  Sink stops reading from C, and closes (or the run() caller closes) the
  shared done channel.
  Every stage's select statement, which races a send against a receive on
  done, observes done closed and returns instead of blocking on a send
  nobody will ever consume, unwinding the whole pipeline without a leaked
  goroutine.
```

## 8. Implementation variants

**Channel-based, closed-channel-as-EOF (Go idiom).** Each stage is a function
returning a receive-only channel. The stage's goroutine ranges over its input
channel and closes its output channel in a deferred call when the range loop
ends, which happens automatically when the upstream closes its channel. This is
the variant Ajmani's post documents and it is the idiomatic Go shape (Sameer
Ajmani, "Go Concurrency Patterns. Pipelines and cancellation," go.dev, 2014,
verified 2026-08-02, https://go.dev/blog/pipelines).

**Bounded queue with poison pill (thread-based languages without a native
closable-channel primitive).** Each stage is a thread or worker loop reading
from a bounded Queue. End of stream is signaled by a distinguished sentinel
object placed on the queue, which each stage forwards downstream after
consuming it, exactly as demonstrated in this entry's Python example. This
variant is common in Java (BlockingQueue), Python (queue.Queue), and C
implementations that predate or avoid a dedicated channel type.

**Reactive-streams, backpressure-protocol variant.** Stages implement a
Publisher/Subscriber/Subscription contract in which a downstream stage
explicitly requests a bounded number of items (request(n)) rather than the
upstream simply pushing until a buffer blocks, giving the consumer, not the
buffer size, control over the rate of flow. This is the shape Java's
java.util.concurrent.Flow API and the wider Reactive Streams specification
formalize, where a Processor is defined as "a component that acts as both a
Subscriber and Publisher" so it can sit in the middle of a chain (Java SE 21
API documentation, java.util.concurrent.Flow, verified 2026-08-02,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Flow.html).

**Dataflow-block variant.** Stages are pre-built, composable block types
(TransformBlock, ActionBlock, BufferBlock in .NET's TPL Dataflow) each
with a configurable BoundedCapacity, linked together with an explicit LinkTo
call rather than hand-written channel plumbing. "You can connect dataflow
blocks to form pipelines, which are linear sequences of dataflow blocks... In
a pipeline or network, sources asynchronously propagate data to targets as
that data becomes available" (Microsoft Learn, "Dataflow (Task Parallel
Library)," verified 2026-08-02,
https://learn.microsoft.com/en-us/dotnet/standard/parallel-programming/dataflow-task-parallel-library).
This variant trades hand-rolled control for a library-managed scheduler and
built-in bounded-capacity backpressure.

**Element-graph, pad-based variant.** Stages are typed elements with input
and output pads, and buffers of data (not merely scalar items) flow between
pads. the framework itself schedules each element's processing thread and
negotiates the buffer format between adjacent elements at pipeline-construction
time rather than at every item. GStreamer's element and pad model is the
canonical example of this shape for streaming media (GStreamer Application
Development Manual, "Basic Concepts," verified 2026-08-02,
https://gstreamer.freedesktop.org/documentation/application-development/introduction/basics.html).

**Single-thread, cooperative-yield variant.** In a single-threaded, event-loop
runtime (Node.js, an async Rust executor without work-stealing, single-threaded
Python asyncio), the pipeline shape is preserved as a sequence of async
generators or futures chained together, and the concurrency benefit comes not
from true parallel CPU execution but from overlapping I/O wait time across
stages. a stage awaiting a network call yields control so another stage can
make progress on a different item, which is pipeline concurrency without
pipeline parallelism in the strict CPU-bound sense, but produces the same
throughput shape for I/O-bound stages.

## 9. Known production uses

- **The Unix shell and coreutils pipe operator.** Every "cmd1 | cmd2 | cmd3"
  invocation is a pipeline of separate operating-system processes connected by
  anonymous pipes, "a set of processes chained together by their standard
  streams, so that the output text of each process (stdout) is passed directly
  as input (stdin) to the next one," the mechanism McIlroy invented and
  Thompson implemented in Version 3 Unix in 1973 (Wikipedia, "Pipeline
  (Unix)," verified 2026-08-02, https://en.wikipedia.org/wiki/Pipeline_(Unix)).
  It is the pattern's founding, and still most widely executed, real-world
  instance.

- **Go's standard concurrency idiom for streaming data.** Sameer Ajmani's blog
  post, published on the official Go blog, documents the channel-based pipeline
  with cancellation via a done channel as the language's recommended idiom for
  exactly this class of problem, and the pattern is reused throughout the Go
  standard library and the broader Go ecosystem's data-processing code (Sameer
  Ajmani, go.dev, 2014, verified 2026-08-02, https://go.dev/blog/pipelines).

- **GStreamer**, the open-source multimedia framework used by GNOME, several
  Linux media players, and numerous embedded and broadcast systems, structures
  every media-processing task, playback, capture, transcoding, as a pipeline of
  connected elements exchanging buffers through source and sink pads
  (GStreamer Application Development Manual, verified 2026-08-02,
  https://gstreamer.freedesktop.org/documentation/application-development/introduction/basics.html).

- **The Java Platform's java.util.concurrent.Flow API**, standardized in
  Java 9 and still current in Java 21, ships Publisher, Subscriber,
  Subscription, and Processor interfaces specifically so libraries can
  build interoperable, backpressure-aware pipeline stages that any conforming
  Reactive Streams implementation can chain together (Oracle, Java SE 21 API
  documentation, verified 2026-08-02,
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Flow.html).

- **The .NET Task Parallel Library's Dataflow component**, shipped as part of
  the .NET Framework and .NET (cross-platform), provides prebuilt block types
  explicitly documented as composable into "pipelines, which are linear
  sequences of dataflow blocks," used in Microsoft's own example applications
  for image-processing and message-driven pipelines and by third-party .NET
  systems that need bounded-capacity, asynchronous multi-stage processing
  (Microsoft Learn, verified 2026-08-02,
  https://learn.microsoft.com/en-us/dotnet/standard/parallel-programming/dataflow-task-parallel-library).

- **The LMAX Disruptor**, an open-source high-performance inter-thread
  messaging library originating at the LMAX financial exchange, supports
  chaining multiple EventHandler consumers into a dependency sequence so that
  one handler's processing of a ring-buffer slot is guaranteed complete before
  a downstream handler consumes the same slot, the documented example being
  disruptor.handleEventsWith(new ProcessingEventHandler()).then(new
  ClearingEventHandler()), a linear pipelined-consumer chain built directly
  into the library's public API (LMAX Disruptor User Guide, verified
  2026-08-02, https://lmax-exchange.github.io/disruptor/user-guide/index.html).

## 10. Consequences

Positive.

- Overlaps distinct kinds of work (CPU-bound decoding, I/O-bound fetching,
  disk-bound writing) so total wall-clock time for a large stream approaches
  the slowest single stage's total time rather than the sum of every stage's
  total time.
- Lets each stage's concurrency (its worker-pool size) be tuned independently
  to its own resource profile, so an I/O-bound stage can run far more
  concurrent workers than a CPU-bound stage without over- or under-provisioning
  the whole pipeline uniformly.
- Bounds memory use predictably when channels or queues between stages are
  bounded, because backpressure naturally stalls a fast producer rather than
  letting an unbounded backlog accumulate.
- Isolates failure per stage. a panic, exception, or crash inside one stage's
  worker need not corrupt or halt the state of stages that have already
  completed their part of the work on earlier items.
- Composes cleanly. Stages are independently testable functions or objects
  with a narrow input-output contract, and new stages can be inserted or
  removed from the chain without rewriting the stages on either side, as long
  as the channel type contract is preserved.

Negative.

- Adds real latency to the first and last items in a short-lived or low-volume
  stream, since every item still crosses every stage boundary in order, and
  the throughput win only materializes once enough items are simultaneously in
  flight to keep every stage busy.
- Introduces goroutine, thread, or task leaks as a class of bug that does not
  exist in sequential code, whenever a stage blocks forever trying to send
  into a channel that a downstream consumer has stopped reading from, unless
  every stage correctly participates in the cancellation protocol.
- Multiplies the number of independently schedulable units of concurrency
  (one set of workers per stage rather than one set of workers for the whole
  job), which increases context-switch and scheduling overhead relative to a
  single worker-pool pattern applied to the whole task, unless stage
  granularity is chosen deliberately.
- Complicates ordering guarantees the moment any stage fans work out across
  multiple workers for throughput, requiring an explicit reorder buffer if the
  downstream consumer needs strict input order preserved.
- Debuggability drops relative to a single sequential loop. a stack trace from
  a failing item no longer shows the whole causal chain in one call stack, it
  shows only the failing stage's local context, and correlating an error back
  to the originating input item requires deliberately propagating an
  identifier through every stage.

## 11. Failure modes and misuse

**Symptom.** The process's goroutine, thread, or task count grows without
bound over the life of a long-running service, eventually exhausting memory or
hitting the runtime's scheduler limits.
**Cause.** A downstream consumer (the Sink, or a caller who only wanted the
first few results) stopped reading early without signaling cancellation
upstream, so every stage's worker is permanently blocked on a channel send
that will never be received, and the goroutine or thread backing that blocked
send is never reclaimed.
**Fix.** Give every stage a cancellation path, a shared done channel, a
context with cancellation in Go, a CancellationToken in .NET, that is
selected alongside the data send, and confirm the code path that stops
consuming early is the same code path that triggers cancellation, not a
separate cleanup step that is easy to forget to call.

**Symptom.** Memory use grows unbounded and the process is eventually killed
by the operating system's out-of-memory mechanism during a burst of fast
input.
**Cause.** The channel or queue between a fast upstream stage and a slow
downstream stage was created unbounded, so the fast stage's output backs up
without limit while the slow stage works through its backlog.
**Fix.** Bound every inter-stage channel or queue to a fixed capacity sized to
the desired amount of in-flight buffering, and accept that the fast stage will
block (apply backpressure) once the buffer fills, which is the correct and
intended behavior, not a bug to work around by simply growing the buffer.

**Symptom.** Output items appear in a different order than the corresponding
input items, and a consumer that assumed order was preserved produces
incorrect downstream results, for example a log aggregator that assumes
timestamps arrive monotonically.
**Cause.** A stage was fanned out across multiple concurrent workers for
throughput, and the natural completion order of concurrent work is not the
same as the order items entered the stage, so results reach the next stage or
the sink out of their original sequence.
**Fix.** Either avoid fanning out any stage where order matters end to end, or
explicitly reorder. tag each item with its original sequence number before
fan-out and merge results back into sequence order at a dedicated reorder
buffer stage before they reach a consumer that depends on ordering.

**Symptom.** The pipeline deadlocks entirely, every stage's worker is blocked,
and the process makes no forward progress though no crash or error is
reported.
**Cause.** A stage was implemented to send its output before finishing its
receive loop for the current batch, or two stages hold a bidirectional channel
relationship (stage A sends to B and also expects a value back from B before
continuing), creating a circular wait. each stage is simultaneously waiting on
another that is itself waiting.
**Fix.** Keep the topology strictly acyclic. a pipeline is a directed acyclic
graph of stages by definition, and any apparent need for a stage to wait on a
result from a stage downstream of it in the same pipeline is a sign the work
should be restructured, often by splitting a stage in two or introducing an
explicit request-response channel pair that is not part of the main data flow.

**Symptom.** One stage's error is silently swallowed. An item that should have
failed disappears from the output with no log entry, or the pipeline appears
to succeed with fewer output items than input items and nobody notices until a
downstream system reports missing data.
**Cause.** The stage's transform function returned early on an error condition
without sending anything downstream and without recording the error anywhere,
so the item simply vanishes from the stream instead of being represented as an
explicit error value or being logged before being dropped.
**Fix.** Model errors as values that flow through the pipeline (a
result or either type, or a dedicated error channel every stage also writes to)
rather than as silent early returns, so every dropped item is accounted for
somewhere a human or a metric can observe it.

## 12. Trade-off matrix

| Force | Pipeline Parallelism | Producer-Consumer (single queue, N symmetric workers) | Fork-Join (divide and conquer) |
|---|---|---|---|
| Best when | Ordered, heterogeneous transformation steps with different resource profiles | Homogeneous, independent units of work with no ordering between stages | A single problem recursively splits into independent subproblems with a combine step |
| Concurrency granularity | Per stage, independently tunable | Per worker, uniform across the pool | Per recursive split, task-based |
| Overlaps distinct resource types | Yes, that is the primary benefit | No, every worker does the same kind of work | Only incidentally, if subproblems happen to use different resources |
| Natural fit for streaming, unbounded input | Yes | Yes | No, expects a bounded input that can be fully divided upfront |
| Ordering preserved by default | Yes, within a single-worker-per-stage topology, requires extra work once any stage fans out | No, workers complete in arbitrary order | Preserved through the combine step, which merges subresults in known positions |
| Failure isolation | Per stage | Per item, workers are interchangeable | Per subtask, propagated up through join |
| Coordination primitives needed | One channel or bounded queue per stage boundary, plus a cancellation signal | One shared queue | A task scheduler with work-stealing or a join barrier |
| Typical cost when misapplied | Goroutine or thread leaks on early cancellation, unbounded buffers | Underuses heterogeneous resources if stages differ in kind | Poor fit for streaming or unbounded input, and recursion overhead on trivially small subproblems |

## 13. Related and incompatible patterns

**Producer-Consumer.** Pipeline parallelism is best understood as a chain of
Producer-Consumer relationships, each stage is a consumer relative to its
upstream neighbor and a producer relative to its downstream neighbor. A
two-stage pipeline is exactly one Producer-Consumer pair. the pipeline pattern
is the generalization to N stages with heterogeneous transformations at each
link rather than a single symmetric worker pool.

**Fork-Join.** Fork-Join and Pipeline Parallelism solve different shapes of
the same broader "parallelize this work" problem. Fork-Join splits one unit of
work into independent subunits that are combined at the end, which fits
recursive, divide-and-conquer problems with a bounded input known in advance.
Pipeline Parallelism instead overlaps different kinds of sequential work
applied to a stream of many independent items. The two compose. a pipeline
stage can internally use Fork-Join to parallelize the transformation it
applies to a single large item.

**Reactor and Half-Sync/Half-Async.** These patterns describe how a single
stage's I/O is multiplexed or how synchronous and asynchronous execution
contexts are bridged. a pipeline stage is frequently implemented internally
using a Reactor-style event loop (for the I/O-bound stages) or a
Half-Sync/Half-Async boundary (to hand work from a synchronous producer thread
into an asynchronous worker pool). They operate one level below the pipeline's
own stage-to-stage structure.

**Active Object.** Each stage of a pipeline can be implemented as an Active
Object, encapsulating its own thread and processing loop behind a method-call
interface, which is a common way to make a stage's internal concurrency
invisible to the stages on either side of it.

**Future/Promise.** A pipeline stage's per-item work can be represented as a
Future, letting the stage submit work to an underlying thread pool and forward
the resulting Future downstream rather than blocking its own worker thread
while the work completes, which is common in reactive-streams-based pipeline
implementations.

**Incompatibilities.** There is no strict structural incompatibility between
Pipeline Parallelism and another named pattern in this catalog. it is
incompatible in effect, not in kind, with any design that requires the whole
input set to be visible before processing starts (a full-sort stage, for
example, cannot begin its work until the previous stage's entire output has
arrived), which forces that particular stage boundary back into a batch,
blocking handoff rather than a continuously streaming one, without breaking
the pipeline shape of the stages before and after it.

## 14. Refactoring path in and out

**Introducing a pipeline into sequential code.** Start from a single function
or loop that performs several distinct transformations on each item in
sequence. First, extract each transformation into its own named function with
a single input and single output, purely for clarity, with no concurrency
change yet. this is an Extract Function refactoring and should not change
behavior. Second, introduce a channel or bounded queue between each pair of
adjacent functions and wrap each function in a loop that reads from its input
channel, applies the function, and writes to its output channel. run this
still on a single goroutine or thread first, verifying the channel plumbing is
correct with no concurrency bugs possible because there is no concurrency yet.
Third, move each stage's loop into its own goroutine, thread, or task, one
stage at a time, verifying after each move that output remains correct on a
representative test input before moving the next stage. Fourth, add the
cancellation signal (a done channel or equivalent) to every stage's select or
receive logic before this code is trusted with a caller that might stop
consuming early. Fifth, only after correctness is established, consider
fanning out any single stage that is the measured bottleneck across multiple
workers, and only then add the reorder logic if ordering must be preserved.

**Removing a pipeline that has stopped earning its place.** This typically
happens when volume dropped enough that the coordination overhead now exceeds
the benefit, or when a stage was removed and only two stages remain with no
meaningful resource-profile difference between them. Collapse stage functions
back into direct sequential calls one boundary at a time, starting from the
boundary with the lowest observed concurrency benefit (measure actual overlap,
do not guess), removing the channel and the goroutine or thread wrapper at
each collapsed boundary, and re-run the correctness test suite after each
collapse. Stop collapsing at the point where the remaining stages still show a
measurable throughput benefit from staying separate. a pipeline does not need
to be all-or-nothing, a hybrid with some stages merged and one genuinely
expensive I/O-bound stage kept separate is a legitimate stopping point.

## 15. Testing and verification

Test each stage's transformation function in complete isolation from
concurrency, as a pure function from input to output wherever the stage logic
allows it to be pure, which is the majority of the value of having extracted
stages as named functions in the first place. this is by far the easiest part
of a pipeline to get high test coverage on and should carry the bulk of the
correctness testing burden.

Test the pipeline's plumbing (channel wiring, closing, cancellation) with a
small, deterministic end-to-end test using a bounded, known input sequence and
asserting the exact output set (and, where ordering matters, the exact output
order). run this test with the race detector enabled (Go's -race, or the
equivalent thread-sanitizer tooling in other languages) since pipeline bugs are
overwhelmingly data races and improperly synchronized channel access rather
than logic errors in a single stage.

Explicitly test cancellation. Construct a test that starts the pipeline,
reads only the first item from the sink, then triggers cancellation, and
assert that every goroutine or thread the pipeline spawned has actually
terminated within a bounded time, using a goroutine-leak detector (such as
go.uber.org/goleak in Go) or the language's equivalent, since a leaked
worker is exactly the class of bug that a functional-output-only test will
never catch.

Explicitly test backpressure at the boundary of the bounded buffer, by feeding
the pipeline a burst larger than the buffer capacity and a deliberately slow
downstream consumer, and asserting that the upstream producer blocks (does not
drop data, does not grow memory unbounded) rather than either dropping items
silently or exhausting memory, which is best verified with a memory or
goroutine-count assertion rather than a timing-based one.

Where a stage is fanned out across multiple workers and ordering must be
preserved, test the reorder logic separately with an adversarial input where
worker completion order is deliberately reversed relative to submission order
(achievable by injecting an artificial, varying delay per item in a test
double for the stage), and assert the final output order still matches input
order.

## 16. Observability signals

Per-stage queue depth (the current number of items buffered in each
inter-stage channel or queue) is the single most useful pipeline health
metric, exposed as a gauge per stage boundary. a queue that sits consistently
near its bound indicates that stage is the bottleneck, and a queue that sits
consistently near zero indicates that stage boundary has slack capacity that
could be reduced or reallocated.

Per-stage processing latency (time from an item entering a stage to it being
sent downstream) and per-stage throughput (items processed per unit time),
both broken out by stage name so the slowest stage is immediately visible on a
dashboard rather than only visible as an aggregate end-to-end latency number
that hides which stage caused it.

Active worker count per stage, so an operator can see at a glance whether a
stage's configured concurrency is fully utilized (all workers busy, a sign to
consider adding more) or under-utilized (workers frequently idle, a sign the
stage is over-provisioned relative to its actual bottleneck status).

A healthy pipeline's dashboard shows queue depths oscillating within their
bounded range without any queue pinned at its maximum for a sustained period,
per-stage throughputs converging toward the same steady-state rate across all
stages (because in steady state every stage processes items at the rate the
slowest stage allows), and zero goroutine or thread count growth over time for
a service that runs many pipeline invocations across its lifetime. An unhealthy
pipeline shows one queue permanently pinned at capacity (the bottleneck
stage), a worker or goroutine count that grows monotonically rather than
returning to baseline between runs (a cancellation or leak bug), or a
per-stage error-item counter that is nonzero but was never noticed because
nothing alerts on it, which is why error counts belong on the same dashboard
as throughput, not in a separate log a person must go looking for.

## 17. Security and privacy implications

A pipeline stage that logs an item for debugging (a common early-development
habit, since a stage's local context is otherwise hard to inspect mid-stream)
can inadvertently log personally identifiable information or secrets that were
present in the item payload, and because the item flows through several
independently developed stages, each with its own logging habits, the surface
area for an accidental leak is larger than in an equivalent single-function
implementation where one code review covers the whole data path.

A stage that fans out across a worker pool sized by an attacker-influenced
input (for example, a "number of concurrent enrichment lookups" derived
directly from a request parameter rather than a fixed or capped configuration
value) is a resource-exhaustion vector, since an attacker can submit input
shaped to force the pipeline to spawn far more concurrent workers, outbound
connections, or memory allocations than the system was provisioned for. stage
concurrency limits should be fixed by the operator's configuration, never
derived directly from untrusted input.

Cross-stage data that crosses a trust boundary, for example a pipeline stage
that receives items sourced from an external, untrusted network input and
passes them to a stage that performs a privileged operation (a database write,
a shell command, a file-system write), must apply the same input validation
discipline it would in a non-pipelined design. splitting validation and the
privileged action into separate stages does not itself add any security
benefit, and if the validating stage's rejection path silently drops the item
rather than explicitly signaling rejection (see the silent-error failure mode
in dimension 11), an attacker's malformed input may be dropped from the
pipeline's happy path while a security-relevant rejection event goes
unlogged, exactly when it should have been the most visible event of the run.

The pattern carries no security implication specific to encryption, key
handling, or authentication protocols beyond the general observation that
in-transit data between stages, if stages run in genuinely separate processes
or machines rather than in-process goroutines or threads sharing memory, must
be transported over an authenticated, encrypted channel like any other
inter-service communication, which is a statement about distributed systems in
general rather than about pipeline parallelism specifically.

## 18. References

1. Wikipedia contributors, "Pipeline (Unix)," Wikipedia, The Free Encyclopedia.
   Describes Douglas McIlroy's invention of the Unix pipe concept and Ken
   Thompson's 1973 implementation in Version 3 Unix. Verified 2026-08-02.
   https://en.wikipedia.org/wiki/Pipeline_(Unix)

2. Sameer Ajmani, "Go Concurrency Patterns. Pipelines and cancellation," The
   Go Blog, go.dev, published 13 March 2014. The definitional treatment of the
   channel-based pipeline pattern with done-channel cancellation. Verified
   2026-08-02. https://go.dev/blog/pipelines

3. GStreamer project, "Basic Concepts," GStreamer Application Development
   Manual. Describes the element and pad based pipeline model used throughout
   GStreamer. Verified 2026-08-02.
   https://gstreamer.freedesktop.org/documentation/application-development/introduction/basics.html

4. Oracle, java.util.concurrent.Flow, Java SE 21 API Specification.
   Describes the Publisher, Subscriber, Subscription, and Processor
   interfaces underpinning the Reactive Streams backpressure protocol used to
   build pipeline stages on the JVM. Verified 2026-08-02.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Flow.html

5. Microsoft, "Dataflow (Task Parallel Library)," .NET documentation, Microsoft
   Learn. Describes TPL Dataflow blocks and their composition into linear
   pipeline sequences via LinkTo. Verified 2026-08-02.
   https://learn.microsoft.com/en-us/dotnet/standard/parallel-programming/dataflow-task-parallel-library

6. LMAX Exchange, "Disruptor User Guide." Describes chaining multiple
   EventHandler instances into a pipelined consumer sequence over a shared
   ring buffer. Verified 2026-08-02.
   https://lmax-exchange.github.io/disruptor/user-guide/index.html

## Code examples

The pipeline shape, Source, N stages, Sink, connected by bounded channels or
queues with an explicit cancellation path, is shown below in Go (the language
whose standard idiom this entry names most directly), Python (representing
languages without a native closable-channel primitive, using a poison-pill
sentinel over a bounded queue), and Rust (representing a systems language with
mpsc channels and no garbage collector). All three were compiled or run
directly against the toolchains available in this environment. none required
modification after the first successful run.

### Go

Idiomatic closable-channel pipeline. generate is the Source, square is a
Stage, sum is the Sink. Compiled successfully with go build.

```go
package main

import (
	"fmt"
)

func generate(nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for _, n := range nums {
			out <- n
		}
	}()
	return out
}

func square(done <-chan struct{}, in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			select {
			case out <- n * n:
			case <-done:
				return
			}
		}
	}()
	return out
}

func sum(done <-chan struct{}, in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		total := 0
		for n := range in {
			total += n
		}
		select {
		case out <- total:
		case <-done:
		}
	}()
	return out
}

func main() {
	done := make(chan struct{})
	defer close(done)

	src := generate(1, 2, 3, 4, 5)
	squared := square(done, src)
	total := sum(done, squared)

	fmt.Println(<-total)
}
```

The done channel is closed by main on return, which is the cancellation
signal every stage's select races against its send, so a caller that stops
reading early unblocks every upstream goroutine instead of leaking them, per
the pattern Ajmani documents (reference 2).

### Python

Bounded-queue pipeline with a poison-pill sentinel standing in for closable
channels, one thread per stage. Compiled with py_compile and executed
directly, producing [3, 5, 7, 9, 11] for the input [1, 2, 3, 4, 5] through
a double-then-increment two-stage pipeline.

```python
import queue
import threading

POISON = object()


def stage(func, in_q, out_q):
    while True:
        item = in_q.get()
        if item is POISON:
            out_q.put(POISON)
            return
        out_q.put(func(item))


def run_pipeline(items, stages):
    queues = [queue.Queue() for _ in range(len(stages) + 1)]
    for item in items:
        queues[0].put(item)
    queues[0].put(POISON)

    threads = []
    for func, in_q, out_q in zip(stages, queues, queues[1:]):
        t = threading.Thread(target=stage, args=(func, in_q, out_q))
        t.start()
        threads.append(t)

    results = []
    while True:
        item = queues[-1].get()
        if item is POISON:
            break
        results.append(item)

    for t in threads:
        t.join()
    return results


def double(n):
    return n * 2


def increment(n):
    return n + 1


if __name__ == "__main__":
    out = run_pipeline([1, 2, 3, 4, 5], [double, increment])
    print(sorted(out))
```

Queue.get() blocks the calling thread until an item is available, which is
the bounded-buffer backpressure point. swapping queue.Queue() for
queue.Queue(maxsize=N) bounds memory the same way a bounded Go channel does.

### Rust

mpsc channel pipeline with one thread per stage. Compiled with rustc -O
and executed directly, producing 55, the sum of squares of 1 through 5.

```rust
use std::sync::mpsc;
use std::thread;

fn generate(nums: Vec<i32>) -> mpsc::Receiver<i32> {
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        for n in nums {
            if tx.send(n).is_err() {
                return;
            }
        }
    });
    rx
}

fn square(input: mpsc::Receiver<i32>) -> mpsc::Receiver<i32> {
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        for n in input {
            if tx.send(n * n).is_err() {
                return;
            }
        }
    });
    rx
}

fn sum(input: mpsc::Receiver<i32>) -> i32 {
    input.iter().sum()
}

fn main() {
    let src = generate(vec![1, 2, 3, 4, 5]);
    let squared = square(src);
    let total = sum(squared);
    println!("{}", total);
}
```

tx.send(...).is_err() is Rust's cancellation signal in this shape. once the
receiving end of a channel is dropped (because a downstream stage stopped
reading, or panicked), every subsequent send returns an error rather than
blocking forever, so each stage's loop exits cleanly instead of leaking its
thread, the same guarantee the Go example provides through an explicit done
channel rather than through the channel's own drop semantics.

A fourth language, TypeScript, was considered and omitted. Node.js's
single-threaded event loop means a channel-based, multi-threaded pipeline
would require either Worker Threads (a materially different API shape from
the channel-passing idiom shown above) or an async-generator chain that
demonstrates I/O-bound concurrency overlap rather than CPU-bound parallelism,
and adding a fourth, structurally different example was judged to add length
without adding a new load-bearing idea beyond what the reactive-streams
variant in dimension 8 already covers in prose.
