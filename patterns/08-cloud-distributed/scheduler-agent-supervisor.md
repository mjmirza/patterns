---
name: Scheduler Agent Supervisor
slug: scheduler-agent-supervisor
family: 08-cloud-distributed
category: Coordination
aliases: [Workflow Orchestrator with Watchdog, Orchestrator Worker Watchdog, State Store Driven Workflow]
first_described: "Homer, Sharp, Brader, Narumoto, Swanson. Cloud Design Patterns. Microsoft patterns and practices, 2014 (named catalog entry, still maintained at Microsoft Learn); conceptually related to Hohpe and Woolf's Process Manager, Enterprise Integration Patterns, Addison-Wesley, 2003"
maturity: canonical
related: [saga, compensating-transaction, retry, circuit-breaker, leader-election, competing-consumers, queue-based-load-leveling, choreography]
incompatible_with: [two-phase-commit]
verified: 2026-08-02
---

# Scheduler Agent Supervisor

## 1. Name, aliases, and lineage

The canonical name in this catalog is Scheduler Agent Supervisor, following the
name Microsoft's Azure Architecture Center gives its standalone pattern page,
"Scheduler Agent Supervisor pattern." The page states the pattern's purpose
plainly. To "coordinate a set of distributed actions as a single operation,"
handling failures transparently or undoing completed work so the whole
operation succeeds or fails as one unit (Microsoft Learn, Azure Architecture
Center, "Scheduler Agent Supervisor pattern,"
https://learn.microsoft.com/en-us/azure/architecture/patterns/scheduler-agent-supervisor,
last updated 2025-12-09, verified 2026-08-02). The pattern first appeared as
one of twenty four patterns in Alex Homer, John Sharp, Larry Brader, Masashi
Narumoto and Trent Swanson, *Cloud Design Patterns. Prescriptive Architecture
Guidance for Cloud Applications*, Microsoft patterns and practices, 2014, and
the content has since been migrated onto Microsoft Learn and continues to be
revised there, most recently in 2025.

No competing name has taken hold outside the Microsoft catalog. Practitioners
who arrive at the same architecture from a workflow-engine or job-queue
background usually describe it operationally rather than by a pattern name, as
an "orchestrator with a watchdog," a "durable workflow with a reaper process,"
or simply "the state machine plus the sweep job." This entry treats those
phrases as informal aliases rather than as separate patterns, because they
describe the identical three-role separation the Microsoft catalog names.

The pattern sits next to, and is frequently confused with, the Process Manager
pattern from Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns.
Designing, Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
ISBN 0-321-20068-3. The Azure Architecture Center page says so directly. "The
Scheduler performs a similar function to the Process Manager in the Process
Manager pattern," and adds that the workflow itself is typically defined and
run by a separate workflow engine that the Scheduler controls, which decouples
the business logic from the Scheduler's own responsibilities (Microsoft Learn,
"Scheduler Agent Supervisor pattern," section "Solution," verified 2026-08-02).
The Enterprise Integration Patterns site frames its own pattern the same way, a
central unit that maintains "the state of the sequence" and determines "the
next processing step based on intermediate results" (Enterprise Integration
Patterns, "Process Manager,"
https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html,
verified 2026-08-02). The distinction that matters for this catalog is scope.
Process Manager is a message-routing pattern for a single coordinating
component. Scheduler Agent Supervisor names three separate roles, one of which
exists purely to watch the other two and recover from their failure, and it is
this third role, the Supervisor, that the Process Manager literature does not
call out as its own participant.

A second point of confusion is with the generic phrase "scheduler," which in
operating systems and batch computing means a component that decides *when* a
unit of work runs (a CPU scheduler, a cron daemon, a Kubernetes scheduler that
places pods on nodes). In this pattern, Scheduler is narrower, closer to
"orchestrator," the component that decides the *order and identity* of steps
within one distributed operation and tracks their progress. A reader coming
from Kubernetes should mentally substitute "orchestrator" for "scheduler,"
because the two overlap in name only by coincidence, while the overlap in
mechanism, watching desired state against actual state, is real and is
discussed under Implementation variants.

## 2. Problem and context

An application needs to run a task that has more than one step, and at least
one of those steps calls a remote service or accesses a remote resource that
the application does not control. The Azure Architecture Center states the
starting condition this way. "An application performs tasks that include
multiple steps, some of which might invoke remote services or access remote
resources," and each step "might be independent of each other," but the
application logic still has to run them as one coherent task (Microsoft Learn,
"Scheduler Agent Supervisor pattern," section "Context and problem," verified
2026-08-02).

The concrete shape of the problem is familiar to anyone who has written an
order-processing pipeline, a resource-provisioning flow, or an onboarding
sequence. A request arrives, and has to move through a sequence of remote
calls, reserve inventory, charge a payment provider, schedule a shipment,
notify a partner system. Any one of those calls can fail outright, hang, or
take longer than expected, because a network partition or an overloaded
downstream service does not announce itself in advance. The naive version
writes the whole sequence as one synchronous function with a chain of try or
catch blocks, and it works during a demo. It stops working the moment a
remote call gets slow rather than erroring cleanly, because the calling
process now cannot distinguish "still working" from "silently dead," and no
record survives a crash of that process itself.

The context that pushes toward this pattern rather than a simpler sequential
function has three parts, and all three usually need to hold before the extra
machinery earns its cost.

First, the task is genuinely multi-step and the steps talk to systems outside
the application's own process boundary, so partial failure is a normal
operating condition rather than an edge case. Second, the operation must
survive the failure of the orchestrating process itself. A crash midway
through order processing cannot silently drop the order. Some other process,
possibly a fresh instance of the same code, has to be able to discover the
half-finished order and either continue it or roll it back. Third, the
individual steps are wrapped by adapters, one per remote system, that already
know how to talk to that system and, ideally, already implement whatever
retry logic is local to that one call. The pattern gives those three concerns
three separate homes rather than mixing them into one function. Routing and
sequencing state lives with the Scheduler, per-system communication logic
lives with the Agent, and failure detection lives with the Supervisor.

The pattern is a cloud and distributed systems answer, not a general
workflow-engine feature list. Homer, Sharp, Brader, Narumoto and Swanson
wrote the original catalog for teams building on early Azure services where
a remote call could fail for reasons outside the application's own code,
and the pattern's shape reflects that origin. No shared transaction
coordinator across services, no assumption a hung call can be cancelled,
and an explicit acceptance that the same side effect might be attempted
more than once.

## 3. Forces

This dimension is largely engineering judgement about which pressure the
pattern favors, stated as reasoning rather than as a sourced claim, except
where a specific mechanism is cited from the Microsoft catalog page.

**Resiliency against operability cost.** The pattern buys resilience against
transient and even long outages in a remote dependency, at the direct cost of
three components to build, test, and run instead of one function to write.
The Azure Architecture Center names this trade openly under "Issues and
considerations." "This pattern can be difficult to implement and requires
thorough testing of each possible failure mode of the system," and warns that
the recovery logic held by the Scheduler is "complex and dependent on state
information held in the state store" (Microsoft Learn, "Scheduler Agent
Supervisor pattern," section "Issues and considerations," verified
2026-08-02). A team adopting this pattern is choosing to spend real
engineering time up front so that a 2 a.m. partial outage self-heals instead
of paging a human.

**Latency against correctness under uncertainty.** Every step carries a
complete-by deadline rather than an assumption of prompt response, which means
the system deliberately waits out a window before declaring a step failed. A
short deadline recovers quickly from real failures but risks declaring a slow
but genuinely successful call as failed, which forces the burden of
idempotency onto every Agent. A long deadline reduces false failures but
increases end-to-end latency for the legitimate failure case. There is no
deadline that eliminates this tension. The pattern trades a tunable amount of
latency for a tunable amount of false-positive failure detection, and the
right setting is a property of the remote system's own latency distribution,
not of the pattern.

**Consistency against availability of the calling process.** The pattern
explicitly favors keeping the orchestrating logic available and recoverable
over guaranteeing that any single step commits or rolls back atomically with
its neighbors. There is no cross-service transaction. A step that partially
succeeds at the remote system while the coordinator considers it failed is a
real, expected outcome, not a bug, and the pattern's answer is idempotency and
compensation rather than atomicity. This is the same trade the Saga pattern
makes, and the two patterns are frequently combined, with Scheduler Agent
Supervisor providing the state-tracking and retry machinery and a
compensating transaction providing the undo path when retries are exhausted.

