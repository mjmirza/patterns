---
name: Rate Limiter
slug: rate-limiter
family: 09-concurrency
category: Concurrency
aliases: [Throttle, Traffic Shaper, Request Governor]
first_described: "ITU-T I.371 (1996), Turner 1986"
maturity: canonical
related: [semaphore, backpressure, circuit-breaker, bulkhead, load-shedding]
incompatible_with: []
verified: 2026-08-02
---

# Rate Limiter

## 1. Name, aliases, and lineage

The canonical name in software engineering is Rate Limiter. The underlying
algorithms predate the web by decades and were first formalized for
telecommunication traffic control, not application programming. The two
foundational algorithms are the leaky bucket and the token bucket, and both
carry a documented lineage independent of any particular language or
framework.

Jonathan S. Turner is credited with the first published description of the
leaky bucket idea, in "New directions in communications (or which way to the
information age?)", IEEE Communications Magazine, volume 24, issue 10, October
1986. Turner described a counter associated with each connection that
increments when a packet arrives and decrements at a fixed periodic rate, so
that a burst of arrivals drains the counter down over time rather than passing
through unmodulated
([Wikipedia summary of Turner's description](https://en.wikipedia.org/wiki/Leaky_bucket),
verified 2026-08-02). The leaky bucket was later standardized for
Asynchronous Transfer Mode networks as the Generic Cell Rate Algorithm, defined
in ITU-T Recommendation I.371, "Traffic control and congestion control in B
ISDN" (1996, revised 2004), and in the ATM Forum User Network Interface
specification version 3.1
([Wikipedia, Leaky bucket, standards section](https://en.wikipedia.org/wiki/Leaky_bucket),
verified 2026-08-02).

The token bucket is described in the same body of ATM standards, ITU-T I.371
and the ATM Forum UNI 3.1 specification, as a scheduling discipline that adds
tokens to a fixed-capacity bucket at a constant rate, where each arriving
packet consumes a number of tokens proportional to its size, and a packet
arriving to an empty bucket is non-conformant
([Wikipedia, Token bucket](https://en.wikipedia.org/wiki/Token_bucket), verified
2026-08-02). The same source notes that the token bucket is directly
comparable to one of the two variants of the leaky bucket found in the
literature, since a token bucket that never accumulates unused tokens behaves
identically to a leaky bucket meter, and the two names are sometimes used
loosely as synonyms in application-layer writing even though they describe
opposite physical metaphors, one bucket that fills with tokens and drains on
use, the other that fills with requests and drains on a timer.

Other names in circulation carry more specific connotations. Throttle is the
common verb and noun used in application frameworks and library APIs, for
example Guava's `RateLimiter` and RxJava's `throttleFirst` operator, and
usually implies the caller-side or gate-side perspective rather than the
network-layer traffic-shaping perspective. Traffic Shaper is the network
engineering term for the same mechanism applied to packet flows rather than
API calls, most visible in Linux traffic control's Hierarchical Token Bucket
queuing discipline. Request Governor is a less common synonym seen in some
enterprise API gateway documentation, describing the same mechanism from the
operator's point of view rather than the client's.

## 2. Problem and context

A shared, finite resource is exposed to a population of independent callers
whose combined demand can exceed the resource's safe operating capacity at any
given moment, and there is no way to know in advance how many callers will
arrive or how much work each one will request.

The situation recurs in three shapes. First, a public or partner-facing API
where the operator wants every client to receive a fair, predictable share of
capacity and wants to prevent a single misbehaving or malicious client from
starving every other client, the classic denial of service concern. Second, an
internal service-to-service call where a downstream dependency has a known
safe throughput, for example a database that saturates past a certain query
rate, and an upstream caller must not overwhelm it even when its own load
spikes. Third, a background job or batch process that consumes an external
resource billed or rationed by request count, where staying under a contracted
cap is a business requirement, not a technical one.

The context that makes rate limiting the right tool, rather than a bigger
resource pool or more replicas, has two parts. The demand pattern is bursty or
adversarial rather than smoothly averaged, so provisioning for the average
still leaves the system exposed at the peak. And the cost of a request being
delayed or rejected is lower than the cost of the shared resource degrading for
every caller at once, so trading a controlled number of individual failures
for the health of the whole system is an acceptable exchange. When neither
condition holds, for example when demand truly is smooth and predictable, a
rate limiter adds latency and complexity for no protective benefit, and simple
capacity provisioning is the better answer.

## 3. Forces

Fairness pulls against throughput. A limiter that guarantees every caller an
equal share necessarily leaves some capacity unused when one caller has
nothing to send and another has a queue, unless the limiter also supports
borrowing unused allowance across callers, which adds coordination cost.

Burst tolerance pulls against steady-state protection. Real traffic is rarely
uniform, and a limiter with zero burst allowance rejects perfectly reasonable
short spikes that the downstream resource could easily absorb, while a limiter
with generous burst allowance can let a burst through that the downstream
resource cannot absorb. The token bucket's burst capacity parameter exists
specifically to tune this trade, and there is no value that is correct for
every workload.

Accuracy pulls against memory and coordination cost. A precise sliding window
that tracks every individual request timestamp gives an exact rate at the cost
of storing every timestamp, which does not fit in a fixed amount of memory as
traffic grows. An approximate counter that only stores two numbers per window
saves memory and coordination overhead at the cost of a bounded but real
error, documented by Cloudflare's own production measurement of their
approximate sliding window counter as an average six percent difference from
the true rate, with 0.003 percent of four hundred million sampled requests
wrongly allowed or rejected
([Cloudflare Engineering Blog, "Counting things, a lot of different things", 2015](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/),
verified 2026-08-02).

Local decision speed pulls against global correctness. A rate limiter that
decides locally on each node, with no coordination, is fast and adds no
network hop, but a fleet of N nodes each independently enforcing a limit of R
requests per second effectively enforces N times R in aggregate unless a
centralized store like Redis is consulted on every decision, which reintroduces
the latency and single-point-of-failure concerns the local decision was meant
to avoid.

Client experience pulls against operator protection. Rejecting a request
outright with an error is the cheapest implementation for the operator and the
worst experience for the client, which is why the more considered
implementations, including nginx's `limit_req` module and Stripe's API, prefer
delaying a request within a burst allowance over rejecting it immediately,
reserving outright rejection for genuine overload.

## 4. Applicability and non-applicability

Reach for a rate limiter when a shared resource has a known or estimable safe
throughput cap and the caller population is untrusted, unpredictable, or
simply numerous enough that uncoordinated demand can exceed that cap.
Reach for it when protecting a downstream dependency from an upstream caller
whose retry behavior under failure could otherwise create a feedback loop that
worsens the outage, the classic retry storm. Reach for it when a contract,
license, or cost model imposes a hard external cap on request volume that
must not be exceeded regardless of internal capacity, for example a paid
third-party API with a metered plan. Reach for it at the boundary of a
multi-tenant system where one tenant's traffic must not degrade another
tenant's experience, which is the fairness use case rather than the pure
protection use case.

Do not reach for it as a substitute for capacity planning. A rate limiter that
is tuned below the system's actual safe capacity manufactures artificial
failures that a bigger resource pool would have avoided entirely, and tuning it
correctly requires knowing the real cap, which is exactly the number
capacity planning is supposed to produce.

Do not reach for it as the only defense against a failure that spreads across
dependent services. A rate limiter caps the rate of new requests but does
nothing about work already admitted and now stuck, which is the job of a
circuit breaker and a timeout, not a rate limiter, and the two are commonly
deployed together rather than as alternatives.

Do not reach for a precise, per-request coordinated limiter when an
approximate local one is adequate. Consulting a centralized counter store on
every single request adds a network round trip to the hot path for every
caller, and if the actual risk is a single caller sending an unreasonable
burst rather than the aggregate across a fleet, a local token bucket per node
with no coordination is both simpler and faster, at the cost of the aggregate
limit becoming approximate across the fleet as described in the forces above.

Do not use it to enforce correctness or ordering. A rate limiter has no
opinion about which request arrives first or whether two requests conflict,
only about how many are allowed through per unit time, so it does not replace
a lock, a queue with ordering guarantees, or an idempotency key for
correctness-sensitive operations.

Do not build a bespoke rate limiter inside a request handler when the
surrounding infrastructure, an API gateway, a reverse proxy, or a service mesh
sidecar, already offers one, because a limiter enforced at the edge is visible
to operators and consistent across every service behind it, while one
scattered through application code invites drift between services.

## 5. Structure

A rate limiter has four participants regardless of the specific algorithm
chosen underneath.

The **Limit Policy** is the configuration, holding the target rate, expressed
as a count over a time unit, and optionally a burst allowance and a key
function that partitions callers into separate buckets, for example one
bucket per API key or one bucket per source IP address.

The **State Store** holds the mutable counters or token counts that the
algorithm reads and updates on every admission decision. For a single-process
limiter this is an in-memory structure guarded by a lock or implemented
lock-free with atomic operations. For a distributed limiter this is an
external store, commonly Redis, accessed with an atomic script or transaction
so that concurrent callers across processes see a consistent count.

The **Admission Decision** is the pure function that, given the current state
and the policy, answers whether a specific request is allowed now, and if not,
how long the caller should wait before retrying. This is the seam where the
different algorithms, fixed window, sliding window, leaky bucket, token
bucket, differ from one another while presenting the same allow-or-deny
contract to the caller.

The **Guarded Resource** is whatever the limiter protects, and it is
intentionally decoupled from the limiter itself. The limiter has no knowledge
of what the resource does, only of the policy and the current state. This
decoupling is what lets the same limiter implementation protect a database
connection pool, an outbound HTTP client, or an inbound API endpoint without
modification.

## 6. ASCII structure diagram

```
+------------------+        +-------------------+
|   Caller / Job    |------->|   Rate Limiter     |
+------------------+        |  (Admission        |
                             |   Decision)         |
                             +---------+----------+
                                       |
                        reads / writes |
                                       v
                             +---------+----------+
                             |   State Store       |
                             |  (in-process or      |
                             |   Redis / shared)    |
                             +----------------------+

        allow -----> +--------------------+
                      |  Guarded Resource   |
                      |  (DB, API, queue)   |
                      +--------------------+

        deny --> reject (429) or
                  delay + retry (queue)
```

## 7. Dynamics

The token bucket variant is the most common shape in application code, and its
runtime behavior follows a repeating cycle.

```
Time T0. bucket holds C tokens (full at startup or after idle period)

Request arrives, needs 1 token
    if bucket.tokens >= 1:
        bucket.tokens -= 1
        ADMIT request
    else:
        DENY or DELAY until refill

Background (conceptual, usually computed lazily on each check
rather than with a real timer thread):
    elapsed = now - bucket.last_refill_time
    new_tokens = elapsed * refill_rate
    bucket.tokens = min(bucket.capacity, bucket.tokens + new_tokens)
    bucket.last_refill_time = now
```

Guava's `RateLimiter` documents exactly this lazy-refill approach under the
name smooth bursty behavior, stating that "on average no more than
permitsPerSecond are issued during any given second, with sustained requests
being smoothly spread over each second," and when the limiter has been idle,
it "will allow bursts of up to permitsPerSecond permits" before settling back
to the steady rate
([Guava 33.4.0 Javadoc, RateLimiter](https://guava.dev/releases/33.4.0-jre/api/docs/com/google/common/util/concurrent/RateLimiter.html),
verified 2026-08-02). Guava additionally supports a warming-up mode where the
limiter "smoothly ramps up its rate, until it reaches its maximum rate at the
end of the period," intended for the case where the downstream resource itself
needs a warmup interval, such as a cache that is initially cold, rather than
being able to sustain full throughput from the first request
([same source](https://guava.dev/releases/33.4.0-jre/api/docs/com/google/common/util/concurrent/RateLimiter.html),
verified 2026-08-02).

The leaky bucket variant, by contrast, does not admit bursts through to the
resource at all when configured as a queue. It accepts requests into a
bounded FIFO buffer and drains that buffer to the resource at a strictly fixed
rate, so from the resource's perspective, traffic always arrives smoothly no
matter how bursty the arrivals were. nginx's `ngx_http_limit_req_module`
implements exactly this behavior, and its own documentation states plainly
that it "limits the request processing rate ... using the 'leaky bucket'
method," with a `burst` parameter controlling how many requests may queue
before being rejected, and a `nodelay` flag that, when set, admits queued
burst requests immediately rather than spacing them out
([nginx documentation, ngx_http_limit_req_module](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html),
verified 2026-08-02).

## 8. Implementation variants

**Fixed window counter.** A single counter per time window, for example per
calendar minute, incremented on each request and reset to zero when the
window boundary passes. Trivial to implement and to reason about, but suffers
a well-known edge effect. a caller who sends its full quota in the last moment
of one window and its full quota again in the first moment of the next window
can push twice the intended rate through in a brief span straddling the
boundary, because the two windows are counted independently with no memory of
each other.

**Sliding window log.** Every request timestamp is stored, and a request is
admitted only if fewer than the limit fall within the trailing time window
measured from now, computed by discarding timestamps older than the window on
each check. This is exact, with no boundary effect, but its memory cost grows
with the request rate rather than staying constant, which makes it a poor fit
for very high-traffic keys.

**Sliding window counter (approximation).** Two counters are kept, the
completed previous window and the still-accumulating current window, and the
estimated rate is computed as a weighted blend of the two based on how far
into the current window the request arrived. Cloudflare's own production
description gives the formula as the previous window's count multiplied by
the fraction of the previous window that overlaps the trailing window, plus
the full current window count, illustrated with a fifty-request-per-minute
limit where fifteen seconds have elapsed, giving forty-two prior requests
times zero point seven five, plus eighteen current requests, an estimated
forty-nine point five
([Cloudflare Engineering Blog, "Counting things, a lot of different things", 2015](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/),
verified 2026-08-02). This variant fixes the fixed-window boundary effect
while using only two stored numbers per key, at the cost of the approximation
error quantified in the forces section above.

**Leaky bucket as a meter.** A counter increments on arrival and decrements at
a fixed periodic rate, with no queueing, and a request that would push the
counter past capacity is simply rejected. This is a pure conformance check,
used to classify traffic as within or outside contract, most visible in its
telecommunications origin as the Generic Cell Rate Algorithm.

**Leaky bucket as a queue.** As described in the dynamics section, requests
enter a bounded FIFO and are drained to the resource at a fixed rate,
producing genuinely smooth output traffic rather than merely a smooth count.
This variant trades latency, since an admitted request may sit in the queue
before being served, for the strongest smoothing guarantee among the common
implementations.

**Token bucket.** As described in the dynamics section, tokens accumulate at a
fixed rate up to a capacity, and each request consumes tokens on admission.
Unlike the leaky-bucket-as-queue, an admitted request is served immediately,
which makes the token bucket the more common choice when the goal is bounding
average throughput while tolerating bursts, rather than eliminating burstiness
from the resource's perspective entirely.

**Distributed token bucket via Redis.** The same token bucket algorithm, but
with the bucket's token count and last-refill timestamp stored as Redis keys,
updated inside a Lua script or a `MULTI`/`EXEC` transaction so the
read-check-decrement sequence is atomic across concurrently calling
processes. This is the shape needed whenever the limiter must enforce a single
logical limit across a fleet of stateless application instances rather than
per-instance.

**Concurrency limiter (a distinct but related shape).** Rather than bounding
requests per unit time, this bounds the number of requests in flight at once,
implemented as a counting semaphore rather than a token bucket. Stripe
documents this as a separate mechanism from its rate limits, noting that
"reaching concurrent request limits is rarer than errors due to overall rate
limits, and generally points to long-running or resource-intensive API
requests"
([Stripe API documentation, Rate limits, page served in German](https://docs.stripe.com/rate-limits),
verified 2026-08-02, translated by the author from that page's German
prose; the German phrase read was "Erreichen von Begrenzungen fur
gleichzeitige Anfragen", corresponding to reaching concurrent request
limits). This variant is covered in depth in the semaphore entry in this
catalog and is named here only to distinguish it from rate-over-time
limiting, since the two are frequently confused.

## 9. Known production uses

**nginx**, the widely deployed HTTP server and reverse proxy, ships a built-in
leaky bucket rate limiter as `ngx_http_limit_req_module`, configured with a
`limit_req_zone` directive defining a shared memory zone, a key such as the
client's binary IP address, and a rate such as `1r/s`, and a `limit_req`
directive applying that zone to a location block with an optional `burst`
parameter
([nginx documentation, ngx_http_limit_req_module](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html),
verified 2026-08-02).

**Stripe** enforces global and per-endpoint API rate limits measured in
requests per second per account, published as one hundred requests per second
in live mode and twenty five requests per second in the sandbox environment
for the global limit, returns HTTP 429 with a `Stripe-Rate-Limited-Reason`
header identifying which specific limit was hit, and its own documentation
recommends client-side use of a token bucket algorithm as "a common approach"
to controlling outbound call volume to their API
([Stripe API documentation, Rate limits](https://docs.stripe.com/rate-limits),
verified 2026-08-02).

**GitHub's REST API** enforces a primary rate limit reported via three
response headers, `x-ratelimit-limit`, `x-ratelimit-remaining`, and
`x-ratelimit-reset`, the last expressed as Unix time in seconds for when the
window resets, with the baseline authenticated allowance documented at five
thousand requests per hour for personal access tokens, OAuth apps, and GitHub
Apps, rising for GitHub Apps installed on an Enterprise Cloud organization
([GitHub REST API documentation, Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api),
verified 2026-08-02).

**Google Guava**, the widely used Java core library, ships `RateLimiter`
under `com.google.common.util.concurrent`, implementing a smooth token-bucket
style limiter with both a smooth-bursty default mode and an optional
warming-up mode, distributed as part of Guava and consumed as a library
dependency by a very large number of downstream Java applications
([Guava 33.4.0 Javadoc, RateLimiter](https://guava.dev/releases/33.4.0-jre/api/docs/com/google/common/util/concurrent/RateLimiter.html),
verified 2026-08-02).

**Cloudflare** operates an approximate sliding-window-counter rate limiter as
part of its edge network, described in the company's own engineering blog as
storing only two counters per key and reporting, from a sample of four hundred
million real requests, that only 0.003 percent were allowed or denied
incorrectly relative to an exact count
([Cloudflare Engineering Blog, "Counting things, a lot of different things", 2015](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/),
verified 2026-08-02).

## 10. Consequences

Positive consequences. A shared resource is protected from any single caller's
demand exceeding its safe operating capacity, converting an unbounded failure
mode, total resource exhaustion affecting every caller, into a bounded one, a
controlled fraction of requests from the offending caller being delayed or
rejected. The decoupling described in the structure section lets one limiter
implementation protect many different kinds of resources without knowledge of
what each one does. A well-chosen algorithm, particularly the token bucket,
tolerates realistic bursty traffic rather than forcing every caller into an
artificially smooth request pattern the real world does not produce.

Negative consequences. Every rate limiter adds a decision point, and therefore
latency, to the hot path of every guarded request, even when the decision is
trivial and fast, and this cost is small per request but is not zero and
compounds under extreme scale. A distributed limiter backed by a shared store
introduces a new dependency, and if that store becomes unavailable, the
limiter must choose between failing open, letting all traffic through
unguarded, and failing closed, rejecting all traffic even when the guarded
resource itself is healthy, and both choices carry risk. An incorrectly tuned
limit, set too low, manufactures artificial errors that erode trust in the API
among well-behaved clients, and set too high, provides no real protection at
all, so the limiter is only as good as the operational discipline that keeps
its configuration matched to the resource's true capacity over time as that
capacity changes.

## 11. Failure modes and misuse

**Symptom.** A fleet of N application instances, each enforcing an
independent, purely local token bucket at rate R, allows an aggregate traffic
rate far above R, sometimes close to N times R, even though every individual
instance appears to be enforcing its limit correctly when inspected alone.
**Cause.** The limit was designed as a single logical cap but implemented
with per-instance state and no coordination, so the true aggregate is the sum
across instances rather than the intended single value.
**Fix.** Move the state to a shared, atomically updated store such as Redis
when the limit must hold across a fleet, or explicitly divide the intended
aggregate limit by the instance count and accept the resulting approximation
if a coordinated store is not acceptable on the hot path.

**Symptom.** Clients that receive a rejected request retry it immediately,
and the retry traffic itself becomes large enough to keep the limiter
perpetually saturated even after the original burst that triggered the first
rejections has passed, a self-sustaining overload sometimes called a retry
storm.
**Cause.** The limiter's rejection response gave the client no signal about
how long to wait, or the client's retry logic ignored the signal and retried
on a fixed short interval with no jitter.
**Fix.** Return a `Retry-After` header or equivalent with every rejection,
and require client-side retry logic to use exponential backoff with random
jitter, which is the exact remedy Stripe's own documentation recommends for
its own 429 responses, warning specifically about the thundering herd effect
that synchronized retries produce
([Stripe API documentation, Rate limits](https://docs.stripe.com/rate-limits),
verified 2026-08-02).

**Symptom.** The limiter appears to reject roughly twice the configured rate
of requests clustered right around a fixed clock boundary, for example the
top of every minute, while behaving correctly the rest of the time.
**Cause.** A fixed window counter is in use, and a caller sent its full quota
at the very end of one window followed immediately by its full quota at the
very start of the next, which the fixed window counts as two separate,
independently-limited events rather than one continuous burst.
**Fix.** Replace the fixed window counter with a sliding window counter or a
token bucket, both of which do not reset abruptly at a clock boundary.

**Symptom.** A downstream service that the limiter is meant to protect still
degrades or falls over even though the rate limiter reports it is enforcing
its configured limit correctly.
**Cause.** The configured limit was set from a guess or from an old capacity
figure rather than a currently measured safe throughput, or the guarded
resource's true capacity dropped, for example due to a slow query plan
regression, without the limiter's configuration being revisited.
**Fix.** Treat the limit as a live operational parameter tied to the
resource's measured capacity, re-derive it whenever the resource's capacity
changes, and alert when the resource shows signs of stress at a request rate
still comfortably under the configured limit, which is the signal that the
limit itself is stale.

**Symptom.** A single high-value or high-volume tenant in a multi-tenant
system is rate limited into a poor experience even though the system overall
has spare capacity, while low-volume tenants never approach their share.
**Cause.** The limiter is enforcing a single flat global limit rather than a
per-key limit partitioned by tenant, so one tenant's traffic consumes the
shared allowance meant for everyone.
**Fix.** Key the limiter's state by tenant identifier rather than globally, so
each tenant's usage is tracked and bounded independently, which is the pattern
GitHub's own documentation describes for its per-app and per-token allowances
([GitHub REST API documentation, Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api),
verified 2026-08-02).

## 12. Trade-off matrix

| Force | Rate Limiter (token bucket) | Semaphore (concurrency limit) | Circuit Breaker | Backpressure (queue-based) |
|---|---|---|---|---|
| What it bounds | Requests admitted per unit time | Requests in flight at once | Calls to a failing dependency | Rate the consumer can actually drain |
| Reacts to | A configured rate, independent of resource health | A configured concurrency count, independent of resource health | Observed failure rate or latency of the dependency | Observed queue depth or consumer signal |
| Protects against | Sustained excess volume, bursts | Long-running requests piling up | A dependency already unhealthy spreading failure downstream | Producer outpacing consumer capacity |
| Fails open or closed on store outage | Depends on implementation, must be chosen explicitly | N/A for in-process semaphores | Opens to reject, by design | Consumer naturally slows, no separate outage mode |
| Coordination cost across a fleet | High if globally exact, low if per-instance approximate | Usually per-instance, rarely fleet-wide | Usually per-instance | Depends on queue technology, can be centralized |
| Typical latency added | Microseconds locally, a round trip if distributed | Near zero, local counter | Near zero when closed, zero calls when open | Adds queueing delay by design |

## 13. Related and incompatible patterns

**Semaphore.** A rate limiter bounds work over time, while a semaphore bounds
work in flight at any instant. They compose naturally, and Stripe's own
concurrency limit alongside its rate limit is a real production example of
both being applied to the same API at once, guarding two distinct failure
modes with two distinct mechanisms.

**Backpressure.** Backpressure is a broader signal-propagation idea, where a
slow consumer communicates its capacity constraint upstream so producers slow
down voluntarily. A rate limiter is one concrete way to implement
backpressure at a boundary, particularly the leaky-bucket-as-queue variant,
but backpressure can also be implemented with bounded queues and blocking
without any explicit rate calculation at all.

**Circuit breaker.** A circuit breaker reacts to observed failure, opening
only once the dependency is already unhealthy, while a rate limiter reacts to
a configured threshold regardless of whether the dependency shows any signs of
stress yet. The two are complementary rather than substitutable. a rate
limiter prevents the dependency from becoming unhealthy in the first place for
predictable excess demand, and a circuit breaker protects the caller once the
dependency is unhealthy for any reason, including reasons the rate limiter
never anticipated.

**Bulkhead.** A bulkhead isolates resource pools per caller or per dependency
so that exhaustion in one pool cannot spread to another. A per-tenant keyed
rate limiter is one way to achieve a bulkhead-like effect for request volume
specifically, while a true bulkhead more commonly isolates thread pools or
connection pools rather than request counts.

**Load shedding.** Load shedding drops or degrades work once the system is
already under duress, usually prioritizing by request importance rather than
by a per-caller fairness rule. A rate limiter is proactive and per-key, while
load shedding is usually reactive and system-wide, and a mature system often
layers both, the rate limiter preventing routine overload and load shedding
catching the residual cases the rate limiter's configuration did not
anticipate.

No pattern in this catalog is flatly incompatible with rate limiting, since it
operates at a system boundary rather than inside any particular internal
structure, but stacking multiple uncoordinated rate limiters at different
layers of the same call path, for example an nginx limiter in front of a
Guava limiter in front of a database connection pool limiter, without a shared
understanding of the true bottleneck, commonly produces confusing, redundant
rejections that are hard to diagnose because no single limiter's configuration
alone explains the observed behavior.

## 14. Refactoring path in and out

Introducing a rate limiter into code that has none starts with measurement,
not implementation. Before writing any limiting logic, establish the actual
safe throughput of the resource being protected, usually by load testing it
in isolation or by observing its behavior at the highest traffic it has
already survived without degrading. Only once that number exists does a
specific limit value mean anything.

The next step is choosing the narrowest boundary that actually needs
protecting, usually the entry point closest to the resource rather than the
entry point closest to the caller, since limiting close to the resource
protects it from every caller including internal ones the operator does not
control, while limiting only at a public API edge leaves internal callers
unguarded. Introduce the limiter there first, in a permissive, log-only mode
that records what it would have rejected without actually rejecting anything,
so the chosen limit can be validated against real traffic before it starts
affecting users. Once the log-only period shows the limit does not reject
legitimate traffic, flip it to enforcing mode, and add the `Retry-After`
header or equivalent so well-behaved clients can back off correctly rather
than hammering the rejection.

Removing a rate limiter, when the underlying capacity concern has genuinely
been resolved, for example the resource was replaced with one which scales
horizontally and no longer has a real cap, follows the same caution in
reverse. Switch the limiter back to log-only mode first, confirm over a
representative traffic period that removing it entirely would not have
caused any incidents, and only then delete the enforcement path, leaving the
observability around request volume in place even after the limiter itself is
gone, since that observability is what will reveal if the capacity concern
returns.

## 15. Testing and verification

Unit testing a rate limiter in isolation means testing the pure admission
decision function against a controllable clock, never against the real
system clock, because any test asserting timing behavior against wall-clock
time is unreliable under load on a shared test runner. Inject a fake
clock that the test advances explicitly, then assert the exact admit or deny
sequence for a scripted series of requests and clock advances. This makes it
straightforward to test the fixed-window boundary effect directly, by
constructing the exact scenario from the failure modes section, a burst at
the end of one window followed by a burst at the start of the next, and
asserting whether the implementation under test allows the combined double
burst through, which is precisely the property that distinguishes a fixed
window from a sliding window or token bucket.

Testing the distributed variant additionally requires testing the atomicity
of the read-check-decrement sequence under concurrent access, since the most
common real-world bug in a distributed limiter is a race between two
concurrent callers both reading the same stale token count before either one
writes its decrement, which silently doubles the effective limit. This is
best verified with an integration test against a real instance of the backing
store, issuing many concurrent requests from multiple threads or processes
and asserting the total number admitted never exceeds the configured limit,
because a purely mocked store cannot exercise the actual atomicity guarantee
the production Lua script or transaction is relying on.

Load testing, as distinct from unit testing, verifies the limiter's
behavior under the traffic shape it will actually see in production,
including realistic burstiness rather than a uniform synthetic rate, and
should specifically probe the boundary between the burst allowance and the
steady-state rate to confirm the observed admitted rate matches the
configured rate within the tolerance the chosen algorithm's approximation
implies, using the Cloudflare-documented error bound as a reference point for
what tolerance is reasonable to expect from an approximate sliding-window
implementation.

## 16. Observability signals

A healthy rate limiter emits, at minimum, a count of admitted requests and a
count of rejected or delayed requests, both broken down by the key the limiter
partitions on, for example per API key or per tenant, since an aggregate
rejection count with no key breakdown cannot answer the operationally
important question of whether one specific caller is being throttled or
whether the limit itself is set too low for everyone.

A dashboard for a healthy limiter shows the rejection rate near zero under
normal traffic, with visible, correlated spikes only during genuine bursts or
abusive traffic, and those spikes should correlate with an alert or a log
entry naming the specific key responsible, so an operator investigating a
rejection spike can immediately tell whether it reflects one caller's bug, an
intentional load test, or a general limit that needs raising.

A failing or misconfigured limiter shows one of two opposite signatures.
Either the rejection rate stays high continuously rather than only during
bursts, which indicates the configured limit is below the resource's actual
safe capacity and legitimate traffic is being needlessly rejected, or the
guarded resource itself shows signs of stress, high latency or a high error
rate, while the limiter's own rejection count stays at zero, which indicates
the limit is set too high to provide any real protection at all. Both
signatures are useful only if the limiter's admit and reject counts are
exported alongside the guarded resource's own health metrics on the same
dashboard, so the two can be read together rather than investigated
separately after an incident.

## 17. Security and privacy implications

Judgement in this dimension. The analysis below is engineering reasoning
about attack surface, not a sourced specification of any vendor's security
posture.

Rate limiting is itself a defensive control against denial of service and
credential-stuffing style abuse, since it bounds how quickly an attacker can
attempt requests such as login guesses or scraping requests, but a limiter
keyed on a client-controlled value, such as a header the client sets or an IP
address behind a shared proxy, can itself be trivially evaded by an attacker
who rotates that value, so the key chosen for partitioning has direct security
consequences, not only fairness consequences. A limiter keyed on an
authenticated identity, such as an API key or a signed session token, is
harder to evade than one keyed on network-layer identifiers alone, since
rotating an authenticated identity has a real cost to the attacker that
rotating an IP address usually does not.

The state a distributed rate limiter stores, usually a count per key and a
timestamp, is itself a low-sensitivity artifact, since it reveals only volume
of activity rather than the content of what was requested, but a key that
directly embeds personal data, for example a raw email address used as the
partition key rather than a hashed or opaque identifier, turns an otherwise
low-sensitivity operational store into one that carries personal data subject
to the same data protection obligations as any other store containing that
data, an easy detail to overlook because the rate limiter's own logic never
inspects the key's contents, only its identity.

A rejection response itself can leak information if it is not designed
carefully, for example if a limiter enforces a stricter limit or behaves
observably differently for requests bearing a valid API key versus an invalid
one, an attacker probing for valid keys could use the limiter's own behavior
as an oracle, so the admission decision and its observable timing should not
depend on whether the request would otherwise have been authenticated or
authorized, only on the volume already consumed by that specific key.

## 18. References

Turner, Jonathan S. "New directions in communications (or which way to the
information age?)". IEEE Communications Magazine, volume 24, issue 10, October
1986. Cited via
[Wikipedia, "Leaky bucket"](https://en.wikipedia.org/wiki/Leaky_bucket),
verified 2026-08-02.

ITU-T. "Recommendation I.371, Traffic control and congestion control in B
ISDN (B-ISDN)". International Telecommunication Union, 1996, revised 2004.
Cited via [Wikipedia, "Leaky bucket"](https://en.wikipedia.org/wiki/Leaky_bucket)
and [Wikipedia, "Token bucket"](https://en.wikipedia.org/wiki/Token_bucket),
verified 2026-08-02.

ATM Forum. "User-Network Interface (UNI) Specification, version 3.1". Cited via
[Wikipedia, "Leaky bucket"](https://en.wikipedia.org/wiki/Leaky_bucket), and
[Wikipedia, "Token bucket"](https://en.wikipedia.org/wiki/Token_bucket),
verified 2026-08-02.

Wikipedia. "Rate limiting". Section on rate limiting mechanisms and use
against denial of service and scraping.
[https://en.wikipedia.org/wiki/Rate_limiting](https://en.wikipedia.org/wiki/Rate_limiting),
verified 2026-08-02.

Google. "RateLimiter", Guava 33.4.0-jre API documentation, class
`com.google.common.util.concurrent.RateLimiter`.
[https://guava.dev/releases/33.4.0-jre/api/docs/com/google/common/util/concurrent/RateLimiter.html](https://guava.dev/releases/33.4.0-jre/api/docs/com/google/common/util/concurrent/RateLimiter.html),
verified 2026-08-02.

nginx. "Module ngx_http_limit_req_module".
[https://nginx.org/en/docs/http/ngx_http_limit_req_module.html](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html),
verified 2026-08-02.

Stripe. "Rate limits", Stripe API documentation.
[https://docs.stripe.com/rate-limits](https://docs.stripe.com/rate-limits),
verified 2026-08-02. The page was served in German by the fetch tool used to
verify it; quoted figures and terms attributed to this source in this entry
are translated by the author from that page's tables and prose.

GitHub. "Rate limits for the REST API", GitHub REST API documentation.
[https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api),
verified 2026-08-02.

Cloudflare. "Counting things, a lot of different things", Cloudflare
Engineering Blog, 2015.
[https://blog.cloudflare.com/counting-things-a-lot-of-different-things/](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/),
verified 2026-08-02.

## Code examples

### TypeScript, token bucket

```typescript
class TokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private readonly capacity: number,
    private readonly refillPerSecond: number,
  ) {
    this.tokens = capacity;
    this.lastRefill = Date.now();
  }

  private refill(now: number): void {
    const elapsedSeconds = (now - this.lastRefill) / 1000;
    const added = elapsedSeconds * this.refillPerSecond;
    this.tokens = Math.min(this.capacity, this.tokens + added);
    this.lastRefill = now;
  }

  tryAcquire(cost = 1): boolean {
    const now = Date.now();
    this.refill(now);
    if (this.tokens >= cost) {
      this.tokens -= cost;
      return true;
    }
    return false;
  }
}

function demo(): void {
  const bucket = new TokenBucket(5, 1);
  let admitted = 0;
  for (let i = 0; i < 8; i++) {
    if (bucket.tryAcquire()) admitted++;
  }
  console.log(`admitted ${admitted} of 8 immediate requests, capacity was 5`);
}

demo();
```

### Python, sliding window counter (approximate)

```python
import time


class SlidingWindowCounter:
    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window = window_seconds
        self.previous_count = 0
        self.current_count = 0
        self.current_window_start = time.monotonic()

    def _roll_window(self, now: float) -> None:
        elapsed = now - self.current_window_start
        if elapsed >= self.window:
            windows_passed = int(elapsed // self.window)
            if windows_passed == 1:
                self.previous_count = self.current_count
            else:
                self.previous_count = 0
            self.current_count = 0
            self.current_window_start += windows_passed * self.window

    def allow(self) -> bool:
        now = time.monotonic()
        self._roll_window(now)
        elapsed_in_current = now - self.current_window_start
        overlap = max(0.0, (self.window - elapsed_in_current) / self.window)
        estimated = self.previous_count * overlap + self.current_count
        if estimated < self.limit:
            self.current_count += 1
            return True
        return False


if __name__ == "__main__":
    limiter = SlidingWindowCounter(limit=3, window_seconds=1.0)
    results = [limiter.allow() for _ in range(5)]
    print(f"first five checks. {results}")
```

### Go, leaky bucket as a queue with a fixed drain rate

```go
package main

import (
	"context"
	"fmt"
	"time"
)

type LeakyQueue struct {
	requests chan int
	interval time.Duration
}

func NewLeakyQueue(capacity int, drainInterval time.Duration) *LeakyQueue {
	return &LeakyQueue{
		requests: make(chan int, capacity),
		interval: drainInterval,
	}
}

func (q *LeakyQueue) Submit(id int) bool {
	select {
	case q.requests <- id:
		return true
	default:
		return false
	}
}

func (q *LeakyQueue) Drain(ctx context.Context, handle func(int)) {
	ticker := time.NewTicker(q.interval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			select {
			case id := <-q.requests:
				handle(id)
			default:
			}
		}
	}
}

func main() {
	q := NewLeakyQueue(3, 50*time.Millisecond)
	admitted := 0
	for i := 0; i < 5; i++ {
		if q.Submit(i) {
			admitted++
		}
	}
	fmt.Printf("admitted %d of 5 into a capacity-3 queue\n", admitted)

	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()
	drained := 0
	q.Drain(ctx, func(id int) { drained++ })
	fmt.Printf("drained %d requests at a fixed interval before context expired\n", drained)
}
```

### Rust, token bucket with atomic state for concurrent callers

```rust
use std::sync::atomic::{AtomicI64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

struct TokenBucket {
    tokens_micro: AtomicI64,
    last_refill_micros: AtomicI64,
    capacity_micro: i64,
    refill_per_second_micro: i64,
}

fn now_micros() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("system time error")
        .as_micros() as i64
}

impl TokenBucket {
    fn new(capacity: i64, refill_per_second: i64) -> Self {
        TokenBucket {
            tokens_micro: AtomicI64::new(capacity * 1_000_000),
            last_refill_micros: AtomicI64::new(now_micros()),
            capacity_micro: capacity * 1_000_000,
            refill_per_second_micro: refill_per_second * 1_000_000,
        }
    }

    fn try_acquire(&self) -> bool {
        let now = now_micros();
        let last = self.last_refill_micros.swap(now, Ordering::AcqRel);
        let elapsed_micros = (now - last).max(0) as i64;
        let added = (elapsed_micros as i128 * self.refill_per_second_micro as i128
            / 1_000_000) as i64;
        let prev = self.tokens_micro.fetch_add(added, Ordering::AcqRel);
        let mut current = prev + added;
        if current > self.capacity_micro {
            let excess = current - self.capacity_micro;
            self.tokens_micro.fetch_sub(excess, Ordering::AcqRel);
            current = self.capacity_micro;
        }
        if current >= 1_000_000 {
            self.tokens_micro.fetch_sub(1_000_000, Ordering::AcqRel);
            true
        } else {
            false
        }
    }
}

fn main() {
    let bucket = TokenBucket::new(3, 1);
    let mut admitted = 0;
    for _ in 0..5 {
        if bucket.try_acquire() {
            admitted += 1;
        }
    }
    println!("admitted {} of 5 immediate requests from a capacity-3 bucket", admitted);
}
```

Java is omitted from this entry's runnable set because the pattern's canonical
Java expression is already the production `com.google.common.util.concurrent.RateLimiter`
class shipped in Guava, cited in dimension 9, rather than a hand-rolled
equivalent, and reimplementing it here would only restate that library's
public documentation rather than demonstrate a distinct idiom. Swift is
omitted because the pattern does not surface a Swift-specific idiom beyond a
direct translation of the token bucket shown in Go and Rust above.
