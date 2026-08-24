---
name: Context Selector
slug: context-selector
family: 13-frontend-ui
category: State Management
aliases: [useContextSelector, Selective Context Subscription]
first_described: "use-context-selector library, dai-shi"
maturity: established
related: [reducer-hook, headless-component]
incompatible_with: []
verified: 2026-08-21
---

# Context Selector

## 1. Name, aliases, and lineage

The canonical name is Context Selector, a technique that lets a
component subscribe to only a specific, derived slice of a shared
context value, rather than re-rendering whenever any part of that
context changes. The use-context-selector library's own documentation
states the underlying problem directly. "React Context and useContext
is often used to avoid prop drilling, however it's known that there's
a performance issue. When a context value is changed, all components
that useContext will re-render." It then states the fix. "It will
trigger re-render if only the selected value is referentially
changed."

The alias **useContextSelector** names the specific hook most
implementations of the technique expose, mirroring React's own
`useContext` naming. **Selective Context Subscription** names the
technique by its effect rather than its API, subscribing selectively
to part of a value rather than the whole of it.

## 2. Problem and context

React's own documentation states plainly how context re-rendering
works. "React automatically re-renders all the children that use a
particular context starting from the provider that receives a
different value," comparing the previous and next values with a
reference check, and noting directly that "skipping re-renders with
memo does not prevent the children receiving fresh context values."
This means a component reading even a small, unrelated slice of a
large context value re-renders every time any part of that context
changes, regardless of whether the specific slice that component
actually reads was affected at all. For a context whose value bundles
many independent pieces of state together, this causes real,
unnecessary re-rendering across every consumer, proportional to how
often any piece of the bundled value changes rather than how often
the specific piece a given consumer cares about changes. Context
Selector solves this by letting each consumer declare exactly which
derived slice of the context value it needs, and re-rendering that
consumer only when that specific slice's value actually changes.

## 3. Forces

The pattern balances the following competing pressures.

- **Avoiding unnecessary re-renders.** Favored. The library's own
  documentation states the guarantee directly. Context Selector
  "will trigger re-render if only the selected value is referentially
  changed," meaning a consumer subscribed to one slice of a context
  is left alone when an unrelated slice changes.
- **Sharing one context provider for many related values.** Favored.
  A single context can continue bundling many related pieces of
  state together at the provider level, while each consumer still
  gets the fine-grained subscription behavior a separate context per
  value would otherwise require.
- **An additional layer between the raw context value and what a
  component reads.** Sacrificed. A consumer using a selector reads
  through an extra function, the selector itself, rather than reading
  the context value directly, a small but real added indirection
  compared to plain `useContext`.
- **Correctness of the selector function itself.** In tension. The
  technique's entire benefit depends on the selector genuinely and
  stably deriving the same slice for the same underlying state, and a
  poorly written selector can undermine the optimization it exists to
  provide.

## 4. Applicability and non-applicability

Reach for a Context Selector when the following hold.

- A context's value genuinely bundles multiple, largely independent
  pieces of state together, and different consumers genuinely only
  care about different slices of that bundled value.
- Unnecessary re-renders from plain context usage are a real, measured
  problem, not merely a theoretical concern, since React's own
  documentation confirms that even `memo` does not prevent a consumer
  from receiving a fresh context value on every provider update.
- The team can write and maintain correct, stable selector functions
  for each consumer's actual data needs.

Do NOT reach for a Context Selector in these cases, and the reason
matters more than the rule.

- **The context's value is already small and simple enough that every
  consumer genuinely needs the whole thing**, adding a selector layer
  on top of a context every consumer already fully depends on adds
  indirection with no corresponding re-render reduction.
- **Re-renders from the plain context have not actually been measured
  as a real performance problem**, applying the pattern speculatively,
  before the specific re-render cost has been confirmed, adds
  complexity ahead of a genuine, felt need.
- **The context's value changes together as a genuinely coupled unit**,
  where every consumer would need to re-render on every change anyway,
  since the values genuinely always change in lockstep, a selector
  provides no real isolation benefit over reading the whole value
  directly.

## 5. Structure

Context Selector has three structural parts.

- **The context provider**, holding the full, bundled value, unchanged
  from how a plain React context provider works.
- **The selector function**, supplied by each consumer, deriving the
  specific slice of the context value that consumer actually needs.
