---
name: Process Manager
slug: process-manager
family: 11-ddd
category: Behavioral
aliases: [Orchestrator, Saga Orchestrator, Central Coordinator]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [saga, mediator, state-machine, aggregate, event-sourcing, command]
incompatible_with: [choreography]
verified: 2026-08-02
---

# Process Manager

## 1. Name, aliases, and lineage

The canonical name is Process Manager, catalogued by Gregor Hohpe and Bobby
Woolf in *Enterprise Integration Patterns. Designing, Building, and Deploying
Messaging Solutions*, Addison-Wesley, 2003, in the Message Routing chapter. The
pattern's own page states the intent directly. "How do we route a message
through multiple processing steps when the required steps may not be known at
design time and may not be sequential." The solution is to "use a central
processing unit, a Process Manager, to maintain the state of the sequence and
determine the next processing step based on intermediate results"
(enterpriseintegrationpatterns.com, Process Manager,
https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html,
verified 2026-08-02). The book frames Process Manager as the stateful, dynamic
sibling of Routing Slip, which encodes a fixed sequence of steps into the
message itself rather than deciding the next step live.

The most common alias in day to day engineering conversation is Orchestrator,
used interchangeably with Process Manager in nearly every workflow engine's own
documentation, including Temporal, Camunda, and AWS Step Functions. Inside the
distributed transaction literature the same shape carries a third name, Saga
Orchestrator, coined when the Saga pattern (Hector Garcia Molina and Kenneth
Salem, "Sagas", ACM SIGMOD Record, 1987) was adapted to microservices and split
into two implementation styles, orchestration and choreography. NServiceBus,
MassTransit, and Eventuate all name their stateful coordinator class Saga, and
that class is a Process Manager applied specifically to compensating a
multi-step business transaction. Central Coordinator appears in older
distributed systems papers describing the same structural idea outside a
messaging context, most visibly in two phase commit coordinators, though two
phase commit is a narrower, blocking protocol rather than a general
long-running workflow pattern and the two should not be conflated.

Three things frequently get called a Process Manager and only one of them is.

- **Process Manager (Hohpe and Woolf, stateful, dynamic).** A component that
  owns durable state for one instance of a business process, receives events or
  replies, and decides the next step from that state plus the incoming message.
  The decision logic can change at runtime because it is code, not a fixed list.
- **Routing Slip (Hohpe and Woolf, stateless, static).** A predetermined
  ordered list of steps attached to the message itself. Each processing station
  reads the list, does its step, and forwards to the next entry. There is no
  central component holding state, and the sequence cannot branch based on an
  intermediate result unless the slip itself is rewritten mid-flight.
- **Choreography (no central coordinator).** Every service reacts to events
  published by other services and decides its own next action locally. No
  single place holds the full sequence. This is the structural opposite of
  Process Manager, not a variant of it, and the two are frequently compared as
  alternatives for the same problem, see dimension 4 and dimension 12.

## 2. Problem and context

A business process spans more than one service, more than one aggregate, or
more than one external system, and it cannot complete in a single local
transaction. A customer places an order that must reserve inventory, charge a
payment provider, and schedule a shipment. Each of those three actions lives in
a different bounded context with its own database, so a single ACID transaction
across all three is either impossible, because the systems are literally
separate processes over a network, or architecturally forbidden, because
coupling three services to one distributed transaction manager defeats the
reason they were split apart in the first place.

The process also takes real time to run. Payment authorization can take
seconds. A warehouse reservation can take minutes if it depends on a batch job.
A shipment carrier's booking API can be down and need a retry with backoff over
hours. Somewhere between the request coming in and the process finishing, the
service instance that started the work will very likely have restarted,
redeployed, or been load balanced to a different node. The state of "we
reserved inventory, we are waiting on payment" has to survive that, or the
process silently stalls with no path back to consistency.

Finally, the steps are not always a straight line. Payment can be declined, in
which case inventory must be released rather than shipment being scheduled.
Inventory can be short, in which case a partial fulfilment or a backorder path
runs instead of the happy path. The routing decision depends on results that
are not known until earlier steps have replied, which rules out a pattern that
only knows how to run a fixed list forward.

The context that makes Process Manager the right answer has three parts, and
all three usually need to be true together. The process crosses more than one
service or bounded context. The process is long running relative to a single
request, meaning it survives more than one message exchange and must persist
between them. The routing decision genuinely branches on results the process
manager does not have until an earlier step replies. Outside that context, see
dimension 4, a different pattern is usually cheaper.

## 3. Forces

- **Consistency.** Favoured, but only eventual consistency. The pattern trades
  atomic all-or-nothing transactions for a sequence of local transactions each
  compensated on failure, see the Saga entry. There is a window, sometimes
  visible to a user, where the world is in an intermediate state.
- **Visibility of the process.** Strongly favoured. The entire sequence of a
  business process, including its branches and compensations, is readable in
  one place, the process manager's own code and its persisted state, rather
  than reconstructed by reading event handlers scattered across every
  participating service.
- **Coupling.** Sacrificed toward the coordinator. Every participant that the
  process manager calls becomes a dependency of the process manager, and the
  process manager becomes a single place that knows the shape of the whole
  process. Participants themselves stay decoupled from each other, since they
  never call one another directly, only the coordinator.
- **Single point of failure and bottleneck.** Sacrificed. If the coordinator's
  state store or the coordinator process itself is unavailable, no instance of
  that process type can advance. This is why the state has to be durable and
  the coordinator itself stateless between invocations, see dimension 8.
- **Operability.** Favoured overall. One dashboard can show every in-flight
  process instance and its current step, which is close to impossible with
  choreography, where the same question means correlating logs across every
  service that might have participated.
