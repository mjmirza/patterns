---
name: Model-View-Presenter
slug: model-view-presenter
family: 05-architectural
category: Architectural
aliases: [MVP, Taligent MVP, Passive View, Supervising Controller, Supervising Presenter]
first_described: "Potel, Mike, Taligent Inc. 1996"
maturity: established
related: [model-view-controller, model-view-viewmodel, observer, application-controller, dependency-injection]
incompatible_with: []
verified: 2026-08-05
---

# Model-View-Presenter

## 1. Name, aliases, and lineage

The canonical name is Model-View-Presenter, abbreviated MVP. It was set out in
Mike Potel, VP and CTO of Taligent Inc, "MVP. Model-View-Presenter, The Taligent
Programming Model for C++ and Java," Taligent Inc, 1996, available at
https://www.wildcrest.com/Potel/Portfolio/mvp.pdf, verified 2026-08-05. The
paper states plainly that Taligent, then a joint venture of Apple, IBM and
Hewlett-Packard operating as an IBM subsidiary, was "developing a next
generation programming model for the C++ and Java programming languages,
called Model-View-Presenter or MVP, based on a generalization of the classic
MVC programming model of Smalltalk." Martin Fowler corroborates the origin and
adds a second lineage. "MVP first appeared in IBM and more visibly at Taligent
during the 1990's" and was "further popularized and described by the
developers of Dolphin Smalltalk," Martin Fowler, "GUI Architectures,"
https://martinfowler.com/eaaDev/uiArchs.html, verified 2026-08-05. Wikipedia
adds that "Andy Bower and Blair McGlashan of Dolphin Smalltalk adapted the MVP
pattern to form the basis for their Smalltalk user interface framework" and
that "in 2006, Microsoft began incorporating MVP into its documentation and
examples for user interface programming in the .NET Framework," Wikipedia,
"Model-view-presenter,"
https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93presenter, verified
2026-08-05.

A fact most secondary sources omit, and it matters for reading the pattern
correctly. Taligent's original MVP was not the two-participant View plus
Presenter shape that most engineers picture today. Potel's paper decomposes
the interactive application into six abstractions answering six questions,
Model (what is my data), Selections (how do I specify my data), Commands (how
do I change my data), View (how do I display my data), Interactor (how do
events map into changes in my data), and Presenter (how do I put it all
together). The paper is explicit about the Presenter's job. "To capture this
distinction we refer to this kind of controller as a presenter... The role of
the presenter within MVP is to interpret the events and gestures initiated by
the user and provide the business logic that maps them onto the appropriate
commands for manipulating the model in the intended fashion." It goes on to
describe the presenter as "the traditional main or event loop part of the
application... like a traffic cop or orchestra conductor." That is a much
larger role than the "thin view, testable presenter" shape the industry
settled on later. The MVP most codebases build today, one View interface, one
Presenter, is closer to the simplified reading that Dolphin Smalltalk and
later Fowler and Microsoft each independently converged on, than to Taligent's
original six-part model.

Aliases that name real variants rather than pure synonyms. **Passive View** and
**Supervising Controller**, also called **Supervising Presenter**, are two
distinct sub-patterns of the general MVP idea, both catalogued by Fowler, see
dimension 8. The name **Presenter First** shows up in the Extreme Programming
and behavior-driven-development community for a workflow that writes the
Presenter and its tests before the View exists at all. This entry treats MVP
as the family name and treats Passive View and Supervising Controller as its
two dominant, competing implementation strategies rather than as separate
patterns, which is how Fowler himself organizes them.

## 2. Problem and context

A screen, form, or activity has to do three jobs at once. Render widgets, react
to the person's input, and coordinate with whatever the input changes, a
domain object, a network call, a file. Left alone, all three jobs collapse
into one class, usually the class the UI framework hands you, an Activity, a
UIViewController, a code-behind file, a JSF backing bean. That class ends up
importing the widget toolkit, the domain layer, and often the network client
in the same file, and every one of its methods is a `void` reacting to a
framework callback with no return value to assert on.

The concrete symptom that motivates reaching for MVP is a test suite that
cannot run without a display. A `LoginActivity` that reads a `EditText`,
calls a repository, and sets a `TextView`'s error text cannot be unit tested
on a JVM with no Android runtime, because the widget classes are stubs that
throw when touched outside an instrumented test. The same failure shows up as
`NotImplementedException` from a WinForms designer control under `NUnit`, or a
JSF backing bean that needs a live `FacesContext` to resolve a message bundle.
The business rule, "an empty password shows this exact error string," is
real logic that deserves a fast, deterministic test, but it is welded to a
widget that only exists inside a running UI.

MVP's context is therefore any UI-bearing class whose framework base type is
expensive, slow, or impossible to instantiate off the main thread or outside a
real display, combined with enough view-triggered logic, more than a null
check, that leaving it untested is a real risk. Where the widget toolkit is
already cheap to instantiate in a unit test, for example a pure DOM in a
headless browser test runner, the motivating problem weakens and other
patterns compete harder, see dimension 4.

## 3. Forces

- **Testability.** Favoured, and this is the pattern's entire reason to exist.
  Every branch of view-triggered logic moves into a plain object with no
  framework base class, so it runs on a JVM, a CLR, or a JavaScript engine with
  no display attached.
- **Coupling direction.** Favoured. The View depends on the Presenter through a
  narrow, hand-written interface it implements. The Presenter depends only on
  that interface, never on the concrete widget class, so the dependency points
  away from the framework and toward the application's own code.
- **Boilerplate.** Sacrificed. Every screen needs a View interface, a View
  implementation, and a Presenter, at minimum three types where a framework
  callback class alone would have done one. In the Passive View variant this
  interface can grow one property per widget.
