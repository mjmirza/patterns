---
name: Container Presentational
slug: container-presentational
family: 13-frontend-ui
category: Component Composition
aliases: [Smart and Dumb Components, Container and Presentational Components, Stateful and Stateless Components]
first_described: "Abramov 2015"
maturity: deprecated
related: [hooks, higher-order-component, render-props, compound-components, separation-of-concerns]
incompatible_with: [monolithic-component]
verified: 2026-08-21
---

# Container Presentational

## 1. Name, aliases, and lineage

The canonical name is Container Presentational, describing the split
between two component roles. Dan Abramov named and popularised the
pattern in "Presentational and Container Components", published 23
March 2015
(https://medium.com/@dan_abramov/smart-and-dumb-components-7ca2f9a7c7d0,
verified 2026-08-21), which states. "you'll find your components much
easier to reuse and reason about if you divide them into two
categories." A presentational component receives data through props
and renders it, a container component owns the data and the logic that
produces it.

The alias **Smart and Dumb Components** is the informal name the same
article popularised, container components are the smart ones, holding
state and logic, presentational components are the dumb ones, purely
rendering what they are given. **Stateful and Stateless Components**
names the same split by the property most directly responsible for it.

The article itself carries an important later addition. a 2019 update
from the same author states plainly. "I don't suggest splitting your
components like this anymore... Hooks let me do the same thing without
an arbitrary division." This entry treats that retraction honestly, see
dimension 10 and the maturity field above.

## 2. Problem and context

A component that both fetches data, manages loading and error state,
and renders the resulting markup mixes two genuinely different
concerns in one place. the logic that decides WHAT to show, and the
markup that decides HOW to show it. Mixing them makes the component
harder to reuse, since the rendering cannot be reused without also
pulling in the specific data-fetching logic it happens to be bundled
with, and harder to test, since testing the rendering requires setting
up the same state management the logic needs.

The Container Presentational pattern solves this by splitting the
component in two. a container component that owns data fetching, state,
and business logic, and a presentational component that receives
everything it needs through props and focuses purely on markup and
styling. The presentational half becomes reusable across different data
sources, and the container half becomes testable independently of any
specific rendering.

## 3. Forces

The pattern balances the following competing pressures.

- **Reusability of the rendering.** Favoured. A presentational
  component with no knowledge of where its data comes from can be
  reused with any container, or with static test data, or in a
  storybook-style catalogue, without change.
- **Testability of the logic.** Favoured. Logic isolated in a container
  component can be tested without rendering any markup, and rendering
  can be tested without setting up the logic that would normally
  produce its data.
- **File and component count.** Sacrificed. Every component split this
  way becomes two components and, typically, two files, which is a real
  cost for a small or simple component where the split offers little
  practical benefit.
- **Modern ergonomics.** Sacrificed, and largely superseded. Hooks give
  a function component the ability to hold state and side-effect logic
  directly, without needing the container's separate wrapper, which is
  exactly why the pattern's own creator retracted his original
  recommendation to split by default.

## 4. Applicability and non-applicability

Reach for Container Presentational when the following hold.

- The codebase's component model does not have Hooks, or a comparable
  built-in mechanism, available, older class-based React code, or a
  UI framework with a similar stateless-versus-stateful split as its
  own idiom.
- A genuinely reusable presentational component needs to be shared
  across several different data sources or contexts, and separating it
  from any one specific container makes that reuse concrete rather than
  aspirational.
- A design system or component catalogue benefits from cataloguing pure,
  input-to-output rendering components independently of the application
  logic that will eventually feed them real data.

Do NOT reach for Container Presentational in these cases, and the
reason matters more than the rule.

- **The codebase already has Hooks or an equivalent built-in mechanism
  for separating logic from rendering**, the pattern's own creator
  retracted the general recommendation for exactly this reason. reach
  for a custom hook to hold the stateful logic instead of splitting the
  component into two files.
- **The component is small and used in exactly one place**, splitting a
  simple, single-use component into a container and a presentational
  half adds two files and an extra layer of prop-passing for no real
  reuse benefit.
- **The split would separate data and rendering that are never used
  independently**, if no test, no reuse case, and no design-system
  cataloguing ever benefits from the split, it is ceremony without a
  payoff.

## 5. Structure