- **Team topology.** Mixed. Favoured for a team that owns an entire business
  process end to end and wants one artefact to reason about it. Sacrificed for
  teams organised strictly around bounded contexts, because the process manager
  now needs to know something about every participating context's contract,
  which is exactly the kind of cross-team knowledge a bounded context boundary
  is meant to avoid concentrating in one place.
- **Cost of change.** Favoured for changing the sequence itself, since the
  branching logic lives in one component and one deployment. Sacrificed for
  adding a genuinely new independent reaction to an existing event, since
  choreography lets any service subscribe without touching the others while
  orchestration requires editing the coordinator.
- **Latency.** Sacrificed relative to choreography for the steady state. Every
  step's reply round trips through the coordinator before the next command is
  issued, adding a hop that a direct event subscription does not pay.

A pattern that gave up nothing would not be a trade, it would be a free lunch.
The price here is a concentrated dependency and an added hop, paid to buy
visibility and a place to put branching logic that would otherwise be smeared
across every participant.

## 4. Applicability and non-applicability

Reach for Process Manager when the following hold together.

- The business process spans more than one bounded context, service, or
  external system, and no single local transaction can cover it.
- The process is long running across more than one message exchange, and its
  state must survive a restart or redeploy of the coordinating component.
- The next step genuinely depends on the outcome of a previous step, so the
  sequence cannot be encoded as a fixed list decided in advance.
- Compensating actions are required on partial failure, meaning some steps
  already completed must be undone or offset rather than simply retried.
- One team or one system owns the process end to end and benefits from a
  single artefact that shows the whole sequence, including its failure paths.
- Operators need to answer, for any in-flight instance, which step it is on and
  why, without correlating logs across several services.

Do NOT reach for Process Manager in these cases, and the reason matters more
than the rule.

- **The steps are a fixed, known sequence with no branching.** A Routing Slip,
  or simply a pipeline of function calls, does the same job with no persisted
  state and no coordinator to keep alive. Adding a Process Manager here buys a
  database table and a state machine for a sequence that never varies.
- **The steps all belong to one bounded context and can share one local
  transaction.** A single database transaction inside one aggregate, or a
  Unit of Work spanning one service's own tables, is strictly simpler and
  gives real atomic consistency instead of eventual consistency. Reaching for
  Process Manager here trades a real guarantee for a weaker one for no reason.
- **Each participant can react to an event independently with no shared
  outcome to track.** If nothing needs to know the process finished, or the
  finishing condition is "every subscriber that cares has reacted", plain
  publish and subscribe, choreography, is lighter and adds no coordinator to
  keep alive. See dimension 12 for exactly where the line sits.
- **The process completes within the lifetime of a single request and needs
  no persistence between steps.** An in-process pipeline, or a plain sequence
  of awaited calls inside one handler, does the job. Persisting state for a
  process that finishes in milliseconds is waste.
- **A workflow engine already exists in the stack and the process is simple
  linear automation with no cross-service compensation.** A rules engine or a
  simple background job queue may fit better than either the pattern by hand
  or a full orchestration platform.
- **The number of independently evolving reactions is expected to grow
  without bound and no one component should need to know all of them.** A
  notification fan-out where new subscribers are added by teams who should
  never need to touch a central coordinator is the choreography case, not
  this one.

## 5. Structure

Four participants, named by the role they play in the messaging literature and
carried forward largely unchanged into modern orchestration frameworks.

- **Process Manager.** Owns the durable state for one running instance of the
  process, evaluates each incoming reply or event against that state, and
  decides the next command to issue. It is stateful across invocations but
  each individual invocation is a short, resumable step, not a long-lived
  thread blocking on I/O, see dimension 8.
- **Process State (or Saga Data).** The persisted record of where this
  instance of the process is, what it has already done, and what it is
  waiting on. In Hohpe and Woolf's terms this is what lets the Process Manager
  resume correctly after a restart, since the state, not an in-memory stack
  frame, is the source of truth for progress.
- **Participant.** A service, aggregate, or external system that performs one
  step of the process on command from the Process Manager and reports back a
  result, either synchronously as a reply or asynchronously as an event the
  Process Manager subscribes to.
- **Correlation Identifier.** The value that lets an incoming reply be matched
  back to the correct in-flight Process State. Every message that is part of
  a process instance carries this identifier, and the Process Manager's
  message handling infrastructure uses it to load the right state before
  invoking any decision logic. Getting this identifier wrong is the single
  most common cause of the failure modes in dimension 11.

The relationship shape is a hub and spoke. The Process Manager sits at the
centre and holds the only knowledge of the full sequence. Participants never
call each other, and in a correctly built system a participant does not even
know it is part of a larger process, it only knows it received a command and
must reply or publish a result.

## 6. ASCII structure diagram

```
                      +---------------------------------------+
                      |             Process Manager            |
                      |-----------------------------------------|
                      | + handle(TriggerEvent)                  |
                      | + handle(ReplyOrEvent)                  |
                      | - decideNextStep(ProcessState): Command |
                      +---------------------------------------+
                            |          ^            |
                       loads/saves     |    issues Command
                            v          |            v
                +-----------------+    |   +--------------------+
                |  Process State  |    |   |    Participant A    |
                |-----------------|    |   |----------------------|
                | correlationId   |    |   | + handleCommand()    |
                | currentStep     |    |   | -> publishes Reply   |
                | completedSteps  |    +---|   or ResultEvent     |
                | payload         |        +--------------------+
                +-----------------+
                            ^
                            |               +--------------------+
                            +---------------|    Participant B    |
                                            |----------------------|
                                            | + handleCommand()    |
                                            | -> publishes Reply   |
                                            |   or ResultEvent     |
                                            +--------------------+

  Correlation Identifier travels on every Command and every Reply,
  and is the key used to load Process State before decideNextStep runs.
```

## 7. Dynamics

The runtime flow is event driven and resumable, never a single blocking call
stack. Each arrow into the Process Manager is a separate invocation that loads
state, runs decision logic, saves state, and returns, which is what allows the
process to survive a crash between any two steps.

