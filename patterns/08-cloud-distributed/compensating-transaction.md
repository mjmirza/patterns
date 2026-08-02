---
name: Compensating Transaction
slug: compensating-transaction
family: 08-cloud-distributed
category: Data consistency
aliases: [Compensating Action, Undo Transaction, Semantic Rollback]
first_described: "Garcia-Molina and Salem 1987 (mechanism); Microsoft Azure Architecture Center (named catalog entry)"
maturity: canonical
related: [saga, retry, circuit-breaker, transactional-outbox, event-sourcing, scheduler-agent-supervisor, idempotent-receiver]
incompatible_with: [two-phase-commit]
verified: 2026-08-02
---

# Compensating Transaction

## 1. Name, aliases, and lineage

The canonical name in this catalog is Compensating Transaction, following the
name Microsoft's Azure Architecture Center gives its standalone pattern page,
"Compensating Transaction Pattern" (Microsoft Learn, Azure Architecture Center,
*Compensating Transaction Pattern*, verified 2026-08-02 at
https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction).
That page states its purpose in one line. "Use the Compensating Transaction
pattern to undo work when a step of an eventually consistent operation fails
in distributed systems" (same source).

The mechanism, not the catalog entry, is older. Hector Garcia-Molina and
Kenneth Salem's 1987 paper "SAGAS" is the first place the term compensating
transaction is defined precisely for computing. A saga is a sequence of
transactions that can be interleaved with other transactions by the database
management system, and either the whole sequence completes or compensating
transactions run to remove the effect of the steps that did commit before a
failure (Garcia-Molina and Salem, "SAGAS", *Proceedings of the 1987 ACM SIGMOD
International Conference on Management of Data*, pages 249 to 259, DOI
10.1145/38713.38742). In that 1987 paper the compensating transaction is not a
pattern of its own. It is the mechanism a saga uses to undo one already
committed sub-transaction, defined precisely enough that the paper requires
each compensating transaction to itself be a proper transaction that a crash
can retry to completion.

So there are two lineages that this entry has to keep separate, because a
reader coming from either one will otherwise misread the other.

- In the database transaction-processing literature, a compensating
  transaction is a component of a saga. It has no independent existence,
  because a saga is precisely the unit that ties an original step to its
  compensation and guarantees the DBMS runs the right one at the right time.
- In the cloud architecture literature, Compensating Transaction is catalogued
  as its own pattern, one level below Saga in Azure's own taxonomy, because a
  single failed step inside a larger eventually consistent workflow can be
  undone by one compensating action without invoking the full saga machinery.
  The Azure page says exactly this relationship. "This approach is similar to
  the Saga distributed transactions pattern" and elsewhere, on the Saga page
  itself, "Saga uses compensating transactions for failure recovery" (same
  Azure page, Related resources section, verified 2026-08-02).

Business Process Model and Notation, BPMN 2.0, formalises the same idea as a
first-class modelling construct rather than a code-level convention. The BPMN
2.0 specification is maintained by the Object Management Group at
http://www.omg.org/spec/BPMN/2.0/ (verified 2026-08-02, specification index
page, formal edition formal-13-12-09). BPMN defines a Compensation Boundary
Event attached to an activity, and a Compensation Handler, an activity that is
excluded from the normal sequence flow and is invoked only when a compensation
throw event fires for the scope that contains the completed activity. Camunda,
the commercial vendor whose engine implements the specification, documents the
runtime behaviour this way. "A compensation activity becomes enabled when the
activity it is associated with transitions into state Completed", and the
compensation handler for an activity is invoked only if that activity actually
completed, never for an activity that is still active or was terminated by
some other means (Camunda, *Compensation events*, verified 2026-08-02 at
https://docs.camunda.io/docs/components/modeler/bpmn/compensation-events/).

Aliases in current use. **Compensating Action** is the name Temporal, the
workflow engine, prefers in its own writing, because a compensation is not
always transactional in the ACID sense, it is simply an action with an
opposite intent (Temporal, *Saga Design Pattern Explained for Distributed
Systems*, verified 2026-08-02 at
https://temporal.io/blog/saga-pattern-made-easy). **Undo Transaction** and
**Semantic Rollback** appear in engineering blogs and internal documentation
as informal restatements. Semantic Rollback is the more precise of the two,
because it draws the exact contrast this entry rests on. it is a rollback in
intent, computed by application semantics, not a rollback in mechanism,
computed by a log.

## 2. Problem and context

A single database transaction gives you atomicity for free. If the third of
four writes fails, the database engine rolls the first two back using its own
write-ahead log, and the caller never observes a partial state. That guarantee
stops the instant the four writes cross a transaction boundary, and in a
cloud-hosted, service-oriented, or microservices system they almost always
do. An order-placement flow that debits a payment provider, decrements
inventory in a separate service, books a shipping slot with a carrier's API,
and writes a confirmation row, touches four systems that do not share a
transaction manager and frequently do not even share a network zone.

The Azure Architecture Center frames the problem precisely. "Cloud
applications frequently modify data that is spread across various data
sources in different geographic locations. To avoid contention and improve
performance in a distributed environment, applications should implement
eventual consistency instead of strong transactional consistency" (Microsoft
Learn, *Compensating Transaction Pattern*, Context and problem section,
verified 2026-08-02). Eventual consistency buys back the performance and
availability that a distributed two-phase commit would cost, at the price of
a window in which the system's overall state is visibly inconsistent while a
multi-step operation is mid-flight.

The problem this pattern answers is what happens when step three of four
fails inside that window. You cannot roll the database back, because there is
no single database and no single log spanning all four systems. You cannot
always restore the earlier state by simply reversing the write, because a
concurrent operation may have already observed or built on top of the
now-committed state, and blindly overwriting it back to the old value would
silently destroy that concurrent work. The same source names this directly.
"You can't always roll back the data because other concurrent application
instances might change the data. Even when concurrent instances don't change
the data, it can be more complex to undo a step than to restore the original
state. You might need to apply business-specific rules" (same source, Context
and problem section).

