---
name: Hydration Island
slug: hydration-island
family: 13-frontend-ui
category: Loading Strategy
aliases: [Client Directive, Selective Hydration, Partial Hydration Directive]
first_described: "Astro documentation, client directives"
maturity: established
related: [islands-architecture, code-splitting, virtual-list]
incompatible_with: []
verified: 2026-08-21
---

# Hydration Island

## 1. Name, aliases, and lineage

The canonical name is Hydration Island, the specific mechanism that
controls WHEN and WHETHER an individual island's JavaScript actually
hydrates, as distinct from the broader Islands Architecture that
decides WHICH parts of a page are islands in the first place. Astro's
own documentation states the mechanism directly. "You can tell Astro
exactly how and when to render each component. If that image carousel
is really expensive to load, you can attach a special client
directive that tells Astro to only load the carousel when it becomes
visible on the page."

The alias **Client Directive** names Astro's own specific syntax for
the mechanism, a directive attached to a component in markup.
**Selective Hydration** names the technique by its effect, choosing
which islands hydrate and under what condition. **Partial Hydration
Directive** distinguishes this per-island timing control from
Islands Architecture's broader structural decision about which parts
of a page are islands at all.

## 2. Problem and context

Even once a page has been structured into islands, a real choice
remains for each individual island, exactly when its JavaScript
should load and hydrate. An island positioned prominently at the top
of the page genuinely needs to become interactive as soon as possible,
while an island far down the page, one the user may never scroll to
in a given session, gains nothing from hydrating immediately and only
costs bandwidth and main-thread time doing so. A single, uniform
hydration timing for every island wastes resources on islands that do
not need to be interactive yet, or ever, in a given visit. Hydration
Island directives solve this by letting a developer declare, per
island, the specific condition, immediately, when the browser is
idle, when the island scrolls into view, when a media query matches,
or never on the server at all, under which that specific island's
JavaScript should actually load and hydrate.

## 3. Forces

The pattern balances the following competing pressures.

- **Prioritizing interactivity where it is genuinely needed first.**
  Favored. Astro's own documentation states the `client:load`
  directive's behavior directly. "Load and hydrate the component
  JavaScript immediately on page load," reserved for content that
  genuinely needs instant interactivity.
- **Deferring cost for content the user may never reach.** Favored.
  The `client:visible` directive "loads and hydrates the component
  JavaScript once the component has entered the user's viewport,"
  meaning an island far down the page never pays its hydration cost
  at all if the user never scrolls to it.
- **Avoiding competition with more critical initial work.** Favored.
  The `client:idle` directive "loads and hydrates the component
  JavaScript once the page is done with its initial load and the
  requestIdleCallback event has fired," letting lower-priority
  islands wait until the browser genuinely has spare capacity.
- **Choosing the correct directive for each island's actual
  importance.** In tension. The technique's entire benefit depends on
  a developer correctly judging which directive fits each island's
  real priority, and a mismatched choice, an above-the-fold
  interactive element deferred with `client:idle`, undermines the
  very interactivity the island exists to provide.

## 4. Applicability and non-applicability

Reach for Hydration Island directives when the following hold.

- The page is already structured into islands, and each island's
  actual priority for becoming interactive genuinely differs from the
  others.
- A specific island is expensive to hydrate and positioned somewhere
  the user may not immediately, or ever, scroll to, making a deferred
  or conditional directive a real, measured benefit.
- The team can correctly judge, and periodically re-verify, which
  directive genuinely matches each island's real interactivity needs.

Do NOT reach for Hydration Island directives in these cases, and the
reason matters more than the rule.

- **Every island on the page genuinely needs to be interactive
  immediately**, applying differentiated directives to islands that
  all genuinely need `client:load` behavior adds decision-making
  overhead with no real benefit over a simpler, uniform approach.
- **The specific directive chosen does not actually match the
  island's real priority**, deferring an above-the-fold, immediately
  needed interactive element with `client:idle` or `client:visible`
  makes it feel broken or unresponsive during the exact window a user
  is most likely to try to use it.
- **The page has not been structured into islands at all**, a
  hydration directive controls the timing of an already-identified
  island's hydration, and applying the concept without the underlying
  island structure in place first has nothing to attach the
  directive to.

## 5. Structure

A Hydration Island has two structural parts.

- **The island component**, the specific piece of interactive markup
  whose hydration timing is being controlled.
- **The directive**, the declared condition, immediate load, browser
  idle, viewport visibility, a media query match, or client-only with
  no server render at all, that determines when, or whether, the
  island's JavaScript actually loads and hydrates.

