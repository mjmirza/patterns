---
name: Retry Storm
slug: retry-storm
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Retry Multiplication, Retry Avalanche, Retry Explosion, Thundering Herd of Retries]
first_described: "AWS Architecture Blog, Marc Brooker, 2015"
maturity: canonical
related: [circuit-breaker, bulkhead, timeout-pattern, chatty-i-o, cascading-failure]
incompatible_with: []
verified: 2026-08-02
---

# Retry Storm

## 1. Name, aliases, and lineage

The canonical name is Retry Storm, sometimes written Retry Multiplication or
Retry Avalanche. Unlike the classical Gang of Four catalog, this anti-pattern
has no single named originator in a book. It was recognized independently
across several large operators as they scaled distributed backends in the
2010s, and it entered common vocabulary through operational postmortems and
site reliability engineering literature rather than an academic paper.

The clearest and most cited early public treatment is Marc Brooker's 2015 AWS
Architecture Blog post "Exponential Backoff And Jitter", which frames the
problem as many independent clients retrying a failed call to the same
resource, producing synchronized bursts of load that make recovery harder
(Marc Brooker, "Exponential Backoff And Jitter", AWS Architecture Blog, 2015,
https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/,
verified 2026-08-02). The Google Site Reliability Engineering book gives the
pattern its most rigorous named treatment under the heading of cascading
failures, describing exactly this mechanism as retries multiplying request
volume against an already overloaded backend (Betsy Beyer, Chris Jones,
Jennifer Petoff, Niall Richard Murphy, editors, *Site Reliability Engineering.
How Google Runs Production Systems*, O'Reilly, 2016, chapter 22, "Addressing
Cascading Failures", https://sre.google/sre-book/addressing-cascading-failures/,
verified 2026-08-02). Neither source uses the exact phrase "retry storm" as a
formal term of art, but the phrase is now the standard shorthand across
engineering blogs, conference talks, and vendor documentation for the
mechanism both sources describe, and this entry treats it as the settled name
for that mechanism.

The alias Thundering Herd of Retries borrows from the older operating-systems
term thundering herd, which describes many processes waking simultaneously to
contend for one resource. A retry storm is a network-level instance of the
same shape. Many callers wake up on the same failure signal and press the
same resource at the same moment, rather than many threads waking on the same
kernel event.

## 2. Problem and context

A service calls a downstream dependency over the network. Networks are
unreliable, dependencies are sometimes overloaded, and processes crash and
restart. So the calling code retries a failed request, which is a reasonable
default reaction to a transient fault. The retry storm anti-pattern appears
when that reasonable reaction is implemented without limits, and the retry
policy itself becomes the mechanism that turns a small, recoverable problem
into a large, self-sustaining one.

The context in which this occurs almost always has three ingredients present
together. First, a shared downstream resource, a database, a single
microservice, an authentication provider, a payment gateway, that many
independent callers depend on. Second, a retry policy applied uniformly and
independently by each caller, with no coordination or shared state between
callers about how many retries are already in flight. Third, a failure
trigger that hits many callers at once, whether a deploy, a network
partition, a capacity limit, a certificate expiry, or the downstream service
itself briefly degrading under ordinary load.

When the downstream starts failing a fraction of requests, every caller,
independently and simultaneously, decides to retry. If retries are immediate
or on a fixed short delay, the retry traffic adds to the already struggling
downstream's load rather than easing it. The downstream degrades further,
more requests fail, more retries fire, and the system enters a feedback loop
that does not resolve itself even after the original trigger is gone,
because the retry traffic alone is now sufficient to keep the downstream
overloaded. The Google SRE book's worked example makes the arithmetic
explicit. A backend rejecting requests at 100 queries per second under an
immediate-retry policy sees its total incoming rate climb to 200, then 300
queries per second within a few seconds, entirely from retries of
already-failed work (Beyer, Jones, Petoff, Murphy, *Site Reliability
Engineering*, chapter 22, verified 2026-08-02).

The pattern is also recognizable in its multi-layer form. A user-facing
request that passes through three internal service hops, each independently
retrying its own downstream call three times on failure, can generate up to
3 cubed, or 27, attempts on the innermost service from a single original
click, and the SRE book's own account of this multiplicative effect reports
it reaching 64 attempts, 4 cubed, at three layers of independent retry
(Beyer, Jones, Petoff, Murphy, chapter 22, verified 2026-08-02). Nobody wrote
27 or 64 retries as a design decision. Each layer's author reasoned locally
about their own call and chose a retry count that looked conservative in
isolation. The storm is an emergent property of composing independently
reasonable local decisions with no global retry budget.

## 3. Forces

**Availability versus load.** A retry improves the apparent availability seen
by a single caller on a single transient failure. The same retry, multiplied
across many callers and many layers, degrades the aggregate load on the
downstream, which is the opposite effect at a larger scale. Retry policy is
therefore not purely a client-side decision. It carries a system-wide
externality that the caller writing the retry loop cannot see and is not
incentivized to account for.

**Latency versus completeness.** Retrying trades added latency for a higher
chance of eventual success. Uncapped or aggressively short retry intervals
minimize added latency per caller at the cost of load on the shared
resource, while longer backoff and retry budgets accept more latency for a
caller to protect the shared resource for everyone.

**Local reasoning versus global effect.** Each individual retry decision,
made by the author of one HTTP client call, is locally sound. Of course a
failed request to a flaky network should be retried. The anti-pattern lives
entirely in the aggregate, which is invisible from any single call site.
This is the central force this pattern balances badly by default. Distributed
systems reward local reasoning during development and punish it during an
incident.

**Recovery speed versus retry pressure.** A downstream service recovering
from an incident needs its load to actually drop so its queues can drain and
its processes can catch up. A population of clients still hammering it with
retries at the exact moment it starts to recover can re-trigger the same
overload before recovery completes, extending an outage that would
otherwise have been short. This is the specific mechanism by which retry
storms convert brief blips into extended outages.

**Simplicity of client code versus coordination cost.** The naive retry loop
is a few lines and requires no shared state. A retry policy that respects a
system-wide budget requires either server-side signaling, a header telling
clients to back off, client-side coordination, a shared token bucket per
process or per fleet, or both. That coordination is real engineering cost
that a team under deadline pressure is tempted to skip, and skipping it is
precisely how the anti-pattern gets shipped.