The context in which the pattern belongs, then, has four properties at once.
The operation spans more than one autonomous data store or service boundary.
The system deliberately trades strong consistency for eventual consistency to
keep latency and availability acceptable. A step can fail after earlier steps
have already committed and become visible to other actors. And undoing the
earlier steps is not a mechanical reverse of the write, it is itself a
business decision, sometimes with a cost, a fee, a partial refund, or a
requirement for a person to approve it.

## 3. Forces

The pattern balances several pressures that pull in different directions, and
naming which ones it favours and which it accepts a cost on is the honest way
to describe it rather than presenting it as free.

**Consistency versus availability and latency.** A compensating transaction
exists specifically because the alternative, holding a distributed lock or
running a two-phase commit across every participant, buys stronger
consistency at the direct cost of availability and tail latency under
partition. This is judgement, in the sense the template distinguishes, but it
rests on the well-established CAP framing that a partition forces a choice
between consistency and availability. The pattern is a deliberate choice
toward availability, accepting a temporary inconsistent window in exchange for
each service staying independently responsive.

**Correctness of the undo versus mechanical simplicity.** A literal rollback,
restoring a captured "before" value, is mechanically simple and can be coded
generically. It is also frequently wrong, because it silently discards any
work a concurrent actor did on top of the now-reverted value. A compensating
transaction, by contrast, is application-specific and must be hand-written per
step, which is more expensive to build and reason about but is the only
approach that correctly handles concurrent writers.

**Coupling.** A compensating step usually has to know something about the
forward step it undoes, at minimum its identity and any resource it consumed
that must be released. Well-designed compensations minimise this to an
idempotent, addressable identifier rather than the full business context, but
some coupling between the forward operation and its compensation is
unavoidable, because the compensation exists only to undo that specific
operation's effect.

**Operability and auditability.** Because compensations run after the fact,
often much later, and other operations can have changed the world in between,
the system needs a durable, correlated record of exactly which forward steps
completed, so the correct and only the correct compensations run. The Azure
guidance is explicit that the infrastructure "reliably monitors compensation
logic progress" and that operators must be able to "correlate and audit both
the original operation and its compensation end-to-end" (Microsoft Learn,
*Compensating Transaction Pattern*, Problems and considerations section,
verified 2026-08-02). This is a real operational cost, not a formality, since
without it a partial failure becomes an unresolved mystery days later.

**Reversibility versus finality.** Some steps genuinely cannot be undone. A
physical package handed to a courier, an email already delivered to an inbox,
a payment captured after the provider's chargeback window has closed. The
pattern only works for the subset of steps that are compensable, so a system
that uses it must draw a hard line, ahead of time, between the compensable
steps that can be freely retried into and the irreversible steps that must
happen last, only after every earlier, compensable step has already
succeeded. The Azure page names this directly under a heading it calls points
of no return. "Define clear points of no return and irreversible steps... You
can't safely or meaningfully undo some operations, such as external side
effects or legally binding actions... Design the workflow so that irreversible
steps occur only after all critical validations succeed" (same source,
Problems and considerations section).

## 4. Applicability and non-applicability

Use a compensating transaction when the following hold together.

- A business operation spans more than one service, database, or bounded
  context, so no shared transaction manager can span all of it.
- The system has already chosen an eventual consistency model for this
  operation, for performance, availability, or architectural reasons, rather
  than paying for a synchronous distributed transaction.
- Undoing a completed step requires business logic, not a mechanical restore
  of a prior value. A refund is not the exact reverse of a charge, it can
  differ by a fee. A seat release is not identical to never having booked it,
  it can leave a waitlisted customer in a new position.
- The step in question is genuinely compensable. Its effect can be neutralised
  by a later, well-defined action, even if that action does not perfectly
  restore the world to its exact earlier state.
- The workflow can tolerate a period of visible partial state between a
  failure and the completion of its compensation, and the business accepts
  that risk window as the cost of the architecture.

Do NOT reach for a compensating transaction when any of the following holds.
This list is deliberately as long as the applicability list, because it is
the one most catalogs shorten and it is where the pattern is most often
misapplied.

- **The operation fits inside a single database transaction.** If every write
  can share one ACID transaction boundary, a compensating transaction adds
  cost and a new failure surface for no benefit. Use the database's native
  rollback.
- **The failure is transient and retrying the same step will likely
  succeed.** The Azure guidance states this as a design principle. "Retry
  logic that treats more errors as transient can help minimize failures that
  trigger a compensating transaction... Only stop the operation and trigger
  compensation if the step fails repeatedly or you can't recover it" (Microsoft
  Learn, *Compensating Transaction Pattern*, Problems and considerations
  section, verified 2026-08-02). Compensation is a last resort after retry is
  exhausted, never a substitute for retry, because a retry that would have
  succeeded is strictly cheaper and strictly simpler than an undo followed by
  a fresh attempt.
- **The step is irreversible.** A message already sent to a human, a physical
  shipment already dispatched, funds already settled past the provider's
  reversal window. There is no compensation for these, only downstream
  remediation such as a customer-service credit, which is a different,
  human-mediated process, not this pattern.
- **The system cannot tolerate the visible inconsistent window at all**, for
  example a safety-critical control system or a regulatory ledger that must
  never show an intermediate state to any reader. Use a strongly consistent,
  atomic mechanism, accepting its availability and latency cost, instead.
- **The domain has no sensible undo, only an alternative forward path.** The
  Azure page's own travel example makes this concrete. if hotel booking H1
  fails after flights F1, F2, and F3 succeeded, the better response is
  frequently not to compensate the flights but to offer the customer a
  different hotel and let a human choose whether to cancel (same source,
  Solution section). Reaching automatically for compensation when a forward
  alternative exists produces worse customer outcomes for a cost the customer
  never asked to pay.
