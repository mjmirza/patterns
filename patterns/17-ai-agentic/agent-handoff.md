---
name: Agent Handoff
slug: agent-handoff
family: 17-ai-agentic
category: Multi-Agent Coordination
aliases: [Handoff, Handoff Orchestration, Control Transfer, Agent Transfer, Warm Handoff, Escalation]
first_described: "OpenAI, Swarm framework, informal 2024 description; formalized as a named `handoff` primitive in the OpenAI Agents SDK"
maturity: established
related: [orchestrator-worker, routing, sub-agent-isolation, chain-of-responsibility, state]
incompatible_with: []
verified: 2026-08-02
---

# Agent Handoff

## 1. Name, aliases, and lineage

Agent Handoff is a coordination pattern for multi-agent large language model
systems in which the agent currently responsible for a conversation or task
transfers that responsibility, together with the working context it needs, to
a different agent or to a human, so that the receiving party becomes the
primary responder from that point forward. The transfer is a discrete,
one-time event rather than a per-turn decision made by a central router. Once
it happens, the new agent owns the exchange until it either finishes the task
or hands it off again.

The framework authors who built this into production tooling call it, almost
without exception, a Handoff. OpenAI's experimental Swarm framework describes
the mechanism plainly, "An `Agent` can hand off to another `Agent` by
returning it in a function"
([openai/swarm README](https://github.com/openai/swarm), verified
2026-08-02). The same README notes that "Swarm is now replaced by the [OpenAI
Agents SDK], which is a production-ready evolution of Swarm," and the Agents
SDK documents handoffs as agents "represented as tools to the LLM," following
the naming convention `transfer_to_<agent_name>`
([OpenAI Agents SDK, Handoffs](https://openai.github.io/openai-agents-python/handoffs/),
verified 2026-08-02). Microsoft's AutoGen independently converged on the same
name for its team-based multi-agent pattern, introducing a `HandoffMessage`
type where, per the documentation, "the speaker agent is selected based on
the most recent `HandoffMessage` message in the context"
([AutoGen AgentChat, Swarm](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html),
verified 2026-08-02). Microsoft Semantic Kernel names the entire topology
"Handoff Orchestration," configured through an `OrchestrationHandoffs`
builder
([Semantic Kernel, Handoff Agent Orchestration](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/handoff),
verified 2026-08-02). LangGraph does not introduce a new type called
"handoff," but its documentation describes returning a `Command` object from
a tool as "particularly useful when implementing multi-agent handoffs,"
reusing its general dynamic-routing primitive for exactly this purpose
([LangGraph, Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api),
verified 2026-08-02).

Aliases in circulation include Handoff Orchestration, the name Semantic
Kernel gives to the pattern as a whole system, Control Transfer or Agent
Transfer, generic descriptions used interchangeably with Handoff in
practitioner writing, and Escalation, the special case where the receiving
party is a human rather than another model. A useful, informal mental model
many practitioners reach for is the call center image of a warm transfer,
where a representative briefs the receiving specialist before disconnecting,
set against a cold transfer that drops the caller with no context at all.
Treat that image as a teaching analogy only. It is not a claim about where
the term originated in the LLM tooling world, since the framework authors
above describe their own independent coinage of "handoff," and this entry
does not assert an earlier documented lineage for the specific phrase.

Two distinctions matter for reading the rest of this entry correctly. First,
handoff is not the same as delegation. When a coordinating agent dispatches a
sub-task to a worker and keeps the conversational seat itself, waiting for
the worker's result before it continues, that is delegation, covered by the
Orchestrator-Worker entry in this family. Handoff is what happens when the
seat itself changes hands. Second, handoff exists at two different
distances. In-process handoff happens inside one running application, where
the source and target agents share memory and a coordinating loop written in
the host language, the Swarm, Agents SDK, AutoGen, Semantic Kernel, and
LangGraph implementations all work this way. Cross-process handoff happens
between separate services, possibly built by different organizations, where
the only thing that crosses the boundary is a serialized message. Google's
Agent2Agent (A2A) protocol formalizes this second distance with a `Task`
object carrying a `contextId` and a `taskId`
([A2A Protocol, Life of a Task](https://a2a-protocol.org/latest/topics/life-of-a-task/),
verified 2026-08-02). Both distances implement the same underlying idea, but
the engineering trade-offs differ enough that dimension 8 treats them as
separate variants.

## 2. Problem and context

A team building an LLM-driven assistant for a domain with more than one kind
of request quickly runs into a shape problem. A single agent with one system
prompt cannot hold every persona, every tool, and every set of instructions
the business needs without the prompt growing past what any one conversation
actually requires. Picture a customer support assistant that has to answer
general questions, look up an order's shipping status, process a return, and
issue a refund. Each of those four jobs wants its own vocabulary, its own
tools, an order lookup function differs from a refund-processing function,
and often its own guardrails, a refund tool needs stricter confirmation logic
than a shipping lookup. Writing all four into one prompt produces a document
that instructs the model to behave like four different specialists depending
on which paragraph applies, and the model has to silently decide, on every
single turn, which paragraph is the one in force. That silent decision is
exactly the failure surface this pattern removes by making it explicit.

Two shortcuts are commonly tried before a team reaches for handoff, and both
carry a real cost worth naming plainly. The first shortcut is the single
mega-agent already described, one prompt, every tool, every instruction,
always loaded. Every additional instruction and tool that agent carries is
present on every turn whether or not the current request needs it, which
raises token cost on every call and gives the model more surface area on
which to pick the wrong tool for an unrelated request. The second shortcut is
a central router or supervisor that looks at every single message and
decides which specialist should answer, then discards that decision and
starts over on the very next message. That approach avoids the mega-agent's
bloated prompt, but it pays a routing decision, and typically an extra model
call, on every turn of the conversation, even during a long back-and-forth
that has obviously settled into one specialist's territory, such as ten
consecutive messages about the same return.

Agent Handoff answers both shortcuts with a narrower move. Let the currently
active agent recognize, as part of its own single turn, that the request in
front of it falls outside what it should own, and transfer control once,
carrying the context the receiving agent needs to continue without asking
the user to repeat themselves. After that single transfer, the new agent
answers directly on every following turn, with no further routing decision
required until it, in turn, decides the conversation has moved outside its
domain. The context that makes this pattern the right answer has three
parts. The business genuinely has more than one distinct area of competence
that a person or a compliance policy would recognize as different jobs. The
conversation tends to settle into one area for a run of turns rather than
alternating unpredictably every message. And a human escalation path needs
to exist as a real, first-class destination, not a special-cased exception
bolted onto the side of the system, because the AutoGen and Semantic Kernel
frameworks verified above both model a human as only another named target on
the same handoff roster.

## 3. Forces

**Coupling versus discoverability.** Every framework examined for this entry
requires the source agent to declare, ahead of time, the finite roster of
agents it may hand control to. The Agents SDK's `handoffs` parameter on an
`Agent`, AutoGen's `AssistantAgent(handoffs=[...])`, and Semantic Kernel's
`OrchestrationHandoffs.add(...)` calls are all closed, code-reviewed lists
rather than a dynamic lookup the model resolves at run time. That closed
roster buys predictability. A reviewer can see, from the wiring alone, every
possible destination a given agent could send a user to. It costs wiring
effort, because adding one new specialist means editing every existing
agent's roster that should reasonably be able to reach it, an effort that
grows with the number of specialists in the system.

**Context fidelity versus cost and exposure.** By default, the frameworks
examined pass the full conversation history across a handoff. The Agents SDK
states that, by default, "the new agent takes over the conversation, and
gets to see the entire previous conversation history," while also exposing
an `input_filter` that receives `HandoffInputData` and can narrow what
crosses
([OpenAI Agents SDK, Handoffs](https://openai.github.io/openai-agents-python/handoffs/),
verified 2026-08-02). AutoGen's documentation makes the same default
explicit, "the receiving agent takes over the task with the same message
context"
([AutoGen AgentChat, Swarm](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html),
verified 2026-08-02). Full history maximizes continuity, since the target
agent never has to ask the user to repeat what they already said, but it
also maximizes cost and the amount of information a specialist agent is
exposed to, including information outside its own domain. Anthropic's own
account of running a multi-agent research system reports that "agents
typically use about 4x more tokens than chat interactions, and multi-agent
systems use about 15x more tokens than chats"
([Anthropic, How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system),
verified 2026-08-02), and every full-history handoff adds directly to that
multiplier. This is the force that decides how badly a team needs the filter
mechanism the frameworks provide but do not turn on by default.

**Turn cost after the transfer settles.** Because the trigger for a handoff
is ordinarily a tool call the source agent's own model emits, the actual
decision cost is one extra reasoning step inside a turn the model was
already taking, not a separate model invocation by a supervisor. After the
handoff lands, the target agent answers directly on the following turns
with no routing hop at all. A repeated-supervisor design pays its routing
cost on every single turn for the life of the conversation, while a
handoff-based design pays it once per transfer and nothing in between. This
favors handoff whenever a conversation is expected to settle into one
specialist's area for several turns, and favors a supervisor when the topic
genuinely swings turn to turn.

**Flexibility versus loop risk.** Allowing an agent to hand a conversation
back to where it came from, the pattern Semantic Kernel's own sample wires
as `.Add(statusAgent, triageAgent, "Transfer to this agent if the issue is
not status related")`
([Semantic Kernel, Handoff Agent Orchestration](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/handoff),
verified 2026-08-02), gives the system a way to correct a wrong route. It
also opens the possibility that two agents disagree about who owns a
request and keep bouncing it back and forth. None of the frameworks examined
for this entry enforce a numeric hop limit by default. Whether and how
tightly to bound that back-and-forth is a design decision every team using
this pattern has to make for itself, discussed further under failure modes.

**Human handoff as an equal citizen, not an exception.** AutoGen models
escalation through a `HumanAgent` that, per the documentation, subscribes to
`agent_topic_type` and is reached when a delegate tool "returns
`human_agent_topic_type`"
([AutoGen, Handoffs design pattern](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html),
verified 2026-08-02), and Semantic Kernel reaches a human through an
`InteractiveCallback`, or `human_response_function` in Python, described as
being "called whenever an agent needs input from the user"
([Semantic Kernel, Handoff Agent Orchestration](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/handoff),
verified 2026-08-02). Treating a human as only another named roster entry,
rather than a special code path with its own control flow, is a real design
force worth naming on its own. It means an escalation path is close to free
once the handoff abstraction exists at all, and it means the same auditing
and roster-review discipline that applies to agent-to-agent transfers
applies to agent-to-human ones too.

## 4. Applicability and non-applicability

Reach for Agent Handoff when the system has more than one genuinely distinct
area of competence that deserves its own persona, its own instructions, and
its own tool loadout, and the conversation is expected to settle into one
area for a run of consecutive turns rather than swinging every message. It
fits when a human escalation path needs to be a real, auditable destination
in the same graph as the automated agents, not a side exception. It also
fits cross-organization interop, where the target agent is a service built
by a different party and the only thing that can cross the boundary is a
task envelope, the shape A2A's `Task` and `contextId` design supports
directly.

Do not reach for it in the following situations, each with a distinct
reason.

- **A single short-lived request answerable in one model call.** The
  tool-call trigger, the roster check, and the context-transfer step all add
  overhead that a plain single agent, or plain function calling with no
  multi-agent machinery at all, does not need to pay.
- **Independent sub-tasks that must run at the same time and be merged by a
  coordinator that stays in charge.** That shape is delegation, described in
  the Orchestrator-Worker entry, where Anthropic's lead agent, in the
  documentation's own words, "spawns subagents to explore different aspects
  simultaneously" and keeps control of the conversation the entire time
  ([Anthropic, How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system),
  verified 2026-08-02). Forcing that work through a handoff serializes what
  should run concurrently, and stalls the transfer of the conversational
  seat to work that was never meant to hold it.
- **Deterministic, rule-based routing on a structured field, such as a
  ticket category already set by a web form.** Putting an if-else decision
  inside an LLM tool call's reasoning is unneeded cost and a source of
  non-determinism where a plain lookup table, the Routing entry in this
  family, is cheaper, faster, and testable with ordinary unit tests instead
  of model evaluations.
- **A regulated setting that requires a centrally auditable policy decision
  on every single message before it reaches the user.** Handoff
  intentionally cedes turn-by-turn control to whichever agent is currently
  active, and a compliance requirement to review every message before it
  goes out is in direct tension with that decentralization. A supervisor or
  router that re-asserts control on every turn fits that requirement more
  directly.
- **A set of "specialist" agents that are really the same system prompt
  under different names.** If every branch of the roster would give the
  same answer to the same question, the handoff machinery adds an entire
  class of new failure modes, misrouting, loops, context leakage, for no
  behavioral gain over a single agent.

## 5. Structure

- **Active agent (source).** The agent currently responsible for the turn.
  It carries its own instructions and tool loadout, plus a declared roster
  of the other agents it is permitted to transfer to.
- **Handoff declaration.** The static, code-reviewed roster telling the
  runtime which targets a given source agent may reach, along with a short
  natural-language description of when each transfer applies, matching the
  "Transfer to this agent if..." phrasing used across the Semantic Kernel
  and AutoGen samples verified above.
- **Handoff trigger.** The signal the source agent emits to request a
  transfer. In every in-process framework examined, this is a tool call the
  model itself generates, following a naming convention such as
  `transfer_to_<agent_name>`, rather than an external decision made by a
  supervisor watching the conversation from outside.
- **Handoff envelope.** The payload that crosses the boundary, full
  conversation history by default in the frameworks examined, or a
  filtered, summarized, or redacted subset produced by an explicit function
  such as the Agents SDK's `input_filter`.
- **Coordinator (runtime).** The host-language loop that intercepts the
  trigger, checks the roster, applies any filter, and re-invokes generation
  with the target as the new active agent. This step is ordinary control
  flow in the framework's own language, not a second LLM call, which is why
  the actual decision cost stays close to a single extra reasoning step
  rather than a whole additional model round trip.
- **Target agent (destination).** The agent that becomes active. It may
  itself declare a roster that includes handing back to the source, forming
  the triage-and-specialist loop shown in the Semantic Kernel sample.
- **Human escalation node.** A named roster entry that is not a model at
  all, but a queue, console, or ticketing webhook awaiting a person's
  reply, modeled by AutoGen as another actor on the same message topic and
  by Semantic Kernel as a callback the orchestration blocks on.
- **Audit log.** The record of every handoff event, source, target, reason,
  and a correlation identifier for the conversation or task. Without it, a
  team cannot later determine why a given specialist ended up speaking,
  because from the transcript alone a legitimate handoff can look identical
  to the assistant contradicting itself.

## 6. ASCII structure diagram

```
                    +---------------------------------------+
                    |             Coordinator                |
                    |  holds active agent pointer, audit log |
                    +---------------------------------------+
                       |                    ^
             active =  |                    | logs each
             "triage"  v                    | transfer
     +---------------------------+          |
     |       TriageAgent          |----------+
     |-----------------------------|
     | instructions, tool loadout  |
     | roster [Billing, Human]     |
     +---------------------------+
        |  transfer_to_billing        transfer_to_human
        v  (tool call)                (tool call)
     +---------------------------+   +---------------------------+
     |       BillingAgent         |   |    Human Escalation Node  |
     |-----------------------------|   |----------------------------|
     | instructions, tool loadout  |   | queue, console, webhook   |
     | roster [Triage]             |   | (no model call at all)    |
     +---------------------------+   +---------------------------+
        |  transfer_to_triage
        v  (hands back, out of scope)
     +---------------------------+
     |       TriageAgent          |
     +---------------------------+

     Envelope crossing each arrow carries a task id, a reason, and
     the filtered history. Only the current active agent talks to
     the user at any point.
```

## 7. Dynamics

```
User        Coordinator        TriageAgent        BillingAgent
 |               |                   |                  |
 |-- message --->|                   |                  |
 |               |-- turn(env) ----->|                  |
 |               |                   | tool call        |
 |               |                   | transfer_to_     |
 |               |                   | billing          |
 |               |<-- HandoffResult -|                  |
 |               |   (handoffTo =    |                  |
 |               |    "billing")     |                  |
 |               |                   |                  |
 |          check roster, is billing in TriageAgent.roster? yes
 |          apply filter for "billing" (redact card data)
 |          hops += 1, hops <= maxHops? yes, log transfer
 |               |                                       |
 |               |-- turn(filtered env) ----------------->|
 |               |                                        | works on
 |               |                                        | the task,
 |               |                                        | replies
 |               |<-- HandoffResult (no handoffTo) -------|
 |<-- reply -----|                                        |
 |               |                                        |
 |-- follow-up ->|                                        |
 |               |-- turn(env) --------------------------->|
 |               |   (active is still "billing",           |
 |               |    no routing hop was needed)            |
 |<-- reply -----|<---------------------------------------|
```

Two properties of this sequence are worth stating plainly, because they are
easy to miss on a first reading. First, the decision to hand off comes from
inside the source agent's own model call, as part of the same turn where it
would otherwise have answered directly; the coordinator never asks a
separate model who should handle this, it only enforces the roster and
applies the filter after the source agent has already decided. Second, once
a target becomes active, ordinary follow-up turns skip the coordinator's
routing branch entirely, going straight to the active agent, which is
exactly the turn-cost saving described under forces. A hop counter travels
alongside the envelope specifically to bound the case where the target
immediately hands back, discussed as a failure mode in dimension 11.

## 8. Implementation variants

**In-process, tool-call handoff.** The shape used by the OpenAI Agents SDK,
AutoGen's Swarm team pattern, and Semantic Kernel's Handoff Orchestration.
The model itself emits a specially named tool call, the host runtime
intercepts that call as control flow rather than executing ordinary tool
logic, and swaps which agent's instructions and tools drive the next
generation step. The notable engineering point here is that function or
tool calling, a mechanism designed for invoking external actions such as a
database lookup or an API request, is repurposed as a first-class
control-flow primitive. That repurposing is unusual outside the LLM-agent
world, where control transfer between components is ordinarily expressed
through method calls, message sends, or state transitions rather than
through the same channel used to ask a model to fetch a weather report.

**In-process, Command-based handoff.** LangGraph's approach, where a tool or
node returns a `Command(goto=<node>, update=<state-delta>)` instead of a
specially recognized tool name the runtime pattern-matches. Handoff is not a
new primitive here, it is an application of the framework's general dynamic
routing mechanism, which the documentation states can also update graph
state in the same call
([LangGraph, Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api),
verified 2026-08-02). Setting `graph` to `Command.PARENT` lets a node inside
a subgraph route to a sibling that lives in the parent graph, extending the
same handoff idea across a subgraph boundary rather than only between peer
agents in one flat graph.

**Cross-process, protocol-level handoff.** Google's A2A protocol, where
there is no shared process or memory at all. The envelope is a serialized
`Task` or `Message` object exchanged over the network, correlated by a
`contextId` that, per the specification, "logically groups multiple `Task`
objects and independent `Message` objects, providing continuity across a
series of interactions," while a `taskId` identifies one unit of work
([A2A Protocol, Life of a Task](https://a2a-protocol.org/latest/topics/life-of-a-task/),
verified 2026-08-02). The `input-required` state acts as a partial handoff
back to the caller, pausing the remote agent until more information arrives
on the same `contextId` and `taskId`. Completed tasks are immutable, a
refinement opens a new task that references the old one through
`referenceTaskIds`, a discipline closer to a workflow or saga's envelope
handling than to the lightweight in-process pattern above.

**Human handoff.** The trigger mechanism is identical to any other target,
a declared roster entry reached through the same tool call, but the
receiving side is a blocking human-input boundary rather than another
model. AutoGen models this literally as another subscriber on the same
message topic
([AutoGen, Handoffs design pattern](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html),
verified 2026-08-02), so the rest of the coordination logic needs no
special case to support it.

**Context strategy, independent of any of the above.** Full-history
pass-through is the default observed in the Agents SDK and AutoGen.
Filtered or redacted pass-through applies an explicit function before the
boundary, the Agents SDK's `input_filter` being the concrete example.
Summarized pass-through compacts the history into a shorter form before it
crosses. Reference-only pass-through stores the large artifact externally
and hands over a pointer instead of the content itself, the technique
Anthropic describes for subagent results returning to a lead agent, where
subagents, in the documentation's phrasing, "store their work in external
systems, then pass lightweight references back to the coordinator" so as
"to prevent information loss during multi-stage processing and reduce
token overhead"
([Anthropic, How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system),
verified 2026-08-02). That technique was described for delegation results,
but it applies equally well to a handoff envelope carrying a large document
or a long transcript.

## 9. Known production uses

- **OpenAI Agents SDK.** The `handoffs` feature is the SDK's primary
  multi-agent delegation primitive, the production successor to the
  experimental Swarm framework, using the `transfer_to_<agent_name>` tool
  naming convention
  ([OpenAI Agents SDK, Handoffs](https://openai.github.io/openai-agents-python/handoffs/);
  [openai/swarm README](https://github.com/openai/swarm), both verified
  2026-08-02).
- **Microsoft AutoGen.** The Swarm team pattern (`HandoffMessage`,
  `Handoff`) is documented for building multi-agent customer-support-style
  teams, and the framework's core layer separately documents a `UserTask`
  and `AgentResponse` handoff-and-escalation design pattern with a
  `HumanAgent`
  ([AutoGen AgentChat, Swarm](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html);
  [AutoGen, Handoffs design pattern](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html),
  both verified 2026-08-02).
- **Microsoft Semantic Kernel.** Handoff Orchestration, configured through
  `OrchestrationHandoffs` and run by a `HandoffOrchestration` object, ships
  a concrete customer-support triage-to-specialist example, order status,
  return, and refund agents, with a working human-in-the-loop callback
  ([Semantic Kernel, Handoff Agent Orchestration](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/handoff),
  verified 2026-08-02).
- **LangGraph.** The `Command`-based multi-agent handoff, documented as the
  recommended way to implement transfer of control between graph nodes
  representing different agents, where a tool call returns
  `Command(goto=..., update=...)`
  ([LangGraph, Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api),
  verified 2026-08-02).
- **Google Agent2Agent (A2A) protocol.** An open, cross-vendor
  specification whose `Task` lifecycle (`contextId`, `taskId`,
  `input-required`) is designed specifically so that one agent's unit of
  work can be handed to and worked on by a remote agent built by a
  different organization
  ([A2A Protocol, Life of a Task](https://a2a-protocol.org/latest/topics/life-of-a-task/),
  verified 2026-08-02).
- **Anthropic's multi-agent research system for Claude.** A `CitationAgent`
  receives the finished research report as its own final-stage
  responsibility, and per the documentation "processes the documents and
  research report to identify specific locations for citations" so that
  "all claims are properly attributed to their sources"
  ([Anthropic, How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system),
  verified 2026-08-02). This example is cited here mainly for the boundary
  it draws. The lead agent's relationship to its subagents earlier in the
  same pipeline is delegation, since the lead keeps control and only
  receives compressed results back, while the final step to the
  CitationAgent, where a distinct piece of work becomes fully owned by a
  different named process, reads as a genuine handoff of ownership over the
  citation step.

## 10. Consequences

Positive consequences. Each agent's instructions and tool list stay narrow
and specific to one job, which matters directly against the token-cost
force from dimension 3, since Anthropic's own account puts multi-agent
systems at roughly 15 times the token cost of a single chat turn and every
unnecessary tool or instruction in an agent's prompt adds to that baseline
on every call it makes. After a transfer lands, following turns skip the
routing decision altogether, unlike a design where a supervisor re-decides
on every message. The Semantic Kernel sample output demonstrates a readable
per-agent audit trail out of the box, prefixing every line with the agent
that produced it, which is directly useful for later review and for
debugging why a particular reply was given. Escalation to a human becomes
an ordinary declared edge in the same roster rather than a separate
exception path bolted onto the side of the system, since both AutoGen and
Semantic Kernel model it through the same abstraction used for
agent-to-agent transfers.

Negative consequences. The receiving agent inherits whatever context
strategy the source chose, and when the framework default of full history
is used without an explicit filter, the target agent sees, and may act on,
information outside its own area of responsibility, an information-flow
problem the pattern does not solve on its own, it only provides the hook,
`input_filter` and similar mechanisms, that a team has to choose to use. A
statically declared roster, the shape every framework examined here settled
on, means adding a new specialist agent requires editing every existing
agent's roster that should reasonably reach it, an amount of wiring that
grows as the number of specialists grows, a cost the GoF Chain of
Responsibility and Mediator patterns were built to avoid by centralizing or
chaining discovery instead, discussed further in dimension 13. Because the
transfer trigger is the source model's own reasoning, a poorly instructed
source agent can hand off too eagerly, deflecting a question it could
actually have answered, or too reluctantly, holding onto a request it
should not own, and neither failure is visible to the surrounding
application unless every handoff decision is logged, per dimension 16.

## 11. Failure modes and misuse

**Ping-pong handoff loop.** The symptom is that the conversation, or the
automated process behind it, bounces between two agents with no progress,
either producing repeated near-identical prompts to the user or exhausting
a step or time budget. The cause is that both agents' routing descriptions
overlap or are ambiguous, so each one genuinely believes the request is not
its own to keep, and none of the frameworks examined here enforce a maximum
hop count by default. The fix is to track a hop counter per conversation or
task and stop, or escalate to a human or a default agent, once a small
fixed limit is reached, and to sharpen each handoff's natural-language
description so the domains it covers do not overlap, following the
mutually exclusive "if the issue is not X related" phrasing shown in the
verified Semantic Kernel sample.

**Context leakage across a trust boundary.** The symptom is that a
specialist agent references information the user never told it, or a
lower-trust or externally facing agent ends up quoting a transcript that
belongs to a different, higher-sensitivity domain. The cause is that the
default full-history handoff was used without applying a filter before
crossing into a lower-trust or third-party target. The fix is to treat
every handoff's context payload as a trust-boundary crossing that requires
an explicit allow-list filter, the Agents SDK's `input_filter` or an
equivalent custom mapper, rather than relying on a framework's
full-history default, particularly before any transfer to a human-facing
or externally owned target.

**Stale or duplicate handoff re-execution.** The symptom is that the same
task is processed twice, producing two refunds, two open tickets, or two
contradictory replies sent to the same user. The cause is that a retried
handoff after a timeout or crash carried no stable identifier the target
could use to recognize it had already handled the exact same request. The
fix is to carry a stable correlation identifier through the handoff, the
A2A protocol's paired `taskId` and `contextId` being a directly citable
example of this discipline
([A2A Protocol, Life of a Task](https://a2a-protocol.org/latest/topics/life-of-a-task/),
verified 2026-08-02), and to have the target check and record that
identifier before performing any side effect, matching ordinary
at-least-once delivery handling from messaging systems.

**Handoff used where delegation was needed.** The symptom is that work that
could run concurrently instead runs one specialist at a time, each fully
taking over the conversation before handing back, so total latency
approaches the sum of every specialist's time rather than the slowest
single one. The cause is that a team modeled genuinely independent
sub-tasks, such as checking a billing status and a shipment status at the
same time, as sequential handoffs because handoff was the only multi-agent
primitive the team already knew. The fix is to reclassify the work. If a
coordinator needs the combined results of several specialists to answer one
question, and the specialists never need to speak to the user directly,
that is delegation, not a transfer of the conversational seat, and belongs
in the Orchestrator-Worker entry instead.

**Silent persona drift.** The symptom is that the user notices an
unexplained change in tone, claimed knowledge, or capability
mid-conversation, and reads it as the assistant contradicting or losing
track of itself, without ever being told that a transfer happened. The
cause is that the application surfaces every agent's reply under one
generic identity, with no indication that control changed hands, so a
legitimate handoff and an actual model failure are indistinguishable from
the outside. The fix is to surface the event to the user, a short message
such as "connecting you with billing" matching the warm-transfer image
from dimension 1, and to expose the acting agent's name in the transcript,
exactly as the verified Semantic Kernel sample output already does by
prefixing every line with the responding agent's name.

## 12. Trade-off matrix

| Force | Agent Handoff | Supervisor / Routing | Orchestrator-Worker (delegation) | Chain of Responsibility (GoF) |
|---|---|---|---|---|
| Who decides the next agent | The currently active agent, per transfer | A central router, every turn | The lead agent, per sub-task dispatch | The next handler in a fixed chain |
| Does control return to the original caller | Only if explicitly handed back | Yes, the router is always the caller's proxy | Yes, the lead keeps the seat | No, the accepting handler owns the request |
| Cost after the first decision settles | Near zero for following turns | Paid again on every turn | One dispatch plus one collected result per sub-task | One pass through remaining handlers, in-process |
| Context that crosses | Full history by default, filterable | Not applicable, the router usually sees everything already | Compressed or referenced results, per Anthropic's account | Whatever the request object itself carries |
| Human escalation | A first-class roster target | Possible, but the router still decides return routing | Awkward, the lead would have to model a human as a worker | Not a native concept, handlers are code objects |
| Best fit | Distinct domains, settled runs of turns, visible transfer | Turn-by-turn topic swings, centralized policy needs | Independent, parallelizable sub-tasks with one final answer | In-process, silent, single-request routing between objects |

## 13. Related and incompatible patterns

**Orchestrator-Worker (delegation).** The closest cousin in this family and
the pattern most often confused with handoff. A useful test to tell them
apart is this. Does the caller get the conversational seat back
automatically once a bounded amount of work finishes, or does control stay
wherever it was sent until that party decides to move it again? Anthropic's
lead agent keeps control the entire time its subagents work, which is
delegation, the Swarm, AutoGen, and Semantic Kernel examples verified above
keep control at whichever agent last received it, which is handoff. The two
compose cleanly. A triage agent can hand off to an orchestrator agent that
then delegates internally to several parallel workers before it replies,
using handoff for the outer transfer of the conversational seat and
delegation for the inner fan-out.

**Routing (supervisor pattern).** A router that re-decides every turn is a
repeated, centralized version of the single decision a handoff makes once.
In fact, AutoGen's Swarm speaker-selection rule, choosing the next speaker
based on the most recent `HandoffMessage`, is itself built directly on top
of the handoff primitive to implement a lightweight form of routing, which
shows the two patterns are not mutually exclusive. Routing can be
implemented as a sequence of handoffs rather than as a separate mechanism.

**Sub-Agent Isolation.** A complementary, not competing, pattern. Isolation
is about giving a spawned worker its own context window so it does not
pollute the parent's, the reason Anthropic states directly for isolating
subagents. Handoff is about which agent the user is currently talking to.
A system built with real care commonly uses isolation for delegated
background workers and handoff for the primary conversational seat, at the
same time, without either one replacing the other.

**Chain of Responsibility (GoF, `01-design-patterns-gof/chain-of-responsibility.md`).** The
classical structural ancestor in spirit. A request travels along a
sequence of handlers until one accepts it. The difference is who is aware
of the transfer. Chain of Responsibility's handlers are ordinarily silent,
in-process objects, unaware of each other as distinct personas, and the
original caller never learns which handler ultimately responded. Agent
Handoff, by contrast, is meant to be externally visible, a differently
named agent, often disclosed to the user, takes over, and it usually keeps
ownership for many following turns rather than processing one request and
returning control up a chain immediately after.

**State (GoF, `01-design-patterns-gof/state.md`).** Also structurally close. An object's
behavior changes because it delegates to a different internal state
object. State's transitions are private implementation detail belonging to
one object with one identity from any caller's point of view. Agent
Handoff's transitions are typically meant to be observed, a different
named agent, possibly with an entirely different underlying model or tool
set, becomes primary, and that change often persists for a whole
sub-conversation rather than for the lifetime of a single method call.

**Tension with centralized-policy requirements.** A strict rule that every
outgoing message needs a central compliance check is in direct tension with
handoff's decentralization, since a reviewer cannot audit who is allowed to
say what at the point of decision if any agent on the roster can
unilaterally accept a transfer of control. Combining the two means
wrapping every target's acceptance in an additional policy check, at which
point the system has, in effect, rebuilt a router that sits in front of the
handoff mechanism, which is a reasonable design but should be recognized as
a deliberate hybrid rather than plain handoff.

## 14. Refactoring path in and out

Refactoring in, from a single overloaded agent to a handoff-based system.

1. Start from an agent whose instructions have grown to cover multiple
   unrelated domains, recognized by a prompt that reads as a series of "if
   the user asks about X, do Y" sections that never interact with each
   other.
2. Split those sections into separate agent definitions, one per domain,
   each carrying only the tools and instructions that domain needs.
3. Keep one agent, usually the original generalist voice, as the default
   entry point the user always talks to first.
4. Add a declared handoff roster to that entry-point agent naming the new
   specialists, each with a short natural-language description of when the
   transfer applies, and add a return edge from each specialist back to the
   entry point for requests that turn out to fall outside its domain.
5. Decide the context strategy on purpose, full history or filtered, rather
   than accepting whatever the chosen framework defaults to silently, this
   is the step most refactors skip and later regret, per the
   context-leakage failure mode in dimension 11.
6. Add the per-handoff log line described in dimension 16 before shipping,
   so the first production loop or misroute is diagnosable from logs rather
   than from a user complaint.

Refactoring out, folding a specialist back into the agent that owns it.

1. Watch for a specialist that is handed off to on effectively every
   conversation, with no other path ever reaching it, that is not real
   selectivity, it is a fixed pipeline stage wearing a handoff's clothing.
2. Fold that specialist's instructions and tools back into whichever agent
   always hands off to it, removing the extra tool-call turn and, in the
   in-process variants, the extra model round trip that specialist added
   for no actual routing benefit.
3. If a rarely used specialist is expensive to keep alive as a standing
   model call, consider a deterministic Routing lookup step for the cases
   that turn out to be simple pattern matches, reserving a model-driven
   handoff only for genuinely ambiguous requests that remain after the
   lookup fails.

## 15. Testing and verification

Test the routing decision and the specialist's own behavior as two
separate concerns, since they are two separate failure surfaces.
Hard-code the routing decision in the test setup, calling a target
agent function directly with a synthetic envelope, to unit-test what that
specialist does independent of whether the source model reliably reaches
for the correct tool call. Then, separately, hold a labeled set of user
messages, each tagged with the expected handoff target or with no handoff
at all, replay them against the source agent alone with the target agents
replaced by recording fakes, and assert on the emitted tool call's name and
arguments. This directly exercises the reasoning step behind the ping-pong
and misrouting failures from dimension 11, without requiring the target
agent's own logic to be correct at the same time.

Build a loop or hop-limit test by constructing an adversarial pair of
agents deliberately configured to hand back to each other on every turn,
and assert that the coordinator enforces its hop limit and reaches a
terminal or escalation state instead of looping without end, an
adversarial test in the same spirit as testing a Chain of Responsibility's
fallback handler. Build a context-filter test by placing a marker piece of
information into a conversation that should never cross a particular
handoff boundary, then assert the target agent's received envelope does
not contain it, a straightforward test that is easy to skip precisely
because the leakage failure mode is silent by default. For the A2A-style
cross-process variant, add an idempotency test that replays the same
`taskId` twice and asserts the target performs any side effect, a refund,
a ticket creation, exactly once.

A recording fake target agent, one that stores whatever envelope it
received and returns a canned reply, is the natural test double for both
the routing-decision and context-filter tests above, because it lets
assertions run against the envelope's contents without needing a real
model call on the target side at all.

## 16. Observability signals

Log every handoff as a discrete event, source agent, target agent, a
timestamp, the reason the source gave for the transfer, and a stable
conversation or task correlation identifier. This single log line is the
artifact needed to determine, after the fact, why a particular specialist
ended up speaking, the exact gap named in the silent-persona-drift failure
mode. Track a hop count per conversation or task and alert as it
approaches the enforced limit, giving a leading indicator of the ping-pong
failure before it actually exhausts the budget. Track a simple counter of
how often each target is reached, which surfaces both over-triggering
specialists, candidates for the fold-back refactor in dimension 14, and
under-triggering ones, candidates for removal or for a clearer routing
description that should be sending them traffic in the first place.

Measure the size of the envelope crossing each boundary, tokens before and
after any filter is applied, which is directly actionable against the cost
force from dimension 3 and against Anthropic's cited multiplier for
multi-agent token spend generally. Measure time to resolution from the
first agent that touched a conversation to its terminal state, broken down
by how many handoffs occurred along the way, to separate a conversation
that was slow because the underlying problem was hard from one that was
slow because routing kept bouncing. Where the A2A protocol's transport is
used directly, the `Task` state transition history for a given `taskId`,
moving through states such as submitted, working, and input-required
before reaching a terminal state, is itself a ready-made, timestamped
observability trail with no additional logging required
([A2A Protocol, Life of a Task](https://a2a-protocol.org/latest/topics/life-of-a-task/),
verified 2026-08-02).

## 17. Security and privacy implications

Every handoff is a point where data scoped to one agent's context becomes
visible to a different one. When the target is a service built by a
different organization, the cross-process A2A case, this is a literal
network transmission of what may be sensitive conversation content, and,
per dimensions 3 and 11, the frameworks examined for this entry default to
sending the full history unless a filter is explicitly applied. A security
reviewer's expectation of a safe-by-default posture is generally not what
ships out of the box, and has to be added deliberately.

Roster integrity matters as much as filtering. If user input is ever
allowed to influence which target string a handoff resolves to, rather
than the roster being a closed, code-reviewed set baked into the
application, a crafted message could try to steer the source agent's tool
call toward an unintended or attacker-controlled destination. Keeping the
roster closed and never deriving it from untrusted input at run time
follows the same defense-in-depth posture already expected of any serious
deployment, this point is engineering judgement rather than a claim any of
the framework documents make directly, since none of the sources verified
above discuss adversarial roster manipulation explicitly.

Handing a conversation back to a higher-privilege agent deserves
particular care. If a lower-privilege specialist, such as an
unauthenticated general information bot, can hand a request back to an
agent that holds account-modifying tools without the receiving agent
re-checking the user's authentication or authorization state, the handoff
mechanism can become a route for smuggling an unverified user into a
privileged tool loadout. Each accepting agent should treat the true
identity of the party on the other end of a handoff as state that must be
verified again at the boundary, not as trust inherited automatically from
the fact that a transfer happened.

Handing a conversation to a human deserves the same discipline, arguably
more of it. Whatever context reaches a human's screen through AutoGen's
`HumanAgent` or Semantic Kernel's interactive callback is now subject to
the access controls of whatever system displays it, a ticketing tool or a
console, which are frequently weaker or scoped differently than the LLM
application's own controls, and a human reviewer can screenshot, forward,
or paste content elsewhere in ways an automated agent cannot. The same
filter discipline used for agent-to-agent transfers should apply, and
often more strictly, to agent-to-human ones. Finally, the same
per-handoff log line from dimension 16 doubles as a security and
compliance artifact, since it is what lets a reviewer reconstruct which
agent, acting under which instructions, actually produced a given
user-facing statement when something goes wrong and someone needs to
determine which specialist's prompt or tool was responsible.

## Code examples

The following three implementations model the same coordinator, a source
agent that emits a handoff decision, a roster check, an optional context
filter, a hop-limit guard against the ping-pong failure mode, and an audit
trail. Java and Kotlin are omitted. The pattern's control flow rests
entirely on a tool call or return value being interpreted by a
host-language loop, and that shape translates directly into any language
with closures or first-class functions, so nothing about it is
idiomatically bound to a JVM language for this entry.

```typescript
type Role = "user" | "assistant";

interface Turn {
  role: Role;
  agent: string;
  content: string;
}

interface HandoffEnvelope {
  taskId: string;
  reason: string;
  history: Turn[];
}

interface HandoffResult {
  reply: string;
  handoffTo?: string;
}

type ContextFilter = (history: Turn[]) => Turn[];

interface AgentDefinition {
  name: string;
  roster: string[];
  respond: (envelope: HandoffEnvelope) => HandoffResult;
}

class HandoffLoopError extends Error {}

class Coordinator {
  private agents = new Map<string, AgentDefinition>();
  private filters = new Map<string, ContextFilter>();
  private readonly maxHops: number;
  private log: string[] = [];

  constructor(maxHops = 4) {
    this.maxHops = maxHops;
  }

  register(agent: AgentDefinition, filter?: ContextFilter): void {
    this.agents.set(agent.name, agent);
    if (filter) this.filters.set(agent.name, filter);
  }

  run(taskId: string, startAgent: string, userMessage: string): string {
    const history: Turn[] = [{ role: "user", agent: "user", content: userMessage }];
    let active = startAgent;
    let hops = 0;

    while (true) {
      const agent = this.agents.get(active);
      if (!agent) {
        throw new Error(`unknown agent: ${active}`);
      }
      const filter = this.filters.get(active);
      const filtered = filter ? filter(history) : history;
      const envelope: HandoffEnvelope = { taskId, reason: userMessage, history: filtered };
      const result = agent.respond(envelope);
      history.push({ role: "assistant", agent: active, content: result.reply });

      if (!result.handoffTo) {
        return result.reply;
      }
      if (!agent.roster.includes(result.handoffTo)) {
        throw new Error(`${active} may not hand off to ${result.handoffTo}`);
      }
      hops += 1;
      this.log.push(`${taskId}: ${active} -> ${result.handoffTo}`);
      if (hops > this.maxHops) {
        throw new HandoffLoopError(`hop limit exceeded for task ${taskId}`);
      }
      active = result.handoffTo;
    }
  }

  auditTrail(): readonly string[] {
    return this.log;
  }
}

// Redacts any turn that mentions a raw card token before it crosses into
// the billing agent's context, the fix for the leakage failure mode.
const redactBilling: ContextFilter = (history) =>
  history.filter((turn) => !turn.content.includes("card-"));

const triage: AgentDefinition = {
  name: "triage",
  roster: ["billing"],
  respond: (env) => {
    if (env.reason.toLowerCase().includes("refund")) {
      return { reply: "Routing you to billing.", handoffTo: "billing" };
    }
    return { reply: "I can help with general questions." };
  },
};

const billing: AgentDefinition = {
  name: "billing",
  roster: ["triage"],
  respond: (env) => ({ reply: `Billing sees ${env.history.length} prior turns.` }),
};

const coordinator = new Coordinator(4);
coordinator.register(triage);
coordinator.register(billing, redactBilling);

const finalReply = coordinator.run("t-1", "triage", "I need a refund, card-4242 was charged twice");
console.log(finalReply);
console.log(coordinator.auditTrail());
```

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class TaskState(Enum):
    """Mirrors the state names used by the A2A protocol's Task lifecycle."""

    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"


@dataclass
class Envelope:
    task_id: str
    context_id: str
    reason: str
    history: list[str] = field(default_factory=list)


@dataclass
class HandoffResult:
    reply: str
    state: TaskState
    handoff_to: Optional[str] = None


AgentFn = Callable[[Envelope], HandoffResult]


class LoopLimitExceeded(RuntimeError):
    pass


class DuplicateTask(RuntimeError):
    pass


class HandoffCoordinator:
    def __init__(self, max_hops: int = 4) -> None:
        self._agents: dict[str, AgentFn] = {}
        self._roster: dict[str, set[str]] = {}
        self._seen_tasks: set[str] = set()
        self._audit: list[str] = []
        self._max_hops = max_hops

    def register(self, name: str, fn: AgentFn, roster: set[str]) -> None:
        self._agents[name] = fn
        self._roster[name] = roster

    def run(self, task_id: str, context_id: str, start_agent: str, reason: str) -> HandoffResult:
        # A stale retry of an already-completed task must never re-run a
        # side effect, so the idempotency check happens before anything else.
        if task_id in self._seen_tasks:
            raise DuplicateTask(f"task {task_id} already processed")
        self._seen_tasks.add(task_id)

        active = start_agent
        history: list[str] = [reason]
        hops = 0
        while True:
            fn = self._agents[active]
            envelope = Envelope(task_id, context_id, reason, list(history))
            result = fn(envelope)
            history.append(f"{active}: {result.reply}")

            if result.handoff_to is None:
                return result
            if result.handoff_to not in self._roster[active]:
                raise ValueError(f"{active} cannot hand off to {result.handoff_to}")

            hops += 1
            self._audit.append(f"{task_id}: {active} -> {result.handoff_to}")
            if hops > self._max_hops:
                raise LoopLimitExceeded(f"task {task_id} exceeded {self._max_hops} hops")
            active = result.handoff_to

    @property
    def audit_trail(self) -> list[str]:
        return list(self._audit)


def triage(envelope: Envelope) -> HandoffResult:
    if "refund" in envelope.reason.lower():
        return HandoffResult("Routing to billing.", TaskState.WORKING, "billing")
    return HandoffResult("Handled by triage.", TaskState.COMPLETED)


def billing(envelope: Envelope) -> HandoffResult:
    if "card" not in envelope.reason.lower():
        return HandoffResult("Need the card reference.", TaskState.INPUT_REQUIRED, "human")
    return HandoffResult("Refund issued.", TaskState.COMPLETED)


def human(envelope: Envelope) -> HandoffResult:
    return HandoffResult("Escalated to a support agent.", TaskState.INPUT_REQUIRED)


if __name__ == "__main__":
    coordinator = HandoffCoordinator(max_hops=3)
    coordinator.register("triage", triage, roster={"billing"})
    coordinator.register("billing", billing, roster={"human"})
    coordinator.register("human", human, roster=set())

    outcome = coordinator.run("task-1", "ctx-1", "triage", "I would like a refund")
    print(outcome)
    print(coordinator.audit_trail)

    try:
        coordinator.run("task-1", "ctx-1", "triage", "duplicate attempt")
    except DuplicateTask as exc:
        print(f"guarded: {exc}")
```

```go
package main

import (
	"errors"
	"fmt"
	"sync"
)

// Envelope crosses an agent boundary. It is copied, not shared, so a
// concurrent handoff on another goroutine cannot mutate history in place.
type Envelope struct {
	TaskID  string
	Reason  string
	History []string
}

type Result struct {
	Reply     string
	HandoffTo string
}

type AgentFunc func(Envelope) Result

var ErrHopLimit = errors.New("handoff hop limit exceeded")
var ErrUnknownTarget = errors.New("handoff target not on roster")

type Coordinator struct {
	mu      sync.Mutex
	agents  map[string]AgentFunc
	roster  map[string]map[string]bool
	audit   []string
	maxHops int
}

func NewCoordinator(maxHops int) *Coordinator {
	return &Coordinator{
		agents:  make(map[string]AgentFunc),
		roster:  make(map[string]map[string]bool),
		maxHops: maxHops,
	}
}

func (c *Coordinator) Register(name string, fn AgentFunc, roster ...string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.agents[name] = fn
	allowed := make(map[string]bool, len(roster))
	for _, r := range roster {
		allowed[r] = true
	}
	c.roster[name] = allowed
}

func (c *Coordinator) Run(taskID, start, reason string) (Result, error) {
	active := start
	history := []string{reason}
	hops := 0

	for {
		c.mu.Lock()
		fn, ok := c.agents[active]
		allowed := c.roster[active]
		c.mu.Unlock()
		if !ok {
			return Result{}, fmt.Errorf("unknown agent %q", active)
		}

		result := fn(Envelope{TaskID: taskID, Reason: reason, History: append([]string{}, history...)})
		history = append(history, fmt.Sprintf("%s: %s", active, result.Reply))

		if result.HandoffTo == "" {
			return result, nil
		}
		if !allowed[result.HandoffTo] {
			return Result{}, ErrUnknownTarget
		}

		hops++
		c.mu.Lock()
		c.audit = append(c.audit, fmt.Sprintf("%s: %s -> %s", taskID, active, result.HandoffTo))
		c.mu.Unlock()
		if hops > c.maxHops {
			return Result{}, ErrHopLimit
		}
		active = result.HandoffTo
	}
}

func (c *Coordinator) AuditTrail() []string {
	c.mu.Lock()
	defer c.mu.Unlock()
	out := make([]string, len(c.audit))
	copy(out, c.audit)
	return out
}

func triage(env Envelope) Result {
	if len(env.Reason) > 0 && env.Reason[0] == 'R' {
		return Result{Reply: "Routing to billing.", HandoffTo: "billing"}
	}
	return Result{Reply: "Handled by triage."}
}

func billing(env Envelope) Result {
	return Result{Reply: fmt.Sprintf("Billing saw %d prior turns.", len(env.History))}
}

func main() {
	c := NewCoordinator(3)
	c.Register("triage", triage, "billing")
	c.Register("billing", billing)

	result, err := c.Run("task-1", "triage", "Refund please")
	if err != nil {
		fmt.Println("error:", err)
		return
	}
	fmt.Println(result.Reply)
	fmt.Println(c.AuditTrail())
}
```

## 18. References

- OpenAI. "Handoffs." OpenAI Agents SDK documentation.
  [https://openai.github.io/openai-agents-python/handoffs/](https://openai.github.io/openai-agents-python/handoffs/).
  Verified 2026-08-02.
- OpenAI. "swarm" repository README.
  [https://github.com/openai/swarm](https://github.com/openai/swarm).
  Verified 2026-08-02.
- Microsoft. "Handoffs." AutoGen core user guide, design patterns.
  [https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html).
  Verified 2026-08-02.
- Microsoft. "Swarm." AutoGen AgentChat user guide.
  [https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html).
  Verified 2026-08-02.
- Microsoft. "Handoff Agent Orchestration." Semantic Kernel documentation.
  [https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/handoff](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/handoff).
  Verified 2026-08-02.
- LangChain. "Graph API." LangGraph documentation.
  [https://docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api).
  Verified 2026-08-02.
- Google. "Life of a Task." Agent2Agent (A2A) protocol documentation.
  [https://a2a-protocol.org/latest/topics/life-of-a-task/](https://a2a-protocol.org/latest/topics/life-of-a-task/).
  Verified 2026-08-02.
- Anthropic. "How we built our multi-agent research system." Anthropic
  Engineering blog.
  [https://www.anthropic.com/engineering/multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system).
  Verified 2026-08-02.
