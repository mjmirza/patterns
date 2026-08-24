---
name: Virtual List
slug: virtual-list
family: 13-frontend-ui
category: Rendering Strategy
aliases: [List Virtualization, Windowing]
first_described: "web.dev, react-window virtualization guide"
maturity: canonical
related: [infinite-scroll, hooks, atomic-design]
incompatible_with: []
verified: 2026-08-21
---

# Virtual List

## 1. Name, aliases, and lineage

The canonical name is Virtual List, a rendering technique where a
long list keeps only the items currently visible to the user in the
DOM, recycling and repositioning them as the user scrolls, rather
than rendering every item in the underlying data set at once. TanStack
Virtual's own documentation defines the idea directly. "TanStack
Virtual is a headless UI utility for virtualizing long lists of
elements." Web.dev's guide to the technique names the mechanism
equally plainly. "List virtualization, the concept of only rendering what
is visible to the user. The number of elements that are rendered at
first is a very small subset of the entire list."

The alias **List Virtualization** is the formal, general name for the
technique across implementations. **Windowing** names the same idea
by its mechanism directly, the "window" of visible content moving as
the user scrolls, with content outside that window never mounted in
the DOM at all.

## 2. Problem and context

A list rendered in full, every item mounted as a real DOM node
regardless of whether the user can currently see it, works fine for a
short list but degrades badly as the list grows into the thousands.
Web.dev's own guide names the cost directly. "Super large tables and
lists can slow down your site's performance significantly," since
every mounted node adds to the cost of the browser's style
calculations and layout, whether or not that node is ever actually
visible on screen. Virtual List solves this by keeping only the small
subset of items currently within, or slightly outside, the visible
viewport actually mounted in the DOM, recycling those DOM nodes for
new content as the user scrolls, so a list of fifty thousand items
lives in the DOM as only the small handful of nodes the viewport can
actually display at once.

## 3. Forces

The pattern balances the following competing pressures.

- **Rendering cost proportional to viewport size, not data size.**
  Favored. Because only the visible items are mounted, the DOM node
  count, and the corresponding style and layout cost, stays roughly
  constant regardless of whether the underlying list has one hundred
  items or one hundred thousand.
- **Scroll performance at large data sizes.** Favored. Web.dev's own
  guide states the direct benefit. recycling DOM nodes as items enter
  and exit the visible window "improves both the rendering and
  scrolling performance of the list," keeping scrolling smooth even
  for a data set that would otherwise overwhelm the browser if fully
  rendered.
- **Simplicity of implementation.** Sacrificed. A virtualized list
  needs to calculate item positions, track scroll offset, and
  correctly size a container to match the full list's total scrolled
  height, a real amount of additional bookkeeping a naive, fully
  rendered list does not need.
- **Native browser behaviors that assume every item is present.**
  Sacrificed unless deliberately handled. Browser-native find-in-page,
  full-page printing, and screen-reader navigation by default only
  see the items currently mounted, so a virtualized list needs
  deliberate additional work to remain accessible and searchable in
  the same way a fully rendered list is by default.

## 4. Applicability and non-applicability

Reach for Virtual List when the following hold.

- The underlying list is genuinely large enough, hundreds to
  thousands of items or more, that rendering every item at once
  causes a measurable degradation in rendering, scrolling, or
  interaction performance.
- The list's items are of a predictable, or at least calculable,
  size, since the technique needs to compute each item's position
  within the overall scrollable container.
- The team is prepared to invest the additional implementation effort
  the technique needs, and to deliberately address the accessibility
  and native-browser-behavior gaps a virtualized list introduces by
  default.

Do NOT reach for Virtual List in these cases, and the reason matters
more than the rule.

- **The list is genuinely small enough that rendering every item
  causes no measurable performance problem**, adopting the technique's
  real implementation and accessibility overhead for a list that was
  never actually slow trades complexity for a benefit that does not
  exist.
- **The list's items have wildly unpredictable or unmeasurable sizes
  that cannot be calculated in advance**, since the technique depends
  on being able to compute each item's position within the scrollable
  container, and a poor size estimate produces visible jumping or
  incorrect scrollbar behavior.
- **The team cannot invest the additional effort to keep the list
  genuinely accessible**, native browser find-in-page, full-page
  printing, and default screen-reader navigation all assume every
  item is present in the DOM, and a virtualized list that ignores this
  gap degrades the experience for those specific, real use cases.

