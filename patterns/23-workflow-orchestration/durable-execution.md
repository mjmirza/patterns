---
name: Durable Execution
slug: durable-execution
family: 23-workflow-orchestration
category: workflow orchestration
aliases: [Fault Tolerant Workflow Execution, Crash Proof Execution, Durable Functions]
first_described: "Fred B. Schneider, Implementing Fault Tolerant Services Using the State Machine Approach, ACM Computing Surveys, December 1990, which formalized deterministic state machine replication as the theoretical basis for reconstructing execution from a recorded request sequence. The event sourced replay mechanism itself traces to Martin Fowler's Event Sourcing pattern, published on his site in 2005. The term durable execution as a named category for this specific mechanism was popularized by Temporal in its own documentation and blog beginning in the early 2020s"
maturity: established
related: [workflow-engine, state-machine-workflow, human-task, compensation-handler, saga]
verified: 2026-08-23
---

# Durable Execution

## 1. Name, aliases, and lineage

Durable execution names a runtime property, not a single algorithm. A program has durable execution when its progress through a sequence of steps, including its local variables and its position in the call stack, survives a process crash, a redeploy, or a host reboot, and resumes exactly where it left off rather than restarting from the beginning or losing its place entirely.

The mechanism that makes this possible is Event Sourcing, applied to program control flow rather than to data records. Martin Fowler's own definition of the general pattern is to "capture all changes to an application state as a sequence of events," so that the state "can be discarded completely and rebuilt by re-running the events from the event log" (Fowler, Event Sourcing, martinfowler.com, 2005-12-12, https://martinfowler.com/eaaDev/EventSourcing.html, verified 2026-08-23). Durable execution takes that same append-and-replay idea and applies it to which step of a program ran and what it returned, so that replaying the recorded sequence against the original code reconstructs identical in-memory state.

The theoretical justification for why deterministic replay is correct at all traces further back, to Fred B. Schneider's tutorial on state machine replication. Schneider defines a state machine as consisting of "state variables, which encode its state, and commands, which transform its state," where "execution of the command is atomic with respect to other commands," and states the property durable execution depends on directly, that "outputs of a state machine are completely determined by the sequence of requests it processes, independent of time and any other activity in a system" (Schneider, Implementing Fault Tolerant Services Using the State Machine Approach, A Tutorial, ACM Computing Surveys 22(4), December 1990, pp. 299 to 319, https://www.cs.cornell.edu/fbs/publications/SMSurvey.pdf, verified 2026-08-23). If a program's output is a deterministic function of an ordered event sequence, then persisting that sequence and re-running the deterministic code against it is sufficient to reconstruct the program's exact prior state, which is the entire mechanical basis of every durable execution runtime described below.

