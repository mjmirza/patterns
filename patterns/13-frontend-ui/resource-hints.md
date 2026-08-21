---
name: Resource Hints
slug: resource-hints
family: 13-frontend-ui
category: Loading Strategy
aliases: [Link Rel Hints, Speculative Loading, dns-prefetch and preconnect]
first_described: "MDN, link rel preload and Speculative loading documentation"
maturity: canonical
related: [prpl-pattern, code-splitting, route-based-lazy-loading]
incompatible_with: []
verified: 2026-08-21
---

# Resource Hints

## 1. Name, aliases, and lineage

The canonical name is Resource Hints, a family of link rel
declarations placed in a page's head that tell the browser about
resources or origins the page is likely to need, so the browser can
begin fetching, resolving, or connecting to them earlier than it
otherwise would discover the need. MDN's own documentation for the
preload value states the mechanism directly. "The preload value of
the link element's rel attribute lets you declare fetch requests in
the HTML's head, specifying resources that your page will need very
soon, which you want to start loading early in the page lifecycle,
before browsers' main rendering machinery kicks in."

The alias **Link Rel Hints** names the family by its shared HTML
syntax rather than any single member. **Speculative Loading** is
MDN's own umbrella term for the group, covering preload, prefetch,
dns-prefetch, and preconnect together as related but distinct
techniques. **dns-prefetch and preconnect** names the two
connection-level hints specifically, as distinct from the two
resource-level hints, preload and prefetch.

## 2. Problem and context

A browser discovers most of a page's resources by parsing its HTML
and CSS as it goes, which means a resource referenced deep in a
stylesheet, or fetched only after a script runs, is not discovered
until the browser reaches that specific point in parsing or
execution. For a resource the page will need soon, or an origin the
page is about to make a request to, waiting for natural discovery
wastes real time the browser could have spent connecting or fetching
in parallel with everything else already happening. Resource Hints
solve this by letting a developer declare, ahead of natural
discovery, exactly which resources or origins deserve early attention,
and by distinguishing several different kinds of hint, each with a
different scope and a different cost, so a developer can pick the
narrowest, cheapest hint that actually addresses the specific delay
they are trying to remove.

## 3. Forces

The pattern balances the following competing pressures.

- **Removing a real, measured discovery delay.** Favored. A resource
  or origin a page genuinely needs soon, but that natural parsing and
  execution would only discover late, benefits directly from a hint
  that starts the relevant work earlier.
- **Bandwidth and connection budget.** Sacrificed when overused. Every
  hint asks the browser to spend real network and connection
  resources ahead of confirmed need, and a page issuing many hints for
  resources it does not end up using wastes exactly the resources the
  pattern exists to use well.
- **Precision of scope, matching the hint to the actual need.**
  Favored, through the deliberate distinction between hint types.
  MDN's own documentation distinguishes preload, for the current
  page's high-priority subresources, from prefetch, for pre-populating
  the cache ahead of a likely future navigation, and from
  dns-prefetch and preconnect, for the connection-level cost of
  resolving and reaching an origin before any specific resource
  request is made.
- **Simplicity of the page's head.** Sacrificed. Each hint is one more
  declaration a developer must add, justify, and keep in sync with
  what the page actually ends up needing as the application evolves.

## 4. Applicability and non-applicability

Reach for Resource Hints when the following hold.

- A specific resource is genuinely needed very soon after the page
  loads, but is not discoverable early through normal HTML or CSS
  parsing, such as a font referenced only inside a stylesheet, or a
  script-injected image.
- A specific future navigation is genuinely likely, such as the next
  page in a well-established multi-step flow, making the prefetch
  hint's speculative cache-population worthwhile.
- A third-party origin the page is about to request something from is
  known ahead of the actual request, making a dns-prefetch or
  preconnect hint for that origin's connection setup worthwhile.
- The team can measure, or has reason to expect, that the hint
  genuinely removes time from a real discovery delay, rather than
  adding a hint speculatively with no specific measured problem in
  mind.

Do NOT reach for Resource Hints in these cases, and the reason
matters more than the rule.

- **The resource is already discoverable early through normal parsing**,
  such as an image referenced directly in the initial HTML, adding a
  preload hint for something the browser was already going to fetch
  early provides no real benefit and only adds a redundant
  declaration.
- **The future navigation being prefetched is genuinely uncertain**,
  speculatively prefetching every link on a page wastes bandwidth on
  the large share of links a user will never click, particularly
  costly on a metered or constrained connection.
