---
name: Interrupt Service Routine
slug: interrupt-service-routine
family: 28-embedded-hardware
category: Behavioral
aliases: [ISR, Interrupt Handler, FromISR Pattern]
first_described: "FreeRTOS Kernel Book, interrupt management"
maturity: canonical
related: [hardware-abstraction-layer, ring-buffer]
incompatible_with: []
verified: 2026-08-21
---

# Interrupt Service Routine

## 1. Name, aliases, and lineage

The canonical name is Interrupt Service Routine, the pattern where a
short, dedicated function runs in response to a hardware interrupt,
does the minimum work the interrupt genuinely requires immediately,
and defers everything else to code running outside the interrupt
context. The FreeRTOS Kernel Book states the deferred half of this
pattern directly. "Any other processing necessitated by the interrupt
can often be performed in a task, allowing the interrupt service
routine to exit as quickly as is practical. This is called 'deferred
interrupt processing,' because the processing necessitated by the
interrupt is 'deferred' from the ISR to a task."

The alias **ISR** is the standard industry abbreviation, used
constantly across every RTOS and microcontroller vendor's own
documentation. **Interrupt Handler** names the same routine by its
more general, RTOS-agnostic term. **FromISR Pattern** names the
specific API-naming convention FreeRTOS uses to mark which functions
are genuinely safe to call from inside this routine, its own
documentation stating it directly. "Functions intended for use from
ISRs have 'FromISR' appended to their name."

## 2. Problem and context

A hardware interrupt genuinely must be handled with the smallest
possible delay, since the processor stops whatever it was doing the
instant the interrupt fires, and every other pending interrupt is
held off for as long as the current one runs. If the response to an
interrupt performs substantial work directly inside the handler, that
work delays every other time-sensitive event in the system for its
entire duration. An Interrupt Service Routine solves this by doing
only the minimum work the interrupt genuinely requires immediately,
capturing or acknowledging whatever the hardware needs right now, and
deferring the rest to a task, following the FreeRTOS Kernel Book's own
description of the pattern that lets "the interrupt service routine
to exit as quickly as is practical."

## 3. Forces

The pattern balances the following competing pressures.

- **Minimizing interrupt latency for the whole system.** Favored. A
  short interrupt handler that exits quickly holds off other pending
  interrupts for the shortest possible time, directly protecting the
  timing of every other time-sensitive event in the system.
- **Immediate response to time-critical hardware state.** Favored, for
  the narrow slice of work that genuinely cannot wait, capturing a
  hardware register's value before it changes, or acknowledging an
  interrupt flag before the hardware re-fires it.
- **Access to a full, general-purpose API inside the handler.**
  Sacrificed. The FreeRTOS Kernel Book states plainly why. "Many
  FreeRTOS API functions perform actions that are not valid inside an
  ISR. The most notable of these is placing the task that called the
  API function into the Blocked state, if an API function is called
  from an ISR, then it is not being called from a task, so there is no
  calling task that can be placed into the Blocked state." A separate,
  narrower API surface, marked by the FromISR naming convention, is
  the trade this pattern accepts.
- **Implementation simplicity.** Sacrificed, to a degree. Deferring
  work to a task means introducing a hand-off mechanism, a queue, a
  flag, or a semaphore, between the interrupt context and the task
  that will finish the work, real implementation surface a single
  monolithic handler would not need.

## 4. Applicability and non-applicability

Reach for an Interrupt Service Routine, built with genuine interrupt
and task halves, when the following hold.

- The hardware event genuinely needs an immediate response, faster
  than a task's own scheduling latency could provide, to capture
  transient state or acknowledge the interrupt source.
- The full processing the event requires is substantial enough, or
  needs API calls unsafe from interrupt context, that deferring it to
  a task is genuinely necessary rather than merely convenient.
- The system has a real, working hand-off mechanism, a queue or a
  task-notification primitive, to move the deferred work from the
  interrupt context to the task that will complete it.

Do NOT reach for a full interrupt-plus-deferred-task split in these
cases, and the reason matters more than the rule.

- **The interrupt's entire response is genuinely trivial and safe to
  complete inside the handler**, a single register write that
  completes in a few cycles gains nothing from the added complexity of
  a deferred hand-off, and the hand-off mechanism itself would add more
  latency than it saves.
- **The system has no RTOS or task scheduler at all**, a bare-metal
  polling loop with no task context to defer work to has no genuine
  destination for deferred processing, and the whole response
  necessarily lives inside the interrupt handler or the main loop that
  polls for its flag.
