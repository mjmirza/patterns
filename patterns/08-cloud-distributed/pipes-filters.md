---
name: Pipes and Filters
slug: pipes-filters
family: 08-cloud-distributed
category: Cloud and Distributed Systems
aliases: [Pipeline Architecture, Filter Chain, Data Flow Pattern]
first_described: "McIlroy 1964 concept, Bell Labs Unix 1973 implementation, catalogued as an architectural style by Garlan and Shaw 1993, catalogued as an integration pattern by Hohpe and Woolf 2003"
maturity: canonical
related: [competing-consumers, publisher-subscriber, claim-check, queue-based-load-leveling, saga, choreography, strategy, decorator, chain-of-responsibility, template-method]
incompatible_with: []
verified: 2026-08-02
---

# Pipes and Filters

## 1. Name, aliases, and lineage

The canonical name is Pipes and Filters. Two lineages converge on it, and both
matter because they explain why the pattern shows up under different names in
different communities.

The first lineage is a concrete mechanism. Douglas McIlroy at Bell Labs
proposed connecting programs so that the output of one becomes the input of
the next as early as 1964, in an internal memo. Ken Thompson turned the idea
into a real kernel facility in 1973 when he added the `pipe()` system call to
Version 3 Unix, along with pipe support in the shell and the core utilities.
The vertical bar notation, `|`, was added by Thompson in Version 4 Unix and
simplified the syntax for describing a pipe (Wikipedia contributors,
"Pipeline (Unix)", https://en.wikipedia.org/wiki/Pipeline_(Unix), verified
2026-08-02, citing the Version 3 and Version 4 Unix manuals). This is the
origin of the alias Filter Chain, because a Unix program that reads a stream
and writes a transformed stream is literally called a filter in Unix
terminology and documentation.

The second lineage is architectural taxonomy. David Garlan and Mary Shaw
formalised Pipes and Filters as one of a small set of named software
architectural styles in their 1993 CMU technical report "An Introduction to
Software Architecture", describing it as a style in which components
(filters) transform data and connectors (pipes) carry the data between them,
with the constraint that filters are independent and unaware of the identity
of their neighbours. Gregor Hohpe and Bobby Woolf then catalogued Pipes and
Filters as an integration pattern in *Enterprise Integration Patterns.
Designing, Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
in the chapter on Messaging Systems, applying the same idea to message-based
systems where a pipe is a channel rather than an operating-system file
descriptor. This is the origin of the alias Pipeline Architecture, used when
the emphasis is on the whole composed structure rather than any one stage.

A third, looser use of the phrase appears in data engineering as Data Flow
Pattern, describing any system where records move through a fixed sequence of
transform steps, whether or not the steps are literally connected by anything
called a pipe. That usage is not wrong, but it stretches the term far enough
that a reader should confirm, for any given system, whether the steps are
truly independent and reorderable, which is the property that separates a
genuine Pipes and Filters system from an ordinary sequential function call
chain, see dimension 4.

## 2. Problem and context

A system needs to apply a series of transformations or checks to a stream of
data, and the natural first implementation is one large function or one large
class that performs every step in order. That single unit compiles cleanly
and passes its first test, and then three things go wrong as the system grows.

First, a new requirement arrives that needs one more step inserted between two
existing steps, or needs the existing steps reordered for a different data
source. In a monolithic function this means editing the one function again,
and every edit risks the steps that already worked. Second, one step turns
out to be far more expensive than the others, for example an image resize or
a fraud check that calls an external service, and the whole unit now runs at
the speed of its slowest part with no way to give that part more resources
without giving every part more resources. Third, two products in the same
company need almost the same processing with one step different, and the
honest options are duplicating the whole function or growing it a conditional
branch for every product, both of which make the function harder to read with
every addition.

The context in which Pipes and Filters is the right answer has a specific
shape. The processing genuinely decomposes into a sequence of steps, each of
which reads some input and produces some output in a shared or compatible
format, each step does not need to know which step produced its input or
which step will consume its output, and the steps have different enough
resource profiles, failure modes, or reuse needs that treating them as
separately deployable, separately scalable, and separately testable units pays
for itself. This is exactly the context the Azure Architecture Center names.
"You have a pipeline of sequential tasks that you need to process... this
approach is likely to reduce the opportunities for refactoring the code,
optimizing it, or reusing it if parts of the same processing are required
elsewhere in the application" (Microsoft, "Pipes and Filters pattern", Azure
Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/pipes-and-filters,
verified 2026-08-02).

Outside that context, most often when the steps genuinely need to see each
other's full context or must commit as one atomic unit, the pattern is a
liability rather than a solution, see dimension 4.

## 3. Forces

- **Latency.** Sacrificed at the small scale, potentially favoured at large
  scale. A single pipe adds serialization, a network hop or a queue write and
  read, which a monolithic function call never pays. Once filters run in
  parallel on independent partitions of the stream, aggregate throughput can
  exceed the monolith by more than the per-hop cost, but the tail latency of
  any single record grows with the number of hops.
- **Coupling.** Strongly favoured. A filter depends only on its input and
  output schema, never on the identity or implementation of its neighbours.
  This is the central payoff of the pattern and the reason it survives across
  every implementation variant in dimension 8.
- **Reusability.** Favoured. The same filter, and the same pipe infrastructure,
  can be composed into more than one pipeline, which is the specific problem
  the Azure Architecture Center opens with, describing a monolithic
  implementation's "inability to reuse code across multiple pipelines"
  (Microsoft, Azure Architecture Center, cited above).
- **Independent scalability.** Favoured, and one of the strongest reasons this
  pattern belongs in a cloud and distributed catalog rather than only a
  language-level catalog. A compute-heavy filter can run on many instances
  while a cheap filter runs on one, addressing exactly the bottleneck the
  monolith could not isolate.
- **Consistency and transactionality.** Sacrificed. A pipeline of independently
  scheduled filters cannot easily offer one atomic commit across all its
  stages. Partial failure, out-of-order delivery, and duplicate delivery are
  now first-class concerns rather than absent by construction, see dimension
  11 and the idempotency discussion in the Azure Architecture Center's Issues
  and considerations section.
