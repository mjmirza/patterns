---
name: Bulkhead
slug: bulkhead
family: 08-cloud-distributed
category: Resilience
aliases: [Resource Isolation, Compartmentalization, Cell-Based Architecture, Partition]
first_described: "Michael T. Nygard 2007"
maturity: canonical
related: [circuit-breaker, timeout, retry, rate-limiter, load-shedding, backpressure, queue-based-load-leveling]
incompatible_with: []
verified: 2026-08-02
---

# Bulkhead

## 1. Name, aliases, and lineage

The canonical name is Bulkhead. Michael T. Nygard introduced it to software
engineering in *Release It! Design and Deploy Production-Ready Software*,
Pragmatic Bookshelf, 2007, in the stability patterns material, alongside Circuit
Breaker and Timeout ([Bulkhead pattern, Wikipedia](https://en.wikipedia.org/wiki/Bulkhead_pattern),
verified 2026-08-02). The second edition, Pragmatic Bookshelf, 2018, carries the
same pattern in the stability patterns chapter ([Release It! Second Edition,
Pragmatic Bookshelf](https://pragprog.com/titles/mnee2/release-it-second-edition/),
verified 2026-08-02).

The metaphor is naval. A ship's hull is divided by transverse walls into
watertight compartments, so a hull breach floods one compartment rather than the
whole vessel. Microsoft's Azure Architecture Center states the analogy in those
terms, that if the hull is compromised only the damaged section fills with water,
which keeps the ship afloat ([Bulkhead pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
verified 2026-08-02).

Several names circulate for the same idea at different scopes.

- **Bulkhead** is the standard name when the partition is a pool of concurrency,
  connections, or threads inside one process.
- **Cell-based architecture** is the name when the partition is a full deployment
  unit serving a subset of traffic. Azure treats the two as the same pattern at
  different granularity, listing cell-based architecture directly as an alias in
  the pattern's opening line ([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
  verified 2026-08-02).
- **Resource isolation** and **compartmentalization** are descriptive names used
  in library documentation. Resilience4j documents the pattern under the module
  name Bulkhead and describes it as limiting the number of concurrent executions
  ([Resilience4j Bulkhead documentation](https://resilience4j.readme.io/docs/bulkhead),
  verified 2026-08-02).
- **Partition** appears in database and queue contexts. Note that partitioning
  for throughput and partitioning for isolation are different goals that happen
  to use the same word. Sharding to spread load is not a bulkhead unless the
  shards also fail independently.

The most common confusion is with Circuit Breaker. A bulkhead limits how much of
a shared resource one dependency may consume at any instant. A circuit breaker
stops calling a dependency entirely after a failure threshold. They solve
adjacent problems and are routinely deployed together, but a bulkhead protects
the caller even when the dependency is slow rather than failing, which is the
case a circuit breaker keyed on errors will miss. Netflix documented exactly this
in the Hystrix design notes, observing that latency without errors is the harder
case because it consumes caller resources without ever tripping an error-based
signal ([Hystrix How it Works, Netflix](https://github.com/Netflix/Hystrix/wiki/How-it-Works),
verified 2026-08-02).

## 2. Problem and context

A process holds a finite pool of something that every request needs. Threads in a
servlet container. Connections in a database pool. File descriptors. Memory.
Goroutines bounded by scheduler pressure. Slots in an event loop's concurrency
budget. That pool is shared across every code path the process serves.

One downstream dependency becomes slow. Not broken, slow. Its median latency
moves from 20 milliseconds to 8 seconds because it is garbage collecting, or its
own database is doing a full table scan, or a network path is retransmitting.
Requests to that dependency do not fail. They occupy a thread and wait.

Arrival rate has not changed. Service rate for that one path has collapsed. By
Little's Law the number of concurrent requests in flight for that path grows
until it equals arrival rate multiplied by the new latency. At 200 requests per
second and 8 seconds of latency, that path alone wants 1600 concurrent slots. A
container tuned for 200 threads has 200. Every one of them ends up parked on the
slow dependency.

Now the failure spreads. A request for a completely unrelated endpoint arrives.
It needs a thread. There are none, because all 200 are blocked waiting on a
dependency that request never touches. The health check endpoint arrives. It also
needs a thread. It times out. The load balancer removes the instance. Traffic
shifts to the remaining instances, which now receive a higher share of the same
poisoned traffic, and they saturate faster. Azure's description of this sequence
is exact. Resource exhaustion in a consumer means requests to other services are
affected, and eventually the consumer cannot send requests to any service, not
only the original unresponsive one ([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
verified 2026-08-02).

The observable symptom is the thing worth memorising. **A dependency that
represents two percent of traffic takes down one hundred percent of the service,
and the error rate on the failing dependency looks normal in the dashboard
because the calls are succeeding, slowly.** Operators chase the wrong service for
the first thirty minutes of the incident because the alert fires on the healthy
endpoints, not the sick one.

The context in which the bulkhead is the right answer has four parts.

- The process serves more than one class of work, and those classes have
  different importance or different downstream dependencies.
- Some resource is shared across those classes and is finite.
- At least one dependency can become slow without becoming unavailable.
- Degrading one class of work is preferable to degrading all of them.

Remove any of the four and the pattern is overhead. A single-purpose worker that
does exactly one thing gains nothing from partitioning a pool it is the only
user of.

## 3. Forces

Judgement is involved in weighing these. The direction of each pressure is
determined by the mechanism, the magnitude is a matter of context.

- **Blast radius.** Favoured, and this is the whole point. A fault is confined to
  the partition that contains it. Everything else in the trade is paid to buy
  this one property.
- **Utilisation.** Sacrificed, unavoidably. Partitioned capacity cannot be
  reallocated on demand. Azure names this directly in its when-not-to-use list,
  saying the pattern may not suit a project where less efficient use of resources
  is unacceptable ([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
  verified 2026-08-02). Dimension 10 quantifies the loss.
- **Latency.** Sacrificed slightly for thread-pool isolation, close to neutral for
  semaphore isolation. Netflix measured the overhead of running a command on a
  separate thread rather than the calling thread at a load of 60 requests per
  second, finding no measurable cost at the median, 3 milliseconds at the
  ninetieth percentile, and 9 milliseconds at the ninety-ninth ([Hystrix How it
  Works](https://github.com/Netflix/Hystrix/wiki/How-it-Works), verified
  2026-08-02).
- **Coupling.** Favoured. Each caller now depends on a named, bounded budget for
  each dependency rather than on the global health of a shared pool. The failure
  domain becomes explicit in configuration.
- **Operability.** Favoured on diagnosis, sacrificed on tuning. When a bulkhead
  rejects, the rejection names the dependency, which turns a mystery outage into
  a labelled counter. The cost is that every bulkhead is a number somebody has to
  choose, and a wrong number is a self-inflicted outage.
- **Cost.** Sacrificed. Isolation at the process or pod level means paying for
  capacity that sits idle in the partitions that are not busy. Isolation inside a
  process costs memory per thread and scheduler pressure.
- **Cognitive load.** Sacrificed. A reader tracing a request now has to know which
  pool it runs on, whether that pool has a queue, and what happens when the queue
  is full. Three new failure paths exist where there was one.
- **Consistency.** Neutral to sacrificed. Thread-pool isolation moves work off the
  calling thread, which breaks thread-local state. Anything relying on a thread
  local, a request-scoped context, or a security principal bound to the thread has
  to be propagated explicitly.
- **Team topology.** Favoured. A bulkhead per dependency draws a line that maps
  cleanly to team ownership. The team that owns the slow dependency owns the
  budget assigned to it, and its failure is contained inside its own name.

The pattern trades average-case efficiency for worst-case survivability. That is
a bad trade when the worst case does not happen, and the only trade that matters
when it does.

## 4. Applicability and non-applicability

Reach for a bulkhead when the following hold.

- A process calls two or more downstream dependencies with different reliability
  characteristics, and one of them can go slow without going down.
- A service has tiers of consumers, and a lower tier must not be able to starve a
  higher tier. Azure lists isolating critical consumers from standard consumers
  as a primary use ([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
  verified 2026-08-02).
- The system is multi-tenant and one tenant's traffic spike must not become every
  tenant's outage.
- A background or batch path shares a resource pool with an interactive path. The
  batch path will win the race for the pool every time unless bounded.
- A dependency's timeout is long relative to its latency budget. A five second
  timeout on a call that normally takes 30 milliseconds is a 160x amplification
  waiting to consume the pool.
- The service must keep its health check and its liveness path answerable under
  saturation of every other path.

Do NOT reach for a bulkhead in these cases. This non-applicability list is the
part most treatments omit, and the reason matters more than the rule.

- **The process serves one class of work with one dependency.** Partitioning a
  pool with a single user leaves it exactly as it was, plus a configuration
  parameter that can now be set wrong. The failure mode you add exceeds the
  failure mode you remove.
- **Capacity is already tight.** A bulkhead makes the effective capacity lower
  than the nominal capacity, always. If the service is already running at
  utilisation where a small traffic increase causes queueing, partitioning that
  capacity will cause rejections during normal operation. Fix capacity first,
  then partition.
- **The dependency fails fast rather than slowly.** If a downstream returns a
  connection refused in under a millisecond, it is not holding caller concurrency
  long enough to matter. A circuit breaker plus a retry budget is the right tool.
  Isolation buys nothing against a fast failure.
- **The work is CPU-bound rather than IO-bound.** A semaphore bulkhead around CPU
  work does not stop the CPU from being consumed. The operating system scheduler
  is already the arbiter. What you want is a cgroup CPU quota or a lower thread
  priority, not a concurrency semaphore.
- **The resource is not actually shared.** Isolating a per-request allocation
  that has no pool behind it is theatre. Verify that the resource under
  contention is genuinely finite and genuinely shared before partitioning it.
- **The platform already does it.** Azure explicitly advises using built-in
  platform controls such as API Management rate limits, Cosmos DB request unit
  isolation, and resource limits in Kubernetes or Container Apps, rather than
  recreating throttling and isolation in application code ([Azure Architecture
  Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
  verified 2026-08-02). A hand-rolled semaphore inside a pod that already has a
  CPU limit adds a second, less observable, less correct limiter.
- **Nobody will tune it.** A bulkhead is a number that must track the dependency's
  latency and the service's traffic. If no team owns that number, it will be set
  once at a guess and never revisited, and the first time traffic doubles it will
  become the cause of the outage rather than the cure. An untended bulkhead is
  worse than none, because it fails in a way that looks like the dependency's
  fault.
- **The correct answer is a queue.** If the work can be made asynchronous and
  durable, Queue-Based Load Levelling absorbs the burst rather than rejecting it.
  A bulkhead sheds load. A queue defers it. Shedding a payment is worse than
  deferring it.

## 5. Structure

The participants below hold across all three isolation mechanisms. What changes
between mechanisms is what the Permit physically is.

- **Caller.** Application code that wants to invoke a dependency. It does not
  know the partition exists beyond asking to enter it.
- **Bulkhead.** The guard that owns a fixed budget of Permits for exactly one
  Partition Key. It decides admit, queue, or reject, and it is the only component
  that knows the budget.
- **Permit.** The unit of the finite resource. A semaphore count, a worker
  thread, a pooled connection, a CPU quota slice, or a pod. The Permit is what
  makes the budget physical.
- **Partition Key.** The identity that the budget is scoped to. Usually a
  downstream dependency name, but it can be a tenant, a consumer tier, an
  endpoint class, or a priority band. Choosing this key is the design decision
  that determines whether the bulkhead works.
- **Admission Queue.** Optional. A bounded holding area for callers waiting on a
  Permit. Present in thread-pool isolation, present as a maximum wait duration in
  semaphore isolation, absent when the bulkhead rejects immediately.
- **Rejection Policy.** What happens when no Permit is available and the queue is
  full or absent. Fail fast, fall back to a degraded response, shed to a
  different partition, or block for a bounded time.
- **Protected Resource.** The downstream dependency, connection pool, or compute
  budget the Bulkhead exists to shield the rest of the process from.

The relationships. One Caller talks to many Bulkheads, one per Partition Key. One
Bulkhead owns exactly one budget of Permits and one Rejection Policy. Bulkheads
never share Permits, and that non-sharing is the entire mechanism. A Bulkhead
that can borrow from another Bulkhead under pressure is not a bulkhead, it is a
weighted fair queue, which is a different pattern with different guarantees.

## 6. ASCII structure diagram

```
                        +---------------------------+
   incoming requests    |         Caller            |
   ------------------>  |  (application code)       |
                        +---+---------+---------+---+
                            |         |         |
              partition key |         |         | partition key
                "payments"  |         |         |  "search"
                            v         v         v
              +-------------------+ +-----+ +-------------------+
              |    Bulkhead A     | | ... | |    Bulkhead C     |
              |  permits  20 / 20 | |     | |  permits   4 / 4  |
              |  queue     0 / 10 | |     | |  queue    10 / 10 |
              |  policy fail-fast | |     | |  policy  fallback |
              +---------+---------+ +--+--+ +----+---------+----+
                        |              |         |         |
                    admitted       admitted  admitted   REJECTED
                        |              |         |         |
                        v              v         v         v
              +-------------------+ +-----+ +----------+ +----------+
              |  Protected        | | ... | | Protected| | degraded |
              |  Resource         | |     | | Resource | | response |
              |  payments API     | |     | | search   | | (cached) |
              +-------------------+ +-----+ +----------+ +----------+

   Key property. Bulkhead C exhausting its 4 permits and 10 queue slots
   has no effect on Bulkhead A's 20 permits. No permit crosses the wall.
```

## 7. Dynamics

The runtime behaviour that matters is what happens as a dependency degrades. The
sequence below shows one partition saturating while a neighbour stays healthy.

```
 t=0    dependency C healthy, p99 = 40ms
 -----------------------------------------------------------------
 Caller -> BulkheadC.acquire()          permits 1/4   admitted
 Caller -> C                            40ms
 Caller <- C ok
 Caller -> BulkheadC.release()          permits 0/4

 t=30s  dependency C degrades to 6000ms, arrival rate unchanged
 -----------------------------------------------------------------
 Caller -> BulkheadC.acquire()          permits 4/4   admitted
 Caller -> BulkheadC.acquire()          permits 4/4   -> QUEUE 1/10
 Caller -> BulkheadC.acquire()          permits 4/4   -> QUEUE 2/10
   ...    (queue fills over ~2s at 5 rps)
 Caller -> BulkheadC.acquire()          queue 10/10   -> REJECT
                                        |
                                        +-> RejectionPolicy
                                            emit bulkhead_rejected{dep="C"}
                                            return cached / degraded result
                                            latency 2ms, not 6000ms

 t=30s  SAME INSTANT, dependency A still healthy
 -----------------------------------------------------------------
 Caller -> BulkheadA.acquire()          permits 3/20  admitted
 Caller -> A                            18ms
 Caller <- A ok                         UNAFFECTED

 t=90s  timeout on C fires, permits recycle at 4 / timeout interval
 -----------------------------------------------------------------
 Caller -> C  [timeout 2000ms]          TIMEOUT
 Caller -> BulkheadC.release()          permits 3/4
                                        queued caller admitted
```

Three properties of that flow decide whether the bulkhead works.

**A bulkhead without a timeout is not a bulkhead.** Permits are released when
work completes. If work never completes, permits never return, and the partition
is permanently saturated rather than temporarily. The timeout is what makes the
permit a rental rather than a gift. Netflix's own documentation makes the
corresponding point about semaphores, that a semaphore-isolated dependency which
becomes slow leaves the parent thread blocked until the underlying network call
times out, because the semaphore cannot interrupt the caller ([Hystrix How it
Works](https://github.com/Netflix/Hystrix/wiki/How-it-Works), verified
2026-08-02).

**The queue converts rejection into latency.** A ten-slot queue in front of a
four-permit pool serving six-second calls means the last caller in the queue
waits fifteen seconds before it even starts. If the caller's own deadline is two
seconds, those queue slots produce work that nobody will read. Bound the wait,
not only the queue depth. Resilience4j's semaphore bulkhead exposes exactly this
as `maxWaitDuration`, defaulting to zero, meaning reject immediately rather than
wait ([Resilience4j Bulkhead documentation](https://resilience4j.readme.io/docs/bulkhead),
verified 2026-08-02).

**Steady-state throughput under degradation is permits divided by latency.** Four
permits against six-second calls is 0.67 requests per second, whatever the
arrival rate. Everything above that is rejected. This is arithmetic, not tuning,
and it is the number to compute before choosing the permit count.

## 8. Implementation variants

Three mechanisms are in common use, and they differ in what they can interrupt,
what they cost, and what they can protect.

### Variant A. Semaphore isolation

A counter guards entry. The caller runs the work on its own thread after taking a
permit, and returns the permit when the work finishes or throws.

Cost is close to zero. No context switch, no extra thread, no thread-local
propagation problem. This makes it the correct choice on runtimes where a thread
is expensive or where the work is already asynchronous, and on single-threaded
event loops where there is no second thread to hand work to.

The limitation is that a semaphore cannot interrupt the caller. Netflix states
this plainly. A semaphore-isolated dependency that becomes latent leaves the
parent threads blocked until the underlying network calls time out ([Hystrix How
it Works](https://github.com/Netflix/Hystrix/wiki/How-it-Works), verified
2026-08-02). The consequence is that semaphore isolation depends entirely on the
transport-level timeout being set and being correct. A socket read timeout that
is unset, or set to an infinite default, turns a semaphore bulkhead into a slow
leak of permits that never return.

Resilience4j's `SemaphoreBulkhead` implements this variant with two settings,
`maxConcurrentCalls` defaulting to 25 and `maxWaitDuration` defaulting to zero
milliseconds ([Resilience4j Bulkhead documentation](https://resilience4j.readme.io/docs/bulkhead),
verified 2026-08-02).

### Variant B. Thread pool isolation

Each partition owns a dedicated pool of worker threads and a bounded queue. The
caller submits work and receives a future. The caller's own thread is never the
one that blocks on the dependency.

This is the only in-process variant that gives true timeout enforcement, because
the calling thread holds a future it can abandon while the worker thread remains
stuck. It also isolates against a dependency's client library misbehaving, since
the misbehaviour is confined to threads the pool owns.

The cost is real. Netflix measured 3 milliseconds at the ninetieth percentile and
9 milliseconds at the ninety-ninth for the hop onto a separate thread, and
accepted it, noting that the Netflix API processed more than 10 billion Hystrix
command executions per day using thread isolation with more than 40 thread pools
per API instance ([Hystrix How it Works](https://github.com/Netflix/Hystrix/wiki/How-it-Works),
verified 2026-08-02). Forty pools is forty sets of threads whose memory and
scheduler cost is paid whether or not the pools are busy.

The second cost is context propagation. Thread locals, MDC logging context,
security principals, and OpenTelemetry spans bound to the calling thread do not
follow the work onto the worker thread unless explicitly copied. This is the most
common source of bugs when converting semaphore isolation to thread pool
isolation, and it produces log lines with the wrong trace identifier rather than
an exception, so it is found late.

Resilience4j's `ThreadPoolBulkhead` implements this variant, with
`maxThreadPoolSize` defaulting to the number of available processors,
`coreThreadPoolSize` to available processors minus one, and `queueCapacity` to
100 ([Resilience4j Bulkhead documentation](https://resilience4j.readme.io/docs/bulkhead),
verified 2026-08-02).

### Variant C. Process, container, or pod isolation

The partition is a separate operating system process, container, or scheduling
unit, with its own memory, its own CPU quota, and its own crash domain.

This is the only variant that survives the failure modes the other two cannot
touch. A memory leak, a native crash, a runaway garbage collection pause, a
kernel-level file descriptor exhaustion. Nothing inside a process protects the
process from itself.

Kubernetes implements this with requests and limits. The scheduler uses requests
to decide placement, and the kubelet enforces limits at runtime ([Managing
Resources for Containers, Kubernetes documentation](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/),
verified 2026-08-02). The enforcement mechanism differs by resource in a way that
matters for isolation design. CPU limits are enforced by throttling, described in
that documentation as a hard limit the kernel enforces, so a container may not
use more CPU than its limit. Memory limits are enforced by out-of-memory kills,
and the same documentation is explicit that terminations happen only when the
kernel detects memory pressure, so a container that over-allocates memory may not
be killed immediately ([Kubernetes documentation](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/),
verified 2026-08-02).

The practical reading of that asymmetry is worth stating plainly. **CPU isolation
degrades the offender, memory isolation kills it, and the kill is not prompt.** A
pod leaking memory inside its limit is a bulkhead working correctly. A pod
leaking memory on a node under pressure can be killed alongside neighbours if
requests were set too low, which is the bulkhead failing because the wall was
drawn in the wrong place.

Azure's example for the pattern is exactly a pod spec with requests of 64Mi and
250m CPU and limits of 128Mi and 1 CPU ([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
verified 2026-08-02).

### Variant D. Connection pool partitioning

A specialisation of semaphore isolation where the permit is a pooled connection.
Rather than one connection pool shared across all downstream targets, each target
gets its own pool with its own maximum size.

Azure's first diagram for the pattern is exactly this shape, bulkheads structured
around connection pools calling individual services, where a failure in Service A
isolates that pool while workloads using Service B and C continue ([Azure
Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
verified 2026-08-02).

This variant is the highest value per unit of effort in most systems, because
connection pools are already present and already the scarcest resource. A single
shared HTTP client with a global connection cap is the most common unintentional
shared-fate resource in a service-oriented system, and splitting it per
destination is usually a configuration change rather than a code change.

Envoy implements this at the sidecar level. It enforces, per upstream cluster and
per priority, a maximum connections, a maximum pending requests, a maximum
requests, a maximum active retries, and a maximum concurrent connection pools.
The documentation names the benefit as enforcing these limits at the network
level rather than having to configure and code each application independently
([Circuit breaking, Envoy documentation](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking),
verified 2026-08-02). Note the naming. Envoy files these under circuit breaking,
but the mechanism described is concurrency limiting per cluster, which is a
bulkhead by the definitions in this entry.

### Variant E. Deployment-level cells

The partition is a full stack, and traffic is routed to a cell by a partition key
such as tenant, region, or account hash. Azure's second diagram for the pattern
shows exactly this, multiple clients each assigned to a separate service
instance, so a client that overwhelms its instance leaves the others unaffected
([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
verified 2026-08-02).

The strength is that a cell contains everything, including deployment risk, since
a bad release can be rolled to one cell first. The cost is the highest of any
variant, because every cell needs a full set of infrastructure and the routing
layer becomes a new single point of failure that must itself be partitioned or
made stateless.

### Mechanism comparison

| Property | Semaphore | Thread pool | Pod or process |
|---|---|---|---|
| Interrupts a stuck caller | no | yes | yes, by kill |
| Protects against memory leak | no | no | yes |
| Protects against native crash | no | no | yes |
| Added latency at p99 | negligible | about 9 ms measured by Netflix | none in the call path |
| Context propagation cost | none | thread locals must be copied | full serialisation |
| Works on a single-threaded event loop | yes | not applicable | yes |
| Granularity achievable | per call site | per dependency | per deployment unit |
| Reconfiguration cost | a number | a number plus threads | a rollout |

## 9. Known production uses

**Netflix Hystrix.** Hystrix assigned each downstream dependency its own thread
pool, and Netflix reported processing more than 10 billion Hystrix command
executions per day using thread isolation, with more than 40 thread pools per API
instance ([Hystrix How it Works, Netflix](https://github.com/Netflix/Hystrix/wiki/How-it-Works),
verified 2026-08-02). Hystrix is now in maintenance mode. The project README
states it is no longer in active development, that version 1.5.18 is stable
enough for Netflix's existing applications, and recommends Resilience4j for new
projects ([Netflix/Hystrix README](https://github.com/Netflix/Hystrix), verified
2026-08-02). This history matters because the industry's mental model of the
pattern is largely Hystrix's model, including the assumption that thread pools
are the default, which Resilience4j deliberately reversed.

**Resilience4j.** The JVM successor, shipping both `SemaphoreBulkhead` and
`ThreadPoolBulkhead` as separate implementations with separate configuration
surfaces, documented with the defaults listed in dimension 8 ([Resilience4j
Bulkhead documentation](https://resilience4j.readme.io/docs/bulkhead), verified
2026-08-02). The documentation notes that unlike Hystrix it provides no shadow
thread pool for the semaphore variant, so callers manage their own thread sizing
in line with the bulkhead configuration.

**Kubernetes requests and limits.** Pod-level isolation as a platform primitive.
The scheduler places by request, the kubelet enforces by limit, CPU by throttling
and memory by out-of-memory kill ([Managing Resources for Containers, Kubernetes
documentation](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/),
verified 2026-08-02). Every workload running on Kubernetes with limits set is
running a bulkhead whether or not the team calls it that.

**Envoy proxy.** Per-cluster concurrency limits enforced in the data plane,
covering connections, pending requests, requests, retries, and connection pools
([Circuit breaking, Envoy documentation](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking),
verified 2026-08-02). This places the bulkhead outside the application, which
means it applies uniformly across languages and cannot be bypassed by application
code that forgot to wrap a call.

**Polly.** The .NET resilience library, named by Microsoft alongside Resilience4j
as a framework for creating consumer bulkheads ([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
verified 2026-08-02). The library's own documentation is at
[pollydocs.org](https://www.pollydocs.org/), verified 2026-08-02.

## 10. Consequences

The direction of each consequence follows from the mechanism. The magnitudes
below are engineering judgement supported by the arithmetic shown.

### Positive

- **A slow dependency cannot consume the whole process.** This is the property
  everything else is paid for.
- **The failure becomes labelled.** A rejection counter tagged by partition key
  names the sick dependency at the moment of saturation, rather than leaving
  operators to infer it from a pool exhaustion stack trace.
- **Partial availability replaces total unavailability.** Losing the
  recommendations panel is a different incident from losing checkout.
- **Timeouts become enforceable.** Thread pool and process isolation give a way to
  abandon work that a stuck caller cannot abandon by itself.
- **Capacity planning becomes explicit.** Choosing a permit count forces somebody
  to state the expected concurrency of a dependency, which is a number most teams
  have never written down.
- **Deployment risk shrinks with cell isolation.** A release rolled to one cell
  exposes a fraction of traffic to a regression.

### Negative

- **Utilisation loss is structural, not incidental.** Split a pool of 100 permits
  across five equal partitions and each dependency is now capped at 20, even when
  the other four partitions are idle. Under a skewed load where one dependency
  carries 60 percent of traffic, that dependency is held to 20 percent of the
  resource, so the service rejects work while 60 permits sit unused. Sizing
  partitions to peak per-dependency demand rather than to average demand means
  total allocation exceeds total capacity, which is the standard fix and it
  reintroduces shared fate at the extreme. **There is no partitioning that is
  both isolating and fully utilising. Pick the loss you can afford.** A useful
  planning number. If partition sizes are set to each dependency's p99
  concurrency, expected idle capacity at the median is roughly the gap between
  p50 and p99 concurrency summed across partitions, which in a bursty service is
  commonly a large fraction of the total.
- **Every bulkhead is a new configuration surface that can be wrong.** Set too
  low, it becomes the outage. Set too high, it does nothing. Both failure modes
  are silent until load arrives.
- **Latency cost on the thread pool variant.** The measured 9 milliseconds at p99
  is small against a slow dependency and large against a 2 millisecond cache
  lookup. Applying thread pool isolation uniformly to fast in-memory calls is a
  real regression.
- **Memory and scheduler cost of many pools.** Forty pools of ten threads is 400
  threads, each with a stack, most of them idle.
- **Debugging gets a layer.** A stack trace now shows a worker thread with no
  connection to the request that submitted the work, unless context was
  propagated deliberately.
- **False safety.** A bulkhead around a call whose client library maintains its
  own internal unbounded queue protects nothing. The work is bounded at
  submission and unbounded inside the library.

## 11. Failure modes and misuse

These are drawn from practice and are labelled as such. Each is written as
symptom, cause, fix, because the symptom is the part a reader will actually meet.

**Bulkhead without a timeout.**
*Symptom.* Rejection rate for one partition rises to 100 percent and stays there
after the dependency recovers. Permit gauge pinned at maximum. Restarting the
process clears it.
*Cause.* Permits are released on completion. Work that never completes never
returns its permit. A missing or infinite socket read timeout makes a permit a
one-way allocation.
*Fix.* Set an explicit transport timeout below the bulkhead's implied service
time, and pair it with a queue wait bound. Verify by injecting a black-hole
endpoint that accepts a connection and never responds.

**Sized from average load rather than from Little's Law.**
*Symptom.* The bulkhead rejects during a normal traffic peak, with the dependency
healthy and its latency unchanged.
*Cause.* The permit count was chosen as a round number rather than computed as
arrival rate multiplied by expected latency, with headroom.
*Fix.* Compute the required concurrency at p99 latency and p99 arrival rate, then
add margin. Recompute when either changes. Alert on sustained utilisation above
70 percent of permits as a sizing signal, separately from alerting on rejections.

**The partition key is wrong.**
*Symptom.* One tenant's traffic spike still degrades other tenants, despite a
bulkhead being in place and its metrics looking healthy.
*Cause.* The bulkhead was keyed by downstream dependency when the contended axis
was tenant, or the reverse. The wall was built, but not across the direction the
water flows.
*Fix.* Identify the axis along which failures actually correlate before choosing
the key. If both axes matter, nest them, accepting the utilisation cost of the
product of the two.

**Queue depth used as the only bound.**
*Symptom.* Rejections are near zero, but total request latency at p99 exceeds the
client's timeout, and the client retries work that the server is still executing.
*Cause.* A deep queue converts rejection into unbounded waiting. The server
happily accepts work that nobody is waiting for any more.
*Fix.* Bound the wait, not only the depth. Drop work whose deadline has already
passed at dequeue time rather than executing it.

**Retry storm through the bulkhead.**
*Symptom.* Rejection rate rises superlinearly as a dependency degrades, far
faster than arrival rate.
*Cause.* Rejections are fast, so a naive retry loop retries them immediately,
multiplying arrival rate at the exact moment capacity fell. The bulkhead is doing
its job and the retry layer is undoing it.
*Fix.* Treat a bulkhead rejection as non-retryable at the immediate layer, or
apply a retry budget with exponential backoff and jitter. Never retry a
saturation signal without backoff.

**Thread-local context lost on migration to thread pool isolation.**
*Symptom.* Logs and traces from inside the dependency call carry the wrong or a
missing trace identifier. Security checks inside the call see an anonymous
principal. Nothing throws.
*Cause.* Work moved off the calling thread and the thread-bound context did not
follow.
*Fix.* Capture context at submission and restore it in the worker, using the
runtime's context propagation facility. Add a test that asserts the trace
identifier inside the worker equals the one at submission.

**Health check sharing a partition with application traffic.**
*Symptom.* Instances are removed from the load balancer during a partial
degradation, converting a degraded service into an unavailable one.
*Cause.* The liveness path competes for the same permits as the saturated path.
*Fix.* Give the health and admin paths a dedicated partition, and preferably a
dedicated listener. This is the single highest-value bulkhead in most services
and the one most often missing.

**Bulkhead placed on the wrong side of the buffer.**
*Symptom.* Permit gauge is well below maximum, yet the process runs out of memory
or file descriptors.
*Cause.* The guarded call submits to a client library holding its own unbounded
internal queue. The bulkhead bounds submissions in flight, not resources held.
*Fix.* Bound the library's internal queue too, or move the bulkhead to the
resource being exhausted. Verify by measuring the actual resource, not the
proxy.

**Uniform partition sizes on skewed traffic.**
*Symptom.* Aggregate resource utilisation sits near 30 percent while rejections
run at 5 percent.
*Cause.* Equal budgets against unequal demand. The busiest partition starves
while the quiet ones idle.
*Fix.* Size by measured per-partition demand, review on a schedule, and accept
that the sum of budgets will exceed nominal capacity for partitions that never
peak together. Say out loud which partitions are assumed not to peak together,
because that assumption is the residual shared fate.

**Isolation claimed but never tested.**
*Symptom.* The first real degradation produces a full outage anyway, and the
post-incident review finds the bulkhead was configured on a code path that was
refactored around six months earlier.
*Cause.* No fault injection exercised the partition boundary.
*Fix.* Run a regular exercise that makes one dependency artificially slow in a
production-like environment and asserts that the neighbouring partition's success
rate is unchanged. A bulkhead nobody has watched hold is a claim, not a control.

## 12. Trade-off matrix

Compared against named alternatives that address overlapping forces.

| Force | Bulkhead | Circuit Breaker | Timeout alone | Rate Limiter | Load Shedding | Queue-Based Load Levelling |
|---|---|---|---|---|---|---|
| Contains a slow, non-failing dependency | yes, its primary case | no, error-keyed breakers do not trip on slowness | partly, caps each call but not aggregate concurrency | partly, caps arrival not occupancy | yes, but service-wide not per dependency | yes, by decoupling arrival from service |
| Contains a fast-failing dependency | little value | yes, its primary case | yes | no | no | no |
| Blast radius containment | per partition | per dependency, all-or-nothing | none | per key | whole service | per queue |
| Utilisation cost | high, capacity reserved | low | none | low | none until shedding | moderate, queue storage |
| Latency added in the healthy path | 0 to 9 ms by mechanism | near zero | none | near zero | none | high, work is deferred |
| Preserves work under overload | no, sheds it | no, fails it | no | no, rejects it | no, sheds it | yes, defers it |
| Configuration burden | one budget per partition | thresholds plus half-open policy | one duration per call | one rate per key | one global policy | queue size plus workers |
| Fails safe when misconfigured | no, low budget causes outage | no, low threshold causes outage | yes, generous timeout is inert | no | yes | partly, deep queue hides overload |
| Protects against memory or crash faults | only the pod variant | no | no | no | no | partly, by process separation |
| Requires the dependency to cooperate | no | no | no | no | no | no |

The honest reading. Bulkhead and Circuit Breaker are complements, not
alternatives, and a system with one and not the other has a named gap. Bulkhead
without Timeout is broken by construction. Rate Limiter caps how fast work
arrives, Bulkhead caps how much work is resident, and a system under a latency
shock needs the second because the first stays satisfied while occupancy climbs.

## 13. Related and incompatible patterns

**Timeout.** A hard prerequisite, not merely a companion. Permits are returned on
completion, so without a bound on completion the bulkhead leaks permits until it
is permanently full. Any bulkhead deployed without a timeout on the guarded call
should be treated as a defect.

**Circuit Breaker.** Deployed together, in a fixed order. The bulkhead limits
occupancy, and the breaker stops calling once failure is established. Resilience4j
composes them as separate decorators around the same call. The distinction to
hold onto is that a breaker keyed on error rate is blind to a dependency that is
slow but correct, which is the exact case that exhausts pools.

**Retry.** Actively hostile to a bulkhead when unbounded. A rejection is a
saturation signal, and retrying it immediately raises arrival rate at the moment
capacity fell. Compose only with a retry budget, backoff, and jitter, and prefer
treating bulkhead rejection as terminal at the innermost layer.

**Rate Limiter.** Adjacent but not substitutable. Rate limits arrival, bulkhead
limits occupancy. Under a latency shock arrival is constant and occupancy grows,
so the rate limiter never fires and the bulkhead does. Under a traffic spike with
stable latency the reverse holds. Systems facing both need both.

**Load Shedding.** The service-wide sibling. Shedding drops work based on global
pressure, a bulkhead drops work based on per-partition pressure. Shedding is the
outer layer and bulkheads the inner. A service with only shedding drops requests
uniformly, including the ones for the healthy dependency.

**Queue-Based Load Levelling.** An alternative when the work can be deferred
durably. Where the bulkhead rejects, the queue defers. Choose the queue when
losing the work is worse than delaying it, and the bulkhead when a stale result
is worthless.

**Backpressure.** The same intent expressed as a protocol rather than a guard.
Where backpressure is available across the whole path, as in a reactive stream or
HTTP/2 flow control, it subsumes much of the bulkhead's job by slowing the
producer instead of rejecting at the consumer. A bulkhead is what you build when
the producer cannot be slowed.

**Fallback.** The natural rejection policy. A bulkhead that rejects into an
exception surfaces the failure to the user. One that rejects into a cached or
degraded response converts it into partial availability, which is the outcome the
pattern is deployed for.

**Sharding.** Overlaps only when shards fail independently. Sharding for
throughput with a shared coordinator does not partition failure, so it is not a
bulkhead. Cell-based architecture is sharding where the shards are complete and
independently failing, which is a bulkhead.

No pattern in this catalog is strictly incompatible with Bulkhead. The nearest
thing to a conflict is unbounded Retry, which does not forbid the bulkhead but
reliably defeats it.

## 14. Refactoring path in and out

### Introducing a bulkhead

1. **Measure occupancy before partitioning anything.** Instrument the shared
   resource with a gauge of in-use units and a histogram of hold time, tagged by
   the candidate partition key. Without this the permit count is a guess.
2. **Confirm the resource is genuinely shared and genuinely finite.** Chase it to
   the actual pool object or kernel limit. Many suspected shared resources turn
   out to be per-request allocations.
3. **Set the timeout first, and deploy that alone.** A correct timeout on the
   guarded call is most of the benefit and carries none of the utilisation cost.
   Deploy and observe for a full traffic cycle before adding partitions. In many
   incidents the timeout alone stops the spread, and the bulkhead turns out to be
   unnecessary.
4. **Choose the partition key from the measured correlation**, not from the
   organisation chart. Partition along the axis where hold time actually
   correlates.
5. **Compute the budget rather than choosing it.** Arrival rate at p99 multiplied
   by hold time at p99, plus margin. Write the computation down next to the
   configuration so the next person can recheck it.
6. **Deploy in observe-only mode.** Count what would have been rejected without
   rejecting. Run for a full weekly cycle. If the shadow rejection count is
   non-zero under healthy conditions, the budget is wrong.
7. **Enable rejection with a fallback**, never with a bare exception, unless the
   caller genuinely has no degraded mode.
8. **Add the fault injection test.** Make the dependency artificially slow and
   assert the neighbouring partition's success rate does not move. Until this
   passes, the isolation is unverified.
9. **Extract the health and admin path into its own partition**, if it is not
   already separate. Do this even if nothing else is partitioned.

Where a named refactoring applies, this is Introduce Parameter Object applied to
the resource budget, followed by Extract Class for the guard, and the cross
reference is to the refactoring family entries for both.

### Removing a bulkhead

1. **Establish why it is no longer earning its place.** The valid reasons are
   that the dependency was removed, the call became synchronous and in-process,
   the protection moved to the platform layer such as a service mesh, or
   measurement shows the partition never approaches saturation and the resource
   is no longer contended.
2. **Raise the budget to effectively unbounded first**, and observe. This is the
   reversible step. If nothing degrades over a full traffic cycle including a
   peak, the bulkhead was not doing load-bearing work.
3. **Verify the timeout survives the removal.** The most common damage from
   removing a bulkhead is silently removing the timeout that lived on the same
   decorator.
4. **Remove the guard, keep the metrics.** The occupancy gauge remains useful and
   costs almost nothing. Losing it means the next person cannot tell whether
   reintroducing the bulkhead is warranted.
5. **Record the removal and its evidence.** A bulkhead removed without a written
   reason gets reintroduced during the next incident by somebody who cannot tell
   whether it was removed deliberately.

## 15. Testing and verification

This dimension is practice rather than sourced fact.

**What becomes easy to test.** The guard itself is a pure concurrency object with
no IO. Its contract is a small set of assertions. Never admit more than the
budget. Reject when the budget and queue are full. Release on both the success
and the failure path. Honour the wait bound. All three code samples in this entry
assert the first of those with a peak-concurrency counter, which is the single
most valuable unit assertion because it is the property everything else rests on.

**What becomes harder to test.** Whole-system behaviour under degradation is now
a system property rather than a unit property. Verifying it needs a slow
dependency, and a slow dependency is harder to fake convincingly than a broken
one. A mock that returns an error tests the circuit breaker path, not the
bulkhead path.

**Techniques that apply.**

- **A deterministic concurrency probe.** Wrap the work in a counter that
  increments on entry and decrements on exit, and assert the observed maximum
  never exceeds the budget across a burst larger than the budget. This catches
  the class of bug present in the first draft of the TypeScript sample in this
  entry, where an already-resolved promise let every waiter increment after the
  admission check.
- **A black-hole test double.** An endpoint that accepts the connection and never
  responds. This is the only double that reproduces the slow-not-broken case, and
  it is the one that catches a missing timeout.
- **A latency-injecting proxy.** Toxiproxy or an equivalent placed between the
  service and one dependency, adding a fixed delay. Assert that the neighbouring
  partition's success rate and latency distribution are statistically unchanged.
  This is the acceptance test for the pattern.
- **A permit-leak test.** Run a burst where every call times out, then assert
  that the permit gauge returns to zero. A leak here is invisible in normal
  testing and fatal in production.
- **Deadline propagation assertion.** Submit work with a deadline that has
  already passed and assert it is discarded at dequeue rather than executed.
- **Property-based testing of the guard.** Over random interleavings of acquire
  and release, the invariant that in-flight stays between zero and the budget
  must hold. This is the right shape for the guard because the state space of
  interleavings is exactly what a hand-written example misses. Cross reference
  the property-first testing discipline in the repository's testing family.
- **Fake time for the wait bound.** Assert the wait duration is honoured without
  a real sleep, so the test is deterministic and fast.

**What not to test.** Do not assert on exact rejection counts under a real
concurrency burst. Scheduling makes those numbers vary run to run. Assert on
invariants, peak occupancy and permit balance, not on totals.

## 16. Observability signals

This dimension is practice rather than sourced fact.

Every signal below carries the partition key as a label. A bulkhead metric
without the partition dimension is close to useless, because the entire purpose
of the pattern is knowing which partition is sick.

**Metrics to emit.**

| Signal | Type | What it answers |
|---|---|---|
| `bulkhead_permits_in_use{partition}` | gauge | current occupancy |
| `bulkhead_permits_max{partition}` | gauge | the budget, so utilisation is computable |
| `bulkhead_queue_depth{partition}` | gauge | how much waiting is happening |
| `bulkhead_rejected_total{partition,reason}` | counter | saturation, split by full versus wait-timeout |
| `bulkhead_wait_duration{partition}` | histogram | latency added by admission, not by the dependency |
| `bulkhead_hold_duration{partition}` | histogram | how long a permit is held, the Little's Law input |
| `bulkhead_permits_available{partition}` | gauge | headroom, easier to alarm on than occupancy |

**What healthy looks like.** Occupancy oscillating well below the budget with a
clear diurnal shape. Queue depth at or near zero most of the time. Rejection
counter flat at zero. Hold duration distribution matching the dependency's own
latency distribution, and moving together with it.

**What failing looks like, and the sequence matters for diagnosis.** Hold
duration rises first, while occupancy is still fine. Then occupancy rises to the
budget and pins there. Then queue depth fills. Then rejections begin. The gap
between the hold duration rising and the rejections starting is the warning
window, and it is the reason to alert on hold duration and occupancy rather than
only on rejections. By the time rejections fire, users are already affected.

**What a distinct pathology looks like.** Occupancy pinned at maximum with hold
duration flat and the dependency healthy. That is a permit leak, not saturation,
and the fix is different. Distinguishing the two on a dashboard is the main
argument for emitting hold duration at all.

**Tracing.** Add a span around the admission wait, separate from the span around
the dependency call. Without that separation the time spent waiting for a permit
is attributed to the dependency, and the trace tells the operator to go and fix a
service that was never slow. Tag the span with the partition key and the
admission outcome.

**Logging.** Log rejections at warning level, with the partition key, the current
budget, and the wait duration that elapsed. Do not log admissions, they are the
common path and the volume is not worth carrying. Sample rejection logs if the
rejection rate can go high, since a saturating bulkhead can produce enough
rejections to saturate the logging pipeline, which is a bulkhead problem
recursing into the observability stack.

**Dashboard layout.** One row per partition, showing occupancy against budget as
a single utilisation ratio. Reading five separate gauges during an incident is
too slow. A ratio makes the sick partition visible at a glance.

## 17. Security and privacy implications

This dimension is analytical rather than sourced, except where a citation is
given.

**What the pattern closes.**

- **Noisy-neighbour and denial-of-service amplification.** A bulkhead keyed by
  tenant or by caller identity puts a hard limit on how much of a shared resource
  any single principal can occupy. This turns an availability attack from a
  service-wide outage into a self-inflicted degradation confined to the
  attacker's own partition. This is the availability leg of the security triad,
  and Microsoft's Well-Architected mapping for the pattern makes the segmentation
  claim explicitly, that segmentation between components helps constrain security
  incidents to the compromised bulkhead ([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
  verified 2026-08-02).
- **Lateral movement, at the process and pod variant only.** Separate processes
  with separate credentials mean a compromise of one partition does not
  automatically grant the credentials of another. The in-process variants provide
  none of this. A semaphore does not stop code in the same address space from
  reading anything in that address space, and claiming otherwise is a
  misunderstanding worth naming plainly.
- **Blast radius for a compromised dependency.** If a downstream is compromised
  and starts returning hostile responses, a bulkhead bounds the number of
  concurrent in-process handlers exposed to those responses at any instant. This
  is a small effect and should not be oversold.

**What the pattern opens.**

- **A cheaper denial-of-service target.** A bulkhead is a documented, precise
  capacity limit. An attacker who learns the budget knows exactly how much
  concurrent load is needed to saturate a partition, and that number is usually
  far below what would be needed to saturate the service as a whole. Publishing
  bulkhead configuration in a public repository or exposing it on an unprotected
  metrics endpoint hands an attacker the target. Treat the budget as capacity
  information and protect the metrics endpoint accordingly.
- **A side channel through rejection timing.** Rejections are fast and successes
  are slow. An unauthenticated caller can probe which partition is saturated and,
  by extension, infer which downstream dependency is degraded and roughly how
  much traffic the service is carrying. This is low severity in most systems and
  real in a multi-tenant one where partition identity maps to a customer.
- **Partition key as an information leak.** If the key is a tenant identifier and
  it appears in error responses or in trace headers returned to the client, the
  service is disclosing tenancy structure. Keep the key in server-side telemetry,
  out of the client-visible error body.
- **Amplification through unequal budgets.** If a low-priority partition is
  generously sized and a high-priority one is not, an attacker who can steer
  traffic into the low-priority partition can consume shared underlying capacity
  such as CPU or connections at the node level while every per-partition metric
  reads healthy.

**Where it is silent.** The pattern has no bearing on confidentiality of data at
rest or in transit, no bearing on authentication or authorisation correctness,
and no bearing on input validation. A bulkhead around a call that passes
unvalidated input to a downstream service isolates the resource consumption and
does nothing about the injection. Claiming security benefit beyond availability
and segmentation would be inventing a concern.

## Code

Three implementations, each demonstrating a different mechanism. All three were
run on 2026-08-02 and their output is shown. Java is the language the pattern's
canonical libraries are written in, and a `ThreadPoolExecutor` sample was drafted
for it, but no Java runtime is installed on the authoring machine, so it is
omitted rather than shipped unverified. The Python sample below demonstrates the
same thread pool mechanism.

### Go, semaphore isolation with a bounded wait

Semaphore isolation on a runtime where the caller's unit of concurrency is cheap.
The permit is a slot in a buffered channel, and the wait is bounded by a timer so
a saturated partition fails fast rather than queueing without limit.

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

var ErrBulkheadFull = errors.New("bulkhead full")

// Semaphore bulkhead. Caps concurrency on the caller's own goroutine.
type Bulkhead struct {
	slots    chan struct{}
	maxWait  time.Duration
	name     string
	rejected atomic.Int64
	inFlight atomic.Int64
	peak     atomic.Int64
}

func New(name string, maxConcurrent int, maxWait time.Duration) *Bulkhead {
	return &Bulkhead{
		slots:   make(chan struct{}, maxConcurrent),
		maxWait: maxWait,
		name:    name,
	}
}

func (b *Bulkhead) Do(ctx context.Context, work func(context.Context) error) error {
	timer := time.NewTimer(b.maxWait)
	defer timer.Stop()

	select {
	case b.slots <- struct{}{}:
	case <-timer.C:
		b.rejected.Add(1)
		return ErrBulkheadFull
	case <-ctx.Done():
		return ctx.Err()
	}

	b.enter()
	defer func() {
		b.inFlight.Add(-1)
		<-b.slots
	}()
	return work(ctx)
}

// Records the high-water mark without a mutex, retrying on a lost race.
func (b *Bulkhead) enter() {
	now := b.inFlight.Add(1)
	for {
		old := b.peak.Load()
		if now <= old || b.peak.CompareAndSwap(old, now) {
			return
		}
	}
}

func (b *Bulkhead) Stats() (peak, rejected int64) {
	return b.peak.Load(), b.rejected.Load()
}

func main() {
	slow := New("recommendations", 4, 20*time.Millisecond)
	var wg sync.WaitGroup
	var served atomic.Int64

	for i := 0; i < 40; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			err := slow.Do(context.Background(), func(context.Context) error {
				time.Sleep(60 * time.Millisecond)
				return nil
			})
			if err == nil {
				served.Add(1)
			}
		}()
	}
	wg.Wait()

	peak, rejected := slow.Stats()
	fmt.Printf("peak=%d served=%d rejected=%d\n", peak, served.Load(), rejected)
	if peak > 4 {
		panic("bulkhead breached")
	}
}
```

Run with `go run bh.go`, output `peak=4 served=4 rejected=36`, and clean under
`go vet`. Forty callers against four permits and a 20 millisecond wait bound.
Four are served, the rest fail fast rather than piling up. That rejection ratio
is the pattern working, not the pattern failing.

### TypeScript, semaphore isolation on a single-threaded event loop

The event loop has no second thread to hand work to, so semaphore isolation is
the only in-process mechanism available. The subtle part is that admission must
increment the counter synchronously. An earlier draft incremented after
`await this.acquire()`, and because an already-resolved promise defers to the
microtask queue, all twenty callers passed the capacity check before any of them
incremented. Peak occupancy was 20 against a budget of 3. The guard compiled,
passed a casual read, and provided no isolation at all.

```typescript
export class BulkheadFullError extends Error {
  constructor(name: string) {
    super(`bulkhead ${name} full`);
    this.name = "BulkheadFullError";
  }
}

type Waiter = {
  resolve: () => void;
  reject: (e: Error) => void;
  timer: ReturnType<typeof setTimeout>;
};

export class Bulkhead {
  private inFlight = 0;
  private queue: Waiter[] = [];
  peak = 0;
  rejected = 0;

  constructor(
    private readonly name: string,
    private readonly maxConcurrent: number,
    private readonly maxWaitMs: number,
    private readonly maxQueue: number,
  ) {}

  async run<T>(work: () => Promise<T>): Promise<T> {
    await this.acquire();
    try {
      return await work();
    } finally {
      this.inFlight--;
      this.release();
    }
  }

  private acquire(): Promise<void> {
    if (this.inFlight < this.maxConcurrent) {
      this.admit();
      return Promise.resolve();
    }
    if (this.queue.length >= this.maxQueue) {
      this.rejected++;
      return Promise.reject(new BulkheadFullError(this.name));
    }
    return new Promise<void>((resolve, reject) => {
      const w: Waiter = {
        resolve: () => {
          this.admit();
          resolve();
        },
        reject,
        timer: setTimeout(() => {
          this.queue = this.queue.filter((q) => q !== w);
          this.rejected++;
          reject(new BulkheadFullError(this.name));
        }, this.maxWaitMs),
      };
      this.queue.push(w);
    });
  }

  // Admission must be synchronous. Deferring it past an await lets every
  // caller pass the capacity check before any of them increments.
  private admit(): void {
    this.inFlight++;
    if (this.inFlight > this.peak) this.peak = this.inFlight;
  }

  private release(): void {
    const w = this.queue.shift();
    if (!w) return;
    clearTimeout(w.timer);
    w.resolve();
  }
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function demo(): Promise<void> {
  const bh = new Bulkhead("pricing", 3, 30, 5);
  const results = await Promise.allSettled(
    Array.from({ length: 20 }, () =>
      bh.run(async () => {
        await sleep(50);
        return 1;
      }),
    ),
  );
  const ok = results.filter((r) => r.status === "fulfilled").length;
  console.log(`peak=${bh.peak} ok=${ok} rejected=${bh.rejected}`);
  if (bh.peak > 3) throw new Error("bulkhead breached");
}

demo();
```

Compiled with `tsc --strict --target es2020 --module commonjs` and run on Node
23. Output `peak=3 ok=3 rejected=17`.

### Python, thread pool isolation with a bounded queue

Dedicated worker threads plus a bounded queue, which is the mechanism Resilience4j
calls `ThreadPoolBulkhead`. The caller's thread is never the one that blocks on
the dependency, which is what makes an enforceable client-side timeout possible.

```python
"""Thread pool bulkhead. Dedicated workers plus a bounded queue per dependency."""
import queue
import threading
import time
from concurrent.futures import Future
from dataclasses import dataclass, field


class BulkheadFull(Exception):
    pass


@dataclass
class ThreadPoolBulkhead:
    name: str
    workers: int
    queue_capacity: int
    _q: "queue.Queue" = field(init=False)
    _threads: list = field(default_factory=list, init=False)
    rejected: int = field(default=0, init=False)
    peak: int = field(default=0, init=False)
    _active: int = field(default=0, init=False)
    _guard: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self):
        self._q = queue.Queue(maxsize=self.queue_capacity)
        for i in range(self.workers):
            t = threading.Thread(
                target=self._loop, name=f"bh-{self.name}-{i}", daemon=True
            )
            t.start()
            self._threads.append(t)

    def submit(self, fn, *args):
        fut = Future()
        try:
            self._q.put_nowait((fut, fn, args))
        except queue.Full:
            self.rejected += 1
            fut.set_exception(BulkheadFull(f"bulkhead {self.name} full"))
        return fut

    def _loop(self):
        while True:
            fut, fn, args = self._q.get()
            if not fut.set_running_or_notify_cancel():
                continue
            self._enter()
            try:
                fut.set_result(fn(*args))
            except Exception as exc:
                fut.set_exception(exc)
            finally:
                self._leave()

    def _enter(self):
        with self._guard:
            self._active += 1
            self.peak = max(self.peak, self._active)

    def _leave(self):
        with self._guard:
            self._active -= 1


if __name__ == "__main__":
    bh = ThreadPoolBulkhead("search", workers=4, queue_capacity=8)
    futures = [bh.submit(time.sleep, 0.12) for _ in range(40)]
    ok = 0
    for f in futures:
        try:
            f.result(timeout=5)
            ok += 1
        except BulkheadFull:
            pass
    print(f"peak={bh.peak} ok={ok} rejected={bh.rejected}")
    assert bh.peak <= 4, "bulkhead breached"
```

Run with `python3 bh.py`, output `peak=4 ok=8 rejected=32`. Note the shape of the
result compared with the Go sample. The queue admits eight callers beyond the
workers, then the remaining thirty-two are rejected at submission rather than
waiting. Queue capacity converts a rejection into a delay for exactly eight
callers, and no more, which is the property a bounded queue exists to provide.

### Kubernetes, pod-level isolation

The declarative form of the process variant. Requests drive scheduling, limits
drive runtime enforcement, and the two together define the partition.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: search-worker
spec:
  containers:
    - name: search
      image: example/search:1.0
      resources:
        requests:
          memory: "256Mi"
          cpu: "500m"
        limits:
          memory: "512Mi"
          cpu: "1"
```

The asymmetry described in dimension 8 applies here. Exceeding the CPU limit
throttles the container, exceeding the memory limit risks an out-of-memory kill
that arrives only when the kernel detects pressure ([Kubernetes documentation](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/),
verified 2026-08-02). Setting requests well below limits gives higher packing
density and weaker isolation, because the node can become oversubscribed. Setting
requests equal to limits gives the strongest isolation and the lowest packing
density, which is the same utilisation trade this pattern makes everywhere.

## 18. References

- Michael T. Nygard, *Release It! Design and Deploy Production-Ready Software*,
  Pragmatic Bookshelf, 1st edition 2007, stability patterns. The origin of the
  pattern in software engineering. Publisher page for the second edition, 2018,
  [pragprog.com/titles/mnee2/release-it-second-edition](https://pragprog.com/titles/mnee2/release-it-second-edition/),
  verified 2026-08-02. Page numbers are not cited because the physical text was
  not consulted for this entry.
- Bulkhead pattern, Wikipedia,
  [en.wikipedia.org/wiki/Bulkhead_pattern](https://en.wikipedia.org/wiki/Bulkhead_pattern),
  verified 2026-08-02. Attribution of the pattern to Nygard 2007, the naval
  metaphor, and the underutilisation caveat.
- Bulkhead pattern, Azure Architecture Center, Microsoft,
  [learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
  page dated 2026-03-19, verified 2026-08-02. Cell-based architecture as an
  alias, the spreading resource exhaustion, the connection pool and per-client
  diagrams, the when-not-to-use list, the Kubernetes example, and the
  Well-Architected pillar mapping.
- Hystrix, How it Works, Netflix,
  [github.com/Netflix/Hystrix/wiki/How-it-Works](https://github.com/Netflix/Hystrix/wiki/How-it-Works),
  verified 2026-08-02. Thread pool versus semaphore isolation, the semaphore's
  inability to enforce a timeout, the 3 millisecond p90 and 9 millisecond p99
  overhead measurements at 60 requests per second, and the 10 billion executions
  per day with 40 or more pools per instance figure.
- Netflix Hystrix README, [github.com/Netflix/Hystrix](https://github.com/Netflix/Hystrix),
  verified 2026-08-02. Maintenance mode status at version 1.5.18 and the
  recommendation of Resilience4j for new projects.
- Resilience4j Bulkhead documentation,
  [resilience4j.readme.io/docs/bulkhead](https://resilience4j.readme.io/docs/bulkhead),
  verified 2026-08-02. The `SemaphoreBulkhead` and `ThreadPoolBulkhead`
  implementations, and the documented defaults of `maxConcurrentCalls` 25,
  `maxWaitDuration` 0ms, `maxThreadPoolSize` available processors,
  `coreThreadPoolSize` available processors minus one, `queueCapacity` 100, and
  `keepAliveDuration` 20ms.
- Managing Resources for Containers, Kubernetes documentation,
  [kubernetes.io/docs/concepts/configuration/manage-resources-containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/),
  verified 2026-08-02. Requests driving scheduling, limits enforced by the
  kubelet, CPU throttling as a hard kernel-enforced limit, and memory limits
  enforced by out-of-memory kill only under detected memory pressure.
- Circuit breaking, Envoy proxy documentation,
  [envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking),
  verified 2026-08-02. Per-cluster and per-priority limits on connections,
  pending requests, requests, retries, and connection pools, and the statement
  that enforcement happens at the network level rather than per application.
- Polly documentation, [pollydocs.org](https://www.pollydocs.org/), verified
  2026-08-02. The .NET resilience library named by Microsoft as a consumer
  bulkhead framework.