The pattern has two component roles connected by props.

- **The container component**, holding state, side effects, and data
  fetching, with no markup of its own beyond delegating to the
  presentational component it wraps.
- **The presentational component**, a function of its props alone, with
  no internal state beyond purely local UI state, such as whether a
  dropdown is currently open, and no direct knowledge of where its data
  came from.

The container passes data and callback functions down as props, and
the presentational component calls those callbacks in response to user
interaction, never reaching back into the container's internals
directly.

## 6. ASCII structure diagram

```
    UserListContainer (container, owns logic and state)
    - fetches the user list on mount
    - tracks loading and error state
    - passes data and callbacks down as props

              |
              v  props: { users, loading, error, onSelect }

    UserList (presentational, pure rendering)
    - renders a loading state, an error state, or the list
    - calls onSelect(user) when a row is clicked
    - holds no knowledge of where users came from
```

## 7. Dynamics

The trace below shows a container fetching data and passing it down to
a presentational component that renders it and reports a user
interaction back up through a callback.

```
Mount

UserListContainer mounts
   |-- starts fetching the user list -------------------->|
   |<-- fetch resolves with the user array -----------------|
   |-- sets internal state, loading = false, users = [...]
   |
   |-- renders <UserList users={...} loading={false}
   |            onSelect={handleSelect} />

UserList (presentational) receives the props
   |-- renders one row per user in the array

User interaction

person clicks a row
   |-- UserList calls onSelect(user) ---------------------->|
   |                                                          |-- container's
   |                                                          |   handleSelect
   |                                                          |   runs, updates
   |                                                          |   its own state
   |<-- container re-renders, passing updated props down ----|
```

## 8. Implementation variants

**Class-component container, function-component presentational.** The
original, historical form, a stateful class component as the
container, wrapping a plain, stateless function component that receives
props and renders markup.

**Hook-based container, still split into two components.** A more
modern variant that keeps the two-component split for reuse or
cataloguing reasons, but implements the container's logic with Hooks
internally rather than class lifecycle methods, combining the
pattern's structural benefit with the newer implementation style.

**Custom-hook replacement, the pattern's modern successor.** Rather
than splitting into two components at all, the stateful logic moves
into a custom hook that any presentational component can call directly,
which is the specific alternative the pattern's own creator recommends
in the 2019 update, achieving the same separation of concerns without
the extra component and file.

**Higher-order-component-based container.** An older variant using a
higher-order component to wrap a presentational component and inject
container-provided props, common in codebases from before Hooks
existed and often layered alongside the pattern rather than replacing
it.

## 9. Known production uses

**The pattern's own originating source, Dan Abramov's article.**
"Presentational and Container Components" states the core rationale.
"you'll find your components much easier to reuse and reason about if
you divide them into two categories," and the same article's 2019
update documents the retraction described in dimension 1. Dan
Abramov, Presentational and Container Components, 2015, updated 2019,
https://medium.com/@dan_abramov/smart-and-dumb-components-7ca2f9a7c7d0,
verified 2026-08-21.

**Patterns.dev's Container/Presentational Pattern reference.** The
widely used frontend pattern reference site documents the pattern
directly. "with this pattern, we can separate the view from the
application logic," and notes that Hooks have largely superseded it for
many use cases, matching the honest maturity assessment in this entry.
Patterns.dev, Container/Presentational Pattern,
https://www.patterns.dev/react/presentational-container-pattern/,
verified 2026-08-21.

## 10. Consequences

Positive.

- A presentational component with no knowledge of its data source can
  be reused across different containers, static test fixtures, or a
  component catalogue with no change to its own code.
- Rendering logic and stateful logic can be tested independently, each
  in isolation from the other.
- A team new to a codebase can reason about a presentational
  component's output purely from its props, without needing to trace
  where the data originated.

Negative.

- The split doubles the file and component count for every component
  that adopts it, a real cost when the presentational half is never
  reused anywhere else.
- The pattern's own creator publicly retracted the general
  recommendation once Hooks made the same separation achievable without
  an extra component, so adopting it by default in a modern
  Hooks-capable codebase repeats a documented mistake.
- Passing every piece of data and every callback down as props between
  the two halves can produce a long, awkward prop list for a component
  with many pieces of state, a friction the pattern itself does nothing
  to reduce.

