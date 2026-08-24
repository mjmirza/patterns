---
name: Redux
slug: redux
family: 13-frontend-ui
category: State Management
aliases: [Redux Store, Predictable State Container]
first_described: "Dan Abramov, 2015"
maturity: canonical
related: [flux, hooks, provider-pattern, signals]
incompatible_with: []
verified: 2026-08-21
---

# Redux

## 1. Name, aliases, and lineage

The canonical name is Redux. Its own documentation defines it
directly. "Redux is a JS library for predictable and maintainable
global state management." The library's copyright notice traces its
origin to Dan Abramov and the Redux documentation authors, beginning
in 2015, roughly a year after Facebook's original Flux announcement.

The alias **Redux Store** names the single, centralized object tree
the library holds all application state in. **Predictable State
Container** is Redux's own long-standing tagline, naming the
guarantee its three core rules exist to provide, a state change is
always predictable and traceable to the action that caused it.

## 2. Problem and context

Flux's original architecture solved unidirectional data flow with
several independent stores, each holding its own slice of state and
its own update logic, which worked but left every application
re-inventing how a store subscribes to the dispatcher, how a store's
change event propagates to views, and how several stores compose
into one coherent picture of application state. Redux solves this by
collapsing Flux's several independent stores into one centralized
store holding the entire application's state as a single object tree,
updated only by pure reducer functions that take the previous state
and a dispatched action and return the next state, with no store-side
mutation and no imperative update logic to write by hand for each
store.

## 3. Forces

The pattern balances the following competing pressures.

- **A single, predictable source of truth.** Favored. The entire
  application's state lives in one object tree, in one store, so
  there is exactly one place to look to understand the application's
  current state at any moment.
- **Pure, testable update logic.** Favored. A reducer is a pure
  function, the previous state and an action in, the next state out,
  with no side effects, making an update trivially testable without
  rendering anything or wiring up a real store.
- **Serialization and time-travel debugging.** Favored. Because state
  is a single, plain object tree updated only through pure functions,
  the entire state history can be recorded, replayed, and inspected,
  a capability Flux's several independent, imperatively updated
  stores did not offer as directly.
- **A rigid, ceremony-heavy update path.** Sacrificed unless a
  toolkit reduces it. Every state change needs an action type, an
  action creator, and a reducer case, a real amount of boilerplate
  the ecosystem eventually addressed with Redux Toolkit, described in
  dimension 8.

## 4. Applicability and non-applicability

Reach for Redux when the following hold.

- An application's state is large, interconnected, and benefits from
  living in one predictable, centrally inspectable place, rather than
  scattered across many independent local or per-component state
  values.
- Traceability, testability, and tooling such as time-travel debugging
  matter enough to justify the action-and-reducer ceremony every state
  change requires.
- The team adopts Redux Toolkit rather than hand-rolling the original,
  more verbose Redux patterns, since Redux Toolkit is now the
  documented standard way to write Redux logic.

Do NOT reach for Redux in these cases, and the reason matters more
than the rule.

- **The application's state is mostly local to individual components
  or a small subtree**, the centralization and action-reducer
  ceremony is not repaid when a framework's own built-in state
  primitive, such as Hooks, already covers the need with far less
  code.
- **A team wants fine-grained update precision on frequently changing
  values**, a single centralized store re-renders its subscribed
  consumers on any relevant state change, sharing the same coarse
  re-render cost Signals were specifically designed to avoid.
- **The team is not prepared to adopt Redux Toolkit**, hand-writing
  the original, more verbose action-type-constant, action-creator,
  and switch-statement-reducer pattern by hand produces noticeably
  more boilerplate than the toolkit's own recommended approach.

## 5. Structure

Redux has three structural parts.

- **The store**, a single object holding the application's entire
  state tree, created once and exposing methods to dispatch an
  action, read the current state, and subscribe to changes.
- **Actions**, plain objects describing what happened, the only
  mechanism by which state can be changed, dispatched to the store.
- **Reducers**, pure functions that take the current state and a
  dispatched action and return the next state, composed together to
  produce the store's overall state shape.

## 6. ASCII structure diagram