- **Update latency and correctness.** A genuine trade inside the pattern, not
  against it. Passive View pushes every value, even the ones data binding
  would set for free, which removes any chance of a stale label, at the cost
  of writing that push by hand. Supervising Controller lets data binding carry
  the simple cases, which is less code but reintroduces a class of bug, an
  unbound field, that only a running screen will reveal.
- **Framework fit.** Sacrificed on any UI toolkit whose lifecycle already owns
  object construction, Android's `Activity`, ASP.NET Web Forms' page model,
  iOS's storyboard-instantiated `UIViewController`. The View still has to be
  constructed by the framework, so the Presenter is wired in after the fact,
  typically in `onCreate`, `Page_Load`, or `viewDidLoad`, which is an extra
  seam the framework did not ask for.
- **Navigation and lifecycle ownership.** Sacrificed without a companion
  pattern. MVP by itself says nothing about who decides to move from one
  screen's Presenter to the next, or who tears down a Presenter when its View
  is destroyed. Left unaddressed this becomes the leaked-reference failure
  mode in dimension 11.
- **Cognitive load for a newcomer.** Sacrificed at first, recovered later. A
  developer new to a codebase has to learn the View interface convention
  before touching a screen, which is friction on day one, but the same
  convention is what lets that developer read any screen's Presenter and know
  exactly what it can do to the screen, without opening the widget file.

## 4. Applicability and non-applicability

Reach for MVP when the following hold together.

- The UI framework's base class is expensive or impossible to instantiate in
  a fast unit test, and the screen has real view logic beyond trivial
  wiring, validation rules, conditional visibility, formatting, multi-step
  flows.
- More than one concrete View could sensibly exist behind the same behavior,
  a phone layout and a tablet layout, a web form and a CLI prompt, a
  production widget and a fake for tests.
- The team can commit to writing and maintaining a View interface per screen,
  and to keeping the View implementation genuinely passive, a discipline the
  compiler cannot enforce.
- The application already has, or can afford, a way to construct and dispose
  a Presenter alongside its View's lifecycle, whether that is manual wiring, a
  dependency injection container, or a navigation framework.

Do NOT reach for MVP in these cases, and the reason is the point.

- **The UI framework already gives you a cheap, testable seam.** A modern web
  frontend built on a virtual DOM (React, Vue) can unit test a component's
  render output and event handlers directly, in milliseconds, with no real
  browser. Wrapping that component in a hand-written View interface adds a
  layer the framework's own test tools already made unnecessary.
- **The screen has no branching logic, only display.** A read-only detail
  screen that shows five fields from one object has nothing worth testing in
  isolation. A View interface here is ceremony around a `data class`.
- **The framework's own state-holder already survives configuration changes
  and testable in isolation.** Android's `ViewModel`, backed by
  `Jetpack Compose` or `LiveData`/`StateFlow`, and iOS's `ObservableObject`
  under SwiftUI, both give the "logic that outlives the view and can be unit
  tested" property MVP exists to provide, without a hand-written View
  interface, because the reactive binding layer itself is unit-testable. This
  is why Google's own reference Android architecture samples moved away from
  their historical MVP branch toward MVVM-shaped ViewModel samples, a change
  visible in the current default branch of `googlesamples/android-architecture`
  on GitHub, verified 2026-08-05, which documents `ViewModel`, `Flow`, and
  `Repository` as the current recommended shape and no longer ships an MVP
  sample on its default branch.
- **The team wants two-way, declarative data binding as the default, not the
  exception.** MVVM's binder exists exactly for this. Forcing every field
  through an imperative `view.setX(value)` call when a binding expression
  would do is the Passive View tax paid with no testability benefit, because
  a modern binding layer is itself testable, see the trade-off matrix in
  dimension 12.
- **Multiple Views must stay synchronized against one shared model in real
  time**, a chat window and a notification badge both reflecting one
  unread-count model. Observer, applied directly between View and Model, or a
  shared reactive store, fits this better than routing every update through
  one Presenter's imperative calls.
- **The product is a single, short-lived script or CLI tool with one output
  path.** There is no second View to justify the interface, and no test the
  team plans to write against the branching, because there is no branching.

## 5. Structure

Three participants, following the naming Fowler settles on for the general
family, which differs slightly from Potel's original six-part vocabulary, see
dimension 1 for that distinction.

- **Model.** The domain data and the operations on it. It knows nothing about
  the View or the Presenter. In the simplified, modern form of MVP the Model
  is usually a plain domain object or a repository, not Potel's separate
  Selections and Commands abstractions.
- **View.** An interface, not a class, declaring the operations a Presenter
  needs, setters for display state and events the View raises when the person
  acts. The concrete View, an Activity, a Fragment, a Web Form's code-behind,
  a `UIViewController`, implements that interface and forwards raw framework
  callbacks to the Presenter with no interpretation of its own.
- **Presenter.** Holds a reference to the View through its interface, never
  through the concrete class. Receives events from the View, consults or
  mutates the Model, and pushes the Model's state back through View interface
  calls. The Presenter has no reference to the UI framework's base types at
  all, which is precisely what makes it constructible in a unit test.

Relationships. View depends on Presenter, by holding a reference to it and
forwarding events into it. Presenter depends on View, but only through the View
interface, and on Model, directly. Model depends on nothing above it. Unlike
classic MVC, there is no dependency from Model back to View, or from Model to
Presenter, unless the team layers Observer on top by choice, see dimension 13.
The dependency from View to Presenter, in addition to Presenter to View,
distinguishes MVP from MVC's one-directional Controller-to-View flow, and is
part of why Fowler classes MVP as its own pattern rather than a spelling
variant of MVC.

## 6. ASCII structure diagram