- **Operability and debuggability.** Sacrificed by default, recoverable with
  investment. A record's path through five independently deployed filters
  is not visible in a single stack trace the way a function call chain is,
  and must be reconstructed from distributed telemetry, see dimension 16.
- **Cognitive load per unit.** Favoured. Each filter is small and can be
  understood, tested, and reasoned about on its own, at the cost of needing to
  reason about the pipeline as a composed whole separately, see dimension 11's
  monolithic-pipeline failure mode.
- **Ordering guarantees.** Sacrificed unless deliberately engineered. Filters
  running on multiple parallel instances, or reading from partitioned pipes,
  do not preserve the original arrival order of records unless the pipe
  infrastructure and the filter design specifically preserve it, which itself
  costs throughput.

A pattern that gave up nothing would not be a pattern. Here the price is paid
in per-hop latency, weakened consistency guarantees, and end-to-end
observability effort, in exchange for independent scaling, reuse, and the
ability to reorder or replace one stage without retesting the whole system.

## 4. Applicability and non-applicability

Reach for Pipes and Filters when the following hold.

- Processing decomposes naturally into a sequence of independent
  transformations or validations over a stream of records, files, messages, or
  events.
- Individual steps have meaningfully different resource profiles, so scaling
  them together wastes resources on the cheap steps or starves the expensive
  ones.
- The set of steps, or their order, is expected to change over the system's
  life, and the cost of retesting a monolith on every such change is real.
- More than one pipeline in the system can share some of the same steps, so a
  reusable filter earns back its extraction cost more than once.
- The system can tolerate the pattern's native consistency weaknesses,
  meaning either true idempotent processing is achievable at every stage, or
  eventual consistency is acceptable for this workload.
- The processing is genuinely a stream, so that a later stage can begin work
  on the output of an earlier stage before that earlier stage has finished the
  whole input, which is the pipelining payoff the Azure Architecture Center
  describes explicitly. "If the input and output of a filter are structured as
  a stream, you can perform the processing for each filter in parallel"
  (Microsoft, Azure Architecture Center, cited above).

Do NOT reach for Pipes and Filters in the following cases, and the reason
matters more than the rule.

- **The steps must commit as a single atomic transaction.** A pipeline of
  independently deployed filters cannot give this for free. If two steps must
  both succeed or both roll back together, either keep them as one step, use
  a two-phase commit only where the infrastructure genuinely supports it, or
  reach for Saga, which is built for exactly this coordination problem and
  admits up front that it uses compensation instead of atomicity. The Azure
  Architecture Center notes the pattern can be paired with Compensating
  Transaction as an alternative to distributed transactions, which is a tell
  that the pattern itself does not supply transactionality (Microsoft, Azure
  Architecture Center, cited above).
- **There is exactly one processing step and no plausible second.** Splitting
  a single transformation into a pipe and a filter to look architecturally
  sophisticated is speculative generality with an added network hop for no
  reuse benefit.
- **The steps genuinely need each other's full context, not just their
  neighbour's output.** A step that needs to see the original raw input plus
  the output of three earlier steps at once does not fit the strict
  neighbour-to-neighbour data flow this pattern assumes, and forcing it in
  produces filters that carry an ever-growing envelope of accumulated state,
  which erodes the independence the pattern exists to provide.
- **Ultra-low, single-digit-millisecond, synchronous request latency is a hard
  requirement**, and the filters cannot be collapsed into one process. Every
  hop, whether an in-process call, an HTTP call, or a queue round trip, adds
  measurable time, and a request-response API endpoint is explicitly named by
  the Azure Architecture Center as a case where the pattern "might not be
  useful". "The application follows a request-response pattern" (Microsoft,
  Azure Architecture Center, cited above).
- **Strict, global ordering across the whole stream is required, and the
  filters must run in parallel for throughput.** The two requirements are in
  direct tension. Either accept single-threaded processing per partition key
  to preserve order, or accept that ordering is only guaranteed within a
  partition, not globally.
- **The amount of shared context each filter needs is large enough that
  loading, passing, and persisting it costs more than the processing itself.**
  The Azure Architecture Center calls this out directly under Context and
  state, warning that "every filter has to load, operate, and persist that
  state, which adds overhead over solutions that load the external state a
  single time" (Microsoft, Azure Architecture Center, cited above).

## 5. Structure

Three kinds of participant, named by the role they play.

- **Filter.** A component that consumes messages from one or more inbound
  pipes, performs one well-defined transformation, enrichment, validation, or
  filtering operation, and publishes the result to one or more outbound
  pipes. A filter is stateless with respect to the pipeline, meaning it holds
  no memory of prior records beyond what its own implementation needs for a
  single record or a bounded window, and it is unaware of which component
  produced its input or which component will consume its output. A filter
  that only inspects and forwards without transforming, deciding whether the
  record continues downstream, plays a specialised role sometimes called a
  Filter in the narrower Enterprise Integration Patterns sense of a
  pass-or-drop gate.
- **Pipe.** A connector that transports messages from one filter's output to
  the next filter's input, and does nothing else. A pipe never inspects,
  transforms, or routes based on message content, that responsibility belongs
  entirely to filters, which is the structural discipline that keeps the
  pattern's coupling low. A pipe may be an in-process queue, a message broker
  channel, a cloud storage queue, a file, or an operating-system file
  descriptor, see dimension 8 for the concrete choices.
- **Source and Sink.** The endpoints of a pipeline. A source produces the
  initial stream with no upstream pipe, a sink consumes the final stream with
  no downstream pipe. Some catalogs treat these as degenerate filters with
  only an output or only an input, others treat them as a distinct pair of
  participants, and both conventions are in active use, so this entry treats
  them as filters with one side of their pipe connection absent.

