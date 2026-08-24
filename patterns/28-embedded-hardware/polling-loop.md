---
name: Polling Loop
slug: polling-loop
family: 28-embedded-hardware
category: Behavioral
aliases: [Busy-Wait Loop, Spin Loop, Poll-and-Check]
first_described: "Zephyr Project documentation, UART polling mode"
maturity: canonical
related: [interrupt-service-routine, watchdog-timer]
incompatible_with: []
verified: 2026-08-21
---

# Polling Loop

## 1. Name, aliases, and lineage

The canonical name is Polling Loop, the pattern where code repeatedly
reads a hardware status flag or register in a tight loop until the
flag reports the condition the code is waiting for, rather than being
notified asynchronously by an interrupt. Zephyr's own documentation
names the mechanism directly for its UART peripheral, stating
"polling is the most basic method to access the UART peripheral," with
its write function "a blocking function" where "the thread waits
until the given character is sent."

The alias **Busy-Wait Loop** names the pattern by its cost, the CPU
stays fully active, never idling, for the entire wait. **Spin Loop**
names the same idea by the loop's shape, spinning through repeated
checks. **Poll-and-Check** names the pattern by its mechanism, one
read, one check, repeated.

## 2. Problem and context

A peripheral such as a UART, an ADC, or a GPIO pin reports its status
through a hardware register, and code needs to know the moment that
status changes, such as when a transmitted character has genuinely
left the UART or a conversion has genuinely completed. A Polling Loop
solves this by having the code itself repeatedly read that status
register in a loop, checking on every iteration whether the awaited
condition has become true, and only proceeding once it has. Zephyr's
own documentation states the read function's behavior directly, that
`uart_poll_in()` "is a non-blocking function and returns a character
or -1 when no valid data is available," so the calling code is the one
responsible for looping and re-checking until data genuinely arrives.

## 3. Forces

The pattern balances the following competing pressures.

- **Simplicity of implementation.** Favored. Zephyr's own
  documentation states this directly, that "polling is the most basic
  method to access the UART peripheral," requiring no interrupt
  registration, no callback, and no shared state between an interrupt
  handler and the main code path.
- **Predictable, low setup overhead.** Favored. A polling loop needs no
  interrupt controller configuration, no interrupt priority
  assignment, and no interrupt service routine, so it is genuinely the
  fastest path to a working, minimal implementation.
- **CPU availability for other work.** Sacrificed. Zephyr's own
  documentation names the alternative's benefit directly, that with
  interrupt-driven mode, "possibly slow communication can happen in the
  background while the thread continues with other tasks," a benefit
  a polling loop does not have, since the CPU is fully occupied
  checking the status register for the entire wait.
- **Power efficiency.** Sacrificed. The CPU stays fully active for the
  entire polling loop, unable to enter a low-power idle state the way
  it could while waiting for an interrupt to wake it.

## 4. Applicability and non-applicability

Reach for a Polling Loop when the following hold.

- The wait for the condition is genuinely short and bounded, such as
  waiting for a single UART character to finish transmitting, where
  the busy-wait cost is small and predictable.
- The system genuinely has no other work to do during the wait, so
  the CPU time spent polling is not actually taken from any other
  useful task.
- Simplicity genuinely matters more than efficiency, such as in an
  early bring-up or debug build where getting a peripheral working
  correctly, with the least code, outweighs the runtime cost.

Do NOT reach for a Polling Loop in these cases, and the reason matters
more than the rule.

- **The wait is genuinely unbounded or unpredictably long**, such as
  waiting for a UART character to arrive from an external device on
  its own schedule, a polling loop wastes CPU time for a duration it
  cannot know in advance, an interrupt-driven approach, per Zephyr's
  own documented benefit, lets the thread do other work during that
  same wait.
- **The system genuinely has other work that must run concurrently**,
  per Zephyr's own documented interrupt-driven benefit, a polling loop
  blocks the CPU from that other work for its entire duration, an
  interrupt-driven or event-driven approach fits this need instead.
- **Power efficiency is genuinely a hard requirement**, a polling loop
  keeps the CPU fully active for the entire wait, unable to enter a
  low-power state, an interrupt-driven approach that lets the CPU idle
  while waiting fits a battery-powered or energy-constrained system
  far better.

## 5. Structure

A Polling Loop has three structural parts.

- **The status source**, the hardware register or flag the loop reads,
  such as the UART data-ready bit Zephyr's own `uart_poll_in()`
  checks.
- **The check**, the condition evaluated against the status source on
  every loop iteration, deciding whether to continue looping or
  proceed.
- **The loop body**, the repeated read-and-check cycle itself, which
  runs with no yield or sleep between iterations, per the busy-wait
  alias's own name.

## 6. ASCII structure diagram

