---
name: Retry Budget
slug: retry-budget
family: 10-microservices
category: Microservices, Resilience
aliases: [Retry Throttling, Client-Side Retry Throttling, Retry Token Bucket]
first_described: "Twitter, Finagle project, retry budgets blog post, 2016"
maturity: established
related: [circuit-breaker, timeout, bulkhead, remote-procedure-invocation, exponential-backoff-and-jitter, health-check-api, application-metrics]
incompatible_with: []
verified: 2026-08-02
---

# Retry Budget

## 1. Name, aliases, and lineage

The canonical name in wide industry use is Retry Budget. The mechanism is also
called Retry Throttling in the gRPC specification and Client-Side Retry
Throttling in AWS guidance, and the underlying data structure is frequently
called a Retry Token Bucket because nearly every production implementation
uses a token bucket to track how much retry capacity remains.

The earliest widely cited public description under this exact name comes from
Twitter's Finagle RPC framework. The Finagle team published a blog post titled
"Retry Budgets" on 8 February 2016, introducing the `RetryBudget` abstraction
and its default `TokenBucketRetryBudget` implementation, and stating the
motivating problem directly. A fixed retry count per request is either too
generous, and amplifies load during an outage, or too conservative, and
sacrifices legitimate recovery from a transient blip
([Finagle, "Retry Budgets", 8 February 2016](https://finagle.github.io/blog/2016/02/08/retry-budgets/),
verified 2026-08-02). The Finagle post frames retry budgets as a correction to
the older idiom of "retry up to N times per request," which the Finagle team
had shipped for years before concluding that request-scoped retry counts
cannot see the aggregate retry rate across the whole client fleet, which is
the quantity that actually threatens a struggling downstream service.

The same idea appears independently, without the "budget" name, in Google's
gRPC project as "Retry Throttling", specified in gRFC A6 alongside the retry
policy proposal and documented in the public gRPC guide
([gRPC, "Retries"](https://grpc.io/docs/guides/retry/), verified 2026-08-02).
Envoy Proxy ships the same mechanism under the name `RetryBudget`, configured
as a field of the circuit breaker thresholds
([Envoy, `CircuitBreakers.Thresholds.RetryBudget` proto reference](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/cluster/v3/circuit_breaker.proto),
verified 2026-08-02), which is a naming convergence worth noting on its own.
Three independent engineering organizations, Twitter, Google, and the Envoy
project originally spun out of Lyft, arrived at functionally identical
mechanisms and, in two of the three cases, the identical name, within a few
years of each other. This is judgement, not a sourced claim from any of the
three, but it is evidence the pattern was discovered rather than invented, in
roughly the sense Christopher Alexander used when he wrote that a pattern
describes a problem that occurs over and over again.

AWS documents the same behavior without a single fixed proper noun, describing
"client-side throttling" of retries as one of the recommended controls in the
Well-Architected Framework reliability pillar, and crediting the token bucket
implementation shipped in the AWS SDK since 2016
([AWS Well-Architected Framework, REL05-BP03, "Control and limit retry calls"](https://docs.aws.amazon.com/en_us/wellarchitected/2022-03-31/framework/rel_mitigate_interaction_failure_limit_retries.html),
verified 2026-08-02). This catalog uses Retry Budget as the canonical name
because it is the name that ships in the most widely deployed configuration
surface, Envoy's `circuit_breaker.proto`, and because it is the name the
pattern's own inventors at Twitter gave it.

## 2. Problem and context

A service client calls a downstream dependency over the network. The call can
fail for reasons that are transient, a single backend instance briefly
overloaded, a load balancer routing to an instance mid-restart, a packet lost
on a congested link, or reasons that are not transient, the downstream is
genuinely out of capacity, a bad deploy is failing every request, a database
behind the downstream is down. The naive fix for transient failure is to
retry the call, and retrying transient failures genuinely improves the
end-to-end success rate seen by the caller, which is why every serious RPC
framework ships retry support by default.

The context where the problem in this entry arises is the second failure
class, the non-transient one, combined with fan-out. A downstream service in a
microservice topology is rarely called by one client. It is called by dozens
or hundreds of upstream services, each of which independently decided, for
good local reasons, to retry failed calls up to some fixed count, commonly
three. When the downstream genuinely degrades, every one of its callers
observes failures at roughly the same time, and every one of them independently
triples or quadruples its offered load in response, because each caller is
retrying every failed call up to three times. The retries do not find spare
capacity, because there is none, they find more of the same overloaded
service, and they fail too, at which point the same clients that are also
retrying the retries continue to pile load onto a service that is now serving
strictly less useful work per unit of incoming request than it was before any
client began retrying. This failure mode has a name of its own, retry storm or
retry amplification, and AWS's Well-Architected guidance describes it
directly, stating that at scale, and if clients attempt to retry the failed
operation as soon as an error occurs, the network can quickly become saturated
with new and retried requests, each competing for network bandwidth, and that
this can result in a retry storm which reduces availability of the service
([AWS Well-Architected Framework, REL05-BP03](https://docs.aws.amazon.com/en_us/wellarchitected/2022-03-31/framework/rel_mitigate_interaction_failure_limit_retries.html),
verified 2026-08-02).

Backoff and jitter alone do not solve this. Exponential backoff spreads retries
out in time per client, and jitter prevents synchronized retry waves from a
single client's own request stream, but neither backoff nor jitter puts any
ceiling on the aggregate volume of retry traffic the downstream receives once
thousands of independent client processes are each backing off and retrying on
their own schedule. A per-request retry limit, three tries and stop, has the
same blind spot for the same reason. It bounds how many times one request can
retry. It says nothing about how many requests, in aggregate, across the whole
fleet, are retrying right now. Retry budget exists to put a number on that
aggregate quantity and refuse new retries once the number is exceeded, so that
the fraction of total offered load that is retry traffic is bounded regardless
of how many upstream services or how many client processes exist.

## 3. Forces

**Recoverability versus load amplification.** A retry that succeeds converts
a transient failure into a success the caller never has to know about. A retry
that fails against a genuinely down dependency is pure wasted load, and it is
load added at exactly the moment the dependency can least afford it, because
retries concentrate on the failing subset of a fleet by construction. The
retry budget's entire reason to exist is choosing a bound on this trade rather
than leaving it unbounded.

**Fast local decisions versus global visibility.** The individual client that
decides whether to retry a given failed call has no visibility into what every
other client of the same downstream is doing right now. A per-request retry
count is a purely local decision. A retry budget requires each client to keep
a small piece of local state, the token bucket, that is a proxy for a global
quantity, the aggregate success rate of calls to that downstream, without
requiring any actual coordination between clients. This is the pattern's
central engineering trick. It approximates a global signal from a purely local
statistic, at the cost of never seeing the true aggregate directly.

**Availability of the calling service versus availability of the downstream.**
An individual client wants to retry every failed call it can, because every
successful retry is one fewer error surfaced to whatever called it. A retry
budget deliberately sacrifices some of that local availability, refusing
retries once the budget is spent, in exchange for protecting the availability
of the shared downstream, and by extension every other client that shares it.
This is a fairness trade as much as a technical one, and it only pays off if
most clients of a shared downstream adopt the same discipline, which is why
retry budgets are usually shipped as framework or sidecar defaults rather than
left to individual application authors.

**Operational simplicity versus adaptiveness.** A fixed per-request retry
count of three is trivial to reason about and requires no runtime state. A
retry budget requires a token bucket, a decay or time-to-live policy on the
tokens, and a decision about what percentage of traffic is allowed to be
retries, and that percentage itself is a tuning parameter that can be wrong in
either direction. The pattern trades a small amount of operational and
conceptual complexity for a behavior that degrades gracefully as the aggregate
failure rate rises, instead of amplifying linearly with it.

**Coupling to observability.** A retry budget is only as good as the signal it
is fed. If the client cannot distinguish a genuine failure from, for instance,
a client-side bug that always returns an error before the call is even sent,
the budget will drain on noise that has nothing to do with the downstream's
health, and legitimate retries will be refused for the wrong reason. This
couples the pattern to the correctness of the surrounding error classification
logic, discussed further in dimension 11.

## 4. Applicability and non-applicability

Reach for a retry budget when the following hold together.

- The client makes network calls to a downstream service, and the same
  downstream is called by many other clients, so an uncoordinated per-request
  retry policy can produce a retry storm during a downstream degradation.
- The call being retried is idempotent, or the framework can make it
  idempotent through a mechanism such as an idempotency key, because a retry
  budget bounds the volume of retries but does nothing to prevent a
  non-idempotent retried write from executing twice.
- The client already has, or is willing to build, a lightweight per-call
  outcome signal, success or failure, that the budget's token bucket can
  consume, typically inside the same client-side interceptor or middleware
  layer that already implements the retry loop and backoff.
- The system operates at a scale where the aggregate retry volume across
  clients is a meaningful fraction of total traffic to a shared downstream,
  which in practice means more than a handful of caller processes or more than
  a trivial request rate.

Do not reach for a retry budget in these situations, and use the alternative
named in parentheses instead.

- **A single client talking to a dependency it does not share with anyone
  else**, where a per-request retry count with jitter is sufficient because
  there is no fan-out to amplify (use exponential backoff and jitter alone,
  dimension 13 below).
- **A call that mutates state and is not idempotent, and cannot be made
  idempotent**, because bounding retry volume does not address the correctness
  problem of a duplicate write, and the correct fix is either to make the
  operation idempotent or to not retry it at all (use idempotent consumer or
  an idempotency key pattern first, then layer a retry budget on top once the
  call is safe to repeat).
- **A downstream that is already fully unavailable, not merely degraded**,
  where the correct response is to stop calling it entirely rather than to
  spend a portion of the retry budget on calls that are certain to fail (use a
  circuit breaker in front of, or composed with, the retry budget, dimension
  13 below).
- **A batch or offline job with no latency requirement and no shared
  downstream contention**, where simple fixed-count retries with a generous
  backoff are sufficient and the added state of a token bucket is unjustified
  complexity for a workload that does not create fan-out pressure.
- **Server-side retries of a request the server itself received**, as opposed
  to client-side retries of an outbound call the server is making, which is a
  different problem addressed by request deduplication and idempotency keys,
  not by the client-side mechanism this entry describes.

## 5. Structure

- **Caller.** The code issuing the RPC or HTTP call. It invokes the retry
  logic and ultimately receives either a successful response or an exhausted
  failure.
- **Retry Budget.** The stateful component holding the token bucket. It
  exposes two operations to the retry loop, a query of whether a retry is
  currently permitted, and a report of the outcome, success or failure, of
  each attempt including the initial one. The budget is typically scoped per
  destination, meaning per downstream service or per upstream cluster, not
  global to the process and not per individual request.
- **Token Bucket.** The underlying data structure. It holds a bounded pool of
  tokens. A successful call deposits a fractional token, a retry attempt
  withdraws a whole token, and the bucket enforces both an upper bound, so
  tokens cannot accumulate without limit during a long healthy period, and a
  lower bound at or near zero, below which retries are refused.
- **Retry Policy.** The surrounding logic that decides how many times, with
  what backoff and jitter, and under what error classification a call is
  eligible to be retried at all, independent of budget. The retry budget gates
  this policy, it does not replace it, a call still needs a retryable error
  and remaining attempts under the policy's own cap before the budget is even
  consulted.
- **Downstream Service.** The dependency being called. It is the entity the
  budget exists to protect, and in practice it never has direct knowledge that
  a budget exists on the caller side.

## 6. ASCII structure diagram

```
+------------------+        query()        +-------------------+
|      Caller      |----------------------->|    Retry Budget    |
|  (RPC / HTTP      |                        |  wraps a token      |
|   client stub)    |<-----------------------|  bucket per         |
+------------------+   permit / deny         |  destination         |
        |                                    +-------------------+
        |  report(outcome)                            ^
        |------------------------------------------->  |
        v                                               |
+------------------+                                    |
|   Retry Policy    |   backoff, jitter,                 |
|  (attempt count,  |   error classification             |
|   retryable set)  |------------------------------------+
+------------------+
        |
        v
+------------------+
| Downstream        |
| Service            |
+------------------+
```

## 7. Dynamics

The token bucket in the retry budget dynamic works identically across every
production implementation surveyed for this entry, differing only in the
exact numeric constants. Deposits happen on success, withdrawals happen on
retry, and the current fill level gates whether the next retry is even
attempted.

```
time ->

call #1 (initial attempt)        succeeds
  budget: deposit +tokenRatio     bucket: 9.10 -> 9.20

call #2 (initial attempt)        fails, retryable error
  budget: no change on the initial attempt
  retry policy asks budget: "may I retry?"
  budget: bucket (9.20) > threshold (maxTokens/2 = 5.0) -> PERMIT
  budget: withdraw 1 token        bucket: 9.20 -> 8.20
  retry attempt                   succeeds
  budget: deposit +tokenRatio     bucket: 8.20 -> 8.30

... downstream begins to degrade, failure rate rises sharply ...

call #N (initial attempt)        fails
  retry policy asks budget: "may I retry?"
  budget: bucket (4.80) < threshold (5.0) -> DENY
  caller receives the original failure immediately, no retry issued

call #N+1 (initial attempt)      fails
  budget: bucket still below threshold -> DENY
  (this repeats for every caller sharing this budget, across the fleet,
   until enough successes refill the bucket above threshold again)
```

The essential property visible in this trace is that the budget denies retries
the moment the ratio of failures to successes crosses the configured
threshold, well before the bucket reaches zero, which in Envoy's and gRPC's
implementations happens at exactly half of the configured maximum. This
half-threshold design is deliberate. It leaves headroom so that a brief burst
of transient failures does not fully exhaust the budget and lock out retries
for calls that would otherwise have succeeded, while still triggering the
protective denial well before the client would be contributing meaningfully to
retry storm load.

## 8. Implementation variants

**Token bucket with a fixed deposit ratio, gated at half capacity (gRPC and
Envoy).** The client maintains `token_count`, a floating point value bounded
between zero and `maxTokens`. Every failed call decrements the count by one
token. Every successful call increments it by `tokenRatio`, a fraction less
than one, commonly `0.1`. Retries are permitted only while `token_count`
remains above half of `maxTokens`
([gRPC, "Retries"](https://grpc.io/docs/guides/retry/), verified 2026-08-02).
Envoy exposes the same mechanism as `RetryBudget` with a `budget_percent`
field expressing the retry ceiling as a percentage of concurrent active
requests plus active pending requests, defaulting to 20 percent, and a
`min_retry_concurrency` floor, defaulting to 3, so a low-traffic service
is not denied every retry purely because its absolute request volume is small
([Envoy, `circuit_breaker.proto`, `RetryBudget`](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/cluster/v3/circuit_breaker.proto),
verified 2026-08-02). This variant is the most widely deployed one because it
ships as infrastructure default rather than requiring application code.

**Time-decayed token bucket with an explicit percentage cap (Finagle).**
Finagle's default `TokenBucketRetryBudget` is parameterized by
`percentCanRetry`, defaulting to 20 percent, `ttl`, defaulting to 10 seconds,
and `minRetriesPerSec`, defaulting to 10. Tokens expire after the configured
time-to-live rather than only decaying through explicit withdrawal, so a
downstream that recovers is not penalized by tokens spent during an outage
that has already ended, the bucket's effective state reflects only recent
history, not the entire process lifetime
([Finagle, "Retry Budgets"](https://finagle.github.io/blog/2016/02/08/retry-budgets/),
verified 2026-08-02). This variant is the more configurable one and is the
shape most commonly reimplemented by hand outside the Twitter and Envoy
ecosystems, because the time-window framing, "no more than X percent of calls
in the last N seconds may be retries," is the easiest version of the idea to
explain to an application team that has not encountered the pattern before.

**Sliding window counter instead of a token bucket.** Rather than a
continuous-valued bucket, some hand-rolled implementations track two integer
counters over a fixed or sliding time window, total attempts and retry
attempts, and simply compute the ratio on each retry decision, denying once
the ratio exceeds a configured cap. This is functionally close to the
time-decayed token bucket but trades the smoother exponential-style decay of a
true bucket for simpler, more auditable arithmetic. It is judgement on this
entry's part, not a sourced claim, that this variant is more common in
internally built resilience libraries that predate exposure to the Finagle or
gRPC prior art, because it is the version an engineer is most likely to invent
independently when solving the problem from first principles.

**Per-destination versus global scoping.** Every production implementation
surveyed scopes the budget per downstream destination, per upstream cluster in
Envoy's terms, per service name in Finagle's and gRPC's terms, rather than one
global budget shared across every dependency a client calls. A single
misbehaving downstream should not exhaust the retry allowance available for
calls to a healthy one. A variant seen in simpler client libraries collapses
this to a single process-wide budget when the client only ever talks to one
downstream, which is a legitimate simplification but stops being correct the
moment a second dependency is added.

**Composed with a circuit breaker.** A common production variant does not use
the retry budget as the sole gate. It layers a circuit breaker in front of the
call, so that once the downstream is judged fully unhealthy the circuit opens
and no calls, retried or otherwise, are attempted at all, while the retry
budget continues to govern the finer-grained decision of whether an individual
failed call, while the circuit remains closed, is worth retrying. This
composition is discussed further in dimension 13.

## 9. Known production uses

**Envoy Proxy**, the widely deployed L7 sidecar proxy and the data plane for
Istio and several other service meshes, implements retry budgets natively as
part of its circuit breaker configuration, `CircuitBreakers.Thresholds.
RetryBudget`, with a documented default `budget_percent` of 20 percent and
`min_retry_concurrency` floor of 3
([Envoy, `circuit_breaker.proto` API reference](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/cluster/v3/circuit_breaker.proto),
verified 2026-08-02). Because Envoy sits as the sidecar for every service in a
mesh deployment, this makes retry budgets an ambient, largely invisible
default for any organization running Istio, Consul Connect, or a bespoke Envoy
mesh, without individual application teams writing any retry-budget code
themselves.

**Google gRPC**, specified across every officially supported language
implementation, C, Java, Go, and the rest, ships retry throttling as part of
its per-method service configuration, configured with `maxTokens` and
`tokenRatio` fields and gated at half of `maxTokens` as described in dimension
8 ([gRPC, "Retries"](https://grpc.io/docs/guides/retry/), verified
2026-08-02). Any gRPC client that enables the service config's `retryPolicy`
alongside `retryThrottling` inherits this behavior directly from the framework
runtime.

**Twitter's Finagle**, the JVM RPC framework used across Twitter's backend
services and later open sourced, is the framework whose blog post coined the
retry budget name used throughout this entry, and it ships
`TokenBucketRetryBudget` as the default `RetryBudget` implementation attached
to Finagle's client stack, with the specific default parameters documented in
dimension 8 ([Finagle, "Retry Budgets"](https://finagle.github.io/blog/2016/02/08/retry-budgets/),
verified 2026-08-02).

**AWS SDKs**, across the language SDKs AWS ships for calling its own services,
implement client-side retry throttling using a token bucket that AWS states
has been built into the SDKs since 2016, as documented in the AWS
Well-Architected Framework's reliability pillar guidance on controlling and
limiting retry calls
([AWS Well-Architected Framework, REL05-BP03](https://docs.aws.amazon.com/en_us/wellarchitected/2022-03-31/framework/rel_mitigate_interaction_failure_limit_retries.html),
verified 2026-08-02). This makes retry budgets an ambient default for any
application calling AWS APIs, S3, DynamoDB, and the rest, through an
AWS-provided SDK, in the same way Envoy makes it an ambient default for mesh
traffic.

## 10. Consequences

**Positive.**

- Bounds the fraction of total offered load to a downstream that can ever be
  retry traffic, which directly prevents the retry storm failure mode
  described in dimension 2, without requiring any single client to have
  visibility into what every other client is doing.
- Degrades gracefully. As the true failure rate of a downstream rises, the
  fraction of retries permitted falls automatically, because the bucket fills
  more slowly and drains faster, requiring no operator intervention or manual
  circuit-breaker style state transition to take effect.
- Composes cleanly with existing retry and backoff logic. The budget is a gate
  consulted before an already-decided retry attempt is issued, so it can be
  layered onto an existing retry loop with a small, localized code change
  rather than a rearchitecture.
- Per-destination scoping means a single degraded dependency does not consume
  retry capacity that would otherwise be available for calls to healthy
  dependencies sharing the same client process.

**Negative.**

- Adds stateful, mutable, concurrently-accessed state, the token bucket, to
  every client that adopts it, which is a small but real increase in
  implementation and testing surface compared to a stateless per-request
  retry count.
- The threshold and ratio parameters, `tokenRatio`, `budget_percent`,
  `percentCanRetry`, are tuning knobs that can be set wrong in either
  direction. Too generous and the budget fails to prevent a retry storm under
  genuine load, too conservative and legitimate transient-failure recovery is
  denied during ordinary background error noise, degrading availability the
  caller could otherwise have recovered from at no real cost to the
  downstream.
- A shared budget scoped too coarsely, for example one budget shared across
  many logically distinct call sites to the same physical destination, can let
  a high-volume, low-importance call site exhaust the budget and starve a
  low-volume, high-importance call site to the same destination of any retry
  capacity at all.
- The pattern only protects the downstream from retry-amplified load. It does
  nothing about the load from first attempts, so a retry budget alone cannot
  prevent an overload caused purely by organic traffic growth. It must be
  paired with the other resilience patterns in dimension 13 to form a complete
  defense.

## 11. Failure modes and misuse

**Symptom.** Retries stop happening entirely during a genuine, sustained
outage, and error rates surfaced to end users are indistinguishable from a
system with no retry logic at all.

**Cause.** This is largely the pattern working as intended, not a bug, once a
downstream is genuinely and persistently failing, the budget is supposed to
deny retries so client fleets do not amplify the outage. The misuse to watch
for is treating a fully denied budget as a signal that retries are broken,
when it is in fact the correct signal that the downstream, not the retry
logic, needs remediation.

**Fix.** Pair the budget with a circuit breaker and clear dashboards,
discussed in dimensions 13 and 16, so operators can distinguish a budget
that correctly denied retries because the dependency is down from a retry
logic bug, and route the incident response accordingly, toward the downstream
rather than toward the client's retry code.

**Symptom.** A low-traffic call site to an otherwise healthy shared
destination intermittently sees every retry denied, even though the
destination's overall error rate looks fine on its own dashboards.

**Cause.** The retry budget for that destination is being drained by a
different, much higher-volume call site sharing the same destination and the
same budget scope, and the low-volume call site's own healthy traffic is not
enough to refill the shared bucket fast enough to offset the other call
site's withdrawals.

**Fix.** Scope budgets more finely, per call site or per logical operation as
well as per destination, when call sites to the same physical service have
very different traffic volumes or very different tolerance for a denied
retry, or raise the `min_retry_concurrency` floor so low-volume traffic is
not starved purely by the arithmetic of a shared percentage.

**Symptom.** The budget drains rapidly even though the downstream service's
own metrics show it is healthy and error-free.

**Cause.** The client's error classification treats a category of error as
retryable that should never be retried at all, most commonly a client-side
bug such as a malformed request that always fails validation, or an
authentication token that has expired and will fail every subsequent attempt
identically. Every such call correctly counts as a failure in the budget's
accounting, because from the budget's point of view a withdrawn token is a
withdrawn token regardless of whose fault the failure was, but none of those
failures are actually about the downstream's health, so the budget is being
drained on noise unrelated to the condition it exists to protect against.

**Fix.** Separate the concept of an error being retryable at all from an
error that should count against the shared retry budget, and audit the error
classification feeding the budget so that deterministic, non-transient client
errors, 4xx-class errors in the HTTP analogy, are excluded from budget
accounting even when the retry policy itself correctly refuses to retry them.

**Symptom.** A service appears to have effectively no retry protection at
all, because its client library was written before the organization adopted
retry budgets, and continues to retry every failed call up to a fixed count
regardless of aggregate fleet behavior.

**Cause.** A retry budget is an opt-in pattern implemented inside a specific
client library or sidecar. A service whose client stack predates the
adoption, or that bypasses the shared client library and issues raw HTTP or
socket calls directly, gets none of the protection, and its retries continue
to contribute unbounded load to a shared, struggling downstream even while
every other, budget-aware client in the same incident correctly backs off.

**Fix.** Treat retry budget adoption as a fleet-wide migration with a
completion target, and, where feasible, enforce the behavior at the
infrastructure layer, for example by moving retry logic into a shared
sidecar proxy such as Envoy rather than leaving it to each application
team's own client code, so adoption does not depend on every team
remembering to opt in.

## 12. Trade-off matrix

| Force | Retry Budget | Fixed per-request retry count | Circuit Breaker alone | Bulkhead alone |
|---|---|---|---|---|
| Bounds aggregate fleet-wide retry load | Yes, directly, by design | No, only bounds per-request retries, not fleet aggregate | Indirectly, once tripped it stops all traffic including retries, but has no notion of a partial retry allowance | No, bulkheads isolate resource pools per dependency but do not gate retry decisions at all |
| Degrades gracefully as failure rate rises | Yes, denial rate rises continuously with failure rate | No, fixed count is oblivious to fleet-wide failure rate | No, binary open or closed transition, not a gradient | No, isolation is static, not responsive to failure rate |
| Requires stateful, shared, concurrently-accessed data structure | Yes, the token bucket | No, purely per-request state | Yes, the breaker's own failure counter and state machine | Yes, the resource pool or semaphore per dependency |
| Protects against non-idempotent retry duplication | No, orthogonal concern | No, orthogonal concern | No, orthogonal concern | No, orthogonal concern |
| Distinguishes downstream fully down from briefly degraded | Partially, denial rate correlates with degradation but no explicit open state | No | Yes, this is exactly what the breaker's state machine models | No |
| Operational simplicity to introduce into an existing retry loop | Moderate, requires a small stateful gate wrapped around existing logic | Lowest, already the default in most client libraries | Moderate to high, requires a state machine and failure-rate windowing | Moderate, requires resource pool partitioning per dependency, often the largest change of the four |

## 13. Related and incompatible patterns

**Circuit Breaker.** The two patterns are complementary and commonly deployed
together rather than as alternatives, despite both appearing in the trade-off
matrix above as if competing. A circuit breaker makes a binary decision,
whether calls to this downstream are currently allowed at all, based on a
recent failure-rate window, and when open it stops every call, first attempts
included, saving the client the cost of even issuing the request. A retry
budget makes a finer-grained decision that only applies once a call has
already failed and the retry policy has already decided the error is worth
retrying, namely whether there is currently enough retry capacity left in the
aggregate budget for this one destination to spend a token on this particular
retry. Production topologies, Envoy's chief among them, typically run the
breaker as the outer gate and the retry budget as an inner one, so that when
the breaker is open no calls happen at all, and when it is closed the retry
budget still governs how much of the traffic that does get through is allowed
to be retries rather than first attempts.

**Timeout.** A retry budget has no protective effect without a bounded
timeout on each individual call attempt, because a retry loop that waits
indefinitely on a hung attempt never reaches the point of asking the budget
whether a retry is permitted, the timeout is what converts a hang into the
failure signal the budget needs to see. The same AWS reliability guidance
cited above treats timeouts, retries, and backoff with jitter as a combined
foundation resilient remote clients are built on, not as independent options
to pick from
([AWS Well-Architected Framework, REL05-BP03](https://docs.aws.amazon.com/en_us/wellarchitected/2022-03-31/framework/rel_mitigate_interaction_failure_limit_retries.html),
verified 2026-08-02).

**Exponential Backoff and Jitter.** Backoff and jitter govern the timing of
individual retries for a single request, spreading them out so a burst of
simultaneous failures does not itself synchronize into a wave of simultaneous
retries. Retry budget governs the aggregate volume of retries across every
request and every client sharing a destination. The two solve adjacent but
distinct halves of the retry storm problem, timing versus volume, and are
routinely implemented in the same retry interceptor, one governing when the
next attempt happens and the other governing whether it is allowed to happen
at all.

**Bulkhead.** A bulkhead partitions finite client-side resources, thread
pools, connection pools, semaphores, per downstream dependency, so exhaustion
calling one dependency cannot starve calls to another. It is a resource
isolation pattern, not a decision-gating pattern, and it composes with retry
budget rather than overlapping it, a retry budget can deny a retry before it
ever competes for a connection from a bulkhead's pool, reducing the pressure
the bulkhead itself has to absorb.

**Idempotent Consumer and idempotency keys.** These patterns make an
operation safe to execute more than once, which is a prerequisite for safely
retrying it at all. Retry budget assumes this precondition is already met, it
governs how much retry volume is permitted, never whether a particular
operation is safe to retry in the first place. Attempting to apply a retry
budget to a call that is not idempotent does not make the call safe, it only
bounds how many times an unsafe duplicate can occur, which is rarely the
actual guarantee the caller needs.

**Health Check API.** Health checks feed the load balancing and routing layer
that decides which instances of a downstream receive traffic at all, which is
a separate mechanism from a retry budget's client-side gating of how many
retries are permitted to whatever instances the load balancer does route to.
A well-tuned health check reduces the rate at which clients even encounter the
failures a retry budget exists to bound, so the two patterns lower each
other's load in practice, without either depending on the other's presence.

**No documented incompatibility.** No source consulted for this entry
describes a pattern that a retry budget actively conflicts with in the sense
of the two being mutually exclusive, every related pattern above is
complementary rather than substitutable one-for-one.

## 14. Refactoring path in and out

Introducing a retry budget into an existing client that already retries on
fixed counts, but has no aggregate throttling, proceeds in stages.

1. Confirm every call site that will share a budget is calling an idempotent
   operation, or is guarded by an idempotency key mechanism, because a retry
   budget does not itself make an unsafe retry safe, this is the same
   precondition the applicability section names, and it must be true before
   step 2 has any point in being taken.
2. Introduce a single shared, per-destination token bucket, or adopt an
   existing framework's implementation, gRPC's `retryThrottling` service
   config field or Envoy's `RetryBudget` circuit breaker threshold, rather
   than hand-rolling a new one, unless the client stack has no such framework
   support available.
3. Wire the bucket's outcome-reporting call into the existing retry
   interceptor at the point where each attempt, including the very first one,
   completes, depositing on success and withdrawing on a retry attempt as
   described in dimension 8, being careful to withdraw only on the retry
   itself, never on the initial attempt.
4. Wire the bucket's permission query into the existing retry decision, so
   that a call which the pre-existing retry policy already judged eligible
   for a retry, retryable error, attempts remaining under the per-request cap,
   is additionally gated on the budget's permission before the retry is
   issued.
5. Ship the change with the budget's threshold set generously at first, a
   high `budget_percent` or `percentCanRetry`, and observe the denial rate in
   production before tightening it, because the correct threshold is a
   property of the real traffic pattern to that destination and is rarely
   knowable in advance, treat the initial rollout as measurement, not as the
   final tuning.
6. Add the dashboard and alert coverage from dimension 16 before considering
   the rollout complete, because a silently-denying budget with no visibility
   reproduces the symptom described first in dimension 11.

Removing a retry budget, when a call site's traffic pattern has changed enough
that the fixed-scope shared bucket no longer models the caller's actual retry
needs, for example after splitting one high-volume monolithic client into
several independently scaled services each calling the same downstream,
proceeds by first re-scoping the budget per new service rather than removing
it outright, since the reason for having one at all, aggregate fleet-wide
retry load against a shared downstream, has not gone away merely because the
caller has been split. A retry budget is genuinely removable only when the
downstream it protects is no longer shared by more than one caller, at which
point a per-request fixed retry count with backoff and jitter, dimension 13,
is sufficient and the budget's added state has stopped earning its cost, per
dimension 3.

## 15. Testing and verification

Retry budget logic is unusually testable compared to most resilience
mechanisms because the token bucket is pure, deterministic state given a
sequence of deposit and withdrawal events, and the pass or fail decision at
any point in time is a pure function of that state, with no network calls, no
real clocks beyond what a time-decayed variant needs, and no concurrency
required to exercise the core logic in a unit test.

- Unit test the bucket in isolation, injecting a fixed clock. Feed the
  bucket a scripted sequence of successes and failures and assert the exact
  permit or deny outcome at each step, including the boundary case at exactly
  half of `maxTokens`, which is where an off-by-one in a hand-rolled
  implementation is most likely to hide. Time-decayed variants need a fake or
  injectable clock so a test can assert that tokens genuinely expire after the
  configured time-to-live without the test itself needing to sleep in real
  time.
- Property-based test the invariant that the bucket never falls below its
  floor or exceeds its ceiling, generating long random sequences of
  successes and failures and asserting the bucket's value stays within
  `[0, maxTokens]` after every event, which catches accumulation bugs that a
  small number of hand-written scenarios tend to miss.
- Integration test the retry interceptor with a fault-injecting fake
  downstream that can be told to fail every request for a configured
  duration, then asserting two things together, that the observed retry rate
  against the fake downstream falls as the injected failure rate rises, and
  that the caller still sees, and correctly surfaces, the original failure
  once the budget denies a retry, rather than swallowing it silently.
- Load test the shared-scope failure mode from dimension 11 by running
  two simulated call sites of very different volume against the same fake
  downstream sharing one budget, and asserting the low-volume call site's
  effective retry allowance is not starved below a documented floor, which is
  exactly what `min_retry_concurrency` exists to guarantee in Envoy's
  implementation and is worth asserting explicitly rather than trusting the
  configuration default.

What becomes easier because of the pattern. Reasoning about worst-case
retry-amplified load on a downstream becomes a bounded calculation, budget
percentage times steady-state offered load, rather than an unbounded
function of however many clients happen to be retrying at once, which makes
capacity planning and load testing of the downstream itself more tractable.

What becomes harder. End-to-end tests that assert a specific number of
retries were attempted for a given failure become sensitive to whatever
other traffic shares the same budget during the test run, so budget-aware
retry logic is best isolated per test with its own freshly constructed
bucket rather than sharing process-wide state across an entire test suite.

## 16. Observability signals

- Retry budget denial rate, per destination. The count or rate of retry
  attempts denied because the bucket was below threshold. This is the single
  most important signal the pattern adds, a sustained nonzero denial rate
  means the budget is actively protecting a downstream, and an operator
  should be able to see this correlated against the downstream's own error
  rate to distinguish working as intended during a real incident from
  misconfigured and denying during ordinary operation, the failure mode
  described first in dimension 11.
- Current token bucket fill level, per destination, as a gauge. Exposed as
  a percentage of `maxTokens`, this gives a leading indicator of an
  approaching denial state before denials actually start, useful for alerting
  ahead of the point where the budget begins visibly refusing retries.
- Retry-to-first-attempt ratio, per destination, over a rolling window.
  This is the observed value of the same quantity the budget's percentage
  threshold is trying to bound, and comparing it directly against the
  configured `budget_percent` or `percentCanRetry` is the most direct way to
  validate the threshold is set sensibly for the real traffic pattern, rather
  than tuning blind.
- Correlation with downstream-reported error rate and saturation
  metrics. A healthy dashboard shows the retry denial rate rising in step
  with the downstream's own reported error rate or CPU and queue saturation,
  which is the sign the budget is reacting to genuine degradation. A denial
  rate that rises with no corresponding movement in the downstream's own
  health metrics points at the misclassified-error failure mode from
  dimension 11.

A healthy instance of this pattern in production, as engineering judgement
rather than a sourced universal number, typically shows a near-zero denial
rate during normal operation, a bucket fill level that hovers near its
ceiling rather than oscillating close to the threshold, and a sharp,
short-lived spike in both the denial rate and the retry-to-first-attempt
ratio precisely coincident with any real downstream incident, followed by a
return to baseline once the downstream recovers and successful calls refill
the bucket.

## 17. Security and privacy implications

A retry budget is largely silent on data handling in the sense that it does
not itself read, transform, or store request or response payloads, it
operates purely on the success or failure outcome of a call and a small
integer or fractional counter, so it introduces no new data-at-rest or
data-in-transit exposure of its own.

There is one narrow denial-of-service-adjacent consideration worth naming as
engineering judgement rather than as a sourced fact. Because the budget is
shared per destination across every caller of that destination, an attacker
or a misbehaving internal client that can force a high volume of failing
calls against a shared destination, for example by sending malformed requests
that always error, can deliberately or accidentally drain the shared retry
budget and thereby deny legitimate retries to every other, well-behaved
caller of the same destination, which is the same shared-scope starvation
failure mode described in dimension 11 but with an adversarial actor rather
than an accidental one behind it. Scoping budgets narrowly enough that a
single untrusted or low-trust caller cannot exhaust the allowance shared by
higher-trust callers, and excluding client-attributable, deterministic
errors, malformed input, failed authentication, from the accounting fed into
the budget as recommended in dimension 11's third failure mode, mitigates
this without requiring any change to the pattern's core mechanism.

No source consulted for this entry documents a data privacy implication
specific to the pattern beyond this availability-adjacent consideration.

## 18. References

1. Finagle project, "Retry Budgets", published 8 February 2016.
   https://finagle.github.io/blog/2016/02/08/retry-budgets/, verified
   2026-08-02.
2. Google gRPC, "Retries" guide, retry throttling section, `maxTokens` and
   `tokenRatio` parameters. https://grpc.io/docs/guides/retry/, verified
   2026-08-02.
3. Envoy Proxy, `envoy.config.cluster.v3.CircuitBreakers.Thresholds.
   RetryBudget` API reference, `budget_percent` default 20 percent,
   `min_retry_concurrency` default 3.
   https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/cluster/v3/circuit_breaker.proto,
   verified 2026-08-02.
4. AWS Well-Architected Framework, Reliability Pillar, REL05-BP03, "Control
   and limit retry calls", including the discussion of retry storms and
   citation of client-side retry token buckets in AWS SDKs since 2016.
   https://docs.aws.amazon.com/en_us/wellarchitected/2022-03-31/framework/rel_mitigate_interaction_failure_limit_retries.html,
   verified 2026-08-02.
5. Amazon Web Services Architecture Blog, Marc Brooker, "Exponential Backoff
   And Jitter", cited within the Well-Architected Framework guidance above as
   the source for the jitter recommendation this entry's dimension 13
   discusses alongside retry budgets.
   https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/,
   verified 2026-08-02.

## Code examples

Three implementations of the same token-bucket retry budget, following the
gRPC and Envoy shape described in dimension 8, a bounded bucket, a fractional
deposit on success, a whole-token withdrawal on retry, and permission gated at
half of the configured maximum. Each was executed locally against the toolchain
available on this machine and its output is reported below.

### TypeScript

```typescript
class RetryBudget {
  private tokens: number;
  private readonly maxTokens: number;
  private readonly tokenRatio: number;

  constructor(maxTokens = 10, tokenRatio = 0.1) {
    this.maxTokens = maxTokens;
    this.tokenRatio = tokenRatio;
    this.tokens = maxTokens;
  }

  canRetry(): boolean {
    return this.tokens > this.maxTokens / 2;
  }

  onRetryAttempt(): void {
    this.tokens = Math.max(0, this.tokens - 1);
  }

  onSuccess(): void {
    this.tokens = Math.min(this.maxTokens, this.tokens + this.tokenRatio);
  }

  fillLevel(): number {
    return this.tokens;
  }
}

function simulate(): void {
  const budget = new RetryBudget(10, 0.1);
  let permitted = 0;
  let denied = 0;

  for (let i = 0; i < 5; i++) {
    budget.onSuccess();
  }

  for (let i = 0; i < 20; i++) {
    if (budget.canRetry()) {
      permitted++;
      budget.onRetryAttempt();
    } else {
      denied++;
    }
  }

  console.log(`permitted=${permitted} denied=${denied} fillLevel=${budget.fillLevel().toFixed(2)}`);
  if (permitted !== 5 || denied !== 15) {
    throw new Error("unexpected simulation result");
  }
  console.log("assertion passed. budget denies once tokens fall to or below half of maxTokens");
}

simulate();
```

Executed with `npx tsc retry-budget.ts && node retry-budget.js`. Output.

```
permitted=5 denied=15 fillLevel=5.00
assertion passed. budget denies once tokens fall to or below half of maxTokens
```

### Python

```python
class RetryBudget:
    def __init__(self, max_tokens: float = 10.0, token_ratio: float = 0.1) -> None:
        self.max_tokens = max_tokens
        self.token_ratio = token_ratio
        self.tokens = max_tokens

    def can_retry(self) -> bool:
        return self.tokens > self.max_tokens / 2

    def on_retry_attempt(self) -> None:
        self.tokens = max(0.0, self.tokens - 1.0)

    def on_success(self) -> None:
        self.tokens = min(self.max_tokens, self.tokens + self.token_ratio)


def simulate() -> None:
    budget = RetryBudget(max_tokens=10.0, token_ratio=0.1)
    permitted = 0
    denied = 0

    for _ in range(5):
        budget.on_success()

    for _ in range(20):
        if budget.can_retry():
            permitted += 1
            budget.on_retry_attempt()
        else:
            denied += 1

    print(f"permitted={permitted} denied={denied} fill_level={budget.tokens:.2f}")
    assert permitted == 5 and denied == 15, "unexpected simulation result"
    print("assertion passed. budget denies once tokens fall to or below half of max_tokens")


if __name__ == "__main__":
    simulate()
```

Executed with `python3 retry_budget.py`. Output.

```
permitted=5 denied=15 fill_level=5.00
assertion passed. budget denies once tokens fall to or below half of max_tokens
```

### Go

```go
package main

import "fmt"

type RetryBudget struct {
	tokens     float64
	maxTokens  float64
	tokenRatio float64
}

func NewRetryBudget(maxTokens, tokenRatio float64) *RetryBudget {
	return &RetryBudget{tokens: maxTokens, maxTokens: maxTokens, tokenRatio: tokenRatio}
}

func (b *RetryBudget) CanRetry() bool {
	return b.tokens > b.maxTokens/2
}

func (b *RetryBudget) OnRetryAttempt() {
	b.tokens -= 1
	if b.tokens < 0 {
		b.tokens = 0
	}
}

func (b *RetryBudget) OnSuccess() {
	b.tokens += b.tokenRatio
	if b.tokens > b.maxTokens {
		b.tokens = b.maxTokens
	}
}

func main() {
	budget := NewRetryBudget(10, 0.1)
	permitted, denied := 0, 0

	for i := 0; i < 5; i++ {
		budget.OnSuccess()
	}

	for i := 0; i < 20; i++ {
		if budget.CanRetry() {
			permitted++
			budget.OnRetryAttempt()
		} else {
			denied++
		}
	}

	fmt.Printf("permitted=%d denied=%d fillLevel=%.2f\n", permitted, denied, budget.tokens)
	if permitted != 5 || denied != 15 {
		panic("unexpected simulation result")
	}
	fmt.Println("assertion passed. budget denies once tokens fall to or below half of maxTokens")
}
```

Executed with `go run retry_budget.go`. Output.

```
permitted=5 denied=15 fillLevel=5.00
assertion passed. budget denies once tokens fall to or below half of maxTokens
```

Java and Rust were not run for this entry despite being available in the
project toolchain, because the same deterministic token-bucket logic offers
no additional idiomatic variation in either language worth demonstrating
beyond the three shown, the pattern is a small piece of arithmetic state
rather than a language-feature-dependent structural pattern such as Visitor or
Iterator, so a fourth or fifth translation would not surface a genuinely new
implementation concern.