The critical relationship is what each filter is allowed to know. A filter
depends on the schema of the message it receives and the schema of the
message it produces. It has no dependency on any other filter's identity,
implementation, or existence. This is the same seam Chain of Responsibility
uses for handler independence and Strategy uses for interchangeable
algorithms, applied here to an entire multi-stage flow rather than to one
substitution point, see dimension 13.

## 6. ASCII structure diagram

```
   +--------+      +----------+      +----------+      +----------+
   | Source |----->| Filter A |----->| Filter B |----->|   Sink   |
   +--------+ pipe +----------+ pipe +----------+ pipe +----------+

   Filter A knows only:                Filter B knows only:
     - the schema it reads from its      - the schema it reads from its
       inbound pipe                        inbound pipe
     - the schema it writes to its       - the schema it writes to its
       outbound pipe                       outbound pipe
     - nothing about Source, B, or Sink  - nothing about Source, A, or Sink

   Cloud variant, each filter independently deployed and scaled:

   +--------+   +-----------------+   +-----------------+   +--------+
   | Source |-->| Queue (pipe 1)  |-->| Filter A         |
   +--------+   +-----------------+   | instances: x3    |
                                       +-----------------+
                                                |
                                                v
                                       +-----------------+
                                       | Queue (pipe 2)  |
                                       +-----------------+
                                                |
                                                v
                                       +-----------------+   +--------+
                                       | Filter B         |-->|  Sink  |
                                       | instances: x1    |   +--------+
                                       +-----------------+

   Each filter scales to the instance count its own workload needs.
   The queues are the only shared infrastructure between stages.
```

## 7. Dynamics

Two distinct runtime shapes are both called Pipes and Filters, and confusing
them causes real design mistakes, so both are shown.

**Blocking, streamed shape.** This is the Unix shell shape. Every filter runs
concurrently as its own process, and the operating system buffers a bounded
amount of data between them, so a downstream filter can begin consuming
output before the upstream filter has finished producing it, and an upstream
filter blocks (backpressure) once the buffer fills and the downstream filter
is not draining it fast enough. Doug McIlroy's design gave every stage this
concurrent, buffered behaviour by construction, which is why a shell pipeline
of `grep`, `sort`, and `uniq` on a large file starts printing results before
`sort` alone would have finished, because `sort` still has to buffer its own
input, but `grep` and `uniq` are streaming the whole time.

```
   Producer          Filter A (grep)      Filter B (sort)     Consumer (uniq)
     |                     |                     |                    |
     |-- write chunk 1 --->|                     |                    |
     |                     |-- write matches --->|  (sort buffers,    |
     |-- write chunk 2 --->|                     |   cannot emit      |
     |                     |-- write matches --->|   until EOF)       |
     |-- (buffer full,     |                     |                    |
     |    blocks) ---------|<-- kernel backpres. |                    |
     |                     |-- resumes when B    |                    |
     |                     |   drains its pipe   |                    |
     |-- EOF ------------->|-- EOF ------------->|-- (now sorts,      |
     |                     |                     |    emits) -------->|
```

**Asynchronous, message-queue shape.** This is the cloud shape shown in the
second structure diagram, matching the Azure Architecture Center's example
implementation. "You can use a sequence of message queues to provide the
infrastructure required to implement a pipeline. An initial message queue
receives unprocessed messages... A component implemented as a filter task
listens for a message on this queue, performs its work, and then posts a new
or transformed message to the next queue in the sequence" (Microsoft, Azure
Architecture Center, cited above). Here every filter instance is decoupled in
time from its neighbours. A filter is not blocked waiting for a downstream
consumer, it simply writes to a queue and returns, and it may be scaled to
many instances that compete for the same inbound queue, see the Competing
Consumers pattern in dimension 13.

```
   Queue 1        Filter A instance 1      Filter A instance 2      Queue 2
     |                    |                        |                   |
     |-- msg 1 --------->|                          |                  |
     |-- msg 2 -----------------------------------> |                  |
     |                    |-- process msg 1          |                 |
     |                    |-- write result --------------------------->|
     |                    |                          |-- process msg 2 |
     |                    |                          |-- write result ->|
     |-- msg 3 --------->|                          |                  |
     |                    |-- process msg 3          |                 |
     |                    |-- write result --------------------------->|
```

The dynamics differ in whether a filter is blocked awaiting downstream
capacity (the Unix shape, tight coupling in time, low latency, no persistent
intermediate storage) or a filter is fully decoupled and the queue absorbs
bursts (the cloud shape, loose coupling in time, higher per-hop latency,
durable intermediate state that survives a filter crash). Choosing between
them is the single most consequential decision in an implementation, see
dimension 8.

## 8. Implementation variants

**OS process pipes.** The Unix shape. `producer | filterA | filterB` where
each `|` is a kernel-managed buffer connecting two processes' standard
streams. Lowest overhead of any variant, strong backpressure for free from
the kernel, but confined to one machine and one process lifetime, no
durability if a stage crashes mid-stream, and no independent horizontal
scaling of one stage beyond running more parallel pipelines of the whole
chain.

**In-process functional composition.** Each filter is a pure function or a
generator/iterator, and the pipe is simply passing the return value of one
function as the argument to the next, or chaining generators so that
consuming from the tail pulls records through every stage lazily. This is the
shape most language standard libraries offer directly, for example Python
generator chains or a reduce over a list of callables. Zero network cost, but
no independent deployment, no independent scaling, and a crash anywhere takes
down the whole process.

**Message broker pipeline.** Each pipe is a topic or queue on a broker such
as RabbitMQ, Apache Kafka, Azure Service Bus, or Amazon SQS, and each filter
is a separately deployed consumer-then-producer service. This is the cloud
shape from dimension 7. It buys independent deployment, independent scaling,
durability across a filter crash (the message survives on the broker until
acknowledged), and the ability to run filters in different languages, at the
cost of per-hop latency, the need to design for at-least-once delivery and
therefore idempotency, and operational ownership of the broker itself.

