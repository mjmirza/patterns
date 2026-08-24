---
name: Low Coupling
slug: low-coupling
family: 04-principles-and-laws
category: Principle
aliases: [Loose Coupling, Weak Coupling, Minimal Coupling]
first_described: "Stevens, Myers, Constantine 1974 (structured design); Larman GRASP 1997"
maturity: canonical
related: [high-cohesion, dependency-inversion-principle, interface-segregation-principle, facade, observer, dependency-injection]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

Low Coupling is the principle that modules, classes, components, or services
should depend on one another as little as possible, and that the dependencies
that remain should be as narrow and as stable as possible. It is stated
positively as "loose coupling" or "weak coupling" in most industry writing,
and it is one of the two structural halves of a pairing with High Cohesion,
the other being that each unit should have a single, tightly related purpose.

The idea traces to Larry Constantine's work on structured design in the late
1960s, formalized in the paper "Structured Design" by Wayne P. Stevens,
Glenford J. Myers, and Larry L. Constantine, published in IBM Systems Journal,
volume 13, issue 2, pages 115 to 139, in June 1974. That paper introduced
coupling and cohesion as measurable properties of a modular decomposition and
proposed a taxonomy of coupling strength, from content coupling (the worst) to
data coupling (close to the best). A related and independently important
paper is David Parnas, "On the Criteria To Be Used in Decomposing Systems
into Modules", Communications of the ACM, volume 15, issue 12, pages 1053 to
1058, December 1972, DOI 10.1145/361598.361623. Parnas argued that a module
should hide a design decision behind an interface so that other modules do
not depend on that decision, which is the information hiding argument for low
coupling rather than the data flow argument the structured design school used.

The name Low Coupling as a named design principle inside an explicit
responsibility assignment method comes from Craig Larman, "Applying UML and
Patterns, An Introduction to Object-Oriented Analysis and Design and
Iterative Development", third edition, Prentice Hall, in the chapter that
introduces GRASP (General Responsibility Assignment Software Patterns).
Larman lists Low Coupling and High Cohesion as two of the nine GRASP
principles, alongside Information Expert, Creator, Controller, Polymorphism,
Pure Fabrication, Indirection, and Protected Variations. In that book Low
Coupling is presented as an evaluative principle, a lens for judging a
proposed responsibility assignment, rather than a pattern that produces code
directly.

A later refinement of the same idea is connascence, a taxonomy of coupling
types and coupling strength popularized by the reference site connascence.io,
which defines connascence as a software quality metric and a taxonomy for
different types of coupling, extending the earlier static and dynamic
coupling categories with named forms such as connascence of name, of type,
of position, of algorithm, and of execution order, each carrying a different
cost when the two connascent elements must change together.

## 2. Problem and context

Every nontrivial system is built from more than one unit of code, whether
those units are classes in one process, packages in one codebase, or services
across a network. The moment two units exist, a decision has to be made about
how much one is allowed to know about the internals of the other, and how
much a change inside one forces a change inside the other. A codebase where
every class reaches into every other class's fields, calls concrete
constructors of collaborators, and depends on a specific implementation
rather than a narrow contract, is a codebase where a single change ripples
outward unpredictably. The symptom a working engineer recognizes immediately
is the small fix that takes three days because it touches nineteen files that
had no obvious reason to know about each other.

The problem context is exactly this. A team is decomposing a system into
units, classes, modules, services, packages, and has to decide, for every
relationship between two units, how much one unit should depend on the
concrete details of the other. This decision recurs at every scale, within a
class between its private methods, between classes in a package, between
packages in an application, between services in a distributed system, and
between an application and the third-party libraries it imports. Low
Coupling names the goal state for that decision, and the surrounding body of
technique, interfaces, dependency inversion, events, facades, message
passing, is the mechanism for reaching it.

## 3. Forces

The forces below are named because Low Coupling is not free. Reducing
coupling always costs something else, and pretending otherwise is dishonest
engineering. The following weighting is judgement, drawn from practice across
many systems, not a citable fact.

Coupling and change cost pull directly against each other, and this is the
whole reason to want low coupling. A unit whose collaborators change
concrete shape often forces a wave of edits through everything that
depends on it, and lowering coupling is a direct bet against future change
cost.

Coupling and indirection pull against each other in the opposite direction
from the previous force. Every mechanism that lowers coupling, an interface,
an event bus, a facade, a message queue, inserts a layer between the caller
and the thing that actually does the work, and that layer costs a reader
mental effort to trace, costs the runtime a hop, and costs the team a new
artifact to maintain.

Coupling and performance can conflict, particularly at the boundary between
process-local and network-remote units. A tightly coupled, direct, in-process
call is cheaper in latency and simpler in failure modes than the same
relationship rebuilt as a decoupled asynchronous message across a network
boundary, so decoupling for its own sake at a boundary where the two units
will always deploy and scale together can be a pure cost.

Coupling and testability pull toward low coupling almost without exception.
A unit that depends on a narrow, mockable interface rather than a concrete
class with side effects is dramatically easier to test in isolation, and
this is one of the few forces in this list where the pull is nearly always
in the same direction as the principle's name.

