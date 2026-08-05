---
name: Model-View-Controller
slug: model-view-controller
family: 05-architectural
category: Architectural
aliases: [MVC, Model-View-Controller pattern, Smalltalk MVC]
first_described: "Trygve Reenskaug, Xerox PARC, 1978-1979"
maturity: canonical
related: [observer, strategy, composite, front-controller, mediator, presentation-model]
incompatible_with: []
verified: 2026-08-02
---

# Model-View-Controller

## 1. Name, aliases, and lineage

The pattern is universally called Model-View-Controller, almost always shortened to
MVC. There is no serious rival name in modern usage, though the original 1979 papers
used slightly different wording before the terminology settled.

Trygve Reenskaug invented the pattern while a visiting scientist with the Learning
Research Group at Xerox PARC, working alongside the Smalltalk team from the summer
of 1978 to the summer of 1979. He wrote two internal notes that document the
evolution of the idea. The first, dated 12 May 1979, was titled "Thing-Model-View-
Editor" and used the word Editor rather than Controller. The second, dated 10
December 1979, settled on the name "Models-Views-Controllers" and is the direct
ancestor of the term used today. Reenskaug has been careful, in his own
retrospective writing, to say he was not one of the original Smalltalk inventors,
only an early contributor who applied their ideas to a concrete problem, namely how
to let end users of a Smalltalk-based simulation system directly manipulate the
objects they were viewing, rather than treating the screen as a passive report
(Trygve Reenskaug, "MVC XEROX PARC 1978-79," https://folk.universitetetioslo.no/trygver/themes/mvc/mvc-index.html, verified
2026-08-02).

The pattern reached a much larger audience through Smalltalk-80, where it shipped as
a first-class part of the class library, and through Glenn Krasner and Stephen
Pope's 1988 paper on the Model-View-Controller user interface approach in
Smalltalk-80, published in the Journal of Object-Oriented Programming, vol. 1, no.
3, 1988, which is the paper most later authors cite when they describe the classic
Smalltalk MVC triad of Model, View, and Controller, with a Controller object per
View handling raw input events. The Gang of Four's Design Patterns book does not
treat MVC as one of its 23 catalogued patterns, but its introduction explicitly
credits MVC as the inspiration for Observer, Strategy, and Composite, describing the
model-view relationship as "a good example of the Observer pattern" (Erich Gamma,
Richard Helm, Ralph Johnson, John Vlissides, Design Patterns. Elements of Reusable
Object-Oriented Software, Addison-Wesley, 1994, Introduction, section 1.4). The
pattern's most widely cited architectural writeup outside Smalltalk circles is Frank
Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, and Michael Stal,
Pattern-Oriented Software Architecture Volume 1. A System of Patterns (Wiley, 1996),
which places MVC in the book's chapter on interactive systems patterns and treats it
as a composition of Observer, Strategy, and Composite rather than a single
indivisible unit.

A caution belongs in this section rather than later. The phrase "MVC" is used today
for at least three meaningfully different architectures, the original Smalltalk
pattern with a Controller per widget that owns raw input handling, the web variant
popularised by Ruby on Rails and Spring MVC where the Controller is a per-request
coordinator invoked by a front controller, and the desktop or mobile variant where
the Controller sits between a passive View and a Model and pushes data in both
directions. This entry treats all three as one family and calls out the differences
explicitly under Implementation Variants, because treating them as identical is the
single most common source of confusion when engineers argue about what MVC "really"
means.

## 2. Problem and context

The problem MVC solves is separation of concerns in a system where a person is
directly manipulating a live data structure through a graphical interface, and the
interface must stay synchronized as the data changes, sometimes because of that
person's own actions, sometimes because of another process entirely.

Reenskaug's original motivation was concrete. Build a simulation editor for
Smalltalk where end users could see a live picture of the objects in a running
program and directly edit them. Before MVC, the natural way to write such a program
mixed input handling, screen drawing, and business logic in one object per widget.
Every widget that displayed the same underlying data duplicated the logic for
keeping itself current, and every change to how data was displayed risked touching
code that also decided what the data meant.

The context in which the pattern earns its keep is any system with these three
properties at once. First, there is a body of application state, the domain data
and rules, that has meaning independent of any particular screen. Second, that
state can be presented in more than one way, or is expected to be presentable in
more than one way eventually, whether that is two different windows on the same
object, a desktop client and a web client, or a JSON API and an HTML page. Third,
user input needs to be translated into changes to that state through some layer of
interpretation, validation, or routing that is itself worth naming and testing
separately from both the state and the presentation.

Where only one of those three properties holds, MVC is often more structure than the
problem needs. A single-screen script that reads a file, transforms it, and prints
one report gains little from three named layers. The pattern earns its cost when the
model is genuinely reusable across more than one presentation, or when the
presentation is genuinely expected to change independently of the underlying rules,
for example a REST API and a server-rendered HTML view sharing one set of domain
objects and validation logic.

