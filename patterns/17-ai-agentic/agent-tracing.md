---
name: Agent Tracing
slug: agent-tracing
family: 17-ai-agentic
category: Observability
aliases: [LLM Tracing, Agent Observability, GenAI Tracing, Trace-Based Agent Debugging]
first_described: "Sigelman, Barroso, Burrows, Stephenson, Plakal, Beaver, Jaspan, Shanbhag 2010 (distributed tracing origin, Google Dapper); adapted to LLM and agent workloads by LangSmith, Langfuse and OpenTelemetry's GenAI semantic conventions working group from 2023 onward"
maturity: emerging
related: [model-context-protocol, function-calling, llm-circuit-breaker, cost-guard, multi-agent-supervisor, react, agent-handoff, evaluation-suite]
incompatible_with: []
verified: 2026-08-02
---

# Agent Tracing

## 1. Name, aliases, and lineage

The pattern is called Agent Tracing in this catalog because its unit of
instrumentation is a single agent invocation, not a single HTTP request. It is
also called LLM Tracing, Agent Observability, or GenAI Tracing depending on the
vendor. The three names describe the same mechanism at slightly different
scopes. LLM Tracing usually means only the model call boundary. Agent
Observability is the umbrella term a vendor uses when it sells dashboards on
top of the traces. GenAI Tracing is the term the OpenTelemetry community uses
in its semantic conventions working group.

The lineage runs through two separate traditions that only merged around 2023.

The first tradition is distributed request tracing for microservice systems.
Benjamin Sigelman and seven co-authors at Google published "Dapper, a
Large-Scale Distributed Systems Tracing Infrastructure" in 2010, describing a
production system that annotated a single logical request with a trace tree of
nested spans as it moved through many machines, using low-overhead sampling and
transparent propagation so application code rarely had to change (Sigelman et
al. 2010, see references). Dapper's vocabulary, a trace as a tree of spans, a
span as a named, timed unit of work with a parent, became the vocabulary every
later tracing system reused. Twitter open sourced Zipkin in 2012 based on the
Dapper paper, and Uber released Jaeger in 2016, donating it to the Cloud Native
Computing Foundation, where it became a graduated project (Jaeger project
documentation, see references). In 2019 two competing instrumentation efforts,
OpenTracing and OpenCensus, merged into OpenTelemetry, a CNCF project that
standardized how traces, metrics, and logs are generated and exported
(OpenTelemetry, "What is OpenTelemetry", see references). The W3C separately
standardized how a trace identifier crosses a network boundary, publishing
Trace Context as a Recommendation on 23 November 2021, defining the
`traceparent` HTTP header carrying a trace id, a parent span id, and sampling
flags (W3C Trace Context, see references).

The second tradition is prompt and chain debugging for large language model
applications. Early LLM frameworks logged a prompt and a completion to a flat
file. As chains grew retrieval steps, tool calls, and multi-turn loops, a flat
log stopped being readable, and framework authors reached for the tracing
vocabulary they already knew from backend work. LangChain shipped LangSmith as
a paid observability product for its own framework starting in 2023. Langfuse
launched as an open source alternative the same year, explicitly building an
OpenTelemetry-compatible ingestion path so a trace could originate from any
instrumented framework, not only its own SDK (Langfuse observability docs, see
references). OpenAI shipped tracing as a built-in feature of its Agents SDK,
recording a trace per workflow run composed of typed spans for model
generations, tool calls, and handoffs (OpenAI Agents SDK tracing docs, see
references). By 2024 the OpenTelemetry community had formed a GenAI semantic
conventions working group to standardize span names and attribute keys for
model calls, tool executions, and agent invocations across all of these tools,
publishing conventions such as the `invoke_agent` span and the
`gen_ai.operation.name` attribute (OpenTelemetry GenAI semantic conventions,
gen-ai-agent-spans, see references).

The `maturity` field for this entry is `emerging`. The underlying distributed
tracing mechanism is `canonical`, proven over fifteen years of production use.
The agent-specific naming layer on top of it, the exact span names, the exact
attribute keys, is still being standardized as of the verification date of this
entry, and different vendors disagree on details even while agreeing on the
shape.

## 2. Problem and context

An agent that calls a model, receives a decision to call a tool, calls that
tool, feeds the result back to the model, and repeats until it produces an
answer, fails in ways a stack trace cannot explain. The process did not crash.
It ran to completion and returned a wrong answer, a slow answer, or an
expensive answer, and the reason lives inside a sequence of natural language
decisions that a debugger cannot step through.

Three symptoms recur once an agent moves from a demo to a system with real
traffic. First, an operator is told "the assistant gave a wrong answer" and has
no way to reconstruct what the model actually saw at each step, because the
prompt was assembled dynamically from retrieval results, prior turns, and tool
output that no longer exists anywhere by the time the ticket is filed. Second,
latency becomes unpredictable because a single user turn can trigger a variable
number of model calls and tool calls depending on what the model decides to
do, and a flat request-duration metric cannot say whether the slow turn spent
its time waiting on the model, waiting on a tool, or looping. Third, cost
becomes unpredictable for the same reason. A retry loop, a tool the model calls
three times when once would do, or a context window that grows every turn
because nothing prunes it, all show up as a monthly bill spike with no
attribution to the code path that caused it.

Agent Tracing treats one agent invocation as a distributed trace, the same
mental model Dapper applied to a web request crossing many backend services.
The agent invocation becomes the root span. Every model call, every tool call,
every retrieval step, and every sub-agent delegation becomes a child span
carrying its own start time, end time, inputs, outputs, and status. The trace
that results is a record a person can read after the fact to answer three
questions in order. What did the model see. What did the model decide. What
happened when that decision was carried out. The context this pattern assumes
is an agent with more than one internal step, running in an environment where
requests are not reproducible on demand, because the model is not
deterministic and the world the agent touches, a database, an API, a file
system, changes between the failure and the investigation.

## 3. Forces

Note. This dimension is largely engineering judgement about which pressures a
given tracing setup favors, not a sourced claim about a specification.

- **Debuggability.** Favored, and the entire reason the pattern exists. A trace
  reconstructs a failed run after the fact without needing to reproduce it.
- **Payload size and cost.** Sacrificed unless deliberately managed. A trace
  that records every prompt, every tool argument, and every model response in
  full, for every request, multiplies storage and export cost by the size of
  the payloads being traced, which for an agent are often the largest payloads
  in the system.
- **Privacy and data residency.** Sacrificed unless deliberately managed. A
  trace that carries a full prompt also carries whatever personal data,
  credentials, or internal documents that prompt was built from, and it now
  exists a second time in a tracing backend with its own retention policy.
- **Latency.** Mildly sacrificed. Span creation and export add overhead per
  step. In practice this overhead is small relative to a model call, which
  usually costs hundreds of milliseconds to several seconds, but it is not
  free, and a naive synchronous exporter can add real latency to the critical
  path if it is not decoupled from the request.
- **Sampling fidelity versus cost.** A direct trade. Tracing every request
  gives complete data and the highest cost. Sampling reduces cost and risks
  missing exactly the rare, expensive failure the pattern was built to catch,
  because failures are not uniformly distributed across a sample.
- **Vendor lock-in versus standardization.** Favors openness when the trace is
  emitted through OpenTelemetry's vocabulary rather than a single vendor's
  proprietary SDK, at the cost of losing convenience features a single-vendor
  SDK bundles for free, such as an automatic evaluation queue tied to trace
  data.
- **Operability for a human, not just a machine.** Favored when span and
  attribute names are chosen so an operator reading the trace understands the
  agent's decision without cross-referencing source code. Sacrificed when
  attributes are dumped as opaque JSON blobs that require the original
  developer to interpret.

A tracing setup that captured everything, at full fidelity, forever, with no
review of retained data, would eliminate the debuggability tradeoff entirely
and create a privacy and cost problem instead. The pattern only earns its place
when someone actively decides what to keep, what to redact, and how long to
keep it.

