---
name: Micro Frontends
slug: micro-frontends
family: 13-frontend-ui
category: Application Architecture
aliases: [Frontend Microservices, Micro Frontend Architecture]
first_described: "Thoughtworks Technology Radar, November 2016"
maturity: established
related: [server-components, islands-architecture, atomic-design]
incompatible_with: []
verified: 2026-08-21
---

# Micro Frontends

## 1. Name, aliases, and lineage

The canonical name is Micro Frontends, an architectural style where
a large frontend application is decomposed into several
independently deliverable applications, each owned by its own team,
composed together into a single experience for the end user. The
technique first appeared on Thoughtworks' own Technology Radar in
November 2016, listed at the earliest, most exploratory ring, and had
moved to the strongly recommended Adopt ring by 2020. Cam Jackson's
2019 article on Martin Fowler's site, the most detailed treatment of
the pattern, defines it directly. "An architectural style where
independently deliverable frontend applications are composed into a
greater whole."

The alias **Frontend Microservices** names the pattern's direct
lineage from the microservices architectural style, applied to the
frontend rather than the backend. **Micro Frontend Architecture** is
a more formal variant of the same name, used interchangeably with the
canonical form.

## 2. Problem and context

A large, single frontend codebase shared by several teams commonly
becomes a bottleneck as the organization grows, every team's change
must pass through the same build pipeline, the same test suite, and
the same release process, so one team's slow or risky change can
block every other team's release, and the codebase's own size and
shared dependencies make it steadily harder for any one team to
reason about the whole. Micro Frontends solves this by splitting the
frontend into several independently deliverable applications, one per
team or one per feature area, each built, tested, and deployed on its
own schedule, composed together into a single experience only at
render time or at build time, rather than sharing one monolithic
codebase, build pipeline, and release schedule.

## 3. Forces

The pattern balances the following competing pressures.

- **Independent team ownership and release schedule.** Favored. Each
  team owns its own micro frontend end to end, choosing its own
  release schedule, its own internal architecture, and in some
  implementations its own framework, without needing to coordinate
  with every other team's release.
- **A consistent end-user experience.** Sacrificed unless actively
  managed. Because each micro frontend can be built and evolved
  independently, keeping a shared visual language, a shared design
  system, and a shared navigation experience across all of them needs
  deliberate, ongoing coordination that a single, unified codebase
  would not need.
- **Reduced coordination overhead between teams.** Favored. Splitting
  the frontend along team boundaries removes the need for every team
  to negotiate a shared build pipeline, shared release windows, and
  shared code review, letting each team move at its own pace.
- **Duplicated dependencies and increased total payload size.**
  Sacrificed unless actively managed. When each micro frontend ships
  its own copy of a shared framework or library, the total amount of
  JavaScript the end user's browser downloads across the whole
  composed page can grow well past what one shared, deduplicated
  bundle would need.

## 4. Applicability and non-applicability

Reach for Micro Frontends when the following hold.

- Several independent teams genuinely need to own, build, and release
  separate parts of a large frontend application on their own
  schedules, and a shared monolithic codebase has become a genuine
  bottleneck to their independence.
- The organization is prepared to invest in the shared infrastructure
  and the shared design system needed to keep the composed
  application feeling consistent to the end user, rather than a
  visibly disjointed patchwork.
- The application is genuinely large enough, and the team structure
  genuinely large enough, that the coordination cost of a single
  shared codebase measurably outweighs the composition and
  consistency cost of splitting it.

Do NOT reach for Micro Frontends in these cases, and the reason
matters more than the rule.

- **The application is built and owned by a single team, or a small
  enough team that coordinating within one shared codebase is not a
  genuine bottleneck**, the composition, deployment, and consistency
  overhead of splitting into several micro frontends is a real cost
  with no team-independence benefit to offset it.
- **The organization is not prepared to invest in a shared design
  system and consistent cross-team conventions**, several
  independently built micro frontends composed without a shared
  visual language usually produce a visibly disjointed end-user
  experience.
- **The total JavaScript payload shipped to the end user is already a
  concern**, since duplicated framework and library code across
  several independently built micro frontends can noticeably
  increase it unless deliberately managed through shared, deduplicated
  dependencies.

## 5. Structure

Micro Frontends has three structural parts.

