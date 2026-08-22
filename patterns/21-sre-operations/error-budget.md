---
name: Error Budget
slug: error-budget
family: 21-sre-operations
category: Behavioral
aliases: [Unreliability Budget, Reliability Budget]
first_described: 'Google, Site Reliability Engineering, Embracing Risk chapter, 2016'
maturity: canonical
related: [service-level-objective, graceful-degradation]
incompatible_with: []
verified: 2026-08-22
---

# Error Budget

## 1. Name, aliases, and lineage

Error Budget. Also called an Unreliability Budget or a Reliability Budget. The name is deliberately literal. it is a budget, spent against a fixed allowance, in exactly the way a financial budget is spent against a fixed sum. Google's Site Reliability Engineering book, in its Embracing Risk chapter, introduces the concept directly. The difference between these two numbers is the budget of how much unreliability is remaining for the quarter (https://sre.google/sre-book/embracing-risk/), describing the gap between a service's actual measured reliability and its stated Service Level Objective target.

The lineage runs directly from the SLO. an Error Budget only exists because an SLO has already been agreed, and the budget is arithmetically its complement. an SLO of 99.9 percent implies an Error Budget of 0.1 percent over the same measurement window. The pattern formalized Google's internal practice of treating an agreed amount of failure as expected and planned for, rather than as an unplanned deviation to be minimized at any cost.

## 2. Problem and context

Engineering teams building on top of a service and the team operating that service structurally want different things. one wants to ship features and changes as fast as possible, the other wants the service to stay reliable. Left to informal negotiation, that tension gets resolved by whichever side argues loudest in a given week, which produces inconsistent decisions and recurring conflict.

The Error Budget resolves this by turning an abstract argument into a concrete, shared number both sides already agreed to. Google's own framing states the operating rule plainly. As long as the uptime measured is above the SLO, in other words, as long as there is error budget remaining, new releases can be pushed (https://sre.google/sre-book/embracing-risk/). The problem the pattern solves is not eliminating the tension between velocity and reliability, it is making the trade-off objective, so neither side has to win the argument case by case.

## 3. Forces

- Release velocity and reliability compete for the same underlying resource, the service's tolerance for something going wrong.
- A team with budget remaining should be free to move fast and take real risk, since the SLO has explicit room for it.
- A team that has exhausted its budget needs an enforceable, agreed consequence, or the budget is a number nobody actually acts on.
- The budget resets on a defined window (commonly rolling or a fixed calendar period), and how that reset interacts with a long-running incident needs to be handled deliberately.
- Not every kind of change carries the same risk, so a rigid all-or-nothing policy (halt everything, or allow everything) can be too blunt for real operational needs.

## 4. Applicability and non-applicability

Use an Error Budget wherever a Service Level Objective is already in place and the team needs an objective, agreed mechanism for deciding how much release risk is currently acceptable. It is the natural governance layer on top of an SLO, and is especially valuable when engineering and product teams have historically disagreed about how much reliability work versus feature work the team should be doing.

Skip it for a service with no SLO yet, since an Error Budget has nothing to be derived from without one. It is also not the right mechanism for a team that already has effective, lightweight release governance and genuinely does not experience the velocity-versus-reliability conflict the pattern exists to resolve.

## 5. Structure

- Source SLO. the Service Level Objective the Error Budget is arithmetically derived from, an allowed failure rate over a defined measurement window.
- Budget balance. the remaining allowance of unreliability for the current window, computed continuously from real SLI measurements against the SLO.
- Consumption events. real incidents, degraded periods, or outages that consume budget as they occur, each attributable to a measurable amount of the allowed unreliability.
- Error Budget Policy. the agreed, written rule for what happens as the budget approaches or reaches zero (a release freeze, a mandatory shift to reliability work, an escalation).
- Reset boundary. the point at which the budget replenishes for the next measurement window, whether that boundary is a rolling window or a fixed calendar period.

