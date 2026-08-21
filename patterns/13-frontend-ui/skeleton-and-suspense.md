---
name: Skeleton and Suspense
slug: skeleton-and-suspense
family: 13-frontend-ui
category: Loading Strategy
aliases: [Skeleton Screens, Suspense Boundaries, Loading Placeholders]
first_described: "React Suspense documentation"
maturity: canonical
related: [server-components, optimistic-ui, hooks]
incompatible_with: []
verified: 2026-08-21
---

# Skeleton and Suspense

## 1. Name, aliases, and lineage

The canonical name is Skeleton and Suspense, the combination of a
skeleton screen, a lightweight placeholder that visually approximates
the shape of the content still loading, with a suspense boundary, the
mechanism that declares where in a component tree that placeholder
should appear while its content is not yet ready. React's own
documentation defines the boundary mechanism directly. "`Suspense`
lets you display a fallback until its children have finished
loading." It defines the recommended shape of that fallback equally
directly. "A fallback is a lightweight placeholder view, such as a
loading spinner or skeleton."

The alias **Skeleton Screens** names the visual placeholder technique
on its own, independent of any particular framework's boundary
mechanism. **Suspense Boundaries** names React's specific declarative
mechanism for coordinating where a fallback appears. **Loading
Placeholders** is the more generic, framework-agnostic name for the
same underlying idea.

## 2. Problem and context

A component whose data has not yet loaded commonly renders nothing
at all, an empty region of the page, or a generic, centered spinner
with no relation to the content that will eventually appear there.
An empty region reads as broken or unfinished, and a generic spinner
gives the user no sense of what shape the eventual content will take
or how much of the page is still loading. This produces a jarring
transition once the real content finally appears, since the layout
shifts abruptly from an unrelated placeholder into structured
content. Skeleton and Suspense solve this together, a suspense
boundary declares where and when a fallback should appear as its
children's data loads, and a skeleton screen fills that fallback with
a placeholder shaped like the actual content, gray blocks
approximating where a heading, an image, and a paragraph will appear,
so the loading state visually previews the structure of what is
coming rather than either an empty gap or an unrelated spinner.

## 3. Forces

The pattern balances the following competing pressures.

- **Perceived loading speed.** Favored. A skeleton screen that
  visually previews the shape of the incoming content gives the user
  an immediate sense of structure and progress, making the wait feel
  shorter than an empty region or a generic spinner would, even when
  the actual load time is identical.
- **Declarative coordination of loading state across a tree.**
  Favored. A suspense boundary lets a team declare a single fallback
  for an entire subtree of components, rather than each individual
  component needing its own manually tracked loading flag and
  conditional render.
- **A layout shift when the real content finally arrives.** Sacrificed
  unless the skeleton's dimensions are deliberately matched to the
  real content's eventual size. A skeleton that does not closely
  match the real content's dimensions still produces a visible layout
  shift when the swap happens, undermining the smoothness the pattern
  exists to provide.
- **Coverage of every asynchronous loading path.** Sacrificed unless
  deliberately managed. React's own documentation states plainly that
  Suspense does not activate for data fetched inside an effect or an
  event handler, only for the specific mechanisms it supports, so a
  team must be deliberate about which loading paths a suspense
  boundary actually covers.

## 4. Applicability and non-applicability

Reach for Skeleton and Suspense when the following hold.

- A component or a subtree of components genuinely has an
  asynchronous loading period the user will notice, long enough that
  an empty region or an unstyled spinner would feel jarring or
  uninformative.
- The eventual content's shape is predictable enough in advance that a
  skeleton can be built to closely match its real dimensions, keeping
  the layout shift on arrival small.
- The team's framework and rendering strategy genuinely support a
  suspense-style boundary mechanism, or the team is prepared to
  hand-roll the equivalent loading-state coordination without one.

Do NOT reach for Skeleton and Suspense in these cases, and the reason
matters more than the rule.

- **The loading period is genuinely so brief that a placeholder would
  itself flash briefly and disappear**, adding its own jarring,
  distracting transition rather than smoothing one out.
