---
name: Application Metrics
slug: application-metrics
family: 10-microservices
category: Observability
aliases: [Metrics Instrumentation, Service Metrics, Operational Metrics]
first_described: "Richardson 2018 (microservices.io pattern catalog)"
maturity: canonical
related: [health-check-api, log-aggregation, distributed-tracing, circuit-breaker, service-mesh, api-gateway]
incompatible_with: []
verified: 2026-08-02
---

# Application Metrics

## 1. Name, aliases, and lineage

The canonical name in the microservices pattern literature is Application
Metrics. Chris Richardson catalogs it as an Observability pattern at
`https://microservices.io/patterns/observability/application-metrics.html`, defined as
instrumenting a service to collect statistics about its operations and
reporting them, in an aggregated form, to a metrics service that supports
reporting and alerting (Richardson, microservices.io, Application Metrics
pattern page, verified 2026-08-02). Richardson places the pattern in his 2018
book alongside Health Check API, Log Aggregation, Distributed Tracing, and
Exception Tracking as the observability quartet plus one, the group of patterns
a team adopts once a system has more than a handful of service instances and a
person can no longer simply SSH into a box and read a log file (Chris Richardson,
*Microservices Patterns*, Manning, 2018, chapter 11, "Developing production
ready services").

The pattern is also known, informally and interchangeably depending on the
community, as Metrics Instrumentation (used across the OpenTelemetry and
Prometheus toolchains to describe the act of adding metric-emitting code to
an application) and Operational Metrics (used in site reliability
engineering literature to distinguish this class of signal from business
metrics such as revenue, which are a related but separate practice). None of
these aliases change the shape of the pattern, and all three describe a
service that produces small, cheap, numeric time series about its own
behavior and hands them to something outside the service that can store,
aggregate, graph, and alert on them.

The pattern has no single named inventor in the way a Gang of Four pattern
does. It crystallized as monitoring practice moved from single-host tools
(sar, vmstat, a cron job that emailed a report) to the StatsD protocol
released by Etsy in 2011, described in the Etsy Code as Craft blog post
"Measure Anything, Measure Everything" from 2011, as still cited by the
current statsd project README at `https://github.com/statsd/statsd` (verified
2026-08-02), and then to the pull-based model Prometheus introduced in 2012
at SoundCloud (Prometheus documentation, "Overview",
`https://prometheus.io/docs/introduction/overview/`, verified 2026-08-02).
Richardson's pattern name is the one this repository treats as canonical
because it is the name used specifically in a microservices architecture
context, as opposed to the wider and older discipline of systems monitoring,
from which this pattern borrows its mechanics but not its scope.

## 2. Problem and context

A monolith has one process. When something is slow or wrong, an engineer
attaches a profiler, reads a thread dump, or greps one log file, and the whole
picture of the system's behavior is in that one place. A microservices
architecture removes that single vantage point. The same business
transaction now crosses a dozen independently deployed, independently scaled,
independently failing processes, and the question "is the order service slow,
or is it the payment service it calls, or the database connection pool
underneath it" no longer has an answer that lives in one process's memory.

The concrete situation looks like this in a team that has recently split a
monolith. A deploy goes out. Ten minutes later, checkout latency climbs. The
on-call engineer opens a dashboard and it shows nothing, because nobody wired
the new service to send any numbers anywhere. The engineer instead SSHes into
three container hosts, reads raw log lines, and manually counts how many of
the last hundred requests took over a second, by eye, in a terminal. This is
survivable once. In an organization running fifty services and a hundred
container instances, it is not survivable at all, because the number of
places to look grows with the number of services, while the amount of time
available to find the cause during an incident does not.

The forces that create the need are structural, not incidental. A request
that spans several services produces partial signals in each one, latency in
service A, a raised error rate in service B, saturation of a connection pool
in service C, and none of those signals is visible from outside that one
process unless the process itself measures and reports it. A container
orchestrator can restart a crashed process, but it cannot tell an operator
that a process is alive, accepting requests, and returning wrong answers
slowly, because "alive" and "healthy" are different facts and only the
process itself can compute the second one cheaply. Auto-scaling decisions
need a number to scale on, request rate, queue depth, CPU, and that number
has to come from inside the fleet, continuously, or the orchestrator scales
blind. Capacity planning, SLO tracking, and root cause analysis after an
incident all depend on having a historical record of these numbers, not only
their current value, because the question during a postmortem is almost
always "what did this look like an hour before it broke", which no live
inspection can answer retroactively.

Application Metrics is the pattern that answers all four needs with one
mechanism, every service instruments itself to produce small numeric
measurements about counts, durations, and current levels, and exports those
measurements, on a schedule or on request, to a system built to store,
aggregate across instances, graph, and alert on them. The pattern does not
specify which metrics to collect or which backend to use, only the shape of
the solution, self-instrumentation plus centralized aggregation, as distinct
from centralized log parsing (Log Aggregation) or per-request causal tracing
(Distributed Tracing), which solve adjacent but different problems.

## 3. Forces

**Overhead versus resolution.** A metric that samples every request in full
detail costs CPU and memory proportional to request volume. A metric that
samples nothing costs nothing and tells nothing. The pattern lives on the
tension between wanting a fine-grained picture and wanting the instrumentation
itself to be invisible in a profiler. Counters and gauges are cheap, an atomic
increment or a volatile write. Histograms and summaries that track quantiles
are more expensive, because computing an accurate p99 requires either storing
individual observations or maintaining a more elaborate sketch data
structure. Richardson's own definition names low runtime overhead as an
explicit constraint on any acceptable implementation (Richardson,
microservices.io, Application Metrics, verified 2026-08-02).

**Push versus pull.** In a push model, the service decides when to send data
and to whom, which the pattern's own description names as one of its two
supported aggregation approaches (Richardson, microservices.io, Application
Metrics, verified 2026-08-02). Push couples the service to knowledge of where
the metrics backend lives and creates back-pressure risk if the backend is
slow or down. In a pull model, exemplified by Prometheus, the service exposes
a stateless HTTP endpoint and the aggregation system decides when and how
often to scrape it (Prometheus documentation, "Overview",
`https://prometheus.io/docs/introduction/overview/`, verified 2026-08-02). Pull
decouples the service from backend location and availability at the cost of
requiring service discovery on the aggregator's side and losing very
short-lived processes that die between scrapes, which is why Prometheus
itself ships a Pushgateway for exactly that case.

**Series count versus queryability.** A metric labeled only by its name
answers one question. A metric labeled by service, instance, route, status
code, and customer tier answers many questions but multiplies the number of
distinct time series the backend must store, a problem metrics-tooling
documentation commonly discusses under the label-explosion heading. A high
number of distinct label-value combinations makes ad hoc queries powerful
and makes the storage engine expensive or, past a threshold, unable to keep
up at all. This is the central operability force in the pattern, and it is
why nearly every metrics system draws a hard or soft line against labeling a
metric with something unbounded, such as a raw user ID or a full URL with a
query string.

**Coupling to a vendor versus coupling to an API.** A service can call a
specific backend's client library directly, or it can call a vendor-neutral
facade and let a pluggable exporter translate at the boundary. Direct coupling
is simpler to write and harder to change later, while a facade, such as
Micrometer for the JVM or the OpenTelemetry metrics API, adds one layer of
indirection in exchange for the ability to swap Prometheus for Datadog
without touching business code (Micrometer documentation, "Micrometer
Concepts", `https://docs.micrometer.io/micrometer/reference/concepts.html`, verified
2026-08-02; OpenTelemetry documentation, "Metrics",
`https://opentelemetry.io/docs/concepts/signals/metrics/`, verified 2026-08-02).

**Cognitive load on the team.** Every metric added is a metric someone has to
know exists, name consistently, and eventually delete when it stops mattering.
A team that instruments everything produces a dashboard nobody can read. A
team that instruments nothing produces an incident nobody can debug. The
pattern favors the second failure over the first, because the cost of adding
a metric later is lower than the cost of an outage with no data, but the
forces genuinely pull against each other and there is no setting that removes
the tension.

## 4. Applicability and non-applicability

Reach for Application Metrics when.

- The system is deployed as more than one independently scaled or
  independently deployed process, so that a single process's internal state is
  no longer sufficient to answer "is the system healthy."
- Auto-scaling, capacity planning, or SLO-based alerting depends on a
  continuously updated numeric signal rather than a point-in-time check.
- The team needs to answer "was this always slow or did it recently get slow" for
  a specific window in the past, which requires a stored time series, not only
  a live snapshot.
- The cost of an undetected regression (a slow endpoint, a growing error rate,
  a saturating connection pool) is higher than the cost of instrumenting the
  code path that could regress.
- The organization already runs, or is willing to run, a metrics aggregation
  backend (self-hosted Prometheus, a managed SaaS such as Datadog or New
  Relic, or a cloud-native option such as Amazon CloudWatch), because
  Application Metrics without a place to send the data is instrumentation with
  no destination.

Do NOT reach for Application Metrics, or do not reach for it as the primary
tool, when.

- The system is a single monolithic process with a small, well-known number
  of instances, where a profiler, an APM agent, or simple log inspection
  already answers the operational questions the team actually asks. Adding a
  full metrics pipeline here is process for its own sake.
- The question is "what happened to this one specific request," rather than
  "what is the aggregate behavior of this endpoint." That question belongs to
  Distributed Tracing, which preserves per-request causal structure that a
  metric, being an aggregate by construction, discards the moment it is
  recorded.
- The signal needed is a business or product metric with strict correctness
  and auditability requirements, such as revenue recognized or units shipped.
  Application Metrics backends are built for approximate, high-volume,
  best-effort telemetry and most accept dropped samples under load, and a
  financial figure belongs in a system of record, not a metrics time series
  database, even though the two are sometimes visualized on the same
  dashboard.
- The team has no operational capacity to run or pay for an aggregation
  backend and no near-term plan to acquire one. Emitting metrics nobody
  collects is pure overhead with none of the pattern's benefit, and the
  correct first step in that situation is Log Aggregation, which many teams
  already have from day one because logs are a byproduct of writing code
  rather than a deliberate instrumentation decision.
- The metric under consideration would be labeled by an effectively unbounded
  dimension, such as a raw request ID, a session token, or free-text user
  input. That data belongs in a trace span or a log line, both of which are
  built to hold per-event data with many distinct values, never in a metric label.
- The service is so short-lived, a batch job that runs and exits in
  milliseconds, that a pull-based scrape interval will structurally miss it.
  In that case a push model with an intermediary gateway, or event-based
  logging, fits better than a scraped metric.

## 5. Structure

- **Instrumented service.** The application process that owns the business
  logic and, incidentally, records measurements about its own behavior at the
  points that matter, request entry and exit, calls to downstream
  dependencies, queue depths, cache hit rates, and any domain-specific counter
  the team decides is worth tracking. It is the only participant with direct
  knowledge of what a given number means.
- **Metrics library or facade.** An in-process component, linked into the
  service, that provides the primitive metric types (counter, gauge,
  histogram, sometimes a summary), gives them thread-safe or otherwise
  concurrency-safe update operations, and either exposes them for pull-based
  collection or pushes them out. Micrometer on the JVM and the
  `prometheus/client_golang` and `prom-client` libraries on Go and Node.js are
  concrete examples of this role. It never decides what the numbers mean, only
  how they are recorded and shipped.
- **Metric.** The unit of measurement itself, always carrying a name, a
  numeric value, a type that constrains how the value can change, and usually
  a set of key-value labels (also called dimensions or tags) that let one
  metric name represent many related time series, such as `http_requests_total`
  broken down by `route` and `status_code`.
- **Collector or exporter endpoint.** The interface between the instrumented
  service and the outside world. In the pull model this is an HTTP endpoint,
  conventionally `/metrics`, that returns the current value of every
  registered metric in a text or binary exposition format when scraped. In
  the push model this is a client that periodically sends a batch of metric
  values to a receiving service, such as a StatsD daemon or an OpenTelemetry
  Collector.
- **Aggregation and storage service.** The external system, running outside
  every individual service instance, that pulls or receives metrics from many
  service instances, stores them as time series, and lets an operator query
  and combine them. Prometheus, Amazon CloudWatch, and Datadog's metrics
  backend all fill this role. This is the component that turns per-instance
  numbers into a fleet-wide picture.
- **Dashboard and alerting layer.** A consumer of the aggregation service's
  query interface that renders time series as graphs for humans and evaluates
  alerting rules against the same data for machines. Grafana querying
  Prometheus, or CloudWatch Alarms querying CloudWatch metrics, are examples.
  This participant is often a separate tool from the aggregation service, and
  the pattern does not require them to be the same product.

## 6. ASCII structure diagram

```
+-----------------------------------------------------------+
|                    Service Instance A                      |
|                                                             |
|  +-------------------+     +---------------------------+   |
|  | Business logic      | -->| Metrics library / facade    | |
|  | (request handlers,  |    | (Counter, Gauge, Histogram) | |
|  |  downstream calls)  |    +--------------+---------------+
|  +-------------------+                    |                |
|                                            v                |
|                              +---------------------------+  |
|                              |  /metrics exporter endpoint | |
|                              +--------------+---------------+
+---------------------------------------------|----------------+
                                               | (scrape / push)
                                               v
+-----------------------------------------------------------+
|                    Service Instance B                      |
|                     (same shape as A)                       |
+---------------------------------------------|---------------+
                                               |
                                               v
                    +----------------------------------+
                    |   Aggregation / storage service   |
                    |   (Prometheus, CloudWatch, ...)   |
                    +-----------------+------------------+
                                      |
                     +----------------+-----------------+
                     v                                  v
          +--------------------+             +--------------------+
          | Dashboard (Grafana) |             | Alerting rules      |
          +--------------------+             +--------------------+
```

## 7. Dynamics

```
Push model (StatsD-style)

  Business logic     Metrics facade        StatsD/OTel Collector       Backend
       |                    |                        |                    |
       |--record event----->|                        |                    |
       |                    |--UDP/TCP send---------->|                    |
       |                    |  (fire and forget)      |--flush batch------>|
       |                    |                        |                    |
       (request continues immediately, no wait on send)

Pull model (Prometheus-style)

  Business logic     Metrics registry          Exporter HTTP handler     Prometheus
       |                    |                        |                       |
       |--record event----->| (in-memory update)     |                       |
       |                    |                        |<--GET /metrics--------|
       |                    |<--read current values--|                       |
       |                    |                        |--text exposition----->|
       |                    |                        |                       |
       |                    |                        |    (repeats every scrape_interval,
       |                    |                        |     e.g. every 15s, independent
       |                    |                        |     of request traffic)
```

In the pull model the exporter endpoint is stateless and synchronous from the
scraper's point of view, and the aggregator initiates every collection, and a
service that is unreachable simply produces a gap in its time series rather
than an error the application code has to handle. In the push model the
service initiates every send and must decide, usually by simply dropping the
send, what happens when the receiving side is slow or unavailable, because
blocking business logic on a metrics send would invert the pattern's own
low-overhead constraint.

## 8. Implementation variants

- **StatsD-style UDP push.** The service fires a fixed-format UDP packet per
  event (`metric_name`, value, type) at a local StatsD agent, which batches and
  forwards to a backend. UDP is chosen specifically because a dropped packet
  never blocks or errors the caller, trading perfect accuracy for zero
  application-visible failure mode (Etsy Code as Craft, "Measure Anything,
  Measure Everything", 2011, referenced by `https://github.com/statsd/statsd`,
  verified 2026-08-02).
- **Prometheus client library, pull-based exposition.** The service links a
  client library that maintains metric state in memory and serves it over
  HTTP in the Prometheus text exposition format on a `/metrics` route. This
  is the dominant variant in Kubernetes-native stacks because the scrape
  target list is derived directly from service discovery (Prometheus
  documentation, "Overview", verified 2026-08-02).
- **Vendor-neutral facade with pluggable registry.** Micrometer on the JVM,
  or the OpenTelemetry Metrics API on any supported language, sits between
  application code and the concrete backend. The application calls a plain
  increment method against the facade's interface, and a `MeterRegistry` or
  `MeterProvider` implementation, chosen at wiring time, decides whether that
  call ultimately becomes a Prometheus scrape value, a CloudWatch metric
  data point, or a Datadog StatsD packet (Micrometer documentation,
  "Micrometer Concepts", verified 2026-08-02; OpenTelemetry documentation,
  "Metrics", verified 2026-08-02).
- **Sidecar or agent-based collection.** Instead of the application process
  serving its own `/metrics` endpoint, a sidecar container (in the service
  mesh sense) or a host-level agent (Datadog Agent, CloudWatch Agent) either
  scrapes the application's local endpoint and forwards it, or receives
  StatsD packets on localhost and forwards them, decoupling the shipping
  concern from the application container entirely.
- **Push gateway for short-lived jobs.** For a batch job or cron task too
  short-lived to be scraped, the job pushes its final metric values to an
  intermediary gateway process once, at exit, and the gateway holds those
  values so the normal pull-based scraper can collect them on its own
  schedule. Prometheus documents this explicitly as the exception to its
  usual pull model, not a general-purpose push path (Prometheus
  documentation, "Overview", `https://prometheus.io/docs/introduction/overview/`,
  verified 2026-08-02).
- **Language-idiomatic shape.** In Go, metrics are typically package-level
  variables registered once at process start, because Go has no framework
  dependency-injection convention to lean on. In Java and Kotlin, metrics are
  usually injected via a `MeterRegistry` bean managed by the framework's DI
  container. In Python, metrics are commonly module-level singletons from the
  `prometheus_client` library, reflecting the same low-ceremony, globally
  reachable shape as Go, because Python's request-handling model (WSGI
  workers, often multi-process) makes per-request instantiation of metric
  objects both wasteful and, in multi-process deployments, incorrect without
  an explicit multiprocess collector.

