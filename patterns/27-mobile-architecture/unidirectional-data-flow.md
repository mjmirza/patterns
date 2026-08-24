---
name: Unidirectional Data Flow (Mobile)
slug: unidirectional-data-flow
family: 27-mobile-architecture
category: Structural
aliases: [UDF, One-Way Data Binding, State Down Events Up]
first_described: 'Google Android Developers, "UI layer" architecture guidance, and independently by the Composable Architecture (TCA) on iOS'
maturity: canonical
related: [coordinator-pattern, redux-for-mobile]
incompatible_with: [mvvm-c]
verified: 2026-08-22
---

# Unidirectional Data Flow (Mobile)

## 1. Name, aliases, and lineage

The canonical name is Unidirectional Data Flow, a broader architectural
family, shared across Android and iOS mobile development, where state
flows in exactly one direction, down from a single source of truth to
the view, and events flow in exactly the opposite direction, up from
the view to whatever owns that state, with no other path for data to
travel between the two. Google's own Android architecture guidance
states the core rule directly, "the pattern where the state flows
down and the events flow up is called a unidirectional data flow
(UDF)." Independently, on iOS, the Composable Architecture library
formalizes the same discipline through its own named types, "State, a
type that describes the data your feature needs to perform its logic
and render its UI," and "Action, a type that represents all of the
actions that can happen in your feature."

The alias **UDF** is the common shorthand used across both platforms.
**One-Way Data Binding** names the pattern by what it explicitly
rules out, the two-way property binding common to plain MVVM. **State
Down Events Up** names the pattern by its own literal, one-sentence
rule, Google's own phrase, restated as a mnemonic.

## 2. Problem and context

A screen whose state can be changed from more than one direction, a
view mutating its own local property directly in one place, and a
separate object also updating that same conceptual state in another
place, quickly loses a single, trustworthy answer to "what does the
screen actually show right now." Google's own documentation names the
benefit UDF restores directly, "there is a single source of truth for
the UI." Unidirectional Data Flow solves the multiple-writers problem
by making state change origin from exactly one place, and letting the
view do only two things, render whatever state it is given, and emit
an event describing what the user did, never mutate its own state
directly. Google's own description of the resulting cycle is exact,
"the ViewModel holds and exposes the state to be consumed by the UI,"
"the UI notifies the ViewModel of user events," "the ViewModel
handles the user actions and updates the state," and "the updated
state is fed back to the UI to render."

## 3. Forces

The pattern balances the following competing pressures.

- **Exactly one source of truth for a screen's real state.** Favored.
  Google's own documentation states this directly as the first
  benefit, "data consistency. There is a single source of truth for
  the UI."
- **A state owner that can be tested without any real UI present.**
  Favored. Google's own documentation states this directly, "the
  source of state is isolated and therefore testable independent of
  the UI." The Composable Architecture's own Reducer type, "a function
  that describes how to evolve the current state of the app to the
  next state given an action," is likewise a plain function, testable
  with no view involved.
- **A well-defined, traceable path for every state change.** Favored.
  Google's own documentation states this directly, "mutation of state
  follows a well-defined pattern where mutations are a result of both
  user events and the sources of data they pull from."
- **A view that never takes a shortcut around the cycle.** Sacrificed.
  Every view in the system must genuinely commit to rendering only
  what it is given and emitting only events, never reading or writing
  its own separate copy of state, a real discipline that is easy to
  break under time pressure.
- **An explicit event or action type for every real interaction.**
  Sacrificed. The Composable Architecture's own Action type must
  genuinely enumerate "all of the actions that can happen in your
  feature," a real, up-front cost compared to wiring a direct method
  call for each new interaction as it comes up.

## 4. Applicability and non-applicability

Reach for Unidirectional Data Flow when the following hold.

- The screen genuinely has state that more than one part of the
  codebase could plausibly want to change, and the team genuinely
  wants Google's own stated benefit, a single source of truth, rather
  than reconciling several independent writers.
- The team genuinely wants the logic that produces a screen's state to
  be testable with no real UI present, per Google's own isolation
  benefit and the Composable Architecture's own plain-function
  Reducer.
- The app genuinely spans, or is expected to grow to span, more than
  one platform, and the team wants one shared architectural discipline
  that both Google's own Android guidance and iOS's own Composable
  Architecture independently converge on.

Do NOT reach for Unidirectional Data Flow in these cases, and the
reason matters more than the rule.

