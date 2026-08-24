---
name: Model-View-Intent
slug: model-view-intent
family: 05-architectural
category: Architectural
aliases: [MVI, Cycle MVI, Unidirectional MVI]
first_described: "Andre Staltz, Cycle.js documentation and blog, circa 2015"
maturity: established
related: [model-view-viewmodel, model-view-presenter, flux, redux, elm-architecture, observer, command, memento, state]
incompatible_with: [model-view-controller]
verified: 2026-08-02
---

# Model-View-Intent

## 1. Name, aliases, and lineage

The canonical name is Model-View-Intent, almost always shortened to MVI. The
name and the specific three-function formulation, Model as a function of
Intent to State, View as a function of State to DOM, Intent as a function of
DOM events to Actions, are described by Andre Staltz in his essay
"Unidirectional User Interface Architectures", which walks through Flux, MVC,
and MVI side by side and lays out MVI as the architecture behind his Cycle.js
framework (Andre Staltz, "Unidirectional User Interface Architectures",
https://staltz.com/unidirectional-user-interface-architectures.html, verified
2026-08-02). Staltz frames Intent as "a function from Observable of user
events to Observable of actions", which is the precise, narrow claim that
distinguishes MVI from a plain Flux-style dispatcher, the intent function is a
named, testable seam between a raw DOM event and the meaning the application
assigns to it.

The name is contested in exactly one respect worth stating plainly. MVI as
practiced on Android and Kotlin Multiplatform since roughly 2017 is a
different, though closely related, formulation than the reactive-stream
version above. The mobile community's MVI drops the requirement that Model
and View be pure functions over an Observable pipeline and instead describes
a cycle of an immutable State object, a sealed class or enum of Intents that a
user or the system can raise, and a reducer that folds an Intent onto the
current State to produce the next State. Google's own Android architecture
guidance for Jetpack Compose describes the same shape under the name
Unidirectional Data Flow, UDF, without using the letters MVI at all, stating
that "the pattern where the state flows down and the events flow up is
called a unidirectional data flow" and that "there is a single source of
truth for the UI" (Google, Android Developers, "UI layer",
https://developer.android.com/topic/architecture/ui-layer, verified
2026-08-02). This entry treats MVI as the name the mobile and Kotlin
Multiplatform community settled on for that UDF shape, and treats Staltz's
reactive-stream formulation as the earlier, stricter ancestor. Both agree on
the core discipline, a single immutable State, and a named channel, called
Intent, through which the outside world is allowed to ask for a change.

MVI is frequently confused with the Elm Architecture, which predates it and
uses the vocabulary Model, Msg, update, view rather than Model, Intent, View.
The two are structurally the same cycle under different names, see dimension
13. It is also frequently confused with plain MVVM, because most MVI
implementations on Android sit inside a ViewModel class, see dimension 4 for
the test that tells them apart.

## 2. Problem and context

A View that mutates its own local, mutable fields in response to individual
events accumulates state that nobody can reconstruct from a single snapshot.
A checkbox toggled here, a spinner shown there, a list scrolled somewhere
else, each mutation is a small, local, imperative edit, and the full picture
of what the screen currently shows exists only by re-deriving it from dozens
of scattered booleans and optionals living across several objects. This is
the everyday shape of a codebase before MVI. A `ViewController` or `Activity`
with fields like `isLoading`, `errorMessage`, `items`, `selectedId`, each set
independently from a different callback, a different network completion
handler, a different button tap. Two of those fields can disagree with each
other, `isLoading` true while `items` is already populated, and nothing in
the code prevents it, because nothing ever asserted that the combination of
all fields at any instant is a single, valid, describable thing.

The problem sharpens under three real conditions. First, asynchronous work.
A network call started under one state can complete after the user has
already left the screen or triggered a second request, and if completion
directly mutates fields, the field values become a race rather than a
history. Second, testing. Asserting that a screen looks right after a
sequence of taps means either driving the real UI or hand-reconstructing
which fields a test double happened to set, because there is no single value
to assert against. Third, debugging a report from a user. Without a record of
what state the screen was actually in, and what sequence of external
triggers produced it, a bug that only a user manages to reproduce is close to
unfalsifiable from the developer's side.

MVI's context is any interactive UI, most commonly a mobile screen or a
single-page web application, where the state space is genuinely stateful
across more than a couple of fields and where reproducibility of that state
across time, or across a debugging session, actually matters. It is
narrower than a claim about all UI code, see dimension 4.

## 3. Forces

- **Predictability.** Favoured, strongly. Every state transition is a pure
  function, current State plus an Intent yields next State, so the same
  Intent applied to the same State always produces the same result, with no
  hidden mutable context.
- **Debuggability and reproducibility.** Favoured. Because State is a single
  immutable value and Intents are a linear, loggable stream, a bug report can
  become a replayable list of Intents applied to a starting State, which is
  the origin of the time-travel debugging feature several MVI libraries
  advertise, see dimension 9.
- **Consistency of the rendered UI.** Favoured. The View is a pure rendering
  of State, so it is structurally impossible for two parts of the screen to
  disagree, because there is only one State object for both to read from.
- **Boilerplate and file count.** Sacrificed. A trivial screen with three
  buttons still needs a State data class, an Intent sealed hierarchy, a
  reducer, and often a SideEffect or Label channel for one-shot events, four
  new types for what a mutable field would have done in one line.
- **Latency and allocation pressure.** Sacrificed, in proportion to update
  frequency. Every transition allocates a new State object rather than
  mutating one in place, which is a real cost on a screen updating many
  times per second, for example a live audio waveform, and is negligible on
  a screen that updates a handful of times per user session.
