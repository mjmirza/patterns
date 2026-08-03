---
name: Fallback Chain
slug: fallback-chain
family: 17-ai-agentic
category: Reliability
aliases: [Model Fallback, Provider Fallback Chain, LLM Failover Chain, Cascading Fallback]
first_described: "Gamma, Helm, Johnson, Vlissides 1994 (Chain of Responsibility); applied to LLM providers by AI gateway and orchestration libraries circa 2023 to 2024"
maturity: established
related: [chain-of-responsibility, circuit-breaker, retry, bulkhead, llm-circuit-breaker, routing, function-calling]
incompatible_with: []
verified: 2026-08-03
---

# Fallback Chain

## 1. Name, aliases, and lineage

The canonical name in this catalog is Fallback Chain. The idea it names is
narrow and specific inside the much larger space of LLM reliability work. an
ordered list of model or provider configurations is tried in sequence for a
single logical request, and the first one that returns a usable response wins.
Every attempt after the first exists only because the one before it failed in
a way the caller judged retryable on a different target.

The pattern has no single named inventor in the way Gamma, Helm, Johnson and
Vlissides named Chain of Responsibility. Design Patterns. Elements of Reusable
Object-Oriented Software, Addison-Wesley, 1994, chapter 4, Chain of
Responsibility, describes a chain of handler objects where each handler either
processes a request or passes it to the next handler in the chain
(Wikipedia summary of the GoF intent, https://en.wikipedia.org/wiki/Chain-of-responsibility_pattern,
verified 2026-08-03). Fallback Chain is a direct application of that
structural idea to a single failure mode. the handler chain exists purely to
survive an unreliable remote dependency, not to route work by content or
responsibility as the GoF pattern's original servlet-filter and event-bubbling
examples do.

