---
name: Chaos Engineering
slug: chaos-engineering
family: 21-sre-operations
category: Behavioral
aliases: [Fault Injection Testing, Resilience Testing, Simian Army]
first_described: 'Netflix, Chaos Monkey and the Principles of Chaos Engineering manifesto, 2011 to 2015'
maturity: canonical
related: [game-day, error-budget]
incompatible_with: []
verified: 2026-08-22
---

# Chaos Engineering

## 1. Name, aliases, and lineage

Chaos Engineering. Also called Fault Injection Testing, Resilience Testing, or Simian Army, after Netflix's own name for its family of fault injecting tools. The canonical manifesto states the discipline directly. Chaos Engineering is the discipline of experimenting on a system in order to build confidence in the system's capability to withstand turbulent conditions in production (https://principlesofchaos.org/).

The lineage runs from a single tool to a discipline. Netflix built Chaos Monkey, described in its own engineering blog as a tool that randomly disables our production instances to make sure we can survive this common type of failure (https://netflixtechblog.com/the-netflix-simian-army-16e57fbab116). That single tool grew into a wider Simian Army of fault injecting services, and the underlying idea, deliberately breaking a live system on purpose to prove resilience rather than assume it, was later generalized and named as its own discipline by the Principles of Chaos Engineering manifesto.

## 2. Problem and context

A distributed system's resilience is, by default, an assumption. Engineers design for fault tolerance, but the actual behavior of a live system under a real, partial failure is rarely tested until a real failure happens. Netflix's own framing of the problem states this directly. just designing a fault tolerant architecture is not enough. We have to constantly test our ability to actually survive these once in a blue moon failures (https://netflixtechblog.com/the-netflix-simian-army-16e57fbab116).

The problem this pattern solves is the gap between a designed resilience and a proven one. a system that was designed to survive an instance failure, a region outage, or a dependency timeout has not actually demonstrated that survival until something exercises the failure for real. Chaos Engineering closes that gap by deliberately and continuously exercising real failure conditions against a live system, so a weakness is found by a controlled experiment rather than by an uncontrolled real incident.

## 3. Forces

- Injecting a real fault into a live production system risks a real user impact if the blast radius is not carefully bounded.
- A resilience assumption is only proven false, or proven true, by actually testing it against a real failure, but that testing has to happen somewhere with real consequences.
- Confidence in a system's resilience needs to be renewed continually, since the system, its dependencies, and its traffic pattern all keep changing after any single experiment.
- An experiment that always finds a known result stops being useful, so the practice needs to keep expanding into new, untested failure conditions to keep finding real weaknesses.
- The organization running the experiments needs the authority and the appetite to deliberately break its own live systems, which is a genuine cultural and trust hurdle, not just a technical one.

## 4. Applicability and non-applicability

Use Chaos Engineering for a distributed, redundant system where surviving a partial failure is a real design goal, and the organization wants ongoing, empirical confidence that the goal is actually being met, not just assumed. It fits especially well once a team has already exercised its readiness through scheduled Game Days and wants to move toward continuous, automated verification of the same resilience assumptions.

Skip it for a system with no real redundancy or fault tolerance design to test in the first place, since injecting a fault into a system with no designed resilience just produces an outage with no useful finding. It is also not the right starting point for a team that has not yet built the monitoring and abort mechanisms needed to safely bound an experiment's blast radius.

## 5. Structure

- Steady state hypothesis. a measurable definition of the system's normal, healthy behavior, the baseline an experiment is measured against.
- Fault injector. the tool or service that introduces the real failure condition (an instance termination, a network delay, a dependency timeout) into the live system.
- Blast radius scope. the explicit boundary limiting which part of the system and which portion of traffic an experiment is allowed to affect.
- Abort mechanism. an automated or manual trigger that halts the experiment immediately if the steady state hypothesis is violated beyond the scoped boundary.
- Experiment record. the documented result of each run, feeding confidence back into the team's understanding of the system's real resilience.

## 6. ASCII structure diagram

```
  Steady state hypothesis
  (define normal, healthy behavior)
        |
        v
  Fault injector introduces a real failure, bounded by Blast radius scope
        |
        v
  steady state holds?  ----- yes -----> confidence increases, record result
        |
        no
        |
        v
  Abort mechanism halts the experiment
        |
        v
  Experiment record captures the weakness found
```

## 7. Dynamics

1. The team defines a steady state hypothesis, a measurable definition of the system's normal behavior that the experiment will check against.
2. The fault injector introduces a real, deliberate failure into the live system, bounded by an explicit blast radius scope so the experiment cannot exceed its intended reach.
3. If the steady state hypothesis continues to hold despite the injected failure, confidence in the system's resilience genuinely increases, and the result is recorded.
4. The manifesto frames this outcome directly. Chaos verifies that the system does work, rather than trying to validate how it works (https://principlesofchaos.org/), meaning the experiment tests real observed behavior, not a theoretical design.
5. If the steady state hypothesis is violated, the abort mechanism halts the experiment immediately, containing the blast radius before it grows beyond the scoped boundary.
6. The experiment record captures the weakness that was found, and the manifesto describes the underlying purpose of the whole practice as the facilitation of experiments to uncover systemic weaknesses (https://principlesofchaos.org/), turning that finding into concrete follow-up work.

## 8. Implementation variants

- Instance termination. randomly terminating individual production instances, the original Chaos Monkey shape, testing whether the system tolerates losing a single node.
- Region or zone level failure. simulating the loss of an entire availability zone or region, testing a much larger blast radius of designed redundancy.
- Network fault injection. introducing latency, packet loss, or a dependency timeout rather than terminating an instance outright, testing a different class of partial failure.
- Continuous, automated experimentation. running fault injection on an ongoing schedule against production, rather than as a one-off exercise, matching the manifesto's framing of building continual, renewed confidence rather than a single proof.

## 9. Known production uses

- Netflix originated the practice with Chaos Monkey and its wider Simian Army of fault injecting tools, documented in Netflix's own engineering blog (https://netflixtechblog.com/the-netflix-simian-army-16e57fbab116).
- The Principles of Chaos Engineering manifesto, maintained by the engineers who generalized Netflix's practice into a named discipline, documents the canonical definition and the experiment-driven method (https://principlesofchaos.org/), used as the reference definition across the industry.
- Organizations across the industry that operate large distributed systems have since adopted the discipline, commonly building or adopting their own fault injection tooling to continuously exercise their own resilience assumptions the same way Netflix pioneered.

## 10. Consequences

### Benefits

- A weakness in the system's designed resilience is found by a controlled experiment, with an explicit abort mechanism, rather than by an uncontrolled real incident with real user impact.
- Confidence in the system's resilience becomes an ongoing, measured property rather than a one-time design assumption that quietly goes stale as the system changes.
- The practice directly tests observed system behavior rather than a theoretical design, closing the gap between what a system was designed to survive and what it actually survives.

### Costs

- Building the fault injector, the blast radius controls, and the abort mechanism safely takes real engineering investment before any experiment can run.
- An experiment that is poorly scoped risks becoming a genuine unintended outage, the exact opposite of what a controlled experiment was meant to be.
- Sustaining the practice requires ongoing organizational appetite for deliberately breaking live production systems, which is a real cultural cost, not only a technical one.

## 11. Failure modes and misuse

- Running an experiment with no defined steady state hypothesis, so there is no clear signal for whether the system actually held up or not.
- No abort mechanism, or an abort mechanism that is too slow, so a failing experiment grows past its intended blast radius before anyone can stop it.
- Injecting a fault into a system with no genuine designed resilience to test, producing an outage rather than a useful finding.
- Running an experiment once and treating the result as permanent, when the system, its dependencies, and its traffic keep changing after that single run.
- Treating the practice as purely a testing exercise rather than acting on what each experiment finds, so real weaknesses are discovered repeatedly but never fixed.

## 12. Trade-off matrix

| Dimension | Instance termination | Continuous automated experimentation |
|---|---|---|
| Scope of blast radius | Narrow, one instance | Broader, ongoing across the system |
| Engineering investment required | Lower | Higher, needs mature tooling first |
| Confidence gained | Point-in-time | Continually renewed |
| Risk if poorly scoped | Lower | Higher, runs unattended and repeatedly |
| Good starting point for a new team | Yes | Better attempted after manual experiments |

## 13. Related and incompatible patterns

### Related

- Game Day. both patterns deliberately introduce failure to test resilience, but a Game Day is a scheduled, team-driven exercise, while this pattern is continuous and often automated.
- Error Budget. the incidents an experiment discovers, or deliberately causes while proving a weakness, consume error budget the same way a real incident would, so the two practices are naturally measured against the same ceiling.

### Incompatible with

- None directly, though running experiments with no abort mechanism and no bounded blast radius works against the pattern's own safe experimental design, even though it is still labeled as the same practice.

## 14. Refactoring path in and out

### Introducing it

1. Start from a Game Day exercise or a manual, single-instance experiment, defining a clear steady state hypothesis and a tightly bounded blast radius before touching any real system.
2. Build the fault injector and the abort mechanism together, so no experiment can run without a way to stop it safely.
3. Run the experiment against a small, low-risk blast radius first, and review the experiment record before expanding scope.
4. Gradually widen the blast radius and the frequency of experiments as confidence in the tooling and the abort mechanism grows.
5. Move toward continuous, scheduled experimentation once the team trusts the safety controls enough to run experiments without a person watching each one directly.

### Removing it

1. Confirm the system being exercised is being retired, or the team has a different, equally rigorous way of maintaining resilience confidence.
2. Retire the scheduled experiments and their fault injector configuration, keeping the historical experiment record as a record of what was learned.
3. Confirm the abort mechanism and any experiment-specific monitoring are also decommissioned, so nothing keeps watching for a fault condition that no longer gets deliberately triggered.

## 15. Testing and verification

- Verify the abort mechanism itself before running any real experiment, confirming it genuinely halts fault injection when the steady state hypothesis is violated.
- Verify the blast radius scope holds in practice, by reviewing what the fault injector actually touched during a run against what it was configured to be allowed to touch.
- Review the experiment record after every run, confirming a real finding is turned into a concrete, tracked follow-up item.
- Periodically re-run a past experiment after its finding was addressed, confirming the fix genuinely closed the weakness the experiment found.

## 16. Observability signals

- Track how often the steady state hypothesis holds versus is violated across experiments, as the primary measure of the system's real, ongoing resilience.
- Track how often the abort mechanism actually triggers, and how quickly, since a rising rate of aborts signals the system may be getting more fragile, not less.
- Track the experiment cadence itself, confirming continuous experimentation is actually happening on schedule rather than being quietly deferred.

## 17. Security and privacy implications

- A fault injector that can terminate instances or disrupt network traffic in production needs to be scoped with the same access control rigor as any other high-privilege operational tool, since it can cause real damage if misused or compromised.
- An experiment that touches a system carrying real user data should never expose that data to unintended observers as a side effect of the injected failure, even when the failure itself is deliberate.
- The experiment record, especially when it captures a genuine security or access-control weakness, should be handled with the same care as any other sensitive incident record.

## 18. References

- Principles of Chaos Engineering manifesto (https://principlesofchaos.org/)
- Netflix Technology Blog, The Netflix Simian Army (https://netflixtechblog.com/the-netflix-simian-army-16e57fbab116)

## Code examples

### Python

```python
from dataclasses import dataclass, field


@dataclass
class SteadyStateHypothesis:
    metric_name: str
    expected_min: float


@dataclass
class ChaosExperiment:
    name: str
    hypothesis: SteadyStateHypothesis
    blast_radius_percent: float
    aborted: bool = False
    findings: list = field(default_factory=list)

    def observe(self, measured_value):
        if measured_value < self.hypothesis.expected_min:
            self.aborted = True
            self.findings.append(
                "steady state violated at " + str(measured_value)
            )
        return not self.aborted


experiment = ChaosExperiment(
    name="terminate one worker instance",
    hypothesis=SteadyStateHypothesis("success_rate", 0.99),
    blast_radius_percent=1.0,
)
print('holds', experiment.observe(0.995))
print('holds', experiment.observe(0.80))
print('findings', experiment.findings)
```

### Kotlin

```kotlin
data class SteadyStateHypothesis(
    val metricName: String,
    val expectedMin: Double,
)

class ChaosExperiment(
    val name: String,
    val hypothesis: SteadyStateHypothesis,
    val blastRadiusPercent: Double,
) {
    var aborted = false
        private set
    val findings = mutableListOf<String>()

    fun observe(measuredValue: Double): Boolean {
        if (measuredValue < hypothesis.expectedMin) {
            aborted = true
            findings.add("steady state violated at " + measuredValue)
        }
        return !aborted
    }
}

fun main() {
    val experiment = ChaosExperiment(
        name = "terminate one worker instance",
        hypothesis = SteadyStateHypothesis("success_rate", 0.99),
        blastRadiusPercent = 1.0,
    )
    println("holds " + experiment.observe(0.995))
    println("holds " + experiment.observe(0.80))
    println("findings " + experiment.findings)
}
```

### Swift

```swift
struct SteadyStateHypothesis {
    let metricName: String
    let expectedMin: Double
}

final class ChaosExperiment {
    let name: String
    let hypothesis: SteadyStateHypothesis
    let blastRadiusPercent: Double
    private(set) var aborted = false
    private(set) var findings: [String] = []

    init(name: String, hypothesis: SteadyStateHypothesis, blastRadiusPercent: Double) {
        self.name = name
        self.hypothesis = hypothesis
        self.blastRadiusPercent = blastRadiusPercent
    }

    func observe(_ measuredValue: Double) -> Bool {
        if measuredValue < hypothesis.expectedMin {
            aborted = true
            findings.append("steady state violated at " + String(measuredValue))
        }
        return !aborted
    }
}

let experiment = ChaosExperiment(
    name: "terminate one worker instance",
    hypothesis: SteadyStateHypothesis(metricName: "success_rate", expectedMin: 0.99),
    blastRadiusPercent: 1.0
)
print("holds " + String(experiment.observe(0.995)))
print("holds " + String(experiment.observe(0.80)))
print("findings " + String(experiment.findings.count))
```
