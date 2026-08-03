---
name: Multi-Agent Supervisor
slug: multi-agent-supervisor
family: 17-ai-agentic
category: Agentic
aliases: [Orchestrator-Worker, Agent Supervisor, Lead Agent Pattern, Manager-Worker Agents, Classifier-Router Agents]
first_described: "LangChain/LangGraph docs and Wu et al. AutoGen, 2023-2024"
maturity: established
related: [chain-of-responsibility, mediator, command, strategy, react-agent-loop, tool-use-function-calling]
incompatible_with: [peer-to-peer-agent-handoff]
verified: 2026-08-02
---

# Multi-Agent Supervisor

## 1. Name, aliases, and lineage

The canonical name in use across the two most cited frameworks is Supervisor,
short for agent supervisor, and Orchestrator-Worker, used by Anthropic's own
engineering writeup of its research system. LangChain's LangGraph documentation
names the pattern directly. It states plainly that "an agent supervisor is
responsible for routing to individual agents," and adds the framing that
carries the most weight for implementers, "the supervisor can also be thought
of an agent whose tools are other agents" (LangChain, LangGraph multi-agent
workflows blog, https://www.langchain.com/blog/langgraph-multi-agent-workflows,
verified 2026-08-02). Anthropic's engineering blog on its Claude multi-agent
research system uses Lead Agent and Orchestrator-Worker for the same shape, a
lead agent that "analyzes queries, develops a strategy, and spawns subagents to
explore different aspects simultaneously" (Anthropic, "How we built our
multi-agent research system," https://www.anthropic.com/engineering/multi-agent-research-system,
verified 2026-08-02).

