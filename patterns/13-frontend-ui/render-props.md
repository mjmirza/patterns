---
name: Render Props
slug: render-props
family: 13-frontend-ui
category: Component Composition
aliases: [Render Prop Pattern, Function as Child, Children as a Function]
first_described: "Jackson 2017"
maturity: established
related: [compound-components, higher-order-component, container-presentational, hooks]
incompatible_with: [hoc-wrapper-hell]
verified: 2026-08-21
---

# Render Props

## 1. Name, aliases, and lineage

The canonical name is Render Props, describing a component that
accepts a function as one of its props and calls that function to
decide what to render, rather than rendering fixed markup itself.
Michael Jackson named and popularised the pattern in "Use a Render
Prop!", published 18 September 2017
(https://medium.com/@mjackson/use-a-render-prop-50de598f11ce, verified
2026-08-21), which states plainly. "a render prop is a function prop
that a component uses to know what to render." The article presented
the pattern as a direct alternative to Higher-Order Components and
mixins for sharing behaviour between components.

The alias **Function as Child** and **Children as a Function** name the
specific variant where the function is passed as the component's
`children` rather than under a named prop such as `render`, which
Jackson's own article notes is the identical pattern under a different
prop name.

## 2. Problem and context

A piece of stateful or side-effecting logic, tracking mouse position,
managing a form field's validation state, fetching data, is often
needed by more than one component, each of which wants to render that
shared behaviour differently. Duplicating the logic in every component
that needs it is wasteful and error-prone. wrapping it in a Higher-
Order Component works, but couples the logic to a specific way of
injecting props, and stacking several HOCs to combine several pieces of
shared behaviour produces a hard-to-trace wrapper chain, where a prop's
origin is not visible from the component that ultimately renders it.

Render Props solves this by inverting the relationship. instead of a
wrapper injecting props into a fixed child, the component holding the
shared logic accepts a function as a prop and calls that function with
whatever data or state it manages, letting the caller decide exactly
what to render with that data, inline, at the exact call site, with no
wrapper chain and no injected props whose origin has to be traced back
through several layers.

## 3. Forces

The pattern balances the following competing pressures.

- **Rendering flexibility.** Favoured. The consumer decides exactly
  what to render with the shared state, inline at the call site, rather
  than being constrained to whatever a wrapper component injects.
- **Traceability.** Favoured, compared to a stack of Higher-Order
  Components. Because the function is called directly rather than
  props being injected through a wrapper chain, a reader can see
  exactly what a render prop's data becomes at the point it is used.
- **Nesting depth in JSX.** Sacrificed. Using several render props
  together nests each one's function inside the previous one's call,
  producing a visibly deeper indentation level for every additional
  shared behaviour composed this way, sometimes called callback hell's
  JSX cousin.
- **Explicitness over convention.** Favoured. Nothing about how the
  data reaches the rendered markup is implicit or based on naming
  convention, the function's own parameters are the entire contract.

## 4. Applicability and non-applicability

Reach for Render Props when the following hold.

- Shared logic needs to be reused across several components that each
  render the resulting state or data differently, and inline
  flexibility at the call site is worth more than a fixed rendering
  contract.
- The codebase does not have Hooks or an equivalent built-in mechanism
  available, or the shared logic genuinely needs to control WHEN and
  HOW its consumer renders, not only supply values to it.
- A library needs to expose behaviour, not markup, to its consumers,
  the way Downshift exposes autocomplete behaviour while leaving every
  visual decision to the library's user.

Do NOT reach for Render Props in these cases, and the reason matters
more than the rule.

- **The codebase already has Hooks or an equivalent built-in
  mechanism**, a custom hook achieves the identical logic-sharing
  benefit with no extra nesting level in the rendered markup, and is
  the modern default choice in a Hooks-capable codebase.
- **Composing more than two or three render props in one place**, the
  resulting nested function calls become genuinely hard to read, and
  either a custom hook or a combined, purpose-built component serves
  the need with far less visual nesting.
- **The shared behaviour has exactly one rendering shape across every
  consumer**, if nobody ever renders the shared state differently, a
  plain component with no render-prop indirection is simpler and needs
  no function to be passed at all.

