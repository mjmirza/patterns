---
name: Watchdog Timer
slug: watchdog-timer
family: 28-embedded-hardware
category: Behavioral
aliases: [WDT, Feed the Dog, Kick the Watchdog]
first_described: "Zephyr Project documentation, Task Watchdog service"
maturity: canonical
related: [interrupt-service-routine, polling-loop]
incompatible_with: []
verified: 2026-08-21
---

# Watchdog Timer

## 1. Name, aliases, and lineage

The canonical name is Watchdog Timer, the hardware and software pattern
where a timer counts down independently of the main application, and
the running software must periodically reset that countdown before it
reaches zero, or a corrective action, usually a full system reset,
fires automatically. The Zephyr Project's own documentation states the
purpose directly. "Its purpose is to trigger an action, usually a
system reset, in case of severe software malfunctions."

The alias **WDT** is the standard industry abbreviation, used
constantly across microcontroller vendor datasheets and RTOS
documentation. **Feed the Dog** and **Kick the Watchdog** are the
common informal names for the periodic reset action itself, both
describing the same operation Zephyr's own documentation calls
feeding. "Once initialized, the watchdog timer has to be restarted,
fed, in regular intervals to prevent it from timing out."

## 2. Problem and context

Embedded software can genuinely hang, an infinite loop, a deadlock, a
stuck wait on hardware that never responds, and once it hangs there is
often no human present to notice and power-cycle the device, since a
huge share of embedded systems run unattended for months or years. A
Watchdog Timer solves this by placing a countdown entirely outside the
application's own control, in hardware or in a dedicated, independent
timer, so that the application's own hang cannot prevent the
corrective action from firing. Zephyr's own documentation states the
consequence of a genuine hang directly. "If the software got stuck and
does not manage to feed the watchdog anymore, the corrective action is
triggered to bring the system back to normal operation." The watchdog
does not detect what went wrong, it only detects that the application
stopped doing the one thing a working application reliably does, feed
it on schedule.

## 3. Forces

The pattern balances the following competing pressures.

- **Automatic recovery from an unattended hang.** Favored. A device
  that hangs and cannot be manually power-cycled recovers on its own,
  directly addressing the core problem the pattern exists to solve.
- **Detecting a genuine application hang, not merely the absence of a
  hang somewhere specific.** Sacrificed, to a real degree. A watchdog
  fed with no real condition attached, by a timer interrupt regardless of whether the
  application's actual logic is still healthy, proves nothing about
  whether the application is genuinely working, only that some
  interrupt still fires, a much weaker guarantee than the pattern
  appears to offer at first glance.
- **Simplicity of the feeding mechanism.** Favored, for the simplest
  variant, a single periodic feed call. Sacrificed for the more
  faithful variant that requires every genuinely critical task to
  report its own health before the watchdog is fed on their behalf.
- **The severity of the corrective action.** Sacrificed to a degree,
  since the corrective action, usually a full system reset, is itself
  disruptive, losing any unsaved state and interrupting whatever the
  system was doing, a cost that must be weighed against the cost of
  leaving a genuinely hung system running unattended.

## 4. Applicability and non-applicability

Reach for a Watchdog Timer when the following hold.

- The device genuinely runs unattended, where a hang with no automatic
  recovery could leave it non-functional for an unacceptable length of
  time before a human intervenes.
- The corrective action, usually a reset, is genuinely an acceptable
  outcome for the specific failure the watchdog is meant to catch,
  since the watchdog exists specifically to force that action when
  the software cannot recover on its own.
- The feeding mechanism can be genuinely tied to the actual health of
  the critical work the system performs, rather than to an interrupt
  or timer that would keep firing even if that critical work had
  already hung.

Do NOT reach for a Watchdog Timer, or reach for it only with real
caution, in these cases, and the reason matters more than the rule.

- **The feeding mechanism cannot genuinely be tied to real application
  health**, a watchdog fed with no real condition attached, by a hardware timer that
  runs independently of the application's actual logic gives a false
  sense of protection, since it will keep being fed even while the
  application it is meant to protect has genuinely hung.