The pattern does not have a single point of origin the way a Gang of Four
pattern does. It crystallized across three lineages roughly concurrently
between 2023 and 2024. Microsoft's AutoGen paper, Qingyun Wu, Gagan Bansal,
Jieyu Zhang, Yiran Wu, Beibin Li, Erkang Zhu, Li Jiang, Xiaoyun Zhang, Shaokun
Zhang, Jiale Liu, Ahmed Hassan Awadallah, Ryen W. White, Doug Burger, and Chi
Wang, "AutoGen. Enabling Next-Gen LLM Applications via Multi-Agent
Conversation," arXiv 2308.08155, 2023, introduced conversable agents that talk
to each other, and its GroupChat abstraction added a manager agent,
GroupChatManager, whose job is to pick the next speaker rather than to speak
itself (Microsoft, AutoGen stable docs,
https://microsoft.github.io/autogen/stable/reference/python/autogen_agentchat.teams.html,
verified 2026-08-02). LangChain's LangGraph took the same shape and built it as
a first-class graph topology, with a supervisor node whose only output is a
routing decision. AWS shipped a third implementation under the name Multi-Agent
Orchestrator, later renamed Agent Squad, structured as a Classifier plus an
Orchestrator. The classifier "analyzes user input and conversation history to
identify the best-suited agent," the chosen agent processes the request, and
the orchestrator "records the exchange and returns the response" (AWS Labs,
Agent Squad documentation, https://github.com/awslabs/agent-squad, verified
2026-08-02, noting the project has since moved to
https://github.com/2fastlabs/agent-squad under the same name history).

Two things are worth naming here because they get confused constantly. First,
Supervisor is not the only multi-agent topology, it is one of several named
topologies that also include Network, where every agent can talk to every
other agent, Hierarchical, supervisors of supervisors, and Handoff, a peer
agent transfers control directly to another peer with no central router.
Second, the word supervisor in this pattern means router, not manager in the
human-organization sense. The supervisor agent typically does no domain work
itself. Its entire job is to read the current state and decide which single
participant acts next, which is closer to a dispatcher than to a boss.

## 2. Problem and context

A single LLM-driven agent loop, one system prompt, one tool set, one context
window, works well until the task genuinely needs more than one area of
expertise or more than one independent thread of exploration. Two distinct
pressures push a team past a single agent, and it is worth separating them
because they call for different justifications.

The first pressure is domain specialization. A support system needs an agent
that is good at looking up an order status, a different agent that is good at
processing a refund with the correct guardrails, and a third that answers FAQ
questions from a knowledge base. Stuffing all three domains, their distinct
tool sets, and their distinct guardrails into one system prompt produces an
agent whose instructions fight each other and whose tool list grows past what
a model reliably attends to. Anthropic frames this need for compression
directly, describing the work of research as distilling insight out of a
large body of source material, a compression job that a single overloaded
context window performs worse the broader the query becomes (Anthropic,
multi-agent research system writeup, verified 2026-08-02).

The second pressure is parallelizable breadth. Some tasks are not really about
different domains, they are about the same kind of work performed on several
independent slices of the problem at once. Anthropic's example is exactly this
shape, a lead agent spawns several subagents that each explore a different
angle of a broad research question in parallel, each with its own separate
context window, and the lead agent later synthesizes their findings. The state
model for this second case is deliberately isolated rather than shared,
because letting every subagent see every other subagent's half-finished work
would collapse the value of exploring independently.

Both pressures create the same structural need, something has to decide who
acts next, hand that participant the right slice of context, and reassemble
the results into a single coherent answer for the caller. That something is
the supervisor. The context in which this pattern belongs is specifically an
LLM-orchestrated system where the routing decision itself benefits from
judgment, not from a fixed workflow graph. When the sequence of who does what
is known in advance and does not change per request, a plain pipeline or a
deterministic state machine is the right tool and a supervisor is unneeded
weight, exactly the boundary drawn in dimension 4.

## 3. Forces

Latency versus quality of decomposition. A supervisor call is itself an LLM
call, and in the naive design it runs before every worker turn, adding a full
round trip of latency to every step of a multi-turn task. A better
decomposition, more subagents working genuinely independent slices, tends to
improve final answer quality on broad, open-ended tasks, but every added
subagent adds its own latency and, in a sequential implementation, that
latency stacks. Anthropic reports its production implementation runs subagents
sequentially rather than asynchronously specifically because of this force,
which "prevents mid-task steering and creates blocking dependencies between
research phases," an explicit trade the team made and named rather than solved
(Anthropic, verified 2026-08-02).

Coupling and blast radius. A supervisor concentrates routing logic in one
place, which lowers coupling between the worker agents themselves, since a
refund agent never needs to know the order-status agent exists. That same
concentration raises the blast radius of the supervisor's own prompt. A
regression in the supervisor's routing instructions degrades every worker
behind it, whereas a regression in one worker's prompt degrades only that
worker's domain.

Consistency versus isolation. A shared-scratchpad topology, the collaborative
alternative LangGraph documents alongside supervisor, keeps every participant
aware of every other participant's reasoning, which favors consistency across
agents at the cost of context bloat. The supervisor pattern, in its
Anthropic-documented isolated-subagent form, sacrifices that cross-agent
visibility in exchange for parallelism and reduced path dependency, "this
isolation reduces path dependency and allows thorough investigation without
interference" (Anthropic, verified 2026-08-02). Neither is free, a team that
needs subagents to build on each other's partial findings mid-task is choosing
the wrong end of this trade if it reaches for supervisor with full isolation.

Cost. Anthropic states plainly that its multi-agent research system uses
"approximately 15x more tokens than chats," which forces the team to reserve
the pattern for tasks whose value justifies that multiplier (Anthropic,
verified 2026-08-02). This is not a minor implementation detail, it is a
first-order design force. A team that adopts supervisor for tasks a single
agent already handles well is paying a real multiple of token cost for no
quality gain.

Operability and debuggability. A single agent's failure has one obvious
culprit. A supervisor system's failure can originate in the supervisor's
routing decision, in a worker's execution, or in the synthesis step that
recombines worker output, and Anthropic's team found that "minor system
failures can be catastrophic for agents" precisely because errors compound
across these hops (Anthropic, verified 2026-08-02). Observability has to be
designed in from the start, covered in dimension 16, or debugging becomes a
matter of guessing which hop failed.

Team topology. Because worker agents in this pattern are independently
prompted, independently tool-scoped units, different engineers or teams can
own different workers without coordinating on a single shared prompt, which is
engineering judgment observed in practice rather than a claim this repository
has a citation for, and it is stated here as judgment, not fact.

## 4. Applicability and non-applicability

Reach for a multi-agent supervisor when the task genuinely spans more than one
domain of expertise that benefits from distinct tools, distinct guardrails, or
distinct system prompts, and cramming them into one agent has already produced
measurably worse instruction-following. Reach for it when a task is broad and
open-ended enough to decompose into independently explorable subtasks whose
results can be recombined afterward, the shape Anthropic names explicitly for
research queries. Reach for it when the routing decision itself needs
judgment that a fixed if-else or a static workflow graph cannot express, for
example because the right next agent depends on the content of a user message
that a classifier or an LLM must interpret. Reach for it when the value of the
task, measured in outcome quality or in what the alternative costs, clearly
exceeds the roughly order-of-magnitude token multiplier the pattern imposes.

Do not reach for it in any of these situations.

The task is well served by a single agent with a well-scoped tool list. Adding
a supervisor here adds latency and token cost with no quality gain, this is
the single most common misuse this repository has observed described in
practitioner writeups and is the first thing a review should check.

The sequence of steps is known and fixed ahead of time, for example always
run retrieval, then always run synthesis, then always run formatting. A
deterministic pipeline, or the plain Chain of Responsibility pattern with a
fixed chain order, does this with no LLM call spent on a decision that has
only one correct answer. Spending a model call to make a decision that a
static graph edge already encodes is pure waste.

Two agents genuinely need to hand off control to each other directly, with the
receiving agent taking over the full conversation and the first agent exiting
the loop, rather than reporting back to a coordinator. This is the Handoff
topology, implemented directly by the OpenAI Agents SDK, where "handoffs are
represented as tools to the LLM" and, by default, "when a handoff occurs, it's
as though the new agent takes over the conversation, and gets to see the
entire previous conversation history" (OpenAI, Agents SDK handoffs docs,
https://openai.github.io/openai-agents-python/handoffs/, verified 2026-08-02).
Handoff has no central coordinator reassembling results, it is architecturally
incompatible with supervisor's shape, which is why it is listed as
incompatible in the frontmatter rather than merely related.

The task requires subagents to see and build on each other's partial work
step by step, not just receive a final synthesized answer. This is the
collaborative shared-scratchpad topology, not supervisor, and forcing
isolated-context subagents into a task that needs shared reasoning produces
duplicated or contradictory work, one of the failure modes named in dimension
11.

The budget cannot absorb an order-of-magnitude token multiplier over a single
agent, and the task at hand is not high enough value to justify it. Anthropic
states this constraint as a design principle, not a caveat, systems of this
kind "require clear evaluation of when the increased performance justifies
the higher token usage" (Anthropic, verified 2026-08-02).

## 5. Structure

Supervisor. The routing participant. Reads the current conversation or task
state, decides which worker agent, if any, should act next, and typically
performs no domain work itself. In the tools-based implementation used by
LangGraph, each worker agent is exposed to the supervisor as a callable tool,
so the supervisor's own decision loop is an ordinary tool-calling agent loop
whose available tools happen to be other agents rather than APIs.

Worker agent, also called subagent, specialist agent, or participant. A
domain-scoped agent with its own system prompt, its own tool set, and
frequently its own isolated context window. A worker's job is to complete the
slice of work it is handed and report a result back, not to decide what
happens next in the overall task.

Shared state or scratchpad. The subset of information visible to more than one
participant. In the isolated-context implementation Anthropic describes, this
is deliberately thin, limited to the lead agent's persistent research plan,
stored externally so it survives context-window pressure, and the final
findings each subagent reports back. In the collaborative alternative
LangGraph documents, this is thick, a single shared message list every
participant reads and appends to.

Router or classifier. In some implementations this role is split out from the
supervisor as a separate, often cheaper or non-LLM, component. AWS's Agent
Squad names this split explicitly. The Classifier selects the agent, that
agent executes, and the Orchestrator, a distinct component, records the
exchange and returns the response. Whether classifier and orchestrator are one
component or two is an implementation choice, not a structural requirement of
the pattern, both shapes appear across the surveyed frameworks.

Synthesizer or aggregator. The step, sometimes performed by the supervisor
itself and sometimes by a separate final-answer agent, that recombines worker
outputs into the single response returned to the caller. Anthropic's lead
agent performs this role after all subagents complete.

## 6. ASCII structure diagram

```
+------------------------------------------------------------+
|                         Caller                              |
+---------------------------+----------------------------------+
                            |
                            v
                +-----------------------+
                |      Supervisor        |  <- reads state, no
                |  (routing decision)    |     domain work itself
                +-----------------------+
                  |        |        |
     "worker A"   |        |        |  "worker C"
        as tool    |  "worker B"    |    as tool
                    v   as tool    v
        +---------------+  +----+---+  +---------------+
        | Worker Agent A |  | Worker |  | Worker Agent C |
        | (own prompt,   |  | Agent  |  | (own prompt,   |
        |  own tools,    |  | B      |  |  own tools,    |
        |  own context)  |  |        |  |  own context)  |
        +-------+--------+  +---+----+  +--------+-------+
                |               |                |
                v               v                v
        +--------------------------------------------------+
        |     Shared state (thin: plan + final results,     |
        |     or thick: full shared scratchpad, per design) |
        +--------------------------------------------------+
                            |
                            v
                +-----------------------+
                |   Synthesizer /        |
                | Aggregator (often the  |
                | supervisor itself)     |
                +-----------------------+
                            |
                            v
                +-----------------------+
                |    Final response      |
                +-----------------------+
```

## 7. Dynamics

The tool-calling implementation, the shape LangGraph documents, runs as an
ordinary agent loop at the supervisor level. On each turn the supervisor
receives the current message state, decides either to call a worker
represented as a tool or to end the loop and return a final answer, and that
decision is made the same way any tool call is made. The underlying model
picks a tool name and arguments from its available tool schema. A worker
invoked this way runs its own, possibly multi-step, internal loop using its
own prompt and tools, then returns a single result back up to the supervisor,
which appends that result to the shared state and loops again to decide the
next step.

The parallel-fan-out implementation, the shape Anthropic documents for its
research system, differs in when subagents are spawned and how their results
are recombined. The lead agent first reads the incoming query, develops a
research strategy, and decides up front how many subagents to spawn and what
each should investigate, rather than deciding one worker at a time inside a
loop. Anthropic reports this decomposition step is where early prototypes
failed most often, producing over 50 subagents for simple queries or vague
task descriptions that caused duplicated work across subagents (Anthropic,
verified 2026-08-02). Each spawned subagent then runs independently in its own
context window, with no visibility into sibling subagents' progress, and
reports its findings back to the lead agent only once it completes. The lead
agent waits for the subagents it spawned, in the current production
implementation sequentially rather than concurrently, then synthesizes all
findings into a single response.

```
sequence. fan-out and synthesize (Anthropic-style)

Caller        Supervisor(lead)      Worker A        Worker B
  |  query          |                   |                |
  |---------------->|                   |                |
  |                  | decompose into   |                |
  |                  | N subtasks       |                |
  |                  |------------------>|                |
  |                  |    spawn A        |                |
  |                  |-------------------------------->    |
  |                  |    spawn B                          |
  |                  |                   | isolated context|
  |                  |                   | explores slice A|
  |                  |                   |------ result A ->|
  |                  |<------------------|                |
  |                  |                   |  isolated context
  |                  |                   |  explores slice B
  |                  |                   |<------ result B -|
  |                  |<--------------------------------------|
  |                  | synthesize A + B  |                |
  |<-----------------|  into final answer|                |
  |  final response  |                   |                |
```

## 8. Implementation variants

Tool-based supervisor. Each worker is registered on the supervisor's tool
schema exactly like an API tool, and the supervisor's own model decides which
tool to call by name. This is the shape LangGraph documents and the shape most
directly portable to any LLM SDK that supports function calling, since a
worker agent is, from the supervisor's point of view, indistinguishable from
any other callable tool.

Classifier-plus-orchestrator split. Routing is separated into a distinct,
often lighter-weight classification step, which can be a smaller or cheaper
model, a fine-tuned classifier, or even a non-LLM heuristic, from the
bookkeeping step that records the exchange and formats the returned response.
AWS's Agent Squad implements this split explicitly, and the split is valuable
whenever routing decisions are simple enough that spending a full-capability
model call on every routing decision is wasteful.

Graph-based state machine supervisor. The supervisor is not a freestanding
loop but a named node inside a directed graph, where edges from the supervisor
node to worker nodes and back are declared statically and the runtime decides,
at each visit to the supervisor node, which outgoing edge to take. LangGraph's
own implementation is this shape, the graph structure is fixed and inspectable
ahead of time, while the specific path taken through it varies per request.
This variant trades a small amount of flexibility for materially better
debuggability, since the set of possible next states is enumerable from the
graph definition alone.

Group-chat manager selection. Rather than the supervisor calling a worker as
a discrete function, all participants including the supervisor share a single
conversation transcript, and the manager's only job each turn is to pick which
participant speaks next. AutoGen's SelectorGroupChat implements this variant.
The manager "uses a ChatCompletion model to select the next speaker" after
each message, guided by a configurable prompt template populated with roles,
participants, and history, and exposes `allow_repeated_speaker` and
`max_selector_attempts` as explicit controls over selection behavior
(Microsoft, AutoGen stable docs, verified 2026-08-02). This variant keeps a
single shared transcript rather than isolated per-worker context, which makes
it closer to the collaborative topology than to Anthropic's isolated-subagent
research-system shape, even though both are commonly called supervisor
patterns in casual usage.

Hierarchical supervisors. A supervisor's own worker set can itself contain
another supervisor managing a sub-team, nesting the pattern recursively.
LangGraph's documentation names this explicitly as an extension of the
single-level supervisor, built by treating an entire nested graph as a single
callable participant from the parent supervisor's point of view (LangChain,
verified 2026-08-02). This variant is the right tool when a domain is itself
complex enough to need its own internal routing, for example a "finance team"
sub-supervisor that internally coordinates a billing worker and a fraud-review
worker, exposed to the top-level supervisor as one unit.

