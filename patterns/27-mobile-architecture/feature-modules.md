---
name: Feature Modules
slug: feature-modules
family: 27-mobile-architecture
category: Structural
aliases: [App Modularization, Multi-Module Architecture]
first_described: 'Google Android Developers, "Guide to app modularization" architecture guidance'
maturity: canonical
related: [clean-architecture, single-activity-architecture]
incompatible_with: []
verified: 2026-08-22
---

# Feature Modules

## 1. Name, aliases, and lineage

The canonical name is Feature Modules, a pattern where an app's
functionality is split into separate, independently buildable
modules, each one owning a single, isolated part of the app's real
functionality, most commonly one screen or one closely related group
of screens, rather than the whole app living in one large, undivided
module. Google's own modularization guidance states the core
definition directly, "modularization is a practice of organizing a
codebase into loosely coupled and self contained parts. Each part is
a module. Each module is independent and serves a clear purpose." The
same guidance defines the specific feature-module unit directly, "a
feature is an isolated part of an app's functionality that usually
corresponds to a screen or series of closely related screens, like a
sign up or checkout flow."

The alias **App Modularization** names the pattern by its broader,
whole-app practice. **Multi-Module Architecture** names it by its
real, structural result, a codebase built from more than one
independently buildable module rather than a single, undivided one.

## 2. Problem and context

A single, undivided app module genuinely forces every real change,
however small, to rebuild and recompile the entire codebase, and it
genuinely gives every part of the code equal, unrestricted access to
every other part, with no real, enforced boundary preventing a screen
from reaching into another feature's private internals. Google's own
guidance names the resulting cost directly, "by dividing a problem
into smaller and easier to solve subproblems, you reduce the
complexity of designing and maintaining a large system." Feature
Modules solve this by splitting the app along its real feature
boundaries, so a real change to one feature only rebuilds that
feature's own module, and by making every module's own internals
genuinely inaccessible from outside it, per Google's own stated
mechanism, "you can mark everything but your public interface as
internal or private to prevent it from being used outside the
module."

## 3. Forces

The pattern balances the following competing pressures.

- **A real build that only rebuilds what genuinely changed.** Favored.
  Google's own guidance states this directly, Gradle's own
  "incremental build, build cache, and parallel build" mechanisms use
  a module boundary to improve real build performance.
- **A real, enforced boundary between one feature's internals and the
  rest of the app.** Favored. Google's own guidance states this
  directly, modules "enable you to easily control what you expose to
  other parts of your codebase."
- **Code and features that can genuinely be reused or conditionally
  included.** Favored. Google's own guidance states this directly,
  "apps should be a sum of their features where the features are
  organized as separate modules. The functionality that a certain
  module provides may or may not be enabled in a particular app."
- **A real, additional module graph that must genuinely stay
  acyclic.** Sacrificed. Google's own guidance names the real risk
  directly, a real dependency between two modules "may also be
  impossible, such as with cyclic dependencies," a constraint the
  team must genuinely design around.
- **A real, up-front decision about where each feature's real
  boundary genuinely lies.** Sacrificed. Google's own high-cohesion,
  low-coupling principle, "modules should have clearly defined
  responsibilities and stay within boundaries of certain domain
  knowledge," is a genuine, ongoing design judgment, not a mechanical
  rule.

## 4. Applicability and non-applicability

Reach for Feature Modules when the following hold.

- The app genuinely has real, distinct features, per Google's own
  definition, "a screen or series of closely related screens," that
  benefit from being built, tested, and reasoned about independently.
- The team genuinely wants a real, enforced boundary preventing one
  feature from reaching into another's internals, per Google's own
  visibility-control benefit.
- The real build time or the real team size has genuinely grown large
  enough that a single, undivided module's real rebuild cost or real
  ownership ambiguity has become a genuine problem.

Do NOT reach for Feature Modules in these cases, and the reason
matters more than the rule.

- **The app genuinely has too few real, distinct features, or is
  genuinely too small, for the real module-boundary overhead to be
  worth its own cost**, a small app with one real team and a fast real
  build gains little from splitting what was never genuinely large.
- **The team genuinely cannot commit to designing and maintaining a
  real, acyclic module dependency graph**, per Google's own named
  cyclic-dependency risk, introducing modules without that discipline
  can create a real, tangled graph that is harder to reason about than
  the single module it replaced.
