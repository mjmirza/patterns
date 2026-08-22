---
name: Reducer Hook
slug: reducer-hook
family: 13-frontend-ui
category: State Management
aliases: [useReducer, State Reducer Pattern]
first_described: "React documentation, useReducer"
maturity: canonical
related: [headless-component, context-selector, flux, redux]
incompatible_with: []
verified: 2026-08-21
---

# Reducer Hook

## 1. Name, aliases, and lineage

The canonical name is Reducer Hook, a state-management technique
where a component's state updates are consolidated into a single
function outside the component, rather than scattered across many
individual event handlers. React's own documentation states the
underlying idea directly. "Components with many state updates spread
across many event handlers can get overwhelming. For these cases, you
can consolidate all the state update logic outside your component in
a single function, called a reducer."

The alias **useReducer** names React's own specific hook
implementation of the pattern, the mechanism most developers reach
for first. **State Reducer Pattern** names the broader technique
independent of any specific framework's hook syntax, since the same
consolidate-updates-into-one-function idea predates and extends
beyond React's own hook.

## 2. Problem and context

A component whose state updates are spread across many individual
event handlers, each directly calling its own state setter, becomes
hard to reason about as the number of related updates grows, since
understanding how the state can change means reading every handler
individually rather than reading one place that governs every
transition. React's own documentation names the debugging cost of
this scattered approach directly, that when a bug with individually
scattered state setters occurs, it is difficult to tell where the
state was set incorrectly and why. A reducer solves this by
collecting every possible state transition into a single function,
so the answer to "how can this state change" is always found in one
place, and the answer to "why did it change this way" is always found
in the specific action that was dispatched to trigger it.

## 3. Forces

The pattern balances the following competing pressures.

- **Centralized, auditable state transitions.** Favored. React's own
  documentation states the debugging benefit directly. "With
  useReducer, you can add a console log into your reducer to see
  every state update and why it happened," since every transition
  passes through the same single function.
- **Upfront code for simple cases.** Sacrificed. React's own
  documentation is candid about this trade-off. "Generally, useState
  requires less code upfront," since a reducer needs both a reducer
  function and dispatched actions, more structure than a direct state
  setter call for a genuinely simple update.
- **Separation of what happened from how state responds.** Favored.
  React's own documentation names this separation directly. "useReducer
  lets you cleanly separate the how of update logic from the what
  happened of event handlers," letting an event handler simply
  describe what occurred without also encoding the resulting state
  transformation.
- **Reduced duplication across many similar updates.** Favored,
  conditionally. React's own documentation notes that a reducer "can
  help cut down code if many event handlers modify state in a similar
  way," consolidating that shared logic into the one reducer function
  rather than repeating it per handler.

## 4. Applicability and non-applicability

Reach for a Reducer Hook when the following hold.

- The component genuinely has many state updates spread across many
  event handlers, matching the exact case React's own documentation
  names as the pattern's origin problem.
- Bugs from incorrect state updates recur often enough that React's
  own recommendation applies directly. "We recommend using a reducer
  if you often encounter bugs due to incorrect state updates in some
  component, and want to introduce more structure to its code."
- Many event handlers modify related state in a similar way, so
  consolidating that shared update logic into one reducer function
  reduces real duplication rather than adding structure for its own
  sake.

Do NOT reach for a Reducer Hook in these cases, and the reason
matters more than the rule.

- **The component has only a small number of simple, independent state
  updates**, React's own documentation states plainly that "useState
  requires less code upfront," and adding a reducer's extra structure
  to a genuinely simple case trades that lower upfront cost for
  centralization the case does not need.
- **State updates are not actually interrelated**, a reducer's value
  comes specifically from consolidating related transitions into one
  place, and applying it to state that genuinely does not interact
  gains little over several independent, simple state values.
- **The team has not actually experienced the debugging or
  readability pain the pattern addresses**, reaching for a reducer
  speculatively, before the scattered-handler problem has genuinely
  materialized, adds structure ahead of a real, felt need.

## 5. Structure