```
    View                              (a React component or any UI)
      |
      | user interacts, creates an Action
      v
    Action -----------------> store.dispatch(action)
                                    |
                                    v
                          Root Reducer(state, action)
                                    |
                    +---------------+---------------+
                    |                               |
              userReducer(userState, action)   cartReducer(cartState, action)
                    |                               |
                    v                               v
              next userState                 next cartState
                    |                               |
                    +---------------+---------------+
                                    |
                                    v
                          new combined state tree
                                    |
                                    v
                     store notifies its subscribers
                                    |
                                    v
                          View re-renders with new state
```

## 7. Dynamics

The trace below shows an action dispatched to the store, flowing
through the root reducer, and the resulting state update reaching a
subscribed view.

```
User interaction

CartView's add-to-cart button is clicked
   |-- CartView creates an ADD_ITEM action
   |-- store.dispatch(action) is called

Reducer computes next state

the root reducer receives (currentState, action)
   |-- cartReducer(currentState.cart, action) computes next cart state
   |-- userReducer(currentState.user, action) returns unchanged state,
       since it does not recognize ADD_ITEM
   |-- the root reducer combines both into one new state tree

Store notifies subscribers

store's internal state is replaced with the new state tree
   |-- every subscribed view is notified
   |-- CartView re-renders, reading the updated cart state
   |-- a view subscribed only to user state does not re-render,
       since that slice of state did not change
```

## 8. Implementation variants

**The original, hand-written Redux pattern.** Action type constants,
action-creator functions, and a switch-statement reducer written by
hand, the shape Redux originally documented, now considered verbose
and largely superseded by the toolkit-based approach.

**Redux Toolkit, the standard modern approach.** Redux Toolkit's own
documentation states it directly. "the standard way to write Redux
logic," bundling `createSlice`, which generates action creators and a
reducer together from a single object, `configureStore`, which sets
up sensible defaults, and built-in support for writing what looks
like direct state mutation inside a reducer while Immer, used
internally, produces the correct immutable update.

**Middleware for asynchronous logic.** A layer, such as Redux Thunk
or Redux Saga, inserted into the dispatch pipeline to handle
asynchronous work, a network request completing and then dispatching
a follow-up action, without any reducer needing to handle
asynchronous logic itself, since reducers must stay pure.

**Selectors for derived state.** A function that reads a specific
slice or a computed value out of the store's state tree, often
memoized so a component reading a selector only re-renders when the
specific derived value it depends on actually changes, narrowing the
coarse re-render cost named in the trade-off matrix.

## 9. Known production uses

**Redux's own documentation, describing its core architecture.**
Redux's introduction states directly. "Redux is a JS library for
predictable and maintainable global state management," built on
three explicit rules. a single store holds "the whole global state of
your app," the only way to change state is to "create an action, an
object describing what happened, and dispatch it to the store," and
state updates happen through "pure reducer functions that calculate a
new state based on the old state and the action." Redux
documentation, Getting Started with Redux,
https://redux.js.org/introduction/getting-started, verified
2026-08-21.

**Redux Toolkit, the officially recommended modern implementation.**
Redux Toolkit's own documentation states directly. "The Redux Toolkit
package is intended to be the standard way to write Redux logic," and
that "these tools should be beneficial to all Redux users" across
every experience level, from a first project to an existing,
established codebase, a first-party statement that Redux's original
patterns have been formally superseded by this toolkit as the
recommended production approach. Redux Toolkit documentation, Getting
Started, https://redux-toolkit.js.org/introduction/getting-started,
verified 2026-08-21.

## 10. Consequences

Positive.

- The entire application's state lives in one predictable, centrally
  inspectable object tree, with exactly one place to look to
  understand the application's current state at any moment.
- Reducers are pure functions, trivially testable by calling them
  directly with a state and an action and asserting the result, with
  no need to render anything or wire up a real store.
- The single, serializable state tree enables tooling that would be
  harder to build on Flux's several independent stores, most notably
  time-travel debugging and full state-history replay.

Negative.

- The original, hand-written Redux pattern needs an action type, an
  action creator, and a reducer case for every distinct kind of state
  change, a real amount of boilerplate the ecosystem addressed with
  Redux Toolkit rather than eliminating outright.
