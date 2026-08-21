---
name: Undo Stack
slug: undo-stack
family: 13-frontend-ui
category: Behavioral
aliases: [Undo History, Past-Present-Future State, Command History]
first_described: "Gamma, Helm, Johnson, Vlissides, Design Patterns, 1994, the Command pattern's undo application"
maturity: canonical
related: [reducer-hook, error-boundary]
incompatible_with: []
verified: 2026-08-21
---

# Undo Stack

## 1. Name, aliases, and lineage

The canonical name is Undo Stack, the pattern where every reversible
action a user takes is recorded in an ordered history, so the
application can step backward to an earlier state, and forward again,
rather than the user's mistakes being permanent. The Command pattern's
own description of this application states the storage shape
directly. "The command history is a stack that contains all executed
command objects along with related backups of the application's
state."

The alias **Undo History** names the same record by its more everyday
term. **Past-Present-Future State** names the specific three-part
shape a widely used implementation of this pattern gives its state,
described in that library's own documentation. "past," "present," and
"future." **Command History** ties the pattern directly back to its
lineage in the Command design pattern, where an executed command
object is retained specifically so its effect can later be reversed.

## 2. Problem and context

An interactive application where every user action mutates state
irreversibly forces a user who makes a mistake, whether a wrong edit,
an accidental delete, or a change they simply reconsider, to either
manually reconstruct the prior state by hand or lose the work
entirely. An Undo Stack solves this by recording every reversible
action as it happens, in an ordered history, so a single undo command
can step the application back to the state immediately before that
action, and a redo command can step forward again if the user changes
their mind a second time. A widely used implementation states the
resulting state shape directly, wrapping the underlying state as
"past," "present," and "future," which names exactly what the pattern
tracks, everything already undone into the past, the current state,
and everything available to redo back out of that past.

## 3. Forces

The pattern balances the following competing pressures.

- **Recoverability for the user.** Favored. Every reversible action
  becomes safe to attempt, since its effect can be undone, which
  directly lowers the cost of a wrong or accidental action.
- **Memory and storage cost.** Sacrificed, to a degree that depends on
  the implementation. A history that stores the Command pattern's own
  "backups of the application's state" for every action grows with
  every action taken, and a long session can accumulate a real memory
  cost if the history is kept unbounded.
- **Correctness of state reconstruction.** Favored, when built
  correctly. A step backward must genuinely restore the exact prior
  state, not an approximation of it, or the user's trust in undo
  itself breaks the moment it produces a subtly wrong result.
- **Simplicity of the action-recording mechanism.** Sacrificed to some
  degree. Every action that should be undoable must be deliberately
  wired to record itself into the history, rather than mutating state
  directly and without any recorded history.

## 4. Applicability and non-applicability

Reach for an Undo Stack when the following hold.

- The application performs actions genuinely valuable to reverse, an
  edit, a deletion, a reordering, or any change a user might
  reasonably reconsider or trigger by mistake.
- The cost of recording each action's history, in memory or in stored
  state snapshots, is genuinely affordable for the application's real
  usage pattern, either because sessions are short, actions are
  infrequent, or the history is deliberately bounded.
- Correctly reconstructing prior state is achievable for the
  application's actual data model, without the reconstruction itself
  introducing subtle inconsistencies.

Do NOT reach for an Undo Stack in these cases, and the reason matters
more than the rule.

- **The application's actions are not genuinely reversible in the
  first place**, an action that triggers an external, real-world
  effect, such as sending an email or charging a payment, cannot
  genuinely be undone by restoring in-memory state, and building an
  undo stack around it creates a false sense of safety.
- **The memory cost of the history genuinely does not fit the
  application's real constraints**, a resource-constrained or very
  long-running session accumulating full state snapshots for every
  action can grow the memory footprint past what the application can
  sustain, without a bounded or more selective history.
- **The state being tracked is derived, rather than authoritative**,
  wrapping state that is itself only ever recomputed from some other
  source of truth in an undo stack duplicates and complicates state
  that should instead simply be recomputed after undoing the change to
  its actual source.

## 5. Structure

