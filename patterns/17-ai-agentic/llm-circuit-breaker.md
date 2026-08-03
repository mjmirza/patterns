---
name: LLM Circuit Breaker
slug: llm-circuit-breaker
family: 17-ai-agentic
category: Reliability
aliases: [AI Gateway Circuit Breaker, Provider Circuit Breaker, Model Circuit Breaker, Deployment Circuit Breaker]
first_described: "Michael T. Nygard 2007, applied to LLM providers by AI gateway vendors circa 2023 to 2025"
maturity: established
related: [circuit-breaker, retry, bulkhead, rate-limiting, output-guardrails, input-guardrails, function-calling, agentic-rag, corrective-rag]
incompatible_with: []
verified: 2026-08-03
---

# LLM Circuit Breaker

## 1. Name, aliases, and lineage

LLM Circuit Breaker is the application of Michael T. Nygard's Circuit Breaker
stability pattern to calls that leave an application and enter a large
language model provider, whether that provider is a hosted API, an inference
endpoint behind a gateway, or a self-hosted model server. The pattern keeps
Nygard's three-state proxy shape, closed, open, half open, and layers three
concerns on top of it that a plain HTTP-facing circuit breaker does not have
to solve. LLM calls carry a per-call dollar cost, a "successful" response can
still be a failure in every sense that matters to the caller, and the calling
code is often an agent loop that can retry the same broken call hundreds of
times inside a single user turn without ever crossing a request boundary a
human would notice.