- **The real features genuinely share so much internal state or logic
  that splitting them would force a real, awkward, artificial
  boundary**, per Google's own high-cohesion principle, features that
  are not genuinely independent should not be forced into separate
  modules only to match the pattern.

## 5. Structure

Feature Modules has four structural parts, per Google's own module
taxonomy.

- **The app module**, Google's own definition, "an entry point to the
  application. They depend on feature modules and usually provide
  root navigation."
- **Feature modules**, Google's own definition, each one "an isolated
  part of an app's functionality," and Google's own stated dependency
  rule, "feature modules depend on data modules."
- **Data modules**, Google's own description, encapsulating "all data
  and business logic of a certain domain" and exposing "the repository
  as an external API," while hiding "all implementation details and
  data sources from the outside."
- **Common (core) modules**, Google's own definition, containing
  "code that other modules frequently use," reducing redundancy
  without representing "any specific layer in an app's architecture."

## 6. ASCII structure diagram

```
  App module (entry point, root navigation)
        |
        +-- Feature module A
        |         |
        |         v
        |     Data module (repository as the only public API)
        |
        +-- Feature module B
                  |
                  v
              Data module (shared, or its own)

  Common (core) modules
     (used by any of the above, no specific layer)
```

## 7. Dynamics

The trace below shows one complete real dependency resolution, per
Google's own described module graph.

```
The app module starts

per Google's own description, the app module is "an entry point to
the application" that "depend[s] on feature modules and usually
provide[s] root navigation"
   |-- it navigates the user into a real feature module

The feature module needs real data

per Google's own stated rule, "feature modules depend on data
modules"
   |-- it calls the data module's own exposed repository, per Google's
       own description, the only real public surface a data module
       exposes
   |-- the data module's own real implementation details and data
       sources stay hidden, per Google's own stated encapsulation

Two features need to communicate

per Google's own named constraint, direct communication "may also be
impossible, such as with cyclic dependencies"
   |-- rather than depending on each other directly, a third,
       mediating module is introduced, per Google's own described
       solution, "you can have a third module mediating between two
       other modules"
```

## 8. Implementation variants

**Feature-per-screen modularization, the fine-grained form.** Each
real, individual screen becomes its own module, increasing the real
build-time and ownership isolation benefit, at the cost of a larger
real module count and graph to maintain.

**Feature-per-flow modularization, Google's own described default.**
A module covers one real, closely related group of screens, per
Google's own definition, "a sign up or checkout flow," balancing real
isolation against a manageable real module count.

**Dependency-inversion variant.** A variant applying Google's own
described abstraction-and-implementation split directly, "modules
that rely on the behavior defined in the abstraction module should
only depend on the abstraction itself, rather than the specific
implementations," so a feature module depends on an interface module
rather than a concrete data-module implementation, further loosening
the real coupling between them.

## 9. Known production uses

**Google, Android Developers, "Guide to app modularization", the
pattern's own core definition and benefits.** Google states the
mechanism and its benefits directly. "Modularization is a practice of
organizing a codebase into loosely coupled and self contained parts."
"Apps should be a sum of their features where the features are
organized as separate modules." "You can mark everything but your
public interface as internal or private to prevent it from being
used outside the module." Google, Android Developers, "Guide to app
modularization," https://developer.android.com/topic/modularization,
verified 2026-08-22.

**Google, Android Developers, "Common modularization patterns", the
pattern's own module taxonomy and dependency rules.** Google states
the four module types and the cyclic-dependency solution directly. "A
feature is an isolated part of an app's functionality that usually
corresponds to a screen or series of closely related screens." "
Feature modules depend on data modules." "App modules are an entry
point to the application. They depend on feature modules." "You can
have a third module mediating between two other modules." Google,
Android Developers, "Common modularization patterns,"
https://developer.android.com/topic/modularization/patterns, verified
2026-08-22.

## 10. Consequences

Positive.

- A real change to one feature only rebuilds that feature's own
  module, per Google's own stated build-performance benefit, rather
  than the whole app.
- A real, enforced boundary genuinely prevents one feature from
  reaching into another's internals, per Google's own visibility-
  control mechanism.
- Features, and their underlying data modules, are genuinely reusable
  or conditionally includable across more than one real app target,
  per Google's own stated reusability benefit.

Negative.

