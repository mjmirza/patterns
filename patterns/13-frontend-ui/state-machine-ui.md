---
name: State Machine UI
slug: state-machine-ui
family: 13-frontend-ui
category: State Management
aliases: [Statechart UI, Finite State Machine UI, XState Pattern]
first_described: "David Khourshid, React Rally 2017"
maturity: established
related: [redux, hooks, provider-pattern]
incompatible_with: []
verified: 2026-08-21
---

# State Machine UI

## 1. Name, aliases, and lineage

The canonical name is State Machine UI, the practice of modeling a
component's or a flow's possible states, and the events that move
between them, as an explicit finite state machine rather than as a
collection of independent boolean flags. XState's own documentation
states the idea directly. "XState is a state management and
orchestration solution for JavaScript and TypeScript apps," using
"event-driven programming, state machines, statecharts, and the
actor model" to handle complex logic in a predictable, visually
inspectable way. XState's creator, David Khourshid, traces the library's public
origin to a talk given at React Rally in 2017, writing in a later
release announcement, "It's been over a year since I first talked
about state machines and statecharts to the web community at React
Rally 2017."

The alias **Statechart UI** points at statecharts, the extension of
plain finite state machines (hierarchical and parallel states, guards,
actions) that most modern UI state-machine libraries actually
implement, rather than a strictly flat classical automaton. **Finite
State Machine UI** is the more formal, textbook name for the same
idea. **XState Pattern** names the dominant JavaScript library that
popularized the approach for UI work.

## 2. Problem and context

A component with several loading, error, and success conditions is
commonly modeled with several independent boolean flags, such as
`isLoading`, `isError`, and `hasData`, tracked as separate pieces of
state. As the number of flags grows, so does the number of
combinations the code technically allows, most of which are
impossible in practice, `isLoading` true at the same time as
`hasData` true, for example, and none of those impossible
combinations are prevented by the type system or the code itself.
State Machine UI solves this by replacing the pile of independent
booleans with one explicit set of named states, `idle`, `loading`,
`success`, `error`, and a defined set of events that transition
between them, so an impossible combination cannot be represented at
all, since the component can only ever be in exactly one named state
at a time.

## 3. Forces

The pattern balances the following competing pressures.

- **Preventing impossible states by construction.** Favored. A
  component modeled as a state machine can only occupy one of its
  explicitly named states at a time, so a combination such as loading
  and success being true together simply cannot be represented,
  rather than being a runtime bug to catch later.
- **Visualizing and reasoning about behavior.** Favored. Because a
  state machine's states and transitions are declared explicitly
  rather than scattered across conditional checks, the entire
  behavior of a component can be drawn as a diagram and read by
  someone who never wrote the code.
- **Up-front modeling cost.** Sacrificed for simple components. A
  component with genuinely one or two states gains little from being
  formally modeled, and the ceremony of defining states, events, and
  transitions is not repaid until the number of states and the
  interactions between them grow past what a few boolean flags can
  hold safely.
- **Predictable, exhaustive transition handling.** Favored. Every
  transition a state machine allows is declared, so an event the
  current state does not recognize is a defined, provable no-op
  rather than an unhandled edge case discovered later.

## 4. Applicability and non-applicability

Reach for State Machine UI when the following hold.

- A component or flow has several distinct states, loading,
  success, error, and possibly several more, and the transitions
  between them are conditional on more than one piece of
  independent state.
- Impossible or contradictory combinations of boolean flags have
  actually appeared as bugs in the codebase, or the surrounding team
  has enough experience with the pattern to recognize the risk before
  it appears.
- The flow benefits from being visualized as a diagram for design
  review, debugging, or onboarding a new engineer to the component's
  behavior.

Do NOT reach for State Machine UI in these cases, and the reason
matters more than the rule.

- **The component genuinely has one or two states with no
  interaction between them**, defining an explicit machine for a
  single loading boolean adds ceremony a plain conditional already
  handles correctly.
- **The team has no familiarity with state machines or statecharts**,
  a state-machine library introduces a real amount of new vocabulary,
  hierarchical states, guards, actions, that a team unfamiliar with
  the concepts will misuse before they benefit from it.
