---
name: Exception Tracking
slug: exception-tracking
family: 10-microservices
category: Observability
aliases: [Error Tracking, Crash Reporting, Centralized Exception Reporting]
first_described: "Chris Richardson, microservices.io, Observability patterns, 2018"
maturity: established
related: [log-aggregation, application-metrics, circuit-breaker, microservice-chassis]
incompatible_with: []
verified: 2026-08-02
---

# Exception Tracking

## 1. Name, aliases, and lineage

The canonical name in the microservices catalog is Exception Tracking. Chris
Richardson lists it under the Observability category of his microservices
pattern catalog, describing the problem as a service instance throwing an
exception during request handling and the solution as reporting all
exceptions to a centralized exception tracking service that aggregates and
tracks exceptions and notifies developers (Chris Richardson, microservices.io,
"Pattern. Exception tracking", https://microservices.io/patterns/observability/exception-tracking.html
verified 2026-08-02).

The idea is older than the microservices vocabulary. Web application
frameworks have shipped an equivalent mechanism under the name error
reporting since at least the mid 2000s. Django ships a built in email based
error reporter that fires on any unhandled server error, and explicitly
documents that a third party service can be substituted through the
`DEFAULT_EXCEPTION_REPORTER` setting (Django Software Foundation, Django 5.2
documentation, "Error reporting",
https://docs.djangoproject.com/en/5.2/howto/error-reporting/ verified
2026-08-02). Commercial products from the same era, and the ones a reader
will install today, use the names Error Tracking (Sentry, Rollbar, Bugsnag)
or Crash Reporting (mobile platform vendors, where an unhandled exception
usually terminates the process). Crash Reporting is worth keeping as a
distinct alias rather than a synonym, because a crash implies process
termination and a service side exception often does not, see dimension 4.

Two things get called exception tracking that are not the pattern described
here, and the distinction matters for dimension 4.

- **Log aggregation with a grep for the word Exception.** Searching a
  centralized log store for stack traces is not exception tracking, it is
  log aggregation used as a substitute for it. Log aggregation stores every
  line without deduplication, ranking, or a notification path, and the two
  patterns are commonly paired rather than confused once the difference is
  named, see dimension 13.
- **Application performance monitoring (APM).** An APM product such as Azure
  Application Insights or Datadog APM does exception tracking as one of
  several capabilities alongside distributed tracing, latency percentiles,
  and infrastructure metrics. Azure Application Insights documents a
  dedicated `UnhandledExceptionTelemetryModule` that automatically captures
  unhandled .NET exceptions and a manual `TelemetryClient.TrackException`
  API for the rest (Microsoft, Azure Monitor documentation, "Diagnose
  exceptions in ASP.NET web apps with Application Insights",
  https://learn.microsoft.com/en-us/azure/azure-monitor/app/asp-net-exceptions
  verified 2026-08-02). Calling the whole APM product exception tracking
  understates what it does and overstates what a narrower, single purpose
  exception tracker like Sentry or Rollbar provides.

## 2. Problem and context

A request arrives at a service instance and, partway through handling it,
code raises an exception the calling frames do not catch. The process does
not necessarily crash, most server frameworks catch the exception at the top
of the request handling stack and return an error response, but the specific
failure that occurred is now only visible as a single line in a log file on
one of possibly hundreds of running instances, and it will scroll out of
that log within minutes under real traffic.

The concrete situation a reader recognises from their own codebase. A
deploy goes out on a Tuesday. By Wednesday, a null reference started firing
in an edge case nobody wrote a test for, on maybe one request in ten
thousand. Nobody notices, because the request still returns a 500 that the
client silently retries or silently drops, and the exception is one entry
among millions in a log aggregation index that nobody is watching in real
time. Three weeks later a customer complains that a feature intermittently
fails, and an engineer spends an afternoon constructing a log query trying
to find the one relevant line among the noise, with no idea whether this is
a new problem, a problem that started three weeks ago, or a problem that has
always existed.

The context that produces this problem has three properties working
together, and the pattern only earns its place where all three are present.

- The system has many service instances, often across many services, so an
  exception raised on instance 47 of service B is invisible to whoever is
  watching instance 12 of service A.
- Failures are individually low frequency against total traffic, so they do
  not show up on an aggregate error rate dashboard until the rate climbs far
  enough to move a percentage, by which point real customers have already
  been affected for a while.
- The team wants to know about a regression within minutes of a deploy, not
  discover it from a support ticket weeks later, which requires the failure
  to be pushed to a person rather than waited for by a person.

## 3. Forces

- **Signal versus volume.** Favoured toward signal. A single bug that fires
  on 0.1 percent of requests at a million requests a day produces a
  thousand exceptions an hour. The pattern's whole value depends on
  collapsing that thousand into one issue a human looks at once, which
  means the deduplication algorithm is the pattern, not an implementation
  detail.
- **Time to detection.** Strongly favoured. A raw log line sits inert until
  queried. A tracking service that notifies on a new or regressed issue
  turns detection from a pull the engineer has to remember to do into a
  push that reaches them.
- **Cost.** Sacrificed, in two forms. A hosted service is priced per event
  or per unique issue and gets expensive fast under noisy logging, and a
  self hosted instance is one more stateful service to operate, patch, and
  scale. Both costs are usually paid deliberately in exchange for detection
  time, but neither is free, and dimension 11 covers the specific failure
  mode where the cost silently spikes.
- **Payload sensitivity.** Sacrificed unless actively managed. An exception
  captured with full context, request body, headers, local variables in
  the stack frames, routinely includes personal data, secrets, or both.
  See dimension 17.
- **Latency and reliability of the request path.** Close to neutral if done
  right, sacrificed if done wrong. Reporting must be asynchronous and must
  itself be allowed to fail without taking the request down with it,
  otherwise the observability mechanism becomes a new cause of outages,
  which is the opposite of its purpose.
- **Coupling to a vendor or a self hosted platform.** Sacrificed. Every
  service that reports through the same tracking service now shares an
  operational dependency, and most tracking SDKs are not drop in
  replaceable for one another once custom fingerprinting rules or
  integrations are configured.
