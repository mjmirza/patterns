---
name: Single-Activity Architecture
slug: single-activity-architecture
family: 27-mobile-architecture
category: Structural
aliases: [Single Activity, Fragment-Only Navigation, One-Activity Pattern]
first_described: 'Google Android Developers, Navigation component guidance'
maturity: canonical
related: [feature-modules, unidirectional-data-flow]
incompatible_with: []
verified: 2026-08-22
---

# Single-Activity Architecture

## 1. Name, aliases, and lineage

Single-Activity Architecture. Also called Single Activity, Fragment-Only Navigation, or the One-Activity Pattern. The name is literal. the entire app runs inside one Android Activity, and every individual screen is a fragment or a composable managed by a navigation graph, rather than each screen owning its own Activity.

The pattern emerged from Google's own guidance as Android's early convention, one Activity per screen, showed its cost as apps grew large. cross-Activity data passing required Bundle serialization, shared UI state needed awkward workarounds, and transitions between screens were limited by Activity-level animation APIs. Google's Navigation component formalized the alternative directly in its own documentation. While it is best practice to have a single activity in your app, apps often use separate activities for distinct components or screen within an app (https://developer.android.com/guide/navigation/design/activity-destinations). Multiple Android Dev Summit talks, including one titled Single activity, why, when, and how, cemented this as the recommended default for new Android apps from roughly 2018 onward.

## 2. Problem and context

In the pre-Navigation-component era, an Android app with N screens commonly had N Activities. Passing data between them meant serializing it into an Intent's Bundle, which is slow for anything beyond primitives, loses type safety, and has a hard size limit that silently crashes the app (TransactionTooLargeException) when exceeded. Sharing UI state, a logged-in user, a shopping cart, a form draft, across screens meant reaching for a singleton, a static field, or a separate persistence layer only to bridge Activity boundaries that should not have existed in the first place.

Cross-Activity transitions were also limited by the platform itself. shared-element transitions, custom animations, and any UI that needed to persist visually across a navigation event fought against each Activity being its own window with its own lifecycle. Deep linking into a specific screen required either a dedicated Activity per linkable destination or brittle Intent-extras plumbing to reconstruct state inside a shared Activity.

## 3. Forces

- Screens frequently need to share state (a user session, a form in progress) and a shared ViewModel scoped to a single Activity is far simpler than any cross-Activity sharing mechanism.
- Passing typed data between screens should not require Bundle serialization or String-keyed extras, which lose compile-time safety.
- Custom transitions and shared-element animations between screens work far more naturally within one window than across separate Activity windows.
- Deep linking into an arbitrary screen must resolve to a specific destination without launching a new Activity for every possible target.
- A single Activity still needs a navigation model with its own back stack, up/back semantics, and lifecycle boundaries, or the simplification only moves the complexity rather than removing it.

## 4. Applicability and non-applicability

Use single-Activity architecture for essentially any new Android app, especially one with more than a handful of screens that share state, need custom transitions, or must support deep linking into specific destinations. It is the default Google itself recommends for apps built with the Navigation component or Jetpack Compose.

Skip it, or scope it deliberately, when a screen genuinely needs its own process-level isolation or a distinct Activity lifecycle. a launcher shortcut target that must be independently killable by the system, a screen that hosts a separate task on the recents screen by design, or an app widget configuration Activity that Android's own APIs require to be a standalone Activity. Multi-window and multi-instance apps on large-screen devices sometimes need more than one Activity too, so the pattern is a strong default, not an absolute rule.

## 5. Structure

- Host Activity. the single Activity that owns the window, the lifecycle, and hosts the navigation graph's container view (a NavHostFragment or a Compose NavHost).
- Navigation graph. a declarative map of destinations (fragments or composables) and the actions that connect them, owned by a NavController scoped to the Host Activity.
- Destinations. the individual screens, implemented as Fragments or composables, each receiving typed arguments through the navigation graph rather than an Intent Bundle.
- Scoped ViewModels. state shared across a subset of destinations lives in a ViewModel scoped to the navigation graph (or a sub-graph), so multiple destinations read and write the same instance without any cross-Activity plumbing.
- Back stack. managed entirely by the NavController inside the single Activity, giving one consistent back and up behavior instead of reconciling the OS task back stack with N separate Activity stacks.

