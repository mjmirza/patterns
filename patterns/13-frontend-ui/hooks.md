---
name: Hooks
slug: hooks
family: 13-frontend-ui
category: Component Composition
aliases: [React Hooks, Function Component State]
first_described: "React v16.8, 6 February 2019"
maturity: canonical
related: [render-props, higher-order-component, compound-components, provider-pattern]
incompatible_with: []
verified: 2026-08-21
---

# Hooks

## 1. Name, aliases, and lineage

The canonical name is Hooks, most often written React Hooks to
distinguish it from the general functional-programming sense of the
word. React's official blog post announcing the stable release states
the goal directly. "Hooks let you use state and other React features
without writing a class." The feature shipped in React 16.8, released
6 February 2019.

The React team's own reference documentation frames the individual
built-in hooks by what capability each one grants a function
component. "State lets a component remember information like user
input," "Context lets a component receive information from distant
parents without passing it as props," "Refs let a component hold some
information that isn't used for rendering," and "Effects let a
component connect to and synchronize with external systems."

## 2. Problem and context

Before Hooks, a function component in React could not hold its own
state or run a side effect, so any component needing state, a
lifecycle-tied effect, or access to context had to be rewritten as a
class component. Sharing stateful logic between class components
needed either a Higher-Order Component or a Render Prop, both of
which introduce an extra layer in the rendered tree and, when several
are combined, a nesting or wrapper chain that becomes hard to trace,
a problem the community had already named wrapper hell. Hooks solve
this by letting a plain function component call a small set of
built-in functions, useState, useEffect, useContext, and others, to
opt into exactly the React features it needs, and by letting a
developer extract and share stateful logic as a plain function, a
custom hook, with no wrapper component and no change to the
component tree at all.

## 3. Forces

The pattern balances the following competing pressures.

- **Logic reuse with zero tree overhead.** Favored. A custom hook
  shares stateful logic across components with no wrapper component,
  no extra nesting, and no prop collision risk, unlike a Higher-Order
  Component or a Render Prop.
- **Simplicity of the function-component mental model.** Favored. A
  component using only hooks is a plain function, with no `this`
  binding, no constructor, and no lifecycle methods split across
  several separately named callbacks.
- **Rule enforcement outside the type system.** Sacrificed. Hooks
  must be called in the same order on every render, and only from a
  function component or another hook, a constraint the language
  itself does not enforce and that needs either discipline or a
  lint rule to catch a violation.
- **Explicit dependency tracking.** Sacrificed unless carefully
  managed. An effect or a memoized value must declare every value it
  depends on, and an incomplete dependency list produces a subtle,
  hard-to-spot bug rather than a compile error.

## 4. Applicability and non-applicability

Reach for Hooks when the following hold.

- The codebase targets React 16.8 or later, and new components are
  being written as function components rather than classes.
- Stateful logic needs to be shared across components with no extra
  wrapper layer in the rendered tree, the case a custom hook serves
  better than a Higher-Order Component or a Render Prop.
- A component needs to opt into a specific React capability, local
  state, a side effect, context, a ref, without paying for the
  ceremony of a full class component.

Do NOT reach for Hooks in these cases, and the reason matters more
than the rule.

- **The codebase's own dependencies still require class components**,
  such as an older lifecycle method a hook has no equivalent for, or
  an error boundary, which as of this writing still needs a class
  component in React.
- **The logic genuinely needs to intercept a component's props before
  they reach it**, rather than being called from inside the
  component, the specific shape a Higher-Order Component or a Render
  Prop still serves better.
- **A team has not yet adopted and enforced the Rules of Hooks**,
  since a violation, calling a hook conditionally or inside a loop,
  produces state corruption that is easy to introduce and hard to
  debug without a lint rule actively catching it.

## 5. Structure

Hooks have two structural parts.

- **A built-in hook**, one of React's own functions, `useState`,
  `useEffect`, `useContext`, `useRef`, and others, each granting a
  function component access to a specific React capability.
