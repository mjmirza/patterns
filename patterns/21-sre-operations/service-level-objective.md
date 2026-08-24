---
name: Service Level Objective
slug: service-level-objective
family: 21-sre-operations
category: Behavioral
aliases: [SLO, Reliability Target]
first_described: 'Google, Site Reliability Engineering, 2016'
maturity: canonical
related: [error-budget, graceful-degradation]
incompatible_with: []
verified: 2026-08-22
---

# Service Level Objective

## 1. Name, aliases, and lineage

Service Level Objective, almost always abbreviated SLO. Also called a Reliability Target. Google's Site Reliability Engineering book, the source that formalized the term for the software industry, defines the three related concepts precisely, and the distinctions matter. An SLI is a service level indicator, a carefully defined quantitative measure of some aspect of the level of service that is provided. An SLO is a service level objective, a target value or range of values for a service level that is measured by an SLI. Finally, SLAs are service level agreements, an explicit or implicit contract with your users that includes consequences of meeting (or missing) the SLOs they contain (https://sre.google/sre-book/service-level-objectives/).

The lineage traces to Google's internal Site Reliability Engineering practice, which formed in the early 2000s and was documented publicly in the 2016 SRE book. The pattern spread industry-wide as other organizations adopted SRE practices, and cloud providers built dedicated tooling to define and monitor SLOs directly against production telemetry.

## 2. Problem and context

A service either works or it does not, but complex distributed systems rarely fail as a binary. they degrade in latency, drop a fraction of requests, or become unavailable in one region while healthy elsewhere. Without an agreed, numeric definition of good enough, engineering teams either over-invest in reliability well past the point where a person can perceive the difference, or under-invest and let real degradation go unnoticed until it becomes an outage.

Google's own guide on distinguishing an SLO from an SLA states the practical test plainly. An easy way to tell the difference between an SLO and an SLA is to ask what happens if the SLOs are not met. if there is no explicit consequence, then you are almost certainly looking at an SLO (https://sre.google/sre-book/service-level-objectives/). The SLO exists to give engineering, product, and operations a single, agreed number that settles the too-reliable versus too-fragile argument before it becomes a late-night incident debate.

## 3. Forces

- Reliability work competes directly with feature work for the same engineering time, and without a numeric target, that trade-off is argued case by case instead of decided once.
- A target that is too strict (approaching 100 percent) is both technically expensive and, per Google's own workbook framing, the wrong target because it leaves no room for the risk that shipping any change at all carries.
- A target that is too loose lets real user-facing degradation go unaddressed until it compounds into a genuine outage.
- The SLI an SLO measures must be something a person actually experiences (request success, latency, freshness), not an internal implementation detail that happens to be easy to measure.
- Multiple services in a dependency chain each need their own SLO, and a downstream service's SLO can never be tighter than what its upstream dependencies are actually able to provide.

## 4. Applicability and non-applicability

Use a Service Level Objective for any production service with real users or downstream consumers, where reliability is a genuine engineering priority that competes against feature velocity for the same time and attention. It is essential wherever an Error Budget is used to govern release pace, since the budget is derived directly from the SLO's allowed failure rate.

Skip a formal SLO for a prototype, an internal tool with no real consumer relying on it, or a system in such early development that its normal operating behavior is not yet understood well enough to set a target that means anything. A number chosen before the system's real behavior is known is worse than no number, since it anchors expectations to noise.

## 5. Structure

- Service Level Indicator (SLI). the underlying quantitative measurement (percentage of successful requests, 99th-percentile latency, freshness of a data pipeline) the SLO is defined against.
- Target value or range. the numeric threshold the SLI must meet over a defined measurement window (99.9 percent of requests succeed over a rolling 30 days), which is the SLO itself.
- Measurement window. the time period over which the SLI is aggregated and compared to the target, chosen to be long enough to smooth noise and short enough to act on meaningfully.
- Error Budget. the inverse of the SLO's allowed failure rate, treated as a spendable resource that governs how much risk (releases, experiments, planned maintenance) the team can take before the SLO itself is at risk.
- Alerting policy. the rules that fire when the SLI is burning the Error Budget fast enough that the SLO will be missed if the trend continues, distinct from a simple threshold alert on the raw SLI.

## 6. ASCII structure diagram

```
  raw telemetry (requests, latencies, errors)
        |
        v
  +------------------------+
  |   SLI computation       |   e.g. successful_requests / total_requests
  +------------------------+
        |
        v
  +------------------------+     compare against     +------------------+
  |   SLI value over window  | ----------------------> |  SLO target      |
  +------------------------+                          +------------------+
        |                                                     |
        v                                                     v
  +------------------------+                          +------------------+
  |    Error Budget          | <----- derived from ---- |  gap to target   |
  |    remaining             |                          +------------------+
  +------------------------+
        |
        v
  release pace, alerting, and prioritization decisions
```

## 7. Dynamics