```
  loop {
      read status register  <----------+
      check condition                  |
      condition met? --- no ----------+
          |
         yes
          |
          v
      proceed
  }
```

## 7. Dynamics

The trace below shows one complete polling wait.

```
Code begins waiting for a condition

the loop reads the status register on its first iteration
   |-- if the condition is already true, per Zephyr's own documented
       non-blocking read behavior, the loop exits immediately and
       code proceeds
   |-- if the condition is not yet true, the loop reads the status
       register again on the next iteration, with no delay or yield
       in between, per the busy-wait alias

The condition becomes true

on some later iteration, the status register's value now satisfies
the check
   |-- the loop exits at that exact iteration
   |-- the CPU has been fully occupied, reading and checking, for the
       entire duration between the wait beginning and the condition
       becoming true, the cost the busy-wait alias names directly
```

## 8. Implementation variants

**Pure busy-wait, no yield.** The canonical form, described directly
above, where the loop reads and checks with no pause between
iterations, spending every available CPU cycle on the check.

**Polling with a bounded timeout.** The loop tracks elapsed time
alongside the status check, and exits with a failure result if the
condition has not become true within a defined time bound, preventing
an unbounded hang if the awaited condition never actually occurs.

**Cooperative polling, yielding between checks.** In a multi-threaded
or cooperative-scheduling system, the loop yields the CPU to other
ready work between each check, rather than spinning continuously,
trading some latency in detecting the condition for genuinely
allowing other work to run during the wait.

## 9. Known production uses

**Zephyr's own documentation, defining UART polling mode and its
non-blocking read behavior.** Zephyr states the mechanism directly.
"Polling is the most basic method to access the UART peripheral." The
reading function, `uart_poll_in()`, "is a non-blocking function and
returns a character or -1 when no valid data is available." The
writing function, `uart_poll_out()`, "is a blocking function and the
thread waits until the given character is sent." Zephyr Project,
"UART (Universal Asynchronous Receiver-Transmitter),"
https://docs.zephyrproject.org/latest/hardware/peripherals/uart.html,
verified 2026-08-21.

**Zephyr's own documentation, on the interrupt-driven alternative this
pattern trades against, and the warning against mixing the two.**
Zephyr states the alternative's benefit directly. With the
interrupt-driven API, "possibly slow communication can happen in the
background while the thread continues with other tasks." That same
documentation warns explicitly against using the polling and
interrupt-driven APIs simultaneously on one peripheral. Zephyr
Project, "UART (Universal Asynchronous Receiver-Transmitter),"
https://docs.zephyrproject.org/latest/hardware/peripherals/uart.html,
verified 2026-08-21.

## 10. Consequences

Positive.

- The implementation is genuinely simple, per Zephyr's own documented
  characterization of polling as "the most basic method," needing no
  interrupt registration or shared state between a handler and the
  main code.
- Behavior is easy to reason about, since the code that waits and the
  code that checks are the same sequential code path, with no
  asynchronous handler to reason about separately.
- Setup overhead is minimal, since no interrupt controller
  configuration or priority assignment is needed.

Negative.

- The CPU is fully occupied for the entire wait, unable to do any
  other work, a real cost Zephyr's own documentation names directly
  by contrast with the interrupt-driven alternative.
- The CPU cannot enter a low-power idle state during the wait, a real
  cost for any energy-constrained system.
- An unbounded polling loop with no timeout can hang the system
  indefinitely if the awaited condition never actually becomes true.

## 11. Failure modes and misuse

**A polling loop with no bounded timeout that can hang indefinitely if
the awaited hardware condition never actually occurs.** Symptom. The
system stops responding entirely, stuck in the polling loop, with no
error reported and no path forward, even though the rest of the
system is otherwise healthy. Cause. The loop's exit condition depends
entirely on a hardware status flag becoming true, with no independent
time bound, so a hardware fault, a disconnected peripheral, or a
genuine but unanticipated edge case that never sets the flag leaves
the loop spinning forever. Fix. Add a bounded timeout alongside the
status check, per the timeout variant in dimension 8, so the loop
always exits, with either success or a reported failure, within a
known, finite duration.

**Mixing the polling API and the interrupt-driven API on the same
peripheral at the same time.** Symptom. Data is lost, corrupted, or
processed out of order, and the failure is intermittent and hard to
reproduce, because two independent code paths, one polling and one
interrupt-driven, both read from the same underlying hardware
register. Cause. Zephyr's own documentation warns against this
directly, using both APIs on the same peripheral, because the
interrupt handler and the polling loop race to consume the same data,
each unaware of the other. Fix. Choose exactly one access mode, either
polling or interrupt-driven, for a given peripheral, and never mix
the two on the same hardware resource.

