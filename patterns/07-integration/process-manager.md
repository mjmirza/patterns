---
name: Process Manager
slug: process-manager
family: 07-integration
category: System Management
aliases: [Process Orchestrator, Orchestration Engine, Central Coordinator]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [routing-slip, aggregator, correlation-identifier, content-based-router, message-bus, event-message, command-message]
incompatible_with: []
verified: 2026-08-02
---

# Process Manager

## 1. Name, aliases, and lineage

The canonical name is Process Manager, cataloged by Gregor Hohpe and Bobby
Woolf in *Enterprise Integration Patterns. Designing, Building, and Deploying
Messaging Solutions*, Addison-Wesley, 2003, in the System Management chapter of
their pattern language. The book's companion site states the intent directly.
how do we route a message through multiple processing steps when the required
steps may not be known at design time and may not be sequential, solved by
using a central processing unit, the Process Manager, to maintain the state of
the sequence and determine the next processing step based on intermediate
results (see [enterpriseintegrationpatterns.com, Process Manager](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html),
verified 2026-08-02). Hohpe and Woolf group it alongside Routing Slip and
Message Broker as the three answers to the same underlying problem, dynamic,
data-dependent routing of a message through more than one step.

**Process Orchestrator** and **Orchestration Engine** are the names the same
concept carries in the SOA and BPM literature that grew up alongside the EIP
book, most visibly in the WS-BPEL 2.0 specification, which is explicitly an
orchestration language for a central engine that drives a business process
forward, in contrast to WS-CDL, a choreography language with no central
controller. **Central Coordinator** is the plain description Hohpe and Woolf
use inside the pattern's own text when comparing it against a decentralized
routing slip. The pattern predates the word microservice by a decade, but the
same shape reappears, largely unchanged, in every modern workflow orchestration
product, from AWS Step Functions to Camunda to Netflix Conductor to Temporal,
because the problem it solves, coordinating a multi-step business transaction
across independently deployed services, did not go away when the deployment
unit got smaller.

It is worth being precise about what the pattern is not. It is not a message
broker in the transport sense (Message Bus solves message delivery, Process
Manager solves sequencing logic that happens to travel over that bus). It is
not the same as choreography, where each participant knows only its own next
step and there is no central authority. And it is not a plain "if statement",
though a naive implementation often degenerates into exactly that, which
dimension 11 below covers in detail.

## 2. Problem and context

Picture an order fulfillment system built from independently owned services.
inventory, payment, shipping, fraud check, notification. A single customer
order is not one call to one service. it is a sequence. reserve inventory,
charge payment, and only if both succeed, schedule shipping and send a
confirmation. If payment fails, the inventory reservation must be released. If
fraud check flags the order, shipping must never happen at all, regardless of
what payment and inventory already did.

None of the individual services can own this logic, because none of them has
visibility into the others' outcomes and none of them should have to know
about the others' existence. A Content-Based Router can pick a destination for
one message based on its content, but it has no memory. it cannot say "wait
for both the payment confirmation and the inventory confirmation before
deciding what happens next," because a router is stateless by design, one
message in, one decision out, no correlation across messages.

The context that makes this problem sharp is threefold, and all three usually
show up together. First, the steps are conditional on results that are not
known until earlier steps have run, so the full path cannot be hardcoded into
any one message or any one service. Second, the steps may need to happen out
of a strict linear order, or in parallel, with the results reconciled later.
Third, and this is the part that most distinguishes Process Manager from
simpler routing patterns, the process itself has a lifespan that outlives any
single message. It must survive a service restart, a network partition, an
hours-long wait for a human approval, or a multi-day wait for a shipment to
physically arrive. That lifespan requirement is why the pattern is filed under
System Management rather than under Message Routing in the EIP catalog. it
needs somewhere durable to keep its state between the messages it reacts to.

## 3. Forces

**Coupling versus visibility.** A fully choreographed system, where each
service reacts to events and decides its own next action, minimizes coupling
because no service needs to know the others exist. But the moment something
goes wrong, nobody can answer "what state is order 4471 in right now" without
reconstructing it from a trail of events scattered across every participant.
Process Manager trades some of that decoupling for a single place that can
answer the question, at the cost of a central component every participant now
indirectly depends on for the workflow to progress.

