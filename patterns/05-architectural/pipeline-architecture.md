---
name: Pipeline Architecture
slug: pipeline-architecture
family: 05-architectural
category: Architectural
aliases: [Pipes and Filters, Pipeline Pattern, Data Pipeline, Filter Chain]
first_described: "McIlroy and Thompson, Bell Labs, 1973 (mechanism); Buschmann, Meunier, Rohnert, Sommerlad, Stal 1996 (formal pattern name)"
maturity: canonical
related: [chain-of-responsibility, decorator, iterator, event-driven-architecture, microkernel-architecture]
incompatible_with: []
verified: 2026-08-02
---

# Pipeline Architecture

## 1. Name, aliases, and lineage

The pattern's mechanism and its catalog name have two different birthdays, and
conflating them is the first mistake a reader makes with this pattern.

The mechanism was born at Bell Labs. Douglas McIlroy proposed connecting a
program's output directly to another program's input in an internal memo in
October 1964, and Ken Thompson implemented the pipe() system call and the
pipe notation in the Thompson shell for Version 3 Unix in 1973
([Wikipedia, Pipeline (Unix), citing McIlroy's account of the implementation
happening in one session at Bell Labs](https://en.wikipedia.org/wiki/Pipeline_(Unix)),
verified 2026-08-02). Version 4 Unix added the vertical bar `|` as the
notation, replacing an earlier syntax, which is the symbol every reader now
associates with the idea. McIlroy later distilled the design philosophy that
grew out of this mechanism into a short manifesto published in a special
Unix issue of the Bell System Technical Journal on 8 July 1978. "Write
programs that do one thing and do it well. Write programs to work together.
Write programs to handle text streams, because that is a universal
interface" (M. D. McIlroy, E. N. Pinson, B. A. Tague, "Unix Time-Sharing
System. Foreword", Bell System Technical Journal, volume 57, issue 6, 1978,
pages 1902 to 1903, [as quoted on Wikipedia's Unix philosophy
article](https://en.wikipedia.org/wiki/Unix_philosophy), verified
2026-08-02). That sentence is the closest thing this pattern has to a design
constitution, and it is a statement about composition, not about any
particular syntax.

The catalog name most software architects actually use is **Pipes and
Filters**. It was formalized as an architectural pattern, with a named
structure of participants and a documented set of consequences, by Frank
Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, and Michael Stal in
*Pattern-Oriented Software Architecture, Volume 1. A System of Patterns*,
Wiley, 1996, chapter 2 ([confirmed via lecture notes summarizing the POSA1
chapter structure and participant vocabulary,
https://john.cs.olemiss.edu/~hcc/docs/Patterns/Pipes/Pipes.html](https://john.cs.olemiss.edu/~hcc/docs/Patterns/Pipes/Pipes.html),
verified 2026-08-02). POSA1 is where the vocabulary this entry uses, filter,
pipe, active filter, passive filter, pump, comes from as a named
architectural pattern rather than as folk knowledge about shell scripting.

Two aliases carry different connotations in different communities. **Pipes
and Filters** is the term used in software architecture and system design
literature, where the emphasis is on the structural pattern independent of
any particular runtime. **Data pipeline** is the term used in data
engineering, where the emphasis is on batch and streaming ETL work rather
than in-process composition, and where the individual stages are commonly
called stages, steps, or tasks rather than filters. **Filter chain** is used
in some web framework documentation (notably the Java Servlet specification's
FilterChain) for an in-process variant of the same idea applied to HTTP
request and response processing. This entry treats all of these as the same
architectural pattern wearing different clothes for different audiences, and
notes where the clothes actually change the semantics, particularly around
error handling and backpressure.

The pattern is closely related to, and frequently confused with, Chain of
Responsibility. Section 13 draws that boundary precisely, because it is the
single most common point of confusion a reader will hit.

## 2. Problem and context

A system needs to transform a stream of data through a sequence of
independent processing steps, and the set of steps, their order, or their
implementation is expected to change over the system's lifetime. Consider a
build tool that must lex, parse, type-check, optimize, and code-generate a
source file. Consider a log ingestion service that must parse a raw line,
enrich it with geolocation, redact personally identifiable fields, and write
the result to a sink. Consider an image processing tool that must decode,
resize, apply a filter, and re-encode a photo. In every one of these cases
the naive first implementation is a single function or a single class that
does everything inline, in one method body, with each step's logic
interleaved with the next step's logic and with the control flow that
decides what runs when.

That naive implementation works until one of three things happens, and in
production systems one of them always eventually happens. The set of steps
needs to grow, for example a new PII field needs to be redacted, or a new
target architecture needs a new code generation backend. The order of steps
needs to become configurable, for example some deployments need the redaction
step and some do not, or a customer wants to reorder resize before filter.
Or the throughput characteristics of the steps diverge so far that running
them all in one thread wastes hardware, for example decoding a RAW photo is
CPU-bound and takes 200 milliseconds while writing the encoded JPEG to S3 is
I/O-bound and takes 2 seconds, and running both sequentially in one thread
per image serializes work that could overlap.

Pipeline Architecture addresses this by decomposing the single monolithic
transformation into a sequence of independent, single-responsibility filter
components, each of which consumes data from an input, applies one
transformation, and produces data to an output, with the plumbing between
filters, the pipe, extracted into a separate, reusable abstraction. The
context in which this decomposition earns its cost is specifically a
linear or near-linear data flow. A workflow with heavy branching,
cycles, or many-to-many fan-out between steps is not the context this
pattern was designed for, and forcing it into a pipeline shape produces the
misuse documented in section 11.

## 3. Forces

**Composability versus per-step overhead.** Splitting one function into N
filters connected by pipes lets any subset of those filters be reused,
reordered, or swapped independently, but every pipe introduces a hop, and
depending on the pipe implementation that hop can mean a function call, a
channel send with a context switch, a buffer copy, or a network round trip.
The pattern trades a fixed per-call overhead for the ability to recompose
the system without touching filter code.

**Uniformity versus expressive power.** The pattern gets its power from
every filter presenting the same input and output shape, which is what lets
filters be reordered or substituted without a rewrite. That uniformity is
also the pattern's biggest constraint. A filter that genuinely needs to
consult two upstream sources, or that needs to fan its output out to
three different downstream consumers with different lifetimes, does not fit
the uniform one-in, one-out shape without either awkward workarounds or a
different pattern entirely (see section 4 and section 13 on fan-out).

**Backpressure and memory versus throughput.** An unbounded pipe between a
fast producer and a slow consumer will buffer without limit and eventually
exhaust memory, which is the single most common production failure of this
pattern (see section 11). Bounding the pipe and blocking the producer trades
raw throughput for a bounded memory footprint, and the size of that bound is
a genuine engineering judgment call that trades latency for throughput
smoothing.

**Testability versus indirection.** Each filter, tested in isolation with a
known input and a known expected output, is trivially unit-testable because
it has no dependency on its neighbors, only on the shared pipe contract. The
cost is that no single filter's test proves the pipeline as a whole is
correct, which is a distinct concern addressed in section 15.

**Operability versus visibility.** A pipeline running as one process is easy
to observe. A pipeline distributed across processes or machines, which is
the common case once throughput or team ownership boundaries push filters
apart, requires per-stage observability to be designed in deliberately, or
the operator loses the ability to see which stage a slow or stuck item is
sitting in. Section 16 covers what that visibility actually needs to look
like.

This pattern sacrifices raw single-function speed and the ability to see the
whole transformation as one linear read, in exchange for independent
testability, independent deployability of stages, and the ability to
recompose the sequence of steps without touching the steps themselves.

## 4. Applicability and non-applicability

### When to reach for it

- The data flows through a fixed or near-fixed sequence of transformations,
  and each transformation is naturally expressed as taking one input and
  producing one output. A compiler front end (lex, parse, resolve, type
  check) is the textbook case.
- The set of steps is expected to change over the life of the system, either
  because new steps get added (a new ETL enrichment stage) or because steps
  need to be reordered or made optional per deployment or per customer.
- Different steps have meaningfully different resource profiles (CPU-bound
  versus I/O-bound, or different scaling needs), and separating them lets
  each be scaled, retried, or deployed independently.
- Multiple teams need to own different steps independently, and a clean pipe
  contract lets those teams work without coordinating on a shared internal
  data structure.
- The transformation needs to be testable step by step, with each step's
  correctness verifiable against fixed inputs and outputs in isolation from
  the rest of the chain.

### When NOT to reach for it, with the reason

- **The workflow branches based on data content in ways that change which
  steps run next**, not just whether a step is a no-op. Pipes and Filters
  assumes the topology is fixed at composition time; a workflow whose next
  step depends at runtime on the result of the current step, with genuinely
  different downstream steps for different outcomes, needs a state machine
  or a workflow engine (see the Workflow Engine and State Machine entries),
  not a linear pipe chain, or the pipeline degenerates into filters that
  each contain an internal switch statement, which defeats the pattern's
  single-responsibility premise.
- **A step genuinely needs random access to the whole dataset**, not just
  the current element or a bounded window of recent elements, for example a
  step that needs to compute a global median before it can process any
  individual record. Forcing that into a streaming pipe either requires
  buffering the entire dataset in one filter, which erases the memory
  benefit the pattern exists to provide, or requires a two-pass design that
  the linear pipeline shape does not express cleanly. A batch aggregation
  pattern or a MapReduce-shaped pattern fits this case better.
- **The number of steps is small, fixed for the system's lifetime, and never
  independently reusable.** A three-line function that validates, then
  saves, a form submission does not need the ceremony of filter interfaces,
  pipe wiring, and per-stage testing; a plain function composition is
  cheaper to read and to change. The pattern's cost is only justified once
  reuse, reordering, or independent scaling is a real, not hypothetical,
  requirement.
- **Latency for a single item matters more than throughput for a stream**,
  and the pipe implementation under consideration is queue-based with
  buffering (see section 11's head-of-line blocking failure mode). A
  request-response RPC call does not want to sit behind three buffered
  stages of unrelated work.
- **The steps have circular dependencies on each other's output**, for
  example step 3 needs to revise a decision step 1 already made based on
  what step 4 will produce. A pipeline is by definition acyclic; a cyclic
  dependency needs a different pattern, commonly a shared mutable state plus
  an explicit control loop, or a full redesign of the step boundaries so the
  cycle does not exist.
- **The steps must run inside one transaction with atomic all-or-nothing
  commit semantics across every step**, for example a financial transfer
  that must not leave money in an intermediate state visible to any other
  process. Independent filters connected by pipes have no shared transaction
  boundary by default; adding one requires either a saga pattern layered on
  top or abandoning the pipeline decomposition for that specific operation.

## 5. Structure

The canonical participants, following the POSA1 vocabulary
([https://john.cs.olemiss.edu/~hcc/docs/Patterns/Pipes/Pipes.html](https://john.cs.olemiss.edu/~hcc/docs/Patterns/Pipes/Pipes.html),
verified 2026-08-02).

**Filter.** The unit of computation. A filter reads data, applies exactly
one transformation, and writes the transformed data onward. A filter is
either **active**, meaning it owns its own thread, process, or coroutine and
pulls input from its upstream pipe and pushes output to its downstream pipe
on its own schedule, or **passive**, meaning it is invoked as a plain
function call by whatever drives the pipeline, with no independent thread of
control. Active filters are what makes a shell pipeline like `grep foo |
sort | uniq -c` run all three programs concurrently; passive filters are
what makes a chain of `.map().filter().reduce()` calls in a language
standard library run inline in the caller's own call stack.

**Pipe.** The connector between two adjacent filters. A pipe transports data
from one filter's output to the next filter's input, and, in any pipe
implementation that matters in production, also provides synchronization
between a producer and a consumer running at different speeds. The pipe is
the seam where the pattern's most consequential engineering decisions live,
buffered or unbounded, blocking or dropping, in-process or across a network.

**Data source.** The origin of the stream. A data source either actively
produces data on its own schedule (a socket that pushes bytes as they
arrive) or passively provides data on request (a file the first filter
reads from when it is ready).

**Data sink.** The terminus of the stream. A data sink either actively pulls
final results (a consumer that reads from the pipeline when it wants more)
or passively accepts what is pushed to it (a write to standard output or a
database insert).

**Pump.** An optional driver used when every filter in the chain is passive.
Because passive filters do not have their own thread of control, something
has to call the first filter, take its output, call the second filter with
that output, and so on. That driver is the pump. It appears explicitly in
POSA1's structural description and is exactly what a language's `reduce`
built over a chain of pure functions is doing under the hood.

The essential structural property, regardless of implementation, is that
each filter's contract depends only on the shape of the pipe, never on the
identity of its neighbors. Filter B does not know or care whether its
input came from filter A or from a data source directly; it only knows the
pipe's data shape. This is what makes filters independently substitutable
and is the property every implementation variant in section 8 must
preserve or the pattern has been abandoned in practice even where its name
survives in a variable called pipeline.

## 6. ASCII structure diagram

```
  DATA SOURCE                                                  DATA SINK
  (file, socket,                                             (file, socket,
   queue, request)                                            queue, response)
        |                                                            ^
        v                                                            |
  +-----------+     pipe     +-----------+     pipe     +-----------+
  |  FILTER A |------------->|  FILTER B |------------->|  FILTER C |
  | (e.g.     |   [buffer,   | (e.g.     |   [buffer,   | (e.g.     |
  |  parse)   |   backpress] |  enrich)  |   backpress] |  encode)  |
  +-----------+              +-----------+              +-----------+
        ^                          ^                          ^
        |                          |                          |
   single input,             single input,               single input,
   single output              single output               single output
   (uniform contract          (uniform contract           (uniform contract
    shared by every            shared by every             shared by every
    filter in the chain)       filter in the chain)        filter in the chain)

  Optional PUMP drives passive filters that have no thread of their own.

  +------+   calls A(x)   +---+   calls B(A(x))   +---+   calls C(B(A(x)))
  | PUMP |--------------->| A |------------------->| B |------------------>  out
  +------+                +---+                    +---+
```

## 7. Dynamics

Two distinct runtime shapes exist, and confusing them is a common source of
bugs when a design that assumed one shape gets implemented in the other.

**Active-filter dynamics (concurrent, push or pull driven).** Each filter
runs on its own thread, goroutine, process, or coroutine. Filter A begins
producing as soon as it has its first output ready and pushes it into the
pipe to B without waiting for A to finish its entire input. B, running
concurrently, pulls from the pipe as soon as data is available, processes
it, and pushes to C. All three filters are in flight simultaneously on
different items, the way a factory assembly line has a different unit at
each station at the same instant. This is what gives shell pipelines their
speed. `gunzip large.log.gz | grep ERROR | sort` starts sorting the first
matched lines while `gunzip` is still decompressing bytes near the end of
the file. The synchronization discipline that keeps this correct is exactly
the blocking behavior of the pipe itself. a bounded pipe blocks A's write
when B is not keeping up, and blocks B's read when A has not produced
anything yet, which is the backpressure mechanism examined in section 11.

**Passive-filter dynamics (pump-driven, single thread of control).** Nothing
runs until the pump calls it. The pump calls A with the initial input, A
returns its complete output, the pump immediately calls B with that output,
B returns, the pump calls C. No two filters execute concurrently; the whole
chain runs to completion inside one call stack, the way `functools.reduce`
or a chain of `.then()` calls composes pure functions. This shape has no
backpressure concern because there is no concurrent producer to outrun a
consumer, but it also has no concurrency benefit, and if any filter blocks
on I/O the entire pipeline blocks with it unless the language's own
concurrency primitives (an event loop, an async or await chain) are layered
underneath the passive-filter abstraction, which is exactly what
asyncio pipelines and JavaScript Promise chains do.

```
Active-filter (concurrent, streaming) timeline.

 time -->
 A:  |--produce item1--|--produce item2--|--produce item3--|
 B:                     |--consume item1, produce item1'--|--consume item2...
 C:                                        |--consume item1', write out--|--...

 (B starts as soon as A's first item is available; three filters overlap.)

Passive-filter (pump-driven, sequential) timeline.

 time -->
 pump: call A(in) --> A returns out_a --> call B(out_a) --> B returns out_b
                                                              --> call C(out_b)
                                                                   --> done

 (Nothing overlaps. Each filter's full execution completes before the next
  filter is even invoked.)
```

## 8. Implementation variants

**OS-level, process-connected pipes.** The original variant. Each filter is
an independent operating-system process; the pipe is a kernel-provided
anonymous pipe created by the pipe() system call, a unidirectional byte
stream with a kernel-managed buffer, on Linux 65,536 bytes by default since
kernel 2.6.11, adjustable via /proc/sys/fs/pipe-max-size
([man7.org pipe(7),
https://man7.org/linux/man-pages/man7/pipe.7.html](https://man7.org/linux/man-pages/man7/pipe.7.html),
verified 2026-08-02). Writing to a full pipe blocks the writer; reading from
an empty pipe blocks the reader; when every write end is closed the reader
sees end-of-file. This is the shell pipeline, `cmd1 | cmd2 | cmd3`, and it is
the variant where the pattern's backpressure story is enforced directly by
the kernel with no application code needed.

**In-process, thread- or goroutine-connected channels.** Each filter is a
concurrently running unit within one process; the pipe is an in-memory,
synchronized queue, a bounded or unbounded channel. Go's `chan` type with a
fixed capacity is the idiomatic form of this variant, and it is deliberately
modeled on the Unix pipe's blocking semantics. This variant avoids the
per-item serialization and inter-process context-switch cost of the OS-level
variant, at the price of confining the pipeline to one process's memory
space and losing the OS's automatic cleanup on process crash.

**In-process, iterator- or generator-connected lazy chains.** Each filter is
a pure function operating on a lazily evaluated sequence; the pipe is not a
buffer at all but a pull-based protocol, the consumer asks the producer for
the next item and the producer computes it on demand. Python generators
chained with `yield from`, Rust's Iterator trait with adapter methods like
`.map()` and `.filter()`, and Java 8 Stream all implement this variant.
There is no independent thread of control and no buffer between stages by
default, so backpressure is not a distinct concern, the puller simply does
not ask for more until it wants more, which is the cheapest possible
backpressure but only works when the whole chain is single-threaded and
synchronous.

**Passive functional composition with an explicit pump.** Each filter is a
plain function with a documented input and output type; the pump is
whatever code calls them in sequence, commonly `reduce` over a list of
functions or explicit sequential calls. This variant has the least
ceremony and is the right choice when there is no concurrency need at all,
just a desire to keep each transformation step independently testable and
independently named.

**Message-broker-connected distributed pipeline.** Each filter is an
independently deployed service or job; the pipe is a durable queue or a
topic in a message broker (Kafka, RabbitMQ, SQS), which adds durability
across process and machine crashes at the cost of network latency per hop
and the operational burden of running the broker. This is the shape data
engineering calls an ETL pipeline once each stage is its own scheduled job,
and the shape stream processing calls a topology once each stage is a
continuously running consumer group, as in Kafka Streams (section 9).

**Reactive-stream connected, backpressure-typed chain.** Each filter
implements a standardized interface with an explicit, protocol-level
backpressure signal, most notably the JVM Reactive Streams specification's
four interfaces, Publisher, Subscriber, Subscription, and Processor,
where a Subscriber calls Subscription.request(n) to tell its upstream
Publisher exactly how many items it is currently willing to receive
([reactive-streams.org,
https://www.reactive-streams.org/](https://www.reactive-streams.org/),
verified 2026-08-02). This is the most explicit encoding of backpressure of
any variant in this list, because it makes the demand signal a first-class,
typed part of the protocol rather than an implicit property of a buffer's
fullness.

## 9. Known production uses

- **The Unix and Linux shell pipeline itself.** Every `cmd1 | cmd2 | cmd3`
  invocation is a live instance of the OS-level variant, connecting
  independent processes through kernel pipes with 64 KiB buffers and
  blocking backpressure ([man7.org pipe(7),
  https://man7.org/linux/man-pages/man7/pipe.7.html](https://man7.org/linux/man-pages/man7/pipe.7.html),
  verified 2026-08-02).
- **LLVM's pass pipeline.** LLVM's new pass manager chains a sequence of
  module, CGSCC, function, and loop passes over the compiler's intermediate
  representation, with adaptors nesting a lower-level pass inside a
  higher-level manager and an analysis manager caching results like
  dominator trees between passes ([LLVM documentation, New Pass Manager,
  https://llvm.org/docs/NewPassManager.html](https://llvm.org/docs/NewPassManager.html),
  verified 2026-08-02). This is the passive, pump-driven variant applied to
  compiler optimization, and it is the same shape POSA1 names as a
  classical compiler use case (lexer, parser, semantic analysis, code
  generation) ([https://john.cs.olemiss.edu/~hcc/docs/Patterns/Pipes/Pipes.html](https://john.cs.olemiss.edu/~hcc/docs/Patterns/Pipes/Pipes.html),
  verified 2026-08-02).
- **Apache Beam's Pipeline and PTransform model.** A Beam Pipeline
  encapsulates an entire data processing task as a directed acyclic graph of
  PTransforms connected by PCollections, and the same graph runs
  unmodified on batch and streaming runners, with unbounded PCollections
  divided into logical windows for aggregation ([Apache Beam programming
  guide,
  https://beam.apache.org/documentation/programming-guide/](https://beam.apache.org/documentation/programming-guide/),
  verified 2026-08-02). This is the message-broker-adjacent, distributed
  variant applied to large-scale ETL, and it is one of the clearest
  real-world instances of the pattern's DAG structure (section 4 notes that
  pure linear pipelines are the common case, but Beam demonstrates the
  pattern generalizes to a DAG of filters as long as each edge still carries
  a single-producer, single-consumer stream contract).
- **Kafka Streams' processor topology.** A Kafka Streams application defines
  a topology of source processors, which read from a Kafka topic with no
  upstream; stream processors, which transform records; and sink processors,
  which write to a topic with no downstream, connected into a directed graph
  and instantiated across parallel stream threads and tasks for partitioned,
  ordered processing ([Confluent documentation, Kafka Streams Architecture,
  https://docs.confluent.io/platform/current/streams/architecture.html](https://docs.confluent.io/platform/current/streams/architecture.html),
  verified 2026-08-02). This is the message-broker-connected distributed
  variant, and its source and sink processor terminology maps directly onto
  the data source and data sink participants of the POSA1 structure.
- **Jenkins Pipeline (Pipeline-as-code CI/CD).** Jenkins Pipeline treats a
  continuous delivery workflow as a versioned Jenkinsfile defining stages
  such as Build, Test, and Deploy, executed in sequence by the Jenkins
  engine acting as the pump ([Jenkins documentation, Pipeline,
  https://www.jenkins.io/doc/book/pipeline/](https://www.jenkins.io/doc/book/pipeline/),
  verified 2026-08-02). Every CI/CD system that models a build as ordered
  stages, GitHub Actions jobs, GitLab CI stages, CircleCI workflows, is the
  same architectural pattern applied to release engineering rather than to
  data transformation.
- **JVM Reactive Streams and its adopters.** The Reactive Streams
  specification, whose JVM API became java.util.concurrent.Flow in JDK 9,
  standardizes non-blocking backpressure for asynchronous stream pipelines
  ([reactive-streams.org,
  https://www.reactive-streams.org/](https://www.reactive-streams.org/),
  verified 2026-08-02), and is implemented by Project Reactor and RxJava,
  both of which expose fluent `.map().filter().flatMap()` pipeline chains
  used throughout production Spring WebFlux and Android reactive codebases.

## 10. Consequences

### Positive

- Each filter can be unit-tested in complete isolation, given a known input
  and asserting a known output, with no need to stand up its neighbors.
- Filters are independently reusable across different pipelines; the same
  redaction filter can sit in a logging pipeline and an analytics pipeline
  without modification, because it depends only on the pipe's data shape.
- The pipeline's topology, the order and membership of the filter list,
  becomes a piece of configuration or composition code that is easy to read
  and easy to change, separate from any individual filter's internal logic.
- Filters with different resource profiles can be scaled, deployed, or
  parallelized independently once the pipe boundary between them is
  explicit, which is what lets a distributed pipeline run a CPU-bound
  filter on many workers while an I/O-bound filter runs on fewer.
- Active-filter variants of the pattern give genuine concurrency for free.
  Three filters connected by pipes run concurrently on separate cores
  without any explicit thread management by the filters themselves; the
  concurrency is a property of the wiring, not of the filter code.

### Negative

- Every pipe hop is overhead that a single monolithic function does not
  pay. In tight loops or latency-sensitive request paths this overhead is
  measurable and sometimes dominant; see the trade-off matrix in section
  12 for when a monolith wins.
- The uniform, single-input single-output contract forces awkward
  workarounds for any filter that genuinely needs multiple inputs or
  needs to fan out to multiple downstream consumers, and code that hacks
  around this constraint erodes the pattern's core benefit.
- End-to-end error handling is genuinely harder than in a monolith, because
  an exception in filter B by default only tells filter B's immediate
  caller something went wrong; propagating that failure meaningfully to
  the pipeline's overall caller, with the item that caused it and the
  stage it failed in, requires deliberate design (see section 11).
- Debugging a pipeline requires either tracing the item through every stage
  or having per-stage observability already built, because a single stack
  trace from a monolithic function no longer exists; the failure surfaces
  wherever the item happened to be.
- An unbounded or poorly bounded pipe converts a slow consumer into an
  unbounded memory liability, the single most common real-world outage this
  pattern causes (section 11).

## 11. Failure modes and misuse

**Unbounded buffering causing out-of-memory kills.** Symptom. A pipeline
that processes fine under light load starts getting killed by the operating
system's out-of-memory killer, or a language runtime's heap grows without
bound, hours or days into a run, specifically when one stage is slower than
its upstream. Cause. The pipe between the fast producer and the slow
consumer has no capacity bound, so every item the producer emits before the
consumer catches up sits in memory, and under a sustained speed mismatch
that queue grows without limit. Fix. Bound every pipe's capacity explicitly.
A Go channel declared with `make(chan T, 0)` (unbuffered) or a small fixed
capacity forces the producer to block, which is a deliberate transfer of
backpressure upstream, rather than to buffer without limit; in a reactive
stream, this is exactly what Subscription.request(n) exists to prevent.
Choosing an unbounded queue "to be safe" is the misuse; the bound is what
makes the pipeline safe.

**Head-of-line blocking on a single slow item.** Symptom. Overall pipeline
throughput drops to near zero even though only one item out of thousands is
genuinely slow to process, and the slow item is nowhere near the front of
what looks like the visible backlog. Cause. A single-lane pipe processes
items strictly in order; if item 500 takes ten seconds in filter B while
items 501 through 10,000 would each take ten milliseconds, none of them can
be processed until item 500 clears, because the pipe has no concept of
skipping ahead. Fix. Either shard the pipeline into parallel lanes keyed by
a partition key so one slow item only blocks its own lane, which is exactly
what Kafka Streams' per-partition parallelism does, or give the slow filter
its own timeout and dead-letter path so it cannot indefinitely occupy the
lane, or, when ordering genuinely does not matter for a given filter, use a
worker pool consuming from a shared queue rather than a strict single-file
pipe.

**Silent data loss on filter exceptions.** Symptom. Items are known to have
entered the pipeline, confirmed by an upstream log or metric, but never
appear at the sink, and no error is ever logged. Cause. A filter throws or
panics partway through processing an item, and the surrounding code, often
a generic try or except pass or an unhandled goroutine panic, swallows the
error instead of propagating it, so the item is simply gone and nothing
downstream or upstream ever finds out. Fix. Every filter boundary needs an
explicit decision about what happens to a failed item. commonly, route it
to a dead-letter queue with the original payload and the exception, never
silently drop it, and emit a counter metric on every drop path so the
failure is visible in aggregate even before anyone reads a specific log
line (see section 16).

**Filters that secretly depend on their neighbor's identity or internal
state.** Symptom. Reordering two filters that look independent, or
substituting a filter for a functionally equivalent replacement, breaks the
pipeline in a way that is not explainable by the pipe's documented
contract. Cause. A filter reaches around the pipe contract, for example by
reading a global variable another specific filter is known to set, or by
relying on side effects of a specific upstream filter's implementation
rather than on the data the pipe actually carries. Fix. Enforce, by code
review discipline and ideally by construction, that a filter's only
allowed input is what arrives through its pipe. If two filters genuinely
need to share context, that context belongs in the pipe's data shape as an
explicit field, not as an implicit shared side channel.

**Modeling a branching workflow as a pipeline anyway.** Symptom. A "filter"
in the middle of the chain grows a large conditional or switch statement
that decides, based on the item's content, which of several different
downstream code paths to invoke, and the pipeline's linear diagram no
longer describes what the code actually does. Cause. The underlying problem
was never a linear transformation; it was a workflow with genuine branches,
and the team defaulted to Pipes and Filters because it was the familiar
shape rather than because it fit. Fix. Recognize the branch as a signal
that a state machine or workflow-engine pattern is the better fit (see
section 4's non-applicability list), and either split the pipeline into two
or more genuinely separate linear pipelines selected by an upstream router,
or move to an explicit workflow representation where the branching is a
first-class part of the model rather than hidden inside one filter's body.

## 12. Trade-off matrix

Compared against the two most commonly considered named alternatives for the
same class of problem, a monolithic single function or method, and the
Chain of Responsibility pattern, across the forces named in section 3.

| Force | Pipeline Architecture (Pipes and Filters) | Monolithic single function | Chain of Responsibility |
|---|---|---|---|
| Composability, reuse of individual steps | High. Any filter is independently reusable in a different pipeline because it depends only on the pipe's data shape. | Very low. A step is a private code block inside one function and cannot be reused without extracting it first. | Low to moderate. A handler is reusable but typically carries a reference to the next handler as internal state, coupling it more tightly to chain assembly than a pipeline filter is coupled to pipe assembly. |
| Per-call overhead for a single item | Moderate to high, depending on the pipe variant; every hop is a function call at minimum and can be a channel send, a buffer copy, or a network round trip at worst. | Lowest. One function call, no intermediate hops. | Moderate. Similar per-hop overhead to a passive-filter pipeline, one call per handler in the chain. |
| Concurrency across steps for free | High, in active-filter variants; independent filters connected by pipes run concurrently with no explicit thread management inside filter code. | None. A single function runs on one thread with no independent stage concurrency, though internal steps could be manually parallelized. | None by default. A chain typically processes one request through handlers sequentially on the caller's thread, unless the caller adds concurrency separately. |
| Suitability for a request that must stop at the first applicable step and skip the rest | Poor fit. Every filter in a pipeline is expected to run on every item; short-circuiting requires an explicit escape mechanism that is not part of the base pattern. | Trivial. A single function can return at any point. | Purpose-built for exactly this. Chain of Responsibility's defining feature is that a handler can consume the request and stop propagation, which the pattern documents as its core intent. |
| Independent testability of each step | High. Each filter is tested with a fixed input, asserting a fixed output, with no dependency on neighbors. | Low. Testing one internal step typically requires exercising the whole function or extensive mocking of internal state. | High, similar to a pipeline filter, each handler can be tested with a fixed request and a fixed expected outcome (handled or passed on). |
| Fit for a linear, fixed-shape data transformation with changing steps over time | Best fit. This is the pattern's native problem shape. | Poor fit once the step count grows past a handful, because every change requires editing the shared function body. | Poor fit; Chain of Responsibility's semantics (a handler either consumes the request or passes it unchanged) do not naturally express a sequence of transformations, each of which is expected to modify the data. |

## 13. Related and incompatible patterns

**Chain of Responsibility (closely related, frequently confused, distinct
intent).** Both patterns connect a sequence of components that a piece of
data or a request travels through. The difference is in what happens at
each stop. A pipeline filter is expected to transform every item and pass
the transformed result onward; every filter runs on every item, and the
pipeline's output is the cumulative effect of all filters. A Chain of
Responsibility handler is expected to decide whether it can fully handle
the request, and if it can, it stops the chain there; the request is
untransformed as it travels, and typically only one handler, or none, ever
acts on it. A validation pipeline that runs five checks and accumulates
all five results is Pipes and Filters; an error handler chain that tries
five handlers until one claims the exception is Chain of Responsibility.
Section 12's trade-off matrix makes this concrete by comparing the two
directly.

**Decorator (compositional cousin, different axis of composition).**
Decorator wraps one object with layers that each add behavior around a
single call, preserving the wrapped object's original interface at every
layer, and the composition happens by nesting one decorator inside
another's constructor. A pipeline connects independent, peer components
through an explicit pipe, and composition happens by wiring one filter's
output to the next filter's input, not by one filter wrapping another. In
practice, a chain of decorators around a single process() call and a
passive-filter pipeline that calls each filter in sequence can produce
identical runtime behavior, and some codebases genuinely blur the two; the
distinguishing question is whether the components think of themselves as
independent stages with a shared pipe contract (pipeline) or as layers
wrapping a common interface (decorator).

**Iterator (frequent implementation substrate, not the same pattern).**
Many in-process pipeline implementations, Python generators chained with
`yield from`, Rust's Iterator adapter methods, Java Stream, are built
directly on top of a language's Iterator pattern, using the iterator's
pull-based next() protocol as the pipe. Iterator itself is a pattern for
traversing a collection without exposing its internal representation; a
lazy-chain pipeline uses that same pull protocol as its plumbing but adds
the notion of independent, composable transformation stages on top of it.

**Event-Driven Architecture (composes at larger scale, different coupling
model).** A pipeline's filters are directly wired to their specific
neighbors, filter A's output goes to filter B and to nothing else. An
event-driven system's producers publish events to a broker or bus with no
knowledge of which consumers, if any, are listening, and multiple consumers
can react to the same event independently. A large distributed pipeline,
particularly the message-broker-connected variant in section 8, commonly
sits on top of event-driven infrastructure (a Kafka topic is both the pipe
between two Kafka Streams processors and an event stream any number of
other consumer groups can also subscribe to), which is why the two
patterns are frequently deployed together rather than as alternatives.

**Microkernel Architecture (compatible, different concern).** A microkernel
system separates a stable core from plug-in modules that extend it.
Nothing prevents a microkernel plug-in from internally being implemented as
a pipeline, or a pipeline's individual filters from being loaded as
microkernel plug-ins; the two patterns address different axes of the
system's design (extensibility of the whole system, versus decomposition
of one data flow) and compose without conflict.

No pattern in this repository is fundamentally incompatible with Pipeline
Architecture at the structural level; the closest thing to a genuine
incompatibility is applying the pattern to a workflow with the branching or
cyclic-dependency characteristics documented in section 4's
non-applicability list, where the pattern's own core assumption, a fixed
linear or DAG-shaped flow, does not hold.

## 14. Refactoring path in and out

### Introducing the pattern into code that does not have it

1. **Identify the seams.** Read the monolithic function and mark every
   point where one conceptually distinct transformation ends and the next
   begins. A seam candidate is a place where you could draw a horizontal
   line through the function and describe everything above the line and
   everything below the line in one sentence each, using different verbs.
2. **Extract each segment as a pure function with a fixed signature.** Give
   every extracted segment the exact same input type and the exact same
   output type as its neighbors, even if that means introducing a small
   shared data-transfer type to carry fields a later stage needs but an
   earlier stage does not produce naturally. This step alone, done with no
   change to control flow, is Martin Fowler's Extract Function refactoring
   applied repeatedly, and it is entirely mechanical and low risk.
3. **Verify behavior is unchanged with existing tests, or write
   characterization tests first if none exist**, calling the original
   monolithic function with representative inputs and recording its
   outputs before extraction, then confirming the newly extracted sequence
   of function calls reproduces the same outputs.
4. **Replace the sequential calls with an explicit pump or pipe wiring.**
   For a first pass, a passive-filter pump (a reduce over the list of
   extracted functions, or explicit sequential calls) is the lowest-risk
   choice, because it changes nothing about execution order or timing,
   only the shape of the code that expresses it.
5. **Only move to an active-filter, concurrent variant (goroutines,
   threads, an async pipeline) once a measured need exists.** Concurrency
   between stages introduces the backpressure and ordering concerns of
   section 11, and adding it before there is a proven throughput or
   latency reason is pure risk with no corresponding benefit.
6. **Add per-filter unit tests once the extraction is stable**, replacing
   or supplementing the end-to-end characterization tests from step 3 with
   focused tests that exercise each filter's contract directly.

### Removing the pattern when it stops earning its place

1. **Confirm the reuse or reordering flexibility the pattern was
   introduced for is genuinely no longer needed.** If every filter is only
   ever assembled in exactly one order, in exactly one pipeline, and has
   been that way for a long stable period, the pattern's main benefit has
   already gone unused.
2. **Inline the pipe wiring first, leaving the filter functions
   intact**, replacing the loop or pump call with direct sequential calls,
   so the transformation reads top to bottom as one linear sequence of
   function calls rather than as data flowing through an abstraction.
3. **Inline the filter functions into the call site one at a time**, using
   Inline Function, only where a filter's body is small enough that the
   inlined version is genuinely more readable than the extracted version,
   which is not automatic; a filter with meaningful internal complexity
   often remains more readable as a named function even after the pipe
   abstraction around it is gone.
4. **Keep any filter that is still independently unit-tested or reused
   elsewhere** as a standalone function even after removing the pipeline
   wiring, since the extraction from step 2 above and the pipe wiring
   are two separable decisions, and removing the wiring does not obligate
   removing the extraction.

## 15. Testing and verification

**Per-filter unit tests are what this pattern makes cheap, and they are
where most of the testing effort belongs.** Because a filter's contract is
exactly its input type and its output type, a filter test needs no
mocks, no fixtures beyond a representative input value, and no knowledge of
the rest of the pipeline; it asserts filter(known_input) equals
expected_output, and, for a filter with error paths, asserts the specific
failure behavior (raises a specific exception, routes to a specific
dead-letter shape) for known-bad input.

**What becomes harder is asserting the pipeline's end-to-end behavior**,
because no single filter's test proves the wiring between filters is
correct, that filter B actually receives what filter A actually produces,
and in the right order under concurrent execution. This needs a distinct
class of integration test that constructs the real pipe wiring, feeds a
small representative set of items through the whole pipeline, and asserts
on the sink's final contents, deliberately including at least one item
designed to fail partway through so the dead-letter or error path from
section 11 is exercised, not just the happy path.

**Backpressure and bounded-memory behavior need an explicit test of their
own**, not just an assumption that a bounded channel "should" work. A
useful test constructs a deliberately slow consumer filter (an artificial
sleep or a controllable gate) behind a bounded pipe, feeds items faster than
the consumer can drain them, and asserts that the producer blocks (or the
pipe's queue depth caps at the configured bound) rather than that memory
grows unbounded; this directly tests the failure mode named first in
section 11, and it is the test most codebases skip.

**Property-based testing suits pipelines unusually well** when a filter, or
a short sub-chain of filters, has an invariant that should hold for any
valid input, for example that the number of records leaving the redaction
filter equals the number of records entering it, or that sorting is
idempotent, running the sort filter twice produces the same output as
running it once. Generating random valid inputs and asserting the invariant
catches edge cases a handful of hand-picked example inputs will not.

**Test doubles for a pipe itself are useful** when a filter needs to be
tested in a context that exercises how it behaves as part of a chain
without standing up the real neighboring filters; a fake pipe that records
every item written to it, or that can be configured to simulate a full,
blocking buffer, lets a filter's interaction with backpressure be tested in
isolation from the rest of the system.

## 16. Observability signals

**Per-stage throughput and latency**, emitted as a counter of items
processed and a histogram of processing time, tagged by filter name, is the
single most important signal, because it is what turns "the pipeline is
slow" into "filter B is slow", which is the difference between an
actionable alert and a guess. A healthy pipeline shows roughly steady
per-stage throughput across all filters in a linear chain, because a
sustained throughput imbalance is exactly the precondition for the
unbounded-buffering and head-of-line-blocking failure modes in section 11.

**Pipe queue depth or buffer occupancy**, sampled per pipe, is the direct
signal for backpressure building up before it becomes an outage. A healthy
pipeline's queue depths sit near zero most of the time, with brief spikes
that drain quickly; a queue depth that is monotonically climbing over
minutes or hours, even slowly, is the leading indicator of the out-of-memory
failure mode, and it is visible in this metric long before it is visible in
overall process memory usage.

**Items dropped, dead-lettered, or retried, per filter and per failure
reason**, as a counter, is the signal that makes the silent-data-loss
failure mode in section 11 impossible to miss, because a drop with no
corresponding metric increment is exactly what "silent" means. A healthy
pipeline shows this counter at or near zero; any sustained non-zero rate
deserves investigation regardless of whether it is currently paging anyone.

**End-to-end item latency, from data source entry to data sink exit**,
distinct from per-stage latency, is what tells an operator whether the sum
of the stages, plus queueing time between them, is meeting the pipeline's
actual service-level objective; a pipeline can have every individual stage
within its expected latency budget while the end-to-end latency still
regresses because of accumulated queueing time, which per-stage metrics
alone will not surface.

**A correlation identifier attached to each item as it enters the pipeline
and carried unchanged through every filter**, logged at each stage
transition, is what makes it possible to trace one specific item's path
through a distributed pipeline after the fact, which is the distributed
pipeline's equivalent of a single stack trace in a monolith and is the
concrete answer to the operability force named in section 3.

## 17. Security and privacy implications

**A pipe is a trust boundary the moment it crosses a process, machine, or
organizational boundary**, and this pattern's whole design encourages
splitting a transformation into independently deployable stages, which
means the pattern actively increases the number of trust boundaries a
system has compared to a monolithic function that never serializes data at
all. Every filter that receives data over a network-connected pipe (the
message-broker variant in section 8 in particular) must treat that data as
untrusted input and validate it, exactly as it would validate a request
from an external client, rather than assuming an upstream filter already
sanitized it; a filter that skips this because "the upstream filter already
checked it" reintroduces the same trust assumption that made a monolith's
internal function calls implicitly safe, except now across a boundary an
attacker with access to any single stage's deployment can influence.

**Pipelines that process personally identifiable or otherwise sensitive
data need the redaction, masking, or encryption stage placed deliberately
early**, as close to the data source as the design allows, because every
filter downstream of the point where sensitive data enters the pipeline is
a place that data can be logged, buffered to disk, cached, or exposed in an
error message; a redaction filter placed late in the chain leaves every
filter before it as a place raw sensitive data was momentarily at rest or
in flight, and any of the observability signals in section 16, particularly
per-item logging enabled for debugging, can inadvertently capture that raw
data if the redaction has not already happened.

**Durable, message-broker-connected pipes persist data at rest** in the
broker's own storage, which means the broker inherits whatever data
retention, encryption-at-rest, and access-control obligations the data
itself carries; a pipeline design that treats the broker as pure plumbing
with no data-governance properties of its own is a common gap in real
deployments, because the broker was chosen for throughput and durability
reasons and its retention or encryption defaults were not reviewed against
the sensitivity of what actually flows through it.

**A dead-letter path, which section 11 recommends as the fix for silent
data loss, is itself a place sensitive data can accumulate and be
overlooked.** A dead-letter queue holding failed items complete with their
original payload, kept for debugging convenience, needs the same retention
and access-control review as the primary pipeline's data sink, not an
exemption from it because it was added as an operational afterthought.

## 18. References

- Wikipedia, "Pipeline (Unix)". History of the pipe mechanism, McIlroy's
  1964 memo, Thompson's 1973 implementation, and the Version 4 introduction
  of the pipe notation. https://en.wikipedia.org/wiki/Pipeline_(Unix) .
  Verified 2026-08-02.
- M. D. McIlroy, E. N. Pinson, B. A. Tague, "Unix Time-Sharing System.
  Foreword", Bell System Technical Journal, volume 57, issue 6, 8 July
  1978, pages 1902 to 1903. Source of the "do one thing well" design
  philosophy quote, as reproduced on Wikipedia, "Unix philosophy".
  https://en.wikipedia.org/wiki/Unix_philosophy . Verified 2026-08-02.
- man7.org, pipe(7) Linux manual page. Pipe capacity (65,536 bytes since
  kernel 2.6.11), PIPE_BUF, and blocking read and write semantics.
  https://man7.org/linux/man-pages/man7/pipe.7.html . Verified 2026-08-02.
- Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, Michael
  Stal, Pattern-Oriented Software Architecture, Volume 1. A System of
  Patterns, Wiley, 1996, chapter 2, "Pipes and Filters". Confirmed via
  https://john.cs.olemiss.edu/~hcc/docs/Patterns/Pipes/Pipes.html , a
  university lecture-notes summary of the chapter's participant vocabulary
  (filter, pipe, data source, data sink, pump), structure, context, and
  known uses. Verified 2026-08-02.
- Apache Beam, "Beam Programming Guide". Pipeline, PCollection,
  PTransform, the DAG structure of a pipeline, and unified batch and
  streaming execution.
  https://beam.apache.org/documentation/programming-guide/ . Verified
  2026-08-02.
- Confluent, "Kafka Streams Architecture". Source, stream, and sink
  processor topology as a directed graph, and parallel execution across
  stream threads and tasks.
  https://docs.confluent.io/platform/current/streams/architecture.html .
  Verified 2026-08-02.
- Jenkins, "Pipeline" documentation. Pipeline-as-code, the Jenkinsfile,
  declarative versus scripted syntax, and staged CI/CD workflows.
  https://www.jenkins.io/doc/book/pipeline/ . Verified 2026-08-02.
- Reactive Streams, specification homepage. Purpose (asynchronous stream
  processing with non-blocking backpressure), the JVM API's alignment with
  java.util.concurrent.Flow in JDK 9, and working groups for JavaScript
  and network protocol bindings. https://www.reactive-streams.org/ .
  Verified 2026-08-02.
- LLVM Project, "The New Pass Manager" documentation. Module, CGSCC,
  function, and loop pass hierarchy, pass adaptors, and analysis-result
  caching across a chained pipeline of compiler passes.
  https://llvm.org/docs/NewPassManager.html . Verified 2026-08-02.

## Code examples

Three implementation variants from section 8, one per language, each
compiled or run directly. Comments are kept to one or two lines per the
repository comment policy.

The first is the active, concurrent, channel-connected variant in Go,
where each filter owns a goroutine and a bounded output channel provides
backpressure.

```go
package main

import "fmt"

// upperFilter is an active filter: it owns a goroutine and reads from in,
// writes to a new bounded out channel, then closes out when in is drained.
func upperFilter(in <-chan string) <-chan string {
	out := make(chan string, 2)
	go func() {
		defer close(out)
		for s := range in {
			out <- fmt.Sprintf("[%s]", s)
		}
	}()
	return out
}

func lenFilter(in <-chan string) <-chan int {
	out := make(chan int, 2)
	go func() {
		defer close(out)
		for s := range in {
			out <- len(s)
		}
	}()
	return out
}

func main() {
	source := make(chan string, 2)
	go func() {
		defer close(source)
		for _, s := range []string{"go", "rust", "python"} {
			source <- s
		}
	}()

	pipeline := lenFilter(upperFilter(source))

	for n := range pipeline {
		fmt.Println(n)
	}
}
```

The second is the passive, generator-based lazy chain in Python, where
nothing runs until the caller iterates, and each filter pulls from its
upstream one item at a time.

```python
from typing import Iterable, Iterator


def bracket_filter(items: Iterable[str]) -> Iterator[str]:
    # A passive, generator-based filter driven lazily by whoever pulls it.
    for item in items:
        yield f"[{item}]"


def length_filter(items: Iterable[str]) -> Iterator[int]:
    for item in items:
        yield len(item)


def redact_filter(items: Iterable[int], threshold: int) -> Iterator[str]:
    for length in items:
        yield "REDACTED" if length > threshold else str(length)


def build_pipeline(source: Iterable[str]) -> Iterator[str]:
    return redact_filter(length_filter(bracket_filter(source)), threshold=6)


if __name__ == "__main__":
    for result in build_pipeline(["go", "rust", "python"]):
        print(result)
```

The third is the same passive, iterator-adapter variant in Rust, where the
compiler fuses the whole chain into a single loop at compile time with no
intermediate allocation between stages.

```rust
// Each adapter method is a passive filter chained over a lazy iterator,
// the pipe here, with no buffer, no thread, pulled one item at a time.
fn main() {
    let source = vec!["go", "rust", "python"];

    let results: Vec<String> = source
        .into_iter()
        .map(|s| format!("[{}]", s))
        .map(|s| s.len())
        .map(|n| if n > 6 { "REDACTED".to_string() } else { n.to_string() })
        .collect();

    for r in results {
        println!("{}", r);
    }
}
```

All three were run directly. `go run` on the Go source, `python3` on the
Python source, and `rustc` followed by executing the resulting binary on
the Rust source, each producing the expected chained transformation of the
three input strings.