- **The state genuinely needs to represent several independent,
  simultaneously true conditions**, such as a form where multiple
  fields can independently be valid or invalid at once, a shape a
  single current-state machine does not naturally represent without
  additional parallel-state machinery.

## 5. Structure

A state machine used for UI has four structural parts.

- **States**, the named, mutually exclusive conditions the component
  can be in, such as `idle`, `loading`, `success`, and `error`.
- **Events**, the named signals that can be sent to the machine, such
  as `FETCH`, `RESOLVE`, and `REJECT`.
- **Transitions**, the mapping from a given state and a given event
  to the next state, defined explicitly for each state rather than
  computed from several independent conditions.
- **Context**, optional extended data carried alongside the current
  state, such as the fetched result or an error message, distinct
  from the finite set of named states itself.

## 6. ASCII structure diagram

```
                 FETCH
      +-------------------------+
      |                         v
  +-------+                +---------+
  | idle  |                | loading |
  +-------+                +---------+
      ^                     |       |
      |                RESOLVE   REJECT
      |                     |       |
      |                     v       v
      |               +---------+ +-------+
      +---- RESET -----| success | | error |
                        +---------+ +-------+
                             |          |
                             +--RESET---+
```

## 7. Dynamics

The trace below shows a component fetching data, following the
machine from `idle` through `loading` to `success`.

```
Initial render

component mounts in the idle state
   |-- no request has been sent yet

User triggers a fetch

a FETCH event is sent to the machine
   |-- the machine's idle-state transition table maps FETCH to loading
   |-- the machine's current state becomes loading
   |-- an entry action for loading fires, starting the network request

Request resolves

the network request completes successfully
   |-- a RESOLVE event, carrying the fetched data, is sent to the machine
   |-- the machine's loading-state transition table maps RESOLVE to success
   |-- the machine's current state becomes success, with the fetched
       data stored in the machine's context
   |-- the component re-renders, reading the current state name and
       context to decide what to show
```

## 8. Implementation variants

**A hand-rolled reducer as a state machine.** A single reducer
function whose switch statement is deliberately structured so each
case only handles events valid for that state, effectively
implementing a state machine's shape without a dedicated library,
often the first step a team takes before adopting a formal library.

**XState, the dominant JavaScript and TypeScript library.** A full
statechart implementation supporting hierarchical and parallel
states, guards, actions, and the actor model for coordinating several
machines together, with first-class visualization tooling that
renders a machine's definition as an interactive diagram.

**Framework-native reducer hooks used as a lightweight machine.** A
framework's own reducer-style state primitive, such as `useReducer`,
used with a reducer function shaped as a state machine, giving much
of the impossible-states-prevented benefit without adopting a
dedicated state-machine library.

**Statechart visualization and simulation tooling.** A companion tool
that renders a machine's states and transitions as an interactive
diagram, letting a team simulate events against the machine and watch
it move between states before writing any component code around it.

## 9. Known production uses

**XState's own documentation, describing its core purpose.** XState's
documentation states directly. "XState is a state management and
orchestration solution for JavaScript and TypeScript apps," built on
"event-driven programming, state machines, statecharts, and the
actor model." Stately documentation, XState,
https://stately.ai/docs/xstate, verified 2026-08-21.

**David Khourshid, on why statecharts prevent a specific class of
bug.** In the announcement of XState's fourth major version,
Khourshid describes the benefit of the approach as the "natural
prevention of impossible states," writing that the library's public
origin traces to a talk given at React Rally in 2017. "XState Version
4 Released," David Khourshid, Medium,
https://medium.com/@DavidKPiano/xstate-version-4-released-665b59409f99,
verified 2026-08-21.

## 10. Consequences

Positive.

- A component modeled as a state machine cannot represent an
  impossible combination of conditions, since it can only ever
  occupy one of its explicitly named states at a time.
- The machine's states and transitions can be visualized as a
  diagram, letting a reviewer or a new team member understand a
  component's full behavior without reading every conditional branch
  in its implementation.
