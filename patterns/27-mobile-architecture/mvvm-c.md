---
name: MVVM-C (Model-View-ViewModel-Coordinator)
slug: mvvm-c
family: 27-mobile-architecture
category: Structural
aliases: [MVVM Plus Coordinator, Coordinated MVVM]
first_described: 'Composition of MVVM and the Coordinator Pattern, common in iOS practice since roughly 2015'
maturity: canonical
related: [coordinator-pattern, unidirectional-data-flow]
incompatible_with: [model-view-intent]
verified: 2026-08-22
---

# MVVM-C (Model-View-ViewModel-Coordinator)

## 1. Name, aliases, and lineage

The canonical name is MVVM-C, the direct composition of the
Model-View-ViewModel pattern with the already-published Coordinator
Pattern, so that every screen's presentation logic lives in its own
view model while every screen's navigation logic lives in a
coordinator, the two concerns never mixed into the same object.
Microsoft's own MVVM documentation states the core MVVM half plainly,
"the MVVM pattern helps cleanly separate an application's business
and presentation logic from its user interface." Soroush Khanlou's own
Coordinator posts, already cited in the coordinator-pattern entry,
supply the navigation half directly, "a coordinator is an object that
bosses one or more view controllers around." MVVM-C is not a new
mechanism, it is the deliberate, named combination of the two.

The alias **MVVM Plus Coordinator** names the pattern by its literal
composition. **Coordinated MVVM** names it from the MVVM side, MVVM
whose navigation responsibility has been extracted into a coordinator
rather than left inside the view model or the view.

## 2. Problem and context

Plain MVVM cleanly separates a screen's own presentation logic from
its view, per Microsoft's own description, "the view model implements
properties and commands to which the view can data bind to." But
plain MVVM does not, by itself, say where the decision "what screen
comes after this one" should live. If that decision is placed inside
the view model, per this pattern's own composition, the view model
must now know about the wider navigation graph, exactly the same
coupling problem Khanlou's own Coordinator posts describe for view
controllers, "your navigation flow is now spread among three
different objects." MVVM-C solves this by keeping the view model
scoped strictly to its own screen's presentation state, per Microsoft's
own guidance, and routing every navigation decision to a coordinator,
per Khanlou's own mechanism, so neither object ever needs to know
about the other's responsibility.

## 3. Forces

The pattern balances the following competing pressures.

- **A view model scoped strictly to presentation, never navigation.**
  Favored. Microsoft's own documentation states the view model's real
  job directly, it "implements properties and commands to which the
  view can data bind to, and notifies the view of any state changes,"
  nothing about deciding the next screen.
- **A coordinator scoped strictly to navigation, never presentation
  state.** Favored. Khanlou's own description of the coordinator
  applies unchanged here, it "bosses one or more view controllers
  around," while the view controller and its own view model stay
  "inert."
- **Independent testability of each concern.** Favored. Microsoft's
  own documentation states this directly, "developers can create unit
  tests for the view model and the model, without using the view,"
  and the coordinator's own navigation decisions, per the
  coordinator-pattern entry, can likewise be tested with no real
  screen present.
- **Two separate object graphs to keep synchronized.** Sacrificed.
  Every screen now needs both a view model, for its presentation
  state, and a coordinator, or a coordinator-owned entry, for its
  place in the navigation flow, and the two must agree about when a
  screen's flow has genuinely finished.
- **A real question of which object triggers navigation.** Sacrificed.
  A view model that reacts to a user action by starting a navigation
  transition must still, per Khanlou's own inert-view-controller
  principle, report that intent upward rather than performing the
  transition itself, adding one more indirection to reason through.

## 4. Applicability and non-applicability

Reach for MVVM-C when the following hold.

- The app genuinely already benefits from plain MVVM's own separation
  of presentation logic from the view, per Microsoft's own stated
  benefits, and additionally has more than one real, independent
  navigation flow, per the coordinator-pattern entry's own
  applicability.
- The team genuinely wants a view model that can be unit tested with
  no real navigation stack present, and a navigation flow that can be
  reasoned about and tested with no real view model present, each in
  isolation.
- The app's real screens are genuinely reusable across more than one
  flow, and keeping the view model free of navigation knowledge is
  what makes that reuse genuinely possible.

