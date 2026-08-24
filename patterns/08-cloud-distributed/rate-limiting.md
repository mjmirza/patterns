---
name: Rate Limiting
slug: rate-limiting
family: 08-cloud-distributed
category: Resilience and Traffic Management
aliases: [Throttling, Traffic Policing, Traffic Shaping, Quota Enforcement, Admission Control]
first_described: "Turner 1986, leaky bucket, IEEE Communications Magazine 24(10)"
maturity: canonical
related: [circuit-breaker, bulkhead, retry-with-backoff, load-shedding, backpressure, queue-based-load-leveling]
incompatible_with: []
verified: 2026-08-02
---

# Rate Limiting

## 1. Name, aliases, and lineage

Rate Limiting is the practice of bounding how many operations a named party may
perform against a resource in a named span of time, and deciding what to do with
the operations that exceed the bound.

The lineage runs through telecommunications rather than through application
software. The leaky bucket, the oldest of the algorithms in common use, is
credited to Jonathan S. Turner in *New directions in communications (or which way
to the information age?)*, IEEE Communications Magazine 24(10), pages 8 to 15,
1986 ([Wikipedia, Leaky bucket](https://en.wikipedia.org/wiki/Leaky_bucket),
verified 2026-08-02). The same page records that a version of the leaky bucket,
the generic cell rate algorithm, is the recommended conformance test for
Asynchronous Transfer Mode networks in the ITU-T I.371 recommendation and the ATM
Forum User Network Interface specification, used for usage parameter control at
network interfaces. Rate limiting therefore arrived in web APIs as a borrowed
idea, already carrying a formal conformance definition, several decades of
hardware implementation, and a vocabulary of cells, buckets and tolerance that
still shows up in library names.

The name is not stable across communities, and the aliases carry real
distinctions rather than being synonyms.

- **Traffic policing** is the network term for measuring a flow and dropping or
  marking the non-conforming part. It maps to rate limiting that rejects.
- **Traffic shaping** is the network term for measuring a flow and delaying the
  non-conforming part so the output is smooth. It maps to rate limiting that
  queues. The nginx `limit_req` directive implements both shapes, delaying by
  default and rejecting when `nodelay` is set
  ([nginx ngx_http_limit_req_module](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html),
  verified 2026-08-02).
- **Quota enforcement** usually means a limit over a long window, a day or a
  month, tied to a commercial plan rather than to instantaneous capacity.
- **Admission control** is the broader family that rate limiting belongs to,
  alongside concurrency limits and load shedding.
- **Throttling** is used loosely for all of the above. Dimension 12 pins down
  what it means here.

The pattern has no single canonical text in the software design literature the
way the Gang of Four patterns do. Its authority comes from standards and from
operator writing. The HTTP status code for a rejected request is defined in
Mark Nottingham and Roy T. Fielding, *RFC 6585, Additional HTTP Status Codes*,
April 2012, section 4
([RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html), verified 2026-08-02).
The operational treatment closest to a canonical reference is chapter 21,
Handling Overload, of the Google SRE book
([sre.google/sre-book/handling-overload](https://sre.google/sre-book/handling-overload/),
verified 2026-08-02).

## 2. Problem and context

A service exposes an operation that costs something to perform. The cost may be
CPU, a database connection, an outbound call to a paid third party, disk write
bandwidth, or a scarce lock. The number of callers is not under the service
owner's control, and neither is the shape of their traffic.

The problem shows up in a codebase in a recognisable way. A single caller, often
by accident, sends two orders of magnitude more traffic than the service was
sized for. The immediate symptom is not that the caller gets slow answers. It is
that every other caller gets slow answers, because the shared resource behind the
endpoint is saturated. Latency rises for everybody, timeouts fire, clients retry,
the retries add load, and the service enters a state it cannot leave without
operator action. The failure is not local to the greedy caller. It is a shared
failure caused by one caller, which is what makes it worth building machinery to
prevent.

Four distinct situations create the need, and they want different answers.

- **Capacity protection.** The service has a known maximum sustainable
  throughput and must stay under it regardless of who is asking. The limit is
  about the service.
- **Fairness between tenants.** The service has spare capacity in aggregate but
  one tenant is consuming a share that starves others. The limit is about
  isolation, and it is the multi-tenant version of the Bulkhead pattern applied
  to request rate rather than to thread pools.
- **Commercial metering.** The limit encodes what the customer paid for. It has
  nothing to do with capacity, and a request rejected under this limit would have
  been served without any strain.
- **Abuse resistance.** The limit exists to make credential stuffing, scraping,
  or enumeration expensive. Here the adversary is trying to evade the limit,
  which changes the design of the keying function more than it changes the
  algorithm.

The context that makes rate limiting the right answer has three parts. The
caller can be identified with something more durable than a source address. The
cost of an operation is roughly uniform, or can be expressed as a weight. And
rejecting a request is an acceptable outcome, which is to say the caller can
retry later or degrade gracefully. Where any of those fail, dimension 4 lists
what to reach for instead.

## 3. Forces

The weighting below is engineering judgement, informed by the sources cited
elsewhere in this entry but not itself a sourced claim.

- **Availability under load.** Favoured, strongly. This is the reason the pattern
  exists. Bounded admitted traffic means bounded queue depth, which means latency
  that stays inside its budget instead of growing without limit.
- **Goodput for the rejected caller.** Sacrificed. A rejected request is work the
  caller wanted done and did not get. The pattern converts a slow degraded
  experience for everyone into a fast clear failure for some, and that trade is
  only correct when the caller can handle the failure.
- **Latency of the admitted path.** Mildly sacrificed. Every request now pays for
  a limiter decision. In-process the cost is a lock and some arithmetic. Against
  a shared store it is a network round trip, which can exceed the latency of the
  work being protected. Dimension 8 covers the two-tier answer.
- **Accuracy against memory.** In direct tension. A sliding window log is exact
  and costs one timestamp per admitted request per key. A fixed window counter
  costs one integer per key and is wrong by up to a factor of two at the
  boundary. The sliding window counter buys most of the accuracy for the memory
  of two integers.
- **Consistency across replicas.** Sacrificed unless paid for. A limiter that is
  correct across a fleet needs shared state, and shared state is a coordination
  point with its own availability, latency and blast radius.
- **Operability.** Favoured on one axis, sacrificed on another. The service
  becomes predictable under load, which is a large operational win. But a new
  class of incident appears, the false rejection, and it is reported by customers
  rather than detected by monitoring unless the instrumentation in dimension 16
  is present from the start.
- **Coupling.** Favoured. The limiter sits at the edge as a decorator around the
  handler and the handler does not know it exists.
- **Cost.** Favoured for the operator, since capacity is bounded and predictable.
  Sacrificed by the addition of the store, which for a global limiter is a
  clustered Redis or an equivalent, with its own bill and its own on-call.
- **Cognitive load.** Sacrificed. Limits interact. A request can pass a per-IP
  limit, a per-token limit, a per-endpoint limit and a per-account daily quota,
  and diagnosing which one rejected it requires the rejection reason to be
  carried through to the response and the logs.

The pattern gives up the ability to serve every request. Anything describing it
as costless is describing a system that has not yet been overloaded.

## 4. Applicability and non-applicability

Reach for rate limiting when the following hold.

- A public or semi-public interface is exposed to callers whose behaviour is not
  under your control, including your own mobile clients after a bad release.
- The protected resource has a maximum sustainable throughput lower than the
  traffic the network can deliver to it.
- A single caller's usage can plausibly harm other callers, so isolation is worth
  buying.
- The commercial model sells units of usage, and the limit is the enforcement of
  the contract.
- An operation is a target for automated abuse, for example login, password
  reset, one-time-code send, or a search endpoint that is expensive per call.
- An outbound integration imposes a limit on you, and you must stay under it. The
  limiter is on the client side and its job is to avoid receiving a 429 rather
  than to send one.

Do NOT reach for rate limiting in these cases. The reason matters more than the
rule.

- **The resource constraint is concurrency, not rate.** If the bottleneck is a
  pool of thirty database connections, a rate limit expressed in requests per
  second does not bound the number in flight, because it does not know how long
  each one takes. A concurrency limiter or a semaphore bounds the thing that
  actually runs out. Stripe treats these as two separate limiters for this
  reason, a request rate limiter and a concurrent requests limiter
  ([Stripe, Scaling your API with rate limiters](https://stripe.com/blog/rate-limiters),
  verified 2026-08-02).
- **The load is internal and trusted, and the correct response is to slow the
  producer rather than to drop.** Dropping a message from your own upstream
  service loses work that nobody will retry. Backpressure, a bounded queue, or
  Queue-Based Load Levelling keeps the work and moves the wait to the producer.
- **The service is already failing and the goal is to survive.** A static rate
  limit calibrated for a healthy service admits far too much when a dependency
  has degraded and every request is now ten times more expensive. Load shedding
  driven by a live health signal is the pattern for that, and it is a different
  mechanism, see dimension 12.
- **The caller cannot be identified.** A limit keyed on something the caller
  controls and can change for free is not a limit. An unauthenticated endpoint
  behind a carrier-grade NAT, keyed on IP, either lets an attacker rotate
  addresses or blocks a whole mobile network. Solve identity first.
- **Request cost varies by orders of magnitude.** A limit of one hundred requests
  per minute means nothing when one request is a key lookup and another is an
  unbounded report. Either weight the requests, which turns the counter into a
  cost meter, or limit the expensive operation separately.
- **There is exactly one caller and you control it.** Configuration in the caller
  is simpler, cheaper and easier to reason about than a limiter at the edge.
- **The goal is to stop a determined attacker rather than to bound load.** Rate
  limiting raises the cost of abuse. It does not prevent it. A distributed
  attacker with many identities passes every per-identity limit. Pair it with
  detection, proof of work, or authentication, and treat the limiter as one layer
  of several.
- **The window you need is long and the accounting must be exact.** Monthly
  billing quotas that must reconcile with an invoice want a durable ledger with
  transactional semantics, not an eventually consistent counter that resets when
  a cache node is replaced.

## 5. Structure

The participants below are roles, and several can collapse into one component in
a small implementation. Naming them separately matters because each is a
different failure surface.

- **Identity Extractor.** Turns an inbound request into a limiter key. This is
  the security-critical participant, because the whole limit is only as strong as
  the key. Typical inputs are an API key, an authenticated account identifier, a
  session, a client certificate subject, or a network address as a last resort.
  It also decides aggregation, for example collapsing an IPv6 address to a /64
  so a single allocation is not a thousand free identities.
- **Policy Resolver.** Maps the key, plus the route and the caller's plan, to a
  concrete policy. A policy is a limit, a window, a burst allowance, a cost per
  request, and a rejection behaviour. This participant is where multi-tenancy and
  commercial tiers live, and it is usually backed by configuration that changes
  without a deploy.
- **Quota Store.** Holds the counter state for a key. In process this is a map
  guarded by a lock. Globally it is a shared datastore whose read-modify-write
  must be atomic. This is the availability-critical participant.
- **Decision Engine.** Runs the algorithm against the stored state and the policy
  and returns a verdict. The verdict is richer than a boolean. It carries whether
  the request conforms, how much quota remains, when the quota next changes, and
  which policy produced the answer.
- **Enforcement Point.** Acts on the verdict. Admit, reject, delay, or admit with
  a lower priority. It is placed at a chokepoint, an API gateway, a service mesh
  sidecar, a middleware in the handler chain, or a client-side interceptor.
- **Response Annotator.** Writes the verdict into the response so the caller can
  behave well. This is the participant most often omitted, and its absence is why
  so many clients hammer a limiter in a tight loop.
- **Client Governor.** Lives in the caller. Reads the annotations, waits, retries
  with jitter, and optionally self-throttles before sending. The Google SRE book
  describes the self-throttling form, where a client that sees a large share of
  its recent requests rejected caps its own outgoing traffic
  ([Google SRE book, Handling Overload](https://sre.google/sre-book/handling-overload/),
  verified 2026-08-02).

The relationships are a straight pipeline with one loop. Extractor feeds
Resolver feeds Engine, which reads and writes the Store, and returns a verdict to
the Enforcement Point, which drives both the Annotator and the protected handler.
The loop is Annotator back to Client Governor, and it is what turns a limiter
from a wall into a protocol.

## 6. ASCII structure diagram

```
+------------------------------------------+
| Enforcement Point, gateway or middleware |
+------------------------------------------+
     ^ inbound request
     |
     v
+-----------------------------------------------------+
| Identity Extractor                                  |
| api key over account over session over /64 net addr |
+-----------------------------------------------------+
     | key
     v
+--------------------------------------------+
| Policy Resolver                            |
| route + plan -> limit, window, burst, cost |
+--------------------------------------------+
     | key + policy
     v
+-----------------------------------------------+
| Decision Engine                               |
| token bucket, leaky, fixed, log, or sliding   |
| reads and modifies the Quota Store atomically |
+-----------------------------------------------+
     | verdict, conform or deny, plus remaining,
     | reset, retry_after, and policy_id
     v
conform? yes -> handler (admitted)
conform? no  -> Response Annotator

+-------------------------------------------+
| Response Annotator, sets 429 plus headers |
+-------------------------------------------+
     |
     v
+---------------------------------------------+
| Client Governor                             |
| waits, adds jitter, self-throttles, retries |
+---------------------------------------------+

The Decision Engine's atomic read, modify, write cycle
runs against the Quota Store, an in-process map, Redis,
DynamoDB, or a mesh sidecar, held out of this chain.
```

## 7. Dynamics

Two flows matter. The admitted path and the rejected path, and the state that
carries between them.

```
 CLIENT        ENFORCE       ENGINE        STORE        HANDLER
   |              |             |            |             |
   |--request---->|             |            |             |
   |              |--key,pol--->|            |             |
   |              |             |--atomic--->|             |
   |              |             |   incr /   |             |
   |              |             |   refill   |             |
   |              |             |<--state----|             |
   |              |<--CONFORM---|            |             |
   |              |   rem=41    |            |             |
   |              |----------------------------->work----->|
   |              |<-----------------------------200-------|
   |<--200 + RateLimit hdr (rem=41, reset=17)|             |
   |              |             |            |             |
   |  ... burst exhausts the bucket ...      |             |
   |              |             |            |             |
   |--request---->|             |            |             |
   |              |--key,pol--->|            |             |
   |              |             |--atomic--->|             |
   |              |             |<--state----|             |
   |              |<--EXCEED----|            |             |
   |              |   retry=3s  |            |             |
   |<--429 + Retry-After hdr (3)--------------             |
   |              |             |            |             |
  wait 3s + jitter              |            |             |
   |--request---->|             |            |             |
```

The state transition inside the Decision Engine, expressed for a token bucket
because it is the variant with the clearest state, is a two-phase step on every
arrival. First a refill phase, which is a pure function of elapsed time since the
last observation and never depends on the arrival itself. Then a spend phase,
which is conditional. Splitting them is what allows the store to hold two values,
a token count and a timestamp, rather than a running timer.

```
        arrival at time t, cost c
                 |
                 v
      tokens = min(cap, tokens + (t - last) * rate)
      last   = t
                 |
        ,--------+--------.
        | tokens >= c ?   |
        `--+-----------+--'
          yes          no
           |            |
           v            v
   tokens -= c    retry_after = (c - tokens) / rate
   ADMIT          REJECT, state unchanged except last
```

The property that makes this correct under concurrency is that both phases must
happen inside one atomic section. A refill that lands between another caller's
refill and spend produces a bucket that has paid out tokens it never had.

## 8. Implementation variants

### The five algorithms

**Fixed window counter.** Divide time into aligned windows of length W. Keep one
counter per key per window. Admit while the counter is below the limit L, reset
on the boundary. One integer of state, one atomic increment, trivially correct
under concurrency, and the cheapest thing that can be called a rate limiter. Its
defect is the boundary burst, which dimension 11 works through with numbers. Use
it when the window is short relative to the harm a double-rate burst can do, or
when the limit is a commercial quota over a day and the boundary is a billing
boundary anyway.

**Sliding window log.** Store the timestamp of every admitted request in a
per-key ordered set. On arrival, drop everything older than one window ago, then
compare the remaining count to L. Exact by construction, with no boundary
artefact, and it answers the question the operator actually asked. The cost is
memory proportional to L per active key and a data structure operation that is
logarithmic rather than constant. In Redis this is a sorted set with
`ZREMRANGEBYSCORE` then `ZCARD` then `ZADD`. It is the right choice for small L
and high value per decision, for example five password resets per hour. It is
the wrong choice for L in the thousands across millions of keys.

**Sliding window counter.** Keep the counter for the current fixed window and the
counter for the previous one. Estimate the trailing-window rate by weighting the
previous count by the fraction of the trailing window that still overlaps it.
Two integers of state, constant time, and no boundary doubling. It assumes
traffic inside the previous window was uniform, so it can be wrong in both
directions on genuinely bursty traffic. Cloudflare published the approach with a
measurement over 400 million requests from 270,000 sources, reporting that
0.003 percent of requests were wrongly allowed or wrongly limited, with an
average difference of 6 percent between the real rate and the approximation
([Cloudflare, Counting things, a lot of different things](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/),
7 June 2017, verified 2026-08-02).

**Token bucket.** A bucket of capacity B refills at rate r. Each request removes
tokens equal to its cost. Admit while tokens remain. The Wikipedia treatment
states the two parameters plainly, a token added every 1/r seconds and a bucket
capacity b that bounds the burst
([Wikipedia, Token bucket](https://en.wikipedia.org/wiki/Token_bucket), verified
2026-08-02). Its property is that it permits a burst up to B while holding the
long-run average at r, which matches how real clients behave, and it expresses
non-uniform cost naturally by charging more tokens. This is the variant most
often chosen for API limits. Stripe states it directly, that they use the token
bucket algorithm with a centralised bucket host, taking tokens on each request
and dripping more in over time
([Stripe, Scaling your API with rate limiters](https://stripe.com/blog/rate-limiters),
verified 2026-08-02). AWS API Gateway states the same, that it throttles requests
using the token bucket algorithm where a token counts for a request, with the
throttling rate being the rate tokens are added and the throttling burst being
the capacity of the bucket
([AWS, Throttle requests to your REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html),
verified 2026-08-02).

**Leaky bucket.** Two things share this name and confusing them is the most
common error in this area. The Wikipedia article separates them cleanly. As a
**meter**, a counter is incremented when a packet is sent and decremented
periodically, which is the mirror image of the token bucket and produces the same
conformance decisions. As a **queue**, the bucket is a finite queue, arrivals are
appended if there is room and discarded otherwise, and one item is transmitted
per clock tick ([Wikipedia, Leaky bucket](https://en.wikipedia.org/wiki/Leaky_bucket),
verified 2026-08-02). The queue form is the one with a distinct behaviour. It
shapes rather than polices, so the output is perfectly smooth and bursts are
converted into latency instead of rejections. That is exactly right when a
downstream integration will ban you for bursting, and exactly wrong for an
interactive API, where the caller would rather be told no in two milliseconds
than told yes in nine seconds. nginx implements the queue form, stating that the
limitation is done using the leaky bucket method, with `burst` setting the queue
size and `nodelay` switching from delay to immediate rejection
([nginx ngx_http_limit_req_module](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html),
verified 2026-08-02).

**GCRA, worth naming as a sixth.** The generic cell rate algorithm expresses the
same conformance test as a virtual scheduling problem. It stores a single value,
the theoretical arrival time of the next conforming request, and compares it to
now against a tolerance. One value instead of two, no separate timestamp, and a
retry-after that falls out of the arithmetic. The redis-cell module implements it
as a single Redis command, stating that it implements the generic cell rate
algorithm which provides a rolling time window, and returning an array carrying
the limit, the remaining quota, a retry-after and a reset time
([brandur/redis-cell](https://github.com/brandur/redis-cell), verified
2026-08-02). The Go sample in this entry is a GCRA.

### Distributed variants

**Per-replica local counters.** The naive shape, and the one dimension 11 shows
is wrong. It is defensible only as a coarse safety net layered under a correct
global limit.

**Centralised store with an atomic script.** Every replica calls one shared store
and the read-modify-write happens server side. In Redis this is a Lua script,
which is correct because the Redis documentation states that Redis guarantees the
script's atomic execution and that all server activities are blocked during its
runtime, so all of the script's effects either have not yet happened or have
already happened
([Redis, Scripting with Lua](https://redis.io/docs/latest/develop/programmability/eval-intro/),
verified 2026-08-02). This is the default correct answer. Its costs are a network
round trip on every request and a hard dependency on the store.

**Two-tier, local plus global.** A cheap local limiter absorbs the obvious excess
without a round trip, and a global limiter enforces the real limit. Envoy
recommends exactly this composition, noting that local rate limiting can absorb
very large bursts in load that might otherwise overwhelm a global rate limit
service, with the limit applied in two stages
([Envoy, Global rate limiting](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/other_features/global_rate_limiting),
verified 2026-08-02).

**Lease or batch acquisition.** A replica asks the global store for a block of N
permits and spends them locally, refreshing when the block runs low. This turns
one round trip per request into one per N, at the cost of a bounded overshoot
equal to the unspent leases held by a replica that dies. Correct when the limit
is large and the traffic is steady, wrong when the limit is small, because the
lease granularity becomes the error.

**Key-affine sharding.** Route every request for a key to the replica that owns
that key, so a local counter is a global counter. Removes the store entirely and
gives exact answers. The cost is that the load balancer must be able to route on
the limiter key, and a replica loss makes every key it owned briefly unlimited or
briefly unavailable.

**Approximate gossip.** Replicas broadcast their local counts periodically and
each estimates the global total. Cheap and available, and wrong by roughly the
traffic arriving during one gossip interval. Acceptable for abuse dampening,
unacceptable for a metered quota a customer pays for.

### Language-idiomatic shapes

In Go and Rust the limiter is a value with an `Allow(now)` method and a mutual
exclusion guard, and injecting the clock as a parameter rather than calling the
system clock inside is what makes it testable. In TypeScript and Python the
limiter is naturally a middleware, a function wrapping a handler, and the closure
form replaces any class hierarchy. In JVM services the shape is usually a filter
in the servlet chain or an interceptor. Across all of them the decisive design
choice is the same and it is not language-specific. The limiter must return a
verdict object rather than a boolean, because the response headers in dimension
9 cannot be produced from a boolean.

## 9. Known production uses

**Stripe.** Stripe's engineering blog describes four limiters running in
production, a request rate limiter, a concurrent requests limiter, a fleet usage
load shedder and a worker utilisation load shedder, implemented with the token
bucket algorithm in Redis
([Stripe, Scaling your API with rate limiters](https://stripe.com/blog/rate-limiters),
verified 2026-08-02). The four-limiter structure is the clearest published
illustration that rate limiting and load shedding are separate mechanisms
addressing separate problems.

**GitHub REST API.** GitHub applies 60 requests per hour to unauthenticated
requests and 5,000 per hour to requests authenticated with a personal access
token, and returns five headers on every response, `x-ratelimit-limit`,
`x-ratelimit-remaining`, `x-ratelimit-used`, `x-ratelimit-reset` and
`x-ratelimit-resource`. Exceeding the primary limit produces a 403 or a 429 with
`x-ratelimit-remaining` set to zero, and secondary limits may carry a
`retry-after` header which clients are told to obey before retrying
([GitHub, Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api),
verified 2026-08-02). This is the reference example of the Response Annotator
participant done properly.

**AWS API Gateway.** Throttling is applied with the token bucket algorithm across
four layers, an AWS Region-wide limit, a per-account limit, a per-API per-stage
limit and a per-client limit from a usage plan, evaluated from most specific to
least. Throttled clients receive `429 Too Many Requests`
([AWS, Throttle requests to your REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html),
verified 2026-08-02). The layered evaluation order is the production answer to
the multi-policy problem raised in dimension 3.

**Envoy Proxy.** Envoy ships both a local rate limit filter and a global one that
calls an external gRPC rate limit service backed by Redis. Its documentation
argues the case for a global limiter directly, that it is extremely difficult to
configure a tight enough per-host limit that operates normally during ordinary
request patterns while still preventing failure spreading through the system, and
recommends applying the limit in two stages
([Envoy, Global rate limiting](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/other_features/global_rate_limiting),
verified 2026-08-02).

**nginx.** The `ngx_http_limit_req_module` is the most widely deployed leaky
bucket in existence, with `limit_req_zone` defining the rate and shared memory
zone, `burst` defining the queue depth, `nodelay` converting shaping into
policing, and `limit_req_status` defaulting to 503
([nginx ngx_http_limit_req_module](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html),
verified 2026-08-02). The 503 default is itself a lesson, since 429 is the
status RFC 6585 defines for this case and most deployments override it.

**Google production services.** The SRE book describes per-customer limits
expressed in CPU seconds per second rather than requests per second, aggregated
globally in real time and pushed to backend tasks, together with client-side
adaptive throttling where a client tracks requests and accepts over two minutes
and continues issuing requests only while requests is below K times accepts, with
K of 2 as the recommended default
([Google SRE book, Handling Overload](https://sre.google/sre-book/handling-overload/),
verified 2026-08-02). Limiting on cost rather than on count is the published
answer to the non-uniform cost problem in dimension 4.

## 10. Consequences

Positive.

- Load on the protected resource is bounded, so latency stays inside its budget
  instead of degrading without limit as arrival rate climbs.
- One caller can no longer take the service down for everybody, which is
  tenant isolation expressed at the request layer.
- Capacity planning becomes arithmetic. The worst case is the sum of the limits
  rather than an unknown.
- Failure becomes fast and explicit. A 429 in two milliseconds is a better
  outcome for a caller than a timeout in thirty seconds, because it carries a
  retry instruction and does not consume a connection slot.
- The commercial model becomes enforceable without a separate mechanism.
- With the response headers in place, well-written clients stop generating the
  excess traffic at source, which reduces load ahead of the limiter rather than
  at it.

Negative. The magnitudes here are judgement drawn from operating such systems.

- Real work is refused. If the limit is misconfigured, the refused work is work
  the service could have done, and the customer experiences an outage that no
  error rate dashboard will show as an error.
- A distributed limiter adds a synchronous dependency to the hot path. The store
  becomes a shared failure domain, and its latency is added to every request.
- Limits interact in ways nobody predicted. Four policies over the same request
  produce a rejection whose cause is opaque unless the policy identifier is
  carried into the response and the logs.
- The limiter itself has unbounded state if the key space is unbounded, which
  turns it into an attack surface. See dimension 17.
- Clients that ignore the response headers convert a rejection into a retry
  storm, so the limiter can increase total request volume while decreasing useful
  throughput.
- Calibration decays. A limit set against last year's capacity is either wasting
  headroom or no longer protecting anything, and nothing about the system
  surfaces that drift automatically.

## 11. Failure modes and misuse

Each entry gives the symptom an operator or a customer actually observes, the
cause, and the fix. The symptoms are drawn from practice rather than from a
published source.

**Symptom.** A customer reports being throttled at roughly twice the documented
limit for a few seconds, then normally again, and it happens near round times.
**Cause.** Fixed window boundary burst. Worked through with the numbers, and this
arithmetic is the reason the sliding variants exist. Take a limit of 100 requests
per 60 seconds, with windows aligned to the minute. Call the start of one window
t equals 0 seconds. Window A then covers t from 0 up to 60, and window B covers t
from 60 up to 120. A client sends 100 requests at t equals 59.5. All 100 fall in
window A, A's counter goes from 0 to 100, and all 100 are admitted. The client
sends 100 more at t equals 60.5. The window has rolled, B's counter starts at 0,
and all 100 are admitted. Inside the one-second span from t equals 59.5 to t
equals 60.5 the service admitted 200 requests. Any trailing 60-second observation
window containing the boundary, for example t equals 30 to t equals 90, also
observes 200. The general result is that a fixed window counter with limit L over
window W admits up to 2L in some window of length W, so the worst-case sustained
rate over a trailing window is 2L divided by W, exactly double the nominal. The
TypeScript sample in this entry reproduces the 200 figure.
**Fix.** Switch to the sliding window counter, which costs one extra integer per
key, or to a token bucket, whose burst is bounded by capacity rather than by
window alignment. If the fixed window must stay, size the limit at half of L and
accept the wasted headroom, or randomise the window offset per key so the
boundaries do not align across the tenant base.

**Symptom.** A tenant with a documented limit of 1,000 requests per minute is
rejected at around 300, and the number changes when the service autoscales.
**Cause.** Per-replica counters. This is the defining error of distributed rate
limiting and it is worth the arithmetic. Suppose the global limit is L of 1,000
per minute across N of 10 replicas. Two configurations are possible and both are
wrong. If each replica enforces L divided by N, which is 100, correctness depends
on the load balancer spreading that tenant's traffic perfectly evenly. It does
not. A tenant using HTTP keep-alive holds a small number of long-lived
connections, so its traffic lands on perhaps three replicas, and its effective
limit is 300 rather than 1,000. If instead each replica enforces the full L of
1,000, the aggregate admitted rate is N times L, which is 10,000, ten times the
intended limit, and the limit protects nothing. There is no static per-replica
number that is correct, because the correct number depends on the routing of one
specific tenant's traffic, which changes continuously. Worse, N is not constant.
Autoscaling from 10 to 30 replicas silently triples the effective global limit in
the second configuration and cuts each tenant's share to a third in the first, so
the limit moves with capacity, which is the opposite of what a contractual quota
means. Envoy makes the same argument from the circuit-breaking side, that a
per-host limit tight enough to stop failure spreading through the system is not
loose enough for normal traffic
([Envoy, Global rate limiting](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/other_features/global_rate_limiting),
verified 2026-08-02).
**Fix.** Move the counter to shared state with an atomic read-modify-write, or
shard keys to replicas so a local counter is a global one. Layer a generous local
limiter under the global one for burst absorption, per Envoy's two-stage advice.

**Symptom.** Request rate to the service rises after the limiter is deployed, and
the store's CPU climbs faster than useful throughput.
**Cause.** Rejected clients retrying immediately, in lockstep, because the
response carried no `Retry-After` and no jitter was applied. Every rejected
client waits the same fixed interval and returns as a synchronised wave.
**Fix.** Return `Retry-After`, and apply full jitter in the client, waiting a
uniformly random duration between zero and the advised delay rather than the
delay itself.

**Symptom.** Memory on the limiter or the Redis cluster grows without bound and
never falls, and the key count is far larger than the customer count.
**Cause.** An unbounded key space. The key includes something an attacker
controls and can vary freely, a raw IPv6 address, a `User-Agent`, or a path
segment.
**Fix.** Bound the key space. Aggregate IPv6 to /64, hash unbounded components
into a fixed number of slots, set a time-to-live on every key equal to the window
plus a margin, and cap the total number of tracked keys with an eviction policy.

**Symptom.** The service goes fully unavailable during a Redis failover although
the underlying handler is healthy.
**Cause.** The limiter fails closed on store errors, so a store outage becomes a
service outage with a wider blast radius than the problem it was preventing.
**Fix.** Decide the failure policy per limit and write it down. Capacity
protection should fail open to a local limiter, because serving degraded is
better than serving nothing. Abuse and billing limits should fail closed,
because admitting unlimited login attempts during a store outage is the worse
outcome. Never let the default be an accident of exception handling.

**Symptom.** The overall request rate is at half the limit, and the service is
still saturated.
**Cause.** Limiting count rather than cost, with heterogeneous request cost. Ten
report generations can outweigh ten thousand key lookups.
**Fix.** Charge a weight per request, sized from measured cost, so the bucket
meters work rather than calls. Google's per-customer limits are expressed in CPU
seconds per second for this reason
([Google SRE book, Handling Overload](https://sre.google/sre-book/handling-overload/),
verified 2026-08-02).

**Symptom.** During a dependency outage the limiter keeps admitting the full
configured rate, and the service falls over anyway.
**Cause.** Misuse of rate limiting as overload protection. A static limit
calibrated against a healthy service is far too generous when each request has
become ten times more expensive.
**Fix.** Add load shedding driven by a live signal, queue depth or utilisation or
latency, on top of the static limit. They are complementary, not alternatives.
This is the distinction dimension 12 makes.

**Symptom.** Rejections cluster on one tenant that did nothing unusual, while a
noisy tenant sails through.
**Cause.** A single global counter with no per-key isolation. The limiter is
protecting capacity but not providing fairness, so whoever arrives first wins.
**Fix.** Key the limit per tenant, and if fairness inside a shared budget is the
goal, use a fair queuing discipline rather than a single counter.

**Symptom.** A client that respects the headers still gets rejected constantly.
**Cause.** The headers describe one policy while a different, tighter policy is
doing the rejecting, so the client's arithmetic is correct against the wrong
number.
**Fix.** Annotate with the binding policy, the one closest to exhaustion, and
identify it. The IETF draft covers exactly this case, defining a
`RateLimit-Policy` field for advertising quota policies alongside a `RateLimit`
field for the quota currently available, and explicitly supporting several
policies with different windows
([draft-ietf-httpapi-ratelimit-headers-11](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/),
23 May 2026, Internet-Draft, verified 2026-08-02).

**Symptom.** A test suite that passes locally fails intermittently in CI with
timing errors.
**Cause.** The limiter reads the system clock internally, so tests must sleep,
and sleeps race with CI scheduling.
**Fix.** Inject the clock. Every sample in this entry takes time as a parameter
for this reason. See dimension 15.

## 12. Trade-off matrix

The five algorithms, plus GCRA, compared across the forces from dimension 3. The
memory column is per active key.

| Algorithm | Memory | Burst behaviour | Worst-case error | Distributed cost | Retry-After |
|---|---|---|---|---|---|
| Fixed window counter | 1 integer | Uncontrolled at boundary | Admits 2L per window | 1 atomic incr | Window end, coarse |
| Sliding window log | L timestamps | None, exact | Zero | Ordered-set ops, heaviest | Exact, from oldest entry |
| Sliding window counter | 2 integers | Smoothed, approximate | About 6 percent average, measured by Cloudflare | 2 atomic incr | Derived, approximate |
| Token bucket | 1 float, 1 timestamp | Bounded by capacity B | Zero against its own definition | 1 script call | Exact, deficit over rate |
| Leaky bucket as queue | Queue of depth B | Removed, output is smooth | Zero, but adds latency | Hard, queue is stateful | Queue wait time |
| GCRA | 1 timestamp | Bounded by tolerance | Zero against its own definition | 1 script call | Exact, falls out of arithmetic |

The four mechanisms that get called throttling, compared. This table is the
explicit answer to the naming confusion in dimension 1.

| Mechanism | Question it answers | Trigger | Excess traffic is | Where it lives | Named example |
|---|---|---|---|---|---|
| Rate Limiting | Is this caller within its agreed rate | Static policy per key | Rejected, usually 429 | Edge, per caller | GitHub 5,000 per hour ([docs](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)) |
| Throttling | Can this caller be slowed rather than refused | Static policy per key | Delayed, then rejected | Edge or client | nginx `limit_req` with `burst` and no `nodelay` ([docs](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html)) |
| Load Shedding | Is the service healthy enough to take more work | Live health signal, utilisation or queue depth | Dropped by priority, lowest first | Server, per request criticality | Google criticality levels, CRITICAL_PLUS down to SHEDDABLE ([SRE book](https://sre.google/sre-book/handling-overload/)) |
| Backpressure | Can the consumer accept more, and can the producer be told | Consumer demand signal | Not produced at all | Producer to consumer channel | Reactive Streams 1.0.4, `java.util.concurrent.Flow` in JDK 9 and later ([reactive-streams.org](https://www.reactive-streams.org/)) |

The distinctions that matter in practice. Rate limiting and throttling differ
only in what happens to the excess, rejection against delay, and both use a
static policy that does not know whether the service is healthy. Load shedding is
the one that reads a live signal, which is why it works during a dependency
outage when a static limit does not, and why the Google SRE book pairs
criticality levels with per-customer quotas rather than replacing one with the
other. Backpressure is different in kind from all three, because no request is
refused. The producer is told to slow down and the work is never created, which
is only possible when the producer is cooperative and the channel carries a
demand signal, as in the Reactive Streams specification where back pressure
exists so the queues mediating between threads can be bounded
([reactive-streams.org](https://www.reactive-streams.org/), version 1.0.4,
26 May 2022, verified 2026-08-02). Rate limiting is what you use when the
producer is a stranger.

## 13. Related and incompatible patterns

**Circuit Breaker.** Complementary and frequently confused. A circuit breaker
protects the caller from a failing dependency by refusing to call it. A rate
limiter protects a resource from a healthy caller asking for too much. They sit
on opposite sides of the same call and both return fast failures, which is where
the confusion starts. A service commonly has both, a limiter on its inbound edge
and a breaker on each outbound dependency.

**Bulkhead.** The same isolation idea applied to a different resource. Bulkhead
partitions concurrency, threads or connections, so one workload cannot consume
another's. Rate limiting partitions arrival rate. Use bulkhead when the scarce
thing is in-flight capacity, and rate limiting when it is throughput. Dimension 4
notes that reaching for one when you needed the other is a common mistake.

**Retry with Backoff.** The mandatory partner on the client side, and actively
harmful without jitter. A limiter that returns `Retry-After` and a client that
retries after exactly that interval produce synchronised waves. Full jitter is
what breaks the synchronisation.

**Load Shedding.** Layers above. See dimension 12 for the distinction. Stripe
running both a request rate limiter and two load shedders is the production
demonstration that these are separate mechanisms
([Stripe](https://stripe.com/blog/rate-limiters), verified 2026-08-02).

**Queue-Based Load Levelling.** An alternative rather than a partner, for the
cases where the work must not be lost. Instead of rejecting the excess, accept it
into a durable queue and drain at a controlled rate. Choose it when the operation
can be asynchronous and the caller only needs an acknowledgement. Choose rate
limiting when the caller needs an answer now.

**Decorator and Chain of Responsibility.** The structural patterns the
Enforcement Point is usually built from. A limiter is a decorator around a
handler, and a stack of limiters evaluated most specific first is a
responsibility chain. AWS API Gateway's four-layer evaluation order is that chain
made explicit ([AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html),
verified 2026-08-02).

**Ambassador and Sidecar.** The deployment shapes that let a limiter be added
without touching application code, which is what Envoy's filters are.

**Nothing here is strictly incompatible**, which is why the frontmatter carries
an empty incompatibility list. The closest thing to a conflict is combining a
queueing leaky bucket with an aggressive client-side timeout. The shaper delays a
request to smooth the output while the client has already given up and retried,
so the service does the work twice and the client sees neither result. If you
shape, the queue wait must be visible to the client and shorter than its timeout.

## 14. Refactoring path in and out

### Introducing it

1. **Measure before limiting.** Instrument request rate per candidate key for at
   least one full weekly cycle. The distribution is almost always long-tailed,
   and the limit must sit above the legitimate ninety-ninth percentile, not at
   the mean. Setting a limit without this data is how the false-rejection
   incidents in dimension 11 start.
2. **Choose the key deliberately.** Prefer an authenticated identity. Where none
   exists, decide the aggregation for network addresses explicitly rather than
   inheriting whatever the framework hands you.
3. **Deploy in observe-only mode.** Run the full decision path, record the
   verdict, and admit every request regardless. Compare the count of would-be
   rejections against the customers they belong to. This step catches
   miscalibration before a customer does, and skipping it is the most common
   process failure in rolling out a limiter.
4. **Add the response annotations before the enforcement.** Emit `RateLimit`
   headers while still in observe-only, so well-behaved clients begin
   self-limiting before any rejection happens.
5. **Enforce for a small cohort.** A single internal tenant, then a percentage of
   the base, with the ability to disable per key without a deploy.
6. **Add the client-side governor.** Your own first-party clients should respect
   `Retry-After` and apply jitter before you enforce broadly, or your own traffic
   becomes the retry storm.
7. **Move to shared state only when the fleet makes local state wrong.** A single
   replica does not need Redis. Adding the store before it is needed buys a
   dependency and pays for it in latency.

### Removing it

A limit stops earning its place when the protected resource has been
rearchitected so its capacity sits far above any plausible demand, when the
commercial model no longer meters that operation, or when the limit has never
rejected a legitimate request in a year and the abuse it was built for has moved
elsewhere.

1. Confirm from the metrics in dimension 16 that the rejection count for that
   policy is at or near zero over a long window, and that the near-limit
   histogram shows no tenant approaching it.
2. Raise the limit rather than deleting the code, and observe. A limit set to ten
   times its current value is functionally absent while remaining a safety net
   and a working code path.
3. Keep the headers. Clients built against `RateLimit` handling do not break when
   the numbers grow, and they do break when the header disappears and their
   parsing assumed it.
4. Delete the policy only after the raised limit has held for a full seasonal
   cycle, including whatever the annual peak is for that business.
5. Remove the store dependency last, because it is usually shared with limits you
   are keeping.

Cross reference the refactoring family entries on Extract Method for pulling the
decision out of an inline conditional, and on Replace Conditional with
Polymorphism where several limiter algorithms end up behind one interface.

## 15. Testing and verification

This dimension is practice rather than a sourced claim.

What the pattern makes easy to test. The decision logic is a pure function of
state, policy and time, so it can be tested exhaustively without a server, a
socket or a sleep. Every sample in this entry takes the current time as a
parameter for exactly this reason, and that single design choice is what turns a
flaky timing test into a deterministic one.

What it makes harder. The interesting behaviour is concurrent and distributed,
and neither is reachable from a unit test. The bugs that reach production are in
the atomicity of the read-modify-write and in the interaction between replicas,
which is the part a unit test cannot see.

The techniques that apply.

- **Injected clock.** A fake clock advanced by the test, never `sleep`. The
  Python sample uses a `FakeClock` callable, the Go and Rust samples take a
  timestamp argument.
- **Boundary tables.** Assert at exactly limit minus one, limit, and limit plus
  one, and at the window boundary from both sides. The fixed window arithmetic in
  dimension 11 is a test case, not only an explanation, and the TypeScript sample
  asserts the 200-in-1000ms result.
- **Property-based testing.** The invariant worth stating is that over any
  trailing window of length W, the number of admitted requests never exceeds the
  algorithm's declared bound. For a sliding window log that bound is L. For a
  fixed window it is 2L, and writing the test with the honest bound of 2L is what
  makes the weakness visible to the next reader.
- **Concurrency stress.** Run N threads against one limiter with a fixed total
  budget and assert the total admitted equals the budget exactly. A missing lock
  shows up here and nowhere else.
- **Integration test against a real store.** The Lua script must be tested
  against a real Redis, because the atomicity guarantee is a property of the
  server, not of the client library
  ([Redis, Scripting with Lua](https://redis.io/docs/latest/develop/programmability/eval-intro/),
  verified 2026-08-02). A mocked Redis will pass a script that is not atomic.
- **Failure injection on the store.** Assert the documented fail-open or
  fail-closed behaviour by making the store return errors and time out. This is
  the test that would have caught the total-outage failure mode in dimension 11.
- **Contract test on the response.** Assert the status code is 429, that
  `Retry-After` is present and parses as either a delay in seconds or an HTTP
  date, and that its value is not negative.
- **Clock skew.** For a distributed limiter, feed timestamps that go backwards
  and assert the limiter does not admit a burst or wedge permanently. Monotonic
  time inside a process and store-side time across processes are the two safe
  choices.

## 16. Observability signals

This dimension is practice. The specific thresholds below are judgement.

Emit as counters, labelled by policy identifier, key class such as tenant or
route, and outcome.

- `ratelimit_decisions_total` with labels for outcome, policy and key class.
  The base measurement. Rejections without the policy label are close to useless
  when several policies are in play, which is the diagnosis failure in
  dimension 11.
- `ratelimit_rejected_total` broken out by whether the caller is authenticated.
  A rejection rate concentrated on unauthenticated traffic is a limiter doing its
  job. The same rate on paying authenticated tenants is an incident.
- `ratelimit_headroom_ratio`, a histogram of remaining quota over limit at
  decision time. A healthy dashboard shows most tenants far from their limit with
  a thin tail approaching it. A distribution piled against zero means the limit
  is now the binding constraint on the business rather than a safety net.
- `ratelimit_store_latency_seconds`, a histogram. This is added to every request,
  so its ninety-ninth percentile belongs in the service latency budget. A visible
  step here is the two-tier variant in dimension 8 asking to be adopted.
- `ratelimit_store_errors_total` alongside `ratelimit_failopen_total`. The second
  is the one to alert on, because it is the window during which the limit is not
  being enforced.
- `ratelimit_keys_tracked`, a gauge. Growth that does not level off is the
  unbounded key space attack in dimension 17 in progress.

Log at the rejection, never at the admission, and carry the key class, the policy
identifier, the observed rate and the advised retry. Logging every admitted
request duplicates the access log at the cost of the busiest code path in the
service.

Trace by adding span attributes on the enforcement span, the policy identifier,
the outcome and the remaining quota. A trace showing a 429 with the binding
policy named answers a support ticket in one step.

What healthy looks like. Rejection rate low, single digits per thousand or less,
stable over the day, mostly unauthenticated or known-abusive keys. Headroom
histogram weighted toward plenty remaining. Store latency an order of magnitude
below the handler's. Key count flat and proportional to active tenants.

What failing looks like, in three shapes. A sharp step change in rejections
correlated with a deploy is a policy misconfiguration and should be rolled back
before it is analysed. A slow climb in rejections across many tenants over weeks
is capacity growth outrunning a limit that was never revisited. Rejections
concentrated in one tenant with a simultaneous spike in that tenant's request
rate is the pattern working correctly, and the right response is a conversation
rather than a code change.

## 17. Security and privacy implications

This dimension is analytical.

**The keying function is the security boundary.** A limit keyed on something the
attacker controls for free provides no protection. `X-Forwarded-For` is
attacker-supplied unless a trusted proxy has overwritten it, so a limiter reading
the leftmost value is trivially bypassed by adding a header. Read the address the
proxy inserted, count the proxy hops you actually operate, and treat everything
to the left of that as untrusted. RFC 6585 is explicit that it does not define
how the origin server identifies the user or how it counts requests, which means
the entire security property of a 429 lives in a design decision the standard
deliberately leaves to the implementer
([RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html), section 4, verified
2026-08-02).

**IPv6 aggregation.** A single residential IPv6 allocation is commonly a /64,
which is a 64-bit host space, so keying per address gives an attacker effectively
unlimited identities at no cost. Aggregate to /64, and to /48 for hosting ranges
where a customer may hold many /64s.

**The limiter as an amplification target.** The Quota Store is a shared resource
reached before authentication. An attacker who can create unbounded keys can
exhaust its memory and take down every tenant, converting an availability control
into an availability vulnerability. Bound the key space, set a time-to-live on
every key, and cap total tracked keys.

**Rate limiting as an authentication control.** On login, password reset and
one-time-code endpoints the limiter is a primary defence against credential
stuffing and code brute force. Two design points follow. Key on the target
account as well as on the source, because an attacker distributing one attempt
per account across a million accounts passes every source-keyed limit. And for
these endpoints fail closed, because an open limiter during a store outage is an
open door.

**Information disclosure through the headers.** The exact response headers that
make a limiter usable also tell an attacker their remaining budget, which makes
enumeration efficient, and can reveal a customer's commercial tier through the
limit value. On authentication endpoints, consider omitting the remaining count
and returning only the status and a coarse retry. Elsewhere the interoperability
benefit outweighs the leak, which is the trade GitHub has made by publishing five
headers on every response
([GitHub](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api),
verified 2026-08-02).

**Timing side channels.** A limiter that performs a store lookup only for known
keys and short-circuits for unknown ones leaks key existence through response
time. Keep the work uniform across the hit and miss paths on any endpoint where
key existence is a secret.

**Denial of wallet.** Where the protected resource is metered by a third party, a
model inference API or an SMS gateway, the limiter is a spending control. Its
failure mode is a bill rather than an outage, so it should fail closed and should
be paired with a hard budget cap that is checked independently.

**Privacy.** The Quota Store holds identifiers keyed to behaviour, so a limiter
key naming a specific IPv6 address, carrying a live counter, is a record that a
specific subscriber line made requests at a specific time. Under a data
protection regime that is personal data. Keep the time-to-live short, hash
identifiers where the raw value is not needed for support, and keep limiter keys
out of long-lived analytics stores.

**Where the pattern is silent.** Rate limiting says nothing about the content of
a request. It will not stop one malicious request, and treating it as an
application firewall is a category error. It also says nothing about
authorisation. A caller within its rate is not thereby permitted to do what it is
asking.

## Code

Four implementations, one algorithm each, all compiled or run on 2026-08-02.

### Python, token bucket with injected clock

Run with `python3 tb.py`. Verified output is shown after the listing.

```python
import threading
import time


class TokenBucket:
    """Lazy-refill token bucket. Capacity is the burst, rate is tokens per second."""

    def __init__(self, capacity: float, rate: float, now=time.monotonic):
        if capacity <= 0 or rate <= 0:
            raise ValueError("capacity and rate must be positive")
        self.capacity = float(capacity)
        self.rate = float(rate)
        self._now = now
        self._tokens = float(capacity)
        self._last = now()
        self._lock = threading.Lock()

    def _refill(self, t: float) -> None:
        delta = t - self._last
        if delta > 0:
            self._tokens = min(self.capacity, self._tokens + delta * self.rate)
            self._last = t

    def acquire(self, cost: float = 1.0):
        """Return (allowed, retry_after_seconds). retry_after is 0.0 when allowed."""
        if cost > self.capacity:
            raise ValueError("cost exceeds bucket capacity, request can never succeed")
        with self._lock:
            t = self._now()
            self._refill(t)
            if self._tokens >= cost:
                self._tokens -= cost
                return True, 0.0
            deficit = cost - self._tokens
            return False, deficit / self.rate


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def demo():
    clock = FakeClock()
    b = TokenBucket(capacity=5, rate=1.0, now=clock)
    results = [b.acquire()[0] for _ in range(7)]
    print("burst of 7 against capacity 5:", results)

    ok, wait = b.acquire()
    print("denied, retry_after seconds:", round(wait, 3))

    clock.advance(3.0)
    print("after 3s of refill:", [b.acquire()[0] for _ in range(4)])


if __name__ == "__main__":
    demo()
```

```
burst of 7 against capacity 5: [True, True, True, True, True, False, False]
denied, retry_after seconds: 1.0
after 3s of refill: [True, True, True, False]
```

### Go, GCRA as a virtual scheduler

Verified with `go vet` and `go run` against go1.26.4. The one-slot channel is a
mutual exclusion guard, chosen over `sync.Mutex` only to keep the listing short.

```go
package main

import (
	"fmt"
	"time"
)

// GCRA is the generic cell rate algorithm as a virtual scheduler. emission is
// the spacing between conforming requests, tolerance is the burst slack.
type GCRA struct {
	gate      chan struct{}
	emission  time.Duration
	tolerance time.Duration
	tat       time.Time
}

func NewGCRA(count int, period time.Duration, burst int) *GCRA {
	emission := period / time.Duration(count)
	return &GCRA{
		gate:      make(chan struct{}, 1),
		emission:  emission,
		tolerance: time.Duration(burst-1) * emission,
	}
}

// Allow reports whether the request conforms, and how long to wait if not.
// The one-slot channel serialises access to the stored arrival time.
func (g *GCRA) Allow(now time.Time) (bool, time.Duration) {
	g.gate <- struct{}{}
	defer func() { <-g.gate }()

	if g.tat.Before(now) {
		g.tat = now
	}
	if g.tat.Sub(now) > g.tolerance {
		return false, g.tat.Add(-g.tolerance).Sub(now)
	}
	g.tat = g.tat.Add(g.emission)
	return true, 0
}

func main() {
	g := NewGCRA(10, time.Second, 5)
	base := time.Unix(0, 0)

	var out []bool
	for i := 0; i < 7; i++ {
		ok, _ := g.Allow(base)
		out = append(out, ok)
	}
	fmt.Println("burst of 7 at t=0, burst budget 5:", out)

	_, wait := g.Allow(base)
	fmt.Println("retry after:", wait)

	later := base.Add(300 * time.Millisecond)
	var out2 []bool
	for i := 0; i < 4; i++ {
		ok, _ := g.Allow(later)
		out2 = append(out2, ok)
	}
	fmt.Println("after 300ms at 10 per second:", out2)
}
```

```
burst of 7 at t=0, burst budget 5: [true true true true true false false]
retry after: 100ms
after 300ms at 10 per second: [true true true false]
```

### Rust, sliding window counter

Compiled with `rustc -O sliding.rs`, verified against rustc 1.97.1.

```rust
use std::collections::HashMap;

// Sliding window counter. Two fixed buckets, older one weighted by overlap.
pub struct SlidingWindow {
    window_ms: u64,
    limit: f64,
    state: HashMap<String, Bucket>,
}

#[derive(Clone, Copy)]
struct Bucket {
    window_start: u64,
    current: u64,
    previous: u64,
}

impl SlidingWindow {
    pub fn new(window_ms: u64, limit: u64) -> Self {
        SlidingWindow { window_ms, limit: limit as f64, state: HashMap::new() }
    }

    fn roll(&self, b: &mut Bucket, now_ms: u64) {
        let start = now_ms - (now_ms % self.window_ms);
        if start == b.window_start {
            return;
        }
        if start == b.window_start + self.window_ms {
            b.previous = b.current;
        } else {
            b.previous = 0;
        }
        b.current = 0;
        b.window_start = start;
    }

    // Returns (allowed, estimated_rate_over_trailing_window)
    pub fn allow(&mut self, key: &str, now_ms: u64) -> (bool, f64) {
        let start = now_ms - (now_ms % self.window_ms);
        let w = self.window_ms;
        let mut b = *self.state.entry(key.to_string()).or_insert(Bucket {
            window_start: start,
            current: 0,
            previous: 0,
        });
        self.roll(&mut b, now_ms);

        let elapsed = (now_ms - b.window_start) as f64;
        let overlap = (w as f64 - elapsed) / w as f64;
        let estimate = b.previous as f64 * overlap + b.current as f64;

        let allowed = estimate < self.limit;
        if allowed {
            b.current += 1;
        }
        self.state.insert(key.to_string(), b);
        (allowed, estimate)
    }
}

fn main() {
    let mut sw = SlidingWindow::new(60_000, 100);

    for _ in 0..100 {
        sw.allow("tenant-a", 30_000);
    }
    let (ok, est) = sw.allow("tenant-a", 59_999);
    println!("at t=59.999s, estimate {:.3}, allowed {}", est, ok);

    let (ok2, est2) = sw.allow("tenant-a", 60_001);
    println!("at t=60.001s, estimate {:.3}, allowed {}", est2, ok2);

    let (ok3, est3) = sw.allow("tenant-a", 105_000);
    println!("at t=105s, estimate {:.3}, allowed {}", est3, ok3);
}
```

```
at t=59.999s, estimate 100.000, allowed false
at t=60.001s, estimate 99.998, allowed true
at t=105s, estimate 26.000, allowed true
```

The middle line is the point of the algorithm. One millisecond past the boundary
the previous window still counts for 99.998 of the estimate, so the fixed window
reset does not hand the caller a fresh budget.

### TypeScript, sliding window log and the fixed window boundary burst

Type-checked with `tsc --strict --target es2022 --types node` against TypeScript
5.9, then run under Node 23.11.

```typescript
type Decision = { allowed: boolean; retryAfterMs: number; count: number };

const emit = (s: string): void => {
  process.stdout.write(s + "\n");
};

// Sliding window log. Exact, at one timestamp per admitted request.
class SlidingWindowLog {
  private hits = new Map<string, number[]>();

  constructor(private windowMs: number, private limit: number) {}

  check(key: string, nowMs: number): Decision {
    const cutoff = nowMs - this.windowMs;
    const log = this.hits.get(key) ?? [];

    let drop = 0;
    while (drop < log.length && log[drop] <= cutoff) drop++;
    const live = drop > 0 ? log.slice(drop) : log;

    if (live.length >= this.limit) {
      this.hits.set(key, live);
      const oldest = live[live.length - this.limit];
      return {
        allowed: false,
        retryAfterMs: oldest + this.windowMs - nowMs,
        count: live.length,
      };
    }

    live.push(nowMs);
    this.hits.set(key, live);
    return { allowed: true, retryAfterMs: 0, count: live.length };
  }
}

// Fixed window counter, written so the boundary burst is reproducible.
class FixedWindow {
  private state = new Map<string, { start: number; n: number }>();

  constructor(private windowMs: number, private limit: number) {}

  check(key: string, nowMs: number): boolean {
    const start = nowMs - (nowMs % this.windowMs);
    const s = this.state.get(key);
    if (!s || s.start !== start) {
      this.state.set(key, { start, n: 1 });
      return true;
    }
    if (s.n >= this.limit) return false;
    s.n++;
    return true;
  }
}

function main(): void {
  const log = new SlidingWindowLog(60_000, 100);
  for (let i = 0; i < 100; i++) log.check("t", 30_000);
  emit("log at t=59.9s: " + JSON.stringify(log.check("t", 59_900)));
  emit("log at t=60.1s: " + JSON.stringify(log.check("t", 60_100)));
  emit("log at t=90.1s: " + JSON.stringify(log.check("t", 90_100)));

  const fw = new FixedWindow(60_000, 100);
  let admitted = 0;
  for (let i = 0; i < 100; i++) if (fw.check("t", 59_500)) admitted++;
  for (let i = 0; i < 100; i++) if (fw.check("t", 60_500)) admitted++;
  emit(`fixed window admitted ${admitted} inside a 1000ms span`);
}

main();
```

```
log at t=59.9s: {"allowed":false,"retryAfterMs":30100,"count":100}
log at t=60.1s: {"allowed":false,"retryAfterMs":29900,"count":100}
log at t=90.1s: {"allowed":true,"retryAfterMs":0,"count":1}
fixed window admitted 200 inside a 1000ms span
```

The last line is the boundary burst from dimension 11, reproduced. The log
variant rejects at both 59.9 seconds and 60.1 seconds because it counts the real
trailing window. The fixed window admits 200 requests inside one second against a
policy of 100 per minute.

Java and Swift are omitted rather than padded. The pattern translates to both
without any change of shape, a class holding state behind a guard with an
injected clock, so a fifth and sixth listing would add length without adding
information. For the JVM the idiomatic production choice is an existing
implementation such as a Guava `RateLimiter` or a Resilience4j `RateLimiter`
rather than a hand-rolled one.

## 18. References

1. Turner, Jonathan S. *New directions in communications (or which way to the
   information age?)*. IEEE Communications Magazine, volume 24, issue 10, pages 8
   to 15, 1986. Cited via
   [https://en.wikipedia.org/wiki/Leaky_bucket](https://en.wikipedia.org/wiki/Leaky_bucket),
   verified 2026-08-02. The Wikipedia page was read directly, the IEEE paper was
   not, and the attribution is reported as the encyclopedia states it.
2. Wikipedia. *Leaky bucket*.
   [https://en.wikipedia.org/wiki/Leaky_bucket](https://en.wikipedia.org/wiki/Leaky_bucket),
   verified 2026-08-02. Source for the meter against queue distinction and for
   the ITU-T I.371 and ATM Forum UNI generic cell rate algorithm references.
3. Wikipedia. *Token bucket*.
   [https://en.wikipedia.org/wiki/Token_bucket](https://en.wikipedia.org/wiki/Token_bucket),
   verified 2026-08-02. Source for the rate and capacity parameters and for the
   stated mirror-image relationship with the leaky bucket as a meter.
4. Nottingham, M. and Fielding, R. *RFC 6585, Additional HTTP Status Codes*,
   IETF, April 2012, section 4.
   [https://www.rfc-editor.org/rfc/rfc6585.html](https://www.rfc-editor.org/rfc/rfc6585.html),
   verified 2026-08-02. Defines 429 Too Many Requests, states that the response
   MAY include a Retry-After header, and states that the specification does not
   define how the origin server identifies the user or counts requests.
5. Fielding, R., Nottingham, M. and Reschke, J., editors. *RFC 9110, HTTP
   Semantics*, IETF, June 2022, section 10.2.3, Retry-After.
   [https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after),
   verified 2026-08-02. Defines the two permitted value forms, an HTTP-date and a
   delay in seconds.
6. IETF HTTP API Working Group. *RateLimit header fields for HTTP*,
   draft-ietf-httpapi-ratelimit-headers-11, 23 May 2026, Internet-Draft.
   [https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/),
   verified 2026-08-02. Defines RateLimit-Policy and RateLimit. Not yet an RFC,
   so treat it as a direction of travel rather than a settled standard.
7. Stripe. *Scaling your API with rate limiters*.
   [https://stripe.com/blog/rate-limiters](https://stripe.com/blog/rate-limiters),
   verified 2026-08-02. Source for the four-limiter production structure and for
   the token bucket in Redis.
8. Cloudflare. *Counting things, a lot of different things*, 7 June 2017.
   [https://blog.cloudflare.com/counting-things-a-lot-of-different-things/](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/),
   verified 2026-08-02. Source for the sliding window counter weighting formula
   and for the measured 0.003 percent misclassification and 6 percent average
   deviation over 400 million requests from 270,000 sources.
9. GitHub. *Rate limits for the REST API*.
   [https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api),
   verified 2026-08-02. Source for the 60 and 5,000 per hour figures, the five
   x-ratelimit headers, and the 403 or 429 behaviour.
10. Amazon Web Services. *Throttle requests to your REST APIs for better
    throughput in API Gateway*.
    [https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html),
    verified 2026-08-02. Source for the token bucket statement and the four-layer
    evaluation order.
11. Envoy Proxy. *Global rate limiting*, architecture overview, latest.
    [https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/other_features/global_rate_limiting](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/other_features/global_rate_limiting),
    verified 2026-08-02. Source for the argument against per-host limits and for
    the two-stage local plus global recommendation.
12. nginx. *Module ngx_http_limit_req_module*.
    [https://nginx.org/en/docs/http/ngx_http_limit_req_module.html](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html),
    verified 2026-08-02. Source for the leaky bucket statement, the burst, delay
    and nodelay parameters, and the 503 default status.
13. Beyer, B., Jones, C., Petoff, J. and Murphy, N. R., editors. *Site
    Reliability Engineering*, O'Reilly, 2016, chapter 21, Handling Overload.
    [https://sre.google/sre-book/handling-overload/](https://sre.google/sre-book/handling-overload/),
    verified 2026-08-02. Source for per-customer limits in CPU seconds per
    second, the client-side adaptive throttling formula over requests and accepts
    with K of 2, and the four criticality levels.
14. Redis. *Scripting with Lua*.
    [https://redis.io/docs/latest/develop/programmability/eval-intro/](https://redis.io/docs/latest/develop/programmability/eval-intro/),
    verified 2026-08-02. Source for the statement that Redis guarantees the
    script's atomic execution and blocks all server activities during its
    runtime.
15. Ellis, Brandur. *redis-cell*.
    [https://github.com/brandur/redis-cell](https://github.com/brandur/redis-cell),
    verified 2026-08-02. Source for GCRA as a single Redis command and for the
    five-element reply carrying limit, remaining, retry-after and reset.
16. Reactive Streams. *Specification version 1.0.4*, 26 May 2022.
    [https://www.reactive-streams.org/](https://www.reactive-streams.org/),
    verified 2026-08-02. Source for back pressure existing so the queues
    mediating between threads can be bounded, and for the JDK 9 and later
    `java.util.concurrent.Flow` equivalence.