**Coupling against reuse.** The Scheduler couples to the identity and order of
steps, not to how any individual step is executed, which is delegated to an
Agent per remote system. This keeps the orchestrator reusable across
workflows that share steps, at the cost of an extra indirection. Adding a new
kind of remote call means writing a new Agent, and the Scheduler has to be
told how to address it, typically through a message channel or queue rather
than a direct method call.

**Cognitive load against auditability.** A synchronous chain of calls is
easier to read start to finish. A Scheduler Agent Supervisor implementation
spreads the same logic across three components and a persistent state store,
which raises the cost of "reading the code to understand what happens next"
but lowers the cost of "looking at the state store to see exactly where a
specific in-flight task currently sits." The pattern favors the second
property, operational visibility into a live system, over the first, and that
is a deliberate trade for anything that runs unattended.

## 4. Applicability and non-applicability

**Reach for this pattern when.**

- The task has multiple steps and at least one step calls a remote service or
  resource that the application does not fully control, so transient and
  non-transient failures are a normal operating condition rather than a rare
  event. The Azure catalog page states this as the primary "when to use"
  condition (Microsoft Learn, "Scheduler Agent Supervisor pattern," section
  "When to use this pattern," verified 2026-08-02).
- The operation must survive the failure of the process running it. A crash,
  a redeploy, or an autoscale-down event should not silently lose in-flight
  work. A fresh instance should be able to pick the task back up from durable
  state.
- The remote calls are already, or can be made, idempotent, so that a retried
  step does not double-charge a card, double-ship an order, or double-post a
  message. The pattern depends on this property rather than granting it. See
  the Issues and considerations note quoted in dimension 3.
- The task benefits from a durable, queryable record of progress. "Which step
  is this order on right now," "how many times has step three failed,"
  "which orders are stuck." This is a background job class of problem, and
  Microsoft explicitly places the pattern there. "This pattern is common in
  background jobs that orchestrate multistep workflows, like order processing
  or resource provisioning" (Microsoft Learn, same page, section "When to use
  this pattern," verified 2026-08-02).
- The team can tolerate, and design for, a compensating action when a step
  cannot be completed after a bounded number of retries, rather than assuming
  every operation eventually succeeds.

**Do not reach for this pattern when.**

- The task does not invoke a remote service or access a remote resource. The
  Azure catalog page says this directly. "This pattern might not be suitable
  for tasks that don't invoke remote services or access remote resources"
  (Microsoft Learn, same page, section "When to use this pattern," verified
  2026-08-02). A purely in-process, purely local sequence of function calls
  gains nothing from a state store, a queue, and a separate watchdog process,
  and paying that cost is the single most common misapplication of this
  pattern in code review.
- The operation genuinely needs atomic, all-or-nothing commit across systems
  and those systems expose a real distributed transaction coordinator, such
  as an XA-capable resource manager reachable from a single database or
  message broker. In that narrow case a classic two-phase commit may be
  simpler and stronger, though it introduces its own availability cost. This
  is why `incompatible_with` lists two-phase commit for this entry, not
  because the two cannot coexist in one organization, but because a single
  operation should pick one consistency model rather than layer both.
- The task is a single remote call with no sequencing to track. Wrapping one
  call in a Scheduler, one Agent, and a Supervisor to watch a single step adds
  three moving parts to replace what a bounded retry with backoff, discussed
  in the sibling Retry entry, already does in a few lines.
- Latency is the dominant requirement and the caller needs a synchronous
  answer within tens of milliseconds. The complete-by deadline mechanism this
  pattern relies on is built around tolerating seconds to minutes of
  uncertainty, not microseconds, and a Supervisor sweep interval measured in
  seconds is the wrong tool for a request-response API on the critical path
  of a page load.
- The steps cannot be made idempotent and cannot be wrapped to become
  idempotent, for example a physical, irreversible side effect with no
  compensating action available, such as an SMS one-time code that has
  already been read by the recipient. The pattern's recovery strategy assumes
  a retried or compensated step is safe to repeat or undo. Where that
  assumption cannot be met, the failure mode is a duplicated or unrecoverable
  side effect, discussed under Failure modes and misuse.
- A single team owns a small number of services, all of which are reachable
  synchronously with low, bounded latency and rare failure, and simplicity of
  the codebase matters more than surviving a rare partial outage. Many
  internal admin tools and low-traffic CRUD services fall here, and adding
  this pattern to them is premature machinery.

## 5. Structure

The pattern names four participants, three active roles and one passive
store, and the Azure catalog is explicit that all three roles are "logical
components" whose "physical implementation depends on the technology being
used," so one physical service can host more than one logical role, and a
production system typically runs many instances of each (Microsoft Learn,
"Scheduler Agent Supervisor pattern," section "Solution," verified
2026-08-02).

- **Scheduler.** Owns the workflow definition, that is, the ordered or
  conditionally ordered list of steps that make up one task. For each task
  instance, the Scheduler records step state in the state store as it
  progresses ("not yet started," "running," "completed"), attaches a
  complete-by deadline to each running step, and dispatches a step to the
  Agent responsible for it, usually over an asynchronous request or response
  channel such as a queue. The Scheduler does not itself talk to remote
  systems.
- **Agent.** Wraps exactly one remote service or resource per Agent
  implementation and executes the actual call on the Scheduler's behalf. The
  Agent may implement its own retry logic local to that single call, bounded
  by the complete-by deadline it was given. Once that deadline has passed,
  the Agent must stop working on the step and must not report anything back,
  success, failure, or partial result, because by then the Scheduler has
  already assumed the step failed and a different attempt may already be in
  flight. This "silence after timeout" rule is stated explicitly in the
  Azure catalog. "The Agent should stop its work and not try to return
  anything to the Scheduler... or try any form of recovery" (Microsoft Learn,
  same page, section "Solution," verified 2026-08-02).
- **Supervisor.** Runs on its own schedule, independent of any single task,
  and periodically scans the state store for steps whose complete-by deadline
  has passed while their state still reads "running." For each one it finds,
  the Supervisor either arranges for the step to be retried, by extending the
  deadline and telling the Scheduler to reattempt it, or, once a retry count
  threshold is exceeded, treats the failure as non-transient and either
  raises it for operator attention or triggers a compensating transaction to
  undo the steps already completed. The Supervisor does not know the business
  meaning of any step. Its entire responsibility is timeout detection and
  triggering the Scheduler's or Agent's own recovery mechanics, never
  performing the recovery itself.
- **State store.** A durable, shared data store, external to the Scheduler,
  Agent, and Supervisor processes, that records the current state of every
  in-flight task and step. It is the single source of truth all three roles
  read from and write to, and it is what lets the Supervisor detect a stalled
  step without ever talking to the Scheduler or Agent process directly, and
  what lets a freshly started Scheduler instance resume work an earlier,
  crashed instance had in flight.

The worked example on the Microsoft Learn page names the concrete fields a
real state store record carries for an order-processing task. `OrderID`,
`LockedBy` (the identifier of the Scheduler instance currently owning the
step, so two Scheduler instances cannot race on the same order), `CompleteBy`,
`ProcessState` (one of Pending, Processing, Processed, or Error), and
`FailureCount` (Microsoft Learn, same page, section "Example," verified
2026-08-02). This entry's code samples use the same five fields under
slightly shortened names.

## 6. ASCII structure diagram

```
                         +-------------------+
                         |    Application     |
                         |  (submits a task)  |
                         +---------+----------+
                                   |
                                   v
+----------------+       +--------+---------+       +------------------+
|                |<----->|                  |<----->|                  |
|   Supervisor   |       |    Scheduler     |       |      Agent       |
|                |       |                  |       |  (one per remote |
| periodic sweep |       | owns workflow    |       |   service type)  |
| for timed out  |       | order and step   |       |                  |
| or failed steps|       | sequencing       |       | wraps one remote |
+-------+--------+       +--------+---------+       |  call, enforces  |
        |                         |                 |  complete-by     |
        |    read / write         |  read / write   +--------+---------+
        |    step state           |  step state              |
        v                         v                           v
+-----------------------------------------------------------------+
|                                                                    |
|                          State store (durable)                    |
|  OrderID | LockedBy | CompleteBy | ProcessState | FailureCount   |
|                                                                    |
+-----------------------------------------------------------------+
                                                            |
                                                            v
                                              +---------------------------+
                                              |     Remote service or     |
                                              |     resource (per Agent)  |
                                              +---------------------------+
```