- **The corrective action's disruption is worse than the hang it is
  meant to prevent**, a system where a reset would destroy in-progress,
  unrecoverable work, and where a human is genuinely present and able
  to intervene faster and more safely than an automatic reset, may be
  better served by a different failure-handling strategy.
- **The device is not genuinely unattended**, a development or
  debugging session where an engineer is actively present and would
  rather see the hang directly, rather than have it silently reset
  away by an active watchdog, is a case to disable the watchdog for.

## 5. Structure

A Watchdog Timer has three structural parts.

- **The independent countdown**, a hardware timer or a dedicated
  software timer that counts down on its own schedule, outside the
  main application's direct control.
- **The feed operation**, the function the application calls to reset
  that countdown back to its full value, Zephyr's own API documenting
  it directly. "Feed specified watchdog timeout."
- **The corrective action**, triggered automatically the moment the
  countdown reaches zero without having been fed, Zephyr's own
  documentation naming the usual form. "Usually a system reset."

## 6. ASCII structure diagram

```
  +----------------------------------------------------------+
  |  Watchdog countdown, independent of the application            |
  |    counts down from its configured window                     |
  +----------------------------------------------------------+
            |                              |
   application feeds it          countdown reaches zero
   before it expires              with no feed received
            |                              |
            v                              v
  +--------------------+      +------------------------+
  |  countdown resets     |      |  corrective action fires  |
  |  to its full window    |      |  usually a system reset    |
  +--------------------+      +------------------------+
```

## 7. Dynamics

The trace below shows the two possible outcomes for a running system.

```
Healthy application

the application's critical work completes its cycle on schedule
   |-- the application calls the feed function
   |-- the watchdog's countdown resets to its full window
   |-- the cycle repeats, and the countdown never reaches zero

Hung application

the application's critical work hangs, deadlocks, or enters an
infinite loop and never returns to call the feed function
   |-- the watchdog's countdown continues counting down, unfed
   |-- the countdown reaches zero
   |-- the corrective action fires automatically, per Zephyr's own
       documentation, "to bring the system back to normal operation,"
       with no human intervention required
```

## 8. Implementation variants

**Simple periodic feed.** A single timer interrupt or a low-priority
task feeds the watchdog on a fixed schedule, the simplest variant to
implement, but the one dimension 3 names as the weakest at genuinely
detecting an application hang, since the feed continues regardless of
whether the application's real work is actually healthy.

**Task-health-gated feed, the Task Watchdog pattern.** Every genuinely
critical task must report its own health, an explicit call confirming
it is still making progress, before the watchdog is fed on the whole
system's behalf, following Zephyr's own Task Watchdog service model,
so a single hung critical task, even while other tasks keep running,
still triggers the corrective action.

**Windowed watchdog.** The watchdog's own API accepts a configured
window, feeding either too early or too late within that window is
itself treated as a fault, catching not only a hang but also a runaway
task that is feeding the watchdog far more often than its designed
cycle should produce.

## 9. Known production uses

**The Zephyr Project's own Task Watchdog documentation, defining the
pattern's purpose and behavior.** Zephyr states the purpose and the
feeding requirement directly. "Its purpose is to trigger an action,
usually a system reset, in case of severe software malfunctions,"
and "once initialized, the watchdog timer has to be restarted, fed, in
regular intervals to prevent it from timing out." It further states
the hang-recovery behavior. "If the software got stuck and does not
manage to feed the watchdog anymore, the corrective action is
triggered to bring the system back to normal operation." The Zephyr
Project, "Task Watchdog,"
https://docs.zephyrproject.org/latest/services/task_wdt/index.html,
verified 2026-08-21.

**The Zephyr Project's own watchdog driver API documentation, on the
feed and setup functions.** Zephyr states the feed operation directly.
"Feed specified watchdog timeout," and states that once
`wdt_setup()` completes, "all installed timeouts are valid and must be
serviced periodically by calling `wdt_feed()`." The Zephyr Project,
"Watchdog Interface,"
https://docs.zephyrproject.org/latest/doxygen/html/group__watchdog__interface.html,
verified 2026-08-21.

## 10. Consequences

Positive.

- A device that hangs recovers on its own, without needing a human to
  notice and power-cycle it, directly delivering the automatic
  recovery the pattern exists to provide.