## 11. Failure modes and misuse

**Splitting every component into container and presentational halves
by default, in a codebase with Hooks available.** Symptom. The
codebase carries twice as many component files as it needs, most of
them never reused independently of their one container, and new
contributors ask why the split exists. Cause. Following the pattern's
original, since-retracted 2015 recommendation without accounting for
the 2019 update or the availability of Hooks. Fix. Reach for a custom
hook to hold stateful logic directly inside a single component, per
dimension 8's custom-hook variant, and reserve the two-component split
for cases where a presentational component is genuinely reused across
more than one container.

**A presentational component quietly gaining its own data-fetching
logic.** Symptom. Over time, a presentational component that started
purely as a function of its props accumulates its own state, its own
side effects, or its own data fetching, and the boundary between it and
its container blurs until the split no longer means anything. Cause. A
convenient shortcut, adding one small piece of local logic directly to
the presentational half rather than routing it back through the
container, repeated until the presentational component is no longer
purely presentational. Fix. Periodically confirm the presentational
component remains a pure function of its props, and move any state or
side effect that has crept in back up to the container, or convert the
component to the custom-hook variant entirely.

**Prop-drilling an unmanageable number of fields between the two
halves.** Symptom. The container passes a long, growing list of props
down to the presentational component, and adding one new piece of data
means touching both the container's render call and the presentational
component's prop type on every change. Cause. Letting the two-component
split grow without ever revisiting whether the presentational
component's responsibility has grown too broad for a flat prop list to
carry cleanly. Fix. Group related props into a single object parameter,
or reconsider whether the presentational component has taken on enough
responsibility to be split further, or merged back with its container
via the custom-hook variant.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Container Presentational | A custom hook, single component | Higher-Order Component | Render Props |
|---|---|---|---|---|
| Reuses the rendering independently of the data source | Yes | Not directly, needs the presentational half kept separate anyway | Yes, but couples the wrapped component to the HOC's prop injection | Yes, and with more render flexibility |
| Testable logic in isolation | Yes | Yes, testing the hook directly | Yes, testing the wrapping function | Yes, testing the render function |
| File and component count | Highest, always two | Lowest, one component plus a hook | Two, the HOC and the wrapped component | Two, the render-prop component and its consumer |
| Modern idiomatic fit in a Hooks-capable codebase | Retracted by its own creator | Yes, the recommended modern approach | Largely superseded by Hooks | Largely superseded by Hooks and composition |
| Prop-passing friction as complexity grows | Real, a flat prop list between the two halves | Minimal, state lives directly in the component using it | Real, injected props can be hard to trace | Real, though contained inside one render function |

Reading of the table. Container Presentational wins in a codebase
without Hooks or an equivalent mechanism, or when a presentational
component's reuse across several unrelated containers is a genuine,
active need. A custom hook wins in any modern Hooks-capable codebase
for the general case, which is exactly what the pattern's own creator
now recommends. Higher-Order Component and Render Props are the two
other pre-Hooks composition patterns this one is most often confused
with, and all three have been largely superseded by Hooks for their
original purpose.

## 13. Related and incompatible patterns

- **Hooks.** The modern successor pattern that achieves the same
  separation of stateful logic from rendering without needing a second
  component, and the specific alternative the pattern's own creator
  recommends in the 2019 update.
- **Higher-Order Component.** A sibling pre-Hooks composition pattern,
  often used alongside or instead of Container Presentational to inject
  container-provided props into a wrapped component.
- **Render Props.** Another sibling pre-Hooks composition pattern,
  passing a render function as a prop rather than splitting into a
  separate container component, and, like this pattern, largely
  superseded by Hooks for most use cases.
- **Compound Components.** A related but distinct composition pattern,
  addressing how several related components share implicit state with
  each other, rather than how one component's logic is separated from
  its rendering.
- **Separation of Concerns.** The general software-design principle
  Container Presentational is one specific, UI-layer instance of,
  splitting what to render from how to compute what should be
  rendered.
- **Monolithic Component.** Conflicts directly. a single component that
  mixes state, side effects, and rendering with no separation is
  exactly the shape this pattern, and its modern custom-hook successor,
  both exist to split apart.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a codebase without Hooks available.