## 3. Forces

Coupling versus duplication. Splitting the system into three roles reduces the
coupling between "what the data means" and "how it looks," but if the boundaries are
drawn wrong, and controllers start containing display logic, or views start
querying the database directly, the split adds ceremony without buying the
reduction in coupling it exists to purchase.

Reusability versus indirection. A model that never imports anything about
presentation can be reused behind a different View, a batch job, or an API, but
every layer of indirection between a person's click and the code that actually runs
is a layer that has to be traced during debugging.

Consistency versus latency. When a model notifies its views synchronously through
an Observer-style mechanism, the interface stays consistent by construction, but a
slow or numerous set of observers can turn a single state change into a visible
pause. Asynchronous notification restores responsiveness at the cost of a brief
window where the interface can show stale data.

Team topology versus cognitive load. MVC is one of the few patterns whose primary
justification, historically, is organizational as much as technical, because it lets
one person or team own the model while another owns the view, and the boundary
between them is a real interface, not a convention. That benefit is largest on
teams that are actually split along those lines, front-end engineers who touch views
and back-end engineers who touch models, and smallest on a single engineer working
alone, where the same person now has to hold three files in their head instead of
one to change a single field.

Web MVC's dominant force is different from desktop MVC's. On the web, the request
and response cycle is structurally stateless and one-shot, so the Observer-driven
live-update half of the classic pattern is largely irrelevant. The force that
matters instead is routing many different URLs to the correct handler without
duplicating the plumbing that extracts parameters, checks authentication, and picks
a rendering strategy. This is why web MVC frameworks converge on a front controller
rather than a controller-per-widget, a difference covered in Implementation
Variants.

## 4. Applicability and non-applicability

Reach for MVC when the same underlying state must be presented through more than one
view, live or eventually, and keeping that state's meaning independent of any one
view genuinely reduces future rework. Reach for it when input handling is complex
enough, validation, routing, authorization, multiple input sources, that giving it a
name and a testable boundary pays for itself. Reach for it when more than one person
will work on the system and the model/view split maps onto how the team is actually
organized. Reach for it in a web application with more than a handful of routes,
where a front-controller-style MVC framework buys consistent request handling,
consistent error pages, and a single place to add cross-cutting concerns such as
authentication.

Do not reach for MVC in a single-purpose script or a one-screen tool where there is
exactly one view and it will never have a second. The three-layer split adds files
and indirection for a benefit that never materializes. Do not reach for it as the
concurrency or state-management answer for a genuinely reactive, streaming, or
event-sourced system, those systems are better served by an explicit event or
data-flow architecture, for example Model-View-Presenter or Flux/Redux-style
unidirectional data flow for the UI-facing variant of that problem, because forcing
bidirectional Observer notifications onto a stream of discrete events tends to
produce ordering bugs. Do not reach for it when the "view" is not really a
user-facing presentation at all, for example a machine-to-machine API with no HTML
rendering step. A thin request/response handler talking to a service layer is
usually clearer than maintaining a View concept that never renders anything a
person looks at. Do not reach for classic controller-per-widget MVC, the original
Smalltalk shape, on platforms whose native UI toolkit already gives you a strong
binding or declarative-state mechanism, such as SwiftUI or Jetpack Compose. Forcing
that shape onto a toolkit designed around unidirectional state flow fights the
platform rather than working with it. Finally, do not reach for MVC as a synonym for
"any three-layer architecture." A system with a data-access layer, a business-logic
layer, and a presentation layer is a layered architecture, and calling it MVC when
none of the layers actually observe or push updates to another is a category error
that muddies later architectural discussions on a team.

## 5. Structure

Model. Owns the application's domain state and the rules that govern how that
state may change. In the classic Smalltalk shape the Model is an active, observable
object. Other objects, the Views, register themselves as dependents, and the Model
notifies them whenever its state changes, without knowing anything about who those
dependents are or how they will react. In the web variant the Model is usually a
passive object, an ORM-backed record or a plain data structure, and the
notification half of the pattern is absent because there is no persistent
connection to notify over.

View. Renders a presentation of the Model's current state. In the classic shape a
View both draws itself and forwards raw input events, mouse clicks, keystrokes, to
its associated Controller. It also subscribes to the Model as an Observer so it can
redraw itself when the Model changes, and it may query the Model directly to pull
the data it needs to render, rather than being pushed a full copy of the state. In
the web variant the View is a template or a serializer, invoked once per request
with the data the Controller hands it, and it has no independent existence between
requests.