- **Micro frontends**, the individually owned, independently
  deliverable frontend applications, each responsible for one feature
  area or one part of the overall experience.
- **A composition layer**, the mechanism, at build time, at run time,
  or at the edge, that assembles the several independent micro
  frontends into a single page or a single application for the end
  user.
- **A shared contract**, the agreed conventions, a design system, a
  navigation shell, a communication mechanism between micro frontends,
  that keeps the composed result feeling like one coherent
  application rather than several disconnected pieces.

## 6. ASCII structure diagram

```
  +----------------------------------------------------------------+
  |  Composition layer (build-time, run-time, or edge composition)  |
  |                                                                   |
  |   +------------------+  +------------------+  +---------------+ |
  |   | Checkout team's   |  | Search team's     |  | Account team's | |
  |   | micro frontend     |  | micro frontend     |  | micro frontend | |
  |   | (own release,      |  | (own release,      |  | (own release,  | |
  |   |  own repo)         |  |  own repo)         |  |  own repo)     | |
  |   +------------------+  +------------------+  +---------------+ |
  |                                                                   |
  |   Shared design system, shared navigation shell (the contract)  |
  +----------------------------------------------------------------+
```

## 7. Dynamics

The trace below shows two teams independently releasing their own
micro frontends, composed together into one page for the end user.

```
Independent development and release

the Checkout team makes a change to its micro frontend
   |-- the Checkout team builds, tests, and deploys its own micro
       frontend independently, with no coordination needed from the
       Search or Account teams

the Search team, at a different time, releases its own change
   |-- the Search team's micro frontend is built, tested, and
       deployed on its own separate schedule

Composition at request time

a user requests the composed page
   |-- the composition layer assembles the currently deployed
       versions of the Checkout, Search, and Account micro frontends
       into a single page
   |-- the user sees one coherent experience, unaware that three
       independent teams built and released the pieces separately

Shared contract in effect

each micro frontend renders using the shared design system
   |-- the navigation shell, common across all three micro frontends,
       stays visually consistent regardless of which team last
       released a change
```

## 8. Implementation variants

**Build-time integration.** Each micro frontend is published as a
package, and the composed application is assembled by importing and
bundling those packages together at build time, producing one
combined artifact.

**Run-time integration via iframes.** Each micro frontend renders
inside its own iframe, giving strong isolation of styles and global
state between micro frontends, at the cost of the well-known
usability and communication friction iframes introduce.

**Run-time integration via JavaScript.** Each micro frontend exposes
a mount function that the composition layer calls at run time to
render that micro frontend into a specific region of the page,
without the isolation overhead of an iframe, sharing the same
document and requiring deliberate management of styling and global
state conflicts.

**Edge-side composition.** The composition layer assembles the
several micro frontends' server-rendered fragments at the network
edge, before the response reaches the browser, letting each micro
frontend be independently server-rendered and cached.

## 9. Known production uses

**Cam Jackson's 2019 article on Martin Fowler's site, the most
detailed treatment of the pattern.** Jackson's article defines the
core idea directly. "An architectural style where independently
deliverable frontend applications are composed into a greater whole,"
describing the goal as "breaking up frontend monoliths into many
smaller, more manageable pieces" to increase the effectiveness and
efficiency of teams working at scale. Cam Jackson, "Micro Frontends,"
https://martinfowler.com/articles/micro-frontends.html, verified
2026-08-21.

**Thoughtworks' own Technology Radar, tracking the technique's
adoption over time.** Thoughtworks' Radar describes the core approach
directly. "a web application is broken up by its pages and features,
with each feature being owned end to end by a single team." The
technique first appeared on the Radar in November 2016, and had
progressed to the Adopt ring, Thoughtworks' strongest recommendation,
by 2020. Thoughtworks Technology Radar, "Micro Frontends,"
https://www.thoughtworks.com/en-us/radar/techniques/micro-frontends,
verified 2026-08-21.

## 10. Consequences

Positive.

- Each team owns its own micro frontend end to end, releasing on its
  own schedule without needing to coordinate a shared build pipeline
  or a shared release window with every other team.
- Splitting a large frontend along team boundaries removes a real
  amount of the coordination overhead that a single, shared
  monolithic codebase imposes as an organization and its frontend
  grow.
- A team can, in some implementations, choose its own internal
  framework or architecture for its own micro frontend, independent
  of the choices made by other teams.