- **Developer trust in the signal.** Favoured when tuned, sacrificed when
  not. A tracker that pages someone for every exception, including the
  ones that are expected client errors, trains the team to ignore it within
  a month. Getting this right is mostly a triage and configuration
  discipline problem rather than a code problem, see dimension 11.

## 4. Applicability and non-applicability

Reach for exception tracking when the following hold.

- The system runs more than a handful of long lived service instances, so
  correlating a failure across instances by hand is already impractical.
- Failures individually are rare enough against total traffic that an
  aggregate error rate alert would miss them for a while, but the failure
  still matters, a payment that silently did not process, a message that
  was dropped, a user who hit a broken flow.
- The team wants a new or newly worsening failure surfaced within minutes,
  not discovered from a support ticket or a manual log query days or weeks
  later.
- More than one team or more than one on call rotation needs to see the
  same failures, so a shared, deduplicated, assignable view is worth more
  than everyone independently grepping the same logs.
- The codebase already produces structured exceptions with stack traces, so
  the deduplication algorithm has something reliable to group on.

Do not reach for exception tracking, or reach for a lighter mechanism
instead, in these cases.

- **A single process script or a short lived batch job.** A cron job that
  runs for ninety seconds and either succeeds or fails does not benefit
  from deduplication across running instances, because there is effectively
  one instance and one run. A non zero exit code plus a log line, watched by
  the job scheduler, is the honest shape, and standing up a tracking
  integration here is pure overhead. Cross reference the code smell family
  entry on unneeded infrastructure ceremony.
- **Expected, handled, client caused errors.** A malformed request that a
  handler validates and returns as a 400 is not an exception tracking
  concern, it is a metrics concern, a counter labelled by status code and
  route belongs in application metrics instead, see dimension 13. Routing
  every 400 through the exception tracker is the single most common misuse
  of the pattern, see dimension 11, because it drowns the signal the
  pattern exists to surface.
- **A system with no traffic pattern that would hide a rare failure.** If
  the whole system handles ten requests an hour and every operator already
  reads every log line by hand, a tracking service adds a dependency to
  manage without adding detection speed the team does not already have.
- **Data whose exposure risk outweighs the debugging value.** In a system
  handling regulated health or financial data where request payloads cannot
  leave a compliance boundary, sending a raw exception with local variable
  state to an external SaaS tracker is not an implementation detail to
  tune later, it is a decision that needs data protection review before
  any SDK is installed. Self hosting, or scrubbing before transmission, or
  not tracking exceptions from that boundary at all are the honest
  alternatives, see dimension 17.
- **Distributed tracing already answers the question being asked.** If what
  the team needs is why is this one request slow, a trace with span timings
  answers that better than an exception tracker, which answers which known
  failure happened again. The two are complementary, not substitutes, but
  reaching for exception tracking to solve a latency question is a category
  mismatch.
- **The team has no process to triage what gets reported.** Standing up the
  integration without an owner who reviews new issues, mutes the noisy
  ones, and assigns the real ones produces a growing pile of unread issues
  that nobody trusts, which is worse than not having the tool, because it
  gives a false sense that failures are being watched.

## 5. Structure

Four participants, named by the role each plays.

- **Instrumented Service.** Any process that can raise an exception during
  its own work, whether that is handling an inbound request, consuming a
  message, or running a scheduled job. It carries the tracking SDK or
  client library and is the only participant that knows the full local
  context of a given failure, the stack trace, the request that triggered
  it, and any tags the service chooses to attach.
- **Reporter (the SDK or client).** A library embedded in the Instrumented
  Service that installs a global exception or signal handler, captures the
  exception's type, message, stack trace, and configured context when one
  fires, and transmits it to the Collector, normally asynchronously and off
  the thread that is handling the failing request. The reporter is also
  responsible for local rate limiting and payload scrubbing before anything
  leaves the process, which is the first and cheapest place to enforce the
  privacy concerns in dimension 17.
- **Collector (the exception tracking service).** Receives raw exception
  reports from every Instrumented Service across the system, whether that
  is one service or two hundred. It computes a fingerprint for each report,
  most commonly derived from the normalized stack trace, groups reports
  sharing a fingerprint into one Issue, counts occurrences, and tracks first
  seen and last seen timestamps.
- **Issue (the aggregated record).** The unit a human looks at. One Issue
  represents one root cause across however many raw occurrences it
  absorbed, and carries a status, commonly unresolved, resolved, or
  ignored, an assignee, and a notification policy that decides whether a
  new or reopened Issue pages someone.

Relationships. The Instrumented Service depends on the Reporter, and the
Reporter depends on the Collector's ingestion API, normally over an
authenticated HTTPS endpoint. The Collector owns the Issue store and the
grouping algorithm, and nothing about the grouping logic lives in the
Instrumented Service. Multiple Instrumented Services, potentially written in
different languages, report to the same Collector, which is what makes
cross service correlation possible without every service knowing about
every other service.

## 6. ASCII structure diagram

```
  +------------------------+    +------------------------+
  |  Instrumented Service A |    |  Instrumented Service B |
  |  (order-service)         |    |  (payment-service)       |
  |--------------------------|    |--------------------------|
  |  business logic          |    |  business logic          |
  |  +--------------------+  |    |  +--------------------+  |
  |  |     Reporter       |  |    |  |     Reporter       |  |
  |  | (SDK, global hook) |  |    |  | (SDK, global hook) |  |
  |  +--------------------+  |    |  +--------------------+  |
  +-----------|--------------+    +-----------|--------------+
              |  async report                 |  async report
              |  (HTTPS, batched)              |
              v                                v
      +----------------------------------------------+
      |               Collector                        |
      |  (exception tracking service)                   |
      |  - fingerprint / dedupe                          |
      |  - group into Issues                             |
      |  - notify on new or regressed Issue              |
      +----------------------------------------------+
              |
              v
      +----------------------------------------------+
      |                  Issues                        |
      |  #1842  NullPointerException  order-service    |
      |         seen 1,204x  last 3 min ago   unresolved|
      |  #1843  TimeoutError          payment-service   |
      |         seen 6x     last 2h ago       assigned  |
      +----------------------------------------------+
              |
              v
      Engineer's dashboard, chat notification, or on-call page.
```