## 6. ASCII structure diagram

```
  +----------------------------------------------------+
  |                  Host Activity                     |
  |  +------------------------------------------------+ |
  |  |              NavHost / NavController            | |
  |  |                                                 | |
  |  |   +----------+   action   +----------+          | |
  |  |   |  Screen  |----------->|  Screen  |          | |
  |  |   |    A     |            |    B     |          | |
  |  |   +----------+<-----------+----------+          | |
  |  |        |          back          |                | |
  |  |        v                        v                | |
  |  |   scoped ViewModel (shared across A and B)       | |
  |  +------------------------------------------------+ |
  +----------------------------------------------------+
```

## 7. Dynamics

1. The system launches the Host Activity, which creates its single window and lifecycle, and inflates a NavHost pointing at the app's navigation graph.
2. The NavController resolves the graph's start destination and displays the first screen inside the Host Activity's container.
3. The person triggers a navigation action (tapping a button, following a deep link). the NavController pushes the target destination onto its back stack and swaps the displayed screen, all within the same Activity.
4. Typed arguments travel with the navigation action directly, so the destination receives them without any Bundle serialization step.
5. If the destination reads shared state, it resolves a ViewModel scoped to the navigation graph (or sub-graph), which is the SAME instance a sibling destination may already be observing, so state updates propagate without any cross-Activity messaging.
6. Pressing back pops the NavController's own back stack rather than finishing an Activity, and the Host Activity itself only finishes when the back stack is empty.
7. A deep link resolves directly to the correct destination inside the existing graph, which Google's own Navigation documentation frames as a first-class capability. deep linking implements and handles deep links that take the user directly to a destination (https://developer.android.com/topic/libraries/architecture/navigation).

## 8. Implementation variants

- Fragment-based. the classical Jetpack Navigation setup, where each destination is a Fragment hosted by a NavHostFragment inside the single Activity, still common in Views-based codebases and in apps migrating incrementally.
- Compose-based. destinations are composables registered directly with a Compose NavHost, removing the Fragment layer entirely and letting the whole app be one Activity hosting pure composable functions.
- Hybrid. a Compose NavHost hosting a mix of composable destinations and legacy Fragment destinations (via AndroidView interop), used during an incremental Views-to-Compose migration.
- Multi-graph, multi-module. large apps split the single navigation graph into nested sub-graphs, one per feature module, joined at well-defined entry and exit points, which keeps the single-Activity benefit while still letting feature modules build and test independently.

## 9. Known production uses