**Serverless function chain with storage-backed pipes.** Cloud functions,
Azure Functions or AWS Lambda, each triggered by an item landing in a queue
or a storage bucket, writing their result to the next queue or bucket. The
Azure Architecture Center's own worked example uses exactly this shape for an
image processing pipeline, chaining Azure Functions through Azure Queue
Storage with a claim check pointing at the actual image in Azure Blob
Storage rather than embedding the image bytes in the queue message
(Microsoft, Azure Architecture Center, cited above, see the claim check
cross-reference in dimension 13). This variant minimises operational
ownership, since there is no broker cluster to run, at the cost of
per-invocation cold-start latency and a pricing model that charges per
invocation rather than per running instance.

**Integration framework pipeline.** A dedicated integration engine, most
notably Apache Camel, provides a Pipeline construct as a first-class routing
primitive, chaining a list of Camel endpoints or processors so that each
one's output becomes the next one's input within a single route definition.
Camel documents this directly as an implementation of the Enterprise
Integration Patterns Pipes and Filters pattern. "Camel supports the Pipes and
Filters from the EIP patterns in various ways" (The Apache Software
Foundation, "Pipeline EIP", Apache Camel documentation,
https://camel.apache.org/components/latest/eips/pipeline-eip.html, verified
2026-08-02). This variant is chosen when an organisation already standardises
on an integration framework and wants pipeline routing declared in
configuration rather than hand-wired broker topics.

**Streaming dataflow engine.** Frameworks such as Apache Beam or Apache Flink
express a pipeline as a directed graph of transform stages compiled and
scheduled by the engine, rather than wired by hand through individual queues.
This variant trades manual control over each pipe for automatic parallelism,
checkpointing, and exactly-once processing guarantees the engine provides,
and is the right choice when the pipeline is large, long-lived, and the team
wants the engine to own scheduling rather than owning it themselves.

**Media and signal processing graph.** GStreamer models an entire media
pipeline this way at the library level, connecting elements (filters) through
pads, where "you will usually create a chain of elements linked together and
let data flow through this chain of elements" (The GStreamer team,
"Basic concepts", GStreamer Application Development Manual,
https://gstreamer.freedesktop.org/documentation/application-development/introduction/basics.html,
verified 2026-08-02). This variant matters here because it demonstrates the
pattern operating in-process, at very high throughput, with strict typed
negotiation between adjacent elements over what data format is allowed to
flow through a given pad, a stronger contract than most cloud message
pipelines enforce.

## 9. Known production uses

**Unix and POSIX-compliant shells.** Every Unix and Linux shell implements
the pipe operator as a direct realisation of this pattern, connecting the
standard output of one process to the standard input of the next via the
`pipe()` system call that Ken Thompson added to Version 3 Unix in 1973, with
the `|` shorthand introduced in Version 4 Unix (Wikipedia contributors,
"Pipeline (Unix)", https://en.wikipedia.org/wiki/Pipeline_(Unix), verified
2026-08-02). This is the pattern's oldest and most widely executed
implementation, run by essentially every command line in existence.

**GStreamer.** The open-source multimedia framework used by GNOME, many Linux
distributions' media playback stacks, and numerous embedded and broadcast
systems, structures every playback, capture, or transcoding task as a
pipeline of elements connected by pads, exactly matching the Filter and Pipe
roles from dimension 5 (The GStreamer team, GStreamer Application Development
Manual, https://gstreamer.freedesktop.org/documentation/application-development/introduction/basics.html,
verified 2026-08-02).

**Apache Camel.** The integration framework's Pipeline EIP construct chains
endpoints and processors so each stage's output feeds the next stage's input,
documented by the project as its implementation of the Enterprise Integration
Patterns Pipes and Filters pattern (The Apache Software Foundation, "Pipeline
EIP", https://camel.apache.org/components/latest/eips/pipeline-eip.html,
verified 2026-08-02).

**Azure Functions with Azure Queue Storage.** Microsoft's own reference
architecture for the pattern in the cloud chains Azure Functions through
Azure Queue Storage pipes, using a claim check to Azure Blob Storage for the
image bytes rather than embedding them in each queue message, for an image
processing pipeline performing content moderation, resizing, watermarking,
reorientation, metadata removal, and CDN publication as independently
deployed, independently scalable filters (Microsoft, "Pipes and Filters
pattern", Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/pipes-and-filters,
verified 2026-08-02).

## 10. Consequences

Positive.

- Individual filters can be developed, tested, deployed, and scaled
  independently of one another, which is the pattern's central payoff in a
  cloud environment where compute for a heavy filter can be provisioned
  separately from compute for a light one.
- Filters are reusable across more than one pipeline once extracted, so a
  validation or enrichment step written for one product line can be composed
  into another without duplication.
- Pipelines are reconfigurable by rewiring which filters connect to which
  pipes, without redeploying or retesting filters that were not touched,
  making the system flexible in the face of changing requirements.
- Parallel and pipelined execution across filters, when the pipe supports
  streaming, lets downstream stages begin work before upstream stages finish,
  reducing end-to-end latency compared with a fully sequential monolith on
  large inputs.
- Failure and retry can be scoped to a single filter rather than the whole
  process, when the pipe infrastructure durably persists in-flight messages,
  meaning a crash in one filter does not lose work already completed by
  earlier filters.

Negative.

- Per-hop overhead, whether serialization cost, network latency, or a queue
  round trip, is paid on every stage boundary, and grows with pipeline
  length.
- Global correctness properties, atomic multi-stage commits and strict
  end-to-end ordering, are not native to the pattern and must be explicitly
  designed in when the workload needs them, at real cost.
- Debugging and tracing a single record across many independently
  deployed filters requires investment in distributed tracing that a
  monolithic function never needed.
- The pattern is, as the Azure Architecture Center puts it, still "usually
  implemented as a monolithic pipeline" in the sense that "for any change,
  the entire filter chain should be tested end to end... if a filter or pipe
  fails, the whole pipeline is likely to fail" (Microsoft, Azure Architecture
  Center, cited above), meaning the independence of individual filters does
  not automatically confer independence of the pipeline's overall
  correctness or availability.