```
    +------------------------------+           +-----------------------+
    |            View               |  events   |       Presenter        |
    |    (interface, e.g. LoginView)|  ------>  |-------------------------|
    |--------------------------------|           | - view: LoginView      |
    | + showError(msg)               |  <------  | - model: AuthService   |
    | + showLoading(bool)            |  updates  | + onLoginClicked(...)  |
    | + navigateToHome()             |           | + onScreenShown()      |
    +------------------------------+           +-----------------------+
              ^ implements                                |
              |                                            | reads/writes
    +------------------------------+                       v
    |   LoginActivity (concrete)    |             +-----------------------+
    |   framework base = Activity   |             |         Model          |
    |--------------------------------|             |-------------------------|
    | forwards onClick, onTextChanged|             | + login(user, pass)   |
    | to presenter, no logic of its  |             | + AuthResult          |
    | own beyond that forwarding     |             +-----------------------+
    +------------------------------+

    The Presenter never imports Activity, UIViewController, or any
    widget toolkit type. It only knows the LoginView interface above.
```

## 7. Dynamics

The two dominant variants differ in exactly one step of this flow, marked
below, and that single difference is the whole Passive View versus
Supervising Controller distinction from dimension 8.

```
Person        LoginActivity (View impl)   LoginPresenter        AuthService (Model)
  |                    |                        |                       |
  |-- taps Login ----->|                        |                       |
  |                    |-- onLoginClicked(u,p) ->|                       |
  |                    |                        |-- login(u, p) ------->|
  |                    |                        |                       |-- validates,
  |                    |                        |                       |   calls backend
  |                    |                        |<-- AuthResult --------|
  |                    |                        |                       |
  |                    |                        | [decision made here,  |
  |                    |                        |  in the Presenter,    |
  |                    |                        |  no widget touched]   |
  |                    |                        |                       |
  |                    |<-- showError(msg) -----|  (*)  ---- OR ----    |
  |                    |<-- navigateToHome() ---|                       |
  |                    |                        |                       |
  |<-- screen updates -|                        |                       |
```

`(*)` is the branch point that Passive View and Supervising Controller treat
differently. In pure Passive View, every one of these calls, including a
trivial one like enabling the login button once both fields are non-empty,
goes through an explicit `view.setLoginButtonEnabled(true)` call from the
Presenter. In Supervising Controller, that trivial enablement is expressed as
a declarative binding between the two text field's non-empty state and the
button, set up once when the View is constructed, and the Presenter steps in
only for the harder case, the asynchronous login call and its error path
shown above. Martin Fowler states the distinction directly. "Passive View is
a very similar pattern to Supervising Controller, but with the difference
that Passive View puts all the view update behavior in the controller,
including simple cases," Martin Fowler, "Passive View,"
https://martinfowler.com/eaaDev/PassiveScreen.html, verified 2026-08-05, and
"Supervising Controller uses a controller both to handle input response but
also to manipulate the view to handle more complex view logic," Martin
Fowler, "Supervising Presenter,"
https://martinfowler.com/eaaDev/SupervisingPresenter.html, verified
2026-08-05.

## 8. Implementation variants

**Passive View.** The View exposes only property setters and getters and
raises events. Every value shown on screen, however trivial, is set by an
explicit Presenter call. Fowler names testing as the entire reason to choose
this. "The primary driver for Passive View is testing," and the payoff is
that "there is no dependencies in either direction between the view and the
model," Fowler, "Passive View," cited above. This is the strictest, most
verbose variant, and the one most engineers mean when they say "MVP" today.

**Supervising Controller, also called Supervising Presenter.** The View binds
directly to the Model for simple, declarative cases, and the Presenter
intervenes only for logic a binding expression cannot express. Fowler's
summary is that this trades completeness of testing for less code,
synthesizing the two Fowler pages cited above. Microsoft's own patterns and
practices SharePoint guidance chose this variant explicitly for its Partner
Portal and Training Management sample applications, noting "the Supervising
Presenter pattern makes simpler code a higher priority than complete
testability," Microsoft patterns and practices, "The Model-View-Presenter
(MVP) Pattern,"
https://learn.microsoft.com/en-us/previous-versions/msp-n-p/ff649571(v=pandp.10),
verified 2026-08-05.

**Contract interface per screen.** A common convention, seen throughout
Android's historical MVP samples and in many enterprise codebases, names one
interface `LoginContract` holding two nested interfaces, `LoginContract.View`
and `LoginContract.Presenter`, so both halves of one screen's contract live
in one file and the compiler catches a missing method on either side at the
same location.

**Constructor injection of the View.** The Presenter receives its View
through its constructor and stores it in a field, rather than being handed
the View later through a setter. This is the shape shown in Microsoft's own
sample code, `public RelatedPartsPresenter(IRelatedPartsView view)`, cited
above, and it is the shape that makes substituting a test double
mechanical, because no partial construction state exists.

**Event-bus-mediated MVP.** Google Web Toolkit's official MVP article
describes Presenters that communicate application-wide navigation and
cross-Presenter events through a shared `EventBus`, rather than holding
direct references to each other, explicitly to avoid Presenters coupling to
one another. GWT's own guidance restricts what goes on that bus. "App-wide
events are really the only events that you want to be passing around on the
Event Bus," GWT Project, "Large scale application development and MVP,"
https://www.gwtproject.org/articles/mvp-architecture.html, verified
2026-08-05.

**Reactive Presenter.** In languages with first-class streams, the Presenter
exposes a stream of view-state values instead of imperative setter calls, and
the View subscribes and renders. This form sits at the boundary between MVP
and MVVM, see dimension 13, and is common where the codebase already uses
RxJava, Combine, or coroutine `Flow` for other layers.

