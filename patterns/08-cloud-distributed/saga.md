---
name: Saga
slug: saga
family: 08-cloud-distributed
category: Data consistency
aliases: [Long Running Transaction, Compensating Transaction Pattern, Long Running Action, LRA]
first_described: "Garcia-Molina and Salem 1987"
maturity: canonical
related: [two-phase-commit, transactional-outbox, event-sourcing, cqrs, process-manager, idempotent-receiver, circuit-breaker]
incompatible_with: [distributed-two-phase-commit]
verified: 2026-08-02
---

# Saga

## 1. Name, aliases, and lineage

The canonical name is Saga. It was introduced by Hector Garcia-Molina and
Kenneth Salem of the Department of Computer Science at Princeton University in
a paper titled simply "SAGAS", published in the *Proceedings of the 1987 ACM
SIGMOD International Conference on Management of Data*, pages 249 to 259, DOI
10.1145/38713.38742. The paper's abstract states the idea in one sentence. A
long lived transaction is a saga if it can be written as a sequence of
transactions that can be interleaved with other transactions, and the database
management system guarantees that either all of the transactions in the saga
complete or compensating transactions run to amend a partial execution
(Garcia-Molina and Salem, "SAGAS", 1987, abstract, PDF verified 2026-08-02 at
https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf).

The original problem was not microservices. It was lock duration inside a
single database. A transaction that runs for hours holds locks for hours, and
the paper opens by naming the consequences. Waiting transactions suffer long
blocking delays, the deadlock rate rises steeply with transaction size, and a
long transaction has more wall clock in which to meet a crash and be aborted.
Sagas relaxed atomicity to release those locks early, in exchange for the
application supplying a semantic undo for each piece.

Aliases in current use.

- **Long Running Transaction**, close to the problem statement the paper itself
  uses, which abbreviates long lived transaction to LLT throughout.
- **Compensating Transaction Pattern**, the name that emphasises the mechanism
  rather than the unit. Microsoft's Azure Architecture Center publishes a
  separate Compensating Transaction pattern page alongside its Saga page, so in
  the Azure vocabulary the two are related but not identical entries.