## 4. Applicability and non-applicability

Reach for Agent Tracing when the following hold.

- The system contains an agent loop with more than one internal decision step,
  meaning at least one model call followed by a tool call or a second model
  call, so that a flat request log cannot show the sequence of decisions.
- Requests are not cheaply reproducible, because the model's output varies
  between calls, or because the tools the agent touches have side effects or a
  changing external state, so debugging must work from a recorded trace rather
  than a live re-run.
- More than one person needs to look at agent behavior after the fact, which
  makes an ad hoc `print` or local log file insufficient, because it never
  leaves the machine that produced it.
- Cost or latency needs to be attributed to a specific step in the agent's
  decision sequence, for example distinguishing a slow retrieval call from a
  slow model call from a slow tool call.
- The system already runs behind an existing distributed tracing setup for its
  non-agent services, so extending the same trace through the agent call
  preserves one unified view of a request instead of two disconnected ones.
- Compliance or audit requirements exist around what an autonomous system
  decided and why, which a trace answers directly and a metric cannot.

Do NOT reach for Agent Tracing, or reach for a lighter version of it, in these
cases, and the reason matters more than the rule.

- **A single, stateless prompt-completion call with no tool use and no loop.**
  A request log line with the prompt hash, the model name, the token counts,
  and the latency answers every question a trace would answer, at a fraction
  of the implementation and storage cost. Adding spans, parent-child
  relationships, and a trace exporter for one API call is instrumentation for
  a problem the system does not have yet.
- **A prototype or internal experiment with a handful of daily calls.**
  Standing up an exporter, a collector, and a backend to store traces costs
  more engineering time than the debugging time it saves at that volume.
  `print` statements and a spreadsheet are the honest tool at this scale.
- **The team has not decided what counts as sensitive in a prompt.** Tracing
  captures exactly what the agent saw, which means it captures every piece of
  personal data, secret, or proprietary document that made it into the prompt.
  Turning tracing on before deciding a redaction policy produces a second copy
  of sensitive data sitting in a system with weaker access controls than the
  primary application, and this is worse than not tracing at all.
- **The goal is real-time intervention, not after-the-fact analysis.** A trace
  is written after a span ends. If the requirement is stopping an agent
  mid-run before it takes a dangerous action, that is `output-guardrails` or
  `human-in-the-loop`, which run synchronously inside the loop, not tracing,
  which is fundamentally a record of what already happened.
- **The system already emits sufficient signal through structured metrics
  alone.** If every question that matters, "how many tool calls per turn on
  average", "what fraction of turns hit a retry", can be answered by a counter
  or a histogram, a full trace pipeline is more machinery than the question
  needs. Metrics are cheaper to store and query at scale than traces are.
- **A single developer debugging locally, iterating in a REPL.** The
  interactive session itself is the debugging tool. Wrapping every call in a
  tracer to debug a script that runs once and exits adds ceremony without a
  second person or a later date to benefit from the record.

## 5. Structure

Six participants, named by the role each plays in the pipeline.

- **Instrumented code.** The agent loop, the model client, the tool executors,
  and any retrieval step, each wrapped so that entering and leaving the unit of
  work creates and closes a span. This is the only participant application
  code touches directly.
- **Tracer.** The object, usually one per process, that knows the current
  active span (through a stack or a context variable), mints new span and trace
  identifiers, and hands a finished span to the exporter. The tracer is what
  the instrumented code calls.
- **Span.** The unit of record. Carries a name, a trace id shared with every
  other span in the same logical run, a span id unique to itself, a parent
  span id linking it to its caller, a kind (internal work, a call to another
  service, or a call received from another service), a start and end
  timestamp, a set of key-value attributes, a set of timestamped events, and a
  status.
- **Context propagation carrier.** The mechanism that moves the current trace
  id and parent span id across a boundary the tracer cannot see through
  directly, an in-process call stack, an async task boundary, a queue message,
  or an outbound HTTP call to a tool running in another process. The W3C
  `traceparent` header is the standardized carrier for the HTTP case (W3C
  Trace Context, see references).
- **Exporter.** Serializes a finished span and sends it somewhere durable,
  typically over OTLP, the OpenTelemetry line protocol, to a collector or
  directly to a backend.
- **Backend and query surface.** Stores spans, reconstructs the trace tree from
  the parent-child links, and renders it as a waterfall or a tree for a human,
  or exposes it for programmatic query and alerting. Jaeger, Datadog, Langfuse,
  and LangSmith each play this role for different audiences.

Relationships. Instrumented code depends only on the Tracer's interface, never
on the Exporter or the Backend directly, which keeps the instrumentation
portable across backends. A Span belongs to exactly one Trace, identified by
the shared trace id, and has at most one parent Span, forming a tree rather
than a graph. The Tracer holds the currently active span so that a nested call
can find its parent without the caller having to pass the parent explicitly,
which is what makes instrumentation additive rather than requiring every
function signature in the call chain to be rewritten to thread a context
object through by hand, in languages that support an implicit context
mechanism such as a context variable or a thread-local.

## 6. ASCII structure diagram

```
   +------------------+        creates/ends       +------------------+
   |  Instrumented     |  ----------------------->  |      Span        |
   |  Code (agent      |                             |------------------|
   |  loop, tool call, |        reads current        | trace_id         |
   |  model client)    |  <-----------------------   | span_id          |
   +--------+----------+       active span           | parent_span_id   |
            |                                        | kind             |
            | start_span / end_span                  | start, end       |
            v                                        | attributes[]     |
   +------------------+                              | events[]         |
   |      Tracer       |                              | status           |
   |------------------|                               +------------------+
   | active span stack |                                       |
   | mint ids          |                                       | on end
   +--------+----------+                                       v
            |                                        +------------------+
            | hands finished span to                 |     Exporter     |
            +---------------------------------------> |  (OTLP client)   |
                                                       +--------+---------+
                                                                |
                                                     traceparent header
                                                     crosses process
                                                     boundary here, to
                                                     a remote tool or
                                                     sub-agent process
                                                                |
                                                                v
                                                       +------------------+
                                                       |    Collector /   |
                                                       |     Backend      |
                                                       | (rebuilds trace  |
                                                       |  tree by parent  |
                                                       |  span id)        |
                                                       +------------------+

   One Trace is a tree of Spans, linked only by trace_id and parent_span_id.
   The tree shape is reconstructed at query time, never sent as a tree.
```

## 7. Dynamics

The runtime flow below traces a single user turn that requires one tool call,
the minimal loop that makes tracing worth doing at all. Note that the agent
invocation span (`invoke_agent`) opens before the first model call and closes
only after the final model response, so its duration is the full user-visible
latency, while each `chat` and `execute_tool` span underneath it accounts for
one slice of that duration.

```
User        Agent (invoke_agent span)     Tracer         Model (chat span)   Tool (execute_tool span)
 |                    |                      |                    |                    |
 |-- ask ------------>|                      |                    |                    |
 |                    |-- start_span("invoke_agent") ------------>|                    |
 |                    |                      |-- span A opens --->|                    |
 |                    |-- start_span("chat") ----------------------------------------->|
 |                    |                      |-- span B opens, parent=A ------->|      |
 |                    |                      |                    |<-- call model -----|
 |                    |                      |                    |-- decision:        |
 |                    |                      |                    |   call tool  ------|
 |                    |<-- tool_calls -------|                    |                    |
 |                    |-- end_span(B) ------>|                    |                    |
 |                    |-- start_span("execute_tool") ----------------------------------------->|
 |                    |                      |-- span C opens, parent=A -------------->|
 |                    |                      |                                          |-- run tool
 |                    |<-- tool result ------|                                          |
 |                    |-- end_span(C) ------>|                                          |
 |                    |-- start_span("chat") (second call) ------------------->|
 |                    |                      |-- span D opens, parent=A ------>|
 |                    |                      |                    |<-- call model with
 |                    |                      |                    |    tool result -----|
 |                    |<-- final answer -----|                    |                    |
 |                    |-- end_span(D) ------>|                    |                    |
 |                    |-- end_span(A) ------>|                    |                    |
 |<-- answer ---------|                      |                    |                    |
 |                    |             exporter flushes A, B, C, D as one trace           |
```