Deterministic-function router as supervisor. The routing step need not be an
LLM call at all. A plain function, keyed on message intent already classified
upstream, a regex, or a rules engine, can serve as the supervisor node in an
otherwise identical topology. This is a legitimate variant when the number of
routing categories is small and stable and paying for an LLM call on every
routing decision is not justified, it trades routing flexibility for latency
and cost, and is worth calling out because teams sometimes assume supervisor
must mean an LLM-powered router, when the defining structural property is
central routing to independent workers, not the implementation of the
decision itself.

## 9. Known production uses

Claude's multi-agent research feature, shipped by Anthropic, uses an
orchestrator-worker architecture where "a lead agent coordinates the process
while delegating to specialized subagents that operate in parallel," and
Anthropic's own internal evaluation found this multi-agent system outperformed
single-agent Claude Opus 4 by 90.2 percent on their internal research
evaluation, a figure Anthropic reports directly attached to the trade-off that
the system also uses roughly 15 times the tokens of a single chat interaction
(Anthropic, "How we built our multi-agent research system," verified
2026-08-02). This is the most directly documented, first-party production use
this repository could verify, including named failure modes the team observed
in early versions and the specific fixes applied.

AWS's Agent Squad, formerly named Multi-Agent Orchestrator, is a maintained
open-source framework, distributed in three parity runtimes, Python,
TypeScript, and Swift, implementing the classifier-plus-orchestrator variant
of this pattern for conversational applications that need to route a user
turn to the correct specialized agent, including maintaining conversation
context across agent switches (AWS Labs, Agent Squad documentation, verified
2026-08-02). The project is maintained by AWS Labs and continues under
community stewardship at 2fastlabs/agent-squad after the rename, and its
README documents production-shaped concerns directly, streaming and
non-streaming response support, pluggable storage, and pluggable retrievers,
which are the concerns a team building a customer-facing multi-agent support
system genuinely has, not academic demonstration concerns.

