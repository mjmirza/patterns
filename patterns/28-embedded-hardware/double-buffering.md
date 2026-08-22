---
name: Double Buffering
slug: double-buffering
family: 28-embedded-hardware
category: Structural
aliases: [Back Buffer, Front-Back Buffer Swap, Flip Buffering]
first_described: "LVGL documentation, display double buffering"
maturity: canonical
related: [ring-buffer, hardware-abstraction-layer]
incompatible_with: []
verified: 2026-08-21
---

# Double Buffering

## 1. Name, aliases, and lineage

The canonical name is Double Buffering, the pattern where two
complete buffers hold a display's contents, one currently shown to
the user while the other is written to, and the two are swapped once
the write is genuinely finished, so the user never sees a
partially-drawn frame. LVGL's own documentation states the mechanism
directly. The system "can draw into one buffer while the content of
the other buffer is sent to the display in the background."

The alias **Back Buffer** names the buffer currently being written to,
as distinct from the front buffer currently shown. **Front-Back Buffer
Swap** names the operation that exchanges the two roles once a write
completes. **Flip Buffering** names the pattern by the specific swap
mechanism many implementations use, changing which buffer's address is
treated as the front buffer rather than physically copying pixel data
between two fixed locations.

## 2. Problem and context

Writing new content directly into the same buffer a display is
actively reading from produces a visible defect, since the display
reads the buffer's contents continuously and can capture it mid-write,
showing a frame that is part old content and part new content, a
defect commonly called tearing. Double Buffering solves this by never
writing into the buffer the display is currently reading from,
writing new content into a separate buffer instead, and only exposing
that new content to the display once it is genuinely complete. LVGL's
own documentation names the resulting benefit directly, describing how
"DMA or other hardware should be used to transfer data to the display
so the MCU can continue drawing," so that "the rendering and
refreshing of the display become parallel operations," rather than the
display ever being shown a buffer mid-write.

## 3. Forces

The pattern balances the following competing pressures.

- **Relief from visible tearing.** Favored. The display is never
  shown a buffer that is currently being written to, since writing and
  display always target the two different buffers, directly
  eliminating the mid-write capture that produces tearing.
- **Parallel rendering and display refresh.** Favored. LVGL's own
  documentation states this directly, the MCU "can continue drawing"
  into one buffer "while the content of the other buffer is sent to
  the display in the background," letting rendering and refreshing
  proceed as genuinely parallel operations rather than one blocking
  the other.
- **Memory cost.** Sacrificed. Two complete buffers must be held in
  memory at once, twice the footprint of a single-buffer setup, a
  cost LVGL's own documentation acknowledges directly by offering a
  smaller, partial-buffer alternative specifically for memory-
  constrained targets, described in dimension 8.
- **Immediate visibility of a partial update.** Sacrificed. A change
  written to the back buffer is not visible to the user until the
  entire buffer's write completes and the swap happens, so a system
  needing to show a partial, in-progress update as it happens does not
  fit this pattern directly.

## 4. Applicability and non-applicability

Reach for Double Buffering when the following hold.

- The display's content genuinely changes often enough, or fast
  enough, that visible tearing would be a real, felt defect for the
  user, rather than a purely theoretical concern.
- The system has genuinely enough memory available to hold two
  complete buffers at once, a real, measured constraint rather than an
  assumption.
- The rendering work genuinely benefits from proceeding in parallel
  with the display refresh, rather than a case where rendering is fast
  enough relative to the refresh rate that the parallelism the pattern
  provides adds little real value.

Do NOT reach for Double Buffering in these cases, and the reason
matters more than the rule.

- **The system genuinely lacks the memory for two complete buffers**,
  LVGL's own documentation names this exact constraint directly, on a
  microcontroller where two full-screen buffers would exceed available
  on-board memory, a smaller, partial-render buffering strategy fits
  better than forcing the full double-buffer memory cost.
- **The display's content changes rarely enough that tearing is not a
  genuine, felt problem**, a mostly-static display, updated
  infrequently and not while actively being read by the display
  hardware, gains little from the pattern's added memory cost.
