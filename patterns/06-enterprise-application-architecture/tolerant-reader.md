---
name: Tolerant Reader
slug: tolerant-reader
family: 06-enterprise-application-architecture
category: Enterprise Application Architecture
aliases: [Robustness Principle for Services, Postel's Law for Interfaces]
first_described: "Martin Fowler's own bliki article"
maturity: established
related: [consumer-driven-contract-test]
incompatible_with: []
verified: 2026-08-23
---

# Tolerant Reader

## 1. Name, aliases, and lineage

A Tolerant Reader is a service consumer that extracts only the specific
elements it needs from a response and ignores everything else, so a
provider can add or reorder fields without breaking every client that
happens to be listening.

This entry sources it directly from Martin Fowler's own bliki, fetched
live. "when you consume a service you should code your consumption to be
as tolerant as possible of the response, minimizing dependencies to other
parts of the response" (Martin Fowler, "Tolerant Reader," martinfowler.com
bliki, https://martinfowler.com/bliki/TolerantReader.html, verified
2026-08-23). the article names Postel's Law directly as the principle it
applies to service consumption. "be conservative in what you do, be
liberal in what you accept from others" (same source), and names Rob
Daigneau's own book as the fuller treatment of the same pattern.

## 2. Problem and context

Fowler's own text states the underlying problem directly. "one of the
truisms of service oriented systems is that you have separate services
that need to talk to each other, and that these services are usually built
and maintained by separate teams... a common form of coupling in this
environment is when a consumer of a service breaks because the provider
changes the format of the messages it sends" (Fowler, "Tolerant Reader,"
verified 2026-08-23), even when the change genuinely adds no meaning the
consumer relies on, an added field, a reordered element, a new optional
attribute.

## 3. Forces

Fowler's own text names the direct tension the pattern resolves, between
strict, schema-generated consumption code and a consumer's actual need.
"If you're consuming an XML file, then only take the elements you need,
ignore anything you don't" (same source), rather than binding to the whole
shape of the message. the XPath example makes the same trade concrete.
"rather than use an XPath search like `/order-history/order-list/order`
use `//order`" (same source), trading strict positional precision for
resilience to structural change.

## 4. Applicability and non-applicability

This entry explicitly checked the fetched source for a stated exception,
a case where a consumer should NOT be a tolerant reader, security,
financial precision, or a similarly strict domain, and did not find one.
the article focuses entirely on evolutionary service design and consumer
decoupling, and this entry reports that absence directly rather than
inferring a boundary the source does not state.

## 5. Structure

Fowler's own text describes the consumer-side shape directly. "wrap the
reading of your input payload into a single class... using a single class
to handle this parsing means that if there are problems, you only need to
change the code in one place" (Fowler, "Tolerant Reader," verified
2026-08-23), the pattern's own Data Transfer Object boundary. for a
non-XML, binary-serialized payload, the same shape carries over. "instead
of using strongly typed objects for the elements of the message, you can
use a generic map or list structure" (same source).

## 6. ASCII structure diagram

```
  provider response, evolving over time:

  version 1               version 2 (field added, harmless)
  +----------------+       +----------------------+
  | order-id       |       | order-id             |
  | customer-name  |       | customer-name         |
  +----------------+       | shipping-preference   | <- new
                            +----------------------+

  a strict, schema-bound consumer breaks on version 2.

  a tolerant reader:

  +-----------------------------------+
  | single parsing class (DTO layer)  |
  |   extracts ONLY order-id,         |
  |   customer-name                   |
  |   ignores anything else present   |
  +-----------------------------------+
              |
              v
       consumer's own logic, unaffected by the new field
```

## 7. Dynamics

Fowler's own text describes the provider-side companion practice directly,
naming a bridge to a different, already-published pattern in this
catalogue. "one way to combat this is to share your consumer's tests
with the provider... this is the essence of consumer-driven contracts"
(Fowler, "Tolerant Reader," verified 2026-08-23), so the provider runs the
real consumer's tests as part of its own build and catches an accidental
breaking change before it ships, rather than after.

## 8. Implementation variants

Fowler's own text names a related, complementary pattern on the provider
side, attributed to a named author. "Saleem Siddiqui describes how a
Tolerant Reader works well with a Magnanimous Writer" (Fowler, "Tolerant
Reader," verified 2026-08-23), a provider-side discipline for how a
service writes its own responses so a tolerant consumer has an easier job.
this entry did not find a separately citable, independent primary source
for the Magnanimous Writer half beyond this one mention, and reports that
directly rather than inventing one.

## 9. Known production uses

