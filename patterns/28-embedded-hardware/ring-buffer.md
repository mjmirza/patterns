---
name: Ring Buffer
slug: ring-buffer
family: 28-embedded-hardware
category: Structural
aliases: [Circular Buffer, FIFO Ring, Lock-Free SPSC Queue]
first_described: "Zephyr Project documentation, ring buffer data structure"
maturity: canonical
related: [interrupt-service-routine, double-buffering]
incompatible_with: []
verified: 2026-08-21
---

# Ring Buffer

## 1. Name, aliases, and lineage

The canonical name is Ring Buffer, the data structure that stores a
fixed-capacity, first-in-first-out sequence of elements by wrapping
around to the start of its underlying storage once it reaches the end,
rather than shifting elements or growing without bound. The Zephyr
Project's own documentation states the definition directly. "A ring
buffer is a circular buffer, whose contents are stored in
first-in-first-out order."

The alias **Circular Buffer** names the same structure by its more
descriptive, general term. **FIFO Ring** names it by the ordering
guarantee it provides, described directly in Zephyr's own
documentation. "Data streamed through a ring buffer is always written
to the next byte within the buffer, wrapping around to the first
element after reaching the end." **Lock-Free SPSC Queue** names the
specific, narrower guarantee the structure provides for exactly one
producer and one consumer, the property that makes it the standard
hand-off mechanism between an interrupt context and a task.

## 2. Problem and context

Passing data from one execution context to another, most critically
from an interrupt context to a task, needs a hand-off mechanism that
is genuinely safe under concurrent access without the cost, and the
interrupt-context incompatibility, of a full lock. A Ring Buffer
solves this specifically for the single-producer, single-consumer
case, where Zephyr's own documentation states the safety guarantee
directly. "A single producer and a single consumer running in separate
execution contexts, for example two threads, or one thread and one
ISR, may use the same ring buffer concurrently without additional
locking." The structure achieves this safety not through a lock but
through a careful division of which side owns which piece of shared
state, letting an interrupt context feed data into the buffer and a
task consume it without either side ever blocking the other.

## 3. Forces

The pattern balances the following competing pressures.

- **Lock-free safety for exactly one producer and one consumer.**
  Favored. Zephyr's own documentation names the mechanism directly.
  "The producer side only updates the `put` indices and the consumer
  side only updates the `get` indices, so the two sides never write the
  same fields," a division that makes the structure genuinely safe
  without a lock, specifically for one producer and one consumer.
