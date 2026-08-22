---
name: Infinite Scroll
slug: infinite-scroll
family: 13-frontend-ui
category: Loading Strategy
aliases: [Endless Scroll, Continuous Scroll]
first_described: "MDN, Intersection Observer API documentation"
maturity: established
related: [virtual-list, skeleton-and-suspense, optimistic-ui]
incompatible_with: []
verified: 2026-08-21
---

# Infinite Scroll

## 1. Name, aliases, and lineage

The canonical name is Infinite Scroll, a loading strategy where more
content is fetched and appended to a list automatically as the user
scrolls near its current end, so the user never has to explicitly
click through to a next page. MDN's own documentation for the Intersection
Observer API, the modern mechanism the pattern is usually built on,
names the pattern and its purpose directly. "Implementing infinite
scrolling websites, where more and more content is loaded and
rendered as you scroll, so that the user doesn't have to flip through
pages."

The alias **Endless Scroll** describes the same experience from the
user's perspective, a list that appears to have no fixed end. **Continuous
Scroll** is a more neutral, mechanism-focused variant of the same
name, emphasizing the uninterrupted loading rather than the
apparent endlessness of the result.

## 2. Problem and context

A traditional, paginated list requires the user to explicitly click a
next-page control and wait for a full page reload, or a partial page
update, to see more content, an interaction that interrupts the
otherwise continuous act of browsing a feed or a list. Detecting when
a user has scrolled near the end of the currently loaded content
historically needed repeatedly calling a layout-measuring function on
the main thread on every scroll event, an approach expensive enough
to cause its own performance problems on a long or frequently
scrolling page. Infinite Scroll solves the interaction problem by
loading and appending more content automatically as the user
approaches the end of what is currently loaded, removing the explicit
pagination click, and the modern implementation solves the detection
problem by using a dedicated browser API to observe when a sentinel
element near the bottom of the list enters the viewport, off the main
thread, rather than polling scroll position by hand.

## 3. Forces

The pattern balances the following competing pressures.

- **Uninterrupted browsing.** Favored. The user never has to stop and
  click a next-page control to see more content, keeping the act of
  scrolling through a feed continuous.
- **Efficient detection of when to load more.** Favored, when built on
  a modern mechanism. MDN's own documentation states the efficiency
  benefit directly, since the browser can observe the relevant
  intersection off the main thread rather than the page needing to
  poll scroll position and repeatedly measure layout by hand.
- **A reachable, bounded end to the content.** Sacrificed. A feed that
  keeps appending more content as the user scrolls has no natural
  stopping point the user can see in advance, removing the sense of
  progress or completion a paginated list, or even a visible total
  count, would otherwise provide.
- **Browser-native behaviors that assume a finite, discoverable page.**
  Sacrificed unless deliberately addressed. Full-page printing,
  bookmarking a specific scroll position, and reaching page content
  through the browser's own navigation history all assume a page with
  a defined, addressable extent, which a continuously appending feed
  does not naturally provide.

## 4. Applicability and non-applicability

Reach for Infinite Scroll when the following hold.

- The content is genuinely feed-like, where the user is browsing
  casually rather than searching for a specific, rememberable
  position, such as a social media timeline, a photo stream, or a
  news feed.
- Removing the friction of an explicit next-page click genuinely
  matters to the experience, and the absence of a visible end or
  total count is an acceptable trade for that continuity.
- The team can build the loading-trigger detection on an efficient,
  off-main-thread mechanism, rather than a scroll-position-polling
  approach that would reintroduce the performance cost the modern
  pattern exists to avoid.

Do NOT reach for Infinite Scroll in these cases, and the reason
matters more than the rule.

- **The user genuinely needs to reach, bookmark, or return to a
  specific position within the content**, such as a specific search
  result or a specific item in an ordered list, where a paginated,
  addressable structure serves the user better than a continuously
  appending feed with no stable position to return to.
- **The content includes a footer, a set of secondary links, or other
  content the user is meant to be able to reach**, a continuously
  appending feed can push that content indefinitely further away,
  making it functionally unreachable for a user who keeps scrolling.
- **The team cannot build the loading-trigger detection on an
  efficient mechanism**, falling back to polling scroll position and
  measuring layout on every scroll event reintroduces the exact
  performance cost the modern pattern is meant to avoid.

