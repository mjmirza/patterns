---
name: State Machine (Embedded)
slug: state-machine
family: 28-embedded-hardware
category: Behavioral
aliases: [Finite State Machine, FSM, Statechart]
first_described: "Miro Samek, state-machine.com, Practical UML Statecharts in C/C++"
maturity: canonical
related: [interrupt-service-routine, polling-loop]
incompatible_with: []
verified: 2026-08-21
---

# State Machine (Embedded)

## 1. Name, aliases, and lineage

The canonical name is State Machine, in the embedded context most often
implemented as a finite state machine, the pattern where a system's
event handling is made explicitly dependent on both the event itself
and the system's current context, rather than on an accumulation of
variables and flags tracking history informally. Miro Samek's own
state-machine.com states the core idea directly. States "are
equivalence classes of past histories of a system, all of which are
equivalent in the sense that the future behavior will be identical."

The alias **Finite State Machine** and its abbreviation **FSM** name
the formal model, a finite set of named states with rules governing
movement between them. **Statechart** names the specific, richer
notation, hierarchical and with orthogonal regions, that extends the
plain finite state machine model, and is the notation Samek's own book
title references directly.

## 2. Problem and context

Event-driven embedded code that tracks context using an accumulation
of variables and flags, without a formal state model, degrades as the
number of events and the history that matters grows. state-machine.com
names this failure mode directly. "The traditional techniques handle
the context manually by storing the history of past events in a
multitude of variables and flags. But this results in code riddled
with a disproportionate amount of convoluted conditional logic that
programmers call 'spaghetti' code." A State Machine solves this by
making the relevant history explicit, as a small, named set of states,
so that "event handling" becomes "explicitly dependent on both the
nature of the event and on the context, state, of the system," rather
than an implicit tangle the programmer must reconstruct from scattered
flags every time a new event handler is added.

## 3. Forces

The pattern balances the following competing pressures.

- **Explicit, reviewable representation of what history matters.**
  Favored. A state is, per state-machine.com's own definition, an
  equivalence class abstracting away irrelevant history and keeping
  only what genuinely affects future behavior, so a reviewer can see
  exactly which distinctions the system tracks.
- **Reduced conditional complexity per event handler.** Favored. Each
  state's event handling only needs to reason about the events valid
  in that specific state, rather than every event handler needing to
  reason about every possible combination of flags the system could be
  in.
- **Upfront design cost.** Sacrificed, to a degree. Identifying the
  genuinely relevant states and the valid transitions between them
  needs real upfront design work that an initial ad hoc flag-and-
  variable approach can appear to skip, at least until the flags
  accumulate into the spaghetti code the pattern exists to prevent.
- **Flexibility for a case the state model did not anticipate.**
  Sacrificed. A formally defined state machine that receives an event
  with no defined transition for the current state must have an
  explicit, deliberate policy for that case, rather than an ad hoc
  flag-based system's implicit tolerance for handling an unanticipated
  combination however the code happens to fall through.

## 4. Applicability and non-applicability

Reach for a State Machine when the following hold.

- The system's behavior genuinely depends on a real history of
  past events, not merely the most recent one, making an explicit
  state model a real simplification over tracking that history with
  ad hoc flags.
- The number of distinct events and the contexts they can occur in is
  large enough that an ad hoc, flag-based approach would genuinely
  degrade into the "convoluted conditional logic" state-machine.com's
  own documentation names as spaghetti code.
- The team can invest the real upfront design work to identify the
  genuinely relevant states and transitions, rather than reaching for
  the pattern's structure without doing that design work first.

Do NOT reach for a State Machine in these cases, and the reason
matters more than the rule.

- **The system's behavior genuinely depends only on the single most
  recent event, with no real history to track**, a purely
  stateless event handler, one that reacts identically to the same
  event regardless of what happened before, gains nothing from the
  pattern's state-tracking machinery.
- **The number of genuinely distinct states and events is small enough
  that a direct, ad hoc handler is already simple and reviewable**, a
  handful of events with no real interaction between them does
  not yet need the formal structure, and imposing it prematurely adds
  design overhead for a problem that is not yet real.