- **The subscription mechanism**, tracking whether a given consumer's
  selected slice has actually changed, and re-rendering only that
  consumer when it has.

## 6. ASCII structure diagram

```
Context provider

+-------------------------------------------------------------+
| value = { user: {...}, theme: {...}, notifications: [...] } |
+-------------------------------------------------------------+
           |
     +-----+-----+-----+
     |           |     |
+----------------------+ +----------------------+ +----------------------+
| Consumer A           | | Consumer B           | | Consumer C           |
| selector:            | | selector:            | | selector:            |
| v => v.user          | | v => v.theme         | | v => v.notifications |
| re-renders only      | | re-renders only      | | re-renders only      |
| when user changes    | | when theme changes   | | when notifications   |
|                      | |                      | | change               |
+----------------------+ +----------------------+ +----------------------+
```

## 7. Dynamics

The trace below shows three consumers, each subscribed to a different
slice of the same context, and only the affected consumer re-rendering
when one slice changes.

```
Provider updates the theme slice

the context provider's value updates, changing only the theme field
   |-- Consumer A's selector, v => v.user, re-evaluates and finds an
       unchanged result, since the user field did not change
   |-- Consumer A does not re-render
   |-- Consumer B's selector, v => v.theme, re-evaluates and finds a
       changed result, since the theme field did change
   |-- Consumer B re-renders with the new theme
   |-- Consumer C's selector, v => v.notifications, re-evaluates and
       finds an unchanged result
   |-- Consumer C does not re-render

Provider updates the notifications slice

the context provider's value updates, changing only notifications
   |-- Consumer A and Consumer B's selectors both find unchanged
       results and do not re-render
   |-- Consumer C's selector finds a changed result and re-renders
       with the new notifications
```

## 8. Implementation variants

**Library-provided context selector.** A dedicated library, such as
use-context-selector, provides the subscription mechanism directly,
letting a team adopt fine-grained context subscriptions without
building the underlying tracking logic by hand.

**Multiple, split contexts.** Instead of a selector layer over one
bundled context, the bundled value is split into several separate
contexts from the start, each holding one independent slice, so
plain `useContext` on each already provides the fine-grained
subscription a selector would otherwise add.

**External store with selector-based subscriptions.** A state
management library outside React's own context mechanism entirely
provides selector-based subscriptions as a first-class feature,
sidestepping React context's re-render behavior altogether.

**Memoized selector composition.** Several selectors are composed
together, with intermediate results memoized, letting a consumer
derive a more complex slice from several underlying pieces of context
state while still avoiding a re-render when none of the underlying
pieces its composed selector actually depends on have changed.

## 9. Known production uses

**React's own documentation, naming the re-render behavior a
selector solves.** React states the mechanism directly. "React
automatically re-renders all the children that use a particular
context starting from the provider that receives a different value,"
and specifically notes "skipping re-renders with memo does not
prevent the children receiving fresh context values." React,
"useContext," https://react.dev/reference/react/useContext, verified
2026-08-21.

**use-context-selector's own documentation, defining the pattern and
its guarantee.** The library states the problem and the fix directly.
"React Context and useContext is often used to avoid prop drilling,
however it's known that there's a performance issue. When a context
value is changed, all components that useContext will re-render,"
and the selector-based fix "will trigger re-render if only the
selected value is referentially changed." dai-shi,
"use-context-selector," https://github.com/dai-shi/use-context-selector,
verified 2026-08-21.

## 10. Consequences

Positive.

- A consumer subscribed to one slice of a bundled context value is
  left alone when an unrelated slice changes, directly addressing the
  unnecessary re-render behavior React's own documentation confirms
  even `memo` cannot prevent.
- A single context provider can continue bundling many related pieces
  of state together at the provider level, while each consumer still
  gets fine-grained, isolated re-render behavior.
- The technique composes with existing context-based code, since the
  provider itself is unchanged, only the consumer's subscription
  mechanism differs.

Negative.

- A consumer reads through an extra selector function rather than the
  context value directly, a small added indirection every consumer
  must now write and maintain.
- The optimization's benefit depends entirely on the selector function
  being correct and stable, and a poorly written selector, one that
  returns a new object reference on every call, for instance,
  undermines the exact re-render reduction the pattern exists to
  provide.
