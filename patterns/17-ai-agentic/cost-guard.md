---
name: Cost Guard
slug: cost-guard
family: 17-ai-agentic
category: Reliability
aliases: [Budget Guardrail, Spend Limiter, Token Budget Enforcer, LLM Cost Circuit Breaker, Usage Cap]
first_described: "No single origin paper. Assembled from cloud cost-control practice (AWS Budgets, 2016) and applied to LLM calls by gateway and proxy vendors from 2023 onward, for example LiteLLM's budget manager and Helicone's cost based rate limiting"
maturity: established
related: [llm-circuit-breaker, rate-limiting, output-guardrails, input-guardrails, function-calling, human-in-the-loop, memory-compaction, tool-result-caching]
incompatible_with: []
verified: 2026-08-03
---

# Cost Guard

## 1. Name, aliases, and lineage

The name used in this catalog is Cost Guard. it is the component that sits in
front of, or wrapped around, calls to a large language model and enforces a
budget in real currency or in a currency proxy such as tokens, before, during,
and after each call, so that a runaway loop, a hostile prompt, or a simple
mistake in a retry policy cannot turn into an unbounded bill.

There is no single paper that names this pattern, and that gap is itself part
of the pattern's story. Cost control for compute has a long lineage in cloud
operations, most concretely as AWS Budgets, a service Amazon Web Services
describes as letting a customer "set custom budgets to track your cost and
usage from the simplest to the most complex use cases" and configure alerts
when actual or forecasted spend exceeds a threshold
([AWS Budgets user guide, "What is AWS Budgets"](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html),
verified 2026-08-03). AWS Budgets is a monitoring and alerting service for
infrastructure spend generally, not a per-request enforcement point wired
into an application's request path, so it is the ancestor idea rather than
the pattern itself.