Nygard named and described the classic Circuit Breaker in *Release It!
Second Edition. Design and Deploy Production-Ready Software*, The Pragmatic
Programmers, 2018, ISBN 9781680502398, in the "Stability Patterns" chapter,
where Circuit Breaker sits alongside Timeouts, Bulkheads, and Steady State as
one of the patterns that stop one failing dependency from dragging the whole
system down with it
([publisher page](https://pragprog.com/titles/mnee2/release-it-second-edition/),
verified 2026-08-03). The Azure Architecture Center's own Circuit Breaker
page gives the canonical three-state description most current libraries and
gateways still follow. Closed routes calls through and counts failures, open
rejects calls immediately and starts a cooldown timer, half open lets a
limited number of probe calls through to test whether the dependency has
recovered
([Azure Architecture Center, Circuit Breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
verified 2026-08-03).

The LLM-specific instantiation of this pattern is not attributed to one
paper or one team. It converged, over roughly two years, out of the vendors
who build gateways and routers that sit in front of one or more model
providers and have to keep serving traffic when one provider degrades. Three
of those products are cited by name in dimension 9 below, each with the
exact behavior it ships and a live-verified source.

There is a naming collision worth stating plainly, because a reader who
searches for "LLM Circuit Breaker" will find both this pattern and an
unrelated one, and confusing the two is a real design mistake. Andy Zou,
Long Phan, Justin Wang, Derek Duenas, Maxwell Lin, Maksym Andriushchenko,
Rowan Wang, Zico Kolter, Matt Fredrikson, and Dan Hendrycks published
"Improving Alignment and Robustness with Circuit Breakers,"
`arXiv:2406.04313`, submitted 6 June 2024 and revised 12 July 2024
(https://arxiv.org/abs/2406.04313, verified 2026-08-03). Their circuit
breakers work by representation engineering. They directly alter the
internal activations a model produces that would otherwise lead to a
harmful completion, interrupting the generation before it happens, rather
than training the model to refuse or filtering its output after the fact.
The reference implementation and training code sit in the GraySwanAI
organization's public repository
(https://github.com/GraySwanAI/circuit-breakers, verified 2026-08-03). That
is a content-safety technique that operates inside one model's forward
pass. It shares the electrical-breaker metaphor and nothing else with the
pattern this entry describes, which operates between a caller and a network
dependency and trips on a failure rate, not on a harmful representation. The
two are not interchangeable, not aliases of each other, and a system that
needs both should build both, because neither one substitutes for the
other. This distinction is developed further in dimension 4.

A second point on naming, this pattern is finer grained than the classic
Circuit Breaker in one specific way. A classic breaker usually protects one
downstream dependency, the payments service, the inventory database. An LLM
gateway routing across several providers, several models within a provider,
and several regional deployments of the same model needs one breaker
instance per distinct target, where a target means the tuple of provider,
model, and deployment or region, because a single provider and model pair
can be healthy in one region and degraded in another, and merging their
failure counts into one breaker hides that difference. The Azure
Architecture Center page names this exact hazard under "resource
differentiation," warning that combining error responses from multiple
independent shards behind one breaker can block access to a shard that is
actually healthy while letting traffic through to one that is not
([Azure Architecture Center, Circuit Breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
verified 2026-08-03). Every production LLM gateway cited in dimension 9
keys its breaker state per target rather than per provider for exactly this
reason.

## 2. Problem and context

A team ships an agent or a chat feature that calls out to a large language
model. At first there is one provider and the failure story is the same
story every HTTP client has always had. The network drops a packet, the
provider returns a 500, the caller retries a few times with backoff and
moves on. That story stops being sufficient the moment any of four things
becomes true, and in a production LLM system all four tend to arrive within
the first few months.

First, the team adds a second provider or a second deployment of the same
model as a fallback, because a single point of failure on a rented inference
endpoint is not acceptable for a user-facing product. Now every failed call
has a decision behind it. Keep hammering the primary, or move to the
fallback, and that decision has to be made consistently across every
request, not by whatever retry loop happens to be closest to the failure.

Second, the team notices that LLM failures do not always look like HTTP
failures. A call can return `200 OK` with an empty completion, a completion
that stops mid sentence because it hit a token limit the caller never
expected, or a stream that opens, delivers zero bytes, and then closes.
None of that trips a naive breaker built to watch for 5xx status codes,
because from the transport's point of view nothing went wrong.

Third, the team notices the cost line on the provider invoice moving in a
way that request volume alone does not explain. An agent stuck retrying a
tool call it can never satisfy, or a router blindly retrying a provider that
is rate limiting every request, pays full price for calls that were never
going to succeed. Unlike a database query or a cache lookup, a rejected or
malformed LLM call is rarely free.

Fourth, the gateway or router the team built to solve the first three
problems is now shared across several internal teams or several customer
tenants, and one tenant's malformed prompts, or one tenant's runaway agent,
starts to affect the latency and availability every other tenant sees on a
provider that is, from the provider's point of view, perfectly healthy.

The context this pattern exists for is the point where an application talks
to one or more LLM providers as remote dependencies it does not control, and
where a single provider or deployment being slow, erroring, rate limiting,
or quietly returning bad output must not be allowed to hang the caller past
an acceptable latency budget, burn budget on calls that will not succeed,
or degrade service to callers whose requests had nothing to do with the
failure. A single call with a timeout and a retry does not solve any of
these three at the fleet level, it solves them one call at a time, and that
is the gap this pattern closes.

## 3. Forces

Some of the weighing below is engineering judgement drawn from how the
production systems in dimension 9 are documented to behave, not a sourced
claim about which force always wins. Where a specific number or default is
stated it is attributed to its source.

Latency under failure pulls against thoroughness. A caller wants to fail
fast rather than wait through a full timeout on a hung provider, but failing
too fast, on the first error rather than a sustained pattern of them, throws
away calls that would have succeeded on the very next attempt. The classic
pattern's answer, a threshold over a window rather than a single failure, is
a direct trade of a little latency, waiting for enough failures to
accumulate, for a lot of stability, not tripping on one blip.

Cost pulls against availability. Once a target's circuit trips, the safest
choice for cost is to stop calling it entirely until the cooldown expires.
The safest choice for availability is to keep probing more aggressively so
recovery is detected sooner. A short cooldown recovers fast but risks
flapping the circuit open and shut on a target that is only intermittently
healthy. A long cooldown protects against flapping but leaves the caller
stuck on a more costly fallback for longer than the outage actually lasted.

Correctness of the failure signal pulls against simplicity. The cheapest
breaker to build watches HTTP status codes. The breaker that actually
protects an LLM-calling system also has to watch the shape of a
"successful" response, an empty completion, a stream that opens and stalls,
a `content_filter` stop reason, and deciding which of those count as target
health failures versus expected business behavior is design work that a
generic resilience library does not do on its own.

Isolation pulls against shared efficiency. A single breaker per provider,
model, and region target, shared across every caller of a gateway, is cheap
to build and reason about, but it lets one tenant's badly formed traffic
count against every other tenant's view of that target's health. Isolating
breaker state per tenant, or per request class, is the correct fix but
multiplies the number of breakers the gateway has to track and adds a
dimension of state that has to be sized and expired.

Consistency across a fleet pulls against operational simplicity. Keeping
breaker state in the memory of each gateway process is free and fast but
gives every replica its own, slightly different, view of whether a target
is healthy. A shared store gives every replica the same view but adds a
dependency, and that dependency's own availability now sits on the path of
every routing decision the breaker is meant to protect.

## 4. Applicability and non-applicability

Reach for an LLM circuit breaker when the system has one of these shapes.

- More than one provider, model, or deployment behind a router, so there is
  somewhere useful to fail over to when a target's breaker opens. The
  breaker's value is largely in making the failover decision automatic and
  consistent rather than something scattered across retry loops.
- An agent loop that calls tools or models in a way that is not obviously
  bounded, where a stuck loop can call the same failing target far more
  times per user turn than a person would ever notice by watching request
  counts alone.
- High enough call volume, or high enough per-call cost, that paying for
  calls to a target that is failing most of the time is a real line item,
  not a rounding error.
- A user-facing, latency-sensitive path where a hung or slow-failing
  provider must not be allowed to block the request queue behind it while
  every caller waits out its full timeout.
- A shared gateway serving more than one internal team or customer tenant,
  where isolating one tenant's failures from another tenant's experience of
  the same provider matters.

Do not reach for it in these situations, and treat this list as the more
important half of the dimension, because it is the half most catalogs skip.

- A single sole provider with no fallback and no alternate deployment.
  Tripping the circuit here does not protect anything. It converts a slow,
  partial failure into a fast, total one, because there is nowhere else to
  route to. A timeout and a bounded retry, the Retry pattern this family
  cross-references, is the entire mechanism that situation needs.
- Low-volume, single-shot use, a script or a CLI tool making one call and
  exiting. The state machine, its counters, and its cooldown clock cost more
  to build and reason about than the failures they would ever catch below a
  certain request rate.
- As a replacement for content-safety review. A circuit breaker trips on a
  failure rate. A single response that is factually wrong, unsafe, or
  policy-violating, delivered inside an otherwise low failure rate, never
  crosses any threshold this pattern watches. That job belongs to Output
  Guardrails, checking each response on its own merits, and to Input
  Guardrails on the way in. This is exactly the point where the naming
  collision described in dimension 1 causes real harm. A team that reads
  about Zou et al.'s representation-engineering circuit breakers and
  assumes their resilience-engineering circuit breaker already covers the
  same ground will ship a system with a content-safety gap neither
  mechanism actually fills alone.
- As a substitute for capacity planning. If a breaker for a target trips
  routinely under ordinary peak traffic, that is a signal the target is
  under-provisioned or the token-per-minute quota is set too low, not a
  signal the breaker is doing its job. Fixing the quota or the deployment
  size is the correct response, not tuning the breaker's threshold up until
  it stops firing.
- When the system already sits behind infrastructure, a load balancer, a
  service mesh, or a platform health check, that already performs failure
  detection and rerouting at the level this pattern targets. Layering a
  second, uncoordinated breaker on top of one that already exists at the
  platform layer, per the Azure Architecture Center's own guidance on when
  not to use the classic form, adds complexity without adding protection
  ([Azure Architecture Center, Circuit Breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker),
  verified 2026-08-03).

## 5. Structure

- **Caller.** The code that wants a completion, an embedding, or a tool
  result from a model, an agent loop, an orchestrator, or a request handler
  inside a gateway.
- **Target.** One provider, model, and deployment or region tuple. A target
  is the unit a breaker protects. Two deployments of the same model in
  different regions are two targets, not one.
- **BreakerState.** The per-target state machine, closed, open, or half
  open, together with the data it needs to decide when to transition,
  recent failure timestamps or counts, the time the circuit opened, and how
  many probe calls are currently in flight during half open.
- **FailureClassifier.** The LLM-specific piece a generic HTTP circuit
  breaker does not need. It looks past the status code at the shape of the
  response, an empty completion, a truncated stream, a `content_filter`
  stop reason, a non-retryable 4xx caused by the caller's own malformed
  request, and decides which of those actually count as evidence the
  target is unhealthy versus evidence the caller or the content did
  something the target correctly rejected.
- **SlidingWindow.** The rolling count or rate of classified failures over a
  configured time window, the input the trip decision is made against.
- **CooldownClock.** The timer that governs how long a target stays open
  before a probe is permitted, potentially informed by a `Retry-After`
  header the provider itself supplied rather than a fixed duration.
- **FallbackRouter.** The component that, given an open breaker on the
  preferred target, selects the next target in a priority or weighted order,
  skipping every target whose own breaker is currently open.
- **Probe.** The single, or small number of, requests a half open breaker
  allows through to test recovery, distinct from ordinary traffic in that
  its outcome alone decides the next state transition.
- **Metrics and event sink.** Where every state transition, and the reason
  for it, is emitted so an operator can see why a target was cut off rather
  than only that it was.

## 6. ASCII structure diagram

```
+-----------+     +----------------+     +-------------------+
|  Caller   |---->|  Fallback      |---->| Breaker(Target A)  |
| (agent /  |     |  Router        |     | state: CLOSED      |
|  gateway  |     |  (priority     |     +----------+---------+
|  handler) |     |   ordered)     |                |
+-----------+     +-------+--------+                v
                          |                +-------------------+
                          |                |     Target A       |
                          |                | (provider, model,  |
                          |                |  region tuple)     |
                          |                +-------------------+
                          |
                          v
                  +-------------------+
                  | Breaker(Target B)  |
                  | state: OPEN         |
                  +----------+---------+
                             |  request skipped,
                             |  cooldown still active
                             v
                  +-------------------+
                  |     Target B       |
                  +-------------------+

  Each Breaker consults on every call.
    FailureClassifier  -> status code, stream abort, empty body,
                           content_filter stop reason, failure or not
    SlidingWindow      -> recent failure count or rate in the window
    CooldownClock      -> how long OPEN persists, honoring Retry-After
  Every state transition is reported to a Metrics / event sink.
```

## 7. Dynamics

The state machine advances through the same three states the classic
pattern uses, with the trip and probe conditions supplied by the LLM-aware
FailureClassifier from dimension 5 rather than by transport status alone.

```
closed --(N classified failures within window W)--> open
open   --(cooldown elapsed, honors Retry-After if present)--> half_open
half_open --(probe call classified as success)--> closed, counters reset
half_open --(probe call classified as failure)--> open, cooldown restarts

  time ---->

  [closed] fail  fail  fail        [OPEN, cooldown timer running]
    call    call  call  call  |  reject reject reject reject reject  |
     ok      X     X     X    |    (routed to fallback target)       |
                               \_____________ cooldown elapsed _____/
                                                     |
                                                     v
                                              [half_open]
                                            one probe call allowed
                                            /                    \
                                    probe succeeds          probe fails
                                          |                        |
                                          v                        v
                                     [closed]                   [open]
                                  counters reset          new cooldown,
                                                          optionally longer
```

Two dynamics are specific to this pattern and worth naming separately from
the generic state machine above, because neither exists in a plain HTTP
circuit breaker.

The first is the streaming case. A chat completion or a tool-calling
response is very often delivered as a stream, not a single response body,
so the trip decision cannot be made purely at connection time. The stream
can open successfully, the HTTP status can arrive as `200`, and the failure
can only reveal itself several seconds later when the stream stalls or
closes with zero or partial bytes delivered. The breaker has to observe the
whole stream lifecycle, not only the initial handshake, and classify a
stalled or truncated stream as a target failure even though nothing about
the opening response looked wrong.

The second is the cost or agent-loop dynamic, which runs on an entirely
separate axis from target health. A target can answer every individual call
with a valid `200` and a well-formed tool call, so the transport-level
breaker never trips, while the agent driving those calls is stuck issuing
the same tool call over and over because it never makes progress toward
completing the task. This is not a target-health failure at all. It is a
failure of the caller's own trajectory. Dimension 8 below treats this as an
orthogonal breaker, one keyed on cumulative spend or on a
repeated-call-with-no-progress signature within a single agent turn, running
alongside, not instead of, the target-health breaker described above.

## 8. Implementation variants

**HTTP-status-driven, threshold on count or rate.** The variant closest to
the classic pattern. A breaker trips when a configured number, or
percentage, of calls to a target fail within a rolling window, judged mostly
by status code. Portkey's gateway trips when either a configured
`failure_threshold` count or a `failure_threshold_percentage`, evaluated
once a `minimum_requests` floor is reached, is exceeded, with responses over
`500` classified as failures by default and specific codes such as `401` or
`429` addable to that set
([Portkey, Circuit Breaker](https://portkey.ai/docs/product/ai-gateway/circuit-breaker),
verified 2026-08-03). Azure API Management's backend circuit breaker takes
the same shape, tripping on a configured count of matching status codes
within a defined interval
([Microsoft Learn, Azure API Management Backends](https://learn.microsoft.com/en-us/azure/api-management/backends),
verified 2026-08-03).

**Cooldown-and-allowed-fails counting, without the half-open label.** A
simpler variant that reaches the same outcome, temporarily removing an
unhealthy target from rotation and automatically returning it later,
without naming a half open state explicitly. LiteLLM's Router removes a
specific deployment from its selection pool once it has failed more than
`allowed_fails` times inside a minute, defaulting to three failures and a
five-second cooldown, and returns the deployment to rotation once the
cooldown elapses. Its documentation separates immediate cooldown on a
`429`, a general high-failure-rate trigger above fifty percent of calls in
the current minute, and a distinct set of non-retryable client errors,
`401`, `404`, `408`, that do not count toward the failure rate at all
([LiteLLM, Router - Load Balancing, Fallbacks, Retries](https://docs.litellm.ai/docs/routing),
verified 2026-08-03). LiteLLM's own documentation does not use the term
"circuit breaker" for this behavior, it calls it a cooldown. The mechanism
it describes, removing a failing deployment from rotation for a bounded
period and letting it back in automatically, is functionally the pattern
this entry names, under different vocabulary, and is worth citing precisely
for that reason. The pattern is recognizable by its behavior even where the
product never uses the electrical-breaker metaphor.

**Retry-After-aware dynamic cooldown.** Rather than a fixed trip duration,
the breaker reads a provider-supplied `Retry-After` header and waits that
long before allowing a probe, shortening or lengthening the cooldown to
match what the provider itself reports rather than a static guess. Azure API
Management's backend circuit breaker supports exactly this, an
`acceptRetryAfter` setting that lets the configured trip duration be
overridden by the header value the failing backend returned, and its own
documentation calls out Azure OpenAI specifically as a backend whose `429`
responses can carry a very large `Retry-After` value that the circuit
breaker should honor rather than ignore
([Microsoft Learn, Azure API Management Backends](https://learn.microsoft.com/en-us/azure/api-management/backends),
verified 2026-08-03).

**Cost or token-budget breaker.** A second, independent breaker keyed not on
transport failures at all but on cumulative spend or token consumption
within a window. This variant is largely engineering judgement rather than
a single sourced technique. It trips when a caller, a tenant, or an agent
turn crosses a configured dollar or token ceiling, regardless of whether
every individual call succeeded, and its recovery is often a hard reset at
the next billing period or the next turn rather than a timed cooldown. It
composes with, and never replaces, the target-health breaker above. A
target can be perfectly healthy while a specific caller's spend breaker
still trips.

**Semantic or quality breaker.** A variant keyed on the content of
responses rather than their transport status. A target that keeps
returning empty completions, keeps hitting a `content_filter` stop reason
on otherwise benign prompts, or an agent that keeps issuing an identical
tool call with no forward progress, trips a breaker even though every call
returned `200`. This is the variant with the least standardized production
tooling behind it and the most judgement in how it is tuned. The general
technique of watching output quality, not only transport status, is the
part of this pattern with no equivalent in the classic, non-LLM Circuit
Breaker.

**Per-tenant or per-request-class keying.** Rather than one breaker per
target shared by every caller, a gateway serving multiple teams or customers
keys breaker state on the pair of target and tenant, so one tenant's
malformed traffic or runaway agent trips a breaker only for that tenant,
never for every other caller of the same, otherwise healthy, target. This
variant trades a larger number of tracked breakers for real isolation, and
composes directly with the Bulkhead pattern this family cross-references,
which partitions capacity the same way this variant partitions failure
state.

**Resilience-library building block.** Independent of any LLM-specific
product, general purpose libraries such as Resilience4j implement the same
three-state machine, closed, open, half open, with a configurable failure
rate threshold, a slow-call rate threshold, and a choice of count-based or
time-based sliding window for aggregating outcomes
([Resilience4j, CircuitBreaker](https://resilience4j.readme.io/docs/circuitbreaker),
verified 2026-08-03). Wrapping an LLM client call with a library like this
gives a team the state machine and its concurrency handling for free. The
LLM-specific work that remains is entirely the FailureClassifier from
dimension 5, deciding which LLM-shaped outcomes, an empty completion, a
stalled stream, a `content_filter` stop reason, feed into that library's
generic notion of a failed call.

## 9. Known production uses

**Portkey's AI Gateway** ships a named Circuit Breaker feature that
automatically stops routing to an unhealthy target until it recovers,
tripping when either a configured failure count or a failure percentage,
once a minimum request volume is reached, is crossed, removing that target
from the routing pool, and reopening it after a configurable cooldown of at
least thirty seconds. If every configured target's breaker happens to be
open at once, Portkey documents that the breaker is bypassed so requests
still have somewhere to go rather than failing outright
([Portkey, Circuit Breaker](https://portkey.ai/docs/product/ai-gateway/circuit-breaker),
verified 2026-08-03).

**Azure API Management's AI gateway capabilities** expose a backend circuit
breaker property specifically documented for load balancing and protecting
Azure OpenAI, Microsoft Foundry, and other LLM backend pools, defining trip
rules on a status-code range and a count over an interval, and, once
tripped, returning `503 Service Unavailable` to the caller for the
configured trip duration before resuming traffic. The documentation states
this circuit breaker features dynamic trip duration, applying values from
the `Retry-After` header provided by the backend, explicitly to maximize
use of priority LLM backends such as Provisioned Throughput Unit
deployments while they recover
([Microsoft Learn, AI gateway capabilities in Azure API Management](https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities),
verified 2026-08-03;
[Microsoft Learn, Azure API Management Backends](https://learn.microsoft.com/en-us/azure/api-management/backends),
verified 2026-08-03).

**LiteLLM's Router** implements the cooldown variant described in dimension
8 for load balancing across LLM deployments. A deployment that fails more
than its `allowed_fails` limit within a minute, default three, is removed
from the router's available pool for a configurable `cooldown_time`,
default five seconds, with immediate cooldown on a `429`, a distinct
high-failure-rate trigger, and non-retryable client errors excluded from
the failure count entirely, and the deployment is automatically returned to
rotation once the cooldown elapses
([LiteLLM, Router - Load Balancing, Fallbacks, Retries](https://docs.litellm.ai/docs/routing),
verified 2026-08-03). This is the clearest example in production LLM
tooling of the pattern existing under a different name, cooldown rather
than circuit breaker, while matching the classic pattern's behavior closely
enough that Nygard's own description of the mechanism, not his vocabulary,
is the more reliable way to recognize it in the wild.

## 10. Consequences

The parts of this dimension that describe a degree of cost or benefit,
rather than a documented product behavior, are engineering judgement.

Positive consequences. A caller behind a tripped breaker gets a bounded,
fast failure or an automatic fallback instead of waiting out a full timeout
on every single call to a target that is statistically unlikely to succeed.
Nygard's own framing of the pattern, avoiding the wasted latency of a
doomed call, is exactly this benefit
([publisher page](https://pragprog.com/titles/mnee2/release-it-second-edition/),
verified 2026-08-03). A breaker that trips before a caller keeps paying for
calls that will fail protects real inference budget, which matters more for
LLM calls than for most other remote dependencies because the per-call cost
is rarely negligible. Keying breakers per target rather than per provider
stops one degraded deployment from dragging load-balancing decisions away
from sibling deployments that remain healthy. A breaker's state transitions
give an operator one clear signal per target, open or closed, rather than a
raw stream of individual error logs that has to be aggregated by hand to
answer the same question. And composed with a fallback router, the pattern
turns a multi-provider setup from trying each provider until one of them
eventually responds into a system that actively avoids sending traffic to
targets it already knows are unhealthy.

Negative consequences. A falsely tripped breaker, caused by a threshold
tuned too aggressively for a target's real variance, demotes traffic to a
more costly or lower-quality fallback for the length of the cooldown even
though the primary target would have handled the next call fine. This cost
is paid in both latency and money for the whole cooldown window, not only
for the calls that actually failed. The FailureClassifier is real,
recurring design work specific to each provider's response shapes, and
getting it wrong in either direction causes a real problem. Classify too
narrowly, on status code alone, and the breaker never trips on the
LLM-shaped failures dimension 2 describes. Classify too broadly, treating a
legitimate `content_filter` refusal as a target failure, and the breaker
trips on correct behavior and starts masking a business-logic outcome as an
availability outcome. Breaker state itself is a new piece of infrastructure
that has to live somewhere. Kept in each process's memory it is cheap and
fast but blind across a horizontally scaled fleet, each replica computing
its own view of health. Kept in a shared store it is consistent across the
fleet but adds a dependency whose own outage now sits on the path of every
routing decision the breaker exists to protect. And in an agent context, a
breaker tuned for plain HTTP semantics can trip on a legitimately slow but
eventually successful multi-step tool chain if its threshold treats a long
sequence of intermediate calls the same way it would treat a burst of
unrelated failures.

## 11. Failure modes and misuse

**Symptom.** All traffic silently routes to the most costly fallback model
for hours after what was, on inspection, a two-minute blip on the primary
provider.
**Cause.** The circuit's trip duration is fixed at a value chosen without
regard to the actual outage length, and the breaker ignores any
`Retry-After` signal the provider sent, so it stays open far longer than the
real recovery took.
**Fix.** Honor a provider-supplied `Retry-After` header where one exists,
the way Azure API Management's `acceptRetryAfter` setting does, and, where
no such header exists, prefer a short initial cooldown with exponential
backoff on repeated re-trips over one long, static duration.

**Symptom.** A target is clearly failing on most calls, yet the breaker
never trips.
**Cause.** The FailureClassifier only inspects the HTTP status code, and the
target is returning `200 OK` responses that carry an empty completion, a
truncated stream, or a stop reason that means the model gave up rather than
finished.
**Fix.** Classify on the shape of the response body and, for streamed
responses, on the outcome of the whole stream, not only on the status of
the initial connection. Empty or implausibly short completions, a stall
mid-stream with zero bytes delivered, and provider-specific stop reasons
that indicate a failure to complete all count as target failures regardless
of transport status.

**Symptom.** One tenant on a shared gateway keeps sending malformed
requests that always draw a `400`, and every other tenant now finds
themselves permanently routed to the fallback for a provider that, from
their own traffic, looks perfectly healthy.
**Cause.** The breaker is keyed only on the target, so one tenant's
client-caused errors count toward the same failure window every other
tenant's traffic shares, and a client error is being classified as evidence
of the provider's health rather than evidence of a malformed request.
**Fix.** Exclude non-retryable, client-caused status codes, `400`, `401`,
`404`, from the failure count entirely, the way LiteLLM's own documentation
separates them from its failure-rate accounting, and key breaker state per
target and tenant wherever tenant isolation is actually required rather than
per target alone.

**Symptom.** In a horizontally scaled gateway fleet, roughly half the pods
route new requests to the primary target and the other half route to the
fallback, and users see inconsistent latency depending purely on which pod
handled their request.
**Cause.** Breaker state is kept in each process's local memory with no
shared store and no synchronization across replicas, so each pod's view of
whether a target is open genuinely diverges from its siblings'.
**Fix.** Either accept the approximation deliberately and document it,
which is the explicit trade-off Azure API Management's own documentation
states its distributed backend circuit breaker makes, different instances
of the gateway do not synchronize, or move breaker state to a shared store
when cross-replica consistency matters more than the added dependency risk
that store introduces.

**Symptom.** An agent burns its entire per-request cost budget before any
target-health breaker ever trips, because every individual call to the
model returns a valid, well-formed response.
**Cause.** The only breaker in the system watches transport-level target
health. Nothing watches the agent's own trajectory for repeated, identical
tool calls that make no forward progress, which is a failure of the
caller's loop, not of the target it is calling.
**Fix.** Add a second, independent breaker, the semantic or cost-driven
variant from dimension 8, keyed on cumulative spend or on a
repeated-call-with-no-progress signature within one agent turn, running
alongside the target-health breaker rather than folded into it.

**Symptom.** Adding a circuit breaker in front of an existing LLM call path
makes the measured p99 latency worse, not better.
**Cause.** The half-open probe is implemented synchronously and blocks the
very live user request that happened to trigger the probe attempt, so that
one unlucky caller pays the full cost of testing recovery on behalf of
everyone else.
**Fix.** Never let a live request pay for the recovery probe. Either route
that request to the fallback immediately while a separate, out-of-band
probe checks the primary's health, or accept that only a dedicated probe
call, never a real user's request, is allowed to test a target while it is
half open.

## 12. Trade-off matrix

Compared against three named alternatives this family and the cloud
patterns family already document, evaluated on the forces from dimension 3.

| Force | LLM Circuit Breaker | Retry with backoff alone | Rate Limiter alone | Output Guardrails alone |
|---|---|---|---|---|
| Fails fast on sustained outage | Yes, once tripped | No, keeps paying full timeout cost per attempt | Not its job, limits volume not health | Not its job, evaluates content not availability |
| Protects budget from doomed calls | Yes, stops calling a known-bad target | No, retries still cost money | Only against self-inflicted overuse | No |
| Detects LLM-shaped failures, empty body, stalled stream | Yes, via the FailureClassifier | No, retries on any exception equally | No | Partially, if the classifier looks at content |
| Catches an individually unsafe response inside a low failure rate | No, by design, see dimension 4 | No | No | Yes, this is exactly its job |
| Isolates one bad tenant from the rest of a shared gateway | Yes, when keyed per target and tenant | No | Yes, per consumer quota | No |
| Recovers automatically as the target heals | Yes, via half open probing | Yes, implicitly, each call retries fresh | Not applicable, no notion of target health | Not applicable |
| Operational complexity added | Real, state machine, classifier, cooldown store | Low | Low to moderate | Moderate, needs a policy and a model or ruleset |

The honest reading of this table is that none of the four rows on the right
substitutes for the pattern in the left column, and the pattern in the left
column does not substitute for any of them either. A production LLM system
generally needs several of these at once. A circuit breaker for target
health, a rate limiter for consumption fairness, retries with backoff
underneath the breaker for the transient faults it is not yet sure are
sustained, and guardrails for content correctness that no failure-rate
mechanism will ever catch.

## 13. Related and incompatible patterns

**Circuit Breaker (family 08, cloud and distributed).** The parent pattern
this entry specializes. Everything about the state machine, closed, open,
half open, and the general hazards, resource differentiation across
independent shards, the danger of a fixed timeout on a slow-failing
dependency, comes from that entry. This one adds the LLM-specific failure
classification, the cost dimension, and the agent-loop dimension on top.

**Retry.** Sits underneath this pattern, not beside it. A call that a
breaker allows through, closed or half open, is still a candidate for a
bounded retry on a transient fault. The breaker's job is deciding whether to
attempt the call at all, the retry's job is deciding how many times to
attempt one already-permitted call.

**Bulkhead.** Composes directly with the per-tenant breaker keying variant
from dimension 8. A bulkhead partitions capacity, concurrency limits,
connection pools, so one caller cannot exhaust resources meant for another.
A per-tenant breaker partitions failure state the same way. Used together,
neither one caller's traffic volume nor one caller's failure rate can affect
another caller sharing the same gateway.

**Rate Limiting.** A complementary, not overlapping, control. Rate limiting
bounds how much traffic a consumer is allowed to send regardless of target
health. A circuit breaker bounds how much traffic a target is allowed to
receive regardless of how much a consumer wants to send. A gateway needs
both, because a healthy target can still be overwhelmed by legitimate volume
that a rate limiter, not a breaker, is meant to shape.

**Output Guardrails and Input Guardrails.** The content-correctness
counterpart described repeatedly above. A circuit breaker answers whether a
target is statistically healthy enough to call right now. Guardrails answer
whether a specific input or output is acceptable on its own merits. Both are
required in any system that cares about both availability and content
correctness, and dimension 4 explains at length why one is never a
substitute for the other.

**Function Calling and Agentic RAG or Corrective RAG.** Wherever an agent
loop or a retrieval pipeline calls a model or a retriever repeatedly inside
one turn, the agent-loop breaker variant from dimension 8 applies. A
FailureClassifier for a tool call or a retrieval step is a smaller version
of the same problem this entry solves for a raw model call, and both
Agentic RAG and Corrective RAG already list this pattern as related for
exactly that reason.

**Incompatible patterns.** None structurally. The pattern composes rather
than conflicts with everything above. The one real tension worth naming in
prose rather than in the frontmatter is with any design that treats a
naive, unbounded retry loop as sufficient error handling for LLM calls.
That is closer to an anti-pattern than a named pattern, and a circuit
breaker's entire purpose is to stop that behavior from reaching a target
that has already demonstrated it is unhealthy.

## 14. Refactoring path in and out

Introducing this pattern into a codebase that does not have it starts from
whatever ad hoc retry logic already surrounds the LLM call, and proceeds in
steps that each leave the system working at every point along the way.

First, name the targets. Before any breaker logic exists, enumerate the
distinct provider, model, and deployment or region tuples the system
actually calls, because the breaker granularity decision from dimension 1
has to be made before any code is written, not discovered by accident once
two deployments' failures turn out to have been merged into one signal the
whole time.

Second, extract the failure classifier as a pure function, independent of
any state machine, that takes a raw response or exception and returns
whether it counts as a target-health failure. This step alone, done before
any breaker exists, immediately surfaces every place the current retry
logic is treating a client error as if it were a server error, or ignoring
an empty completion entirely, because writing the classifier forces those
cases to be enumerated explicitly.

Third, wrap the existing call path with a breaker in observe-only mode,
tracking state transitions and emitting them to the metrics sink from
dimension 5 without actually rejecting any call yet. This step validates the
threshold and window choices against real traffic before they can affect a
single user, and is the step most teams are tempted to skip and should not.

Fourth, turn on rejection for the open state, routing rejected calls to the
existing fallback path the system already has, or to a fixed degraded
response if no fallback exists yet. This is the first step with real
behavioral effect, and it should ship after the observe-only period from
step three has run long enough to show the thresholds do not trip on
ordinary traffic variance.

Fifth, add the half-open probe path, replacing whatever ad hoc retry-after-a-
while logic existed before with an explicit, single, non-blocking probe per
cooldown expiry, per the fix in dimension 11's last failure mode.

Sixth, once target-health breakers are stable, add the orthogonal cost or
semantic breaker from dimension 8 if the agent-loop failure mode in
dimension 2 and dimension 11 applies to the system, treating it as a
separate addition rather than folding it into the target-health breaker's
own threshold.

Removing the pattern, which happens less often than adding it but does
happen, is the reverse in reduced form. First confirm, from the metrics sink
built in step three, that the breaker has not tripped in a meaningful window
under real traffic, which usually means either the failure mode it was
built for stopped occurring, a provider outage pattern that ended, a
migration to a single reliable provider with no more fallback to route to,
or a platform-level mechanism, a service mesh or a managed gateway, now
performs the same function underneath the application. Only then remove the
rejection behavior first, leaving observe-only telemetry running for a
period, before deleting the breaker and its state entirely, so a
regression in the underlying failure mode is caught by the still-running
telemetry rather than by a silent return of the original problem.

## 15. Testing and verification

Code that calls an LLM through a circuit breaker is, in one respect, easier
to test than the bare call it replaces. The breaker's state machine is a
pure, deterministic function of a sequence of classified outcomes and the
passage of time, and it can be tested entirely without a real network call
or a real model, using a fake clock and a scripted sequence of success and
failure signals fed straight into the classifier and the state machine.

Test the FailureClassifier in isolation first, and test it exhaustively
against every response shape the target can plausibly return. A clean
success, a `429`, a `5xx`, a `4xx` that should not count against target
health, a `200` with an empty body, a stream that stalls after zero bytes, a
stream that stalls after partial content, and a `content_filter` stop
reason. Each of these is a single, cheap unit test with no breaker state
involved at all, and a classifier bug caught here never has to be
rediscovered later inside a slower, harder-to-reason-about state-machine
test.

Test the state machine next, with the classifier replaced by a test double
that returns a scripted sequence of true or false failure verdicts, and a
fake or injectable clock rather than a real one, so a cooldown period can be
advanced in a test in microseconds rather than actually waiting out the
configured duration. Verify the three transitions the classic pattern
defines directly. Closed to open once the threshold is crossed within the
window, open to half open once the fake clock crosses the cooldown, and
half open to either closed on a successful probe or back to open on a
failed one, with the cooldown timer restarting.

Test the fallback router with a scenario where the primary target's breaker
is open and confirm traffic actually reaches the configured fallback rather
than only confirming the primary was correctly rejected, since a router that
correctly refuses the primary but never actually calls the fallback is a
common, easy-to-miss defect that a test asserting only that the primary was
not called will not catch.

For the streaming case specifically, a test double that yields a few chunks
and then raises, simulating a mid-stream abort, is the right shape of fake.
Asserting the breaker records a failure only after observing the whole
stream lifecycle, not merely the initial connection, catches the exact
failure mode named in dimension 7.

For the multi-replica consistency question from dimension 11, the correct
test is not a unit test of the breaker itself but an integration or load
test that runs several breaker instances concurrently against a simulated
flapping target and observes, empirically, how much divergence in routing
decisions the deployed configuration actually produces, since that
divergence is a property of the deployment topology, local state versus
shared store, not of the breaker's own logic.

Finally, a single end-to-end test with a real provider is worth keeping
even after the above. Not to exercise every edge case, that is what the
unit tests above are for, but to catch drift when a provider changes the
shape of an error response, a stop-reason string, or a `Retry-After`
header's format, that a hand-written test double can silently stop
matching.

## 16. Observability signals

The single most useful signal is the per-target breaker state itself,
emitted as a gauge or a labeled counter on every transition, closed to open,
open to half open, half open to closed or back to open, tagged with the
target identifier so a dashboard can show, at a glance, which provider,
model, and region tuples are currently degraded without anyone having to
grep raw error logs to reconstruct that answer by hand.

Alongside the state itself, track the classified failure rate feeding the
sliding window, separately from the raw HTTP error rate, so an operator can
see the gap between a provider returning errors and the breaker deciding the
target is unhealthy, and diagnose a misclassified failure quickly when that
gap looks wrong. Track cooldown duration actually applied per trip, distinct
from the configured default, whenever a `Retry-After`-aware variant is in
use, since a target repeatedly returning a very long `Retry-After` is itself
a signal worth alerting on independent of the breaker's own behavior.

Track time spent in each state per target over a rolling window, because a
target that flaps between open and half open every few minutes, never
settling into a stable closed state, is a materially different operational
problem, usually an under-provisioned deployment or a threshold tuned too
tight, than a target that trips once and stays open for a clean, single
cooldown period.

For the cost or agent-loop breaker variant from dimension 8, track the
breaker's own trip count and trip reason separately from the target-health
breaker's, since folding both into one metric hides which failure mode is
actually happening. A spike in target-health trips points at a provider
problem, a spike in cost-breaker trips points at an agent or a prompt
problem, and conflating the two sends whoever is on call chasing the wrong
system.

A healthy target, on a dashboard built from these signals, looks like a
flat line at closed with an occasional, brief, single dip to open that
recovers on the first half-open probe. A failing dashboard looks like
either a target stuck at open well past a reasonable cooldown, which points
back at the fix in dimension 11's first failure mode, or a target
oscillating rapidly between open and half open, which points at a threshold
tuned for a target with more natural variance than the configuration
assumed.

## 17. Security and privacy implications

The breaker's own state, per-target failure counts, trip timestamps, and
cooldown windows, carries no prompt content and no completion content by
construction, so keeping that state in a shared store, Redis or an
equivalent, does not by itself introduce a new place where sensitive
conversation data at rest has to be protected. It is metadata about calls,
not the calls' content.

The FailureClassifier is a different story, because deciding whether a
response counts as a failure sometimes requires inspecting the response
body, an empty completion, a `content_filter` stop reason, and any logging
built around that classification has to be careful not to become an
unintentional second copy of prompt or completion content living in a
metrics or logging pipeline with weaker access controls than the primary
request path has. Log the classification outcome and the reason code, not
the content that produced it, unless the logging pipeline itself is already
held to the same data-handling standard as the primary call path.

A shared breaker keyed only on target, not on tenant, as described in
dimension 11's third failure mode, is also a narrow information-leak
surface worth naming. A tenant who can observe a shared target's breaker
state, through response latency, an explicit error indicating a fallback
was used, or a status endpoint, can infer something about another tenant's
traffic pattern or failure rate on that same target. This is a low-severity
signal on its own, but it is one more argument, alongside the isolation
argument in dimension 8 and dimension 11, for per-tenant breaker keying on
any gateway shared across mutually untrusted callers.

Finally, the fallback path this pattern routes traffic through when a
breaker opens deserves the same security review as the primary path, not a
lighter one. A fallback target that is reached only during a degraded state
is exactly the kind of code path that receives less production traffic in
practice and therefore less scrutiny by accident. If the primary path
enforces a data-residency constraint, a regional routing requirement, or a
specific authentication scheme, the fallback target the breaker routes to
during an open state has to satisfy the same constraints, or an outage on
the primary silently becomes a compliance incident on the fallback.

## 18. References

- Michael T. Nygard, *Release It! Second Edition. Design and Deploy
  Production-Ready Software*, The Pragmatic Programmers, 2018, ISBN
  9781680502398, "Stability Patterns" chapter.
  https://pragprog.com/titles/mnee2/release-it-second-edition/, verified
  2026-08-03.
- Azure Architecture Center, "Circuit Breaker pattern."
  https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker,
  verified 2026-08-03.
- Andy Zou, Long Phan, Justin Wang, Derek Duenas, Maxwell Lin, Maksym
  Andriushchenko, Rowan Wang, Zico Kolter, Matt Fredrikson, Dan Hendrycks,
  "Improving Alignment and Robustness with Circuit Breakers,"
  `arXiv:2406.04313`, submitted 6 June 2024, revised 12 July 2024.
  https://arxiv.org/abs/2406.04313, verified 2026-08-03.
- GraySwanAI, `circuit-breakers` repository, reference implementation for
  the paper above.
  https://github.com/GraySwanAI/circuit-breakers, verified 2026-08-03.
- Portkey, "Circuit Breaker," AI Gateway product documentation.
  https://portkey.ai/docs/product/ai-gateway/circuit-breaker, verified
  2026-08-03.
- Microsoft Learn, "Azure API Management Backends," circuit breaker and
  load-balanced pool sections.
  https://learn.microsoft.com/en-us/azure/api-management/backends, verified
  2026-08-03.
- Microsoft Learn, "AI gateway capabilities in Azure API Management,"
  resiliency section.
  https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities,
  verified 2026-08-03.
- LiteLLM, "Router - Load Balancing, Fallbacks, Retries," cooldowns section.
  https://docs.litellm.ai/docs/routing, verified 2026-08-03.
- Resilience4j, "CircuitBreaker" module documentation.
  https://resilience4j.readme.io/docs/circuitbreaker, verified 2026-08-03.

## Code examples

Three languages, each showing a distinct real shape this pattern takes in
practice. A per-target breaker with an LLM-aware failure classifier in
Python, a streaming-aware breaker that judges a whole stream lifecycle in
TypeScript, and a multi-target fallback router built from goroutine-safe
breakers in Go. All three were compiled or run against the toolchains
available at authoring time, see the closing note for exact results.

```python
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, TypeVar

T = TypeVar("T")


class State(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


class BreakerOpenError(Exception):
    """Raised when a call is rejected because the breaker is OPEN."""


@dataclass
class LlmFailureClassifier:
    """Turns a raw LLM response or exception into a breaker verdict.

    Only sustained target-health failures count toward the trip threshold.
    A client-caused error never counts, or one bad tenant trips the
    breaker for every tenant sharing the same target.
    """

    def is_target_failure(
        self,
        status_code: int | None,
        completion: str | None,
        stop_reason: str | None,
        exc: Exception | None,
    ) -> bool:
        if exc is not None:
            return True
        if status_code in (429, 500, 502, 503, 504):
            return True
        if status_code is not None and 400 <= status_code < 500 and status_code != 429:
            return False
        if completion is not None and len(completion.strip()) == 0:
            return True
        if stop_reason in ("length", "content_filter"):
            return False
        return False


@dataclass
class LlmCircuitBreaker:
    target: str
    failure_threshold: int = 5
    window_seconds: float = 60.0
    cooldown_seconds: float = 30.0
    half_open_max_probes: int = 1

    state: State = State.CLOSED
    failures: list[float] = field(default_factory=list)
    opened_at: float | None = None
    probes_in_flight: int = 0
    classifier: LlmFailureClassifier = field(default_factory=LlmFailureClassifier)

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        self.failures = [t for t in self.failures if t >= cutoff]

    def allow(self) -> bool:
        now = time.monotonic()
        if self.state == State.OPEN:
            if self.opened_at is not None and now - self.opened_at >= self.cooldown_seconds:
                self.state = State.HALF_OPEN
                self.probes_in_flight = 0
            else:
                return False
        if self.state == State.HALF_OPEN:
            if self.probes_in_flight >= self.half_open_max_probes:
                return False
            self.probes_in_flight += 1
        return True

    def record_success(self) -> None:
        if self.state == State.HALF_OPEN:
            self.state = State.CLOSED
            self.failures.clear()
            self.probes_in_flight = 0

    def record_failure(
        self,
        status_code: int | None = None,
        completion: str | None = None,
        stop_reason: str | None = None,
        exc: Exception | None = None,
    ) -> None:
        if not self.classifier.is_target_failure(status_code, completion, stop_reason, exc):
            return
        now = time.monotonic()
        if self.state == State.HALF_OPEN:
            self.state = State.OPEN
            self.opened_at = now
            self.probes_in_flight = 0
            return
        self.failures.append(now)
        self._prune(now)
        if len(self.failures) >= self.failure_threshold:
            self.state = State.OPEN
            self.opened_at = now


def call_with_breaker(breaker: LlmCircuitBreaker, fn: Callable[[], T]) -> T:
    if not breaker.allow():
        raise BreakerOpenError(f"circuit open for target {breaker.target!r}")
    try:
        result = fn()
    except Exception as exc:
        breaker.record_failure(exc=exc)
        raise
    breaker.record_success()
    return result
```

```typescript
type BreakerState = "closed" | "open" | "half_open";

interface StreamOutcome {
  ok: boolean;
  httpStatus?: number;
  bytesReceived: number;
  abortedMidStream: boolean;
}

// A stream can open with a healthy status and only fail several
// seconds later, so the breaker judges the whole lifecycle, not the
// initial connection alone.
class LlmStreamBreaker {
  private state: BreakerState = "closed";
  private failureTimestamps: number[] = [];
  private openedAt: number | null = null;
  private halfOpenProbeInFlight = false;

  constructor(
    private readonly target: string,
    private readonly failureThreshold = 5,
    private readonly windowMs = 60_000,
    private readonly cooldownMs = 30_000,
  ) {}

  private prune(now: number): void {
    const cutoff = now - this.windowMs;
    this.failureTimestamps = this.failureTimestamps.filter((t) => t >= cutoff);
  }

  canAttempt(now = Date.now()): boolean {
    if (this.state === "open") {
      if (this.openedAt !== null && now - this.openedAt >= this.cooldownMs) {
        this.state = "half_open";
        this.halfOpenProbeInFlight = false;
      } else {
        return false;
      }
    }
    if (this.state === "half_open") {
      if (this.halfOpenProbeInFlight) return false;
      this.halfOpenProbeInFlight = true;
    }
    return true;
  }

  private isTargetFailure(outcome: StreamOutcome): boolean {
    if (outcome.httpStatus === 429) return true;
    if (outcome.httpStatus !== undefined && outcome.httpStatus >= 500) return true;
    if (outcome.abortedMidStream && outcome.bytesReceived === 0) return true;
    return false;
  }

  report(outcome: StreamOutcome, now = Date.now()): void {
    if (!this.isTargetFailure(outcome)) {
      if (outcome.ok && this.state === "half_open") {
        this.state = "closed";
        this.failureTimestamps = [];
      }
      this.halfOpenProbeInFlight = false;
      return;
    }
    if (this.state === "half_open") {
      this.state = "open";
      this.openedAt = now;
      this.halfOpenProbeInFlight = false;
      return;
    }
    this.failureTimestamps.push(now);
    this.prune(now);
    if (this.failureTimestamps.length >= this.failureThreshold) {
      this.state = "open";
      this.openedAt = now;
    }
  }

  currentState(): BreakerState {
    return this.state;
  }
}

async function callStreamed(
  breaker: LlmStreamBreaker,
  target: string,
  send: () => AsyncGenerator<string, void, unknown>,
): Promise<string> {
  if (!breaker.canAttempt()) {
    throw new Error(`circuit open for target ${target}`);
  }
  let chunks = "";
  let aborted = false;
  try {
    for await (const chunk of send()) {
      chunks += chunk;
    }
  } catch {
    aborted = true;
  }
  breaker.report({ ok: !aborted, bytesReceived: chunks.length, abortedMidStream: aborted });
  if (aborted) {
    throw new Error(`stream aborted for target ${target}`);
  }
  return chunks;
}
```

```go
package main

import (
	"errors"
	"fmt"
	"sync"
	"time"
)

type state int

const (
	closed state = iota
	open
	halfOpen
)

// Target identifies one provider, model, and region deployment behind
// the router. A router with a fallback chain runs one breaker per target.
type Target struct {
	Name     string
	Priority int
}

type breaker struct {
	mu               sync.Mutex
	st               state
	failures         int
	openedAt         time.Time
	threshold        int
	cooldown         time.Duration
	halfOpenInFlight bool
}

func newBreaker(threshold int, cooldown time.Duration) *breaker {
	return &breaker{st: closed, threshold: threshold, cooldown: cooldown}
}

var errBreakerOpen = errors.New("circuit open")

func (b *breaker) allow() bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	if b.st == open {
		if time.Since(b.openedAt) >= b.cooldown {
			b.st = halfOpen
			b.halfOpenInFlight = false
		} else {
			return false
		}
	}
	if b.st == halfOpen {
		if b.halfOpenInFlight {
			return false
		}
		b.halfOpenInFlight = true
	}
	return true
}

func (b *breaker) recordSuccess() {
	b.mu.Lock()
	defer b.mu.Unlock()
	if b.st == halfOpen {
		b.st = closed
		b.failures = 0
		b.halfOpenInFlight = false
	}
}

func isTargetFailure(err error, status int) bool {
	if err != nil {
		return true
	}
	return status == 429 || status >= 500
}

func (b *breaker) recordFailure(err error, status int) {
	if !isTargetFailure(err, status) {
		return
	}
	b.mu.Lock()
	defer b.mu.Unlock()
	if b.st == halfOpen {
		b.st = open
		b.openedAt = time.Now()
		b.halfOpenInFlight = false
		return
	}
	b.failures++
	if b.failures >= b.threshold {
		b.st = open
		b.openedAt = time.Now()
	}
}

// Router fans a call out across an ordered fallback chain of targets,
// skipping any target whose breaker is open, mirroring how a
// multi-provider LLM gateway routes around an unhealthy deployment
// instead of retrying it.
type Router struct {
	targets  []Target
	breakers map[string]*breaker
}

func NewRouter(targets []Target, threshold int, cooldown time.Duration) *Router {
	m := make(map[string]*breaker, len(targets))
	for _, t := range targets {
		m[t.Name] = newBreaker(threshold, cooldown)
	}
	return &Router{targets: targets, breakers: m}
}

func (r *Router) Call(invoke func(t Target) (int, error)) (Target, error) {
	var lastErr error
	for _, t := range r.targets {
		b := r.breakers[t.Name]
		if !b.allow() {
			continue
		}
		status, err := invoke(t)
		if isTargetFailure(err, status) {
			b.recordFailure(err, status)
			lastErr = fmt.Errorf("target %s failed: %w", t.Name, err)
			continue
		}
		b.recordSuccess()
		return t, nil
	}
	if lastErr == nil {
		lastErr = errBreakerOpen
	}
	return Target{}, fmt.Errorf("all targets exhausted: %w", lastErr)
}
```

All three samples above were executed, not only syntax checked, against a
scripted sequence of simulated failures followed by a recovery call. The
Python sample was run directly with `python3`, tripping its breaker after
three classified failures and closing again after the cooldown and a
successful probe. The TypeScript sample was compiled with `tsc --strict`
against a scratch project and run under `node` after transpilation, with
the same trip-then-recover assertions. The Go sample was checked with
`go vet` and run with `go run`, tripping the primary target's breaker and
confirming the router fell back to the secondary target before routing
back to the primary once it recovered. Java, Rust, C#, and Kotlin are
omitted from the code examples because the pattern's idiomatic shape in
those languages does not diverge in any meaningful way from the
state-machine structure already shown in Go, a per-target mutex-guarded
struct with the same three states, rather than because the pattern fails
to translate.