- Splitting a context's value into selector-derived slices adds a
  layer of indirection a reader must understand to know exactly which
  underlying state a given consumer actually depends on.

## 11. Failure modes and misuse

**Writing a selector that returns a new object or array reference on
every call, even when the underlying selected data has not actually
changed.** Symptom. The consumer re-renders on every provider update
regardless of whether the selected slice actually changed, completely
undermining the optimization the pattern exists to provide. Cause. The
selector function constructs a new object or array literal on each
call, rather than returning a stable reference when the underlying
data is unchanged. Fix. Write selectors that return the same
reference for the same underlying data, either by selecting a
primitive or an already-stable reference directly, or by memoizing
the selector's own derived output.

**Applying a context selector to a context whose value is already
small and fully needed by every consumer.** Symptom. The application
now carries a selector-based subscription mechanism and per-consumer
selector functions for a context that never actually had a
real re-render problem, adding real indirection with no
corresponding benefit. Cause. Reaching for the pattern by default,
rather than confirming a genuine, measured over-rendering problem
exists first. Fix. Use plain `useContext` for a context whose value
every consumer genuinely needs in full, reserving the selector
pattern for a context whose value genuinely bundles independent
slices different consumers only partially need.

**Splitting a single context's data across several selector-derived
consumers without confirming the underlying provider itself still
updates efficiently.** Symptom. Individual consumers now re-render
correctly and minimally, but the provider itself still recomputes and
provides a fresh value unnecessarily often, so the underlying source
of the wasted work was never actually addressed. Cause. Optimizing
only the consumer side of the context relationship while leaving an
unoptimized provider that recreates its value object on every render
regardless of whether anything inside it genuinely changed. Fix.
Confirm the provider itself only produces a genuinely new value when
its underlying state actually changes, so the selector-based
consumers are reacting to real changes rather than compensating for
an unnecessarily churning provider.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Context Selector | Plain useContext | Multiple, split contexts |
|---|---|---|---|
| Avoiding unnecessary re-renders | Strong, per-consumer fine-grained subscriptions | Weak, every consumer re-renders on any change | Strong, but requires restructuring the provider itself |
| Sharing one provider for related values | Strong, one bundled context, selective consumption | Strong, but at the cost of over-rendering | Weak, requires several separate providers |
| Added indirection per consumer | Moderate, an extra selector function per consumer | None, direct value access | None, direct value access per split context |
| Ease of restructuring existing code | Strong, providers stay unchanged | Not applicable, the default behavior | Weak, requires splitting the provider and every call site |

Reading of the table. A Context Selector wins specifically when a
bundled context's value cannot easily be split into several separate
contexts, but different consumers genuinely only need different
slices of it. Plain `useContext` remains simplest for a context whose
value every consumer genuinely needs in full. Splitting into multiple
contexts from the start is often the cleaner long-term structure when
the codebase can be restructured, but a selector is the lower-friction
fix for an existing, already-bundled context.

## 13. Related and incompatible patterns

- **Reducer Hook.** A reducer's state and dispatch function are
  frequently shared through context, and a selector-based subscription
  to that context avoids re-rendering every consumer on every
  dispatched action, only the consumers whose selected slice the
  action actually affected.
- **Headless Component.** A headless component's exposed state is
  frequently shared through context to consumers deep in a tree, and a
  selector lets each of those consumers subscribe only to the specific
  piece of that exposed state they actually render from.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing context whose consumers currently
re-render more often than their actual data needs would require.

1. Confirm, through measurement, that consumers of the context are
   genuinely re-rendering more often than their actual data
   dependencies would require, rather than applying the pattern
   speculatively.
2. Identify, for each consumer, exactly which slice of the context's
   value it actually reads and depends on.
3. Introduce a context selector mechanism, either a dedicated library
   or an equivalent subscription tracking implementation, without
   changing the provider's own value shape.
4. Convert each consumer's plain `useContext` call into a selector-based
   call, writing a selector that returns a stable reference for
   unchanged underlying data.
5. Confirm, through measurement, that each consumer now re-renders
   only when its own selected slice actually changes.

Removing the pattern when it stops earning its place, most relevant
when a context's value has genuinely simplified enough that every
consumer needs the whole thing, or the context has been restructured
into several smaller, independent contexts.

