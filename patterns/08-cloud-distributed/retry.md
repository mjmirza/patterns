---
name: Retry
slug: retry
family: 08-cloud-distributed
category: Resilience
aliases: [Retry with Backoff, Exponential Backoff, Requeue, Automatic Retry]
first_described: "Metcalfe and Boggs 1976 for binary exponential backoff, framed for distributed services by Nygard 2007 and the AWS Architecture Blog 2015"
maturity: canonical
related: [circuit-breaker, timeout, bulkhead, idempotent-receiver, rate-limiting, fallback, hedged-request, dead-letter-queue]
incompatible_with: []
verified: 2026-08-02
---

# Retry

## 1. Name, aliases, and lineage

The canonical name in the cloud and distributed catalogs is **Retry**. It is
almost never implemented bare, so the name usually arrives with a qualifier,
**Retry with Exponential Backoff**, **Retry with Jitter**, or in Twitter's
Finagle vocabulary **Requeue** for the transport-level flavour that sits below
application retries
([Finagle client guide](https://twitter.github.io/finagle/guide/Clients.html),
verified 2026-08-02).

The backoff half of the pattern predates distributed services by two decades.
Robert Metcalfe and David Boggs described the algorithm in "Ethernet.
Distributed Packet Switching for Local Computer Networks", *Communications of
the ACM* 19(7), July 1976, pages 395 to 404. Their controller, on a collision,
waited a random interval whose mean doubled after each failed attempt, which
they named **binary exponential backoff**
([ACM Digital Library record for the stability analysis of that
algorithm](https://dl.acm.org/doi/10.1145/44483.44488), verified 2026-08-02).
Every modern retry policy descends from that heuristic, moved up the stack from
a shared coaxial cable to a shared service.

The distributed-systems framing, retry as a deliberate stability tactic with a
cost, comes from Michael Nygard, *Release It!*, Pragmatic Bookshelf, 2007,
where Retry sits alongside Circuit Breaker, Timeout and Bulkhead in the
stability patterns chapter. Nygard's contribution was not the algorithm, it was
the insistence that a retry is load you chose to add to a system that has said
it is struggling.

The randomization half was settled empirically by Marc Brooker in "Exponential
Backoff And Jitter", AWS Architecture Blog, 4 March 2015. That post names four
concrete variants, compares them by simulation, and gives each a formula
([AWS Architecture Blog](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/),
verified 2026-08-02).

- **Exponential Backoff, no jitter.** `sleep = min(cap, base * 2^attempt)`.
- **Full Jitter.** `sleep = random(0, min(cap, base * 2^attempt))`.
- **Equal Jitter.** `sleep = t/2 + random(0, t/2)` where
  `t = min(cap, base * 2^attempt)`.
- **Decorrelated Jitter.** Like Full Jitter, except the upper bound of the draw
  grows from the previously drawn value rather than from the attempt number.

Brooker's measured conclusion is that Full Jitter completes the work with the
fewest total calls, Decorrelated Jitter finishes sooner in wall-clock terms at
the price of more calls, and Equal Jitter is the weakest of the three jittered
schemes (same post, verified 2026-08-02). Full Jitter is the variant most
production SDKs ship. The AWS SDK backoff formula is stated in the shared
configuration reference as `delay = random(0, 1) x min(20,000 ms, base_delay x
2^retry)`, which is Full Jitter with a 20 second cap
([AWS SDKs and Tools Reference Guide, retry behavior](https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html),
verified 2026-08-02).

The name is not contested, the scope is. Some teams use "retry" to mean any
re-execution including a duplicate sent before the first has failed. That is a
different pattern with a different cost model, see dimension 13.

## 2. Problem and context

A caller sends a request across a boundary it does not control. The request
fails. The failure is not a statement about the request, it is a statement
about the moment. A TCP connection reset by a load balancer draining a node, a
socket timeout while a garbage collection pause ran long, a 503 while an
autoscaler was mid-scale, a 429 while a neighbouring tenant burst. Send the
same bytes ten seconds later and it succeeds.

Without a retry, every one of these transient conditions becomes a user-visible
error, and availability collapses toward the product of the availability of
every hop. Four hops at 99.9 percent each is 99.6 percent end to end, roughly
three hours of failure a month that nobody had to accept.

The context that makes Retry the right answer has four parts, and all four have
to hold.

- **The failure is plausibly transient.** Re-sending has a real chance of a
  different outcome. A validation error will fail identically forever.
- **The operation is idempotent, or has been made idempotent.** See dimension 8.
  Retrying a non-idempotent write is not a resilience tactic, it is a data
  corruption tactic with a delay.
- **The caller has time budget left.** A retry spends latency the caller may not
  have. If the deadline is 200 ms and the timeout was 200 ms, there is no retry
  to schedule.
- **The dependency is not saturated.** This is the part that gets skipped.
  Retrying into an overloaded service adds exactly the load that keeps it
  overloaded.

The last point is why this entry is long. Retry is the easiest resilience
pattern to implement and one of the easiest to turn into an outage. Google's SRE
book documents the amplification directly and recommends that a failed request
be retried by one layer only, the layer immediately above the failing one,
because "if multiple layers retried, we'd have a combinatorial explosion"
([Google SRE Book, chapter 21, Handling Overload](https://sre.google/sre-book/handling-overload/),
verified 2026-08-02).

## 3. Forces

This dimension is engineering judgement about which pressure wins, informed by
the cited sources but not reducible to them.

- **Availability against load.** Favoured toward availability, at a directly
  measurable cost in load on the dependency. Every retry is an extra request
  sent to a system that has failed one.
- **Latency.** Sacrificed on the failure path. A three-attempt policy with a one
  second base delay can add several seconds of tail latency to a request that
  ends in failure anyway. Tail latency, not median, is where retries appear.
- **Correctness.** Sacrificed unless idempotency is established first. A retry
  after a timeout is indistinguishable, from the client, from a retry after a
  genuine rejection. The server may have committed the first attempt.
- **Coupling.** Mildly favoured. A retry lets the caller absorb a class of
  dependency behaviour without a code change on either side.
- **Operability.** Sacrificed unless instrumented. Retries hide failures from
  the error rate metric and move them into the latency metric, which is where a
  degradation goes unnoticed until it is an outage.
- **Cost.** Sacrificed. Retried requests are billed requests, billed compute,
  billed egress, and in a metered API they consume quota that the original
  request already consumed.
- **Cognitive load.** Sacrificed at the system level, favoured at the call site.
  One call site becomes trivial. Reasoning about the aggregate behaviour of ten
  thousand call sites under a partial outage becomes hard.
- **Recovery time.** This is the force people get backwards. Uncontrolled
  retries lengthen recovery, because the dependency cannot drain its queue while
  retry traffic keeps refilling it. AWS documents this as the reason the SDK
  retry quota exists, so that the client "fails fast instead of waiting through
  retries that are unlikely to succeed" and service disruptions "resolve faster
  by reducing retry traffic" (AWS SDKs and Tools Reference Guide, retry
  behavior, verified 2026-08-02).

A retry policy that sacrifices nothing has simply not been measured under
saturation.

## 4. Applicability and non-applicability

### Reach for Retry when

- The call crosses a process, network or availability-zone boundary and the
  failure taxonomy includes transient members.
- The operation is idempotent by method, `GET`, `PUT`, `DELETE`, per RFC 9110
  section 9.2.2, or has been made idempotent with a client-supplied key.
- A remaining time budget exists and is explicitly known at the call site.
- The failure mode is a connection reset, a connect timeout, a `5xx` without a
  throttling code, or a documented throttling response carrying `Retry-After`.
- The dependency publishes a retry contract. Both gRPC and Envoy make this
  explicit, gRPC through `retryableStatusCodes` in the service config
  ([gRPC proposal A6, client retries](https://github.com/grpc/proposal/blob/master/A6-client-retries.md),
  verified 2026-08-02) and Envoy through `retry-on` policies such as `5xx`,
  `gateway-error`, `reset`, `connect-failure`, `envoy-ratelimited`,
  `retriable-4xx` and `retriable-status-codes`
  ([Envoy router filter documentation](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/router_filter),
  verified 2026-08-02).

### Non-applicability. Do NOT reach for Retry when

- **The operation is a non-idempotent write with no idempotency key.** Payment
  capture, order submission, message publish without a producer sequence number.
  The correct move is to add the key first, then retry. This is a precondition,
  not a nicety.
- **The error is a client error that will not change.** HTTP 400, 401, 403, 404,
  409 in the general case, 422. AWS classifies `ValidationException`,
  `AccessDeniedException` and `ResourceNotFoundException` as non-retryable and
  returns them to the caller immediately (AWS SDKs and Tools Reference Guide,
  retry behavior, verified 2026-08-02). Retrying these burns quota and hides the
  real bug.
- **A layer below you already retried.** Stacked retries multiply. Pick one
  layer. Google's SRE book is explicit that the retry belongs at the layer
  immediately above the failure (chapter 21, verified 2026-08-02).
- **The caller has no deadline.** A retry loop with no bound on total elapsed
  time is an unbounded resource hold. It will exhaust a connection pool or a
  thread pool before it exhausts the dependency.
- **The dependency is in sustained overload.** Retrying is the mechanism that
  keeps it there. Shed load, open a circuit, or serve a fallback.
- **The failure is a poison message in a consumer loop.** Infinite redelivery of
  a message that will never process is not retry, it is a hot loop with network
  hops. Bound the attempts and route to a dead-letter queue.
- **The operation is expensive and the failure is late.** Retrying a 90 second
  batch job that fails at second 88 triples the cost for a small chance of a
  different outcome. Checkpoint instead.
- **You are inside a request that has passed its deadline.** Check the remaining
  budget before scheduling the sleep, not after.
- **Realtime media and interactive frames.** A late packet is worthless. Forward
  error correction or dropping the frame beats a retransmit that arrives after
  the moment has passed.

## 5. Structure

The participants, named by the role each plays rather than by a class name.

- **Caller.** Application code that wants an operation performed and does not
  want to know about attempt counting.
- **Retry Executor.** The component that owns the attempt loop. It invokes the
  operation, receives the outcome, consults the Classifier, consults the Budget,
  computes a delay from the Backoff Policy, sleeps, and repeats or gives up.
- **Operation.** A thunk representing one attempt. It must be re-invocable and
  must not carry per-attempt state such as an already-consumed request body
  stream.
- **Retry Classifier.** Maps an outcome to one of three verdicts. Succeed,
  retryable failure, terminal failure. This is the highest-value and most
  frequently wrong participant in the whole pattern.
- **Backoff Policy.** Given the attempt number, and optionally the previous
  delay, returns a duration. Full Jitter, Equal Jitter, Decorrelated Jitter, or
  a server-directed value taken from `Retry-After`.
- **Retry Budget.** A shared, process-wide or client-wide limiter that decides
  whether a retry is permitted at all, independent of whether this particular
  call has attempts left. Implemented as a token bucket or a ratio window.
- **Deadline.** The remaining time allowed for the whole logical operation,
  propagated from the caller. It bounds the loop from outside.
- **Idempotency Key Provider.** Generates one key per logical operation and
  keeps it stable across attempts, so the server can deduplicate.
- **Attempt Recorder.** The observability seam. Emits attempt count, outcome per
  attempt, delay, and terminal reason.

The relationship that matters is this. The Retry Executor consults Classifier,
Budget and Deadline as three independent veto points. Any one of them can stop
the loop. A design where the attempt count is the only stopping condition is the
design that produces retry storms.

## 6. Structure diagram

```
                          +-------------------+
      call(op, ctx) ----->|      Caller       |
                          +---------+---------+
                                    |
                                    v
     +------------------------------------------------------------+
     |                      Retry Executor                         |
     |                                                             |
     |   attempt = 0                                               |
     |   +-------------------------------------------------+       |
     |   |  invoke Operation  -------------------------->  |       |
     |   |  outcome                                        |       |
     |   +-------------------------------------------------+       |
     |            |             |              |                   |
     |            v             v              v                   |
     |   +----------------+ +---------+ +-------------+            |
     |   |   Classifier   | | Budget  | |  Deadline   |            |
     |   | ok / retry /   | | token   | | remaining   |            |
     |   | terminal       | | bucket  | | time left   |            |
     |   +----------------+ +---------+ +-------------+            |
     |            |             |              |                   |
     |            +------+------+------+-------+                   |
     |                   v                                         |
     |          +------------------+                               |
     |          |  Backoff Policy  |  full jitter or Retry-After   |
     |          +--------+---------+                               |
     |                   |  delay                                  |
     |                   v                                         |
     |             sleep, attempt++                                |
     +------------------------------------------------------------+
                                    |
                                    v
                          +-------------------+
                          | Attempt Recorder  |  metrics, traces
                          +-------------------+
                                    |
                                    v
                          +-------------------+
                          |    Dependency     |  dedupes on
                          |  remote service   |  Idempotency-Key
                          +-------------------+
```

## 7. Dynamics

Two runtime flows matter. The first is a single call that recovers on the second
attempt. The second is the aggregate behaviour that produces amplification.

```
Caller      Executor     Budget      Dependency
  |            |            |            |
  |--call----->|            |            |
  |            |--attempt 1------------->|
  |            |            |            |  connection reset
  |            |<-----------------------.|
  |            |--classify -> RETRYABLE  |
  |            |--take token->|          |
  |            |<--granted----|          |
  |            |--deadline check, 1800ms left
  |            |--backoff, random(0, 50ms) -> 31ms
  |            |   [sleep 31ms]          |
  |            |--attempt 2------------->|
  |            |            |            |  200 OK
  |            |<-----------------------.|
  |            |--return token->|        |
  |<--result---|            |            |
```

Now the failure flow, where the classifier says terminal or the budget says no.

```
Caller      Executor     Budget      Dependency
  |            |            |            |
  |--call----->|            |            |
  |            |--attempt 1------------->|
  |            |<--503 Retry-After 4-----|
  |            |--classify -> RETRYABLE  |
  |            |--take token->|          |
  |            |<--DEPLETED---|          |
  |            |  no retry, fail fast    |
  |<--error----|            |            |
```

The amplification dynamic, drawn across four tiers where each tier runs a
three-attempt policy. Read it as a tree, not a line.

```
  tier 0  edge         1 request
            |
  tier 1  gateway      3 requests      (3^1)
            |
  tier 2  service      9 requests      (3^2)
            |
  tier 3  service      27 requests     (3^3)
            |
  tier 4  datastore    81 requests     (3^4)

  arithmetic. 3 attempts per hop, 4 hops, 3 * 3 * 3 * 3 = 81
  one user request becomes 81 datastore requests during a partial
  outage. the datastore sees 81x its normal load at exactly the
  moment it is least able to serve it.
```

Two attempts per hop instead of three gives `2^4 = 16`, still a 16x multiplier.
The exponent is the number of retrying layers, so the only change that alters
the exponent is removing retry from intermediate layers. That arithmetic is the
reason behind the SRE book rule that one layer retries (chapter 21, verified
2026-08-02).

## 8. Implementation variants

### 8.1 Fixed delay

`sleep = c`. Simple, and wrong under load. Every client that failed at the same
instant retries at the same instant. This is the thundering herd. Acceptable
only inside a single process retrying a local resource.

### 8.2 Exponential backoff without jitter

`sleep = min(cap, base * 2^attempt)`. Spreads retries in time but not across
clients. A thousand clients that failed together still retry together, at 50 ms,
then 100 ms, then 200 ms. The herd is preserved, only stretched. Brooker's
simulations show this variant doing the most total work of the four (AWS
Architecture Blog, verified 2026-08-02).

### 8.3 Full jitter

`sleep = random(0, min(cap, base * 2^attempt))`. The default choice. It spreads
a thousand simultaneous failures uniformly across the whole backoff window
instead of stacking them at its edge. This is what AWS SDKs ship, with a 50 ms
base for transient errors, a 1000 ms base for throttling errors, and a 20 second
cap (AWS SDKs and Tools Reference Guide, retry behavior, verified 2026-08-02).
Envoy uses "a fully jittered exponential back-off algorithm for retries with a
default base interval of 25ms" and a default maximum of ten times that value
(Envoy router filter documentation, verified 2026-08-02).

### 8.4 Equal jitter

`sleep = t/2 + random(0, t/2)`. Guarantees a minimum wait, which is occasionally
what a protocol needs. Brooker measured it as the weakest jittered variant (AWS
Architecture Blog, verified 2026-08-02). Reach for it only when a hard minimum
delay is a requirement rather than a preference.

### 8.5 Decorrelated jitter

The upper bound for the next draw grows from the previously drawn value rather
than from the attempt index. It finishes faster in wall-clock terms and issues
more calls than Full Jitter (same post, verified 2026-08-02). Suitable when the
dependency is not the bottleneck and completion time is the objective.

### 8.6 Multiplicative jitter around a computed value

gRPC applies `random(0.8, 1.2)` as a multiplier to the computed backoff (gRPC
proposal A6, verified 2026-08-02). This is narrow-band jitter. It breaks exact
synchronization without giving up the shape of the backoff curve. Weaker
decorrelation than Full Jitter, easier to reason about inside a latency budget.

### 8.7 Server-directed backoff

When the server tells you when to come back, obey it. RFC 9110 section 10.2.3
defines `Retry-After` for that purpose, and section 15.6.4 defines 503 Service
Unavailable as the temporary-overload signal it accompanies
([RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#name-503-service-unavailable),
verified 2026-08-02). AWS services use a proprietary `x-amz-retry-after` header
in milliseconds, and the SDK clamps the server value between the computed
backoff and the computed backoff plus 5000 ms, applying no jitter of its own
because the service is expected to have jittered it (AWS SDKs and Tools
Reference Guide, retry behavior, verified 2026-08-02). That clamp is the detail
worth copying. A naked server-supplied delay is a denial-of-service vector when
the server is compromised or buggy.

### 8.8 Retry budgets, the modern remedy

Per-call attempt limits do not bound aggregate retry load, because the number of
calls is not bounded. A budget does. Three shipped shapes exist.

**Ratio window.** Google's client-side budget tracks the ratio of retries to
original requests over a sliding window and permits a retry only while that
ratio is below 10 percent. The SRE book reports that without it a datacenter
sees load rising to a little under 3x, and with the 10 percent ratio the same
scenario settles near 1.1x in the general case (Google SRE Book, chapter 21,
verified 2026-08-02).

**Token bucket.** gRPC keeps a per-server `token_count` initialized to
`maxTokens`. "Every failed RPC will decrement the `token_count` by 1", "Every
successful RPC will increment the `token_count` by `tokenRatio`", and retries
are disabled while `token_count` is at or below `maxTokens / 2`. `maxTokens` is
an integer in the range `(0, 1000]` and `tokenRatio` is a float greater than
zero (gRPC proposal A6, verified 2026-08-02).

The AWS SDK ships the same idea with asymmetric pricing. Budget capacity is 500
tokens, a transient retry costs 14 tokens, a throttling retry costs 5, a
successful retry refunds what that retry consumed, and a first-try success
refunds 1. The documented effect is that the quota begins to drain above roughly
22 percent sustained transient failures or roughly 32 percent throttling
failures (AWS SDKs and Tools Reference Guide, retry behavior, verified
2026-08-02). Transient retries cost nearly three times a throttling retry
because a wave of 500s usually means the whole service is unwell, whereas a 429
means the service is healthy and asking you to slow down.

**Concurrency budget.** Envoy's `RetryBudget` bounds concurrent retries as a
percentage of active plus pending requests. `budget_percent` defaults to 20 and
`min_retry_concurrency` defaults to 3, the minimum existing so that a client
with almost no traffic can still retry at all
([Envoy circuit breaker proto](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/cluster/v3/circuit_breaker.proto),
verified 2026-08-02). Finagle takes the hybrid. Its default `RetryBudget`
"allows for approximately 20% of the total requests to be immediately (no
backoff) retried on top of 10 retries per second", parameterized by `ttl`,
`minRetriesPerSec` and `percentCanRetry`, and the guide warns to share one
budget instance between the `RetryFilter` and the `RequeueFilter` "to prevent
retry storms" (Finagle client guide, verified 2026-08-02).

The shape to copy is a minimum plus a percentage. A pure percentage starves a
low-traffic client, a pure fixed rate does not scale with a busy one.

### 8.9 Adaptive client-side rate limiting

Beyond retries, adaptive mode lets the client throttle its own originating
requests. The AWS SDK documents adaptive mode as standard mode plus a
client-side rate limiter that can delay or block the initial request, not only
the retries, once throttling is detected, scoped per client instance across all
operations. The same documentation warns against it for multi-resource or
multi-tenant clients, because throttling on one resource slows everything that
client sends, and states plainly that adaptive mode "is not recommended as a
general default" (AWS SDKs and Tools Reference Guide, retry behavior, verified
2026-08-02). That caveat is worth repeating in any internal design that copies
the idea.

### 8.10 Idempotency, the precondition for retrying a write

A retry after a timeout cannot distinguish "the server never saw it" from "the
server committed it and the response was lost". Both look identical to the
client. So a write is retryable only when the server can recognise the second
arrival as the same logical operation.

RFC 9110 section 9.2.2 defines idempotent as a method whose "intended effect on
the server of multiple identical requests with that method is the same as the
effect for a single such request", and names GET, HEAD, PUT, DELETE, OPTIONS and
TRACE as idempotent (RFC 9110, verified 2026-08-02). POST is not, which is why
the key mechanism exists.

Stripe's implementation is the reference. The client sends an `Idempotency-Key`
header, up to 255 characters, generated as a V4 UUID or an equivalent random
string. Stripe saves the resulting status code and body of the first request and
replays the identical result for a repeat of the same key, including a 500. Keys
are pruned once they are at least 24 hours old, so a later reuse of the same key
creates a new request. Stripe also compares the parameters of the repeat against
the original and errors on a mismatch, so an accidentally reused key cannot
silently change an operation
([Stripe API reference, idempotent requests](https://docs.stripe.com/api/idempotent_requests),
verified 2026-08-02).

Three implementation notes follow from that design. The key must be generated
once per logical operation and held constant across attempts, generating it
inside the retry loop defeats the entire mechanism. The dedupe record must be
written in the same transaction as the effect, or a crash between the two
reopens the double-write. And the retention window is part of the contract,
Stripe's 24 hours means a client whose retry policy could span longer than a day
cannot rely on it.

### 8.11 Which failures are retryable

The classifier is where most retry bugs live. A workable default taxonomy,
combining the cited contracts.

| Signal | Verdict | Source or reasoning |
|---|---|---|
| Connect timeout, connection reset, DNS failure | Retry | AWS classes I/O failures as transient, 50 ms base |
| Read timeout on an idempotent request | Retry | RFC 9110 section 2.4.3 allows automatic retry on an underlying connection failure |
| Read timeout on a non-idempotent request | Retry only with an idempotency key | The server may have committed |
| HTTP 408 Request Timeout | Retry | The server reports the request timed out |
| HTTP 429 Too Many Requests | Retry, honour `Retry-After`, longer base | AWS uses a 1000 ms base for throttling |
| HTTP 500 | Retry with care | Often terminal in practice, may be a deterministic server bug |
| HTTP 502, 503, 504 | Retry | AWS treats unclassified 5xx as transient |
| HTTP 501 Not Implemented | Never | Deterministic |
| HTTP 400, 401, 403, 404, 405, 409, 422 | Never | AWS returns `ValidationException`, `AccessDeniedException`, `ResourceNotFoundException` immediately |
| gRPC UNAVAILABLE, RESOURCE_EXHAUSTED | Retry | Common members of `retryableStatusCodes` |
| gRPC INVALID_ARGUMENT, NOT_FOUND, PERMISSION_DENIED, UNAUTHENTICATED | Never | Deterministic |
| gRPC DEADLINE_EXCEEDED | Do not retry blindly | The deadline is usually the caller's own, spent |
| Serialization failure, deadlock victim in a database | Retry the transaction | The database is asking you to |
| Constraint violation, unique key conflict | Never | Deterministic, and frequently the sign that the previous attempt succeeded |

The most damaging misclassification is treating a bare HTTP 500 from an
application as transient. A null dereference in a handler returns 500 forever,
and a retry policy converts one bug into three requests per user action. When
the dependency distinguishes its errors, use its taxonomy rather than the status
code alone. AWS makes this explicit. The SDK matches on error code first and
falls back to the HTTP status code, so an HTTP 5xx carrying a throttling error
code is treated as throttling rather than transient (AWS SDKs and Tools
Reference Guide, retry behavior, verified 2026-08-02).

### 8.12 Language-idiomatic shapes

In Go the executor is a loop with `select` on `ctx.Done()`, because the deadline
is carried by `context.Context` and needs no separate participant. In Rust the
loop is usually a `Future` combinator and the classifier is exhaustive pattern
matching over an error enum, which makes terminal cases hard to forget. In
TypeScript the executor is an async function and the deadline arrives as an
`AbortSignal`. In Python the natural shape is a decorator, which is convenient
and hides the deadline, so the deadline has to be passed explicitly or it will
be forgotten.

## 9. Known production uses

- **AWS SDKs and the AWS CLI.** Standard mode is the default across SDKs, with a
  default of 3 max attempts, one initial request plus two retries, and DynamoDB
  and DynamoDB Streams defaulting to 4 attempts with a 25 ms transient base
  instead of 50 ms. Full jitter, a 20 second cap, a 500 token retry quota, and a
  separate adaptive mode with a client-side rate limiter (AWS SDKs and Tools
  Reference Guide, retry behavior, verified 2026-08-02).
- **gRPC.** Retry policy and retry throttling are part of the service config, so
  the server controls the client's retry behaviour. `maxAttempts` must be two or
  greater, backoff is exponential with a `random(0.8, 1.2)` multiplier, and the
  per-server token bucket disables retries at half capacity (gRPC proposal A6,
  verified 2026-08-02).
- **Envoy Proxy.** Fully jittered exponential backoff, a 25 ms default base
  interval, a maximum of ten times the base, a documented `retry-on` policy
  vocabulary, an `x-envoy-max-retries` header override whose value "takes
  precedence over the number of retries set in either retry policy", and a
  `RetryBudget` circuit breaker with `budget_percent` 20 and
  `min_retry_concurrency` 3 (Envoy router filter documentation and circuit
  breaker proto, both verified 2026-08-02).
- **Google production services.** Three attempts per request, a per-client
  retry-to-request ratio capped at 10 percent, and retry at one layer only. The
  SRE book reports the measured effect as a reduction from a little under 3x
  load to about 1.1x (Google SRE Book, chapter 21, verified 2026-08-02).
- **Stripe API.** `Idempotency-Key` on all POST requests, a saved status code
  and body replayed on a repeated key, a 24 hour key lifetime, and a parameter
  comparison that rejects a mismatched reuse (Stripe API reference, verified
  2026-08-02).
- **Twitter Finagle.** `RetryFilter` for application retries and `RequeueFilter`
  inserted into every client stack by default for transport failures, both
  sharing one `RetryBudget` whose default permits roughly 20 percent of total
  requests plus 10 retries per second (Finagle client guide, verified
  2026-08-02).

## 10. Consequences

The magnitude of each item below is engineering judgement. The direction is not.

### Positive

- Transient failures stop reaching the user. That is the whole point, and it
  works, which is why the pattern is everywhere.
- End to end availability rises above the product of per-hop availabilities, so
  a chain of hops stops multiplying its own weakness.
- The dependency gains room to perform routine disruptive operations, a rolling
  deploy, a leader election, a node drain, without every one of them becoming a
  customer-visible error.
- With a budget in place, the client degrades in a known way under a dependency
  outage rather than degrading at random.
- A single, well-tested retry executor turns a scattered per-call-site concern
  into one auditable policy.

### Negative

- **Load multiplication under exactly the wrong conditions.** The pattern adds
  the most load at the moment the dependency has the least capacity. Dimension 7
  gives the 81x arithmetic.
- **Tail latency inflation.** A request that eventually fails now fails slowly.
  p99 and p999 absorb the whole backoff sum. AWS documents an average of about
  1500 ms of added latency for a throttling error with the default three
  attempts (AWS SDKs and Tools Reference Guide, retry behavior, verified
  2026-08-02).
- **Duplicate side effects** wherever idempotency was assumed rather than
  implemented. Double charges, duplicate emails, doubled counters.
- **Resource occupation.** Each in-flight retry holds a connection, a thread or
  a task slot for the duration of the backoff. A retry loop is a slow resource
  leak while the dependency is down.
- **Metric distortion.** The error rate looks healthy because the retry
  succeeded. The degradation appears only in latency and only in the tail, so it
  is found late.
- **Cost.** Retried calls are billed calls. Under a partial outage the bill for
  the dependency can rise while its usefulness falls.
- **False confidence.** A retry around a deterministic bug converts a loud,
  fast, obvious failure into a quiet, slow, intermittent one.

## 11. Failure modes and misuse

Symptoms below are drawn from operating systems that lean on retry. They are
practice, not sourced claims, except where a source is named.

**Retry storm from stacked layers.**
*Symptom.* Dependency request rate rises by an order of magnitude within seconds
of a partial failure, its latency climbs, and the rate keeps climbing after you
scale it up. Each new capacity increment is absorbed instantly.
*Cause.* Several tiers each retry the same logical operation, multiplying as
`attempts^layers`.
*Fix.* Retry at one layer only, the layer immediately above the failure (Google
SRE Book, chapter 21, verified 2026-08-02). Turn off retries in intermediate
proxies, or set their max attempts to 1 and let the edge own the policy.

**Thundering herd on recovery.**
*Symptom.* The dependency recovers, serves traffic for a few hundred
milliseconds, and collapses again. The cycle repeats on a period equal to the
backoff interval.
*Cause.* No jitter, or jitter applied only as a narrow multiplier, so every
client that failed together retries together.
*Fix.* Full jitter, `random(0, min(cap, base * 2^attempt))` (AWS Architecture
Blog, verified 2026-08-02).

**Duplicate writes after timeout.**
*Symptom.* Support tickets about double charges or duplicate records, with
timestamps a few hundred milliseconds apart, concentrated during a past latency
spike.
*Cause.* A read timeout was classified as retryable on a non-idempotent POST.
The server committed the first attempt and the response was lost.
*Fix.* A stable `Idempotency-Key` per logical operation, with the dedupe record
written in the same transaction as the effect (Stripe API reference, verified
2026-08-02).

**Idempotency key regenerated inside the loop.**
*Symptom.* Duplicates persist after idempotency was supposedly added.
*Cause.* The key is generated where the request is built, and the request is
rebuilt on each attempt.
*Fix.* Generate the key once, outside the executor, and pass it in. Assert in a
test that two attempts of one logical call carry the identical key.

**Retrying a deterministic failure.**
*Symptom.* A stable 3x on error-path traffic to one endpoint, and every retry
ends in the identical error message.
*Cause.* A bare 500 or a generic exception type classified as transient.
*Fix.* Classify on the dependency's error code before the HTTP status, and
default to terminal for anything not on an explicit retryable list (AWS SDKs and
Tools Reference Guide, retry behavior, verified 2026-08-02).

**Deadline blown by backoff.**
*Symptom.* An upstream caller times out at exactly its own deadline while the
downstream is still sleeping between attempts. Cancelled requests hold resources
until the sleep ends.
*Cause.* The loop checks attempt count but not remaining time.
*Fix.* Check the remaining budget before scheduling each sleep and abandon when
the sleep would exceed it. In Go this is a `select` on `ctx.Done()`, in
TypeScript an `AbortSignal` passed into the delay.

**Budget exhausted by a healthy client.**
*Symptom.* A low-traffic client cannot retry at all, even for a single genuinely
transient failure.
*Cause.* A pure percentage budget with no minimum. Twenty percent of three
requests per minute is nothing.
*Fix.* A minimum plus a percentage. Envoy's `min_retry_concurrency` default of 3
and Finagle's `minRetriesPerSec` of 10 are the two shipped examples (Envoy
circuit breaker proto and Finagle client guide, both verified 2026-08-02).

**Poison message replay.**
*Symptom.* A consumer's CPU pinned, throughput near zero, and one message ID
repeating in the logs thousands of times a minute.
*Cause.* An unbounded redelivery loop with no attempt limit and no dead-letter
route.
*Fix.* Bound the attempts, then move the message aside so the queue can drain.

**Non-replayable request body.**
*Symptom.* The first attempt fails and every retry fails immediately with an
empty body, a zero content length, or a stream-already-consumed error.
*Cause.* The operation closure captured a one-shot stream or a consumed
iterator.
*Fix.* Buffer the body, or rebuild the request from an immutable description on
each attempt.

**Retry inside a held lock or transaction.**
*Symptom.* Lock wait timeouts and connection pool exhaustion in a component that
looks otherwise idle.
*Cause.* The backoff sleep happens while a database transaction or a mutex is
held.
*Fix.* Release first, retry the whole unit of work from outside.

**Circuit breaker defeated by the retry.**
*Symptom.* The breaker opens and closes rapidly, and the dependency never gets a
quiet period.
*Cause.* The retry sits outside the breaker, so each retried attempt becomes a
new probe that keeps the breaker oscillating.
*Fix.* Put the breaker outside the retry, so an open circuit fails all attempts
immediately, and let the breaker own the half-open probe.

## 12. Trade-off matrix

Named alternatives, compared across the forces of dimension 3. The scoring is
judgement, the mechanism descriptions are sourced above.

| Force | Retry with jitter and budget | Retry, naive fixed delay | Circuit Breaker alone | Hedged Request | Fallback or degraded response | Queue and process later |
|---|---|---|---|---|---|---|
| Transient failure recovery | High | Medium | None, it only stops calling | High, also cuts tail latency | None, it hides the failure | High, when delay is acceptable |
| Load added to a sick dependency | Bounded by budget | Unbounded, multiplies | Reduced, actively sheds | Increased even when healthy | None | None on the sync path |
| Added tail latency | Moderate, capped | High and variable | Low, fails fast | Reduced | Very low | Not applicable, async |
| Correctness risk | Needs idempotency | Needs idempotency | None | Needs idempotency, always duplicates | Stale data risk | Ordering and duplicate risk |
| Cost | Extra billed calls | More extra calls | Fewer calls | Highest, duplicates every slow call | Lowest | Storage and consumer cost |
| Operability | Good when instrumented | Poor, hides degradation | Good, state is observable | Moderate, needs cancellation | Good | Good, queue depth is a clean signal |
| Recovery time of the dependency | Shortened by the budget | Lengthened | Shortened | Lengthened | Unaffected | Shortened |
| Cognitive load | Moderate, several knobs | Low | Low | High, cancellation semantics | Low | High, a whole second path |

Read the matrix as composition rather than selection. Retry with a budget,
wrapped by a circuit breaker, with a fallback for the terminal case, is the
standard production stack. Hedging replaces retry only for read-mostly,
latency-sensitive, genuinely idempotent calls where the cost of a duplicate is
near zero.

## 13. Related and incompatible patterns

- **Timeout.** A precondition, not a companion. A retry over a call with no
  timeout is a retry that never fires, because the first attempt hangs forever.
  Set the per-attempt timeout below the total deadline divided by the maximum
  attempts, or the loop cannot finish inside the budget.
- **Circuit Breaker.** The natural outer wrapper. Retry handles the failure of
  one call, the breaker handles the failure of the dependency. Nesting order
  matters and is the subject of a common bug, see dimension 11.
- **Bulkhead.** Bounds the resources the retry loop can occupy while it sleeps.
  Without it, a slow dependency plus retries exhausts a shared pool and takes
  unrelated traffic with it.
- **Rate Limiting and Load Shedding.** The server-side counterpart. A retry
  budget is client-side self-restraint, load shedding is the server enforcing
  the same restraint when clients do not.
- **Idempotent Receiver.** The precondition for retrying a write. Retry without
  it is unsafe for anything with a side effect.
- **Hedged Request.** A sibling, not a variant. Retry sends attempt two after
  attempt one failed. Hedging sends attempt two after attempt one is merely
  slow, and cancels the loser. Hedging cuts tail latency and adds load even when
  everything is healthy.
- **Dead Letter Queue.** The terminal destination when the attempt limit is
  reached in a message consumer.
- **Saga and Compensating Transaction.** Where the operation genuinely cannot be
  made idempotent, compensation replaces retry as the recovery mechanism.
- **Exponential Backoff as a standalone entry.** Many catalogs list backoff
  separately. This entry treats it as the delay policy inside retry, because
  bare backoff with no attempt loop has no meaning.

Nothing in this list is strictly incompatible with retry. The genuine conflict
is with **retry at another layer**. Two retrying layers in one call path is not
a composition, it is a multiplication, and the frontmatter records no
incompatibility only because the conflict is with an instance of the same
pattern rather than with a different pattern.

## 14. Refactoring path in and out

### Introducing retry into code that has none

1. **Add a timeout first.** A call with no bounded duration cannot be retried.
   This step alone often removes the hang that motivated the change.
2. **Propagate a deadline.** Give the logical operation a total time budget and
   pass it down. In Go this is `context.WithTimeout`, in TypeScript an
   `AbortSignal`, in Java a deadline parameter.
3. **Write the classifier before the loop.** Enumerate the failures the
   dependency actually produces, from its own documentation, and mark each
   retryable or terminal. Default the unknown ones to terminal.
4. **Establish idempotency for every write in scope.** Add the key, add the
   server-side dedupe, prove it with a test that sends the same key twice. Do
   not proceed to step 5 for writes until this is done.
5. **Introduce the executor at one layer.** Extract the call into a thunk and
   wrap it. Start with two attempts and full jitter.
6. **Remove retries from every other layer in the path.** This is the step
   people skip, and skipping it is what produces the 81x from dimension 7.
7. **Add the budget.** A token bucket or ratio window shared per dependency, per
   process. Without this, step 5 is unbounded in aggregate.
8. **Instrument before you tune.** Attempt histogram, retry ratio, budget
   depletion, terminal reason. See dimension 16.
9. **Load-test the failure path.** Not the happy path. Fail the dependency at 50
   percent and confirm the multiplier stays where the budget says it should.

### Removing retry when it stops earning its place

1. **Measure the retry success rate.** The fraction of retried calls that
   eventually succeed. When that number is near zero, the retries are pure cost
   and every one of them is a deterministic failure being repeated.
2. **Check whether the dependency became optional on the synchronous path.**
   When the caller can enqueue the work, the queue replaces the retry entirely.
3. **Reduce max attempts to 1 before deleting the code.** This is reversible in
   a config change and observable in one deploy.
4. **Watch error rate and p99 for a full traffic cycle.** Errors that were
   previously absorbed will now appear. That number is what the retry was
   hiding, and it is the number the decision should be made on.
5. **Delete the executor last.** Keep the classifier, it is useful on its own
   for deciding what to log at which severity.

Related named refactorings. Extracting the call into a thunk is Extract Method
applied to a call site, and moving the timeout and deadline into a parameter
object is Introduce Parameter Object.

## 15. Testing and verification

This dimension is practice rather than sourced fact.

**What the pattern makes easy to test.** The classifier is a pure function from
an error to a verdict, and deserves a table-driven test with one row per failure
the dependency can produce, including the ones you decided are terminal. The
backoff policy is also pure once the random source is injected, so a pinned
generator makes the delay sequence deterministic and assertable.

**What the pattern makes harder to test.** Timing. A test that actually sleeps
through a 20 second cap is a test nobody runs. Inject the clock and the sleep
function, or use the fake timer facility of the test framework, so the executor
can be driven through a full backoff sequence in microseconds.

**Test doubles and techniques.**

- A **scripted stub** dependency returning a fixed sequence of outcomes,
  `[reset, reset, ok]`, to assert the executor stops at the right attempt.
- A **counting spy** to assert the exact number of invocations. The most
  valuable single assertion in the whole suite is that a terminal error produced
  exactly one invocation.
- A **pinned random source** to make full jitter reproducible.
- A **virtual clock** so the deadline check can be exercised without waiting.
- A **duplicate-detection assertion** on the idempotency key. Two attempts, one
  key. Assert equality, not merely presence.
- **Property-based tests** for the delay policy. The invariants are that the
  delay is never negative, never exceeds the cap, and that the deadline check
  never permits a sleep past the remaining budget. Those hold for every attempt
  index and every random draw, which is exactly the shape a property test wants.
- **Fault injection at the integration tier.** A proxy that resets a configured
  percentage of connections, so the aggregate retry rate can be measured against
  the budget under real concurrency.

**The test that catches the expensive bug.** Assert the amplification factor.
Run N logical calls against a dependency that fails every attempt, and assert
the observed dependency call count is at most `N * maxAttempts` and, once the
budget engages, well below it. A regression that reintroduces a second retrying
layer appears here as a multiplied count and nowhere else.

## 16. Observability signals

Practice, not sourced.

**Emit per attempt, not per call.** The attempt is the unit of load on the
dependency, and a call-level metric hides everything worth knowing.

| Signal | Type | What it tells you |
|---|---|---|
| `attempts_total{dependency, outcome, attempt_index}` | counter | The shape of the retry distribution |
| `retry_ratio`, retries over original requests | gauge | The amplification factor, compare against the budget policy |
| `retry_budget_tokens` | gauge | Headroom before the client stops retrying |
| `retry_budget_denied_total` | counter | Retries the budget refused, the fail-fast signal |
| `terminal_reason{reason}` | counter | Which of the veto points ended the loop |
| `backoff_sleep_seconds` | histogram | Latency the pattern itself added |
| `call_duration_seconds{attempts}` | histogram | Tail latency split by attempt count |
| `idempotency_key_replays_total` | counter | Server-side duplicate detections, proof the key works |

**Tracing.** One span per attempt, children of one logical-operation span,
carrying `retry.attempt`, `retry.delay_ms` and `retry.reason`. A trace with a
single span per call makes retries invisible in exactly the incident where you
need to see them. The idempotency key belongs on the span as an attribute so a
duplicate can be traced from client to server.

**A healthy instance on a dashboard.** Retry ratio flat and low, single digit
percent. Attempt histogram with the overwhelming mass at attempt 1. Budget
tokens at capacity with no visible movement. Terminal reasons mostly success.
The p99 of call duration close to the p99 of a single attempt.

**A failing instance.** Retry ratio climbing toward the budget limit and
flattening there, which means the budget is doing its job. Attempt histogram
growing a bar at the maximum attempt index. Budget tokens sawtoothing or pinned
near zero, with `retry_budget_denied_total` rising. Terminal reasons shifting to
attempts-exhausted or budget-denied. Call duration p99 stepping up by roughly
the sum of the backoff series while the error rate stays deceptively flat, which
is the signature of a degradation being masked.

**The alert worth having.** Alert on the retry ratio crossing the budget
threshold, not on the error rate. The ratio moves first, because retries succeed
for a while before they stop succeeding.

## 17. Security and privacy implications

Analytical, not sourced, except where a source is named.

**Amplification as an attack surface.** A retry policy is a request multiplier
an attacker can aim. An endpoint that fails in a retryable way under a crafted
input lets one attacker request become `maxAttempts` requests at every retrying
tier. Where the dependency is metered or billed per call, the multiplier is a
direct economic denial-of-service. The retry budget is the mitigation, and it is
the reason a budget belongs in the threat model rather than only in the
reliability design.

**Server-controlled sleep.** Honouring `Retry-After` hands a remote party
control of how long your thread waits. A hostile or misconfigured dependency can
return an enormous value and park your workers. The AWS SDK clamp, a server
value bounded between the computed backoff and the computed backoff plus 5000
ms, is the right shape to copy (AWS SDKs and Tools Reference Guide, retry
behavior, verified 2026-08-02). Always cap a server-supplied delay against a
local maximum.

**Credential and quota consumption.** Every retry consumes rate limit against
the caller's identity. Retrying a 401 or 403 is worse than useless, it can trip
account lockout or a brute-force detector and turn a configuration mistake into
an authentication outage. Classify authentication and authorization failures as
terminal without exception.

**Idempotency keys are identifiers.** A key derived from a natural identifier,
an email address, a customer reference, an order number, leaks that value into
logs, traces and third-party systems, and makes keys guessable by a party who
can enumerate the natural key. Stripe's documentation states plainly that keys
should be V4 UUIDs or random strings and warns against using email addresses or
personal identifiers (Stripe API reference, verified 2026-08-02). A guessable
key is also a correctness hazard, because a collision suppresses a legitimate
operation.

**Replay semantics on the server.** A dedupe store that replays the original
response must apply the current authorization check, not the original one. A
naive implementation that returns a cached body on key match will serve a
previous caller's response to whoever presents the key. Scope the key to the
authenticated principal.

**Log volume as a cost and a side channel.** Retry loops multiply log lines at
exactly the moment log volume is already high. Log the terminal outcome at error
severity and the intermediate attempts at debug, or an incident becomes an
ingestion bill.

**Where the pattern is silent.** Retry has no direct implication for encryption,
key management or data residency. It does not create a new data flow, it repeats
an existing one, so the privacy posture of a retried call is the privacy posture
of the call. Saying otherwise would be inventing a concern.

## Code

### TypeScript

Full jitter, an explicit classifier, an abort-aware delay, and an idempotency
key generated once outside the loop. Type-checked with `npx tsc --strict`.

```typescript
export type Verdict = "ok" | "retry" | "terminal";

export interface Policy {
  maxAttempts: number;
  baseMs: number;
  capMs: number;
  deadlineMs: number;
}

export class RetryError extends Error {
  constructor(readonly reason: string, readonly attempts: number) {
    super(`${reason} after ${attempts} attempt(s)`);
  }
}

export function classifyHttp(status: number): Verdict {
  if (status >= 200 && status < 300) return "ok";
  if (status === 408 || status === 429) return "retry";
  if (status === 501) return "terminal";
  if (status >= 500) return "retry";
  return "terminal";
}

// Full jitter. random(0, min(cap, base * 2^attempt)).
export function fullJitter(attempt: number, p: Policy, rnd: () => number): number {
  const bound = Math.min(p.capMs, p.baseMs * Math.pow(2, attempt));
  return Math.trunc(rnd() * bound);
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal && signal.aborted) return reject(new RetryError("aborted", 0));
    const t = setTimeout(resolve, ms);
    if (signal) {
      signal.addEventListener("abort", () => {
        clearTimeout(t);
        reject(new RetryError("aborted", 0));
      }, { once: true });
    }
  });
}

export interface Budget {
  take(): boolean;
  refund(): void;
}

export function tokenBudget(capacity: number, costPerRetry: number): Budget {
  let tokens = capacity;
  return {
    take() {
      if (tokens < costPerRetry) return false;
      tokens -= costPerRetry;
      return true;
    },
    refund() {
      tokens = Math.min(capacity, tokens + costPerRetry);
    },
  };
}

export async function retry<T>(
  op: (attempt: number, key: string) => Promise<T>,
  classify: (e: unknown) => Verdict,
  p: Policy,
  budget: Budget,
  now: () => number = Date.now,
  rnd: () => number = Math.random,
  signal?: AbortSignal,
): Promise<T> {
  const key = newKey(rnd);
  const start = now();
  let attempt = 0;

  for (;;) {
    try {
      const value = await op(attempt, key);
      if (attempt > 0) budget.refund();
      return value;
    } catch (err) {
      if (classify(err) === "terminal") throw err;
      if (attempt + 1 >= p.maxAttempts) {
        throw new RetryError("attempts_exhausted", attempt + 1);
      }
      if (!budget.take()) throw new RetryError("budget_denied", attempt + 1);

      const delay = fullJitter(attempt, p, rnd);
      if (now() - start + delay >= p.deadlineMs) {
        throw new RetryError("deadline_exceeded", attempt + 1);
      }
      await sleep(delay, signal);
      attempt += 1;
    }
  }
}

function newKey(rnd: () => number): string {
  const hex = "0123456789abcdef";
  let out = "";
  for (let i = 0; i < 32; i++) out += hex[Math.trunc(rnd() * 16)];
  return out;
}
```

### Python

A token bucket retry budget with the AWS asymmetric costs, a classifier that
distinguishes throttling from transient, and a deadline that bounds the loop.
Run with `python3`.

```python
import random
import time
from dataclasses import dataclass

TRANSIENT_COST = 14
THROTTLE_COST = 5
CAPACITY = 500


class Terminal(Exception):
    pass


class Throttled(Exception):
    pass


class Transient(Exception):
    pass


class RetryGaveUp(Exception):
    def __init__(self, reason, attempts):
        super().__init__("%s after %d attempt(s)" % (reason, attempts))
        self.reason = reason
        self.attempts = attempts


class Budget:
    def __init__(self, capacity=CAPACITY):
        self.capacity = capacity
        self.tokens = capacity

    def take(self, cost):
        if self.tokens < cost:
            return False
        self.tokens -= cost
        return True

    def refund(self, cost):
        self.tokens = min(self.capacity, self.tokens + cost)


@dataclass
class Policy:
    max_attempts: int = 3
    transient_base_ms: int = 50
    throttle_base_ms: int = 1000
    cap_ms: int = 20000
    deadline_ms: int = 30000


def classify(err):
    if isinstance(err, Throttled):
        return "throttle"
    if isinstance(err, Transient):
        return "transient"
    return "terminal"


def full_jitter(attempt, base_ms, cap_ms, rnd):
    bound = min(cap_ms, base_ms * (2 ** attempt))
    return rnd.random() * bound


def call_with_retry(op, policy, budget, rnd=None, clock=time.monotonic,
                    sleep=time.sleep):
    rnd = rnd or random.Random()
    key = "%032x" % rnd.getrandbits(128)
    start = clock()
    attempt = 0
    cost = 0

    while True:
        try:
            value = op(attempt, key)
            if attempt > 0:
                budget.refund(cost)
            return value
        except Exception as err:
            verdict = classify(err)
            if verdict == "terminal":
                raise
            if attempt + 1 >= policy.max_attempts:
                raise RetryGaveUp("attempts_exhausted", attempt + 1) from err

            cost = THROTTLE_COST if verdict == "throttle" else TRANSIENT_COST
            if not budget.take(cost):
                raise RetryGaveUp("budget_denied", attempt + 1) from err

            base = (policy.throttle_base_ms if verdict == "throttle"
                    else policy.transient_base_ms)
            delay_ms = full_jitter(attempt, base, policy.cap_ms, rnd)
            elapsed_ms = (clock() - start) * 1000
            if elapsed_ms + delay_ms >= policy.deadline_ms:
                raise RetryGaveUp("deadline_exceeded", attempt + 1) from err

            sleep(delay_ms / 1000.0)
            attempt += 1


if __name__ == "__main__":
    outcomes = [Transient("reset"), Transient("reset"), "ok"]
    calls = {"n": 0}

    def flaky(attempt, key):
        calls["n"] += 1
        item = outcomes[attempt]
        if isinstance(item, Exception):
            raise item
        return "%s key=%s" % (item, key[:8])

    b = Budget()
    print(call_with_retry(flaky, Policy(), b, rnd=random.Random(7),
                          sleep=lambda _s: None))
    print("dependency calls", calls["n"], "tokens", b.tokens)

    def broken(attempt, key):
        raise Terminal("validation")

    try:
        call_with_retry(broken, Policy(), Budget(), sleep=lambda _s: None)
    except Terminal:
        print("terminal error, one attempt only")
```

### Go

The deadline lives in the context, which is the idiomatic shape. Built and run
with `go run`.

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"math"
	"math/rand"
	"time"
)

type Verdict int

const (
	Ok Verdict = iota
	Retryable
	Terminal
)

type Policy struct {
	MaxAttempts int
	Base        time.Duration
	Cap         time.Duration
}

type GaveUp struct {
	Reason   string
	Attempts int
}

func (g *GaveUp) Error() string {
	return fmt.Sprintf("%s after %d attempt(s)", g.Reason, g.Attempts)
}

type Budget struct {
	tokens, capacity, cost int
}

func NewBudget(capacity, cost int) *Budget {
	return &Budget{tokens: capacity, capacity: capacity, cost: cost}
}

func (b *Budget) Take() bool {
	if b.tokens < b.cost {
		return false
	}
	b.tokens -= b.cost
	return true
}

func (b *Budget) Refund() {
	if b.tokens+b.cost <= b.capacity {
		b.tokens += b.cost
	}
}

func fullJitter(attempt int, p Policy, r *rand.Rand) time.Duration {
	bound := float64(p.Base) * math.Pow(2, float64(attempt))
	if bound > float64(p.Cap) {
		bound = float64(p.Cap)
	}
	return time.Duration(r.Float64() * bound)
}

func Do[T any](
	ctx context.Context,
	op func(ctx context.Context, attempt int, key string) (T, error),
	classify func(error) Verdict,
	p Policy,
	b *Budget,
	r *rand.Rand,
) (T, error) {
	var zero T
	key := fmt.Sprintf("%016x", r.Uint64())

	for attempt := 0; ; attempt++ {
		value, err := op(ctx, attempt, key)
		if err == nil {
			if attempt > 0 {
				b.Refund()
			}
			return value, nil
		}
		if classify(err) == Terminal {
			return zero, err
		}
		if attempt+1 >= p.MaxAttempts {
			return zero, &GaveUp{"attempts_exhausted", attempt + 1}
		}
		if !b.Take() {
			return zero, &GaveUp{"budget_denied", attempt + 1}
		}

		delay := fullJitter(attempt, p, r)
		if dl, ok := ctx.Deadline(); ok && time.Now().Add(delay).After(dl) {
			return zero, &GaveUp{"deadline_exceeded", attempt + 1}
		}
		timer := time.NewTimer(delay)
		select {
		case <-ctx.Done():
			timer.Stop()
			return zero, ctx.Err()
		case <-timer.C:
		}
	}
}

var errReset = errors.New("connection reset")
var errBadInput = errors.New("validation failed")

func classify(err error) Verdict {
	if errors.Is(err, errReset) {
		return Retryable
	}
	return Terminal
}

func main() {
	r := rand.New(rand.NewSource(7))
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	calls := 0
	flaky := func(_ context.Context, attempt int, key string) (string, error) {
		calls++
		if attempt < 2 {
			return "", errReset
		}
		return "ok key=" + key[:8], nil
	}

	p := Policy{MaxAttempts: 3, Base: 10 * time.Millisecond, Cap: time.Second}
	b := NewBudget(500, 14)

	v, err := Do(ctx, flaky, classify, p, b, r)
	fmt.Println(v, err, "calls", calls, "tokens", b.tokens)

	calls = 0
	broken := func(_ context.Context, _ int, _ string) (string, error) {
		calls++
		return "", errBadInput
	}
	_, err = Do(ctx, broken, classify, p, NewBudget(500, 14), r)
	fmt.Println("terminal", err, "calls", calls)
}
```

### Rust

Decorrelated jitter, where the next upper bound grows from the previously drawn
value, plus an exhaustive match over the error enum so a new variant forces a
classification decision at compile time. Built with `rustc`.

```rust
use std::time::Duration;

#[derive(Debug)]
enum CallError {
    ConnectionReset,
    Throttled { retry_after_ms: u64 },
    Validation(String),
}

#[derive(Debug, PartialEq)]
enum Verdict {
    Retryable,
    Terminal,
}

fn classify(e: &CallError) -> Verdict {
    match e {
        CallError::ConnectionReset => Verdict::Retryable,
        CallError::Throttled { .. } => Verdict::Retryable,
        CallError::Validation(_) => Verdict::Terminal,
    }
}

struct Lcg(u64);

impl Lcg {
    fn next_f64(&mut self) -> f64 {
        self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1);
        ((self.0 >> 11) as f64) / ((1u64 << 53) as f64)
    }
}

// Decorrelated jitter. the upper bound grows from the previous sleep.
fn decorrelated(prev_ms: u64, base_ms: u64, cap_ms: u64, r: &mut Lcg) -> u64 {
    let bound = (prev_ms.saturating_mul(3)).max(base_ms + 1);
    let span = bound - base_ms;
    let drawn = base_ms + (r.next_f64() * span as f64) as u64;
    drawn.min(cap_ms)
}

// A server directed delay is clamped against the local computed backoff.
fn clamp_server_delay(server_ms: u64, computed_ms: u64) -> u64 {
    server_ms.clamp(computed_ms, computed_ms + 5_000)
}

#[derive(Debug, PartialEq)]
enum GaveUp {
    Terminal,
    AttemptsExhausted(u32),
    BudgetDenied(u32),
    DeadlineExceeded(u32),
}

struct Budget {
    tokens: i32,
    capacity: i32,
    cost: i32,
}

impl Budget {
    fn new(capacity: i32, cost: i32) -> Self {
        Budget { tokens: capacity, capacity, cost }
    }
    fn take(&mut self) -> bool {
        if self.tokens < self.cost {
            return false;
        }
        self.tokens -= self.cost;
        true
    }
    fn refund(&mut self) {
        self.tokens = (self.tokens + self.cost).min(self.capacity);
    }
}

fn retry<T, F>(
    mut op: F,
    max_attempts: u32,
    base_ms: u64,
    cap_ms: u64,
    deadline_ms: u64,
    budget: &mut Budget,
    r: &mut Lcg,
) -> Result<T, GaveUp>
where
    F: FnMut(u32, &str) -> Result<T, CallError>,
{
    let key = format!("{:016x}", r.0);
    let mut attempt: u32 = 0;
    let mut elapsed_ms: u64 = 0;
    let mut prev_ms: u64 = base_ms;

    loop {
        match op(attempt, &key) {
            Ok(v) => {
                if attempt > 0 {
                    budget.refund();
                }
                return Ok(v);
            }
            Err(e) => {
                if classify(&e) == Verdict::Terminal {
                    return Err(GaveUp::Terminal);
                }
                if attempt + 1 >= max_attempts {
                    return Err(GaveUp::AttemptsExhausted(attempt + 1));
                }
                if !budget.take() {
                    return Err(GaveUp::BudgetDenied(attempt + 1));
                }

                let computed = decorrelated(prev_ms, base_ms, cap_ms, r);
                let delay = match e {
                    CallError::Throttled { retry_after_ms } => {
                        clamp_server_delay(retry_after_ms, computed)
                    }
                    _ => computed,
                };
                if elapsed_ms + delay >= deadline_ms {
                    return Err(GaveUp::DeadlineExceeded(attempt + 1));
                }
                let _slept = Duration::from_millis(delay);
                elapsed_ms += delay;
                prev_ms = delay.max(base_ms);
                attempt += 1;
            }
        }
    }
}

fn main() {
    let mut r = Lcg(7);
    let mut b = Budget::new(500, 14);
    let mut calls = 0u32;

    let out = retry(
        |attempt, key| {
            calls += 1;
            if attempt < 2 {
                Err(CallError::ConnectionReset)
            } else {
                Ok(format!("ok key={}", &key[..8]))
            }
        },
        3, 50, 20_000, 30_000, &mut b, &mut r,
    );
    println!("{:?} calls={} tokens={}", out, calls, b.tokens);

    let mut b2 = Budget::new(500, 14);
    let mut calls2 = 0u32;
    let bad: Result<(), GaveUp> = retry(
        |_a, _k| {
            calls2 += 1;
            Err(CallError::Validation("bad field".into()))
        },
        3, 50, 20_000, 30_000, &mut b2, &mut r,
    );
    println!("{:?} calls={}", bad, calls2);
    println!("clamped {}", clamp_server_delay(600_000, 1_000));
}
```

Swift and Java are omitted here. The pattern translates to both without any
change in shape, and the four samples above already cover the two axes that
change the code, whether the deadline is ambient as in Go through the context
or explicit as in the other three, and whether the classifier is exhaustive at
compile time as in Rust or open as in the rest.

## 18. References

- Metcalfe, R. M. and Boggs, D. R. "Ethernet. Distributed Packet Switching for
  Local Computer Networks", *Communications of the ACM* 19(7), July 1976, pages
  395 to 404. Origin of binary exponential backoff. Attribution and the
  algorithm description confirmed through the ACM Digital Library record for the
  later stability analysis of the same algorithm,
  https://dl.acm.org/doi/10.1145/44483.44488, verified 2026-08-02.
- Brooker, Marc. "Exponential Backoff And Jitter", AWS Architecture Blog,
  4 March 2015.
  https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/,
  verified 2026-08-02. Source for the four named variants and their comparison.
- Amazon Web Services. "Retry behavior", *AWS SDKs and Tools Reference Guide*.
  https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html,
  verified 2026-08-02. Source for standard, adaptive and legacy modes, the
  `delay = random(0, 1) x min(20,000 ms, base_delay x 2^retry)` formula, the
  50 ms and 1000 ms base delays, the 500 token retry quota with 14 and 5 token
  costs, the error classification tables, and the `x-amz-retry-after` clamp.
- Beyer, B., Jones, C., Petoff, J. and Murphy, N. R., editors. *Site Reliability
  Engineering*, O'Reilly, 2016, chapter 21, "Handling Overload".
  https://sre.google/sre-book/handling-overload/, verified 2026-08-02. Source
  for the three-attempt limit, the 10 percent client retry budget, the
  retry-at-one-layer rule, and the load figures near 3x and 1.1x.
- gRPC. "A6, client retries", gRPC proposal.
  https://github.com/grpc/proposal/blob/master/A6-client-retries.md, verified
  2026-08-02. Source for `maxTokens`, `tokenRatio`, the `maxTokens / 2`
  threshold, `maxAttempts`, `initialBackoff`, `backoffMultiplier`,
  `retryableStatusCodes` and the `random(0.8, 1.2)` jitter multiplier.
- Envoy Proxy. "Router", HTTP filters configuration.
  https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/router_filter,
  verified 2026-08-02. Source for the 25 ms default base interval, the ten times
  maximum, `x-envoy-max-retries` and the `retry-on` policy vocabulary.
- Envoy Proxy. "CircuitBreakers", cluster API v3.
  https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/cluster/v3/circuit_breaker.proto,
  verified 2026-08-02. Source for `RetryBudget`, `budget_percent` default 20 and
  `min_retry_concurrency` default 3.
- Stripe. "Idempotent requests", Stripe API reference.
  https://docs.stripe.com/api/idempotent_requests, verified 2026-08-02. Source
  for the `Idempotency-Key` header, the 24 hour key lifetime, response replay
  including 500s, parameter comparison, and the guidance against personal
  identifiers as keys.
- Twitter. "Clients", Finagle user guide.
  https://twitter.github.io/finagle/guide/Clients.html, verified 2026-08-02.
  Source for `RetryBudget`, its `ttl`, `minRetriesPerSec` and `percentCanRetry`
  parameters, the 20 percent plus 10 per second default, `RequeueFilter`, and
  the shared-budget guidance.
- Internet Engineering Task Force. RFC 9110, *HTTP Semantics*, June 2022,
  sections 2.4.3, 9.2.2, 10.2.3 and 15.6.4.
  https://www.rfc-editor.org/rfc/rfc9110.html#name-503-service-unavailable,
  verified 2026-08-02. Source for the definition of idempotent methods, the
  automatic retry allowance, `Retry-After`, and 503 Service Unavailable.
- Nygard, Michael T. *Release It!*, Pragmatic Bookshelf, 2007, stability
  patterns chapter. Source for the framing of Retry alongside Circuit Breaker,
  Timeout and Bulkhead. Page numbers are not cited because the edition was not
  opened during authoring.