- **A custom hook**, an ordinary function, conventionally named
  starting with `use`, that calls one or more built-in hooks
  internally and returns whatever value or values the consuming
  component needs, letting the internal composition of built-in
  hooks be reused across many components with no wrapper.

## 6. ASCII structure diagram

```
    Function component
    - calls useState() for local state
    - calls useEffect() for a side effect
    - calls a custom hook, useSubscription(), for shared logic

              |
              v  useSubscription() internally calls

    Custom hook (useSubscription)
    - calls useState() for its own internal state
    - calls useEffect() to set up and tear down the subscription
    - returns the current subscription value

              |
              v  ultimately reaches

    React's built-in hooks (useState, useEffect, ...)
    - hold state and effects per component instance, in call order
```

## 7. Dynamics

The trace below shows a component using a custom hook that wraps a
subscription, from mount through a data update to unmount.

```
Mount

CommentList renders
   |-- calls useSubscription(source) (a custom hook)
   |     |-- calls useState() internally, initial value = null
   |     |-- calls useEffect() internally, subscribes to source
   |<-- useSubscription returns null (the initial value)
   |-- CommentList renders with no data yet

Data update

subscription source emits a new value -------------------------->|
   |                                                               |-- the effect's own
   |                                                               |   handler calls the
   |                                                               |   hook's internal
   |                                                               |   setState
   |<-- CommentList re-renders --------------------------------------|
   |-- calls useSubscription(source) again
   |<-- useSubscription returns the new value
   |-- CommentList renders with the new data

Unmount

CommentList unmounts
   |-- React runs useEffect's cleanup function
   |-- the subscription is torn down
```

## 8. Implementation variants

**Built-in state and effect hooks used directly.** The simplest form,
a component calling `useState` and `useEffect` directly with no
custom hook, appropriate when the logic is used by exactly one
component and has no reuse need.

**Custom hooks for shared stateful logic.** A plain function starting
with `use`, internally composing one or more built-in hooks, and
returned to any component that calls it, the variant that replaces
most of what Higher-Order Components and Render Props previously
served, with no wrapper component in the rendered tree.

**Reducer-based state with `useReducer`.** For state whose next value
depends on the previous value through several distinct actions rather
than a single set call, `useReducer` centralizes the update logic in
one reducer function, closer in shape to how a class component's
`setState` with a function argument, or an external state library,
manages complex state transitions.

**Memoization hooks, `useMemo` and `useCallback`.** Used to stabilize
a computed value or a function reference across renders where its own
dependencies have not changed, directly addressing the same
inline-function re-render cost discussed for Render Props in the
related pattern, since a memoized function reference passed as a
prop, or into a hook's own dependency array, avoids triggering
unnecessary downstream work.

## 9. Known production uses

**React's own official introduction and documentation.** The React
team's blog post announcing the feature states plainly. "Hooks let
you use state and other React features without writing a class,"
shipped in React 16.8, released 6 February 2019, explicitly framed as
letting a developer "build your own Hooks to share reusable stateful
logic between components." React Blog, React v16.8.0, 6 February
2019, https://legacy.reactjs.org/blog/2019/02/06/react-v16.8.0.html,
verified 2026-08-21.

**SWR, Vercel's data-fetching library.** The SWR README states its
own identity directly. "SWR is a React Hooks library for data
fetching," built entirely around its `useSWR` hook as the library's
sole primary API, a concrete, widely used example of an entire
library designed around the custom-hook variant from dimension 8.
Vercel, SWR README, vercel/swr, https://github.com/vercel/swr,
verified 2026-08-21.

## 10. Consequences

Positive.

- Stateful logic shares across components as a plain function, a
  custom hook, with no wrapper component, no prop collision risk, and
  no extra layer in the rendered tree.
- A component using only hooks is written as a plain function, with
  no class ceremony, no `this` binding, and its related logic for one
  concern grouped together rather than split across separately named
  lifecycle methods.