**Presenter First.** A workflow rather than a structural variant, associated
with the Extreme Programming community, where the Presenter and its unit
tests are written before a single line of the concrete View exists, using a
hand-mocked View interface. It is a discipline for adopting Passive View
rigorously, not a different runtime shape.

## 9. Known production uses

**Google Web Toolkit's official MVP architecture guide.** GWT's own project
documentation lays out Presenter, Display interface, and EventBus as the
recommended architecture for large GWT applications, and gives measured
numbers for the testability payoff of moving logic out of the browser-bound
View. "0.01 seconds" for a JRE-based unit test of extracted presenter logic
against "15.23 seconds" for the equivalent browser-dependent `GWTTestCase`.
GWT Project, "Large scale application development and MVP,"
https://www.gwtproject.org/articles/mvp-architecture.html, verified
2026-08-05.

**Microsoft patterns and practices SharePoint Guidance reference
applications.** The Partner Portal and Training Management sample
applications, shipped as part of Microsoft's patterns and practices SharePoint
guidance, are built around the Supervising Presenter variant of MVP, with view
interfaces such as `IRelatedPartsView` implemented by ASP.NET user-control
code-behind classes and presenters constructed with the view injected through
the constructor. Microsoft patterns and practices, "The Model-View-Presenter
(MVP) Pattern,"
https://learn.microsoft.com/en-us/previous-versions/msp-n-p/ff649571(v=pandp.10),
verified 2026-08-05.

**Dolphin Smalltalk's user interface framework.** Fowler records that "Andy
Bower and Blair McGlashan of Dolphin Smalltalk adapted the MVP pattern to
form the basis for their Smalltalk user interface framework," which is a
second, independent line of adoption from the Taligent origin, feeding into
the version of MVP most commonly described today. Wikipedia,
"Model-view-presenter," cited above, corroborating Fowler's "GUI
Architectures," cited above.

Beyond these three, MVP or a variant of it was, historically, the officially
recommended architecture in Google's own `googlesamples/android-architecture`
reference repository on a branch named `todo-mvp`. That branch no longer
exists on the repository as fetched 2026-08-05, `gh api
repos/googlesamples/android-architecture/branches` returns no branch matching
`mvp`, and the repository's current default branch documents a Jetpack
Compose plus `ViewModel` architecture instead. This entry does not cite the
historical Android sample as a verified current production use, because the
source that would prove it no longer resolves, and it is named here only as
context for the applicability judgment in dimension 4, per the anti-fabrication
requirement of this catalog. A reader wanting that historical example should
search the repository's tag or commit history directly rather than trust an
unverifiable claim in this entry.

## 10. Consequences

Positive.

- View-triggered logic becomes a plain object with no UI framework base
  class, runnable in a fast, deterministic unit test with a hand-written or
  mocked View.
- The View implementation shrinks to nearly nothing, forwarding calls in one
  direction and receiving setter calls in the other, which makes View bugs
  rare because there is almost nothing in the View left to get wrong.
- Multiple Views can share one Presenter's behavior, a mobile layout and a
  tablet layout, or a production View and a scripted UI-test double, without
  touching the Presenter.
- The View interface documents, in one place, everything a screen can ever
  show or do, which is a genuinely useful piece of design documentation a
  reviewer can read without opening the widget layout.
- Presenter construction is ordinary object construction, so it composes
  cleanly with constructor-based dependency injection.

Negative.

- Every screen costs at least one extra type, the View interface, on top of
  the concrete View and the Presenter the screen would have needed anyway.
- Passive View in particular multiplies boilerplate, one interface method and
  one Presenter call for every visible field, including fields a binding
  framework would have kept in sync for free.
- Nothing in the type system prevents the concrete View from quietly doing
  real work instead of forwarding, so "passive" is a discipline the team
  enforces by review, not a property the compiler checks.
- MVP by itself is silent on navigation between screens and on who owns a
  Presenter's lifecycle, which pushes real design work onto whichever
  companion pattern the team picks, see dimension 13.
- A View interface that grows to match every widget on a large screen becomes
  a maintenance burden of its own, changed on every layout tweak even when no
  behavior changed.

## 11. Failure modes and misuse

**The View interface leaks the widget toolkit anyway.** Symptom. The View
interface has a method returning a raw `android.widget.TextView` or a
`System.Windows.Forms.Control`, and the "unit test" for the Presenter needs a
real widget instance to run. Cause. The interface was written by exposing
whatever the concrete View already had rather than by asking what the
Presenter actually needs. Fix. Redesign the interface around values and
verbs, `showItems(List<Item>)`, not `getListView()`.

**The Presenter is retained past the View's death.** Symptom. An intermittent
crash referencing a destroyed Android `Activity`, or a `.NET`
`ObjectDisposedException` from a control, when a slow network call completes
after the person has navigated away. Cause. The Presenter held a strong
reference to the View and called into it after the View was torn down, and
nothing in MVP itself governs this lifecycle. Fix. Detach the View reference
in the screen's teardown callback, `onDestroy`, `Page_Unload`,
`viewWillDisappear`, and have the Presenter null-check or discard results
targeting a detached View, per the lifecycle discipline in dimension 16.

**Two Presenters race to update one View.** Symptom. A field flickers between
two values, or an error message from a stale request overwrites the correct
result of a newer one. Cause. Two asynchronous calls were in flight against
the same Presenter, or the same View was wired to two Presenter instances
after a re-entrant screen creation. Fix. Give every outbound async call a
generation or request identifier and discard the callback if a newer request
has since started, the same technique used to fix the classic race in any
async UI code.

**A "thin" Presenter becomes a god object.** Symptom. One Presenter class
several thousand lines long, handling five unrelated concerns because they
all happen to live on the same screen. Cause. MVP does not itself limit a
Presenter's size, and a large screen naturally accretes logic into whichever
class already has access to the View. Fix. Split by responsibility into
several collaborating Presenters, or extract non-view-specific logic into
plain use-case or interactor objects the Presenter delegates to, keeping the
Presenter itself limited to view orchestration.