## 9. Known production uses

- **SoundCloud, Prometheus's origin.** Prometheus itself was built at
  SoundCloud starting in 2012, specifically to instrument and monitor their
  own service-oriented architecture, before being open sourced and eventually
  joining the Cloud Native Computing Foundation as its second hosted project
  after Kubernetes (Prometheus documentation, "Overview",
  `https://prometheus.io/docs/introduction/overview/`, verified 2026-08-02).
- **Etsy, StatsD.** Etsy created and open sourced StatsD in 2011 as part of a
  deliberate engineering culture shift toward instrumenting essentially every
  code path, summarized in their own engineering blog post title, "Measure
  Anything, Measure Everything," which the current statsd project repository
  still cites as the tool's origin story (Etsy Code as Craft blog, 2011, as
  referenced in `https://github.com/statsd/statsd`, verified 2026-08-02).
- **Kubernetes-native stacks using kube-state-metrics and cAdvisor.** The
  Kubernetes project itself ships cAdvisor, embedded in the kubelet, which
  exposes container-level Application Metrics (CPU, memory, network per
  container) in the Prometheus exposition format, and the separate
  `kube-state-metrics` project exposes metrics about Kubernetes API objects
  in the same format, both consumed by the same pull-based aggregation model
  this pattern describes. The underlying mechanism is the Prometheus pull
  model documented at `https://prometheus.io/docs/introduction/overview/`, verified
  2026-08-02.