An Undo Stack has three structural parts, matching the widely used
implementation's own described shape.

- **The past**, an ordered collection of prior states, or of the
  commands whose reversal would reconstruct them, most recent last.
- **The present**, the application's actual current state, the one the
  user is looking at and interacting with right now.
- **The future**, an ordered collection of states that were undone out
  of the present, available to redo back into it, cleared the moment a
  genuinely new action is taken rather than an undo or redo.

## 6. ASCII structure diagram

```
  +-----------------------------------------------------------+
  |  past                    present                 future     |
  |  [ s0, s1, s2 ]  ---->   s3 (current)   <----  [ s4, s5 ]   |
  |                                                             |
  |  undo. pop the last of past, push present into future        |
  |  redo. pop the first of future, push present into past       |
  |  a new action. clear future, push present into past           |
  +-----------------------------------------------------------+
```

## 7. Dynamics

The trace below shows a user taking an action, undoing it, and redoing
it.

```
User takes a new action

the user performs an action that changes state
   |-- the current present state is pushed onto the past
   |-- the future is cleared, since a new action invalidates any
       previously undone states
   |-- the new resulting state becomes the present

User undoes the action

the user issues an undo command
   |-- the most recent state is popped off the past
   |-- the current present is pushed onto the future, so it can be
       redone later
   |-- the popped state becomes the new present

User redoes the action

the user issues a redo command
   |-- the earliest state is popped off the future
   |-- the current present is pushed back onto the past
   |-- the popped state becomes the new present again
```

## 8. Implementation variants

**Full state snapshot per action.** Every recorded history entry is a
complete copy of the application's state at that point, the simplest
to reason about, at the highest memory cost per entry.

**Command-object history with inverse operations.** Following the
Command pattern's own described shape, each history entry is the
executed command object itself, "along with related backups of the
application's state," and undoing an entry replays its stored inverse
rather than restoring a full snapshot, trading some implementation
complexity for a smaller per-entry footprint.

**Bounded history.** The past and future collections are capped at a
fixed length, discarding the oldest entries once the cap is reached,
directly addressing the memory-cost force from dimension 3 for a
long-running or resource-constrained session.

**Diff-based history.** Each history entry stores only the difference
between consecutive states rather than a full snapshot of either,
reducing memory cost further at the price of needing a reliable
diffing and patching mechanism for the application's actual data
shape.

## 9. Known production uses

**The Command pattern's own description, defining the storage shape
this pattern is built on.** The pattern's own explanation states the
history's shape directly. "The command history is a stack that
contains all executed command objects along with related backups of
the application's state." Refactoring.Guru, "Command,"
https://refactoring.guru/design-patterns/command, verified 2026-08-21.

**redux-undo, a widely used implementation of the pattern for Redux
applications.** The library's own documentation states its mechanism
directly. "`redux-undo` is a reducer enhancer, a higher-order reducer.
It provides the `undoable` function, which takes an existing reducer
and a configuration object and enhances your existing reducer with
undo functionality," wrapping the resulting state into the described
"past," "present," and "future" shape. omnidan, "redux-undo,"
https://github.com/omnidan/redux-undo, verified 2026-08-21.

## 10. Consequences

Positive.

- A user who makes a mistake, whether an accidental edit or a
  deliberate change they reconsider, can reverse it directly, lowering
  the real cost of taking an action in the first place.
- The command-object variant, storing the Command pattern's own
  described "backups of the application's state" alongside the
  command itself, keeps the reversal mechanism tied directly to a
  well-established, well-understood pattern rather than an ad hoc one.
- A bounded or diff-based history keeps the pattern's real memory cost
  proportionate to what a specific application actually needs, rather
  than growing unboundedly.

Negative.

- An unbounded history storing a full state snapshot per action grows
  its memory footprint with every action taken, a real cost in a
  long-running or resource-constrained session.
- Every action that should be undoable must be deliberately wired to
  record itself into the history, adding real implementation surface
  compared to mutating state directly.
- Reconstructing prior state incorrectly, even subtly, breaks the
  user's trust in undo itself the moment it produces a wrong result,
  which is a genuinely higher bar to hold than the application's
  ordinary state transitions.