- **You are tempted to implement compensation as a blind restore of a
  captured prior value.** That is not this pattern, it is a race condition
  waiting for a concurrent write, and it is explicitly warned against by the
  source catalog entry (same source, Solution section, "you can simply
  restore the system to its original state, but this approach can overwrite
  changes from other concurrent application instances").

## 5. Structure

A compensating transaction is not, by itself, a multi-participant coordination
protocol. It is a single well-defined unit with an internal structure, plus
the surrounding record-keeping that lets some coordinator, whether a saga
orchestrator, a BPMN engine, or a plain retry loop, find and invoke it at the
right moment. The participants are the following.

- **The forward operation.** The original business action, for example
  `ReserveInventory`, that has a durable, externally visible side effect once
  it commits.
- **The compensation record.** A durable entry, written at or immediately
  after the forward operation commits, that names the forward operation, its
  identity or idempotency key, and enough context, such as the reservation
  identifier and quantity, to reverse it without re-deriving that context from
  a possibly-changed present state.
- **The compensating action.** A separate operation, for example
  `ReleaseInventory`, that consumes the compensation record and produces a new
  forward-moving effect whose business result is the semantic opposite of the
  original. It is not a delete of the original record, it is a new committed
  fact, visible in the audit trail alongside the original.
- **The trigger.** The event that decides a compensation must run. Typically a
  later step in the same workflow failing irrecoverably, or an explicit
  cancellation request from outside the workflow.
- **The compensation coordinator.** The component that decides which
  compensation records apply, in what order to invoke them, and how to retry a
  compensating action that itself fails. In the simplest case this coordinator
  is folded into the same orchestrator that ran the forward steps, as in the
  Saga pattern. In BPMN it is the process engine's compensation-event
  machinery. In the Azure reference implementation it is an orchestrator
  process reading its own event store (Microsoft Learn, *Compensating
  Transaction Pattern*, Example section, verified 2026-08-02).
- **The idempotency guard.** A mechanism, usually a stored key checked before
  the compensating action executes its side effect, that makes re-running the
  same compensating action safe. The source catalog entry states this as a
  requirement rather than an option. "Compensating transactions don't always
  work. Define the steps in a compensating transaction as idempotent commands
  so that you can repeat them if the compensating transaction itself fails"
  (same source, Problems and considerations section).

## 6. ASCII structure diagram

```
+------------------------------------------------------------+
|                    Compensation Coordinator                 |
|  (saga orchestrator | BPMN engine | plain retry supervisor) |
+------------------------------------------------------------+
        |                          |                    ^
        | invoke                   | invoke on failure  | reads
        v                          v                    |
+----------------+          +------------------+   +-------------------+
| Forward Op      |--writes->| Compensation      |   | Compensation      |
| (e.g. Reserve   |          | Record Store       |   | Record            |
|  Inventory)     |          | (append-only log,  |<--| forward_id,       |
+----------------+          |  Cosmos DB, table,  |   | step_name,        |
        | commits             |  event store)       |   | undo_context,    |
        v                    +------------------+   | status            |
+----------------+                                    +-------------------+
|  External       |
|  side effect     |                          on trigger
|  (inventory       |                                |
|   decremented)   |                                v
+----------------+                          +------------------+
                                              | Compensating      |
                                              | Action             |
                                              | (e.g. Release       |
                                              |  Inventory)         |
                                              +------------------+
                                                       | guarded by
                                                       v
                                              +------------------+
                                              | Idempotency Guard  |
                                              | (dedupe key check) |
                                              +------------------+
                                                       | commits
                                                       v
                                              +------------------+
                                              | New forward-moving |
                                              | fact recorded in    |
                                              | the audit trail     |
                                              +------------------+
```

## 7. Dynamics

```
Happy path, no failure.

  Coordinator      ForwardOp(A)    ForwardOp(B)    ForwardOp(C)
       |                |               |               |
       |--- invoke ---->|               |               |
       |<-- committed --|               |               |
       |    (record A undo info)        |               |
       |--- invoke -------------------->|               |
       |<-- committed --|               |               |
       |    (record B undo info)        |               |
       |--- invoke ---------------------------------->|
       |<-- committed --|               |               |
       |                              overall operation succeeds


Failure at C, compensation runs, LIFO order.

  Coordinator      ForwardOp(A)    ForwardOp(B)    ForwardOp(C)
       |--- invoke ---->|               |               |
       |<-- committed --|               |               |
       |--- invoke -------------------->|               |
       |<-- committed --|               |               |
       |--- invoke ---------------------------------->|
       |<-- FAILS ------------------------------------|
       |
       |  compensation begins, most recent completed step first
       |
       |--- CompensateB (undo B) ------>|
       |<-- committed --|               |
       |--- CompensateA ->|
       |<-- committed --|
       |
       |    overall operation reports failure, system state
       |    is now compensated, not identical to the pre-A state,
       |    but consistent under the business rules for undo
```

The reverse order shown above is the common default, and the Temporal SDK
implements exactly this as its default Saga behaviour, running registered
compensations in last-in-first-out order, the most recently completed step
compensated first (php.temporal.io, *Saga in package Application*, verified
2026-08-02 at https://php.temporal.io/classes/Temporal-Workflow-Saga.html).
Reverse order is a default, not a law. The Azure catalog entry is explicit
that it can be overridden. "The compensating transaction steps don't always
reverse the original operation in the exact opposite order. For example, if
one data store is more sensitive to inconsistencies than another, undo
changes to that store first" (Microsoft Learn, *Compensating Transaction
Pattern*, Problems and considerations section, verified 2026-08-02). The same
source also notes some compensations can run in parallel rather than
sequentially, when they touch independent resources with no ordering
dependency between them.

## 8. Implementation variants

**Sequential LIFO compensation, coordinator-owned.** The default shape used by
Temporal's `Saga` helper class and by hand-rolled orchestrators. The
coordinator keeps an in-memory or durable stack of registered undo callbacks
and pops them in reverse order on failure. Simple to reason about, correct
when compensations are independent, but serial and therefore slow when a
workflow has many steps and each compensation call has real network latency.

**Parallel compensation.** Temporal's `Saga` class exposes a
`setParallelCompensation` flag that, when enabled, fires every registered
compensation concurrently rather than one at a time, and always collects
every resulting exception rather than stopping at the first failure
(php.temporal.io, *Saga in package Application*, verified 2026-08-02). This
variant trades strict ordering for lower total compensation latency, and is
only correct when the compensations genuinely do not depend on each other's
completion.

**Declarative compensation via BPMN compensation events.** Rather than the
application code explicitly registering an undo callback, the process
definition itself declares, for each activity, a Compensation Boundary Event
and an associated Compensation Handler activity. The engine, not the
application, decides when a compensation throw event fires and which
handlers to invoke, and restricts this to activities that actually reached
the Completed state (Camunda, *Compensation events*, verified 2026-08-02).
This variant moves the compensation topology out of code and into a
process model that non-developers can read, at the cost of coupling the
application to a BPM engine's runtime and modelling language.

**Annotation-driven compensation for Long Running Actions.** MicroProfile
LRA, and its Red Hat implementation Narayana, mark a compensating method with
an `@Compensate` annotation on a JAX-RS resource. Enlistment happens
automatically the first time the annotated resource participates in an LRA,
and the specification guarantees the compensating method is invoked if the
LRA is later cancelled, though it does not mandate the exact timing of that
invocation, only that it eventually happens (Eclipse Foundation, *MicroProfile
Long Running Actions 2.0*, section on the `@Compensate` annotation, verified
2026-08-02 at
https://download.eclipse.org/microprofile/microprofile-lra-2.0/microprofile-lra-spec-2.0.html).
This variant is idiomatic to the Jakarta EE and MicroProfile ecosystem and
integrates compensation directly into REST resource method dispatch.

**Orchestrated compensation as a state-machine branch.** AWS Step Functions
models the compensation path as an explicit set of states in the same state
machine that runs the forward path. A `Choice` state after each forward task
routes success to the next forward task and any error to a dedicated
compensating Lambda task, chained backward through the earlier compensating
tasks (AWS, *Saga orchestration pattern*, AWS Prescriptive Guidance, verified
2026-08-02 at
https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html).
This variant makes the compensation topology visible as literal graph nodes in
the workflow definition, which is easy to audit visually but grows the state
machine definition linearly with the number of compensable steps.

**Choreographed compensation via events.** Rather than one coordinator
knowing every step and its compensation, each service listens for a
cancellation or failure event and independently runs its own compensation if
it had previously completed the corresponding forward step. This removes the
single coordinator as a component but pushes the responsibility for correct
sequencing onto the event ordering and each service's own bookkeeping of
whether it needs to compensate. This is the same choreography-versus-
orchestration axis the Saga pattern entry in this catalog covers in depth,
and a compensating-transaction implementation inherits whichever choice the
surrounding saga makes.

## 9. Known production uses

- **Azure Container Apps reference architecture.** Microsoft's own published
  implementation runs an orchestrator container that coordinates two
  downstream services over Azure Service Bus, records both the forward
  execution state and the corresponding compensating action for each
  completed step into Azure Cosmos DB, and on failure replays the compensating
  actions in reverse order, moving unresolvable failures to a Service Bus
  dead-letter queue and raising alerts through Application Insights and Azure
  Monitor (Microsoft Learn, *Compensating Transaction Pattern*, Example
  section, verified 2026-08-02).
- **AWS Step Functions saga orchestration.** AWS's own prescriptive guidance
  ships a complete sample, `Place Order`, `Update Inventory`, `Make Payment`
  as the forward path, and `Revert Payment`, `Revert Inventory`, `Remove
  Order` as the compensating tasks invoked when a later step's `Choice` state
  detects an error status (AWS, *Saga orchestration pattern*, verified
  2026-08-02, with the full sample published at
  https://github.com/aws-samples/saga-orchestration-netcore-blog per the same
  page).
- **Temporal's `Saga` helper class.** Shipped as a first-class construct in
  Temporal's SDKs across multiple languages including PHP, Java, and Go,
  giving workflow authors `addCompensation`, sequential LIFO execution by
  default, an optional parallel mode, and an option to continue running
  remaining compensations after one throws rather than aborting the whole
  compensation chain (php.temporal.io, *Saga in package Application*, verified
  2026-08-02).
- **BPMN 2.0 process engines.** Camunda, Flowable, and other BPMN 2.0 conformant
  engines implement the Compensation Boundary Event and Compensation Handler
  constructs from the OMG BPMN 2.0 specification (http://www.omg.org/spec/BPMN/2.0/,
  verified 2026-08-02) as first-class modelling elements, letting a business
  analyst attach an undo activity to any completed task without writing
  coordination code (Camunda, *Compensation events*, verified 2026-08-02).
- **MicroProfile Long Running Actions, implemented by Narayana.** The
  `@Compensate` annotation and LRA coordinator protocol are specified by the
  Eclipse Foundation's MicroProfile LRA 2.0 specification and are implemented
  as a JAX-RS filter and coordinator service in Red Hat's Narayana transaction
  manager, giving Java EE and Quarkus applications a REST-native way to
  register a compensating method per resource (Eclipse Foundation,
  *MicroProfile Long Running Actions 2.0*, verified 2026-08-02).

## 10. Consequences

**Positive.**

- Correctness under concurrency that a naive value restore cannot offer,
  because the compensation is defined in terms of business intent rather than
  a snapshot that a concurrent writer may have already invalidated.
- No requirement for a distributed lock manager or a two-phase commit
  coordinator across services, so each participating service keeps its own
  local transactional boundary and its own availability characteristics.
- The undo is visible in the audit trail as a first-class fact, not a silent
  erasure, which is frequently a compliance and debugging advantage over a
  mechanism that tries to make the failed attempt disappear.
- The pattern composes cleanly with retry, because retry is tried first and
  compensation is reserved for the case retry cannot resolve, which keeps the
  expensive, business-specific undo path off the common case.

**Negative.**

- Compensation logic is application-specific and cannot be generated
  automatically from the forward operation, so every compensable step doubles
  the amount of business logic that must be written, reviewed, and kept in
  sync with the forward step as requirements change.
- The system never actually returns to its exact pre-operation state. The
  Azure catalog entry states this plainly. "A compensating transaction
  doesn't necessarily return the system data to its state at the start of the
  original operation. Instead, the transaction compensates for the work that
  the operation completes successfully before it failed" (Microsoft Learn,
  *Compensating Transaction Pattern*, Problems and considerations section,
  verified 2026-08-02). Readers who assume compensation means rollback will
  build incorrect expectations into downstream code.
- A period of visible inconsistency exists between the original failure and
  the completion of compensation, and during that window other actors can
  observe and act on state that will shortly be reversed.
- Compensating actions can themselves fail, and failing to plan for that
  failure produces a stuck workflow with no defined recovery path, discussed
  in detail in dimension 11.
- Determining which steps require irreversible-versus-compensable treatment,
  and enforcing that irreversible steps run only after every compensable step
  has committed, is an ongoing design discipline, not a one-time decision, and
  it is easy to violate accidentally as a workflow gains new steps over time.

## 11. Failure modes and misuse

**Symptom.** A refund or a release action runs twice for the same original
charge or reservation, producing a duplicate credit or over-releasing an
inventory count. **Cause.** The compensating action was not built to be
idempotent, and a retry after a transient network failure, or a redelivered
message, invoked it a second time. **Fix.** Give every compensating action a
deterministic idempotency key derived from the forward operation's identity,
persist which keys have already been applied, and check that store before
performing the side effect. The Azure catalog entry states this as a
requirement, not a nice-to-have. "Define the steps in a compensating
transaction as idempotent commands so that you can repeat them if the
compensating transaction itself fails" (Microsoft Learn, *Compensating
Transaction Pattern*, Problems and considerations section, verified
2026-08-02).

