---
name: Coordinator Pattern
slug: coordinator-pattern
family: 27-mobile-architecture
category: Structural
aliases: [Flow Coordinator, Navigator Pattern, App Coordinator]
first_described: 'Soroush Khanlou, "The Coordinator", 2015'
maturity: canonical
related: [mvvm-c, deep-link-router]
incompatible_with: []
verified: 2026-08-22
---

# Coordinator Pattern

## 1. Name, aliases, and lineage

The canonical name is Coordinator Pattern, an object whose sole job is
to own navigation and flow decisions for one or more view controllers,
removing that responsibility from the view controllers themselves. The
pattern was introduced by Soroush Khanlou in a 2015 blog post and a
related conference talk, and his own framing of the core idea is
direct, "a coordinator is an object that bosses one or more view
controllers around. Taking all of the driving logic out of your view
controllers, and moving that stuff one layer up is gonna make your
life a lot more awesome." A later companion post describes the object
more directly, "an even higher level object, one whose role is to
marshal and manage all the view controllers in its purview."

The alias **Flow Coordinator** names the pattern by the specific
concern it owns, the sequence of screens a user moves through for one
task. **Navigator Pattern** names it by its most visible action,
deciding which screen appears next. **App Coordinator** names the
root-level instance many implementations use, the single top-level
coordinator that owns the whole app's navigation tree and creates
child coordinators as the user moves through different flows.

## 2. Problem and context

A view controller that decides what happens after a button tap,
whether to push a new screen, present a modal, or pop back, is a view
controller that knows about the rest of the app's navigation graph,
not only its own screen. Khanlou names the resulting failure mode
directly, a view controller "is now grabbing its parent, because
remember, these view controllers exist in a hierarchy, and then it's
sending a precise message to its parent about what to do. It's
bossing its parent around." As an app grows, this spreads navigation
logic across every view controller that can trigger a transition, and
Khanlou names the concrete symptom, "your navigation flow is now
spread among three different objects" for even a short user-facing
flow, making the real flow of screens hard to see, hard to test, and
hard to change without touching several unrelated view controllers.

## 3. Forces

The pattern balances the following competing pressures.

- **View controllers that only render and report, never decide where
  to go next.** Favored. Khanlou states this directly, "view
  controllers don't know anything beyond how to present their data.
  Whenever anything happens, it tells its delegate, but of course it
  doesn't know who its delegate is."
- **A single, inspectable place to read and change navigation
  logic.** Favored. Rather than navigation decisions scattered across
  every view controller that can trigger one, per Khanlou's own
  description of the spread-out failure mode, one coordinator owns the
  whole flow.
- **Composability across independent flows.** Favored. Khanlou's own
  child-coordinator mechanism states this directly, "every coordinator
  holds an array of its child coordinators," so a large app's
  navigation tree is built from small, independently testable pieces
  rather than one monolithic router.
- **A new layer of objects to create, own, and release correctly.**
  Sacrificed. Every flow needs its own coordinator instance, and every
  coordinator's lifetime, and its parent's array of child
  coordinators, must be managed correctly or a coordinator, and the
  view controllers it owns, leaks.
- **Indirection between a user action and the screen that appears.**
  Sacrificed. Reading "what happens when this button is tapped" now
  means following a delegate call from the view controller out to its
  coordinator, rather than reading a single, local push or present
  call inline.

## 4. Applicability and non-applicability

Reach for the Coordinator Pattern when the following hold.

- The app genuinely has more than one user-facing flow, such as
  onboarding, the main tab flow, and a settings flow, each of which
  benefits from being read, tested, and changed independently, per
  Khanlou's own child-coordinator composition mechanism.
- View controllers in the app genuinely need to be reusable across
  more than one flow, and deciding "what screen comes next" needs to
  live outside the view controller for that reuse to work cleanly.
- The team genuinely values being able to read the app's whole
  navigation graph from one place, rather than reconstructing it by
  reading every view controller's own transition calls.

Do NOT reach for the Coordinator Pattern in these cases, and the
reason matters more than the rule.

- **The app genuinely has one simple, linear flow, with no real
  prospect of screens being reused across different contexts**, the
  extra coordinator layer and its lifetime-management overhead add
  real complexity for a navigation graph that a platform's own
  built-in navigation controller already expresses clearly.
- **The team genuinely finds the coordinator's own delegate-call
  indirection harder to follow than the view controller's own inline
  transition calls**, for a small app, this is a real, legitimate
  trade-off, and Khanlou's own stated benefit, one inspectable place
  for navigation logic, only pays off once the app is genuinely large
  enough for that indirection to be worth it.