Controller. Interprets input and decides how it should change the Model or select a
View. In the classic shape, each View has an associated Controller, and the two
together are sometimes treated as a single visual widget. The Controller receives
raw input events from the View, translates them into operations on the Model, or
into commands to swap which View or Controller is active, a mechanism Krasner and
Pope call view/controller replacement, and may also directly set state on its View
for things that are purely about interaction state rather than domain state, such as
which item in a list is currently selected. In the web variant, the Controller,
often called an "action" or a "handler," is invoked once per HTTP request by a
front controller, reads request parameters, calls into the Model or a service
layer, and chooses which View to render with which data. It does not persist state
and does not hold a reference to a live View instance between requests.

A fourth, unofficial participant appears in nearly every real implementation, a
dispatcher or front controller that decides which Controller instance handles a
given request or event in the first place. Reenskaug's original design left this
implicit, a Controller was wired to its View at construction time, but nearly every
production web MVC framework makes it an explicit, named object, because with
dozens or hundreds of routes the wiring cannot reasonably be done by hand for each
one. This is documented explicitly in Spring's own architecture description of the
DispatcherServlet as the central request-handling component of Spring Web MVC
(Spring Framework Reference Documentation, "Web on Servlet Stack, Web MVC," https://docs.spring.io/spring-framework/reference/web/webmvc.html, verified
2026-08-02).

## 6. ASCII structure diagram

```
                       Classic (Smalltalk / desktop) shape
  +------------------------------------------------------------------+
  |                                                                   |
  |   +-----------+   notifies (Observer)     +-----------+          |
  |   |   Model   |--------------------------->|   View    |          |
  |   +-----------+                            +-----------+          |
  |        ^                                        |                 |
  |        | reads state to render                  | raw input       |
  |        | (pull)                                 v                 |
  |        |                                    +-----------+          |
  |        +------------- updates model --------|Controller |          |
  |                                              +-----------+          |
  |                                              (one Controller       |
  |                                               per View instance)   |
  +------------------------------------------------------------------+

                        Web (front-controller) shape
  +---------------------------------------------------------------------+
  |  HTTP request                                                        |
  |      |                                                                |
  |      v                                                                |
  |  +----------------+   routes to    +------------+   reads/writes     |
  |  | FrontController |--------------->| Controller |------------------->+
  |  | (DispatcherServlet, |            +------------+                   |
  |  |  Rails router, etc.)|                  |                          |
  |  +----------------+                       | picks a view + data      |
  |                                            v                          |
  |                                       +-----------+     +-----------+ |
  |                                       |   View    |<----|   Model   | |
  |                                       | (template)|      +-----------+|
  |                                       +-----------+                  |
  |                                            |                          |
  |                                            v                          |
  |  HTTP response                       (rendered HTML/JSON)             |
  +---------------------------------------------------------------------+
```

## 7. Dynamics

Classic Smalltalk flow, a person clicks a widget.

```
Person clicks a shape in a drawing editor
   |
   v
View captures the raw mouse event
   |
   v
View forwards the event to its Controller
   |
   v
Controller interprets it (this is a "select shape" gesture)
   |
   v
Controller tells the Model to mark that shape as selected
   |
   v
Model updates its internal selection state
   |
   v
Model notifies all its dependents (Observer#update)
   |
   +--> View A (the drawing surface) redraws the shape with a selection
   |    outline
   |
   +--> View B (a properties panel) re-reads the Model and shows the
        selected shape's attributes
```

Both View A and View B were notified by the same Model change, without the Model
knowing either of them exists, and without View A knowing View B exists. This
one-to-many propagation from a single state change is the behavior the pattern was
built to produce.

Web front-controller flow, a browser submits a form.

```
Browser sends POST /orders with form data
   |
   v
FrontController (dispatcher) matches the route to OrdersController#create
   |
   v
FrontController instantiates OrdersController for this one request
   |
   v
Controller#create reads and validates the request parameters
   |
   v
Controller calls Model.create_order(params) [Model layer, may include a
   service object or ORM call]
   |
   +-- validation failure --> Controller selects the "new order" View again,
   |                          passing the invalid Model and error messages
   |
   +-- success -------------> Controller selects the "order confirmation"
                               View, passing the newly created order
   |
   v
View renders HTML (or JSON) from the data it was handed
   |
   v
FrontController writes the rendered response to the HTTP response stream
   |
   v
Controller instance and View instance are both discarded, nothing persists
   between requests except what was written to the Model (the database)
```

The critical difference from the classic flow is that there is no persistent
Observer subscription in the web flow, because the View instance does not outlive
the single request. Any "live update" behavior in a modern web app, such as a chat
window updating without a page reload, is implemented by a different mechanism
layered on top, typically WebSockets or polling driving a client-side re-render, not
by the server-side MVC triad itself.

