---
name: Compensation Handler
slug: compensation-handler
family: 23-workflow-orchestration
category: workflow orchestration
aliases: [Compensating Transaction, Compensation Action, Semantic Rollback]
first_described: "Hector Garcia-Molina and Kenneth Salem, Sagas, ACM SIGMOD 1987, which coined the term compensating transaction for the undo-step of a long-lived transaction. Given a formal XML construct by the OASIS WS-BPEL 2.0 specification's compensationHandler element, 2007, which cites the Sagas paper directly. Given a graphical, event-driven shape by the OMG BPMN 2.0 specification's Compensation Boundary Event, January 2011"
maturity: canonical
related: [saga, workflow-engine, state-machine-workflow, human-task]
verified: 2026-08-23
---

# Compensation Handler

## 1. Name, aliases, and lineage

A Compensation Handler is the piece of a long-running, multi-step transaction that undoes
the effects of a previously completed step by running a semantically opposite action,
rather than a database ROLLBACK. It is the specific undo mechanism a Saga invokes when a
later step fails and earlier, already-committed steps must be unwound.

The pattern's academic root is a single, precisely dated paper. Hector Garcia-Molina and
Kenneth Salem, Princeton University, "Sagas," ACM SIGMOD 1987. The paper's own core
definition, and the sentence that coined the term.

> "A LLT is a saga if it can be written as a sequence of transactions that can be
> interleaved with other transactions. The database management system guarantees that
> either all the transactions in a saga are successfully completed or compensating
> transactions are run to amend a partial execution."

The paper is explicit, from its first formal definition, that compensation is a semantic
undo, not a state restore, using its own airline-reservation example.

> "To amend partial executions, each saga transaction T1 should be provided with a
> compensating transaction C1. The compensating transaction undoes, from a semantic point
> of view, any of the actions performed by T1, but does not necessarily return the
> database to the state that existed when the execution of T1 began. In our airline
> example, if T1 reserves a seat on a flight, then C1 can cancel the reservation. But C1
> cannot simply store in the database the number of seats that existed when T1 ran because
> other transactions could have run between the time T1 reserved the seat and C1 canceled
> the reservation."

The paper's own memorable illustration of a genuinely non-invertible action names the
canonical technique that every modern vendor doc still echoes without attribution.

> "It may even be possible to compensate for actions that are harder to undo, like sending
> a letter or printing a check. To compensate for the letter, send a second letter
> explaining the problem. To compensate for the check, send a stop-payment message to the
> bank."

Garcia-Molina and Salem credit Jim Gray's own, earlier, informal observation of the same
idea, "transactions often have corresponding compensating transactions within the
application transaction set. This is especially true when the transaction models a real
world action that can be undone, like reserving a rental car or issuing a shipping order,"
citing Gray's 1981 work. This confirms the 1987 paper formalized and named a practice that
was already informally understood, rather than inventing it whole cloth.

The next step in the lineage gave the mechanism a formal, machine-executable shape. WS-BPEL
2.0, the OASIS Web Services Business Process Execution Language specification, defines a
`compensationHandler` XML element and, notably, cites the Sagas paper by its own
bibliography key.

> "Error handling in WS-BPEL processes therefore leverages the concept of compensation,
> that is, application-specific activities that attempt to reverse the effects of a
> previous activity that was carried out as part of a larger unit of work that is being
> abandoned. There is a history of work in this area regarding the use of Sagas and open
> nested transactions. WS-BPEL provides a variant of such a compensation mechanism"

