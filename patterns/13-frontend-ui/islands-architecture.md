---
name: Islands Architecture
slug: islands-architecture
family: 13-frontend-ui
category: Rendering Strategy
aliases: [Component Islands, Partial Hydration]
first_described: "Katie Sylor-Miller, 2019, named by Jason Miller, August 2020"
maturity: established
related: [server-components, progressive-enhancement, hooks]
incompatible_with: []
verified: 2026-08-21
---

# Islands Architecture

## 1. Name, aliases, and lineage

The canonical name is Islands Architecture, a rendering strategy
where a page is served as static HTML with small, independently
interactive regions, the islands, hydrated with JavaScript, while the
rest of the page ships no JavaScript at all. Jason Miller, the
creator of Preact, credits the pattern's naming to Etsy's frontend
architect. "To the best of my knowledge, the 'Component Islands'
pattern was coined by Etsy's frontend architect Katie Sylor-Miller
during a meeting we had in 2019." Miller's own 2020 post, which
popularized the term more broadly, defines the idea directly.
"Render HTML pages on the server, and inject placeholders or slots
around highly dynamic regions."

The alias **Component Islands** is the original name Sylor-Miller
used for the pattern. **Partial Hydration** is the more technical,
mechanism-focused name for the same idea, describing what actually
happens at runtime, only the interactive regions are hydrated,
rather than the whole page.

## 2. Problem and context

A single-page application that hydrates its entire page as one
monolithic JavaScript bundle ships and executes JavaScript for every
part of the page, including large static regions such as an article's
body text or a marketing page's hero section that never need
interactivity at all. Since JavaScript is among the slowest assets to
download, parse, and execute per byte, shipping a full framework
runtime and hydrating an entire page for the sake of one small
interactive widget, a like button or a comment form, wastes a real
amount of the browser's time on work the page did not need. Islands
Architecture solves this by rendering the page as static HTML by
default and marking only the specific, genuinely interactive regions
as islands, so JavaScript is downloaded, parsed, and hydrated only
for the parts of the page that actually need it.

## 3. Forces

The pattern balances the following competing pressures.

- **Minimizing JavaScript shipped to the browser.** Favored. A page
  built from islands ships JavaScript only for its explicitly marked
  interactive regions, rather than for the entire page, directly
  addressing the cost named in dimension 2.
- **Fast initial page load.** Favored. Because most of the page is
  static HTML with no JavaScript to download or execute, the page can
  become visible and readable before any framework runtime loads at
  all.
- **Cross-island coordination and shared state.** Sacrificed by
  default. Because each island hydrates independently, sharing state
  between two islands on the same page needs a deliberate mechanism,
  such as a shared store or custom events, that a single, fully
  hydrated application would not need to think about.
- **Framework flexibility per island.** Favored in some
  implementations. Because each island hydrates independently, a page
  can mix islands built with different frameworks, a React island next
  to a Vue island, something a single, fully hydrated application
  cannot do.

## 4. Applicability and non-applicability

Reach for Islands Architecture when the following hold.

- The page is predominantly static content, an article, a marketing
  page, a documentation site, with only a small number of genuinely
  interactive widgets scattered through it.
- Minimizing the JavaScript shipped to the browser and the resulting
  initial load time matters enough to justify designing the page
  around explicit islands rather than one uniform, fully hydrated
  application.
- The interactive regions on the page are largely independent of one
  another, so the cross-island coordination cost named in dimension 3
  stays manageable.

Do NOT reach for Islands Architecture in these cases, and the reason
matters more than the rule.

- **The application is genuinely a single-page application with deep,
  pervasive interactivity across the whole page**, such as a design
  tool or a spreadsheet, where nearly every region needs to be
  interactive anyway, and the static-by-default model offers little
  benefit over a fully hydrated application.
- **The interactive regions of the page are tightly coupled and share
  a real amount of state**, needing frequent, low-latency
  coordination between islands adds a real amount of state-sharing
  ceremony a single hydrated tree would not need.
- **The team has no framework or tooling support for the pattern**,
  hand-rolling island boundaries and selective hydration without a
  framework such as Astro that supports it directly is a real amount
  of infrastructure work most teams should not take on themselves.

## 5. Structure

Islands Architecture has three structural parts.