## 5. Structure

Infinite Scroll has three structural parts.

- **The content list**, the growing collection of items rendered so
  far, appended to as more content loads.
- **The sentinel**, a marker positioned near the end of the currently
  loaded content, whose entry into the viewport signals that more
  content should be requested.
- **The loading trigger**, the mechanism, usually the Intersection
  Observer API, that watches the sentinel and fires a callback when
  it becomes visible, initiating the request for the next batch of
  content.

## 6. ASCII structure diagram

```
  +----------------------------------------------------------------+
  |  Content list                                                    |
  |    item 1                                                        |
  |    item 2                                                        |
  |    ...                                                            |
  |    item 40                                                        |
  |  +--------------------------------------------------------+       |
  |  |  Sentinel (invisible marker, observed by the trigger)   |       |
  |  +--------------------------------------------------------+       |
  +----------------------------------------------------------------+
                              |
                              v
              sentinel enters the viewport as the user
              scrolls near the bottom of the loaded list
                              |
                              v
              loading trigger fires, requests the next batch
                              |
                              v
              new items 41 to 60 appended, sentinel repositioned
              at the new end of the list
```

## 7. Dynamics

The trace below shows a user scrolling a feed, the sentinel entering
the viewport, and a new batch of content loading and appending.

```
Initial load

the feed loads its first batch of items, items 1 through 40
   |-- a sentinel element is positioned right after item 40
   |-- the loading trigger begins observing the sentinel

User scrolls down

the user scrolls through the feed
   |-- as the user approaches item 40, the sentinel enters the
       viewport
   |-- the loading trigger's callback fires

Loading the next batch

the callback requests the next batch of content
   |-- items 41 through 60 are fetched and appended to the feed
   |-- the sentinel is repositioned to right after the new last item,
       item 60
   |-- the loading trigger continues observing the sentinel at its
       new position, able to fire again as the user continues
       scrolling
```

## 8. Implementation variants

**Intersection Observer based triggering.** The modern, efficient
implementation, using a dedicated browser API to observe a sentinel
element's visibility off the main thread, avoiding the cost of
polling scroll position and repeatedly measuring layout.

**Scroll-event polling.** An older implementation that listens
directly to scroll events and repeatedly measures the user's distance
from the bottom of the content, a real amount of main-thread cost per
scroll event compared to the Intersection Observer approach.

**Click-to-load-more as a manual fallback.** A variant that still
appends new content in place without a full page navigation, but
requires an explicit button click rather than triggering
automatically on scroll, trading some of the continuity benefit for a
more discoverable, user-initiated loading point.

**Bidirectional infinite scroll.** A variant that can load and append
content both above and below the currently visible window, letting a
user scroll upward into earlier content as well as downward into
newer content, common in a chat or messaging interface.

## 9. Known production uses

**MDN's own documentation, naming the pattern and its mechanism.**
MDN's Intersection Observer documentation states the use case
directly. "Implementing infinite scrolling websites, where more and
more content is loaded and rendered as you scroll, so that the user
doesn't have to flip through pages." MDN Web Docs, "Intersection
Observer API,"
https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API,
verified 2026-08-21.

**MDN's own documentation, on why the modern mechanism is efficient.**
The documentation explains the performance benefit directly. "The
Intersection Observer API lets code register a callback function that
is executed whenever a particular element enters or exits an
intersection with another element or the viewport," adding that
"sites no longer need to do anything on the main thread to watch for
this kind of element intersection, and the browser is free to
optimize the management of intersections as it sees fit." MDN Web
Docs, "Intersection Observer API,"
https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API,
verified 2026-08-21.

## 10. Consequences

Positive.

- The user never has to stop and click a next-page control to see
  more content, keeping the act of browsing a feed continuous.
- Built on the Intersection Observer API, the loading trigger runs
  off the main thread, avoiding the cost of a scroll-event-polling
  approach that would repeatedly measure layout on every scroll.
- The pattern fits the casual, browsing-oriented use case, a social
  feed, a photo stream, particularly well, where the user is not
  searching for a specific, rememberable position.

Negative.

- A continuously appending feed has no natural, visible stopping
  point, removing the sense of progress or total scope a paginated
  list or a visible total count would otherwise give the user.
- Content the user is meant to reach, such as a footer or a set of
  secondary links, can be pushed indefinitely further away as more
  content keeps appending, making it functionally unreachable for a
  user who keeps scrolling.
