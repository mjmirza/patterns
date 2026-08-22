---
name: Runbook Automation
slug: runbook-automation
family: 21-sre-operations
category: Behavioral
aliases: [Playbook Automation, Automated Runbook, Executable Runbook]
first_described: 'Google, Site Reliability Engineering, Effective Troubleshooting chapter, 2016'
maturity: canonical
related: [toil-automation, service-level-objective]
incompatible_with: []
verified: 2026-08-22
---

# Runbook Automation

## 1. Name, aliases, and lineage

Runbook Automation. Also called Playbook Automation, Automated Runbook, or Executable Runbook. A runbook is a documented, step by step procedure for diagnosing or resolving a known operational condition, and this pattern is the practice of converting that documented human procedure into an executable one. Google's Site Reliability Engineering book describes the runbook entry as something an on-call engineer is directed to during an incident. The alerting system has filed a bug, with links to the black-box prober's recent results and to the playbook entry for this alert, and assigned it to you (https://sre.google/sre-book/effective-troubleshooting/).

The lineage runs directly from the runbook itself. before this pattern, a runbook was a document a person read and then acted on by hand, and the natural evolution, once a runbook's steps are well understood and stable, is to let a machine execute those same steps instead of a person reading and typing them under incident pressure.

## 2. Problem and context

During an incident, a person following a runbook by hand introduces two real costs. the time it takes a person to read, interpret, and execute each step, and the risk that a stressed or unfamiliar on-call engineer makes a mistake performing a step that a machine would perform identically every time. Google's SRE Workbook documents a real incident response where the on-call SRE validated that all automated recovery actions had been executed, and completed the mitigation steps in relevant runbooks (https://sre.google/workbook/incident-response/), showing that even a mature response still leans on a mix of automated recovery and manual runbook steps.

The problem this pattern solves is that a runbook's value is capped by how fast and how reliably a person can execute it under pressure. converting the well understood, stable steps of a runbook into executable automation removes both the human execution time and the human error risk from exactly the moments when a fast, correct response matters most.

## 3. Forces

- A runbook's steps need to be well understood and stable before automating them, or the automation encodes a procedure that is still changing underneath it.
- Some runbook steps genuinely require human judgment (deciding whether to escalate, deciding whether an unusual signal is a real incident), and automating those steps away removes a decision point that still needs a person.
- Automating a runbook step changes who is accountable for the action, from the person who read the runbook and executed it, to whoever wrote and maintains the automation.
- A runbook automated too early, before its steps have proven stable across several real incidents, risks encoding a wrong or outdated procedure and executing it faster than a person would have caught the mistake.
- Incident pressure is exactly when a team is least able to pause and carefully review whether an automated step is behaving correctly.

## 4. Applicability and non-applicability

Use Runbook Automation for a runbook whose steps are well understood, have been executed successfully by hand across multiple real incidents, and follow a deterministic procedure with no judgment call in the middle. It is especially valuable for a high frequency, well bounded condition (restarting a specific stuck service, clearing a known queue backlog) where the speed and consistency of automation meaningfully shortens the time to resolution.

Skip it for a runbook that still requires genuine diagnostic judgment (deciding what is actually wrong before choosing a remediation), or for a runbook whose steps have not yet stabilized, since automating an immature procedure risks encoding and repeating a wrong action faster than a person would.

## 5. Structure

- Runbook document. the human readable, step by step procedure for diagnosing or resolving a known condition, the source of truth the automation is built from.
- Trigger condition. the specific alert or signal that indicates this runbook's procedure applies.
- Automated step set. the subset of the runbook's steps that have been converted into executable automation, distinct from any step still requiring a person.
- Escalation path. the defined point at which the automation hands control back to a person, either because a step still requires judgment or because the automated steps did not resolve the condition.
- Execution log. a record of what the automation actually did during a given run, so the action taken is traceable after the fact the same way a person's manual execution would have been.

## 6. ASCII structure diagram

```
  Trigger condition detected
        |
        v
  +-------------------+
  |   Runbook document   |
  |   (source of truth)  |
  +-------------------+
        |
        v
  Automated step set executes, writing to Execution log
        |
        v
  resolved?  ----- yes -----> incident closed
        |
        no
        |
        v
  Escalation path hands control to a person
```

## 7. Dynamics

1. A trigger condition (an alert, a monitored signal) fires and identifies which runbook's procedure applies to the current incident.
2. The automated step set executes the portion of the runbook that has already been converted to executable automation, writing each action taken to the execution log.
3. If the automated steps resolve the condition, the incident is closed with a full record of what was executed and when.
4. If the automated steps do not resolve the condition, or the runbook reaches a step still requiring human judgment, the escalation path hands control to a person, who continues from exactly where the automation stopped.
5. The person handling an escalated incident reviews the execution log as their starting context, the same way Google's own incident record shows a mix of automated recovery actions already executed before the on-call SRE completed the remaining manual mitigation steps (https://sre.google/workbook/incident-response/).
6. After the incident, any step that repeatedly required manual intervention becomes a candidate for the next round of automation, growing the automated step set over time.

## 8. Implementation variants

- Fully automated remediation. the entire runbook executes without a person, appropriate only for a condition whose diagnosis and resolution are both fully deterministic.
- Human-triggered automation. a person confirms the diagnosis matches the runbook's trigger condition, then runs the automated step set with a single action rather than executing each step by hand.
- Partial automation with escalation. the automated step set handles the deterministic early steps, then hands off to a person for any step still requiring judgment, the most common shape for a runbook that is not yet fully mature.
- Dry-run mode. the automation executes every step except the final action and reports what it would have done, used to validate a newly automated runbook against real trigger conditions before trusting it to act unattended.

## 9. Known production uses

- Google's own SRE practice documents the runbook entry as a standard part of the on-call workflow, linked directly from the alert itself, in the Effective Troubleshooting chapter of the freely available SRE book (https://sre.google/sre-book/effective-troubleshooting/).
- The SRE Workbook's Incident Response chapter documents a real incident where automated recovery actions and manual runbook steps were both used together as part of the same response (https://sre.google/workbook/incident-response/), showing the pattern as it is actually practiced rather than as a purely theoretical ideal.
- Organizations across the industry that adopt SRE practice commonly start by automating the steps of their highest frequency, best understood runbooks first, treating automation coverage of runbook steps as a tracked operational metric alongside toil.

## 10. Consequences

### Benefits

- Automated steps execute faster and more consistently than a person reading and typing the same steps under incident pressure, directly shortening time to resolution for the conditions covered.
- The execution log gives every escalated incident a documented, traceable starting point, rather than an on-call engineer having to reconstruct what has already been tried.
- Automation coverage of a team's runbooks becomes a measurable, trackable investment, the same way toil reduction is, rather than an unmeasured aspiration.

### Costs

- Building and validating the automation for a runbook takes real engineering time, and that cost is only worth paying once the underlying steps have proven stable.
- The automation itself needs ongoing maintenance as the systems it acts on change, or it silently starts executing a stale procedure.
- A poorly scoped automated step set can act faster than a person would have caught a mistake, so the validation and dry-run investment before trusting a runbook to run unattended is a real, ongoing cost.

## 11. Failure modes and misuse

- Automating a runbook before its steps have stabilized, encoding a procedure that is still actively changing and executing the wrong action faster than a person would have.
- No escalation path, so an automated step set that cannot resolve the condition leaves the incident stuck with nobody notified.
- An execution log that is incomplete or hard to find, so the person who is escalated to has to reconstruct what the automation already tried instead of reading it directly.
- Treating full automation as the only acceptable end state, when a partial automation with a deliberate escalation point is often the correct and safer shape for a runbook that still has a genuine judgment step in it.
- Letting the automated step set drift out of sync with the runbook document, so the human readable procedure and what the machine actually does silently disagree.

## 12. Trade-off matrix

| Dimension | Fully automated remediation | Partial automation with escalation |
|---|---|---|
| Speed to resolution | Fastest, no human step | Faster than manual, slower than full automation |
| Risk of a wrong action executing unattended | Highest | Lower, a person reviews before the judgment step |
| Fit for a still-maturing runbook | Poor | Better, the person catches what automation cannot yet |
| Engineering investment required | Highest | Moderate |
| Auditability of the final decision | Machine only | Machine plus a documented human decision |

## 13. Related and incompatible patterns

### Related

- Toil Automation. runbook automation is a specific, incident-response focused case of the broader practice of eliminating manual, repetitive operational work.
- Service Level Objective. the time an incident spends unresolved consumes error budget, so faster automated remediation directly helps a service stay within its SLO.

### Incompatible with

- None directly, though a fully automated runbook that removes every human decision point from a condition that still genuinely needs judgment works against the pattern's own safe applicability, even though it is still labeled as runbook automation.

## 14. Refactoring path in and out

### Introducing it

1. Confirm the target runbook's steps have been executed successfully by hand across multiple real incidents, and that the procedure has not changed recently.
2. Identify which specific steps are fully deterministic and which still require human judgment, and scope the automated step set to only the deterministic ones.
3. Build the automation with an explicit dry-run mode first, and validate it against real trigger conditions before trusting it to act unattended.
4. Define the escalation path explicitly, so any step still requiring judgment, or any failure of the automated steps to resolve the condition, hands off to a person cleanly.
5. Enable the automation for live incidents, and review its execution log after each run to confirm it behaves as intended before expanding the automated step set further.

### Removing it

1. Confirm the underlying condition the runbook addresses no longer occurs, or the system it acts on has been retired.
2. Retire the automation and its maintenance ownership, keeping the runbook document itself if the condition could still recur and need a manual response.
3. Remove the trigger wiring so the retired automation can no longer fire on a stale condition.

## 15. Testing and verification

- Test the automated step set in dry-run mode against a range of real past trigger conditions, confirming it would have taken the correct action every time before trusting it to act unattended.
- Test the escalation path explicitly, confirming a step that still requires judgment, or a failure of the automated steps, genuinely reaches a person rather than silently stalling.
- Review the execution log after every real run, confirming the recorded actions match what the runbook document actually specifies.
- Periodically re-validate an automated runbook against the systems it acts on, confirming the automation has not silently drifted out of sync as those systems changed.

## 16. Observability signals

- Track how often the automated step set resolves an incident without escalation versus how often it hands off to a person, as a primary measure of the automation's real coverage.
- Track the time from trigger condition to resolution separately for fully automated runs versus escalated ones, confirming the automation is genuinely faster than the manual path it replaced.
- Track how often an escalated incident's automated steps had already been executed correctly, confirming the execution log is genuinely useful context rather than being ignored by the person who is escalated to.

## 17. Security and privacy implications

- An automated step set that performs a previously human-reviewed action removes the judgment check a person would have applied, so any automated step that touches access control, credentials, or a destructive operation needs its own explicit safety checks, not just a copy of the manual runbook's steps.
- The automation commonly needs broader system access than any single on-call engineer would have had to perform the runbook manually, since it runs unattended, and that access should be scoped as narrowly as the automated step set actually requires.
- The execution log should record what the automation did and why, with the same care as the incident record a manual response would have left, so an automated action remains fully traceable after the fact.

## Code examples

### Python

```python
from dataclasses import dataclass
from enum import Enum


class StepResult(Enum):
    RESOLVED = 'resolved'
    NEEDS_ESCALATION = 'needs_escalation'


@dataclass
class RunbookStep:
    name: str
    requires_judgment: bool
    action: object


class RunbookRunner:
    def __init__(self, steps, log=None):
        self.steps = steps
        self.log = log if log is not None else []

    def run(self, context):
        for step in self.steps:
            if step.requires_judgment:
                self.log.append((step.name, "escalated"))
                return StepResult.NEEDS_ESCALATION
            outcome = step.action(context)
            self.log.append((step.name, outcome))
            if outcome == StepResult.RESOLVED:
                return StepResult.RESOLVED
        return StepResult.NEEDS_ESCALATION


def restart_worker(context):
    return StepResult.RESOLVED


runner = RunbookRunner(
    [RunbookStep("restart stuck worker", False, restart_worker)]
)
print('result', runner.run({}))
print('log', runner.log)
```

### Kotlin

```kotlin
enum class StepResult { RESOLVED, NEEDS_ESCALATION }

data class RunbookStep(
    val name: String,
    val requiresJudgment: Boolean,
    val action: (Map<String, Any>) -> StepResult,
)

class RunbookRunner(private val steps: List<RunbookStep>) {
    val log = mutableListOf<Pair<String, String>>()

    fun run(context: Map<String, Any>): StepResult {
        for (step in steps) {
            if (step.requiresJudgment) {
                log.add(step.name to "escalated")
                return StepResult.NEEDS_ESCALATION
            }
            val outcome = step.action(context)
            log.add(step.name to outcome.name)
            if (outcome == StepResult.RESOLVED) return StepResult.RESOLVED
        }
        return StepResult.NEEDS_ESCALATION
    }
}

fun restartWorker(context: Map<String, Any>): StepResult = StepResult.RESOLVED

fun main() {
    val runner = RunbookRunner(
        listOf(RunbookStep("restart stuck worker", false, ::restartWorker))
    )
    println("result " + runner.run(emptyMap()))
    println("log " + runner.log)
}
```

### Swift

```swift
enum StepResult: Equatable {
    case resolved
    case needsEscalation
}

struct RunbookStep {
    let name: String
    let requiresJudgment: Bool
    let action: ([String: Any]) -> StepResult
}

final class RunbookRunner {
    private let steps: [RunbookStep]
    private(set) var log: [(String, String)] = []

    init(steps: [RunbookStep]) {
        self.steps = steps
    }

    func run(context: [String: Any]) -> StepResult {
        for step in steps {
            if step.requiresJudgment {
                log.append((step.name, "escalated"))
                return .needsEscalation
            }
            let outcome = step.action(context)
            let outcomeLabel = outcome == .resolved ? "resolved" : "needsEscalation"
            log.append((step.name, outcomeLabel))
            if case .resolved = outcome { return .resolved }
        }
        return .needsEscalation
    }
}

func restartWorker(context: [String: Any]) -> StepResult { .resolved }

let runner = RunbookRunner(steps: [
    RunbookStep(name: "restart stuck worker", requiresJudgment: false, action: restartWorker)
])
let finalResult = runner.run(context: [:])
let finalLabel = finalResult == .resolved ? "resolved" : "needsEscalation"
print("result " + finalLabel)
print("log entries " + String(runner.log.count))
```

## 18. References

- Google, Site Reliability Engineering, Effective Troubleshooting chapter (https://sre.google/sre-book/effective-troubleshooting/)
- Google, SRE Workbook, Incident Response chapter (https://sre.google/workbook/incident-response/)