Coupling and team topology interact through Conway's Law. Two teams that own
tightly coupled modules must coordinate every release, so an organization
that wants independently deployable teams has an organizational reason to
decouple its architecture along team boundaries even where the technical
argument alone might not demand it, and the inverse also holds, decoupling
code across a boundary that one team owns end to end adds process cost with
no organizational payoff.

Coupling and cognitive load pull toward low coupling for the reader trying to
understand one unit in isolation, and against it for the reader trying to
understand the system as a whole, because a system decoupled through many
small interfaces and indirections requires holding more names and more
seams in mind to trace one full behavior, even though each individual
piece is simpler.

The pattern favors change isolation, testability, and independent
deployability, and it sacrifices some directness, some traceability, and in
distributed contexts some latency and some operational simplicity.

## 4. Applicability and non-applicability

Reach for deliberately low coupling when a boundary in the system is likely
to change independently on either side. When a dependency is a third-party
library or an external service whose API or vendor might change. When two
units are or will be owned by different teams. When a unit needs to be
substituted for testing, for a different deployment target, or for a plugin
architecture. When a unit crosses a process, service, or repository
boundary and therefore already pays a network or deployment cost regardless
of how tightly the code is coupled. When the domain concept the boundary
represents is genuinely stable and well understood, so that a narrow
contract at that boundary is unlikely to need frequent widening. And when a
unit's internal representation, data layout, algorithm, storage engine, is
an implementation detail that callers should never have needed to observe in
the first place.

Do not chase low coupling in these situations, and each has a concrete
reason.

Do not decouple two classes that are conceptually one idea split for no
reason, such as a value object and its own field accessors, because the
interface and indirection cost buys nothing when the two pieces always
change together by definition. This is the connascence taxonomy's point that
connascence of name and type between tightly related elements in the same
module is cheap and appropriate, and manufacturing an interface around it
only adds a file to maintain.

Do not decouple a hot path where the profiler has shown the indirection cost,
a virtual dispatch, an interface boundary, a serialization step, is the
actual bottleneck, because low coupling is a maintainability property and
maintainability is not the force under pressure once a system is
demonstrably CPU-bound or latency-bound at that exact call site. Inlining or
directly coupling the hot path and documenting why is the correct trade.

Do not add a speculative interface, dependency-injected abstraction, or
plugin seam for a collaborator that has exactly one implementation and no
credible second implementation planned, because this is the classic
misapplication that the YAGNI heuristic and the anti-pattern literature call
speculative generality. The coupling you were avoiding gets replaced by an
abstraction that itself must be maintained, understood, and kept in sync,
for a flexibility nobody uses.

Do not decouple within a single team's single deployable when the two units
will always be built, tested, deployed, and versioned together, because
Conway's Law forces on team topology do not apply, and the interface adds a
seam with no organizational or deployment payoff.

Do not use event-based or asynchronous decoupling to hide a synchronous
business invariant, such as the order must not be marked paid until the
payment has actually cleared, because when two units must observe a strict
ordering or an atomic joint state, weakening the coupling that enforced that
invariant converts a compile-time or transaction-time guarantee into a
runtime race condition that must then be solved with compensating
transactions or sagas, trading a simple problem for a harder one it did not
need to have.

## 5. Structure

Low Coupling is a property of a relationship, not a class of object, so its
structure is best described as the participants in a coupled relationship
and the mechanism that mediates it.

The Dependent is the unit that needs a capability it does not implement
itself, a class calling a collaborator, a service calling another service, a
module importing another module.

The Dependency is the unit that supplies the capability. In a tightly coupled
design the Dependent references the Dependency's concrete type directly. In a
loosely coupled design the Dependent references an abstraction instead.

The Contract is the narrow surface the Dependent is allowed to see, an
interface, an abstract base class, a protocol, a wire format, an event
schema, or a function signature. The Contract is the object that actually
carries the coupling. Everything not exposed through the Contract is hidden
and therefore not a source of coupling at all.

The Mediator, present only in the more decoupled variants, is an
intermediary the Dependent talks to instead of the Dependency directly, a
dependency injection container that supplies a concrete instance behind the
Contract, an event bus or message broker that the Dependent publishes to
without knowing who, if anyone, subscribes, or a facade that exposes one
simplified Contract over several concrete Dependencies.

The Composition Root, where dependency injection is used, is the single
place, usually near the process entry point, where concrete Dependencies
are actually constructed and wired to the abstractions the rest of the
system depends on, so that the wiring knowledge is concentrated in one unit
rather than scattered across every Dependent.

## 6. ASCII structure diagram

