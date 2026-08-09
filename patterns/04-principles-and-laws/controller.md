---
name: Controller
slug: controller
family: 04-principles-and-laws
category: Principle
aliases: [GRASP Controller, Use Case Controller, Facade Controller, Front Controller related not identical]
first_described: "Larman 1997, Applying UML and Patterns, 1st edition"
maturity: canonical
related: [information-expert, creator, single-responsibility-principle, interface-segregation-principle, dependency-inversion-principle]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Controller, one of nine responsibility-assignment
patterns Craig Larman collected under the acronym GRASP, General Responsibility
Assignment Software Patterns, in the first edition of his book Applying UML and
Patterns, published in 1997. Verified against the Wikipedia summary of GRASP,
which lists Controller among the nine patterns alongside Information Expert,
Creator, Low Coupling, High Cohesion, Polymorphism, Pure Fabrication,
Indirection, and Protected Variations
(https://en.wikipedia.org/wiki/GRASP_(object-oriented_design), verified
2026-08-02). The same source gives the pattern's own definition, saying it
"assigns the responsibility of dealing with system events to a non-UI class
that represents the overall system or a use case scenario," and describes the
controller as "the first object beyond the UI layer that receives and
coordinates a system operation," a role that should delegate work to other
objects rather than perform much of the work itself.

Larman's Controller predates and is distinct from, though closely related to,
the Front Controller pattern documented later by Deepak Alur, John Crupi, and
Dan Malks in Core J2EE Patterns, and popularized independently in Martin
Fowler's Patterns of Enterprise Application Architecture. Front Controller
names a specific architectural device, a single entry-point object that
receives every incoming request for a whole application and dispatches it to
the right handler. GRASP Controller is broader and lower level, a
responsibility-assignment heuristic that says system events belong on a
non-UI coordinating object, and it applies whether that object is a single
front controller for the whole application or one controller per use case.
This entry treats GRASP Controller as the primary subject and Front Controller
as a named implementation variant, covered in dimension 8.

Two named variants of GRASP Controller appear consistently across the
literature. Larman's own text, summarized in the Wikipedia GRASP article,
distinguishes a use case controller, which represents a single use case or a
small family of closely related use cases and handles all the system events
for that use case, from a facade controller, which represents the overall
system, the overall device, or a subsystem and handles all system events for
it as a single coarse-grained object
(https://en.wikipedia.org/wiki/GRASP_(object-oriented_design), verified
2026-08-02). Neither variant has a further alternate name in wide use. The
term controller itself is heavily overloaded in the industry, and this
entry is careful throughout to distinguish the GRASP responsibility-assignment
principle from the Model-View-Controller architectural pattern's Controller
role, which is related but was described earlier and independently by
Trygve Reenskaug's 1979 Smalltalk work at Xerox PARC, and from the base
Controller classes shipped by web frameworks such as Spring MVC, Ruby on
Rails, and ASP.NET Core MVC. Dimension 9 covers those framework instances as
production applications of the same underlying idea, because in every one of
those frameworks the shipped Controller base class exists to satisfy exactly
the responsibility GRASP names, receive an external event, do not do the
domain work yourself, delegate to the objects that hold the information and
the behavior.

## 2. Problem and context

A team wiring a new interaction into an object-oriented system reaches a
concrete, recurring question the moment a user clicks a button, submits a
form, or an external system delivers a message. Something outside the domain
model, a UI widget, an HTTP request, a message queue consumer, has just
produced an event, and someone has to receive that event and turn it into a
call, or a sequence of calls, on the objects that actually know how to handle
it. The question is where that receiving object lives, and what it is allowed
to do once it has the event in hand.

Two default answers recur across immature codebases and both create damage
that is invisible in the first commit and expensive within a year. The first
default puts the handling code directly inside the UI layer, a button's click
handler, an HTTP route closure, a servlet's doPost method, which then reaches
straight into the domain objects and performs validation, business rules, and
persistence inline. This couples the application's actual behavior to
whichever delivery mechanism happens to be in front of it that day. Web,
CLI, and test suite each get their own copy of the same logic, and the
logic can never be exercised without also standing up the UI framework, which
is precisely the failure Larman was naming when he asked, in the words the
GRASP literature attributes to him, who should be responsible for handling an
input system event.

The second default goes the other way and puts the domain objects themselves
in direct contact with the UI, letting a Customer or an Order object read
form fields, populate an HTTP response, or otherwise reach outward into the
presentation layer. This is arguably worse, because it means the domain
model, the part of the system meant to be the most stable and the most
reusable across delivery channels, is now coupled to the least stable part of
the system, the UI technology, which changes with fashion far more often than
business rules do.