Microsoft's AutoGen, the framework introduced in Wu et al., arXiv 2308.08155,
2023, ships GroupChatManager and its model-driven successor SelectorGroupChat
as first-class, documented components in its stable public API, used to
coordinate conversable agents in a shared group chat where the manager
decides, turn by turn, which agent speaks next (Microsoft, AutoGen stable
docs, verified 2026-08-02). AutoGen is maintained by Microsoft Research and
has been adopted broadly enough among open-source LLM tooling projects that
its GroupChatManager naming, manager selects the next speaker, workers
produce content, is one of the two or three most commonly cited reference
implementations of this pattern in practitioner writeups this repository's
research pass encountered.

LangGraph, LangChain's graph-based agent orchestration library, documents the
supervisor pattern as one of its named reference architectures for multi-agent
systems, alongside network and hierarchical topologies, and the framework is
used across a wide range of production LangChain deployments. LangChain's own
blog post states the supervisor's defining property directly, that it "can
also be thought of an agent whose tools are other agents," which this
repository treats as the clearest single-sentence definition of the pattern's
structure across all the surveyed implementations (LangChain, verified
2026-08-02).

## 10. Consequences

Positive.

Domain isolation. Each worker agent can be prompted, tooled, and tested
independently of every other worker, which lets teams own and iterate on
separate workers without the cross-contamination that a single monolithic
system prompt suffers as it grows.

Parallel exploration on genuinely open-ended tasks. When the task decomposes
into independent slices, isolated-context subagents can explore those slices
concurrently, and Anthropic's own measured result, a 90.2 percent improvement
over single-agent Claude Opus 4 on their internal research evaluation, is
direct evidence this parallelism buys real quality on the right task shape
(Anthropic, verified 2026-08-02).

Central point of routing control. Access control, rate limiting, logging, and
guardrail enforcement can all live in one place, the supervisor, rather than
being duplicated across every worker, which is a genuine operational win for
governance-sensitive systems.

Composability into hierarchies. Because a supervisor's worker can itself be
another supervisor, the pattern scales structurally to arbitrarily deep
organizational shapes without inventing a new mechanism at each level.

Negative.

Token and latency cost. Anthropic's own reported figure, roughly 15 times the
token usage of a single-agent chat, is not a worst case, it is the documented
cost of a production system built by the team that also documents its
benefit, which means this cost is intrinsic to the pattern's value
proposition, not an implementation mistake to be optimized away (Anthropic,
verified 2026-08-02).

Error compounding across hops. A mistake at the supervisor's routing step, at
any single worker's execution, or at the synthesis step propagates forward,
and Anthropic's team observed directly that "minor system failures can be
catastrophic for agents" in this architecture because of how errors cascade
across turns (Anthropic, verified 2026-08-02).

Coordination overhead that early implementations underestimate. Anthropic
reports its own early prototype spawned more than 50 subagents for simple
queries and duplicated work across subagents when task descriptions were
vague, both direct consequences of getting the decomposition step wrong, and
both requiring deliberate engineering fixes rather than resolving themselves
as the underlying model improved (Anthropic, verified 2026-08-02).

Debuggability tax. A failure report from a supervisor system has to name
which participant, and often which turn, produced the wrong output before a
fix is possible, which is strictly harder than debugging a single agent's
single trace and requires the observability investment described in
dimension 16 to be paid up front rather than added later.