**Symptom.** A workflow is stuck. Its status shows a failed forward step, but
neither the forward step nor its compensation has resolved days later, and no
alert fired. **Cause.** The compensating action itself failed, and the system
had no retry, dead-letter, or escalation path for a failed compensation, only
for a failed forward step. **Fix.** Treat the compensating action as a
first-class operation with its own retry policy and its own dead-letter
destination. In the Azure reference architecture, a compensation that fails
transiently is retried by the messaging layer, and a compensation that
exhausts its retries moves to a dead-letter queue with structured telemetry,
which then triggers a human alert rather than silently stalling (Microsoft
Learn, *Compensating Transaction Pattern*, Example section, verified
2026-08-02).

**Symptom.** A step that a customer or an auditor believed was undone is
still, functionally, in effect. For example, an email confirmation was
already delivered even though the order it confirmed was later compensated.
**Cause.** A genuinely irreversible step was treated as compensable and
sequenced before the workflow's true point of no return, so a subsequent
failure triggered a compensation attempt against something that has no valid
undo. **Fix.** Enumerate, at design time, which steps in the workflow are
irreversible, and place them last, only after every compensable step has
already committed successfully. The Azure guidance names this explicitly as a
design discipline. "Define clear points of no return and irreversible
steps... Design the workflow so that irreversible steps occur only after all
critical validations succeed" (same source, Problems and considerations
section).