- At-least-once delivery, which most durable pipe implementations provide, is
  the norm rather than the exception, so every filter that has side effects
  must be written to be idempotent, which is real design effort that a
  synchronous call chain does not require.

## 11. Failure modes and misuse

**The pipeline that quietly duplicates work.** Symptom. A downstream analytics
count is roughly double the true number of processed items, or a customer
receives the same notification twice. Cause. A filter crashes after
committing its output to the next pipe but before acknowledging its own
inbound message, so the pipe redelivers the message and the same output is
produced twice. Fix. Design every filter to be idempotent, most often by
deriving a deterministic message identifier and having the sink or the next
filter deduplicate on it, matching the Azure Architecture Center's own
warning under Repeated messages and its note that some broker infrastructure,
citing Azure Service Bus queues, offers built-in duplicate detection
(Microsoft, Azure Architecture Center, cited above).

**Silent backpressure collapse.** Symptom. Memory on one filter's host grows
without bound, or the pipe's storage cost climbs steadily, with no obvious
error anywhere. Cause. A downstream filter is slower than its upstream
producers and the pipe has no bounded capacity or no backpressure signal, so
messages accumulate faster than they drain. Fix. Bound queue depth, apply
backpressure (block or shed load) once a threshold is reached, and alert on
queue depth growth rather than only on error rate, since this failure mode
produces no errors until the bound is finally hit.

**The reintroduced monolith.** Symptom. A filter's code imports types or
calls functions belonging to a supposedly independent neighbouring filter,
or two filters are always deployed and released together despite living in
separate services. Cause. The team extracted the pipeline's shape without
extracting its independence, most often because a shared context object grew
until it effectively coupled every filter to every other filter's data
needs. Fix. Audit what each filter actually reads and writes against its
declared pipe schema, and split any accumulated shared-state object back into
the specific fields each filter genuinely needs.

**Out-of-order processing corrupting a stateful downstream step.** Symptom.
A filter that maintains a running total or a latest-value cache produces a
result that depends on which order two records happened to arrive in, and the
same input set produces different output on different runs. Cause. Parallel
filter instances or a partitioned pipe do not preserve the original ordering
of the stream, and a downstream step silently assumed they would. Fix.
Partition the pipe by a key that requires ordering (for example customer
identifier) so records needing relative order always land on the same
consumer instance, or make the downstream step order-independent by design
(commutative and associative aggregation).

**The pipeline nobody can trace.** Symptom. A support engineer, given a
complaint that one specific record produced the wrong output, cannot
determine which of six independently deployed filters mangled it, and spends
hours reproducing the input against each filter in isolation. Cause. No
correlation identifier was propagated through the pipeline, so log lines from
different filters cannot be joined for a single record. Fix.
Generate a correlation identifier at the source and require every filter to
propagate it unchanged into both its logs and its output message, then build
tracing around that identifier, see dimension 16.

**Schema drift breaking a filter that "just forwards" unknown fields.**
Symptom. A filter added six months after the pipeline shipped starts
receiving records missing a field it depends on, and either crashes or
silently produces a wrong default. Cause. An upstream filter changed its
output schema without a contract or version negotiated with downstream
filters, and no schema registry or compatibility check caught it before
deploy. Fix. Version pipe schemas explicitly, and use a schema registry or
compatibility test in CI so an incompatible producer change is caught before
it reaches a consumer that has not been updated.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Pipes and Filters | Monolithic function (no pattern) | Orchestrated saga (a single orchestrator calls each step) | Choreography (steps react to events with no central pipeline) | Competing Consumers alone |
|---|---|---|---|---|---|
| Coupling between steps | Low, only shared schema | High, one compiled unit | Medium, steps decoupled from each other but coupled to the orchestrator | Low between steps, but implicit coupling through shared event names | Low, but assumes one homogenous queue rather than a staged sequence |
| Independent scaling per step | Strong, that is the core payoff | None | Possible, since steps are separate services, but the orchestrator itself becomes a scaling bottleneck | Strong per consumer, weaker to reason about overall throughput | Strong, but for one stage only, not a multi-stage flow |
| Reordering or inserting a new step | Rewire pipes, filters unaffected | Edit the function, retest everything | Edit the orchestrator's step list | Add a new subscriber, existing publishers unaware, but overall flow visibility drops further | Not applicable, no ordered stages exist |
| Failure visibility and control | Distributed, needs the orchestrator's or observability layer's help | Centralised, one stack trace | Strong, the orchestrator sees every step's outcome and can compensate | Weak, no single place sees the whole flow, hardest of the group to debug | Per-stage only |
| Atomic multi-step commit | Not native, must be engineered | Free, one transaction | Not atomic either, but explicitly designed for compensating rollback | Not native, and hardest of the group to compensate since no one component owns the sequence | Not applicable |
| Latency for a single record | One hop per stage | Lowest, in-process only | Similar to Pipes and Filters plus orchestrator round trips | Similar to Pipes and Filters, potentially lower since no orchestrator hop | One hop |
| Best fit | A fixed or evolving sequence of independent transform steps | A stable, small, single-owner sequence with a hard latency budget | A business process needing centralised visibility and compensation, not primarily a data transform | Loosely coupled domain-driven step reactions where no team wants to own a central flow | Scaling one stage of any of the above patterns |

Reading of the table. Pipes and Filters and Saga both decompose a large
operation into steps, but Pipes and Filters is a data transformation pipeline
with pipes carrying data forward, while Saga is a business transaction with
an orchestrator or a chain of events carrying commands and compensations. A
system that needs both, a multi-stage data transform and a compensable
business transaction, commonly combines them, with each Saga step
implemented internally as its own small Pipes and Filters chain, exactly as
the Azure Architecture Center suggests when it pairs the two patterns
(Microsoft, Azure Architecture Center, cited above).

## 13. Related and incompatible patterns