1. Confirm, rather than assume, that the context's value has genuinely
   simplified, or has been restructured, in a way that removes the
   original over-rendering problem.
2. Replace each selector-based subscription with a plain `useContext`
   call, or with a call to the newly split, smaller context.
3. Confirm the resulting consumers still re-render only as often as
   their actual data needs require.

## 15. Testing and verification

Easier because of the pattern.

- A test can assert a specific consumer does not re-render when an
  unrelated slice of the context changes, directly verifying the
  fine-grained subscription behavior the pattern is meant to provide.
- Because each selector is a plain function from the context's full
  value to a derived slice, a test can call a selector directly with a
  given context value and assert the exact expected result, without
  needing to render any component.

Harder because of the pattern.

- Verifying that a selector genuinely returns a stable reference for
  unchanged underlying data needs a specific test asserting reference
  equality across repeated calls with equivalent input, a subtlety
  easy to overlook in a typical rendering test.
- Diagnosing an unexpected re-render needs tracing through which
  specific selector's output actually changed, an extra layer of
  indirection compared to a plain context consumer where the entire
  value's change is the only possible cause.

Techniques that apply.

- **Re-render count assertions.** Render several consumers subscribed
  to different slices of a context, update one slice, and assert only
  the affected consumer's render count increased.
- **Selector stability tests.** Call a selector function repeatedly
  with equivalent underlying data, asserting it returns the same
  reference, catching a selector that unnecessarily constructs a new
  object or array each time.
- **Isolated selector unit tests.** Test each selector function
  directly against a range of context value shapes, asserting the
  correct derived slice, independent of any component rendering.
- **Provider efficiency tests.** Assert the provider itself only
  produces a new value object when its underlying state has actually
  changed, confirming the source of truth is not itself churning
  unnecessarily.

## 16. Observability signals

Context Selector exists specifically to reduce a measurable
performance cost, unnecessary component re-renders, so a dedicated
production or development-time signal is the honest and expected
form here.

What to record.

- The re-render count of each context consumer over a representative
  session, compared against how often that consumer's actual selected
  slice genuinely changed, since a consumer re-rendering noticeably
  more often than its own slice changes points at a selector that is
  not returning stable references.
- The frequency of provider value updates versus the frequency of
  genuine underlying state changes, since a provider producing new
  values more often than its state actually changes undermines every
  downstream selector's optimization.

A healthy state. Each consumer's re-render count tracks closely with
how often its own selected slice actually changes, and the provider
itself produces a new value only when its underlying state has
genuinely changed.

A failing state. A consumer re-renders noticeably more often than its
selected slice changes, pointing at an unstable selector returning a
fresh reference on every call, or the provider itself produces a new
value far more often than its underlying state changes, undermining
every downstream selector regardless of how well each one is written.

## 17. Security and privacy implications

Context Selector is close to neutral for security, being a
performance-oriented state-subscription technique rather than a
data-handling one, and inventing a dedicated attack surface here would
be dishonest. One practical implication is worth naming.

**Because a context selector still reads from the same underlying
context value every consumer shares, using a selector to expose only
part of a context's value to a given consumer narrows what that
consumer RENDERS from, not what data actually passes through the
provider and is available in the surrounding application's memory,
so a selector must never be treated as an access-control mechanism
separating sensitive data a given consumer should not be able to
reach.** The full context value remains present in the provider and
is fully reachable by any code with access to the context itself,
regardless of how a given consumer's selector narrows what it reads
from it, so any genuine access restriction on sensitive data belongs
to a real authorization layer, never to which slice a particular
selector happens to derive.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models a selector-based
subscription store the way use-context-selector's own approach
structures it, kept free of JSX and any specific framework's package
so the sample compiles as plain TypeScript. Python shows the
conceptual shape of the same selector-and-subscription mechanism
using a minimal, framework-agnostic implementation, since Python has
no browser-facing component model and therefore no single dominant
context-selector implementation the way TypeScript has React context
and use-context-selector. Swift shows the same conceptual shape using
a minimal model, analogous to how a native app's own observable state
container might notify only the specific observers whose derived
value actually changed. Java, Go, and Rust are omitted, since none has
a dominant, idiomatic browser-facing component framework this
specifically UI-state pattern maps to as directly as TypeScript does.