- The React ecosystem has converged on hooks as the default
  composition mechanism, so a codebase using them aligns with the
  majority of current documentation, libraries, and hiring
  expectations.

Negative.

- Hooks must be called in the same order on every render, a
  constraint the JavaScript language itself does not enforce, and a
  violation produces state corruption that is easy to introduce
  accidentally and can be hard to trace back to its cause.
- An effect's or a memoized value's dependency list must be kept
  accurate by hand unless tooling assists, and an incomplete list
  produces a subtle bug, a stale closure, rather than a visible error.
- Some capabilities, an error boundary being the clearest example,
  still have no hook equivalent as of this writing, meaning a
  codebase built entirely on hooks may still need an occasional class
  component for those specific cases.

## 11. Failure modes and misuse

**Calling a hook conditionally or inside a loop.** Symptom. A
component's state becomes corrupted or associated with the wrong
piece of UI after a re-render, and the bug appears intermittently
depending on which branch executed. Cause. React associates each
hook's state with its call order within a component, and calling a
hook inside an `if` block or a loop changes that order between
renders, breaking the association. Fix. Call every hook on every
render with no branching around the call itself, at the top level of
the component or another hook, and push the conditional logic inside
the hook's own body instead.

**An incomplete dependency array capturing a stale value.** Symptom.
An effect or a memoized callback uses an outdated value from a
previous render, even after the actual value has changed. Cause. A
value referenced inside the effect or callback was omitted from its
dependency array, so React does not know it should recompute when
that value changes, and the closure keeps referencing the value from
whichever render it was created in. Fix. Include every value the
effect or callback references in its dependency array, using
automated lint tooling to catch an incomplete list before it ships.

**Reaching for `useEffect` to synchronize derived state that could be
computed directly during render.** Symptom. A component renders
twice for what should be a single state change, once with the stale
derived value and once after an effect updates it, adding
unnecessary render passes and complexity. Cause. Storing a value in
state and syncing it from an effect when the value could simply be
computed inline from existing props or state during render. Fix.
Compute the derived value directly in the component's body, with no
`useState` or `useEffect` involved, reserving effects for genuine
synchronization with an external system.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Hooks | Higher-Order Component | Render Props | Class components (pre-Hooks) |
|---|---|---|---|---|
| Logic reuse with zero tree overhead | Highest, a custom hook adds no component | Lower, adds a wrapper component per use | Lower, adds JSX nesting per use | Not applicable, class methods do not share across components without a HOC or render prop |
| Simplicity of the component mental model | High, a plain function with no `this` | Moderate, still class-shaped for the wrapper | Moderate, function props but still class-shaped wrapping | Lower, `this` binding and split lifecycle methods |
| Compile-time enforcement of correct usage | Weak on its own, needs lint tooling | Not applicable | Not applicable | Not applicable |
| Fit in a modern, actively maintained codebase | Strong, the current default | Weak, largely superseded | Weak, largely superseded | Weak, largely superseded for new code |
| Coverage of every React capability | Strong but incomplete, no hook error boundary yet | Full, any lifecycle method is available | Full, any lifecycle method is available | Full, the original mechanism |

Reading of the table. Hooks win for the overwhelming majority of
modern React work, achieving logic reuse with the least structural
overhead of any alternative, at the cost of a discipline the type
system does not enforce on its own. A Higher-Order Component or a
class component remains genuinely necessary only for the narrow
cases dimension 4 names, most notably error boundaries, where no
hook equivalent currently exists.

## 13. Related and incompatible patterns

- **Render Props.** The pattern Hooks most directly supersede for
  general logic sharing, achieving the same reuse with no function
  prop and no JSX nesting cost.
- **Higher-Order Component.** The other pattern Hooks most directly
  supersede for general logic sharing, achieving the same reuse with
  no wrapper component and no prop-collision risk.
- **Compound Components.** A related but distinct composition
  pattern, addressing sibling arrangement through markup and shared
  context rather than the state-and-effect concerns hooks address
  directly, and often implemented using `useContext` internally.