This entry explicitly checked the fetched source for a named, production
deployment of this pattern and did not find one. the article frames the
pattern as a general service-consumption discipline rather than naming a
specific company or system that adopted it, and this entry reports that
absence directly rather than inventing a case study the source does not
supply.

## 10. Consequences

The benefit is stated directly, already quoted in dimension 3, a consumer
that survives a provider's additive change without a deploy of its own.
the cost is a direct trade against interface precision. a tolerant reader
cannot detect a MEANINGFUL change to a field it does not read, since it
never looks at that field at all, so a genuinely breaking change to an
unread field passes silently rather than failing loudly.

## 11. Failure modes and misuse

This entry explicitly checked the fetched source for a named failure mode
or misuse case and did not find one described directly. the structural
trade named in dimension 10, silence on a change to an unread field, is
this entry's own reasoned extension of the pattern's own mechanism rather
than a failure mode the source itself names, and this entry reports that
distinction directly.

## 12. Trade-off matrix

| Dimension | Tolerant Reader | Strict schema-bound consumer |
|---|---|---|
| Survives an additive provider change | Yes, dimension 3 | No, typically breaks |
| Detects a meaningful change to an unread field | No, silent, dimension 10 | Yes, fails loudly |
| Coupling to provider's exact shape | Low, dimension 5 | High |
| Provider-side safety net available | Consumer-driven contracts, dimension 7 | Not specific to this pattern |
| Code shape | Single parsing class, dimension 5 | Often schema-generated types |

## 13. Related and incompatible patterns

Fowler's own text draws the direct bridge to consumer-driven contracts,
already quoted in dimension 7, which is a separate, already-published
entry in this same catalogue. this entry explicitly checked whether the
fetched source compares Tolerant Reader to a general defensive-programming
concept by name and confirmed it does not, framing it specifically as a
service-interface consumption discipline, and reports that distinction
directly rather than asserting a broader bridge the source does not draw.

## 14. Refactoring path in and out

This entry explicitly checked the fetched source for a documented
migration path from a strict, schema-bound consumer to a tolerant one, or
an explicit way to revert, and did not find either described as a staged
process. the article names the mechanism, wrap parsing in a single class
and extract only needed elements, per dimension 5, rather than a phased
adoption plan, and this entry reports that directly.

## 15. Testing and verification

Fowler's own text names the verification method directly, already quoted
in dimension 7, the consumer's own tests shared with and run by the
provider's build, which is the consumer-driven-contract-test mechanism
this catalogue already publishes as its own entry.

## 16. Observability signals

This entry explicitly checked the fetched source for a named metric or
observability signal specific to this pattern and did not find one. this
entry reports that absence directly rather than inventing an
observability surface the source does not describe.

## 17. Security and privacy implications

This entry explicitly checked the fetched source for a security or privacy
discussion and did not find one. the article's own scope is service
interface evolution, not the security posture of what a consumer reads,
and this entry reports that absence directly rather than asserting a
security property the source does not state.

## 18. References

1. Martin Fowler, "Tolerant Reader," martinfowler.com bliki,
   https://martinfowler.com/bliki/TolerantReader.html, verified
   2026-08-23.
2. IETF, "Requirements for Internet Hosts, Communication Layers," RFC
   1122, https://www.rfc-editor.org/rfc/rfc1122, verified 2026-08-23.
3. Wikipedia, "Robustness principle,"
   https://en.wikipedia.org/wiki/Robustness_principle, verified
   2026-08-23.

## Code

TypeScript, Python, and Go implementations of a tolerant reader following
the mechanism from dimensions 5 and 6, extracting only named fields from
an arbitrary, larger response object and ignoring everything else present.

```typescript
interface OrderSummary {
  orderId: string;
  customerName: string;
}

function readOrder(raw: Record<string, unknown>): OrderSummary {
  return {
    orderId: String(raw["order-id"]),
    customerName: String(raw["customer-name"]),
  };
}
```

```python
from typing import Any, Dict


class OrderSummary:
    def __init__(self, order_id: str, customer_name: str) -> None:
        self.order_id = order_id
        self.customer_name = customer_name


def read_order(raw: Dict[str, Any]) -> OrderSummary:
    return OrderSummary(
        order_id=str(raw["order-id"]),
        customer_name=str(raw["customer-name"]),
    )
```

```go
package tolerantreader

import "fmt"

type OrderSummary struct {
	OrderID      string
	CustomerName string
}

func ReadOrder(raw map[string]interface{}) OrderSummary {
	return OrderSummary{
		OrderID:      fmt.Sprintf("%v", raw["order-id"]),
		CustomerName: fmt.Sprintf("%v", raw["customer-name"]),
	}
}
```
