---
name: Higher-Order Component
slug: higher-order-component
family: 13-frontend-ui
category: Component Composition
aliases: [HOC, Component Wrapper Function]
first_described: "Common React practice, formalized in official React documentation"
maturity: established
related: [render-props, compound-components, container-presentational, hooks]
incompatible_with: []
verified: 2026-08-21
---

# Higher-Order Component

## 1. Name, aliases, and lineage

The canonical name is Higher-Order Component, often abbreviated HOC,
borrowing its name from the functional-programming idea of a
higher-order function, a function that takes another function as an
argument or returns a function. The React project's own legacy
documentation defines it directly. "a higher-order component is a
function that takes a component and returns a new component."

Unlike most patterns in this family, no single article or person is
credited with inventing the pattern for React specifically, it emerged
from the community applying an established functional-programming idea
to component composition, and the official React documentation later
formalized the name and the convention around it.

## 2. Problem and context

Several components in a codebase often need the same cross-cutting
behavior applied to them, subscribing to a data source, checking
authentication before rendering, logging every prop change, injecting
a piece of shared state. Copying that behavior into every component
that needs it duplicates logic and risks each copy drifting out of
sync as the behavior evolves. A Higher-Order Component solves this by
wrapping a component in a function that adds the shared behavior once,
producing a new component with the original component's own rendering
untouched, so any component can gain the shared behavior by being
passed through the same wrapping function.

## 3. Forces

The pattern balances the following competing pressures.

- **Reuse across unrelated components.** Favored. The same wrapping
  function applies identically to any component matching its expected
  prop shape, regardless of what that component otherwise does.
- **Static composition at definition time.** Favored. The wrapped
  component is produced once, when the module is loaded, rather than
  being recomputed on every render, which keeps the wrapping cost
  predictable.
- **Prop-origin traceability.** Sacrificed. When multiple HOCs wrap a
  single component, the props a component receives can come from
  several layers up the wrapper chain, and tracing a specific prop
  back to its source means reading each wrapper in the chain.
- **Naming and debugging clarity.** Sacrificed unless deliberately
  addressed. A wrapped component's display name in developer tools
  defaults to a generic wrapper name unless the higher-order function
  explicitly sets a more descriptive one.

## 4. Applicability and non-applicability

Reach for a Higher-Order Component when the following hold.

- Several components across a codebase need the identical
  cross-cutting behavior applied to them, and that behavior can be
  expressed generically enough to work across all of them.
- The codebase already depends on a class-component-based library
  whose own composition convention is HOCs, Redux's connect being the
  best-known example, so following the library's own idiom keeps the
  codebase consistent.
- The behavior genuinely needs to intercept a component's props before
  they reach it, rather than merely supplying additional values
  alongside the component's own props.

Do NOT reach for a Higher-Order Component in these cases, and the
reason matters more than the rule.

- **The codebase already has Hooks available**, a custom hook achieves
  the identical sharing benefit with no wrapper component, no prop
  collision risk, and no extra layer in the rendered tree.
- **Wrapping the same component with three or more HOCs**, the
  resulting chain becomes hard to trace, each layer obscuring where a
  given prop actually originates, and either consolidating into fewer
  wrappers or migrating to hooks removes the problem.
- **The shared behavior is needed by exactly one component**, wrapping
  a single, non-reused component in a HOC adds an indirection layer
  with no reuse benefit to justify it.

## 5. Structure

A Higher-Order Component has two structural parts.

- **The higher-order function itself**, accepting a component as its
  argument and returning a new component, defined once and reused
  across every component it wraps.
- **The wrapper component it returns**, rendering the wrapped
  component with whatever additional props, state, or behavior the
  higher-order function adds, passing through the original props it
  received unchanged.

## 6. ASCII structure diagram