1. Identify a component that mixes data-fetching or state-management
   logic with markup, and confirm splitting it would produce a
   presentational half that is genuinely reusable, not merely a
   cosmetic separation.
2. Extract the markup into a new presentational component, accepting
   every piece of data and every callback it needs as props, with no
   internal state beyond purely local UI concerns.
3. Rename the original component to a container, removing its markup
   and replacing it with a render call to the new presentational
   component, passing the state and callbacks it already owns down as
   props.
4. Confirm the presentational component can be rendered in isolation,
   with static test data and no real container, proving the split is
   genuine rather than only nominal.
5. Add a test for the container's logic that does not depend on the
   presentational component's actual markup, and a test for the
   presentational component's rendering that does not depend on the
   container's actual data source.

Removing the pattern when it stops earning its place, most relevant to
a codebase that has adopted Hooks. Signals that it should go include a
presentational component that is only ever rendered by its one
container, or a growing, awkward prop list between the two halves that
a custom hook would eliminate entirely.

1. Confirm the presentational component is genuinely used only by its
   one container. if so, the split offers no active reuse benefit.
2. Extract the container's stateful logic into a custom hook, keeping
   its exact behaviour, before removing any markup.
3. Merge the container and presentational component back into one,
   calling the new custom hook directly inside it, keeping the
   existing tests green after the merge.
4. Delete the now-redundant container component only after no call
   site references it.

## 15. Testing and verification

Easier because of the pattern.

- A presentational component can be tested by rendering it with a
  fixed set of props and asserting the output, with no need to mock a
  data source, a network call, or any state-management setup.
- A container's logic can be tested by asserting the props it produces
  and the callbacks it exposes, without needing to render or assert
  against any actual markup.
- A design-system or component-catalogue tool, such as a storybook
  setup, can exercise the presentational component directly with a
  range of prop combinations, independent of any real data.

Harder because of the pattern.

- A test suite covering both halves separately can still miss a bug
  that only appears in the integration between them, the exact shape
  of the props the container actually passes versus what the
  presentational component actually expects, which needs at least one
  integration test wiring the two together for real.
- Refactoring the props passed between the two halves needs coordinated
  updates to both the container's render call and the presentational
  component's prop type, and a test suite that only tests each half in
  isolation can miss a mismatch introduced by an incomplete refactor.

Techniques that apply.

- **Isolated rendering test.** Render the presentational component
  directly with a fixed set of props, including a loading state, an
  error state, and a populated state, and assert the output for each.
- **Isolated logic test.** Test the container's state transitions and
  side effects directly, asserting the props it would pass down, with
  no rendering involved.
- **Integration wiring test.** Render the full container-plus-
  presentational pair together at least once, confirming the actual
  prop shape the container produces matches what the presentational
  component actually consumes.
- **Callback-contract test.** Assert the presentational component calls
  its callback props with the expected arguments on the expected user
  interaction, confirming the contract between the two halves holds in
  both directions.

## 16. Observability signals

The Container Presentational split is a source-level organisational
pattern with no independent runtime footprint of its own, and
inventing a dedicated production signal purely for the split itself
would be dishonest. Two things are worth watching in a codebase that
uses it.

What to record.

- A count, tracked over a codebase's history, of presentational
  components that are rendered by exactly one container, as a proxy
  for how much of the split is delivering real reuse versus adding
  unearned file overhead.
- The size of the prop list passed between paired containers and
  presentational components, since a prop list that keeps growing is a
  signal the split's boundary, or the component's responsibility, needs
  revisiting.

A healthy state. Most presentational components in the codebase are
genuinely reused across more than one container, or are actively
catalogued in a design system, and prop lists between paired halves
stay small and stable.

A failing state. Most presentational components are rendered by
exactly one container with no other consumer, and prop lists keep
growing between paired halves with no refactor addressing it, both
signals the codebase would benefit from the custom-hook variant instead.

## 17. Security and privacy implications

The Container Presentational split is, on its own, close to neutral
for security, being a UI-layer organisational pattern rather than a
data-handling mechanism, and inventing a dedicated attack surface here
would be dishonest. One practical implication is worth naming.

