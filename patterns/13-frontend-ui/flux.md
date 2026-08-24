---
name: Flux
slug: flux
family: 13-frontend-ui
category: State Management
aliases: [Unidirectional Data Flow, Flux Architecture]
first_described: "Facebook, 30 July 2014"
maturity: deprecated
related: [provider-pattern, hooks, signals, higher-order-component]
incompatible_with: []
verified: 2026-08-21
---

# Flux

## 1. Name, aliases, and lineage

The canonical name is Flux. Facebook's own React Blog post
introducing the architecture states it directly. "Flux is the
application architecture Facebook uses to build JavaScript
applications. It's based on a unidirectional data flow." The post was
published 30 July 2014, and the archived Flux documentation restates
the description in fuller form. "Flux is the application architecture
that Facebook uses for building client-side web applications. It
complements React's composable view components by utilizing a
unidirectional data flow."

The alias **Unidirectional Data Flow** names the defining property
the architecture enforces, data always travels the same direction
through the system, action to dispatcher to store to view, with no
path for a view to mutate a store's data directly. **Flux
Architecture** is the fuller name used interchangeably with the
short form.

## 2. Problem and context

Traditional MVC-style architectures let a view update a model
directly, and let multiple models observe and update one another,
which becomes difficult to reason about as an application grows,
since a single user action can trigger a long chain of interdependent
updates whose order and cause are hard to trace. Facebook found this
particularly painful in a large, real-time application with many
interconnected pieces of state. Flux solves this by enforcing a
single direction for data to travel. a user action is dispatched
through one central dispatcher to every store, each store updates its
own state in response, and every view affected by that state
re-renders, with no view ever mutating a store directly and no
store ever calling another store to update it.

## 3. Forces

The pattern balances the following competing pressures.

- **Predictable, traceable data flow.** Favored. Because data always
  travels the same direction, action to dispatcher to store to view,
  a developer can trace any state change back to the single action
  that caused it, with no possibility of a view mutating a store out
  of band.
- **Decoupled stores.** Favored. A store never calls another store
  directly, avoiding the cascading update chains that make
  traditional MVC hard to reason about as an application grows.
- **Boilerplate per action.** Sacrificed. Every distinct kind of
  state change needs its own explicitly defined action and explicit
  handling in every store that cares about it, producing a real
  amount of repetitive code compared to directly mutating a model.
- **A single, central dispatcher as a coordination point.**
  Sacrificed unless carefully managed. Routing every action through
  one dispatcher avoids uncoordinated cross-store updates, but the
  dispatcher itself becomes a single, central piece of the
  architecture that every store depends on.

## 4. Applicability and non-applicability

Reach for Flux, or study its ideas, when the following hold.

- A large, real-time application has many interconnected pieces of
  state, and traditional two-way data binding or direct
  model-to-model updates have become hard to trace and debug.
- Traceability of exactly what caused a given state change matters
  more than minimizing the boilerplate of defining an explicit action
  for every kind of change.
- A team is studying the historical foundation of unidirectional data
  flow before adopting a modern successor library that implements the
  same core idea with less boilerplate.

Do NOT reach for Flux itself in these cases, and the reason matters
more than the rule.

- **A new project starting today**, since the original Flux library
  is archived, and its own README recommends modern successors,
  Redux, MobX, Recoil, Zustand, or Jotai, which implement the same
  unidirectional-flow idea with substantially less boilerplate.
- **The application's state is simple or mostly local to a few
  components**, the ceremony of an action, a dispatcher, and explicit
  store handling for every change is not repaid when a framework's
  own built-in state primitive, such as Hooks, already suffices.
- **A team wants fine-grained update precision on frequently
  changing values**, Flux's store-driven re-render model shares the
  same coarse re-render cost as other whole-component-re-run
  approaches, the specific cost Signals were designed to avoid.

## 5. Structure

Flux has four structural parts.

- **Actions**, plain objects describing what happened, created by a
  view in response to a user interaction or created from a server
  response.
- **The dispatcher**, a single, central hub that every action passes
  through, broadcasting each action to every registered store.
- **Stores**, each holding a specific slice of application state and
  its update logic, receiving every dispatched action and updating
  their own state when an action they care about arrives.
