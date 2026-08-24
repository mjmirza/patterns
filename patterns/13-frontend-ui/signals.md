---
name: Signals
slug: signals
family: 13-frontend-ui
category: State Management
aliases: [Fine-Grained Reactivity, Reactive Primitives]
first_described: "Preact Signals, 6 September 2022"
maturity: established
related: [hooks, provider-pattern, higher-order-component, render-props]
incompatible_with: []
verified: 2026-08-21
---

# Signals

## 1. Name, aliases, and lineage

The canonical name is Signals, a reactive primitive that has appeared
under this name across several frontend frameworks in roughly the
same period. The Preact team's announcement post defines the core
mechanism directly. "a signal is an object with a `.value` property
that holds some value," presented as a way of expressing state that
keeps an application fast regardless of how complex it gets. Preact's
Signals were announced 6 September 2022.

The alias **Fine-Grained Reactivity** names the underlying mechanism
signals provide, updates that reach only the specific piece of the UI
that reads a changed value rather than re-rendering an entire
component. **Reactive Primitives** names the broader category of
small, composable reactive building blocks that signals, and similar
constructs across other frameworks, belong to.

## 2. Problem and context

A component-based UI framework built on a virtual DOM diff and
re-render cycle, such as React, re-runs an entire component function
whenever any piece of its state changes, then diffs the result
against the previous render to find what actually changed in the DOM.
For frequently updating values, this re-run-then-diff cycle repeats
work a framework could otherwise avoid entirely if it knew, in
advance, precisely which piece of the UI a specific value change would
affect. Signals solve this by making a value itself the unit of
reactivity. a signal wraps a value, and any place that reads the
signal's `.value` becomes a subscriber, so updating the signal updates
exactly the subscribers that read it, with no need to re-run an
entire enclosing component function to discover what changed.

## 3. Forces

The pattern balances the following competing pressures.

- **Update precision.** Favored. A signal update reaches exactly the
  places that read it, whether that is a single DOM text node or a
  small computed value, without re-running an entire component
  function to discover what changed.
- **No manual memoization needed.** Favored. Preact's own
  announcement states this directly. "Signals are fast by default
  without requiring memoization or tricks throughout your app,"
  removing the discipline burden the dependency-array cost from Hooks
  imposes.
- **A new mental model beyond plain function-component state.**
  Sacrificed. A signal is read via `.value` rather than a plain
  variable, and the subscription mechanism operates differently from
  the render-and-diff cycle most component-based frameworks already
  use, adding a second reactivity model for a team to learn.
- **Interop with the surrounding component-render model.** Sacrificed
  unless the framework has first-class support. A signal read outside
  a reactive context does not automatically trigger a re-render,
  which can silently produce a UI that never updates unless the
  framework's own primitives detect the read correctly.

## 4. Applicability and non-applicability

Reach for Signals when the following hold.

- Frequent, fine-grained value updates need to reach a narrow part of
  the UI without paying the cost of re-running an entire component
  function on each update.
- The framework in use has first-class signal support, either built
  in, such as Solid's `createSignal`, or via an official integration,
  such as Preact's `@preact/signals-react` for React.
- A team is willing to adopt a `.value`-based reactive model
  alongside, or instead of, the framework's default state primitive.

Do NOT reach for Signals in these cases, and the reason matters more
than the rule.

- **The framework has no first-class signal support**, using an
  unofficial or community-maintained signal library on a framework
  that was not designed around fine-grained reactivity can produce
  subtle interop bugs where a signal read outside its reactive
  context silently fails to trigger an update.
- **State updates are infrequent or the component tree is shallow**,
  the fine-grained update precision signals provide has little
  benefit when a full component re-render is already cheap, and the
  added mental model cost is not repaid.
- **A team has not yet learned the reactive-context rules a specific
  signal implementation enforces**, since reading a signal outside
  the places a given framework tracks as reactive is a real,
  documented failure mode, covered in dimension 11.

## 5. Structure

Signals have two structural parts.

- **The signal itself**, a small reactive container exposing a
  `.value` property, created once and held for as long as the state
  it represents is needed.
- **A subscriber**, any place that reads the signal's value inside a
  context the framework tracks, a rendered piece of UI, a computed
  value, or an effect, automatically re-evaluated when the signal's
  value changes.

## 6. ASCII structure diagram

```
count = signal(0)              (the signal itself)

          |
          v  read inside a reactive context

<span>{count}</span>          (a subscriber, a UI fragment)
doubled = computed(() => count.value * 2)
                               (a subscriber, a derived value)

          |
          v  count.value = 1

Only the subscribers that actually read count re-evaluate.
A sibling component that never reads count does not re-render.
```