**Supervising Controller's binding hides an untested path.** Symptom. A
production bug in a field that "just" uses data binding and was never
covered by a Presenter test, because the team assumed binding needs no test.
Cause. Choosing Supervising Controller trades some testability for less
code, deliberately, per dimension 3, and a team that forgets the trade was
made ships the untested half with false confidence. Fix. Add a thin
integration or UI-level test for the bound paths specifically, since the
Presenter-level unit tests will never see them.

**The interface is designed once and never revisited.** Symptom. The View
interface has methods nobody calls anymore and a Presenter that reaches
around it by casting to the concrete type when a new need arises, defeating
the whole abstraction quietly, one cast at a time. Cause. No review step
treats the View interface as a contract that changes with intention. Fix.
Delete unused interface methods when found, and add new capability to the
interface first, the concrete View second, exactly as any interface
evolution should proceed.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | MVP, Passive View | MVP, Supervising Controller | MVC (classic) | MVVM | Autonomous View (no pattern) |
|---|---|---|---|---|---|
| Testability of view logic | Highest. Every path goes through an explicit call the test can assert on | High. Bound paths are untested unless separately covered | Low. Logic scattered across widget-reacting controller methods | High, if the binding layer is itself unit-testable | Lowest. Logic lives inside framework callback methods |
| Boilerplate per screen | Highest. One interface method per visible field | Medium. Interface covers only complex cases | Low to medium, framework-dependent | Medium. A ViewModel plus bindings, no hand-written View interface | Lowest. No extra types |
| Coupling direction | View depends on Presenter through an interface, Presenter depends on nothing UI-specific | Same, plus View depends on Model for bound fields | Controller depends on View and Model, weaker inversion | ViewModel exposes observable state, View binds to it, similar inversion to MVP | View is coupled to everything it touches |
| Update propagation | Explicit, imperative, one call per change | Declarative for simple fields, explicit for complex ones | Model change notifies View directly, or View polls | Declarative, reactive, binding-driven throughout | Manual, embedded in the same method that handles input |
| Multi-view sync to one model | Poor, unless layered with Observer separately | Poor, same limitation | Native strength, MVC's Observer roots handle this directly | Good, observable state naturally fans out to many bindings | Poor |
| Framework fit on a reactive-native toolkit (SwiftUI, Compose, React) | Poor. Fighting the toolkit's own binding layer | Poor for the same reason | Poor | Strong. This is the shape those toolkits were designed around | N/A, no real seam exists to fight |
| Cost of adding a second View for the same behavior | Low. Implement the interface again | Low, same reason | Medium, controller logic often assumes one view shape | Low. Bind a new view to the same ViewModel | High. Logic must be copied or extracted first |
| Navigation and lifecycle ownership | Not addressed by the pattern itself | Not addressed by the pattern itself | Often owned by the controller layer or a front controller | Often owned by the platform's navigation framework | Owned informally by the view |

Reading of the table. MVP wins decisively where the toolkit's own binding
story is weak or absent and the team needs a hard testability guarantee.
MVVM wins where the toolkit already ships a first-class observable binding
layer, because it gets MVP's inversion with less hand-written interface code.
Classic MVC still wins for genuine multi-view-one-model fan-out. An
autonomous view is defensible only where the screen has no branching logic
worth testing.

## 13. Related and incompatible patterns

- **Model-View-Controller.** The direct ancestor. MVP is, by Potel's own
  framing, "a generalization of the classic MVC programming model of
  Smalltalk." The practical difference in the simplified modern form both
  patterns are usually compared in, is that MVC's Controller typically only
  receives input and updates the Model, leaving the View to observe the
  Model directly, while MVP's Presenter both receives input and pushes state
  back to the View through the View interface, so the View never talks to
  the Model at all in the Passive View variant.
- **Model-View-ViewModel.** The pattern that has, on toolkits with native
  reactive binding, largely superseded MVP for new work, see dimension 4.
  MVVM keeps MVP's dependency inversion, the ViewModel does not know its
  View, but replaces MVP's hand-written View interface and imperative setter
  calls with an observable state object the View binds to declaratively.
  Migrating a Passive View Presenter to a ViewModel is usually a matter of
  turning each `view.setX(value)` call into an assignment to an observable
  property.
- **Observer.** MVP's update mechanism, when a team wants the Model to
  notify interested parties of a change rather than have the Presenter poll
  it, is commonly layered in using Observer, with the Presenter as the
  observer. Pure Passive View, as described in dimension 8, deliberately
  avoids this by having the Presenter drive every update itself, so
  layering Observer on top of pure Passive View is a design choice, not a
  requirement of the pattern.
- **Application Controller.** Composes cleanly to solve the navigation gap
  named in dimension 3 and dimension 10. Fowler's related-patterns note in
  Microsoft's own SharePoint MVP documentation names this pairing directly.
  "If presenters interact with an application controller, the presenters do
  not need page flow and screen navigation logic," per the Microsoft
  patterns and practices page cited in dimension 9.
- **Dependency injection.** Composes cleanly and is close to mandatory in
  practice. A container supplies each Presenter with its Model
  collaborators, and the View, once constructed by the framework, supplies
  itself to the Presenter's constructor, exactly as shown in Microsoft's
  sample code cited in dimension 8.
- **Service Locator.** A tempting shortcut that conflicts with the pattern's
  purpose. A Presenter that reaches into a global locator inside its own
  methods, rather than receiving its collaborators through its constructor,
  hides a dependency the whole point of MVP was to make explicit and
  substitutable in tests, the same anti-pattern relationship this catalog
  names under the Factory Method entry's own discussion of Service Locator,
  and it applies identically here.