- **Spring Boot Actuator and Micrometer.** Every Spring Boot application that
  enables the Actuator module gets an automatically wired `MeterRegistry`
  from Micrometer, which the Micrometer project describes as its purpose,
  letting JVM applications instrument themselves without vendor lock-in
  across a long list of supported backends including Prometheus, Datadog,
  CloudWatch, and OpenTelemetry Protocol (Micrometer documentation,
  "Micrometer Concepts", `https://docs.micrometer.io/micrometer/reference/concepts.html`,
  verified 2026-08-02).

## 10. Consequences

Positive.

- Operators gain a continuously updated, aggregate view of system behavior
  across every instance of every service, closing the gap that a
  single-process monolith never had in the first place.
- Auto-scalers and load balancers get a concrete numeric signal (request
  rate, queue depth, CPU) to make decisions on, rather than relying on a
  human to notice a problem first.
- Alerting becomes proactive rather than reactive, because a threshold on a
  metric (error rate above 1 percent for five minutes) can page someone
  before a customer notices, whereas a log-based or trace-based signal
  usually only explains an incident after it has already happened.
- Historical time series make capacity planning and SLO tracking possible,
  answering questions such as "how has p99 latency trended over the last
  quarter" that neither a live process inspection nor a single trace can
  answer.
- Because metrics are pre-aggregated numbers rather than raw events, storage
  and query cost per unit of operational insight is far lower than the
  equivalent insight extracted from raw logs or traces, which is why metrics
  remain the first-line signal even in systems that also have full tracing.

