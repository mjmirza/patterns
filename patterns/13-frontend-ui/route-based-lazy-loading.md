---
name: Route-based Lazy Loading
slug: route-based-lazy-loading
family: 13-frontend-ui
category: Loading Strategy
aliases: [Route Splitting, Per-route Code Splitting]
first_described: "React Router documentation, Automatic Code Splitting"
maturity: canonical
related: [code-splitting, prpl-pattern, resource-hints]
incompatible_with: []
verified: 2026-08-21
---

# Route-based Lazy Loading

## 1. Name, aliases, and lineage

The canonical name is Route-based Lazy Loading, a specific application
of Code Splitting where the split boundary is drawn along an
application's own route structure, so a browser fetches a given
route's code only when the user actually visits that route. React
Router's own documentation states the mechanism directly. "Because
these entry points are coupled to URL segments, React Router knows...
which bundles are needed in the browser, and more
importantly, which are not. If the user visits /about then the
bundles for about.tsx will be loaded but not contact.tsx."

The alias **Route Splitting** names the same technique by its
mechanism rather than its timing, splitting a bundle along route
boundaries. **Per-route Code Splitting** makes the relationship to
the broader Code Splitting pattern explicit, naming the route as the
specific unit each split chunk corresponds to.

## 2. Problem and context

A multi-route application whose routes are all bundled together
forces every visitor to fetch and evaluate the code for every route,
even the ones that specific visit never touches, since a typical
session visits only a fraction of an application's full route set.
Generic Code Splitting solves the underlying problem, but still
leaves open the question of where exactly to draw a split boundary,
and a route is often the single clearest, most naturally
self-contained unit an application already has, since a route's code
is already scoped to a specific URL and a specific view the rest of
the application does not directly depend on. Route-based Lazy
Loading answers that question directly. draw the split boundary at
the route level, so each route becomes its own independently loadable
chunk, fetched only when a visitor's own path actually reaches it.

## 3. Forces

The pattern balances the following competing pressures.

- **A naturally self-contained split unit.** Favored. A route is
  already a distinct, addressable unit of an application, with its own
  URL and its own view, making it a low-friction, obvious boundary to
  split along compared to inventing a boundary elsewhere in the code.
- **A real, measured reduction in initial payload.** Favored. React
  Router's own documentation states the direct outcome. "This
  drastically reduces the JavaScript footprint for initial page loads
  and speeds up your application," since only the currently matched
  route's bundle is fetched rather than every route's combined code.
- **A loading moment on route transitions.** Sacrificed. A route
  visited for the first time in a session pays a fetch delay for its
  chunk at the exact moment the user visits it, a cost a fully
  bundled application does not have.
- **Coordination with the router's own matching logic.** Sacrificed.
  Route-based splitting depends on the routing layer to map a URL to
  the correct chunk correctly and reliably, coupling the splitting
  strategy to the specific router in use rather than leaving it fully
  independent.

## 4. Applicability and non-applicability

Reach for Route-based Lazy Loading when the following hold.

- The application genuinely has multiple distinct routes, and a real
  share of sessions only ever visit a subset of them.
- The routing layer in use supports, or can be configured to support,
  loading a route's code lazily, tied to that route actually being
  matched.
- The team is prepared for a brief loading moment on a route's first
  visit within a session, and can design a loading state for that
  transition.

Do NOT reach for Route-based Lazy Loading in these cases, and the
reason matters more than the rule.

- **The application has only a small number of routes, or nearly every
  session visits all of them anyway**, splitting along a boundary
  nearly every session crosses gains little over a single bundle,
  while still paying the coordination cost of route-level splitting.
- **A route's code is small enough that fetching it up front is
  already cheap**, applying route-based splitting to a route whose
  code was never a real share of the total bundle adds a chunk
  boundary, and a loading transition, for no real benefit.
- **The routing layer has no reliable way to map a matched route to
  its correct lazily loaded chunk**, forcing a route-based split
  without that support risks a mismatch between the URL the user
  visited and the code that actually loads for it.

## 5. Structure

Route-based Lazy Loading has two structural parts.

- **The route-to-chunk mapping**, the routing configuration that
  associates a specific URL pattern with a specific, independently
  loadable code chunk, most commonly a route module file.