- **Long Running Action**, abbreviated **LRA**, the name used by the Eclipse
  MicroProfile specification. MicroProfile LRA 2.0, released 14 February 2023,
  describes its model as one where all work performed within the scope of an
  activity is required to be compensatable, and the protocol arranges that when
  the activity terminates either all work is accepted or it is compensated
  (MicroProfile LRA 2.0 specification, verified 2026-08-02 at
  https://download.eclipse.org/microprofile/microprofile-lra-2.0/microprofile-lra-spec-2.0.html).
  That specification traces its lineage to the OASIS Web Services Composite
  Application Framework rather than directly to the 1987 paper, and the word
  saga appears only once in it, so LRA is a sibling lineage rather than a rename.

The name is not contested, but its scope is. In the database literature a saga
is a mechanism inside one DBMS with a saga execution component that owns the
log. In the microservices literature a saga is a coordination protocol across
independent services with independent databases. The mechanism is the same. The
trust boundary is not, and almost every practical difficulty in the modern form
comes from that difference.

## 2. Problem and context

A business operation spans several stores of record and must either happen in
full or leave nothing of consequence behind, and there is no transaction manager that
can span them.

The concrete shape in a codebase looks like this. An order handler calls the
inventory service to hold stock, the payment service to capture a card, and the
shipping service to create a label. Each call succeeds or fails on its own. The
handler wraps nothing, because there is nothing to wrap. When the payment
capture fails after the stock hold succeeded, the stock sits held for an order
that will never exist, and the fix is a manual database edit at two in the
morning by whoever is on call.

The context in which a saga is the right answer has four parts.

- **The operation crosses a consistency boundary.** Separate databases,
  separate services, or an internal database plus a third party API. If all of
  the work fits inside one database, a local transaction is correct and a saga
  is a mistake.
- **Every step has a genuine business reversal.** Not a state restore, a
  reversal. Cancelling a reservation, issuing a refund, voiding a label. The
  paper is explicit that compensation undoes the actions of a step from a
  semantic point of view but does not necessarily return the database to the
  state that existed when the step began (Garcia-Molina and Salem, 1987,
  section 1).
- **The business can tolerate a visible intermediate state.** During the saga,
  other readers will see the stock held and the payment pending. If any observer
  must never see that, a saga is the wrong shape.
- **There is no viable atomic commit protocol.** Either the participants do not
  speak one, or the availability cost of blocking is unacceptable. Pat Helland
  made the strong version of this argument in "Life beyond Distributed
  Transactions, an Apostate's Opinion", CIDR 2007, arguing that very large
  applications are built with techniques that do not provide transactional
  guarantees, and that what remains is workflow style updates through
  asynchronous messaging (Helland, CIDR 2007, page 137, PDF verified 2026-08-02
  at https://www.cidrdb.org/cidr2007/papers/cidr07p15.pdf).

## 3. Forces

The weighing below is engineering judgement. The mechanics are sourced, the
ranking of which pressure matters most is reasoning from practice.

- **Availability.** Strongly favoured. No participant waits on a coordinator's
  decision to release its locks, so one slow or dead participant does not freeze
  the others. This is the single largest reason the pattern displaced two phase
  commit in service architectures.
- **Isolation.** Sacrificed outright. This is not a tunable, it is the trade. A
  saga is ACD, not ACID. AWS states the same point plainly in its prescriptive
  guidance, that saga lacks transaction isolation and concurrent orchestration
  can lead to stale data (AWS Prescriptive Guidance, saga orchestration pattern,
  verified 2026-08-02 at
  https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html).
- **Latency of the happy path.** Favoured against two phase commit, because
  there is no prepare round trip and no coordinator disk sync before each
  participant may proceed. Sacrificed against a single local transaction, since
  every step is a network hop.
- **Latency of the unhappy path.** Sacrificed. A failure at step five means four
  compensations, each a network call with its own retry budget. AWS names this
  directly and advises avoiding synchronous calls when the saga has many steps.
- **Coupling.** Depends entirely on the coordination style. Choreography lowers
  direct coupling and raises semantic coupling, since every participant must
  know which events matter. Orchestration concentrates the knowledge in one place
  and creates a component every participant depends on.
- **Cognitive load.** Sacrificed sharply. The reader of any single service can no
  longer see the business operation. It exists only in the union of the services,
  or in an orchestrator definition. Microsoft's guidance lists a shift in design
  thinking as the first consideration for adopting the pattern.
- **Operability.** Sacrificed at first, then recoverable. A saga is invisible
  until it is instrumented with a correlation identifier and a state store. Once
  instrumented it is more observable than a distributed transaction, because
  every step boundary is an explicit event rather than a lock inside a database
  engine.
- **Cost.** Mildly sacrificed. Compensations, retries, and a saga state store are
  all real infrastructure that a local transaction does not need.
- **Team topology.** Favoured for choreography, since each team owns its reaction
  and deploys independently. Favoured differently for orchestration, since one
  team owns the process definition and can change the order of steps without
  touching the participants.

The pattern sacrifices isolation and the reader's ability to see the whole
operation in one place, and buys availability and independent deployability.
Anyone describing a saga as free is describing something else.

## 4. Applicability and non-applicability

Reach for a saga when all of the following hold.

- The operation must update state in two or more services or stores that do not
  share a transaction manager.
- Each step has a genuine business reversal that the domain already understands.
  A refund, a cancellation, a credit note, a release.
- Intermediate states are acceptable to the business, or can be hidden behind a
  status field that callers respect.
- Failure of one step is expected often enough that manual repair does not scale.
  A once a year failure that a support agent fixes by hand is cheaper to leave
  alone.
- You are willing to own the compensation code as first class business logic,
  with its own tests, and not as an afterthought in an error branch.

**Non-applicability.** Do not reach for a saga when any of the following hold.

- **All of the work fits in one database.** A local transaction gives real
  atomicity and real isolation for free. Splitting it into a saga to look
  microservice shaped adds failure modes and removes guarantees. This is the most
  common misapplication.
- **A step cannot be compensated at all.** Some effects escape. An email that
  reached a human inbox, an SMS, a push notification, a wire transfer that
  settled, a physical package handed to a courier, a report filed with a
  regulator, an irreversible third party API call with no void endpoint. A
  followup email apologising is a new business action, not a compensation, and
  calling it one hides a real inconsistency. Order the saga so that every such
  step sits at or after the pivot, where nothing needs to unwind.
- **The business requires that no observer ever sees the intermediate state.** If
  a regulator or an auditor treats a held reservation as a commitment, the
  intermediate state is not private and cannot be quietly undone.
- **The participants already support a shared atomic commit protocol and can
  afford to block.** Two databases inside one datacentre under one operations
  team, with XA available and a low transaction rate, may be better served by two
  phase commit. The saga's advantage is availability under partition, which is
  worth little when partition is not a real risk and the coordinator is reliable.
- **Strong read-your-writes across services is a stated requirement.** A saga
  gives eventual consistency across participants by construction. AWS calls this
  out as an explicit consideration and suggests either resetting the business
  expectation or changing the data store.
- **The operation is two steps and the second is idempotent and retriable.** A
  durable outbox plus at-least-once delivery plus an idempotent consumer is
  simpler, has fewer moving parts, and is a strictly smaller commitment. Reach
  for the Transactional Outbox pattern instead.
- **You do not control the ordering of the steps.** A saga's correctness depends
  on placing compensatable work before the pivot. If a third party forces the
  irreversible call first, the pattern degrades to hope.

## 5. Structure

The participants below use role names, not class names.

- **Saga definition.** The ordered list of steps, each paired with its
  compensation where one exists, plus the classification of each step. This is
  data in an orchestrated saga and is implicit in the event topology in a
  choreographed one.
- **Saga instance.** One execution of the definition, identified by a correlation
  identifier that every message carries. Its state is the index of the last
  completed step plus whichever business identifiers the compensations will need.
- **Local transaction**, also called a saga step or a participant transaction.
  One unit of work that commits atomically inside a single participant. In the
  1987 paper these are T1 through Tn.
- **Compensating transaction.** The semantic reversal of one local transaction,
  C1 through Cn in the paper. It is itself a local transaction that commits, and
  it may fail, which is a distinct failure class from the forward step failing.
- **Coordinator.** The component that decides what runs next. In orchestration it
  is an explicit service. In choreography it does not exist as a component and the
  decision is distributed into the participants' event handlers. The 1987 paper
  calls its version the **saga execution component**, or SEC, and records that
  every saga command is written to the log before any action is taken
  (Garcia-Molina and Salem, 1987, section 3).
- **Saga log.** The durable record of which steps started, completed, and
  compensated. Without it, a coordinator crash mid saga leaves an instance that
  nobody will ever finish or unwind.
- **Pivot transaction.** The step that is neither compensatable nor safely
  retriable, and therefore the point of no return. Microsoft's Azure Architecture
  Center defines it as the point after which compensable transactions are no
  longer relevant and all subsequent actions must complete (Microsoft Learn, Saga
  design pattern, verified 2026-08-02 at
  https://learn.microsoft.com/en-us/azure/architecture/patterns/saga).

The classification of steps into compensatable, pivot, and retriable is the
constraint that makes a saga analysable. Every step before the pivot must have a
compensation. Every step after it must be retriable until it succeeds, because
there is no longer a path backwards.

## 6. ASCII structure diagram

```
              ORCHESTRATION                        CHOREOGRAPHY

  +---------------------------+          +------------------------+
  |    Saga Orchestrator      |          |     Message broker     |
  |  (holds the definition)   |          |   (topics, no logic)   |
  +---------------------------+          +------------------------+
     |        |         |                    ^   |    ^   |   ^  |
 cmd |    cmd |     cmd |                evt |   v    |   v   |  v
     v        v         v                 +-----+  +-----+  +-----+
  +------+ +------+ +--------+            |Order|  |Stock|  | Pay |
  |Order | |Stock | |Payment |            +-----+  +-----+  +-----+
  |  svc | |  svc | |   svc  |               |        |        |
  +------+ +------+ +--------+               v        v        v
     |        |         |                  [db]     [db]     [db]
     v        v         v
   [db]     [db]      [db]              each service knows which
                                        event it reacts to, and
  +---------------------------+         which event it emits next
  |        Saga log           |
  | id | step | phase | data  |
  +---------------------------+

  STEP CLASSIFICATION along the definition

  T1 ......... T2 ......... T3 ......... T4 ......... T5
  compensatable  compensatable   PIVOT     retriable   retriable
  |              |               |
  C1 <---------- C2 <------------+        no path back past here
  (unwind runs in reverse order)
```

## 7. Dynamics

Two runtime flows matter. The forward path and the unwind. The paper guarantees
one of exactly two sequences will be executed, either T1 through Tn, or T1
through Tj followed by Cj down to C1 for some j less than n (Garcia-Molina and
Salem, 1987, section 1).

```
HAPPY PATH (orchestrated)

Client   Orchestrator     Stock        Payment       Shipping
  |          |              |             |              |
  |--start-->|              |             |              |
  |          |--log START-->[saga log]    |              |
  |          |--reserve---->|             |              |
  |          |<---reserved--|             |              |
  |          |--log T1 OK-->[saga log]    |              |
  |          |--------charge------------->|              |
  |          |<-------authorized----------|   PIVOT      |
  |          |--log T2 OK-->[saga log]    |              |
  |          |--------------ship------------------------>|
  |          |<-------------shipped----------------------|
  |<--done---|                                           |

UNWIND PATH (payment declines at T2)

Client   Orchestrator     Stock        Payment
  |          |              |             |
  |--start-->|              |             |
  |          |--reserve---->|             |
  |          |<---reserved--|             |
  |          |--------charge------------->|
  |          |<-------DECLINED------------|
  |          |--log T2 FAIL->[saga log]
  |          |--release---->|         C1 runs, C2 does not
  |          |<---released--|         because T2 never committed
  |          |--log C1 OK-->[saga log]
  |<--failed-|

COMPENSATION FAILS (the case most designs forget)

Orchestrator     Stock
  |                |
  |--release------>|  X  service down
  |<--timeout------|
  |--retry (bounded backoff)---> still failing
  |--log C1 STUCK-->[saga log]
  |--emit SagaStuck event ---> alert, human queue
  |
  the saga instance stays open. It is NOT closed as failed,
  because the stock is still held and somebody must release it.
```

The state machine of one saga instance has five waiting-or-terminal states.
Running, Compensating, Completed, Compensated, and Stuck. Designs that omit
Stuck silently discard the case where a compensation cannot succeed, which is
the case that produces the two in the morning page.

## 8. Implementation variants

### Choreography

Each participant subscribes to events and publishes the next event. There is no
coordinator. Microsoft's guidance lists the benefits as suiting simple workflows
with few services, needing no additional service, and avoiding a single point of
failure because responsibility is distributed. It lists the drawbacks as
confusion when steps are added, a risk of cyclic dependency between participants
because they consume each other's commands, and difficult integration testing
because every service must run to simulate one transaction (Microsoft Learn,
Saga design pattern, verified 2026-08-02).

### Orchestration

A coordinator holds the definition and sends commands. Microsoft lists the
benefits as suiting complex workflows and the addition of new services, avoiding
cyclic dependencies, and a clear separation of responsibilities. It lists the
drawbacks as the design complexity of the coordination logic and the coordinator
being a point of failure.

**The choosing boundary.** The honest rule, and this is judgement drawn from the
two sourced lists above, is a threshold rather than a preference.

Choose choreography when the saga has roughly four steps or fewer, the order is
unlikely to change, no step needs a decision that depends on the results of two
earlier steps, and no single team is accountable for the end to end outcome. The
moment any of those four stops being true, choreography starts paying for itself
in incident time. The tell is the first time somebody asks where the order
process is defined and the answer requires opening five repositories.

Choose orchestration when the saga has branching, when the order of steps is a
business decision that changes, when timeouts or human approval steps appear, or
when an auditor will ask for the state of a specific instance. AWS makes the
availability objection to orchestration concrete rather than theoretical, noting
that using Step Functions mitigates the single point of failure that the
orchestration pattern carries, because the service maintains capacity across
multiple Availability Zones (AWS Prescriptive Guidance, verified 2026-08-02).
Once the coordinator is a managed durable workflow engine rather than a service
you wrote, the main argument for choreography has largely gone.

A mixed form is common and legitimate. Orchestrate the part that has business
branching, and let a downstream fan out of purely retriable notifications run by
choreography, since none of it needs to unwind.

### Durable workflow engines

The coordinator is expressed as ordinary code whose execution is checkpointed, so
a process crash resumes rather than restarts. Temporal describes the pattern in
its own documentation as breaking a transaction into smaller sub transactions,
where a failure is compensated by executing actions that undo the previous steps
(Temporal Platform Documentation, use cases and design patterns, verified
2026-08-02 at https://docs.temporal.io/evaluate/use-cases-design-patterns). The
trade is a hard runtime dependency and a determinism constraint on the workflow
code, in exchange for the saga log being the engine's problem rather than yours.

### BPMN compensation

The saga is a diagram. Camunda 8 implements compensation as a first class BPMN
construct, where a compensation boundary event is attached to an activity and
associated with a handler that reverts its effects. Its documentation records an
important default. The process instance invokes all compensation handlers at once
without any specific order, and enforcing a sequence requires triggering
compensation for a specific activity through the activityRef property (Camunda 8
Docs, compensation events, verified 2026-08-02 at
https://docs.camunda.io/docs/components/modeler/bpmn/compensation-events/). That
default differs from the reverse order unwind of the 1987 paper, and mistaking
one for the other produces compensations that run in an order the domain does not
expect.

### Framework DSL over messaging

A library expresses the definition in code and drives it over a message
transport. Eventuate Tram Sagas provides a saga framework for Java microservices
using JDBC or JPA with Spring Boot or Micronaut, with a fluent definition where
each step pairs an invocation with a withCompensation clause and compensations
run in reverse order (Eventuate Tram Sagas repository README, verified 2026-08-02
at https://github.com/eventuate-tram/eventuate-tram-sagas).

### Protocol specification

The coordination is a wire protocol rather than a library. MicroProfile LRA 2.0
defines @LRA to control the life cycle, @Compensate to mark the method invoked
when the LRA is cancelled, @Complete for when it is closed, and @AfterLRA for
notification of the final state, alongside @Status, @Forget, and @Leave
(MicroProfile LRA 2.0 specification, verified 2026-08-02). The value is that
participants from different vendors interoperate. The cost is that the protocol
constrains the shape of the participants.

### Language shape differences

In Go and Rust the natural expression is a slice of step records with an explicit
stack of completed steps to unwind, because closures capture the state directly
and there is no ambient exception to unwind for you. In TypeScript and Python the
natural expression is async functions with try and catch, which makes it tempting
to put compensation in a catch block. That temptation is worth resisting, because
a catch block cannot easily unwind steps that completed in a previous process.
The step record form survives a restart. A catch block does not.

## 9. Known production uses

- **AWS Step Functions.** AWS publishes the saga orchestration pattern as
  prescriptive guidance with a Step Functions state machine as the coordinator,
  including the compensating Revert Payment, Revert Inventory, and Remove Order
  tasks, and ships reference source at
  https://github.com/aws-samples/saga-orchestration-netcore-blog (AWS
  Prescriptive Guidance, saga orchestration pattern, verified 2026-08-02 at
  https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html).
- **Microsoft Azure Architecture Center.** Saga is a named pattern in the Azure
  catalog, with the compensable, pivot, and retryable classification and the six
  isolation countermeasures documented as guidance, page dated 2025-02-25,
  https://learn.microsoft.com/en-us/azure/architecture/patterns/saga
  verified 2026-08-02.
- **Temporal.** The platform documents native support for the saga pattern,
  including a trip booking tutorial in which every operation can be rolled back
  by a compensating transaction and compensations run sequentially by default,
  https://docs.temporal.io/evaluate/use-cases-design-patterns
  verified 2026-08-02.
- **Camunda 8 and the Zeebe engine.** BPMN compensation events are a shipped
  modeller construct with documented semantics for handler invocation,
  https://docs.camunda.io/docs/components/modeler/bpmn/compensation-events/
  verified 2026-08-02.
- **Eventuate Tram Sagas.** An open source saga orchestration framework for Java
  microservices on JDBC or JPA with Spring Boot or Micronaut,
  https://github.com/eventuate-tram/eventuate-tram-sagas
  verified 2026-08-02.
- **Eclipse MicroProfile LRA.** A ratified specification, version 2.0 final,
  dated 14 February 2023, defining the compensation protocol and its annotations
  for Jakarta EE style services,
  https://download.eclipse.org/microprofile/microprofile-lra-2.0/microprofile-lra-spec-2.0.html
  verified 2026-08-02.

## 10. Consequences

The mechanics below are sourced. The weighting of how badly each cost bites is
judgement.

**Positive.**

- No participant holds a lock across a network round trip, so a slow or dead
  participant degrades throughput rather than freezing every other transaction.
- Participants stay independently deployable and can be scaled independently,
  because none of them needs to agree with the others on a commit protocol
  version.
- Failure handling becomes explicit domain logic that a business person can read.
  What happens when the card declines is a named step rather than an implicit
  database rollback.
- The saga log doubles as an audit trail. Which step ran, when, with what result,
  is recorded because the pattern needs it, not because compliance asked.
- Steps can be long. A saga tolerates a step that waits on a human approval for
  three days, which no lock based protocol can.

**Negative.**

- Isolation is gone. Every anomaly that isolation prevented is now the
  application's problem, and the countermeasures in dimension 11 are partial.
- Compensation code roughly doubles the surface of the operation, and it is the
  half that gets exercised least in testing and most during incidents.
- Some steps cannot be compensated, so the design constrains the ordering of
  business operations, which is a real limit on how the business may change.
- A failed compensation has no automatic recovery. Microsoft names this directly,
  that compensating transactions might not always succeed, which can leave the
  system in an inconsistent state.
- Debugging requires distributed tracing from day one. Microsoft lists debugging
  complexity as a consideration that grows with participant count.
- The end to end operation exists in no single file, which raises the cost of
  onboarding and the cost of any change that reorders steps.

## 11. Failure modes and misuse

Symptom, cause, and fix. The symptoms are drawn from practice, so treat the
diagnosis as experienced judgement rather than a sourced result. The anomaly
names and the countermeasure names are sourced to Microsoft's guidance.

**Lost update.** *Symptom.* A customer's stored address reverts to a previous
value minutes after they changed it, and the audit log shows both writes
succeeded. *Cause.* Two sagas read the same record, and the second wrote a value
computed from data read before the first saga's step committed. Microsoft defines
a lost update as one saga modifying data without accounting for changes made by
another. *Fix.* Apply the **commutative updates** countermeasure, so that
operations are expressed as deltas that compose in any order, for example
incrementing a balance rather than setting it. Where the operation genuinely is
not commutative, apply the **version file** countermeasure, which maintains a log
of all operations performed on a record and arranges that they are performed in
the correct sequence, turning a non-commutative operation into one that can be
applied out of order.

**Dirty read.** *Symptom.* A customer receives an order confirmation email for an
order that is cancelled thirty seconds later, because a reporting job read the
order in its intermediate state. *Cause.* A reader saw data written by a
compensatable step that was subsequently compensated. *Fix.* Apply the **semantic
lock** countermeasure. The compensatable step writes an explicit status flag,
PENDING or IN_REVIEW, that marks the record as not yet committed, and every reader
is required to respect that flag. Microsoft describes it as an application level
lock where the compensable transaction uses a semaphore to indicate that an
update is in progress. Alternatively apply the **pessimistic view**
countermeasure, which reorders the saga so that the risky update happens in a
retriable step after the pivot, eliminating the window entirely.

**Non-repeatable read inside one saga.** *Symptom.* A saga validates that a
credit limit is sufficient at step one and then exceeds it at step four, because
another saga consumed the credit in between. *Cause.* Two reads of the same data
at different points in a saga returned different values, which Microsoft calls a
fuzzy or nonrepeatable read. *Fix.* Apply the **reread value** countermeasure,
confirming the data is unchanged immediately before the update and aborting the
step if it moved. This is optimistic concurrency control applied at the step
boundary rather than the transaction boundary.

**Concurrency policy applied uniformly regardless of stake.** *Symptom.* A saga
that moves fifty cents and a saga that moves fifty thousand carry identical
safeguards, and the business is unhappy with both. *Cause.* One mechanism was
chosen for the whole system. *Fix.* Apply the **by value** countermeasure,
described by Microsoft as risk-based concurrency, dynamically choosing the
concurrency mechanism from the business risk at stake, for example a saga for
low-risk updates and a distributed transaction for high-risk ones.

**Compensation that is not a reversal.** *Symptom.* Refund totals do not
reconcile with charge totals at month end, and the difference is exactly the
processing fees. *Cause.* The compensation was written as if it restored prior
state, when the reversal has its own cost, its own tax treatment, and its own
timing. *Fix.* Treat the compensation as a first class business operation with
its own name, its own ledger entry, and its own tests. Never model it as an undo.
The 1987 paper is explicit that compensation does not necessarily return the
database to the prior state, and every accounting system in the world agrees.

**Uncompensatable step placed too early.** *Symptom.* Customers receive a
shipment notification for an order that was then cancelled, and support handles
the fallout by hand. *Cause.* An irreversible effect, an email, an SMS, a settled
transfer, was placed before the pivot, so the unwind path reaches a step it cannot
undo. *Fix.* Reclassify. Move every irreversible effect to the retriable region
after the pivot. Where the business insists on notifying early, change the
notification to a tentative one whose language survives cancellation.

**Compensation fails and the saga is marked failed.** *Symptom.* Inventory counts
drift downward over weeks with no single explanation, and reconciliation finds
reservations that were never released. *Cause.* The compensation call failed, the
code caught the exception, logged it, and closed the saga as failed. The failure
was recorded as the saga's outcome rather than as an open incident. *Fix.*
Introduce an explicit STUCK state distinct from COMPENSATED. A saga whose
compensation failed is not finished. Retry with bounded backoff, then route to a
human queue with the exact compensating action pre-populated. Microsoft lists this
failure directly under limitations of compensating transactions.

**Non-idempotent participant under at-least-once delivery.** *Symptom.* A customer
is charged twice for one order, and both charges have different transaction
identifiers. *Cause.* The coordinator retried after a timeout on a call that had
actually succeeded, and the participant treated the retry as a new request. *Fix.*
Every step and every compensation takes an idempotency key derived from the saga
instance identifier and the step name, and the participant stores it. AWS states
the requirement plainly, that saga participants need to be idempotent to allow
repeated execution in the case of transient failures caused by unexpected crashes
and orchestrator failures.

**Compensation arrives before the forward step completes.** *Symptom.* A refund is
rejected with charge not found, and moments later the charge appears. *Cause.* The
coordinator timed out and began compensating while the forward call was still in
flight at the participant. *Fix.* Compensations must tolerate a forward step that
has not landed yet. Either the compensation records a tombstone that the late
forward step checks, or the participant treats a compensation for an unknown
identifier as a durable instruction rather than an error. This is the semantically
compensatable window, and it is the failure most often discovered in production
rather than in test.

**Choreography cycle.** *Symptom.* A deployment of one service causes an event
storm, and the broker's queue depth climbs without bound. *Cause.* Two
participants each react to an event the other emits, forming a cycle. Microsoft
names the risk of cyclic dependency between saga participants as a drawback of
choreography. *Fix.* Draw the event graph mechanically, from the subscriptions in
code rather than from a diagram somebody maintained by hand. A cycle in that graph
is a build failure, not a design discussion.

**The saga that should have been a transaction.** *Symptom.* Two services always
deploy together, always fail together, and share a large fraction of their schema.
*Cause.* A service boundary was drawn in the wrong place, and a saga was
introduced to paper over it. *Fix.* Merge the services and use a local
transaction. A saga is not a substitute for a correct boundary, and this is the
most expensive misuse because it adds all of the cost of the pattern and none of
the benefit.

## 12. Trade-off matrix

Compared against named alternatives across the forces in dimension 3. TCC is Try
Confirm Cancel, the reservation based protocol. Outbox refers to the
Transactional Outbox pattern with an idempotent consumer.

| Force | Saga | Two-Phase Commit (XA) | TCC | Transactional Outbox | Single local transaction |
|---|---|---|---|---|---|
| Atomicity | Semantic, via compensation | Real, all or nothing | Real within reservations | Per message, not per operation | Real |
| Isolation | None across steps | Serialisable if participants are | Partial, reservations hold intent | None | Full |
| Availability under partition | High, no participant blocks | Low, participants block on the coordinator | Medium, reservations expire | High | Not applicable |
| Coordinator failure impact | Instance stalls, resumable from the log | Participants hold locks indefinitely | Reservations time out | None | None |
| Happy path latency | Sum of steps, no prepare round | Two rounds plus a coordinator disk sync | Two rounds, try then confirm | One local commit plus async relay | One commit |
| Unhappy path latency | Compensation chain, can be long | Single abort broadcast | Cancel broadcast | Retry of one message | Instant rollback |
| Participant requirements | A business reversal per step | XA support in every resource | Try, confirm, and cancel per service | Outbox table plus idempotent consumer | One database |
| Works across vendors and third parties | Yes, plain API calls suffice | Rarely, XA is not offered by most SaaS | Yes if the API exposes reservations | Yes | No |
| Cognitive load | High, the operation is distributed | Low, the code reads as one transaction | High, three methods per participant | Low | Lowest |
| Operational burden | Saga log, tracing, stuck queue | Coordinator, in-doubt resolution | Reservation expiry, sweeper | Relay lag monitoring | None |
| Best fit | Cross service business processes | Two databases, one operations team, low rate | Third party APIs with hold semantics | One write plus one downstream effect | One consistency boundary |

**Saga versus two-phase commit, expanded.** These are not competitors on a single
axis, they trade different guarantees. Two phase commit gives real atomicity and,
given serialisable participants, real isolation, at the price of blocking. The
blocking is not a quality of implementation problem. Dale Skeen's "Nonblocking
commit protocols", *Proceedings of the 1981 ACM SIGMOD International Conference on
Management of Data*, pages 133 to 142, DOI 10.1145/582318.582339, established the
distinction between protocols that block and those that allow operational sites to
continue transaction processing when site failures have occurred, and 2PC sits in
the first category. A participant that has voted to commit and then loses the
coordinator holds its locks until the coordinator returns.

The saga does not solve that problem, it declines to have it, by never asking a
participant to hold anything on behalf of another. AWS states the practical
consequence for microservices, that in systems following a database per service
design there is no single controller able to coordinate a process similar to two
phase commit, and one solution is saga orchestration (AWS Prescriptive Guidance,
verified 2026-08-02). The decision procedure is short. If every participant speaks
XA, is inside one failure domain, and the transaction rate is low enough that
occasional blocking is tolerable, 2PC is simpler and gives more. In every other
case the saga is the available option, and its costs are the price of that
availability.

## 13. Related and incompatible patterns

- **Transactional Outbox.** Composes closely and is nearly a prerequisite for a
  choreographed saga. Each step must commit its local change and publish its event
  atomically, which is exactly what the outbox provides. A choreographed saga
  without an outbox has a window where the database commits and the event is lost,
  and that window silently strands saga instances. AWS lists the transactional
  outbox pattern as related content on its saga page.
- **Idempotent Receiver.** Required, not optional. At-least-once delivery is the
  only realistic delivery guarantee, so every participant must deduplicate.
- **Process Manager.** An orchestrated saga is a process manager whose steps
  happen to be compensatable. The terms are used almost interchangeably in
  practice, and the useful distinction is that a process manager may coordinate
  work that never needs to unwind.
- **Event Sourcing and CQRS.** Compose well. An event sourced participant makes
  the saga log partly redundant, since the step outcomes are already durable
  events. The read side is where dirty reads become visible, so the semantic lock
  countermeasure usually has to be enforced in the projection.
- **Circuit Breaker and Retry.** Compose beneath a saga, at the transport level. A
  retriable step after the pivot needs a retry budget that never gives up
  permanently, which is a different policy from the fail fast policy a circuit
  breaker normally applies. Applying a standard breaker to a post-pivot step
  produces a saga that abandons work it promised to finish.
- **Two-Phase Commit.** Replaces the saga where it is available and affordable.
  Mixing them inside one operation is possible, using 2PC inside a step whose
  participants share a coordinator, and is legitimate. Using both to coordinate the
  same set of participants is not, since the saga's compensations would race the
  coordinator's abort.
- **Try Confirm Cancel.** A close relative that inverts the ordering. TCC reserves
  capacity in every participant before confirming any, so the visible intermediate
  state is a reservation rather than a completed change. It reduces the dirty read
  window at the cost of requiring every participant to expose three operations.
  Choose TCC when the participants naturally support holds, such as payment
  authorisation before capture, and a saga when they do not.
- **Incompatible with distributed two-phase commit over the same participants.**
  The two protocols make contradictory assumptions about who owns the abort
  decision, so a step's compensation and the coordinator's rollback can both fire
  for one failure.

## 14. Refactoring path in and out

**Introducing a saga into code that does not have one.** The sequence below is
ordered so that each step is independently shippable and reversible.

1. **Name the operation.** Find the handler that currently calls several services
   in sequence, and give the whole thing a name the business uses. Place order,
   not createOrderAndChargeAndShip.
2. **Make every call idempotent first.** Add an idempotency key parameter to each
   participant and store it. Do this before anything else, because every later
   step depends on safe retries. Ship it. Nothing about the saga exists yet.
3. **Add the correlation identifier.** Generate one identifier per operation and
   thread it through every call and every log line. Ship it. Now incidents are
   already easier to investigate.
4. **Write the compensations as public operations.** Cancel reservation, refund
   payment, void label. Give each one an endpoint, a test, and a runbook entry. Do
   not call them from the saga yet. A human on call can already use them.
5. **Classify the steps.** Mark each as compensatable, pivot, or retriable, and
   reorder so every irreversible step sits at or after the pivot. This reordering
   is the real design work and it usually surfaces a business conversation
   about when a customer is told something.
6. **Introduce the saga log.** A table with the instance identifier, the step, the
   phase, and the payload needed by the compensation. Write to it from the existing
   handler before touching control flow.
7. **Replace the inline sequence with a step list.** Turn the handler into a
   definition plus a runner. At this point the code shape changes but the behaviour
   does not.
8. **Turn on the unwind.** Wire the runner to call the compensations in reverse on
   failure. Ship behind a flag, and compare the manual repair volume before and
   after.
9. **Add the stuck path.** Bounded retries on compensation, then an alert and a
   human queue. Do not skip this. It is the step that decides whether the pattern
   reduces or relocates the operational burden.
10. **Move the runner out of the request path.** Only now, if latency or
    reliability demands it, hand the definition to a durable engine or split it
    into choreographed events.

**Removing a saga when it stops earning its place.** Two exits.

- **Collapse into a local transaction.** When the participants have merged, or the
  boundary was wrong to begin with, delete the saga in this order. Stop starting
  new instances, drain the open ones, verify the log is empty, replace the runner
  with a single transaction, then delete the compensations last. Deleting the
  compensations before draining strands the open instances.
- **Degrade into an outbox plus an idempotent consumer.** When the saga has been
  reduced to two steps and the second can no longer fail in a way that requires
  unwinding, the coordinator is overhead. Replace it with one local transaction
  plus one reliably delivered message. Keep the correlation identifier and the
  idempotency keys. They cost nothing and remain useful.

The named refactorings that apply are Extract Method for pulling each step out of
the handler, Replace Conditional with Polymorphism where the step list replaces a
chain of nested error branches, and Introduce Parameter Object for the saga state
that threads through the steps.

## 15. Testing and verification

This dimension is practice rather than a sourced result.

What becomes easier. Each step is a small, independently testable unit with a
clear contract, and each compensation is a public operation that can be tested
directly. The definition, being data, can be asserted against without running
anything. A property test over the definition catches the two structural errors
cheaply, that every pre-pivot step has a compensation and every post-pivot step is
marked retriable. The TypeScript sample below performs exactly that check at
construction time.

What becomes harder. There is no single place to assert that the operation
happened. Correctness is a property of a distributed execution, so the test has to
observe several stores.

Techniques that apply.

- **Compensation round trip test.** For each step, run the forward action then the
  compensation, and assert the business invariant is restored. Not the state, the
  invariant. Available stock returns to its prior number, the ledger nets to zero,
  the reservation count is unchanged. Testing for state equality will fail
  correctly and confusingly, because compensation is semantic.
- **Fault injection at every step boundary.** Parameterise a test over the index of
  the failing step and assert the resulting system state for each index. A saga
  with five steps has six distinct outcomes and each deserves a case.
- **Duplicate delivery test.** Deliver every message twice, in both orders, and
  assert the outcome is unchanged. This catches missing idempotency keys, which is
  the defect class most likely to reach production.
- **Out of order compensation test.** Deliver a compensation before its forward
  step's response has landed. This is the window described in dimension 11 and it
  needs an explicit test because it is invisible in a synchronous test runner.
- **Contract tests per participant.** Consumer driven contract tests keep the
  coordinator's expectations and the participant's behaviour aligned without
  running everything together.
- **A full integration test, sparingly.** Microsoft names integration testing
  difficulty as a specific drawback of choreography, because every service must run
  to simulate one transaction. Treat the full integration test as a smoke test of
  the wiring, and put the behavioural coverage at the unit and contract levels where
  it is fast.

Test doubles that apply. An in-memory message bus for choreography, as in the
Python sample. A fake participant that can be told to fail on the Nth call for
retry testing. A clock double, since timeouts drive the transition into
compensation and testing them against real time is slow and flaky.

## 16. Observability signals

This dimension is practice.

**Log.** Every step transition as a structured event carrying the saga definition
name, the instance identifier, the step name, the phase started, completed, or
compensated, the attempt number, and the idempotency key. The 1987 paper's saga
execution component wrote each command to the log before taking any action, and
the same discipline applies. Log intent before effect, or a crash between the two
is invisible.

**Trace.** One trace per saga instance, with the instance identifier as the trace
correlation. Each step is a span, each compensation is a span with an explicit
compensation attribute so that unwind time can be separated from forward time in
aggregate. Without this, a saga's latency profile is uninterpretable because
forward and backward work are mixed together.

**Metrics that matter.**

- Saga completion rate, split by definition. A drop is the primary alert.
- Compensation rate, split by which step triggered it. A rise localises the
  failing participant faster than any individual service's error rate.
- Compensation failure rate. This should be near zero, and any non-zero value
  needs a page rather than a dashboard, because each one is state that will not
  fix itself.
- Count and age of instances in the STUCK state. This is the health metric that
  distinguishes a working saga implementation from one that is quietly leaking.
- Saga duration percentiles, forward path and unwind path separately.
- Open instance count and its age distribution. A growing tail means instances are
  starting and not finishing, which a completion rate alone can hide.

**A healthy instance on a dashboard.** Completion rate flat and high, compensation
rate low and steady rather than spiky, compensation failures at zero, stuck count
at zero, and the open instance age distribution with a short tail that matches the
slowest expected step.

**A failing instance.** Compensation rate climbing while completion falls, which
points at one participant. Or completion and compensation both falling while open
count rises, which points at the coordinator or the transport rather than a
participant. Or compensation failures appearing at all, which is the signal that
manual repair work is accumulating right now. AWS names observability as a specific
consideration, that detailed logging and tracing become important as the number of
participants grows.

## 17. Security and privacy implications

This dimension is analytical.

**Attack surface the pattern opens.**

- **Compensation as an unauthorised write primitive.** Every compensation is an
  endpoint that reverses a committed business effect. Refund payment, cancel
  reservation, void document. If the coordinator authenticates to participants with
  a broad credential, anyone who reaches that credential can reverse arbitrary
  business state. Compensations need the same authorisation rigour as the forward
  operations, scoped to the specific saga instance rather than granted wholesale.
- **Saga instance identifier as a capability.** If a participant accepts a
  compensation for any instance identifier presented, the identifier becomes a
  bearer token. Use unguessable identifiers and verify that the requesting
  coordinator is the one that started the instance.
- **Replay.** Idempotency keys make retries safe against duplication but do not by
  themselves make them safe against a malicious replay from a different actor. The
  key deduplicates, it does not authenticate.
- **The saga state store as a data concentration point.** The store holds whatever
  the compensations will need, which frequently means payment references, customer
  identifiers, and addresses, in one place, for the lifetime of the instance and
  often beyond. This is a privacy problem that the pattern creates and that a local
  transaction does not. Store references rather than values wherever the participant
  can be re-queried, set a retention period on completed instances, and treat the
  store as in scope for whatever data protection regime the business operates under.
- **Event payloads in choreography.** Choreographed events are broadcast to a
  topic, so every subscriber sees the payload. A saga that carries personal data in
  its events distributes that data to services that had no reason to hold it. Carry
  identifiers, and let each participant fetch what it is entitled to.

**Attack surface the pattern closes.** Modest but real. Removing distributed
transactions removes the in-doubt state, in which a participant holds locks
awaiting a coordinator decision. That state is exploitable as a denial of service,
since an attacker who can stall a coordinator can freeze a resource for every other
user. A saga has no equivalent, because no participant ever waits.

**Where the pattern is silent.** The saga says nothing about encryption,
authentication mechanism, or transport security. Those are properties of the
messaging and API layers beneath it, and inventing a saga specific concern where
none exists would be wrong.

## Code

### Go, orchestrated saga with a compensation stack

Compiled and run with `go run`, output verified.

```go
package main

import (
	"errors"
	"fmt"
)

type Step struct {
	Name      string
	Do        func(*Order) error
	Undo      func(*Order) error
	Retriable bool
}

type Order struct {
	ID       string
	Reserved bool
	Charged  bool
	Shipped  bool
	Log      []string
}

var errDeclined = errors.New("card declined")

func run(steps []Step, o *Order) error {
	done := make([]Step, 0, len(steps))
	for _, s := range steps {
		err := s.Do(o)
		if err != nil && s.Retriable {
			// Past the pivot nothing may unwind, so retry until it holds.
			for attempt := 0; attempt < 3 && err != nil; attempt++ {
				err = s.Do(o)
			}
		}
		if err != nil {
			o.Log = append(o.Log, "FAILED "+s.Name+": "+err.Error())
			compensate(done, o)
			return err
		}
		o.Log = append(o.Log, "OK "+s.Name)
		done = append(done, s)
	}
	return nil
}

func compensate(done []Step, o *Order) {
	for i := len(done) - 1; i >= 0; i-- {
		s := done[i]
		if s.Undo == nil {
			o.Log = append(o.Log, "NO-COMPENSATION "+s.Name)
			continue
		}
		if err := s.Undo(o); err != nil {
			o.Log = append(o.Log, "COMPENSATION-FAILED "+s.Name)
			continue
		}
		o.Log = append(o.Log, "UNDO "+s.Name)
	}
}

func main() {
	steps := []Step{
		{
			Name: "reserve-stock",
			Do:   func(o *Order) error { o.Reserved = true; return nil },
			Undo: func(o *Order) error { o.Reserved = false; return nil },
		},
		{
			Name: "charge-card",
			Do:   func(o *Order) error { return errDeclined },
			Undo: func(o *Order) error { o.Charged = false; return nil },
		},
		{
			Name:      "ship",
			Do:        func(o *Order) error { o.Shipped = true; return nil },
			Retriable: true,
		},
	}

	o := &Order{ID: "A-1"}
	err := run(steps, o)
	fmt.Println("result:", err)
	for _, line := range o.Log {
		fmt.Println(" ", line)
	}
	fmt.Printf("reserved=%v charged=%v shipped=%v\n", o.Reserved, o.Charged, o.Shipped)
}
```

Output.

```text
result: card declined
  OK reserve-stock
  FAILED charge-card: card declined
  UNDO reserve-stock
reserved=false charged=false shipped=false
```

Note what the COMPENSATION-FAILED branch does. It records and continues rather
than aborting the unwind, because abandoning the remaining compensations would
strand more state, not less. In production that branch also writes a STUCK record
and raises an alert.

### Python, choreographed saga with a semantic lock

Run with `python3`, output verified.

```python
"""Choreographed saga. Each service reacts to events and emits the next one."""

from dataclasses import dataclass, field


@dataclass
class Event:
    name: str
    order_id: str


@dataclass
class Bus:
    handlers: dict = field(default_factory=dict)
    trace: list = field(default_factory=list)

    def on(self, name):
        def register(fn):
            self.handlers.setdefault(name, []).append(fn)
            return fn
        return register

    def emit(self, event):
        self.trace.append(event.name)
        for fn in self.handlers.get(event.name, []):
            for nxt in fn(event) or []:
                self.emit(nxt)


bus = Bus()
STOCK = {"A-1": "AVAILABLE"}
PAYMENTS = {}


@bus.on("OrderPlaced")
def reserve(e):
    # Semantic lock. The row is marked pending so a concurrent saga can see it.
    STOCK[e.order_id] = "PENDING"
    return [Event("StockReserved", e.order_id)]


@bus.on("StockReserved")
def charge(e):
    PAYMENTS[e.order_id] = "DECLINED"
    return [Event("PaymentDeclined", e.order_id)]


@bus.on("PaymentDeclined")
def release(e):
    if STOCK.get(e.order_id) == "PENDING":
        STOCK[e.order_id] = "AVAILABLE"
    return [Event("StockReleased", e.order_id)]


@bus.on("PaymentAuthorized")
def confirm(e):
    STOCK[e.order_id] = "COMMITTED"
    return [Event("OrderConfirmed", e.order_id)]


if __name__ == "__main__":
    bus.emit(Event("OrderPlaced", "A-1"))
    print(" -> ".join(bus.trace))
    print("stock:", STOCK, "payments:", PAYMENTS)
```

Output.

```text
OrderPlaced -> StockReserved -> PaymentDeclined -> StockReleased
stock: {'A-1': 'AVAILABLE'} payments: {'A-1': 'DECLINED'}
```

Two details carry the pattern. No participant knows the shape of the whole
process, which is the defining property of choreography. And the PENDING marker is
the semantic lock countermeasure in its smallest form, since a concurrent reader
can distinguish held stock from available stock.

### TypeScript, step classification enforced at construction

Compiled with `tsc --strict --target es2020` and run with `node`, output verified.

```typescript
type Kind = "compensatable" | "pivot" | "retriable";

interface Step<S> {
  name: string;
  kind: Kind;
  invoke: (s: S) => Promise<void>;
  compensate?: (s: S) => Promise<void>;
}

class SagaError extends Error {
  constructor(readonly step: string, readonly cause: unknown) {
    super(`step ${step} failed`);
  }
}

function validate<S>(steps: Step<S>[]): void {
  const pivot = steps.findIndex((s) => s.kind === "pivot");
  const cut = pivot === -1 ? steps.length : pivot;
  steps.slice(0, cut).forEach((s) => {
    if (!s.compensate) throw new Error(`${s.name} precedes the pivot and needs a compensation`);
  });
  steps.slice(cut + 1).forEach((s) => {
    if (s.kind !== "retriable") throw new Error(`${s.name} follows the pivot and must be retriable`);
  });
}

async function runSaga<S>(steps: Step<S>[], state: S, log: string[]): Promise<void> {
  validate(steps);
  const done: Step<S>[] = [];
  for (const step of steps) {
    try {
      await withRetry(() => step.invoke(state), step.kind === "retriable" ? 5 : 1);
      log.push(`ok ${step.name}`);
      done.push(step);
    } catch (err) {
      log.push(`fail ${step.name}`);
      for (const prior of done.reverse()) {
        if (!prior.compensate) continue;
        await prior.compensate(state);
        log.push(`undo ${prior.name}`);
      }
      throw new SagaError(step.name, err);
    }
  }
}

async function withRetry(fn: () => Promise<void>, attempts: number): Promise<void> {
  let last: unknown;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (err) {
      last = err;
    }
  }
  throw last;
}

interface Booking {
  seat: boolean;
  paid: boolean;
  emailed: boolean;
}

const steps: Step<Booking>[] = [
  {
    name: "hold-seat",
    kind: "compensatable",
    invoke: async (b) => { b.seat = true; },
    compensate: async (b) => { b.seat = false; },
  },
  {
    name: "capture-payment",
    kind: "pivot",
    invoke: async () => { throw new Error("insufficient funds"); },
  },
  {
    name: "send-confirmation",
    kind: "retriable",
    invoke: async (b) => { b.emailed = true; },
  },
];

const booking: Booking = { seat: false, paid: false, emailed: false };
const log: string[] = [];
runSaga(steps, booking, log)
  .catch((e) => log.push(`saga aborted: ${(e as Error).message}`))
  .then(() => { console.log(log.join("\n")); console.log(booking); });
```

Output.

```text
ok hold-seat
fail capture-payment
undo hold-seat
saga aborted: step capture-payment failed
{ seat: false, paid: false, emailed: false }
```

The `validate` function is the part worth stealing. It turns the compensatable,
pivot, retriable classification from a convention into a construction time error,
so a definition that puts an irreversible step before the pivot cannot be deployed.

### Rust, an ownership-friendly step list

Compiled with `rustc -O` and run, output verified.

```rust
type StepFn = fn(&mut Booking) -> Result<(), String>;

struct Step {
    name: &'static str,
    forward: StepFn,
    backward: Option<StepFn>,
}

#[derive(Default, Debug)]
struct Booking {
    seat: bool,
    charged: bool,
}

fn run(steps: &[Step], state: &mut Booking) -> Result<(), String> {
    let mut done: Vec<&Step> = Vec::new();
    for step in steps {
        match (step.forward)(state) {
            Ok(()) => done.push(step),
            Err(e) => {
                for prior in done.iter().rev() {
                    if let Some(undo) = prior.backward {
                        let _ = undo(state);
                        println!("undo {}", prior.name);
                    }
                }
                return Err(format!("{} failed: {}", step.name, e));
            }
        }
    }
    Ok(())
}

fn main() {
    let steps = [
        Step {
            name: "hold-seat",
            forward: |b| { b.seat = true; Ok(()) },
            backward: Some(|b| { b.seat = false; Ok(()) }),
        },
        Step {
            name: "capture-payment",
            forward: |b| { b.charged = false; Err("declined".to_string()) },
            backward: None,
        },
    ];
    let mut booking = Booking::default();
    println!("{:?}", run(&steps, &mut booking));
    println!("{:?}", booking);
}
```

Output.

```text
undo hold-seat
Err("capture-payment failed: declined")
Booking { seat: false, charged: false }
```

`Option<StepFn>` on `backward` makes the absence of a compensation part of the
type rather than a runtime null, which is the same guarantee the TypeScript
`validate` function reaches for at runtime.

A Java sample was drafted around a saga log with idempotency keys, but no Java
runtime is installed on the authoring machine, so it is omitted rather than
shipped uncompiled.

## 18. References

1. Hector Garcia-Molina, Kenneth Salem. "SAGAS". *Proceedings of the 1987 ACM
   SIGMOD International Conference on Management of Data*, pages 249 to 259.
   DOI 10.1145/38713.38742. Full text PDF verified 2026-08-02 at
   https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf
   Source for the definition of a saga, the semantic nature of compensating
   transactions, the T1 through Tn and Cj through C1 guarantee, the saga execution
   component, and the log before act discipline.
2. Microsoft. "Saga design pattern", Azure Architecture Center, page dated
   2025-02-25.
   https://learn.microsoft.com/en-us/azure/architecture/patterns/saga
   Verified 2026-08-02. Source for the compensable, pivot, and retryable
   classification, the choreography and orchestration benefit and drawback tables,
   the three data anomalies, and the six countermeasures.
3. Amazon Web Services. "Saga orchestration pattern", AWS Prescriptive Guidance,
   Cloud Design Patterns.
   https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html
   Verified 2026-08-02. Source for the two phase commit comparison in a database
   per service architecture, the idempotency requirement, the isolation and
   observability considerations, and the Step Functions production use.
4. Pat Helland. "Life beyond Distributed Transactions, an Apostate's Opinion".
   *3rd Biennial CIDR Conference*, 2007, page 137. PDF verified 2026-08-02 at
   https://www.cidrdb.org/cidr2007/papers/cidr07p15.pdf
   Source for the argument that large scale applications reject distributed
   transactions and reach for workflow style updates over asynchronous messaging.
5. Dale Skeen. "Nonblocking commit protocols". *Proceedings of the 1981 ACM SIGMOD
   International Conference on Management of Data*, pages 133 to 142.
   DOI 10.1145/582318.582339. Record verified 2026-08-02 at
   https://dl.acm.org/doi/10.1145/582318.582339
   Source for the blocking versus nonblocking distinction used in the two phase
   commit comparison. The full text sits behind the ACM paywall, so this citation
   rests on the indexed record and the paper's abstract, not on a full read.
6. Eclipse MicroProfile. *MicroProfile LRA Specification, version 2.0*, final,
   14 February 2023.
   https://download.eclipse.org/microprofile/microprofile-lra-2.0/microprofile-lra-spec-2.0.html
   Verified 2026-08-02. Source for the Long Running Action lineage, the
   compensatable activity model, and the annotation set.
7. Temporal Technologies. "Temporal use cases and design patterns", Temporal
   Platform Documentation.
   https://docs.temporal.io/evaluate/use-cases-design-patterns
   Verified 2026-08-02. Source for the durable workflow engine production use.
8. Camunda. "Compensation events", Camunda 8 Docs.
   https://docs.camunda.io/docs/components/modeler/bpmn/compensation-events/
   Verified 2026-08-02. Source for BPMN compensation semantics and the unordered
   handler invocation default.
9. Eventuate. *eventuate-tram-sagas* repository README.
   https://github.com/eventuate-tram/eventuate-tram-sagas
   Verified 2026-08-02. Source for the framework DSL variant and the Java
   production use.
10. Chris Richardson. "Pattern, Saga", microservices.io.
    https://microservices.io/patterns/data/saga.html
    Verified 2026-08-02. Used to confirm the choreography and orchestration
    definitions and the attribution of the countermeasure catalog to chapter 4
    section 4.3 of *Microservices Patterns*, Manning, 2018. The countermeasure
    names themselves are cited to reference 2, because the microservices.io page
    names the concept without listing them.