Negative.

- Instrumentation code is now interleaved with business logic, and
  Richardson names this directly as a real cost, the metrics collection code
  intertwined with the business logic that this pattern introduces
  (Richardson, microservices.io, Application Metrics, verified 2026-08-02).
  Every metrics call is a small piece of infrastructure concern living inside
  a method whose primary job is something else.
- Aggregating and storing metrics at fleet scale is itself infrastructure
  that must be built, operated, and paid for, and Richardson's own
  description of the pattern names this operational burden explicitly as a
  drawback (Richardson, microservices.io, Application Metrics, verified
  2026-08-02).
- A high number of distinct label-value combinations is a standing liability,
  and a single label added carelessly to a hot-path metric (a raw user ID,
  an unbounded URL path) can multiply the number of stored time series by
  orders of magnitude and degrade or crash the aggregation backend, a
  failure mode that is invisible in code review and only shows up under
  real traffic.
- Metrics are aggregates by construction, so they discard the very
  information (which specific request, which specific user, the full causal
  chain across services) that a person debugging a single incident often
  needs, which is precisely the space Distributed Tracing exists to fill and
  metrics alone cannot.
- A dashboard or alert built on a metric is only as trustworthy as the
  instrumentation behind it, and a metric silently stops being emitted
  (a code path removed, a label renamed) far more often than it fails
  loudly, which means metrics-based systems accumulate silent blind spots
  unless someone actively audits what is and is not still being recorded.

## 11. Failure modes and misuse