- The team must genuinely design and maintain a real, acyclic module
  dependency graph, per Google's own named cyclic-dependency risk, a
  real, ongoing structural discipline.
- Choosing where each real feature's boundary genuinely lies, per
  Google's own high-cohesion, low-coupling principle, is a real,
  ongoing design judgment, not a mechanical rule.
- A small app genuinely gains little from the real module-boundary
  overhead, per the non-applicability named in dimension 4.

## 11. Failure modes and misuse

**Letting two feature modules depend on each other directly, so the
real module graph becomes cyclic, breaking Google's own stated
requirement that a real dependency between modules stay resolvable.**
Symptom. The real build genuinely fails to resolve, or the team
resorts to a real, awkward workaround, such as merging the two
modules back together, because the graph itself is not genuinely
acyclic. Cause. Introducing a direct dependency from one feature
module to another, rather than genuinely applying Google's own
described mediator-module solution, "a third module mediating between
two other modules." Fix. Confirm no two feature modules genuinely
depend on each other directly, and introduce a real, dedicated
mediating module for any real cross-feature communication, per
Google's own described solution.

**Passing a real, concrete object as a navigation argument between
feature modules, rather than a plain identifier, violating Google's
own best-practice rule.** Symptom. Two features become silently
coupled to the same real object's concrete shape, and the real
single-source-of-truth guarantee genuinely breaks, because the
receiving feature now holds its own, potentially stale copy of data
the sending feature already owned. Cause. Not applying Google's own
stated rule directly, "you shouldn't pass objects as navigation
arguments. Instead, use simple ids that features can use to access
and load desired resources from the data layer." Fix. Confirm every
real cross-module navigation argument is a plain identifier, per
Google's own rule, with the receiving feature loading the real, current
data itself from the data layer, never receiving a copy passed
directly.

