---
name: State Machine Workflow
slug: state-machine-workflow
family: 23-workflow-orchestration
category: workflow orchestration
aliases: [Finite State Machine, Statechart, Explicit State Modeling]
first_described: "Mealy machines, George H. Mealy, 1955. Moore machines, Edward F. Moore, 1956. Extended with hierarchy and orthogonal regions by David Harel's Statecharts, 1987. Given an object-oriented implementation shape by the Gang of Four's State design pattern, 1994"
maturity: canonical
related: [state, saga, choreography, workflow-engine, orchestrator-worker]
incompatible_with: []
verified: 2026-08-22
---

# State Machine Workflow

## 1. Name, aliases, and lineage

State Machine Workflow is the pattern of modeling a process or an entity's lifecycle
explicitly as a finite set of named states, connected by guarded transitions that fire on
events, rather than scattering `if (status == "x")` checks across a codebase. It is the
broader, foundational pattern that a full durable-execution runtime often implements
underneath, and it applies just as well with no runtime at all, a status column in a
database, a hand-rolled enum and switch, or a small library running entirely in one
process.

Two distinct lineages feed this pattern, and this entry keeps them separate.

The mathematical model traces to two 1950s papers. George H. Mealy's 1955 paper "A
Method for Synthesizing Sequential Circuits" (Bell System Technical Journal, Vol. 34,
Issue 5, pp. 1045 to 1079) defines a machine whose output depends on both the current
state and the current input. Edward F. Moore's 1956 paper "Gedanken-experiments on
Sequential Machines" (Automata Studies, Annals of Mathematics Studies 34, Princeton
University Press, pp. 129 to 153) defines a machine whose output depends only on the
current state ([Wikipedia, Mealy
machine](https://en.wikipedia.org/wiki/Mealy_machine); [Wikipedia, Moore
machine](https://en.wikipedia.org/wiki/Moore_machine), verified 2026-08-22). The 1956
volume containing Moore's paper brought together Claude Shannon, W. Ross Ashby, John von
Neumann, Marvin Minsky, and Stephen Cole Kleene, and automata theory "emerged as a
relatively autonomous discipline" that same year, alongside Noam Chomsky's description
of the Chomsky hierarchy ([Wikipedia, Automata
theory](https://en.wikipedia.org/wiki/Automata_theory), verified 2026-08-22). A
deterministic finite-state machine is formally the quintuple (Sigma, S, s0, delta, F),
an input alphabet, a finite set of states, an initial state, a transition function, and
a set of accepting states ([Wikipedia,
Finite-state machine](https://en.wikipedia.org/wiki/Finite-state_machine), verified
2026-08-22).

David Harel extended the flat automaton with hierarchy, orthogonality, and broadcast
communication in "Statecharts. A Visual Formalism for Complex Systems" (Science of
Computer Programming, 8(3):231 to 274, 1987, DOI 10.1016/0167-6423(87)90035-9),
cross-checked against DBLP record `journals/scp/Harel87`. UML State Machine is "an
object-based variant of Harel statechart, adapted and extended by UML," built "to
overcome the main limitations of traditional finite-state machines while retaining
their main benefits," and it combines both the Mealy style (event-triggered transition
actions) and the Moore style (state entry and exit actions) at once ([Wikipedia, UML
state machine](https://en.wikipedia.org/wiki/UML_state_machine), verified 2026-08-22).

The separate, object-oriented implementation lineage is the Gang of Four's **State**
design pattern, from Gamma, Helm, Johnson, and Vlissides, *Design Patterns. Elements of
Reusable Object-Oriented Software* (Addison-Wesley, 1994), a Behavioral pattern that
"allows an object to alter its behavior when its internal state changes," implemented
by delegating from a `Context` object to a `State` interface and its `ConcreteState`
classes ([Wikipedia, State
pattern](https://en.wikipedia.org/wiki/State_pattern), verified 2026-08-22). This is
the entry catalogued separately at [`patterns/01-design-patterns-gof/state.md`], and
it is the object-oriented vocabulary a hand-rolled implementation reaches for. State
Machine Workflow, this entry, is the broader pattern the GoF State pattern is one way
to implement.

The modern software-engineering framing bridges the mathematical model to a business
entity's lifecycle. XState's own documentation states, under its "in the backend"
guidance, that the goal is to "simplify the design and implementation of complex
workflows" ([stately.ai, State machines and
statecharts](https://stately.ai/docs/state-machines-and-statecharts), verified
2026-08-22). Automata theory asks whether a machine accepts a formal language over an
alphabet. The workflow framing repurposes the identical states-and-transitions
machinery to answer a different question, did this order correctly reach `shipped`, not
whether a string is accepted.

## 2. Problem and context

Spring Statemachine's own reference documentation states the origin story for this
pattern in its Background section directly.

> "State machines are powerful because their behavior is always guaranteed to be
> consistent and relatively easily debugged due to how operational rules are written in
> stone when a machine is started."

The same page names the code smell this pattern replaces.

> "Traditionally, state machines are added to an existing project when developers
> realize that the code base is starting to look like a plate full of spaghetti.
> Spaghetti code looks like a never ending, hierarchical structure of IF, ELSE, and
> BREAK clauses, and compilers should probably ask developers to go home when things
> are starting to look too complex."

And its Usage Scenarios section names the exact signal that a codebase already needs
this pattern, whether or not it has one, framed as a single flowing statement rather
than a bulleted list.

> "You are already trying to implement a state machine when you use boolean flags or
> enums to model situations, have variables that have meaning only for some part of
> your application lifecycle, or loop through an if-else structure (or, worse,
> multiple such structures), check whether a particular flag or enum is set, and then
> make further exceptions about what to do when certain combinations of your flags and
> enums exist or do not exist."

([docs.spring.io, Spring Statemachine
reference](https://docs.spring.io/spring-statemachine/docs/current/reference/), verified
2026-08-22). A community reference site, statecharts.dev, makes the same point from a
different angle, stating plainly that most codebases are already coding state machines,
just with the states hidden inside ordinary conditional logic rather than declared
anywhere ([statecharts.dev](https://statecharts.dev/), verified 2026-08-22, treated as
a secondary source, not a vendor document).

A real system whose own public documentation frames its domain this way, rather than as
an implicit boolean, is Stripe's subscription lifecycle, which names an explicit,
finite set of status values and their transition triggers rather than an `is_active`
flag ([docs.stripe.com, Subscriptions
overview](https://docs.stripe.com/billing/subscriptions/overview), verified 2026-08-22,
full detail in dimension 9).

## 3. Forces

**Explicitness against setup cost.** The clearest sourced statement of the cost of
adopting the pattern too early, rather than the cost of not adopting it, comes from a
paraphrase of the GoF Applicability section, "Applying the pattern can be overkill if a
state machine has only a few states or rarely changes"
([refactoring.guru, State](https://refactoring.guru/design-patterns/state), verified
2026-08-22, a secondary source paraphrasing the book, since the original text was not
independently fetched this pass).

**Runtime versus compile-time exhaustiveness.** XState's own documentation describes a
guard as "a condition function that the machine checks when it goes through an event,"
requiring guards to be "pure, synchronous functions that return either `true` or
`false`," which is unambiguously a runtime check
([stately.ai, Guards](https://stately.ai/docs/guards), verified 2026-08-22). Whether a
typed enum with an exhaustive `switch` or `match` in a statically typed language (Rust,
Swift, TypeScript's discriminated unions) catches a missing transition at compile time
instead is common practice, but this pass did not find a primary source confirming that
XState's own TypeScript integration provides that guarantee, so it is marked here as
unconfirmed rather than asserted.

**Hierarchical and orthogonal states against a flat machine.** XState's own guidance is
explicit about when to introduce nesting. "Begin with a flat state structure and only
introduce parent states when patterns emerge," and to "avoid premature abstraction,"
refactoring "to parent states when you notice repeated patterns or common behaviors."
It says to skip nesting "when states don't share any common behavior or transitions" or
"when the hierarchy would make the state machine more complex without adding value"
([stately.ai, Parent states](https://stately.ai/docs/parent-states), verified
2026-08-22). The quantified reason nesting matters is a cartesian-product growth in a
flat machine, statecharts.dev walks it with numbers, two states (valid and invalid),
add an independent enabled and disabled axis and the count becomes four (2x2), add a
third independent axis and it becomes eight (2x2x2). Orthogonal regions avoid the
multiplication, "adding more regions does not cause an explosion of states; the
statechart grows more or less linearly"
([statecharts.dev, State explosion](https://statecharts.dev/state-machine-state-explosion.html),
verified 2026-08-22).

**Persistence, the exact boundary with the Workflow Engine pattern.** XState's own
persistence documentation lists why a machine's snapshot needs to be saved and
restored, "maintaining state across browser reloads" on the client, and on a backend,
that a machine can "span multiple requests," "survive service restarts," "be fault
tolerant," "represent long-running processes," and "be auditable and traceable"
([stately.ai, Persistence](https://stately.ai/docs/persistence), verified 2026-08-22).
This is a state-machine library's own documentation describing exactly the
requirements a durable-execution runtime exists to satisfy at scale and reliably. AWS
makes the identity between the two patterns explicit at the product level, cited here
narrowly for this one framing point, never for its full state machine structure, which
belongs to the sibling `workflow-engine` entry. AWS states, "With AWS Step Functions,
you can create workflows, also called State machines," and separately, "Step Functions
is based on state machines and tasks. In Step Functions, state machines are called
workflows, which are a series of event-driven steps. Each step in a workflow is called
a state."
([docs.aws.amazon.com, What is Step
Functions](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html), verified
2026-08-22).

## 4. Applicability and non-applicability

**Reach for an explicit state machine when.**

- A class or object's behavior changes with an internal condition, the number of
  distinct behaviors is large, and that condition-specific code changes often. The GoF
  Applicability guidance, as paraphrased, "Use the State pattern when you have an
  object that behaves differently depending on its current state, the number of states
  is enormous, and the state-specific code changes frequently"
  ([refactoring.guru, State](https://refactoring.guru/design-patterns/state), verified
  2026-08-22).
- The Spring Statemachine signal from dimension 2 already applies, a boolean flag or
  enum stands in for a real lifecycle, or an if-else chain checks combinations of flags.
- The domain is one of the good-fit categories a real system already models this way,
  see dimension 9, a subscription or payment lifecycle, a network or telephony
  connection lifecycle, a CI or CD pipeline run, a document or change approval flow, a
  UI component with distinct interactive modes, or a game character's behavior modes.

**Do not reach for it when.**

- The state machine would have only a few states that rarely change, per the GoF
  caveat above, the machinery costs more than the clarity it buys.
- Nesting is being added where states share no behavior and no transitions, per XState's
  own guidance, that adds complexity with nothing to show for it.
- Worth stating honestly, this pass found no sourced statement naming "a purely linear
  pipeline of independent steps with no real lifecycle" as a poor fit for this specific
  pattern. The claim is plausible and consistent with the good-fit sources above, but it
  is this entry's own reasoning, not an independently sourced claim.

## 5. Structure

Cross-checking XState, Spring Statemachine, and UML against each other confirms this
vocabulary is standard, not idiosyncratic to one library.

| Term | Definition | Source |
|---|---|---|
| State | An element of the finite, non-empty set S | Wikipedia, Finite-state machine |
| Transition | "A change from one finite state to another, triggered by an event" | XState docs, Transitions |
| Event | "A signal, trigger, or message that causes a transition" | XState docs, Transitions |
| Enabled transitions | "Only the active finite states are checked to see if any of them have a transition for that event. Those transitions are called enabled transitions" | XState docs, Transitions |
| Guard | "A condition function that the machine checks when it goes through an event," must be a "pure, synchronous function that returns either true or false" | XState docs, Guards |
| Guard, cross-checked | "You can use the `Guard` interface to do an evaluation where a method has access to a `StateContext`" | Spring Statemachine docs |
| Entry action | "Actions that occur on any transition that enters a state node" | XState docs, Actions |
| Exit action | "Actions that occur on any transition that exits a state node" | XState docs, Actions |
| Entry and exit action, cross-checked | `.state(States.S1, action(), null)` for entry, `.state(States.S2, null, action())` for exit | Spring Statemachine docs |
| Initial state | s0, the designated starting element of S | Wikipedia, Finite-state machine; usage confirmed in XState's initial-state configuration field |
| Final state | "A final state is a state that represents the completion or successful termination of a machine," set by a final type on the state node, and once reached "it can no longer receive any events" | XState docs, Final states |
| Composite or parent state | "States can contain more states, also known as child states. These child states are only active when the parent state is active" | XState docs, Parent states |
| Composite state, UML term | "Hierarchically nested states, substates can be contained within superstates, enabling behavior reuse" | Wikipedia, UML state machine |
| Orthogonal or parallel regions | "A parallel state is a state that has multiple child states, also known as regions, that are all active at the same time" | XState docs, Parallel states |
| Orthogonal regions, UML term | "Independent, concurrent regions within a composite state" | Wikipedia, UML state machine |
| Internal transition | "Event processing without state changes" | Wikipedia, UML state machine |
| Internal transition, cross-checked | The transition configurer "supports three types, external, internal, and local" | Spring Statemachine docs |
| Context, State interface, ConcreteState | The separate GoF/OOP vocabulary, a `Context` object that delegates to a `State` interface implemented by `ConcreteState` classes | Wikipedia, State pattern |

Spring Statemachine names a third transition kind, `local`, beyond UML's external and
internal, without an independent definition found this pass, noted honestly rather than
guessed at.

## 6. ASCII structure diagram

```
                       event + guard
   +-----------+  passes  +-----------+  event + guard
   |  State A  | -------> |  State B  | -------> passes to State C
   +-----------+          +-----------+
   exit action A  ->  transition action  ->  entry action B

   Nested (parent) state:
   +-----------------------------------+
   |  Parent State                     |
   |  +-------------+   +------------+ |
   |  | Child State1| ->| ChildState2| |
   |  +-------------+   +------------+ |
   +-----------------------------------+

   Orthogonal (parallel) regions:
   +---------------------------------------------+
   | Region 1: [Idle] -> [Loading] -> [Loaded]    |
   | Region 2: [Muted] -> [Unmuted]                |
   +---------------------------------------------+
   both regions are active at once, independently
```

## 7. Dynamics

```
1. An event arrives while the machine is in its current state (or set of active
   states, if orthogonal regions or nesting are in play).
2. The machine finds the enabled transitions for that event in the currently
   active state(s).
3. Each enabled transition's guard is evaluated. Only a transition whose guard
   returns true (or has no guard) can fire.
4. If more than one guarded transition could fire, the machine picks by a
   defined priority (implementation-specific, commonly declaration order).
5. The exit action of the source state runs.
6. The transition's own action runs.
7. The entry action of the target state runs.
8. The current state is updated to the target state.
9. If the machine persists its snapshot (dimension 3, and the Workflow Engine
   sibling entry), the new state and any extended-state context are written to
   storage before the machine is considered to have moved on.
```

## 8. Implementation variants

**XState (JavaScript and TypeScript).** A machine is built with `createMachine(config)`.
Data that travels alongside the finite control state, XState's `context`, "is how you
store data in a state machine actor," is immutable from the outside, and is updated only
through the `assign()` action, the classic extended-state-machine shape, finite control
states plus a data bag ([stately.ai,
Context](https://stately.ai/docs/context), verified 2026-08-22). A running instance is
described as "a running instance of the machine," and many independent actors can run
off one machine definition, created via `createActor(machine)`. This actor layer is how
XState composes multiple machines, parent and child, spawned actors, rather than one
monolithic machine ([stately.ai,
Actors](https://stately.ai/docs/actors), verified 2026-08-22). XState's older, v4-era
documentation states compatibility with the W3C's SCXML specification, mapping XState's
own event-target map, its `cond` guards, and its `invoke` field to SCXML's own
`<transition>`, conditional expressions, and `<invoke>` ([xstate.js.org,
SCXML](https://xstate.js.org/docs/guides/scxml.html), verified 2026-08-22). This pass
could not confirm whether the current v5/v6 documentation still makes the same claim,
so the claim is presented as historically confirmed for the v4 era and unconfirmed for
the current version. SCXML itself, "State Chart extensible Markup Language," is a W3C
Recommendation published September 1, 2015, still standing (not superseded), described
by the W3C as "a generic state-machine based execution environment based on CCXML and
Harel State Tables" ([w3.org, SCXML](https://www.w3.org/TR/scxml/), verified 2026-08-22).

**Spring Statemachine (Java).** A machine can be built outside Spring configuration via
`StateMachineBuilder.builder()`, with `configureStates()`, `configureTransitions()`,
and `configureConfiguration()` called individually, "cannot be chained together." Guards
are `Guard<S,E>` beans or SpEL expressions, `.guard(guard())` on a transition, and a
reactive variant `ReactiveGuard<S,E>` exists. Actions wire to transitions or to state
entry and exit, with dedicated error handlers, `.action(action(), errorAction())`, and a
`ReactiveAction<S,E>` for non-blocking work. Orthogonal states are called regions,
declared with multiple `.parent(...).region("R1")` blocks, each with its own initial and
end states, and a region can carry an explicit ID "for better persistence and reset
management." Persistence runs through a `StateMachinePersister<S,E,T>` interface
(`persist`/`restore`) with a `StateMachineContext` snapshot type, and backends for
Redis, JPA, MongoDB, and ZooKeeper
([docs.spring.io, Spring Statemachine
reference](https://docs.spring.io/spring-statemachine/docs/current/reference/), verified
2026-08-22). As of this verification, the last released version was **4.0.2** (June 11,
2026), and the GitHub repository carries a formal archival notice, "This repository was
archived by the owner on Jul 5, 2026. It is now read-only," with the README itself
stating "Spring Statemachine is no longer maintained"
([github.com, spring-statemachine](https://github.com/spring-projects/spring-statemachine),
verified 2026-08-22). Anyone choosing this library going forward should weigh that
directly, and see dimension 17 for what 4.0.2's own release covered.

**Rails and Ruby, AASM.** The AASM gem "provides AASM, a library for adding finite
state machines to Ruby classes," supporting plain Ruby objects, ActiveRecord, Mongoid,
NoBrainer, and Dynamoid. A state is declared by name with an optional initial flag, and
an event is declared with a block naming the states it transitions from and to. AASM
auto-generates predicate and trigger methods per state and event (`job.sleeping?`,
`job.may_run?`, `job.run`). Guards attach to an event by naming a predicate method,
chainable, with `if`/`unless` alternatives, and callbacks include `before_enter`,
`after_exit`, `before_all_transitions`, and `after_commit`
([github.com, aasm/aasm](https://github.com/aasm/aasm), verified 2026-08-22, an
actively maintained project as of this verification).

**Python, the `transitions` library.** Self-described as "a lightweight,
object-oriented finite state machine implementation in Python with many extensions,"
supporting Python 2.7 and 3.0 or newer. States accept `on_exit`/`on_enter` callbacks per
state, transitions are a declarative dict table (`trigger`, `source`, `dest`), guards
use a `conditions` parameter (and an inverted `unless`), and callbacks include
`before`/`after`/`prepare` per transition plus machine-wide `before_state_change` and
`after_state_change`. A `HierarchicalMachine` subclass supports nested states and
`parallel` regions for simultaneous sub-states, the direct analogue of Harel's
orthogonal regions and SCXML's `<parallel>`
([github.com, pytransitions/transitions](https://github.com/pytransitions/transitions),
verified 2026-08-22).

**.NET, Stateless.** Self-described as "a simple library for creating state machines in
C# code." Configuration is fluent, `sm.Configure(State.OffHook).Permit(Trigger.CallDialled,
State.Ringing)`, guards use `PermitIf(trigger, state, () => condition)` with an async
`PermitIfAsync`. Persistence is bring-your-own, the constructor accepts external
state-read and state-write functions so a caller can back the current state with an ORM
field or a bound property, a lighter shape than Spring Statemachine's dedicated
persister interface. It remains "single-threaded and non-concurrent" internally even
with its `FireAsync()` async support ([github.com,
dotnet-state-machine/stateless](https://github.com/dotnet-state-machine/stateless),
verified 2026-08-22, an actively maintained project as of this verification).

**The bridge to Workflow Engine.** Two durable-execution vendors implement this pattern
underneath their own product. AWS's own product-level identity was already quoted in
dimension 3, its execution model literally is a persisted state machine. Azure Durable
Functions frames the same mechanics through event sourcing rather than the words "state
machine." Its orchestrator function, on a restart, "wakes up and re-executes the entire
function from the start to rebuild the local state," a process the docs call replay
([learn.microsoft.com, Durable
orchestrations](https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-orchestrations),
verified 2026-08-22, this pass found no Microsoft-authored sentence using the literal
words "state machine" for orchestrator functions, so the connection is presented as
architecturally sound but the vendor's own preferred vocabulary differs from AWS's).
Neither vendor's own structural mechanics (Amazon States Language state types, Azure's
determinism constraints) are re-derived here, both belong to the sibling
`workflow-engine` entry.

## 9. Known production uses

1. **Stripe Subscriptions.** Stripe's own subscriptions documentation names a finite
   `status` field with values `trialing`, `active`, `incomplete`, `incomplete_expired`,
   `past_due`, `canceled`, `unpaid`, and `paused`. Documented transitions, "The
   subscription automatically transitions to `active` status once a customer makes
   their first payment" (from `trialing`); an initial `incomplete` subscription becomes
   `active` if paid within 23 hours, or "If the customer does not pay within 23 hours,
   the subscription is set to `incomplete_expired`"; from `past_due`, "If, after all
   attempted Smart Retries, the invoice remains unpaid, you can configure the
   subscription to transition to `canceled` or `unpaid`, or to remain in `past_due`
   status." `canceled` is explicitly documented as a terminal state, "This is a final
   status that cannot be updated." Transitions are event-driven and observable through
   webhooks named `invoice.paid`, `invoice.payment_failed`, and
   `invoice.payment_action_required`
   ([docs.stripe.com, Subscriptions
   overview](https://docs.stripe.com/billing/subscriptions/overview), verified
   2026-08-22, page content fetched in German, quotes translated back to English for
   this entry, the API status values themselves are English identifiers).
2. **GitHub Actions workflow runs.** A run's `status` takes values `queued`,
   `in_progress`, `completed`, `pending`, `waiting`, or `requested`, with the note
   "Only GitHub Actions can set a status of waiting, pending, or requested." A second,
   independent axis, `conclusion`, is populated once `status` reaches `completed`, with
   values `success`, `failure`, `neutral`, `cancelled`, `skipped`, `timed_out`,
   `action_required`, or `stale`
   ([docs.github.com, Workflow
   runs](https://docs.github.com/en/rest/actions/workflow-runs), verified 2026-08-22).
   The two-axis shape, a coarse progress axis plus a finer terminal-outcome axis, is a
   real, distinct structural choice worth naming against Stripe's single flat `status`
   field.
3. **GitHub Pull Requests.** State is "either open or closed," with a separate
   `"merged": boolean` field ([docs.github.com, Pull
   requests](https://docs.github.com/en/rest/pulls/pulls), verified 2026-08-22).
   Stated honestly, GitHub's own docs do not frame this in explicit state-machine
   language, merging and closing are documented as distinct API operations, not
   narrated as transitions, even though the underlying shape (a fixed set of states, a
   fixed set of ways to move between them) is the same pattern.
4. **Twilio Voice, the Call resource.** Documented `status` values, each with Twilio's
   own description, `queued` ("The call is ready and waiting in line before dialing"),
   `ringing` ("The call is currently ringing"), `in-progress` ("The call was answered
   and is currently in progress"), `completed` ("The call was answered and has ended
   normally"), `busy`, `failed`, `no-answer`, and `canceled` ("The call was canceled via
   the REST API while it was ringing")
   ([twilio.com, Call
   resource](https://www.twilio.com/docs/voice/api/call-resource), verified 2026-08-22).

## 10. Consequences

**Positive.**

- A single named location holds the legal transition graph, replacing scattered
  conditionals with one table a reviewer can read in full, per the Spring Statemachine
  and statecharts.dev framing in dimension 2.
- Guards centralize the check for whether a transition is legal right now, rather than
  leaving that logic embedded ad hoc at each call site, this is also the structural
  property dimension 17's two access-control CVEs show going wrong when it is missing.
- Entry and exit actions give a single place to run a side effect exactly once per
  state change, instead of duplicating that side effect at every call site that might
  cause the change.
- The same finite-states-plus-guarded-transitions shape scales from a UI component's
  interactive modes up to a durable-execution engine's own persisted execution model,
  the vocabulary transfers.

**Negative.**

- A flat machine's state count grows as the cartesian product of independent
  concerns, the statecharts.dev example in dimension 3 shows two axes producing four
  states and three axes producing eight.
- Guards are checked at runtime in the libraries this pass verified, so an unhandled or
  incorrectly guarded transition is a runtime bug, not a compile error, unless the
  implementation deliberately encodes states into the type system (dimension 14).
- A persisted machine's context can carry sensitive data, and the persistence layer
  itself becomes an attack surface, per the real, severe CVE in dimension 17.
- Choosing a specific library carries real lifecycle risk, Spring Statemachine's own
  archival this year is a concrete instance of that risk materializing for a widely
  used implementation.

## 11. Failure modes and misuse

**State explosion.** Already sourced in dimension 3 with the cartesian-product example
and the parallel-region fix. statecharts.dev's own framing, "The main problem that's
stopping widespread usage of state machines is the fact that beyond very simple
examples, state machines often end up with a large number of states, a lot of them with
identical transitions"
([statecharts.dev, State explosion](https://statecharts.dev/state-machine-state-explosion.html),
verified 2026-08-22).

**Incomplete transition table causing an unhandled event.** This pass could not find
and independently verify a specific, real postmortem or issue clearly matching a
missing or unhandled state transition in a state-machine library specifically, and that
gap is stated honestly rather than papered over. The closest verified, real, dated,
high-impact example of the same underlying discipline failure, implicit state colliding
with an incompletely retired code path, is the 2012 Knight Capital Group trading
disruption. A technician failed to deploy new code to one of eight servers; the new
code "repurposed a flag that was formerly used to activate an old function known as
'Power Peg'"; orders on the unpatched server "triggered the defective Power Peg code
still present on that server," which ran unbounded because the fulfillment-reporting
code "had been altered after the deprecation of 'Power Peg', resulting in the order
never being recorded as completed." Knight Capital took a pre-tax loss of $440 million
across "4 million executions in 154 stocks for more than 397 million shares in
approximately 45 minutes"
([Wikipedia, Knight Capital
Group](https://en.wikipedia.org/wiki/Knight_Capital_Group), verified 2026-08-22). This
is offered as an illustration of the risk class, a repurposed flag colliding with a
never-fully-retired path, and it must be read that way, it was not built on an explicit
state-machine library and no source found frames it that way directly.

**State drift, persisted or in-memory state disagreeing with reality.** The clearest
sourced treatment of this class of bug is from an adjacent domain, infrastructure
controllers, not application-level workflow entities, and is presented here as an
analogy rather than a direct citation about this pattern. Kubernetes' own documentation
frames the problem plainly. A thermostat's target setting is the desired state, while
"the actual room temperature is the current state," and "the thermostat acts to bring
the current state closer to the desired state." The same idea scales to a whole
cluster, "controllers are control loops that watch the state of your cluster, then make
or request changes where needed," each one trying "to move the current cluster state
closer to the desired state." Kubernetes states the honest limit of this loop directly,
"potentially, your cluster never reaches a stable state"
([kubernetes.io, Controller
concept](https://kubernetes.io/docs/concepts/architecture/controller/), verified
2026-08-22). The same discipline, continuously reconcile against what is actually true
rather than trust a single transition or the persisted record blindly, applies to a
crashed or racing state machine.

**Over-modeling.** The clearest sourced critique remains the GoF caveat already quoted
in dimension 3, overkill when a machine has few states or rarely changes. A
statecharts.dev FAQ page that appeared, from an earlier broader fetch, to directly
rebut the "it's simply not needed" objection returned an HTTP error on a direct fetch
this pass and could not be independently re-verified with its full argument, so it is
noted here as a partial, unconfirmed source rather than quoted.

## 12. Trade-off matrix

| Approach | Explicit legal transitions | Compile-time safety | Survives a process crash | Setup cost |
|---|---|---|---|---|
| Explicit state machine, in-process library (XState, Stateless, transitions, AASM) | Yes, one declared table | Runtime in the libraries verified here, some languages can encode it at compile time (dimension 14) | Only if the library's own persistence hook is wired to storage | Low to moderate |
| Boolean flags or an implicit status field, no library | No, logic is scattered at call sites | No | Whatever the storage layer itself gives you, not the modeling choice | Lowest to start, highest to maintain past a few states, per dimension 2 |
| Workflow Engine (Temporal, Step Functions, and similar) | Yes, and durably persisted with replay | Determinism rules are runtime-enforced, not compile-time | Yes, by design | Highest, see the sibling `workflow-engine` entry |
| Saga orchestrator | Yes, tracked as its own state (dimension 13) | Depends on the orchestrator's own implementation | Depends on whether the orchestrator itself is built on a durable engine | Moderate to high, scoped to the multi-service transaction problem |

The Workflow Engine row's durability claim is the sibling entry's own territory
(dimension 3), repeated here only for the comparison. The in-process versus engine line
is not sharp in the tooling itself, XState's own v6 alpha series is actively adding
durable-execution primitives not previously in the library (dimension 14), which is
direct, if circumstantial, evidence that the industry's own tooling is narrowing this
exact gap rather than treating it as fixed.

## 13. Related and incompatible patterns

**Saga**, in depth, this is this entry's own angle, the sibling `workflow-engine`
entry only touches it briefly. A saga orchestrator's core job is to answer, at every
point, "where are we right now, and if we must unwind, which compensating actions have
already fired." That answer is exactly a finite set of control states (for example, an
order saga might move `pending` to `credit_reserved` to `order_approved` on success, or
`pending` to `credit_reserved` to `compensating` to `order_rejected` on a failed credit
check), and the orchestrator's loop is a transition function, given the current saga
state and the outcome of the most recent step, compute the next state and the next
action, either call the next forward step or run the next compensation in reverse
order. The compensation-ordering rule itself only makes sense if the orchestrator
tracks, as its own persisted context, the ordered set of forward steps that already
completed, which is precisely what a state machine's extended state (XState's `context`,
dimension 5) is for. Stated honestly, this pass could not obtain a fresh, distinct
quotable passage from Chris Richardson's microservices.io on saga state tracking
specifically, one URL returned an HTTP error and a second, when queried directly for
this detail, stated the detail was not present in what could be fetched. The connection
above is this entry's own reasoned architectural analysis, well established in the
distributed-systems field, not a freshly sourced citation, and a future pass should
re-attempt Richardson's site or his published book for a direct quote before this claim
is treated as independently sourced.

**State** (the GoF design pattern, [`patterns/01-design-patterns-gof/state.md`]). The
narrower, object-oriented implementation shape, a `Context` delegating to a `State`
interface and `ConcreteState` classes. State Machine Workflow, this entry, is the
broader pattern that the GoF State pattern, a hand-rolled library like AASM or
`transitions`, or a full Workflow Engine can each implement.

**Choreography.** An alternative to a single central orchestrator's transition table,
where services react to each other's events with no shared machine. Covered from the
Workflow Engine sibling's own trade-off matrix.

**Workflow Engine** (sibling entry). A durable-execution runtime whose own execution
model is very often literally a persisted state machine, see dimension 3 and dimension
8's bridge paragraph.

**Orchestrator-Worker.** The AI-agentic family's coordination pattern, related in
intent, a lead process assigning work, but distinct in mechanism from a guarded
transition table.

## 14. Refactoring path in and out

**Introducing it.** Start from the Spring Statemachine signal in dimension 2, a
boolean flag or an enum standing in for a real lifecycle, or an if-else chain checking
combinations of flags. Begin flat, per XState's own guidance in dimension 3, and only
introduce nesting or orthogonal regions once a repeated pattern or an independent axis
of state actually appears, never up front. Name the states after the domain, not after
implementation details.

**A genuinely modern variant worth naming here, not as a recent development but as an
implementation choice.** Rust's typestate pattern encodes each state as its own type,
so an operation is only callable on the type representing the state it is legal in, and
a transition consumes the old value (via Rust's move semantics) and returns a new
type, making an invalid call a compile error rather than a runtime one. Cliff L.
Biffle's own framing, from a widely cited 2019 explanation, "It moves certain types of
errors from run-time to compile-time, giving programmers faster feedback"
([cliffle.com, The typestate
pattern in Rust](https://cliffle.com/blog/rust-typestate/), verified 2026-08-22, dated
June 5, 2019, so it predates this entry's own verification window and is presented as
an established, not a recent, technique). This pass could not confirm the pattern is
named in the official Rust API Guidelines, that page covers newtypes, custom argument
types, and builders, but does not mention typestate by name
([rust-lang.github.io, Type
safety](https://rust-lang.github.io/api-guidelines/type-safety.html), verified
2026-08-22), so this remains a single, solid, but uncorroborated primary source.

**Removing or evolving it.** Move from an in-process library toward a Workflow Engine
once the process's own lifetime stops matching the workflow's required lifetime, a
crash mid-transition can no longer be acceptable to simply lose, per the persistence
force in dimension 3. Move the other direction, collapse a machine back to a plain
enum, when the states stop being genuinely distinct or the transition table stops
changing, per the GoF overkill caveat in dimension 4.

## 15. Testing and verification

**XState's model-based testing.** Stately's own docs state that the model-based
testing utilities "allow you to automatically generate test cases from your state
machines," walking the declared transition graph to derive test paths across the
whole machine rather than hand-writing them one at a time
([stately.ai, Testing](https://stately.ai/docs/testing), verified 2026-08-22). The
same page states the standalone `@xstate/test` package "is no longer the recommended
approach. Instead, testing utilities are now available under `xstate/graph`." This
pass could not independently confirm the exact current function names under
`xstate/graph` (two separate fetch attempts against the package registry and the
repository both failed), so specific function names are not asserted here.

**Spring Statemachine's testing support.** A dedicated module, `spring-statemachine-test`,
is confirmed in the reference documentation's own module table, "Support module for
state machine testing," alongside a `@WithStateMachine` annotation for test-context
integration ([docs.spring.io, Spring Statemachine
reference](https://docs.spring.io/spring-statemachine/docs/current/reference/), verified
2026-08-22). The module and the annotation are confirmed to exist, a more specific
fluent test-builder API commonly referenced in secondary sources could not be retrieved
from the primary documentation across repeated attempts this pass, and is not asserted
here. Given the project's own archival (dimension 8), this testing surface should be
treated as frozen at its last release rather than actively evolving.

**Property-based, stateful testing, a strong, independently verified example.**
Hypothesis's own documentation describes its `RuleBasedStateMachine` feature directly,
"Hypothesis instead tries to generate not just data but entire tests," generating
sequences of operations against a stateful object rather than single inputs. Rules,
defined via the `rule()` decorator, are the direct analogue of transitions, and "a
single test run may involve multiple rule invocations, which may interact in various
ways." Bundles let generated data flow between rules, modeling a dependency between
transitions. Preconditions are Hypothesis's own direct guard analogue, "used on
`rule`-decorated functions, and must be given a function that returns True or False
based on the RuleBasedStateMachine instance," so a rule whose precondition currently
returns false is never attempted, exactly mirroring a state machine guard. Invariants
"run after every step" and assert a property holds across the whole generated sequence,
not only at the end
([hypothesis.readthedocs.io, Stateful
testing](https://hypothesis.readthedocs.io/en/latest/stateful.html), verified
2026-08-22). This pass could not find a source describing the general technique of
asserting every declared transition fires and every non-declared transition is
correctly rejected as a named, cited practice, so that specific framing is not
presented as sourced.

## 16. Observability signals

**Time-in-state.** AWS Step Functions exposes real, per-step timing metrics that map
onto this signal, `ActivityRunTime` ("Interval, in milliseconds, between the time the
activity starts and the time it closes") and `ActivityScheduleTime` (the time an
activity spends waiting in the schedule state before a worker picks it up). AWS's own
guidance is that a timeout value can be set against the same time period
([docs.aws.amazon.com, Monitoring with
CloudWatch](https://docs.aws.amazon.com/step-functions/latest/dg/procedure-cw-metrics.html),
verified 2026-08-22, cited here narrowly for the general dwell-time signal a
state-machine-shaped system exposes, not for Step Functions' own full metrics
catalogue, which belongs to the sibling entry). A step whose dwell time is
anomalously long against its historical baseline is the signature of a stuck instance.

**Transition rate by (from-state, to-state) pair.** AWS exposes a coarser
`ServiceMetric` dimension filtering on `StateTransition`, plus an account-wide
`ExecutionThrottled` metric described as related to state-transition throttling, but
this pass found no first-class per-pair breakdown as a built-in metric. A true
(from, to) count is something a team layers on top themselves, for example by emitting
a custom metric on every recorded entry and exit event, using the machine's own
identifier as the join key. That layering detail is this entry's own reasoning, not a
directly quoted feature.

**Invalid-transition-attempt counters.** No vendor metric measuring "a transition was
attempted and a guard rejected it" was found as a first-class counter. This is the
weakest-sourced of the four signals here, and it is presented as reasoned engineering
guidance, emit a counter every time a guard function returns false, labeled by the
machine type, the source state, and the attempted event, grounded in a real reason to
bother, the two access-control CVEs in dimension 17 are exactly the class of bug this
counter would surface early.

**Current-state distribution.** AWS's closest metric is `OpenExecutionCount`,
"Approximate number of currently open executions," stated purpose "to provide insight
into when your workflows are approaching the maximum execution limit"
([docs.aws.amazon.com, Monitoring with
CloudWatch](https://docs.aws.amazon.com/step-functions/latest/dg/procedure-cw-metrics.html),
verified 2026-08-22). For a database-backed machine, a status column, this signal is a
plain `GROUP BY status COUNT(*)` query, this is reasoned engineering fact rather than a
cited feature, but it is straightforward enough to state with confidence.

## 17. Security and privacy implications

**A missing or incorrect guard is a real, exploited access-control bug class.** Two
distinct, currently tracked CVEs confirm this precisely.

CVE-2026-48014, GHSA-f8q6-3g5w-jjr6, Shopware, "Admin API ACL Bypass in Order State
Transition Endpoints," package `shopware/core`, moderate severity, published June 4,
2026, credited to "offset." An access-control-list check that should have gated
whether a caller was permitted to move an order into a given status was missing or
bypassable on the order state-transition endpoints, letting an under-privileged caller
trigger a transition it should not have been authorized to make.

CVE-2026-34738, GHSA-m577-w9j8-ch7j, AVideo (`wwbn/avideo`), "Video Publishing Workflow
Bypass via Unauthorized `overrideStatus` Request Parameter," moderate severity,
published April 1, 2026, credited to "adrgs and aisafe-bot." Here the bug is a second,
unguarded path, an `overrideStatus` request parameter that could set the workflow
status directly, skipping the normal transition table and its guard entirely, the
application had two ways to change status and only guarded one of them.

Both confirmed via the GitHub Advisory Database ([github.com,
GHSA-f8q6-3g5w-jjr6](https://github.com/advisories/GHSA-f8q6-3g5w-jjr6); [github.com,
GHSA-m577-w9j8-ch7j](https://github.com/advisories/GHSA-m577-w9j8-ch7j), verified
2026-08-22).

**Persisted context as a deserialization attack surface, a real, high-severity CVE.**
CVE-2026-41862, Spring Statemachine, confirmed independently against both the GitHub
Advisory Database and NVD. NVD's own description, "Spring Statemachine's Kryo-based
persistence backends (JPA, MongoDB, Redis and ZooKeeper) deserialise persisted
state-machine contexts without enforcing a class allowlist (CWE-502, deserialisation of
untrusted data), which can lead to remote code execution inside the application JVM."
Affected versions 4.0.0 to 4.0.1 and 3.2.0 to 3.2.4, CVSS 3.1 base score 8.8, rated
high severity, network-attackable with low complexity and low privileges required
([nvd.nist.gov,
CVE-2026-41862](https://nvd.nist.gov/vuln/detail/CVE-2026-41862), verified 2026-08-22).
This is stronger than a general "sensitive data might leak if persisted insecurely"
concern, it is the sharper case, the deserialization path itself trusted the bytes read
back from storage enough to reconstruct arbitrary Java objects with no restriction on
which classes were legal to reconstruct, a classic CWE-502 remote-code-execution shape.
The library shipped this across four separate storage backends at once (JPA, MongoDB,
Redis, ZooKeeper), which shows the bug lived in the shared serialization layer, not in
any one backend's own integration code. The general principle for any persisted state
machine, distinct from the vendor-specific payload-encryption mechanics the sibling
`workflow-engine` entry already covers for Temporal and Step Functions, whenever a
machine's context or extended state is persisted and later restored, the deserialization
path is itself a first-class attack surface, the bytes coming back from storage need
the same treatment as an untrusted request body, a class allowlist for a binary format
like Kryo or Java serialization, or schema validation for a JSON-based format, because
"who last wrote to the persistence store" is not always a trust boundary that holds in
a distributed or long-running system.

## 18. References

1. Wikipedia. *Mealy machine*.
   https://en.wikipedia.org/wiki/Mealy_machine
   Verified 2026-08-22. Source of the 1955 Mealy machine origin and definition.
2. Wikipedia. *Moore machine*.
   https://en.wikipedia.org/wiki/Moore_machine
   Verified 2026-08-22. Source of the 1956 Moore machine origin and definition.
3. Wikipedia. *Automata theory*.
   https://en.wikipedia.org/wiki/Automata_theory
   Verified 2026-08-22. Source of the field's 1956 crystallization and its
   contributors.
4. Wikipedia. *Finite-state machine*.
   https://en.wikipedia.org/wiki/Finite-state_machine
   Verified 2026-08-22. Source of the formal FSM definition.
5. Wikipedia. *UML state machine*.
   https://en.wikipedia.org/wiki/UML_state_machine
   Verified 2026-08-22. Source of the UML/Harel statechart framing, composite
   states, orthogonal regions, and internal transitions.
6. Wikipedia. *State pattern*.
   https://en.wikipedia.org/wiki/State_pattern
   Verified 2026-08-22. Source of the GoF State design pattern and its
   Context/State/ConcreteState vocabulary.
7. Stately (XState). *State machines and statecharts*.
   https://stately.ai/docs/state-machines-and-statecharts
   Verified 2026-08-22. Source of the workflow-framing bridge quote.
8. Spring Statemachine. Reference documentation.
   https://docs.spring.io/spring-statemachine/docs/current/reference/
   Verified 2026-08-22. Source of the Background, Usage Scenarios, builder API,
   guards, actions, regions, persistence, and testing-module content.
9. statecharts.dev.
   https://statecharts.dev/
   Verified 2026-08-22. Secondary community source, corroborating problem
   framing.
10. Stripe. *Subscriptions overview*.
    https://docs.stripe.com/billing/subscriptions/overview
    Verified 2026-08-22. Source of the Stripe subscription status lifecycle.
11. Refactoring.Guru. *State*.
    https://refactoring.guru/design-patterns/state
    Verified 2026-08-22. Secondary source paraphrasing GoF applicability
    guidance.
12. Stately (XState). *Guards*.
    https://stately.ai/docs/guards
    Verified 2026-08-22. Source of the runtime guard definition.
13. Stately (XState). *Parent states*.
    https://stately.ai/docs/parent-states
    Verified 2026-08-22. Source of the flat-first hierarchy guidance.
14. statecharts.dev. *State machine state explosion*.
    https://statecharts.dev/state-machine-state-explosion.html
    Verified 2026-08-22. Source of the cartesian-product example and the
    parallel-region fix.
15. Stately (XState). *Persistence*.
    https://stately.ai/docs/persistence
    Verified 2026-08-22. Source of the persistence-requirements list bridging
    to Workflow Engine.
16. AWS. *What is Step Functions*.
    https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html
    Verified 2026-08-22. Source of the state-machine-equals-workflow product
    identity quote.
17. Stately (XState). *Transitions*.
    https://stately.ai/docs/transitions
    Verified 2026-08-22. Source of transition, event, and enabled-transition
    definitions.
18. Stately (XState). *Actions*.
    https://stately.ai/docs/actions
    Verified 2026-08-22. Source of entry and exit action definitions.
19. Stately (XState). *Final states*.
    https://stately.ai/docs/final-states
    Verified 2026-08-22. Source of the final-state definition.
20. Stately (XState). *Parallel states*.
    https://stately.ai/docs/parallel-states
    Verified 2026-08-22. Source of the orthogonal-region definition.
21. Stately (XState). *Context*.
    https://stately.ai/docs/context
    Verified 2026-08-22. Source of the extended-state (context) definition.
22. Stately (XState). *Actors*.
    https://stately.ai/docs/actors
    Verified 2026-08-22. Source of the actor-model composition layer.
23. XState (legacy v4 docs). *SCXML*.
    https://xstate.js.org/docs/guides/scxml.html
    Verified 2026-08-22. Source of the SCXML-compatibility mapping, confirmed
    for the v4 era only.
24. W3C. *SCXML, State Chart XML*.
    https://www.w3.org/TR/scxml/
    Verified 2026-08-22. Source of the W3C Recommendation status and date.
25. GitHub. *spring-projects/spring-statemachine*.
    https://github.com/spring-projects/spring-statemachine
    Verified 2026-08-22. Source of the July 5, 2026 archival notice and last
    release version.
26. GitHub. *aasm/aasm*.
    https://github.com/aasm/aasm
    Verified 2026-08-22. Source of the AASM gem's API and maintenance status.
27. GitHub. *pytransitions/transitions*.
    https://github.com/pytransitions/transitions
    Verified 2026-08-22. Source of the Python `transitions` library's API.
28. GitHub. *dotnet-state-machine/stateless*.
    https://github.com/dotnet-state-machine/stateless
    Verified 2026-08-22. Source of the .NET Stateless library's API.
29. Microsoft Learn. *Durable orchestrations*.
    https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-orchestrations
    Verified 2026-08-22. Source of the Azure Durable Functions event-sourcing
    framing.
30. docs.github.com. *Workflow runs*.
    https://docs.github.com/en/rest/actions/workflow-runs
    Verified 2026-08-22. Source of the GitHub Actions status and conclusion
    axes.
31. docs.github.com. *Pull requests*.
    https://docs.github.com/en/rest/pulls/pulls
    Verified 2026-08-22. Source of the GitHub PR state and merged field.
32. Twilio. *Call resource*.
    https://www.twilio.com/docs/voice/api/call-resource
    Verified 2026-08-22. Source of the Twilio Voice call status values.
33. Wikipedia. *Knight Capital Group*.
    https://en.wikipedia.org/wiki/Knight_Capital_Group
    Verified 2026-08-22. Source of the 2012 trading-disruption facts, presented
    as an analogous illustration, not an FSM-library bug.
34. Kubernetes. *Controllers*.
    https://kubernetes.io/docs/concepts/architecture/controller/
    Verified 2026-08-22. Source of the desired-state-versus-actual-state
    reconciliation framing.
35. Hypothesis. *Stateful testing*.
    https://hypothesis.readthedocs.io/en/latest/stateful.html
    Verified 2026-08-22. Source of the RuleBasedStateMachine, rules, bundles,
    preconditions, and invariants.
36. AWS. *Monitoring Step Functions using CloudWatch*.
    https://docs.aws.amazon.com/step-functions/latest/dg/procedure-cw-metrics.html
    Verified 2026-08-22. Source of the time-in-state and current-state
    observability metrics.
37. GitHub Advisory Database. *GHSA-f8q6-3g5w-jjr6*.
    https://github.com/advisories/GHSA-f8q6-3g5w-jjr6
    Verified 2026-08-22. Source of the Shopware ACL bypass CVE.
38. GitHub Advisory Database. *GHSA-m577-w9j8-ch7j*.
    https://github.com/advisories/GHSA-m577-w9j8-ch7j
    Verified 2026-08-22. Source of the AVideo overrideStatus bypass CVE.
39. NVD. *CVE-2026-41862*.
    https://nvd.nist.gov/vuln/detail/CVE-2026-41862
    Verified 2026-08-22. Source of the Spring Statemachine deserialization RCE.
40. Cliff L. Biffle. *The typestate pattern in Rust*.
    https://cliffle.com/blog/rust-typestate/
    Verified 2026-08-22, originally dated June 5, 2019. Source of the typestate
    pattern explanation.
41. Rust API Guidelines. *Type safety*.
    https://rust-lang.github.io/api-guidelines/type-safety.html
    Verified 2026-08-22. Checked for a typestate mention, not found, cited to
    support the honest gap.

**Evidence grade.** established

**Most solid findings.** Both automata-theory origin papers (Mealy 1955, Moore 1956)
and the GoF State pattern and Harel Statecharts lineage are each independently
confirmed. The vocabulary table in dimension 5 cross-checks across XState, Spring
Statemachine, and UML, three independent sources agreeing on the same terms. The Stripe
subscription lifecycle is a real, current, first-party production example with a
directly quoted terminal-state statement. The two access-control CVEs and the Spring
Statemachine deserialization CVE in dimension 17 are all currently tracked, real, and
precisely on-pattern. Hypothesis's RuleBasedStateMachine is a strong, directly
documented, verified property-based testing example.

**Unverified or unclear.** No real, named production state-machine example from
Netflix, Uber, or Lyft could be independently fetched this pass, every attempted URL
returned an error, this is a real gap against what was originally sought. The Saga
relationship in dimension 13 is reasoned architectural analysis, not a freshly sourced
quote from Chris Richardson's own site, a future pass should retry that source or his
published book. XState's current TypeScript exhaustiveness guarantees, its current
SCXML-compatibility claim on the v5/v6 documentation, and the exact `xstate/graph`
testing function names are all unconfirmed this pass and are presented with that
hedge. A specific real postmortem or issue matching "an incomplete transition table
caused a production bug" was not found, the Knight Capital incident is offered only as
an analogous illustration. The statecharts.dev claim that statechart-based code has a
lower bug count than traditional code was seen but its underlying study was not located
or verified, and is not repeated as fact in this entry.

## Code

### TypeScript, a generic guarded state machine applied to an order lifecycle

```typescript
type Transition<S extends string, E extends string> = {
  from: S;
  event: E;
  to: S;
  guard?: () => boolean;
};

class StateMachine<S extends string, E extends string> {
  private current: S;
  private readonly transitions: Transition<S, E>[];
  private readonly onEnter: Partial<Record<S, () => void>>;
  private readonly onExit: Partial<Record<S, () => void>>;

  constructor(
    initial: S,
    transitions: Transition<S, E>[],
    onEnter: Partial<Record<S, () => void>> = {},
    onExit: Partial<Record<S, () => void>> = {}
  ) {
    this.current = initial;
    this.transitions = transitions;
    this.onEnter = onEnter;
    this.onExit = onExit;
  }

  state(): S {
    return this.current;
  }

  send(event: E): boolean {
    const enabled = this.transitions.filter(
      (t) => t.from === this.current && t.event === event
    );
    const legal = enabled.find((t) => !t.guard || t.guard());
    if (!legal) {
      return false;
    }
    this.onExit[this.current]?.();
    this.current = legal.to;
    this.onEnter[this.current]?.();
    return true;
  }
}

type OrderState = "pending" | "paid" | "shipped" | "delivered" | "canceled";
type OrderEvent = "pay" | "ship" | "deliver" | "cancel";

function buildOrderMachine(hasPaymentMethod: () => boolean) {
  return new StateMachine<OrderState, OrderEvent>(
    "pending",
    [
      { from: "pending", event: "pay", to: "paid", guard: hasPaymentMethod },
      { from: "pending", event: "cancel", to: "canceled" },
      { from: "paid", event: "ship", to: "shipped" },
      { from: "paid", event: "cancel", to: "canceled" },
      { from: "shipped", event: "deliver", to: "delivered" },
    ],
    { shipped: () => console.log("notify: order shipped") },
    { paid: () => console.log("stop: accepting further payments") }
  );
}

function run(): void {
  const machine = buildOrderMachine(() => true);
  console.log(machine.send("pay"), machine.state());
  console.log(machine.send("ship"), machine.state());
  console.log(machine.send("pay"), machine.state());
  console.log(machine.send("deliver"), machine.state());
}

run();
```

### Python, a transition-table machine that rejects an illegal move

```python
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


@dataclass
class ApprovalMachine:
    state: str = "draft"
    reviewer_assigned: bool = False
    transitions: Dict[Tuple[str, str], str] = field(
        default_factory=lambda: {
            ("draft", "submit"): "submitted",
            ("submitted", "approve"): "approved",
            ("submitted", "reject"): "rejected",
            ("rejected", "submit"): "submitted",
        }
    )

    def guard_passes(self, event: str) -> bool:
        if event == "approve":
            return self.reviewer_assigned
        return True

    def send(self, event: str) -> bool:
        key = (self.state, event)
        if key not in self.transitions:
            return False
        if not self.guard_passes(event):
            return False
        self.state = self.transitions[key]
        return True


def exhaustive_transition_check(
    machine: ApprovalMachine, legal: List[Tuple[str, str]], illegal: List[Tuple[str, str]]
) -> bool:
    for state, event in legal:
        machine.state = state
        machine.reviewer_assigned = True
        if not machine.send(event):
            return False
    for state, event in illegal:
        machine.state = state
        machine.reviewer_assigned = False
        if machine.send(event):
            return False
    return True


if __name__ == "__main__":
    m = ApprovalMachine()
    ok = exhaustive_transition_check(
        m,
        legal=[("draft", "submit"), ("submitted", "reject"), ("rejected", "submit")],
        illegal=[("draft", "approve"), ("approved", "submit")],
    )
    print("every declared transition fires and every undeclared one is rejected:", ok)
```

### Go, a state machine with entry and exit actions for a document workflow

```go
package main

import "fmt"

type DocState string

const (
	StateDraft     DocState = "draft"
	StateReview    DocState = "review"
	StatePublished DocState = "published"
	StateArchived  DocState = "archived"
)

type transitionKey struct {
	from  DocState
	event string
}

type DocMachine struct {
	current     DocState
	transitions map[transitionKey]DocState
	onEnter     map[DocState]func()
	onExit      map[DocState]func()
}

func NewDocMachine() *DocMachine {
	m := &DocMachine{
		current: StateDraft,
		transitions: map[transitionKey]DocState{
			{StateDraft, "submit"}:     StateReview,
			{StateReview, "approve"}:   StatePublished,
			{StateReview, "reject"}:    StateDraft,
			{StatePublished, "retire"}: StateArchived,
		},
		onEnter: map[DocState]func(){},
		onExit:  map[DocState]func(){},
	}
	m.onEnter[StatePublished] = func() { fmt.Println("notify subscribers: published") }
	m.onExit[StateReview] = func() { fmt.Println("release the reviewer lock") }
	return m
}

func (m *DocMachine) Send(event string) bool {
	next, ok := m.transitions[transitionKey{m.current, event}]
	if !ok {
		return false
	}
	if exit, has := m.onExit[m.current]; has {
		exit()
	}
	m.current = next
	if enter, has := m.onEnter[m.current]; has {
		enter()
	}
	return true
}

func main() {
	m := NewDocMachine()
	fmt.Println(m.Send("submit"), m.current)
	fmt.Println(m.Send("approve"), m.current)
	fmt.Println(m.Send("submit"), m.current)
	fmt.Println(m.Send("retire"), m.current)
}
```
