---
name: Application Controller
slug: application-controller
family: 06-enterprise-application-architecture
category: Web Presentation
aliases: [Flow Controller, Navigation Controller, Coordinator]
first_described: "Fowler 2002"
maturity: established
related: [front-controller, page-controller, model-view-controller, template-view, mediator, state, command]
incompatible_with: []
verified: 2026-08-02
---

# Application Controller

## 1. Name, aliases, and lineage

The canonical name is Application Controller. It was named and described by Martin
Fowler in *Patterns of Enterprise Application Architecture*, Addison-Wesley,
2002, ISBN 0-321-12742-0, chapter 14, "Web Presentation Patterns", under the
entry "Application Controller"
(https://martinfowler.com/eaaCatalog/applicationController.html,
verified 2026-08-02). The catalog page states the intent in one sentence,
quoted here exactly, that Application Controller is "a centralized point for
handling screen navigation and the flow of an application," and that "input
controllers then ask the Application Controller for the appropriate commands
for execution against a model and the correct view to use depending on the
application context" (same source, verified 2026-08-02). Chapter 14 places the
pattern alongside Model View Controller, Page Controller, Front Controller,
Template View, Transform View, and Two Step View, the group the catalog index
labels "Web Presentation Patterns"
(https://martinfowler.com/eaaCatalog/, verified 2026-08-02).

Two aliases are in genuine use, and one is a name collision worth naming so a
reader is not misled by it.

**Flow Controller** is the informal name used in Java Server Faces and Spring
discussions for the same responsibility, and it is descriptive rather than a
different pattern, since the whole point of the controller is to decide the
flow between screens.

**Coordinator** is the name the iOS community settled on for its own
realization of the same idea, and the naming is not a coincidence. Soroush
Khanlou's widely cited 2015 article "The Coordinator" states plainly that "to
really execute this pattern well, you need one high-level coordinator that
directs the whole app (this is sometimes known as the Application Controller
pattern)" and links directly to Fowler's catalog page
(https://khanlou.com/2015/01/the-coordinator/, verified 2026-08-02). The
Coordinator variant decomposes the single global controller Fowler describes
into a tree of per-flow controllers, a structural difference covered in
dimension 8 and dimension 11 below, but the responsibility, deciding which
screen comes next and passing control to it, is the same responsibility.

**UINavigationController**, Apple's own UIKit class, is not this pattern and
the similarity of the name is coincidental and has caused real confusion in
iOS teams. `UINavigationController` is a view-stack container widget, it
pushes and pops screens and draws the back button, but it holds no knowledge
of which screen should come next given business state. That decision is
exactly what the Coordinator pattern was invented to hold instead, precisely
because `UINavigationController` does not hold it. A reader coming from iOS
should keep the two apart. one is a widget, the other is the decision-maker
that tells the widget what to push.

A second useful boundary is with Front Controller, the pattern immediately
before Application Controller in the same chapter. Front Controller centralizes
the entry point of a web request, one servlet or handler that every request
passes through for common concerns such as authentication, encoding, and
logging, before dispatching onward. Application Controller centralizes a
different decision, which command to run and which view to show next, and the
catalog's own wording places Application Controller downstream of the input
controllers a Front Controller dispatches to, not in competition with the
Front Controller itself. The two compose, see dimension 13.

## 2. Problem and context

The problem shows up first in an application with more than one screen that
share the same underlying process. A checkout, a multi-step registration, an
onboarding wizard, a loan application with conditional pages depending on
earlier answers. In a plain Model View Controller build, each screen owns its
own input controller, and that controller decides two things after it runs its
work. which command to execute against the domain model, and which view to
render next. When there is one screen this decision is trivial and belongs
entirely inside that one controller.

The problem appears once a second screen needs the same decision logic. A
registration flow that skips the company-details step for a personal account
and shows it for a business account needs that branch evaluated wherever the
company-details screen can be reached from, which is often more than one
place, the initial signup and a later profile-completion prompt. Each input
controller that can lead there ends up carrying its own copy of the same
conditional. A later change to the rule, adding a third account type, now
means finding and editing every copy correctly, and a copy that is missed
produces a flow that is broken for one entry point only, which is exactly the
kind of bug that survives a quick manual test of the happy path and is
discovered by a real user weeks later.

The concrete symptom to look for in a codebase is a scatter of return-the-next
view-name statements, a `response.sendRedirect`, a `return "next-step"`, an
`RequestDispatcher.forward`, repeated across several controller classes, more
than one of which computes the same condition to decide the target. That
repetition, not the mere existence of navigation code, is the signal that the
flow decision has outgrown a single controller and needs one place to live.

The context that makes Application Controller the right answer has three
parts, matching the pattern's own framing.

- More than one input controller can reach the same downstream screen, or the
  same screen must be reachable from more than one starting point, and the
  routing decision between them is shared.
- The order of screens, or the set of legal next screens, depends on
  accumulated state, not solely on which button was clicked. A wizard where
  step three depends on what was chosen at step one is the clearest instance.
- The team wants the flow itself to be inspectable and changeable in one
  place, separate from the request-handling code of any single screen, often
  because product or compliance teams need to reason about "what screen comes
  after what" without reading five controller classes.

Outside that context the pattern is unearned complexity, covered in full in
dimension 4.

## 3. Forces

- **Duplication versus centralization.** The core trade the pattern makes.
  Every input controller loses its private copy of the flow decision, and one
  new component gains all of it. Favours centralization.
- **Coupling.** Individual input controllers become simpler and less coupled
  to the flow as a whole, they ask a question and act on the answer. The
  Application Controller itself becomes coupled to the entire flow graph,
  which is the price paid for the controllers around it being decoupled from
  each other.
- **Cognitive load, per file.** Reading a single input controller becomes
  simpler because "what happens next" is no longer inline. Cognitive load, per
  system, does not fall to zero, it moves. A new engineer must now learn one
  more component, the Application Controller and its table or state model,
  before they can answer "where does clicking Submit take the user."
- **Testability of flow logic.** Favoured strongly. Once flow decisions live
  in one place expressed as data, transitions can be enumerated and tested
  without booting a web container, see dimension 15.
- **Consistency across entry points.** Favoured. The same event from two
  different starting screens produces the same downstream screen, because both
  ask the same authority rather than each computing its own answer.
- **Statefulness and scaling.** Sacrificed to a degree. The richer
  implementation variant, an explicit state model, needs somewhere to keep the
  current state between requests, normally the HTTP session, which reintroduces
  server-side session affinity concerns that a stateless design would rather
  avoid. The simpler flat-lookup variant, see dimension 8, avoids this cost
  when the flow genuinely is context-free.
- **Change control.** Favoured for product and compliance changes to the flow
  itself, since editing one table or state graph is safer and more reviewable
  than editing several controller classes, but sacrificed for the risk of a
  single component becoming a bottleneck every team change must pass through,
  see the God-controller failure mode in dimension 11.
- **Latency.** Close to neutral by design. The decision itself is a lookup or
  a small state-machine transition, not I O. Latency only enters if a team
  makes the mistake, covered in dimension 11, of letting the controller query
  the database directly to make its decision.

## 4. Applicability and non-applicability

Reach for Application Controller when the following hold.

- More than one input controller can reach, or must reach, the same
  downstream screen, and the decision of which screen comes next is
  duplicated or would be duplicated without a shared authority.
- The application has a genuine wizard, multiple steps with an order, some of
  which are conditional on earlier answers or on session or account state.
- The legality of a transition matters and should be enforced, not merely
  hoped for, for example a payment screen must be structurally unreachable
  before a shipping address has been captured.
- Product, design, or compliance teams need the flow to be inspectable, and
  ideally editable, without reading through several unrelated controller
  classes.
- The screens involved are served from one process with one session, a web
  application within one request-response session, a desktop or mobile app
  within one running process, not a flow that must survive across independent
  services or across days, see the workflow-engine boundary below.

Do NOT reach for Application Controller in these cases.

- **There is exactly one path through the screens, and no second path is
  plausible.** A three-screen signup with a fixed, always-identical order
  gains nothing from a table or state machine, a plain sequence of redirects
  inside two or three controllers is honest and reads faster. Building the
  abstraction anyway is the same speculative-generality trap that applies to
  Factory Method when there is only one product, adding a whole layer for a
  branch that will never exist.
- **The routing decision is purely a function of the current URL and
  nothing else, with no shared logic and no conditional history.** A REST
  resource-per-screen application with no wizard has no flow to centralize,
  only routes, which is a Front Controller or a plain router's job, not this
  pattern's.
- **The framework already owns declarative navigation and the team should
  not fight it.** A modern file-based or data-loader router, for example a
  React Router route tree with loaders, or a server-rendered framework with
  route-level guards, already centralizes the decision of what to render for
  a given URL and state. Layering a second, hand-rolled Application Controller
  on top duplicates the router's own responsibility and produces two sources
  of truth for the same question. When the framework's router cannot express
  a genuinely stateful wizard, the fix is usually a flow-scoped piece of state
  the router consults, not a parallel controller object competing with it.
- **Navigation is client-owned state in a single-page application backed by a
  state manager.** Where "what screen is showing" already lives as UI state
  in Redux, Zustand, or an equivalent client store, and the server is a
  stateless API, porting Application Controller to the server duplicates the
  client's own state machine and reintroduces server-side session state the
  architecture deliberately avoided.
- **The system exposes a hypermedia API and expects the client to follow
  server-supplied links.** A HATEOAS style API returns the legal next actions
  as links in the response body, letting the client decide. Adding a
  server-side Application Controller that also decides "what comes next" on
  the client's behalf duplicates the very decision the hypermedia contract was
  designed to hand to the client.
- **The flow must survive across independent services, or across a time span
  measured in hours or days, or must be resumable after a process restart
  with exactly-once semantics.** That is the job of a workflow or
  orchestration engine, Temporal, AWS Step Functions, Camunda, or the Process
  Manager and Saga patterns from enterprise integration literature, not a
  single in-process, session-scoped Application Controller. Stretching this
  pattern's session model to cover a multi-day, multi-service saga produces
  the durability and idempotency bugs those engines exist to solve properly.
- **The team genuinely finds a flat if-else inside two controllers easier to
  read and maintain than a table.** When the number of transitions is small
  and stable, and the team's honest judgement is that the abstraction costs
  more than it saves, that judgement should be trusted over the pattern's
  name recognition.

## 5. Structure

Five participants, named by the role each plays. Not every implementation uses
all five, see the variants in dimension 8.

- **InputController.** The per-action handler behind a Page Controller or
  Front Controller dispatch, the object that actually receives the request.
  It extracts parameters and hands a decision key, an event or action
  identifier, to the Application Controller. It does not itself decide the
  next command or the next view.
- **ApplicationController.** The centralized authority. Conceptually it
  answers two questions given a key and the current context, which Command
  should run, and which View should be rendered afterward. Fowler's catalog
  text frames input controllers as asking the Application Controller "for the
  appropriate commands for execution against a model and the correct view to
  use depending on the application context"
  (https://martinfowler.com/eaaCatalog/applicationController.html,
  verified 2026-08-02).
- **Command.** An instance of the Command pattern, the unit of domain-facing
  work the Application Controller selects for a given key. It may be a no-op
  when the key means "show this screen with no domain work."
- **View.** The identifier of the screen or template to render next. The
  Application Controller names it, it does not render it, that stays the
  responsibility of whichever presentation pattern, Template View or Two Step
  View, is already in place.
- **State, optional.** Present only in the richer variant covered in
  dimension 8. A State object represents one legal position in the flow and
  holds the mapping from an incoming event to the next State, the Command to
  run, and the View to show. Widely corroborated secondary descriptions of the
  pattern, consistent with how JSF's NavigationHandler and Spring Web Flow
  each independently implement the same idea, describe this as an explicit
  finite state machine scoped to one flow instance. This structural detail
  goes beyond what the short online catalog page states and is presented here
  as the community's settled reading of the pattern rather than a verbatim
  quote from the book, since the book's full chapter text was not directly
  accessible for this entry.

Relationships. InputController holds a reference to ApplicationController and
calls it, never the reverse. ApplicationController holds, or computes,
references to Command and View, and in the stateful variant holds a reference
to the current State. Command executes against the domain Model and returns an
outcome the ApplicationController can use to pick the next State. View is
consumed by the presentation layer, not by the ApplicationController itself.

## 6. ASCII structure diagram

```
   +------------------+     asks       +------------------------+
   |  InputController  |  --------->   |   ApplicationController |
   |------------------|                |------------------------|
   | + handle(request) |   getCommand  | + getCommand(key, ctx)  |
   +------------------+  <----------   | + getView(key, ctx)     |
             |                          +------------------------+
             |                              |             |
             | executes                     | selects     | selects
             v                              v             v
   +------------------+           +---------------+   +--------+
   |      Command      |           |  State (opt)  |   |  View  |
   |------------------|           |---------------|   |--------|
   | + execute(model)   |           | transitions:  |   | id     |
   +------------------+           |  event -> next |   +--------+
             |                     +---------------+
             v
   +------------------+
   |       Model        |
   +------------------+

   InputController never inspects the flow graph itself.
   Only ApplicationController knows which State follows which.
```

## 7. Dynamics

The flat, stateless form of the sequence first, since it is the more common
starting point.

```
Client        InputController      ApplicationController      Command / View
  |                  |                       |                       |
  |-- POST action -->|                       |                       |
  |                  |-- getCommand(key) --->|                       |
  |                  |                       |-- lookup table[key] ->|
  |                  |<-- Command -----------|                       |
  |                  |-- execute(model) --------------------------->|
  |                  |<-- outcome ------------------------------------|
  |                  |-- getView(key, outcome) ->|                    |
  |                  |<-- View id ------------|                       |
  |<-- rendered view-|                       |                       |
```

The stateful form adds a step, reading the current State before dispatch and
writing the next State after it, so that the same event key can legally lead
to different destinations depending on where the user actually is in the
flow.

```
Client     InputController   ApplicationController      State (session)
  |               |                    |                        |
  |-- event ----->|                    |                        |
  |               |-- currentState? -->|                        |
  |               |                    |-- read from session --->|
  |               |                    |<-- State S -------------|
  |               |-- getCommand(S, event) -->|                  |
  |               |<-- Command -------|                          |
  |               |-- execute() -------------------------------->|
  |               |-- getView(S, event, outcome) -->|            |
  |               |<-- View, nextState |                         |
  |               |-- write nextState -------------------------->|
  |<-- view ------|                    |                        |
```

Two ordering notes. First, the State must be read at the start of the request
and the next State written only after the Command's outcome is known,
otherwise a failed Command would advance the flow anyway. Second, in a
horizontally scaled deployment the session read and write above must go
through a shared session store or sticky routing, or two requests from the
same user hitting different application instances will disagree about the
current State, a concrete instance of the statefulness cost named in
dimension 3.

## 8. Implementation variants

**Flat lookup table.** A map from an action key directly to a Command class
and a View, with no dependency on prior state, typically kept as
configuration outside the code, the shape Apache Struts 1's action mappings
and Struts config files used. Cheapest to build and reason about, and correct
exactly when the next screen depends only on the current action, not on
history. Reaching for this first and upgrading only when a genuine
history-dependent branch appears keeps the abstraction earned rather than
speculative, per dimension 4.

**Explicit state model.** Session-scoped State objects, one per legal
position in the flow, each holding its own event-to-transition map. This is
the variant that makes an illegal transition, jumping from the cart screen
straight to the confirmation screen, structurally impossible rather than
merely unlikely, because the State for "cart" simply has no transition entry
for the confirmation event. The cost is more code and a state graph that must
be kept in sync with the actual set of screens, see the stale-state failure
mode in dimension 11.

**Declarative flow-definition language.** Spring Web Flow externalizes the
state model into an XML flow definition consumed by a flow engine, rather
than Java code. Spring's own documentation frames the underlying need
plainly, "many web applications require the same sequence of steps to execute
in different contexts," offering user registration, login, and cart checkout
as its own examples of such a reusable sequence, called a flow
(https://docs.spring.io/spring-webflow/docs/current/reference/,
verified 2026-08-02). The same reference describes a flow as composed of
states and transitions, "a view state, action state, or subflow state may
have any number of transitions that direct them to other states" (same
source, verified 2026-08-02), which is the State-model structure from
dimension 5 expressed declaratively rather than as hand-written Java classes.
The practical benefit is that the flow graph becomes readable, and reviewable,
by someone who does not read the surrounding Java code.

**Outcome-and-context navigation rules.** JavaServer Faces takes a third
shape again, matching outcome strings against rules keyed by the combination
of the current view and the action that produced the outcome, rather than a
strict linear state machine. Oracle's own Javadoc for `NavigationHandler`
states that the handler "will compare the view identifier of the current
view, the specified action binding, and the specified outcome against any
navigation rules provided in faces-config.xml file(s)," and that "if a
navigation case matches, the current view will be changed"
(https://docs.oracle.com/cd/E17802_01/j2ee/j2ee/javaserverfaces/1.2/docs/api/javax/faces/application/NavigationHandler.html,
verified 2026-08-02). This is looser than a strict finite state machine
because the same outcome string, for example "success," can route to two
different views depending on which screen produced it, a genuine third shape
distinct from both the flat lookup and the strict state model.

**Coordinator objects.** The mobile and desktop realization decomposes the
single global controller into a tree, one Coordinator per cohesive flow
rather than one Application Controller for the whole application. A
CheckoutCoordinator owns the checkout flow's screens and hands control to a
PaymentCoordinator for the payment sub-flow, receiving a completion callback
when that sub-flow finishes, rather than one object holding every screen in
the entire app in one table. This directly addresses the God-controller
failure mode named in dimension 11, at the cost of needing a convention for
how parent and child coordinators communicate completion and cancellation.

**Router-guard hybrid, client side.** In single-page applications the same
responsibility, deciding whether an event is allowed to lead to a given
screen, is sometimes implemented as a centralized navigation guard or a
route-loader function consulted before a client-side route renders, rather
than as a Command-returning object. The shape is the same question, "is this
transition legal, and if so what should render," implemented against the
client router's own extension points instead of a server-side session.

## 9. Known production uses

**Apache Struts 1, `RequestProcessor`.** Struts' `RequestProcessor` sits
behind `ActionServlet` and owns exactly the decision this pattern names,
which `Action` to invoke and which forward to follow next, structured
internally as a Chain of Responsibility of processing steps. Apache's own
project wiki states that `RequestProcessor` "contains the processing logic
that the Struts controller servlet performs as it receives each servlet
request from the container," and that "a new request processor can be
plugged in without touching the Servlet"
(https://cwiki.apache.org/confluence/display/STRUTS1/RequestProcessor,
verified 2026-08-02), which is the centralization and pluggability an
Application Controller is meant to provide. An independent technical
description states the connection to this pattern by name directly, "the
RequestProcessor of Struts framework is an implementation of Application
Controller pattern that takes many infrastructure responsibilities mainly
Action management and View Management"
(https://javapracticalinfo.blogspot.com/2013/02/the-requestprocessor.html,
verified 2026-08-02). That second source is a secondary technical blog, not
Fowler's own text, and is cited here as a named, checkable claim about a real
framework rather than as an authority on the pattern's original definition.

**JavaServer Faces, `NavigationHandler`.** Quoted in full in dimension 8
above. The Oracle Javadoc for `javax.faces.application.NavigationHandler`
describes exactly the responsibility this pattern names, receiving an outcome
from application code and deciding the next view against externally
configured navigation rules
(https://docs.oracle.com/cd/E17802_01/j2ee/j2ee/javaserverfaces/1.2/docs/api/javax/faces/application/NavigationHandler.html,
verified 2026-08-02).

**Spring Web Flow.** Also quoted in full in dimension 8. Spring's own
reference documentation frames the product around reusable, multi-context
sequences of steps, states, and transitions, the same vocabulary the pattern
uses, and explicitly targets "wizards" as the motivating use case
(https://docs.spring.io/spring-webflow/docs/current/reference/,
verified 2026-08-02).

**iOS application development, the Coordinator pattern.** Soroush Khanlou's
2015 article, one of the most widely cited pieces of iOS architecture
writing in the following decade, names the connection to this pattern
directly and links to Fowler's catalog page, describing a single high-level
object that "directs the whole app" as "sometimes known as the Application
Controller pattern"
(https://khanlou.com/2015/01/the-coordinator/, verified 2026-08-02). This use
matters for a reason beyond popularity, it shows the pattern surviving a
platform transplant entirely outside web presentation, from server-rendered
HTTP wizards to native mobile screen stacks, with the decomposition into a
tree of per-flow objects, dimension 8, becoming the dominant shape in that
community precisely to avoid the God-controller failure named in dimension
11.

## 10. Consequences

Positive.

- Flow logic that would otherwise be duplicated across every input
  controller that can reach a shared screen is written once and read from one
  place.
- The same event produces the same downstream screen regardless of which
  entry point triggered it, because every entry point asks the same
  authority rather than computing its own answer.
- Changing the flow, adding a step, removing one, reordering two, becomes an
  edit to one table or one state graph, reviewable by someone who does not
  need to read every input controller.
- In the state-model variant, an illegal transition is structurally
  unreachable rather than merely untested, because the current State simply
  has no entry for it.
- Flow logic becomes testable as data, enumerable and checkable without a
  running web container, see dimension 15.

Negative.

- The Application Controller can become a single large, frequently edited
  component that every feature team touches, a merge-conflict and
  code-review bottleneck, the God-controller failure named in dimension 11
  and the reason the Coordinator community moved to a tree of per-flow
  objects instead of one global table.
- It adds one more component a new engineer must learn before tracing "what
  happens when clicking this button," a real cost against the alternative of
  reading a single controller top to bottom.
- The state-model variant needs somewhere to keep the current State between
  requests, ordinarily the session, which reintroduces session-affinity and
  session-store concerns a stateless design would rather avoid.
- The state graph and the actual set of screens can drift apart over time if
  a screen is renamed or removed without a matching edit to the flow
  definition, producing the stale-state and silent-default failure modes in
  dimension 11.
- Session-scoped flow state inherits the security posture of the underlying
  session mechanism, covered fully in dimension 17.

## 11. Failure modes and misuse

**The God controller.** Symptom. One Application Controller class, or one
flow-definition file, grows to hundreds of entries and thousands of lines,
and becomes the file nearly every pull request touches, with frequent merge
conflicts between unrelated feature teams working on unrelated flows. Cause.
Every new flow in the application was added to one global controller instead
of being decomposed into its own cohesive controller. Fix. Split into one
Application Controller, or one Coordinator in Khanlou's terminology, per
cohesive flow, checkout, onboarding, account-recovery, each independently
ownable, with a thin top-level dispatcher choosing which one to enter.

**Stale state after a deploy.** Symptom. A user with an in-progress wizard
in their session, on step two of three, hits an error or is silently skipped
past a step after a deployment changes the flow graph. Cause. A running
session still references the previous version of the State machine or an
outdated step index, and the new code does not know how to resume from it.
Fix. Version the flow definition, and either migrate any persisted step state
on resume against the new version, or invalidate in-flight sessions
explicitly when a flow graph changes rather than letting them fail
unpredictably.

**Silent default routing.** Symptom. Users occasionally land on a fallback or
"please try again" screen for no reason a support agent can explain, and the
underlying cause is only found by reading logs. Cause. An action or outcome
key was never explicitly enumerated in the lookup table or navigation rules,
and the framework silently falls through to a default, redisplaying the
current view rather than failing loudly. Fix. Make an unmatched outcome fail
loudly in non-production environments, and add a build-time or test-time
check enumerating every outcome string any Command can return against the
routing table, catching a missing entry before it reaches a user.

**Domain logic leaking into the routing decision.** Symptom. The Application
Controller itself starts issuing database queries, "if user.hasPaidInvoices
then go to view X," making the routing layer depend on infrastructure that
belongs to the Command and Model layers, and slowing down every navigation
decision with I O it was never meant to perform. Cause. A developer adds a
quick inline check for convenience rather than expressing the decision as an
outcome symbol returned by the Command that already ran. Fix. Keep the
Application Controller pure over its inputs, the event key, the prior State,
and the Command's returned outcome, never a fresh query of its own. Push any
new check into the Command, which returns a new outcome symbol the routing
table can then map.

**Overlapping concurrent flows sharing one mutable state slot.** Symptom. Two
browser tabs open to the same in-progress wizard for one logged-in user
produce "wrong step" errors, or one tab silently corrupts the other's
progress. Cause. The current State is stored keyed by the raw HTTP session
rather than by a unique flow-instance or conversation identifier, so two tabs
of the same session share one mutable slot. Fix. Scope flow state to a
per-flow-instance identifier, the shape Spring Web Flow calls a flow
execution key, not to the session as a whole, so concurrent instances of the
same flow do not collide.

**Deep-link bypass.** Symptom. A user bookmarks, or manually types, the URL
of a mid-wizard screen and lands on it directly, skipping required earlier
steps, and the downstream screen then breaks or behaves incorrectly because
it assumes state that was never actually collected. Cause. The
`getView` decision is trusted only along the forward navigation path, and no
guard re-validates legality when a screen is requested directly rather than
arrived at through a transition. Fix. Every screen-serving input controller
re-checks with the Application Controller, or the State machine directly,
whether the current server-held state legally permits rendering that
particular screen right now, independent of how the request arrived.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Application Controller | Front Controller alone, no App Controller | Page Controller per screen | GoF State, one object's own behaviour | Declarative SPA router, React Router or similar | Workflow / orchestration engine, Temporal or Step Functions |
|---|---|---|---|---|---|---|
| Where the flow decision lives | One centralized table or state graph | Scattered across dispatch code, or absent | Duplicated inside each screen's own controller | Inside the object whose behaviour varies by state | The client router's route tree and loaders | The engine's durable workflow definition |
| Duplication across entry points | Eliminated by design | Not addressed | The exact problem this pattern fixes | Not applicable, one object only | Eliminated for client-owned navigation | Eliminated across services |
| Cross-request statefulness needed | Sometimes, for the state-model variant | Rarely the concern | Rarely the concern | No, state lives in one in-memory object | Client-side, no server session needed | Yes, durable and long-running by design |
| Legality of a transition enforced | Yes, in the state-model variant | No | No, ad hoc per controller | Yes, within the one object | Only if the route guard is written for it | Yes, as a first-class engine feature |
| Survives across services or days | No, session-scoped, single process | No | No | No | No | Yes, that is its purpose |
| Cognitive load to learn the system | Medium, one more component to read | Low, but flow logic is untracked | Low per file, high system-wide | Low, contained to one class | Medium, spread across route files | Medium to high, a whole engine's concepts |
| Team topology fit | Good for one owned flow, bad for one giant shared controller | Neutral | Poor once more than one controller shares logic | Neutral | Good, matches front-end ownership | Good for cross-service processes |
| Testability of the flow itself | Strong, table-driven, see dimension 15 | Weak, logic is scattered | Weak, duplicated | Strong within its own object | Strong, route configuration is data | Strong, the engine itself is tested |

Reading of the table. Application Controller wins precisely at the boundary
Page Controller alone cannot hold, more than one entry point sharing flow
logic within one process and one session. Front Controller alone solves a
different problem, the entry point, not the decision. GoF State solves the
same shape of problem for a single object's internal behaviour, and the
state-model implementation variant of Application Controller is that same
pattern applied at the scale of a whole session. A declarative router wins
once navigation is genuinely client-owned. A workflow engine wins once the
flow must outlive a single process or a single session, which Application
Controller was never designed to do.

## 13. Related and incompatible patterns

- **Front Controller.** Composes directly, and the two are commonly confused
  because both centralize something. Front Controller centralizes the entry
  point of a request, security, encoding, common preprocessing, before
  dispatching to an input controller. Application Controller centralizes the
  decision that input controller then consults, which command to run and
  which view to show. A typical build has exactly one Front Controller and
  consults one Application Controller from behind it.
- **Page Controller.** The baseline this pattern is extracted from. When Page
  Controllers, each handling one screen independently, begin duplicating the
  same flow decision, that duplication is the trigger described in dimension
  14 for pulling an Application Controller out of them.
- **Mediator, GoF.** Application Controller is, structurally, a Mediator
  scoped specifically to screen-navigation events. Input controllers and
  views do not reference each other directly, they each reference the
  Application Controller, which is exactly the shape Mediator gives a set of
  colleague objects that should not know about each other.
- **State, GoF.** The explicit state-model implementation variant, dimension
  8, is the State pattern applied to session-scoped application state rather
  than to a single object's internal field. Each Fowler-style State object
  plays the role a GoF ConcreteState plays, holding its own legal transitions.
- **Command, GoF.** Directly composed. The Application Controller's
  `getCommand` returns a Command-pattern object, and the two patterns are
  meant to be used together, not as alternatives.
- **Template View, Two Step View.** Downstream and unrelated in concern. Once
  the Application Controller has named the View, rendering that view is
  entirely the job of whichever presentation pattern is already in place.
  Neither pattern needs to know the other exists.
- **Coordinator, iOS convention.** The mobile and desktop realization of the
  same responsibility, decomposed into a tree of per-flow objects rather than
  one flat global table, see dimension 8 and dimension 9.
- **Saga, Process Manager.** Conflicts at the boundary of scope rather than
  in principle. Both answer "what happens next in a multi-step process," but
  a Saga or Process Manager is built to survive across independent services
  and across time, with compensating actions for partial failure, none of
  which Application Controller's single-process, session-scoped model
  provides. Stretching Application Controller across that boundary instead of
  adopting a Saga is the workflow-engine non-applicability case in dimension
  4.
- **Service Locator.** An easy naming confusion, not a real relationship.
  Service Locator centralizes the resolution of object dependencies. This
  pattern centralizes the resolution of a navigation decision. They solve
  different problems and neither depends on the other.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered steps.

1. Find two or more Page or Input Controllers that each contain their own
   conditional block deciding the next screen, and confirm the condition or
   its outcome genuinely overlaps between them, not merely that both branch
   on something.
2. Extract each controller's condition-and-destination pairs into a single
   table, keyed by an event or action identifier, literally an Extract
   Method followed by a Move Method into a new class, see the refactoring
   family entries for both.
3. Introduce the Application Controller class holding that table, with a
   single `getView` method reading it.
4. Update each Input Controller to call the new `getView` method and delete
   its own local branch. Run the existing tests, or add characterization
   tests first if none exist covering the current behaviour.
5. Repeat the same extraction for the "which Command to run" decision if the
   controllers also duplicate that, adding `getCommand` to the same class.
6. Once duplication is gone and behaviour is verified, decide whether the
   flat table needs to become an explicit state model. That upgrade is
   earned only when a genuine history-dependent branch appears, "the payment
   screen is legal only after shipping has been captured," not merely
   because a state machine sounds more correct.
7. If adopting the state model, introduce State objects one at a time behind
   the existing `getView` and `getCommand` interface, so callers see no
   change in their own code while the internal representation changes, the
   same incremental substitution the Strangler approach uses at a larger
   scale.

Removing the pattern once it stops earning its place. Signals include a table
where nearly every entry has become an unconditional one-to-one mapping with
no real branching left, or a rewrite to a client-side single-page application
where the framework's own router should own navigation instead.

1. Confirm the remaining table entries genuinely carry no shared logic
   anymore, only a straight one-to-one mapping, before removing anything.
2. For each entry with exactly one remaining caller, inline it back into that
   caller directly, an Inline Method in reverse of step 3 above.
3. Delete the Application Controller once no caller queries it, or once a
   framework-native declarative router has fully absorbed the responsibility
   for the flows being migrated, per the non-applicability case in dimension
   4.
4. When migrating one flow at a time to a client-owned router, keep the
   server-side Application Controller serving only the flows not yet
   migrated, gated behind a feature flag, so the migration itself can proceed
   flow by flow rather than as one large cutover.

## 15. Testing and verification

Easier because of the pattern.

- Flow logic is a function of an event key and a context, event and prior
  State in, Command and View out, and that function can be unit tested as
  plain data, with no web server, no mocked servlet objects, and no browser
  involved.
- In the state-model variant, every declared transition can be enumerated
  and checked in a table-driven test, one row per legal transition, without
  writing a single custom test per screen.
- Illegal transitions become directly assertable. a test can attempt every
  event against every State and assert that only the declared transitions
  succeed, everything else is rejected, which is close in spirit to a
  property-based check over the whole transition table, see the sibling
  entry on property-first testing for the general technique this specializes.

Harder because of the pattern.

- End-to-end coverage of a whole wizard, start to finish, still needs an
  integration or browser-level test, because individually correct per-step
  unit tests can each pass while the composed sequence still breaks, for
  example step two's saved context does not actually contain the field step
  three expects to read.
- Session-scoped state complicates isolating an Input Controller's own unit
  test, since it now needs a fake or injected flow-execution context rather
  than nothing at all.

Techniques that apply.

- **Table-driven transition test.** One test enumerating every declared
  (State, event) pair against its expected (nextState, View), and a second
  pass asserting every undeclared pair is rejected rather than silently
  defaulted, which directly targets the silent-default failure mode from
  dimension 11.
- **Contract test between Commands and the routing table.** Assert that
  every outcome string any Command can actually return is present as a key
  somewhere in the routing table, catching a missing mapping at build time
  rather than when a real user's action produces an outcome nobody wired up.
- **One happy-path and one abandon-and-resume end-to-end test per flow.**
  The happy path proves the whole sequence composes correctly. an
  abandon-and-resume test, starting the flow, leaving it mid-way, and
  returning later, proves the stale-state failure mode from dimension 11 is
  actually handled, not merely assumed away.
- **Fuzz-style transition test.** Feed every declared event into every
  declared State exhaustively and assert the controller either returns a
  legal transition or explicitly and loudly rejects the attempt, never a
  silent no-op, which is the mechanical version of the same fix named for
  the deep-link bypass failure mode.

## 16. Observability signals

The whole reason this pattern centralizes the flow decision is so that
decision can be watched in one place, and that observability payoff is lost
if nothing is actually recorded.

What to record.

- Every navigation decision, logged or emitted as a span attribute,
  including the event key, the prior State or view, the resulting View, and
  whether the decision matched a declared rule or fell through to a default.
- A counter of `getView` calls labelled by the triple of prior view, event,
  and resulting view. The label distribution over time is directly useful
  well beyond debugging, it is real funnel and drop-off data for product
  analysis, with no separate analytics instrumentation needed.
- A counter of fallback or default-routing hits specifically, separate from
  the general counter above. A healthy system holds this at or near zero. any
  rise after a deployment is the silent-default failure mode from dimension
  11 happening in production right now, not a theoretical risk.
- A gauge or histogram of how long a flow-state has sat unfinished in a
  session, a direct abandonment signal per step of a wizard.
- In the state-model variant, a counter of rejected or illegal transition
  attempts labelled by the (State, attempted event) pair. A spike here is
  either a stale client bypassing a newly added required step, or an active
  deep-link bypass attempt, and either reading is worth investigating.

A healthy instance on a dashboard. The fallback-routing counter sits flat at
zero. The per-step abandonment gauge matches the shape a product manager
would already expect from the business funnel. The illegal-transition counter
sits near zero and does not correlate with any one client version.

A failing instance. The fallback-routing counter begins climbing right after
a deployment, meaning a new outcome string was introduced without a matching
routing-table entry. One step's abandonment gauge spikes on its own, pointing
at a broken or confusing screen at that exact step, localized without reading
a line of that screen's code. The illegal-transition counter spikes and
correlates with one specific client version, pointing at a stale mobile build
attempting to skip a step the server now requires.

## 17. Security and privacy implications

This pattern is not silent on security, and treating it as purely a UX
convenience under-states a real risk surface it opens.

**Trusting a client-supplied destination.** Because the Application
Controller frequently decides the next screen based on authorization state,
verified against unverified, paid against unpaid, it becomes a natural place
for an authorization bypass to live if the decision ever trusts client input
directly. If a hidden form field or a query parameter naming the intended
next step is read and honoured without re-deriving the legal next view from
server-held state, an attacker who can influence that value can skip a
required 2FA screen, a consent screen, or a payment step entirely. This is
the same defect as the deep-link bypass failure mode in dimension 11,
restated here as a security concern rather than a UX one, because the fix is
identical, never trust a requested destination, always re-derive the legal
one from state the server itself holds.

**Session hijacking inherits directly.** Session-scoped flow state, the cost
named in dimension 10, means the Application Controller inherits every
session-fixation and session-hijacking risk of the underlying session
mechanism without adding any protection of its own. A hijacked session lets
an attacker resume someone else's in-progress wizard exactly where it was
left, including a partially completed payment flow. Standard session-security
practice, regenerating the session identifier on a privilege change such as a
login that occurs mid-flow, applies directly here and is easy to forget,
because the flow state feels like ordinary navigation rather than
authentication-adjacent state, when in this pattern it functionally is.

**Logging leaks.** The observability advice in dimension 16 recommends
recording every navigation decision. If the event or context payload
recorded includes user-identifying data directly, an email address or part
of a government identifier used as a routing key, that data now sits in log
lines and metric labels. Label observability data by opaque flow-step
identifiers, never by raw user-identifying values.

**Flow-definition files as a change-control surface.** In the declarative
variant, Spring Web Flow's XML flow definitions or a faces-config.xml
navigation-rule file, the flow graph is configuration, not code guarded by
the same review process as a controller class in every deployment pipeline.
If that configuration is writable by a less trusted deployment stage, or by
a compromised build pipeline, an attacker who can edit it can redirect users
past a consent or compliance screen, or toward a phishing-adjacent internal
state, without touching a single line of application code that a security
review would normally scrutinize. Flow-definition files carrying
authorization-adjacent routing decisions deserve the same change-control
rigor as an authorization policy file, not the lighter review a view
template typically receives.

## Code examples

Three languages, each chosen because the pattern is idiomatic in a genuinely
different way in each. TypeScript shows the flat lookup-table variant from
dimension 8, the cheapest and most common starting shape. Python shows the
explicit state-model variant, an actual finite state machine enforcing legal
transitions. Swift shows the Coordinator variant from dimension 8 and
dimension 9, the mobile realization, deliberately written against a small
protocol rather than UIKit so it compiles standalone with `swiftc` and
carries no framework scaffolding. Java and Go are omitted, Java because no
Java Runtime is present on this machine to compile against and a hand-typed,
unverified Java sample would violate the run-or-say-so requirement this
catalog holds itself to. Go is omitted because it has no inheritance and no
native state-machine idiom distinct from the flat-map form already shown
fully in TypeScript, so a Go sample would repeat the same shape with no new
idiom to teach.

### TypeScript, flat lookup table variant

A three-step checkout, cart, shipping, payment, confirm, where a purely
digital cart skips the shipping step. The routing decision is a plain map
from an event key to a destination, with no dependency on flow history,
matching the Struts-style flat variant from dimension 8.

```typescript
type ViewId = "cart" | "shipping" | "payment" | "confirm";

interface Command {
  execute(cart: { digitalOnly: boolean }): string;
}

const noop: Command = { execute: () => "ok" };

const routingTable: Record<string, { command: Command; nextView: ViewId }> = {
  "cart:submit:physical": { command: noop, nextView: "shipping" },
  "cart:submit:digital": { command: noop, nextView: "payment" },
  "shipping:submit": { command: noop, nextView: "payment" },
  "payment:submit": { command: noop, nextView: "confirm" },
};

class ApplicationController {
  getRoute(fromView: ViewId, event: string, digitalOnly: boolean) {
    const suffix = fromView === "cart" ? (digitalOnly ? "digital" : "physical") : "";
    const key = suffix ? `${fromView}:${event}:${suffix}` : `${fromView}:${event}`;
    const route = routingTable[key];
    if (!route) {
      throw new Error(`no route declared for key: ${key}`);
    }
    return route;
  }
}

class InputController {
  constructor(private readonly appController: ApplicationController) {}

  handle(fromView: ViewId, event: string, digitalOnly: boolean): ViewId {
    const { command, nextView } = this.appController.getRoute(fromView, event, digitalOnly);
    command.execute({ digitalOnly });
    return nextView;
  }
}

const controller = new InputController(new ApplicationController());
console.log(controller.handle("cart", "submit", false)); // shipping
console.log(controller.handle("cart", "submit", true)); // payment
console.log(controller.handle("payment", "submit", true)); // confirm
```

### Python, explicit state-model variant

The same checkout expressed as a finite state machine. Each `State` declares
its own legal transitions, so an event with no matching transition raises
rather than falling through to a default, directly addressing the
silent-default failure mode from dimension 11.

```python
from dataclasses import dataclass, field


@dataclass
class Transition:
    command: str
    next_state: str


@dataclass
class State:
    name: str
    transitions: dict[str, Transition] = field(default_factory=dict)


class IllegalTransition(Exception):
    pass


class ApplicationController:
    def __init__(self) -> None:
        self.states: dict[str, State] = {
            "cart": State(
                "cart",
                {
                    "submit_physical": Transition("noop", "shipping"),
                    "submit_digital": Transition("noop", "payment"),
                },
            ),
            "shipping": State("shipping", {"submit": Transition("noop", "payment")}),
            "payment": State("payment", {"submit": Transition("noop", "confirm")}),
            "confirm": State("confirm", {}),
        }

    def get_route(self, current_state_name: str, event: str) -> Transition:
        state = self.states[current_state_name]
        if event not in state.transitions:
            raise IllegalTransition(f"{event} is not legal from {current_state_name}")
        return state.transitions[event]


class InputController:
    def __init__(self, app_controller: ApplicationController) -> None:
        self.app_controller = app_controller
        self.current_state = "cart"

    def handle(self, event: str) -> str:
        transition = self.app_controller.get_route(self.current_state, event)
        # the command would run against the domain model here
        self.current_state = transition.next_state
        return self.current_state


if __name__ == "__main__":
    ic = InputController(ApplicationController())
    print(ic.handle("submit_physical"))  # shipping
    print(ic.handle("submit"))  # payment
    print(ic.handle("submit"))  # confirm
    try:
        ic.handle("submit_physical")  # illegal from confirm
    except IllegalTransition as exc:
        print(f"rejected: {exc}")
```

### Swift, coordinator variant

The Coordinator variant from dimension 8, deliberately written against a
small `Screen` and `Navigator` protocol rather than `UIKit`, so it compiles
standalone. Each coordinator owns one cohesive flow rather than one global
table, matching Khanlou's structure named in dimension 9.

```swift
protocol Screen {
    var name: String { get }
}

struct CartScreen: Screen { let name = "cart" }
struct ShippingScreen: Screen { let name = "shipping" }
struct PaymentScreen: Screen { let name = "payment" }
struct ConfirmScreen: Screen { let name = "confirm" }

protocol Navigator {
    func present(_ screen: Screen)
}

final class ConsoleNavigator: Navigator {
    func present(_ screen: Screen) {
        print("presenting: \(screen.name)")
    }
}

protocol Coordinator: AnyObject {
    func start()
}

final class CheckoutCoordinator: Coordinator {
    private let navigator: Navigator
    private let digitalOnly: Bool
    private var onFinished: () -> Void

    init(navigator: Navigator, digitalOnly: Bool, onFinished: @escaping () -> Void) {
        self.navigator = navigator
        self.digitalOnly = digitalOnly
        self.onFinished = onFinished
    }

    func start() {
        navigator.present(CartScreen())
        submitCart()
    }

    private func submitCart() {
        if digitalOnly {
            goToPayment()
        } else {
            navigator.present(ShippingScreen())
            submitShipping()
        }
    }

    private func submitShipping() {
        goToPayment()
    }

    private func goToPayment() {
        navigator.present(PaymentScreen())
        submitPayment()
    }

    private func submitPayment() {
        navigator.present(ConfirmScreen())
        onFinished()
    }
}

let navigator = ConsoleNavigator()
let physicalFlow = CheckoutCoordinator(navigator: navigator, digitalOnly: false) {
    print("physical checkout finished")
}
physicalFlow.start()

let digitalFlow = CheckoutCoordinator(navigator: navigator, digitalOnly: true) {
    print("digital checkout finished")
}
digitalFlow.start()
```

## 18. References

1. Martin Fowler. *Patterns of Enterprise Application Architecture*.
   Addison-Wesley, 2002. ISBN 0-321-12742-0. Chapter 14, Web Presentation
   Patterns, "Application Controller". Source of the pattern's name, its
   original intent, and its placement in the Web Presentation Patterns group.
2. Martin Fowler. "Application Controller".
   https://martinfowler.com/eaaCatalog/applicationController.html
   Verified 2026-08-02. Source of the exact quoted intent sentence and the
   description of input controllers consulting the Application Controller
   for a command and a view.
3. Martin Fowler. "Enterprise Application Architecture Patterns" catalog
   index. https://martinfowler.com/eaaCatalog/
   Verified 2026-08-02. Source confirming the Web Presentation Patterns
   grouping and the sibling patterns in it.
4. Martin Fowler. "Front Controller".
   https://martinfowler.com/eaaCatalog/frontController.html
   Verified 2026-08-02. Source for the Front Controller description used to
   draw the boundary in dimension 1 and dimension 13.
5. Apache Software Foundation. "RequestProcessor", Struts 1 wiki.
   https://cwiki.apache.org/confluence/display/STRUTS1/RequestProcessor
   Verified 2026-08-02. Source for the description of `RequestProcessor`'s
   centralizing, pluggable role used in dimension 9.
6. "The RequestProcessor". Java Practical Info.
   https://javapracticalinfo.blogspot.com/2013/02/the-requestprocessor.html
   Verified 2026-08-02. Source of the explicit secondary claim naming
   `RequestProcessor` as an Application Controller implementation, used in
   dimension 9 and labelled there as a secondary, checkable source rather
   than an authority on the pattern's original definition.
7. Oracle. *JavaServer Faces 1.2 API documentation*,
   `javax.faces.application.NavigationHandler`.
   https://docs.oracle.com/cd/E17802_01/j2ee/j2ee/javaserverfaces/1.2/docs/api/javax/faces/application/NavigationHandler.html
   Verified 2026-08-02. Source of the quoted Javadoc description used in
   dimension 8 and dimension 9.
8. VMware, Spring team. *Spring Web Flow Reference Guide*.
   https://docs.spring.io/spring-webflow/docs/current/reference/
   Verified 2026-08-02. Source of the quoted descriptions of flows, states,
   and transitions used in dimension 8 and dimension 9.
9. Soroush Khanlou. "The Coordinator".
   https://khanlou.com/2015/01/the-coordinator/
   Verified 2026-08-02. Source of the Coordinator alias, the explicit named
   link to Fowler's Application Controller pattern, and the mobile
   production use in dimension 9.
10. Ruby on Rails Guides. "Action Controller Overview".
    https://guides.rubyonrails.org/action_controller_overview.html
    Verified 2026-08-02. Consulted while researching this entry to check a
    possible Ruby on Rails production use. `ApplicationController` in Rails
    is confirmed by this guide to be the shared base class every controller
    inherits from, a naming convention for common controller behaviour, not
    a centralized flow-decision authority in Fowler's sense, and it is
    therefore deliberately not listed as a production use in dimension 9 to
    avoid overstating the connection.