A Reducer Hook has three structural parts.

- **The state**, the current value the reducer manages, read by the
  component to render.
- **The reducer function**, a single function taking the current
  state and a dispatched action, returning the new state, containing
  every possible state transition the component supports.
- **The dispatch function**, the mechanism a component's event
  handlers call to describe what happened, without directly computing
  or setting the resulting state themselves.

## 6. ASCII structure diagram

```
  Component

  +----------------------------------------------------------+
  |  event handler A -- dispatch({ type: "increment" })         |
  |  event handler B -- dispatch({ type: "reset" })              |
  +----------------------------------------------------------+
                      |
                      v
              +--------------------+
              |  reducer function     |
              |  (state, action) =>    |
              |     new state           |
              +--------------------+
                      |
                      v
              +--------------------+
              |  current state         |
              |  read by the           |
              |  component to render    |
              +--------------------+
```

## 7. Dynamics

The trace below shows two event handlers dispatching actions that
both route through the same reducer function.

```
User triggers event handler A

event handler A calls dispatch with an "increment" action
   |-- the reducer function receives the current state and the
       increment action
   |-- the reducer computes and returns the new, incremented state
   |-- the component re-renders with the new state

User triggers event handler B

event handler B calls dispatch with a "reset" action
   |-- the reducer function receives the current state and the
       reset action
   |-- the reducer computes and returns the new, reset state
   |-- the component re-renders with the new state

Debugging a state transition

a developer adds a log inside the reducer function
   |-- every dispatched action, from either handler, passes through
       that single logged point
   |-- the developer can see every state update and the specific
       action that caused it, in one place, rather than tracing
       through each handler individually
```

## 8. Implementation variants

**Framework-native reducer hook.** React's own `useReducer` hook, the
most direct implementation, pairing a reducer function with a
component's local state and returning a dispatch function to trigger
transitions.

**Reducer paired with context.** A reducer's state and dispatch
function are shared through a context provider, letting components
deep in a tree dispatch actions and read the resulting state without
prop drilling the reducer's own values down manually.

**Reducer composition.** Several smaller reducer functions, each
handling a distinct slice of state, are combined into one larger
reducer, letting a large, complex state shape stay organized as
several focused, individually understandable functions.

**Middleware-extended reducers.** A dispatch call passes through
additional functions before reaching the reducer itself, letting a
team add logging, asynchronous side effects, or other cross-cutting
behavior without modifying the reducer function's own pure state
transition logic.

## 9. Known production uses

**React's own documentation, naming the origin problem and the
solution.** React states the problem directly. "Components with many
state updates spread across many event handlers can get overwhelming.
For these cases, you can consolidate all the state update logic
outside your component in a single function, called a reducer,"
recommending it specifically "if you often encounter bugs due to
incorrect state updates in some component, and want to introduce more
structure to its code." React, "Extracting State Logic into a
Reducer," https://react.dev/learn/extracting-state-logic-into-a-reducer,
verified 2026-08-21.

**React's own documentation, on the useReducer hook itself.** React
states the hook's definition directly. "useReducer is a React Hook
that lets you add a reducer to your component," noting that it "lets
you move the state update logic from event handlers into a single
function outside of your component." React, "useReducer,"
https://react.dev/reference/react/useReducer, verified 2026-08-21.

## 10. Consequences

Positive.

- Every possible state transition lives in one auditable place, so
  debugging an incorrect update means reading one function rather
  than tracing through every event handler that might have caused it.
- Event handlers describe what happened without also encoding how
  state should respond, a separation React's own documentation names
  directly as a readability benefit.
- Many event handlers that modify related state in a similar way can
  share that logic through the single reducer function, reducing
  duplication that would otherwise be repeated per handler.

Negative.

- A reducer needs more code upfront than a direct state setter call,
  a real cost React's own documentation is candid about for genuinely
  simple cases.
- A team unfamiliar with the reducer's action-and-dispatch vocabulary
  faces a real learning curve compared to directly calling a state
  setter.