- **Learning curve and onboarding.** Sacrificed. A developer arriving from an
  imperative background must learn the discipline of never mutating outside
  the reducer, which is enforced by convention in most implementations
  rather than by the compiler, see dimension 11.
- **Handling of transient, one-shot events.** Genuinely awkward, and this is
  the force most MVI writeups gloss over. A toast, a one-time UI event, or a
  snackbar is not a durable fact about the screen's State, and cramming it
  into State risks it firing again on every recomposition or configuration
  change. Serious MVI implementations add a second, separate channel for
  these, see dimension 8.
- **Team topology.** Favoured for a codebase where UI logic and rendering are
  owned by different people or reviewed separately, because the reducer is a
  self-contained, synchronously readable unit that a reviewer can audit
  without running the app.

No pattern here gives something for nothing. The price of a single
predictable State is paid in ceremony and in an allocation on every event,
and the price of that allocation is worth it exactly when the state space
and its history are complex enough that the alternative, mutable fields,
would otherwise cost more in bugs than the ceremony costs in typing.

## 4. Applicability and non-applicability

Reach for MVI when the following hold.

- The screen has a state space wide enough that mutable fields would need to
  be checked against each other for consistency, more than two or three
  interdependent pieces of information.
- Asynchronous work, network calls, database reads, sensor streams, can
  complete after the user has moved on, and the code needs a principled way
  to discard or reconcile a stale result against the current State.
- Reproducing a reported bug from a linear log of user actions is valuable,
  which is common in consumer mobile apps at scale and in collaborative
  editors.
- The team already has, or is willing to adopt, a UI toolkit that renders
  from a single state object efficiently, Jetpack Compose, SwiftUI, React,
  or an equivalent declarative renderer. MVI paired with an imperative View
  that must be manually diffed on every state change reintroduces by hand
  the work the declarative renderer would have done for free.
- Multiple sources can produce State changes concurrently, a user tap, a
  push notification, a background sync, and the code needs one place where
  all of them are serialized into a single, ordered stream.

Do NOT reach for MVI in these cases, and the reason matters more than the
rule.

- **A static or near-static screen.** A settings row that shows the app
  version has no state machine worth modelling. A single `@State` field or a
  constant is the honest shape, and a State data class plus an Intent
  hierarchy for it is ceremony with no payoff, the speculative generality
  the GoF entries in this repository also warn against.
- **A screen whose complexity lives in a multi-step wizard with heavy
  branching and backtracking.** MVI models the current, single snapshot
  well, but a wizard's real complexity is the transition graph between many
  named steps, which a plain State enum tends to represent as a sprawling
  sealed hierarchy that duplicates fields across cases. A dedicated
  finite-state-machine formulation, see the State pattern entry, or a
  dedicated flow-graph library, usually reads more honestly than shoehorning
  the wizard into one MVI State.
- **High-frequency, low-level animation or per-frame rendering state.**
  Reallocating an immutable State object on every animation frame, sixty
  times a second, is measurable overhead against a mutable, in-place-updated
  render target. Games and custom drawing code that update every frame
  belong to a different pattern family entirely, usually an entity system
  or direct mutable buffers.
- **Genuinely global, cross-screen application state with no single owning
  View.** MVI's State belongs to one screen or one bounded feature. Global
  concerns, the signed-in user, feature flags, a shopping cart shared across
  screens, are better served by a dedicated store the individual screens'
  MVI State objects read from as a dependency, rather than folding
  everything into one State per screen. Conflating the two is the most
  common real-world misuse, see dimension 11.
- **One-shot side effects treated as durable state.** If the team's answer to
  "how do we show a toast" is "add an `errorMessage: String?` field to
  State", the pattern is being applied past where it is honest, see
  dimension 8 for the correct separate channel.
- **A team with no declarative rendering layer and no appetite to add one.**
  MVI without a renderer that can efficiently diff a whole State object
  against the previous one forces hand-written manual diffing at every
  callback, which reproduces the very inconsistency bugs the pattern exists
  to remove.

## 5. Structure

Four participants, named by the role they play. Nomenclature varies slightly
across implementations, the roles below are stable across almost all of
them.

- **State, or Model.** An immutable value type holding every piece of
  information the View needs to render itself, and nothing else. A
  well-formed State is a single source of truth, any two reads of the same
  State value at the same instant must render identically.
- **Intent.** A closed set of the things that can legitimately ask the State
  to change, usually a sealed class, enum, or discriminated union.
  Confusingly named relative to Android's own `android.content.Intent`
  inter-component messaging class, which is unrelated, this is a domain
  concept private to the MVI cycle. An Intent instance carries only the data
  needed to describe what happened, `LoadClicked`, `ItemSelected(id)`,
  `RetryRequested`, never a reference to the View or a callback.
  Distinguish an Intent, which describes a completed user or system action,
  from an Event, the raw platform callback that produced it, `onClick`
  fires an Event, which the caller translates into an Intent before it
  enters the cycle.
- **Reducer, or Update function.** A pure function, or as close to pure as
  the platform allows, from the current State and an Intent to the next
  State, `(State, Intent) -> State`. Any asynchronous work an Intent
  triggers, a network call, is dispatched as a side effect that will itself
  eventually produce a new Intent when it completes, the reducer step that
  receives that Intent is still pure.
- **View.** A pure rendering function from State to the visible UI,
  `(State) -> UI`, and the sole origin of new Intents, translating a raw
  platform Event into a domain Intent and forwarding it back into the cycle.
  In every serious implementation a fifth, quieter participant exists
  alongside these four.