**Splitting features into modules that genuinely do not have clearly
defined, independent responsibilities, violating Google's own
high-cohesion principle and reintroducing tight coupling inside a
multi-module structure.** Symptom. The real module boundaries add
real overhead, extra build configuration, extra indirection, without
delivering the real isolation the pattern exists to provide, because
the "separate" modules still genuinely reach into each other's
internal state constantly. Cause. Modularizing along a boundary that
does not genuinely reflect the app's real feature structure, rather
than genuinely applying Google's own stated principle, modules
"should have clearly defined responsibilities and stay within
boundaries of certain domain knowledge." Fix. Confirm each real module
boundary reflects a genuinely independent, cohesive part of the app's
real functionality, and merge back together any modules that were
split without a genuine, real boundary between them.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Feature Modules (Google's own mechanism) | A single, undivided app module | Feature-per-package, no real module boundary |
|---|---|---|---|
| Real incremental build performance | Strong, per Google's own stated Gradle benefit | Weak, every real change rebuilds the whole app | Weak, the compiler still treats it as one real compilation unit |
| Real, enforced internal-visibility boundary | Strong, per Google's own internal/private mechanism | None, everything is genuinely accessible from everywhere | Weak, package-private visibility is real but far more porous than a real module boundary |
| Real reusability or conditional inclusion of a feature | Strong, per Google's own stated reusability benefit | None, the whole app is one real, indivisible unit | Weak, a package cannot genuinely be included or excluded independently |
| Real graph-maintenance overhead | Real, the team must genuinely keep the module graph acyclic | None, there is no real graph to maintain | Low, but the real benefits above are also genuinely absent |

Reading of the table. Feature Modules wins specifically when the app
genuinely has real, distinct features and the team genuinely wants
real build-performance and visibility-control benefits worth the real
graph-maintenance cost. A genuinely small app, or one whose real
features are not genuinely independent, fits a single module or a
lighter package-based boundary better.

## 13. Related and incompatible patterns

- **Clean Architecture (Mobile).** A genuinely complementary concern,
  Clean Architecture's own layering, per that entry, commonly maps
  directly onto this pattern's own module taxonomy, a data module
  corresponding to the domain and data layers, and a feature module
  corresponding to the presentation layer for one real screen or flow.
- **Single Activity Architecture.** A genuinely complementary concern,
  a single-activity app commonly hosts destinations that live in, and
  are opened from, separate real feature modules, the two
  patterns composing directly.

## 14. Refactoring path in and out

Introducing the pattern into a single, undivided app module. Ordered
steps, most relevant when the real build time or real team-ownership
ambiguity named in dimension 2 has genuinely become a problem.

1. Identify the app's real, genuine feature boundaries, per Google's
   own definition, "a screen or series of closely related screens,"
   rather than an arbitrary technical split.
2. Extract each real feature's own data access into a genuine data
   module, exposing only "the repository as an external API," per
   Google's own stated data-module responsibility.
3. Extract each real feature's own presentation code into its own
   feature module, depending only on its real data module, per
   Google's own stated dependency rule.
4. Confirm the resulting real module graph is genuinely acyclic, and
   introduce a real mediating module for any real cross-feature
   communication that would otherwise create a cycle.

Removing the pattern when it stops earning its place, most relevant
when the app has genuinely shrunk, or the real module-maintenance
overhead has genuinely stopped being worth its own cost.

1. Confirm, concretely, that the app's real features no longer benefit
   from independent building, testing, or ownership.
2. Merge the real feature and data modules back into a single,
   undivided module, removing the real module-boundary overhead.
3. Confirm no other part of the build, such as a real Play Feature
   Delivery configuration, still depends on the module split before
   removing it entirely.

## 15. Testing and verification

Easier because of the pattern.

- A real feature module can be built and tested genuinely in
  isolation, per Google's own stated testability benefit, with no
  real need to compile or run the rest of the app.
- A real data module's own exposed repository can be tested against a
  real, known API surface, per Google's own encapsulation description,
  with its own internal data sources genuinely hidden from the test.

Harder because of the pattern.

- Verifying the real, full app behavior across more than one feature
  module needs a real integration or full-flow test that exercises
  the real, assembled module graph, not only one module in isolation.
- Confirming the real module dependency graph stays genuinely acyclic
  as the app grows needs a real, structural check, not something a
  single module's own unit tests can catch.

Techniques that apply.

- **Per-module unit tests.** Test a real feature or data module's own
  logic in isolation, with no real dependency on the rest of the app's
  modules being built or run.
- **Dependency-graph audits.** Assert the real module dependency
  graph stays genuinely acyclic, catching the reintroduced-cycle
  failure mode from dimension 11 before it reaches a real build
  failure.
- **Cross-module integration tests.** Assemble a real subset of
  modules and exercise a genuine, real user flow that spans more than
  one feature module.
- **Navigation-argument audits.** Confirm every real cross-module
  navigation call passes a plain identifier, per Google's own rule,
  catching the object-passing failure mode from dimension 11.

## 16. Observability signals

What to record.

- The real, current shape of the module dependency graph, since any
  genuinely cyclic edge points directly at the reintroduced-cycle
  failure mode from dimension 11.
- Whether any real cross-module navigation call passes a concrete
  object rather than a plain identifier, since any such call points
  directly at the object-passing failure mode from dimension 11.

A healthy state. The real module dependency graph stays genuinely
acyclic, and every real cross-module navigation call passes only a
plain identifier.

A failing state. A genuinely cyclic edge is found in the real module
graph, pointing directly at a reintroduced cycle, or a cross-module
navigation call is found passing a concrete object, pointing directly
at a broken single-source-of-truth guarantee.

## 17. Security and privacy implications

**Because Google's own visibility-control mechanism genuinely relies
on marking a module's own real internals as internal or private, a
data module that genuinely holds sensitive data, such as a real
authentication token or a real payment credential, is only as secure
as the discipline with which that boundary is genuinely maintained,
and a single real, careless public exposure of an internal type
defeats the boundary for every module that depends on it.** Because
Google's own visibility-control benefit is a real, compiler-enforced
mechanism only when genuinely used correctly, a data module's own
public API must genuinely expose only what a consuming feature module
actually needs, per Google's own stated principle, "hide all
implementation details and data sources from the outside," never a
broader surface that happens to also carry a sensitive internal type
along with it. Confirming a data module's own public API is genuinely
minimal, and never accidentally exposes a sensitive internal type
through a real, broader-than-intended visibility modifier, is a
necessary part of a security-conscious Feature Modules
implementation.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. Kotlin models Google's own original mechanism directly, the
language and build system, Gradle, the pattern's own canonical
documentation is written for. Swift shows the same conceptual shape on
iOS, an idiomatic composition of separate Swift packages standing in
for Google's own module boundary. Python shows the same conceptual
shape using a minimal, host-testable simulation of the module
dependency graph and the mediator-module solution, useful for
verifying the acyclic-graph and mediator mechanisms in isolation, per
dimension 15, expressed portably. Java, Go, and Rust are omitted,
since the pattern's real home is mobile-app build systems, and the
three languages chosen already cover its two production platforms and
its testable-simulation shape.

### Kotlin

```kotlin
// data module's own public API
interface CheckoutRepository {
    fun currentOrderId(): String
}

class InMemoryCheckoutRepository : CheckoutRepository {
    override fun currentOrderId() = "order-42"
}

// feature module, depends only on the data module's own interface
class CheckoutFeature(private val repository: CheckoutRepository) {
    fun start() {
        println("checkout for " + repository.currentOrderId())
    }
}

// mediator module, avoids a direct feature-to-feature dependency
class FeatureMediator {
    private val listeners = mutableListOf<(String) -> Unit>()

    fun onOrderPlaced(listener: (String) -> Unit) {
        listeners.add(listener)
    }

    fun notifyOrderPlaced(orderId: String) {
        listeners.forEach { it(orderId) }
    }
}

fun main() {
    val repository = InMemoryCheckoutRepository()
    val checkout = CheckoutFeature(repository)
    checkout.start()

    val mediator = FeatureMediator()
    mediator.onOrderPlaced { orderId -> println("receipts feature notified of " + orderId) }
    mediator.notifyOrderPlaced(repository.currentOrderId())
}
```

### Swift

```swift
// data module's own public API
protocol CheckoutRepository {
    func currentOrderId() -> String
}

final class InMemoryCheckoutRepository: CheckoutRepository {
    func currentOrderId() -> String { "order-42" }
}

// feature module, depends only on the data module's own interface
final class CheckoutFeature {
    private let repository: CheckoutRepository

    init(repository: CheckoutRepository) {
        self.repository = repository
    }

    func start() {
        print("checkout for", repository.currentOrderId())
    }
}

// mediator module, avoids a direct feature-to-feature dependency
final class FeatureMediator {
    private var listeners: [(String) -> Void] = []

    func onOrderPlaced(_ listener: @escaping (String) -> Void) {
        listeners.append(listener)
    }

    func notifyOrderPlaced(_ orderId: String) {
        listeners.forEach { $0(orderId) }
    }
}

let repository = InMemoryCheckoutRepository()
let checkout = CheckoutFeature(repository: repository)
checkout.start()

let mediator = FeatureMediator()
mediator.onOrderPlaced { orderId in print("receipts feature notified of", orderId) }
mediator.notifyOrderPlaced(repository.currentOrderId())
```

### Python

```python
from typing import Callable, List, Protocol


class CheckoutRepository(Protocol):
    def current_order_id(self) -> str: ...


class InMemoryCheckoutRepository:
    def current_order_id(self) -> str:
        return "order-42"


class CheckoutFeature:
    def __init__(self, repository: CheckoutRepository):
        self.repository = repository

    def start(self) -> None:
        print("checkout for", self.repository.current_order_id())


class FeatureMediator:
    def __init__(self):
        self.listeners: List[Callable[[str], None]] = []

    def on_order_placed(self, listener: Callable[[str], None]) -> None:
        self.listeners.append(listener)

    def notify_order_placed(self, order_id: str) -> None:
        for listener in self.listeners:
            listener(order_id)


if __name__ == "__main__":
    repository = InMemoryCheckoutRepository()
    checkout = CheckoutFeature(repository)
    checkout.start()

    mediator = FeatureMediator()
    mediator.on_order_placed(
        lambda order_id: print("receipts feature notified of", order_id)
    )
    mediator.notify_order_placed(repository.current_order_id())
```

## 18. References

1. Google, Android Developers. "Guide to app modularization".
   https://developer.android.com/topic/modularization
   Verified 2026-08-22. Source of the core modularization definition,
   the feature-module definition, the visibility-control and
   reusability benefits, and the build-performance benefit, used in
   dimensions 1, 2, 3, 5, 9, and 10.
2. Google, Android Developers. "Common modularization patterns".
   https://developer.android.com/topic/modularization/patterns
   Verified 2026-08-22. Source of the four-module taxonomy, the
   high-cohesion-low-coupling principle, the cyclic-dependency
   mediator solution, and the navigation-argument rule, used in
   dimensions 1, 3, 5, 7, 9, and 11.