```
TIGHT COUPLING (what Low Coupling replaces)

+-------------------------------+
| Dependent                     |
| (knows concrete type, fields, |
| constructor)                  |
+-------------------------------+
           | new / direct call
           v
+----------------------------+
| ConcreteDependency         |
| (fields, methods, internal |
| layout all visible)        |
+----------------------------+


LOOSE COUPLING (Low Coupling applied via a Contract)

+---------------------------------+
| Dependent                       |
| (knows only the Contract shape) |
+---------------------------------+
           | calls via Contract
           v
+---------------------------------------+
| Contract                              |
| (interface / protocol / event schema) |
+---------------------------------------+
           ^
           | implements
+-----------------------------------+
| ConcreteDependency                |
| (internals hidden from Dependent) |
+-----------------------------------+


LOOSE COUPLING WITH A MEDIATOR (event bus / DI container)

+----------------------------------+
| Dependent (unaware who fulfills) |
+----------------------------------+
           | publishes/requests
           v
+----------------------------------------+
| Mediator (bus / DI container / facade) |
+----------------------------------------+
           | notifies/supplies
           v
+------------------------------------+
| Dependency (unaware who triggered) |
+------------------------------------+
```

## 7. Dynamics

The runtime dynamics differ sharply between the tight and the loose forms,
and the difference is the entire practical payoff of the principle.

In the tight coupling case, at compile time or interpret time the Dependent's
source references the Dependency's concrete type by name. A build of the
Dependent therefore cannot succeed without the Dependency's concrete
definition present and unchanged in the shape the Dependent expects. At run
time, a call from Dependent to Dependency goes directly to the concrete
implementation with no intervening lookup.

In the loose coupling case mediated by a Contract, at compile time the
Dependent's source references only the Contract's shape. A build of the
Dependent succeeds against the Contract alone. The concrete Dependency can be
compiled, versioned, and even deployed separately, as long as it satisfies
the Contract. At run time, something, a constructor argument passed in by the
caller, a dependency-injection container resolving the Contract to a
registered concrete type, or a factory, supplies a concrete instance that
satisfies the Contract, and the Dependent invokes it through the Contract's
method signatures without knowing the concrete type at all. This is the
mechanism by which a test can substitute a fake or a mock. The substitute
satisfies the same Contract the production Dependency satisfies, and the
Dependent cannot tell the difference.

In the mediator case with an event bus, the dynamics change from a call-and-
return shape to a fire-and-forget or publish-and-subscribe shape. The
Dependent constructs an event describing what happened and hands it to the
Mediator, then continues without waiting for or knowing about any
Dependency's reaction. Zero, one, or many Dependencies may be subscribed to
that event type at run time, and that set can change, a new subscriber
added, an old one removed, without the Dependent's code changing at all,
because the Dependent was never coupled to the identity or count of its
consumers in the first place, only to the shape of the event it emits.

```
  SEQUENCE, tight coupling
  Dependent -> ConcreteDependency.method(args)
  ConcreteDependency -> Dependent -- result

  SEQUENCE, loose coupling via Contract, DI container resolves it
  CompositionRoot -> Container   -- register(Contract, ConcreteDependency)
  Dependent       -> Container   -- resolve(Contract)
  Container       -> Dependent   -- instance implementing Contract
  Dependent       -> instance    -- contractMethod(args)
  instance        -> Dependent   -- result

  SEQUENCE, loose coupling via event bus, zero or more subscribers
  Dependent -> EventBus -- publish(OrderPaidEvent)
  EventBus  -> SubA     -- notify(OrderPaidEvent)   [if subscribed]
  EventBus  -> SubB     -- notify(OrderPaidEvent)   [if subscribed]
  (Dependent never learns whether SubA or SubB exist or reacted)
```

## 8. Implementation variants

Interface-based decoupling is the most common variant in statically typed
object-oriented languages. Define an interface or abstract class, have the
Dependent hold a reference typed to the interface, and supply a concrete
implementation either by constructor injection, setter injection, or a
factory. Java, C#, Kotlin, and Swift protocols all use this shape directly.

Structural typing decoupling is the variant idiomatic to Go and TypeScript.
Because both languages use structural rather than nominal interface
satisfaction, a Dependency does not even need to declare that it implements a
Contract. It merely needs to have the right method or property shape, and the
Dependent's declared parameter type is the only place the Contract is
written down at all. This removes a step, no explicit implements declaration
required on the Dependency, but keeps the same run time and compile time
coupling reduction as the nominal-interface variant.

Functional decoupling replaces the interface with a plain function value.
Instead of injecting an object satisfying a multi-method interface, the
Dependent takes a function, a closure, a lambda, a first-class function
reference, as a parameter and calls it. This is idiomatic in JavaScript,
Python, and any language with first-class functions, and it is a strictly
narrower Contract than a full interface when only one method is actually
needed, which itself reduces coupling further because the Dependent cannot
accidentally depend on any method of the Dependency beyond the one function
signature.

Dependency injection container variants centralize the wiring of concrete
types to abstractions in a Composition Root, using either constructor
injection, the container passes dependencies into a constructor, the
preferred form because it makes required dependencies visible and makes
the object impossible to construct in a partially wired state, or
container-managed field or property injection, more convenient in some
frameworks, at the cost of making required dependencies invisible in the
type's own constructor signature.

Event-driven and message-based decoupling removes the compile-time
dependency entirely on one side. In a publish-subscribe system, an in-
process event bus, or a network message broker such as a Kafka topic or an
AMQP exchange, the publisher never references the subscriber's type or even
its existence at compile time, only the shape of the message it emits. This
is the strongest form of decoupling available and is the standard mechanism
at service and system boundaries in distributed architectures.