- **The static shell**, the page's HTML, rendered on the server or at
  build time, that ships with no JavaScript and needs no hydration.
- **Islands**, explicitly marked regions of the page, each an
  independent, self-contained interactive component, hydrated with
  its own JavaScript.
- **Hydration directives**, the explicit signal, such as a directive
  naming when or how eagerly an island hydrates, controlling whether
  an island hydrates immediately, when it becomes visible, or only
  when the browser is idle.

## 6. ASCII structure diagram

```
  +--------------------------------------------------------------+
  |  Static HTML shell (no JavaScript, server rendered)          |
  |                                                                |
  |   +----------------+          +----------------+             |
  |   |  Island A       |          |  Island B       |             |
  |   |  Like button     |          |  Comment form    |             |
  |   |  (hydrated)      |          |  (hydrated)      |             |
  |   +----------------+          +----------------+             |
  |                                                                |
  |   Static article body, static footer, static navigation      |
  |   (no JavaScript shipped for any of this)                    |
  +--------------------------------------------------------------+
```

## 7. Dynamics

The trace below shows a page with two islands loading in the
browser, each hydrating independently.

```
Initial page load

the browser receives the static HTML shell
   |-- the article body, navigation, and footer render immediately,
       with no JavaScript to download or execute
   |-- Island A's markup, a like button, is present in the HTML but
       not yet interactive
   |-- Island B's markup, a comment form, is present in the HTML but
       not yet interactive

Selective hydration

Island A's hydration directive says hydrate immediately
   |-- Island A's JavaScript is downloaded and executed
   |-- Island A becomes interactive, independent of Island B

Island B's hydration directive says hydrate when visible
   |-- the browser has not yet scrolled Island B into view
   |-- Island B's JavaScript is not downloaded yet

User scrolls the page

Island B enters the viewport
   |-- Island B's hydration directive condition is now met
   |-- Island B's JavaScript is downloaded and executed
   |-- Island B becomes interactive, independent of Island A
```

## 8. Implementation variants

**Astro's client directives.** A framework-level implementation where
a component is rendered to static HTML by default, and a component
author explicitly opts a specific component into hydration with a
directive naming the timing, immediately on load, when the component
becomes visible, or when the browser is idle.

**Astro's server islands.** A complementary variant where a region of
the page is deferred and rendered separately on the server, letting
that region's dynamic, server-generated content be streamed in
without blocking the rest of the static page's initial render.

**Hand-rolled selective hydration.** A team implementing the same
concept without a dedicated framework, manually marking specific DOM
regions for hydration and writing the JavaScript that attaches
interactivity to only those regions, the approach the pattern's
original 2019 and 2020 descriptions were reasoning about before
framework-level support existed.

**Resumability as a related but distinct approach.** A different
technique, used by some newer frameworks, that avoids re-executing
component logic on hydration entirely by serializing the application's
state on the server and resuming it in the browser, addressing the
same JavaScript-cost problem through a different mechanism than
islands.

## 9. Known production uses

**Jason Miller's 2020 post, popularizing and defining the pattern.**
Miller's post states the core idea directly. "Render HTML pages on
the server, and inject placeholders or slots around highly dynamic
regions." Miller also credits the pattern's origin, writing that "the
'Component Islands' pattern was coined by Etsy's frontend architect
Katie Sylor-Miller during a meeting we had in 2019." Jason Miller,
"Islands Architecture," https://jasonformat.com/islands-architecture/,
verified 2026-08-21.

**Astro's own documentation, describing its islands implementation.**
Astro's documentation describes Islands Architecture as a frontend
pattern where most of a page renders as static HTML, with smaller
islands of JavaScript added only where a component is explicitly
marked interactive, using client directives such as loading a
component's JavaScript immediately or only once the component becomes
visible in the viewport. Astro documentation, "Astro Islands,"
https://docs.astro.build/en/concepts/islands/, verified 2026-08-21.

## 10. Consequences

Positive.

- A page ships JavaScript only for its explicitly marked interactive
  islands, directly reducing the amount of JavaScript the browser
  must download, parse, and execute compared to a fully hydrated
  application.
- Most of the page becomes visible and readable as static HTML before
  any framework runtime loads at all, improving perceived and actual
  load performance.
- Different islands on the same page can be built with different
  frameworks, since each island hydrates independently, which a
  single, fully hydrated application tree cannot support.

