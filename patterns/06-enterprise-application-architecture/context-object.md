---
name: Context Object
slug: context-object
family: 06-enterprise-application-architecture
category: Enterprise Application Architecture
aliases: [Request Context, Configuration Context]
first_described: "Deepak Alur, John Crupi, Dan Malks, Core J2EE Patterns, 2nd Edition, Prentice Hall, 2003, ISBN 0-13-142246-4"
maturity: established
related: [front-controller, application-controller, data-transfer-object]
incompatible_with: []
verified: 2026-08-23
---

# Context Object

## 1. Name, aliases, and lineage

A Context Object carries protocol-independent state through an
application so components and services never have to reach directly into
a protocol-specific object, such as an HTTP request, to read the
information they need.

This entry sources it directly from the corejeepatterns.com companion
site to the book that named it, retrieved live from the Internet
Archive's Wayback Machine after the site's own live hosting stopped
resolving. "you want to avoid using protocol-specific system information
outside of its relevant context" is the pattern's own stated Problem,
verbatim (Deepak Alur, John Crupi, Dan Malks, "Context Object," Core J2EE
Patterns companion site, archived snapshot,
https://web.archive.org/web/20211225105002/http://corej2eepatterns.com/ContextObject.htm,
archived 25 December 2021, verified 2026-08-23, excerpted from Core J2EE
Patterns, 2nd Edition, Prentice Hall, 2003).

## 2. Problem and context

A component or a service somewhere in an application needs access to
system information, such as request parameters or configuration values,
that originates from a specific protocol, and reaching into that
protocol's own object directly from deep inside application logic ties
the logic to that protocol's shape.

## 3. Forces

The archived source names three forces directly, verbatim. "you have
components and services that need access to system information," "you
want to decouple application components and services from the protocol
specifics of system information," and "you want to expose only the
relevant APIs within a context" (Alur, Crupi, Malks, "Context Object,"
verified 2026-08-23).

## 4. Applicability and non-applicability

The archived source names its own Consequences directly, quoted in full
under dimension 10, including "reduces performance" as a stated cost, so
the pattern does not apply where the protocol-specific object is already
narrowly scoped and cheaply passed, and where the extra indirection of
wrapping it would only add overhead with no decoupling benefit to show
for it.

## 5. Structure

The archived source's own stated Solution names the structural shape
directly. "use a Context Object to encapsulate state in a
protocol-independent way to be shared throughout your application" (Alur,
Crupi, Malks, "Context Object," verified 2026-08-23), and the same source
names three families of concrete strategies for that encapsulation
directly, "Request Context Strategies," "Configuration Context
Strategies," and "General Context Object Strategies."

## 6. ASCII structure diagram

```
+---------------------------------------------+
| protocol-specific object, e.g. HTTP request |
+---------------------------------------------+
           v
+----------------------------+
| Context Object             |
| protocol-independent state |
+----------------------------+
           v
+-------------------------------------+
| application components and services |
+-------------------------------------+

A component only ever reads from the context object,
never the protocol-specific object directly, per
dimension 5.
```

## 7. Dynamics

The archived source names the runtime relationship to two named
front-of-request patterns directly, under its own Related Patterns
section. "a Front Controller can use a ContextFactory to create a Context
Object during web request handling" and "an Application Controller can
use a ContextFactory to create a Context Object during web request
handling" (Alur, Crupi, Malks, "Context Object," verified 2026-08-23), so
the context object is typically constructed once, early in a request's
handling, by a factory, then read by whatever components downstream need
the state it carries.

## 8. Implementation variants

The archived source names three distinct strategy families directly,
already listed under dimension 5. "Request Context Strategies" (naming
"Request Context Map Strategy," "Request Context POJO Strategy," and
"Request Context Validation Strategy" as its own sub-variants),
"Configuration Context Strategies" (naming "JSTL Configuration Strategy"
and "Security Context Strategy"), and "General Context Object Strategies"
(naming "Context Object Factory Strategy" and "Context Object
Auto-Population Strategy") (Alur, Crupi, Malks, "Context Object," verified
2026-08-23).

## 9. Known production uses

The pattern is documented as one of the named presentation-tier
patterns listed in the same source's own site navigation, alongside
Intercepting Filter, Front Controller, Application Controller, View
Helper, and Composite View (Alur, Crupi, Malks, "Context Object," Core
J2EE Patterns companion site, archived snapshot,
https://web.archive.org/web/20211225105002/http://corej2eepatterns.com/ContextObject.htm,
verified 2026-08-23), the reference catalogue for the J2EE platform's own
enterprise application architecture, per dimension 1.

## 10. Consequences