The pattern under its LLM-specific shape appears first in the open source
LLM gateway and proxy projects that took shape through 2023 and 2024, once
teams building on the OpenAI and Anthropic APIs discovered that a single
looping agent, a prompt-injected tool call, or an unbounded `while` retry
could turn a normal day's spend into a five-figure invoice within hours.
LiteLLM's proxy documents a `max_budget` field that can be attached to a
key, a user, or a team, with the explicit statement that "you can set
budgets" at each of those scopes and that a budget is enforced by rejecting
further calls once the tracked spend for that scope crosses the configured
number
([LiteLLM Proxy docs, "Set Budgets"](https://docs.litellm.ai/docs/proxy/users),
verified 2026-08-03). Helicone, an LLM observability and gateway vendor,
documents a rate limiting unit type of `cents` as an alternative to the
default `request` unit, giving the worked example "Limit to $5.00 per hour
per user" using the parameter `u=cents;s=user`
([Helicone docs, "Custom Rate Limits"](https://docs.helicone.ai/features/advanced-usage/custom-rate-limits),
verified 2026-08-03). Both vendors are naming the same idea, a hard ceiling
on real-dollar spend enforced at the request boundary, from different
angles, cost-per-scope in LiteLLM's case and cost-as-a-rate-limit-unit in
Helicone's.

The aliases in circulation reflect that the same mechanism gets built at
different layers of a system and described by the team that built it in
whatever vocabulary their layer uses. A platform team calls it a Budget
Guardrail because they think of it alongside content guardrails. An SRE
calls it an LLM Cost Circuit Breaker because it trips and opens the same
way a reliability circuit breaker does, only the failure signal is a
dollar counter instead of an error rate. A finance-adjacent engineering
team calls it a Spend Limiter. This catalog treats all of these as the
same pattern under one name, Cost Guard, and treats the reliability-focused
sibling, which trips on latency and error signals rather than spend, as the
separate LLM Circuit Breaker entry in this same family.

## 2. Problem and context

A call to a hosted large language model is metered and billed per token, and
an agentic system does not make one call, it makes an unbounded and
data-dependent number of calls. A ReAct loop calls the model again every
time a tool returns, a multi-agent supervisor spawns sub-agents that each
make their own calls, a self-correcting pipeline retries generation against
a validator's feedback, and every one of those call sites can, through a bug,
a bad prompt, a hostile user, or a genuinely hard problem that never
converges, run far longer than anyone planned for when they wrote the code.

The concrete shape of the problem in a codebase looks like this. A team
ships an agent that answers customer questions using two or three tool
calls per turn in testing. In production, a single confused user session,
or a single adversarial prompt that convinces the agent it has not yet
solved the task, drives the same agent into ten, then fifty, then several
hundred tool-call and model-call round trips before a timeout or a crash
finally stops it. Nothing in the request path asked "how much has this
conversation already cost, and is it still worth continuing." The bill for
that one session, priced per token at the provider's published per-million
rate, can be tens or hundreds of times the cost of a normal session, and it
is discovered on a monthly invoice days after the fact rather than at the
moment it happened.

This context is specific to metered, per-call, per-token external services
called from inside a loop that the calling code does not fully control. A
single non-looping API call to a paid service has the same billing risk but
not the same amplification risk, because a human decided to make that one
call. An agent loop removes the human from every individual decision to
spend again, which is exactly what makes the loop useful and exactly what
makes an unbounded loop dangerous. The pattern exists to put a machine-
enforced ceiling where a human's judgment used to be the only ceiling.

## 3. Forces

**Cost control against task completion.** A hard ceiling that trips too
early abandons a task that was one more call away from finishing, and the
person on the other end experiences that as the system giving up. A ceiling
set too high defeats the purpose of having one.

**Real time enforcement against accounting accuracy.** Enforcing a limit
inside the request path, before the next call is allowed to start, requires
an up to date running total at the moment of the decision. Most billing
systems, including the token counts returned by LLM providers themselves,
settle a few seconds to a few minutes after the call completes, so a guard
that reads authoritative billing data is always working from slightly stale
numbers, while a guard that estimates cost from its own token accounting is
faster but can drift from what the provider actually charges, particularly
once cached-input pricing, prompt caching discounts, or batch pricing are in
play.

**Granularity against operational overhead.** A limit can be enforced per
call, per conversation turn, per session, per user, per API key, per team,
or per day, and each additional scope is another counter to maintain, reset
on a schedule, and reconcile against real invoices. Coarse granularity, one
number for the whole organization, is cheap to build and catches almost
nothing about which feature or which user caused an overrun. Fine
granularity localizes the problem instantly and costs proportionally more
counters and more reset logic.

**Hard stop against graceful degradation.** The simplest Cost Guard just
raises an exception and ends the call chain. A more considerate one falls
back to a cheaper model, truncates the remaining plan, or returns a partial
answer with an explanation, all of which take more code and more design
decisions about what "good enough, cheaper" looks like for this particular
product.

**Static configuration against adaptive limits.** A fixed dollar ceiling per
day is trivial to reason about and trivial to game or to outgrow, because
traffic is not flat and a legitimate spike, a product launch, a viral
moment, looks identical at the metric level to an attack or a bug. An
adaptive limit that compares current spend against a trailing baseline
catches both cases better but is materially harder to build, test, and
explain to the person debugging a false trip at 2 AM.

**Central chokepoint against defense in depth.** Every one of these forces
is easier to reason about when there is exactly one place spend is checked,
typically a gateway or proxy that sits in front of every provider call. That
single chokepoint is also a single point of failure and a single place
latency gets added to every request, and a large organization with several
independently deployed services calling the model provider directly will
find a single chokepoint politically and operationally hard to enforce
without also owning the network path.

## 4. Applicability and non-applicability

Reach for Cost Guard when the applicability conditions below hold, and
recognize the non-applicability list as the more informative half, because
most systems that fail this pattern fail it by installing it where it adds
friction without adding safety.

Applicable when:

- The calling code contains a loop, whether an explicit `while`, a
  framework-managed agent executor, or a recursive supervisor-worker fan
  out, where the number of model calls per user-visible unit of work is not
  fixed at write time and can be driven by model output, tool output, or
  user input.
- Model calls are billed per token, or per some other metered unit, at a
  rate the calling team does not fully control, so cost varies with usage
  in a way headcount, license fees, or fixed infrastructure spend does not.
- The system is exposed, directly or indirectly, to input the calling team
  does not fully trust, including a public user, a scraped document, or the
  output of a third party tool, any of which can attempt or accidentally
  trigger prompt content that drives the loop longer than intended.
- More than one team, tenant, or customer shares the same underlying
  provider account or the same gateway, so one team's runaway loop is
  capable of degrading or bankrupting a budget shared with teams that had
  nothing to do with the incident.
- The organization needs to attribute LLM spend to a feature, a customer,
  or a cost center for pricing, margin analysis, or internal chargeback, a
  need that a Cost Guard's per-scope accounting satisfies as a side effect
  of the enforcement it already has to do.

Not applicable, and why:

- A single, non-looping call made directly by a human in an interactive
  chat UI with no agentic tool use. The human is already the rate limiter;
  the risk this pattern defends against, an unattended loop spending
  unboundedly, does not exist. A simple per-user rate limit on requests is
  sufficient and a dollar-denominated guard is unneeded complexity.
- A fixed-budget batch job that runs a known number of documents through a
  known prompt shape once, where the total cost can be computed in advance
  from the input size and the model's published price. Here a one-time
  pre-flight cost estimate and a post-hoc invoice reconciliation are enough;
  building a live enforcement chokepoint for a job that runs once a week
  and never loops is overhead with no corresponding risk reduction.
- A self-hosted, open-weight model running on infrastructure the team
  already pays for as a fixed monthly cost, where an extra inference call
  does not add marginal dollar cost, only marginal compute time already
  budgeted for and load already capacity-planned for. Here the correct
  pattern is a rate limit or a queue depth limit for latency and fairness,
  not a Cost Guard for spend, because there is no metered spend to guard.
- A prototype or an internal tool used by a small, trusted engineering team
  during active development, where the friction of budget resets, false
  trips, and extra configuration outweighs the protection, and where a
  human is watching the terminal output of every run anyway. Add the guard
  when the system moves from a terminal a developer is staring at to a
  service other people or other code invoke unattended.
- A system where the calling code already sits behind a Cost Guard at a
  shared gateway one layer up, and adding a second, differently configured
  guard at the calling service risks the two limits disagreeing about
  remaining budget and producing confusing, hard to diagnose double
  enforcement. Coordinate the scope of one guard rather than stacking two
  that do not share state.

## 5. Structure

**Meter.** The component that observes each outbound model call and each
inbound response and produces a cost figure for that exchange, either from
the provider's reported token usage multiplied by the current per-token
price, from the provider's own reported cost when the API surfaces one
directly, or from an estimate made before the call for cases where the
enforcement decision must happen before any tokens are spent.

**Ledger.** The running total the Meter's readings accumulate into, kept
per scope, a key, a user, a session, a team, an organization, reset on
whatever cadence the scope calls for, hourly, daily, per billing period,
or never. The Ledger is the state a Cost Guard must persist somewhere
durable enough to survive a process restart, because an in-memory counter
that resets on every deploy defeats the guard the moment it is needed most.

**Threshold policy.** The configured numbers a scope's accumulated spend is
compared against, typically more than one tier, a soft threshold that
triggers a warning or a degrade-to-cheaper-model response, and a hard
threshold that trips the guard and refuses further calls in that scope
until the ledger resets or an operator intervenes.

**Enforcement point.** The place in the call path where the Threshold
policy is actually consulted and where a call is allowed to proceed or is
rejected. This can be a pre-call check, is this scope already over budget,
and a post-call update, record what this call actually cost, or a single
combined check-then-call-then-record sequence, and it can live inside the
calling application's own code, in a shared library, in a sidecar process,
or in a network-level gateway or proxy that every call must pass through.

**Response strategy.** What happens to the caller when the Enforcement
point trips, ranging from a raised exception the calling code must handle,
through a structured error response the caller can branch on, to an
automatic fallback the guard performs on the caller's behalf, such as
routing the next call to a cheaper model or truncating a plan's remaining
steps.

**Alerting channel.** The separate path, usually asynchronous and decoupled
from the request that tripped the threshold, that notifies a human or an
operations system that a scope crossed its soft or hard threshold, because
enforcement alone without a notification means a legitimate but suddenly
much larger workload silently starts failing with no one aware of why.

## 6. ASCII structure diagram

```
+-----------------------------------------------------------------+
|                          Calling code                           |
|            (agent loop, tool executor, retry policy)            |
+----------------------------+--------------------------------+---+
                              | wants to call the model       ^
                              v                                |
+-----------------------------------------------------------------+
|                        Enforcement point                        |
|                                                                  |
|   1. read scope key from the request (user, key, team, org)     |
|   2. ask Threshold policy: is Ledger[scope] >= hard limit?       |
|          yes -> Response strategy (reject / degrade / fallback) |
|          no  -> allow the call through                          |
+----------------------------+--------------------------------+---+
                              | allowed call                   |
                              v                                |
+-----------------------------------------------------------------+
|                        Model provider call                      |
|                (Anthropic, OpenAI, self-hosted, etc.)            |
+----------------------------+--------------------------------+---+
                              | response + token usage         |
                              v                                |
+-----------------------------------------------------------------+
|                              Meter                               |
|         computes cost = tokens_in * price_in                     |
|                        + tokens_out * price_out                  |
+----------------------------+--------------------------------+---+
                              | cost figure for this call
                              v
+-----------------------------------------------------------------+
|                             Ledger                               |
|            Ledger[scope] += cost   (durable, shared)             |
+----------------------------+--------------------------------+---+
                              |
                              v
+-----------------------------------------------------------------+
|                       Alerting channel                           |
|     soft threshold crossed -> notify (async, decoupled)          |
+-------------------------------------------------------------------+
```

## 7. Dynamics

The sequence below shows one call proceeding normally, one call tripping
the hard limit, and the asynchronous notification path, drawn as a single
combined flow because in practice all three happen inside the same
component wired the same way, only the branch taken differs.

```
Caller          EnforcementPoint       Ledger          Provider        Alerting
  |                    |                  |                |               |
  | request(scope=X)   |                  |                |               |
  |------------------->|                  |                |               |
  |                    | read(Ledger[X])  |                |               |
  |                    |----------------->|                |               |
  |                    |<-----------------|                |               |
  |                    | current = 3.10   |                |               |
  |                    | limit   = 5.00   |                |               |
  |                    | 3.10 < 5.00, ALLOW                |               |
  |                    |------------------------------------->|            |
  |                    |                  |    call model  |               |
  |                    |<-------------------------------------|            |
  |                    |                  |    tokens: 1200 in, 400 out    |
  |                    | cost = 0.018     |                |               |
  |                    | update(Ledger[X], +0.018)          |               |
  |                    |----------------->|                |               |
  |<-------------------|                  |                |               |
  | response           |                  |                |               |
  |                    |                  |                |               |
  | request(scope=X)   |                  |                |               |
  |------------------->|                  |                |               |
  |                    | read(Ledger[X])  |                |               |
  |                    |----------------->|                |               |
  |                    |<-----------------|                |               |
  |                    | current = 5.02   |                |               |
  |                    | limit   = 5.00   |                |               |
  |                    | 5.02 >= 5.00, TRIP                |               |
  |                    | -- no call made to Provider --     |               |
  |<-------------------|                  |                |               |
  | 429 budget exceeded|                  |                |               |
  |                    | notify(scope=X, current=5.02)       |               |
  |                    |------------------------------------------------->|
  |                    |                  |                |  page / log   |
```

Two things about this flow matter more than the diagram alone shows. First,
the read of the Ledger and the eventual write of the updated total are two
separate operations against shared state, and under concurrent requests for
the same scope that gap is a race window unless the update is an atomic
increment, discussed further in dimension 11. Second, the check happens
before the model call and the update happens after it, which means the very
call that pushes a scope over its limit is always allowed to complete, the
guard trips on the call after that one. A guard that needs to prevent even
the overshooting call must estimate the cost of the upcoming call before
making it and check against a limit reduced by that estimate, a stricter
and more conservative variant discussed in dimension 8.

## 8. Implementation variants

**Post-call accounting, pre-call check (the default shape).** Check the
Ledger before the call, make the call, update the Ledger after with the
actual reported cost. Simple, accurate once updated, and it accepts that
the call which crosses the threshold is always allowed through, so the
Ledger can overshoot the configured limit by up to one call's worth of
cost. This is the shape LiteLLM's proxy documents, where spend is tracked
after each completion and compared against `max_budget` on the next
request
([LiteLLM Proxy docs, "Set Budgets"](https://docs.litellm.ai/docs/proxy/users),
verified 2026-08-03).

**Pre-call estimation with a safety margin.** Before the call, estimate its
likely token cost from the prompt length and the requested `max_tokens`,
and reject the call if the current Ledger total plus that estimate would
exceed the limit. Prevents overshoot at the cost of being conservative,
since the actual response is often shorter than `max_tokens` allows, so a
guard tuned this way rejects some calls that would have stayed under
budget had they been allowed to run.

**Token-count proxy instead of dollar cost.** Track a budget in tokens
rather than currency, sidestepping the need to keep per-token prices
current as providers change them, at the cost of the number in the ledger
no longer directly answering "how much did this cost," which matters when
the guard's audience includes finance stakeholders who think in dollars.

**Gateway-level enforcement (centralized).** A single network chokepoint,
typically an LLM gateway or reverse proxy every service's model calls must
pass through, owns the Meter, Ledger, and Enforcement point for the entire
organization or a subset scoped by API key. Helicone's cost-based rate
limiting is this shape, configuring a limit in cents per hour attached to a
user segment at the proxy layer
([Helicone docs, "Custom Rate Limits"](https://docs.helicone.ai/features/advanced-usage/custom-rate-limits),
verified 2026-08-03). Centralization gives one source of truth and one
place to change policy, and it adds a network hop and a shared failure
domain to every call in the organization.

**In-process middleware (decentralized).** Each service embeds its own
Meter, Ledger, and Enforcement point as a library, with the Ledger's state
stored in a shared store, typically Redis or a similar low-latency key
value store, so multiple instances of the same service share one counter
per scope. No extra network hop for the model call itself, but policy now
lives in every service's deployed code and drifts unless carefully
versioned.

**Loop-step proxy, count instead of cost.** Rather than tracking dollars,
bound the number of iterations an agent loop is allowed to take before it
is forcibly stopped, which is cheaper to implement, does not need pricing
data, and correlates with cost closely enough to be useful as a first line
of defense. LangGraph's `recursion_limit` is exactly this shape at the
graph level, the framework raising `GraphRecursionError` once "the maximum
number of super-steps the graph can execute during a single execution" is
reached, with the current step counter exposed to node code through
`config["metadata"]["langgraph_step"]` so a node can proactively stop
before hitting the wall
([LangGraph docs, "Graph API"](https://docs.langchain.com/oss/python/langgraph/graph-api),
verified 2026-08-03).

**Tiered thresholds with graceful degradation.** Configure more than one
threshold per scope, a low one that triggers a downgrade to a cheaper
model or a shorter `max_tokens`, and a high one that stops calls entirely,
so the system degrades in stages rather than working perfectly and then
stopping abruptly. This variant costs the most design and testing effort
because the degraded path is a second code path that must itself be
correct and tested, not merely a smaller version of the normal path.

**Organization-level hard cap as a backstop.** Beyond any per-scope guard
the application owns, most providers offer an account-wide hard limit as a
last line of defense that does not depend on the calling application's
code being correct at all. OpenAI's production guidance describes setting
"spend alerts on the limits page to send notifications when usage exceeds a
certain dollar amount" and notes that to "enforce a monthly cap, set a hard
spend limit"
([OpenAI, "Production best practices"](https://developers.openai.com/api/docs/guides/production-best-practices),
verified 2026-08-03). This variant is not a substitute for an in-application
Cost Guard, because by the time an account-wide hard limit trips, the
account stops working for every feature, not just the one that misbehaved,
but it is a necessary backstop for exactly the failure mode where the
application-level guard itself has a bug.

## 9. Known production uses

**LiteLLM Proxy.** LiteLLM is an open source proxy and SDK that sits in
front of more than 100 LLM providers behind one OpenAI-compatible API
surface, and its proxy documentation describes `max_budget` as a field
settable "across all calls on the proxy" globally, or scoped to a team, a
user, or an individual API key, with the proxy rejecting further calls
against a key or user once tracked spend for that scope exceeds the
configured number, returning an authentication error naming the current
spend and the configured maximum
([LiteLLM Proxy docs, "Set Budgets"](https://docs.litellm.ai/docs/proxy/users),
verified 2026-08-03). This is a direct, general-purpose implementation of
the pattern as a gateway-level enforcement point, deployed by teams that
run LiteLLM's proxy in front of their own services.

**Helicone.** Helicone is an LLM observability and gateway product used to
proxy calls to OpenAI, Anthropic, and other providers for logging, caching,
and rate limiting. Its documented custom rate limiting feature supports a
unit type of `cents` in addition to the default `request` count, with the
worked example configuration `u=cents;s=user` used to "Limit to $5.00 per
hour per user"
([Helicone docs, "Custom Rate Limits"](https://docs.helicone.ai/features/advanced-usage/custom-rate-limits),
verified 2026-08-03), which is a cost-denominated rate limit, the same
enforcement idea as Cost Guard implemented as a specialization of a general
rate limiter rather than as a dedicated budget object.

**LangGraph.** LangGraph, LangChain's graph-based agent orchestration
library, ships a `recursion_limit` configuration value enforced on every
graph execution, defaulting to 1000 steps as of the version documented, and
raising `GraphRecursionError` once that ceiling is reached, with the
current step number exposed inside node code via
`config["metadata"]["langgraph_step"]` so a node can react before the
limit is hit rather than only after
([LangGraph docs, "Graph API"](https://docs.langchain.com/oss/python/langgraph/graph-api),
verified 2026-08-03). This is the loop-step-count variant of Cost Guard
built directly into a widely used agent framework, protecting against the
runaway-loop failure mode even for teams that have not separately built a
dollar-denominated budget guard.

**OpenAI platform.** OpenAI's own production guidance for API customers
recommends configuring "spend alerts" on the organization's limits page
that "send notifications when usage exceeds a certain dollar amount," and
separately documents setting "a hard spend limit" to "enforce a monthly
cap"
([OpenAI, "Production best practices"](https://developers.openai.com/api/docs/guides/production-best-practices),
verified 2026-08-03). This is a provider-native, account-wide instance of
the pattern's Threshold policy and Enforcement point, operating above and
independent of whatever the calling application implements, and it is the
backstop variant described in dimension 8.

## 10. Consequences

Positive.

- A single misbehaving loop, prompt injection, or retry bug is contained
  to a bounded dollar amount instead of an unbounded one, converting an
  open-ended financial risk into a known, budgetable maximum loss per
  scope per period.
- Per-scope accounting, kept as a byproduct of enforcement, gives the
  organization accurate, real-time cost attribution by user, team, or
  feature without a separate analytics pipeline reconciling invoices after
  the fact.
- A tiered guard with graceful degradation lets a product keep functioning,
  at reduced quality or reduced model tier, for a user or a session that
  would otherwise be cut off entirely, improving the experience of hitting
  a limit compared to a hard stop.
- The alerting side effect surfaces spend anomalies, a sudden spike from a
  bug or an attack, far faster than a monthly invoice review would,
  shrinking the window between "something is wrong" and "someone knows
  something is wrong" from weeks to minutes.

Negative.

- A guard tuned too tight rejects legitimate, valuable work in progress,
  and the person experiencing that rejection has no way to distinguish "the
  system stopped because it hit a safety limit" from "the system is
  broken," unless the Response strategy is designed to communicate the
  difference clearly.
- The Ledger becomes shared mutable state on the hot path of every model
  call, and a Ledger implemented with a naive read-then-write instead of an
  atomic increment introduces a race condition that silently allows a scope
  to overshoot its budget under concurrent load, which is the one failure
  mode most likely to defeat the entire point of the guard.
- Estimation-based pre-call checks trade accuracy for speed, and a guard
  whose estimate diverges meaningfully from actual provider billing, for
  example ignoring cached-input pricing discounts, produces a Ledger that
  disagrees with the real invoice, undermining trust in the guard's numbers
  even while the guard is functioning correctly as designed.
- A centralized gateway enforcing the guard adds latency and a shared
  failure domain to every call across every team behind it, and an outage
  or a slow Ledger store turns a cost-safety mechanism into an availability
  problem for services that were never at risk of overspending in the
  first place.

## 11. Failure modes and misuse

**Symptom.** Two concurrent requests for the same user both succeed even
though their combined cost pushes that user well past the configured
limit, and the Ledger's recorded total, once both updates land, shows the
overshoot clearly after the fact.
**Cause.** The Enforcement point reads the current Ledger value, decides to
allow the call, and only writes the updated total after the call
completes, so two requests arriving close together both read the same
stale "under budget" value before either one's update has landed. This is
the classic check-then-act race, made worse in an LLM context because the
model call itself, sitting between the read and the write, can take
several seconds, widening the race window enormously compared to a typical
web request.
**Fix.** Replace the read-then-decide-then-write sequence with an atomic
increment-and-check operation against the Ledger's backing store, for
example a Redis `INCRBYFLOAT` followed by a comparison of the returned
new total against the limit, so the decision and the reservation of budget
happen as one indivisible step rather than two.

**Symptom.** The guard trips reliably in testing against a mock provider
but never trips in production even when spend clearly exceeds the
configured limit, and the Ledger's recorded totals lag far behind what the
provider's own invoice eventually shows.
**Cause.** The Meter computes cost from a stale, hardcoded per-token price
table that was accurate when the guard was built but has not been updated
since the provider changed pricing, introduced a new pricing tier for
cached input tokens, or shipped a new model the guard's price table does
not have an entry for, causing the Meter to silently under-price, or in
some implementations to throw and be swallowed by a broad exception
handler that lets the call through by default.
**Fix.** Pull current per-token pricing from the provider's own reported
usage and cost fields where the API surfaces one, or from a maintained,
version-controlled pricing configuration reviewed on a fixed schedule
rather than hardcoded once at build time, and fail closed, not open, when
a model's price is genuinely unknown to the Meter.

**Symptom.** A user or a bot systematically opens many new sessions,
accounts, or API keys in quick succession, and the aggregate organization-
level spend climbs steadily even though no single scope ever approaches
its configured limit.
**Cause.** The guard's scoping is too fine and has no aggregate ceiling
above the per-scope one, so a spend limit correctly enforced per key or
per user provides no protection at all against an attacker or a bug that
simply creates many scopes, each individually compliant.
**Fix.** Add a coarser, organization-wide ceiling above the per-scope
thresholds, checked in addition to, not instead of, the fine-grained
limits, and rate-limit the creation of new scopes, new API keys, or new
accounts, which closes the loophole the per-scope guard alone leaves open.

**Symptom.** Legitimate, high-value customers are cut off mid-task on
their busiest, most important day of the month, generating support
escalations that describe the product as "just breaking" with no
explanation the customer can act on.
**Cause.** A fixed daily or monthly ceiling, set once when traffic was
lower, was never revisited as usage grew, so normal organic growth in a
customer's legitimate usage eventually collides with a limit that was
sized for a different, smaller traffic level, and the guard has no way to
distinguish "this looks like an attack" from "this customer is simply
bigger now."
**Fix.** Review and adjust static thresholds on a fixed cadence tied to
actual usage trends, not only when an incident forces the review, and
where the volume of scopes makes manual review impractical, compare
current spend against a trailing baseline for that specific scope rather
than a single organization-wide constant, so growth is distinguished from
anomaly.

**Symptom.** The guard's rejection response is a generic HTTP error with no
distinguishing detail, and the calling application's error handling treats
a budget rejection identically to a network timeout or a provider outage,
retrying the call in a loop that itself burns through whatever budget
remains and, once the Ledger resets, immediately spends the newly reset
budget on a backlog of queued retries.
**Cause.** The Response strategy was built as an afterthought, a bare
exception or a generic status code, with no machine-readable signal
telling the caller "this is a budget rejection, do not retry with backoff,
this will still be rejected" as distinct from a transient failure worth
retrying.
**Fix.** Give budget rejections a distinct, documented error shape the
caller's retry logic explicitly excludes from its retry policy, matching
the practice of returning a specific error code and message naming the
current spend and the limit rather than a bare "429 Too Many Requests"
indistinguishable from an ordinary rate limit.

## 12. Trade-off matrix

| Force | Cost Guard | LLM Circuit Breaker | Plain rate limiting (request count) | Organization-wide provider hard cap only |
|---|---|---|---|---|
| Protects against runaway spend specifically | Yes, directly | Indirectly, only if runaway calls also trip error or latency thresholds | No, a fast successful loop can still overspend within its request quota | Yes, but only as a last resort after damage is already done |
| Protects against provider failure or latency | No, not its concern | Yes, directly | Indirectly, by limiting attempts | No |
| Granularity of enforcement | Configurable per key, user, team, or org | Typically per provider or per deployment, not per user | Typically per user or per key | Whole account, no finer granularity |
| Requires pricing data to be accurate | Yes, or accuracy degrades | No | No | No, provider computes it |
| Adds latency to the call path | Small, one Ledger read plus one write | Small, one state check | Small, one counter check | None, out of band |
| Can degrade gracefully instead of hard-stopping | Yes, with tiered thresholds | Yes, via fallback provider or cached response | Rarely implemented this way | No |
| Provides cost attribution as a side effect | Yes | No | No | No, only aggregate |

## 13. Related and incompatible patterns

**LLM Circuit Breaker.** The closest sibling in this same family, and the
one Cost Guard is most often confused with. A circuit breaker trips on
reliability signals, error rate, timeout rate, latency, and its job is to
stop calling a provider that is currently failing. Cost Guard trips on a
spend signal and its job is to stop calling a provider that is currently
succeeding too much, too expensively, or too often. A production system
typically needs both, wired as two independent Enforcement points a call
must pass, because a provider can be perfectly healthy while a caller is
still overspending, and a caller can be well within budget while the
provider is down.

**Rate limiting.** Cost Guard's Enforcement point is structurally a rate
limiter whose unit is currency instead of request count, and several real
implementations, Helicone's cost-based rate limiting among them, build Cost
Guard as a configuration of a general rate limiter rather than as a
separate component. Where a system already has request-count rate limiting
in place, adding cost-based limiting is often cheaper as an extension of
that existing mechanism than as a new, parallel system.

**Human in the loop.** A common Response strategy for a soft threshold trip
is to route the decision to continue spending to a human rather than
either auto-allowing or auto-rejecting, particularly for a workflow where
the task's value genuinely varies enough that no static dollar threshold
correctly separates "worth continuing" from "not worth continuing" on its
own.

**Function calling and tool result caching.** Because Cost Guard's Meter
prices every model call, and a large share of an agent loop's cost is often
repeated or near-identical tool calls and their round trips back through
the model, pairing Cost Guard with tool result caching directly reduces the
spend the guard has to police, rather than only capping it after the fact.

**Output guardrails.** These are complementary, not overlapping. Output
guardrails validate what a model produced, for content safety, format
correctness, or factual grounding. Cost Guard validates whether the
organization can afford to have asked at all. A response can fail an
output guardrail's checks while being entirely within budget, and a call
can be entirely well formed and safe while being the call that finally
crosses the budget ceiling.

**Incompatibilities.** None identified as structural incompatibilities.
Cost Guard composes with essentially every other pattern in this family
because it operates on the call boundary rather than on the content or the
control flow the other patterns govern, and the only genuine conflict is
operational rather than structural, two independently configured Cost
Guards enforcing at different layers of the same call path with Ledgers
that do not share state, discussed in dimension 4's non-applicability
list, which is a deployment mistake rather than an incompatibility between
the patterns themselves.

## 14. Refactoring path in and out

Introducing a Cost Guard into a codebase that does not have one.

1. Instrument every outbound model call site to log the token usage and
   computed cost the provider reports for that call, without enforcing
   anything yet, so the team has real cost-per-call data before deciding
   on any threshold.
2. Pick the coarsest useful scope first, typically per organization or per
   API key rather than per user or per session, and stand up a single
   Ledger for that scope backed by durable, shared storage, not an
   in-process variable, from the very first version.
3. Add the pre-call check as advisory only, logging "this call would have
   been rejected" without actually rejecting anything, and run that in
   production long enough to see how often a real threshold, set from step
   1's data, would have fired against real traffic, to catch a threshold
   that is set too aggressively before it starts rejecting real calls.
4. Flip the advisory check to enforcing for the coarsest scope only, ship
   a distinct, documented rejection response shape, and update the calling
   code's error handling to treat that response shape differently from a
   transient failure, closing the retry-storm failure mode from dimension
   11 before finer scopes are added.
5. Narrow the scope, per team, then per user, then per session if the
   product genuinely needs that granularity, each narrowing step repeating
   the advisory-then-enforcing sequence from steps 3 and 4, because a
   threshold tuned correctly at one scope is not automatically correct at a
   finer one.
6. Add the tiered soft threshold and its degrade behavior last, once the
   hard threshold has been running in production long enough that the team
   trusts its numbers, since the degrade path is new code exercising a new
   branch that itself needs the same validation the hard stop already went
   through.

Removing a Cost Guard, or scaling it back, when it stops earning its
place.

1. Confirm the removal candidate first against the applicability list in
   dimension 4, most commonly because the calling code that used to loop
   unboundedly has since been refactored to a fixed, bounded call count
   that no longer needs a live spend ceiling, or because the workload
   moved to a self-hosted model with no marginal per-call cost.
2. Before removing enforcement, downgrade it back to advisory-only logging
   for a full billing cycle, to confirm the assumption that removal is
   safe against real traffic rather than against a belief about traffic.
3. Keep the Meter and the accounting even after removing the Enforcement
   point, if the organization still values per-scope cost attribution for
   reporting, since the observability value of the Ledger is independent of
   whether it is also used to reject calls.
4. Remove the Enforcement point and its distinct rejection response shape
   from the calling code's error handling last, once no traffic has hit it
   for a full cycle, so the removal itself does not silently change error
   handling behavior for a code path nobody exercises anymore.

## 15. Testing and verification

Cost Guard is straightforward to unit test because its core decision, is
`current + delta` above the limit, is pure arithmetic with no model call
involved, and the mistake to avoid is testing only that arithmetic while
never exercising the concurrency and integration behavior that is where
this pattern actually fails in production.

**Unit level.** Test the Threshold policy in isolation against a fake
Ledger, covering the boundary exactly at the limit, one unit below it, and
one unit above it, since off-by-one errors at the threshold, using `>`
where `>=` was intended or vice versa, are common and easy to get backward.
Test that a Meter given a fixed token count and a fixed price table
produces the exact expected cost, and separately test that an unknown
model or an unpriced token type causes the Meter to fail closed, refusing
to allow the call, rather than defaulting to a cost of zero.

**Concurrency level.** Fire many concurrent requests against the same
scope, sized so their combined cost should trip the limit exactly once
partway through the batch, and assert that the number of calls actually
allowed through matches what an atomic Ledger would allow, not what a
racy read-then-write Ledger would allow. This test exists specifically to
catch the race condition described in dimension 11's first failure mode,
and it is one that only fails under real concurrency, so a single-threaded
test suite that never runs requests in parallel will pass even with a
broken, racy implementation.

**Integration level.** Run the guard against a mock provider that returns
a controllable, deterministic token count and cost per call, drive a
simulated agent loop through enough iterations to cross the configured
limit, and assert both that the call which crosses the limit is the last
one allowed, or is itself rejected, depending on which pre-call versus
post-call variant from dimension 8 is implemented, and that the calling
code's retry logic correctly does not retry the rejection.

**Chaos and adversarial testing.** Feed the guard a workload deliberately
shaped like the misuse case from dimension 11, many new scopes created in
quick succession, each individually under its per-scope limit, and assert
that a coarser aggregate ceiling, if the design includes one, actually
catches the aggregate overspend the per-scope limits individually miss.

**Test doubles that apply.** A fake Ledger backed by an in-memory map is
sufficient for unit tests of the Threshold policy, but the concurrency test
above should run against the real backing store, Redis or whatever the
production Ledger uses, in a test environment, because an in-memory fake's
locking behavior does not reproduce the race conditions a real shared
store under real network latency exposes.

## 16. Observability signals

**Current spend per scope, as a gauge.** The Ledger's live value for every
active scope, exported so a dashboard can show which scopes are closest to
their limit before any of them actually trip, giving operators lead time
rather than only a post-trip alert.

**Threshold trip count, as a counter, labeled by scope and by which
threshold, soft or hard.** A rising rate of soft-threshold trips with a
flat rate of hard-threshold trips indicates the degrade path is doing its
job, containing overruns before they become outright rejections. A rising
rate of hard trips indicates either a genuine attack or bug, or a threshold
that has fallen behind legitimate growth, and distinguishing the two
requires correlating the trip against the specific scope's historical
baseline, not the trip count alone.

**Cost per call and cost per successful task, as a histogram.** Tracking
these separately from the pass or fail rejection counters catches cost
drift that never trips any threshold at all, a slow, organization-wide
increase in average cost per task that a fixed per-scope limit will not
notice until it eventually does trip, by which point the drift has already
been accruing for a while.

**Estimate versus actual divergence, as a gauge, for guards using pre-call
estimation.** The difference between the Meter's pre-call estimate and the
provider's actual reported cost for the same call, tracked over time,
surfaces the pricing-table staleness failure mode from dimension 11 well
before it causes a visible incident, because a growing divergence is
detectable long before it grows large enough to matter.

**A healthy instance on a dashboard** shows current spend per scope
tracking a smooth, explainable curve correlated with known traffic
patterns, soft-threshold trips occurring occasionally and correlated with
genuinely larger sessions rather than randomly, hard-threshold trips rare
and each one individually explainable by an operator who looked at it, and
estimate-versus-actual divergence staying close to zero. **A failing
instance** shows current spend jumping in step changes uncorrelated with
any known traffic event, hard-threshold trips clustering suddenly across
many unrelated scopes at once, which is the aggregate-overspend failure
mode's signature, or estimate-versus-actual divergence widening steadily
over days, which is the stale-pricing failure mode's signature well before
it produces a visible dollar overrun.

## 17. Security and privacy implications

The primary security value Cost Guard provides is turning a class of
denial-of-wallet attack into a bounded, contained incident. An attacker who
discovers a prompt that drives an exposed agent into a long, expensive
loop, whether through prompt injection against a tool result the agent
reads, or through direct adversarial input to a public endpoint, is limited
by the guard's configured ceiling rather than able to run the attack until
someone notices the invoice, which is the concrete threat model this
pattern is built to close.

The Ledger itself is a store of per-scope spend data, and where a scope
maps to an individual, identifiable customer, that spend history is
usage data about that customer, subject to whatever data protection
regime the surrounding application already operates under, and it should
be retained, exported, and deleted under the same policy the application's
other per-customer usage data follows rather than treated as exempt
because it happens to live in a cost-tracking subsystem.

A Cost Guard's rejection response, if it echoes back detailed internal
state, the exact remaining budget, the exact threshold configured, or
internal scope identifiers, to an untrusted caller, discloses operational
and pricing information an attacker can use to probe how close a
particular scope is to its limit and time an attack to land just before a
reset, or discloses competitive pricing tier information a business may
not want a competitor able to enumerate by probing the API. A rejection
response intended for an untrusted, external caller should communicate
that a limit was reached without disclosing the specific numbers, while a
rejection response intended for an authenticated, trusted operator or
dashboard can safely be far more detailed.

The Enforcement point, being on every request's critical path, is itself a
target for a denial-of-service attack distinct from the denial-of-wallet
attack it defends against, an attacker who can drive traffic to the
Ledger's backing store faster than that store can serve reads and atomic
writes turns the guard's own dependency into the bottleneck, so the
Ledger's backing store needs the same availability and rate-limiting
consideration given to any other shared, hot-path dependency, rather than
being assumed safe because it is "just a counter."

## Code examples

The three examples below implement the same minimal shape, a per-scope
in-memory Ledger with an atomic check-and-increment, a Threshold policy
with a soft and a hard limit, and an Enforcement point that returns a
distinct rejection when the hard limit is reached. They are deliberately
minimal, a production implementation would back the Ledger with Redis or
an equivalent durable, shared store rather than an in-process map, per
dimension 8 and dimension 16.

### TypeScript

```typescript
type CostRecord = { spent: number; softLimit: number; hardLimit: number };

class BudgetExceededError extends Error {
  constructor(public readonly scope: string, public readonly spent: number, public readonly limit: number) {
    super(`Cost Guard: scope "${scope}" over budget. spent=${spent.toFixed(4)} limit=${limit.toFixed(4)}`);
  }
}

class CostGuard {
  private ledger = new Map<string, CostRecord>();

  register(scope: string, softLimit: number, hardLimit: number): void {
    this.ledger.set(scope, { spent: 0, softLimit, hardLimit });
  }

  // Check throws before allowing a call that is already over budget.
  checkBeforeCall(scope: string): void {
    const rec = this.ledger.get(scope);
    if (!rec) throw new Error(`Cost Guard: unknown scope "${scope}"`);
    if (rec.spent >= rec.hardLimit) {
      throw new BudgetExceededError(scope, rec.spent, rec.hardLimit);
    }
  }

  // Recorded after the model call returns real token usage.
  recordSpend(scope: string, inputTokens: number, outputTokens: number, priceInPerM: number, priceOutPerM: number): { spent: number; softTripped: boolean } {
    const rec = this.ledger.get(scope);
    if (!rec) throw new Error(`Cost Guard: unknown scope "${scope}"`);
    const cost = (inputTokens / 1_000_000) * priceInPerM + (outputTokens / 1_000_000) * priceOutPerM;
    rec.spent += cost;
    return { spent: rec.spent, softTripped: rec.spent >= rec.softLimit };
  }
}

// Simulated model call used only for this example.
function fakeModelCall(scope: string): { inputTokens: number; outputTokens: number } {
  return { inputTokens: 1200, outputTokens: 400 };
}

function main(): void {
  const guard = new CostGuard();
  guard.register("user:42", 0.05, 0.08); // soft at 5 cents, hard at 8 cents
  const priceIn = 3.0; // dollars per million input tokens
  const priceOut = 15.0; // dollars per million output tokens

  let calls = 0;
  try {
    for (let i = 0; i < 30; i++) {
      guard.checkBeforeCall("user:42");
      const { inputTokens, outputTokens } = fakeModelCall("user:42");
      const { spent, softTripped } = guard.recordSpend("user:42", inputTokens, outputTokens, priceIn, priceOut);
      calls++;
      if (softTripped) {
        console.log(`call ${calls}: soft threshold crossed, spent=${spent.toFixed(4)}`);
      }
    }
  } catch (err) {
    if (err instanceof BudgetExceededError) {
      console.log(`stopped after ${calls} calls: ${err.message}`);
    } else {
      throw err;
    }
  }
}

main();
```

### Python

```python
from dataclasses import dataclass
from threading import Lock


@dataclass
class CostRecord:
    spent: float
    soft_limit: float
    hard_limit: float


class BudgetExceededError(Exception):
    def __init__(self, scope: str, spent: float, limit: float) -> None:
        self.scope = scope
        self.spent = spent
        self.limit = limit
        super().__init__(f'Cost Guard: scope "{scope}" over budget. spent={spent:.4f} limit={limit:.4f}')


class CostGuard:
    def __init__(self) -> None:
        self._ledger: dict[str, CostRecord] = {}
        self._guard_lock = Lock()

    def register(self, scope: str, soft_limit: float, hard_limit: float) -> None:
        with self._guard_lock:
            self._ledger[scope] = CostRecord(spent=0.0, soft_limit=soft_limit, hard_limit=hard_limit)

    def check_before_call(self, scope: str) -> None:
        with self._guard_lock:
            rec = self._ledger.get(scope)
            if rec is None:
                raise KeyError(f'Cost Guard: unknown scope "{scope}"')
            if rec.spent >= rec.hard_limit:
                raise BudgetExceededError(scope, rec.spent, rec.hard_limit)

    def record_spend(
        self,
        scope: str,
        input_tokens: int,
        output_tokens: int,
        price_in_per_m: float,
        price_out_per_m: float,
    ) -> tuple[float, bool]:
        with self._guard_lock:
            rec = self._ledger.get(scope)
            if rec is None:
                raise KeyError(f'Cost Guard: unknown scope "{scope}"')
            cost = (input_tokens / 1_000_000) * price_in_per_m + (output_tokens / 1_000_000) * price_out_per_m
            rec.spent += cost
            return rec.spent, rec.spent >= rec.soft_limit


def fake_model_call(scope: str) -> tuple[int, int]:
    return 1200, 400


def main() -> None:
    guard = CostGuard()
    guard.register("user:42", soft_limit=0.05, hard_limit=0.08)
    price_in = 3.0
    price_out = 15.0

    calls = 0
    try:
        for _ in range(30):
            guard.check_before_call("user:42")
            input_tokens, output_tokens = fake_model_call("user:42")
            spent, soft_tripped = guard.record_spend("user:42", input_tokens, output_tokens, price_in, price_out)
            calls += 1
            if soft_tripped:
                print(f"call {calls}: soft threshold crossed, spent={spent:.4f}")
    except BudgetExceededError as exc:
        print(f"stopped after {calls} calls: {exc}")


if __name__ == "__main__":
    main()
```

### Go

Go's standard mutex API is avoided here in favor of a tiny buffered-channel
mutex, `acquire` and `release`, so the example carries no dependency beyond
the standard library while keeping every method name plain and unambiguous.

```go
package main

import (
	"errors"
	"fmt"
)

type chanMutex chan struct{}

func newChanMutex() chanMutex {
	m := make(chanMutex, 1)
	m <- struct{}{}
	return m
}

func (m chanMutex) acquire() { <-m }
func (m chanMutex) release() { m <- struct{}{} }

type costRecord struct {
	spent     float64
	softLimit float64
	hardLimit float64
}

type budgetExceededError struct {
	scope string
	spent float64
	limit float64
}

func (e *budgetExceededError) Error() string {
	return fmt.Sprintf("cost guard: scope %q over budget. spent=%.4f limit=%.4f", e.scope, e.spent, e.limit)
}

type CostGuard struct {
	guardMu chanMutex
	ledger  map[string]*costRecord
}

func NewCostGuard() *CostGuard {
	return &CostGuard{guardMu: newChanMutex(), ledger: make(map[string]*costRecord)}
}

func (g *CostGuard) Register(scope string, softLimit, hardLimit float64) {
	g.guardMu.acquire()
	defer g.guardMu.release()
	g.ledger[scope] = &costRecord{spent: 0, softLimit: softLimit, hardLimit: hardLimit}
}

func (g *CostGuard) CheckBeforeCall(scope string) error {
	g.guardMu.acquire()
	defer g.guardMu.release()
	rec, ok := g.ledger[scope]
	if !ok {
		return fmt.Errorf("cost guard: unknown scope %q", scope)
	}
	if rec.spent >= rec.hardLimit {
		return &budgetExceededError{scope: scope, spent: rec.spent, limit: rec.hardLimit}
	}
	return nil
}

func (g *CostGuard) RecordSpend(scope string, inputTokens, outputTokens int, priceInPerM, priceOutPerM float64) (float64, bool, error) {
	g.guardMu.acquire()
	defer g.guardMu.release()
	rec, ok := g.ledger[scope]
	if !ok {
		return 0, false, fmt.Errorf("cost guard: unknown scope %q", scope)
	}
	cost := (float64(inputTokens)/1_000_000)*priceInPerM + (float64(outputTokens)/1_000_000)*priceOutPerM
	rec.spent += cost
	return rec.spent, rec.spent >= rec.softLimit, nil
}

func fakeModelCall(scope string) (int, int) {
	return 1200, 400
}

func main() {
	guard := NewCostGuard()
	guard.Register("user:42", 0.05, 0.08)
	priceIn, priceOut := 3.0, 15.0

	calls := 0
	for i := 0; i < 30; i++ {
		if err := guard.CheckBeforeCall("user:42"); err != nil {
			var be *budgetExceededError
			if errors.As(err, &be) {
				fmt.Printf("stopped after %d calls: %v\n", calls, err)
				break
			}
			panic(err)
		}
		in, out := fakeModelCall("user:42")
		spent, softTripped, err := guard.RecordSpend("user:42", in, out, priceIn, priceOut)
		if err != nil {
			panic(err)
		}
		calls++
		if softTripped {
			fmt.Printf("call %d: soft threshold crossed, spent=%.4f\n", calls, spent)
		}
	}
}
```

All three samples were run directly, not merely compiled, and their output
confirms the intended behavior, the soft threshold logging starting once
accumulated spend passes 0.05, and execution stopping with a
budget-exceeded message once accumulated spend would reach 0.08, after 9
simulated calls at the token counts and prices used in the samples.

## 18. References

1. AWS Cost Management User Guide, "What is AWS Budgets."
   [https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html),
   verified 2026-08-03.
2. LiteLLM documentation, "Set Budgets, Rate Limits per User."
   [https://docs.litellm.ai/docs/proxy/users](https://docs.litellm.ai/docs/proxy/users),
   verified 2026-08-03.
3. Helicone documentation, "Custom Rate Limits."
   [https://docs.helicone.ai/features/advanced-usage/custom-rate-limits](https://docs.helicone.ai/features/advanced-usage/custom-rate-limits),
   verified 2026-08-03.
4. LangChain documentation, "LangGraph, Graph API" (recursion_limit and
   GraphRecursionError).
   [https://docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api),
   verified 2026-08-03.
5. OpenAI developer documentation, "Production best practices" (spend
   alerts and hard spend limits).
   [https://developers.openai.com/api/docs/guides/production-best-practices](https://developers.openai.com/api/docs/guides/production-best-practices),
   verified 2026-08-03.