- **The lazy loading mechanism**, most commonly a dynamic `import()`
  call or a framework's own lazy-component wrapper, invoked by the
  router at the moment a matching route is actually visited.

## 6. ASCII structure diagram

```
  Route configuration

  route("/about",   "./about.tsx")    -> chunk: about.js
  route("/contact", "./contact.tsx")  -> chunk: contact.js

  User visits /about

  router matches "/about"
       |
       v
  router fetches about.js, the chunk mapped to that route
       |
       v
  about.tsx renders
       |
  contact.js was never fetched, since /contact was never visited
```

## 7. Dynamics

The trace below shows a user visiting one route and never reaching
another.

```
Initial page load

the application loads with only its shared shell and the currently
matched route's chunk
   |-- the user lands on "/about"
   |-- the router fetches about.js specifically, since that is the
       route currently matched
   |-- contact.js and every other route's chunk remain unfetched

User moves within the application

the user clicks a link to "/contact"
   |-- the router matches "/contact" against the route configuration
   |-- it fetches contact.js, the chunk mapped to that route
   |-- while that fetch is in flight, a loading state renders
   |-- once contact.js arrives and evaluates, the contact route
       renders and becomes usable

Session ends without visiting every route

the user leaves having visited only "/about" and "/contact"
   |-- every other route's chunk was never fetched at all, its cost
       entirely avoided for this session
```

## 8. Implementation variants

**Router-native lazy route modules.** A routing library's own
configuration format directly supports mapping a route to a lazily
loaded module, as React Router's own route module system does,
without the developer manually writing a dynamic import call for
each route.

**Manual dynamic import per route.** A developer wraps each route's
component in a dynamic import call by hand, most commonly paired with
a component-level lazy-loading wrapper the framework provides.

**Nested route splitting.** A route's own child routes are split
independently of their parent, so a deeply nested section of the
application defers even further, only fetching a specific nested
route's code when that specific nested URL is matched.

**Prefetch-on-hover route loading.** A router observes when the user
hovers over, or otherwise signals likely intent toward, a link to a
lazily loaded route, and begins fetching that route's chunk ahead of
the actual click, softening the loading delay the split would
otherwise introduce.

## 9. Known production uses

**React Router's own documentation, defining the mechanism and its
outcome.** React Router states the mechanism and its benefit
directly. "Because these entry points are coupled to URL segments,
React Router knows... which bundles are needed in the
browser, and more importantly, which are not. If the user visits
/about then the bundles for about.tsx will be loaded but not
contact.tsx. This drastically reduces the JavaScript footprint for
initial page loads and speeds up your application." React Router,
"Automatic Code Splitting,"
https://reactrouter.com/explanation/code-splitting, verified
2026-08-21.

**React's own documentation, on the underlying lazy-loading
primitive.** React's own documentation describes the mechanism
route-based splitting is frequently built on top of. "lazy lets you
defer loading component's code until it is rendered for the first
time." React, "lazy," https://react.dev/reference/react/lazy,
verified 2026-08-21.

## 10. Consequences

Positive.

- The initial payload shrinks to only the currently matched route's
  code, directly reducing the JavaScript footprint React Router's own
  documentation names as the pattern's benefit.
- A route is already a natural, self-contained boundary, so choosing
  it as the split unit needs little additional design work compared
  to inventing a boundary elsewhere in the application's code.
- A route a given session never visits never has its code fetched at
  all, its cost fully avoided rather than merely deferred.

Negative.

- A route visited for the first time in a session pays a real fetch
  delay for its chunk at the moment it is reached, a cost a fully
  bundled application does not have.
- The split boundary is coupled to the routing layer's own matching
  logic, so a change to how routes are configured can affect which
  code loads when in ways that are less obvious than a manually drawn
  split boundary.
- An application with few routes, or one whose sessions consistently
  visit nearly every route, gains little from the pattern while still
  paying its coordination cost.

## 11. Failure modes and misuse