## 7. Dynamics

The trace below shows a signal's value changing and only its actual
subscribers updating in response.

```
Mount

count = signal(0)
   |-- <span>{count}</span> subscribes, renders "0"
   |-- a sibling <p>Unrelated content</p> renders, never reads count

Value change

count.value = 1
   |-- the signal notifies its subscribers directly
   |-- <span>{count}</span> re-evaluates, renders "1"
   |-- the sibling <p>Unrelated content</p> does not re-render,
       because it never subscribed to count
```

## 8. Implementation variants

**Framework-native signals.** A framework built around signals from
the start, Solid's `createSignal` being the clearest example, where
signals are the primary state primitive and the framework's own
compiler and runtime are designed around fine-grained subscription
tracking.

**Signals layered onto an existing framework.** An official or
well-supported integration adds signals to a framework not originally
built around them, such as Preact's own signals library and its React
adapter, letting specific, hot parts of a component tree opt into
fine-grained updates without rewriting the whole application.

**Computed signals.** A signal whose value is derived from one or
more other signals, automatically recalculating and notifying its own
subscribers whenever any signal it reads changes, composing signals
the way a memoized derived value composes plain state.

**Effects reacting to signal changes.** A side effect that reads one
or more signals and re-runs whenever any of them changes, the signal
equivalent of a dependency-array-driven effect, but with the
dependencies tracked automatically from which signals were actually
read rather than declared by hand.

## 9. Known production uses

**Preact's own Signals announcement.** The Preact team's blog post
defines signals directly. "a signal is an object with a `.value`
property that holds some value," states plainly that "Signals are
fast by default without requiring memoization or tricks throughout
your app," and that a signal "can be updated without re-rendering the
components they've been passed through, since components see the
signal and not its value." Preact Blog, Introducing Signals, 6
September 2022, https://preactjs.com/blog/introducing-signals/,
verified 2026-08-21.

**SolidJS, where signals are the primary state primitive.** The
Solid documentation states directly. "Signals are the primary means
of managing state in your Solid application. They provide a way to
store and update values, and are the foundation of reactivity in
Solid," created via `createSignal`, which "returns a pair of
functions, a getter function, and a setter function," a concrete,
production framework built entirely around the signal as its
foundational reactive primitive rather than an addition layered onto
an existing model. SolidJS documentation, Signals,
https://docs.solidjs.com/concepts/signals, verified 2026-08-21.

## 10. Consequences

Positive.

- An update reaches exactly the subscribers that read the changed
  signal, without re-running an entire enclosing component function
  to discover what changed.
- Signals are fast without hand-written memoization, removing the
  dependency-array discipline burden that a Hooks-based approach
  needs for equivalent update precision.
- A computed signal or an effect automatically tracks exactly which
  signals it reads, with no separately maintained dependency list to
  keep accurate by hand.

Negative.

- A `.value`-based reactive model is a second mental model alongside
  a framework's existing component-render model, adding a genuine
  learning cost for a team new to it.
- Reading a signal outside a context the framework tracks as reactive
  does not automatically trigger a re-evaluation, and the resulting
  bug, a UI that silently never updates, can be hard to trace back to
  its cause.
- Adopting signals on a framework not originally designed around them
  needs an official or well-supported integration, since an ad hoc
  implementation risks subtle interop bugs with the framework's
  existing render cycle.

## 11. Failure modes and misuse

**Reading a signal's value outside a tracked reactive context.**
Symptom. A piece of UI renders the signal's initial value once and
never updates again, even though the signal's value genuinely
changes. Cause. The value was read in a plain, untracked context, a
destructured variable captured once rather than a live read inside
the framework's reactive scope, so no subscription was ever
established. Fix. Read the signal's `.value` directly inside the
reactive context the framework tracks, rather than destructuring or
copying it into a plain variable ahead of time.

**Mixing signal-based and component-render-based state for the same
value.** Symptom. A value appears to update in one part of the UI but
not another, or updates inconsistently depending on which mechanism a
given component happens to use. Cause. The same conceptual piece of
state is represented once as a signal and once as ordinary
component-render state, or a signal's value is copied into
component-render state at one point in time and never kept in sync
afterward. Fix. Pick one representation for a given piece of state,
the signal or the framework's native state primitive, and have every
consumer read from that single source, rather than maintaining a
parallel, easily-desynchronized copy.