**Using a busy-wait polling loop for a genuinely long or unpredictable
wait, starving other work that should be running concurrently.**
Symptom. Other tasks in the system become unresponsive or miss their
own timing requirements while the polling loop is running, even though
the polling loop itself eventually succeeds. Cause. Choosing the
pure busy-wait variant for a wait whose real duration is long or
unpredictable, so the CPU is denied to every other task for that
entire, uncertain duration. Fix. Use the cooperative-polling variant
that yields between checks, or switch to an interrupt-driven approach
entirely, per Zephyr's own documented interrupt-driven benefit, for
any wait whose duration is not genuinely short and bounded.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Polling Loop | Interrupt-driven | Cooperative polling with yield |
|---|---|---|---|
| Simplicity of implementation | Strong, per Zephyr's own documented characterization as the most basic method | Weak, needs interrupt registration and a handler | Moderate, needs a yield point but no interrupt setup |
| CPU availability for other work | None, the CPU is fully occupied for the entire wait | Strong, per Zephyr's own documented background-communication benefit | Moderate, other work runs between checks but latency increases |
| Power efficiency | Weak, the CPU cannot idle during the wait | Strong, the CPU can idle until the interrupt fires | Weak to moderate, still no true idle, only cooperative yielding |
| Setup overhead | Lowest, no interrupt controller configuration needed | Highest, needs interrupt priority and handler registration | Low, similar to pure polling plus a yield call |

Reading of the table. A Polling Loop wins specifically when the wait
is genuinely short, bounded, and the system has no other concurrent
work, matching Zephyr's own stated case for polling as the simplest
access method. A genuinely long, unpredictable wait, or a system with
real concurrent work, fits the interrupt-driven alternative better,
per Zephyr's own documented background-communication benefit.

## 13. Related and incompatible patterns

- **Interrupt Service Routine.** The direct alternative this pattern
  trades against, an interrupt notifies the CPU asynchronously rather
  than requiring the CPU to repeatedly ask, and Zephyr's own
  documentation explicitly warns against mixing the two on one
  peripheral, described in dimension 11.
- **Watchdog Timer.** A watchdog is itself often serviced from within
  a loop that also polls other conditions, but the watchdog's own
  purpose, detecting a hang, is distinct from a polling loop's
  purpose, waiting for a specific hardware condition, and a polling
  loop that hangs indefinitely, per the failure mode in dimension 11,
  is exactly the kind of hang a watchdog exists to catch.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to code currently using an interrupt-driven
approach for a wait that is, in practice, short and bounded, and where
the added interrupt-handling complexity is not earning its cost.

1. Confirm the real wait duration is genuinely short and bounded,
   measuring it under real conditions rather than assuming it.
2. Confirm the system genuinely has no other concurrent work that
   would be starved by the CPU being fully occupied during the wait.
3. Replace the interrupt registration, handler, and any shared state
   between the handler and the main code with a direct status-register
   read-and-check loop.
4. Add a bounded timeout to the new loop, per dimension 8, so it can
   never hang indefinitely.

Removing the pattern when it stops earning its place, most relevant
when the wait has genuinely grown long, unpredictable, or the system
now has other concurrent work that the busy-wait loop would starve.

1. Confirm, concretely, that the wait duration or the system's
   concurrency needs have genuinely changed, rather than assuming they
   have.
2. Move to an interrupt-driven approach, per Zephyr's own documented
   background-communication benefit, replacing the loop with an
   interrupt registration and handler.
3. Confirm no other code path still polls the same peripheral, since
   Zephyr's own documentation warns directly against mixing the two
   access modes on one peripheral.

## 15. Testing and verification

Easier because of the pattern.

- A test can drive the underlying status register through a known
  sequence of values and assert the polling loop exits at exactly the
  iteration the condition becomes true, a simple, deterministic check
  since the loop's own code is the entire mechanism, with no
  asynchronous handler to separately verify.
- A test can assert a polling loop with a bounded timeout genuinely
  exits, with a reported failure, when the awaited condition never
  becomes true, directly verifying the fix for the failure mode in
  dimension 11.

Harder because of the pattern.

- Measuring the real CPU time cost of a polling loop under real
  hardware timing needs a test on the actual target, since a host-
  based simulation does not reproduce the real peripheral's actual
  timing.
- Confirming a polling loop does not starve other real concurrent
  work needs a test that can drive that other work at the same time,
  under real timing pressure, not a single-threaded sequence.

Techniques that apply.

- **Deterministic-exit tests.** Drive the status register through a
  known sequence and assert the loop exits at exactly the correct
  iteration.
- **Timeout-bound tests.** Assert a polling loop with a bounded
  timeout genuinely exits with a reported failure when the condition
  never becomes true.
- **No-mixed-access tests.** Confirm no other code path in the system
  polls the same peripheral an interrupt handler also services.