**A presentational component receiving raw, unsanitised data through
props can still render unsafe content.** Splitting a component into a
container and a presentational half does not, on its own, sanitise
anything passed between them. if the container fetches data that could
contain untrusted content, the presentational component still needs
the same output-encoding and sanitisation discipline it would need
without the split, since the pattern only reorganises where the
rendering happens, not what is safe to render.

## 18. References

1. Dan Abramov. "Presentational and Container Components". 23 March
   2015, updated 2019.
   https://medium.com/@dan_abramov/smart-and-dumb-components-7ca2f9a7c7d0
   Verified 2026-08-21. Source of the first_described lineage claim
   and the 2019 retraction quoted in dimension 1.
2. Patterns.dev. Container/Presentational Pattern.
   https://www.patterns.dev/react/presentational-container-pattern/
   Verified 2026-08-21. Source for the production reference use in
   dimension 9.

## Code examples

Three languages and frameworks where the pattern is genuinely idiomatic
in different ways, since Container Presentational is a UI-framework
pattern rather than a general-purpose language pattern. TypeScript
models the classic container-and-presentational split the way React
code structures it, kept free of JSX and the react package so the
sample compiles as plain TypeScript. The Python example models the
same split conceptually using a minimal, framework-agnostic
presentation function paired with a stateful controller object, since
Python has no single dominant UI-component framework the way
TypeScript has React. Swift with SwiftUI shows the split as a View
struct receiving state through its initialiser, paired with an
ObservableObject that owns the state and logic, SwiftUI's own idiomatic
shape for the same separation. Java, Go, and Rust are omitted, since
none has a dominant, idiomatic UI-component framework this
specifically frontend pattern maps to as directly as React and
SwiftUI do.

### TypeScript (React)

A framework-agnostic model of the container/presentational split, since
the checker environment has no React type declarations installed.
JSX is intentionally not used here so the sample compiles as plain
TypeScript; the shape below is what a real React implementation would
carry inside its component bodies.

```typescript
interface User {
  id: string;
  name: string;
}

interface UserListProps {
  users: User[];
  loading: boolean;
  onSelect: (user: User) => void;
}

function renderUserList(props: UserListProps): string[] {
  if (props.loading) return [];
  return props.users.map((user) => user.name);
}

function selectUser(props: UserListProps, userId: string): void {
  const user = props.users.find((u) => u.id === userId);
  if (user) props.onSelect(user);
}

class UserListContainer {
  private users: User[] = [];
  private loading = true;

  load(): void {
    this.users = [{ id: "1", name: "Ada" }];
    this.loading = false;
  }

  toProps(onSelect: (user: User) => void): UserListProps {
    return { users: this.users, loading: this.loading, onSelect };
  }
}

const container = new UserListContainer();
container.load();
const props = container.toProps((user) => console.log("selected", user.name));
console.log(renderUserList(props));
selectUser(props, "1");
```

### Python

```python
from dataclasses import dataclass
from typing import Callable, List


@dataclass(frozen=True)
class User:
    id: str
    name: str


def render_user_list(users: List[User], on_select: Callable[[User], None]) -> str:
    rows = chr(10).join(f"<li>{u.name}</li>" for u in users)
    return f"<ul>{rows}</ul>"


class UserListController:
    def __init__(self) -> None:
        self.users: List[User] = []

    def load(self) -> None:
        self.users = [User(id="1", name="Ada")]

    def render(self) -> str:
        return render_user_list(self.users, self._on_select)

    def _on_select(self, user: User) -> None:
        print("selected", user.name)


if __name__ == "__main__":
    controller = UserListController()
    controller.load()
    print(controller.render())
```

### Swift (SwiftUI)

```swift
import SwiftUI
import Combine

struct User: Identifiable {
    let id: String
    let name: String
}

struct UserListView: View {
    let users: [User]
    let onSelect: (User) -> Void

    var body: some View {
        List(users) { user in
            Text(user.name).onTapGesture { onSelect(user) }
        }
    }
}

final class UserListController: ObservableObject {
    @Published var users: [User] = []

    func load() {
        users = [User(id: "1", name: "Ada")]
    }

    func select(_ user: User) {
        print("selected " + user.name)
    }
}

struct UserListContainer: View {
    @StateObject private var controller = UserListController()

    var body: some View {
        UserListView(users: controller.users, onSelect: controller.select)
            .onAppear { controller.load() }
    }
}
```