- **The team has not done the real design work to identify the
  system's genuine states**, reaching for the pattern's code structure,
  a switch on a state variable, without first doing the equivalence-
  class analysis state-machine.com's own definition describes,
  produces a state machine in name only, one that still tangles
  unrelated concerns inside its state-handling code.

## 5. Structure

A State Machine has three structural parts.

- **The states**, the finite set of named contexts, each one, per
  state-machine.com's own definition, an equivalence class of past
  event histories that produce identical future behavior.
- **The events**, the inputs the system reacts to, each one either
  triggering a transition in the current state or being explicitly
  ignored, per the current state's own defined behavior.
- **The transitions**, the rules connecting a specific state and event
  pair to a resulting state, state-machine.com's own definition stating
  their purpose directly. "These rules are called transitions and
  capture the fact that some events contribute to the relevant history
  while others do not."

## 6. ASCII structure diagram

```
                event A
  +--------+  ------------>  +--------+
  | State 1 |                 | State 2 |
  +--------+  <------------  +--------+
                event B
       |
       | event C
       v
  +--------+
  | State 3 |
  +--------+
```

## 7. Dynamics

The trace below shows the state machine receiving two events.

```
Machine starts in State 1

the machine's current state is State 1

Event A arrives

the machine looks up the transition defined for State 1 plus event A
   |-- the defined transition fires, moving the machine to State 2
   |-- the current state is now State 2

Event B arrives

the machine looks up the transition defined for State 2 plus event B
   |-- the defined transition fires, moving the machine back to
       State 1
   |-- the current state is now State 1 again

An unexpected event arrives in a state with no defined transition for
it

the machine's explicit, deliberate policy for this case runs, per
dimension 3's forces, either ignoring the event or raising a
deliberate error, never an implicit, undefined fallthrough
```

## 8. Implementation variants

**Switch-on-state, table-driven.** The current state is stored in a
single variable, and a switch statement, or a lookup table keyed by
state and event, dispatches to the correct transition logic, the
simplest and most common variant in plain C embedded code.

**Function-pointer state table.** Each state is represented by a set of
function pointers for its valid events, and the current state variable
holds a pointer to the active set, letting a transition simply update
that pointer rather than dispatching through a switch on every event.

**Hierarchical state machine, the statechart variant.** States can
nest, so a substate inherits the event handling of its parent state
unless it overrides it, the richer model Samek's own book title
references, useful when many states genuinely share common event
handling that a plain flat finite state machine would otherwise
duplicate. Zephyr's own State Machine Framework documents exactly this
shape. "Ancestor entry actions are executed before the sibling entry
actions," and "transitioning from one sibling to another with a shared
ancestry does not re-execute the ancestor's entry action," letting the
shared behavior live once, in the parent, rather than being duplicated
into every child state.

## 9. Known production uses

**state-machine.com, Miro Samek's own site, defining the core model
and the failure mode it prevents.** The site states the definition of
a state directly. States "are equivalence classes of past histories of
a system, all of which are equivalent in the sense that the future
behavior will be identical," and names the transition's purpose.
"These rules are called transitions and capture the fact that some
events contribute to the relevant history while others do not." It
also names the ad hoc alternative's failure mode directly. "The
traditional techniques handle the context manually by storing the
history of past events in a multitude of variables and flags. But this
results in code riddled with a disproportionate amount of convoluted
conditional logic that programmers call 'spaghetti' code." Quantum
Leaps, "Finite State Machines,"
https://www.state-machine.com/fsm, verified 2026-08-21.

**The Zephyr Project's own State Machine Framework documentation, on
the hierarchical variant's transition and propagation mechanism.**
Zephyr states the state and transition mechanism directly. "A state is
represented by three functions, where one function implements the
Entry actions, another function implements the Run actions, and the
last function implements the Exit actions," and "the `smf_set_state()`
function is used" to move between states. The run action's own return
value "determines if the state machine propagates the event to parent
run actions, `SMF_EVENT_PROPAGATE`, or if the event was handled by the
run action, `SMF_EVENT_HANDLED`." The Zephyr Project, "State Machine
Framework,"
https://docs.zephyrproject.org/latest/services/smf/index.html,
verified 2026-08-21.