### TypeScript

```typescript
interface SharedState {
  user: string;
  theme: string;
  notificationCount: number;
}

type Selector<T> = (state: SharedState) => T;
type Listener = () => void;

class SelectableStore {
  private state: SharedState;
  private listeners: Map<string, { selector: Selector<unknown>; lastValue: unknown; listener: Listener }> = new Map();

  constructor(initialState: SharedState) {
    this.state = initialState;
  }

  subscribe<T>(id: string, selector: Selector<T>, listener: Listener): void {
    this.listeners.set(id, { selector, lastValue: selector(this.state), listener });
  }

  setState(partial: Partial<SharedState>): void {
    this.state = { ...this.state, ...partial };
    for (const entry of this.listeners.values()) {
      const nextValue = entry.selector(this.state);
      if (nextValue !== entry.lastValue) {
        entry.lastValue = nextValue;
        entry.listener();
      }
    }
  }
}

const store = new SelectableStore({ user: "ada", theme: "light", notificationCount: 0 });

store.subscribe("userConsumer", (s) => s.user, () => console.log("user consumer re-rendered"));
store.subscribe("themeConsumer", (s) => s.theme, () => console.log("theme consumer re-rendered"));

store.setState({ theme: "dark" });
store.setState({ user: "grace" });
```

### Python

```python
from dataclasses import dataclass, replace
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class SharedState:
    user: str
    theme: str
    notification_count: int


@dataclass
class Subscription:
    selector: Callable[[SharedState], object]
    last_value: object
    listener: Callable[[], None]


class SelectableStore:
    def __init__(self, initial_state: SharedState) -> None:
        self._state = initial_state
        self._subscriptions: dict[str, Subscription] = {}

    def subscribe(self, sub_id: str, selector: Callable[[SharedState], object], listener: Callable[[], None]) -> None:
        self._subscriptions[sub_id] = Subscription(selector, selector(self._state), listener)

    def set_state(self, **updates: object) -> None:
        self._state = replace(self._state, **updates)
        for sub in self._subscriptions.values():
            next_value = sub.selector(self._state)
            if next_value != sub.last_value:
                sub.last_value = next_value
                sub.listener()


if __name__ == "__main__":
    store = SelectableStore(SharedState(user="ada", theme="light", notification_count=0))

    store.subscribe("user_consumer", lambda s: s.user, lambda: print("user consumer re-rendered"))
    store.subscribe("theme_consumer", lambda s: s.theme, lambda: print("theme consumer re-rendered"))

    store.set_state(theme="dark")
    store.set_state(user="grace")
```

### Swift

```swift
struct SharedState {
    var user: String
    var theme: String
    var notificationCount: Int
}

final class SelectableStore {
    private var state: SharedState
    private var subscriptions: [String: (selector: (SharedState) -> AnyHashable, lastValue: AnyHashable, listener: () -> Void)] = [:]

    init(initialState: SharedState) {
        state = initialState
    }

    func subscribe(id: String, selector: @escaping (SharedState) -> AnyHashable, listener: @escaping () -> Void) {
        subscriptions[id] = (selector, selector(state), listener)
    }

    func setState(_ update: (inout SharedState) -> Void) {
        update(&state)
        for (id, entry) in subscriptions {
            let nextValue = entry.selector(state)
            if nextValue != entry.lastValue {
                subscriptions[id] = (entry.selector, nextValue, entry.listener)
                entry.listener()
            }
        }
    }
}

let store = SelectableStore(initialState: SharedState(user: "ada", theme: "light", notificationCount: 0))

store.subscribe(id: "userConsumer", selector: { $0.user }, listener: { print("user consumer re-rendered") })
store.subscribe(id: "themeConsumer", selector: { $0.theme }, listener: { print("theme consumer re-rendered") })

store.setState { $0.theme = "dark" }
store.setState { $0.user = "grace" }
```

## 18. References

1. React. "useContext".
   https://react.dev/reference/react/useContext
   Verified 2026-08-21. Source of the re-render mechanism quotes used
   in dimensions 2, 3, and 9.
2. dai-shi. "use-context-selector".
   https://github.com/dai-shi/use-context-selector
   Verified 2026-08-21. Source of the problem-and-fix quotes used in
   dimensions 1, 3, and 9.