## 6. ASCII structure diagram

```
  Page with several islands, each with its own directive

  +----------------------------------------------------------+
  | <SearchBar client:load />         hydrates immediately       |
  |                                                              |
  | <NewsletterForm client:idle />    hydrates once the browser   |
  |                                    is idle after initial load |
  |                                                              |
  | <ImageCarousel client:visible />  hydrates once scrolled       |
  |                                    into the viewport            |
  |                                                              |
  | <SidebarToggle client:media="(max-width: 768px)" />          |
  |                                    hydrates only if the media   |
  |                                    query matches                |
  +----------------------------------------------------------+
```

## 7. Dynamics

The trace below shows a page load where each directive fires at a
different point.

```
Page loads

the page's static HTML, including every island's server-rendered
markup, is delivered and displayed immediately
   |-- the SearchBar's client:load directive fires immediately,
       hydrating it right away
   |-- the NewsletterForm and ImageCarousel remain unhydrated for now

Browser reaches idle

after the page's initial load work completes and the browser fires
its idle callback
   |-- the NewsletterForm's client:idle directive fires, hydrating
       it during otherwise unused browser capacity

User scrolls down

the user scrolls far enough that the ImageCarousel enters the
viewport
   |-- the client:visible directive fires at that moment, hydrating
       the carousel only now, having cost nothing until this point

Session ends without the user ever scrolling that far

if a different user never scrolls to the ImageCarousel at all
   |-- its client:visible directive never fires, and its hydration
       cost is entirely avoided for that session
```

## 8. Implementation variants

**Immediate hydration.** Astro's own `client:load` directive,
hydrating a component's JavaScript immediately on page load, reserved
for genuinely above-the-fold, immediately needed interactivity.

**Idle-time hydration.** The `client:idle` directive, deferring
hydration until the browser fires its idle callback after the page's
initial load work completes, suited to lower-priority interactive
elements.

**Visibility-triggered hydration.** The `client:visible` directive,
hydrating only once the component enters the viewport, well suited to
resource-heavy components positioned far down the page.

**Media-query-conditional hydration.** The `client:media` directive,
hydrating "once a certain CSS media query is met," useful for an
element, such as a mobile-only sidebar toggle, that only needs
interactivity under a specific screen condition.

**Client-only rendering.** The `client:only` directive, which
"skips HTML server rendering, and renders only on the client,"
for a component that genuinely cannot render usefully on the
server at all.

## 9. Known production uses

**Astro's own documentation, on the general mechanism.** Astro states
the directive mechanism directly. "You can tell Astro exactly how and
when to render each component. If that image carousel is really
expensive to load, you can attach a special client directive that
tells Astro to only load the carousel when it becomes visible on the
page." Astro, "Islands," https://docs.astro.build/en/concepts/islands/,
verified 2026-08-21.

**Astro's own documentation, on the specific directives and their
exact behavior.** Astro states each directive's behavior directly.
`client:load` will "load and hydrate the component JavaScript
immediately on page load." `client:idle` will "load and hydrate the
component JavaScript once the page is done with its initial load and
the requestIdleCallback event has fired." `client:visible` will "load
and hydrate the component JavaScript once the component has entered
the user's viewport." `client:only` "skips HTML server rendering, and
renders only on the client." Astro, "Directives reference,"
https://docs.astro.build/en/reference/directives-reference/, verified
2026-08-21.

## 10. Consequences

Positive.

- Interactivity is prioritized exactly where it is genuinely needed
  first, `client:load`'s immediate hydration reserved for content
  that actually needs instant interactivity.
- Resource-heavy or lower-priority islands defer their hydration
  cost, and a `client:visible` island the user never scrolls to never
  pays that cost at all for that session.
- Each directive's exact behavior is precisely, individually defined,
  letting a developer choose a specific timing strategy per island
  rather than accepting one uniform behavior for the whole page.

Negative.

- The technique's benefit depends entirely on choosing the correct
  directive for each island's real priority, and a mismatch,
  particularly deferring something genuinely urgent, actively
  degrades the experience rather than merely failing to help.
- Each island now carries an individual timing decision a developer
  must make and periodically re-verify as the page's actual content
  and usage patterns evolve.
- `client:only` skips server rendering entirely, meaning a component
  using it shows no content at all until its client-side JavaScript
  has loaded, a real trade-off for whatever content that component
  would otherwise have shown.

## 11. Failure modes and misuse