Do NOT reach for MVVM-C in these cases, and the reason matters more
than the rule.

- **The app genuinely does not need the Coordinator Pattern at all**,
  per that entry's own non-applicability, a single, simple, linear
  flow, plain MVVM alone, with the view or view model handling its own
  direct transitions, is a real, legitimate simpler choice.
- **The team genuinely finds keeping two parallel object graphs, view
  models and coordinators, synchronized more costly than the real
  benefit of separating the two concerns**, for a small app this is a
  real, valid trade-off against the composed pattern's own added
  structure.
- **The platform's own newer, unidirectional state-management
  approach genuinely already covers both concerns in one place**, a
  team already committed to that approach gains real, unneeded
  complexity by also introducing a separate coordinator layer.

## 5. Structure

MVVM-C has four structural parts.

- **The view**, per Microsoft's own description, "responsible for
  defining the structure, layout, and appearance of what the user
  sees on screen," and, per Khanlou's own inert-view-controller
  principle, never deciding navigation itself.
- **The view model**, per Microsoft's own description, implementing
  "properties and commands to which the view can data bind to," scoped
  strictly to that one screen's own presentation state.
- **The coordinator**, per the coordinator-pattern entry, owning
  navigation decisions and the childCoordinators composition
  mechanism, exactly as already described there.
- **The reporting path from the view model to the coordinator**, most
  commonly a closure or a delegate the coordinator supplies to the
  view model at creation time, so the view model can signal "the user
  wants to move on" without knowing where that leads.

## 6. ASCII structure diagram

```
  Coordinator
     |
     |-- creates --> View + ViewModel (scoped to one screen)
     |                      |
     |                      |  view model reports
     |<---------------------+  "user finished this screen"
     |
     |-- decides the next step, per the coordinator-pattern's own
         mechanism (push, present, or start a child coordinator)
```

## 7. Dynamics

The trace below shows one complete screen-to-screen transition.

```
The coordinator creates a screen

per the coordinator-pattern entry's own mechanism, the coordinator
creates the view model, supplying it a completion closure or delegate
   |-- the coordinator creates the view, binds it to the view model,
       per Microsoft's own BindingContext description, and presents it

The user interacts with the screen

per Microsoft's own description, the view's controls are "data bound"
to the view model's own properties and commands
   |-- the view model updates its own presentation state, and, per
       Microsoft's own change-notification requirement, raises a
       change notification so the view updates

The user finishes the screen

the view model does not move to the next screen itself, per Khanlou's own
inert-object principle applied to this composition
   |-- it calls the completion closure or delegate the coordinator
       supplied at creation time
   |-- the coordinator receives that report and decides the real next
       step, exactly as described in the coordinator-pattern entry's
       own dynamics trace
```

## 8. Implementation variants

**Closure-based reporting, the lightest form.** The coordinator passes
a plain completion closure into the view model at creation, and the
view model calls it directly, with no named protocol required.

**Delegate-protocol reporting, Khanlou's own original form.** The view
model conforms to reporting through a named delegate protocol, mirroring
the coordinator-pattern entry's own delegate-protocol variant, at the
cost of one more named type per screen.

**Coordinator-owned view model factory.** A variant where the
coordinator does more than create the view model once, it also owns a
factory method the view model itself can call to request a related
view model, such as a detail screen's view model built from a list
screen's selected item, keeping the construction logic colocated with
the coordinator that already owns the flow.

## 9. Known production uses

**Microsoft's own MVVM documentation, the presentation half of the
composition.** Microsoft states the core separation and its benefit
directly. "The MVVM pattern helps cleanly separate an application's
business and presentation logic from its user interface." The
isolation mechanism, "the view 'knows about' the view model, and the
view model 'knows about' the model, but the model is unaware of the
view model, and the view model is unaware of the view." The
testability benefit, "developers can create unit tests for the view
model and the model, without using the view." Microsoft, "Model-View-
ViewModel - .NET,"
https://learn.microsoft.com/en-us/dotnet/architecture/maui/mvvm,
verified 2026-08-22.