- **Real-hardware timing verification.** Confirm the real CPU time
  cost, and any starvation of other concurrent work, on the actual
  target hardware.

## 16. Observability signals

What to record.

- The real, measured duration of each polling wait, since a rising
  duration directly signals the awaited hardware condition is taking
  longer to become true than expected, or is failing to become true
  at all.
- Whether a polling loop's bounded timeout was ever actually hit,
  since a hit timeout directly points at the exact failure mode from
  dimension 11, the awaited condition never becoming true.

A healthy state. Polling waits complete within their expected,
measured duration, consistently, and a bounded timeout is never
actually hit under real, sustained operation.

A failing state. Polling wait durations trend upward over time, or a
bounded timeout is observed being hit, either pointing directly at a
hardware fault, a disconnected peripheral, or a genuine but
unanticipated condition that never sets the awaited flag.

## 17. Security and privacy implications

**A polling loop with no bounded timeout is a genuine denial-of-
service surface, since an external actor who can prevent the awaited
hardware condition from becoming true, such as by disrupting a
peripheral's signal, can hang the polling code indefinitely.** Because
a pure busy-wait loop with no timeout has no independent exit path
other than the awaited condition becoming true, an external actor with
the ability to influence that condition, directly or indirectly, can
force the loop to spin forever, denying the CPU to every other task in
the system for as long as the actor sustains the disruption. Adding a
bounded timeout, per dimension 8, is a real, necessary part of a
security-conscious polling loop implementation whenever the awaited
condition could plausibly be influenced by an untrusted or external
source, not only a defensive habit for reliability.

## 18. References

1. Zephyr Project. "UART (Universal Asynchronous Receiver-Transmitter)".
   https://docs.zephyrproject.org/latest/hardware/peripherals/uart.html
   Verified 2026-08-21. Source of the polling-mode definition,
   non-blocking read and blocking write behavior, the interrupt-driven
   comparison, and the warning against mixing access modes, used in
   dimensions 1, 2, 3, 4, 9, 10, and 11.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. C models the register-read-and-check loop directly, the
language most embedded polling code is actually written in. Python
shows the same conceptual shape using a minimal, host-testable
simulation, the pattern's deterministic-exit-testable variant from
dimension 15, expressed portably, including the bounded-timeout
variant from dimension 8. Swift shows the same conceptual shape using
a minimal model, analogous to how a native application's own
condition-polling code might be structured. Java, Go, and Rust are
omitted, since the pattern's real home is C and the two languages
chosen already cover its production and its testable-simulation
shapes.

### C

```c
#include <stdio.h>
#include <stdint.h>

#define STATUS_READY 0x01
#define TIMEOUT_ITERATIONS 1000

static uint8_t fake_status_register;

static uint8_t read_status(void) {
    return fake_status_register;
}

static int poll_for_ready(int timeout_iterations) {
    for (int i = 0; i < timeout_iterations; i++) {
        if (read_status() & STATUS_READY) {
            return 0;
        }
    }
    return -1;
}

static void print_result(const char *label, int rc) {
    printf("%s result %d", label, rc);
    putchar(10);
}

int main(void) {
    fake_status_register = 0;
    int rc_before_ready = poll_for_ready(TIMEOUT_ITERATIONS);
    print_result("polled before ready", rc_before_ready);

    fake_status_register = STATUS_READY;
    int rc_after_ready = poll_for_ready(TIMEOUT_ITERATIONS);
    print_result("polled after ready", rc_after_ready);

    return 0;
}
```

### Python

```python
def poll_for_ready(read_status, is_ready, max_iterations: int) -> bool:
    for _ in range(max_iterations):
        if is_ready(read_status()):
            return True
    return False


if __name__ == "__main__":
    status = {'ready': False}

    def read_status():
        return status['ready']

    def is_ready(value):
        return value is True

    ok_before = poll_for_ready(read_status, is_ready, max_iterations=10)
    print("polled before ready, succeeded:", ok_before)

    status['ready'] = True
    ok_after = poll_for_ready(read_status, is_ready, max_iterations=10)
    print("polled after ready, succeeded:", ok_after)
```

### Swift

```swift
func pollForReady(readStatus: () -> Bool, maxIterations: Int) -> Bool {
    for _ in 0..<maxIterations {
        if readStatus() {
            return true
        }
    }
    return false
}

final class FakeStatus {
    var ready = false
}

let status = FakeStatus()

let okBefore = pollForReady(readStatus: { status.ready }, maxIterations: 10)
print("polled before ready, succeeded:", okBefore)

status.ready = true
let okAfter = pollForReady(readStatus: { status.ready }, maxIterations: 10)
print("polled after ready, succeeded:", okAfter)
```