- **The platform's own idiomatic navigation and state-restoration
  mechanisms genuinely already solve the real problem**, layering a
  custom coordinator hierarchy over a navigation system that already
  works well can add real, unneeded structure without matching real
  benefit.

## 5. Structure

The Coordinator Pattern has three structural parts, per Khanlou's own
description.

- **The coordinator object itself**, described directly as "an even
  higher level object, one whose role is to marshal and manage all the
  view controllers in its purview," a plain object, Khanlou calls it
  "a PONSO, like all great objects", holding no UIKit-specific base
  class requirement.
- **The child-coordinator array**, Khanlou's own composition
  mechanism, "every coordinator holds an array of its child
  coordinators," added to when a new child flow starts and removed
  from when a child flow finishes.
- **The view controllers the coordinator owns and directs**, which
  stay "inert", per Khanlou's own description, a view controller "can
  be presented, it can fetch data, transform it for presentation,
  display it, but it crucially can't alter it," reporting user actions
  upward through a delegate rather than deciding what happens next
  itself.

## 6. ASCII structure diagram

```
  App Coordinator (root, owns the whole navigation tree)
        |
        |-- childCoordinators [ ]
        |
        +-- Onboarding Coordinator
        |       |
        |       +-- view controller (delegate reports "next tapped")
        |
        +-- Main Flow Coordinator
                |
                +-- view controller (delegate reports "item selected")
                +-- view controller (delegate reports "back tapped")
```

## 7. Dynamics

The trace below shows one complete flow transition.

```
The user taps a button on a screen

the view controller does not decide what happens next itself, per
Khanlou's own description, it "doesn't know anything beyond how to
present their data"
   |-- it reports the action to its delegate, which it does not know
       the concrete identity of

The coordinator, set as that delegate, receives the report

the coordinator, per Khanlou's own description, "bosses one or more
view controllers around"
   |-- it decides the real next step, push a new view controller,
       present a modal, or start a new child coordinator entirely
   |-- if a new flow is starting, the coordinator creates a child
       coordinator and adds it to its own childCoordinators array,
       per Khanlou's own composition mechanism

The child flow finishes

the child coordinator reports completion back to its parent
   |-- the parent removes the finished child from its
       childCoordinators array, releasing it and the view controllers
       it owned
```

## 8. Implementation variants

**Delegate-protocol coordinator, Khanlou's own original form.** Each
coordinator conforms to a small protocol, start, and the view
controllers it owns report user actions upward through their own
delegate protocols, exactly as Khanlou's original posts describe.

**Closure-based coordinator.** A variant that replaces the
delegate-protocol reporting mechanism with closures passed at
creation time, so a view controller calls a completion closure rather
than a named delegate method, trading Khanlou's original delegate
indirection for a lighter-weight callback at the cost of losing a
named, discoverable protocol.

**Coordinator with a shared router or navigator object.** A variant
where the actual push and present calls are extracted into a separate,
shared router object that every coordinator calls into, so the
coordinators themselves hold only flow-decision logic, and the
concrete navigation-controller manipulation lives in one reusable
place.

## 9. Known production uses

**Soroush Khanlou, "Coordinators Redux", the pattern's own core
motivation and mechanism.** Khanlou states the core idea and its
benefit directly. "A coordinator is an object that bosses one or more
view controllers around. Taking all of the driving logic out of your
view controllers, and moving that stuff one layer up is gonna make
your life a lot more awesome." The problem it solves, a view
controller "is now grabbing its parent... it's bossing its parent
around," and the resulting spread, "your navigation flow is now spread
among three different objects." Soroush Khanlou, "Coordinators
Redux," https://khanlou.com/2015/10/coordinators-redux/, verified
2026-08-22.

**Soroush Khanlou, "The Coordinator", the original composition
mechanism.** Khanlou's own words describe the object and its
child-coordinator composition directly. "An even higher level object,
one whose role is to marshal and manage all the view controllers in
its purview." The composition mechanism, "every coordinator holds an
array of its child coordinators." Soroush Khanlou, "The Coordinator,"
https://khanlou.com/2015/01/the-coordinator/, verified 2026-08-22.

## 10. Consequences

Positive.

- View controllers stay reusable and inert, per Khanlou's own
  description, they present and report, and never decide the real
  next screen, so the same view controller can be reused across
  different flows without modification.
- Navigation logic lives in one inspectable place per flow, rather
  than spread across every view controller that can trigger a
  transition, directly reversing the spread-out failure Khanlou names.