Two timing notes carried over from distributed tracing practice and confirmed
by direct observation in the reference implementation below. First, a span
must be closed even when the work inside it raises an exception, or the trace
loses that step entirely and the record misrepresents what happened. The
common fix is a `try/finally` or an equivalent context manager, so the span
records an error status and closes rather than being silently dropped. Second,
because the tracer's active-span tracking is implicit, per-request or per-task
state (a context variable in Python, an async local in Node, a request-scoped
value in Go), any code path that spawns genuinely parallel work, a thread pool,
a fire-and-forget task, or a queue consumer, must propagate the trace context
explicitly across that boundary, because the implicit mechanism does not
follow control flow that leaves the calling stack.

## 8. Implementation variants

**Manual span wrapping.** The instrumented code calls `tracer.start_span` and
`tracer.end_span` (or an equivalent context manager) explicitly at every step
worth recording. This is the form shown in dimension 7 and in the code
examples below. It costs the most lines of application code but gives complete
control over what becomes a span and what attributes it carries, which matters
most when a team is deciding its own attribute vocabulary before adopting a
standard one.

**Decorator or middleware wrapping.** A function or class method is annotated,
and the tracing library creates and closes the span around the call
automatically, inferring the span name from the function name and inferring
some attributes from the function's arguments. This trades explicit control
for less boilerplate, and works well for tool functions where the same shape
repeats across every tool. Both LangSmith and Langfuse offer this as their
default integration path, wrapping a framework's existing call sites rather
than asking application code to call a tracer directly (LangSmith observability
docs, Langfuse observability docs, see references).

**Framework-level auto-instrumentation.** The agent framework itself emits
spans for every model call, tool call, and handoff without any tracing code in
application logic at all, because tracing is built into the framework's
runtime. The OpenAI Agents SDK does this, wrapping every tool call in a
`function_span()`, every agent-to-agent handoff in a `handoff_span()`, and every
guardrail check in a `guardrail_span()`, all under one `Trace` per
`workflow_name` (OpenAI Agents SDK tracing docs, see references). This gives
the most consistency across an organization's agents at the cost of tying
instrumentation shape to the framework's own model of what a step is, which
can be a poor fit if the application's real unit of work does not match the
framework's built-in one.

**OpenTelemetry-native instrumentation.** Spans are created directly through
the OpenTelemetry API using the vendor-neutral GenAI semantic conventions,
`gen_ai.operation.name`, `gen_ai.agent.name`, `gen_ai.tool.name`, and so on
(OpenTelemetry GenAI semantic conventions, see references), and exported over
OTLP to any OpenTelemetry-compatible backend. This is the variant that avoids
lock-in, because the same trace can be read by Jaeger, Datadog, Langfuse, or a
homegrown backend without re-instrumenting, at the cost of the vocabulary
still being new enough as of the verification date of this entry that not
every attribute a team wants yet has a standardized name.

**Runtime-level tracing built into the agent host itself.** Rather than the
application choosing to instrument, the process running the agent exports
spans for its own internal operations. Claude Code exports a span hierarchy
rooted at `claude_code.interaction`, with `claude_code.llm_request`,
`claude_code.hook`, and `claude_code.tool` as children, when distributed
tracing is enabled, giving an operator visibility into what the coding agent
did during a session without any instrumentation work in the agent's own
prompt or tool code (Anthropic, Claude Code monitoring usage, see references).
This variant is the least work for an application team and the least flexible,
because the span shape is fixed by the host, not the application.

**Sampling and redaction as a first-class layer.** Any of the variants above
can be combined with a processor that runs before export, dropping or
truncating attributes above a size threshold, hashing or redacting fields
matching a sensitive-data pattern, and sampling a fraction of traces rather
than exporting every one. This is not optional in a production system, as
argued in dimension 3, and is usually implemented as an OpenTelemetry span
processor or an equivalent hook in whichever tracing library is in use.

## 9. Known production uses

**Claude Code, Anthropic's coding agent.** When enhanced telemetry is enabled,
Claude Code exports OpenTelemetry spans and events linking each user prompt to
the model calls, hook executions, and tool executions it triggers, with a
documented span hierarchy of `claude_code.interaction` containing
`claude_code.llm_request`, `claude_code.hook`, and `claude_code.tool` spans,
alongside `claude_code.tool.execution` and `claude_code.tool.blocked_on_user`
as further children, exported over OTLP to any configured backend. Anthropic,
"Monitoring usage", Claude Code documentation,
https://code.claude.com/docs/en/monitoring-usage
verified 2026-08-02.

**OpenAI Agents SDK.** The SDK records LLM generations, tool calls, handoffs,
guardrails, and custom events as a full record of an agent run, grouped under
one `Trace` per logical `workflow_name`, with
each step wrapped in a typed span, `function_span()` for tool calls,
`handoff_span()` for agent-to-agent transfer, and `guardrail_span()` for
guardrail checks, and traces optionally grouped by `group_id` to link every
trace in one conversation. OpenAI, "Tracing", openai-agents-python
documentation, https://openai.github.io/openai-agents-python/tracing/
verified 2026-08-02.

**LangSmith, LangChain's commercial observability product.** LangSmith
provides trace-level visibility for applications built on LangChain and
LangGraph and, through its SDK, for applications built without either,
supporting trace inspection, filtering, sharing, and automated online
evaluation over recorded runs, and integrates with OpenAI, Anthropic, CrewAI,
and Pydantic AI among other frameworks. LangChain, "Observability", LangSmith
documentation, https://docs.langchain.com/langsmith/observability
verified 2026-08-02.

**Langfuse.** Langfuse defines a trace as the full execution record of an
application run, an observation (its term for a span) as one unit of work
inside that trace, and a generation as an observation type reserved for LLM
calls specifically, recording prompt, model, and output for that step. Langfuse
accepts traces natively through its own SDKs and also accepts standard
OpenTelemetry OTLP traces directly, so an application already emitting OTel
spans needs no separate Langfuse-specific instrumentation. Langfuse, "Get
Started with Observability", https://langfuse.com/docs/observability/get-started
verified 2026-08-02.

**Datadog LLM Observability.** Datadog models each request served by an
application as a trace, which can wrap "individual inferences, predetermined
workflows, or dynamic agent-executed workflows", with spans representing "each
choice made by an agent or each step of a given workflow", automatically
instrumenting OpenAI, LangChain, AWS Bedrock, and Anthropic SDK calls without
requiring code changes, and capturing token usage, cost, and latency alongside
each span. Datadog, "LLM Observability",
https://docs.datadoghq.com/llm_observability/
verified 2026-08-02.

**Jaeger, the general-purpose distributed tracing backend many agent tracing
pipelines export into.** Jaeger was released as open source by Uber
Technologies in 2016 and donated to the Cloud Native Computing Foundation,
where it is a graduated project, and Jaeger v2, released in 2024, is built
directly on the OpenTelemetry Collector, which is what lets an agent tracing
pipeline emitting standard OTLP spans use Jaeger as its backend with no
custom adapter. Jaeger project, documentation,
https://www.jaegertracing.io/docs/latest/
verified 2026-08-02.

## 10. Consequences

Positive.

- A failed agent run becomes reconstructable after the fact, by anyone with
  access to the trace, without needing the original request to still be
  reproducible.
- Latency and cost attribute to a specific step rather than to the request as
  a whole, which turns "the assistant is slow" into "the retrieval step is
  slow" or "the third model call in the loop is slow", a concrete, actionable
  finding.
- The trace tree makes tool-call loops, redundant calls, and retry storms
  visible as a shape, a wide flat trace or a deep repeating one, that a person
  can recognize at a glance in a waterfall view, before reading a single
  attribute.