- Full-page printing, bookmarking a specific scroll position, and
  reaching content through the browser's own back and forward
  navigation all assume a page with a defined, addressable extent,
  which a continuously appending feed does not naturally provide.

## 11. Failure modes and misuse

**Implementing the loading trigger by polling scroll position and
repeatedly measuring layout on the main thread, instead of using an
efficient, off-main-thread mechanism.** Symptom. Scrolling through
the feed feels janky or unresponsive, particularly on a long session
with many appended batches, since each scroll event triggers a real
amount of main-thread layout measurement. Cause. Building the
detection mechanism by hand with scroll-event listeners rather than
using the Intersection Observer API MDN's own documentation names as
the efficient approach. Fix. Use the Intersection Observer API, or an
equivalent off-main-thread mechanism, to detect when the sentinel
enters the viewport, rather than polling scroll position by hand.

**Placing a footer or other important, reachable content directly
below a feed that continuously appends more items.** Symptom. A user
who wants to reach the footer, or a set of secondary links placed
below the feed, effectively cannot, since the feed keeps appending
new content and pushing that footer further away as long as they keep
scrolling. Cause. Assuming a continuously appending feed can coexist
below a fixed piece of layout the same way a bounded, paginated list
would. Fix. Place any content the user genuinely needs to reach
outside the continuously scrolling region entirely, such as in a
persistent header, a separate navigation area, or a dedicated page,
rather than below an unbounded feed.

**Applying Infinite Scroll to content the user genuinely needs to
return to a specific position within, such as a search
results list.** Symptom. A user who leaves the page and returns, or
goes back using the browser's own history, cannot easily return
to the specific item they were viewing, since the continuously
appended feed has no stable, addressable position to restore. Cause.
Applying the pattern to a use case that actually needs the
addressability a paginated or otherwise bounded structure provides.
Fix. Use pagination, or a bounded list with an explicit, addressable
position, for content the user genuinely needs to return to,
reserving Infinite Scroll for genuinely casual, browsing-oriented
feeds.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Infinite Scroll | Pagination | Click to load more | Virtual List (without infinite loading) |
|---|---|---|---|---|
| Uninterrupted browsing continuity | Strong | Weak, an explicit next-page click interrupts | Moderate, still an explicit click, but no full navigation | Not applicable, a different concern |
| Efficient loading-trigger detection | Strong, with Intersection Observer | Not applicable, loading is explicitly triggered | Not applicable, loading is explicitly triggered | Not applicable |
| A visible, reachable end or total count | Weak | Strong | Moderate, still discoverable via the explicit button | Strong, if the underlying data set is itself bounded |
| Reachability of content placed after the list, such as a footer | Weak, unless deliberately addressed | Strong | Moderate, better than automatic infinite scroll since loading is user-paced | Strong |
| Fit for a search-result or rememberable-position use case | Weak | Strong | Weak, same reason as infinite scroll | Not directly applicable, a rendering concern rather than a loading one |

Reading of the table. Infinite Scroll wins specifically for a
casual, browsing-oriented feed where continuity matters more than
addressability or a visible total scope. Pagination remains the
better fit whenever the user genuinely needs to reach, bookmark, or
return to a specific position, or when content placed after the list
needs to stay reliably reachable.

## 13. Related and incompatible patterns

- **Virtual List.** A closely related, frequently combined pattern
  addressing a different half of the same problem, keeping the
  rendering cost of the content already loaded bounded, while
  Infinite Scroll addresses when and how more content gets loaded in
  the first place.
- **Skeleton and Suspense.** A complementary pattern for the loading
  period each newly appended batch goes through, showing a
  skeleton-shaped placeholder for the incoming batch rather than an
  empty gap while it loads.
- **Optimistic UI.** A different response to a related feeling
  problem, prioritizing showing a predicted result of a user's own
  action immediately, rather than progressively loading more content
  the user did not directly request.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing paginated list whose explicit
next-page interaction the team wants to remove for a genuinely
casual, browsing-oriented use case.

1. Confirm the content is genuinely feed-like, and that the user does
   not need to reach, bookmark, or return to a specific position
   within it.
2. Move any content placed after the list, such as a footer or a set
   of secondary links, out of the continuously scrolling region
   entirely.