## 11. Failure modes and misuse

Over-decomposition. The symptom is the supervisor spawning far more workers
than the task warrants, for example dozens of subagents for a question a
single agent could answer directly, producing high latency and cost with no
proportional quality gain. The cause is a decomposition prompt or logic with
no upper bound and no cost-awareness, so the model defaults to maximal
fan-out whenever it is plausible rather than whenever it is warranted. This is
not a hypothetical concern, Anthropic reports this exact failure directly,
"spawning excessive subagents (50+) for simple queries," as an early
production problem in its own system (Anthropic, verified 2026-08-02). The
fix is bounding the maximum number of subagents explicitly, and gating
fan-out behind a cheap upfront judgment of query complexity rather than
letting the decomposition step decide freely.

Vague task boundaries causing duplicated work. The symptom is two or more
workers independently producing overlapping or contradictory results on what
turns out to be the same underlying subtask. The cause is the supervisor's
task descriptions to workers being underspecified, so workers cannot tell
their slice apart from a sibling's slice. Anthropic names this directly as an
observed production failure, "duplicating work when task descriptions were
vague" (Anthropic, verified 2026-08-02). The fix is requiring the
supervisor's decomposition step to produce explicitly non-overlapping task
boundaries, and validating that boundaries are disjoint before dispatching
workers, rather than trusting the decomposition prompt to get this right
implicitly.

Runaway or under-terminated workers. The symptom is a worker continuing to
call tools or produce output well past the point where it already has
sufficient information to answer, inflating latency and cost. The cause is
the worker having no explicit stopping criterion tied to information
sufficiency, so it defaults to exhausting its available turn budget.
Anthropic names this directly, "agents continuing research despite having
sufficient information," as an early observed failure (Anthropic, verified
2026-08-02). The fix is giving each worker an explicit, checkable stopping
condition, not just a maximum turn count, and preferring a worker that
self-reports confidence over one that only stops when it runs out of turns.

Router misclassification. The symptom is a user request being routed to the
wrong specialist, most visibly when a refund request lands on the
order-status agent and the worker either fails silently or, worse, attempts
the task outside its intended scope and guardrails. The cause is the
classifier or supervisor prompt having insufficient discriminating signal
between similar-sounding categories, or the worker descriptions it routes
against being themselves vague. The fix is treating the classifier's routing
accuracy as a measured, monitored metric, not an assumed property, logging
every routing decision with its confidence, and alerting on low-confidence
routes rather than silently dispatching them.

Synthesis losing information. The symptom is the final answer omitting or
misstating a finding that an individual worker correctly produced, because
the supervisor's synthesis step compressed too aggressively or was not given
enough of each worker's raw output to preserve nuance. The cause is a
synthesis prompt that treats worker outputs as short summaries to be glued
together rather than as sources it must reconcile and attribute carefully.
The fix is passing full worker outputs, or well-structured intermediate
artifacts, into synthesis rather than pre-compressed one-line summaries, and
having the synthesis step cite which worker produced which claim so a
downstream reviewer can trace a disputed statement back to its source.

Treating the pattern as a default choice for tasks that do not need it. The
symptom is a team standing up a full supervisor architecture for a task a
single, well-scoped agent already handles correctly, and the team then being
surprised by a fifteen-fold token bill increase with no corresponding quality
improvement. The cause is adopting the pattern by imitation, because it is
the trend in agentic tooling, rather than because the task exhibits the
specific forces described in dimension 3. The fix is requiring a stated
justification, either genuine domain separation or genuine parallelizable
breadth, before adopting the pattern, and measuring the outcome quality delta
against a single-agent baseline before committing to it in production,
matching the explicit evaluation discipline Anthropic states it applies
before shipping multi-agent systems.

## 12. Trade-off matrix

| Force | Multi-Agent Supervisor | Single agent, larger tool set | Peer-to-Peer Handoff | Deterministic pipeline (Chain of Responsibility) |
|---|---|---|---|---|
| Latency per request | High, one routing call plus N worker calls, higher still if sequential | Low, one agent loop | Moderate, no central router hop but full history transfer per hop | Lowest, no routing decision cost |
| Token cost | Highest, roughly 15x a single chat per Anthropic's reported figure | Baseline | Moderate, grows with number of hops and history carried | Lowest, fixed steps only |
| Domain separation | Strong, each worker independently prompted and tooled | Weak, one prompt must cover every domain | Strong, each peer independently prompted | Strong if each stage is a distinct component, but stages are fixed, not dynamically chosen |
| Suitable when sequence is fixed | Overkill, pays for a decision with only one right answer | Fine if the tool list stays manageable | Not designed for fixed sequences | Best fit |
| Suitable for open-ended parallel exploration | Best fit, this is the case Anthropic reports the largest measured gain for | Weak, no parallelism | Weak, control passes serially, not in parallel | Not applicable, no branching |
| Central governance point | Strong, one place to enforce guardrails and logging across all routing | Effectively N/A, single agent is itself the point | Weak, control and its guardrails move with the conversation | Strong, but only over a fixed sequence |
| Debuggability | Hardest, failure can originate at any of three hops | Easiest, one trace | Moderate, trace follows the conversation across peers | Easiest among multi-step designs, sequence is fixed and inspectable |
| Composability into hierarchies | Native, a worker can itself be a nested supervisor | Not applicable | Not designed for nesting | Possible but requires an outer coordinator not native to the pattern |

## 13. Related and incompatible patterns

Chain of Responsibility. The classic object-oriented pattern this repository
also documents shares the surface idea of a request moving through a sequence
of handlers, but the two differ in the axis that matters most, Chain of
Responsibility's handlers are typically arranged in a fixed, statically known
order and each handler either processes the request or forwards it unchanged
to the next, with no central decision-maker choosing the path per request. A
multi-agent supervisor instead makes an active, per-request routing decision
and can call a worker directly rather than passing a request hand to hand.
Teams sometimes reach for supervisor when what they actually need is a plain
Chain of Responsibility with a static order, which is the cheaper and more
debuggable choice whenever the order genuinely never varies.