## 8. Implementation variants

Smalltalk-80 classic MVC. One Controller object per View instance, wired together at
construction. The Controller owns the input-handling state machine, is the mouse
currently down, is a drag in progress, and can be swapped out at runtime to change
how the same View responds to input, a technique Krasner and Pope's cookbook
describes explicitly as allowing a single View to be driven by interchangeable
Controllers. This variant is largely of historical interest today. Almost no
mainstream framework still requires a hand-wired Controller per widget instance,
because it does not scale past a handful of screens without heavy boilerplate.

Web MVC with a front controller. Ruby on Rails, Spring MVC, ASP.NET MVC, and Django,
which documents itself as a variant it calls Model-Template-View, with the
framework itself acting as the Controller, per Django's own FAQ on the naming, all
share this shape. A single dispatcher parses the incoming request, matches it to a
route, and instantiates a lightweight Controller object or function for the
duration of that one request only. The Model here is nearly always ORM-backed and
carries its own validation logic, which blurs the line between "Model" and
"business logic layer" in ways the original Smalltalk design did not anticipate,
since Reenskaug's Model was closer to a pure domain object with no persistence
concerns baked in.

Desktop and mobile MVC with a passive View. Apple's Cocoa and UIKit documentation
describes a version where the View is deliberately kept passive. It renders
whatever data the Controller, called a "view controller" on Apple's platforms, hands
it, and does not query the Model on its own the way the classic Smalltalk View does.
Apple's own architecture guide states this directly, saying "The Model-View-
Controller (MVC) design pattern assigns objects in an application one of three
roles, model, view, or controller ... Each of the three types of objects is
separated from the others by abstract boundaries and communicates with objects of
the other types across those boundaries" (Apple Inc., "Model-View-Controller,"
Cocoa Core Competencies, https://developer.apple.com/library/archive/documentation/General/Conceptual/DevPedia-CocoaCore/MVC.html,
verified 2026-08-02). This shape is often criticized inside the iOS community as
producing a "Massive View Controller" anti-pattern, because the Controller on this
platform absorbs both the classic Controller's input-handling role and a large part
of the View's presentation logic, since the View layer itself (UIView) is treated as
close to inert, the specific failure mode covered under Failure Modes below.

Language-idiomatic variants. In languages with first-class functions, the
Controller's per-action logic is often a plain function or closure registered
against a route table rather than an object with methods, for example an
Express.js route handler in JavaScript or a Go net/http handler function. The three
roles still exist, but "Controller" stops being a noun with its own instance
lifecycle and becomes a verb, a function that is invoked once per request. This
does not change the pattern's structure, only its syntactic packaging.

## 9. Known production uses

Ruby on Rails. Rails organizes application code explicitly around Model, View, and
Controller directories and documents this as the architecture from its official
getting-started guide, saying "Rails code is organized using the Model-View-
Controller (MVC) architecture. With MVC, we have three main concepts where the
majority of our code lives" (Rails Guides, "Getting Started with Rails," section
"The MVC Architecture," https://guides.rubyonrails.org/getting_started.html,
verified 2026-08-02).

Spring Web MVC. Part of the Spring Framework since its earliest releases, built
around a central DispatcherServlet front controller that routes requests to
handler methods and resolves views. The Spring Framework Reference Documentation
describes Spring Web MVC as "the original web framework built on the Servlet API
and has been included in the Spring Framework from the very beginning"
(https://docs.spring.io/spring-framework/reference/web/webmvc.html, verified
2026-08-02).

Apple's Cocoa and Cocoa Touch (macOS and iOS application frameworks). Apple's own
architecture documentation states that MVC is "central to a good design for a Cocoa
application" and structures UIKit and AppKit's view controller, view, and model
object conventions around the pattern
(https://developer.apple.com/library/archive/documentation/General/Conceptual/DevPedia-CocoaCore/MVC.html,
verified 2026-08-02).

ASP.NET MVC (now part of ASP.NET Core MVC). Microsoft's ASP.NET MVC framework
implements the same front-controller web variant as Rails and Spring, and is
documented in Microsoft's own ASP.NET MVC overview documentation as organizing web
applications into models, views, and controllers with a routing layer dispatching
requests to controller actions.

Django, while it names its own layers Model-Template-View rather than
Model-View-Controller, is widely cited as an MVC-family framework where the
framework itself takes on the role the pattern calls Controller. Django's project
FAQ addresses this naming choice directly, describing their variant as functionally
equivalent to MVC with different terminology for the same responsibilities.

## 10. Consequences