**Symptom.** A compensating action restores a value that a concurrent process
had already changed for a legitimate, unrelated reason, silently destroying
that concurrent change. **Cause.** The compensation was implemented as a blind
restore of a captured earlier snapshot instead of a semantic, business-aware
undo. **Fix.** Replace snapshot-restore compensation with a compensation that
expresses intent, for example decrementing a counter by the exact amount the
forward step incremented it, rather than resetting the counter to its earlier
absolute value. The source catalog entry warns against the naive approach
directly. "You might think that you can simply restore the system to its
original state, but this approach can overwrite changes from other concurrent
application instances" (same source, Solution section).

**Symptom.** A step failure that would have succeeded on a second attempt
instead triggers a full, expensive, multi-service compensation cascade.
**Cause.** The failure classifier does not distinguish a transient error, a
timeout, a momentary rate limit, from a genuine, non-retryable business
failure, so every failure of any kind falls straight through to compensation.
**Fix.** Classify errors before deciding to compensate, and retry transient
failures using the Retry pattern first. Compensation is invoked only when
retries are exhausted or the failure is classified as non-transient, per the
Azure reference architecture's own model, which "uses retries first to
preserve forward progress" and invokes compensation "only when forward
progress becomes impossible" (Microsoft Learn, *Compensating Transaction
Pattern*, Example section, verified 2026-08-02).

**Symptom.** It is impossible to determine, from logs alone, which
compensations ran, in what order, against which forward operations, after an
incident. **Cause.** The compensation record was not durably correlated to the
forward operation with a shared identifier, so the two halves of the audit
trail cannot be joined after the fact. **Fix.** Persist a compensation record
at or immediately after the forward operation commits, keyed by a stable
identifier that both the forward and the compensating call carry, so that
correlation and audit end to end is possible without reconstructing intent
from timestamps alone.

## 12. Trade-off matrix

| Force | Compensating Transaction | Distributed Two-Phase Commit | Blind snapshot restore | Retry only, no undo |
|---|---|---|---|---|
| Consistency model | Eventual, with a defined compensated end state | Strong, atomic across participants | Eventual, but frequently incorrect under concurrency | Eventual, but leaves partial state unresolved on permanent failure |
| Correctness under concurrent writers | Correct, because the undo is expressed as business intent | Correct, because no other writer can observe the partial state at all | Incorrect, can overwrite unrelated concurrent changes | Not applicable, does not address partial failure |
| Availability under partition | High, each participant stays independently available | Low, a participant outage blocks the whole transaction | High, but at a correctness cost | High |
| Implementation cost per step | High, one compensation must be authored per compensable step | Low per step, but very high to build and operate the coordinator itself | Low to write, expensive later in incident cost | Lowest, no undo logic at all |
| Auditability | High, the undo is a new recorded fact | Moderate, the abort simply never becomes visible | Low, the earlier state is silently overwritten | Low, a permanently failed step has no recorded resolution |
| Suitable for irreversible steps | No, by definition | Yes, because nothing is visible until commit | No | No, a permanent failure is simply left unresolved |

