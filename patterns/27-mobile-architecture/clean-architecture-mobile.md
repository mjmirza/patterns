---
name: Clean Architecture (Mobile)
slug: clean-architecture-mobile
family: 27-mobile-architecture
category: Structural
aliases: [Onion Architecture (Mobile), Domain-Centric Architecture, Layered Clean Architecture]
first_described: 'Robert C. Martin, The Clean Architecture, 2012'
maturity: canonical
related: [repository-pattern, mvvm-c]
incompatible_with: []
verified: 2026-08-22
---

# Clean Architecture (Mobile)

## 1. Name, aliases, and lineage

Clean Architecture, applied to mobile apps. Also called Onion Architecture (Mobile), Domain-Centric Architecture, or Layered Clean Architecture. The name comes directly from Robert C. Martin, whose 2012 post described a set of concentric layers with one governing rule. Source code dependencies can only point inwards. Nothing in an inner circle can know anything at all about something in an outer circle (https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html).

On mobile, the pattern arrived as teams outgrew MVC and MVP architectures whose business logic was entangled with Activities, Fragments, and UI framework classes that were slow or impossible to unit test. Android's own official architecture guidance later adopted the same idea as an optional domain layer sitting between the UI and data layers, giving Google's blessing to Uncle Bob's original concept inside the standard Android app architecture.

## 2. Problem and context

Business logic that lives directly inside a ViewController, an Activity, or a ViewModel is coupled to the UI framework whether or not it needs to be. A pricing calculation, a validation rule, or an eligibility check that only manipulates plain data ends up importing UI lifecycle types, framework annotations, or platform-specific classes it has no real dependency on. That coupling makes the logic slow to unit test (it needs a framework-attached test rig instead of a plain unit test), hard to reuse (a rule written for the phone UI cannot be reused for a widget, a watch companion, or a backend job without a rewrite), and fragile against UI or platform changes that have nothing to do with the business rule itself.