- **The eventual content's shape is not predictable enough to build a
  skeleton that closely matches it**, a skeleton whose dimensions
  differ substantially from the real content still produces a real
  layout shift on arrival, undermining the pattern's core benefit.
- **The asynchronous loading happens inside an effect or an event
  handler the team's suspense mechanism does not cover**, applying a
  suspense boundary around a loading path it does not actually
  activate for gives a false sense of coverage while the real loading
  state goes unhandled.

## 5. Structure

Skeleton and Suspense has three structural parts.

- **The suspense boundary**, the declared point in a component tree
  where a fallback should render while its children's data is not yet
  ready.
- **The fallback**, the lightweight placeholder view rendered while
  the boundary's children are loading, ideally a skeleton shaped like
  the eventual content rather than a generic spinner.
- **The suspending component**, the actual component inside the
  boundary whose data-loading mechanism is one the suspense
  implementation recognizes and can coordinate against.

## 6. ASCII structure diagram

```
  <Suspense fallback={<ArticleSkeleton />}>
      |
      |-- while loading, renders:
      |     +--------------------------------+
      |     |  [====] gray block (title)     |
      |     |  [==========] gray block (img) |
      |     |  [========] gray block (text)  |
      |     +--------------------------------+
      |
      |-- once loaded, renders:
            +--------------------------------+
            |  How Suspense Works             |
            |  [ real article image ]         |
            |  Real paragraph content here.   |
            +--------------------------------+
```

## 7. Dynamics

The trace below shows a page requesting an article, the suspense
boundary rendering a skeleton, and the swap to real content once data
arrives.

```
Initial render

the page renders, reaching the ArticlePage's suspense boundary
   |-- the Article component inside the boundary begins fetching its
       data, using a mechanism the suspense implementation recognizes
   |-- since the data is not yet ready, the boundary renders its
       fallback, the ArticleSkeleton, immediately

Data arrives

the article's data finishes loading
   |-- the suspense implementation detects the Article component can
       now render
   |-- the boundary swaps from rendering the ArticleSkeleton fallback
       to rendering the real Article component with its loaded data

User perception

the user sees a structured, article-shaped placeholder immediately,
followed by the real content appearing in roughly the same layout
position, minimizing the visible layout shift compared to an empty
region suddenly filling with content
```

## 8. Implementation variants

**React's `<Suspense>` boundary with a skeleton fallback.** The
canonical, framework-level implementation, where a `<Suspense>`
component wraps a subtree and renders a skeleton component as its
`fallback` prop, coordinating automatically with the specific loading
mechanisms Suspense recognizes.

**Route-level suspense boundaries.** A boundary placed around an
entire route or page, rendering a full-page skeleton while the
route's data loads, rather than several smaller boundaries around
individual components within it.

**Nested, granular suspense boundaries.** Several smaller boundaries
placed around individual components within a page, letting each
piece of content reveal itself independently as its own data becomes
ready, rather than the whole page waiting on its slowest piece.

**Hand-rolled loading-state skeletons.** A team without a suspense
mechanism tracking a manual loading flag and conditionally rendering
a skeleton component in its place, achieving the same visual effect
without the declarative boundary coordination.

## 9. Known production uses

**React's own documentation, defining the Suspense boundary.** React's
documentation states the core mechanism directly. "`Suspense` lets
you display a fallback until its children have finished loading." It
recommends the specific shape of that fallback in its own words. "A
fallback is a lightweight placeholder view, such as a loading spinner
or skeleton." React documentation, "Suspense,"
https://react.dev/reference/react/Suspense, verified 2026-08-21.

**React's own documentation, on the boundary of what Suspense
actually covers.** The documentation states this limitation plainly,
noting Suspense recognizes lazy-loaded components, promise reading
through its `use` API, data streamed from Server Components, and
stylesheet loading, but explicitly does not detect data fetched
inside an effect or an event handler. React documentation,
"Suspense," https://react.dev/reference/react/Suspense, verified
2026-08-21.

## 10. Consequences

Positive.

- A skeleton screen that visually previews the shape of the incoming
  content makes a load feel faster to the user than an empty region
  or a generic spinner, even at an identical actual load time.