- When built on OpenTelemetry and the GenAI semantic conventions rather than a
  single vendor's proprietary format, the same trace data is portable across
  backends, so switching observability vendors does not require
  re-instrumenting the agent.
- Traces feed evaluation pipelines directly. A recorded run's inputs and
  outputs at each step can become a test case, closing the loop between
  production behavior and the `evaluation-suite` and `golden-dataset`
  patterns.

Negative.

- Every trace that records full prompts and full model outputs duplicates the
  most sensitive and largest data in the system into a second store, which is
  a real privacy and security liability unless redaction and access control
  are treated as part of the tracing setup from the start, not added later.
- Storage and export cost scale with the size and volume of what is traced,
  and an agent's prompts, which grow every turn as conversation history
  accumulates, are exactly the kind of payload that makes this cost grow
  faster than a comparable non-agent system's traces would.
- A trace only records what the instrumentation captured. A step that was not
  wrapped in a span is invisible, and a partially instrumented agent gives a
  false sense of completeness, a trace that looks complete but silently skips
  the one step that actually failed.
- The span-name and attribute vocabulary is not fully settled as of the
  verification date of this entry, so an organization that picks its own names
  today risks a migration later if it wants to adopt the OpenTelemetry GenAI
  conventions once they stabilize.
- Tracing answers "what happened" well and "why the model decided this"
  poorly. A span records the model's output, not its reasoning process, so
  tracing complements but does not replace techniques such as
  `chain-of-thought` prompting or a dedicated evaluation pipeline when the
  question is model judgement quality rather than execution flow.

## 11. Failure modes and misuse

Note. This dimension draws on direct hands-on experience building the
reference implementation for this entry and on patterns described by the
observability vendors cited above, not on a single authoritative source for
each failure.

- **Symptom.** A trace shows the agent's root span with the correct total
  duration, but no child spans underneath it, so the trace is useless for
  attributing where the time went.
  **Cause.** The tool-call and model-call code paths were never wrapped in
  their own spans, only the outer agent loop was instrumented, often because
  instrumentation was added at the entry point first and never finished.
  **Fix.** Treat every call across a real boundary, a model API, a tool
  execution, a retrieval query, as a span by policy, and enforce it in code
  review or with a lint rule that flags an uninstrumented call to a known
  model or tool client.

- **Symptom.** Two spans that should share a trace id, for example a tool call
  made in a background worker triggered by the agent, show up as two separate
  root traces in the backend instead of one connected trace.
  **Cause.** The trace context (trace id and parent span id) was not
  propagated across the process or thread boundary between the caller and the
  worker, because propagation was assumed to be automatic when it is only
  automatic within a single call stack tracked by the tracer's own context
  mechanism.
  **Fix.** Explicitly serialize the current trace context (for example as a
  `traceparent` header per the W3C Trace Context format) when handing work to
  a queue, a background thread, or a remote service, and restore it as the
  active context on the receiving side before starting the next span.

- **Symptom.** The tracing backend's monthly bill or storage grows far faster
  than request volume, and nobody can explain why.
  **Cause.** Full, unredacted prompts and model responses are being recorded
  on every span with no sampling and no size limit, and conversation history
  grows every turn, so the payload recorded per trace grows over the life of
  a session rather than staying constant.
  **Fix.** Cap the size of any attribute value at export time, truncate
  conversation history recorded in a span to the delta for that turn rather
  than the full accumulated history, and introduce sampling once the system
  has enough volume that a full record of every request is no longer
  affordable, retaining a bias toward always sampling error and outlier-
  latency traces.