- **The deferred work would need to run faster than the scheduler's own
  task-switch latency can provide**, a genuinely hard real-time
  deadline that the scheduling overhead of a deferred task cannot meet
  needs the work done directly in the interrupt context instead,
  accepting the API restrictions that come with it.

## 5. Structure

An Interrupt Service Routine, built with the deferred-processing
variant, has three structural parts.

- **The interrupt context**, the short routine that actually runs when
  the hardware interrupt fires, doing only the minimum immediate work
  and calling only the narrow, ISR-safe API surface.
- **The hand-off mechanism**, a queue, flag, or task-notification
  primitive the interrupt context uses to signal that deferred work is
  needed, following the FreeRTOS-documented pattern of a `FromISR`
  variant of the normal signaling API.
- **The deferred task**, the ordinary task-context code that performs
  the substantial remainder of the processing, with the FreeRTOS
  Kernel Book stating directly that deferring lets that task use the
  full API and "be prioritized relative to other tasks in the
  application."

## 6. ASCII structure diagram

```
  +----------------------------------------------------------+
  |  Hardware interrupt fires                                    |
  +----------------------------------------------------------+
                          |
  +----------------------------------------------------------+
  |  Interrupt Service Routine, interrupt context                 |
  |    minimum immediate work only                                |
  |    calls only FromISR-suffixed, ISR-safe API functions          |
  |    signals the hand-off mechanism, then returns quickly         |
  +----------------------------------------------------------+
                          |
  +----------------------------------------------------------+
  |  Hand-off mechanism, a queue or task notification              |
  +----------------------------------------------------------+
                          |
  +----------------------------------------------------------+
  |  Deferred task, ordinary task context                          |
  |    full API available, can block, can be prioritized             |
  |    completes the substantial remainder of the processing        |
  +----------------------------------------------------------+
```

## 7. Dynamics

The trace below shows a hardware interrupt handled with the deferred
pattern.

```
Hardware interrupt fires

the processor immediately jumps to the interrupt service routine
   |-- the handler captures or acknowledges whatever hardware state
       genuinely cannot wait
   |-- the handler calls a FromISR-suffixed hand-off function to
       signal the deferred task, following the FreeRTOS-documented
       naming convention for ISR-safe API calls
   |-- the handler returns immediately

Scheduler resumes normal operation

the interrupt context ends, and the scheduler resumes whatever task
was running, or, if the deferred task now has higher priority, switches
to it
   |-- the deferred task, once it runs, reads the signal or the queued
       data the interrupt context left behind
   |-- the deferred task performs the substantial remainder of the
       processing, with the full API available, since it is running
       in task context, not interrupt context
```

## 8. Implementation variants

**Deferred processing via a queue.** The interrupt context pushes a
small payload, a captured value or an event identifier, onto a queue
using its FromISR variant, and the deferred task blocks reading from
that queue, waking whenever new data arrives.

**Deferred processing via a task notification or a binary semaphore.**
The interrupt context signals a lightweight notification rather than
queuing data, and the deferred task, once woken, reads whatever
hardware state it needs directly, a lower-overhead hand-off than a
full queue when no payload genuinely needs to travel with the signal.

**Direct handling with no deferral.** For a genuinely trivial response,
the entire handling happens inside the interrupt context itself, with
no hand-off mechanism at all, the correct choice per the
non-applicability guidance in dimension 4.

**Polling-loop fallback.** On a system with no RTOS or task scheduler,
the interrupt context sets a flag, and a main polling loop checks that
flag and performs the deferred work synchronously, the bare-metal
equivalent of the deferred-task variant.

## 9. Known production uses

**The FreeRTOS Kernel Book, defining the naming convention and the
deferred pattern.** The book states the API restriction and its
naming solution directly. "Many FreeRTOS API functions perform actions
that are not valid inside an ISR. The most notable of these is placing
the task that called the API function into the Blocked state," and
"functions intended for use from ISRs have 'FromISR' appended to their
name." FreeRTOS, "FreeRTOS-Kernel-Book, Chapter 7, Interrupt
Management,"
https://github.com/FreeRTOS/FreeRTOS-Kernel-Book/blob/main/ch07.md,
verified 2026-08-21.

**The same source, on why deferring processing to a task is valuable.**
"Any other processing necessitated by the interrupt can often be
performed in a task, allowing the interrupt service routine to exit as
quickly as is practical. This is called 'deferred interrupt
processing.'" FreeRTOS, "FreeRTOS-Kernel-Book, Chapter 7, Interrupt
Management,"
https://github.com/FreeRTOS/FreeRTOS-Kernel-Book/blob/main/ch07.md,
verified 2026-08-21.