- **Passive View and Supervising Controller.** Not two different patterns
  related to MVP, but the two dominant strategies for implementing MVP
  itself, mutually exclusive per screen, since a Presenter either pushes
  every field explicitly or delegates some of them to binding, not both at
  once for the same field.

## 14. Refactoring path in and out

Introducing MVP into a screen whose logic currently lives inside a framework
callback class. Ordered steps.

1. Identify every piece of logic in the existing screen class that does not
   itself construct or touch a widget directly, meaning it could run without
   a display, validation rules, formatting, decisions about what to show
   next.
2. Write the View interface containing only what step 1's logic actually
   needs from the screen, expressed as setters and getters over plain values,
   never over widget types. Keep it minimal on the first pass, it grows as
   needed.
3. Make the existing screen class implement the new interface, delegating
   each interface method to the widget it already owns. Nothing behavioral
   changes yet. Run the existing tests, or manually verify the screen, since
   there likely are none yet, which is the whole reason for this refactor.
4. Create the Presenter class, empty, taking the View interface in its
   constructor and storing it in a field.
5. Move one piece of logic from step 1 into the Presenter, replacing its
   direct widget access with a call through the View interface. Wire the
   screen's existing callback method to call the new Presenter method
   instead of running the logic inline. Verify the screen still behaves
   identically.
6. Repeat step 5 for every remaining piece of movable logic, one at a time,
   verifying after each move, until the screen class contains nothing but
   forwarding calls.
7. Write the first Presenter unit test using a hand-written fake or a mock
   implementing the View interface. This is the payoff step, and it should
   be markedly faster than any UI test the team had before.
8. Decide, now that the seam exists, whether any remaining trivial fields
   should move to declarative binding, converting the screen from pure
   Passive View toward Supervising Controller if the team prefers less code
   over complete Presenter-level test coverage, per the trade in dimension 3.

Removing the pattern, when the toolkit's own reactive binding has made a
hand-written View interface pure overhead, for example after a rewrite from
Android Views to Jetpack Compose, or from UIKit to SwiftUI.

1. Confirm the new toolkit gives a testable observable state holder,
   `ViewModel` under Compose, an `ObservableObject` or `@Observable` type
   under SwiftUI, so the testability the View interface was providing is not
   lost in the move.
2. Convert the Presenter's fields into that observable holder's published
   properties, one at a time, replacing each `view.setX(value)` call with a
   direct assignment.
3. Delete the View interface's corresponding method as each property
   migrates, and update the concrete View to bind to the new observable
   property instead of implementing the removed method.
4. Once every method has migrated, delete the empty View interface and
   rename the class if the team's convention distinguishes `Presenter` from
   `ViewModel` naming.
5. Re-run the Presenter's existing unit tests against the new observable
   holder's properties directly, confirming the same behavioral coverage
   survived the move.

## 15. Testing and verification

Easier because of the pattern.

- The Presenter is a plain constructor-injected object, so a unit test
  constructs it with a hand-written fake View and asserts on the calls the
  fake recorded, with no UI framework, no display, and typically no mocking
  library needed at all for a small interface.
- Because the View interface is small and hand-controlled, a fake View
  implementation, one that stores whatever value it was passed in a public
  field the test reads back, is usually cheaper to write and read than a
  generated mock, and it makes the assertion read as plain data comparison.
- Async Model calls can be exercised deterministically by controlling
  whatever the Model's test double returns and when, then asserting the
  Presenter called the correct View methods in the correct order.

Harder because of the pattern.

- The concrete View's forwarding code, "does tapping this exact button call
  the exact right Presenter method with the exact right arguments," is
  outside the Presenter's own tests by construction and needs a genuine UI
  or instrumented test to cover, small as that surface should be if the View
  stayed passive.
- Supervising Controller's bound fields are, by design, outside Presenter
  test coverage entirely, per the failure mode in dimension 11, and need
  their own test strategy or an accepted gap.
- A View interface that grows large increases the size of every fake or mock
  written against it, which is a maintenance cost that compounds across
  every test file for that screen.

Techniques that apply.

- **Hand-written fake View over a generated mock**, for the reason given
  above, a small interface reads better as plain assertions than as
  mock-framework verify calls, and a fake avoids over-specifying interaction
  order the way a strict mock can.
- **Constructor injection of every Model collaborator**, so a Presenter test
  never needs a real network client, database, or file system, only a fake
  or a stub returning the exact response the test scenario calls for.
- **Golden-path plus one test per branch in dimension 11's failure modes**,
  specifically a test asserting the Presenter discards a stale async result
  after the View has been detached, which is the single highest-value test
  this pattern earns and the one teams most often skip.
- **A thin instrumented or UI-level smoke test per screen**, covering only
  that tapping the primary control calls the Presenter, never re-testing
  business logic already covered at the Presenter level, keeping the slow
  layer of the test pyramid genuinely thin.

## 16. Observability signals

MVP concentrates a screen's decision-making in one object, which makes that
object the natural place to instrument, and it also makes the Presenter's
lifecycle relative to its View's lifecycle the single most important thing
to make visible, because dimension 11's leading failure mode is exactly a
lifecycle mismatch.

What to record.

- A structured log line or trace span on Presenter attach and detach,
  carrying the screen name and a per-instance identifier, so a crash or a
  stale-update bug can be correlated to exactly which Presenter instance was
  live at the time.
- A counter of "update called on a detached view" events, which should be
  zero in a correct implementation and is the direct, cheap signal for the
  race condition failure mode in dimension 11. A non-zero rate on this
  counter is worth alerting on even before it causes a visible crash.
