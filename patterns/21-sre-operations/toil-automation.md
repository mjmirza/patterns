---
name: Toil Automation
slug: toil-automation
family: 21-sre-operations
category: Behavioral
aliases: [Operational Automation, Toil Elimination, Toil Reduction]
first_described: 'Google, Site Reliability Engineering, Eliminating Toil chapter, 2016'
maturity: canonical
related: [error-budget, runbook-automation]
incompatible_with: []
verified: 2026-08-22
---

# Toil Automation

## 1. Name, aliases, and lineage

Toil Automation. Also called Operational Automation, Toil Elimination, or Toil Reduction. The name centers on the specific word Google's Site Reliability Engineering practice gave to a category of work, and the practice of removing that category through automation. The SRE book's Eliminating Toil chapter defines the category directly. Toil is the kind of work tied to running a production service that tends to be manual, repetitive, automatable, tactical, devoid of enduring value, and that scales linearly as a service grows (https://sre.google/sre-book/eliminating-toil/).

The lineage runs from Google's own operational history. before the pattern was named, operations teams across the industry already recognized the feeling of repetitive manual work, but had no shared vocabulary or discipline for measuring it, capping it, or eliminating it systematically. Naming it as toil and giving engineering teams an explicit mandate to automate it away turned an informal complaint into a measurable, actionable practice.

## 2. Problem and context

As a service grows, the amount of manual operational work required to keep it running (provisioning, restarts, routine configuration changes, responding to the same class of alert) tends to grow along with it. Left unchecked, that manual work consumes an ever larger share of an engineering team's time, leaving less and less capacity for the engineering work that actually improves the service.

Google's own definition names the exact test for whether a task belongs in this category. If a machine could accomplish the task just as well as a human, or the need for the task could be designed away, that task is toil (https://sre.google/sre-book/eliminating-toil/). The problem this pattern solves is that manual operational work, left unmeasured and unchallenged, silently crowds out real engineering, and a team needs a systematic way to notice it, measure it, and remove it before it does.

## 3. Forces

- Manual operational work is often individually small, so no single instance feels worth automating, even though the cumulative cost across a team and a quarter is large.
- The team best positioned to notice a repetitive task is also the team under the most immediate pressure to just do the task and move on, rather than pausing to automate it.
- Full automation is not always achievable or worth the investment for every manual task, so a team needs a way to decide which toil is worth automating now versus tolerating for a while.
- Automation itself has an ongoing maintenance cost, so eliminating one kind of manual work can introduce a new kind of operational burden if the automation is not maintained.
- Measuring toil requires the team to actually track how time is spent, which many teams have no existing habit of doing.

## 4. Applicability and non-applicability

Use Toil Automation wherever an operational team performs a task repeatedly, the task follows a defined and reproducible procedure, and a machine executing that same procedure would produce an equally good or better result than a person doing it by hand. It applies especially well as a service's user base and infrastructure footprint grow, since that growth is exactly what makes manual, linearly scaling work unsustainable.

Skip it for genuinely novel work that requires human judgment, design, or creativity, since automating a task that has no repeatable procedure produces a fragile, hard to maintain script rather than a real gain. It is also not the right investment for a task performed so rarely that the cost of building and maintaining the automation would exceed the total cost of doing it by hand.

## 5. Structure

- Task inventory. an explicit, tracked list of the operational tasks a team performs, distinguishing genuine toil from engineering work.
- Toil budget. an agreed ceiling on how much of the team's time may be spent on toil, commonly expressed as a percentage of total capacity.
- Automation target. the specific manual task selected for elimination, chosen for its frequency, cost, and how well it fits a repeatable procedure.
- Automation implementation. the script, tool, or system that performs the task without a person, replacing the manual procedure end to end.
- Maintenance owner. the team or person responsible for keeping the automation working as the underlying system evolves.

## 6. ASCII structure diagram

```
  +-------------------+
  |   Task inventory    |
  |   (tracked manual    |
  |    operational work) |
  +-------------------+
        |
        v
  measure against Toil budget
        |
        v
  over budget?  ----- no ------> tolerate, revisit later
        |
        yes
        |
        v
  select highest-value Automation target
        |
        v
  build Automation implementation
        |
        v
  Maintenance owner keeps it working as the system evolves
```

## 7. Dynamics

1. The team maintains an inventory of the manual operational tasks it performs, tracking how often each recurs and roughly how much time each consumes.
2. Time spent on toil is measured against an agreed toil budget, commonly expressed as a percentage cap on total operational time, following Google's own practice of treating toil as a bounded resource rather than an unavoidable cost.
3. When toil exceeds the budget, or a single recurring task is clearly consuming a disproportionate share of time, the team selects it as an automation target.
4. The SRE Workbook frames the resulting strategic choice directly. the optimal strategy for handling toil is to eliminate it at the source (https://sre.google/workbook/eliminating-toil/), meaning the task is designed away entirely wherever possible, not merely scripted.
5. Where elimination at the source is not possible, the team builds an automation implementation that performs the same procedure without requiring a person, and assigns a maintenance owner responsible for keeping it working.
6. Reducing toil is an acknowledgment that an engineer's effort is better utilized in areas where human judgment and expression are possible (https://sre.google/workbook/eliminating-toil/), so the time reclaimed from the automated task is redirected toward engineering work that has lasting value.

## 8. Implementation variants

- Script-based automation. a standalone script that performs the previously manual procedure on demand or on a schedule, the lowest investment variant, appropriate for a task that is well understood but not yet worth full platform integration.
- Self-service tooling. a tool or internal platform feature that lets the requester perform the task themselves without operations involvement at all, removing the operations team from the loop rather than merely speeding up their part of it.
- Auto-remediation. a system that detects the condition that would have triggered the manual task and resolves it automatically, without a person initiating anything, the highest investment variant and the one that most closely matches eliminating the task at the source.
- Design-away elimination. removing the underlying need for the task entirely, through a system or process redesign, rather than automating the existing procedure, matching the Workbook's own preferred strategy.

## 9. Known production uses

- Google's own SRE practice tracks toil as a first-class operational metric across its production services, documented in the Eliminating Toil chapter of the freely available SRE book (https://sre.google/sre-book/eliminating-toil/).
- The SRE Workbook publishes a dedicated chapter on eliminating toil in practice, covering the strategic preference for designing tasks away over merely scripting them (https://sre.google/workbook/eliminating-toil/), used across organizations that have adopted Google-style SRE practice as the practitioner-facing companion to the book's definition.
- Organizations across the industry that adopt SRE practice commonly cap toil as a percentage of on-call and operational time, using that cap to justify automation investment that would otherwise be hard to prioritize against feature work.

## 10. Consequences

### Benefits

- Engineering time previously spent on repetitive manual work is freed for work that has lasting value, which the pattern's own framing states directly as the reason to reduce toil at all.
- A task automated once continues to be performed correctly every time it recurs, removing the variability of a person performing the same procedure slightly differently under time pressure.
- Naming and measuring toil gives a team an objective basis for prioritizing automation work against other competing priorities, rather than automation being a vague aspiration nobody ever schedules.

### Costs

- Building the automation itself takes real engineering time upfront, which is a genuine cost even when the payoff is clear.
- An automated task still needs a maintenance owner, or the automation quietly breaks as the underlying system changes and reintroduces the manual work it was meant to remove.
- Measuring toil accurately requires a team to track how its time is spent, which itself takes discipline and can feel like overhead before the automation payoff is realized.

## 11. Failure modes and misuse

- Automating a task that was not genuinely repeatable, producing a brittle script that breaks on the first edge case it was not written to handle.
- Building automation with no maintenance owner, so it silently rots and the team eventually reverts to the manual process without noticing the automation had stopped working.
- Treating the toil budget as a target to hit rather than a ceiling, so the team spends effort chasing a specific percentage instead of actually reducing the underlying manual work.
- Automating a task instead of asking whether the task needs to exist at all, missing the Workbook's own preferred strategy of eliminating the task at the source.
- Counting genuine engineering work as toil, or vice versa, which corrupts the measurement the whole practice depends on.

## 12. Trade-off matrix

| Dimension | Script-based automation | Auto-remediation |
|---|---|---|
| Investment required | Low | High |
| Coverage of edge cases | Limited to what was scripted | Can be broader if well designed |
| Maintenance burden | Moderate | Higher, since it runs unattended |
| Risk if it fails silently | Lower, a person still initiates it | Higher, nobody may notice it stopped |
| Fit for infrequent tasks | Often appropriate | Usually not worth the investment |

## 13. Related and incompatible patterns

### Related

- Error Budget. both patterns come from the same SRE practice of measuring an operational quantity against an agreed ceiling and acting when it is exceeded.
- Runbook Automation. a runbook documents the manual procedure a person follows, and automating that same procedure is often the direct next step once the runbook exists and is well understood.

### Incompatible with

- None directly, though automating a task with no genuinely repeatable procedure produces brittle tooling that works against the pattern's own intent, even though it is still labeled as automation.

## 14. Refactoring path in and out

### Introducing it

1. Build a task inventory by tracking, for a defined period, every manual operational task the team performs and roughly how much time each one takes.
2. Classify each tracked task against the toil definition, distinguishing genuine toil from engineering work that happens to be recurring.
3. Agree a toil budget as a percentage ceiling on operational time, and review actual toil against it on a regular cadence.
4. Select the highest-value automation target, considering both frequency and cost, rather than automating whichever task is most visible in the moment.
5. Build the automation, assign a maintenance owner, and track whether the task actually stops recurring manually once the automation ships.

### Removing it

1. Confirm the automated task is genuinely obsolete (the underlying system or process has changed enough that the task no longer needs to happen at all) before retiring the automation.
2. Retire the automation and its maintenance ownership together, so nobody continues to carry responsibility for something no longer in use.
3. Remove the task from the tracked inventory once it is confirmed to no longer recur.

## 15. Testing and verification

- Test the automation against the same set of cases the manual procedure was known to handle, confirming it produces an equivalent or better result every time.
- Test the automation's failure behavior explicitly, confirming it fails loudly (an alert, a visible error) rather than silently, since a silent failure reintroduces the manual burden it was meant to remove without anyone noticing.
- Periodically re-measure actual toil against the tracked inventory, confirming the automated task has genuinely stopped consuming manual time rather than merely being reported as automated.
- Review the toil budget's real usage on a regular cadence, confirming the ceiling is still meaningful as the service and team change.

## 16. Observability signals

- Track the ratio of toil to total operational time as a primary, regularly reviewed metric, distinct from raw incident or ticket counts.
- Track how often the automation for a given task is actually invoked versus how often the underlying manual procedure would have been required, confirming the automation is genuinely absorbing the load.
- Track automation failure and fallback events distinctly, since a rising rate of fallback to the manual procedure signals the automation is silently breaking down.

## 17. Security and privacy implications

- Automation that performs a previously manual, human-reviewed action removes the human judgment step, so any automated task that touches access control, credentials, or a destructive operation needs its own explicit safety checks, not just a copy of the manual procedure's steps.
- An automation implementation commonly needs broader system access than any single person would have had to perform the task manually, since it runs unattended, and that expanded access should be scoped as narrowly as the task actually requires.
- Logs generated by the automation should record what it did and why, with the same care as the audit trail the manual procedure would have left, so an automated action remains traceable after the fact.

## Code examples

### Python

```python
from dataclasses import dataclass, field


@dataclass
class ToilTask:
    name: str
    frequency_per_month: int
    minutes_per_occurrence: int
    automatable: bool

    @property
    def monthly_minutes(self):
        return self.frequency_per_month * self.minutes_per_occurrence


@dataclass
class ToilInventory:
    tasks: list = field(default_factory=list)

    def total_monthly_minutes(self):
        return sum(t.monthly_minutes for t in self.tasks)

    def over_budget(self, capacity_minutes, budget_fraction):
        return self.total_monthly_minutes() > capacity_minutes * budget_fraction

    def best_automation_target(self):
        candidates = [t for t in self.tasks if t.automatable]
        if not candidates:
            return None
        return max(candidates, key=lambda t: t.monthly_minutes)


inventory = ToilInventory(
    tasks=[
        ToilTask("restart stuck worker", 20, 10, True),
        ToilTask("manual quarterly design review", 1, 90, False),
    ]
)
print('over budget', inventory.over_budget(10000, 0.05))
target = inventory.best_automation_target()
print('automation target', target.name if target else None)
```

### Kotlin

```kotlin
data class ToilTask(
    val name: String,
    val frequencyPerMonth: Int,
    val minutesPerOccurrence: Int,
    val automatable: Boolean,
) {
    val monthlyMinutes: Int
        get() = frequencyPerMonth * minutesPerOccurrence
}

class ToilInventory(private val tasks: List<ToilTask>) {
    fun totalMonthlyMinutes(): Int = tasks.sumOf { it.monthlyMinutes }

    fun overBudget(capacityMinutes: Int, budgetFraction: Double): Boolean {
        return totalMonthlyMinutes() > capacityMinutes * budgetFraction
    }

    fun bestAutomationTarget(): ToilTask? {
        return tasks.filter { it.automatable }.maxByOrNull { it.monthlyMinutes }
    }
}

fun main() {
    val inventory = ToilInventory(
        listOf(
            ToilTask("restart stuck worker", 20, 10, true),
            ToilTask("manual quarterly design review", 1, 90, false),
        )
    )
    println("over budget " + inventory.overBudget(10000, 0.05))
    val target = inventory.bestAutomationTarget()
    println("automation target " + (target?.name ?: "none"))
}
```

### Swift

```swift
struct ToilTask {
    let name: String
    let frequencyPerMonth: Int
    let minutesPerOccurrence: Int
    let automatable: Bool

    var monthlyMinutes: Int {
        frequencyPerMonth * minutesPerOccurrence
    }
}

struct ToilInventory {
    let tasks: [ToilTask]

    func totalMonthlyMinutes() -> Int {
        tasks.reduce(0) { $0 + $1.monthlyMinutes }
    }

    func overBudget(capacityMinutes: Int, budgetFraction: Double) -> Bool {
        let budget = Double(capacityMinutes) * budgetFraction
        return Double(totalMonthlyMinutes()) > budget
    }

    func bestAutomationTarget() -> ToilTask? {
        tasks.filter { $0.automatable }.max { $0.monthlyMinutes < $1.monthlyMinutes }
    }
}

let inventory = ToilInventory(tasks: [
    ToilTask(name: "restart stuck worker", frequencyPerMonth: 20, minutesPerOccurrence: 10, automatable: true),
    ToilTask(name: "manual quarterly design review", frequencyPerMonth: 1, minutesPerOccurrence: 90, automatable: false),
])
print("over budget " + String(inventory.overBudget(capacityMinutes: 10000, budgetFraction: 0.05)))
if let target = inventory.bestAutomationTarget() {
    print("automation target " + target.name)
}
```

## 18. References

- Google, Site Reliability Engineering, Eliminating Toil chapter (https://sre.google/sre-book/eliminating-toil/)
- Google, SRE Workbook, Eliminating Toil chapter (https://sre.google/workbook/eliminating-toil/)