Negative.

- Keeping a consistent visual language and a consistent navigation
  experience across several independently built micro frontends needs
  deliberate, ongoing investment in a shared design system, without
  which the composed result reads as visibly disjointed.
- Each micro frontend shipping its own copy of a shared framework or
  library can noticeably increase the total JavaScript payload the
  end user's browser downloads, unless deduplication is deliberately
  managed.
- The composition layer, and the shared contract between micro
  frontends, becomes a new piece of infrastructure the organization
  must build and maintain, a cost a single shared codebase does not
  carry.

## 11. Failure modes and misuse

**Splitting a small, single-team application into several micro
frontends purely to follow the pattern's popularity.** Symptom. The
team now maintains a composition layer, several separate
repositories, and several separate release pipelines, with no
corresponding team-independence benefit, since the same one team
owns all of it anyway. Cause. Adopting the pattern because it is
popular for large organizations, without the actual organizational
scale that makes its coordination-overhead reduction worth its
composition and infrastructure cost. Fix. Keep a small, single-team
application as one shared codebase, and reserve the split for a
genuine multi-team scale where the coordination overhead the split
removes is real.

**Composing several micro frontends with no shared design system,
producing a visibly inconsistent end-user experience.** Symptom.
Different regions of the composed page use different typography,
different spacing, and different interaction patterns, since each
team's micro frontend was built independently with no shared
convention to align them. Cause. Treating team independence as
license to skip the shared design system investment the pattern's own
consistency force depends on. Fix. Invest in and enforce a shared
design system across every micro frontend, treating it as a required
piece of the architecture rather than an optional extra.

**Shipping a duplicated copy of a large shared framework in every
micro frontend, without deduplication.** Symptom. The total
JavaScript payload the composed page ships to the end user grows well
past what a single, shared, deduplicated bundle would need, since
each independently built micro frontend bundled its own full copy of
the same framework. Cause. Treating each micro frontend's independent
build as license to ignore what the other micro frontends on the same
page are already shipping. Fix. Deliberately manage shared,
heavyweight dependencies across micro frontends, through a shared
external dependency, a common build-time deduplication step, or a
runtime module federation mechanism, rather than letting each micro
frontend bundle its own full copy.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Micro Frontends | A single shared monolithic frontend | Islands Architecture | Server Components |
|---|---|---|---|---|
| Independent team release schedule | Strong, by design | Weak, one shared pipeline for everyone | Not directly applicable, a page-composition concern, not a team-ownership one | Not directly applicable |
| Consistent end-user experience by default | Weak, needs deliberate investment | Strong, one shared codebase | Strong, usually one team's page | Strong, usually one team's page |
| Coordination overhead at organizational scale | Low, once split | High, grows with team count | Not applicable at this scale | Not applicable at this scale |
| Duplicated dependency and payload risk | Real, unless managed | Not applicable, one shared bundle | Not applicable, a different concern | Not applicable, a different concern |
| Fit for a small, single-team application | Weak, unneeded overhead | Strong | Strong, if mostly static | Strong, if server-render-heavy |

Reading of the table. Micro Frontends wins specifically at genuine
multi-team organizational scale, where the coordination overhead of a
single shared codebase has become a real, measured cost. A small,
single-team application, or a page whose real problem is JavaScript
payload rather than team coordination, is usually better served by a
single shared codebase, Islands Architecture, or Server Components
instead.

## 13. Related and incompatible patterns

- **Islands Architecture.** A different, page-level composition
  concern, addressing how much JavaScript a single page ships, that
  is sometimes combined with Micro Frontends when each independently
  owned micro frontend also wants to minimize its own client-side
  JavaScript footprint.
- **Server Components.** A complementary technique some micro
  frontend implementations use internally to reduce the JavaScript
  each individual micro frontend ships, addressing the payload
  concern named in dimension 10 at the level of one micro frontend
  rather than across all of them.
- **Atomic Design.** A component-organization methodology that
  several independently built micro frontends can share as their
  common design system vocabulary, directly supporting the shared
  contract named in dimension 5.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an organization whose single, shared frontend
codebase has become a genuine bottleneck to independent team release.

1. Confirm the organization has genuinely reached a scale where the
   coordination overhead of a single shared codebase measurably
   outweighs the cost of splitting it, rather than adopting the
   pattern because it is popular.
