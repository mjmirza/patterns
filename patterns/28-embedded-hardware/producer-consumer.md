---
name: Producer-Consumer (Embedded)
slug: producer-consumer
family: 28-embedded-hardware
category: Structural
aliases: [ISR-Safe Message Queue, Non-Blocking Producer Handoff, Interrupt-to-Task Data Passing]
first_described: "Zephyr Project documentation, message queues and pipes"
maturity: canonical
related: [ring-buffer, interrupt-service-routine]
incompatible_with: []
verified: 2026-08-21
---

# Producer-Consumer (Embedded)

## 1. Name, aliases, and lineage

The canonical name is Producer-Consumer (Embedded), the embedded-
specific constraint on the general Producer-Consumer pattern where the
producer side, most often an interrupt handler, can never block or
wait, unlike the general pattern's producer and consumer threads,
which may both wait on a shared buffer. This is a genuinely distinct
concern from the general concurrency Producer-Consumer entry, which
covers thread-to-thread handoff using semaphores and condition
variables that both sides may block on. Zephyr's own documentation
states the embedded-specific constraint directly, "the kernel does
allow an ISR to receive an item from a message queue, however the ISR
must not attempt to wait if the message queue is empty," and the same
non-blocking discipline applies equally strictly to an ISR acting as
the producer.

The alias **ISR-Safe Message Queue** names the pattern by the
mechanism most embedded kernels provide for it. **Non-Blocking
Producer Handoff** names the pattern by its defining constraint.
**Interrupt-to-Task Data Passing** names the pattern by its most common
real shape, an interrupt handler producing data that a lower-priority
task later consumes.

## 2. Problem and context

An interrupt handler frequently needs to hand data off to code that
runs later, at task or thread level, such as a received UART byte, a
completed ADC conversion, or a network packet, but an interrupt
handler cannot use the blocking synchronization primitives, mutexes,
semaphores that wait, or condition variables, that the general
Producer-Consumer pattern relies on, since blocking inside an
interrupt context would stall the entire system. Producer-Consumer
(Embedded) solves this by using a queue whose producer-side operation
is always non-blocking, immediately succeeding or immediately failing,
never waiting, so an interrupt handler can safely act as the producer.
Zephyr's own documentation shows this directly, a producer using
`k_msgq_put(&my_msgq, &data, K_NO_WAIT)` to send without blocking, "K_NO_WAIT"
being exactly the non-blocking discipline an ISR-safe producer
requires.

## 3. Forces

The pattern balances the following competing pressures.

- **Safety inside an interrupt handler.** Favored. Zephyr's own
  documentation states the constraint directly, an ISR "must not
  attempt to wait if the message queue is empty," and the same
  applies symmetrically to production, so a correctly-built ISR-safe
  producer-consumer pair can never stall the interrupt handler.
- **Bounded, predictable interrupt latency.** Favored. Because the
  producer-side operation is always non-blocking, the interrupt
  handler's own execution time is bounded and predictable, never
  extended by waiting on the consumer.
- **Guaranteed delivery of every produced item.** Sacrificed. Zephyr's
  own documentation names this trade-off directly, "if the message
  queue fills up because the consumers can't keep up, the producing
  thread throws away all existing data so the newer data can be
  saved," meaning a slow consumer can genuinely cause data loss rather
  than the producer ever blocking to wait for space.
- **Structured, discrete items versus a continuous stream.** A real
  choice, not strictly a trade-off. Zephyr's own documentation
  distinguishes the two mechanisms directly, a message queue passes
  discrete, fixed-size items, while a pipe is "a kernel object that
  allows a thread to send a byte stream to another thread," suited to
  continuous data rather than discrete messages.

## 4. Applicability and non-applicability

Reach for Producer-Consumer (Embedded) when the following hold.

- The producer genuinely runs in interrupt context, or in any other
  context that genuinely cannot block, so a blocking synchronization
  primitive is genuinely unsafe to use on the producer side.
- The consumer genuinely runs at task or thread level, where waiting
  for new data is genuinely safe, allowing an asymmetric design, a
  never-blocking producer paired with a blocking-capable consumer.
- The real data being passed is genuinely either fixed-size discrete
  items, fitting a message-queue mechanism, or a continuous byte
  stream, fitting a pipe mechanism, per Zephyr's own documented
  distinction between the two.

