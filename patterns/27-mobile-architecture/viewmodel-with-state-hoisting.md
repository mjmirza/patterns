---
name: ViewModel with State Hoisting
slug: viewmodel-with-state-hoisting
family: 27-mobile-architecture
category: Structural
aliases: [State Hoisting, Stateless Composable Pattern]
first_described: 'Google, Jetpack Compose "Thinking in Compose" and "State and Jetpack Compose" documentation'
maturity: canonical
related: [unidirectional-data-flow, mvvm-c]
incompatible_with: []
verified: 2026-08-22
---

# ViewModel with State Hoisting

## 1. Name, aliases, and lineage

The canonical name is ViewModel with State Hoisting, the specific,
composable-level mechanism where a piece of UI state is moved out of
a composable function and up to its caller, replaced with two plain
parameters, the current value and a callback for requesting a change,
so the composable itself becomes stateless and reusable, while a
ViewModel usually owns the real, hoisted state at the top of that
chain. Google's own Jetpack Compose documentation states the core
definition directly, "state hoisting in Compose is a pattern of
moving state to a composable's caller to make a composable stateless."
This entry is a narrower, more mechanical sibling of the already-
published Unidirectional Data Flow (Mobile) entry, that entry covers
the broader Android-plus-iOS architectural convergence, this entry
covers the specific, composable-level parameter-hoisting mechanism
Compose itself uses to achieve it.

The alias **State Hoisting** is Google's own name for the mechanism
itself. **Stateless Composable Pattern** names the pattern by its
real, immediate result, a composable function that holds no state of
its own.

## 2. Problem and context

A composable function that declares and mutates its own local state
directly is genuinely difficult to reuse, test, or preview, because
its behavior depends on state hidden inside the function itself,
invisible to whatever calls it. Google's own documentation, "State
and Jetpack Compose,"
https://developer.android.com/develop/ui/compose/state, verified
2026-08-22, names the mechanical fix directly, "the general pattern
for state hoisting in Jetpack Compose is to replace the state
variable with two parameters, value, the current value to display,
and onValueChange, an event that requests the value to change."
ViewModel with State Hoisting solves
the reuse and testability problem by moving the real, owned state up
to a caller, commonly a ViewModel, and leaving the composable itself
with nothing to hold, only a value to render and an event to raise
when the user wants it changed.

## 3. Forces

The pattern balances the following competing pressures.

- **Exactly one real place a piece of state is genuinely stored.**
  Favored. Google's own documentation states this directly, hoisted
  state is "single source of truth. By moving state instead of
  duplicating it," there is only one real, current place a value
  genuinely lives.
- **A composable that can be reused, tested, and previewed in
  isolation.** Favored. A stateless composable, per Google's own
  definition, needs no real backing state of its own to be exercised,
  only a value and a callback, both trivially supplied by a test or a
  preview.
- **Callers that can intercept or modify an event before the state
  actually changes.** Favored. Google's own documentation states this
  directly, hoisted state is "interceptable, callers to the stateless
  composables can decide to ignore or modify events before changing
  the state."
- **A real decision about how far up to hoist a given piece of
  state.** Sacrificed. Google's own three rules require genuine
  judgment, hoisting too low limits reuse, hoisting too high adds real
  distance between where a value is used and where it is owned.
- **Two extra parameters for every piece of state a composable used to
  hold locally.** Sacrificed. Every hoisted value genuinely needs both
  a value parameter and an onValueChange parameter, a real, small but
  compounding cost as more state is hoisted.

## 4. Applicability and non-applicability

Reach for ViewModel with State Hoisting when the following hold.

- The composable genuinely needs to be reused in more than one real
  context, or genuinely needs to be tested or previewed in isolation,
  and holding its own local state genuinely prevents that.
- The team genuinely wants a single, real source of truth for a piece
  of state, per Google's own stated benefit, rather than the state
  existing separately inside the composable and anywhere else that
  might also care about it.