Controller names the third option and gives it a concrete home. Introduce a
non-UI object, one that is not itself the domain model and not itself the
presentation layer, whose sole job is to sit between the two, receive the
system event, and coordinate the response by delegating to the objects that
actually hold the information and the behavior needed, per Information
Expert. The context in which this problem recurs is any system with more than
one delivery mechanism in mind, any system a team intends to unit test without
booting a UI, and any system where more than one team member will eventually
need to add a new use case without first understanding how the UI framework
routes events, which in practice is nearly every non-trivial application built
after the first prototype.

## 3. Forces

Judgement. The following weighing of forces is engineering reasoning drawn
from the GRASP literature and from observed practice, not a sourced fact.

Controller is a coordination point, and every coordination point concentrates
several competing pressures onto one class.

Coupling versus discoverability. Pushing event handling into a dedicated
controller reduces coupling between the UI and the domain, because the UI now
depends only on the controller's narrow interface and the domain depends on
nothing UI-related at all. The cost is an extra layer a new team member must
learn to find, since a bug that manifests in the UI now requires stepping
through one more hop before reaching the domain code that actually decides
the outcome.

Cohesion versus growth. A controller scoped to one use case, per Larman's use
case controller variant, stays small and focused, which keeps its own
cohesion high. But a system with hundreds of use cases and a policy of one
controller per use case produces hundreds of small classes, and the team must
then invest in naming and organizing conventions so that the right controller
is easy to find. A facade controller, one object representing a whole
subsystem, avoids that sprawl but risks becoming a God Object as more and more
event-handling responsibility accretes onto it, which is precisely the
failure mode Larman warned against and which dimension 11 covers directly.

Testability versus indirection. A controller that does nothing but delegate
is trivial to test with mocks or fakes standing in for its collaborators, and
it lets the domain logic underneath be tested completely independently of any
UI. The cost is an added layer of indirection between an integration test
that exercises the real UI and the unit tests that exercise the domain, so
end-to-end confidence still requires a separate, slower test that walks the
full path.

Statelessness versus session affinity. Many controller implementations in web
frameworks are deliberately stateless, request-scoped objects instantiated
fresh per request specifically so that horizontal scaling and concurrent
requests need no special handling. The ASP.NET Core documentation states
controllers "are activated and disposed on a per request basis"
(https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/actions,
verified 2026-08-02). This favors operability and scalability but forces any
state a use case needs across multiple events into an explicit session,
cache, or persistence mechanism the controller must consult, rather than
letting the controller itself remember anything between calls.

Cognitive load versus explicit workflow. A dedicated controller makes the
sequence of steps in a use case explicit and readable in one place, which
lowers cognitive load for a reader trying to understand what a given action
does end to end. The competing cost is that this explicitness can tempt
developers to write the actual business logic inline inside the controller,
because the controller is already the place where the whole sequence is
visible, which is the single most common misuse of the pattern and is covered
in dimension 11.

## 4. Applicability and non-applicability

Reach for Controller when the following hold.

1. The system has more than one delivery mechanism, actual or planned, for
   the same use cases, a web UI and a CLI, a REST API and a message consumer,
   because a controller layer is what lets the domain logic be reused across
   all of them unchanged.
2. The team wants to unit test business rules without booting the UI
   framework, since a controller that only coordinates leaves the actual
   rules in domain objects that a plain unit test can exercise directly.
3. A use case involves coordinating more than one domain object across a
   sequence of steps, validation, then a domain operation, then a
   notification, and no single domain object is a natural home for that
   sequence.
4. The team is building on a web framework that already ships a Controller
   base class, Spring MVC, Rails, ASP.NET Core MVC, Django's function or
   class-based views, in which case the framework has already made the
   architectural decision and the remaining discipline is keeping the
   controller thin.
5. An external event, a webhook, a scheduled job, a queue message, needs a
   receiving object that translates the event into calls on the domain model
   without becoming part of the domain model itself.

Do not reach for Controller when the following hold instead.

1. The system is small enough, and will stay small enough, that a single
   entry point calling directly into two or three domain objects is easier to
   read than an extra layer of indirection would be. A script, a small CLI
   tool with one command, or a proof of concept does not need a controller
   layer, and adding one is premature structure that a reader has to learn
   for no payoff.
2. The event itself carries no coordination work, it is a single, direct
   call to a single domain method with no validation or sequencing beyond
   what the domain method already does itself. Wrapping a one-line
   delegation in a controller class adds a file and a name without adding
   any actual responsibility separation.
3. The team is building a pure functional core with an imperative shell, a
   style where the shell already plays the controller's coordinating role
   by construction, and introducing an additional named Controller class on
   top of the shell would duplicate a responsibility the architecture already
   assigns elsewhere.
4. The actual domain logic genuinely IS the same as the event-handling logic,
   as can happen in a very small event-sourced aggregate where the command
   handler and the aggregate are the same object by design, in which case
   forcing a separate controller layer fights the architecture rather than
   supporting it.