## 4. Applicability and non-applicability

This is an anti-pattern, so this dimension inverts. It identifies when a
system HAS the retry storm problem, and, separately, when adding retries at
all is the wrong reflex in the first place.

Recognize a retry storm in the wild when:

- A downstream's request volume climbs sharply during and after an incident,
  even though the number of distinct user actions or upstream triggers did
  not climb proportionally. The extra volume is retries, not new work.
- The downstream's error rate stays high well after the triggering
  fault, a deploy, a brief network blip, has cleared, because the ongoing
  retry volume alone is enough to keep it overloaded.
- Multiple independent services each retry the same failed call three or
  more times with no coordination, and no single team owns or can see the
  combined retry rate hitting the shared dependency.
- Retries are issued on a fixed short interval, or with no jitter, so waves
  of retries arrive synchronized rather than spread over time.
- There is no retry budget, no circuit breaker, and no server-side signal,
  a Retry-After header, a load-shedding response, that clients respect.

A system is exposed to the risk of a retry storm, even without one having
happened yet, when a retry policy is added to client code with no explicit
answer to how many callers exist, what the maximum combined retry rate they
could produce is, and what happens to the downstream if all of them retry at
once. If nobody on the team can answer that, the system is carrying latent
retry storm risk.

Retrying at all is the wrong default, independent of storm risk, when:

- The failed operation is not idempotent and no idempotency key or
  equivalent safeguard exists. Retrying a non-idempotent write risks
  duplicate side effects, a duplicate charge, a duplicate email, a duplicate
  order, that are a worse outcome than the original failure. Stripe's API
  documentation states this precisely, that idempotency keys "enable safe
  retries of a request", explicitly tying safe retry to the presence of the
  key, not merely to the retry loop (Stripe, "Idempotent requests",
  https://docs.stripe.com/api/idempotent_requests, verified 2026-08-02).
- The error is a client error rather than a transient server or network
  error. Retrying an HTTP 400 Bad Request, a validation failure, or an
  authorization failure will fail identically every time and only adds load
  and latency with zero chance of success. AWS SDK retry classification
  explicitly excludes these. ValidationException and similar codes are
  classified non-retryable and returned to the caller immediately rather
  than retried (AWS, "Retry behavior", AWS SDKs and Tools Reference Guide,
  https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html,
  verified 2026-08-02).
- The caller has no deadline or the retry would exceed the caller's own
  deadline. Retrying past the point where the result is still useful to the
  original caller wastes downstream capacity on work whose answer will be
  discarded.
- A human is present and can decide better than an automatic retry can, for
  example a payment declined for insufficient funds, where retrying the
  identical request will not change the outcome and only the human changing
  something, a different card, will.

## 5. Structure

The retry storm anti-pattern names a system-level failure mode, not a single
class diagram, but its structure can still be described in terms of the
recurring participants that produce it.

**Caller population.** A set of independent processes, each running client
code that issues requests to the same downstream and each running its own
retry logic in isolation. The defining structural property is that this
population has no shared state. No caller knows how many retries any other
caller has already sent or is about to send.

**Naive retry policy.** The logic embedded in each caller that decides,
locally, whether and when to retry a failed call. In the anti-pattern's
canonical shape this policy has three specific defects, each independently
sufficient to enable a storm and commonly found together. No backoff, the
same delay, or no delay, between attempts. No jitter, every caller computes
the identical delay from the identical failure, so retries stay synchronized
across the whole population. No bound, either an unlimited retry count, or a
bound so high it is functionally unlimited under sustained failure.

**Shared downstream resource.** The single dependency, database, service, or
gateway that the entire caller population targets. Its finite capacity is
the resource the retry storm exhausts. Its behavior under overload, whether
it degrades gracefully by shedding load or degrades catastrophically by
falling over, determines how survivable a given storm is.

**Failure trigger.** The event that causes an initial wave of failures large
enough to seed the storm. A deploy, a certificate rotation, a capacity
limit, a network partition, or ordinary tail-latency variance crossing a
timeout threshold for many callers near-simultaneously.

**Feedback loop.** The structural core of the anti-pattern, that retry
traffic adds to the load that caused the original failures, which produces
more failures, which produces more retries. This loop is self-sustaining
once it starts, independent of whether the original trigger persists, which
is the property that makes a retry storm categorically different from a
normal transient failure and is the reason it deserves its own name rather
than being filed under generic overload.

## 6. ASCII structure diagram

```
  Caller population (no shared state between callers)
  +----------+  +----------+  +----------+       +----------+
  | Caller A |  | Caller B |  | Caller C |  ...   | Caller N |
  +----+-----+  +----+-----+  +----+-----+       +----+-----+
       |             |             |                  |
       | each runs its own local retry policy.
       | no backoff / no jitter / no bound
       v             v             v                  v
  +---------------------------------------------------------+
  |            Shared downstream resource (finite)          |
  |   e.g. one database, one auth service, one gateway      |
  +---------------------------------------------------------+
       ^ failures cause more retries
       |
       +--- initial failures caused by  deploy / partition /
            capacity limit / latency spike near a timeout
```

## 7. Dynamics

```
t=0    Downstream is at capacity, rejecting 10% of requests
       (a normal, survivable degradation on its own).

t=0    Every caller whose request failed retries immediately,
       with no jitter, so the retries land in the SAME instant
       as t=0's ordinary next-second traffic.

t=1s   Downstream now receives  100% of ordinary traffic
                               + 100% of t=0's failed 10% retried
       Effective load has grown. Rejection rate climbs above 10%.

t=2s   The larger population of t=1 failures retries again,
       still synchronized, still uncapped.
       Rejection rate climbs further.

t=Ns   Rejection rate has grown from 10% toward saturation.
       The ORIGINAL trigger (a deploy blip, a partition) may
       already be resolved. The storm now sustains itself.
       Retry traffic alone is sufficient load to keep the
       downstream rejecting requests.

       ------------------- without intervention -------------
       the loop does not self-terminate, it continues until
       either callers give up (timeout/circuit open) or an
       operator manually sheds load / restarts / scales up.

       ------------------- with backoff + jitter + budget ---
t=0    10% fail. Each caller schedules its retry at a RANDOM
       point inside an exponentially growing window, and only
       if its local retry budget still has tokens.
t=1s   Retries are spread across the window, not synchronized.
       Added load is smoothed, not spiked. Rejection rate holds
       near 10% or recovers as the trigger clears.
t=Ns   Budget-exhausted callers fail fast instead of retrying,
       further reducing pressure on the downstream exactly when
       it most needs load reduction to recover.
```

## 8. Implementation variants

The anti-pattern has one core shape, but it shows up in several concrete
guises depending on where the missing safeguard lives.

**No-backoff variant.** The simplest and most common form, a for loop that
retries N times with zero delay or a small fixed delay between attempts.
This is frequently written by a developer copying a "retry this flaky call"
example from a forum post or an early draft of internal code, without
carrying the backoff logic along with it. It produces the fastest, most
severe storms because there is effectively no time between the failure and
the retry for the downstream's queues to drain.

**Synchronized-backoff variant, missing jitter.** The code does
exponentially increasing delays, which looks correct in isolation, but every
caller computes the identical delay from the identical failure event
because there is no randomization. The population's retries remain
phase-locked, the whole herd backs off together and then retries together,
producing periodic spikes rather than a smooth trickle. This is the specific
failure mode Brooker's AWS post targets by name, contrasting a pure
exponential backoff strategy against several jittered variants, and finding
that "Full Jitter" and "Decorrelated Jitter" substantially reduce the work
needed for clients to succeed under contention compared to backoff with no
jitter at all (Marc Brooker, "Exponential Backoff And Jitter", verified
2026-08-02).

**Unbounded-retry variant.** Backoff and jitter are both present, but there
is no cap on the number of attempts, or the cap is effectively infinite, a
very large number, or "retry until success". Under a sustained outage this
still produces a storm, just a slower-building one, because the population
never stops adding retry pressure regardless of how long the downstream has
been struggling.

**Multi-layer variant.** Each individual service in a call chain implements
a correct, bounded, jittered retry policy for its own immediate downstream,
but no layer is aware of how many retries have already happened upstream in
the same logical request. The combinatorial multiplication described in
section 2, N retries per layer across L layers yielding up to N to the L
attempts on the innermost service, is this variant's signature, and it can
occur even when every individual retry policy, viewed in isolation, looks
textbook-correct.

**Server-blind variant.** The client-side retry policy is well designed, but
the server gives it no information to work with, no Retry-After header, no
distinct status code for "you are being throttled, back off longer" versus
"this was a one-off blip, retry normally". AWS SDK documentation notes
exactly this distinction by classifying ThrottlingException-family errors
with a much longer base backoff, 1,000 ms, than ordinary transient errors
like RequestTimeout, 50 ms base, precisely because throttling signals a
different, longer-lived condition that deserves a different response curve
(AWS, "Retry behavior", verified 2026-08-02). A server that returns
undifferentiated 500s for both cases denies well-behaved clients the
information they need to avoid contributing to a storm.

## 9. Known production uses

**AWS SDKs, standard and adaptive retry modes.** Every current-generation AWS
SDK implements exponential backoff with full jitter by default, standard
mode, computing each retry delay as random(0, 1) times min(cap, base times
2 raised to the retry number), and layers a token-bucket retry quota on top
so that once failures become widespread the SDK stops retrying and fails
fast rather than continuing to add retry load. Adaptive mode goes further
and can delay or block even the initial request when a client-side rate
limiter detects sustained throttling on a single resource (AWS, "Retry
behavior", AWS SDKs and Tools Reference Guide,
https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html,
verified 2026-08-02). This is a direct, named, load-bearing engineering
response to the retry storm problem, shipped as the default behavior for
every AWS service call from every supported language.

**gRPC retry throttling.** The gRPC framework's retry policy configuration
includes a retryThrottling block with maxTokens and tokenRatio parameters.
Unsuccessful calls decrement a per-server token count and successful calls
increment it, and once the token count falls below half of maxTokens the
client pauses retries until the count recovers. gRPC also applies jitter of
roughly plus or minus 20 percent to the backoff delay "to avoid hammering
servers at the same time from a large number of clients" (gRPC Authors,
"Retry Design", gRPC documentation, https://grpc.io/docs/guides/retry/,
verified 2026-08-02). This is a protocol-level, cross-language mechanism
specifically named and documented as a defense against exactly this
anti-pattern.