**Applying route-based splitting to an application with few routes,
or one whose sessions nearly always visit all of them.** Symptom. The
initial payload shrinks only slightly, since most routes' code is
fetched in nearly every session anyway, while the application now
carries the coordination cost of managing per-route chunks and
loading states. Cause. Applying the pattern by default rather than
confirming a real, measured share of sessions genuinely skip a
real share of routes. Fix. Measure real session route-visit
patterns before splitting, reserving the pattern for applications
where a genuine share of routes go unvisited in a typical session.

**Leaving no loading state for the route transition a lazily loaded
chunk introduces.** Symptom. Moving to a route the user has not
yet visited in the session shows a blank or frozen screen for the
duration of the chunk's fetch, rather than a clear loading indication.
Cause. Wiring the lazy route mechanism without also designing the
loading state a Suspense boundary, or its framework equivalent, is
meant to show during that fetch. Fix. Pair every lazily loaded route
with an explicit, designed loading state, so the transition feels
deliberate rather than broken.

**Splitting nested routes so finely that a single user flow through
several nested screens triggers a chain of separate chunk fetches in
quick succession.** Symptom. Moving through a multi-step nested flow
shows a loading delay at each step, even though the whole flow was
always going to be visited together in the same session. Cause.
Applying route-based splitting uniformly to every route, including
nested routes a session's natural flow visits together as a unit,
rather than considering which nested boundaries genuinely correspond
to independent usage. Fix. Group nested routes a typical flow visits
together into a single chunk, reserving separate chunks for routes
that are genuinely, independently optional.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Route-based Lazy Loading | Generic Code Splitting, feature-scoped | Single bundle, no splitting |
|---|---|---|---|
| A naturally self-contained split unit | Strong, the route already exists as a distinct boundary | Moderate, requires identifying a feature boundary explicitly | Not applicable |
| Reduction in initial payload | Strong, when routes are genuinely underused per session | Strong, for the specific feature split | Weak, everything loads up front |
| Coordination cost | Moderate, coupled to the router's own matching logic | Moderate, coupled to wherever the feature boundary lives | Strong, nothing extra to coordinate |
| Loading moment on first use | Present, at route transition | Present, at first feature use | Not applicable |

Reading of the table. Route-based Lazy Loading wins specifically for
a multi-route application where routes already form a natural
boundary and a real share of sessions skip a real share of
them. Feature-scoped splitting suits a case where the natural
boundary lives inside a single route rather than between routes, and
a small, low-route-count application gains little from either over a
single bundle.

## 13. Related and incompatible patterns

- **Code Splitting.** The general pattern this is a specific instance
  of, drawing the split boundary along an application's route
  structure rather than an arbitrary feature or component boundary.
- **PRPL Pattern.** Route-based Lazy Loading directly implements the
  lazy load half of PRPL, deferring non-initial routes until the user
  actually visits them.
- **Resource Hints.** A prefetch hint applied on link hover or
  visibility softens the loading delay a lazily loaded route would
  otherwise introduce on first visit.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing multi-route application currently
bundled as a single unit.

1. Confirm, through measurement, that a real share of sessions visit
   only a subset of the application's routes, rather than assuming so
   without checking real usage data.
2. Convert each route's static import into a dynamic import, or the
   router's own lazy route mechanism if one is provided.
3. Add an explicit loading state for the transition a lazily loaded
   route's fetch introduces.
4. Group nested routes a typical session visits together as a single
   flow into one chunk, rather than splitting every nested boundary
   independently.
5. Measure the resulting initial payload and time to interactive
   against the pre-split baseline, confirming the split produced a
   genuine improvement.

Removing the pattern when it stops earning its place, most relevant
when the application's route set has shrunk, or session behavior has
shifted so nearly every session visits nearly every route anyway.

1. Confirm, through measurement, that route-level splitting no longer
   corresponds to a genuine usage boundary, rather than assuming so
   without checking real session data.
2. Convert the lazily loaded routes back into static imports, folding
   them back into the application's main bundle.
3. Re-measure the resulting bundle's parse time and initial payload
   to confirm the consolidation did not reintroduce a genuine startup
   delay.

## 15. Testing and verification

Easier because of the pattern.

- A test can assert a specific route's chunk is not present in the
  application's initial bundle, catching a regression where a build
  misconfiguration accidentally folds a lazily loaded route back into
  the main bundle.
