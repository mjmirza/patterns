---
name: State
slug: state
family: 01-design-patterns-gof
category: Behavioral
aliases: [Objects for States, State Object, Statechart Pattern]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [strategy, flyweight, singleton, command, observer, memento, bridge]
incompatible_with: []
verified: 2026-08-02
---

# State

## 1. Name, aliases, and lineage

The canonical name is State. It appears in the Gang of Four catalog as one of the
eleven behavioral patterns, described in Erich Gamma, Richard Helm, Ralph Johnson
and John Vlissides, *Design Patterns. Elements of Reusable Object-Oriented
Software*, Addison-Wesley, 1994, chapter 5, Behavioral Patterns, section State.
The intent is that an object alters its behavior when its internal state changes,
so that the object appears to change its class
([Wikipedia summary of the GoF intent](https://en.wikipedia.org/wiki/State_pattern),
verified 2026-08-02). The same summary records the two problems the pattern
addresses. An object should change behavior when internal state changes, and
state-specific behavior should be defined independently so that adding a new
state does not disturb existing ones.

**Objects for States** is the alias the GoF book itself records, and it is the
more descriptive of the two names because it says exactly what the pattern does.
It replaces a state variable plus conditionals with one object per state. **State
Object** appears in framework documentation for the same idea. **Statechart
Pattern** is used loosely in the embedded and modelling communities for the
hierarchical form, which is a different thing and is discussed below.

Three distinct ideas travel under the word state, and conflating them produces
most of the bad code in this area.

- **The State pattern (GoF, object-per-state).** Each state of the subject is a
  separate type. The subject, called the Context, holds a reference to the
  current state object and forwards every state-dependent request to it. The
  conditional that used to switch on a state code is deleted and replaced by
  dynamic dispatch. The set of states is closed at compile time, and a state is
  a *type*.
- **A finite state machine.** A mathematical object, a tuple of states, an input
  alphabet, a transition function, an initial state and a set of accepting
  states. The State pattern is one possible *implementation strategy* for a
  finite state machine, and it is by no means the only one, nor usually the best
  one when the machine is large. A transition table is the other common
  implementation and it is often superior, see dimension 8 and dimension 12.
- **A statechart.** David Harel's extension of state diagrams with hierarchy,
  concurrency and broadcast communication, published as "Statecharts. A visual
  formalism for complex systems", *Science of Computer Programming*, volume 8,
  1987, pages 231 to 274
  ([ScienceDirect record](https://www.sciencedirect.com/science/article/pii/0167642387900359),
  verified 2026-08-02). A statechart is a strictly more expressive notation than
  a flat finite state machine, and the State pattern does not give you hierarchy
  or orthogonal regions without extra machinery. The W3C standardised an XML
  serialisation of the same ideas as SCXML, whose abstract states that it
  "provides a generic state-machine based execution environment based on CCXML
  and Harel State Tables", published as a W3C Recommendation on 1 September 2015
  ([W3C SCXML](https://www.w3.org/TR/scxml/), verified 2026-08-02).

A test that separates the first from the other two. If deleting the polymorphism
and writing a table of transitions loses nothing the design relied on, then what
you had was a finite state machine and the pattern was one encoding of it. If the
state objects carry behavior richer than a transition, hold state-local data, and
are extended by code outside the module that owns the Context, then the pattern
is doing work a table cannot do.

## 2. Problem and context

An object behaves differently depending on a mode it is in, and every method that
depends on that mode has grown the same conditional.

The situation reads like this in a codebase. There is a class with a field named
`status`, `mode`, `phase` or `state`, typed as an enum, an integer or a string.
Five or six public methods each open with a switch or an if-else ladder over that
field. Each branch does the mode-specific work and then, near the end, assigns a
new value to the field. The ladders are not identical, because some modes do not
handle some methods, so each ladder has a slightly different set of cases and a
slightly different default. A new mode arrives and the change is to edit every
one of those ladders, and the compiler helps with none of it because a missing
case in a switch over a string or an integer is legal.

The characteristic pain is not that the code is ugly. It is that the *rules* of
the machine, which state can follow which, are not written down anywhere. They
are smeared across the assignment statements at the bottom of each branch. Nobody
can answer "can an order go from refunded back to shipped" by reading a single
place, and the answer in production turns out to be yes because one branch on one
path forgot a guard.

A document editor is the textbook illustration and a connection is the honest
one. TCP is the canonical real example, and it is exactly the example the GoF
book uses. A TCP endpoint responds to the same request, send a segment, in
completely different ways depending on whether it is in LISTEN, SYN-SENT,
ESTABLISHED or TIME-WAIT. RFC 9293, *Transmission Control Protocol*, August 2022,
names eleven connection states and draws the transitions in section 3.3.2,
figure 5 ([RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html), verified
2026-08-02). Writing that endpoint as one class with eleven-way switches in every
method is how the code looks before the pattern.

The context that makes State the right answer has four parts.

- The number of modes is small, closed, and known to the module that owns the
  Context. Small means roughly under a dozen, see dimension 11 on explosion.
- Several methods, not one, branch on the same mode field. One method branching
  on a mode is a conditional, not a design problem.
- The behavior difference between modes is real behavior, not a data difference.
  If the only difference is which string gets returned, a lookup table is
  cheaper and clearer.
- Transitions between modes carry rules that matter, and those rules are worth
  making explicit and testable.

Outside that context the pattern imposes indirection and object count for
nothing, see dimension 4.

## 3. Forces

This dimension is engineering judgement about which pressure dominates, not a
sourced claim. It is written as reasoning so a reader can disagree with the
weighting.

- **Cognitive load, local.** Favoured strongly. Reading what the system does in
  one state means reading one class. Every branch that used to be spread across
  six methods is now co-located by state rather than by operation. This is the
  single largest payoff and it is why the pattern survives.
- **Cognitive load, global.** Sacrificed. Reading what one *operation* does
  across all states now means opening every state class. The pattern rotates the
  code ninety degrees, and whether that helps depends entirely on whether the
  reader's question is state-shaped or operation-shaped. Teams that debug by
  asking "what happens when I call cancel" are worse off than before.
- **Coupling between states.** Sacrificed when the state objects own transitions.
  A state that returns its successor names that successor, so the states form a
  graph of compile-time dependencies. The Rust book states this plainly as a
  downside of the pattern, that "because the states implement the transitions
  between states, some of the states are coupled to each other"
  ([The Rust Programming Language, chapter 18](https://doc.rust-lang.org/book/ch18-03-oo-design-patterns.html),
  verified 2026-08-02).
- **Correctness of the transition graph.** Favoured when transitions are declared
  in one place, sacrificed when they are scattered across state classes. This is
  the tension that dimension 8 resolves and there is no free answer.
- **Extensibility.** Favoured for adding a state, sacrificed for adding an
  operation. Adding a state is one new class. Adding an operation is an edit to
  every state class, and the compiler will only help if the state interface is
  exhaustive and the language rejects incomplete implementations. This is the
  same axis Bridge and Visitor sit on, and it is the reason the pattern suits
  domains where the operation set is stable.
- **Object count and allocation.** Sacrificed mildly. One class per state, plus
  either one instance per state shared across all contexts or one instance per
  context. Sharing is usually correct, see the Flyweight relationship in
  dimension 13.
- **Latency.** Close to neutral. One virtual call replaces one branch. On a
  modern out-of-order processor a well-predicted branch and a monomorphic virtual
  call are both close to free, and a megamorphic call site with eight state
  classes will miss the inline cache more often than the branch predictor missed
  the switch. If the machine steps millions of times per second, measure rather
  than assume.
- **Operability.** Sacrificed unless deliberately repaired. The current state is
  a pointer to an object, not a value in a field, so it does not appear in a log
  line, a metric label or a database column without extra work. Every state class
  needs a stable name, see dimension 16.
- **Persistence and serialisation.** Sacrificed sharply. A pointer to a
  polymorphic object does not round-trip through a database column, a JSON
  payload or a message queue. This is a real cost and it is treated in its own
  right below and in dimension 11.
- **Consistency.** Favoured. Illegal transitions become impossible to express
  rather than merely discouraged, because a state class that does not implement a
  transition simply has no code path to the forbidden successor.
- **Team topology.** Neutral to mildly favoured. The pattern draws a seam per
  state, which suits a team that owns one lifecycle phase. It draws no seam per
  operation, which does not suit a team that owns one cross-cutting concern.
- **Cost of change.** Favoured for the graph, sacrificed for the interface. The
  transition graph becomes cheap to reason about and change. The state interface
  becomes expensive to change once there are many states.

A pattern that gave up nothing would be a language feature. State pays in object
count, in operation-axis rigidity, and above all in the awkwardness of getting
the current state out of the object graph and into a durable store.

## 4. Applicability and non-applicability

Reach for State when the following hold.

- An object's behavior depends on a mode, and several operations branch on that
  mode with substantially different bodies per branch.
- The set of modes is closed, small, and owned by one module.
- The transition rules matter and are worth making explicit, testable and hard to
  violate.
- State-local data exists. A state that carries fields nothing else needs, a
  retry counter that only means something while retrying, a half-parsed buffer
  that only exists mid-frame, is the strongest signal, because a state object
  gives that data a natural home and a natural lifetime.
- Entry and exit actions exist. Work that must happen exactly when the machine
  enters or leaves a mode has an obvious place to live.
- The operation set is stable. Adding operations is the expensive direction.
- New states are contributed by code the Context's author does not own, for
  example a protocol library that lets an application add a negotiation phase.

Do NOT reach for State in these cases. This non-applicability list is the more
useful of the two, and the reason attached to each item matters more than the
rule.

- **There is one conditional, in one method.** The pattern replaces N branches in
  M methods. With M equal to one, it replaces a readable switch with a class
  hierarchy and a level of indirection. Keep the switch.
- **The modes differ only in data, not in behavior.** If every branch does the
  same thing with a different constant, the honest shape is a lookup table keyed
  by the mode, or an enum carrying associated values. Turning a data table into a
  class hierarchy is the classic over-application.
- **The state must persist across a process restart, and the design is
  object-per-state.** This is treated at length below because it is the failure
  that surprises people. A `Box<dyn State>`, a `State` interface reference or a
  Python instance does not serialise. Every persistence boundary has to translate
  the object back to a discriminator and back again, which reintroduces the exact
  table the pattern deleted, in a second and less visible place.
- **The state count is large or combinatorial.** Beyond roughly a dozen states,
  or as soon as the state is a product of independent flags, the class count
  grows faster than comprehension. The statecharts community documents this as
  the primary blocker to state machine adoption, noting that "adding a new aspect
  to the state machine multiplies the number of states that need to be modeled,
  and creates a disproportionately high number of transitions", with a worked
  example going from two states to four to eight and twelve transitions
  ([statecharts.dev on state explosion](https://statecharts.dev/state-machine-state-explosion.html),
  verified 2026-08-02). Use hierarchy or orthogonal regions, which means a
  statechart engine, not the flat pattern.
- **The transition graph is configuration, not code.** If a workflow is authored
  by a non-programmer, changed without a deploy, or read from a database, then
  the transitions are data and the machine must be table-driven. AWS Step
  Functions is the industrial version of this position. States are declared in
  JSON with a `Type` field and a `Next` field naming the successor, and the whole
  machine is a document rather than a class hierarchy
  ([AWS Step Functions workflow states](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-states.html),
  verified 2026-08-02).
- **The operation set changes more often than the state set.** Each new operation
  is an edit to every state class. If the states are stable and the operations
  churn, the pattern points the extensibility axis the wrong way. Consider a
  transition table plus free functions.
- **The language gives you a better tool.** In Rust, encoding states as distinct
  types moves the whole check to compile time. The Rust book takes this position
  explicitly, arguing that with types "invalid states are now impossible because
  of the type system and the type checking that happens at compile time"
  ([The Rust Programming Language, chapter 18](https://doc.rust-lang.org/book/ch18-03-oo-design-patterns.html),
  verified 2026-08-02). In Erlang, `gen_statem` already supplies the machine. In
  Scala or Kotlin, an exhaustive `when` or `match` over a sealed hierarchy gives
  compile-time totality that the pattern does not.
- **You need history, orthogonal regions, deferred events or hierarchical
  states.** These are statechart features. Building them on top of the flat
  pattern by hand produces a small, undocumented, untested state machine engine
  inside the application. Use an engine that already has them, see dimension 9.
- **The Context is a value object or is shared across threads without
  synchronisation.** Swapping the state reference is a mutation, and an unguarded
  mutation of the state pointer under concurrency produces the torn-transition
  failure in dimension 11.

## 5. Structure

Three participants, named by the role each plays.

- **Context.** The object whose behavior varies. It holds a reference to the
  current State, exposes the public interface clients call, and forwards each
  state-dependent request to the current state object. It also owns whatever data
  is common to all states, and it exposes whichever of that data the states need
  to do their work. The Context is the only participant clients see, which is the
  property that makes the pattern substitutable for a plain conditional
  implementation without touching callers.
- **State.** The interface or abstract type declaring one method per
  state-dependent request. It is the contract every mode implements. Its width is
  the pattern's main design decision, because every method added here is an edit
  to every concrete state.
- **ConcreteState.** One per mode. It implements the state-dependent behavior for
  that mode, and it holds data that is relevant only while the machine is in that
  mode. Where the states own transitions, a ConcreteState also decides which
  state comes next and either returns it or asks the Context to install it.

Relationships. Context holds an association to State, never to a ConcreteState,
which is what keeps callers ignorant of the mode. Each ConcreteState implements
State. The Context passes itself to the state on each call when the state needs
access to shared data, which creates a bidirectional relationship that has to be
handled with care under reference counting, see dimension 11.

There is a fourth participant present in every real implementation and absent
from most diagrams. The **initial state selector**, the code that decides which
ConcreteState a freshly constructed or freshly loaded Context begins in. In the
constructor case it is a literal. In the rehydration case it is a table from a
persisted discriminator to a state object, and that table is the persistence seam
discussed below.

State objects come in two lifetimes and the choice matters.

- **Stateless and shared.** The ConcreteState holds no per-Context data, so one
  instance serves every Context in the process. This is the Flyweight
  relationship the GoF book records, and it makes states natural singletons. It
  also means every state method must receive the Context as a parameter, because
  the state has no other way to reach the data.
- **Stateful and per-Context.** The ConcreteState holds data specific to this
  Context's stay in this mode. It cannot be shared, it is allocated on entry and
  discarded on exit, and its lifetime is a natural scope for mode-local
  resources. This variant is what makes the pattern worth more than a table.

## 6. ASCII structure diagram

```
   +---------------------------------+
   |            Context              |
   |---------------------------------|        +------------------------+
   | - state: State                  |------->|        State           |
   | - sharedData                    |  has-a |------------------------|
   |---------------------------------|        | + handleA(ctx): State  |
   | + requestA()  -> state.handleA()|        | + handleB(ctx): State  |
   | + requestB()  -> state.handleB()|        | + name(): String       |
   | + setState(s: State)            |        +------------------------+
   +---------------------------------+                    ^
                 ^                                        |
                 | clients see only this                  | implements
                 |                            +-----------+-----------+
           +-----------+                      |                       |
           |  Client   |            +---------------+     +---------------+
           +-----------+            | ConcreteState |     | ConcreteState |
                                    |       A       |     |       B       |
                                    |---------------|     |---------------|
                                    | + handleA()   |     | + handleA()   |
                                    | + handleB()   |     | + handleB()   |
                                    | - localData   |     | - localData   |
                                    +---------------+     +---------------+
                                            |                     ^
                                            |  names its          |
                                            +---------------------+
                                                 successor

   The idea worth seeing. The bottom arrow is the coupling cost.
   If a ConcreteState names its successor, the states form a graph.
   If the Context owns the table instead, that arrow disappears and
   the Context gains a switch. There is no third option.
```

## 7. Dynamics

Two flows matter. A request that does not change state, and a request that does.
The important property is that the client never sees a transition happen. It
calls one method on the Context and the mode may or may not be different
afterwards.

```
Client            Context            ConcreteStateA      ConcreteStateB
  |                  |                      |                   |
  |-- requestA() --->|                      |                   |
  |                  |-- handleA(this) ---->|                   |
  |                  |                      |-- reads ctx data  |
  |                  |<--- returns self ----|                   |
  |                  |  (no transition)     |                   |
  |<--- result ------|                      |                   |
  |                  |                      |                   |
  |-- requestB() --->|                      |                   |
  |                  |-- handleB(this) ---->|                   |
  |                  |                      |-- exit work       |
  |                  |                      |-- new StateB ---->|
  |                  |<--- returns StateB --|                   |
  |                  |-- state = StateB     |                   |
  |                  |-- entry work ------------------------->  |
  |<--- result ------|                      |                   |
  |                  |                      |                   |
  |-- requestA() --->|                      |                   |
  |                  |-- handleA(this) ------------------------>|
  |                  |   (same call site, different behavior)   |
  |<--- result ------|                      |                   |
```

The state transition itself, drawn as a machine rather than a sequence. This is
the view a domain expert can review and the sequence diagram is the view a
programmer debugs with. Both are needed.

```
                  coin                 dispense
      +--------+ ------> +--------+ -------------> +--------+
      |  IDLE  |         |  PAID  |                |  IDLE  |
      +--------+ <------ +--------+                +--------+
          ^        refund     |
          |                   | coin  (self transition, refunded)
          |                   v
          |               +--------+
          +-------------- |  PAID  |
              timeout     +--------+

      Guard on dispense.  stock > 0, else the transition is not taken
      Entry action  PAID  start the 30 second refund timer
      Exit action   PAID  cancel the refund timer
```

Four timing notes that separate a working implementation from a subtly broken
one.

First, the order of exit work, state assignment and entry work has to be fixed
and documented. The safe order is exit the old state, assign the new state, then
run entry work. Running entry work before the assignment means an entry action
that calls back into the Context sees the old state.

Second, a transition triggered from inside an entry action is a re-entrant
transition. If entry work can itself cause a transition, the machine needs either
a queue of pending events or an explicit ban, because otherwise the assignment
from the outer transition overwrites the assignment from the inner one and the
machine silently lands in the wrong state.

Third, self transitions are ambiguous by default. Returning the same state object
can mean "nothing happened" or "leave and re-enter this state, running exit and
entry work". Erlang's `gen_statem` disambiguates this in its API by offering
`keep_state` and `repeat_state` as distinct return values, where the second
re-runs the state enter call
([Erlang gen_statem documentation](https://www.erlang.org/doc/apps/stdlib/gen_statem.html),
verified 2026-08-02). Any hand-rolled implementation needs the same distinction
or it will get one of the two cases wrong.

Fourth, the state must not be swapped from the Context's constructor before the
Context's own fields are initialised. In Java, C# and Kotlin a constructor may
legally call an overridable method, so an entry action that reads Context data
runs before the fields are assigned and observes defaults or nulls. Swift is the
instructive counter-example rather than another instance of the hazard. Its
two-phase initialisation forbids calling an instance method, reading an instance
property or referring to `self` until phase one has completed, so the compiler
rejects the mistake instead of letting it run
([The Swift Programming Language, Initialization](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/initialization/),
verified 2026-08-02).

## 8. Implementation variants

**States own transitions, returning the successor.** Each state method returns
the next state, and the Context assigns it. This is the form used in the code
examples below and it is the safest of the state-owned variants, because the
Context does the assignment in exactly one place and can wrap it with logging,
entry and exit hooks, and validation. The cost is that each state names its
successors, which is the coupling the Rust book flags
([The Rust Programming Language, chapter 18](https://doc.rust-lang.org/book/ch18-03-oo-design-patterns.html),
verified 2026-08-02).

**States own transitions, calling back into the Context.** Each state calls
`context.setState(next)` as a side effect. The Wikipedia treatment shows this
shape, with `ConcreteStateA` calling `setState(ConcreteStateB)` on the Context
([Wikipedia, State pattern](https://en.wikipedia.org/wiki/State_pattern),
verified 2026-08-02). It is more flexible, because a state can transition from
deep inside a helper, and correspondingly harder to audit, because there is no
single point where the assignment can be observed. It also opens the
transition-during-iteration failure in dimension 11. Prefer the returning form
unless a state genuinely needs to transition from a nested call.

**Context owns transitions with a table.** The states carry only behavior, and
the Context consults a map from state plus event to next state. This is the
variant that survives growth. The rules live in one readable declaration, an
illegal transition is a missing entry rather than a missing branch, and the table
can be tested exhaustively, printed as documentation and diffed in review. The
cost is that state-local transition logic, the case where the successor depends
on state-local data, has to be expressed as a guard function in the table rather
than as a line of ordinary code.

**Hybrid, and the recommended boundary.** The honest recommendation is a
threshold, not a principle. Under about five states with simple rules, let the
states own the transitions and keep the code local. At five or more states, or as
soon as one state has more than two outgoing edges, or as soon as a non-programmer
needs to review the rules, move the transitions into a declared table owned by the
Context and keep the states for behavior only. The tipping point is when someone
first asks "what are all the transitions" and the answer requires opening more
than two files.

**Function per state rather than object per state.** In a language with
first-class functions, a state is a function from event to next function. This is
exactly Erlang's `state_functions` callback mode, where "the state must be an
atom and uses that state as the name of the current callback function, arity 3",
and the documentation motivates it as co-locating all code for a state in one
function ([Erlang gen_statem documentation](https://www.erlang.org/doc/apps/stdlib/gen_statem.html),
verified 2026-08-02). Akka Typed takes the same shape in a typed setting, where
"each state becomes a distinct behavior and after processing a message the next
state in the form of a `Behavior` is returned"
([Akka Typed FSM documentation](https://doc.akka.io/libraries/akka-core/current/typed/fsm.html),
verified 2026-08-02). The variant removes the class boilerplate and keeps the
co-location benefit. It loses the ability to attach state-local fields to a type,
though a closure recovers that.

**Single handler over an explicit state value.** The opposite pole. One function
receives the current state and the event and returns the next state, matching on
the pair. Erlang's `handle_event_function` mode is this, allowing "the state to
be any term" with `Module:handle_event/4` handling all states. It is the right
shape when many states share handling of a common event, and the wrong shape when
states diverge, which is precisely the trade the two `gen_statem` modes exist to
let you make.

**States as types, checked at compile time, sometimes called typestate.** Each
state is a distinct type and each transition is a method that consumes the old
type by value and returns the new one. An operation not legal in a state simply
does not exist on that type, so the compiler rejects the call. Rust is the
mainstream language where this is idiomatic, because ownership makes consuming
the old value enforceable. The Rust book presents this as the alternative to the
object form and argues it converts a runtime check into a compile-time one. The
limits are real. The state cannot be chosen from runtime data without erasing the
type again, the state cannot be stored in a homogeneous collection, and the whole
machine cannot be persisted or sent over a wire without a discriminator.

**Stateless shared instances.** Where a ConcreteState holds no per-Context data,
allocate one instance per state for the whole process and share it. Every state
method then takes the Context as its first parameter. This removes allocation
from the hot path entirely and is the correct default for high-frequency machines
such as protocol parsers.

**Hierarchical states.** A state has substates, and an event not handled by a
substate bubbles to its parent. This is Harel's central contribution and it is
the answer to explosion. Building it by hand means giving each state a parent
pointer and writing the bubbling dispatch, which is a small state machine engine.
Spring Statemachine supplies it as a framework feature, with hierarchical state
structure, regions, triggers, transitions, guards and actions, plus pseudostates
for choice, junction, fork, join and history
([Spring Statemachine reference](https://docs.spring.io/spring-statemachine/docs/current/reference/),
verified 2026-08-02).

**Language note on Go.** Go has interfaces but no inheritance, so the classical
diagram translates directly with an interface and per-state structs, and the
result is idiomatic. The table variant is arguably more idiomatic still, because
a `map[state]map[event]state` is a compact and reviewable declaration and Go
culture prefers explicit data over dispatch.

**Language note on Python.** The dynamic variant seen in real Python code
reassigns `self.__class__` so the object literally changes class, which matches
the GoF intent wording exactly. It is clever, it works, and it is hostile to
readers and to static analysis. Prefer holding a state attribute.

## 9. Known production uses

**Erlang/OTP `gen_statem`.** The OTP standard library ships a state machine
behaviour with two callback modes. In `state_functions` mode each state is a
callback function of arity three named after the state, and transitions are
returned as `{next_state, NextState, NewData [, Actions]}`. This is the State
pattern realised with functions rather than classes, inside a runtime used for
telephone switches and messaging systems. Erlang/OTP documentation,
`gen_statem`, https://www.erlang.org/doc/apps/stdlib/gen_statem.html verified
2026-08-02.

**Akka Typed finite state machines.** Akka documents modelling an FSM by making
each state a distinct `Behavior`, returned from the message handler, with
`Behaviors.receiveMessage`, `Behaviors.withTimers` for state timeouts,
`Behaviors.unhandled` and `Behaviors.ignore`. Akka documentation, Behaviors as
finite state machines,
https://doc.akka.io/libraries/akka-core/current/typed/fsm.html verified
2026-08-02.

**Spring Statemachine.** A Spring project providing flat and hierarchical state
machines, regions, guards, actions, triggers including timer triggers, an
extended state for variables outside the state identity, and pseudostates for
choice, junction, fork, join, history and entry or exit points. It is the
production answer for JVM applications whose machine outgrew the flat pattern.
Spring Statemachine reference documentation,
https://docs.spring.io/spring-statemachine/docs/current/reference/ verified
2026-08-02.

**Boost.Statechart, C++.** A header-only Boost library by Andreas Huber Dönni
for "straightforward transformation from UML statechart to executable C++ code
and vice versa", with hierarchical states, orthogonal states, entry and exit
actions, guards, history and event deferral, built for compile-time statechart
validation and type safety. Boost documentation, Boost.Statechart,
https://www.boost.org/doc/libs/release/libs/statechart/doc/index.html verified
2026-08-02.

**W3C SCXML and XState.** SCXML is a W3C Recommendation of 1 September 2015
providing "a generic state-machine based execution environment based on CCXML and
Harel State Tables". XState is the JavaScript and TypeScript implementation of
statecharts in wide web use, supplying hierarchy, parallel states and actor-model
communication as first-class concepts. W3C, State Chart XML,
https://www.w3.org/TR/scxml/ verified 2026-08-02. Stately, state machines and
statecharts documentation, https://stately.ai/docs/state-machines-and-statecharts
verified 2026-08-02.

**TCP, RFC 9293.** The protocol specification defines eleven connection states,
LISTEN, SYN-SENT, SYN-RECEIVED, ESTABLISHED, FIN-WAIT-1, FIN-WAIT-2, CLOSE-WAIT,
CLOSING, LAST-ACK, TIME-WAIT and CLOSED, with the transition diagram in section
3.3.2, figure 5. This is the domain the GoF book chose for its own worked example
and it remains the clearest case of behavior that is genuinely state-dependent
rather than merely data-dependent. IETF, RFC 9293, Transmission Control Protocol,
August 2022, https://www.rfc-editor.org/rfc/rfc9293.html verified 2026-08-02.

**AWS Step Functions, Amazon States Language.** A managed service in which the
machine is declared in JSON, each state has a `Type` and a `Next` field naming
its successor, and the state types are Task, Choice, Parallel, Map, Pass, Wait,
Succeed and Fail. It is the table-driven alternative in industrial form, and it
is cited here as the named counter-example to the object-per-state design rather
than as an instance of it. AWS Step Functions Developer Guide, Discovering
workflow states,
https://docs.aws.amazon.com/step-functions/latest/dg/concepts-states.html
verified 2026-08-02.

**The Rust Programming Language, chapter 18.** The official Rust book implements
the pattern with a blog post moving through Draft, PendingReview and Published,
using `Box<dyn State>`, then rewrites it with `DraftPost`, `PendingReviewPost`
and `Post` as distinct types. This is a documented reference implementation in a
language's official book rather than a deployed system, and it is listed because
it is the best available side-by-side comparison of the two forms.
https://doc.rust-lang.org/book/ch18-03-oo-design-patterns.html verified
2026-08-02.

## 10. Consequences

Positive.

- All behavior for one mode sits in one class, so the question "what does the
  system do while suspended" has a single answer with a single file.
- The conditionals disappear. Adding a mode does not require finding and editing
  every switch, which removes the most common source of partially updated
  machines.
- Transitions become explicit objects of study. They can be logged, validated,
  rendered as a diagram and reviewed by someone who does not read code.
- State-local data gets a natural home and a natural lifetime. A retry counter
  that only means something during retry lives on the retrying state and is
  destroyed with it, which removes a class of stale-field bugs.
- Entry and exit actions have somewhere obvious to go, which makes resource
  acquisition and release symmetric with the mode they belong to.
- The state objects are substitutable, so a test can install an arbitrary state
  directly and exercise one mode in isolation without driving the machine through
  every preceding transition. This is the largest testing win and it is treated
  in dimension 15.
- Illegal operations become absent by construction rather than rejected
  defensively, which is a stronger guarantee than a runtime check.

Negative.

- Object count grows by one class per state, and the classes are often small.
  A machine with fifteen states costs fifteen files that each carry a few lines
  of real logic.
- The behavior of a single operation is now scattered across every state class.
  Answering "what does cancel do" requires reading all of them, which is the
  exact inverse of the benefit.
- Adding a method to the State interface is an edit to every ConcreteState. In
  languages without exhaustiveness checks this fails silently at runtime rather
  than loudly at compile time.
- States are coupled to their successors in the state-owned-transitions form, so
  the module has an internal dependency graph that mirrors the machine graph.
- The current state is a reference, not a value, which breaks persistence,
  serialisation, equality, logging and metrics until each of those is explicitly
  repaired.
- Debugging is harder in the small. A stack trace shows the state class, which is
  helpful, but a breakpoint on "any transition" requires the transitions to have
  been funnelled through one place, which the callback variant does not do.
- The pattern gives no help with hierarchy, orthogonal regions, deferred events
  or history. Applications that need those end up hand-building a partial
  statechart engine with none of the testing an existing engine has.

## 11. Failure modes and misuse

Written as symptom, cause, fix. The symptoms are drawn from practice rather than
from a source, and are stated as such.

**The persistence round-trip that lost the machine.** Symptom. A workflow resumes
after a deploy in the wrong state, usually the initial one, and the bug is only
visible for records created before the restart. Or a `NotSerializableException`,
a `TypeError: Object of type Paid is not JSON serializable`, or a silently empty
column. Cause. The current state is a pointer to a polymorphic object. Nothing
writes it. The code that saves the Context saves the shared data and skips the
state field because it has no natural representation. Fix. Give every
ConcreteState a stable string discriminator that is part of its contract and is
never derived from the class name, because class names get refactored and the
database does not. Persist the discriminator. Rehydrate through one explicit
table from discriminator to state object, keep that table in the same file as the
state classes, and write a test that asserts every ConcreteState appears in it
and that every discriminator in the table maps to a distinct class.

**The state name that was the class name.** Symptom. After a rename or a package
move, records saved before the change fail to load, or worse, load into the wrong
state because a fallback silently picked the initial one. Cause. Persistence used
reflection or the type name as the discriminator. Fix. An explicit constant per
state, asserted by a test that pins the exact strings so a rename breaks the test
rather than production.

**State explosion.** Symptom. A directory with twenty-eight state classes, most
of them named as a combination, `ActiveVerifiedDirty`, `ActiveVerifiedClean`,
`ActiveUnverifiedDirty`. Nobody can draw the diagram. Cause. The state is a
product of independent flags, and each new flag doubles the class count. The
statecharts documentation describes this progression precisely, from two states
to four to eight with twelve transitions on adding two boolean aspects
([statecharts.dev](https://statecharts.dev/state-machine-state-explosion.html),
verified 2026-08-02). Fix. Separate the axes. Keep the genuinely sequential
lifecycle as states, and move the independent flags into extended state, that is,
ordinary fields on the Context, guarded by transition guards. If the axes really
do interact, adopt hierarchy or orthogonal regions, which means adopting an
engine rather than extending the pattern.

**Transition during iteration.** Symptom. A `ConcurrentModificationException`, a
half-processed batch, or an event handled by a state the machine had already left,
occurring only under load. Cause. The callback variant, where a state calls
`context.setState()` from inside a loop the Context is running, so the Context
continues with a stale local reference to the old state. Fix. Return the
successor rather than assigning it, and have the Context complete the current
operation before installing the new state. Where events can arrive during a
transition, queue them and drain the queue after the assignment, which is what
`gen_statem` does with postponed events.

**The torn transition under concurrency.** Symptom. An order that is both shipped
and cancelled, or a counter incremented by an exit action twice. Cause. Two
threads read the same current state, both compute a successor, both assign. The
state pointer is a plain field and the read-decide-write sequence is not atomic.
Fix. Serialise transitions on the Context, either with a lock held across the
whole read-decide-write, or by making the Context an actor with a mailbox, which
is the property that makes the Akka behavior form safe by construction.

**The Context reference cycle.** Symptom. Steadily growing memory in a
long-running process, and in reference-counted runtimes such as Swift or Python
with `__del__`, objects that never deallocate. Cause. The Context holds the state
and the stateful ConcreteState holds a strong reference back to the Context. Fix.
Pass the Context as a method parameter rather than storing it, which is the
reason the shared-flyweight form takes the Context on every call. Where a stored
reference is unavoidable, make it weak.

**The state interface that grew a leak.** Symptom. Casts from `State` to a
concrete state inside the Context, followed by `instanceof` or `isinstance`
branches, which is the switch the pattern was adopted to delete, now written
against types. Cause. The Context needs something only some states can do. Fix.
Either widen the interface with a method that has a harmless default in the
states that do not care, or accept that the Context is asking a state-shaped
question and add a query method such as `canCancel()` that every state answers.

**Entry action run twice, or not at all.** Symptom. A duplicate outbound webhook,
two timers running, or a resource never released. Cause. A self transition
returning the same state object, where the implementation cannot tell "stay" from
"leave and re-enter". Fix. Represent the two cases distinctly, as `gen_statem`
does with `keep_state` versus `repeat_state`, and route every assignment through
one Context method that compares old and new before running exit and entry work.

**The pattern applied to a data table.** Symptom. Nine ConcreteState classes,
each with one method, each returning a different constant, and a factory that
picks between them by string. Cause. The modes differ in data, not behavior. Fix.
Delete the hierarchy and keep a map from the discriminator to the constant. This
is the most common over-application and it costs a code review to catch.

**The untestable initial state.** Symptom. A test for the terminal state has to
call fourteen methods in order to reach it, and it breaks whenever an early
transition changes. Cause. The Context's constructor hard-codes the initial state
and offers no other entry point. Fix. A package-private or test-visible
constructor that accepts a starting state, which is cheap and turns a fourteen
step test into a one line one.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3. The
alternatives are real designs in use, not strawmen.

| Force | State pattern (object per state) | Enum plus switch in each method | Transition table owned by Context | Typestate (states as types) | Statechart engine (Spring Statemachine, XState) | Strategy |
|---|---|---|---|---|---|---|
| Where one state's behavior lives | One class, co-located | Scattered across every switch | Split. Behavior in handlers, rules in the table | One type, co-located | One node in the chart | Not the concern |
| Where one operation's behavior lives | Scattered across every state | One method, co-located | One handler map, co-located | Scattered across types | One transition set | One class |
| Adding a state | One new class | Edit every switch | One table row plus a handler | One new type plus its methods | One node, often in a diagram | Not applicable |
| Adding an operation | Edit every state class | Edit one method | Edit the handler map | Edit every type | One event, often in a diagram | Widen the interface |
| Transition rules visible in one place | No, unless states are stripped of them | No, smeared across assignments | Yes. That is its purpose | No, spread across signatures | Yes, and renderable as a diagram | Not applicable |
| Illegal transitions | Absent by construction | Runtime check at best | Missing table entry, checkable | Compile error | Rejected by the engine | Not applicable |
| Persistence across restart | Poor. Needs a discriminator table | Trivial. The enum is the value | Trivial. The key is the value | Poor. Types are erased at the boundary | Handled by the engine, often with a persister | Poor, same as State |
| Hierarchy and orthogonal regions | Not supported | Not supported | Not supported without extension | Not supported | Supported. That is the reason to adopt one | Not applicable |
| State-local data | Strong. Fields on the state object | Weak. Fields on the Context, always present | Weak, same as enum | Strong. Fields on the type | Extended state plus per-state data | Strong |
| Cognitive load | Medium. Indirection plus object count | Low at three states, high at ten | Low. One table to read | Medium. Ownership moves are unusual | High. A framework to learn | Low |
| Type or class count | Plus one per state | None | None beyond handlers | Plus one per state | Plus configuration | Plus one per algorithm |
| Runtime, data-driven graph | Poor. Graph is compiled in | Poor | Good. The table can be loaded | Impossible | Good. Often the point | Not applicable |
| Latency | One virtual call, possibly megamorphic | One well-predicted branch | One map lookup | Direct call, inlinable | Framework overhead per event | One virtual call |
| Operability | Poor by default. Needs a name per state | Good. The enum is already loggable | Good. Keys are loggable | Poor at the boundary | Good. Engines emit events | Poor by default |
| Concurrency safety | Needs external serialisation | Needs external serialisation | Needs external serialisation | Ownership prevents sharing | Usually handled by the engine | Usually not stateful |

Reading of the table. The State pattern wins on state-local behavior and
state-local data, and loses on transition visibility, persistence and
operability. The enum-plus-switch design that everyone starts with is genuinely
better below about four states and genuinely worse above about six. A transition
table owned by the Context recovers the visibility and persistence the pattern
loses, at the cost of pushing state-local logic into guard functions. Typestate
is the strongest correctness story and the weakest boundary story. A statechart
engine wins the moment hierarchy or orthogonal regions appear, and it is
over-engineering before then.

## 13. Related and incompatible patterns

- **Strategy.** The confusion this entry exists to settle, treated in full below
  because a bare list entry does not do it justice.
- **Flyweight.** Composes directly. Where a ConcreteState holds no per-Context
  data, one shared instance serves every Context, which is exactly Flyweight
  applied to states. This is the reason state methods conventionally take the
  Context as a parameter rather than storing it, and it is the reason states are
  so often written as singletons.
- **Singleton.** The usual realisation of the shared form, and a hazard. A state
  singleton is safe precisely when it is immutable and stateless. The moment
  somebody adds a field to a shared state, every Context in the process shares
  it, and the resulting bug looks like data corruption rather than aliasing.
- **Command.** Composes on the event side. Where events arriving at the machine
  are reified as Command objects, transitions can be queued, replayed, postponed
  and audited. This is how deferred events are implemented in practice, and it is
  the pairing that makes an event-sourced state machine possible.
- **Memento.** The natural companion for undo. A Memento captures the Context
  including its state discriminator, so a machine can be rolled back to an
  earlier point. Without it, undo across a state machine means running the
  transitions backwards, which is usually not well defined.
- **Observer.** Composes on the output side. State changes are the events other
  parts of a system most often want to hear about, and publishing a transition
  event from the single Context assignment point is cheap and gives operability
  for free.
- **Bridge.** Sits on the same extensibility axis. Both separate an abstraction
  from a set of implementations so implementations vary independently. Bridge's
  implementations are chosen once and are stable. State's are swapped constantly
  and swap themselves.
- **Template Method.** A frequent pairing inside a state hierarchy. An abstract
  state supplies default handling for every event, usually rejecting or ignoring
  it, and concrete states override only what they handle. This removes the
  boilerplate that otherwise makes the pattern expensive, and it converts a
  missing implementation from a compile error into a default, which is a real
  trade rather than a free win.
- **Interpreter and the table-driven machine.** A substitute rather than a
  collaborator. Where the machine is data, the pattern is the wrong shape.
- **Visitor.** Actively conflicts in intent. Visitor makes adding operations
  cheap and adding types expensive. State makes adding types cheap and adding
  operations expensive. Applying both to the same hierarchy leaves neither axis
  cheap, and the usual outcome is a double dispatch that nobody can follow.
- **Null Object.** A small, useful companion. A terminal or unknown state
  implemented as a state that accepts every event and does nothing removes a
  layer of null checks from the Context.

### State versus Strategy, in full

These two patterns have identical structure. Both define an interface, both have
a context holding a reference to an implementation of that interface, both
forward requests to it, and both allow the reference to be swapped at runtime. If
you draw the class diagrams side by side and erase the names, you cannot tell
them apart. Wikipedia records the same observation, noting that the state pattern
"can be interpreted as a strategy pattern, which is able to switch a strategy
through invocations of methods defined in the pattern's interface"
([Wikipedia, State pattern](https://en.wikipedia.org/wiki/State_pattern),
verified 2026-08-02).

The difference is entirely in intent and in who drives the swap, and that
difference produces a set of observable consequences.

| Question | State | Strategy |
|---|---|---|
| Why does the implementation vary | Because the object is in a different mode | Because a different algorithm was chosen for the same task |
| Who chooses the implementation | The object itself, or its own transition rules | The client, or the wiring, usually once |
| How often does it change | Continuously, as part of normal operation | Rarely, often never after construction |
| Does the implementation know its successors | Usually yes. A state returns or installs the next state | No. A strategy has no notion of a next strategy |
| Are the implementations aware of each other | Yes, in the state-owned-transitions form | No. Strategies are mutually ignorant by design |
| Is the set of implementations a graph | Yes. The transition graph is the model | No. It is a flat set of interchangeable options |
| Does the client know a swap happened | No. The swap is internal and invisible | Usually yes. The client picked it |
| Is a swap valid from anywhere | No. Only along declared transitions | Yes. Any strategy can replace any other |
| What does the interface represent | The full set of events the object responds to | One operation, or one small cohesive group |
| Typical interface width | Wide. One method per state-dependent request | Narrow. Often a single method |
| Natural degenerate form | A function per state | A closure or a function pointer |
| What breaks if you swap arbitrarily | The machine reaches an invalid state | Nothing. That is the point |
| Persistence concern | Real. The current state is domain data | Rare. The strategy is configuration |
| Testing focus | The transition graph and per-state behavior | Each algorithm against the same contract |

The single most useful discriminator is the successor question. A state object
usually knows which states can follow it, either by returning one or by calling
`setState` with one. That knowledge is what makes the objects a graph rather than
a set, and it is why the Rust book lists inter-state coupling as an inherent
downside of the state pattern and never says anything of the sort about strategy
([The Rust Programming Language, chapter 18](https://doc.rust-lang.org/book/ch18-03-oo-design-patterns.html),
verified 2026-08-02). A strategy that named another strategy would be a design
error, because a client that chose quicksort has no interest in the sort deciding
to become mergesort halfway through.

The second discriminator is the direction of the swap. In Strategy the swap comes
from outside and is visible to whoever made it. In State the swap comes from
inside and is invisible to callers. This is why a Strategy is usually injected in
a constructor and a State is usually assigned in the middle of a method.

Two practical consequences follow. First, a Context whose states never transition
and are chosen by the caller is a Strategy that has been given the wrong name, and
it should be renamed and simplified, because calling it a state machine invites
future maintainers to look for a transition graph that does not exist. Second, a
Strategy that has grown a field recording which strategy should come next has
become a State machine and should be modelled as one, with the transitions
declared rather than hidden inside the algorithms.

### Who owns transitions, the Context or the States

Both are valid and both ship in production. The choice is a real trade and it
should be made deliberately rather than by copying whichever example was read
first.

**States own transitions.** Each state either returns its successor or calls
`setState` on the Context. The argument for it is locality. The rule "from PAID,
a dispense event with stock available leads to IDLE" is written in the PAID class
next to the code that performs the dispense, so a reader working on the paid case
sees the whole story in one place. It also allows the successor to depend on
state-local data without ceremony, which a declarative table can only express by
calling out to a guard. This form suits small machines and machines where the
transition logic is genuinely intertwined with the work.

The argument against it is that the graph is now spread over N files and cannot
be read, diffed, diagrammed or reviewed as a unit. Adding a state means finding
every state that should be able to reach it. Removing a state means finding every
state that references it, and the compiler will find those, which is the one
genuine advantage the coupling buys.

**The Context owns transitions.** The Context holds a declared table from state
plus event to next state, optionally with guards and actions, and the states hold
only behavior. The argument for it is that the machine's rules become one
artifact. That artifact can be printed as a diagram, reviewed by a domain expert,
tested exhaustively including for unreachable states and missing edges, compared
across versions in a pull request, and in the extreme loaded from configuration.
Every framework that grew past this problem chose this shape. Spring Statemachine
declares transitions in a configuration adapter with `withExternal().source(...)
.target(...).event(...)`, entirely separate from the code that runs in each state
([Spring Statemachine reference](https://docs.spring.io/spring-statemachine/docs/current/reference/),
verified 2026-08-02). SCXML puts transitions in the document. Amazon States
Language puts a `Next` field on each state node in JSON
([AWS Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-states.html),
verified 2026-08-02).

The argument against it is indirection. Reading a state class no longer tells you
what happens next, and a transition that depends on state-local data has to reach
that data through the Context or through a guard closure, which is more ceremony
than an ordinary conditional.

**The recommendation, with its boundary stated.** Default to the states owning
transitions while the machine has fewer than five states and no state has more
than two outgoing edges. Move to a Context-owned table at the first of these
three signals, whichever arrives soonest. A sixth state is added. Somebody asks
for a diagram of the machine and it cannot be produced from one file. A
non-programmer needs to approve the rules. The migration is mechanical and is
written out in dimension 14, so choosing the local form early is not a trap, it
is a deliberately reversible starting point.

Note the composite form that most large systems land on. The Context owns the
table, the states own the work, and the table's guards are methods on the states.
This keeps the graph readable and the state-dependent logic local, and it costs
one indirection.

### Relationship to formal finite state machines and to statecharts

A finite state machine is a formal object with a transition function. The State
pattern is one encoding of that function, in which the function is decomposed by
source state and each piece is attached to an object. Nothing about the pattern
makes the machine more correct than the same machine encoded as a table. The
formal properties, reachability, determinism, completeness, absence of live-lock,
are properties of the graph and are analysable only when the graph is available
as data. This is a direct argument for the table variant in any system where
those properties matter, and it is the reason model checking tools consume tables
and diagrams rather than class hierarchies.

Statecharts are strictly more expressive. Harel's 1987 paper extends state
diagrams along three axes, hierarchy, concurrency and communication, so that a
compact diagram can describe behavior a flat machine could only describe with an
exponential number of states
([Science of Computer Programming volume 8, 1987, pages 231 to 274](https://www.sciencedirect.com/science/article/pii/0167642387900359),
verified 2026-08-02). UML absorbed the formalism. The current formal
specification is UML 2.5.1, OMG document formal/17-12-05, December 2017
([OMG UML specification page](https://www.omg.org/spec/UML/), verified
2026-08-02), and its behavioral state machines are described as an object-based
variant of Harel statecharts
([uml-diagrams.org on state machine diagrams](https://www.uml-diagrams.org/state-machine-diagrams.html),
verified 2026-08-02).

The practical consequence for a reader deciding what to build. The State pattern
gives you neither hierarchy nor orthogonal regions nor history nor deferred
events. Each of those can be hand-built on top of it, and each hand-built version
is a piece of a state machine engine that will be less tested than an existing
one. The decision point is honest and specific. If any of the following is true,
adopt an engine rather than extending the pattern. Two states share most of their
event handling and differ in a few cases, which is what hierarchy solves. The
object is genuinely in two modes at once along independent axes, which is what
orthogonal regions solve. An event arriving in the wrong state must be handled
later rather than dropped, which is deferred events. Returning to a composite
state must resume at the substate it came from, which is history.

### Persisting state across a restart

This deserves its own treatment because it is the practical weakness of the
object-per-state design and it is under-discussed in the pattern literature.

The problem. The current state is a reference to an object of a polymorphic type.
Every durable representation a real system uses, a database column, a JSON
document, a protocol buffer, a message on a queue, a URL, is a value. There is no
general way to write a `Box<dyn State>`, a Java `State` reference or a Python
instance to a column. So the boundary between the in-memory machine and the store
demands a translation both ways, and that translation is a table from a
discriminator value to a state object. Which is to say, the design deletes a
switch from the domain logic and reintroduces one at the persistence boundary,
where it is less visible and usually less tested.

Four consequences that bite in production.

- **The translation table is easy to leave incomplete.** Adding a state means
  adding a class and adding a row to the rehydration table. Nothing links the
  two, so the second step gets forgotten, and the symptom is a record that loads
  into the initial state months later.
- **Serialisation frameworks do the wrong thing by default.** A framework that
  writes fields will either fail on the state reference, silently skip it, or
  write the whole state object graph including a back reference to the Context,
  which is worse. Java serialisation of a state object that holds the Context
  will drag the entire Context into the stream.
- **Class names are not stable identifiers.** Any scheme that writes the type
  name binds the database schema to the package layout, and a refactor becomes a
  data migration.
- **State-local data has nowhere to go.** The strongest reason to use the pattern
  is that a state can carry fields, and those fields also have to be persisted,
  keyed by which state they belong to. This is where a naive design either loses
  the data or grows a column per state.

The shape that works. Treat the persisted form as the authoritative record and
the object graph as a projection of it. Concretely. Give every ConcreteState an
explicit, hand-written, never-derived discriminator constant. Persist the
discriminator plus a per-state payload, usually a small JSON object, alongside
the Context's shared data. Rehydrate through one factory that maps discriminator
to state, and treat an unknown discriminator as a loud error rather than a
fallback to the initial state, because the fallback turns a deploy ordering
mistake into silent data corruption. Write two tests. One asserts every
ConcreteState has a discriminator and that all discriminators are distinct. One
round-trips every state through save and load and asserts the machine behaves
identically afterwards.

The alternative that avoids the problem entirely. Persist the state as an enum or
string and rebuild the state object on load, that is, treat the state objects as
a runtime convenience rather than as the model. This is what every framework
does. Spring Statemachine's states are enumerable values with a separate machine
configuration, and Amazon States Language state names are strings in a document.
If the machine is long-lived, distributed or crosses a service boundary, start
from the value-typed representation and add objects for behavior on top, rather
than starting from objects and bolting values on at the edge.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The named refactoring is
Replace Type Code with State/Strategy, see the refactoring family entry. Ordered
steps, each one leaving the code green.

1. Find the field that carries the mode and every conditional that reads it. If
   there is only one such conditional, stop. The pattern does not apply, see
   dimension 4.
2. Write the transition graph on paper or in a diagram, derived from the
   assignments to the mode field. This step almost always finds a transition
   nobody intended, and finding it is worth the exercise even if the refactor is
   abandoned.
3. Make the mode field private and route every read and write through accessor
   methods. Run the tests. Nothing else changes.
4. Introduce the State interface with one method per operation that branches on
   the mode, plus a `name()` returning the discriminator. Keep the methods as
   close as possible to the existing signatures.
5. Create one ConcreteState per mode with an empty or delegating body. Add the
   discriminator constants and the discriminator-to-state table now, not later,
   because adding it later means retrofitting persistence, which is the failure
   in dimension 11.
6. Move one branch, from one conditional, into the matching ConcreteState. Leave
   the conditional in place calling into the state. Run the tests. Repeat until
   that conditional has one branch left, then replace the whole conditional with
   a forward to the state. This is Replace Conditional with Polymorphism applied
   one arm at a time, and doing it one arm at a time is what keeps the refactor
   reversible.
7. Repeat step 6 for each remaining conditional.
8. Replace the mode field with a reference to the current State, and make the
   accessor from step 3 the single assignment point. Put the logging, the entry
   and exit hooks, and the transition validation in that one method.
9. Decide transition ownership per dimension 13. If the machine has five or more
   states, extract the transitions from the state classes into a table on the
   Context in a separate commit, so the behavior move and the rules move are
   reviewable independently.
10. Add the tests from dimension 15, especially the round-trip test and the
    exhaustive discriminator test.

Removing the pattern when it stops earning its place. Signals that it should go
include ConcreteStates with one trivial method each, a machine that never
transitions after construction, or a persistence layer that has become larger
than the states it serves.

1. Confirm the states carry no state-local data. If they do, that data needs a
   home first, either as nullable fields on the Context or as a sum type, and
   that is a separate change.
2. Add the discriminator as a real field on the Context, kept in sync with the
   state object on every assignment. Run the tests. The system now carries both
   representations, which is the safe intermediate state.
3. Change every read of the current state that only needs the identity to read
   the discriminator instead. Run the tests after each one.
4. Replace the transitions with a table keyed by discriminator, if one does not
   already exist.
5. Inline each ConcreteState's method bodies back into the Context, guarded by a
   switch over the discriminator. Do one operation at a time. This is Inline
   Class run backwards through Replace Polymorphism with Conditional, and it is
   deliberately painful, which is the correct signal if there were more than four
   states.
6. Delete the State interface and the ConcreteStates. Delete the
   discriminator-to-state table, which is the moment the persistence layer gets
   materially simpler and the reason a small machine is often better off without
   the pattern.

## 15. Testing and verification

This dimension is practice rather than sourced claim.

Easier because of the pattern.

- A single state can be tested in isolation by constructing it and calling its
  methods with a test Context. No transition sequence is needed to reach the
  state under test, which removes the long arrange blocks that make state machine
  tests brittle.
- The set of legal transitions is enumerable when the Context owns the table, so
  a single test can assert the entire graph rather than sampling it.
- Substituting a state is trivial. A test can install a state that records every
  call and returns a scripted successor, which gives a spy without a mocking
  framework.
- Entry and exit actions are directly observable, because they run in one place.

Harder because of the pattern.

- Asserting which state the machine is in requires either a public accessor,
  which widens the API for tests, or a discriminator, which is the right answer
  and is needed for persistence anyway.
- Coverage becomes misleading. Line coverage over state classes looks high while
  most transitions have never been taken, because a state class is mostly
  reached, not mostly exercised.
- A missing implementation in a new state fails at runtime rather than at compile
  time in languages without exhaustiveness checking, so a test has to stand in
  for the compiler.

Techniques that apply.

- **Transition matrix test.** One parameterised test over the cross product of
  every state and every event, asserting either the expected successor or an
  explicit rejection. For a machine with eight states and six events this is
  forty-eight assertions, which sounds like a lot and is the cheapest complete
  specification of the machine you will ever write. It also catches the
  transition nobody intended, which step 2 of the refactoring path finds by hand.
- **Reachability test.** Walk the graph from the initial state and assert every
  state is reachable and every terminal state is reachable from every state that
  should be able to terminate. This catches the orphan state a refactor forgot to
  remove.
- **Round-trip persistence test.** For every ConcreteState, put a machine into
  that state, save, load, and assert the loaded machine behaves identically for
  every event. This is the single test that would prevent the most common
  production failure in dimension 11.
- **Discriminator completeness test.** Reflectively or by an explicit registry,
  assert that every ConcreteState appears in the rehydration table and that no
  two share a discriminator. Assert the exact discriminator strings so a rename
  breaks a test rather than a database.
- **Contract test over states.** One abstract test case written against the State
  interface, subclassed once per ConcreteState, asserting the invariants every
  state must hold, for example that no method leaves the Context without a
  current state, and that `name()` is non-empty and stable.
- **Property-based test on the graph.** Generate random event sequences and
  assert the machine never reaches a state outside the declared set and never
  throws. This finds the re-entrant transition and the ordering bugs from
  dimension 7 far more reliably than example tests do.
- **Model-based test.** Where a table exists, drive the real implementation and a
  trivial reference model from the same event stream and compare final states.
  This is only available in the table variant, which is another argument for it.
- **A fake Context, not a mock.** State methods receive the Context, so a small
  handwritten fake with public fields is clearer and less fragile than a mocking
  framework configured with six expectations.

## 16. Observability signals

The pattern hides the current mode behind a pointer. Unless that is repaired
deliberately, a production incident produces no answer to the first question an
operator asks, which is what state was it in. This dimension is practice.

What to record.

- **A state gauge, labelled by state name, counting Contexts currently in each
  state.** This is the single most useful signal for a long-lived machine such as
  an order or a subscription, because the distribution answers whether anything
  is stuck. Use the persisted discriminator as the label, never the class name,
  so the label survives refactors.
- **A transition counter, labelled by from-state, to-state and event.** This is
  the graph, observed. It answers which edges are actually taken in production,
  which is regularly different from what the design says, and it makes dead edges
  visible so they can be deleted.
- **A rejected-transition counter, labelled by state and event.** An event
  arriving in a state that cannot handle it is normally a client bug or a race,
  and it is invisible unless counted. Silently ignoring an unhandled event is the
  most common way a machine hides a defect.
- **A histogram of time spent in each state**, recorded on exit and labelled by
  state. Long-lived machines with a timeout per state need this to set the
  timeout honestly rather than by guess.
- **A structured log line at the single assignment point**, carrying the Context
  identifier, the from-state, the to-state, the triggering event and a
  correlation identifier. Emitting this from one method is the practical reward
  for choosing the returning-successor variant over the callback variant.
- **A trace span per transition**, or at minimum a span attribute on the enclosing
  request span carrying the resulting state, so a slow request can be attributed
  to a state rather than to a method.

A healthy instance on a dashboard. The state gauge shows the expected shape for
the domain, usually a large terminal bucket and small working buckets, and the
working buckets are flat rather than growing. The transition counter shows edges
in the proportions the business expects, and every edge in the declared graph has
non-zero traffic over a week. Rejected transitions are near zero. Time-in-state
histograms have a tight body and a short tail.

A failing instance. The gauge for one non-terminal state climbs monotonically,
which is the stuck-machine signature and usually means a transition out of that
state depends on an event that stopped arriving. Or the rejected-transition
counter for one state and event pair rises after a deploy, which means a client
now sends an event the machine no longer expects. Or an edge that should carry
traffic drops to zero while a neighbouring edge picks it up, which is a guard
that changed meaning. Or the time-in-state tail for one state grows without the
count growing, which points at a small set of records that will never move and is
the population to inspect. Or transitions appear between states the declared
graph says are not adjacent, which means somebody is assigning the state field
outside the single assignment point, and that is a design defect rather than an
operational one.

## 17. Security and privacy implications

The pattern is close to silent on security in a closed design where every state
ships in the same build. Three genuine implications appear, and one privacy
caveat. This dimension is analytical.

**The state machine is an authorisation surface, and treating it as one is the
main win.** Where an operation is legal only in some states, the state machine is
already expressing an access rule, and encoding that rule in the shape of the
code is stronger than expressing it as a check. A refund that is only reachable
from the SETTLED state cannot be issued against a pending payment, because no
code path exists. The failure to watch for is the escape hatch, a method on the
Context that performs the operation without going through the current state,
added for an administrative tool or a test, which quietly bypasses every rule the
machine encodes. Route every state-dependent operation through the state, without
exception, and if an administrative override is genuinely needed, model it as a
transition with its own audit trail rather than as a bypass.

**Rehydration from persisted state is deserialisation of attacker-influenced
data.** The discriminator that selects which state object to construct arrives
from a database, a queue or in the worst case a client-supplied token. If the
mapping from discriminator to class is done by name lookup, reflection or dynamic
class loading rather than by an explicit closed table, an attacker who can
influence that value chooses which class gets instantiated, which is a class of
deserialisation vulnerability with a long history in Java and Python. The fix is
the same explicit table that dimension 11 recommends for correctness. A closed
mapping, an unknown value rejected loudly, and no reflection anywhere near it.
The correctness fix and the security fix are the same fix, which is a reason to
prioritise it.

**A client-supplied state is a privilege escalation.** Any design that accepts
the current state from outside, in a request body, a hidden form field, a JWT
claim that is not verified, or a resumable-workflow token, lets a caller declare
itself to be in a state it never reached. The observable symptom is an operation
succeeding that the user interface never offered. State must be derived from the
server's record of transitions taken, never from what the caller says it is. Where
a resumption token is unavoidable, sign it and bind it to the record and the
principal.

**Extension points and untrusted states.** Where an application can register its
own ConcreteState into a library's machine, that state runs inside the library's
event loop with the library's privileges and can install any successor it likes,
including one that skips a validation state. If states are pluggable, validate
that a registered state's declared transitions lie within the permitted graph
rather than trusting the object, and reject a registration that would introduce
an edge the machine's owner did not declare.

On privacy the pattern is neutral in itself, with one practical caveat that
follows from dimension 16. State names are recommended as metric labels and log
fields, and in some domains a state name is sensitive. States named
`AWAITING_MEDICAL_REVIEW`, `SANCTIONS_HOLD` or `DECEASED` reveal a fact about a
person to anyone with dashboard access. A per-state gauge with few label values
per tenant can also be a disclosure channel. Where a state name carries that
meaning, treat the label as attributable data under the same retention and access
rules as any other identifier, or map to an opaque code for external telemetry
while keeping the readable name in access-controlled logs.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 5, Behavioral Patterns, section State. Source of
   the pattern's intent, the Objects for States alias, the three participants,
   the TCPConnection worked example, and the Flyweight and Singleton
   relationships. Page numbers are not cited because they were not verified
   against a copy of the book during authoring.
2. Wikipedia contributors. "State pattern".
   https://en.wikipedia.org/wiki/State_pattern
   Verified 2026-08-02. Used to confirm the wording of the GoF intent, the two
   problems the pattern addresses, the `setState` callback structure in the
   sequence diagram, and the observation that the pattern can be read as a
   Strategy whose strategy switches itself.
3. David Harel. "Statecharts. A visual formalism for complex systems". *Science
   of Computer Programming*, volume 8, 1987, pages 231 to 274.
   https://www.sciencedirect.com/science/article/pii/0167642387900359
   Verified 2026-08-02. Source for the statechart formalism and the three
   extensions of hierarchy, concurrency and communication. The publisher page
   was reachable through search indexing but returned HTTP 403 to direct
   retrieval, so the bibliographic details were confirmed from the ScienceDirect
   record and the Weizmann Institute publication listing rather than from the
   article text.
4. World Wide Web Consortium. *State Chart XML (SCXML). State Machine Notation
   for Control Abstraction*. W3C Recommendation, 1 September 2015.
   https://www.w3.org/TR/scxml/
   Verified 2026-08-02. Source for the SCXML abstract wording and its lineage
   from CCXML and Harel State Tables.
5. Object Management Group. *Unified Modeling Language*, version 2.5.1, OMG
   document formal/17-12-05, December 2017.
   https://www.omg.org/spec/UML/
   Verified 2026-08-02. Source for the current formal UML version and document
   number. The specification PDF itself exceeded the retrieval size limit during
   authoring, so no section or page of the PDF is cited.
6. uml-diagrams.org. "UML State Machine Diagrams".
   https://www.uml-diagrams.org/state-machine-diagrams.html
   Verified 2026-08-02. Secondary source for the distinction between behavioral
   and protocol state machines and for the description of UML behavioral state
   machines as an object-based variant of Harel statecharts.
7. Internet Engineering Task Force. RFC 9293, *Transmission Control Protocol*,
   August 2022. https://www.rfc-editor.org/rfc/rfc9293.html
   Verified 2026-08-02. Source for the eleven TCP connection states and the
   state diagram in section 3.3.2, figure 5.
8. Ericsson and the Erlang/OTP team. *Erlang/OTP stdlib documentation*,
   `gen_statem`. https://www.erlang.org/doc/apps/stdlib/gen_statem.html
   Verified 2026-08-02. Source for the `state_functions` and
   `handle_event_function` callback modes, the `{next_state, NextState, NewData}`
   return shape, and the `keep_state` versus `repeat_state` distinction.
9. Lightbend and the Akka team. *Akka documentation*, Behaviors as finite state
   machines. https://doc.akka.io/libraries/akka-core/current/typed/fsm.html
   Verified 2026-08-02. Source for the state-as-`Behavior` model and the named
   `Behaviors.receiveMessage`, `Behaviors.withTimers`, `Behaviors.unhandled` and
   `Behaviors.ignore` constructors.
10. Broadcom and the Spring team. *Spring Statemachine reference documentation*.
    https://docs.spring.io/spring-statemachine/docs/current/reference/
    Verified 2026-08-02. Source for hierarchical states, regions, guards,
    actions, triggers, extended state, pseudostates, and the
    `withExternal().source().target().event()` transition declaration form.
11. Andreas Huber Dönni. *Boost.Statechart documentation*.
    https://www.boost.org/doc/libs/release/libs/statechart/doc/index.html
    Verified 2026-08-02. Source for the C++ UML-statechart library, its author,
    and its support for hierarchical states, orthogonal states, entry and exit
    actions, guards, history and event deferral.
12. Stately. *XState documentation*, State machines and statecharts.
    https://stately.ai/docs/state-machines-and-statecharts
    Verified 2026-08-02. Source for XState's core concepts of states,
    transitions and events, and for its support of hierarchy, parallel states
    and actor-model communication.
13. Amazon Web Services. *AWS Step Functions Developer Guide*, Discovering
    workflow states.
    https://docs.aws.amazon.com/step-functions/latest/dg/concepts-states.html
    Verified 2026-08-02. Source for the Amazon States Language `Type` and `Next`
    fields and the eight state types.
14. The Rust Project. *The Rust Programming Language*, chapter 18,
    Object-Oriented Design Pattern Implementations.
    https://doc.rust-lang.org/book/ch18-03-oo-design-patterns.html
    Verified 2026-08-02. Source for the Draft, PendingReview and Published
    worked example, the quoted downside that states which implement transitions
    become coupled to each other, and the argument that encoding states as types
    makes invalid states impossible at compile time.
15. statecharts.dev. "State machine state explosion".
    https://statecharts.dev/state-machine-state-explosion.html
    Verified 2026-08-02. Source for the state explosion description, the worked
    two-to-four-to-eight state progression with twelve transitions, and the
    hierarchy-based remedy.
16. Apple. *The Swift Programming Language*, Initialization.
    https://docs.swift.org/swift-book/documentation/the-swift-programming-language/initialization/
    Verified 2026-08-02. Source for two-phase initialisation and the safety check
    that an initializer cannot call an instance method, read an instance property
    or refer to `self` before phase one of initialisation completes. Cited in
    dimension 7 to correct the common assumption that the constructor
    virtual-call hazard applies uniformly across object-oriented languages.

### Claims deliberately not made

Three things a reader might expect here are absent because they could not be
verified during authoring on 2026-08-02, and asserting them would be worse than
omitting them.

- No page numbers are cited for the GoF book. The chapter and section are cited
  because they are stable and well established, but no page was confirmed against
  a copy.
- No direct quotation is taken from the GoF book's Implementation section on who
  defines the state transitions. The trade-off is instead argued from the
  Wikipedia structural description of `setState`, from the Rust book's explicit
  statement about inter-state coupling, and from the observable design choices of
  Spring Statemachine, SCXML and Amazon States Language.
- No claim is made about which UML 2.5.1 chapter covers state machines. The
  specification PDF exceeded the retrieval size limit, and the version and
  document number are cited from the OMG specification page instead.

## Code examples

Four languages, chosen because each shows a different genuine face of the
pattern. TypeScript shows the classical object form with the successor returned.
Python shows the shared, stateless flyweight form that is the common shape in
practice, and the paired transition table. Go shows the interface form plus the
table variant that Go culture tends to prefer. Rust shows both the trait-object
form and the typestate form, which is the comparison the Rust book draws.

Java and Kotlin are omitted here, not because the pattern is unidiomatic in them,
which it is not, but because the shape is the same as the TypeScript example with
more ceremony, and no Java or Kotlin toolchain was available to compile a sample
on the authoring machine. Saying so is better than shipping unverified code.

All four samples below were compiled and executed on 2026-08-02. TypeScript with
`tsc --strict --target es2020` then `node`. Python 3.14. Go via `go run`. Rust
with `rustc --edition 2021`. The Rust sample includes both forms in one file.

The domain is deliberately trivial so the structure is visible. A vending slot
that is either idle or paid.

### TypeScript

The classical form. Each state returns its successor, and the Context performs
the single assignment.

```typescript
interface State {
  readonly name: string;
  coin(ctx: Machine): State;
  dispense(ctx: Machine): [State, boolean];
}

const Idle: State = {
  name: "idle",
  coin(ctx) {
    ctx.coins += 1;
    return Paid;
  },
  dispense() {
    return [Idle, false];
  },
};

const Paid: State = {
  name: "paid",
  coin(ctx) {
    ctx.refunded += 1;
    return Paid;
  },
  dispense(ctx) {
    ctx.served += 1;
    return [Idle, true];
  },
};

class Machine {
  private state: State = Idle;
  coins = 0;
  refunded = 0;
  served = 0;

  get currentName(): string {
    return this.state.name;
  }

  coin(): void {
    this.state = this.state.coin(this);
  }

  dispense(): boolean {
    const [next, served] = this.state.dispense(this);
    this.state = next;
    return served;
  }
}

type Name = "idle" | "paid";
type Signal = "coin" | "dispense" | "refund";

const table: Record<Name, Partial<Record<Signal, Name>>> = {
  idle: { coin: "paid" },
  paid: { dispense: "idle", refund: "idle" },
};

function step(current: Name, signal: Signal): [Name, boolean] {
  const next = table[current][signal];
  return next === undefined ? [current, false] : [next, true];
}

const m = new Machine();
console.log(m.currentName, m.dispense());
m.coin();
console.log(m.currentName, m.dispense());
console.log(m.currentName, m.coins, m.served);
console.log(step("idle", "coin"), step("idle", "dispense"));
```

The `table` and `step` above are the Context-owned variant shown side by side.
Note that the union types make an undeclared transition a compile error at the
call site, which is the property the object form does not give you.

Observed output.

```
idle false
paid true
idle 1 1
[ 'paid', true ] [ 'idle', false ]
```

### Python

The shared flyweight form. `IDLE` and `PAID` are single module-level instances
reused by every Machine, which is why every method takes the Context.

```python
from __future__ import annotations
from typing import Protocol


class State(Protocol):
    name: str

    def coin(self, ctx: Machine) -> State: ...
    def dispense(self, ctx: Machine) -> tuple[State, bool]: ...


class Idle:
    name = "idle"

    def coin(self, ctx: Machine) -> State:
        ctx.coins += 1
        return PAID

    def dispense(self, ctx: Machine) -> tuple[State, bool]:
        return self, False


class Paid:
    name = "paid"

    def coin(self, ctx: Machine) -> State:
        ctx.refunded += 1
        return self

    def dispense(self, ctx: Machine) -> tuple[State, bool]:
        ctx.served += 1
        return IDLE, True


IDLE: State = Idle()
PAID: State = Paid()


class Machine:
    def __init__(self) -> None:
        self.state: State = IDLE
        self.coins = 0
        self.refunded = 0
        self.served = 0

    def coin(self) -> None:
        self.state = self.state.coin(self)

    def dispense(self) -> bool:
        self.state, served = self.state.dispense(self)
        return served


TABLE = {
    ("idle", "coin"): "paid",
    ("paid", "dispense"): "idle",
    ("paid", "refund"): "idle",
}


def step(current: str, signal: str) -> tuple[str, bool]:
    nxt = TABLE.get((current, signal))
    return (current, False) if nxt is None else (nxt, True)


if __name__ == "__main__":
    m = Machine()
    print(m.state.name, m.dispense())
    m.coin()
    print(m.state.name, m.dispense())
    print(m.state.name, m.coins, m.served)
    print(step("idle", "coin"), step("idle", "dispense"))
```

The `name` attribute is the persistence discriminator from dimension 11, written
by hand so that renaming the class does not break stored records.

Observed output.

```
idle False
paid True
idle 1 1
('paid', True) ('idle', False)
```

### Go

Interfaces with no inheritance, which is the shape Go pushes you toward anyway.
The `table` at the bottom is the same machine expressed as data.

```go
package main

import "fmt"

type State interface {
	Coin(m *Machine) State
	Dispense(m *Machine) (State, bool)
	Name() string
}

type idle struct{}
type paid struct{}

func (i idle) Coin(m *Machine) State             { m.Coins++; return paid{} }
func (i idle) Dispense(m *Machine) (State, bool) { return i, false }
func (i idle) Name() string                      { return "idle" }
func (p paid) Coin(m *Machine) State             { m.Refunded++; return p }
func (p paid) Dispense(m *Machine) (State, bool) { return idle{}, true }
func (p paid) Name() string                      { return "paid" }

type Machine struct {
	state    State
	Coins    int
	Refunded int
}

func New() *Machine { return &Machine{state: idle{}} }

func (m *Machine) Coin() { m.state = m.state.Coin(m) }

func (m *Machine) Dispense() bool {
	next, served := m.state.Dispense(m)
	m.state = next
	return served
}

func (m *Machine) Name() string { return m.state.Name() }

type Event string

var table = map[string]map[Event]string{
	"idle": {"coin": "paid"},
	"paid": {"dispense": "idle", "refund": "idle"},
}

func step(current string, e Event) (string, bool) {
	next, ok := table[current][e]
	if !ok {
		return current, false
	}
	return next, true
}

func main() {
	m := New()
	fmt.Println(m.Name(), m.Dispense())
	m.Coin()
	fmt.Println(m.Name(), m.Dispense())
	fmt.Println(m.Name(), m.Coins)

	s := "idle"
	s, _ = step(s, "coin")
	s, ok := step(s, "coin")
	fmt.Println(s, ok)
}
```

Observed output. The final `false` is a rejected transition, the event that
dimension 16 says to count rather than ignore.

```
idle false
paid true
idle 1
paid false
```

### Rust

Both forms in one file. The trait-object form uses `self: Box<Self>` so a state
consumes itself and returns its successor, which is how ownership expresses a
transition. The typestate form below it deletes the runtime check entirely.

```rust
trait State {
    fn coin(self: Box<Self>) -> Box<dyn State>;
    fn dispense(self: Box<Self>) -> (Box<dyn State>, bool);
    fn name(&self) -> &'static str;
}

struct Idle;
struct Paid;

impl State for Idle {
    fn coin(self: Box<Self>) -> Box<dyn State> { Box::new(Paid) }
    fn dispense(self: Box<Self>) -> (Box<dyn State>, bool) { (self, false) }
    fn name(&self) -> &'static str { "idle" }
}

impl State for Paid {
    fn coin(self: Box<Self>) -> Box<dyn State> { self }
    fn dispense(self: Box<Self>) -> (Box<dyn State>, bool) { (Box::new(Idle), true) }
    fn name(&self) -> &'static str { "paid" }
}

struct Machine { state: Option<Box<dyn State>> }

impl Machine {
    fn new() -> Self { Machine { state: Some(Box::new(Idle)) } }

    fn coin(&mut self) {
        if let Some(s) = self.state.take() {
            self.state = Some(s.coin());
        }
    }

    fn dispense(&mut self) -> bool {
        match self.state.take() {
            Some(s) => {
                let (next, served) = s.dispense();
                self.state = Some(next);
                served
            }
            None => false,
        }
    }

    fn name(&self) -> &'static str {
        self.state.as_ref().map(|s| s.name()).unwrap_or("poisoned")
    }
}

struct Empty;
struct Funded;

impl Empty { fn coin(self) -> Funded { Funded } }
impl Funded { fn dispense(self) -> Empty { Empty } }

fn main() {
    let mut m = Machine::new();
    println!("{} {}", m.name(), m.dispense());
    m.coin();
    println!("{} {}", m.name(), m.dispense());
    println!("{}", m.name());

    let slot = Empty;
    let slot = slot.coin();
    let _slot = slot.dispense();
}
```

Two things worth reading closely. The `Option` wrapper on `state` exists because
`self: Box<Self>` consumes the state, so the Machine must surrender ownership to
call it and take it back afterwards. The `take()` leaves a window in which the
Machine has no state, which is why `name()` has a `"poisoned"` arm. That window
is the ownership-level expression of the torn-transition hazard from dimension
11, and it is the price of the consuming signature.

In the typestate half, `Empty` has no `dispense` method, so writing
`Empty.dispense()` does not compile. There is no runtime check because there is
nothing to check.

Observed output.

```
idle false
paid true
idle
```
