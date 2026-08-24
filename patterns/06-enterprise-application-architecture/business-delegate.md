---
name: Business Delegate
slug: business-delegate
family: 06-enterprise-application-architecture
category: Enterprise Application Architecture
aliases: [Delegate Proxy, Delegate Adapter]
first_described: "Deepak Alur, John Crupi, Dan Malks, Core J2EE Patterns, 2nd Edition, Prentice Hall, 2003, ISBN 0-13-142246-4"
maturity: established
related: [proxy, adapter, service-locator]
incompatible_with: []
verified: 2026-08-23
---

# Business Delegate

## 1. Name, aliases, and lineage

A Business Delegate hides a client from the complexity of remote
communication with a business-tier service, giving the client a local,
simple-looking object to call instead of a remote endpoint.

This entry sources it directly from the corejeepatterns.com companion
site to the book that named it, retrieved live from the Internet
Archive's Wayback Machine after the site's own live hosting stopped
resolving. "you want to hide clients from the complexity of remote
communication with business service components" is the pattern's own
stated Problem, verbatim (Deepak Alur, John Crupi, Dan Malks, "Business
Delegate," Core J2EE Patterns companion site, archived snapshot,
https://web.archive.org/web/20210423055822/http://www.corej2eepatterns.com/BusinessDelegate.htm,
archived 23 April 2021, verified 2026-08-23, excerpted from Core J2EE
Patterns, 2nd Edition, Prentice Hall, 2003).

## 2. Problem and context

A presentation-tier client, or another remote caller such as a device, a
web service, or a rich client, needs to reach a business-tier service,
and calling that remote service directly couples the client to lookup
mechanics, network exceptions, and retry logic that have nothing to do
with the client's own job.

## 3. Forces

The archived source names five forces directly, verbatim. "you want to
access the business-tier components from your presentation-tier
components and clients, such as devices, web services, and rich clients,"
"you want to minimize coupling between clients and the business services,
thus hiding the underlying implementation details of the service, such as
lookup and access," "you want to avoid unnecessary invocation of remote
services," "you want to translate network exceptions into application or
user exceptions," and "you want to hide the details of service creation,
reconfiguration, and invocation retries from the clients" (Alur, Crupi,
Malks, "Business Delegate," verified 2026-08-23).

## 4. Applicability and non-applicability

The source's own named Consequences, quoted in full under dimension 10,
include "introduces an additional layer" as a directly acknowledged cost,
so the pattern does not apply where a client already sits close to its
service with no remote boundary between them, an extra local indirection
layer with no remote call to hide behind it.

## 5. Structure

The source's own stated Solution names the structural shape directly.
"use a Business Delegate to encapsulate access to a business service. The
Business Delegate hides the implementation details of the business
service, such as lookup and access mechanisms" (Alur, Crupi, Malks,
"Business Delegate," verified 2026-08-23), and the same source names two
concrete structural strategies for that encapsulation, a "Delegate Proxy
Strategy" and a "Delegate Adapter Strategy."

## 6. ASCII structure diagram

```
+-------------------------------------------+
| Client                                    |
| presentation tier, device, or web service |
+-------------------------------------------+
     |
     v
+--------------------------------------------+
| Business Delegate                          |
| hides lookup, retry, exception translation |
+--------------------------------------------+
     |
     v
+----------------------------------------+
| Business-tier service, remote or local |
+----------------------------------------+

The client only ever calls the local-looking delegate,
per dimension 5.
```

## 7. Dynamics

The archived source names the runtime role of two related patterns
directly, under its own Related Patterns section. "the Business Delegate
typically uses a Service Locator to encapsulate the implementation
details of business service lookup. When the Business Delegate needs to
look up a business service, it delegates the lookup functionality to the
Service Locator" (Alur, Crupi, Malks, "Business Delegate," verified
2026-08-23), so at call time the delegate first resolves the real service
reference through a Service Locator before invoking it, rather than the
client ever doing that resolution itself.

## 8. Implementation variants

The archived source names its two strategies directly, already listed
under dimension 5, "Delegate Proxy Strategy" and "Delegate Adapter
Strategy," and names the GoF patterns each one builds on directly. "a
Business Delegate can act as a proxy, providing a stand-in for objects in
the business tier. The Delegate Proxy strategy provides this
functionality," and "a Business Delegate can use the Adapter design
pattern to provide integration for otherwise incompatible systems" (Alur,
Crupi, Malks, "Business Delegate," verified 2026-08-23), naming this
catalogue's own already published Proxy and Adapter entries directly as
the structural basis for each strategy.

## 9. Known production uses

The pattern is documented as one of the named business-tier patterns
listed in the same source's own site navigation, alongside Service
Locator, Session Facade, Application Service, Business Object, and
Composite Entity (Alur, Crupi, Malks, "Business Delegate," Core J2EE
Patterns companion site, archived snapshot,
https://web.archive.org/web/20210423055822/http://www.corej2eepatterns.com/BusinessDelegate.htm,
verified 2026-08-23), the reference catalogue for the J2EE platform's own
enterprise application architecture, per dimension 1.

## 10. Consequences

The archived source names its own Consequences directly, verbatim, as a
list. "reduces coupling, improves maintainability," "translates business
service exceptions," "improves availability," "exposes a simpler, uniform
interface to the business tier," "improves performance," "introduces an
additional layer," and "hides remoteness" (Alur, Crupi, Malks, "Business
Delegate," verified 2026-08-23), naming both the direct benefits and the
one named cost, the added layer, in the same list.

## 11. Failure modes and misuse

The source's own named cost under dimension 10, "introduces an additional
layer," is the sharpest directly sourced risk, an unnecessary Business
Delegate placed in front of a client that never actually needed the
lookup, exception-translation, or remoteness-hiding it exists to provide
adds indirection with no offsetting benefit.