- **SideEffect handler, or Effect, or Label channel.** Owns the boundary to
  the outside world, actually making the network call an Intent requested,
  actually changing screens, actually showing the toast, then feeding any
  result back in as a new Intent. Kept separate from the reducer precisely
  so the reducer stays pure and testable, see dimension 8.

Relationships. State flows one direction, Reducer to View. Intent flows the
opposite direction, View to Reducer. The View never mutates State directly
and never calls the Reducer's internals, it only emits an Intent into the
cycle and receives whatever State comes back. This one-directional, closed
loop is the structural feature that every other MVI claim, testability,
predictability, replayability, is derived from.

## 6. ASCII structure diagram

```
        +-------------------------------------------------------------+
        |                                                              |
        v                                                              |
+---------------+   State (immutable)   +----------------------+       |
|    Reducer    |----------------------->        View          |       |
|  (State,      |                       | render(State) -> UI  |       |
|   Intent)     |                       +----------+-----------+       |
|   -> State    |                                  |                   |
+-------^-------+                                  | user event        |
        |                                          v                   |
        |                              +----------------------+        |
        |         Intent               | translate Event      |        |
        +------------------------------|   -> Intent           |       |
        |                              +----------------------+        |
        |                                                              |
        |            Intent (from an async result)                    |
+-------+-------+                                                      |
| SideEffect    |  performs network calls, screen changes, storage     |
| handler       |  reads, requested by an Intent                      |
| emits: Intent |----------------------------------------------------->+
+---------------+

  Only two things ever cross the boundary between the boxes, an
  immutable State value flowing down, and a discrete Intent value
  flowing up. Nothing else is shared.
```

## 7. Dynamics

The runtime cycle is a strict loop with one entry point, an Intent, and one
observable output, a new State.

```
View            Reducer/Store         SideEffect handler        Backend
 |                    |                       |                    |
 |-- taps button ---->|                       |                    |
 |  (translated to    |                       |                    |
 |   Intent.Load)     |                       |                    |
 |                    |-- reduce(State0,      |                    |
 |                    |   Intent.Load)        |                    |
 |                    |   -> State1           |                    |
 |                    |   (State1.loading     |                    |
 |                    |    = true)            |                    |
 |<-- render(State1) -|                       |                    |
 |  (spinner shown)   |                       |                    |
 |                    |-- dispatch effect --->|                    |
 |                    |   "fetch items"       |                    |
 |                    |                       |-- GET /items ----->|
 |                    |                       |<-- 200, JSON ------|
 |                    |                       |                    |
 |                    |<-- Intent.LoadedOK(   |                    |
 |                    |     items) -----------|                    |
 |                    |-- reduce(State1,      |                    |
 |                    |   Intent.LoadedOK)    |                    |
 |                    |   -> State2           |                    |
 |                    |   (loading=false,     |                    |
 |                    |    items populated)   |                    |
 |<-- render(State2) -|                       |                    |
 |  (list shown)      |                       |                    |
 |                    |                       |                    |
```

Two timing properties worth stating plainly. First, the loop is
single-consumer, every Intent, whether raised by a tap or by a side effect
completing, passes through one serialized reduction point, which is exactly
what removes the two-fields-disagreeing race from dimension 2, there is
never a moment where two Intents are being reduced concurrently against the
same State. Second, the loop is why MVI supports replay debugging, because
the entire history of the screen is representable as `State0` plus an
ordered list of Intents, `reduce` folded across that list from `State0`
deterministically reproduces every intermediate State, which is exactly the
time-travel feature several implementations expose as a developer tool, see
dimension 9 for Mobius and MVIKotlin.

## 8. Implementation variants

**Reactive-stream MVI, the original Cycle.js shape.** State, View, and
Intent are literally functions over Observables, `intent(Sources) ->
Stream<Action>`, `model(Stream<Action>) -> Stream<State>`,
`view(Stream<State>) -> Sinks`. This is the strictest, most functionally pure
form and the one Staltz describes, and it is rare outside the Cycle.js
project itself because most platforms do not ship a first-class Observable
primitive.

**Sealed-class Kotlin MVI, the dominant Android shape.** State is a data
class, Intent is a sealed class or interface, the Reducer is a `when`
expression, or a `reduce` method, inside a ViewModel that exposes State as a
`StateFlow`. This is the shape MVIKotlin, Orbit MVI, and most hand-rolled
Android MVI implementations use, see dimension 9.

**Redux-shaped MVI.** A single global Store holds the entire application's
State, Actions are dispatched through middleware, and Reducers are pure
functions combined via `combineReducers`. Redux itself predates the MVI name
and is usually classified separately, but Redux applied to one screen's local
state, rather than the whole application, is functionally identical to MVI,
see dimension 13 for where the line is drawn.

**Elm Architecture shaped, non-JavaScript.** `update(Msg, Model) -> (Model,
Cmd Msg)`, `view(Model) -> Html Msg`, with Commands standing in for the
SideEffect handler. Rust's iced GUI toolkit and several Rust cross-platform
UI libraries implement this shape directly under the name Model-Update-View,
see dimension 9. The formulation is structurally MVI with different names for
the same four roles.

**MVI-over-MVVM, the pragmatic hybrid.** The State, Intent, and Reducer
triple lives inside a conventional ViewModel, and the View subscribes to the
ViewModel's exposed State the same way it would subscribe to a plain MVVM
ViewModel's properties. This is by far the most common shape encountered in
production code, because it lets a team adopt MVI's internal discipline
without discarding an existing MVVM binding layer, SwiftUI's `@Published`, or
Compose's `StateFlow` collection. The trade-off is that MVI in this variant
is really a design discipline enforced by convention inside a ViewModel's
body, not a structurally distinct architecture from MVVM at the View
boundary, see dimension 4's test for telling the two apart.

