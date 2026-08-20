---
name: Over-Agentification
slug: over-agentification
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Agent Sprawl, Agentic Overengineering, Agent Theater, Multi-Agent Sprawl]
first_described: "Folk knowledge, LLM systems engineering practice, no single named originator"
maturity: emerging
related: [golden-hammer, inner-platform-effect, distributed-monolith, chatty-i-o, not-invented-here, service-locator]
incompatible_with: [pipes-and-filters, transaction-script, simple-factory, rules-engine, workflow]
verified: 2026-08-02
---

# Over-Agentification

## 1. Name, aliases, and lineage

Over-Agentification is the anti-pattern of turning ordinary software steps into
autonomous or semi-autonomous LLM agents when a simpler prompt, tool call,
workflow, rules engine, queue worker, or user interface would meet the need with
less cost and less operational risk. The name is folk terminology rather than a
term from a canonical pattern catalog. This entry treats the term as emerging
systems-engineering vocabulary, because the failure mode is now visible in LLM
applications even though no single book or paper coined it.

The lineage comes from the split between workflows and agents in modern LLM
systems literature. Anthropic defines workflows as systems where LLMs and tools
follow predefined code paths, and agents as systems where the LLM directs its
own process and tool use. The same article advises teams to start with the
simplest useful design, because agentic systems trade latency and cost for task
performance, and because frameworks can hide prompts and responses behind
abstraction layers that make debugging harder (Anthropic, "Building effective
agents," https://www.anthropic.com/engineering/building-effective-agents,
verified 2026-08-02). OpenAI gives a similar boundary. Its agent guide says an
agent uses an LLM to manage workflow execution and make decisions, while an
application that uses an LLM without giving it workflow control is not an agent
(OpenAI, "A practical guide to building agents,"
https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/,
verified 2026-08-02).

The research ancestor most readers will recognize is ReAct, published by Shunyu
Yao and coauthors, which interleaves reasoning, acting, and observation so a
language model can use environment feedback during task solving. The Google
Research summary describes the method as combining reasoning traces with text
actions, where actions produce observations from an external environment
(Shunyu Yao and Yuan Cao, "ReAct. Synergizing Reasoning and Acting in Language
Models," Google Research blog, November 8, 2022,
https://research.google/blog/react-synergizing-reasoning-and-acting-in-language-models/,
verified 2026-08-02). ReAct is not the anti-pattern. Over-Agentification is
what happens when teams take the presence of an agent loop as proof that every
problem should be shaped like one.

The related names are imprecise but useful. **Agent sprawl** stresses the count
of named agents and handoffs. **Agentic overengineering** stresses needless
architecture. **Agent theater** names a system that looks autonomous in demos
but hides a rigid prompt chain, manual operations, or brittle routing under
agent branding. **Multi-agent sprawl** is the narrower case where the damage is
caused by too many communicating agents, not by one oversized agent.

This entry is intentionally classified as emerging. The problem is real enough
to name, but the industry has not settled stable language for it. The stable
part is the decision rule. Autonomy is expensive. It should be bought only when
the task needs model-chosen steps, tool choice, recovery, or planning under
uncertainty.

## 2. Problem and context

A team needs to add an LLM feature. The first working prototype is impressive,
so the architecture grows around the most exciting shape rather than the
simplest working shape. A sentiment classifier becomes a "sentiment agent." A
fixed invoice extraction flow becomes an "accounts payable agent" even though
the fields, validations, and escalation rules are known in advance. A CRUD
admin task becomes a planner that decides which internal API to call, despite
the UI already knowing the action. A support bot is split into billing,
shipping, refund, fraud, and loyalty agents before anyone has measured whether
a single routed workflow fails.

The problem is not the word agent. The problem is giving a probabilistic
planner control over work that does not need planning. The result is a system
with more prompts, more model calls, more tool schemas, more handoffs, more
traces, and more failure paths than the business case can pay for. Latency
rises because each agent turn waits on a model. Cost rises because planning and
handoff tokens are now part of the hot path. Testability falls because the
output depends on hidden intermediate reasoning, tool choice, and context
packing. Security scope widens because each agent needs data and tools to seem
useful. User trust drops when the system explains, routes, or reflects instead
of completing the known task.

The context that creates this anti-pattern has four common ingredients.

First, the team confuses linguistic ambiguity with workflow ambiguity. A user
may describe a refund request in many ways, but the refund process itself may
still be a fixed policy with known checks. Natural language at the boundary does
not require an autonomous core.

Second, the team treats a multi-agent diagram as evidence of architecture
maturity. Microsoft Research's AutoGen paper presents a framework for composing
multiple conversable agents and describes applications with different
conversation patterns (Qingyun Wu et al., "AutoGen. Enabling Next-Gen LLM
Applications via Multi-Agent Conversation," COLM 2024,
https://www.microsoft.com/en-us/research/publication/autogen-enabling-next-gen-llm-applications-via-multi-agent-conversation-framework/,
verified 2026-08-02). That research makes multi-agent systems easier to build.
It does not make agent count a quality metric.