- **Competing Consumers.** Composes directly underneath. Any one filter stage
  in a queue-based pipeline can itself be scaled using Competing Consumers,
  running several instances that pull from the same inbound pipe and race for
  work, which is exactly how the cloud shape in dimension 7 achieves
  independent scaling per stage.
- **Claim Check.** Composes above it for large payloads. Rather than passing a
  large object through every pipe, a filter writes the object to storage and
  passes a reference, which the Azure Architecture Center's own worked
  example does for images, keeping the pipes carrying small claim-check
  messages while Blob Storage carries the bytes (Microsoft, Azure
  Architecture Center, cited above).
- **Publisher-Subscriber.** A generalisation in one direction. Where a pipe
  connects exactly one producer stage to exactly one consumer stage,
  Publisher-Subscriber allows one message to fan out to many independent
  subscribers with no shared downstream schema requirement between them.
  Some pipeline implementations use a publish-subscribe topic as the pipe
  itself when a stage's output must feed more than one downstream filter.
- **Saga and Choreography.** Sibling decomposition patterns solving a
  different problem. Saga and Choreography coordinate a multi-step business
  transaction that must eventually reach a consistent outcome, including
  compensating a partial failure, while Pipes and Filters transforms a data
  stream with no built-in notion of compensation. See dimension 12 for how
  the two combine.
- **Chain of Responsibility.** The closest object-oriented sibling and the one
  most often confused with this pattern. Both connect a sequence of
  independent handlers, but Chain of Responsibility is built for exactly one
  handler in the chain to consume and stop the request (a request-response
  shape), whereas Pipes and Filters is built for every filter to transform
  the data and pass it along (a data-transform shape). A Chain of
  Responsibility implemented so that every handler always calls the next one
  after doing its own work has, in effect, become a Pipes and Filters chain.
- **Strategy and Template Method.** A single filter's internal transformation
  logic is frequently implemented using Strategy, to make that one filter's
  algorithm swappable, or Template Method, when a family of filters shares a
  common skeleton (read, transform, write) and varies only the transform
  step, see the respective entries for how those two compose inside one
  filter.
- **Decorator.** A structural cousin at a smaller scale. Decorator wraps one
  object to add behaviour before and after delegating to the wrapped object,
  which is a two-participant version of the same idea Pipes and Filters
  applies to an arbitrary-length chain of independent stages.
- **Incompatibility.** No named pattern is flatly incompatible with Pipes and
  Filters, but it actively conflicts with the assumption behind a plain
  synchronous request-response API contract, since introducing durable,
  asynchronous pipes into a path a caller is synchronously waiting on
  reintroduces the very request-response mismatch the Asynchronous
  Request-Reply pattern exists to bridge, so the two are frequently paired
  rather than substituted for each other.

## 14. Refactoring path in and out

Introducing the pattern into a monolithic processing function.

1. Identify the ordered list of logically distinct transformation or
   validation steps already inside the monolithic function or class, even
   though they are not yet separated.
2. Extract each step into its own pure function or small class with an
   explicit input type and output type, changing nothing about the order or
   behaviour yet. Run the existing tests after each extraction.
3. Define a shared message schema (or a small family of compatible schemas)
   that every extracted step's output conforms to and every next step's input
   accepts, so the steps genuinely no longer need direct knowledge of each
   other, only of the schema.
4. Introduce the first pipe, in-process to start, as simple as a list of
   functions applied in sequence via a fold or reduce, and verify the
   behaviour is unchanged before touching deployment topology at all.
5. Once the in-process chain is proven correct, decide per stage whether it
   needs independent deployment or independent scaling. Move only the stages
   that need it behind a real pipe, a queue or a broker topic, leaving cheap,
   tightly coupled stages composed in-process. Not every stage has to cross
   the network just because the pattern exists.
6. Add idempotency keys and deduplication at any stage that gained an
   at-least-once pipe, before that stage goes live, not after the first
   duplicate incident.
7. Add the correlation identifier and per-stage telemetry from dimension 16
   before declaring the migration complete, so the new topology is
   observable from day one rather than retrofitted after the first
   incident.

Removing the pattern when it stops earning its place. Signals that removal is
warranted include stages that are always deployed and released together, a
pipeline where every filter after the first is a trivial pass-through, or a
system where the independent-scaling benefit never materialised because
every stage runs at the same load in practice.

1. Confirm the stages truly are always co-deployed by checking release
   history, not by assumption.
2. Inline each filter's logic back into a single ordered function call chain,
   one stage at a time, running the pipeline's existing tests after each
   inlining to confirm behaviour is unchanged.
3. Remove the pipe infrastructure (queues, topics, or brokers) for the
   collapsed stages only after the inlined version has run correctly in
   production for a full deployment cycle, so a rollback path exists during
   the transition.
4. Delete the now-unused schemas and message contracts once nothing else in
   the system depends on them, checking downstream consumers first since a
   pipe's schema sometimes outlives the pipeline that first defined it.

## 15. Testing and verification

Easier because of the pattern.

- Each filter can be unit tested in complete isolation, supplying a sample
  input message and asserting the output message, with no need to stand up
  the rest of the pipeline, its broker, or any other filter.
- A filter's contract, defined by its input and output schema, is naturally
  the seam for contract testing between teams that each own different
  filters in the same pipeline, avoiding the need for a shared integration
  environment to catch a schema mismatch.
- Individual filters can be property tested against their schema alone, for
  example asserting that any valid input record produces a valid output
  record, without needing the rest of the pipeline present.

Harder because of the pattern.

- End-to-end correctness, that the whole pipeline from source to sink
  produces the right result for a given input, now requires either a full
  integration environment with every filter and pipe running, or a carefully
  maintained end-to-end test double chain, since no single process boundary
  contains the whole flow.
- Idempotency and duplicate-delivery behaviour cannot be verified by a single
  call, it requires deliberately redelivering a message to a filter under
  test and asserting the observable side effect happened exactly once, not
  merely that no exception was thrown.