```
    withSubscription (the higher-order function)
    - accepts WrappedComponent as its argument
    - returns a new component class

              |
              v  produces

    WithSubscription (the returned wrapper component)
    - holds subscription state internally
    - renders <WrappedComponent {...this.props} data={this.state.data} />
    - passes through every original prop, adds the new data prop

              |
              v  renders

    WrappedComponent (the original, unmodified component)
    - receives its own original props plus the new data prop
    - has no knowledge that it is being wrapped
```

## 7. Dynamics

The trace below shows a component being wrapped once, at module load,
and the resulting wrapped component being rendered and receiving a
subscription update at runtime.

```
Module load

withSubscription(CommentList) called once
   |-- returns WithSubscription, a new component class
   |-- CommentList itself is unchanged, still usable directly elsewhere

Mount

<WithSubscription /> mounts
   |-- WithSubscription's own constructor sets up the subscription
   |-- renders <CommentList {...props} data={initial data} />

Data update

subscription source emits a new value ------------------------->|
   |                                                              |-- WithSubscription's
   |                                                              |   handler updates
   |                                                              |   its own state
   |<-- WithSubscription re-renders ------------------------------|
   |-- renders <CommentList {...props} data={new data} />
   |-- CommentList re-renders with the new data prop
```

## 8. Implementation variants

**Props proxy.** The wrapper passes through the original props
unchanged while adding new ones, the shape shown in dimensions 5
through 7, the most common variant, used to inject additional data or
callbacks without altering the wrapped component's existing contract.

**Inheritance inversion.** The higher-order function returns a class
that extends the wrapped component itself, giving the wrapper access
to override the wrapped component's own render method or lifecycle
methods directly, a rarer and more invasive variant, generally
considered fragile since it couples the wrapper tightly to the wrapped
component's internal implementation rather than only its props.

**Conditional rendering wrapper.** The wrapper decides whether to
render the wrapped component at all, based on some condition, most
commonly seen in authentication-gating HOCs that render a redirect or
a loading state instead of the wrapped component when a precondition
is not yet met.

**Display name assignment for debugging.** A disciplined
implementation sets the returned wrapper's `displayName` explicitly,
`WithSubscription(CommentList)` rather than a generic name, so
developer tools show which component was wrapped and by which HOC,
directly addressing the naming and debugging force sacrificed in
dimension 3.

## 9. Known production uses