## 13. Related and incompatible patterns

**Saga.** Saga is the coordinating protocol; Compensating Transaction is the
mechanism each saga step relies on to undo itself. A saga without
compensating transactions for its compensable steps is not a saga in the
Garcia-Molina and Salem sense, it is only a sequence of independent local
transactions with no recovery story. This catalog's own Saga entry documents
the orchestration and choreography topologies that decide which coordinator
invokes which compensation and in what order.

**Retry.** Retry and compensation sit on the same axis but at opposite ends of
cost. Retry is always tried first, because a transient failure resolved by
retry is strictly cheaper than a compensation followed by a fresh attempt.
Compensation is reached for only once retry is exhausted or the failure is
classified as non-transient.

**Circuit Breaker.** A circuit breaker protects a forward call from repeatedly
hammering a failing dependency, and its open state is frequently the trigger
that causes a workflow to give up on retrying a forward step and fall through
to compensation instead, rather than retrying indefinitely against a
dependency that is known to be down.

**Transactional Outbox.** A compensating action, like any other business
operation, often needs to publish an event or send a message reliably as part
of undoing a step, for example notifying a downstream system that a
reservation was released. The Transactional Outbox pattern is the mechanism
that makes that publish atomic with the compensation's own state change, so
the compensation cannot commit its own effect while losing the notification
that tells the rest of the system it happened.

**Event Sourcing.** An event-sourced aggregate makes writing a compensating
action more natural in one specific way. because every state change is
already an explicit, named event, a compensation is simply a new event with an
opposite meaning appended to the same stream, rather than a mutation that must
be reconstructed from a snapshot. Event Sourcing is not required for
Compensating Transaction, but it removes one common source of the blind-
snapshot misuse named in dimension 11.

**Scheduler Agent Supervisor.** The Azure catalog cross-references this
pattern directly for the case where an entire distributed process, not just
one step, needs monitoring, retry, and, when necessary, compensation, treating
the compensating transaction as one tool the supervisor reaches for rather
than the whole coordination story.

**Idempotent Receiver.** Every compensating action must itself be idempotent,
per dimension 11, and the Idempotent Receiver pattern, whether implemented as
a dedupe table, a natural key check, or a version-conditioned write, is the
concrete mechanism most implementations use to guarantee that.

**Incompatible with Two-Phase Commit.** The two patterns solve the same
underlying problem, undoing partial work across participants, by opposite
means. Two-phase commit prevents partial visibility in the first place by
holding participant locks until every participant has voted to commit.
Compensating Transaction accepts partial visibility and repairs it afterward.
Combining both in the same workflow is not merely redundant, it actively
conflicts, because the lock-holding discipline two-phase commit requires is
precisely what an eventually consistent, compensable workflow is designed to
avoid.

## 14. Refactoring path in and out

**Introducing the pattern into code that lacks it.** Start from a workflow
that currently has no undo story at all, typically a sequence of calls with
no compensation and a failure path that simply logs an error and leaves
whatever succeeded in place.

1. Enumerate every step in the workflow and classify each one as compensable
   or irreversible, writing this classification down explicitly rather than
   leaving it implicit in code structure.
2. Reorder the workflow, where the business allows it, so every irreversible
   step runs after every compensable step, establishing the point of no
   return as a concrete position in the sequence rather than an assumption.
3. For each compensable step, write its compensating action as a separate,
   named operation, and give it its own idempotency key derived from the
   forward step's identity, before wiring any coordination around it.
4. Add a durable compensation record, written at or immediately after each
   forward step commits, carrying enough context for the compensating action
   to run without needing to re-derive that context from a state that may
   already have moved on.
5. Wire a coordinator, whether an existing saga orchestrator, a workflow
   engine's saga helper, or a hand-rolled supervisor, to invoke the
   compensations in the chosen order when a later step fails irrecoverably,
   after retry is exhausted.
6. Add retry, and a dead-letter or escalation path, to the compensating
   actions themselves, not only to the forward steps, closing the stuck-
   workflow failure mode from dimension 11.
7. Instrument correlation between each forward operation and its compensation
   so an operator can reconstruct, after the fact, exactly what happened and
   in what order, per dimension 16.

**Removing the pattern when it stops earning its place.** A compensating
transaction earns removal when the workflow it protects has been consolidated
onto a single transactional boundary, for example when two services that
previously owned separate databases have been merged behind one service with
one database, making the multi-step, multi-store failure mode this pattern
exists for structurally impossible. At that point, replace the compensation
logic and its coordinator with a single native database transaction, and
retire the compensation records and their storage once no in-flight workflow
still references them, verifying first that no compensation record has an
open, unresolved status.

## 15. Testing and verification

Compensation logic is easy to leave untested precisely because the failure
path it protects is, by construction, the uncommon case in a healthy system.
Testing it well requires deliberately forcing that uncommon case to happen.

- **Fault injection at every step, not only the last one.** Write a test for
  each forward step that forces that specific step to fail, and assert that
  every compensation for the steps before it runs, in the expected order,
  exactly once. Testing only "the last step fails" misses bugs in how earlier
  steps unwind when a middle step fails.
- **Idempotency tests for every compensating action.** Invoke each
  compensating action twice with the same idempotency key and assert the
  second invocation produces no additional side effect, directly exercising
  the guard named in dimension 11.
- **Compensation-of-compensation tests.** Force the compensating action itself
  to fail on its first attempt and succeed on a retry, and assert the retry
  path, not only the happy path, actually reaches the correct terminal state.
- **Concurrency tests against the naive-restore failure mode.** Run a
  concurrent, unrelated write against the same resource while a compensation
  is in flight, and assert the compensating action's semantic undo, for
  example a relative decrement, does not clobber the concurrent write, in
  contrast to what a blind snapshot restore would do.