- **Views**, React components that read state from one or more
  stores and re-render when a store they depend on emits a change,
  and that create new actions in response to user interaction rather
  than mutating any store directly.

## 6. ASCII structure diagram

```
    View                              (a React component)
      |
      | user interacts, creates an Action
      v
    Action -----------------> Dispatcher   (the single central hub)
                                    |
                                    | broadcasts the action to every store
                                    v
                          +---------+---------+
                          |                   |
                       Store A             Store B
                          |                   |
                          | emits a change event when its own state updates
                          v                   v
                        View A              View B
                    (re-renders)         (re-renders)

    Data always flows this one direction. no view mutates a store
    directly, and no store calls another store to update it.
```

## 7. Dynamics

The trace below shows a user interaction traveling through the full
Flux cycle, from the originating view back to the views that
re-render.

```
User interaction

TodoView's checkbox is clicked
   |-- TodoView creates a TOGGLE_TODO action
   |-- the action is dispatched to Dispatcher.dispatch(action)

Dispatcher broadcasts

Dispatcher notifies every registered store of the action
   |-- TodoStore receives TOGGLE_TODO, updates its own state
   |-- CounterStore receives TOGGLE_TODO, ignores it (does not care)

Store emits change

TodoStore emits a change event after updating its state
   |-- TodoListView, subscribed to TodoStore, re-renders with the
       updated todo list
   |-- CounterStore never emitted a change, so any view depending on
       it does not re-render
```

## 8. Implementation variants

**The original Facebook Flux implementation.** A single dispatcher
object, plain-object stores using an event emitter to notify
subscribers, and action creators as plain functions, the reference
shape the architecture was originally documented with, now archived.

**Redux, the most widely adopted successor.** A single, centralized
store rather than several independent stores, pure reducer functions
in place of imperative store update logic, and the same
unidirectional action-to-update-to-view flow, trading Flux's multiple
independent stores for one combined state tree and a more
predictable, serializable update mechanism.

**Store composition via combined reducers.** Several independently
defined update functions, each responsible for one slice of state,
composed into a single store's overall state shape, letting a large
application's state stay organized into logical pieces while still
presenting as one central store to the rest of the architecture.

**Middleware intercepting the action stream.** A layer inserted
between an action being dispatched and a store actually receiving
it, used for logging every action, handling asynchronous side
effects, or transforming an action before it reaches a store,
without any store or view needing to know the middleware exists.

## 9. Known production uses

**Facebook's own architecture, as described in its original
documentation.** Facebook's own React Blog post states directly.
"Flux is the application architecture Facebook uses to build
JavaScript applications," and the fuller archived overview restates
it. "Flux is the application architecture that Facebook uses for
building client-side web applications," a first-party statement that
the architecture was actually deployed in Facebook's own real
applications, not merely a proposed pattern. Facebook, Flux, Actions
and the Dispatcher, 30 July 2014,
https://legacy.reactjs.org/blog/2014/07/30/flux-actions-and-the-dispatcher.html,
verified 2026-08-21.

**The archived Flux in-depth overview, describing the four-part
architecture directly deployed by Facebook.** The documentation
states the full unidirectional flow directly. "When a user interacts
with a React view, the view propagates an action through a central
dispatcher, to the various stores that hold the application's data
and business logic, which updates all of the views that are
affected." Facebook, Flux, In-Depth Overview,
https://facebookarchive.github.io/flux/docs/in-depth-overview/,
verified 2026-08-21.

## 10. Consequences

Positive.

- Every state change traces back to the single action that caused
  it, since data only ever travels action to dispatcher to store to
  view, with no path for a view to mutate a store directly.
- Stores stay decoupled from one another, since no store calls
  another store to update it, avoiding the cascading update chains
  that make traditional MVC hard to reason about at scale.
- The architecture directly addressed real, documented scalability
  problems Facebook encountered building a large, interconnected
  application, rather than being a purely theoretical proposal.

Negative.

- Every distinct kind of state change needs an explicitly defined
  action and explicit handling in every store that cares about it,
  producing noticeably more code than directly mutating a model.
- The original Flux library itself is archived, with its own README
  recommending Redux, MobX, Recoil, Zustand, or Jotai as the modern
  path forward, so a new project reaching for Flux by name is
  reaching for a superseded implementation.