(the spec's [Sagas] reference is a real, formal bibliography citation, direct confirmation
the standard's authors built explicitly on the 1987 paper).

> "Syntactically, a compensationHandler is simply a wrapper for an activity that performs
> compensation."

Finally, BPMN 2.0, the OMG's Business Process Model and Notation specification, gave the
mechanism a graphical, event-driven shape, the Compensation Boundary Event. Read directly
from the official OMG BPMN 2.0.2 specification PDF, section 10.7, "Compensation."

> "Compensation is concerned with undoing steps that were already successfully completed,
> because their results and possibly side effects are no longer desired and need to be
> reversed. If an Activity is still active, it cannot be compensated, but rather needs to
> be canceled." "Compensation is performed by a compensation handler. A compensation
> handler performs the steps necessary to reverse the effects of an Activity."

BPMN 2.0.2 also formally retains a legacy transaction-attribute value for backward
compatibility with BPMN 1.1, its Transaction Sub-Process's `method` attribute "can also be
set to '##compensate,' '##store,' or '##image.'" ([Garcia-Molina and Salem, Sagas, ACM
SIGMOD 1987](https://dl.acm.org/doi/10.1145/38713.38742); [OASIS, WS-BPEL 2.0
specification](https://docs.oasis-open.org/wsbpel/2.0/OS/wsbpel-v2.0-OS.html); [OMG, BPMN
2.0.2 specification](https://www.omg.org/spec/BPMN/2.0.2/PDF), verified 2026-08-23).

## 2. Problem and context

The problem this pattern solves is architectural, not merely inconvenient. Azure's own
Architecture Center names the limit directly.

> "In a single service, transactions follow ACID principles because they operate within a
> single database. However, it can be more complex to achieve ACID compliance across
> multiple services. Traditional database guarantees like ACID aren't directly applicable
> to multiple independently managed data stores."

AWS's Prescriptive Guidance names the exact reason a two-phase commit cannot rescue a
multi-service transaction.

> "To maintain consistency in a transaction, relational databases use the two-phase commit
> method. In distributed systems that follow a database-per-service design pattern, the
> two-phase commit is not an option. This is because each transaction is distributed
> across various databases, and there is no single controller that can coordinate a
> process that's similar to the two-phase commit in relational data stores."

The deeper reason a database ROLLBACK cannot reach across this boundary follows directly
from how a rollback actually works. A database's rollback mechanism replays before-values
from a write-ahead log that is entirely internal to one storage engine. The instant a
step's effect leaves that boundary, a third-party payment gateway charged a card, a
carrier's system holds a seat, an SMTP relay handed a message to the next hop, there is no
before-value any local log can restore, because the effect now lives inside a system with
no shared transaction log at all. WS-BPEL's own introduction states the practical
consequence plainly, "the overall business transaction can fail or be cancelled after many
ACID transactions have been committed. The partial work done must be undone as best as
possible," language that itself signals this is approximation, not guaranteed-perfect
undo. microservices.io names the same fact from its own angle, "a developer must design
compensating transactions that explicitly undo changes made earlier in a saga rather than
relying on the automatic rollback feature of ACID transactions" ([Azure Architecture
Center, Saga design
pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/saga);
[microservices.io, Saga
pattern](https://microservices.io/patterns/data/saga.html), verified 2026-08-23).

## 3. Forces

**Compensation is a semantic apology, not a literal inverse.** Already sourced in full in
dimension 1, the "letter and stop-payment" examples and BPMN's own presumed-abort
principle, "compensation of a failed Activity results in a null operation," both make the
same point from different angles. compensation approximates an undo well enough for the
business, it does not restore bytes.

**Compensations can themselves fail.** The 1987 paper is honest about the worst case, in
a section titled "Other Errors."

> "What happens if a compensating transaction cannot be successfully completed due to
> errors. In this case, the system is stuck, it cannot abort the transaction nor can it
> complete it."

Azure echoes the same honest limit, "Compensating transactions might not always succeed,
which can leave the system in an inconsistent state." Vendors differ on the mitigation.
AWS Step Functions retries a failing compensation task via the same Retry and Catch fields
it uses for forward steps, then routes to a dead-letter or manual-intervention state if
retries exhaust. Temporal's own Saga helper class exposes a continueWithError option,
"gives user the option to bail out of compensation operations if exception is thrown while
running them," defaulting to false, and aggregates every failure into a
CompensationException when it does continue.

**Ordering is reverse by default, with a real, documented exception.** The 1987 paper's
own backward-recovery mechanism runs compensations in reverse commit order, C2 before C1.
WS-BPEL 2.0 formalizes this as Rule 1, "the compensation handler of B MUST run to
completion before the compensation handler of A is started," where B has a control
dependency on A. Temporal's samples name it directly, "Compensate in Last-In-First-Out
order, to undo in the reverse order that activities were applied." But both BPMN and
WS-BPEL carve out room for the exception. BPMN's own worked example shows a compensation
handler that "runs Compensation Activities in an order different from the order in the
forward case," and WS-BPEL's own introduction gives the business reason such an exception
is sometimes required, "if a payroll advance has been given to pay for the travel, the
reservation must be successfully cancelled before the payroll advance for it can be
reversed," meaning the compensation actions must run in the SAME order as the originals,
not reversed. Reverse order is the strong default, never an absolute law.

**Idempotency is not optional.** WS-BPEL 2.0 gives the strongest, most precise guarantee
found anywhere in this research, written as a formal engine-level semantic rule rather
than mere advice.

> "Any repeated attempt to compensate immediately enclosed scopes is treated as executing
> an empty activity."

AWS and Azure both state the same requirement as an operational necessity rather than a
spec guarantee, "Saga participants need to be idempotent to allow repeated execution in
case of transient failures." AWS's own reference implementation operationalizes this with
a concrete, testable technique, a compensating transaction's ID is a UUIDv5 deterministically
derived from the order ID and the transaction type, so a retried compensation overwrites
its own prior record instead of double-refunding a customer ([Garcia-Molina and Salem,
Sagas, 1987]; [Azure Architecture Center, Saga design pattern]; [docs.aws.amazon.com,
Handling errors in Step Functions
workflows](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html);
[github.com, temporalio/sdk-java,
Saga.java](https://github.com/temporalio/sdk-java/blob/main/temporal-sdk/src/main/java/io/temporal/workflow/Saga.java);
[github.com, aws-samples/aws-step-functions-long-lived-transactions,
guide.md](https://github.com/aws-samples/aws-step-functions-long-lived-transactions/blob/main/docs/guide.md),
verified 2026-08-23).

## 4. Applicability and non-applicability

**Reach for compensation handling when.**

- Data consistency must span independently owned services or data stores with no shared
  transaction coordinator, per the AWS and Azure statements in dimension 2.
- Azure's own guidance names the direct fit, data consistency matters in a distributed
  system without tight coupling, and, in its own words, "You need to roll back or
  compensate if one of the operations in the sequence fails."
- AWS names the same signal from the storage side, "The data store doesn't provide 2PC to
  provide ACID transactions, and implementing 2PC within the application boundaries is a
  complex task."

**It may not be the right fit when.**

- Azure names the exact opposite shape directly, "Transactions are tightly coupled.
  Compensating transactions occur in earlier participants. There are cyclic dependencies."
  Cyclic dependencies specifically break the whole reverse-order mental model this
  pattern relies on.
- The whole operation can stay inside one service and one database. A plain ACID
  transaction is strictly simpler and should be preferred, the compensation machinery pays
  for a problem that does not exist yet.

**Designing for compensatability is a design-time discipline, not an afterthought.** Three
independent sources converge on treating this as something you build in from the start,
never bolt on later. Azure's own taxonomy classifies every step in a saga up front as
compensable, pivot, or retryable, before the saga is ever built (dimension 5). AWS states
idempotency as a standing requirement on every participant service. The 1987 paper itself
frames this as the central design question, "the programmer must write code that performs
the action and preserves the database consistency constraints," treating the forward step
and its compensation as a matched pair authored together, never one written first and the
other retrofitted.

## 5. Structure

Cross-checked against the 1987 paper, the BPMN 2.0.2 spec, the WS-BPEL 2.0 spec, and Azure
and AWS vendor docs.

| Term | Definition | Source |
|---|---|---|
| Forward Activity / Compensable Transaction | An activity or transaction whose effects "can be undone or compensated for by other transactions with the opposite effect" | Azure Architecture Center |
| Compensation Activity / Compensation Handler | "Compensation is performed by a compensation handler. A compensation handler performs the steps necessary to reverse the effects of an Activity." A Compensation Activity is "connected to the boundary Event through an Association" | BPMN 2.0.2 spec section 10.7, 10.7.1 |
| compensationHandler (formal element) | "A compensationHandler is simply a wrapper for an activity that performs compensation" | WS-BPEL 2.0 spec section 12.4.1 |
| Compensation Boundary Event | "When attached to the boundary of an Activity, this Event is used to catch the Compensation Event. Compensations can only be triggered after completion of the Activity to which they are attached. Thus they cannot interrupt the Activity" | BPMN 2.0.2 spec, Intermediate Events table |
| Compensation Throw Event | "Compensation is triggered using a compensation throw Event. By default, compensation is triggered synchronously. Alternatively, compensation can just be triggered without waiting for its completion, by setting the throw Compensation Event's waitForCompletion attribute to false" | BPMN 2.0.2 spec section 10.7.2 |
| Pivot Transaction | "The go/no-go point in a saga. If the pivot transaction commits, the saga will run until completion. A pivot transaction can be a transaction that's neither compensatable nor retriable. Alternatively, it can be the last compensatable transaction or the first retriable transaction." Verified directly, exact wording, from the companion repository for Chris Richardson's book Microservices Patterns, chapter four | [github.com, learn-co-curriculum/microservices-patterns-chapter-4](https://github.com/learn-co-curriculum/microservices-patterns-chapter-4) |
| Retriable transaction | "Transactions that follow the pivot transaction and are guaranteed to succeed," reinforced by AWS and Azure's own idempotency requirements for every participant past the pivot | Same source, cross-checked against Azure and AWS |
| Scope Snapshot | The frozen state a compensation handler is allowed to act on, captured at the moment the forward activity completed. BPMN calls it "snapshot data," WS-BPEL calls it "scope snapshot," "the preserved state of a successfully completed uncompensated scope" | BPMN 2.0.2 section 10.7. WS-BPEL 2.0 section 12.4.2 |

A note on attribution, stated honestly. The Pivot Transaction, Compensatable, and
Retriable vocabulary is very often credited in the wider industry to Caitie McCaffrey's
2015 conference talk, "Applying the Saga Pattern." Her own original slide deck, fetched
directly for this entry, uses a different vocabulary entirely, sub-transactions Ti and
compensating transactions Ci, tracked in a persisted Saga Log interpreted by a Saga
Execution Coordinator. The three-part pivot and compensatable and retriable terminology
traces, in exact verbatim wording, to Chris Richardson's 2018 book Microservices Patterns
instead, confirmed directly from its own companion repository. Both are real, useful,
independently valuable sources, they are simply not interchangeable, and this entry cites
each for what it actually said, not for what is commonly assumed.

## 6. ASCII diagram

```
 FORWARD PATH, each step commits locally, then triggers the next

   +----------+     +----------+     +----------+     +----------+
   |  Step 1  | --> |  Step 2  | --> |  Step 3  |  X  |  Step 4  |
   |  T1      |     |  T2      |     |  T3      |FAILS|  never   |
   | commits  |     | commits  |     | (fault)  |     |  runs    |
   +----------+     +----------+     +----------+     +----------+
        |                 |                |
        | compensable     | compensable    | T3 never committed,
        | (has C1)        | (has C2)       | rolled back normally

 COMPENSATION PATH, fires in REVERSE order, only for steps that committed

                                  +----------+
                                  |    C2    |
                                  | undo T2  |
                                  +----+-----+
                                       |
                                       v
                                  +----------+
                                  |    C1    |
                                  | undo T1  |
                                  +----+-----+
                                       |
                                       v
                             +-------------------+
                             |  SAGA COMPENSATED  |
                             |  final state is    |
                             |  consistent, the    |
                             |  overall transaction|
                             |  still FAILED       |
                             +-------------------+
```

## 7. Dynamics

```
1. A saga executes forward steps T1, T2, T3, each committing locally
   and, where a compensation exists, registering it (Temporal's own
   pattern, register the compensation the moment the step succeeds,
   not upfront).
2. Step Tn fails before it commits. It rolls back normally, since it
   never left local scope, nothing to compensate.
3. The orchestrator (or the saga's own failure handler) walks the
   list of registered compensations in reverse.
4. Each compensation runs. If one fails, the strategy differs by
   vendor, retry it with backoff, or log and continue unwinding the
   rest, or halt and page a human.
5. Once every eligible compensation has run (or exhausted its
   retries), the saga reaches a terminal, consistent state, the
   overall business transaction failed, but no step is left with an
   orphaned, unacknowledged side effect.
```

## 8. Implementation variants

**AWS Step Functions.** Compensation rides the same Retry and Catch state fields used for
any failure. "When the error name appears in the value of a catcher's ErrorEquals field,
the state machine transitions to the state named in the Next field," with Retry trying
first, "Step Functions uses any appropriate retriers first. If the retry policy fails to
resolve the error, Step Functions applies the matching catcher transition." AWS ships two
real, maintained reference implementations under its own GitHub organization.
aws-samples slash aws-step-functions-long-lived-transactions, an order and payment and
inventory saga whose state machine names each compensating Lambda directly,
inventory-release and payment-credit, and aws-samples slash aws-step-functions-saga-pattern-with-sam,
a trip-booking saga across hotel, flight, and car, whose own README states plainly, "Each
request has a compensating request for rollback" ([docs.aws.amazon.com, Handling errors in
Step Functions
workflows](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html);
[github.com,
aws-samples/aws-step-functions-long-lived-transactions](https://github.com/aws-samples/aws-step-functions-long-lived-transactions);
[github.com,
aws-samples/aws-step-functions-saga-pattern-with-sam](https://github.com/aws-samples/aws-step-functions-saga-pattern-with-sam),
verified 2026-08-23).

**Temporal, a genuine built-in helper class, not just a documented pattern.** The Java
SDK ships io.temporal.workflow.Saga as a first-class primitive.

```
Saga saga = new Saga(options);
try {
  String r = activity.foo();
  saga.addCompensation(activity::cleanupFoo, arg2, r);
} catch (Exception e) {
  saga.compensate();
}
```

Two configuration flags map directly onto dimension 9's trade-offs, parallelCompensation
(default false, "the compensation operations will be run the reverse order as they are
added" when false), and continueWithError (dimension 3). Temporal's own documentation
states the general pattern plainly, "You register compensations as each step completes,
then automatically trigger them when errors occur," so cleanup happens reliably, and
its worked example shows a compensation registered BEFORE its forward step runs, "it
executes even if addBankAccount failed mid-flight, its implementation must be idempotent."
Equivalent Saga helpers or hand-rolled compensation-stack samples were confirmed, via a
live GitHub code search across the temporalio organization, in the PHP, Go, dot-NET,
Ruby, Rust, and TypeScript SDKs as well ([github.com, temporalio/documentation,
saga-pattern.mdx](https://github.com/temporalio/documentation/blob/main/docs/design-patterns/saga-pattern.mdx);
[github.com, temporalio/sdk-java, Saga.java], verified 2026-08-23).

**WS-BPEL engines, confirmed legacy.** Apache ODE, the best-known open-source WS-BPEL
engine, is formally retired. Its own site states, "This project has retired. For details
please refer to its Attic page." Its last release, version 1.3.8, shipped March 23, 2018.
A live GitHub search across every WS-BPEL engine this pass could identify, ODE, bpel-g,
WSO2 BPS, and several academic conformance-test projects, found none with commit activity
past 2019 or 2020. Stated honestly, as of this verification the formal compensationHandler
XML construct has no actively maintained open-source engine implementing it, having been
succeeded by code-first orchestration (Step Functions, Temporal) and by BPMN's own
Compensation Boundary Event in modern BPM systems ([ode.apache.org], verified 2026-08-23).

**A lighter-weight, no-engine implementation.** Chris Richardson's microservices.io
states the same undo-in-reverse mechanic without a dedicated engine, "the saga executes a
series of compensating transactions that undo the changes that were made by the preceding
local transactions," pairing it with the Transactional Outbox pattern to atomically
persist a forward step's local state alongside the event that will drive the next step or
trigger compensation. A team without any orchestration engine typically builds a plain
in-process stack of undo-closures, pushing one after each successful step and popping and
running them in reverse on failure, effectively Temporal's own hand-rolled samples shape,
minus the durable-execution guarantee. This narrower, engine-free shape is this entry's own
reasoned synthesis of the sourced mechanics above, no single named engineering blog post
describing exactly this shape with no engine at all was found this pass ([microservices.io,
Saga pattern], verified 2026-08-23).

## 9. Known production uses

1. **AWS's own reference architectures.** Both aws-samples repositories named in
   dimension 8 are real, currently maintained, code-backed implementations under AWS's own
   GitHub organization, not third-party blog posts. the order and inventory and payment
   saga, and the hotel and flight and car trip-booking saga, are AWS's chosen canonical
   demonstrations of this exact mechanism.
2. **Temporal's own SDK test suites.** Temporal's Java SDK carries its own dedicated
   SagaTest.java, testing the built-in Saga class against a forced mid-saga failure
   and asserting the exact reverse-order compensation call sequence, and a second test,
   testSagaParallelCompensation, proving the parallel-mode trade-off in code. Confirmed
   present across the Go, Ruby, PHP, and Kotlin SDK sample and test suites as well.
3. **A recently shipped, verified AI-agent adoption.** LangGraph's node-level error
   handler (dimension 14) is itself production code shipped by LangChain, described in
   their own docs as existing specifically "for compensation flows (Saga patterns)."

Stated honestly, no real, named, non-vendor company's engineering blog post documenting a
flight and hotel style compensation case study was found this pass, despite a genuine
attempt. The flight and hotel domain traces to the 1987 paper's own airline example and to
WS-BPEL's own travel-itinerary worked example, both academic and standards-body sources,
not a company's production postmortem.

## 10. Consequences

**Positive.**

- A rejected or timed-out step no longer leaves an orphaned, unacknowledged side effect,
  the customer was charged but never got their order, or a seat stayed reserved forever.
- Reverse-order execution is a well-defined, formally specified default (WS-BPEL Rule 1),
  not a convention every team reinvents from scratch.
- WS-BPEL's spec-level idempotency guarantee, and Temporal's registered-before-execution
  design, mean a retried compensation is safe by construction when the pattern is followed.
- The pivot transaction concept gives a saga a clear, named point past which the system
  commits to forward progress rather than continuing to hedge.

**Negative.**

- A compensation can itself fail, and the 1987 paper is honest that this can leave the
  system genuinely stuck, no amount of pattern-following removes this risk entirely.
- Compensation is an approximation, not a true undo, for a genuinely irreversible action
  (a shipped package, a sent email), the fix is a corrective action, never a literal
  reversal, and that distinction must be designed for up front.
- WS-BPEL, the formal, most rigorously specified implementation of this pattern, is now a
  legacy technology with no actively maintained engine, a real cost for anyone who adopted
  it early.
- A compensation trigger exposed on an unauthenticated channel is a real, currently
  exploited vulnerability class, detailed in dimension 17.

## 11. Failure modes and misuse

**A stuck saga with no working compensation.** The 1987 paper's own honest limit, quoted
in full in dimension 3, "the system is stuck, it cannot abort the transaction nor can it
complete it," is the sourced worst case a bug in compensation logic itself produces.

**Choosing literal undo over semantic compensation for an irreversible action.** Azure's
own older Compensating Transaction pattern documentation gives the exact worked example.
A trip through Seattle, London, Paris, and back to Seattle, with flights already booked,
then a hotel reservation fails. "In many business solutions, failure of a single step does
not always necessitate rolling the system back by using a compensating transaction. It is
preferable to offer the customer a room at a different hotel in the same city rather than
cancelling the flights." The same page notes plainly, "unbooking a seat on a flight might
not entitle the customer to a complete refund of any money paid," the compensation is a
business-rule-driven approximation, never a guaranteed literal inverse.

**An unauthorized party triggering the compensation.** This is a real, currently exploited
vulnerability class, not a hypothetical, covered in full in dimension 17. A refund or
order-reversal webhook exposed with no authentication is exactly this failure mode.

**Non-idempotent compensation logic causing a double-undo.** WS-BPEL's own formal
guarantee, "any repeated attempt to compensate is treated as executing an empty activity,"
exists precisely because an engine that lacks this guarantee can double-refund a customer
or double-release an inventory hold on a retried compensation.

## 12. Trade-off matrix

| Approach | Reverse-order guarantee | Idempotency guarantee | Compensation-failure handling | Setup cost |
|---|---|---|---|---|
| AWS Step Functions, Catch and Retry | Modeled by hand in the state machine's own transitions, not automatic | Left to the developer, AWS's own sample uses deterministic UUIDv5 IDs | Retry then Catch to a dead-letter or manual-intervention state | Low, one state field per compensation branch |
| Temporal, the Saga helper class | Automatic, LIFO by default, configurable | Left to the developer, but the API design (register on success) structurally encourages it | continueWithError flag, aggregated CompensationException on parallel mode | Low, a few lines against a real SDK class |
| WS-BPEL, compensationHandler | Formally specified (Rule 1) | Formally specified, spec-mandated no-op on repeat | Left to the engine's own error-handling machinery | High, and the engines are now legacy |
| BPMN, Compensation Boundary Event | Default order, explicitly overridable per the spec's own worked example | Not itself specified by BPMN, left to the implementing engine | Left to the implementing engine (for example Camunda) | Moderate, a full BPM engine to run |

## 13. Related and incompatible patterns

**Saga** (sibling entry, published). This entry's own mechanism IS the thing a Saga
invokes on failure. The relationship is precise. what triggers compensation is a step's
failure, surfaced to the orchestrator directly (AWS Step Functions), or as a published
failure event other participants react to (choreography). How the saga tracks which
compensations are eligible is, per Temporal's own documented mechanism, an ordered list
built up as each step succeeds, never computed upfront, then walked in reverse on failure.
McCaffrey's own original framing (dimension 5's honest attribution note) names this
tracking structure a persisted Saga Log, interpreted by a Saga Execution Coordinator, an
independently useful, differently-shaped description of the same underlying mechanism
Richardson's pivot and compensatable and retriable vocabulary also describes.

**Workflow Engine** (sibling entry, published). The runtime that persists the saga's own
compensation list durably, so it survives a crash, is exactly what a Workflow Engine
provides. a hand-rolled, in-memory list of undo-closures does not survive a process
restart on its own, the durable-execution guarantee is what a Workflow Engine adds on top.

**State Machine Workflow** (sibling entry, published). Compensation is the specific action
a saga's own state machine transitions into on a failure signal, the compensation branch
is a first-class part of the transition graph, not a mechanism bolted on separately, shown
directly in AWS's own sample's state diagram.

**Human Task** (sibling entry, published). A rejected or timed-out human-approval step is
exactly the kind of failure signal that should trigger compensation of everything that
already committed before it, the same relationship this entry's sibling Human Task entry
names from its own side.

## 14. Refactoring path in and out

**Introducing it.** The signal is a saga whose ad hoc undo logic keeps growing at each new
failure discovered in production. Formalizing it, a Temporal Saga helper, or explicit
Catch branches in a Step Functions state machine, gives that logic one named home with a
defined ordering and a defined idempotency contract, rather than scattered, inconsistent
handling per code path.

**Evolving or narrowing it.** WS-BPEL's own formal compensationHandler construct is the
clearest, most complete example of this pattern's own evolution. Teams that adopted it in
the mid-2000s have, per dimension 8's honest finding, migrated to code-first orchestration
engines or to BPMN's own Compensation Boundary Event inside a modern BPM system, because no
actively maintained WS-BPEL engine remains. The underlying pattern did not disappear, its
implementation vehicle did.

**A newer variant, applied to AI agents.** LangGraph shipped a node-level error handler in
2026 that its own documentation names directly for this purpose. "This is useful for
compensation flows (Saga patterns) where you want to recover gracefully rather than abort
the entire graph." The handler fires only after a configured retry policy exhausts, and
can route the graph to a recovery branch. Verified via the shipping pull request itself,
langchain-ai/langgraphjs number 2451, created May 28 2026 and merged June 10 2026, and
requires langgraph version 1.2 or newer in Python, the equivalent JavaScript package
version 1.4.0 or newer. This is the same underlying shape as AWS's Catch field and
Temporal's Saga class, applied at the point where an autonomous agent's own next action,
rather than a distributed service call, is what needs undoing.

## 15. Testing and verification

**Temporal.** The Go SDK's own sample carries a directly on-point test, mocking both a
forward activity and its compensation, forcing a mid-saga error, and asserting the
workflow completed with an error.

```
env.OnActivity(Withdraw, mock.Anything, testDetails).Return(nil)
env.OnActivity(WithdrawCompensation, mock.Anything, testDetails).Return(nil)
env.OnActivity(StepWithError, mock.Anything, testDetails).Return(errors.New("some error"))
env.ExecuteWorkflow(TransferMoney, testDetails)
require.True(t, env.IsWorkflowCompleted())
require.Error(t, env.GetWorkflowError())
```

The Java SDK's own test of its built-in Saga class goes further, asserting the exact
reverse-order call sequence via a tracing interceptor, and a second test proving the
parallelCompensation mode's weaker, order-agnostic guarantee in code rather than only in
prose ([github.com, temporalio/samples-go,
workflow_test.go](https://github.com/temporalio/samples-go/blob/main/saga/workflow_test.go);
[github.com, temporalio/sdk-java,
SagaTest.java](https://github.com/temporalio/sdk-java/blob/main/temporal-sdk/src/test/java/io/temporal/workflow/SagaTest.java),
verified 2026-08-23).

**AWS.** The deterministic-UUID technique from dimension 3 is itself a testable
idempotency design, asserting a compensation invoked twice produces the same deterministic
ID and overwrites its own prior record rather than duplicating it.

**Compensation idempotency testing, as a general practice.** No single vendor page names
this exact methodology directly. It is this entry's own synthesis of the three sourced
requirements above, run the compensation twice in a test and assert the end state matches
running it once, grounded in real, vendor-stated design requirements rather than presented
as a directly cited methodology.

## 16. Observability signals

**AWS Step Functions.** Real, named CloudWatch metrics map directly onto this pattern.
ExecutionsFailed and ExecutionsAborted against ExecutionsStarted are the closest
built-in proxy for a compensation trigger rate, since a Catch transition into a
compensation branch is what usually produces those outcomes for a saga-shaped state
machine. ActivityRunTime gives a compensation latency proxy when the activity in
question is a compensating one. The redrive family, ExecutionsRedriven,
RedrivenExecutionsFailed, is the closest built-in stuck-compensation signal. AWS's own
caveat is worth carrying forward, "CloudWatch metrics are delivered on a best-effort
basis. The completeness and timeliness of metrics are not guaranteed."

**Temporal.** temporal_workflow_failed, temporal_activity_execution_failed, and
temporal_activity_execution_latency are real, named SDK metrics. Stated honestly, no
metric is specifically and uniquely named for saga compensation, monitoring it means
filtering these generic metrics by the compensating activities' own type names, a derived
signal, not a vendor-native one.

**Azure.** Rather than a fixed metric catalogue, Azure's own mechanism is a
SetCustomStatus call an orchestrator can use to report "completion percentages, step
descriptions, and error summaries," retrievable via the runtime's own status API,
alongside ready Kusto queries against Application Insights trace data filtered on a
state.Failed value.

## 17. Security and privacy implications

**No CVE directly matching the words compensating transaction, or saga, plus workflow was
found in NVD.** A direct NVD keyword search across several phrasings, "compensating
transaction," "saga workflow," "double refund," "payment reversal," returned zero results
each time. This negative finding is reported honestly rather than papered over.

**Three real, current, directly analogous CVEs were found**, all sharing the identical
root cause, the trigger for a compensating, refund-shaped action was exposed on an
unauthenticated or spoofable channel.

CVE-2026-3640, the STRABL checkout plugin for WordPress, CVSS score 5.3, published June
2026. Its webhook endpoint "registers a REST API webhook endpoint... with a permission
callback of return true," with no shared secret or signature validation, letting an
unauthenticated attacker "issue refunds on existing orders, cancel existing orders, and
apply chargeback fees, all without making a legitimate payment or having any valid
credentials."

CVE-2026-3641, the Appmax plugin for WordPress, CVSS score 5.3, published March 2026,
"without implementing webhook signature validation, secret verification, or any mechanism
to authenticate that incoming webhook requests genuinely originate from the legitimate
Appmax payment service," letting an attacker "craft malicious webhook payloads that can
modify the status of existing WooCommerce orders" to refunded or cancelled.

CVE-2026-0692, the BlueSnap Payment Gateway plugin for WordPress, CVSS score 7.5,
published February 2026. The plugin trusted spoofable request headers, X-Real-IP and
X-Forwarded-For, to validate an IPN request's origin, letting an attacker "bypass IP
allowlist restrictions by spoofing a whitelisted BlueSnap IP address and send forged IPN
data to manipulate order statuses (mark orders as paid, failed, refunded, or on-hold)
without proper authorization" ([nvd.nist.gov, CVE-2026-3640, CVE-2026-3641,
CVE-2026-0692](https://services.nvd.nist.gov/rest/json/cves/2.0), verified 2026-08-23).

All three confirm the general principle this pattern's own design must respect, a
compensation's trigger needs exactly the same authentication and authorization rigor as
the forward action it reverses, never a looser standard just because it is cast as
internal cleanup logic.

**Privacy.** A compensation handler frequently needs the same sensitive data the forward
step used, a payment method to issue a refund against, a shipping address to cancel a
delivery, and that data must remain available in the scope snapshot (dimension 5) long
enough for the compensation to run. No vendor-documented guidance specific to how long
that snapshot data should be retained, or how it should be scoped, was found this pass,
so this observation is this entry's own reasoning, flagged as such.

## 18. References

1. Hector Garcia-Molina and Kenneth Salem. *Sagas*. ACM SIGMOD 1987.
   https://dl.acm.org/doi/10.1145/38713.38742
   Verified 2026-08-23. Source of the compensating-transaction origin and definition.
2. OASIS. *WS-BPEL 2.0 specification*.
   https://docs.oasis-open.org/wsbpel/2.0/OS/wsbpel-v2.0-OS.html
   Verified 2026-08-23. Source of the compensationHandler element and idempotency rule.
3. OMG. *BPMN 2.0.2 specification*.
   https://www.omg.org/spec/BPMN/2.0.2/PDF
   Verified 2026-08-23, section 10.7. Source of the Compensation Boundary Event.
4. Azure Architecture Center. *Saga design pattern*.
   https://learn.microsoft.com/en-us/azure/architecture/patterns/saga
   Verified 2026-08-23. Source of the applicability, pivot vocabulary usage, and orchestration versus choreography comparison.
5. Microsoft. *Compensating Transaction pattern* (previous-versions archive).
   https://learn.microsoft.com/en-us/previous-versions/msp-n-p/dn589804(v=pandp.10)
   Verified 2026-08-23. Source of the flight and hotel worked example and the parallel-compensation-order note.
6. AWS. *Handling errors in Step Functions workflows*.
   https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html
   Verified 2026-08-23. Source of the Retry and Catch mechanism.
7. AWS. *Monitoring Step Functions using Amazon CloudWatch*.
   https://docs.aws.amazon.com/step-functions/latest/dg/procedure-cw-metrics.html
   Verified 2026-08-23. Source of the observability metrics.
8. GitHub. *aws-samples/aws-step-functions-long-lived-transactions*.
   https://github.com/aws-samples/aws-step-functions-long-lived-transactions
   Verified 2026-08-23. Source of the order and inventory and payment saga reference implementation.
9. GitHub. *aws-samples/aws-step-functions-saga-pattern-with-sam*.
   https://github.com/aws-samples/aws-step-functions-saga-pattern-with-sam
   Verified 2026-08-23. Source of the trip-booking saga reference implementation.
10. GitHub. *temporalio/documentation, saga-pattern.mdx*.
    https://github.com/temporalio/documentation/blob/main/docs/design-patterns/saga-pattern.mdx
    Verified 2026-08-23. Source of Temporal's own saga documentation.
11. GitHub. *temporalio/sdk-java, Saga.java*.
    https://github.com/temporalio/sdk-java/blob/main/temporal-sdk/src/main/java/io/temporal/workflow/Saga.java
    Verified 2026-08-23. Source of the built-in Saga helper class.
12. GitHub. *temporalio/sdk-java, SagaTest.java*.
    https://github.com/temporalio/sdk-java/blob/main/temporal-sdk/src/test/java/io/temporal/workflow/SagaTest.java
    Verified 2026-08-23. Source of the reverse-order and parallel-mode compensation tests.
13. GitHub. *temporalio/samples-go, saga/workflow_test.go*.
    https://github.com/temporalio/samples-go/blob/main/saga/workflow_test.go
    Verified 2026-08-23. Source of the Go SDK saga test example.
14. ode.apache.org.
    https://ode.apache.org/
    Verified 2026-08-23. Source of Apache ODE's retirement notice.
15. GitHub. *learn-co-curriculum/microservices-patterns-chapter-4*.
    https://github.com/learn-co-curriculum/microservices-patterns-chapter-4
    Verified 2026-08-23. Source of the pivot, compensatable, and retriable transaction vocabulary, Chris Richardson, Microservices Patterns.
16. GitHub. *CaitieM20/Talks, Sagas README*.
    https://github.com/CaitieM20/Talks/blob/master/Sagas/README.md
    Verified 2026-08-23. Source of the talk's metadata, used to confirm the honest attribution correction in dimension 5.
17. SpeakerDeck. *Applying the Saga Pattern*.
    https://speakerdeck.com/caitiem20/applying-the-saga-pattern
    Verified 2026-08-23. Source confirming the original slide deck's own Ti and Ci and Saga Log vocabulary.
18. microservices.io. *Saga pattern*.
    https://microservices.io/patterns/data/saga.html
    Verified 2026-08-23. Source of the lack-of-automatic-rollback framing and the Transactional Outbox link.
19. NVD. *CVE-2026-3640*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2026-3640
    Verified 2026-08-23.
20. NVD. *CVE-2026-3641*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2026-3641
    Verified 2026-08-23.
21. NVD. *CVE-2026-0692*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2026-0692
    Verified 2026-08-23.
22. GitHub. *langchain-ai/docs, fault-tolerance.mdx*.
    https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/fault-tolerance.mdx
    Verified 2026-08-23. Source of the LangGraph node-level error handler, described by LangChain's own docs for compensation flows.
23. GitHub. *langchain-ai/langgraphjs, CHANGELOG.md*.
    https://github.com/langchain-ai/langgraphjs/blob/main/libs/langgraph-core/CHANGELOG.md
    Verified 2026-08-23. Source of the shipping pull request 2451, merged June 10 2026.
24. Microsoft. *Azure Durable Functions diagnostics*.
    https://learn.microsoft.com/en-us/azure/durable-task/durable-functions/durable-functions-diagnostics
    Verified 2026-08-23. Source of the custom orchestration status and Kusto query guidance.

**Evidence grade.** established

**Most solid findings.** The 1987 Garcia-Molina and Salem paper is confirmed directly from
the original text, including its own honest limit on compensation failure. The BPMN 2.0.2
and WS-BPEL 2.0 specifications are both confirmed directly from their primary source
documents, with WS-BPEL's own bibliography confirming its direct lineage from the Sagas
paper. AWS's and Temporal's own reference implementations and test suites are real,
currently maintained, code-backed sources, not secondary paraphrase. The three CVEs are
NVD-verified and share a precisely on-point root cause. The LangGraph 2024-2026
development is confirmed at the shipping-pull-request level, not from marketing copy.

**Unverified or unclear.** A directly citable, dedicated Azure Durable Functions saga or
compensation implementation page could not be located, three plausible URLs all returned
errors. Azure-specific saga testing guidance was not found and general orchestration
debugging guidance was substituted with that gap named honestly. No single vendor page
names compensation idempotency testing as a methodology, this entry's own dimension 15
synthesis is labeled as such. No real, named, non-vendor company's engineering blog case
study for the classic flight and hotel scenario was found. No verified 2024-2026 named
production postmortem attributable specifically to a compensation or rollback bug was
found, despite a genuine, multi-channel attempt, and that negative finding is reported
rather than invented around.

## Code

### TypeScript, a reverse-order compensation stack with a continue-past-failure option

```typescript
type Compensation = () => Promise<void>;

class CompensationStack {
  private readonly stack: Compensation[] = [];
  private readonly continueOnError: boolean;

  constructor(continueOnError = false) {
    this.continueOnError = continueOnError;
  }

  register(compensation: Compensation): void {
    this.stack.push(compensation);
  }

  async compensate(): Promise<Error[]> {
    const failures: Error[] = [];
    while (this.stack.length > 0) {
      const undo = this.stack.pop()!;
      try {
        await undo();
      } catch (err) {
        failures.push(err as Error);
        if (!this.continueOnError) {
          throw new AggregateError(failures, "compensation failed, stopping unwind");
        }
      }
    }
    return failures;
  }
}

async function reserveInventory(): Promise<void> {
  console.log("inventory reserved");
}
async function releaseInventory(): Promise<void> {
  console.log("inventory released");
}
async function chargeCard(): Promise<void> {
  console.log("card charged");
}
async function refundCard(): Promise<void> {
  console.log("card refunded");
}

async function run(): Promise<void> {
  const saga = new CompensationStack(true);
  await reserveInventory();
  saga.register(releaseInventory);
  await chargeCard();
  saga.register(refundCard);

  const shipmentFailed = true;
  if (shipmentFailed) {
    const failures = await saga.compensate();
    console.log("compensation failures:", failures.length);
  }
}

run();
```

### Python, an idempotent compensation keyed by a deterministic ID

```python
import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Dict, List


def deterministic_compensation_id(order_id: str, kind: str) -> str:
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    return str(uuid.uuid5(namespace, order_id + ":" + kind))


@dataclass
class CompensationLedger:
    applied: Dict[str, bool] = field(default_factory=dict)
    log: List[str] = field(default_factory=list)

    def refund(self, order_id: str) -> bool:
        comp_id = deterministic_compensation_id(order_id, "refund")
        if self.applied.get(comp_id):
            self.log.append("skipped duplicate refund for " + comp_id)
            return False
        self.applied[comp_id] = True
        self.log.append("refunded order " + order_id + ", compensation " + comp_id)
        return True


if __name__ == "__main__":
    ledger = CompensationLedger()
    first = ledger.refund("order-42")
    retried = ledger.refund("order-42")
    print("first refund applied:", first)
    print("retried refund applied (should be False):", retried)
    for line in ledger.log:
        print(line)
```

### Go, a saga runner with LIFO compensation and per-step failure logging

```go
package main

import "fmt"

type Step struct {
	Name       string
	Forward    func() error
	Compensate func()
}

type Saga struct {
	steps      []Step
	completed  []Step
}

func NewSaga(steps ...Step) *Saga {
	return &Saga{steps: steps}
}

func (s *Saga) Run() error {
	for _, step := range s.steps {
		if err := step.Forward(); err != nil {
			fmt.Println("step", step.Name, "failed:", err, "compensating")
			s.compensateAll()
			return err
		}
		s.completed = append(s.completed, step)
	}
	return nil
}

func (s *Saga) compensateAll() {
	for i := len(s.completed) - 1; i >= 0; i-- {
		step := s.completed[i]
		func() {
			defer func() {
				if r := recover(); r != nil {
					fmt.Println("compensation for", step.Name, "panicked:", r, "continuing")
				}
			}()
			step.Compensate()
		}()
	}
}

func main() {
	saga := NewSaga(
		Step{
			Name:       "reserve-inventory",
			Forward:    func() error { fmt.Println("inventory reserved"); return nil },
			Compensate: func() { fmt.Println("inventory released") },
		},
		Step{
			Name:       "charge-payment",
			Forward:    func() error { fmt.Println("payment charged"); return nil },
			Compensate: func() { fmt.Println("payment refunded") },
		},
		Step{
			Name:       "ship-order",
			Forward:    func() error { return fmt.Errorf("carrier unavailable") },
			Compensate: func() { fmt.Println("no shipment to undo") },
		},
	)
	if err := saga.Run(); err != nil {
		fmt.Println("saga ended with error:", err)
	}
}
```