**Split-channel MVI, State plus one-shot Effects.** The most important
practical variant, and the one every serious production implementation
converges on. A second, separate stream, usually called SideEffect, Effect,
or Label, carries transient, non-idempotent events, a toast, a one-time UI
event, a haptic buzz, so that they are consumed exactly once and never
re-fire on a configuration change or a State replay the way a plain State
field would. Orbit MVI's `postSideEffect` and MVIKotlin's `Label` are named
instances of this variant, see dimension 9.

## 9. Known production uses

**Spotify's Mobius, on the Spotify Android application.** Mobius is
described by Spotify as a functional reactive framework for managing state
evolution and side effects, built around a Model, an Event, an Effect, an
Update function receiving the current model and an event and producing the
next model plus effects, and an Effect Handler that executes effects and can
emit further events. Mobius does not use the letters MVI in its own name but
implements the same closed loop described in dimension 5, and Spotify states
it is used in Spotify's Android applications. Spotify AB, Mobius project
documentation, https://github.com/spotify/mobius, verified 2026-08-02.

**Google's Android Jetpack Compose UI-layer guidance, applied across the
Compose stack.** Android's own architecture documentation for the UI
layer prescribes the pattern where state flows down and events flow up,
names it unidirectional data flow, and states plainly that there is a
single source of truth for the UI, the identical shape to dimension 5 under
different naming. This is not a single named app but the recommended
architecture Google ships to every Compose developer through the official
Android Developers guides. Google, Android Developers, "UI layer",
https://developer.android.com/topic/architecture/ui-layer, verified
2026-08-02.

**MVIKotlin, maintained by Arkadii Ivanov, in production Kotlin Multiplatform
applications.** MVIKotlin is a Kotlin Multiplatform framework that provides a
way of writing shared code using the MVI pattern, exposing a Store with a
single source of truth for State and integrated time-travel debugging.
Arkadii Ivanov, MVIKotlin project documentation,
https://github.com/arkivanov/MVIKotlin, verified 2026-08-02.

**Orbit MVI, maintained by Appmattus Limited, shipped across Android, iOS,
and desktop targets via Kotlin Multiplatform.** Orbit is described by its
maintainer as a simple, type-safe MVI framework for Kotlin Multiplatform,
enabling shared business logic across Android, iOS and desktop, built around
an immutable State, a one-time SideEffect channel kept separate from State
to avoid memory leaks, and Intents that modify State only through a `reduce`
block. Mikolaj Leszczynski and Appmattus Limited, Orbit MVI documentation,
https://orbit-mvi.org/, verified 2026-08-02.

**iced, a cross-platform Rust GUI toolkit, under the name Model-Update-View
rather than MVI.** iced follows the Elm Architecture explicitly, a State
struct, a Message enum, an `update` function of type `(&mut self, Message)
-> Task<Message>`, and a `view` function of type `(&self) -> Element
<Message>`, the structurally identical loop to dimension 5 with Message
playing the role of Intent, cited here as a named non-Kotlin, non-JavaScript
production implementation of the same architecture.

## 10. Consequences

Positive.

- A single immutable State value fully describes what the screen shows at
  any instant, which removes by construction the class of bug where two
  parts of a rendered screen disagree with each other.
- State transitions are pure and therefore trivially unit-testable, given a
  starting State and an Intent, the expected next State is an assertion with
  no mocking of the View or the platform required.
- A linear history of Intents applied to a starting State is a replayable,
  loggable record of exactly how the screen got where it is, which converts
  many not-reproducible bug reports into a replayable Intent log.
- Asynchronous completions are folded back into the same single reduction
  point as user actions, so a stale network response arriving after the user
  has moved on is just another Intent the current reducer logic can choose
  to ignore, rather than a race against mutable fields.
- New behaviour is added by adding a new Intent case and a new reducer
  branch, which a code reviewer can read end to end without running the app.

Negative.

- Every event allocates a new State object, which is measurable overhead on
  high-frequency updates and is one reason the pattern is inappropriate for
  per-frame rendering state, see dimension 4.
- The State, Intent, Reducer, and often a SideEffect type are four new
  declarations for even the simplest screen, which is real, ongoing typing
  and file-count cost that a mutable-field implementation does not pay.
- One-shot events do not fit naturally into a durable State value, and a
  team that has not adopted the split-channel variant from dimension 8 will
  reinvent it badly, usually as a nullable String field that must be
  manually cleared after being consumed.
- The discipline that the reducer stays pure and all side effects live
  outside it is enforced by team convention on most platforms, not by the
  type system, so a codebase can silently rot into calling network APIs
  directly from inside a reducer with nothing stopping it at compile time.
- A State object that grows to hold every field any part of a large screen
  might ever need becomes its own maintenance burden, effectively a second,
  informally typed schema that must be kept consistent with the actual UI.

## 11. Failure modes and misuse

**The God State object.** Symptom. A single State data class with forty
fields, most of them nullable, most of them relevant only to one sub-section
of the screen, and a reducer with an equally long `when` block. Cause. Every
new feature added a field to the one State type instead of asking whether it
belonged to a sub-screen with its own State. Fix. Split the screen into
independently reduced sub-features, each with its own State, Intent, and
reducer, composed by the parent, the same decomposition Redux's
`combineReducers` exists to formalise.

**One-shot events crammed into State.** Symptom. A toast or a one-time UI
event fires again, unprompted, after a screen rotation, a process restart, or
a State replay in a test. Cause. The event was stored as a plain State field,
for example `errorMessage: String?`, rather than routed through a separate,
consume-once channel. Fix. Adopt the split-channel variant from dimension 8,
a SideEffect or Label stream that the View collects exactly once and that is
never part of the State snapshot a replay or a configuration change restores.

