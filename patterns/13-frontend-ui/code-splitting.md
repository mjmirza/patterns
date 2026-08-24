---
name: Code Splitting
slug: code-splitting
family: 13-frontend-ui
category: Loading Strategy
aliases: [Bundle Splitting, Dynamic Import Splitting, Chunk Splitting]
first_described: "web.dev, Reduce JavaScript payloads with code splitting"
maturity: canonical
related: [prpl-pattern, resource-hints, route-based-lazy-loading, virtual-list]
incompatible_with: []
verified: 2026-08-21
---

# Code Splitting

## 1. Name, aliases, and lineage

The canonical name is Code Splitting, a technique that divides an
application's JavaScript into multiple separate bundles, so a browser
only has to fetch and evaluate the code the current page genuinely
needs, rather than the application's entire codebase at once. web.dev's
own documentation states the goal directly. "Code splitting is a
technique that seeks to minimize startup time. When we ship less
JavaScript at startup, we can get applications to be interactive
faster."

The alias **Bundle Splitting** describes the same technique from the
build-output side, the single bundle a build tool would otherwise
produce is split into several smaller ones. **Dynamic Import
Splitting** names the JavaScript-language mechanism most commonly
used to implement it, the dynamic `import()` function. **Chunk
Splitting** uses the term several popular build tools give to each
resulting piece, a chunk.

## 2. Problem and context

A JavaScript application that bundles its entire codebase into a
single file forces every visitor to download, parse, and evaluate
code for every feature the application has, even the parts of a page,
or an entire route, that visitor never uses in that session. On a
constrained device or a slow connection, this delay is not abstract,
it directly pushes back the moment the page becomes interactive,
since the browser's main thread stays busy parsing and running code
the current view does not need before it can respond to the user at
all. Code Splitting solves this by breaking the single bundle into
multiple, independently loadable pieces, so a page fetches only the
code its current view actually requires, and defers the rest until,
or unless, it is genuinely needed.

## 3. Forces

The pattern balances the following competing pressures.

- **Fast time to interactive.** Favored. web.dev's own documentation
  states the direct benefit. "When we ship less JavaScript at
  startup, we can get applications to be interactive faster," since
  the main thread spends less time parsing and evaluating code the
  current view does not use.
- **Deferred cost for code not yet needed.** Favored, through dynamic
  loading. MDN's own documentation on dynamic import describes the
  underlying mechanism directly. "Dynamic imports allow one to
  circumvent the syntactic rigidity of import declarations and load a
  module conditionally or on demand," used "when importing statically
  significantly slows the loading of your code."
- **A visible, if brief, loading moment for deferred code.**
  Sacrificed. A chunk fetched only when first needed introduces a real
  fetch delay at the exact moment the user tries to use that part of
  the application, a cost a single up-front bundle does not have.
- **Build and coordination simplicity.** Sacrificed. A single bundle
  needs no chunk boundaries to design, while a properly split
  application needs the team to reason about which code belongs in
  which chunk, and to keep that boundary sensible as the application
  grows.

## 4. Applicability and non-applicability

Reach for Code Splitting when the following hold.

- The application is genuinely large enough that a single bundle's
  parse and evaluation time is a measurable share of the delay before
  the page becomes interactive.
- The application has natural boundaries, distinct routes, a rarely
  used feature, an admin-only view, that a real share of visitors in
  a given session never actually use.
- The team can tolerate, or actively design around, the brief loading
  moment a deferred chunk introduces the first time a user reaches it.

Do NOT reach for Code Splitting in these cases, and the reason
matters more than the rule.

- **The application is small enough that its full bundle already
  parses and evaluates quickly on the audience's real devices**,
  splitting a bundle that is not genuinely a measured problem adds
  build complexity and chunk-boundary decisions for no corresponding
  user-facing benefit.
- **The split boundary does not correspond to a genuine usage
  pattern**, splitting code into chunks a typical session ends up
  fetching anyway, in quick succession, adds the coordination cost of
  splitting without the deferred-cost benefit that justifies it.
- **The team has not measured where the actual parse and evaluation
  time is going**, applying code splitting speculatively, without
  profiling to confirm which part of the bundle genuinely delays
  interactivity, risks splitting the wrong boundary and gaining
  little.