**Soroush Khanlou, the navigation half of the composition, already
cited in the coordinator-pattern entry.** Khanlou's own coordinator
mechanism supplies the navigation half unchanged. "A coordinator is an
object that bosses one or more view controllers around." Soroush
Khanlou, "Coordinators Redux,"
https://khanlou.com/2015/10/coordinators-redux/, verified 2026-08-22.

## 10. Consequences

Positive.

- Presentation logic and navigation logic are genuinely separate
  concerns, each independently testable, per Microsoft's own
  view-model-in-isolation testing benefit and the coordinator-pattern
  entry's own decision-testing benefit.
- A view model never accumulates navigation-graph knowledge, so it
  stays reusable across different flows the same way an inert view
  controller does, per Khanlou's own description.
- The two halves can evolve independently, a navigation restructuring
  touches coordinators only, and a presentation-logic change touches
  view models only.

Negative.

- Two parallel object graphs, view models and coordinators, must be
  kept synchronized for every screen, a real, additional bookkeeping
  cost over plain MVVM alone.
- A view model's completion report must be wired correctly to its
  coordinator at creation time, or the coordinator never learns the
  screen has finished, silently stalling the flow.
- The composition inherits every real failure mode named in both the
  coordinator-pattern entry and plain MVVM, rather than resolving
  either on its own.

## 11. Failure modes and misuse

**Letting a view model perform navigation directly, such as
constructing and presenting the next screen itself, rather than
reporting through its coordinator.** Symptom. The exact coupling
MVVM-C exists to avoid reappears, a view model that was genuinely
reusable across flows becomes tied to one specific navigation path,
breaking the moment it is placed inside a different coordinator's
flow. Cause. Reaching for a direct navigation call from inside the
view model, perhaps for convenience on a simple screen, rather than
calling the completion closure or delegate the coordinator supplied.
Fix. Confirm every view model reports completion exclusively through
its supplied closure or delegate, never constructing or presenting a
screen itself, mirroring the same discipline the coordinator-pattern
entry requires of view controllers.

**Forgetting to wire a view model's completion report at creation
time, so the coordinator never learns a screen has finished.**
Symptom. The user finishes a screen's real task, but the app appears
to hang, staying on the same screen, because no coordinator ever
receives the signal to move on. Cause. Constructing the view model
without supplying the completion closure or delegate the coordinator
expects, often when a screen is added quickly and the wiring step is
skipped. Fix. Treat wiring a view model's completion report as a
required part of the coordinator's own creation step for that screen,
never an optional afterthought, and cover it with the same
child-coordinator lifecycle tests the coordinator-pattern entry
already describes.

**Duplicating the same presentation logic inside both the view model
and the coordinator, because it was unclear which object owns it.**
Symptom. A change to a screen's presentation behavior needs to be made
in two places, and the two copies silently drift apart over time.
Cause. Not applying the real line dimension 5 draws, presentation
state lives in the view model, navigation decisions live in the
coordinator, consistently. Fix. Audit any logic living in a
coordinator that reads or computes a screen's own presentation state,
and move it into that screen's view model, leaving the coordinator
with navigation decisions only.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | MVVM-C (this composition) | Plain MVVM, navigation in the view model | Coordinator Pattern alone, no MVVM |
|---|---|---|---|
| View model scoped strictly to presentation | Strong, per both source documents' own separation | Weak, the view model also knows the navigation graph | Not applicable, no view model exists in this comparison |
| Independent testability of navigation and presentation | Strong, per Microsoft's own and the coordinator entry's own testing benefits | Weak, navigation and presentation logic are tested together | Strong for navigation, but presentation logic has no dedicated, testable object |
| Synchronization overhead between two object graphs | Real, view models and coordinators must agree on completion signals | None, one object graph only | None, no view model graph exists to synchronize |
| Reusability of a screen's presentation logic across flows | Strong, per the same reusability argument the coordinator-pattern entry makes for view controllers | Weak, the view model is tied to its own navigation calls | Not applicable |

Reading of the table. MVVM-C wins specifically when a team genuinely
wants both of the two composed patterns' own real benefits at once,
testable presentation logic and testable, reusable navigation. A team
that only needs one of the two, or that finds the synchronization
overhead genuinely not worth paying, fits one of the two patterns
alone better than the full composition.

## 13. Related and incompatible patterns