3. Add a sentinel element near the end of the currently loaded
   content, and wire an Intersection Observer, or an equivalent
   efficient mechanism, to watch it.
4. When the sentinel becomes visible, fetch and append the next batch
   of content, and reposition the sentinel to the new end of the
   list.
5. Add a loading skeleton for the period each newly requested batch
   spends in flight, so the appending itself does not feel abrupt.

Removing the pattern when it stops earning its place, most relevant
when the content has genuinely shifted toward a use case where
addressability matters more than continuity.

1. Confirm the content's use case has genuinely shifted toward
   needing addressable, rememberable positions, rather than assuming
   so without review.
2. Replace the continuously appending feed with a paginated structure,
   giving each page a stable, addressable position.
3. Remove the sentinel and its loading-trigger mechanism once the
   migration to pagination is complete.

## 15. Testing and verification

Easier because of the pattern.

- The loading-trigger logic itself, deciding whether the sentinel is
  currently intersecting the viewport and whether a load should fire,
  can be tested directly by simulating the intersection event,
  independent of any real scrolling.
- Because each batch of appended content is a discrete, well-defined
  unit, a test can assert the correct number of items are present
  after a given number of simulated load triggers, without needing to
  reason about a continuously growing, unbounded list.

Harder because of the pattern.

- Testing the actual user-facing scroll experience, that content
  genuinely appends smoothly as a real user scrolls, needs simulating
  real scroll behavior and viewport intersection together, rather
  than testing the trigger logic in isolation.
- Verifying content placed after the feed remains reachable needs a
  specific, deliberate test for that case, since the natural, easy
  path is to test only that the feed itself loads correctly, missing
  the surrounding layout concern entirely.

Techniques that apply.

- **Isolated trigger tests.** Simulate the sentinel entering the
  viewport directly and assert the loading callback fires correctly,
  independent of any real scroll behavior.
- **Batch-append tests.** Simulate a sequence of load triggers and
  assert the correct, expected content accumulates in the list after
  each one.
- **Reachability tests.** Specifically assert that content placed
  after the feed, such as a footer, remains reachable regardless of
  how much content has been appended to the feed above it.
- **Real-scroll integration tests.** Render the feed in a real or
  simulated browser environment and scroll through it, asserting the
  visible content and the loading behavior match what a real user
  would experience.

## 16. Observability signals

Infinite Scroll has a genuine runtime footprint, since it directly
governs when and how much content a real user's browser fetches and
renders as they scroll, so a dedicated production signal is honest
here.

What to record.

- The number of batches a typical session actually loads before the
  user stops scrolling or leaves the page, since this shapes how much
  content, and how much request volume, the pattern actually
  generates in practice.
- The latency between the sentinel becoming visible and the next
  batch of content actually appearing, since a growing gap signals
  either a slow underlying data-fetching endpoint or a
  loading-trigger mechanism that is not firing promptly.

A healthy state. The loading trigger fires promptly as the user
approaches the end of the currently loaded content, and each new
batch appears with a latency short enough that the user rarely, if
ever, scrolls past the end of loaded content before the next batch
arrives.

A failing state. A user frequently scrolling past the end of the
currently loaded content and seeing an empty gap before the next
batch appears, pointing at a loading trigger firing too late or an
underlying fetch that is too slow, or a request volume per session
that is unexpectedly high, pointing at a batch size that may be too
small for the pattern's actual usage pattern.

## 17. Security and privacy implications

Infinite Scroll is close to neutral for security, being a loading
and interaction strategy rather than a data-handling one, and
inventing a dedicated attack surface here would be dishonest. One
practical implication is worth naming.