- **The team is adding hints without measuring whether they help**,
  since MDN's own documentation notes preload only schedules a
  download with higher priority rather than executing anything, a
  poorly scoped or excessive set of preload hints can crowd out the
  bandwidth genuinely critical resources need, making load time worse
  rather than better.

## 5. Structure

Resource Hints have four commonly used members, each with a distinct
scope.

- **preload**, declaring a resource the current page needs very soon,
  scheduling it for high-priority download and caching in a
  per-document, in-memory cache, without executing it.
- **prefetch**, declaring a resource likely needed for a future
  navigation, populating the browser's on-disk HTTP cache ahead of
  that navigation actually happening.
- **dns-prefetch**, declaring an origin the page is likely to request
  from, resolving that origin's DNS ahead of the actual request.
- **preconnect**, declaring an origin the page is likely to request
  from, performing DNS resolution together with the TCP and TLS
  handshake ahead of the actual request, a strict superset of what
  dns-prefetch alone does.

## 6. ASCII structure diagram

```
  Page head, before natural parsing discovers the resource

  link rel=preload href=hero-font.woff2 as=font
       |
       v
  browser begins fetching hero-font.woff2 immediately,
  high priority, before the stylesheet referencing it
  would otherwise have been discovered

  link rel=prefetch href=/next-step
       |
       v
  browser fetches /next-step into the on-disk cache,
  low priority, ready if the user actually goes there

  link rel=preconnect href=https://api.example.com
       |
       v
  browser resolves DNS, opens TCP, completes TLS handshake
  for api.example.com ahead of the first real request to it
```

## 7. Dynamics

The trace below shows a page declaring all three hint types and the
browser acting on each at a different point.

```
Page load begins

the browser starts parsing the page's HTML
   |-- it encounters a preload hint for a font the page's
       stylesheet will reference later
   |-- it begins fetching that font immediately, at high priority,
       well before the stylesheet parsing would have discovered it
   |-- it encounters a preconnect hint for a third-party API origin
   |-- it begins resolving DNS and completing the connection
       handshake for that origin immediately

Page becomes interactive

the stylesheet finishes parsing and references the font
   |-- the font is already fetched, or well underway, so the text
       using it renders without the delay a late-discovered font
       fetch would have caused

the page later makes a request to the preconnected API origin
   |-- the connection is already established, so the request
       skips the DNS, TCP, and TLS setup delay it would otherwise
       have paid at request time

Prefetch, a separate flow

the browser encounters a prefetch hint for a likely next page
   |-- it fetches that page into the on-disk HTTP cache, at low
       priority, without blocking anything on the current page
   |-- if the user later goes to that page, it loads from
       cache rather than the network
   |-- if the user never goes there, the prefetched resource
       is simply unused, its cost limited to the bandwidth spent
       fetching it speculatively
```

## 8. Implementation variants

**Static, hand-authored hints.** A developer adds link rel
declarations directly to a page's HTML, choosing specific resources
and origins based on their own knowledge of what the page needs.

**Build-tool generated hints.** A bundler or framework inspects the
page's actual dependency graph and automatically injects preload
hints for the resources it determines the initial render genuinely
needs, removing the burden of manually keeping hints in sync with the
application's real dependencies.

**Framework-level navigation prefetching.** A client-side router
automatically issues a prefetch hint, or an equivalent fetch, for a
link the user hovers over or that scrolls into view, treating that
signal as evidence the navigation is likely enough to be worth the
speculative cost.

**Server-driven hints via HTTP headers.** Some servers can send an
equivalent hint via the HTTP Link response header rather than an
HTML tag, letting the browser learn about a resource to preload
before it has even finished receiving the page's HTML.

## 9. Known production uses

**MDN's own documentation, defining preload.** MDN states the
mechanism directly. "The preload value of the link element's rel
attribute lets you declare fetch requests in the HTML's head,
specifying resources that your page will need very soon, which you
want to start loading early in the page lifecycle, before browsers'
main rendering machinery kicks in," adding that it "doesn't load and
execute the script but only schedules it to be downloaded and cached
with a higher priority." MDN Web Docs, "rel=preload,"
https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/rel/preload,
verified 2026-08-21.

**MDN's own documentation, defining prefetch, dns-prefetch, and
preconnect.** MDN's speculative loading guide states each hint's
purpose directly. "link rel=prefetch provides a hint to browsers
that the user is likely to need the target resource for future
navigations." "link rel=dns-prefetch provides a hint to browsers that
the user is likely to need resources from the specified resource's
origin," and preconnect is described as identical to dns-prefetch
"except that it only handles the DNS part," since preconnect performs
"part or all of the connection handshake, DNS plus TCP plus TLS."
MDN Web Docs, "Speculative loading,"
https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Speculative_loading,
verified 2026-08-21.