- A single centralized store re-renders its subscribed consumers on
  any relevant state change by default, sharing the same coarse
  re-render cost as other whole-store or whole-component-re-run
  approaches, unless narrowed with memoized selectors.
- Asynchronous logic cannot live inside a reducer, since a reducer
  must stay pure, needing an additional middleware layer, such as
  Redux Thunk or Redux Saga, for any operation that is not a
  synchronous state computation.

## 11. Failure modes and misuse

**Mutating state directly inside a reducer instead of returning a new
state object.** Symptom. State updates behave unpredictably,
sometimes appearing to work and sometimes silently failing to trigger
a re-render, depending on how the surrounding code compares state for
equality. Cause. The reducer mutated the existing state object in
place rather than returning a new one, and Redux's default equality
check compares by reference, so a mutated-in-place object that keeps
the same reference is indistinguishable from unchanged state. Fix.
Always return a new state object from a reducer, or use Redux
Toolkit's `createSlice`, which uses Immer internally to let
mutation-looking code produce a correct, genuinely new state object.

**Putting asynchronous logic directly inside a reducer.** Symptom.
The reducer either fails to compile against Redux's expectations or
produces inconsistent, timing-dependent state, since two dispatches
of the same action with the same state can now produce different
results depending on when an asynchronous operation resolves. Cause.
A reducer must be a pure function, returning the same output for the
same input every time, and an asynchronous operation, or any other
side effect, breaks that guarantee. Fix. Move the asynchronous logic
into a middleware layer, such as a thunk or a saga, which dispatches
the resulting action once the asynchronous work completes, keeping
every reducer itself pure.

**Storing every piece of application state in Redux, including state
that is genuinely local to one component.** Symptom. Simple,
component-scoped state, such as whether a dropdown is open, is
threaded through action types, action creators, and a reducer,
producing unnecessary boilerplate and coupling that component's
trivial UI state to the global store. Cause. Defaulting to Redux for
all state without considering whether a specific piece of state is
genuinely shared or is purely local. Fix. Keep component-local state
in the framework's own local state primitive, such as `useState`,
reserving Redux for state that genuinely needs to be shared,
traceable, or centrally inspectable.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Redux (with Redux Toolkit) | Flux (original) | Hooks (useState/useReducer) | The Provider Pattern |
|---|---|---|---|---|
| Predictability and traceability | High, one store, pure reducers, a full action history | High, but spread across several independent stores | Low, a state setter can be called from anywhere | Low, a context value can change for any reason |
| Boilerplate per distinct state change | Moderate with Redux Toolkit, high without it | High, an action plus explicit handling in each store | Low, a plain state update | Low, a plain state update |
| Time-travel debugging and tooling | Strong, enabled by the single serializable state tree | Weaker, harder across several independent stores | Not applicable, no dedicated tooling | Not applicable, no dedicated tooling |
| Current maintenance and adoption status | Actively maintained, the dominant Flux successor | Archived, successor recommended | Actively maintained, a core framework feature | Actively maintained, a core framework feature |
| Fit for state genuinely local to a component | Weak, unnecessary ceremony for trivial local state | Weak, the same ceremony problem | Strong | Weak, coarse re-render cost even for a small value |

Reading of the table. Redux wins when an application's state is
large, interconnected, and benefits from centralization,
predictability, and tooling enough to justify its ceremony, now
substantially reduced by Redux Toolkit relative to the original
hand-written pattern. Hooks remain the right default for state
genuinely local to a component. Flux's own ideas live on almost
entirely inside Redux, which is why Redux, not the original Flux
library, is the pattern most teams reach for today.

## 13. Related and incompatible patterns

- **Flux.** The architecture Redux directly descends from, collapsing
  Flux's several independent stores into one centralized store while
  keeping the same unidirectional action-to-update-to-view flow.
- **Hooks.** The default state primitive for state genuinely local to
  a component, and, via `useSelector` and `useDispatch` in
  react-redux, the mechanism modern Redux code uses to read from and
  dispatch to the store from a function component.
- **Provider Pattern.** The mechanism react-redux's own `<Provider>`
  component uses internally to make the Redux store available to any
  nested component, without threading the store through every
  intermediate component's props.