**The pattern's own canonical definition.** The official React
documentation (the legacy reactjs.org site, kept online after
the site's newer version moved away from recommending the pattern)
defines it directly. "a higher-order component is a
function that takes a component and returns a new component," and
names Redux's `connect` and Relay's `createFragmentContainer` as
common third-party library examples. It notes plainly that
"higher-order components are not commonly used in modern React code,"
which supports this entry's `established` rather than `canonical`
maturity marker. React documentation, Higher-Order Components,
https://legacy.reactjs.org/docs/higher-order-components.html, verified
2026-08-21.

**Redux's connect function.** The react-redux documentation describes
`connect` directly. "the connect() function connects a React component
to a Redux store," and describes its returned value as one that "does
not modify the component class passed to it, instead, it returns a
new, connected component class that wraps the component you passed
in," which is the props-proxy structural shape from dimension 5,
applied at genuinely large scale across the React ecosystem's most
widely used state-management library. react-redux documentation,
connect(), https://react-redux.js.org/api/connect, verified 2026-08-21.

## 10. Consequences

Positive.

- A single wrapping function applies identical cross-cutting behavior
  to any number of components, with no duplication of the shared
  logic across each one.
- The wrapped component itself needs no knowledge that it is being
  wrapped, keeping its own implementation unchanged and reusable both
  wrapped and unwrapped.
- The wrapper is produced once, at module load, keeping the
  composition cost predictable and independent of how often the
  resulting component renders.

Negative.

- Wrapping a component with several HOCs produces a chain where a
  specific prop's origin is only traceable by reading each wrapper in
  sequence, unlike a render prop's directly visible function call.
- A wrapper's default display name in developer tools is generic
  unless deliberately overridden, making a wrapped component harder to
  identify while debugging than an unwrapped one.
- Two HOCs wrapping the same component can pass props under identical
  names, silently overwriting one another depending on wrapping order,
  a collision risk a render prop or a hook does not share.

## 11. Failure modes and misuse

**Prop name collisions between stacked HOCs.** Symptom. A component
wrapped by two HOCs receives the wrong value for a prop, and the bug
only appears once both HOCs happen to add a prop under the same name.
Cause. Each higher-order function adds its own prop with no visibility
into what prop names sibling HOCs in the same chain might also use,
and whichever wrapper renders closest to the wrapped component wins
silently. Fix. Namespace each HOC's added props under a distinct key,
or document and enforce a fixed wrapping order where a later collision
is at least deterministic and reviewable.

**Wrapping inside another component's render method.** Symptom. The
wrapped component and all of its own internal state remount, losing
any local state, on every render of its parent. Cause. Calling the
higher-order function inside a render method produces a brand-new
wrapper component identity on every call, and React treats a changed
component identity as a full unmount and remount rather than an
update. Fix. Call the higher-order function once, outside any render
method, typically at module scope right after the wrapped component's
own definition.

**Reaching for a HOC where a custom hook would serve identically, with
no wrapper component.** Symptom. A codebase that has otherwise adopted
Hooks continues to add new HOCs for shared logic, producing an
inconsistent mix of composition styles and unnecessary extra layers in
the rendered component tree. Cause. Following an established
convention out of habit rather than reassessing what the codebase's
current idioms call for. Fix. Default to a custom hook for new shared
logic in a Hooks-capable codebase, reserving HOCs for the genuine
cases in dimension 4 where the codebase's own dependencies, such as
Redux's connect, already establish the convention.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Higher-Order Component | Render Props | A custom hook | Compound Components |
|---|---|---|---|---|
| Reuse across unrelated components | High, identical wrapping applies anywhere | High, same call-site flexibility | Highest, called directly wherever needed | Lower, addresses sibling arrangement, not general reuse |
| Prop-origin traceability | Lower, obscured by the wrapper chain | Higher, visible at the function call | Highest, values come directly from the hook call | Moderate, implicit through context |
| Composition cost as more behaviors combine | Grows with each additional wrapper in the chain | Grows with each additional render prop | None, hooks compose without adding tree depth | Low, arrangement rather than wrapping |
| Fit in a modern, Hooks-capable codebase | Largely superseded for the general case | Largely superseded for the general case | The default modern choice | Still genuinely useful for markup-arrangement needs |
| Fit for a class-component-era library convention | Strong, matches Redux's connect and similar | Weaker, less common in that era | Not applicable to class components | Not applicable to this problem shape |

Reading of the table. A Higher-Order Component wins when the
codebase's own dependencies already establish the convention, Redux's
connect being the clearest case, or when a class-component-based
library provides no hook-based alternative. A custom hook wins for the
general case in any modern, Hooks-capable codebase, achieving the same
sharing with no extra component layer and no prop-collision risk.
Render Props solves a closely related problem with better traceability
at the cost of JSX nesting rather than a wrapper chain.

## 13. Related and incompatible patterns

- **Render Props.** The direct sibling pattern, solving the same
  behavior-sharing problem through a function prop rather than a
  wrapping function, with better traceability at the cost of JSX
  nesting instead of a wrapper chain.
- **Compound Components.** A related but distinct composition pattern,
  addressing how several sibling components share implicit state with
  each other through markup arrangement, rather than how one
  component's behavior is shared across many unrelated components.
- **Container Presentational.** A related composition pattern
  addressing the separation of logic from rendering within one
  component's own structure, a separation a HOC often exists to
  automate across many components at once.
- **Hooks.** The modern successor mechanism that achieves the same
  logic-sharing benefit as a HOC without a wrapper component, without
  a prop-collision risk, and without an extra layer in the rendered
  tree, and the pattern most Hooks-capable codebases reach for by
  default today.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a class-component-based codebase where shared
cross-cutting behavior needs to be applied to several components.

1. Identify the shared behavior that several components need, and
   confirm it can be expressed generically enough to apply to more
   than one component's props shape.
2. Write the higher-order function, accepting a component and
   returning a new wrapper component that renders the original with
   the shared behavior applied.
3. Set the wrapper's `displayName` explicitly, so the wrapped
   component remains identifiable in developer tools per the naming
   guidance in dimension 8.
4. Migrate each existing consumer to import the wrapped version rather
   than duplicating the shared behavior inline, confirming behavior is
   unchanged after the migration.
5. Add a test asserting the wrapper passes through the original props
   unchanged and adds exactly the new behavior it is responsible for.

Removing the pattern when it stops earning its place, most relevant to
a codebase that has adopted Hooks. Signals that it should go include a
wrapper chain three or more layers deep, or a Hooks-capable codebase
where the same logic could be a custom hook with no wrapper at all.

1. Confirm the codebase has Hooks or an equivalent mechanism available,
   and that the component being un-wrapped is a function component or
   can become one.
2. Extract the higher-order function's internal logic into a custom
   hook, keeping its exact behavior, before touching any consumer.
3. Migrate each consumer from importing the wrapped component to
   calling the new hook directly inside its own component, keeping
   tests green after each migration.
4. Remove the now-redundant higher-order function only after no
   consumer imports the wrapped version it produced.

## 15. Testing and verification

Easier because of the pattern.

- The higher-order function's own shared behavior can be tested once,
  against a minimal stand-in component, independent of every real
  component it will eventually wrap.
- A wrapped component's original, unwrapped behavior can still be
  tested directly by importing and rendering the unwrapped component,
  since the wrapping function does not modify the original.

Harder because of the pattern.

- Testing the full, real integration needs rendering the wrapped
  version and confirming both the original component's behavior and
  the wrapper's added behavior are both intact, since testing the two
  in isolation does not prove the real composition holds.
- A prop collision between stacked HOCs, per the first failure mode in
  dimension 11, is invisible to a test that only exercises one HOC at
  a time, needing a test that exercises the full wrapping chain as it
  is actually composed in production.

Techniques that apply.

- **Isolated higher-order-function test.** Wrap a minimal stand-in
  component and assert the wrapper adds exactly the expected behavior,
  independent of any real consumer's own logic.
- **Unwrapped-component test.** Import and test the original,
  unwrapped component directly, confirming its own behavior remains
  correct and is unaffected by whatever wrapping it may later receive.
- **Full-chain integration test.** Render the fully wrapped component
  as it is actually composed in production, with every HOC in its
  actual wrapping order, and assert the combined behavior and props
  are correct, guarding specifically against the collision failure
  mode.
- **Display-name regression test.** Assert the wrapped component's
  `displayName` is set to a descriptive value rather than a generic
  default, guarding the debugging concern named in dimension 3.

## 16. Observability signals

A Higher-Order Component is a source-level composition pattern with no
independent runtime footprint of its own beyond the rendering it
already does, and inventing a dedicated production signal purely for
the pattern would be dishonest. Two things are worth watching in a
codebase that uses it.

What to record.

- The depth of the wrapping chain applied to any single component,
  since a chain that keeps growing over a codebase's history is a
  signal worth flagging for consolidation into fewer wrappers or
  migration to hooks.
- Component display names as they appear in developer tools and in any
  production error-reporting stack trace, since a generic wrapper name
  makes an error harder to attribute to the correct source when it
  surfaces in a monitoring system.

A healthy state. Wrapping chains stay shallow, typically one or two,
and every wrapper's display name identifies both the wrapping function
and the component it wraps, remaining identifiable in an error report.

A failing state. A component wrapped by three or more HOCs with no
plan to consolidate, or a stack trace naming an unidentifiable generic
wrapper component with no indication of which higher-order function
produced it or which component it wraps.

## 17. Security and privacy implications

A Higher-Order Component is close to neutral for security, being a
UI-composition pattern rather than a data-handling mechanism, and
inventing a dedicated attack surface here would be dishonest. One
practical implication is worth naming.

**A wrapper that adds an authentication or authorization check must be
applied consistently, or a component reachable through an unwrapped
import path bypasses the check entirely.** Because the wrapped
component and the original, unwrapped component are both still
directly importable unless the codebase deliberately prevents it, a
wrapper responsible for gating access, such as an authentication HOC,
only protects the paths that actually render the wrapped version. this
is worth naming explicitly, since a codebase relying on a HOC for
access control should verify no route or component tree renders the
unwrapped original directly, never assuming the wrapping function
alone is sufficient enforcement.

## Code examples

Three languages and frameworks where the pattern is genuinely idiomatic
in different ways. TypeScript models the classic wrapping function
returning a new class the way React code structures it, kept free of
JSX and the react package so the sample compiles as plain TypeScript.
Python shows the same conceptual split using a plain function that
wraps a callable, decorator-shaped, the closest Python idiom to a
higher-order function returning a modified version of its input.
Swift shows the pattern using a generic function that wraps a
protocol-conforming type, SwiftUI's own idiomatic equivalent of view
composition through a wrapping initializer. Java, Go, and Rust are
omitted, since none has a dominant, idiomatic UI-component framework
this specifically frontend pattern maps to as directly as React and
SwiftUI do.

### TypeScript

```typescript
interface SubscriptionData {
  value: string;
}

interface WrappedProps {
  data: SubscriptionData;
}

class WithSubscription<P extends WrappedProps> {
  private data: SubscriptionData = { value: "" };
  private wrapped: (props: P) => string;

  constructor(wrapped: (props: P) => string) {
    this.wrapped = wrapped;
  }

  update(value: string): void {
    this.data = { value };
  }

  render(otherProps: Omit<P, "data">): string {
    const fullProps = { ...otherProps, data: this.data } as P;
    return this.wrapped(fullProps);
  }
}

function commentList(props: WrappedProps & { title: string }): string {
  return `${props.title}: ${props.data.value}`;
}

const wrapped = new WithSubscription(commentList);
wrapped.update("first comment");
console.log(wrapped.render({ title: "Comments" }));
```

### Python

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class SubscriptionData:
    value: str


class WithSubscription:
    def __init__(self, wrapped: Callable[..., str]) -> None:
        self.wrapped = wrapped
        self.data = SubscriptionData("")

    def update(self, value: str) -> None:
        self.data = SubscriptionData(value)

    def render(self, **other_props: object) -> str:
        return self.wrapped(data=self.data, **other_props)


def comment_list(*, title: str, data: SubscriptionData) -> str:
    return f"{title}: {data.value}"


if __name__ == "__main__":
    wrapped = WithSubscription(comment_list)
    wrapped.update("first comment")
    print(wrapped.render(title="Comments"))
```

### Swift

```swift
struct SubscriptionData {
    let value: String
}

final class WithSubscription<Wrapped> {
    private var data = SubscriptionData(value: "")
    private let wrapped: (Wrapped, SubscriptionData) -> String

    init(wrapped: @escaping (Wrapped, SubscriptionData) -> String) {
        self.wrapped = wrapped
    }

    func update(value: String) {
        data = SubscriptionData(value: value)
    }

    func render(with props: Wrapped) -> String {
        wrapped(props, data)
    }
}

struct CommentListProps {
    let title: String
}

func commentList(props: CommentListProps, data: SubscriptionData) -> String {
    props.title + ": " + data.value
}

let wrapped = WithSubscription(wrapped: commentList)
wrapped.update(value: "first comment")
print(wrapped.render(with: CommentListProps(title: "Comments")))
```

## 18. References

1. React documentation. "Higher-Order Components".
   https://legacy.reactjs.org/docs/higher-order-components.html
   Verified 2026-08-21. Source of the canonical definition and the
   note on the pattern's diminished modern usage.
2. react-redux documentation. "connect()".
   https://react-redux.js.org/api/connect
   Verified 2026-08-21. Source for the production use in dimension 9.