## 7. Dynamics

This dimension follows the request/response messaging shape the Azure catalog
describes, condensed into the three timelines that actually occur in
production. The fast path, the timeout-and-retry path, and the exhausted-
retries path that hands off to a compensating action.

**Fast path, one step, no failure.** The application submits a task. The
Scheduler writes a Pending record for the task and its first step to the
state store, then transitions the step to Processing, sets a complete-by
deadline, and sends a request message to the appropriate Agent, including the
step's data and the deadline. The Agent performs the remote call, receives a
response before the deadline, and sends a response message back to the
Scheduler. The Scheduler updates the state store to Processed and, if more
steps remain, repeats the cycle for the next step. Otherwise the task is done.

**Timeout, retry, eventual success.** The Scheduler dispatches a step exactly
as above, but the Agent's remote call is slow, or the Agent process itself
dies mid-call. No response arrives before the complete-by deadline. The
Scheduler does nothing special at this point. It simply has not heard back.
Independently, the Supervisor's next sweep examines the state store, finds
the step still marked Processing with an expired complete-by time, increments
the step's failure count, and, because the count is below the retry
threshold, resets the step to Pending and clears its lock. On its next pass
over pending work, the Scheduler picks the step back up as a fresh attempt,
assigns it a new complete-by deadline, and dispatches it again, this time to
a healthy instance of the Agent, which completes it successfully and reports
back. If the original, abandoned Agent call eventually does complete and
tries to report in after the deadline has passed and a newer attempt is
already in flight, that report is discarded, per the "Agent must stay silent
past its deadline" contract from dimension 5, or, in implementations where
the underlying remote call cannot be recalled, the report is accepted at the
transport layer but produces no state change because a fresher attempt has
already superseded it.

**Retries exhausted, compensation.** The same timeout sequence as above
repeats, but this time the failure count crosses the configured threshold
before a successful response ever arrives. The Supervisor, instead of
resetting the step to Pending, marks it (and the enclosing task) as Error and
raises that fact, either to an operator or by invoking the compensating
action that undoes whatever earlier steps in the same task already succeeded.
The Azure catalog frames this explicitly as a hand-off to the Compensating
Transaction pattern. The Supervisor "can send a message to the Scheduler to
request the entire task be undone by implementing a Compensating Transaction
pattern," which "will depend on the Scheduler and Agents providing the
information necessary to implement the compensating operations for each step
that completed successfully" (Microsoft Learn, "Scheduler Agent Supervisor
pattern," section "Solution," verified 2026-08-02).

```
 Application     Scheduler          State store         Agent           Supervisor
      |               |                   |                |                |
      | submit task   |                   |                |                |
      |-------------->|                   |                |                |
      |               | write Pending     |                |                |
      |               |------------------>|                |                |
      |               | dispatch step,    |                |                |
      |               | set Processing,   |                |                |
      |               | completeBy=T+5    |                |                |
      |               |------------------>|                |                |
      |               |------------------------------------->|                |
      |               |                   |    (call hangs, no reply by T+5) |
      |               |                   |                |                |
      |               |                   |     sweep at T+6, sees expired   |
      |               |                   |<----------------------------------|
      |               |                   |   failureCount++, reset Pending  |
      |               |                   |----------------------------------->|
      |               | poll Pending,     |                |                |
      |               | redispatch,       |                |                |
      |               | completeBy=T+11   |                |                |
      |               |------------------>|                |                |
      |               |------------------------------------->|                |
      |               |                   |    reply arrives before T+11    |
      |               |<-------------------------------------|                |
      |               | write Processed   |                |                |
      |               |------------------>|                |                |
      | task done     |                   |                |                |
      |<--------------|                   |                |                |
```

## 8. Implementation variants

This dimension mixes sourced claims about named systems with judgement about
how the pattern's three roles map onto today's platforms. The labels are
consistent with dimension 9 below, where each claim is sourced individually.

**Queue-mediated messaging, the pattern's own default shape.** The original
worked example uses a pair of message queues as the request/response channel
between the Scheduler and an Agent, specifically Azure Service Bus queues in
the reference implementation (Microsoft Learn, "Scheduler Agent Supervisor
pattern," section "Example," verified 2026-08-02). This is the most literal
implementation. The Scheduler is a background worker polling the state store
for pending work and posting request messages, each Agent is a separate
background worker polling its own request queue and posting reply messages,
and the Supervisor is a third background worker on a timer. Any durable
queue, from a cloud-managed broker to a self-hosted one, fills the same role,
and the state store can be any store that supports an atomic
compare-and-set or conditional update on the `LockedBy` and `ProcessState`
fields, so two Scheduler instances never both claim the same pending step.

**Managed workflow-as-state-machine services.** AWS Step Functions
externalizes the Scheduler's job into a declarative state machine definition
that AWS itself executes and persists. A `Task` state in a Step Functions
workflow "represents a unit of work that another AWS service performs, such
as calling another AWS service or API," which is the Agent's job expressed as
configuration rather than code, and the service's own `Retry` and `Catch`
fields on each state implement the Supervisor's timeout-and-recovery
responsibility natively. A workflow author can "retry failed tasks, or catch
failed tasks and automatically run alternative steps" (AWS documentation,
"What is Step Functions?" and "Handling errors in Step Functions workflows,"
https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machines.html,
verified 2026-08-02). The state store in this variant is Step Functions'
own execution history, which the service exposes for the "Standard" workflow
type as a full, inspectable audit trail. The trade this variant makes is
giving up direct control over the Scheduler's and Supervisor's internals in
exchange for not having to build or operate them.

**Durable execution frameworks.** Temporal reframes the same three roles
around a single programming model. A Workflow function plays the Scheduler's
role, deciding sequencing, and an Activity function plays the Agent's role,
performing the actual call to an external system. Temporal's own
documentation is explicit that "Activities serve as the units that interact
with external systems" including "API calls, Database queries," while the
Workflow layer "remains deterministic and recoverable through event replay,"
meaning the platform reconstructs the exact prior state of an in-flight
Workflow by replaying its recorded event history rather than by the
application reading rows out of a hand-built state store (Temporal
documentation, "Workflows,"
https://docs.temporal.io/workflows, verified 2026-08-02). The Supervisor's
timeout-and-retry sweep is built into the platform as Activity timeout and
retry policy configuration rather than a separately written watchdog process.
This is the pattern with its state store, retry sweep, and Scheduler-Agent
message plumbing collapsed into a managed runtime, at the cost of adopting
that runtime's programming model and its requirement that Workflow code stay
deterministic.

**Control loops as a continuous Supervisor.** Kubernetes' controller pattern
is a close relative rather than a literal implementation, and the difference
is instructive. A Kubernetes controller is "a non-terminating loop that
regulates the state of a system," continuously comparing a resource's desired
`spec` against its observed status and issuing corrective API calls
(Kubernetes documentation, "Controllers,"
https://kubernetes.io/docs/concepts/architecture/controller/, verified
2026-08-02). This fuses the Scheduler's sequencing role and the Supervisor's
recovery role into one continuously running reconciliation loop rather than
keeping them as two separately scheduled components, because a Kubernetes
controller's "steps" are not an ordered pipeline but a single idempotent
reconcile function re-run on every change and on a timer regardless of
outcome. A team building a small number of long-running, self-healing
resources, rather than many independent, transactional multi-step tasks, may
find a continuous reconcile loop simpler to reason about than a separate
Scheduler and Supervisor, at the cost of losing the explicit, inspectable
step-by-step progress record that a dedicated state store gives a
Scheduler-Agent-Supervisor implementation.

**Multi-agent AI orchestration, a live 2026 direction.** The pattern's
three-role shape is now explicitly cited as a foundation for coordinating
autonomous AI agents rather than only deterministic remote calls. Microsoft's
own AI agent orchestration guidance states that "traditional patterns like
Scheduler Agent Supervisor or Choreography provide foundational concepts" for
multi-agent systems, while noting that AI agents add "nondeterministic
outputs, dynamic reasoning capabilities, and the need for intelligent
handoffs" the classic pattern was not built to handle (Microsoft Learn, "AI
agent orchestration patterns,"
https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns,
verified 2026-08-02). The same page documents a "magentic orchestration"
variant in which a manager agent plays a Scheduler-like role by building and
revising a task ledger, worker agents play an Agent-like role by calling
tools against external systems, and the manager evaluates goal completion
in a loop resembling the Supervisor's sweep, driven by model judgement
rather than a fixed timeout. The guidance recommends that "the orchestrator
or the receiving agent should check output quality and either retry, request
clarification, or halt the workflow" before one agent's output reaches
another (same page, section on multi-agent resiliency, verified 2026-08-02),
a distinction from the classic pattern's timeout-only detection, discussed
further in dimensions 11 and 17.