**Deferring an above-the-fold, immediately needed interactive
element with `client:idle` or `client:visible`.** Symptom. A user who
tries to interact with the element right away finds it unresponsive,
since its hydration has been deferred to a later point the user's
actual behavior does not match. Cause. Applying a deferred directive
to an island without confirming its real, actual priority matches
that deferral. Fix. Use `client:load` for genuinely above-the-fold,
immediately needed interactive elements, reserving deferred
directives for content whose real priority is genuinely lower.

**Applying `client:idle` or `client:visible` uniformly to every
island on the page regardless of each one's actual priority.**
Symptom. The page's overall interactivity feels inconsistent and
unpredictable, some elements work immediately by coincidence of
timing while others that are equally important lag behind. Cause.
Treating deferred hydration as a default best practice to apply
everywhere, rather than a deliberate choice made per island based on
its actual, real priority. Fix. Evaluate each island's genuine
priority individually, choosing the directive that matches its real
interactivity needs rather than applying one directive uniformly
across the page.

**Using `client:only` for a component that could usefully render
useful content on the server.** Symptom. The user sees nothing at all
where that component should be until its client-side JavaScript has
fully loaded, a worse experience than a server-rendered version that
becomes interactive later would have provided. Cause. Reaching for
`client:only` as a default for any client-heavy component, rather
than reserving it for the case where server rendering genuinely
cannot produce useful output at all. Fix. Prefer a directive that
still server-renders the component's initial markup, `client:load`,
`client:idle`, or `client:visible`, reserving `client:only` for a
component that genuinely has no useful server-rendered
representation.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Hydration Island directives | Uniform, whole-page hydration | Manual, hand-rolled lazy loading |
|---|---|---|---|
| Prioritizing genuinely urgent interactivity first | Strong, via `client:load` on the correct islands | Weak, everything hydrates at once regardless of priority | Moderate, but requires building the prioritization logic by hand |
| Deferring cost for content the user may not reach | Strong, via `client:visible` and `client:idle` | Not applicable, everything hydrates immediately | Strong, but with more implementation effort |
| Precision matching each island's real need | Strong, five distinct, well-defined directive behaviors | Not applicable, one uniform behavior for the whole page | Strong, but the developer must build each distinct behavior |
| Ease of adoption and correctness | Moderate, choosing the right directive per island needs judgment | Strong, nothing to decide | Weak, hand-rolled logic risks its own bugs |

Reading of the table. Hydration Island directives win specifically
when a page's islands genuinely differ in priority, and a
well-supported framework already provides the distinct timing
behaviors a team would otherwise have to hand-build. A page whose
islands are all genuinely equally urgent gains little from
differentiating them, and hand-rolled lazy loading remains an option
when a framework's own directive vocabulary does not cover a
genuinely needed, more specific timing condition.

## 13. Related and incompatible patterns

- **Islands Architecture.** The broader structural pattern this
  directive mechanism operates within, deciding which parts of a page
  are islands in the first place, while Hydration Island directives
  decide when each of those already-identified islands actually
  hydrates.
- **Code Splitting.** The underlying mechanism a hydration directive
  frequently relies on, since deferring an island's hydration
  usually means deferring the fetch of that island's own,
  separately split JavaScript chunk as well.
- **Virtual List.** A resource-heavy island positioned far down a
  long, scrollable page is a natural candidate for both
  `client:visible` hydration and virtualized rendering, addressing
  the loading and the rendering half of the same long-list
  performance concern.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing islands-architecture page whose
islands currently all hydrate with the same, uniform timing.

1. Survey the page's existing islands and assess each one's genuine,
   real priority for becoming interactive, distinguishing immediately
   needed content from lower-priority or rarely reached content.
2. For a genuinely immediately needed island, apply an immediate
   hydration directive.
3. For a lower-priority island, apply an idle-time directive, letting
   it hydrate only once the browser has spare capacity after the
   page's initial load.
4. For a resource-heavy island positioned far down the page, apply a
   visibility-triggered directive, deferring its cost until the user
   actually scrolls to it.
5. Measure the resulting page's actual interactivity timing and
   resource usage against the pre-change baseline, confirming each
   directive choice produced a genuine improvement.

Removing the pattern when it stops earning its place, most relevant
when a page's islands have genuinely converged toward similar,
equally urgent priority.

1. Confirm, rather than assume, that the page's islands no longer
   genuinely differ enough in priority to justify differentiated
   directives.
2. Apply a single, uniform hydration directive across the
   now-similar-priority islands.
3. Confirm the resulting page's interactivity timing remains
   acceptable without the differentiated directives.

## 15. Testing and verification

Easier because of the pattern.

- A test can assert a specific island's JavaScript has not yet been
  fetched or hydrated at initial page load when its directive defers
  that hydration, directly verifying the deferred behavior the
  directive is meant to provide.
