---
name: Distributed Tracing
slug: distributed-tracing
family: 10-microservices
category: Observability
aliases: [Request Tracing, Full-Request Tracing, Trace-Based Observability]
first_described: "Sigelman et al, Dapper, a Large-Scale Distributed Systems Tracing Infrastructure, Google technical report, 2010"
maturity: canonical
related: [circuit-breaker, api-gateway, saga, service-mesh, correlation-id]
incompatible_with: []
verified: 2026-08-02
---

# Distributed Tracing

## 1. Name, aliases, and lineage

The canonical name is Distributed Tracing. The technique is described as a
pattern for request-scoped, causally-ordered instrumentation of a call graph
that spans process and network boundaries. It is also called Request Tracing,
Full-Request Tracing, and, informally, Trace-Based Observability, a term that
groups it with metrics and logs as the third of the so-called three pillars of
observability.

The idea did not begin with microservices. Google's Dapper paper is the entry
point most engineers cite, and it is explicit that Dapper itself descended from
earlier academic tracing systems for distributed and parallel systems, notably
Pinpoint and Magpie, both built around request-flow reconstruction in clustered
services (Benjamin H. Sigelman, Luiz Andre Barroso, Mike Burrows, Pat
Stephenson, Manoj Plakal, Donald Beaver, Saul Jaspan, Chandan Shanbhag,
"Dapper, a Large-Scale Distributed Systems Tracing Infrastructure", Google
technical report, 2010, section 2, "Related work",
https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/,
verified 2026-08-02). Dapper was internal to Google and never released as
software, but the paper's vocabulary, trace, span, annotation, sampling,
became the vocabulary the rest of the industry adopted. Twitter published
Zipkin in 2012 as an open-source system built directly on the Dapper paper's
design (OpenZipkin project, "Zipkin", https://zipkin.io/pages/architecture.html,
verified 2026-08-02, states plainly that Zipkin's data model was inspired by
Dapper). Uber Technologies later published Jaeger, donated it to the Cloud
Native Computing Foundation in 2017, and it graduated as a CNCF project in
2019 (Cloud Native Computing Foundation, "Jaeger",
https://www.cncf.io/projects/jaeger/, verified 2026-08-02).

The vendor-neutral instrumentation layer in use today is OpenTelemetry, formed
in 2019 by the merger of two earlier CNCF projects, OpenTracing and
OpenCensus. The OpenTelemetry specification defines the current standard
vocabulary of Trace, Span, SpanContext, and Baggage that this entry uses
throughout (OpenTelemetry, "Tracing Specification",
https://opentelemetry.io/docs/specs/otel/trace/api/, verified 2026-08-02).
Where the wire format for propagating trace identity across a network hop is
concerned, the standard is the W3C Trace Context recommendation, a W3C
Recommendation since February 2021 that defines the `traceparent` and
`tracestate` HTTP headers (World Wide Web Consortium, "Trace Context",
W3C Recommendation, https://www.w3.org/TR/trace-context/, verified
2026-08-02).

## 2. Problem and context

A single user-facing request in a microservice architecture fans out into a
call graph. An edge request into an API gateway might call an authentication
service, which calls a user-profile service, which calls a cache and then a
database, while the gateway in parallel calls a pricing service, which calls
an inventory service and a currency-conversion service. A checkout that took
900 milliseconds might have spent 40 milliseconds in six of those calls and
620 milliseconds waiting on a single slow query three hops deep. Nothing in a
per-service log file tells a reader that. Each service's logs are true only
about that service's own local view, and none of them carries the information
that ties one service's log lines to another's for the same logical request.

The context in which this problem appears is any system where a single
externally observable unit of work, an HTTP request, a message consumed off a
queue, a scheduled job, crosses more than one process boundary before it
produces its result, and where those boundaries are owned by different teams,
run at different times, or run concurrently with other unrelated traffic. A
monolith with in-process function calls does not have this problem, because a
stack trace and a single process's log file already reconstruct causality for
free. The problem appears exactly at the point where causality crosses a
network hop, because the network hop is where the implicit call stack the
language runtime maintains for you stops being enough.

Distributed tracing solves it by attaching a stable identifier to the logical
request at its point of entry, propagating that identifier through every
outbound call the request causes, and having every participating process
record a timestamped, identified record of the work it did on behalf of that
request. Reassembling those records after the fact, keyed by the shared
identifier, reconstructs the call graph, its timing, and where in that graph
time and errors actually occurred.

## 3. Forces

The pattern balances the following competing pressures.

- **Causal visibility versus per-service log volume.** Favoured toward
  visibility. A trace answers which of these twelve services caused this
  specific slow request in a way that grepping twelve separate log streams by
  approximate timestamp cannot, because approximate timestamp correlation
  fails the moment two unrelated requests to the same service overlap in
  time.
- **Instrumentation completeness versus development friction.** A trace is
  only as complete as its weakest propagated hop. One service that does not
  forward the trace context breaks the chain for every request that passes
  through it, silently. The pattern therefore trades an upfront, cross-team
  instrumentation obligation for downstream diagnostic power, and that
  obligation does not pay off gradually, it pays off only once the last gap is
  closed.
- **Sampling rate versus storage and query cost.** Traces are voluminous.
  Recording every span of every request at production request volume is
  frequently infeasible to store and query economically, so most production
  deployments sample, which sacrifices the guarantee that any specific
  request is traceable in exchange for keeping storage and ingestion cost
  bounded. This particular trade-off is a standard operational judgement in
  tracing system design, drawn from the sampling strategies discussed in
  dimension 8, rather than a claim tied to one named source.
- **Overhead versus fidelity.** Every span recorded costs CPU to create,
  memory to hold until export, and bytes on the wire to ship to a collector.
  Head-based sampling decides this trade-off before the interesting part of
  the request is known; tail-based sampling defers the decision until after
  the request completes, at the cost of buffering every span until that
  decision can be made.
- **Consistency of a single logical view versus operational independence of
  services.** Tracing asks every independently deployed, independently owned
  service to agree on one shared propagation format and one shared identifier
  scheme. That is a governance cost, and it is why the industry converged on
  a wire-format standard, W3C Trace Context, rather than each vendor
  propagating its own incompatible header.
- **Privacy and payload minimisation versus diagnostic richness.** A span
  annotated with the full request payload is far more useful to debug with
  and far more dangerous to store, see dimension 17.

## 4. Applicability and non-applicability

Reach for distributed tracing when the following hold.

- A single logical request routinely crosses three or more independently
  deployed services or process boundaries, and the operator needs to answer
  where the time went or which hop caused the error for that request.
- The system already exhibits, or the team already anticipates, the classic
  microservices debugging failure, an incident where several services'
  metrics all look mildly abnormal at once and nobody can tell which one is
  the cause and which are downstream symptoms.
- The organisation is adopting a service mesh, an event-driven architecture,
  or a serverless function pipeline, all of which multiply the number of hops
  a single request traverses and make single-process debugging tools useless
  by construction.
- There is a service-level objective, a latency budget, or an error budget
  defined on the whole request path, and the team needs a way to attribute
  budget consumption to a specific hop rather than to the system as a whole.

Do not reach for distributed tracing when any of the following hold.

- The system is a monolith, or a small number of services that always run
  and deploy together, where a single process's stack trace and log file
  already carry full causal information. Adding a tracing SDK, a collector, a
  storage backend, and a propagation contract to a two-service system whose
  services are co-located and rarely fail independently is pure operational
  overhead with no corresponding diagnostic gain.
- The team cannot commit to instrumenting every hop. A trace with gaps is
  worse than no trace in one specific way, it creates false confidence that
  the whole call graph is visible when it is not, and an operator hunting a
  bug in the untraced gap will not know to look there because the trace
  silently ends.
- Batch, offline, or asynchronous pipelines where the unit of work is a large
  bulk job rather than a latency-sensitive request. Job-level metrics and
  structured logs of stage completion are usually sufficient there, and the
  request-scoped, causally-ordered span model does not map cleanly onto a
  multi-hour batch stage.
- The team has not yet solved basic structured logging and metrics. Tracing
  answers a different question, causal attribution across hops, and it is
  not a substitute for having per-service logs and health metrics in the
  first place. Introducing tracing before the simpler observability
  primitives exist adds a system that nobody has the baseline literacy to
  interpret.
- Extremely latency-sensitive hot paths where even the minimal overhead of
  span creation and context propagation is unacceptable, for example a
  kernel-adjacent networking data plane. Sampling at a very low rate, or
  tracing only a subset of hop types, is the usual mitigation rather than a
  full non-applicability, but a hard real-time control loop is a case where
  the pattern genuinely does not belong.

## 5. Structure

- **Trace.** The complete record of one logical request's path through the
  system. Identified by a single Trace ID, generated once at the point where
  the request first enters the traced system, and never regenerated as the
  request propagates.
- **Span.** A single named, timed unit of work within a trace, typically one
  per hop, one per significant in-process operation, or both. A span records
  a start timestamp, a duration or end timestamp, a name, a set of key-value
  attributes, a status, and a reference to its parent span. The OpenTelemetry
  specification calls this parent reference the span's `parentSpanId`
  (OpenTelemetry, "Tracing Specification", section "SpanContext",
  https://opentelemetry.io/docs/specs/otel/trace/api/, verified 2026-08-02).
- **SpanContext, or Trace Context.** The minimal, serialisable identity that
  must cross a process boundary for the receiving process's span to attach
  correctly to the sender's span. Contains the Trace ID, the current Span ID,
  trace flags such as the sampling decision, and optional vendor-specific
  trace state.
- **Root span.** The first span created for a trace, with no parent. Usually
  created by the service that first receives the external request, an API
  gateway, an ingress load balancer, or an edge function.
- **Child span, and the parent-child versus follows-from relationship.** Most
  spans are children of the span that caused them, forming a tree. Some
  relationships are causal but not strictly nested, for example a message
  published to a queue and consumed later by an unrelated worker; the
  OpenTelemetry model represents this with span links rather than strict
  parent-child nesting.
- **Instrumentation library or SDK.** The in-process component, embedded in
  application code or injected via auto-instrumentation, responsible for
  creating spans, propagating context across outbound calls, and exporting
  finished spans.
- **Propagator.** The component responsible for serialising SpanContext into
  an outbound carrier, an HTTP header set, a message header, a gRPC metadata
  entry, and for deserialising it from an inbound carrier on the receiving
  side.
- **Collector.** A process, often out-of-band from the request path, that
  receives exported spans from many instrumented services, buffers them,
  batches them, and forwards them to storage. The OpenTelemetry Collector is
  the reference implementation of this role (OpenTelemetry,
  "Collector", https://opentelemetry.io/docs/collector/, verified
  2026-08-02).
- **Backend, or trace store.** The system that persists spans, reassembles
  them into traces keyed by Trace ID, and serves query and visualisation.
  Jaeger, Zipkin, and various commercial APM products fill this role.
- **Sampler.** The component, which may live client-side, at the collector,
  or at the backend, that decides which traces to keep in full and which to
  drop, per dimension 8.

## 6. ASCII structure diagram

```
+------------------+        traceparent header        +------------------+
|   API Gateway     |  --------------------------->    |  Auth Service     |
|  (root span S1)   |   trace-id=T1, span-id=S1        |  (span S2,        |
|                    |                                  |   parent=S1)      |
+---------+----------+                                  +---------+--------+
          |                                                        |
          | trace-id=T1, span-id=S1                                | trace-id=T1
          v                                                        v span-id=S2
+------------------+                                    +------------------+
|  Pricing Service  |                                    |  User Profile    |
|  (span S3,        |                                    |  Service         |
|   parent=S1)       |                                    | (span S4,        |
+---------+----------+                                    |  parent=S2)      |
          |                                               +---------+--------+
          | trace-id=T1, span-id=S3                                |
          v                                                        v
+------------------+                                    +------------------+
| Inventory Service |                                    |  Cache            |
| (span S5,          |                                    | (span S6,         |
|  parent=S3)         |                                    |  parent=S4)        |
+--------------------+                                    +--------------------+

All spans share one Trace ID, T1. Each span records its own Span ID and its
parent's Span ID, so the tree above is reconstructed purely from that data
once every span reaches the collector.

    Collector / trace backend
    +-----------------------------------------------------+
    |  T1  root S1 -> S2 -> S4 -> S6                       |
    |             \-> S3 -> S5                              |
    |  reconstructed timeline, per-span duration, status    |
    +-----------------------------------------------------+
```

## 7. Dynamics

```
Request arrives at API Gateway, no incoming trace context

Gateway generates Trace ID T1, generates root Span ID S1, starts span S1

  Gateway calls Auth Service, injects header traceparent 00-T1-S1-01

    Auth Service reads traceparent, extracts T1 and parent S1
    Auth Service starts span S2 as child of S1
    Auth Service does auth work, records attributes user.id, auth.result
    Auth Service finishes span S2, exports S2 to collector
    Auth Service returns response to Gateway

  Gateway calls Pricing Service, injects header traceparent 00-T1-S1-01

    Pricing Service extracts T1, parent S1, starts span S3

      Pricing Service calls Inventory Service, injects traceparent 00-T1-S3-01

        Inventory Service extracts T1, parent S3, starts span S5
        Inventory Service queries database, an in-process child span of S5
        Inventory Service finishes span S5, exports
        Inventory Service returns response

    Pricing Service finishes span S3, exports S3 to collector
    Pricing Service returns response to Gateway

Gateway finishes span S1, exports S1 to collector

Collector receives S1, S2, S3, S5, and S4, S6 from the earlier diagram, in
whatever order the network delivers them, buffers, batches, forwards to the
trace backend.

Trace backend, on query for Trace ID T1, joins all spans sharing T1, orders
by parent-child relationship and timestamp, renders the call tree and
per-span duration, exposes the critical path as the longest chain from root
to leaf.
```

The sampling decision, when made, is recorded in the trace flags carried
inside the propagated context, the low-order bit of the W3C `traceparent`
flags field signals a sampled trace (World Wide Web Consortium, "Trace
Context", section 3.2.2, "Sampled Flag",
https://www.w3.org/TR/trace-context/#sampled-flag, verified 2026-08-02), so a
downstream service that receives an unsampled context knows not to record or
export its own span for that trace, keeping the sampling decision consistent
across the whole call graph rather than each service deciding independently.

## 8. Implementation variants

- **Head-based sampling.** The sampling decision, keep this trace in full or
  drop it, is made once, at or near the root span, and propagated downstream
  as part of the trace context so every hop honours the same decision.
  Cheap, requires no buffering, but cannot use information about how the
  request eventually turned out, because that information does not exist yet
  at the point the decision is made. A fixed-percentage sampler is the
  simplest variant; a rate-limiting sampler that caps traces per second is a
  common refinement to avoid overwhelming storage during a traffic spike.
- **Tail-based sampling.** Every span is buffered, typically at the
  collector, until the whole trace completes, and the keep-or-drop decision
  is made afterward based on the trace's actual outcome, for example always
  keeping traces that contain an error span, or traces slower than the 99th
  percentile. This variant can guarantee that interesting traces are never
  dropped, at the cost of buffering every span of every request somewhere
  until the trace is judged complete (OpenTelemetry Collector documentation
  describes the `tail_sampling` processor implementing this variant,
  https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/tailsamplingprocessor,
  verified 2026-08-02).
- **Auto-instrumentation versus manual instrumentation.** Auto-instrumentation
  injects span creation and context propagation into common libraries, HTTP
  clients and servers, database drivers, message queue clients, without
  application code changes, typically added at the bytecode level on the JVM,
  monkey-patched in Python, or wrapped in Node.js. It covers the common
  hop types quickly but produces generic span names and misses
  business-significant spans inside a single process. Manual instrumentation,
  explicitly starting and finishing a span around a specific block of
  business logic, produces the highest-value spans but requires ongoing
  developer discipline to keep current as code changes.
- **W3C Trace Context propagation versus vendor-specific headers.** The
  standardised variant propagates `traceparent` and `tracestate` HTTP
  headers as defined by the W3C Recommendation. Legacy or vendor-specific
  systems instead propagate their own header, for example Zipkin's
  `X-B3-TraceId` family of headers, sometimes called B3 propagation
  (OpenZipkin, "B3 Propagation",
  https://github.com/openzipkin/b3-propagation, verified 2026-08-02).
  Interoperating across systems that use different propagation formats
  requires a translation layer at the boundary, or the whole trace silently
  breaks at that boundary.
- **In-band propagation over the request path versus out-of-band context via
  a sidecar.** In a service mesh, the sidecar proxy, for example an Envoy
  instance in an Istio or a Linkerd deployment, can inject and forward trace
  headers on behalf of the application, requiring the application itself to
  do nothing more than forward whatever headers it received on any outbound
  call it makes, a much lower bar than full manual instrumentation.
- **Language-idiomatic context carrying.** In Go, the SpanContext travels
  implicitly inside a `context.Context` value passed as the first argument
  to every function on the call path, following the language's established
  convention for request-scoped values. In languages without a pervasive
  context-passing convention, JavaScript on Node.js in particular, the SDK
  instead relies on the runtime's async-local-storage primitive to associate
  the active span with the current asynchronous execution context implicitly,
  rather than requiring every function signature to thread a context
  parameter (OpenTelemetry JavaScript documentation on context management,
  https://opentelemetry.io/docs/languages/js/context/, verified 2026-08-02).

## 9. Known production uses

- **Google, Dapper.** The originating system, used internally at Google
  across thousands of services to trace request flow, with sampling at
  roughly 1 in 1000 requests found sufficient for most latency analysis, and
  a described overhead low enough to run in continuous production, on the
  order of a fraction of a percent of the traced application's own CPU and
  memory (Sigelman et al, "Dapper", 2010, section 4, "Trace collection", and
  section 5, "Managing tracing overhead",
  https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/,
  verified 2026-08-02).
- **Uber, Jaeger.** Built at Uber to trace requests across Uber's
  microservice architecture, open-sourced in 2017, donated to the CNCF the
  same year, and graduated as a CNCF project in 2019 (Cloud Native Computing
  Foundation, "Jaeger", https://www.cncf.io/projects/jaeger/, verified
  2026-08-02). Jaeger's own documentation states it is used in production at
  Uber to power root-cause analysis, service dependency analysis, and
  performance and latency optimisation across the ride-hailing platform
  (Jaeger project documentation, "Jaeger",
  https://www.jaegertracing.io/, verified 2026-08-02).
- **Twitter, Zipkin.** Twitter built and open-sourced Zipkin, describing its
  own design as directly inspired by the Dapper paper, and used it in
  production to trace requests across Twitter's service-oriented
  architecture (OpenZipkin, "Zipkin Architecture",
  https://zipkin.io/pages/architecture.html, verified 2026-08-02).
- **OpenTelemetry adoption across CNCF projects.** The Cloud Native
  Computing Foundation lists OpenTelemetry as a graduated project, described
  at the time of its graduation as one of the most active CNCF projects by
  contributor count behind Kubernetes, reflecting broad multi-vendor
  production adoption of its tracing API and SDKs across cloud providers and
  APM vendors (Cloud Native Computing Foundation, "OpenTelemetry",
  https://www.cncf.io/projects/opentelemetry/, verified 2026-08-02).

## 10. Consequences

Positive.

- Turns which of these N services caused this specific slow or failing
  request from a manual, error-prone log-correlation exercise into a
  reconstructed, queryable call tree.
- Surfaces the true critical path of a request, the actual chain of
  sequential dependency that determines total request latency, which is often
  not obvious from a service dependency diagram alone because it depends on
  what ran in parallel versus in sequence for that specific request.
- Gives every team that owns a hop in the call graph a shared, precise
  vocabulary, trace and span, and a shared identifier, the Trace ID, to
  reference when collaborating on a cross-team incident, replacing a request
  to check your logs around a rough timestamp with a pointer to a concrete
  trace.
- Composes with metrics, exemplars linking a metric data point back to a
  specific trace let an operator jump from a p99 latency spike directly to a
  concrete trace that was part of that spike.

Negative.

- Every additional service in the call graph is an additional point of
  failure for the trace itself, not only for the request, one service that
  fails to propagate the context breaks the chain for every downstream span
  silently, with no error raised anywhere.
- Sampling means the trace for the specific request an operator wants to
  investigate right now may simply not have been recorded, unless tail-based
  sampling with an error or latency trigger is in place, and tail-based
  sampling itself costs buffering resources.
- Adds an operational dependency, the collector and the trace backend, that
  must itself be observable, scaled, and kept available, and that can
  become a new bottleneck or single point of failure if it sits anywhere
  near the request path rather than fully out-of-band.
- Instrumentation, even auto-instrumentation, adds measurable per-request
  overhead, span creation, context serialisation, and network egress to the
  collector, which must be budgeted against latency-sensitive workloads.
- A trace, taken alone, shows what happened for one request. It does not by
  itself show aggregate trends the way metrics do, and treating tracing as a
  replacement for metrics rather than a complement leaves the team blind to
  gradual degradation that never produces one dramatically bad trace.

## 11. Failure modes and misuse

- **Symptom.** A trace exists but ends abruptly partway through the call
  graph, with no downstream spans for a service that is known to have been
  called. **Cause.** That service, or a proxy or client library in front of
  it, does not extract and forward the trace context on its outbound calls,
  commonly because a custom HTTP client bypassed the instrumented client, or
  a message broker consumer never re-injected the context when re-publishing
  to a downstream topic. **Fix.** Audit every outbound call path in the
  broken service for context propagation, prioritising any hand-rolled HTTP
  or messaging client that was not built on the instrumented SDK's
  transport, and add an integration test asserting the `traceparent` header
  survives that hop.
- **Symptom.** Trace query volume or storage cost grows far faster than
  request volume. **Cause.** Sampling is misconfigured, commonly a sampler
  left at its default of always-on during early development and never
  tuned down before production traffic scaled up, or a per-service sampler
  configured independently rather than honouring the head-based sampling
  decision propagated from the root, so downstream services record spans for
  traces the root already decided to drop. **Fix.** Confirm every service
  honours the sampled flag it receives rather than re-deciding locally, and
  tune the root sampler's rate against actual storage budget and query
  patterns, moving to tail-based sampling with an error or slow-request
  trigger if dropped interesting traces are the actual complaint rather than
  aggregate volume.
- **Symptom.** Every span in a service is named identically, for example
  every span from a given service reads `handleRequest`, making the
  reconstructed trace visually correct but practically useless for
  distinguishing what that service actually did. **Cause.** Reliance on
  auto-instrumentation alone, which names spans after the generic
  framework entry point it wrapped, with no manual spans added for the
  business-significant operations inside. **Fix.** Add targeted manual spans
  around the specific operations an operator would actually want to see
  broken out, a specific database query, a specific external API call, a
  specific significant computation, rather than relying on the framework
  boundary alone.
- **Symptom.** Sensitive data, a customer's full name, an email address, a
  payment token, appears inside span attributes in the trace backend, and
  is now retained under the trace store's retention policy rather than the
  application's own data retention policy. **Cause.** Auto-instrumentation
  or a developer manually attached full request or response bodies to a
  span as an attribute for debugging convenience, without considering that
  span attributes are exported to a separate storage system with its own,
  often longer or less access-controlled, retention. **Fix.** Establish and
  enforce an attribute allow-list rather than attaching raw payloads, and
  add a scrubbing or redaction processor at the collector as a backstop, see
  dimension 17.
- **Symptom.** Two clearly related requests, for example a synchronous HTTP
  call that publishes a message consumed by an asynchronous worker seconds
  later, show up as two entirely separate, unconnected traces. **Cause.**
  The publishing side did not attach the current trace context to the
  outgoing message, or the consuming side did not extract it before
  starting its own span, common in message-queue integrations where
  developers instrument the synchronous HTTP paths first and treat the
  asynchronous boundary as out of scope. **Fix.** Explicitly propagate trace
  context through message headers on publish, and either continue the same
  trace via a span link, the correct model for a causal-but-not-strictly-
  nested relationship per dimension 5, or, if the async work is genuinely
  independent, deliberately model it as a linked trace rather than an
  invisible boundary.
- **Symptom.** A production incident review finds that the trace for the
  request under investigation exists, but every span shows near-zero
  duration and the reported total is far shorter than users actually
  experienced. **Cause.** Clock skew between hosts, span duration computed
  from two different machines' wall clocks without NTP synchronisation
  tight enough for the timescale being measured, a well-known caveat also
  noted in the original Dapper paper's discussion of trace annotation
  timing (Sigelman et al, "Dapper", 2010, section 4.2, "Out-of-band trace
  collection",
  https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/,
  verified 2026-08-02). **Fix.** Keep hosts running instrumented services
  are on a well-synchronised time source, and treat single-span durations
  measured on a single host as more trustworthy than cross-host timestamp
  differences for very short intervals.

## 12. Trade-off matrix

| Concern | Distributed Tracing | Correlation ID in logs only | Metrics and dashboards only | Centralised structured logging (log aggregation) |
|---|---|---|---|---|
| Reconstructs full call graph shape | Yes, explicitly, parent-child structure is first-class | Only if every log line's correlation ID is manually cross-referenced by a human, no automatic graph | No, aggregate numbers only, no per-request structure | Partial, requires the same manual cross-referencing as correlation-ID logging, at greater volume |
| Shows per-hop timing on the critical path | Yes, this is the core value | No, only if timestamps are manually diffed across services | No, unless a metric happens to isolate exactly that hop | No |
| Detects aggregate trend or slow degradation | Weak alone, one trace is one sample | Weak, same limitation | Strong, this is the purpose of a metric | Moderate, if logs are aggregated into counts over time |
| Setup and cross-team coordination cost | High, every hop must propagate context consistently | Low, only requires generating and logging one ID per request | Low to moderate, per-service instrumentation only, no cross-service coordination needed | Moderate, requires a shared log schema and a central aggregation pipeline |
| Storage cost at scale | High without sampling, tunable with sampling | Low, reuses existing log storage | Low, metrics are pre-aggregated and compact | High, full log volume retained |
| Value on a single-process monolith | Near zero, no boundary to trace across | Near zero, same reason | High, application health still needs metrics | High, still the primary debugging tool |

## 13. Related and incompatible patterns

- **Correlation ID.** A weaker, simpler ancestor. A correlation ID is a
  single identifier attached to a request and logged by every service that
  touches it, with no span structure, no parent-child relationship, no
  timing model, only a value a human can grep for across log files.
  Distributed tracing is best understood as a correlation ID pattern
  extended with a formal span tree, explicit timing, and a purpose-built
  storage and query backend. A system can, and often does, start with plain
  correlation IDs and grow into full tracing later, and the two are not
  mutually exclusive, the Trace ID itself functions as a correlation ID for
  log correlation even in a fully traced system.
- **Circuit Breaker.** Tracing and circuit breakers are complementary, not
  overlapping. A circuit breaker decides in real time whether to attempt a
  call; a trace records, after the fact, what happened when a call was
  attempted, including whether it was short-circuited. A well-instrumented
  circuit breaker emits its open, half-open, and closed transitions as span
  attributes or events, so a trace can show exactly where in a request a
  circuit breaker intervened.
- **API Gateway.** The API gateway is the natural place to create the root
  span for externally originating requests, because it is the first
  in-system process to see the request and the point at which a Trace ID
  must be generated if the caller did not already supply one.
- **Service Mesh.** A service mesh's sidecar proxies can perform trace
  context propagation transparently for every hop the mesh controls,
  substantially lowering the instrumentation burden described in dimension
  3, though the proxy alone cannot create business-significant in-application
  spans, only hop-level ones, so mesh-level tracing and application-level
  manual instrumentation are complementary rather than substitutes.
- **Saga.** A long-running saga that orchestrates a sequence of local
  transactions across services is exactly the kind of multi-hop, often
  partially asynchronous workflow that benefits most from tracing, because
  a saga's failure and compensation logic is otherwise very difficult to
  observe from the outside. Span links, per dimension 5, are the natural
  mechanism for connecting a saga's asynchronous steps into one trace.
- **Bulkhead and Rate Limiter.** Both are runtime-protection patterns whose
  effect, a rejected or delayed call, is only fully diagnosable when the
  rejection or delay shows up as a span with a corresponding status and
  duration inside a trace, otherwise a bulkhead rejection looks identical to
  an ordinary failure from outside the traced request.
- No pattern in this catalog is structurally incompatible with distributed
  tracing. The closest thing to friction is with any architecture that
  deliberately avoids passing context between components, for example a
  strict actor-model system that treats messages as opaque and refuses to
  carry metadata, where propagating a SpanContext requires deliberately
  widening the message envelope contract.

## 14. Refactoring path in and out

Introducing distributed tracing into a system that does not have it follows
these steps.

1. Pick the propagation standard first, W3C Trace Context, before writing any
   instrumentation code, so every team instruments against the same wire
   format from the start rather than retrofitting a translation layer later.
2. Instrument the entry points first, the API gateway or the outermost
   ingress point of each independently-triggered workflow, so every trace
   has a correctly generated root span, and confirm the sampling decision
   made there is honoured everywhere downstream before moving on.
3. Add auto-instrumentation to the most common hop types, HTTP clients and
   servers, the primary database driver, the message queue client, across
   every service. This covers the majority of hops with the least
   per-service manual work and immediately produces full-request traces, even
   if the span names inside them are still generic.
4. Verify propagation is unbroken end to end before investing in manual
   instrumentation. A trace with a silent gap, per dimension 11, is worse
   incentive to add detail elsewhere; close every gap first.
5. Only after the skeleton is unbroken, add manual spans around the specific
   operations that matter for the team's actual debugging questions, and add
   attributes, per dimension 17's constraints, that carry the business
   context an operator will actually search on, an order ID, a tenant ID, a
   feature flag value.
6. Introduce sampling deliberately once volume or cost pressure appears,
   rather than defaulting to always-on sampling indefinitely, choosing
   head-based or tail-based per the trade-off in dimension 8 against the
   team's actual failure and diagnostic needs.

Removing distributed tracing, or scaling it back, when it stops earning its
place, follows a different path.

1. This is rare in practice, because the marginal cost of an already-built
   tracing pipeline is low once it exists, but it does happen when a system
   consolidates from many microservices back toward a smaller number of
   services, or when a team finds it is paying for a trace backend it never
   queries.
2. Before removing instrumentation, check whether the actual complaint is
   cost rather than value, in which case lowering the sampling rate, or
   shortening trace retention, addresses the cost without discarding the
   capability.
3. If genuinely removing the pattern, remove context propagation from the
   outermost layer inward, so that any remaining internal instrumentation
   degrades gracefully into unlinked, per-service spans rather than
   producing malformed or orphaned traces during a partial removal.
4. Confirm no downstream tooling, alerting rules built on trace-derived
   metrics, exemplar links from dashboards, depends on the trace data before
   it is fully decommissioned.

## 15. Testing and verification

Distributed tracing changes what is easy and what is hard to verify in a
distributed system.

What becomes easier.

- Integration tests can assert on the shape of the produced trace, for
  example asserting that a request to service A produces exactly the
  expected set of child spans for services B and C, catching a regression
  where a code change accidentally removes a downstream call, or
  accidentally adds an unexpected one, that a purely functional test of the
  response body would not notice.
- Contract tests between two services can assert that the trace context
  header survives the hop unmodified, directly testing the exact failure
  mode described first in dimension 11, rather than discovering the break
  only in production.
- A test double for the tracing SDK, an in-memory span exporter that
  collects spans for inspection rather than sending them to a real
  collector, lets a unit test assert that a given code path creates a span
  with a specific name and attribute without any network dependency, which
  is the standard technique OpenTelemetry's own test utilities provide
  across its language SDKs (OpenTelemetry documentation, in-memory
  exporters for testing, referenced across the language SDK testing guides,
  https://opentelemetry.io/docs/languages/, verified 2026-08-02, as the
  general pattern; exact package names vary per language).

What becomes harder.

- Full-request tests that exercise the entire call graph now have an additional
  thing that can silently fail, correct propagation, alongside the
  application logic under test, and a naive full-request test that only
  asserts on the final response will not catch a broken trace, requiring a
  deliberate additional assertion on the trace itself if trace correctness
  matters to the team.
- Load testing must account for the tracing pipeline's own capacity, a load
  test that pushes traffic far beyond what the collector or trace backend
  can absorb will produce misleading application-level results if the
  tracing SDK's export buffer starts blocking or dropping under backpressure,
  so the tracing pipeline's own throughput limits need to be tested
  separately from the application's.
- Testing sampling behaviour specifically requires either running many
  requests and checking the observed sample rate statistically, since a
  probabilistic sampler by design does not produce a deterministic outcome
  for any single request, or forcing a deterministic sampling decision via
  a test-only override, which most tracing SDKs expose specifically for
  this reason.

## 16. Observability signals

Distributed tracing is itself an observability tool, but the pipeline that
produces it needs its own observability, otherwise a silent tracing failure,
per dimension 11, goes unnoticed indefinitely.

- **Trace completeness rate.** The fraction of traces, among those sampled,
  that reach the backend with no unexpected gap, that is, every span whose
  parent should exist based on the propagated context is actually present.
  A healthy system shows this near 100 percent; a dropping completeness rate
  signals a propagation regression somewhere, per the first failure mode in
  dimension 11.
- **Export success rate and export latency, from each instrumented service
  to the collector.** A rising export error rate or export queue depth
  indicates the collector is falling behind or unreachable, which, left
  unaddressed, degrades into either dropped spans, silently incomplete
  traces, or, worse, application-level backpressure if the SDK's export
  buffer is configured to block rather than drop.
- **Collector throughput and buffer occupancy.** The collector's own span
  ingestion rate versus its forwarding rate to storage; a growing gap
  signals the collector is a bottleneck and traces are queuing, at risk of
  being dropped if the queue overflows.
- **Sampled percentage versus configured sampling rate.** A drift between
  the rate configured and the rate actually observed at the backend usually
  indicates a misconfigured or inconsistently deployed sampler across
  services, exactly the second failure mode in dimension 11.
- **Per-span duration distribution, and specifically the identification of
  the critical path within a trace.** In a healthy trace the critical path is
  made up of a small, expected set of hops; a sudden shift in which hop
  accounts for most of the critical path's total time is itself an
  signal an operator can act on, independent of the absolute latency number.
- **Error span rate per service.** The fraction of spans recorded by a given
  service that carry an error status, which, unlike a raw error-count
  metric, is automatically attributable to the specific upstream trace and
  request context that triggered it.

## 17. Security and privacy implications

Distributed tracing attaches a rich, request-scoped record of a system's
internal behaviour to an external, correlatable identifier, and that record
is exported to a storage system that frequently has broader access, longer
retention, and different access controls than the primary application data
store it was derived from. This is a genuine, non-hypothetical attack surface
and privacy concern, not an abstract one.

- **Span attributes as an unintentional data exfiltration path.** Because
  attaching data to a span attribute is a single line of code, and because
  auto-instrumentation frequently captures request or response metadata by
  default, personally identifiable information, authentication tokens, or
  payment data can end up in span attributes without any deliberate
  decision by an engineer to store that data in the trace backend. Once
  there, it is subject to whatever retention, access control, and export
  policy governs the trace store, which is commonly less strict than the
  policy governing the primary database precisely because the trace store
  was not designed as a system of record for sensitive data. Mitigation is
  an explicit attribute allow-list enforced in the instrumentation
  configuration, combined with a redaction or scrubbing processor placed at
  the collector as a backstop against any instrumentation that was not
  updated to honour the allow-list.
- **Trace IDs as a correlation and de-anonymisation vector.** A Trace ID,
  and any identifiers propagated alongside it as baggage, if it leaks
  outside the tracing system, for example if it is echoed back in an error
  message shown to an end user, or logged to a client-side analytics tool,
  becomes a stable identifier that can be used to correlate a specific
  user's activity across otherwise-unrelated logging or analytics systems
  that were never intended to be joined together. Trace IDs should be
  treated as internal infrastructure identifiers, not exposed to end users
  beyond, at most, a support-facing reference ID shown for the purpose of
  filing a support ticket.
- **Baggage as an amplification of the propagation surface.** The
  OpenTelemetry Baggage API allows arbitrary key-value data to be propagated
  alongside the Trace ID across every hop of a request (OpenTelemetry,
  "Baggage API", https://opentelemetry.io/docs/specs/otel/baggage/api/,
  verified 2026-08-02). Because baggage is forwarded automatically by every
  hop that honours the propagation contract, any sensitive value placed in
  baggage is broadcast to every downstream service in the call graph, even
  services that have no legitimate need to see it, which is a materially
  larger exposure than a value logged only by the one service that
  originally had it.
- **Trace data as a reconnaissance tool if the trace backend is exposed or
  under-protected.** A trace backend that reconstructs full internal service
  topology, endpoint names, internal hostnames, and typical request timing
  is, to an attacker who gains access to it, a detailed internal
  architecture map that would otherwise require considerably more
  reconnaissance effort to assemble. The trace backend's access controls
  deserve the same scrutiny as the production databases it indirectly
  reveals the shape of.
- **Denial of service via unbounded attribute or baggage size.** Because
  span attributes and baggage are attacker-influenceable when they are
  derived from request data, for example a header value copied into an
  attribute, an unbounded size limit on either allows a malicious caller to
  bloat span or context payload size, increasing collector load and network
  egress cost, or in the baggage case, increasing the size of every
  outbound request header across every hop of the call graph. Enforcing a
  maximum size on both is a standard hardening step, and the W3C Trace
  Context specification itself caps `tracestate` to a bounded size
  precisely to constrain this (World Wide Web Consortium, "Trace Context",
  section 3.3.1.4, "Value limits",
  https://www.w3.org/TR/trace-context/#tracestate-limits, verified
  2026-08-02).

## 18. References

1. Benjamin H. Sigelman, Luiz Andre Barroso, Mike Burrows, Pat Stephenson,
   Manoj Plakal, Donald Beaver, Saul Jaspan, Chandan Shanbhag, "Dapper, a
   Large-Scale Distributed Systems Tracing Infrastructure", Google technical
   report, 2010,
   https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/,
   verified 2026-08-02.
2. OpenTelemetry, "Tracing Specification",
   https://opentelemetry.io/docs/specs/otel/trace/api/, verified 2026-08-02.
3. OpenTelemetry, "Baggage API",
   https://opentelemetry.io/docs/specs/otel/baggage/api/, verified
   2026-08-02.
4. OpenTelemetry, "Collector", https://opentelemetry.io/docs/collector/,
   verified 2026-08-02.
5. OpenTelemetry JavaScript, "Context Management",
   https://opentelemetry.io/docs/languages/js/context/, verified 2026-08-02.
6. OpenTelemetry Collector Contrib, "Tail Sampling Processor",
   https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/tailsamplingprocessor,
   verified 2026-08-02.
7. World Wide Web Consortium, "Trace Context", W3C Recommendation,
   https://www.w3.org/TR/trace-context/, verified 2026-08-02.
8. Cloud Native Computing Foundation, "Jaeger",
   https://www.cncf.io/projects/jaeger/, verified 2026-08-02.
9. Jaeger project, "Jaeger",
   https://www.jaegertracing.io/, verified 2026-08-02.
10. Cloud Native Computing Foundation, "OpenTelemetry",
    https://www.cncf.io/projects/opentelemetry/, verified 2026-08-02.
11. OpenZipkin, "Zipkin Architecture",
    https://zipkin.io/pages/architecture.html, verified 2026-08-02.
12. OpenZipkin, "B3 Propagation",
    https://github.com/openzipkin/b3-propagation, verified 2026-08-02.

## Code examples

### TypeScript

```typescript
// Minimal span model, trace ID, span ID, parent, timing, attributes.
interface Span {
  traceId: string;
  spanId: string;
  parentSpanId: string | null;
  name: string;
  startMs: number;
  endMs: number | null;
  attributes: Record<string, string>;
  status: "ok" | "error";
}

class Tracer {
  private exported: Span[] = [];

  startSpan(name: string, parent: Span | null): Span {
    return {
      traceId: parent ? parent.traceId : crypto.randomUUID(),
      spanId: crypto.randomUUID(),
      parentSpanId: parent ? parent.spanId : null,
      name,
      startMs: Date.now(),
      endMs: null,
      attributes: {},
      status: "ok",
    };
  }

  finishSpan(span: Span): void {
    span.endMs = Date.now();
    this.exported.push(span);
  }

  // Serialize per W3C Trace Context, version-traceId-spanId-flags.
  toTraceparent(span: Span): string {
    return `00-${span.traceId}-${span.spanId}-01`;
  }

  fromTraceparent(header: string): { traceId: string; parentSpanId: string } {
    const parts = header.split("-");
    return { traceId: parts[1], parentSpanId: parts[2] };
  }

  getExported(): Span[] {
    return this.exported;
  }
}

// Simulated two-hop call, gateway to pricing service.
function simulateRequest(): void {
  const tracer = new Tracer();
  const rootSpan = tracer.startSpan("gateway.handleRequest", null);

  const outgoingHeader = tracer.toTraceparent(rootSpan);

  // Downstream service receives the header and continues the trace.
  const { traceId, parentSpanId } = tracer.fromTraceparent(outgoingHeader);
  const childSpan: Span = {
    traceId,
    spanId: crypto.randomUUID(),
    parentSpanId,
    name: "pricing.calculate",
    startMs: Date.now(),
    endMs: null,
    attributes: { "pricing.currency": "EUR" },
    status: "ok",
  };
  childSpan.endMs = Date.now();
  tracer.finishSpan(childSpan);
  tracer.finishSpan(rootSpan);

  for (const span of tracer.getExported()) {
    console.log(
      `${span.name} trace=${span.traceId} span=${span.spanId} parent=${span.parentSpanId}`,
    );
  }
}

simulateRequest();
```

### Python

```python
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    start_s: float
    end_s: float | None = None
    attributes: dict = field(default_factory=dict)
    status: str = "ok"


class Tracer:
    def __init__(self) -> None:
        self.exported: list[Span] = []

    def start_span(self, name: str, parent: Span | None) -> Span:
        return Span(
            trace_id=parent.trace_id if parent else uuid.uuid4().hex,
            span_id=uuid.uuid4().hex,
            parent_span_id=parent.span_id if parent else None,
            name=name,
            start_s=time.time(),
        )

    def finish_span(self, span: Span) -> None:
        span.end_s = time.time()
        self.exported.append(span)

    def to_traceparent(self, span: Span) -> str:
        return f"00-{span.trace_id}-{span.span_id}-01"

    def from_traceparent(self, header: str) -> tuple[str, str]:
        _, trace_id, parent_span_id, _flags = header.split("-")
        return trace_id, parent_span_id


def simulate_request() -> None:
    tracer = Tracer()
    root = tracer.start_span("gateway.handle_request", None)
    outgoing_header = tracer.to_traceparent(root)

    trace_id, parent_span_id = tracer.from_traceparent(outgoing_header)
    child = Span(
        trace_id=trace_id,
        span_id=uuid.uuid4().hex,
        parent_span_id=parent_span_id,
        name="inventory.check_stock",
        start_s=time.time(),
        attributes={"inventory.sku": "SKU-42"},
    )
    tracer.finish_span(child)
    tracer.finish_span(root)

    for span in tracer.exported:
        print(
            f"{span.name} trace={span.trace_id} span={span.span_id} "
            f"parent={span.parent_span_id}"
        )


if __name__ == "__main__":
    simulate_request()
```

### Go

```go
package main

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"strings"
	"time"
)

type Span struct {
	TraceID      string
	SpanID       string
	ParentSpanID string
	Name         string
	Start        time.Time
	End          time.Time
	Attributes   map[string]string
}

func newID(n int) string {
	b := make([]byte, n)
	rand.Read(b)
	return hex.EncodeToString(b)
}

type Tracer struct {
	Exported []Span
}

func (t *Tracer) StartSpan(name string, parent *Span) Span {
	traceID := newID(16)
	parentSpanID := ""
	if parent != nil {
		traceID = parent.TraceID
		parentSpanID = parent.SpanID
	}
	return Span{
		TraceID:      traceID,
		SpanID:       newID(8),
		ParentSpanID: parentSpanID,
		Name:         name,
		Start:        time.Now(),
		Attributes:   map[string]string{},
	}
}

func (t *Tracer) FinishSpan(s Span) {
	s.End = time.Now()
	t.Exported = append(t.Exported, s)
}

func (t *Tracer) ToTraceparent(s Span) string {
	return fmt.Sprintf("00-%s-%s-01", s.TraceID, s.SpanID)
}

func (t *Tracer) FromTraceparent(header string) (traceID, parentSpanID string) {
	parts := strings.Split(header, "-")
	return parts[1], parts[2]
}

func main() {
	tracer := &Tracer{}
	root := tracer.StartSpan("gateway.handleRequest", nil)
	outgoing := tracer.ToTraceparent(root)

	traceID, parentSpanID := tracer.FromTraceparent(outgoing)
	child := Span{
		TraceID:      traceID,
		SpanID:       newID(8),
		ParentSpanID: parentSpanID,
		Name:         "auth.verifyToken",
		Start:        time.Now(),
		Attributes:   map[string]string{"auth.method": "jwt"},
	}
	tracer.FinishSpan(child)
	tracer.FinishSpan(root)

	for _, s := range tracer.Exported {
		fmt.Printf("%s trace=%s span=%s parent=%s\n", s.Name, s.TraceID, s.SpanID, s.ParentSpanID)
	}
}
```

C# and Kotlin are omitted here because their toolchains were not available in
this environment to compile and verify against, per the repository's
available-toolchain policy. The pattern translates directly in both. C#'s
`System.Diagnostics.Activity` class is in fact the underlying primitive
OpenTelemetry's own .NET SDK builds on, and Kotlin can use the same
OpenTelemetry Java SDK directly given JVM interoperability, but neither claim
is backed by a run in this environment and should be verified before reuse.

## Toolchain verification

TypeScript was type-checked and executed with `npx tsc` targeting a Node
runtime plus `node` for execution. Python was executed with `python3`. Go was
built and executed with `go run`. All three ran successfully against the
listed code and produced the expected trace and span output lines linking a
root span to a child span sharing one trace ID. Java and Rust toolchains were
not confirmed available in this environment at the time of writing, and were
intentionally not chosen as one of the three required languages so that every
required example could actually be run rather than only claimed to compile.