## 11. Failure modes and misuse

**Treating a genuinely irreversible, external action as undoable.**
Symptom. A user undoes an action in the application's own UI, and the
UI reflects the reversal, but the real, external effect the action
triggered, an email sent, a payment charged, a message delivered, has
already happened and is not actually undone. Cause. Wrapping an
action that has a real external side effect in the same undo
mechanism used for purely in-memory state changes, without
distinguishing the two. Fix. Reserve the undo stack for actions whose
effect is genuinely and entirely reversible in-memory, and handle a
genuinely external action with its own explicit confirmation step
instead of a false undo affordance.

**Letting the history grow unbounded in a long-running session.**
Symptom. A session left open for a long time accumulates enough
history entries that the application's memory footprint grows
noticeably, eventually degrading performance or exhausting available
memory. Cause. Storing a full state snapshot per action with no cap on
how many entries the past and future collections are allowed to hold.
Fix. Bound the history to a fixed length, discarding the oldest
entries once the cap is reached, or move to the command-object or
diff-based variant to reduce the per-entry cost.

**Not clearing the future when a genuinely new action is taken.**
Symptom. A user undoes an action, then takes a different, new action,
and a subsequent redo unexpectedly reapplies the OLD, now-invalid
future state instead of doing nothing or redoing the new action,
producing state that does not correspond to any coherent sequence of
the user's real actions. Cause. Failing to clear the future collection
the moment a genuinely new action is taken, rather than only clearing
it on undo and redo. Fix. Clear the future collection whenever a new,
non-undo, non-redo action changes state, exactly as the pattern's own
dynamics in dimension 7 specify.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Undo Stack | No undo, direct mutation | Manual confirmation dialogs |
|---|---|---|---|
| Recoverability for the user | Strong, any recorded action can be reversed | Weak, a mistake is permanent once made | Moderate, prevents some mistakes upfront but offers no reversal after |
| Memory and storage cost | Moderate to high, depending on the implementation variant chosen | Minimal, no history is retained at all | Minimal, no history is retained at all |
| Correctness of state reconstruction | Strong, when the history is built and tested correctly | Not applicable, there is no reconstruction to get wrong | Not applicable |
| Simplicity of the action-recording mechanism | Weak, every undoable action needs deliberate wiring | Strong, actions simply mutate state directly | Strong for the dialog itself, though it adds a distinct interruption on every risky action |

Reading of the table. An Undo Stack wins specifically when actions are
genuinely reversible and the real memory cost of recording history
fits the application's constraints. A confirmation dialog remains the
better fit for a genuinely irreversible action, where reversing after
the fact is not actually possible.

## 13. Related and incompatible patterns

- **Reducer Hook.** The command-object and diff-based variants of an
  undo stack are frequently implemented as a reducer, dispatching a
  distinct undo or redo action alongside the application's ordinary
  actions, reusing the same current-state-and-dispatch shape a reducer
  hook already provides.
- **Error Boundary.** An error boundary and an undo stack address
  different failure classes, an error boundary catches a rendering
  failure the application did not intend, while an undo stack reverses
  a state change the user deliberately made and later wants reversed.
  The two are not in conflict and often sit side by side in the same
  application.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an application whose state currently mutates
directly with no history.

1. Identify which specific actions are genuinely and entirely
   reversible in-memory, rather than assuming every action qualifies.
2. Choose an implementation variant, a full snapshot, a command-object
   history, or a diff-based history, based on the application's real
   memory constraints from dimension 3.
3. Wrap the identified actions so each one records the state, or the
   command and its inverse, into the past collection before applying
   its effect.
4. Wire an undo command to pop the most recent entry off the past,
   push the current present onto the future, and restore the popped
   entry as the new present.
5. Wire a redo command to do the reverse, and confirm every genuinely
   new action clears the future collection.

Removing the pattern when it stops earning its place, most relevant
when the recorded history's real memory cost has grown to outweigh
the recoverability benefit for a specific application.

1. Confirm, concretely, that the history's memory cost is the actual
   problem, rather than assuming so without measuring real usage.
