---
name: VIPER
slug: viper
family: 05-architectural
category: Architectural
aliases: []
first_described: "Gilbert, Stoll (Mutual Mobile) 2014"
maturity: established
related: [model-view-presenter, model-view-controller, clean-architecture, mediator, observer, command, repository]
incompatible_with: []
verified: 2026-08-02
---

# VIPER

## 1. Name, aliases, and lineage

VIPER is a backronym for View, Interactor, Presenter, Entity, and Router. It
was described by Jeff Gilbert and Conrad Stoll, engineers at the mobile
consultancy Mutual Mobile, in an article published in objc.io Issue 13,
"Architecting iOS Apps with VIPER", June 2014
(<https://www.objc.io/issues/13-architecture/viper/>, verified 2026-08-02).
The article states the pattern's origin plainly, saying Mutual Mobile
"developed a set of principles and a way of thinking about application
architecture that we call VIPER," built on the observation that writing
tests for their iOS apps had become difficult, and that a stronger
separation of layers would fix that.

Mutual Mobile also published an earlier standalone announcement of the same
pattern on its own engineering blog. That original page no longer resolves.
The company was absorbed into Grid Dynamics and its old blog domain now
redirects to a merger notice, checked directly at
<https://www.mutualmobile.com/posts/introducing-viper>, verified dead
2026-08-02. The objc.io article, written by the same two engineers who
introduced the pattern, is the durable primary source and is treated as such
throughout this entry.

The pattern descends directly from Robert C. Martin's Clean Architecture, an
architecture built around one dependency rule, stated by Martin himself as
"source code dependencies can only point inwards" and that "nothing in an
inner circle can know anything at all about something in an outer circle"
(Martin, "The Clean Architecture", 13 August 2012,
<https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html>,
verified 2026-08-02). VIPER takes that rule and gives each of Martin's rings
a concrete iOS shape. Entities are the innermost ring, the Interactor plays
the role of a use case, and the View plus Presenter form the interface
adapter layer.

Two naming details are worth settling because sources disagree on the
surface form while agreeing on the underlying role.

The original objc.io article calls the fifth object a wireframe and says the
responsibility for routing is shared between two objects, "the Presenter,
and the wireframe." Later writers, including Bohdan Orlov's widely cited
"iOS Architecture Patterns" essay
(<https://medium.com/ios-os-x-development/ios-architecture-patterns-ecba4c38de52>,
verified 2026-08-02, describing the Router as "responsible for the segues
between the VIPER modules") and Kodeco's current VIPER tutorial
(<https://www.kodeco.com/8440907-getting-started-with-the-viper-architecture-pattern>,
verified 2026-08-02, stating "The Router handles navigation between
screens") settled on Router as the class name and kept wireframe, when it
appears at all, as an informal synonym for the same object. This entry uses
Router throughout and notes wireframe only as the historical term.

VIPER is frequently confused with two patterns that share vocabulary but are
not VIPER. Clean Swift, also called VIP, is a distinct architecture with its
own site (<https://clean-swift.com>, verified 2026-08-02) that explicitly
removes the Router. The site states a user "can continue to use segues" and
that there is "no wireframe to confuse you." Clean Swift's request and
response cycle runs View to Interactor to Presenter and back to View in one
direction, without a separate Entity layer and without VIPER's Router
object. The other frequent point of confusion is Uber's RIBs framework. Its
own README states plainly, "MVC, MVP, MVI, MVVM and VIPER are architecture
patterns. RIBs is a framework" and explains that RIBs is "short for Router,
Interactor and Builder"
(<https://github.com/uber/RIBs>, verified 2026-08-02). RIBs reuses the
Router and Interactor names and the idea of business logic driving the
screen tree, but it removes the Presenter and View from the same role split
and adds a Builder as a first-class dependency graph node, so it is a
related sibling rather than an implementation of VIPER. A reader who sees
Router or Interactor in a codebase should check which of these three
architectures is actually in play before assuming VIPER.

## 2. Problem and context

A screen in a UIKit or AppKit application tends to accumulate three kinds of
code inside one view controller, code that lays out and updates the user
interface, code that decides what should happen when the user interacts
with it, and code that talks to a network client, a database, or a domain
service to get the data the screen needs. Apple's own `UIViewController`
base class already owns the view lifecycle, so it is the path of least
resistance to add one more method to it every time a new piece of behaviour
is needed. Over the life of a real app this produces the object commonly
called a massive view controller, a class of a thousand lines or more that
mixes layout code, state machines, network calls, and analytics calls in
one file, with no seam a test can be written against.

The concrete symptom that motivated VIPER's authors was testing. A
`UIViewController` subclass is heavy to instantiate outside a running app,
it needs a window, a view hierarchy, and often a storyboard, so unit tests
against it are slow, brittle, or skipped outright. When business logic
lives inside that class, the business logic inherits the same testing
problem even though nothing about validating a form or deciding which
screen to show next actually depends on `UIKit`.

The context in which VIPER earns its cost has three parts. The app is
built from screens, or modules in VIPER's own vocabulary, that are large
enough to carry real decision logic rather than a single label and a
button. The team is large enough, or the app is long lived enough, that
more than one person will work on the same module over time and needs a
predictable place to find a given kind of code. And automated testing of
the business rules, separate from the UI, is a real requirement of the
project rather than a nice addition. Outside that context, see the
non-applicability list in dimension 4, the same five-object split becomes a
cost with no matching benefit.

## 3. Forces

Some of this dimension is engineering judgement about which force dominates
in a typical iOS team, rather than a claim any single source states
outright.

- Testability. Favoured, and this is the pattern's reason for existing. The
  Interactor holds business logic with no reference to `UIKit`, so it can
  be instantiated and exercised in a plain unit test with no simulator, no
  view hierarchy, and no storyboard.
- Separation of concerns. Favoured strongly. Bohdan Orlov's essay puts this
  plainly, writing that "undoubtedly, VIPER is a champion in distribution
  of responsibilities" among the patterns it compares
  (<https://medium.com/ios-os-x-development/ios-architecture-patterns-ecba4c38de52>,
  verified 2026-08-02). Each of the five roles has exactly one reason to
  change.
- Boilerplate and maintainability. Sacrificed. The same essay names this
  directly as the cost of the separation above, writing that engineers
  "have to write huge amount of interface for classes with very small
  responsibilities," and it compares a module built this way for too small
  a screen to "building The Empire State Building from LEGO blocks." Etsy's
  own engineering team named the identical cost when they built tooling
  around VIPER, listing "boilerplate", "retain cycles across multiple
  classes", and "cognitive overhead in understanding setup requirements" as
  the three problems their VIPERBuilder scaffolding tool was written to
  reduce (<https://github.com/etsy/VIPERBuilder>, verified 2026-08-02).
- File count and navigation cost. Sacrificed. A module that would be one
  file in MVC becomes five to seven files, View, Presenter, Interactor,
  Entity, Router, and usually two or more protocols, so a reader jumping
  between files pays a real navigation tax the first time they touch a
  module.
- Onboarding cost. Sacrificed for a new team member, favoured once the
  team already knows the shape. Every module in a VIPER codebase looks the
  same, so a developer who has learned the pattern once can predict where
  any given piece of logic lives in any module, at the price of a real
  learning curve before that predictability pays off.
- Team topology. Favoured. Because each module's five objects talk only
  through protocols, two engineers can build the View and the Interactor
  of the same module in parallel against a shared protocol, and a module
  can be reassigned between engineers without a walkthrough of the whole
  app.
- Consistency across features. Favoured. Because module assembly is
  mechanical, code generators such as Etsy's VIPERBuilder and Rambler's
  Generamba, described in dimension 9, exist specifically to keep that
  consistency without hand copying files.
- Latency and runtime cost. Close to neutral. The extra protocol calls
  between View, Presenter, Interactor, and Router cost one or two
  additional method dispatches per user action, which is not measurable
  next to layout and rendering cost on any real device.
- Memory management discipline. Sacrificed without care. Because the five
  objects hold references to each other in both directions, the Presenter
  holds the Interactor, the Interactor calls back into the Presenter, the
  module is a natural home for retain cycles unless the back references
  are declared weak, a point Etsy's own tool description raises
  explicitly.

A pattern that gave up nothing would not need naming. VIPER's price is paid
in file count, boilerplate, and a genuine memory management trap, all in
exchange for a business logic layer a test suite can reach directly.

## 4. Applicability and non-applicability

### When VIPER fits

- The screen carries real decision logic, validation rules, multiple
  network calls that must be sequenced, or state transitions that a test
  suite needs to exercise without booting the full UI.
- The team has more than one iOS engineer and needs a predictable,
  repeatable shape so any engineer can open any module and know where to
  look for a given kind of code.
- The organisation already accepts, or wants to accept, the cost of
  writing protocols for every collaborator in exchange for the ability to
  substitute a fake Interactor or a fake Router in a test without touching
  a real network or a real screen.
- The app is expected to live for years and be maintained by a changing
  roster of engineers, so the up front cost of scaffolding pays back over
  the app's life rather than over one release.
- A code generator or project template already exists inside the team, so
  the boilerplate cost from dimension 3 is paid once by the tool rather
  than by hand on every module, the way Etsy and Rambler both solved it
  for their own codebases, described in dimension 9.

### Non-applicability, when not to reach for it

- The screen is a thin display of data the app already fetched, a
  settings toggle list, a static about screen, a simple detail view with
  no validation and no branching logic. Kodeco's own VIPER tutorial builds
  its worked example around a five day trip planner precisely because a
  screen with real state and real navigation is what makes the split worth
  reading about, and a screen without that state does not need five files
  (<https://www.kodeco.com/8440907-getting-started-with-the-viper-architecture-pattern>,
  verified 2026-08-02).
- The team is one or two engineers building a short lived app, a
  prototype, or a proof of concept. The protocol boilerplate is a fixed
  cost paid before the first line of real logic is written, and a small
  team rarely recovers that cost inside a short project.
- The app already uses SwiftUI with the Observation framework end to end
  and the team wants view state to flow through `@Observable` model types
  directly. VIPER's five way protocol split was designed for `UIKit`'s
  delegate heavy, imperative view controller world; forcing it onto a
  declarative view tree usually collapses back into something closer to
  MVVM with extra ceremony, and the objc.io article itself never had to
  reconcile the pattern with a declarative UI framework because none
  existed in 2014.
- The team cannot commit to writing and maintaining the protocol contracts
  between objects. A VIPER module with no enforced protocol boundary,
  where the View reaches directly into the Interactor because "it was
  faster this time," has all of the file count cost and none of the
  testability benefit.
- Business logic genuinely does not exist for the screen in question. If
  there is no decision to unit test, the Interactor exists only to hold a
  single pass through call to a service, which is the exact "Empire State
  Building from LEGO blocks" case Orlov's essay describes.

## 5. Structure

- View. A passive display surface, in practice a `UIViewController` or
  `UIView` subclass, that renders exactly what the Presenter tells it to
  render and forwards raw user input events to the Presenter. The View
  never makes a decision and never talks to the Interactor or the Router
  directly. It depends only on a small protocol the Presenter implements,
  and it exposes its own small protocol so the Presenter can drive it
  without knowing it is talking to a real screen rather than a test
  double.
- Presenter. The coordination point of the module. It receives events from
  the View, translates them into calls on the Interactor, receives the
  Interactor's result, formats that result into whatever plain values the
  View needs, and asks the Router to change screens when the use case
  finishes. The Presenter is UI framework independent in the sense that it
  never imports `UIKit` types like `UIColor` or `UIImage` into its own
  reasoning, even though the concrete View it talks to does.
- Interactor. Holds the business logic for exactly one use case, or a
  small family of closely related use cases. The objc.io article puts it
  directly, "the Interactor contains pure logic that is independent of any
  UI." It reads and writes Entities, calls out to services such as a
  network client or a persistence layer through their own protocols, and
  reports success or failure back to the Presenter through a delegate
  style callback protocol, never by returning a value the Presenter waits
  on synchronously, because most of that work is asynchronous.
- Entity. A plain data object, the domain data the Interactor works with.
  The objc.io article and Orlov's essay are both explicit that an Entity
  is not the same thing as a Core Data managed object or a network
  response model, it is the domain's own shape, decoupled from how that
  data arrived or how it will be stored.
- Router. Owns navigation. It knows how to construct the next module, its
  View, Presenter, Interactor, and Entity together, and how to present it,
  whether by pushing a view controller, presenting it modally, or swapping
  a container's child. The objc.io article's own description splits this
  work between the Presenter, which decides that a transition should
  happen, and the wireframe, the article's own name for the Router, which
  knows how to perform it and often also assembles the destination
  module.
- Module assembler, sometimes called a Builder or a Configurator. Not one
  of the five backronym letters, but present in almost every real
  implementation, including the worked example in dimension 6. A small
  factory function or type that constructs the View, Presenter,
  Interactor, Router, and any services, and wires them to each other
  before handing the finished View back to whoever needs to display it.
  Without this object the five collaborators would each need to know how
  to build the others, which reintroduces the coupling the pattern exists
  to remove.

## 6. ASCII structure diagram

```
                     +----------------------------------------+
                     |             Module Assembler            |
                     |   builds and wires the five objects     |
                     +--------------------+---------------------+
                                          | builds all of
                                          v
   input events            +-----------+          async result
+----------+ -----------> |           | -----------> +------------+
|   View   |               | Presenter |               | Interactor |
| (passive)| <----------- |  (module   | <----------- | (use case  |
+----------+  display()   |   logic)   |  success/     |  logic)    |
                            +-----------+   failure     +------------+
                              |     ^                        |
                       route()|     | screenData      reads/writes
                              v     |                        v
                            +-----------+               +----------+
                            |  Router   |               | Entities |
                            | (Wireframe)|               | (data)   |
                            +-----------+               +----------+
                              |
                              v
                       next module's View
```

The View and Interactor never reference each other directly. Every arrow
that crosses a box boundary in this diagram is a protocol call, never a
concrete class reference, which is the property the whole pattern is built
to protect.

## 7. Dynamics

The runtime flow below traces one user action, a tap on a sign in button,
through a complete module, matching the worked code example in the code
examples section.

```
User               View            Presenter          Interactor        Router
 |                   |                  |                  |                |
 | taps Sign In      |                  |                  |                |
 |------------------>|                  |                  |                |
 |                   | onSignInTapped() |                  |                |
 |                   |----------------->|                  |                |
 |                   |  showLoading(true)                  |                |
 |                   |<-----------------|                  |                |
 |                   |                  | authenticate()   |                |
 |                   |                  |----------------->|                |
 |                   |                  |                  | calls AuthService
 |                   |                  |                  |----+           |
 |                   |                  |                  |<---+           |
 |                   |                  | authenticationSucceeded(user)     |
 |                   |                  |<-----------------|                |
 |                   |  showLoading(false)                 |                |
 |                   |<-----------------|                  |                |
 |                   |                  | routeToHome(user)                 |
 |                   |                  |----------------------------------->|
 |                   |                  |                  |     presents next
 |                   |                  |                  |     module's View
```

Two properties of this flow matter beyond the happy path shown above.
First, the Interactor never calls the Router, only the Presenter decides
that a transition should happen, because the Interactor has no concept of
screens at all, only of use cases succeeding or failing. Second, the
failure branch mirrors the success branch one for one, `authenticationFailed`
flows back to the Presenter exactly like `authenticationSucceeded`, and the
Presenter decides what the View shows, which keeps every UI facing
decision, including error copy, in one place instead of scattered across
the Interactor.

## 8. Implementation variants

- Delegate protocol variant. The variant shown in dimension 6 and in every
  code example below. Interactor output flows back through a weakly held
  delegate protocol the Presenter implements, matching the objc.io
  article's own description of the pattern. This is the classical and most
  widely documented form.
- Closure or callback variant. Instead of a delegate protocol for output,
  the Interactor's methods accept a completion closure directly, as shown
  in the TypeScript and Java examples below through a returned `Promise`
  and a `Consumer` callback respectively. This removes one protocol per
  module at the cost of a slightly harder to trace call graph, since the
  closure's destination is not declared anywhere near the Interactor's own
  type definition.
- Reactive stream variant. RxSwift, Combine, or RxJava replace both the
  delegate protocol and the closure with a stream the Presenter subscribes
  to. Rambler's own open source RxViper line of tooling, referenced from
  their Generamba README, was built around exactly this combination of
  VIPER's module shape with RxSwift's stream based Interactor output
  (<https://github.com/rambler-digital-solutions/Generamba>, verified
  2026-08-02).
- Code generated scaffolding. Because every module repeats the same five
  to seven file shape, teams write or adopt a generator rather than hand
  copying a previous module. Etsy's VIPERBuilder supplies "a set of base
  classes to divide your app's functionality and a builder object to
  manage the connections"
  (<https://github.com/etsy/VIPERBuilder>, verified 2026-08-02). Rambler's
  Generamba is described in its own README as "designed to generate VIPER
  modules" using a Liquid style template file per project
  (<https://github.com/rambler-digital-solutions/Generamba>, verified
  2026-08-02). Both tools solve the same boilerplate force named in
  dimension 3 by moving the file creation cost from the developer to a
  command line step.
- Separated Router and Builder. Some implementations, including the
  pattern described in the community authored Book of VIPER
  (<https://github.com/strongself/The-Book-of-VIPER>, verified
  2026-08-02), split the module assembler out of the Router entirely into
  its own type, so the Router's only job is presenting an already built
  module rather than also constructing it. This trades one more file for
  a Router whose single responsibility is easier to state.
- Android adaptation. VIPER's role split is not iOS specific in
  principle, and it has real Android adopters, evidenced by open source
  Android VIPER starter templates and micro frameworks on GitHub,
  including a project explicitly named "Android micro framework for
  developing apps based on clean VIPER architecture." The Java example
  below follows that adaptation, using an `Activity` in place of a
  `UIViewController` as the View.
- Cross platform module shape. Because the pattern's contract is
  expressed entirely as interfaces, it translates to any object oriented
  language with interfaces or protocols and a UI framework that supports
  a passive view. The TypeScript example below applies the identical five
  role split outside a mobile context to make that portability concrete
  rather than asserted.

## 9. Known production uses

- Etsy, the online marketplace, built and open sourced VIPERBuilder, a
  scaffolding tool whose own README states it exists to reduce
  "boilerplate", "retain cycles across multiple classes", and "cognitive
  overhead" when building VIPER modules for Etsy's iOS app, and it points
  to Etsy's engineering blog for the fuller account of the adoption
  (<https://github.com/etsy/VIPERBuilder>, verified 2026-08-02). A tool
  built and maintained by a public company's own engineering
  organisation, rather than a personal side project, is direct evidence
  that the underlying architecture reached production use inside that
  company.
- Rambler, a Russian internet and media company, and its Rambler.iOS
  engineering team built Generamba, a VIPER module generator, and
  separately wrote and maintain The Book of VIPER, described in its own
  repository as "the most complete guide to the VIPER architecture" and
  covering module structure and history in depth
  (<https://github.com/rambler-digital-solutions/Generamba>,
  <https://github.com/strongself/The-Book-of-VIPER>, both verified
  2026-08-02). A generator built for internal use and a book length
  internal guide are both signs of an architecture load bearing enough
  inside a company to justify tooling investment beyond a single app.
- ustwo, the digital product studio known outside the mobile architecture
  world for the game Monument Valley, published an open source VIPER
  structured module, `videoplayback-ios`, a Swift wrapper around
  `AVFoundation` for playing progressive downloads and live streams. Its
  README states the team's own reasoning directly, "The VIPER
  architecture has been talked about in the iOS community; however, it is
  uncommonly used. We wanted to gain an in depth understanding of this
  design pattern," and it names video playback specifically because
  "Playing video involves UI updates, data downloading and data
  synchronization," which the team judged a good real test of the pattern
  (<https://github.com/ustwo/videoplayback-ios>, verified 2026-08-02).

Two further data points sit near, without being direct examples of, VIPER
in production. Uber built RIBs, its own cross platform mobile architecture
framework used to build the Uber Driver and Rider apps, and explicitly
positions RIBs against VIPER in its own documentation while reusing the
Router and Interactor names
(<https://github.com/uber/RIBs>, verified 2026-08-02), which shows VIPER's
vocabulary and its business logic first philosophy reaching one of the
largest production mobile codebases in the industry even where the company
ultimately built something else. Community catalogs such as
`onmyway133/awesome-ios-architecture` and GitHub's own
`viper-architecture` topic list dozens of further sample and boilerplate
repositories, which corroborates that the pattern is in active,
widespread developer use even where a company name behind a given
repository cannot always be confirmed.

## 10. Consequences

### Positive

- Business logic in the Interactor is reachable by a plain unit test with
  no simulator, no view hierarchy, and no storyboard, because it depends
  on nothing from `UIKit`. The objc.io article names this as the entire
  reason the pattern was created.
- Every module has the identical five file shape, so an engineer who
  learns the pattern once can predict the location of any given kind of
  code in any module of the app, which lowers the cost of moving between
  features inside a large codebase.
- Screen transition logic lives in one place, the Router, rather than
  scattered across `prepareForSegue` calls and ad hoc navigation code in
  every view controller.
- Module boundaries are protocol boundaries, which makes substituting a
  fake Interactor, a fake Router, or a fake View in a test a matter of
  writing a small class that conforms to the relevant protocol, with no
  mocking framework required.
- Parallel work on one module becomes practical, since two engineers can
  build the View and the Interactor side by side against an already
  agreed protocol.

### Negative

- File count and boilerplate rise sharply. A screen that would be one
  class in MVC becomes five or more classes plus their protocols, the
  exact cost Orlov's essay measures against the pattern's own separation
  benefit.
- Retain cycles are easy to introduce by accident, because the module's
  objects hold references to each other in both directions. Etsy's own
  VIPERBuilder README lists "retain cycles" as one of the three problems
  its tool exists to reduce.
- Onboarding cost is real. A new engineer has to learn the shape before
  its predictability starts paying back, and until then the extra
  indirection reads as pure overhead.
- Small or simple screens are actively harmed, not merely unhelped,
  because the fixed protocol and file cost is paid whether or not there
  is any real logic to protect, the situation Orlov calls building "The
  Empire State Building from LEGO blocks."
- The pattern predates SwiftUI and the Observation framework, so a team
  adopting VIPER inside a modern declarative UI has to decide how much of
  the original `UIKit` era shape, particularly the View's passivity and
  the Router's imperative presentation calls, still applies, and every
  source in this entry's reference list was written for `UIKit`.

## 11. Failure modes and misuse

The symptom, cause, and fix below are drawn from the practical guidance in
the sources cited through this entry, combined with the ordinary
experience of teams running any five object per screen architecture,
labelled here as judgement grounded in those sources rather than as one
further sourced statistic.

- **Symptom.** The View calls the Interactor or reads an Entity directly
  instead of going through the Presenter, and a change to the Interactor's
  return shape now forces a change in the View as well.
  **Cause.** The Presenter's protocol was treated as optional scaffolding
  rather than as the pattern's actual enforcement mechanism, usually under
  a deadline, with the reasoning that "it is faster this time."
  **Fix.** Restore the boundary by giving the View only the two protocols
  described in dimension 5, and add a compile time check, such as marking
  the Interactor and Entity types internal to the module's own file or
  target, so a future shortcut fails to build rather than merely reading
  wrong in review.
- **Symptom.** The app crashes or silently stops updating a screen with
  no obvious cause, most often after navigating away and back to the same
  module.
  **Cause.** A retain cycle between the Presenter and its View, or between
  the Presenter and its Interactor, because one of the two back references
  was declared as a strong property instead of a weak one, the exact risk
  Etsy names in its own README.
  **Fix.** Declare every reference that points back toward the object
  that created it, View holding Presenter and Interactor holding its
  output delegate, as weak, and verify with Instruments or the Memory
  Graph Debugger that the module's objects deallocate after the screen is
  dismissed.
- **Symptom.** Every module in the codebase looks identical in shape but
  wildly different in size, with some Interactors carrying a thousand
  lines and others carrying five.
  **Cause.** The team treats VIPER as mandatory for every screen rather
  than reserving it for screens with real logic, exactly the case flagged
  in the non-applicability list in dimension 4.
  **Fix.** Allow simple screens to use a lighter pattern, commonly MVC or
  MVP for a static or read only screen, and reserve the full VIPER split
  for modules with real decision logic, so the file count cost is only
  paid where the testability benefit is real.
- **Symptom.** A code review takes far longer than the change itself
  would suggest, because a one line business rule change touches the
  Interactor, its output protocol, the Presenter's conformance to that
  protocol, and a test double, four files for one rule.
  **Cause.** Over granular protocol splitting, one protocol per method
  rather than one protocol per role, which multiplies the boilerplate cost
  named in dimension 3 well beyond what the pattern itself calls for.
  **Fix.** Keep exactly the five protocols the structure in dimension 5
  describes, one per collaborator boundary, and resist adding a new
  protocol for every new method. A growing Interactor protocol is a
  normal, not an alarming, sign of a module doing real work.
- **Symptom.** The Router ends up holding business logic, deciding, for
  example, which of two possible next screens to show based on a domain
  rule rather than being told which screen to show.
  **Cause.** Routing decisions and business decisions were not kept
  separate, usually because it felt convenient to make the choice at the
  point the transition code already existed.
  **Fix.** Move the decision itself into the Interactor or Presenter, and
  leave the Router with exactly one job, performing a transition it is
  told to perform. This keeps the Router testable purely by checking it
  constructs and presents the right module for a given instruction, with
  no domain logic to fake.

## 12. Trade-off matrix

| Force | VIPER | Model-View-Presenter | Model-View-ViewModel | Clean Swift (VIP) |
|---|---|---|---|---|
| Testability of business logic | Strong, business logic isolated in the Interactor with no UI import | Strong, logic isolated in the Presenter | Strong, logic isolated in the ViewModel, but binding glue is harder to unit test | Strong, logic isolated in the Interactor, same idea as VIPER |
| File count per screen | Highest of the four, five to seven files plus protocols | Moderate, View, Presenter, and a protocol pair | Moderate, View and ViewModel, fewer protocols if bindings are used | Moderate, no separate Router file since routing folds into the scene |
| Navigation ownership | Dedicated Router object, one clear place | Usually left to the View or a shared coordinator, not part of the pattern itself | Usually left to the View or a shared coordinator, not part of the pattern itself | Folded back into the scene, no dedicated Router |
| Declarative UI fit (SwiftUI style) | Weak, designed for imperative `UIKit` view controllers | Weak to moderate | Strong, ViewModel maps closely onto SwiftUI's `@Observable` state | Weak, also designed for `UIKit` |
| Boilerplate cost | Highest, named directly as a cost by Orlov and by Etsy's own tooling README | Lower than VIPER, no Interactor or Entity split | Lower, especially with two way binding | Lower than VIPER, one fewer object and no Router protocol |
| Best fit | A large screen with real business rules inside a team that values a strict, uniform module shape | A screen where the View needs to stay simple to test but a full Router split is not needed | A screen whose state maps naturally onto bindable, observable properties | A team that wants VIPER style logic isolation without the Router's extra ceremony |

The comparison targets three named alternatives rather than a strawman
because all three genuinely compete for the same slot, a screen level
architecture that separates business logic from `UIKit`. Model-View-
Controller is deliberately left out of this table because it is the anti
example every one of the four patterns above is written to replace, not a
serious competitor for a screen with real logic.

## 13. Related and incompatible patterns

- Model-View-Presenter. VIPER is best understood as MVP with two further
  splits applied to it, the Presenter's data access logic is pulled out
  into a dedicated Interactor, and its screen transition logic is pulled
  out into a dedicated Router. A team that finds a VIPER module's
  Interactor and Presenter doing nearly identical jobs, with the
  Interactor reduced to a single pass through call, is often better
  served by moving that module back to plain MVP.
- Model-View-Controller. VIPER exists as a direct reaction against the
  massive view controller failure mode MVC produces on `UIKit`, described
  in dimension 2. The two are not combined inside one module. A codebase
  in transition instead runs some modules as MVC and others as VIPER side
  by side, and moves modules across the boundary one at a time as
  described in dimension 14.
- Clean Architecture. VIPER is Clean Architecture's dependency rule
  applied to a specific, opinionated iOS module shape, as described in
  dimension 1. Clean Architecture supplies the underlying rule, VIPER
  supplies the concrete class names and the protocol boundaries that
  satisfy that rule for one screen.
- Mediator. The Presenter plays a Mediator role between the View and the
  Interactor, neither of those two objects references the other directly,
  and every interaction between them passes through the Presenter, which
  matches the Mediator pattern's core idea of replacing many to many
  object references with one central coordinator.
- Observer. The delegate protocol callback from the Interactor back to
  the Presenter, and from the Presenter back to the View, is a single
  subscriber variant of the Observer pattern. The reactive stream
  implementation variant described in dimension 8 makes this relationship
  explicit by using an actual observable stream in place of a plain
  delegate method.
- Command. A user action forwarded from the View to the Presenter, and
  from the Presenter to the Interactor, can be modelled as a Command
  object rather than as a direct method call when a module needs to
  queue, undo, or log user actions, though the worked example in this
  entry uses plain method calls for clarity, matching how most real
  VIPER codebases are written.
- Repository. The Interactor rarely talks to a network client or a
  database directly. The more disciplined and more common shape puts a
  Repository between the two, so the Interactor depends on a Repository
  protocol and the concrete networking or persistence code lives behind
  it, independent of VIPER's own five roles.

No pattern in this list is formally incompatible with VIPER at the level a
type system could reject. The one genuine tension is with SwiftUI's
Observation model, discussed as a non-applicability case in dimension 4. A
`@Observable` model type driving a SwiftUI view already gives most of what
a Presenter and Entity together give a VIPER module, so layering the two
on top of each other tends to produce a module with a redundant layer
rather than a clearer one.

## 14. Refactoring path in and out

Introducing VIPER into a module that does not have it, and removing VIPER
from a module that no longer earns its cost, are the same operation run in
opposite directions.

Introducing VIPER, into an existing massive view controller.

1. Extract Interface on the view controller for the small set of methods
   the rest of the module will need to call on it, becoming the View
   protocol. This is the classical Extract Interface refactoring, applied
   here to create the View's own contract rather than to break a
   dependency on an external library.
2. Move every line of business logic, meaning any code that decides
   something rather than displays something, such as validation,
   sequencing of network calls, or state transitions, out of the view
   controller and into a newly created Interactor class, using Extract
   Class repeatedly until the view controller holds only display code.
3. Extract Class again to create a Presenter, and Move Method every
   remaining decision the view controller still makes, such as which
   Interactor method to call for a given user action or how to format a
   result for display, into that Presenter.
4. Extract Class one further time to create a Router, and Move Method
   every `prepareForSegue`, `present`, or `pushViewController` call out
   of the view controller and into it.
5. Introduce the delegate protocols between Presenter and Interactor, and
   between Presenter and View, so the four objects created above talk
   only through those protocols from this point forward, closing the door
   on the View or Router reaching directly into the Interactor.
6. Introduce a small assembler function, as described in dimension 5,
   that builds and wires the four objects, and route every place that
   used to instantiate the old view controller through that assembler
   instead.

Removing VIPER, from a module whose Interactor has thinned down to a
single pass through call with no real logic left to protect.

1. Confirm the removal candidate honestly by reading the Interactor's
   methods and checking whether any of them still branch, validate, or
   sequence more than one call. If any of them do, this module still
   earns the split and should not be collapsed.
2. Inline Method to fold the Interactor's remaining pass through calls
   directly into the Presenter, since a call with no logic of its own
   adds only a file and a protocol with nothing behind it.
3. Merge the Presenter and the View's protocol conformance if the team's
   target pattern is MVC, or keep the View protocol boundary if the target
   is MVP, matching the team's chosen replacement rather than defaulting
   to MVC by omission.
4. Keep the Router if screen transition logic for the module is
   genuinely complex, a Router earns its place independently of whether
   the rest of the module still needs the full VIPER split, since
   navigation logic scattered back into a view controller reintroduces
   exactly the massive view controller symptom described in dimension 2.
5. Delete the now empty protocols and the assembler function last, once
   every call site has been moved, so the module never spends time in a
   state where some collaborators go through the old protocols and
   others do not.

## 15. Testing and verification

This dimension is largely practice rather than a claim any one source
states as a rule, though the underlying motivation, that the Interactor
should be reachable without `UIKit`, is the pattern's own stated reason
for existing, per the objc.io article cited in dimension 1.

- Interactor tests. Instantiate the Interactor directly with a fake or in
  memory implementation of whatever service protocol it depends on, call
  its methods, and assert on the plain values or Entities it produces or
  on the output protocol calls it makes. No view, no simulator, and no
  asynchronous UI test runner are needed, which is the entire testability
  benefit the pattern exists to provide.
- Presenter tests. Give the Presenter a fake View that records every
  method called on it and a fake Interactor whose output methods the test
  triggers directly, then assert the Presenter drove the fake View with
  the right sequence of calls, for example `showLoading(true)` before the
  Interactor call and `showLoading(false)` paired with either a router
  call or an error display afterward. This is the layer where regressions
  in the dynamics diagram in dimension 7, such as a missing
  `showLoading(false)` on the failure branch, are actually caught.
- Router tests. Give the Router a fake navigation target, call its
  methods, and assert it attempted to present the correct module, without
  needing a real window or view hierarchy, since the Router's own logic
  is a pure mapping from an instruction to a presentation call.
- View tests. The View itself is usually left to UI level testing, such
  as `XCUITest` on Apple platforms or Espresso on Android, precisely
  because it is the one object in the module that genuinely needs a
  rendered screen to test meaningfully. VIPER does not remove the need
  for UI tests, it removes business logic from needing them.
- Contract tests between layers. Because every collaborator talks through
  a protocol, a shared fake conforming to that protocol, used by both the
  Presenter's tests and the Interactor's tests, keeps the two test suites
  from silently drifting apart if the protocol's shape changes. This is
  the practical payoff of dimension 5's insistence that every module
  boundary be a protocol rather than a concrete class reference.

## 16. Observability signals

This dimension is analytical rather than sourced to any one VIPER
specific document, applying general mobile observability practice to the
pattern's own object boundaries.

- Log or trace a correlation identifier at the moment the View forwards a
  user action to the Presenter, and carry that same identifier through
  the Interactor's call to any network or persistence service, so a
  single user tap can be traced end to end across the module's five
  objects in a crash report or a performance trace.
- Instrument the Interactor's use case methods with timing, since that is
  where a slow network call or a slow database query actually happens. A
  module whose Presenter shows a loading state for several seconds but
  whose own code does nothing slow is a signal to look inside the
  Interactor, not the Presenter or the View.
- Count Router presentations by source module and destination module in
  analytics, since the Router is the one object in a VIPER module that
  already knows, by construction, every screen transition the app makes,
  which turns it into a natural single place to instrument a screen flow
  funnel rather than sprinkling analytics calls through many view
  controllers.
- Watch memory graph snapshots, or the equivalent tool on a non Apple
  platform, for modules whose Presenter, View, or Interactor instances
  are still alive after the module's Router has already presented the
  next module. A live instance after its screen has been dismissed is the
  direct observable sign of the retain cycle failure mode described in
  dimension 11.
- A module that is healthy on a dashboard shows Interactor call
  durations clustered by use case, Router presentations that always pair
  one for one with a Presenter decision to transition, and zero
  surviving instances of the previous module's objects a short time
  after a new module is presented. A module that is failing shows
  Interactor durations with a long tail for no visible network reason,
  Router presentations with no matching Presenter log entry immediately
  before them, and object counts for a dismissed module that never drop
  to zero.

## 17. Security and privacy implications

- The Entity layer is the natural, and often the only, place in a VIPER
  module where sensitive domain data, such as a user's credentials,
  health data, or payment details, is held in memory in its plain,
  decoded form. Because Entities are deliberately kept independent of any
  persistence or network model in the design described in dimension 5, a
  team can apply a single data handling policy, such as zeroing sensitive
  fields once a use case completes, at that one layer rather than
  tracking the same data shape across a network model, a database model,
  and a UI model.
- Because the Interactor is the only object in the module permitted to
  talk to a network client or a persistence layer, an audit of where a
  given module can send or receive data reduces to reading one file
  rather than searching the whole module, which is a real, if
  incidental, security benefit of the pattern's own structure rather than
  a feature it markets itself on.
- The View, being intentionally passive, never independently decides to
  log or transmit anything, every value it displays came from the
  Presenter, so a review of what user facing data could leak through
  analytics or crash reporting SDKs attached to the View narrows to a
  review of what the Presenter passed it.
- None of the sources cited in this entry discuss authentication,
  encryption, or data protection as part of VIPER itself, and this entry
  does not invent a position on those topics beyond the structural
  observations above. VIPER is silent on transport security, at rest
  encryption, and access control, and a team still needs its own policy
  for all three regardless of which screen level architecture it
  chooses.

## 18. References

- Gilbert, J., Stoll, C., "Architecting iOS Apps with VIPER", objc.io
  Issue 13, June 2014. <https://www.objc.io/issues/13-architecture/viper/>,
  verified 2026-08-02.
- Martin, R. C., "The Clean Architecture", The Clean Code Blog, 13 August
  2012.
  <https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html>,
  verified 2026-08-02.
- Orlov, B., "iOS Architecture Patterns", Medium, netguru.
  <https://medium.com/ios-os-x-development/ios-architecture-patterns-ecba4c38de52>,
  verified 2026-08-02.
- Kodeco (formerly raywenderlich.com), "Getting Started with the VIPER
  Architecture Pattern".
  <https://www.kodeco.com/8440907-getting-started-with-the-viper-architecture-pattern>,
  verified 2026-08-02.
- Etsy, Inc., VIPERBuilder repository README.
  <https://github.com/etsy/VIPERBuilder>, verified 2026-08-02.
- Rambler Digital Solutions, Rambler.iOS Team, Generamba repository
  README. <https://github.com/rambler-digital-solutions/Generamba>,
  verified 2026-08-02.
- Rambler.iOS Team and contributors, The Book of VIPER repository.
  <https://github.com/strongself/The-Book-of-VIPER>, verified 2026-08-02.
- ustwo, videoplayback-ios repository README.
  <https://github.com/ustwo/videoplayback-ios>, verified 2026-08-02.
- Uber Technologies, RIBs repository README.
  <https://github.com/uber/RIBs>, verified 2026-08-02.
- Clean Swift, project site. <https://clean-swift.com>, verified
  2026-08-02.
- Mutual Mobile, merged into Grid Dynamics, original introductory post,
  checked and found no longer live, now redirecting to a merger notice.
  <https://www.mutualmobile.com/posts/introducing-viper>, checked and
  found dead 2026-08-02. Retained here so a reader who finds the URL
  cited elsewhere on the web knows it no longer resolves. The objc.io
  article above, written by the same two authors, is the durable
  substitute.

## Code examples

Three languages where the pattern is genuinely idiomatic, all built
around the same worked example, a sign in module, so a reader can compare
the identical five role split across languages line by line. Swift is the
pattern's native language and is shown first in its classical delegate
protocol form. Java shows the same shape adapted to Android, using an
`Activity` as the View and a functional `Consumer` callback in place of a
delegate protocol for the Interactor's output, matching the closure
variant described in dimension 8. TypeScript shows the identical five
role split applied outside a mobile context entirely, using `Promise`
based output from the Interactor, to make the point from dimension 8 that
the pattern's contract is a set of interfaces and does not depend on any
one UI framework. Python is omitted because VIPER's value comes from a
compiler enforced protocol boundary between collaborators, and Python's
duck typed method resolution does not reject a View that reaches past its
Presenter into the Interactor the way Swift's protocol conformance or
Java's interface implementation does, so the pattern's central guarantee
cannot be demonstrated faithfully in Python without adding a static type
checker on top of the language.

### Swift

```swift
struct User {
    let id: String
    let displayName: String
}

enum SignInError: Error {
    case invalidCredentials
    case network
}

protocol SignInInteractorInput: AnyObject {
    func authenticate(email: String, password: String)
}

protocol SignInInteractorOutput: AnyObject {
    func authenticationSucceeded(user: User)
    func authenticationFailed(error: SignInError)
}

protocol SignInViewInput: AnyObject {
    func showLoading(_ visible: Bool)
    func showError(_ message: String)
}

protocol SignInViewOutput: AnyObject {
    func viewDidTapSignIn(email: String, password: String)
}

protocol SignInRouterInput: AnyObject {
    func routeToHome(for user: User)
}

final class AuthService {
    func signIn(email: String, password: String, completion: @escaping (Result<User, SignInError>) -> Void) {
        if email.contains("@") && password.count >= 8 {
            completion(.success(User(id: "u1", displayName: email)))
        } else {
            completion(.failure(.invalidCredentials))
        }
    }
}

final class SignInInteractor: SignInInteractorInput {
    weak var output: SignInInteractorOutput?
    private let service: AuthService

    init(service: AuthService) {
        self.service = service
    }

    func authenticate(email: String, password: String) {
        service.signIn(email: email, password: password) { [weak self] result in
            switch result {
            case .success(let user):
                self?.output?.authenticationSucceeded(user: user)
            case .failure(let error):
                self?.output?.authenticationFailed(error: error)
            }
        }
    }
}

final class SignInPresenter: SignInViewOutput, SignInInteractorOutput {
    weak var view: SignInViewInput?
    var interactor: SignInInteractorInput?
    var router: SignInRouterInput?

    func viewDidTapSignIn(email: String, password: String) {
        view?.showLoading(true)
        interactor?.authenticate(email: email, password: password)
    }

    func authenticationSucceeded(user: User) {
        view?.showLoading(false)
        router?.routeToHome(for: user)
    }

    func authenticationFailed(error: SignInError) {
        view?.showLoading(false)
        view?.showError("Sign in failed. Check your details and try again.")
    }
}

final class SignInRouter: SignInRouterInput {
    func routeToHome(for user: User) {
        print("Routing to home for \(user.displayName)")
    }
}

final class SignInViewController: SignInViewInput {
    var presenter: SignInViewOutput?

    func showLoading(_ visible: Bool) {
        print(visible ? "Loading" : "Done")
    }

    func showError(_ message: String) {
        print("Error: \(message)")
    }

    func tapSignIn(email: String, password: String) {
        presenter?.viewDidTapSignIn(email: email, password: password)
    }
}

func buildSignInModule() -> SignInViewController {
    let view = SignInViewController()
    let presenter = SignInPresenter()
    let interactor = SignInInteractor(service: AuthService())
    let router = SignInRouter()

    view.presenter = presenter
    presenter.view = view
    presenter.interactor = interactor
    presenter.router = router
    interactor.output = presenter

    return view
}

let module = buildSignInModule()
module.tapSignIn(email: "mirza@example.com", password: "hunter2pass")
```

### Java

```java
import java.util.function.Consumer;

final class User {
    final String id;
    final String displayName;

    User(String id, String displayName) {
        this.id = id;
        this.displayName = displayName;
    }
}

interface SignInContract {
    interface View {
        void showLoading(boolean visible);
        void showError(String message);
    }

    interface Presenter {
        void onSignInTapped(String email, String password);
    }

    interface Interactor {
        void authenticate(String email, String password, Consumer<User> onSuccess, Consumer<String> onFailure);
    }

    interface Router {
        void routeToHome(User user);
    }
}

final class AuthService {
    void signIn(String email, String password, Consumer<User> onSuccess, Consumer<String> onFailure) {
        if (email.contains("@") && password.length() >= 8) {
            onSuccess.accept(new User("u1", email));
        } else {
            onFailure.accept("invalid_credentials");
        }
    }
}

final class SignInInteractor implements SignInContract.Interactor {
    private final AuthService service;

    SignInInteractor(AuthService service) {
        this.service = service;
    }

    public void authenticate(String email, String password, Consumer<User> onSuccess, Consumer<String> onFailure) {
        service.signIn(email, password, onSuccess, onFailure);
    }
}

final class SignInPresenter implements SignInContract.Presenter {
    private final SignInContract.View view;
    private final SignInContract.Interactor interactor;
    private final SignInContract.Router router;

    SignInPresenter(SignInContract.View view, SignInContract.Interactor interactor, SignInContract.Router router) {
        this.view = view;
        this.interactor = interactor;
        this.router = router;
    }

    public void onSignInTapped(String email, String password) {
        view.showLoading(true);
        interactor.authenticate(email, password,
            user -> {
                view.showLoading(false);
                router.routeToHome(user);
            },
            error -> {
                view.showLoading(false);
                view.showError("Sign in failed. Check your details and try again.");
            });
    }
}

final class SignInRouter implements SignInContract.Router {
    public void routeToHome(User user) {
        System.out.println("Routing to home for " + user.displayName);
    }
}

final class SignInActivity implements SignInContract.View {
    private SignInContract.Presenter presenter;

    void attach(SignInContract.Presenter presenter) {
        this.presenter = presenter;
    }

    public void showLoading(boolean visible) {
        System.out.println(visible ? "Loading" : "Done");
    }

    public void showError(String message) {
        System.out.println("Error: " + message);
    }

    void tapSignIn(String email, String password) {
        presenter.onSignInTapped(email, password);
    }
}

public final class Demo {
    public static void main(String[] args) {
        SignInActivity view = new SignInActivity();
        AuthService service = new AuthService();
        SignInInteractor interactor = new SignInInteractor(service);
        SignInRouter router = new SignInRouter();
        SignInPresenter presenter = new SignInPresenter(view, interactor, router);
        view.attach(presenter);

        view.tapSignIn("mirza@example.com", "hunter2pass");
    }
}
```

### TypeScript

```typescript
interface User {
  id: string;
  displayName: string;
}

interface SignInViewInput {
  showLoading(visible: boolean): void;
  showError(message: string): void;
}

interface SignInViewOutput {
  onSignInTapped(email: string, password: string): void;
}

interface SignInInteractorInput {
  authenticate(email: string, password: string): Promise<User>;
}

interface SignInRouterInput {
  routeToHome(user: User): void;
}

class AuthService {
  async signIn(email: string, password: string): Promise<User> {
    if (email.includes("@") && password.length >= 8) {
      return { id: "u1", displayName: email };
    }
    throw new Error("invalid_credentials");
  }
}

class SignInInteractor implements SignInInteractorInput {
  constructor(private readonly service: AuthService) {}

  authenticate(email: string, password: string): Promise<User> {
    return this.service.signIn(email, password);
  }
}

class SignInPresenter implements SignInViewOutput {
  constructor(
    private readonly view: SignInViewInput,
    private readonly interactor: SignInInteractorInput,
    private readonly router: SignInRouterInput
  ) {}

  async onSignInTapped(email: string, password: string): Promise<void> {
    this.view.showLoading(true);
    try {
      const user = await this.interactor.authenticate(email, password);
      this.view.showLoading(false);
      this.router.routeToHome(user);
    } catch {
      this.view.showLoading(false);
      this.view.showError("Sign in failed. Check your details and try again.");
    }
  }
}

class SignInRouter implements SignInRouterInput {
  routeToHome(user: User): void {
    console.log(`Routing to home for ${user.displayName}`);
  }
}

class SignInScreen implements SignInViewInput {
  presenter!: SignInViewOutput;

  showLoading(visible: boolean): void {
    console.log(visible ? "Loading" : "Done");
  }

  showError(message: string): void {
    console.log(`Error: ${message}`);
  }

  tapSignIn(email: string, password: string): void {
    this.presenter.onSignInTapped(email, password);
  }
}

function buildSignInModule(): SignInScreen {
  const view = new SignInScreen();
  const interactor = new SignInInteractor(new AuthService());
  const router = new SignInRouter();
  const presenter = new SignInPresenter(view, interactor, router);
  view.presenter = presenter;
  return view;
}

const screen = buildSignInModule();
screen.tapSignIn("mirza@example.com", "hunter2pass");
```