**Envoy proxy retry budgets.** Envoy's circuit breaker configuration exposes
a retry budget at the cluster level, tracked separately from the general
connection and request circuit breakers, so that the proportion of a
cluster's total request volume made up of retries is bounded independent of
how many individual retryable errors occur (Envoy Proxy documentation,
"Router filter", https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/router_filter,
verified 2026-08-02, referencing the circuit_breaker.proto retry_budget
field). Envoy sits as a sidecar or edge proxy in front of a very large
population of production microservice deployments, making this budget a
widely deployed, infrastructure-level guard against the storm.

**Netflix Hystrix, circuit breaking as a companion defense.** Hystrix, the
resilience library Netflix built and open-sourced for its microservice
architecture, documents that it trips "a circuit-breaker to stop all
requests to a particular service for a period of time" once an error
threshold is exceeded, using per-dependency thread pools so a struggling
dependency cannot exhaust resources shared across the rest of the caller's
codebase (Netflix, Hystrix Wiki, https://github.com/Netflix/Hystrix/wiki,
verified 2026-08-02). Hystrix itself is now in maintenance mode, with
Netflix recommending newer resilience libraries for new work, but it remains
the canonical, most widely cited named production system demonstrating that
a retry storm's twin defense, stop retrying entirely once a dependency is
confirmed unhealthy, is a first-class architectural component rather than an
afterthought, and its design vocabulary, circuit breaker, bulkhead, fail
fast, is now standard across the industry regardless of which specific
library implements it.

