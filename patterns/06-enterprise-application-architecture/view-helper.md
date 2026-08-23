---
name: View Helper
slug: view-helper
family: 06-enterprise-application-architecture
category: Enterprise Application Architecture
aliases: [JavaBean Helper, Custom Tag Helper, Tag File Helper]
first_described: "Deepak Alur, John Crupi, Dan Malks, Core J2EE Patterns, 2nd Edition, Prentice Hall, 2003, ISBN 0-13-142246-4"
maturity: established
related: [composite-view, business-delegate]
incompatible_with: []
verified: 2026-08-23
---

# View Helper

## 1. Name, aliases, and lineage

A View Helper encapsulates view-processing logic, such as formatting or
adapting model data for display, so the view itself stays limited to
formatting markup and never carries embedded program logic of its own.

This entry sources it directly from the corejeepatterns.com companion
site to the book that named it, retrieved live from the Internet
Archive's Wayback Machine after the site's own live hosting stopped
resolving. "you want to separate a view from its processing logic" is the
pattern's own stated Problem, verbatim (Deepak Alur, John Crupi, Dan
Malks, "View Helper," Core J2EE Patterns companion site, archived
snapshot,
https://web.archive.org/web/20211230074425/http://corej2eepatterns.com/ViewHelper.htm,
archived 30 December 2021, verified 2026-08-23, excerpted from Core J2EE
Patterns, 2nd Edition, Prentice Hall, 2003).

## 2. Problem and context

A template-based view, such as a JSP page, is easy to fill with embedded
processing logic simply because the logic and the markup live in the same
file, and once that happens, the view can no longer be understood, tested,
or handed to a page designer without also touching the program logic
mixed into it.

## 3. Forces

The archived source names three forces directly, verbatim. "you want to
use template-based views, such as JSP," "you want to avoid embedding
program logic in the view," and "you want to separate programming logic
from the view to facilitate division of labor between software developers
and web page designers" (Alur, Crupi, Malks, "View Helper," verified
2026-08-23).

## 4. Applicability and non-applicability

The archived source names its own Consequences directly, quoted in full
under dimension 10, including "helper usage mirrors scriptlets" as a
directly named caveat, so a helper introduced carelessly can reproduce the
exact embedded-logic problem it was meant to solve, just moved one layer
away, rather than genuinely separating the view from its processing logic.

## 5. Structure

The archived source's own stated Solution names the structural shape
directly. "use Views to encapsulate formatting code and Helpers to
encapsulate view-processing logic. A View delegates its processing
responsibilities to its helper classes, implemented as POJOs, custom
tags, or tag files. Helpers serve as adapters between the view and the
model, and perform processing related to formatting logic, such as
generating an HTML table" (Alur, Crupi, Malks, "View Helper," verified
2026-08-23).

## 6. ASCII structure diagram

```
  +--------+     +-----------+     +----------+
  | model    | --> | Helper      | --> | View       |
  | data      |     | processing  |     | formatting  |
  |          |     | logic only  |     | markup only |
  +--------+     +-----------+     +----------+

  the view delegates its processing to the helper, per dimension 5
```

## 7. Dynamics

The archived source names the runtime relationship to this catalogue's
own already published Business Delegate entry directly, under its own
Related Patterns section. "a Business Delegate reduces the coupling
between a helper object and a remote business service, upon which the
helper object can invoke" (Alur, Crupi, Malks, "View Helper," Core J2EE
Patterns companion site, archived snapshot,
https://web.archive.org/web/20211230074425/http://corej2eepatterns.com/ViewHelper.htm,
verified 2026-08-23), so at render time a helper that itself needs data
from a remote business service reaches it through a Business Delegate
rather than calling that remote service directly.

## 8. Implementation variants