- A suspense boundary lets a team declare loading-state coordination
  for an entire subtree in one place, rather than each individual
  component needing its own manually tracked loading flag.
- A skeleton whose dimensions closely match the real content keeps
  the layout shift on arrival small, producing a visibly smoother
  transition than a mismatched placeholder or none at all.

Negative.

- Suspense recognizes only specific loading mechanisms, and
  explicitly does not detect data fetched inside an effect or an
  event handler, so a team must be deliberate about which loading
  paths a given boundary actually covers, or coverage gaps go
  unnoticed.
- A skeleton whose dimensions do not closely match the eventual real
  content still produces a real layout shift on arrival, undermining
  the smoothness benefit the pattern is meant to provide.
- Building and maintaining a skeleton component shaped like the real
  content is additional design and implementation work a plain
  spinner or an empty state would not need.

## 11. Failure modes and misuse

**Using a generic spinner as a suspense boundary's fallback instead
of a shaped skeleton, missing the pattern's actual perceived-speed
benefit.** Symptom. The loading state gives the user no sense of what
shape the eventual content will take, reproducing the same jarring,
uninformative wait a skeleton screen is meant to eliminate, even
though a suspense boundary is technically in place. Cause. Adopting
the boundary mechanism without the specific fallback content, a
shaped skeleton, that the pattern's real benefit depends on. Fix.
Build a skeleton component whose dimensions and rough shape match
the eventual real content, and use it as the boundary's fallback
rather than a generic spinner.

**Building a skeleton whose dimensions do not match the real
content's eventual size, producing a visible layout shift on
arrival.** Symptom. The page visibly jumps or reflows the moment the
real content replaces the skeleton, since the skeleton's placeholder
blocks were a different size than what actually rendered. Cause.
Building the skeleton without measuring or matching it against the
real content's typical dimensions. Fix. Size the skeleton's
placeholder elements to closely match the real content's typical
dimensions, verified against actual rendered content rather than
guessed.

**Wrapping a component in a suspense boundary while its actual data
fetching happens inside an effect or an event handler, a mechanism
Suspense does not detect.** Symptom. The boundary's fallback never
appears, or the component renders with incomplete data, since the
suspense mechanism has no visibility into the fetch happening inside
the effect or handler. Cause. Assuming a suspense boundary
automatically coordinates with any asynchronous operation inside its
subtree, when it in fact only recognizes specific supported
mechanisms. Fix. Use a data-fetching mechanism the suspense
implementation genuinely recognizes, such as reading a promise
through a supported API, rather than fetching inside a plain effect
or event handler and expecting the boundary to detect it.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Skeleton and Suspense | A generic spinner | An empty region until loaded | Optimistic UI |
|---|---|---|---|---|
| Perceived loading speed | Strong, previews the content's shape | Moderate, feedback without structure | Weak, no feedback at all | Strong, but for a different case, a predictable action result rather than a load |
| Declarative coordination across a tree | Strong, one boundary for a subtree | Weak, usually manual per component | Weak, usually manual per component | Not directly applicable |
| Layout shift on content arrival | Low, if dimensions are matched | Moderate, spinner region often differs in size from content | High, an empty region abruptly fills | Low, the predicted content is usually the real shape already |
| Coverage of every async loading path | Partial, only specific mechanisms | Fully manual, covers whatever is wired by hand | Fully manual, same | Not applicable, a different concern |
| Fit for a genuinely brief loading period | Weak, the skeleton itself can flash and distract | Weak, same reason | Moderate, sometimes nothing is the least distracting option | Not applicable |

Reading of the table. Skeleton and Suspense wins specifically for a
loading period long enough to be noticed but not so brief that the
placeholder itself becomes a distracting flash, where the eventual
content's shape is predictable enough to build a well-matched
skeleton. A generic spinner or an empty state remains simpler for a
loading path outside what the team's suspense mechanism actually
covers.

## 13. Related and incompatible patterns

- **Server Components.** A closely related modern technique whose
  data-streaming mechanism is one of the specific cases React's
  Suspense recognizes, letting a server-streamed component's loading
  state be coordinated through the same boundary mechanism.