Do NOT reach for Producer-Consumer (Embedded) in these cases, and the
reason matters more than the rule.

- **Both the producer and the consumer genuinely run at task level,
  where blocking is genuinely safe on both sides**, the general
  Producer-Consumer pattern's blocking semaphore or condition-variable
  approach, covered in that entry, fits this case without the
  embedded-specific non-blocking constraint adding real, unnecessary
  restriction.
- **Losing data under a slow consumer is genuinely unacceptable, with
  no way to size the queue or throttle production to prevent it**, per
  Zephyr's own documented data-loss trade-off, a design that genuinely
  cannot tolerate any loss needs a mechanism with real backpressure on
  the producer, which by definition cannot exist if the producer
  genuinely cannot block, and needs a different architecture, such as
  a lower-priority producer thread that genuinely can block.
- **The real data being passed is neither a fixed-size discrete item
  nor a genuine continuous byte stream**, such as a variable-length
  structured message with no clean fit to either mechanism, needing a
  different, purpose-built data-passing design instead.

## 5. Structure

Producer-Consumer (Embedded) has three structural parts.

- **The producer**, most often an interrupt handler, that writes data
  using a non-blocking operation that either succeeds immediately or
  fails immediately, never waiting.
- **The queue**, either a message queue for fixed-size discrete items
  or a pipe for a continuous byte stream, per Zephyr's own documented
  distinction, sized to hold enough data for the real timing gap
  between production and consumption.
- **The consumer**, running at task or thread level, that reads data
  using an operation that may safely wait, since blocking is genuinely
  safe outside an interrupt context.

## 6. ASCII structure diagram

```
  interrupt context               task context
  +--------------+                +--------------+
  |  producer, ISR |  non-blocking  |  consumer, task |
  |  never waits     |  -----------> |  may safely wait   |
  +--------------+     put         +--------------+
                                            ^
                                            |
                                     the queue itself,
                                     fixed-size items or
                                     a byte stream
```

## 7. Dynamics

The trace below shows one complete produce-and-consume cycle.

```
The producer, running in interrupt context, has data ready

it attempts a non-blocking put into the queue, per Zephyr's own
documented `K_NO_WAIT` discipline
   |-- if the queue has space, the put succeeds immediately, and the
       interrupt handler continues and returns quickly
   |-- if the queue is genuinely full, per Zephyr's own documented
       trade-off, the producer either drops the new item, or, in some
       implementations, purges old data to make room for the new item,
       but it never waits

The consumer, running at task level, reads from the queue

because the consumer genuinely runs outside interrupt context, it may
safely block, waiting for an item to become available
   |-- once an item is available, the consumer reads it and processes
       it, taking however long the real processing genuinely requires,
       with no interrupt-latency constraint on the consumer side
```

## 8. Implementation variants

**Message queue, discrete fixed-size items.** The canonical form for
structured data, Zephyr's own documented mechanism, where each put and
get transfers one complete, fixed-size item.

**Pipe, continuous byte stream.** Zephyr's own documentation describes
this variant directly, "a kernel object that allows a thread to send a
byte stream to another thread," suited to continuous data such as a
UART receive stream, where the natural unit is a stream of bytes
rather than discrete messages.

**Purge-on-full, rather than drop-newest.** Rather than simply
rejecting a new item when the queue is full, Zephyr's own documented
example instead purges the existing, older data so the newer data can
be saved, a real policy choice trading old data for new rather than
the reverse.

## 9. Known production uses

**Zephyr's own documentation, defining the ISR non-blocking constraint
and the full-queue data-loss trade-off for message queues.** Zephyr
states this directly. "The kernel does allow an ISR to receive an item
from a message queue, however the ISR must not attempt to wait if the
message queue is empty." "If the message queue fills up because the
consumers can't keep up, the producing thread throws away all existing
data so the newer data can be saved." Zephyr Project, "Message
Queues,"
https://docs.zephyrproject.org/latest/kernel/services/data_passing/message_queues.html,
verified 2026-08-21.

**Zephyr's own documentation, on the pipe variant for a continuous
byte stream rather than discrete items.** Zephyr states this directly.
"A pipe is a kernel object that allows a thread to send a byte stream
to another thread." Zephyr Project, "Pipes,"
https://docs.zephyrproject.org/latest/kernel/services/data_passing/pipes.html,
verified 2026-08-21.