- **Signals.** A different response to a related problem,
  prioritizing fine-grained update precision over Redux's centralized,
  traceable, whole-store update model, and generally not combined
  with Redux directly.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an application whose state has grown large
and interconnected enough that scattered local state or an
ad hoc shared-state mechanism has become hard to trace.

1. Confirm the application's state genuinely benefits from
   centralization, predictability, and tooling before adopting the
   ceremony.
2. Set up a store using Redux Toolkit's `configureStore`, rather than
   the original, more verbose manual store setup.
3. Define one or more slices with `createSlice`, each responsible for
   one logical piece of state, generating their action creators and
   reducer together.
4. Migrate the state that genuinely needs to be shared or traceable
   into the store, connecting consuming components via `useSelector`
   and `useDispatch`, and leave state genuinely local to one
   component where it already is.
5. Add a test asserting each reducer's state updates correctly for
   its defined actions, independent of any specific view.

Removing the pattern when it stops earning its place, most relevant
when an application's state has genuinely simplified, or a
significant portion of what lives in the store is actually local to
one component.

1. Confirm the centralization and traceability guarantee is
   genuinely no longer needed for the specific state in question,
   rather than assuming so without review.
2. Migrate simple, locally scoped state back to the framework's
   native state primitive, keeping its external interface unchanged
   so consumers require minimal changes.
3. Remove the corresponding slice from the store only after every
   consumer has migrated off it.

## 15. Testing and verification

Easier because of the pattern.

- A reducer is a pure function, testable directly by calling it with
  a specific previous state and action and asserting the returned
  next state, with no need to render anything or wire up a real
  store.
- Because every state change traces to a single dispatched action, a
  test can simulate an entire user interaction as a sequence of
  actions dispatched to a real store instance and assert the final
  state, without rendering any actual UI.

Harder because of the pattern.

- Testing the full, real integration, a component dispatching an
  action and re-rendering in response to the resulting store change,
  needs wiring together the store, the Provider, and the component,
  rather than testing any one piece in isolation.
- The first failure mode in dimension 11, a reducer mutating state
  directly instead of returning a new object, is invisible to a test
  that only checks the reducer's returned value looks correct on the
  surface, since the actual bug is about reference equality, not the
  value's contents.

Techniques that apply.

- **Isolated reducer test.** Call a reducer directly with a specific
  previous state and action, and assert the returned next state,
  independent of any store or view.
- **Action-sequence test.** Dispatch a sequence of actions to a real
  store instance representing a user interaction, and assert the
  final state, entirely independent of any rendered UI.
- **Full-integration test.** Render a component wrapped in a real
  Provider and store, trigger the interaction that dispatches an
  action, and assert the component re-renders correctly with the
  resulting state.
- **Immutability regression test.** Assert a reducer's output is a
  genuinely new object reference distinct from its input state,
  guarding against the first failure mode in dimension 11.

## 16. Observability signals

Redux is a source-level state-management architecture with no
independent runtime footprint of its own beyond the dispatching and
reducer computation it already performs, and inventing a dedicated
production signal purely for the pattern would be dishonest. Two
things are worth watching in a codebase that uses it.

What to record.

- The volume and type of dispatched actions over time, since Redux's
  own action stream is a natural, already-available place to capture
  a complete, ordered history of every state change an application
  has made.
- The re-render frequency of components subscribed to the store
  relative to how often the specific slice of state they actually
  read changes, since a mismatch signals a selector that is not
  narrowly scoped or not memoized.

A healthy state. Every state change corresponds to exactly one
dispatched action captured in the action history, and components
re-render in proportion to how often the specific state they read
actually changes.

A failing state. A component re-rendering far more often than the
specific state it reads actually changes, pointing at an unmemoized
or overly broad selector, or a state change with no corresponding
action in the dispatch history, pointing at a direct mutation
bypassing the store entirely.

## 17. Security and privacy implications

Redux is close to neutral for security, being a state-management
architecture rather than a data-handling one, and inventing a
dedicated attack surface here would be dishonest. One practical
implication is worth naming.