- **Optimistic UI.** A different response to a related feeling
  problem, prioritizing showing a predicted result of a user's own
  action immediately, rather than a placeholder for content still
  being fetched from elsewhere.
- **Hooks.** The mechanism a hand-rolled, non-suspense loading-state
  implementation usually uses internally to track its own loading
  flag and conditionally render a skeleton in its place.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a component or page currently showing an
empty region or a generic spinner while its data loads.

1. Identify the component or subtree whose loading period is genuinely
   long enough for a user to notice, and confirm its eventual content
   shape is predictable enough to build a matching skeleton.
2. Confirm the component's data-loading mechanism is one the team's
   suspense implementation genuinely recognizes, or plan to migrate
   it to one that is.
3. Build a skeleton component whose dimensions and rough shape closely
   match the eventual real content, measured against the actual
   rendered content rather than guessed.
4. Wrap the component in a suspense boundary, using the skeleton as
   its fallback.
5. Verify visually that the transition from skeleton to real content
   produces a minimal layout shift, adjusting the skeleton's
   dimensions if a noticeable jump remains.

Removing the pattern when it stops earning its place, most relevant
when the underlying loading period has genuinely become fast enough
that the placeholder itself is the more noticeable, distracting
element.

1. Confirm the loading period has genuinely become fast enough that
   the skeleton's brief flash is now more distracting than helpful,
   rather than assuming so without review.
2. Remove the suspense boundary and its skeleton fallback, letting the
   content render directly once its now-fast load completes.
3. Retire the skeleton component once no boundary references it.

## 15. Testing and verification

Easier because of the pattern.

- The skeleton fallback itself can be tested directly and
  synchronously as a plain component, with no need to simulate an
  actual asynchronous load to verify its appearance and dimensions.
- Because a suspense boundary declares its fallback explicitly in one
  place, a test can assert the fallback renders correctly while the
  wrapped component's data is deliberately held pending, without
  needing to track a manually managed loading flag.

Harder because of the pattern.

- Testing the actual transition from the skeleton fallback to the
  real content, confirming the swap happens correctly once data
  arrives, needs a test environment that can control exactly when the
  underlying asynchronous operation resolves.
- Verifying a specific data-loading mechanism inside a suspense
  boundary is genuinely one Suspense recognizes, rather than one it
  silently does not detect, such as a fetch inside an effect, needs a
  test that specifically checks the fallback actually appears while
  loading, not only that the eventual content is correct.

Techniques that apply.

- **Isolated skeleton rendering tests.** Render the skeleton component
  directly and assert its structure and dimensions, independent of
  any suspense boundary or real data.
- **Suspended-state tests.** Hold the wrapped component's data
  deliberately pending and assert the suspense boundary's fallback
  renders correctly during that period.
- **Resolution transition tests.** Resolve the wrapped component's
  data and assert the boundary correctly swaps from the skeleton to
  the real content.
- **Layout-shift regression tests.** Capture the rendered layout at
  the skeleton state and again at the resolved state, comparing
  their dimensions to catch a mismatch that would produce a visible
  jump.

## 16. Observability signals

Skeleton and Suspense has a genuine runtime footprint, since it
directly governs what a real user sees during a loading period, so a
dedicated production signal is honest here.

What to record.

- The actual duration a given suspense boundary's fallback is shown
  before the real content resolves, since a duration that is
  consistently very short signals the skeleton itself may be
  flashing and becoming a distraction rather than a genuine aid.
- The layout-shift metric, such as cumulative layout shift, measured
  specifically at the moment a boundary's fallback swaps to its real
  content, since a real, measured shift signals the skeleton's
  dimensions do not genuinely match what actually renders.

A healthy state. A boundary's fallback shows for a duration long
enough to feel intentional rather than a flash, and the layout shift
measured at the swap from skeleton to real content stays close to
zero.

A failing state. A fallback that is shown for a duration too brief to
register as anything but a flash, pointing at a boundary applied to a
load that did not need one, or a measurable layout shift at the
skeleton-to-content swap, pointing at a skeleton whose dimensions do
not genuinely match the real content it stands in for.

## 17. Security and privacy implications