**Because each newly loaded batch is a fresh request to the server,
the same access-control and rate-limiting logic that applies to any
other data-fetching endpoint must apply consistently to every batch
request an infinite-scrolling feed makes, since an attacker or an
automated script can trigger repeated batch loads far faster than a
real user scrolling would, effectively turning the loading endpoint
into an easily automatable enumeration or scraping surface if it is
not otherwise protected.** Because the continuous, automatic nature of
the pattern can make it easy to overlook that each appended batch is
still a real, individually authorizable request, a team should apply
the same authorization and rate-limiting discipline to the batch
endpoint that any other data-fetching API would need, rather than
assuming the feed's continuous framing makes it a lower-risk surface.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models the sentinel-based
loading trigger the way the Intersection Observer API structures the
concept, kept free of JSX and any specific framework's package so the
sample compiles as plain TypeScript. Python shows the same conceptual
split using a minimal, framework-agnostic feed manager that appends a
batch of items each time a load is triggered, since Python has no
single dominant Infinite Scroll UI framework the way TypeScript has
the Intersection Observer API. Swift shows the pattern using a
minimal model where a threshold-based check decides whether the next
batch should load, closely analogous to how infinite scrolling is
reasoned about in a native table or collection view. Java, Go, and
Rust are omitted, since none has a dominant, idiomatic UI-component
framework this specifically frontend loading pattern maps to as
directly as TypeScript and Swift do.

### TypeScript

```typescript
interface FeedItem {
  id: number;
  text: string;
}

function fetchNextBatch(batchNumber: number, batchSize: number): FeedItem[] {
  const start = batchNumber * batchSize;
  const items: FeedItem[] = [];
  for (let i = 0; i < batchSize; i++) {
    items.push({ id: start + i, text: "item " + (start + i) });
  }
  return items;
}

class InfiniteFeed {
  private items: FeedItem[] = [];
  private nextBatch = 0;
  private readonly batchSize: number;

  constructor(batchSize: number) {
    this.batchSize = batchSize;
  }

  loadInitial(): void {
    this.items = fetchNextBatch(this.nextBatch, this.batchSize);
    this.nextBatch += 1;
  }

  onSentinelVisible(): void {
    const nextItems = fetchNextBatch(this.nextBatch, this.batchSize);
    this.items = this.items.concat(nextItems);
    this.nextBatch += 1;
  }

  getItems(): FeedItem[] {
    return this.items;
  }
}

const feed = new InfiniteFeed(20);
feed.loadInitial();
feed.onSentinelVisible();
console.log("total items loaded:", feed.getItems().length);
```

### Python

```python
from dataclasses import dataclass, field


@dataclass
class FeedItem:
    id: int
    text: str


def fetch_next_batch(batch_number: int, batch_size: int) -> list[FeedItem]:
    start = batch_number * batch_size
    return [FeedItem(id=start + i, text=f"item {start + i}") for i in range(batch_size)]


@dataclass
class InfiniteFeed:
    batch_size: int
    items: list[FeedItem] = field(default_factory=list)
    next_batch: int = 0

    def load_initial(self) -> None:
        self.items = fetch_next_batch(self.next_batch, self.batch_size)
        self.next_batch += 1

    def on_sentinel_visible(self) -> None:
        next_items = fetch_next_batch(self.next_batch, self.batch_size)
        self.items.extend(next_items)
        self.next_batch += 1

    def get_items(self) -> list[FeedItem]:
        return self.items


if __name__ == "__main__":
    feed = InfiniteFeed(batch_size=20)
    feed.load_initial()
    feed.on_sentinel_visible()
    print("total items loaded:", len(feed.get_items()))
```

### Swift

```swift
struct FeedItem {
    let id: Int
    let text: String
}

func fetchNextBatch(batchNumber: Int, batchSize: Int) -> [FeedItem] {
    let start = batchNumber * batchSize
    return (0..<batchSize).map { offset in
        FeedItem(id: start + offset, text: "item " + String(start + offset))
    }
}

final class InfiniteFeed {
    private(set) var items: [FeedItem] = []
    private var nextBatch = 0
    private let batchSize: Int

    init(batchSize: Int) {
        self.batchSize = batchSize
    }

    func loadInitial() {
        items = fetchNextBatch(batchNumber: nextBatch, batchSize: batchSize)
        nextBatch += 1
    }

    func onSentinelVisible() {
        let nextItems = fetchNextBatch(batchNumber: nextBatch, batchSize: batchSize)
        items.append(contentsOf: nextItems)
        nextBatch += 1
    }
}

let feed = InfiniteFeed(batchSize: 20)
feed.loadInitial()
feed.onSentinelVisible()
print("total items loaded: " + String(feed.items.count))
```

## 18. References

1. MDN Web Docs. "Intersection Observer API".
   https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API
   Verified 2026-08-21. Source of the defining infinite-scrolling
   quote and the off-main-thread efficiency explanation quoted in
   dimensions 1, 3, and 9.