Third, the team defers product decisions into prompts. Instead of writing which
refunds need approval, which customer data is visible, or which tool is allowed
after authentication, the design asks the model to decide from prose. That can
be correct when cases are genuinely open ended. It is wasteful when the policy
is already known.

Fourth, the team adds autonomy before evals, tracing, and rollback exist.
LangGraph documents agents as systems in a feedback loop that choose tools and
actions, while workflows have predetermined code paths
(LangChain, "Workflows and agents,"
https://langchain-ai.github.io/langgraph/agents/tools/, verified 2026-08-02).
That feedback loop is the power and the cost. Without observability and tests,
it becomes a black-box control plane.

## 3. Forces

Judgement. The weighting below is engineering judgement. It is informed by the
sources cited in this entry, but the balances are analytical rather than quoted
fact.

**Latency.** Over-Agentification sacrifices latency. A direct API call, a rules
engine, or a deterministic workflow has bounded steps. An agent loop adds model
planning, tool selection, possible retries, and sometimes another agent handoff.
Anthropic states that agentic systems often trade latency and cost for better
task performance (Anthropic, "Building effective agents,"
https://www.anthropic.com/engineering/building-effective-agents, verified
2026-08-02). The anti-pattern appears when the task performance gain was never
measured.

**Coupling.** It may look decoupled because agents talk through messages, but
often increases semantic coupling. A billing agent, policy agent, and escalation
agent all depend on prompt conventions, tool names, hidden context summaries,
and informal response contracts. Those contracts are weaker than function
signatures and harder to refactor safely.

**Consistency.** Deterministic workflows favor consistent behavior. Agents favor
adaptation. Over-Agentification sacrifices consistency in flows that users
expect to be repeatable, such as account updates, refunds, report generation,
or compliance checks.

**Operability.** Agent systems can be operable when every tool call, decision,
handoff, guardrail, and stop condition is traced. OpenAI's Agents SDK
documentation lists tracing as a way to visualize and debug agentic flows
(OpenAI, "OpenAI Agents SDK,"
https://openai.github.io/openai-agents-python/, verified 2026-08-02). The
anti-pattern appears when the architecture adds autonomy faster than telemetry.

**Cost.** Every extra planning turn consumes tokens and model capacity. Each
agent boundary tends to add context restatement, role instructions, summaries,
and validation calls. A cheap deterministic branch can become a multi-call
conversation.

**Team topology.** Agent names can mirror teams and departments, but this often
copies the org chart into runtime. A customer request should not cross five
model personas because five teams own parts of the policy. Conway's Law is not
an orchestration strategy.

**Cognitive load.** Over-Agentification adds a new kind of debugging question.
The engineer must ask what the code did, what each prompt asked for, what each
model saw, which tools were exposed, which agent received which summary, and
why the loop stopped. That is a high tax for a fixed task.

**Change cost.** Adding an agent feels cheap because it starts as a prompt.
Owning an agent is expensive because the prompt, tool schema, test set, traces,
failure policy, permissions, and data handling all become product surface.

## 4. Applicability and non-applicability

Reach for an agentic design when these conditions hold.

- **The path cannot be known ahead of time.** A coding task may require reading
  unknown files, editing several locations, running tests, and revising after
  failures. Anthropic names coding as a domain where agents are effective
  because tests can verify progress and the needed file changes vary by task
  (Anthropic, "Building effective agents,"
  https://www.anthropic.com/engineering/building-effective-agents, verified
  2026-08-02).
- **The agent needs tool choice under uncertainty.** A support investigation
  might need order lookup, policy search, account state, shipment status, and
  human handoff, with the next step depending on the previous result.
- **The work benefits from recovery.** If a tool fails or data is missing, the
  system can choose a different route, ask the user for a missing field, or
  stop and escalate.
- **The outcome can be judged.** There is an eval set, a policy checker, a test
  suite, a human review queue, or a business metric that can tell whether the
  agent's extra freedom improved results.
- **The action surface is bounded.** The agent has a small set of documented
  tools, scoped permissions, and clear stop rules.
- **Human review is placed where risk demands it.** OpenAI's guide recommends
  human intervention for high-risk actions and failure thresholds (OpenAI, "A
  practical guide to building agents,"
  https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/,
  verified 2026-08-02).

Explicit non-applicability list. Do not use an agentic design in these cases.

- **The path is fixed.** Use a workflow, pipeline, form handler, transaction
  script, or state machine. A model may still classify the input, but it should
  not decide the process.
- **The task is single-turn transformation.** Summarization, translation,
  sentiment classification, field extraction, and format conversion normally
  need one model call plus validation, not an agent loop.
- **The tool choice is known by code.** If the current page, route, button, or
  event type already determines the API call, letting a model choose the tool
  adds failure without adding value.
- **The policy is deterministic.** Eligibility checks, access rules, rate
  limits, and approval thresholds belong in code or a rules engine unless the
  policy itself requires natural-language interpretation.
- **The workflow has strict latency.** Checkout, login, search autocomplete,
  request signing, and synchronous entitlement checks cannot afford exploratory
  turns.
- **The action is irreversible or high-stakes and lacks approval.** Money
  movement, account deletion, production deploys, legal submissions, and
  medical triage need hard gates before tool execution.
- **The team cannot observe intermediate behavior.** If traces, tool logs,
  prompt versions, and evaluation records are missing, adding autonomy creates
  an incident response gap.
- **The design exists to sound modern.** Renaming a handler, cron job, or
  classifier as an agent does not change its architecture.
- **The team cannot explain why a workflow failed.** Until a non-agent version
  has been measured and found lacking, agent autonomy is premature.

## 5. Structure

Over-Agentification has a recognizable structure even though it is a negative
pattern.

The **User Intent** enters as a natural-language request, event, ticket, or
document. The work often contains a small amount of ambiguity at the boundary
and a large amount of known process behind it.

The **Agent Router** is an LLM prompt or model call that decides which named
agent should handle the request. In many failing designs this router replaces a
simple classifier, a route table, or a UI event.

The **Specialist Agents** each own a prompt, a partial tool set, and a role
description. Their names mirror departments or nouns in the product domain.
They may call one another, ask a manager agent for clarification, or summarize
their result for the next agent.

The **Shared Tool Belt** contains APIs, search indexes, databases, file systems,
ticketing operations, and write actions. The anti-pattern often exposes more
tools than any one request needs because every agent has to seem capable.

The **Conversation Memory** carries summaries, scratchpads, prior tool results,
and hidden assumptions between agents. This memory becomes a second control
plane because later agents act on what earlier agents chose to include.

The **Guardrail Ring** is either missing, placed only at the outer boundary, or
added as yet another agent. OpenAI's guardrails documentation distinguishes
input, output, and tool guardrails, and says tool guardrails run on custom
function-tool invocation boundaries (OpenAI Agents SDK, "Guardrails,"
https://openai.github.io/openai-agents-python/guardrails/, verified
2026-08-02). In the anti-pattern, guardrails are too far from the risky action.

The **Actual Business Operation** is the small deterministic act the user needed
all along. Update the address. Produce the report. Create the ticket. Read the
policy. Send the notification. The structure is wasteful when the operation was
known before the agents started talking.

## 6. ASCII structure diagram

```
OVER-AGENTIFIED SHAPE

  User request
       |
       v
  +------------------+       +------------------+
  | LLM agent router | ----> | billing agent    |
  +------------------+       +------------------+
       |       |                    |
       |       +------------+       v
       |                    |  +------------------+
       v                    +> | policy agent     |
  +------------------+         +------------------+
  | account agent    |                  |
  +------------------+                  v
       |                         +------------------+
       |                         | escalation agent |
       |                         +------------------+
       |                                  |
       +------------------+---------------+
                          |
                          v
                 +-------------------+
                 | shared tool belt  |
                 | APIs, DBs, docs   |
                 +-------------------+
                          |
                          v
                 +-------------------+
                 | business action   |
                 +-------------------+

SIMPLER TARGET WHEN PROCESS IS KNOWN

  User request -> classify -> validate -> call approved API -> report result
```

## 7. Dynamics

The dynamic failure is a loop of delegation and restatement. Each agent has only
part of the state, so it asks another agent, summarizes for another agent, or
returns a partial answer. The user sees delay, hedging, or a request for data
the system already has. The operator sees many traces for one business action.

```
User        Router       Agent A       Agent B       Tool        Human
 |            |             |             |            |            |
 |--request-->|             |             |            |            |
 |            |--choose A-->|             |            |            |
 |            |             |--ask B----->|            |            |
 |            |             |             |--lookup--->|            |
 |            |             |             |<--data-----|            |
 |            |             |<--summary---|            |            |
 |            |             |--tool call-------------->|            |
 |            |             |<--policy error-----------|            |
 |            |--handoff to human---------------------------------->|
 |<--delay and partial answer---------------------------------------|
 |            |             |             |            |            |

Healthy replacement for a known path:

User -> parser -> policy check -> approved tool call -> result or human gate
```

Runtime usually breaks in one of four ways. The first is **handoff drift**,
where each agent summarizes away a detail that the next agent needed. The
second is **tool thrash**, where two tools overlap and the model alternates
between them. The third is **policy evaporation**, where a rule stated in the
outer prompt is not present at the point of tool execution. The fourth is
**runaway reflection**, where an agent critiques, plans, or asks for another
agent instead of acting.

Judgement. The repair is to collapse the path until each runtime choice earns
its place. Keep the model where interpretation is needed. Keep code where the
step is known.

## 8. Implementation variants

**One oversized agent.** A single prompt gets every tool, every policy, and
every task. This avoids handoff drift but creates tool overload, a huge context
surface, and confusing evals. LangChain's agent documentation discusses dynamic
tools, including filtering which tools are exposed by state, permissions, or
conversation stage, because too many tools can overload context and raise error
rates (LangChain, "Agents,"
https://langchain-5e9cc07a.mintlify.app/oss/python/langchain/agents, verified
2026-08-02).

**Manager with specialists.** A manager agent delegates to specialist agents.
This fits cases where subtasks are not known ahead of time. It fails when the
manager is delegating a fixed business process that code could express.
OpenAI's guide describes manager and decentralized multi-agent patterns, and
also recommends maximizing a single agent before creating more agents (OpenAI,
"A practical guide to building agents,"
https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/,
verified 2026-08-02).

**Agent as a thin wrapper over a deterministic workflow.** The agent takes the
user request, then calls one workflow tool. This can be a good compromise when
natural language is the interface but the process is fixed. It becomes theater
when the agent has no meaningful choice and could be replaced by a parser plus
a button.

**Every workflow step as an agent.** Each stage, classifier, validator, writer,
reviewer, sender, becomes a named agent. This is the most common sprawl variant.
It gives each step a prompt but removes the strong contracts that a workflow
engine would give.

**Guardrail as agent.** A separate model reviews inputs, outputs, or tool calls.
This can be valid for semantic safety checks. It is insufficient when the
business rule is deterministic. A database write permission should not depend on
a reviewer prompt alone.

**Human-in-the-loop agent.** The agent drafts and a human approves. This is
often the right variant for risky actions. It becomes Over-Agentification when
the human is approving routine, reversible, low-risk steps only because the
system cannot be trusted.

**Workflow-first design.** The preferred alternative for known paths. Model
calls are components inside a state machine, not the owner of the state machine.
This keeps autonomy narrow while retaining LLM value.

## 9. Known production uses

Because Over-Agentification is an anti-pattern, this section does not claim the
named systems are misdesigned. It names production agent systems that prove the
architecture family is real, then states the boundary each source makes visible.

**Klarna AI assistant.** Klarna announced an OpenAI-powered assistant that was
live globally, handled 2.3 million conversations in its first month, and
handled two-thirds of its customer service chats during that period (Klarna
Bank AB, "Klarna AI assistant handles two-thirds of customer service chats in
its first month," February 27, 2024,
https://www.prnewswire.com/news-releases/klarna-ai-assistant-handles-two-thirds-of-customer-service-chats-in-its-first-month-302072744.html,
verified 2026-08-02). Judgement. This is the kind of domain where an agent can
earn its cost because the conversation, account state, policy interpretation,
and handoff decision vary per customer.

**GitHub Copilot coding agent.** GitHub's documentation says a user can assign
an issue to Copilot, after which Copilot starts work, opens a pull request, and
requests review when finished. The same page labels the feature public preview
and subject to change (GitHub Docs, "Using Copilot cloud agent on GitHub,"
https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github,
verified 2026-08-02). Judgement. Coding is a strong agent fit because the steps
and files are not known in advance, while tests and review can judge output.

**Intercom Fin.** Intercom describes Fin as a customer agent that can
disambiguate queries, take action, follow policies, work across languages and
channels, and resolve an average of 76 percent of customer queries (Intercom
Help, "What is Fin?", https://www.intercom.com/help/en/articles/9515824-what-is-fin,
verified 2026-08-02). Intercom's FAQ says Fin can be configured with escalation
rules for sensitive topics (Intercom Help, "Fin AI Agent FAQs,"
https://www.intercom.com/help/en/articles/7837535-fin-ai-agent-faqs, verified
2026-08-02). Judgement. The notable point for this entry is not that Fin uses an
agent label. It is that the product documentation talks about roles,
configured activation, policies, and escalation, which are exactly the controls
Over-Agentification lacks.

**AutoGen-based multi-agent applications.** Microsoft Research presents AutoGen
as an open-source framework for composing conversable agents with LLMs, tools,
and human inputs, and lists pilot application domains including mathematics,
coding, question answering, supply-chain optimization, online decision making,
and entertainment (Qingyun Wu et al., "AutoGen. Enabling Next-Gen LLM
Applications via Multi-Agent Conversation," COLM 2024,
https://www.microsoft.com/en-us/research/publication/autogen-enabling-next-gen-llm-applications-via-multi-agent-conversation-framework/,
verified 2026-08-02). Judgement. A framework can make a complex design
practical, but it cannot make complexity free.

## 10. Consequences

Judgement. The following consequences are engineering judgement. The cited
sources establish the agent and workflow boundary; the cost and failure
analysis here is the catalog's synthesis.

Positive consequences when the design was warranted:

- The system can handle tasks whose path is not known when the request starts.
- The model can recover from missing information, failed tools, and unexpected
  observations.
- Tool use can be adapted to user context, permissions, and intermediate
  results.
- Human operators can supervise at checkpoints rather than performing every
  step.
- A single natural-language interface can cover a wide set of task variants.
- The architecture can express search, planning, drafting, verification, and
  revision in one runtime loop.

Negative consequences when the design is overused:

- Latency becomes a function of model turns rather than business steps.
- Token cost grows with role prompts, summaries, handoffs, and self-review.
- Behavior becomes harder to reproduce because tool choice and intermediate
  context vary.
- Test suites must cover prompt behavior, tool schemas, routing, permissions,
  and stop conditions, not only code.
- Security review scope grows with every tool exposed to an agent.
- Observability volume grows faster than user value, and traces become hard to
  read.
- Ownership blurs. A bug may live in policy prose, route prompts, tool
  description, memory compaction, model choice, or code.
- Users wait through planning steps for work that could have been completed by
  a known command.

The largest cost is opportunity cost. Every unnecessary agent consumes design,
eval, monitoring, and incident response time that could have made one valuable
agent safer.

## 11. Failure modes and misuse

Judgement. These are practical failure patterns. Each item is written as
Symptom, Cause, Fix so a reviewer can act on observable evidence.

- **Symptom.** A trace for one user action contains many model calls, repeated
  summaries, and several handoffs, while the final side effect is one API call.
  **Cause.** The system delegated a known process to agents. **Fix.** Replace
  the handoff chain with a workflow, keep one model call only for intent or
  field extraction, and call the API from code.

- **Symptom.** The agent sometimes chooses the wrong tool among similar tools,
  such as `refund_order`, `cancel_order`, and `credit_account`. **Cause.** Tool
  choice was left to a model even though application state knows the allowed
  action. **Fix.** Filter tools by state and permission, or expose a single
  typed workflow tool for the current step.

- **Symptom.** A safety rule appears in the top-level prompt but is not applied
  before a write tool executes. **Cause.** Guardrails were placed at the wrong
  boundary. **Fix.** Move validation to tool guardrails or code-level
  authorization checks. OpenAI's guardrails docs distinguish input, output, and
  tool guardrails for this reason (OpenAI Agents SDK, "Guardrails,"
  https://openai.github.io/openai-agents-python/guardrails/, verified
  2026-08-02).

- **Symptom.** The system asks users for information already stored in account
  data. **Cause.** Context is fragmented across agents and summaries omit a
  needed field. **Fix.** Make account state an explicit workflow input, not
  conversational memory passed between agents.

- **Symptom.** Unit tests pass, but production behavior shifts after a prompt
  edit in a different agent. **Cause.** Agents depend on informal response
  contracts between prompts. **Fix.** Replace free-form handoff messages with
  typed outputs, schema validation, and regression evals.

- **Symptom.** The team adds a reviewer agent after every bad answer, and the
  system still ships bad answers. **Cause.** The reviewer has no ground truth,
  executable check, or authority to block the risky action. **Fix.** Add data
  retrieval, deterministic validation, or human approval. Remove reviewer calls
  that only restate preferences.

- **Symptom.** Production incidents cannot be reconstructed. **Cause.** Prompt
  versions, model versions, tool inputs, tool outputs, and handoffs were not
  logged as a single run. **Fix.** Add run IDs, trace spans, prompt hashes, tool
  call records, and final outcome labels.

- **Symptom.** Users abandon the flow because the agent explains its process
  before acting. **Cause.** The agent was optimized for visible reasoning
  rather than completion. **Fix.** Move planning into traces and return only the
  decision, requested artifact, or concise question needed to continue.

- **Symptom.** Cost grows with the number of agent personas rather than request
  volume alone. **Cause.** Agent boundaries are being used as modules. **Fix.**
  Use code modules for deterministic responsibilities and reserve agent
  boundaries for autonomy.

## 12. Trade-off matrix

| Approach | Best fit | Latency | Coupling | Consistency | Operability | Cost | Cognitive load |
|---|---|---:|---|---|---|---:|---|
| Over-Agentification | No good fit. It is the failure case | High | Semantic and hidden | Low | Hard without deep tracing | High | High |
| Transaction Script | Known business operation with clear steps | Low | Direct code coupling | High | Easy | Low | Low |
| Pipes and Filters | Ordered transformations with stable contracts | Medium | Typed stage contracts | High | Easy per stage | Low to medium | Medium |
| Rules Engine | Deterministic policy with many rules | Medium | Rule data coupling | High if governed | Medium | Medium | Medium |
| Workflow Engine | Long-running known process with retries | Medium | Explicit state coupling | High | Strong | Medium | Medium |
| Single Agent with Tools | Unknown path, bounded tools | Medium to high | Tool schema coupling | Medium | Good with traces | Medium to high | Medium |
| Manager and Specialist Agents | Unknown subtasks, broad problem space | High | Prompt and handoff coupling | Medium to low | Hard but possible | High | High |

Judgement. The matrix does not say agents are worse than workflows. It says the
axis that makes agents valuable is unknown path selection. When that axis is
absent, the remaining cells are mostly costs.

## 13. Related and incompatible patterns

**Golden Hammer** is the parent smell. The team has a new tool and starts seeing
every problem as an agent problem. Over-Agentification is Golden Hammer applied
to LLM autonomy.

**Inner Platform Effect** appears when the team builds a mini operating system
of agents, tools, permissions, memory, retries, routing, and scheduling, while
recreating features a workflow engine or queue already had.

**Distributed Monolith** appears when agents are separate deployable or runtime
units but must change together because their prompts and handoff formats are
co-dependent.

**Chatty I/O** appears when agents call many tools or other agents for small
pieces of state. The natural-language layer can hide how many round trips were
added.

**Service Locator** is related when tools are exposed as a flat bag and agents
discover what they need at runtime. Dependency injection or explicit workflow
inputs make dependencies easier to audit.

**Pipes and Filters** is often the replacement. If the work is a fixed sequence
of transformations, filters with typed inputs and outputs beat agents.

**Transaction Script** is the best replacement for simple business actions. A
model can parse the request, but the transaction should own validation and side
effects.

**Rules Engine** replaces agents when policy is known but large. A model may
extract facts from text, then rules decide eligibility.

**Workflow Engine** replaces agents when state, retries, timers, and human tasks
are the hard part.

**Human-in-the-Loop** composes with agents when risk is real. It conflicts with
Over-Agentification when human review is used to compensate for a needless agent
instead of controlling a necessary one.

## 14. Refactoring path in and out

Refactoring into a warranted agent:

1. Write the current process as steps. Mark each step as deterministic,
   semantic interpretation, uncertain search, tool choice, or human judgement.
2. Build the deterministic version first. Use code, queues, workflows, and
   rules for steps whose path is known.
3. Add one model call at the narrowest interpretation point. Give it typed
   output and reject invalid shapes.
4. Measure failures. If failures require unknown step selection, not better
   extraction or better rules, introduce one agent loop.
5. Expose the smallest useful tool set. Tool descriptions should be distinct,
   typed, and permission-aware.
6. Add stop conditions, retry limits, approval gates, and trace IDs before the
   agent reaches production.
7. Add evals that compare the agent against the deterministic baseline on real
   tasks.
8. Split into multiple agents only after a single agent fails because prompt
   complexity, tool overlap, or domain separation is measured as the cause.

Refactoring out of Over-Agentification:

1. Trace a set of production runs and count model calls, handoffs, tool calls,
   retries, and final side effects.
2. Identify branches where the agent always makes the same choice. Replace
   those branches with code.
3. Replace free-form handoff messages with typed records. If the type is stable,
   the handoff probably does not need an agent.
4. Merge agents whose only difference is role text but whose tools and outputs
   overlap.
5. Move deterministic policy from prompts into code or a rules engine.
6. Collapse reviewer agents into validators when the check has a clear rule.
7. Keep one agent at the boundary where path choice remains unknown.
8. Run old and new flows side by side. Compare task success, latency, cost,
   escalation rate, and user satisfaction before removing the old path.

Named refactorings that often apply are Replace Conditional with Polymorphism
when a stable type hierarchy is the real problem, Replace Method with Method
Object when a deterministic flow is too large, Extract Function for tool code,
Introduce Parameter Object for typed handoff state, and Substitute Algorithm
when an agent loop is replaced by a known workflow.

## 15. Testing and verification

Judgement. Testing Over-Agentification starts by proving the agent boundary is
needed. The goal is not to make a bloated agent graph pass tests. The goal is to
delete autonomy where tests show it adds no value.

Use **baseline comparison tests**. Build a deterministic or workflow-first
baseline, then compare the agentic version on the same task set. The agent must
win on task success, coverage of edge cases, or operator time by enough margin
to pay for latency and cost.

Use **golden task suites**. Store realistic user requests, account states,
documents, permissions, and expected outcomes. For each run, assert the final
business result and also assert banned actions, such as no refund without
approval.

Use **tool contract tests**. Every tool exposed to an agent needs schema tests,
permission tests, idempotency tests, and bad-input tests. The agent is an
untrusted caller from the tool's point of view.

Use **handoff schema tests**. If agents exchange JSON, validate it. If agents
exchange prose summaries, treat that as a smell and add tests that prove no
required field is lost.

Use **metamorphic tests**. Rephrase the same user intent in several ways and
assert that the same business action occurs. This catches systems that route by
surface wording rather than intent.

Use **budget tests**. Fail a run if it exceeds a turn count, token budget, tool
count, or wall-clock limit. An agent that succeeds only after unbounded retries
is not production-ready.

Use **fault injection**. Make tools fail, return partial data, return stale
data, or time out. The expected result should be retry, fallback, user question,
or human handoff, not another agent loop with no new information.

Use **human review calibration**. If humans approve agent actions, sample
approved and rejected cases. Measure whether review catches defects and whether
the agent is sending too much routine work to humans.

What becomes easier. Agent tests can express outcomes at a task level rather
than step level, which matches open-ended work. What becomes harder. Reproducing
failures requires prompt versions, model versions, tool outputs, and context
state. Without those artifacts, a failed test may be unrepeatable.

## 16. Observability signals

Judgement. The dashboard should make agent autonomy visible as a resource, not
hide it as implementation detail.

Log a **run ID** across the whole request. Every model call, tool call,
handoff, guardrail result, human approval, and final side effect should attach
to that ID.

Track **model turns per completed task**. Healthy values are stable by task
type. A rising turn count means the agent is searching, confused, or receiving
less useful context.

Track **handoffs per task**. A high average suggests agent sprawl. A high
tail latency suggests a small set of cases is bouncing between agents.

Track **tool calls per task** and **duplicate tool calls**. Duplicate reads show
lost state or poor memory. Duplicate writes require idempotency review.

Track **time to first action**. Users care less about how long the agent thinks
than when it begins useful work. A long planning phase for a known operation is
an Over-Agentification signal.

Track **agent-selected tool distribution**. If one tool handles almost all
requests, the agent may be unnecessary. If similar tools are selected with high
variance for the same intent, the tool surface is unclear.

Track **guardrail trip rate by boundary**. Input, output, and tool guardrails
answer different questions. Tool-boundary trips show attempted risky actions.
Output trips show final response quality. A single aggregate hides the problem.

Track **human escalation rate and reason**. Healthy escalation is concentrated
in high-risk, ambiguous, or out-of-policy cases. Failing escalation includes
routine cases, missing data the system has, and retries that exhaust turn
limits.

Track **cost per successful task**, not only cost per request. A cheap request
that fails and escalates may cost more than an expensive request that completes
correctly.

Track **prompt and tool version drift**. Incidents need to answer which
instructions and schemas were active. Store prompt hashes and tool schema
versions in traces.

A healthy instance has low variance for known task types, bounded turns, low
duplicate tool calls, high task success, and clear escalation reasons. A failing
instance has long traces, repeated summaries, tool thrash, many handoffs, and
cost growth without matching outcome growth.

## 17. Security and privacy implications

Judgement. Over-Agentification is a security multiplier. It may not create a
new class of vulnerability by itself, but it widens every existing LLM
application risk by adding more prompts, tools, data flows, and delegated
decisions.

Prompt injection risk grows with each place untrusted text can enter the
agent's context. OWASP lists prompt injection as a 2025 LLM application risk
(OWASP GenAI Security Project, "2025 Top 10 Risk and Mitigations for LLMs and
Gen AI Apps," https://genai.owasp.org/llm-top-10/, verified 2026-08-02). In an
over-agentified system, the injected text may travel through summaries and
handoffs until the origin is no longer visible.

Tool poisoning and command injection risks grow when agents consume tool
descriptions, plugin outputs, retrieved documents, or third-party context as
instructions. OWASP's MCP Top 10 names weak scope enforcement, tool poisoning,
software supply chain attacks, command injection, and prompt injection via
contextual payloads as MCP risks (OWASP Foundation, "OWASP MCP Top 10,"
https://owasp.org/www-project-mcp-top-10/, verified 2026-08-02). The more tools
an agent graph exposes, the more careful scope design must be.

Authorization must live below the agent. The agent may decide what it wants to
do, but code must decide whether the user and run are allowed to do it. Tool
functions should check identity, permission, resource ownership, rate limits,
and approval state. Prompt instructions are not an access-control mechanism.

Privacy review must follow data flow, not agent names. A specialist agent that
seems harmless may receive a summary containing personal data, payment state,
health data, legal facts, or internal notes. Data minimization is harder when
agents summarize freely. Prefer typed context objects with explicit fields and
redaction rules.

Auditability matters for user rights and incident response. Store enough
metadata to answer which data the agent saw, which tools it called, which
outputs it produced, which human approved an action, and which policy version
was active. Avoid storing raw chain-of-thought unless your policy and provider
contract permit it. Store decisions, tool inputs, tool outputs, and concise
reason codes instead.

High-risk actions require a non-agent gate. OpenAI's agent guide recommends
human intervention for sensitive, irreversible, or high-stakes actions (OpenAI,
"A practical guide to building agents,"
https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/,
verified 2026-08-02). The gate can be human approval, a deterministic rule, a
typed policy engine, or a transaction authorization service. It should not be
another unconstrained agent with a sterner prompt.

## Code examples

The examples below compile or run as standalone demonstrations. Each shows the
same repair. Keep the model-like decision at the boundary, then execute a typed
workflow in code.

### TypeScript

```typescript
type Intent = "refund" | "address_change";

type AgentRequest = {
  intent: Intent;
  orderId: string;
  approvedByHuman: boolean;
};

type Result = { status: "done" | "needs_approval"; message: string };

function parseIntent(text: string): Intent {
  return text.toLowerCase().includes("refund") ? "refund" : "address_change";
}

function runWorkflow(request: AgentRequest): Result {
  if (request.intent === "refund" && !request.approvedByHuman) {
    return { status: "needs_approval", message: "refund requires approval" };
  }
  return { status: "done", message: `${request.intent}:${request.orderId}` };
}

const intent = parseIntent("Please refund order A100");
console.log(runWorkflow({ intent, orderId: "A100", approvedByHuman: false }));
```

### Python

```python
from dataclasses import dataclass
from enum import Enum


class Intent(Enum):
    REFUND = "refund"
    ADDRESS_CHANGE = "address_change"


@dataclass(frozen=True)
class Request:
    intent: Intent
    order_id: str
    approved_by_human: bool


def parse_intent(text: str) -> Intent:
    return Intent.REFUND if "refund" in text.lower() else Intent.ADDRESS_CHANGE


def run_workflow(request: Request) -> str:
    if request.intent is Intent.REFUND and not request.approved_by_human:
        return "needs_approval"
    return f"done:{request.intent.value}:{request.order_id}"


req = Request(parse_intent("refund order A100"), "A100", False)
print(run_workflow(req))
```

### Go

```go
package main

import (
	"fmt"
	"strings"
)

type Intent string

const (
	Refund        Intent = "refund"
	AddressChange Intent = "address_change"
)

type Request struct {
	Intent          Intent
	OrderID         string
	ApprovedByHuman bool
}

func parseIntent(text string) Intent {
	if strings.Contains(strings.ToLower(text), "refund") {
		return Refund
	}
	return AddressChange
}

func runWorkflow(r Request) string {
	if r.Intent == Refund && !r.ApprovedByHuman {
		return "needs_approval"
	}
	return fmt.Sprintf("done:%s:%s", r.Intent, r.OrderID)
}

func main() {
	req := Request{Intent: parseIntent("refund order A100"), OrderID: "A100"}
	fmt.Println(runWorkflow(req))
}
```

### Java

```java
public class OverAgentificationExample {
    enum Intent { REFUND, ADDRESS_CHANGE }

    record Request(Intent intent, String orderId, boolean approvedByHuman) {}

    static Intent parseIntent(String text) {
        return text.toLowerCase().contains("refund")
            ? Intent.REFUND
            : Intent.ADDRESS_CHANGE;
    }

    static String runWorkflow(Request request) {
        if (request.intent() == Intent.REFUND && !request.approvedByHuman()) {
            return "needs_approval";
        }
        return "done:" + request.intent() + ":" + request.orderId();
    }

    public static void main(String[] args) {
        Request request = new Request(parseIntent("refund order A100"), "A100", false);
        System.out.println(runWorkflow(request));
    }
}
```

## 18. References

- Anthropic, Erik S. and Barry Zhang, "Building effective agents," published
  December 19, 2024, sections "What are agents?", "When and when not to use
  agents", "When and how to use frameworks", "Agents", and "Summary",
  https://www.anthropic.com/engineering/building-effective-agents, verified
  2026-08-02.
- OpenAI, "A practical guide to building AI agents," sections "What is an
  agent?", "When should you build an agent?", "Orchestration", and "Guardrails",
  https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/,
  verified 2026-08-02.
- OpenAI, "OpenAI Agents SDK," overview section,
  https://openai.github.io/openai-agents-python/, verified 2026-08-02.
- OpenAI Agents SDK, "Guardrails," sections "Workflow boundaries", "Input
  guardrails", "Output guardrails", and "Tool guardrails",
  https://openai.github.io/openai-agents-python/guardrails/, verified
  2026-08-02.
- LangChain, "Workflows and agents," sections "Workflows" and "Agents",
  https://langchain-ai.github.io/langgraph/agents/tools/, verified 2026-08-02.
- LangChain, "Agents," section "Dynamic tools",
  https://langchain-5e9cc07a.mintlify.app/oss/python/langchain/agents, verified
  2026-08-02.
- Qingyun Wu, Gagan Bansal, Jieyu Zhang, Yiran Wu, Beibin Li, Erkang Zhu, Li
  Jiang, Xiaoyun Zhang, Shaokun Zhang, Ahmed Awadallah, Ryen W. White, Doug
  Burger, Chi Wang, "AutoGen. Enabling Next-Gen LLM Applications via
  Multi-Agent Conversation," COLM 2024,
  https://www.microsoft.com/en-us/research/publication/autogen-enabling-next-gen-llm-applications-via-multi-agent-conversation-framework/,
  verified 2026-08-02.
- Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik
  Narasimhan, Yuan Cao, "ReAct. Synergizing Reasoning and Acting in Language
  Models," Google Research blog summary, November 8, 2022,
  https://research.google/blog/react-synergizing-reasoning-and-acting-in-language-models/,
  verified 2026-08-02.
- Klarna Bank AB, "Klarna AI assistant handles two-thirds of customer service
  chats in its first month," PR Newswire, February 27, 2024,
  https://www.prnewswire.com/news-releases/klarna-ai-assistant-handles-two-thirds-of-customer-service-chats-in-its-first-month-302072744.html,
  verified 2026-08-02.
- GitHub Docs, "Using Copilot cloud agent on GitHub," section "Assigning an
  issue to Copilot",
  https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github,
  verified 2026-08-02.
- Intercom Help, Beth-Ann Sher, "What is Fin?", June 9, 2026,
  https://www.intercom.com/help/en/articles/9515824-what-is-fin, verified
  2026-08-02.
- Intercom Help, Beth-Ann Sher, "Fin AI Agent FAQs," section "Customer
  Experience", https://www.intercom.com/help/en/articles/7837535-fin-ai-agent-faqs,
  verified 2026-08-02.
- OWASP GenAI Security Project, "2025 Top 10 Risk and Mitigations for LLMs and
  Gen AI Apps," https://genai.owasp.org/llm-top-10/, verified 2026-08-02.
- OWASP Foundation, "OWASP MCP Top 10,"
  https://owasp.org/www-project-mcp-top-10/, verified 2026-08-02.