Facade-based decoupling wraps several concrete Dependencies behind one
simplified Contract, so that a Dependent that needs a coarse-grained
capability depends only on the Facade and never learns how many finer-
grained collaborators the Facade coordinates internally. This is a distinct
variant from a plain interface because it collapses the count, many
concrete dependencies become one Contract, rather than merely hiding one
concrete type behind one abstract type.

## 9. Known production uses

Kubernetes Custom Resource Definitions decouple the core API server from any
specific extension's implementation. A CRD lets an operator define a new
resource type and schema that the Kubernetes API serves and stores without
the core API server code needing to know anything about that resource's
semantics, so extension authors and the Kubernetes core team can evolve
independently. Kubernetes documentation, "Extend the Kubernetes API with
CustomResourceDefinitions", https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/, verified 2026-08-02.

Protocol Buffers, used as the interface definition mechanism for gRPC and
inside large parts of Google's internal service architecture, decouple a
service's callers from its implementation language and runtime by defining
the Contract once in a proto schema file and generating client and server
bindings for many languages from that single schema, so a caller in one
language never depends on the concrete implementation language, memory
layout, or runtime of the service it calls. Google, "Protocol Buffers
Overview", https://protobuf.dev/overview/, verified 2026-08-02.

The Java Servlet specification's filter chain is a long-standing production
example of Contract-mediated, event-flow decoupling inside a single process.
A web container invokes a chain of Filter implementations purely through the
javax.servlet.Filter, or in newer versions jakarta.servlet.Filter, interface,
so the container's dispatch code is coupled only to that interface and not to
any concrete filter, letting application authors add, remove, or reorder
authentication, logging, and compression filters without touching the
container's dispatch logic. Jakarta Servlet Specification, version 6.0,
section 6, "Filtering", Eclipse Foundation, 2022.

The observer pattern's central production instance, DOM event listeners in
every modern web browser, decouples the code that dispatches a user action, a
click, a keypress, from the arbitrarily many, arbitrarily authored listener
callbacks registered against it via addEventListener. The browser event
dispatch code has no compile-time or load-time knowledge of which listeners
exist, only the DOM Contract that a listener is a callable receiving an
Event object. WHATWG, "DOM Standard", section 2.7, "Interface EventTarget",
https://dom.spec.whatwg.org/#interface-eventtarget, verified 2026-08-02.

## 10. Consequences

Low Coupling brings a set of real, achievable benefits, and it brings a set
of costs that a thorough treatment must state with equal weight.

Positive consequences. A change localized to one unit's internals is far
less likely to force edits in unrelated units, because the units on the far
side of a Contract never observed those internals in the first place. A unit
behind a narrow Contract is straightforwardly substitutable for a test
double, which is why loosely coupled code is dramatically easier to unit
test in isolation. Two teams can own units on either side of a Contract and
release independently, as long as neither side breaks the Contract, which is
the direct payoff for team topology forces. A system decoupled through
Contracts tends to have a smaller blast radius per change, meaning
regressions from one change are, by construction, less likely to reach into
distant, unrelated parts of the codebase. And a loosely coupled architecture
is more amenable to incremental replacement, since a Dependency behind a
Contract can be swapped for a rewritten or vendor-replaced implementation
without the Dependent's code changing.

Negative consequences. Every Contract, interface, or mediator introduced is
an additional artifact that must be read, understood, kept synchronized with
its implementations, and versioned. A codebase that has decoupled
aggressively can require a reader to jump through several files or several
layers of indirection to answer the simple question "what code actually runs
here", which is the classic complaint about over-abstracted enterprise
codebases. Loose coupling through asynchronous messaging or an event bus
converts previously atomic, ordered operations into operations whose
ordering and delivery guarantees must now be reasoned about explicitly,
introducing a class of bug, out-of-order delivery, duplicate delivery, lost
messages, that simply did not exist in the tightly coupled, synchronous
version. Debugging a loosely coupled system, especially one decoupled across
process or network boundaries, is harder, because a stack trace stops at the
Contract boundary and the actual failure may be in a process the debugger
has no visibility into. And speculative decoupling, applied to a Dependency
that in practice never needed substituting, is pure cost. The abstraction
earns nothing and still must be maintained forever.

## 11. Failure modes and misuse

Interface explosion is the most common misuse pattern. The observable
symptom is that nearly every class in the codebase has a matching IFoo
interface with exactly one implementation, and finding what actually
happens when this method runs requires two jumps in the IDE instead of one,
every time, for every class. The cause is applying dependency inversion
mechanically to every dependency rather than to the dependencies that
genuinely need substitutability, for testing, for multiple implementations,
or for a real deployment boundary. The fix is to remove the interface for
any Dependency with exactly one production implementation and no test
double need, and keep interfaces only where a second implementation
genuinely exists or is imminent, per the applicability guidance in
dimension 4.