- A histogram of time from a user-initiated Presenter method call to the
  matching View update call completing, labelled by screen and by which
  branch was taken, error path or success path, since these often have very
  different latency profiles and averaging them hides both.
- For screens on the Supervising Controller variant, an explicit marker in
  logs or a code comment audited during review distinguishing bound fields
  from Presenter-driven fields, since this is exactly the boundary that
  silently loses test coverage, per dimension 11, and observability at
  review time is the only real defense.

A healthy instance on a dashboard. Attach and detach counts for a screen are
roughly equal over any window longer than a few seconds, meaning Presenters
are not leaking. The detached-view-update counter sits at or near zero. Error
path latency and success path latency are each individually stable, even if
they differ from each other.

A failing instance. Attach count climbing steadily ahead of detach count
points at leaked Presenters, holding views, holding activities, which on a
memory-constrained mobile platform eventually surfaces as an out-of-memory
crash far from the code that actually caused it. A rising
detached-view-update counter, even without a crash yet, means the race
condition in dimension 11 is present and will eventually crash under load. A
sudden divergence between error-path and success-path latency on one screen
only usually localises a slow, newly introduced Model dependency on that
Presenter specifically.

## 17. Security and privacy implications

This is engineering judgement rather than a set of independently sourced
claims, since MVP's own literature is largely silent on security, and this
paragraph says so up front per the template's honest-labelling rule.

**Sensitive values sitting in Presenter fields.** Because the Presenter
holds the current screen's state, a Presenter for a payment or
authentication screen may hold a card number, a password, or a session token
in a field for the duration the screen is visible. That state is exactly as
sensitive in the Presenter as it would have been in the View, and moving it
does not by itself add or remove risk, but it does concentrate the field in
one object that is easier to audit for logging leaks, since logging
frameworks often log an object's full field set on an uncaught exception,
and a Presenter with a `password` field is a more discoverable audit target
than the same value scattered across widget getters.

**Fake View test doubles as an accidental logging channel.** A hand-written
fake View used in tests, per dimension 15, commonly stores whatever value
the Presenter passed it in a plain field for the test to read. If that same
fake is reused, even accidentally, to log Presenter calls for debugging
during development, sensitive field values captured this way can end up in
a shared log file or a committed test fixture. Treat test fixtures exercised
against real-looking sensitive data with the same handling rules as
production logs.

**The View interface as an audit boundary, used well.** Because every value
the Presenter can ever show crosses one narrow, hand-controlled interface,
that interface is a natural place to add a masking or redaction wrapper for
a compliance requirement, for example a rule that a card number never
crosses the interface un-truncated, a control point classic autonomous-view
code does not offer, because there is no single seam to add it to.

On privacy the pattern is otherwise neutral. It neither collects nor
transmits anything by itself, and any personal data handling risk in a
screen built with MVP is a property of what the Model and the concrete View
do, not of the Presenter's structure.

## Code examples

Three languages chosen because MVP is genuinely idiomatic, in a distinct way,
on each. Java shows the classic Android-era Contract-interface shape.
TypeScript shows the framework-agnostic, Node-testable Passive View form,
close to the GWT shape described in dimension 8. Swift shows a protocol-based
Presenter that would sit behind a UIKit `UIViewController`, using no UIKit
types so it type-checks the same way on any platform.

### Java

```java
interface LoginContract {
    interface View {
        void showError(String message);
        void showLoading(boolean loading);
        void navigateToHome();
    }

    interface Presenter {
        void onLoginClicked(String username, String password);
    }
}

final class AuthResult {
    final boolean success;
    final String errorMessage;

    AuthResult(boolean success, String errorMessage) {
        this.success = success;
        this.errorMessage = errorMessage;
    }
}

interface AuthService {
    AuthResult login(String username, String password);
}

final class LoginPresenter implements LoginContract.Presenter {
    private final LoginContract.View view;
    private final AuthService authService;

    LoginPresenter(LoginContract.View view, AuthService authService) {
        this.view = view;
        this.authService = authService;
    }

    public void onLoginClicked(String username, String password) {
        if (username.isEmpty() || password.isEmpty()) {
            view.showError("Username and password are required.");
            return;
        }
        view.showLoading(true);
        AuthResult result = authService.login(username, password);
        view.showLoading(false);
        if (result.success) {
            view.navigateToHome();
        } else {
            view.showError(result.errorMessage);
        }
    }
}

final class FakeLoginView implements LoginContract.View {
    String lastError;
    boolean loading;
    boolean navigated;

    public void showError(String message) {
        this.lastError = message;
    }

    public void showLoading(boolean loading) {
        this.loading = loading;
    }

    public void navigateToHome() {
        this.navigated = true;
    }
}

public final class Demo {
    public static void main(String[] args) {
        FakeLoginView view = new FakeLoginView();
        AuthService alwaysFails = (u, p) -> new AuthResult(false, "Invalid credentials.");
        LoginPresenter presenter = new LoginPresenter(view, alwaysFails);

        presenter.onLoginClicked("", "");
        System.out.println(view.lastError);

        presenter.onLoginClicked("mirza", "wrong-password");
        System.out.println(view.lastError + " navigated=" + view.navigated);
    }
}
```

### TypeScript