## 5. Structure

A Render Props component has two structural parts.

- **The state-owning component**, holding whatever data, logic, or side
  effects the pattern exists to share, with no markup of its own beyond
  calling a function prop with the current state.
- **The function prop**, most often named `render` or passed directly
  as `children`, supplied by the consumer, receiving the shared state
  as its argument and returning whatever markup the consumer wants for
  that state.

The state-owning component calls the function on every render, passing
the current state, and renders whatever the function returns directly.

## 6. ASCII structure diagram

```
    MouseTracker (state-owning component)
    - tracks mouse position internally
    - on every render, calls this.props.render(position)
    - renders whatever that call returns

              |
              v  render={(position) => ...}

    Consumer's function
    - receives { x, y } as its argument
    - returns whatever markup the consumer wants for that position,
      a cursor icon, a coordinate readout, a tooltip, anything
```

## 7. Dynamics

The trace below shows a mouse-move event updating the state-owning
component's internal state, which then calls the consumer's function
with the new position on the next render.

```
Mount

MouseTracker mounts, position = { x: 0, y: 0 }
   |-- calls this.props.render({ x: 0, y: 0 })
   |<-- consumer's function returns markup for position (0, 0)
   |-- MouseTracker renders that markup

Mouse movement

browser fires a mousemove event -------------------------->|
   |                                                         |-- MouseTracker's
   |                                                         |   handler updates
   |                                                         |   internal state,
   |                                                         |   position = { x: 42, y: 87 }
   |<-- MouseTracker re-renders -----------------------------|
   |-- calls this.props.render({ x: 42, y: 87 })
   |<-- consumer's function returns markup for the new position
   |-- MouseTracker renders that new markup
```

## 8. Implementation variants

**Named prop, most often `render`.** The consumer passes the function
under an explicit prop name, `render`, so the state-owning component's
call site reads `this.props.render(state)`, and the consumer's JSX
reads `<MouseTracker render={(pos) => ...} />`, making the pattern's
use visible directly in the prop list.

**Children as a function.** The consumer passes the function as the
component's `children`, so the state-owning component calls
`this.props.children(state)` instead, and the consumer's JSX nests the
function directly inside the component's open and close tags rather
than as a named attribute, a stylistic variant Jackson's own article
notes is identical in mechanism.

**Custom-hook replacement, the pattern's modern successor.** Rather
than a component calling a function prop, the shared logic moves into
a custom hook the consumer calls directly, returning the same state a
render prop would have passed, with no extra component or nesting
level in the rendered markup, the specific alternative most
Hooks-capable codebases now reach for by default.

**Library-exposed behaviour with zero rendered markup of its own.** A
variant common in accessible, headless UI libraries, where the
state-owning component renders nothing itself beyond calling its
render prop, existing purely to compute and expose behaviour, letting
the consumer supply one hundred percent of the visual output.

## 9. Known production uses

**The pattern's own originating source.** Michael Jackson's "Use a
Render Prop!" defines the pattern directly. "a render prop is a
function prop that a component uses to know what to render," presented
as a clearer alternative to Higher-Order Components for sharing
behaviour between React components. Michael Jackson, Use a Render
Prop!, 18 September 2017,
https://medium.com/@mjackson/use-a-render-prop-50de598f11ce, verified
2026-08-21.

**Downshift, Kent C. Dodds' accessible autocomplete library.** The
Downshift README describes the library's own core mechanism directly.
"it uses a render prop which gives you maximum flexibility with a
minimal API because you are responsible for the rendering of
everything and you simply apply props to what you're rendering."
Downshift README, downshift-js/downshift,
https://github.com/downshift-js/downshift, verified 2026-08-21.

## 10. Consequences

Positive.

- The consumer decides exactly what to render with the shared state,
  inline at the call site, with no wrapper chain to trace and no
  injected props whose origin is hidden.
- A single state-owning component can serve many visually different
  consumers, each supplying its own function, without the component
  itself needing to know anything about the range of possible
  renderings.