- Ordering-sensitive bugs, see dimension 11, are the hardest class to catch
  in a unit test, since a single-instance unit test of one filter cannot
  reproduce the interleaving that only appears once several instances run in
  parallel against a partitioned pipe.

Techniques that apply.

- **Contract tests per pipe.** One test suite asserting that every producer of
  a given pipe's schema and every consumer of that same schema agree, run
  independently in each filter's own build so a breaking schema change is
  caught before the producing filter is deployed, not after the consuming
  filter starts failing in production.
- **In-memory pipe substitute for integration tests.** Replace the real
  broker with an in-memory or embedded equivalent for a full pipeline
  integration test, keeping the real filter code and only swapping the
  transport, which keeps the test fast while still exercising every filter's
  real logic end to end.
- **Chaos and redelivery tests.** Deliberately redeliver the same message
  twice to a filter under test, or deliver messages out of order to a
  partitioned consumer, and assert the observable state converges to the
  correct result either way, directly exercising the idempotency and
  ordering concerns from dimension 11.
- **Golden-file or snapshot tests on the whole pipeline.** For pipelines that
  transform structured documents, run a fixed input document through the
  whole chain (in-process substitute pipes are fine here) and assert the
  final output matches a committed golden file, catching accidental
  behaviour drift across the whole sequence at once.

## 16. Observability signals

Because a record crosses filter and pipe boundaries the pattern
itself introduces, the record's path has to be reconstructed from telemetry
rather than read off a single call stack, so instrumentation is not optional
polish here, it is load-bearing.

What to record.

- A correlation identifier generated once at the source and propagated
  unchanged through every filter's logs, traces, and output messages, so a
  single record's full path across every stage can be reassembled after
  the fact.
- Per-filter, per-stage counters of messages received, messages successfully
  produced, and messages failed, labelled by filter name, so a stage-level
  success rate is directly visible.
- Pipe depth (queue length or lag) per pipe, since a growing depth on one
  specific pipe localises a slow or stuck downstream filter without needing
  to inspect that filter's own metrics first.
- Per-filter processing duration, as a histogram, so the slowest stage in the
  pipeline, the one that determines end-to-end latency per the Azure
  Architecture Center's own observation that "the time it takes to process a
  single request depends on the speed of the slowest filters in the
  pipeline" (Microsoft, Azure Architecture Center, cited above), is visible
  directly rather than inferred.
- Duplicate-delivery and deduplication-hit counters at any filter relying on
  idempotency, so a rising duplicate rate is caught as a signal rather than
  silently absorbed.

A healthy pipeline on a dashboard. Every pipe's depth is low and flat, or
oscillates within an expected band under load without trending upward.
Per-stage success rates sit near one hundred percent, with failures, when
present, isolated to a specific, known, and alerted-on cause rather than
spread thinly across every stage. Per-stage duration histograms are stable
over time and the slowest stage is the one the team expects to be slowest,
given its known workload, not a surprise. Correlation-identifier-based
traces for a sample of records show the expected number of hops with no
unexplained gaps.

A failing pipeline. One pipe's depth trends upward with no corresponding
increase in the downstream filter's processing rate, which is the
backpressure-collapse failure from dimension 11 becoming visible before it
becomes an incident. A duplicate-delivery counter that used to read zero
starts incrementing, which is the earliest observable sign of the
duplicate-work failure from dimension 11. A specific filter's success rate
drops while every other filter's stays flat, localising a bad deploy or a
downstream dependency outage to exactly one stage without needing to
reproduce the failure. Traces for a sample of records show a variable number
of hops for what should be a fixed-shape pipeline, which is evidence of
either conditional routing behaving unexpectedly or a filter silently
dropping some records.

## 17. Security and privacy implications

The pattern has three concrete implications once it is deployed across
process or network boundaries, beyond the concerns any distributed system
shares.

**Data in transit between filters.** Because a pipe is, in the cloud
variants from dimension 8, a network-visible channel (a queue, a topic, a
storage object), every hop is a place data could be observed or tampered
with if the transport is not secured. Encrypt pipes carrying sensitive data
in transit, and where the pipe is a durable queue or storage service,
encrypt the data at rest in that pipe too, since the message may sit there
for an unbounded time waiting for a slow or scaled-down consumer.

**Filter-level authorization and least privilege.** Each filter, when
independently deployed, should hold only the credentials it needs for its
own pipe reads and writes, not credentials for the whole pipeline's
infrastructure. A filter compromised through a dependency vulnerability
should not, by virtue of its service identity, be able to read or write pipes
belonging to stages it has no legitimate reason to touch. This is the same
least-privilege discipline any microservice needs, made more pressing here
because the very appeal of the pattern is composing many small, independently
built and deployed units, which multiplies the number of service identities
and credentials that must be scoped correctly.

**Sensitive data lingering in intermediate pipes.** A durable pipe retains
its message until consumed, which means personal or regulated data now has
a second place it is stored, beyond the source and the sink, for as long as
the message sits in the queue. Retention and deletion policy for the pipe
infrastructure itself needs to satisfy the same data protection requirements
as the source and sink, and a dead-letter queue holding failed messages is
frequently the place this is overlooked, since a message that failed
processing may sit in a dead-letter queue indefinitely with nobody assigned
to review it.

**Supply chain and filter provenance, when filters are pluggable.** In a
pipeline architecture where third parties can register or supply additional
filters, most relevant to the integration-framework and plugin-style
variants from dimension 8, an untrusted filter runs with whatever
privileges the pipeline infrastructure grants it and can inspect or modify
every message it touches. This mirrors the untrusted-implementor concern any
extensible plugin architecture carries, and the mitigation is the same,
validate what a third-party filter actually does rather than trusting its
declared behaviour, and scope its pipe access narrowly.

On privacy specifically, the correlation identifier recommended in dimension
16 for tracing should itself be reviewed against data protection
requirements if it is, or can be joined with, personal data, since a
correlation identifier that is easy to link back to a specific individual
across every stage of the pipeline is exactly the kind of persistent
identifier privacy regulations are often concerned with.