## 5. Structure

Code Splitting has two structural parts.

- **The split boundary**, the decision about which code belongs in
  the initial bundle versus a separate, deferred chunk, most commonly
  drawn along route, feature, or rarely used code boundaries.
- **The loading trigger**, the mechanism, most commonly a dynamic
  `import()` call, that fetches and evaluates a deferred chunk at the
  moment it is actually needed.

## 6. ASCII structure diagram

```
  Without code splitting

  +----------------------------------------------------------+
  | single bundle, main.js                                    |
  |   route A code, route B code, route C code,                |
  |   admin feature code, everything, fetched and evaluated    |
  |   before the page can become interactive                   |
  +----------------------------------------------------------+

  With code splitting

  +----------------+   +----------------+   +----------------+
  | initial.js       |   | route-b.js       |   | admin.js         |
  | route A only,     |   | fetched only if   |   | fetched only if  |
  | fetched and       |   | the user           |   | the user reaches |
  | evaluated for     |   | visits            |   | the admin        |
  | the initial       |   | route B            |   | feature          |
  | interactive       |   |                    |   |                  |
  | render            |   |                    |   |                  |
  +----------------+   +----------------+   +----------------+
```

## 7. Dynamics

The trace below shows a user loading the initial page, then reaching
a deferred route.

```
Initial page load

the browser requests the page
   |-- only the initial chunk, containing route A's code, is
       fetched and evaluated
   |-- the page becomes interactive as soon as that smaller chunk is
       ready, without waiting for route B or the admin feature's code
   |-- route B's chunk and the admin feature's chunk remain deferred,
       unfetched

User moves to route B

the user clicks a link to route B
   |-- a dynamic import call fetches route B's chunk
   |-- while that fetch is in flight, the application shows a brief
       loading state
   |-- once the chunk arrives and evaluates, route B renders and
       becomes usable

Session ends without visiting the admin feature

the user leaves the application having never visited the admin
feature
   |-- the admin feature's chunk was never fetched at all, its cost
       entirely avoided for this session
```

## 8. Implementation variants

**Route-based splitting.** Each distinct route in the application
becomes its own chunk, the most common and often the highest-value
split boundary, since a given session usually visits only a
fraction of an application's total routes.

**Feature-based splitting.** A specific feature, such as a rich text
editor or a chart library, that only a subset of users or sessions
actually reaches, is split into its own chunk independent of the
route it happens to live on.

**Vendor and shared-dependency splitting.** Third-party library code
is split into its own chunk separate from an application's own code,
so a browser can cache that shared, slowly changing dependency chunk
across an application's own more frequently changing releases.

**Framework-level automatic splitting.** A framework's own routing
and build layer automatically determines chunk boundaries along route
lines, removing the need for a team to hand-author every dynamic
import call.

## 9. Known production uses

**web.dev's own documentation, defining the goal.** web.dev states
the pattern's purpose directly. "Code splitting is a technique that
seeks to minimize startup time. When we ship less JavaScript at
startup, we can get applications to be interactive faster." web.dev,
"Reduce JavaScript payloads with code splitting,"
https://web.dev/articles/reduce-javascript-payloads-with-code-splitting,
verified 2026-08-21.

**MDN's own documentation, on the dynamic import mechanism.** MDN
describes the underlying language feature directly. "The import
declaration syntax is static and will always result in the imported
module being evaluated at load time. Dynamic imports allow one to
circumvent the syntactic rigidity of import declarations and load a
module conditionally or on demand," recommending it specifically
"when importing statically significantly slows the loading of your
code or increases your program's memory usage, and there is a low
likelihood that you will need the code you are importing." MDN Web
Docs, "import,"
https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/import,
verified 2026-08-21.

## 10. Consequences

Positive.

- The page becomes interactive sooner, since the browser's main
  thread spends less time parsing and evaluating code the current
  view does not need, directly addressing the startup-time goal
  web.dev's own documentation names.
- Code the current session never actually reaches, an admin feature, a
  rarely used route, never has to be fetched at all, its cost fully
  avoided rather than merely deferred.
- Splitting shared, slowly changing dependencies into their own chunk
  lets a browser cache that chunk across an application's own more
  frequently changing releases.