- Because each route's code is a deliberately isolated chunk, a size
  budget assertion per route catches a regression where an unrelated
  dependency leaks into a specific route's chunk.

Harder because of the pattern.

- Testing that navigation between routes correctly triggers, waits
  for, and resolves each route's lazy chunk fetch needs a test
  environment that can simulate real navigation and a real, or
  realistically delayed, chunk load, rather than assuming the chunk
  always resolves instantly.
- Verifying the actual reduction in initial payload needs measuring
  the real, built bundle output, since a fast local development
  environment can mask whether a route's code has actually been
  isolated into its own separately loadable chunk.

Techniques that apply.

- **Route chunk isolation assertions.** Directly assert a specific
  route's code is absent from the application's initial bundle output.
- **Navigation and loading-state integration tests.** Simulate a real
  navigation to a lazily loaded route and assert the loading state
  renders correctly during the fetch, and the route itself renders
  correctly once it resolves.
- **Per-route bundle size budgets.** Assert each route's chunk stays
  under an explicit size threshold in continuous integration.
- **Real navigation performance measurement.** Measure the actual time
  to interactive for a first-time route visit on a realistically
  constrained device and network, confirming the split boundary
  produces the improvement it was chosen for.

## 16. Observability signals

Route-based Lazy Loading has a genuine, measurable runtime footprint,
since it directly governs what a real user's browser fetches on
initial load and on each route transition, so a dedicated production
signal is honest here.

What to record.

- The initial payload size for a typical first visit, since this is
  the specific metric route-based splitting exists to reduce, and a
  regression here points at a route's code leaking back into the
  main bundle.
- The latency of each route's first-visit chunk fetch within a
  session, since a consistently slow fetch for a specific route may
  need its own further splitting, or a prefetch hint for a route
  users commonly visit soon after landing.

A healthy state. The initial payload stays small relative to the
application's total route count, and each route's first-visit chunk
fetch resolves quickly enough that the loading transition feels
brief and deliberate rather than jarring.

A failing state. The initial payload has drifted upward, pointing at
a route's code leaking back into the main bundle, or a specific
route's chunk fetch is consistently slow, pointing at that route
needing its own further splitting, a prefetch hint, or a
reconsideration of how it was scoped.

## 17. Security and privacy implications

Route-based Lazy Loading carries the same access-control caution as
generic Code Splitting, worth restating specifically for the route
case since it is the most common place the mistake actually happens.

**A route's chunk being lazily loaded, rather than present in the
application's initial bundle, is never itself an access-control
mechanism, since the chunk's URL remains directly, individually
fetchable by anyone who requests it, regardless of whether the
application's own router would ever have taken a given user
there.** A route intended to be restricted, such as an admin section,
must have its actual authorization enforced by the server handling
the data that route's code goes on to request, never by the mere fact
that its chunk is not part of the application's initial download. A
lazily loaded route is a loading-timing decision, not a security
boundary, and treating it as the latter is the specific mistake this
pattern's own route-per-chunk shape makes easy to fall into.

## 18. References

1. React Router. "Automatic Code Splitting".
   https://reactrouter.com/explanation/code-splitting
   Verified 2026-08-21. Source of the defining route-to-bundle mapping
   quote and the JavaScript footprint reduction quote used in
   dimensions 1, 3, and 9.
2. React. "lazy".
   https://react.dev/reference/react/lazy
   Verified 2026-08-21. Source of the underlying lazy-loading
   primitive quote used in dimensions 8 and 9.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models a route-to-chunk
registry using the same dynamic import mechanism React Router and
React's own lazy loading are built on, kept free of JSX and any
specific framework's package so the sample compiles as plain
TypeScript. Python shows the conceptual shape of the same
route-to-module mapping using a minimal, framework-agnostic router,
since Python has no browser runtime and therefore no single dominant
route-based splitting implementation the way TypeScript has React
Router and the dynamic import operator. Swift shows the same
conceptual shape using a minimal model, analogous to how a native
app's own navigation layer might lazily instantiate a screen's view
controller only when that screen is actually visited. Java, Go,
and Rust are omitted, since none has a dominant, idiomatic
browser-facing routing framework this specifically URL-mapped pattern
maps to as directly as TypeScript does.

### TypeScript