The distributed monolith is the most damaging misuse pattern at the service
level. The symptom is that services are physically decoupled, separate
deployables, separate repositories, a network call between them, but
logically still tightly coupled, because a deploy of service A always
requires a coordinated, same-day deploy of service B, or because service
A's database schema is directly queried by service B, bypassing any API
Contract at all. The cause is that teams decouple the deployment topology,
splitting a monolith into services, without first decoupling the logical
model, so the physical boundary adds network latency and operational
complexity without buying any of the independent-deployability benefit that
was the entire point. The fix is to check for hidden logical coupling,
shared database tables, synchronous call chains that must all succeed
together, shared deployment timing, before or during a service split, and
either eliminate it through an event-driven Contract or a proper data
ownership boundary, or accept that the services are not actually decoupled
and stop paying the network cost for nothing.

Leaky abstraction is a failure mode where the Contract nominally hides the
Dependency's internals but the Dependent's callers have, in practice, come
to depend on a specific concrete implementation's behavior anyway, its
exact timing, its exact error type, its exact ordering of results. The
symptom is that swapping the concrete Dependency for a different
implementation that satisfies the same formal Contract breaks callers
anyway, meaning the decoupling was cosmetic. The cause is that the Contract
was written to match one concrete implementation's signature rather than to
specify the actual behavioral guarantees callers may rely on. The fix is to
write the Contract's documentation to state explicit behavioral guarantees,
ordering, error semantics, idempotency, latency bounds where relevant, and
add a second, deliberately different implementation as a conformance test
early, so that implementation-specific assumptions become visible and are
removed before they calcify.

Chatty decoupled boundaries occur when a boundary correctly decoupled at the
type level is called too many times per logical operation, because the
Contract was designed around the internal shape of the old, tightly coupled
code rather than around the coarse-grained needs of the caller. The symptom
is that what used to be one in-process method call becomes twenty round
trips across a decoupled network boundary for the equivalent operation, and
the operation that used to take microseconds now takes hundreds of
milliseconds. The cause is that decoupling was applied mechanically to every
existing fine-grained method without redesigning the Contract's granularity
for its new cost profile. The fix is to redesign the Contract around
coarse-grained, batch-oriented operations at any boundary that crosses a
process or network, which is the same lesson that motivated the Facade
pattern and the remote-object anti-pattern literature on fine-grained remote
interfaces.

## 12. Trade-off matrix

The alternatives compared here are named, concrete design choices, not a
generic naive approach. Comparison is across the forces named in dimension 3.

| Approach | Change isolation | Testability | Runtime cost | Cognitive load to trace one call | When it wins |
|---|---|---|---|---|---|
| Tight coupling, direct concrete reference | Low, a change to the Dependency's shape forces every Dependent to change | Low, hard to substitute a test double without a mocking framework that bypasses the type system | Lowest, a direct call, no indirection | Low, one jump from call site to implementation | Two units genuinely always change together, same team, same deployable, hot path |
| Interface-based decoupling, constructor injection | High, Dependents depend on the Contract, not the concrete shape | High, any conforming test double substitutes cleanly | Small, one virtual dispatch | Medium, one extra jump through the interface to find the implementation | Multiple implementations exist or are likely, or unit tests need isolation |
| Event bus, publish-subscribe | Highest for the publisher, it never references any subscriber | High for the publisher's own logic, subscriber-side effects need separate integration tests | Higher, message construction, dispatch, and possibly network or queue latency | High, tracing the full flow requires finding all subscribers, which the code does not name | Zero, one, or many independent reactions to one fact, across team or process boundaries |
| Facade over several concrete dependencies | Medium, the Facade's own Contract still shields Dependents from the coordinated internals changing | Medium, test the Facade's Contract, but its internal coordination logic still needs its own tests | Small, one extra call layer, coordinating calls that would happen anyway | Medium, the Facade concentrates complexity in one readable place instead of scattering it | Several fine-grained collaborators are always used together and their coordination is itself a distinct concern worth naming |
| Dependency Inversion via abstract base class with template methods | High for the varying steps, low for the fixed algorithm shape, which is intentionally shared | High for the varying steps in isolation | Lowest to small, usually no more than an interface | Medium, requires understanding the base class's fixed algorithm plus the override points | The overall algorithm shape is stable and shared, but specific steps vary by implementation, and reuse of the fixed shape is itself valuable |

## 13. Related and incompatible patterns

High Cohesion is the constant companion of Low Coupling in the GRASP
literature and in structured design before it. The two principles are
usually pursued together because a poorly cohesive module, one that mixes
unrelated responsibilities, is very often also a highly coupled one, since
each of its unrelated responsibilities drags in its own set of unrelated
collaborators. In the other direction, sharpening a module's cohesion around one clear
purpose naturally reduces the number of things it needs to depend on.

The Dependency Inversion Principle is the specific mechanism by which
object-oriented Low Coupling is usually achieved between a high-level policy
module and a low-level implementation detail module. Rather than the
high-level module depending directly on the low-level module, both depend on
an abstraction owned by the high-level module, which is precisely the
interface-based decoupling variant described in dimension 8.