Negative.

- A deferred chunk introduces a real, visible fetch delay at the
  exact moment a user first reaches the code it contains, a cost a
  single up-front bundle does not have.
- The team must design and maintain sensible chunk boundaries, a
  decision a single bundle never requires, and a boundary that stops
  matching real usage patterns as the application evolves needs
  active revisiting.
- Splitting too finely can produce a large number of small chunks,
  each carrying its own request overhead, offsetting some of the
  benefit splitting is meant to provide.

## 11. Failure modes and misuse

**Splitting along a boundary that does not correspond to how sessions
actually use the application.** Symptom. A session that visits route
A also, in quick succession, visits the supposedly deferred route B,
so the split provides no real deferred-cost benefit and only adds the
fetch delay of a second chunk request. Cause. Choosing a chunk
boundary based on the application's code structure rather than its
real, measured usage pattern. Fix. Profile actual session behavior to
confirm code genuinely deferred by a split boundary is genuinely
often not needed in the same session, rather than assuming a
structural boundary implies a usage boundary.

**Deferring a chunk the user needs immediately after the initial
page, with no prefetch hint to soften the delay.** Symptom.
Moving to the very next screen the user was always going to visit
shows a visible loading delay, since its chunk was deferred and only
begins fetching on navigation. Cause. Applying code splitting
uniformly to every non-initial route, without distinguishing a route
the user is likely to reach soon from one they may never reach at
all. Fix. Pair a deferred chunk that the user is likely to need soon
with a prefetch resource hint, so its fetch begins in the background
before the user actually visits it.

**Splitting so finely that the number of chunks, and their combined
request overhead, offsets the benefit of a smaller initial bundle.**
Symptom. The total time to load and become interactive is not
noticeably better, and may even be worse, than a coarser split, or
no split at all, since the browser now issues many small requests
each carrying its own overhead. Cause. Splitting along every possible
boundary without measuring whether the resulting chunk count and size
genuinely improves the outcome. Fix. Measure the actual load and
interactivity time at different chunk granularities, and settle on
the coarsest split that still captures the deferred-cost benefit,
rather than splitting as finely as the tooling allows.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Code Splitting | Single bundle, no splitting | Server Components |
|---|---|---|---|
| Fast time to interactive | Strong, when the split boundary matches real usage | Weak, everything must parse and evaluate up front | Strong, for the portion rendered on the server with no client JavaScript at all |
| Deferred cost for unneeded code | Strong | Not applicable, everything is always fetched | Strong for server-rendered portions, not directly applicable to client interactivity |
| Build and coordination simplicity | Weak, chunk boundaries must be designed and maintained | Strong, nothing extra to configure | Moderate, a different but real coordination cost between server and client boundaries |
| A visible loading moment for deferred code | Present, at first use of a deferred chunk | Not applicable, nothing is deferred | Not applicable, a different mechanism entirely |

Reading of the table. Code Splitting wins specifically when an
application is genuinely large enough that startup parse time is a
measured problem, and its natural usage pattern has a real
route or feature boundary a real share of sessions never
cross. A small application gains little and only pays the added
build complexity, and an application whose sessions consistently
touch most of its code gains little from splitting along a boundary
nearly every session crosses anyway.

## 13. Related and incompatible patterns

- **PRPL Pattern.** Code Splitting is the mechanism most commonly
  used to implement the render and lazy load halves of PRPL, giving
  the pattern a genuinely smaller initial bundle to render first.
- **Resource Hints.** A prefetch hint is frequently paired with a
  deferred chunk the user is likely to need soon, softening the
  loading delay a split would otherwise introduce at first use.
- **Route-based Lazy Loading.** A specific, route-scoped instance of
  Code Splitting, where the split boundary is drawn directly along an
  application's route structure.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing application currently shipped as
a single bundle.

1. Profile the current bundle to identify how much of its total
   parse and evaluation time belongs to code a typical session does
   not actually use.
2. Identify a natural split boundary, most commonly a route or a
   rarely used feature, that a real, measured share of sessions never
   cross.
3. Convert the static import for that boundary's code into a dynamic
   `import()` call, or use the framework's own route-based splitting
   mechanism if one is available.