**Google, retry budgets in the SRE book's stated practice.** The Google SRE
book describes retry budgets as an operational practice Google runs in
production, not a hypothetical. It gives a concrete recommendation drawn
from operating systems at Google's scale, that a server-wide, or even
global, limit on the number of retries allowed per minute is one way to
avoid the runaway effect, so that once the limit is reached the caller stops
retrying and returns the error to its own caller instead, alongside deadline
propagation and per-layer retry suppression to stop the multiplicative
effect across service hops (Beyer, Jones, Petoff, Murphy, *Site Reliability
Engineering*, chapter 22, "Addressing Cascading Failures", verified
2026-08-02).

## 10. Consequences

Positive consequences, of recognizing and fixing the anti-pattern, what a
correct retry policy buys.

- A well-designed retry policy still gives individual callers resilience to
  genuinely transient faults, which is the legitimate benefit the naive
  version was reaching for. Fixing the anti-pattern does not mean removing
  retries, it means bounding them.
- Jittered backoff spreads retry load over time instead of concentrating it,
  which measurably reduces the total work needed for the population to
  succeed under contention. Brooker's data shows Full Jitter and
  Decorrelated Jitter "reducing client work by more than half" compared to
  backoff with no jitter in a high-contention scenario with 100 competing
  clients (Brooker, "Exponential Backoff And Jitter", verified 2026-08-02).
- A retry budget, whether client-side, AWS's token bucket, or server-side,
  Envoy's, gRPC's, gives the system an explicit, tunable ceiling on how much
  of total traffic can be retries, which is a number an operator can reason
  about and alert on, unlike an uncapped policy that has no such number.
- Failing fast once a budget is exhausted returns control to the caller
  quickly, which frees client-side threads, connections, and timeout budget
  that would otherwise be consumed waiting on retries very unlikely to
  succeed, a benefit AWS's documentation names explicitly as the reason its
  standard retry mode returns an error immediately rather than continuing to
  retry once the quota depletes (AWS, "Retry behavior", verified 2026-08-02).

Negative consequences, of the anti-pattern itself, left uncorrected.

- A downstream's error rate can remain high, or the downstream can
  remain fully unavailable, well after the original triggering fault has
  cleared, because the retry traffic alone sustains the overload. This
  directly extends the duration of user-visible incidents beyond what the
  original fault would have caused on its own.
- Combinatorial retry multiplication across service layers means that
  correctly bounding retries at each individual layer is not sufficient to
  bound the total attempts a single user action produces on the innermost
  system, so a system can look correct at every code review and still be
  exposed to a large multiplier at the architecture level.
- Capacity planning becomes unreliable, because observed traffic during an
  incident includes an unknown, non-constant multiple of retry traffic on
  top of genuine work, making it hard to size the downstream correctly or
  to distinguish "we need more capacity" from "we need to stop retrying so
  much".
- Non-idempotent operations retried during a storm can produce duplicate
  side effects at exactly the moment operators are least able to notice and
  correct them, because attention during an incident is on restoring
  availability rather than auditing for duplicates.
- Postmortems for these incidents are harder to write and to learn from,
  because the root cause, a small trigger, is easy to find, but the reason
  the incident lasted as long as it did, self-sustaining retry load, is
  invisible in the metrics unless retries were explicitly instrumented
  separately from first attempts.

## 11. Failure modes and misuse

Symptom. A downstream service's request rate spikes far above its normal
baseline during an incident, with no corresponding spike in genuine upstream
user activity.
Cause. Retries from a caller population, either uncoordinated or with no
retry budget, are adding to first-attempt traffic rather than replacing it.
Fix. Instrument retries with a distinct metric or label separate from first
attempts, so this becomes directly observable, then introduce a client-side
or server-side retry budget sized as a fraction of steady-state traffic.

Symptom. An incident's error rate stays high for many minutes after the
underlying cause, such as a bad deploy, has already been rolled back.
Cause. The retry storm has become self-sustaining. The retries themselves are
now the load keeping the downstream saturated, independent of the original
trigger.
Fix. Shed load explicitly, either by having the downstream return an
aggressive rejection response the clients respect, a Retry-After header, a
503 with backoff hint, or by an operator temporarily disabling retries at
the client fleet level until the queue drains, then re-enabling with jitter.

Symptom. Retries appear to arrive in periodic bursts rather than a smooth
trickle, visible as a sawtooth pattern in the downstream's request-rate
graph.
Cause. Exponential backoff is present but jitter is missing, so every caller
that failed at the same moment computes the identical delay and retries in
lockstep with every other caller.
Fix. Add randomization to the computed delay, per Brooker's Full Jitter
formula, delay equals a random value between 0 and min(cap, base times 2 to
the power of attempt), which decorrelates callers that started retrying at
the same instant (Brooker, "Exponential Backoff And Jitter", verified
2026-08-02).

Symptom. A single slow user action, traced end to end, shows dozens of
attempts hitting the innermost database, far more than any one service's
retry count would suggest.
Cause. Multiple independent layers in the call chain each retry their own
downstream call, with no shared knowledge of retries already performed by
an outer layer, producing multiplicative growth in total attempts.
Fix. Propagate a deadline and, where feasible, a retry-attempt count or a
"do not retry, this was already retried upstream" signal down the call
chain, and consider retrying at only one layer, typically the outermost
layer closest to the user, rather than at every hop.

Symptom. After adding retries to a payment or order-creation endpoint, the
team starts seeing duplicate charges or duplicate orders correlated with
periods of higher latency.
Cause. The retried operation is not idempotent, so a request that actually
succeeded on the server but whose response was lost or delayed gets retried
and executes a second time.
Fix. Require an idempotency key on the request, generated once by the
client and reused across every retry of that same logical operation, so the
server can recognize and safely return the original result instead of
repeating the side effect, as documented in Stripe's idempotent requests API
(Stripe, "Idempotent requests", verified 2026-08-02).

Symptom. Retries continue for a very long time on a call whose result the
original caller no longer needs, because the caller itself already gave up
or timed out higher up the stack.
Cause. The retry loop has no awareness of the caller's own deadline and
keeps attempting past the point where the answer is useful, wasting the
downstream's capacity on discarded work.
Fix. Bind the total retry loop, including all backoff delays, to the
caller's remaining deadline, and abandon the retry loop the moment that
deadline is exceeded rather than the moment the retry count is exhausted.