- **The application genuinely needs to show a partial, in-progress
  update as it happens**, rather than only the completed result,
  double buffering's very purpose, hiding an in-progress write until
  it completes, works against that specific need.

## 5. Structure

Double Buffering has three structural parts.

- **The front buffer**, the buffer currently being read by the display
  hardware, shown to the user right now.
- **The back buffer**, the buffer currently being written to, holding
  content not yet shown to the user.
- **The swap operation**, the point at which the roles of the two
  buffers exchange, LVGL's own documentation describing the mechanism
  as the flush callback needing only "to update the address of the
  frame buffer," rather than physically copying pixel data between two
  fixed memory locations.

## 6. ASCII structure diagram

```
  +--------------------+       +--------------------+
  |  Front buffer         |       |  Back buffer          |
  |  currently shown        |       |  currently written to   |
  |  to the display          |       |  by the application      |
  +--------------------+       +--------------------+
             ^                              |
             |                              |
             +----- swap once write --------+
                   genuinely completes
```

## 7. Dynamics

The trace below shows one complete write-and-swap cycle.

```
Application writes a new frame

the application writes the new content into the back buffer, the one
NOT currently being read by the display
   |-- the front buffer, meanwhile, continues being read and shown by
       the display hardware, entirely unaffected by the write
   |-- per LVGL's own documentation, this write can proceed in
       parallel with the display's own refresh, since the two target
       different buffers

Write completes, swap happens

the application's write to the back buffer genuinely finishes
   |-- the swap operation exchanges the two buffers' roles, the
       newly-written buffer becomes the new front buffer
   |-- the display now reads from what was the back buffer, showing
       the complete, finished frame, never a partial one
   |-- what was the front buffer becomes the new back buffer, ready
       for the next write
```

## 8. Implementation variants

**Address-swap double buffering.** The two buffers occupy fixed,
separate memory locations, and the swap operation changes which
address is treated as the front buffer, LVGL's own documentation
describing this as the "traditional" form, where the flush callback
"only has to update the address of the frame buffer."

**Partial-buffer rendering, the memory-constrained alternative.**
Rather than two full-screen buffers, one or more smaller buffers, sized
well below the full display, are used, with only the changed region
redrawn and transferred. LVGL's own documentation states this variant
directly avoids the cost of two full-screen buffers, recommending a
draw buffer of roughly "1/10 screen sized buffer(s)" as the point past
which "there is no significant performance improvement," so a small
buffer captures most of the benefit at a fraction of the memory.

**Triple buffering.** A third buffer is added specifically to further
overlap rendering and transfer, so that while one buffer is displayed
and a second undergoes its transfer to the display, a third is
available for the application to begin rendering the next frame
immediately, rather than waiting for the transfer to finish.

## 9. Known production uses

**LVGL's own documentation, defining the double-buffering mechanism
and its trade-offs.** LVGL states the mechanism directly. The system
"can draw into one buffer while the content of the other buffer is
sent to the display in the background," using DMA or similar hardware
"so the MCU can continue drawing," making "the rendering and
refreshing of the display become parallel operations." LVGL also
states the swap mechanism. The flush callback "only has to update the
address of the frame buffer." LVGL, "Display interface,"
https://lvgl.io/docs/open/8.3/porting/display, verified 2026-08-21.

**LVGL's own documentation, on the single-buffer trade-off this
pattern removes.** LVGL states the constraint directly, that "a
larger buffer results in better performance but above 1/10 screen
sized buffer(s) there is no significant performance improvement,"
and that with a single buffer the system must wait for the flush to
complete before drawing can continue, the exact serial cost double
buffering removes. LVGL, "Display interface" (the buffer-sizing and
single-buffer sections), https://lvgl.io/docs/open/8.3/porting/display,
verified 2026-08-21.

## 10. Consequences

Positive.

- The display is never shown a buffer mid-write, directly eliminating
  the visible tearing defect the pattern exists to prevent.
- Rendering and display refresh proceed as genuinely parallel
  operations, LVGL's own documentation naming this benefit directly,
  rather than one blocking the other.
- The swap operation itself, when implemented as an address change
  rather than a physical copy, is cheap, adding negligible cost
  compared to the write it follows.

Negative.