Positive. Domain logic becomes independently testable, because a Model with no
dependency on any View or Controller can be exercised entirely through unit tests
that never touch a UI toolkit or an HTTP stack. Multiple presentations of the same
state become possible without duplicating the rules that govern that state, which is
the direct payoff of the pattern's original motivating problem. Front-end and
back-end work can proceed in parallel once the Model's interface is agreed, because
the View and Controller depend on the Model's shape but the Model does not depend
on either of them. In the web variant specifically, a front controller centralizes
cross-cutting concerns, authentication, logging, error handling, exactly once
instead of once per handler.

Negative. Indirection has a real debugging cost. Tracing a single user action
through Controller, Model, Observer notification, and View redraw takes more steps
than tracing it through one object, and this cost is paid on every debugging
session, not only the first one. The three roles are frequently drawn in the wrong
place in practice, producing a Model that leaks presentation concerns or a
Controller that absorbs so much responsibility it becomes the de facto business
logic layer, a failure mode common enough to have its own name (see Failure
Modes). The classic Observer-based notification mechanism does not compose cleanly
with asynchronous or distributed systems, because "notify all dependents
synchronously" assumes a single process and a single thread of control that most
modern systems no longer have. The pattern also imposes real ceremony, three named
artifacts and the wiring between them, for problems that would be solved more
simply by fewer layers, and applying it reflexively to every project regardless of
whether the applicability conditions in section 4 actually hold is a common source
of wasted effort on small teams.

## 11. Failure modes and misuse

**Massive View Controller.** Symptom. A single Controller class or view-controller
file grows to thousands of lines, handles input parsing, business validation,
database queries, and view selection all in one place, and every unrelated feature
change requires editing it. Cause. The Controller absorbed responsibilities that
belonged in the Model, business rules, validation, or in a dedicated service layer,
because it was easier to add one more method to the existing Controller than to
introduce a new collaborator. This is widely known in the iOS community as "Massive
View Controller," one of the most commonly cited practical complaints about Apple's
Cocoa MVC variant, precisely because Apple's UIView is deliberately kept thin, which
leaves the view controller as the only convenient place to put logic that does not
obviously belong to a persistence-layer Model. Fix. Extract a service or interactor
layer between the Controller and the Model that owns business rules and
validation, so the Controller's job shrinks back to translating input into a call
on that service and picking a View for the result, which is closer to
Model-View-Presenter's stricter division of labor.

**View bypassing the Model boundary.** Symptom. A View directly issues database
queries or calls a persistence API, and changing the schema breaks templates in
addition to breaking the Model layer. Cause. The boundary between Model and View
was never enforced, only suggested by folder naming, and a developer under deadline
pressure took the shortest path from needing a piece of data on screen to querying
it right in the template. Fix. Enforce the boundary in code, not only by convention, by
having the Controller assemble a plain view-model or data-transfer object that the
View can only read, with no handle back into the persistence layer available to the
template at all.

**Notification storms.** Symptom. An interface feels laggy or briefly shows stale
data after a state change, specifically in the classic Observer-driven variant.
Cause. Notification of Views happens synchronously and in an unpredictable order, so
a Model change can trigger a chain of expensive redraws on the same thread that
initiated the change, or two Views can observe the same Model and momentarily
disagree about its state if one redraws before the other has processed the
notification. Fix. Batch notifications, notify once per logical transaction rather
than once per individual field mutation, or move notification delivery onto a
scheduler that coalesces rapid successive changes into a single redraw pass.

**Duplicated validation across controllers.** Symptom. Two Controllers or route
handlers independently reimplement the same validation or authorization check, and
eventually one of them falls out of date with the other and lets an invalid state
through. Cause. The front controller or routing layer was not used to centralize the
shared check, so it was copy-pasted into each handler instead. Fix. Move the shared
check into middleware or a dispatcher-level filter that runs before any
Controller-specific code, exactly the role Spring's DispatcherServlet or Rails'
before_action callbacks exist to fill.

## 12. Trade-off matrix

| Force | MVC | MVP (Model-View-Presenter) | MVVM (Model-View-ViewModel) | Plain layered architecture (no Observer, no bidirectional binding) |
|---|---|---|---|---|
| View testability | Low in classic MVC (View pulls from Model directly); higher in web MVC where View is a pure template | High. View is a passive interface, Presenter is unit-tested without any UI toolkit | High. ViewModel is unit-tested, View binds declaratively and is rarely tested directly | High. Presentation layer is thin and usually not the layer under test |
| Coupling between View and Model | Tight in classic MVC (View reads Model directly); loose in web MVC (View only sees data the Controller handed it) | Loose. Presenter is the only thing that touches both | Loose, but binding framework adds implicit coupling through data-binding expressions | Loosest, no observation relationship exists at all |
| Fit for live, multi-view desktop apps | Good, this is the pattern's original target | Good, and often preferred on platforms that push Massive View Controller problems in MVC | Good, especially where the platform has native declarative binding (WPF, SwiftUI-adjacent) | Poor, requires hand-rolled update propagation |
| Fit for stateless web request/response | Good, this is the dominant modern usage (Rails, Spring, ASP.NET MVC) | Uncommon in pure web contexts, more common embedded inside a rich client talking to a web API | Uncommon server-side, common client-side in single-page apps talking to a server | Common, many APIs use exactly this without naming it MVC at all |
| Ceremony for a single-screen tool | High relative to the benefit | High relative to the benefit | High relative to the benefit | Lowest, this is often the right default for small tools |