Misuse. Treating "we added exponential backoff" as sufficient without
jitter or a budget. Backoff alone slows the individual caller down but does
not desynchronize the population. A population of callers all backing off
in lockstep still produces periodic full-strength bursts, just spaced
further apart than a no-backoff storm. Teams sometimes stop at this point
believing the problem is solved, because the average retry rate looks
lower in a coarse-grained dashboard, while the burst peaks, which are what
actually overload a downstream, remain just as sharp.

Misuse. Setting a very large retry count as a substitute for a real retry
budget. A cap of, for example, 50 retries with backoff looks bounded on
paper, but if every caller in a population of thousands independently
exhausts 50 retries during a sustained outage, the aggregate retry volume
is still enormous. A per-caller cap does not protect the shared downstream,
only a fleet-wide or server-side budget does.

## 12. Trade-off matrix

| Dimension | No retry at all | Naive retry (retry storm risk) | Exponential backoff + jitter, no budget | Backoff + jitter + retry budget | Circuit breaker (bulkhead pattern) |
|---|---|---|---|---|---|
| Resilience to a single transient fault | None, caller fails on any blip | High for one caller | High for one caller | High for one caller | High once tripped open, but adds one round-trip of detection lag |
| Risk of a widespread failure growing worse | None, no retries to grow it | Severe, this is the anti-pattern | Reduced but not eliminated, sustained failure can still storm | Low, budget caps aggregate retry volume regardless of trigger duration | Low, stops sending new requests entirely once threshold trips |
| Implementation complexity | Trivial | Trivial, which is exactly the trap | Moderate, needs a jitter source and a delay cap | Higher, needs shared or server-communicated budget state | Higher, needs failure-rate tracking, half-open probing, and per-dependency isolation |
| Coordination required across callers | None | None | None | Some, for a shared budget, none if server-enforced via headers or throttling responses | None per caller, but tuning thresholds requires knowing the dependency's real capacity |
| Added latency on the happy path | Zero | Zero | Zero | Zero | Zero, and can be lower during an outage since it fails immediately instead of waiting on a doomed retry |
| Behavior once the downstream is fully saturated | Fails fast, no help but no harm | Keeps adding load, prolongs the outage | Slows the addition of load but eventually can still contribute | Stops contributing once budget is exhausted, actively helps recovery | Stops contributing entirely, actively helps recovery, and probes for recovery automatically |

Circuit breaker and retry budget are not mutually exclusive with backoff and
jitter. In mature production systems, see section 9, they are typically
layered together, with backoff and jitter shaping each individual retry's
timing and a budget or breaker bounding the aggregate.

## 13. Related and incompatible patterns

**Circuit Breaker.** The most closely related pattern and the most common
companion fix. Where a retry budget limits how much of the traffic can be
retries, a circuit breaker goes further and stops sending any traffic, first
attempts included, to a dependency once it is confirmed unhealthy, then
periodically probes to detect recovery. The two compose naturally. Retries
handle brief, likely-transient blips, and the circuit breaker handles
sustained, likely-systemic failure, taking over once a threshold of retry
failures is crossed.

**Bulkhead.** Isolates the resources, threads, connections, memory, used to
call one dependency from the resources used to call every other dependency,
so a retry storm against one downstream cannot exhaust resources needed for
calls to unrelated, healthy downstreams. Hystrix's per-dependency thread
pools are a concrete instance of bulkhead applied specifically to contain
the blast radius of exactly this kind of storm.

**Timeout.** A prerequisite for any sane retry policy, not an optional
extra. Without a bounded per-attempt timeout, a caller cannot know when an
attempt has failed and should be retried versus is merely slow, and a
caller with no timeout at all cannot bound the total time or resource cost
of its retry loop regardless of how well the retry count or backoff is
tuned.

**Chatty I/O (18-anti-patterns).** A related anti-pattern where a system
issues far more network round trips than necessary for its actual work.
Retry storms are a special case of chatty I/O triggered specifically by
failure handling rather than by the steady-state call pattern, and the same
family of fixes, batching, reducing round trips, applies conceptually,
though the retry storm's fix is about bounding failure-triggered traffic
rather than reducing successful-path traffic.

**Cascading Failure.** Retry storm is one specific, extremely common
mechanism by which a cascading failure develops and sustains itself. Not
every cascading failure is caused by a retry storm, resource exhaustion
from a memory leak, for example, cascades without any retry involved, but a
large share of documented, publicly discussed distributed systems incidents
that escalate from one degraded service to a whole platform being down
involve retry-driven growth in request volume as a contributing or
dominant factor.

**Idempotent Receiver, Idempotency Key.** Not a retry pattern itself but a
required safety property for any retry to be sound when the retried
operation has side effects. A retry storm compounds the damage of a
missing idempotency guarantee, because it multiplies the number of
duplicate side effects produced, but the two problems are distinct. A
system can have a perfectly bounded, jittered, budgeted retry policy and
still corrupt data on every single retry if the underlying operation is not
idempotent.

No pattern in this catalog is structurally incompatible with fixing a
retry storm. The fix composes with essentially any architecture, because it
constrains client-side failure handling behavior rather than changing the
shape of the system being called.

## 14. Refactoring path in and out

Path in, how a retry storm gets introduced, so it can be recognized in
review.

1. A developer notices a call site failing intermittently due to a flaky
   network or a briefly overloaded dependency.
2. They wrap the call in a loop that retries a fixed number of times,
   typically copied from a quick example or written from memory, with no
   delay or a small fixed delay between attempts. This closes the immediate
   ticket and the flaky failure appears resolved in testing.
3. The change ships without anyone asking how many other services or
   processes call the same downstream, or what happens if all of them hit a
   failure at the same moment.
4. Months later, an unrelated trigger, a deploy, a certificate expiry, a
   traffic spike, causes the downstream to briefly degrade for every caller
   simultaneously, and the previously invisible retry loop now grows that
   brief degradation into a sustained outage.

Path out, how to correct an existing retry storm risk, in order.

1. Instrument retries separately from first attempts in metrics, so the
   aggregate retry volume against each shared downstream becomes visible
   before, not only during, an incident.