## 10. Consequences

Positive.

- Event handling becomes, per state-machine.com's own description,
  "explicitly dependent on both the nature of the event and on the
  context, state, of the system," making the relevant history visible
  and reviewable rather than implicit in scattered flags.
- Each state's event handling only needs to reason about the events
  genuinely valid in that state, reducing the conditional complexity
  any single handler needs to manage.
- A state machine with a genuinely complete transition table has an
  explicit, deliberate policy for every event in every state, rather
  than an ad hoc system's implicit, undefined behavior for a case
  nobody anticipated.

Negative.

- Identifying the genuinely relevant states and their valid
  transitions needs real upfront design work, a cost an ad hoc
  flag-based approach can appear to avoid, at least initially.
- A state machine imposed on a system whose behavior does not
  genuinely depend on a real, tracked history adds real structure for a
  problem the system does not actually have.
- A state machine built without genuine equivalence-class analysis, a
  switch on a state variable with no real design behind it, gains none
  of the pattern's real benefit while still carrying its structural
  cost.

## 11. Failure modes and misuse

**Building a state machine with no real upfront design, treating the
switch-statement structure alone as the pattern.** Symptom. The
resulting code still tangles unrelated concerns inside its per-state
handlers, and the states chosen do not genuinely correspond to
distinct future-behavior equivalence classes, so the code is no
clearer than the ad hoc flags it was meant to replace. Cause. Reaching
for the pattern's code shape without first doing the genuine
equivalence-class analysis state-machine.com's own definition
describes, identifying which past history actually matters. Fix. Do
the real design work first, identify the system's genuinely distinct
states by asking which past event histories produce identical future
behavior, before writing the switch statement or the transition table.

**Leaving an event with no defined transition in a given state
unhandled, with no deliberate policy.** Symptom. The system receives an
event the current state's transition table does not define, and the
resulting behavior is whatever the switch statement's implicit
fallthrough or default case happens to do, rather than a deliberate,
reviewed decision. Cause. Building the transition table incompletely,
without explicitly deciding, for every state and event combination,
whether the event should be ignored, should raise an error, or should
trigger a specific defined transition. Fix. Make the policy for an
undefined event in a given state an explicit, reviewed decision for
every state, rather than relying on whatever the implementation's
default behavior happens to produce.

**Letting the number of states grow without periodically reassessing
whether a flat finite state machine still fits, rather than the
hierarchical variant.** Symptom. Many states end up duplicating nearly
identical event-handling logic, because a large group of them
genuinely share common behavior that a flat model has no way to
express once, forcing that shared logic to be copied into every state
that needs it. Cause. Continuing to add states to a flat finite state
machine as the system grows, without recognizing that a hierarchical
statechart's substate inheritance would let the shared logic live in
one place. Fix. When a genuine, real group of states shares
common event handling, move to the hierarchical variant so that shared
behavior is expressed once, in a parent state, rather than duplicated
across every state that needs it.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | State Machine | Ad hoc flags and variables | A single, large monolithic handler |
|---|---|---|---|
| Explicit, reviewable representation of relevant history | Strong, the states are named and reviewable | Weak, the relevant history is implicit across scattered flags | Weak, history tracking is embedded inside one large function |
| Reduced conditional complexity per event handler | Strong, each state only reasons about its own valid events | Weak, every handler may need to reason about every flag combination | Weak, all logic lives in one place with no structural separation |
| Upfront design cost | Moderate, needs genuine equivalence-class analysis | Low initially, but grows as flags accumulate | Low initially, but grows as the handler's own complexity accumulates |
| Flexibility for an unanticipated event | Weak, needs an explicit, deliberate policy | Strong in the sense that undefined behavior is easy to produce, though this is rarely a genuine benefit | Weak, an unanticipated case falls into whatever the handler's own logic happens to do |

Reading of the table. A State Machine wins specifically when the
system's behavior genuinely depends on a real, tracked history and the
number of distinct events and contexts is large enough that an ad hoc
approach would degrade. For a small, genuinely simple event set with
no real history, the pattern's upfront design cost is not yet
justified.