**Creating a new signal on every render instead of once.** Symptom.
A component's reactive subscriptions reset unexpectedly, losing any
accumulated state the signal was meant to persist across renders.
Cause. The signal is constructed inline inside the component's
render path rather than once, outside it or in a stable
initialization step, so a fresh signal instance is created every time
the surrounding function runs. Fix. Create the signal once, outside
the render path or in whatever stable initialization mechanism the
framework provides, and reuse the same instance across subsequent
renders.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Signals | Hooks (useState) | The Provider Pattern | Class-component state |
|---|---|---|---|---|
| Update precision on a value change | Highest, only actual subscribers re-evaluate | Coarse, the whole component function re-runs | Coarse, every context consumer re-renders | Coarse, the whole component re-renders |
| Manual memoization needed for update precision | None, tracked automatically | Yes, useMemo and useCallback by hand | Yes, the value object must be memoized | Not applicable, no built-in fine-grained mechanism |
| A second mental model beyond the framework's default | Yes, `.value` reads and a distinct reactive scope | No, the framework's own default primitive | No, the framework's own default primitive | No, the framework's own default primitive |
| Framework support required | Needs first-class or well-supported integration | Universal in any Hooks-capable framework | Universal wherever context exists | Universal in any class-component framework |
| Fit for frequently updating, narrowly scoped values | Strong | Weak without careful manual memoization | Weak, coarse re-render on every change | Weak, coarse re-render on every change |

Reading of the table. Signals win specifically where update
frequency and precision matter enough to justify learning a second
reactive model, and the framework has genuine, well-supported signal
integration. Hooks, the Provider Pattern, and class-component state
all share the same coarse, whole-function-re-run update model, which
is simpler to learn and sufficient for the majority of ordinary
application state, but pays a real cost for state that changes
often and only affects a small, specific part of the UI.

## 13. Related and incompatible patterns

- **Hooks.** The default state primitive in a React-shaped codebase
  that Signals compete with, or, via an official integration, can be
  layered alongside for the specific hot paths that benefit from
  fine-grained updates.
- **Provider Pattern.** A related mechanism for sharing state broadly
  across a component tree, sharing the same coarse re-render cost
  that Signals are specifically designed to avoid, and sometimes
  combined with signals by holding a signal inside a context value.
- **Higher-Order Component.** An older composition mechanism largely
  unrelated to the state-update-precision problem Signals solve,
  addressing behavior sharing across components rather than
  fine-grained reactivity.
- **Render Props.** Another older composition mechanism addressing a
  different problem, sharing rendering control through a function
  prop rather than the value-level reactivity Signals provide.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a codebase experiencing measured, real
performance cost from coarse component re-renders on frequently
updating state.

1. Confirm the framework has first-class or well-supported signal
   integration before adopting the pattern.
2. Identify a specific, measured hot path where a frequently updating
   value currently triggers a broader component re-render than
   necessary.
3. Introduce a signal for that specific value, created once outside
   the render path, and migrate the reads that need fine-grained
   updates to read the signal's `.value` inside a tracked reactive
   context.
4. Confirm no consumer reads the signal outside a tracked context,
   guarding against the first failure mode in dimension 11.
5. Measure the actual re-render or update-precision improvement
   before expanding signal usage beyond the specific hot path
   identified in step 2.

Removing the pattern when it stops earning its place, most relevant
when a signal-based value's update frequency has dropped, or when the
second-mental-model cost has proven not worth the update-precision
benefit in practice.

1. Confirm the value genuinely no longer needs fine-grained update
   precision, rather than assuming so without measurement.
2. Migrate the value back to the framework's native state primitive,
   `useState` or an equivalent, keeping its external interface
   unchanged so consumers require minimal changes.
3. Remove the signal only after every consumer has migrated off it.

## 15. Testing and verification

Easier because of the pattern.

- A signal's own value and update behavior can be tested directly,
  reading and writing `.value` and asserting the result, entirely
  independent of any specific rendered UI.
- A computed signal's derivation logic can be tested by setting its
  underlying signals and asserting the computed value updates
  correctly, with no need to render any component at all.

Harder because of the pattern.

- The first failure mode in dimension 11, a signal read outside a
  tracked reactive context, is invisible to a test that only checks
  the signal's own value updates correctly, since the bug is
  specifically that a subscriber never got created, not that the
  signal itself misbehaved.
- Testing that only the expected subscribers re-evaluate on a signal
  change, and no others, needs render or evaluation-count
  instrumentation that a simple output assertion does not provide by
  itself.

Techniques that apply.

- **Isolated signal-value test.** Read and write a signal's `.value`
  directly and assert the resulting value, independent of any
  rendered UI.
- **Computed-signal derivation test.** Set the underlying signals a
  computed value depends on and assert the computed value updates
  correctly, with no component rendering involved.