- **Coordinator Pattern.** The navigation half of this composition,
  described in full in its own entry, and unchanged here except for
  its reporting source now being a view model rather than a view
  controller directly.
- **Unidirectional Data Flow (Mobile).** A genuinely different
  architectural family, where presentation state and, often,
  navigation state both flow through one single, unidirectional store
  rather than being split across a view model and a coordinator, a
  real alternative to reach for instead of MVVM-C when a team prefers
  that model.
- **Model-View-Intent (MVI).** Incompatible in practice. MVI's own
  single-state-stream model for a screen genuinely conflicts with
  MVVM-C's split between a view model's own mutable, bindable
  properties and a separate coordinator, so a codebase does not mix
  the two patterns on the same screen.

## 14. Refactoring path in and out

Introducing the pattern into a plain-MVVM codebase that does not have
it. Ordered steps, most relevant to a codebase where view models
currently trigger navigation directly.

1. Introduce the Coordinator Pattern first, per that entry's own
   refactoring path, scoped to the app's real, genuine flows.
2. For each screen, add a completion closure or delegate parameter to
   its view model's own constructor, supplied by the coordinator that
   creates it.
3. Move every real navigation call currently inside a view model into
   the coordinator that now owns that screen, replacing it with a call
   to the new completion closure or delegate.
4. Confirm every view model's own tests can now run with no real
   navigation stack present, per Microsoft's own testability benefit,
   proving the separation genuinely took hold.

Removing the pattern when it stops earning its place, most relevant
when a team decides the two-object-graph overhead is not worth its
own benefit for a genuinely small or simple app.

1. Confirm, concretely, that removing the coordinator layer, per that
   entry's own removal path, is already the right decision for the
   app's real navigation needs.
2. Move each view model's completion report back into a direct
   navigation call, removing the closure or delegate parameter.
3. Confirm no other part of the app still depends on the coordinator's
   existence before removing it entirely, exactly as the
   coordinator-pattern entry's own removal path already describes.

## 15. Testing and verification

Easier because of the pattern.

- A view model's own presentation logic can be tested in complete
  isolation, per Microsoft's own stated benefit, "developers can
  create unit tests for the view model and the model, without using
  the view," with no real coordinator or navigation stack present.
- A coordinator's own navigation decisions can be tested in isolation,
  per the coordinator-pattern entry's own testing techniques, by
  simulating a view model's completion report directly, with no real
  view model needed.

Harder because of the pattern.

- Verifying the real, full hand-off from a view model's completion
  report to the coordinator's real next decision needs a test that
  exercises both objects together, not only one in isolation.
- Confirming a screen's view model and its coordinator agree about
  when a screen has genuinely finished needs coverage of every real
  exit path a user can take, mirroring the coordinator-pattern entry's
  own child-coordinator-leak failure mode, now one level deeper.

Techniques that apply.

- **View-model isolation tests.** Assert a view model's own
  presentation state and command behavior, with no real coordinator or
  view present, per Microsoft's own testing benefit.
- **Coordinator decision tests.** Assert a coordinator's own next step
  given a simulated view-model completion report, per the
  coordinator-pattern entry's own testing techniques.
- **Wiring tests.** Assert every screen's real view model was
  genuinely supplied a completion closure or delegate at creation
  time, catching the unwired-completion failure mode from dimension 11
  before it reaches a real user.
- **Full-flow tests.** Drive a real screen-to-screen transition and
  assert the expected next screen actually appears, exercising the
  view model and the coordinator together.

## 16. Observability signals

What to record.

- Whether every screen's real view model genuinely calls its
  completion report on the real, expected user action, since a screen
  that never reports completion points directly at the unwired-
  completion failure mode from dimension 11.
- Whether any view model genuinely constructs or presents a screen
  directly, rather than reporting through its coordinator, since any
  such call points directly at the reintroduced-coupling failure mode
  from dimension 11.

A healthy state. Every screen's real completion report reaches its
coordinator on the expected user action, and no view model in the app
ever constructs or presents a screen directly.

A failing state. A screen's real completion report never fires,
pointing directly at an unwired view model, or a view model is found
constructing or presenting a screen directly, pointing directly at
reintroduced coupling.

## 17. Security and privacy implications