- Independent flows compose cleanly through the child-coordinator
  array, so a large app's navigation tree is built and tested in
  small, independent pieces.

Negative.

- The coordinator hierarchy and its child-coordinator array become a
  real, additional object graph that must be managed correctly, or a
  finished child coordinator, and the view controllers it owned, leaks
  memory.
- Reading "what happens when this button is tapped" now needs
  following a delegate call out to a coordinator, rather than reading
  one inline transition call, a real, genuine indirection cost.
- A poorly-scoped coordinator hierarchy, one coordinator per screen
  rather than per flow, can recreate the exact same spread of
  navigation logic the pattern exists to avoid, only moved into more,
  smaller coordinator objects instead of view controllers.

## 11. Failure modes and misuse

**Forgetting to remove a finished child coordinator from its parent's
childCoordinators array.** Symptom. The finished coordinator, and
every view controller and closure it retained, stays alive in memory
long after its flow has genuinely ended, a real, silent memory leak
that grows with every flow the user completes. Cause. Not calling the
parent's removal step on the finished child, per Khanlou's own
described removal mechanism, often because the "flow finished" signal
was never wired up for every real exit path, such as a user
dismissing a modal by swiping rather than tapping a genuine
completion button. Fix. Confirm every real way a flow can end,
including a swipe-to-dismiss or a system-triggered cancellation, calls
the same completion path that removes the child coordinator from its
parent's array.

**Letting a view controller reach directly into its coordinator's
concrete type, rather than reporting through a delegate protocol,
reintroducing the exact coupling this pattern exists to remove.**
Symptom. A view controller that was genuinely reusable across
different flows becomes silently coupled to one specific coordinator
implementation, breaking the moment it is placed inside a different
flow's coordinator. Cause. Reaching for the coordinator's own concrete
type directly from the view controller, perhaps for convenience,
rather than reporting the action through a delegate protocol the view
controller does not know the concrete identity of, per Khanlou's own
description, "it doesn't know who its delegate is." Fix. Report every
user action from a view controller through a delegate protocol, never
a concrete coordinator reference, and treat any direct reference as a
structural bug reintroducing the original coupling.