## Code examples

Three languages chosen for genuinely different idiomatic shapes. Go shows the
concurrent, channel-based shape that is closest to the Unix pipe model and is
the idiomatic Go pattern for exactly this problem. Python shows the
generator-chain shape, which is the idiomatic in-process form in that
language and mirrors lazy streaming without threads. TypeScript shows an
async, queue-backed shape that models the cloud, message-broker variant from
dimension 8 without requiring an actual broker to run the example. Rust is
omitted from the runnable examples because its idiomatic shape is the same
iterator-adapter chain already shown for Python, only with static types
instead of duck typing, so it does not add a genuinely different structural
lesson, and the entry keeps the code budget on the three shapes that differ.

### Go

Channels as pipes, goroutines as filters. This is the idiomatic Go form and
was run with `go run` to confirm it compiles and executes.

```go
package main

import (
	"fmt"
	"strings"
)

func source(words []string) <-chan string {
	out := make(chan string)
	go func() {
		defer close(out)
		for _, w := range words {
			out <- w
		}
	}()
	return out
}

func upperFilter(in <-chan string) <-chan string {
	out := make(chan string)
	go func() {
		defer close(out)
		for w := range in {
			out <- strings.ToUpper(w)
		}
	}()
	return out
}

func lengthFilter(in <-chan string, min int) <-chan string {
	out := make(chan string)
	go func() {
		defer close(out)
		for w := range in {
			if len(w) >= min {
				out <- w
			}
		}
	}()
	return out
}

func main() {
	words := []string{"go", "pipes", "and", "filters", "cloud"}
	pipeline := lengthFilter(upperFilter(source(words)), 4)
	for result := range pipeline {
		fmt.Println(result)
	}
}
```

### Python

Generator functions as filters, lazily consumed by the final `for` loop. Run
with `python3` to confirm output.

```python
def source(words):
    for w in words:
        yield w


def upper_filter(records):
    for w in records:
        yield w.upper()


def length_filter(records, minimum):
    for w in records:
        if len(w) >= minimum:
            yield w


def pipeline(words, minimum):
    return length_filter(upper_filter(source(words)), minimum)


if __name__ == "__main__":
    words = ["go", "pipes", "and", "filters", "cloud"]
    for result in pipeline(words, 4):
        print(result)
```

### TypeScript

An async pipe abstraction modelling the queue-backed cloud variant, with an
in-memory queue standing in for a real broker so the example runs standalone.
Compiled with `npx tsc --strict` to confirm the types check.

```typescript
type Message = { id: number; word: string };

class Pipe<T> {
  private queue: T[] = [];
  push(item: T): void {
    this.queue.push(item);
  }
  drain(): T[] {
    const items = this.queue;
    this.queue = [];
    return items;
  }
}

type Filter<In, Out> = (input: In) => Out;

const upperFilter: Filter<Message, Message> = (m) => ({
  id: m.id,
  word: m.word.toUpperCase(),
});

const lengthFilter =
  (minimum: number): Filter<Message, Message | null> =>
  (m) =>
    m.word.length >= minimum ? m : null;

function runPipeline(
  source: Message[],
  filters: Filter<Message, Message | null>[]
): Message[] {
  const pipeA = new Pipe<Message>();
  source.forEach((m) => pipeA.push(m));

  let current: Message[] = pipeA.drain();
  for (const filter of filters) {
    const nextPipe = new Pipe<Message>();
    for (const msg of current) {
      const result = filter(msg);
      if (result !== null) nextPipe.push(result);
    }
    current = nextPipe.drain();
  }
  return current;
}

const source: Message[] = ["go", "pipes", "and", "filters", "cloud"].map(
  (word, id) => ({ id, word })
);

const output = runPipeline(source, [
  upperFilter as Filter<Message, Message | null>,
  lengthFilter(4),
]);

console.log(output);
```

## 18. References

1. Wikipedia contributors. "Pipeline (Unix)".
   https://en.wikipedia.org/wiki/Pipeline_(Unix) Verified 2026-08-02. Source
   for the McIlroy 1964 concept, Ken Thompson's 1973 `pipe()` implementation
   in Version 3 Unix, and the `|` notation added in Version 4 Unix.
2. Microsoft. "Pipes and Filters pattern". Azure Architecture Center.
   https://learn.microsoft.com/en-us/azure/architecture/patterns/pipes-and-filters
   Verified 2026-08-02. Source for the Context and problem framing, the
   Issues and considerations (idempotency, repeated messages, context and
   state, message tolerance), the When to use and When not to use lists, the
   pairing with Compensating Transaction, and the Azure Functions plus Azure
   Queue Storage plus Azure Blob Storage worked example with claim check.
3. The Apache Software Foundation. "Pipeline EIP". Apache Camel documentation.
   https://camel.apache.org/components/latest/eips/pipeline-eip.html
   Verified 2026-08-02. Source for Apache Camel's implementation of the
   Pipes and Filters pattern as a named EIP construct.
4. The GStreamer team. "Basic concepts". GStreamer Application Development
   Manual.
   https://gstreamer.freedesktop.org/documentation/application-development/introduction/basics.html
   Verified 2026-08-02. Source for the elements-and-pads pipeline
   architecture used as a production example.
5. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*. Addison-Wesley, 2003.
   ISBN 0-321-20068-3. Messaging Systems chapter, Pipes and Filters pattern.
   Source for the message-based cataloguing of the pattern and its pipe and
   filter terminology as applied to enterprise integration rather than to
   operating-system processes.
6. David Garlan, Mary Shaw. "An Introduction to Software Architecture".
   Carnegie Mellon University, School of Computer Science, Technical Report
   CMU-CS-94-166, 1994 (an earlier version circulated as a 1993 technical
   report). Source for the architectural-style formalisation of Pipes and
   Filters as a named style with filters as components and pipes as
   connectors, cited here for the taxonomy the pattern's lineage draws on
   rather than for a specific quoted claim.