## 7. Dynamics

The reporting path must never sit on the critical path of the request it is
reporting on. The sequence below shows the request thread handing off to a
background reporting path rather than blocking on it, which is the property
that keeps the observability mechanism from becoming an outage cause in its
own right.

```
Caller        Instrumented Service         Reporter (SDK)        Collector
  |                    |                          |                    |
  |-- request -------->|                          |                    |
  |                    |-- (business logic runs,   |                    |
  |                    |    an exception is raised)|                    |
  |                    |                          |                    |
  |                    |-- global handler catches -|                    |
  |                    |   the exception            |                    |
  |                    |                          |                    |
  |                    |-- handler returns an     |                    |
  |                    |   error response NOW ---->|                    |
  |<-- 500 response ---|                          |                    |
  |                    |                          |                    |
  |                    |-- (in parallel, not on   |                    |
  |                    |    the response path)    |                    |
  |                    |-- capture(exception,     |                    |
  |                    |   context) ------------->|                    |
  |                    |                          |-- rate limit check |
  |                    |                          |-- scrub sensitive  |
  |                    |                          |   fields           |
  |                    |                          |-- enqueue locally  |
  |                    |                          |-- background flush |
  |                    |                          |   (batched) ------>|
  |                    |                          |                    |-- compute fingerprint
  |                    |                          |                    |-- match or create Issue
  |                    |                          |                    |-- update seen count
  |                    |                          |                    |-- if new/regressed,
  |                    |                          |                    |   fire notification
```

Two timing properties are worth stating plainly. First, the response to the
caller is returned before the report necessarily reaches the Collector, the
two are decoupled on purpose. Second, when the Collector itself is
unreachable, the correct behaviour of the Reporter is to drop the report
after a bounded local queue and a bounded number of retries, never to block
the Instrumented Service waiting for the Collector to come back, and never
to grow an unbounded local queue that itself becomes a memory leak, see
dimension 11.

## 8. Implementation variants

**Global uncaught handler.** The Reporter installs itself as the runtime's
top level uncaught exception hook, `sys.excepthook` in Python (Python
Software Foundation, Python 3 documentation, "sys.excepthook",
https://docs.python.org/3/library/sys.html#sys.excepthook verified
2026-08-02), the 'uncaughtException' process event in Node.js (OpenJS
Foundation, Node.js documentation, "process, the uncaughtException event",
https://nodejs.org/api/process.html#event-uncaughtexception verified
2026-08-02), or `Thread.setDefaultUncaughtExceptionHandler` in Java (Oracle,
Java SE 21 API Specification, `java.lang.Thread`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html
verified 2026-08-02). This variant catches whatever the application code did
not, which is a safety net rather than the primary reporting path, and the
Node.js documentation is explicit that resuming normal operation after this
event fires is not safe, the correct use is synchronous cleanup before the
process exits.

**Middleware or interceptor capture.** For request handling frameworks, the
Reporter wraps the request pipeline as middleware, catches any exception
that escapes the handler chain, reports it with the request's method, route,
and headers attached as context, and then re raises or converts it to the
framework's normal error response. This is the variant most services should
prefer over the global handler, because it runs before an exception has a
chance to reach the top level hook, and it has the request already in scope
to attach as context.

**Explicit capture at a call site.** Application code calls
`captureException(err)` directly, typically inside a handler block that
otherwise swallows or handles the error. This is the only variant that
works for exceptions the application deliberately caught and handled, which
the two automatic variants above never see, because a caught exception never
reaches an uncaught handler or an unhandled middleware boundary. A team that
relies only on automatic capture systematically misses every "caught it,
logged it, moved on" failure, which is frequently where the interesting
bugs live.

**Log forwarder based capture.** Rather than an SDK embedded in the process,
a sidecar or log shipper watches structured log output for records tagged
as an error or exception and forwards matching records to the Collector's
ingestion API. This decouples capture from the application's runtime and
language entirely, at the cost of losing whatever rich, structured context
an in process SDK can attach, such as breadcrumbs of the preceding user
actions, and of depending on log format discipline staying consistent.

**Fingerprint override.** Most Collectors let the Reporter or the server
side rule engine override the default stack trace based fingerprint for a
given exception. Sentry documents that a custom fingerprint takes priority
over the default stack trace based algorithm (Sentry, Sentry documentation,
"Grouping and Fingerprints", https://docs.sentry.io/concepts/data-management/event-grouping/
verified 2026-08-02). This matters for exceptions whose stack trace is
uninformative, a generic timeout raised from many call sites, where the
default algorithm would either over merge unrelated failures or fragment one
real failure into many Issues, and the application is the only party that
knows which of those two is happening.

**Framework integrated exception reporter.** Rather than a general SDK, the
framework exposes an extension point specifically for this, Django's
`DEFAULT_EXCEPTION_REPORTER` setting lets a project substitute its own
`ExceptionReporter` subclass for the built in email based one (Django
Software Foundation, Django 5.2 documentation, "Error reporting",
https://docs.djangoproject.com/en/5.2/howto/error-reporting/ verified
2026-08-02), and Azure Application Insights ships a dedicated
`UnhandledExceptionTelemetryModule` for ASP.NET rather than asking the
application to install a generic hook (Microsoft, Azure Monitor
documentation, "Diagnose exceptions in ASP.NET web apps with Application
Insights", https://learn.microsoft.com/en-us/azure/azure-monitor/app/asp-net-exceptions
verified 2026-08-02). This variant trades generality for a tighter fit with
the framework's own request lifecycle and error page rendering.

## 9. Known production uses