## 13. Related and incompatible patterns

- **Interrupt Service Routine.** An interrupt context frequently
  signals an event into a state machine running in task context,
  keeping the interrupt handler itself short while the state machine,
  running as ordinary task-context code, does the actual state-
  dependent processing.
- **Polling Loop.** A state machine's event-processing step is often
  driven from inside a polling loop, on a bare-metal system with no
  RTOS, each loop iteration checking for a new event and running the
  state machine's transition logic if one has arrived.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to code currently tracking context with an
accumulation of ad hoc flags and variables.

1. Identify the genuinely relevant history, asking which past event
   sequences produce identical future behavior, following
   state-machine.com's own equivalence-class definition of a state.
2. Name the resulting states explicitly, and define the transition
   table, deciding, for every state and event combination, what the
   resulting state and any deliberate no-transition policy should be.
3. Replace the ad hoc flags and variables with the single current-state
   variable the new transition table drives.
4. Confirm every event handler now reasons only about the events valid
   in its own state, rather than every possible flag combination the
   old code had to consider.

Removing the pattern when it stops earning its place, most relevant
when the number of genuinely distinct states has shrunk to the point
that the formal structure outweighs its benefit.

1. Confirm, concretely, that the remaining states no longer represent
   genuinely distinct future-behavior equivalence classes, rather
   than assuming so without checking the real transition table.
2. Fold the remaining, genuinely simple logic back into a direct event
   handler, removing the state variable and the transition table.
3. Confirm the folded code's behavior for every event genuinely
   matches what the state machine previously defined, including its
   deliberate policy for any event with no defined transition.

## 15. Testing and verification

Easier because of the pattern.

- A test can drive the state machine through a specific sequence of
  events and assert the resulting current state directly, verifying
  the transition table's correctness independent of whatever code
  eventually reacts to that state.
- Because the transition table is explicit, a test can systematically
  walk every state and event combination, asserting either the defined
  transition or the deliberate no-transition policy, a coverage goal
  an ad hoc flag-based system has no equivalent structure to organize
  around.

Harder because of the pattern.

- Verifying a hierarchical state machine's inherited event handling
  needs tests that specifically exercise a substate's fallback to its
  parent's handling, a category of test easy to omit if only each
  substate's own explicitly overridden events are tested.
- Confirming the chosen states genuinely correspond to real,
  genuinely distinct future-behavior equivalence classes needs a
  design review, a category of verification no automated test alone
  can perform.

Techniques that apply.

- **Full transition-table coverage tests.** Systematically drive every
  defined state and event combination, and assert the resulting state
  matches the transition table exactly.
- **Undefined-event policy tests.** For every state, assert the
  system's deliberate policy fires correctly for an event with no
  defined transition in that state, rather than an unverified,
  implicit fallthrough.
- **Hierarchical inheritance tests, for the statechart variant.**
  Specifically exercise a substate's fallback to its parent state's
  event handling, confirming the inheritance behaves as designed.
- **State-equivalence design review.** Review the chosen states
  directly against state-machine.com's own equivalence-class
  definition, confirming each one genuinely represents a distinct
  future-behavior class rather than an arbitrary code-organization
  choice.

## 16. Observability signals

What to record.

- The sequence of states the machine actually passes through in real
  operation, since this signal directly reveals whether the system's
  real-world event sequences match what the transition table's design
  anticipated.
- The frequency with which the deliberate undefined-event policy fires
  in a given state, since a rising frequency points at an event
  arriving in a context the original design did not anticipate.

A healthy state. The state machine's real-world state sequence matches
what the design anticipated, and the deliberate undefined-event policy
fires rarely or never, showing the transition table's coverage of
real, actually-occurring event and state combinations.

A failing state. The undefined-event policy fires with real
frequency in a specific state, pointing at a real event and context
combination the original design did not anticipate, needing either a
new defined transition or a deliberate reconsideration of that
policy's own correctness.

## 17. Security and privacy implications