4. Measure the resulting time to interactive against the pre-split
   baseline, confirming the split boundary genuinely improved the
   outcome.
5. Pair any deferred chunk the user is likely to reach soon with a
   prefetch resource hint, to soften its first-use loading delay.

Removing the pattern when it stops earning its place, most relevant
when the application has genuinely shrunk, or its usage pattern has
shifted so nearly every session crosses the previous split boundary.

1. Confirm, through measurement, that the split boundary no longer
   corresponds to a genuine usage boundary, rather than assuming so
   without checking real session data.
2. Convert the deferred dynamic import back into a static import,
   folding that chunk back into the main bundle.
3. Re-measure the resulting bundle's parse and evaluation time to
   confirm the consolidation did not reintroduce a genuine startup
   delay.

## 15. Testing and verification

Easier because of the pattern.

- Because each chunk is a deliberately isolated unit, a test asserting
  a specific chunk's size stays under an explicit budget can catch a
  regression where an unrelated dependency accidentally leaks into a
  chunk meant to stay small.
- A test can assert that a specific deferred chunk is not present in
  the initial bundle's dependency graph, catching a build
  misconfiguration that accidentally folds deferred code back into
  the main bundle.

Harder because of the pattern.

- Verifying the actual interactivity improvement needs measuring real,
  or realistically simulated, device and network conditions, since a
  fast local development environment will not surface the specific
  parse-time delay the pattern exists to reduce.
- Testing the user-facing loading state a deferred chunk shows while
  its fetch is in flight needs simulating that fetch delay directly,
  rather than assuming the chunk always resolves instantly the way it
  might in a fast local test environment.

Techniques that apply.

- **Bundle size budgets.** Assert each chunk's size stays under an
  explicit threshold in continuous integration, catching a regression
  before it reaches production.
- **Dependency graph assertions.** Assert a specific dependency is
  present only in its intended chunk, catching an accidental leak
  into the initial bundle.
- **Simulated slow-fetch tests.** Force a deferred chunk's import to
  resolve slowly in a test environment, confirming the resulting
  loading state renders correctly rather than only ever exercising the
  instant-resolve path.
- **Real-device interactivity measurement.** Measure the actual time
  to interactive on a realistically constrained device and network,
  confirming the split boundary produces the improvement it was
  chosen for.

## 16. Observability signals

Code Splitting has a genuine, measurable runtime footprint, since it
directly governs what a real user's browser fetches, parses, and
evaluates on a given visit, so a dedicated production signal is
honest here.

What to record.

- The time to interactive for the initial page load, since this is
  the specific metric splitting the initial bundle exists to improve,
  and a regression here points at a chunk boundary that has drifted
  or a dependency that leaked back into the initial bundle.
- The frequency and latency of deferred-chunk fetches across real
  sessions, since a chunk fetched in nearly every session points at a
  split boundary that no longer matches actual usage, and a
  consistently slow fetch points at a chunk that may need its own
  further splitting or a prefetch hint.

A healthy state. The initial page consistently reaches interactive
quickly, and deferred chunks are fetched only by the share of
sessions that genuinely reach the feature or route they contain, each
resolving promptly when they are.

A failing state. The initial page's time to interactive has drifted
upward, pointing at a dependency that leaked back into the initial
bundle, or a deferred chunk is fetched by nearly every session,
pointing at a split boundary that no longer reflects real usage and
should be reconsidered or folded back into the initial bundle.

## 17. Security and privacy implications

Code Splitting is close to neutral for security, being a bundling and
loading strategy rather than a data-handling one, and inventing a
dedicated attack surface here would be dishonest. One practical
implication is worth naming.

**Because each deferred chunk is served as its own separately
requestable asset, any access-control logic gating a feature's code
must be enforced by the server that actually returns the data that
code operates on, never by the mere absence of that chunk from the
initial bundle, since a chunk's URL or filename is discoverable and
directly fetchable by anyone who inspects the application's network
requests, regardless of whether the application's own client-side
routing would ever have triggered that fetch itself.** Treating a
split boundary as an access-control boundary is a mistake specific to
this pattern, since splitting code into its own chunk changes only
when it is fetched, not who is able to fetch it, and the real
authorization decision belongs entirely to the server handling the
requests that chunk's code goes on to make.