- **Tracked-context regression test.** Render a consumer that reads a
  signal inside its actual reactive context, change the signal, and
  assert the consumer updates, guarding against the first failure
  mode in dimension 11.
- **Subscriber-count test.** Instrument a component to count its own
  re-evaluations, change an unrelated signal, and assert it did not
  re-evaluate, confirming the fine-grained update behavior a specific
  implementation actually delivers.

## 16. Observability signals

Signals are a source-level reactivity mechanism with no independent
runtime footprint of their own beyond the updates they already
perform, and inventing a dedicated production signal purely for the
pattern would be dishonest. Two things are worth watching in a
codebase that uses them heavily.

What to record.

- The frequency of updates to a specific signal relative to how often
  its subscribers actually re-evaluate, since a mismatch, subscribers
  re-evaluating far more often than the underlying signal actually
  changes, points at an unintended subscription somewhere in the
  reactive graph.
- Instances of a UI that appears not to update, since that is the
  concrete symptom of the first failure mode in dimension 11, a
  signal read outside its tracked reactive context.

A healthy state. Subscriber re-evaluation counts track proportionally
with actual signal value changes, and no part of the UI silently
fails to reflect a signal's current value.

A failing state. A subscriber re-evaluating far more often than the
signal it reads actually changes, or a reported bug where a piece of
UI never updates despite the underlying value genuinely changing,
pointing at an untracked read.

## 17. Security and privacy implications

Signals are close to neutral for security, being a state-reactivity
mechanism rather than a data-handling one, and inventing a dedicated
attack surface here would be dishonest. One practical implication is
worth naming.

**A signal holding sensitive data is readable by any code that has a
reference to it, with no access control beyond ordinary variable
scoping.** Because a signal is a plain object exposing a `.value`
property, any code that holds a reference to the signal can read or
write it, the same as any other shared mutable reference. this is not
different from any other shared state mechanism in principle, but it
is worth naming explicitly, since a signal's global or widely shared
nature, the very property that makes it convenient, is exactly what
makes an accidentally over-broadly shared reference to sensitive data
easy to overlook during a security review.

## 18. References

1. Preact Blog. "Introducing Signals". 6 September 2022.
   https://preactjs.com/blog/introducing-signals/
   Verified 2026-08-21. Source of the defining sentence and the
   first_described lineage.
2. SolidJS documentation. "Signals".
   https://docs.solidjs.com/concepts/signals
   Verified 2026-08-21. Source for the production use in dimension 9.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models the classic
signal-plus-subscriber shape the way Preact and Solid structure it,
kept free of JSX and any specific framework's package so the sample
compiles as plain TypeScript, using a minimal class to model the
value-plus-subscription contract. Python shows the same conceptual
split using a minimal, framework-agnostic class exposing a comparable
get-set-and-notify interface, since Python has no single dominant
signals-based UI framework the way TypeScript has Solid and Preact.
Swift shows the pattern using SwiftUI's own `@Observable` macro, the
current, first-class SwiftUI mechanism for fine-grained,
property-level reactivity, closely analogous to a signal's
per-property subscription model. Java, Go, and Rust are omitted,
since none has a dominant, idiomatic UI-component framework this
specifically frontend pattern maps to as directly as TypeScript and
Swift do.

### TypeScript

```typescript
type Subscriber = () => void;

class Signal<T> {
  private _value: T;
  private subscribers: Set<Subscriber> = new Set();

  constructor(initial: T) {
    this._value = initial;
  }

  get value(): T {
    return this._value;
  }

  set value(next: T) {
    this._value = next;
    this.subscribers.forEach((subscriber) => subscriber());
  }

  subscribe(subscriber: Subscriber): void {
    this.subscribers.add(subscriber);
  }
}

const count = new Signal(0);

count.subscribe(() => {
  console.log("count is now " + count.value);
});

count.value = 1;
count.value = 2;
```

### Python

```python
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class Signal(Generic[T]):
    def __init__(self, initial: T) -> None:
        self._value = initial
        self._subscribers: list[Callable[[], None]] = []

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, next_value: T) -> None:
        self._value = next_value
        for subscriber in self._subscribers:
            subscriber()

    def subscribe(self, subscriber: Callable[[], None]) -> None:
        self._subscribers.append(subscriber)


if __name__ == "__main__":
    count: Signal[int] = Signal(0)

    def on_change() -> None:
        print(f"count is now {count.value}")

    count.subscribe(on_change)
    count.value = 1
    count.value = 2
```

### Swift

```swift
import Observation

@Observable
final class Counter {
    var count: Int = 0
}

let counter = Counter()
counter.count = 1
counter.count = 2
print("count is now " + String(counter.count))
```