**Side effects performed inside the reducer.** Symptom. A test that calls
`reduce(state, intent)` and asserts the returned State makes a real network
call, or the test suite becomes flaky because reduction depends on wall-clock
time or I/O completion. Cause. A network call, a database write, or a
screen-change call was placed directly inside the reducer function instead
of being dispatched as an effect for a separate handler to perform. Fix.
Move every impure operation into the SideEffect handler from dimension 5,
and have it communicate back only by emitting a new Intent.

**Intent explosion mirroring every UI callback one-to-one.** Symptom. An
Intent hierarchy with as many cases as the screen has interactive widgets,
none of them named for what the user meant, all of them named for which
widget fired, `ButtonAClicked`, `ButtonBClicked`, `CheckboxToggled`. Cause.
The translation step from raw Event to Intent was skipped, and the platform
Event was passed through unchanged. Fix. Name Intents for the user's meaning,
`RetryRequested` rather than `ButtonAClicked`, which is also what makes the
Intent log in dimension 9 useful for a human reading a bug report.

**Global application state modelled as one screen's local MVI State.**
Symptom. A change to the signed-in user, made from an unrelated screen, does
not appear on this screen until an unrelated, coincidental State
recalculation happens to touch it. Cause. Cross-screen shared state was
folded into a screen-local State object rather than kept in a shared,
independently observed store the screen's reducer reads as a dependency.
Fix. Separate screen-local UI State from shared application state, and have
the reducer subscribe to the shared store's changes as an Intent,
`UserChanged(user)`, rather than owning a private copy of it.

**Reducer that is not actually a pure function.** Symptom. Two runs of the
same test with the same Intent sequence produce different final States, or a
production bug only reproduces intermittently despite an identical Intent
log. Cause. The reducer reads a mutable field, the wall clock, or a random
number generator directly, rather than receiving everything it needs as
arguments on the Intent or the current State. Fix. Push every non-deterministic
input, timestamps, random values, into the Intent payload at the point the
Intent is created, so the reducer's own body stays a pure function of its two
arguments.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Model-View-Intent | Model-View-ViewModel | Redux, whole-app store | Elm Architecture | Model-View-Controller |
|---|---|---|---|---|---|
| Single source of truth for a screen | Strong, by construction | Weak, ViewModel state is often several independent observables | Strong, but scoped to the whole app, not one screen | Strong, identical shape to MVI under different names | Weak, state lives partly in the Model and partly in Controller-held fields |
| Replayable history of user actions | Strong, an Intent log plus a starting State reproduces every intermediate State | Weak, ViewModel methods are usually imperative calls, not a loggable stream | Strong, this is Redux's own headline feature via Redux DevTools | Strong, Commands and Msgs form the same loggable stream | Weak, no standard mechanism |
| Handling one-shot events, toasts, screen changes | Awkward without a dedicated second channel, see dimension 8 | Natural, an event can be a one-shot callback or a `SharedFlow` with no State involved | Awkward, same problem as MVI, middleware or a dedicated slice is needed | Awkward, same problem, addressed via a Cmd that the runtime consumes once | Natural, the Controller just performs the action directly |
| Boilerplate for a simple screen | High, four new types minimum | Low, one ViewModel class with plain properties | Very high, actions, reducers, and often middleware, for even one screen | High, the same as MVI | Low, a Controller method calling the Model directly |
| Testing state transitions in isolation | Very easy, a reducer is a pure function of two arguments | Moderate, requires instantiating the ViewModel and observing exposed state after calling a method | Very easy, same reason as MVI | Very easy, same reason as MVI | Hard, Controller logic is usually entangled with the platform View APIs |
| Fit for high-frequency updates, per-frame state | Poor, allocates a new State object per update | Moderate, mutable properties can be updated in place | Poor, same reason as MVI | Poor, same reason as MVI | Poor, direct Controller mutation is possible but usually un-observed |
| Scope of the single store | One screen or one bounded feature | One screen, usually, sometimes shared across a flow | The entire application, one global store | Usually the entire application, following Elm's own convention | One screen, entangled with the platform View |
| Learning curve for a team new to the pattern | High, the split-channel discipline in particular is easy to get wrong | Low, close to how most teams already think about a presenter object | High, plus Redux-specific vocabulary, middleware, thunks, selectors | High, plus a new language's own idioms in the canonical case | Low, closest to how most frameworks are taught by default |

Reading of the table. MVI and the Elm Architecture are, for practical
purposes, the same trade-off under different names, see dimension 13. MVI
wins over MVVM specifically where replayability and a single indisputable
State snapshot matter more than low ceremony. Redux wins over screen-scoped
MVI specifically where state genuinely needs to be shared and observed from
many unrelated screens at once. MVC loses to all of the above on
testability and predictability but remains the lowest-ceremony option for a
screen simple enough that none of the other columns' strengths are needed.

## 13. Related and incompatible patterns

- **Elm Architecture.** The closest relative, structurally identical, Model
  plus Msg plus update plus view, under different names, Msg for Intent,
  update for Reducer, Cmd for SideEffect. Where a codebase already commits
  to Elm's own vocabulary, adding MVI on top is renaming, not architecture,
  see the Rust production use in dimension 9.
- **Redux and Flux.** A generalisation upward. MVI scoped to a single global
  store, with the same Action-in, State-out, pure-reducer shape, is Redux.
  The practical difference in most real codebases is scope, MVI is usually
  one screen's local architecture, Redux is usually the whole application's,
  see dimension 12.