2. Audit every retry loop for the three defects named in section 5, missing
   backoff, missing jitter, missing bound. Add exponential backoff with
   full jitter to any loop lacking it, using AWS's formula as a concrete
   reference, delay equals a random value between 0 and min(cap, base times
   2 to the power of attempt) (AWS, "Retry behavior", verified 2026-08-02).
3. Classify errors before retrying. Only retry errors known to be
   transient or throttling-related, return client errors and validation
   failures to the caller immediately without a retry attempt, matching
   the classification approach AWS SDKs apply by default.
4. Add a retry budget, either as a client-side token bucket shared across a
   process, or better, communicated across a fleet, or by relying on a
   server-side or proxy-level budget such as Envoy's cluster-level retry
   budget or gRPC's per-server retry throttling configuration, so the
   aggregate retry rate has an enforced ceiling independent of how many
   individual callers exist.
5. For any retried operation with side effects, add or confirm an
   idempotency key so a retry of a request that actually succeeded server
   side cannot duplicate the effect.
6. For multi-layer call chains, decide explicitly which single layer owns
   retry responsibility for a given failure class, and suppress retries at
   the other layers for that failure class, to prevent the multiplicative
   effect described in section 2.
7. Where the downstream's failure mode under sustained overload is severe,
   it falls over rather than gracefully shedding load, add a circuit
   breaker in front of the retry logic so that once failures cross a
   threshold, the system stops sending any traffic, including first
   attempts, rather than continuing to retry against a confirmed-unhealthy
   dependency.

Removing retries entirely is rarely the correct end state. The goal of this
refactoring path is a bounded, jittered, idempotency-safe retry policy
backed by an enforced budget, not the absence of retries.

## 15. Testing and verification

Testing for this anti-pattern is unusual among the entries in this catalog
because the defect is a property of aggregate, multi-process behavior under
failure, not something a conventional unit test targeting a single retry
loop in isolation can fully capture.

Unit level. A retry loop's individual behavior is straightforward to test in
isolation. Inject a fake clock and a fake downstream that fails N times
then succeeds, and assert the loop makes the expected number of attempts,
respects the expected delay bounds between them, and stops retrying on a
non-retryable error class. This confirms the loop's local correctness but
says nothing about storm risk, because storm risk is emergent across many
instances of this loop running at once.

Fault injection at the dependency boundary. Testing that a caller survives
a downstream returning errors requires a test double or a fault injection
proxy that can simulate a downstream returning a controlled error rate, a
controlled latency distribution, and, ideally, a Retry-After style header,
so the retry logic's response to each condition can be observed directly
rather than inferred.

Load testing with a shared simulated downstream. The storm itself can only
be reproduced by running many concurrent instances of the caller against
one shared, rate-limited or intentionally overloaded test downstream, and
measuring the downstream's actual received request rate over time as
failures are introduced. A useful concrete assertion here is to inject a
fixed period of higher error rate at the simulated downstream, then
measure how long the downstream's request rate takes to return to baseline
after the injected fault is removed. A system without a retry budget will
show request rate remaining high well past the fault's removal, a
system with an effective budget will show it returning to baseline
promptly, close to the fault's own duration.

Chaos and game-day exercises. Because the trigger for a real-world storm is
frequently a whole-fleet event, a deploy, a certificate expiry, a shared
infrastructure blip, verifying resilience realistically benefits from
exercises that inject the trigger at the infrastructure level, killing a
percentage of a downstream's instances, injecting network latency between
an entire availability zone and a dependency, rather than only at a single
caller's test setup, so that synchronization effects across the whole
caller population are actually present in the test.

Budget exhaustion path. Explicitly test the behavior once a retry budget is
exhausted. Confirm the caller returns an error promptly rather than
hanging, confirm it does not silently fall back to unbounded retrying, and
confirm the budget itself recovers correctly once the downstream starts
succeeding again, matching AWS's documented behavior where a successful
first-try request restores one token and a successful retry restores the
tokens its own attempt consumed (AWS, "Retry behavior", verified
2026-08-02).

## 16. Observability signals

Retries as a distinct, labeled metric. The single most important signal is
having "attempt is a retry" as a queryable dimension separate from total
request volume. Without this, a retry storm is indistinguishable in
metrics from a genuine, organic traffic spike, and operators will
misdiagnose the incident as a capacity problem rather than a retry-policy
problem.

Retry rate as a ratio of total requests. Track retries divided by total
attempts, per downstream, per caller service. A healthy system's ratio
stays low and roughly constant. A ratio that climbs sharply during an
incident and stays high after the initiating fault would normally have
cleared is the clearest single indicator that the retry policy itself is
now the dominant factor sustaining the incident.

Retry budget token level. Where a token-bucket style budget is in use,
expose its current level as a gauge. A budget sitting near zero for a
sustained period means the system is actively suppressing retries it would
otherwise send, which is valuable both as an early warning that a
dependency is unhealthy and as confirmation the safeguard is doing its job
rather than being silently bypassed.

Downstream saturation signals correlated with client retry timing. Graph
the downstream's queue depth, error rate, or latency percentile alongside
the calling population's retry attempt timestamps. A visible periodic
correlation, spikes in downstream load lining up with computed backoff
intervals, is the direct fingerprint of a missing-jitter variant of the
anti-pattern, see section 8, and is difficult to see without both signals
plotted on the same timeline.

Time-to-recovery after fault clearance. Measure the interval between when
an injected or observed fault at the downstream is resolved and when the
downstream's error rate actually returns to baseline. A large gap between
these two points, longer than the round trip time of a single retry, is
strong evidence that retry traffic, not the original fault, is what is
prolonging the incident.

Per-layer retry attribution in distributed traces. In a multi-layer call
chain, distributed tracing that marks each span as either a first attempt
or a retry, and at which layer, makes the multiplicative growth effect
from section 2 directly visible in a single trace, showing an operator
exactly how many total attempts one user action produced on the innermost
service and at which layers those attempts originated.

## 17. Security and privacy implications

The security surface of this anti-pattern is primarily availability-related
rather than confidentiality- or integrity-related, but two concrete
implications are worth naming plainly rather than left implied.