```
Client        Process Manager        Process State store       Participant A     Participant B
  |                  |                        |                       |                 |
  |-- Start(orderId)->|                        |                       |                 |
  |                  |-- create + save state ->|                       |                 |
  |                  |<-- ack -----------------|                       |                 |
  |                  |-- ReserveInventory ----------------------------->|                 |
  |                  |                        |                       |                 |
  |          (process manager instance may terminate or redeploy here, state persists)
  |                  |                        |                       |                 |
  |                  |<-- InventoryReserved --------------------------|                 |
  |                  |-- load state by correlationId --------->|                       |                 |
  |                  |<-- state (step = reserving) -------------|                       |                 |
  |                  |-- decideNextStep(state, reply) -> ChargePayment                  |                 |
  |                  |-- save state (step = charging) --------->|                       |                 |
  |                  |-- ChargePayment ------------------------------------------------->|
  |                  |                        |                       |                 |
  |                  |<-- PaymentDeclined ------------------------------------------------|
  |                  |-- load state ---------->|                       |                 |
  |                  |-- decideNextStep(...) -> ReleaseInventory (compensation)          |
  |                  |-- ReleaseInventory ----------------------------->|                 |
  |                  |<-- InventoryReleased ----------------------------|                 |
  |                  |-- save state (step = failed) ----------->|                       |
  |<-- OrderFailed --|                        |                       |                 |
```

Two timing properties matter for correctness. First, the Process Manager must
be idempotent per correlation identifier and step, because at-least-once
message delivery, the norm in every message broker used for this pattern, will
redeliver a reply after a timeout even when the first delivery was actually
processed. A Process Manager that issues ChargePayment twice for one order
because a reply was redelivered is a production incident, not a theoretical
risk. Second, the state must be loaded and saved atomically with respect to
issuing commands, typically inside the same database transaction as an
outbox write, or the process can crash between deciding a next step and
persisting that decision, leaving state that says step A finished while no
command for step B was ever actually sent.

## 8. Implementation variants

**Hand-rolled state machine with explicit persistence.** A class with an
explicit state field, a switch or pattern match over current state plus
incoming event type, and a repository that loads and saves the state row
transactionally around each handled message. This is the closest to Hohpe and
Woolf's original description and the variant every framework beneath it
ultimately compiles down to.

**Saga base class in a messaging framework.** NServiceBus's `Saga<TData>` and
MassTransit's `MassTransitStateMachine<TInstance>` give the developer a
correlation configuration, a persisted data class, and a set of message
handlers, while the framework owns loading, locking, and saving the saga
instance around each handled message. NServiceBus documents this directly.
"Any process that involves multiple network calls has an interim state. Using
NServiceBus, it is possible to explicitly define the data used for this state
by inheriting from the ContainSagaData abstract class" (Particular Software,
NServiceBus documentation, Sagas,
https://docs.particular.net/nservicebus/sagas/, verified 2026-08-02). This
variant removes almost all of the plumbing at the cost of coupling the process
logic to the messaging framework's saga base class.