## 5. Structure

Virtual List has three structural parts.

- **The scroll container**, sized to match the full list's total
  scrolled height, even though only a small subset of its content is
  actually mounted, so the browser's scrollbar and scroll behavior
  reflect the true size of the underlying data.
- **The visible window**, the small range of items currently within,
  or slightly outside, the viewport, the only items actually mounted as
  real DOM nodes at any given moment.
- **The recycling mechanism**, the logic that unmounts an item as it
  scrolls out of the window and mounts a new item as it scrolls in,
  repositioning DOM nodes rather than creating and destroying them
  freely.

## 6. ASCII structure diagram

```
  +----------------------------------------------------------------+
  |  Scroll container (sized to match all 10,000 items' total      |
  |  height, even though only a handful are actually mounted)       |
  |                                                                   |
  |   ... (scrolled-past items, not in the DOM) ...                  |
  |                                                                   |
  |   +--------------------------------------------------------+     |
  |   |  Visible window (the only items actually in the DOM)    |     |
  |   |  item 4021                                               |     |
  |   |  item 4022                                               |     |
  |   |  item 4023  <-- visible viewport                         |     |
  |   |  item 4024                                               |     |
  |   +--------------------------------------------------------+     |
  |                                                                   |
  |   ... (not-yet-scrolled-to items, not in the DOM) ...            |
  +----------------------------------------------------------------+
```

## 7. Dynamics

The trace below shows a user scrolling a large list, items being
recycled as they leave and enter the visible window.

```
Initial render

the list mounts with a scroll container sized for all 10,000 items
   |-- only the first handful of items, those within the initial
       visible viewport, are mounted as real DOM nodes
   |-- every other item's position is known and accounted for in the
       container's total height, but nothing else is mounted yet

User scrolls down

the visible window moves as the user scrolls
   |-- an item that has scrolled out of view at the top is unmounted,
       or its DOM node is recycled and repositioned for new content
   |-- a new item that has scrolled into view at the bottom is
       mounted, or an existing recycled node is repositioned and
       repopulated with that item's data

Scroll continues

the process repeats continuously as the user keeps scrolling
   |-- at any given moment, only the small number of items within, or
       slightly outside, the visible viewport are actually present in the
       DOM
   |-- the browser's scroll position and scrollbar size still
       correctly reflect the full 10,000-item list's true total
       height
```

## 8. Implementation variants

**Fixed-height virtualization.** Every item in the list has the same,
known height, letting the container calculate each item's position
with simple arithmetic, the simplest and most performant form of the
technique.

**Variable-height virtualization.** Items have different, but
individually measurable or estimable, heights, needing the container
to track or measure each item's actual size to correctly calculate
positions and the total scrolled height.

**Windowed grid virtualization.** The same underlying idea applied to
a two-dimensional grid rather than a single-column list, virtualizing
both the vertical and horizontal axes so only the cells within the
visible viewport are mounted.

**Overscan, rendering a small buffer beyond the visible viewport.** A
refinement where a small number of items slightly outside the visible
window are also kept mounted, so a fast scroll or a keyboard-driven
focus move does not produce a visible flash of empty space before the
next item mounts.

## 9. Known production uses

**TanStack Virtual's own documentation, defining the technique.**
TanStack Virtual's documentation states the core purpose directly.
"TanStack Virtual is a headless UI utility for virtualizing long
lists of elements." TanStack documentation, "Virtual, Introduction,"
https://tanstack.com/virtual/latest/docs/introduction, verified
2026-08-21.

**Web.dev's own guide, defining windowing and its performance
benefit.** Web.dev's article states the definition directly. "List
virtualization, the concept of only rendering what is visible to the
user. The number of elements that are rendered at first is a very
small subset of the entire list and the window of visible content
moves when the user continues to scroll." It names the direct
performance benefit. "This improves both the rendering and scrolling
performance of the list." Web.dev, "Virtualize long lists with
react-window,"
https://web.dev/articles/virtualize-long-lists-react-window, verified
2026-08-21.

## 10. Consequences

Positive.

- The DOM node count, and the corresponding style and layout cost,
  stays roughly constant regardless of the underlying data set's
  size, since only the visible window is ever actually mounted.
- Scrolling stays smooth for a genuinely large data set that would
  otherwise overwhelm the browser if every item were rendered at
  once, directly addressing the performance force named in dimension
  3.
