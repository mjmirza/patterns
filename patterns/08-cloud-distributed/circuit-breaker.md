---
name: Circuit Breaker
slug: circuit-breaker
family: 08-cloud-distributed
category: Stability
aliases: [Breaker, Fail Fast Proxy, Trip Switch]
first_described: "Michael T. Nygard 2007"
maturity: canonical
related: [retry, bulkhead, timeout, fallback, health-endpoint-monitoring, rate-limiter, hedging]
incompatible_with: []
verified: 2026-08-02
---

# Circuit Breaker

## 1. Name, aliases, and lineage

The canonical name is Circuit Breaker. Michael T. Nygard named and popularised it
as one of the stability patterns in *Release It!*, first published by The
Pragmatic Programmers in 2007 and revised as *Release It! Second Edition. Design
and Deploy Production-Ready Software*, The Pragmatic Programmers, 2018, ISBN
9781680502398, Part I "Create Stability", chapter "Stability Patterns", section
"Circuit Breaker"
([publisher listing](https://pragprog.com/titles/mnee2/release-it-second-edition/),
verified 2026-08-02). Nygard pairs each stability pattern with a matching
antipattern, and Circuit Breaker is the answer to the chain reaction in which one
integration point that fails slowly, rather than cleanly, drags down every caller
that depends on it.

The metaphor is borrowed from electrical engineering. A domestic breaker trips
when current passes a rated threshold, and a human resets it once the fault is
cleared. The software version trips itself and, unlike the electrical one,
resets itself on a timer.

The pattern entered mainstream cloud architecture vocabulary through the
Microsoft Azure Architecture Center, whose Circuit Breaker page gives the
three-state proxy formulation that most libraries now implement
([Azure Architecture Center, Circuit Breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
verified 2026-08-02).

Aliases in real use are few and mostly informal. Teams say **breaker** in
conversation. **Fail fast proxy** appears in code review comments because the
behaviour in the tripped state is exactly the Fail Fast pattern, which Nygard
lists separately in the same chapter. **Trip switch** turns up in British English
codebases. One naming collision matters more than any alias, and it is a real
source of confusion.

Envoy uses the term **circuit breaking** for something that is not this pattern.
Envoy's circuit breaking is a set of concurrency ceilings, maximum connections,
maximum pending requests, maximum requests, maximum active retries, and maximum
concurrent connection pools, tracked per upstream cluster and per priority. The
documentation describes it as enforcing limits at the network level rather than
in each application, and the mechanism is a counter-based limiter, not a state
machine
([Envoy, Circuit breaking](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking),
verified 2026-08-02). What Envoy calls **outlier detection** is the feature that
behaves like the pattern in this entry. It ejects a host from the load balancing
set after consecutive 5xx responses or a poor success rate, holds it out for
`base_ejection_time` multiplied by the number of consecutive ejections, and
returns it to the pool when that window expires
([Envoy, Outlier detection](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier),
verified 2026-08-02). A reader who assumes Envoy circuit breaking is a state
machine will configure the wrong knob and wonder why nothing ever trips.

## 2. Problem and context

A service calls a remote dependency. The dependency degrades in the worst
possible way, which is not by refusing connections but by accepting them and
answering slowly or not at all.

The failure shape is specific and it is what makes this pattern necessary. If a
dependency returns connection refused in one millisecond, the caller fails fast
by accident and nothing catastrophic follows. The dangerous case is a dependency
that holds the socket open. Every caller thread now blocks for the full timeout.
Azure's page describes the mechanism plainly. A timeout strategy can block
concurrent requests to the same operation until the timeout expires, those
blocked requests hold memory, threads and database connections, and exhausting
those resources can fail unrelated parts of the system that share the same pool
([Azure Architecture Center, Circuit Breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
verified 2026-08-02).

The situation reads like this in a real incident. One downstream service starts
taking eight seconds instead of eighty milliseconds. The calling service has a
thread pool of two hundred. Within a minute every thread is parked waiting on
that one dependency. Health checks on the calling service now time out, because
the health endpoint cannot get a thread. The load balancer marks the caller
unhealthy and removes it. Its traffic shifts to the remaining instances, which
saturate faster. A dependency that was merely slow has taken down a service that
did not depend on it, because both shared a connection pool. That is failure
propagating along a resource boundary, and the blast radius is set by resource
sharing, not by the call graph.

Two secondary problems ride along. First, every retry aimed at a saturated
dependency adds load to something already failing, which makes recovery slower.
Second, the caller keeps paying full latency for calls that were never going to
succeed, so its own latency percentiles collapse even for requests that could
have been served from cache or degraded.

The context in which the pattern earns its place has four parts.

- The call crosses a process or network boundary, so it can fail in ways local
  calls cannot.
- Failures are correlated rather than independent. When one call to the
  dependency fails, the next is more likely to fail than a random call would be.
  Without correlation there is nothing to predict and the breaker is noise.
- The caller has a meaningful action available when the call is skipped, whether
  that is a cached value, a degraded response, a queued write or a clean error.
- The dependency benefits from being left alone. Shedding load during recovery
  helps it, which is the difference between this and a pure client-side
  optimisation.

Outside that context the pattern adds latency variance and operational surface
for nothing. Dimension 4 lists the specific cases.

## 3. Forces

This dimension mixes sourced behaviour with engineering judgement about which
pressure dominates. The weightings below are judgement, drawn from operating
breakers in production, and a different system can reasonably weigh them
differently.

- **Latency under failure.** Strongly favoured. A tripped breaker converts a
  multi-second timeout into a sub-millisecond rejection. This is the single
  largest benefit and the reason the pattern exists.
- **Latency under health.** Slightly sacrificed. Every call now passes through a
  guard that reads shared state. On a well-implemented breaker this is a few
  atomic operations, which is irrelevant against network latency, but the guard
  must not take a coarse lock on the hot path or it becomes the bottleneck it
  was added to prevent. Azure lists concurrency explicitly, saying the
  implementation should not block concurrent requests or add excessive overhead
  per call
  ([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
  verified 2026-08-02).
- **Correctness of individual requests.** Sacrificed, deliberately. A tripped
  breaker rejects requests that would have succeeded. That is not a bug, it is
  the trade. The breaker accepts a false positive rate in exchange for bounded
  resource use, and tuning is the act of choosing that rate.
- **Availability of the caller.** Favoured. The caller stays responsive even
  when the dependency is gone, which keeps its own callers alive.
- **Availability of the dependency.** Favoured during recovery. Shedding load
  gives a restarting service room to warm caches, rebuild connection pools and
  replay a write-ahead log.
- **Consistency.** Sacrificed where the protected call is a write. A rejected
  write is a write that did not happen, and the caller must decide between
  losing it, queueing it or failing the whole operation. A breaker in front of a
  non-idempotent write is a correctness decision, not a resilience decision.
- **Operability.** Mixed. The breaker gives a clean binary signal about
  dependency health, which is excellent on a dashboard. It also introduces a
  hidden state machine whose current state is invisible in the code, so an
  operator without instrumentation cannot tell whether an error came from the
  dependency or from the guard. Dimension 16 exists because of this.
- **Cognitive load.** Sacrificed. A reader tracing a request must now account
  for a rejection path that no line of business logic mentions, and for a state
  that changed because of traffic minutes ago in a different thread.
- **Cost.** Favoured in the failure case. Rejected calls consume no downstream
  compute and no egress. On a metered dependency this is directly financial.
- **Team topology.** Favoured. The breaker is the contractual boundary between
  the team that owns the caller and the team that owns the dependency. It gives
  the caller a way to survive an SLO breach it does not control.

The pattern gives up per-request success in return for system-level survival.
Any description that does not name that sacrifice is describing something else.

## 4. Applicability and non-applicability

Reach for Circuit Breaker when these hold.

- The call is remote and the failure mode includes slowness, not only refusal.
- Failures are correlated in time, so recent failures predict imminent ones.
- Call volume is high enough that a failure rate is statistically meaningful.
  Resilience4j defaults `minimumNumberOfCalls` to 100 before it will compute a
  rate at all
  ([Resilience4j CircuitBreaker documentation](https://resilience4j.readme.io/docs/circuitbreaker),
  verified 2026-08-02), and Polly defaults `MinimumThroughput` to 100 executions
  inside the sampling window
  ([Polly circuit breaker documentation](https://www.pollydocs.org/strategies/circuit-breaker.html),
  verified 2026-08-02). Those defaults encode the same judgement.
- A fallback exists, even if the fallback is a fast, honest error.
- The dependency recovers better with less load than with more.

Do NOT reach for Circuit Breaker in the following cases. This
non-applicability list carries more information than the list above, and the
reason attached to each entry is the part that matters.

- **The resource is local and in-process.** An in-memory cache, a data structure,
  a local computation. Azure names this first among the cases where the pattern
  is unsuitable, because the breaker adds overhead with nothing to protect
  against
  ([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
  verified 2026-08-02). There is no queue to exhaust and no remote party to
  protect.
- **Traffic is too low to form a rate.** At three calls per minute, a failure
  rate is meaningless and a threshold breaker will flap on ordinary noise. The
  breaker will spend most of its life in a state chosen by two data points. Use
  a timeout and a retry with backoff instead, and revisit when volume grows.
- **Failures are independent rather than correlated.** If each call has an
  unrelated chance of failing, past failures predict nothing about the next
  call, so opening the circuit rejects good traffic for no gain. Sharded stores
  with independent shard health are the classic trap. Azure raises this under
  resource differentiation, warning that merging error responses from
  independent providers causes the application to try shards that are failing
  and to block shards that would have worked
  ([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
  verified 2026-08-02).
- **The operation is a non-idempotent write with no safe rejection path.** A
  breaker that rejects a payment capture has not protected anything, it has
  moved the failure to a place with worse consequences. Put the write behind a
  durable queue first, then protect the queue drain, not the caller.
- **The call is already asynchronous and message-driven.** Azure lists
  message-driven and event-driven architectures as poor fits, because failed
  messages already route to a dead letter queue and the built-in isolation and
  retry mechanisms usually suffice
  ([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
  verified 2026-08-02). Adding a breaker there produces two competing retry
  policies.
- **Waiting for the reset window is worse than failing slowly.** If the caller
  is a batch job with a six-hour budget and the dependency recovers in ninety
  seconds, a breaker holding open for five minutes costs more than it saves.
  Azure names unacceptable reset delay as a disqualifier.
- **The platform already does it.** If the workload sits behind a service mesh
  with outlier detection, or a global load balancer with health-based routing,
  an application-level breaker duplicates the decision with different data and
  a different clock. The two will disagree during an incident, and reconciling
  two disagreeing breakers under pressure is a bad use of an operator's night.
  Azure lists infrastructure-managed failure recovery as a case where the
  pattern is unsuitable.
- **You are reaching for it to avoid handling exceptions.** Azure states plainly
  that the pattern is not a substitute for exception handling in business logic.
  A breaker converts one failure into a different failure. Something still has
  to decide what the user sees.
- **The dependency degrades gradually rather than binary.** A recommendation
  service that returns worse recommendations under load has no failure to count.
  A breaker keyed on errors will never trip, and one keyed on latency will trip
  on a cold cache. Latency budgets and load shedding fit better.

## 5. Structure

The participants and what each is responsible for.

- **Caller.** The application code performing the operation. It knows nothing
  about the state machine and sees either the operation result or a rejection.
- **Breaker Proxy.** Wraps the protected operation. It decides on each call
  whether to admit or reject, and it observes the outcome. Azure describes the
  breaker as acting as a proxy for operations that might fail, monitoring recent
  failures and deciding whether to allow the operation to proceed or return an
  exception immediately
  ([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
  verified 2026-08-02).
- **State Machine.** Holds the current state, one of Closed, Open or Half-Open,
  and owns the transition rules. Real libraries add administrative states, see
  dimension 8.
- **Outcome Window.** The record of recent results against which the trip
  decision is made. Two shapes dominate. A count-based window over the last N
  calls, or a time-based window over the last N seconds. Resilience4j implements
  both as circular arrays with a subtract-on-evict strategy so a snapshot is
  O(1)
  ([Resilience4j CircuitBreaker documentation](https://resilience4j.readme.io/docs/circuitbreaker),
  verified 2026-08-02).
- **Failure Classifier.** Decides whether a given outcome counts against the
  window. This participant is missing from most diagrams and is where most
  production bugs live. A 404 is a successful call with a negative answer. A
  400 is the caller's fault. A 503 and a timeout are the dependency's fault.
  Only the last group belongs in the window.
- **Reset Timer.** Determines when an open breaker is allowed to probe again.
- **Probe Gate.** In Half-Open, admits a bounded number of trial calls and
  rejects the rest. Resilience4j rejects further calls with
  `CallNotPermittedException` until all permitted calls have completed
  ([Resilience4j CircuitBreaker documentation](https://resilience4j.readme.io/docs/circuitbreaker),
  verified 2026-08-02).
- **Fallback.** Optional. Supplies the degraded answer when the breaker rejects.
  Keeping it outside the breaker rather than inside is the choice discussed in
  dimension 8.
- **Event Sink.** Receives state transition events. Azure notes that raising an
  event on every state change gives monitoring the health of the protected
  component and can alert an administrator when a breaker opens.

The relationships. The Caller holds the Breaker Proxy. The Proxy consults the
State Machine, which consults the Outcome Window and the Reset Timer. Outcomes
flow back through the Failure Classifier into the Window. The Probe Gate is
active only while the State Machine is in Half-Open. Every transition emits to
the Event Sink.

## 6. ASCII structure diagram

```
    +----------+
    |  Caller  |
    +-----+----+
          | call(op)
          v
 +------------------------------------------------------+
 |                   Breaker Proxy                       |
 |                                                       |
 |   +-------------------+       +-------------------+   |
 |   |   State Machine   |<----->|  Outcome Window   |   |
 |   |  Closed / Open /  |       |  count-based or   |   |
 |   |     Half-Open     |       |    time-based     |   |
 |   +---+-----------+---+       +---------^---------+   |
 |       |           |                     |             |
 |       v           v                     |             |
 | +-----------+ +-----------+     +-------+----------+  |
 | |Reset Timer| |Probe Gate |     |Failure Classifier|  |
 | +-----------+ +-----------+     +-------^----------+  |
 |       |                                 |             |
 +-------|---------------------------------|-------------+
         | admit                           | outcome
         v                                 |
   +-----------+   request    +------------+-----------+
   | Fallback  |<--reject--   |  Protected Dependency  |
   +-----------+              +------------------------+
         |                                 ^
         |  degraded answer                | admitted call
         v                                 |
    +----------+                           |
    |  Caller  |---------------------------+
    +----------+

   every transition ---> +-------------+
                         | Event Sink  |  metrics, logs, traces
                         +-------------+
```

## 7. Dynamics

The state machine and its transition rules, stated exactly. Azure's formulation
is the reference and the wording below follows its semantics
([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
verified 2026-08-02).

**Closed.** Requests are routed to the operation. The proxy counts recent
failures. When the number of recent failures passes a configured threshold
inside a configured interval, the breaker moves to Open and starts a timeout
timer. The failure counter in Closed is time based and resets at periodic
intervals, which stops occasional isolated failures from accumulating into a
trip over hours. A success in Closed resets or decrements the failure count
depending on the window shape.

**Open.** Requests fail immediately with an exception. No call reaches the
dependency. When the timeout timer expires the breaker moves to Half-Open.

**Half-Open.** A limited number of requests are allowed through. Azure's rule
is that if these requests succeed the breaker assumes the fault is fixed,
switches to Closed and resets the failure counter, and that if any request fails
the breaker assumes the fault is still present, reverts to Open and restarts the
timeout timer. The success counter records successful invocations and the
breaker closes after a configured number of consecutive successes. A single
failure in Half-Open returns it to Open immediately, and the success counter is
reset the next time Half-Open is entered.

Two properties of this machine deserve naming because they are asymmetric on
purpose.

The path from Closed to Open is *statistical*. It needs a threshold crossed over
a window. The path from Half-Open to Open is *immediate*. One failure is enough.
That asymmetry is correct. In Closed the breaker is deciding whether a healthy
system has become sick, and it should not be twitchy. In Half-Open it is testing
a hypothesis with one probe, and a single counterexample refutes it.

The Half-Open state exists specifically to protect recovery. Azure states that it
helps prevent a recovering service from suddenly being flooded with requests,
because a recovering service may support a limited volume while recovery is in
progress and a flood of work can cause it to time out or fail again. Dimension 11
covers what happens when this protection is implemented badly.

```
             failure count exceeds threshold
             within the rolling interval
   +---------+ --------------------------------> +--------+
   | CLOSED  |                                   |  OPEN  |
   +---------+ <-------------------------------- +--------+
        ^         success count reaches              |
        |         successesToClose                   | reset timer
        |                                            | expires
        |          +-------------+                   |
        +--------- |  HALF-OPEN  | <-----------------+
                   +------+------+
                          |
                          | ANY probe fails
                          |  (immediate, no threshold)
                          v
                      +--------+
                      |  OPEN  |  timer restarted
                      +--------+

  admission per state
    CLOSED     all calls admitted, outcomes recorded
    OPEN       zero calls admitted, immediate rejection
    HALF-OPEN  at most `probeLimit` concurrent calls admitted,
               the rest rejected exactly as in OPEN
```

A single request walking the machine.

```
 t0   caller -> breaker.call(op)
 t0   breaker  state CLOSED, admit
 t0   breaker -> dependency, request sent
 t3s  dependency silent, attempt timeout fires
 t3s  breaker  classify as failure, window failures 5 of 5
 t3s  breaker  TRIP, state OPEN, openedAt = t3s, emit event
 t3s  breaker -> caller, OpenCircuitError

 t4s  caller -> breaker.call(op)
 t4s  breaker  OPEN and 1s elapsed < 30s window, reject
 t4s  breaker -> caller, OpenCircuitError retryAfter 29s  [0.02ms]

 t33s caller -> breaker.call(op)
 t33s breaker  OPEN and 30s elapsed, state HALF-OPEN, probes 0
 t33s breaker  admit probe, probes 1 of 1
 t33s breaker -> dependency, request sent
 t33s concurrent caller -> breaker.call(op) -> reject, probes exhausted
 t33s dependency -> breaker, 200 OK
 t33s breaker  successes 1 of 2, remain HALF-OPEN, probes 0
 t34s next probe succeeds, successes 2 of 2 -> state CLOSED
```

## 8. Implementation variants

**Consecutive failure count.** Trip after N failures in a row. Simple, cheap,
and the shape most hand-rolled breakers take. It handles a hard-down dependency
well and a partially degraded one badly, because one success in every N calls
keeps the counter at zero while 90 percent of traffic fails.

**Failure rate over a sliding window.** Trip when the failure percentage passes
a threshold, given a minimum call volume. Resilience4j defaults
`failureRateThreshold` to 50 percent with `minimumNumberOfCalls` of 100, and
offers count-based and time-based windows
([Resilience4j CircuitBreaker documentation](https://resilience4j.readme.io/docs/circuitbreaker),
verified 2026-08-02). Polly is rate-based, defaulting `FailureRatio` to 0.1 over
a `SamplingDuration` of 30 seconds with `MinimumThroughput` of 100
([Polly circuit breaker documentation](https://www.pollydocs.org/strategies/circuit-breaker.html),
verified 2026-08-02). The minimum volume guard is what stops a rate breaker from
tripping on the first two calls after a deploy.

**Slow call rate.** Trip on latency rather than on errors, treating any call
slower than a threshold as a failure. Resilience4j exposes this as
`slowCallRateThreshold`, defaulting to 100 percent, alongside the error rate.
This variant catches the case that hurts most, a dependency that answers
correctly but too late to be useful, and it trips before thread pools drain.

**Percentile or adaptive thresholds.** Rather than a fixed number, derive the
trip point from observed behaviour. Azure notes that traditional breakers relied
on preconfigured thresholds giving deterministic but sometimes suboptimal
behaviour, and that adaptive techniques can adjust thresholds from real-time
traffic patterns and historical failure rates. Netflix moved in the same
direction, saying it shifted focus toward more adaptive implementations that
react to an application's real time performance rather than pre-configured
settings, for example through adaptive concurrency limits
([Netflix Hystrix README](https://github.com/Netflix/Hystrix), verified
2026-08-02). Judgement, not sourced. Adaptive breakers are harder to reason
about during an incident, because the operator cannot predict the trip point
from configuration alone, so the operability cost is real.

**Health probe instead of a timer.** Rather than moving to Half-Open on a timer
and probing with real traffic, ping a health endpoint and move to Closed when it
answers. Azure lists this under failed operations testing, suggesting the
breaker can periodically ping the remote service or use a special health-check
operation. The gain is that no user request is spent on the probe. The cost is
that a health endpoint can be green while the specific operation is broken, so
the breaker closes into a still-failing dependency.

**Accelerated trip on a signalling error.** Some failures carry enough
information to trip immediately without waiting for a threshold. Azure describes
this as accelerated circuit breaking, giving the example of an overloaded shared
resource whose error response indicates the caller should try again in a few
minutes. An HTTP 429 with a `Retry-After` header is the everyday case, and
honouring that header as the open duration is better than any locally configured
constant.

**Administrative states.** Production libraries add states beyond the canonical
three. Polly adds **Isolated**, a manual hold-open reached through
`CircuitBreakerManualControl`
([Polly circuit breaker documentation](https://www.pollydocs.org/strategies/circuit-breaker.html),
verified 2026-08-02). Resilience4j adds three, `METRICS_ONLY` which permits all
calls while still generating events, `DISABLED` which permits all calls and
emits nothing, and `FORCED_OPEN` which denies all calls and emits nothing
([Resilience4j CircuitBreaker documentation](https://resilience4j.readme.io/docs/circuitbreaker),
verified 2026-08-02). Azure argues for these under manual override, noting that
an administrator needs a way to close a breaker and reset the counter, and to
force one open when a protected operation is known to be unavailable. A breaker
without a manual override will eventually be worked around in a way nobody
documents.

**Fallback inside or outside.** Placing the fallback inside the breaker makes
rejection invisible to the caller, which is convenient and dangerous, because
the caller cannot distinguish a real answer from a degraded one and neither can
its own callers. Placing it outside forces every call site to handle rejection,
which is verbose and honest. Judgement. Put the fallback outside for anything
whose correctness a downstream consumer depends on, and inside only for
presentation concerns where a stale value is acceptable.

**Language-shaped variants.** In Go the breaker is a struct guarding its state
with either a mutex or a capacity-one channel, and the protected call is a
`func() error`, which composes with the `context.Context` deadline already
present in the call. In Rust the same state lives behind a `Mutex` and the API
returns a nested `Result` so that a rejection is a different type from an
operation error, which the type system then forces the caller to distinguish. In
TypeScript and Python the breaker wraps a thunk and the async variant must
decide whether a probe permit is released on the promise or on the awaited
result, which is the difference between counting concurrency correctly and not.
In languages with decorators, Python and Java, the breaker is usually applied as
an annotation, which reads well and hides the state, so the observability work
in dimension 16 becomes the only way to see it.

## 9. Known production uses

**Netflix Hystrix.** The reference implementation for a decade. Its circuit
logic checks whether call volume passes
`circuitBreakerRequestVolumeThreshold`, then whether the error percentage passes
`circuitBreakerErrorThresholdPercentage`, and if both hold the circuit opens.
After `circuitBreakerSleepWindowInMilliseconds` the next single request is let
through as the Half-Open probe, and a failure returns the circuit to Open for
another sleep window. The wiki records the scale, stating that the Netflix API
processes more than 10 billion Hystrix command executions per day using thread
isolation, with each API instance holding more than 40 thread pools of 5 to 20
threads
([Netflix Hystrix, How it Works](https://github.com/Netflix/Hystrix/wiki/How-it-Works),
verified 2026-08-02). Hystrix is now in maintenance mode. The README states that
Hystrix is no longer in active development and is currently in maintenance mode,
that Netflix will no longer actively review issues, merge pull requests or
release new versions, that the final release was 1.5.18, and that Netflix
recommends open and active projects such as Resilience4j instead
([Netflix Hystrix README](https://github.com/Netflix/Hystrix), verified
2026-08-02). The stated reason for the shift is the move toward adaptive
implementations that react to real time performance rather than preconfigured
settings, which is the same argument the Azure page makes about adaptive
thresholds. The practical lesson for a reader in 2026 is that a pattern can be
correct while its most famous implementation is retired, and that choosing
Hystrix today means adopting an unmaintained dependency.

**Microsoft.Extensions.Http.Resilience and Polly in .NET.** Microsoft's standard
resilience handler for `HttpClient` chains five strategies and a circuit breaker
is one of them, with documented defaults of a 10 percent failure ratio, minimum
throughput of 100, a 30 second sampling duration and a 5 second break duration.
The circuit breaker there handles HTTP 500 and above, HTTP 408 and HTTP 429,
plus `HttpRequestException` and `TimeoutRejectedException`
([Microsoft, .NET HTTP resilience documentation](https://learn.microsoft.com/en-us/dotnet/core/resilience/http-resilience),
verified 2026-08-02). This is a breaker shipped as a framework default across
the .NET HTTP client surface, which makes it one of the widest deployments of
the pattern by installation count.

**Envoy and the service meshes built on it.** Envoy's outlier detection ejects
an upstream host from the load balancing set on consecutive 5xx responses, on a
success rate that falls below the cluster statistical baseline, or on a failure
percentage threshold. Ejection lasts `base_ejection_time` multiplied by the
consecutive ejection count, capped by `max_ejection_time`, bounded overall by
`max_ejection_percent`, and a successful active health check unejects the host
and clears the outlier counters
([Envoy, Outlier detection](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier),
verified 2026-08-02). The multiplier on repeat ejections is the exponential
backoff variant of the open duration, applied per host rather than per
dependency.

**Resilience4j in the Spring stack.** The named successor Netflix points to,
implementing the three canonical states plus `METRICS_ONLY`, `DISABLED` and
`FORCED_OPEN`, with count-based and time-based sliding windows and both an error
rate and a slow call rate threshold
([Resilience4j CircuitBreaker documentation](https://resilience4j.readme.io/docs/circuitbreaker),
verified 2026-08-02).

## 10. Consequences

Positive.

- Failure latency collapses from the timeout to near zero, which is the
  mechanism by which the caller's thread pool survives.
- Failure propagation is bounded. A dependency's outage stops at the breaker
  instead of spreading through shared resource pools.
- A recovering dependency receives a controlled trickle rather than the full
  retry storm, which shortens recovery.
- The breaker's state is a high-quality health signal about a dependency,
  measured from the caller's position, which is the position that matters.
- Cost drops during an outage, because rejected calls consume no downstream
  compute.
- Degraded operation becomes an explicit, designed path rather than an
  accidental one.

Negative.

- Requests that would have succeeded are rejected. The false positive rate is a
  design parameter, not a defect, but it is a real loss of availability at the
  request level.
- Failure becomes bimodal and correlated. Instead of scattered errors the
  service produces a clean block of rejections, which is easier to alert on and
  harder to explain to a customer who hit the block.
- A second failure surface exists. The breaker itself can be misconfigured, can
  hold a lock, can leak probe permits, or can be keyed wrongly, and each of
  those is an outage caused by the resilience mechanism.
- State is hidden. Nothing in the call site says which state the breaker is in,
  and two instances of the same service will hold different states.
- Tuning is empirical and perishable. The thresholds that were right at one
  traffic level are wrong at ten times that level, and nothing tells you.
- Every breaker adds a configuration surface that somebody must own, review and
  test. Judgement. On a service with forty dependencies the aggregate
  configuration burden is larger than the code.

## 11. Failure modes and misuse

Symptoms below are drawn from operating this pattern and are engineering
judgement about what a reader observes, with the underlying mechanism sourced
where a source exists.

**Half-open thundering herd.**
*Symptom.* The breaker opens, waits its 30 seconds, then a latency spike appears
on the dependency at exactly the 30 second mark, the breaker opens again, and the
cycle repeats with metronomic regularity. The dependency's own graphs show a
sawtooth of load spikes spaced at exactly the open duration. The dependency never
finishes recovering, and if several caller instances share the same open
duration, the spikes from all of them land in the same instant.
*Cause.* On transition to Half-Open, every request that arrives is admitted as a
probe, rather than a bounded number. All the traffic that queued or was rejected
during the open window arrives at once against a dependency that has only now
come back, with cold caches, empty connection pools and an unwarmed JIT. Azure
names the risk directly, stating that Half-Open helps prevent a recovering
service from suddenly being flooded with requests because it may only support a
limited volume while recovery is in progress, and that a flood of work can cause
it to time out or fail again
([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
verified 2026-08-02). A second cause compounds it. Multiple instances of the same
caller open at the same moment because they saw the same outage, so their reset
timers are synchronised and they probe in lockstep.
*Fix.* Three parts, all needed.
First, cap concurrent probes. Resilience4j permits exactly
`permittedNumberOfCallsInHalfOpenState`, default 10, and rejects further calls
with `CallNotPermittedException` until all permitted calls have completed
([Resilience4j CircuitBreaker documentation](https://resilience4j.readme.io/docs/circuitbreaker),
verified 2026-08-02). Hystrix took the strictest form, letting exactly one
request through
([Netflix Hystrix, How it Works](https://github.com/Netflix/Hystrix/wiki/How-it-Works),
verified 2026-08-02). The permit must be released when the call completes, not
when it is admitted, or the cap counts admissions rather than concurrency and
does nothing.
Second, add jitter to the open duration so instances desynchronise. Without
jitter, N instances that tripped together will probe together forever.
Third, ramp rather than step. On closing, do not go from one probe per window to
full traffic in one transition. Increase the admitted fraction over several
windows, or use a growing open duration on repeat failures, which is exactly what
Envoy does by multiplying `base_ejection_time` by the consecutive ejection count
([Envoy, Outlier detection](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier),
verified 2026-08-02). Azure supports the same idea, suggesting an increasing
timeout timer that starts at a few seconds and grows to minutes if the failure
is not resolved.

**Client errors counted as dependency failures.**
*Symptom.* The breaker opens during a traffic spike from one badly behaved
client. Dependency dashboards are green, its error rate is near zero, yet every
caller is rejecting. Digging into the breaker's own counters shows a failure rate
above threshold made almost entirely of HTTP 400 and 422.
*Cause.* The failure classifier counts every non-2xx as a failure. A validation
error is the dependency working correctly. One client sending malformed requests
at volume can then trip a breaker for every other client.
*Fix.* Classify explicitly, never by status class. Count 5xx, 429, connection
errors and timeouts. Do not count 4xx other than 408 and 429. Microsoft's
standard handler encodes exactly this split, handling HTTP 500 and above, 408 and
429 plus `HttpRequestException` and `TimeoutRejectedException`
([Microsoft, .NET HTTP resilience documentation](https://learn.microsoft.com/en-us/dotnet/core/resilience/http-resilience),
verified 2026-08-02). Azure makes the general argument under types of exceptions,
noting a breaker can examine the exception type and adjust its strategy, for
example requiring more timeout exceptions to trip than unavailability failures.

**One breaker in front of many independent backends.**
*Symptom.* One database shard, one region or one tenant degrades, and the
breaker rejects calls to all of them. Overall availability drops by far more than
the failing partition's share of traffic. Alternatively the reverse, a single bad
shard never produces enough failures against the aggregate to trip anything, so
it degrades silently forever.
*Cause.* Granularity chosen at the client or service level when the failure
domain is finer. Azure calls this resource differentiation, warning against a
single breaker for one type of resource when there are multiple underlying
independent providers, and noting the two symptoms above as the consequence of
merging their error responses
([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
verified 2026-08-02).
*Fix.* Key the breaker on the failure domain. See the granularity discussion in
dimension 12.

**Breaker outside the timeout.**
*Symptom.* The dependency is hard down. The breaker is configured with a 5
second reset. Thread pools still drain and the service still dies, and the
breaker's state graph shows it stuck in Closed the whole time.
*Cause.* There is no attempt timeout inside the breaker, so a call that hangs
never returns an outcome, never records a failure and never trips anything. The
breaker cannot count what it never observes. Azure names this under
inappropriate timeouts on external services, observing that a thread running a
breaker can be blocked for an extended period before the breaker indicates a
failure, and that many application instances can tie up threads in the same way
before all of them fail
([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
verified 2026-08-02).
*Fix.* An attempt timeout must sit inside the breaker so that every call
terminates with an outcome the breaker can classify. See the nesting order in
dimension 12.

**Retry outside the breaker, storming through it.**
*Symptom.* Load on the dependency during an outage is higher than in steady
state. The breaker is open and rejecting, and the rejection count is enormous
while the dependency's request count is low, but CPU on the caller is pinned.
*Cause.* Retry sits inside the breaker instead of outside, so each retry attempt
is counted as an independent failure and a single user request contributes three
or four failures to the window. Alternatively the retry policy does not
recognise the open-circuit rejection and retries it immediately in a tight loop.
Azure warns about exactly this, stating that retry logic should be sensitive to
any exceptions the breaker returns and should stop retrying when the breaker
indicates the fault is not transient.
*Fix.* Put retry outside the breaker, and make the retry predicate treat the
open-circuit exception as non-retryable. Polly's `BrokenCircuitException` carries
a `RetryAfter` property for precisely this decision
([Polly circuit breaker documentation](https://www.pollydocs.org/strategies/circuit-breaker.html),
verified 2026-08-02).

**Probe permit leak.**
*Symptom.* The breaker enters Half-Open and never leaves. Probes are rejected
forever with an open-circuit error even though the dependency recovered hours
ago. Restarting the process fixes it.
*Cause.* The probe counter is incremented on admission and decremented only on
the success path, so a probe that throws leaks a permit. After
`permittedNumberOfCallsInHalfOpenState` failures the gate is permanently shut.
*Fix.* Release the permit in a finally-equivalent construct on every exit path,
including cancellation and timeout. The four samples in this entry decrement in
both the success and failure handlers for this reason.

**Tuned once, never retuned.**
*Symptom.* A breaker that behaved well for a year starts flapping after a
traffic increase, or stops tripping at all after a traffic decrease.
*Cause.* Absolute thresholds do not scale with volume. A minimum call count of
100 per window is a low bar at 10,000 requests per second and an impossible one
at 2 requests per second. A consecutive-failure count of 5 is meaningless when a
single instance now handles a tenth of the previous share.
*Fix.* Prefer rate thresholds with a minimum volume guard over absolute counts,
express the window in time rather than in calls where traffic is bursty, and put
breaker configuration in the same review cycle as capacity planning.

**Breaker used to hide a real error.**
*Symptom.* Customers report stale or missing data. Dashboards are green because
the fallback returns a 200 with an empty list, and the breaker's own rejection
metric was never alerted on.
*Cause.* The fallback lives inside the breaker and returns a plausible empty
result, so a total dependency outage looks like a quiet day.
*Fix.* An empty fallback result must be distinguishable from a real empty
result at every layer, and rejection rate must be alerted on independently of
error rate. Azure lists exception handling as an application concern precisely
because the breaker cannot decide what a degraded answer means.

## 12. Trade-off matrix

The alternatives compared here are named patterns, each with a distinct job.
Timeout, Retry, Bulkhead and Circuit Breaker are not competing choices, they
are four different mechanisms that a production call path uses together.

| Force | Circuit Breaker | Retry with backoff | Timeout | Bulkhead | Rate Limiter | Fallback or Cache | Hedged request |
|---|---|---|---|---|---|---|---|
| Failure it addresses | Sustained dependency failure | Transient, self-clearing failure | A call that never returns | Resource contention across dependencies | Overload the caller creates | Absence of an answer | Tail latency on a healthy dependency |
| Latency under dependency failure | Near zero once tripped | Worse than no retry, multiplies wait | Bounded at the timeout | Unchanged for the failing call | Unchanged | Near zero | Worse, sends more load |
| Load placed on a failing dependency | Reduced to probes | Increased, this is its cost | Unchanged | Capped at the pool size | Capped at the rate | None | Increased |
| Protects the caller's threads | Yes, by rejecting | No, holds them longer | Yes, by releasing them | Yes, by partitioning them | Yes, by shedding early | Yes | No |
| Helps a dependency recover | Yes, sheds load | No, adds load | Neutral | Partly, caps concurrency | Yes | Yes | No |
| Rejects requests that would succeed | Yes, by design | No | Yes, slow but valid ones | Yes, when the pool is full | Yes, above the rate | No | No |
| Needs traffic volume to work | Yes, materially | No | No | No | No | No | No |
| Configuration surface | Large, 4 to 6 knobs | Medium | Small, 1 knob | Small, 1 to 2 knobs | Medium | Application specific | Medium |
| Hidden state | Yes, a state machine | No | No | Counter only | Counter only | Cache freshness | No |
| Correctness risk on writes | High, rejects writes | High, duplicates writes | Medium, unknown outcome | Low | Low | High, stale data | High, duplicates writes |

The composition matters more than the comparison. Microsoft's standard
resilience handler for `HttpClient` documents the order its five strategies are
applied, from outermost to innermost. Rate limiter, then total timeout, then
retry, then circuit breaker, then attempt timeout
([Microsoft, .NET HTTP resilience documentation](https://learn.microsoft.com/en-us/dotnet/core/resilience/http-resilience),
verified 2026-08-02). That order is the answer to the nesting question and every
position in it is load bearing.

```
  request
     |
     v
 +---------------------------------------------------+
 | 1. Rate limiter / Bulkhead                        |  cap concurrency
 |    reject early, before any resource is committed |  before entry
 |  +---------------------------------------------+  |
 |  | 2. Total timeout                            |  |  bound the whole
 |  |    covers every attempt plus its backoff    |  |  operation
 |  |  +---------------------------------------+  |  |
 |  |  | 3. Retry with backoff and jitter      |  |  |  one user request
 |  |  |    stops on OpenCircuitError          |  |  |  -> N attempts
 |  |  |  +---------------------------------+  |  |  |
 |  |  |  | 4. Circuit Breaker              |  |  |  |  sees ONE outcome
 |  |  |  |    counts attempts, not requests|  |  |  |  per attempt
 |  |  |  |  +---------------------------+  |  |  |  |
 |  |  |  |  | 5. Attempt timeout        |  |  |  |  |  guarantees the
 |  |  |  |  |    every call terminates  |  |  |  |  |  breaker gets an
 |  |  |  |  |  +---------------------+  |  |  |  |  |  outcome to count
 |  |  |  |  |  | the actual call     |  |  |  |  |  |
 |  |  |  |  |  +---------------------+  |  |  |  |  |
 |  |  |  |  +---------------------------+  |  |  |  |
 |  |  |  +---------------------------------+  |  |  |
 |  |  +---------------------------------------+  |  |
 |  +---------------------------------------------+  |
 +---------------------------------------------------+
```

Why each position is what it is. The attempt timeout is innermost because the
breaker cannot classify a call that never returns, which is the failure mode
from dimension 11. The breaker sits inside retry so a tripped breaker
short-circuits every remaining attempt instead of the retry loop hammering an
open circuit. Retry sits inside the total timeout so that N attempts plus their
backoff cannot exceed the operation's budget. The rate limiter or bulkhead is
outermost because rejecting before committing a thread or connection is cheaper
than rejecting after.

One consequence of this order is worth stating. The breaker observes attempts,
not user requests, so a retry policy of three attempts triples the sample size
the breaker sees during an outage and trips it three times faster. That is
usually the desired behaviour and it should be a conscious choice, not a
surprise.

**Per-endpoint versus per-service granularity.** The choice is which failure
domain the breaker keys on, and both extremes are wrong.

One breaker per service is too coarse when the service's endpoints have
independent failure modes. A search endpoint backed by a struggling index and a
profile endpoint backed by a healthy cache share nothing except a hostname. A
service-level breaker either trips on the search failures and takes out profile
reads, or is tuned loosely enough to survive them and then never protects
anything. This is the resource differentiation problem Azure describes, applied
to endpoints rather than shards.

One breaker per endpoint per instance is too fine when it fragments the sample.
Ten endpoints across twenty instances is 200 independent windows, each seeing a
twentieth of a tenth of the traffic, and none of them reaching the minimum call
count that makes a rate meaningful. The breakers then behave randomly.

The rule that follows is judgement rather than a sourced claim. Key the breaker
on the smallest unit that has an independent failure mode AND carries enough
traffic to fill its window inside the sampling duration. In practice that
usually means per dependency plus per operation class, so reads and writes to
the same service get separate breakers because they hit different storage paths,
while ten read endpoints backed by the same cache share one. Where the failure
domain is the host rather than the endpoint, for example a partially failed node
in a cluster, the mesh layer is the right place, which is exactly the shape
Envoy's per-host outlier detection takes
([Envoy, Outlier detection](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier),
verified 2026-08-02). Polly's standard hedging handler makes the same choice in
the opposite direction, selecting a breaker from a pool keyed by URL authority,
scheme plus host plus port, so unhealthy endpoints are not hedged against
([Microsoft, .NET HTTP resilience documentation](https://learn.microsoft.com/en-us/dotnet/core/resilience/http-resilience),
verified 2026-08-02).

A useful test for a proposed key. If two calls sharing the key can fail
independently, the key is too coarse. If a key cannot reach the minimum call
volume in one sampling window at normal traffic, the key is too fine.

## 13. Related and incompatible patterns

**Timeout.** Not an alternative, a prerequisite. Without an attempt timeout the
breaker has no outcomes to count for a hung call. Every breaker in production
has a timeout inside it whether the author noticed or not, because the transport
has a default.

**Retry.** Complementary and adjacent, and the pairing needs care. Azure states
that the two serve different purposes, retry expecting eventual success and the
breaker preventing an operation likely to fail, and that an application can
combine them by using retry to invoke an operation through a breaker, provided
retry stops when the breaker signals a non-transient fault
([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
verified 2026-08-02). Retry outside, breaker inside, and the retry predicate
must exclude the open-circuit exception.

**Bulkhead.** Complementary, and it addresses the residual risk the breaker
leaves. The breaker limits calls to one failing dependency, the bulkhead limits
how much of a shared resource any dependency can consume, so a dependency that
fails in a way the breaker does not detect still cannot drain the whole pool.
Netflix used thread pools per dependency for this, with each API instance
carrying more than 40 thread pools
([Netflix Hystrix, How it Works](https://github.com/Netflix/Hystrix/wiki/How-it-Works),
verified 2026-08-02). Envoy's connection and request ceilings are the same idea
at the proxy layer, confusingly labelled circuit breaking
([Envoy, Circuit breaking](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking),
verified 2026-08-02).

**Fallback.** The natural partner. The breaker decides not to call, the fallback
decides what to return instead. A breaker with no fallback story converts a slow
failure into a fast failure, which is worth having but is only half the value.

**Health Endpoint Monitoring.** An input variant. Azure links the two, noting
that a breaker can test service health by calling an endpoint the service
exposes rather than waiting on a timer.

**Rate Limiter and Load Shedding.** Adjacent, pointing the other way. The
breaker protects the caller from a failing dependency. Load shedding protects a
service from its own callers. A system needs both, and confusing them produces a
breaker that trips when the service itself is overloaded, which sheds traffic
the service could have served.

**Hedged requests.** In direct tension. Hedging sends a second copy of a slow
request to reduce tail latency, which adds load to a dependency the breaker may
be trying to relieve. Polly resolves the conflict by putting a per-endpoint
breaker inside the hedging strategy so unhealthy endpoints are excluded from
hedging
([Microsoft, .NET HTTP resilience documentation](https://learn.microsoft.com/en-us/dotnet/core/resilience/http-resilience),
verified 2026-08-02). Hedging without a breaker under it turns a partial outage
into a full one.

**Saga and compensating transaction.** A breaker in front of a saga step means a
step can be rejected without being attempted, which is easier to compensate than
an attempted step with an unknown outcome. The two compose well, but the saga
must treat rejection and failure differently.

Genuinely incompatible in practice. A breaker whose open duration exceeds the
caller's own request deadline is not compatible with a synchronous
request-response API, because the caller will have given up before any probe
runs, and every request during that window is wasted. Either shorten the open
duration or move the work behind a queue.

## 14. Refactoring path in and out

Introducing a breaker into code that does not have one, in an order that keeps
the system working at every step.

1. **Find the boundary.** Locate every call that crosses a process boundary.
   The breaker goes at the boundary, not at the business logic that calls it.
2. **Extract the call behind a single seam.** If the same dependency is called
   from nine places with nine slightly different configurations, introduce one
   client type and route all nine through it. This is the Extract Class and
   Introduce Facade refactoring applied to an integration point, and it is the
   step most of the work lives in. Nothing about resilience improves yet, and
   that is fine.
3. **Add an attempt timeout.** Before any breaker. Confirm it fires by pointing
   the client at a black-hole address and watching the call terminate. Until
   this step passes, a breaker is decorative.
4. **Add classification and measure, without acting.** Instrument the seam with
   a counter split by outcome class, success, dependency failure, caller
   failure. Run for a full traffic cycle including a peak. Now the trip
   threshold can be chosen from data rather than guessed. Resilience4j's
   `METRICS_ONLY` state exists for exactly this phase
   ([Resilience4j CircuitBreaker documentation](https://resilience4j.readme.io/docs/circuitbreaker),
   verified 2026-08-02).
5. **Decide the fallback.** Before the breaker, not after. If there is no
   acceptable answer when the call is skipped, the correct design may be a
   queue, and the breaker discussion ends there.
6. **Insert the breaker with the trip disabled.** Wire the state machine in but
   configure the threshold so it cannot fire, or use the library's disabled
   state. Confirm the metrics and the state gauge appear on a dashboard.
7. **Enable with a conservative threshold.** Start high, for example a 70
   percent failure rate over a large window, then tighten toward the library
   default once the false positive rate is observed.
8. **Order the stack.** Place retry outside, the total timeout outside that, the
   bulkhead outermost, per the diagram in dimension 12.
9. **Prove it.** A test that opens the breaker and a game day that opens it in
   staging. Dimension 15 covers the technique.

Removing a breaker when it stops earning its place, which happens more often
than the literature admits. Three signals justify removal. The dependency now
lives in-process after a merge. The mesh took over the decision. The breaker has
not tripped in a year and its rejections during that year were all false
positives.

1. **Confirm from data, never from opinion.** Query the trip count and the
   rejection count over a long window. A breaker that has genuinely never
   protected anything is a different case from one whose protection you have
   forgotten.
2. **Move to a metrics-only state first.** Keep the observation, stop the
   action. Run for a full cycle. If nothing changes, the breaker was inert.
3. **Verify the replacement covers the same failure.** If the mesh now handles
   it, confirm the mesh's ejection actually fires for the failure mode that
   opened the application breaker. Latency-based trips are the usual gap,
   because host ejection on 5xx does not catch a host that answers slowly and
   correctly.
4. **Remove the breaker, keep the timeout and the classifier.** The timeout is
   always earned. The classification metric is the thing that tells you whether
   removing the breaker was a mistake.
5. **Keep the fallback.** A fallback that only existed because of the breaker is
   usually still the right answer for the timeout path.

## 15. Testing and verification

Practice rather than sourced claim, except where a library behaviour is cited.

**Inject the clock.** The single decision that makes a breaker testable. Every
sample in this entry takes a `now` function or clock closure rather than reading
the system clock. Without that, testing the open-to-half-open transition means
sleeping for the reset duration in a unit test, which makes the suite slow and
flaky and which pushes people to configure absurdly short durations in tests
that then do not resemble production. With an injected clock the whole state
machine is testable in microseconds.

**Test the transitions, not the happy path.** The cases that must exist.

- N failures below the threshold leave the breaker closed.
- The Nth failure trips it, and the transition emits an event.
- A call in Open is rejected without touching the dependency. Assert on a call
  counter on the fake dependency, not only on the exception type, because a
  breaker that rejects after calling is a real bug that a type assertion misses.
- Advancing the clock past the reset duration moves it to Half-Open.
- Concurrent calls in Half-Open beyond the probe limit are rejected.
- One failing probe returns it to Open and restarts the timer.
- The configured number of consecutive probe successes closes it and resets the
  failure counter.
- A probe that throws releases its permit, which is the leak from dimension 11.
- A caller-error outcome, an HTTP 400, does not move the failure counter.

**What became easier to test.** Degraded behaviour. Before the breaker, testing
what the application does when a dependency is down needed a fake that hangs,
which is awkward to arrange and slow. With a breaker, forcing the state is one
call. Resilience4j's `FORCED_OPEN` and Polly's `Isolated` exist partly for this
([Resilience4j CircuitBreaker documentation](https://resilience4j.readme.io/docs/circuitbreaker)
and
[Polly circuit breaker documentation](https://www.pollydocs.org/strategies/circuit-breaker.html),
both verified 2026-08-02). Every integration test can now assert the degraded
path cheaply.

**What became harder to test.** Anything downstream of a shared breaker in an
integration test. A test that generates failures leaves the breaker open, and
the next test in the same process gets rejections it did not expect and cannot
explain. The fix is a fresh breaker per test or an explicit reset in teardown,
and a breaker held in a static field is the reason this bites. Also harder,
whole-path tests where a slow dependency is expected. The breaker may trip
mid-test and change the assertion under you.

**Test doubles that apply.** A fake dependency with programmable outcome
sequences, so a test can express fail, fail, fail, succeed. A controllable clock.
A latency-injecting proxy such as a fault-injection filter for integration
tests. A spy on the event sink to assert transitions rather than inferring them
from behaviour.

**Property-based testing fits well here.** The state machine has invariants that
hold for any sequence of outcomes and clock advances. The breaker is never in
Open with elapsed time greater than the open duration and a call arriving. The
probe count never goes negative. The breaker never admits more than the probe
limit concurrently in Half-Open. Generating random operation sequences against
those invariants finds permit leaks that example tests do not.

**Failure injection in staging.** A game day where the dependency is made slow,
not down, is the one that finds the missing attempt timeout. Down is the easy
case.

## 16. Observability signals

Practice, not sourced, except where Azure's guidance is cited. Azure asks for
clear observability into both failed and successful requests so operations teams
can assess system health, and recommends distributed tracing for visibility
across services
([Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
verified 2026-08-02).

Emit these.

- **State as a gauge**, labelled by breaker key, values closed, open, half_open.
  This is the single most useful signal and the one most often missing.
- **Transition events as a counter**, labelled from-state and to-state. A rate of
  closed-to-open transitions is the flapping detector.
- **Call outcomes as a counter**, labelled outcome in success, failure,
  rejected, and for failures a sub-label for the class, timeout, 5xx, 429,
  transport. Rejected must be its own outcome and never folded into failure,
  because the two mean opposite things about the dependency.
- **Observed failure rate as a gauge**, the value the breaker is actually
  computing. Without it, an operator cannot tell whether a breaker sat at 49
  percent against a 50 percent threshold all night.
- **Calls in the current window as a gauge.** If this sits below the minimum
  volume, the breaker is inert and the operator should know.
- **Probe outcomes as a counter**, so a repeatedly failing half-open probe is
  visible as its own series rather than as generic failures.
- **Time in open state as a histogram.** Long tails mean the dependency is not
  recovering. A tight cluster at exactly the open duration means the breaker is
  flapping.

Trace and log.

- A span attribute on every protected call carrying the breaker key and the
  state at admission time. This makes a rejected request explicable in a trace
  rather than an unexplained fast error.
- A log line at every transition, at warn for closed-to-open and at info for the
  others, carrying the failure rate, the window size and the classified reason.
  Do not log per rejected call. During an outage that is the highest-volume
  event in the system and it will fill the disk while the incident is running.

A healthy breaker on a dashboard. State gauge pinned at closed. Observed failure
rate a flat low line well under the threshold. Window call count comfortably
above the minimum. Zero transitions over days. Rejection counter at zero.

An unhealthy one, and what each shape means. State oscillating between open and
half_open on a fixed period equal to the open duration, which is the thundering
herd from dimension 11. State stuck in half_open with probes rejected, which is
the permit leak. Failure rate high but state closed, which means the window
minimum is never met so the breaker is inert. State closed with rising latency
and no failures, which means the classifier is not counting slow calls and a
slow call rate threshold is needed. Rejections high while the dependency's own
error rate is near zero, which means the classifier is counting caller errors.

Alert on transitions and on sustained open time. Do not alert on rejection
count alone, because a correctly working breaker produces a large rejection
count during a dependency outage that is already alerting on its own.

## 17. Security and privacy implications

Analytical rather than sourced, and the honest answer is that the pattern is
mostly neutral on security with three specific exceptions.

**A breaker is a denial of service amplifier when its key is attacker
controlled.** If the breaker key includes anything a client supplies, a tenant
identifier, a header, a path segment, then an attacker who can drive failures on
their own key gains direct control over whether the breaker opens. Worse, if the
key is coarse and shared, an attacker who can reliably produce dependency
failures can trip a breaker that serves every tenant, converting a small volume
of malicious traffic into a full outage for everyone. The combination with the
classification bug from dimension 11 is the sharp edge, because if 4xx counts as
failure then an attacker needs only to send malformed requests. Key breakers on
server-side identity, never on unvalidated client input, and count only failures
the dependency is responsible for.

**The open state is an information channel.** A response that is fast and
distinctly shaped tells a client that a specific backend is down. Across an API
surface this leaks the internal dependency graph and the current health of each
part of it, which is reconnaissance. The mitigation is to return the same status
and body shape for a rejection as for a genuine dependency failure, and to keep
breaker keys and internal service names out of client-visible errors and headers.
The `Retry-After` header is the one detail worth exposing, because it helps
well-behaved clients back off.

**Fail-open versus fail-closed on a security dependency.** This is the case
where the pattern is genuinely dangerous. A breaker in front of an
authorisation service, a token introspection endpoint, a fraud check or a
consent lookup has to answer a question the resilience literature does not.
When the check cannot run, is the answer allow or deny. A breaker whose fallback
is a cached or default allow has converted a dependency outage into an
authorisation bypass, and it will not appear in any resilience review because it
looks like the pattern working. The rule is that security decisions fail closed
unless a written risk decision says otherwise, and if failing closed is
unacceptable for availability then the correct design is a signed, short-lived
cached decision with an explicit expiry, not a breaker with a permissive
fallback.

On privacy the pattern is close to silent, with one caveat. Breaker telemetry
should carry keys and counts, never request payloads. A well-meaning debug log
that captures the failing request body at trip time is a personal data leak
sitting in an observability pipeline with different retention rules from the
application, and it fires precisely during incidents when logs are shared widely.

The pattern closes one small surface. By capping calls to a failing dependency
it bounds the caller's exposure to a compromised or hijacked upstream, since a
dependency returning malformed responses at volume will trip the breaker and
stop being called.

## 18. References

1. Michael T. Nygard. *Release It! Second Edition. Design and Deploy
   Production-Ready Software*. The Pragmatic Programmers, 2018.
   ISBN 9781680502398. Part I "Create Stability", chapter "Stability Patterns",
   section "Circuit Breaker". Publisher listing and table of contents at
   https://pragprog.com/titles/mnee2/release-it-second-edition/
   Verified 2026-08-02. Source of the pattern's naming, its place among the
   stability patterns, and its pairing with the matching antipattern.
   The chapter and section were confirmed from the publisher table of contents.
   No page number is claimed because no page was independently confirmed.
2. Microsoft. *Azure Architecture Center*, "Circuit Breaker pattern", page dated
   2025-02-05.
   https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker
   Verified 2026-08-02. Source of the three-state proxy formulation, the exact
   transition rules, the time-based failure counter, the Half-Open flooding
   rationale, and the considerations list covering exception types, monitoring,
   recoverability, failed operations testing, manual override, concurrency,
   resource differentiation, accelerated circuit breaking, failed request
   replay, inappropriate timeouts, and the unsuitability list.
3. Netflix. *Hystrix README*.
   https://github.com/Netflix/Hystrix
   Verified 2026-08-02. Source for the maintenance mode statement, the final
   1.5.18 release, the recommendation of Resilience4j, and the stated shift
   toward adaptive implementations such as adaptive concurrency limits.
4. Netflix. *Hystrix wiki, "How it Works"*.
   https://github.com/Netflix/Hystrix/wiki/How-it-Works
   Verified 2026-08-02. Source for the request volume threshold and error
   percentage threshold logic, the single-request Half-Open probe, the sleep
   window, the 10 billion command executions per day figure, and the 40-plus
   thread pools per API instance.
5. Resilience4j project. *CircuitBreaker documentation*.
   https://resilience4j.readme.io/docs/circuitbreaker
   Verified 2026-08-02. Source for the six states including METRICS_ONLY,
   DISABLED and FORCED_OPEN, the count-based and time-based sliding windows with
   subtract-on-evict, the default values for failureRateThreshold,
   slowCallRateThreshold, minimumNumberOfCalls, waitDurationInOpenState and
   permittedNumberOfCallsInHalfOpenState, and the CallNotPermittedException
   behaviour in Half-Open.
6. App-vNext. *Polly documentation, Circuit breaker resilience strategy*.
   https://www.pollydocs.org/strategies/circuit-breaker.html
   Verified 2026-08-02. Source for the Isolated state and
   CircuitBreakerManualControl, the rate-based design, the defaults for
   FailureRatio, SamplingDuration, MinimumThroughput and BreakDuration, and the
   BrokenCircuitException RetryAfter property.
7. Microsoft. *.NET documentation, HTTP resilience page in the fundamentals
   section*, page dated 2026-02-24.
   https://learn.microsoft.com/en-us/dotnet/core/resilience/http-resilience
   Verified 2026-08-02. Source for the standard resilience handler's
   five-strategy ordering from rate limiter to attempt timeout, the circuit
   breaker defaults in that handler, the handled status codes and exceptions,
   and the per-authority breaker pool used by the standard hedging handler.
8. Envoy Project. *Envoy documentation, "Circuit breaking"*.
   https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking
   Verified 2026-08-02. Source for the five concurrency limits Envoy calls
   circuit breaking and for the statement that they are enforced at the network
   level rather than per application.
9. Envoy Project. *Envoy documentation, "Outlier detection"*.
   https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier
   Verified 2026-08-02. Source for passive ejection on consecutive 5xx and
   success rate, the base_ejection_time multiplier on consecutive ejections,
   max_ejection_percent and max_ejection_time, and the unejection on a
   successful active health check.

## Code

Four implementations of the same minimal breaker. Each takes an injected clock,
caps concurrent probes in Half-Open, releases the probe permit on both exit
paths, and returns a rejection type distinct from an operation error.

**TypeScript.** Compiled with `tsc --strict --target es2022` and run on Node.
Output confirmed as open, rejected fast, halfOpen, closed.

```typescript
type State = "closed" | "open" | "halfOpen";

class OpenCircuitError extends Error {
  constructor(readonly retryAfterMs: number) {
    super("circuit open");
  }
}

interface Config {
  failureThreshold: number;
  probeLimit: number;
  successesToClose: number;
  openDurationMs: number;
  now: () => number;
}

class CircuitBreaker {
  private state: State = "closed";
  private failures = 0;
  private successes = 0;
  private probesInFlight = 0;
  private openedAt = 0;

  constructor(private readonly cfg: Config) {}

  async call<T>(op: () => Promise<T>): Promise<T> {
    const permit = this.acquire();
    try {
      const value = await op();
      this.onSuccess(permit);
      return value;
    } catch (err) {
      this.onFailure(permit);
      throw err;
    }
  }

  private acquire(): State {
    if (this.state === "open") {
      const elapsed = this.cfg.now() - this.openedAt;
      if (elapsed < this.cfg.openDurationMs) {
        throw new OpenCircuitError(this.cfg.openDurationMs - elapsed);
      }
      this.state = "halfOpen";
      this.successes = 0;
      this.probesInFlight = 0;
    }
    if (this.state === "halfOpen") {
      if (this.probesInFlight >= this.cfg.probeLimit) {
        throw new OpenCircuitError(0);
      }
      this.probesInFlight += 1;
      return "halfOpen";
    }
    return "closed";
  }

  private onSuccess(permit: State): void {
    if (permit === "halfOpen") {
      this.probesInFlight -= 1;
      if (this.state !== "halfOpen") return;
      this.successes += 1;
      if (this.successes >= this.cfg.successesToClose) {
        this.state = "closed";
        this.failures = 0;
      }
      return;
    }
    this.failures = 0;
  }

  private onFailure(permit: State): void {
    if (permit === "halfOpen") {
      this.probesInFlight -= 1;
      this.trip();
      return;
    }
    this.failures += 1;
    if (this.failures >= this.cfg.failureThreshold) this.trip();
  }

  private trip(): void {
    this.state = "open";
    this.openedAt = this.cfg.now();
    this.successes = 0;
  }

  get current(): State {
    return this.state;
  }
}

let clock = 0;
const cb = new CircuitBreaker({
  failureThreshold: 3,
  probeLimit: 1,
  successesToClose: 2,
  openDurationMs: 1000,
  now: () => clock,
});

const boom = async (): Promise<string> => {
  throw new Error("upstream down");
};
const fine = async (): Promise<string> => "ok";

async function main(): Promise<void> {
  for (let i = 0; i < 3; i++) {
    await cb.call(boom).catch(() => undefined);
  }
  console.log("after 3 failures", cb.current);
  await cb.call(fine).catch((e) => console.log("rejected fast", e.message));
  clock += 1500;
  await cb.call(fine);
  console.log("after 1 probe success", cb.current);
  await cb.call(fine);
  console.log("after 2 probe successes", cb.current);
}

void main();
```

**Python.** Run on CPython 3. Output confirmed as open, rejected fast with a
retry_after of 10.0, half_open, closed. The lock is held only around state
mutation, never around the protected call, which is the concurrency point Azure
raises.

```python
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, TypeVar

T = TypeVar("T")


class OpenCircuitError(RuntimeError):
    def __init__(self, retry_after: float) -> None:
        super().__init__("circuit open")
        self.retry_after = retry_after


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    successes_to_close: int = 2
    probe_limit: int = 1
    open_duration: float = 30.0
    clock: Callable[[], float] = time.monotonic

    _state: str = field(default="closed", init=False)
    _failures: int = field(default=0, init=False)
    _successes: int = field(default=0, init=False)
    _probes: int = field(default=0, init=False)
    _opened_at: float = field(default=0.0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def call(self, op: Callable[[], T]) -> T:
        permit = self._acquire()
        try:
            value = op()
        except Exception:
            self._on_failure(permit)
            raise
        self._on_success(permit)
        return value

    def _acquire(self) -> str:
        with self._lock:
            if self._state == "open":
                elapsed = self.clock() - self._opened_at
                if elapsed < self.open_duration:
                    raise OpenCircuitError(self.open_duration - elapsed)
                self._state = "half_open"
                self._successes = 0
                self._probes = 0
            if self._state == "half_open":
                if self._probes >= self.probe_limit:
                    raise OpenCircuitError(0.0)
                self._probes += 1
                return "half_open"
            return "closed"

    def _on_success(self, permit: str) -> None:
        with self._lock:
            if permit == "half_open":
                self._probes -= 1
                if self._state != "half_open":
                    return
                self._successes += 1
                if self._successes >= self.successes_to_close:
                    self._state = "closed"
                    self._failures = 0
                return
            self._failures = 0

    def _on_failure(self, permit: str) -> None:
        with self._lock:
            if permit == "half_open":
                self._probes -= 1
                self._trip()
                return
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._trip()

    def _trip(self) -> None:
        self._state = "open"
        self._opened_at = self.clock()
        self._successes = 0

    @property
    def state(self) -> str:
        return self._state


if __name__ == "__main__":
    now = [0.0]
    cb = CircuitBreaker(failure_threshold=3, open_duration=10.0, clock=lambda: now[0])

    def boom() -> str:
        raise IOError("upstream down")

    for _ in range(3):
        try:
            cb.call(boom)
        except IOError:
            pass
    print("after 3 failures", cb.state)

    try:
        cb.call(lambda: "ok")
    except OpenCircuitError as exc:
        print("rejected fast, retry after", exc.retry_after)

    now[0] = 20.0
    cb.call(lambda: "ok")
    print("after 1 probe", cb.state)
    cb.call(lambda: "ok")
    print("after 2 probes", cb.state)
```

**Go.** Passed `go vet` and ran, output confirmed as open, rejected fast,
halfOpen, closed. The protected operation is a `func() error`, which composes
with a `context.Context` deadline supplied by the caller as the attempt timeout.
State is guarded by a capacity-one channel used as a semaphore, which is an
ordinary Go idiom and keeps the critical section explicit.

```go
package main

import (
	"errors"
	"fmt"
	"time"
)

type State int

const (
	Closed State = iota
	Open
	HalfOpen
)

func (s State) String() string {
	return [...]string{"closed", "open", "halfOpen"}[s]
}

var ErrOpen = errors.New("circuit open")

type Config struct {
	FailureThreshold int
	SuccessesToClose int
	ProbeLimit       int
	OpenDuration     time.Duration
	Now              func() time.Time
}

type Breaker struct {
	cfg       Config
	gate      chan struct{}
	state     State
	failures  int
	successes int
	probes    int
	openedAt  time.Time
}

func New(cfg Config) *Breaker {
	if cfg.Now == nil {
		cfg.Now = time.Now
	}
	return &Breaker{cfg: cfg, gate: make(chan struct{}, 1)}
}

func (b *Breaker) enter() { b.gate <- struct{}{} }
func (b *Breaker) leave() { <-b.gate }

func (b *Breaker) Call(op func() error) error {
	permit, err := b.acquire()
	if err != nil {
		return err
	}
	if opErr := op(); opErr != nil {
		b.onFailure(permit)
		return opErr
	}
	b.onSuccess(permit)
	return nil
}

func (b *Breaker) acquire() (State, error) {
	b.enter()
	defer b.leave()
	if b.state == Open {
		if b.cfg.Now().Sub(b.openedAt) < b.cfg.OpenDuration {
			return Open, ErrOpen
		}
		b.state = HalfOpen
		b.successes, b.probes = 0, 0
	}
	if b.state == HalfOpen {
		if b.probes >= b.cfg.ProbeLimit {
			return Open, ErrOpen
		}
		b.probes++
		return HalfOpen, nil
	}
	return Closed, nil
}

func (b *Breaker) onSuccess(permit State) {
	b.enter()
	defer b.leave()
	if permit == HalfOpen {
		b.probes--
		if b.state != HalfOpen {
			return
		}
		b.successes++
		if b.successes >= b.cfg.SuccessesToClose {
			b.state, b.failures = Closed, 0
		}
		return
	}
	b.failures = 0
}

func (b *Breaker) onFailure(permit State) {
	b.enter()
	defer b.leave()
	if permit == HalfOpen {
		b.probes--
		b.trip()
		return
	}
	b.failures++
	if b.failures >= b.cfg.FailureThreshold {
		b.trip()
	}
}

func (b *Breaker) trip() {
	b.state = Open
	b.openedAt = b.cfg.Now()
	b.successes = 0
}

func (b *Breaker) State() State {
	b.enter()
	defer b.leave()
	return b.state
}

func main() {
	clock := time.Unix(0, 0)
	b := New(Config{
		FailureThreshold: 3,
		SuccessesToClose: 2,
		ProbeLimit:       1,
		OpenDuration:     10 * time.Second,
		Now:              func() time.Time { return clock },
	})

	boom := func() error { return errors.New("upstream down") }
	fine := func() error { return nil }

	for i := 0; i < 3; i++ {
		_ = b.Call(boom)
	}
	fmt.Println("after 3 failures", b.State())

	if err := b.Call(fine); errors.Is(err, ErrOpen) {
		fmt.Println("rejected fast")
	}

	clock = clock.Add(20 * time.Second)
	_ = b.Call(fine)
	fmt.Println("after 1 probe", b.State())
	_ = b.Call(fine)
	fmt.Println("after 2 probes", b.State())
}
```

**Rust.** Compiled with `rustc -O` and ran, output confirmed as Open, rejected
fast, HalfOpen, Closed. The nested `Result` is the point of this version. The
outer `Result` distinguishes rejection from execution, and the inner one carries
the operation's own error, so a caller cannot accidentally treat a rejection as
an operation failure.

```rust
use std::sync::Mutex;
use std::time::Duration;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum State {
    Closed,
    Open,
    HalfOpen,
}

#[derive(Debug)]
pub struct Rejected;

struct Inner {
    state: State,
    failures: u32,
    successes: u32,
    probes: u32,
    opened_at: Duration,
}

pub struct Breaker<C: Fn() -> Duration> {
    failure_threshold: u32,
    successes_to_close: u32,
    probe_limit: u32,
    open_duration: Duration,
    clock: C,
    inner: Mutex<Inner>,
}

impl<C: Fn() -> Duration> Breaker<C> {
    pub fn new(
        failure_threshold: u32,
        successes_to_close: u32,
        probe_limit: u32,
        open_duration: Duration,
        clock: C,
    ) -> Self {
        Breaker {
            failure_threshold,
            successes_to_close,
            probe_limit,
            open_duration,
            clock,
            inner: Mutex::new(Inner {
                state: State::Closed,
                failures: 0,
                successes: 0,
                probes: 0,
                opened_at: Duration::ZERO,
            }),
        }
    }

    pub fn call<T, E>(&self, op: impl FnOnce() -> Result<T, E>) -> Result<Result<T, E>, Rejected> {
        let permit = self.acquire()?;
        match op() {
            Ok(v) => {
                self.on_success(permit);
                Ok(Ok(v))
            }
            Err(e) => {
                self.on_failure(permit);
                Ok(Err(e))
            }
        }
    }

    fn acquire(&self) -> Result<State, Rejected> {
        let mut g = self.inner.lock().unwrap();
        if g.state == State::Open {
            if (self.clock)().saturating_sub(g.opened_at) < self.open_duration {
                return Err(Rejected);
            }
            g.state = State::HalfOpen;
            g.successes = 0;
            g.probes = 0;
        }
        if g.state == State::HalfOpen {
            if g.probes >= self.probe_limit {
                return Err(Rejected);
            }
            g.probes += 1;
            return Ok(State::HalfOpen);
        }
        Ok(State::Closed)
    }

    fn on_success(&self, permit: State) {
        let mut g = self.inner.lock().unwrap();
        if permit == State::HalfOpen {
            g.probes -= 1;
            if g.state != State::HalfOpen {
                return;
            }
            g.successes += 1;
            if g.successes >= self.successes_to_close {
                g.state = State::Closed;
                g.failures = 0;
            }
            return;
        }
        g.failures = 0;
    }

    fn on_failure(&self, permit: State) {
        let mut g = self.inner.lock().unwrap();
        if permit == State::HalfOpen {
            g.probes -= 1;
        } else {
            g.failures += 1;
            if g.failures < self.failure_threshold {
                return;
            }
        }
        g.state = State::Open;
        g.opened_at = (self.clock)();
        g.successes = 0;
    }

    pub fn state(&self) -> State {
        self.inner.lock().unwrap().state
    }
}

fn main() {
    use std::sync::atomic::{AtomicU64, Ordering};
    static NOW: AtomicU64 = AtomicU64::new(0);
    let cb = Breaker::new(3, 2, 1, Duration::from_secs(10), || {
        Duration::from_secs(NOW.load(Ordering::Relaxed))
    });

    for _ in 0..3 {
        let _ = cb.call(|| Err::<(), &str>("upstream down"));
    }
    println!("after 3 failures {:?}", cb.state());

    if cb.call(|| Ok::<_, &str>(())).is_err() {
        println!("rejected fast");
    }

    NOW.store(20, Ordering::Relaxed);
    let _ = cb.call(|| Ok::<_, &str>(()));
    println!("after 1 probe {:?}", cb.state());
    let _ = cb.call(|| Ok::<_, &str>(()));
    println!("after 2 probes {:?}", cb.state());
}
```

Java and Swift are omitted from the samples, not because the pattern does not
translate but because in both communities the idiomatic answer is to adopt a
library rather than hand-roll. On the JVM that is Resilience4j, which supplies
the sliding windows, the administrative states and the metrics binding that a
hand-written version would have to reinvent.