- **The screen genuinely has state that only one object could ever
  plausibly write to**, the real discipline of routing every change
  through a single, one-way cycle adds structure without a matching
  real benefit when there was never more than one writer to begin
  with.
- **The team genuinely needs simple, direct, per-field two-way
  binding**, such as a form with many independently editable fields,
  where MVVM's own bindable properties, described in the mvvm-c entry,
  fit the real interaction shape more directly than routing every
  keystroke through an explicit action and a full state recomputation.
- **The real cost of enumerating every possible action up front,
  per the Composable Architecture's own Action type requirement, is
  genuinely not worth paying for a screen that is small, short-lived,
  or unlikely to grow further real complexity.**

## 5. Structure

Unidirectional Data Flow has three structural parts, named
consistently across both platform sources.

- **The single source of truth**, Google's own term, the one place a
  screen's real state genuinely lives, whether a ViewModel's exposed
  state property on Android or the Composable Architecture's own State
  type on iOS.
- **The event or action channel**, Google's own "the UI notifies the
  ViewModel of user events," matched by the Composable Architecture's
  own Action type, "a type that represents all of the actions that can
  happen in your feature."
- **The state-producing logic**, Google's own "the ViewModel handles
  the user actions and updates the state," matched by the Composable
  Architecture's own Reducer, "a function that describes how to evolve
  the current state of the app to the next state given an action."

## 6. ASCII structure diagram

```
  Single source of truth (State)
        |
        |  state flows down
        v
       View (renders only, never mutates)
        |
        |  events/actions flow up
        v
  State-producing logic (ViewModel / Reducer)
        |
        +-- produces the next State, fed back to the top
```

## 7. Dynamics

The trace below shows one complete cycle, per Google's own named
sequence.

```
The user interacts with the view

per Google's own description, "the UI notifies the ViewModel of user
events"
   |-- the view emits an event or action, never mutating its own
       local state directly

The state-producing logic consumes the event

per Google's own description, "the ViewModel handles the user actions
and updates the state," or, on the Composable Architecture's own
terms, the Reducer "describes how to evolve the current state of the
app to the next state given an action"
   |-- it produces a new, complete state value from the previous
       state and the incoming event

The new state flows back down to the view

per Google's own description, "the updated state is fed back to the
UI to render"
   |-- the view renders exactly what the new state describes, and the
       cycle repeats for the next real user event
```

## 8. Implementation variants

**ViewModel-and-state-holder implementation, Google's own Android
form.** A ViewModel exposes a single, observable state property, and
the view collects or observes it, matching Google's own described
cycle directly, with no separate reducer type required.

**Store-and-reducer implementation, the Composable Architecture's own
iOS form.** A Store owns the State, receives Actions, and runs a
Reducer function to compute the next State, per the Composable
Architecture's own four named types, State, Action, Reducer, and
Store.

**Reactive-stream implementation.** A variant common to both
platforms, where actions or events are emitted onto a reactive stream
or a Kotlin Flow, transformed through the state-producing logic, and
the resulting state stream is what the view subscribes to, keeping the
same one-way discipline while composing naturally with other reactive
code already present in the app.

## 9. Known production uses

**Google, Android Developers, "UI layer", the Android half of the
convergence.** Google states the core rule and its benefits directly.
"The pattern where the state flows down and the events flow up is
called a unidirectional data flow (UDF)." The stated benefits, "data
consistency. There is a single source of truth for the UI,"
"testability. The source of state is isolated and therefore testable
independent of the UI," and "maintainability. Mutation of state
follows a well-defined pattern." Google, Android Developers, "UI
layer," https://developer.android.com/topic/architecture/ui-layer,
verified 2026-08-22.

**Point-Free, "The Composable Architecture", the iOS half of the
convergence.** The library states its own four core types directly.
"State. A type that describes the data your feature needs to perform
its logic and render its UI." "Action. A type that represents all of
the actions that can happen in your feature." "Reducer. A function
that describes how to evolve the current state of the app to the next
state given an action." "Store. The runtime that actually drives your
feature." Point-Free, "The Composable Architecture,"
https://github.com/pointfreeco/swift-composable-architecture, verified
2026-08-22.

## 10. Consequences

Positive.

- The screen's real state has exactly one source of truth, per
  Google's own stated benefit, eliminating the class of bugs where two
  independent writers disagree about the current state.