5. The system already has a message-bus or command-handler architecture, a
   CQRS command handler for example, that fulfills the same
   responsibility-assignment goal Controller exists to satisfy, receive an
   external instruction, do not embed business logic in the receiving code,
   delegate to the domain. Adding a GRASP-style controller on top of an
   already-explicit command handler is redundant naming, not additional
   structure.

## 5. Structure

| Participant | Responsibility |
|---|---|
| System event source | The UI widget, HTTP request, message, or scheduled trigger that originates the event the controller must handle. It has no knowledge of the controller's internals and depends only on the controller's public interface. |
| Controller | The non-UI coordinating object. Receives the system event, performs no business logic of its own beyond input translation and sequencing, and delegates each piece of real work to the collaborator that is the Information Expert for that piece. |
| Domain collaborators | The objects, aggregates, or services that hold the data and the behavior the use case actually needs. The controller calls these but does not replace their responsibilities. |
| Presentation or output boundary | The view, response object, or outbound message the controller hands the result to once the domain collaborators have finished, without the controller itself formatting or rendering that output beyond selecting which output to produce. |

The controller's structural role is deliberately thin, existing as a stable
seam between an unstable, frequently changing delivery mechanism and a domain
model that should not need to know that mechanism exists.

## 6. ASCII structure diagram

```
                +-------------------+
                |   Event Source    |
                |  (UI, HTTP route, |
                |   message queue)  |
                +---------+---------+
                          |
                          |  system event
                          v
                +-------------------+
                |     Controller     |
                |  (use case OR      |
                |   facade variant)  |
                +----+----------+----+
                     |          |
        delegates    |          |    delegates
                     v          v
          +-------------+   +-------------+
          |  Domain      |   |  Domain     |
          |  Collaborator|   |  Collaborator|
          |  A (Expert)  |   |  B (Expert) |
          +-------------+   +-------------+
                     |          |
                     +----+-----+
                          |
                          v
                +-------------------+
                |  Presentation /    |
                |  Output boundary   |
                +-------------------+
```

## 7. Dynamics

```
EventSource       Controller        DomainCollab_A     DomainCollab_B    Output
    |                  |                  |                  |             |
    | systemEvent()    |                  |                  |             |
    |----------------->|                  |                  |             |
    |                  | validate/parse   |                  |             |
    |                  |------------------|                  |             |
    |                  |                  |                  |             |
    |                  | doStepOne()      |                  |             |
    |                  |----------------->|                  |             |
    |                  |<-----------------|                  |             |
    |                  |     result A     |                  |             |
    |                  |                  |                  |             |
    |                  | doStepTwo(resultA)                  |             |
    |                  |------------------------------------->|             |
    |                  |<-------------------------------------|             |
    |                  |          result B                    |             |
    |                  |                                                    |
    |                  | present(resultB)                                  |
    |                  |--------------------------------------------------->|
    |                  |                                                    |
    |<-----------------|                                                    |
    |  response/ack    |                                                    |
```

The critical property the diagram is meant to show is that the controller
sits on the call path between the event source and every domain collaborator,
but it never contains the business rule that decides what doStepOne or
doStepTwo actually compute. It sequences, it does not decide.

## 8. Implementation variants

Judgement. The variants below are drawn from the GRASP literature's own
distinction plus widely observed framework practice, and the trade-offs
stated are engineering reasoning rather than a single sourced claim.

Use case controller. One controller per use case or per small family of
closely related use cases, for example PlaceOrderController and
CancelOrderController as separate classes even though both touch Order.
This keeps each controller small and gives it a name that documents exactly
what it does, at the cost of a growing number of classes as the number of use
cases grows. This is the variant Larman's own GRASP text favors for systems of
non-trivial size, per the Wikipedia GRASP summary
(https://en.wikipedia.org/wiki/GRASP_(object-oriented_design), verified
2026-08-02).

Facade controller. One controller representing an entire subsystem or the
whole application, handling every system event for that subsystem, for
example a single OrderManagementController handling placement,
modification, and cancellation together. This trades a smaller class count
for a controller whose responsibility list grows every time a new use case is
added, which is the direct path to the God Object failure mode in dimension
11 if left unchecked.

Front Controller. A single, application-wide entry point that every incoming
request passes through before being dispatched to a more specific handler.
Spring's own documentation states that Spring MVC "is designed around the
front controller pattern where a central Servlet, the DispatcherServlet,
provides a shared algorithm for request processing, while actual work is
performed by configurable delegate components"
(https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet.html,
verified 2026-08-02). Front Controller solves a different, complementary
problem, centralizing cross-cutting request-processing concerns such as
routing, authentication, and logging, and it typically dispatches onward to
per-use-case or per-resource controllers that then play the GRASP Controller
role Larman described.