- A list holding tens of thousands of items can be presented to the
  user with the same responsiveness as a list holding a handful of
  items, since the rendering cost is bounded by the viewport, not the
  data.

Negative.

- Calculating item positions, tracking scroll offset, and correctly
  sizing the container to match the full list's total height is a
  real amount of implementation bookkeeping a naive, fully rendered
  list does not need.
- Native browser find-in-page, full-page printing, and default
  screen-reader navigation only see the items currently mounted,
  degrading those specific behaviors unless the team deliberately
  addresses the gap.
- A poor estimate of item size in the variable-height variant can
  produce visible content jumping or an incorrect scrollbar position,
  since the technique depends directly on knowing or accurately
  estimating each item's size.

## 11. Failure modes and misuse

**Applying Virtual List to a list small enough that it was never
actually slow, adding real implementation complexity for no measured
benefit.** Symptom. The codebase carries the technique's full
position-calculation and recycling logic for a list that would have
rendered fine in full, with no actual performance problem it was
solving. Cause. Adopting the pattern because a list is technically
long, rather than because rendering it in full is measurably slow.
Fix. Reserve Virtual List for a list genuinely measured to cause a
performance problem when fully rendered, and render a small or
moderate list in full otherwise.

**Ignoring the accessibility gap the technique introduces, leaving
native browser find-in-page, full-page printing, and default
screen-reader navigation broken for the virtualized list.** Symptom.
A user searching the page with the browser's built-in find function,
printing the page, or moving through it with a screen reader in its
default mode cannot reach content that has scrolled out of the visible window
and is not currently mounted. Cause. Adopting the performance benefit
of the technique without deliberately addressing the browser-native
behaviors that assume every item is present in the DOM. Fix. Provide
an explicit alternative for these specific use cases, such as a
dedicated print view that renders the full list, or accept and
document the trade-off deliberately rather than leaving it as an
unnoticed gap.

**Estimating item heights inaccurately in the variable-height
variant, producing visible content jumping as the user scrolls.**
Symptom. The scroll position and scrollbar jump or jitter as the
user scrolls, since the container's calculated positions were based
on an estimate that did not match the items' actual, measured
heights once they rendered. Cause. Using a rough, static estimate for
item height instead of measuring the real, rendered height and
correcting the calculation once it is known. Fix. Measure each item's
actual rendered height once it mounts, and correct the container's
position calculations based on that real measurement rather than the
initial estimate alone.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Virtual List | Fully rendered list | Pagination | Infinite Scroll (without virtualization) |
|---|---|---|---|---|
| Rendering cost for a very large data set | Low, bounded by viewport | High, grows with data size | Low, only one page's worth is rendered at a time | High, grows unbounded as more pages append |
| Scroll performance at large data sizes | Strong | Weak, degrades as items accumulate | Not applicable, scrolling is bounded to one page | Weak, degrades over a long session as more content appends |
| Implementation complexity | Real, position calculation and recycling | Low, no special handling needed | Low to moderate, page-boundary logic only | Low to moderate, append logic only, no virtualization |
| Native browser find-in-page and printing | Weak, unless deliberately addressed | Strong, everything is present | Strong within a page, weak across pages | Weak, only appended content so far is present |
| Fit for a genuinely small list | Weak, unneeded overhead | Strong | Strong | Strong |

Reading of the table. Virtual List wins specifically for a genuinely
large, continuously scrollable data set where rendering cost and
scroll performance are measured to degrade without it. Infinite
Scroll without virtualization solves the loading problem but not the
rendering-cost problem, since it keeps appending fully rendered
content rather than recycling it, and eventually accumulates the
same performance problem Virtual List is built to avoid.

## 13. Related and incompatible patterns

- **Infinite Scroll.** A closely related, frequently combined pattern
  addressing a different half of the same problem, loading more data
  as the user approaches the end of what has been fetched, while
  Virtual List addresses the rendering cost of the data already
  loaded, however much of it there is.
- **Hooks.** The mechanism a modern implementation of Virtual List
  usually uses internally to track scroll position and manage the
  currently mounted window of items.
- **Atomic Design.** A complementary component-organization
  methodology, unrelated to the virtualization mechanism itself, that
  a team can still apply to the individual list-item components a
  Virtual List implementation renders.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing, fully rendered list that has
grown large enough to cause a measured performance problem.