## 10. Consequences

Positive.

- A short interrupt handler that exits quickly holds off other pending
  interrupts for the shortest possible time, directly protecting the
  timing of every other time-sensitive event in the system.
- Deferring the substantial part of the work to a task lets that work
  use the full, general-purpose API and be prioritized against the
  rest of the application's tasks, capabilities unavailable directly
  inside the interrupt context.
- The FromISR naming convention makes it immediately visible, by
  reading the function name at the call site, whether a given API call
  is genuinely safe inside an interrupt context.

Negative.

- Building the deferred half of the pattern adds real implementation
  surface, a queue or notification mechanism the system would not need
  if the entire response fit safely inside the interrupt handler.
- A developer who calls a non-FromISR API function from inside an
  interrupt context by mistake introduces a defect that can behave
  unpredictably, since the function's own assumption of a calling task
  to be blocked does not hold.
- For work that is genuinely trivial, the deferred variant's hand-off
  mechanism adds more latency and complexity than handling the
  response directly inside the interrupt context would have.

## 11. Failure modes and misuse

**Calling a non-FromISR API function from inside an interrupt context.**
Symptom. The system behaves unpredictably, crashes, or corrupts state
after handling a specific interrupt, in a way that is hard to
reproduce because it depends on the exact state the scheduler was in
when the interrupt fired. Cause. The FreeRTOS Kernel Book names the
root cause directly, calling a function that can place a task into the
Blocked state when there is no genuine calling task to block, because
the code is running in interrupt context rather than task context.
Fix. Use only the FromISR-suffixed variant of any API function called
from inside an interrupt context, and treat a non-FromISR call inside
a handler as a defect to fix immediately, not a stylistic choice.

**Doing substantial, unbounded work directly inside the interrupt
context instead of deferring it.** Symptom. Other, unrelated
interrupts in the system experience unpredictable, sometimes severe
delay, and a real-time deadline elsewhere in the system is missed,
even though the code that misses the deadline is entirely unrelated to
the interrupt actually causing the delay. Cause. An interrupt handler
performing work whose duration is not bounded and predictable, holding
off every other pending interrupt for the full duration of that work.
Fix. Move any work that is not genuinely time-critical and bounded out
of the interrupt context, deferring it to a task using the hand-off
mechanism from dimension 8, following the FreeRTOS-documented deferred
processing pattern.

**Building a hand-off mechanism between the interrupt context and the
deferred task with no genuine data-race protection.** Symptom. The
deferred task occasionally reads a corrupted or torn value that the
interrupt context was in the middle of writing when the interrupt
fired mid-write, producing an intermittent, hard-to-reproduce bug.
Cause. Sharing state between the interrupt context and task context
through a plain variable with no atomic access or proper queuing
mechanism, rather than using the RTOS's own FromISR-safe primitives
built specifically to make this hand-off safe. Fix. Use the RTOS's own
queue, semaphore, or notification primitive for the hand-off, rather
than a raw shared variable, since these primitives are specifically
built to make the interrupt-to-task hand-off safe.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Interrupt Service Routine, deferred variant | Direct handling, no deferral | Pure polling loop, no interrupts at all |
|---|---|---|---|
| Minimizing interrupt latency for the whole system | Strong, the handler itself stays short | Weak to strong, depends entirely on how much work the handler does directly | Not applicable, there is no interrupt latency to minimize |
| Immediate response to time-critical hardware state | Strong, the immediate part still runs in the interrupt context | Strong, the entire response is immediate | Weak, response time depends entirely on how often the polling loop runs |
| Access to a full, general-purpose API for the response | Strong, for the deferred half running in task context | Weak, the entire response is constrained by the narrower ISR-safe API | Strong, the entire response runs in ordinary code |
| Implementation simplicity | Moderate, needs a real hand-off mechanism | Strong for a genuinely trivial response | Strong for the loop itself, though it costs power and responsiveness |

Reading of the table. The deferred variant of an Interrupt Service
Routine wins specifically when the full response is substantial enough
to need the general-purpose API, but at least part of the response
genuinely needs an interrupt-speed reaction. Direct handling remains
correct for the genuinely trivial case, and a pure polling loop remains
correct on a system with no interrupt-driven hardware or scheduler at
all.

## 13. Related and incompatible patterns

- **Hardware Abstraction Layer.** An interrupt service routine
  frequently interacts with hardware through the abstraction layer,
  and dimension 4 of that pattern's own entry names exactly this case,
  where the abstraction layer's real overhead most needs to be
  measured against a routine's actual timing budget.