Command Handler as controller. In a CQRS or event-sourced architecture, a
dedicated command handler class fulfills the same responsibility-assignment
role as a GRASP controller, receiving a command object and delegating to the
aggregate that owns the relevant state, without the handler containing the
business rule itself. The naming convention differs, but the underlying force
being balanced, keep the receiving object thin, is the same one Larman named.

Language-idiomatic variant, closures replacing controller classes. In
languages with first-class functions, a small use case can be represented as
a single function or lambda that receives the event and calls into the domain,
rather than as a class. This is common in Go HTTP handlers and in serverless
function-as-a-service platforms, where the controller is a single exported
function bound to a route rather than an instantiated object. The
responsibility split GRASP names is unchanged, only the syntactic container
is different.

## 9. Known production uses

1. Spring MVC's DispatcherServlet and the @Controller, @RestController
   annotated classes it dispatches to. Spring's reference documentation
   describes DispatcherServlet as implementing the front controller pattern,
   providing "a shared algorithm for request processing, while actual work is
   performed by configurable delegate components"
   (https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet.html,
   verified 2026-08-02), and documents @Controller annotated classes as the
   per-request-mapping handlers DispatcherServlet delegates to
   (https://docs.spring.io/spring-framework/reference/web/webmvc.html, verified
   2026-08-02).
2. Ruby on Rails Action Controller. The official Rails guide states plainly
   that "Action Controller is the C in the Model View Controller (MVC)
   pattern. After the router has matched a controller to an incoming request,
   the controller is responsible for processing the request and generating
   the appropriate output"
   (https://guides.rubyonrails.org/action_controller_overview.html, verified
   2026-08-02). Every Rails application defines its controllers as subclasses
   of the Rails ActionController base class, and Rails convention explicitly discourages
   putting persistence or business rule logic directly in controller actions,
   pushing that work to models and, in larger applications, dedicated service
   objects, which is the same thin-controller discipline GRASP names.
3. ASP.NET Core MVC's Controller base class. Microsoft's own documentation
   states that "within the Model-View-Controller pattern, a controller is
   responsible for the initial processing of the request and instantiation of
   the model. Generally, business decisions should be performed within the
   model," and describes the controller as a UI-level abstraction whose job
   is to check that request data is valid and to choose which view, or which
   result for an API, should be returned, adding that "in well-factored apps,
   it doesn't directly include data access or business logic. Instead, the
   controller delegates to services handling these responsibilities"
   (https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/actions,
   verified 2026-08-02). This is close to a restatement of the GRASP
   Controller definition, published by a completely independent engineering
   organization.
