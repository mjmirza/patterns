---
name: Model View ViewModel
slug: model-view-viewmodel
family: 05-architectural
category: Architectural
aliases: [MVVM, Presentation Model, Application Model]
first_described: "Fowler 2004 (Presentation Model), Gossman 2005 (MVVM name)"
maturity: canonical
related: [observer, mediator, command, facade, front-controller]
incompatible_with: [model-view-controller]
verified: 2026-08-02
---

# Model View ViewModel

## 1. Name, aliases, and lineage

The canonical name is Model View ViewModel, almost always written MVVM. The
pattern has two independent lineages that converged on the same shape under
different names, and a master-level treatment has to keep both straight
because practitioners cite either one depending on which platform they came
from.

The first lineage is Martin Fowler's Presentation Model, published as part of
his ongoing Enterprise Application Architecture writing on 19 July 2004. Fowler
describes it as pulling "the state and behavior of the presentation independent
of the GUI controls used in the interface", so that a presentation model class
can be fully unit tested without a running UI, and the actual GUI becomes a
thin, mostly declarative binding target for that class
([Martin Fowler, Presentation Model](https://martinfowler.com/eaaDev/PresentationModel.html),
verified 2026-08-02). Fowler's own page states plainly that the pattern is "now
increasingly known as MVVM", which is the primary source for treating
Presentation Model and MVVM as the same pattern under two names rather than as
two related but distinct patterns.

The second lineage is John Gossman's blog post of 8 October 2005, written while
he was a Microsoft architect working on the WPF UI framework (then codenamed
Avalon) and its design tool Sparkle. Gossman coined the name Model/View/
ViewModel explicitly as "a variation of Model/View/Controller (MVC) that is
tailored for modern UI development platforms where the View is the
responsibility of a designer rather than a classic developer", built on top of
a "general mechanism for data binding" that WPF supplied natively
([John Gossman, Introduction to Model/View/ViewModel pattern for building WPF
apps](https://learn.microsoft.com/en-us/archive/blogs/johngossman/introduction-to-modelviewviewmodel-pattern-for-building-wpf-apps),
verified 2026-08-02, archived Microsoft post dated 2005-10-08). Gossman's
original post already names the ViewModel's two jobs precisely. It is "Model of
a View", an abstraction of what the view needs, and it is "a specialization of
the Model that the View can use for data-binding", exposing data transformers
and Commands. Both jobs recur in every serious implementation since.

A third name that shows up in older .NET material is Application Model, used
interchangeably with ViewModel in some early Silverlight and WPF community
writing from 2006 to 2009, though it never displaced ViewModel as the settled
term and is mentioned here only because a reader researching period sources
will encounter it.

## 2. Problem and context

A user interface has three kinds of code tangled together whenever it is built
without a discipline. The raw visual layout and control wiring, the logic that
decides what the screen should currently show, and the domain data and rules
the screen is a window onto. When these three live in one class, that class
grows in every direction at once. A button click handler mutates a label's
text, reads a domain object, formats a number for display, and enables another
control, all in a few lines, and none of it can be exercised without
instantiating the actual UI control tree.

The problem gets sharper on platforms that split UI authoring across two
different tools and, often, two different people. WPF's XAML, Android's
Compose or XML layouts, and the browser's HTML and templating engines are all
declarative surfaces meant to be edited by a UI-focused developer or designer
using a visual tool, while the domain and application logic is written by a
developer in an imperative language. Gossman's original framing is specific
about this. MVVM exists because "the View is the responsibility of a designer
rather than a classic developer", and the two need a boundary they can each
work up to without stepping on the other ([Gossman
2005](https://learn.microsoft.com/en-us/archive/blogs/johngossman/introduction-to-modelviewviewmodel-pattern-for-building-wpf-apps),
verified 2026-08-02).

The other half of the context is data binding. MVVM only earns its keep when
the platform, or a library layered on top of it, can observe a property on one
object and automatically push its new value into a bound control, and observe
a control's user edit and automatically push it back into a property, without
either side writing that plumbing by hand. WPF had this built in from the
start through `INotifyPropertyChanged` and the binding engine. Knockout.js
brought the same idea to the browser through observables and a `data-bind`
attribute a few years later. SwiftUI brought it to Apple platforms through
`ObservableObject` and `@Published`. Where a platform has no first-class
binding mechanism, MVVM degrades into a naming convention with no automatic
synchronization, and a different pattern, often plain MVC or MVP with explicit
update calls, fits the platform better.

## 3. Forces

This is engineering judgement rather than a sourced claim. The forces below
are how MVVM is usually justified and where its cost actually lands, drawn
from the shape of the pattern itself and from the objc.io critique cited in
section 11, not from a single named source enumerating them.

- **Testability versus indirection.** Pulling presentation logic into a
  ViewModel that has no reference to any UI control makes that logic testable
  with a plain unit test, no UI test rig, no rendering, no simulator. The
  cost is an extra layer between the view and the model that a reader has to
  trace through, and a ViewModel whose only job in a given screen is to
  re-expose model data unchanged is pure ceremony.
- **Designer and developer parallelism versus discoverability.** Splitting the
  visual layer from the logic layer lets a UI-focused person and a
  logic-focused person work the same screen in parallel through the binding
  contract. The cost is that the binding contract itself, which property binds
  to which control, is often invisible to static analysis. A renamed
  ViewModel property that is only referenced from a string-keyed binding in a
  markup file compiles cleanly and fails at runtime.
- **Declarative synchronization versus binding cost.** Automatic two-way
  binding removes the largest single source of manual UI-update bugs, the
  screen showing stale data because a developer forgot one update call site.
  It costs a runtime observation mechanism, whether that is dirty checking,
  property-changed events, or a reactive graph, and that mechanism has its own
  performance profile that a raw, hand-wired update call does not.
- **Reuse across views versus over-abstraction.** A ViewModel with no
  reference to any concrete view type can, in principle, back more than one
  view of the same data. In practice most ViewModels are built for exactly one
  screen and the reuse rarely materializes, so treating reusability as the
  headline justification for adding a ViewModel to a trivial screen is usually
  wrong.
- **Command indirection versus direct calls.** Routing every user action
  through a Command object (`ICommand`, a Kotlin lambda-backed action, a
  Combine `.send` closure) instead of a direct method call gives the view a
  uniform, bindable surface for enabling and disabling controls based on
  application state. It costs an extra object per action, and a screen with
  many small actions accumulates a matching pile of Command wrappers.

## 4. Applicability and non-applicability

Reach for MVVM when the platform has genuine two-way or reactive data binding
and the screen has real presentation logic worth isolating. Derived,
formatted, or filtered state, enable and disable rules tied to more than one
piece of state, validation feedback that has to update as the user types,
or a screen complex enough that a plain unit test of its behaviour is worth
having. It also fits well when a single ViewModel genuinely needs to drive
more than one presentation, for example the same underlying selection state
shown as a list in one panel and a detail view in another, which is the exact
case Gossman uses selection for in his original post.

Do not reach for MVVM in these cases, and the reasons matter more than the
list itself.

- **The platform has no data binding mechanism.** Without observable
  properties and an automatic sync path, a ViewModel is just a second copy of
  the model with hand-written update calls duplicated in both directions,
  which is strictly more code than calling the model directly from the view
  and is not the pattern, only its name.
- **The screen is a pass-through of the model with no derived state.** A
  detail screen that shows a record's fields verbatim, with no formatting,
  filtering, or validation, gains nothing from a ViewModel layer between it
  and the model. Fowler is explicit that Presentation Model is for screens
  where the view "can't easily be data bound to the domain model" as-is
  ([Fowler](https://martinfowler.com/eaaDev/PresentationModel.html), verified
  2026-08-02). When it can, skip the layer.
- **The team cannot maintain binding discipline.** Because most binding
  systems resolve property names as strings or through generated code the IDE
  does not always cross-reference cleanly, a team unfamiliar with the
  platform's binding tooling will accumulate silent runtime binding failures
  faster than they accumulate the testability benefit.
- **The application is not interactive UI at all.** A batch job, a CLI tool,
  or a server that renders no persistent, stateful screen has no view to bind
  to and no reason to introduce a ViewModel. This is worth stating because
  MVVM is sometimes proposed by habit for any layer that happens to sit
  between data and output.
- **A single, short-lived component with trivial state.** A button that
  toggles its own highlighted state on click does not need a dedicated
  ViewModel object. Component-local state in the view is the right amount of
  machinery, and manufacturing a ViewModel class for it is the over-abstraction
  failure named in section 11.

## 5. Structure

- **Model.** The domain data and business logic, with no reference to any UI
  type, control, or framework. Gossman's post is explicit that this is defined
  exactly as in MVC and is "completely UI independent"
  ([Gossman 2005](https://learn.microsoft.com/en-us/archive/blogs/johngossman/introduction-to-modelviewviewmodel-pattern-for-building-wpf-apps),
  verified 2026-08-02). The Model is frequently code the ViewModel's author
  does not own, such as a generated data-access layer, a pre-existing domain
  library, or a remote API client.
- **View.** The visual surface. XAML, a SwiftUI `View` struct, an Android
  Compose function, or an HTML template with `data-bind` attributes. The View
  binds to properties and commands exposed by the ViewModel and, in a
  correctly built MVVM screen, contains no logic beyond what the binding
  language itself expresses (a format string, a visibility trigger, a simple
  conditional). The View holds a reference to its ViewModel; the ViewModel
  never holds a reference to its View.
- **ViewModel.** The binding target and command surface for exactly one View.
  It exposes view-ready state, meaning state already shaped, formatted, and
  filtered the way the view needs to display it, as observable properties, and
  it exposes user-initiated operations as Commands rather than as plain
  methods the view calls imperatively. Internally it holds a reference to the
  Model (or to a service that mediates access to it) and translates Model
  changes into observable-property updates, and translates Command invocations
  into Model mutations.
- **Binder.** The platform mechanism that keeps View and ViewModel
  synchronized. WPF's binding engine reading `INotifyPropertyChanged`, Android
  Data Binding or `StateFlow` collection in a Compose composable, SwiftUI's
  `@StateObject`/`@ObservedObject` subscribing to `ObservableObject`, or a
  library like Knockout evaluating `data-bind` attributes against observables.
  The Binder is not a class either the View or the ViewModel author writes; it
  is supplied by the platform or a library, and its presence or absence is
  what decides whether MVVM is applicable at all, per section 4.

## 6. ASCII structure diagram

```text
+-------------------+       binds to        +--------------------+
|        View        | ---------------------> |    ViewModel       |
|  (XAML / SwiftUI /  |   observable props     |  view-ready state  |
|   Compose / HTML)   |   + commands           |  + commands        |
|                     | <--------------------- |                    |
+---------+-----------+   change notifications  +---------+----------+
          |                (via the Binder)               |
          | never references                               | references
          v                                                 v
   (no direct link)                              +--------------------+
                                                  |       Model         |
                                                  |  domain data/logic  |
                                                  |  no UI awareness    |
                                                  +--------------------+

              +-----------------------------------------+
              |          Binder (platform-supplied)       |
              |  INotifyPropertyChanged / Combine /        |
              |  StateFlow / Knockout observables           |
              +-----------------------------------------+
                 subscribes View <-> ViewModel automatically
```

## 7. Dynamics

```text
User edits a bound control in the View
        |
        v
Binder writes the new value into the corresponding
ViewModel property (two-way binding case)
        |
        v
ViewModel property setter runs, may invoke Model logic
directly, or the View instead triggers a Command
        |
        v
ViewModel calls into the Model (query or mutation)
        |
        v
Model returns updated domain state / raises its own
change notification if it has one
        |
        v
ViewModel recomputes its view-ready observable
properties from the new Model state
        |
        v
ViewModel raises a property-changed notification
(INotifyPropertyChanged, @Published sink, StateFlow
emission, Knockout observable write)
        |
        v
Binder reads the new ViewModel property value and
pushes it into every bound control in the View
        |
        v
View re-renders the affected controls only, with
no code in the View deciding what changed
```

The one-way flavor, used for read-only displays and for platforms favoring
unidirectional data flow such as current Android Compose guidance, drops the
first two steps. The View never writes back into the ViewModel directly, and
all mutation happens through explicit Commands or event callbacks that the
View invokes, keeping data flowing from ViewModel to View in only one
direction while events flow from View to ViewModel in the other, which is the
Unidirectional Data Flow principle described in Google's Android architecture
guidance ([Android Developers, App architecture
guide](https://developer.android.com/topic/architecture), verified 2026-08-02).

## 8. Implementation variants

- **Two-way property binding (classic WPF/.NET).** The ViewModel implements
  `INotifyPropertyChanged`, raising `PropertyChanged` on every setter. XAML
  bindings default to `TwoWay` mode for editable controls, so a `TextBox`
  bound to a string property both displays and edits it with zero manual
  synchronization code. Commands implement `ICommand`, exposing `CanExecute`
  so bound buttons enable and disable themselves automatically.
- **Source-generated boilerplate reduction (.NET, current).** The Microsoft
  .NET Community Toolkit's `CommunityToolkit.Mvvm` package supplies
  `ObservableObject` as a base class plus `[ObservableProperty]` and
  `[RelayCommand]` attributes that a Roslyn source generator expands into the
  full `INotifyPropertyChanged` and `ICommand` boilerplate at compile time,
  removing the hand-written property-changed code entirely while keeping the
  same runtime binding contract ([Microsoft Learn, Introduction to the MVVM
  Toolkit](https://learn.microsoft.com/en-us/dotnet/communitytoolkit/mvvm/),
  verified 2026-08-02).
- **Declarative observable binding (JavaScript, Knockout.js).** The ViewModel
  is a plain object whose fields are `ko.observable()` wrappers. The View is
  ordinary HTML annotated with `data-bind` attributes, and `ko.applyBindings`
  walks the DOM once, wiring each annotated element to the matching
  observable. Knockout's own introduction frames this explicitly as MVVM
  applied through "declarative bindings" and "elegant dependency tracking"
  ([Knockout.js,
  Introduction](https://knockoutjs.com/documentation/introduction.html),
  verified 2026-08-02).
- **Reactive publisher binding (Swift, Combine and SwiftUI).** The ViewModel
  conforms to `ObservableObject`. Each bindable field is marked `@Published`,
  which synthesizes a `Combine.Publisher` that fires on every mutation.
  SwiftUI views declare `@StateObject` (when they own the ViewModel's
  lifetime) or `@ObservedObject` (when a parent owns it) and the view body
  re-evaluates automatically whenever any `@Published` property the body reads
  changes, with no manual subscription code required inside the view.
- **Unidirectional state-holder binding (Kotlin, Android Jetpack).**
  The ViewModel exposes a single immutable `UiState` data class wrapped in a
  `StateFlow`, rather than many independent bindable properties. The View
  (a Compose composable) collects that `StateFlow` with
  `collectAsStateWithLifecycle()` and re-composes on every emission; all
  mutation happens through explicit functions the View calls, never through
  two-way binding. Google's own architecture guidance frames this as the
  ViewModel acting as a state holder inside a broader Unidirectional Data Flow
  discipline rather than classic two-way MVVM binding
  ([Android Developers, ViewModel
  overview](https://developer.android.com/topic/libraries/architecture/viewmodel),
  verified 2026-08-02).
- **ViewModel-first composition (Caliburn.Micro and similar).** A convention-
  over-configuration framework resolves the View for a given ViewModel type
  by naming convention, so application code never instantiates a View
  directly. This inverts the more common view-first flow (View is created,
  View's `DataContext` is set to a ViewModel) and pushes navigation and screen
  activation logic entirely into ViewModel-level code.

## 9. Known production uses

- **Windows Presentation Foundation and the Sparkle design tool at
  Microsoft.** MVVM was coined for and first used inside WPF's own tooling; the
  Library, Appearance, and Project panels in Sparkle are the worked examples
  in Gossman's original post, each with its Model, View, and ViewModel
  identified concretely ([Gossman
  2005](https://learn.microsoft.com/en-us/archive/blogs/johngossman/introduction-to-modelviewviewmodel-pattern-for-building-wpf-apps),
  verified 2026-08-02).
- **The Microsoft Store app on Windows.** The .NET Community Toolkit's MVVM
  package documentation states it "is also used by several first party
  applications that are built into Windows, such as the Microsoft Store"
  ([Microsoft Learn, Introduction to the MVVM
  Toolkit](https://learn.microsoft.com/en-us/dotnet/communitytoolkit/mvvm/),
  verified 2026-08-02), citing the Windows blog's account of the Store's
  rebuild for Windows 11.
- **Knockout.js in production web applications.** Knockout shipped MVVM as its
  central organizing model for the browser starting in 2010 and documents
  observables and declarative `data-bind` bindings as its two headline
  mechanisms for keeping a JavaScript view model synchronized with the DOM
  ([Knockout.js,
  Introduction](https://knockoutjs.com/documentation/introduction.html),
  verified 2026-08-02).
- **SwiftUI applications across Apple's platform documentation and the wider
  iOS ecosystem.** Apple's `ObservableObject` and `@Published` combination is
  the standard, first-party binding mechanism SwiftUI ships with specifically
  to let a Combine-based ViewModel drive a SwiftUI View's re-rendering, and it
  is the default pattern taught in Apple's own SwiftUI sample code and
  documentation for any screen with non-trivial state.
- **Android apps built on Jetpack Architecture Components.** Google ships
  `androidx.lifecycle.ViewModel` as first-party infrastructure specifically so
  that screen state survives configuration changes such as rotation without
  being refetched, and frames current Compose-based apps around ViewModel
  state holders feeding Unidirectional Data Flow, per Google's own
  architecture and ViewModel documentation ([Android Developers, ViewModel
  overview](https://developer.android.com/topic/libraries/architecture/viewmodel);
  [Android Developers, App architecture
  guide](https://developer.android.com/topic/architecture), both verified
  2026-08-02).

## 10. Consequences

**Positive.**

- Presentation logic becomes independently unit-testable without a UI test
  rig, because the ViewModel holds no reference to any concrete view
  control, only to observable state and commands.
- Designer-authored, declarative view markup and developer-authored logic can
  be worked on in parallel against a stable binding contract, which is the
  reason Gossman gives for coining the pattern in the first place.
- Automatic, bidirectional synchronization between displayed state and
  underlying data removes an entire class of "screen shows stale data" bugs
  that hand-wired manual update code is prone to.
- A single ViewModel can, when genuinely needed, back more than one View of
  the same underlying selection or state, avoiding duplicated coordination
  logic across those views.
- Commands give the view a uniform way to reflect whether an action is
  currently valid, through `CanExecute` or an equivalent, without the view
  itself encoding that business rule.

**Negative.**

- The extra layer adds indirection a reader has to trace through even for
  simple screens, and a screen that only re-displays model fields unchanged
  pays that cost for no benefit.
- Binding is frequently resolved by name at runtime, whether through XAML
  string paths, Knockout's `data-bind` HTML attributes, or a Compose state
  read the compiler cannot statically connect back to its producer. A renamed
  or removed ViewModel property is a silent runtime failure rather than a
  compile error on several implementations.
- ViewModels tend to accumulate state and logic that was originally specific
  to the view and gradually absorbs application and even domain logic, the
  same "God object" failure MVVM was meant to prevent at the view-controller
  layer, now recurring one layer over. This is the "massive view model"
  problem named explicitly in the iOS architecture literature (section 11).
- The Command pattern adds one object per user action; a screen with many
  fine-grained actions accumulates a matching pile of small Command classes
  or lambda-backed command properties.
- Testing the ViewModel in isolation proves the ViewModel's logic is correct
  but proves nothing about the binding wiring itself. A broken binding path
  between a correct View and a correct ViewModel is invisible to both the
  ViewModel's unit tests and, on many platforms, to the compiler.

## 11. Failure modes and misuse

- **Symptom.** A screen displays stale or blank data for one specific field
  after a refactor, while everything else on the screen updates correctly.
  **Cause.** The binding path (a XAML `{Binding PropertyName}`, a Knockout
  `data-bind="text: propertyName"`, a manually mistyped `@Published` name
  reference) still references the old property name after a rename, and the
  binding engine fails silently rather than throwing a compile error.
  **Fix.** Use a compile-time-checked binding mechanism where the platform
  offers one (Compose's direct property references, source-generated
  `[ObservableProperty]` in the .NET toolkit, Swift's `$propertyName`
  publisher syntax checked by the compiler), and where string-keyed binding is
  unavoidable, enable the platform's binding-failure trace output during
  development and treat a binding warning as a build-breaking signal, not
  noise.

- **Symptom.** The ViewModel class for one screen has grown past a thousand
  lines, mixes network calls, validation, formatting, and navigation logic,
  and is now as hard to test in isolation as the "massive view controller" it
  was supposed to replace. **Cause.** This is the "massive view model"
  failure, and it is engineering judgement rather than a sourced fact, drawn
  from the same structural pressure Ash Furrow's objc.io piece names for the
  view-controller equivalent. Without an explicit second layer to push
  business logic into (a service, a use case, a repository), a ViewModel
  becomes the only place left to put logic once it has been pulled out of the
  View, and it absorbs everything ([objc.io, MVVM on iOS by Ash
  Furrow](https://www.objc.io/issues/13-architecture/mvvm/), verified
  2026-08-02, discussing testability and the "notoriously hard to test"
  massive view controller MVVM is meant to relieve). **Fix.** Give the
  ViewModel a Model-side collaborator (a use case, an interactor, a
  repository) for anything that is not literally "shape this data for this
  view", and keep the ViewModel to orchestration. Calling that collaborator
  and translating its result into observable, view-ready state.

- **Symptom.** A ViewModel unit test suite is fully green, but the actual
  running screen never updates when the underlying data changes. **Cause.**
  The ViewModel raises its change notification correctly (proven by the unit
  test observing the notification directly), but the View never subscribed to
  it, commonly because the View was given a fresh ViewModel instance instead
  of the one it originally bound to, or because a `@StateObject` was
  mistakenly declared as `@ObservedObject` (or the reverse) and the object's
  identity, and therefore its subscription, was lost across a re-render.
  **Fix.** Verify ViewModel-View wiring with an integration or UI test that
  drives the real binding path, not only a unit test of the ViewModel in
  isolation. Treat ViewModel unit tests and View-binding tests as two
  separate, both-required layers of coverage.

- **Symptom.** A ViewModel is instantiated fresh, and expensive, every time
  its View recomposes or re-renders, and profiling shows repeated redundant
  network or database calls on every keystroke into an unrelated text field.
  **Cause.** The ViewModel's lifetime was accidentally tied to the View's
  render lifecycle instead of to the screen's navigation lifecycle, which
  loses exactly the configuration-change survival that Android's
  `ViewModelStoreOwner` scoping and SwiftUI's `@StateObject` are specifically
  designed to provide when used correctly ([Android Developers, ViewModel
  overview](https://developer.android.com/topic/libraries/architecture/viewmodel),
  verified 2026-08-02). **Fix.** Scope the ViewModel to the screen or
  navigation destination, not to the individual composable or view render
  pass, using the platform's dedicated ViewModel-scoping mechanism rather than
  creating the ViewModel inline inside the view body.

- **Symptom.** Two screens showing what should be the same underlying data
  drift out of sync. Editing a record on one screen does not reflect on the
  other until the second screen is fully torn down and rebuilt.
  **Cause.** Each screen was given its own ViewModel holding its own private
  copy of the fetched data rather than both ViewModels observing a single
  shared source of truth in the Model layer, so the two ViewModels are
  synchronized with the same origin but never with each other.
  **Fix.** Route all reads through one Model-level Single Source of Truth
  (a repository, a shared reactive store) and have every ViewModel that needs
  the data subscribe to that source rather than caching its own private copy,
  which is the Single Source of Truth discipline Google's architecture
  guidance names explicitly for this exact failure ([Android Developers, App
  architecture guide](https://developer.android.com/topic/architecture),
  verified 2026-08-02).

## 12. Trade-off matrix

| Force | MVVM | MVC | MVP | Presentation Model without MVVM's name |
|---|---|---|---|---|
| Testability of presentation logic | High. ViewModel has no view reference and is a plain unit-testable object. | Low to medium. Controller often references view types directly, complicating isolated testing. | High. Presenter has no view reference, same as ViewModel, communicates through a narrow view interface instead of binding. | High. Same mechanism as MVVM, this is MVVM's direct ancestor and near-synonym per Fowler. |
| Requires platform data binding | Yes, and is the pattern's defining dependency. | No. Controller updates view through direct calls. | No. Presenter updates view through an explicit interface call, not binding. | Yes, same requirement as MVVM. |
| View update mechanism | Automatic, via the Binder observing property changes. | Manual, Controller calls view methods to update it. | Manual, Presenter calls interface methods on the view. | Automatic, via the Binder, identical to MVVM. |
| Designer/developer parallel work | Strong, because binding is declarative and resolved at runtime or by codegen. | Weak, view templates and controller logic are typically more entangled. | Moderate, the view interface gives a contract but updates are still explicit calls, not declarative markup. | Strong, same as MVVM. |
| Risk of a bloated middle layer | Real, the "massive view model" failure (section 11). | Real under the equivalent name, "massive view controller". | Real, presenters accumulate the same way when given no service layer. | Real, identical risk, same underlying structure as MVVM. |
| Compile-time safety of the view-logic link | Weak to moderate, depends heavily on the platform; string-keyed bindings are common and unchecked. | Strong, Controller calls are ordinary method calls the compiler checks. | Strong, Presenter calls a defined interface the compiler checks. | Weak to moderate, same binding-dependent risk as MVVM. |

## 13. Related and incompatible patterns

MVVM is a direct structural descendant of the Observer pattern. Every binding
mechanism described in section 8, `INotifyPropertyChanged`, Combine
publishers, Knockout observables, `StateFlow`, is an Observer implementation
specialized for UI property change notification, and a reader who does not
understand Observer will not understand why MVVM's binding step works at all.

MVVM composes closely with Command, since the ViewModel's user-triggered
operations are conventionally exposed as Command objects (`ICommand`,
`RelayCommand`, a bound lambda) rather than as plain methods the View calls
directly, giving the View a uniform way to query whether an action can
currently run. It also composes with Mediator in larger applications, where a
messaging layer such as the .NET Community Toolkit's `IMessenger` lets
ViewModels that do not directly reference each other still coordinate,
avoiding a web of direct ViewModel-to-ViewModel references.

MVVM is a sibling, not a composition partner, of Model View Presenter. Both
descend from the same "pull presentation logic out of the view" instinct that
Fowler's broader Enterprise Application Architecture writing on Presentation
Model, Passive View, and Supervising Controller documents as a family, and
choosing between MVVM and MVP is a single either-or decision for a given
screen or application, driven entirely by whether the platform gives you real
data binding (choose MVVM) or not (choose MVP, using explicit interface calls
instead).

MVVM is incompatible with, rather than merely different from, classic Model
View Controller for the same screen, because the two disagree about where the
authority to update the view lives. In MVC the Controller actively decides
when and how to update the View through direct calls; in MVVM the Binder
mediates that update automatically from a passive property change, and the
ViewModel never calls into the View. Layering both patterns onto the same
screen produces two competing update paths and is a design smell, not a valid
hybrid. This is recorded in the entry's `incompatible_with` field rather than
in the applicability list because the conflict is structural, not situational.

## 14. Refactoring path in and out

**Introducing MVVM into a screen that currently mixes view and logic code.**
Start by identifying every piece of state the view currently displays that is
not a raw, unformatted model field, meaning anything derived, formatted,
filtered, or validated. Create a ViewModel class exposing exactly that
derived state as observable properties, computed from a reference to the
existing Model or service. Move the formatting and derivation code that
currently lives inline in the view's event handlers into that ViewModel,
verified at each step by a unit test asserting the ViewModel's observable
property equals the value the old inline code used to produce. Only after the
ViewModel's state is verified correct, rewire the view's bindings to point at
the new ViewModel properties instead of at the raw model or at inline
computed expressions, and delete the corresponding inline logic from the view.
Do the same for user actions last. Wrap each action currently handled by a
direct event handler in a Command exposed by the ViewModel, and bind the
corresponding control's trigger to that Command instead of to the handler.

**Removing MVVM from a screen where it has stopped earning its place.**
This is the direction most catalogs skip, and it matters because a screen that
started complex and was later simplified, or a screen where MVVM was applied
by habit rather than need, should not carry the pattern forever by inertia.
Confirm first, using section 4's non-applicability list, that the screen now
genuinely has no derived state, no validation, and no reuse of the ViewModel
across more than one view. If so, inline the ViewModel's properties back into
direct bindings against the Model (where the platform's binding mechanism
supports binding to the Model directly, which is the same mechanism Gossman
describes for the simple, direct-bind case in his original post) and delete
the ViewModel class. Do this one property at a time, re-running the screen's
existing tests after each removal, rather than deleting the whole ViewModel in
one pass, since a property that looked unused sometimes turns out to feed a
binding elsewhere that was not obvious from the ViewModel's own code.

## 15. Testing and verification

A correctly built ViewModel is the easiest layer in the entire UI stack to
unit test, because it has no dependency on any concrete view control, window
handle, or rendering surface. Instantiate it against a fake or in-memory
Model, invoke its Commands or setters, and assert on its observable
properties' resulting values, exactly as the Swift, TypeScript, and Rust
examples in this entry do by subscribing directly to the ViewModel's
observables with no UI framework present at all.

What becomes harder is proving the View is actually wired to the ViewModel
correctly, since a binding path is frequently resolved at runtime by name and
is invisible to the ViewModel's own unit tests. This needs a second, separate
layer of coverage. A UI or integration test that drives the real rendered
view (a SwiftUI view hosted in a test rig, a Compose UI test using
`createComposeRule`, a WPF automation test, or a Knockout binding assertion
against the live DOM) and asserts that a ViewModel state change produces the
expected visible change, and that a simulated user interaction produces the
expected ViewModel state change. Skipping this second layer and trusting
ViewModel unit tests alone is exactly the failure mode described as the third
symptom in section 11.

Command objects benefit from testing their `CanExecute` or equivalent enabling
logic as a pure function of ViewModel state, independent of whether the
Command's action itself is invoked, so that enabling and disabling behaviour
is verified without needing to exercise the action's side effects.

## 16. Observability signals

A healthy MVVM screen in production shows a stable, bounded rate of
property-change notifications per user interaction. One user edit produces one
or a small, fixed number of downstream ViewModel property updates, not a
cascade. A failing instance shows either silence, meaning the ViewModel
mutated state but no corresponding change notification fired, visible as a
stale-data bug report with no matching error log, or storm, meaning a single
user interaction triggers an unbounded chain of property-changed events, often
from two observable properties whose setters each update the other, producing
either visible flicker or, on some binding implementations, a stack overflow.

Where the platform exposes it, instrument the count of active ViewModel
instances against the count of active navigable screens. A growing gap
between the two, especially one that grows monotonically over a session
rather than staying roughly proportional to visible screens, is the signature
of ViewModels leaking because their lifetime was tied to something other than
the screen's own lifecycle, the fourth failure mode in section 11. On
platforms with a garbage collector, a ViewModel retained past its screen's
navigation-away point commonly shows up first as a memory growth trend rather
than as an explicit error, since nothing throws when a ViewModel simply
outlives the screen that owned it. Correlate memory growth against navigation
event counts to catch this before it becomes a crash.

## 17. Security and privacy implications

MVVM itself is silent on security. This dimension is analytical judgement
rather than a sourced claim. The one implication worth naming concretely is
that a ViewModel is a natural place for personally identifiable or otherwise
sensitive data to accumulate in a shaped, display-ready form, distinct from
whatever redaction or access-control the Model layer applies to the raw data.
A ViewModel that formats a payment card number for display, for example, has
to independently decide how much of that number to expose, since the
formatting step happens after the Model's own access control has already
released the value. A masking or redaction rule enforced only in the Model and
not re-applied in the ViewModel's formatting logic can silently leak more of
the value than the Model's own policy intended once it passes through the
ViewModel's transformation.

The other implication is retention. Because ViewModels commonly cache a
formatted, view-ready copy of Model data for the lifetime of a screen, and
that lifetime can outlive a single user session on platforms where ViewModels
survive configuration changes or backgrounding, a ViewModel holding sensitive
data has to be explicitly cleared, not merely left to fall out of scope, on
sign-out or session-expiry, or the data persists in memory for as long as the
process itself does.

## 18. References

1. Martin Fowler, "Presentation Model", 19 July 2004, in the further Enterprise
   Application Architecture writing. https://martinfowler.com/eaaDev/PresentationModel.html
   (verified 2026-08-02).
2. John Gossman, "Introduction to Model/View/ViewModel pattern for building
   WPF apps", Microsoft blog, 8 October 2005, archived at Microsoft Learn.
   https://learn.microsoft.com/en-us/archive/blogs/johngossman/introduction-to-modelviewviewmodel-pattern-for-building-wpf-apps
   (verified 2026-08-02).
3. Microsoft Learn, "Introduction to the MVVM Toolkit", .NET Community
   Toolkit documentation, last updated 2024-11-07.
   https://learn.microsoft.com/en-us/dotnet/communitytoolkit/mvvm/
   (verified 2026-08-02).
4. Knockout.js, "Introduction" documentation page.
   https://knockoutjs.com/documentation/introduction.html
   (verified 2026-08-02).
5. Android Developers, "ViewModel overview", Jetpack Architecture Components
   documentation. https://developer.android.com/topic/libraries/architecture/viewmodel
   (verified 2026-08-02).
6. Android Developers, "App architecture guide".
   https://developer.android.com/topic/architecture
   (verified 2026-08-02).
7. Ash Furrow, "MVVM", objc.io Issue 13, Architecture.
   https://www.objc.io/issues/13-architecture/mvvm/
   (verified 2026-08-02).
8. Apple, `ObservableObject` protocol and `@Published` property wrapper,
   Combine framework documentation, used here per Apple's published Combine
   API surface for the SwiftUI binding mechanism described in sections 5 and
   8. Consult the current Apple Developer Documentation for
   `ObservableObject` for the authoritative API reference.

## Code examples

Three languages are used, chosen because each represents a genuinely distinct
production binding mechanism for MVVM rather than three copies of the same
idea. Swift with Combine's `ObservableObject`/`@Published` (the reactive
publisher variant, section 8), TypeScript with a hand-rolled observable (the
declarative, Knockout-style variant, section 8), and Rust with a hand-rolled
observable behind `Rc<RefCell<_>>` (representing the shape MVVM takes on a
platform, such as most current Rust GUI toolkits, that has no first-party
reactive binding framework and has to build the Binder by hand). Java and
Kotlin are omitted. No JDK was available in the verification environment
(`javac` reported no Java runtime installed) and Kotlin was not installed, so
neither could be compiled and run here. Kotlin's idiomatic form is documented
in section 8 and cited to Google's own architecture guidance instead of shown
as unverified code. All three examples below were compiled and executed in
this environment, and their real output is shown in the comment beneath each.

### Swift (Combine, compiled with `swiftc`, ran successfully)

```swift
import Combine
import Foundation

// Model: plain data, no UI awareness.
struct TodoItem {
    let id: UUID
    var title: String
    var isDone: Bool
}

enum TodoRepositoryError: Error {
    case notFound
}

final class TodoRepository {
    private(set) var items: [TodoItem] = [
        TodoItem(id: UUID(), title: "Write MVVM entry", isDone: false),
        TodoItem(id: UUID(), title: "Verify citations", isDone: true)
    ]

    func toggle(id: UUID) throws {
        guard let idx = items.firstIndex(where: { $0.id == id }) else {
            throw TodoRepositoryError.notFound
        }
        items[idx].isDone.toggle()
    }
}

// ViewModel: ObservableObject + @Published is the Combine binding
// mechanism a SwiftUI view subscribes to automatically.
final class TodoListViewModel: ObservableObject {
    @Published private(set) var rows: [String] = []
    @Published private(set) var remainingCount: Int = 0

    private let repository: TodoRepository

    init(repository: TodoRepository) {
        self.repository = repository
        refresh()
    }

    func toggle(id: UUID) {
        try? repository.toggle(id: id)
        refresh()
    }

    private func refresh() {
        rows = repository.items.map { item in
            (item.isDone ? "[x] " : "[ ] ") + item.title
        }
        remainingCount = repository.items.filter { !$0.isDone }.count
    }

    var firstItemID: UUID? { repository.items.first?.id }
}

// Stand-in view: subscribes the way @ObservedObject would in SwiftUI,
// proving the binding fires with no UI framework present.
let repo = TodoRepository()
let vm = TodoListViewModel(repository: repo)
var cancellables = Set<AnyCancellable>()

vm.$rows.sink { rows in
    print("view received rows:", rows)
}.store(in: &cancellables)

vm.$remainingCount.sink { count in
    print("view received remainingCount:", count)
}.store(in: &cancellables)

if let id = vm.firstItemID {
    vm.toggle(id: id)
}

// Actual output:
// view received rows: ["[ ] Write MVVM entry", "[x] Verify citations"]
// view received remainingCount: 1
// view received rows: ["[x] Write MVVM entry", "[x] Verify citations"]
// view received remainingCount: 0
```

### TypeScript (declarative observable, compiled with `tsc --strict`, ran with `node`)

```typescript
class Observable<T> {
  private value: T;
  private subscribers: Array<(v: T) => void> = [];
  constructor(initial: T) { this.value = initial; }
  get(): T { return this.value; }
  set(next: T): void {
    this.value = next;
    for (const sub of this.subscribers) sub(next);
  }
  subscribe(fn: (v: T) => void): void {
    this.subscribers.push(fn);
    fn(this.value);
  }
}

// Model: plain data, no UI concept.
interface Invoice {
  id: string;
  amountCents: number;
  paid: boolean;
}

class InvoiceStore {
  private invoices: Invoice[] = [
    { id: "INV-1", amountCents: 12000, paid: false },
    { id: "INV-2", amountCents: 5400, paid: true },
  ];
  all(): Invoice[] { return this.invoices; }
  markPaid(id: string): void {
    const inv = this.invoices.find((i) => i.id === id);
    if (inv) inv.paid = true;
  }
}

// ViewModel: view-ready state as observables, plus a command.
class InvoiceListViewModel {
  readonly rows = new Observable<string[]>([]);
  readonly outstandingTotal = new Observable<string>("$0.00");

  constructor(private readonly store: InvoiceStore) {
    this.refresh();
  }

  markPaid(id: string): void {
    this.store.markPaid(id);
    this.refresh();
  }

  private refresh(): void {
    const invoices = this.store.all();
    this.rows.set(
      invoices.map((i) => `${i.id}: ${(i.amountCents / 100).toFixed(2)} ${i.paid ? "(paid)" : "(due)"}`)
    );
    const outstanding = invoices
      .filter((i) => !i.paid)
      .reduce((sum, i) => sum + i.amountCents, 0);
    this.outstandingTotal.set(`$${(outstanding / 100).toFixed(2)}`);
  }
}

// Stand-in view: subscribes the way a template's data-bind would.
const vm = new InvoiceListViewModel(new InvoiceStore());
vm.rows.subscribe((rows) => console.log("view rows:", rows));
vm.outstandingTotal.subscribe((total) => console.log("view outstandingTotal:", total));

vm.markPaid("INV-1");

// Actual output:
// view rows: [ 'INV-1: 120.00 (due)', 'INV-2: 54.00 (paid)' ]
// view outstandingTotal: $120.00
// view rows: [ 'INV-1: 120.00 (paid)', 'INV-2: 54.00 (paid)' ]
// view outstandingTotal: $0.00
```

### Rust (hand-rolled Binder, compiled with `rustc`, ran successfully)

```rust
use std::cell::RefCell;
use std::rc::Rc;

// A minimal observable property: the Binder a Rust GUI toolkit's
// binding layer would otherwise supply. Subscribers fire on set.
struct Observable<T: Clone> {
    value: T,
    subscribers: Vec<Box<dyn Fn(&T)>>,
}

impl<T: Clone> Observable<T> {
    fn new(value: T) -> Self {
        Observable { value, subscribers: Vec::new() }
    }
    fn set(&mut self, next: T) {
        self.value = next;
        for sub in &self.subscribers {
            sub(&self.value);
        }
    }
    fn subscribe(&mut self, f: Box<dyn Fn(&T)>) {
        f(&self.value);
        self.subscribers.push(f);
    }
}

// Model: plain data, no UI concept.
#[derive(Clone)]
struct Track {
    title: String,
    liked: bool,
}

struct Library {
    tracks: Vec<Track>,
}

impl Library {
    fn new() -> Self {
        Library {
            tracks: vec![
                Track { title: "Sonata in C".into(), liked: false },
                Track { title: "Prelude in D".into(), liked: true },
            ],
        }
    }
    fn toggle_like(&mut self, index: usize) {
        if let Some(t) = self.tracks.get_mut(index) {
            t.liked = !t.liked;
        }
    }
}

// ViewModel: wrapped in Rc<RefCell<_>> so a view closure can hold a
// handle without owning the ViewModel, the shape hand-rolled Rust
// binding layers converge on absent a reactive framework.
struct TrackListViewModel {
    library: Library,
    rows: Observable<Vec<String>>,
    liked_count: Observable<usize>,
}

impl TrackListViewModel {
    fn new(library: Library) -> Rc<RefCell<Self>> {
        let vm = Rc::new(RefCell::new(TrackListViewModel {
            library,
            rows: Observable::new(Vec::new()),
            liked_count: Observable::new(0),
        }));
        TrackListViewModel::refresh(&vm);
        vm
    }

    fn toggle_like(vm: &Rc<RefCell<Self>>, index: usize) {
        vm.borrow_mut().library.toggle_like(index);
        TrackListViewModel::refresh(vm);
    }

    fn refresh(vm: &Rc<RefCell<Self>>) {
        let mut inner = vm.borrow_mut();
        let rows: Vec<String> = inner
            .library
            .tracks
            .iter()
            .map(|t| format!("{} {}", if t.liked { "L" } else { "-" }, t.title))
            .collect();
        let liked = inner.library.tracks.iter().filter(|t| t.liked).count();
        inner.rows.set(rows);
        inner.liked_count.set(liked);
    }
}

fn main() {
    let vm = TrackListViewModel::new(Library::new());

    vm.borrow_mut().rows.subscribe(Box::new(|rows: &Vec<String>| {
        println!("view rows: {:?}", rows);
    }));
    vm.borrow_mut().liked_count.subscribe(Box::new(|count: &usize| {
        println!("view liked_count: {}", count);
    }));

    TrackListViewModel::toggle_like(&vm, 0);
}

// Actual output:
// view rows: ["- Sonata in C", "L Prelude in D"]
// view liked_count: 1
// view rows: ["L Sonata in C", "L Prelude in D"]
// view liked_count: 2
```