- Because each directive's behavior is precisely, individually
  defined by the framework, testing a specific island's hydration
  timing means asserting against a well-documented, framework-owned
  contract rather than a custom, hand-built timing mechanism.

Harder because of the pattern.

- Verifying a `client:visible` island's hydration timing needs
  simulating a real or realistic scroll and viewport intersection,
  rather than a simple, immediate render assertion.
- Confirming a `client:idle` island's hydration timing needs
  simulating, or waiting for, the browser's actual idle callback
  behavior, which does not fire on a fixed, easily mocked schedule
  the way a simple timer would.

Techniques that apply.

- **Initial-load hydration state assertions.** Assert which islands
  have and have not hydrated immediately after page load, confirming
  deferred islands genuinely have not yet hydrated.
- **Simulated viewport intersection tests.** Simulate scrolling a
  `client:visible` island into the viewport and assert its hydration
  occurs at that specific point, not before.
- **Simulated idle-callback tests.** Trigger, or wait for, the
  browser's idle callback in a test environment and assert a
  `client:idle` island hydrates at that point.
- **Real-device interactivity measurement.** Measure the actual time
  to interactive for each differentiated island on a realistically
  constrained device, confirming the directive choices produce the
  prioritization the team intended.

## 16. Observability signals

Hydration Island directives directly govern real, measurable
hydration timing for a real user's browser, so a dedicated production
signal is honest and expected here.

What to record.

- The actual time each island takes to become interactive, broken
  down by its assigned directive, since an immediately loaded island
  taking noticeably longer than expected to hydrate points at a
  genuine performance regression in that specific island.
- The share of `client:visible` islands that genuinely never
  hydrate in a typical session, since a high share confirms the
  directive is correctly avoiding wasted cost, and a low share may
  indicate the island was misjudged as low-priority when users
  actually reach it often.

A healthy state. Immediately loaded islands become interactive
quickly and consistently, deferred islands hydrate at their intended
trigger point, and a real share of `client:visible` islands
never pay their hydration cost at all because users genuinely do not
scroll to them.

A failing state. An island assigned an immediate directive takes
noticeably longer than expected to become interactive, pointing at a
regression in that island's own code, or a `client:visible` island
that was assumed low-priority is reached by nearly every session,
suggesting its directive choice should be reconsidered toward a more
immediate one.

## 17. Security and privacy implications

Hydration Island directives are close to neutral for security, being
a loading and hydration timing mechanism rather than a data-handling
one, and inventing a dedicated attack surface here would be
dishonest. One practical implication is worth naming.

**Because a `client:only` island skips server rendering entirely and
renders solely on the client, any access-control decision about
whether a given user should see that island's content at all must be
enforced by the data layer the island's client-side code actually
fetches from, never by the mere fact that the island is client-only
and therefore absent from the server-rendered HTML, since the
client-side JavaScript that would render it, and any bundled logic
determining what it fetches, is still fully present and inspectable
in the delivered page.** Choosing `client:only`, or any other
directive, changes when and how a component's markup appears, not
who is authorized to see the data that component ultimately renders,
and that authorization decision belongs to the server the client
fetches from, exactly as with any other client-rendered content.

## 18. References

1. Astro. "Islands".
   https://docs.astro.build/en/concepts/islands/
   Verified 2026-08-21. Source of the general directive-mechanism
   quote used in dimensions 1 and 9.
2. Astro. "Directives reference".
   https://docs.astro.build/en/reference/directives-reference/
   Verified 2026-08-21. Source of the individual directive definition
   quotes used in dimensions 3, 8, and 9.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models a directive-based
hydration scheduler the way Astro's own client directives structure
the concept, kept free of JSX and any specific framework's package so
the sample compiles as plain TypeScript. Python shows the conceptual
shape of the same directive-and-trigger logic using a minimal,
framework-agnostic implementation, since Python has no browser
runtime and therefore no single dominant hydration-directive
implementation the way TypeScript has Astro's own client directives.
Swift shows the same conceptual shape using a minimal model, analogous
to how a native app might defer initializing a specific, expensive
view controller until it actually scrolls into view or the system
signals idle capacity. Java, Go, and Rust are omitted, since none has
a dominant, idiomatic browser-facing islands framework this
specifically hydration-timing pattern maps to as directly as
TypeScript does.

### TypeScript