- Two complete buffers must be held in memory at once, twice the
  footprint of a single-buffer setup, a real cost on a memory-
  constrained microcontroller, which is exactly why LVGL's own
  documentation offers the smaller, partial-buffer alternative from
  dimension 8 for targets that cannot afford it.
- A change is not visible to the user until the entire back-buffer
  write completes and the swap happens, so the pattern does not fit a
  genuine need to show a partial, in-progress update.
- On a system where rendering is already fast relative to the display's
  refresh rate, the added memory cost buys comparatively little real
  benefit over a simpler single-buffer approach.

## 11. Failure modes and misuse

**Swapping the buffers before the write to the back buffer has
genuinely finished.** Symptom. The display shows a partially-drawn
frame, the exact tearing defect the pattern exists to prevent, even
though double buffering was implemented, because the swap fired before
the write it was meant to wait for actually completed. Cause. Treating
the swap as safe to perform as soon as the write operation was issued,
rather than confirming, through a genuine completion signal, that the
write has actually finished. Fix. Gate the swap operation on a real,
verified completion signal from the write, whether that is a DMA
completion interrupt or an explicit synchronous confirmation, never on
an assumption that the write finished by the time the swap code runs.

**Choosing full double buffering on a system with genuinely
insufficient memory for two complete buffers.** Symptom. The system
runs out of available memory, because two full-screen buffers were
budgeted without first confirming the target hardware's real,
available memory. Cause. Defaulting to the full double-buffering
variant without checking whether the specific target hardware
genuinely has the memory for two complete buffers. Fix. Measure the
target hardware's real available memory before committing to full
double buffering, and use the partial-buffer rendering variant, per
LVGL's own documented buffer-sizing guidance, when the memory
genuinely does not fit two complete buffers.

**Writing to the buffer currently being shown, rather than the back
buffer, due to a bookkeeping error in which buffer is which.** Symptom.
The display shows visible corruption or flicker, the exact defect
double buffering exists to prevent, because the application's own
tracking of which buffer is currently the front buffer and which is
the back buffer became inconsistent with reality. Cause. A bug in the
swap bookkeeping, an off-by-one error, a race between the swap and the
next write, or a missed update to which buffer pointer the application
treats as writable. Fix. Keep the front-and-back buffer role tracking
in one single, authoritative place, updated only by the swap
operation itself, and never let application code independently
determine which buffer is currently writable from a separate,
a separate, possibly stale source.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Double Buffering | Single buffer, direct write | Partial-buffer rendering |
|---|---|---|---|
| Relief from visible tearing | Strong, the display never sees a mid-write buffer | Weak, a write in progress is directly visible to the display | Strong for the changed region, since only the smaller buffer's transfer is synchronized |
| Parallel rendering and display refresh | Strong, per LVGL's own documented design | Not applicable, there is only one buffer to contend over | Moderate, parallelism is possible but scoped to the smaller buffer |
| Memory cost | High, two complete buffers, per LVGL's own noted external-RAM constraint | Low, exactly one buffer | Low, LVGL's own documentation states it can fit in internal RAM |
| Immediate visibility of a partial update | Weak, a write is hidden until the full swap | Strong, a write is visible as soon as it happens, tearing risk included | Moderate, the changed region becomes visible once its own smaller write and transfer complete |

Reading of the table. Double Buffering wins specifically when tearing
is a real, felt problem and the target hardware genuinely has the
memory for two full buffers. On a genuinely memory-constrained target,
LVGL's own partial-buffer rendering variant delivers most of the
tearing-relief benefit at a fraction of the memory cost.

## 13. Related and incompatible patterns

- **Ring Buffer.** Both patterns solve a producer-consumer hand-off
  problem, but a ring buffer streams individual elements continuously
  while double buffering swaps between exactly two whole buffers as a
  unit, a genuinely different shape suited to a genuinely different
  kind of data flow, a full frame at a time rather than a continuous
  stream.
- **Hardware Abstraction Layer.** The DMA or display-controller
  hardware that transfers a completed back buffer to the display is
  frequently accessed through a hardware abstraction layer, keeping
  the double-buffering logic itself portable across different display
  controller implementations.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a display currently written to directly,