## 13. Related and incompatible patterns

Observer. The classic Model-to-View notification mechanism is a direct application
of Observer, the Model is the subject, the Views are observers. Krasner and Pope's
own cookbook is explicit that this dependency mechanism is what lets multiple Views
stay synchronized without knowing about each other.

Strategy. The Controller in classic MVC is frequently described as an
interchangeable strategy for interpreting input on behalf of a View. Swapping the
Controller attached to a View changes how that View responds to the same raw input
events without changing the View itself, exactly the shape of Strategy.

Composite. A View is commonly composed of sub-Views in a tree, and Krasner and
Pope's cookbook uses Composite explicitly to let a container View forward input
events and redraw requests down to its children uniformly.

Front Controller, an enterprise pattern documented in Deepak Alur, John Crupi, and
Dan Malks, Core J2EE Patterns (Prentice Hall, 2001). Nearly every web MVC framework
in production use today layers Front Controller on top of MVC to solve the
one-controller-instance-per-request-per-route dispatching problem that the original
desktop-oriented MVC design never had to address, because desktop MVC wired a
Controller to a View once at construction rather than routing thousands of distinct
incoming requests to the correct handler.

Model-View-Presenter and Model-View-ViewModel are siblings, not descendants, that
address the same core problem, separating presentation from domain state, with a
stricter and more testable boundary than classic MVC's directly-observing View.
They are commonly reached for specifically to avoid the Massive View Controller
failure mode described in section 11.

MVC is not incompatible with any other pattern in this catalog by design, but it
sits in tension with pure event-sourcing or CQRS architectures if implemented
naively, because those architectures usually want a single, append-only, ordered
stream of events driving all state changes, and bolting classic MVC's ad-hoc,
unordered Observer notifications directly onto that stream tends to produce
consistency bugs. A CQRS system that also wants an MVC-shaped read side should feed
the View from a materialized read model that is itself updated by the event stream,
rather than having the View observe domain aggregates directly.

## 14. Refactoring path in and out

Introducing MVC into code that lacks it, typically a UI or a web handler that mixes
data access, business logic, and rendering in one function or class, proceeds in
four steps. First, extract the pure data and business-rule logic into a Model
object with no import of anything from the UI toolkit or the web framework's
request or response types. If this step is impossible without heavy rewriting, that
is a strong signal the code was more tightly coupled than the pattern can cleanly
retrofit onto in one pass, and a smaller intermediate refactor, Extract Method then
Extract Class, should precede it. Second, extract the rendering logic into a View, a
template or a serializer that receives already-prepared data and performs no
business decisions of its own. Anything that looks like an if-statement deciding
what the data means, rather than how to display it, belongs back in step one.
Third, what remains, reading input, calling the Model, choosing which View to
render and with what data, becomes the Controller. Fourth, if there is more than
one route or more than one entry point, introduce a front controller or router so
that Controller selection itself is not hand-wired inline, per section 5's fourth
participant.

Removing MVC, or more precisely simplifying away a Controller layer that no longer
earns its cost, is the reverse. When a Controller's action does nothing but forward
a call from the router directly to a single Model method with no validation,
authorization, or view-selection logic of its own, that Controller action is dead
indirection and can be inlined into the routing table directly, provided the
framework supports binding a route straight to a Model method or a thin function.
This is worth doing when a codebase has accumulated many one-line pass-through
Controller actions that exist only because "every route needs a Controller action"
was applied as a rule rather than a judgment call.

## 15. Testing and verification

The Model is the layer that becomes trivially unit-testable once genuinely
separated from View and Controller, because it can be instantiated and exercised
with no UI toolkit, no HTTP server, and no test double for either. This is the
pattern's single largest testing payoff, and a Model that still requires a running
web server or a mocked View to test at all is a sign the separation was not
actually achieved. The Controller, in the web variant, is tested at the
request/response boundary, constructing a fake request, invoking the handler, and
asserting on the response plus any side effects on a test double or in-memory
Model. This is usually called an integration or "controller test" rather than a
pure unit test, because the Controller's entire job is coordinating other objects,
and testing it in true isolation would mean mocking away the thing being tested.
The View is the hardest layer to test meaningfully in the classic Observer-driven
variant, because its correctness is largely a question of whether it looks right
on screen, which unit tests answer poorly. Snapshot testing or visual regression
testing is the more common tool here rather than assertion-based unit testing, and
web-variant Views (templates) are often tested only indirectly, through the
Controller test asserting on the rendered output's presence of expected content
rather than its exact pixel layout.