2. Identify natural team or feature boundaries along which the
   frontend can be split into independently ownable pieces.
3. Choose a composition mechanism, build time, run time, or edge,
   matched to the organization's actual deployment infrastructure and
   consistency needs.
4. Establish the shared contract, a design system, a navigation shell,
   and a communication mechanism between micro frontends, before
   splitting the codebase, not after.
5. Split the codebase incrementally, one feature area at a time,
   verifying the composed experience remains consistent after each
   split.

Removing the pattern when it stops earning its place, most relevant
when the organization or team structure has consolidated enough that
the independent-release benefit no longer outweighs the composition
and consistency overhead.

1. Confirm the team structure has genuinely consolidated, rather than
   assuming so without review.
2. Merge the several micro frontends back into a single shared
   codebase, preserving each feature's external behavior so end users
   see no visible change.
3. Retire the composition layer and the cross-micro-frontend shared
   contract once the merge is complete.

## 15. Testing and verification

Easier because of the pattern.

- Each micro frontend can be tested in isolation, independent of the
  other micro frontends it is eventually composed with, since each
  team owns and can validate its own piece end to end.
- A team can release and verify its own micro frontend's change
  without needing to run the full test suite of every other team's
  micro frontend, since the pieces are independently deliverable.

Harder because of the pattern.

- Testing the fully composed experience, confirming several
  independently built micro frontends genuinely work correctly
  together on the same page, needs an integration test environment
  that assembles real or representative versions of all of them, a
  setup a single shared codebase would not need.
- A visual or behavioral regression introduced by one micro
  frontend's change can only be caught by testing the composed page,
  since testing that micro frontend in isolation would not surface an
  interaction with another team's piece.

Techniques that apply.

- **Isolated micro frontend unit and component tests.** Test each
  micro frontend's own behavior directly, independent of the
  composition layer or any other micro frontend.
- **Contract tests between micro frontends and the composition
  layer.** Assert each micro frontend correctly implements the
  agreed mount interface or communication contract the composition
  layer depends on.
- **Composed integration tests.** Assemble representative versions of
  every micro frontend together and test the full, composed
  experience, catching an interaction bug isolated tests would miss.
- **Visual regression testing on the composed page.** Render the
  fully composed page and compare against a known-good screenshot,
  catching a visual inconsistency introduced by one team's change
  that clashes with another team's micro frontend.

## 16. Observability signals

Micro Frontends has a genuine runtime footprint, since it directly
affects how many independent pieces of JavaScript a real user's
browser downloads and how they are composed together, so a dedicated
production signal is honest here.

What to record.

- The total JavaScript payload actually shipped for a composed page,
  broken down by which micro frontend contributed which portion,
  since an unexpectedly large total payload often traces to a single
  micro frontend bundling a heavyweight dependency other micro
  frontends already ship.
- The error rate and load success of each individual micro frontend
  within the composed page, since a failure in one micro frontend
  should ideally degrade gracefully rather than breaking the entire
  composed page.

A healthy state. The total composed payload stays close to what a
deduplicated, shared-dependency approach would produce, and a failure
in one micro frontend degrades only that micro frontend's region of
the page rather than the whole composed experience.

A failing state. The total composed payload growing well past what a
single shared bundle would need, pointing at undeduplicated shared
dependencies across micro frontends, or a failure in one micro
frontend taking down the entire composed page, pointing at a
composition layer with no failure isolation between the pieces.

## 17. Security and privacy implications

Micro Frontends carries a real security implication, since composing
several independently built and independently deployed pieces of
code into one page introduces a genuine trust boundary between them.

**A composed page assembling micro frontends built and deployed by
different teams, and in some organizations by different vendors,
means a vulnerability or a supply-chain compromise in any single
micro frontend can affect the entire composed page,
unless the composition mechanism enforces genuine isolation, such as
an iframe boundary or a strict content security policy, between
them.** Because run-time JavaScript composition without iframe
isolation shares the same document, global scope, and cookies across
every micro frontend on the page, a team adopting this variant should
apply the same trust and review standard to every micro frontend on
the page that it would apply to its own code, and consider a stronger
isolation mechanism when the micro frontends genuinely come from
different, independently trusted teams or vendors.

## 18. References