- The logic that produces state is genuinely testable on its own, per
  Google's own isolation benefit and the Composable Architecture's own
  plain-function Reducer, with no real UI needed to exercise it.
- The same discipline is expressed consistently across Android and
  iOS, per this entry's own two independently-converging citations, so
  a team working across both platforms shares one mental model.

Negative.

- Every view in the system must genuinely commit to never mutating its
  own local state directly, a real discipline that is easy to
  accidentally violate under deadline pressure.
- The Composable Architecture's own Action type must genuinely
  enumerate every real interaction up front, a real, up-front cost
  compared to a direct method call wired as each interaction is added.
- A screen whose state genuinely only ever had one writer gains real,
  unneeded structure from adopting the full one-way cycle.

## 11. Failure modes and misuse

**Letting a view read or mutate a piece of local state directly,
alongside rendering the state it is genuinely given, breaking the
single-source-of-truth guarantee the pattern exists to provide.**
Symptom. The screen shows a combination of values that the real,
current State never actually described, because part of what is
visible came from the view's own local mutation rather than from the
one, genuine source of truth. Cause. Reaching for a direct, local view
update, perhaps for a small, seemingly harmless visual tweak, rather
than expressing that change as part of the State the state-producing
logic owns. Fix. Confirm the view's own render step is the only place
the view's visible output is ever set, and treat any direct, local
mutation of view state as a structural bug reintroducing the
multiple-writers problem the pattern was adopted to remove.

**Producing a new state that is only a partial patch of the previous
one, rather than the complete value Google's own cycle and the
Composable Architecture's own Reducer both require.** Symptom. The
view genuinely receives an incomplete picture, missing information the
previous state held, because the state-producing logic assumed the
view would merge the new, partial value with something it remembers
from before. Cause. Computing the new state by mutating or partially
copying the previous one, rather than genuinely producing a whole,
self-contained value for every single event. Fix. Confirm the
state-producing logic always produces a genuinely complete state
value, matching Google's own "the updated state is fed back to the UI
to render" and the Composable Architecture's own Reducer definition,
never a partial delta.

