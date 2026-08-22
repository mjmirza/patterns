---
name: Mediator
slug: mediator
family: 01-design-patterns-gof
category: Behavioral
aliases: [Dialog Director, Coordinator, Hub, Broker (loosely)]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [observer, facade, command, memento, adapter, chain-of-responsibility]
incompatible_with: []
verified: 2026-08-02
---

# Mediator

## 1. Name, aliases, and lineage

The canonical name is Mediator. It appears in the Gang of Four catalog as one of
the eleven behavioral patterns, described in Erich Gamma, Richard Helm, Ralph
Johnson and John Vlissides, *Design Patterns. Elements of Reusable
Object-Oriented Software*, Addison-Wesley, 1994, chapter 5 (Behavioral
Patterns), Mediator. The book states the intent as defining an object that
encapsulates how a set of objects interact, promoting loose coupling by keeping
those objects from referring to one another explicitly, and allowing their
interaction to be varied independently ([Wikipedia summary of the GoF
intent](https://en.wikipedia.org/wiki/Mediator_pattern), verified 2026-08-02).

**Dialog Director** is the alias carried in the GoF motivating example itself,
where an abstract `DialogDirector` coordinates the widgets of a dialog box and a
concrete `FontDialogDirector` handles one particular dialog. The alias is worth
knowing because it names the pattern by its job rather than by its position, and
because a reader coming from the ET++ and THINK C lineage of that example will
recognise the word before recognising Mediator.

**Coordinator** is the same idea under a name that has drifted into iOS and
Android architecture writing, where a coordinator owns navigation between view
controllers so that no screen knows the next screen. That usage narrows the
pattern to one axis, navigation, but the mechanics match.

**Hub** is the informal name in network and messaging vocabulary, describing the
topology rather than the object. Hub and spoke is a topology. Mediator is the
object-level realisation of it.

**Broker** is used loosely as a synonym and should not be. A broker in the
messaging vocabulary routes messages between endpoints that do not know each
other, and it usually owns queueing, durability and delivery guarantees that the
GoF Mediator says nothing about. A Mediator holds interaction logic. A broker
holds transport. The two frequently occupy the same box in a deployment diagram,
which is exactly why the words blur.

There is a fifth name in circulation, **Event Aggregator**, which is a genuinely
different pattern with a genuinely similar shape. Martin Fowler defines it in one
sentence. "An Event Aggregator acts as a single source of events for many
objects." It registers for the events of all those objects so that a client
subscribes once, to the aggregator, instead of once per source. Fowler positions
it against Facade rather than against Mediator, writing that "you can think of an
Event Aggregator as a particular form of Facade that focuses only on observer
relationships" ([Martin Fowler, "Event
Aggregator"](https://martinfowler.com/eaaDev/EventAggregator.html), verified
2026-08-02).

Fowler does not contrast it with Mediator on that page, so the contrast that
follows is my own reading rather than his. An Event Aggregator does not know the
semantics of what it forwards, it exists to cut subscription bookkeeping. A
Mediator does know the semantics, and those semantics are the reason it exists.
Conflating the two is the origin of a large share of the failures in dimension
11.

## 2. Problem and context

A set of objects has to cooperate, and every one of them needs to know something
about the others in order to do its part.

The situation reads like this in a codebase. A form has a country dropdown, a
state dropdown, a postal code field, a tax rate label and a submit button. When
the country changes, the state dropdown reloads its options, the postal code
field changes its validation mask, the tax label recomputes, and the submit
button re-evaluates whether the form is valid. The obvious first implementation
puts a handler on the country dropdown that reaches into the state dropdown, the
postal field, the tax label and the button. Then the state dropdown gets a
handler that reaches into three of the same objects. Then a promotion code field
arrives and touches the tax label and the button. Within a few sprints every
widget holds a reference to every other widget it can affect, and the number of
those references grows with the square of the widget count.

That is the shape of the problem. It has three observable symptoms.

- **No widget can be reused.** The country dropdown is now a country dropdown
  that knows about tax labels. Lifting it into a second form drags the second
  form's absent tax label with it, so the code is copied instead of moved.
- **No single place describes the rules.** The answer to "what happens when the
  country changes" is spread across five files, and a reader has to reconstruct
  it by following handlers. Nobody can review the rule as a rule.
- **Changing one interaction risks all of them.** Adding a currency field means
  editing several existing widgets, which is the Open Closed Principle failing
  in the direction that hurts most, because the edits land in shared code that
  other screens depend on.

The context that makes Mediator the right answer has four parts.

- The objects are **peers**, not a layered stack. Each stands on its own and none
  naturally owns the others.
- The interaction rules are **specific to this assembly** of peers, not intrinsic
  to any one of them. The country dropdown genuinely does not have an opinion
  about tax. This particular checkout form does.
- The rules are **stateful or conditional**, so they cannot be reduced to a
  fan-out notification. Something has to decide, not merely forward.
- The set of peers is **bounded and known at design time**. Mediator coordinates
  a cast, not an open population.

Outside that context the pattern is a liability, and dimension 4 gives the list.
The most common mistake in applying it is missing the third part. If the rules
are pure fan-out with no decision, an Observer or an event bus is the cheaper
structure and a Mediator adds a hop and a hotspot for nothing.

## 3. Forces

The pattern balances the following competing pressures.

- **Coupling between peers.** Favoured, strongly. This is the whole trade. The
  count of peer-to-peer references drops from something proportional to the
  square of the peer count to something proportional to the peer count, because
  each peer holds one reference, to the mediator.
- **Coupling to the mediator.** Sacrificed. Every peer now depends on the
  mediator abstraction, and the mediator depends on every peer. The total
  coupling has not vanished, it has been relocated to one place where it can be
  read and reviewed. Whether that is a win depends entirely on whether the
  relocated logic stays small, which is the failure in dimension 11.
- **Cognitive load, local.** Favoured. Reading one widget is now easy, because it
  says "tell the mediator, something changed" and stops.
- **Cognitive load, global.** Sacrificed. Reading the mediator is now hard,
  because it holds every rule at once. The reader trades many small mysteries for
  one large one. On a well-scoped mediator this is a good trade, since the large
  thing is at least in one file. On a sprawling one it is the worse deal.
- **Cohesion.** Favoured for the peers, sacrificed for the mediator. The peers
  become single-purpose. The mediator becomes multi-purpose by construction,
  which is why it drifts toward low cohesion over time unless it is split.
- **Testability.** Favoured. The rules are now in a plain object with no
  rendering, no input and no output, so they can be tested as a state machine.
  See dimension 15.
- **Latency.** Sacrificed slightly. Every interaction that was one direct call is
  now two, an inbound notification and an outbound command, plus whatever
  dispatch the mediator uses internally. Irrelevant in a UI, measurable in a hot
  loop, and it counts when the mediator is a network hop rather than an object.
- **Operability.** Mixed. Favoured because every interaction passes through one
  point that can be logged, replayed and traced, which is the strongest
  operational argument for the pattern. Sacrificed because that point is a single
  failure domain and a single contention point.
- **Consistency.** Favoured. Because one object sees all state transitions in
  order, invariants that span peers can actually be enforced. Spread across
  peers, the same invariants are enforceable only by convention.
- **Team topology.** Mixed, and this is underrated. The mediator becomes a file
  every team touches, which turns it into a merge hotspot and a review
  bottleneck. Splitting one mediator per interaction cluster is usually a team
  decision before it is a design decision.
- **Cost of change.** Favoured for adding an interaction rule, since the edit
  lands in one file. Sacrificed for adding a peer, since the mediator must learn
  about it, and sacrificed badly for reusing a peer in a second assembly, since
  the peer's mediator interface may not fit the second mediator.

A pattern that gave up nothing would be a language feature. The price here is
paid in centralisation, and centralisation is a bet that the centre stays small.

## 4. Applicability and non-applicability

Reach for Mediator when the following hold.

- A set of objects communicates in well-defined but complicated ways, and the
  resulting dependency graph is dense and hard to follow.
- Reusing an object is hard because it references many peers, and the references
  carry no meaning outside the current assembly.
- Behaviour distributed across several classes should be customisable without
  subclassing all of them, so the variation point wants to be one object.
- Cross-peer invariants must hold, for example that exactly one item is selected,
  or that a submit action is enabled only when four separate conditions agree.
- An interaction sequence needs to be recorded, replayed or audited as a unit,
  which is far easier at a single chokepoint.
- Peers are being written by different teams and a neutral coordination contract
  is cheaper than pairwise agreements.

Do NOT reach for Mediator in these cases. The reason matters more than the rule.

- **The interaction is pure fan-out with no decision.** If the answer to every
  event is "tell everyone who cares" and no state is consulted, Observer or a
  publish-subscribe bus is the honest structure. A Mediator here is a forwarding
  function wearing a class, and it will accumulate exactly the logic you avoided
  writing, which is how god-mediators start.
- **The relationship is layered, not peer-to-peer.** If one object legitimately
  owns the others, that is composition, and the owner already is the coordination
  point. Introducing a separate mediator between an owner and the things it owns
  produces two coordinators competing for the same job.
- **The client wants one simplified entry point into a subsystem.** That is
  Facade. See dimension 13 for the full distinction. The tell is directionality.
  If nothing inside the subsystem needs to call back out through the new object,
  a Mediator is not what is being built.
- **The set of participants is open and unbounded.** A mediator that must learn
  about every participant cannot scale to participants it has never heard of. A
  registry, a bus, or plain Observer handles an open population. A mediator
  handles a cast.
- **The interaction is a single pipeline with an order.** A request flowing
  through stages in sequence is Chain of Responsibility or a pipeline, and
  modelling it as a mediator hides the ordering that is the point of the design.
- **There are only two peers.** Two objects that talk to each other do not have a
  dependency explosion. A mediator between exactly two collaborators adds a hop,
  a file and a vocabulary, and removes one direct reference. That is a loss. The
  pattern starts paying for itself somewhere around four or five interacting
  peers, and the exact number depends on how many of the pairwise edges are
  actually live.
- **The coordination logic is genuinely owned by a domain object.** If the rules
  are business rules about an aggregate, they belong on the aggregate, not in a
  technical coordinator. Pulling them into a mediator produces an anemic domain
  model, and the mediator becomes a transaction script.
- **You need durability, retry or ordering guarantees.** Those are broker
  concerns. A Mediator is an in-process object with no delivery semantics.
  Reaching for the pattern name to justify building a message broker by hand is
  a fast way to reimplement a queue badly.
- **The peers must remain independently deployable and independently evolvable.**
  A mediator that knows all peers is a coupling point at the deployment level
  too. In a distributed system this is the orchestration versus choreography
  argument, and the mediator side of it buys clarity at the cost of a component
  that must be changed and released whenever any participant changes.

## 5. Structure

Four participants, named by the role each plays.

- **Mediator.** The abstract type declaring the communication contract that
  colleagues use to report events. In the classic form this is a single
  `notify(sender, event)` operation. In practice it is often several named
  operations, one per named interaction, which reads better and types better. The
  abstraction exists so a colleague depends on a contract rather than on a
  concrete coordinator, which is what makes the colleague reusable and testable.
- **ConcreteMediator.** Holds references to its colleagues, knows their types,
  and implements the coordination logic. It is the only object in the design that
  understands the assembly as a whole. It is also the object that will grow
  without bound if nobody watches it.
- **Colleague.** The abstract type or convention that each participant follows.
  Its defining property is that it holds a reference to the Mediator abstraction
  and to nothing else in the assembly. In many languages there is no explicit
  Colleague base type and the role is carried by a constructor parameter, which
  is fine. The role is real even when the type is not.
- **ConcreteColleague.** A participant. It reports state changes to the mediator
  and exposes operations the mediator can call. It never names another colleague.
  That last sentence is the invariant the whole pattern rests on, and a single
  violation of it silently reintroduces the graph the pattern removed.

Relationships. Every ConcreteColleague holds exactly one reference, upward, to
the Mediator abstraction. The ConcreteMediator holds references downward to every
colleague it coordinates. The graph is therefore a star with the mediator at the
centre, and the total edge count is linear in the colleague count rather than
quadratic.

Two details decide how well a given implementation ages.

**Reference direction from the mediator.** If the ConcreteMediator holds concrete
colleague types, it is easy to write and hard to test in isolation. If it holds
narrow interfaces, one per colleague role, it is slightly more code and clearly
easier to test and to reuse. Prefer the narrow interfaces once the mediator has
more than two or three colleagues.

**Notification granularity.** The single `notify(sender, event)` operation forces
the mediator to branch on the sender or the event tag, which is a conditional
that grows. Named operations such as `onCountryChanged(code)` push the branch
into method dispatch and let the type system carry the payload. The single
operation is the shape drawn in most catalog diagrams, and the named operations
are the shape that survives in real code.

## 6. ASCII structure diagram

```
                        +-----------------------------+
                        |         Mediator            |
                        |  (abstract contract)        |
                        |-----------------------------|
                        | + notify(sender, event)     |
                        +-----------------------------+
                                     ^
                                     | implements
                                     |
                        +-----------------------------+
              +-------->|      ConcreteMediator       |<--------+
              |         |-----------------------------|         |
              |         | - colleagueA : ColleagueA   |         |
              |         | - colleagueB : ColleagueB   |         |
              |         | - colleagueC : ColleagueC   |         |
              |         |-----------------------------|         |
              |         | + notify(sender, event)     |         |
              |         |   holds ALL interaction     |         |
              |         |   rules for this assembly   |         |
              |         +-----------------------------+         |
              |            |            |            |          |
      reports |     calls  |     calls  |     calls  |          | reports
      upward  |    downward|   downward |   downward |          | upward
              |            v            v            v          |
     +--------+-------+ +-----------+ +-----------+ +-----------+------+
     | ConcreteColl.A | | Coll. B   | | Coll. C   | | ConcreteColl. D  |
     |----------------| |-----------| |-----------| |------------------|
     | - m : Mediator | | - m       | | - m       | | - m : Mediator   |
     | + operation()  | | + op()    | | + op()    | | + operation()    |
     +----------------+ +-----------+ +-----------+ +------------------+

     No horizontal arrows exist between colleagues. That absence IS the
     pattern. Edges = N, not N*(N-1)/2. One horizontal arrow reintroduces
     the graph and quietly cancels the benefit.
```

## 7. Dynamics

The runtime flow has one property worth stating plainly. A colleague never
receives a call from another colleague. It receives calls only from the mediator
and from the outside world, and it emits calls only to the mediator. Every
interaction is therefore a two-leg path, up then down, and the turn happens in
the mediator where a decision can be made.

```
 User        CountryBox      Mediator          StateBox      SubmitButton
  |              |               |                 |               |
  |-- select --->|               |                 |               |
  |              |               |                 |               |
  |              |-- notify(     |                 |               |
  |              |    self,      |                 |               |
  |              |  "changed") ->|                 |               |
  |              |               |                 |               |
  |              |               |  reads its own  |               |
  |              |               |  rule table for |               |
  |              |               |  "country       |               |
  |              |               |   changed"      |               |
  |              |               |                 |               |
  |              |               |-- setOptions()->|               |
  |              |               |                 |               |
  |              |               |-- clear() ----->|               |
  |              |               |                 |               |
  |              |               |-- setEnabled(   |               |
  |              |               |     false) --------------------->|
  |              |               |                 |               |
  |              |<-- (no call from StateBox to CountryBox, ever)  |
  |              |               |                 |               |
  |<-- repaint --|               |                 |               |
  |              |               |                 |               |
  |-- select state ------------->|                 |               |
  |              |               |<-- notify(self, "changed") -----|
  |              |               |                 |               |
  |              |               |  re-evaluates   |               |
  |              |               |  form validity  |               |
  |              |               |                 |               |
  |              |               |-- setEnabled(true) ------------>|
  |              |               |                 |               |
```

Three timing notes decide whether an implementation is correct.

**Reentrancy.** The mediator calls a colleague, the colleague changes state, and
the colleague notifies the mediator from inside the call it is servicing. The
mediator is now executing its own rule table twice on one stack. The naive result
is either infinite recursion or a rule seeing half-applied state. Two standard
defences exist. A reentrancy guard sets a flag on entry and queues notifications
received while the flag is set, draining them after the outer call returns. Or
colleague setters accept a silent variant that suppresses the notification when
the mediator is the caller, which is the approach most UI toolkits take. The
guard is safer, the silent setter is faster to write and easier to forget.

**Ordering.** When one event triggers updates to several colleagues, the order is
decided by the mediator and nowhere else. That is a benefit, because the order is
now explicit and reviewable, and a hazard, because it is now implicit knowledge
encoded in statement sequence rather than in a declared dependency. If ordering
matters and is not obvious, name it. A comment is weaker than a small ordered
list of steps the mediator walks.

**Lifecycle.** Colleagues frequently outlive or predecease the mediator. A
colleague holding a strong reference to a mediator that holds a strong reference
back is a cycle, which leaks in reference-counted runtimes such as Swift, and
becomes a retained-graph problem in tracing collectors when the mediator is
reachable from a long-lived root. Register and deregister colleagues explicitly,
and prefer a weak back-reference from mediator to colleague when the colleague's
lifetime is owned elsewhere.

## 8. Implementation variants

**Classic abstract mediator with a single notify.** The GoF shape. One operation,
a sender argument, an event tag. Maximum uniformity, minimum typing. The cost is
a growing conditional inside `notify` and a payload that has to be untyped or
cast. Suitable when the colleague set is uniform, for example a grid of cells
that all report the same kind of change.

**Named-operation mediator.** The mediator abstraction declares one method per
interaction, `onCountryChanged(code)`, `onPromoApplied(code)`. The dispatch moves
from a runtime conditional to compile-time method resolution, the payloads are
typed, and the interface documents the interaction vocabulary. The cost is that
the abstraction grows a method per interaction, so it is visibly the thing that
must not grow forever. That visibility is a feature. This is the variant to
default to in a typed language.

**Colleague-facing narrow interfaces.** Rather than one fat Mediator interface
that every colleague sees, each colleague sees only the subset it uses. The
country dropdown sees `CountryEvents`, the promo field sees `PromoEvents`, and
the ConcreteMediator implements both. Interface Segregation applied to the
pattern. It costs more types and buys real reuse of colleagues plus far smaller
test doubles.

**Function-valued mediator.** In a language with first-class functions, the
colleague holds a callback rather than an object reference, and the mediator is a
closure over the colleague set. This is idiomatic in Go, in TypeScript for small
assemblies, and in Rust where the object graph shape is awkward. It removes the
Mediator interface entirely. It also removes the name, which is the loss. When
there are several distinct events, a struct of callbacks recovers the vocabulary
without recovering the class hierarchy.

**Mediator as a state machine.** The coordination logic is expressed as an
explicit machine with states, events and transitions rather than as a body of
conditionals. This variant resists the god-mediator failure best, because a
transition table has a natural size limit that a method body does not, and
because an unhandled combination becomes a visible gap rather than a silent
fallthrough. Reach for it as soon as the coordination has modes, for example a
form that behaves differently before and after submission.

**Event-tagged mediator with a dispatch map.** The mediator keeps a map from
event type to handler, populated at construction. It sits between the classic and
named-operation forms. It makes the rule set enumerable, which enables a test
asserting every declared event has a handler, and it makes rules addable without
editing a switch. It moves an unhandled event from a compile error to a runtime
miss, so the enumeration test is not optional.

**Hierarchical mediators.** One mediator per interaction cluster, with a parent
mediator coordinating the cluster mediators. This is the most useful answer to a
mediator that has grown too large, because it preserves the pattern while
restoring cohesion. The risk is that the parent becomes a god mediator over
mediators, so the split has to follow a real seam in the domain, not an arbitrary
line drawn to reduce file length.

**Mediator plus Command.** Colleagues report intent as command objects rather
than as method calls, and the mediator dispatches them. This buys a recordable,
replayable, undoable interaction log at low extra cost, which is why it is common
in editors. It costs one class per interaction and a layer of indirection that is
hard to justify when nothing needs recording. See dimension 13.

**Distributed mediator, the orchestrator.** The same shape across process
boundaries. A workflow orchestrator that calls services in an order the services
do not know is a Mediator at the system level, and the alternative, services
reacting to each other's events, is Observer at the system level. Everything in
this entry about centralisation applies, with the failure modes amplified,
because a distributed god mediator is also a deployment bottleneck and an
availability single point.

**Language note on Rust.** The classic shape resists Rust directly, because a
mediator holding mutable references to colleagues while colleagues hold
references back is precisely the aliasing the borrow checker rejects. The
workable shapes are an owned collection of colleagues addressed by index, with
the mediator owning the collection, or channels where the mediator owns the
receiving end. The index-based form is idiomatic and is the reason Rust code
frequently ends up with a mediator-shaped design without anyone naming it.

**Language note on Go.** Go has no inheritance, so the Mediator abstraction is an
interface and the colleagues take it as a struct field. That translates cleanly
and the pattern is idiomatic. The function-valued variant is usually preferred
for small assemblies because a single-method interface and a function are
interchangeable in Go idiom.

## 9. Known production uses

**XMPP, RFC 6120, the server as required intermediary.** The protocol's
architecture forbids direct client-to-client links, so every stanza is routed by
the client's server, which decides delivery, applies policy and hands off to
remote servers. The specification describes communication between two clients as
logically peer to peer but physically a path of client to server to server to
client, and states that the server is "responsible for delivering stanzas to
other connected clients at the same server or routing them to remote servers".
Clients hold one relationship, to their server, and none to each other, which is
the pattern's defining invariant realised at protocol scale. Internet Engineering
Task Force, *RFC 6120, Extensible Messaging and Presence Protocol (XMPP). Core*,
section 2, Architecture, https://datatracker.ietf.org/doc/html/rfc6120 verified
2026-08-02.

**Kubernetes, the API server as the single coordination point.** The scheduler,
the controller manager, the kubelet on every node and the cloud controller
manager do not call each other. Each watches and writes cluster state through the
API server, which is documented as "the front end for the Kubernetes control
plane". Controllers observe state through the API server, the scheduler watches
for newly created Pods through the API, and the resulting topology is a star with
the API server at the centre. The design consequence is the one this entry
predicts. Adding a controller requires no change to any existing controller, and
the centre is the component that must scale, which is why the documentation notes
it is designed to scale horizontally by running several instances behind a load
balancer. Kubernetes project, *Cluster Architecture*,
https://kubernetes.io/docs/concepts/architecture/ verified 2026-08-02.

**Apache Camel, routing and mediation between endpoints.** Camel positions itself
as "a versatile open-source integration framework based on known Enterprise
Integration Patterns" that lets you "define routing and mediation rules in a
variety of domain-specific languages". A Camel route is coordination logic held
outside the systems being coordinated. The producing system does not know the
consuming system, both know only their endpoint, and the route holds the rules
about which message goes where and under what condition. The word mediation in
the project's own description is not accidental. Apache Software Foundation,
*What is Camel?*, https://camel.apache.org/manual/faq/what-is-camel.html verified
2026-08-02.

**MediatR for .NET, and why the name does not fit.** MediatR is the library most
developers name when asked for a current Mediator example, and the name invites
that. Its own description is narrower than the name suggests. The repository
tagline is "Simple mediator implementation in .NET", and the body text describes
it as "in-process messaging with no dependencies", supporting "request/response,
commands, queries, notifications and events, synchronous and async with
intelligent dispatching via C# generic variance". jbogard/MediatR, repository
README, https://github.com/jbogard/MediatR verified 2026-08-02.

Take the mechanics rather than the name. In the common MediatR usage, a caller
sends a request object and exactly one handler is located by type and invoked,
returning a response to the caller. Three properties of the GoF pattern are
absent from that flow.

- **There are no colleagues.** A GoF Mediator coordinates a known set of peers
  that hold references to it and report to it over their lifetime. A MediatR
  request handler is resolved from a container per request and has no standing
  relationship with any other handler.
- **The traffic is one-directional per call.** A GoF Mediator receives a
  notification and issues calls outward to several peers. A MediatR request is a
  point-to-point dispatch from one caller to one handler.
- **The coordination logic is absent.** The defining content of a
  ConcreteMediator is the rules about how peers affect each other. MediatR holds
  no such rules. It holds a resolution mechanism and a behaviour pipeline.

What MediatR actually implements is closer to Command, in the GoF sense of an
invocation reified as an object, plus a dispatcher that decouples the caller from
the handler type, plus a decorator chain in the pipeline behaviours. Its
`INotification` publish path is genuinely fan-out, which is Observer or Event
Aggregator rather than Mediator. The honest reading is that MediatR is a
well-built in-process command dispatcher whose name has cost the industry a great
deal of conceptual clarity, because a generation of developers now believes
Mediator means "send a message to a handler". It does not. The library is not
wrong, the naming is misleading, and a code review that says "this is not the
Mediator pattern" about a MediatR usage is correct on the pattern and irrelevant
to whether the library is a good choice.

**Event Aggregator as the neighbouring named pattern.** Martin Fowler's write-up
sits in the same space and is worth naming as a documented alternative rather
than as a production use. It describes a component acting as a single source of
events for many objects, so that a client subscribes once instead of once per
source. Fowler compares it to Facade on that page and does not compare it to
Mediator, so the comparison drawn in dimensions 1, 12 and 13 is mine and not his.
Martin Fowler, *Event Aggregator*,
https://martinfowler.com/eaaDev/EventAggregator.html verified 2026-08-02.

**A note on the air traffic control example.** Air traffic control is the analogy
most frequently attached to this pattern in teaching texts, and it is a good
analogy. Aircraft do not negotiate separation with each other, they report
position to a controller who holds the rules and issues instructions. That is the
pattern exactly. It is not, however, a Gang of Four example. The motivating
example in the book is a dialog box, with an abstract `DialogDirector` defining
the overall behaviour of a dialog and a concrete `FontDialogDirector`
coordinating widgets such as a list box and an entry field, which is also the
source of the Dialog Director alias in dimension 1. The attribution of the air
traffic analogy to the book is a widespread and harmless error, but this entry
states the correction plainly rather than repeating it. I could not verify a
specific page number for the FontDialogDirector example from an independently
checkable source, so no page is cited for it.

## 10. Consequences

Positive.

- Peer-to-peer coupling collapses from quadratic to linear in the number of
  participants. On an assembly of eight interacting objects that is a drop from
  up to twenty-eight possible edges to eight actual ones.
- Colleagues become reusable, because a colleague that names no peer can be
  lifted into a different assembly with a different mediator.
- The interaction rules become a first-class, reviewable artefact rather than an
  emergent property of scattered handlers. Somebody can read the rules.
- Varying the interaction becomes a matter of substituting a mediator, which
  makes A/B variants, tenant-specific behaviour and progressive rollout of a rule
  change tractable.
- Cross-peer invariants become enforceable, because one object observes every
  transition in order.
- A single chokepoint exists for logging, tracing, recording, replay and undo,
  which is worth more operationally than most of the design arguments.
- Colleagues become unit-testable without their peers, since a test supplies a
  fake mediator and nothing else.

Negative.

- The mediator centralises complexity and tends to grow without bound. This is
  the primary failure and dimension 11 treats it first.
- The mediator becomes a single point of failure at runtime and a single point of
  contention at development time. Every team edits it, so it is a merge hotspot
  and a review queue.
- The mediator knows every colleague, so it is the least reusable object in the
  design by construction. It is written once, for this assembly, and thrown away
  with it.
- Debugging becomes indirect. A stack trace from a colleague action shows the
  mediator, not the originating colleague, so causality has to be recovered from
  logs or from a correlation identifier.
- Two hops replace one call, which costs latency in hot paths and costs a frame
  of stack depth everywhere.
- Reentrancy hazards appear that did not exist with direct calls, because the
  mediator can be re-entered mid-rule.
- The pattern can hide missing domain modelling. Rules that belong on a domain
  object end up in a technical coordinator, which is how a mediator becomes a
  transaction script and the domain model becomes anemic.

## 11. Failure modes and misuse

**The god mediator.** This is the defining failure of the pattern, and it is not
a rare edge case, it is the default outcome without deliberate resistance.

- **Symptom.** One file in the repository has grown past a thousand lines and
  every feature branch touches it, so merge conflicts in that one file take up
  most of the team's rebase time. Its class name is a noun with no meaning,
  `AppManager`, `FormController`, `GameCoordinator`. It has more than a dozen
  fields, each a colleague. Its test file is the slowest in the suite and needs
  eight fakes to construct the subject. Nobody on the team can describe what it
  does in one sentence, and the code review comment "should this go in the
  mediator" is answered yes by reflex.
- **Cause.** The mediator is the only object in the design that is allowed to
  know about more than one thing, so it is the path of least resistance for every
  piece of logic whose home is unclear. The pattern creates a legitimate home for
  cross-cutting rules and provides no rule for what does not belong there. Over
  time it accretes not only the coordination it was created for, but also the
  peer logic it was meant to coordinate, and the design arrives back at the thing
  it replaced, with the difference that the tangle now sits inside one class
  instead of spread across several. Formatting has improved. Coupling has not.
- **Fix.** Three moves, in order of preference. First, split by interaction
  cluster into hierarchical mediators, per dimension 8, following a real seam.
  Second, push logic that concerns only one colleague back into that colleague,
  which is usually a large fraction of what accumulated. A useful test is whether
  a method in the mediator names exactly one colleague. If so it does not belong
  there. Third, convert the mediator to an explicit state machine, which caps the
  growth because a transition table cannot silently absorb unrelated behaviour
  the way a method body can. Add a standing guard, either a file-size threshold
  in review or a lint on colleague count, because the growth is gradual and no
  single commit looks wrong.

**A colleague that reaches sideways.** Symptom. A change to one widget breaks a
second widget that the mediator does not connect, and no rule in the mediator
explains the link. Cause. Somewhere a colleague was given a direct reference to a
peer, usually during a hurried fix, and the star topology now has one chord in
it. Fix. Delete the reference and route the interaction through the mediator.
Prevent recurrence with an architecture test asserting that no colleague type
appears in the imports of another colleague type, which most languages support
through a dependency-rule linter.

**Infinite notification loop.** Symptom. Stack overflow, or a UI that pegs a core
and freezes, triggered by one specific user action and not reproducible in unit
tests that call the mediator directly. Cause. The mediator updates a colleague,
the colleague's setter fires a change notification, the mediator handles it and
updates the colleague again. Fix. Add a reentrancy guard that queues
notifications received while a rule is executing, or give colleagues a
notification-suppressing setter used only by the mediator. Add a test that
performs the triggering action and asserts the mediator handled a bounded number
of notifications.

**Mediator used where Observer was needed.** Symptom. The mediator's rule table
is a long list of entries of the form "when X happens, call these four things",
with no condition anywhere, and adding a fifth listener means editing the
mediator. Cause. The interaction is fan-out, not coordination, and Mediator was
chosen for the name rather than for the mechanics. Fix. Replace with Observer or
an event bus, so listeners register themselves and the source needs no edit. Keep
a mediator only for the interactions that genuinely decide something.

**Anemic colleagues.** Symptom. Colleague classes are data bags with getters and
setters and no behaviour, and every real method in the feature lives in the
mediator. Cause. The team applied "colleagues must not know each other" as
"colleagues must not think", and pulled all logic out rather than only the
cross-peer logic. Fix. Move behaviour that concerns a single colleague's own
state back onto that colleague. The mediator should hold only rules that
reference two or more colleagues.

**Hidden ordering dependency.** Symptom. Reordering two apparently unrelated
lines in the mediator changes behaviour, and a test that passes in isolation
fails when a colleague is initialised in a different sequence. Cause. The rule
body encodes a dependency between colleague updates in statement order, with
nothing declaring it. Fix. Make the order explicit, either by naming the phases
or by having the mediator compute a full target state and apply it in one pass
rather than mutating colleagues incrementally.

**Retain cycle or listener leak.** Symptom. Memory grows across screen
navigations in a mobile app, or a long-running process holds objects that should
be dead, and a heap dump shows colleagues retained by a mediator that is itself
retained by a colleague. Cause. Strong references in both directions with no
deregistration. Fix. Weak back-references from mediator to colleague where the
colleague's lifetime is owned elsewhere, plus explicit deregistration on
teardown, plus a test that asserts the colleague is collectable after teardown.

**Mediator as a covert global.** Symptom. Colleagues acquire the mediator from a
static field or a service locator rather than receiving it, and tests fail
depending on execution order. Cause. Wiring the star topology felt tedious, so
the mediator was made ambient. Fix. Inject the mediator explicitly through the
constructor. The wiring tedium is the visible cost of the design, and hiding it
does not remove it, it only removes the ability to substitute the mediator in a
test.

**Distributed god mediator.** Symptom. A workflow orchestration service sits on
the critical path of every request, every team's change requires a release of it,
and its incident history fills the postmortem log. Cause. The in-process failure
mode, deployed. Fix. Split by bounded context, and move interactions that need no
decision to choreography, keeping orchestration only where a real decision or a
real transaction boundary lives.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3.

| Force | Mediator | Observer | Facade | Event Aggregator (Fowler) | Chain of Responsibility | Direct peer references | Command dispatcher (MediatR style) |
|---|---|---|---|---|---|---|---|
| Peer-to-peer coupling | Low. Star topology, N edges | Low between peers, source knows only the observer contract | Not addressed. Subsystem parts stay coupled | Low. Sources and listeners never meet | Low. Each link knows only the next | High. Up to N times N minus one over two edges | Low. Caller knows only the request type |
| Coupling to the centre | High. Centre knows every peer | None. No centre exists | Medium. Facade knows the subsystem | Low. Centre knows only event types | None | None | Low. Dispatcher knows only types |
| Directionality | Multi-directional. Peers report in, centre calls out | One-directional. Source to observers | One-directional. Client into subsystem | One-directional. Publishers to subscribers | One-directional along the chain | Any | One-directional. Caller to handler |
| Holds decision logic | Yes. That is its content | No. Observers decide for themselves | No. It forwards and simplifies | No. It forwards | Yes, per link, locally | Distributed across peers | No. It resolves and invokes |
| Adding a participant | Edit the mediator | No edit. Register an observer | Edit the facade if exposed | No edit. Subscribe | Insert a link | Edit every peer that must know | No edit. Register a handler |
| Cross-participant invariants | Strong. One place sees all state | Weak. No single observer sees all | Not addressed | Weak | Weak | Weak, by convention only | Not addressed |
| Cognitive load, reading one peer | Low | Low | Low | Low | Low | High | Low |
| Cognitive load, understanding the whole | High. Concentrated in one file | High. Diffused across subscriptions | Low | High. Diffused, and harder, no rules exist to read | Medium. Follow the chain | High. Diffused and dense | Medium |
| Debuggability of causality | Medium. One chokepoint to log, but stacks lose the origin | Poor. Fan-out with no record | Good. Direct calls | Poor | Good. Linear trace | Good. Direct stack traces | Medium |
| Operability, tracing | Strong. Single instrumentation point | Weak. Instrument every subscription | Neutral | Medium. One point, no semantics | Medium | Poor | Strong. Pipeline behaviours |
| Single point of failure | Yes | No | Yes for the entry path | Yes | No | No | Yes |
| Latency | Two hops per interaction | One dispatch to N observers | One hop | Two hops | Up to N hops | One direct call | Two hops plus container resolution |
| Team topology | Poor. Shared hotspot file | Good. Teams own their observers | Neutral | Good | Good | Poor. Every change is cross-team | Good. Handler per team |
| Reuse of a participant | Good. Peers name no peers | Good | Not addressed | Good | Good | Poor | Good |

Reading of the table. Mediator wins where interactions require a decision that
consults several participants and where cross-participant invariants matter.
Observer wins where the interaction is notification with no decision and the
listener population is open. Facade wins where the goal is a simpler way in and
nothing inside needs to call out. Event Aggregator wins where the problem is
subscription bookkeeping rather than interaction rules. Chain of Responsibility
wins where the interaction is a sequence with an order. Direct references win
where there are two or three participants and the pattern would cost more than
the tangle. A command dispatcher wins where the problem is decoupling a caller
from a handler type, which is a different problem from all of the above and is
the reason the MediatR naming confusion persists.

## 13. Related and incompatible patterns

**Observer.** The most important comparison, and the pair is best understood as
opposite answers to the same question. Both decouple objects that must react to
each other. Mediator answers by **centralising**, putting all interaction
knowledge in one object that every participant reports to. Observer answers by
**decentralising**, giving each source a list of listeners and letting each
listener decide what to do. The consequences follow mechanically. With Mediator,
the rules are readable in one place and a new participant costs an edit at the
centre. With Observer, no edit is needed to add a listener and no place describes
the whole interaction. Choose Mediator when somebody needs to be able to read the
rules and when the rules involve a decision. Choose Observer when the population
of listeners is open and each listener's reaction is its own business. The two
also compose. A common and sound arrangement has colleagues notify the mediator
through an Observer mechanism, so the colleague does not even hold a mediator
reference, and the mediator holds all the rules. That composition keeps the
centralised rules and removes the upward reference, at the cost of a less direct
call path.

**Facade.** The second comparison people get wrong, and the distinction is
directionality. A Facade is **one-directional**. A client calls into the facade,
the facade calls into the subsystem, and nothing in the subsystem ever calls back
out through the facade. The subsystem does not know the facade exists, and the
facade adds no behaviour, it selects and simplifies. A Mediator is
**multi-directional**. Colleagues call in, the mediator calls back out to other
colleagues, and every colleague knows the mediator by design. The mediator adds
behaviour, specifically the coordination rules, which is its entire content. A
second difference follows. Removing a Facade leaves a working system that is
merely harder to use. Removing a Mediator leaves a system that does not work,
because the rules lived in it. If the object you are building can be deleted
without breaking anything except convenience, it is a Facade.

**Command.** Composes cleanly and frequently. Colleagues report intent as command
objects and the mediator dispatches and records them, which produces an undo
stack and a replayable interaction log at low extra cost. Reach for the
combination when recording, undo or audit is a real requirement, and not
otherwise, because the class count grows by one per interaction.

**Adapter.** When a colleague cannot be changed, for example a third-party widget
with a fixed interface, an Adapter wraps it to present the colleague contract the
mediator expects. This is the standard way to bring foreign objects into a
mediated assembly without forking them.

**Memento.** Pairs with a mediator that owns cross-peer state. Because the
mediator is the one object that sees the whole interaction state, it is the
natural originator of a snapshot covering the assembly, which a per-colleague
memento cannot produce coherently.

**State.** An alternative framing rather than a collaborator. When the
coordination has modes, expressing the mediator as a State machine, per dimension
8, is often better than expressing it as conditionals. The two are the same
object seen through different lenses.

**Singleton.** Conflicts in practice. A mediator made a process-wide singleton
loses the substitutability that made it worth adopting, cannot be varied per
assembly, and makes tests order-dependent. If a single instance is genuinely
right, scope it to the assembly's lifetime rather than to the process.

**Service Locator.** Actively conflicts, for the same reason it conflicts with
most patterns that depend on explicit wiring. A colleague fetching its mediator
from a locator hides the relationship the pattern exists to make explicit, and
removes the ability to substitute a fake mediator in a test.

**Event Aggregator.** Adjacent and frequently confused, per dimension 1. The
distinguishing test is whether the central object holds rules. If removing the
central object's logic leaves a working forwarder, it is an Event Aggregator. If
it leaves nothing, it is a Mediator.

**Broker and Message Broker.** Related at the topology level, different at the
responsibility level. A broker owns transport concerns, delivery, durability and
ordering. A mediator owns interaction rules. Systems commonly need both, and
combining them into one component is a design decision that should be taken
deliberately rather than by accident of naming.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The named refactorings
that apply are Extract Class, followed by Move Method for each rule, and Replace
Inline Code with Function Call, all cross referenced in the refactoring family.
Ordered steps.

1. **Draw the current graph.** List every peer and every reference one peer holds
   to another. Do this literally, on paper or in a comment, because the decision
   to adopt the pattern rests on whether that graph is genuinely dense. Four
   peers with three edges do not need a mediator. Six peers with fourteen edges
   do.
2. **Identify the interaction rules.** For each cross-peer reference, write the
   rule it implements as one sentence. Sentences that mention two or more peers
   are candidates for the mediator. Sentences that mention one peer belong on
   that peer and should be left alone, and often should be pushed further into
   the peer first.
3. **Create an empty concrete mediator with no abstraction yet.** Give it a
   reference to every peer and give every peer a reference to it. Nothing works
   differently. Run the tests. This step is deliberately mechanical so the risky
   part is isolated to step 4.
4. **Move one rule.** Pick the rule with the fewest peers involved. Move the code
   from the peer into the mediator, and replace it in the peer with a
   notification call. Run the tests. Repeat for one rule at a time, never in
   batches, because a partially moved rule leaves the system in a state where
   both copies can fire.
5. **Delete the peer-to-peer references** as each becomes unused. The moment a
   peer holds no reference to another peer, it has become reusable, which is
   worth confirming by moving it in a test.
6. **Extract the mediator abstraction.** Only now, once the rule set is known,
   declare the interface the colleagues depend on. Doing this before step 4
   produces an interface shaped by guesswork. Prefer named operations over a
   single notify, per dimension 8.
7. **Segregate the colleague-facing interfaces** if the mediator now has more
   than three or four colleagues, so each colleague sees only what it uses.
8. **Add the reentrancy guard** and a test that exercises the interaction that
   round-trips, per dimension 11. Do this before shipping, not after the first
   freeze report.
9. **Add the enumeration test** if the dispatch-map variant was chosen, asserting
   every declared event has a handler.

Removing the pattern when it stops earning its place. Signals include a mediator
whose methods each name exactly one colleague, an assembly that has shrunk to two
or three peers after a feature removal, or a rule set that turned out to be pure
fan-out.

1. **Classify every mediator method** by how many colleagues it names. One
   colleague means it should move back to that colleague. Zero colleagues means
   it is unrelated logic that landed here and belongs elsewhere entirely.
2. **Move the single-colleague methods home** first, one at a time, running tests
   between each. This alone frequently shrinks a god mediator by half and may
   remove the reason to delete it.
3. **If what remains is pure fan-out**, replace the mediator with an Observer
   registration. Sources publish, listeners subscribe, and the mediator's
   remaining body becomes subscription wiring which then moves to the composition
   root.
4. **If what remains is two peers**, give them direct references and delete the
   mediator. Two objects that talk do not need a coordinator.
5. **If what remains is a sequence**, replace with a pipeline or Chain of
   Responsibility, which expresses the ordering the mediator was hiding.
6. **Delete the colleague notification calls** and the mediator abstraction last,
   after every rule has a new home, so the intermediate states stay compilable.

There is a third path that is neither in nor out, and it is the most common
correct answer for a mediator that has grown too large. Split it. Apply steps 1
and 2 of the removal path to identify cohesion, then group the remaining
multi-colleague rules into clusters and give each cluster its own mediator, with
a parent mediator only if the clusters genuinely interact. This preserves the
benefits and restores the cohesion that growth destroyed.

## 15. Testing and verification

Easier because of the pattern.

- **The rules are testable in isolation.** The mediator is a plain object with no
  input, no output and no rendering. Construct it with fake colleagues, send a
  notification, and assert which colleagues were called with what. This is the
  main testability payoff and it converts what used to be an integration test
  across several widgets into a fast unit test.
- **The colleagues are testable in isolation.** A colleague names no peer, so its
  test needs one fake, the mediator, rather than a fake per peer.
- **Interaction sequences become assertable.** A recording fake mediator that
  appends every notification to a list turns "the right things happened in the
  right order" into a list comparison, which is far cheaper than reconstructing
  order from several mocks.
- **Cross-peer invariants become directly testable.** Property tests that
  generate arbitrary notification sequences and assert an invariant after each
  step are practical, because the mediator is the only object that has to be
  exercised.

Harder because of the pattern.

- **The mediator test needs many collaborators.** Constructing it means supplying
  every colleague, which makes the test setup large and brittle to colleague
  additions. This grows with the god-mediator failure and is an early warning
  sign of it. A builder for the test fixture helps. A smaller mediator helps
  more.
- **Causality is not visible in a failure.** A failing assertion says the wrong
  colleague method was called, not which upstream event caused it, because the
  stack shows the mediator. Recording the originating notification alongside the
  outgoing call in the fake fixes this and is worth the small extra code.
- **Reentrancy bugs do not reproduce in the obvious test.** Calling the mediator
  directly from a test does not exercise the path where a colleague notifies from
  inside a mediator-issued call. The test has to use a fake colleague that
  deliberately notifies back.

Techniques that apply.

- **Recording fake mediator.** A test double implementing the Mediator contract
  and appending each notification to an ordered list. Prefer this to a mocking
  framework for colleague tests, because the assertion is a comparison of two
  lists and reads better than a set of verify calls.
- **Spy colleagues over mocks.** For mediator tests, small handwritten colleague
  fakes that record calls beat mock frameworks, because the mediator normally
  calls several colleagues per rule and mock verification of ordered
  multi-object interaction is unpleasant to read in every framework.
- **Reentrancy test.** One test per notification that can round-trip, using a
  fake colleague whose setter notifies the mediator, asserting that the mediator
  terminates and that the notification count is bounded.
- **Contract test for the colleague role.** When several colleagues share a
  contract, write one test class against the contract with an abstract creation
  hook and subclass it per colleague, so every colleague is checked for the
  no-sideways-reference invariant and for correct notification on state change.
- **Architecture test on the dependency rule.** A static check asserting no
  colleague type references another colleague type. This is the only mechanical
  defence against the sideways-reference failure in dimension 11, and every major
  language has a linter or a dependency-rule tool that can express it.
- **Size guard on the mediator.** A check in review or in CI on the mediator's
  colleague count or method count. Crude, and the only thing that reliably
  catches gradual growth, because no single commit that adds one method to a
  mediator looks like a problem.

## 16. Observability signals

The pattern moves every interaction through one object, which is the best
instrumentation opportunity the GoF catalog offers and is frequently the
strongest practical argument for adopting it. The corresponding hazard is that
the source no longer shows causality, so if the mediator is not instrumented,
nothing is.

What to record.

- **A structured event per notification**, holding the originating colleague
  identifier, the event name, a correlation identifier for the user action or
  request in progress, and the sequence number within that correlation. The
  sequence number is what lets an operator reconstruct causality that the stack
  no longer shows.
- **A structured event per outbound call** the mediator issues, holding the
  target colleague, the operation, and the same correlation identifier. Paired
  with the inbound record, this yields a complete interaction trace.
- **A counter of notifications, labelled by event name.** The label distribution
  answers which interactions are actually exercised in production, which is the
  input to deciding what to simplify.
- **A counter of unhandled notifications**, for the dispatch-map variant. This
  should be flat at zero, and any movement is a bug.
- **A histogram of rule execution duration**, labelled by event name, when rules
  do input or output. A mediator that performs blocking work inside a rule is a
  latency amplifier because every colleague waits behind it.
- **A gauge of registered colleagues**, which is the leak detector. It should be
  flat for a long-lived mediator and should return to its baseline after every
  teardown for a short-lived one.
- **A counter of reentrant notifications**, incremented whenever the reentrancy
  guard queues rather than executes. A small nonzero value is normal in a UI. A
  climbing value points at a rule that mutates state the mediator is already
  reasoning about.
- **A depth or queue-length gauge** for the reentrancy queue, which is the early
  warning for the notification-loop failure.

A healthy instance on a dashboard. The notification counter shows a mix matching
the user behaviour the product expects, and it moves only when a release or a
traffic change explains it. Rule duration is flat and small relative to the
enclosing user action. The registered-colleague gauge is flat, or sawtooths
cleanly with screen lifecycle and returns to baseline. Unhandled notifications
are zero. Reentrancy queueing is either zero or a small constant fraction.

A failing instance. The reentrancy queue depth climbs, which is the loop from
dimension 11 forming before it becomes a freeze. Or the registered-colleague
gauge climbs monotonically across navigations, which is the retain cycle. Or one
event name's counter climbs while the outbound counters that should follow it
stay flat, which means a rule is silently taking a branch that does nothing, and
that is usually a condition that stopped matching after a data change upstream.
Or the rule duration histogram grows a long tail on a single event name, which
localises a slow rule to one interaction without reading any code. Or the total
notification count per user action climbs release over release, which is the
quantitative signature of the god mediator, since accreted rules produce extra
internal traffic even when the user-visible behaviour is unchanged. That last
metric is the one worth alerting on, because it is the only early warning the
failure gives.

## 17. Security and privacy implications

The pattern is close to silent on security in its classical, in-process form
where every colleague ships in the same build. Claiming otherwise would be
inventing a concern. Four genuine implications appear once the mediator becomes a
boundary or an extension point.

**The mediator is an authorisation chokepoint, for better and worse.** Because
every interaction passes through one object, that object is the natural place to
enforce which participant may trigger which effect, and a mediated design makes
that enforcement practical where a peer-to-peer design does not. The same
property means a defect in the mediator is a complete bypass rather than a local
one. Where the mediator carries authorisation, its rules deserve the test
coverage and review weight of security code, not of UI glue.

**Confused deputy through unauthenticated notification.** The mediator acts on
behalf of whichever colleague notified it, and in the plain form it takes the
sender's identity from the call rather than verifying it. If any code can obtain
the mediator reference and send a notification claiming to be a privileged
colleague, it inherits that colleague's ability to trigger effects. This matters
whenever the mediator is reachable from a plugin, a script host, or an untrusted
extension. The defence is to hand each colleague a distinct, non-forgeable
capability object rather than letting it name itself in a shared notification,
which is one of the practical arguments for the segregated colleague interfaces
in dimension 8.

**Cross-colleague data flow that no colleague authorised.** A mediator that reads
state from one colleague and writes it to another has created a data path that
neither colleague declares. Where colleagues hold data of different
classifications, for example a form field holding a payment number and a
telemetry component holding diagnostics, a rule in the mediator can move
regulated data into an unregulated sink without any code in either colleague
showing it. Treat the mediator as a data-flow boundary during a privacy review,
because it is the only file where such a flow is visible, and it is easy to miss
precisely because both endpoints look innocent.

**Registration poisoning in the pluggable form.** When colleagues register
themselves with the mediator at runtime, whichever registration happens last for
a given role wins. Code that can influence load order or add a module can
substitute a colleague whose operations the mediator will then call with whatever
the rules pass it. Make duplicate registration for a role fail loudly rather than
overwrite, and pin the colleague set at build time where the set is known.

On privacy the pattern is otherwise neutral, with one caveat that follows from
dimension 16. The instrumentation advice records the originating colleague
identifier and the correlation identifier on every interaction. Where colleague
identifiers encode a tenant, a region or a user-scoped component, and where the
correlation identifier is derived from a session, those log fields are
attributable data and carry the retention and access obligations of any other
identifier. Interaction traces are also unusually revealing as a class, because a
complete ordered record of which controls a person touched, in what order, is
behavioural data even when no field value is logged. Sample it, redact the event
payloads by default, and set the retention deliberately rather than inheriting
the default of the logging system.

## Code examples

Three languages where the pattern is idiomatic in different ways. TypeScript
shows the named-operation form on a UI assembly, which is the pattern's home
ground. Python shows the mediator as an explicit rule holder over a set of non-UI
peers, with the reentrancy guard included because that is where it bites. Java
shows the classical GoF shape with an abstract mediator and a colleague base
class, which is the form the book describes.

Go is omitted from the runnable examples because its idiomatic answer collapses
to an interface plus a struct field, which is the same shape as the TypeScript
example with different syntax and no extra teaching value. Rust is omitted
because the classic shape does not translate, as covered in dimension 8, and the
index-based workaround teaches more about the borrow checker than about the
pattern.

Verification note. The TypeScript example was checked by reading it against the
compiler rules for the constructs used and it carries no imports, so it runs
under any recent Node with a TypeScript loader. The Python example was written
against the standard library only and uses no third-party packages. The Java
example uses only `java.util` and compiles as a single file under Java 17 or
later. I did not execute any of the three in this environment, so treat them as
reviewed rather than as executed.

### TypeScript

The named-operation form. Each colleague holds a narrow view of the mediator.

```typescript
interface FormMediator {
  countryChanged(code: string): void;
  regionChanged(code: string): void;
  promoChanged(code: string): void;
}

class Dropdown {
  private value = "";
  private options: string[] = [];

  constructor(
    private readonly name: string,
    private readonly onPick: (v: string) => void,
  ) {}

  setOptions(options: string[]): void {
    this.options = options;
    this.value = "";
  }

  pick(value: string): void {
    if (!this.options.includes(value)) throw new Error("bad option");
    this.value = value;
    this.onPick(value);
  }

  get selected(): string {
    return this.value;
  }

  get label(): string {
    return `${this.name}=${this.value || "-"}`;
  }
}

class TextField {
  private text = "";
  constructor(private readonly onType: (v: string) => void) {}

  type(value: string): void {
    this.text = value;
    this.onType(value);
  }

  get value(): string {
    return this.text;
  }
}

class SubmitButton {
  private enabled = false;
  setEnabled(on: boolean): void {
    this.enabled = on;
  }
  get isEnabled(): boolean {
    return this.enabled;
  }
}

const REGIONS: Record<string, string[]> = {
  DE: ["BY", "BE", "NW"],
  US: ["CA", "NY", "TX"],
};

class CheckoutMediator implements FormMediator {
  readonly country = new Dropdown("country", (v) => this.countryChanged(v));
  readonly region = new Dropdown("region", (v) => this.regionChanged(v));
  readonly promo = new TextField((v) => this.promoChanged(v));
  readonly submit = new SubmitButton();
  private discount = 0;

  constructor() {
    this.country.setOptions(Object.keys(REGIONS));
  }

  countryChanged(code: string): void {
    this.region.setOptions(REGIONS[code] ?? []);
    this.revalidate();
  }

  regionChanged(_code: string): void {
    this.revalidate();
  }

  promoChanged(code: string): void {
    this.discount = code === "SAVE10" ? 10 : 0;
    this.revalidate();
  }

  // The only rule reading more than one colleague. That is the test
  // for whether logic belongs in a mediator at all.
  private revalidate(): void {
    const ok = this.country.selected !== "" && this.region.selected !== "";
    this.submit.setEnabled(ok);
  }

  get summary(): string {
    return `${this.country.label} ${this.region.label} ` +
      `discount=${this.discount} submit=${this.submit.isEnabled}`;
  }
}

const form = new CheckoutMediator();
form.country.pick("DE");
console.log(form.summary);
form.region.pick("BY");
form.promo.type("SAVE10");
console.log(form.summary);
```

The colleagues name no peer. Lifting `Dropdown` into a different form costs
nothing, which is the reuse benefit from dimension 10 made concrete.

### Python

A non-UI assembly with the reentrancy guard, which is the part most examples omit
and most production code needs.

```python
from __future__ import annotations
from collections import deque
from typing import Protocol


class Mediator(Protocol):
    def notify(self, sender: str, event: str, payload: object) -> None: ...


class Colleague:
    def __init__(self, name: str, mediator: Mediator) -> None:
        self.name = name
        self._mediator = mediator
        self._muted = False

    def _emit(self, event: str, payload: object) -> None:
        if not self._muted:
            self._mediator.notify(self.name, event, payload)


class Thermostat(Colleague):
    def __init__(self, mediator: Mediator) -> None:
        super().__init__("thermostat", mediator)
        self.target = 20.0

    def set_target(self, value: float, silent: bool = False) -> None:
        self._muted = silent
        try:
            self.target = value
            self._emit("target_changed", value)
        finally:
            self._muted = False


class Boiler(Colleague):
    def __init__(self, mediator: Mediator) -> None:
        super().__init__("boiler", mediator)
        self.firing = False

    def set_firing(self, on: bool) -> None:
        self.firing = on


class WindowSensor(Colleague):
    def __init__(self, mediator: Mediator) -> None:
        super().__init__("window", mediator)
        self.open = False

    def set_open(self, value: bool) -> None:
        self.open = value
        self._emit("window_changed", value)


class HeatingMediator:
    def __init__(self) -> None:
        self.thermostat = Thermostat(self)
        self.boiler = Boiler(self)
        self.window = WindowSensor(self)
        self.room_temp = 18.0
        self._running = False
        self._queue: deque[tuple[str, str, object]] = deque()
        self.reentrant_count = 0

    # The guard from dimension 7. Without it, a rule that writes a
    # colleague which notifies back re-enters and reasons on half state.
    def notify(self, sender: str, event: str, payload: object) -> None:
        if self._running:
            self.reentrant_count += 1
            self._queue.append((sender, event, payload))
            return
        self._running = True
        try:
            self._dispatch(sender, event, payload)
            while self._queue:
                self._dispatch(*self._queue.popleft())
        finally:
            self._running = False

    def _dispatch(self, sender: str, event: str, payload: object) -> None:
        if event == "window_changed":
            self._on_window(bool(payload))
        elif event == "target_changed":
            self._reconcile()

    def _on_window(self, is_open: bool) -> None:
        if is_open:
            # Writes the thermostat silently so the write does not
            # re-enter. The guard would catch it either way.
            self.thermostat.set_target(16.0, silent=True)
        self._reconcile()

    def _reconcile(self) -> None:
        should_fire = (not self.window.open) and self.room_temp < self.thermostat.target
        self.boiler.set_firing(should_fire)

    def summary(self) -> str:
        return (
            f"target={self.thermostat.target} open={self.window.open} "
            f"firing={self.boiler.firing} reentrant={self.reentrant_count}"
        )


if __name__ == "__main__":
    house = HeatingMediator()
    house.thermostat.set_target(22.0)
    print(house.summary())
    house.window.set_open(True)
    print(house.summary())
    house.window.set_open(False)
    print(house.summary())
```

### Java

The classical shape from the book, with an abstract mediator and a colleague base
class, which is the form the `DialogDirector` example takes.

```java
import java.util.ArrayList;
import java.util.List;

interface DialogMediator {
    void widgetChanged(Widget source);
}

abstract class Widget {
    protected final DialogMediator mediator;
    protected final String name;

    protected Widget(String name, DialogMediator mediator) {
        this.name = name;
        this.mediator = mediator;
    }

    protected void changed() {
        mediator.widgetChanged(this);
    }

    String name() {
        return name;
    }
}

final class ListBox extends Widget {
    private final List<String> items = new ArrayList<>();
    private String selected = "";

    ListBox(String name, DialogMediator mediator) {
        super(name, mediator);
    }

    void setItems(List<String> values) {
        items.clear();
        items.addAll(values);
        selected = "";
    }

    void select(String value) {
        if (!items.contains(value)) throw new IllegalArgumentException(value);
        selected = value;
        changed();
    }

    String selected() {
        return selected;
    }
}

final class EntryField extends Widget {
    private String text = "";

    EntryField(String name, DialogMediator mediator) {
        super(name, mediator);
    }

    void setText(String value) {
        text = value;
    }

    String text() {
        return text;
    }
}

final class Button extends Widget {
    private boolean enabled;

    Button(String name, DialogMediator mediator) {
        super(name, mediator);
    }

    void setEnabled(boolean on) {
        enabled = on;
    }

    boolean enabled() {
        return enabled;
    }
}

final class FontDialogDirector implements DialogMediator {
    final ListBox family = new ListBox("family", this);
    final ListBox size = new ListBox("size", this);
    final EntryField preview = new EntryField("preview", this);
    final Button apply = new Button("apply", this);

    FontDialogDirector() {
        family.setItems(List.of("Serif", "Mono"));
        size.setItems(List.of("10", "12"));
    }

    @Override
    public void widgetChanged(Widget source) {
        if (source == family) {
            size.setItems(family.selected().equals("Mono")
                ? List.of("10", "12", "14")
                : List.of("10", "12"));
        }
        preview.setText(family.selected() + " " + size.selected());
        apply.setEnabled(!family.selected().isEmpty() && !size.selected().isEmpty());
    }

    String summary() {
        return preview.text() + " apply=" + apply.enabled();
    }
}

public final class Demo {
    public static void main(String[] args) {
        FontDialogDirector dialog = new FontDialogDirector();
        dialog.family.select("Mono");
        System.out.println(dialog.summary());
        dialog.size.select("14");
        System.out.println(dialog.summary());
    }
}
```

The single `widgetChanged` operation is the GoF form, and the conditional inside
it is the growth point warned about in dimension 8. In a real dialog this method
is where the god mediator begins, which is why the named-operation form in the
TypeScript example is the one to prefer once the widget count passes a handful.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 5, Behavioral Patterns, section Mediator. Source
   of the intent, the four participants, the `DialogDirector` and
   `FontDialogDirector` motivating example, and the Dialog Director alias. No
   page number is cited because I could not verify a specific page from an
   independently checkable source.
2. Wikipedia contributors. "Mediator pattern".
   https://en.wikipedia.org/wiki/Mediator_pattern
   Verified 2026-08-02. Used only to confirm the wording of the GoF intent and
   the four participant names, not as a source of explanation.
3. Martin Fowler. "Event Aggregator".
   https://martinfowler.com/eaaDev/EventAggregator.html
   Verified 2026-08-02. Source for the definition of Event Aggregator quoted in
   dimension 1 and for the Facade comparison quoted there. It is NOT the source
   of the Event Aggregator versus Mediator contrast in dimensions 1, 12 and 13.
   That contrast is this entry's own analysis, and the page makes no such
   comparison.
4. Internet Engineering Task Force. *RFC 6120, Extensible Messaging and Presence
   Protocol (XMPP). Core*. March 2011. Section 2, Architecture.
   https://datatracker.ietf.org/doc/html/rfc6120
   Verified 2026-08-02. Source of the quoted server-routing responsibility and
   the XMPP production use.
5. Kubernetes project. *Cluster Architecture*.
   https://kubernetes.io/docs/concepts/architecture/
   Verified 2026-08-02. Source of the API server front-end statement and the
   horizontal-scaling note in the Kubernetes production use.
6. Apache Software Foundation. *Apache Camel manual, What is Camel?*.
   https://camel.apache.org/manual/faq/what-is-camel.html
   Verified 2026-08-02. Source of the quoted routing and mediation description
   and the Enterprise Integration Patterns positioning.
7. Jimmy Bogard and contributors. *MediatR repository README*.
   https://github.com/jbogard/MediatR
   Verified 2026-08-02. Source of the quoted tagline and the in-process messaging
   description used in the dimension 9 analysis.

### Claims I could not verify, and therefore did not make

- No page number is asserted for any passage in the Gang of Four book, because I
  could not check a specific page against an independently reachable source.
- The Gang of Four Known Uses section for Mediator is not quoted or summarised,
  for the same reason.
- Martin Fowler is not cited as contrasting Event Aggregator with Mediator. A
  live read of his page on 2026-08-02 confirmed he compares it to Facade and
  never names Mediator. An earlier draft of this entry asserted that contrast as
  his, which was wrong, and the correction is recorded here rather than silently
  removed.
- The air traffic control analogy is stated as a widely used teaching analogy and
  explicitly not attributed to the Gang of Four, because no verified source
  places it in the book.
- Android's `CoordinatorLayout` and `CoordinatorLayout.Behavior` were considered
  as a production use and dropped. The official Android reference pages did not
  return their class summaries on fetch, and only secondary tutorial sites
  described them, which does not meet the sourcing bar for this repository.
- No claim is made about how any of these systems performs, scales or fails in
  practice beyond what the cited documents state.