4. Django's request-handling view function, which the Django project's own
   FAQ explicitly maps onto the Controller concept from classic MVC. The
   Django FAQ states that in Django's architecture, "a view is the Python
   callback function for a particular URL, because that callback function
   describes which data is presented," and that the actual dispatching role,
   "the machinery that sends a request to the appropriate view, according to
   the Django URL configuration," is "probably the framework itself"
   (https://docs.djangoproject.com/en/5.2/faq/general/, verified 2026-08-02).
   This is a documented, named case where an entire framework consciously
   renamed the Controller role, model-template-view instead of
   model-view-controller, while keeping the underlying responsibility split
   GRASP describes.

## 10. Consequences

Positive.

1. The UI and the domain model become independently testable and
   independently replaceable, because neither depends directly on the other,
   they depend only on the controller's narrow interface.
2. Business logic gains a single, reusable home that every delivery
   mechanism can call, which is exactly what lets the same domain model back
   a web UI, a CLI, and an API without duplicating rules in each one.
3. The sequence of steps a use case performs becomes explicit and readable
   in one place, rather than scattered across event handlers, which helps a
   new team member trace what a given action actually does.
4. Cross-cutting concerns, authentication, logging, request validation, gain
   a natural attachment point at the controller or front-controller layer,
   without polluting the domain model with delivery-mechanism concerns.

Negative.

1. An extra layer of indirection exists on every call path, which a reader
   must learn to navigate before reaching the code that actually decides an
   outcome.
2. A poorly disciplined team will drift business logic into the controller
   over time, because the controller is the object with visibility into the
   whole sequence, producing the God Object failure mode covered in
   dimension 11.
3. Facade-style controllers accumulate responsibility as new use cases are
   added, and nothing in the pattern itself prevents that accumulation, the
   discipline to split a growing controller is a team practice, not a
   structural guarantee.
4. In frameworks where the controller is instantiated per request, state
   that genuinely needs to persist across a use case's multiple steps must be
   pushed into session storage, a cache, or the database, adding operational
   complexity that a stateful design would not need.

## 11. Failure modes and misuse

Judgement. The following symptom, cause, and fix triples are drawn from
observed practice across the frameworks named in dimension 9, not from a
single citable source.

Symptom. A single controller class has grown past several hundred lines,
handles a dozen unrelated actions, and every new feature request means
editing the same file.
Cause. A facade controller was chosen for convenience early on and was never
split as the number of use cases it handled grew, turning the coordinating
object into the classic God Object anti-pattern, where GRASP Controller's own
coordinating role has been stretched past the point Larman intended.
Fix. Split the facade controller into per-use-case controllers, following the
use case controller variant from dimension 8, grouping actions that share a
cohesive purpose and moving the rest into their own classes.

Symptom. Unit tests for a use case require standing up the web framework, a
real HTTP request, and a database, even though the test is meant to check a
business rule.
Cause. The actual business logic, validation and decision making, was
written directly inside the controller action method instead of being
delegated to domain objects, so testing the rule means testing the whole
controller and everything the framework wires around it.
Fix. Extract the decision logic into a domain object or a plain service
class the controller calls, per Information Expert, so the rule can be unit
tested directly and the controller test, if kept at all, only verifies that
delegation happened correctly.

Symptom. The same validation rule, or the same multi-step workflow, is
duplicated nearly verbatim across a REST controller and a CLI command, and
bug fixes routinely get applied to one copy and forgotten in the other.
Cause. Business logic was written inline in each delivery-specific
controller instead of in a shared domain layer both controllers call into,
defeating the entire reason to introduce a controller layer in the first
place.
Fix. Pull the duplicated logic into a shared domain service, and reduce both
controllers to thin adapters that translate their respective input formats
into calls on that shared service.

Symptom. Adding a new field to a form requires editing the controller, the
view, and the domain model, and the controller change is where most bugs get
introduced.
Cause. The controller is doing data transformation and mapping work that
properly belongs to a dedicated mapping or DTO layer, mixing input-translation
concerns with coordination concerns inside a single class.
Fix. Introduce an explicit request or command object and a mapper responsible
for the transformation, so the controller's own code stays limited to
receiving the already-parsed object and calling the domain.

Symptom. A controller reaches directly into a data access layer, an ORM
context, or a raw SQL call, bypassing the domain model entirely for
convenience on what seemed like a simple read.
Cause. The team treated the controller as a place any code could live,
rather than as a boundary that delegates strictly to the domain and the
persistence layers that domain exposes.
Fix. Route the read through a query object or a repository the domain model
or an explicit query service exposes, keeping the controller's only
knowledge of persistence indirect, through an interface it is handed.

## 12. Trade-off matrix

| Force | Controller per use case | Facade Controller | Front Controller alone, no per-use-case controller | Command Handler CQRS |
|---|---|---|---|---|
| Coupling to UI framework | Low, each controller is small and framework-agnostic aside from its entry point | Low to medium, same isolation but growing surface area | Medium, the single entry point concentrates framework-specific dispatch logic | Low, handler is UI-agnostic by construction |
| Class count and discoverability | High class count, but each class is self-documenting by name | Low class count, but harder to find the specific handling code inside a large class | Very low class count for entry points, dispatch logic can obscure where handling code lives | Moderate, one handler per command, similar profile to use case controller |
| Cohesion | High, each controller has one reason to change | Decreasing over time as use cases accumulate | Not applicable, front controller handles routing, not use case logic | High, one handler per command by design |
| Testability | High, small controller is trivial to test in isolation | Medium, testing one action still means loading the whole facade class | Low for business logic, since front controller is dispatch only | High, handler tested independently, similar to use case controller |
| Operability at scale | Straightforward, controllers are typically stateless and easy to scale horizontally | Same statelessness, but a hot facade controller can become a deployment bottleneck for changes | Front controller itself rarely changes, so it is a stable deployment unit | Straightforward, handlers are typically stateless |
| Team scalability, multiple developers | High, developers rarely collide since files are small and use-case-scoped | Low, multiple developers editing the same facade file collide frequently | Not applicable for business logic, applies to routing configuration only | High, similar profile to use case controller |

## 13. Related and incompatible patterns

Information Expert is the principle Controller depends on once the event has
been received, since the controller decides that a piece of work must
happen, and Information Expert decides which object actually performs it. A
controller that ignores Information Expert and performs the work itself is
the direct cause of the God Object failure mode in dimension 11.

Creator is the sibling GRASP pattern that governs which object is responsible
for constructing new instances the use case needs, for example a new Order
aggregate a PlaceOrderController must instantiate before delegating to it.
Controller and Creator frequently appear in the same use case, one deciding
who receives the event, the other deciding who builds the objects the event
requires.

Single Responsibility Principle is the class-level discipline that keeps a
controller from becoming a facade that has quietly accumulated many unrelated
reasons to change. Applying SRP to controllers is the mechanical justification
for preferring the use case controller variant, from dimension 8, once a
facade controller's responsibility list starts to sprawl.

Interface Segregation Principle governs the shape of the interface a
controller exposes to its event source and the interfaces it depends on from
its domain collaborators, keeping those interfaces narrow so that a change to
an unrelated use case does not force a recompile or a redeploy of a
controller that never used the changed part of the interface.

Dependency Inversion Principle is what allows a controller to depend on an
abstraction of its domain collaborators rather than a concrete
implementation, which is the mechanism that keeps the controller replaceable
and testable with fakes or mocks standing in for the real domain objects.

Front Controller, covered in dimension 8 as an implementation variant rather
than a separate related pattern, is close enough to GRASP Controller in name
that the two are frequently conflated. They are compatible and commonly
layered together, a front controller for application-wide dispatch and
cross-cutting concerns, with per-use-case GRASP controllers underneath it for
the actual coordination work.

No pattern in this family is structurally incompatible with Controller, since
the pattern is a responsibility-assignment heuristic rather than a structural
constraint, so it composes with essentially any architectural style, layered,
hexagonal, or event-driven, that separates an event source from a domain
model.

## 14. Refactoring path in and out

Introducing Controller into code that lacks it, step by step. First, locate
every place a UI event handler, an HTTP route closure, or a message consumer
callback currently calls directly into a domain object or performs business
logic inline. Second, for each such location, extract a new class, named
after the use case it represents, whose only public method takes the
translated event data and does nothing but call the domain collaborators in
sequence, mirroring the Extract Class refactoring for isolating a cohesive
set of responsibilities into their own type. Third, move any validation or
sequencing logic that was inline in the original event handler into this new
controller, verifying with each move that the moved logic performs no
decision that the domain itself should be making. Fourth, replace the
original event handler's body with a call to the new controller, leaving the
handler responsible only for translating the raw event, an HTTP request, a
UI callback argument, into whatever input type the controller expects.
Fifth, add unit tests directly against the new controller using fakes for its
domain collaborators, confirming the controller correctly sequences calls
without needing the original UI framework running.

Removing Controller when it no longer earns its place, step by step. First,
confirm the concern that justified introducing the controller no longer
applies, typically because the system has been reduced to a single delivery
mechanism and the team has decided multiple mechanisms are permanently out of
scope. Second, check that the controller's method bodies still contain only
delegation, no business logic, since inlining a controller that has
accumulated real logic would move that logic back into the UI layer, which is
a net loss even for a single-mechanism system. Third, inline the controller's
calls directly into the remaining event handler, following the reverse of
Extract Class, an Inline Class style refactoring, one call site at a time,
running the existing test suite after each inlining to confirm behavior is
unchanged. Fourth, delete the now-empty controller class and update any
dependency injection registration or test fixtures that referenced it.

## 15. Testing and verification

A controller written to the pattern's intent, doing coordination only, is
easy to unit test in isolation. Inject fakes or mocks for every domain
collaborator it calls, invoke its handling method with a representative event
payload, and assert on which collaborator methods were called, with which
arguments, and in what order, since the controller's entire job is that
sequencing. This is a behavior-verification test rather than a state-
verification test, and the mock or fake framework native to the language,
Jest's jest.fn() in TypeScript, unittest.mock in Python, Mockito in Java,
or Go's interface-based fakes, is normally sufficient without a specialized
tool.

What becomes easy to test because of the pattern is that domain logic
underneath the controller can be tested completely independently, with no
HTTP server, no UI framework, and no test double for the controller itself,
since the domain objects have no dependency on the controller in the first
place.

What becomes harder to test because of the pattern is that true end-to-end
behavior, the actual sequence a real user experiences from UI event through
controller through domain and back to a rendered response, now requires an
integration or end-to-end test that exercises the full stack, because the
unit tests for the controller and the unit tests for the domain, taken
separately, cannot by themselves prove the two are wired together correctly.
A minimal integration test suite that exercises each controller's happy path
against the real domain objects, with only external I/O such as the database
or network mocked, is the usual complement to the unit-level controller
tests.

A useful regression check specific to this pattern is a static or code-review
rule that flags any controller method exceeding a small line count, or
containing a conditional that branches on business data rather than on
input-shape validation, since either signal is an early indicator that
business logic has begun leaking into the controller, per the misuse pattern
in dimension 11.

## 16. Observability signals

A healthy controller layer shows a flat, predictable distribution of request
latency per action, since a controller doing pure coordination adds a small,
consistent overhead on top of whatever the domain collaborators themselves
take, rather than a wide variance that would suggest some actions are doing
unbounded work inline. Logging at the controller boundary should capture the
system event received, which use case or action was invoked, and the outcome,
success or the specific failure category, without logging the internal
decision-making detail that belongs to the domain layer's own instrumentation.

Tracing, where distributed tracing is in place, should show the controller
span as a thin parent span whose children are calls into the domain
collaborators, a repository, a domain service, an external integration, with
the controller's own span duration accounting for a small fraction of the
total, typically single-digit milliseconds of parsing and delegation
overhead. A controller whose own span duration grows to be a significant
fraction of total request time, with no identifiable child span accounting
for the difference, is direct observability evidence that logic has been
written inline in the controller rather than delegated, again pointing back
to dimension 11's God Object failure mode.

A dashboard tracking exception or error rates per controller action, broken
out by action rather than aggregated across the whole application, makes it
possible to see when a single facade controller is responsible for a
disproportionate share of total errors, which is an operational signal that
the facade has grown too large and heterogeneous to reason about as one unit,
supporting the case to split it per dimension 14's refactoring path.

## 17. Security and privacy implications

Judgement. The security implications below are analytical reasoning about
where a controller sits in the request path, not sourced claims about a
specific vulnerability.

Because a controller is, by definition, the first non-UI object to receive an
external system event, it is also the natural and correct place to perform
input validation, authentication checks, and authorization checks before any
domain logic runs, since the domain model should generally be able to trust
that data reaching it has already been validated for shape and that the
caller has already been authenticated. Placing these checks anywhere further
downstream, inside the domain model itself, means every domain method has to
independently defend against malformed or unauthorized input, duplicating
that defense across many classes instead of centralizing it at the one seam
that already exists for exactly this purpose.

The framework instances named in dimension 9 largely encode this
expectation directly. ASP.NET Core's model binding and validation attributes,
Rails' strong parameters, and Spring MVC's @Valid annotated method
parameters all attach validation to the controller layer specifically, which
means a controller that skips or bypasses the framework's validation
machinery, accepting raw, unvalidated input and passing it straight to the
domain, reintroduces the injection and mass-assignment risks those mechanisms
exist to close.

Because the controller sits directly on the boundary between untrusted input
and trusted domain logic, it is also the layer most exposed to logging
sensitive data by accident, request bodies, headers, or query parameters that
may contain credentials or personal data logged at the controller boundary
for debugging purposes. A controller's own instrumentation, per dimension 16,
should log the shape of the event and its outcome, not the raw payload
verbatim, unless the payload has already been scrubbed of anything sensitive.

Controller is otherwise silent on data-at-rest encryption, transport
security, and cryptographic concerns, which belong to the layers the
controller delegates to and to the transport mechanism, TLS termination for
example, that sits in front of it.

## 18. References

1. Wikipedia. GRASP object-oriented design.
   https://en.wikipedia.org/wiki/GRASP_(object-oriented_design). Verified
   2026-08-02. Source for the GRASP acronym's origin with Craig Larman's 1997
   Applying UML and Patterns, the list of nine GRASP patterns, and the
   Controller pattern's own definition and use-case-versus-facade variant
   split.
2. Spring Framework reference documentation. Web on Servlet Stack, Spring
   Web MVC. https://docs.spring.io/spring-framework/reference/web/webmvc.html.
   Verified 2026-08-02. Source for DispatcherServlet and @Controller
   annotated classes as the Spring MVC implementation of the Controller and
   Front Controller roles.
3. Spring Framework reference documentation. DispatcherServlet.
   https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet.html.
   Verified 2026-08-02. Source for the direct quotation describing
   DispatcherServlet as implementing the front controller pattern.
4. Ruby on Rails Guides. Action Controller Overview.
   https://guides.rubyonrails.org/action_controller_overview.html. Verified
   2026-08-02. Source for the definition of Action Controller as the C in
   Model-View-Controller and its request-processing responsibility.
5. Microsoft Learn. Handle requests with controllers in ASP.NET Core MVC.
   https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/actions.
   Verified 2026-08-02. Source for ASP.NET Core's Controller class
   definition, its per-request activation and disposal, and the explicit
   statement that controllers should delegate business logic to services
   rather than perform it directly.
6. Django Software Foundation. Django FAQ, General questions.
   https://docs.djangoproject.com/en/5.2/faq/general/. Verified 2026-08-02.
   Source for Django's own explanation of why it names the Controller role
   differently, and its mapping of the MTV naming onto classic MVC roles.

## Code examples

Three languages are shown, each implementing the same use case controller,
CancelOrderController, coordinating a single Order aggregate through an
injected repository. TypeScript and Go are chosen because their strong,
explicit typing makes the controller's narrow interface to its collaborators
easy to see at a glance. Python is chosen because it is the most common
language for the Django and Flask family of frameworks named in dimension 9.
Java is omitted from the runnable set here only because the three above
already cover the class-based, interface-based, and duck-typed variations of
the same idea, not because the pattern translates poorly to Java, where it is
in fact the dominant idiom via Spring MVC as shown in dimension 9.

All three samples were compiled or executed directly before inclusion.
TypeScript with `tsc --strict` and executed with `node`. Python executed
directly with `python3`. Go executed with `go run`. Each produced the
expected output, a success result for an existing pending order and a
not-found result for a missing order.

TypeScript.

```typescript
interface OrderRepository {
  findById(id: string): Order | undefined;
  save(order: Order): void;
}

class Order {
  constructor(public id: string, public status: string, public total: number) {}
  cancel(): void {
    if (this.status === "shipped") {
      throw new Error("cannot cancel a shipped order");
    }
    this.status = "cancelled";
  }
}

class CancelOrderController {
  constructor(private repo: OrderRepository) {}

  handle(orderId: string): { ok: boolean; message: string } {
    const order = this.repo.findById(orderId);
    if (!order) {
      return { ok: false, message: "order not found" };
    }
    try {
      order.cancel();
    } catch (e) {
      return { ok: false, message: (e as Error).message };
    }
    this.repo.save(order);
    return { ok: true, message: "order cancelled" };
  }
}

class InMemoryOrderRepository implements OrderRepository {
  private store = new Map<string, Order>();
  add(order: Order): void {
    this.store.set(order.id, order);
  }
  findById(id: string): Order | undefined {
    return this.store.get(id);
  }
  save(order: Order): void {
    this.store.set(order.id, order);
  }
}

const repo = new InMemoryOrderRepository();
repo.add(new Order("A1", "pending", 42));
const controller = new CancelOrderController(repo);
console.log(controller.handle("A1"));
console.log(controller.handle("missing"));
```

Python.

```python
from dataclasses import dataclass


class OrderNotFound(Exception):
    pass


class InvalidTransition(Exception):
    pass


@dataclass
class Order:
    id: str
    status: str
    total: float

    def cancel(self) -> None:
        if self.status == "shipped":
            raise InvalidTransition("cannot cancel a shipped order")
        self.status = "cancelled"


class InMemoryOrderRepository:
    def __init__(self):
        self._store = {}

    def add(self, order: Order) -> None:
        self._store[order.id] = order

    def find_by_id(self, order_id: str) -> Order:
        order = self._store.get(order_id)
        if order is None:
            raise OrderNotFound(order_id)
        return order

    def save(self, order: Order) -> None:
        self._store[order.id] = order


class CancelOrderController:
    def __init__(self, repo: InMemoryOrderRepository):
        self._repo = repo

    def handle(self, order_id: str) -> dict:
        try:
            order = self._repo.find_by_id(order_id)
        except OrderNotFound:
            return {"ok": False, "message": "order not found"}
        try:
            order.cancel()
        except InvalidTransition as e:
            return {"ok": False, "message": str(e)}
        self._repo.save(order)
        return {"ok": True, "message": "order cancelled"}


if __name__ == "__main__":
    repo = InMemoryOrderRepository()
    repo.add(Order("A1", "pending", 42.0))
    controller = CancelOrderController(repo)
    print(controller.handle("A1"))
    print(controller.handle("missing"))
```

Go.

```go
package main

import (
	"errors"
	"fmt"
)

type Order struct {
	ID     string
	Status string
	Total  float64
}

func (o *Order) Cancel() error {
	if o.Status == "shipped" {
		return errors.New("cannot cancel a shipped order")
	}
	o.Status = "cancelled"
	return nil
}

type OrderRepository interface {
	FindByID(id string) (*Order, bool)
	Save(o *Order)
}

type InMemoryOrderRepository struct {
	store map[string]*Order
}

func NewInMemoryOrderRepository() *InMemoryOrderRepository {
	return &InMemoryOrderRepository{store: make(map[string]*Order)}
}

func (r *InMemoryOrderRepository) Add(o *Order) {
	r.store[o.ID] = o
}

func (r *InMemoryOrderRepository) FindByID(id string) (*Order, bool) {
	o, ok := r.store[id]
	return o, ok
}

func (r *InMemoryOrderRepository) Save(o *Order) {
	r.store[o.ID] = o
}

type Result struct {
	OK      bool
	Message string
}

type CancelOrderController struct {
	repo OrderRepository
}

func NewCancelOrderController(repo OrderRepository) *CancelOrderController {
	return &CancelOrderController{repo: repo}
}

func (c *CancelOrderController) Handle(orderID string) Result {
	order, found := c.repo.FindByID(orderID)
	if !found {
		return Result{OK: false, Message: "order not found"}
	}
	if err := order.Cancel(); err != nil {
		return Result{OK: false, Message: err.Error()}
	}
	c.repo.Save(order)
	return Result{OK: true, Message: "order cancelled"}
}

func main() {
	repo := NewInMemoryOrderRepository()
	repo.Add(&Order{ID: "A1", Status: "pending", Total: 42})
	controller := NewCancelOrderController(repo)
	fmt.Printf("%+v\n", controller.Handle("A1"))
	fmt.Printf("%+v\n", controller.Handle("missing"))
}
```
