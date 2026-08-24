---
name: Saga versus Process Manager
slug: saga-versus-process-manager
family: 11-domain-driven-design
category: Structural, Distributed Coordination
aliases: [Saga Pattern, Orchestration Saga, Choreography Saga, EIP Process Manager]
first_described: "Garcia-Molina and Salem 1987 (sagas); Hohpe and Woolf 2003 (Process Manager)"
maturity: canonical
related: [aggregate, domain-event, event-sourcing, outbox, template-method, mediator, state-machine]
incompatible_with: [two-phase-commit]
verified: 2026-08-02
---

# Saga versus Process Manager

## 1. Name, aliases, and lineage

Two names get used almost interchangeably in distributed systems conversation,
and conflating them is the single most common source of confusion in this
area. They come from different decades and different problems, and they solve
overlapping but not identical needs.

**Saga** is the older term. Hector Garcia-Molina and Kenneth Salem defined it
in "Sagas," a paper presented at the 1987 ACM SIGMOD International Conference
on Management of Data. Garcia-Molina and Salem, "Sagas," Proceedings of the
1987 ACM SIGMOD International Conference on Management of Data, pages 249 to
259 ([ACM Digital Library record](https://dl.acm.org/doi/10.1145/38713.38742),
verified 2026-08-02). The original paper addressed a database problem, not a
microservices problem. a long-lived transaction inside a single database
holding locks for too long, harming concurrency. Their fix was to break the
long transaction into a sequence of smaller local transactions, each with a
corresponding compensating transaction that can undo its effect, and to let
other transactions interleave between the steps rather than blocking behind
one giant lock. The name has since migrated wholesale into distributed
systems and microservices literature, where the "database" that held one
long lock is replaced by several independent services that would otherwise
need a distributed transaction to stay consistent. Chris Richardson's
*Microservices Patterns*, Manning, 2018, chapter 4, restates the pattern for
this context. a saga is a sequence of local transactions, where each local
transaction updates its own service's database and publishes a message or
event that triggers the next local transaction in the sequence
([microservices.io Saga pattern
page](https://microservices.io/patterns/data/saga.html), verified
2026-08-02).

**Process Manager** comes from Gregor Hohpe and Bobby Woolf, *Enterprise
Integration Patterns. Designing, Building, and Deploying Messaging
Solutions*, Addison-Wesley, 2003, in the Messaging Systems chapter, under
the pattern name Process Manager. Their stated intent addresses a routing
problem, how to route a message through multiple processing steps when the
required steps are not known at design time and might not be sequential
([Enterprise Integration Patterns, Process
Manager](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html),
verified 2026-08-02). Their answer is a central processing unit, the
Process Manager, that maintains the state of the in-flight sequence and
decides the next step from intermediate results. Where a Saga is a
coordination strategy for keeping several transactional boundaries
eventually consistent, a Process Manager is a structural pattern for a
stateful object that owns a workflow and issues commands to move it
forward. It says nothing about compensation by itself.

The overlap that causes the confusion is this. One of the two ways to
implement a Saga is to build a central coordinator that sends commands to
each participant and reacts to their replies. That coordinator is,
structurally, a Process Manager. Richardson calls this the
orchestration-based saga and names the coordinating object a saga
orchestrator, which he explicitly draws as playing the same structural role
as the Process Manager (Richardson, *Microservices Patterns*, chapter 4,
section 4.2). So an orchestration-based saga is an application of the
Process Manager pattern to the specific problem of maintaining eventual
consistency across local transactions, with compensation built in as a
first-class concept. The other implementation style, choreography, has no
Process Manager at all. services react to each other's domain events
directly, with the sequence emerging from local if-this-then-that rules
distributed across every participant, and no single object anywhere holds
the whole flow. Two names, three shapes emerge from this history. Saga
implemented as choreography, Saga implemented as orchestration (which reuses
Process Manager), and Process Manager used on its own for a workflow that
has no compensation requirement at all, such as a document approval flow or
a customer support ticket router.

Several aliases circulate. "Saga Pattern" and "distributed saga" name the
same coordination strategy described above. "Orchestration Saga" and
"Choreography Saga" name its two implementation styles. "Workflow
Orchestrator" and "Business Process Orchestrator" are marketing names
vendors such as Camunda, Temporal, and AWS Step Functions use for what is
structurally a Process Manager, sometimes carrying saga-style compensation
and sometimes not.

## 2. Problem and context

The concrete situation is this. A business operation spans more than one
service, each service owns its own datastore, and no distributed
transaction coordinator is available or acceptable. An order placement
touches an Order service, a Payment service, an Inventory service, and a
Shipping service. Each of those services has its own database, by design,
because that separation is what makes the services independently deployable
in the first place, see the Aggregate entry for why a service's
transactional boundary should map to one aggregate. A single ACID
transaction across all four databases would need a two-phase commit
coordinator holding locks across four separate systems for the duration of
the whole operation, which reintroduces the tight coupling and availability
coupling the services were split apart to escape.

The context in which this problem arises has three properties, and a design
that lacks any one of them does not need this whole apparatus.

- The operation must touch more than one independently deployed service or
  independently owned data store, so a single local ACID transaction cannot
  cover it.
- The operation has a natural sequence of steps, each of which is itself
  transactional at the local level, and each of which can plausibly fail
  after some earlier steps have already committed.
- A failure partway through must be handled by something, either automatic
  compensation (undo what already happened) or an explicit, visible manual
  recovery path. Silently leaving the system in a half-completed state is
  not an option a production system can tolerate.

A reader who recognises "order goes through, payment is charged, but the
warehouse never got the reservation and nobody noticed for three days" is
recognising exactly the problem this pattern family exists to solve, whether
or not they know the word "saga."

## 3. Forces

Both the saga coordination strategy and the Process Manager structural
pattern trade the same handful of forces, though they land in different
places on some of them.

- **Consistency model.** Sacrificed relative to a single ACID transaction,
  deliberately. A saga gives up atomicity and isolation across steps in
  exchange for availability and service autonomy. The intermediate states
  are visible to the rest of the system while the saga is in flight, which
  is the defining trade-off. This is eventual consistency, not strong
  consistency, and any design that pretends otherwise is lying to itself.
- **Coupling.** Choreography favours low coupling, since no service knows
  about the others, each only knows the events it listens for and the
  events it emits. Orchestration (Process Manager) trades that away
  deliberately, since the orchestrator knows about every participant by
  name, which is a form of coupling concentrated in one place rather than
  spread everywhere.
- **Visibility and debuggability.** Orchestration favours this heavily. One
  object holds the entire state of the in-flight process, so "where is
  order 47291 right now" has one answer in one place. Choreography
  sacrifices it. reconstructing the state of a multi-step flow means
  correlating events across every participating service's logs, because no
  single place holds the whole picture.
- **Single point of failure and bottleneck risk.** Orchestration takes this
  on directly; the EIP text names it explicitly as the central drawback of
  Process Manager. Choreography avoids it structurally, since there is no
  central component to become unavailable, though a shared message broker
  can reintroduce the same risk in a different shape.
- **Testability in isolation.** Choreography sacrifices this. Testing "what
  happens across the whole order flow" in choreography means standing up
  every participating service and its message bus, because the sequence
  exists only as the emergent behaviour of many independent listeners.
  Orchestration favours it, since the orchestrator's logic can be unit
  tested against fake participant responses, because the sequence is one
  piece of code.
- **Operational cost of new steps.** Choreography sacrifices this as the
  flow grows. adding a step that must fire in the middle of an existing
  sequence means modifying the event contracts of several existing
  services, or reasoning very carefully about a new listener's ordering
  relative to others. Orchestration favours it, since adding a step means
  editing one workflow definition.
- **Compensation complexity.** Both approaches carry it, but orchestration
  concentrates the compensation logic in one place where it can be reviewed
  as a whole, while choreography scatters it. Each service must
  independently know how to undo its own step in response to a "step N
  failed" event, and nobody has an easy view of whether the aggregate
  compensation logic is actually correct end to end.

No option here is free. A team that picks orchestration because "it is
easier to reason about" is trading away the decoupling that was the entire
reason to split into services in the first place, and that trade must be
made consciously, not by default.

## 4. Applicability and non-applicability

Reach for a saga, in either coordination style, when:

- The operation spans two or more independently deployed services with
  separate datastores, and a distributed transaction coordinator is not
  available, not desired, or not acceptable for availability reasons.
- Each individual step is naturally transactional at the local level and has
  a plausible, definable compensating action, or the business accepts a
  documented manual recovery path for a rare failure.
- The business process is long enough, or crosses enough network
  boundaries, that holding locks for its whole duration would be
  operationally unacceptable (seconds to days, not the sub-100-millisecond
  case a single local transaction handles fine).
- The team can tolerate, and the domain permits, other actors observing
  intermediate, not-yet-fully-committed state for the duration of the saga.

Reach specifically for the orchestration style (Process Manager) when:

- The sequence of steps is genuinely dynamic, meaning the next step depends
  on the outcome of the previous one, on external input, or on business
  rules that change independently of the participating services' code.
- Central visibility into "where is this specific business process instance
  right now" is a hard operational requirement, for compliance, support, or
  debugging.
- The number of participants and the branching complexity are large enough
  that reconstructing the flow from scattered event listeners would be
  unmanageable.

Reach specifically for the choreography style when:

- The sequence is genuinely simple and close to linear, each participant's
  reaction to an event is a small, self-contained rule, and no one service
  is a natural owner of the whole process.
- Maximum service autonomy is a hard requirement, for example because the
  participating teams release independently on very different schedules
  and a shared central workflow definition would become a coordination
  bottleneck between teams, not merely between runtimes.

Do NOT reach for this pattern family, and this is the list most catalogs
skip:

- **The operation fits inside one aggregate's transactional boundary.** If
  every piece of state that must change together is owned by one aggregate
  in one bounded context, a single local transaction covers it completely,
  and a saga adds distributed failure modes for zero benefit. Consult the
  Aggregate entry. aggregate boundaries should be drawn specifically so
  that most business invariants are enforceable inside one aggregate
  exactly to avoid needing this pattern.
- **The steps cannot be meaningfully compensated and the business has not
  accepted a manual recovery path.** A payment capture that has already
  been settled through card networks cannot always be reversed cleanly; if
  "compensate" really means "issue a refund days later and eat the
  chargeback risk," that is a real business decision, not a technical
  detail, and it must be made explicitly by the business, not silently
  encoded by an engineer.
- **Strong consistency is a genuine legal or safety requirement.** Certain
  financial ledger postings, certain safety interlocks, and certain
  regulatory reporting numbers must be atomically consistent by law or by
  physical safety constraint. A saga's eventual consistency window is not
  an option there; the correct answer is redesigning the boundary so the
  invariant lives inside one transactional store, even if that costs some
  service autonomy.
- **The whole "process" is actually one HTTP request-response with no
  durable state to track.** If nothing needs to survive a crash between
  step one and step two, and the whole thing completes or fails within one
  synchronous call chain, a saga's durable state machine and message-driven
  choreography are pure overhead. A function call with a try-catch and a
  local transaction handles it.
- **Choosing orchestration for a two-step flow because it will grow later.**
  Speculative Process Manager, matching the Applicability discussion in the
  Factory Method entry's non-applicability list. build the coordinator when
  the third step and its branching actually arrive, not in anticipation of
  it.
- **Choosing choreography purely to avoid a central component, when the
  flow already has more than about five steps with real branching.** Past a
  certain complexity the "no coupling" property of choreography becomes an
  illusion. the coupling has not disappeared, it has become implicit,
  encoded in the shared assumption every service holds about what events
  mean and in what order they arrive. Implicit coupling that nobody can see
  in one place is worse than explicit coupling that one orchestrator makes
  visible.

## 5. Structure

**Saga participants**, applicable to either coordination style.

- **Saga participant (local transaction owner).** A service that owns one
  step. It performs a local transaction against its own datastore and also
  defines the compensating transaction that can semantically undo that step
  if a later step fails.
- **Saga log or saga state.** The durable record of which steps have
  completed and which compensations, if any, have been triggered. In
  choreography this is implicit and distributed, reconstructed from the
  union of events each service persisted. In orchestration it is explicit,
  held by the orchestrator.
- **Compensating transaction.** Semantically the inverse of a forward step,
  not necessarily its literal reversal. Garcia-Molina and Salem's original
  1987 paper is explicit that a compensating transaction need not restore
  the exact prior state, only bring the system to an acceptable equivalent
  state; "cancel the reservation" compensates "reserve the seat" even
  though the specific seat that gets freed might differ from the one
  originally held, and that is fine.

**Choreography-specific participants.**

- **Domain event.** The only communication mechanism. Each participant
  publishes an event describing what it did (`OrderCreated`,
  `PaymentCharged`, `InventoryReserved`) and each other participant that
  cares subscribes and reacts, entirely independently.

**Orchestration-specific participants (the Process Manager shape).**

- **Orchestrator (the Process Manager itself).** A stateful object, one
  instance per in-flight business process, holding the current step, the
  data needed to make routing decisions, and the logic for what command to
  send next given the current state and the latest reply.
- **Command.** A directed, imperative message the orchestrator sends to a
  specific participant, telling it what to do, as opposed to a domain event
  a participant broadcasts about what it already did.
- **Reply or event listener.** The channel by which a participant reports
  back to the orchestrator that its step succeeded or failed, which the
  orchestrator consumes to decide the next command.

## 6. ASCII structure diagram

```
CHOREOGRAPHY (no Process Manager, no central object)

+---------------+
| Order Service |
+---------------+
           | OrderCreated
           v
+-----------------+
| Payment Service |
+-----------------+
           | PaymentCharged
           v
+-------------------+
| Inventory Service |
+-------------------+

Failure paths, each its own pub/sub event:
  Payment Service --PaymentFailed--> Order Service
  Inventory Service --InventoryReservationFailed-->
  Order Service

No single object holds the whole flow. Each arrow
is a pub/sub event.


ORCHESTRATION (a Process Manager coordinates the
same steps)

+--------------------------+
| Order Saga Orchestrator  |
| (a Process Manager)      |
| state = AWAITING_PAYMENT |
+--------------------------+
           | command      ^ reply
           v              |
+-----------------+
| Payment Service |
+-----------------+
           | command      ^ reply
           v              |
+-------------------+
| Inventory Service |
+-------------------+

The orchestrator sends one command at a time and
owns the whole sequence. Participants know only the
orchestrator, not each other.
```

## 7. Dynamics

The forward path and the compensation path both need showing, because the
compensation path is where most real designs go wrong. This trace shows an
orchestration-based saga, since that is the style where the state machine is
explicit enough to draw cleanly; a choreography saga's dynamics are the same
sequence of events with no orchestrator column, replaced by direct
participant-to-participant event delivery.

```
Client        Orchestrator          Payment Svc        Inventory Svc
  |                |                     |                   |
  |-- PlaceOrder ->|                     |                   |
  |                |-- ChargePayment --->|                   |
  |                |                     |-- (local tx) -----|
  |                |<-- PaymentCharged --|                   |
  |                |                     |                   |
  |                |-- ReserveStock --------------------------->|
  |                |                                             |-- (local tx, FAILS)
  |                |<---------------- StockReservationFailed ----|
  |                |                     |                   |
  |                | -- decide to compensate the completed step -
  |                |-- RefundPayment --->|                   |
  |                |                     |-- (compensating tx)
  |                |<-- PaymentRefunded -|                   |
  |                |                     |                   |
  |<-- OrderFailed |                     |                   |
  |                |                     |                   |
```

Two timing properties determine whether this actually works in production,
not only on the diagram. First, every message send and every local database
write must be atomic together, or the saga log itself becomes unreliable;
this is the reason the Saga and Process Manager patterns are almost always
paired with the Outbox pattern in a real implementation, see dimension 13.
Second, compensations must be issued in strict reverse order of the
completed steps, and each compensating transaction must itself be either
idempotent or de-duplicated at the receiver, because a saga orchestrator can
crash and resume mid-compensation, replaying a compensation message it
already sent once.

## 8. Implementation variants

**Choreography with plain domain events and a message broker.** Each
service publishes and subscribes directly, with no shared library beyond
the event schema. Lowest infrastructure cost, highest coordination cost as
the flow grows. This is the shape Richardson demonstrates using the
Eventuate Tram framework in *Microservices Patterns*, chapter 4.

**Orchestration with a hand-written state machine per saga.** The
orchestrator is application code, an enum for the current state, a switch
or pattern match over incoming replies, and explicit calls that send the
next command. Cheapest to start, and the shape almost every team writes
first before reaching for a workflow engine. The risk is that durability,
idempotency, and timeout handling all have to be hand-built and are easy to
get subtly wrong.

**Orchestration on a durable workflow engine (Temporal, Cadence, AWS Step
Functions, Camunda).** The engine persists the orchestrator's execution
state automatically, replays deterministically after a crash, and provides
built-in retry, timeout, and (in Temporal and Cadence) a native concept of
compensation via `defer`-style cleanup blocks in the workflow code itself.
Temporal's own workflow documentation describes a Workflow Execution as
able to keep running for years even across underlying infrastructure
failures, restoring pre-crash state by replaying its persisted Event
History ([Temporal Workflows
documentation](https://docs.temporal.io/workflows), verified 2026-08-02).
AWS Step Functions models the same idea as a state machine with native
`Retry` and `Catch` fields on every task state, letting a step's failure
branch directly to a documented compensating state ([AWS Step Functions
developer guide, "What is Step
Functions"](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html),
verified 2026-08-02, section "Error handling").

**Orchestration via a saga-aware messaging framework (NServiceBus,
MassTransit).** The framework provides a base class (NServiceBus's
`Saga<T>`, MassTransit's `MassTransitStateMachine<T>`) that couples message
handling to persisted saga data automatically, with declarative correlation
between incoming messages and the correct in-flight instance. NServiceBus
documents this directly. a saga class implements `IAmStartedByMessages<T>`
to declare which message creates a new instance, inherits saga data from
`ContainSagaData`, and requires an explicit correlation property because
the saga's own identifier must not be used to correlate incoming messages
([NServiceBus Sagas documentation](https://docs.particular.net/nservicebus/sagas/),
verified 2026-08-02).

**Choreography with event sourcing as the saga log.** Instead of a
separately-tracked saga state, the sequence of domain events already
persisted by event sourcing (see the Event Sourcing entry) is read back to
reconstruct which steps have completed, and a saga process reacts to new
events as they are appended. This removes the need for a dedicated saga
table but couples the saga's correctness to the event store's ordering and
delivery guarantees.

## 9. Known production uses

**Uber's Cadence, orchestration-based sagas at large scale.** Uber built
Cadence, an open-source, durable workflow orchestration engine, specifically
because implementing saga-style compensation logic by hand at Uber's scale
was error-prone; Cadence provides built-in support for compensation,
unlimited exponential-backoff retry, and a guarantee that workflow code
eventually completes. As of the engine's own public reporting, Cadence
executes over 12 billion workflow executions and 270 billion actions per
month inside Uber, powering more than 1,000 services ranging from the most
critical (T0) to the least (T5) ([Uber Engineering blog, "Conducting Better
Business with Uber's Open Source Orchestration Tool,
Cadence"](https://www.uber.com/en-CO/blog/open-source-orchestration-tool-cadence-overview/),
verified 2026-08-02).

**AWS Step Functions, orchestration for distributed AWS workflows.**
Amazon's own Step Functions service is a hosted, durable state-machine
orchestrator used to coordinate multi-step business processes across AWS
services, explicitly supporting `Retry` and `Catch` on individual task
states so a failed step can lead into a compensating step, and offering a
Standard workflow type with exactly-once execution guarantees for workflows
running up to one year ([AWS Step Functions developer
guide](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html),
verified 2026-08-02).

**NServiceBus sagas in production .NET service architectures.** Particular
Software's NServiceBus messaging framework ships a first-class `Saga<T>`
base class used across production .NET service architectures to manage
long-running business processes with fault tolerance and eventual
consistency, with documented support for SQL Server, CosmosDB, and other
persistence backends for saga state ([NServiceBus Sagas
documentation](https://docs.particular.net/nservicebus/sagas/), verified
2026-08-02).

**Camunda as a Process Manager for microservices orchestration.** Camunda
positions its BPMN-based workflow engine directly as the orchestrator role
in the orchestration-versus-choreography decision for microservices,
providing a visual process definition that plays the same structural part
as Hohpe and Woolf's Process Manager. a central engine that holds the state
of an in-flight process instance and issues the next task ([Camunda,
orchestration vs. choreography for
microservices](https://camunda.com/blog/2023/02/orchestration-vs-choreography/),
verified 2026-08-02).

**Eventuate frameworks as the reference implementation for both saga
styles.** Chris Richardson's own Eventuate platform ships an Eventuate Tram
implementation for choreography-based sagas and an Eventuate Tram Sagas
framework specifically for orchestration-based sagas, used as the canonical
worked examples in *Microservices Patterns* and referenced directly from
the microservices.io pattern catalog's own Saga entry
([microservices.io, Saga
pattern](https://microservices.io/patterns/data/saga.html), verified
2026-08-02).

## 10. Consequences

Positive.

- Each participating service keeps full autonomy over its own datastore and
  its own local transactions; no distributed lock is ever held across
  service boundaries.
- The business process can span seconds, hours, or days without holding any
  database resource open for that whole span, which a distributed
  transaction coordinator could never do safely.
- Orchestration specifically gives one place to see the state of any
  in-flight process instance, which materially shortens incident response
  time compared to reconstructing a flow from scattered logs.
- Compensation logic, once written and tested, gives an explicit, reviewable
  answer to "what happens when step three fails," rather than leaving that
  answer as an unhandled edge case discovered in production.
- Choreography specifically keeps participating services from needing to
  know about each other by name, which lets teams evolve their own services
  independently as long as the event contract is honoured.

Negative.

- The system as a whole gives up atomicity and isolation across the steps;
  other actors can observe a state that will later be compensated away, and
  every read path that could see this must be designed to tolerate it,
  which is a design cost that spreads well beyond the saga's own code.
- Compensating transactions are not free to design. Some steps genuinely
  cannot be cleanly undone (an email already sent, a card already charged
  and settled), and the business has to make and document a real decision
  about what "compensate" means for those steps.
- Orchestration concentrates a single point of failure and a coordination
  bottleneck in the Process Manager, exactly as the EIP text warns; every
  participant becomes dependent on the orchestrator being available and
  correct.
- Choreography scatters compensation logic and sequencing knowledge across
  every participant, so understanding "what happens across the whole flow"
  requires reading every service involved, and adding a step in the middle
  of an existing choreographed flow risks silently breaking an assumption
  another service was relying on.
- Both styles require durable, replayable state (a saga log or an
  orchestrator's persisted execution state), which is genuine additional
  infrastructure and operational surface area that a single local
  transaction never needed.

## 11. Failure modes and misuse

**The half-compensated saga.** Symptom. A support ticket reports a customer
who was charged but whose order shows cancelled, and nobody can explain why
the refund never fired. Cause. The orchestrator crashed after sending the
compensating command but before recording that it did so, and on restart it
did not resume the compensation because its recovery logic only replayed
from the last successfully persisted step, not from "compensation was in
flight." Fix. Persist the intent to compensate before sending the
compensating command, in the same transaction as the state transition that
decided to compensate, and make the compensating command itself idempotent
on the receiving side so a resumed retry is safe.

**Sagas without idempotent participants.** Symptom. A customer's inventory
reservation quietly doubles after a network blip, discovered weeks later
during a stock reconciliation. Cause. The orchestrator retried a command
after a timeout, assuming the first attempt had failed, but the first
attempt had actually succeeded and the receiving service processed both.
Fix. Every command a saga sends carries a stable idempotency key (usually
the saga instance identifier plus the step identifier), and every
participant deduplicates on that key before applying the operation.

**Choreography drift, the silently broken implicit contract.** Symptom. A
new team adds a feature that changes the payload or timing of an event an
older, unrelated service was quietly depending on, and that older service
starts silently skipping a step because a field it expected is now absent.
Cause. Choreography has no central place that documents which service
reacts to which event and why, so the dependency exists only in code nobody
read before shipping the change. Fix. Maintain an explicit, versioned event
catalog outside the code (a schema registry, a documented contract test
suite per consumer) and treat any change to an event's shape as a breaking
change requiring the same review discipline as an API change.

**Using a saga where a single aggregate would do.** Symptom. A team builds
a full orchestrator with compensation logic to update a customer's shipping
address and their loyalty points balance together, both of which live in
the same service and the same database. Cause. Reaching for the pattern by
reflex rather than checking whether the operation actually crosses a
transactional boundary. Fix. Confirm both pieces of state are owned by the
same aggregate or the same local transaction before reaching past it; if
they are, a plain local transaction is correct and the saga machinery is
pure overhead, matching the non-applicability list in dimension 4.

**Compensation that assumes the world stood still.** Symptom. A "cancel
reservation" compensating transaction fails or, worse, silently succeeds
against the wrong data, because between the forward step and the
compensation the underlying record was already modified by something else,
for example the customer manually cancelled the order through a different
channel while the saga was still compensating. Cause. The compensating
transaction was written assuming it always runs against the exact state the
forward transaction left, with no check for concurrent modification. Fix.
Compensating transactions must be as defensive as any other transaction.
check the current state before acting, and treat "there is nothing left to
compensate" as a valid, expected outcome rather than an error.

**The orchestrator as an accidental god object.** Symptom. The order saga
orchestrator's code grows to contain business rules that actually belong to
individual participants. pricing logic, inventory allocation rules, and
fraud scoring all get pulled into the orchestrator because it is already
there and can see everything. Cause. The Process Manager's central
visibility is genuinely convenient, and that convenience quietly attracts
logic that should stay local to a participant. Fix. The orchestrator should
only decide which command to send next and when, never how a participant
carries out that command; any logic that needs the participant's own data
to evaluate belongs inside that participant, called via the command, not
inlined into the orchestrator.

## 12. Trade-off matrix

Compared against named alternatives for keeping cross-service consistency,
across the forces from dimension 3.

| Force | Choreography Saga | Orchestration Saga (Process Manager) | Two-Phase Commit (XA) | TCC (Try-Confirm-Cancel) |
|---|---|---|---|---|
| Coupling between participants | Lowest. Only shared event contracts | Higher. Orchestrator names every participant | Highest. All resource managers coordinate synchronously | Medium. Participants share the Try/Confirm/Cancel protocol |
| Central visibility of an in-flight process | None. Reconstructed from many logs | Strong. One instance, one state | Strong, but only for the duration of the transaction | Weak. State lives per-participant |
| Availability during a participant outage | Degrades gracefully, other steps proceed if independent | Blocks on the unavailable participant's step | Blocks the whole transaction, holds all locks | Blocks the affected Try or Confirm phase |
| Consistency window | Eventually consistent, no upper bound guaranteed by the pattern itself | Same, but a workflow engine can bound it with timeouts | Strongly consistent, atomic | Eventually consistent, narrower window than a saga since resources are pre-reserved |
| Adding a new step | Requires touching multiple existing services' listeners | Edit one workflow definition | Add a new resource manager to the coordinator | Add a new Try/Confirm/Cancel participant |
| Operational infrastructure cost | Low, reuses the existing message broker | Medium to high, needs durable orchestrator state | High, needs a distributed transaction coordinator (rare in modern stacks) | Medium, needs a reservation phase per resource |
| Testability of the whole flow | Poor in isolation, needs all services running | Good, orchestrator logic testable against fakes | Good for the coordinator, poor for cross-resource-manager behaviour | Good, similar to orchestration |
| Resource locking during the operation | None, each local transaction commits immediately | None, each local transaction commits immediately | Held across every participant for the whole duration | Resources reserved (not locked) during Try, released on Confirm or Cancel |

Reading of the table. A saga in either style always beats two-phase commit
on availability, because no saga participant ever holds a lock waiting on
another service; that is the entire reason the pattern exists in modern
microservices architectures where XA coordinators are rarely acceptable.
Between the two saga styles, orchestration buys visibility and testability
at the cost of coupling and a central bottleneck; choreography buys
autonomy at the cost of visibility. TCC sits between a saga and two-phase
commit. it narrows the consistency window by reserving resources up front,
at the cost of every participant needing to implement three distinct
operations instead of one forward step and one compensation.

## 13. Related and incompatible patterns

- **Aggregate.** The pattern this whole family exists to avoid crossing
  carelessly. An aggregate's transactional boundary should be drawn so that
  most invariants live inside one aggregate; a saga is what handles the
  invariants that genuinely must span more than one aggregate or more than
  one bounded context, and should never be reached for as a substitute for
  correctly sizing an aggregate boundary.
- **Domain Event.** The communication primitive choreography is built on
  entirely, and the mechanism by which an orchestrator learns that a
  participant's local transaction has completed or failed.
- **Outbox pattern.** Nearly always paired with a saga in a real
  implementation. A saga participant's local transaction and its outgoing
  message (the next command or the completion event) must be atomic
  together, or a crash between the two leaves the saga log lying about what
  actually happened. The Outbox pattern is the standard fix, writing the
  outgoing message to a table in the same local transaction and relaying it
  separately.
- **State Machine / State pattern.** A Process Manager is, structurally, a
  persisted state machine. it has a defined set of states, and transitions
  between them triggered by incoming events or replies. The GoF State
  pattern describes the same shape at the object level, without the
  durability, distribution, and messaging concerns a Process Manager adds
  on top.
- **Template Method.** Some orchestrator implementations structure the
  overall saga as a fixed sequence with per-participant hooks for the
  forward and compensating action, mirroring Template Method's fixed
  algorithm with pluggable steps; see the Factory Method entry's discussion
  of Template Method pairing for the same relationship in a different
  context.
- **Mediator.** A Process Manager is a specialised, stateful, durable
  Mediator. it centralises communication between participants that would
  otherwise need to know about each other, exactly as Mediator does, but
  adds persistence and an explicit workflow definition that a plain
  in-memory Mediator does not carry.
- **Two-Phase Commit (incompatible in intent, not merely different).** A
  saga exists specifically because 2PC's synchronous, lock-holding
  coordination is unacceptable across independently deployed services.
  Mixing the two, for example having one saga step internally use 2PC
  across two of its own resources, is fine; using 2PC to try to make a saga
  strongly consistent defeats the entire reason to have chosen a saga.
- **CQRS and Event Sourcing.** Frequently deployed alongside orchestration.
  the orchestrator's own state is often itself event-sourced (see dimension
  8), and the read side that shows a customer "your order is being
  processed" is typically a CQRS read model built by projecting the saga's
  own events, since the saga's write-side state is not meant to be queried
  directly by external callers.

## 14. Refactoring path in and out

Introducing a saga into code that currently attempts a distributed
transaction, or that silently ignores the cross-service consistency problem
entirely (the common starting point is a controller that calls three
services in sequence with no failure handling at all). Ordered steps, using
the orchestration style since it is the easier one to introduce
incrementally.

1. Identify every service call in the existing sequential code and, for
   each one, write down explicitly what "undo this" means in business
   terms. If any step genuinely has no answer, stop and get an explicit
   business decision before writing any code; do not invent a compensating
   action that has not been agreed.
2. Wrap the existing sequence in a single orchestrator object that holds an
   explicit state field, starting with the states "IN_PROGRESS",
   "COMPLETED", and "FAILED". Do not add compensation yet; this step only
   makes the in-flight state observable and persisted.
3. Persist the orchestrator's state after every step, atomically with any
   local write the orchestrator itself performs, using the Outbox pattern
   if the orchestrator needs to emit the next command as a message.
4. Add the compensating action for each step, one at a time, starting from
   the last step and working backward, since the last step's compensation
   is usually the simplest (nothing after it to worry about) and testing
   each one in isolation is easier moving backward.
5. Add idempotency keys to every command the orchestrator sends and every
   compensation, and add deduplication on the receiving side of each
   participant, closing the retry-related failure mode from dimension 11.
6. Add explicit timeout handling. what happens if a participant never
   replies. A saga with no timeout path is a saga that can hang forever
   waiting for a reply that will never come.
7. Once the orchestrator's state machine and its transitions are stable,
   consider whether a durable workflow engine (dimension 8) would remove
   hand-maintained persistence and retry code that is now duplicating what
   such an engine provides for free; that migration is a replacement of
   infrastructure, not of the saga's logical design, so it should not
   change step 1's list of compensations.

Removing a saga when it stops earning its place. The clearest signal is a
saga whose participants have since been consolidated into a single service
with a single datastore, so the cross-service boundary that justified the
saga no longer exists.

1. Confirm every participant the saga coordinates now shares one
   transactional store. If even one still lives elsewhere, the saga is
   still earning its place and should not be removed.
2. Replace the saga's forward steps with direct calls inside one local
   transaction, and delete the compensating transactions; a local
   transaction that fails rolls back for free, so compensation logic is now
   dead weight.
3. Delete the orchestrator's persisted state and any workflow-engine
   registration, and remove the outbox rows and the messages that used to
   flow between what are now the same process.
4. Keep the saga's own tests as regression tests during this migration,
   converted to assert the same end-to-end business outcome against the new
   single-transaction implementation, so the removal is provably behaviour
   preserving.

## 15. Testing and verification

Easier because of the pattern.

- Orchestration specifically makes the whole business process's sequencing
  logic unit-testable in isolation. Feed the orchestrator a sequence of
  fake participant replies, including failure replies, and assert the
  sequence of commands it issues, with no real network call anywhere.
- Compensation logic, once extracted as an explicit method per step, can be
  tested directly. given the state a forward step left behind, assert the
  compensating action returns the system to the documented acceptable
  state, without needing the forward step to have actually run first.
- A saga's explicit state machine gives a natural place to write a state
  transition test asserting that every state has a defined transition for
  every possible incoming event, catching a missing case (an unhandled
  timeout, an unhandled failure reply) at test time instead of in
  production three months later.

Harder because of the pattern.

- End-to-end behaviour, across every real participant with real network
  calls and real message delivery timing, is genuinely harder to test than
  a single local transaction, because timing, ordering, and partial failure
  are now genuine variables rather than things a database's ACID guarantees
  hide.
- Choreography is specifically hard to test as a whole, since no single
  test target holds the full sequence; verifying "the whole flow works" in
  choreography usually means an integration test standing up every
  participating service and its broker, which is slow and brittle compared
  to a unit test against an orchestrator.
- Compensation ordering under concurrent saga instances (two orders for the
  same limited-stock item compensating at the same moment) is a genuine
  concurrency testing problem that a single-service local transaction never
  had to face.

Techniques that apply.

- **Saga instance state-machine testing.** Drive the orchestrator through
  every documented state transition with a table of (current state,
  incoming event) pairs and assert the resulting state and emitted command,
  which is the same technique used for testing the GoF State pattern's
  transition table.
- **Contract tests per participant.** Each participant that a choreography
  saga depends on publishes a documented event schema, and each downstream
  consumer runs a contract test against that schema (a tool such as Pact is
  the common choice) so a breaking change is caught at build time in the
  producing service, not discovered at runtime by the consuming service.
- **Fault-injection testing on the failure path.** Because the entire point
  of the pattern is correct behaviour under partial failure, a test suite
  that never injects a participant failure has not actually tested the
  saga; deliberately fail each step in turn, including failing after the
  local transaction commits but before the reply is sent, and assert the
  saga still reaches a correct terminal state.
- **Idempotency replay tests.** Send the same command or compensating
  command to a participant twice and assert the observable effect is
  identical to sending it once, directly verifying the fix for the
  duplicate-command failure mode in dimension 11.

## 16. Observability signals

A saga's state is, by design, spread across time and across services, so
without deliberate telemetry a production incident becomes archaeology.

What to record.

- On every state transition of an orchestrator, a structured log event or
  span carrying the saga instance identifier, the previous state, the new
  state, and the triggering event, so a single trace query answers "show me
  everything that happened to order 47291."
- A counter of saga instances currently in each state, labelled by state
  name, giving a live gauge of how many orders are, for example, stuck in
  `AWAITING_INVENTORY` right now.
- A counter, labelled by step and by outcome (succeeded, failed, timed
  out), of every step attempt, which is the primary signal for spotting a
  participant that has started failing more often than its historical
  baseline.
- A dedicated counter for compensations triggered, labelled by which step
  triggered the chain of compensations, since a rising compensation rate is
  usually the earliest visible sign that something upstream broke.
- A histogram of saga instance duration from start to terminal state
  (completed or fully compensated), because a saga that used to finish in
  seconds and now takes minutes is a leading indicator of a struggling
  participant well before that participant's own error rate rises.
- The correlation identifier that ties an incoming saga command back to the
  originating business request, propagated end to end through every
  participant's own logs (a trace ID in the sense of distributed tracing),
  so a support engineer can pivot from a customer's order number straight
  into every service that touched it.

A healthy instance on a dashboard. The state-distribution gauge shows the
expected shape for current volume, with most instances passing through
transient states quickly and settling into a terminal state within the
expected duration histogram. The compensation counter sits near its
historical baseline. No saga instance sits in a non-terminal state past its
configured timeout.

A failing instance. A specific state's gauge climbs and does not drain,
meaning instances are piling up waiting on a step that is not completing,
which usually points directly at the participant responsible for that
step. Or the compensation counter for one specific step spikes, localising
a regression to that step's participant without reading any of its own
logs first. Or the duration histogram develops a long tail, showing sagas
that eventually complete but are taking far longer than normal, often the
earliest sign of a downstream retry storm.

## 17. Security and privacy implications

The pattern moves what used to be internal database state into messages
that cross network boundaries and, in orchestration, into a persisted
workflow store that outlives any single request. That has real
implications, and several concerns are frequently invented that do not
actually apply, so both are stated plainly.

**Message payload exposure.** Commands and events carried between saga
participants often contain the same sensitive business data the local
transactions were operating on, an order total, a shipping address, a
payment token. Every message broker, every persisted saga log, and every
observability trace that captures message payloads becomes a place that
data now lives, multiplying the attack surface compared to a single
database holding that data once. Payloads should carry the minimum data
each participant actually needs (a reference or token rather than a raw
payment instrument, for instance), and any broker, saga-state store, or
tracing backend holding this data needs the same access control and
encryption at rest as the services' own databases, not a lighter standard
because "it is only a message."

**Replay and forged compensation risk.** Because sagas are message-driven
and often rely on retries to survive transient failures, a system that does not
authenticate the sender of a command is open to a forged or replayed
compensating command triggering an unwanted rollback, for example an
attacker replaying an old `RefundPayment` command to trigger a duplicate
refund. Participants must authenticate the source of every command,
typically via message signing or mutual TLS on the transport plus the
idempotency-key deduplication already required for correctness in
dimension 11, which happens to double as a defence here.

**Orchestrator as a high-value target.** In the orchestration style, the
orchestrator has the authority to issue commands to every participant,
which makes it a concentrated target. compromising the orchestrator, or
injecting a forged command that appears to come from it, gives an attacker
the ability to trigger arbitrary steps across every service the saga
touches. This argues for the orchestrator's outbound commands being signed
or otherwise attributable, and for the orchestrator's own credentials being
scoped as narrowly as the individual commands actually require, rather
than holding a single broad credential that can act as any participant.

**Data residency and retention.** A saga's persisted log or workflow-engine
execution history is, itself, a durable copy of business data that may
include personal data subject to retention limits under data protection
law. A saga log kept indefinitely for debugging purposes can quietly
become a long-lived, undocumented copy of personal data that the rest of
the system has a defined deletion policy for and the saga infrastructure
does not. Retention and deletion policy for saga state needs to be an
explicit design decision, not an accidental side effect of the workflow
engine keeping history by default.

On the specific claim that choreography is by nature more secure than
orchestration because it has no central component, this claim is not accurate.
Choreography moves the same sensitive payloads across the same message
broker, and simply removes the one place where an access-control review
could look at everything the flow touches in a single pass; that is a
genuine trade-off in auditability, stated here as engineering judgement
rather than a sourced claim, since no cited source makes this comparison
directly.

## Code examples

Three languages, each showing a different genuine implementation shape from
dimension 8, rather than the same shape translated three times. Go shows a
hand-written orchestrator state machine, which is the shape most teams
write first and the one where Go's explicit error handling reads most
naturally. TypeScript shows the outbox-backed step contract that ties a
saga participant's local write to its outgoing message, the piece most
implementations get wrong first. Python shows a compact choreography
listener, the shape with no central orchestrator at all. Compiled and run
where the toolchain allows; state plainly where it does not.

### Go, a hand-written orchestrator state machine

```go
package main

import "fmt"

type SagaState int

const (
	StateStarted SagaState = iota
	StatePaymentCharged
	StateCompleted
	StateCompensatingPayment
	StateFailed
)

type OrderSaga struct {
	OrderID string
	State   SagaState
}

// ChargePayment and ReserveStock are the two participants, simulated here.
func chargePayment(orderID string) error {
	return nil // succeeds in this example
}

func reserveStock(orderID string) error {
	return fmt.Errorf("no stock available for order %s", orderID)
}

func refundPayment(orderID string) error {
	return nil
}

func (s *OrderSaga) Run() error {
	s.State = StateStarted

	if err := chargePayment(s.OrderID); err != nil {
		s.State = StateFailed
		return err
	}
	s.State = StatePaymentCharged

	if err := reserveStock(s.OrderID); err != nil {
		s.State = StateCompensatingPayment
		if compErr := refundPayment(s.OrderID); compErr != nil {
			return fmt.Errorf("compensation failed: %w (original: %v)", compErr, err)
		}
		s.State = StateFailed
		return err
	}

	s.State = StateCompleted
	return nil
}

func main() {
	saga := &OrderSaga{OrderID: "order-47291"}
	err := saga.Run()
	fmt.Printf("final state: %d, err: %v\n", saga.State, err)
}
```

### TypeScript, the outbox-backed step contract

This shows the piece dimension 7's dynamics section calls out as the most
commonly missed correctness requirement, a step's local write and its
outgoing saga message committed atomically. The transaction and outbox are
simulated in memory for a runnable, self-contained example.

```typescript
interface OutboxMessage {
  sagaId: string;
  type: string;
  payload: unknown;
}

class InMemoryStore {
  private orders = new Map<string, { status: string }>();
  private outbox: OutboxMessage[] = [];

  // Atomic in the sense that both writes happen or neither does.
  chargeAndEnqueue(sagaId: string, message: OutboxMessage): void {
    this.orders.set(sagaId, { status: "payment_charged" });
    this.outbox.push(message);
  }

  getOrderStatus(sagaId: string): string | undefined {
    return this.orders.get(sagaId)?.status;
  }

  drainOutbox(): OutboxMessage[] {
    const drained = this.outbox;
    this.outbox = [];
    return drained;
  }
}

function chargePaymentStep(store: InMemoryStore, sagaId: string): void {
  store.chargeAndEnqueue(sagaId, {
    sagaId,
    type: "PaymentCharged",
    payload: { sagaId },
  });
}

const store = new InMemoryStore();
chargePaymentStep(store, "order-47291");
console.log("order status", store.getOrderStatus("order-47291"));
console.log("outbox to relay", store.drainOutbox());
```

### Python, a choreography listener with no orchestrator

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class Event:
    type: str
    order_id: str


class EventBus:
    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[Event], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        self._listeners.setdefault(event_type, []).append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._listeners.get(event.type, []):
            handler(event)


bus = EventBus()


def on_order_created(event: Event) -> None:
    print(f"payment service charging order {event.order_id}")
    bus.publish(Event(type="PaymentCharged", order_id=event.order_id))


def on_payment_charged(event: Event) -> None:
    print(f"inventory service reserving stock for order {event.order_id}")
    # Simulate a failure with no orchestrator to catch it centrally.
    bus.publish(Event(type="StockReservationFailed", order_id=event.order_id))


def on_stock_reservation_failed(event: Event) -> None:
    print(f"payment service compensating (refunding) order {event.order_id}")
    bus.publish(Event(type="PaymentRefunded", order_id=event.order_id))


bus.subscribe("OrderCreated", on_order_created)
bus.subscribe("PaymentCharged", on_payment_charged)
bus.subscribe("StockReservationFailed", on_stock_reservation_failed)

bus.publish(Event(type="OrderCreated", order_id="order-47291"))
```

## 18. References

1. Hector Garcia-Molina, Kenneth Salem. "Sagas." Proceedings of the 1987 ACM
   SIGMOD International Conference on Management of Data, pages 249 to 259.
   https://dl.acm.org/doi/10.1145/38713.38742
   Verified 2026-08-02. Source of the original saga definition, the
   compensating transaction concept, and the database-lock-contention
   problem the pattern was first designed to solve.
2. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*. Addison-Wesley, 2003.
   ISBN 978-0321200686. Messaging Systems chapter, Process Manager pattern.
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html
   Verified 2026-08-02. Source of the Process Manager intent, its
   distinction from Routing Slip, and the named bottleneck drawback used in
   dimension 3 and dimension 11.
3. Chris Richardson. *Microservices Patterns*. Manning, 2018.
   ISBN 978-1617294549. Chapter 4, "Managing transactions with sagas."
   Source of the modern microservices restatement of the saga pattern, the
   orchestration versus choreography naming, and the Eventuate Tram
   reference implementations.
4. Chris Richardson. microservices.io, "Pattern. Saga."
   https://microservices.io/patterns/data/saga.html
   Verified 2026-08-02. Source of the choreography and orchestration
   definitions cited in dimension 1, and the Eventuate framework production
   use cited in dimension 9.
5. Particular Software. NServiceBus documentation, "Sagas."
   https://docs.particular.net/nservicebus/sagas/
   Verified 2026-08-02. Source of the `Saga<T>`, `IAmStartedByMessages<T>`,
   `ContainSagaData`, and correlation-property details cited in dimension 8
   and dimension 9.
6. Temporal Technologies. Temporal documentation, "Workflows."
   https://docs.temporal.io/workflows
   Verified 2026-08-02. Source of the durable-execution and Event History
   replay description cited in dimension 8.
7. Amazon Web Services. AWS Step Functions Developer Guide, "What is Step
   Functions?"
   https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html
   Verified 2026-08-02. Source of the state-machine model, the `Retry` and
   `Catch` error-handling fields, and the Standard workflow execution
   guarantees cited in dimension 8 and dimension 9.
8. Uber Engineering. "Conducting Better Business with Uber's Open Source
   Orchestration Tool, Cadence."
   https://www.uber.com/en-CO/blog/open-source-orchestration-tool-cadence-overview/
   Verified 2026-08-02. Source of the Cadence saga-compensation description
   and the 12 billion executions per month production-scale figure cited in
   dimension 9.
9. Camunda. "Orchestration vs Choreography," Camunda blog, February 2023.
   https://camunda.com/blog/2023/02/orchestration-vs-choreography/
   Verified 2026-08-02. Source of Camunda's Process Manager positioning
   cited in dimension 9.