**Creating one coordinator per individual screen rather than per
genuine flow, recreating the original spread-out navigation problem
inside the coordinator layer instead of removing it.** Symptom. The
app ends up with as many coordinators as it has screens, and reading
one real user flow means following a chain of many tiny coordinators,
every bit as confusing as the original chain of view controllers Khanlou's
own posts describe the problem in terms of. Cause. Scoping each
coordinator to a single screen instead of a single, genuine flow, so
the pattern is applied mechanically rather than at the granularity
where it genuinely earns its own overhead. Fix. Scope each coordinator
to a real, coherent user-facing flow, such as onboarding or checkout,
not to an individual screen, and let a single coordinator own several
screens within that one flow.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Coordinator Pattern (Khanlou's own mechanism) | View controllers own navigation directly | A single shared router with no coordinator hierarchy |
|---|---|---|---|
| View-controller reusability | Strong, per Khanlou's own inert-view-controller description | Weak, a view controller is coupled to its own transition calls | Moderate, screens are decoupled from navigation calls but not from each other's flow logic |
| One inspectable place per flow | Strong, per Khanlou's own child-coordinator composition | None, navigation logic is spread across every triggering view controller | Partial, one place for all navigation, but not scoped per flow |
| Composability across independent flows | Strong, the childCoordinators array, per Khanlou's own mechanism | Weak, flows are entangled through direct view-controller-to-view-controller calls | Weak, one router usually handles every flow, with no natural flow boundary |
| Object-lifetime management overhead | Real, a coordinator hierarchy that must be released correctly | None, no coordinator objects exist | Low, a single shared router with a simple lifetime |

Reading of the table. The Coordinator Pattern wins specifically when
an app genuinely has multiple, independent, growing flows and
view-controller reusability across them is genuinely valuable. A
small, linear app fits direct view-controller navigation better, and
an app that wants centralized navigation with no real per-flow
boundary fits a single shared router better than a full coordinator
hierarchy.

## 13. Related and incompatible patterns

- **MVVM-C (Model-View-ViewModel-Coordinator).** The direct
  composition of this pattern with MVVM, where the coordinator owns
  navigation exactly as described here, and each screen's own
  presentation logic lives in a separate view model, the two concerns
  kept genuinely apart.
- **Deep Link Router.** A deep link handler frequently needs to drive
  the same coordinator hierarchy this pattern builds, jumping straight
  to a specific child coordinator or screen rather than walking the
  full, normal flow from the root, so the two patterns commonly
  compose directly.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a codebase where view controllers currently
trigger their own navigation directly.

1. Identify the app's real, genuine flows, such as onboarding, the
   main tab flow, and settings, rather than one coordinator per
   screen, per the failure mode named in dimension 11.
2. Create one coordinator per genuine flow, and move that flow's real
   transition decisions, push, present, dismiss, into it.
3. Convert each affected view controller's direct transition calls
   into delegate reports, so the view controller "doesn't know who its
   delegate is," per Khanlou's own description, and never decides the
   next screen itself.
4. Wire the childCoordinators array at the root, per Khanlou's own
   composition mechanism, confirming every flow's real completion path
   removes its coordinator from its parent's array.

Removing the pattern when it stops earning its place, most relevant
when an app has genuinely shrunk, or was always simple enough, that
the coordinator layer adds real overhead without matching benefit.

1. Confirm, concretely, that the app's real navigation is genuinely
   simple and linear enough that one inspectable place for it is no
   longer a real, distinct benefit over the platform's own built-in
   navigation.
2. Move each flow's real transition decisions back into the view
   controllers that trigger them, removing the delegate-report
   indirection.
3. Confirm no other part of the app still depends on a coordinator's
   existence, such as a deep link handler targeting a specific child
   coordinator, before removing the hierarchy entirely.

## 15. Testing and verification

Easier because of the pattern.

- A coordinator's real navigation decisions can be tested in
  isolation, asserting which view controller or child coordinator is
  created next given a specific delegate report, with no real UIKit
  view controller lifecycle needed to drive the test.
- A view controller, kept inert per Khanlou's own description, can be
  tested purely on its own presentation logic, since it genuinely
  never decides where the app goes next.

Harder because of the pattern.

- Verifying the real, full user-facing flow, several screens in
  sequence, end to end, needs a test that drives the real coordinator
  hierarchy and its child-coordinator lifecycle, not only one
  coordinator's decision logic in isolation.
- Confirming a finished child coordinator is genuinely released, and
  did not leak per the failure mode in dimension 11, needs a test that
  can observe real object deallocation, not only the logical
  navigation decision.

Techniques that apply.

- **Coordinator decision tests.** Assert which view controller or
  child coordinator a coordinator creates next, given a specific
  delegate report, with no real UIKit lifecycle driven at all.
- **Inert-view-controller tests.** Assert a view controller's own
  presentation logic in isolation, confirming it reports every user
  action through its delegate and never triggers a transition itself.
- **Child-coordinator lifecycle tests.** Assert a child coordinator is
  genuinely removed from its parent's array, and genuinely
  deallocated, once its real completion path fires.
- **Full-flow tests.** Drive the real coordinator hierarchy
  through a full, genuine user-facing flow and assert the expected
  sequence of screens actually appears.

## 16. Observability signals

What to record.

- The real size of the root coordinator's childCoordinators array
  over time, since a size that only grows and never shrinks points
  directly at the leaked-child-coordinator failure mode from
  dimension 11.
- Whether any view controller in the app genuinely calls a transition
  method directly, rather than reporting through a delegate, since any
  such call points directly at the reintroduced-coupling failure mode
  from dimension 11.

A healthy state. The childCoordinators array's real size tracks the
number of genuinely active flows, growing and shrinking as flows start
and finish, and every view controller in the app reports transitions
exclusively through a delegate.

A failing state. The childCoordinators array's real size only grows
over a session, pointing directly at a leaked child coordinator, or a
view controller is found calling a transition method directly,
pointing directly at reintroduced coupling.

## 17. Security and privacy implications

**A coordinator that retains a completed flow's view controllers and
their own retained data, per the leaked-child-coordinator failure mode
in dimension 11, can keep sensitive information genuinely alive in
memory long after the user believes that flow is finished, such as a
payment or authentication flow's own screen state.** Because a leaked
child coordinator keeps every view controller it owned alive, per
Khanlou's own child-ownership description, any sensitive data those
view controllers held, a typed password field's real backing string,
a fetched payment token, stays in memory well past the point the user
genuinely finished that flow, and can be inspected by any code, or any
memory-inspection tool, with access to the running process. Similarly,
a deep link handler that jumps straight into a specific child
coordinator, per the composition this pattern shares with Deep Link
Router, must confirm the target flow's own real authentication and
authorization checks still run, rather than assuming a deep link that
reaches a screen has implicitly passed whatever checks the normal,
full navigation path would have enforced. Confirming every real flow
completion path removes its coordinator, and confirming a deep-linked
entry point still enforces the same real checks the normal path would
have, are necessary parts of a security-conscious coordinator
implementation.

## 18. References

1. Soroush Khanlou. "Coordinators Redux".
   https://khanlou.com/2015/10/coordinators-redux/
   Verified 2026-08-22. Source of the core coordinator definition, the
   view-controller-bossing-its-parent failure mode, and the
   inert-view-controller description, used in dimensions 1, 2, 3, 5,
   7, and 9.
2. Soroush Khanlou. "The Coordinator".
   https://khanlou.com/2015/01/the-coordinator/
   Verified 2026-08-22. Source of the original coordinator role
   description and the childCoordinators composition mechanism, used
   in dimensions 1, 3, 5, 7, 9, 11, and 16.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. Swift models Khanlou's own original mechanism directly, the
language the pattern was introduced in and is overwhelmingly used in
production. Kotlin shows the same conceptual shape on Android, the
platform's own idiomatic composition of Fragments or Compose
destinations directed by a coordinator-equivalent object. Python shows
the same conceptual shape using a minimal, host-testable simulation,
useful for verifying the coordinator's own decision logic and
child-coordinator lifecycle in isolation, per dimension 15, expressed
portably. Java, Go, and Rust are omitted, since the pattern's real
home is mobile-app UI frameworks, and the three languages chosen
already cover its two production platforms and its testable-simulation
shape.

### Swift

```swift
protocol Coordinator: AnyObject {
    var childCoordinators: [Coordinator] { get set }
    func start()
}

protocol ItemListViewControllerDelegate: AnyObject {
    func itemListDidSelectItem(id: Int)
}

final class ItemListViewController {
    weak var delegate: ItemListViewControllerDelegate?

    func userDidTapItem(id: Int) {
        delegate?.itemListDidSelectItem(id: id)
    }
}

final class ItemFlowCoordinator: Coordinator, ItemListViewControllerDelegate {
    var childCoordinators: [Coordinator] = []
    private let listViewController = ItemListViewController()

    func start() {
        listViewController.delegate = self
    }

    func itemListDidSelectItem(id: Int) {
        print("push detail screen for item", id)
    }
}

final class AppCoordinator: Coordinator {
    var childCoordinators: [Coordinator] = []

    func start() {
        let itemFlow = ItemFlowCoordinator()
        childCoordinators.append(itemFlow)
        itemFlow.start()
    }

    func childDidFinish(_ child: Coordinator) {
        childCoordinators.removeAll { $0 === child }
    }
}

let app = AppCoordinator()
app.start()
```

### Kotlin

```kotlin
interface Coordinator {
    val childCoordinators: MutableList<Coordinator>
    fun start()
}

interface ItemListListener {
    fun onItemSelected(id: Int)
}

class ItemListScreen(private var listener: ItemListListener?) {
    fun onItemTapped(id: Int) {
        listener?.onItemSelected(id)
    }
}

class ItemFlowCoordinator : Coordinator, ItemListListener {
    override val childCoordinators = mutableListOf<Coordinator>()
    private val listScreen = ItemListScreen(null)

    override fun start() {
        listScreen
    }

    override fun onItemSelected(id: Int) {
        println("push detail screen for item $id")
    }
}

class AppCoordinator : Coordinator {
    override val childCoordinators = mutableListOf<Coordinator>()

    override fun start() {
        val itemFlow = ItemFlowCoordinator()
        childCoordinators.add(itemFlow)
        itemFlow.start()
    }

    fun childDidFinish(child: Coordinator) {
        childCoordinators.remove(child)
    }
}

fun main() {
    val app = AppCoordinator()
    app.start()
}
```

### Python

```python
from typing import Protocol, Callable


class Coordinator(Protocol):
    def start(self) -> None: ...


class ItemListScreen:
    def __init__(self, on_select: Callable[[int], None]):
        self._on_select = on_select

    def user_tapped_item(self, item_id: int) -> None:
        self._on_select(item_id)


class ItemFlowCoordinator:
    def __init__(self):
        self.child_coordinators = []
        self._screen = ItemListScreen(self._on_item_selected)

    def start(self) -> None:
        pass

    def _on_item_selected(self, item_id: int) -> None:
        print("push detail screen for item", item_id)


class AppCoordinator:
    def __init__(self):
        self.child_coordinators = []

    def start(self) -> None:
        item_flow = ItemFlowCoordinator()
        self.child_coordinators.append(item_flow)
        item_flow.start()

    def child_did_finish(self, child) -> None:
        self.child_coordinators.remove(child)


if __name__ == "__main__":
    app = AppCoordinator()
    app.start()
```