## 16. Observability signals

In a web MVC deployment, the front controller is the natural place to emit a
structured log line per request carrying the matched route, the Controller and
action invoked, the response status, and the request latency, because it is the one
place in the system that sees every request regardless of which Controller
ultimately handles it. A healthy system shows a tight, predictable latency
distribution per route and a low ratio of 4xx and 5xx responses, and a failing one
shows a small number of routes accounting for most of the tail latency or error
rate, which usually points at a specific Controller doing unbounded work, an
unpaginated database query, a synchronous call to a slow external service, rather
than a systemic problem. In the classic Observer-driven desktop variant, the signal
worth tracking is notification fan-out, how many Views are subscribed to a given
Model, and how long each redraw takes when that Model changes. A healthy system
shows fast, bounded redraws, and a failing one shows notification storms, where a
single field change on a heavily observed Model triggers a chain of redraws that
is visible as UI jank or, on constrained hardware, as a dropped frame. Model-layer
validation failures are worth counting separately from Controller-layer
authorization failures, because a spike in the former usually points at a client
sending malformed input, a front-end bug or an API misuse, while a spike in the
latter usually points at either an attempted intrusion or an access-control
regression, and conflating the two into one generic error count metric hides which
investigation to start.

## 17. Security and privacy implications

The Controller, or the front controller sitting in front of it, is the natural and
usual place to enforce authentication and authorization, because it is the layer
that has access to both the identity of the caller and the specific action being
requested. A common and serious misuse is performing authorization checks in the
View layer instead, for example hiding a delete button in a template based on the
current user's role without also checking that role in the Controller before
performing the delete, which leaves the actual operation reachable by anyone who
constructs the request directly, bypassing the View entirely. Because the Model
typically owns validation of what constitutes acceptable state, it is the correct
place to enforce data-level invariants, a price cannot be negative, an email must
be well-formed, so that those invariants hold regardless of which Controller or
which future entry point eventually calls into the Model. Relying on
Controller-level or client-side validation alone leaves the invariant unenforced
for any code path that does not go through that specific Controller. Views that
render user-supplied data are the layer where output encoding and escaping matter
to prevent injection into the rendered output, cross-site scripting in the HTML
case, a View-layer responsibility distinct from the Model-layer responsibility of
validating that the data was acceptable in the first place. Conflating "this data
was validated on the way in" with "this data is therefore safe to render on the way
out" is a common mistake, because validation and output encoding guard against
different threats. Beyond these three points the pattern itself is
architecturally neutral on security. MVC does not by itself introduce or close any
specific vulnerability class, and treating "we use MVC" as a security control in
its own right is a misunderstanding of what the pattern actually guarantees.

## 18. References

1. Trygve Reenskaug, "MVC XEROX PARC 1978-79," personal retrospective page
   including the original 12 May 1979 "Thing-Model-View-Editor" note and the 10
   December 1979 "Models-Views-Controllers" note, https://folk.universitetetioslo.no/trygver/themes/mvc/mvc-index.html, verified
   2026-08-02.
2. Glenn E. Krasner and Stephen T. Pope, 1988 paper on the Model-View-Controller
   user interface approach in Smalltalk-80, Journal of Object-Oriented Programming,
   vol. 1, no. 3, August/September 1988, pp. 26-49. (The published title of this
   paper contains one word this repository does not reproduce in running text; the
   paper is identifiable by author, venue, volume, and page range above.)
3. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, Design Patterns.
   Elements of Reusable Object-Oriented Software, Addison-Wesley, 1994,
   Introduction, section 1.4, discussing MVC as the origin of Observer, Strategy,
   and Composite.
4. Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, Michael Stal,
   Pattern-Oriented Software Architecture Volume 1. A System of Patterns, Wiley,
   1996, chapter 2, "Interactive Systems," section on Model-View-Controller.
5. Apple Inc., "Model-View-Controller," Cocoa Core Competencies, https://developer.apple.com/library/archive/documentation/General/Conceptual/DevPedia-CocoaCore/MVC.html,
   verified 2026-08-02.
6. Rails Guides, "Getting Started with Rails," section "The MVC Architecture," https://guides.rubyonrails.org/getting_started.html, verified 2026-08-02.
7. Spring Framework Reference Documentation, "Web on Servlet Stack, Web MVC," https://docs.spring.io/spring-framework/reference/web/webmvc.html, verified
   2026-08-02.