## 6. ASCII structure diagram

```
  SLO target (e.g. 99.9% over 30 days)
        |
        v
  +-------------------------+
  |   Error Budget = 100% - SLO   |
  +-------------------------+
        |
        v
  +-------------------------+     real incidents consume     +----------------+
  |   Budget balance          | <----------------------------  |  Consumption   |
  |   (updated continuously)  |                                |  events        |
  +-------------------------+                                +----------------+
        |
        v
  budget healthy?  ----- yes -----> ship at normal or faster pace
        |
        no
        |
        v
  Error Budget Policy triggers: freeze releases, shift to reliability work
```

## 7. Dynamics

1. A team agrees an SLO for the service, and the Error Budget is derived arithmetically as the SLO's allowed failure rate over the same measurement window.
2. Real production telemetry continuously measures the service's actual reliability, and the Budget balance updates in real time as the gap between the SLO target and actual performance narrows or widens.
3. Every incident, degraded period, or outage consumes a measurable amount of the remaining budget, proportional to how far and how long the SLI fell short of the SLO.
4. While budget remains healthy, teams building on the service ship releases and take on risk at their normal pace, per Google's own operating rule that new releases can be pushed as long as budget remains.
5. As the budget approaches exhaustion, the Error Budget Policy activates. the SRE Workbook's own example policy states that if the service has exceeded its error budget for the preceding four-week window, all changes and releases other than urgent fixes are halted until the service is back within its SLO (https://sre.google/workbook/error-budget-policy/).
6. Once the service recovers and the budget replenishes past the policy's threshold, normal release pace resumes automatically, with no separate negotiation required.

## 8. Implementation variants

- Hard freeze policy. releases stop entirely once the budget is exhausted, resuming only once the service is back within its SLO, the strictest and simplest variant to enforce.
- Graduated policy. release risk tolerance scales down gradually as the budget depletes, rather than a single hard cutoff, allowing lower-risk changes to continue while higher-risk ones pause first.
- Exception carve-outs. a written policy that explicitly permits certain categories of change (a critical security fix, a rollback) to proceed even during a freeze, since blocking those categories would make the service less reliable, not more.
- Team-scoped budgets. a large service's error budget is split across contributing teams or subsystems, so one team's risk-taking does not silently consume the whole service's shared allowance.

## 9. Known production uses