- The state genuinely needs to be shared across more than one
  composable, per Google's own "shareable" property, hoisted state
  can be passed down to as many composables as genuinely need to read
  it.

Do NOT reach for ViewModel with State Hoisting in these cases, and the
reason matters more than the rule.

- **The state genuinely never needs to leave the one composable that
  uses it, and the composable itself has no real need to be reused,
  tested independently, or previewed with varying values**, hoisting
  it up adds real parameter-passing overhead without a matching real
  benefit.
- **The real cost of choosing where to hoist a piece of state,
  correctly applying Google's own three rules, genuinely outweighs the
  benefit for a small, one-off composable that will never grow further
  real complexity.**
- **The state genuinely belongs to a transient, purely visual concern,
  such as whether a ripple animation is currently playing, that no
  real caller, ViewModel, or sibling composable will ever
  legitimately need to read or influence.**

## 5. Structure

ViewModel with State Hoisting has three structural parts, per
Google's own naming.

- **The stateless composable**, Google's own definition, a composable
  with its local state variable replaced by "value, the current value
  to display" and "onValueChange, an event that requests the value to
  change."
- **The state holder**, commonly a ViewModel, which genuinely owns
  the real, hoisted state, per Google's own single-source-of-truth
  property.
- **The unidirectional flow between them**, Google's own description
  of the resulting cycle, "the pattern where the state goes down, and
  events go up," matching this entry's own sibling, the
  unidirectional-data-flow entry, at the specific granularity of one
  composable and its caller.

## 6. ASCII structure diagram

```
  State holder (commonly a ViewModel)
        |
        |  value flows down
        v
  Stateless composable (value, onValueChange)
        |
        |  onValueChange event flows up
        v
  State holder updates the real, hoisted state
```

## 7. Dynamics

The trace below shows one complete cycle, per Google's own described
mechanism.

```
The composable renders

per Google's own definition, the composable holds no state of its
own, it receives "value, the current value to display" as a plain
parameter
   |-- it renders exactly what value describes, with nothing else to
       consult

The user interacts with the composable

per Google's own definition, the composable calls "onValueChange, an
event that requests the value to change"
   |-- the composable does not mutate anything itself, it only raises
       the request

The state holder receives the request

per Google's own "interceptable" property, the caller "can decide to
ignore or modify events before changing the state"
   |-- if the caller accepts the request, it updates the real, hoisted
       state
   |-- the new value flows back down to the composable, and the cycle
       repeats for the next real user interaction
```

## 8. Implementation variants

**ViewModel-hoisted state, the canonical Android form.** The real
state lives inside a ViewModel, exposed as an observable value, and
the composable receives that value plus a lambda that calls a
ViewModel method, matching the pattern's own most common real-world
placement.

**Parent-composable-hoisted state.** A variant where the state is
hoisted only as far as the nearest real, common parent composable,
per Google's own first rule, "state should be hoisted to at least the
lowest common parent of all composables that use the state," rather
than all the way to a ViewModel, appropriate when no real business
logic needs to observe or react to the value.

**Hoisted-together state.** A variant applying Google's own third
rule directly, "if two states change in response to the same events
they should be hoisted together," combining two or more related
values into one hoisted state object rather than hoisting each
separately.

## 9. Known production uses

**Google, Jetpack Compose documentation, "State and Jetpack Compose",
the pattern's own core definition and rules.** Google states the
mechanism and its properties directly. "State hoisting in Compose is
a pattern of moving state to a composable's caller to make a
composable stateless." The general pattern, "replace the state
variable with two parameters, value, the current value to display,
and onValueChange, an event that requests the value to change." The
stated properties, "single source of truth," "encapsulated, only
stateful composables can modify their state," "shareable, hoisted
state can be shared with multiple composables," and "interceptable,
callers to the stateless composables can decide to ignore or modify
events before changing the state." The three placement rules, "state
should be hoisted to at least the lowest common parent of all
composables that use the state," "state should be hoisted to at least
the highest level it may be changed," and "if two states change in
response to the same events they should be hoisted together." Google,
"State and Jetpack Compose,"
https://developer.android.com/develop/ui/compose/state, verified
2026-08-22.

