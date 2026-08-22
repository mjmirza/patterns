---
name: Redux for Mobile
slug: redux-for-mobile
family: 27-mobile-architecture
category: Behavioral
aliases: [ReSwift Pattern, Native Redux, Mobile Redux Store]
first_described: 'Dan Abramov, Redux, 2015, adapted for mobile by ReSwift and similar libraries'
maturity: established
related: [unidirectional-data-flow, mvvm-c]
incompatible_with: []
verified: 2026-08-22
---

# Redux for Mobile

## 1. Name, aliases, and lineage

Redux for Mobile. Also called the ReSwift Pattern, Native Redux, or a Mobile Redux Store. The name marks a deliberate port. taking the Redux pattern, originally a JavaScript library for web applications, and reimplementing its three governing rules directly in Swift or Kotlin for iOS and Android, rather than running the Redux.js library itself inside a native app.

The lineage starts with Dan Abramov's Redux, whose own documentation states the pattern as three principles. The global state of your application is stored in an object tree within a single store. The only way to change the state is to emit an action, an object describing what happened. To specify how the state tree is transformed by actions, you write pure reducers (https://redux.js.org/understanding/thinking-in-redux/three-principles). Native mobile ports followed once teams wanted the same predictability on iOS and Android. ReSwift describes itself as a Redux-like implementation of the unidirectional data flow architecture in Swift (https://github.com/ReSwift/ReSwift), and comparable Kotlin state-container libraries brought the same shape to Android.

## 2. Problem and context

A mobile app's state can be scattered across many ViewModels, view controllers, and singletons, each owning a private slice and mutating it directly. When several screens need to react to the same piece of state, or when a bug needs to be traced back to exactly which mutation caused an incorrect value, an app with many independent, mutable state owners makes both jobs hard. there is no single place to look, and no way to replay the sequence of changes that produced a given state.

Redux, and its mobile ports, answer this by making every state change go through one, and only one, path. an action describing what happened is dispatched, a pure reducer function computes the entire next state from the previous state and that action, and the store is the single, immutable source of truth every screen reads from. This trades the flexibility of many independent mutation points for a strict, traceable, and highly testable flow, which matters most in apps whose state is genuinely shared and complex across many screens.

## 3. Forces

- Multiple screens frequently need to react to the same shared state, and keeping N independent copies in sync is error-prone.
- Debugging a wrong state value is far easier when every change is an explicit, named action processed by a pure function, rather than a mutation buried inside a ViewModel method.
- Reducers must stay pure (no side effects, no mutation of their input) for the pattern's testability and predictability guarantees to actually hold.
- A single global store adds real ceremony (action types, action creators, reducer composition) that a small, simple screen does not need.
- Native mobile UI frameworks were not designed around a single global store, so connecting a store to a SwiftUI view or a Composable requires an explicit binding layer the web version does not need in the same way.

## 4. Applicability and non-applicability

Use Redux for Mobile when app state is genuinely shared across many screens, when a team wants every state change to be traceable through named, loggable actions, or when time-travel debugging and highly deterministic unit tests (a reducer is a pure function of state and action, so its output is trivially assertable) are a real priority. It suits complex, long-lived apps where the cost of an untraceable state bug is high.