The Interface Segregation Principle refines Low Coupling one step further by
insisting that the Contract itself be narrow. A fat interface that bundles
many unrelated methods still creates coupling to methods a given Dependent
never calls, so Interface Segregation is the guidance for keeping the
Contract from dimension 5 as small as the actual relationship requires.

The Facade pattern is a direct implementation vehicle for Low Coupling at
the boundary between a subsystem and its callers, collapsing many concrete
Dependencies behind one Contract, as covered as a distinct variant in
dimension 8.

The Observer pattern, and its production-scale generalization,
publish-subscribe messaging, is the implementation vehicle for the
event-driven decoupling variant, and it composes naturally with Low
Coupling because a Subject in the Observer pattern is, by construction,
coupled only to the abstract Observer Contract and not to any concrete
observer.

Dependency Injection, as a mechanism rather than a design principle, is the
runtime wiring technique that makes interface-based Low Coupling practical
across a large codebase. Without some form of injection, manual, container-managed, or
service-locator-based, the latter itself contested, every Dependent would
need to construct its own concrete Dependencies, which reintroduces the
tight coupling the interface was meant to remove.

Low Coupling has no pattern it flatly conflicts with in the sense the
schema's incompatible_with field is meant to capture, but it is in direct
tension, as a force rather than an incompatibility, with any pattern whose
entire value proposition is a single, tightly integrated, shared-state
implementation optimized for one concrete use, such as a purpose-built
in-memory cache tuned to one specific caller's access pattern. Applying Low
Coupling there by generalizing the cache behind a broad Contract for
hypothetical future callers is very often the speculative-generality misuse
named in dimension 11, not a genuine application of the principle.

## 14. Refactoring path in and out

Introducing Low Coupling into code that lacks it follows a repeatable
sequence. First, identify the concrete type a Dependent references directly
and ask what behavior the Dependent actually uses from it, not what the
whole type happens to expose. This scoping step is what keeps the resulting
Contract narrow rather than a mechanical copy of the concrete type's full
public surface. Second, extract an interface, or, in a language that uses
structural typing, simply write the Dependent's parameter type as the minimal
structural shape it needs, containing only that used behavior. This step
corresponds to the Extract Interface refactoring in the refactoring
literature. Third, change the Dependent's field or parameter type from the
concrete type to the new Contract type, and change every call site that
constructs the concrete Dependency directly into either a constructor
parameter passed in from a caller, manual dependency injection, sometimes
called Introduce Parameter or Extract Constructor Parameter, or a
resolution through a dependency injection container if the codebase already
uses one. Fourth, once the Dependent compiles and its existing tests pass
against the concrete implementation supplied through the new Contract, write
a test double satisfying the Contract and add at least one test that
exercises the Dependent with the double, which is the concrete proof that
the decoupling actually achieved its purpose rather than merely adding a
layer. Fifth, if the goal is a Composition Root pattern, move all
construction of concrete Dependencies for a given module up to one place
near the process entry point, rather than leaving construction scattered
through the codebase at every point a Contract is used.

Removing Low Coupling, when it has stopped earning its place, is the
inverse and is equally deliberate rather than accidental. First, confirm
there is exactly one production implementation of the Contract and no
credible plan for a second, and confirm the only reason the interface
exists is that it once seemed prudent, not that it is used for testing, if
it is still used for testing, keep it, the test-substitution benefit alone
can justify the Contract even with one production implementation. Second,
inline the interface by changing the Dependent's parameter or field type
back to the concrete implementation's type directly. Third, delete the
interface declaration and any dependency-injection registration entry that
existed solely to wire that one implementation to that one Contract. Fourth,
re-run the full test suite for the affected module, since removing a Contract
can occasionally reveal a place where the abstraction was hiding an
accidental extra dependency on the concrete type's internals that the
interface had been correctly preventing. If that happens, it is evidence
the coupling reduction should be kept, not removed.

## 15. Testing and verification

Testing code that has been decoupled through a Contract is easier in the
specific, mechanical sense that the test can construct a stand-in
implementation of the Contract, a hand-written fake, or a mock generated by
a mocking framework such as Mockito for Java, unittest.mock for Python, or
Jest's jest.mock for TypeScript, and inject it into the Dependent under
test, entirely bypassing whatever expensive or nondeterministic behavior the
real Dependency has, a network call, a database write, a slow computation.
This is the single most direct, practically observable payoff of Low
Coupling and is frequently the actual reason a team introduces an interface,
even when the production code has and will only ever have one
implementation.

What becomes harder is verifying that the Contract's fake or mock
implementation used in tests actually mirrors the real Dependency's
behavior. This is the contract testing problem. A test suite that only ever
exercises the Dependent against a hand-written fake can pass every test
while the real Dependency has drifted to violate an assumption the fake
encodes incorrectly, which is exactly the leaky-abstraction failure mode
from dimension 11 manifesting as a false-positive test suite. The standard
technique to close this gap is a shared conformance test suite, sometimes
called contract tests, that is run against every implementation of the
Contract, both the real one and the test doubles, so that a mismatch
between them is caught by the test suite itself rather than discovered in
production.