- **Provider Pattern.** A closely related pattern for supplying
  shared values down a component tree, most often consumed through
  the `useContext` hook, making the two patterns commonly used
  together.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a codebase still primarily using class
components, Higher-Order Components, or Render Props.

1. Confirm the codebase's React version is 16.8 or later, upgrading
   first if it is not.
2. Convert one class component to a function component, replacing its
   `this.state` and `setState` calls with `useState`, and its
   lifecycle methods with an equivalent `useEffect`.
3. Where several components share the same stateful logic through a
   Higher-Order Component or a Render Prop, extract that logic into a
   custom hook, and migrate each consumer to call the hook directly.
4. Add or enable a hooks-specific lint rule that enforces the two
   Rules of Hooks, calling hooks with no branching around the call
   and only from a function component or another hook, catching a
   violation before it ships.
5. Confirm behavior is unchanged after each migration with the
   component's existing test suite before moving to the next one.

Removing the pattern is rarely warranted, since Hooks are the current
default mechanism with no broadly adopted successor as of this
writing. The narrow exception is migrating a specific hook-based
component back to a class component when it genuinely needs a
capability with no hook equivalent, an error boundary being the
clearest case.

1. Confirm the specific capability needed truly has no hook
   equivalent, rather than assuming one does not exist.
2. Convert only the specific component that needs the capability,
   leaving the rest of the codebase on hooks.
3. Keep the converted component's external interface, its own props
   and behavior, unchanged, so consumers require no changes.

## 15. Testing and verification

Easier because of the pattern.

- A custom hook's own logic can be tested in isolation using a
  hook-testing utility that renders it outside any specific
  component, independent of what any real consumer renders.
- A function component using only hooks can often be tested by
  simply rendering it and asserting its output, with no need to
  instantiate a class or manage `this` binding in the test itself.

Harder because of the pattern.

- A missing or incorrect dependency array is invisible to most tests
  unless the test specifically exercises the scenario where the
  omitted value actually changes, since the stale-closure bug only
  manifests under that specific condition.
- Testing a component that composes several custom hooks together
  needs care to distinguish a failure in one hook's own logic from a
  failure in how the component combines their results, since the
  hooks are not visually separated the way distinct props or wrapper
  components would be.

Techniques that apply.

- **Isolated custom-hook test.** Render a custom hook outside any
  specific component using a hook-testing utility, and assert its
  returned value and behavior directly, independent of any real
  consumer.
- **Dependency-change regression test.** Explicitly change a value an
  effect or a memoized value depends on during a test, and assert the
  effect re-runs or the memoized value recomputes, guarding against
  the second failure mode in dimension 11.
- **Rendered-output component test.** Render the full function
  component and assert its output at each stage of its lifecycle,
  mount, an interaction, and unmount, confirming the hooks compose
  correctly together.
- **Lint-rule enforcement as a test.** Run the hooks-specific lint
  rule as part of the test suite itself, so a violation of the Rules
  of Hooks fails the build the same way a failing assertion would.

## 16. Observability signals

Hooks are a source-level composition mechanism with no independent
runtime footprint of their own beyond the rendering and effects a
component already performs, and inventing a dedicated production
signal purely for hooks as a concept would be dishonest. Two things
are worth watching in a codebase that uses them heavily.

What to record.

- The frequency and duration of effects that perform expensive work,
  a network request or a large computation, since an effect that
  re-runs more often than intended is a concrete, measurable
  performance cost worth tracking.
- Lint-rule violation counts for the hooks-specific rule over time,
  since a rising count signals a codebase accumulating exactly the
  kind of bug dimension 11's first failure mode describes.

A healthy state. Effects re-run only when their genuine dependencies
change, and the hooks lint rule reports zero violations across the
codebase.

A failing state. An effect that re-runs on every render regardless of
its dependencies, pointing at either a missing memoization or an
overly broad dependency, or a lint rule that is disabled or
consistently ignored rather than fixed.

## 17. Security and privacy implications