The archived source names six strategy variants directly. "Template-Based
View Strategy," "Controller-Based View Strategy," "JavaBean Helper
Strategy," "Custom Tag Helper Strategy," "Tag File Helper Strategy," and
"Business Delegate as Helper Strategy" (Alur, Crupi, Malks, "View
Helper," verified 2026-08-23), naming the last of the six directly as the
combination with this catalogue's own already published Business Delegate
entry.

## 9. Known production uses

The pattern is documented as one of the named presentation-tier patterns
listed in the same source's own site navigation, alongside Intercepting
Filter, Context Object, Front Controller, Application Controller, and
Composite View (Alur, Crupi, Malks, "View Helper," verified 2026-08-23),
the reference catalogue for the J2EE platform's own enterprise
application architecture, per dimension 1.

## 10. Consequences

The archived source names its own Consequences directly, verbatim, as a
list. "improves application partitioning, reuse, and maintainability,"
"improves role separation," "eases testing," and "helper usage mirrors
scriptlets" (Alur, Crupi, Malks, "View Helper," verified 2026-08-23),
naming both direct benefits and one directly named caveat, that a helper
used carelessly resembles the embedded-scriptlet problem it exists to
solve, in the same list.

## 11. Failure modes and misuse

The source's own named caveat under dimension 4 and 10, "helper usage
mirrors scriptlets," is the sharpest directly sourced failure mode, a
helper that grows to contain the same kind of ad hoc, view-specific logic
a scriptlet would have carried reproduces the original problem this
pattern exists to remove, just relocated into a differently named class.

## 12. Trade-off matrix

| Dimension | With a View Helper | Program logic embedded in the view |
|---|---|---|
| Testability of processing logic | Improved, dimension 10 | Hard, coupled to the view engine |
| Division of labor between roles | Enabled, dimension 3 and 10 | Blocked, one file mixes both |
| Risk of scriptlet-like sprawl | Named, dimension 4, 10, and 11 | The default failure mode itself |
| Access to a remote business service | Via Business Delegate, dimension 7 and 8 | Ad hoc, if attempted at all |

## 13. Related and incompatible patterns

This entry cross-references this catalogue's own already published
Business Delegate entry directly, per the archived source's own directly
stated strategy already quoted in full under dimension 7 and 8, and this
entry's own sibling entry in this same batch, Composite View, per the
archived source's own directly stated relationship. "a Composite View can
fulfill the role of View in View Helper" (Alur, Crupi, Malks, "View
Helper," verified 2026-08-23).

## 14. Refactoring path in and out

The archived source names the concrete lever for adopting this pattern
directly, already quoted in dimension 5, extracting view-processing logic
out of a template-based view into a POJO, custom tag, or tag file helper,
leaving the view itself with only formatting markup. The reverse lever,
implied directly by the source's own named caveat under dimension 4, 10,
and 11, is collapsing a helper that has grown scriptlet-like back down, or
splitting it, once its own logic stops being genuinely view-processing and
starts being business logic that belongs elsewhere.

## 15. Testing and verification

The archived source names the testability benefit directly under
dimension 10, "eases testing," which a test would exercise concretely by
invoking a helper's own processing method directly, with fixed model
input, and asserting its formatted output, with no template engine or
rendered page needed to exercise that logic at all.

## 16. Observability signals

This entry explicitly checked the fetched source for a named metric or
dashboard specific to this pattern and did not find one described on the
archived page. the closest directly sourced signal is the named caveat
under dimension 4, 10, and 11, which a reviewer could check for directly
in code review, whether a given helper's own logic is still limited to
view-processing and formatting, or has grown to include business rules
that belong somewhere else.

## 17. Security and privacy implications

This entry explicitly checked the fetched source for a security or
privacy discussion specific to this pattern and did not find one
addressed on the archived page. this entry reports that absence directly
rather than asserting a security property the source does not state.

## 18. References

1. Deepak Alur, John Crupi, Dan Malks, "View Helper," Core J2EE Patterns
   companion site, archived snapshot,
   https://web.archive.org/web/20211230074425/http://corej2eepatterns.com/ViewHelper.htm,
   archived 30 December 2021, verified 2026-08-23. Excerpted from Core
   J2EE Patterns, 2nd Edition, Prentice Hall, 2003, ISBN 0-13-142246-4.

## Code

TypeScript, Python, and Go implementations of a minimal View Helper
following the mechanism from dimensions 5 and 6, encapsulating
view-processing logic so the view itself only formats already-processed
data.

```typescript
interface Product {
  name: string;
  priceCents: number;
}

class ProductViewHelper {
  formatPrice(priceCents: number): string {
    return "$" + (priceCents / 100).toFixed(2);
  }

  toRow(product: Product): string {
    return product.name + " - " + this.formatPrice(product.priceCents);
  }
}
```

```python
from dataclasses import dataclass


@dataclass
class Product:
    name: str
    price_cents: int


class ProductViewHelper:
    def format_price(self, price_cents: int) -> str:
        return "$" + "{:.2f}".format(price_cents / 100)

    def to_row(self, product: Product) -> str:
        return product.name + " - " + self.format_price(product.price_cents)
```

```go
package viewhelper

import "strconv"

type Product struct {
	Name       string
	PriceCents int
}

type ProductViewHelper struct{}

func (h ProductViewHelper) FormatPrice(priceCents int) string {
	dollars := float64(priceCents) / 100
	return "$" + strconv.FormatFloat(dollars, 'f', 2, 64)
}

func (h ProductViewHelper) ToRow(product Product) string {
	return product.Name + " - " + h.FormatPrice(product.PriceCents)
}
```