For event-driven and message-based decoupling, testing the publisher in
isolation is straightforward, assert the correct event was published with
the correct payload, but testing the full behavior across the
decoupled boundary requires either an integration test setup that runs a
real or embedded broker, or an explicit test double for the broker itself
that faithfully replays delivery, ordering, and, if the real broker
provides at-least-once delivery, duplicate-delivery semantics, since a test
double that silently guarantees exactly-once, perfectly-ordered delivery
when the production broker does not will hide bugs that only appear under
real message-delivery conditions.

## 16. Observability signals

A healthy, low-coupled system shows a specific, observable pattern in
change history. File-level co-change frequency, how often two files are
modified in the same commit, a metric extractable from git history with
tools such as git log fed into a co-change analysis, is low between units
that are supposed to be decoupled, and high only within a single cohesive
unit. A rising co-change frequency between two units that are formally
decoupled through a Contract is the earliest, cheapest sign that the
decoupling has become cosmetic, the leaky abstraction failure mode, even
before a developer consciously notices it.

At the architecture level, a dependency graph extracted from the build
system or from static analysis, import graphs, module dependency graphs,
should show a low fan-in and fan-out ratio anomaly count. A healthy
low-coupled module has a bounded, small number of things it depends on,
fan-out, and, separately, a number of things that depend on it, fan-in,
that is proportional to how stable and general-purpose that module's
Contract is meant to be. A module with unexpectedly high fan-out relative
to its stated purpose is a warning sign of accumulated tight coupling worth
investigating.

At the service level in a distributed system, the most direct observable
indicator for coupling health is correlated deploy frequency and correlated
incident timing. If service A's deploys reliably require a same-day deploy
of service B to avoid an incident, that is the distributed monolith failure
mode from dimension 11 showing up directly in deployment and incident
telemetry, and it is measurable from a deployment log and an incident
tracker without any code-level analysis at all. For message-based
boundaries specifically, queue depth, consumer lag, and dead-letter queue
volume are the indicators that show whether the decoupling is holding up
under real load. A growing dead-letter queue is the runtime evidence that
the Contract between publisher and subscriber has drifted or that a
subscriber cannot keep pace, either of which is the loose-coupling
equivalent of a compile error that a tightly coupled system would have
caught earlier, at build time instead of at run time.

## 17. Security and privacy implications

Low Coupling has a mostly positive security implication through the
principle of least privilege applied to the structure of a call. A Dependent that depends
only on a narrow Contract cannot reach into the Dependency's internal state
even accidentally, which limits the blast radius of a bug or a compromised
Dependent to what the Contract exposes, rather than to the Dependency's
full internal surface. This is directly comparable to, and often
implemented through the same mechanism as, capability-based security,
where a component can only exercise the specific operations it was
explicitly handed a reference to.

The negative security implication is at the boundary itself. Every Contract
that crosses a trust boundary, a process boundary, a network boundary, a
tenant boundary in a multi-tenant system, is an attack surface that did not
exist when the two units were compiled into one tightly coupled unit inside
one trust domain, and the Contract's serialization format, an event schema,
a wire protocol, is a concrete place where deserialization vulnerabilities,
schema confusion attacks, or injection through a loosely typed message
payload can be introduced. The well-known Java and .NET deserialization
vulnerability classes are specific, real-world instances of this general
risk, arising precisely at decoupled boundaries where one side deserializes
data supplied by the other.

On privacy, decoupling through an event bus or a shared message format has
a specific implication worth stating plainly. Because a publisher in a
publish-subscribe system does not know who, if anyone, is subscribed, it is
easy for a message to be over-broadcast, containing more personal data than
any actual subscriber needs, simply because the publisher, decoupled from
its consumers, has no visibility into what each subscriber's minimal data
need actually is. The mitigation is deliberate schema minimization at
design time, publish the minimum necessary fields per event type, combined
with access controls at the message broker level, since the decoupling
itself removes the natural, implicit access control that a direct,
coupled, in-process call would have provided by construction.

## 18. References

1. Stevens, Wayne P., Myers, Glenford J., Constantine, Larry L. "Structured
   Design". IBM Systems Journal, volume 13, issue 2, pages 115 to 139, June
   1974.
2. Parnas, David L. "On the Criteria To Be Used in Decomposing Systems into
   Modules". Communications of the ACM, volume 15, issue 12, pages 1053 to
   1058, December 1972. DOI 10.1145/361598.361623.
   https://dl.acm.org/doi/10.1145/361598.361623, verified 2026-08-02. The
   page returns HTTP 403 to automated fetch behind the ACM paywall. The DOI
   resolves and the citation metadata is independently checkable through it.
3. Larman, Craig. "Applying UML and Patterns, An Introduction to
   Object-Oriented Analysis and Design and Iterative Development", third
   edition, Prentice Hall, 2004, chapter 17, "GRASP, Designing Objects with
   Responsibilities".
4. Connascence.io. "Connascence". https://connascence.io/, verified
   2026-08-02.
5. Fowler, Martin. "Reduce Coupling". IEEE Software.
   https://martinfowler.com/ieeeSoftware/coupling.pdf, verified 2026-08-02.
   The PDF resource resolves and downloads, confirming the publication.