## 10. Consequences

Positive.

- The producer, most often an interrupt handler, can never stall the
  system waiting for space, per Zephyr's own documented non-blocking
  discipline, keeping interrupt latency bounded and predictable.
- The consumer can safely use a blocking wait, since it genuinely runs
  outside interrupt context, simplifying the consumer's own code
  compared to having to poll.
- The message-queue and pipe variants, per Zephyr's own documented
  distinction, fit either discrete structured data or a continuous
  byte stream cleanly, without forcing one shape onto the other.

Negative.

- A slow consumer can genuinely cause data loss, per Zephyr's own
  documented full-queue trade-off, since the producer, by design,
  never blocks to wait for space.
- The queue's real size must be chosen carefully against the real
  timing gap between production and consumption, since an undersized
  queue causes real data loss under real, sustained load.
- The consumer must genuinely tolerate the possibility of lost or
  purged data, a real design constraint that a use case demanding
  guaranteed delivery cannot accept under this pattern.

## 11. Failure modes and misuse

**Using a blocking wait on the producer side inside an interrupt
handler, expecting it to behave the way it would at task level.**
Symptom. The system hangs or misses real, time-critical interrupts
entirely, because the interrupt handler is stuck waiting for queue
space that a lower-priority task, itself starved by the stalled
interrupt, can never free. Cause. Treating the producer side as if it
were a normal task-level producer that may safely block, rather than
genuinely respecting Zephyr's own documented non-blocking constraint
for ISR context. Fix. Always use the non-blocking put operation, per
Zephyr's own documented `K_NO_WAIT` discipline, on any producer that
genuinely runs in interrupt context, and never a blocking wait, no
matter how briefly it seems it would need to wait.

**Sizing the queue too small for the real timing gap between
production and consumption, causing silent, unexpected data loss under
real, sustained load.** Symptom. Data is genuinely lost during real
operation, even though the system appeared to work correctly during
light or typical testing, because typical testing rarely exercises the
genuine worst-case timing gap between when the interrupt produces data
and when the consumer task actually gets scheduled to consume it.
Cause. Choosing a queue size without measuring the real, worst-case
gap between production and consumption under real system load, so the
queue fills and starts dropping or purging data exactly when the
system is under real, sustained stress. Fix. Measure the real,
worst-case timing gap between production and consumption under real,
representative load, and size the queue to genuinely tolerate that
gap, rather than an assumed or typical-case gap.

**Assuming the general, task-level Producer-Consumer pattern's
blocking semantics apply here, when the actual producer is an
interrupt handler.** Symptom. Code that would be entirely correct for
the general concurrency Producer-Consumer pattern, using a blocking
semaphore-based handoff, is copied into an embedded context where the
producer genuinely runs in interrupt context, and the system misbehaves
in exactly the way the first failure mode describes. Cause. Not
recognizing that this pattern's producer-side non-blocking constraint
is a genuinely different requirement from the general pattern's
symmetric, both-sides-may-block design. Fix. Explicitly confirm which
context, interrupt or task, each side of a producer-consumer handoff
genuinely runs in before choosing an implementation, and use this
pattern's non-blocking-producer discipline whenever the producer
genuinely runs in interrupt context.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Producer-Consumer (Embedded) | General Producer-Consumer (task-level) | Polling Loop |
|---|---|---|---|
| Safety inside an interrupt handler | Strong, per Zephyr's own documented non-blocking constraint | Weak, a blocking wait is genuinely unsafe in interrupt context | Strong, a polling loop never blocks either, but is less structured for data handoff |
| Bounded, predictable interrupt latency | Strong, the producer-side operation is always non-blocking | Not applicable, both sides may block, per that entry's own design | Weak, a polling loop's own duration is itself unbounded without a timeout |
| Guaranteed delivery of every produced item | Weak, per Zephyr's own documented full-queue data-loss trade-off | Strong, both sides can block, so the producer can genuinely wait for space | Not applicable, polling is not a data-handoff mechanism on its own |
| Structural fit for discrete items or a stream | Strong, per Zephyr's own documented message-queue and pipe distinction | Moderate, depends on the specific blocking primitive chosen | Weak, polling alone carries no data-passing structure |