Mediator. The supervisor's structural idea, a central component that
coordinates interactions between otherwise-decoupled participants so those
participants do not need to know about each other, is a direct application of
the Mediator pattern to LLM agents. Where classic Mediator coordinates a fixed
set of GUI widgets or domain objects, a multi-agent supervisor coordinates a
set of LLM-driven workers, and the mediator's coordination logic is itself
frequently LLM-driven rather than hand-coded, which is the genuinely new
element this domain adds to an old, well-understood structural idea.

Strategy. Each worker agent, viewed from the supervisor's side, is
interchangeable in the same way a Strategy implementation is, the supervisor
selects which worker to invoke without needing to know how that worker
internally accomplishes its task, only what interface, typically a
function-call or tool schema, it exposes. The selection mechanism differs
from classic Strategy in that the choice is dynamic per request and often
made by a model rather than set once by the calling code.

Tool Use and Function Calling. This pattern is the load-bearing mechanism the
tool-based supervisor variant depends on entirely. A worker agent exposed to
the supervisor as a callable tool is, from the supervisor's model's point of
view, indistinguishable from any other function-calling tool, which is
precisely the mechanism the OpenAI Agents SDK names directly for its own
handoff implementation, "handoffs are represented as tools to the LLM"
(OpenAI, verified 2026-08-02), and the same mechanism LangGraph's supervisor
uses to expose workers.

ReAct Agent Loop. Each individual worker agent, and frequently the supervisor
itself, is commonly implemented internally as a ReAct-style reason-then-act
loop. Supervisor composes with ReAct rather than replacing it, ReAct describes
how a single agent decides its next action, and supervisor describes how
several such single-agent loops are coordinated at a level above any one of
them.

Peer-to-Peer Handoff, incompatible. Listed as incompatible in the frontmatter
because the two patterns make opposite structural choices about where control
and coordination live. Supervisor keeps a central coordinator that every
worker reports back to, Handoff, as implemented by the OpenAI Agents SDK,
transfers full control to the receiving agent, which then owns the
conversation directly with no return to a central router, "as though the new
agent takes over the conversation" (OpenAI, verified 2026-08-02). A system
that mixes both without a clear boundary between them produces ambiguous
ownership of the final response, since it is unclear whether the original
supervisor or the handed-off agent is responsible for what happens next.
Systems that need both shapes typically nest them, a supervisor that includes
one worker which internally uses handoffs among its own sub-peers, rather than
blending the two at the same level.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently has one large agent.
Start by auditing the single agent's system prompt and tool list for natural
seams, groups of instructions and tools that only apply to one class of
request and never interact with another class. Extract each seam into its own
worker agent with only the tools and instructions relevant to that seam,
leaving the original agent's tool list strictly smaller after each extraction.
Once at least two workers exist, replace the original monolithic agent's
remaining direct-response logic with a thin supervisor whose only job is to
decide which extracted worker, if any, should handle the current turn, using
the exact worker descriptions the extraction step produced as the routing
signal. Validate at this point, before adding a third worker, that overall
task quality on a held-out evaluation set has not regressed relative to the
original single agent, since the token and latency cost the pattern
introduces is only justified once this baseline holds. Only after that
baseline holds should additional workers be extracted, one seam at a time,
each validated the same way, rather than decomposing the whole system in one
pass.

Removing the pattern from a system that has outgrown it, or that adopted it
prematurely. This direction is worth naming explicitly because it is the less
commonly documented one and the one Anthropic's own cost figures make most
relevant. If measurement shows a supervisor system's quality gain over a
well-tuned single agent does not justify its roughly order-of-magnitude token
cost, collapse the workers back toward a single agent starting with the two
workers whose domains overlap the most, since merging overlapping domains
first removes the routing ambiguity that caused misclassification failures in
the first place, and merging non-overlapping domains first tends to recreate
the original bloated, hard-to-follow single prompt the extraction was meant to
avoid. After each merge, re-run the same held-out evaluation set used during
introduction and stop merging as soon as further merges start to regress
quality below the acceptable floor for the task, which marks the point where
the remaining domain separation is earning its keep.

## 15. Testing and verification

Test the routing decision independently of worker execution. Build a labeled
set of representative inputs, each paired with the worker or workers a human
reviewer agrees is correct, and run only the supervisor's routing step against
this set, mocking out actual worker execution entirely. This isolates
classifier accuracy from execution quality and makes routing regressions
visible immediately rather than buried inside an end-to-end quality metric
that could also move for unrelated reasons.

Test each worker in isolation with its own held-out evaluation set, exactly as
if it were a standalone single agent, since from a testing point of view each
worker is a standalone single agent with a narrower scope. This is the
existing single-agent testing discipline applied per worker, and it is easier
to build good evaluation sets per worker than for the whole system, because
each worker's scope is deliberately narrower.

Test the synthesis step with controlled, synthetic worker outputs rather than
only end to end. Feed the synthesizer a fixed set of worker outputs, including
adversarial cases such as two workers returning contradictory findings, and
verify the synthesis either resolves the contradiction with correct reasoning
or surfaces it rather than silently picking one side.

Test the full pipeline end to end against outcome-level evaluation, not just
component-level correctness, since a system where every component tests
correctly in isolation can still fail end to end if the interfaces between
components lose information at the seams, exactly the synthesis failure mode
in dimension 11. Anthropic's own evaluation methodology is directly cited
evidence this is standard practice at the highest-scale documented deployment
of this pattern, the team measured its multi-agent system's 90.2 percent
improvement against single-agent Claude Opus 4 using an internal research
evaluation designed for the outcome, not for any individual component
(Anthropic, verified 2026-08-02).