Negative.

- Sharing state between two islands on the same page needs a
  deliberate mechanism, such as a shared store or custom browser
  events, that a single, fully hydrated application tree would not
  need to think about at all.
- An application with pervasive, deep interactivity across nearly the
  entire page gains little from the static-by-default model, since
  almost everything would need to be marked as an island anyway.
- Implementing the pattern well usually depends on framework-level
  support, such as Astro's client directives, and hand-rolling
  selective hydration without that support is a real amount of
  infrastructure work.

## 11. Failure modes and misuse

**Marking every component on the page as an island, defeating the
purpose of the pattern.** Symptom. The page ships nearly as much
JavaScript as a fully hydrated application would have, since almost
every region was marked interactive, and the expected performance
improvement from the static-by-default model never materializes.
Cause. Applying the island directive reflexively to every component
rather than reserving it for regions that are genuinely interactive.
Fix. Audit which regions of the page truly need interactivity, and
mark only those as islands, leaving everything else as plain static
HTML.

**Building two islands that silently depend on shared state with no
explicit coordination mechanism between them.** Symptom. Interacting
with one island fails to update another island on the same page that
should have reflected the change, since the two islands hydrated
independently and have no shared state by default. Cause. Assuming
islands on the same page can communicate the way two components in a
single hydrated tree would, when each island is genuinely isolated
unless a coordination mechanism is deliberately added. Fix. Introduce
an explicit shared mechanism, a small shared store or custom browser
events, for any state that genuinely needs to be shared between
islands, rather than assuming implicit coordination.

**Choosing an eager hydration directive for an island that is rarely
seen or rarely interacted with.** Symptom. The page's initial load
still ships and executes a real amount of JavaScript for an island
far below the fold that most visitors never scroll to, undermining
the pattern's load-time benefit for exactly the visitors who leave
before scrolling. Cause. Defaulting every island to eager, load time
hydration instead of choosing a directive matched to when the island
actually needs to become interactive. Fix. Choose the hydration
timing deliberately per island, using a visibility or idle-time
directive for anything not needed immediately, reserving eager
hydration for genuinely above-the-fold, immediately needed
interactivity.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Islands Architecture | Fully hydrated SPA | Server Components | Progressive Enhancement |
|---|---|---|---|---|
| JavaScript shipped for static content | Minimal, only marked islands | High, the whole tree hydrates | Minimal, server-rendered parts ship none | Minimal, enhancement layered on top of working HTML |
| Cross-region shared state | Needs a deliberate mechanism | Simple, one shared tree | Needs a deliberate mechanism, similar to islands | Rarely applicable, minimal shared client state |
| Fit for deep, pervasive interactivity | Weak, most of the page ends up as islands anyway | Strong | Moderate, depends on how much stays server rendered | Weak, the model favors simple enhancement |
| Mixing frameworks on one page | Strong, each island is independent | Not applicable, single framework tree | Rarely applicable | Rarely applicable |
| Initial load performance for mostly static pages | Strong | Weak | Strong | Strong |

Reading of the table. Islands Architecture wins specifically for
pages that are predominantly static with a small number of genuinely
independent interactive regions. A deeply, pervasively interactive
application such as a design tool gains little from it, since nearly
every region would end up marked as an island regardless.

## 13. Related and incompatible patterns

- **Server Components.** A related, complementary approach to
  reducing client-side JavaScript by rendering as much of the
  component tree as possible on the server, often combined with
  islands to hydrate only the small subset of components that
  genuinely need client interactivity.
- **Progressive Enhancement.** A closely related philosophy, building
  a working experience from plain HTML first and layering
  interactivity on top, which Islands Architecture can be seen as a
  modern, component-scoped implementation of.
- **Hooks.** The mechanism a given island's interactive component is
  frequently implemented with internally, independent of the islands
  pattern itself, which governs how the component is hydrated rather
  than how its internal state is managed.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a predominantly static site or page currently
shipped as one fully hydrated single-page application.

1. Inventory the page's components and classify each one as either
   genuinely interactive or purely static content.
2. Confirm the project's rendering framework supports islands or
   selective hydration directly, adopting one that does if not.
3. Convert the page's static content to render with no client-side
   JavaScript, leaving only the genuinely interactive components as
   candidates for islands.