- The task-health-gated variant genuinely ties the watchdog's feed to
  real application health, catching a hang in a specific critical task
  even while the rest of the system continues running.
- The pattern's corrective action is unconditional and independent of
  the application's own logic, so it fires even in failure modes the
  application's own error handling never anticipated.

Negative.

- A simple watchdog fed with no real condition attached gives a false sense of
  protection, since it keeps being fed by a timer or interrupt that has
  no genuine connection to whether the application's real work is
  still healthy.
- The corrective action, usually a full reset, is itself disruptive,
  losing any unsaved state and interrupting whatever the system was
  doing at the moment the watchdog expired.
- Implementing the more faithful, task-health-gated variant adds real
  implementation surface, every genuinely critical task must be
  wired to report its own health before the shared watchdog is fed.

## 11. Failure modes and misuse

**Feeding the watchdog with no real condition attached, from an interrupt or timer with
no genuine connection to application health.** Symptom. The
application genuinely hangs, but the watchdog continues to be fed by
an unrelated periodic interrupt, and the corrective action never
fires, leaving the hung device running unattended and unrecovered.
Cause. Wiring the feed call to a source, a hardware timer interrupt or
a low-priority idle task, whose continued execution says nothing about
whether the application's actual critical work is still making
progress. Fix. Tie the feed call to the genuine health of the specific
work the watchdog is meant to protect, following the task-health-gated
variant, so a hang in that work is the thing that actually stops the
feed.

**Setting the watchdog's timeout window too short for the application's
own legitimate worst-case processing time.** Symptom. The watchdog
fires and resets the system during genuine, correct operation, not
because the application hung, but because a legitimately long
operation, a large data transfer or a slow peripheral response, simply
took longer than the configured window allows. Cause. Configuring the
watchdog's timeout without measuring the application's real worst-case
timing, or without accounting for a legitimately slow but correct
operation. Fix. Measure the application's genuine worst-case timing
for the work between feeds, and set the watchdog's window with real
margin above that measured worst case, rather than an arbitrary,
unmeasured value.

**Disabling the watchdog during development and forgetting to
re-enable it before shipping.** Symptom. A device shipped to
production hangs in the field and never recovers automatically, even
though the watchdog was correctly implemented, because it was left
disabled from a debugging session and never turned back on before the
firmware was released. Cause. Treating the watchdog's disabled state,
convenient during active debugging so a hang can be inspected directly
rather than silently reset away, as a temporary setting that was never
verified to be re-enabled in the shipped build. Fix. Verify, as part
of the release process, that the watchdog is genuinely enabled in the
production build, treating an accidentally-disabled watchdog in a
shipped device as a release-blocking defect.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Watchdog Timer, task-health-gated | Watchdog Timer, simple periodic feed | No watchdog, manual power-cycle only |
|---|---|---|---|
| Automatic recovery from an unattended hang | Strong, recovers with no human present | Strong for total hangs, weak for a hang in one specific task if the feed source keeps running | Weak, requires a human to notice and intervene |
| Detecting a genuine application hang | Strong, tied to real critical-task health | Weak, only detects that the feed source itself stopped, not that the application is healthy | Not applicable, there is no automatic detection |
| Simplicity of the feeding mechanism | Weak, every critical task must report health | Strong, a single periodic feed call | Strong, there is no feeding mechanism to build |
| Severity of the corrective action's disruption | Moderate, same reset cost as the simple variant | Moderate, same reset cost | None automatically, though an undetected hang may persist far longer |

Reading of the table. A task-health-gated Watchdog Timer wins
specifically when the system genuinely needs the strongest real
guarantee that critical work is healthy, worth its added
implementation cost. A simple periodic feed remains a reasonable,
lighter-weight choice when total-hang recovery is the real goal and
the implementation cost of task-level health reporting is not
justified.

## 13. Related and incompatible patterns

- **Interrupt Service Routine.** A watchdog's feed call, or the health
  reports that gate it in the task-health-gated variant, are sometimes
  driven from a periodic interrupt, and dimension 11's first failure
  mode is the specific trap of tying that interrupt to something with
  no genuine connection to real application health.