Google's own domain-layer guidance frames the layer's purpose directly. The domain layer is responsible for encapsulating complex business logic, or simple business logic that is reused by multiple ViewModels (https://developer.android.com/topic/architecture/domain-layer). The problem Clean Architecture solves is making that encapsulation structural rather than a matter of discipline alone. the dependency direction itself prevents business logic from ever importing a UI or framework type in the first place.

## 3. Forces

- Business logic needs to be unit-testable without booting a UI framework, an emulator, or a device.
- The same business rule frequently needs to run in more than one context. the phone UI, a widget, a background job, a watch companion, or a server-side equivalent.
- UI frameworks and platform APIs change far more often than the core business rules they display, so coupling the two ties stable logic to an unstable dependency.
- Strict layering adds real indirection. every operation crosses at least one interface boundary, which is friction a small app may not need.
- The data layer's storage and network details (a specific database, a specific HTTP client) should be swappable without the domain layer noticing, which requires the domain layer to depend on an abstraction, not a concrete implementation.

## 4. Applicability and non-applicability

Use Clean Architecture for an app whose business logic is genuinely complex enough to be worth isolating, is reused across more than one presentation surface, or is expected to survive multiple UI framework rewrites over the app's lifetime (a common reality for long-lived enterprise or financial apps). It is also a strong fit whenever a team wants business logic covered by fast, plain unit tests with no framework dependency at all.

Skip it for a small app, a prototype, or a screen whose logic is genuinely trivial UI glue with no real business rule to isolate. Forcing three strict layers and interface boundaries onto a five-screen app with no meaningfully reusable logic is over-engineering, and the domain layer itself is explicitly optional in Google's own guidance for exactly this reason.

## 5. Structure

- Domain layer (the innermost circle). plain business rules and use cases, with zero dependency on any UI framework, database library, or networking client. Depends on nothing but its own abstractions.
- Repository interfaces. abstractions the domain layer depends on to read and write data, defined IN the domain layer but IMPLEMENTED in the data layer, so the dependency still points inward.
- Data layer. concrete repository implementations, database access, and network clients, which depend on the domain layer's interfaces rather than the reverse.
- Presentation layer (the outermost circle). ViewModels, Activities, Fragments, or composables that depend on the domain layer's use cases and render their output, never the reverse.
- Dependency injection boundary. the mechanism (manual factories or a DI framework) that wires concrete data-layer implementations into the domain layer's interfaces at app startup, keeping the domain layer itself free of any knowledge of which concrete implementation it received.

## 6. ASCII structure diagram

```
        +------------------------------------------+
        |          Presentation layer               |
        |   ViewModel, Activity, Composable          |
        |   +------------------------------------+  |
        |   |            Domain layer            |  |
        |   |   Use cases, business rules         |  |
        |   |   (depends on nothing outward)      |  |
        |   +------------------------------------+  |
        |          ^  depends on   ^                |
        +----------|---------------|----------------+
                   |               |
        +----------+               +----------------+
        |                                           |
  +-----------+                              +-----------+
  | Data layer|  implements domain interfaces | Data layer|
  | (network) |                                | (local)  |
  +-----------+                                +-----------+

  arrows point INWARD, toward the domain layer, always
```

## 7. Dynamics

1. The presentation layer (a ViewModel) receives a person's action and calls a use case exposed by the domain layer, passing plain data, never a UI or framework type.
2. The use case executes the business rule, calling one or more repository interfaces it depends on when it needs data, without knowing or caring whether the concrete implementation is a network call, a local database read, or a cache.
3. The concrete repository, living in the data layer, fulfills the request using whatever storage or network mechanism it wraps, and returns plain domain-layer data types back through the interface.
4. The use case applies the actual business logic to that data and returns a result to the ViewModel, still as plain data with no UI framework dependency.
5. The ViewModel maps that result into UI state and the presentation layer renders it, completing the round trip without the domain layer ever having imported a single UI or platform type.
6. Google's own domain-layer guidance notes an additional discipline this flow must respect. use cases don't have their own lifecycle, instead, they're scoped to the class that uses them (https://developer.android.com/topic/architecture/domain-layer), and must be main-safe, meaning safe to call directly from the calling ViewModel's own coroutine scope without the caller needing to manage threading itself.

## 8. Implementation variants

- Strict three-layer. domain, data, and presentation as three distinct modules or packages, each depending only inward, enforced at the module boundary so a build-time dependency violation is a compile error rather than an unenforced convention.
- Google's official domain-layer flavor. the domain layer is explicitly optional and introduced only where business logic is complex or reused across multiple ViewModels, rather than mandated for every feature regardless of complexity.
- Feature-scoped Clean Architecture. each feature module carries its own internal domain, data, and presentation layering, which composes naturally with a modularized, multi-feature-module app.
- Package-by-layer versus package-by-feature. the same three-layer dependency direction can be organized as three top-level packages (domain, data, presentation) or repeated inside each feature package, trading global layer visibility against feature-local cohesion.

## 9. Known production uses

- Uncle Bob's original formulation, names of something declared in an outer circle must not be mentioned by the code in an inner circle (https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html), underlies Clean Architecture implementations across Android, iOS, and backend codebases well beyond mobile.
- Android's own official architecture guidance documents an optional domain layer sitting between the UI and data layers (https://developer.android.com/topic/architecture/domain-layer), making the pattern a first-class, Google-endorsed option for any Android app built on the recommended architecture.
- Large, long-lived enterprise and financial mobile apps commonly adopt this pattern specifically because their business rules (pricing, eligibility, compliance checks) must survive multiple UI framework rewrites over the app's lifetime without themselves being rewritten.

## 10. Consequences

### Benefits

- Business logic is testable with fast, plain unit tests, with no UI framework, emulator, or device required.
- The same use case can be reused across the phone UI, a widget, a watch companion, or a background job without any rewrite.
- UI framework and platform changes stay isolated to the outer layers. the domain layer does not need to change when the UI toolkit does.
- Storage and network implementation details can be swapped (a new database, a new HTTP client) without touching the business rules that depend only on an interface.

### Costs

- Every operation crosses at least one interface boundary, which is real indirection and boilerplate a small app does not need.
- Enforcing the dependency direction without module-level build enforcement relies on convention, and a rushed change can quietly violate the inward-only rule.
- The extra layers and mapping between layer-specific data types add a real learning curve for a team new to the pattern.

## 11. Failure modes and misuse

- Leaky abstraction. a repository interface defined in the domain layer that exposes a data-layer-specific type (a database row, an HTTP response model) instead of a plain domain type, defeating the whole point of the boundary.
- Anemic use cases. a use case that does nothing but forward a call to a repository with no actual business rule applied, adding indirection with no real benefit.
- Framework leakage. a UI framework annotation or lifecycle type quietly imported into the domain layer because it was the path of least resistance under a deadline, silently breaking the dependency rule.
- Over-layering a trivial feature. applying the full three-layer structure to a screen with no real business logic to isolate, producing ceremony with no corresponding benefit.
- God use case. a single use case that accumulates unrelated responsibilities over time instead of being split, becoming its own tangled dependency for every ViewModel that calls it.

## 12. Trade-off matrix

| Dimension | Strict three-layer Clean Architecture | MVVM with no domain layer |
|---|---|---|
| Testability of business logic | High, plain unit tests, no framework needed | Lower, logic often entangled with the ViewModel |
| Reuse across surfaces | High, use cases callable from any presentation layer | Low, logic tied to one ViewModel |
| Indirection and boilerplate | Higher, every call crosses an interface | Lower, direct calls from ViewModel to repository |
| Fit for a small or simple app | Often excessive | A natural, lighter default |
| Resilience to UI framework rewrites | High, domain layer untouched | Lower, logic often needs to move with the UI |

## 13. Related and incompatible patterns

### Related

- Repository Pattern (Mobile Offline-First). the repository interfaces Clean Architecture's domain layer depends on are exactly the abstraction the Repository Pattern defines, implemented concretely in the data layer.
- MVVM-C (Model-View-ViewModel-Coordinator). the presentation layer in Clean Architecture is commonly structured internally as MVVM, with the ViewModel calling into the domain layer's use cases rather than a data layer directly.

### Incompatible with

- None directly, though a genuinely trivial app with no reusable or complex business logic gains little from the pattern and is better served by a simpler MVVM structure with no separate domain layer.

## 14. Refactoring path in and out

### Introducing it

1. Identify the business logic currently entangled with ViewModels or UI controllers that is complex enough, or reused enough, to be worth extracting.
2. Extract that logic into plain use case classes with no UI or framework import, taking and returning only plain domain data types.
3. Define repository interfaces in the domain layer for whatever data access the extracted use cases need, rather than letting them call a concrete data source directly.
4. Implement those interfaces concretely in the data layer, wiring the concrete implementation into the domain layer's interface through dependency injection.
5. Update the presentation layer to call the new use cases instead of reaching into a repository or data source directly, migrating one feature at a time.

### Removing it

1. Confirm the business logic genuinely no longer needs isolation, reuse across surfaces, or independent testability, which is uncommon once a domain layer is established.
2. Inline the use case's logic back into the calling ViewModel or controller, one use case at a time.
3. Remove the now-unused repository interface and its indirection once nothing depends on it, keeping the concrete data-layer implementation if it is still needed directly.

## 15. Testing and verification

- Unit-test every use case in complete isolation, with a fake or mock implementation of its repository interfaces, asserting the business rule's output for both the expected and the edge-case inputs.
- Assert the domain layer has zero import of any UI framework or platform-specific type, either by convention review or by enforcing it at the module or package boundary so a violation is a build failure.
- Test the concrete data-layer repository implementations against their interface contract, so swapping the implementation later cannot silently break a guarantee the domain layer relies on.
- Test ViewModels with a fake use case rather than a fake repository, verifying the presentation layer only ever depends on the domain layer's public interface.
- Verify main-safety for every use case explicitly, since Google's own guidance requires them to be safe to call from the main thread without the caller managing threading.

## 16. Observability signals

- Track which use cases are actually reused across more than one presentation surface, since a domain layer with no genuine reuse is a signal the pattern may be more ceremony than benefit for that codebase.
- Track unit test execution time for the domain layer specifically. it should stay in the range of plain, framework-free unit tests. a domain-layer test suite that grows slow usually means a framework dependency leaked in.
- Track dependency-direction violations if the codebase has static analysis or module-boundary enforcement in place, since a rising count signals the layering is eroding under delivery pressure.

## 17. Security and privacy implications

- Centralizing business rules in the domain layer is also the natural place to centralize authorization and validation logic, so a permission check written once in a use case is not silently skipped by a presentation layer that calls a data source directly instead.
- Because the domain layer has no UI dependency, it is easy to unit-test security-sensitive rules (an eligibility check, a permission gate) directly and exhaustively, which is harder to do reliably when the same logic is entangled with a ViewModel or Activity.
- Repository interfaces should expose only the data a use case genuinely needs, not a full raw data-layer model, so a use case cannot accidentally leak a field (an internal identifier, a raw credential) that the presentation layer was never meant to see.

## 18. References

- Robert C. Martin, The Clean Architecture (https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- Android Developers, Domain layer (https://developer.android.com/topic/architecture/domain-layer)

## Code examples

### Python

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Order:
    id: str
    total_cents: int
    is_eligible_for_discount: bool


class OrderRepository(ABC):
    @abstractmethod
    def find_by_id(self, order_id):
        raise NotImplementedError


class ApplyDiscountUseCase:
    def __init__(self, repository):
        self._repository = repository

    def execute(self, order_id, discount_percent):
        order = self._repository.find_by_id(order_id)
        if not order.is_eligible_for_discount:
            return order
        discounted = int(order.total_cents * (100 - discount_percent) / 100)
        return Order(order.id, discounted, order.is_eligible_for_discount)


class SqliteOrderRepository(OrderRepository):
    def find_by_id(self, order_id):
        return Order(order_id, 10000, True)


use_case = ApplyDiscountUseCase(repository=SqliteOrderRepository())
result = use_case.execute('order-1', discount_percent=10)
print('discounted total', result.total_cents)
```

### Kotlin

```kotlin
data class Order(val id: String, val totalCents: Int, val isEligibleForDiscount: Boolean)

interface OrderRepository {
    suspend fun findById(orderId: String): Order
}

class ApplyDiscountUseCase(private val repository: OrderRepository) {
    suspend fun execute(orderId: String, discountPercent: Int): Order {
        val order = repository.findById(orderId)
        if (!order.isEligibleForDiscount) return order
        val discounted = order.totalCents * (100 - discountPercent) / 100
        return order.copy(totalCents = discounted)
    }
}

class SqliteOrderRepository : OrderRepository {
    override suspend fun findById(orderId: String): Order {
        return Order(orderId, 10000, true)
    }
}

suspend fun demo() {
    val useCase = ApplyDiscountUseCase(repository = SqliteOrderRepository())
    val result = useCase.execute("order-1", discountPercent = 10)
    println("discounted total " + result.totalCents)
}
```

### Swift

```swift
struct Order {
    let id: String
    let totalCents: Int
    let isEligibleForDiscount: Bool
}

protocol OrderRepository {
    func findById(_ orderId: String) async throws -> Order
}

struct ApplyDiscountUseCase {
    let repository: OrderRepository

    func execute(orderId: String, discountPercent: Int) async throws -> Order {
        let order = try await repository.findById(orderId)
        guard order.isEligibleForDiscount else { return order }
        let discounted = order.totalCents * (100 - discountPercent) / 100
        return Order(id: order.id, totalCents: discounted, isEligibleForDiscount: order.isEligibleForDiscount)
    }
}

struct SqliteOrderRepository: OrderRepository {
    func findById(_ orderId: String) async throws -> Order {
        return Order(id: orderId, totalCents: 10000, isEligibleForDiscount: true)
    }
}

let useCase = ApplyDiscountUseCase(repository: SqliteOrderRepository())
Task {
    let result = try await useCase.execute(orderId: "order-1", discountPercent: 10)
    print("discounted total " + String(result.totalCents))
}
```