in a single buffer the display hardware also reads from.

1. Confirm the target hardware genuinely has enough memory for two
   complete buffers, measuring the real, available memory rather than
   assuming it fits.
2. Allocate the second buffer, and establish a single, authoritative
   place that tracks which buffer is currently the front buffer and
   which is the back buffer.
3. Redirect all writes to target the back buffer exclusively, never
   the buffer currently being read by the display.
4. Gate the swap operation on a genuine, verified write-completion
   signal, never an assumption that the write finished by the time the
   swap code runs.

Removing the pattern when it stops earning its place, most relevant
when the target hardware's real memory constraints make two complete
buffers genuinely unaffordable.

1. Confirm, concretely, that the memory constraint is real and
   measured, rather than assumed, before removing the pattern's
   tearing-relief guarantee.
2. Move to the partial-buffer rendering variant, per LVGL's own
   documented approach, rather than dropping to a single, full-size
   buffer with no tearing protection at all.
3. Confirm the resulting tearing behavior, on the smaller, partial
   buffer, is genuinely acceptable for the application's real visual
   requirements.

## 15. Testing and verification

Easier because of the pattern.

- A test can drive a sequence of writes and swaps and assert the
  front buffer, at every point the display would actually read it,
  always contains a complete, never a partial, frame.
- Because the swap operation is a single, well-defined point, a test
  can specifically assert it only fires after a genuine write-
  completion signal, directly verifying the exact mechanism the first
  failure mode in dimension 11 depends on.

Harder because of the pattern.

- Verifying tearing is genuinely absent on the real target display
  needs a test on the actual hardware, since a host-based simulation
  does not reproduce the real display's actual read timing.
- Confirming the swap's write-completion gating is genuinely correct
  under real timing pressure, not merely in a slow, artificial test
  sequence, needs a test that can exercise the real DMA or hardware
  completion signal under production-like load.

Techniques that apply.

- **Complete-frame assertion tests.** Drive a sequence of writes and
  swaps, and assert the front buffer, at every point it would be read,
  contains a complete, coherent frame, never a partial write.
- **Swap-gating tests.** Assert the swap operation only fires after a
  genuine, verified write-completion signal, never merely after the
  write was issued.
- **Real-hardware tearing verification.** Confirm, on the actual
  target display, that no visible tearing occurs across a real,
  sustained sequence of frame updates.
- **Memory-budget verification.** Confirm the target hardware's real,
  measured available memory genuinely fits two complete buffers before
  committing to the full double-buffering variant over the
  partial-buffer alternative.

## 16. Observability signals

What to record.

- Whether the swap operation's write-completion gate is ever bypassed
  or fires early, since this signal directly points at the exact
  mechanism behind the tearing failure mode in dimension 11.
- The real, measured memory footprint the two buffers consume in
  production, since this signal directly confirms whether the target
  hardware's real memory budget genuinely supports the pattern as
  deployed.

A healthy state. The swap operation consistently fires only after a
genuine, verified write completion, and the real, measured memory
footprint of the two buffers stays comfortably within the target
hardware's actual available memory.

A failing state. The swap operation is observed firing before a
write-completion signal, a defect that would produce the exact
tearing the pattern exists to prevent, or the real, measured memory
footprint runs uncomfortably close to the target hardware's total
available memory, pointing at a system that should reconsider the
memory-constrained partial-buffer alternative.

## 17. Security and privacy implications

**A back buffer that is not fully overwritten before its content is
made visible as the new front buffer can leak stale, previously
displayed content, including genuinely sensitive information, if the
new write does not cover every pixel the previous frame occupied.** If
an application writes only a partial update into the back buffer,
assuming the untouched region still holds the same content as the
current front buffer, but the swap then makes that back buffer the new
front buffer without confirming the assumption genuinely holds, any
region the new write did not actually touch can display stale content
from an earlier, unrelated frame, a real information-disclosure risk
for a display that shows sensitive information such as a
password-entry field or a private notification. Confirming the back
buffer's content is genuinely complete and correct for every pixel
before the swap makes it visible is a real, necessary part of a
security-conscious double-buffering implementation, not merely a
visual-quality concern.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. C models the front-buffer-back-buffer-swap shape directly, the
language embedded display drivers are actually written in, using
pointer swapping to represent the address-swap variant. Python shows
the same conceptual shape using a minimal, host-testable simulation,
the pattern's complete-frame-assertion-testable variant from
dimension 15, expressed portably. Swift shows the same conceptual
shape using a minimal model, analogous to how a native application's
own rendering pipeline might track a front and back buffer pair. Java,
Go, and Rust are omitted, since the pattern's real home is C and the
two languages chosen already cover its production and its
testable-simulation shapes.