- **Polling Loop.** On a system with no RTOS, a bare-metal polling loop
  is a common place to call the watchdog's feed function, once per
  loop iteration, tying the feed directly to the loop's own continued,
  genuine execution.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a system with no watchdog protection currently
in place.

1. Confirm the device genuinely runs unattended, and that an
   automatic reset is a genuinely acceptable corrective action for
   the failures the watchdog is meant to catch.
2. Measure the application's real worst-case timing for the work
   between feeds, and configure the watchdog's timeout window with
   real margin above that measured worst case.
3. Choose between the simple periodic-feed variant and the
   task-health-gated variant, based on how strong a real guarantee of
   application health the system genuinely needs.
4. Wire the feed call, or the critical tasks' health reports, to a
   source that genuinely reflects whether the protected work is
   actually making progress, never to an unrelated interrupt or timer.
5. Verify, as part of the release process, that the watchdog is
   genuinely enabled in the shipped production build.

Removing the pattern when it stops earning its place, most relevant
for a device that has moved from unattended field deployment to an
actively supervised debugging or development context.

1. Confirm, concretely, that a human is genuinely present and able to
   intervene faster and more safely than an automatic reset would,
   rather than assuming so without checking the actual deployment
   context.
2. Disable the watchdog for that specific development or debugging
   session, so a hang can be inspected directly rather than silently
   reset away.
3. Confirm, before the device returns to an unattended production
   context, that the watchdog is genuinely re-enabled, treating a
   forgotten disable as a release-blocking defect.

## 15. Testing and verification

Easier because of the pattern.

- A test can deliberately simulate a hang, by never calling the feed
  function, and assert the corrective action fires within the
  configured timeout window, directly verifying the pattern's core
  guarantee.
- Because the feed operation has a single, well-defined API, a test
  double can substitute for the real watchdog hardware, letting the
  application's own feeding logic be verified on a host machine
  without needing the real watchdog peripheral present.

Harder because of the pattern.

- Verifying the watchdog's real timeout window and its real corrective
  action genuinely match the configured values needs a test on the
  actual target hardware, since a host-based simulation does not
  reproduce the real hardware timer's actual behavior.
- Confirming the task-health-gated variant genuinely catches a hang in
  one specific critical task, while other tasks continue running, needs
  a test that can selectively hang exactly one task, a category of
  test that is easy to omit if only a total system hang is tested.

Techniques that apply.

- **Deliberate hang simulation.** Never call the feed function in a
  test scenario, and assert the corrective action fires within the
  configured timeout window on the real target hardware.
- **Worst-case timing tests.** Measure the application's real
  worst-case timing for the work between feeds, on real hardware, and
  assert it stays comfortably within the configured timeout window
  with real margin.
- **Single-task hang tests, for the task-health-gated variant.**
  Deliberately hang one specific critical task while the rest of the
  system continues running, and assert the corrective action still
  fires.
- **Release-build watchdog-enabled verification.** Confirm, as part of
  the release process, that the shipped production build genuinely
  has the watchdog enabled, not left disabled from a development
  session.

## 16. Observability signals

What to record.

- Whether the watchdog's corrective action has fired in the field,
  and how frequently, since this signal directly measures how often
  the system is genuinely hanging in real, unattended deployment.
- The measured real-world margin between the application's actual
  feed timing and the configured timeout window, since a shrinking
  margin points at a system drifting toward its own timeout budget.

A healthy state. The watchdog's corrective action fires rarely or
never in real field deployment, and the measured margin between real
feed timing and the configured timeout stays comfortably wide.

A failing state. The corrective action fires with real
frequency in the field, pointing at a genuine, recurring hang that
needs root-cause investigation, or the measured margin between real
feed timing and the configured timeout shrinks over time, pointing at
a system whose real-world timing is drifting toward its own
configured budget.

## 17. Security and privacy implications