- Overusing the pattern for state that is not actually interrelated
  adds structure without the centralization benefit that justifies
  the added code.

## 11. Failure modes and misuse

**Applying a reducer to a component with only a small number of
simple, independent state updates.** Symptom. The component now
carries a reducer function, an action vocabulary, and dispatch calls
for state that never actually needed centralizing, adding real code
for no corresponding readability or debugging benefit. Cause.
Reaching for a reducer by default rather than confirming the specific
scattered-handler or recurring-bug problem the pattern is meant to
solve is genuinely present. Fix. Use direct state setters for
genuinely simple, independent state, reserving the reducer for state
whose updates are actually interrelated or recurring enough to
justify the added structure.

**Writing a reducer function with side effects, such as a network
request, directly inside it.** Symptom. The reducer's behavior becomes
unpredictable and hard to test in isolation, since calling it with
the same state and action no longer reliably produces the same
result. Cause. Treating the reducer as a general-purpose place to put
logic related to a state transition, rather than keeping it a pure
function that only computes the next state. Fix. Keep the reducer
function pure, computing only the next state from the current state
and action, and handle any side effects, such as a network request
triggered by a dispatched action, outside the reducer itself.

**Dispatching many small, granular actions for what is conceptually
one logical update, instead of one action that captures the full
intent.** Symptom. Understanding what actually happened from reading
the dispatched actions becomes harder, not easier, since a single
logical event now appears as several disconnected, low-level actions
rather than one action that names the real thing that occurred.
Cause. Designing actions around the mechanics of the state shape
rather than around the actual events the application experiences.
Fix. Design each action to represent a genuine, named event from the
application's perspective, letting the reducer itself handle whatever
internal state mechanics that single event requires.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Reducer Hook | Direct state setters | Redux, a global store |
|---|---|---|---|
| Centralized, auditable state transitions | Strong, within the component's own scope | Weak, scattered across handlers | Strong, across the entire application |
| Upfront code for simple cases | Weak, more structure than a direct setter | Strong, minimal code for a simple update | Weak, the heaviest upfront structure of the three |
| Separation of what happened from how state responds | Strong | Weak, handlers directly encode both | Strong, at an application-wide scale |
| Scope of the centralization | Local, one component's own state | Not applicable, no centralization | Global, the entire application's state |

Reading of the table. A Reducer Hook wins specifically for a single
component whose own state updates are genuinely interrelated or
scattered enough to benefit from centralizing. Direct state setters
remain simplest for genuinely simple, independent state. Redux
extends the same reducer idea to an entire application's shared
state, a heavier commitment appropriate only when the centralization
benefit needs to span far beyond one component.

## 13. Related and incompatible patterns

- **Headless Component.** A headless component's internal state is
  frequently managed by exactly this pattern, exposing the resulting
  state and dispatch function, or a derived interface built on top of
  them, to whatever consumer renders the actual markup.
- **Context Selector.** A reducer's state and dispatch function are
  frequently shared through context, and a selector-based approach to
  reading that context avoids re-rendering every consumer on every
  dispatched action.
- **Flux.** The reducer pattern is a direct descendant of Flux's
  own single-direction, action-dispatched state update architecture,
  scoped down from an application-wide store to a single component's
  own local state.
- **Redux.** Applies the identical reducer concept at the scale of an
  entire application's state, rather than one component's local
  state.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing component whose state updates are
currently scattered across several individual event handlers.

1. Confirm the component genuinely has many interrelated state
   updates spread across many handlers, or a recurring history of
   incorrect-update bugs, rather than applying the pattern
   speculatively.
2. Identify every distinct way the component's state can change,
   naming each as a genuine, real application action rather
   than a low-level state mechanic.
3. Write a single reducer function that takes the current state and
   one of those actions, returning the new state for each case.
4. Replace each event handler's direct state-setting call with a
   dispatch call describing the action that occurred.
5. Confirm the reducer function stays pure, moving any side effect,
   such as a network request triggered by a dispatched action,
   outside the reducer itself.

Removing the pattern when it stops earning its place, most relevant
when a component's state has genuinely simplified down to a small
number of independent values.