- **Model-View-ViewModel.** The most commonly confused sibling, and the one
  most production MVI code is actually built on top of, see dimension 8's
  MVI-over-MVVM variant. The test that separates them, does State change
  only through a named, closed set of Intents reduced by a pure function, or
  can any method on the ViewModel mutate exposed state directly. If the
  latter, it is MVVM regardless of what the team calls it.
- **Observer.** The mechanism, not the architecture. The View observing
  State, and the Reducer's output notifying that observer, is an instance
  of the Observer pattern, `StateFlow`, `@Published`, an RxJava
  `Observable`, are all Observer implementations MVI is commonly built on.
- **Command.** The SideEffect handler from dimension 5 is frequently
  implemented as a queue of Command objects, one per requested effect,
  executed by a dedicated executor that reports back via a new Intent. Cmd
  in the Elm Architecture is a named instance of exactly this composition.
- **Memento.** A snapshot of State plus the Intent log that produced it is,
  structurally, a sequence of Mementos, which is precisely what makes
  time-travel debugging, see dimension 9's MVIKotlin, possible without any
  bespoke serialization work beyond what the pattern already requires.
- **State, the GoF behavioural pattern.** A different granularity of the
  same idea. State the GoF pattern models one object's own internal
  behavioural mode switching between named classes. MVI's State is a plain
  immutable data value with no behaviour attached, and the transitions
  between its values are external, in the reducer, not internal, in
  polymorphic methods on the State itself. A screen whose real complexity is
  a small number of named modes with very different behaviour, not merely
  different data, is often better served by GoF State nested inside one
  field of an MVI State object, rather than by either pattern alone.
- **Model-View-Controller.** Actively incompatible as a mental model, though
  not impossible to bolt together badly. MVC's Controller is explicitly
  permitted, expected even, to mutate the Model directly in response to a
  View event, which is precisely the unguarded mutation MVI's closed
  Intent-Reducer loop exists to prevent. A codebase that layers an MVI
  reducer underneath an MVC Controller that also directly pokes the Model
  has two disagreeing sources of truth and neither pattern's benefits.

## 14. Refactoring path in and out

Introducing the pattern into a screen built on mutable fields.

1. Identify every field on the View or Controller that participates in what
   the screen currently shows, `isLoading`, `items`, `errorMessage`, and
   collect them into one new immutable data class, the State. Do not yet
   change how they are set, only where they live.
2. Add a single setter, `setState(newState)`, and route every existing
   mutation through it instead of touching a field directly. At this point
   nothing about the architecture has changed, only the storage location,
   and the tests, if any, should still pass unmodified.
3. Enumerate every distinct place in the code that currently calls
   `setState`, and give each one a name describing what happened, not which
   field changed, `LoadStarted`, `ItemsReceived(items)`,
   `LoadFailed(error)`. This enumeration becomes the Intent sealed
   hierarchy.
4. Extract the logic inside each `setState` call site into one pure function
   taking the current State and the new Intent and returning the next
   State, the Reducer. Move the actual call sites to instead construct an
   Intent and pass it through this one function.
5. Identify any call site that performs I/O, a network call, a database
   write, alongside computing the new State, and split it, the I/O becomes
   a SideEffect the Reducer requests, the result of that I/O becomes a new
   Intent fed back into step 4's function once the effect completes.
6. Identify anything that was set as a field but is really a one-shot
   signal, an error dialog shown once, a one-time screen change, and move it
   out of State into the separate SideEffect or Label channel from
   dimension 8, rather than leaving it as a nullable State field that must
   be manually cleared.
7. Write the reducer-level unit tests this refactor now makes possible,
   asserting that `reduce(state, intent)` equals the expected next State for
   the important transitions, before the refactor is considered finished.

Removing the pattern when it stops earning its place. Signals include a
State object that has grown past what any single feature actually needs, or
a screen simple enough, after simplification elsewhere in the product, that
the ceremony now outweighs the benefit.

1. Confirm the screen genuinely no longer needs replay, testability of
   transitions in isolation, or protection against races between
   concurrent Intents, since those are what the ceremony is buying.
2. Inline the Reducer's `when` branches back into the call sites that used
   to construct each Intent, turning each branch back into a direct
   mutation or a direct call to a plain setter.
3. Delete the Intent sealed hierarchy once nothing constructs an instance of
   it.
4. Fold the SideEffect handler's logic back into the call sites that
   trigger it, if the split-channel discipline from step 6 above is no
   longer earning its keep either.
5. Verify the remaining tests, rewritten against the plain fields or a
   simpler ViewModel API, still assert the same observable behaviour a user
   would see, since this direction of the refactor trades testability of
   transitions for less ceremony, and that trade should be made
   deliberately, not by omission.

## 15. Testing and verification

Easier because of the pattern.

- The reducer is a pure function, `(State, Intent) -> State`, so unit tests
  need no mocks, no fakes, and no running platform, asserting the returned
  State against an expected value covers a transition completely.
- A sequence of Intents applied left to right against a starting State is a
  complete scenario test, folding `reduce` over the sequence from the
  initial State, which reads like a story of user actions and is easy for a
  non-author reviewer to follow.
- Because the View is a pure function of State, a snapshot test can assert
  the rendered output for a given State value directly, without driving any
  of the Intents that would normally produce that State, which decouples
  UI-rendering tests from business-logic tests entirely.
- Property-based testing applies naturally to the reducer, generating random
  valid Intent sequences and asserting an invariant holds of the resulting
  State, for example that a `loading` flag is never true at the same time as
  a populated error message, is a direct, cheap way to fuzz a state machine
  that would otherwise need hand-written edge-case tests.

Harder because of the pattern.