Test doubles that apply. A mock worker, a fixed function returning a
predetermined result instead of invoking a real LLM-backed worker, is the
right double for isolating supervisor routing tests from worker
non-determinism and cost. A recorded transcript, capturing a real run's
sequence of supervisor decisions and worker outputs, serves as a regression
fixture that can be replayed to detect whether a prompt change altered
routing behavior on a known case, without needing to re-run the full,
expensive live system for every regression check.

What became harder because of the pattern. Reproducing a specific failure is
harder than in a single agent, because the same input can route differently
across runs if the supervisor's decision has any non-determinism, which means
a test suite for this pattern needs either deterministic routing for its
regression fixtures or explicit seed and temperature control on the
supervisor's own model calls, neither of which a single-agent test suite
typically has to think about.

## 16. Observability signals

Log the supervisor's routing decision on every turn, including which worker
or workers were selected, the reasoning or confidence the supervisor produced
if the underlying model exposes one, and the full state the supervisor
observed when it made the decision. This is the single most valuable log line
in the system, because dimension 11's misclassification and over-decomposition
failure modes are both, first and foremost, diagnosed from this log.

Trace each worker's execution as its own span, tagged with the supervisor
decision that spawned it, so that a distributed trace of one end-to-end
request shows the full tree, one supervisor span, N worker spans nested or
linked underneath it, and one synthesis span consuming all N worker outputs.
This tree shape is what makes the debuggability cost named in dimension 10
tractable at all, without it, a failure report has no way to localize which
hop produced the wrong output.

Measure token usage per component, not just per request, specifically
supervisor tokens, per-worker tokens, and synthesis tokens tracked separately.
Since Anthropic's reported cost figure, roughly 15x a single chat, is an
aggregate, a team cannot know which component to optimize without this
breakdown, and a component-level breakdown is what makes the introduction and
removal refactoring paths in dimension 14 measurable rather than a guess.

Track worker fan-out count as a metric with an alert threshold, since
Anthropic's own reported failure, spawning more than 50 subagents for a
simple query, is directly detectable as an anomalous spike in this single
metric before it ever reaches a human reviewing transcripts.

A healthy instance on a dashboard looks like a narrow, stable distribution of
worker fan-out count clustered around the expected range for the task types
the system serves, routing confidence consistently above whatever threshold
the team has validated correlates with correct routing, and per-component
token cost that scales roughly linearly with fan-out rather than showing
runaway growth in any single worker's turn count. A failing instance looks
like a bimodal or long-tailed fan-out distribution, indicating the
decomposition step is inconsistent, a routing confidence metric that has
drifted downward over time without a corresponding prompt or model change,
which usually signals the underlying request distribution has shifted away
from what the classifier was validated against, or a single worker's token
consumption growing without bound on a subset of requests, which usually
signals the under-termination failure mode from dimension 11.

## 17. Security and privacy implications

Tool and data scope must be enforced per worker, not assumed from the
supervisor's own scope. Because each worker typically has its own tool set,
the security boundary that matters is what each individual worker can access,
and a common mistake is granting every worker the union of all tools the
system needs anywhere, which turns any single worker compromise, whether from
prompt injection or from a genuine model error, into access to capabilities
that worker's stated domain never required. Scope each worker's tools as
narrowly as the domain-separation rationale for creating that worker in the
first place already implies.

Cross-worker data leakage through the shared state. In the collaborative,
shared-scratchpad variant, information one worker gathers, including anything
sensitive the caller provided that turn, is visible to every other
participant by default, which may violate a need-to-know boundary the system
otherwise intends to enforce, for example a refund worker seeing an order
history detail that a general FAQ worker had no legitimate reason to read.
The isolated-context variant Anthropic documents avoids this specific risk
structurally, since a subagent only ever sees the task description the
supervisor gave it, not sibling subagents' raw findings, which is a genuine
privacy advantage of that variant worth weighing alongside its other
trade-offs.

Prompt injection surface multiplies with worker count. Every worker that
processes external or user-controlled content, a fetched web page, a document,
a customer message, is an independent injection surface, and a supervisor
architecture does not reduce this risk relative to a single agent, it
multiplies the number of independent surfaces an attacker could target,
because each worker's own prompt and tool set is a separate target rather
than one shared surface a single defense could cover. Each worker needs its
own injection-resistant prompt design and its own output validation before
its result is trusted by the synthesizer, rather than assuming a defense
applied once at the supervisor level covers every downstream worker.

Synthesis is a trust boundary. The synthesizer consumes output from every
worker and produces the response the caller sees, which means a compromised
or manipulated worker's output can influence the final answer unless the
synthesis step treats worker output as untrusted input requiring the same
scrutiny a single agent would apply to any external tool result, not as
already-trusted internal state simply because it came from another part of
the same system.

## 18. References

Anthropic. "How we built our multi-agent research system." Anthropic
Engineering blog.
https://www.anthropic.com/engineering/multi-agent-research-system. Verified
2026-08-02.

LangChain. "LangGraph Multi-Agent Workflows." LangChain blog.
https://www.langchain.com/blog/langgraph-multi-agent-workflows. Verified
2026-08-02.

Microsoft. "autogen_agentchat.teams." AutoGen stable API reference.
https://microsoft.github.io/autogen/stable/reference/python/autogen_agentchat.teams.html.
Verified 2026-08-02.

Wu, Qingyun, Gagan Bansal, Jieyu Zhang, Yiran Wu, Beibin Li, Erkang Zhu, Li
Jiang, Xiaoyun Zhang, Shaokun Zhang, Jiale Liu, Ahmed Hassan Awadallah, Ryen W.
White, Doug Burger, and Chi Wang. "AutoGen. Enabling Next-Gen LLM Applications
via Multi-Agent Conversation." arXiv 2308.08155, 2023.
https://arxiv.org/abs/2308.08155. Verified 2026-08-02.