6. Kubernetes documentation. "Extend the Kubernetes API with
   CustomResourceDefinitions".
   https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/,
   verified 2026-08-02.
7. Google. "Protocol Buffers Overview". https://protobuf.dev/overview/,
   verified 2026-08-02.
8. Eclipse Foundation. "Jakarta Servlet Specification", version 6.0, section
   6, "Filtering", 2022.
9. WHATWG. "DOM Standard", section 2.7, "Interface EventTarget".
   https://dom.spec.whatwg.org/#interface-eventtarget, verified 2026-08-02.
10. Wikipedia contributors. "Coupling (computer programming)".
    https://en.wikipedia.org/wiki/Coupling_(computer_programming), verified
    2026-08-02, used only to cross-check the Stevens, Myers, Constantine
    attribution above, not as a primary source for any claim in this entry.

## Code examples

The examples below show the same relationship, a NotificationService that
must send a message through some channel, first tightly coupled to a
concrete EmailSender, then loosely coupled through a Notifier Contract that
a test double can satisfy. All three were run or compiled locally.

### TypeScript

```typescript
class EmailSender {
  send(to: string, body: string): void {
    console.log(`EMAIL to ${to}: ${body}`);
  }
}

class TightNotificationService {
  private sender = new EmailSender();
  notify(to: string, body: string): void {
    this.sender.send(to, body);
  }
}

interface Notifier {
  send(to: string, body: string): void;
}

class EmailNotifier implements Notifier {
  send(to: string, body: string): void {
    console.log(`EMAIL to ${to}: ${body}`);
  }
}

class LooseNotificationService {
  constructor(private notifier: Notifier) {}
  notify(to: string, body: string): void {
    this.notifier.send(to, body);
  }
}

class RecordingNotifier implements Notifier {
  sent: { to: string; body: string }[] = [];
  send(to: string, body: string): void {
    this.sent.push({ to, body });
  }
}

const tight = new TightNotificationService();
tight.notify("a@example.com", "hello");

const fake = new RecordingNotifier();
const loose = new LooseNotificationService(fake);
loose.notify("b@example.com", "hi");
console.log("recorded", JSON.stringify(fake.sent));
```

Compiled and run with the TypeScript compiler in strict mode targeting
es2020, output through commonjs, then executed with node. Output confirmed
the tight path prints directly and the loose path routes through the
injected RecordingNotifier, recording the injected call without ever
touching the console.

### Python

```python
from typing import Protocol


class Notifier(Protocol):
    def send(self, to: str, body: str) -> None: ...


class EmailNotifier:
    def send(self, to: str, body: str) -> None:
        print(f"EMAIL to {to}, {body}")


class NotificationService:
    def __init__(self, notifier: Notifier) -> None:
        self._notifier = notifier

    def notify(self, to: str, body: str) -> None:
        self._notifier.send(to, body)


class RecordingNotifier:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(self, to: str, body: str) -> None:
        self.sent.append((to, body))


if __name__ == "__main__":
    NotificationService(EmailNotifier()).notify("a@example.com", "hello")

    fake = RecordingNotifier()
    NotificationService(fake).notify("b@example.com", "hi")
    assert fake.sent == [("b@example.com", "hi")]
    print("recorded", fake.sent)
```

Run directly with the python3 interpreter. Notifier is a structural
Protocol, so EmailNotifier and RecordingNotifier never declare that they
implement it, matching the structural-typing variant from dimension 8.
Output confirmed both paths executed and the assertion held.

### Go

```go
package main

import "fmt"

type Notifier interface {
	Send(to, body string)
}

type EmailNotifier struct{}

func (EmailNotifier) Send(to, body string) {
	fmt.Printf("EMAIL to %s, %s\n", to, body)
}

type NotificationService struct {
	notifier Notifier
}

func NewNotificationService(n Notifier) *NotificationService {
	return &NotificationService{notifier: n}
}

func (s *NotificationService) Notify(to, body string) {
	s.notifier.Send(to, body)
}

type RecordingNotifier struct {
	Sent []string
}

func (r *RecordingNotifier) Send(to, body string) {
	r.Sent = append(r.Sent, to+" "+body)
}

func main() {
	NewNotificationService(EmailNotifier{}).Notify("a@example.com", "hello")

	fake := &RecordingNotifier{}
	NewNotificationService(fake).Notify("b@example.com", "hi")
	fmt.Println("recorded", fake.Sent)
}
```

Run with the go toolchain directly. EmailNotifier and RecordingNotifier
both satisfy Notifier through structural typing alone, with no implements declaration,
consistent with Go's interface satisfaction model. Output confirmed the
recorded slice held the injected call.

Java and Rust are omitted from this entry's runnable set only because their
toolchains were reported as being installed rather than confirmed present at
authoring time, and neither variant was compiled here, and that limitation
is stated rather than implied. The pattern translates directly to Java
through a plain interface plus constructor injection, and to Rust through a
trait plus a boxed trait object or a generic type parameter bound by the
trait.