- Every transition the machine allows is declared explicitly, so an
  event the current state does not recognize is a defined no-op
  rather than a silent, unhandled edge case.

Negative.

- A component with genuinely one or two states gains little from
  formal modeling, and the ceremony of defining states, events, and
  transitions is not repaid on a component that simple.
- A team unfamiliar with state machines and statecharts introduces a
  real amount of new vocabulary, hierarchical states, guards, and
  actions, that takes time to use correctly.
- Representing several independent, simultaneously true conditions,
  such as multiple form fields each independently valid or invalid,
  needs additional parallel-state machinery a plain, single
  current-state machine does not provide by default.

## 11. Failure modes and misuse

**Modeling every piece of component state as part of the machine,
including state that has no bearing on which named state the
component is in.** Symptom. The machine's context grows to hold
values, such as a text input's current character count, that never
influence which state the machine transitions to, adding complexity
to the machine's definition without adding any of the
impossible-states-prevented benefit. Cause. Treating the machine as
the single place all component state must live, rather than reserving
it for state that genuinely determines behavior. Fix. Keep state that
does not affect which named state the component occupies in the
framework's own local state primitive, reserving the machine's
context for data the transition logic actually depends on.

**Defining transitions implicitly through scattered conditional
checks instead of an explicit transition table.** Symptom. The
supposed state machine's actual behavior can only be understood by
reading every conditional branch across the component, defeating the
pattern's core benefit of a single, readable, explicit transition
table. Cause. Adopting the vocabulary of states and events without
adopting the discipline of defining transitions in one explicit,
centralized place. Fix. Define every transition in the machine's own
declaration, in one place, rather than scattering equivalent logic
across the surrounding component code.

**Building a machine so large and hierarchical that no single person
can hold its full behavior in their head.** Symptom. Understanding a
single transition needs tracing through several levels of nested
states and guards, and the visualization that was supposed to make
the machine's behavior legible instead becomes too large to be
useful. Cause. Modeling an entire application's behavior as one
machine instead of composing several smaller, focused machines.
Fix. Split a large machine into several smaller machines, each owning
one coherent flow, coordinated through the actor model rather than
folded into a single, unmanageably large definition.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | State Machine UI (XState) | Independent boolean flags | Redux | Hooks (useState) |
|---|---|---|---|---|
| Preventing impossible state combinations | Strong, by construction | Weak, every combination is technically representable | Weak, a reducer's shape can still allow contradictory flags | Weak, the same as independent booleans |
| Visualizing behavior as a diagram | Strong, first-class tooling | Not applicable | Not applicable directly | Not applicable |
| Up-front modeling cost | Moderate to high | Low | Moderate | Low |
| Fit for a component with one or two simple states | Weak, unneeded ceremony | Strong | Weak, unneeded ceremony | Strong |
| Fit for a flow with several interdependent states | Strong | Weak, combination count grows unmanageably | Moderate, needs discipline to avoid the same problem | Weak, the same growth problem |

Reading of the table. State Machine UI wins specifically when a
component's states are genuinely interdependent and the number of
theoretically possible boolean combinations has grown past what a
team can safely reason about by inspection. Independent boolean flags
and plain Hooks remain the right default for a component simple
enough that the combination-explosion risk never actually appears.

## 13. Related and incompatible patterns

- **Redux.** A different, complementary approach to centralizing
  state, addressable together with State Machine UI by using a state
  machine to model one specific flow's behavior while Redux holds
  broader, cross-cutting application state.
- **Hooks.** The framework-native mechanism, such as `useReducer`,
  that a hand-rolled or lightweight state machine is frequently
  implemented on top of.
- **Provider Pattern.** The mechanism used to make a shared machine
  instance, and the current state it reports, available to several
  components without threading it through every intermediate
  component's props.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a component whose independent boolean flags
have started to allow combinations that should not be possible.

1. List every distinct, mutually exclusive condition the component
   can genuinely be in, and name each one as an explicit state.
2. List every event that can cause the component to move from one
   named state to another.
3. Define the transition table, one explicit mapping per state, of
   which event moves to which next state.