The archived source names its own Consequences directly, verbatim, as a
list. "improves reusability and maintainability," "improves testability,"
"reduces constraints on evolution of interfaces," and "reduces
performance" (Alur, Crupi, Malks, "Context Object," verified 2026-08-23),
naming both the direct benefits and the one named cost, reduced
performance, in the same list.

## 11. Failure modes and misuse

The source's own directly named distinction from a sibling pattern,
already quoted in dimension 13, is the sharpest boundary this entry found.
using a Context Object where a Transfer Object is actually needed, or the
reverse, misapplies the wrong one of the two, since the archived source
states they solve different problems, hiding implementation details
versus carrying state across remote tiers.

## 12. Trade-off matrix

| Dimension | With a Context Object | Reading the protocol-specific object directly |
|---|---|---|
| Coupling to the originating protocol | Decoupled, dimension 3 and 5 | Tightly coupled |
| Testability | Improved, dimension 10 | Harder, needs the real protocol object |
| Performance overhead | A named cost, dimension 4, 10, and 11 | None, direct access |
| API surface exposed to a component | Only the relevant APIs, dimension 3 | The full protocol object's surface |

## 13. Related and incompatible patterns

This entry cross-references this catalogue's own already published Front
Controller and Application Controller entries directly, per dimension 7,
as the two patterns the archived source names as typical creators of a
Context Object via a factory during request handling, and this
catalogue's own already published Data Transfer Object entry, per the
archived source's own directly stated distinction. "a Transfer Object is
used specifically to transfer state across remote tiers to reduce network
communication, while a Context Object is used to hide implementation
details, improving reuse and maintainability" (Alur, Crupi, Malks,
"Context Object," verified 2026-08-23).

## 14. Refactoring path in and out

The archived source names the concrete lever for adopting this pattern
directly, already quoted in dimension 5 and 7, introducing a
ContextFactory that builds a protocol-independent Context Object early in
request handling, and having downstream components read from that object
instead of the original protocol-specific one. The reverse lever, implied
directly by the source's own named performance cost under dimension 4, 10,
and 11, is collapsing the context object back to direct protocol access
once the decoupling it provides is no longer needed.

## 15. Testing and verification

The archived source names the testability benefit directly under
dimension 10, "improves testability," which a test would exercise
concretely by constructing a Context Object with fixed, protocol-free test
values and passing it to a component under test, rather than needing to
stand up a real protocol-specific request object just to exercise that
component's logic.

## 16. Observability signals

This entry explicitly checked the fetched source for a named metric or
dashboard specific to this pattern and did not find one described on the
archived page. the closest directly sourced signal is the named
"Request Context Validation Strategy" under dimension 8, which implies
the context object's own construction is a point where invalid or missing
system information could be caught and surfaced, rather than only failing
later inside a downstream component.

## 17. Security and privacy implications

The archived source names a "Security Context Strategy" directly under
its own Configuration Context Strategies, per dimension 8, naming security
information as one of the concrete kinds of state a Context Object is
meant to carry in a protocol-independent way, though the fetched page
does not itself elaborate on what that strategy protects against.

## 18. References

1. Deepak Alur, John Crupi, Dan Malks, "Context Object," Core J2EE
   Patterns companion site, archived snapshot,
   https://web.archive.org/web/20211225105002/http://corej2eepatterns.com/ContextObject.htm,
   archived 25 December 2021, verified 2026-08-23. Excerpted from Core
   J2EE Patterns, 2nd Edition, Prentice Hall, 2003, ISBN 0-13-142246-4.

## Code

TypeScript, Python, and Go implementations of a minimal Context Object
following the mechanism from dimensions 5 and 7, built once by a factory
from a protocol-specific source and read from thereafter by application
components with no knowledge of that source.

```typescript
interface RequestLike {
  headers: Record<string, string>;
  params: Record<string, string>;
}

class RequestContext {
  private constructor(
    private readonly userId: string | null,
    private readonly locale: string,
  ) {}

  static from(request: RequestLike): RequestContext {
    return new RequestContext(
      request.headers["x-user-id"] ?? null,
      request.params["locale"] ?? "en",
    );
  }

  getUserId(): string | null {
    return this.userId;
  }

  getLocale(): string {
    return this.locale;
  }
}
```

```python
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class RequestContext:
    user_id: Optional[str]
    locale: str

    @staticmethod
    def from_request(headers: Dict[str, str], params: Dict[str, str]) -> "RequestContext":
        return RequestContext(
            user_id=headers.get("x-user-id"),
            locale=params.get("locale", "en"),
        )
```

```go
package contextobject

type RequestContext struct {
	UserID string
	Locale string
}

func NewRequestContext(headers map[string]string, params map[string]string) RequestContext {
	locale := params["locale"]
	if locale == "" {
		locale = "en"
	}
	return RequestContext{
		UserID: headers["x-user-id"],
		Locale: locale,
	}
}
```