- The function's parameters are the entire contract, so a reader can
  see exactly what data is available at the point it is used, with no
  implicit convention to learn first.

Negative.

- Composing more than a couple of render props in one place nests each
  function inside the previous one's call, producing a visibly deeper,
  harder-to-scan JSX structure with every additional shared behaviour.
- In a codebase with Hooks available, the same sharing benefit is
  achievable with a custom hook and no extra nesting level, which is
  why the pattern is now largely superseded for its original purpose.
- A state-owning component that renders nothing beyond calling its
  render prop needs care to avoid unnecessary re-renders of the
  function's own return value, since a new inline function passed on
  every parent render defeats memoisation the same way an inline object
  or array literal would.

## 11. Failure modes and misuse

**Nesting several render props until the JSX becomes genuinely hard to
scan.** Symptom. A component's return statement grows several levels
of indentation deep, each level belonging to a different render prop's
function, and a reader has to trace matching braces across a wide
vertical span to see the actual rendered markup. Cause. Reaching for
another render prop for each additional piece of shared behaviour
without considering whether the pieces could combine into fewer,
purpose-built components or hooks. Fix. Combine several small render
props into one purpose-built component when they are consistently used
together, or migrate to custom hooks per dimension 8's modern
successor variant, which removes the nesting entirely.

**Passing a new inline function on every render, defeating
memoisation.** Symptom. A state-owning component wrapped in a
memoisation boundary still re-renders on every parent update, even when
its own state has not changed. Cause. The consumer passes a new inline
arrow function as the render prop on every render of the parent, and
because that function is a new value each time, any memoisation
comparing props by reference sees a changed prop even though the
function's actual behaviour is identical. Fix. Define the render
function outside the render path, with `useCallback` or an equivalent
stable reference, so the same function value is passed across renders
when its actual behaviour has not changed.

**Reaching for a render prop in a codebase where a custom hook would
serve identically, with less nesting.** Symptom. A team continues
writing new render-prop components in a codebase that has fully
adopted Hooks, producing nesting the rest of the codebase does not
otherwise have. Cause. Following an older convention out of habit
rather than reassessing which mechanism the codebase's current idioms
actually call for. Fix. Default to a custom hook for new shared logic
in a Hooks-capable codebase, reserving render props for the genuine
cases in dimension 4 where a component, not a hook, is what a consumer
actually needs to receive.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Render Props | Higher-Order Component | A custom hook | Compound Components |
|---|---|---|---|---|
| Rendering flexibility at the call site | High, inline function decides everything | Lower, fixed to whatever the HOC injects | Highest, the consumer's own component renders freely | High, but through markup arrangement rather than a function |
| Traceability of where data comes from | High, visible at the function call | Lower, props arrive from an outer wrapper chain | Highest, values come directly from the hook call | Moderate, implicit through context |
| JSX nesting cost as more behaviours combine | Grows with each additional render prop | Grows with each additional wrapper in the chain | None, hooks compose without adding markup nesting | Low, arrangement rather than nesting |
| Fit in a modern, Hooks-capable codebase | Largely superseded for the general case | Largely superseded for the general case | The default modern choice | Still genuinely useful for markup-arrangement needs |
| Fit for a library exposing pure behaviour with no opinion on rendering | Strong | Moderate | Strong, if the consumer owns the component entirely | Weak, needs several named sub-components |

Reading of the table. Render Props wins when a component genuinely
needs to hand rendering control to its consumer at the exact call site,
and the codebase either lacks Hooks or the shared logic genuinely needs
to be received by a component rather than called from inside one. A
custom hook wins for the general case in any modern, Hooks-capable
codebase, achieving the same sharing with no nesting cost. Higher-Order
Components share the same largely-superseded status as render props for
their original purpose. Compound Components solves a related but
distinct problem, several sibling pieces arranged in markup, rather
than one component receiving a function.

## 13. Related and incompatible patterns

- **Compound Components.** A related but distinct composition pattern,
  addressing how several sibling components share implicit state with
  each other through markup arrangement, rather than how one component
  hands rendering control to a function.
- **Higher-Order Component.** The sibling pattern Michael Jackson's
  originating article presents Render Props as a direct alternative to,
  both solving the same behaviour-sharing problem through different
  mechanisms.