4. Replace the independent boolean flags with a single piece of state
   holding the current named state, driven by the transition table
   rather than by several separately updated flags.
5. Add a test asserting every defined transition moves to the correct
   next state, and that an event not defined for the current state is
   correctly treated as a no-op.

Removing the pattern when it stops earning its place, most relevant
when a machine has grown simple enough, or complex enough, that its
formal structure is no longer earning its cost.

1. Confirm the component's states have genuinely simplified to one or
   two conditions with no real interaction between them, rather
   than assuming so without review.
2. Replace the machine with the framework's own local state
   primitive, preserving the same external behavior so consuming code
   requires minimal changes.
3. Remove the machine's definition and any dedicated visualization
   tooling that referenced it, once every consumer has migrated off
   it.

## 15. Testing and verification

Easier because of the pattern.

- Every transition the machine allows is declared in one explicit
  table, so a test can enumerate every defined state-and-event pair
  and assert the correct next state, achieving genuinely exhaustive
  coverage of the component's behavior.
- Because an impossible combination of conditions cannot be
  represented by the machine at all, a whole category of test cases,
  asserting that an impossible combination never happens, becomes
  unnecessary, since the machine's own structure already rules it out.

Harder because of the pattern.

- Testing the full, real integration, a component driven by a real
  machine instance responding to real user interaction, needs wiring
  the machine, its side effects, and the rendered component together,
  rather than testing the machine's transition logic in isolation.
- A machine with several hierarchical or parallel states needs a test
  suite that accounts for every reachable combination of nested
  states, which can grow large for a genuinely complex machine.

Techniques that apply.

- **Transition-table test.** For every defined state, send every
  event the machine recognizes and assert the resulting next state,
  independent of any rendered component.
- **Model-based testing.** Generate test paths automatically by
  walking every reachable path through the machine's own transition
  table, catching a state or transition a hand-written test happened
  to miss.
- **Full-integration test.** Render the component with a real machine
  instance, trigger the interaction that sends an event, and assert
  the component renders correctly for the resulting state.
- **Visualization-driven review.** Render the machine's definition as
  a diagram and have a reviewer walk every path by inspection before
  the component ships, catching a missing or unintended transition a
  purely textual review might miss.

## 16. Observability signals

State Machine UI is a source-level modeling technique with no
independent runtime footprint of its own beyond the state transitions
the underlying implementation already performs, and inventing a
dedicated production signal purely for the pattern would be
dishonest. Two things are worth watching in a codebase that uses it.

What to record.

- The sequence of states a machine actually passes through in
  production, since a machine's explicit transition table is a
  natural, already-available place to capture a complete, ordered
  history of how a component's behavior actually played out for a real
  user.
- The frequency with which an event is sent to the machine while it
  is in a state that does not recognize that event, since a
  consistently ignored event often signals a missing transition or a
  user interacting with a control that should have been disabled.

A healthy state. Every state the machine reaches in production
corresponds to a state genuinely reachable according to its own
transition table, and an event the current state does not recognize
is a rare, expected occurrence rather than a frequent one.

A failing state. An event sent to the machine while in a state that
does not recognize it happening frequently, pointing at a missing
transition or a UI control that should have been disabled in that
state, or the machine reaching a state that its own diagram suggests
should be unreachable, pointing at a bug in the transition table
itself.

## 17. Security and privacy implications

State Machine UI is close to neutral for security, being a
UI-behavior modeling technique rather than a data-handling one, and
inventing a dedicated attack surface here would be dishonest. One
practical implication is worth naming.

**A machine's context, the extended data carried alongside the
current named state, can carry sensitive data the same way any other
piece of component state can, and a machine's visualization or
debugging tooling that displays this context for inspection can
expose it if not used carefully.** Because a state machine's context
is frequently persisted or logged alongside the machine's transition
history for debugging, a team using such tooling should confirm no
piece of context carries a password, a token, or other sensitive data
before persisting or displaying it in a debugging tool, the same
consideration that applies to any other logging surface, worth
naming explicitly here because the visualization tooling that makes
state machines so legible is exactly what makes an accidental
exposure of sensitive context easy to produce.