**A state machine that accepts an externally supplied event without
validating it can be driven into a defined but security-relevant state
transition by an attacker who understands the transition table.** If
the events a state machine reacts to are reachable from untrusted,
external input, an attacker who can observe or infer the transition
table can deliberately construct a sequence of events designed to
reach a specific state, one that, for example, bypasses an
authentication check the designer assumed could only be reached
through a legitimate event sequence. Any state machine whose events
originate from external, untrusted input needs its transition table
reviewed specifically for this concern, confirming that no sequence of
externally-triggerable events can reach a security-sensitive state
through a path the design did not intend to permit.

## 18. References

1. Quantum Leaps. "Finite State Machines".
   https://www.state-machine.com/fsm
   Verified 2026-08-21. Source of the state and transition definition
   quotes, and the spaghetti-code failure-mode quote, used in
   dimensions 1, 2, 3, 5, and 9.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. C models the switch-on-state, table-driven variant directly, the
shape embedded firmware state machines are most commonly written in.
Python shows the same conceptual shape using a minimal, host-testable
implementation, the pattern's transition-table-testing variant from
dimension 15, expressed portably. Swift shows the same conceptual
shape using an enum to represent the finite set of states, analogous
to how a native application's own event-driven UI logic might model a
small, explicit set of states. Java, Go, and Rust are omitted, since
the pattern's real home is C and the two languages chosen already
cover its production and its testable-table shapes.

### C

```c
#include <stdio.h>

typedef enum { STATE_IDLE, STATE_RUNNING, STATE_STOPPED } state_t;
typedef enum { EVENT_START, EVENT_STOP, EVENT_RESET } event_t;

static state_t transition(state_t current, event_t ev) {
    switch (current) {
        case STATE_IDLE:
            if (ev == EVENT_START) {
                return STATE_RUNNING;
            }
            return current;
        case STATE_RUNNING:
            if (ev == EVENT_STOP) {
                return STATE_STOPPED;
            }
            return current;
        case STATE_STOPPED:
            if (ev == EVENT_RESET) {
                return STATE_IDLE;
            }
            return current;
        default:
            return current;
    }
}

static const char *state_name(state_t s) {
    switch (s) {
        case STATE_IDLE: return "idle";
        case STATE_RUNNING: return "running";
        case STATE_STOPPED: return "stopped";
        default: return "unknown";
    }
}

int main(void) {
    state_t current = STATE_IDLE;

    current = transition(current, EVENT_START);
    printf("after start: %s", state_name(current));
    putchar(10);

    current = transition(current, EVENT_STOP);
    printf("after stop: %s", state_name(current));
    putchar(10);

    current = transition(current, EVENT_RESET);
    printf("after reset: %s", state_name(current));
    putchar(10);

    return 0;
}
```

### Python

```python
from enum import Enum, auto


class State(Enum):
    IDLE = auto()
    RUNNING = auto()
    STOPPED = auto()


class Event(Enum):
    START = auto()
    STOP = auto()
    RESET = auto()


def transition(current: State, event: Event) -> State:
    if current is State.IDLE and event is Event.START:
        return State.RUNNING
    if current is State.RUNNING and event is Event.STOP:
        return State.STOPPED
    if current is State.STOPPED and event is Event.RESET:
        return State.IDLE
    return current


if __name__ == "__main__":
    current = State.IDLE

    current = transition(current, Event.START)
    print("after start: " + current.name)

    current = transition(current, Event.STOP)
    print("after stop: " + current.name)

    current = transition(current, Event.RESET)
    print("after reset: " + current.name)
```

### Swift

```swift
enum MachineState {
    case idle
    case running
    case stopped
}

enum MachineEvent {
    case start
    case stop
    case reset
}

func transition(current: MachineState, event: MachineEvent) -> MachineState {
    switch (current, event) {
    case (.idle, .start):
        return .running
    case (.running, .stop):
        return .stopped
    case (.stopped, .reset):
        return .idle
    default:
        return current
    }
}

var current = MachineState.idle

current = transition(current: current, event: .start)
print("after start: " + String(describing: current))

current = transition(current: current, event: .stop)
print("after stop: " + String(describing: current))

current = transition(current: current, event: .reset)
print("after reset: " + String(describing: current))
```