## 12. Trade-off matrix

| Dimension | With a Business Delegate | Client calling the business service directly |
|---|---|---|
| Coupling to lookup and access mechanics | Hidden behind the delegate, dimension 3 and 5 | Directly exposed to the client |
| Network exception handling | Translated to application exceptions, dimension 3 and 10 | Raw network exceptions reach the client |
| Extra indirection layer | Yes, named cost, dimension 4, 10, and 11 | None |
| Availability under retries and reconfiguration | Improved, dimension 10 | Client bears retry logic itself |

## 13. Related and incompatible patterns

This entry cross-references this catalogue's own already published Proxy
and Adapter entries directly, per dimension 8, as the two GoF patterns the
source names its own Delegate Proxy and Delegate Adapter strategies on top
of, and this catalogue's own already published Service Locator entry, per
dimension 7, as the lookup mechanism a Business Delegate typically
delegates to.

## 14. Refactoring path in and out

The archived source names the concrete lever for adopting this pattern
directly, already quoted in dimension 5, wrapping a remote business
service behind a local-looking delegate that itself uses a Service
Locator for lookup. The reverse lever, implied directly by the source's
own named cost under dimension 10 and 11, is collapsing the delegate back
into a direct call once the remote boundary, or the reason to hide it, no
longer exists.

## 15. Testing and verification

This entry explicitly checked the fetched source for a documented test
methodology specific to this pattern and did not find one described as a
formal process on the archived page. the closest verifiable behavior is
the named exception-translation consequence under dimension 10, which a
test would exercise by confirming a network-level failure from the
underlying business service surfaces to the client as the delegate's own
translated application exception, not the raw network exception.

## 16. Observability signals

This entry explicitly checked the fetched source for a named metric or
dashboard specific to this pattern and did not find one described on the
archived page. the closest directly sourced signal is the named retry and
reconfiguration hiding under dimension 3, which an operator would need to
instrument separately, since the delegate's own stated purpose is to keep
those details invisible to the client.

## 17. Security and privacy implications

This entry explicitly checked the fetched source for a security or
privacy discussion specific to this pattern and did not find one addressed
on the archived page. this entry reports that absence directly rather
than asserting a security property the source does not state.

## 18. References

1. Deepak Alur, John Crupi, Dan Malks, "Business Delegate," Core J2EE
   Patterns companion site, archived snapshot,
   https://web.archive.org/web/20210423055822/http://www.corej2eepatterns.com/BusinessDelegate.htm,
   archived 23 April 2021, verified 2026-08-23. Excerpted from Core J2EE
   Patterns, 2nd Edition, Prentice Hall, 2003, ISBN 0-13-142246-4.

## Code

TypeScript, Python, and Go implementations of a minimal Business Delegate
following the mechanism from dimensions 5 and 7, hiding lookup and
exception translation behind a local-looking call.

```typescript
interface BusinessService {
  process(input: string): string;
}

class ServiceLocator {
  private cache: Map<string, BusinessService> = new Map();

  lookup(name: string, factory: () => BusinessService): BusinessService {
    let service = this.cache.get(name);
    if (!service) {
      service = factory();
      this.cache.set(name, service);
    }
    return service;
  }
}

class BusinessDelegate {
  constructor(
    private locator: ServiceLocator,
    private serviceName: string,
    private factory: () => BusinessService,
  ) {}

  process(input: string): string {
    try {
      const service = this.locator.lookup(this.serviceName, this.factory);
      return service.process(input);
    } catch (err) {
      throw new Error("business service unavailable: " + (err as Error).message);
    }
  }
}
```

```python
from typing import Callable, Dict, Protocol


class BusinessService(Protocol):
    def process(self, input_value: str) -> str: ...


class ServiceLocator:
    def __init__(self) -> None:
        self._cache: Dict[str, BusinessService] = {}

    def lookup(self, name: str, factory: Callable[[], BusinessService]) -> BusinessService:
        if name not in self._cache:
            self._cache[name] = factory()
        return self._cache[name]


class BusinessDelegate:
    def __init__(self, locator: ServiceLocator, service_name: str, factory: Callable[[], BusinessService]) -> None:
        self._locator = locator
        self._service_name = service_name
        self._factory = factory

    def process(self, input_value: str) -> str:
        try:
            service = self._locator.lookup(self._service_name, self._factory)
            return service.process(input_value)
        except Exception as err:
            raise RuntimeError("business service unavailable: " + str(err)) from err
```

```go
package businessdelegate

import "fmt"

type BusinessService interface {
	Process(input string) (string, error)
}

type ServiceFactory func() BusinessService

type ServiceLocator struct {
	cache map[string]BusinessService
}

func NewServiceLocator() *ServiceLocator {
	return &ServiceLocator{cache: make(map[string]BusinessService)}
}

func (l *ServiceLocator) Lookup(name string, factory ServiceFactory) BusinessService {
	if service, ok := l.cache[name]; ok {
		return service
	}
	service := factory()
	l.cache[name] = service
	return service
}

type BusinessDelegate struct {
	locator     *ServiceLocator
	serviceName string
	factory     ServiceFactory
}

func NewBusinessDelegate(locator *ServiceLocator, serviceName string, factory ServiceFactory) *BusinessDelegate {
	return &BusinessDelegate{locator: locator, serviceName: serviceName, factory: factory}
}

func (d *BusinessDelegate) Process(input string) (string, error) {
	service := d.locator.Lookup(d.serviceName, d.factory)
	result, err := service.Process(input)
	if err != nil {
		return "", fmt.Errorf("business service unavailable: %w", err)
	}
	return result, nil
}
```