**Persisting or logging the entire Redux state tree or action
history, a common and useful debugging practice, can capture
sensitive data if any slice of state or any action payload carries
it.** Because Redux's single, serializable state tree and dispatched
action stream are exactly what makes tooling such as time-travel
debugging and remote logging so convenient, a team adopting such
tooling should confirm no piece of state or any action payload
carries a password, a token, or other sensitive data before
persisting or transmitting it elsewhere. this is not different from
any other logging or persistence surface in principle, but it is
worth naming explicitly, since Redux's very serializability, the
property that makes it so tool-friendly, is exactly what makes an
accidental leak of sensitive state easy to produce.

## 18. References

1. Redux documentation. "Getting Started with Redux".
   https://redux.js.org/introduction/getting-started
   Verified 2026-08-21. Source of the defining sentence and the three
   core rules described in dimension 9.
2. Redux Toolkit documentation. "Getting Started".
   https://redux-toolkit.js.org/introduction/getting-started
   Verified 2026-08-21. Source for the production-recommendation claim
   in dimension 9 and the standard-approach status described in
   dimension 8.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models the classic
store-action-reducer shape the way Redux and Redux Toolkit structure
it, kept free of JSX and any specific framework's package so the
sample compiles as plain TypeScript. Python shows the same
conceptual split using a minimal, framework-agnostic store class with
a pure reducer function, since Python has no single dominant
Redux-shaped UI framework the way TypeScript has React. Swift shows
the pattern using a minimal unidirectional-flow store with a pure
reduce function, closely analogous to the Redux-inspired state
containers used in several SwiftUI architectures. Java, Go, and Rust
are omitted, since none has a dominant, idiomatic UI-component
framework this specifically frontend pattern maps to as directly as
TypeScript and Swift do.

### TypeScript

```typescript
interface State {
  count: number;
}

interface Action {
  type: string;
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "INCREMENT":
      return { count: state.count + 1 };
    default:
      return state;
  }
}

class Store {
  private state: State;
  private listeners: (() => void)[] = [];

  constructor(initial: State) {
    this.state = initial;
  }

  getState(): State {
    return this.state;
  }

  dispatch(action: Action): void {
    this.state = reducer(this.state, action);
    this.listeners.forEach((listener) => listener());
  }

  subscribe(listener: () => void): void {
    this.listeners.push(listener);
  }
}

const store = new Store({ count: 0 });

store.subscribe(() => {
  console.log("count is now " + store.getState().count);
});

store.dispatch({ type: "INCREMENT" });
store.dispatch({ type: "INCREMENT" });
```

### Python

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class State:
    count: int


@dataclass
class Action:
    type: str


def reducer(state: State, action: Action) -> State:
    if action.type == "INCREMENT":
        return State(count=state.count + 1)
    return state


class Store:
    def __init__(self, initial: State) -> None:
        self._state = initial
        self._listeners: list[Callable[[], None]] = []

    def get_state(self) -> State:
        return self._state

    def dispatch(self, action: Action) -> None:
        self._state = reducer(self._state, action)
        for listener in self._listeners:
            listener()

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)


if __name__ == "__main__":
    store = Store(State(count=0))

    def on_change() -> None:
        print(f"count is now {store.get_state().count}")

    store.subscribe(on_change)
    store.dispatch(Action(type="INCREMENT"))
    store.dispatch(Action(type="INCREMENT"))
```

### Swift

```swift
struct AppState {
    var count: Int = 0
}

struct Action {
    let type: String
}

func reduce(state: AppState, action: Action) -> AppState {
    var next = state
    if action.type == "INCREMENT" {
        next.count += 1
    }
    return next
}

final class Store {
    private(set) var state: AppState
    private var listeners: [() -> Void] = []

    init(initial: AppState) {
        state = initial
    }

    func dispatch(_ action: Action) {
        state = reduce(state: state, action: action)
        listeners.forEach { $0() }
    }

    func subscribe(_ listener: @escaping () -> Void) {
        listeners.append(listener)
    }
}

let store = Store(initial: AppState())

store.subscribe {
    print("count is now " + String(store.state.count))
}

store.dispatch(Action(type: "INCREMENT"))
store.dispatch(Action(type: "INCREMENT"))
```