1. Confirm, rather than assume, that the component's state updates
   have genuinely simplified enough that centralizing them no longer
   earns its added structure.
2. Replace the reducer and its dispatched actions with direct state
   setter calls for each now-independent piece of state.
3. Confirm the resulting component behaves identically to before the
   consolidation.

## 15. Testing and verification

Easier because of the pattern.

- Because the reducer is, when kept pure, a plain function from
  current state and an action to a new state, a test can call it
  directly with a given state and action and assert the exact
  resulting state, without needing to render any component at all.
- A bug in a specific state transition can be reproduced and tested
  by dispatching the exact same action against the exact same
  starting state, isolated from whatever component or handler
  originally triggered it.

Harder because of the pattern.

- Testing the full, real-world interaction, a user triggering an
  event handler that dispatches an action that updates state that
  then re-renders the component, needs an integration-level test
  exercising the whole chain, not only the reducer function in
  isolation.
- If a reducer's action vocabulary grows large, testing genuinely
  exhaustive coverage of every action and every state it can be
  dispatched against grows correspondingly, needing deliberate
  attention to which combinations actually matter.

Techniques that apply.

- **Pure reducer unit tests.** Call the reducer function directly with
  a specific state and action, asserting the exact resulting state,
  independent of any component rendering.
- **Action-and-state combination coverage.** Systematically test the
  reducer's behavior across the real combinations of starting
  state and dispatched action, particularly edge cases such as an
  action dispatched against an already-terminal state.
- **Integration tests through the real component.** Render the
  component, trigger a real event, and assert the resulting rendered
  output, confirming the whole chain from event handler to dispatch
  to reducer to re-render works correctly together.
- **Regression tests for fixed bugs.** When a specific incorrect state
  transition is found and fixed, add a test dispatching that same
  action against that same starting state, confirming the bug cannot
  silently return.

## 16. Observability signals

A Reducer Hook's own runtime footprint is usually small, since it
computes a new state value rather than performing heavy work, so the
more honest signal here is about the health of the state-transition
logic itself rather than raw performance.

What to record.

- The frequency of each distinct action type being dispatched, since
  an action that is never dispatched in practice may indicate dead
  code, and an unexpectedly frequent action may point at a handler
  dispatching more often than the interaction actually warrants.
- Any reducer invocation that produces an unexpected or invalid state
  shape, since this is the direct signal that a specific action or
  state combination was not correctly handled.

A healthy state. Every dispatched action produces the expected,
valid state transition, and the distribution of action types matches
what the application's real usage patterns would predict.

A failing state. A reducer invocation produces an unexpected or
invalid state shape, pointing at a missing or incorrect case inside
the reducer function, or an action type is dispatched far more or far
less often than expected, pointing at a handler wired incorrectly to
the interaction it is meant to represent.

## 17. Security and privacy implications

A Reducer Hook is close to neutral for security, being a
state-management technique operating on data already present in the
application, and inventing a dedicated attack surface here would be
dishonest. One practical implication is worth naming.

**Because a reducer's state is usually visible to debugging and
logging tools, including browser developer tools and any middleware
that logs every dispatched action and resulting state, a reducer
managing genuinely sensitive data, such as a plaintext credential or
a full payment card number, exposes that sensitive data to whatever
tooling observes the reducer's transitions, in a way that a value
never placed into reducer-managed state at all would not.** A reducer
intended to hold sensitive data should be scoped deliberately, with
an awareness that its state and every dispatched action are visible
to development and debugging tooling by design, and genuinely
sensitive values are better kept out of reducer state entirely,
handled instead through a path that does not pass through
general-purpose logging or inspection tooling.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models a reducer function and
a dispatch mechanism the way React's own useReducer hook structures
them, kept free of JSX and any specific framework's package so the
sample compiles as plain TypeScript. Python shows the conceptual
shape of the same action-and-reducer state management using a
minimal, framework-agnostic implementation, since Python has no
browser-facing component model and therefore no single dominant
reducer-hook implementation the way TypeScript has React's own
useReducer. Swift shows the same conceptual shape using a minimal
model, analogous to how a native app's own state-management layer
might centralize state transitions behind a single reducing function
responding to dispatched actions. Java, Go, and Rust are omitted,
since none has a dominant, idiomatic browser-facing component
framework this specifically UI-state pattern maps to as directly as
TypeScript does.

