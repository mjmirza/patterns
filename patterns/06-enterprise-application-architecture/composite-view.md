---
name: Composite View
slug: composite-view
family: 06-enterprise-application-architecture
category: Enterprise Application Architecture
aliases: [Template View Composition, Modular View Assembly]
first_described: "Deepak Alur, John Crupi, Dan Malks, Core J2EE Patterns, 2nd Edition, Prentice Hall, 2003, ISBN 0-13-142246-4"
maturity: established
related: [composite, view-helper]
incompatible_with: []
verified: 2026-08-23
---

# Composite View

## 1. Name, aliases, and lineage

A Composite View assembles a page from smaller, independently reusable
subviews, such as a header, a footer, and a body, so each subview's own
content and each subview's own placement in the overall layout can change
without the others needing to change with it.

This entry sources it directly from the corejeepatterns.com companion
site to the book that named it, retrieved live from the Internet
Archive's Wayback Machine after the site's own live hosting stopped
resolving. "you want to build a view from modular, atomic component parts
that are combined to create a composite whole, while managing the content
and the layout independently" is the pattern's own stated Problem,
verbatim (Deepak Alur, John Crupi, Dan Malks, "Composite View," Core J2EE
Patterns companion site, archived snapshot,
https://web.archive.org/web/20211228031740/http://corej2eepatterns.com/CompositeView.htm,
archived 28 December 2021, verified 2026-08-23, excerpted from Core J2EE
Patterns, 2nd Edition, Prentice Hall, 2003).

## 2. Problem and context

A page is commonly built from parts that are shared across many other
pages, a header, a footer, a navigation block, and duplicating those
shared parts directly inside every page that uses them means a single
layout change has to be repeated everywhere that duplicate lives.

## 3. Forces

The archived source names three forces directly, verbatim. "you want
common subviews, such as headers, footers and tables reused in multiple
views, which may appear in different locations within each page layout,"
"you have content in subviews which might frequently change or might be
subject to certain access controls, such as limiting access to users in
certain roles," and "you want to avoid directly embedding and duplicating
subviews in multiple views which makes layout changes difficult to manage
and maintain" (Alur, Crupi, Malks, "Composite View," verified 2026-08-23).

## 4. Applicability and non-applicability

The archived source names its own Consequences directly, quoted in full
under dimension 10, including "reduces maintainability" and "reduces
performance" as two directly named costs, so the pattern does not apply
where a page has no genuinely reusable subviews to extract, adding the
composition machinery with nothing shared to justify it.

## 5. Structure

The archived source's own stated Solution names the structural shape
directly. "use Composite Views that are composed of multiple atomic
subviews. Each subview of the overall template can be included
dynamically in the whole, and the layout of the page can be managed
independently of the content" (Alur, Crupi, Malks, "Composite View,"
verified 2026-08-23), naming the same page-versus-part relationship
directly to this catalogue's own already published Composite entry.
"a Composite View is based on Composite [GoF], which describes part-whole
hierarchies where a composite object is composed of numerous subparts"
(Alur, Crupi, Malks, "Composite View," Core J2EE Patterns companion site,
archived snapshot,
https://web.archive.org/web/20211228031740/http://corej2eepatterns.com/CompositeView.htm,
verified 2026-08-23).

## 6. ASCII structure diagram

```
  +---------------------------------------------------+
  | Composite View, one overall template                 |
  |                                                       |
  |  +----------+  +----------------------+  +----------+  |
  |  | header    |  | body, this catalogue's |  | footer    |  |
  |  | subview   |  | own View Helper entry  |  | subview   |  |
  |  +----------+  +----------------------+  +----------+  |
  +---------------------------------------------------+

  content and layout managed independently, per dimension 5
```

## 7. Dynamics

The archived source names its own strategy families under dimension 8,
which govern how the composite is actually assembled at runtime, one of
the six directly named, "Early-Binding Resource Strategy" and
"Late-Binding Resource Strategy," naming a real, runtime choice, whether
each subview's own source is fixed at compile time or resolved dynamically
each time the composite is rendered.

## 8. Implementation variants

The archived source names six strategy variants directly. "JavaBean View
Management Strategy," "Standard Tag View Management Strategy," "Custom
Tag View Management Strategy," "Transformer View Management Strategy,"
"Early-Binding Resource Strategy," and "Late-Binding Resource Strategy"
(Alur, Crupi, Malks, "Composite View," verified 2026-08-23).

## 9. Known production uses

The pattern is documented as one of the named presentation-tier patterns
listed in the same source's own site navigation, alongside Intercepting
Filter, Context Object, Front Controller, Application Controller, and
View Helper (Alur, Crupi, Malks, "Composite View," verified 2026-08-23),
the reference catalogue for the J2EE platform's own enterprise
application architecture, per dimension 1.

## 10. Consequences

The archived source names its own Consequences directly, verbatim, as a
list. "improves modularity and reuse," "adds role-based or policy-based
control," "enhances maintainability," "reduces maintainability," and
"reduces performance" (Alur, Crupi, Malks, "Composite View," verified
2026-08-23), naming both directly stated benefits and two directly named
costs in the same list, one of which is a maintainability cost sitting
alongside a maintainability benefit.