```typescript
interface RouteModule {
  path: string;
  render(): void;
}

async function loadRouteModule(path: string): Promise<RouteModule> {
  return {
    path,
    render: () => console.log("rendering route:", path),
  };
}

class Router {
  private routeLoaders: Map<string, () => Promise<RouteModule>> = new Map();
  private loadedChunks: Set<string> = new Set();

  registerRoute(path: string): void {
    this.routeLoaders.set(path, () => loadRouteModule(path));
  }

  async navigate(path: string): Promise<void> {
    const loader = this.routeLoaders.get(path);
    if (!loader) {
      throw new Error("no route registered for: " + path);
    }
    console.log("navigating to:", path, "fetching chunk if needed");
    const routeModule = await loader();
    this.loadedChunks.add(path);
    routeModule.render();
  }

  isChunkLoaded(path: string): boolean {
    return this.loadedChunks.has(path);
  }
}

async function main(): Promise<void> {
  const router = new Router();
  router.registerRoute("/about");
  router.registerRoute("/contact");

  console.log("contact chunk loaded before visit:", router.isChunkLoaded("/contact"));

  await router.navigate("/about");
  console.log("about chunk loaded:", router.isChunkLoaded("/about"));
  console.log("contact chunk loaded after visiting only /about:", router.isChunkLoaded("/contact"));
}

main();
```

### Python

```python
import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, Callable


@dataclass
class RouteModule:
    path: str

    def render(self) -> None:
        print(f"rendering route: {self.path}")


async def load_route_module(path: str) -> RouteModule:
    return RouteModule(path=path)


@dataclass
class Router:
    route_loaders: dict[str, Callable[[], Awaitable[RouteModule]]] = field(default_factory=dict)
    loaded_chunks: set[str] = field(default_factory=set)

    def register_route(self, path: str) -> None:
        self.route_loaders[path] = lambda: load_route_module(path)

    async def navigate(self, path: str) -> None:
        loader = self.route_loaders.get(path)
        if loader is None:
            raise ValueError(f"no route registered for: {path}")
        print(f"navigating to: {path}, fetching chunk if needed")
        route_module = await loader()
        self.loaded_chunks.add(path)
        route_module.render()

    def is_chunk_loaded(self, path: str) -> bool:
        return path in self.loaded_chunks


async def main() -> None:
    router = Router()
    router.register_route("/about")
    router.register_route("/contact")

    print("contact chunk loaded before visit:", router.is_chunk_loaded("/contact"))

    await router.navigate("/about")
    print("about chunk loaded:", router.is_chunk_loaded("/about"))
    print("contact chunk loaded after visiting only /about:", router.is_chunk_loaded("/contact"))


if __name__ == "__main__":
    asyncio.run(main())
```

### Swift

```swift
struct RouteModule {
    let path: String

    func render() {
        print("rendering route: " + path)
    }
}

func loadRouteModule(path: String) async -> RouteModule {
    RouteModule(path: path)
}

actor Router {
    private var registeredPaths: Set<String> = []
    private var loadedChunks: Set<String> = []

    func registerRoute(_ path: String) {
        registeredPaths.insert(path)
    }

    func navigate(_ path: String) async throws {
        guard registeredPaths.contains(path) else {
            throw NSError(domain: "Router", code: 1, userInfo: [NSLocalizedDescriptionKey: "no route registered for: " + path])
        }
        print("navigating to: " + path + ", fetching chunk if needed")
        let routeModule = await loadRouteModule(path: path)
        loadedChunks.insert(path)
        routeModule.render()
    }

    func isChunkLoaded(_ path: String) -> Bool {
        loadedChunks.contains(path)
    }
}

func main() async throws {
    let router = Router()
    await router.registerRoute("/about")
    await router.registerRoute("/contact")

    let beforeContact = await router.isChunkLoaded("/contact")
    print("contact chunk loaded before visit: " + String(beforeContact))

    try await router.navigate("/about")
    let aboutLoaded = await router.isChunkLoaded("/about")
    print("about chunk loaded: " + String(aboutLoaded))

    let afterContact = await router.isChunkLoaded("/contact")
    print("contact chunk loaded after visiting only /about: " + String(afterContact))
}

try await main()
```