## 18. References

1. web.dev. "Reduce JavaScript payloads with code splitting".
   https://web.dev/articles/reduce-javascript-payloads-with-code-splitting
   Verified 2026-08-21. Source of the defining startup-time quote used
   in dimensions 1, 3, and 9.
2. MDN Web Docs. "import".
   https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/import
   Verified 2026-08-21. Source of the dynamic import mechanism quotes
   used in dimensions 3 and 9.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models a chunk loader using
the dynamic import mechanism the way MDN's own documentation
describes it, kept free of JSX and any specific framework's package
so the sample compiles as plain TypeScript. Python shows the
conceptual shape of the same deferred-loading logic using a minimal,
framework-agnostic module loader, since Python has no browser runtime
and therefore no single dominant code-splitting implementation the
way TypeScript has the dynamic import operator. Swift shows the same
conceptual shape using a minimal model, analogous to how a native app
might reason about deferring a rarely used feature module until the
user actually visits it. Java, Go, and Rust are omitted, since
none has a dominant, idiomatic browser-facing bundler this
specifically web-loading pattern maps to as directly as TypeScript
does.

### TypeScript

```typescript
interface FeatureModule {
  name: string;
  run(): void;
}

async function loadFeatureModule(name: string): Promise<FeatureModule> {
  return { name, run: () => console.log("running module:", name) };
}

class ChunkLoader {
  private loaded: Map<string, FeatureModule> = new Map();

  async loadOnDemand(name: string): Promise<FeatureModule> {
    const existing = this.loaded.get(name);
    if (existing) {
      return existing;
    }
    const loadedModule = await loadFeatureModule(name);
    this.loaded.set(name, loadedModule);
    return loadedModule;
  }

  isLoaded(name: string): boolean {
    return this.loaded.has(name);
  }
}

async function main(): Promise<void> {
  const loader = new ChunkLoader();
  console.log("admin feature loaded before use:", loader.isLoaded("admin"));

  const adminModule = await loader.loadOnDemand("admin");
  adminModule.run();

  console.log("admin feature loaded after use:", loader.isLoaded("admin"));
}

main();
```

### Python

```python
import asyncio
from dataclasses import dataclass, field


@dataclass
class FeatureModule:
    name: str

    def run(self) -> None:
        print(f"running module: {self.name}")


async def load_feature_module(name: str) -> FeatureModule:
    return FeatureModule(name=name)


@dataclass
class ChunkLoader:
    loaded: dict[str, FeatureModule] = field(default_factory=dict)

    async def load_on_demand(self, name: str) -> FeatureModule:
        if name in self.loaded:
            return self.loaded[name]
        loaded_module = await load_feature_module(name)
        self.loaded[name] = loaded_module
        return loaded_module

    def is_loaded(self, name: str) -> bool:
        return name in self.loaded


async def main() -> None:
    loader = ChunkLoader()
    print("admin feature loaded before use:", loader.is_loaded("admin"))

    admin_module = await loader.load_on_demand("admin")
    admin_module.run()

    print("admin feature loaded after use:", loader.is_loaded("admin"))


if __name__ == "__main__":
    asyncio.run(main())
```

### Swift

```swift
struct FeatureModule {
    let name: String

    func run() {
        print("running module: " + name)
    }
}

func loadFeatureModule(name: String) async -> FeatureModule {
    FeatureModule(name: name)
}

actor ChunkLoader {
    private var loaded: [String: FeatureModule] = [:]

    func loadOnDemand(_ name: String) async -> FeatureModule {
        if let existing = loaded[name] {
            return existing
        }
        let loadedModule = await loadFeatureModule(name: name)
        loaded[name] = loadedModule
        return loadedModule
    }

    func isLoaded(_ name: String) -> Bool {
        loaded[name] != nil
    }
}

func main() async {
    let loader = ChunkLoader()
    let before = await loader.isLoaded("admin")
    print("admin feature loaded before use: " + String(before))

    let adminModule = await loader.loadOnDemand("admin")
    adminModule.run()

    let after = await loader.isLoaded("admin")
    print("admin feature loaded after use: " + String(after))
}

await main()
```
