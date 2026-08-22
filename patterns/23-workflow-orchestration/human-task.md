---
name: Human Task
slug: human-task
family: 23-workflow-orchestration
category: workflow orchestration
aliases: [User Task, Manual Task, Human-in-the-Loop Step, Human Interaction Task]
first_described: "The Workflow Management Coalition's Automated Activity versus Manual Activity split, from its 1990s workflow reference terminology. Given a durable, orchestrated shape by the OASIS WS-BPEL Extension for People (BPEL4People) and WS-HumanTask specifications, 2007. Made a first-class element, split into User Task and Manual Task, by the OMG BPMN 2.0 specification, January 2011"
maturity: established
related: [workflow-engine, state-machine-workflow, saga]
verified: 2026-08-22
---

# Human Task

## 1. Name, aliases, and lineage

Human Task is the step inside a larger, otherwise-automated workflow where execution
pauses and waits for a person to act. approve, reject, review, enter data, or make a
judgment call, before the workflow can continue.

The Workflow Management Coalition's glossary carries the earliest confirmed root of the
concept, a binary split that predates BPMN by over a decade. WfMC defines an "Automated
Activity" as "a task or step in a business process that is executed by a software
system, rather than by a human," and a "Manual Activity" as "a task or step in a
business process that is executed by a human, rather than by a software system" ([wfmc.org,
Glossary](https://wfmc.org/glossary/), verified 2026-08-22). The same glossary defines a
"Worklist" as "a list of tasks that need to be completed, usually in the context of a
workflow management system," the direct ancestor of the modern task inbox.

The next step in the lineage gave the human step a durable, engine-tracked shape. Before
BPEL4People, "despite wide acceptance of Web services in distributed business
applications, the absence of human interactions was a significant gap for many
real-world business processes." BPEL4People closed that gap, it "extended BPEL from
orchestration of Web services alone to orchestration of role-based human activities as
well." In June 2007, a cross-vendor group, "Active Endpoints, Adobe Systems, BEA, IBM,
Oracle, and SAP," published both the BPEL4People and WS-HumanTask specifications
together ([Wikipedia, BPEL4People](https://en.wikipedia.org/wiki/BPEL4People), verified
2026-08-22). The original OASIS technical-committee page for this work is no longer
reachable at its published URL as of this verification, so this entry cites the still-live
Wikipedia summary rather than a dead primary link.

BPMN 2.0, the OMG's Business Process Model and Notation specification, made the concept a
first-class graphical and executable element, and drew a precise line the model has kept
ever since. Read directly from the official OMG BPMN 2.0.2 specification PDF
([omg.org/spec/BPMN/2.0.2/PDF](https://www.omg.org/spec/BPMN/2.0.2/PDF), pp. 160 to 166,
verified 2026-08-22).

> "A User Task is a typical 'workflow' Task where a human performer performs the Task
> with the assistance of a software application and is scheduled through a task list
> manager of some sort." (p. 160, restated p. 164 as managed "in the context of a
> Process" by a software component "called task manager.")

The spec draws the opposite case with equal precision.

> "A Manual Task is a Task that is expected to be performed without the aid of any
> business process execution engine or any application. An example of this could be a
> telephone technician installing a telephone at a customer location." (p. 161)

Section 10.3.4.1, "Tasks with Human involvement" (p. 163), states the distinction
plainly.

> "In many business workflows, human involvement is needed to complete certain Tasks
> specified in the workflow model. BPMN specifies two different types of Tasks with
> human involvement, the Manual Task and the User Task."

It then defines each side of that split in one breath.

> "A User Task is executed by and managed by a business process runtime. Attributes
> concerning the human involvement, like people assignments and UI rendering can be
> specified in great detail. A Manual Task is neither executed by nor managed by a
> business process runtime."

Crucially, the spec itself names the prior standard it interoperates with, closing the
lineage loop directly rather than by inference. "A User Task for instance can be
implemented using WS-HumanTask by setting the implementation attribute to
'http colon slash slash docs dot oasis dash open dot org slash ns slash bpel4people
slash ws dash humantask slash protocol slash 200803'" (p. 164, the literal URI string
from the spec, reformatted here so it renders as prose rather than an active link). The
spec adds that vendor extensions to these attributes "SHOULD use attributes defined by
the OASIS WS-HumanTask specification."

BPMN itself traces back further still. Originally developed by the Business Process
Management Initiative and maintained by the OMG since a 2005 merger, BPMN 1.0 shipped in
May 2004 with only a generic Task element, no User Task versus Manual Task split. That
split, and the added execution semantics generally, arrived with BPMN 2.0 in January
2011, the same release that renamed the spec from "Business Process Modeling Notation" to
"Business Process Model and Notation." The current release is BPMN 2.0.2, January 2014,
also ratified as ISO 19510 ([Wikipedia, Business Process Model and
Notation](https://en.wikipedia.org/wiki/Business_Process_Model_and_Notation), verified
2026-08-22).

## 2. Problem and context

AWS states the rationale for pausing a workflow for a human directly, in its own product
documentation, as one of exactly three named reasons a callback task exists.

> "Callback tasks provide a way to pause a workflow until a task token is returned. A
> task might need to wait for a human approval, integrate with a third party, or call
> legacy systems."

The same page lists "Human in the loop" as one of six headline use cases for the whole
Step Functions service, with a worked example.

> "Step Functions can include human approval steps in the workflow. For example, imagine
> a banking customer attempts to send funds to a friend. With a callback and a task
> token, you can have Step Functions wait until the customer's friend confirms the
> transfer, and then Step Functions will continue the workflow to notify the banking
> customer that the transfer has completed."

A second, sharper AWS example names the exact trigger for routing to a human rather than
finishing automatically, a threshold crossed.

> "Imagine that a customer requests a credit limit increase. If the request is more than
> your customer's pre-approved credit limit, you can have Step Functions send your
> customer's request to a manager for sign-off. If the request is less than your
> customer's pre-approved credit limit, you can have Step Functions approve the request
> automatically."

([docs.aws.amazon.com, What is Step
Functions](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html), verified
2026-08-22).

Camunda frames the same idea from the process-modeling side. "A user task is used to
model work that needs to be done by a human and is assisted by a workflow engine or
software application," and, on the pause mechanic itself, "When the process instance
arrives at a user task, a new user task instance is created at Zeebe. The process
instance stops at this point and waits until the user task instance is completed"
([docs.camunda.io, User
Tasks](https://docs.camunda.io/docs/components/modeler/bpmn/user-tasks/), verified
2026-08-22).

Temporal, which has no first-class "human task" concept, implements the same pause
through its general-purpose Signal mechanism, "an asynchronous message sent to a running
Workflow Execution to change its state and control its flow." The documented approval
pattern sets a boolean flag from a signal handler and blocks the workflow body on it.

```
let approvedForRelease = false;
wf.setHandler(approve, (input) => {
  approvedForRelease = true;
});
await wf.condition(() => approvedForRelease);
```

("The call returns when the server accepts the Signal, it does not wait for the Signal
to be delivered," and "The WorkflowExecutionSignaled Event appears in the Workflow's
Event History," giving a durable record of the human's action.
[docs.temporal.io, Workflow message
passing](https://docs.temporal.io/encyclopedia/workflow-message-passing), verified
2026-08-22.)

Two named, repeated reasons for why the step exists at all recur across these vendors.
First, authorization or exception handling above a threshold, AWS's credit-limit example
above. Second, judgment automation cannot yet perform on its own. Greylock Federal
Credit Union's own Camunda case study states this directly for a real production system.
"The AI scores every case, a person validates it, and as we get comfortable we let it
take on more," and "a person stays in control of every high-stakes decision"
([camunda.com, Greylock Federal Credit
Union](https://camunda.com/case-studies/greylock-federal-credit-union/), verified
2026-08-22). Stripe's Radar fraud-review documentation makes the identical point from a
different domain, cautioning against overuse rather than only justifying use. "Focus on
payments where human judgment can add valuable insight for a decision. Most payments can
be handled by automated systems. In some fraud-detection cases, however, accuracy can be
significantly improved by human decisions. Manual involvement doesn't add value in every
case, so choose transactions where the benefit is clearly evident" ([docs.stripe.com,
Radar reviews](https://docs.stripe.com/radar/reviews), fetched in German and translated
back to English for this entry, verified 2026-08-22).

## 3. Forces

**Timeout design.** AWS's callback pattern has a documented, sourced worst case for a
missing timeout. A waiting task "will wait until the workflow execution reaches the one
year service quota" if left unconfigured. Two distinct, separately configured timeout
mechanisms exist, a repeating heartbeat and a single overall bound. "The task will wait
for the task token to be returned with one of these API actions. SendTaskSuccess,
SendTaskFailure, SendTaskHeartbeat. If the waiting task doesn't receive a valid task
token within that period, the task fails with a States.Timeout error name" ([docs.aws.amazon.com,
Discover service integration
patterns](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html),
verified 2026-08-22).

**Escalation when nobody acts.** BPMN's mechanism is the Escalation Event, "used to
communicate to a higher flow scope," and non-critical by design, "execution continues at
the location of throwing" rather than aborting the process. Critically, escalation is
opt-in, not automatic. Camunda's own docs state plainly, "if there are no escalation
catch events that match the escalationCode, the escalation will not be caught," and that
in that case "the process will continue without escalating" ([docs.camunda.io], verified
2026-08-22). A designer who forgets to attach a matching escalation catch event has, by
this documented behavior, silently built a task that can sit unclaimed forever with no
alarm.

**Single assignee against a candidate pool.** Cross-confirmed across two independent
engines. Camunda's `assignee` "allows direct assignment of a User Task to a given user,"
against `candidateUsers`/`candidateGroups`, which "allows you to make a group a
candidate for a task." Flowable's shape is identical, "Only one user can be assigned as
the human performer for the task," or "a given group" made "a candidate for a task."
The BPMN spec's own formal term for a pool member is Potential Owner, "persons who can
claim and work on it" (p. 166). A fixed assignee gives certainty of ownership at design
time but requires the upstream logic to already know who should do the work. A candidate
pool defers that decision to claim time, trading certainty for flexibility, and for the
real risk that a task sits in a shared pool nobody claims.

**Polling against a pushed callback.** AWS documents this trade-off explicitly rather
than leaving it implicit. Its `.sync` polling integration pattern "uses polling that
consumes your assigned quota and events to monitor a job's status." Its
`waitForTaskToken` callback pattern has no polling at all, the caller pushes a token back
when the human acts. The callback avoids the polling cost entirely, at the price of
pushing the "how does the human find out about the task" problem onto whatever external
system delivers the notification, email, Slack, a task-list UI.

**Idempotency of the human's action.** Not named as a force by any fetched vendor
source, but structural in the design. AWS's task token is single-use per wait, "If a
Task state using the callback task token times out, a new random token is generated,"
which is itself a replay-prevention choice, a stale or reused token cannot resolve a
task twice.

**Metadata richness against engine footprint.** Visible directly in the BPMN 2.0.2 spec.
The formal, engine-tracked instance attributes of a User Task are deliberately thin,
just `implementation`, `renderings`, `actualOwner`, and `taskPriority` (Table 10.14, p.
165). Richer task metadata, forms, due dates, business descriptions, is pushed out to
either a vendor extension namespace (Camunda's `camunda:` attributes) or the separate
OASIS WS-HumanTask spec the BPMN spec itself defers to. This is the specification
deliberately keeping the engine's own model small, and letting the UI and extension
layer carry the weight.

## 4. Applicability and non-applicability

**Reach for a first-class Human Task step when.**

- A workflow needs a genuine authorization or exception gate above a threshold, the AWS
  credit-limit shape, or Greylock's fraud/address-hygiene review shape.
- Judgment a person can bring outperforms an automated score for at least a meaningful
  slice of cases, and that slice is expected to shrink as trust in the automated system
  grows, the Greylock "as we get comfortable we let it take on more" pattern.
- The step needs the engine's own tracked lifecycle, assignment, claim, escalation,
  reporting, rather than being invisible to the engine. This is exactly BPMN's own
  User Task versus Manual Task line, formalized at the specification level.

**Reach for the plain BPMN Manual Task, or skip a workflow-engine element entirely,
when.**

- The human step happens fully outside the system's view and the engine should treat it
  as an unobserved pass-through. Camunda's own docs describe exactly this behavior,
  "For the engine, a manual task is handled as a pass-through activity, automatically
  continuing the process when the process execution arrives at it." A Manual Task is,
  from an automation standpoint, close to a no-op, present purely to document a real
  step, not to gate on it.
- The step has a genuine cost to the person waiting on the other end, and that cost may
  outweigh the value of the review. Stripe's own Radar guidance is explicit about this
  boundary, "Avoid extra wait time for your customers... if there is typically no delay
  between order and fulfillment, an additional review step can slow down the order
  process for legitimate customers. Consider the customer impact before adding a review
  step."
- There is no real multi-step orchestration around the human action, one request and one
  response with nothing durable to resume afterward. None of the sources fetched state
  this exact non-applicability case in so many words, this line follows from the
  structural shape all three engines share rather than a direct vendor quote, and is
  flagged here as this entry's own reasoning rather than a cited claim.

## 5. Structure

Cross-checked directly against the BPMN 2.0.2 spec plus two independent engine
implementations, Camunda and Flowable.

| Term | Definition | Source |
|---|---|---|
| User Task | "A typical 'workflow' Task where a human performer performs the Task with the assistance of a software application" | BPMN 2.0.2 spec, p. 160 |
| Manual Task | "A Task that is expected to be performed without the aid of any business process execution engine or any application" | BPMN 2.0.2 spec, p. 161 |
| Assignee | Direct, single-person ownership. "Only one user can be assigned as the human performer for the task" | Flowable docs, cross-checked against Camunda's identical shape |
| Candidate users / groups | A pool a task can be claimed from. "Makes a given group a candidate for a task" | Camunda docs, cross-checked against Flowable's identical shape |
| Potential Owner | The BPMN spec's own formal term for a pool member. "Persons who can claim and work on it" | BPMN 2.0.2 spec, p. 166 |
| Claim | "A potential owner becomes the actual owner of a Task, usually by explicitly claiming it." Camunda 8's Tasklist collapses this into an "Assign to me" button | BPMN 2.0.2 spec, p. 166. docs.camunda.io Tasklist docs |
| Actual owner | The formal spec attribute recording who claimed the task, "the value is a literal representing the user's id, email address etc." | BPMN 2.0.2 spec, Table 10.14, p. 165 |
| Complete | Marks the task done and resumes the paused process. Camunda 7, `taskService.complete(taskId, variables)`. Camunda 8, clicking Complete Task on a filled-in form | Camunda 7 REST docs, Camunda 8 user docs |
| Priority | An integer, 0 to 100, default 50, "higher values indicating greater importance." The spec's own formal attribute is `taskPriority` | Camunda docs, BPMN 2.0.2 spec, Table 10.14 |
| Rendering / task form | The spec deliberately leaves the form schema unspecified, "The content of the rendering element is not defined by this International Standard." Camunda's own concrete implementation offers Camunda Forms or a custom external form reference | BPMN 2.0.2 spec, p. 165. docs.camunda.io |
| Escalation | Not a User Task attribute. Implemented via the general BPMN Escalation Event, a boundary event that communicates "to a higher flow scope" and is non-critical | docs.camunda.io |
| Human Performer / Potential Owner hierarchy | The spec's formal metamodel specializes `Performer` into `HumanPerformer` into `PotentialOwner`, letting a process define roles finer than BPMN 1.2's single generic Performer | BPMN 2.0.2 spec, p. 165 |
| Due date / follow-up date | Camunda distinguishes a soft reminder marker from a hard deadline for a task, though this pass could not confirm the exact source wording with full confidence, so the precise phrasing is left unquoted here rather than risk misstating it | docs.camunda.io, flagged as partially unverified |

Camunda's tooling also names a `delegate`/`resolve` pair of lifecycle operations
referenced in its REST API navigation, a Camunda-specific extension with no equivalent in
the BPMN spec itself. This pass could not retrieve a full, standalone prose definition of
that pair from the pages fetched, so it is named here without a quoted definition rather
than guessed at.

## 6. ASCII structure diagram

```
  Upstream step        Workflow engine            Task queue / inbox
  completes      --->  reaches the Human    --->  (candidateGroup:
                        Task step, CREATES a       "loan-officers")
                        task instance, and
                        the process PAUSES         [ ] Task 4471
                        here                        [ ] Task 4472  <- claimed

                                                          |
                                                          | CLAIM
                                                          v
                                              Claimed by. alice
                                              actualOwner = alice
                                              status. in progress
                                                          |
                                                          | human does the
                                                          | real work, fills
                                                          | the task form
                                                          v
                                              COMPLETE
                                              form data submitted,
                                              e.g. approved = true

  Workflow engine   <---------------------------------- resume
  RESUMES with the
  submitted data,
  continues to the
  next step

  Guard rails not shown above.
  - a boundary TIMER on the paused step, catching a missed deadline and
    firing an ESCALATION event to a supervisor group
  - a heartbeat and an overall timeout on the callback token itself, so
    the workflow never waits literally forever if nobody claims the task
```

## 7. Dynamics

```
1. The workflow reaches the Human Task step. The engine creates a task
   instance and the process instance pauses here.
2. The task is either assigned directly to a person, or placed in a
   pool visible to a candidate group.
3. A person claims the task, becoming its actual owner. In a pool model,
   this prevents two people from duplicating the same work.
4. The person performs the real work and submits the task form.
5. The engine marks the task complete, merging the submitted data back
   into the process's own variables.
6. The engine resumes the paused process instance with that data, and
   the workflow continues to its next step.
7. If a boundary timer fires before step 3 or 5, an escalation event
   (if one is attached) redirects the task to a supervisor or a wider
   candidate group. If none is attached, the task keeps waiting.
```

## 8. Implementation variants

**AWS Step Functions, "Wait for a Callback with Task Token."** A task token generated
via a special JSONPath into the running execution's Context object, `"TaskToken.$":
"$$.Task.Token"`, is handed to whatever system needs to notify Step Functions when the
human is done. "This tells Step Functions to pause and wait for the task token." The
task later resolves when an external caller returns that same token via `SendTaskSuccess`
or `SendTaskFailure`. Token return is restricted to the same account, "You must pass task
tokens from principals within the same AWS account." AWS's own docs point to a named,
maintained reference project for exactly this shape, "Create a callback pattern example
with Amazon SQS, Amazon SNS, and Lambda"
([docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html], verified
2026-08-22).

**Camunda 8 or Zeebe User Tasks, plus Tasklist.** "The process instance stops at this
point and waits until the user task instance is completed." Camunda 8 currently ships two
implementation types for a BPMN User Task, and the older one is explicitly deprecated.
The Camunda user task (the engine-managed implementation) runs "directly on the
automation engine for high performance," while the older job-worker implementation
"is deprecated. We recommend using Camunda user tasks instead for enhanced
functionality and adherence to best practices," with its own stated limitations, "no
visibility into lifecycle and state management" and "reduced metrics and reporting."
Lifecycle listener hooks named in the docs are `creating`, `assigning`, `updating`,
`completing`, `canceling`. Tasklist, Camunda's own inbox UI, claims a task for a known
user when "the value of the assignee must be the user's unique identifier" ([docs.camunda.io,
User
Tasks](https://docs.camunda.io/docs/components/modeler/bpmn/user-tasks/), and the [migration
manual](https://docs.camunda.io/docs/apis-tools/migration-manuals/migrate-to-camunda-user-tasks/),
verified 2026-08-22).

**Temporal, Signals and Update, no dedicated primitive.** As shown in dimension 2,
Temporal's docs never use the phrase "human task." The general Signal and Update
mechanisms carry it instead, "asynchronous write requests" for Signal, versus Update,
"a synchronous, blocking call that can change Workflow state, control its flow, and
return a result." Temporal's own blog post "When the human is the Workflow" (published
2026-08-11) is the closest thing found to an explicit human-in-the-loop marketing frame,
describing field technicians whose entire shift is one long-running Workflow instance
receiving Updates over its lifetime. "A shift is not a request slash response. It opens
in the morning, accumulates events such as clock-ins, safety questionnaires, mid-shift
schedule changes, tool sign-outs, task completions, document signatures, and closes at
night," and "the workflow is the source of truth for where a shift is, and it cannot
lose that truth, not to a crash, a deploy, or a dropped connection" ([temporal.io/blog,
When the human is the
Workflow](https://temporal.io/blog/durable-execution-in-harsh-physical-field-operations),
[docs.temporal.io/encyclopedia/workflow-message-passing], verified 2026-08-22).

**jBPM and Kogito.** This pass could not directly verify jBPM's compliance with the
OASIS WS-HumanTask specification from a live jBPM or Kogito docs page, every attempt
returned an error or an index-only page with no body content. What is confirmed is that
jBPM and Kogito now live under Apache KIE, described on its own landing page as "an
effort undergoing incubation at The Apache Software Foundation," and that a "Human
Task" component name surfaces in Red Hat's own security advisories for the jBPM family
(dimension 17). The widely cited jBPM to WS-HumanTask lineage is not asserted here as a
directly sourced fact, since it could not be confirmed against a primary source this
pass ([kie.apache.org], verified 2026-08-22).

**n8n, a lightweight, non-BPM-engine implementation.** The Wait node "offloads the
execution data to the database" when it pauses, and resumes on one of several
conditions, including "on webhook call" and "on form submitted." A unique,
per-execution URL carries the resume signal, "The Wait node provides the
`$execution.resumeUrl` variable so that you can reference and send the yet-to-be-generated
URL wherever needed." A documented caveat, "Partial executions of your workflow changes
the `$resumeWebhookUrl`, so be sure that the node sending this URL to your desired
third-party runs in the same execution as the Wait node" ([docs.n8n.io, Wait
node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait/), verified
2026-08-22). n8n's own docs never frame this as human-in-the-loop, that framing is this
entry's own synthesis, but the mechanism, generate a resumable URL, hand it to a person
by email or Slack, resume on their action, is functionally the same shape as AWS's task
token, implemented at the automation-tool layer rather than the cloud-service layer.

## 9. Known production uses

1. **Stripe Radar's manual payment review queue.** "While Stripe's automated systems
   prevent fraud on your account, manual payment review lets you add an additional
   layer of fraud prevention," triggered by conditions like an elevated fraud score, a
   transaction outside the account's usual country, or an amount above a threshold. The
   review list is described as "a prioritized list of completed or to-be-captured
   payments that may need investigation." Claiming works exactly like a BPM candidate
   pool, "All team members who manage the review list can assign reviews to themselves
   to avoid duplicated effort," with filters for reviews "assigned to you, or reviews
   assigned to no one." A reviewer resolves a flagged payment with one of three named
   actions, Approve, Refund, or Report as fraud and refund the payment. The queue emits
   `review.opened` and `review.closed` webhook events, giving other systems the same
   create/complete lifecycle hook a BPM engine's own task events would provide
   ([docs.stripe.com/radar/reviews], verified 2026-08-22).
2. **GitHub Actions, required reviewers on a deployment environment.** "A job that
   references an environment must follow any protection rules for the environment
   before running or accessing the environment's secrets." A configured environment can
   "specify people or teams that must approve workflow jobs that use this environment,"
   up to six, and "only one of the required reviewers needs to approve the job for it to
   proceed." The two documented outcomes, "To approve the job, click Approve and
   deploy. Once a job is approved... the job will proceed," and "To reject the job,
   click Reject. If a job is rejected, the workflow will fail" ([docs.github.com,
   Using environments for
   deployment](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment),
   verified 2026-08-22). This is a real, extremely widely used human-task node embedded
   inside an otherwise fully automated CI and CD pipeline.
3. **Goldman Sachs, an internal Camunda-based workflow platform.** A named Goldman
   Sachs executive, co-head of workflow engineering, states, "On average we have about
   8,000 people completing tasks on the platform on a daily basis," with 6 million
   tasks executed per week across payment processing and a shared automation platform
   used by 15 or more internal teams ([camunda.com/about/customers/goldman-sachs/],
   verified 2026-08-22). Stated honestly, this figure spans the platform's full task
   volume, not human-approval tasks alone, so it is evidence of large-scale production
   use of the underlying BPM engine rather than a precise count of approval steps
   specifically.
4. **Greylock Federal Credit Union, an address-hygiene and exception-handling
   workflow.** Already quoted in dimension 2, "The AI scores every case, a person
   validates it," a direct, named instance of an automated score plus a mandatory
   human-task checkpoint before the outcome commits ([camunda.com/case-studies/greylock-federal-credit-union/],
   verified 2026-08-22).

## 10. Consequences

**Positive.**

- Pausing on a pushed callback token, rather than polling, avoids ongoing API cost, a
  direct AWS-documented trade-off from dimension 3.
- A claim or assignee model gives clear, single ownership even when the work sits in a
  shared pool, preventing duplicated effort, Stripe's Radar docs name this benefit
  explicitly.
- Completion events, Temporal's `WorkflowExecutionSignaled`, Stripe's `review.closed`,
  give other systems a durable, subscribable audit trail of the human's decision.
- Candidate groups give flexible routing without the process designer needing to know
  in advance exactly who will do the work.

**Negative.**

- Without an explicit timeout, an AWS callback task can legally sit open for up to one
  year, dimension 3's sourced worst case.
- A person waiting on the review carries a real cost, Stripe's own guidance explicitly
  warns against adding a review step where it slows a legitimate customer down for
  little benefit.
- Vendor-specific lifecycle vocabulary is not stable. Camunda 8's own migration away
  from the job-worker task implementation is active, multi-release churn a team
  building on this pattern has to track.
- The exact surface, who may claim, complete, or approve a task, is a real and
  currently tracked source of severe vulnerabilities, detailed in dimension 17.

## 11. Failure modes and misuse

**A missing or misconfigured timeout.** AWS's own one-year quota, from dimension 3, is
the sourced worst case, a callback task left with no `HeartbeatSeconds` or
`TimeoutSeconds` can legitimately sit open that long.

**An unclaimed task with no escalation path.** BPMN's Escalation Event is opt-in, not
automatic. Camunda's own docs state plainly that when no matching escalation catch event
exists, "the process will continue without escalating," which means a task sitting in an
unattended candidate pool can remain there indefinitely with no alarm, unless the
process designer deliberately wired an escalation.

**Choosing the deprecated implementation path.** Camunda's own migration docs name the
job-worker User Task implementation's limitations directly, "no visibility into
lifecycle and state management" and "reduced metrics and reporting," a vendor-acknowledged
failure mode of continuing to build on the older mechanism rather than the current
engine-managed one.

**Authorization bypass at the exact claim or complete boundary.** This is not a general
illustration, it is a real, currently tracked, critical vulnerability class, detailed in
full in dimension 17. A workflow gate that is supposed to require a specific role's
approval can be bypassed entirely if the underlying claim or role-grant check is
missing.

**Choosing a code-shaped tool for a data-shaped problem.** A team already committed to
Temporal gains its Signal and Update primitives, but loses the candidate-pool, claim,
and escalation tooling a BPM engine ships natively for this exact purpose, and must
build that assignment and escalation UX itself. This is this entry's own reasoning
about the trade-off, not a directly sourced vendor caution.

## 12. Trade-off matrix

| Approach | Built-in assignment / candidate pool | Built-in escalation and timeout | Durable across a crash or restart | Setup cost |
|---|---|---|---|---|
| AWS Step Functions, `waitForTaskToken` | No, entirely delegated to whatever external system holds the token | Heartbeat and overall timeout, configured per state, no assignment or escalation concept at all | Yes, part of the durable state machine | Low, one state field plus an external notify path |
| Camunda 8, engine-managed user task | Yes, assignee and candidate groups, Tasklist inbox | Yes, via Escalation Events, opt-in per process | Yes, Zeebe's own persistence | Moderate, a BPM engine to run and operate |
| Temporal, Signal or Update | No native concept, built by hand on top of a general message primitive | No native concept, built by hand | Yes, the workflow's own durable execution and event history | Moderate, general-purpose durability, human-specific UX is homegrown |
| n8n, Wait node plus webhook | No native concept, one resumable URL per wait | No native concept | Yes, execution data offloaded to n8n's own database | Low, a workflow-automation tool rather than a full BPM engine |

## 13. Related and incompatible patterns

**Saga**, the compensation angle. AWS names two specific error conditions a human-task
callback can raise, "States.HeartbeatTimeout," described as "A Task state failed to send
a heartbeat for a period longer than the HeartbeatSeconds value," and "States.Timeout."
Both are documented as usable inside a `Catch` block's `ErrorEquals` array, meaning a
rejected or timed-out human approval can be routed directly to a compensating state, the
same `Catch`/`Retry` mechanism the sibling Saga entry documents generally, applied here
to the specific case of a human saying no or never answering
([docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html], verified
2026-08-22). Stated honestly, a dedicated AWS document naming "Saga" alongside a human
approval step specifically could not be fetched this pass, so this connection is
presented as a sourced mechanism applied through this entry's own reasoning, not a
direct vendor statement about sagas.

**Workflow Engine** (sibling entry). Camunda's own words are the clearest confirmation
that a Human Task is implemented as a wait-state inside a durable execution model, "The
process instance stops at this point and waits until the user task instance is
completed." AWS's `waitForTaskToken` is, architecturally, one Task state type among
several inside the very state machine the sibling entry documents.

**State Machine Workflow** (sibling entry). The same wait-state framing applies at the
narrower, engine-agnostic level, a Human Task is a state whose only outbound guarded
transitions are "approved," "rejected," or "timed out."

**Compensation Handler** (queued, not yet published). A rejected or timed-out human
task is exactly the kind of signal a compensation handler exists to listen for. This
relationship will be developed further once that sibling entry lands.

A brief, honest note on the philosophical split found across dimension 8. BPM-engine
tools, Camunda and by strong implication jBPM given a shared WS-HumanTask lineage, model
Human Task as data, a first-class element with its own stored lifecycle, listeners, and
inbox. Temporal models the same idea as code, an ordinary blocking call awaiting a
message. This framing is this entry's own synthesis of the sourced mechanics above, not
a claim any single vendor states in those terms.

## 14. Refactoring path in and out

**Introducing it.** The signal is a manual override queue or an ad hoc side channel, a
shared spreadsheet, a Slack thread, that keeps growing around an otherwise automated
process, the Stripe Radar and AWS credit-limit shape from dimension 2. Formalizing that
side channel into a first-class Human Task step gives it a claim model, a timeout, and
an audit trail the side channel never had.

**Evolving or narrowing it.** When an approval task's accept rate approaches near-total
consistency over time with few genuine rejections, that is a signal the underlying
judgment could shift toward automation. Greylock's own words describe exactly this
evolution as a deliberate, gradual practice, "as we get comfortable we let it take on
more," the human task functioning as a circuit breaker whose scope narrows as trust in
the automated score grows, never removed all at once. Separately, Camunda 8's own
migration path from the job-worker implementation to the engine-managed user task is
itself a refactor of a Human Task's implementation, not its removal, evidence that even
a settled pattern's underlying mechanism keeps evolving.

**A newer variant, applied to AI agents.** The most current place this pattern is
appearing is inside agentic AI frameworks, gating a risky action an autonomous agent is
about to take, an API call, a database change, a financial transaction, behind human
approval before it executes. LangGraph's own codebase confirms this as a real,
maintained primitive rather than a marketing claim, its `Interrupt` dataclass, "information
about an interrupt that occurred in a node," has shipped since the library's version
0.2.24 and continued to evolve through version 0.6.0. This is the same underlying
shape as AWS's callback token and Camunda's claim-and-complete cycle, applied at the
point where an AI agent's own next action, rather than a human's own next process
step, is what waits for approval.

## 15. Testing and verification

**AWS Step Functions.** The docs carry an honest, prominent deprecation notice for the
older local-testing tool. "Step Functions Local is unsupported. Step Functions Local
does not provide feature parity and is unsupported. You might consider third party
solutions that emulate Step Functions for testing purposes." The currently recommended
alternative is the TestState API. Despite the notice, the documented callback-testing
mechanism for Step Functions Local still works as described, "Step Functions Local will
automatically generate a task token when you mock a Task using the waitForTaskToken." A
test declares a `MockConfigFile.json` with named `TestCases`, mapping each Task state to
a `MockedResponses` entry that returns a success payload or throws an error, letting a
test simulate a human's approval or rejection without a real external system
([docs.aws.amazon.com/step-functions/latest/dg/sfn-local.html], verified 2026-08-22).

**Temporal.** The Go SDK's test environment lets a test inject a simulated approval
Signal at an arbitrary point in simulated time.

```
env.RegisterDelayedCallback(func() {
    env.SignalWorkflow("complete", nil)
}, time.Hour*24*90)
```

This resolves the approval 90 simulated days into the workflow with no real wall-clock
wait ([docs.temporal.io/develop/go/testing-suite], verified 2026-08-22). The TypeScript
test environment offers the same time-skipping behavior, `createTimeSkipping()`, "the
test server switches to 'skipped' time mode until the Workflow completes," fast-forwarding
timers except while an Activity is actually running
([docs.temporal.io/develop/typescript/testing-suite], verified 2026-08-22). This pass
did not find a TypeScript-specific code example for sending a test Signal, so that
detail is not asserted, only the Go example is quoted directly.

**Camunda.** This pass could not retrieve a working page for the current
`camunda-process-test` testing library's exact API for programmatically claiming or
completing a user task in a test, both attempted URLs returned an error. That specific
API surface is left unasserted here rather than guessed at.

## 16. Observability signals

AWS Step Functions ships several metrics that map directly onto a callback-style Human
Task. `ActivityScheduleTime`, "Interval, in milliseconds, for which the activity stays
in the schedule state," is the direct time-in-queue signal. `ActivityRunTime`,
"Interval, in milliseconds, between the time the activity starts and the time it
closes," combines queue time and completion time together. `ActivitiesHeartbeatTimedOut`
is the closest built-in abandonment counter, and `ActivitiesTimedOut` the general SLA
breach counter. The equivalent trio, `ServiceIntegrationScheduleTime`,
`ServiceIntegrationRunTime`, and `ServiceIntegrationsTimedOut`, covers a
`waitForTaskToken` implemented via a direct service integration rather than the older
Activity worker pattern. `ExecutionTime` covers the whole workflow, which for a workflow
with a human approval step will be dominated by the wait. AWS's own honesty caveat is
worth carrying forward, "CloudWatch metrics are delivered on a best-effort basis. The
completeness and timeliness of metrics are not guaranteed"
([docs.aws.amazon.com/step-functions/latest/dg/procedure-cw-metrics.html], verified
2026-08-22).

This pass could not find a documented built-in reporting page for Camunda Tasklist
itself, the fetched introduction page points toward Optimize, a separate Camunda
component, as where actual reporting lives, and the migration guide names "task reports
in Optimize" as a capability gained specifically by moving off the older job-worker
implementation.

Queue depth per candidate group and a general SLA breach counter are, based on the
sourced mechanics above, the two signals worth adding by hand where a platform does not
ship them natively. Neither AWS Step Functions nor Temporal has any built-in concept of
a named assignee or candidate group at all, so this signal only applies to a BPM-engine-style
implementation with that concept in the first place. This paragraph is this
entry's own reasoning, not a vendor-documented metric.

## 17. Security and privacy implications

Task-claim and task-authorization bugs are a real, currently tracked vulnerability
class, not a hypothetical concern.

**CVE-2026-62183**, Apache Syncope, using a Flowable-based workflow engine internally.
CVSS 3.1 score 9.8, critical, published July 20, 2026. Precisely on point for this
entry's central concern, an authorization bypass at a workflow approval gate. "A REST
API call can allow the user to grant themselves one or more of defined Roles, thus
gaining their Entitlements and becoming in fact an administrator," triggered when a
workflow configuration lacks an admin-approval requirement step. In BPM terms, a user
completed, or entirely skipped, an approval task they were never authorized to resolve
themselves ([services.nvd.nist.gov, CVE-2026-62183], verified 2026-08-22).

**CVE-2026-53405**, Apache Syncope, same product family. CVSS 3.1 score 9.8, critical,
published July 20, 2026. An administrator can import BPMN process definitions
containing Groovy script tasks that execute unsandboxed on the server the moment the
process starts, an adjacent, process-definition-authoring path to remote code execution.

**CVE-2020-11977**, Apache Syncope's Flowable extension. Published September 15, 2020.
"An administrator with workflow entitlements can use Shell Service Tasks to perform
malicious operations, including but not limited to file read, file write, and code
execution."

**CVE-2021-20306**, jBPM 7.51.0.Final, Red Hat Business-central. CVSS 3.1 score 4.3,
medium. A confidentiality leak across project boundaries in the BPMN editor. "Any
authenticated user from any project can see the name of Ruleflow Groups from other
projects, despite the user not having access to those projects." Not a task-claim bug
directly, but a real, cited instance of an authorization boundary failing inside the
exact BPM-editor surface this entry describes ([services.nvd.nist.gov, CVE-2021-20306],
citing Red Hat Bugzilla 1946213, verified 2026-08-22).

**Adjacent tooling vulnerabilities, confirmed but not task-claim specific.**
CVE-2021-28154 (Camunda Modeler, CVSS 9.1 critical, arbitrary file access via an exposed
IPC interface, though the vendor disputed the finding). CVE-2025-58059, GHSA-w48j-pp7j-fj55
(Valtimo, CVSS 9.1 critical, an admin who can author a process definition can run
executables on the host or read the application's own secrets). CVE-2014-3682 and
CVE-2014-8125 (jBPM and Drools, XML external entity vulnerabilities via crafted BPMN2
process files, allowing arbitrary file read). CVE-2017-7545 (jbpm-migration, the same
XXE class). CVE-2013-6465 (jBPM Designer, stored and reflected XSS). CVE-2010-2493
(JBoss Enterprise SOA Platform, a default-configuration access-restriction bypass).
CVE-2018-20594 (hsweb, a Flowable-based platform, reflected XSS).

Honestly, no genuine, filtered Apache Activiti-specific CVE was found this pass. Every
NVD keyword search for "Activiti" returned only false-positive substring matches
against the unrelated word "activities" inside old, unrelated CVE descriptions, and
that negative result is reported here rather than papered over.

**Privacy.** Task payloads routinely carry sensitive data, a KYC review task carries
personal identity information, an insurance-claim or loan-underwriting task carries
financial detail, and that payload persists in the workflow engine's own storage, its
audit log, and any downstream reporting tool built on top of it. This pass found no
vendor-documented guidance specific to handling PII inside a human task's payload, so
this observation is this entry's own reasoning, flagged as such rather than presented
as a cited best practice.

## 18. References

1. WfMC. *Glossary*.
   https://wfmc.org/glossary/
   Verified 2026-08-22. Source of the Automated Activity, Manual Activity, and Worklist definitions.
2. Wikipedia. *BPEL4People*.
   https://en.wikipedia.org/wiki/BPEL4People
   Verified 2026-08-22. Source of the pre-BPMN-2.0 human-interaction standard and its 2007 publication.
3. OMG. *BPMN 2.0.2 specification*.
   https://www.omg.org/spec/BPMN/2.0.2/PDF
   Verified 2026-08-22, pp. 155 to 166. Source of the User Task and Manual Task definitions and the formal vocabulary.
4. Wikipedia. *Business Process Model and Notation*.
   https://en.wikipedia.org/wiki/Business_Process_Model_and_Notation
   Verified 2026-08-22. Source of the BPMN version history.
5. AWS. *What is Step Functions*.
   https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html
   Verified 2026-08-22. Source of the human-in-the-loop use case and the credit-limit example.
6. AWS. *Discover service integration patterns*.
   https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html
   Verified 2026-08-22. Source of the waitForTaskToken mechanics, timeouts, and token semantics.
7. Camunda. *User Tasks*.
   https://docs.camunda.io/docs/components/modeler/bpmn/user-tasks/
   Verified 2026-08-22. Source of the process-pause mechanic and lifecycle listeners.
8. Camunda. *Migrate to Camunda user tasks*.
   https://docs.camunda.io/docs/apis-tools/migration-manuals/migrate-to-camunda-user-tasks/
   Verified 2026-08-22. Source of the job-worker deprecation and its stated limitations.
9. Temporal. *Workflow message passing*.
   https://docs.temporal.io/encyclopedia/workflow-message-passing
   Verified 2026-08-22. Source of the Signal and Update definitions.
10. Temporal. *When the human is the Workflow*.
    https://temporal.io/blog/durable-execution-in-harsh-physical-field-operations
    Verified 2026-08-22. Source of the field-operations shift framing.
11. n8n. *Wait node*.
    https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait/
    Verified 2026-08-22. Source of the resumeUrl mechanics.
12. Stripe. *Radar reviews*.
    https://docs.stripe.com/radar/reviews
    Verified 2026-08-22. Source of the manual review queue lifecycle and events.
13. GitHub. *Using environments for deployment*.
    https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment
    Verified 2026-08-22. Source of the required-reviewers mechanism.
14. Camunda. *Goldman Sachs case study*.
    https://camunda.com/about/customers/goldman-sachs/
    Verified 2026-08-22. Source of the production-scale task-completion figures.
15. Camunda. *Greylock Federal Credit Union case study*.
    https://camunda.com/case-studies/greylock-federal-credit-union/
    Verified 2026-08-22. Source of the AI-scores-a-person-validates framing.
16. Apache KIE.
    https://kie.apache.org/
    Verified 2026-08-22. Source of jBPM and Kogito's incubation status.
17. Flowable. Task assignment documentation, cross-checked for the assignee and candidate group vocabulary.
    Verified 2026-08-22.
18. AWS. *Handling errors in Step Functions workflows*.
    https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html
    Verified 2026-08-22. Source of States.HeartbeatTimeout and States.Timeout.
19. AWS. *Step Functions Local*.
    https://docs.aws.amazon.com/step-functions/latest/dg/sfn-local.html
    Verified 2026-08-22. Source of the deprecation notice and the mock-token testing mechanism.
20. Temporal. *Go SDK testing suite*.
    https://docs.temporal.io/develop/go/testing-suite
    Verified 2026-08-22. Source of the RegisterDelayedCallback test example.
21. Temporal. *TypeScript SDK testing suite*.
    https://docs.temporal.io/develop/typescript/testing-suite
    Verified 2026-08-22. Source of the time-skipping test environment.
22. AWS. *Monitoring Step Functions using Amazon CloudWatch*.
    https://docs.aws.amazon.com/step-functions/latest/dg/procedure-cw-metrics.html
    Verified 2026-08-22. Source of the observability metrics.
23. NVD. *CVE-2026-62183*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2026-62183
    Verified 2026-08-22.
24. NVD. *CVE-2026-53405*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2026-53405
    Verified 2026-08-22.
25. NVD. *CVE-2020-11977*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=Flowable
    Verified 2026-08-22.
26. NVD. *CVE-2021-20306*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2021-20306
    Verified 2026-08-22. Also citing Red Hat Bugzilla 1946213.
27. NVD. *CVE-2021-28154*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2021-28154
    Verified 2026-08-22.
28. GitHub Advisory Database. *GHSA-w48j-pp7j-fj55*.
    https://github.com/valtimo-platform/valtimo-backend-libraries/security/advisories/GHSA-w48j-pp7j-fj55
    Verified 2026-08-22.
29. NVD. *CVE-2014-3682*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2014-3682
    Verified 2026-08-22.
30. NVD. *CVE-2014-8125*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2014-8125
    Verified 2026-08-22.
31. NVD. *CVE-2017-7545*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2017-7545
    Verified 2026-08-22.
32. NVD. *CVE-2013-6465*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2013-6465
    Verified 2026-08-22.
33. NVD. *CVE-2010-2493*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2010-2493
    Verified 2026-08-22.
34. NVD. *CVE-2018-20594*.
    https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2018-20594
    Verified 2026-08-22.
35. Camunda. *Camunda 8.6 release*.
    https://camunda.com/blog/2024/09/camunda-8-6-release/
    Verified 2026-08-22. Source of the task-prioritization feature and the release date, October 8, 2024.
36. LangChain. *langgraph, types.py, the Interrupt class*.
    https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/types.py
    Verified 2026-08-22. Source confirming the Interrupt primitive, added in library version 0.2.24, exists in the current LangGraph codebase.

**Evidence grade.** established

**Most solid findings.** The BPMN 2.0.2 spec's own text for User Task and Manual Task is
fully verified from the primary OMG PDF, read directly rather than paraphrased from a
secondary source. AWS's callback-task mechanics, timeouts, and error names are directly
quoted from AWS's own current documentation. Stripe Radar's full review lifecycle,
trigger conditions, claim mechanic, resolution actions, and webhook events, is
independently confirmed and internally consistent. The CVE list is NVD-verified, each ID
individually checked against the NVD REST API.

**Unverified or unclear.** jBPM and Kogito's compliance with the OASIS WS-HumanTask
specification could not be confirmed against a live primary source this pass. The exact
API of Camunda's current `camunda-process-test` testing library could not be retrieved.
Camunda's own documentation disagrees with itself on whether the engine-managed user
task type arrived in version 8.6 or 8.7, both readings are quoted honestly rather than
one being silently chosen. Camunda's Compensation Boundary Event trigger semantics for a
rejected or timed-out human task could not be retrieved. No verifiable, on-point Apache
Activiti CVE was found, only false-positive substring matches. Camunda's precise
due-date versus follow-up-date distinction could not be confirmed with full confidence
and is left unquoted in dimension 5 rather than risk a misstatement.

## Code

### TypeScript, a claimable task queue with candidate groups and a heartbeat timeout

```typescript
type TaskStatus = "queued" | "claimed" | "completed" | "timed_out";

interface HumanTask {
  id: string;
  candidateGroup: string;
  status: TaskStatus;
  claimedBy?: string;
  lastHeartbeatMs: number;
  createdAtMs: number;
}

class TaskQueue {
  private tasks = new Map<string, HumanTask>();
  private readonly heartbeatTimeoutMs: number;

  constructor(heartbeatTimeoutMs: number) {
    this.heartbeatTimeoutMs = heartbeatTimeoutMs;
  }

  create(id: string, candidateGroup: string, nowMs: number): void {
    this.tasks.set(id, {
      id,
      candidateGroup,
      status: "queued",
      lastHeartbeatMs: nowMs,
      createdAtMs: nowMs,
    });
  }

  claim(id: string, actor: string): boolean {
    const task = this.tasks.get(id);
    if (!task || task.status !== "queued") {
      return false;
    }
    task.status = "claimed";
    task.claimedBy = actor;
    return true;
  }

  complete(id: string, actor: string): boolean {
    const task = this.tasks.get(id);
    if (!task || task.status !== "claimed" || task.claimedBy !== actor) {
      return false;
    }
    task.status = "completed";
    return true;
  }

  sweepTimeouts(nowMs: number): string[] {
    const timedOut: string[] = [];
    for (const task of this.tasks.values()) {
      if (task.status === "claimed" && nowMs - task.lastHeartbeatMs > this.heartbeatTimeoutMs) {
        task.status = "timed_out";
        timedOut.push(task.id);
      }
    }
    return timedOut;
  }
}

function run(): void {
  const queue = new TaskQueue(600_000);
  queue.create("task-1", "loan-officers", 0);
  console.log(queue.claim("task-1", "alice"));
  console.log(queue.complete("task-1", "alice"));
  console.log(queue.sweepTimeouts(0));
}

run();
```

### Python, an AWS-style callback token gate with an escalation on timeout

```python
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional


@dataclass
class PendingApproval:
    token: str
    created_at: float
    heartbeat_seconds: float
    resolved: bool = False
    approved: Optional[bool] = None


class ApprovalGate:
    def __init__(self, heartbeat_seconds: float, escalate: Callable[[str], None]) -> None:
        self.heartbeat_seconds = heartbeat_seconds
        self.escalate = escalate
        self.pending: Dict[str, PendingApproval] = {}

    def wait_for_task_token(self) -> str:
        token = str(uuid.uuid4())
        self.pending[token] = PendingApproval(
            token=token, created_at=time.monotonic(), heartbeat_seconds=self.heartbeat_seconds
        )
        return token

    def send_task_success(self, token: str) -> bool:
        approval = self.pending.get(token)
        if not approval or approval.resolved:
            return False
        approval.resolved = True
        approval.approved = True
        return True

    def send_task_failure(self, token: str) -> bool:
        approval = self.pending.get(token)
        if not approval or approval.resolved:
            return False
        approval.resolved = True
        approval.approved = False
        return True

    def sweep(self, now: float) -> None:
        for token, approval in self.pending.items():
            if not approval.resolved and now - approval.created_at > approval.heartbeat_seconds:
                self.escalate(token)


if __name__ == "__main__":
    escalated: list = []
    gate = ApprovalGate(heartbeat_seconds=0.0, escalate=lambda t: escalated.append(t))
    tok = gate.wait_for_task_token()
    gate.sweep(now=time.monotonic() + 1.0)
    print("escalated after heartbeat miss:", escalated == [tok])
    print("success resolves once:", gate.send_task_success(tok), gate.send_task_success(tok))
```

### Go, a task manager that reassigns to a supervisor group on a missed deadline

```go
package main

import "fmt"

type TaskState string

const (
	StateQueued    TaskState = "queued"
	StateClaimed   TaskState = "claimed"
	StateCompleted TaskState = "completed"
	StateEscalated TaskState = "escalated"
)

type Task struct {
	ID              string
	CandidateGroup  string
	State           TaskState
	ClaimedBy       string
	DeadlineElapsed bool
}

type TaskManager struct {
	tasks            map[string]*Task
	supervisorGroup  string
}

func NewTaskManager(supervisorGroup string) *TaskManager {
	return &TaskManager{
		tasks:           map[string]*Task{},
		supervisorGroup: supervisorGroup,
	}
}

func (m *TaskManager) Create(id, candidateGroup string) {
	m.tasks[id] = &Task{ID: id, CandidateGroup: candidateGroup, State: StateQueued}
}

func (m *TaskManager) Claim(id, actor string) bool {
	t, ok := m.tasks[id]
	if !ok || t.State != StateQueued {
		return false
	}
	t.State = StateClaimed
	t.ClaimedBy = actor
	return true
}

func (m *TaskManager) Complete(id, actor string) bool {
	t, ok := m.tasks[id]
	if !ok || t.State != StateClaimed || t.ClaimedBy != actor {
		return false
	}
	t.State = StateCompleted
	return true
}

func (m *TaskManager) EscalateOverdue() []string {
	var escalated []string
	for _, t := range m.tasks {
		if t.State == StateQueued && t.DeadlineElapsed {
			t.State = StateEscalated
			t.CandidateGroup = m.supervisorGroup
			escalated = append(escalated, t.ID)
		}
	}
	return escalated
}

func main() {
	m := NewTaskManager("supervisors")
	m.Create("task-1", "loan-officers")
	m.tasks["task-1"].DeadlineElapsed = true
	fmt.Println(m.EscalateOverdue())
	fmt.Println(m.tasks["task-1"].CandidateGroup)
}
```