## 10. Consequences

Positive.

- A resource or origin the page genuinely needs soon starts being
  fetched, resolved, or connected to earlier than natural discovery
  would have found it, directly removing measured delay.
- The distinction between preload, prefetch, dns-prefetch, and
  preconnect lets a developer choose a hint scoped precisely to the
  actual need, current-page resource versus future navigation versus
  connection setup, rather than a single blunt mechanism for all
  three.
- Because preload only schedules a download rather than executing
  anything, MDN's own documentation notes it does not risk running
  code the page does not otherwise need, keeping the hint's cost
  limited to bandwidth.

Negative.

- A hint issued for a resource or origin the page does not actually
  end up using wastes real bandwidth and connection resources, the
  exact cost the pattern exists to spend well rather than wastefully.
- An excessive set of preload hints can crowd out bandwidth the
  page's genuinely critical resources need, making load time worse
  rather than better.
- Hints must be kept in sync with what the page actually references,
  and a hint for a resource that has since been removed or renamed
  becomes dead weight that no longer helps anything.

## 11. Failure modes and misuse

**Adding a preload hint for a resource the browser was already going
to discover early through normal parsing.** Symptom. No measurable
improvement in load time, and the hint adds a redundant declaration
with no corresponding benefit. Cause. Adding hints speculatively,
without confirming the specific resource was genuinely a late
discovery in the first place. Fix. Confirm, through profiling, that
the targeted resource is actually discovered late before adding a
hint for it, reserving the hint for resources that genuinely benefit.

**Prefetching every link on a page regardless of how likely the user
is to click it.** Symptom. A real amount of bandwidth is spent
fetching pages the user never visits, particularly costly on a
metered or constrained connection. Cause. Applying prefetch broadly,
to every link, rather than scoping it to navigations genuinely likely
given the page's actual flow. Fix. Scope prefetch to links with a
real, evidenced likelihood of being clicked next, such as the
established next step in a multi-step flow, or a link the user has
specifically hovered over.

**Confusing preconnect's connection-level cost with preload's
resource-level cost, and preconnecting to an origin far in advance of
any real request.** Symptom. The connection opened by a preconnect
hint sits idle and may time out before the page actually makes a
request to that origin, wasting the setup cost entirely. Cause.
Treating preconnect as a low-cost, always-safe hint to add for any
third-party origin, rather than scoping it to an origin the page
genuinely requests from soon after the hint fires. Fix. Reserve
preconnect for an origin the page will genuinely request from shortly
after the page loads, and prefer dns-prefetch alone, a cheaper hint,
for an origin whose exact request timing is less certain.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Resource Hints | No hints, natural discovery only | Eager fetch of everything up front |
|---|---|---|---|
| Removing a real discovery delay | Strong, when precisely scoped | Weak, the browser waits for natural discovery | Strong, but at a real cost |
| Bandwidth and connection budget | Moderate, spent deliberately on confirmed needs | Strong, nothing extra spent | Weak, everything is fetched regardless of actual need |
| Precision of scope | Strong, four distinct hint types for four distinct needs | Not applicable, no hinting mechanism | Weak, no distinction between urgent and non-urgent resources |
| Simplicity of the page's head | Weak, hints must be added and kept in sync | Strong, nothing to maintain | Weak, requires its own coordination |

Reading of the table. Resource Hints win specifically when a team can
identify, and confirm through measurement, a genuine late-discovery
delay or a genuinely likely future navigation, and is willing to
maintain a small, precisely scoped set of declarations. A page with
no such measured delay gains nothing from adding hints, and a team
tempted to eagerly fetch everything up front pays a much larger,
less targeted bandwidth cost than a well-scoped hint would.

## 13. Related and incompatible patterns

- **PRPL Pattern.** The preload step of PRPL is built directly on
  the preload resource hint, and Resource Hints more broadly support
  the pattern's goal of fetching exactly what the initial route needs
  as early as possible.
- **Code Splitting.** A complementary technique, splitting a bundle
  into pieces gives a team specific, smaller resources it can then
  choose to preload or prefetch individually, rather than hinting at
  an undifferentiated single bundle.
- **Route-based Lazy Loading.** The prefetch hint is frequently paired
  with route-based lazy loading, prefetching a lazily loaded route's
  code ahead of the user actually visiting it.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a page that currently relies entirely on
natural resource discovery.

1. Profile the page's actual load timeline to identify a specific
   resource that is discovered later than it is genuinely needed, or
   a future navigation that is genuinely likely.
2. For a late-discovered but currently needed resource, add a
   preload hint scoped specifically to it, and confirm the fetch now
   starts earlier through profiling.