Reading of the table. Producer-Consumer (Embedded) wins specifically
when the producer genuinely runs in interrupt context, where the
general, task-level Producer-Consumer pattern's blocking design is
genuinely unsafe to use. When both sides genuinely run at task level,
the general pattern's guaranteed-delivery blocking design fits better.

## 13. Related and incompatible patterns

- **Ring Buffer.** The mechanism most message-queue implementations
  use internally, and the pattern this entry's dimension 9 citation
  builds directly on, a fixed-capacity, lock-free structure a single
  interrupt-context producer and a single task-context consumer can
  share with no blocking on either side.
- **Interrupt Service Routine.** The producer side of this pattern is,
  in its most common real shape, an interrupt service routine itself,
  so the non-blocking discipline this entry describes is a direct,
  necessary consequence of the constraints that entry already
  describes for interrupt context.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to code currently using a blocking, task-level
producer-consumer handoff where the real producer has migrated to
interrupt context.

1. Confirm the producer genuinely now runs in interrupt context, and
   confirm the consumer genuinely can remain at task level, where
   blocking is genuinely safe.
2. Choose the message-queue or pipe variant based on whether the real
   data is genuinely discrete, fixed-size items or a genuine
   continuous byte stream, per Zephyr's own documented distinction.
3. Replace the blocking producer-side operation with the non-blocking
   equivalent, per Zephyr's own documented `K_NO_WAIT` discipline,
   confirming no code path on the producer side can still block.
4. Size the queue against the real, measured worst-case timing gap
   between production and consumption under real, representative
   load, before deploying.

Removing the pattern when it stops earning its place, most relevant
when the producer has genuinely moved out of interrupt context
entirely, to a task that can safely block.

1. Confirm, concretely, that the producer genuinely no longer runs in
   interrupt context, rather than assuming it does not.
2. Move to the general, task-level Producer-Consumer pattern's
   blocking design, which can offer genuine guaranteed delivery this
   pattern's non-blocking constraint cannot.
3. Confirm no remaining code path still assumes the producer can never
   block, since the general pattern's design intentionally allows it
   to.

## 15. Testing and verification

Easier because of the pattern.

- A test can assert the producer-side operation genuinely never blocks
  under any queue state, a simple, deterministic check since the
  non-blocking discipline is an unconditional property of the
  operation itself, not a runtime-dependent behavior.
- A test can drive the queue to genuinely full and assert the real,
  intended full-queue policy, per Zephyr's own documented purge-or-
  drop trade-off, actually fires as designed.

Harder because of the pattern.

- Confirming the queue's real size is genuinely sufficient for the
  real, worst-case timing gap between production and consumption needs
  measurement under real, representative system load, not an assumed
  typical-case gap.
- Verifying the producer's real, non-blocking behavior under genuine
  interrupt-context timing pressure needs a test on real target
  hardware, since a host-based simulation does not reproduce the real
  interrupt latency and preemption behavior.

Techniques that apply.

- **Non-blocking assertion tests.** Assert the producer-side operation
  genuinely returns immediately, under every queue state, full or
  otherwise.
- **Full-queue policy tests.** Drive the queue to genuinely full and
  assert the intended drop-or-purge policy actually fires as designed.
- **Worst-case timing-gap measurement.** Measure the real, worst-case
  gap between production and consumption under real, representative
  load, and confirm the queue size genuinely tolerates it.
- **Real-hardware interrupt-context verification.** Confirm the
  producer's real, non-blocking behavior on the actual target
  hardware, under genuine interrupt timing pressure.

## 16. Observability signals

What to record.

- The real count of dropped or purged items, since a rising count
  directly signals the queue is genuinely undersized for the real,
  current timing gap between production and consumption.
- The queue's real, measured occupancy over time, since a sustained,
  rising occupancy directly signals the consumer is genuinely falling
  behind the real producer rate.

A healthy state. Dropped or purged items stay at, or very near, zero
under real, sustained operation, and queue occupancy stays comfortably
below capacity.

A failing state. Dropped or purged items rise under real, sustained
operation, or queue occupancy trends toward full capacity, either
directly signaling the queue is genuinely undersized, or the consumer
is genuinely falling behind the real producer rate.

## 17. Security and privacy implications