**Single point of failure versus single source of truth.** Centralizing the
sequencing decision creates the operational risk classically associated with
any hub, if the Process Manager is down, no in-flight order can advance. But
it also creates the only place in the system where the true, current state of
a multi-step transaction lives, which is exactly what makes debugging,
auditing, and compensating (the Saga pattern's rollback logic) tractable. A
codebase whose state is scattered across a dozen services never running the
same query to answer "how far did order 4471 get" is a codebase that cannot
be operated with confidence.

**Latency versus correctness.** Routing every intermediate result back through
a central process manager, rather than letting a service call the next
service directly, adds a hop, or several, of latency. In exchange, the process
manager can enforce ordering and conditional logic (do not ship if fraud check
failed, even if the shipping request arrived first) that a direct
service-to-service call chain cannot enforce without duplicating that logic
into every service that might be first, second or third depending on runtime
conditions.

**Flexibility versus predictability.** Because the sequence is data-driven
rather than hardcoded, the same Process Manager code can route a domestic
order down a three-step path and an international order down a six-step path
that includes customs documentation, without either path being written into
the message itself (contrast with Routing Slip, dimension 13). This
flexibility is the pattern's whole reason for existing. it is also what makes
a Process Manager's logic harder to reason about by inspection than a fixed
pipeline, because the actual path any given instance took is not visible from
reading the code alone. it emerges from the combination of the code and the
data.

**Team topology and cognitive load.** A Process Manager owned by one team, but
coordinating steps owned by five other teams, concentrates business-process
knowledge in one place. It also means that team must understand enough about
every downstream service's contract, and every downstream team must coordinate
any breaking change with the Process Manager owner, a dependency that a fully
choreographed, event-driven design would spread thinner but never eliminate,
since somebody, somewhere, still needs to understand the business outcome as
a whole.

## 4. Applicability and non-applicability

Reach for Process Manager when the routing path genuinely depends on
intermediate results and cannot be known before the process starts. when
steps may run out of strict sequence or in parallel and must be reconciled.
when the process has a lifespan measured in more than a single request-response
round trip, spanning restarts, human approval delays, or external waits. when
an auditor, support engineer, or compensating-transaction routine needs a
single place to ask "what state is this instance in." and when the business
process itself is a first-class artifact that product owners want to see,
change, and reason about independently of the services it coordinates.

Do NOT reach for it in the following situations, each for a distinct reason.

- **A fixed, linear sequence known entirely at design time.** If step B always
  follows step A and step C always follows step B, with no conditional
  branching on runtime data, a Pipes and Filters chain or a plain synchronous
  call chain is simpler, has no central state to persist, and has one fewer
  moving part to operate. Introducing a Process Manager here adds an
  operational dependency for zero flexibility gained.
- **A single request that fans out and immediately fans back in.** If the
  "process" amounts only to calling three services in parallel, combining
  their three responses, and returning, that is Scatter-Gather, or a plain
  Aggregator, neither of which needs durable cross-message state that
  outlives the single request. A Process Manager's state store is overhead
  here.
- **When the participants can genuinely be autonomous.** If no single actor
  needs a global view, and each service reacting independently to events it
  cares about produces the correct overall outcome without anyone coordinating
  it, event-driven choreography keeps coupling lower and avoids creating the
  central component this pattern requires. Introducing a Process Manager into
  a system that was cleanly choreographed re-centralizes something that did
  not need to be centralized.
- **Very high-throughput, sub-millisecond paths.** The extra hop through a
  central coordinator, plus a durable state write per step, adds latency that
  a hot path processing millions of events per second usually cannot afford.
  Stream processing topologies (Kafka Streams, Flink) that keep state
  co-located with the computation are the better fit there.
- **When the team cannot own or operate a stateful service.** A Process
  Manager is a piece of infrastructure with its own failure modes, its own
  persistence layer, its own need for monitoring. A team without the
  operational maturity to run a stateful service reliably will often be
  better served by a managed orchestration product (Step Functions, Camunda
  SaaS) than by hand-rolling one, or, if neither is available, by simplifying
  the process until it no longer needs central state at all.

## 5. Structure

Four participants recur across every real implementation of this pattern, with
the same responsibilities regardless of whether the mechanism underneath is a
message-driven state machine, a BPMN engine, or a language-native durable
function.

- **Process Manager (or Process Manager Instance).** The stateful coordinator.
  Owns the current state for one in-flight business process instance,
  receives events or messages that carry results from prior steps, decides the
  next step based on that state plus the message content, and emits commands
  or requests that trigger the next step. Does not itself perform the business
  logic of any step, it only decides what happens next and tracks what has
  happened so far.
- **Process Definition (or Workflow Definition, or State Machine
  Definition).** The declarative or code-defined description of the possible
  states, the transitions between them, and the conditions that trigger each
  transition. In BPMN engines this is the XML process diagram. in Step
  Functions it is the Amazon States Language JSON. in a language-native
  implementation it is a state-transition table or a switch expression.
- **Correlation Identifier.** The value carried by every message related to
  one process instance, used to look up and update the correct Process
  Manager instance's state when a new message arrives. Almost always
  implemented as its own pattern, Correlation Identifier, and treated in this
  entry's dimension 13.
- **Participants (or Activities, or Tasks).** The independent services or
  steps the Process Manager coordinates but does not itself implement. Each
  participant receives a command from the Process Manager, does its work, and
  reports a result back, most often as an event, without needing to know
  anything about the other participants or about the overall process shape.

The relationships. the Process Manager reads and writes its own state, using
the Process Definition to decide the next transition. It sends commands to,
and receives events from, the Participants, using the Correlation Identifier
on every message to route the event back to the correct process instance.
Participants never talk directly to each other, and never need to know the
process's overall shape, only their own single-step contract with the Process
Manager.

## 6. ASCII structure diagram

```
+-------------------------------------+
| Process Manager Instance            |
| correlation_id: "order-4471"        |
| current_state:  AWAITING_PAYMENT    |
| history:        [InventoryReserved] |
+-------------------------------------+
           |
           | reads / writes state, per
           | Process Definition rules
           v
+-----------------------------------------------------------+
| Process Definition (rules)                                |
| STARTED           --InventoryReserved--> AWAITING_PAYMENT |
| AWAITING_PAYMENT  --PaymentConfirmed-->   READY_TO_SHIP   |
| AWAITING_PAYMENT  --PaymentDeclined-->    COMPENSATING    |
| READY_TO_SHIP     --ShipmentDispatched--> COMPLETED       |
+-----------------------------------------------------------+

  command(reserve)   command(charge)   command(ship)
       |                  |                 |
       v                  v                 v
+------------+ +------------+ +------------+
| Inventory  | | Payment    | | Shipping   |
| Service    | | Service    | | Service    |
+------------+ +------------+ +------------+
     |             |             |
     | event(Reserved) event(Confirmed/  event(Dispatched)
     | corr=order-4471 Declined)          corr=order-4471
     |                 corr=order-4471
     +-----------------+-----------------+
                       v
back to the Process Manager Instance, looked up by
correlation_id "order-4471"
```

## 7. Dynamics

The runtime flow is a repeated cycle. a message arrives carrying a
correlation identifier, the correct process instance is looked up or created,
its current state and the message content together determine the next
transition per the process definition, the transition is applied and
persisted, and zero or more new commands are emitted to participants. The
process manager never blocks waiting for a reply in the same thread. it
persists its state and waits to be woken by the next inbound message,
possibly seconds later, possibly days later.

```
Customer         Process Manager        Inventory      Payment      Shipping
  |                     |                    |             |            |
  |--PlaceOrder-------->|                    |             |            |
  |                     |--Reserve---------->|             |            |
  |                     |   state=STARTED    |             |            |
  |                     |<--Reserved---------|             |            |
  |                     |   state=AWAITING_PAYMENT          |            |
  |                     |------------------- Charge ------->|            |
  |                     |                    |             |            |
  |                     |   (persist and wait; may be       |            |
  |                     |    seconds or hours before the    |            |
  |                     |    next event arrives)            |            |
  |                     |                    |             |            |
  |                     |<-------------- PaymentConfirmed --|            |
  |                     |   state=READY_TO_SHIP              |           |
  |                     |------------------------------- Ship ---------->|
  |                     |                    |             |            |
  |                     |<---------------------------------ShipmentDispatched
  |                     |   state=COMPLETED  |             |            |
  |<--OrderCompleted----|                    |             |            |
  |                     |                    |             |            |

  Alternate path, PaymentDeclined branches to COMPENSATING and emits a
  ReleaseReservation command back to Inventory, never reaching Shipping.
```

Every arrow into the Process Manager column above is a separate, independent
message, arriving on its own schedule, with the correlation identifier as the
only thing tying them together into "this is still order 4471." That
independence is what lets the process survive the Process Manager process
itself restarting between any two of those events, provided the state was
durably persisted before the previous message finished processing.

## 8. Implementation variants

**Message-driven, hand-rolled state machine.** The classic EIP shape. a
consumer reads from a queue or topic, looks up the persisted state for the
correlation identifier (a row in a database, a document in a store), applies
a transition function, persists the new state, and publishes the next
command. This is the variant every language can implement with nothing more
exotic than a database and a message broker, and it is what most teams build
before adopting a dedicated orchestration product.

**BPMN process engine.** Camunda, jBPM, and Flowable interpret a BPMN 2.0 XML
diagram as the process definition and manage instance state, timers, and
human tasks in an embedded or standalone engine, giving business analysts a
visual notation that maps directly to the running process, at the cost of a
heavier runtime and a learning curve around the BPMN token-flow execution
semantics.

**Language orchestration built on WS-BPEL.** The SOA-era answer to the same
problem, an XML-based language whose execution semantics are explicitly
defined by the OASIS WS-BPEL 2.0 specification, still found in older
enterprise service bus deployments, and the historical bridge between the EIP
pattern language and today's cloud workflow services.

**Durable execution frameworks.** Temporal and, in a narrower cloud-native
form, AWS Step Functions and Azure Durable Functions, let the process
definition be written as ordinary code (a function that calls other
functions), while the framework transparently persists execution progress so
that a crash or redeploy resumes exactly where the code left off, without the
developer managing an explicit state table by hand. This variant trades the
visible state machine for developer ergonomics, at the cost of the framework
owning a nontrivial amount of magic around what is and is not safe to do
inside the orchestrating function (nondeterministic calls, direct I/O, and
unpinned random or time values are disallowed inside the orchestrator
body itself).

**Actor-per-instance.** Each process instance is modeled as a long-lived actor
(an Erlang/OTP process, an Akka actor, a Microsoft Orleans grain), whose
mailbox naturally serializes the events for that one instance and whose
internal state is the process state, without a separate state-store lookup on
every message. This variant removes the explicit correlation-identifier
lookup step by letting the runtime's own actor addressing do that job, at the
cost of needing an actor runtime with durable, restart-surviving actor state
(actor persistence, event sourcing of the actor) if the process must outlive a
node failure.

## 9. Known production uses

**AWS Step Functions.** Amazon's own documentation describes it as the
service for building workflows, called state machines, that orchestrate a
series of event-driven steps, tracking the progress of the workflow at each
step so an application runs in order and as expected, with explicit `Retry`
and `Catch` states for error handling and a `Choice` state for
data-conditional branching (see
[docs.aws.amazon.com, What is Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html),
verified 2026-08-02). This is the pattern's core structure, a central engine
tracking state and deciding the next step, delivered as a managed cloud
primitive rather than hand-rolled code.

**Camunda / Zeebe.** Camunda's own product description positions the platform
as the layer that decides when and how work executes and proves what
happened, distinct from an agent framework that reasons and an integration
platform that only moves data (see
[camunda.com, Platform](https://camunda.com/platform/), verified 2026-08-02).
The underlying Zeebe engine executes BPMN process definitions and persists
each running process as a stateful process instance, the textbook Process
Manager and Process Definition pairing implemented as an open-core BPM
engine.

**Netflix Conductor.** Conductor's own README describes it as an open source
durable workflow engine built at Netflix for orchestrating microservices, AI
agents, and durable workflows at internet scale, built explicitly because
orchestrating distributed systems means wrestling with failures, retries, and
state recovery, work Conductor performs so individual services do not have to
(see [github.com, conductor-oss/conductor README](https://raw.githubusercontent.com/conductor-oss/conductor/main/README.md),
verified 2026-08-02). This is a direct, named descendant of the EIP Process
Manager pattern operating at very large scale, coordinating microservice
calls that the individual services themselves have no visibility into as a
whole.

## 10. Consequences

Positive.

- A single, queryable place holds the true current state of a multi-step
  business transaction, which is what makes operational questions like "why
  is order 4471 stuck" answerable without stitching together logs from five
  services.
- Business-process logic (which step follows which, under what conditions) is
  centralized and can change without touching the individual participant
  services, as long as their command and event contracts stay stable.
- Compensating actions (Saga-style rollback) have a natural home, the Process
  Manager already tracks exactly which steps completed and can emit the
  correct undo commands for exactly those steps and no others.
- New participants can be added to a process by changing only the process
  definition and the new participant's own contract, without every existing
  participant needing to know about the addition.

Negative.

- The Process Manager becomes a required dependency for every in-flight
  instance to progress. its downtime does not lose data, if state is
  durably persisted, but it does stall every process instance until it
  recovers.
- It concentrates cross-team knowledge in whichever team owns the process
  definition, who must understand enough of every participant's contract to
  route correctly, and who becomes a coordination bottleneck for any breaking
  change to a participant's message shape.
- The actual runtime path of any given instance is not visible from reading
  the process manager's code alone. it is determined by the combination of
  code and the sequence of messages that instance happened to receive, which
  makes reasoning by inspection harder than for a fixed pipeline.
- Persisting state on every transition adds write latency and storage cost
  that a purely in-memory, choreographed design does not pay, a cost that
  scales with process instance count and average process lifetime.

## 11. Failure modes and misuse

**The god object process manager.** Symptom, one process definition grows to
cover dozens of unrelated business flows, with deeply nested conditional
branches that no single engineer can trace by reading the code. Cause, every
new business rule gets bolted onto the existing process manager instead of
being modeled as its own process, because splitting it looks like more
up-front work. Fix, split by business capability, one process manager per
distinct business transaction type, with clear entry and exit points, the
same single-responsibility instinct that governs class design applied to
process design.

**Correlation identifier collision or loss.** Symptom, events for order 4471
occasionally update the state of an unrelated order, or a legitimate event
never finds its process instance and silently gets dropped. Cause, the
correlation identifier is reused across process types without a namespace, or
generated with insufficient entropy, or a participant's response fails to
carry the identifier through because it was stripped by an intermediate
transformation step. Fix, treat the correlation identifier as a first-class,
namespaced part of every message contract from the start (see Correlation
Identifier, dimension 13), and add a dead-letter path for any inbound event
that cannot be correlated, rather than dropping it silently.

**Timeout amnesia.** Symptom, a process instance sits in an intermediate
state forever because the participant it was waiting on never responded, and
nobody notices for days. Cause, the process definition specifies what happens
on success and on explicit failure, but never specifies what happens if
nothing happens at all. Fix, every wait state in the process definition
carries an explicit timeout with a defined transition (retry, escalate to a
human, or move to a compensating path), never an implicit, unbounded wait.

**In-memory state with no durability.** Symptom, a routine service restart or
deploy silently loses every in-flight process instance, and customers whose
orders were mid-flow never get a resolution. Cause, the state was kept only
in process memory (a plain in-memory hashmap keyed by correlation id) because
it was fast to build, and durability was deferred as a later concern. Fix,
persist state transitionally, meaning the new state is durably written before
the next outbound command is emitted, so a crash between persisting and
sending at worst results in a duplicate command, which idempotent
participants can safely absorb, rather than a lost instance.

**Synchronous chaining disguised as orchestration.** Symptom, the "process
manager" amounts only to a single function that calls participant A, blocks
for its reply, then calls participant B, blocks for its reply, all inside one
request thread, with no persisted intermediate state at all. Cause, this is
faster to write for the happy path and looks identical to a real Process
Manager on a sequence diagram. Fix, recognize this is not the pattern, it is
a Request-Reply chain, and it has none of the pattern's durability or
partial-failure recovery properties. It fails the applicability test in
dimension 4, and a durable execution framework or explicit state persistence
is what turns it into the real pattern.

## 12. Trade-off matrix

| Force | Process Manager | Routing Slip | Choreography (event-driven, no central owner) |
|---|---|---|---|
| Central visibility of process state | High, one place to query | Low, path travels with the message, no single query answers "where is this now" without inspecting the message itself | Very low, state is implicit in the union of every participant's own records |
| Coupling to a central component | High, participants depend on the manager to progress | Low, the message carries its own routing, no central dispatcher needed at runtime | None, participants only depend on the event contracts they subscribe to |
| Handles data-dependent, non-linear routing | Yes, explicitly the pattern's purpose | Only if the slip itself can be built dynamically before dispatch, weaker for branches that depend on results not yet known | Yes, but no single actor decides the overall path, so complex branching is hard to audit |
| Adding a new step | Change the process definition centrally | Add a step to how the slip is assembled, decentralized decision of who builds the slip | Add a new subscriber, zero change to existing participants, but nobody guarantees full correctness |
| Survives long-lived, multi-day waits | Yes, this is the pattern's core strength | Weak, the slip pattern does not by itself address persistence across long waits | Depends entirely on how durably each participant's own state is kept |
| Operational cost | Higher, a stateful service to run and monitor | Lower, no separate coordinator process to operate | Lowest infrastructure cost, highest debugging cost when something goes wrong |

## 13. Related and incompatible patterns

**Correlation Identifier** is not optional, it is how a Process Manager finds
the right in-flight instance for an arriving message, and every implementation
of this pattern implicitly depends on it even when it is not called out as a
separate component in the code.

**Routing Slip** solves a closely related problem, a variable, data-dependent
sequence of steps, but decentralizes the decision by attaching the itinerary
to the message itself rather than keeping it in a central coordinator. The
two are frequently confused because both solve "the steps are not known until
runtime," and the EIP book explicitly discusses them side by side. Choose
Routing Slip when the itinerary can be fully determined once, up front, and
attached to the message. choose Process Manager when later steps genuinely
depend on results that later steps themselves produce.

**Aggregator** is often a participant inside a larger process a Process
Manager coordinates, used to combine several parallel responses (from a
fan-out the process manager itself triggered) back into a single result the
process manager then reacts to as one event.

**Content-Based Router** and **Process Manager** are sometimes conflated
because both make routing decisions based on message content, but a router
is stateless, one message decides one destination, while a process manager's
decisions depend on accumulated state across multiple messages. A router can
be, and often is, a stateless building block a Process Manager calls as part
of deciding a transition, without itself becoming stateful.

**Saga (application-level, not the GoF Memento-adjacent usage)** is the
compensating-transaction pattern most commonly implemented on top of a
Process Manager, orchestrated saga, where the manager tracks completed steps
and issues explicit compensating commands on failure, versus choreographed
saga, where each participant listens for failure events and undoes its own
work without a central coordinator.

**Message Bus** or **Message Broker** provides the transport a Process
Manager's commands and events travel over, but is a distinct pattern
concerned with delivery, not sequencing logic. a Process Manager is a
consumer and producer on top of a message bus, not a replacement for one.

No pattern in this catalog is genuinely incompatible with Process Manager in
the sense of being unable to compose, though replacing one variant's
mechanism with another mid-implementation (say, migrating a hand-rolled
message-driven state machine to a durable execution framework) is a real
migration project, not a drop-in swap, because the persistence and retry
semantics differ.

## 14. Refactoring path in and out

Introducing the pattern into a codebase that currently lacks it usually starts
from one of two shapes. either a growing pile of conditional logic scattered
across several services, each partially aware of what the others are doing,
or a synchronous call chain that has started needing conditional branches and
long waits it was never designed for.

1. Name the process explicitly. write down, in one place, the states an
   instance can be in and the events that cause a transition between them,
   even before any code changes, purely as documentation of the implicit
   process that already exists in the scattered conditionals.
2. Introduce a correlation identifier if one does not already exist, and
   confirm every message related to one instance of the process carries it.
   This is almost always the first concrete code change, and it is safe to
   make incrementally, one participant at a time, because adding a field to a
   message is backward compatible.
3. Extract the transition logic (dimension 1's list above) out of the
   individual participant services and into a new, single component, backed
   by durable storage keyed by the correlation identifier. At this point the
   participants stop deciding "what happens next" and start simply reporting
   "here is what happened," which the new Process Manager consumes.
4. Move participants from calling each other directly to only accepting
   commands from, and emitting events back to, the Process Manager, one
   participant at a time, verifying at each step that the process's observable
   behavior has not changed.
5. Add explicit timeout transitions for every wait state (see dimension 11's
   timeout amnesia failure mode) as the final hardening step, since these are
   easy to omit and hard to notice missing until an instance actually gets
   stuck.

Removing the pattern, when a process has stabilized into a fixed, linear
sequence with no remaining conditional branches, follows the reverse path,
in the opposite order of risk. First confirm, over a real observation window,
that no instance has taken a nonstandard path in a fair stretch of that
window, then collapse the fixed sequence back into a direct call chain or a
Pipes and Filters pipeline, retiring the persisted state store last, only
once the simpler mechanism has been running in parallel and verified
equivalent, since a persisted process manager can be running alongside a new
simpler implementation for a transition period without conflict, one
draining the old mechanism's remaining in-flight instances while the other
handles all new ones.

## 15. Testing and verification

Testing here divides cleanly along the seam the pattern itself creates,
between the transition logic and everything else. This is largely engineering
judgement, drawn from the practice of testing state machines generally rather
than from a single citable source.

The transition function (current state plus incoming event, yields next state
plus outbound commands) is pure and should be tested as such, table-driven,
enumerating every state and every event the process definition declares, with
particular attention to events that arrive in a state that does not expect
them (a `PaymentConfirmed` event arriving while the instance is already in
`COMPLETED`, for example, which a correct implementation should treat as a
duplicate or an error, not as a fresh transition).

Because instances persist across restarts, a test suite for this pattern is
incomplete without a "crash between persist and publish" test, restarting the
process manager's own state after a persisted-but-not-yet-published transition
and confirming recovery either resumes the outbound command or, if it was
already sent, that the receiving participant's idempotency handles the
duplicate correctly. This is the single highest-value test class for this
pattern and the one most often skipped.

Out-of-order and duplicate event delivery should be tested explicitly, since
most transport layers underneath a Process Manager (queues, event streams)
offer at-least-once, not exactly-once, delivery by default. a correct process
manager either ignores a duplicate transitively (idempotent transition
application keyed on event id) or the test suite should assert that a
duplicate does not double-apply a compensating action or double-charge a
downstream participant.

For BPMN or state-machine-engine implementations, most engines (Camunda's test
framework being the visible example) offer time-travel or timer-skipping test
utilities specifically so that a process with a multi-day wait state can be
tested in milliseconds by advancing the engine's simulated clock rather than
sleeping the test thread, which is worth reaching for over hand-rolled
timeout mocking when the underlying engine provides it.

## 16. Observability signals

A healthy process manager shows a stable distribution of instance states, most
instances moving steadily from a start state toward a terminal state within an
expected time window, and a low, roughly constant count of instances parked in
any single intermediate state relative to overall throughput. The signals
worth alerting on, drawn from operating this class of system in production.

Instance age distribution per current state, alerting when the 95th or 99th
percentile time spent in any single non-terminal state exceeds its expected
service level, which is the earliest and cheapest way to catch the timeout
amnesia failure mode from dimension 11 before a customer notices.

Transition rejection rate, counting events that arrived but did not match a
valid transition for the instance's current state, which surfaces both
correlation bugs (an event landing on the wrong instance) and out-of-order
delivery problems (an event arriving for a state the instance has already
moved past).

Dead-lettered or uncorrelated event count, tracking messages that carried a
correlation identifier the process manager could not resolve to any known
instance at all, distinct from a rejected transition, and a strong signal of
either a bug in identifier propagation or a participant emitting events for
processes that were never started.

Compensation and rollback rate, since Process Manager implementations that
also handle Saga-style compensation should treat a rising compensation rate
as a leading indicator of a failing downstream participant, worth its own
dashboard separate from the raw error rate, because compensations are the
system working correctly under failure, not the failure itself.

## 17. Security and privacy implications

A Process Manager's persisted state is, by construction, a durable record of
every business transaction that has passed through it, correlation
identifiers, intermediate results, and often the full payload of every
command and event exchanged. This makes the process manager's state store a
concentrated target and a concentrated compliance surface, distinct from any
single participant service, because it aggregates data that no individual
participant would otherwise hold in one place.

Where a process handles personal data subject to deletion rights (GDPR-style
erasure requests), the process manager's own history and audit log must be
included in that deletion scope, not only the participant services' own
databases, since the process manager's state and history frequently outlive
any single participant's retention window by design, that durability being
the pattern's core feature.

Access to a process manager's administrative surface, the ability to
manually advance, retry, or cancel an in-flight instance, is a real
privilege, since it can be used to bypass business rules encoded in the
process definition (forcing a shipment past a fraud hold, for example), and
should be scoped and audited separately from ordinary read access to instance
state.

This dimension is largely analytical judgement about the pattern's shape,
rather than a claim about any specific product's security posture, and does
not name a documented vulnerability in any of the systems cited in dimension
9.

## 18. References

- Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, System
  Management chapter, Process Manager.
- Enterprise Integration Patterns companion site, Process Manager, [enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html), verified 2026-08-02.
- OASIS, *Web Services Business Process Execution Language Version 2.0*, 11 April 2007, orchestration semantics of WS-BPEL as an executable, engine-driven process language.
- Amazon Web Services, "What is Step Functions", AWS Step Functions Developer Guide, [docs.aws.amazon.com/step-functions/latest/dg/welcome.html](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html), verified 2026-08-02.
- Camunda, Platform overview, [camunda.com/platform](https://camunda.com/platform/), verified 2026-08-02.
- Conductor OSS, project README, [github.com/conductor-oss/conductor](https://raw.githubusercontent.com/conductor-oss/conductor/main/README.md), verified 2026-08-02.
- Chris Richardson, *Microservices Patterns. With Examples in Java*, Manning, 2018, chapter 4, the Saga pattern and orchestrated versus choreographed compensation.

## Code examples

### TypeScript

```typescript
type OrderEvent =
  | { type: "InventoryReserved"; orderId: string }
  | { type: "PaymentConfirmed"; orderId: string }
  | { type: "PaymentDeclined"; orderId: string }
  | { type: "ShipmentDispatched"; orderId: string };

type OrderState = "STARTED" | "AWAITING_PAYMENT" | "READY_TO_SHIP" | "COMPLETED" | "COMPENSATING";

interface Instance {
  orderId: string;
  state: OrderState;
  history: string[];
}

type Command = { participant: string; action: string; orderId: string };

class OrderProcessManager {
  private instances = new Map<string, Instance>();

  private get(orderId: string): Instance {
    let inst = this.instances.get(orderId);
    if (!inst) {
      inst = { orderId, state: "STARTED", history: [] };
      this.instances.set(orderId, inst);
    }
    return inst;
  }

  handle(event: OrderEvent): Command[] {
    const inst = this.get(event.orderId);
    inst.history.push(event.type);
    const commands: Command[] = [];

    if (inst.state === "STARTED" && event.type === "InventoryReserved") {
      inst.state = "AWAITING_PAYMENT";
      commands.push({ participant: "payment", action: "charge", orderId: inst.orderId });
    } else if (inst.state === "AWAITING_PAYMENT" && event.type === "PaymentConfirmed") {
      inst.state = "READY_TO_SHIP";
      commands.push({ participant: "shipping", action: "ship", orderId: inst.orderId });
    } else if (inst.state === "AWAITING_PAYMENT" && event.type === "PaymentDeclined") {
      inst.state = "COMPENSATING";
      commands.push({ participant: "inventory", action: "release", orderId: inst.orderId });
    } else if (inst.state === "READY_TO_SHIP" && event.type === "ShipmentDispatched") {
      inst.state = "COMPLETED";
    }
    return commands;
  }
}

function main(): void {
  const pm = new OrderProcessManager();
  const orderId = "order-4471";
  console.log(pm.handle({ type: "InventoryReserved", orderId }));
  console.log(pm.handle({ type: "PaymentConfirmed", orderId }));
  console.log(pm.handle({ type: "ShipmentDispatched", orderId }));
}

main();
```

### Python

```python
from dataclasses import dataclass, field


@dataclass
class Instance:
    order_id: str
    state: str = "STARTED"
    history: list = field(default_factory=list)


@dataclass
class Command:
    participant: str
    action: str
    order_id: str


class OrderProcessManager:
    def __init__(self) -> None:
        self._instances: dict[str, Instance] = {}

    def _get(self, order_id: str) -> Instance:
        if order_id not in self._instances:
            self._instances[order_id] = Instance(order_id=order_id)
        return self._instances[order_id]

    def handle(self, event_type: str, order_id: str) -> list[Command]:
        inst = self._get(order_id)
        inst.history.append(event_type)
        commands: list[Command] = []

        if inst.state == "STARTED" and event_type == "InventoryReserved":
            inst.state = "AWAITING_PAYMENT"
            commands.append(Command("payment", "charge", order_id))
        elif inst.state == "AWAITING_PAYMENT" and event_type == "PaymentConfirmed":
            inst.state = "READY_TO_SHIP"
            commands.append(Command("shipping", "ship", order_id))
        elif inst.state == "AWAITING_PAYMENT" and event_type == "PaymentDeclined":
            inst.state = "COMPENSATING"
            commands.append(Command("inventory", "release", order_id))
        elif inst.state == "READY_TO_SHIP" and event_type == "ShipmentDispatched":
            inst.state = "COMPLETED"

        return commands


def main() -> None:
    pm = OrderProcessManager()
    order_id = "order-4471"
    print(pm.handle("InventoryReserved", order_id))
    print(pm.handle("PaymentConfirmed", order_id))
    print(pm.handle("ShipmentDispatched", order_id))
    print(pm._get(order_id))


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import "fmt"

type Instance struct {
	OrderID string
	State   string
	History []string
}

type Command struct {
	Participant string
	Action      string
	OrderID     string
}

type OrderProcessManager struct {
	instances map[string]*Instance
}

func NewOrderProcessManager() *OrderProcessManager {
	return &OrderProcessManager{instances: make(map[string]*Instance)}
}

func (pm *OrderProcessManager) get(orderID string) *Instance {
	inst, ok := pm.instances[orderID]
	if !ok {
		inst = &Instance{OrderID: orderID, State: "STARTED"}
		pm.instances[orderID] = inst
	}
	return inst
}

func (pm *OrderProcessManager) Handle(eventType, orderID string) []Command {
	inst := pm.get(orderID)
	inst.History = append(inst.History, eventType)
	var commands []Command

	switch {
	case inst.State == "STARTED" && eventType == "InventoryReserved":
		inst.State = "AWAITING_PAYMENT"
		commands = append(commands, Command{"payment", "charge", orderID})
	case inst.State == "AWAITING_PAYMENT" && eventType == "PaymentConfirmed":
		inst.State = "READY_TO_SHIP"
		commands = append(commands, Command{"shipping", "ship", orderID})
	case inst.State == "AWAITING_PAYMENT" && eventType == "PaymentDeclined":
		inst.State = "COMPENSATING"
		commands = append(commands, Command{"inventory", "release", orderID})
	case inst.State == "READY_TO_SHIP" && eventType == "ShipmentDispatched":
		inst.State = "COMPLETED"
	}
	return commands
}

func main() {
	pm := NewOrderProcessManager()
	orderID := "order-4471"
	fmt.Println(pm.Handle("InventoryReserved", orderID))
	fmt.Println(pm.Handle("PaymentConfirmed", orderID))
	fmt.Println(pm.Handle("ShipmentDispatched", orderID))
	fmt.Printf("%+v\n", pm.get(orderID))
}
```

Java and Rust were not attempted for this entry, since the state-machine shape
translates directly and without idiom-specific variation from the three
languages above, and three verified, runnable languages already satisfy the
repository requirement.