- Google's own SRE practice introduced the Error Budget as the mechanism that operationalizes an SLO into a concrete release-governance tool, documented in the Embracing Risk chapter of the freely available SRE book (https://sre.google/sre-book/embracing-risk/).
- The SRE Workbook publishes a worked example Error Budget Policy stating that error budgets are the tool SRE uses to balance service reliability with the pace of innovation (https://sre.google/workbook/error-budget-policy/), used as a direct template by many organizations adopting the pattern.
- Organizations across the industry that have adopted Google-style SRE practice commonly implement an Error Budget Policy as the enforceable consequence attached to every service's SLO, rather than leaving reliability versus velocity as an unresolved, recurring argument.

## 10. Consequences

### Benefits

- The velocity-versus-reliability trade-off becomes an objective, shared number rather than a recurring argument decided by whoever is loudest.
- A healthy budget gives teams explicit permission to take real risk and ship fast, which removes unnecessary caution when the service is genuinely performing well.
- An exhausted budget gives an equally explicit, agreed signal to shift priority toward reliability work, without anyone needing to make that call subjectively in the moment.
- The policy that governs the budget can be written down once and applied consistently, rather than negotiated fresh after every incident.

### Costs

- The policy needs a genuinely enforced consequence, or the budget is a number that exists on a dashboard and changes nothing in practice.
- A rigid, unwritten exception process can turn a legitimate emergency fix into a fight over whether the freeze applies, exactly the kind of ambiguity the pattern was meant to remove.
- Splitting a budget across multiple contributing teams adds real accounting complexity that a single-team service does not need.

## 11. Failure modes and misuse

- Unenforced policy. an Error Budget that is tracked and reported but whose policy is never actually applied when exhausted, making the whole mechanism theater rather than governance.
- Budget gaming. incidents deliberately mis-categorized or under-reported to avoid consuming budget, which corrupts the very signal the pattern depends on.
- No exception path. a policy with no carve-out for a genuine emergency fix or rollback, which can make an already-bad incident worse by blocking the fix that would resolve it.
- Budget attributed to the wrong cause. an outage caused by a dependency or the platform itself charged against a team's own budget, producing a freeze that has nothing to do with that team's actual releases.
- Reset-boundary gaming. deliberately timing risky releases just after a reset to maximize available budget before the next measurement window begins, which defeats the pattern's intent of steady, ongoing risk discipline.

## 12. Trade-off matrix

| Dimension | Hard freeze policy | Graduated policy |
|---|---|---|
| Simplicity to enforce | High, one clear rule | Lower, requires risk-tiering changes |
| Disruption when budget is low | High, all releases stop | Lower, only higher-risk changes pause |
| Clarity of the signal | Very clear, binary | Requires more judgment to apply |
| Fit for a small team | Often appropriate | Often more overhead than needed |
| Fit for a large, multi-team service | Can be too blunt | Better matches varied real risk levels |

## 13. Related and incompatible patterns

### Related

- Service Level Objective. the Error Budget is arithmetically derived from the SLO and has no meaning without one already in place.
- Graceful Degradation. a service that degrades gracefully under stress consumes its Error Budget more slowly than one that fails completely under the same real-world conditions.

### Incompatible with

- None directly, though an Error Budget Policy with no genuinely enforced consequence is functionally incompatible with the pattern's purpose, even though it may still be labeled as one.

## 14. Refactoring path in and out

### Introducing it

1. Confirm the service already has an agreed Service Level Objective, since the Error Budget has nothing to derive from without one.
2. Compute the Error Budget arithmetically as the SLO's allowed failure rate over the same measurement window, and build or configure the monitoring that tracks the remaining balance continuously.
3. Draft an Error Budget Policy in writing with the teams affected, including the exact consequence when the budget is exhausted and any genuine exception carve-outs.
4. Pilot the policy for one full measurement window before treating it as final, so the team can observe whether the threshold and consequence are actually workable in practice.
5. Enforce the policy consistently once it is agreed, and revisit it periodically as the service and its usage evolve.

### Removing it

1. Confirm the underlying SLO itself is being removed or the velocity-versus-reliability tension the budget resolves has genuinely stopped being a real problem for the team.
2. Retire the Error Budget Policy and its enforcement mechanism first.
3. Remove the budget-tracking monitoring once no policy or decision depends on it.

## 15. Testing and verification

- Verify the budget calculation itself against known historical incidents, confirming the consumed amount matches what a manual calculation of the same incident's impact on the SLI would produce.
- Test the policy's trigger condition with synthetic data, asserting the freeze (or graduated response) activates at exactly the agreed threshold, not earlier or later.
- Test the reset boundary explicitly, asserting a long-running incident spanning a reset is accounted for correctly rather than silently disappearing from the budget.
- Review real applications of the policy periodically, confirming the written consequence was genuinely followed the last time the budget was exhausted, not quietly waived.

## 16. Observability signals

- Track the current budget balance and its burn rate as a primary, continuously visible dashboard, distinct from the raw SLI value alone.
- Track how often the policy's threshold is actually crossed and how often the written consequence was genuinely enforced versus waived, since a policy that is frequently waived has effectively stopped functioning.
- Track which incident categories consume the most budget over time, which directs reliability investment toward the failure modes that actually matter most to the SLO.

## 17. Security and privacy implications

- A public or widely shared Error Budget dashboard can reveal how close a service is to a release freeze, which is operationally useful internally but should not be exposed externally where it could signal an attacker the service is under strain.
- An Error Budget Policy under pressure to keep releasing must never be allowed to waive security review or testing as a way to preserve release pace, since that trades a visible reliability metric for an invisible security risk.
- Incident data feeding the budget calculation should be handled with the same care as any other operational log, avoiding retention of more detail about the underlying cause or affected users than the aggregate budget computation genuinely needs.

## Code examples

### Python

```python
from dataclasses import dataclass


@dataclass
class ErrorBudget:
    slo_target: float
    allowed_failure_rate: float
    consumed_failure_rate: float

    @property
    def remaining_fraction(self):
        if self.allowed_failure_rate == 0:
            return 0.0
        used = self.consumed_failure_rate / self.allowed_failure_rate
        return max(0.0, 1.0 - used)


def build_error_budget(slo_target, actual_sli):
    allowed_failure_rate = 1.0 - slo_target
    consumed_failure_rate = max(0.0, 1.0 - actual_sli)
    return ErrorBudget(slo_target, allowed_failure_rate, consumed_failure_rate)


def is_release_allowed(budget, policy_threshold=0.0):
    return budget.remaining_fraction > policy_threshold


budget = build_error_budget(slo_target=0.999, actual_sli=0.9985)
print('remaining budget', budget.remaining_fraction)
print('release allowed', is_release_allowed(budget))
```

### Kotlin

```kotlin
data class ErrorBudget(
    val sloTarget: Double,
    val allowedFailureRate: Double,
    val consumedFailureRate: Double,
) {
    val remainingFraction: Double
        get() {
            if (allowedFailureRate == 0.0) return 0.0
            val used = consumedFailureRate / allowedFailureRate
            return (1.0 - used).coerceAtLeast(0.0)
        }
}

fun buildErrorBudget(sloTarget: Double, actualSli: Double): ErrorBudget {
    val allowedFailureRate = 1.0 - sloTarget
    val consumedFailureRate = (1.0 - actualSli).coerceAtLeast(0.0)
    return ErrorBudget(sloTarget, allowedFailureRate, consumedFailureRate)
}

fun isReleaseAllowed(budget: ErrorBudget, policyThreshold: Double = 0.0): Boolean {
    return budget.remainingFraction > policyThreshold
}

fun main() {
    val budget = buildErrorBudget(sloTarget = 0.999, actualSli = 0.9985)
    println("remaining budget " + budget.remainingFraction)
    println("release allowed " + isReleaseAllowed(budget))
}
```

### Swift

```swift
struct ErrorBudget {
    let sloTarget: Double
    let allowedFailureRate: Double
    let consumedFailureRate: Double

    var remainingFraction: Double {
        guard allowedFailureRate != 0 else { return 0.0 }
        let used = consumedFailureRate / allowedFailureRate
        return max(0.0, 1.0 - used)
    }
}

func buildErrorBudget(sloTarget: Double, actualSli: Double) -> ErrorBudget {
    let allowedFailureRate = 1.0 - sloTarget
    let consumedFailureRate = max(0.0, 1.0 - actualSli)
    return ErrorBudget(sloTarget: sloTarget, allowedFailureRate: allowedFailureRate, consumedFailureRate: consumedFailureRate)
}

func isReleaseAllowed(budget: ErrorBudget, policyThreshold: Double = 0.0) -> Bool {
    return budget.remainingFraction > policyThreshold
}

let budget = buildErrorBudget(sloTarget: 0.999, actualSli: 0.9985)
print("remaining budget " + String(budget.remainingFraction))
print("release allowed " + String(isReleaseAllowed(budget: budget)))
```

## 18. References

- Google, Site Reliability Engineering, Embracing Risk chapter (https://sre.google/sre-book/embracing-risk/)
- Google, SRE Workbook, Error Budget Policy chapter (https://sre.google/workbook/error-budget-policy/)