**Language-idiomatic shapes.** In languages with strong async runtimes, the
Agent is naturally an async task or actor rather than a separately deployed
process, and the request or response channel between Scheduler and Agent can
be an in-process channel (Go's `chan`, an actor mailbox) instead of a network
queue, provided the two still cross a process or restart boundary at the
state store, which is what actually gives the pattern its crash-
recoverability. Collapsing Scheduler and Agent into one process with no
durable state store between them quietly discards that guarantee, a misuse
discussed in dimension 11.

## 9. Known production uses

**Microsoft's own reference implementation, Azure Service Bus-backed order
processing.** The Azure Architecture Center's worked example describes an
ecommerce system in which a web frontend posts a new order to a queue, a
Scheduler worker picks it up and drives the workflow, communicating with an
Agent through a pair of Service Bus request and reply queues, while a
separate Supervisor worker periodically scans the state store for orders
whose complete-by time has expired. The state record fields, `OrderID`,
`LockedBy`, `CompleteBy`, `ProcessState`, `FailureCount`, are given by name
(Microsoft Learn, "Scheduler Agent Supervisor pattern," section "Example,"
verified 2026-08-02).

**AWS Step Functions.** Step Functions state machines implement the
Scheduler and Supervisor roles as a managed service. A `Task` state
represents one unit of work delegated to another AWS service or to a worker
polling an Activity task, functioning as the Agent, and the state machine's
declarative `Retry` and `Catch` fields implement automatic recovery from a
failed or timed-out task with no hand-written watchdog. Amazon documents
Standard workflows as offering "exactly-once workflow execution" with
persisted execution history for up to one year of a running workflow (AWS
documentation, "What is Step Functions?",
https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machines.html,
verified 2026-08-02).

**Temporal, and its predecessor Uber Cadence.** Temporal's programming model
maps Workflow code to the Scheduler role and Activity code to the Agent role,
with the platform's own server persisting a durable Event History that lets a
failed or paused Workflow resume "right where it left off" through
deterministic replay, and enforcing Activity-level timeout and retry policy
in place of a hand-written Supervisor sweep (Temporal documentation,
"Workflows," https://docs.temporal.io/workflows, verified 2026-08-02).
Temporal is an open source continuation of the same durable-execution
architecture originated at Uber as Cadence, and both are widely used for
exactly the class of problem this pattern names. Multi-step operations that
call external services and must survive process failure.

**Kubernetes controllers, including the built-in Job controller.** Every
built-in controller, and every custom controller written against the
`controller-runtime` library, implements a continuous variant of the
Scheduler and Supervisor roles fused into one reconciliation loop, which
"watches the state of your cluster, then makes or requests changes where
needed," with the Job controller specifically watching for a Job's Pods to
complete and recreating them when they fail (Kubernetes documentation,
"Controllers,"
https://kubernetes.io/docs/concepts/architecture/controller/, verified
2026-08-02).

**Multi-agent AI orchestration platforms, current generation.** Microsoft's
own Agent Framework documents named orchestration variants, sequential,
concurrent, group chat, handoff, and magentic, built specifically for
coordinating multiple AI agents, and explicitly positions this family as
descending from "traditional patterns like Scheduler Agent Supervisor"
extended to handle agents whose outputs are nondeterministic rather than
strictly retryable (Microsoft Learn, "AI agent orchestration patterns,"
https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns,
verified 2026-08-02). This is a live, actively documented production
direction as of 2026 rather than a historical curiosity, and it is the
clearest evidence that the three-role separation this pattern names has
outlived its original Azure Service Bus reference implementation.

## 10. Consequences

**Positive.**

- Survives the failure of the orchestrating process. Because progress lives
  in a durable state store rather than in the memory or local disk of one
  running instance, a crashed Scheduler can be replaced by a fresh instance
  that resumes exactly where the record says the task stood.
- Recovers from transient and even fairly long remote outages without a human
  in the loop, because the Supervisor's retry mechanism runs independently
  of, and is not blocked by, the failure it is recovering from.
- Gives an operator a durable, queryable audit trail of every in-flight and
  completed task, since the state store's job is precisely to answer "where
  is this task right now" and "how many times has it failed," which a
  synchronous call chain cannot answer once the calling stack frame is gone.
- Cleanly separates three concerns that a monolithic pipeline function
  otherwise tangles together. What order steps run in, how to talk to one
  specific remote system, and how to notice when something has gone
  quiet. Each can be tested, deployed, and reasoned about independently.
- Scales the Agent role horizontally and independently of the Scheduler,
  since any healthy Agent instance can pick up any dispatched step. A slow
  or unhealthy remote system can be isolated to its own Agent pool without
  affecting the Scheduler or other Agents.

**Negative.**

- Introduces real implementation and operational cost. A durable state
  store, at least one message channel, and a separately scheduled Supervisor
  process, none of which a simple sequential function needs.
- Pushes the burden of idempotency onto every Agent and every remote system
  it wraps, and if that burden cannot be met the pattern's own recovery
  mechanism becomes a source of duplicated side effects rather than a cure
  for failure, as detailed in dimension 11.
- Adds latency to the legitimate failure case, because a genuine failure is
  only detected once the complete-by deadline has elapsed and the next
  Supervisor sweep has run, which is by design measured in seconds to
  minutes rather than milliseconds.
- The recovery logic itself is nontrivial and needs its own testing.
  Choosing retry thresholds, sweep intervals, and compensation triggers is a
  design exercise with real failure modes of its own, not a solved problem
  that ships for free with the pattern's name.
- Concentrates a form of coordination risk in the state store and in
  correct handling of the `LockedBy` field. A bug that lets two Scheduler
  instances both claim the same pending step reintroduces exactly the race
  condition the pattern exists to prevent.

## 11. Failure modes and misuse

The pairs below are drawn from operating this pattern and are engineering
judgement about what a reader observes, with the underlying mechanism sourced
where a source exists.

**Duplicate charge on a retried payment step.**
*Symptom.* The same order gets charged twice at the payment provider.
*Cause.* The remote payment call is not idempotent, or the Agent passes a
freshly generated request identifier on every retry instead of a stable one
tied to the step, so the payment provider has no way to recognize a retried
attempt as a duplicate of an earlier one.
*Fix.* Pass one stable identifier for the life of the step across every retry
attempt, and require the remote system's own API to support deduplication on
that identifier. The Azure catalog states this requirement directly, advising
that Agents "pass a stable identifier across all retry attempts so that the
remote service can use it for any deduplication logic that it might have"
(Microsoft Learn, "Scheduler Agent Supervisor pattern," section "Solution,"
verified 2026-08-02).

**A task appears permanently stuck in Processing.**
*Symptom.* A task appears permanently stuck in the running state, and the
Supervisor never seems to touch it.
*Cause.* The Supervisor's sweep interval is longer than the complete-by
window, or the Supervisor process itself has died and nothing is restarting
it, which is easy to miss because a stalled Supervisor produces silence
rather than an error.
*Fix.* Monitor the Supervisor's own liveness and last-sweep timestamp as a
first-class metric, not only the tasks it watches, and set the sweep
interval to a fraction of the shortest complete-by deadline in the system so
that no step can wait more than one sweep past its own deadline.

**Two Scheduler instances race on the same order.**
*Symptom.* Two instances of the Scheduler both claim and process the same
pending step, and the state store shows contradictory updates.
*Cause.* The claim operation that sets `LockedBy` and moves a step from
Pending to Processing is implemented as a read followed by a separate write
rather than as one atomic conditional update, so two Scheduler instances can
both read the same Pending record before either one writes its lock.
*Fix.* Use a compare-and-set or conditional write primitive native to the
state store (an optimistic concurrency token, a conditional `UPDATE ... WHERE
state = 'Pending'`, or an equivalent), so exactly one of the two racing
writers succeeds and the other observes a write conflict and simply moves on.

**Runaway retries against a permanently broken dependency.**
*Symptom.* Retries never stop, and a permanently broken downstream dependency
keeps a failing task cycling through Pending and Processing forever.
*Cause.* No failure-count threshold, or a threshold that is never actually
checked because the code path that increments `FailureCount` is separate
from the code path that compares it against the limit, and a bug decouples
the two.
*Fix.* Make the threshold check and the increment one atomic unit of work in
the Supervisor's sweep, and add an explicit test that asserts a task reaches
the Error state, and stays there, once its failure count exceeds the
configured limit. This is exactly the scenario this entry's own code samples
exercise for `order-3`.

**A late reply from an abandoned attempt corrupts state.**
*Symptom.* An abandoned Agent call eventually does complete, long after the
Scheduler gave up on it, and its late report corrupts the state of a task
that has already moved on to a fresh attempt or has already been marked
Error.
*Cause.* The Agent, or the transport carrying its reply, does not honor the
"stay silent past the deadline" contract, so a late reply is delivered and
naively applied by the Scheduler regardless of whether the step it refers to
is still the current attempt.
*Fix.* Have the Scheduler check that an incoming reply's attempt identifier
matches the state store's current attempt for that step, and discard any
reply that does not match, rather than trusting that a late reply simply
will not arrive. This defensive check is required precisely because, as this
entry's code samples demonstrate, the underlying remote effect can still
land even after the coordinator has moved on.

**The pattern in name only, with no durable state store.**
*Symptom.* The whole system, including the Scheduler and every Agent, is
fused into one deployable, and a single process crash loses every in-flight
task with no way to recover them.
*Cause.* The three roles were implemented as function calls within one
process and the "durable state store" is an in-memory dictionary, which
satisfies none of the pattern's actual guarantee and is, in effect, the
original naive sequential pipeline with extra ceremony.
*Fix.* This is not a bug to patch but a sign the pattern was adopted without
its load-bearing element, the durable, external state store. Either add a
genuinely durable store or, if the extra machinery genuinely is not needed,
remove it and go back to a plain sequential function guarded by the Retry
pattern.

**Silent propagation of a low-quality agent response, multi-agent variant.**
*Symptom.* One agent's low-quality or hallucinated output is silently passed
to the next agent and the compounded error surfaces several steps later, far
from its root cause.
*Cause.* The orchestrator treats every agent response as equivalent to a
successful Agent reply in the classic pattern, when in fact an AI agent can
return a confidently wrong result that is neither a timeout nor a
transport-level error and so trips none of the classic Supervisor's
detection logic.
*Fix.* Validate agent output quality before it is handed to the next agent
or to an external system, and treat a low-confidence or off-topic response
as a distinct failure class with its own retry, escalate, or halt path,
which is the explicit guidance Microsoft gives for multi-agent resiliency
(Microsoft Learn, "AI agent orchestration patterns," section on resiliency,
verified 2026-08-02).

## 12. Trade-off matrix

The comparison below weighs Scheduler Agent Supervisor against four named
alternatives that address overlapping parts of the same problem. Sequencing
distributed work with a durable recovery story.

| Force | Scheduler Agent Supervisor | Choreography | Saga (orchestrated) | Two-Phase Commit | Bare Retry with backoff |
|---|---|---|---|---|---|
| Cross-service atomicity | None, relies on idempotency and compensation | None, each service reacts to events independently | None, same compensation-based model, narrower scope than SAS | Strong, all-or-nothing, if every participant is XA-capable | None, retries one call, no cross-step story |
| Central point of coordination | Yes, the Scheduler, plus a separate watchdog role | No, coordination emerges from event subscriptions | Yes, a saga orchestrator, structurally close to a Scheduler | Yes, a transaction coordinator | No coordination, single call site |
| Crash recoverability of in-flight work | Durable by design, the whole point of the state store | Depends entirely on each service's own durability | Durable if the orchestrator persists saga state | Durable if the coordinator's log survives | None beyond the caller's own retry loop |
| Operational visibility into progress | High, state store is directly queryable per step | Low, progress is implicit across many event logs | High, comparable to SAS | Medium, transaction log exists but is coordinator-internal | Low, no persisted step-by-step record |
| Coupling between components | Low coupling of business logic to remote calls, moderate coupling to a shared workflow definition | Lowest, services know only the events they emit and consume | Moderate, steps must know their own compensating action | High, every participant must speak the transaction protocol | None beyond the one call |
| Best fit | Multi-step tasks against remote resources with a background-job execution model | Loosely coupled domains where no single team owns the whole flow | Business transactions with a clear compensation story per step | Small, tightly controlled systems all sharing a resource manager | A single flaky call with no multi-step sequencing to track |
| Detection of a stuck step | A dedicated Supervisor sweep against a complete-by deadline | No built-in detection, a stalled consumer is invisible until observed downstream | Usually folded into the orchestrator itself, no separate Supervisor role named | Coordinator-level timeout, blocks participants while waiting | Bounded by the retry policy's own attempt count, not a shared deadline |

## 13. Related and incompatible patterns

**Compensating Transaction.** The Supervisor's exhausted-retries path names
this pattern directly as its own recovery mechanism once a step cannot
succeed after the configured number of attempts. The Azure catalog's own
"Solution" section describes the Supervisor sending "a message to the
Scheduler to request the entire task be undone by implementing a
Compensating Transaction pattern" (Microsoft Learn, "Scheduler Agent
Supervisor pattern," verified 2026-08-02). Scheduler Agent Supervisor
supplies the detection and sequencing machinery. Compensating Transaction
supplies the actual undo logic per step.

**Saga.** A Saga is the business-transaction framing of largely the same
mechanics. A sequence of local transactions across services, each with a
paired compensating action, coordinated either by choreography or by a
central orchestrator. An orchestrated Saga's coordinator plays a role close
to this pattern's Scheduler, and the two are frequently implemented on the
same underlying durable-workflow platform. The difference is emphasis rather
than mechanism, Saga foregrounds the compensation contract per step, while
Scheduler Agent Supervisor foregrounds the timeout-detection and retry
machinery that decides when compensation is even triggered.

**Retry.** This pattern deliberately nests inside Scheduler Agent Supervisor
twice, once locally inside each Agent for the specific remote call it wraps,
and once at the whole-step level, implemented by the Supervisor resetting a
timed-out step back to Pending for a fresh Scheduler dispatch. A team that
finds it only ever needs the local, single-call version, with no durable
state store and no separate watchdog process, has outgrown the need for this
pattern's other two roles and should reach for Retry alone.

**Circuit Breaker.** An Agent that keeps calling a remote system which is
clearly down, rather than failing fast, wastes the complete-by window on
every single attempt. Wrapping the Agent's own remote call in a Circuit
Breaker lets it fail immediately once the breaker is open, so the Supervisor
learns about the outage sooner and the retry cycle does not waste its full
timeout budget on a call that was never going to succeed.

**Leader Election.** The Azure catalog notes directly that when a system runs
multiple concurrent Supervisor instances for redundancy, they "must coordinate
their work with each other carefully" so they never both attempt to recover
the same failed step at once, and names Leader Election as "one possible
solution to this problem" (Microsoft Learn, "Scheduler Agent Supervisor
pattern," verified 2026-08-02).

**Competing Consumers.** When the Scheduler-to-Agent channel is a queue, a
pool of Agent instances reading from that queue is a direct application of
Competing Consumers. Any healthy Agent instance may pick up any dispatched
step, which is exactly what lets the Agent role scale horizontally,
independent of the Scheduler, as noted under Consequences.

**Choreography, and why it is not incompatible but is a genuine alternative.**
Choreography solves an overlapping problem, coordinating distributed steps,
by removing the central Scheduler entirely and letting each service react to
events it observes. Microsoft's own catalog page lists Scheduler Agent
Supervisor and Choreography side by side as two "traditional patterns" that
"provide foundational concepts" for coordination, without treating them as
mutually exclusive within one organization. A system may reasonably use
Choreography for loosely coupled domain events and this pattern for a
tightly sequenced, must-complete-or-compensate task within one bounded
context.

**Two-Phase Commit, listed as incompatible.** Two-Phase Commit assumes a
transaction coordinator can hold every participant blocked until all agree
to commit or all agree to abort, a strong, synchronous, all-or-nothing
guarantee. Scheduler Agent Supervisor is built for exactly the situation
where that guarantee is unavailable, remote resources outside the
application's control, so combining the two within a single operation is a
contradiction in design intent rather than a genuine composition. A step
under this pattern that internally uses Two-Phase Commit against resources
it owns is fine, but the pattern's own cross-step coordination should never
be replaced with an attempt at a distributed two-phase commit across the
whole task.

## 14. Refactoring path in and out

**Introducing the pattern into code that does not have it.** Start from the
common shape, a single function that runs several remote calls in sequence
inside one try or catch block, with no persisted record of progress. Move
in four independently shippable steps.

First, name every sequential call as a distinct step and extract each into
its own function with a stable, explicit input and output shape, making the
eventual Agent boundary visible before anything about persistence changes.
Second, introduce the state store and write, but do not yet act on, a
record per task and step at each transition the original function already
makes; this is safe to ship alone and lets the team validate the schema and
locking discipline under real traffic before it becomes load-bearing.
Third, replace the direct in-process calls to each step function with a
dispatch through a queue or channel to a separate Agent process, which
reports completion by updating the state store rather than returning a
value up a call stack; this is the step that buys crash-recoverability,
since it moves execution outside the lifetime of the original request.
Fourth, add the Supervisor as a separately scheduled process that only
reads the state store and only acts by resetting expired steps to Pending
or triggering the compensating path once retries are exhausted; because it
never talks to a remote system directly, it can be introduced and
load-tested with no risk to the systems the Agents already talk to.

**Removing the pattern once it stops earning its place.** The signal this
pattern has outlived its usefulness for a given task is not "the code looks
complicated," a permanent property of the pattern, but "the task no longer
meaningfully fails independent of the calling process," for example because
every step was consolidated behind one transactional API the team now owns.
Removing the pattern mirrors introducing it in reverse. First confirm the
Supervisor has not triggered a retry or a compensating action in a
meaningful monitoring window, since regular firing is strong evidence the
instability that justified the pattern has not gone away. Second, inline
the Agent's remote call back into the Scheduler's own process, keeping the
state store writes for one further deployment cycle as a safety net.
Third, once the simplified path performs at parity, collapse the state
store writes into ordinary logging and delete the Supervisor process last,
since it is the cheapest component to keep running as a backstop and the
most expensive one to reintroduce in a hurry if the removal was premature.

## 15. Testing and verification

The pattern's three-role separation is, on its own, a gift to testability.
Each role can be tested against a mocked state store and a mocked partner
role, without ever standing up a real remote dependency, which is exactly
the property this entry's own code samples exploit by replacing wall-clock
time with an explicit tick counter passed into every function.

**Testing the Scheduler in isolation.** Feed it a state store with hand-
crafted records in every reachable `ProcessState` and assert it dispatches
exactly the Pending steps, sets the expected complete-by deadline, and
leaves Processing, Processed, and Error records untouched. A Scheduler that
touches a record it should not have is the most common Scheduler bug and is
trivial to catch this way.

**Testing the Agent in isolation.** Assert that a reply arriving before the
step's complete-by deadline, for the step's current attempt, results in a
report back to the Scheduler, and that a reply arriving after the deadline,
or tagged with a stale attempt identifier, results in no report at all.
Separately, and this is the check teams skip most often, assert that calling
the Agent's underlying remote-call wrapper twice with the same idempotency
key produces the side effect exactly once. This is a property test in the
sense used by this repository's own testing standards, because it should
hold for every possible pair of call orderings and timings, not only for the
one example a developer happened to write down.

**Testing the Supervisor in isolation.** Seed the state store with a
Processing record whose complete-by time is already in the past relative to
the sweep's clock and assert the failure count increments and the record
either returns to Pending, below the threshold, or moves to Error, at or
above it. Then assert the inverse, a Processing record whose deadline has
not yet passed is left completely untouched by a sweep, which catches the
class of bug where a Supervisor is too aggressive and reclaims work that is
still legitimately in flight.

**Testing the whole assembly together.** Run the three roles against one
shared, in-memory but still externally observable state store, and drive
time forward explicitly rather than by sleeping in wall-clock time, exactly
as this entry's TypeScript, Python, and Go samples do with a manually
incremented tick counter. This keeps the test deterministic and fast while
still exercising the real coordination logic between all three roles,
including the specific, easy-to-miss case where an abandoned attempt's
underlying effect lands after a fresher attempt has already succeeded.
Chaos-style fault injection, killing the Scheduler process mid-task and
confirming a fresh instance resumes correctly from the state store, is the
strongest end-to-end proof this pattern's core guarantee actually holds,
and it should be part of any pre-production checklist for a system relying
on it.

**What becomes harder to test.** End-to-end tests now have to treat the
Supervisor's sweep interval as real latency in the test's own timeline,
which pushes teams toward the tick-based determinism above or toward a
deliberately short sweep interval in the test environment; a suite that
waits on the production interval to observe recovery is correct but slow.

## 16. Observability signals

A healthy instance of this pattern, viewed on a dashboard, shows a state
store where the overwhelming majority of records sit briefly in Pending,
move quickly through Processing, and land in Processed, with a small,
roughly constant trickle of Supervisor-triggered retries that themselves
resolve to Processed shortly after. The signals worth alerting on, rather
than merely graphing, are the ones that distinguish that healthy trickle
from an actual incident.

- **Age of the oldest non-terminal step.** The single most direct measure of
  "is anything actually stuck." A step whose age exceeds several multiples of
  its own complete-by window and has not yet been touched by a Supervisor
  sweep points at a dead or misconfigured Supervisor, not at a slow remote
  call, since the Supervisor's job is precisely to bound this age.
- **Supervisor sweep count and duration.** A steady heartbeat metric per
  sweep, incrementing on every run regardless of whether it found anything to
  recover, is what distinguishes "the Supervisor is alive and found nothing
  wrong" from "the Supervisor is dead and nothing is watching." A sweep
  duration climbing over time against a fixed sweep interval predicts the
  Supervisor will eventually fall behind before it visibly does.
- **Retry rate per Agent.** Graphed per remote system rather than in
  aggregate, this is the earliest warning of a specific downstream
  dependency degrading, well before that dependency's own health checks
  might trip, because the retry rate reflects real production traffic
  hitting real timeouts rather than a synthetic probe.
- **Distinct failure-count distribution at Error time.** If most tasks that
  reach Error do so at exactly the configured threshold, the threshold is
  doing its job as a deliberate cutoff. If a meaningful share reach Error
  after only one attempt, either the complete-by deadline is set too short
  for that step's real latency, or a whole class of failure is genuinely
  non-transient and retrying it at all is wasted effort.
- **Compensating-action trigger rate and outcome.** Every time the
  Supervisor hands a task to a compensating action, that hand-off, and
  whether the compensation itself succeeded, deserves its own logged event
  and metric, because a failed compensation leaves the system in the exact
  inconsistent state this whole pattern exists to prevent, and that failure
  will not show up in any of the metrics above.
- **Duplicate-effect counter at the idempotency boundary.** The Agent's
  remote-call wrapper is the one place in the system positioned to observe
  a retried attempt land a second time against an already-applied
  idempotency key. Logging that event, even though the correct behavior is
  to silently no-op it, gives an operator direct, positive confirmation that
  the idempotency contract is holding under real retries rather than only
  under test.

## 17. Security and privacy implications

The state store is the pattern's most exposed surface, because by design it
holds a durable, queryable record of every task the system has run through
it, including whatever business data was attached to each step, an order
identifier, a customer reference, a payment reference. Access control on the
state store deserves the same scrutiny as access control on the underlying
business data itself, and a store retained indefinitely "for debugging" can
quietly become an unmanaged copy of sensitive data outside the retention and
access policy that governs the system of record. Where the tasks touch
personal data, the store's retention period should be an explicit decision,
not an accident of years of unmanaged growth.

The `LockedBy` field and any Scheduler or Supervisor instance identifiers
written into the state store are operational metadata rather than business
data, but they still reveal internal topology, which host or worker claimed
a given task, and that should not be exposed through an externally facing
status API to a caller who only needs to know whether their task succeeded.

The idempotency key passed on every retry, discussed in dimensions 5 and 11,
is frequently tied to a business identifier such as an order number, and
because it is designed to be logged and stored by the remote system on the
other end of the call, it should never itself be, or be reversibly derived
from, a secret or sensitive personal data. It needs only to be stable and
unique per step.

Compensating actions, discussed in dimension 13, deserve their own security
review, because an undo operation frequently needs broader privilege than
the original action, a refund capability where the original call only
needed a charge capability, for example, and a Supervisor that can trigger
compensation is, by extension, a component able to trigger those
broader-privileged actions. Its credentials and the audit trail of when and
why it triggered a compensation belong under the same access-control and
logging discipline as the systems the compensation reaches into, not under
a lighter, it is merely a watchdog, assumption.

Finally, in the multi-agent AI orchestration variant discussed in
dimensions 8 and 11, an agent's output is untrusted input to whatever agent
receives it next, in the same sense any externally sourced text is
untrusted. A manager agent that passes one agent's raw output directly into
another agent's tool call, without the validation step Microsoft's own
guidance recommends, opens a path for a prompt-injection-style attack to
ride along inside ordinary inter-agent coordination traffic, a risk that
did not exist in the classic, purely deterministic version of this pattern.

## 18. References

- Microsoft Learn, Azure Architecture Center, "Scheduler Agent Supervisor
  pattern," https://learn.microsoft.com/en-us/azure/architecture/patterns/scheduler-agent-supervisor,
  content last updated 2025-12-09, verified 2026-08-02.
- Microsoft Learn, Azure Architecture Center, "Cloud Design Patterns,"
  index page listing all catalog entries, https://learn.microsoft.com/en-us/azure/architecture/patterns/,
  content last updated 2026-07-02, verified 2026-08-02.
- Alex Homer, John Sharp, Larry Brader, Masashi Narumoto, Trent Swanson,
  *Cloud Design Patterns. Prescriptive Architecture Guidance for Cloud
  Applications*, Microsoft patterns and practices, 2014. Origin of the
  named catalog entry, now maintained on Microsoft Learn as cited above.
- Gregor Hohpe, Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, ISBN
  0-321-20068-3. Source of the related Process Manager pattern.
- Enterprise Integration Patterns companion site, "Process Manager,"
  https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html,
  verified 2026-08-02.
- Amazon Web Services documentation, "What is Step Functions?",
  https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machines.html,
  verified 2026-08-02.
- Temporal Technologies documentation, "Workflows,"
  https://docs.temporal.io/workflows, verified 2026-08-02.
- The Kubernetes Authors, Kubernetes documentation, "Controllers,"
  https://kubernetes.io/docs/concepts/architecture/controller/, verified
  2026-08-02.
- Microsoft Learn, Azure Architecture Center, "AI Agent Orchestration
  Patterns," https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns,
  content last updated 2026-05-12, verified 2026-08-02.

## Code examples

The three implementations below share one deterministic scenario, driven by
an explicit tick counter rather than by wall-clock time, so the same output
is reproducible on every run and in every language. Three orders are
submitted at tick zero. `order-1`'s remote call answers quickly and
succeeds on the first attempt. `order-2`'s first attempt hangs past its
complete-by deadline, the Supervisor times it out and requeues it, and the
second attempt succeeds, while the first attempt's underlying remote call
still eventually lands late and is correctly discarded because the
idempotency key it shares with the second attempt has already been applied.
`order-3`'s remote call hangs past its deadline on every attempt, so after
one retry it exceeds the configured failure threshold and is marked Error,
and its own late, abandoned attempt is likewise discarded on arrival. All
three languages produce byte-for-byte identical trace output, reproduced
once below the samples, because the scenario, the timeout, and the retry
threshold are the same numbers in every version.

```typescript
type ProcessState = "Pending" | "Processing" | "Processed" | "Error";

interface StepRecord {
  orderId: string;
  processState: ProcessState;
  lockedBy: string | null;
  completeBy: number;
  currentAttempt: number;
  failureCount: number;
}

interface AgentEvent {
  orderId: string;
  attempt: number;
  arrivalTick: number;
}

const STEP_TIMEOUT = 5;
const MAX_RETRIES = 1;

const delaySchedule: Record<string, number[]> = {
  "order-1": [1],
  "order-2": [10, 1],
  "order-3": [10, 10],
};

const store = new Map<string, StepRecord>();
const applied = new Set<string>();
const events: AgentEvent[] = [];

function submit(orderId: string): void {
  store.set(orderId, {
    orderId,
    processState: "Pending",
    lockedBy: null,
    completeBy: 0,
    currentAttempt: -1,
    failureCount: 0,
  });
}

function dispatchPendingSteps(tick: number): void {
  for (const record of store.values()) {
    if (record.processState !== "Pending") continue;
    record.currentAttempt += 1;
    record.lockedBy = "scheduler-1";
    record.completeBy = tick + STEP_TIMEOUT;
    record.processState = "Processing";
    const delays = delaySchedule[record.orderId];
    const delay = delays[Math.min(record.currentAttempt, delays.length - 1)];
    events.push({ orderId: record.orderId, attempt: record.currentAttempt, arrivalTick: tick + delay });
  }
}

// remoteServiceApply is the idempotency boundary every real Agent must offer.
function remoteServiceApply(idempotencyKey: string): boolean {
  if (applied.has(idempotencyKey)) return false;
  applied.add(idempotencyKey);
  return true;
}

function deliverAgentEvent(evt: AgentEvent, tick: number): void {
  const record = store.get(evt.orderId)!;
  const firstApply = remoteServiceApply(evt.orderId);
  const onTime =
    evt.attempt === record.currentAttempt &&
    record.processState === "Processing" &&
    tick <= record.completeBy;
  console.log(
    `tick=${tick} agent-response order=${evt.orderId} attempt=${evt.attempt} newEffect=${firstApply} onTime=${onTime}`
  );
  if (onTime) {
    record.processState = "Processed";
  }
}

function supervisorSweep(tick: number): void {
  for (const record of store.values()) {
    if (record.processState !== "Processing") continue;
    if (record.completeBy >= tick) continue;
    record.failureCount += 1;
    if (record.failureCount > MAX_RETRIES) {
      record.processState = "Error";
      console.log(`tick=${tick} supervisor order=${record.orderId} exceeded retries -> Error`);
    } else {
      record.processState = "Pending";
      record.lockedBy = null;
      console.log(
        `tick=${tick} supervisor order=${record.orderId} timed out, requeue attempt=${record.currentAttempt + 1}`
      );
    }
  }
}

function allTerminal(): boolean {
  for (const record of store.values()) {
    if (record.processState !== "Processed" && record.processState !== "Error") return false;
  }
  return true;
}

submit("order-1");
submit("order-2");
submit("order-3");
dispatchPendingSteps(0);

for (let tick = 1; tick <= 20; tick++) {
  const due = events.filter((e) => e.arrivalTick === tick);
  for (const evt of due) deliverAgentEvent(evt, tick);
  supervisorSweep(tick);
  dispatchPendingSteps(tick);
  if (allTerminal() && events.every((e) => e.arrivalTick <= tick)) break;
}

for (const record of store.values()) {
  console.log(
    `final order=${record.orderId} state=${record.processState} failureCount=${record.failureCount} attempts=${record.currentAttempt + 1}`
  );
}
```

```python
from dataclasses import dataclass

STEP_TIMEOUT = 5
MAX_RETRIES = 1

DELAY_SCHEDULE = {
    "order-1": [1],
    "order-2": [10, 1],
    "order-3": [10, 10],
}


@dataclass
class StepRecord:
    order_id: str
    process_state: str = "Pending"
    locked_by: str | None = None
    complete_by: int = 0
    current_attempt: int = -1
    failure_count: int = 0


@dataclass
class AgentEvent:
    order_id: str
    attempt: int
    arrival_tick: int


store: dict[str, StepRecord] = {}
applied: set[str] = set()
events: list[AgentEvent] = []


def submit(order_id: str) -> None:
    store[order_id] = StepRecord(order_id=order_id)


def dispatch_pending_steps(tick: int) -> None:
    for record in store.values():
        if record.process_state != "Pending":
            continue
        record.current_attempt += 1
        record.locked_by = "scheduler-1"
        record.complete_by = tick + STEP_TIMEOUT
        record.process_state = "Processing"
        delays = DELAY_SCHEDULE[record.order_id]
        delay = delays[min(record.current_attempt, len(delays) - 1)]
        events.append(AgentEvent(record.order_id, record.current_attempt, tick + delay))


# remote_service_apply is the idempotency boundary every real Agent must offer.
def remote_service_apply(idempotency_key: str) -> bool:
    if idempotency_key in applied:
        return False
    applied.add(idempotency_key)
    return True


def deliver_agent_event(evt: AgentEvent, tick: int) -> None:
    record = store[evt.order_id]
    first_apply = remote_service_apply(evt.order_id)
    on_time = (
        evt.attempt == record.current_attempt
        and record.process_state == "Processing"
        and tick <= record.complete_by
    )
    print(
        f"tick={tick} agent-response order={evt.order_id} attempt={evt.attempt} "
        f"newEffect={first_apply} onTime={on_time}"
    )
    if on_time:
        record.process_state = "Processed"


def supervisor_sweep(tick: int) -> None:
    for record in store.values():
        if record.process_state != "Processing":
            continue
        if record.complete_by >= tick:
            continue
        record.failure_count += 1
        if record.failure_count > MAX_RETRIES:
            record.process_state = "Error"
            print(f"tick={tick} supervisor order={record.order_id} exceeded retries -> Error")
        else:
            record.process_state = "Pending"
            record.locked_by = None
            print(
                f"tick={tick} supervisor order={record.order_id} timed out, "
                f"requeue attempt={record.current_attempt + 1}"
            )


def all_terminal() -> bool:
    return all(r.process_state in ("Processed", "Error") for r in store.values())


def main() -> None:
    for order_id in ("order-1", "order-2", "order-3"):
        submit(order_id)
    dispatch_pending_steps(0)

    for tick in range(1, 21):
        due = [e for e in events if e.arrival_tick == tick]
        for evt in due:
            deliver_agent_event(evt, tick)
        supervisor_sweep(tick)
        dispatch_pending_steps(tick)
        if all_terminal() and all(e.arrival_tick <= tick for e in events):
            break

    for record in store.values():
        print(
            f"final order={record.order_id} state={record.process_state} "
            f"failureCount={record.failure_count} attempts={record.current_attempt + 1}"
        )


if __name__ == "__main__":
    main()
```

```go
package main

import "fmt"

const stepTimeout = 5
const maxRetries = 1

type stepRecord struct {
	orderID        string
	processState   string
	lockedBy       string
	completeBy     int
	currentAttempt int
	failureCount   int
}

type agentEvent struct {
	orderID     string
	attempt     int
	arrivalTick int
}

var delaySchedule = map[string][]int{
	"order-1": {1},
	"order-2": {10, 1},
	"order-3": {10, 10},
}

var store = map[string]*stepRecord{}
var applied = map[string]bool{}
var events []agentEvent

func submit(orderID string) {
	store[orderID] = &stepRecord{orderID: orderID, processState: "Pending", currentAttempt: -1}
}

func dispatchPendingSteps(tick int) {
	for _, record := range store {
		if record.processState != "Pending" {
			continue
		}
		record.currentAttempt++
		record.lockedBy = "scheduler-1"
		record.completeBy = tick + stepTimeout
		record.processState = "Processing"
		delays := delaySchedule[record.orderID]
		idx := record.currentAttempt
		if idx > len(delays)-1 {
			idx = len(delays) - 1
		}
		events = append(events, agentEvent{record.orderID, record.currentAttempt, tick + delays[idx]})
	}
}

// remoteServiceApply is the idempotency boundary every real Agent must offer.
func remoteServiceApply(key string) bool {
	if applied[key] {
		return false
	}
	applied[key] = true
	return true
}

func deliverAgentEvent(evt agentEvent, tick int) {
	record := store[evt.orderID]
	firstApply := remoteServiceApply(evt.orderID)
	onTime := evt.attempt == record.currentAttempt && record.processState == "Processing" && tick <= record.completeBy
	fmt.Printf("tick=%d agent-response order=%s attempt=%d newEffect=%t onTime=%t\n", tick, evt.orderID, evt.attempt, firstApply, onTime)
	if onTime {
		record.processState = "Processed"
	}
}

func supervisorSweep(tick int) {
	for _, record := range store {
		if record.processState != "Processing" || record.completeBy >= tick {
			continue
		}
		record.failureCount++
		if record.failureCount > maxRetries {
			record.processState = "Error"
			fmt.Printf("tick=%d supervisor order=%s exceeded retries -> Error\n", tick, record.orderID)
		} else {
			record.processState = "Pending"
			record.lockedBy = ""
			fmt.Printf("tick=%d supervisor order=%s timed out, requeue attempt=%d\n", tick, record.orderID, record.currentAttempt+1)
		}
	}
}

func allTerminal() bool {
	for _, record := range store {
		if record.processState != "Processed" && record.processState != "Error" {
			return false
		}
	}
	return true
}

func main() {
	for _, id := range []string{"order-1", "order-2", "order-3"} {
		submit(id)
	}
	dispatchPendingSteps(0)

	for tick := 1; tick <= 20; tick++ {
		var due []agentEvent
		latest := 0
		for _, e := range events {
			if e.arrivalTick > latest {
				latest = e.arrivalTick
			}
			if e.arrivalTick == tick {
				due = append(due, e)
			}
		}
		for _, evt := range due {
			deliverAgentEvent(evt, tick)
		}
		supervisorSweep(tick)
		dispatchPendingSteps(tick)
		if allTerminal() && latest <= tick {
			break
		}
	}

	for _, id := range []string{"order-1", "order-2", "order-3"} {
		r := store[id]
		fmt.Printf("final order=%s state=%s failureCount=%d attempts=%d\n", r.orderID, r.processState, r.failureCount, r.currentAttempt+1)
	}
}
```

Compiled and run directly on this machine, `npx tsc` targeting ES2020 plus
`node`, `python3`, and `go run`, all three produce the identical trace.

```
tick=1 agent-response order=order-1 attempt=0 newEffect=true onTime=true
tick=6 supervisor order=order-2 timed out, requeue attempt=1
tick=6 supervisor order=order-3 timed out, requeue attempt=1
tick=7 agent-response order=order-2 attempt=1 newEffect=true onTime=true
tick=10 agent-response order=order-2 attempt=0 newEffect=false onTime=false
tick=10 agent-response order=order-3 attempt=0 newEffect=true onTime=false
tick=12 supervisor order=order-3 exceeded retries -> Error
tick=16 agent-response order=order-3 attempt=1 newEffect=false onTime=false
final order=order-1 state=Processed failureCount=0 attempts=1
final order=order-2 state=Processed failureCount=1 attempts=2
final order=order-3 state=Error failureCount=2 attempts=2
```

The line `tick=10 agent-response order=order-2 attempt=0 newEffect=false
onTime=false` is the detail worth reading twice. `order-2`'s abandoned first
attempt does eventually complete against the remote service, but
`newEffect=false` shows the idempotency guard correctly recognized it as a
duplicate of the effect already applied by attempt one at tick seven, and
`onTime=false` shows the Scheduler correctly refused to let a stale attempt
overwrite the task's already-Processed state. Java, Rust, and Swift versions
were not written for this entry because TypeScript, Python, and Go already
cover the async-oriented, script-oriented, and statically compiled shapes
the pattern is commonly built in production, and a fourth deterministic port
would repeat the identical simulation logic in a fourth syntax without
adding a new implementation idea.