**Durable execution as code.** Temporal, and the older Amazon Simple Workflow
it is spiritually descended from, let the developer write the process as
ordinary sequential code, an `async` function calling activities in order and
branching with normal `if` statements, and the platform durably records every
step so the function can be transparently replayed from an event history after
a crash rather than the developer hand-writing a state machine. Temporal's own
documentation frames this precisely. "A workflow defines a sequence of steps"
and after a failure the platform "starts the Workflow code from the beginning,
replays the Event History step by step" to restore the exact pre-failure state
before continuing (Temporal Technologies, Temporal documentation, Workflows,
https://docs.temporal.io/workflows, verified 2026-08-02). This is Process
Manager with the state machine and the persistence both made implicit by the
runtime, at the cost of the code only being safely re-executable if it is kept
deterministic, no direct system clock reads, no unrecorded random values,
inside the workflow function itself.

**Declarative state machine or JSON workflow definition.** AWS Step Functions
and Camunda BPMN both let the sequence, including branches and error
handlers, be described in a data file rather than imperative code, and the
platform interprets that definition per instance. This trades code flexibility
for a visual, auditable artefact that a non-developer can review, and for a
built-in execution history UI, at the cost of expressing complex branching
logic in a domain specific language rather than a general purpose one.

**Aggregate acting as its own process manager.** In a strict DDD codebase, a
long running Aggregate can hold the process state as part of its own invariant
and react to domain events by raising the next command, blurring the line
between Aggregate and Process Manager. This works when the process state is
naturally owned by one aggregate's lifecycle, and breaks down the moment the
process must coordinate across more than one aggregate root, at which point a
dedicated Process Manager separate from any single aggregate is the honest
shape, see dimension 13.

**Timer driven polling variant.** Where the participants have no event or
callback mechanism at all, only a query API, the Process Manager is instead
woken on a timer, polls each participant's current status, and advances state
based on what it observes. Functionally identical decision logic, higher
latency, and no dependency on message delivery guarantees from participants
that were never built to publish one.

## 9. Known production uses

**NServiceBus Sagas, Particular Software.** NServiceBus ships a first class
`Saga<TSagaData>` base class specifically implementing the Process Manager
pattern for long running business processes, with declared message
correlation and a `ContainSagaData` persisted state contract, used across
production .NET service meshes for order processing and similar multi step
workflows. Particular Software, NServiceBus documentation, Sagas,
https://docs.particular.net/nservicebus/sagas/, verified 2026-08-02.

**MassTransit Saga State Machines, .NET.** MassTransit's
`MassTransitStateMachine<TInstance>` implements the same coordinator role on
top of a message bus abstraction over RabbitMQ, Azure Service Bus, and Amazon
SQS, with declarative `During`, `When`, and `TransitionTo` state machine
syntax that compiles to exactly the load, decide, save cycle described in
dimension 7. MassTransit documentation, Saga State Machines,
https://masstransit.io/documentation/patterns/saga/state-machine, verified
2026-08-02.

**Temporal Workflows, Temporal Technologies.** Temporal's Workflow Execution
model is a durable execution implementation of Process Manager, coordinating
long running Activities across services with automatic state recovery via
Event History replay, used in production by companies including Netflix,
Snap, and Stripe for exactly the multi step, crash-surviving processes this
pattern targets. Temporal Technologies, Temporal documentation, Workflows,
https://docs.temporal.io/workflows, verified 2026-08-02.

**AWS Step Functions.** Step Functions state machines coordinate AWS Lambda
functions and other AWS services as a sequence of States with explicit
branching, retry, and Catch error handling, persisted by the service itself
between steps so a state machine execution survives independently of any
single Lambda invocation's lifetime, which is the durable coordinator role of
a Process Manager delivered as a managed AWS service. Amazon Web Services,
AWS Step Functions Developer Guide, "What is AWS Step Functions",
https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html, verified
2026-08-02.

## 10. Consequences

Positive.

- The full sequence of a multi step business process, including its branches
  and its compensating actions, is visible in one place rather than
  reconstructed by reading event handlers scattered across every participant.
- The process survives a restart, a redeploy, or a crash of the coordinating
  component, because progress lives in durable Process State rather than in
  memory or on a call stack.
- Adding a new step to an existing sequence, or changing a branching
  condition, is a change to one component rather than a coordinated change
  across every participant that would otherwise each hold a fragment of the
  routing logic.
- Compensation logic for partial failure has a natural home, since the
  Process Manager already knows exactly which steps have completed and in
  what order, information a purely choreographed system has to reconstruct.
- Operators can build one dashboard, or use one built-in execution history
  view in platforms like Temporal or Step Functions, to answer what state any
  in-flight process instance is in and why.

Negative.

- The Process Manager becomes a single component that must know the contract
  of every participant it coordinates, concentrating cross-context knowledge
  that a services-organised team structure is otherwise designed to avoid.
- Availability of the coordinator, and of its state store, becomes a
  dependency for every in-flight instance of that process. An outage there
  stalls every running process of that type at once, unlike choreography
  where each participant can keep processing its own local work.
- Every step's reply must round trip through the coordinator before the next
  command is issued, adding a hop of latency compared to a participant
  reacting directly to another participant's event.
- The persisted Process State schema becomes a long-lived contract in its own
  right, since instances created under an older schema version must still be
  loadable and resumable after a deployment changes the schema, see
  dimension 11.
- Participants that are called by the same Process Manager gain an implicit
  dependency on each other through the coordinator's sequencing even though
  they never call each other directly, and a bug in the sequencing can leave
  the world in an inconsistent cross-service state that no single
  participant's own logs will fully explain.

## 11. Failure modes and misuse

**Correlation identifier mismatch.** Symptom. A reply arrives and either no
Process State is found for it, so the process silently never advances, or the
wrong Process State is found and updated, corrupting an unrelated instance.
Cause. The correlation configuration on the receiving side does not match the
identifier the participant actually returns, often after a participant's
message schema changes and the correlated field is renamed without updating
the Process Manager's mapping. Fix. Treat the correlation contract as a
versioned interface between the Process Manager and each participant, and add
a test, see dimension 15, asserting every participant reply type resolves to
the correct saga instance.

**Non-idempotent command issuance under at-least-once delivery.** Symptom. A
customer is charged twice, or a warehouse reservation is made twice, for one
order. Cause. The same reply message is delivered a second time, most often
after a broker level timeout on the first delivery's acknowledgement, and the
Process Manager's decision logic runs again from the same prior state and
issues the same command again. Fix. Make command issuance idempotent using a
deterministic idempotency key derived from the correlation identifier and the
step, so the downstream participant can reject or deduplicate a repeat.

**State and command issuance not committed atomically.** Symptom. The
Process State record says a step completed and the next command was issued,
but the downstream participant never received it, or the reverse, the command
went out but the process crashed before the state update was saved, so the
same step runs again on the next redelivery. Cause. Saving the updated
Process State and publishing the outgoing command happen as two separate,
unrelated operations rather than one atomic unit. Fix. Use the Transactional
Outbox pattern, writing the outgoing message to an outbox table in the same
database transaction as the state update, with a separate relay process
publishing from the outbox.

**God orchestrator.** Symptom. One Process Manager class grows to coordinate
a dozen unrelated business capabilities, becomes the file every team on the
codebase has open a pull request against in a given week, and a change to one
process's branching risks breaking an unrelated process that happens to share
the class. Cause. Every new cross-service workflow was added to an existing
coordinator instead of getting its own, because it already existed and
seemed to need only one more step. Fix. Split by business process, one Process
Manager type per distinct process, even when two processes share a
participant.

**Compensation that assumes a step it never confirmed.** Symptom. A
compensating action, for example releasing an inventory reservation, is
issued for a step whose original command was sent but whose success reply
was never actually received, and the compensation fails or is a no-op
against a reservation that was never actually made. Cause. The Process
Manager tracks "command sent" rather than "step confirmed complete" as its
signal for what needs compensating. Fix. Track confirmed completion
separately from command issuance in the Process State, and make
compensation logic tolerant of compensating a step that turns out never to
have actually succeeded.

**Schema drift on long-lived instances.** Symptom. A deployment changes the
shape of the Process State class, and every in-flight instance created
before the deployment fails to deserialize, or worse, deserializes with a
new field silently defaulted in a way that corrupts the decision logic.
Cause. The Process State persistence format was treated as internal
implementation detail rather than as a schema requiring migration
discipline, and a process that can legitimately run for days or weeks
outlives the deployment that changed its shape. Fix. Version the Process
State schema explicitly and write a migration or an upcasting step for
in-flight instances, the same discipline event-sourced aggregates require
for their event schemas.

**Choreography and orchestration mixed for the same process.** Symptom. Part
of a business process is coordinated by an explicit Process Manager and part
is left to participants independently reacting to events published mid
process, and nobody can say from reading the code alone what triggers the
final step, because the answer depends on a race between the orchestrator's
own next command and an independent subscriber's reaction. Cause. A
Process Manager was introduced onto an already-choreographed system
incrementally, and the boundary between the two coordination styles was
never made explicit. Fix. Pick one coordination style per process and be
explicit about the boundary where a Process Manager hands off to
independent choreography, if it must, documenting exactly which events are
still consumed outside the coordinator's control.

## 12. Trade-off matrix

Compared against named alternatives for coordinating a multi step business
process, across the forces from dimension 3.

| Force | Process Manager (Orchestration) | Choreography | Routing Slip | Two Phase Commit | Manual Saga (hand rolled) | Aggregate as coordinator |
|---|---|---|---|---|---|---|
| Consistency model | Eventual, with explicit compensation | Eventual, compensation implicit and distributed | Eventual, no compensation built in | Strong, atomic across participants | Eventual, same as orchestrated Process Manager | Eventual within aggregate's own transaction boundary |
| Central visibility of the sequence | High. One place shows the whole flow | Low. Sequence emerges from independent handlers | Medium. The slip lists steps but not why | High for the duration of the commit, then gone | High if disciplined, same code shape as framework version | Medium. Visible inside the aggregate, invisible outside it |
| Coupling to participants | High at the coordinator, low between participants | Low everywhere, no shared knowledge of the whole | Medium. Each station knows only its own step | High. Every participant must support the protocol | High at the coordinator, same as framework Process Manager | High between the aggregate and any second aggregate it must reach |
| Blast radius of coordinator outage | Every in-flight instance of that process stalls | None. Each participant keeps processing independently | Low. Message carries its own routing | Total. Commit protocol blocks all participants | Same as framework Process Manager | Limited to processes owned by that aggregate instance |
| Adding a new independent reaction | Requires editing the coordinator | Free. New subscriber, no edits elsewhere | Requires editing every slip template | Not applicable, fixed set of participants | Requires editing the coordinator | Requires editing the aggregate |
| Branching on intermediate results | Native, that is the pattern's purpose | Possible but implicit, scattered across handlers | Poor, the slip is largely fixed at creation | Not applicable, all or nothing | Native, same as framework version | Native, within the aggregate's own scope |
| Operational cost | Coordinator process plus durable state store | No coordinator, but harder to trace failures | Lightweight, no coordinator state | Locking overhead, blocking, rarely used across networks today | Same infrastructure cost as framework Process Manager | Reuses the aggregate's existing persistence |
| Testability of the full flow | High, one component to drive end to end | Low, must assemble every participant to see the flow | Medium | Low, requires all participants live | High, same as framework version | Medium, entangled with the aggregate's other invariants |

Reading of the table. Process Manager wins wherever a human or an operator
needs to see and reason about the whole sequence in one place, and wherever
branching genuinely depends on intermediate results. Choreography wins where
independent evolution of reactions matters more than central visibility, and
where no single outcome needs to be tracked as a whole. Two Phase Commit wins
only when true atomicity is achievable and the participants are willing to
hold locks, which is rare across service boundaries and effectively unused
for the cross-service case this entry targets. Routing Slip wins when the
sequence is fixed and no branching or compensation is needed. An Aggregate
acting as its own coordinator wins when the process genuinely never needs to
reach outside that aggregate's own boundary.

## 13. Related and incompatible patterns

- **Saga.** The closest relative and, in the microservices literature, often
  treated as a near-synonym. Saga names the overall strategy of a sequence of
  local transactions with compensating actions for failure. Process Manager
  is one of the two ways to implement a Saga, the orchestrated way, with
  Choreography being the other. Every orchestrated Saga is a Process Manager,
  but Process Manager as Hohpe and Woolf describe it predates and is broader
  than the Saga literature, since it also covers processes with no
  compensation requirement at all.
- **Mediator.** Structurally similar, a central component through which other
  components communicate rather than talking to each other directly, which is
  exactly the hub and spoke shape from dimension 5. The difference is
  temporal scope. Mediator coordinates a single, typically synchronous,
  interaction among objects in one process. Process Manager coordinates a
  long running, asynchronous, persisted sequence across process and service
  boundaries. A Process Manager is a Mediator with durability and time added.
- **State Machine.** The decision logic inside a Process Manager is almost
  always literally a state machine, current state plus incoming event
  determines next state and next action. Frameworks like MassTransit make
  this explicit by building the saga directly on a state machine DSL. The
  distinction is that a bare State Machine pattern says nothing about
  persistence or cross-service commands, both of which Process Manager adds.
- **Aggregate (DDD).** Complementary and occasionally confused. An Aggregate
  enforces invariants within one consistency boundary using one local
  transaction. A Process Manager coordinates across more than one
  consistency boundary using eventual consistency and compensations. A
  Process Manager frequently issues commands that each target a different
  Aggregate, and should never itself try to enforce another aggregate's
  invariants directly, that responsibility stays with the aggregate.
- **Event Sourcing.** Composes cleanly and is the storage mechanism several
  production Process Manager implementations use for their own Process
  State, including Temporal's Event History, which is itself an event log
  the workflow's state is derived from by replay. Event Sourcing is not
  required for a Process Manager, a plain mutable state row is equally
  valid, but the two share the same replay-for-recovery idea.
- **Command.** The Process Manager's output at each step is naturally
  modelled as a Command object dispatched to a participant, giving a uniform
  shape for "the next thing to do" regardless of which participant receives
  it. This composes without friction.
- **Choreography.** Named directly incompatible in this entry's frontmatter
  because the two are structural opposites for coordinating the same kind
  of process, not because they can never coexist in one system. A single
  business process should pick one coordination style, see the mixed-style
  failure mode in dimension 11. Different processes within the same system
  can legitimately use different styles.
- **Two Phase Commit.** A different tool for a related problem, atomic
  cross-participant consistency rather than eventual consistency with
  compensation. Rarely composes with Process Manager in practice, since a
  system that can use Two Phase Commit usually does not need the
  compensation machinery a Process Manager exists to hold, and a system that
  needs Process Manager usually cannot use Two Phase Commit because its
  participants do not support the protocol across a public network boundary.

## 14. Refactoring path in and out

Introducing the pattern into a process that is currently implicit, typically
scattered across a chain of event handlers or an ad hoc sequence of direct
service calls inside one request handler.

1. Identify the actual instances of the process as a concept, what uniquely
   identifies one running instance, an order id, a subscription id, a case
   number. This becomes the correlation identifier.
2. Write down the current sequence of steps as they exist today, including
   every branch and every failure path, even the ones handled by ad hoc
   retries or manual operator intervention. This document is the
   specification the Process Manager will encode.
3. Introduce a Process State type holding the correlation identifier, the
   current step, and whatever payload the decision logic needs, and a
   repository or table to persist it. Do this before writing any decision
   logic, so the persistence contract is settled first.
4. Write the Process Manager's message handling for the trigger event only,
   creating and persisting a new Process State instance, without yet issuing
   any commands. Verify instances are created and persisted correctly.
5. Add the first command issuance and its corresponding reply handler,
   loading state by correlation identifier, deciding the next command, and
   saving state, one step at a time. Run the existing implicit flow and the
   new Process Manager side by side against a shadow traffic sample if the
   process is high stakes, comparing outcomes before cutting over.
6. Once every step and every branch from the specification in step 2 is
   represented, redirect the trigger event to the new Process Manager and
   retire the old implicit chain of handlers. Keep the old chain's code
   available, disabled, until the new coordinator has run in production
   through at least one full cycle of every branch, including the failure
   branches, which are usually the rarest and the last to be exercised.

Removing the pattern when the process it coordinates has become fixed,
simple, and single-context, meaning it no longer needs the general
capability the coordinator provides.

1. Confirm the branching has genuinely stabilised into a fixed sequence with
   no remaining data-dependent routing decisions. If any branch still
   depends on an intermediate result, this refactoring is premature.
2. Confirm every step the process touches has moved into, or could move
   into, a single bounded context or a single local transaction. If steps
   still genuinely span services, downgrading loses the compensation
   machinery those steps still need.
3. Replace the persisted Process State and its load, decide, save cycle with
   either a Routing Slip if steps still cross participants in a fixed
   order, or a plain sequential method call chain if everything now lives
   in one context.
4. Delete the correlation identifier plumbing and the state persistence
   schema once no in-flight instances under the old coordinator remain,
   verified by querying the state store for open instances before dropping
   the table.

## 15. Testing and verification

Easier because of the pattern.

- The entire process can be driven end to end in a single test by publishing
  the trigger event, then simulating each participant reply in sequence,
  and asserting the Process State and the outgoing commands at each step,
  with no need to stand up every real participant service.
- Compensation paths are directly testable by simulating a failure reply at
  any step and asserting the correct compensating commands are issued for
  exactly the steps that had already completed, and no others.
- Because the decision logic is a pure function of current state plus
  incoming event in the well factored form, see dimension 8, it can be unit
  tested without any messaging infrastructure at all, feeding state and
  event objects directly and asserting the resulting next command.

Harder because of the pattern.

- A correctness bug is only visible across the full sequence of messages,
  so a test that only exercises one handler in isolation can pass while the
  overall multi step flow is still broken by a correlation or ordering
  issue that only appears end to end.
- Concurrency and message ordering, specifically what happens when two
  replies for the same correlation identifier arrive out of order or
  concurrently, is genuinely hard to reproduce deterministically without a
  test setup built specifically to interleave message delivery.

Techniques that apply.

- **Saga or workflow test kit provided by the framework.** MassTransit ships
  a `SagaTestHarness` designed exactly for driving a state machine through a
  sequence of simulated messages and asserting the resulting state and sent
  messages without a real broker. Temporal ships a dedicated test
  environment that runs workflow code with time skipping, letting a test
  simulate days of elapsed process time in milliseconds while still
  exercising the real replay logic.
- **Correlation identifier mismatch test.** For every participant reply
  type, assert that a message with a given correlation value updates
  exactly the Process State instance created with the matching value, and
  no other instance, catching the failure mode from dimension 11 directly.
- **Idempotent redelivery test.** Deliver the same reply message twice to
  the handler and assert the resulting state and the set of outgoing
  commands are identical to delivering it once, directly exercising the
  at-least-once delivery failure mode.
- **Compensation coverage test.** For each step in the process, simulate a
  failure at that exact point and assert the correct subset of prior steps
  is compensated, building a table of step index to expected compensation
  set and asserting every row, rather than testing only the final failure
  point.
- **Schema migration test for in-flight instances.** Serialize a Process
  State instance using the previous schema version, run it through the
  current deserialization and decision logic, and assert it resumes
  correctly, directly guarding against the schema drift failure mode.

## 16. Observability signals

A Process Manager's entire value proposition is visibility into a distributed
process, so its own observability matters more than almost any other
pattern's.

What to record.

- On every state transition, a structured log line or span holding the
  correlation identifier, the previous step, the new step, and the event
  that triggered the transition, forming a per-instance timeline that can
  be reconstructed without joining across participant service logs.
- A gauge, per process type, of instance count by current step, which is
  the single most useful production signal, since it answers "where is
  everything stuck" at a glance.
- A histogram of time spent per step, per process type, so a step that has
  started taking materially longer than its historical baseline is visible
  before it becomes a customer facing incident.
- A counter of compensations issued, labelled by which step triggered the
  compensation, since a rising compensation rate for one specific step is
  the earliest signal that a downstream participant has started failing.
- A counter of duplicate or out-of-order reply deliveries observed and
  deduplicated, which validates the idempotency handling from dimension 11
  is actually engaging rather than silently being bypassed.
- For platforms with a built-in execution history, such as Temporal's
  Workflow history view or Step Functions' execution graph, treat that view
  as the primary debugging tool and confirm every custom-built alternative
  exposes an equivalent per-instance timeline.

A healthy instance on a dashboard. The instance-count-by-step gauge shows a
shape consistent with the expected duration of each step, most instances in
early steps, few in late ones, for a process whose steps take roughly
similar time, or a shape matching known step-duration differences otherwise.
The compensation counter sits near its historical baseline. Step duration
histograms show tight, stable distributions.

A failing instance. A single step's instance count climbs and does not
drain, meaning instances are entering that step but nothing is completing it,
which points directly at a stuck or unavailable participant for that step.
The compensation counter for one specific step spikes, localising a
downstream failure without reading any participant's own logs. The
duplicate-delivery counter climbs alongside a rise in process duration,
suggesting a participant is timing out and being retried by the messaging
infrastructure rather than genuinely failing. An instance whose per-instance
timeline shows a transition into a step with no corresponding transition out
of it for far longer than the step's historical duration is the direct,
per-case version of the aggregate stuck-step signal above.

## 17. Security and privacy implications

The Process Manager is a genuine, not incidental, security and privacy
surface, because it is by construction the one component that holds the
combined state of a business process spanning several systems, which is
usually exactly the combination of data an attacker or an unauthorised
insider would most want to read in one place.

**Aggregated sensitive data in one persisted record.** An order Process
State might hold, in one row, the customer identifier, the payment
authorization result, and the shipping address, three pieces of data that
individually live in three separate participant systems with three separate
access controls, now co-located in the coordinator's own state store. This
concentration is the direct consequence of the pattern's structure, not a
misuse of it, and it means the Process State store needs access controls,
encryption at rest, and a retention policy at least as strict as the
strictest of the systems whose data it aggregates, per applicable data
protection law such as GDPR's data minimisation principle. Retain only what
the decision logic and the audit trail genuinely require, and purge
completed Process State on a defined schedule rather than by default,
keeping it indefinitely.

**Correlation identifier as an authorization bypass vector.** If the
correlation identifier used to route replies back to the correct Process
State is predictable or is accepted from an untrusted source without
verifying the caller is authorised for that specific instance, an attacker
can inject a forged reply that advances, corrupts, or prematurely completes
someone else's in-flight process. The identifier should be treated as a
capability, unguessable, and every inbound reply should be authenticated as
genuinely originating from the expected participant, not merely as carrying
a value that happens to match an open instance.

**Command replay and duplicate side effects as an abuse vector, not only a
reliability bug.** The idempotency failure mode from dimension 11 is framed
there as a correctness bug, and it is also directly exploitable. An attacker
who can trigger redelivery of a reply, for example by manipulating
acknowledgement timing on a message they control, can attempt to force a
duplicate downstream command, a second payment charge or a second shipment,
if the idempotency guard is missing or is keyed on something an attacker can
also control rather than on a value the Process Manager itself generates.

On broader privacy the pattern is otherwise neutral, and the observability
advice in dimension 16 carries the same caveat noted for other patterns in
this repository, that correlation identifiers and any payload fields logged
for debugging may themselves be personal or otherwise sensitive data and
should be subject to the same access and retention rules as the Process
State they describe, not treated as exempt because they appear in
operational telemetry rather than the primary data store.

## Code examples

Three languages, chosen because the pattern shows up idiomatically differently
in each. TypeScript shows a hand-rolled, framework-free implementation
matching dimension 5 and dimension 7 directly, the clearest way to see the
load, decide, save cycle with no library hiding it. Java shows the same shape
built as a small library-free saga runner, closer to how a JVM shop without a
framework like Axon would write it by hand. Python shows a compact
dataclass-driven version, common in smaller services that adopt the pattern
without pulling in a full workflow engine. Go is omitted from a full example
because its idiomatic form is functionally identical to the TypeScript
version, a struct plus a switch over current state, with no additional
language-idiomatic variant beyond what the state machine implementation
variant in dimension 8 already covers.

### TypeScript

```typescript
type Step = "reserving" | "charging" | "compensating" | "completed" | "failed";

interface ProcessState {
  correlationId: string;
  step: Step;
  orderId: string;
}

interface Command {
  type: string;
  correlationId: string;
}

interface Reply {
  type: "InventoryReserved" | "PaymentCharged" | "PaymentDeclined" | "InventoryReleased";
  correlationId: string;
}

class OrderProcessManager {
  private states = new Map<string, ProcessState>();

  start(correlationId: string, orderId: string): Command {
    const state: ProcessState = { correlationId, step: "reserving", orderId };
    this.states.set(correlationId, state);
    return { type: "ReserveInventory", correlationId };
  }

  handleReply(reply: Reply): Command | null {
    const state = this.states.get(reply.correlationId);
    if (!state) return null;

    if (state.step === "reserving" && reply.type === "InventoryReserved") {
      state.step = "charging";
      return { type: "ChargePayment", correlationId: state.correlationId };
    }
    if (state.step === "charging" && reply.type === "PaymentCharged") {
      state.step = "completed";
      return null;
    }
    if (state.step === "charging" && reply.type === "PaymentDeclined") {
      state.step = "compensating";
      return { type: "ReleaseInventory", correlationId: state.correlationId };
    }
    if (state.step === "compensating" && reply.type === "InventoryReleased") {
      state.step = "failed";
      return null;
    }
    return null;
  }
}

const pm = new OrderProcessManager();
const first = pm.start("order-1", "order-1");
console.log(first);
console.log(pm.handleReply({ type: "InventoryReserved", correlationId: "order-1" }));
console.log(pm.handleReply({ type: "PaymentDeclined", correlationId: "order-1" }));
console.log(pm.handleReply({ type: "InventoryReleased", correlationId: "order-1" }));
```

### Java

```java
import java.util.HashMap;
import java.util.Map;

final class ProcessManagerDemo {
    enum Step { RESERVING, CHARGING, COMPENSATING, COMPLETED, FAILED }

    record Command(String type, String correlationId) {}
    record Reply(String type, String correlationId) {}

    static final class ProcessState {
        Step step;
        final String orderId;
        ProcessState(Step step, String orderId) {
            this.step = step;
            this.orderId = orderId;
        }
    }

    static final class OrderProcessManager {
        private final Map<String, ProcessState> states = new HashMap<>();

        Command start(String correlationId, String orderId) {
            states.put(correlationId, new ProcessState(Step.RESERVING, orderId));
            return new Command("ReserveInventory", correlationId);
        }

        Command handleReply(Reply reply) {
            ProcessState state = states.get(reply.correlationId());
            if (state == null) return null;

            if (state.step == Step.RESERVING && reply.type().equals("InventoryReserved")) {
                state.step = Step.CHARGING;
                return new Command("ChargePayment", reply.correlationId());
            }
            if (state.step == Step.CHARGING && reply.type().equals("PaymentCharged")) {
                state.step = Step.COMPLETED;
                return null;
            }
            if (state.step == Step.CHARGING && reply.type().equals("PaymentDeclined")) {
                state.step = Step.COMPENSATING;
                return new Command("ReleaseInventory", reply.correlationId());
            }
            if (state.step == Step.COMPENSATING && reply.type().equals("InventoryReleased")) {
                state.step = Step.FAILED;
                return null;
            }
            return null;
        }
    }

    public static void main(String[] args) {
        OrderProcessManager pm = new OrderProcessManager();
        System.out.println(pm.start("order-1", "order-1"));
        System.out.println(pm.handleReply(new Reply("InventoryReserved", "order-1")));
        System.out.println(pm.handleReply(new Reply("PaymentDeclined", "order-1")));
        System.out.println(pm.handleReply(new Reply("InventoryReleased", "order-1")));
    }
}
```

### Python

```python
from dataclasses import dataclass
from enum import Enum, auto


class Step(Enum):
    RESERVING = auto()
    CHARGING = auto()
    COMPENSATING = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class ProcessState:
    correlation_id: str
    order_id: str
    step: Step


@dataclass
class Command:
    type: str
    correlation_id: str


@dataclass
class Reply:
    type: str
    correlation_id: str


class OrderProcessManager:
    def __init__(self) -> None:
        self._states: dict[str, ProcessState] = {}

    def start(self, correlation_id: str, order_id: str) -> Command:
        self._states[correlation_id] = ProcessState(correlation_id, order_id, Step.RESERVING)
        return Command("ReserveInventory", correlation_id)

    def handle_reply(self, reply: Reply) -> Command | None:
        state = self._states.get(reply.correlation_id)
        if state is None:
            return None

        if state.step is Step.RESERVING and reply.type == "InventoryReserved":
            state.step = Step.CHARGING
            return Command("ChargePayment", state.correlation_id)
        if state.step is Step.CHARGING and reply.type == "PaymentCharged":
            state.step = Step.COMPLETED
            return None
        if state.step is Step.CHARGING and reply.type == "PaymentDeclined":
            state.step = Step.COMPENSATING
            return Command("ReleaseInventory", state.correlation_id)
        if state.step is Step.COMPENSATING and reply.type == "InventoryReleased":
            state.step = Step.FAILED
            return None
        return None


if __name__ == "__main__":
    pm = OrderProcessManager()
    print(pm.start("order-1", "order-1"))
    print(pm.handle_reply(Reply("InventoryReserved", "order-1")))
    print(pm.handle_reply(Reply("PaymentDeclined", "order-1")))
    print(pm.handle_reply(Reply("InventoryReleased", "order-1")))
```

## 18. References

1. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*. Addison-Wesley, 2003.
   ISBN 978-0-321-20068-6. Message Routing chapter, Process Manager.
   Source of the canonical name, the intent, the solution statement, and the
   Process Manager versus Routing Slip distinction in dimension 1.
2. enterpriseintegrationpatterns.com. "Process Manager".
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html
   Verified 2026-08-02. Source for the direct quotations of the pattern's
   intent and solution in dimension 1 and dimension 2.
3. Hector Garcia Molina, Kenneth Salem. "Sagas". ACM SIGMOD Record, Volume
   16, Issue 3, 1987. Source of the original Saga concept referenced in
   dimension 1 as the origin of the Saga Orchestrator alias.
4. Particular Software. NServiceBus documentation, "Sagas".
   https://docs.particular.net/nservicebus/sagas/
   Verified 2026-08-02. Source for the ContainSagaData and production use
   quotations in dimension 8 and dimension 9.
5. MassTransit. Documentation, "Saga State Machines".
   https://masstransit.io/documentation/patterns/saga/state-machine
   Verified 2026-08-02. Source for the MassTransitStateMachine production
   use in dimension 9 and the SagaTestHarness reference in dimension 15.
6. Temporal Technologies. Temporal documentation, "Workflows".
   https://docs.temporal.io/workflows
   Verified 2026-08-02. Source for the Workflow Execution and Event History
   quotations in dimension 8, dimension 9, and dimension 15.
7. Amazon Web Services. AWS Step Functions Developer Guide, "What is AWS
   Step Functions".
   https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html
   Verified 2026-08-02. Source for the Step Functions production use in
   dimension 9.