AWS Labs. "Agent Squad" (formerly Multi-Agent Orchestrator). GitHub
repository. https://github.com/awslabs/agent-squad. Verified 2026-08-02.
Project stewardship subsequently moved to
https://github.com/2fastlabs/agent-squad under the same name.

OpenAI. "Handoffs." OpenAI Agents SDK documentation.
https://openai.github.io/openai-agents-python/handoffs/. Verified 2026-08-02.

Microsoft. "Multi-Agent Reference Architecture."
https://microsoft.github.io/multi-agent-reference-architecture/. Verified
2026-08-02.

## Code examples

Three implementations follow, TypeScript, Python, and Go, each implementing
the same minimal shape, a supervisor that inspects an incoming request, routes
it to one of two narrowly scoped worker functions standing in for worker
agents, and returns the worker's result. This mirrors the tool-based
supervisor variant from dimension 8 at the smallest scale that still shows the
structural point, that the supervisor's decision is a first-class, inspectable
step separate from any worker's execution, without the added weight of a full
LLM call in a documentation example. A production implementation replaces the
`decideRoute` or `decide_route` function with an LLM tool-calling decision,
the substitution point is intentionally left visible.

### TypeScript

```typescript
type WorkerName = "orderStatus" | "refund" | "faq";

interface WorkerResult {
  worker: WorkerName;
  output: string;
}

interface Workers {
  orderStatus: (input: string) => WorkerResult;
  refund: (input: string) => WorkerResult;
  faq: (input: string) => WorkerResult;
}

// Stands in for the supervisor's LLM tool-call decision in production.
function decideRoute(input: string): WorkerName {
  const lower = input.toLowerCase();
  if (lower.includes("refund")) return "refund";
  if (lower.includes("order") || lower.includes("status")) return "orderStatus";
  return "faq";
}

function supervise(input: string, workers: Workers): WorkerResult {
  const route = decideRoute(input);
  return workers[route](input);
}

const workers: Workers = {
  orderStatus: (input) => ({
    worker: "orderStatus",
    output: `Order lookup for: ${input}`,
  }),
  refund: (input) => ({
    worker: "refund",
    output: `Refund processed for: ${input}`,
  }),
  faq: (input) => ({
    worker: "faq",
    output: `FAQ answer for: ${input}`,
  }),
};

const cases = [
  "What is the status of my order?",
  "I want a refund for this item",
  "What are your business hours?",
];

for (const c of cases) {
  const result = supervise(c, workers);
  console.log(`[${result.worker}] ${result.output}`);
}
```

### Python

```python
from dataclasses import dataclass
from typing import Callable, Dict


@dataclass
class WorkerResult:
    worker: str
    output: str


def decide_route(user_input: str) -> str:
    """Stands in for the supervisor's LLM tool-call decision in production."""
    lowered = user_input.lower()
    if "refund" in lowered:
        return "refund"
    if "order" in lowered or "status" in lowered:
        return "order_status"
    return "faq"


def order_status_worker(user_input: str) -> WorkerResult:
    return WorkerResult("order_status", f"Order lookup for: {user_input}")


def refund_worker(user_input: str) -> WorkerResult:
    return WorkerResult("refund", f"Refund processed for: {user_input}")


def faq_worker(user_input: str) -> WorkerResult:
    return WorkerResult("faq", f"FAQ answer for: {user_input}")


WORKERS: Dict[str, Callable[[str], WorkerResult]] = {
    "order_status": order_status_worker,
    "refund": refund_worker,
    "faq": faq_worker,
}


def supervise(user_input: str) -> WorkerResult:
    route = decide_route(user_input)
    return WORKERS[route](user_input)


if __name__ == "__main__":
    cases = [
        "What is the status of my order?",
        "I want a refund for this item",
        "What are your business hours?",
    ]
    for case in cases:
        result = supervise(case)
        print(f"[{result.worker}] {result.output}")
```

### Go

```go
package main

import (
	"fmt"
	"strings"
)

type WorkerResult struct {
	Worker string
	Output string
}

type WorkerFunc func(input string) WorkerResult

// decideRoute stands in for the supervisor's LLM tool-call decision
// in production.
func decideRoute(input string) string {
	lowered := strings.ToLower(input)
	if strings.Contains(lowered, "refund") {
		return "refund"
	}
	if strings.Contains(lowered, "order") || strings.Contains(lowered, "status") {
		return "order_status"
	}
	return "faq"
}

func orderStatusWorker(input string) WorkerResult {
	return WorkerResult{"order_status", fmt.Sprintf("Order lookup for: %s", input)}
}

func refundWorker(input string) WorkerResult {
	return WorkerResult{"refund", fmt.Sprintf("Refund processed for: %s", input)}
}

func faqWorker(input string) WorkerResult {
	return WorkerResult{"faq", fmt.Sprintf("FAQ answer for: %s", input)}
}

func supervise(input string, workers map[string]WorkerFunc) WorkerResult {
	route := decideRoute(input)
	return workers[route](input)
}

func main() {
	workers := map[string]WorkerFunc{
		"order_status": orderStatusWorker,
		"refund":       refundWorker,
		"faq":          faqWorker,
	}

	cases := []string{
		"What is the status of my order?",
		"I want a refund for this item",
		"What are your business hours?",
	}

	for _, c := range cases {
		result := supervise(c, workers)
		fmt.Printf("[%s] %s\n", result.Worker, result.Output)
	}
}
```

C#, Kotlin, Rust, and Swift beyond the three above were not produced for this
entry. The pattern is not language-idiomatic in a way that would surface
meaningfully different implementation techniques across TypeScript, Python,
and Go versus the remaining languages in the approved set, since the
structural point, a routing step separate from worker execution, expresses
identically as a function dispatching to other functions in any of them, the
three above were chosen because they cover a dynamically typed scripting
language, a statically typed compiled language with structural typing, and a
statically typed compiled language with nominal typing and an explicit error
model, which is enough spread to show the pattern is not tied to any single
language's specific features.