## 18. References

1. Stately documentation. "XState".
   https://stately.ai/docs/xstate
   Verified 2026-08-21. Source of the defining sentence in dimension 9.
2. David Khourshid. "XState Version 4 Released".
   https://medium.com/@DavidKPiano/xstate-version-4-released-665b59409f99
   Verified 2026-08-21. Source for the 2017 origin and the
   impossible-states-prevention statement in dimension 9.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models the state, event, and
transition-table shape the way XState and similar libraries structure
it, kept free of JSX and any specific framework's package so the
sample compiles as plain TypeScript. Python shows the same conceptual
split using a minimal, framework-agnostic state machine class with an
explicit transition table, since Python has no single dominant
UI-state-machine framework the way TypeScript has XState. Swift shows
the pattern using a minimal enum-driven state machine with an
explicit transition function, closely analogous to the state-machine
approaches used in several SwiftUI architectures. Java, Go, and Rust
are omitted, since none has a dominant, idiomatic UI-component
framework this specifically frontend pattern maps to as directly as
TypeScript and Swift do.

### TypeScript

```typescript
type State = "idle" | "loading" | "success" | "error";
type MachineEvent = "FETCH" | "RESOLVE" | "REJECT" | "RESET";

const transitions: Record<State, Partial<Record<MachineEvent, State>>> = {
  idle: { FETCH: "loading" },
  loading: { RESOLVE: "success", REJECT: "error" },
  success: { RESET: "idle" },
  error: { RESET: "idle" },
};

class Machine {
  private current: State = "idle";

  send(event: MachineEvent): void {
    const nextState = transitions[this.current][event];
    if (nextState !== undefined) {
      this.current = nextState;
    }
  }

  getState(): State {
    return this.current;
  }
}

const machine = new Machine();

console.log("start: " + machine.getState());
machine.send("FETCH");
console.log("after FETCH: " + machine.getState());
machine.send("RESOLVE");
console.log("after RESOLVE: " + machine.getState());
```

### Python

```python
from enum import Enum, auto
from typing import Optional


class State(Enum):
    IDLE = auto()
    LOADING = auto()
    SUCCESS = auto()
    ERROR = auto()


class Event(Enum):
    FETCH = auto()
    RESOLVE = auto()
    REJECT = auto()
    RESET = auto()


TRANSITIONS = {
    (State.IDLE, Event.FETCH): State.LOADING,
    (State.LOADING, Event.RESOLVE): State.SUCCESS,
    (State.LOADING, Event.REJECT): State.ERROR,
    (State.SUCCESS, Event.RESET): State.IDLE,
    (State.ERROR, Event.RESET): State.IDLE,
}


class Machine:
    def __init__(self) -> None:
        self.current: State = State.IDLE

    def send(self, event: Event) -> None:
        next_state: Optional[State] = TRANSITIONS.get((self.current, event))
        if next_state is not None:
            self.current = next_state


if __name__ == "__main__":
    machine = Machine()
    print("start:", machine.current)
    machine.send(Event.FETCH)
    print("after FETCH:", machine.current)
    machine.send(Event.RESOLVE)
    print("after RESOLVE:", machine.current)
```

### Swift

```swift
enum MachineState {
    case idle
    case loading
    case success
    case error
}

enum MachineEvent {
    case fetch
    case resolve
    case reject
    case reset
}

func transition(state: MachineState, event: MachineEvent) -> MachineState {
    switch (state, event) {
    case (.idle, .fetch):
        return .loading
    case (.loading, .resolve):
        return .success
    case (.loading, .reject):
        return .error
    case (.success, .reset), (.error, .reset):
        return .idle
    default:
        return state
    }
}

final class Machine {
    private(set) var current: MachineState = .idle

    func send(_ event: MachineEvent) {
        current = transition(state: current, event: event)
    }
}

let machine = Machine()

print("start: " + String(describing: machine.current))
machine.send(.fetch)
print("after fetch: " + String(describing: machine.current))
machine.send(.resolve)
print("after resolve: " + String(describing: machine.current))
```