- The store-driven re-render model shares the same coarse,
  whole-component-re-run update cost as other traditional state
  approaches, offering no fine-grained update precision on its own.

## 11. Failure modes and misuse

**Mutating a store's state directly from a view instead of
dispatching an action.** Symptom. A store's state changes with no
corresponding action ever having been dispatched, and the change is
invisible to anything relying on the dispatcher's action stream for
traceability or logging. Cause. A view reached directly into a
store's internal state and mutated it, bypassing the dispatcher
entirely, breaking the single-direction guarantee the whole
architecture exists to provide. Fix. Route every state change through
a dispatched action, with the store's own internal state genuinely
private and only ever updated in response to an action it receives
from the dispatcher.

**One store calling into another store's update logic directly.**
Symptom. Updating one store causes an unexpected chain of changes
in a different store, and the interaction is hard to trace because it
happens outside the normal dispatcher-mediated flow. Cause. A store
was written to directly call a method on another store rather than
letting each store independently react to the same dispatched
action, reintroducing the cross-model chain-reaction problem Flux
exists to prevent. Fix. Have each store react independently to the
actions it cares about, and if two stores genuinely need to
coordinate, use the
dispatcher's own mechanism for waiting on another store to finish
processing an action first, rather than a direct call between stores.

**Adopting the archived original Flux library on a new project
instead of a maintained successor.** Symptom. A new codebase depends
on an unmaintained library, missing improvements the ecosystem has
made since Flux's original release, most notably Redux's more
predictable single-store, pure-reducer model. Cause. Reaching for
Flux specifically by its original name without checking whether the
library itself is still maintained. Fix. Use a maintained successor,
such as Redux, that implements the same unidirectional-flow idea, per
the archived Flux README's own explicit recommendation.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Flux (original) | Redux | The Provider Pattern | Hooks (useState/useReducer) |
|---|---|---|---|---|
| Traceability of what caused a state change | High, every change traces to a dispatched action | High, same guarantee with a single store | Low, a context value can change for any reason | Low, a state setter can be called from anywhere |
| Store or state organization | Several independent stores | One centralized store composed of reducers | No dedicated state-organization mechanism | No dedicated state-organization mechanism |
| Boilerplate per distinct state change | High, an action plus explicit handling in each store | High, an action plus a reducer case, though more standardized | Low, a plain state update | Low, a plain state update |
| Current maintenance status | Archived, successor recommended | Actively maintained, the dominant successor | Actively maintained, a core framework feature | Actively maintained, a core framework feature |
| Fit for a new project starting today | Weak, reach for a successor instead | Strong, for applications wanting the same guarantees | Strong, for sharing values broadly with less ceremony | Strong, for local or moderately shared state |

Reading of the table. Flux's own ideas, traceable, unidirectional
data flow, remain sound and were carried forward almost entirely
intact into Redux, which is why Redux is the pattern's true modern
successor rather than a wholly different architecture. The original
Flux library itself is not a reasonable choice for a new project,
since it is archived and its own maintainers point to modern
alternatives. The Provider Pattern and Hooks solve a different,
narrower problem, sharing or holding state, without Flux's specific
traceability guarantee.

## 13. Related and incompatible patterns

- **Provider Pattern.** A related but distinct mechanism for sharing
  state broadly across a component tree, without Flux's specific
  traceability guarantee that every change traces back to a single
  dispatched action.
- **Hooks.** The modern default state primitive for state genuinely
  local to a component or a small subtree, a much lighter-weight
  alternative to the full Flux ceremony when an application's state
  needs do not call for centralized, traceable updates.
- **Signals.** A different response to a related problem, prioritizing
  fine-grained update precision over Flux's traceability guarantee,
  and generally not combined with Flux directly.
- **Higher-Order Component.** An older, largely unrelated composition
  mechanism, addressing behavior sharing across components rather
  than the centralized state-update-traceability problem Flux
  solves.

## 14. Refactoring path in and out

Introducing the pattern, or more realistically its modern successor,
into code that does not have it. Ordered steps, most relevant to an
application whose state updates have become hard to trace because
views or models mutate each other directly.