## 10. Consequences

Positive.

- The composable becomes genuinely reusable, testable in isolation,
  and previewable with varying values, per Google's own stateless
  definition, with no real backing state of its own to set up.
- The hoisted state has exactly one real owner, per Google's own
  single-source-of-truth property, eliminating the risk of the
  composable's own local copy disagreeing with a separately-tracked
  value elsewhere.
- A caller can genuinely intercept or modify an event before the real
  state changes, per Google's own interceptable property, enabling
  validation or transformation with no change to the composable
  itself.

Negative.

- Every hoisted value genuinely needs two parameters instead of one
  local variable, a real, small overhead that compounds as more state
  is hoisted.
- Choosing correctly where to hoist a given piece of state, per
  Google's own three rules, is a real, ongoing judgment call, not a
  mechanical decision.
- A composable hoisted too aggressively can end up with a long real
  parameter list, trading local simplicity for caller-side
  complexity.

## 11. Failure modes and misuse

**Hoisting a piece of state higher than Google's own rules genuinely
require, so a composable's caller ends up owning and threading through
state that no other real composable ever needed to read or share.**
Symptom. A ViewModel or a parent composable accumulates real state
that exists purely to satisfy one, single child composable, adding
real indirection with no matching real reuse or sharing benefit.
Cause. Hoisting a value reflexively, out of habit, rather than
genuinely applying Google's own first rule, hoisting only to "at
least the lowest common parent of all composables that use the
state." Fix. Confirm the real, current set of composables that
genuinely need to read a given piece of state before hoisting it, and
hoist no higher than that real common parent requires.

**Leaving a composable stateful when it genuinely needs to be reused,
tested, or previewed with varying values, because the real hoisting
step was skipped.** Symptom. The composable genuinely cannot be
exercised with a range of real input values in a test or a preview,
because its state is generated internally rather than supplied, per
Google's own stateless definition, as a plain value parameter. Cause.
Leaving a local state variable inside the composable instead of
genuinely applying Google's own two-parameter replacement, value and
onValueChange. Fix. Confirm every composable that genuinely needs to
be reused, tested, or previewed with different values has its state
hoisted per Google's own pattern, with no remaining local state
variable driving its own behavior.

**Splitting two states that genuinely always change together across
separate hoisting points, violating Google's own third rule.**
Symptom. Two real, related values drift out of sync, because they are
hoisted and updated independently even though they always change
together in response to the same real event. Cause. Not applying
Google's own stated rule, "if two states change in response to the
same events they should be hoisted together," and instead hoisting
each value to a separately-chosen location. Fix. Confirm any two
states that genuinely always change together in response to the same
real event are hoisted to the same real place, as one combined state
value, per Google's own third rule.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | ViewModel with State Hoisting (Google's own mechanism) | A composable holding its own local state | Full Unidirectional Data Flow (a whole-screen state cycle) |
|---|---|---|---|
| Composable reusability, testability, previewability | Strong, per Google's own stateless definition | Weak, the composable's own hidden state must be reproduced to exercise it | Strong, the same stateless-composable benefit applies at every level |
| Real overhead of parameter passing | Real, but small, two parameters per hoisted value | None, the value lives locally | Real, and larger, a whole screen's state and event vocabulary must be threaded through |
| Fit for a single, purely local, transient value | Weak, hoisting adds real overhead with no real benefit | Strong, the simplest, most direct option | Weak, the same overhead as state hoisting, applied to a value that never needed it |
| Fit for a whole screen's real state, spanning many composables | Moderate, this entry's own mechanism composes naturally into a full cycle | Weak, no real coordination across composables | Strong, this is precisely the sibling entry's own scope |

