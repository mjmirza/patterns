---
name: Game Day
slug: game-day
family: 21-sre-operations
category: Behavioral
aliases: [Disaster Recovery Testing, DiRT, Fire Drill]
first_described: 'Google, Site Reliability Engineering, Lessons Learned chapter (DiRT), 2016'
maturity: canonical
related: [runbook-automation, chaos-engineering]
incompatible_with: []
verified: 2026-08-22
---

# Game Day

## 1. Name, aliases, and lineage

Game Day. Also called Disaster Recovery Testing, DiRT, or a Fire Drill. A Game Day is a scheduled exercise where a team deliberately simulates a failure or disaster scenario in a controlled way, to test whether the systems, the runbooks, and the people actually respond correctly. Google names its own annual version of this practice directly in the SRE book. our annual Disaster and Recovery Testing (DiRT) drills seek to address these questions head-on (https://sre.google/sre-book/lessons-learned/). AWS's Well-Architected Framework describes the same practice under its own name. game days simulate events in production-like environments to test systems, processes, and team responses (https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_testing_resiliency_game_days_resiliency.html).

The lineage traces to military and emergency-services fire drills, adapted for software operations. rather than waiting for a real disaster to reveal a gap in a system, a runbook, or a team's readiness, the team creates the disaster on purpose, on a schedule it controls, so the gap is found and fixed before it costs a real incident.

## 2. Problem and context

A system's resilience, a runbook's correctness, and a team's readiness are all assumptions until they are tested against a real failure. Waiting for a genuine disaster to test those assumptions means the first real test happens under the worst possible conditions, with real users affected and no opportunity to pause and reset if something goes wrong.

AWS's own framing states the purpose plainly. the purpose is to perform the same actions the team would perform as if the event actually occurred (https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_testing_resiliency_game_days_resiliency.html). The problem this pattern solves is that a controlled, scheduled rehearsal of a disaster is far cheaper and far safer than discovering the same gap during a genuine one, and it gives the team a chance to reset, discuss, and fix what was found without any real user impact.

## 3. Forces

- A Game Day scenario needs to be realistic enough to find genuine gaps, but controlled enough that it does not itself cause a real outage the team did not intend.
- The team responding to the simulated disaster needs to be the same people who would respond to a real one, or the exercise does not genuinely test the team's actual readiness.
- Running a Game Day takes real coordination and scheduling time from people who are already busy with production work, which competes for priority against feature and reliability work.
- A finding uncovered during a Game Day is only valuable if it is actually acted on afterward, or the exercise becomes a ritual with no real improvement attached to it.
- Simulating a disaster in a production-like environment risks a real impact if the blast radius is not carefully scoped in advance.

## 4. Applicability and non-applicability

Use a Game Day for any system whose failure would have a real cost, where the team wants to verify, on a schedule it controls, that its runbooks, its automated recovery, and its people actually work together correctly under a realistic failure scenario. It is especially valuable before a high-stakes period (a major launch, a peak traffic season) where the cost of an untested gap would be highest.

Skip it for a system too small or too low-stakes for the coordination cost of a full exercise to be worth it, and skip a scenario whose blast radius cannot be safely bounded, since an uncontrolled simulated disaster defeats the purpose of testing readiness safely.

## 5. Structure

- Scenario definition. the specific failure or disaster being simulated, scoped with a defined blast radius and a clear success criteria for what a correct response looks like.
- Responding team. the same people who would handle a real instance of this scenario, participating as if the event actually occurred.
- Observers. people tracking what happens during the exercise without intervening, recording what worked and what did not.
- Abort criteria. an explicit, agreed condition under which the exercise is stopped immediately if it risks a genuine unintended impact.
- Findings log. the record of every gap, confusion, or failure observed during the exercise, the direct input to the follow-up work afterward.

## 6. ASCII structure diagram

```
  Scenario definition
  (scope, blast radius,
   success criteria)
        |
        v
  Responding team acts as if the event is real
        |
        v
  Observers record to the Findings log
        |
        v
  crosses Abort criteria?  ----- yes -----> stop immediately, record why
        |
        no
        |
        v
  exercise completes
        |
        v
  Findings log drives follow-up fixes
```

## 7. Dynamics

1. The team defines the scenario in advance, scoping the specific failure to simulate, the blast radius it is allowed to touch, and what a correct response looks like.
2. The responding team, the same people who would handle a genuine instance of the scenario, acts on it as if the event actually occurred, following AWS's own framing of the practice (https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_testing_resiliency_game_days_resiliency.html).
3. Observers track the response without intervening, recording every gap or confusion into the findings log as it happens, rather than relying on memory afterward.
4. If the exercise crosses its abort criteria (a sign the simulated disaster is at risk of becoming a genuine unintended one), it is stopped immediately, and the reason is recorded for the next attempt.
5. Google's own framing of these drills names the underlying goal directly, as drills that seek to address these questions head-on (https://sre.google/sre-book/lessons-learned/), meaning the exercise exists specifically to surface unknown weaknesses before a real disaster does.
6. After the exercise, the findings log drives concrete follow-up work, fixing the runbook gaps, automation gaps, or team-readiness gaps the exercise revealed.

## 8. Implementation variants

- Tabletop exercise. the team walks through the scenario verbally, without touching real systems, the lowest risk and lowest realism variant, useful for testing a plan before running it for real.
- Scoped production exercise. a real, bounded action is taken against production or a production-like environment, with a tightly defined blast radius and an explicit abort path, matching AWS's own recommendation to conduct game days regularly (https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_testing_resiliency_game_days_resiliency.html).
- Unannounced internal drill. only a small group knows the exercise is not a real incident, testing the team's genuine, unrehearsed response rather than a prepared one, at the cost of higher coordination risk.
- Annual company-wide exercise. matching Google's own DiRT practice, a large, cross-team exercise run on a fixed yearly schedule, testing cross-team coordination in addition to any single team's own readiness.

## 9. Known production uses

- Google runs an annual Disaster and Recovery Testing exercise across its production services, documented in the Lessons Learned chapter of the freely available SRE book (https://sre.google/sre-book/lessons-learned/).
- AWS's Well-Architected Framework publishes a dedicated best practice, REL12-BP05, recommending organizations conduct game days regularly to exercise their procedures for responding to workload-impacting events (https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_testing_resiliency_game_days_resiliency.html), involving the same teams who would be responsible for handling production scenarios.
- Organizations across the industry that adopt SRE or Well-Architected practice commonly schedule game days ahead of major launches or peak traffic periods, treating readiness verification as a planned, repeatable exercise rather than an occasional afterthought.

## 10. Consequences

### Benefits

- A gap in a runbook, an automation, or a team's readiness is found on a schedule the team controls, rather than during a genuine incident with real users affected.
- The exercise gives the team a chance to reset and discuss what went wrong without the pressure and cost of a real outage.
- Running the exercise with the same team that would handle a real incident builds genuine muscle memory for that team, not just a documented plan nobody has actually practiced.

### Costs

- Coordinating and running a genuine exercise takes real time from people who are already busy with production work.
- A poorly scoped scenario risks becoming a real unintended outage, the opposite of what the controlled exercise was meant to achieve.
- Findings that are logged but never acted on turn the exercise into a ritual with no real improvement, wasting the coordination cost without capturing its benefit.

## 11. Failure modes and misuse

- No defined abort criteria, so a scenario that starts drifting toward a genuine unintended outage has no clear point at which it gets stopped.
- Running the exercise with a different team than the one that would handle a real instance of the scenario, testing a plan rather than the actual people and their actual readiness.
- A findings log that is written but never reviewed, so the exercise surfaces real gaps that then sit unfixed until a genuine incident hits the same gap.
- Scheduling the exercise so rarely that the findings from the last one are stale by the time the next one runs, missing changes the system has gone through in between.
- Treating a tabletop-only exercise as equivalent to a real, scoped production exercise, when the two find genuinely different classes of gap.

## 12. Trade-off matrix

| Dimension | Tabletop exercise | Scoped production exercise |
|---|---|---|
| Realism of the finding | Lower, plan-level only | Higher, real system behavior tested |
| Risk of unintended impact | Very low | Real, requires careful scoping |
| Coordination cost | Lower | Higher |
| Confidence gained | Moderate | Higher, since real systems were exercised |
| Good starting point for a new team | Yes | Better attempted after tabletop practice |

## 13. Related and incompatible patterns

### Related

- Runbook Automation. a Game Day is one of the primary ways a team discovers which runbook steps are still manual, slow, or unclear, directly feeding the next round of automation work.
- Chaos Engineering. both patterns deliberately introduce failure to test resilience, but a Game Day is a scheduled, team-driven exercise, while Chaos Engineering is continuous, often automated fault injection.

### Incompatible with

- None directly, though running a Game Day with no abort criteria works against the pattern's own safe-by-design intent, even though it is still labeled as a Game Day.

## 14. Refactoring path in and out

### Introducing it

1. Start with a tabletop exercise for a well understood scenario, walking through the plan verbally before touching any real system.
2. Define the scenario, the blast radius, the success criteria, and the abort criteria explicitly and in writing before the first real exercise.
3. Run a scoped production exercise with the same team that would handle a genuine instance of the scenario, with observers tracking findings throughout.
4. Review the findings log after the exercise, and turn every real gap into a tracked, owned follow-up item.
5. Schedule the exercise on a recurring cadence, so readiness is verified regularly rather than once and never revisited.

### Removing it

1. Confirm the system or team the exercise covers is being retired or has genuinely stopped needing this level of readiness verification.
2. Retire the scheduled exercise and its coordination ownership, keeping the historical findings log as a record of what was learned.

## 15. Testing and verification

- Verify the abort criteria itself before the exercise, confirming every observer and every responding team member knows exactly when and how to stop the exercise if it drifts toward genuine impact.
- Verify the scenario's blast radius is actually bounded as designed, by reviewing what systems and users the scenario could touch before running it for real.
- Review the findings log after every exercise, confirming each real gap is tracked as a concrete follow-up item with an owner.
- Periodically re-run a past scenario after its findings were addressed, confirming the fix genuinely closed the gap the exercise found.

## 16. Observability signals

- Track how many findings each exercise surfaces and how many of the prior exercise's findings were actually closed before the next one runs, as a measure of whether the practice is genuinely improving readiness.
- Track the exercise cadence itself, confirming it is actually happening on schedule rather than being deferred indefinitely under competing priorities.
- Track how often a genuine incident matches a scenario the team has already exercised, and how that response compared to an incident with no prior exercise covering it.

## 17. Security and privacy implications

- A scoped production exercise that touches real systems must never expose real user data to observers or participants beyond what their normal role would already require, even in a simulated scenario.
- The abort criteria and the blast-radius scoping are themselves a security control, and weakening either one to make the exercise more realistic trades safety for realism in a way that should be a deliberate, reviewed decision, not a default.
- Findings logged during the exercise, especially ones revealing a genuine security or access-control gap, should be handled with the same care as any other sensitive incident record.

## Code examples

### Python

```python
from dataclasses import dataclass, field


@dataclass
class GameDayScenario:
    name: str
    blast_radius: str
    success_criteria: str
    abort_criteria: str


@dataclass
class GameDayRun:
    scenario: GameDayScenario
    findings: list = field(default_factory=list)
    aborted: bool = False

    def record_finding(self, description):
        self.findings.append(description)

    def check_abort(self, observed_condition):
        if observed_condition == self.scenario.abort_criteria:
            self.aborted = True
            self.record_finding("aborted: " + observed_condition)
        return self.aborted


scenario = GameDayScenario(
    name="primary datacenter outage",
    blast_radius="staging environment only",
    success_criteria="traffic fails over within 5 minutes",
    abort_criteria="real user impact detected",
)
run = GameDayRun(scenario=scenario)
run.record_finding("failover took 7 minutes, runbook step 3 was unclear")
print('aborted', run.aborted)
print('findings', run.findings)
```

### Kotlin

```kotlin
data class GameDayScenario(
    val name: String,
    val blastRadius: String,
    val successCriteria: String,
    val abortCriteria: String,
)

class GameDayRun(private val scenario: GameDayScenario) {
    val findings = mutableListOf<String>()
    var aborted = false
        private set

    fun recordFinding(description: String) {
        findings.add(description)
    }

    fun checkAbort(observedCondition: String): Boolean {
        if (observedCondition == scenario.abortCriteria) {
            aborted = true
            recordFinding("aborted: " + observedCondition)
        }
        return aborted
    }
}

fun main() {
    val scenario = GameDayScenario(
        name = "primary datacenter outage",
        blastRadius = "staging environment only",
        successCriteria = "traffic fails over within 5 minutes",
        abortCriteria = "real user impact detected",
    )
    val run = GameDayRun(scenario)
    run.recordFinding("failover took 7 minutes, runbook step 3 was unclear")
    println("aborted " + run.aborted)
    println("findings " + run.findings)
}
```

### Swift

```swift
struct GameDayScenario {
    let name: String
    let blastRadius: String
    let successCriteria: String
    let abortCriteria: String
}

final class GameDayRun {
    let scenario: GameDayScenario
    private(set) var findings: [String] = []
    private(set) var aborted = false

    init(scenario: GameDayScenario) {
        self.scenario = scenario
    }

    func recordFinding(_ description: String) {
        findings.append(description)
    }

    func checkAbort(observedCondition: String) -> Bool {
        if observedCondition == scenario.abortCriteria {
            aborted = true
            recordFinding("aborted: " + observedCondition)
        }
        return aborted
    }
}

let scenario = GameDayScenario(
    name: "primary datacenter outage",
    blastRadius: "staging environment only",
    successCriteria: "traffic fails over within 5 minutes",
    abortCriteria: "real user impact detected"
)
let run = GameDayRun(scenario: scenario)
run.recordFinding("failover took 7 minutes, runbook step 3 was unclear")
print("aborted " + String(run.aborted))
print("findings " + String(run.findings.count))
```

## 18. References

- Google, Site Reliability Engineering, Lessons Learned chapter (https://sre.google/sre-book/lessons-learned/)
- AWS Well-Architected Framework, REL12-BP05, Conduct game days regularly (https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_testing_resiliency_game_days_resiliency.html)