- **Test doubles for the compensation coordinator.** Where the coordinator is
  a third-party engine, such as Temporal's `Saga` helper or a BPMN engine,
  test the application-level compensating action in isolation with a plain
  unit test, and separately, at a smaller number of integration test cases,
  verify the coordinator actually invokes it under a forced failure, rather
  than trying to unit test the coordinator's own internal ordering logic.
- **Chaos tests for the correlation store.** Delete or corrupt a compensation
  record in a test environment and assert the system fails safely, for
  example by alerting a human, rather than either silently skipping the
  compensation or throwing an unhandled exception that stalls the entire
  workflow.

## 16. Observability signals

- **Compensation invocation count and rate**, broken down by which forward
  step triggered it. A rising rate of compensations for one specific step is
  the earliest signal that a downstream dependency for that step has degraded,
  often well before its own error rate crosses an alerting threshold.
- **Compensation success and failure counts**, separate from forward-step
  success and failure counts. A healthy system has a low but non-zero
  compensation rate and a compensation success rate close to one hundred
  percent. A compensation failure rate above zero for any sustained period
  means the stuck-workflow failure mode from dimension 11 is actively
  happening.
- **Age of the oldest unresolved compensation record.** A record whose status
  has stayed pending past its expected retry window is the single most
  actionable metric for catching a stalled workflow before a customer
  notices. The Azure reference implementation surfaces exactly this through
  Application Insights and Azure Monitor once a compensation lands on a
  dead-letter queue (Microsoft Learn, *Compensating Transaction Pattern*,
  Example section, verified 2026-08-02).
- **Correlation identifier present on every log line and trace span for both
  a forward operation and its compensation.** Without this, an operator
  cannot answer the single most common incident question, which forward
  operation did this compensation actually undo, without manual log
  archaeology.
- **A healthy dashboard** shows compensation rate as a small, steady fraction
  of total forward-operation volume, a compensation success rate near one
  hundred percent, and zero records older than the retry window. **A failing
  instance** shows a spike in compensation rate correlated with a specific
  downstream dependency, a non-zero and growing count of records stuck past
  their retry window, or a dead-letter queue depth that is rising rather than
  draining.

## 17. Security and privacy implications

A compensating action frequently has to reconstruct enough context to reverse
a business effect, and that context can include the same sensitive data the
forward operation touched, for example a payment instrument identifier needed
to issue a refund, or a customer address needed to redirect or cancel a
shipment. Storing this context in a compensation record, sometimes for an
extended period while a downstream retry or human escalation is pending,
extends the data's retention and exposure surface beyond the lifetime of the
original operation, and that extended surface needs the same access controls,
encryption at rest, and retention policy the original data would carry
elsewhere in the system, not a lighter one because it lives in what looks like
an internal operational log.

Compensating actions are also, functionally, privileged write operations,
frequently able to reverse a financial transaction or release an allocated
resource, and a system that lets an attacker forge or replay a compensation
trigger has effectively handed that attacker the ability to undo legitimate
business outcomes. The idempotency key required in dimension 11 doubles as a
security control here, because it should be tied to the original operation's
identity in a way that is not guessable or forgeable by an external caller,
and the endpoint or message handler that accepts a compensation trigger needs
the same authentication and authorization the forward operation's endpoint
carries, never a weaker check on the theory that it is only cleaning up after
a failure. This is engineering judgement drawn from the general shape of the
pattern rather than a claim sourced to a specific document.

The catalog source is silent on identity and access control specifics for
this pattern, and this entry does not invent a claim where the source does
not make one.

## 18. References

1. Garcia-Molina, Hector, and Kenneth Salem. "SAGAS." *Proceedings of the 1987
   ACM SIGMOD International Conference on Management of Data*, pages 249 to
   259. DOI 10.1145/38713.38742. The originating paper that defines a
   compensating transaction precisely as the mechanism a saga uses to undo a
   committed sub-transaction.
2. Microsoft Learn, Azure Architecture Center. *Compensating Transaction
   Pattern*. Verified 2026-08-02 at
   https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction.
   The primary catalog source for this entry's problem statement, solution
   description, problems and considerations, applicability, and reference
   Azure implementation.
3. Object Management Group. *Business Process Model and Notation, Version
   2.0*. Specification index, verified 2026-08-02 at
   http://www.omg.org/spec/BPMN/2.0/. Defines the Compensation Boundary Event
   and Compensation Handler as first-class modelling constructs.
4. Camunda. *Compensation events*, Camunda 8 documentation. Verified
   2026-08-02 at
   https://docs.camunda.io/docs/components/modeler/bpmn/compensation-events/.
   Vendor implementation notes on when a compensation handler is enabled and
   invoked, used to describe the runtime semantics accurately.
5. AWS. *Saga orchestration pattern*, AWS Prescriptive Guidance, Cloud Design
   Patterns. Verified 2026-08-02 at
   https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html.
   Source for the AWS Step Functions state-machine implementation described
   in dimensions 8 and 9, including the linked sample repository.
6. Temporal. *Saga Design Pattern Explained for Distributed Systems*.
   Verified 2026-08-02 at
   https://temporal.io/blog/saga-pattern-made-easy. Source for the
   Compensating Action naming and the general framing of compensation as an
   action with an opposite intent rather than a strict rollback.
7. Temporal PHP SDK documentation. *Saga in package Application*. Verified
   2026-08-02 at https://php.temporal.io/classes/Temporal-Workflow-Saga.html.
   Source for the `addCompensation`, `setParallelCompensation`, and
   `setContinueWithError` API behaviour described in dimensions 7 and 8.
8. Eclipse Foundation. *MicroProfile Long Running Actions 2.0*. Verified
   2026-08-02 at
   https://download.eclipse.org/microprofile/microprofile-lra-2.0/microprofile-lra-spec-2.0.html.
   Source for the `@Compensate` annotation and its enlistment and invocation
   semantics described in dimensions 8 and 9.