- **Ring Buffer.** A ring buffer is a common choice for the hand-off
  mechanism between an interrupt context and its deferred task,
  specifically because a correctly built ring buffer can be written
  from an interrupt context and read from a task context without
  needing a blocking lock.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a monolithic interrupt handler currently doing
all its work directly inside the interrupt context.

1. Identify which part of the handler's work is genuinely
   time-critical and must happen immediately, versus which part could
   safely run later, in task context.
2. Choose a hand-off mechanism, a queue or a task notification, that
   fits the amount and shape of data that genuinely needs to travel
   from the interrupt context to the deferred task.
3. Move the non-time-critical work into a new task, reading from the
   chosen hand-off mechanism.
4. Confirm every API call remaining inside the interrupt context uses
   its ISR-safe, FromISR-suffixed variant, and confirm the handler's
   measured execution time has genuinely shrunk.

Removing the pattern when it stops earning its place, most relevant
when a deferred task's real work has shrunk to the point that the
hand-off mechanism itself costs more than it saves.

1. Confirm, concretely, that the deferred work is now genuinely
   trivial and safe to run directly inside the interrupt context,
   rather than assuming so without measuring its real execution time.
2. Fold the deferred task's work back into the interrupt context
   directly, removing the hand-off mechanism and the separate task.
3. Confirm the handler's measured execution time still fits the
   system's real interrupt-latency budget after the fold, since a
   response that was genuinely trivial when deferred processing was
   introduced may have grown since.

## 15. Testing and verification

Easier because of the pattern.

- The deferred task's logic can be unit tested as ordinary task-context
  code, independent of any real interrupt actually firing, since it
  reads from the hand-off mechanism the same way regardless of what
  triggered the data to be there.
- Because the interrupt context itself is kept deliberately small, it
  is a small, reviewable surface to verify for correct FromISR API
  usage, rather than a large handler mixing time-critical and ordinary
  logic together.

Harder because of the pattern.

- Verifying the interrupt context's real execution time genuinely fits
  the system's interrupt-latency budget needs a measurement on the
  real target hardware, since a host-based simulation does not
  reproduce genuine interrupt timing.
- Confirming the hand-off mechanism is genuinely free of data races
  needs a test that can reliably trigger the interrupt at the specific
  moments most likely to expose a race, a category of test that is
  hard to construct reliably without real hardware-in-the-loop support.

Techniques that apply.

- **Interrupt-context timing measurement.** Measure the real execution
  time of the interrupt handler on the actual target hardware,
  confirming it fits the system's genuine interrupt-latency budget.
- **Deferred-task unit tests.** Test the deferred task's logic directly
  against a range of simulated hand-off payloads, independent of any
  real interrupt actually firing.
- **FromISR API usage review.** Confirm, by reading the interrupt
  context's code, that every API call inside it uses its ISR-safe
  variant, treating any non-FromISR call inside a handler as a defect.
- **Hardware-in-the-loop race testing.** Trigger the real interrupt
  under real timing pressure against the deferred task's real
  execution, verifying the hand-off mechanism holds up under genuine
  concurrent access.

## 16. Observability signals

What to record.

- The real, measured execution time of the interrupt context itself,
  since this signal directly answers whether the handler still fits
  the system's genuine interrupt-latency budget as the firmware
  evolves.
- The depth or backlog of the hand-off mechanism, a queue's fill level
  or a notification's pending count, since a persistently full or
  growing hand-off signals the deferred task cannot keep up with the
  rate interrupts are arriving.

A healthy state. The interrupt context's measured execution time stays
comfortably within the system's real interrupt-latency budget, and the
hand-off mechanism's backlog stays consistently low, showing the
deferred task keeps pace with the interrupt's actual arrival rate.

A failing state. The interrupt context's measured execution time grows
to compete with, or exceed, its latency budget, pointing at work that
needs to move from the interrupt context into the deferred task, or
the hand-off mechanism's backlog grows persistently, pointing at a
deferred task that cannot keep up and needs either a higher priority
or a faster implementation.

## 17. Security and privacy implications