**An external actor who can drive the producer to genuinely exceed the
consumer's real processing rate can force the queue's full-queue
policy to discard or purge legitimate data, a real denial-of-service
effect against whatever the consumer was supposed to process.**
Because Zephyr's own documented full-queue policy exists specifically
because the producer can never block to wait for space, an external
actor with the ability to influence the real production rate, such as
by flooding a UART or network interface with traffic that triggers the
producer's interrupt at a genuinely much higher rate, can deliberately
cause legitimate data to be dropped or purged, without ever needing to
compromise the system directly. Rate-limiting or filtering untrusted
input at a layer before it reaches the producer, and sizing the queue
with a real, adversarial worst-case rate in mind rather than only a
typical or expected rate, are real, necessary parts of a security-
conscious implementation of this pattern whenever the producer's real
trigger rate can be influenced by an untrusted or external source.

## 18. References

1. Zephyr Project. "Message Queues".
   https://docs.zephyrproject.org/latest/kernel/services/data_passing/message_queues.html
   Verified 2026-08-21. Source of the ISR non-blocking constraint and
   the full-queue data-loss trade-off quotes used in dimensions 1, 2,
   3, 7, 9, 10, and 11.
2. Zephyr Project. "Pipes".
   https://docs.zephyrproject.org/latest/kernel/services/data_passing/pipes.html
   Verified 2026-08-21. Source of the byte-stream pipe variant quote
   used in dimensions 3, 4, 8, and 9.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. C models the ISR-safe, non-blocking producer shape directly, the
language most embedded interrupt handlers are actually written in.
Python shows the same conceptual shape using a minimal, host-testable
simulation, the pattern's non-blocking-assertion-testable variant from
dimension 15, expressed portably. Swift shows the same conceptual
shape using a minimal model, analogous to how a native application's
own interrupt-context-to-task data handoff might be structured. Java,
Go, and Rust are omitted, since the pattern's real home is C and the
two languages chosen already cover its production and its
testable-simulation shapes.

### C

```c
#include <stdio.h>

#define QUEUE_CAPACITY 4

typedef struct {
    int items[QUEUE_CAPACITY];
    int count;
    int dropped;
} isr_queue_t;

static int queue_put_no_wait(isr_queue_t *q, int value) {
    if (q->count >= QUEUE_CAPACITY) {
        q->dropped++;
        return -1;
    }
    q->items[q->count] = value;
    q->count++;
    return 0;
}

static int queue_get(isr_queue_t *q, int *out) {
    if (q->count == 0) {
        return -1;
    }
    *out = q->items[0];
    for (int i = 1; i < q->count; i++) {
        q->items[i - 1] = q->items[i];
    }
    q->count--;
    return 0;
}

int main(void) {
    isr_queue_t queue = { .count = 0, .dropped = 0 };

    for (int i = 0; i < 6; i++) {
        int rc = queue_put_no_wait(&queue, i);
        printf("produce %d rc %d dropped %d", i, rc, queue.dropped);
        putchar(10);
    }

    int value;
    while (queue_get(&queue, &value) == 0) {
        printf("consume %d", value);
        putchar(10);
    }

    return 0;
}
```

### Python

```python
from collections import deque


class ISRQueue:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items = deque()
        self.dropped = 0

    def put_no_wait(self, value: int) -> bool:
        if len(self.items) >= self.capacity:
            self.dropped += 1
            return False
        self.items.append(value)
        return True

    def get(self) -> int | None:
        if not self.items:
            return None
        return self.items.popleft()


if __name__ == "__main__":
    queue = ISRQueue(capacity=4)

    for i in range(6):
        ok = queue.put_no_wait(i)
        print("produce", i, "ok", ok, "dropped", queue.dropped)

    while True:
        value = queue.get()
        if value is None:
            break
        print("consume", value)
```

### Swift

```swift
final class ISRQueue {
    private var items: [Int] = []
    private let capacity: Int
    private(set) var dropped = 0

    init(capacity: Int) {
        self.capacity = capacity
    }

    func putNoWait(_ value: Int) -> Bool {
        guard items.count < capacity else {
            dropped += 1
            return false
        }
        items.append(value)
        return true
    }

    func get() -> Int? {
        guard !items.isEmpty else {
            return nil
        }
        return items.removeFirst()
    }
}

let queue = ISRQueue(capacity: 4)

for i in 0..<6 {
    let ok = queue.putNoWait(i)
    print("produce", i, "ok", ok, "dropped", queue.dropped)
}

while let value = queue.get() {
    print("consume", value)
}
```