- **Container Presentational.** A related composition pattern
  addressing the separation of logic from rendering within one
  component's own structure, rather than sharing logic across several
  different consumers.
- **Hooks.** The modern successor mechanism that achieves the same
  logic-sharing benefit as Render Props without an extra component or
  any JSX nesting cost, and the pattern most Hooks-capable codebases
  reach for by default today.
- **HOC wrapper hell.** Conflicts by contrast rather than direct
  incompatibility. the specific failure mode, several stacked Higher-
  Order Components with an untraceable prop chain, that Render Props
  was introduced specifically to solve.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a codebase without Hooks where shared logic
needs to be reused across differently-rendering consumers.

1. Identify the shared logic, state, or side effect that several
   components need, and confirm each consumer genuinely wants to render
   the resulting data differently, not identically.
2. Extract the shared logic into a component that owns the state and
   calls a function prop, `render` or `children`, with the current
   state on every render.
3. Migrate each existing consumer to pass its own rendering function,
   confirming the resulting markup matches its previous, duplicated
   implementation.
4. Confirm the render function passed by each consumer is stable across
   renders where its own dependencies have not changed, per the second
   failure mode in dimension 11.
5. Add a test asserting the state-owning component calls its render
   prop with the correct data on state changes, independent of any
   specific consumer's rendering choice.

Removing the pattern when it stops earning its place, most relevant to
a codebase that has adopted Hooks. Signals that it should go include
several render props nested deeply enough to hurt readability, or a
Hooks-capable codebase where the same logic could be a custom hook with
no nesting cost.

1. Confirm the codebase has Hooks or an equivalent mechanism available.
   if not, the pattern likely still earns its place.
2. Extract the state-owning component's internal logic into a custom
   hook, keeping its exact behaviour, before touching any consumer.
3. Migrate each consumer from calling the render-prop component to
   calling the new hook directly inside its own component, keeping
   tests green after each migration.
4. Remove the now-redundant render-prop component only after no
   consumer references it.

## 15. Testing and verification

Easier because of the pattern.

- The state-owning component's own logic can be tested by supplying a
  simple recording function as the render prop and asserting the state
  values it was called with, with no need to assert against any actual
  rendered markup.
- Each consumer's rendering choice can be tested independently, by
  calling its render function directly with a fixed, known state value
  and asserting the output, with no need to trigger the real state
  transitions that would normally produce that value.

Harder because of the pattern.

- Testing the full, real integration needs rendering the state-owning
  component with a real consumer function and triggering the actual
  state-changing interaction, since testing the two halves separately
  does not prove the real wiring between them holds.
- A render prop passed as a new inline function on every render can
  make a naive re-render count assertion misleading, since the function
  identity changing does not necessarily mean the rendered output
  actually changed, needing a test that asserts against output rather
  than render count alone.

Techniques that apply.

- **Recording-function isolation test.** Supply a test render function
  that records every state value it is called with, and assert the
  recorded sequence matches the expected state transitions, independent
  of what a real consumer would render.
- **Fixed-state rendering test.** Call a consumer's render function
  directly with a fixed, known state value, asserting the output, with
  no need to drive the state-owning component's real logic.
- **Full-integration interaction test.** Render the state-owning
  component with a real consumer function, trigger the real interaction
  that changes its state, and assert the rendered output updates
  correctly.
- **Stable-reference regression test.** Assert that a render function
  defined with a stable reference across renders is genuinely passed
  unchanged when its own dependencies have not changed, guarding
  against the second failure mode in dimension 11.

## 16. Observability signals

Render Props is a source-level composition pattern with no independent
runtime footprint of its own beyond the rendering it already does, and
inventing a dedicated production signal purely for the pattern would be
dishonest. Two things are worth watching in a codebase that uses it.

What to record.

- The nesting depth of render props used together at any single call
  site, since a depth that keeps growing over a codebase's history is a
  signal worth flagging for consolidation into fewer components or
  hooks.