**Series-count explosion from an unbounded label.** Symptom. The metrics
backend's memory usage grows without bound, queries that used to return in
milliseconds start timing out, and eventually the backend either falls over
or starts silently dropping new time series. Cause. A label was added to a
metric using a value with effectively unlimited distinct values, most
commonly a raw user ID, a session token, a full request path with path
parameters still embedded (each order ID producing its own distinct label
value), or a full URL including query string. Fix. Bucket or strip the
offending dimension before it becomes a label, use a route template instead
of the resolved path, and push the truly high-variety identifier into a
log line or a trace span, both of which are architecturally built to hold
per-event unique values.

**Recording a duration as a Gauge instead of a Histogram.** Symptom. A
latency dashboard shows a single jagged line jumping between the duration of
whichever request happened to finish last, instead of a true distribution,
and any alert built on it fires and clears erratically because it is
watching one sample at a time rather than an aggregate. Cause. The team used
a Gauge, which by definition holds only the most recently set value, to
record something that should be summarized across many observations, such
as request latency, which needs a Histogram or a Summary to produce a
trustworthy percentile (Prometheus documentation, "Metric Types",
`https://prometheus.io/docs/concepts/metric_types/`, verified 2026-08-02, defines
Gauge as a single numerical value that can arbitrarily go up and down,
versus Histogram as observations counted into buckets). Fix. Replace the
Gauge with a Histogram, or a Summary, for any measurement that represents
one observation among many per interval, and reserve Gauge strictly for
values that genuinely represent a current level, such as an open connection
count or a queue depth.

**Blocking the request path on a metrics send.** Symptom. Under load,
request latency spikes correlate exactly with metrics backend slowness, even
though the metrics backend has nothing to do with the actual business logic
being measured. Cause. The service pushes metrics synchronously, on the same
thread handling the request, to a network endpoint that can itself be slow
or momentarily unavailable, so a slow metrics collector becomes a slow
application. Fix. Make metric recording an in-memory, non-blocking update to
a local counter or histogram, and perform the actual network send (whether
push or pull) asynchronously, on a separate thread or in response to an
external scrape, so the metrics subsystem can never add latency to the
request it is measuring.

**Silent metric death after a refactor.** Symptom. A dashboard panel that
used to show data now shows a flat line at zero or a permanent gap, and
nobody notices for weeks because nothing pages on the absence of a metric,
only on a threshold breach within it. Cause. A code path that incremented a
counter was refactored, renamed, or deleted, and the metric name changed or
the increment call was accidentally dropped, with no compile-time or runtime
signal that this happened, because metric names are almost always plain
strings. Fix. Treat metric emission as a tested contract, assert in unit or
integration tests that the expected counters increment on the expected code
paths, and periodically audit dashboards against the metric names actually
present in the backend rather than trusting that a panel still means what it
meant when it was created.

**Confusing an average for a distribution.** Symptom. The team reports
average latency as healthy while a large share of real users experience
multi-second waits, and this is only discovered when a customer complains.
Cause. The team instrumented and alerted on a mean, or worse, an average of
per-instance averages, rather than a percentile, and an average is
mathematically insensitive to a long tail. a handful of very slow
requests barely move the mean but can represent a large share of unhappy
users. Fix. Instrument latency as a Histogram and alert on p95 or p99, not
the mean, and treat a healthy average as a claim that must be checked
against the actual distribution before it is trusted.

## 12. Trade-off matrix

| Force | Application Metrics | Log Aggregation | Distributed Tracing | Health Check API |
|---|---|---|---|---|
| Per-request causal detail | Low, metrics are aggregates by design | Medium, one line per event, causality inferred | High, explicit parent-child span graph per request | None, answers only current process state |
| Storage cost at scale | Low per unit of insight, pre-aggregated numbers | High, every log line stored and often re-parsed | High, every span stored, though often sampled | Negligible, not stored historically by default |
| Time-series / trend analysis | Native strength, this is exactly what it is for | Possible but requires extra pipeline (parsing, indexing) | Weak, spans are per-request, not naturally aggregated over time | None |
| Runtime overhead per request | Very low, an atomic increment or histogram observation | Low to medium, depends on log verbosity | Medium, span creation, context propagation, export | Very low, endpoint only hit periodically |
| Good for auto-scaling decisions | Yes, purpose-built for this | No, not structured for real-time decisioning | No | Partial, tells liveness or readiness, not load |
| Good for root cause of one bad request | No | Sometimes, if request ID is correlated | Yes, purpose-built for this | No |
| Setup cost | Medium, needs a metrics backend and instrumentation discipline | Low, logs often already exist as a byproduct | High, needs context propagation across every service boundary | Very low, a single endpoint per service |

Application Metrics and Log Aggregation, Distributed Tracing, and Health
Check API are not mutually exclusive alternatives in the way a Strategy and a
Template Method might be. Richardson presents them as siblings within the
same observability practice, each answering a different question at a
different cost, and a production-grade microservices system in practice runs
all four together rather than choosing one (Richardson, *Microservices
Patterns*, Manning, 2018, chapter 11).

## 13. Related and incompatible patterns

- **Health Check API.** A narrower, point-in-time sibling. Health Check API
  answers "is this instance alive and ready right now," a single boolean or
  small enum evaluated on demand, usually by an orchestrator's liveness or
  readiness probe. Application Metrics answers "what has this instance's
  behavior looked like over time," a continuous numeric record. The two
  compose cleanly, an unhealthy readiness check is itself often exposed as a
  metric so its history can be graphed and alerted on, not only acted on in
  the moment.
- **Log Aggregation.** A complementary observability pattern operating on
  unstructured or semi-structured text events rather than numeric time
  series. Teams frequently derive metrics from aggregated logs (counting
  ERROR lines per minute as a proxy metric) when they have not yet built
  direct instrumentation, making Log Aggregation a common stepping stone
  toward, rather than a replacement for, Application Metrics.