1. Confirm the list's rendering, scrolling, or interaction
   performance has actually been measured to degrade, rather than
   assuming so because the list is technically long.
2. Determine whether the list's items have a fixed, known height, or
   a variable, measurable height, since this decides which
   implementation variant to use.
3. Introduce a scroll container sized to match the full list's total
   height, and a windowing mechanism that mounts only the items
   currently within, or slightly outside, the visible viewport.
4. Add an overscan buffer if fast scrolling or keyboard-driven focus
   movement produces a visible flash of empty space.
5. Deliberately address the accessibility and native-browser-behavior
   gap, such as providing a dedicated full-list print view, rather
   than leaving it as an unaddressed side effect.

Removing the pattern when it stops earning its place, most relevant
when the underlying list has genuinely shrunk small enough that the
original performance problem no longer exists.

1. Confirm the list's size has genuinely shrunk enough that rendering
   it in full no longer causes a measured performance problem, rather
   than assuming so without review.
2. Remove the virtualization's position-calculation and recycling
   logic, rendering every item directly.
3. Remove any special-cased accessibility or print-view workaround
   that existed specifically to compensate for the virtualization,
   since the fully rendered list no longer needs it.

## 15. Testing and verification

Easier because of the pattern.

- The position-calculation logic that decides which items should be
  mounted for a given scroll offset can be tested directly, as a pure
  function, independent of any actual DOM rendering.
- Because only a small, bounded number of items are ever mounted at
  once, a rendering test can assert the exact set of currently
  mounted items for a given scroll position, rather than needing to
  reason about a fully rendered tree that could be enormous.

Harder because of the pattern.

- Testing the actual scroll behavior, that items correctly mount and
  unmount as the user scrolls through a large data set, needs
  simulating scroll events and asserting the mounted set changes
  correctly at each step, rather than a single, static render
  assertion.
- Verifying the variable-height variant correctly measures and
  corrects for real item heights needs a test environment that can
  genuinely render and measure content, rather than working purely
  from a static, estimated size.

Techniques that apply.

- **Position-calculation unit tests.** Test the pure function that
  maps a scroll offset to the set of items that should currently be
  mounted, independent of any actual DOM rendering.
- **Scroll-simulation tests.** Simulate scrolling through a large data
  set and assert the mounted item set correctly updates at each
  distinct scroll position.
- **Height-estimation-correction tests.** For the variable-height
  variant, assert the container's calculated positions correctly
  adjust once an item's real, measured height differs from its
  initial estimate.
- **Accessibility fallback tests.** Assert the deliberate
  accessibility workaround, such as a dedicated print view, correctly
  presents the full list's content, independent of the virtualized
  scroll behavior.

## 16. Observability signals

Virtual List has a genuine runtime footprint, since it directly
governs how many DOM nodes a real user's browser actually holds while
scrolling a large list, so a dedicated production signal is honest
here.

What to record.

- The actual number of DOM nodes mounted for a given virtualized
  list at any moment, since a count that grows well past the expected
  visible-window size signals the recycling mechanism is not
  correctly unmounting items that have scrolled out of view.
- Scroll jank or dropped frames measured specifically during
  scrolling through a virtualized list, since a large data set that
  still produces jank despite virtualization signals either an
  inefficient per-item render or a position-calculation cost that has
  grown too expensive.

A healthy state. The mounted DOM node count for a virtualized list
stays close to its expected visible-window size regardless of how
large the underlying data set is, and scrolling stays smooth with no
measurable jank.

A failing state. A mounted node count that grows unexpectedly as the
user scrolls further into a large list, pointing at a recycling
mechanism failing to unmount items correctly, or measurable scroll
jank despite virtualization being in place, pointing at an expensive
per-item render or an inefficient position calculation.

## 17. Security and privacy implications

Virtual List is close to neutral for security, being a rendering and
performance technique rather than a data-handling one, and inventing
a dedicated attack surface here would be dishonest. One practical
implication is worth naming.

**Because a virtualized list only mounts the currently visible
window, any access-control or sensitivity check that should apply per
item must run when that item is actually mounted and rendered, not
only once at the point the full underlying data set is fetched,
since an item that is fetched but never mounted, or mounted only
later as the user scrolls, still needs the same per-item check applied
at render time as any other item.** Because it can be tempting to
assume a single, upfront access check on the full fetched data set is
sufficient, a team should confirm any per-item sensitivity or
access-control logic genuinely runs for every item at the point it is
actually rendered into the visible window, not only once when the
underlying data was first fetched, so a later change to what a user is
authorized to see is correctly reflected as items scroll into view.

