---
name: Workflow Engine
slug: workflow-engine
family: 23-workflow-orchestration
category: workflow orchestration
aliases: [Durable Execution Engine, Orchestration Engine, Durable Workflow Runtime]
first_described: "Workflow Management Coalition, founded May 1993, published the Workflow Reference Model in 1995. The modern durable-execution framing traces through Amazon Simple Workflow Service to Uber's Cadence, open sourced 2017, and its fork Temporal, founded around 2019 by the same two engineers who co-created Amazon SWF"
maturity: established
related: [saga, choreography, queue-based-load-leveling, orchestrator-worker]
incompatible_with: []
verified: 2026-08-22
---

# Workflow Engine

## 1. Name, aliases, and lineage

A workflow engine is a dedicated runtime that coordinates a multi-step process, a
sequence of calls, waits, human approvals, and error and retry logic, as one durable
unit of execution, so the process survives a crash, a restart, or a delay measured in
days rather than seconds. It is also called a durable execution engine or an
orchestration engine.

The discipline this pattern grew out of has two distinct lineages. Business Process
Management, described as a formal discipline since the early 1990s, evolved from
Business Process Reengineering, an approach that began in the early 1990s and focused
on the analysis and design of workflows within an organization
([Wikipedia, Business process
management](https://en.wikipedia.org/wiki/Business_process_management), verified
2026-08-22). The **Workflow Management Coalition** was founded in **May 1993** by IBM,
Hewlett-Packard, Fujitsu, ICL, Staffware, and roughly 300 other software and services
firms, to define standards for interoperability between workflow management systems.
In 1995 it published the **Workflow Reference Model**, which forms the basis of most
process and workflow software in use today, and it later produced XPDL, an XML process
definition language adopted by around 60 tools ([Wikipedia, Workflow Management
Coalition](https://en.wikipedia.org/wiki/Workflow_Management_Coalition), verified
2026-08-22). Wikipedia states the coalition regarded its work as complete as of 2019
and disbanded, while the organization's own live site still self-describes as active
and operating through 2026 ([wfmc.org](https://www.wfmc.org/), verified 2026-08-22).
Both sources are cited here, and the conflict is left unresolved rather than papered
over.

The executable-process side of this lineage runs through **BPEL**. IBM's Web Services
Flow Language and Microsoft's XLANG were the two competing 2001-era predecessors. In
April 2003, BEA Systems, IBM, Microsoft, SAP, and Siebel submitted BPEL4WS 1.1 to
OASIS, and on September 14, 2004 the OASIS technical committee renamed the effort
WS-BPEL 2.0, which was published on April 11, 2007. In June 2007 several of the same
vendors published BPEL4People and WS-HumanTask, an explicit admission that raw BPEL
could not express a human-approval step and needed an extension to do so
([Wikipedia, Business Process Execution
Language](https://en.wikipedia.org/wiki/Business_Process_Execution_Language), verified
2026-08-22).

The modern durable-execution framing has a tighter, more precisely dated lineage.
Samar Abbas and Maxim Fateev co-created Amazon Simple Workflow Service. Abbas went on
to build Azure's Durable Task Framework at Microsoft, the direct ancestor of Azure
Durable Functions, and Fateev built the Amazon Flow Framework. In 2015 the two reunited
at Uber to build Cadence, which Uber's own documentation describes as open source
since 2017 ([temporal.io/about](https://temporal.io/about); [GitHub,
cadence-workflow/cadence](https://github.com/cadence-workflow/cadence), verified
2026-08-22). Temporal is a fork of Cadence built by the same two founders. The
`temporalio` GitHub organization was created on 2019-10-13 per the GitHub API, a
machine-readable primary source that corroborates the commonly cited 2019 founding
date, though it is technically the date the GitHub org was created rather than a
confirmed date of legal incorporation
([api.github.com/orgs/temporalio](https://api.github.com/orgs/temporalio), verified
2026-08-22).

## 2. Problem and context

A process that spans more than one service call, or that waits on a timer or a human
response, cannot safely keep its state only in a running process's memory. Temporal's
own framing states plainly that its guarantee is that an application "will run to
completion" and that if something goes wrong, such as a power outage, "it guarantees
that your application can pick up right where it left off," by keeping a history of
every step ([docs.temporal.io, Understanding
Temporal](https://docs.temporal.io/evaluate/understanding-temporal), verified
2026-08-22).

Amazon's own description of the ancestor service states the same pain from the other
direction. Simple Workflow Service exists so a person can "build, run, and scale
background jobs that have parallel or sequential steps," coordinating work "without
worrying about underlying complexities, such as tracking progress and maintaining task
state," for tasks that are "long-running, or that may fail, time out, or require
restarts," with execution state maintained durably so a failure in one component does
not take the whole application down with it. The same page now steers new users toward
AWS Step Functions as the modern successor for most use cases
([docs.aws.amazon.com, What is Amazon Simple Workflow
Service](https://docs.aws.amazon.com/amazonswf/latest/developerguide/swf-welcome.html),
verified 2026-08-22).

Azure states the same problem in code terms. Durable Functions "lets you build stateful
workflows in a serverless environment by writing orchestrator, activity, and entity
functions in code," and its runtime "manages state, checkpoints, retries, and recovery
so your workflows can run reliably for long periods"
([learn.microsoft.com, Durable Functions
overview](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview),
verified 2026-08-22).

Read together, the pain three separate vendors independently describe is the same.
losing execution state on a crash, hand-writing retry and recovery logic per process,
and tracking step-by-step state across an execution that can span months. A workflow
engine exists to take that job away from application code and put it in a runtime built
for exactly that purpose.

## 3. Forces

**Determinism versus replay.** Temporal states that "Workflow code must be
deterministic to support replay," and that non-deterministic work such as an API call,
an LLM call, or a database query belongs in an Activity, not in Workflow code
([docs.temporal.io, Workflow
Definition](https://docs.temporal.io/workflow-definition), verified 2026-08-22). Azure
states the identical structural constraint independently. "Orchestrator code must be
deterministic," because "the Durable Task runtime uses event sourcing and replay to
rebuild orchestrator state, so nondeterministic code can cause failures or deadlocks"
([learn.microsoft.com, Programming model
overview](https://learn.microsoft.com/en-us/azure/durable-task/common/programming-model-overview),
verified 2026-08-22). Two vendors, arrived at independently, confirm this is a
structural force of the replay-based durability approach itself, not a quirk of one
product.

**Versioning code under an execution that is still running.** A Workflow Execution can
run for months, yet the platform requires the code to stay deterministic, so a code
change that reorders, adds, or removes an await on an Activity or a timer can break
replay for every already-running instance. Temporal documents two mechanisms to resolve
this. a `patched()` API that opens "a logical branch in a Workflow for a specific
change, similar to a feature flag," and Worker Versioning, which tags workers so old
code paths and new code paths run on the workers built for them
([docs.temporal.io, Workflow
Versioning](https://docs.temporal.io/develop/typescript/versioning), verified
2026-08-22).

**State size and history growth against durability.** Temporal logs a warning past
10,240 recorded events, and terminates a Workflow Execution outright past 51,200
events, 2,000 updates, or 10,000 signals. The documented answer is Continue-As-New,
which closes the current execution and opens a fresh one with the same logical
identity and an empty history ([docs.temporal.io, Event
History](https://docs.temporal.io/workflow-execution/event), verified 2026-08-22).

**Engine-imposed structure versus application flexibility.** AWS resolves this
tension with two workflow types carrying genuinely different guarantees rather than a
single configurable knob. Standard offers exactly-once execution, runs up to a year,
and keeps its execution history in the service itself, at 2,000 executions started per
second. Express offers at-least-once execution, runs up to five minutes, sends its
history to CloudWatch instead of keeping it in the service itself, and supports
100,000 executions started per second ([docs.aws.amazon.com, What is Step
Functions](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html), verified
2026-08-22). Durability and an in-service audit trail trade directly against
throughput and cost. AWS's own model gives no way to have both at once.

## 4. Applicability and non-applicability

**Reach for a workflow engine when.**

- The business process is expected to run past a few minutes, spans multiple
  services, or needs a wait step. AWS's own guidance is explicit that when "your
  business process is expected to take longer than five minutes for a single
  execution, you should choose Standard," naming an ETL pipeline and a
  human-approval step as examples
  ([docs.aws.amazon.com, What is Step
  Functions](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html),
  verified 2026-08-22).
- The process needs a human-in-the-loop step, a saga-style compensating rollback,
  or state that accumulates over a long lifetime. Temporal names transactions,
  business processes, entity lifecycle, repeatable operations, data and AI
  pipeline orchestration, human-in-the-loop steps, and the saga pattern as its own
  stated use-case categories
  ([docs.temporal.io, Use cases and design
  patterns](https://docs.temporal.io/evaluate/use-cases-design-patterns), verified
  2026-08-22).
- The step logic already involves calling more than one downstream system with
  retry and rollback requirements, where hand-writing that recovery logic per
  process is the real cost being avoided (dimension 2).

**Do not reach for a workflow engine when.**

- The task is a single, short, synchronous operation. Step Functions' own two-tier
  design, Standard at a five-minute lower bound for its use case and Express
  capped at five minutes for its own, both assume a process with more than one
  step worth durable tracking. a task with no branching, no wait, and no external
  call has no engine work to durably record. This is the entry's own inference
  from AWS's stated design boundary, not a directly quoted AWS warning, and is
  marked here as engineering judgement rather than a sourced claim.
- The process is stateful in a way the engine's determinism rules forbid without
  workaround. Azure's orchestrator code, for example, cannot call a random-number
  generator, read the system clock, or perform direct I/O, all of which must move
  into an Activity function instead
  ([learn.microsoft.com, Programming model
  overview](https://learn.microsoft.com/en-us/azure/durable-task/common/programming-model-overview),
  verified 2026-08-22). A process built around exactly those calls needs a
  redesign before it fits the pattern at all.
- Worth stating honestly. across every Temporal document fetched for this entry,
  no vendor page states a case where Temporal itself is the wrong choice. AWS and
  Azure both draw an explicit line (a five-minute product boundary, a determinism
  rule with a named workaround), while Temporal's own documentation is oriented
  toward adoption more than caveats. That asymmetry across vendors is itself
  worth naming rather than smoothing into invented balance.

## 5. Structure

Vendor terminology differs enough to be worth a direct comparison table rather than one
shared vocabulary.

| Concept | Temporal | AWS Step Functions | Azure Durable Functions | Camunda / Zeebe |
|---|---|---|---|---|
| The definition | Workflow Definition, code | State machine, JSON in Amazon States Language | Orchestrator function, code | BPMN process, XML with a visual model |
| The running instance | Workflow Execution | Execution | Orchestration instance | Process instance |
| A unit of work | Activity | Task, a state that a service performs | Activity function | Job, run by a job worker |
| The durable log | Event History | Execution history, kept in the service for Standard, sent to CloudWatch for Express | Rebuilt via event sourcing and replay | Not separately named in the fetched docs |
| The code executor | Worker, polling a Task Queue, external to the service | Work performed via service integrations or an external Activity worker | Not separately named beyond the Activity function itself | Job worker, polls for jobs and reports completion |
| Human-interaction primitive | Signals and Updates plus an Activity | Wait for Callback, `.waitForTaskToken` | Human interaction pattern (not independently re-verified in this pass) | Not covered in the fetched docs |

Temporal states plainly that "Worker Processes are external to a Temporal Service. The
Temporal Service itself does not execute developer code"
([docs.temporal.io, Workers](https://docs.temporal.io/workers), verified 2026-08-22).
The Amazon States Language is a JSON-based language describing a state machine
declaratively, with eight state types, `Task`, `Choice`, `Parallel`, `Map`, `Pass`,
`Wait`, `Succeed`, and `Fail`
([states-language.net](https://states-language.net/spec.html), verified 2026-08-22).

## 6. ASCII structure diagram

```
              +----------------------+
              | Workflow Definition   |
              | (code or JSON/BPMN)   |
              +-----------+----------+
                          |
                          v
              +----------------------+
              |  Engine / Orchestrator|
              |  (durable event log)  |
              +-----------+----------+
                    ^      |
        result      |      | task assignment
        recorded    |      v
              +----------------------+
              |  Worker pool          |
              | (polls a task queue)  |
              +-----------+----------+
                          |
                          v
              +----------------------+
              | External services,    |
              | APIs, databases        |
              +----------------------+
```

## 7. Dynamics

```
1. A client starts a Workflow Execution from a Workflow Definition and an input.
2. The engine records the start as the first entry in the durable event log.
3. A worker polls its task queue, picks up the next unit of work, and runs it.
4. The worker returns a result, which the engine records as a new log entry.
5. The engine evaluates the definition against the updated log and assigns the
   next unit of work, or waits on a timer or a human response.
6. If the worker or the process hosting it crashes, a new worker replays the
   event log from the start to rebuild in-memory state, then resumes exactly
   at the next unresolved step, never re-running a step whose result is
   already recorded.
7. When the log grows large enough to threaten replay cost, the engine closes
   the execution and opens a new one carrying the same logical identity and a
   fresh, empty log.
8. The execution ends when the definition reaches a terminal state, its result
   recorded as the final log entry.
```

## 8. Implementation variants

**Temporal.** The Workflow and Activity split places all orchestration logic, which
must be deterministic and replay-safe, in the Workflow, and everything that touches the
outside world, an API call, a database query, an LLM call, file I/O, in an Activity
([docs.temporal.io, Workflows](https://docs.temporal.io/workflows), verified
2026-08-22). On replay, "Temporal doesn't restore memory from a snapshot. It starts the
Workflow code from the beginning, replays the Event History step by step," and reuses
each recorded Activity result rather than recomputing it. **Signals** are asynchronous,
fire-and-forget write requests that change Workflow state and are recorded in the Event
History. **Queries** are read-only, never block, and never add an entry to the Event
History ([docs.temporal.io, Workflow message
passing](https://docs.temporal.io/encyclopedia/workflow-message-passing), verified
2026-08-22). A Worker Process continuously polls a Task Queue, executes Workflow or
Activity code in response, and returns results to the service, which is solely
responsible for assigning the next task
([docs.temporal.io, Workers](https://docs.temporal.io/workers), verified 2026-08-22).
**Continue-As-New** closes a Workflow Execution and atomically opens a new one under
the same Workflow ID with a fresh, empty Event History, avoiding the race that a
manual close-then-restart would carry. Guidance names long-running loops, high
message-volume workflows, and indefinite entity workflows, such as an account or a
subscription, as the cases that need it
([docs.temporal.io, Workflow
Execution](https://docs.temporal.io/workflow-execution), verified 2026-08-22;
[temporal.io/blog, very long-running
workflows](https://temporal.io/blog/very-long-running-workflows), verified 2026-08-22).

**AWS Step Functions.** The Amazon States Language defines a state machine in JSON, with
`StartAt` naming the entry state and `States` holding every named state object. Three
service-integration patterns, distinguished by the `Resource` field's suffix, cover
different needs. Request Response progresses "immediately after it receives an HTTP
response," Run a Job (`.sync`) waits for a job to finish, and Wait for a Callback with a
Task Token (`.waitForTaskToken`) waits until an external system returns the token
through a callback, the mechanism behind a human-approval step
([docs.aws.amazon.com, Connect to a
resource](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html),
verified 2026-08-22). Standard and Express differ across execution semantics, maximum
duration, throughput, and price, covered fully in dimension 3, and the workflow type is
fixed once a state machine is created.

**Azure Durable Functions.** An orchestrator function is real code, not a declarative
schema, and Microsoft states it plainly. "They define workflows by using procedural
code. No declarative schemas or designers are needed," and the runtime "automatically
checkpoint execution progress when the function calls an await or yield operator"
([learn.microsoft.com, Durable
orchestrations](https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-orchestrations),
verified 2026-08-22). The mechanism behind this is event sourcing. "Instead of directly
storing the current state of an orchestration, the Durable Task Framework uses an
append-only store to record the full series of actions the function orchestration
takes," and replay reruns the orchestrator code from the start, reusing each recorded
Activity result rather than calling it again. The documented determinism constraints are
specific and enforced. no `DateTime.Now` or equivalent, use `context.CurrentUtcDateTime`
instead; no `Guid.NewGuid()`, use `context.NewGuid()`, which produces a deterministic
Type 5 UUID; no direct I/O or bindings inside the orchestrator, since replay "can cause
duplicate I/O with external systems"; no thread-blocking sleep calls, use a durable
timer instead; and JavaScript and Python orchestrators must be declared as plain
generator functions, never `async`, since neither runtime guarantees deterministic
behavior for async code
([learn.microsoft.com, Code
constraints](https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-code-constraints),
verified 2026-08-22). The runtime throws a `NonDeterministicOrchestrationException` on
some detected violations, but the docs state plainly this detection "won't catch all
violations." Support for the in-process .NET hosting model ends November 10, 2026, with
migration to the isolated worker model recommended.

**Netflix Conductor.** Netflix's own repository states that "Effective December 13,
2023, Netflix will discontinue maintenance of Conductor OSS on GitHub." The repository
is not archived, and a community continuation, `conductor-oss/conductor`, states
plainly that it "is the continuation of the original Netflix Conductor repository after
Netflix contributed the project to the open-source foundation," with Orkes as its
primary maintainer, offering an event-driven workflow runtime aimed at applications and
AI agents, under an Apache 2.0 license
([GitHub, Netflix/conductor](https://github.com/Netflix/conductor);
[GitHub, conductor-oss/conductor](https://github.com/conductor-oss/conductor), verified
2026-08-22).

**Camunda and Zeebe.** BPMN, an XML document with a visual representation, is described
by Camunda as "source code and documentation in one artifact," containing everything a
workflow engine or a modeling tool needs to interpret a process
([docs.camunda.io, BPMN
primer](https://docs.camunda.io/docs/components/modeler/bpmn/bpmn-primer/), verified
2026-08-22). Zeebe's own internal mechanism is a genuinely different structure from the
replay-based engines above. it is a stream-processing state machine over an append-only
log. a stream processor reads commands sequentially, interprets each against an
entity's current state, and publishes an event recording the new state
([docs.camunda.io, Internal
processing](https://docs.camunda.io/docs/components/zeebe/technical-concepts/internal-processing/),
verified 2026-08-22). Zeebe's current state is therefore updated incrementally as each
event is applied, rather than rebuilt by replaying a full workflow-instance history from
the start on every resume the way Temporal, Cadence, and Azure Durable Functions do.
This distinction is the entry's own synthesis of Zeebe's documented internal mechanics,
since no fetched Camunda page directly names Temporal or Cadence for comparison, and it
is flagged here as such rather than presented as a direct Camunda-authored claim.

**Recent entrants, Restate and DBOS.** Both are real, active projects as of this
verification date, positioned against the heavier separate-orchestrator topology of
the engines above. Restate ships as a single self-contained binary. "Restate journals
every step so handlers resume exactly where they left off," recording each operation
and its result and replaying past completed steps on a crash
([restate.dev](https://restate.dev/), verified 2026-08-22). DBOS instead uses an
application's own Postgres database as the durability layer, with no separate
orchestrator service at all. "While your application runs, DBOS checkpoints those
workflows and steps to a Postgres database," and on restart it "restarts each
interrupted workflow by calling it with its checkpointed inputs," skipping any step
whose output is already checkpointed
([dbos.dev](https://www.dbos.dev/), verified 2026-08-22). Both still implement the
same record-and-skip mechanism as the older engines. the change is operational, a
lighter-weight runtime, not a new durability mechanism.

## 9. Known production uses

1. **Uber, Cadence.** A Secrets Management Platform's "Secret Lifecycle Manager based
   on Cadence workflows" manages roughly 20,000 secret rotations a month with no
   human step, coordinating a Secret Provider API and Uber's own deployment platform
   ([uber.com/blog, multi-cloud secrets management
   platform](https://www.uber.com/blog/building-ubers-multi-cloud-secrets-management-platform/),
   verified 2026-08-22). Separately, Uber's IAM policy simulation service uses
   Cadence for "sub-minute impact analysis" of a proposed access-policy change,
   stating Cadence provides the durability and fault tolerance needed to "execute all
   steps within the replay logic accurately" while many simulations run at once
   ([uber.com/blog, IAM policy
   changes](https://www.uber.com/blog/adding-determinism-and-safety-to-uber-iam-policy-changes/),
   verified 2026-08-22).
2. **Netflix, Conductor.** Netflix built Conductor because a prior pub or sub
   choreography approach embedded process flow inside the code of multiple
   applications with no central visibility and no pause, resume, or restart control.
   About a year after launch it had orchestrated more than 2.6 million process
   flows, used for studio content ingestion and title and encoding pipelines
   ([netflixtechblog.com, Netflix Conductor, a microservices
   orchestrator](https://netflixtechblog.com/netflix-conductor-a-microservices-orchestrator-2e8d4771bf40),
   verified 2026-08-22).
3. **Temporal, three independently confirmed customer case studies.** Emergent, an
   AI app-building platform, runs more than 1 billion Temporal Actions a month, with
   each build calling dozens of language-model requests and hundreds of tool
   executions over 10 to 30 minutes
   ([temporal.io, Emergent case
   study](https://temporal.io/resources/case-studies/emergent), verified
   2026-08-22). VEED.IO, an AI video platform, exports around 3 million videos a
   month and runs 4 million Temporal Activities a day, and reports that a feature
   needing five days to build with hand-written error handling could now ship the
   same day
   ([temporal.io, VEED.IO case
   study](https://temporal.io/resources/case-studies/veedio-video-workflows), verified
   2026-08-22). ShareChat, an Indian social platform serving 325 million monthly
   active users, runs more than 450 million actions a month across roughly 50
   million monthly billing transactions, and reports its debit success rate rose
   from about 95 percent to more than 99.9 percent after moving billing off a cron-
   based approach, a figure attributed by name to Shivam Yadav, an SDE-3 on the
   payments team
   ([temporal.io, ShareChat case
   study](https://temporal.io/resources/case-studies/sharechat), verified
   2026-08-22). Temporal's own homepage names DoorDash, Snap, Cloudflare, GitLab, and
   several other companies as customers, and this entry cites those as
   vendor-claimed rather than independently confirmed, since their own engineering
   accounts could not be independently fetched in this research pass
   ([temporal.io](https://temporal.io/), verified 2026-08-22).

## 10. Consequences

**Positive.**

- A crash or restart no longer loses execution state, and the recovery logic that
  would otherwise need to be hand-written per process moves into the runtime
  instead, as stated directly in dimension 2.
- The durable event log doubles as an audit trail and a visibility surface for an
  operator, a property Netflix names explicitly as the reason it moved off plain
  pub or sub choreography.
- Retry, timer, and compensation machinery is provided by the platform, so a saga's
  compensating-transaction logic is the only code a team still has to write, per
  Temporal's own framing in dimension 13.
- Event-driven scaling and Continue-As-New together let an engine handle both a
  bursty short workload and an indefinite entity workflow inside the same
  platform.

**Negative.**

- Determinism is a real constraint, and it costs developer discipline. an
  accidental system-clock read, a random-number call, or a direct I/O call inside
  orchestration code produces a replay failure that a plain function would never
  hit.
- Versioning live code under a running instance is a genuinely hard problem, and
  every replay-based engine surveyed needs an explicit mechanism, a patch API or a
  worker-versioning scheme, to change orchestration code safely.
- Event-history growth is a real, quantified limit, not a theoretical one. a
  workflow that never calls Continue-As-New can be terminated outright once it
  crosses Temporal's documented thresholds.
- Standard, Express, and equivalent split designs across vendors mean the
  exactly-once versus at-least-once choice is made once, up front, and an
  at-least-once engine forces every step to be written idempotently.

## 11. Failure modes and misuse

**The non-determinism error.** This is the failure mode the whole pattern is built
around avoiding, and it recurs across both surveyed replay-based engines. A mismatch
between a newly emitted command and the stored event history surfaces as a
non-determinism error, and a code change that reorders or adds an await on an Activity
or a timer can trigger it for every already-running instance unless versioned first,
per dimension 3. Azure's identical structural constraint confirms this is intrinsic to
the replay-based approach itself, not a Temporal-specific defect. Real, dated evidence
that this is a recurring operational pain, not a rare edge case, comes from a multi-
year trail of GitHub issues asking for better diagnosability. Cadence issue 7640,
opened January 23, 2026 and open at verification, "Non deterministic error with local
activity in Async function or procedure calls"; Cadence issue 2932, closed December 30,
2019, a feature request to add visibility into non-deterministic-error workflows;
Cadence issue 2801, closed November 1, 2024, requesting workflow code position be
exposed in decision events specifically to help diagnose these errors; and Temporal
issue 1756, requesting a dedicated failure-cause value for non-determinism instead of a
generic task-failure bucket, meaning the vendor itself initially lumped this error class
in with ordinary failures until asked to separate it
([GitHub, cadence-workflow/cadence
issues](https://github.com/cadence-workflow/cadence/issues); [GitHub,
temporalio/temporal issue
1756](https://github.com/temporalio/temporal/issues/1756), verified 2026-08-22). Stated
honestly, no fetched documentation page describes the operational blast radius once a
non-determinism error actually fires in production, whether the task retries
indefinitely, whether the execution becomes stuck, or whether the worker crash-loops,
and that gap is left open rather than filled with a guess.

**Unbounded event-history growth.** Covered with exact thresholds in dimension 3,
mitigated by Continue-As-New.

**Infrastructure incidents, scoped honestly.** Temporal Cloud's own public status page
lists real, dated incidents, an onboarding restriction from August 20 to 21, 2026, a
period of higher latency for GCP us-west1 customers on August 20, 2026, and a brief
period of higher latency and error rate for the Cloud Ops API on August 13, 2026
([status.temporal.io](https://status.temporal.io/), verified 2026-08-22). These are
real first-party evidence of production failure in a managed workflow-engine service,
but they are infrastructure and latency incidents, not documented cases of the
non-determinism failure mode itself causing an outage. No third-party postmortem
attributing a real production incident to non-determinism or to event-history growth
was found in this research pass, and that absence is stated here rather than papered
over with an invented example.

## 12. Trade-off matrix

| Approach | Durability across a crash | Central visibility and audit trail | Coupling | Operational complexity |
|---|---|---|---|---|
| Dedicated workflow engine (Temporal, Step Functions, and similar) | Yes, by design, via a durable event log | Yes, the log itself is the audit trail | Steps route through a central orchestrator | Highest, determinism and versioning discipline required |
| Choreography, event-driven with no central coordinator | Depends entirely on each service's own durability, not provided by the pattern | No single place to see the whole process, per Richardson's saga framing | Loosely coupled, services react to events independently | Lower per service, higher to trace end to end |
| Hand-rolled state machine in an application database | Only as durable as the team's own recovery code, not sourced independently in this pass | Only as visible as the team's own tooling, not sourced independently in this pass | Tightly coupled to the specific application | Not independently sourced in this pass, marked as engineering judgement |
| Synchronous call chain with manual retry logic | None past the calling process's own lifetime, not sourced independently in this pass | None beyond application logs, not sourced independently in this pass | Tightly coupled, callers block on callees | Not independently sourced in this pass, marked as engineering judgement |

The choreography row is grounded in Chris Richardson's saga-pattern framing, which
defines a choreography-based saga as services that "publish domain events that
autonomously trigger subsequent steps," reacting to each other with no central
coordination ([microservices.io, Saga](https://microservices.io/patterns/data/saga.html),
verified 2026-08-22). A broader, non-saga-specific source comparing orchestration and
choreography directly could not be located and independently fetched in this research
pass, so the hand-rolled and synchronous-chain rows are marked honestly as this entry's
own reasoning rather than a sourced claim.

## 13. Related and incompatible patterns

**Saga.** A workflow engine is frequently the concrete runtime that implements the
orchestration-style variant of a saga. Temporal states its Saga helper tracks
compensations registered before each forward step, running them in reverse order on
failure, and frames the engine's real contribution this way. "by running your code with
Temporal, you automatically get your state saved and retries on failure at any level,"
so the only code a team still has to write is the compensating, undo, logic per step
([temporal.io/blog, Saga pattern made
easy](https://temporal.io/blog/saga-pattern-made-easy), verified 2026-08-22). Richardson's
own canonical page defines the orchestration variant as one where "an orchestrator
tells the participants what local transactions to execute"
([microservices.io/patterns/data/saga](https://microservices.io/patterns/data/saga.html),
verified 2026-08-22).

**Choreography.** The event-driven, no-central-coordinator alternative to engine-based
orchestration, covered in the trade-off matrix above.

**Queue-Based Load Leveling.** A buffering pattern for a burst that arrives faster
than a workflow engine's own worker pool can provision, giving the engine time to
scale rather than dropping or degrading the incoming work.

**Orchestrator-Worker.** The closely related coordination pattern in the AI-agentic
family, where a lead process assigns work to subagents rather than to Activities.
Temporal names AI agent orchestration among its own stated use cases in dimension 4,
and the two patterns overlap in intent though not in mechanism.

**Sibling patterns in this family, not yet in this catalogue.** State Machine
Workflow, Human Task, Compensation Handler, Durable Execution, and Outbox Inbox Pair
are each queued as their own entries in this family. Determinism and replay, the
mechanism this entry describes at the level needed to explain a workflow engine's
structure, is the deeper subject of the future Durable Execution entry, and this entry
deliberately does not duplicate that depth.

## 14. Refactoring path in and out

**Introducing it.** Start from one well-scoped, long-running process with clear step
boundaries before reaching for an advanced feature. Pick the simplest policy shape
first, a plain Workflow and Activity split, or a Standard state machine with a small
number of states, and confirm the process actually needs durability across a crash
before adding it. Instrument event-history size from the very first workflow, so
growth toward Continue-As-New territory is visible well before a hard limit is hit,
rather than discovered as an outage.

**Removing it.** Two honest reasons exist. The process became short and stateless
enough that no crash-durability guarantee is worth the determinism and versioning
tax, or the team moved to a lighter, database-native durable-execution runtime, in
the shape of Restate or DBOS from dimension 8, rather than a separate orchestrator
service, keeping the same record-and-skip mechanism with less operational surface.

## 15. Testing and verification

- **Temporal's time-skipping test environment.** The `@temporalio/testing` package's
  `TestWorkflowEnvironment` provides "an in-memory implementation of Temporal Server
  that supports skipping time," fast-forwarding a timer or a sleep call so a
  workflow with a multi-day wait completes in seconds inside a test suite
  ([docs.temporal.io, Testing
  suite](https://docs.temporal.io/develop/typescript/testing-suite), verified
  2026-08-22).
- **AWS Step Functions Local is deprecated.** AWS states directly. "Step Functions
  Local is unsupported. Step Functions Local does not provide feature parity and is
  unsupported," and points instead to the TestState API "to unit test your state
  machine logic before deploying to your AWS account"
  ([docs.aws.amazon.com, Step Functions
  Local](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-local.html),
  verified 2026-08-22).
- **The TestState API, the current recommended approach.** It executes the
  definition of a single state without creating or updating a real state machine,
  at three inspection levels, `INFO` (output or error only), `DEBUG` (the full
  input and output filter pipeline at every stage), and `TRACE` (raw HTTP request
  and response for an HTTP task). Service-integration results can be mocked, so a
  Map, Parallel, Activity, or callback-token state can be tested with no live AWS
  call and no IAM permission needed
  ([docs.aws.amazon.com, Test state
  isolation](https://docs.aws.amazon.com/step-functions/latest/dg/test-state-isolation.html),
  verified 2026-08-22).

## 16. Observability signals

- **Temporal's own metrics.** `temporal_activity_schedule_to_start_latency` and
  `temporal_workflow_task_schedule_to_start_latency` measure the time a task waits
  before a worker picks it up, and a rising value points at queue backlog or too
  few workers. `temporal_workflow_endtoend_latency` is the total time from schedule
  to completion for a run. `temporal_sticky_cache_hit` and
  `temporal_sticky_cache_miss` show whether cached execution state is being reused
  effectively, and `temporal_sticky_cache_total_forced_eviction` signals worker
  memory pressure ([docs.temporal.io, SDK
  metrics](https://docs.temporal.io/references/sdk-metrics), verified 2026-08-22,
  noted here that this page's content was retrieved through the fetch tool's own
  summarization rather than raw text, so exact metric names should be spot checked
  against the live reference before being quoted elsewhere). The failure signature
  for a non-determinism error surfaces as
  `temporal_workflow_task_execution_failed` carrying a `failure_reason` tag equal
  to `NonDeterminismError`, a directly alertable signal.
- **AWS Step Functions' own recommended baseline.** "To establish a baseline you
  should, at a minimum, monitor the following metrics. `ExecutionsStarted`,
  `ExecutionsTimedOut`," with `ExecutionsFailed` and `ExecutionsAborted` completing
  the picture of a struggling state machine, plus `ExecutionThrottled` for
  state-transition throttling. AWS states plainly that "CloudWatch metrics are
  delivered on a best-effort basis. The completeness and timeliness of metrics are
  not guaranteed"
  ([docs.aws.amazon.com, Monitoring with
  CloudWatch](https://docs.aws.amazon.com/step-functions/latest/dg/procedure-cw-metrics.html),
  verified 2026-08-22). Step Functions has no metric directly analogous to
  Temporal's non-determinism signature, since a state machine does not replay
  client-side orchestration code from history the way Temporal does. this is the
  entry's own reasoned inference from the fetched metrics list, not a directly
  sourced negative claim.

## 17. Security and privacy implications

A workflow engine's entire value depends on durably recording every step's input and
output, sometimes for months, and that persisted record is a long-lived surface for
sensitive data if the workflow's own inputs carry it.

**Temporal's answer is client-side encryption.** "The Temporal Service persists data
from your Workflow Executions, including inputs, outputs, and results," and the
documented mitigation is a Data Converter paired with a Codec Server the organization
runs itself. "With encryption enabled, data exists unencrypted only on the Client and
the Worker process, on hosts that you control," so payloads on the Temporal Service,
whether self-hosted or on Temporal Cloud, "remain encrypted." Access to decoded
payloads through the web UI or CLI is controlled separately by the organization, via
network isolation or an authentication layer of its own choosing
([docs.temporal.io, Data
conversion](https://docs.temporal.io/dataconversion), verified 2026-08-22). The
responsibility for who can see decoded data is placed on the customer, not on
Temporal itself.

**AWS Step Functions' answer is encryption at rest, with two distinct documented
facts.** First, a general warning that applies to tags and free-text name fields
specifically, not the full payload. "We strongly recommend that you never put
confidential or sensitive information, such as your customers' email addresses, into
tags or free-form text fields such as a Name field," since that data "may be used for
billing or diagnostic logs"
([docs.aws.amazon.com, Data
protection](https://docs.aws.amazon.com/step-functions/latest/dg/data-protection.html),
verified 2026-08-22). Second, Step Functions "always encrypts your data at rest using
transparent server-side encryption" by default, and an optional customer-managed KMS
key adds a second layer, framed explicitly for compliance. "you can secure customer
data that includes protected health information from unauthorized access." A useful
control follows from that second layer. "Execution Input, Output, Error, and Cause
will not be included for execution status change events for workflows that are
encrypted using your customer managed AWS KMS key," stripping sensitive payload data
from downstream event notifications. If that key is later deleted, "all encrypted
data associated with the workflow execution will remain encrypted and can no longer be
decrypted"
([docs.aws.amazon.com, Encryption at
rest](https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html),
verified 2026-08-22).

## 18. References

1. Wikipedia. *Business process management*.
   https://en.wikipedia.org/wiki/Business_process_management
   Verified 2026-08-22. Source of BPM's origin as a formal discipline and its
   evolution from Business Process Reengineering.
2. Wikipedia. *Workflow Management Coalition*.
   https://en.wikipedia.org/wiki/Workflow_Management_Coalition
   Verified 2026-08-22. Source of the May 1993 founding date, the 1995 Workflow
   Reference Model, XPDL, and the disbanded-as-of-2019 claim.
3. Workflow Management Coalition. Live site.
   https://www.wfmc.org/
   Verified 2026-08-22. Self-describes as active through 2026, conflicting with
   Wikipedia's disbanded claim, both cited honestly.
4. Wikipedia. *Business Process Execution Language*.
   https://en.wikipedia.org/wiki/Business_Process_Execution_Language
   Verified 2026-08-22. Source of the WSFL and XLANG predecessors, the OASIS
   submission and rename dates, and BPEL4People and WS-HumanTask.
5. Temporal. *About Temporal*.
   https://temporal.io/about
   Verified 2026-08-22. Source of the Abbas and Fateev lineage from AWS SWF
   through Azure's Durable Task Framework and the Amazon Flow Framework to
   Cadence and Temporal, plus current company metrics.
6. GitHub. *cadence-workflow/cadence*.
   https://github.com/cadence-workflow/cadence
   Verified 2026-08-22. Source of Cadence being open source since 2017 and its
   current maintained state.
7. GitHub API. *temporalio organization*.
   https://api.github.com/orgs/temporalio
   Verified 2026-08-22. Source of the 2019-10-13 GitHub organization creation
   date used as a proxy for Temporal's founding.
8. Temporal. *Understanding Temporal*.
   https://docs.temporal.io/evaluate/understanding-temporal
   Verified 2026-08-22. Source of Temporal's own durable-execution problem
   framing.
9. AWS. *What is Amazon Simple Workflow Service*.
   https://docs.aws.amazon.com/amazonswf/latest/developerguide/swf-welcome.html
   Verified 2026-08-22. Source of AWS SWF's original problem framing and AWS's
   current guidance to prefer Step Functions.
10. Microsoft Learn. *Durable Functions overview*.
    https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview
    Verified 2026-08-22. Source of Azure's own problem framing in code terms.
11. Temporal. *Workflow Definition*.
    https://docs.temporal.io/workflow-definition
    Verified 2026-08-22. Source of the determinism requirement and the
    non-determinism error mechanism.
12. Microsoft Learn. *Programming model overview*.
    https://learn.microsoft.com/en-us/azure/durable-task/common/programming-model-overview
    Verified 2026-08-22. Source of Azure's independent determinism constraint
    and the at-least-once Activity guarantee.
13. Temporal. *Workflow Versioning*.
    https://docs.temporal.io/develop/typescript/versioning
    Verified 2026-08-22. Source of the patching API and Worker Versioning
    mechanisms.
14. Temporal. *Event History*.
    https://docs.temporal.io/workflow-execution/event
    Verified 2026-08-22. Source of the exact event-history thresholds and
    Continue-As-New.
15. AWS. *What is Step Functions*.
    https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html
    Verified 2026-08-22. Source of the Standard versus Express comparison, the
    named use cases, and the five-minute applicability guidance.
16. Temporal. *Workflows*.
    https://docs.temporal.io/workflows
    Verified 2026-08-22. Source of the Workflow and Activity split.
17. Temporal. *Workflow message passing*.
    https://docs.temporal.io/encyclopedia/workflow-message-passing
    Verified 2026-08-22. Source of Signals and Queries.
18. Temporal. *Workers*.
    https://docs.temporal.io/workers
    Verified 2026-08-22. Source of the Worker and Task Queue mechanics.
19. Temporal. *Workflow Execution*.
    https://docs.temporal.io/workflow-execution
    Verified 2026-08-22. Source of the Continue-As-New use-case guidance.
20. Temporal. *Very long-running workflows*, engineering blog.
    https://temporal.io/blog/very-long-running-workflows
    Verified 2026-08-22. Source of additional Continue-As-New guidance.
21. AWS. *Connect to a resource*.
    https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html
    Verified 2026-08-22. Source of the three service-integration patterns.
22. Microsoft Learn. *Durable orchestrations*.
    https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-orchestrations
    Verified 2026-08-22. Source of the event-sourcing replay mechanism and the
    procedural-code framing.
23. Microsoft Learn. *Code constraints*.
    https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-code-constraints
    Verified 2026-08-22. Source of the full determinism constraint list.
24. GitHub. *Netflix/conductor*.
    https://github.com/Netflix/conductor
    Verified 2026-08-22. Source of the December 13, 2023 discontinued-maintenance
    statement.
25. GitHub. *conductor-oss/conductor*.
    https://github.com/conductor-oss/conductor
    Verified 2026-08-22. Source of the continuation project and Orkes as
    maintainer.
26. Camunda. *BPMN primer*.
    https://docs.camunda.io/docs/components/modeler/bpmn/bpmn-primer/
    Verified 2026-08-22. Source of the BPMN-as-source-and-documentation framing.
27. Camunda. *Internal processing, Zeebe technical concepts*.
    https://docs.camunda.io/docs/components/zeebe/technical-concepts/internal-processing/
    Verified 2026-08-22. Source of Zeebe's stream-processing mechanism.
28. Restate. Home page.
    https://restate.dev/
    Verified 2026-08-22. Source of the single-binary journal-based durability
    claim.
29. DBOS. Home page.
    https://www.dbos.dev/
    Verified 2026-08-22. Source of the Postgres-native checkpointing mechanism.
30. Uber Engineering Blog. *Building Uber's multi-cloud secrets management
    platform*.
    https://www.uber.com/blog/building-ubers-multi-cloud-secrets-management-platform/
    Verified 2026-08-22. Source of the Cadence secrets-rotation production use.
31. Uber Engineering Blog. *Adding determinism and safety to Uber IAM policy
    changes*.
    https://www.uber.com/blog/adding-determinism-and-safety-to-uber-iam-policy-changes/
    Verified 2026-08-22. Source of the Cadence IAM policy simulation production
    use.
32. Netflix Technology Blog. *Netflix Conductor, a microservices orchestrator*.
    https://netflixtechblog.com/netflix-conductor-a-microservices-orchestrator-2e8d4771bf40
    Verified 2026-08-22. Source of the 2.6 million process flows figure and
    Conductor's own origin story.
33. Temporal. *Emergent case study*.
    https://temporal.io/resources/case-studies/emergent
    Verified 2026-08-22. Source of the Emergent production figures.
34. Temporal. *VEED.IO case study*.
    https://temporal.io/resources/case-studies/veedio-video-workflows
    Verified 2026-08-22. Source of the VEED.IO production figures.
35. Temporal. *ShareChat case study*.
    https://temporal.io/resources/case-studies/sharechat
    Verified 2026-08-22. Source of the ShareChat production figures and the
    named quote.
36. Temporal. Home page.
    https://temporal.io/
    Verified 2026-08-22. Source of the vendor-claimed customer list, cited as
    such.
37. GitHub. *cadence-workflow/cadence issues*.
    https://github.com/cadence-workflow/cadence/issues
    Verified 2026-08-22. Source of the non-determinism diagnosability issue
    trail.
38. GitHub. *temporalio/temporal issue 1756*.
    https://github.com/temporalio/temporal/issues/1756
    Verified 2026-08-22. Source of the missing dedicated failure-cause request.
39. Temporal Cloud. Status page.
    https://status.temporal.io/
    Verified 2026-08-22. Source of the dated infrastructure incidents.
40. microservices.io. *Saga*, Chris Richardson.
    https://microservices.io/patterns/data/saga.html
    Verified 2026-08-22. Source of the orchestration versus choreography saga
    framing.
41. Temporal. *Saga pattern made easy*, engineering blog.
    https://temporal.io/blog/saga-pattern-made-easy
    Verified 2026-08-22. Source of Temporal's own Saga helper and its stated
    value proposition.
42. Temporal. *Testing suite*.
    https://docs.temporal.io/develop/typescript/testing-suite
    Verified 2026-08-22. Source of the time-skipping test environment.
43. AWS. *Step Functions Local*.
    https://docs.aws.amazon.com/step-functions/latest/dg/sfn-local.html
    Verified 2026-08-22. Source of the deprecation statement.
44. AWS. *Test state isolation*.
    https://docs.aws.amazon.com/step-functions/latest/dg/test-state-isolation.html
    Verified 2026-08-22. Source of the TestState API and its inspection levels.
45. Temporal. *SDK metrics*.
    https://docs.temporal.io/references/sdk-metrics
    Verified 2026-08-22. Source of the named Temporal metrics, noted as
    retrieved via the fetch tool's summarization.
46. AWS. *Monitoring Step Functions using CloudWatch*.
    https://docs.aws.amazon.com/step-functions/latest/dg/procedure-cw-metrics.html
    Verified 2026-08-22. Source of the recommended metrics baseline and the
    best-effort delivery statement.
47. Temporal. *Data conversion*.
    https://docs.temporal.io/dataconversion
    Verified 2026-08-22. Source of the Data Converter and Codec Server
    encryption architecture.
48. AWS. *Data protection in Step Functions*.
    https://docs.aws.amazon.com/step-functions/latest/dg/data-protection.html
    Verified 2026-08-22. Source of the tags and free-text-field sensitive-data
    warning.
49. AWS. *Encryption at rest for Step Functions*.
    https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html
    Verified 2026-08-22. Source of the default and customer-managed-key
    encryption model and the key-deletion consequence.
50. states-language.net. *Amazon States Language specification*.
    https://states-language.net/spec.html
    Verified 2026-08-22. Source of the eight state types and the JSON
    structure.

**Evidence grade.** established

**Most solid findings.** The Temporal, AWS, and Azure sources gave precise, directly
quotable mechanics for determinism, replay, versioning, event-history thresholds, and
testing. Three of Temporal's own case studies, Emergent, VEED.IO, and ShareChat, were
each independently fetched from their own dedicated case-study pages with concrete
figures and a named quote, giving this entry sourced production evidence rather than
vendor-logo claims alone. Uber's own two engineering blog posts on Cadence, and
Netflix's own blog post on Conductor's origin, are each a company's first-party
account of its own production use.

**Unverified or unclear.** The Workflow Management Coalition's active-versus-disbanded
status is a genuine, unresolved conflict between Wikipedia and the organization's own
live site, both cited. Temporal's exact founding date rests on a GitHub organization
creation timestamp used as a proxy, not a confirmed date of legal incorporation.
DoorDash, Snap, Cloudflare, and several other companies named on Temporal's own
homepage were not independently confirmed through each company's own engineering
account in this research pass, and are cited as vendor-claimed. The operational
consequence of a live non-determinism error firing in production, whether the task
retries, stalls, or crash-loops the worker, is not documented on any fetched page. No
third-party postmortem attributing a real outage to non-determinism or to
event-history growth was found. Zeebe's stream-processing mechanism was directly
sourced from Camunda's own docs, but the explicit comparison to Temporal and Cadence's
replay-based approach is this entry's own synthesis, not a direct Camunda-authored
claim. A general, non-saga-scoped source explicitly comparing orchestration and
choreography could not be located and independently fetched, so the hand-rolled and
synchronous-call rows of the trade-off matrix are marked as reasoning rather than
sourced claims.

## Code

### TypeScript, a durable step recorder that replays and skips completed steps

```typescript
type StepRecord = {
  name: string;
  output: string;
};

class DurableExecution {
  private log: StepRecord[] = [];

  private findCompleted(name: string): StepRecord | undefined {
    return this.log.find((r) => r.name === name);
  }

  async runStep(name: string, work: () => Promise<string>): Promise<string> {
    const existing = this.findCompleted(name);
    if (existing) {
      return existing.output;
    }
    const output = await work();
    this.log.push({ name, output });
    return output;
  }

  loadFrom(previous: StepRecord[]): void {
    this.log = [...previous];
  }

  snapshot(): StepRecord[] {
    return [...this.log];
  }
}

async function chargeCard(amount: number): Promise<string> {
  return "charge-" + amount;
}

async function reserveInventory(sku: string): Promise<string> {
  return "reserve-" + sku;
}

async function run(): Promise<void> {
  const execution = new DurableExecution();
  const charge = await execution.runStep("charge", () => chargeCard(4200));
  const reservation = await execution.runStep("reserve", () =>
    reserveInventory("sku-99")
  );

  const resumed = new DurableExecution();
  resumed.loadFrom(execution.snapshot());
  const chargeAgain = await resumed.runStep("charge", () => chargeCard(4200));

  console.log(charge, reservation, chargeAgain === charge);
}

run();
```

### Python, a saga orchestrator running compensations in reverse order on failure

```python
from dataclasses import dataclass, field
from typing import Callable, List


@dataclass
class Saga:
    compensations: List[Callable[[], None]] = field(default_factory=list)

    def step(self, forward: Callable[[], None], compensate: Callable[[], None]) -> None:
        forward()
        self.compensations.append(compensate)

    def rollback(self) -> None:
        while self.compensations:
            undo = self.compensations.pop()
            undo()


def reserve_credit(order_id: str) -> None:
    print("reserved credit for", order_id)


def release_credit(order_id: str) -> None:
    print("released credit for", order_id)


def reserve_inventory(order_id: str) -> None:
    print("reserved inventory for", order_id)


def release_inventory(order_id: str) -> None:
    print("released inventory for", order_id)


def ship_order(order_id: str) -> None:
    raise RuntimeError("carrier unavailable for " + order_id)


def place_order(order_id: str) -> bool:
    saga = Saga()
    try:
        saga.step(lambda: reserve_credit(order_id), lambda: release_credit(order_id))
        saga.step(
            lambda: reserve_inventory(order_id),
            lambda: release_inventory(order_id),
        )
        ship_order(order_id)
        return True
    except RuntimeError as failure:
        print("order failed, rolling back:", failure)
        saga.rollback()
        return False


if __name__ == "__main__":
    place_order("order-501")
```

### Go, a continue-as-new style loop that resets accumulated history past a threshold

```go
package main

import "fmt"

type EventLog struct {
	events    []string
	threshold int
}

func NewEventLog(threshold int) *EventLog {
	return &EventLog{threshold: threshold}
}

func (l *EventLog) Record(event string) {
	l.events = append(l.events, event)
}

func (l *EventLog) shouldContinueAsNew() bool {
	return len(l.events) >= l.threshold
}

func (l *EventLog) continueAsNew(carriedState string) {
	l.events = []string{"ContinueAsNew:" + carriedState}
}

func runIndefiniteWorkflow(iterations int, threshold int) []int {
	log := NewEventLog(threshold)
	resets := 0
	carried := "count=0"

	for i := 0; i < iterations; i++ {
		log.Record(fmt.Sprintf("tick-%d", i))
		if log.shouldContinueAsNew() {
			log.continueAsNew(carried)
			resets++
		}
	}
	return []int{resets, len(log.events)}
}

func main() {
	result := runIndefiniteWorkflow(23, 5)
	fmt.Println("resets:", result[0], "events remaining in log:", result[1])
}
```