- **Distributed Tracing.** A complementary pattern that preserves per-request
  causal structure across service boundaries, which Application Metrics
  deliberately discards in exchange for cheap, storable aggregates. A metric
  spike (a rise in p99 latency) commonly triggers a search for individual
  slow traces to explain why, so the two patterns are usually wired together
  operationally even though they are structurally distinct.
- **Circuit Breaker.** Circuit Breaker's open, closed, and half-open state
  transitions are themselves a natural source of metrics (breaker trip
  count, current state as a gauge), and a well-instrumented Circuit Breaker
  implementation emits Application Metrics as a byproduct of protecting a
  downstream call, making the two patterns commonly paired in practice.
- **Service Mesh.** A service mesh's sidecar proxy (Envoy in Istio, for
  example) can emit a large share of the request-level metrics (rate,
  errors, duration, the so-called RED metrics) automatically for every
  service in the mesh, without any in-process instrumentation, which shifts
  where Application Metrics is implemented (infrastructure layer instead of
  application code) without changing the pattern's intent. Services in a
  mesh commonly still instrument business-specific metrics themselves, since
  the mesh only sees network-level traffic, not domain events.
- **API Gateway.** An API Gateway sits at the system's edge and can record
  Application Metrics for every inbound request before it fans out into the
  microservices architecture, giving a useful outside-in view that
  complements, rather than substitutes for, the per-service metrics each
  downstream service records about its own internal behavior.
- No pattern in this catalog is structurally incompatible with Application
  Metrics. its cost is additive code and additive infrastructure, not a
  design constraint that conflicts with another pattern's structure.

## 14. Refactoring path in and out

Introducing Application Metrics into a service that has none, step by step.

1. Pick a facade appropriate to the language and stack rather than a
   specific vendor's client library directly, for example Micrometer on the
   JVM or the OpenTelemetry Metrics API elsewhere, so the eventual choice of
   backend does not require touching business code a second time.
2. Instrument the request entry point first, a single counter for total
   requests labeled by route and status code, and a single histogram for
   request duration labeled by route. This alone answers the two most
   commonly needed operational questions, how much traffic and how fast, for
   the whole service with the smallest possible change.
3. Add a `/metrics` exposition endpoint, or wire the push client to a
   locally reachable collector, and confirm with a manual curl or a local
   scrape that real numbers appear before wiring up any backend
   infrastructure.
4. Point a metrics backend, even a throwaway local Prometheus instance
   during development, at the new endpoint and confirm the time series
   appears and updates as expected traffic is generated.
5. Instrument the next layer of interest, calls to downstream services
   (latency and error rate per dependency) and any resource pool the service
   manages (connection pool utilization as a gauge), because these are the
   signals that most often explain a request-level regression once one is
   detected in step 2's metrics.
6. Add domain-specific counters only after the generic request and
   dependency metrics are in place and proven useful, resisting the urge to
   instrument everything on day one, since an unused metric is pure ongoing
   cost with no offsetting benefit.
7. Wire alerting rules against the new metrics only after they have been
   observed for long enough, typically at least one full traffic cycle, a
   week for most consumer-facing services, to know what a normal baseline
   looks like, so the first alert threshold is not a guess.

Removing or reducing Application Metrics, when a metric has stopped earning
its place.

1. Confirm the metric has no active dashboard panel or alerting rule
   depending on it, by querying the aggregation backend's own metadata
   (Prometheus exposes which series still have recent samples) rather than
   relying on memory of who built what.
2. Remove the instrumentation call from the code, not only the dashboard
   panel, because a metric still being recorded but no longer viewed is
   still paying its full runtime and storage cost with zero remaining
   benefit.
3. Leave the historical data in the backend to expire on its own retention
   schedule rather than attempting to delete it, since most time series
   backends are not built for efficient point deletes and the old data is
   harmless once nothing is writing to it.
4. If the metric is being replaced rather than simply retired, ship the new
   metric under a new name and run both in parallel for one full baseline
   period before removing the old one, so historical continuity is not lost
   at exactly the moment someone needs to compare before and after the
   change.

## 15. Testing and verification

What Application Metrics makes easier to test. the presence and correctness
of a metric increment can be asserted directly, because most metrics
libraries expose an in-memory registry that a unit test can query
synchronously after invoking the code under test, without needing a real
network call, a real metrics backend, or a real clock beyond what the test
itself controls. A test can call the handler under test, then assert that a
counter's current value equals the expected value, or that a histogram's
observation count increased by exactly one, giving a fast, deterministic,
fully local test for something that in production only becomes visible on a
dashboard.

What becomes harder. verifying that the exported format is correct end to
end, that the `/metrics` endpoint actually serializes the registry into
valid Prometheus exposition format, or that a push client actually
constructs a well-formed StatsD packet, requires either an integration test
that stands up the real HTTP endpoint and parses its response, or a
contract test against the client library's own documented format, since a
unit test against the in-memory registry alone cannot catch a serialization
bug in the exporter layer.

Useful techniques and test doubles.