- The re-render frequency of a state-owning component whose consumer
  passes a fresh inline function on every render, since this is a
  concrete, measurable performance cost worth tracking on any component
  where render frequency matters.

A healthy state. Render props used together at any one call site stay
shallow, typically one or two, and re-render counts for a state-owning
component stay proportional to its own actual state changes rather than
to unrelated parent re-renders.

A failing state. A call site nests three or more render props deep with
no plan to consolidate, or profiling shows a state-owning component
re-rendering far more often than its own state actually changes,
pointing at an unstable function reference passed from its consumer.

## 17. Security and privacy implications

Render Props is close to neutral for security, being a UI-composition
pattern rather than a data-handling mechanism, and inventing a
dedicated attack surface here would be dishonest. One practical
implication is worth naming.

**The render function receives whatever the state-owning component
passes, and trusts it implicitly.** Because the consumer's function is
called directly with the state-owning component's internal data, any
sensitive value that component holds is exposed to whatever code the
consumer supplies as its render prop. this is not different from an
ordinary prop in principle, but it is worth naming explicitly, since a
state-owning component sharing sensitive data through a render prop
should apply the same review it would apply to exposing that data
through any other prop, never assuming the function-prop mechanism
itself adds any protection.

## Code examples

Three languages and frameworks where the pattern is genuinely idiomatic
in different ways. TypeScript models the classic state-owning component
calling a render function the way React code structures it, kept free
of JSX and the react package so the sample compiles as plain
TypeScript. Python shows the same conceptual split using a minimal,
framework-agnostic state object accepting a rendering callback, since
Python has no single dominant UI-component framework the way
TypeScript has React. Swift shows the pattern using a generic struct
holding a closure the caller supplies, SwiftUI's own idiomatic
equivalent of a view builder closure receiving state. Java, Go, and
Rust are omitted, since none has a dominant, idiomatic UI-component
framework this specifically frontend pattern maps to as directly as
React and SwiftUI do.

### TypeScript

```typescript
interface Position {
  x: number;
  y: number;
}

class MouseTracker {
  private position: Position = { x: 0, y: 0 };
  private renderFn: (position: Position) => string;

  constructor(renderFn: (position: Position) => string) {
    this.renderFn = renderFn;
  }

  move(x: number, y: number): string {
    this.position = { x, y };
    return this.render();
  }

  render(): string {
    return this.renderFn(this.position);
  }
}

const tracker = new MouseTracker((pos) => `cursor at (${pos.x}, ${pos.y})`);
console.log(tracker.render());
console.log(tracker.move(42, 87));
```

### Python

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class Position:
    x: int
    y: int


class MouseTracker:
    def __init__(self, render_fn: Callable[[Position], str]) -> None:
        self.position = Position(0, 0)
        self.render_fn = render_fn

    def move(self, x: int, y: int) -> str:
        self.position = Position(x, y)
        return self.render()

    def render(self) -> str:
        return self.render_fn(self.position)


if __name__ == "__main__":
    tracker = MouseTracker(lambda pos: f"cursor at ({pos.x}, {pos.y})")
    print(tracker.render())
    print(tracker.move(42, 87))
```

### Swift

```swift
struct Position {
    let x: Int
    let y: Int
}

final class MouseTracker {
    private var position = Position(x: 0, y: 0)
    private let renderFn: (Position) -> String

    init(renderFn: @escaping (Position) -> String) {
        self.renderFn = renderFn
    }

    func move(x: Int, y: Int) -> String {
        position = Position(x: x, y: y)
        return render()
    }

    func render() -> String {
        renderFn(position)
    }
}

let tracker = MouseTracker { pos in "cursor at (" + String(pos.x) + ", " + String(pos.y) + ")" }
print(tracker.render())
print(tracker.move(x: 42, y: 87))
```

## 18. References

1. Michael Jackson. "Use a Render Prop!". 18 September 2017.
   https://medium.com/@mjackson/use-a-render-prop-50de598f11ce
   Verified 2026-08-21. Source of the first_described lineage claim.
2. Downshift README. downshift-js/downshift.
   https://github.com/downshift-js/downshift
   Verified 2026-08-21. Source for the production use in dimension 9.