Unverifiable at the time of writing. Pat Helland's 2007 CIDR paper "Life
beyond Distributed Transactions, an Apostate's Opinion" was located and its
existence and venue confirmed through secondary indexes, but the primary PDF
could not be extracted into readable text by the tooling available during
authoring, so no direct quote or specific page claim from that paper appears
in this entry, and it is not cited above.

## Code examples

The examples below all implement the same scenario. an order-placement
workflow that reserves inventory and then charges a payment method. If the
charge fails, a compensating action releases the inventory reservation. Each
compensating action is guarded by an idempotency check against a set of
already-applied compensation keys, matching the requirement discussed in
dimensions 11 and 15.

### TypeScript

```typescript
// compensating-transaction.ts
type StepResult<T> = { ok: true; value: T } | { ok: false; error: string };

interface CompensationRecord {
  key: string;
  undo: () => Promise<void>;
}

class CompensationLog {
  private applied = new Set<string>();

  async runOnce(record: CompensationRecord): Promise<void> {
    if (this.applied.has(record.key)) {
      return;
    }
    await record.undo();
    this.applied.add(record.key);
  }
}

interface InventoryService {
  reserve(sku: string, qty: number): Promise<StepResult<string>>;
  release(reservationId: string): Promise<void>;
}

interface PaymentService {
  charge(amount: number): Promise<StepResult<string>>;
}

async function placeOrder(
  sku: string,
  qty: number,
  amount: number,
  inventory: InventoryService,
  payment: PaymentService,
): Promise<StepResult<string>> {
  const log = new CompensationLog();

  const reserved = await inventory.reserve(sku, qty);
  if (!reserved.ok) {
    return reserved;
  }
  const reservationId = reserved.value;

  const charged = await payment.charge(amount);
  if (!charged.ok) {
    await log.runOnce({
      key: `release-${reservationId}`,
      undo: () => inventory.release(reservationId),
    });
    return { ok: false, error: `payment failed, compensated reservation ${reservationId}` };
  }

  return { ok: true, value: charged.value };
}

async function main(): Promise<void> {
  let releasedCount = 0;
  const inventory: InventoryService = {
    reserve: async () => ({ ok: true, value: "res-1" }),
    release: async () => {
      releasedCount += 1;
    },
  };
  const payment: PaymentService = {
    charge: async () => ({ ok: false, error: "card declined" }),
  };

  const outcome = await placeOrder("sku-1", 2, 5000, inventory, payment);
  console.log(JSON.stringify(outcome));
  console.log(`compensations applied ${releasedCount}`);
}

main();
```

### Python

```python
# compensating_transaction.py
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class StepResult:
    ok: bool
    value: Optional[str] = None
    error: Optional[str] = None


class CompensationLog:
    def __init__(self) -> None:
        self._applied: set[str] = set()

    def run_once(self, key: str, undo: Callable[[], None]) -> None:
        if key in self._applied:
            return
        undo()
        self._applied.add(key)


class InventoryService:
    def __init__(self) -> None:
        self.released: list[str] = []

    def reserve(self, sku: str, qty: int) -> StepResult:
        return StepResult(ok=True, value="res-1")

    def release(self, reservation_id: str) -> None:
        self.released.append(reservation_id)


class PaymentService:
    def charge(self, amount: int) -> StepResult:
        return StepResult(ok=False, error="card declined")


def place_order(
    sku: str,
    qty: int,
    amount: int,
    inventory: InventoryService,
    payment: PaymentService,
) -> StepResult:
    log = CompensationLog()

    reserved = inventory.reserve(sku, qty)
    if not reserved.ok:
        return reserved
    reservation_id = reserved.value
    assert reservation_id is not None

    charged = payment.charge(amount)
    if not charged.ok:
        log.run_once(
            key=f"release-{reservation_id}",
            undo=lambda: inventory.release(reservation_id),
        )
        return StepResult(
            ok=False,
            error=f"payment failed, compensated reservation {reservation_id}",
        )

    return charged


if __name__ == "__main__":
    inv = InventoryService()
    pay = PaymentService()
    outcome = place_order("sku-1", 2, 5000, inv, pay)
    print(outcome)
    print(f"compensations applied {len(inv.released)}")
```

### Go

```go
// compensating_transaction.go
package main

import "fmt"

type StepResult struct {
	OK    bool
	Value string
	Err   string
}

type CompensationLog struct {
	applied map[string]bool
}

func NewCompensationLog() *CompensationLog {
	return &CompensationLog{applied: make(map[string]bool)}
}

func (c *CompensationLog) RunOnce(key string, undo func()) {
	if c.applied[key] {
		return
	}
	undo()
	c.applied[key] = true
}

type InventoryService struct {
	Released []string
}

func (i *InventoryService) Reserve(sku string, qty int) StepResult {
	return StepResult{OK: true, Value: "res-1"}
}

func (i *InventoryService) Release(reservationID string) {
	i.Released = append(i.Released, reservationID)
}

type PaymentService struct{}

func (p *PaymentService) Charge(amount int) StepResult {
	return StepResult{OK: false, Err: "card declined"}
}

func PlaceOrder(sku string, qty int, amount int, inv *InventoryService, pay *PaymentService) StepResult {
	log := NewCompensationLog()

	reserved := inv.Reserve(sku, qty)
	if !reserved.OK {
		return reserved
	}
	reservationID := reserved.Value

	charged := pay.Charge(amount)
	if !charged.OK {
		log.RunOnce("release-"+reservationID, func() {
			inv.Release(reservationID)
		})
		return StepResult{OK: false, Err: fmt.Sprintf("payment failed, compensated reservation %s", reservationID)}
	}

	return charged
}

func main() {
	inv := &InventoryService{}
	pay := &PaymentService{}

	outcome := PlaceOrder("sku-1", 2, 5000, inv, pay)
	fmt.Printf("%+v\n", outcome)
	fmt.Printf("compensations applied %d\n", len(inv.Released))
}
```