1. Identify the state whose updates need to become traceable, and
   confirm the application genuinely has the scale of interconnected
   state that justifies the ceremony.
2. Choose a maintained implementation of the same unidirectional-flow
   idea, such as Redux, rather than the archived original Flux
   library.
3. Define explicit actions for each distinct kind of state change,
   and migrate the corresponding update logic into a store or reducer
   that only updates its own state in response to a dispatched
   action.
4. Migrate every view that previously mutated the state directly to
   instead dispatch an action, confirming no direct mutation path
   remains, guarding against the first failure mode in dimension 11.
5. Add a test asserting a store or reducer's state updates correctly
   for each defined action, independent of any specific view.

Removing the pattern when it stops earning its place, most relevant
when an application's state has genuinely simplified, or when a
lighter-weight mechanism now covers the same need with less
ceremony.

1. Confirm the traceability guarantee is genuinely no longer needed
   for the specific state in question, rather than assuming so
   without review.
2. Migrate simple, locally scoped state back to a framework's native
   state primitive, such as `useState` or `useReducer`, where the
   full action-dispatcher-store ceremony is no longer repaid.
3. Remove the store or reducer only after every consumer has
   migrated off it.

## 15. Testing and verification

Easier because of the pattern.

- A store or reducer's update logic can be tested directly by
  dispatching a specific action and asserting the resulting state,
  entirely independent of any view.
- Because every state change traces to a single dispatched action, a
  test can simulate an entire user interaction as a sequence of
  actions and assert the final state, without needing to render or
  interact with any actual UI.

Harder because of the pattern.

- Testing the full, real integration, a view dispatching an action
  and re-rendering in response to the resulting store change, needs
  wiring together the dispatcher, the store, and the view, rather
  than testing any one piece in isolation.
- The first failure mode in dimension 11, a direct store mutation
  bypassing the dispatcher, is invisible to a test that only
  dispatches actions through the intended path, since the bug is
  specifically that some other code skipped that path entirely.

Techniques that apply.

- **Isolated store or reducer test.** Dispatch a specific action
  directly against a store or reducer and assert the resulting
  state, independent of any view.
- **Action-sequence test.** Dispatch a sequence of actions
  representing a real user interaction and assert the final state,
  entirely independent of any rendered UI.
- **Full-integration test.** Render a view, trigger the interaction
  that dispatches an action, and assert the view re-renders correctly
  in response to the resulting store change.
- **Direct-mutation regression test.** Audit or lint for any code path
  that mutates a store's state without going through a dispatched
  action, guarding against the first failure mode in dimension 11.

## 16. Observability signals

Flux is a source-level architectural pattern with no independent
runtime footprint of its own beyond the dispatching and store updates
it already performs, and inventing a dedicated production signal
purely for the pattern would be dishonest. Two things are worth
watching in a codebase that uses it or a direct successor.

What to record.

- The volume and type of dispatched actions over time, since logging
  every action through the dispatcher is a natural place to capture
  a complete, ordered history of every state change an application
  has made.
- Any detected direct store mutation that bypassed the dispatcher, a
  concrete, checkable violation of the architecture's core guarantee.

A healthy state. Every state change corresponds to exactly one
dispatched action, and the action log forms a complete, ordered
record of everything that happened in the application.

A failing state. A store's state changes with no corresponding
action in the dispatch log, pointing at a direct mutation that
bypassed the dispatcher entirely.

## 17. Security and privacy implications

Flux is close to neutral for security, being a state-management
architecture rather than a data-handling one, and inventing a
dedicated attack surface here would be dishonest. One practical
implication is worth naming.

**Logging or persisting every dispatched action, a common and useful
Flux practice, can capture sensitive data if an action carries it in
its payload.** Because the dispatcher's central position makes it a
convenient place to log a complete history of everything an
application does, a team building such logging should confirm no
action payload carries a password, a token, or other sensitive data
in raw form before persisting or transmitting the action log elsewhere.
this is not different from any other logging surface in principle,
but it is worth naming explicitly, since the dispatcher's very
usefulness as a central logging point is exactly what makes it easy
to log more than intended.

## 18. References

