---
name: RED Method
slug: red-method
family: 22-observability
category: Structural
aliases: [Rate Errors Duration]
first_described: 'Tom Wilkie, 2015, presented while at Weaveworks and later at Grafana Labs'
maturity: canonical
related: [use-method, structured-logging, correlation-id]
incompatible_with: []
verified: 2026-08-22
---

# RED Method

## 1. Name, aliases, and lineage

RED Method. The name is an acronym for its three signals, Rate, Errors, Duration, and it is sometimes written out as Rate Errors Duration in full.

Tom Wilkie coined it in 2015. Grafana Labs' own engineering blog, published by the company Wilkie later joined, describes the origin directly. he created it after a new colleague asked what his monitoring philosophy was, and framed it against Brendan Gregg's USE Method, saying the USE Method does not really apply to services, it applies to hardware and network disks, so he wanted a microservices oriented monitoring philosophy and came up with the RED Method (https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/). His own slide deck from that period states the method in the fewest possible words, for every service, monitor request, rate, the number of requests per second, errors, the number of those requests that are failing, duration, the amount of time those requests take (https://www.slideshare.net/kausalco/the-red-method-how-to-instrument-your-services). InfoWorld's independent coverage traces its lineage further back, describing it as derived from practices established at Google known as the four golden signals, developed by Google's own site reliability engineering team (https://www.infoworld.com/article/2270578/the-red-method-a-new-strategy-for-monitoring-microservices.html).

## 2. Problem and context

A team running many request driven services, each built by a different group of engineers, ends up with a different, inconsistent set of dashboards and metrics per service. One team graphs average latency, another graphs a raw request count with no error breakdown, and a third has no dashboard at all until something breaks. When an incident spans several services, an engineer moving from one dashboard to the next has to relearn what each one shows before they can even start comparing them.

The RED Method solves this by naming exactly three signals every request driven service should expose, in the same shape, every time. Rate, how many requests the service is handling. Errors, how many of those requests are failing. Duration, how long they take. With the same three signals defined the same way across every service, one dashboard template serves the whole fleet, and an engineer who has seen one service's RED dashboard already knows how to read every other service's dashboard too.

## 3. Forces

- A consistent, reusable dashboard template across many services is only possible if every service defines Rate, Errors, and Duration the same way, which means the definitions have to be agreed and enforced, not left to each team's own judgement.
- Three signals are simpler to build and read than the four golden signals they are derived from, but the fourth, Saturation, is deliberately left out, so RED alone says nothing about whether the underlying machine or resource a service runs on is close to its own limit.
- Duration needs to be captured as a distribution, not a single average, since Prometheus's own guidance is explicit that aggregating the precomputed quantiles from a summary across multiple service instances rarely makes sense, and recommends histograms instead so percentiles can be computed correctly after aggregation (https://prometheus.io/docs/practices/histograms/).
- Reporting Rate and Errors per label, for example per HTTP route or per status code, gives more useful detail, but every additional label multiplies the number of distinct time series a metrics backend has to store, so the label set has to be chosen deliberately rather than added without limit.
- RED assumes the unit of work is a request with a clear start, end, and outcome, which is a genuine assumption, not a universal one, and it does not transfer cleanly to workloads that do not have that shape.

## 4. Applicability and non-applicability

### When it applies

Use the RED Method for any request driven service, an HTTP API, an RPC service, or anything else that receives discrete requests with a clear start, end, and success or failure outcome. It is most valuable across a fleet of many such services, where the payoff is one dashboard template that works the same way everywhere rather than a bespoke dashboard per service.

### When it does not apply (non-applicability)

Skip it, or reach for the USE Method instead, for infrastructure and hardware resources, CPU, disk, memory, and network, which are not request driven and do not have Rate, Errors, or Duration in the sense this pattern defines them. ClickHouse's own engineering resource hub states this limitation plainly, RED fits poorly for batch jobs and streaming pipelines, where requests are not the natural unit of work (https://clickhouse.com/resources/engineering/red-use-methods), and the same source states the USE Method is the better fit for exactly that infrastructure and resource layer.

## 5. Structure

- Rate metric. a counter incremented once per request received, from which a per-second rate can be computed over a time window.
- Errors metric. a counter incremented once per request that fails, or a ratio derived from comparing failed requests against total requests, usually broken down by an outcome label such as a status code.
- Duration metric. a histogram recording how long each request takes, chosen over a plain average specifically because it supports computing percentiles after aggregating across many service instances.
- Instrumentation middleware. the shared library or framework hook that emits all three metrics consistently, so an individual engineer does not have to remember to wire each one up by hand for every new service.
- Dashboard template. the reusable set of panels that queries Rate, Errors, and Duration the same way for any service that follows the convention.

## 6. ASCII structure diagram

```
  Request arrives at a service
        |
        v
  Instrumentation middleware
        |
        +----> increments Rate counter
        |
        v
  Service processes the request
        |
        v
  On completion
        +----> records Duration into a histogram
        +----> increments Errors counter if the outcome failed
        |
        v
  Dashboard template queries all three
  (same query shape for every service)
```

## 7. Dynamics

1. A request arrives at a service, and the instrumentation middleware increments the Rate counter for that service before any business logic runs.
2. The service processes the request as it normally would, with no change to its own logic.
3. When the request completes, the middleware records how long it took into the Duration histogram, and, if the outcome was a failure, increments the Errors counter.
4. A query engine such as Prometheus computes a per-second rate from the Rate counter using its own rate function, which calculates the per-second average rate of increase over a range vector and automatically adjusts for counter resets such as a service restart (https://prometheus.io/docs/prometheus/latest/querying/functions/).
5. The same query engine computes latency percentiles from the Duration histogram using a quantile function over the recorded buckets, giving a p50, p95, or p99 figure rather than a single average that hides tail latency (https://prometheus.io/docs/prometheus/latest/querying/functions/).
6. The dashboard template renders all three, Rate, Errors, Duration, using the identical query shape for every service that follows the same instrumentation convention, so a new service gets a working dashboard the moment it adopts the convention, with no per-service customization needed.

## 8. Implementation variants

- Prometheus and Grafana. the canonical implementation, using a counter for Rate, a counter or ratio for Errors, and a histogram for Duration, queried with rate and histogram_quantile, and rendered through a shared Grafana dashboard template, the environment the method itself was created in.
- Datadog APM dashboards. Datadog's own documentation instructs building the same three signals through its tracing metrics, a hit and error count widget for Rate and Errors, and a latency percentile widget such as the 99th percentile of request duration for the Duration signal (https://docs.datadoghq.com/tracing/guide/apm_dashboard/), showing the pattern is not tied to any single vendor.
- A minimal, framework only implementation. for a small stack with no full APM system, the same three signals can be emitted with a lightweight metrics library, a counter, an error counter, and a histogram, without adopting an entire observability platform first.

## 9. Known production uses

- Grafana Labs documents and promotes the RED Method directly through its own engineering blog, the company Tom Wilkie joined after creating the method, and through GrafanaCon talks describing its use (https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/).
- Datadog's own tracing documentation instructs customers to build an application performance monitoring dashboard around request rate, error count, and latency percentile widgets, independent of the Grafana ecosystem the method originated in (https://docs.datadoghq.com/tracing/guide/apm_dashboard/).
- The wider Prometheus and Grafana community has adopted the RED Method as a standard, reusable dashboard shape for request driven services, following the same rate and histogram_quantile query pattern the method's own creator used (https://prometheus.io/docs/prometheus/latest/querying/functions/).

## 10. Consequences

### Benefits

- One dashboard template works for every request driven service in a fleet, so a new service gets a working, familiar dashboard the moment it adopts the shared instrumentation convention.
- The three signals map directly to what a user of the service actually experiences, how much traffic is flowing, how much of it is failing, and how long it takes, rather than to an internal implementation detail only the service's own team would understand.
- An engineer who already knows how to read one service's RED dashboard can read every other service's RED dashboard immediately, cutting the time it takes to move across a fleet during an incident.

### Costs

- Duration has to be captured as a histogram to support correct cross instance percentile computation, which costs more in instrumentation effort and stored data than a single running average would.
- RED alone says nothing about the resource layer underneath a service, so a slowdown caused by the underlying machine running out of a resource is invisible to a RED dashboard and needs the USE Method alongside it.
- Enforcing a consistent definition of what counts as a request and what counts as an error across every team takes ongoing discipline, and a service that defines either differently quietly breaks the fleet wide comparability the method is meant to provide.

## 11. Failure modes and misuse

- The method is applied to a batch job, a streaming pipeline, or another workload with no natural request unit, producing a dashboard with metrics that do not map to anything real, exactly the fit ClickHouse's own engineering resource hub names as a genuine limitation, not a misuse it invented (https://clickhouse.com/resources/engineering/red-use-methods).
- Duration is instrumented as a simple running average rather than a histogram, which hides tail latency entirely, and, if it is instrumented as a pre aggregated summary and then combined across service instances, produces a number that does not represent any real percentile, the exact problem Prometheus's own histogram guidance warns against (https://prometheus.io/docs/practices/histograms/).
- A team treats RED as sufficient on its own and never checks the resource layer, so a slowdown whose real cause is a saturated resource is investigated entirely at the service level and never found, because that signal was never in scope for this method to begin with.
- Rate, Error, or Duration labels are broken out by a value that can take on very many distinct values, such as a raw identifier rather than a normalized route template, which multiplies the number of distinct time series far beyond what the dashboard or its backend was built to hold.
- Two services define Errors differently, one counting only server side failures and another also counting client side validation failures as errors, so a fleet wide error rate comparison between them is misleading even though both dashboards look identical.

## 12. Trade-off matrix

| Dimension | RED Method | USE Method | Four golden signals |
|---|---|---|---|
| Signal count | 3, Rate, Errors, Duration | 3, Utilization, Saturation, Errors | 4, Latency, Traffic, Errors, Saturation |
| Primary scope | Request driven services | Hardware and infrastructure resources | User facing systems generally |
| Covers resource saturation | No | Yes, its central signal | Yes |
| Best fit for a fleet of microservices | Very good | Poor, does not apply to services | Good, but heavier to instrument fully |
| Best fit for CPU, disk, memory, network | Poor | Very good | Partial, via Saturation only |

## 13. Related and incompatible patterns

Related to the USE Method, its direct counterpart, and the two are commonly used together rather than as alternatives, RED for the request driven services and USE for the resources those services run on, exactly the split Grafana's own account of the method's origin describes (https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/).

Related to Structured Logging, since the label values attached to Rate, Errors, and Duration metrics are only as consistent and queryable as the field naming discipline structured logging depends on, and both patterns share the same risk around a label or field taking on very many distinct values.

Related to Correlation ID, since correlating a Duration outlier or an error spike back to the specific requests that caused it depends on the same request scoped identifier that pattern defines.

Not incompatible with anything in this catalog. it is one leg of a fuller observability setup, not a replacement for the others.

## 14. Refactoring path in and out

To introduce it into a fleet of services with no consistent monitoring today, start with one pilot service. add the Rate counter, the Errors counter, and the Duration histogram through shared instrumentation middleware rather than hand writing the metrics calls in the service's own code, then build the dashboard template against that one service. Once the template is proven, roll the same middleware out to every other request driven service in the fleet, so each one inherits a working dashboard immediately on adoption rather than needing its own bespoke setup.

Removing it entirely is rare for a request driven service, since the ongoing cost is small relative to the debugging value, but a service that stops being request driven, for example one that is refactored into a purely event driven or batch oriented shape, should drop RED style instrumentation and adopt whichever pattern actually fits its new shape instead, rather than keeping metrics that no longer map to anything real.

## 15. Testing and verification

Assert that the Rate counter increments exactly once per request handled, neither more nor less, including under concurrent load, so a race in the instrumentation code cannot silently under or over count traffic. Assert that the Errors counter increments only for outcomes the team has agreed constitute a genuine failure, and stays flat for outcomes that are not, so the definition stays consistent as the codebase changes around it. Load test the Duration histogram directly, sending a known distribution of request latencies and asserting the computed p50, p95, and p99 percentiles match what was actually sent, catching a bucket boundary or aggregation bug before it reaches a real dashboard. Test that the shared dashboard template renders correctly for a newly onboarded service using only the standard instrumentation, with no custom configuration required.

## 16. Observability signals

Watch the Rate trend over time for traffic anomalies, both a sudden drop, which often means something upstream is failing before it even reaches this service, and a sudden spike, which may be legitimate or may itself be the cause of a later problem. Watch the Error ratio, not the raw Error count alone, since a raw count naturally rises and falls with Rate and can hide a real regression inside a busy period. Watch Duration at the percentile level, p95 and p99 specifically, since an average can stay flat while a real portion of users experience a genuine slowdown. The single most useful compound signal this method produces is Errors rising while Rate stays flat, which is a strong signal of a real regression in the service itself rather than an artifact of changing traffic.

## 17. Security and privacy implications

Metrics themselves, aggregate counters and histogram buckets, carry low direct risk, since they describe volumes and distributions rather than the content of any individual request. The risk sits in the labels attached to them. a label populated from a raw, user supplied value, an account identifier, an email address, or an unnormalized URL path, both multiplies the number of distinct time series far past what the system is designed to hold and can leak identifying information into a metrics backend that was never meant to store it. Always use a normalized route template or a small, agreed set of label values, never a raw identifier or free text, when breaking Rate, Errors, or Duration down by a dimension.

## 18. References

1. Grafana Labs engineering blog. Documents Tom Wilkie coining the RED Method in 2015 and defines Rate, Errors, Duration in his own words. https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/, verified 2026-08-22.
2. Tom Wilkie's own slide deck, published by Kausal. States the method in its original form, for every service, monitor request, rate, errors, duration. https://www.slideshare.net/kausalco/the-red-method-how-to-instrument-your-services, verified 2026-08-22.
3. InfoWorld. Independent coverage tracing the method's lineage to Google's four golden signals. https://www.infoworld.com/article/2270578/the-red-method-a-new-strategy-for-monitoring-microservices.html, verified 2026-08-22.
4. Prometheus documentation, query functions. Defines rate and histogram_quantile, the two functions the RED Method's dashboards are typically built on. https://prometheus.io/docs/prometheus/latest/querying/functions/, verified 2026-08-22.
5. Prometheus documentation, histograms. Explains why a histogram, not a summary or a plain average, is needed for correct cross instance percentile computation. https://prometheus.io/docs/practices/histograms/, verified 2026-08-22.
6. ClickHouse engineering resource hub. Explicit comparison of the RED and USE methods, and the documented limitation that RED fits poorly for batch jobs and streaming pipelines. https://clickhouse.com/resources/engineering/red-use-methods, verified 2026-08-22.
7. Datadog documentation, application performance monitoring dashboards. An independent, named vendor instructing customers to build a rate, error, and latency dashboard. https://docs.datadoghq.com/tracing/guide/apm_dashboard/, verified 2026-08-22.
8. Google SRE book, monitoring distributed systems. Defines the four golden signals, Latency, Traffic, Errors, Saturation, the source the RED Method's three signals are derived from. https://sre.google/sre-book/monitoring-distributed-systems/, verified 2026-08-22.

**Evidence grade.** high

**Most solid findings.** The origin and the exact definition of Rate, Errors, and Duration (source 1, 2) trace to Tom Wilkie's own words, a blog post from his eventual employer and his own original slide deck, not a secondary paraphrase. The RED-versus-USE comparison and the batch and streaming limitation (source 6) come from a single engineering source that states both clearly. The histogram-over-average guidance (source 5) is quoted directly from Prometheus's own documentation.

**Unverified or unclear.** The original weave.works blog post where Wilkie first published the method could not be verified live. the domain has been abandoned and now redirects to an unrelated site. The origin claim in dimension 1 is instead sourced from Grafana's own later account plus Wilkie's own slide deck, both independently checkable, but a reader who wants the very first publication should be aware the original URL no longer resolves to it.

## Code examples

### Go, RED metrics with net/http middleware

```go
package main

import (
	"net/http"
	"sync"
	"time"
)

type redMetrics struct {
	mu        sync.Mutex
	requests  map[string]int
	errors    map[string]int
	durations map[string][]time.Duration
}

func newRedMetrics() *redMetrics {
	return &redMetrics{
		requests:  map[string]int{},
		errors:    map[string]int{},
		durations: map[string][]time.Duration{},
	}
}

func (m *redMetrics) record(route string, d time.Duration, failed bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.requests[route]++
	if failed {
		m.errors[route]++
	}
	m.durations[route] = append(m.durations[route], d)
}

func redMiddleware(m *redMetrics, route string, next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rec := &statusRecorder{ResponseWriter: w, status: 200}
		next(rec, r)
		m.record(route, time.Since(start), rec.status >= 500)
	}
}

type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (s *statusRecorder) WriteHeader(code int) {
	s.status = code
	s.ResponseWriter.WriteHeader(code)
}
```

### Python, RED metrics with a simple decorator

```python
import time
from collections import Counter, defaultdict

request_count = Counter()
error_count = Counter()
durations = defaultdict(list)


def red_instrumented(route):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.monotonic()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                error_count[route] += 1
                raise
            finally:
                request_count[route] += 1
                durations[route].append(time.monotonic() - start)

        return wrapper

    return decorator


@red_instrumented("checkout")
def handle_checkout(order_id):
    return {"order_id": order_id, "status": "confirmed"}
```

### TypeScript, RED metrics for an Express-style handler

```typescript
interface RedMetrics {
  requests: Map<string, number>;
  errors: Map<string, number>;
  durationsMs: Map<string, number[]>;
}

function createRedMetrics(): RedMetrics {
  return {requests: new Map(), errors: new Map(), durationsMs: new Map()};
}

function recordRequest(metrics: RedMetrics, route: string, durationMs: number, failed: boolean): void {
  metrics.requests.set(route, (metrics.requests.get(route) ?? 0) + 1);
  if (failed) {
    metrics.errors.set(route, (metrics.errors.get(route) ?? 0) + 1);
  }
  const list = metrics.durationsMs.get(route) ?? [];
  list.push(durationMs);
  metrics.durationsMs.set(route, list);
}

const metrics = createRedMetrics();
const started = Date.now();
recordRequest(metrics, "/checkout", Date.now() - started, false);
```