- Google's own Navigation component documentation names single-Activity as the recommended default. While it is best practice to have a single activity in your app (https://developer.android.com/guide/navigation/design/activity-destinations), and the Navigation library scopes its NavController and active graph to a single Activity by default.
- The Navigation component's own feature list, type safety, includes support for passing data between destinations with type safety, and ViewModel support, enables scoping a ViewModel to a navigation graph to share UI-related data between the graph's destinations (https://developer.android.com/topic/libraries/architecture/navigation), documents exactly the mechanisms that make single-Activity apps practical for a large app with many screens.
- Google's own sample apps (the Now in Android sample, and multiple official Jetpack Compose codelabs) are built single-Activity by default, and the pattern is the standard starting point for any new Android app scaffolded with current Android Studio templates.

## 10. Consequences

### Benefits

- Passing data between screens is type-safe and direct, with no Bundle serialization and no size-limit crash risk.
- Shared state (a session, a cart, a multi-step form) lives in one graph-scoped ViewModel, readable by every destination that needs it, with no cross-Activity bridging.
- Transitions and shared-element animations work naturally within one window instead of being constrained by Activity-to-Activity animation APIs.
- Deep linking resolves directly to a destination inside the existing graph, with no need for a dedicated Activity per linkable target.

### Costs

- The navigation graph itself becomes a single, potentially large piece of shared configuration that every feature touches, so its structure needs real care in a modularized app.
- Migrating an existing multi-Activity app is nontrivial, since Activity lifecycle assumptions baked into old screens (process death handling, Intent-based communication) need to be reworked around the NavController's model.
- A handful of Android APIs genuinely require a standalone Activity (widget configuration, certain launcher shortcuts), so a real app is rarely 100 percent single-Activity in practice, and that boundary needs to be drawn deliberately.

## 11. Failure modes and misuse

- Graph-scoped ViewModel leaks. a ViewModel scoped too broadly (to the whole graph instead of a feature sub-graph) outlives the destinations that genuinely need it and holds stale or unbounded state.
- Deep-link state assumption bugs. a destination reached via deep link assumes prior destinations already ran and set up state they normally would have, crashing or showing an empty screen when entered directly.
- Back stack mismanagement. manually manipulating the NavController's back stack (popping to an arbitrary destination without using the documented popUpTo semantics) produces inconsistent back and up behavior that differs screen to screen.
- Monolithic navigation graph. every feature adding destinations directly to one flat graph instead of nested sub-graphs, producing a single file that every team edits and that becomes a merge-conflict and coupling hotspot.
- Forced single-Activity where the OS genuinely requires otherwise. bending an app widget configuration screen or a launcher-shortcut target into the main graph when the platform API requires its own Activity, producing a fragile workaround instead of the platform-intended structure.

## 12. Trade-off matrix

| Dimension | Single-Activity | Multi-Activity |
|---|---|---|
| Cross-screen data passing | Type-safe, direct via navigation arguments | Bundle serialization via Intent extras, no compile-time safety |
| Shared state across screens | One graph-scoped ViewModel | Singleton, static field, or a separate store bridging Activities |
| Custom transitions and shared elements | Natural, within one window | Constrained by Activity-to-Activity animation APIs |
| Deep linking | Resolves directly to a destination in the graph | Often needs a dedicated Activity per linkable target |
| Platform APIs requiring a standalone Activity | Still need a small, deliberate exception | Naturally supported, no exception needed |

## 13. Related and incompatible patterns

### Related

- Feature Modules. a single navigation graph composed of nested sub-graphs, one per feature module, lets single-Activity architecture scale to a large, modularized codebase.
- Unidirectional Data Flow (Mobile). state shared through a graph-scoped ViewModel still flows one way, state down, events up, from the ViewModel to every destination that observes it.

### Incompatible with

- None directly, though a screen the OS platform API requires to be its own Activity (an app widget configuration screen) sits outside the single-Activity graph by necessity, as a deliberate, small exception rather than an architectural conflict.

## 14. Refactoring path in and out

### Introducing it

1. Inventory every existing Activity and classify it as a genuine screen (migrate to a destination) or a platform-required standalone Activity (leave as is).
2. Introduce a Host Activity with a NavHost and a navigation graph, and migrate the app's start destination first, verifying the Host Activity's lifecycle and back behavior before moving anything else.
3. Migrate one screen at a time from its own Activity into a Fragment or composable destination, moving its cross-screen data passing from Intent extras to typed navigation arguments as part of the same change.
4. Move state that was previously bridged between Activities (a singleton, a static field) into a properly scoped ViewModel on the navigation graph.
5. Once every migratable screen is a destination, remove the now-unused standalone Activities and their manifest entries.

### Removing it

1. Confirm the app genuinely needs per-screen Activity isolation for a reason the Navigation component cannot express, which is rare in practice.
2. Extract the destination back into its own Activity, replacing navigation arguments with an equivalent typed Intent-extras contract.
3. Move any shared state that lived in a graph-scoped ViewModel into an explicit cross-Activity mechanism (a repository, a persisted store) before deleting the shared ViewModel.

## 15. Testing and verification

- Test navigation actions directly against the NavController using its official testing APIs, asserting the correct destination is reached with the correct arguments, without needing to launch the full Host Activity.
- Test graph-scoped ViewModels in isolation, asserting the state they expose is correct independent of which destination is currently displayed.
- Test deep links explicitly, asserting each documented deep link resolves to its intended destination and that destination renders correctly when entered directly, without assuming prior navigation history.
- Test back stack behavior for every custom popUpTo usage, asserting the resulting stack matches the documented navigation design rather than an assumption.
- Include a process-death and state-restoration test for at least the start destination and one deep destination, since a single long-lived Activity still needs correct SavedStateHandle usage per destination.

## 16. Observability signals

- Track navigation events (destination entered, destination exited) so unexpected navigation loops or dead-end screens surface in product analytics rather than only in manual QA.
- Track crash and ANR (Application Not Responding) rates keyed by destination, since a single Activity means a crash on one destination no longer isolates itself the way a crash confined to a dedicated Activity once did.
- Track deep-link resolution failures (a link that fails to match any destination), which is invisible in normal in-app navigation testing but directly affects marketing and push-notification effectiveness.

## 17. Security and privacy implications

- A graph-scoped ViewModel that holds sensitive data (an auth token, a person's profile) outlives individual destinations, so its scope must be chosen deliberately, cleared on sign-out, and never scoped more broadly than the data's actual lifetime requires.
- Deep links resolving directly into an authenticated destination must re-verify authentication and authorization inside the destination itself, since a link can be constructed to target a screen directly, bypassing whatever gate a normal in-app navigation path would have enforced.
- Because the whole app shares one Activity and one process, a memory-dump or debugging tool attached to that process sees every destination's state at once, so sensitive in-memory data should be cleared promptly rather than left resident in a long-lived, broadly scoped ViewModel.

## Code examples

### Python

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Destination:
    name: str
    args: dict


class NavController:
    def __init__(self, start_destination):
        self._back_stack = [start_destination]
        self._scoped_state = {}

    @property
    def current(self):
        return self._back_stack[-1]

    def navigate(self, destination):
        self._back_stack.append(destination)

    def pop_back_stack(self):
        if len(self._back_stack) > 1:
            self._back_stack.pop()
            return True
        return False

    def scoped_view_model(self, key, factory):
        if key not in self._scoped_state:
            self._scoped_state[key] = factory()
        return self._scoped_state[key]


nav = NavController(start_destination=Destination('home', {}))
nav.navigate(Destination('profile', {'user_id': 482}))
cart = nav.scoped_view_model('cart', lambda: {'items': []})
print('current destination', nav.current.name)
```

### Kotlin

```kotlin
data class Destination(val name: String, val args: Map<String, Any> = emptyMap())

class NavController(startDestination: Destination) {
    private val backStack = mutableListOf(startDestination)
    private val scopedState = mutableMapOf<String, Any>()

    val current: Destination get() = backStack.last()

    fun navigate(destination: Destination) {
        backStack.add(destination)
    }

    fun popBackStack(): Boolean {
        return if (backStack.size > 1) {
            backStack.removeAt(backStack.size - 1)
            true
        } else {
            false
        }
    }

    fun <T : Any> scopedViewModel(key: String, factory: () -> T): T {
        "@Suppress("UNCHECKED_CAST")
        return scopedState.getOrPut(key, factory) as T
    }
}

val nav = NavController(startDestination = Destination("home"))
nav.navigate(Destination("profile", mapOf("userId" to 482)))
val cart = nav.scopedViewModel("cart") { mutableListOf<String>() }
println("current destination " + nav.current.name)
```

### Swift

```swift
struct Destination {
    let name: String
    let args: [String: Any]
}

final class NavController {
    private var backStack: [Destination]
    private var scopedState: [String: Any] = [:]

    init(startDestination: Destination) {
        backStack = [startDestination]
    }

    var current: Destination { backStack.last! }

    func navigate(_ destination: Destination) {
        backStack.append(destination)
    }

    @discardableResult
    func popBackStack() -> Bool {
        guard backStack.count > 1 else { return false }
        backStack.removeLast()
        return true
    }

    func scopedViewModel<T>(key: String, factory: () -> T) -> T {
        if let existing = scopedState[key] as? T {
            return existing
        }
        let created = factory()
        scopedState[key] = created
        return created
    }
}

let nav = NavController(startDestination: Destination(name: "home", args: [:]))
nav.navigate(Destination(name: "profile", args: ["userId": 482]))
let cart = nav.scopedViewModel(key: "cart") { [String]() }
print("current destination " + nav.current.name)
```

## 18. References

- Android Developers, Activity destinations (https://developer.android.com/guide/navigation/design/activity-destinations)
- Android Developers, Navigation component overview (https://developer.android.com/topic/libraries/architecture/navigation)