### C

```c
#include <stdio.h>
#include <string.h>

#define BUFFER_SIZE 4

typedef struct {
    int pixels[BUFFER_SIZE];
    int write_complete;
} frame_buffer_t;

static frame_buffer_t buffer_a = {{0, 0, 0, 0}, 1};
static frame_buffer_t buffer_b = {{0, 0, 0, 0}, 1};

static frame_buffer_t *front = &buffer_a;
static frame_buffer_t *back = &buffer_b;

static void write_frame(frame_buffer_t *buf, int value) {
    buf->write_complete = 0;
    for (int i = 0; i < BUFFER_SIZE; i++) {
        buf->pixels[i] = value;
    }
    buf->write_complete = 1;
}

static int swap_if_ready(void) {
    if (!back->write_complete) {
        return 0;
    }
    frame_buffer_t *temp = front;
    front = back;
    back = temp;
    return 1;
}

static void print_front(void) {
    printf("front buffer:");
    for (int i = 0; i < BUFFER_SIZE; i++) {
        printf(" %d", front->pixels[i]);
    }
    putchar(10);
}

int main(void) {
    write_frame(back, 42);
    swap_if_ready();
    print_front();

    write_frame(back, 7);
    swap_if_ready();
    print_front();

    return 0;
}
```

### Python

```python
from dataclasses import dataclass, field


@dataclass
class FrameBuffer:
    pixels: list
    write_complete: bool = True


def write_frame(buf: FrameBuffer, value: int) -> None:
    buf.write_complete = False
    buf.pixels = [value] * len(buf.pixels)
    buf.write_complete = True


def swap_if_ready(front: FrameBuffer, back: FrameBuffer) -> tuple[FrameBuffer, FrameBuffer]:
    if not back.write_complete:
        return front, back
    return back, front


if __name__ == "__main__":
    front = FrameBuffer(pixels=[0, 0, 0, 0])
    back = FrameBuffer(pixels=[0, 0, 0, 0])

    write_frame(back, 42)
    front, back = swap_if_ready(front, back)
    print("front buffer: " + str(front.pixels))

    write_frame(back, 7)
    front, back = swap_if_ready(front, back)
    print("front buffer: " + str(front.pixels))
```

### Swift

```swift
final class FrameBuffer {
    var pixels: [Int]
    var writeComplete: Bool = true

    init(pixels: [Int]) {
        self.pixels = pixels
    }
}

func writeFrame(_ buf: FrameBuffer, value: Int) {
    buf.writeComplete = false
    buf.pixels = Array(repeating: value, count: buf.pixels.count)
    buf.writeComplete = true
}

func swapIfReady(front: FrameBuffer, back: FrameBuffer) -> (FrameBuffer, FrameBuffer) {
    guard back.writeComplete else {
        return (front, back)
    }
    return (back, front)
}

var front = FrameBuffer(pixels: [0, 0, 0, 0])
var back = FrameBuffer(pixels: [0, 0, 0, 0])

writeFrame(back, value: 42)
(front, back) = swapIfReady(front: front, back: back)
print("front buffer: " + String(describing: front.pixels))

writeFrame(back, value: 7)
(front, back) = swapIfReady(front: front, back: back)
print("front buffer: " + String(describing: front.pixels))
```

## 18. References

1. LVGL. "Display interface".
   https://lvgl.io/docs/open/8.3/porting/display
   Verified 2026-08-21. Source of the double-buffering mechanism,
   swap, and buffer-sizing quotes used in dimensions 1, 2, 3, 8, 9,
   and 10.