A retry storm is functionally indistinguishable, from the downstream's
perspective, from a distributed denial-of-service condition, even though it
originates entirely from the system's own legitimate clients rather than
from an attacker. A downstream's rate-limiting and abuse-detection
systems, if they exist, may not be tuned to recognize this pattern as
internal rather than malicious, and an operator responding to what looks
like a DoS condition may reasonably, and correctly, apply the same
emergency mitigation, aggressive rate limiting, temporary blocking, that
would be applied to an actual attack, which is itself a useful and
appropriate response regardless of the traffic's origin.

Conversely, and this is engineering judgement rather than a sourced claim,
the mechanism a retry storm relies on, many independent clients hammering a
shared resource in response to a failure signal, is structurally similar
enough to a distributed denial-of-service technique that an attacker who
can trigger a small number of transient failures against a target's
dependency, for example by briefly overloading a shared upstream the
attacker can also reach, may be able to turn the target's own legitimate,
well-intentioned retry logic against it, converting a small attack
investment into a much larger resulting load, in the same spirit as a
protocol reflection attack that abuses a system's own retry or response
behavior to multiply a small input into much larger output traffic, rather
than sending overwhelming traffic directly.

On the privacy and data-handling side, the concrete implication documented
in production idempotency systems is the one in section 11. A retry storm
interacting with non-idempotent operations can produce duplicate records
containing personal data, duplicate notifications sent to a person, or
duplicate financial transactions, none of which are confidentiality
breaches but all of which are data-correctness incidents with real
customer and compliance impact, and this is a documented reason
idempotency keys are required, not merely recommended, for retried write
operations in payment APIs such as Stripe's (Stripe, "Idempotent
requests", verified 2026-08-02).

## 18. References

1. Marc Brooker, "Exponential Backoff And Jitter", AWS Architecture Blog,
   2015. https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
   Verified 2026-08-02.
2. Betsy Beyer, Chris Jones, Jennifer Petoff, Niall Richard Murphy, editors,
   *Site Reliability Engineering. How Google Runs Production Systems*,
   O'Reilly, 2016, chapter 22, "Addressing Cascading Failures".
   https://sre.google/sre-book/addressing-cascading-failures/
   Verified 2026-08-02.
3. AWS, "Retry behavior", AWS SDKs and Tools Reference Guide.
   https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html
   Verified 2026-08-02.
4. gRPC Authors, "Retry Design", gRPC documentation.
   https://grpc.io/docs/guides/retry/
   Verified 2026-08-02.
5. Envoy Proxy documentation, "Router filter" (HTTP filters), including the
   cluster circuit breaker retry_budget configuration field.
   https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/router_filter
   Verified 2026-08-02.
6. Netflix, Hystrix Wiki.
   https://github.com/Netflix/Hystrix/wiki
   Verified 2026-08-02. Project is in maintenance mode, cited for its
   documented circuit-breaker rationale, not as an active recommendation.
7. Stripe, "Idempotent requests", Stripe API Reference.
   https://docs.stripe.com/api/idempotent_requests
   Verified 2026-08-02.

## Code examples

The retry storm anti-pattern is best shown as a contrast. the naive version
that causes it, and a corrected version applying exponential backoff, full
jitter, error classification, and a bounded retry budget. Three languages
are shown. TypeScript, Python, and Go. Each corrected sample is a runnable,
self-contained simulation using an in-process fake downstream so the storm
and its fix can be observed without a real network dependency.

### TypeScript

```typescript
// retry-storm.ts
// Simulates a population of callers hitting a shared, capacity-limited
// downstream, contrasting a naive retry loop against a corrected one.

interface Downstream {
  call(): boolean; // true = success, false = rejected (overloaded)
}

// A downstream that rejects a request whenever concurrent load exceeds
// its capacity. This stands in for a real overloaded backend.
class CapacityLimitedDownstream implements Downstream {
  private inFlight = 0;
  totalAttempts = 0;
  totalRejections = 0;

  constructor(private readonly capacity: number) {}

  call(): boolean {
    this.totalAttempts++;
    this.inFlight++;
    const ok = this.inFlight <= this.capacity;
    if (!ok) this.totalRejections++;
    this.inFlight--;
    return ok;
  }
}

// ANTI-PATTERN: no backoff, no jitter, no budget.
function naiveRetry(downstream: Downstream, maxAttempts: number): boolean {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    if (downstream.call()) return true;
    // no delay at all between attempts
  }
  return false;
}

// FIX: exponential backoff with full jitter, plus a shared retry budget
// (a simple token bucket) that all callers draw from.
class RetryBudget {
  private tokens: number;
  constructor(private readonly capacity: number) {
    this.tokens = capacity;
  }
  tryConsume(): boolean {
    if (this.tokens <= 0) return false;
    this.tokens -= 1;
    return true;
  }
  refund(amount: number) {
    this.tokens = Math.min(this.capacity, this.tokens + amount);
  }
}

function fullJitterDelayMs(baseMs: number, capMs: number, attempt: number): number {
  const exp = Math.min(capMs, baseMs * 2 ** attempt);
  return Math.random() * exp;
}

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function correctedRetry(
  downstream: Downstream,
  budget: RetryBudget,
  maxAttempts: number,
  baseMs: number,
  capMs: number
): Promise<boolean> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    if (attempt > 0 && !budget.tryConsume()) {
      // budget exhausted: fail fast instead of adding more load
      return false;
    }
    if (downstream.call()) {
      if (attempt > 0) budget.refund(1);
      return true;
    }
    if (attempt < maxAttempts - 1) {
      await sleep(fullJitterDelayMs(baseMs, capMs, attempt));
    }
  }
  return false;
}

async function main() {
  const CALLERS = 40;
  const CAPACITY = 8; // downstream can only handle 8 concurrent calls

  // Scenario A: naive retry storm
  const naiveDownstream = new CapacityLimitedDownstream(CAPACITY);
  let naiveSuccesses = 0;
  for (let i = 0; i < CALLERS; i++) {
    if (naiveRetry(naiveDownstream, 5)) naiveSuccesses++;
  }
  console.log(
    `Naive: attempts=${naiveDownstream.totalAttempts} ` +
      `rejections=${naiveDownstream.totalRejections} ` +
      `successes=${naiveSuccesses}/${CALLERS}`
  );

  // Scenario B: corrected retry with a shared budget of 20 retry tokens
  const correctedDownstream = new CapacityLimitedDownstream(CAPACITY);
  const budget = new RetryBudget(20);
  let correctedSuccesses = 0;
  const jobs = Array.from({ length: CALLERS }, () =>
    correctedRetry(correctedDownstream, budget, 5, 10, 200)
  );
  const results = await Promise.all(jobs);
  correctedSuccesses = results.filter(Boolean).length;
  console.log(
    `Corrected: attempts=${correctedDownstream.totalAttempts} ` +
      `rejections=${correctedDownstream.totalRejections} ` +
      `successes=${correctedSuccesses}/${CALLERS}`
  );
}

main();
```

