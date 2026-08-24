---
name: Throttling
slug: throttling
family: 08-cloud-distributed
category: Resilience and Traffic Management
aliases: [Traffic Shaping, Client-Side Self-Throttling, Adaptive Concurrency Limiting, Graceful Degradation Control, Overload Control]
first_described: "Homer, Sharp, Brader, Narumoto, Swanson 2014, Cloud Design Patterns"
maturity: canonical
related: [rate-limiting, circuit-breaker, bulkhead, retry, load-shedding, queue-based-load-leveling, priority-queue, backpressure]
incompatible_with: []
verified: 2026-08-02
---

# Throttling

## 1. Name, aliases, and lineage

Throttling is the practice of a service watching its own resource use and
capping or degrading the work it accepts, so that the whole system keeps
meeting its service-level objectives while a subset of demand is delayed,
rejected, or served in a reduced form.

The name enters the software architecture literature as a named pattern in
Alex Homer, John Sharp, Larry Brader, Masashi Narumoto, and Trent Swanson,
*Cloud Design Patterns, Prescriptive Architecture Guidance for Cloud
Applications*, Microsoft patterns and practices, 2014, ISBN 9781621140368,
in the chapter titled Throttling Pattern. That chapter is the origin of the
catalog entry now published as the Microsoft Learn Azure Architecture Center
Throttling pattern page
([learn.microsoft.com, Throttling Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/throttling),
verified 2026-08-02), which opens the pattern's definition with the sentence,
"Limit the resources that an application instance, an individual tenant, or
an entire service can consume." That page is treated here as the primary
source, current at the point of verification, and updated by Microsoft as
recently as 2026-05-29 according to the page's own `ms.date` field.

The word carries an older, unrelated meaning in networking hardware, where a
throttle is a physical or logical valve on a link's bandwidth, and in
operating systems, where CPU throttling reduces a process's clock cycles or
a core's frequency. The cloud application meaning inherited here is
narrower. It is a decision made in application or platform code about which
logical operations to admit, not a hardware-level bandwidth cap.

Several communities use the word loosely to mean any traffic-control
mechanism, and the aliases below name the real distinctions hiding inside
that looseness.

- **Traffic shaping** is the network-engineering term for smoothing a flow
  by delaying its excess rather than dropping it, which is one of the
  strategies this pattern's own source page lists under load leveling.