**Bypassing the event or action channel entirely by calling a method
directly on the state owner from the view, rather than emitting a
named event or action.** Symptom. The one-way discipline the pattern
provides silently erodes, because some code paths genuinely go
through the event channel while others genuinely call the state owner
directly, and the codebase loses the single, traceable path Google's
own documentation describes. Cause. Reaching for a direct method call
on the ViewModel or Store, perhaps for convenience on a simple screen,
rather than defining and emitting a real event or action for that
interaction. Fix. Confirm every real interaction is genuinely
expressed as an event or action, per the Composable Architecture's
own Action type, with no direct method call on the state owner
bypassing that channel.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Unidirectional Data Flow (this entry's own mechanism) | Direct, multi-writer state mutation | MVVM-C (bindable, two-way view model) |
|---|---|---|---|
| A single source of truth for real state | Strong, per Google's own stated benefit | Weak, more than one writer can plausibly touch the same conceptual state | Moderate, the view model is the source, but its individual bound properties can be written from more than one place |
| Testability of the state-producing logic | Strong, per Google's own isolation benefit and the Composable Architecture's own plain-function Reducer | Weak, state changes are scattered across whatever code happens to write to them | Strong, per the mvvm-c entry's own testability benefit |
| Explicit, enumerable set of possible events | Strong, per the Composable Architecture's own Action type | None, inputs are untyped method calls with no shared vocabulary | Moderate, commands are named, but property mutation is not |
| Fit for fine-grained, per-field editing | Weak, every keystroke can trigger a full state recomputation | Moderate, direct calls can update only the changed field | Strong, per-property binding updates exactly what changed |

Reading of the table. Unidirectional Data Flow wins specifically when
a screen's real state genuinely has, or could genuinely gain, more
than one plausible writer, and the team wants one architectural
discipline consistent across Android and iOS. A screen with simple,
direct, per-field interaction and a genuinely single writer fits
MVVM-C's own per-property binding better.

## 13. Related and incompatible patterns

- **Coordinator Pattern.** A genuinely complementary concern, this
  entry's own state-down-events-up discipline governs a single
  screen's own state, while the coordinator-pattern entry governs
  navigation between screens, and the two commonly compose, a
  coordinator creating a UDF-governed screen exactly as it would
  create any other.
- **Redux-for-Mobile (Unidirectional Store).** A closely related
  sibling and, on many codebases, a specific named implementation of
  this broader family, usually differing in scope, a single,
  app-wide store versus this entry's own typical per-screen state.
- **MVVM-C (Model-View-ViewModel-Coordinator).** Incompatible in
  practice. MVVM-C's own mutable, individually bindable view-model
  properties genuinely conflict with this pattern's own single,
  complete, one-way state value, so a codebase does not mix the two on
  the same screen.

## 14. Refactoring path in and out

Introducing the pattern into a codebase where a screen's state
currently has more than one real writer. Ordered steps, most relevant
when the multiple-writers problem named in dimension 2 has genuinely
started causing real bugs.

1. Identify every real place that currently writes to the screen's
   conceptual state, and design a single state type that genuinely
   holds all of it, per Google's own single-source-of-truth
   description.
2. Name every real interaction the view can trigger as an explicit
   event or action, per the Composable Architecture's own Action type,
   replacing the direct method calls that currently trigger them.
3. Write the state-producing logic as a real, independently testable
   function or object, per Google's own ViewModel description or the
   Composable Architecture's own Reducer, consuming an event and the
   previous state and producing the next, complete state.
4. Replace the view's own direct state reads and writes with a single
   render step taking the current state, per Google's own cycle, and
   confirm no other code path still mutates the view's state directly.

Removing the pattern when it stops earning its place, most relevant
when a screen's real state has genuinely settled to having exactly one
writer, with no real prospect of gaining a second.

1. Confirm, concretely, that the screen's real state genuinely has, and
   will continue to have, exactly one writer, so the single-source-of-
   truth guarantee is no longer solving a real problem.
2. Replace the event-and-state-producing-logic cycle with direct reads
   and writes from that one real owner.
3. Confirm no other part of the app still depends on the screen's
   event or state types before removing them entirely.

## 15. Testing and verification

Easier because of the pattern.

- The state-producing logic can be tested as a real, pure function or
  isolated object, per Google's own testability benefit, "the source
  of state is isolated and therefore testable independent of the UI,"
  with no real view present.
- The Composable Architecture's own Reducer, "a function that
  describes how to evolve the current state of the app to the next
  state given an action," can be tested by asserting the exact next
  state for a given previous state and action, with no runtime Store
  needed.

Harder because of the pattern.

- Verifying the real, full cycle, a genuine user event through to the
  rendered view, needs a test that exercises the event emission, the
  state-producing logic, and the render step together, not only one
  piece in isolation.
- Confirming no code path anywhere bypasses the pattern, per the
  direct-mutation and channel-bypassing failure modes in dimension 11,
  needs discipline enforced across the whole codebase, not a single
  localized check.

Techniques that apply.

- **State-producing logic tests.** Assert the exact next state
  produced by a given event and previous state, with no real view
  present at all, matching Google's own isolation benefit.
- **State-enumeration tests.** Render the view against every real
  state the logic can produce, asserting each one displays correctly.
- **Full-cycle tests.** Drive a real user event through emission, the
  state-producing logic, and the render step together, asserting the
  final visible output.
- **Purity audits.** Confirm no code path mutates view state directly
  or bypasses the event channel, catching both failure modes named in
  dimension 11.

## 16. Observability signals

What to record.

- The real sequence of state values a screen produces over a session,
  since a state in that sequence that is genuinely incomplete, missing
  information the previous state held, points directly at the
  partial-state failure mode from dimension 11.
- Whether any code path genuinely calls a method on the state owner
  directly, bypassing the event or action channel, since any such call
  points directly at the channel-bypassing failure mode from
  dimension 11.

A healthy state. Every state value in a screen's real sequence is
complete and self-contained, and no code path ever calls the state
owner directly outside the event or action channel.

A failing state. A state value in the real sequence is missing
information the previous one held, pointing directly at a
partial-state bug, or a direct call on the state owner is found
outside the event channel, pointing directly at a bypassed cycle.

## 17. Security and privacy implications

**Because the single source of truth, per Google's own description,
genuinely holds the complete real state a screen needs, a state value
that includes sensitive data, such as a fetched payment detail or an
authentication token used only for a status display, is retained in
full inside every historical state a debugging or time-travel tool
keeps around, a real, broader retention surface than a single,
transient direct mutation would have created.** Because many
implementations of this pattern, particularly the Composable
Architecture's own Store, genuinely support recording a history of
state values for debugging, any sensitive value placed inside the
state persists for as long as that history is retained, not only for
as long as the screen is visible. Confirming sensitive values are
never placed directly inside a state value that could be retained in
a debugging history, and are instead re-fetched or recomputed from a
secure source only when genuinely needed for display, is a necessary
part of a security-conscious Unidirectional Data Flow implementation.

## 18. References

1. Google, Android Developers. "UI layer".
   https://developer.android.com/topic/architecture/ui-layer
   Verified 2026-08-22. Source of the core UDF rule, the state-down-
   events-up cycle, and the data-consistency, testability, and
   maintainability benefits, used in dimensions 1, 2, 3, 5, 7, 9, 10,
   and 15.
2. Point-Free. "The Composable Architecture".
   https://github.com/pointfreeco/swift-composable-architecture
   Verified 2026-08-22. Source of the iOS-side State, Action, Reducer,
   and Store definitions, used in dimensions 1, 3, 5, 7, 9, 11, and 15.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. Kotlin models Google's own ViewModel-and-state-holder mechanism
directly, the language the Android UI layer guidance is written for.
Swift shows the same conceptual shape idiomatic to the Composable
Architecture's own State, Action, Reducer, Store vocabulary on iOS.
Python shows the same conceptual shape using a minimal, host-testable
simulation, useful for verifying the state-producing logic in
isolation, per dimension 15, expressed portably. Java, Go, and Rust
are omitted, since the pattern's real home is mobile-app UI
frameworks, and the three languages chosen already cover its two
production platforms and its testable-simulation shape.

### Kotlin

```kotlin
sealed class Event {
    object LoadPersons : Event()
}

data class PersonsState(
    val loading: Boolean,
    val persons: List<String>
)

class PersonsViewModel {
    var state: PersonsState = PersonsState(loading = true, persons = emptyList())
        private set

    fun onEvent(event: Event) {
        state = when (event) {
            is Event.LoadPersons -> {
                val fetched = listOf("Ada", "Grace")
                state.copy(loading = false, persons = fetched)
            }
        }
    }
}

class PersonsView {
    fun render(state: PersonsState) {
        if (state.loading) {
            println("loading")
        } else {
            println("persons: ${state.persons}")
        }
    }
}

fun main() {
    val viewModel = PersonsViewModel()
    val view = PersonsView()
    view.render(viewModel.state)
    viewModel.onEvent(Event.LoadPersons)
    view.render(viewModel.state)
}
```

### Swift

```swift
enum Action {
    case loadPersons
}

struct PersonsState {
    let loading: Bool
    let persons: [String]
}

func reduce(_ state: PersonsState, _ action: Action) -> PersonsState {
    switch action {
    case .loadPersons:
        let fetched = ["Ada", "Grace"]
        return PersonsState(loading: false, persons: fetched)
    }
}

final class PersonsStore {
    private(set) var state: PersonsState

    init(state: PersonsState) {
        self.state = state
    }

    func send(_ action: Action) {
        state = reduce(state, action)
    }
}

final class PersonsView {
    func render(_ state: PersonsState) {
        if state.loading {
            print("loading")
        } else {
            print("persons:", state.persons)
        }
    }
}

let store = PersonsStore(state: PersonsState(loading: true, persons: []))
let view = PersonsView()
view.render(store.state)
store.send(.loadPersons)
view.render(store.state)
```

### Python

```python
from dataclasses import dataclass


class LoadPersonsEvent:
    pass


@dataclass(frozen=True)
class PersonsState:
    loading: bool
    persons: list


def reduce(state: PersonsState, event) -> PersonsState:
    if isinstance(event, LoadPersonsEvent):
        fetched = ["Ada", "Grace"]
        return PersonsState(loading=False, persons=fetched)
    return state


class PersonsStore:
    def __init__(self, state: PersonsState):
        self.state = state

    def send(self, event) -> None:
        self.state = reduce(self.state, event)


class PersonsView:
    def render(self, state: PersonsState) -> None:
        if state.loading:
            print("loading")
        else:
            print("persons:", state.persons)


if __name__ == "__main__":
    store = PersonsStore(PersonsState(loading=True, persons=[]))
    view = PersonsView()
    view.render(store.state)
    store.send(LoadPersonsEvent())
    view.render(store.state)
```