- Testing the SideEffect handler in isolation requires faking the boundary
  it talks to, the network client, the screen-routing host, which is
  ordinary integration-test work but is now a separate test surface from the
  reducer tests, and a team that only writes reducer tests can miss real
  bugs living entirely in the SideEffect handler.
- Verifying that a one-shot SideEffect or Label genuinely fires exactly
  once, and not zero or two times across a configuration change, needs a
  test that specifically exercises the platform lifecycle the split-channel
  discipline exists to survive, which is easy to skip because it looks like
  an edge case rather than the core behaviour.

Techniques that apply.

- **Table-driven reducer tests**, one row per given State, Intent, and
  expected State triple, the most common and highest-value test shape for
  this pattern, because the reducer's whole contract fits a table.
- **Golden Intent-sequence replay tests**, capturing a real, reported bug's
  exact Intent sequence, from a production log per dimension 16, and
  replaying it in a test to lock the fix in as a regression test.
- **Contract tests for the SideEffect handler's interface**, asserting that
  every effect the reducer can request has a corresponding case handled by
  the handler, catching the failure mode where a new Intent variant is added
  but the effect it requests is never wired up.

## 16. Observability signals

The single most valuable observability property of MVI is that the entire
history of a screen is representable as a starting State plus an ordered
Intent log, so production observability should be built to capture exactly
that, not a scattering of ad hoc log lines.

What to record.

- Every Intent as it enters the reducer, tagged with a screen identifier, a
  session or correlation identifier, and a monotonic sequence number, at
  debug level for high-frequency screens and info level for screens where
  every Intent is business-meaningful.
- The shape, not necessarily the full content, of the resulting State after
  each reduction, a hash or a small summary is often enough to detect drift
  without logging potentially sensitive full State contents on every event.
- A counter of Intents processed, labelled by Intent type, which shows the
  actual distribution of what users do on a screen without needing separate
  analytics instrumentation.
- Every SideEffect dispatched and its outcome, success, failure, or timeout,
  labelled by effect type, since the SideEffect handler is where real I/O
  failures live and the reducer's own logs will not show them.
- A gauge or histogram of time spent in each named State, which turns "users
  are stuck on the loading screen" from an anecdote into a measured
  distribution.

A healthy instance on a dashboard. The Intent-type distribution matches the
expected mix of user behaviour for the feature, the time-in-loading-state
histogram is tight and short, and the SideEffect success rate stays flat and
high. A failing instance. A specific Intent type's processing rate spikes
with no matching user-action spike, which usually means an Intent is being
re-emitted in a loop, often from a SideEffect that keeps failing and
retrying. Or the time-in-a-particular-State histogram develops a long tail,
which localises exactly which state transition is stuck, directly from the
histogram label, with no need to read code first. Or the SideEffect failure
counter for one effect type climbs while the reducer's Intent counter for
the corresponding retry Intent climbs in lockstep, which is the signature of
a retry storm and points straight at the SideEffect handler rather than the
reducer.

## 17. Security and privacy implications

The pattern is largely silent on security in its pure, in-memory form, the
Reducer and the View touch no external boundary at all. Three genuine
implications appear once the surrounding system is considered.

**The Intent log as a sensitive record.** The same property that makes MVI
valuable for debugging, a complete, ordered log of every Intent a user ever
raised, is a detailed behavioural record of that user. If a team wires
Intent logging in dimension 16 into a shared analytics or crash-reporting
pipeline without reviewing what each Intent's payload carries, form input,
a search query, a partially-typed message, that payload can leak personal
data into a system with weaker access controls than the app itself. Treat
Intent payloads the same as any other user-generated content for logging
purposes, redact or hash fields that carry personal data before they leave
the device, and do not log full State snapshots that include authentication
tokens or other secrets a ViewModel holds transiently.

**Replayed State as a stale-permission surface.** Because MVI is built to
reproduce a past State from a log, a naive implementation of a restore-my-
last-session feature that replays a saved Intent log after a permission or
an entitlement has since been revoked can reconstruct a State that displays
data the user, or the account, is no longer authorized to see. Any replay or
State-restoration feature should re-validate authorization at restoration
time, not assume the original Intent sequence is still valid to replay
blindly.

**The SideEffect handler as the actual trust boundary.** Because the
Reducer is deliberately pure and side-effect-free, all real security
enforcement, authentication headers, input sanitisation before a network
call, output encoding before rendering untrusted content, has to live in the
SideEffect handler or the View, never inside the reducer, since the reducer
by design cannot see anything outside its two arguments. A team that
mentally files MVI as handling their logic can under-scrutinize the
SideEffect handler specifically because it looks like plumbing rather than
logic, when it is in fact the one place in the whole architecture where
untrusted input and outbound requests actually meet.

On privacy specifically, State snapshots used for crash reporting or session
replay should be scrubbed of personal data the same way any other client-side
state dump would be, MVI does not change that obligation, it only makes it
easier to accidentally capture a complete, structured snapshot in one place,
which is a reason to be more deliberate about what that place logs, not less.

## 18. References

1. Andre Staltz. "Unidirectional User Interface Architectures".
   https://staltz.com/unidirectional-user-interface-architectures.html
   Verified 2026-08-02. Source of the Model-View-Intent name, the intent
   function definition, "a function from Observable of user events to
   Observable of actions", and the comparison against Flux and MVC in
   dimension 1.
2. Google, Android Developers. "UI layer".
   https://developer.android.com/topic/architecture/ui-layer
   Verified 2026-08-02. Source of the unidirectional data flow definition,
   "the pattern where the state flows down and the events flow up", and the
   single-source-of-truth statement quoted in dimensions 1 and 9.