Skip it for a small app, a screen with genuinely local and simple state, or a team that already has a lighter pattern (an MVVM ViewModel with its own state, or the platform's native state-holder APIs) that solves the same problem with less ceremony. Applying a single global store to state that only one screen ever touches produces unnecessary indirection for no real benefit.

## 5. Structure

- Store. the single, app-wide holder of the current state tree, exposing a way to read the current state, dispatch actions, and subscribe to state changes.
- State. one immutable tree describing the app's entire relevant state at a point in time. a new state tree is produced on every change, never mutated in place.
- Action. a plain, named description of something that happened (a person tapped a button, a network request finished), carrying only the data needed to describe that event.
- Reducer. a pure function taking the current state and an action and returning the next state, with no side effects and no dependency on anything outside its two inputs.
- Subscriber or connector. the binding layer (a ViewModel observing the store, or a view subscribing directly) that maps the store's state into what a particular screen renders, and forwards person actions back as dispatched actions.

## 6. ASCII structure diagram

```
   person action (tap, swipe, network callback)
        |
        v
   dispatch(Action)
        |
        v
  +----------------------------------+
  |              Store               |
  |  +-----------------------------+  |
  |  |     Reducer(state, action)   |  |
  |  |     -> next State            |  |
  |  +-----------------------------+  |
  +----------------------------------+
        |
        v  notifies subscribers
  +----------------------------------+
  |   Subscriber / Connector          |
  |   maps State -> screen render      |
  +----------------------------------+
```

## 7. Dynamics

1. A person interacts with a screen (a tap, a swipe) or an async event completes (a network response), and the app constructs an Action describing what happened.
2. The Action is dispatched to the Store, which is the only entry point for any state change in the entire app.
3. The Store passes the current State and the Action to the Reducer, which computes and returns an entirely new State tree, per Redux's own core rule. to specify how the state tree is transformed by actions, you write pure reducers (https://redux.js.org/understanding/thinking-in-redux/three-principles).
4. The Store replaces its current State with the Reducer's returned value and notifies every Subscriber that the state has changed.
5. Each Subscriber reads the new State, maps the relevant slice into whatever its screen needs, and the UI re-renders to reflect it.
6. If a person action requires new data (a network call), that side effect runs outside the Reducer (in a middleware, an effect handler, or the dispatching code itself), and its result is fed back in as a new Action once it completes, keeping the Reducer itself pure.

## 8. Implementation variants

- ReSwift-style native port. a Swift library reimplementing the Redux shape directly, described on its own README as a Redux-like implementation of the unidirectional data flow architecture in Swift (https://github.com/ReSwift/ReSwift), with Store, Action, State, and Reducer as first-class Swift types.
- Kotlin state-container libraries. Android-native equivalents that adopt the same single-store, pure-reducer shape idiomatically in Kotlin, commonly paired with coroutines or Flow for the subscription mechanism.
- Hand-rolled minimal Redux. a small, app-specific implementation limited to the Store, Action, and Reducer contract with no external dependency, common in teams that want the pattern's discipline without adopting a full third-party library.
- Redux plus middleware. an extended variant where a middleware layer intercepts dispatched actions before they reach the reducer, used for logging, analytics, or coordinating async side effects in a consistent, centralized place.

## 9. Known production uses

- Redux's own documentation states the three founding principles directly. the global state of your application is stored in an object tree within a single store (https://redux.js.org/understanding/thinking-in-redux/three-principles), and those same three principles are what every native mobile port, including ReSwift, deliberately reproduces.
- ReSwift, described as a Redux-like implementation of the unidirectional data flow architecture in Swift (https://github.com/ReSwift/ReSwift), has been adopted across iOS apps that want Redux's predictability and traceability without depending on a JavaScript runtime.
- Larger, long-lived native mobile apps with genuinely complex, widely-shared state (banking, enterprise, and multi-screen dashboard apps) commonly build or adopt a Redux-shaped store specifically for the traceable debugging and deterministic testing it gives their most state-heavy screens.

## 10. Consequences

### Benefits

- Every state change is traceable to a single, named Action, which makes debugging a wrong state value far more direct than hunting through scattered mutation sites.
- Reducers being pure functions makes them trivially and exhaustively unit testable, since their entire behavior is a function of two plain inputs.
- A single source of truth removes an entire class of bug where two screens hold subtly different copies of what should be the same state.
- Middleware gives one, centralized place to add cross-cutting concerns (logging, analytics, undo) without touching every feature that dispatches an action.

### Costs

- The pattern adds real ceremony (action types, action creators, reducer composition) that a simple, locally-scoped screen does not need.
- Native UI frameworks were not designed around a single external store, so the binding layer connecting the store to SwiftUI or Compose is extra code the pattern itself does not provide.
- A large, single global state tree can become a coupling hazard if its shape is not deliberately partitioned, since many unrelated features end up reading and writing the same object.

## 11. Failure modes and misuse

- Impure reducers. a reducer that performs a network call, mutates its input state directly, or reads external mutable state breaks every guarantee (testability, replayability, predictability) the pattern exists to provide.
- Action explosion. an action type created for every trivial UI detail instead of a real domain event, producing hundreds of near-duplicate actions that add ceremony with no corresponding clarity.
- Monolithic state tree. one giant, undivided state object that every feature reads and writes, turning the store itself into a coupling hazard the pattern was meant to avoid.
- Side effects leaking into the reducer. an async call or a mutation smuggled into what should be a pure function, silently breaking determinism in a way unit tests may not catch until it manifests as a real bug.
- Over-subscription. a screen subscribing to the entire state tree instead of the specific slice it needs, causing unnecessary re-renders on every unrelated state change.

## 12. Trade-off matrix

| Dimension | Redux for Mobile | A local ViewModel-owned state |
|---|---|---|
| Traceability of state changes | High, every change is a named action | Lower, changes are direct mutations |
| Testability | High, reducers are pure functions | Moderate, depends on ViewModel structure |
| Ceremony for a simple screen | Higher, action and reducer boilerplate | Lower, direct state assignment |
| Cross-screen shared state | Well suited, single source of truth | Requires manual synchronization |
| Native UI framework fit | Requires an explicit binding layer | Native, no extra binding needed |

## 13. Related and incompatible patterns

### Related

- Unidirectional Data Flow (Mobile). Redux for Mobile is one concrete, named implementation of the broader state-down, events-up unidirectional flow that pattern describes generally.
- MVVM-C (Model-View-ViewModel-Coordinator). a Redux store commonly sits behind a ViewModel in an MVVM-C app, with the ViewModel as the subscriber and connector layer between the store and the view.

### Incompatible with

- None directly, though adopting Redux for Mobile alongside an unrelated, independent state-management library for the same slice of state reintroduces the exact multiple-sources-of-truth problem the pattern exists to remove.

## 14. Refactoring path in and out

### Introducing it

1. Identify the state that is genuinely shared across multiple screens and would benefit from a single source of truth, rather than migrating every screen's state indiscriminately.
2. Define the initial State shape and the first set of Action types for that shared state, deliberately partitioned rather than one giant object.
3. Write the Reducer as a pure function covering the identified actions, with unit tests for every action before wiring anything to the UI.
4. Introduce the Store and connect the first screen's ViewModel as a subscriber, replacing its own local mutable copy of that state.
5. Migrate remaining screens that touch the same shared state one at a time, verifying each against the reducer's tests before moving to the next.

### Removing it

1. Confirm the previously shared state has become simple enough, or localized enough, that a single global store no longer earns its ceremony.
2. Migrate each subscribing screen back to owning its own local state, one screen at a time, verifying behavior is unchanged at each step.
3. Delete the Store, Reducer, and Action types once no subscriber depends on them.

## 15. Testing and verification

- Unit-test every Reducer directly, asserting the exact next state for every action and every distinct prior state, with no mocking required since a pure function needs none.
- Assert Reducer purity explicitly where feasible. calling a reducer twice with the same inputs must produce equal outputs, and the original state object must remain unmutated.
- Test the Store's subscription mechanism, asserting every subscriber is notified exactly once per dispatched action that changes relevant state.
- Test any middleware in isolation from the reducers it wraps, asserting it forwards, blocks, or transforms actions exactly as documented.
- Add an integration test that dispatches a realistic sequence of actions and asserts the final state matches the expected outcome of that full sequence, not only individual actions in isolation.

## 16. Observability signals

- Log every dispatched action with a timestamp, which gives a complete, replayable history of how the app reached its current state, invaluable for reproducing a hard-to-catch bug report.
- Track state tree size and subscriber count over time, since both growing unbounded are early signals the store is becoming the monolithic, over-coupled state object the pattern is meant to avoid.
- Track re-render counts per subscriber, since a spike often means a screen is subscribing to more of the state tree than it actually needs.

## 17. Security and privacy implications

- A single global state tree is an attractive target for a debugging or memory-inspection tool to dump in one place, so sensitive data (an auth token, a person's profile) held in the store should be cleared promptly on sign-out rather than left resident indefinitely.
- Action logging, valuable for debugging, must exclude or redact sensitive payload fields before it is written to any log or analytics pipeline, since a logged action is effectively a permanent, searchable record of what state changed and with what data.
- Because every state change flows through one traceable path, the store is also a natural place to enforce a consistent authorization check before a sensitive action is allowed to reach its reducer, rather than trusting every dispatch site to have checked independently.

## Code examples

### Python

```python
from dataclasses import dataclass, replace
from typing import Callable, List


@dataclass(frozen=True)
class AppState:
    counter: int
    last_action: str


@dataclass(frozen=True)
class Action:
    kind: str
    payload: int = 0


def reducer(state, action):
    if action.kind == 'increment':
        return replace(state, counter=state.counter + action.payload, last_action=action.kind)
    return replace(state, last_action=action.kind)


class Store:
    def __init__(self, initial_state, reducer_fn):
        self._state = initial_state
        self._reducer = reducer_fn
        self._subscribers = []

    @property
    def state(self):
        return self._state

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def dispatch(self, action):
        self._state = self._reducer(self._state, action)
        for callback in self._subscribers:
            callback(self._state)


store = Store(AppState(counter=0, last_action='init'), reducer)
store.subscribe(lambda s: print('state now', s.counter))
store.dispatch(Action(kind='increment', payload=5))
```

### Kotlin

```kotlin
data class AppState(val counter: Int, val lastAction: String)

sealed class Action {
    data class Increment(val amount: Int) : Action()
    object Reset : Action()
}

fun reducer(state: AppState, action: Action): AppState = when (action) {
    is Action.Increment -> state.copy(counter = state.counter + action.amount, lastAction = "increment")
    is Action.Reset -> state.copy(counter = 0, lastAction = "reset")
}

class Store(initialState: AppState, private val reducerFn: (AppState, Action) -> AppState) {
    var state: AppState = initialState
        private set
    private val subscribers = mutableListOf<(AppState) -> Unit>()

    fun subscribe(callback: (AppState) -> Unit) {
        subscribers.add(callback)
    }

    fun dispatch(action: Action) {
        state = reducerFn(state, action)
        subscribers.forEach { it(state) }
    }
}

val store = Store(AppState(counter = 0, lastAction = "init"), ::reducer)
store.subscribe { println("state now " + it.counter) }
store.dispatch(Action.Increment(amount = 5))
```

### Swift

```swift
struct AppState {
    var counter: Int
    var lastAction: String
}

enum Action {
    case increment(Int)
    case reset
}

func reducer(state: AppState, action: Action) -> AppState {
    var next = state
    switch action {
    case .increment(let amount):
        next.counter += amount
        next.lastAction = "increment"
    case .reset:
        next.counter = 0
        next.lastAction = "reset"
    }
    return next
}

final class Store {
    private(set) var state: AppState
    private let reducerFn: (AppState, Action) -> AppState
    private var subscribers: [(AppState) -> Void] = []

    init(initialState: AppState, reducerFn: @escaping (AppState, Action) -> AppState) {
        state = initialState
        self.reducerFn = reducerFn
    }

    func subscribe(_ callback: @escaping (AppState) -> Void) {
        subscribers.append(callback)
    }

    func dispatch(_ action: Action) {
        state = reducerFn(state, action)
        subscribers.forEach { $0(state) }
    }
}

let store = Store(initialState: AppState(counter: 0, lastAction: "init"), reducerFn: reducer)
store.subscribe { print("state now " + String($0.counter)) }
store.dispatch(.increment(5))
```

## 18. References

- Redux documentation, The Three Principles (https://redux.js.org/understanding/thinking-in-redux/three-principles)
- ReSwift, GitHub repository README (https://github.com/ReSwift/ReSwift)