1. Cam Jackson. "Micro Frontends".
   https://martinfowler.com/articles/micro-frontends.html
   Verified 2026-08-21. Source of the defining sentence and the
   frontend-monolith framing quoted in dimensions 1 and 9.
2. Thoughtworks Technology Radar. "Micro Frontends".
   https://www.thoughtworks.com/en-us/radar/techniques/micro-frontends
   Verified 2026-08-21. Source of the November 2016 origin, the
   feature-team ownership description, and the Adopt ring status
   quoted in dimensions 1 and 9.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models a minimal composition
layer, each micro frontend exposing a mount function the composition
layer calls at run time, the way a JavaScript run-time composition
implementation structures the concept, kept free of JSX and any
specific framework's package so the sample compiles as plain
TypeScript. Python shows the same conceptual split using a minimal,
framework-agnostic registry of independently registered application
fragments composed into one page, since Python has no single dominant
micro-frontend UI framework the way TypeScript has several run-time
composition libraries. Swift shows the pattern using a minimal
protocol-driven model where independently implemented modules are
composed into one root view, closely analogous to how modular
composition is reasoned about in a native, multi-team mobile context.
Java, Go, and Rust are omitted, since none has a dominant, idiomatic
UI-component framework this specifically frontend composition pattern
maps to as directly as TypeScript and Swift do.

### TypeScript

```typescript
interface MicroFrontend {
  name: string;
  mount(containerId: string): void;
}

class CheckoutMicroFrontend implements MicroFrontend {
  name = "checkout";

  mount(containerId: string): void {
    console.log("mounting " + this.name + " into " + containerId);
  }
}

class SearchMicroFrontend implements MicroFrontend {
  name = "search";

  mount(containerId: string): void {
    console.log("mounting " + this.name + " into " + containerId);
  }
}

class CompositionLayer {
  private registered: Map<string, MicroFrontend> = new Map();

  register(microFrontend: MicroFrontend): void {
    this.registered.set(microFrontend.name, microFrontend);
  }

  composePage(regions: Record<string, string>): void {
    for (const [name, containerId] of Object.entries(regions)) {
      const microFrontend = this.registered.get(name);
      if (microFrontend !== undefined) {
        microFrontend.mount(containerId);
      }
    }
  }
}

const composition = new CompositionLayer();
composition.register(new CheckoutMicroFrontend());
composition.register(new SearchMicroFrontend());

composition.composePage({ checkout: "checkout-region", search: "search-region" });
```

### Python

```python
from dataclasses import dataclass, field


@dataclass
class MicroFrontend:
    name: str

    def mount(self, container_id: str) -> None:
        print(f"mounting {self.name} into {container_id}")


@dataclass
class CompositionLayer:
    registered: dict[str, MicroFrontend] = field(default_factory=dict)

    def register(self, micro_frontend: MicroFrontend) -> None:
        self.registered[micro_frontend.name] = micro_frontend

    def compose_page(self, regions: dict[str, str]) -> None:
        for name, container_id in regions.items():
            micro_frontend = self.registered.get(name)
            if micro_frontend is not None:
                micro_frontend.mount(container_id)


if __name__ == "__main__":
    composition = CompositionLayer()
    composition.register(MicroFrontend(name="checkout"))
    composition.register(MicroFrontend(name="search"))

    composition.compose_page({"checkout": "checkout-region", "search": "search-region"})
```

### Swift

```swift
protocol MicroFrontend {
    var name: String { get }
    func mount(containerId: String)
}

struct CheckoutMicroFrontend: MicroFrontend {
    let name = "checkout"

    func mount(containerId: String) {
        print("mounting " + name + " into " + containerId)
    }
}

struct SearchMicroFrontend: MicroFrontend {
    let name = "search"

    func mount(containerId: String) {
        print("mounting " + name + " into " + containerId)
    }
}

final class CompositionLayer {
    private var registered: [String: MicroFrontend] = [:]

    func register(_ microFrontend: MicroFrontend) {
        registered[microFrontend.name] = microFrontend
    }

    func composePage(regions: [String: String]) {
        for (name, containerId) in regions {
            if let microFrontend = registered[name] {
                microFrontend.mount(containerId: containerId)
            }
        }
    }
}

let composition = CompositionLayer()
composition.register(CheckoutMicroFrontend())
composition.register(SearchMicroFrontend())

composition.composePage(regions: ["checkout": "checkout-region", "search": "search-region"])
```
