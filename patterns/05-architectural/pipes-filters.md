---
name: Pipes and Filters
slug: pipes-filters
family: 05-architectural
category: Architectural
aliases: [Pipeline Architecture, Filter Pipeline, Pipe and Filter, Data Flow Architecture]
first_described: "Buschmann, Meunier, Rohnert, Sommerlad, Stal 1996"
maturity: canonical
related: [layered-architecture, microkernel, chain-of-responsibility, decorator, mediator]
incompatible_with: []
verified: 2026-08-02
---

# Pipes and Filters

## 1. Name, aliases, and lineage

The canonical name is Pipes and Filters. It was catalogued as an architectural
pattern by Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad and
Michael Stal in *Pattern-Oriented Software Architecture, Volume 1. A System of
Patterns*, Wiley, 1996, chapter 2, "Architectural Patterns", section "Pipes and
Filters", where it appears alongside Layers, Blackboard, and Broker as one of
the four foundational structural patterns the book presents for organizing a
whole system.

The name is taken directly from Unix pipes, and the borrowing is not
incidental. The mechanism the pattern generalizes was implemented by Ken
Thompson at Bell Labs in 1973, after Douglas McIlroy had spent years arguing
inside Bell Labs that a shell should be able to connect the output of one
program to the input of another without an intermediate file. McIlroy's own
account, quoted on Wikipedia's "Pipeline (Unix)" article
(https://en.wikipedia.org/wiki/Pipeline_(Unix), verified 2026-08-02), describes
Thompson adding the `pipe()` system call and pipe support to the shell and
utilities "in one feverish night", after which "the next day saw an
unforgettable orgy of one-liners as everybody joined in the excitement of
plumbing." The feature first appeared in the Version 3 Unix manual, and the
now familiar `|` notation was introduced by Thompson in Version 4 (same
source, verified 2026-08-02). Buschmann and coauthors took that shell-level
idiom and generalized it into a full architectural pattern for structuring an
entire system as a sequence of independent processing steps, not merely a
notation for chaining shell commands.

The pattern was independently formalized a second time, at message-integration
level rather than process level, by Gregor Hohpe and Bobby Woolf in
*Enterprise Integration Patterns*, Addison-Wesley, 2003, in the messaging
patterns chapter, whose "Pipes and Filters" page gives the intent as
"divide a larger processing task into a sequence of smaller, independent
processing steps (Filters) that are connected by channels (Pipes)"
(https://www.enterpriseintegrationpatterns.com/patterns/messaging/PipesAndFilters.html,
verified 2026-08-02). This is the same pattern applied to message-oriented
middleware instead of operating-system processes, and it is the version most
enterprise-integration engineers meet first, through tools that implement the
Enterprise Integration Patterns (EIP) catalog directly.

Aliases in day-to-day use track which of the two lineages a speaker learned
from. "Pipeline Architecture" and "Data Flow Architecture" are the informal
names used by engineers who arrived at the shape from streaming or ETL work
and never opened either book. "Filter Pipeline" is common in web-framework
documentation, describing the same participants under ASP.NET Core
middleware chains and similar constructs. This entry treats all of them as
the same pattern under the POSA1 name, because POSA1 is the source that first
gave the pattern its formal participants, consequences, and known uses as an
architectural pattern rather than a shell feature or a messaging idiom.

## 2. Problem and context

A system must transform a stream of data through several independent
processing steps, and the set of steps, their order, or the data source
itself is expected to change over the system's life.

The situation shows up in a codebase as one long function or one large class
that reads input, does several unrelated transformations on it in sequence,
and writes output. The first version does one thing. A revision needs to add
a validation step before the transform, or a compression step after it, and
the obvious edit is to insert another block of code into the same function.
Six revisions later the function does eight things, none of it individually
testable, none of it reusable in the next pipeline that needs five of those
eight steps and none of the other three.

The context that makes Pipes and Filters the right answer has three parts,
matching the description POSA1 gives for the pattern's applicability.

- Processing decomposes naturally into a sequence of independent steps, each
  of which reads a stream of data and produces a stream of data, with no step
  needing knowledge of any other step's internals.
- The set of steps, or their order, changes over the life of the system, so
  the cost of rewiring the sequence matters as much as the cost of writing an
  individual step.
- The data volume is large enough, or the processing time per step is long
  enough, that the steps benefit from running concurrently, each one starting
  work on the output of the previous step before that step has finished
  processing everything.

Compilers are the textbook instance of the third condition. A source file
passes through lexing, parsing, semantic analysis, optimization, and code
generation, and a classical compiler design runs each of these as a separate
pass over the whole program, which is architecturally Pipes and Filters even
when a single process runs every stage.

## 3. Forces

Pipes and Filters balances a fixed set of competing pressures, and it resolves
them by trading throughput and reuse for latency and end-to-end visibility.
This dimension is largely engineering judgement, reasoning about which force
the pattern favours in a typical deployment, rather than a claim that can be
independently checked against a source.

- Reuse against specialization. A filter that only reads and writes a stream,
  with no dependency on its neighbours, is trivially reusable in a different
  pipeline. That same isolation prevents a filter from taking a shortcut that
  a more specialized, tightly coupled step could take, such as skipping a
  redundant pass over data that a neighbouring step already touched.
- Concurrency against simplicity. Running each filter as an independent
  process, thread, or goroutine lets stages overlap, so total wall-clock time
  can approach the slowest stage rather than the sum of every stage. That
  concurrency introduces buffering, backpressure, and shutdown ordering as
  real engineering problems the naive sequential version never had.
- Composability against efficiency. Because a pipe carries an entire stream,
  not just one document, filters can be reordered or swapped at will and the
  system keeps a uniform interface between stages. That uniformity costs a
  serialization or copy step at every pipe boundary that a monolithic
  function performing every transformation in one pass over memory would
  never pay.
- Testability against transactional integrity. Each filter is unit-testable
  in isolation because it depends on nothing but its input and output stream.
  The pattern gives up an easy answer for what happens when the fourth filter
  in an eight-stage pipeline fails after the first three have already
  produced and possibly delivered output, because there is no single
  transactional boundary around the whole pipeline the way there is around a
  single function call.
- Latency against throughput. Streaming architectures, where a filter starts
  emitting partial output before it has consumed all of its input, favour low
  end-to-end latency. Batch-style filters that must see an entire input
  before producing any output favour throughput and simplicity of
  implementation, at the cost of the pipeline stalling on its slowest batch
  stage.

## 4. Applicability and non-applicability

Reach for Pipes and Filters when the following hold.

- The processing task decomposes into a sequence of steps, each of which
  reads one kind of stream and writes another, with no step needing to see
  more than its immediate input.
- The steps, or their order, are expected to change independently of each
  other, so the ability to insert, remove, or reorder a step without editing
  the others has real value.
- The same step is genuinely useful in more than one pipeline, for example a
  validation filter reused across three different ingestion pipelines that
  otherwise share nothing.
- The volume of data or the cost per stage justifies concurrent execution,
  where a later stage can begin work on early output before an earlier stage
  has finished.
- The failure mode of "some output already left the pipeline before a later
  stage failed" is acceptable, or can be handled by an outer mechanism such
  as a dead-letter queue, rather than needing atomic all-or-nothing semantics.

Do NOT reach for Pipes and Filters when any of the following hold.

- The processing is a single transformation with no natural decomposition
  into independent steps. Forcing one function into three filter classes
  connected by pipes adds indirection with no corresponding reuse or
  concurrency benefit.
- The steps share deep, mutable state that cannot be expressed as the stream
  flowing between them. A pipeline whose "filters" actually communicate
  through a shared database row defeats the isolation the pattern exists to
  provide, and the shared-state design is closer to Blackboard than to Pipes
  and Filters.
- The operation must be transactional across every step, with all-or-nothing
  commit semantics and no acceptable intermediate state. A payment-capture
  flow that must never leave a customer charged with no matching ledger entry
  is a poor fit for a pattern whose per-stage failure model is local, not
  global, unless a compensating-transaction layer is added on top, at which
  point the added machinery may cost more than the pipeline saved.
- Per-record latency is the overriding concern and even one extra stage
  boundary is unacceptable, for example a hot path inside a database
  engine's row comparison function, where a hand-written single pass beats
  any stage-by-stage indirection.
- The steps genuinely need to see the whole dataset at once to make a
  decision, such as a sort or a join over the full stream, where framing the
  operation as a "filter that reads one record at a time" is either
  impossible or requires buffering the entire input inside a single stage
  anyway, which erases the pattern's memory and latency advantages.

## 5. Structure

POSA1 names four participants for the pattern, and this entry follows that
vocabulary because it is the source under which the pattern was first
catalogued with a formal structure.

- **Filter.** The unit of processing. It reads data from an input pipe or
  pipes, transforms it, and writes the result to an output pipe or pipes. A
  filter knows nothing about which filter produced its input or which filter
  will consume its output, only the shape of the data on the pipe. Filters
  are classified as active, when the filter drives its own thread of control
  and pulls data at its own pace, or passive, when an external driver calls
  the filter and pushes data into it.
- **Pipe.** The connector between two filters. A pipe carries a stream of
  data, buffers it as needed so that a fast producer does not overrun a slow
  consumer, and defines nothing about the meaning of the data it carries,
  only its transport. In an in-process implementation a pipe is often a
  bounded queue or channel. Across processes it is a literal operating-system
  pipe, a socket, or a message broker topic.
- **Data source.** The origin of the stream that enters the first filter. It
  may be a file, a socket, a message queue, or, in the active-filter variant,
  a filter that has no upstream neighbour and instead generates data itself.
- **Data sink.** The destination that consumes the output of the final
  filter, symmetrical to the data source. A sink may itself be another
  pipeline, in which case one pipeline's sink is the next pipeline's source.
- **Pump.** An optional active data source used when nothing else drives the
  flow of data through the pipeline. A pump is the thing that periodically
  reads or generates new input so that passive downstream filters have
  something to process, most visible in pull-based pipelines where every
  filter is otherwise reactive rather than self-driving.

The relationships between these participants are strictly linear or, in the
more general form, form a directed acyclic graph. Each filter has one or more
input pipes and one or more output pipes, and no filter has a direct reference
to any other filter, only to the pipe abstraction it reads from or writes to.
This is the structural property that gives the pattern its reuse and
recomposition benefits, and it is also the property that a violated
implementation most often loses first, described further under dimension 11.

## 6. ASCII structure diagram

```text
                Filter                Filter                Filter
              +--------+            +--------+            +--------+
Data Source ->|  A     |--- Pipe -->|  B     |--- Pipe -->|  C     |--> Data Sink
              +--------+            +--------+            +--------+

   each filter:
     - reads only from its own inbound pipe(s)
     - writes only to its own outbound pipe(s)
     - has no reference to any other filter

   the general form is a directed acyclic graph, not only a line:

              +--------+
              | Filter |----+
   Source --->|   A    |    |    +--------+
              +--------+    +--->| Filter |---> Sink
                             |    |   C    |
              +--------+     |    +--------+
              | Filter |-----+
   Source --->|   B    |
              +--------+
```

## 7. Dynamics

At runtime a filter has one job on each side of the pipeline it sits inside,
receive from its inbound pipe, do its transformation, send to its outbound
pipe, and the specific rhythm of that job depends on whether the filter is
active or passive.

In the active-filter, pull-based flow, each filter runs on its own thread of
control. It reads a chunk of data from its inbound pipe, blocking if none is
available yet, processes that chunk, and writes the result to its outbound
pipe, blocking if the downstream pipe's buffer is already full. This is the
model behind Unix shell pipes, where each program in a pipeline is a separate
process, and behind Go's channel-based pipeline idiom, where each stage is one
or more goroutines. Backpressure emerges naturally from this model, because a
slow consumer's full buffer blocks a fast producer without either side
needing to coordinate explicitly.

In the passive-filter, push-based flow, an external pump or the previous
filter directly calls the next filter's processing method with each unit of
data, and the filter has no thread of its own. This is closer to how a
composed sequence of `map` or transform operators over a synchronous iterator
behaves in languages without lightweight concurrency, and it is the shape the
TypeScript and Python samples in this entry both use, because it needs no
runtime scheduler to demonstrate.

Two failure signals matter at runtime and are worth naming here because they
recur across every implementation variant in dimension 8. First, a pipe's
buffer filling to capacity is the visible symptom of a downstream filter that
is slower than its upstream neighbour, and how the pipeline responds, by
blocking the producer, by dropping data, or by growing the buffer without
bound, is a design decision, not an accident. Second, a filter that closes or
errors mid-stream must propagate that closure downstream so that later
filters do not block forever waiting on input that will never arrive, and
must propagate a matching signal upstream so that an earlier filter does not
keep producing output nobody is left to consume.

```text
   time -->

   Filter A   [read]--[work]--[write]--[read]--[work]--[write]---> ...
                          \                          \
   Pipe A-B                \--data-->                 \--data-->
                              \                            \
   Filter B              [read]--[work]--[write]--[read]--[work]-->
                                     \                          \
   Pipe B-C                          \--data-->                  \--data-->
                                        \                             \
   Filter C                       [read]--[work]--[write]--[read]--[work]-->

   stages overlap: Filter B starts on the first chunk from A while A is
   already producing the second chunk, so total time approaches the
   slowest single stage rather than the sum of every stage.
```

## 8. Implementation variants

The pattern shows up in four broad shapes in real code, and the shape a team
chooses depends almost entirely on whether concurrency is worth its cost for
the volume of data involved.

- **Process-level, via the operating system.** Each filter is a separate
  operating-system process, and each pipe is a literal OS pipe, exactly as in
  a Unix shell command like `grep error access.log | sort | uniq -c`. This is
  the strongest form of isolation, since a crash in one filter cannot corrupt
  another filter's memory, and it is the only variant where filters can be
  written in entirely different languages with zero coordination beyond the
  byte stream on the pipe.
- **Thread or coroutine level, via channels.** Each filter runs as one or
  more goroutines, green threads, or async tasks within a single process, and
  pipes are implemented as bounded channels or queues. Go's standard
  concurrency idiom for this is described directly in the official Go blog
  post "Go Concurrency Patterns, Pipelines and cancellation" by Sameer Ajmani,
  published 13 March 2014, which defines a pipeline as "a series of stages
  connected by channels, where each stage is a group of goroutines running
  the same function" (https://go.dev/blog/pipelines, verified 2026-08-02).
  This variant keeps most of the concurrency benefit of the process-level
  form while avoiding the cost of inter-process serialization, at the price
  of losing the crash-isolation guarantee, since a panic in one goroutine can
  bring down the whole process unless explicitly recovered.
- **Function or generator composition, single-threaded.** Each filter is a
  pure function or a generator that consumes an iterable and yields a new
  iterable, and the pipes are implicit in the function composition itself,
  with no actual buffering, thread, or channel involved. This is the
  Python and TypeScript shape used in the code samples for this entry, and
  it is the right choice when the volume of data does not justify concurrent
  execution and the value being sought is purely the decomposition and reuse
  benefit, not the throughput benefit.
- **Middleware or message-broker level, via named connectors.** Each filter
  is a component registered with a framework or broker, and the pipe is a
  named queue, topic, or route the framework wires together based on
  configuration rather than direct code references. Apache Camel implements
  the Enterprise Integration Patterns catalog's Pipes and Filters pattern
  directly under the name Pipeline, and its own documentation states "Camel
  supports the Pipes and Filters from the EIP patterns in various ways. With
  Camel, you can separate your processing across multiple independent
  Endpoints which can then be chained together"
  (https://camel.apache.org/components/next/eips/pipeline-eip.html, verified
  2026-08-02). This variant is the most configuration-driven of the four,
  trading compile-time type safety for the ability to rewire a production
  pipeline without a code deployment.

A related but distinct idiom worth naming so it is not mistaken for a fifth
variant, streaming media frameworks such as GStreamer build a directed graph
of elements connected through typed "pads" rather than untyped byte pipes,
where "elements receive data on their sink pads and generate data on their
source pads" and pads negotiate a shared data format before any data flows
(https://gstreamer.freedesktop.org/documentation/application-development/basics/pads.html,
verified 2026-08-02). This is the same architectural shape as Pipes and
Filters with a type-negotiating pipe instead of an untyped one, and it
demonstrates that the pattern's core idea, independent stages connected by a
uniform transport, survives even when the transport itself becomes richer
than a raw byte stream.

## 9. Known production uses

- **The Unix shell and its command pipeline.** The canonical instance of the
  pattern, where independent processes such as `grep`, `sort`, and `uniq` are
  connected by the shell's `|` operator, each unaware of the identity of its
  neighbour, communicating only through the shared convention of text on
  standard input and standard output. Implemented by Ken Thompson in 1973 at
  Bell Labs following Douglas McIlroy's design, first documented in the
  Version 3 Unix manual (https://en.wikipedia.org/wiki/Pipeline_(Unix),
  verified 2026-08-02).
- **Apache Camel's Pipeline EIP.** Camel implements the Enterprise
  Integration Patterns Pipes and Filters pattern as a first-class routing
  construct named Pipeline, letting message-processing endpoints be
  chained together and, per Camel's own route DSL, making a Camel route's
  default multi-step behaviour an implicit pipeline even without the
  construct being named explicitly
  (https://camel.apache.org/components/next/eips/pipeline-eip.html, verified
  2026-08-02).
- **GStreamer's element and pad architecture.** Every GStreamer application,
  from a simple `gst-launch-1.0` command line to a full media player, is a
  graph of elements such as decoders, filters, and sinks connected through
  typed pads, with data flowing from a source element through zero or more
  filter elements to a sink element
  (https://gstreamer.freedesktop.org/documentation/application-development/basics/pads.html,
  verified 2026-08-02).
- **Node.js streams.** The `readable.pipe(destination)` method attaches a
  writable stream to a readable one so that data flows automatically from
  source to destination with built-in backpressure, and the same method
  chains, so `r.pipe(z).pipe(w)` composes a read stream, a gzip transform
  stream, and a write stream into a three-stage pipeline in one expression,
  documented directly in the Node.js stream API reference
  (https://nodejs.org/api/stream.html, verified 2026-08-02).
- **Go's pipeline idiom.** Documented on the official Go blog as the
  standard pattern for structuring concurrent, streaming computation in Go,
  where a pipeline is "a series of stages connected by channels", each stage
  a group of goroutines that receive from inbound channels and send to
  outbound channels (https://go.dev/blog/pipelines, verified 2026-08-02). The
  standard library's own `io.Pipe` function provides the connecting primitive
  this idiom is built on.

## 10. Consequences

Positive consequences.

- Each filter is independently reusable in a different pipeline, because it
  depends only on the shape of the data crossing its pipes, never on the
  identity of a specific neighbour.
- Adding, removing, or reordering a step is a change local to the pipeline's
  wiring, not a change to the internals of any existing filter, which lowers
  the cost of evolving the processing sequence over time.
- Concurrent variants let stages overlap in time, so a pipeline's total
  latency can approach the cost of its slowest stage instead of the sum of
  every stage.
- Each filter is unit-testable in isolation, since its dependencies reduce to
  a well-defined input stream and a well-defined output stream, with no
  hidden collaborators to mock.
- Filters written in different languages, or running as different processes,
  can be composed as long as they agree on the transport, which is what
  makes the Unix shell pipeline compose `grep`, written in C, with an
  arbitrary user script written in anything that reads standard input.

Negative consequences.

- There is no single transactional boundary around the whole pipeline. If
  the fourth filter in an eight-stage pipeline fails, the first three have
  already produced output, and that output may already have left the
  pipeline through a partially consumed pipe, so recovering to a consistent
  state needs a mechanism the pattern itself does not provide.
- Every pipe boundary is a serialization or copy point. Data crossing from
  one filter to the next usually pays a cost, whether that is an actual
  operating-system context switch, a channel send with its associated
  synchronization, or a plain in-memory copy, and a naive pipeline with many
  small stages can lose more to that overhead than it gains from
  decomposition.
- Debugging a multi-stage pipeline is harder than debugging a single
  function, because a wrong final result requires isolating which stage
  introduced the error, and a stalled pipeline requires distinguishing
  between a slow stage, a full buffer downstream of a slow consumer, and a
  genuine deadlock.
- Sharing context across filters that legitimately need it, a request ID for
  logging correlation, a security principal, or a deadline, has no built-in
  channel in the base pattern and must be threaded through the data stream
  itself or attached as metadata alongside every record, which either
  couples every filter to a shared envelope format or forces an
  out-of-band mechanism.
- A pipeline whose filters buffer their entire input before producing any
  output loses the pattern's latency and memory advantages while keeping all
  of its indirection cost, effectively becoming a slower, harder to debug
  version of a plain sequential function call.

## 11. Failure modes and misuse

- **Symptom.** A pipeline that used to run in a few seconds now takes
  minutes, with CPU usage on most stages near zero and one stage pegged.
  **Cause.** A single slow filter has become a bottleneck, and every
  upstream filter is blocked writing to a full pipe while every downstream
  filter is blocked waiting on empty input, so the whole pipeline runs at
  the speed of its slowest stage even though the architecture visually
  suggests parallel work is happening.
  **Fix.** Profile per-stage throughput directly, not the pipeline as a
  whole, and either optimize the slow stage, run multiple instances of it
  in parallel with a fan-out and fan-in around it, or increase buffer sizes
  if the bottleneck is bursty rather than sustained.

- **Symptom.** The pipeline hangs forever on shutdown, with no error and no
  progress, and has to be killed externally.
  **Cause.** A filter's outbound pipe is never closed after that filter's
  own inbound pipe closes, so downstream filters keep reading a channel or
  file descriptor that will never receive more data and will never signal
  end-of-stream either, which is the single most common bug in hand-rolled
  concurrent pipeline implementations.
  **Fix.** Every filter must close every outbound pipe it owns exactly once,
  on every exit path including error paths, and the pipeline's shutdown
  logic must be tested by deliberately closing an inbound pipe early and
  asserting the whole chain shuts down within a bounded time.

- **Symptom.** Two filters that were supposed to be independent start
  producing subtly different results depending on which one runs first, or
  a change to one filter unexpectedly changes another filter's output.
  **Cause.** The filters share mutable state that bypasses the pipe, most
  often a shared cache, a shared database connection with implicit session
  state, or a static or module-level variable one filter reads and another
  writes. This silently converts the design from Pipes and Filters into an
  undocumented Blackboard pattern, losing the reasoning-in-isolation
  property the pipe abstraction exists to provide.
  **Fix.** Audit every filter for state that is not either purely local or
  explicitly part of the data flowing on a pipe, and either move that state
  into the stream as an explicit field or eliminate the sharing entirely.

- **Symptom.** Memory usage grows without bound over a long-running
  pipeline, eventually crashing the process.
  **Cause.** A downstream filter is slower than its upstream producer and
  the pipe between them has an unbounded buffer, so the producer never
  experiences backpressure and keeps writing faster than the consumer can
  drain, accumulating queued data in memory indefinitely. This is common in
  hand-rolled pipelines built on unbounded language-level queues rather than
  a bounded channel or an OS pipe, both of which enforce backpressure by
  construction.
  **Fix.** Bound every pipe's buffer explicitly, and make the producer block
  or apply an explicit drop policy when the buffer is full rather than
  growing it silently.

- **Symptom.** Adding a new filter to the middle of an existing pipeline
  breaks a filter three steps downstream that was never touched.
  **Cause.** A filter reaches past its own inbound pipe to read from an
  earlier filter's internal state, or relies on an implicit ordering
  guarantee, such as records always arriving in file order, that the new
  filter happens to violate by reordering or batching its own output. This
  is a violation of the structural rule from dimension 5 that a filter has
  no reference to any other filter, and every downstream break traces back
  to that violation.
  **Fix.** Enforce, by code review or by the type system where the language
  allows it, that a filter's only dependency is the shape of the data on its
  own pipes, never a reference to another filter or an assumption about
  another filter's internal implementation.

- **Symptom.** A pipeline that processes personally identifiable data leaks
  a fragment of that data into a log file or a metrics dashboard nobody
  expected.
  **Cause.** A filter added for observability purposes, most often a debug
  logging step or a metrics-tagging step, was inserted into the pipeline
  without auditing what data crosses that particular pipe, and it logs the
  entire record rather than a redacted or aggregated summary of it.
  **Fix.** Treat every new filter insertion into an existing pipeline as an
  event requiring the same data-classification review as any other new code
  that touches sensitive data, addressed further under dimension 17.

## 12. Trade-off matrix

The alternatives compared here are named patterns, not a generic naive
approach. Layers organizes a system into horizontal tiers where each layer
depends only on the layer directly beneath it. Chain of Responsibility passes
a single request along a chain of handlers, any one of which may fully
consume the request and stop propagation. Mediator centralizes interaction
logic between a set of collaborating objects into one coordinator object
rather than distributing it across the collaborators themselves.

| Force | Pipes and Filters | Layers | Chain of Responsibility | Mediator |
|---|---|---|---|---|
| Data model | A stream flows through every stage in order | A request passes down and a response passes back up through tiers | A single request or message passes along a chain, any handler may stop it | Objects communicate only through a central coordinator, not a flowing stream |
| Every stage runs | Yes, by default every filter processes every unit of data | Yes, every layer sits on the call path | No, a handler may consume the request and stop the rest of the chain from running | Not applicable, there is no ordered stage list |
| Natural concurrency | Strong, stages can overlap in time on a continuous stream | Weak, layers are usually synchronous call and return | Weak, a chain is normally walked sequentially per request | Weak, the mediator usually processes one interaction at a time |
| Reuse of a single step in a different composition | Strong, a filter has no reference to its neighbours | Moderate, a layer is reusable but tied to the tier above and below it in practice | Moderate, a handler is reusable but the chain order still matters to behaviour | Weak, mediator logic is usually specific to one set of collaborators |
| Coupling between steps | None beyond the shared pipe data shape | Adjacent layers only, by contract | None beyond the shared request type | All collaborators are coupled to the mediator, not to each other |
| Best fit | Bulk transformation of a stream through independent stages | Separating concerns by level of abstraction across a whole application | Deciding which one of several possible handlers should own a request | Reducing many-to-many coupling among a fixed set of collaborating objects |

## 13. Related and incompatible patterns

**Layered Architecture.** Layers and Pipes and Filters are often confused
because both draw as a vertical or horizontal stack of boxes. The distinction
is that a layer calls the layer beneath it and waits for a return value,
forming a request and response relationship, while a filter writes to an
outbound stream that a downstream filter reads independently, with no return
value flowing back. A system can combine both, for example a web application
built in Layers where the business logic layer internally uses a Pipes and
Filters pipeline to process an uploaded file.

**Microkernel.** A microkernel's plug-in modules are often themselves
implemented as filters in a processing pipeline, particularly when the
microkernel's core is a media, build, or data-processing tool whose
extensibility comes from letting third parties register new pipeline stages
rather than new top-level features.

**Chain of Responsibility.** Both patterns pass data through a linear
sequence of independent units, and the structural diagrams look similar.
The behavioural difference is decisive. In Pipes and Filters every filter
runs, transforming the data and passing it on. In Chain of Responsibility any
handler may fully consume the request and stop it from reaching the rest of
the chain, and a handler that does not want to act on a request typically
passes it through unmodified rather than transforming it.

**Decorator.** A Decorator wraps a single object to add behaviour around
every call to that object's interface, and decorators nest around one
underlying component. Pipes and Filters connects multiple independent
components in sequence over a stream. Some pipeline implementations, notably
`io.Reader` wrapping in Go or `InputStream` wrapping in Java, use Decorator
at the level of an individual pipe's transport while the pipeline as a whole
remains Pipes and Filters at the architectural level, so the two patterns
frequently coexist at different granularities within the same system.

**Mediator.** Mediator centralizes coordination logic that Pipes and Filters
deliberately keeps out of any single participant, so they express opposite
philosophies for organizing collaboration, one distributed and unaware, one
centralized and aware. Neither pattern is incompatible with the other in a
single system, but they solve the same category of problem, coordinating
multiple collaborating units, in structurally opposite ways, so choosing one
for a given interaction usually means not choosing the other for that same
interaction.

**Blackboard.** Blackboard is the pattern Pipes and Filters silently
degrades into when filters share mutable state outside their pipes, as
described in the failure mode in dimension 11. Blackboard is a legitimate
pattern in its own right for problems with no obvious sequential
decomposition, where multiple specialists read and write a shared data
structure opportunistically, but arriving at that shape by accident inside
what was meant to be a clean pipeline is the misuse this entry warns against,
not a deliberate architectural choice.

No pattern in this catalog is structurally incompatible with Pipes and
Filters at the whole-system level, because it operates at the level of data
flow between independent units, a concern orthogonal to how any individual
unit is internally structured.

## 14. Refactoring path in and out

Introducing Pipes and Filters into code that does not have it follows a
sequence of small, verifiable steps.

1. Identify the sequence of transformations currently living inside one
   function or one class, and write down, in order, what each conceptual
   step does to the data, even before touching any code.
2. Extract the first identified step into its own function or class that
   takes the current input type and returns an intermediate type, leaving
   the calling code to invoke it and pass the result into the rest of the
   original function unchanged. This is a plain Extract Method or Extract
   Class step, verified by running the existing test suite with no expected
   change in output.
3. Repeat step 2 for each remaining conceptual step, always keeping the
   overall function's observable output identical after each extraction.
4. Once every step is its own function or class with a well-defined input
   and output type, replace the single calling function's body with an
   explicit composition, a fixed sequence of calls or a fold over a list of
   filter functions, so that reordering the sequence becomes a change to
   that composition alone.
5. Only after the sequential version is proven correct, introduce
   concurrency if the volume of data or the cost of a per-stage bottleneck
   justifies it, replacing direct function calls with channels, queues, or
   actual pipes, one boundary at a time, testing shutdown behaviour at each
   boundary before moving to the next.

Removing Pipes and Filters, when the pipeline has stopped earning its place,
follows the mirror sequence.

1. Confirm the pipeline genuinely no longer needs the flexibility to
   reorder, reuse, or run stages concurrently, since removing the pattern
   removes those capabilities along with the indirection.
2. Inline the filters back into a single function in the pipeline's fixed
   order, one filter at a time, running the test suite after each inlining
   to confirm behaviour has not changed.
3. Once every filter is inlined, remove the now-unused pipe abstraction and
   any buffering or channel machinery it required, and simplify data
   handling to whatever the single merged function actually needs, rather
   than the general stream interface the pipeline demanded.

## 15. Testing and verification

Each filter's isolation is the pattern's largest testing advantage. A filter
that only depends on its input stream type and only produces its output
stream type needs no mocks, no fixtures beyond representative input data, and
no knowledge of the rest of the pipeline to be tested completely on its own,
which is a genuine and measurable simplification compared with testing a
single large function that performs the same set of transformations inline.

What becomes harder is testing the pipeline as a whole, specifically its
behaviour under partial failure and under backpressure, neither of which is
visible from any single filter's unit tests.

- Test each filter's core transformation logic with ordinary input, empty
  input, and malformed input, asserting on its output stream alone, with no
  dependency on the rest of the pipeline.
- Test the pipeline's composition, not just its individual filters, with a
  small end-to-end test that feeds a known input through the full chain and
  asserts on the final output, catching wiring mistakes such as two filters
  connected in the wrong order that no individual filter test can catch.
- Test shutdown and error propagation explicitly, by injecting a failure
  into a middle filter and asserting that upstream filters stop producing,
  downstream filters stop waiting, and no pipe is left blocked forever. This
  is the single highest-value test class for any concurrent implementation
  of the pattern, because the failure mode it targets, the hang described in
  dimension 11, otherwise only surfaces in production under load.
- For a streaming implementation, test backpressure directly by pairing a
  fast producer with a deliberately slow consumer in the test and asserting
  memory usage stays bounded rather than growing without limit, which
  ordinary functional tests of individual filters will never exercise.
- Use a fake or in-memory pipe implementation for unit tests of a single
  filter, and reserve the real transport, an actual OS pipe, an actual
  message broker, for the smaller number of full-pipeline integration tests,
  since the real transport is usually the slowest and most environment
  dependent part of the test suite.

## 16. Observability signals

A healthy pipeline, viewed from a dashboard, shows every stage's throughput
converging toward roughly the same steady rate, with buffer occupancy for
every pipe sitting well below its maximum most of the time, only spiking
briefly during load bursts and draining back down afterward.

- **Per-stage throughput**, records or bytes processed per unit time by
  each filter individually, is the signal that identifies a bottleneck
  stage directly, rather than the aggregate pipeline throughput, which only
  reveals that a bottleneck exists somewhere, not which stage it is in.
- **Pipe occupancy**, how full each pipe's buffer is at any moment, tells
  whether the pipeline is balanced. A pipe that is consistently near full
  indicates the filter downstream of it is the current bottleneck, and a
  pipe that is consistently near empty indicates the filter upstream of it
  is the bottleneck instead.
- **Per-stage latency**, the time a single unit of data spends inside one
  filter, distinguished from end-to-end pipeline latency, localizes a slow
  stage the same way per-stage throughput does, and the two together
  usually agree on which stage is at fault.
- **Error and drop counts per stage**, separated by which filter produced
  them, are necessary because a pipeline-wide error rate says nothing about
  whether the errors are concentrated in one fragile stage or spread evenly
  across all of them, which changes where the fix belongs.
- **Pipeline-wide backlog**, the total number of records currently in
  flight across every pipe combined, is the signal that answers whether the
  whole pipeline is falling behind its input rate, distinct from any single
  stage's occupancy, and is the number most worth alerting on for a
  pipeline that must keep pace with a continuous, unbounded input stream.

Judgement, drawn from operating streaming systems rather than from a single
citable source. The single most useful dashboard for a production pipeline is
a horizontal bar per stage showing current throughput next to current
downstream pipe occupancy, because that one view answers the two questions
that matter most during an incident, which stage is slow, and how much
buffered work is currently stuck behind it.

## 17. Security and privacy implications

Every pipe boundary is a place where data crosses a trust or a serialization
boundary, and each of those boundaries deserves the same scrutiny an API
boundary would receive, not less scrutiny because it sits inside what feels
like internal plumbing.

- **Data exposure at every stage.** Any filter, including one added for a
  purpose as ordinary as logging, metrics, or debugging, has access to the
  full record on the pipe it reads from, unless the pipeline explicitly
  narrows what each filter sees. A pipeline processing personal data must
  audit every filter, not only the filters whose stated purpose involves
  that data, for what fields it reads and what it does with them, since the
  failure mode described in dimension 11, a debug filter leaking a field
  into a log line, is a data exposure incident, not a cosmetic bug.
- **Trust boundary crossings between process-level filters.** When filters
  run as separate operating-system processes or across a network, as in the
  message-broker variant, each pipe is also a network or inter-process
  boundary that can be intercepted, replayed, or spoofed unless it is
  explicitly protected. A pipeline whose stages communicate over an
  unauthenticated message broker inherits every trust assumption the broker
  itself makes, and a filter that trusts its input pipe unconditionally is
  vulnerable to a compromised or misconfigured upstream stage injecting
  malformed or malicious data.
- **Amplified blast radius from filter reuse.** The same property that makes
  a filter reusable, its independence from any specific pipeline, also means
  a vulnerability discovered in one widely reused filter, an insufficient
  input validation step, for example, is present in every pipeline that
  filter is composed into, not only the one where the bug was found. An
  organization reusing filters across many pipelines should track which
  pipelines a given filter is deployed into, the same way a shared library's
  dependents are tracked, so a fix can be propagated everywhere it is needed.
- **Denial of service through unbounded buffering.** The unbounded-buffer
  failure mode described in dimension 11 is also a security concern, not
  only a reliability one, because an attacker able to influence a slow
  downstream consumer or a fast upstream producer can deliberately trigger
  unbounded memory growth in a pipeline that lacks explicit backpressure,
  turning an availability weakness into an exploitable denial-of-service
  vector.
- **Partial completion as an information leak.** Because the pattern has no
  built-in transactional boundary, a pipeline that fails partway through can
  leave observable side effects, a file already written by an earlier
  filter, a partial record already delivered to a downstream sink, that
  reveal information about data the pipeline was never meant to fully
  process, which matters for any pipeline handling data subject to a
  right-to-erasure or similar regulatory constraint.

## 18. References

- Buschmann, Frank, Meunier, Regine, Rohnert, Hans, Sommerlad, Peter, and
  Stal, Michael. *Pattern-Oriented Software Architecture, Volume 1. A System
  of Patterns*. Wiley, 1996. Chapter 2, "Architectural Patterns", section
  "Pipes and Filters".
- Hohpe, Gregor, and Woolf, Bobby. *Enterprise Integration Patterns.
  Designing, Building, and Deploying Messaging Solutions*. Addison-Wesley,
  2003. "Pipes and Filters" page, messaging patterns chapter.
  https://www.enterpriseintegrationpatterns.com/patterns/messaging/PipesAndFilters.html,
  verified 2026-08-02.
- Wikipedia. "Pipeline (Unix)".
  https://en.wikipedia.org/wiki/Pipeline_(Unix), verified 2026-08-02.
- Wikipedia. "Pipeline (software)".
  https://en.wikipedia.org/wiki/Pipeline_(software), verified 2026-08-02.
- Ajmani, Sameer. "Go Concurrency Patterns, Pipelines and cancellation". The
  Go Blog, 13 March 2014. https://go.dev/blog/pipelines, verified 2026-08-02.
- Apache Software Foundation. "Pipeline EIP". Apache Camel documentation.
  https://camel.apache.org/components/next/eips/pipeline-eip.html, verified
  2026-08-02.
- GStreamer project. "Pads, Caps, and Capabilities". GStreamer Application
  Development Manual.
  https://gstreamer.freedesktop.org/documentation/application-development/basics/pads.html,
  verified 2026-08-02.
- OpenJS Foundation. "Stream". Node.js API documentation.
  https://nodejs.org/api/stream.html, verified 2026-08-02.

## Code examples

Three languages are shown. TypeScript and Python use the function or
generator composition variant from dimension 8, the simplest form to read and
the one that needs no runtime scheduler. Go uses the channel-based variant,
because it is the language whose standard idiom for this pattern is
documented directly by its own maintainers and is the clearest illustration
of the concurrent dynamics described in dimension 7. Java, Rust, and Swift
are omitted here because the pattern does not add idiomatic value beyond what
the three shown languages already demonstrate, generator or channel
composition, and including all six would repeat the same structure six times
rather than show anything new.

Every sample below was compiled or run during authoring. TypeScript was
type-checked and compiled with `tsc --strict` then executed with `node`.
Python was executed directly with `python3`. Go was executed with `go run`.
All three produced the expected output, filtering blank lines, upper-casing
the remainder, and numbering the result.

### TypeScript

```typescript
type Filter<T> = (input: Iterable<T>) => Iterable<T>;

function pipeline<T>(source: Iterable<T>, ...filters: Filter<T>[]): Iterable<T> {
  return filters.reduce((stream, filter) => filter(stream), source);
}

function* removeBlank(lines: Iterable<string>): Iterable<string> {
  for (const line of lines) if (line.trim().length > 0) yield line;
}

function* upperCase(lines: Iterable<string>): Iterable<string> {
  for (const line of lines) yield line.toUpperCase();
}

function* numberLines(lines: Iterable<string>): Iterable<string> {
  let n = 1;
  for (const line of lines) yield `${n++}: ${line}`;
}

const input = ["  hello world  ", "", "second line", "   "];
const result = pipeline(input, removeBlank, upperCase, numberLines);
for (const line of result) console.log(line);
```

Each filter is a generator function with the same shape, an iterable in and
an iterable out, so `pipeline` can fold any list of them over a source with
no filter aware of its neighbours. Because generators are lazy, no filter
runs to completion before the next filter starts consuming its output, which
is the single-threaded analogue of the overlap shown in dimension 7's
dynamics diagram, without any actual concurrency.

### Python

```python
from typing import Iterable, Iterator


def remove_blank(lines: Iterable[str]) -> Iterator[str]:
    for line in lines:
        if line.strip():
            yield line


def upper_case(lines: Iterable[str]) -> Iterator[str]:
    for line in lines:
        yield line.upper()


def number_lines(lines: Iterable[str]) -> Iterator[str]:
    for i, line in enumerate(lines, start=1):
        yield f"{i}: {line}"


def pipeline(source: Iterable[str], *filters):
    stream = source
    for f in filters:
        stream = f(stream)
    return stream


if __name__ == "__main__":
    data = ["  hello world  ", "", "second line", "   "]
    for line in pipeline(data, remove_blank, upper_case, number_lines):
        print(line)
```

Python's generator functions are the idiomatic filter unit for this pattern,
the same lazy composition as the TypeScript sample. `pipeline` here takes a
variadic list of filters rather than a fixed array, showing the same fold
composition with Python's own calling convention. No filter imports or
references another filter, satisfying the structural rule from dimension 5.

### Go

```go
package main

import (
	"fmt"
	"strings"
)

func source(items []string) <-chan string {
	out := make(chan string)
	go func() {
		defer close(out)
		for _, s := range items {
			out <- s
		}
	}()
	return out
}

func removeBlank(in <-chan string) <-chan string {
	out := make(chan string)
	go func() {
		defer close(out)
		for s := range in {
			if strings.TrimSpace(s) != "" {
				out <- s
			}
		}
	}()
	return out
}

func upperCase(in <-chan string) <-chan string {
	out := make(chan string)
	go func() {
		defer close(out)
		for s := range in {
			out <- strings.ToUpper(s)
		}
	}()
	return out
}

func numberLines(in <-chan string) <-chan string {
	out := make(chan string)
	go func() {
		defer close(out)
		n := 1
		for s := range in {
			out <- fmt.Sprintf("%d: %s", n, s)
			n++
		}
	}()
	return out
}

func main() {
	data := []string{"  hello world  ", "", "second line", "   "}
	pipeline := numberLines(upperCase(removeBlank(source(data))))
	for line := range pipeline {
		fmt.Println(line)
	}
}
```

Each function is a filter that spawns its own goroutine, reads from an
inbound channel, and closes its outbound channel when its input is
exhausted, matching the active-filter dynamics from dimension 7 exactly, and
matching Sameer Ajmani's description of a Go pipeline stage as a group of
goroutines that receive from inbound channels and send to outbound channels.
The `defer close(out)` call in every stage is the concrete answer to the
hang failure mode in dimension 11, propagating end-of-stream downstream so
that no later stage blocks forever on a channel nothing will ever write to
again.