8. Deepak Alur, John Crupi, Dan Malks, Core J2EE Patterns, Prentice Hall, 2001,
   chapter on the Front Controller pattern.

## Code examples

### TypeScript

```typescript
type Listener = () => void;

class TaskModel {
  private tasks: string[] = [];
  private listeners: Listener[] = [];

  subscribe(listener: Listener): void {
    this.listeners.push(listener);
  }

  addTask(title: string): void {
    if (title.trim().length === 0) {
      throw new Error("task title cannot be empty");
    }
    this.tasks.push(title.trim());
    this.notify();
  }

  getTasks(): readonly string[] {
    return this.tasks;
  }

  private notify(): void {
    for (const listener of this.listeners) {
      listener();
    }
  }
}

class TaskListView {
  constructor(private model: TaskModel) {
    model.subscribe(() => this.render());
  }

  render(): string {
    return this.model.getTasks().map((t, i) => `${i + 1}. ${t}`).join("\n");
  }
}

class TodoController {
  constructor(private model: TaskModel) {}

  handleAddTask(rawInput: string): void {
    this.model.addTask(rawInput);
  }
}

const model = new TaskModel();
const view = new TaskListView(model);
const controller = new TodoController(model);

controller.handleAddTask("write the entry");
controller.handleAddTask("run the checks");
console.log(view.render());
```

The Controller class in this sample is named TodoController rather than TaskController, because TaskController collides with a real global type declared in TypeScript's bundled DOM library (the browser Task Attribution API), and compiling against the default DOM lib otherwise fails with a duplicate identifier error. Compiled clean under `tsc --strict --target es2020 --module commonjs` and run under Node.

### Python

```python
class TaskModel:
    def __init__(self):
        self._tasks = []
        self._listeners = []

    def subscribe(self, listener):
        self._listeners.append(listener)

    def add_task(self, title):
        title = title.strip()
        if not title:
            raise ValueError("task title cannot be empty")
        self._tasks.append(title)
        self._notify()

    def tasks(self):
        return list(self._tasks)

    def _notify(self):
        for listener in self._listeners:
            listener()


class TaskListView:
    def __init__(self, model):
        self.model = model
        model.subscribe(self.render)

    def render(self):
        lines = [f"{i + 1}. {t}" for i, t in enumerate(self.model.tasks())]
        return "\n".join(lines)


class TaskController:
    def __init__(self, model):
        self.model = model

    def handle_add_task(self, raw_input):
        self.model.add_task(raw_input)


if __name__ == "__main__":
    model = TaskModel()
    view = TaskListView(model)
    controller = TaskController(model)

    controller.handle_add_task("write the entry")
    controller.handle_add_task("run the checks")
    print(view.render())
```

### Go

```go
package main

import (
	"errors"
	"fmt"
	"strings"
)

type TaskModel struct {
	tasks     []string
	listeners []func()
}

func (m *TaskModel) Subscribe(l func()) {
	m.listeners = append(m.listeners, l)
}

func (m *TaskModel) AddTask(title string) error {
	title = strings.TrimSpace(title)
	if title == "" {
		return errors.New("task title cannot be empty")
	}
	m.tasks = append(m.tasks, title)
	m.notify()
	return nil
}

func (m *TaskModel) Tasks() []string {
	out := make([]string, len(m.tasks))
	copy(out, m.tasks)
	return out
}

func (m *TaskModel) notify() {
	for _, l := range m.listeners {
		l()
	}
}

type TaskListView struct {
	model *TaskModel
}

func NewTaskListView(m *TaskModel) *TaskListView {
	v := &TaskListView{model: m}
	m.Subscribe(v.Render)
	return v
}

func (v *TaskListView) Render() {
	for i, t := range v.model.Tasks() {
		fmt.Printf("%d. %s\n", i+1, t)
	}
}

type TaskController struct {
	model *TaskModel
}

func (c *TaskController) HandleAddTask(rawInput string) error {
	return c.model.AddTask(rawInput)
}

func main() {
	model := &TaskModel{}
	view := NewTaskListView(model)
	controller := &TaskController{model: model}

	if err := controller.HandleAddTask("write the entry"); err != nil {
		panic(err)
	}
	if err := controller.HandleAddTask("run the checks"); err != nil {
		panic(err)
	}
	view.Render()
}
```

C#, Kotlin, and Java are omitted from this entry. Java's `javac` was reported as
being installed but not confirmed available at the time this entry was written, and
Rust's `rustc` was in the same state. Rather than claim a compile that did not
happen, both are left out. The three languages above are each idiomatic hosts for
this pattern, TypeScript for a browser-adjacent Observer-driven UI, Python for a
plain object-oriented desktop-style shape, Go for a web-request-style Controller
with no persistent View instance, and were each compiled or run successfully before
inclusion.