4. Mark each interactive component as an island, choosing a hydration
   directive, immediately, on visibility, or on idle, matched to when
   that specific component actually needs to become interactive.
5. Add an explicit coordination mechanism for any state that
   genuinely needs to be shared between two or more islands on the
   same page.

Removing the pattern when it stops earning its place, most relevant
when a page's interactivity has grown pervasive enough that nearly
every region ends up marked as an island anyway.

1. Confirm the page's interactivity has genuinely grown pervasive,
   rather than assuming so without review.
2. Migrate the page to a single, fully hydrated application tree,
   preserving each component's external behavior so consumers require
   minimal changes.
3. Remove the per-island hydration directives and any cross-island
   coordination mechanism once the migration to a single tree is
   complete.

## 15. Testing and verification

Easier because of the pattern.

- Each island is a self-contained, independently hydrated component,
  so it can be tested in isolation without needing to render the rest
  of the static page around it.
- Because most of the page ships no JavaScript at all, a test
  asserting the static shell renders correctly can run as a pure HTML
  assertion, with no need to simulate hydration or client-side
  behavior for that part of the page.

Harder because of the pattern.

- Testing that two islands genuinely coordinate correctly through
  their shared mechanism needs simulating both islands hydrating
  independently and then interacting through that mechanism, rather
  than testing a single component tree's internal state flow.
- Testing that a lazily hydrated island actually hydrates at the
  correct time, when it becomes visible or when the browser is idle,
  needs simulating that specific browser condition, which is more
  involved than testing a component that is simply always mounted.

Techniques that apply.

- **Isolated island component test.** Test each island's interactive
  behavior directly, independent of the static shell or any other
  island on the page.
- **Static shell rendering test.** Assert the page's static HTML
  renders correctly with no client-side JavaScript, confirming the
  content is genuinely usable before any hydration occurs.
- **Hydration timing test.** Simulate the specific condition, page
  load, visibility, or browser idle, that a given island's directive
  depends on, and assert the island becomes interactive only once
  that condition is met.
- **Cross-island coordination test.** Simulate an interaction on one
  island and assert the expected update reaches another island
  through their shared coordination mechanism.

## 16. Observability signals

Islands Architecture has a genuine runtime footprint, since it
directly governs how much JavaScript a real user's browser downloads
and executes, so a dedicated production signal is honest here.

What to record.

- The total JavaScript payload size actually shipped for a given
  page, and how that payload is distributed across individual
  islands, since a page whose payload grows disproportionate to its
  number of genuinely interactive regions signals islands that were
  marked unnecessarily or an island whose own bundle has grown too
  large.
- The elapsed time between a page's initial static render and a given
  island becoming interactive, since a long gap for an above-the-fold,
  immediately needed island signals a hydration directive mismatched
  to how the island is actually used.

A healthy state. The JavaScript payload shipped for a page stays
proportional to its actual number of interactive islands, and each
island becomes interactive close to when a real user is likely to
need it.

A failing state. A page's total JavaScript payload approaching what a
fully hydrated application would ship, pointing at islands marked too
liberally, or a visible, above-the-fold island taking a noticeably
long time to become interactive, pointing at a hydration directive
mismatched to how that island is actually used.

## 17. Security and privacy implications

Islands Architecture is close to neutral for security, being a
rendering and hydration strategy rather than a data-handling one, and
inventing a dedicated attack surface here would be dishonest. One
practical implication is worth naming.

**A static shell rendered on the server can leak sensitive data
directly into the page's HTML source if the server-rendering step
does not distinguish public content from private, per-user data the
way a properly scoped island's server-side data-fetching would.**
Because most of an islands-architecture page is static HTML generated
ahead of an individual user's request, or shared across many
requests, a team should confirm any genuinely user-specific or
sensitive data is fetched and rendered inside a properly scoped
server island rather than baked into a shared static shell, where it
could be served to the wrong user or cached and reused across
requests.

## 18. References

1. Jason Miller. "Islands Architecture".
   https://jasonformat.com/islands-architecture/
   Verified 2026-08-21. Source of the defining sentence and the 2019
   Etsy origin credit quoted in dimensions 1 and 9.
2. Astro documentation. "Astro Islands".
   https://docs.astro.build/en/concepts/islands/
   Verified 2026-08-21. Source of the client-directive implementation
   description quoted in dimension 9.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models a minimal island