The name and the concrete API shape entered common practice through library
code rather than through a paper. LangChain core ships a
`RunnableWithFallbacks` class inside its runnables module, reachable from any
`Runnable` through a `with_fallbacks` method
(https://reference.langchain.com/python/langchain_core/runnables/, verified
2026-08-03). LiteLLM's Router documentation uses the term Fallbacks as a
first-class configuration concept, with a `fallbacks` list and a distinct
`context_window_fallbacks` list for the case where the failure reason is a
prompt too large for the current model rather than an outage
(https://docs.litellm.ai/docs/routing, verified 2026-08-03). OpenRouter's
documentation for its Auto Router describes the same idea under the phrase
Model Fallbacks, and separately documents that "if classification or rankings
are ever unavailable, the router degrades gracefully to a default model set,
a request never fails because routing infrastructure hiccuped"
(https://openrouter.ai/docs/features/model-routing, verified 2026-08-03).
Netflix's Hystrix, a fault tolerance library that predates the current wave of
LLM tooling by a decade, calls the equivalent idea a fallback method, "when a
service call fails or times out, developers define alternative behavior
through fallback methods... allowing applications to degrade gracefully rather
than failing completely" (https://github.com/Netflix/Hystrix, verified
2026-08-03). Every one of these four independent codebases converged on the
word fallback for the same shape, which is why this catalog treats Fallback
Chain as an established, not merely emerging, name.

A companion vocabulary distinction matters here because the surrounding
literature blurs it constantly. Retry means the same target is called again,
usually after a backoff delay, on the belief that the failure was transient.
Fallback means a different target is called, because the caller no longer
trusts the first target to succeed even after waiting. A production fallback
chain almost always nests retry inside each step of the chain, try the primary
model, and inside that attempt retry twice with backoff on a 5xx, before
moving to the next model in the chain. Confusing the two in a design review is
the single most common source of a chain that either gives up too early
(no retry inside a step, so a single blip skips a perfectly good model) or
too late (retrying the same overloaded provider for thirty seconds before the
chain even begins, when a working fallback target sat one step away the whole
time).

## 2. Problem and context

A system calls a large language model as part of serving a real request. a
person waiting for a chat reply, an agent mid-task, a batch job with a
deadline. The provider that model lives behind is, structurally, a shared,
rate-limited, occasionally overloaded remote service the caller does not
control. Anthropic's own API error reference documents a `529 overloaded_error`
explicitly for this case, with the note that these errors "can occur when the
API experiences high traffic across all users"
(https://platform.claude.com/docs/en/api/errors, verified 2026-08-03), and the
same page documents `429 rate_limit_error` and `500 api_error` as the other two
transient failure modes the caller cannot fix by inspecting its own request.
Microsoft's Foundry Models documentation states the same structural fact about
its own Global Standard deployment type in different words. "if the primary
region experiences an interruption in service, all traffic initially routed
to this region is affected"
(https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types,
verified 2026-08-03). Provider-side infrastructure redundancy, cross-region
routing, multiple datacenters behind one endpoint, reduces the frequency of a
correlated outage. It does not remove the caller's obligation to have a plan
for the request that lands during the outage window, because the provider's
own documentation is telling the caller, in plain language, that the failure
mode exists and is visible to every customer at once when it happens.

The situation that calls for a fallback chain, concretely, in a codebase.
There is a function or a service boundary that wraps one call to one model at
one provider. The system has been in production long enough that someone has
watched a real incident. a provider's inference cluster degrades for an hour,
a specific model version gets deprecated and returns errors mid-migration, a
regional network path drops packets, a monthly spend cap on one API key trips
mid-day. During that incident every request that only knows how to call the
one configured model fails, visibly, to the person on the other end. The
fallback chain exists to convert that visible failure into a degraded but
successful response, by trying, in order, alternative targets that are
unlikely to be down for the exact same reason at the exact same moment.

Three structural conditions make the pattern the right tool rather than a
distraction.

- More than one target can plausibly answer the same request. A translation
  request, a summarization request, most chat replies, and most tool-calling
  turns can be answered acceptably by more than one model, even if the models
  differ in quality, latency, or cost. A request that genuinely requires one
  specific model's unique capability, a particular fine-tune, a specific
  context window, a capability no other model in the candidate set has, is a
  poor fit, because the chain will produce a response that is wrong or
  degraded in a way the caller cannot detect from the response shape alone.
- The failure the caller is protecting against is a whole-target failure, not
  a per-request content failure. A fallback chain protects against "this
  provider is down" or "this model is overloaded." It does nothing useful
  against "the model produced a factually wrong or malformed answer while
  healthy," because every model in the chain will happily produce a
  plausible-looking wrong answer with the same 200 status code. That failure
  mode belongs to output guardrails, LLM-as-judge, or a schema validator that
  triggers a targeted retry, not to this pattern.
- The caller can afford, and has budgeted for, the cost and latency of
  multiple attempts landing on multiple providers. A fallback chain trades
  worst-case latency and a second provider's pricing for availability. A
  system with a hard single-digit-millisecond latency budget, or one billed
  per request regardless of success, needs to weigh that trade explicitly
  before adopting the pattern, not discover it during an incident review.

## 3. Forces

**Availability against latency.** Every additional link in the chain is a
guarantee against one more class of single-target failure, purchased with the
tail latency of that link's timeout on the request path when it is the link
that fails. A three-link chain with a five-second per-link timeout has a
worst observed latency near fifteen seconds for the unlucky request that
exhausts the first two links before succeeding on the third. This is the
largest force in the pattern and the one most designs get wrong by not
budgeting for it at all.

**Availability against response quality.** The chain almost never lists
targets of identical quality, it lists a strong, expensive, sometimes-flaky
primary and one or more weaker, cheaper, more available fallbacks. A
successful fallback is a partial failure wearing a success status code, the
system answered, but with a smaller model that reasons less carefully, has a
shorter context window, or is worse at the exact task at hand. Treating every
link's success as equivalent hides this degradation from monitoring and from
the person who received the answer.

**Cost predictability against resilience.** A fallback that lands on a
different provider is billed by that provider's own pricing, which is
frequently not the same as the primary's, and every retried step inside a
link that eventually fails is a paid, discarded call. A chain with generous
per-step retry counts can turn one logical request into five or six billed
calls during a bad incident, at exactly the moment the incident is already
straining the budget dashboard.

**Coupling against operability.** A hardcoded, in-process list of fallback
targets is simple to reason about and ships with the code, but changing the
order or adding a target requires a deploy. A chain driven by external
configuration, the shape LiteLLM's Router and most AI gateway products take,
lets an operator reorder or disable a target during an incident without a
deploy, at the cost of one more moving system whose own availability the
chain now depends on.

**Determinism against adaptivity.** A static, ordered chain is predictable,
the same request always tries targets in the same order, which makes
behavior easy to reason about and easy to test. An adaptive chain that
reorders targets based on recent health, cost, or measured latency, the shape
OpenRouter's Auto Router and LiteLLM's weighted failover both implement,
recovers faster from a degraded target but is genuinely harder to reason
about and to reproduce a specific incident from logs after the fact.

**Team topology against blast radius.** Every model added to a chain is a
provider relationship, a credential, a rate limit, and a prompt-format
translation layer that someone on the team now owns and must keep working.
A chain of five providers is five things that can each independently break
the abstraction the chain promises to hide.

The pattern's honest sacrifice is response quality consistency and worst-case
latency, purchased for availability. A team that adopts it without measuring
and alerting on how often the second and third links actually fire is buying
a false sense of resilience, because the first time a real incident hits, the
degraded response quality and the added latency both arrive as a surprise.

## 4. Applicability and non-applicability

Reach for a fallback chain when the following hold together.

- The request can be answered acceptably by more than one model or provider,
  even at reduced quality, and the caller can tell the difference between
  "no answer" and "a lesser answer" in its own monitoring.
- The failure being defended against is a whole-target outage, overload, rate
  limit, deprecation, or credential exhaustion, not a per-request content
  defect in an otherwise healthy model.
- The system has an availability requirement stronger than "call the one
  configured provider and surface the error," and someone has agreed, in
  writing or in an SLO, to the added latency tail and the added cost of the
  fallback path actually firing.
- There is a way to observe, per request, which link in the chain answered,
  so degraded responses are distinguishable from primary responses in logs,
  traces, and any downstream billing or quality analysis.
- The team can maintain more than one provider integration, including its
  credentials, its prompt-format differences, and its own independent rate
  limits, as an ongoing operational cost, not a one-time setup task.

Do NOT reach for a fallback chain when any of these hold.

- The task genuinely requires one specific model's unique capability, a
  context window no other candidate has, a fine-tune trained on proprietary
  data, or a capability, native tool use in a specific shape, vision, a
  particular reasoning mode, that the fallback targets lack. Falling back
  silently produces a response that looks successful and is substantively
  wrong, which is worse than a visible failure because nobody investigates a
  200 status code.
- The failure mode is a content or correctness problem in an otherwise
  healthy model, a hallucinated fact, a malformed tool call, output that
  fails a schema check. Every other model in the chain is equally capable of
  producing the same class of wrong answer with the same healthy status code.
  This belongs to Output Guardrails, LLM-as-Judge, or a schema-validated
  targeted retry against the same model, not to a whole-target fallback.
- The system has a hard, non-negotiable latency budget that a single
  provider's normal p99 already consumes, so adding a second attempt on
  timeout cannot fit inside the budget under any configuration. A parallel
  hedged request, racing two providers simultaneously and taking the first
  response, is the correct pattern for that constraint, and it is a distinct
  design with its own cost profile, not this one.
- Only one provider is contractually, legally, or technically available, a
  data-residency requirement restricts the workload to a single approved
  vendor, or the organization has one enterprise agreement covering exactly
  one model family. There is nothing to fall back to, and building the
  abstraction anyway adds cost with no achievable benefit.
- The request is not idempotent and a fallback provider re-executing it would
  cause a real side effect twice, sending a notification, charging a card,
  writing to an external system through a tool call the model might invoke
  differently on a second target. The chain needs an idempotency boundary
  around the side effect before it is safe to retry across targets at all.
- The team cannot commit to observing which link answered. An unmonitored
  fallback chain degrades silently for weeks, and the first sign of trouble
  is a slow, unexplained drop in response quality that nobody can trace back
  to "the primary has been down since last Tuesday and everyone has been
  talking to the fallback the whole time."

## 5. Structure

- **Caller.** The code path that needs a completed request, a chat handler, an
  agent step, a batch worker. It holds no knowledge of which target actually
  answered beyond what the chain reports back to it.
- **Chain.** The ordered list of targets plus the policy that governs how the
  chain moves from one target to the next. its responsibilities are strictly
  separated, per-target retry policy (bounded attempts, backoff, which
  exceptions are retryable on the same target), classification of an error as
  retryable-on-same-target, retryable-on-next-target, or fatal, per-target
  timeout, and aggregation of every failure encountered so the caller can see
  the full failure history if every target is exhausted.
- **Target.** One concrete, callable configuration. a model plus a provider
  plus whatever credentials, base URL, and prompt-format adapter that
  provider needs. A target in this pattern is deliberately a configuration,
  not a class hierarchy. two targets can point at the identical model through
  two different providers, which is itself a valid and common chain (the same
  open model served by two different inference hosts).
- **Health signal (optional).** A component that observes recent outcomes per
  target, error rate, latency, and either informs the chain's ordering
  (weighted or adaptive chains) or feeds a sibling Circuit Breaker that skips
  a target the chain would otherwise try and fail against on every request
  during a known outage. See the LLM Circuit Breaker entry in this family for
  the stateful, tripped-open cousin of this idea.
- **Result envelope.** The value returned to the caller carries, at minimum,
  the completion text, which target answered, and how many prior targets were
  attempted and why each failed. Discarding this metadata is the single most
  common mistake in a hand-rolled implementation, because it is exactly the
  data every later observability and cost-accounting need depends on.

## 6. ASCII structure diagram

```
+-------------------------------------------------------------+
|                          Caller                              |
|   (chat handler, agent step, batch worker)                   |
+---------------------------+-----------------------------------+
                            | request
                            v
+-------------------------------------------------------------+
|                       Fallback Chain                         |
|  targets: [ primary, secondary, tertiary ]  (ordered)        |
|  policy:  per-target retry + backoff, per-target timeout,    |
|           error classification, failure aggregation          |
+---------+----------------+----------------+-------------------+
          |                |                |
          v                v                v
   +-------------+  +-------------+  +-------------+
   |  Target A   |  |  Target B   |  |  Target C   |
   | model+prov  |  | model+prov  |  | model+prov  |
   | (primary)   |  | (secondary) |  | (tertiary)  |
   +------+------+  +------+------+  +------+------+
          |                 |                |
          v                 v                v
   +--------------------------------------------------+
   |         Provider APIs (independent failure        |
   |         domains: rate limits, regions, outages)   |
   +--------------------------------------------------+

Optional side channel, feeding ordering or skip decisions:

   +-------------+       +--------------------+
   | Health /    |------>| Circuit Breaker per |
   | outcome log |       | target (skip a      |
   +-------------+       | known-down target)  |
                          +--------------------+
```

## 7. Dynamics

```
Caller           Chain              Target A          Target B
  |  request       |                   |                 |
  |--------------->|                   |                  |
  |                |-- attempt 1 ----->|                  |
  |                |                   | (retryable err)  |
  |                |<-- error, 429 ----|                  |
  |                |-- attempt 2 ----->|  (same target,   |
  |                |    backoff delay  |   inside retry   |
  |                |                   |   policy)        |
  |                |<-- error, 529 ----|                  |
  |                | retries on A exhausted, classify     |
  |                | retryable-on-next-target             |
  |                |-- record A's failure history         |
  |                |                                       |
  |                |-- attempt 1 -------------------------->|
  |                |                                        | (success)
  |                |<-- 200, completion --------------------|
  |<-- result{     |                                        |
  |     text,      |                                        |
  |     answered_by: "target-b",                            |
  |     attempts: [A: 2 failed, B: 1 succeeded] }            |
  |                |                                        |
```

The path where every target is exhausted returns a single aggregated failure
to the caller, carrying the ordered history of every attempt so the caller,
or its own error handler, can decide whether to surface a user-facing error,
serve a cached or templated fallback response, or queue the request for a
later retry once the incident clears.

## 8. Implementation variants

- **Static ordered chain.** A fixed, code- or config-declared list, tried in
  the same order every time. The simplest, most predictable, and most common
  shape for a small chain of two or three targets. LangChain's
  `with_fallbacks` builds this shape, call the base runnable, and on a
  matched exception type, call each fallback runnable in the order supplied
  (https://reference.langchain.com/python/langchain_core/runnables/, verified
  2026-08-03).
- **Weighted or priority-tiered chain.** Targets are grouped into priority
  tiers, and the router exhausts retries within the current tier before
  escalating to the next tier, rather than failing over on the very first
  error. LiteLLM's Router documents exactly this as weighted failover, which
  "keeps regional failures from unnecessarily switching models entirely"
  (https://docs.litellm.ai/docs/routing, verified 2026-08-03). This variant
  suits a chain where several targets are functionally interchangeable
  (multiple regions of the same model) and the true fallback, a different
  model family, should only fire once the entire interchangeable tier is
  confirmed unavailable.
- **Reason-specific fallback lists.** A separate fallback list exists for a
  specific, distinguishable failure reason rather than a single catch-all
  list. LiteLLM's `context_window_fallbacks` is the clearest documented case,
  a prompt that overflows the primary model's context window routes to a
  fallback list of larger-context models specifically, rather than to the
  general-purpose fallback list meant for outages
  (https://docs.litellm.ai/docs/routing, verified 2026-08-03). This is the
  variant that most directly respects the "not every failure is the same
  failure" lesson from dimension 11 below.
- **Cooldown-aware chain.** Each target tracks its own recent failure count
  and, after crossing a configured threshold, enters a cooldown window where
  the chain skips straight past it without attempting a call, then
  automatically becomes eligible again once the cooldown period elapses.
  LiteLLM's Router documents this as `allowed_fails` and `cooldown_time`
  parameters, with deployments that "automatically recover from cooldown
  after the cooldown period expires"
  (https://docs.litellm.ai/docs/routing, verified 2026-08-03). This is the
  fallback chain's own internal, lightweight approximation of a Circuit
  Breaker's open state, scoped to one target rather than governing the whole
  call path.
- **Graceful-degradation default.** Rather than an explicit ordered list, the
  system attempts a preferred, dynamically selected target and, only if the
  selection mechanism itself is unavailable, falls back to one fixed default
  target. OpenRouter's Auto Router is documented this way, classification and
  ranking pick the best model for the request, and if that infrastructure is
  unavailable, the router "degrades gracefully to a default model set"
  (https://openrouter.ai/docs/features/model-routing, verified 2026-08-03).
  This variant is a fallback chain of length two hiding behind a routing
  interface, and it is easy to miss that it is this pattern at all because it
  is marketed as a routing feature.
- **Hedged parallel request (a distinct sibling, named here to avoid
  confusion).** Instead of trying targets in sequence, the caller fires two
  or more targets concurrently and takes the first success, canceling the
  rest. This trades cost, every hedge is a billed call whether it wins or not,
  for the lowest possible worst-case latency, since the chain never waits out
  a full timeout on a failing target before trying the next one. It solves
  the same underlying availability problem as a sequential fallback chain but
  belongs in a separate entry because its cost, concurrency, and
  cancellation concerns are different enough to deserve their own trade-off
  analysis rather than being folded into this one as a footnote.

## 9. Known production uses

- **Netflix Hystrix.** Netflix operated Hystrix as a core fault-tolerance
  library across a large, distributed service mesh, with fallback methods as
  a first-class concept. "when a service call fails or times out, developers
  define alternative behavior through fallback methods... allowing
  applications to degrade gracefully rather than failing completely."
  Netflix released version 1.5.18 as its final active release before moving
  the project to maintenance mode and recommending resilience4j for new
  work, while continuing to run Hystrix in existing applications where it
  remained stable (https://github.com/Netflix/Hystrix, verified 2026-08-03).
  Hystrix predates the current LLM tooling wave and demonstrates that the
  fallback-method shape, and its eventual replacement by newer libraries once
  a pattern matures, is not unique to AI infrastructure.
- **LiteLLM Router.** LiteLLM is an open-source proxy and SDK that many teams
  run in front of multiple LLM providers specifically to get a single,
  OpenAI-compatible interface with configurable fallbacks, cooldowns, and
  weighted failover across a `model_list` of deployments. The router assigns
  each deployment a deterministic `model_id` and automatically tries the
  next `order` tier "when a request to an order=1 deployment fails
  (connection error, 404, 429, etc.)"
  (https://docs.litellm.ai/docs/routing, verified 2026-08-03).
- **LangChain's `RunnableWithFallbacks`.** LangChain core, one of the most
  widely adopted orchestration libraries for LLM applications, ships
  `RunnableWithFallbacks` as a documented class inside its runnables module,
  exposed through the `with_fallbacks` method on any `Runnable`, letting a
  caller wrap a primary chat model runnable with one or more alternate
  runnables tried in order on a matched failure
  (https://reference.langchain.com/python/langchain_core/runnables/, verified
  2026-08-03).
- **OpenRouter's Auto Router.** OpenRouter, an API aggregator sitting in
  front of many model providers, documents a graceful-degradation fallback
  specifically for its own routing infrastructure, when the classification
  and ranking system that picks the best model for a request is itself
  unavailable, "the router degrades gracefully to a default model set, a
  request never fails because routing infrastructure hiccuped"
  (https://openrouter.ai/docs/features/model-routing, verified 2026-08-03).
  This is a production example of the pattern applied one layer up, to the
  routing decision itself rather than only to the model call.

## 10. Consequences

**Positive.**

- Converts a whole-provider outage from a user-visible hard failure into a
  degraded but successful response for the fraction of requests that land
  during the outage window.
- Decouples the caller's availability from any single provider's SLA, which
  matters because a provider's own documented error surface, rate limits,
  overload responses, timeouts, is explicitly outside the caller's control.
- Composes cleanly with per-target retry and with a sibling Circuit Breaker,
  each pattern owning a narrow, well-defined responsibility (retry the same
  target briefly, fall back to a different target, stop calling a target
  known to be down).
- Makes the cost of quality degradation visible and measurable, if and only
  if the result envelope carries which target answered, turning "we think
  the fallback saved us" into a number a team can actually look at.

**Negative.**

- Introduces response quality variance that is invisible to the caller
  unless it explicitly inspects which target answered, so downstream
  consumers of the response can silently receive a weaker answer with no
  signal that anything changed.
- Adds worst-case latency proportional to the number of links the request
  has to exhaust before succeeding, which is easy to underestimate during
  design and painful to discover during an incident when every fallback in
  the chain is also under load from every other caller doing the same thing.
- Multiplies operational surface area, every target is a credential, a rate
  limit, a prompt-format difference, and a billing relationship that must be
  kept working, tested, and monitored independently of the others.
- Can mask a real, ongoing incident. if the fallback path quietly absorbs
  every failed request from the primary for days, nobody escalates the
  primary's outage, and the team pays the fallback's higher unit cost, or
  accepts its lower quality, far longer than intended.
- Risks duplicate side effects on a non-idempotent request that a fallback
  target re-executes after the primary partially succeeded before failing,
  a tool call that ran, a notification that sent, before the response
  itself timed out or errored.

## 11. Failure modes and misuse

- **Symptom.** Response quality degrades gradually over weeks with no
  alerts, and a support ticket eventually surfaces that answers "feel
  worse" than they used to.
  **Cause.** The chain never logs or exposes which target answered each
  request, so the team has no visibility into how often the fallback fires,
  and a slow-onset primary degradation, a rate limit tightened, a model
  quietly deprecated, went unnoticed because every failure the primary threw
  was silently absorbed by the chain.
  **Fix.** Attach the answering target to every response's telemetry, alert
  on the fallback-fire rate crossing a threshold, and treat "the fallback is
  answering more than N percent of traffic" as a paging incident on the
  primary, not a success story for the chain.

- **Symptom.** A single bad request, a malformed tool call the model
  produced while perfectly healthy, chews through the entire chain, costing
  the caller a multiple of the normal latency and billed to every provider
  in the list, and still returns the same wrong answer at the end.
  **Cause.** The chain classifies every non-2xx response as
  retryable-on-next-target, without distinguishing a whole-target outage
  from a per-request content or schema failure that every target in the
  chain will reproduce identically.
  **Fix.** Classify failures before deciding whether to advance the chain.
  a schema validation failure or a malformed tool call belongs to a
  same-target, bounded retry with a corrective prompt, or to an
  LLM-as-Judge or Output Guardrails check, never to advancing to the next
  provider, because the next provider is equally capable of producing the
  same shape of wrong answer.

- **Symptom.** During a real incident, the fallback targets fail almost as
  fast as the primary, and overall system latency during the incident is
  far worse than the primary's outage alone would explain.
  **Cause.** Every caller in the fleet is running the identical chain in the
  identical order, so the moment the primary degrades, the entire fleet's
  traffic pivots onto the secondary target simultaneously, which was
  provisioned for its own baseline load, not for the primary's full traffic
  arriving all at once.
  **Fix.** Load-test the fallback path under the assumption that it must
  absorb one hundred percent of primary traffic, not a small fraction, size
  its rate limits and quota accordingly, and consider staggering or
  randomizing chain order across the fleet, or weighting traffic across more
  than one secondary, so a single fallback target is never the fleet's sole
  point of failure during exactly the incident the chain exists to survive.

- **Symptom.** A user reports receiving a duplicate notification, a
  double-charged action, or a tool side effect that ran twice, and the logs
  show the same logical request answered by two different targets.
  **Cause.** The primary's tool call executed and had a real side effect
  before the primary's response itself failed or timed out, and the chain,
  with no idempotency key or side-effect tracking, re-issued the entire
  request, including the tool call, against the fallback target.
  **Fix.** Wrap any tool call with real-world side effects in an
  idempotency key generated once per logical request, checked and honored
  by the downstream system the tool call reaches, so a fallback re-attempt
  is safe to issue even when the primary's side effect already landed.

- **Symptom.** The team believes the chain gives strong availability
  guarantees, but an incident review after a shared outage shows the chain
  provided no real protection at all.
  **Cause.** The chain's targets are not independent failure domains. two
  "different" targets are the same model served by the same underlying
  provider through two different API keys, or two providers that both
  depend on the same third-party inference host, so a genuine outage at the
  shared dependency takes down every link in the chain at once.
  **Fix.** Audit the chain's targets for a genuinely independent failure
  domain, different vendor, different underlying infrastructure where
  knowable, different region, not merely a different configuration string,
  and document the specific correlated-failure risk that remains for any
  targets that cannot be made fully independent.

- **Symptom.** Per-target retry inside the chain is set generously, and a
  single request takes far longer to fail out of the chain entirely than
  anyone expects, well past the caller's own timeout, so the caller gives up
  and the chain's later, successful attempt is wasted work nobody sees.
  **Cause.** The chain's total worst-case time, the sum of every target's
  retry count times its backoff schedule times its per-attempt timeout, was
  never computed against the caller's own end-to-end deadline.
  **Fix.** Compute and bound the chain's total worst-case duration
  explicitly, propagate the caller's deadline into the chain so it can skip
  remaining retries or remaining targets once the deadline is close, and
  prefer fewer retries per target with more targets in the chain over many
  retries on each target, since a different target is more likely to
  succeed than the same target tried again.

## 12. Trade-off matrix

| Force | Fallback Chain | Circuit Breaker | Retry (same target) | Hedged parallel request |
|---|---|---|---|---|
| Protects against a whole-target outage | Yes, by design | Yes, but only after tripping, so early requests during onset still fail | No, retries the same failing target | Yes, and with the lowest added latency |
| Protects against a per-request content defect | No, every target can reproduce it | No | Sometimes, if paired with a corrective prompt | No |
| Added worst-case latency | High, sum of every failed link's timeout | Low once tripped, requests fail fast; high during the detection window before tripping | Moderate, bounded by retry count times backoff | Lowest, bounded by the fastest responding target |
| Added cost during a healthy period | None, only the primary is called | None | None extra beyond normal calls | High, every hedge is a billed call even when discarded |
| Added cost during an incident | High, multiple providers billed per request | Low, calls to the tripped target stop entirely | Low, but wasted on a target unlikely to recover quickly | Highest, full concurrency across all hedges |
| State the mechanism must maintain | None required, though cooldown variants add per-target counters | Per-target trip state and a half-open probe timer | A per-call attempt counter only | None required |
| Best paired with | Circuit Breaker, to skip a known-down target instead of retrying into it every time | Fallback Chain, to decide when a target is worth skipping entirely | Every step of a fallback chain, nested inside each target attempt | A fallback chain as the degraded path when every hedge fails |

## 13. Related and incompatible patterns

- **Chain of Responsibility (family 01, GoF).** The direct structural
  ancestor. Fallback Chain is Chain of Responsibility specialized to one
  purpose, survive an unreliable remote dependency, with the general
  pattern's content-based routing and short-circuiting replaced by a strict
  linear failure-driven order.
- **Circuit Breaker (family 08).** Circuit Breaker adds memory the plain
  chain lacks. once a target has failed enough times recently, a circuit
  breaker trips open and stops the chain from wasting a full timeout calling
  a target it already knows is down. The two compose directly. wrap each
  link of the chain in its own circuit breaker, and the chain's per-request
  behavior becomes skip known-down targets instantly, still try the rest in
  order.
- **Retry (family 08).** Retry operates inside a single link of the chain,
  not across links. A well-formed fallback chain nests a bounded retry
  policy inside each target attempt and only advances to the next target
  once that target's own retry budget is exhausted.
- **Bulkhead (family 08).** Bulkhead isolates the resource pools, thread
  pools, connection pools, quota, that different targets in the chain draw
  from, so a runaway retry storm against one failing target cannot starve
  the capacity the chain needs to reach a healthy fallback target.
- **LLM Circuit Breaker (family 17).** The AI-specific sibling of Circuit
  Breaker, purpose-built for provider-level failure signals, rate limits,
  overload errors, deprecation notices. It is the natural health signal
  feeding an adaptive fallback chain's ordering decisions, and it is the
  correct place to put the "stop calling this target entirely" state that a
  plain fallback chain, on its own, has no memory to hold.
- **Routing (family 17).** Routing selects a target by classifying the
  request's content, which task type, which complexity tier, before any
  failure has occurred. Fallback Chain selects the next target only after a
  failure. A production system commonly runs both. route to the
  content-appropriate primary target, then fall back through a chain if
  that target fails. Confusing the two produces a design that reorders
  targets by request content on every call and calls it a fallback, when it
  is actually doing routing and has no real failure-driven fallback at all.
- **Function Calling (family 17).** When a fallback target answers a tool-use
  turn, its tool-call format and its willingness to call tools at all can
  differ from the primary's, which is the concrete mechanism behind the
  duplicate-side-effect failure mode in dimension 11. Any chain wrapping a
  tool-calling agent step needs its idempotency guarantees to hold across
  every target in the chain, not only the primary.
- **Incompatible with.** Nothing in this catalog is structurally
  incompatible with Fallback Chain. the pattern's cost is entirely in the
  discipline required to apply it correctly, latency budgeting, failure
  classification, target independence, not in a conflict with another named
  pattern.

## 14. Refactoring path in and out

Introducing a fallback chain into code that currently calls one provider
directly.

1. Locate every call site that invokes the model client directly and confirm
   there is exactly one such call site, or a small, enumerable set. A
   fallback chain retrofitted piecemeal across many ad hoc call sites is
   worse than the single-target code it replaces, because half the system
   gets the protection and half does not, with no way to tell which from the
   outside.
2. Wrap the single call site behind one function or interface whose contract
   is "produce a completion for this prompt," with no caller-visible detail
   about which provider answered. This step alone, done first and shipped on
   its own, is valuable independent of the fallback work, because it is the
   seam the chain will be inserted behind.
3. Add a second target, deliberately choosing one on infrastructure
   independent of the first, and decide the failure classification up front,
   which specific errors advance to the second target versus which are
   fatal. Ship this two-link chain and observe, in production, how often the
   second link actually fires before adding a third.
4. Add the result envelope, which target answered, how many attempts, why
   each prior attempt failed, and wire it into whatever logging or tracing
   the system already has before treating the chain as production-ready.
   A chain shipped without this step is a chain nobody can safely operate.
5. Only after the two-link chain has run in production long enough to
   establish a baseline fallback-fire rate, consider a third target, a
   cooldown policy, or an adaptive ordering. Each of those adds real
   operational complexity and should be justified by an observed gap the
   two-link chain does not cover, not added speculatively on day one.

Removing a fallback chain once it stops earning its place, most commonly
because the organization consolidated onto a single provider under contract,
or because the chain's fallback links never fire and are pure unmaintained
weight.

1. Confirm from the telemetry added in step 4 above how often each
   non-primary link has actually answered a request over a meaningful
   window, months, not days. A link that has not fired in that window is the
   first candidate for removal.
2. Remove the least-used link first, not all of them at once, and watch the
   fallback-fire rate on the remaining links for a rise. a rise means the
   removed link was quietly absorbing a real, if rare, class of primary
   failure, and the decision should be revisited.
3. Once down to a single remaining target, collapse the chain abstraction
   back to a direct call behind the same interface from step 2 above, so any
   future need to reintroduce a fallback has the same seam ready to use.
4. Keep the result envelope's shape, even with a single target, if any
   downstream consumer already depends on it, rather than making its removal
   a second breaking change bundled with the chain's removal.

## 15. Testing and verification

A fallback chain is easy to under-test because the happy path, the primary
succeeds, looks identical to code with no chain at all, so a test suite that
only exercises the happy path proves nothing about the pattern's actual
purpose.

- **Unit test the classification logic in isolation from any real network
  call.** Feed the chain's error classifier every distinct error shape the
  real providers are documented to return, a 429, a 529, a malformed schema
  response, a connection timeout, and assert which ones advance to the next
  target versus which are fatal and stop the chain immediately. This is the
  single highest-value test in the whole pattern, because a classification
  bug is invisible until the exact incident it mishandles occurs in
  production.
- **Fake every target as an injectable, deterministic function rather than
  mocking the HTTP layer.** A target that always fails N times then
  succeeds, a target that always fails, a target that succeeds instantly,
  composed in different chain orders, lets the chain's sequencing,
  aggregation, and result-envelope logic be tested in milliseconds with no
  network dependency and no flakiness. The code samples in dimension 8
  above use exactly this shape.
- **Test the total worst-case duration explicitly.** Construct a chain where
  every target fails after exhausting its own retry budget, and assert the
  chain's total elapsed time is bounded by the value computed in the
  dimension 11 fix for that failure mode, not merely that the chain
  eventually returns an aggregated error.
- **Test the aggregated failure path, not only the success path.** Assert
  that when every target fails, the caller receives a single error carrying
  the full ordered history of every attempt and every reason, rather than the
  last target's error swallowing the earlier ones, which is a common and
  easy-to-miss regression when a chain implementation is refactored.
- **Test idempotency across a simulated fallback for any tool-calling
  chain.** A test that runs the primary target through a partial success,
  the tool call executes, then the response itself errors, then a fallback
  target executes the same tool call, and asserts the downstream side effect
  happened exactly once, catches the duplicate-side-effect failure mode in
  dimension 11 before it reaches a real user.
- **In integration or staging environments, exercise a real fallback fire
  against a real second provider** at least once before the chain reaches
  production, because prompt-format translation differences between
  providers, a tool schema that one provider accepts and another rejects, a
  system-prompt convention one honors and another ignores, are exactly the
  kind of defect that only a real call against the real second provider
  surfaces, and a chain that has never actually fired its second link in a
  test environment is an untested code path shipped straight to an incident.

## 16. Observability signals

- **Which target answered each request**, as a labeled counter or a field on
  the structured log line for every completed request, is the single
  non-negotiable signal. Without it, every other signal in this dimension is
  unreachable, because there is no way to attribute latency, cost, or
  quality to a specific link in the chain.
- **Fallback-fire rate per target, over a rolling window**, alerted when the
  non-primary rate crosses a threshold that would be surprising during
  normal operation. A rising fallback-fire rate is the earliest available
  signal of a primary degrading, often visible in this metric well before
  the primary's own provider-side status page or error dashboard reflects
  the same incident.
- **Per-target latency distribution, not only an aggregate.** A chain's
  aggregate latency can look acceptable on average while its p99 is
  mostly made up of requests that exhausted a slow, failing primary
  before succeeding on a fast fallback. Separating the distribution by
  answering target reveals this immediately, while the aggregate hides it.
- **Per-target error taxonomy**, counted by the same classification labels
  the chain's own classifier uses, rate limited, overloaded, timeout,
  schema failure, fatal. This is what turns dimension 11's failure modes
  from a postmortem narrative into a dashboard a team checks before an
  incident becomes visible to users.
- **Cost attributed per target, per time window.** Because fallback targets
  are frequently priced differently than the primary, a chain that fires
  its fallback often can silently inflate spend well beyond what the
  primary's own pricing led anyone to budget for, and this is invisible
  without cost broken out by which target actually served each request.
- **A trace span per attempt inside a single logical request**, not one span
  for the whole chain, so a distributed trace shows exactly how many
  targets were tried, in what order, with what latency and outcome each,
  for any individual slow or failed request a team needs to investigate.

## 17. Security and privacy implications

Every target added to a fallback chain is a full additional data processor
for the request's content, and this has consequences a chain design cannot
treat as an afterthought.

- **Data residency and cross-border transfer.** A prompt that falls back
  from a target hosted in one jurisdiction to a target hosted in another
  crosses whatever data residency or export-control boundary the
  organization committed to for that data. A chain built without regard to
  where each target actually processes data can silently violate a
  contractual or regulatory commitment the moment its fallback fires, at
  exactly the moment, an incident, when nobody is watching that boundary
  closely. Microsoft's own Foundry Models documentation makes the residency
  distinction explicit at the deployment-type level precisely because
  different deployment types process data in different geographies
  (https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types,
  verified 2026-08-03), and the same distinction applies with more force
  across genuinely different providers rather than only across regions of
  one provider.
- **Prompt and response content reaching a new vendor's logs and training
  pipeline.** Different providers have different data retention and
  model-training-on-customer-data policies. A chain's fallback target
  should be held to at least the same data-handling contract as the
  primary before it is added, and the specific commitment each target makes
  should be recorded next to the chain's configuration, not assumed to
  match the primary by default.
- **Credential sprawl.** Every target is a separate API key or credential
  that must be issued, rotated, and revoked independently. A chain with
  several targets multiplies the number of credentials capable of
  exfiltrating whatever the chain sends them, and a leaked fallback
  credential that nobody remembers exists because it fires rarely is
  exactly the kind of forgotten, over-privileged secret that security
  reviews exist to catch.
- **Sensitive content reaching a lower-quality or less-trusted target during
  degraded conditions.** A chain designed purely around availability, with
  no content-sensitivity awareness, can route a request containing personal
  or regulated data to a fallback target the organization would never have
  chosen deliberately for that content, purely because the primary happened
  to be down at the moment the request arrived. A chain handling any
  regulated or sensitive content category needs either a content-aware
  filter on which targets are eligible fallbacks for that category, or an
  explicit decision that no fallback exists for that category at all and
  the request should fail visibly rather than degrade silently onto an
  unapproved target.
- **The aggregated failure log itself.** The full ordered attempt history
  this pattern's result envelope carries, per dimension 15, frequently
  includes fragments of the original prompt or error messages that echo
  request content. That log is exactly as sensitive as the request it
  describes and needs the same access controls and retention policy as any
  other store of the underlying content, not a lighter one only because it
  is technically an error log rather than a primary data store.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
   Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley,
   1994, chapter 4, Behavioral Patterns, Chain of Responsibility. Summary of
   the intent verified against
   https://en.wikipedia.org/wiki/Chain-of-responsibility_pattern, verified
   2026-08-03.
2. LiteLLM, Router documentation, model list, order-based failover, weighted
   failover, cooldown and retry policy, context window fallbacks.
   https://docs.litellm.ai/docs/routing, verified 2026-08-03.
3. LangChain, `RunnableWithFallbacks` and the `with_fallbacks` method,
   Runnables API reference.
   https://reference.langchain.com/python/langchain_core/runnables/, verified
   2026-08-03.
4. OpenRouter, Model Routing documentation, Auto Router graceful degradation
   to a default model set.
   https://openrouter.ai/docs/features/model-routing, verified 2026-08-03.
5. Netflix, Hystrix repository, fallback method concept and project
   maintenance-mode status.
   https://github.com/Netflix/Hystrix, verified 2026-08-03.
6. Anthropic, Claude API errors reference, HTTP status codes, error types
   including `429 rate_limit_error`, `500 api_error`, `529 overloaded_error`,
   and SDK default retry behavior.
   https://platform.claude.com/docs/en/api/errors, verified 2026-08-03.
7. Microsoft, Understanding deployment types in Microsoft Foundry Models,
   global deployment routing and regional interruption behavior.
   https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types,
   verified 2026-08-03.

## Code examples

The chain is implemented three times, in TypeScript, Python, and Go, each
with the identical shape. an ordered list of callable targets, a wrapper
that surfaces which target answered, and a fake flaky target used to prove
the fallback actually fires. Every sample below was compiled or run on this
machine before being included here.

### TypeScript

```typescript
type ChatResult = { text: string; model: string };

class ProviderError extends Error {
  constructor(public model: string, public retryable: boolean, message: string) {
    super(message);
  }
}

interface ChatProvider {
  readonly model: string;
  complete(prompt: string): Promise<ChatResult>;
}

async function withTimeout<T>(p: Promise<T>, ms: number): Promise<T> {
  let timer: ReturnType<typeof setTimeout>;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new Error("timeout")), ms);
  });
  try {
    return await Promise.race([p, timeout]);
  } finally {
    clearTimeout(timer!);
  }
}

async function callWithFallback(
  providers: ChatProvider[],
  prompt: string,
  timeoutMs = 5000
): Promise<ChatResult> {
  const errors: ProviderError[] = [];
  for (const provider of providers) {
    try {
      return await withTimeout(provider.complete(prompt), timeoutMs);
    } catch (err) {
      const wrapped =
        err instanceof ProviderError
          ? err
          : new ProviderError(provider.model, true, String(err));
      errors.push(wrapped);
      if (!wrapped.retryable) throw wrapped;
    }
  }
  throw new AggregateError(errors, "all providers in fallback chain failed");
}

// A target that fails a fixed number of times, then answers.
// Stands in for a provider recovering from a transient overload.
class FlakyProvider implements ChatProvider {
  constructor(public model: string, private failTimes: number) {}
  async complete(prompt: string): Promise<ChatResult> {
    if (this.failTimes > 0) {
      this.failTimes -= 1;
      throw new ProviderError(this.model, true, "overloaded_error");
    }
    return { text: `reply from ${this.model} to: ${prompt}`, model: this.model };
  }
}

async function main() {
  const chain: ChatProvider[] = [
    new FlakyProvider("primary-large", 1),
    new FlakyProvider("secondary-medium", 0),
  ];
  const result = await callWithFallback(chain, "hello");
  console.log(JSON.stringify(result));
}

main();
```

Compiled with `npx tsc --target es2021 --module commonjs --lib es2021,dom --strict test.ts` and run with `node test.js` on this machine.

```
{"text":"reply from secondary-medium to: hello","model":"secondary-medium"}
```

The output confirms the first target's error was caught, the second target
was tried, and the result envelope names the target that actually answered.

### Python

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Sequence


class ProviderError(Exception):
    def __init__(self, model: str, retryable: bool, message: str) -> None:
        super().__init__(message)
        self.model = model
        self.retryable = retryable


@dataclass
class ChatResult:
    text: str
    model: str


class ChainExhausted(Exception):
    def __init__(self, errors: Sequence[ProviderError]) -> None:
        super().__init__("all providers in fallback chain failed")
        self.errors = list(errors)


def call_with_fallback(
    providers: Sequence[Callable[[str], ChatResult]],
    prompt: str,
) -> ChatResult:
    errors: list[ProviderError] = []
    for provider in providers:
        try:
            return provider(prompt)
        except ProviderError as exc:
            errors.append(exc)
            if not exc.retryable:
                raise
    raise ChainExhausted(errors)


# A target that fails a fixed number of times, then answers.
def make_flaky(model: str, fail_times: int) -> Callable[[str], ChatResult]:
    state = {"remaining": fail_times}

    def call(prompt: str) -> ChatResult:
        if state["remaining"] > 0:
            state["remaining"] -= 1
            raise ProviderError(model, True, "overloaded_error")
        return ChatResult(text=f"reply from {model} to: {prompt}", model=model)

    return call


def main() -> None:
    chain = [make_flaky("primary-large", 1), make_flaky("secondary-medium", 0)]
    result = call_with_fallback(chain, "hello")
    print(result)


if __name__ == "__main__":
    main()
```

Run with `python3 test.py` on this machine.

```
ChatResult(text='reply from secondary-medium to: hello', model='secondary-medium')
```

The same behavior as the TypeScript sample, proving the pattern's shape is
language-independent.

### Go

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

type ChatResult struct {
	Text  string
	Model string
}

type ProviderError struct {
	Model     string
	Retryable bool
	Message   string
}

func (e *ProviderError) Error() string {
	return fmt.Sprintf("%s: %s", e.Model, e.Message)
}

type ChatProvider interface {
	Model() string
	Complete(ctx context.Context, prompt string) (ChatResult, error)
}

func CallWithFallback(ctx context.Context, providers []ChatProvider, prompt string, perCallTimeout time.Duration) (ChatResult, error) {
	var errs []error
	for _, p := range providers {
		callCtx, cancel := context.WithTimeout(ctx, perCallTimeout)
		result, err := p.Complete(callCtx, prompt)
		cancel()
		if err == nil {
			return result, nil
		}
		var pe *ProviderError
		if errors.As(err, &pe) && !pe.Retryable {
			return ChatResult{}, err
		}
		errs = append(errs, err)
	}
	return ChatResult{}, fmt.Errorf("all providers in fallback chain failed: %w", errors.Join(errs...))
}

// A target that fails a fixed number of times, then answers.
type flakyProvider struct {
	model     string
	failTimes int
}

func (f *flakyProvider) Model() string { return f.model }

func (f *flakyProvider) Complete(ctx context.Context, prompt string) (ChatResult, error) {
	if f.failTimes > 0 {
		f.failTimes--
		return ChatResult{}, &ProviderError{Model: f.model, Retryable: true, Message: "overloaded_error"}
	}
	return ChatResult{Text: fmt.Sprintf("reply from %s to: %s", f.model, prompt), Model: f.model}, nil
}

func main() {
	chain := []ChatProvider{
		&flakyProvider{model: "primary-large", failTimes: 1},
		&flakyProvider{model: "secondary-medium", failTimes: 0},
	}
	result, err := CallWithFallback(context.Background(), chain, "hello", 5*time.Second)
	if err != nil {
		panic(err)
	}
	fmt.Println(result)
}
```

Run with `go run main.go` on this machine.

```
{reply from secondary-medium to: hello secondary-medium}
```

The identical outcome as the other two samples.