1. Facebook. "Flux, Actions and the Dispatcher". React Blog. 30 July
   2014.
   https://legacy.reactjs.org/blog/2014/07/30/flux-actions-and-the-dispatcher.html
   Verified 2026-08-21. Source of the defining sentence and the
   first_described lineage.
2. Facebook. "Flux, In-Depth Overview".
   https://facebookarchive.github.io/flux/docs/in-depth-overview/
   Verified 2026-08-21. Source for the production use in dimension 9
   and the full data-flow description.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models the classic
action-dispatcher-store shape the way the original Flux library and
its successors structure it, kept free of JSX and any specific
framework's package so the sample compiles as plain TypeScript.
Python shows the same conceptual split using a minimal,
framework-agnostic dispatcher and store class, since Python has no
single dominant Flux-shaped UI framework the way TypeScript has React
and its Flux-family libraries. Swift shows the pattern using a
minimal unidirectional-flow store, closely analogous to the Redux-
inspired state containers used in several SwiftUI architectures. Java,
Go, and Rust are omitted, since none has a dominant, idiomatic
UI-component framework this specifically frontend pattern maps to as
directly as TypeScript and Swift do.

### TypeScript

```typescript
interface Action {
  type: string;
  payload?: unknown;
}

type Listener = () => void;

class Dispatcher {
  private stores: Store[] = [];

  register(store: Store): void {
    this.stores.push(store);
  }

  dispatch(action: Action): void {
    this.stores.forEach((store) => store.handleAction(action));
  }
}

class Store {
  private state: number = 0;
  private listeners: Listener[] = [];

  handleAction(action: Action): void {
    if (action.type === "INCREMENT") {
      this.state += 1;
      this.emitChange();
    }
  }

  getState(): number {
    return this.state;
  }

  subscribe(listener: Listener): void {
    this.listeners.push(listener);
  }

  private emitChange(): void {
    this.listeners.forEach((listener) => listener());
  }
}

const dispatcher = new Dispatcher();
const counterStore = new Store();
dispatcher.register(counterStore);

counterStore.subscribe(() => {
  console.log("count is now " + counterStore.getState());
});

dispatcher.dispatch({ type: "INCREMENT" });
dispatcher.dispatch({ type: "INCREMENT" });
```

### Python

```python
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Action:
    type: str
    payload: Any = None


class Store:
    def __init__(self) -> None:
        self.state = 0
        self._listeners: list[Callable[[], None]] = []

    def handle_action(self, action: Action) -> None:
        if action.type == "INCREMENT":
            self.state += 1
            self._emit_change()

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def _emit_change(self) -> None:
        for listener in self._listeners:
            listener()


class Dispatcher:
    def __init__(self) -> None:
        self._stores: list[Store] = []

    def register(self, store: Store) -> None:
        self._stores.append(store)

    def dispatch(self, action: Action) -> None:
        for store in self._stores:
            store.handle_action(action)


if __name__ == "__main__":
    dispatcher = Dispatcher()
    counter_store = Store()
    dispatcher.register(counter_store)

    def on_change() -> None:
        print(f"count is now {counter_store.state}")

    counter_store.subscribe(on_change)
    dispatcher.dispatch(Action(type="INCREMENT"))
    dispatcher.dispatch(Action(type="INCREMENT"))
```

### Swift

```swift
struct Action {
    let type: String
}

final class Store {
    private(set) var state: Int = 0
    private var listeners: [() -> Void] = []

    func handleAction(_ action: Action) {
        if action.type == "INCREMENT" {
            state += 1
            emitChange()
        }
    }

    func subscribe(_ listener: @escaping () -> Void) {
        listeners.append(listener)
    }

    private func emitChange() {
        listeners.forEach { $0() }
    }
}

final class Dispatcher {
    private var stores: [Store] = []

    func register(_ store: Store) {
        stores.append(store)
    }

    func dispatch(_ action: Action) {
        stores.forEach { $0.handleAction(action) }
    }
}

let dispatcher = Dispatcher()
let counterStore = Store()
dispatcher.register(counterStore)

counterStore.subscribe {
    print("count is now " + String(counterStore.state))
}

dispatcher.dispatch(Action(type: "INCREMENT"))
dispatcher.dispatch(Action(type: "INCREMENT"))
```