registry, marking specific components for hydration with a directive,
the way a framework such as Astro structures the concept, kept free
of JSX and any specific framework's package so the sample compiles as
plain TypeScript. Python shows the same conceptual split using a
minimal, framework-agnostic static-page renderer that marks specific
regions for later hydration, since Python has no single dominant
islands-architecture UI framework the way TypeScript has Astro. Swift
shows the pattern using a minimal, analogous model where a static view
tree marks specific subviews as needing later activation, closely
analogous to how selective hydration is reasoned about in a native
context. Java, Go, and Rust are omitted, since none has a dominant,
idiomatic UI-component framework this specifically frontend rendering
pattern maps to as directly as TypeScript and Swift do.

### TypeScript

```typescript
type HydrationTiming = "load" | "visible" | "idle";

interface Island {
  id: string;
  html: string;
  hydrationTiming: HydrationTiming;
}

class StaticPage {
  private islands: Island[] = [];

  addIsland(island: Island): void {
    this.islands.push(island);
  }

  renderShell(staticContent: string): string {
    let shell = staticContent;
    for (const island of this.islands) {
      shell += "<div data-island=" + JSON.stringify(island.id) + ">";
      shell += island.html;
      shell += "</div>";
    }
    return shell;
  }

  islandsForTiming(timing: HydrationTiming): Island[] {
    return this.islands.filter((i) => i.hydrationTiming === timing);
  }
}

const page = new StaticPage();
page.addIsland({ id: "like-button", html: "<button>Like</button>", hydrationTiming: "load" });
page.addIsland({ id: "comment-form", html: "<form>Comment</form>", hydrationTiming: "visible" });

console.log(page.renderShell("<article>Static article content</article>"));
console.log("islands to hydrate immediately: " + page.islandsForTiming("load").length);
```

### Python

```python
from dataclasses import dataclass, field
from enum import Enum, auto


class HydrationTiming(Enum):
    LOAD = auto()
    VISIBLE = auto()
    IDLE = auto()


@dataclass
class Island:
    id: str
    html: str
    hydration_timing: HydrationTiming


@dataclass
class StaticPage:
    islands: list[Island] = field(default_factory=list)

    def add_island(self, island: Island) -> None:
        self.islands.append(island)

    def render_shell(self, static_content: str) -> str:
        shell = static_content
        for island in self.islands:
            shell += f'<div data-island="{island.id}">'
            shell += island.html
            shell += "</div>"
        return shell

    def islands_for_timing(self, timing: HydrationTiming) -> list[Island]:
        return [i for i in self.islands if i.hydration_timing == timing]


if __name__ == "__main__":
    page = StaticPage()
    page.add_island(Island(id="like-button", html="<button>Like</button>", hydration_timing=HydrationTiming.LOAD))
    page.add_island(Island(id="comment-form", html="<form>Comment</form>", hydration_timing=HydrationTiming.VISIBLE))

    print(page.render_shell("<article>Static article content</article>"))
    print("islands to hydrate immediately:", len(page.islands_for_timing(HydrationTiming.LOAD)))
```

### Swift

```swift
enum HydrationTiming {
    case load
    case visible
    case idle
}

struct Island {
    let id: String
    let html: String
    let hydrationTiming: HydrationTiming
}

final class StaticPage {
    private(set) var islands: [Island] = []

    func addIsland(_ island: Island) {
        islands.append(island)
    }

    func renderShell(staticContent: String) -> String {
        var shell = staticContent
        for island in islands {
            shell += "<div data-island=" + "'" + island.id + "'" + ">"
            shell += island.html
            shell += "</div>"
        }
        return shell
    }

    func islands(for timing: HydrationTiming) -> [Island] {
        islands.filter { island in
            switch (island.hydrationTiming, timing) {
            case (.load, .load), (.visible, .visible), (.idle, .idle):
                return true
            default:
                return false
            }
        }
    }
}

let page = StaticPage()
page.addIsland(Island(id: "like-button", html: "<button>Like</button>", hydrationTiming: .load))
page.addIsland(Island(id: "comment-form", html: "<form>Comment</form>", hydrationTiming: .visible))

print(page.renderShell(staticContent: "<article>Static article content</article>"))
print("islands to hydrate immediately: " + String(page.islands(for: .load).count))
```
