---
name: Human in the Loop
slug: human-in-the-loop
family: 17-ai-agentic
category: AI Agentic
aliases: [HITL, Human-in-the-Loop Oversight, Interrupt and Resume, Approval Gate, Wait for Human Input]
first_described: "U.S. Department of Defense Modeling and Simulation Glossary, DoD 5000.59-M, 1998 (simulation taxonomy); re-purposed for LLM agent frameworks circa 2023 to 2024"
maturity: established
related: [react, orchestrator-worker, plan-execute, function-calling, input-guardrails, output-guardrails, agent-handoff, chain-of-responsibility]
incompatible_with: []
verified: 2026-08-02
---

# Human in the Loop

## 1. Name, aliases, and lineage

The canonical name in agentic AI systems is Human in the Loop, almost always
abbreviated HITL. The term did not originate in software architecture. It comes
from modeling and simulation, where it distinguishes a live simulation
(a real human operating real equipment), a virtual simulation (a real human
operating simulated equipment), and a constructive simulation (simulated
entities operating simulated equipment, no human required for any single
decision). The U.S. Department of Defense Modeling and Simulation Glossary,
DoD 5000.59-M, 1998, is the earliest formal definition on record and anchors
the live, virtual, constructive taxonomy that later commentary traces the term
back to ([Wikipedia, "Human-in-the-loop"](https://en.wikipedia.org/wiki/Human-in-the-loop),
verified 2026-08-02). The same article records the second major lineage, in
machine learning, where HITL names the practice of humans aiding a system in
producing a correct model, most visibly through labeling, ranking, and
correction of training data.

Both lineages converge in agentic AI, and the convergence is the reason the
term needed a fresh definition rather than an inherited one. An LLM agent is
neither a simulated entity nor a static trained model. It is a running process
that plans, calls tools, and takes consequential actions, and the open
question at each step is not "was the training data correct" but "should this
specific action be allowed to happen without a person confirming it." Framework
authors adopted the existing HITL vocabulary because the shape is the same, a
human sits somewhere in the decision loop, but the mechanics are new, a paused
execution, a resumable state, and a decision surfaced to a person before the
agent proceeds.

Aliases in current framework documentation. **Interrupt and Resume** is
LangGraph's own name for the mechanism, distinct from the pattern's conceptual
name ([LangChain, LangGraph documentation, "Interrupts"](https://docs.langchain.com/oss/python/langgraph/interrupts),
verified 2026-08-02). **Approval Gate** and **Wait for Human Input** describe
the same shape in workflow-orchestration and RPA vocabularies, most visibly the
callback task token pattern in AWS Step Functions, discussed in dimension 9.
**Human-in-the-Loop Oversight** is the phrasing Anthropic uses in its own
guardrail documentation, distinct from HITL as a training signal, to mean a
person confirming an agent's action before it executes
([Anthropic, "Computer use tool", Security considerations](https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/computer-use-tool),
verified 2026-08-02).

A related but distinct concept, human on the loop, describes a human who
monitors an autonomous system and can intervene, but is not consulted before
each decision. Human in the loop is stronger, the action does not proceed at
all until a person acts. This entry covers human in the loop. Human on the
loop is a form of the Observability pattern family combined with an emergency
stop, not covered here.

## 2. Problem and context

An agent is given a goal and a set of tools, and it plans and executes a
sequence of tool calls autonomously. Some of the actions in that sequence are
reversible and low-stakes, reading a file, calling a search API, summarizing a
document. Others are irreversible, expensive, or affect a system the agent
does not own, sending an email to a real customer, deleting a database table,
transferring money, merging code to a production branch, running a shell
command with `rm -rf`, or purchasing something with a person's credit card.

The naive response is to give the agent full autonomy and trust its judgment,
or to give the agent no autonomy and require a person to approve every single
step. Neither works. Full autonomy over destructive tools produces the
documented failure mode where a coding agent runs a database migration it
misread, or a browsing agent completes a purchase the person only asked it to
research, a category of incident this entry returns to in dimension 11.
Full manual approval defeats the reason an agent exists, which is to remove
the person from the loop for the ninety percent of actions that are safe and
repetitive.

The context that produces Human in the Loop is a system where the cost of an
autonomous action varies wildly by action type, and the agent's own confidence
in a given action does not reliably predict whether that action is safe. In
that context, the right design is not a binary autonomous versus manual
switch, but a mechanism that lets the agent proceed unattended on the actions
that are safe by policy, and pause, preserve its exact state, and hand control
to a person at the specific decision points that are not. The agent resumes
from exactly where it stopped once the person answers, rather than restarting
the whole task or losing the context it had built up.

This differs from a synchronous confirmation dialog in a traditional
application. A web form's confirmation modal blocks a single request response
cycle that a server is actively holding open. An agent's pause can last
seconds or days, the process that raised the question may not be the process
that resumes it, and the state being preserved is not one HTTP request but an
entire multi-step reasoning trajectory, tool call history, and partial plan.
That durability requirement is what separates Human in the Loop, as an agentic
pattern, from an ordinary confirmation prompt.

## 3. Forces

- **Autonomy versus control.** Favors control at the specific decision points
  configured, autonomy everywhere else. The pattern's entire value is that it
  does not force an all-or-nothing choice between the two.
- **Latency.** Sacrificed at the interrupt points, sometimes severely. A pause
  waiting on a person can last from seconds to days, and the agent's forward
  progress on that branch of work stops entirely until the person responds.
- **Safety.** Favored, and this is the dominant reason the pattern exists.
  A person reviewing an irreversible action before it executes is the last
  line of defense against a plan that looked reasonable to the model and is
  wrong in a way only a domain expert would catch.
- **Throughput.** Sacrificed in proportion to how many decision points are
  gated. An agent with an approval gate on every tool call has traded almost
  all of its throughput advantage over a human doing the task directly.
- **State management complexity.** Sacrificed. The system must durably persist
  the agent's exact execution state across an arbitrarily long pause, which
  rules out holding state only in a process's memory or an open request. This
  forces a checkpointing or event sourcing mechanism that a fully autonomous
  agent does not need.
- **Trust calibration.** Favored over time. Every approved or rejected
  decision is a labeled example of what the organization considers acceptable,
  which is the raw material for later loosening the gate on that action type
  or leaving it in place with evidence rather than guesswork.
- **User experience for the operator.** Sacrificed unless the interrupt payload
  is designed well. A person asked to approve an action with no context has to
  reconstruct what the agent was doing before they can decide, which is slower
  and less reliable than the agent surfacing the specific question, the
  relevant diff, and the consequence of each answer.
- **Cost.** Sacrificed in wall clock terms during the pause, and in
  operational terms because a human reviewer is now a required, and often the
  scarcest, resource in the pipeline. This is the same throughput limiting
  cost every review gate imposes, whether the reviewer is a code reviewer or
  a content moderator.

A pattern that removed the human from every decision would not be this
pattern. The cost is paid in exactly the places autonomy is withheld, and a
badly designed gate withholds it in far more places than the risk justifies,
which is the central failure mode covered in dimension 11.

## 4. Applicability and non-applicability

Reach for Human in the Loop when the following hold.

- The action is irreversible, or reversal is costly enough that prevention is
  cheaper than remediation. Deleting production data, sending an external
  communication, executing a financial transaction, or merging code to a
  protected branch.
- The action's correctness cannot be fully verified by the agent's own tools.
  A code change can be linted and tested, but whether it is the right change
  for the business is a judgment call outside the agent's available signals.
- Regulatory, legal, or contractual obligation requires a named human to have
  approved the action, independent of whether the agent would have gotten it
  right. Financial trades, medical decisions, and legal filings commonly carry
  this requirement regardless of how capable the underlying model is.
- The action crosses a trust boundary the agent does not fully control, an
  external API with side effects on a third party's system, a payment
  processor, or another team's infrastructure the agent has access to but no
  ownership of.
- The organization is early in its trust relationship with a given agent or
  a given class of task, and wants supervised operation while it gathers
  evidence before loosening the gate. This is a deliberately temporary
  applicability, revisited as dimension 14 describes.
- A prompt injection classifier or guardrail has flagged the current context
  as suspicious, even if the underlying action would normally be autonomous.
  Anthropic's own guidance for the computer use tool is explicit on this
  point, describing an automatic escalation to a confirmation prompt when its
  classifiers detect a likely prompt injection in a screenshot
  ([Anthropic, computer use tool documentation, Security considerations](https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/computer-use-tool),
  verified 2026-08-02).

Do not reach for Human in the Loop in these cases, and the reason matters more
than the rule.

- **The action is fully reversible and cheap to reverse.** A read only query,
  a draft that has not been sent, a staging environment deploy that can be
  rolled back automatically. Gating these produces the exact throughput loss
  the pattern exists to avoid, for no safety gain. Use an automated rollback
  or a post hoc audit log instead, see dimension 16.
- **The agent's own capability, not the action's risk, is the actual concern.**
  If the model is simply unreliable at a task, the fix is better prompting,
  better tools, a smaller scope, or an automated evaluator, not a person
  rubber stamping every output. A human approval gate around a fundamentally
  unreliable agent produces reviewer fatigue and rubber stamping long before
  it produces genuine oversight, see dimension 11.
- **The volume of decisions vastly exceeds available human attention.** A
  content moderation pipeline reviewing every single post before it goes
  live does not scale past a small user base. The honest alternative at scale
  is automated filtering with human review of a statistically chosen sample,
  or of the subset the automated system itself flags as uncertain, which is
  the applicability boundary between this pattern and Output Guardrails.
- **The decision genuinely has no better answer available to a human than to
  the model.** If a person given the same context and the same time budget
  would make the same call the model made, with no additional information the
  model lacked, the gate adds latency without adding safety. This is common
  in low stakes classification and routing decisions.
- **The system needs to operate when no human is available**, an overnight
  batch job, a disaster recovery failover, an on call page triaged with
  nobody awake to answer an approval prompt. A hard dependency on human
  availability in a system that must run unattended is a liveness bug, not a
  safety feature, unless the gate has an explicit, deliberate default deny
  timeout policy that the team has accepted.
- **The interrupt payload cannot give the reviewer enough context to decide
  correctly.** A gate that asks for a bare approve or deny with no rendering
  of what is about to happen produces decisions no better than chance, worse
  than no gate at all because it manufactures false confidence that oversight
  occurred.

## 5. Structure

Five participants, named by the role they play in the interaction.

- **Agent (or Node).** The autonomous unit of execution that reaches a point
  in its plan where it must pause. It does not decide on its own whether to
  pause, that decision is made by policy, described below, but it is the
  agent's own execution that halts and later resumes.
- **Interrupt Point (or Gate).** A specific location in the agent's control
  flow, configured in advance, where execution is suspended and a payload
  describing the pending decision is emitted. This is a design time decision
  about where risk concentrates, not a runtime decision the agent negotiates.
- **State Store (or Checkpointer).** The durable persistence layer that
  captures the agent's complete execution state at the moment of the pause,
  the conversation history, the partial plan, any accumulated tool results,
  and a unique identifier for this specific pause. Without this participant
  the pause cannot survive a process restart, a different reviewer answering
  hours later, or a distributed system where the pausing process and the
  resuming process are not the same process.
- **Human Reviewer.** The person who receives the interrupt payload, evaluates
  it against context the agent may not have, and produces a decision, approve,
  reject, or modify and approve. The reviewer's decision is the sole input
  that determines what happens next, the agent does not proceed on a default.
- **Resume Mechanism.** The API or function that accepts the reviewer's
  decision, rehydrates the agent's saved state, and continues execution as if
  the pause had never happened except for the new information the decision
  supplies. LangGraph names this participant `Command(resume=...)` explicitly
  ([LangChain, "Interrupts"](https://docs.langchain.com/oss/python/langgraph/interrupts),
  verified 2026-08-02), and Step Functions names it the `SendTaskSuccess` and
  `SendTaskFailure` API calls against a task token
  ([AWS, "Wait for a Callback with Task Token"](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html),
  verified 2026-08-02).

Relationship. The Agent never talks to the Human Reviewer directly. It emits a
payload to the Interrupt Point, which the State Store persists, and which some
delivery mechanism, a UI, a Slack message, an email, a queue consumer,
presents to the Human Reviewer. The Reviewer's answer flows back through the
Resume Mechanism, which reads the State Store, not through a channel back to
the Agent's original process. This indirection through durable state, rather
than a direct synchronous call, is what allows the pause to outlive the
process that created it.

## 6. ASCII structure diagram

```
   +------------------------+
   |         Agent          |
   |  (plans, calls tools)  |
   +-----------+------------+
               |
               | reaches configured
               | Interrupt Point
               v
   +------------------------+          +--------------------------+
   |     Interrupt Point    | -------> |       State Store         |
   |  (policy: pause here)  | persist  |  (checkpointer, thread_id |
   +-----------+------------+          |   or task token, payload) |
               |                       +-------------+-------------+
               | payload surfaced                     |
               v                                       |
   +------------------------+                          |
   |    Delivery Surface    |                           |
   |  (UI, Slack, email,    |                           |
   |   queue, dashboard)    |                           |
   +-----------+------------+                          |
               |                                        |
               v                                        |
   +------------------------+                           |
   |    Human Reviewer      |                           |
   |  approve / reject /    |                           |
   |  modify and approve    |                           |
   +-----------+------------+                           |
               |                                        |
               | decision                                |
               v                                        |
   +------------------------+   rehydrate state   <------+
   |    Resume Mechanism    | ------------------->
   |  Command(resume=...)   |
   |  or SendTaskSuccess    |
   +-----------+------------+
               |
               | agent resumes with
               | decision injected
               v
   +------------------------+
   |         Agent          |
   |  (continues execution) |
   +------------------------+
```

## 7. Dynamics

The sequence has a property worth stating plainly before the diagram, the
process that raises the interrupt is frequently not the process that resumes
it. A web server that handled the agent's initial request may have long since
returned and been recycled by the time a reviewer answers a Slack message
three hours later. Everything the resuming process needs must therefore live
in the State Store, never in the memory of the process that paused.

```
Agent            Interrupt Point       State Store          Reviewer
  |                    |                    |                   |
  |-- reach gated ---->|                    |                   |
  |   tool call        |                    |                   |
  |                    |-- persist state -->|                   |
  |                    |   + payload        |                   |
  |                    |<-- ack ------------|                   |
  |<-- execution ------|                    |                   |
  |   paused           |                    |                   |
  .                    .                    .                   .
  .   (arbitrary time gap, seconds to days, process may exit)   .
  .                    .                    .                   .
  |                    |                    |-- payload ------->|
  |                    |                    |   delivered       |
  |                    |                    |                   |
  |                    |                    |<-- decision ------|
  |                    |                    |   (approve/deny/  |
  |                    |                    |    modify)        |
  |                    |                    |                   |
  |<---------------------- rehydrate state -|                   |
  |   resume execution                      |                   |
  |   with decision injected                |                   |
  |                    |                    |                   |
  |-- continues plan ->|                    |                   |
  |   (or halts if     |                    |                   |
  |    denied)         |                    |                   |
```

Two properties this diagram makes visible. First, the arbitrary time gap is
not a defect to be optimized away, it is the entire point of durable
persistence over a held open synchronous call. A held open HTTP connection
cannot survive a server restart or a reviewer who is asleep. A checkpoint in a
durable store can. Second, denial is a first class outcome, not an error path
grafted on. The agent's plan must define what happens on rejection just as
carefully as what happens on approval, otherwise a denied action leaves the
plan in an undefined state, which is one of the failure modes in dimension 11.

## 8. Implementation variants

**Blocking interrupt inside a graph node.** The agent framework itself
provides a function that, called from inside a node's execution, halts that
node, serializes the graph's current state via a checkpointer, and returns
control to the caller. LangGraph's `interrupt()` is this variant. It "can be
placed anywhere in your code and can be conditional based on your application
logic," and resumption uses `Command(resume=...)`, whose value becomes the
return value of the original `interrupt()` call inside the node
([LangChain, "Interrupts"](https://docs.langchain.com/oss/python/langgraph/interrupts),
verified 2026-08-02). Strongest ergonomics for developers, since the pause
reads as an ordinary blocking function call in the source. Costs a hard
dependency on the framework's own checkpointing infrastructure, and on
replaying the node from its start on resume, which requires the node's code
before the interrupt call to be side effect free or idempotent.

**Permission decision hook at the tool call boundary.** Rather than the
agent's own logic deciding to pause, an external policy layer intercepts every
tool call before it executes and returns one of a small set of verdicts. Claude
Code's PreToolUse hooks implement this as a `permissionDecision` field with
values `allow`, `deny`, `ask`, or a pass through default, where `ask`
specifically escalates "to user for manual approval" via a permission prompt,
independent of anything the agent's own reasoning decided
([Anthropic, "Hooks reference"](https://code.claude.com/docs/en/hooks),
verified 2026-08-02). This variant's strength is that the policy lives outside
the agent's prompt and cannot be argued out of by a prompt injection targeting
the model's reasoning, because the hook evaluates the raw tool call, not the
model's stated intent. Its cost is that the policy layer needs its own
matching language for which tool calls trigger which verdict, and a poorly
written matcher either under gates, real risk slips through, or over gates,
the pattern's throughput cost from dimension 3 dominates.

**Callback task token in a workflow orchestrator.** Outside the LLM agent
world, this variant predates agentic AI and the framework simply reuses it.
The orchestrator hands a task an opaque token, publishes the token alongside a
description of the pending decision to an external system, a queue, an email,
an SNS topic, and the workflow does not advance until that exact token comes
back attached to a `SendTaskSuccess` or `SendTaskFailure` call. AWS Step
Functions calls this `.waitForTaskToken`, states plainly that a task might
need to wait for a human approval, and exposes a `HeartbeatSeconds` field so
a token that never returns times out rather than blocking the state machine
indefinitely ([AWS, "Wait for a Callback with Task Token"](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html),
verified 2026-08-02). This variant decouples the orchestrator entirely from
the delivery mechanism, any system capable of calling two API endpoints can be
the human interface, at the cost of needing an explicit timeout policy, since
nothing about the token itself guarantees a human ever sees it.

**Confidence threshold routing.** Rather than a fixed set of gated action
types, the agent, or a downstream classifier, attaches a confidence score to
its own output, and only scores below a configured threshold route to a
human. This is the variant most associated with active learning and
production ML review queues, where the goal is to spend scarce human review
capacity on the cases the automated system is least sure about, rather than a
fixed category of action. It composes naturally with Output Guardrails, which
is where the confidence score is typically computed. Its risk is that a
poorly calibrated model can be confidently wrong, which routes exactly the
cases that most need review away from the human.

**Training time human correction, RLHF.** A structurally different variant
worth naming because it shares the term but not the runtime mechanics. Rather
than pausing a running agent for a per action decision, human judgment is
collected once, offline, as rankings over candidate model outputs, and used to
train a reward model that then shapes the base model's behavior through
reinforcement learning. Ouyang, Wu, Jiang, Almeida, Wainwright, Mishkin,
Zhang, Agarwal, Slama, Ray, Schulman, Hilton, Kelton, Miller, Simens, Askell,
Welinder, Christiano, Leike, and Lowe, "Training language models to follow
instructions with human feedback," arXiv:2203.02155, 2022, describes exactly
this pipeline, supervised fine tuning on human demonstrations, a reward model
trained on human rankings of model outputs, then reinforcement learning
against that reward model ([arXiv:2203.02155](https://arxiv.org/abs/2203.02155),
verified 2026-08-02). This variant produces a model that behaves better on
average across all future runs, but it offers no per decision veto at
inference time, so it does not substitute for a runtime interrupt when a
specific action needs a specific person's sign off.

## 9. Known production uses

- **LangGraph (LangChain).** Ships `interrupt()` as a first class primitive
  for pausing a graph node, persisting state via a checkpointer keyed by
  `thread_id`, and resuming with `Command(resume=...)`, documented as the
  framework's recommended mechanism for review, editing, or approval of agent
  actions ([LangChain, "Interrupts"](https://docs.langchain.com/oss/python/langgraph/interrupts),
  verified 2026-08-02).
- **Claude Code (Anthropic).** Its hooks system supports a `PreToolUse` hook
  returning `permissionDecision: "ask"`, which displays "a permission prompt
  asking the user to allow or deny the tool call" before that specific tool
  call executes, alongside `"deny"` for an unconditional block and `"allow"`
  for an unconditional pass through, giving policy level control over which
  categories of agent action require a human ([Anthropic, "Hooks reference"](https://code.claude.com/docs/en/hooks),
  verified 2026-08-02).
- **Anthropic's computer use tool.** The product documentation itself
  recommends asking a human to confirm decisions that might result in
  meaningful real world consequences and any tasks requiring affirmative
  consent, such as accepting cookies, completing financial transactions, or
  agreeing to terms of service, and describes an automated escalation to a
  confirmation prompt when its prompt injection classifiers flag a screenshot
  as suspicious, explicitly noting this protection is not ideal for every use
  case, "for example, use cases without a human in the loop"
  ([Anthropic, "Computer use tool", Security considerations](https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/computer-use-tool),
  verified 2026-08-02).
- **AWS Step Functions.** The `.waitForTaskToken` service integration pattern
  is documented with human approval named as a primary use case, "a task
  might need to wait for a human approval," implemented via an opaque task
  token that an external process, including a person acting through email or
  a UI, must return through the `SendTaskSuccess` or `SendTaskFailure` API
  before the state machine advances, with a configurable `HeartbeatSeconds`
  timeout to prevent an indefinite stall ([AWS, "Wait for a Callback with Task
  Token"](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html),
  verified 2026-08-02).
- **RLHF pipelines (OpenAI, and the broader field following InstructGPT).**
  As the training time variant described in dimension 8, human labelers rank
  candidate model outputs, and that ranking data trains a reward model used to
  fine tune the base model via reinforcement learning, a pipeline the paper
  credits with producing a 1.3 billion parameter model whose outputs were
  preferred to outputs from the 175B GPT-3, "despite having 100x fewer
  parameters" ([Ouyang et al., arXiv:2203.02155](https://arxiv.org/abs/2203.02155),
  verified 2026-08-02).

## 10. Consequences

Positive.

- Catches irreversible mistakes before they happen, rather than after, which
  is the only point in the pattern's lifecycle where the cost of catching an
  error is bounded by the cost of the review rather than the cost of the
  mistake.
- Produces an auditable decision trail, every gated action carries a record of
  who approved it and when, which satisfies compliance requirements that a
  fully autonomous system cannot satisfy by construction.
- Lets an organization deploy an agent into a risk bearing workflow before it
  has fully earned trust, because the blast radius of a wrong decision is
  capped at whatever the human reviewer would have caught.
- Generates labeled data, in the form of approve, reject, or modify decisions,
  that is directly usable to tighten prompts, adjust tool permissions, or in
  the training time variant, retrain the model itself.
- Decouples policy from model capability, an organization can change which
  actions require approval without touching the agent's prompt or code,
  because the gate lives at the tool call or workflow boundary, not inside
  the model's reasoning.

Negative.

- Introduces unbounded latency at every gated point, from seconds to days
  depending on reviewer availability, which the calling system must design
  for explicitly rather than assume away.
- Requires durable state persistence the fully autonomous version of the same
  agent does not need, which is real infrastructure, a checkpointer, a
  database, or a workflow engine, not a minor implementation detail.
- Creates a scarce resource bottleneck out of human attention, a system that
  gates too many action types produces a review queue that grows faster than
  reviewers can clear it, at which point the gate stops being a safety
  mechanism and becomes a throughput ceiling.
- Habituates reviewers to rubber stamping when the gate fires too often on
  low stakes decisions, which quietly erodes the safety property the pattern
  exists to provide, covered in detail in dimension 11.
- Adds a genuine new failure surface, a lost, corrupted, or expired token or
  checkpoint strands the agent's work with no way to resume it short of
  starting over, which the pattern's own durability requirement was supposed
  to prevent.

## 11. Failure modes and misuse

**Symptom.** Reviewers approve every request within seconds of it arriving,
regardless of content, and post incident review shows the approved action was
clearly wrong on inspection.
**Cause.** Gate fatigue. Too many low stakes actions are routed through the
same approval channel as genuinely high stakes ones, so reviewers learn that
most requests are safe to wave through and stop reading them carefully. This
is the human equivalent of alert fatigue in monitoring systems.
**Fix.** Audit the gate's trigger conditions against dimension 4's
applicability list and remove any low stakes action from the gated set.
Reserve the approval channel for the subset of decisions where a genuine
mistake is expensive, and route everything else to an automated policy or a
post hoc sampled review instead.

**Symptom.** The agent's plan continues to reference an action that was
rejected, or crashes with a state error, some time after a reviewer denied it.
**Cause.** The resume path was implemented only for the approval branch. The
denial path was never designed, so injecting a rejection into the resumed
agent produces a state the rest of the plan never anticipated.
**Fix.** Treat denial as a first class outcome from the start, the same way
dimension 7 requires. Design what the agent does on rejection, retry with
modification, ask a different question, abandon the branch, before the gate
ships, not after the first denial in production surfaces the gap.

**Symptom.** A pending approval sits unresolved for days, silently, until
someone notices the agent's task never completed.
**Cause.** No timeout or escalation policy on the pause itself. The pattern's
durability, correctly implemented, means the pause never expires on its own,
which without an explicit policy becomes an indefinite silent stall rather
than a bounded wait.
**Fix.** Attach a heartbeat or timeout to every interrupt, exactly as AWS Step
Functions' `HeartbeatSeconds` does for its callback tokens, with a defined
default action, escalate to a second reviewer, cancel the branch, or auto
deny, when the timeout fires.

**Symptom.** The gate never fires at all for an action the team explicitly
intended to require approval.
**Cause.** The matcher or policy that decides which actions are gated is
either too narrow, matching an exact string that the agent's actual tool call
does not produce verbatim, or evaluates the model's stated intent rather than
the literal tool call, which a prompt injection or a subtly rephrased request
can slip past.
**Fix.** Evaluate the gate against the literal tool call and its parameters,
not the model's natural language explanation of what it is about to do. Test
the matcher against paraphrased and adversarial variants of the gated action,
not only the canonical example used to write it.

**Symptom.** The reviewer approves an action that turns out to be based on a
misunderstanding of what the agent actually intended, and the post incident
review shows the approval UI displayed too little information to catch it.
**Cause.** The interrupt payload surfaces a generic confirm or deny prompt
instead of the specific consequence of the action, the diff, the recipient,
the amount, the destination.
**Fix.** Design the interrupt payload as a first class UI artifact, not an
afterthought. Surface exactly what will happen if approved, in the reviewer's
domain language, not the agent's internal tool call schema.

## 12. Trade-off matrix

| Force | Human in the Loop | Output Guardrails | Fully Autonomous Agent |
|---|---|---|---|
| Latency per action | High at gated points, unbounded | Low, automated check only | Lowest, no pause |
| Catches novel or judgment-based errors | Yes, human judgment applies | Only errors the guardrail was built to detect | No |
| Scales with request volume | Poorly, bounded by reviewer capacity | Well, fully automated | Best |
| Auditable decision trail | Yes, per gated action | Only if the guardrail logs its verdict | No, unless separately instrumented |
| Requires durable state persistence | Yes, a hard requirement | No | No |
| Works when no human is available | No, unless a timeout default is defined | Yes | Yes |
| Risk of reviewer fatigue eroding safety | Yes, a named failure mode | No, no human in the automated path | Not applicable |
| Appropriate for irreversible actions | Yes, primary use case | Only for content-shape errors, not consequence | No |

Output Guardrails and Human in the Loop are frequently combined rather than
chosen between, a guardrail screens every action automatically and routes
only the subset it flags as risky, uncertain, or policy violating to a human
gate, which is the confidence threshold variant from dimension 8.

## 13. Related and incompatible patterns

**ReAct** and **Plan-Execute** are the agent control flow patterns that
Human in the Loop attaches to. Neither defines where a pause belongs, Human
in the Loop is the mechanism that turns a specific step in either loop into a
gated one, without changing the loop's own reasoning structure.

**Orchestrator-Worker** and **Agent Handoff** compose naturally with Human in
the Loop when the handoff target is a person rather than another agent. A
handoff to a human reviewer uses the identical durable state and resume
mechanics described in this entry, the receiving party is simply not another
autonomous process.

**Function Calling** is the substrate this pattern most often gates, the
interrupt point in the permission decision hook variant sits directly at the
boundary where the model's tool call would otherwise execute.

**Input Guardrails** and **Output Guardrails** are the fully automated
siblings of this pattern, they screen content without pausing for a human at
all, and are the appropriate choice wherever dimension 4's non applicability
list says a human review is unnecessary. The confidence threshold variant
described in dimension 8 is the explicit bridge between the two families, a
guardrail decides which cases escalate to a human gate.

**Chain of Responsibility** is the structural pattern a permission decision
hook chain resembles most closely, a sequence of handlers each able to allow,
deny, or pass a request along, which is exactly what a chain of PreToolUse
hooks implements at the tool call boundary.

No pattern in this catalog is flagged incompatible with Human in the Loop, it
is an orthogonal control layer that can be attached to essentially any
agentic control flow pattern, at the cost described in dimension 10.

## 14. Refactoring path in and out

**Introducing the pattern into an existing fully autonomous agent.** Start by
instrumenting, not gating. Log every tool call the agent makes for a period
before adding a single approval gate, and use that log to identify which
action types are actually high consequence in practice rather than guessing.
Add the gate to the smallest set of action types the evidence supports,
implement the denial path from the start per dimension 11's second failure
mode, and add a timeout policy before the first gate ships, not after the
first stuck approval. Only then widen the gated set if the log continues to
show risk the initial set missed.

**Loosening a gate that has proven itself.** This is the refactor most teams
skip, and skipping it is why over gated systems accumulate reviewer fatigue
rather than shrinking their gated surface over time. Once an action type has
accumulated a sufficient volume of approvals with a near zero rejection rate
and no post incident findings tracing back to it, move it from the gated set
to an automated policy, or to the confidence threshold variant so only the
unusual instances of that action still route to a human. The approval history
itself is the evidence base for this decision, which is why dimension 10 lists
it as a positive consequence in its own right.

**Removing the pattern entirely.** Justified only when an action type has
been fully automated to the point that a human reviewer adds no signal the
automated check does not already provide, or when the action itself has been
made safely reversible, at which point the applicability list in dimension 4
no longer holds and the gate should be replaced with a post hoc audit log
rather than removed with no replacement.

## 15. Testing and verification

Testing this pattern splits into two genuinely different concerns, and
conflating them is a common mistake. First, does the gate fire on the correct
set of actions, and never fire on the wrong ones. Second, does the resume
mechanism correctly rehydrate state and continue execution, for every possible
reviewer decision, not only the approval path.

For the first concern, write the matcher's test suite against the literal
tool call and parameters the agent actually produces, including paraphrased
and adversarial variants, per dimension 11's fourth failure mode, not only
against the canonical example that motivated the gate. A gate that only ever
sees its own example in testing will pass every test and still miss real
cases in production.

For the second concern, this pattern is unusually well suited to systematic
state machine testing, because the set of reachable states is small and
enumerable, paused awaiting approval, resumed with approval, resumed with
denial, resumed with modification, timed out. Write an explicit test for each
transition, asserting both that state is correctly persisted at the pause and
correctly rehydrated at the resume, including the case where the resuming
process is a different process from the one that paused, which is the
scenario most manual testing accidentally skips because a developer testing
locally naturally resumes in the same process.

The timeout and denial paths from dimension 11 are the two most under tested
branches in real codebases using this pattern, because they are the least
common path in a demo but among the most common paths in a production
incident. Both belong in the test suite from the first implementation, not
added after the first production stall.

## 16. Observability signals

Track, per gated action type, the volume of interrupts raised, the approval
rate, the median and tail time to decision, and the rate of denials that
required an escalation or a modified resubmission rather than a clean approve
or reject. A healthy gate shows a stable approval rate over time with a time
to decision that matches the reviewer team's actual availability, not an
unbounded tail.

An approval rate climbing toward and staying near 100 percent over a period of
weeks is the leading indicator of the gate fatigue failure mode from
dimension 11, and is worth alerting on directly, since it is invisible in a
simple pass or fail count and only shows up in the trend.

Track separately the count of pending interrupts that have exceeded their
timeout with no default action configured, since this is the observable
signature of the stuck approval failure mode, and the count of denials whose
resume path threw an error, since that is the observable signature of the
undefined denial path failure mode. Both are silent by default and both need
an explicit metric to surface.

## 17. Security and privacy implications

The gate itself is a security control, so its own integrity matters as much
as the actions it protects. If the matcher deciding which actions require
approval evaluates the model's own stated intent rather than the literal tool
call about to execute, a prompt injection can steer the model to describe a
dangerous action in benign language and slip past the gate entirely, which is
the fourth failure mode in dimension 11 and is the single most consequential
security property of this pattern to get right.

The interrupt payload frequently contains sensitive data by necessity, since
the reviewer needs enough context to make an informed decision, a customer's
personal data, financial figures, or draft communications not yet sent. That
payload's delivery surface, a Slack channel, an email, a shared dashboard,
inherits whatever access control that surface provides, and a gate designed
to add safety can become a data exposure vector if the delivery channel is
broader than the set of people who should legitimately see the pending
action's contents.

The durable state store holding a paused agent's checkpoint is itself an
attack surface, an attacker who can write to or replay entries in that store
can potentially forge a resume with a fabricated approval, which is why AWS
Step Functions scopes task tokens to the account that issued them and states
plainly that task tokens must be passed "from principals within the same AWS
account," and that "the tokens won't work if you send them from principals in
a different AWS account" ([AWS, "Wait for a Callback with Task Token"](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html),
verified 2026-08-02). Any implementation of this pattern should treat the
resume token or checkpoint identifier with the same handling discipline as a
session token, unguessable, scoped, and time bounded, rather than as an
opaque convenience value.

## 18. References

1. Wikipedia contributors. "Human-in-the-loop." https://en.wikipedia.org/wiki/Human-in-the-loop
   Verified 2026-08-02. Source for the term's origin in the Department of
   Defense Modeling and Simulation Glossary, DoD 5000.59-M, 1998, the live,
   virtual, constructive taxonomy, and the machine learning lineage of the
   term.
2. LangChain. LangGraph documentation, "Interrupts."
   https://docs.langchain.com/oss/python/langgraph/interrupts
   Verified 2026-08-02. Source for the `interrupt()` function, checkpointer
   state persistence keyed by `thread_id`, and the `Command(resume=...)`
   resume mechanism described across dimensions 1, 5, 7, 8, and 9.
3. Anthropic. "Hooks reference," Claude Code documentation.
   https://code.claude.com/docs/en/hooks
   Verified 2026-08-02. Source for the `PreToolUse` hook `permissionDecision`
   field and its `allow`, `deny`, and `ask` verdicts described in dimensions
   8 and 9.
4. Anthropic. "Computer use tool," Security considerations section.
   https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/computer-use-tool
   Verified 2026-08-02. Source for the recommendation to ask a human to
   confirm consequential decisions, the automated escalation on detected
   prompt injection, and the explicit use of the phrase "human in the loop,"
   described in dimensions 1, 4, and 9.
5. Amazon Web Services. "Discover service integration patterns in Step
   Functions," Wait for a Callback with Task Token.
   https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html
   Verified 2026-08-02. Source for the task token callback mechanism,
   `HeartbeatSeconds` timeout, `SendTaskSuccess` and `SendTaskFailure` API
   calls, and the account scoping security property, described in dimensions
   8, 9, 11, and 17.
6. Ouyang, Long; Wu, Jeff; Jiang, Xu; Almeida, Diogo; Wainwright, Carroll L.;
   Mishkin, Pamela; Zhang, Chong; Agarwal, Sandhini; Slama, Katarina; Ray,
   Alex; Schulman, John; Hilton, Jacob; Kelton, Fraser; Miller, Luke; Simens,
   Maddie; Askell, Amanda; Welinder, Peter; Christiano, Paul; Leike, Jan; and
   Lowe, Ryan. "Training language models to follow instructions with human
   feedback." arXiv:2203.02155, 2022. https://arxiv.org/abs/2203.02155
   Verified 2026-08-02. Source for the RLHF pipeline, the supervised fine
   tuning plus reward model plus reinforcement learning sequence, and the
   1.3B versus 175B preference result, described in dimensions 8, 9, and 10.

## Code examples

Three languages that cover the pattern's three real implementation shapes.
TypeScript shows the permission decision hook variant, the shape used by
Claude Code's own hooks and any policy layer sitting at a tool call boundary.
Python shows the durable, resumable checkpoint variant, the shape LangGraph
implements natively. Go shows the callback token variant, the shape a
workflow orchestrator like Step Functions implements, using a channel backed
in memory store to keep the example runnable without external infrastructure.
Rust is omitted because the pattern's interesting complexity lives in
persistence and delivery, not in language level concurrency or memory safety,
and the shape adds nothing a Go or Python reader does not already see.

### TypeScript

Permission decision hook. A policy function evaluated against every tool call
before execution, independent of the agent's own reasoning.

```typescript
type Verdict = "allow" | "deny" | "ask";

interface ToolCall {
  name: string;
  params: Record<string, unknown>;
}

interface PolicyRule {
  matches(call: ToolCall): boolean;
  verdict: Verdict;
  reason: string;
}

const rules: PolicyRule[] = [
  {
    matches: (call) => call.name === "sendEmail",
    verdict: "ask",
    reason: "Sending email to a real recipient is irreversible.",
  },
  {
    matches: (call) => call.name === "deleteRecord",
    verdict: "ask",
    reason: "Deletion cannot be undone by this agent.",
  },
  {
    matches: (call) => call.name === "readFile",
    verdict: "allow",
    reason: "Read-only, no side effects.",
  },
];

function evaluate(call: ToolCall): { verdict: Verdict; reason: string } {
  for (const rule of rules) {
    if (rule.matches(call)) {
      return { verdict: rule.verdict, reason: rule.reason };
    }
  }
  return { verdict: "ask", reason: "No matching rule, default to review." };
}

type PendingApproval = {
  call: ToolCall;
  reason: string;
  resolve: (approved: boolean) => void;
};

class ApprovalQueue {
  private pending: PendingApproval[] = [];

  request(call: ToolCall, reason: string): Promise<boolean> {
    return new Promise((resolve) => {
      this.pending.push({ call, reason, resolve });
    });
  }

  list(): PendingApproval[] {
    return this.pending;
  }

  decide(index: number, approved: boolean): void {
    const item = this.pending.splice(index, 1)[0];
    if (item) item.resolve(approved);
  }
}

async function runToolCall(
  call: ToolCall,
  queue: ApprovalQueue,
): Promise<string> {
  const { verdict, reason } = evaluate(call);
  if (verdict === "deny") {
    return `denied: ${reason}`;
  }
  if (verdict === "ask") {
    const approved = await queue.request(call, reason);
    if (!approved) {
      return `rejected by reviewer: ${call.name}`;
    }
  }
  return `executed: ${call.name}`;
}

async function main() {
  const queue = new ApprovalQueue();
  const resultPromise = runToolCall(
    { name: "sendEmail", params: { to: "customer@example.com" } },
    queue,
  );
  const pending = queue.list();
  console.log("awaiting review:", pending[0].call.name, "-", pending[0].reason);
  queue.decide(0, true);
  console.log(await resultPromise);
}

main();
```

### Python

Durable checkpoint and resume. State is written to a store keyed by a run id
before the pause, so a different process can resume the run later.

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Checkpoint:
    run_id: str
    plan: list[str]
    completed_steps: list[str] = field(default_factory=list)
    pending_step: str | None = None
    decision: bool | None = None


class CheckpointStore:
    def __init__(self) -> None:
        self._store: dict[str, Checkpoint] = {}

    def save(self, checkpoint: Checkpoint) -> None:
        self._store[checkpoint.run_id] = checkpoint

    def load(self, run_id: str) -> Checkpoint:
        return self._store[run_id]


GATED_STEPS = {"charge_customer", "delete_account"}


def run_agent(store: CheckpointStore, run_id: str, plan: list[str]) -> str:
    checkpoint = Checkpoint(run_id=run_id, plan=plan)
    for step in plan:
        if step in GATED_STEPS:
            checkpoint.pending_step = step
            store.save(checkpoint)
            return f"paused, waiting on approval for '{step}'"
        checkpoint.completed_steps.append(step)
    store.save(checkpoint)
    return f"completed, {checkpoint.completed_steps}"


def resume_agent(store: CheckpointStore, run_id: str, approved: bool) -> str:
    checkpoint = store.load(run_id)
    step = checkpoint.pending_step
    checkpoint.decision = approved
    checkpoint.pending_step = None

    if not approved:
        store.save(checkpoint)
        return f"halted, '{step}' was rejected, no further steps run"

    checkpoint.completed_steps.append(step)
    remaining = checkpoint.plan[len(checkpoint.completed_steps):]
    for next_step in remaining:
        if next_step in GATED_STEPS:
            checkpoint.pending_step = next_step
            store.save(checkpoint)
            return f"paused again, waiting on approval for '{next_step}'"
        checkpoint.completed_steps.append(next_step)

    store.save(checkpoint)
    return f"completed, {checkpoint.completed_steps}"


if __name__ == "__main__":
    store = CheckpointStore()
    plan = ["verify_identity", "charge_customer", "send_receipt"]
    print(run_agent(store, "run-42", plan))
    print(resume_agent(store, "run-42", approved=True))
```

### Go

Callback task token. The orchestrator hands out an opaque token and waits on
a channel until the exact token is returned by an external approver, with a
heartbeat timeout so a lost token does not block forever.

```go
package main

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"time"
)

type callback struct {
	approved chan bool
}

type callbackRegistry struct {
	pending map[string]*callback
}

func newRegistry() *callbackRegistry {
	return &callbackRegistry{pending: make(map[string]*callback)}
}

func (r *callbackRegistry) issueToken() string {
	buf := make([]byte, 8)
	rand.Read(buf)
	token := hex.EncodeToString(buf)
	r.pending[token] = &callback{approved: make(chan bool, 1)}
	return token
}

func (r *callbackRegistry) sendTaskSuccess(token string, approved bool) error {
	cb, ok := r.pending[token]
	if !ok {
		return errors.New("unknown or already-consumed task token")
	}
	cb.approved <- approved
	delete(r.pending, token)
	return nil
}

func waitForApproval(r *callbackRegistry, token string, heartbeat time.Duration) (bool, error) {
	cb := r.pending[token]
	select {
	case approved := <-cb.approved:
		return approved, nil
	case <-time.After(heartbeat):
		delete(r.pending, token)
		return false, errors.New("timed out waiting for human approval")
	}
}

func main() {
	registry := newRegistry()
	token := registry.issueToken()
	fmt.Println("published token to reviewer queue:", token)

	go func() {
		time.Sleep(50 * time.Millisecond)
		if err := registry.sendTaskSuccess(token, true); err != nil {
			fmt.Println("send failed:", err)
		}
	}()

	approved, err := waitForApproval(registry, token, 2*time.Second)
	if err != nil {
		fmt.Println("workflow halted:", err)
		return
	}
	if approved {
		fmt.Println("reviewer approved, workflow resumes")
	} else {
		fmt.Println("reviewer rejected, workflow halts")
	}
}
```