- **Client-side self-throttling** is the caller doing the same job in
  reverse, reading the responses from a service it depends on and reducing
  its own outbound rate before the service has to reject anything. The
  Google Site Reliability Engineering book describes this directly. "When a
  client detects that a significant portion of its recent requests have
  been rejected due to out of quota errors, it starts self-regulating and
  caps the amount of outgoing traffic it generates"
  ([sre.google, Handling Overload](https://sre.google/sre-book/handling-overload/),
  verified 2026-08-02).
- **Adaptive concurrency limiting** is throttling where the cap itself is
  computed from a live signal, most often latency, rather than fixed by an
  operator. Netflix's open-sourced `concurrency-limits` library is the
  reference implementation, discussed in dimension 8.
- **Graceful degradation control** names the specific strategy of turning
  off whole features rather than rejecting individual requests, covered in
  depth in dimension 8 because the task that produced this entry required
  it named explicitly.
- **Overload control** is the systems-research umbrella term, older than
  the cloud-pattern vocabulary, covering everything from telephone switch
  engineering to the criticality-tiered load shedding inside Google's own
  infrastructure.

Dimension 12 resolves the single most consequential naming confusion in this
family in full, because the task that produced this entry required it. Azure
publishes Throttling and Rate Limiting as two separate, named patterns, and
the difference between them is not cosmetic.

## 2. Problem and context

A service exposes an operation that costs something to run. The cost can be
CPU time, a database connection, a write to a storage tier with limited
input and output operations per second, an outbound call to a paid third
party, or a lock on a shared resource. The number of callers, and the shape
of the traffic they send, is not something the service owner controls.

The failure this pattern exists to prevent has a recognisable shape in
production. Demand rises past what the service is provisioned for, whether
from organic growth, a marketing event, a batch job someone forgot to rate
limit, or a bug in a caller that turns one request into a thousand. Nothing
in the system says no, so every request is accepted and every request
competes for the same finite resource. Latency for every caller rises
together, not only for the caller that caused the surge, because the
resource behind the operation is shared. Past a certain point, callers time
out and retry, which adds more load to a system that was already over
capacity, and the system enters a state where it cannot recover without an
operator forcing a return to safety. This shared, self-reinforcing collapse
under overload, rather than a clean, contained failure, is what makes
building deliberate admission control worth the engineering cost.

The Azure Architecture Center Throttling pattern page states the context
this way. "The load on a cloud application varies over time based on active
users and their activity... If processing demand exceeds available
capacity, the system slows or fails. When the system has an agreed service
level, that failure violates the SLO"
([learn.microsoft.com, Throttling Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/throttling),
verified 2026-08-02). The same page frames the alternative most engineers
reach for first, provisioning more capacity through autoscaling, and states
plainly why that alternative is not sufficient on its own. "Provisioning new
resources takes time and adds cost. Demand that exceeds capacity growth or
budget creates a resource deficit." Throttling exists precisely to cover the
gap between the moment demand exceeds capacity and the moment new capacity,
if any is coming, actually arrives. Dimension 8 covers this interaction with
autoscaling explicitly, because the task that produced this entry required
it named.

The problem shows up in several distinct shapes that all reach for
throttling but want different answers.

- **Self-preservation.** The service has a known ceiling and must protect
  itself from any caller, well-behaved or not, that would push it past that
  ceiling.
- **Tenant fairness.** In a multi-tenant system the aggregate capacity is
  fine, but one tenant's traffic is consuming a disproportionate share and
  starving the others.
- **Cascading protection.** The service is healthy but one of its own
  downstream dependencies is not, and it must reduce the calls it makes
  outward before its own retries amplify the outage. Azure's own catalog
  page names this as one of the pattern's own strategies, calling it
  outbound rate limits.
- **Cost and carbon control.** The limit reflects a budget or a commitment
  rather than a hard capacity ceiling. The same Azure page lists reducing
  low-value compute during periods of high grid carbon intensity as a valid
  reason to reach for this pattern, which is a use case with no equivalent
  under a purely commercial rate limit.

The context in which throttling is the right tool has one central feature.
The system can identify, cheaply, which slice of demand to slow, reject, or
degrade, and it can do so before the resource it is protecting actually
runs out. Where that identification is not possible, or where the cost of
rejecting a legitimate request outweighs the cost of degrading everyone a
little, dimension 4 names what to reach for instead.

## 3. Forces

The weighting in this dimension is engineering judgement, shaped by the
sources cited elsewhere in this entry, not itself a sourced claim.

- **Availability of the whole system.** Favoured, strongly, and this is the
  entire reason the pattern exists. A service that sheds a slice of its
  demand in a controlled way stays inside its latency budget for everyone
  else, instead of degrading unpredictably for everyone at once.
- **Fairness between callers.** Contested rather than simply favoured. A
  coarse, single global limit protects the service but does nothing for
  fairness between tenants, and a fine per-tenant limit protects fairness
  but costs more state and more decision latency per request. Dimension 8
  covers priority-based throttling and tenant fairness directly, because
  reconciling this force is most of what that mechanism is for.
- **Completeness of the response the caller gets.** Sacrificed, by design,
  whenever the chosen strategy is rejection or feature degradation rather
  than pure delay. A request that is throttled either does not happen at
  all or happens with a reduced feature set, and the caller must be able to
  tolerate that outcome for the trade to be worth making.
- **Decision latency.** Mildly sacrificed on the admitted path. Every
  request now pays for a check against a counter, a token bucket, or a
  live utilization signal. In process, that cost is close to free. Reading
  a shared counter across a fleet is a network round trip and is not free,
  which is one reason Azure's own considerations list favours local,
  per-node signals where the bottleneck genuinely is local.
- **Operability under incident conditions.** Favoured deliberately.
  Throttling limits that cannot be adjusted without a deployment are
  useless exactly when they are needed most, during an incident, when a
  deployment pipeline is the last thing an operator wants to depend on.
- **Simplicity of the admission decision.** Sacrificed as the pattern
  matures. A binary threshold is simple and produces a latency cliff at the
  threshold. A criticality-tiered, adaptive, or priority-fair scheme avoids
  the cliff at the cost of a materially more complex admission path, more
  state, and more that can be configured incorrectly.

## 4. Applicability and non-applicability

**Reach for throttling when:**

- The service has a known or measurable saturation point, in throughput,
  concurrency, or a specific downstream dependency, and it needs to stay
  under that point regardless of who is asking.
- Multiple tenants or callers share one deployment and a single greedy
  caller could otherwise degrade the experience for every other caller.
- The system needs to survive a burst without failing outright while
  autoscaling, which is not instantaneous, catches up to the new demand.
- Some functionality in the system is more valuable than other
  functionality, and it is acceptable, under load, to serve the valuable
  part and reduce or drop the rest.
- A caller can tolerate the outcome of being slowed, rejected, or served a
  reduced response, meaning it can retry, queue locally, or degrade its own
  user experience gracefully.
- The service calls an external dependency that itself imposes limits, and
  the service wants to avoid tripping those limits and being rejected in
  bulk.

**Do not reach for throttling when:**

- The operation is a single synchronous call that the caller needs answered
  immediately and cannot tolerate any delay or partial result. Throttling
  by delay simply relocates the latency problem onto a caller that cannot
  absorb it. Azure's own Rate Limiting pattern page states this exact
  non-applicability directly for its own sibling pattern. "This pattern
  might not be suitable when the operation requires immediate, synchronous
  completion with very low latency and can't tolerate queuing or deferred
  processing"
  ([learn.microsoft.com, Rate Limiting Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/rate-limiting-pattern),
  verified 2026-08-02), and the same reasoning holds for a throttle that
  queues rather than rejects.
- The actual bottleneck is not arrival rate but in-flight concurrency at a
  fan-out point, a connection pool, or a thread pool. Azure's Throttling
  pattern page names this failure mode by name. "A requests-per-second
  limit doesn't protect a system whose bottleneck is concurrent in-flight
  requests." The Bulkhead pattern, which partitions concurrency rather than
  arrival rate, is the correct tool there, and dimension 13 covers exactly
  where the boundary between the two patterns sits.
- The problem is a single unhealthy downstream dependency rather than
  excess demand on a healthy one. A service that keeps calling a dependency
  that is failing needs a breaker that stops calling entirely, not a
  throttle that keeps calling at a reduced rate. Dimension 13 covers this
  distinction against Circuit Breaker.
- The work must never be lost and can be processed asynchronously. Queueing
  the excess into a durable store and draining it at a controlled pace, the
  Queue-Based Load Leveling pattern, is a better fit than rejecting or
  degrading it, because rejection discards work a durable queue would have
  preserved.
- There is no reliable way to identify which caller, tenant, or feature to
  slow. A limiter keyed on the wrong dimension, for example a shared
  network address behind one corporate proxy for thousands of real users,
  punishes the wrong population and does not solve the underlying fairness
  problem it was built for.
- The system is a single, low-traffic internal service with no plausible
  path to overload. Adding a throttling decision path to every request adds
  latency and a new class of misconfiguration risk that a service with no
  realistic overload scenario does not need to carry.

## 5. Structure

- **Protected Resource.** The thing whose exhaustion the pattern exists to
  prevent, for example a database's provisioned throughput, a fixed pool of
  worker threads, or an external API's own published limit.
- **Load Signal.** The measurement the system reads to decide whether it is
  approaching saturation. It can be as simple as a per-caller request
  counter or as rich as p99 latency, queue depth, or a downstream error
  rate.
- **Classifier.** The component that decides which principal, tenant,
  operation, or feature a given request belongs to, so the enforcement
  point knows what policy applies. Kubernetes API Priority and Fairness's
  FlowSchemas are a fully worked example of a classifier, covered in
  dimension 9.
- **Enforcement Point.** Where the admission decision is actually applied.
  It can sit at the network edge, inside a service mesh sidecar, or inline
  in application code, and it is usually built as a Decorator or a stage in
  a Chain of Responsibility, covered in dimension 13.
- **Response Strategy.** What happens to the excess. The three families
  this entry treats as distinct are reject outright, delay until capacity
  frees up, and degrade by turning off lower-value functionality while
  keeping the operation itself running. Dimension 8 covers all three, and
  graceful feature degradation in particular is covered at the depth the
  task that produced this entry required.
- **Restoration Logic.** The counterpart nobody's happy path diagram shows.
  The rule for when a rejected caller, a delayed queue, or a degraded
  feature returns to normal service, and how the system avoids flapping
  between the two states as the load signal crosses the threshold
  repeatedly.

## 6. ASCII structure diagram

```
                +-----------------------+
   requests --> |      Classifier       |
                |  (who, what, weight)  |
                +-----------+-----------+
                            |
                            v
                +-----------------------+        +------------------+
                |   Enforcement Point    |<------>|   Load Signal    |
                |  reads policy + signal |        | (rate, latency,  |
                +-----------+-----------+        |  queue depth,    |
                            |                     |  utilization)    |
              admit         |        reject/delay/degrade
                            |                     +------------------+
              +-------------+-------------+
              |                           |
              v                           v
      +----------------+       +--------------------------+
      | Protected       |       |    Response Strategy     |
      | Resource        |       |  reject 429/503          |
      | (DB, pool,      |       |  delay + Retry-After      |
      |  downstream)    |       |  degrade a feature tier   |
      +----------------+       +--------------------------+
                                              |
                                              v
                                   +--------------------------+
                                   |   Restoration Logic       |
                                   |  (hysteresis band so a     |
                                   |   feature does not flap)   |
                                   +--------------------------+
```

## 7. Dynamics

The path below traces a single request through a throttle built with a
graceful-degradation response strategy, since that is the strategy dimension
8 covers at the greatest depth, and shows the restoration path that most
sequence diagrams for this pattern leave out.

```
Caller          Enforcement Point       Load Signal        Protected Resource
  |                     |                     |                     |
  | request             |                     |                     |
  |-------------------->|                     |                     |
  |                     | read utilization    |                     |
  |                     |-------------------->|                     |
  |                     |<--------------------|                     |
  |                     | utilization=0.92,   |                     |
  |                     | hard_limit=0.90     |                     |
  |                     |                     |                     |
  |                     | classify. request   |                     |
  |                     | belongs to a        |                     |
  |                     | sheddable feature   |                     |
  |                     | tier                |                     |
  |                     |                     |                     |
  |                     | shed tier, degrade  |                     |
  |                     | rather than forward |                     |
  |<--------------------|                     |                     |
  | 200 with reduced    |                     |                     |
  | payload, feature    |                     |                     |
  | flag off            |                     |                     |
  |                     |                     |                     |
  ... time passes, utilization falls ...
  |                     |                     |                     |
  |                     | read utilization    |                     |
  |                     |-------------------->|                     |
  |                     |<--------------------|                     |
  |                     | utilization=0.58,   |                     |
  |                     | below soft_limit    |                     |
  |                     | minus hysteresis    |                     |
  |                     |                     |                     |
  |                     | restore tier        |                     |
  | next request        |                     |                     |
  |-------------------->|                     |                     |
  |                     | forward, full path  |                     |
  |                     |-------------------------------------------->|
  |                     |<--------------------------------------------|
  |<--------------------|                     |                     |
  | 200 full payload    |                     |                     |
```

A rejecting throttle follows the same first half of this trace, but instead
of degrading the response it returns 429 or 503 with a `Retry-After` value
computed from the load signal, and the caller, not the service, is
responsible for the second half of the trace, retrying after the indicated
delay.

## 8. Implementation variants

This dimension covers, in the order the task that produced this entry
required, graceful degradation tiers, priority-based throttling and tenant
fairness, concurrency-based adaptive throttling, and the interaction with
autoscaling, before the shorter remaining variants.

### Graceful degradation tiers

The core idea is that not every unit of functionality carries the same
value, and under load the system should shed the least valuable unit first,
keep shedding as load rises, and restore in the reverse order as load
falls. Azure's Throttling pattern page describes exactly this shape with a
worked example. "A feature is a specific area of functionality... Just
before time T1, total resource use approaches the threshold and risks
exhausting available capacity. Feature B is less critical than Feature A or
Feature C, so the system turns off Feature B and releases its resources.
Between times T1 and T2, Feature A and Feature C continue normally. By time
T2, total resource use drops enough to turn Feature B back on"
([learn.microsoft.com, Throttling Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/throttling),
verified 2026-08-02).

Building this well means two decisions the naive version gets wrong.
First, the tier assignment is a design-time decision made by whoever owns
the product, not something inferred at run time, because only a human can
say that a recommendations widget matters less than checkout. Second, the
restore threshold must sit below the shed threshold by a deliberate margin,
a hysteresis band, or a feature will flap on and off every time the load
signal crosses the boundary, which is worse for users than staying off. The
Go example in the code section implements exactly this shape, three named
tiers and a configurable restoration gap.

A production instance of this same idea at a coarser grain is Google's
criticality system, described in the SRE book's overload chapter. "The
system defines four tiers, CRITICAL_PLUS, CRITICAL, SHEDDABLE_PLUS, and
SHEDDABLE... When a customer runs out of global quota, a backend task will
only reject requests of a given criticality if it's already rejecting all
requests of all lower criticalities"
([sre.google, Handling Overload](https://sre.google/sre-book/handling-overload/),
verified 2026-08-02). The difference from feature-level degradation is
scope. Google's criticality levels shed whole requests by their declared
importance, while feature-tier degradation shrinks a single request's scope
without failing it outright. The two compose. A request can carry both a
criticality label and, within it, a set of feature flags that degrade
before the request itself is shed.

### Priority-based throttling and tenant fairness

A single global limit protects the service but treats every caller
identically, which is exactly wrong in a multi-tenant system where one
tenant's leader election traffic must never be starved by another tenant's
batch job. The production-grade answer is to partition capacity by priority
level, give each level a guaranteed share, and let a level borrow spare
capacity from an underused level without ever letting a low-priority level
starve a high-priority one.

Kubernetes' own API server solves exactly this problem with its API
Priority and Fairness feature, and its documentation is precise about the
mechanism. "Incoming requests are classified by attributes of the request
using FlowSchemas, and assigned to priority levels. Priority levels add a
degree of isolation by maintaining separate concurrency limits, so that
requests assigned to different priority levels cannot starve each other...
The default configuration, for example, includes separate priority levels
for leader-election requests, requests from built-in controllers, and
requests from Pods. This means that an ill-behaved Pod that floods the API
server with requests cannot prevent leader election or actions by the
built-in controllers from succeeding"
([kubernetes.io, API Priority and Fairness](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/),
verified 2026-08-02). Within a priority level, Kubernetes further divides
requests into flows, one per distinguishing user or namespace, and uses
shuffle sharding across per-flow queues so a single noisy flow cannot
monopolise the queue capacity that belongs to its own priority level either.
The Rust example in the code section implements a simplified version of the
same idea, fixed shares per priority with controlled borrowing, without
Kubernetes' queueing and shuffle-sharding machinery.

### Concurrency-based adaptive throttling

A static requests-per-second number is a proxy for the thing that actually
matters, whether the service still has spare capacity, and a proxy that
does not track the underlying reality drifts stale the moment the fleet
autoscales, a downstream dependency slows down, or the mix of cheap and
expensive operations shifts. Netflix's open-sourced `concurrency-limits`
library replaces the static number with a limit computed continuously from
latency. Its own documentation states the motivation directly. "Rather than
enforcing static RPS limits that quickly go out of date... the library
measures concurrent requests where we apply queuing theory to determine the
number of concurrent requests a service can handle," borrowing the
algorithm family from TCP's own congestion control, "equating a system's
concurrency limit to a TCP congestion window"
([github.com/Netflix/concurrency-limits](https://github.com/Netflix/concurrency-limits),
verified 2026-08-02). The lineage of that borrowing traces to Van Jacobson,
Congestion Avoidance and Control, ACM SIGCOMM Computer Communication Review
18, 4, pages 314 to 329, August 1988, the paper that introduced additive
increase and multiplicative decrease as the shape a self-tuning limit should
follow when latency, not a fixed ceiling, is the signal.

The Python example in the code section implements the same family of idea
at a small scale, a Vegas-style gradient limiter that measures round-trip
latency, infers a minimum achievable latency as its no-queue baseline, and
grows the concurrency limit toward the current achieved ratio of that
baseline to the observed latency, contracting hard on an explicit
rejection. The mechanism generalises past HTTP services. Any resource whose
saturation shows up first as rising latency, a connection pool, a batch
writer, a gRPC server, is a candidate for this style of throttle in place
of a fixed concurrency ceiling picked once and never revisited.

### Interaction with autoscaling

Throttling and autoscaling solve the same underlying problem, insufficient
capacity for current demand, on two different timescales, and Azure's
Throttling pattern page states this relationship plainly rather than
treating the two as competitors. "You can combine autoscaling, graceful
degradation, and throttling to keep applications responsive and within
SLAs. When you expect demand to stay high, throttling maintains stability
while the system scales out. After scaling completes, the system restores
full functionality... At time T1, the system reaches the soft limit and
starts to scale out. If new resources don't arrive in time, demand can
exhaust the existing resources, and the system can fail. Throttling rejects
excess requests during scale-out to keep resource use below the hard limit,
then lifts those restrictions after new capacity comes online"
([learn.microsoft.com, Throttling Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/throttling),
verified 2026-08-02). Autoscaling closes a capacity gap over minutes.
Throttling closes it over milliseconds. A system that only autoscales fails
during the gap between the overload starting and the new instances becoming
healthy. A system that only throttles never grows to meet sustained
legitimate demand and permanently rejects traffic it could have served.
Neither replaces the other, and the soft-limit and hard-limit thresholds in
the Go example's `GracefulThrottle` map directly onto the two trigger points
in Azure's own diagram, the point where scale-out begins and the point past
which requests must be shed regardless.

### Response strategy variants, briefly

The remaining variants are shorter because dimension 12 of this entry, and
dimension 8 of the companion Rate Limiting pattern entry, cover the
algorithm mechanics, token bucket, leaky bucket, fixed and sliding windows,
in depth already, and repeating that material here would not add anything.

- **Reject with a status code and a retry hint.** The response strategy
  used by Microsoft Graph, Shopify, and most public APIs, covered fully in
  dimension 9.
- **Delay until capacity frees.** nginx's `limit_req` directive is the
  reference implementation. Without the `nodelay` flag, excess requests
  inside the configured burst are queued and released at the configured
  rate rather than rejected, and only requests beyond the burst size are
  terminated with an error, which nginx's documentation states as, "If the
  requests rate exceeds the rate configured for a zone, their processing is
  delayed such that requests are processed at a defined rate. Excessive
  requests are delayed until their number exceeds the maximum burst size in
  which case the request is terminated with an error"
  ([nginx.org, ngx_http_limit_req_module](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html),
  verified 2026-08-02).
- **Proxy-local enforcement.** Envoy's local rate limit HTTP filter applies
  a token bucket inside the proxy process itself, either shared across the
  process or scoped per downstream connection, which its documentation
  states as, "Depending on the value of the config
  `local_rate_limit_per_downstream_connection`, the token bucket is either
  shared across all workers or on a per connection basis"
  ([envoyproxy.io, Local rate limit filter](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/local_rate_limit_filter),
  verified 2026-08-02). This variant needs no shared store and no network
  round trip, at the cost of every proxy instance enforcing its own view of
  the limit rather than one global view.

## 9. Known production uses

- **Microsoft Graph** returns HTTP 429 with a `Retry-After` header when a
  client crosses per-application, per-tenant, or per-resource thresholds
  that vary by operation type, writes being throttled sooner than reads.
  Its own guidance states, "When a throttling threshold is exceeded,
  Microsoft Graph limits any further requests from that client app for
  some time [and] returns HTTP status code 429 Too Many Requests"
  ([learn.microsoft.com, Microsoft Graph throttling guidance](https://learn.microsoft.com/en-us/graph/throttling),
  verified 2026-08-02), and it explicitly points its own developers back at
  the Azure Throttling pattern page for the broader architectural
  discussion, tying the production system directly to the named pattern.
- **Shopify's GraphQL Admin API** implements a leaky bucket per app and
  store pair, described in Shopify's own words as, "Each app has access to
  a bucket. It can hold, say, 60 marbles. Each API request tosses some
  number of marbles into the bucket. Each second, a marble is removed from
  the bucket if there are any"
  ([shopify.dev, Rate limits](https://shopify.dev/docs/api/usage/rate-limits),
  verified 2026-08-02), and reports the current bucket state back to the
  caller in the response's `extensions.cost.throttleStatus` object on every
  call, so a well-behaved client can pace itself without ever hitting a
  rejection.
- **The Kubernetes API server** enforces priority-based throttling with
  tenant fairness through its API Priority and Fairness feature, described
  in dimension 8, an in-cluster production system that ships with default
  priority levels precisely so that a misbehaving workload cannot starve
  the control plane's own leader election traffic
  ([kubernetes.io, API Priority and Fairness](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/),
  verified 2026-08-02).
- **Netflix's `concurrency-limits` library**, open sourced and used inside
  Netflix's own service mesh, replaces a fixed concurrency ceiling with one
  computed continuously from measured latency, described in dimension 8
  ([github.com/Netflix/concurrency-limits](https://github.com/Netflix/concurrency-limits),
  verified 2026-08-02).
- **Stripe's API** layers a per-user request rate limit with a separate
  concurrent-requests limiter and two further load shedders keyed on fleet
  utilization and per-worker capacity, so that, in Stripe's own framing,
  the platform keeps "the core part of your business working while the
  rest is on fire"
  ([stripe.com, Scaling your API with rate limiters](https://stripe.com/blog/rate-limiters),
  verified 2026-08-02). Stripe's own documentation deliberately avoids the word
  throttle for its concurrent-requests layer, which is itself evidence for
  the naming inconsistency this entry's dimension 12 resolves.
- **Google's own production infrastructure**, described in the Site
  Reliability Engineering book's overload chapter, layers per-customer
  global quotas with a four-tier criticality system so a task under
  overload sheds the least valuable requests first, and pairs this
  server-side control with client-side self-throttling so that clients stop
  sending doomed requests before the server has to spend resources
  rejecting them ([sre.google, Handling Overload](https://sre.google/sre-book/handling-overload/),
  verified 2026-08-02).

## 10. Consequences

**Positive.**

- A single greedy caller, a bug, or a burst cannot degrade the experience
  of every other caller sharing the resource, because the excess is
  contained at the boundary rather than allowed to saturate the shared
  resource behind it.
- The system fails predictably. A caller that is rejected or degraded gets
  a fast, legible signal instead of a slow, ambiguous one, and can act on
  it, retry later, back off, or accept a reduced response.
- Combined with autoscaling, throttling covers the window during which new
  capacity has been requested but has not yet arrived, which autoscaling
  alone cannot do.
- Priority-tiered and graceful-degradation strategies let the system
  preserve its most valuable functionality under load rather than failing
  uniformly, which a purely binary accept-or-reject scheme cannot do.
- Client-visible signals, a status code, a `Retry-After` header, or a
  reported bucket state, let well-behaved callers self-regulate before they
  are ever rejected, which reduces the total number of rejections the
  system has to produce.

**Negative.**

- Every admitted request now pays a decision cost, and where the decision
  reads shared state across a fleet, that cost is a network round trip, not
  a free arithmetic check.
- A caller that cannot tolerate rejection, delay, or a reduced response
  experiences the pattern as a new failure mode it did not have before the
  throttle existed, and every caller of the protected system now has to be
  audited for whether it can absorb that outcome.
- Feature-tier degradation and priority tiers are design-time decisions
  that require a human to rank the relative value of functionality, and a
  wrong ranking, made once and never revisited, silently shapes which
  users are harmed during every future incident.
- A limit set once at launch and never revisited drifts out of step with
  the traffic pattern it was calibrated against, and this drift is
  invisible until it either rejects legitimate growth or fails to catch a
  new abuse pattern it was never sized for.
- The mechanism itself becomes an attack surface. A limiter, a
  classifier, or a shared counter store that is slow, misconfigured, or
  itself under load can become the bottleneck it was built to prevent,
  covered in dimension 11.

## 11. Failure modes and misuse

Each entry names the symptom an operator or a user would actually observe,
the underlying cause, and the fix, following the format the task that
produced this entry required.

**Symptom.** Every tenant's requests start failing during one tenant's
traffic spike, even though the aggregate service capacity was never
exceeded.
**Cause.** The limiter is keyed at a boundary coarser than the actual
isolation domain, for example a single global counter, or a counter keyed
by a shared network address that many distinct tenants sit behind.
**Fix.** Key the classifier to the real isolation boundary, an
authenticated tenant identity where one exists, and give each tenant or
priority level its own concurrency share so one flow's excess cannot
consume capacity reserved for another, the mechanism dimension 8 covers
under priority-based throttling and tenant fairness.

**Symptom.** Latency is flat and healthy right up until it spikes hard and
without warning, and the spike coincides exactly with requests starting to
fail.
**Cause.** A hard binary threshold admits everything below the line and
rejects sharply above it, with nothing in between, so the caller gets no
advance signal that the system is approaching saturation.
**Fix.** Shed proactively rather than only at the edge of collapse. Azure's
own considerations list states this directly. "A throttle that only rejects
after a component saturates causes latency to spike before callers see any
back-pressure... As utilization approaches the hard limit, start rejecting
a growing fraction of requests"
([learn.microsoft.com, Throttling Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/throttling),
verified 2026-08-02).

**Symptom.** Rejections spike, and instead of the system recovering, the
rejection rate climbs further, and total request volume keeps rising even
as the useful throughput falls.
**Cause.** A retry storm. Clients retry immediately after a rejection, with
no backoff and no jitter, so the retried traffic lands on the system at the
same moment the original traffic would have, and each retry wave is larger
than the one before it.
**Fix.** Return `Retry-After` and require clients to honour it with
randomised backoff, and treat a silent internal retry that hides the
throttling response from an upstream caller as the specific antipattern the
Google SRE book names Retry Storm. Azure's Rate Limiting pattern page states
the mitigation directly, that retries need to be coordinated with rate
limiting so the system can "propagate back-pressure signals, for example
HTTP 429 with Retry-After, and use a limited number of retries with small
random delays between attempts"
([learn.microsoft.com, Rate Limiting Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/rate-limiting-pattern),
verified 2026-08-02).

**Symptom.** A service that fronts a throttled dependency starts returning
generic internal server errors under load, and the caller has no idea it
should slow down, so it keeps sending traffic at the same rate.
**Cause.** The service absorbs a 429 or 503 from its own dependency by
retrying silently and, when the retries are also exhausted, converts the
failure into an opaque error rather than propagating the overload signal
upward.
**Fix.** Surface the dependency's throttling response to the caller
directly, or convert it into the equivalent status and `Retry-After` on the
service's own boundary, so the entire call chain sheds load together rather
than each hop absorbing the signal and hiding it from the one above it.

**Symptom.** A degraded feature turns back on and off rapidly for seconds
at a time, visible in the frontend as flicker, right around the moment the
system is recovering from load.
**Cause.** No separation between the threshold that sheds a feature and the
threshold that restores it, so ordinary noise in the load signal crosses
one shared threshold repeatedly.
**Fix.** Use two thresholds, not one, with the restore threshold set
meaningfully below the shed threshold, the hysteresis band implemented
directly in the `restoreGap` field of the Go example in the code section.

**Symptom.** During a genuine, sustained overload, the system spends a
large fraction of its own capacity producing rejections rather than serving
the requests it is still able to serve.
**Cause.** The rejection path itself does expensive work, authentication,
deep request parsing, or a policy lookup, before the throttling decision is
made, so a flood of requests that were always going to be rejected still
saturates the system.
**Fix.** Reject as early in the request pipeline as possible, and, as
Azure's own considerations list frames it, "Make rejection cheaper than the
work that it prevents... load test the rejection path itself"
([learn.microsoft.com, Throttling Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/throttling),
verified 2026-08-02).

## 12. Trade-off matrix

### Throttling versus Rate Limiting, resolved

Azure publishes these as two distinct, named patterns, on two distinct
pages, and most engineering conversations conflate them because both
mechanisms can be built out of the same token bucket or sliding window
arithmetic. The two pages resolve the confusion themselves, and the
resolution is about which side of a call the mechanism runs on and who it
protects, not about the algorithm underneath.

Throttling runs on the service side and protects the service from its
callers. Its own definition states, "Limit the resources that an
application instance, an individual tenant, or an entire service can
consume"
([learn.microsoft.com, Throttling Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/throttling),
verified 2026-08-02).

Rate Limiting runs on the caller side and protects the caller from being
throttled by a service it depends on. Its own definition states, "Control
the rate at which your application sends requests to a service so that you
stay within the service's throttling limits and overall capacity"
([learn.microsoft.com, Rate Limiting Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/rate-limiting-pattern),
verified 2026-08-02), and the word "throttling" in that sentence links
directly back to the Throttling pattern page, making the relationship
explicit in the source itself. Rate limiting's own worked example is a
batch job ingesting ten thousand records into a database with a fixed
provisioned throughput, using durable queues and job processors to hold
back its own request rate rather than flooding the database and absorbing
repeated rejections.

| Question | Throttling | Rate Limiting |
|---|---|---|
| Whose resource is protected | The service's own capacity | A downstream service's published limit |
| Who decides the policy | The service operator | The caller, based on the downstream service's published limit |
| Typical trigger | A live saturation or utilization signal | A static, known ceiling published by the dependency |
| Typical response | Reject (429/503), delay, or degrade a feature | Queue locally and release at a controlled pace |
| Where it lives | The service's own edge or application code | The caller's own outbound path, often via a durable queue |
| Named example | Microsoft Graph rejecting a client at 429 | A job processor draining a queue at 100 records per second into a rate-limited database |

The practical consequence is that a well-built system commonly runs both at
once, on opposite ends of the same call. A payment processor throttles
inbound calls from merchants to protect itself, per dimension 9's Stripe
example, and the same processor rate limits its own outbound calls to a
card network whose limits it does not control. Building only one side
leaves the other side unmanaged, and that is the gap the naming confusion
this dimension resolves tends to hide.

### Throttling against its other named alternatives

The weighting is engineering judgement, drawn from the sources cited
throughout this entry.

| Mechanism | Question it answers | Trigger | Excess work is | Named example |
|---|---|---|---|---|
| Throttling | Can the service stay under its own capacity right now | A live utilization or rate signal, evaluated server-side | Rejected, delayed, or served in a degraded form | Microsoft Graph 429 with Retry-After |
| Rate Limiting | Can the caller avoid being throttled by a dependency | A static, known ceiling the caller paces itself against | Queued locally, released at a controlled pace | A job processor pacing writes into a throughput-limited database |
| Circuit Breaker | Is a specific downstream dependency healthy enough to call at all | Consecutive failures or a failure rate crossing a threshold | Not attempted at all, failed fast locally | A payment service that stops calling a fraud-check API after repeated timeouts |
| Bulkhead | Is there a free slot in a bounded resource pool | A fixed pool of threads, connections, or slots | Rejected because the pool, not the rate, is exhausted | A connection pool sized per downstream dependency so one slow dependency cannot exhaust threads shared with a healthy one |
| Load Shedding | Is the system healthy enough to take more work of a given importance | A live health signal combined with a request's declared criticality | Dropped by priority, least valuable first | Google's CRITICAL_PLUS through SHEDDABLE tiers |
| Backpressure | Can the consumer of a stream accept more without buffering unboundedly | A demand signal the consumer sends the producer | Never produced in the first place | The Reactive Streams specification's `request(n)` signal between producer and subscriber |

Throttling and Circuit Breaker both return fast failures and both sit at a
call boundary, which is why they are frequently mistaken for the same
mechanism. The distinguishing question is whether the thing being protected
is the caller from a broken dependency, a breaker's job, or a resource from
a healthy but excessive caller, a throttle's job. Load Shedding is the one
member of this family that reads a live health signal rather than a static
policy, which is why it survives conditions a pure rate policy does not,
for example a dependency-driven latency spike with no change in raw request
volume at all.

## 13. Related and incompatible patterns

**Rate Limiting.** The pattern whose relationship to this one dimension 12
resolves in full. Related, not a synonym, and a mature system commonly
implements both, on opposite sides of a call boundary.

**Circuit Breaker.** Complementary, and the most commonly confused
neighbour on the same side of a call boundary. A breaker protects a caller
from a dependency that is failing. A throttle protects a resource from a
caller that is healthy but asking for more than its share. A single
service commonly carries both, a throttle on its inbound edge and a
breaker on each outbound dependency it calls.

**Bulkhead.** The sibling isolation pattern for a different kind of scarce
resource. Bulkhead partitions concurrency, threads, connections, or slots,
while throttling partitions rate or, in its adaptive form, a
latency-derived concurrency estimate. Dimension 4 names reaching for one
when the bottleneck is really the other as a specific non-applicability
case worth watching for.

**Retry.** The client-side partner, and actively dangerous without full
jitter. A client that retries a throttled request at exactly the interval
the `Retry-After` header specifies, with no randomisation, synchronises its
own retries with every other client that received the same rejection at
the same moment, recreating the exact surge the throttle rejected in the
first place.

**Load Shedding.** A layer above rather than a substitute. Dimension 12
covers the distinction in full. Google's own infrastructure and Stripe's
own production system both run load shedding on top of a rate-based
throttle rather than choosing one mechanism over the other.

**Queue-Based Load Leveling.** An alternative for the specific case where
work must not be lost. Instead of rejecting or degrading the excess, accept
it durably and drain it at a controlled pace. Rate Limiting's own worked
example, described in dimension 12, is built directly on top of this
pattern. Choose queue-based leveling when the caller only needs an
eventual acknowledgement, and choose throttling's reject or degrade
strategies when the caller needs an answer now.

**Priority Queue.** The structural partner for priority-based throttling.
Azure's own considerations list points to it directly for implementing the
priority-based deferral strategy, and Kubernetes API Priority and Fairness's
own per-priority-level queues, covered in dimension 9, are a production
instance of exactly this pairing.

**Backpressure.** Different in kind, not merely in degree. Throttling and
its neighbours all reject or delay work that was already created.
Backpressure tells a cooperative producer to stop creating the work in the
first place, which is only possible when the producer honours a demand
signal, as in the Reactive Streams specification. Throttling is what a
system reaches for when the caller across the boundary is a stranger it
cannot ask to slow down.

**Decorator and Chain of Responsibility.** The structural patterns the
Enforcement Point is usually built from. A single throttle is naturally a
Decorator wrapped around a handler, and a stack of several throttles
evaluated in a fixed order, edge first, then service, then a specific
downstream dependency, is a Chain of Responsibility made explicit.

**Nothing here is strictly incompatible**, which is why the frontmatter
carries an empty incompatibility list. The closest thing to a genuine
conflict is combining a delaying, queueing throttle with an aggressive
client-side timeout shorter than the queue wait the throttle imposes. The
service does the work anyway, after the client has already given up and
possibly retried, so the service pays the cost twice and the client sees
neither result. If a throttle delays rather than rejects, the delay must be
visible to the client, ideally via the same `Retry-After` mechanism used for
rejection, and shorter than the client's own timeout.

## 14. Refactoring path in and out

### Introducing it

1. **Measure the resource that actually saturates first**, not the one
   that is easiest to count. Azure's own considerations list warns
   directly that request rate is the familiar dimension but often the
   wrong one, and that the real bottleneck is frequently concurrency,
   queue depth, or a downstream dependency's own limit. Instrument the
   candidate resource for at least one full weekly traffic cycle before
   choosing a threshold.
2. **Decide the response strategy before writing any enforcement code.**
   Reject, delay, or degrade a feature are not interchangeable, and the
   choice depends entirely on what the caller of the protected operation
   can tolerate, decided in dimension 4.
3. **Classify before you enforce.** Build the classifier, the component
   that maps an incoming request to a tenant, a priority level, or a
   feature tier, and deploy it in observe-only mode first, recording the
   verdict it would have applied without actually applying it, so
   miscalibration is caught before a real user is affected.
4. **Add the response signal before the enforcement.** Emit the status
   code, the `Retry-After` header, or a reported utilization figure while
   still in observe-only mode, so well-behaved callers can begin
   self-regulating, the client-side throttling described in dimension 1,
   before any request is actually rejected.
5. **Enforce for a narrow slice first.** A single internal tenant, or a
   single low-value feature tier, with a mechanism to disable the
   enforcement for that slice instantly and without a deployment.
6. **Add the hysteresis band before enabling graceful degradation broadly.**
   A shed threshold with no separate, lower restore threshold produces the
   flapping failure covered in dimension 11 the first time real traffic
   hovers near the boundary.
7. **Move shared state to a centralised store only when local, per-node
   state genuinely produces the wrong decision.** A single-node deployment
   never needs a shared counter, and adding one before it is needed buys a
   new dependency and pays for it in decision latency on every request.

### Removing it

A throttle stops earning its place when the resource it protects has been
resized so its true capacity sits far above any plausible demand, when the
traffic pattern that originally justified it no longer exists, or when the
mechanism has not actually rejected, delayed, or degraded a single request
in a full seasonal cycle including the business's own annual peak.

1. Confirm from the observability signals in dimension 16 that the
   enforcement rate for the policy in question is at or near zero over a
   long window, and that no caller's usage sits close enough to the
   threshold to make that zero fragile.
2. Widen the threshold rather than deleting the enforcement path, and
   observe. A threshold set to several times its current effective value is
   functionally inert while remaining a working safety net and a tested
   code path that has not silently rotted.
3. Keep the response signal, the status code, the header, or the reported
   utilization figure, even after the threshold is widened. Callers built
   against that signal do not break when the numbers grow, and they do
   break the moment the signal disappears while their parsing still expects
   it.
4. Remove the enforcement itself only after the widened threshold has held
   through the business's full seasonal cycle, not merely through a quiet
   month.
5. Remove any shared-state dependency, a distributed counter store or a
   lease-based partition scheme, last, because it is frequently shared with
   other throttles or rate limits that are being kept.

## 15. Testing and verification

This dimension is drawn from engineering practice rather than a single
sourced claim.

Test the classifier and the enforcement decision as pure functions,
separately from the transport layer that carries the request. A throttle's
core decision, given this load signal and this request's classification,
admit, delay, or degrade, has no network dependency of its own and should
be testable with a table of load-signal values and expected verdicts, the
same shape as the simulation functions in the Go and Rust examples in the
code section.

Test the hysteresis behaviour explicitly, not incidentally. A test that
only asserts a feature sheds at the high threshold and never asserts that
it stays shed until the load signal crosses back below the lower restore
threshold will not catch the flapping failure mode in dimension 11, because
the naive implementation and the correct one produce the same result on a
single load reading and only diverge across a sequence of readings that
hover near the boundary.

Test the priority and fairness guarantee under contention, not only in
isolation. A test that admits high-priority requests one at a time proves
nothing about whether a flood of low-priority requests can still starve
high-priority ones when both arrive concurrently. The Rust example's test
in the code section deliberately floods the sheddable priority level first
and then confirms the critical level is unaffected, which is the shape a
real fairness test needs.

Test the restoration path under a realistic load curve, not a step
function. A synthetic test that jumps the load signal from zero straight to
its maximum and back exercises the shed and restore thresholds but never
exercises the noisy, wandering trajectory real production load actually
takes near the boundary, which is exactly where flapping and
misclassification show up.

Load test the rejection path itself, at the volume a real overload would
produce, not only the admission path. Dimension 11 names a rejection path
that itself saturates the system as a distinct failure mode, and the only
way to catch it before production is to generate the rejected traffic at
scale and measure the service's own resource use while it produces nothing
but 429 or 503 responses.

Test client-side backoff behaviour end to end, including jitter, against a
service double that always returns the throttled response. A retry
implementation that looks correct in isolation can still produce a
synchronised retry storm once many client instances run the same
unjittered backoff schedule against the same server-reported delay, the
failure covered in dimension 11.

## 16. Observability signals

A healthy throttle, on a dashboard, shows a low and roughly steady
enforcement rate that tracks the traffic pattern rather than a flat zero,
because a flat zero for a long period means either the system never
approaches the condition the throttle exists for, worth questioning per
dimension 14's removal path, or the throttle is silently not evaluating
requests at all.

- **Enforcement rate**, split by the verdict, admitted, delayed, rejected,
  degraded, and by the classifier's dimension, tenant, priority level, or
  feature tier, so an operator can see which slice of traffic is actually
  paying the cost.
- **Load signal value against its configured thresholds**, plotted over
  time with both the shed and restore thresholds drawn as reference lines,
  which is the single view that makes flapping, covered in dimension 11,
  visible at a glance.
- **Near-limit population**, the count or the identity of callers sitting
  close to but under their threshold, which is the leading indicator that a
  threshold set too low is about to start rejecting legitimate growth
  before the rejections themselves appear in the enforcement rate.
- **Latency of the enforcement decision itself**, separated from the
  latency of the underlying protected operation, so a slow shared-state
  lookup that has itself become a bottleneck, the failure mode named in
  dimension 10, is visible rather than blended into overall request
  latency.
- **Retry-After adherence**, comparing the delay a rejected client actually
  waited against the delay the service told it to wait, which is the
  metric that catches a misbehaving or unjittered client before it produces
  a full retry storm.
- **Propagated overload signals from downstream dependencies**, counted
  separately from locally generated rejections, so an operator can tell
  whether a rise in throttling at this service is caused by its own load or
  is an overload signal correctly propagated upward from something it
  depends on, the behaviour dimension 11 names as the fix for silently
  absorbed downstream failures.

## 17. Security and privacy implications

Throttling is one of the primary defences against a class of denial of
service that does not require exhausting network bandwidth, a flood of
legitimate-looking application-level requests, each individually cheap to
send and each individually expensive for the service to answer. Where a
service has no throttle, an attacker with a small number of clients can
exhaust the same shared resource that a genuine traffic surge would exhaust
naturally.

Azure's own considerations list flags a distinct attack surface directly.
"Normalize resource costs for different operations because they generally
don't carry equal execution costs... Ignoring per-operation cost can
exhaust capacity and create an attack vector"
([learn.microsoft.com, Throttling Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/throttling),
verified 2026-08-02). A throttle that counts every request as equally
expensive, regardless of whether it is a cheap cache read or an expensive
uncached write, lets an attacker pick the most expensive operation the
system offers and stay comfortably under a count-based limit while still
exhausting the resource the limit was meant to protect. Shopify's own
weighted-cost bucket, covered in dimension 9, is a production example of
pricing operations rather than merely counting them for exactly this
reason.

The classifier itself carries privacy implications the pattern's own
mechanics do not force a designer to consider. A throttle keyed on a raw
network address retains and logs that address as part of its normal
operation, and a throttle keyed on an authenticated identity retains and
logs that identity, both of which are personal data under most privacy
regimes and both of which need the same retention, access, and deletion
handling as any other logged identifier, not a special exemption because
the logging happens inside infrastructure code rather than application
code.

A rejection response is itself a small information disclosure. A precise
error naming exactly which limit was exceeded, exactly how many requests
remain, and exactly when the window resets gives an attacker doing
reconnaissance a clean, low-noise oracle for probing a system's internal
capacity and configuration, though the transparency that same precision
gives a legitimate, well-behaved caller is a genuine benefit and this is a
trade a designer makes deliberately, not a defect to eliminate outright.

Where a rejection is used as a signal to escalate, for example
automatically blocking a caller after repeated throttling, the escalation
logic itself becomes a new denial-of-service surface. An attacker who knows
that a threshold triggers an automatic block can trigger that block against
a legitimate caller's identity or address, if either is spoofable or
sharable, and get the system to deny service to someone it was never
targeting.

## 18. References

1. Alex Homer, John Sharp, Larry Brader, Masashi Narumoto, Trent Swanson,
   *Cloud Design Patterns, Prescriptive Architecture Guidance for Cloud
   Applications*, Microsoft patterns and practices, 2014, ISBN
   9781621140368, chapter "Throttling Pattern." Verified via
   [abebooks.com](https://www.abebooks.com/9781621140368/Cloud-Design-Patterns-Prescriptive-Architecture-1621140369/plp),
   2026-08-02.
2. Microsoft Learn, "Throttling Pattern, Azure Architecture Center,"
   [learn.microsoft.com/en-us/azure/architecture/patterns/throttling](https://learn.microsoft.com/en-us/azure/architecture/patterns/throttling),
   verified 2026-08-02.
3. Microsoft Learn, "Rate Limiting Pattern, Azure Architecture Center,"
   [learn.microsoft.com/en-us/azure/architecture/patterns/rate-limiting-pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/rate-limiting-pattern),
   verified 2026-08-02.
4. Microsoft Learn, "Microsoft Graph throttling guidance,"
   [learn.microsoft.com/en-us/graph/throttling](https://learn.microsoft.com/en-us/graph/throttling),
   verified 2026-08-02.
5. Shopify, "Rate limits,"
   [shopify.dev/docs/api/usage/rate-limits](https://shopify.dev/docs/api/usage/rate-limits),
   verified 2026-08-02.
6. Kubernetes, "API Priority and Fairness,"
   [kubernetes.io/docs/concepts/cluster-administration/flow-control](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/),
   verified 2026-08-02.
7. Netflix, `concurrency-limits`,
   [github.com/Netflix/concurrency-limits](https://github.com/Netflix/concurrency-limits),
   verified 2026-08-02.
8. Stripe, "Scaling your API with rate limiters,"
   [stripe.com/blog/rate-limiters](https://stripe.com/blog/rate-limiters),
   verified 2026-08-02.
9. Google, *Site Reliability Engineering*, chapter 21, "Handling
   Overload,"
   [sre.google/sre-book/handling-overload](https://sre.google/sre-book/handling-overload/),
   verified 2026-08-02.
10. nginx, `ngx_http_limit_req_module`,
    [nginx.org/en/docs/http/ngx_http_limit_req_module.html](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html),
    verified 2026-08-02.
11. Envoy, "Local rate limit," HTTP filter documentation,
    [envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/local_rate_limit_filter](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/local_rate_limit_filter),
    verified 2026-08-02.
12. Mark Nottingham, Roy T. Fielding, *RFC 6585, Additional HTTP Status
    Codes*, April 2012, section 4,
    [rfc-editor.org/rfc/rfc6585.html](https://www.rfc-editor.org/rfc/rfc6585.html),
    verified 2026-08-02.
13. Roy T. Fielding, Julian Reschke, editors, *RFC 9110, HTTP Semantics*,
    June 2022, section 10.2.3, "Retry-After,"
    [rfc-editor.org/rfc/rfc9110.html#name-retry-after](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after),
    verified 2026-08-02.
14. Van Jacobson, "Congestion Avoidance and Control," *ACM SIGCOMM
    Computer Communication Review*, 18, 4, August 1988, pages 314 to 329.

## Code

### Go, graceful degradation with tiered feature shedding and a hysteresis restore band

```go
package main

import (
	"fmt"
	"sync"
)

// Tier ranks a feature by how essential it is. Lower tiers shed first.
type Tier int

const (
	TierEssential Tier = iota
	TierStandard
	TierOptional
)

// Feature is one unit of functionality that can be turned off under load.
type Feature struct {
	Name string
	Tier Tier
	On   bool
}

// GracefulThrottle watches a load signal and turns features off tier by
// tier as load rises past named thresholds, then restores them in reverse
// order as load falls. It never touches TierEssential.
type GracefulThrottle struct {
	mu         sync.Mutex
	features   []*Feature
	softLimit  float64
	hardLimit  float64
	restoreGap float64 // hysteresis band so a feature does not flap
}

func NewGracefulThrottle(soft, hard, restoreGap float64) *GracefulThrottle {
	return &GracefulThrottle{softLimit: soft, hardLimit: hard, restoreGap: restoreGap}
}

func (g *GracefulThrottle) Register(f *Feature) {
	g.mu.Lock()
	defer g.mu.Unlock()
	f.On = true
	g.features = append(g.features, f)
}

// Observe applies the current utilization reading and returns which
// features changed state, in the order the change was made.
func (g *GracefulThrottle) Observe(utilization float64) []string {
	g.mu.Lock()
	defer g.mu.Unlock()

	var changed []string
	switch {
	case utilization >= g.hardLimit:
		for _, f := range g.features {
			if f.Tier != TierEssential && f.On {
				f.On = false
				changed = append(changed, fmt.Sprintf("shed %s (tier %d)", f.Name, f.Tier))
			}
		}
	case utilization >= g.softLimit:
		for _, f := range g.features {
			if f.Tier == TierOptional && f.On {
				f.On = false
				changed = append(changed, fmt.Sprintf("shed %s (tier %d)", f.Name, f.Tier))
			}
		}
	case utilization < g.softLimit-g.restoreGap:
		for i := len(g.features) - 1; i >= 0; i-- {
			f := g.features[i]
			if f.Tier != TierEssential && !f.On {
				f.On = true
				changed = append(changed, fmt.Sprintf("restore %s (tier %d)", f.Name, f.Tier))
			}
		}
	}
	return changed
}

func main() {
	th := NewGracefulThrottle(0.70, 0.90, 0.10)
	th.Register(&Feature{Name: "checkout", Tier: TierEssential})
	th.Register(&Feature{Name: "recommendations", Tier: TierStandard})
	th.Register(&Feature{Name: "live-inventory-badge", Tier: TierOptional})

	readings := []float64{0.55, 0.74, 0.93, 0.58}
	for _, u := range readings {
		changes := th.Observe(u)
		fmt.Printf("utilization %.2f -> %v\n", u, changes)
	}
}
```

Run with `go run main.go`. The verified output on this machine, `go version
go1.26.4 darwin/arm64`, was.

```
utilization 0.55 -> []
utilization 0.74 -> [shed live-inventory-badge (tier 2)]
utilization 0.93 -> [shed recommendations (tier 1)]
utilization 0.58 -> [restore live-inventory-badge (tier 2) restore recommendations (tier 1)]
```

Note the last line. At utilization 0.58, both tiers restore in the same
observation because 0.58 sits below `softLimit - restoreGap`, which is
0.60. A reading of, for example, 0.65 would sit inside the hysteresis band
itself and restore nothing, which is the flapping-prevention behaviour
dimension 11 names.

### Python, adaptive concurrency limiter, Vegas-style gradient

```python
"""Adaptive concurrency throttle, inspired by the Vegas algorithm in
Netflix's concurrency-limits library. It infers a safe in-flight limit
from round-trip latency instead of enforcing a fixed requests-per-second
number, so the limit tracks the resource the caller actually saturates."""

from dataclasses import dataclass, field
from statistics import mean


@dataclass
class AdaptiveThrottle:
    min_limit: int = 4
    max_limit: int = 200
    limit: float = 10.0
    smoothing: float = 0.2
    in_flight: int = 0
    _min_rtt: float | None = field(default=None, init=False)
    _samples: list[float] = field(default_factory=list, init=False)

    def try_acquire(self) -> bool:
        if self.in_flight >= self.limit:
            return False
        self.in_flight += 1
        return True

    def release(self, rtt_ms: float, rejected: bool = False) -> None:
        self.in_flight = max(0, self.in_flight - 1)
        if rejected:
            self.limit = max(self.min_limit, self.limit * 0.7)
            return
        self._samples.append(rtt_ms)
        if self._min_rtt is None or rtt_ms < self._min_rtt:
            self._min_rtt = rtt_ms
        if len(self._samples) < 5:
            return
        window = self._samples[-5:]
        current_rtt = mean(window)
        # Queuing delay in units of the estimated no-queue RTT is the
        # Vegas gradient signal. A ratio near 1 means no queuing.
        gradient = self._min_rtt / current_rtt if current_rtt else 1.0
        target = self.limit * gradient
        self.limit += self.smoothing * (target - self.limit)
        self.limit = max(self.min_limit, min(self.max_limit, self.limit))
        self._samples.clear()


def simulate() -> None:
    th = AdaptiveThrottle(limit=10.0)
    # Healthy RTTs, the limit should drift toward its ceiling behaviour.
    for rtt in [20, 21, 19, 22, 20, 21, 20, 19, 22, 21, 20, 21, 19, 20, 21]:
        th.release(rtt)
    print(f"after healthy traffic: limit={th.limit:.1f}")
    # Latency doubles under saturation, the limit should contract.
    for rtt in [40, 42, 45, 41, 43, 44, 46, 42, 45, 43]:
        th.release(rtt)
    print(f"after saturation: limit={th.limit:.1f}")
    # A hard rejection from the backend should cut the limit sharply.
    th.release(rtt_ms=0, rejected=True)
    print(f"after a rejection: limit={th.limit:.1f}")


if __name__ == "__main__":
    simulate()
```

Run with `python3 adaptive.py` on `Python 3` as installed on this machine.
The verified output was.

```
after healthy traffic: limit=9.6
after saturation: limit=7.6
after a rejection: limit=5.3
```

The limit drifts down as measured latency rises relative to its own
no-queue baseline, then contracts sharply on an explicit rejection, which
is the shape dimension 8 describes for concurrency-based adaptive
throttling generally.

### Rust, priority-based admission with per-tenant fairness

```rust
// Priority-based throttle with per-tenant fairness, in the spirit of
// Kubernetes API Priority and Fairness. Each priority level owns a
// fixed share of total concurrency seats so a flood in one tenant or
// one priority cannot starve another.
use std::collections::HashMap;

#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
enum Priority {
    Critical,
    Standard,
    Sheddable,
}

struct PriorityThrottle {
    total_seats: u32,
    shares: HashMap<Priority, u32>,
    in_use: HashMap<Priority, u32>,
}

impl PriorityThrottle {
    fn new(total_seats: u32) -> Self {
        // Concurrency is split by weight, not by a hard ceiling per
        // level, so an idle level's headroom is not wasted but a busy
        // level can never take more than its share plus true slack.
        let mut shares = HashMap::new();
        shares.insert(Priority::Critical, total_seats * 50 / 100);
        shares.insert(Priority::Standard, total_seats * 35 / 100);
        shares.insert(Priority::Sheddable, total_seats * 15 / 100);
        PriorityThrottle {
            total_seats,
            shares,
            in_use: HashMap::new(),
        }
    }

    fn seats_in_use(&self) -> u32 {
        self.in_use.values().sum()
    }

    fn try_admit(&mut self, p: Priority) -> bool {
        let used_here = *self.in_use.get(&p).unwrap_or(&0);
        let share = *self.shares.get(&p).unwrap_or(&0);
        let total_used = self.seats_in_use();

        let within_own_share = used_here < share;
        let spare_capacity = self.total_seats.saturating_sub(total_used);
        // A level may borrow beyond its own share only while the fleet
        // has genuine spare seats, and only for the higher-urgency
        // levels. The sheddable level never borrows past its own share.
        let may_borrow = p != Priority::Sheddable && spare_capacity > 0;

        if within_own_share || may_borrow {
            *self.in_use.entry(p).or_insert(0) += 1;
            true
        } else {
            false
        }
    }

    fn release(&mut self, p: Priority) {
        if let Some(count) = self.in_use.get_mut(&p) {
            *count = count.saturating_sub(1);
        }
    }
}

fn main() {
    let mut t = PriorityThrottle::new(20);

    let mut admitted_critical = 0;
    for _ in 0..15 {
        if t.try_admit(Priority::Critical) {
            admitted_critical += 1;
        }
    }
    println!("critical admitted out of 15 requests: {}", admitted_critical);

    let mut admitted_sheddable = 0;
    let mut rejected_sheddable = 0;
    for _ in 0..10 {
        if t.try_admit(Priority::Sheddable) {
            admitted_sheddable += 1;
        } else {
            rejected_sheddable += 1;
        }
    }
    println!(
        "sheddable admitted {} rejected {} while critical holds the fleet",
        admitted_sheddable, rejected_sheddable
    );

    t.release(Priority::Critical);
    let standard_after_release = t.try_admit(Priority::Standard);
    println!("standard admitted after a release: {}", standard_after_release);
}
```

Compiled with `rustc -O priority.rs -o priority`, `rustc 1.97.1` as
installed on this machine. The verified output was.

```
critical admitted out of 15 requests: 15
sheddable admitted 3 rejected 7 while critical holds the fleet
standard admitted after a release: true
```

Fifteen critical requests all fit inside the twenty-seat fleet even though
critical's own guaranteed share is ten seats, because critical is allowed
to borrow the fleet's spare capacity. The sheddable priority is capped at
exactly its own three-seat share, admitting three and rejecting seven, even
though seats remain physically available in the fleet, because sheddable
traffic is never permitted to borrow, which is the fairness guarantee
dimension 8 describes for Kubernetes API Priority and Fairness. After one
critical request releases its seat, a standard request is admitted
immediately, confirming that seats return to the shared pool rather than
staying pinned to the level that first claimed them.

A fourth language, Java, was not used for this entry. No Java Runtime
Environment was available on the machine this entry was authored on, `javac
-version` returned "Unable to locate a Java Runtime," so no Java sample here
was compiled, and none is included rather than presented as though it had
been.