```typescript
type HydrationDirective = "load" | "idle" | "visible" | "media" | "only";

interface IslandDeclaration {
  name: string;
  directive: HydrationDirective;
  mediaQuery?: string;
}

function hydrateIsland(island: IslandDeclaration): void {
  console.log("hydrating island:", island.name, "via directive:", island.directive);
}

class HydrationScheduler {
  scheduleLoad(island: IslandDeclaration): void {
    hydrateIsland(island);
  }

  scheduleIdle(island: IslandDeclaration): void {
    console.log("deferring", island.name, "until browser idle");
    hydrateIsland(island);
  }

  scheduleVisible(island: IslandDeclaration): void {
    console.log("deferring", island.name, "until scrolled into view");
    hydrateIsland(island);
  }

  scheduleMedia(island: IslandDeclaration): void {
    if (island.mediaQuery) {
      console.log("deferring", island.name, "until media query matches:", island.mediaQuery);
    }
    hydrateIsland(island);
  }
}

const scheduler = new HydrationScheduler();

scheduler.scheduleLoad({ name: "SearchBar", directive: "load" });
scheduler.scheduleIdle({ name: "NewsletterForm", directive: "idle" });
scheduler.scheduleVisible({ name: "ImageCarousel", directive: "visible" });
scheduler.scheduleMedia({ name: "SidebarToggle", directive: "media", mediaQuery: "(max-width: 768px)" });
```

### Python

```python
from dataclasses import dataclass
from enum import Enum


class HydrationDirective(str, Enum):
    LOAD = "load"
    IDLE = "idle"
    VISIBLE = "visible"
    MEDIA = "media"
    ONLY = "only"


@dataclass
class IslandDeclaration:
    name: str
    directive: HydrationDirective
    media_query: str | None = None


def hydrate_island(island: IslandDeclaration) -> None:
    print(f"hydrating island: {island.name} via directive: {island.directive.value}")


class HydrationScheduler:
    def schedule_load(self, island: IslandDeclaration) -> None:
        hydrate_island(island)

    def schedule_idle(self, island: IslandDeclaration) -> None:
        print(f"deferring {island.name} until browser idle")
        hydrate_island(island)

    def schedule_visible(self, island: IslandDeclaration) -> None:
        print(f"deferring {island.name} until scrolled into view")
        hydrate_island(island)

    def schedule_media(self, island: IslandDeclaration) -> None:
        if island.media_query:
            print(f"deferring {island.name} until media query matches: {island.media_query}")
        hydrate_island(island)


if __name__ == "__main__":
    scheduler = HydrationScheduler()

    scheduler.schedule_load(IslandDeclaration(name="SearchBar", directive=HydrationDirective.LOAD))
    scheduler.schedule_idle(IslandDeclaration(name="NewsletterForm", directive=HydrationDirective.IDLE))
    scheduler.schedule_visible(IslandDeclaration(name="ImageCarousel", directive=HydrationDirective.VISIBLE))
    scheduler.schedule_media(
        IslandDeclaration(name="SidebarToggle", directive=HydrationDirective.MEDIA, media_query="(max-width: 768px)")
    )
```

### Swift

```swift
enum HydrationDirective: String {
    case load
    case idle
    case visible
    case media
    case only
}

struct IslandDeclaration {
    let name: String
    let directive: HydrationDirective
    let mediaQuery: String?
}

func hydrateIsland(_ island: IslandDeclaration) {
    print("hydrating island: " + island.name + " via directive: " + island.directive.rawValue)
}

final class HydrationScheduler {
    func scheduleLoad(_ island: IslandDeclaration) {
        hydrateIsland(island)
    }

    func scheduleIdle(_ island: IslandDeclaration) {
        print("deferring " + island.name + " until browser idle")
        hydrateIsland(island)
    }

    func scheduleVisible(_ island: IslandDeclaration) {
        print("deferring " + island.name + " until scrolled into view")
        hydrateIsland(island)
    }

    func scheduleMedia(_ island: IslandDeclaration) {
        if let mediaQuery = island.mediaQuery {
            print("deferring " + island.name + " until media query matches: " + mediaQuery)
        }
        hydrateIsland(island)
    }
}

let scheduler = HydrationScheduler()

scheduler.scheduleLoad(IslandDeclaration(name: "SearchBar", directive: .load, mediaQuery: nil))
scheduler.scheduleIdle(IslandDeclaration(name: "NewsletterForm", directive: .idle, mediaQuery: nil))
scheduler.scheduleVisible(IslandDeclaration(name: "ImageCarousel", directive: .visible, mediaQuery: nil))
scheduler.scheduleMedia(IslandDeclaration(name: "SidebarToggle", directive: .media, mediaQuery: "(max-width: 768px)"))
```