Reading of the table. ViewModel with State Hoisting wins specifically
at the composable level, for a value that genuinely needs to be
reused, tested, or shared, without the real overhead of a full,
whole-screen unidirectional cycle. A purely local, transient value
fits a composable's own local state better, and a whole screen's real
state is the sibling Unidirectional Data Flow entry's own scope.

## 13. Related and incompatible patterns

- **Unidirectional Data Flow (Mobile).** The broader architectural
  family this pattern's own composable-level mechanism composes into,
  Google's own documentation states the resulting cycle directly,
  "the pattern where the state goes down, and events go up is called
  a unidirectional data flow," the same rule this entry applies at
  the granularity of one composable and its caller.
- **MVVM-C (Model-View-ViewModel-Coordinator).** A genuinely
  complementary concern, the ViewModel that commonly owns the real,
  hoisted state in this entry's own mechanism is the same ViewModel
  described in that entry, with navigation handled separately by a
  coordinator.

## 14. Refactoring path in and out

Introducing the pattern into a composable that currently holds its own
local state. Ordered steps, most relevant when the composable has
genuinely started needing to be reused, tested, or previewed with
varying values.

1. Identify the real state currently held locally inside the
   composable that genuinely needs to be hoisted, per the real need
   named above.
2. Replace the local state variable with two plain parameters, value
   and onValueChange, per Google's own stated pattern.
3. Choose where the real, hoisted state should now live, applying
   Google's own three rules, the lowest common real parent, the
   highest real level it may change, and combining any two states that
   genuinely always change together.
4. Confirm the composable is now genuinely stateless, and that the
   chosen caller, commonly a ViewModel, correctly owns and updates the
   real state in response to the hoisted onValueChange event.

Removing the pattern when it stops earning its place, most relevant
when a hoisted value's real, current set of readers has genuinely
shrunk to exactly the one composable that originally needed hoisting.

1. Confirm, concretely, that no other real composable, ViewModel
   method, or caller still genuinely reads or reacts to the hoisted
   value.
2. Move the value back into the composable as local state, removing
   the value and onValueChange parameters.
3. Confirm no test or preview still depends on supplying that value
   externally before removing the hoisting.

## 15. Testing and verification

Easier because of the pattern.

- A stateless composable can be tested or previewed with any real
  range of values, per Google's own stateless definition, with no
  real setup needed beyond supplying the value parameter directly.
- The real logic that decides how a hoisted value changes lives in the
  caller, commonly a ViewModel, and can be tested there in complete
  isolation, with no composable rendering needed at all.

Harder because of the pattern.

- Verifying the real, full interaction, a genuine user event through
  the composable, up to the caller, and back down as an updated value,
  needs a test that exercises both the composable and its caller
  together, not only one in isolation.
- Confirming Google's own three hoisting-placement rules were applied
  correctly needs a real, structural review of where each piece of
  state actually lives relative to every real composable that reads
  or writes it.

Techniques that apply.

- **Composable preview and snapshot tests.** Render the stateless
  composable against a real range of value parameters, with no real
  state holder involved at all.
- **State-holder logic tests.** Assert the real behavior of the
  caller's onValueChange handling, with no composable rendered.
- **Full-interaction tests.** Drive a real user interaction through
  the composable, into the caller, and assert the resulting value
  that flows back down.
- **Hoisting-placement audits.** Confirm each piece of state is
  hoisted no higher, and no lower, than Google's own three rules
  genuinely require.

## 16. Observability signals

What to record.

- Whether a composable that is genuinely reused, tested, or previewed
  with varying values still holds any real local state of its own,
  since any such state points directly at the not-genuinely-hoisted
  failure mode from dimension 11.
- Whether two real states that always change together in response to
  the same event are hoisted to different real places, since any such
  split points directly at the violated-third-rule failure mode from
  dimension 11.

A healthy state. Every composable that is genuinely reused, tested, or
previewed with varying values holds no local state of its own, and
every pair of states that always change together is hoisted to the
same real place.