2. Consider a bounded or diff-based variant first, since it may
   resolve the memory cost without removing the recoverability benefit
   entirely.
3. If removal is genuinely the right call, remove the action-recording
   wiring and the undo and redo commands, confirming no part of the
   application still assumes a history is being kept.

## 15. Testing and verification

Easier because of the pattern.

- A test can perform a sequence of actions, undo some of them, and
  assert the resulting state matches exactly what an equivalent
  shorter sequence of actions would have produced, directly verifying
  the reconstruction the pattern is meant to provide.
- Because the history's shape is explicit, past, present, and future,
  a test can assert its length and contents directly after a sequence
  of undo and redo commands, without needing to infer the history from
  indirect side effects.

Harder because of the pattern.

- Verifying the command-object or diff-based variants correctly
  reconstruct state needs tests covering every kind of action the
  application supports, since a single action whose inverse is
  implemented incorrectly can silently produce a wrong result that a
  simpler full-snapshot approach would not have been at risk of.
- Confirming the history is correctly bounded, and does not grow
  unboundedly in a genuinely long-running session, needs a test that
  simulates a long sequence of actions, a category of test easy to
  omit if only a short, typical sequence is tested.

Techniques that apply.

- **Round-trip tests.** Perform a sequence of actions, undo all of
  them, and assert the resulting state exactly matches the state
  before any action was taken.
- **Redo-after-new-action tests.** Undo an action, take a genuinely
  new action, and assert the future collection was correctly cleared
  rather than allowing a stale redo.
- **History-length tests.** For a bounded history, perform more
  actions than the configured cap and assert the oldest entries were
  correctly discarded.
- **Inverse-correctness tests, for the command-object variant.** For
  every distinct kind of undoable action, assert its stored inverse
  genuinely reconstructs the exact prior state, not an approximation.

## 16. Observability signals

What to record.

- The real, measured size of the history, in entry count or in
  memory, across actual production sessions, since a rising size
  points at either a genuinely long session or a history that is not
  being bounded when it should be.
- The frequency of undo and redo commands relative to ordinary
  actions, since this signal directly measures how much real value the
  pattern is providing for the application's actual users.

A healthy state. The history's real memory footprint stays within the
bounds the implementation was designed for, and undo and redo commands
correctly restore the state a user actually expects, with no reports
of a wrong or inconsistent result after an undo.

A failing state. The history's memory footprint grows unboundedly in a
genuinely long session, pointing at a missing or misconfigured bound,
or users report that undo produces state that does not match what
they expected, pointing at an incorrect state-reconstruction
implementation that needs the round-trip tests from dimension 15
tightened.

## 17. Security and privacy implications

**An undo history that retains full state snapshots can retain
sensitive data for longer than the application's own data-retention
policy intends, even after the user believes that data has been
removed.** If a user deletes a piece of sensitive information from the
application's current state, but the deleted value still exists in an
earlier snapshot sitting in the past collection of the undo history,
that value has not actually been removed from memory, and a
sufficiently long or unbounded history can retain it well past when
the application's own data-handling policy would otherwise expect it
gone. Bounding the history, or deliberately excluding genuinely
sensitive fields from what gets snapshotted, is a real consideration
for any application whose undoable state includes sensitive data.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. TypeScript models the past-present-future state shape directly,
the same shape a widely used implementation gives it, kept free of
JSX and any specific framework's package so the sample compiles as
plain TypeScript. Python shows the same conceptual shape using a
minimal, framework-agnostic implementation, since the pattern is a
portable data-structure idea rather than one tied to a specific
browser API. Swift shows the same conceptual shape using a minimal
model, analogous to how a native application's own document editing
model might track undoable state changes. Java, Go, and Rust are
omitted, since the pattern's shape is fully captured by these three,
and none of the remaining languages offers a genuinely different
idiomatic expression of it for this catalogue's purposes.

### TypeScript