**A watchdog whose feed function is reachable from untrusted, external
input is a genuine denial-of-service surface, since an attacker who
can trigger repeated, artificial feeds, or who can prevent legitimate
feeds from occurring, gains real influence over when the corrective
reset fires.** If external, network-reachable input can directly or
indirectly control the timing of the watchdog's feed calls, the
pattern's own protective mechanism becomes a tool an attacker can
pull, either forcing repeated resets as a denial-of-service attack, or,
in a system relying on the watchdog to recover from a specific fault
condition, deliberately starving the feed to hold the system in a
compromised state until the attacker's own timing, rather than the
watchdog's, decides when it resets. The feed function's reachability
from external input is worth auditing directly, treating any path
where untrusted input can influence feed timing as a genuine security
concern rather than a purely theoretical one.

## 18. References

1. The Zephyr Project. "Task Watchdog".
   https://docs.zephyrproject.org/latest/services/task_wdt/index.html
   Verified 2026-08-21. Source of the purpose, feeding, and
   hang-recovery quotes used in dimensions 1, 2, 3, 9, and 10.
2. The Zephyr Project. "Watchdog Interface".
   https://docs.zephyrproject.org/latest/doxygen/html/group__watchdog__interface.html
   Verified 2026-08-21. Source of the feed and setup API quotes used
   in dimensions 5 and 9.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. C models the independent-countdown-plus-feed shape directly, the
language embedded firmware and RTOS watchdog drivers are actually
written in, using a simple counter to simulate the independent
countdown. Python shows the same conceptual shape using a minimal,
host-testable simulation, the pattern's deliberate-hang-test variant
from dimension 15, expressed portably. Swift shows the same conceptual
shape using a minimal model, analogous to how a native application's
own supervisory process might track whether a critical background task
is still reporting progress. Java, Go, and Rust are omitted, since the
pattern's real home is C and the two languages chosen already cover
its production and its testable-simulation shapes.

### C

```c
#include <stdio.h>
#include <stdbool.h>

typedef struct {
    int countdown;
    int window;
    bool expired;
} watchdog_t;

static void watchdog_init(watchdog_t *wdt, int window) {
    wdt->window = window;
    wdt->countdown = window;
    wdt->expired = false;
}

static void watchdog_feed(watchdog_t *wdt) {
    if (!wdt->expired) {
        wdt->countdown = wdt->window;
    }
}

static void watchdog_tick(watchdog_t *wdt) {
    if (wdt->expired) {
        return;
    }
    wdt->countdown -= 1;
    if (wdt->countdown <= 0) {
        wdt->expired = true;
        printf("watchdog expired, corrective action, system reset");
        putchar(10);
    }
}

int main(void) {
    watchdog_t wdt;
    watchdog_init(&wdt, 3);

    watchdog_tick(&wdt);
    watchdog_feed(&wdt);
    watchdog_tick(&wdt);
    watchdog_tick(&wdt);
    watchdog_tick(&wdt);
    watchdog_tick(&wdt);

    printf("watchdog expired: %s", wdt.expired ? "true" : "false");
    putchar(10);
    return 0;
}
```

### Python

```python
from dataclasses import dataclass


@dataclass
class Watchdog:
    window: int
    countdown: int = 0
    expired: bool = False

    def __post_init__(self) -> None:
        self.countdown = self.window

    def feed(self) -> None:
        if not self.expired:
            self.countdown = self.window

    def tick(self) -> None:
        if self.expired:
            return
        self.countdown -= 1
        if self.countdown <= 0:
            self.expired = True
            print("watchdog expired, corrective action, system reset")


if __name__ == "__main__":
    wdt = Watchdog(window=3)

    wdt.tick()
    wdt.feed()
    wdt.tick()
    wdt.tick()
    wdt.tick()
    wdt.tick()

    print("watchdog expired: " + str(wdt.expired))
```

### Swift

```swift
final class Watchdog {
    private let window: Int
    private var countdown: Int
    private(set) var expired: Bool = false

    init(window: Int) {
        self.window = window
        self.countdown = window
    }

    func feed() {
        guard !expired else { return }
        countdown = window
    }

    func tick() {
        guard !expired else { return }
        countdown -= 1
        if countdown <= 0 {
            expired = true
            print("watchdog expired, corrective action, system reset")
        }
    }
}

let wdt = Watchdog(window: 3)

wdt.tick()
wdt.feed()
wdt.tick()
wdt.tick()
wdt.tick()
wdt.tick()

print("watchdog expired: " + String(wdt.expired))
```