3. For a likely future navigation, add a prefetch hint scoped to that
   specific destination, rather than every link on the page.
4. For a third-party origin the page requests from soon after load,
   add a preconnect hint, or dns-prefetch alone if the exact request
   timing is less certain.
5. Re-measure the page's load timeline to confirm each added hint
   produced a real, measured improvement, removing any hint that did
   not.

Removing the pattern when it stops earning its place, most relevant
when a hinted resource or navigation is no longer part of the page.

1. Confirm the hinted resource, origin, or navigation destination is
   genuinely no longer relevant, rather than assuming so without
   checking the current page.
2. Remove the specific hint declaration for that resource, origin, or
   destination.
3. Re-measure the page's load timeline to confirm removing the hint
   did not reintroduce the original discovery delay.

## 15. Testing and verification

Easier because of the pattern.

- A test can assert a specific preload or prefetch hint's presence in
  the rendered page's head, catching a regression where a build
  change accidentally drops a hint the team has confirmed matters.
- Because each hint targets a specific, named resource or origin, a
  test can assert that the hinted target still exists in the
  application, catching a stale hint left behind after a resource was
  renamed or removed.

Harder because of the pattern.

- Verifying the actual performance benefit needs measuring real
  network timing, since a hint's presence in the markup says nothing
  about whether it produced a measurable improvement.
- Confirming a preconnect hint's timing is well matched to the actual
  request that follows it needs a real or realistically simulated
  network trace, since a preconnect that fires too early relative to
  the request it supports may have already timed out by the time it
  is used.

Techniques that apply.

- **Hint presence assertions.** Directly test that a specific,
  confirmed-important hint is present in the rendered page's head.
- **Stale hint detection.** Assert every hinted resource or origin
  still exists in the current application, catching hints left behind
  after the thing they targeted changed.
- **Network trace comparison.** Compare a page's load timeline with
  and without a specific hint, confirming the hint produces a real,
  measured improvement rather than assuming it does.
- **Bandwidth budget assertions.** Assert the total number and
  combined size of hinted resources stays under an explicit budget, so
  hints do not silently accumulate into their own excess.

## 16. Observability signals

Resource Hints have a genuine, measurable runtime footprint, since
they directly govern what a real user's browser fetches, resolves, or
connects to before it is otherwise asked to, so a dedicated
production signal is honest here.

What to record.

- The share of preloaded or prefetched resources that are actually
  used by the page shortly after being fetched, since a low share
  points at hints scoped too broadly, wasting bandwidth on resources
  the user does not end up needing.
- The measured time saved on the specific delay each hint targets, the
  time to a preloaded font rendering, or the time to a preconnected
  origin's first real request completing, since this is the direct
  evidence a hint is earning the bandwidth it costs.

A healthy state. A high share of hinted resources are genuinely used
shortly after being hinted, and the specific delay each hint targets
shows a measurable, confirmed improvement over not having the hint.

A failing state. A real share of hinted resources are fetched
but never used, pointing at hints scoped too broadly or targeting
navigations that turn out unlikely, or the specific delay a hint was
meant to remove shows no measurable improvement, pointing at a hint
that is not actually addressing the discovery delay it was intended
for.

## 17. Security and privacy implications

Resource Hints carry a real, specific privacy implication worth
naming directly, since they cause a browser to make a network
request, DNS lookup, or connection the user did not directly ask for.

**A prefetch, dns-prefetch, or preconnect hint for a third-party
origin reveals to that origin, and to any network observer between
the user and that origin, that the user visited a page containing
that hint, even when the user never actually visits or requests
anything from the hinted destination, since the DNS lookup or
connection setup itself is a real, observable network event.**
Because a hint can leak this signal even when the resource it targets
is never actually used, a team should scope hints for third-party
origins deliberately, considering the same privacy implications a
direct request to that origin would carry, rather than treating a
hint as a lower-risk action than an actual fetch simply because it is
speculative.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models a resource hint
manager that constructs a list of the four hint types, kept free of
JSX and any specific framework's package so the sample compiles as
plain TypeScript. Python shows the conceptual shape of the same
hint-selection logic using a minimal, framework-agnostic hint
builder, since Python has no browser runtime and therefore no single
dominant resource-hint implementation the way TypeScript has the
HTML link element and the Fetch API context it operates in. Swift
shows the same conceptual shape using a minimal model, analogous to
how a native app might reason about prefetching a likely-next
screen's data ahead of the user actually visiting it. Java, Go,
and Rust are omitted, since none has a dominant, idiomatic
browser-facing UI framework this specifically HTML-head-declared
pattern maps to as directly as TypeScript does.