### TypeScript

```typescript
interface CounterState {
  count: number;
}

type CounterAction =
  | { type: "increment" }
  | { type: "reset" };

function counterReducer(state: CounterState, action: CounterAction): CounterState {
  switch (action.type) {
    case "increment":
      return { count: state.count + 1 };
    case "reset":
      return { count: 0 };
  }
}

class ReducerStore<State, Action> {
  private state: State;
  private readonly reducer: (state: State, action: Action) => State;

  constructor(reducer: (state: State, action: Action) => State, initialState: State) {
    this.reducer = reducer;
    this.state = initialState;
  }

  dispatch(action: Action): void {
    this.state = this.reducer(this.state, action);
  }

  getState(): State {
    return this.state;
  }
}

const store = new ReducerStore<CounterState, CounterAction>(counterReducer, { count: 0 });

store.dispatch({ type: "increment" });
store.dispatch({ type: "increment" });
console.log("count after two increments:", store.getState().count);

store.dispatch({ type: "reset" });
console.log("count after reset:", store.getState().count);
```

### Python

```python
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

State = TypeVar("State")
Action = TypeVar("Action")


@dataclass
class CounterState:
    count: int


@dataclass
class IncrementAction:
    pass


@dataclass
class ResetAction:
    pass


def counter_reducer(state: CounterState, action: object) -> CounterState:
    if isinstance(action, IncrementAction):
        return CounterState(count=state.count + 1)
    if isinstance(action, ResetAction):
        return CounterState(count=0)
    return state


class ReducerStore(Generic[State, Action]):
    def __init__(self, reducer: Callable[[State, Action], State], initial_state: State) -> None:
        self._reducer = reducer
        self._state = initial_state

    def dispatch(self, action: Action) -> None:
        self._state = self._reducer(self._state, action)

    def get_state(self) -> State:
        return self._state


if __name__ == "__main__":
    store: ReducerStore[CounterState, object] = ReducerStore(counter_reducer, CounterState(count=0))

    store.dispatch(IncrementAction())
    store.dispatch(IncrementAction())
    print("count after two increments:", store.get_state().count)

    store.dispatch(ResetAction())
    print("count after reset:", store.get_state().count)
```

### Swift

```swift
struct CounterState {
    var count: Int
}

enum CounterAction {
    case increment
    case reset
}

func counterReducer(_ state: CounterState, _ action: CounterAction) -> CounterState {
    switch action {
    case .increment:
        return CounterState(count: state.count + 1)
    case .reset:
        return CounterState(count: 0)
    }
}

final class ReducerStore<State, Action> {
    private var state: State
    private let reducer: (State, Action) -> State

    init(reducer: @escaping (State, Action) -> State, initialState: State) {
        self.reducer = reducer
        self.state = initialState
    }

    func dispatch(_ action: Action) {
        state = reducer(state, action)
    }

    func getState() -> State {
        state
    }
}

let store = ReducerStore(reducer: counterReducer, initialState: CounterState(count: 0))

store.dispatch(.increment)
store.dispatch(.increment)
print("count after two increments: " + String(store.getState().count))

store.dispatch(.reset)
print("count after reset: " + String(store.getState().count))
```

## 18. References

1. React. "Extracting State Logic into a Reducer".
   https://react.dev/learn/extracting-state-logic-into-a-reducer
   Verified 2026-08-21. Source of the origin-problem quote and the
   useState-versus-useReducer comparison quotes used in dimensions 1,
   3, 4, and 9.
2. React. "useReducer".
   https://react.dev/reference/react/useReducer
   Verified 2026-08-21. Source of the hook definition quote used in
   dimension 9.