### Python

```python
"""retry_storm.py
Demonstrates error classification and a fleet-wide retry budget, the two
safeguards a naive retry loop is missing. Uses a fake downstream so the
example runs with no network access.
"""

import random
import time
from dataclasses import dataclass, field


class NonRetryableError(Exception):
    """A client error. Retrying it can never succeed."""


class TransientError(Exception):
    """A transient failure. Safe to retry with backoff."""


@dataclass
class FlakyDownstream:
    """Fails a fixed fraction of calls with a transient error, and one
    specific input with a permanent, non-retryable error."""

    failure_rate: float
    calls: int = field(default=0)
    retried_failures: int = field(default=0)

    def call(self, request_id: str) -> str:
        self.calls += 1
        if request_id == "bad-input":
            raise NonRetryableError("validation failed, will never succeed")
        if random.random() < self.failure_rate:
            self.retried_failures += 1
            raise TransientError("service temporarily overloaded")
        return f"ok:{request_id}"


class RetryBudget:
    """A simple shared token bucket. Once exhausted, callers fail fast
    instead of adding more retry pressure to the downstream."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.tokens = capacity

    def try_consume(self) -> bool:
        if self.tokens <= 0:
            return False
        self.tokens -= 1
        return True

    def refund(self, amount: int) -> None:
        self.tokens = min(self.capacity, self.tokens + amount)


def full_jitter_delay(base: float, cap: float, attempt: int) -> float:
    exp = min(cap, base * (2 ** attempt))
    return random.uniform(0, exp)


def call_with_retry(
    downstream: FlakyDownstream,
    budget: RetryBudget,
    request_id: str,
    max_attempts: int = 4,
    base_delay: float = 0.01,
    cap_delay: float = 1.0,
) -> str | None:
    for attempt in range(max_attempts):
        if attempt > 0 and not budget.try_consume():
            return None  # budget exhausted, fail fast, do not add load
        try:
            result = downstream.call(request_id)
            if attempt > 0:
                budget.refund(1)
            return result
        except NonRetryableError:
            return None  # never retry a client error
        except TransientError:
            if attempt < max_attempts - 1:
                time.sleep(full_jitter_delay(base_delay, cap_delay, attempt))
    return None


def main() -> None:
    random.seed(7)
    downstream = FlakyDownstream(failure_rate=0.4)
    budget = RetryBudget(capacity=15)

    callers = [f"req-{i}" for i in range(30)] + ["bad-input"]
    successes = 0
    for request_id in callers:
        outcome = call_with_retry(downstream, budget, request_id)
        if outcome is not None:
            successes += 1

    print(f"calls_to_downstream={downstream.calls}")
    print(f"successes={successes}/{len(callers)}")
    print(f"remaining_budget_tokens={budget.tokens}")


if __name__ == "__main__":
    main()
```

### Go

```go
// retry_storm.go
// Shows deadline propagation: a caller's remaining context deadline
// bounds the entire retry loop, so retries never continue past the point
// where the result would already be discarded.
package main

import (
	"context"
	"errors"
	"fmt"
	"math"
	"math/rand"
	"time"
)

var errOverloaded = errors.New("downstream overloaded")

// downstream fails a request whenever more than capacity calls are
// in flight at once, standing in for a real capacity-limited backend.
type downstream struct {
	capacity int
	inFlight int
	attempts int
	rejects  int
}

func (d *downstream) call() error {
	d.attempts++
	d.inFlight++
	defer func() { d.inFlight-- }()
	if d.inFlight > d.capacity {
		d.rejects++
		return errOverloaded
	}
	return nil
}

// fullJitterDelay implements the AWS "full jitter" formula:
// delay = random(0, min(cap, base * 2^attempt))
func fullJitterDelay(base, cap time.Duration, attempt int) time.Duration {
	exp := math.Min(float64(cap), float64(base)*math.Pow(2, float64(attempt)))
	return time.Duration(rand.Float64() * exp)
}

// callWithRetry retries only while the caller's own context deadline has
// not yet passed, so a retry loop never outlives the work it serves.
func callWithRetry(ctx context.Context, d *downstream, maxAttempts int) error {
	var lastErr error
	for attempt := 0; attempt < maxAttempts; attempt++ {
		if ctx.Err() != nil {
			return fmt.Errorf("deadline exceeded before attempt %d: %w", attempt, ctx.Err())
		}
		lastErr = d.call()
		if lastErr == nil {
			return nil
		}
		if attempt < maxAttempts-1 {
			delay := fullJitterDelay(10*time.Millisecond, 500*time.Millisecond, attempt)
			select {
			case <-time.After(delay):
			case <-ctx.Done():
				return fmt.Errorf("deadline exceeded during backoff: %w", ctx.Err())
			}
		}
	}
	return lastErr
}

func main() {
	rand.Seed(7)
	d := &downstream{capacity: 6}

	// A caller with a short overall deadline. The retry loop stops trying
	// once this expires, instead of continuing to add load past the point
	// the result would still matter.
	ctx, cancel := context.WithTimeout(context.Background(), 150*time.Millisecond)
	defer cancel()

	const callers = 25
	successes := 0
	for i := 0; i < callers; i++ {
		if err := callWithRetry(ctx, d, 5); err == nil {
			successes++
		}
	}

	fmt.Printf("attempts=%d rejects=%d successes=%d/%d\n",
		d.attempts, d.rejects, successes, callers)
}
```