**A view model that genuinely holds sensitive presentation state, per
Microsoft's own description of the properties it exposes for
data-binding, such as a typed password or a fetched payment detail,
inherits the same real memory-retention risk the coordinator-pattern
entry names for a leaked child coordinator, because the coordinator
that owns that view model is exactly what can leak it.** If a
coordinator fails to release a finished screen's own view model,
mirroring the leaked-child-coordinator failure mode in the
coordinator-pattern entry, any sensitive data the view model held in
its own bindable properties stays in memory well past the point the
user genuinely finished that screen. Confirming a coordinator's real
completion path releases both the screen's view model and its
coordinator together, and never holding a sensitive value in a view
model's own bindable property for longer than the screen's real
lifetime genuinely requires, are necessary parts of a
security-conscious MVVM-C implementation.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. Swift models the composition directly, on the platform
Khanlou's own coordinator mechanism was introduced for, paired with a
plain MVVM view model. Kotlin shows the same conceptual shape on
Android, an idiomatic composition of a ViewModel class with a
coordinator-equivalent navigation object. Python shows the same
conceptual shape using a minimal, host-testable simulation, useful for
verifying the view-model-to-coordinator reporting mechanism in
isolation, per dimension 15, expressed portably. Java, Go, and Rust
are omitted, since the pattern's real home is mobile-app UI
frameworks, and the three languages chosen already cover its two
production platforms and its testable-simulation shape.

### Swift

```swift
protocol Coordinator: AnyObject {
    func start()
}

final class LoginViewModel {
    private(set) var statusText: String = "idle"
    private let onFinished: () -> Void

    init(onFinished: @escaping () -> Void) {
        self.onFinished = onFinished
    }

    func submit(username: String) {
        statusText = "signed in as " + username
        onFinished()
    }
}

final class LoginCoordinator: Coordinator {
    private var viewModel: LoginViewModel?

    func start() {
        let vm = LoginViewModel(onFinished: { [weak self] in
            self?.showHome()
        })
        viewModel = vm
        vm.submit(username: "alice")
    }

    private func showHome() {
        print("navigate to home screen")
        viewModel = nil
    }
}

let coordinator = LoginCoordinator()
coordinator.start()
```

### Kotlin

```kotlin
interface Coordinator {
    fun start()
}

class LoginViewModel(private val onFinished: () -> Unit) {
    var statusText: String = "idle"
        private set

    fun submit(username: String) {
        statusText = "signed in as " + username
        onFinished()
    }
}

class LoginCoordinator : Coordinator {
    private var viewModel: LoginViewModel? = null

    override fun start() {
        val vm = LoginViewModel(onFinished = { showHome() })
        viewModel = vm
        vm.submit("alice")
    }

    private fun showHome() {
        println("navigate to home screen")
        viewModel = null
    }
}

fun main() {
    val coordinator = LoginCoordinator()
    coordinator.start()
}
```

### Python

```python
from typing import Callable, Optional


class LoginViewModel:
    def __init__(self, on_finished: Callable[[], None]):
        self.status_text = "idle"
        self._on_finished = on_finished

    def submit(self, username: str) -> None:
        self.status_text = "signed in as " + username
        self._on_finished()


class LoginCoordinator:
    def __init__(self):
        self.view_model: Optional[LoginViewModel] = None

    def start(self) -> None:
        vm = LoginViewModel(on_finished=self._show_home)
        self.view_model = vm
        vm.submit("alice")

    def _show_home(self) -> None:
        print("navigate to home screen")
        self.view_model = None


if __name__ == "__main__":
    coordinator = LoginCoordinator()
    coordinator.start()
```

## 18. References

1. Microsoft. "Model-View-ViewModel - .NET".
   https://learn.microsoft.com/en-us/dotnet/architecture/maui/mvvm
   Verified 2026-08-22. Source of the core MVVM definition, the
   view/view model/model isolation description, and the testability
   benefit, used in dimensions 1, 2, 3, 5, 7, 9, 10, and 15.
2. Soroush Khanlou. "Coordinators Redux".
   https://khanlou.com/2015/10/coordinators-redux/
   Verified 2026-08-22. Source of the coordinator half of the
   composition, already the primary citation of the coordinator-
   pattern entry, used here in dimensions 1, 2, 3, 5, 7, and 9.