## 18. References

1. TanStack documentation. "Virtual, Introduction".
   https://tanstack.com/virtual/latest/docs/introduction
   Verified 2026-08-21. Source of the defining sentence quoted in
   dimensions 1 and 9.
2. Web.dev. "Virtualize long lists with react-window".
   https://web.dev/articles/virtualize-long-lists-react-window
   Verified 2026-08-21. Source of the windowing definition and the
   performance-benefit quotes in dimensions 1, 2, and 9.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models the position
calculation and visible-window selection the way a fixed-height
virtualizer structures the concept, kept free of JSX and any specific
framework's package so the sample compiles as plain TypeScript.
Python shows the same conceptual split using a minimal,
framework-agnostic function that computes the visible item range for
a given scroll offset, since Python has no single dominant Virtual
List UI framework the way TypeScript has TanStack Virtual and
react-window. Swift shows the pattern using a minimal model where a
visible range is computed from a scroll offset and item height,
closely analogous to how virtualization is reasoned about in a
native table or collection view. Java, Go, and Rust are omitted,
since none has a dominant, idiomatic UI-component framework this
specifically frontend rendering pattern maps to as directly as
TypeScript and Swift do.

### TypeScript

```typescript
interface VisibleRange {
  startIndex: number;
  endIndex: number;
}

function computeVisibleRange(
  scrollOffset: number,
  viewportHeight: number,
  itemHeight: number,
  totalItems: number,
  overscan: number
): VisibleRange {
  const rawStart = Math.floor(scrollOffset / itemHeight);
  const rawEnd = Math.ceil((scrollOffset + viewportHeight) / itemHeight);

  const startIndex = Math.max(0, rawStart - overscan);
  const endIndex = Math.min(totalItems - 1, rawEnd + overscan);

  return { startIndex, endIndex };
}

function totalScrollHeight(totalItems: number, itemHeight: number): number {
  return totalItems * itemHeight;
}

const range = computeVisibleRange(40200, 400, 50, 10000, 2);
console.log("visible items:", range.startIndex, "to", range.endIndex);
console.log("total scroll height:", totalScrollHeight(10000, 50));
```

### Python

```python
from dataclasses import dataclass


@dataclass
class VisibleRange:
    start_index: int
    end_index: int


def compute_visible_range(
    scroll_offset: int,
    viewport_height: int,
    item_height: int,
    total_items: int,
    overscan: int,
) -> VisibleRange:
    raw_start = scroll_offset // item_height
    raw_end = -(-(scroll_offset + viewport_height) // item_height)

    start_index = max(0, raw_start - overscan)
    end_index = min(total_items - 1, raw_end + overscan)

    return VisibleRange(start_index=start_index, end_index=end_index)


def total_scroll_height(total_items: int, item_height: int) -> int:
    return total_items * item_height


if __name__ == "__main__":
    visible = compute_visible_range(40200, 400, 50, 10000, 2)
    print("visible items:", visible.start_index, "to", visible.end_index)
    print("total scroll height:", total_scroll_height(10000, 50))
```

### Swift

```swift
struct VisibleRange {
    let startIndex: Int
    let endIndex: Int
}

func computeVisibleRange(
    scrollOffset: Int,
    viewportHeight: Int,
    itemHeight: Int,
    totalItems: Int,
    overscan: Int
) -> VisibleRange {
    let rawStart = scrollOffset / itemHeight
    let rawEnd = Int(ceil(Double(scrollOffset + viewportHeight) / Double(itemHeight)))

    let startIndex = max(0, rawStart - overscan)
    let endIndex = min(totalItems - 1, rawEnd + overscan)

    return VisibleRange(startIndex: startIndex, endIndex: endIndex)
}

func totalScrollHeight(totalItems: Int, itemHeight: Int) -> Int {
    totalItems * itemHeight
}

let range = computeVisibleRange(
    scrollOffset: 40200,
    viewportHeight: 400,
    itemHeight: 50,
    totalItems: 10000,
    overscan: 2
)

print("visible items: " + String(range.startIndex) + " to " + String(range.endIndex))
print("total scroll height: " + String(totalScrollHeight(totalItems: 10000, itemHeight: 50)))
```