**An interrupt service routine that reads externally controlled data,
from a communications peripheral or a sensor an external party can
influence, must validate that data with the same discipline any other
external input receives, and must not let a malformed or oversized
payload overflow the hand-off mechanism's buffer.** If the interrupt
context copies an externally supplied payload into a fixed-size queue
or buffer without checking its real length against that buffer's
actual capacity, a sufficiently large or malformed input can overflow
memory the interrupt context controls, a genuine, exploitable defect
rather than a purely theoretical concern for any embedded system that
receives data from an external source such as a network or serial
interface. Validating the length and shape of any externally supplied
data before it is copied into the hand-off mechanism is a real,
necessary part of the interrupt context's own implementation, not an
optional hardening step.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. C models the interrupt-context-plus-deferred-task shape
directly, the language embedded firmware and RTOS interrupt handlers
are actually written in, using a small ring buffer as the hand-off
mechanism. Python shows the same conceptual shape using a minimal,
host-testable simulation of the deferred-task logic, the pattern's
unit-testable half from dimension 15, expressed portably. Swift shows
the same conceptual shape using a minimal model, analogous to how a
native application's own event-driven code might separate a fast,
immediate handler from a deferred, fuller processing step. Java, Go,
and Rust are omitted, since the pattern's real home is C and the two
languages chosen already cover its production and its testable-logic
shapes.

### C

```c
#include <stdio.h>
#include <stdint.h>

#define QUEUE_CAPACITY 8

typedef struct {
    uint8_t values[QUEUE_CAPACITY];
    int head;
    int tail;
    int count;
} isr_queue_t;

static isr_queue_t deferred_queue = {{0}, 0, 0, 0};

static int queue_push_from_isr(isr_queue_t *q, uint8_t value) {
    if (q->count >= QUEUE_CAPACITY) {
        return 0;
    }
    q->values[q->tail] = value;
    q->tail = (q->tail + 1) % QUEUE_CAPACITY;
    q->count += 1;
    return 1;
}

static int queue_pop(isr_queue_t *q, uint8_t *out) {
    if (q->count == 0) {
        return 0;
    }
    *out = q->values[q->head];
    q->head = (q->head + 1) % QUEUE_CAPACITY;
    q->count -= 1;
    return 1;
}

static void adc_interrupt_handler(uint8_t captured_value) {
    if (!queue_push_from_isr(&deferred_queue, captured_value)) {
        return;
    }
}

static void deferred_task_step(void) {
    uint8_t value;
    while (queue_pop(&deferred_queue, &value)) {
        printf("deferred task processing captured value %u", (unsigned)value);
        putchar(10);
    }
}

int main(void) {
    adc_interrupt_handler(42);
    adc_interrupt_handler(17);
    deferred_task_step();
    return 0;
}
```

### Python

```python
from collections import deque
from dataclasses import dataclass, field


@dataclass
class IsrQueue:
    capacity: int
    values: deque = field(default_factory=deque)

    def push_from_isr(self, value: int) -> bool:
        if len(self.values) >= self.capacity:
            return False
        self.values.append(value)
        return True

    def pop(self) -> int | None:
        if not self.values:
            return None
        return self.values.popleft()


def adc_interrupt_handler(queue: IsrQueue, captured_value: int) -> None:
    queue.push_from_isr(captured_value)


def deferred_task_step(queue: IsrQueue) -> None:
    value = queue.pop()
    while value is not None:
        print("deferred task processing captured value " + str(value))
        value = queue.pop()


if __name__ == "__main__":
    q = IsrQueue(capacity=8)
    adc_interrupt_handler(q, 42)
    adc_interrupt_handler(q, 17)
    deferred_task_step(q)
```

### Swift

```swift
final class IsrQueue {
    private var values: [Int] = []
    private let capacity: Int

    init(capacity: Int) {
        self.capacity = capacity
    }

    func pushFromIsr(_ value: Int) -> Bool {
        guard values.count < capacity else {
            return false
        }
        values.append(value)
        return true
    }

    func pop() -> Int? {
        guard !values.isEmpty else {
            return nil
        }
        return values.removeFirst()
    }
}

func adcInterruptHandler(_ queue: IsrQueue, capturedValue: Int) {
    _ = queue.pushFromIsr(capturedValue)
}

func deferredTaskStep(_ queue: IsrQueue) {
    while let value = queue.pop() {
        print("deferred task processing captured value " + String(value))
    }
}

let queue = IsrQueue(capacity: 8)
adcInterruptHandler(queue, capturedValue: 42)
adcInterruptHandler(queue, capturedValue: 17)
deferredTaskStep(queue)
```

## 18. References

1. FreeRTOS. "FreeRTOS-Kernel-Book, Chapter 7, Interrupt Management".
   https://github.com/FreeRTOS/FreeRTOS-Kernel-Book/blob/main/ch07.md
   Verified 2026-08-21. Source of the FromISR naming convention, the
   ISR API restriction, and the deferred interrupt processing quotes
   used in dimensions 1, 2, 3, 5, 9, and 10.