Skeleton and Suspense is close to neutral for security, being a
loading and rendering strategy rather than a data-handling one, and
inventing a dedicated attack surface here would be dishonest. One
practical implication is worth naming.

**A skeleton's own placeholder content must never leak a hint about
the real, not-yet-loaded data it stands in for, such as a skeleton
whose block count or structure varies based on the actual size of
the real, sensitive content underneath it, which would let an
observer infer something about that content before it has actually
loaded and been authorized to display.** Because a skeleton is meant
to be a generic, content-agnostic placeholder, a team building one
for a genuinely sensitive piece of data, a private message count, an
account balance, should confirm the skeleton's own shape and
structure do not vary based on the real content's actual value,
keeping the placeholder genuinely uninformative until the real,
authorized content has actually loaded.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models the suspense boundary
and its skeleton fallback the way React's own `<Suspense>` structures
the concept, kept free of JSX and any specific framework's package so
the sample compiles as plain TypeScript. Python shows the same
conceptual split using a minimal, framework-agnostic loading-state
manager that renders a skeleton placeholder while a resource is
pending, since Python has no single dominant Suspense-style UI
framework the way TypeScript has React. Swift shows the pattern using
a minimal model where a loading state renders a skeleton view and
swaps to the real content once an asynchronous load completes,
closely analogous to how suspense-style loading is reasoned about in
a native app's view layer. Java, Go, and Rust are omitted, since none
has a dominant, idiomatic UI-component framework this specifically
frontend loading pattern maps to as directly as TypeScript and Swift
do.

### TypeScript

```typescript
type LoadState<T> = { status: "pending" } | { status: "resolved"; data: T };

interface Article {
  title: string;
  body: string;
}

function renderSkeleton(): string[] {
  return ["[====] title placeholder", "[========] body placeholder"];
}

function renderArticle(article: Article): string[] {
  return [article.title, article.body];
}

class SuspenseBoundary<T> {
  private state: LoadState<T> = { status: "pending" };

  render(): string[] {
    if (this.state.status === "pending") {
      return renderSkeleton();
    }
    return ["resolved"];
  }

  resolve(data: T): void {
    this.state = { status: "resolved", data };
  }
}

const boundary = new SuspenseBoundary<Article>();
console.log(boundary.render());

boundary.resolve({ title: "How Suspense Works", body: "A real article body." });
console.log(renderArticle({ title: "How Suspense Works", body: "A real article body." }));
```

### Python

```python
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Article:
    title: str
    body: str


def render_skeleton() -> list[str]:
    return ["[====] title placeholder", "[========] body placeholder"]


def render_article(article: Article) -> list[str]:
    return [article.title, article.body]


class SuspenseBoundary(Generic[T]):
    def __init__(self) -> None:
        self.resolved_data: Optional[T] = None

    def render(self) -> list[str]:
        if self.resolved_data is None:
            return render_skeleton()
        return ["resolved"]

    def resolve(self, data: T) -> None:
        self.resolved_data = data


if __name__ == "__main__":
    boundary: SuspenseBoundary[Article] = SuspenseBoundary()
    print(boundary.render())

    article = Article(title="How Suspense Works", body="A real article body.")
    boundary.resolve(article)
    print(render_article(article))
```

### Swift

```swift
struct Article {
    let title: String
    let body: String
}

func renderSkeleton() -> [String] {
    ["[====] title placeholder", "[========] body placeholder"]
}

func renderArticle(article: Article) -> [String] {
    [article.title, article.body]
}

final class SuspenseBoundary<T> {
    private var resolvedData: T?

    func render() -> [String] {
        if resolvedData == nil {
            return renderSkeleton()
        }
        return ["resolved"]
    }

    func resolve(_ data: T) {
        resolvedData = data
    }
}

let boundary = SuspenseBoundary<Article>()
print(boundary.render())

let article = Article(title: "How Suspense Works", body: "A real article body.")
boundary.resolve(article)
print(renderArticle(article: article))
```

## 18. References

1. React documentation. "Suspense".
   https://react.dev/reference/react/Suspense
   Verified 2026-08-21. Source of the defining sentence, the
   recommended fallback shape, and the coverage limitation quoted in
   dimensions 1, 3, and 9.