1. The team selects an SLI that reflects what a real user actually experiences, such as the fraction of requests that succeed within an acceptable latency.
2. The team sets an SLO, a target value or range for that SLI over a defined measurement window, agreed with the people and teams who depend on the service's reliability.
3. Production telemetry continuously computes the real SLI value and compares it against the SLO target for the current window.
4. Once you have an SLO, you can use the SLO to derive an error budget (https://sre.google/workbook/implementing-slos/), which is spent whenever the SLI falls short of perfect over the window.
5. As the Error Budget is consumed by real incidents, planned risk (a release, an experiment, scheduled maintenance) is weighed against how much budget remains, rather than being judged in isolation.
6. If the SLI's trend threatens to burn the remaining Error Budget before the window resets, an alert fires and the team shifts priority toward reliability work until the trend recovers.
7. At the end of each measurement window, the team reviews whether the SLO was met, and whether the target itself, the SLI it measures, or the measurement window need to be revised for the next period.

## 8. Implementation variants

- Rolling-window SLO. the SLI is measured over a continuously rolling period (the last 30 days), giving a smoothly updating view of standing at any moment rather than a hard reset boundary.
- Calendar-window SLO. the SLI resets at a fixed calendar boundary (each quarter), which is simpler to reason about and report on but can create an artificial cliff right after a reset.
- Multi-SLI composite SLO. a single SLO derived from more than one SLI (availability AND latency both within target), used when a service's reliability genuinely depends on more than one dimension at once.
- Cloud-provider managed SLO monitoring. defining the SLI and SLO declaratively against a managed observability platform, which computes the burn rate and Error Budget automatically rather than the team building that computation by hand.

## 9. Known production uses

- Google's own Site Reliability Engineering practice originated the formalized SLI, SLO, and SLA distinction, documented in its freely available SRE book (https://sre.google/sre-book/service-level-objectives/), and every Google-scale production service defines and monitors SLOs as a core part of its operational discipline.
- Google's SRE Workbook devotes a full chapter to practical SLO implementation, stating directly that 100 percent reliability is the wrong target (https://sre.google/workbook/implementing-slos/), reflecting the lesson that an achievable, deliberately imperfect target is what actually governs engineering decisions well.
- Major cloud providers ship dedicated SLO monitoring products (declarative SLI and SLO definitions tied to burn-rate alerting) specifically because the pattern is now standard practice across the industry, not a Google-only convention.

## 10. Consequences

### Benefits

- Reliability and feature-velocity decisions get a single, agreed number to argue from, instead of being relitigated case by case.
- An Error Budget derived from the SLO gives an objective, shared signal for when to slow down releases and when it is genuinely safe to move fast.
- Setting the target deliberately below 100 percent forces an honest acknowledgment that all systems fail sometimes, which improves incident response culture by removing the pretense of perfection.
- A well-chosen SLI focuses monitoring and alerting on what a real user actually experiences, rather than on internal metrics that may not correlate with real impact.

### Costs

- Choosing a good SLI and a realistic SLO target requires real understanding of the system's actual behavior, which a team without prior operational history may not yet have.
- The measurement infrastructure (computing the SLI accurately, tracking burn rate, alerting on trend) is real engineering work that a small team may not have the capacity to build well.
- An SLO that is set once and never revisited can drift out of sync with what users actually need as the service and its usage evolve.

## 11. Failure modes and misuse

- Vanity metric SLI. choosing an SLI that is easy to measure but does not correlate with what a real user experiences, producing a green SLO dashboard while people are genuinely unhappy with the service.
- 100-percent target. setting the SLO at or effectively at perfect reliability, which Google's own guidance names directly as the wrong target, since it leaves no error budget for any release risk at all.
- SLO with no consequence and no owner. a target nobody actually acts on when missed, which is indistinguishable in practice from having no SLO.
- Ignoring the SLA distinction. treating an internal SLO as if it were an externally binding SLA, creating contractual exposure the team never actually agreed to.
- Never revisiting the target. an SLO set once at launch and left unchanged for years, even as the service, its users, and its dependencies have all changed substantially.

## 12. Trade-off matrix

| Dimension | Strict SLO (near 100 percent) | Deliberately relaxed SLO |
|---|---|---|
| Error budget available for risk | Very small, blocks release velocity | Larger, supports faster iteration |
| Engineering cost to sustain | High, chasing diminishing returns | Lower, effort matched to real user need |
| Sensitivity to real degradation | High, catches small regressions | Lower, tolerates more noise before alerting |
| Suitability for a critical path | Often appropriate | Often too loose |
| Suitability for a non-critical feature | Usually wasteful | Usually the right fit |

## 13. Related and incompatible patterns

### Related

- Error Budget. derived directly from the SLO's allowed failure rate, and is the mechanism that turns the SLO into a concrete, spendable governance tool for release decisions.
- Graceful Degradation. a service that degrades gracefully under stress protects its SLO by failing in a way that still counts as acceptable to the SLI, rather than failing completely.

### Incompatible with

- None directly, though treating an SLO as a binding external SLA with contractual consequences conflates two genuinely different concepts and should be avoided.

## 14. Refactoring path in and out

### Introducing it

1. Observe the service's real production behavior for long enough to understand its natural reliability baseline before choosing any target.
2. Select an SLI that reflects what a real user actually experiences, rather than whatever internal metric happens to already exist.
3. Propose an initial SLO target with the people and teams who depend on the service, deliberately below 100 percent, and agree on the measurement window.
4. Build or configure the monitoring that computes the SLI continuously and compares it against the SLO target in real time.
5. Derive an Error Budget from the agreed SLO and use it to govern real release and risk decisions, revisiting the target after enough operating history accumulates to judge whether it was set correctly.

### Removing it

1. Confirm the service genuinely no longer needs a formal reliability target, which is uncommon for anything still in production with real users.
2. Retire the associated Error Budget governance and alerting first, since they depend directly on the SLO.
3. Remove the SLO definition and its dedicated monitoring once nothing depends on it for a decision.

## 15. Testing and verification

- Verify the SLI computation itself against known historical incidents, confirming it would have correctly reflected the degradation a real past outage caused.
- Test the burn-rate alerting logic with synthetic data, asserting it fires before the Error Budget is fully exhausted, with enough lead time to act.
- Review the SLO target periodically against real operating history, asserting the target is still achievable without heroics and still tight enough to catch genuine user-facing degradation.
- Confirm the measurement window's boundary behavior (a reset at a calendar edge, or a rolling window's edge case) does not silently mask a genuine breach.