- **Bounded, predictable memory use.** Favored. The buffer's capacity
  is fixed at creation, so its memory footprint never grows
  unboundedly the way an unbounded queue could under sustained
  overload, a property the Zephyr Project's own documentation
  (https://docs.zephyrproject.org/latest/kernel/data_structures/ring_buffers.html)
  reflects directly in its fixed-size, first-in-first-out description.
- **Genuine safety beyond one producer or one consumer.** Sacrificed.
  The lock-free guarantee is specific to exactly one producer and one
  consumer, adding a second writer or a second reader without an
  additional lock reintroduces the exact race condition the structure
  was built to avoid.
- **Graceful behavior when genuinely full.** Sacrificed, to a degree
  that depends on the chosen policy. A ring buffer that is full when a
  new element arrives must have an explicit, deliberate policy,
  overwrite the oldest element, or reject the new one, since neither
  choice is free of consequence.

## 4. Applicability and non-applicability

Reach for a Ring Buffer when the following hold.

- The hand-off is genuinely a single-producer, single-consumer case,
  most commonly an interrupt context feeding a task, where the
  lock-free safety the pattern provides is a genuine, applicable
  guarantee.
- A bounded, predictable memory footprint is a genuine requirement,
  rather than a case where the data volume is unpredictable enough
  that a fixed capacity would need frequent, deliberate tuning.
- The application has a real, considered policy for what happens when
  the buffer is genuinely full, whether that is overwriting the oldest
  data or rejecting the new element.

Do NOT reach for a Ring Buffer in these cases, and the reason matters
more than the rule.

- **The hand-off genuinely needs more than one producer or more than
  one consumer**, using a plain ring buffer in this case without an
  additional lock silently reintroduces the exact race condition the
  structure exists to avoid, since its lock-free guarantee is specific
  to the single-producer, single-consumer case.
- **The data volume is genuinely unpredictable and a fixed capacity
  would need constant, ongoing retuning**, a structure that can
  legitimately grow, accepting its different cost profile, may fit
  better than a ring buffer whose capacity must be chosen once, ahead
  of time.
- **Losing data on overflow, or blocking the producer on overflow, is
  genuinely unacceptable for the specific data being passed**, a case
  needing a stronger delivery guarantee than either of the ring
  buffer's two overflow policies can honestly provide needs a
  different mechanism, one built for that stronger guarantee.

## 5. Structure

A Ring Buffer has three structural parts.

- **The fixed-capacity underlying storage**, a contiguous block sized
  once at creation, that the buffer's contents wrap around within.
- **The put index**, updated only by the producer side, following the
  division of ownership Zephyr's own documentation states directly,
  tracking where the next written element will go.
- **The get index**, updated only by the consumer side, tracking where
  the next read will come from, the separation from the put index
  being exactly what makes the structure safe without a lock for one
  producer and one consumer.

## 6. ASCII structure diagram

```
  +----------------------------------------------------------+
  |  fixed-capacity underlying storage, wraps at the end           |
  |                                                              |
  |   [ e0 ][ e1 ][ e2 ][    ][    ][    ][    ][    ]           |
  |     ^get              ^put                                    |
  |                                                              |
  |   producer writes at put, then advances put                    |
  |   consumer reads at get, then advances get                     |
  |   both indices wrap back to the start after the last slot       |
  +----------------------------------------------------------+
```

## 7. Dynamics

The trace below shows a producer and a consumer using the buffer
concurrently.

```
Producer writes an element

the producer, running in one execution context, writes a new element
at the current put index
   |-- the producer advances the put index, wrapping to the start of
       the storage if it reached the end
   |-- the producer only ever touches the put index, never the get
       index

Consumer reads an element

the consumer, running in a separate execution context, reads the
element at the current get index
   |-- the consumer advances the get index, wrapping to the start of
       the storage if it reached the end
   |-- the consumer only ever touches the get index, never the put
       index
   |-- because each side owns a distinct index, per Zephyr's own
       documentation, the two sides never write the same fields, and
       no lock is needed to keep this safe
```

## 8. Implementation variants

**Byte-stream ring buffer.** The buffer stores a raw stream of bytes
rather than discrete typed elements, matching Zephyr's own description
of data being "written to the next byte within the buffer," suited to
passing an arbitrary-length byte stream between a producer and a
consumer.

**Fixed-size-element ring buffer.** The buffer stores discrete,
fixed-size elements, indexed by element count rather than raw bytes, a
common variant for passing a stream of structured events or
measurements.

**Overwrite-on-full ring buffer.** When the buffer is genuinely full,
the producer overwrites the oldest, not-yet-consumed element rather
than being blocked or rejected, a variant suited to logging or
telemetry where the most recent data matters more than guaranteeing
delivery of every element ever written.

**Reject-on-full ring buffer.** When the buffer is genuinely full, the
producer's write is rejected rather than overwriting existing data, a
variant suited to a case where every element genuinely must be
consumed and losing one silently would be a real defect.

## 9. Known production uses

**The Zephyr Project's own ring buffer documentation, defining the
structure and its lock-free safety guarantee.** Zephyr states the
definition directly. "A ring buffer is a circular buffer, whose
contents are stored in first-in-first-out order," and states the
single-producer, single-consumer safety guarantee directly. "A single
producer and a single consumer running in separate execution contexts,
for example two threads, or one thread and one ISR, may use the same
ring buffer concurrently without additional locking," because "the
producer side only updates the `put` indices and the consumer side
only updates the `get` indices, so the two sides never write the same
fields." The Zephyr Project, "Ring Buffers,"
https://docs.zephyrproject.org/latest/kernel/data_structures/ring_buffers.html,
verified 2026-08-21.

## 10. Consequences

Positive.

- A single producer and a single consumer, most commonly an interrupt
  context and a task, can pass data through the buffer with no lock,
  a genuine, well-defined safety guarantee rather than an assumption.
- The buffer's fixed capacity gives a bounded, predictable memory
  footprint, never growing unboundedly under sustained load the way an
  unbounded queue could.
- The structure is simple enough to implement correctly with a small,
  reviewable amount of code, in contrast to a more general concurrent
  queue built for an arbitrary number of producers and consumers.

Negative.

- The lock-free safety guarantee is specific to exactly one producer
  and one consumer, and does not extend to a second writer or reader
  without an additional lock, a limit easy to violate accidentally as
  a system grows.
- A fixed capacity means the application must have an explicit,
  deliberate policy for what happens when the buffer is genuinely
  full, since the structure itself does not resolve that question on
  its own.
- The structure provides no built-in signal for how full it currently
  is, beyond what the application chooses to compute itself from the
  put and get indices, so observing its real fill level needs
  deliberate instrumentation.

## 11. Failure modes and misuse

**Using a plain ring buffer with more than one producer or more than
one consumer, with no additional lock.** Symptom. Data written by two
concurrent producers is occasionally corrupted or lost, or two
concurrent consumers occasionally read the same element twice or skip
an element entirely, an intermittent, hard-to-reproduce bug. Cause.
The ring buffer's lock-free safety guarantee is specific to exactly
one producer and one consumer, and adding a second writer or reader
without an additional lock reintroduces the exact race condition the
structure was built to avoid. Fix. Either add an explicit lock around
the additional producer or consumer, or use a data structure genuinely
built for multiple producers or consumers, rather than assuming the
plain ring buffer's safety extends beyond its documented
single-producer, single-consumer guarantee.

**Choosing the overflow policy without a deliberate decision about
which data matters more, the newest or the completeness of the
stream.** Symptom. Either genuinely important data is silently
overwritten and lost, in a system that should have rejected the write
instead, or a producer stalls or drops entirely new data waiting for
space, in a system where the most recent data was actually the
priority. Cause. Implementing whichever overflow behavior was simplest
to code, rather than making a deliberate, considered choice about
which failure mode is actually acceptable for the specific data the
buffer carries. Fix. Choose the overflow policy, overwrite-oldest or
reject-newest, based on a deliberate decision about which data matters
more for the specific use, and document that choice so a later
reviewer understands it was intentional.

**Sizing the buffer's capacity without measuring the real rate
mismatch between the producer and the consumer.** Symptom. The buffer
overflows under real production load, even though it never overflowed
in testing, because the real-world gap between how fast the producer
writes and how fast the consumer reads was never actually measured.
Cause. Choosing the buffer's capacity from an arbitrary or
convenient value, rather than from a genuine measurement of the
producer and consumer's real relative rates under real load. Fix.
Measure the real production rate mismatch between the producer and
consumer, and size the buffer's capacity with real margin above that
measured worst case, rather than an unmeasured, arbitrary value.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Ring Buffer, single-producer single-consumer | A locked general-purpose queue | Double Buffering |
|---|---|---|---|
| Lock-free safety for one producer and one consumer | Strong, genuinely lock-free for this specific case | Not applicable, safety comes from the lock, not the structure | Strong for its own narrower swap-based use case |
| Bounded, predictable memory use | Strong, fixed capacity chosen at creation | Moderate to weak, depends on whether the queue is itself bounded | Strong, exactly two fixed buffers |
| Safety for more than one producer or consumer | Weak, requires an additional lock outside the structure itself | Strong, the lock is built in | Not applicable, double buffering is not built for multiple writers |
| Graceful, deliberate overflow behavior | Moderate, needs an explicit policy choice | Strong, a locked queue can block a producer safely until space frees | Not applicable, double buffering has no queue-fullness concept |

Reading of the table. A Ring Buffer wins specifically for the
single-producer, single-consumer case where its lock-free safety is a
genuine, applicable guarantee, most notably an interrupt-to-task
hand-off. A locked general-purpose queue remains the right choice when
the system genuinely needs more than one producer or consumer.

## 13. Related and incompatible patterns

- **Interrupt Service Routine.** A ring buffer is the standard hand-off
  mechanism between an interrupt context and its deferred task,
  specifically because its single-producer, single-consumer safety
  guarantee matches exactly the shape of that hand-off, one interrupt
  context writing, one task reading.
- **Double Buffering.** Both patterns solve a producer-consumer
  hand-off problem, but double buffering swaps between exactly two
  whole buffers as a unit, while a ring buffer streams individual
  elements or bytes continuously, a genuinely different shape suited
  to a different kind of data flow.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a system currently sharing data between an
interrupt context and a task through an unprotected shared variable.

1. Confirm the hand-off is genuinely a single-producer, single-consumer
   case, since the pattern's lock-free safety does not extend beyond
   it.
2. Measure the real rate mismatch between the producer and the
   consumer, and choose the buffer's capacity with real margin above
   that measured worst case.
3. Choose an explicit, deliberate overflow policy, overwrite-oldest or
   reject-newest, based on which failure mode is genuinely acceptable
   for the specific data the buffer will carry.
4. Replace the unprotected shared variable with the ring buffer,
   confirming the producer only ever touches the put index and the
   consumer only ever touches the get index.

Removing the pattern when it stops earning its place, most relevant
when the hand-off has genuinely grown to need more than one producer
or more than one consumer.

1. Confirm, concretely, that the hand-off genuinely now needs multiple
   producers or consumers, rather than assuming so without checking
   the real, current shape of the data flow.
2. Replace the plain ring buffer with a structure genuinely built for
   multiple producers or consumers, such as a locked general-purpose
   queue.
3. Confirm the replacement's overflow and capacity behavior still
   matches what the application genuinely needs, since a different
   structure may carry a different default policy.

## 15. Testing and verification

Easier because of the pattern.

- A test can drive the producer and consumer sides directly, in a
  single-threaded test rig simulating the interleaving, and assert
  the buffer's contents and indices behave correctly, independent of
  any real interrupt actually firing.
- Because the structure's safety rests on the explicit put-index and
  get-index ownership division, a test can specifically assert that
  the producer's operations never touch the get index and the
  consumer's operations never touch the put index, directly verifying
  the safety property's real mechanism.

Harder because of the pattern.

- Verifying the buffer is genuinely safe under real, concurrent
  execution, not merely a single-threaded simulation of interleaving,
  needs a test that can reliably trigger the real interrupt at the
  specific moments most likely to expose a race, a category of test
  that is hard to construct reliably without real hardware-in-the-loop
  support.
- Confirming the chosen overflow policy behaves correctly under
  genuine sustained overload needs a test that can drive the producer
  faster than the consumer for a real, sustained period, rather than a
  brief, artificial burst.

Techniques that apply.

- **Single-threaded interleaving simulation tests.** Drive the
  producer and consumer sides in a controlled sequence, asserting the
  buffer's contents and wrap-around behavior at each step.
- **Ownership-boundary assertion tests.** Assert directly that the
  producer's code path never writes the get index, and the consumer's
  code path never writes the put index, verifying the real mechanism
  behind the pattern's lock-free safety.
- **Sustained-overload overflow tests.** Drive the producer faster than
  the consumer for a real, sustained period, and assert the chosen
  overflow policy, overwrite-oldest or reject-newest, behaves exactly
  as designed.
- **Hardware-in-the-loop race testing.** Trigger the real interrupt
  under real timing pressure against the consuming task's real
  execution, verifying the buffer holds up under genuine concurrent
  access.

## 16. Observability signals

What to record.

- The buffer's real, measured fill level over time in production,
  since this signal directly answers whether the chosen capacity has
  real margin, or is running close to full under genuine load.
- The frequency the overflow policy actually fires, whether that is an
  overwrite of unconsumed data or a rejected write, since either
  outcome represents a real, measurable cost the application is
  paying.

A healthy state. The buffer's real fill level stays comfortably below
its full capacity under genuine production load, and the overflow
policy fires rarely or never.

A failing state. The buffer's real fill level runs consistently close
to full, or the overflow policy fires with real frequency,
pointing at a real, measured rate mismatch between the producer and
consumer that the current capacity does not have enough margin to
absorb.

## 17. Security and privacy implications

**A ring buffer whose producer side is reachable from untrusted,
external input must validate the size and shape of that input before
writing it, since a mismatch between the input's real size and the
buffer's expected element or byte layout is a genuine memory-safety
risk, not merely a theoretical one.** If externally supplied data is
written into a fixed-size ring buffer without confirming it genuinely
fits the buffer's expected element size or byte layout, a malformed or
oversized input can corrupt adjacent memory or overwrite the buffer's
own index state, a real, exploitable defect for any embedded system
that receives data from an external source such as a network or serial
interface. Validating the length and shape of any externally supplied
data before it is written into the buffer is a necessary part of the
producer side's own implementation, not an optional hardening step.

## 18. References

1. The Zephyr Project. "Ring Buffers".
   https://docs.zephyrproject.org/latest/kernel/data_structures/ring_buffers.html
   Verified 2026-08-21. Source of the definition, FIFO ordering, and
   single-producer single-consumer safety quotes used in dimensions 1,
   2, 3, 5, and 9.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. C models the fixed-capacity, put-index-and-get-index shape
directly, the language embedded firmware ring buffers are actually
written in. Python shows the same conceptual shape using a minimal,
host-testable simulation, the pattern's ownership-boundary-testable
variant from dimension 15, expressed portably. Swift shows the same
conceptual shape using a minimal model, analogous to how a native
application's own producer-consumer data flow might be structured.
Java, Go, and Rust are omitted, since the pattern's real home is C and
the two languages chosen already cover its production and its
testable-simulation shapes.

### C

```c
#include <stdio.h>
#include <stdint.h>

#define RING_CAPACITY 8

typedef struct {
    uint8_t data[RING_CAPACITY];
    int put_index;
    int get_index;
} ring_buffer_t;

static void ring_init(ring_buffer_t *rb) {
    rb->put_index = 0;
    rb->get_index = 0;
}

static int ring_is_full(const ring_buffer_t *rb) {
    return ((rb->put_index + 1) % RING_CAPACITY) == rb->get_index;
}

static int ring_is_empty(const ring_buffer_t *rb) {
    return rb->put_index == rb->get_index;
}

static int ring_put(ring_buffer_t *rb, uint8_t value) {
    if (ring_is_full(rb)) {
        return 0;
    }
    rb->data[rb->put_index] = value;
    rb->put_index = (rb->put_index + 1) % RING_CAPACITY;
    return 1;
}

static int ring_get(ring_buffer_t *rb, uint8_t *out) {
    if (ring_is_empty(rb)) {
        return 0;
    }
    *out = rb->data[rb->get_index];
    rb->get_index = (rb->get_index + 1) % RING_CAPACITY;
    return 1;
}

int main(void) {
    ring_buffer_t rb;
    ring_init(&rb);

    ring_put(&rb, 10);
    ring_put(&rb, 20);
    ring_put(&rb, 30);

    uint8_t value;
    while (ring_get(&rb, &value)) {
        printf("consumed %u", (unsigned)value);
        putchar(10);
    }

    return 0;
}
```

### Python

```python
from dataclasses import dataclass, field


@dataclass
class RingBuffer:
    capacity: int
    data: list = field(default_factory=list)
    put_index: int = 0
    get_index: int = 0

    def __post_init__(self) -> None:
        self.data = [0] * self.capacity

    def is_full(self) -> bool:
        return (self.put_index + 1) % self.capacity == self.get_index

    def is_empty(self) -> bool:
        return self.put_index == self.get_index

    def put(self, value: int) -> bool:
        if self.is_full():
            return False
        self.data[self.put_index] = value
        self.put_index = (self.put_index + 1) % self.capacity
        return True

    def get(self) -> int | None:
        if self.is_empty():
            return None
        value = self.data[self.get_index]
        self.get_index = (self.get_index + 1) % self.capacity
        return value


if __name__ == "__main__":
    rb = RingBuffer(capacity=8)

    rb.put(10)
    rb.put(20)
    rb.put(30)

    value = rb.get()
    while value is not None:
        print("consumed " + str(value))
        value = rb.get()
```

### Swift

```swift
final class RingBuffer {
    private var data: [UInt8]
    private var putIndex: Int = 0
    private var getIndex: Int = 0
    private let capacity: Int

    init(capacity: Int) {
        self.capacity = capacity
        self.data = [UInt8](repeating: 0, count: capacity)
    }

    var isFull: Bool {
        (putIndex + 1) % capacity == getIndex
    }

    var isEmpty: Bool {
        putIndex == getIndex
    }

    func put(_ value: UInt8) -> Bool {
        guard !isFull else { return false }
        data[putIndex] = value
        putIndex = (putIndex + 1) % capacity
        return true
    }

    func get() -> UInt8? {
        guard !isEmpty else { return nil }
        let value = data[getIndex]
        getIndex = (getIndex + 1) % capacity
        return value
    }
}

let rb = RingBuffer(capacity: 8)

_ = rb.put(10)
_ = rb.put(20)
_ = rb.put(30)

while let value = rb.get() {
    print("consumed " + String(value))
}
```