3. Spotify AB. Mobius project documentation.
   https://github.com/spotify/mobius
   Verified 2026-08-02. Source of the Model, Event, Effect, Update function,
   and Effect Handler terminology, and the stated production use inside
   Spotify's Android applications, in dimension 9.
4. Arkadii Ivanov. MVIKotlin project documentation.
   https://github.com/arkivanov/MVIKotlin
   Verified 2026-08-02. Source of the Store and single-source-of-truth
   terminology and the time-travel debugging feature cited in dimensions 9
   and 15.
5. Mikolaj Leszczynski and Appmattus Limited. Orbit MVI documentation.
   https://orbit-mvi.org/
   Verified 2026-08-02. Source of the State, SideEffect, and reduce
   terminology, and the stated Android, iOS, and desktop production targets,
   cited in dimensions 8 and 9.

## Code examples

Three platforms where the pattern is genuinely idiomatic in different ways.
TypeScript shows the Redux-shaped variant, a single reducer over a
discriminated-union Action type, which is the form most JavaScript and
TypeScript teams actually reach for under the MVI or Redux name. Swift shows
the sealed-Intent, split-channel variant most common on iOS, a `Store`
class with a `State`, an `Intent` enum, and a separate one-shot
`SideEffect`. Rust shows the Elm Architecture shape via a minimal,
hand-written Model-Update-View loop in the style of the iced toolkit cited
in dimension 9, with no framework dependency, since the Rust implementation,
iced, is not vendorable inline here. Kotlin is omitted despite being the
most common home for the pattern in production, because Kotlin is not an
available toolchain in this environment, and this entry would rather omit a
language than present unrun code as verified.

### TypeScript

```typescript
type State = {
  loading: boolean;
  items: string[];
  error: string | null;
};

type Intent =
  | { kind: "LoadRequested" }
  | { kind: "LoadSucceeded"; items: string[] }
  | { kind: "LoadFailed"; message: string };

function reduce(state: State, intent: Intent): State {
  switch (intent.kind) {
    case "LoadRequested":
      return { ...state, loading: true, error: null };
    case "LoadSucceeded":
      return { loading: false, items: intent.items, error: null };
    case "LoadFailed":
      return { ...state, loading: false, error: intent.message };
  }
}

class Store {
  private state: State = { loading: false, items: [], error: null };
  private listeners: Array<(s: State) => void> = [];

  dispatch(intent: Intent): void {
    this.state = reduce(this.state, intent);
    for (const listener of this.listeners) listener(this.state);
  }

  subscribe(listener: (s: State) => void): void {
    this.listeners.push(listener);
  }

  current(): State {
    return this.state;
  }
}

function render(state: State): string {
  if (state.loading) return "Loading";
  if (state.error) return `Error, ${state.error}`;
  return `Items, ${state.items.join(", ")}`;
}

const store = new Store();
store.subscribe((s) => console.log(render(s)));
store.dispatch({ kind: "LoadRequested" });
store.dispatch({ kind: "LoadSucceeded", items: ["a", "b"] });
```

### Swift

```swift
struct AppState {
    var loading = false
    var items: [String] = []
    var error: String? = nil
}

enum Intent {
    case loadRequested
    case loadSucceeded([String])
    case loadFailed(String)
}

enum SideEffect {
    case showToast(String)
}

final class Store {
    private(set) var state = AppState()
    private var effectHandlers: [(SideEffect) -> Void] = []

    func onSideEffect(_ handler: @escaping (SideEffect) -> Void) {
        effectHandlers.append(handler)
    }

    func dispatch(_ intent: Intent) {
        switch intent {
        case .loadRequested:
            state.loading = true
            state.error = nil
        case .loadSucceeded(let items):
            state.loading = false
            state.items = items
        case .loadFailed(let message):
            state.loading = false
            state.error = message
            emit(.showToast(message))
        }
    }

    private func emit(_ effect: SideEffect) {
        effectHandlers.forEach { $0(effect) }
    }
}

func render(_ state: AppState) -> String {
    if state.loading { return "Loading" }
    if let error = state.error { return "Error, \(error)" }
    return "Items, \(state.items.joined(separator: ", "))"
}

let store = Store()
store.onSideEffect { effect in
    if case .showToast(let message) = effect {
        print("toast, \(message)")
    }
}
store.dispatch(.loadRequested)
print(render(store.state))
store.dispatch(.loadFailed("network unreachable"))
print(render(store.state))
```

### Rust

```rust
#[derive(Debug, Clone, PartialEq)]
struct Model {
    loading: bool,
    items: Vec<String>,
    error: Option<String>,
}

#[derive(Debug, Clone)]
enum Msg {
    LoadRequested,
    LoadSucceeded(Vec<String>),
    LoadFailed(String),
}

fn update(model: Model, msg: Msg) -> Model {
    match msg {
        Msg::LoadRequested => Model {
            loading: true,
            error: None,
            ..model
        },
        Msg::LoadSucceeded(items) => Model {
            loading: false,
            items,
            error: None,
        },
        Msg::LoadFailed(message) => Model {
            loading: false,
            error: Some(message),
            ..model
        },
    }
}

fn view(model: &Model) -> String {
    if model.loading {
        return "Loading".to_string();
    }
    if let Some(err) = &model.error {
        return format!("Error, {}", err);
    }
    format!("Items, {}", model.items.join(", "))
}

fn main() {
    let mut model = Model {
        loading: false,
        items: Vec::new(),
        error: None,
    };
    let history = vec![
        Msg::LoadRequested,
        Msg::LoadSucceeded(vec!["a".to_string(), "b".to_string()]),
    ];
    for msg in history {
        model = update(model, msg);
        println!("{}", view(&model));
    }
    assert_eq!(model.items, vec!["a", "b"]);
}
```