## 16. Observability signals

- Track the current SLI value against the SLO target continuously, and the remaining Error Budget for the active window, as the primary reliability dashboard for the service.
- Track the burn rate (how fast the Error Budget is being consumed relative to the time remaining in the window), which is a leading indicator distinct from the raw SLI value.
- Track how often the SLO target itself is revised over time, since a target that is adjusted very frequently may signal it was never set on solid operating data in the first place.

## 17. Security and privacy implications

- An SLI derived from raw request logs must be computed without exposing or retaining more of the underlying request data than the aggregate measurement genuinely requires.
- A publicly shared SLO or reliability dashboard can reveal operational detail (traffic patterns, dependency structure) useful to an adversary, so what is exposed externally should be deliberately scoped, separate from the full internal detail used for engineering decisions.
- An Error Budget governance process that pressures a team to ship faster as budget remains healthy must not be allowed to silently erode security review or testing steps that are unrelated to the SLI the SLO measures.

## 18. References

- Google, Site Reliability Engineering, Service Level Objectives chapter (https://sre.google/sre-book/service-level-objectives/)
- Google, SRE Workbook, Implementing SLOs chapter (https://sre.google/workbook/implementing-slos/)

## Code examples

### Python

```python
from dataclasses import dataclass


@dataclass
class SLOStatus:
    sli_value: float
    target: float
    error_budget_remaining: float


def evaluate_slo(successful_requests, total_requests, target=0.999):
    sli_value = successful_requests / total_requests if total_requests else 1.0
    allowed_failure_rate = 1.0 - target
    actual_failure_rate = 1.0 - sli_value
    remaining = max(0.0, 1.0 - (actual_failure_rate / allowed_failure_rate))
    return SLOStatus(sli_value=sli_value, target=target, error_budget_remaining=remaining)


status = evaluate_slo(successful_requests=9987, total_requests=10000)
print('SLI', status.sli_value)
print('error budget remaining', status.error_budget_remaining)
```

### Kotlin

```kotlin
data class SloStatus(val sliValue: Double, val target: Double, val errorBudgetRemaining: Double)

fun evaluateSlo(successfulRequests: Long, totalRequests: Long, target: Double = 0.999): SloStatus {
    val sliValue = if (totalRequests > 0) successfulRequests.toDouble() / totalRequests else 1.0
    val allowedFailureRate = 1.0 - target
    val actualFailureRate = 1.0 - sliValue
    val remaining = (1.0 - (actualFailureRate / allowedFailureRate)).coerceAtLeast(0.0)
    return SloStatus(sliValue, target, remaining)
}

fun main() {
    val status = evaluateSlo(successfulRequests = 9987, totalRequests = 10000)
    println("SLI " + status.sliValue)
    println("error budget remaining " + status.errorBudgetRemaining)
}
```

### Swift

```swift
struct SloStatus {
    let sliValue: Double
    let target: Double
    let errorBudgetRemaining: Double
}

func evaluateSlo(successfulRequests: Int, totalRequests: Int, target: Double = 0.999) -> SloStatus {
    let sliValue = totalRequests > 0 ? Double(successfulRequests) / Double(totalRequests) : 1.0
    let allowedFailureRate = 1.0 - target
    let actualFailureRate = 1.0 - sliValue
    let remaining = max(0.0, 1.0 - (actualFailureRate / allowedFailureRate))
    return SloStatus(sliValue: sliValue, target: target, errorBudgetRemaining: remaining)
}

let status = evaluateSlo(successfulRequests: 9987, totalRequests: 10000)
print("SLI " + String(status.sliValue))
print("error budget remaining " + String(status.errorBudgetRemaining))
```