## 11. Failure modes and misuse

The source's own named performance cost under dimension 4 and 10 is the
sharpest directly sourced risk, decomposing a page into many small,
dynamically included subviews adds real per-request assembly overhead,
which the archived source names plainly as "reduces performance" with no
qualification on when that cost is or is not worth paying.

## 12. Trade-off matrix

| Dimension | With a Composite View | Duplicating shared markup per page |
|---|---|---|
| Layout change across many pages | One place, dimension 3 | Repeated in every duplicate |
| Access control per subview | Named as possible, dimension 3 and 10 | Ad hoc per page |
| Rendering performance | A named cost, dimension 4, 10, and 11 | No composition overhead |
| Modularity and reuse | Improved, dimension 10 | Low, content is duplicated |

## 13. Related and incompatible patterns

This entry cross-references this catalogue's own already published
Composite entry directly, per the archived source's own directly stated
lineage already quoted in full under dimension 5, and this entry's own
sibling entry in this same batch, View Helper, per the archived source's
own directly stated relationship. "a Composite View can fulfill the role
of View in View Helper" (Alur, Crupi, Malks, "Composite View," verified
2026-08-23).

## 14. Refactoring path in and out

The archived source names the concrete lever for adopting this pattern
directly, already quoted in dimension 5, extracting shared page fragments
into independently included atomic subviews, assembled through a template
that manages layout separately from each subview's own content. The
reverse lever, implied directly by the source's own named performance and
maintainability costs under dimension 4, 10, and 11, is inlining a
subview back into its one remaining caller once it is no longer genuinely
shared.

## 15. Testing and verification

This entry explicitly checked the fetched source for a documented test
methodology specific to this pattern and did not find one described as a
formal process on the archived page. the closest verifiable behavior is
the named access-control force under dimension 3, which a test would
exercise by confirming a subview subject to a role restriction is
correctly included or excluded from the assembled composite depending on
the requesting user's own role.

## 16. Observability signals

This entry explicitly checked the fetched source for a named metric or
dashboard specific to this pattern and did not find one described on the
archived page. the closest directly sourced signal is the named
performance cost under dimension 4, 10, and 11, which an operator could
instrument as a per-subview assembly time, to see which included
fragments actually dominate the composite's own total render cost.

## 17. Security and privacy implications

The archived source names role-based and policy-based access control
directly under dimension 3 and 10, "adds role-based or policy-based
control," naming a subview as the level at which such access control is
applied, so a subview carrying sensitive content is one that specifically
needs its own access check before being included in the assembled
composite.

## 18. References

1. Deepak Alur, John Crupi, Dan Malks, "Composite View," Core J2EE
   Patterns companion site, archived snapshot,
   https://web.archive.org/web/20211228031740/http://corej2eepatterns.com/CompositeView.htm,
   archived 28 December 2021, verified 2026-08-23. Excerpted from Core
   J2EE Patterns, 2nd Edition, Prentice Hall, 2003, ISBN 0-13-142246-4.

## Code

TypeScript, Python, and Go implementations of a minimal Composite View
following the mechanism from dimensions 5, 6, and 8, assembling a page
from independently named subviews at render time.

```typescript
type SubviewRenderer = () => string;

const NEWLINE = String.fromCharCode(10);

class CompositeView {
  private subviews: Map<string, SubviewRenderer> = new Map();

  addSubview(name: string, renderer: SubviewRenderer): void {
    this.subviews.set(name, renderer);
  }

  render(order: string[]): string {
    return order
      .map((name) => {
        const renderer = this.subviews.get(name);
        return renderer ? renderer() : "";
      })
      .join(NEWLINE);
  }
}
```

```python
from typing import Callable, Dict, List

SubviewRenderer = Callable[[], str]


class CompositeView:
    def __init__(self) -> None:
        self._subviews: Dict[str, SubviewRenderer] = {}

    def add_subview(self, name: str, renderer: SubviewRenderer) -> None:
        self._subviews[name] = renderer

    def render(self, order: List[str]) -> str:
        parts = []
        for name in order:
            renderer = self._subviews.get(name)
            parts.append(renderer() if renderer else "")
        return chr(10).join(parts)
```

```go
package compositeview

import "strings"

type SubviewRenderer func() string

var newline = string(rune(10))

type CompositeView struct {
	subviews map[string]SubviewRenderer
}

func NewCompositeView() *CompositeView {
	return &CompositeView{subviews: make(map[string]SubviewRenderer)}
}

func (c *CompositeView) AddSubview(name string, renderer SubviewRenderer) {
	c.subviews[name] = renderer
}

func (c *CompositeView) Render(order []string) string {
	parts := make([]string, 0, len(order))
	for _, name := range order {
		if renderer, ok := c.subviews[name]; ok {
			parts = append(parts, renderer())
		} else {
			parts = append(parts, "")
		}
	}
	return strings.Join(parts, newline)
}
```