- **In-memory registry assertion.** Most facades (Micrometer's
  `SimpleMeterRegistry`, the Prometheus client library's default registry)
  are designed to be instantiated fresh in a test and inspected directly,
  making this the primary and cheapest verification technique for confirming
  the code recorded what it should have.
- **A no-op or null metrics backend for pure logic tests.** When the code
  under test is not itself about metrics, injecting a no-op implementation
  of the facade interface keeps unrelated unit tests free of any metrics
  concern, verifying only that instrumentation calls do not throw or block,
  never their content.
- **A local scrape integration test.** For services exposing a pull-based
  `/metrics` endpoint, an integration test that starts the real HTTP server,
  issues a real GET to `/metrics`, and asserts the response body contains an
  expected metric name and label combination catches serialization and
  wiring bugs that an in-memory unit test structurally cannot see.
- **Load or soak tests as a check on series count, not only correctness.**
  Because the series-count explosion failure mode described in dimension 11
  only manifests under realistic traffic shape, a periodic load test that
  inspects the actual number of distinct time series produced under
  representative load, rather than only checking that metrics exist at all,
  is the practical way to catch a runaway label before it reaches
  production.

## 16. Observability signals

This is itself the pattern whose subject is observability, so this dimension
is about observing the metrics subsystem's own health, a real and often
overlooked concern.

A healthy instance of the pattern looks like this. the `/metrics` endpoint,
or push client, responds in low single-digit milliseconds even under load,
because recording a metric should never be a measurable fraction of request
latency. the total number of distinct time series exported by a single
service instance stays within a bounded, expected range over time rather
than growing unboundedly as new label value combinations appear. scrape
success rate, as tracked by the aggregation backend itself (Prometheus
exposes an `up` value and per-target scrape duration for exactly this
purpose), stays at or near 100 percent for every registered target. and
every counter that is supposed to be monotonically increasing under normal
load actually is, with unexpected resets serving as a signal of an unplanned
process restart rather than a metrics bug.

A failing instance looks like this. the scrape target starts timing out or
returning partial responses, usually because the metrics registry has grown
so large, driven by an unbounded label producing too many distinct series,
that serializing it on every scrape has itself become expensive. the number
of distinct time series for a single metric name grows linearly or worse
with traffic volume rather than staying flat, the clearest early warning
sign of an unbounded label. a gauge that should track a bounded resource, a
connection pool size, instead grows without bound, indicating either the
gauge itself is being incremented without a matching decrement somewhere, or
the underlying resource really is leaking and the metric is correctly
reporting a real bug elsewhere in the system. and a previously present
metric silently stops appearing in the backend with no corresponding alert,
the silent-death failure mode from dimension 11, which is why teams that
take this pattern seriously add a meta-alert on the absence of an expected
metric, not only on thresholds within metrics that are present.

## 17. Security and privacy implications

Judgement. this dimension is analytical, based on how the pattern's
mechanics interact with common data handling practice, rather than a single
citable specification.

Metric labels are frequently the accidental leak point for personally
identifiable information, because a well-intentioned engineer adds a label
for debuggability (a customer email, a raw user ID, a full request path
carrying a token) without recognizing that the metrics backend, unlike an
access-controlled log store, is often broadly readable by every engineer
with dashboard access, and that the same unbounded label which causes the
series-count failure mode in dimension 11 can simultaneously be a privacy
failure mode, since a distinct time series per user ID means the metrics
backend is, in effect, storing a per-user activity record it was never
designed or access-controlled to hold.

The `/metrics` exposition endpoint itself is, in the default pull-based
implementation, an unauthenticated HTTP endpoint exposing internal
operational detail, request rates by route, error rates, sometimes
downstream dependency identifiers, which is intentionally not customer
facing but is a real information disclosure surface if reachable from
outside the deployment's trusted network. Production deployments typically
restrict this endpoint to a private network reachable only by the
aggregation backend's scraper, and treating that restriction as a load
bearing security control rather than an incidental default is standard
operational practice at teams that run Prometheus at scale.

Push-based metrics over UDP, the StatsD variant, accept data from any
process that can reach the listening port with no authentication, which is
an intentional design trade favoring low overhead over provenance, and it
means the pattern's own trust boundary in that variant is the local network
segment or container namespace the metrics agent listens on, not the
metric data itself.

Aggregated metrics data, being numeric and pre-aggregated across many
instances and requests, is, by its aggregated nature, lower risk to retain
long term than raw logs or full request traces, which is one reason
retention policies for metrics backends are commonly far longer, months to
years, than for logs or traces, days to weeks, at the same organization, a
practical consequence of the aggregation this pattern performs rather than a
formal compliance requirement.

## 18. References

1. Chris Richardson, "Pattern. Application metrics",
   `https://microservices.io/patterns/observability/application-metrics.html`,
   verified 2026-08-02.
2. Chris Richardson, *Microservices Patterns*, Manning Publications, 2018,
   chapter 11, "Developing production ready services".
3. Prometheus documentation, "Overview",
   `https://prometheus.io/docs/introduction/overview/`, verified 2026-08-02.
4. Prometheus documentation, "Metric types",
   `https://prometheus.io/docs/concepts/metric_types/`, verified 2026-08-02.
5. Micrometer documentation, "Micrometer Concepts",
   `https://docs.micrometer.io/micrometer/reference/concepts.html`, verified
   2026-08-02.
6. OpenTelemetry documentation, "Metrics",
   `https://opentelemetry.io/docs/concepts/signals/metrics/`, verified 2026-08-02.
7. Etsy Code as Craft blog, "Measure Anything, Measure Everything", 2011, as
   cited by the statsd project, `https://github.com/statsd/statsd`, verified
   2026-08-02.

## Code examples

### TypeScript

```typescript
type Labels = Record<string, string>;

function labelKey(labels: Labels): string {
  return Object.keys(labels).sort().map(k => `${k}=${labels[k]}`).join(",");
}

class Counter {
  private values = new Map<string, number>();
  constructor(public readonly name: string) {}
  inc(labels: Labels = {}, amount = 1): void {
    const key = labelKey(labels);
    this.values.set(key, (this.values.get(key) ?? 0) + amount);
  }
  get(labels: Labels = {}): number {
    return this.values.get(labelKey(labels)) ?? 0;
  }
}

class Histogram {
  private buckets: number[];
  private counts: Map<string, number[]> = new Map();
  private sums: Map<string, number> = new Map();
  constructor(public readonly name: string, bucketBounds: number[]) {
    this.buckets = [...bucketBounds].sort((a, b) => a - b);
  }
  observe(value: number, labels: Labels = {}): void {
    const key = labelKey(labels);
    if (!this.counts.has(key)) {
      this.counts.set(key, new Array(this.buckets.length).fill(0));
      this.sums.set(key, 0);
    }
    const bucketCounts = this.counts.get(key)!;
    for (let i = 0; i < this.buckets.length; i++) {
      if (value <= this.buckets[i]) bucketCounts[i]++;
    }
    this.sums.set(key, this.sums.get(key)! + value);
  }
  bucketCounts(labels: Labels = {}): number[] {
    return this.counts.get(labelKey(labels)) ?? new Array(this.buckets.length).fill(0);
  }
}

const requestsTotal = new Counter("http_requests_total");
const requestDuration = new Histogram("http_request_duration_ms", [10, 50, 100, 500, 1000]);

function handleRequest(route: string, durationMs: number, statusCode: number): void {
  requestsTotal.inc({ route, status: String(statusCode) });
  requestDuration.observe(durationMs, { route });
}

handleRequest("/orders", 42, 200);
handleRequest("/orders", 812, 500);
handleRequest("/orders", 30, 200);

console.log("requests /orders 200", requestsTotal.get({ route: "/orders", status: "200" }));
console.log("requests /orders 500", requestsTotal.get({ route: "/orders", status: "500" }));
console.log("duration buckets /orders", requestDuration.bucketCounts({ route: "/orders" }));
```

### Python

```python
from collections import defaultdict
from bisect import bisect_left


def label_key(labels):
    return tuple(sorted(labels.items()))


class Counter:
    def __init__(self, name):
        self.name = name
        self.values = defaultdict(int)

    def inc(self, labels=None, amount=1):
        self.values[label_key(labels or {})] += amount

    def get(self, labels=None):
        return self.values[label_key(labels or {})]


class Histogram:
    def __init__(self, name, bucket_bounds):
        self.name = name
        self.buckets = sorted(bucket_bounds)
        self.counts = defaultdict(lambda: [0] * len(self.buckets))
        self.sums = defaultdict(float)

    def observe(self, value, labels=None):
        key = label_key(labels or {})
        idx = bisect_left(self.buckets, value)
        for i in range(idx, len(self.buckets)):
            self.counts[key][i] += 1
        self.sums[key] += value

    def bucket_counts(self, labels=None):
        return self.counts[label_key(labels or {})]


requests_total = Counter("http_requests_total")
request_duration = Histogram("http_request_duration_ms", [10, 50, 100, 500, 1000])


def handle_request(route, duration_ms, status_code):
    requests_total.inc({"route": route, "status": str(status_code)})
    request_duration.observe(duration_ms, {"route": route})


handle_request("/orders", 42, 200)
handle_request("/orders", 812, 500)
handle_request("/orders", 30, 200)

print("requests /orders 200", requests_total.get({"route": "/orders", "status": "200"}))
print("requests /orders 500", requests_total.get({"route": "/orders", "status": "500"}))
print("duration buckets /orders", request_duration.bucket_counts({"route": "/orders"}))
```

### Go

```go
package main

import (
	"fmt"
	"sort"
	"strings"
	"sync"
)

type Labels map[string]string

func labelKey(l Labels) string {
	keys := make([]string, 0, len(l))
	for k := range l {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	parts := make([]string, 0, len(keys))
	for _, k := range keys {
		parts = append(parts, k+"="+l[k])
	}
	return strings.Join(parts, ",")
}

type Counter struct {
	mu     sync.Mutex
	name   string
	values map[string]float64
}

func NewCounter(name string) *Counter {
	return &Counter{name: name, values: make(map[string]float64)}
}

func (c *Counter) Inc(l Labels, amount float64) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.values[labelKey(l)] += amount
}

func (c *Counter) Get(l Labels) float64 {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.values[labelKey(l)]
}

type Histogram struct {
	mu      sync.Mutex
	name    string
	buckets []float64
	counts  map[string][]int
}

func NewHistogram(name string, bounds []float64) *Histogram {
	b := append([]float64(nil), bounds...)
	sort.Float64s(b)
	return &Histogram{name: name, buckets: b, counts: make(map[string][]int)}
}

func (h *Histogram) Observe(value float64, l Labels) {
	h.mu.Lock()
	defer h.mu.Unlock()
	key := labelKey(l)
	if _, ok := h.counts[key]; !ok {
		h.counts[key] = make([]int, len(h.buckets))
	}
	for i, bound := range h.buckets {
		if value <= bound {
			h.counts[key][i]++
		}
	}
}

func (h *Histogram) BucketCounts(l Labels) []int {
	h.mu.Lock()
	defer h.mu.Unlock()
	return h.counts[labelKey(l)]
}

func main() {
	requestsTotal := NewCounter("http_requests_total")
	requestDuration := NewHistogram("http_request_duration_ms", []float64{10, 50, 100, 500, 1000})

	handleRequest := func(route string, durationMs float64, status int) {
		requestsTotal.Inc(Labels{"route": route, "status": fmt.Sprintf("%d", status)}, 1)
		requestDuration.Observe(durationMs, Labels{"route": route})
	}

	handleRequest("/orders", 42, 200)
	handleRequest("/orders", 812, 500)
	handleRequest("/orders", 30, 200)

	fmt.Println("requests /orders 200", requestsTotal.Get(Labels{"route": "/orders", "status": "200"}))
	fmt.Println("requests /orders 500", requestsTotal.Get(Labels{"route": "/orders", "status": "500"}))
	fmt.Println("duration buckets /orders", requestDuration.BucketCounts(Labels{"route": "/orders"}))
}
```