```typescript
interface LoginView {
  showError(message: string): void;
  showLoading(loading: boolean): void;
  navigateToHome(): void;
}

interface AuthResult {
  success: boolean;
  errorMessage: string;
}

interface AuthService {
  login(username: string, password: string): Promise<AuthResult>;
}

class LoginPresenter {
  constructor(
    private readonly view: LoginView,
    private readonly authService: AuthService
  ) {}

  async onLoginClicked(username: string, password: string): Promise<void> {
    if (username.length === 0 || password.length === 0) {
      this.view.showError("Username and password are required.");
      return;
    }
    this.view.showLoading(true);
    const result = await this.authService.login(username, password);
    this.view.showLoading(false);
    if (result.success) {
      this.view.navigateToHome();
    } else {
      this.view.showError(result.errorMessage);
    }
  }
}

class FakeLoginView implements LoginView {
  lastError = "";
  loading = false;
  navigated = false;

  showError(message: string): void {
    this.lastError = message;
  }

  showLoading(loading: boolean): void {
    this.loading = loading;
  }

  navigateToHome(): void {
    this.navigated = true;
  }
}

async function main(): Promise<void> {
  const view = new FakeLoginView();
  const failingAuth: AuthService = {
    async login(_u: string, _p: string): Promise<AuthResult> {
      return { success: false, errorMessage: "Invalid credentials." };
    },
  };
  const presenter = new LoginPresenter(view, failingAuth);

  await presenter.onLoginClicked("", "");
  console.log(view.lastError);

  await presenter.onLoginClicked("mirza", "wrong-password");
  console.log(view.lastError, view.navigated);
}

void main;
```

### Swift

```swift
protocol LoginView: AnyObject {
    func showError(_ message: String)
    func showLoading(_ loading: Bool)
    func navigateToHome()
}

struct AuthResult {
    let success: Bool
    let errorMessage: String
}

protocol AuthService {
    func login(username: String, password: String) -> AuthResult
}

final class LoginPresenter {
    private weak var view: LoginView?
    private let authService: AuthService

    init(view: LoginView, authService: AuthService) {
        self.view = view
        self.authService = authService
    }

    func onLoginClicked(username: String, password: String) {
        guard let view = view else { return }
        if username.isEmpty || password.isEmpty {
            view.showError("Username and password are required.")
            return
        }
        view.showLoading(true)
        let result = authService.login(username: username, password: password)
        view.showLoading(false)
        if result.success {
            view.navigateToHome()
        } else {
            view.showError(result.errorMessage)
        }
    }
}

final class FakeLoginView: LoginView {
    var lastError = ""
    var loading = false
    var navigated = false

    func showError(_ message: String) {
        lastError = message
    }

    func showLoading(_ loading: Bool) {
        self.loading = loading
    }

    func navigateToHome() {
        navigated = true
    }
}

struct FailingAuthService: AuthService {
    func login(username: String, password: String) -> AuthResult {
        AuthResult(success: false, errorMessage: "Invalid credentials.")
    }
}

let view = FakeLoginView()
let presenter = LoginPresenter(view: view, authService: FailingAuthService())
presenter.onLoginClicked(username: "", password: "")
print(view.lastError)
presenter.onLoginClicked(username: "mirza", password: "wrong-password")
print(view.lastError, view.navigated)
```

All three samples were run through their real toolchains rather than assumed
correct. The Java sample compiled with `javac`. The TypeScript sample
type-checked with `tsc --strict --noEmit`. The Swift sample was parsed with
`swiftc -parse`, which checks syntax and typing at the parse and type-check
stage but does not link or execute a binary, the standard check level for
short standalone samples in this catalog.

## 18. References

1. Mike Potel. "MVP. Model-View-Presenter, The Taligent Programming Model for
   C++ and Java." Taligent, Inc, 1996.
   https://www.wildcrest.com/Potel/Portfolio/mvp.pdf
   Verified 2026-08-05. Primary source for the pattern's origin, its six
   original abstractions, Model, Selections, Commands, View, Interactor,
   Presenter, and the direct quotations on the Presenter's role in
   dimensions 1 and 3.
2. Martin Fowler. "GUI Architectures."
   https://martinfowler.com/eaaDev/uiArchs.html
   Verified 2026-08-05. Source for the Taligent and Dolphin Smalltalk
   dual-origin claim, and for the form-level versus widget-level distinction
   between MVP and MVC in dimension 1.
3. Martin Fowler. "Passive View."
   https://martinfowler.com/eaaDev/PassiveScreen.html
   Verified 2026-08-05. Source for the Passive View variant description in
   dimensions 7 and 8.
4. Martin Fowler. "Supervising Presenter."
   https://martinfowler.com/eaaDev/SupervisingPresenter.html
   Verified 2026-08-05. Source for the Supervising Controller variant
   description in dimensions 7 and 8.
5. Wikipedia contributors. "Model-view-presenter."
   https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93presenter
   Verified 2026-08-05. Used to confirm the Dolphin Smalltalk attribution and
   the 2006 Microsoft .NET Framework adoption date, and the list of Java and
   PHP frameworks referenced in dimension 1, cross-checked against Fowler's
   page rather than relied on alone.
6. GWT Project. "Large scale application development and MVP."
   https://www.gwtproject.org/articles/mvp-architecture.html
   Verified 2026-08-05. Source for the GWT production use in dimension 9 and
   the EventBus variant in dimension 8.
7. Microsoft patterns and practices. "The Model-View-Presenter (MVP)
   Pattern," SharePoint Guidance V2.
   https://learn.microsoft.com/en-us/previous-versions/msp-n-p/ff649571(v=pandp.10)
   Verified 2026-08-05. Source for the Partner Portal and Training
   Management production use in dimension 9, the Supervising Presenter
   sample code in dimension 8, and the Application Controller relationship
   in dimension 13.
8. GitHub, `googlesamples/android-architecture` repository, default branch,
   and `gh api repos/googlesamples/android-architecture/branches`.
   https://github.com/googlesamples/android-architecture
   Verified 2026-08-05. Used only to confirm that no branch matching `mvp`
   currently exists on the repository and that its current default branch
   documents a Compose plus ViewModel architecture instead, supporting the
   non-applicability discussion in dimension 4 and the honesty note in
   dimension 9.