A failing state. A genuinely-reused composable is found still holding
local state, pointing directly at a missed hoisting, or two states
that always change together are found hoisted separately, pointing
directly at a violated placement rule.

## 17. Security and privacy implications

**Because a hoisted piece of state is genuinely readable by every
real composable it is passed down to, per Google's own "shareable"
property, hoisting a real, sensitive value, such as a raw password
field's current text, further up the tree than it genuinely needs to
go widens the real set of code that can read it, beyond what a
smaller, more locally-scoped piece of state would have allowed.**
Because Google's own first rule only requires hoisting to "at least
the lowest common parent of all composables that use the state,"
hoisting a sensitive value any higher than that real requirement
genuinely exposes it to more code than necessary, each additional
composable in the chain being a place the value could be logged,
retained, or otherwise mishandled. Confirming a sensitive value is
hoisted no higher than the real, current set of composables that
genuinely need it, per Google's own own placement rules applied
strictly, is a necessary part of a security-conscious implementation
of this pattern.

## 18. References

1. Google. "State and Jetpack Compose".
   https://developer.android.com/develop/ui/compose/state
   Verified 2026-08-22. Source of the state-hoisting definition, the
   value/onValueChange parameter pattern, the single-source-of-truth,
   encapsulated, shareable, and interceptable properties, and the
   three hoisting-placement rules, used in dimensions 1, 2, 3, 5, 7,
   9, and 11.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. Kotlin models Google's own original Jetpack Compose mechanism
directly, the language and framework the pattern's own canonical
documentation is written for. Swift shows the same conceptual shape
on iOS, an idiomatic composition of a SwiftUI-style value-and-callback
parameter pair with a state holder above it. Python shows the same
conceptual shape using a minimal, host-testable simulation, useful for
verifying the state-holder's own logic in isolation, per dimension
15, expressed portably. Java, Go, and Rust are omitted, since the
pattern's real home is declarative mobile UI frameworks, and the
three languages chosen already cover its two production platforms and
its testable-simulation shape.

### Kotlin

```kotlin
class CounterViewModel {
    var count: Int = 0
        private set

    fun onCountChange(newValue: Int) {
        count = newValue
    }
}

class StatelessCounter(
    private val value: Int,
    private val onValueChange: (Int) -> Unit
) {
    fun render() {
        println("count is " + value)
    }

    fun userTapsIncrement() {
        onValueChange(value + 1)
    }
}

fun main() {
    val viewModel = CounterViewModel()
    val counter = StatelessCounter(viewModel.count, viewModel::onCountChange)
    counter.render()
    counter.userTapsIncrement()
    println("viewmodel count is now " + viewModel.count)
}
```

### Swift

```swift
final class CounterViewModel {
    private(set) var count = 0

    func onCountChange(_ newValue: Int) {
        count = newValue
    }
}

struct StatelessCounter {
    let value: Int
    let onValueChange: (Int) -> Void

    func render() {
        print("count is", value)
    }

    func userTapsIncrement() {
        onValueChange(value + 1)
    }
}

let viewModel = CounterViewModel()
let counter = StatelessCounter(value: viewModel.count, onValueChange: viewModel.onCountChange)
counter.render()
counter.userTapsIncrement()
print("viewmodel count is now", viewModel.count)
```

### Python

```python
from typing import Callable


class CounterViewModel:
    def __init__(self):
        self.count = 0

    def on_count_change(self, new_value: int) -> None:
        self.count = new_value


class StatelessCounter:
    def __init__(self, value: int, on_value_change: Callable[[int], None]):
        self.value = value
        self.on_value_change = on_value_change

    def render(self) -> None:
        print("count is", self.value)

    def user_taps_increment(self) -> None:
        self.on_value_change(self.value + 1)


if __name__ == "__main__":
    view_model = CounterViewModel()
    counter = StatelessCounter(view_model.count, view_model.on_count_change)
    counter.render()
    counter.user_taps_increment()
    print("viewmodel count is now", view_model.count)
```