- **Symptom.** A production incident review finds that a trace exists for the
  failing request, but the attribute that would explain the failure, the
  actual tool arguments the model chose, was never recorded, so the trace
  confirms a failure occurred without explaining why.
  **Cause.** Spans were created with only structural attributes (names, ids,
  durations) and no semantic attributes describing what the step actually did,
  because instrumentation was added purely to satisfy "we have tracing now"
  rather than to answer a specific debugging question in advance.
  **Fix.** Decide, before instrumenting, what question each span type needs to
  answer after the fact ("what tool, with what arguments, returning what
  result, at what cost") and record exactly those attributes, using a
  consistent naming convention such as the OpenTelemetry GenAI attributes
  rather than ad hoc keys that differ span by span.

- **Symptom.** Personal data or a customer's proprietary document text shows
  up in the tracing backend's search index, accessible to anyone on the
  engineering team with read access to traces, well beyond who would normally
  see that data.
  **Cause.** No redaction step exists between "the model saw this" and "this
  is stored in the tracing backend forever", and the tracing backend's access
  controls and retention policy are treated as an afterthought rather than as
  part of the data-handling review the rest of the application already went
  through.
  **Fix.** Apply redaction (hashing, truncation, or field removal) as a
  processor in the export path, before data leaves the process, treat the
  tracing backend as a system that itself needs a data classification review,
  and set a retention window on trace data that matches the shortest
  retention policy the underlying content is entitled to, not the tracing
  vendor's default.

## 12. Trade-off matrix

Compared against the alternatives an operator would otherwise reach for on an
agentic system.

| Approach | Reconstructs a failed run | Attributes cost/latency per step | Payload and storage cost | Setup cost | Real-time intervention |
|---|---|---|---|---|---|
| Agent Tracing (this pattern) | Yes, complete | Yes, per span | High unless redacted and sampled | Medium to high | No, after the fact only |
| Flat structured logging (one log line per request) | Partial, no step breakdown | No, only total | Low | Low | No |
| Metrics only (counters, histograms) | No | Aggregate only, not per request | Lowest | Low | No, aggregate signal only |
| Output/Input Guardrails | No, not their purpose | No | N/A | Medium | Yes, blocks before the step completes |
| Human-in-the-Loop approval | No, not their purpose | No | N/A | Medium to high | Yes, blocks before the step executes |
| LLM-as-Judge evaluation on sampled traffic | Partial, judges the output not the path | No | Medium | Medium | No, runs after the response is already sent |

Agent Tracing and metrics answer different questions at different cost, and
the honest setup uses both together rather than treating one as a replacement
for the other. Metrics tell an operator that something is wrong across a
population of requests, cheaply, continuously. Tracing tells the operator
exactly what happened in one specific request, expensively, on demand. Neither
substitutes for `output-guardrails` or `human-in-the-loop`, which prevent a
bad action rather than recording it.

## 13. Related and incompatible patterns

- **`model-context-protocol`.** When an agent calls tools through MCP, each MCP
  tool invocation is a natural span boundary, and the trace context should
  propagate across the MCP transport the same way it propagates across any
  other process boundary, so a tool implemented as a separate MCP server still
  shows up as a connected child span rather than a disconnected trace.
- **`function-calling`.** Agent Tracing is the observability layer that makes
  function calling debuggable at scale. Every tool call function-calling
  produces is a candidate span, and the attribute vocabulary this entry
  describes (`gen_ai.tool.name`, tool arguments, tool result) is specifically
  the record of a function-calling decision and its outcome.
- **`llm-circuit-breaker` and `cost-guard`.** Both patterns need per-call
  latency, error rate, and token cost data to make their decisions, and a
  trace is a natural source of that data, though in practice both are usually
  wired to the metrics emitted alongside a trace rather than to the trace
  itself, because a circuit breaker needs an aggregate signal in real time,
  which dimension 12 already distinguishes from what tracing provides.
- **`multi-agent-supervisor` and `agent-handoff`.** In a multi-agent system,
  the trace is what makes the handoff visible as a single connected flow
  rather than as two unrelated agent runs. The supervising agent's span is the
  natural parent of each delegated sub-agent's span, and losing that parent
  link at a handoff boundary is the specific failure mode described in
  dimension 11 under context propagation.
- **`evaluation-suite`.** Traces recorded in production are a direct source of
  new test cases for an evaluation suite, closing the loop between what
  actually happened for real users and what the offline evaluation pipeline
  checks going forward.
- **`react`.** The ReAct loop's alternating thought, action, observation
  structure maps directly onto a trace's alternating model-call and tool-call
  spans, and a ReAct agent with no tracing is one of the harder agent shapes
  to debug from logs alone, because the reasoning that led to each action is
  otherwise discarded once the loop moves on.

Nothing sits in the `incompatible_with` list for this entry, because tracing is
an observability layer that sits alongside any agent architecture rather than
competing with one, though the amount of value it returns grows with the
complexity of the agent it is attached to, as argued in dimension 4.

## 14. Refactoring path in and out

Introducing tracing into an agent that has none, in order.

1. Identify the entry point of one full agent invocation, the function or
   handler that receives a user turn and eventually returns an answer, and
   wrap it in a root span before touching anything internal to the loop.
2. Add a span around every outbound model call, recording at minimum the model
   name and whether the call ended in a tool-call decision or a final answer,
   which alone already answers "how many model calls did this turn take" and
   "where did most of the time go" without touching tool code yet.
3. Add a span around every tool execution, recording the tool name and a
   size-capped summary of its arguments and result, which now makes tool-call
   loops and redundant calls visible.
4. Verify the trace context survives every boundary the agent crosses that is
   not a plain synchronous function call, a queue, a thread pool, a remote MCP
   server, an async task spawned and awaited later, using the failure mode in
   dimension 11 as a checklist.
5. Add a redaction and size-capping processor to the export path before
   turning tracing on for real user traffic, not after, per the
   non-applicability warning in dimension 4 about deciding a sensitivity
   policy first.
6. Introduce sampling once volume makes tracing every request unaffordable,
   biased toward keeping every error and every outlier-latency trace, and
   sampling the rest.
7. Migrate ad hoc attribute names to the OpenTelemetry GenAI semantic
   conventions where they exist, so the trace data becomes portable across
   backends rather than tied to whichever names were chosen first.

Removing tracing, or scaling it back, when it stops earning its place.

1. If the agent has shrunk to a single model call with no tool use, per
   dimension 4's non-applicability case, delete the span wrapping and replace
   it with a single structured log line, because the tree structure a trace
   provides has nothing left to represent.
2. If cost has become the dominant complaint and debugging value has plateaued,
   reduce fidelity before removing tracing outright, dropping full payload
   capture in favor of size, duration, and status only, which keeps the
   attribution value from dimension 10 while cutting most of the storage cost
   from dimension 3.
3. Never remove tracing from a system with an active compliance or audit
   requirement around agent decisions without first confirming with whoever
   owns that requirement that a lighter-weight record satisfies it, because
   the audit trail, not the debugging convenience, is often the reason
   tracing was mandated in the first place.

## 15. Testing and verification

Testing code that emits spans has one easy part and one part that is easy to
get wrong. The easy part is testing that the traced business logic still
behaves correctly, which needs no change at all, since wrapping a call in a
span does not alter its return value or its side effects when the tracing
plumbing is written correctly. The part that is easy to get wrong is verifying
the trace structure itself, the parent-child relationships, the attributes,
and the status on error, which is a different testing concern from testing
business logic and is skipped far more often than it should be.

A test double for the tracer is the right tool. Rather than exporting to a
real backend during a test, install a Tracer implementation whose exporter
appends every finished span to an in-memory list, exactly as the reference
implementation below does for its demonstration, then assert against that
list. Concrete assertions worth writing for any agent tracing setup include
the following.

- The agent's root span and every span created during the run share one trace
  id, catching the context-propagation failure mode from dimension 11 before
  it reaches production.
- Every span whose function raised an exception is recorded with an error
  status rather than being silently absent from the exported list, catching
  the case where an exception unwinds past a span boundary that fails to close
  it.
- A tool-call span's attributes include the tool name and, in a bounded test
  environment where doing so is safe, its arguments and result, verifying the
  semantic-attribute failure mode from dimension 11 rather than only checking
  that a span with the right name exists.
- The number of spans produced for a fixed, scripted sequence of model
  responses matches an exact expected count, which catches a duplicate span
  (the same step traced twice) or a missing span (a step silently untraced)
  that a looser assertion such as "at least one span exists" would miss.
- A payload above the configured size cap is truncated in the exported span,
  not the raw payload, verifying the redaction and size-capping processor from
  the refactoring path in dimension 14 actually runs rather than only existing
  in configuration.

Integration-level verification, once a real backend is in the loop, should
confirm that the OTLP export succeeds under a simulated backend outage without
blocking the agent's response to the user, since an exporter on the critical
path is a latency and availability risk the pattern must not introduce, per
the latency force named in dimension 3.

## 16. Observability signals

This is the pattern that supplies observability to the rest of an agentic
system, so this dimension is about how to observe the tracing pipeline itself,
which is easy to overlook precisely because it is the thing usually watching
everything else.

A healthy tracing pipeline shows the following on its own dashboard.

- **Export success rate**, the fraction of finished spans that were
  successfully delivered to the collector or backend, close to 100 percent. A
  drop here means the trace record for that period is incomplete, and any
  conclusion drawn from traces during that window should be treated as
  suspect.
- **Exporter queue depth or buffer utilization**, staying low and stable. A
  steadily growing queue means the exporter cannot keep up with span volume,
  which precedes either dropped spans or, worse, a memory-growth incident in
  the traced application itself if the buffer is unbounded.
- **Span count per trace, as a distribution, not a single number.** A sudden
  shift in this distribution, traces that used to average four spans now
  averaging forty, is itself an operational signal, usually a retry loop or an
  infinite tool-call cycle, that is worth alerting on directly rather than
  waiting for someone to open an individual trace and notice.
- **Attribute payload size per span, as a distribution.** A growing tail on
  this distribution is the early warning for the storage-cost failure mode in
  dimension 11, visible well before the monthly bill reflects it.
- **Sampling rate actually applied, versus the configured target rate.** These
  two numbers diverging means the sampler is misconfigured or is being
  overridden somewhere in the pipeline, silently changing what fraction of
  incidents will have a trace available when someone goes looking for one.

A failing tracing pipeline looks like normal application behavior with no
visible symptom in the primary system, which is the specific danger of this
pattern. The agent itself keeps working, users keep getting answers, and the
absence is only discovered the next time someone needs a trace and finds none,
usually during the exact incident the pipeline exists to help diagnose. This is
why export success rate belongs on an always-visible dashboard rather than
something checked only when a trace is needed.

## 17. Security and privacy implications

Note. This dimension is analytical, reasoning from what the pattern records
about the application's own security posture, rather than citing a single
authoritative source for each implication.

Agent Tracing, by design, records the most sensitive data an agentic system
handles. A span capturing a model call captures the full prompt, which for a
retrieval-augmented agent includes whatever documents were retrieved, and for
a conversational agent includes the user's full message history. A span
capturing a tool call captures the arguments passed to that tool, which for a
database query tool or a customer-record lookup tool is frequently personal
data by definition. This is not an edge case the pattern occasionally touches.
It is the pattern's entire value proposition, and a team that treats tracing
data as lower-sensitivity than the primary application's data store is wrong
by construction.

The concrete implications, each requiring an explicit decision rather than a
default.

- **A tracing backend is a second copy of the application's sensitive data,**
  usually with weaker access controls than the primary database, because it
  was provisioned as an observability tool rather than reviewed as a data
  store. Every person with read access to the tracing dashboard has, in
  effect, read access to whatever sensitive content passed through a traced
  prompt or tool call.
- **Trace export crosses a network boundary,** to a collector, and often to a
  third-party SaaS backend outside the organization's own infrastructure. That
  boundary needs the same transport security (TLS) and, where the backend is a
  third party, the same data-processing agreement review that any other
  third-party integration handling personal data would need.
- **Trace retention is a second retention policy** that must be reconciled
  with whatever retention policy governs the underlying data. A user who
  exercises a data-deletion right against the primary application, but whose
  conversation history persists unredacted in trace storage under a longer
  default retention window, has not actually had their data deleted.
- **Credentials and secrets leak into traces easily and by accident,** because
  a tool's arguments or a model's context sometimes legitimately include an
  API key, an authorization token, or a connection string that was never meant
  to be logged anywhere, and a generic tracing instrumentation captures
  arguments indiscriminately unless a specific field-level redaction rule
  excludes them.
- **A trace is itself a map of the agent's internal tool surface and
  decision logic,** which is useful to an attacker who gains read access to
  the tracing backend, since it reveals exactly which internal tools exist,
  what arguments they accept, and under what conditions the agent decides to
  call them, information that would otherwise require reverse-engineering the
  application to obtain.

None of these implications argue against using the pattern. They argue for
treating the redaction, access control, retention, and third-party review
steps named in dimensions 3, 4, and 11 as required parts of adopting Agent
Tracing, not optional hardening to add once time allows.

## 18. References

1. Benjamin H. Sigelman, Luiz Andre Barroso, Mike Burrows, Pat Stephenson,
   Manoj Plakal, Donald Beaver, Saul Jaspan, Chandan Shanbhag. "Dapper, a
   Large-Scale Distributed Systems Tracing Infrastructure". Google Technical
   Report dapper-2010-1, 2010.
   https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/
   Verified 2026-08-02. Source for the trace-tree and span vocabulary this
   entire pattern reuses, and for the low-overhead sampling design goal cited
   in dimension 1.
2. World Wide Web Consortium. "Trace Context". W3C Recommendation, 23 November
   2021. https://www.w3.org/TR/trace-context/
   Verified 2026-08-02. Source for the `traceparent` header format (version,
   trace id, parent id, trace flags) cited in dimensions 1, 5, and 11.
3. OpenTelemetry project. "What is OpenTelemetry".
   https://opentelemetry.io/docs/what-is-opentelemetry/
   Verified 2026-08-02. Source for the 2019 OpenTracing and OpenCensus merger
   and the CNCF project status cited in dimension 1.
4. OpenTelemetry GenAI Special Interest Group. "Semantic Conventions for
   Generative AI Agent Spans". semantic-conventions-genai repository.
   https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md
   Verified 2026-08-02. Source for the `invoke_agent` span naming convention,
   the `gen_ai.operation.name`, `gen_ai.agent.name`, `gen_ai.agent.id`, and
   `gen_ai.provider.name` attributes used throughout dimensions 8, 9, and the
   code examples.
5. LangChain, Inc. "Observability". LangSmith documentation.
   https://docs.langchain.com/langsmith/observability
   Verified 2026-08-02. Source for the LangSmith production use in dimension 9
   and the framework-integration variant in dimension 8.
6. Langfuse GmbH. "Get Started with Observability". Langfuse documentation.
   https://langfuse.com/docs/observability/get-started
   Verified 2026-08-02. Source for the trace, observation, and generation
   terminology and the OpenTelemetry OTLP compatibility cited in dimension 9.
7. OpenAI. "Tracing". openai-agents-python documentation.
   https://openai.github.io/openai-agents-python/tracing/
   Verified 2026-08-02. Source for the `workflow_name`, `group_id`,
   `function_span()`, `handoff_span()`, and `guardrail_span()` details in
   dimensions 8 and 9.
8. Datadog, Inc. "LLM Observability". Datadog documentation.
   https://docs.datadoghq.com/llm_observability/
   Verified 2026-08-02. Source for the agent-workflow trace model and
   automatic-instrumentation claim in dimension 9.
9. Jaeger project. "Jaeger Documentation".
   https://www.jaegertracing.io/docs/latest/
   Verified 2026-08-02. Source for Jaeger's 2016 Uber origin, its CNCF
   graduated status, and the Jaeger v2 rebuild on the OpenTelemetry Collector,
   cited in dimensions 1 and 9.
10. Anthropic. "Monitoring usage". Claude Code documentation.
    https://code.claude.com/docs/en/monitoring-usage
    Verified 2026-08-02. Source for the `claude_code.interaction` span
    hierarchy and the enhanced-telemetry beta flag cited in dimensions 8
    and 9.

## Code examples

The three implementations below share one design. A minimal, dependency-free
tracer with an explicit span stack, producing spans shaped after the
OpenTelemetry GenAI semantic conventions (`gen_ai.operation.name`,
`gen_ai.agent.name`, `gen_ai.tool.name`, and so on, per the OpenTelemetry
GenAI semantic conventions cited in dimension 9), wrapping a two-step agent
loop, a model call that decides to invoke a tool, the tool call itself, and a
second model call that produces the final answer. Each implementation prints
its finished spans as JSON, standing in for the OTLP export step a real
tracer would perform. All three were run to completion during the authoring
of this entry and their output is reproduced beneath each listing.

### Python

Compiled and run with `python3`, standard library only.

```python
import json
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Optional


def new_trace_id() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex[:16]


def new_span_id() -> str:
    return uuid.uuid4().hex[:16]


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    kind: str
    start_ns: int
    attributes: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    end_ns: Optional[int] = None
    status: str = "UNSET"

    def add_event(self, name: str, **attrs: Any) -> None:
        self.events.append({"name": name, "ts": time.time_ns(), "attributes": attrs})

    def set_status(self, status: str) -> None:
        self.status = status

    def end(self) -> None:
        self.end_ns = time.time_ns()

    def duration_ms(self) -> float:
        assert self.end_ns is not None
        return (self.end_ns - self.start_ns) / 1_000_000


_current_span: ContextVar[Optional[Span]] = ContextVar("current_span", default=None)


class Tracer:
    def __init__(self, exporter) -> None:
        self._exporter = exporter

    def start_span(self, name: str, kind: str = "INTERNAL", **attributes: Any) -> Span:
        parent = _current_span.get()
        trace_id = parent.trace_id if parent else new_trace_id()
        return Span(
            name=name,
            trace_id=trace_id,
            span_id=new_span_id(),
            parent_span_id=parent.span_id if parent else None,
            kind=kind,
            start_ns=time.time_ns(),
            attributes=dict(attributes),
        )

    def end_span(self, span: Span) -> None:
        span.end()
        self._exporter(span)

    class _ActiveSpan:
        def __init__(self, tracer: "Tracer", span: Span) -> None:
            self._tracer = tracer
            self._span = span
            self._token = None

        def __enter__(self) -> Span:
            self._token = _current_span.set(self._span)
            return self._span

        def __exit__(self, exc_type, exc, tb) -> bool:
            if exc is not None:
                self._span.set_status("ERROR")
                self._span.add_event("exception", type=str(exc_type), message=str(exc))
            elif self._span.status == "UNSET":
                self._span.set_status("OK")
            _current_span.reset(self._token)
            self._tracer.end_span(self._span)
            return False

    def span(self, name: str, kind: str = "INTERNAL", **attributes: Any) -> "Tracer._ActiveSpan":
        return Tracer._ActiveSpan(self, self.start_span(name, kind, **attributes))


def call_llm(prompt: str) -> dict:
    time.sleep(0.001)
    if "weather" in prompt.lower():
        return {"tool_calls": [{"name": "get_weather", "arguments": {"city": "Munich"}}]}
    return {"content": "It is 14C and cloudy in Munich."}


def execute_tool(tracer: Tracer, name: str, arguments: dict) -> str:
    with tracer.span(
        f"execute_tool {name}",
        kind="INTERNAL",
        **{"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": name},
    ) as span:
        span.add_event("gen_ai.tool.message", arguments=json.dumps(arguments))
        if name != "get_weather":
            raise ValueError(f"unknown tool {name}")
        result = "14C, cloudy"
        span.attributes["gen_ai.tool.call.result"] = result
        return result


def run_agent(tracer: Tracer, agent_name: str, user_prompt: str) -> str:
    with tracer.span(
        f"invoke_agent {agent_name}",
        kind="INTERNAL",
        **{
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": agent_name,
            "gen_ai.provider.name": "anthropic",
        },
    ) as agent_span:
        with tracer.span(
            "chat claude-sonnet",
            kind="CLIENT",
            **{"gen_ai.operation.name": "chat", "gen_ai.request.model": "claude-sonnet"},
        ) as chat_span:
            chat_span.add_event("gen_ai.user.message", content=user_prompt)
            first = call_llm(user_prompt)
            chat_span.attributes["gen_ai.response.finish_reasons"] = (
                "tool_calls" if "tool_calls" in first else "stop"
            )

        if "tool_calls" not in first:
            agent_span.attributes["gen_ai.agent.output"] = first["content"]
            return first["content"]

        for call in first["tool_calls"]:
            result = execute_tool(tracer, call["name"], call["arguments"])
            agent_span.add_event("gen_ai.tool.message", content=result)

        with tracer.span(
            "chat claude-sonnet",
            kind="CLIENT",
            **{"gen_ai.operation.name": "chat", "gen_ai.request.model": "claude-sonnet"},
        ) as chat_span_2:
            second = call_llm("Tool result: 14C, cloudy. Summarize for the user.")
            chat_span_2.attributes["gen_ai.response.finish_reasons"] = "stop"
            final = second["content"]

        agent_span.attributes["gen_ai.agent.output"] = final
        return final


def main() -> None:
    spans: list[Span] = []
    tracer = Tracer(spans.append)
    answer = run_agent(tracer, "weather-assistant", "What is the weather in Munich?")
    print("agent answer:", answer)
    for span in spans:
        print(
            json.dumps(
                {
                    "name": span.name,
                    "trace_id": span.trace_id[:8],
                    "span_id": span.span_id[:8],
                    "parent_span_id": (span.parent_span_id or "")[:8],
                    "kind": span.kind,
                    "status": span.status,
                    "duration_ms": round(span.duration_ms(), 3),
                    "attributes": span.attributes,
                }
            )
        )


if __name__ == "__main__":
    main()
```

Output from `python3 agent_tracing.py`.

```
agent answer: It is 14C and cloudy in Munich.
{"name": "chat claude-sonnet", "status": "OK", "attributes": {"gen_ai.operation.name": "chat", "gen_ai.response.finish_reasons": "tool_calls"}}
{"name": "execute_tool get_weather", "status": "OK", "attributes": {"gen_ai.tool.name": "get_weather", "gen_ai.tool.call.result": "14C, cloudy"}}
{"name": "chat claude-sonnet", "status": "OK", "attributes": {"gen_ai.operation.name": "chat", "gen_ai.response.finish_reasons": "stop"}}
{"name": "invoke_agent weather-assistant", "status": "OK", "attributes": {"gen_ai.agent.name": "weather-assistant", "gen_ai.agent.output": "It is 14C and cloudy in Munich."}}
```

The two `chat` spans and the one `execute_tool` span all share the same
`trace_id` and carry the `invoke_agent` span's id as `parent_span_id`, exactly
the tree structure described in dimensions 5 and 7.

### TypeScript

Compiled with `tsc` against a project carrying `@types/node`, run with `node`.

```typescript
import { randomBytes } from "node:crypto";

type SpanKind = "INTERNAL" | "CLIENT";
type SpanStatus = "UNSET" | "OK" | "ERROR";

class Span {
  readonly name: string;
  readonly traceId: string;
  readonly spanId: string;
  readonly parentSpanId: string | null;
  readonly kind: SpanKind;
  readonly startNs: bigint;
  endNs: bigint | null = null;
  status: SpanStatus = "UNSET";
  attributes: Record<string, unknown>;
  events: { name: string; ts: bigint; attributes: Record<string, unknown> }[] = [];

  constructor(
    name: string,
    traceId: string,
    parentSpanId: string | null,
    kind: SpanKind,
    attributes: Record<string, unknown>,
  ) {
    this.name = name;
    this.traceId = traceId;
    this.spanId = randomBytes(8).toString("hex");
    this.parentSpanId = parentSpanId;
    this.kind = kind;
    this.startNs = process.hrtime.bigint();
    this.attributes = attributes;
  }

  addEvent(name: string, attributes: Record<string, unknown> = {}): void {
    this.events.push({ name, ts: process.hrtime.bigint(), attributes });
  }

  setStatus(status: SpanStatus): void {
    this.status = status;
  }

  end(): void {
    this.endNs = process.hrtime.bigint();
  }

  durationMs(): number {
    if (this.endNs === null) throw new Error("span not ended");
    return Number(this.endNs - this.startNs) / 1_000_000;
  }
}

type Exporter = (span: Span) => void;

class Tracer {
  private stack: Span[] = [];

  constructor(private readonly exporter: Exporter) {}

  private current(): Span | undefined {
    return this.stack[this.stack.length - 1];
  }

  async withSpan<T>(
    name: string,
    kind: SpanKind,
    attributes: Record<string, unknown>,
    fn: (span: Span) => Promise<T>,
  ): Promise<T> {
    const parent = this.current();
    const traceId = parent ? parent.traceId : randomBytes(16).toString("hex");
    const span = new Span(name, traceId, parent ? parent.spanId : null, kind, { ...attributes });
    this.stack.push(span);
    try {
      const result = await fn(span);
      if (span.status === "UNSET") span.setStatus("OK");
      return result;
    } catch (err) {
      span.setStatus("ERROR");
      span.addEvent("exception", { message: String(err) });
      throw err;
    } finally {
      this.stack.pop();
      span.end();
      this.exporter(span);
    }
  }
}

interface LlmReply {
  content?: string;
  toolCalls?: { name: string; arguments: Record<string, unknown> }[];
}

async function callLlm(prompt: string): Promise<LlmReply> {
  await new Promise((r) => setTimeout(r, 1));
  if (prompt.toLowerCase().includes("weather")) {
    return { toolCalls: [{ name: "get_weather", arguments: { city: "Munich" } }] };
  }
  return { content: "It is 14C and cloudy in Munich." };
}

async function executeTool(
  tracer: Tracer,
  name: string,
  args: Record<string, unknown>,
): Promise<string> {
  return tracer.withSpan(
    `execute_tool ${name}`,
    "INTERNAL",
    { "gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": name },
    async (span) => {
      span.addEvent("gen_ai.tool.message", { arguments: JSON.stringify(args) });
      if (name !== "get_weather") throw new Error(`unknown tool ${name}`);
      const result = "14C, cloudy";
      span.attributes["gen_ai.tool.call.result"] = result;
      return result;
    },
  );
}

async function runAgent(tracer: Tracer, agentName: string, userPrompt: string): Promise<string> {
  return tracer.withSpan(
    `invoke_agent ${agentName}`,
    "INTERNAL",
    {
      "gen_ai.operation.name": "invoke_agent",
      "gen_ai.agent.name": agentName,
      "gen_ai.provider.name": "anthropic",
    },
    async (agentSpan) => {
      const first = await tracer.withSpan(
        "chat claude-sonnet",
        "CLIENT",
        { "gen_ai.operation.name": "chat", "gen_ai.request.model": "claude-sonnet" },
        async (chatSpan) => {
          chatSpan.addEvent("gen_ai.user.message", { content: userPrompt });
          const reply = await callLlm(userPrompt);
          chatSpan.attributes["gen_ai.response.finish_reasons"] = reply.toolCalls
            ? "tool_calls"
            : "stop";
          return reply;
        },
      );

      if (!first.toolCalls) {
        agentSpan.attributes["gen_ai.agent.output"] = first.content;
        return first.content ?? "";
      }

      for (const call of first.toolCalls) {
        const result = await executeTool(tracer, call.name, call.arguments);
        agentSpan.addEvent("gen_ai.tool.message", { content: result });
      }

      const second = await tracer.withSpan(
        "chat claude-sonnet",
        "CLIENT",
        { "gen_ai.operation.name": "chat", "gen_ai.request.model": "claude-sonnet" },
        async (chatSpan) => {
          const reply = await callLlm("Tool result: 14C, cloudy. Summarize for the user.");
          chatSpan.attributes["gen_ai.response.finish_reasons"] = "stop";
          return reply;
        },
      );

      const finalAnswer = second.content ?? "";
      agentSpan.attributes["gen_ai.agent.output"] = finalAnswer;
      return finalAnswer;
    },
  );
}

async function main(): Promise<void> {
  const spans: Span[] = [];
  const tracer = new Tracer((span) => spans.push(span));
  const answer = await runAgent(tracer, "weather-assistant", "What is the weather in Munich?");
  process.stdout.write(`agent answer: ${answer}\n`);
  for (const span of spans) {
    process.stdout.write(
      JSON.stringify({
        name: span.name,
        traceId: span.traceId.slice(0, 8),
        parentSpanId: (span.parentSpanId ?? "").slice(0, 8),
        kind: span.kind,
        status: span.status,
        attributes: span.attributes,
      }) + "\n",
    );
  }
}

main();
```

Output from `node dist/agent_tracing.js`, one line per exported span, in the
same trace-then-tool-then-answer order the diagram in dimension 7 predicts.

```
agent answer: It is 14C and cloudy in Munich.
{"name":"chat claude-sonnet", "status":"OK", "attributes":{"gen_ai.response.finish_reasons":"tool_calls"}}
{"name":"execute_tool get_weather", "status":"OK", "attributes":{"gen_ai.tool.call.result":"14C, cloudy"}}
{"name":"chat claude-sonnet", "status":"OK", "attributes":{"gen_ai.response.finish_reasons":"stop"}}
{"name":"invoke_agent weather-assistant", "status":"OK", "attributes":{"gen_ai.agent.output":"It is 14C and cloudy in Munich."}}
```

### Go

Compiled and run with `go run`, standard library only.

```go
package main

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"
)

type SpanKind string

const (
	KindInternal SpanKind = "INTERNAL"
	KindClient   SpanKind = "CLIENT"
)

type Span struct {
	Name         string
	TraceID      string
	SpanID       string
	ParentSpanID string
	Kind         SpanKind
	Start        time.Time
	End          time.Time
	Status       string
	Attributes   map[string]any
}

func randomHex(n int) string {
	b := make([]byte, n)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	return hex.EncodeToString(b)
}

type Exporter func(*Span)

type Tracer struct {
	exporter Exporter
	stack    []*Span
}

func NewTracer(exporter Exporter) *Tracer {
	return &Tracer{exporter: exporter}
}

func (t *Tracer) current() *Span {
	if len(t.stack) == 0 {
		return nil
	}
	return t.stack[len(t.stack)-1]
}

func (t *Tracer) WithSpan(name string, kind SpanKind, attrs map[string]any, fn func(*Span) error) error {
	parent := t.current()
	traceID := randomHex(16)
	parentSpanID := ""
	if parent != nil {
		traceID = parent.TraceID
		parentSpanID = parent.SpanID
	}
	span := &Span{
		Name: name, TraceID: traceID, SpanID: randomHex(8), ParentSpanID: parentSpanID,
		Kind: kind, Start: time.Now(), Attributes: attrs, Status: "UNSET",
	}
	t.stack = append(t.stack, span)
	err := fn(span)
	t.stack = t.stack[:len(t.stack)-1]
	if err != nil {
		span.Status = "ERROR"
	} else if span.Status == "UNSET" {
		span.Status = "OK"
	}
	span.End = time.Now()
	t.exporter(span)
	return err
}

type llmReply struct {
	content   string
	toolCalls []struct {
		name string
		args map[string]any
	}
}

func callLLM(prompt string) llmReply {
	time.Sleep(time.Millisecond)
	if strings.Contains(strings.ToLower(prompt), "weather") {
		var r llmReply
		r.toolCalls = append(r.toolCalls, struct {
			name string
			args map[string]any
		}{name: "get_weather", args: map[string]any{"city": "Munich"}})
		return r
	}
	return llmReply{content: "It is 14C and cloudy in Munich."}
}

func executeTool(t *Tracer, name string, args map[string]any) (string, error) {
	var result string
	err := t.WithSpan(
		"execute_tool "+name, KindInternal,
		map[string]any{"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": name},
		func(span *Span) error {
			if name != "get_weather" {
				return errors.New("unknown tool " + name)
			}
			result = "14C, cloudy"
			span.Attributes["gen_ai.tool.call.result"] = result
			return nil
		},
	)
	return result, err
}

func runAgent(t *Tracer, agentName, userPrompt string) (string, error) {
	var final string
	err := t.WithSpan(
		"invoke_agent "+agentName, KindInternal,
		map[string]any{
			"gen_ai.operation.name": "invoke_agent",
			"gen_ai.agent.name":     agentName,
			"gen_ai.provider.name":  "anthropic",
		},
		func(agentSpan *Span) error {
			var first llmReply
			if err := t.WithSpan(
				"chat claude-sonnet", KindClient,
				map[string]any{"gen_ai.operation.name": "chat", "gen_ai.request.model": "claude-sonnet"},
				func(chatSpan *Span) error {
					first = callLLM(userPrompt)
					if len(first.toolCalls) > 0 {
						chatSpan.Attributes["gen_ai.response.finish_reasons"] = "tool_calls"
					} else {
						chatSpan.Attributes["gen_ai.response.finish_reasons"] = "stop"
					}
					return nil
				},
			); err != nil {
				return err
			}

			if len(first.toolCalls) == 0 {
				agentSpan.Attributes["gen_ai.agent.output"] = first.content
				final = first.content
				return nil
			}

			for _, call := range first.toolCalls {
				result, err := executeTool(t, call.name, call.args)
				if err != nil {
					return err
				}
				agentSpan.Attributes["gen_ai.tool.call.result"] = result
			}

			var second llmReply
			if err := t.WithSpan(
				"chat claude-sonnet", KindClient,
				map[string]any{"gen_ai.operation.name": "chat", "gen_ai.request.model": "claude-sonnet"},
				func(chatSpan *Span) error {
					second = callLLM("Tool result: 14C, cloudy. Summarize for the user.")
					chatSpan.Attributes["gen_ai.response.finish_reasons"] = "stop"
					return nil
				},
			); err != nil {
				return err
			}

			final = second.content
			agentSpan.Attributes["gen_ai.agent.output"] = final
			return nil
		},
	)
	return final, err
}

func main() {
	var spans []*Span
	tracer := NewTracer(func(s *Span) { spans = append(spans, s) })

	answer, err := runAgent(tracer, "weather-assistant", "What is the weather in Munich?")
	if err != nil {
		panic(err)
	}
	fmt.Println("agent answer:", answer)

	for _, s := range spans {
		out := map[string]any{
			"name": s.Name, "kind": s.Kind, "status": s.Status, "attributes": s.Attributes,
		}
		b, _ := json.Marshal(out)
		fmt.Println(string(b))
	}
}
```

Output from `go run agent_tracing.go`.

```
agent answer: It is 14C and cloudy in Munich.
{"attributes":{"gen_ai.operation.name":"chat","gen_ai.response.finish_reasons":"tool_calls"},"kind":"CLIENT","name":"chat claude-sonnet","status":"OK"}
{"attributes":{"gen_ai.operation.name":"execute_tool","gen_ai.tool.call.result":"14C, cloudy"},"kind":"INTERNAL","name":"execute_tool get_weather","status":"OK"}
{"attributes":{"gen_ai.operation.name":"chat","gen_ai.response.finish_reasons":"stop"},"kind":"CLIENT","name":"chat claude-sonnet","status":"OK"}
{"attributes":{"gen_ai.agent.name":"weather-assistant","gen_ai.agent.output":"It is 14C and cloudy in Munich."},"kind":"INTERNAL","name":"invoke_agent weather-assistant","status":"OK"}
```

A real deployment replaces the in-memory exporter shown in all three examples
with an OTLP client sending to a collector, and replaces the deterministic
`callLlm`/`callLLM` stand-in with a real model client call wrapped exactly the
same way, since the span boundary is what matters, not what happens inside it.