### TypeScript

```typescript
type HintType = "preload" | "prefetch" | "dns-prefetch" | "preconnect";

interface ResourceHint {
  type: HintType;
  href: string;
  asType?: string;
}

function buildHintLine(hint: ResourceHint): string {
  const asPart = hint.asType ? ", as=" + hint.asType : "";
  return "rel=" + hint.type + ", href=" + hint.href + asPart;
}

class ResourceHintManager {
  private hints: ResourceHint[] = [];

  preload(href: string, asType: string): void {
    this.hints.push({ type: "preload", href, asType });
  }

  prefetch(href: string): void {
    this.hints.push({ type: "prefetch", href });
  }

  preconnect(origin: string): void {
    this.hints.push({ type: "preconnect", href: origin });
  }

  dnsPrefetch(origin: string): void {
    this.hints.push({ type: "dns-prefetch", href: origin });
  }

  renderLines(): string[] {
    return this.hints.map(buildHintLine);
  }
}

const manager = new ResourceHintManager();
manager.preload("hero-font.woff2", "font");
manager.preconnect("https://api.example.com");
manager.prefetch("/next-step");

for (const line of manager.renderLines()) {
  console.log(line);
}
```

### Python

```python
from dataclasses import dataclass, field
from enum import Enum


class HintType(str, Enum):
    PRELOAD = "preload"
    PREFETCH = "prefetch"
    DNS_PREFETCH = "dns-prefetch"
    PRECONNECT = "preconnect"


@dataclass
class ResourceHint:
    type: HintType
    href: str
    as_type: str | None = None


def build_hint_line(hint: ResourceHint) -> str:
    as_part = f", as={hint.as_type}" if hint.as_type else ""
    return f"rel={hint.type.value}, href={hint.href}{as_part}"


@dataclass
class ResourceHintManager:
    hints: list[ResourceHint] = field(default_factory=list)

    def preload(self, href: str, as_type: str) -> None:
        self.hints.append(ResourceHint(HintType.PRELOAD, href, as_type))

    def prefetch(self, href: str) -> None:
        self.hints.append(ResourceHint(HintType.PREFETCH, href))

    def preconnect(self, origin: str) -> None:
        self.hints.append(ResourceHint(HintType.PRECONNECT, origin))

    def dns_prefetch(self, origin: str) -> None:
        self.hints.append(ResourceHint(HintType.DNS_PREFETCH, origin))

    def render_lines(self) -> list[str]:
        return [build_hint_line(hint) for hint in self.hints]


if __name__ == "__main__":
    manager = ResourceHintManager()
    manager.preload("hero-font.woff2", "font")
    manager.preconnect("https://api.example.com")
    manager.prefetch("/next-step")

    for line in manager.render_lines():
        print(line)
```

### Swift

```swift
enum HintType: String {
    case preload
    case prefetch
    case dnsPrefetch = "dns-prefetch"
    case preconnect
}

struct ResourceHint {
    let type: HintType
    let href: String
    let asType: String?
}

func buildHintLine(_ hint: ResourceHint) -> String {
    let asPart = hint.asType.map { ", as=" + $0 } ?? ""
    return "rel=" + hint.type.rawValue + ", href=" + hint.href + asPart
}

final class ResourceHintManager {
    private(set) var hints: [ResourceHint] = []

    func preload(_ href: String, asType: String) {
        hints.append(ResourceHint(type: .preload, href: href, asType: asType))
    }

    func prefetch(_ href: String) {
        hints.append(ResourceHint(type: .prefetch, href: href, asType: nil))
    }

    func preconnect(_ origin: String) {
        hints.append(ResourceHint(type: .preconnect, href: origin, asType: nil))
    }

    func dnsPrefetch(_ origin: String) {
        hints.append(ResourceHint(type: .dnsPrefetch, href: origin, asType: nil))
    }

    func renderLines() -> [String] {
        hints.map(buildHintLine)
    }
}

let manager = ResourceHintManager()
manager.preload("hero-font.woff2", asType: "font")
manager.preconnect("https://api.example.com")
manager.prefetch("/next-step")

for line in manager.renderLines() {
    print(line)
}
```

## 18. References

1. MDN Web Docs. "rel=preload".
   https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/rel/preload
   Verified 2026-08-21. Source of the defining preload quote used in
   dimensions 1, 3, and 9.
2. MDN Web Docs. "Speculative loading".
   https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Speculative_loading
   Verified 2026-08-21. Source of the prefetch, dns-prefetch, and
   preconnect quotes used in dimensions 3, 5, and 9.