Hooks are close to neutral for security, being a composition
mechanism rather than a data-handling one, and inventing a dedicated
attack surface here would be dishonest. One practical implication is
worth naming.

**An effect that reads sensitive data and syncs it to an external
system, logging, analytics, a third-party script, needs the same
review any other code path handling that data would need.** Because
`useEffect` is a general-purpose escape hatch for side effects, it is
exactly the place a sensitive value can leave the component
boundary, intentionally or by accident, through a call to an external
service. this is not different from any other code path handling
sensitive data in principle, but it is worth naming explicitly, since
an effect's side-effecting nature makes it an easy place to overlook
during a security review focused mainly on rendered output.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models the classic
custom-hook shape the way React code structures it, kept free of JSX
and the react package so the sample compiles as plain TypeScript,
using a plain object to model the hook-like state-and-effect
contract. Python shows the same conceptual split using a minimal,
framework-agnostic class exposing a comparable subscribe-and-read
interface, since Python has no single dominant UI-component framework
the way TypeScript has React. Swift shows the pattern using
SwiftUI's own `@State` property wrapper and a custom `ObservableObject`
class, SwiftUI's closest idiomatic equivalent to a React hook granting
a view access to state and a side effect. Java, Go, and Rust are
omitted, since none has a dominant, idiomatic UI-component framework
this specifically frontend pattern maps to as directly as React and
SwiftUI do.

### TypeScript

```typescript
interface HookState<T> {
  value: T;
  cleanup: () => void;
}

function useSubscription<T>(
  source: { subscribe: (cb: (value: T) => void) => () => void },
  initial: T
): HookState<T> {
  let current = initial;
  const cleanup = source.subscribe((value) => {
    current = value;
  });
  return { value: current, cleanup };
}

class Source {
  private listeners: ((value: string) => void)[] = [];

  subscribe(cb: (value: string) => void): () => void {
    this.listeners.push(cb);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== cb);
    };
  }

  emit(value: string): void {
    this.listeners.forEach((cb) => cb(value));
  }
}

const source = new Source();
const state = useSubscription(source, "");
source.emit("first comment");
console.log(state.value);
state.cleanup();
```

### Python

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class HookState:
    value: str
    cleanup: Callable[[], None]


class Source:
    def __init__(self) -> None:
        self.listeners: list[Callable[[str], None]] = []

    def subscribe(self, callback: Callable[[str], None]) -> Callable[[], None]:
        self.listeners.append(callback)

        def unsubscribe() -> None:
            self.listeners.remove(callback)

        return unsubscribe

    def emit(self, value: str) -> None:
        for listener in self.listeners:
            listener(value)


def use_subscription(source: Source, initial: str) -> HookState:
    current = initial

    def on_value(value: str) -> None:
        nonlocal current
        current = value

    cleanup = source.subscribe(on_value)
    return HookState(current, cleanup)


if __name__ == "__main__":
    source = Source()
    state = use_subscription(source, "")
    source.emit("first comment")
    print(state.value)
    state.cleanup()
```

### Swift

```swift
import Combine

final class SubscriptionModel: ObservableObject {
    @Published var value: String = ""
    private var cancellable: AnyCancellable?

    func subscribe(to publisher: AnyPublisher<String, Never>) {
        cancellable = publisher.sink { [weak self] newValue in
            self?.value = newValue
        }
    }
}

let subject = PassthroughSubject<String, Never>()
let model = SubscriptionModel()
model.subscribe(to: subject.eraseToAnyPublisher())
subject.send("first comment")
print(model.value)
```

## 18. References

1. React Blog. "React v16.8.0". 6 February 2019.
   https://legacy.reactjs.org/blog/2019/02/06/react-v16.8.0.html
   Verified 2026-08-21. Source of the first_described lineage claim
   and the defining sentence.
2. Vercel. "SWR README". vercel/swr.
   https://github.com/vercel/swr
   Verified 2026-08-21. Source for the production use in dimension 9.