The named term itself is more recent. Temporal, currently the most complete general purpose implementation of this pattern, states plainly in its own docs that Durable Execution is what makes an application behave correctly despite adverse conditions, guaranteeing that it "will run to completion" (Temporal Docs, Understanding Temporal, https://docs.temporal.io/evaluate/understanding-temporal, verified 2026-08-23), and its own May 2025 blog post frames the whole category around a single idea, that "Durable Execution is crash proof execution," which "enables developers to write reliable software with less effort" by letting them focus on application goals rather than failure handling (Tom Wheeler, What Is Durable Execution, Temporal blog, 2025-05-06, https://temporal.io/blog/what-is-durable-execution, verified 2026-08-23). Whether Temporal was the first to use this exact two word phrase could not be confirmed independently, and this entry does not assert an origin date for the term stronger than the sourced evidence supports.

## 2. Problem and context

A long running process, one that spans minutes, days, or months of real wall clock time and moves through many sequential steps, will eventually crash, get killed by a deploy, or have its host rebooted, simply because the process runs long enough for one of those events to occur. Without durable execution, everything the process held in memory at that moment, which step it was on, what local variables it had computed, is gone. Temporal's own framing of the problem is direct, that "normally, if a crash occurs then the state of your application's execution is lost," which forces "extensive error handling logic and complex recovery code to resume" (Temporal Docs, Understanding Temporal, https://docs.temporal.io/evaluate/understanding-temporal, verified 2026-08-23).

The naive fix, checkpointing application state to a database by hand at every meaningful step, works but scatters persistence bookkeeping through business logic, and every place a developer forgets a checkpoint becomes a place recovery silently loses ground. AWS frames the same problem from the operator's side, in Step Functions Standard workflows, which it positions for "long running, up to one year, durable, and auditable workflows," and where "execution state internally persists between state transitions" specifically so the platform, not the developer, carries that bookkeeping (AWS Step Functions Developer Guide, Standard vs Express Workflows, https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html, verified 2026-08-23).

Azure Durable Functions arrives at the identical problem statement independently. Its orchestrator functions "automatically checkpoint execution progress when the function calls an await or yield operator, so the process doesn't lose local state when it recycles or the VM reboots," and are built to "support long running processes," where "the total lifespan of an orchestration instance can be seconds, days, or months, or you can configure the instance to never end" (Microsoft Learn, Durable Task orchestrations, https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-orchestrations, verified 2026-08-23). Three vendors, arriving at the same problem statement independently, is itself evidence that the problem is structural to long running processes rather than specific to any one platform.

## 3. Forces

Determinism is the central, hardest force this pattern balances. Since durability is achieved by re-running program code against a recorded history rather than by snapshotting raw memory, the code that gets re-run must produce identical results every time it runs, given the same recorded input. Temporal states this directly, that "Workflow code must be deterministic to support replay," and that "any time your Workflow code is executed it makes the same Workflow API calls in the same sequence, given the same input" (Temporal Docs, Workflow Definition, https://docs.temporal.io/workflow-definition, verified 2026-08-23). A direct call to read the system clock, generate a random number, or perform network I/O inline inside that code would return a different value on replay than it did the first time, breaking the guarantee. The universal fix, present independently in Temporal (Activities) and Azure (Activity Functions), is to push every non-deterministic operation into a separately tracked unit whose real result is recorded once and substituted on every later replay, and Azure states its own version of the same rule plainly, that orchestrator functions "can't perform I/O operations" directly and any code that needs to must be wrapped "in an activity function" (Microsoft Learn, Durable Task orchestrations, https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-orchestrations, verified 2026-08-23).

A second force is that the recorded history grows without bound for the lifetime of a long running execution, and every resume has to replay it from the start to rebuild state, so a very long history is both a scaling risk and a real cost. Temporal documents concrete numeric ceilings on this, warning the operator once an execution's history passes 10,240 events and terminating the execution outright if it exceeds 51,200 events (Temporal Docs, Event History Limits, https://docs.temporal.io/workflow-execution/event, verified 2026-08-23). The documented mitigation is Continue-As-New, described as a mechanism to "close the current execution and create a new one," which developers are told to reach for "when your Workflow might hit Event History Limits" (Temporal Docs, Continue-As-New, https://docs.temporal.io/develop/typescript/continue-as-new, verified 2026-08-23), effectively resetting the history to zero while carrying forward whatever state the workflow still needs.

A third force is versioning an already running execution. Because an execution can be mid flight for months, "it's common to need to make changes to a Workflow Definition, even while a particular Workflow Execution is in progress," and Temporal is explicit that changes such as "adding, removing, or reordering await calls on Command producing APIs" break replay against that execution's existing history (Temporal Docs, Versioning, https://docs.temporal.io/develop/typescript/versioning, verified 2026-08-23). The documented answer is an explicit patch marker recorded into the history itself, so that old, still running executions keep replaying against the code path they started on while new executions pick up the new code, a force with no equivalent in a stateless service, where a deploy simply replaces every future request's behavior with no in flight state to reconcile.

## 4. Applicability and non-applicability

Reach for durable execution when a process genuinely needs to survive the platform events described in section 2 across a duration long enough that they become likely, and when the steps involved are not safely repeatable on their own, so an at-least-once retry model without persisted state could cause a double charge, a duplicate order, or a repeated external side effect. AWS states this applicability directly for its Standard workflow type, whose "exactly-once" execution model is aimed at "non-idempotent actions, such as starting an Amazon EMR cluster or processing payments" (AWS Step Functions Developer Guide, Standard vs Express Workflows, https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html, verified 2026-08-23).

Do not reach for it when the work is short lived and the individual steps are already safely repeatable. AWS draws this line inside its own product line rather than leaving it to guesswork, offering Express workflows as the explicit lighter alternative, positioned for "high volume, event processing workloads" that run "up to five minutes," where "execution state doesn't persist between state transitions" and "execution history is not captured" at all unless the customer wires up CloudWatch Logs separately (AWS Step Functions Developer Guide, Standard vs Express Workflows, https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html, verified 2026-08-23). A team that reaches for the Standard, durability-bearing option for work that actually fits Express is paying the operational and cognitive cost of this pattern for no benefit.

The determinism constraint from section 3 is itself a non-applicability signal. Code that is structurally impossible to split into a deterministic orchestration layer plus isolated non-deterministic units, because it is tightly coupled to a library or an external mutable state source that cannot be moved behind an activity boundary, is a poor fit for this pattern unless it is refactored first. This is not a vendor specific quirk. Temporal (Activities) and Azure (Activity Functions) independently enforce the identical boundary, which is evidence the constraint is structural to the mechanism, not a limitation of one implementation.

## 5. Structure

The following participants recur across every durable execution implementation, defined here primarily from Temporal's own documentation, the most complete and actively maintained general purpose implementation, and cross checked against Azure Durable Functions where the two independently converge on the same shape.

Event History is the durable, ordered record everything durable execution depends on, defined as "a complete, ordered log of everything that has already happened in a Workflow" and treated as "the source of truth for everything that happens in the Workflow" (Temporal Docs, Workflows, https://docs.temporal.io/workflows, verified 2026-08-23). Azure's independent name for the identical record, built with "the event sourcing design pattern," is an "append only store" recording "the full series of actions the function orchestration takes" (Microsoft Learn, Durable Task orchestrations, https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-orchestrations, verified 2026-08-23).

Workflow is the deterministic, replayable orchestration code, "a durable, reliable, and scalable function execution and the main unit of execution of a Temporal Application" (Temporal Docs, Workflow Execution, https://docs.temporal.io/workflow-execution, verified 2026-08-23), defined by "a Workflow Definition," which is "the code that defines the Workflow" (Temporal Docs, Workflow Definition, https://docs.temporal.io/workflow-definition, verified 2026-08-23).

Activity is the non-deterministic, side effect bearing unit of work that the Workflow calls out to. Activities "handle everything that interacts with the outside world, like API calls, database queries, LLM invocations, file I/O" (Temporal Docs, Understanding Temporal, https://docs.temporal.io/evaluate/understanding-temporal, verified 2026-08-23), and every non-deterministic operation is required to live here rather than inside Workflow code.

Replay is the recovery mechanism itself, "the method by which a Workflow Execution resumes making progress," during which "the Commands that are generated are checked against an existing Event History" (Temporal Docs, Workflow Execution, https://docs.temporal.io/workflow-execution, verified 2026-08-23). Concretely, the runtime "starts the Workflow code from the beginning, replays the Event History step by step, and uses that history to guide the code back to the exact state as before" (Temporal Docs, Workflows, https://docs.temporal.io/workflows, verified 2026-08-23). Azure's independently arrived at description of the same mechanism matches closely, that on resume "the orchestrator wakes up and re-executes the entire function from the start to rebuild the local state," and where the framework "consults the execution history" for any already completed step and "replays that function's result" instead of re-triggering it (Microsoft Learn, Durable Task orchestrations, https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-orchestrations, verified 2026-08-23).

Determinism is the formal property Replay depends on, that the Workflow "has to make the same decisions when given the same history" (Temporal Docs, Workflows, https://docs.temporal.io/workflows, verified 2026-08-23), the direct application of Schneider's own state machine property, that outputs are "completely determined by the sequence of requests it processes" (Schneider, 1990, p. 300).

Task Queue and Worker are the execution substrate. A Worker Process is "responsible for polling a Task Queue, dequeueing a Task, executing your code in response to a Task, and responding to the Temporal Service with the results," and critically the platform itself "doesn't execute any of your code on Temporal Service machines," execution always happens on Worker Processes the application team runs (Temporal Docs, Workers, https://docs.temporal.io/workers, verified 2026-08-23), which is precisely what lets any new Worker Process pick up and replay a crashed execution.

Command and Checkpoint describe how progress becomes durable. "A Command is a requested action issued by a Worker to the Temporal Service after a Workflow Task Execution completes," and once the platform accepts that Command, it is "recorded in the Workflow Execution's Event History as an Event" (Temporal Docs, Workflow Execution, https://docs.temporal.io/workflow-execution, verified 2026-08-23), which is the exact moment progress moves from being in memory and fragile to being durable and recoverable.

## 6. ASCII structure diagram

```
+-------------------------------------------------------------+
|                     DURABLE EXECUTION SYSTEM                 |
|                                                                |
|   +----------------+        Commands         +-----------+   |
|   |  Worker Process |----------------------->| Temporal / |   |
|   |  (runs your     |                         | Step Fns / |   |
|   |   Workflow +    |<------------------------| Durable    |   |
|   |   Activity code)|   dequeued Tasks         | Functions  |   |
|   +--------+--------+                         |  Service   |   |
|            |                                   +-----+-----+   |
|            | calls out to                            |         |
|            v                                          v         |
|   +----------------+                        +-------------------+
|   |    Activity     |                        |   Event History    |
|   | (real side      |                        |  (append only,     |
|   |  effects: DB,   |                        |   durable, ordered) |
|   |  API, file I/O) |                        +-------------------+
|   +-----------------+
+----------------------------------------------------------------+
```

## 7. Dynamics

```
t0  Workflow starts on Worker Process A. Code begins executing top to bottom.

t1  Step 1 runs (an Activity, e.g. charge a card). A REAL side effect happens.
    Worker A issues a Command. The Service records:
      Event 1  ActivityScheduled  charge_card
      Event 2  ActivityCompleted  result = charged

t2  Step 2 runs (an Activity, e.g. reserve inventory). A REAL side effect happens.
    Worker A issues a Command. The Service records:
      Event 3  ActivityScheduled  reserve_inventory
      Event 4  ActivityCompleted  result = reserved

t3  Worker Process A crashes. In-memory state (local variables, call stack
    position) is gone. The Event History, held by the Service, is not.

t4  A new Worker Process B polls the Task Queue and picks up the Workflow Task.
    REPLAY begins: Worker B re-runs the Workflow code from the top.
      reaches Step 1  -> history has Event 1/2 -> does NOT re-charge the card,
                          the recorded result is substituted instead
      reaches Step 2  -> history has Event 3/4 -> does NOT re-reserve stock,
                          the recorded result is substituted instead
    In-memory state is now reconstructed exactly as it was before the crash.

t5  Step 3 runs (an Activity with no matching history entry yet, e.g. send a
    confirmation email). Worker B executes it FOR REAL for the first time.
    The Service records:
      Event 5  ActivityScheduled  send_confirmation
      Event 6  ActivityCompleted  result = sent

t6  The Workflow continues forward normally until it completes, or crashes
    again, in which case the same Replay sequence repeats from t3.
```

## 8. Implementation variants

Temporal is the clearest general purpose implementation, splitting orchestration from side effects across SDKs for "Go, Java, TypeScript, or Python" (Temporal Docs, Workflows, https://docs.temporal.io/workflows, verified 2026-08-23), backed by a Temporal Server that persists the Event History as the durability boundary. A Temporal application always has three moving pieces, the Workflow code, the Activity code, and the Server, none of which the developer's own process needs to keep alive between steps.

AWS Step Functions offers two workflow types with a documented, sharp durability line between them. Standard workflows "follow an exactly once model" where "execution state internally persists between state transitions," retrievable "using the Step Functions API for up to 90 days after your execution completes." Express workflows, by contrast, "use an at-least-once model, so an execution could potentially run more than once," "execution state doesn't persist between state transitions," and "execution history is not captured by Step Functions" at all unless the customer bolts on CloudWatch Logs separately (AWS Step Functions Developer Guide, Standard vs Express Workflows, https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html, verified 2026-08-23). This is a single vendor shipping both a durable and a non-durable variant of the same product, letting a customer choose the durability tier per workload rather than paying for it universally.

Azure Durable Functions implements the pattern as a library layered on top of ordinary Azure Functions, using "the event sourcing design pattern" so that on resume "the orchestrator wakes up and re-executes the entire function from the start to rebuild the local state" (Microsoft Learn, Durable Task orchestrations, https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-orchestrations, verified 2026-08-23), checkpointing automatically "when the function calls an await or yield operator" (Microsoft Learn, Durable Functions orchestrations, https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-orchestrations, verified 2026-08-23).

A newer generation of implementations has emerged that self identifies with this exact term while taking a lighter operational shape than a dedicated Temporal Server cluster. Restate describes itself around "durable execution, code that survives crashes, restarts, and infrastructure failures," delivered as "a lightweight, self contained binary requiring no separate message broker or orchestrator" (Restate, restate.dev, verified 2026-08-23). DBOS takes a library rather than server approach, where a developer adds "a few annotations to your application to durably execute it," with "no separate orchestration server and no infrastructure required besides Postgres" (DBOS Docs, docs.dbos.dev, verified 2026-08-23). Inngest positions itself with the headline "Durable Execution for Workflows and AI," aimed at code that "has to work no matter what" (Inngest, inngest.com, verified 2026-08-23). Hatchet advertises "Durable Execution without the overhead, backed by Postgres," as an MIT licensed, self hostable or managed platform (Hatchet, hatchet.run, verified 2026-08-23). All four converge on the same trend, a Postgres backed or single binary alternative to operating a dedicated durability cluster, in exchange for a narrower feature surface than Temporal's mature SDK ecosystem.

## 9. Known production uses

Uber built and open sourced Cadence, described in its own repository as "a distributed, scalable, durable, and highly available orchestration engine to execute asynchronous long running business logic in a scalable and resilient way," available "as an open source platform since 2017" (Uber, Cadence, GitHub, https://github.com/uber/cadence, verified 2026-08-23). Cadence is the direct architectural predecessor to Temporal, built by the same founding engineers before they spun the project out under a new name.

Netflix built Conductor for the same class of problem before the durable execution term existed, writing in its own engineering blog that before the system existed, "process flows are embedded within the code of multiple applications," making it impossible to answer basic questions such as "what is remaining for a movie's setup to be complete." At the center of Conductor sits "a state machine service aka Decider service" that reconciles a workflow's blueprint against its current execution state to resume progress, giving the system the "ability to pause, resume and restart processes" (Viren Baraiya and Vikram Singh, Netflix Conductor, A Microservices Orchestrator, Netflix Tech Blog, 2016-12-12, https://netflixtechblog.com/netflix-conductor-a-microservices-orchestrator-2e8d4771bf40, verified 2026-08-23).

Replit runs Temporal in production specifically to make its AI coding agent survive mid task failures without losing user work, describing the underlying pain in an engineer's own words, that "it's a pretty bad user experience to have the agent get super far into something and then hit a catastrophic error," and reporting that after a September 2024 migration, "Temporal has never been the bottleneck" at scale and the team has "never had any major incidents that trace back to Temporal Cloud" (Temporal Case Study, Replit Uses Temporal to Power Replit Agent Reliably at Scale, 2025-09-15, https://temporal.io/resources/case-studies/replit-uses-temporal-to-power-replit-agent-reliably-at-scale, verified 2026-08-23).

Two further named, dated production deployments confirm the scale this pattern is run at outside a demo environment. Vinted's own case study title states it runs "10 to 12 Million Workflows a Day," and Emergent's states it runs "1 billion plus agent Actions per month on Temporal Cloud" (Temporal, In Use case study index, https://temporal.io/in-use, verified 2026-08-23).

## 10. Consequences

Positive. A crashed process resumes from its exact last recorded step automatically, with no hand written recovery path. Business logic reads as plain, linear code, because the persistence bookkeeping the naive alternative scatters through every step is handled by the platform instead. The Event History doubles as a complete audit trail of the execution, queryable for its retention window. Because the runtime already knows how to fast forward or rewind through recorded time, the same mechanism that gives crash recovery also gives a genuine testing advantage, a multi day execution can be exercised in a test in milliseconds by skipping simulated time rather than actually waiting.

Negative. The determinism constraint is a real, ongoing coding discipline, every non-deterministic operation must be identified and pushed behind an Activity boundary, and a missed one produces a failure that may not surface until a later deploy replays against old history. Event History has documented hard ceilings, a Temporal execution is warned at 10,240 events and terminated outright at 51,200 (Temporal Docs, Event History Limits, https://docs.temporal.io/workflow-execution/event, verified 2026-08-23), which forces Continue-As-New discipline onto any sufficiently long running workflow. Running the platform itself is not free, a team either operates a stateful cluster or pays a managed vendor per action, and deploying new code against an already running execution is a documented hard problem requiring explicit version markers rather than a plain code replace.

## 11. Failure modes and misuse

Non-deterministic workflow code, most commonly a direct call to the system clock, a random number generator, or an inline network call inside orchestration code rather than an Activity, causes replay to diverge from the recorded history. The observable symptom is a workflow task failure carrying a non-determinism error, and on Azure Durable Functions the platform states plainly that "nondeterministic orchestrator code can result in runtime errors or other unexpected behavior" (Microsoft Learn, Durable Task orchestrations, https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-orchestrations, verified 2026-08-23). The dangerous variant of this failure is that a change can pass every unit test cleanly, because a fresh test has no history to replay against, and only fails once it collides with an already in flight execution's real history in production.

Letting the Event History grow without bound is a second failure mode. The observable symptom escalates in two stages, a warning logged once an execution passes 10,240 events, followed by outright termination at 51,200 events (Temporal Docs, Event History Limits, https://docs.temporal.io/workflow-execution/event, verified 2026-08-23), and the fix is to reach for Continue-As-New before the ceiling is close, not after.

Deploying new code that changes the sequence of awaited calls inside an already running workflow's code path, without an explicit version or patch marker, is a documented failure mode specific to this pattern, since the new code will fail to reproduce the old code's sequence of Commands when it tries to replay an in flight execution's existing history (Temporal Docs, Versioning, https://docs.temporal.io/develop/typescript/versioning, verified 2026-08-23).

Reaching for this pattern when the work does not need it is a misuse pattern in the other direction. AWS's own Standard versus Express split exists precisely because customers were applying Standard's exactly-once, history retaining machinery to work that fits Express's five minute, at-least-once model far better, paying the operational and cognitive overhead of durability for a workload that never needed it (AWS Step Functions Developer Guide, Standard vs Express Workflows, https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html, verified 2026-08-23).

Finally, storing sensitive data unencrypted inside a durably retained Event History is a misuse specific to this pattern's data model. Since a Standard or Temporal execution's history is retained for a real, bounded but meaningful window, any secret or personal data passed as a Workflow or Activity input or output persists in that store by default unless it is encrypted before it ever reaches the server.

## 12. Trade-off matrix

| Force | Durable execution (Temporal, Step Functions Standard, Durable Functions) | Manual checkpointing to a database | Non-durable in-process state machine |
|---|---|---|---|
| Crash recovery | Automatic, resumes from the exact last recorded step | Manual, only as complete as the checkpoints a developer remembered to write | None, in-memory state is lost |
| Developer effort | Determinism discipline required, no manual persistence code | High, persistence logic threaded through every step of business logic | Low, but only viable for short-lived processes |
| Auditability | A full ordered event history, queryable for a bounded window | Whatever the developer chose to log, usually partial | Application logs only, no execution record |
| Operational cost | A stateful cluster to run, or a per-action bill on a managed vendor | An existing database, no new cluster to run | None, but no durability either |
| Long-running scale | Bounded by documented event-count ceilings, needs Continue-As-New for very long executions | Bounded only by the database schema and query patterns chosen | Not applicable, bound to a single process's lifetime |
| Versioning in flight work | A documented hard problem with an explicit patch-marker mechanism | Ad hoc, whatever migration strategy the schema allows | Not applicable, nothing survives a deploy anyway |

## 13. Related and incompatible patterns

Workflow Engine, a sibling entry in this family, is the broader orchestration platform that is commonly built on top of durable execution as its foundation. Temporal's own self-description supports this framing directly, branding itself the "open source Durable Execution platform for crash-proof applications and AI agents," treating durable execution as the named underlying capability the wider Workflow Engine product surface, SDKs, UI, Signals, is layered on top of.

State Machine Workflow, another sibling entry, is the modeling pattern for the sequence of steps and transitions a process moves through. Durable execution is what makes that model survive a crash between transitions, the state machine describes what steps exist, durable execution guarantees the process does not lose its place among them.

Human Task, another sibling entry, is implemented directly on top of a durable execution primitive Temporal calls a Signal. A Workflow blocks on a condition wait, an external actor, commonly a human through a client call, sends a Signal, and the Workflow resumes exactly where it paused (Temporal Docs, Sending Messages, https://docs.temporal.io/sending-messages, verified 2026-08-23), confirming that Human Task is a specific use of a general purpose external-event primitive, not a separate mechanism from durable execution itself.

Compensation Handler and Saga, two further sibling entries, are commonly implemented on top of durable execution using ordinary language control flow. Temporal documents the Saga pattern directly, describing it as breaking "a transaction into a series of smaller, manageable sub-transactions," where a failed step triggers "specific actions to undo the previous steps" (Temporal Docs, Use Cases and Design Patterns, https://docs.temporal.io/evaluate/use-cases-design-patterns, verified 2026-08-23), implemented in practice as each sub-transaction being an ordinary Activity call, with compensation triggered from a Workflow's own try and catch control flow invoking compensating Activities, each of those calls durably recorded like any other step.

Incompatible with code that cannot be decomposed into a deterministic orchestration layer plus isolated activities without a significant rewrite, and with workloads carrying a hard sub-second latency budget, where the round trip cost of appending an event and having a worker poll for it is unacceptable overhead compared to an ordinary function call.

## 14. Refactoring path in and out

Refactoring in starts by identifying the long-running, multi-step process that currently loses progress on a crash. Every I/O operation, external call, and use of the system clock or a random number generator is extracted into its own Activity function, isolated from the orchestration logic. The orchestrating logic is then rewritten as Workflow code that only calls those Activities and awaits their results, never performing I/O directly. A Task Queue is chosen and one or more Workers are registered against it. The process is finally started by invoking a client entry point, a Temporal Client, a Step Functions StartExecution call, or an Azure orchestration client, rather than calling the old function directly from the caller's own process.

Refactoring out applies once a process's actual runtime profile no longer needs multi-day or multi-month durability, most commonly because its scope shrank to a single request that reliably completes well inside a short workflow type's ceiling, such as Step Functions Express's five minute limit. At that point the Workflow and its Activities are collapsed back into an ordinary function, and the SDK dependency and history-retention cost are removed. This direction should only be taken once the workload's short, idempotent runtime profile has actually been confirmed, not assumed.

## 15. Testing and verification

Temporal ships a time-skipping test environment specifically so a workflow that sleeps for a day, or an activity with a long retry backoff, does not force a test to wait in real time. Inside that environment, when a test executes a Workflow, "the test server switches to skipped time mode until the Workflow completes," fast-forwarding timers "except when Activities are running" (Temporal Docs, Testing Suite, TypeScript, https://docs.temporal.io/develop/typescript/testing-suite, verified 2026-08-23).

Replay testing is the platform's own recommended safe-deployment practice, distinct from ordinary unit testing precisely because ordinary unit tests have no history to replay against and cannot catch the failure mode described in section 11. The documented recipe is to fetch real Event Histories from representative recent executions of a Workflow type and replay them against the candidate new code, where "replay succeeds only if the Workflow Definition is compatible with the provided history from a deterministic point of view," and CI is expected to "fail if any error is encountered during replay" (Temporal Docs, Testing Suite, Go, https://docs.temporal.io/develop/go/testing-suite, verified 2026-08-23).

Because a non-deterministic change can pass ordinary tests cleanly and only fail on collision with a real in-flight execution's history, review of any change to an already shipped Workflow's sequence of awaited calls, additions, removals, or reorderings, is a necessary discipline in its own right, backed by the explicit patch markers described in section 3 for anything that must change behavior for executions that are already running.

## 16. Observability signals

Temporal's own Web UI surfaces the Event History, the currently pending Activities, and the Workers actively polling a given Workflow's Task Queue (Temporal Docs, Web UI, https://docs.temporal.io/web-ui, verified 2026-08-23), which matters specifically because no single process's local logs cover a logical execution's entire lifetime, a Workflow can span months and be replayed across many different Worker Processes over that time.

Trace propagation must be carried across the replay boundary explicitly rather than relying on an ordinary in-process trace span. Temporal's SDK does this using "protobuf message headers" to "propagate the tracing information from the client to the Workflow and from the Workflow to its successors" (Temporal Docs, Observability, TypeScript, https://docs.temporal.io/develop/typescript/platform/observability, verified 2026-08-23), because a trace tied to a single process's lifetime would not survive a crash and resume on a different worker.

The metrics worth watching are the workflow task failure rate, which surfaces determinism errors as they occur, Event History size relative to the platform's documented ceiling, worker poll latency, and Continue-As-New frequency, or its conspicuous absence on a workflow that is approaching the history limit. Azure Durable Functions documents a specific observability trap directly relevant to this pattern, that raw log lines emitted from orchestrator code "can cause duplicate log messages to be emitted" during replay (Microsoft Learn, Durable Task orchestrations, https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-orchestrations, verified 2026-08-23), which means ordinary process logs cannot be trusted as one line per real event without replay-aware filtering.

## 17. Security and privacy implications

Because the durably retained Event History includes every Activity's real inputs and outputs, and Standard or Temporal executions retain that history for a real, bounded window, any sensitive data passed through a Workflow persists in that store by default. Temporal's documented mitigation is a Payload Codec, used "to encrypt payloads before they reach the Temporal Service," so that "data exists unencrypted only on the Client and the Worker process, on hosts that you control" (Temporal Docs, Data Encryption, https://docs.temporal.io/production-deployment/data-encryption, verified 2026-08-23), decoded only through a customer-controlled Codec Server the organization gates behind its own authorization.

On the platform side, Temporal Server has several disclosed advisories. The more serious 2025 and 2026 dated ones concern namespace isolation, where a caller authorized in one namespace could reach into or affect a different namespace's workflow state, including one where "a writer role user in an attacker-controlled namespace could signal, delete, and reset workflows or activities in a victim namespace on the same cluster" (GitHub Security Advisory GHSA-xpg8-3hhp-p7w8, https://github.com/advisories/GHSA-xpg8-3hhp-p7w8, verified 2026-08-23), and another where the server, with a specific feature enabled, "permits certain workflow task commands to target a different namespace than the namespace authorized at the gRPC boundary" (GitHub Security Advisory GHSA-hmhp-gh8m-c8xp, https://github.com/advisories/GHSA-hmhp-gh8m-c8xp, verified 2026-08-23). This class of finding matters specifically for durable execution as a category, because a durable execution server owns durable control operations, signal, reset, delete, for every tenant's workflow state, giving an authorization bug in that server an unusually wide blast radius compared to a stateless service where a bug typically affects only the current request.

## 18. References

1. Martin Fowler, Event Sourcing, martinfowler.com bliki, 2005-12-12, https://martinfowler.com/eaaDev/EventSourcing.html, verified 2026-08-23.
2. Fred B. Schneider, Implementing Fault Tolerant Services Using the State Machine Approach, A Tutorial, ACM Computing Surveys 22(4), December 1990, pp. 299 to 319, https://www.cs.cornell.edu/fbs/publications/SMSurvey.pdf, verified 2026-08-23.
3. Tom Wheeler, What Is Durable Execution, Temporal blog, 2025-05-06, https://temporal.io/blog/what-is-durable-execution, verified 2026-08-23.
4. Temporal Docs, Understanding Temporal, https://docs.temporal.io/evaluate/understanding-temporal, verified 2026-08-23.
5. Temporal Docs, Workflows, https://docs.temporal.io/workflows, verified 2026-08-23.
6. Temporal Docs, Workflow Definition, https://docs.temporal.io/workflow-definition, verified 2026-08-23.
7. Temporal Docs, Workflow Execution, https://docs.temporal.io/workflow-execution, verified 2026-08-23.
8. Temporal Docs, Event History Limits, https://docs.temporal.io/workflow-execution/event, verified 2026-08-23.
9. Temporal Docs, Continue-As-New, TypeScript, https://docs.temporal.io/develop/typescript/continue-as-new, verified 2026-08-23.
10. Temporal Docs, Versioning, TypeScript, https://docs.temporal.io/develop/typescript/versioning, verified 2026-08-23.
11. Temporal Docs, Workers, https://docs.temporal.io/workers, verified 2026-08-23.
12. Temporal Docs, Web UI, https://docs.temporal.io/web-ui, verified 2026-08-23.
13. Temporal Docs, Observability, TypeScript, https://docs.temporal.io/develop/typescript/platform/observability, verified 2026-08-23.
14. Temporal Docs, Testing Suite, TypeScript, https://docs.temporal.io/develop/typescript/testing-suite, verified 2026-08-23.
15. Temporal Docs, Testing Suite, Go, https://docs.temporal.io/develop/go/testing-suite, verified 2026-08-23.
16. Temporal Docs, Sending Messages, https://docs.temporal.io/sending-messages, verified 2026-08-23.
17. Temporal Docs, Use Cases and Design Patterns, https://docs.temporal.io/evaluate/use-cases-design-patterns, verified 2026-08-23.
18. Temporal Docs, Data Encryption, https://docs.temporal.io/production-deployment/data-encryption, verified 2026-08-23.
19. AWS Step Functions Developer Guide, Standard vs Express Workflows, https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html, verified 2026-08-23.
20. Microsoft Learn, Durable Task orchestrations, https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-orchestrations, verified 2026-08-23.
21. Microsoft Learn, Durable Functions orchestrations, https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-orchestrations, verified 2026-08-23.
22. Uber, Cadence, GitHub repository, https://github.com/uber/cadence, verified 2026-08-23.
23. Viren Baraiya and Vikram Singh, Netflix Conductor, A Microservices Orchestrator, Netflix Tech Blog, 2016-12-12, https://netflixtechblog.com/netflix-conductor-a-microservices-orchestrator-2e8d4771bf40, verified 2026-08-23.
24. Temporal Case Study, Replit Uses Temporal to Power Replit Agent Reliably at Scale, 2025-09-15, https://temporal.io/resources/case-studies/replit-uses-temporal-to-power-replit-agent-reliably-at-scale, verified 2026-08-23.
25. Temporal, In Use case study index, https://temporal.io/in-use, verified 2026-08-23.
26. Restate, restate.dev, verified 2026-08-23.
27. DBOS Docs, docs.dbos.dev, verified 2026-08-23.
28. Inngest, inngest.com, verified 2026-08-23.
29. Hatchet, hatchet.run, verified 2026-08-23.
30. GitHub Security Advisory GHSA-xpg8-3hhp-p7w8, https://github.com/advisories/GHSA-xpg8-3hhp-p7w8, verified 2026-08-23.
31. GitHub Security Advisory GHSA-hmhp-gh8m-c8xp, https://github.com/advisories/GHSA-hmhp-gh8m-c8xp, verified 2026-08-23.

**Evidence grade.** high

**Most solid findings.** The determinism constraint and its enforcement mechanism are independently confirmed, in near-identical terms, by Temporal and Azure, two unrelated vendors, which is strong corroboration that it is structural to the pattern rather than an implementation quirk. The Standard versus Express durability split is stated explicitly and unambiguously by AWS in its own comparison documentation, leaving no ambiguity about where the line is drawn. The documented Event History numeric ceilings, a warning at 10,240 events and termination at 51,200, are stated plainly on a single authoritative Temporal page.

**Unverified or unclear.** Whether Temporal was genuinely first to popularize the exact two word term durable execution, and when, could not be independently confirmed against a source outside Temporal's own site. A precise megabyte-based Event History size ceiling, distinct from the event-count ceiling, could not be confirmed with confidence and is intentionally omitted from this entry rather than stated on weak evidence. Precise founding or public launch dates for Restate, DBOS, and Hatchet were not independently confirmed and are not asserted here.

## Code

### TypeScript

```typescript
type HistoryEvent = { step: string; result: string };

class DurableExecutionEngine {
  private history: HistoryEvent[] = [];
  private cursor = 0;

  loadHistory(history: HistoryEvent[]): void {
    this.history = history;
    this.cursor = 0;
  }

  runStep(step: string, sideEffect: () => string): string {
    const recorded = this.history[this.cursor];
    if (recorded !== undefined && recorded.step === step) {
      this.cursor += 1;
      return recorded.result;
    }
    const result = sideEffect();
    this.history.push({ step, result });
    this.cursor += 1;
    return result;
  }

  getHistory(): HistoryEvent[] {
    return this.history;
  }
}

function chargeCard(): string {
  return "charged 42.00";
}

function reserveInventory(): string {
  return "reserved";
}

function orderWorkflow(engine: DurableExecutionEngine): string[] {
  const results: string[] = [];
  results.push(engine.runStep("chargeCard", chargeCard));
  results.push(engine.runStep("reserveInventory", reserveInventory));
  return results;
}

function main(): void {
  const firstRun = new DurableExecutionEngine();
  const firstResults = orderWorkflow(firstRun);
  console.log(firstResults);

  const savedHistory = firstRun.getHistory();

  const afterCrash = new DurableExecutionEngine();
  afterCrash.loadHistory(savedHistory);
  const replayedResults = orderWorkflow(afterCrash);
  console.log(replayedResults);

  if (JSON.stringify(firstResults) !== JSON.stringify(replayedResults)) {
    throw new Error("replay diverged from original execution");
  }
}

main();
```

### Python

```python
class DurableExecutionEngine:
    def __init__(self):
        self.history = []
        self.cursor = 0

    def load_history(self, history):
        self.history = history
        self.cursor = 0

    def run_step(self, step_name, side_effect):
        if self.cursor < len(self.history) and self.history[self.cursor]["step"] == step_name:
            result = self.history[self.cursor]["result"]
            self.cursor += 1
            return result
        result = side_effect()
        self.history.append({"step": step_name, "result": result})
        self.cursor += 1
        return result


def charge_card():
    return "charged 42.00"


def reserve_inventory():
    return "reserved"


def order_workflow(engine):
    results = []
    results.append(engine.run_step("charge_card", charge_card))
    results.append(engine.run_step("reserve_inventory", reserve_inventory))
    return results


def main():
    first_run = DurableExecutionEngine()
    first_results = order_workflow(first_run)
    print(first_results)

    saved_history = first_run.history

    after_crash = DurableExecutionEngine()
    after_crash.load_history(saved_history)
    replayed_results = order_workflow(after_crash)
    print(replayed_results)

    if first_results != replayed_results:
        raise RuntimeError("replay diverged from original execution")


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import (
	"fmt"
	"reflect"
)

type HistoryEvent struct {
	Step   string
	Result string
}

type DurableExecutionEngine struct {
	History []HistoryEvent
	Cursor  int
}

func (e *DurableExecutionEngine) LoadHistory(history []HistoryEvent) {
	e.History = history
	e.Cursor = 0
}

func (e *DurableExecutionEngine) RunStep(step string, sideEffect func() string) string {
	if e.Cursor < len(e.History) && e.History[e.Cursor].Step == step {
		result := e.History[e.Cursor].Result
		e.Cursor++
		return result
	}
	result := sideEffect()
	e.History = append(e.History, HistoryEvent{Step: step, Result: result})
	e.Cursor++
	return result
}

func chargeCard() string {
	return "charged 42.00"
}

func reserveInventory() string {
	return "reserved"
}

func orderWorkflow(engine *DurableExecutionEngine) []string {
	results := []string{}
	results = append(results, engine.RunStep("chargeCard", chargeCard))
	results = append(results, engine.RunStep("reserveInventory", reserveInventory))
	return results
}

func main() {
	firstRun := &DurableExecutionEngine{}
	firstResults := orderWorkflow(firstRun)
	fmt.Println(firstResults)

	savedHistory := firstRun.History

	afterCrash := &DurableExecutionEngine{}
	afterCrash.LoadHistory(savedHistory)
	replayedResults := orderWorkflow(afterCrash)
	fmt.Println(replayedResults)

	if !reflect.DeepEqual(firstResults, replayedResults) {
		panic("replay diverged from original execution")
	}
}
```