**Sentry, adopted across a broad range of production systems including
infrastructure, gaming, and streaming companies.** Sentry's own published
customer list names Cloudflare, Reddit, Disney Streaming Services, Riot
Games, Instacart, and Anthropic among its users, several with public case
studies describing measured reductions in mean time to detect and mean time
to resolve after adoption (Sentry, "Customer stories",
https://sentry.io/customers/ verified 2026-08-02). Sentry's own grouping
documentation describes the default algorithm as prioritising a custom
fingerprint when one is set, then the normalized stack trace, then the
exception type and value, then the message, as the fallback chain
(Sentry, "Grouping and Fingerprints",
https://docs.sentry.io/concepts/data-management/event-grouping/ verified
2026-08-02).

**Azure Application Insights, `UnhandledExceptionTelemetryModule` and
`TelemetryClient.TrackException`.** Microsoft's own observability platform
for Azure hosted and on premises .NET applications ships a telemetry module
that automatically instruments unhandled exceptions in ASP.NET applications,
alongside a manual `TrackException` API for exceptions the application
catches and wants to report deliberately (Microsoft, Azure Monitor
documentation, "Diagnose exceptions in ASP.NET web apps with Application
Insights", https://learn.microsoft.com/en-us/azure/azure-monitor/app/asp-net-exceptions
verified 2026-08-02). This is the explicit capture plus automatic capture
pairing described in dimension 8, shipped as a first party feature of a
major cloud platform rather than a third party add on.

**Django, the built in `AdminEmailHandler` with a pluggable
`DEFAULT_EXCEPTION_REPORTER`.** When `DEBUG` is `False`, Django's default
behaviour on an unhandled server error is to email every address in the
`ADMINS` setting a report containing the traceback and the request that
triggered it, routed through Django's own logging framework, and a project
can substitute a custom `ExceptionReporter` subclass, which is the
documented extension point third party trackers use to integrate (Django
Software Foundation, Django 5.2 documentation, "Error reporting",
https://docs.djangoproject.com/en/5.2/howto/error-reporting/ verified
2026-08-02). This is a framework shipping the minimal viable version of the
pattern, single instance notification with no cross instance
deduplication, as a built in default, with the deduplicating, multi instance
form available as a plug in.

**Node.js runtime, the 'uncaughtException' process event as the last
resort capture hook.** Every Node.js based exception tracking SDK, and
every hand rolled crash reporter in a Node service, is built on top of this
single documented event, which the Node.js project itself describes as a
crude mechanism intended only as a last resort for synchronous cleanup
before the process exits, explicitly not a mechanism for resuming normal
operation (OpenJS Foundation, Node.js documentation, "process, the
uncaughtException event", https://nodejs.org/api/process.html#event-uncaughtexception
verified 2026-08-02). The runtime documentation's own recommendation, that
an external monitor in a separate process should detect failures and
restart the application, is the process supervision half of a complete
exception handling strategy that the tracking pattern's reporting half does
not replace.

## 10. Consequences

Positive.

- A failure that would otherwise be one anonymous line in a scrolling log
  becomes a single, deduplicated, countable, assignable Issue, which turns
  did anything break from a query someone has to remember to run into a
  notification someone receives.
- Cross service and cross instance correlation becomes possible without any
  individual service knowing about any other service, because every
  Instrumented Service reports to the same Collector.
- Trend visibility over time, first seen, last seen, occurrence rate, lets
  a team distinguish a brand new regression from a long standing known
  issue at a glance, which a raw log cannot do without a query built for
  that specific purpose every time.
- Because the reporter attaches request and environment context
  automatically, an on call engineer frequently has enough information to
  triage without reproducing the failure locally.
- The Issue store becomes a natural place to track resolution state,
  assignment, and regression, functioning as a lightweight bug tracker
  specifically for production failures.

Negative.

- Cost scales with event volume, not with the number of distinct problems,
  so one noisy, high frequency exception can consume a disproportionate
  share of a usage based billing plan or a self hosted Collector's storage
  before anyone notices, see dimension 11.
- The Collector becomes a new operational dependency. A self hosted
  instance needs its own uptime, patching, and scaling story, and a SaaS
  instance is a new third party in the request path's blast radius for
  compliance purposes even when it is off the request's critical path for
  latency purposes.
- Fingerprinting is a heuristic, not a proof. It routinely either
  over merges distinct bugs that happen to share a stack trace shape, or
  fragments one bug into many Issues because a variable element,
  timestamp, request identifier, leaked into the grouping key, see
  dimension 11.
- Rich context capture is in direct tension with data minimization.
  Achieving both requires deliberate scrubbing configuration, which is
  additional work most teams under invest in until an incident forces the
  question, see dimension 17.
- A team that does not actively triage the Issue backlog accumulates a
  growing pile of unresolved entries that erodes trust in the tool faster
  than the tool erodes trust in the team.

## 11. Failure modes and misuse

**Alert fatigue from tracking expected errors.** Symptom. The on call
channel gets paged for validation errors, expired tokens, and other
routine 400 class failures dozens of times a day, and within weeks people
mute the channel entirely, including for the failures that do matter.
Cause. Every exception, including ones the application already handles as
expected client error paths, is routed through the tracker with default
notification settings. Fix. Classify exceptions at the point they are
caught, report unexpected server side failures to the tracker, count
expected client errors as a metric instead, per the non applicability list
in dimension 4, and configure notification thresholds so a new Issue alerts
but a routine, already known one does not re page on every occurrence.

**Cost or storage blowout from one noisy exception.** Symptom. A monthly
bill or a self hosted Collector's disk usage jumps sharply after a deploy,
traced back to a single Issue with an occurrence count in the millions.
Cause. A tight retry loop, a health check endpoint, or a background job
that runs every few seconds started raising the same exception on every
iteration, and nothing rate limited it at the source. Fix. Apply
client side sampling or rate limiting in the Reporter for a given
fingerprint before transmission, not only server side, and treat any single
Issue crossing a defined occurrence threshold as itself an incident worth
paging on, since the exception is very likely firing on the request path
of something important.

**Fingerprint fragmentation.** Symptom. What is obviously one bug, a
database connection timeout, shows up as forty separate Issues, one per
call site, or per pod name, or per request identifier that leaked into the
grouping key. Cause. The default stack trace grouping algorithm included a
frame or a value that varies per occurrence rather than per root cause.
Fix. Apply a custom fingerprint rule that groups on the exception type and
the stable part of the message, per the fingerprint override variant in
dimension 8, and periodically review the Issue list for suspiciously
similar entries that should be merged.

**Fingerprint over merging.** Symptom. One Issue's occurrence graph looks
like a superposition of several unrelated incidents, its first seen
timestamp predates any of the real causes, and resolving what looks like
the root cause does not make the occurrence count drop to zero. Cause. A
generic exception type raised from many unrelated call sites, a bare
`TimeoutError` or `NullPointerException`, groups by type alone when the
stack traces differ only in frames the algorithm ignored. Fix. The opposite
of fragmentation, tighten the fingerprint to include the specific call site
or a distinguishing tag, so the grouping key reflects the root cause
granularity the team cares about.

**Sensitive data captured in the payload.** Symptom. A security or privacy
review finds customer passwords, session tokens, or full request bodies
containing personal data sitting in a third party SaaS tracker's stored
events, discovered months after the SDK was installed with default
settings. Cause. Automatic context capture, request headers, local
variables in stack frames, was enabled without a scrubbing configuration,
and nobody audited what a typical captured event contained before shipping
it. Fix. Configure the Reporter's scrubbing rules before the SDK ever ships
to production, treat this as part of the SDK integration, not a follow up
task, and periodically sample real captured events against the scrubbing
rules rather than trusting the configuration once and forgetting it, per
dimension 17.

**Reporting on the blocking path.** Symptom. Under load, request latency
spikes correlate exactly with a burst of exceptions, and the exceptions
themselves are not obviously related to whatever the request was doing.
Cause. The Reporter was configured, or hand implemented, to transmit
synchronously and wait for the Collector's response before returning
control to the caller, so a slow or unreachable Collector directly slows or
blocks every failing request. Fix. Confirm the Reporter batches and
transmits asynchronously with a bounded queue and a short timeout, per the
dynamics in dimension 7, and load test the failure path, not only the
happy path, before trusting the integration in production.

**Swallowed exceptions that never reach any capture point.** Symptom. A
known bug is visibly affecting users but produces zero Issues in the
tracker. Cause. Application code catches the exception, logs it at a level
nobody watches, and returns a default value, which means neither the
automatic uncaught exception variant nor the middleware variant in
dimension 8 ever sees it, because the exception never leaves the block
where it was caught. Fix. Add an explicit `captureException` call at the
point the exception is caught for any caught exception that represents a
genuine failure rather than an expected condition, which is precisely the
explicit capture variant in dimension 8, and is frequently the coverage gap
teams discover only after relying on automatic capture alone for a while.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Exception Tracking | Log Aggregation alone | Application Metrics (error counters) | Health Check API | APM platform (full distributed tracing plus errors) |
|---|---|---|---|---|---|
| Deduplication of repeated occurrences | Strong, by design | None, every line is separate | Aggregated by label, not by root cause | Not applicable | Strong, same mechanism as a dedicated tracker |
| Push notification on new failure | Strong, configurable per Issue | Requires a saved query and an alert built on top | Requires a threshold alert on the counter | Signals liveness, not root cause | Strong, usually bundled |
| Root cause detail, stack trace, local context | Strong | Present if logged, unstructured | None, a metric has no stack trace | None | Strong, plus request level trace context |
| Answers is this instance alive | Not its job | Not its job | Not its job | Its entire job | Contributes but is not the primary answer |
| Answers why is this request slow | Not its job | Poor, requires manual correlation | Poor, a duration histogram at best | Not its job | Strong, that is a trace's job |
| Cost driver | Per event or per Issue, spikes on noisy bugs | Per byte ingested and retained, spikes on log volume | Per time series, spikes on the number of distinct label combinations | Cheap, low frequency polling | Highest, bundles tracing plus metrics plus errors |
| Setup cost | Low, one SDK per service | Low if already centralizing logs | Low, counters are cheap to add | Low, one endpoint | High, requires trace context propagation across services |
| Best fit | Rare, high value, unexpected failures | Forensic search after the fact, audit trails | High frequency, expected error rates | Orchestrator restart and routing decisions | Teams that need errors and latency correlated in one view |

Reading of the table. Exception tracking wins where the failure is rare
enough to be lost in aggregate metrics and specific enough to need a stack
trace, not a counter. Log aggregation wins where the question is
retrospective and exploratory rather than notify me now. Application
metrics win where the failure is frequent and the question is rate over
time, not root cause. A health check API answers a different question
entirely and is not a substitute at all, only a frequent companion. A full
APM platform subsumes exception tracking's job when a team can afford its
cost and complexity, and is overkill when the team's real gap is only that
failures are not found fast enough.

## 13. Related and incompatible patterns

- **Log Aggregation.** The closest relative and the pattern most often
  confused with this one. Log Aggregation centralizes every log line from
  every instance into one searchable store with no deduplication or
  notification logic. Richardson's own catalog entry links the two
  directly, stating that exceptions should be logged as well as reported to
  a tracking service (Chris Richardson, microservices.io, "Pattern.
  Exception tracking", https://microservices.io/patterns/observability/exception-tracking.html
  verified 2026-08-02), which is a composition, not a substitution, log
  aggregation gives forensic depth after the fact, exception tracking gives
  immediate, deduplicated notification a person can act on.
- **Application Metrics.** Complementary at a different granularity. A
  counter labelled by exception class or HTTP status code answers what the
  current error rate is, which exception tracking's per Issue view does
  not answer well in aggregate. A team typically wants both, a metrics
  dashboard for rate and trend, a tracker for individual root cause detail,
  and the failure modes in dimension 11 around routing expected errors into
  the tracker are exactly the case where the two should have been kept
  separate.
- **Circuit Breaker.** Composes at the point of failure. A circuit breaker
  decides what a caller does after a downstream call fails repeatedly, open
  the circuit, fail fast, fall back. Exception tracking decides what a human
  learns about that same failure. A circuit breaker's own state transitions,
  closed to open, are frequently themselves worth reporting as an event so
  the team learns a dependency degraded even when the breaker successfully
  protected the caller from cascading failure.
- **Health Check API.** Answers a different question and is not a
  substitute. A health check tells an orchestrator whether an instance is
  fit to receive traffic right now. Exception tracking tells a human what
  went wrong inside a request that instance already handled. A service can
  be perfectly healthy by its health check's definition while still
  producing a steady stream of Issues worth investigating.
- **Microservice Chassis.** A common host for the wiring rather than a
  peer pattern. A chassis library that every service in an organization
  builds on is the natural place to install the Reporter once, with
  consistent scrubbing rules and context tags, rather than every service
  team configuring the SDK independently and inconsistently, which is where
  the privacy gaps in dimension 11 tend to originate.
- **Distributed Tracing.** Composes well and is increasingly bundled by
  vendors into the same product, but the two started as, and remain,
  distinct concerns. Tracing answers latency and causality across service
  boundaries for a single request. Exception tracking answers which known
  failure recurred, and how often. A trace identifier attached as context
  on a captured exception is one of the highest value integrations between
  the two, letting an engineer jump from an Issue straight to the full
  request trace that produced it.
- **Alerting or on call paging systems.** A downstream consumer, not a
  conflicting pattern. The tracking service's own notification is normally
  routed through a paging system rather than replacing it, so the same
  escalation policy, quiet hours, and rotation logic the team already has
  for infrastructure alerts also governs exception notifications.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently only logs exceptions.

1. Confirm the codebase raises structured exceptions with a real type and
   message rather than string based error signalling everywhere, since
   the deduplication algorithm needs a stack trace and a type to group on.
   Where error handling is ad hoc, this step is genuinely refactoring the
   error handling itself first, not merely adding a new dependency.
2. Pick one low traffic, low risk service as the pilot. Install the
   Reporter with the middleware or interceptor variant from dimension 8,
   scoped to that one service, before touching anything else.
3. Configure scrubbing rules before the first real event is captured, not
   after. Send a handful of deliberately triggered test exceptions and
   inspect exactly what payload the Collector received, per the fix in
   dimension 11 for sensitive data capture.
4. Turn off, or deliberately configure, notification for expected
   client error exceptions before enabling capture broadly, so the pilot
   does not immediately train the team to ignore the new tool, per
   dimension 11.
5. Once the pilot's Issue stream looks trustworthy, roll the same Reporter
   configuration out through the shared Microservice Chassis if one
   exists, so every subsequent service inherits consistent capture and
   scrubbing rather than each team reconfiguring it from scratch.
6. Add the explicit capture variant at the specific handler blocks the
   team already knows swallow real failures, since automatic capture alone
   systematically misses these, per dimension 11.
7. Establish a triage cadence, a named owner reviewing new Issues on a
   fixed schedule, before calling the rollout complete. The mechanism
   without the process is the misuse case in dimension 11.

Removing or scaling back the pattern when it stops earning its place.
Signals that removal or reduction is warranted include a Collector whose
Issue backlog nobody has triaged in months, a cost line item that keeps
growing without a corresponding drop in production incidents, or a service
being decomposed to the point that a single instance and a watched log are
genuinely sufficient again.

1. Audit which Issues have driven a fix or a deliberate ignore decision in
   the last quarter, versus which have simply accumulated. A backlog that
   is mostly unread is a signal the tool has stopped being trusted, per
   dimension 11, and the fix might be re triaging rather than removing.
2. Where removal is genuinely warranted, for example a service being
   retired or consolidated into one that already has coverage, disable
   the Reporter's transmission first while leaving local logging intact,
   confirming nothing downstream depends on the Issue stream continuing.
3. Remove the SDK dependency and any chassis level wiring for that
   service, and confirm the service's remaining logging still captures
   enough context that a future incident is diagnosable without it.
4. If a Collector instance is being decommissioned entirely rather than
   scaled back for one service, export or archive the historical Issue
   data first, since resolved issue history is frequently the only record
   of what classes of bug a system has had.

## 15. Testing and verification

Easier because of the pattern.

- Whether a given code path correctly reports an exception becomes directly
  assertable. A test can inject a fake Reporter, trigger the failing path,
  and assert `captureException` was called with the expected exception
  type and context, which turns whether a failure gets noticed in
  production into a unit testable property rather than something only
  discovered by triggering the real failure in production and checking.
- Regression detection improves at the system level, since a re occurring
  Issue with a rising occurrence count after a deploy is itself a signal a
  release process can gate on, independent of whatever the automated test
  suite covers.

Harder because of the pattern.

- The Reporter's asynchronous, best effort transmission is hard to assert
  against in an end to end test, since a test cannot reliably wait for a
  background flush without either a real network call to a test Collector
  or a synchronous test hook the production code path does not otherwise
  have.
- Scrubbing correctness is a negative assertion, the test has to prove a
  field is absent from a captured payload, which is easy to get wrong by
  testing the wrong payload shape or missing a nested field the scrubbing
  rule does not reach.

Techniques that apply.

- **Fake Reporter injection.** Provide a test double implementing the
  Reporter's capture interface that records calls in memory instead of
  transmitting them, and inject it in place of the real SDK client for
  unit and integration tests. This is the primary technique and needs no
  network access or test Collector instance.
- **Contract test against a local Collector.** For confidence that the
  real SDK's wire format matches what the Collector expects, run the
  real SDK against a locally running instance of the Collector, or a
  minimal HTTP server that asserts on the ingestion payload shape, at
  least once, typically in a slower integration test tier rather than on
  every unit test run.
- **Payload snapshot test for scrubbing.** Capture a real exception
  containing every field the scrubbing configuration is meant to remove,
  serialize what would actually get transmitted, and assert on the
  serialized shape rather than only on the scrubbing configuration's
  syntax being valid, which catches the case where a scrubbing rule is
  correctly configured but does not reach a nested or renamed field.
- **Fault injection on the Collector path.** Deliberately make
  the Collector unreachable, via a firewall rule, a wrong endpoint, or a
  stopped test double, and assert the request path under test still
  completes successfully and within its normal latency budget, which is
  the direct test for the blocking path failure mode in dimension 11.

## 16. Observability signals

This dimension is close to entirely engineering judgement, since the
pattern is itself an observability mechanism, and what makes an
observability mechanism healthy is a matter of operating experience rather
than a single documented standard.

What to record about the tracking pipeline itself, distinct from what the
tracking pipeline records about the application.

- A count of exceptions successfully transmitted from the Reporter,
  labelled by service and by exception type, so a drop to zero after a
  deploy is itself detectable, which otherwise silently blinds the team to
  every subsequent real failure.
- A count of transmission failures or dropped events at the Reporter,
  which is the signal that the local queue is overflowing or the Collector
  is unreachable, before anyone notices the absence of expected Issues.
- The rate of new, previously unseen fingerprints appearing per unit time,
  which is a leading indicator of a bad deploy independent of whatever
  aggregate error rate metric the team already watches.
- Occurrence count growth rate per Issue, since a sudden slope change on an
  existing Issue, not only a brand new one, is frequently the first sign a
  dependency degraded.
- Time from an Issue's first occurrence to acknowledgment or assignment,
  which measures whether the triage process from dimension 4 and dimension
  11 is functioning, distinct from whether the technical pipeline is
  functioning.

A healthy instance on a dashboard. New fingerprints appear at a low, roughly
steady background rate that correlates with deploy frequency rather than
spiking independently of deploys. The Reporter's own transmission success
rate sits close to one hundred percent, with dropped event counts near
zero. The median time to acknowledgment on new Issues is short enough that
the team trusts the notification path is being watched.

A failing instance. Reporter transmission success drops sharply after an
infrastructure change, meaning every subsequent real failure is invisible
until someone notices the gap by other means. A single Issue's occurrence
count grows without bound over hours, which is the noisy exception failure
mode from dimension 11 and is worth its own alert threshold, since the
Issue is very likely sitting on an important, high traffic path. The rate
of brand new fingerprints per deploy trends upward release over release
with no corresponding increase in test coverage, which is a slow moving
quality regression signal distinct from any single incident.

## 17. Security and privacy implications

Exception tracking is the observability pattern with the sharpest privacy
implication of the ones in this catalog family, because its entire value
proposition is capturing as much context as possible about the exact
moment something went wrong, and that context routinely includes the
customer's own data.

**Sensitive data in captured context.** Local variables in a stack frame,
request headers, request bodies, and query parameters are the highest
value debugging context and also the most likely place to find a password,
a session token, a card number, or personal data that a company has
contractual or regulatory obligations around. Django's own error report
includes the full traceback and request details by default (Django
Software Foundation, Django 5.2 documentation, "Error reporting",
https://docs.djangoproject.com/en/5.2/howto/error-reporting/ verified
2026-08-02), which is exactly the kind of default a team needs to review
rather than assume is already safe. Configure and test scrubbing rules
before the SDK reaches production, per the fix in dimension 11, and treat
a captured event as sensitive data by default until proven otherwise by
inspection, not the reverse.

**Third party data residency and processor status.** Sending exception data
to a hosted SaaS Collector makes that vendor a data processor under most
privacy regimes if any personal data reaches the payload, which carries
its own contractual and jurisdictional obligations, data processing
agreements, regional data residency requirements, breach notification
terms, independent of anything the application code does correctly.
Self hosting the Collector, or restricting which services and which fields
are permitted to report at all, are the two options available when this
matters more than the convenience of a hosted product.

**Denial of service and cost amplification through the reporting path
itself.** An attacker who can trigger a specific exception on demand, a
malformed request that reliably raises a parsing error, for instance, can
drive the tracker's event volume and cost far past normal levels by
hitting that path repeatedly, which is a distinct and often overlooked
cost based denial of service surface separate from the application's own
rate limiting. Client side sampling or rate limiting per fingerprint, the
same fix as the noisy exception failure mode in dimension 11, doubles as a
defence against this.

**Access control on the Issue store.** The Collector's Issue view is a
concentrated, searchable archive of exactly the moments the application
misbehaved, which is valuable to an attacker performing reconnaissance,
stack traces reveal internal file paths, dependency versions, and
sometimes configuration values that leaked into an exception message.
Restrict who can read the Collector's dashboard to the same standard
applied to production logs and infrastructure credentials, not a lighter
standard, since it frequently holds a superset of what the logs alone
would reveal once request context is attached.

## 18. References

1. Chris Richardson. *microservices.io*. "Pattern. Exception tracking".
   https://microservices.io/patterns/observability/exception-tracking.html
   Verified 2026-08-02. Source for the pattern name, its Observability
   category placement, the stated problem and solution, and the linkage to
   log aggregation in dimension 13.
2. Sentry. *Sentry documentation*. "Grouping and Fingerprints".
   https://docs.sentry.io/concepts/data-management/event-grouping/
   Verified 2026-08-02. Source for the default fingerprint priority order
   and the custom fingerprint override behaviour in dimension 8.
3. Sentry. *Customer stories*. https://sentry.io/customers/ Verified
   2026-08-02. Source for the named production use in dimension 9.
4. Microsoft. *Azure Monitor documentation*. "Diagnose exceptions in
   ASP.NET web apps with Application Insights".
   https://learn.microsoft.com/en-us/azure/azure-monitor/app/asp-net-exceptions
   Verified 2026-08-02. Source for the `UnhandledExceptionTelemetryModule`
   and `TrackException` production use in dimension 9 and the framework
   integrated variant in dimension 8.
5. Django Software Foundation. *Django 5.2 documentation*. "Error
   reporting". https://docs.djangoproject.com/en/5.2/howto/error-reporting/
   Verified 2026-08-02. Source for the `AdminEmailHandler` default
   behaviour, the `DEFAULT_EXCEPTION_REPORTER` extension point, and the
   sensitive data by default caution in dimension 17.
6. OpenJS Foundation. *Node.js documentation*. "process, the
   uncaughtException event".
   https://nodejs.org/api/process.html#event-uncaughtexception Verified
   2026-08-02. Source for the global uncaught handler variant in
   dimension 8, its last resort framing, and the production use in
   dimension 9.
7. Python Software Foundation. *Python 3 documentation*. "sys.excepthook".
   https://docs.python.org/3/library/sys.html#sys.excepthook Verified
   2026-08-02. Source for the Python global uncaught handler mechanism used
   in the code example and dimension 8.
8. Oracle. *Java SE 21 API Specification*. `java.lang.Thread`,
   `setDefaultUncaughtExceptionHandler`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html
   Verified 2026-08-02. Source for the Java global uncaught handler
   mechanism used in the code example and dimension 8.

## Code examples

Three languages where a Reporter is idiomatically built differently.
TypeScript on Node.js shows the middleware variant plus the global
uncaughtException safety net. Python shows sys.excepthook plus the
explicit capture variant inside a caught exception. Java shows the
Thread.UncaughtExceptionHandler variant plus a minimal fingerprinting
Collector stub to make the grouping behaviour concrete and runnable without
a real network dependency. All three were compiled or run locally.

### TypeScript

```typescript
interface CapturedEvent {
  fingerprint: string;
  type: string;
  message: string;
  context: Record<string, unknown>;
}

class FakeCollector {
  private issues = new Map<string, { count: number; sample: CapturedEvent }>();

  ingest(event: CapturedEvent): void {
    const existing = this.issues.get(event.fingerprint);
    if (existing) {
      existing.count += 1;
    } else {
      this.issues.set(event.fingerprint, { count: 1, sample: event });
    }
  }

  report(): string {
    const lines: string[] = [];
    for (const [fp, issue] of this.issues) {
      lines.push(`${fp} seen ${issue.count}x. ${issue.sample.message}`);
    }
    return lines.join("\n");
  }
}

class Reporter {
  constructor(private readonly collector: FakeCollector, private readonly service: string) {}

  captureException(err: Error, context: Record<string, unknown> = {}): void {
    const fingerprint = `${err.constructor.name}.${(err.stack ?? "").split("\n")[1] ?? ""}`;
    this.collector.ingest({
      fingerprint,
      type: err.constructor.name,
      message: err.message,
      context: { service: this.service, ...context },
    });
  }
}

function middleware(reporter: Reporter, handler: (path: string) => void) {
  return (path: string) => {
    try {
      handler(path);
    } catch (err) {
      reporter.captureException(err as Error, { path });
      throw err;
    }
  };
}

const collector = new FakeCollector();
const reporter = new Reporter(collector, "order-service");

process.on("uncaughtException", (err) => {
  reporter.captureException(err, { source: "uncaughtException" });
  process.exitCode = 1;
});

function riskyHandler(path: string): void {
  if (path === "/orders/bad") {
    throw new TypeError("cannot read property total of undefined");
  }
}

const wrapped = middleware(reporter, riskyHandler);
for (const path of ["/orders/bad", "/orders/bad", "/orders/ok"]) {
  try {
    wrapped(path);
  } catch {
    // stands in for the response layer, which would return 500 here
  }
}

console.log(collector.report());
```

### Python

```python
import sys
import traceback
from collections import Counter


class FakeCollector:
    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()
        self.samples: dict[str, str] = {}

    def ingest(self, fingerprint: str, message: str) -> None:
        self.counts[fingerprint] += 1
        self.samples.setdefault(fingerprint, message)

    def report(self) -> str:
        return "\n".join(
            f"{fp} seen {count}x. {self.samples[fp]}"
            for fp, count in self.counts.items()
        )


class Reporter:
    def __init__(self, collector: FakeCollector, service: str) -> None:
        self.collector = collector
        self.service = service

    def capture_exception(self, exc: BaseException) -> None:
        tb = traceback.extract_tb(exc.__traceback__)
        frame = tb[-1] if tb else None
        location = f"{frame.filename}#{frame.lineno}" if frame else "unknown"
        fingerprint = f"{type(exc).__name__}.{location}"
        self.collector.ingest(fingerprint, f"[{self.service}] {exc}")


collector = FakeCollector()
reporter = Reporter(collector, "payment-service")


def excepthook(exc_type, exc_value, exc_tb):
    reporter.capture_exception(exc_value)
    sys.__excepthook__(exc_type, exc_value, exc_tb)


sys.excepthook = excepthook


def charge_card(amount: float) -> None:
    if amount < 0:
        raise ValueError("amount must not be negative")


def process_payment(amount: float) -> bool:
    try:
        charge_card(amount)
        return True
    except ValueError as exc:
        # explicit capture variant, this exception is handled right here
        reporter.capture_exception(exc)
        return False


for amt in [-5.0, -5.0, 10.0]:
    process_payment(amt)

print(collector.report())
```

### Java

```java
import java.util.HashMap;
import java.util.Map;

final class CapturedEvent {
    final String fingerprint;
    final String message;

    CapturedEvent(String fingerprint, String message) {
        this.fingerprint = fingerprint;
        this.message = message;
    }
}

final class FakeCollector {
    private final Map<String, Integer> counts = new HashMap<>();
    private final Map<String, String> samples = new HashMap<>();

    void ingest(CapturedEvent event) {
        counts.merge(event.fingerprint, 1, Integer::sum);
        samples.putIfAbsent(event.fingerprint, event.message);
    }

    String report() {
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, Integer> e : counts.entrySet()) {
            sb.append(e.getKey())
              .append(" seen ")
              .append(e.getValue())
              .append("x. ")
              .append(samples.get(e.getKey()))
              .append("\n");
        }
        return sb.toString();
    }
}

final class Reporter {
    private final FakeCollector collector;
    private final String service;

    Reporter(FakeCollector collector, String service) {
        this.collector = collector;
        this.service = service;
    }

    void captureException(Throwable t) {
        StackTraceElement[] frames = t.getStackTrace();
        String site = frames.length > 0 ? frames[0].toString() : "unknown";
        String fingerprint = t.getClass().getSimpleName() + "." + site;
        collector.ingest(new CapturedEvent(fingerprint, "[" + service + "] " + t.getMessage()));
    }
}

public final class ExceptionTrackingDemo {
    public static void main(String[] args) {
        FakeCollector collector = new FakeCollector();
        Reporter reporter = new Reporter(collector, "order-service");

        Thread.setDefaultUncaughtExceptionHandler((thread, ex) -> {
            reporter.captureException(ex);
            System.err.println("uncaught on " + thread.getName() + ". " + ex);
        });

        for (int i = 0; i < 3; i++) {
            try {
                processOrder(i);
            } catch (IllegalStateException ex) {
                // explicit capture variant, handled right here
                reporter.captureException(ex);
            }
        }

        System.out.print(collector.report());
    }

    static void processOrder(int id) {
        if (id < 2) {
            throw new IllegalStateException("order " + id + " has no line items");
        }
    }
}
```