```typescript
interface HistoryState<T> {
  past: T[];
  present: T;
  future: T[];
}

function createHistory<T>(initial: T): HistoryState<T> {
  return { past: [], present: initial, future: [] };
}

function applyAction<T>(history: HistoryState<T>, nextState: T): HistoryState<T> {
  return {
    past: [...history.past, history.present],
    present: nextState,
    future: [],
  };
}

function undo<T>(history: HistoryState<T>): HistoryState<T> {
  if (history.past.length === 0) {
    return history;
  }
  const previous = history.past[history.past.length - 1];
  return {
    past: history.past.slice(0, -1),
    present: previous,
    future: [history.present, ...history.future],
  };
}

function redo<T>(history: HistoryState<T>): HistoryState<T> {
  if (history.future.length === 0) {
    return history;
  }
  const next = history.future[0];
  return {
    past: [...history.past, history.present],
    present: next,
    future: history.future.slice(1),
  };
}

let history = createHistory({ text: "" });
history = applyAction(history, { text: "hello" });
history = applyAction(history, { text: "hello world" });
console.log("after two actions:", history.present);

history = undo(history);
console.log("after undo:", history.present);

history = redo(history);
console.log("after redo:", history.present);
```

### Python

```python
from dataclasses import dataclass, field


@dataclass
class HistoryState:
    past: list
    present: object
    future: list = field(default_factory=list)


def create_history(initial):
    return HistoryState(past=[], present=initial, future=[])


def apply_action(history: HistoryState, next_state) -> HistoryState:
    return HistoryState(
        past=history.past + [history.present],
        present=next_state,
        future=[],
    )


def undo(history: HistoryState) -> HistoryState:
    if not history.past:
        return history
    previous = history.past[-1]
    return HistoryState(
        past=history.past[:-1],
        present=previous,
        future=[history.present] + history.future,
    )


def redo(history: HistoryState) -> HistoryState:
    if not history.future:
        return history
    nxt = history.future[0]
    return HistoryState(
        past=history.past + [history.present],
        present=nxt,
        future=history.future[1:],
    )


if __name__ == "__main__":
    h = create_history({"text": ""})
    h = apply_action(h, {"text": "hello"})
    h = apply_action(h, {"text": "hello world"})
    print("after two actions:", h.present)

    h = undo(h)
    print("after undo:", h.present)

    h = redo(h)
    print("after redo:", h.present)
```

### Swift

```swift
struct HistoryState<T> {
    var past: [T]
    var present: T
    var future: [T]
}

func createHistory<T>(initial: T) -> HistoryState<T> {
    HistoryState(past: [], present: initial, future: [])
}

func applyAction<T>(_ history: HistoryState<T>, nextState: T) -> HistoryState<T> {
    var past = history.past
    past.append(history.present)
    return HistoryState(past: past, present: nextState, future: [])
}

func undo<T>(_ history: HistoryState<T>) -> HistoryState<T> {
    guard let previous = history.past.last else {
        return history
    }
    var past = history.past
    past.removeLast()
    var future = history.future
    future.insert(history.present, at: 0)
    return HistoryState(past: past, present: previous, future: future)
}

func redo<T>(_ history: HistoryState<T>) -> HistoryState<T> {
    guard let next = history.future.first else {
        return history
    }
    var past = history.past
    past.append(history.present)
    var future = history.future
    future.removeFirst()
    return HistoryState(past: past, present: next, future: future)
}

struct DocumentState {
    let text: String
}

var history = createHistory(initial: DocumentState(text: ""))
history = applyAction(history, nextState: DocumentState(text: "hello"))
history = applyAction(history, nextState: DocumentState(text: "hello world"))
print("after two actions: " + history.present.text)

history = undo(history)
print("after undo: " + history.present.text)

history = redo(history)
print("after redo: " + history.present.text)
```

## 18. References

1. Refactoring.Guru. "Command".
   https://refactoring.guru/design-patterns/command
   Verified 2026-08-21. Source of the command-history-as-a-stack quote
   used in dimensions 1, 2, 3, 8, 9, and 10.
2. omnidan. "redux-undo".
   https://github.com/omnidan/redux-undo
   Verified 2026-08-21. Source of the reducer-enhancer mechanism quote
   and the past-present-future state shape quote used in dimensions 1,
   2, 5, and 9.
