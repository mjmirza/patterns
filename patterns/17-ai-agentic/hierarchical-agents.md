---
name: Hierarchical Agents
slug: hierarchical-agents
family: 17-ai-agentic
category: Multi-Agent Coordination
aliases: [Hierarchical Agent Teams, Multi-Level Supervisor Pattern, Agent Organizational Chart, Supervisor-of-Supervisors, Nested Agent Delegation]
first_described: "Erol, Hendler, Nau 1994 (HTN planning, decomposition root); LLM-agentic form named by LangChain in the Hierarchical Agent Teams tutorial, circa 2024"
maturity: established
related: [orchestrator-worker, sub-agent-isolation, blackboard, mediator, chain-of-responsibility, composite, strategy, evaluator-optimizer]
incompatible_with: []
verified: 2026-08-02
---

# Hierarchical Agents

## 1. Name, aliases, and lineage

Hierarchical Agents describes a multi-agent system organized as a tree of at
least three levels of authority. A root supervisor sits at the top, one or
more mid-level supervisors, often called team leads, sit in the middle, and
leaf worker agents sit at the bottom, actually calling tools, reading files,
or querying a model to produce an answer. Every mid-level node is itself both a worker
(from the point of view of the level above it) and a supervisor (from the
point of view of the level below it). This recursive dual role is what
separates the pattern from its shallower, more famous cousin.

The name in current LLM-agentic usage traces to a LangChain tutorial titled
"Hierarchical Agent Teams," which built a research assistant out of a
top-level supervisor coordinating a research team and a document-writing
team, each of which had its own internal supervisor. The tutorial states the
motivation directly. "What if the job for a single worker becomes too
complex? What if the number of workers becomes too large? For some
applications, the system may be more effective if work is distributed
hierarchically. You can do this by composing different subgraphs and
creating a top-level supervisor, along with mid-level supervisors." (Wu et
al. citation aside, tutorial text from LangChain, "Hierarchical Agent
Teams," archived notebook,
[github.com/langchain-ai/langgraph/blob/23961cff61a42b52525f3b20b4094d8d2fba1744/docs/docs/tutorials/multi_agent/hierarchical_agent_teams.ipynb](https://github.com/langchain-ai/langgraph/blob/23961cff61a42b52525f3b20b4094d8d2fba1744/docs/docs/tutorials/multi_agent/hierarchical_agent_teams.ipynb),
verified 2026-08-02, note that this file has since been archived and its
successor content lives in LangChain's consolidated documentation site). The
notebook credits its inspiration to Wu, Bansal, Zhang, Wu, Li, Zhu, Jiang,
Zhang, Zhang, Liu, Awadallah, White, Burger, and Wang, "AutoGen. Enabling
Next-Gen LLM Applications via Multi-Agent Conversation," 2023,
[arxiv.org/abs/2308.08155](https://arxiv.org/abs/2308.08155), verified
2026-08-02.

Amazon Web Services uses the same word for its own commercial offering. "You
can use this hierarchical collaboration model to synchronously respond to
prompts and queries from users in real-time," and lets a team grow over
time by adding further collaborator agents as new capabilities are needed.
(AWS, "Use multi-agent collaboration with Amazon Bedrock
Agents,"
[docs.aws.amazon.com/bedrock/latest/userguide/agents-multi-agent-collaboration.html](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-multi-agent-collaboration.html),
verified 2026-08-02, a page that also notes the underlying service, Bedrock
Agents Classic, is no longer open to new customers and points existing and
new users toward Amazon Bedrock AgentCore). Microsoft's AutoGen framework
implements the same idea under the name nested chats, where a receiving
agent runs an entire internal conversation with a private team before
replying to the outer conversation. "Nested chats is a sequence of chats
created by a receiver agent after receiving a message from a sender agent
and finished before the receiver agent replies to this message. Nested
chats allow AutoGen agents to use other agents as their inner monologue to
accomplish tasks." (Microsoft, AutoGen 0.2 documentation, "Nested Chats,"
[microsoft.github.io/autogen/0.2/docs/notebooks/agentchat_nestedchat/](https://microsoft.github.io/autogen/0.2/docs/notebooks/agentchat_nestedchat/),
verified 2026-08-02).

The word hierarchical itself is older than any of these frameworks and comes
from classical AI planning. Hierarchical Task Networks decompose a compound
task into an ordered set of simpler subtasks, recursively, until every
remaining task is directly executable. Kutluhan Erol, James A. Hendler and
Dana S. Nau formalized the computational complexity and expressive power of
this decomposition in "HTN Planning. Complexity and Expressivity," AAAI 1994,
pages 1123 to 1128
([dblp.org/rec/conf/aaai/ErolHN94](https://dblp.org/rec/conf/aaai/ErolHN94),
verified 2026-08-02). An LLM-based hierarchical agent system performs the
same recursive decomposition, except the decomposition step is a model call
instead of a symbolic planner, and each leaf of the decomposition is an
agent with its own tools rather than a primitive planning operator.

This entry treats depth as the load-bearing distinction from the sibling
Orchestrator-Worker entry in this catalog. Orchestrator-Worker names the
single-level case, one coordinator, N workers, no worker is itself a
coordinator. Hierarchical Agents names the case where at least one worker is
also a supervisor of its own subordinates, so the delegation graph has depth
two or more. Anthropic's own production research system, cited repeatedly
through this entry for its unusually detailed public engineering account, is
in this strict sense an Orchestrator-Worker system, not a Hierarchical Agent
system, because its lead agent delegates directly to leaf subagents with no
intermediate team-lead layer. It is referenced here anyway because its
engineering lessons on cost, coordination and failure modes generalize
directly to the deeper case and because it is the single best-documented
multi-agent system in production as of this writing.

## 2. Problem and context

A single agent with a tool belt and a large context window handles a
surprising amount of real work, and the correct starting point for almost
any agentic system is exactly that single agent, per Anthropic's own
guidance discussed in dimension 3 below. Three things break this simple
shape as a task grows.

First, a task decomposes into subtasks that are themselves complex enough
to need their own tool selection, their own retries, and their own error
handling, and cramming all of that into one flat context makes the
top-level agent's prompt long, its state machine tangled, and its failures
hard to attribute to a cause. Second, the natural groupings of subtasks
correspond to distinct domains of expertise or distinct tool sets, for
example a research team that only ever touches search and scraping tools
and a writing team that only ever touches a document editor and a citation
checker, and mixing both domains' tool descriptions and instructions into
one flat worker roster degrades the coordinator's ability to route
correctly as the roster grows. Third, a flat coordinator managing more than
roughly six to ten direct workers starts to spend an increasing share of its
own context and reasoning on bookkeeping, tracking which worker returned
what, rather than on the actual decomposition and synthesis work it exists
to do.

The context in which Hierarchical Agents becomes the right answer, rather
than a premature complication, is a task whose natural decomposition is
itself two levels deep or more in the real world. A software company
building a product decomposes into a product management function, an
architecture function, and an engineering function, each of which further
decomposes into individual contributors. A research and writing pipeline
decomposes into a research phase with several parallel researchers and a
writing phase with several parallel section writers, and the research phase
and the writing phase have almost no tool overlap. A customer support system
decomposes into a routing layer, then a domain layer (billing, technical,
account), then within the technical domain a set of specialist workers for
different product areas. In each case the mid-level grouping is not an
artifact of the implementation, it mirrors how a human organization would
actually staff the same problem, and that mirroring is the strongest signal
that hierarchy earns its cost rather than merely adding it.

## 3. Forces

Anthropic states the governing force plainly for any agentic system before
multi-agent coordination is even on the table. "When building applications
with LLMs, we recommend finding the simplest solution possible, and only
increasing complexity when needed... you should consider adding complexity
only when it demonstrably improves outcomes." (Anthropic, "Building Effective
Agents,"
[anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents),
verified 2026-08-02). Every force below has to be weighed against that
baseline preference for the flattest system that still solves the problem.

Cost is the sharpest and most measurable force. Anthropic's own multi-agent
research system, a single-level orchestrator with parallel subagents,
measures its own overhead directly, reporting that a single agent uses
roughly four times the tokens of a plain chat interaction, and that
"multi-agent systems use about 15x more tokens than chats." (Anthropic,
"How we built our multi-agent research
system,"
[anthropic.com/engineering/multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system),
verified 2026-08-02). A hierarchical system with two or three delegation
levels compounds this further, because every level's summarization,
planning, and re-delegation step burns its own tokens on top of whatever the
level below it already spent, and a naive implementation that forwards full
transcripts up the tree rather than compact summaries multiplies cost with
depth rather than merely adding to it. The same article states the resulting
constraint on when the pattern is worth using at all. "For economic
viability, multi-agent systems require tasks where the value of the task is
high enough to pay for the increased performance."

Coordination complexity grows with the number of edges in the delegation
graph, not with the number of nodes, and a hierarchy trades a smaller number
of direct edges at any one level (a root talking to three team leads instead
of fifteen workers) for a larger total number of edges across the whole
tree and, critically, for indirection. The root no longer sees a leaf
worker's raw output, only whatever its team lead chose to summarize. This is
the central trade-off of the pattern. It buys the root a manageable span of
control at the cost of every intermediate layer becoming an added point of
risk for information loss, misrouting, or delay. Anthropic names the general shape
of this force even for the shallower single-level case they studied.
"Multi-agent systems have key differences from single-agent systems,
including a rapid growth in coordination complexity."

Latency is a force that pushes toward hierarchy rather than away from it,
which is unusual among the forces here. A flat coordinator processing fifteen
subtasks sequentially, or even with limited parallelism because it is a
single reasoning loop managing fifteen concurrent tool calls, is slower than
three team leads each running three or four workers in parallel and each
being invoked in parallel by the root, because the parallelism is now nested
rather than flat and the critical path through the tree is the depth of the
longest branch, not the total count of leaves.

Consistency and shared state pull hard against hierarchy. A flat worker pool
under one coordinator shares one source of truth, the coordinator's own
running state. A hierarchy has no such single source of truth by default,
each team lead's private sub-conversation is invisible to its siblings and,
depending on implementation, invisible to the root as well, which is exactly
the design Microsoft's AutoGen nested chats describes when it says nested
chats let an agent "use other agents as their inner monologue." Two team
leads pursuing overlapping subgoals with no visibility into each other's
work is a direct, structural consequence of the pattern, not a bug that
appears only under misuse.

Team topology and organizational fit is the force that most often decides
whether the pattern is appropriate independent of the purely computational
trade-offs above. Where the underlying business or technical process is
genuinely staffed, or would be staffed, as a small organizational chart,
mirroring that chart in the agent hierarchy keeps each level's prompt scoped
to a role a person could actually hold, which keeps prompts maintainable as
the system grows. Where the underlying process has no such natural chart,
forcing one onto it produces artificial team boundaries that fight the
actual shape of the work, and a flat pool or a single agent with more tools
almost always outperforms it.

## 4. Applicability and non-applicability

Reach for Hierarchical Agents when the task's natural decomposition is
itself two or more levels deep in the real world, meaning the mid-level
groupings correspond to genuinely distinct domains of expertise, distinct
tool sets, or distinct organizational functions that a human team would
staff separately. Reach for it when a flat coordinator's worker roster has
grown past roughly six to ten direct workers and the coordinator's own
prompt is spending a growing share of its length on routing logic rather
than on synthesis. Reach for it when different branches of the task have
wildly different latency or cost profiles and isolating them under separate
team leads lets each branch apply its own retry policy, its own model
choice, and its own budget cap without those choices leaking into
unrelated branches. Reach for it when the task is high enough value to
absorb the multiplicative token cost the pattern imposes at every level, a
condition Anthropic states as the economic viability threshold for
multi-agent systems generally.

Do not use Hierarchical Agents in the following situations, and the reason
in each case is load-bearing, not decorative.

- A single agent with tools already solves the task within an acceptable
  context budget. Adding any coordination layer, flat or hierarchical, adds
  the coordination-complexity and token-multiplication costs described in
  dimension 3 for zero benefit, and the correct first move per Anthropic's
  own guidance is to find the simplest solution and add complexity only
  when it demonstrably improves outcomes.
- The task is a short, low-value, high-frequency operation, for example
  answering a single factual question or formatting one document, where the
  fifteen-fold token multiplier a multi-agent system imposes cannot be
  justified by the task's value, per the economic viability threshold cited
  above.
- The task requires read-write access to a single shared piece of mutable
  state where two branches could race, for example two workers editing the
  same file concurrently. A hierarchy's structural information isolation
  between branches, the same property that gives it its scaling benefit,
  makes coordinating a shared mutable resource across branches strictly
  harder than in a flat system where one coordinator can serialize every
  write itself.
- The natural decomposition of the task is genuinely flat, meaning every
  subtask is roughly the same kind of work with no real grouping
  above it. Imposing an artificial mid-level grouping onto flat work adds a
  full extra layer of summarization and delegation overhead that returns
  nothing, and the flat Orchestrator-Worker pattern is strictly better here.
- Debuggability and auditability requirements are strict and the team
  cannot invest in full-depth tracing across every level of the tree.
  Anthropic's own team found that even their single-level system needed
  dedicated production tracing before failures were diagnosable at all,
  stating that "agents make dynamic decisions and are non-deterministic
  between runs, even with identical prompts," and that "adding full
  production tracing let us diagnose why agents failed and fix issues
  systematically." A two- or three-level hierarchy multiplies the number of
  decision points that need this tracing, and shipping the pattern without
  the observability investment described in dimension 16 is one of the more
  reliable ways to ship a system nobody can explain when it misbehaves.
- Real-time, low-latency interactive use cases where even the parallelism
  benefit of hierarchy cannot offset the summarization overhead each level
  adds before the first useful token reaches the user.

## 5. Structure

A Hierarchical Agent system has three distinct participant roles, and every
concrete node in the tree plays exactly one of them relative to its parent
and, for mid-level nodes, a second role relative to its children.

- **Root supervisor.** The single entry point for an external request. It
  owns the global task, decomposes it into a small number of branch goals,
  one per mid-level team, and routes each branch goal to the appropriate
  team lead. It owns the global resource cap, the total token or dollar
  budget for the whole request, and enforces that cap across every
  branch, not merely its own direct calls. It synthesizes the final answer
  from whatever summaries its team leads return, and it is the only node in
  the tree whose output the external caller ever sees directly.
- **Team lead (mid-level supervisor).** Every mid-level node is a
  Janus-faced participant. Facing upward, toward its own parent, it behaves
  exactly like a leaf worker, it accepts a branch goal, does work, and
  returns a bounded, well-formatted result. Facing downward, toward its own
  children, it behaves exactly like a root supervisor, it decomposes the
  branch goal further, owns a local resource cap scoped to its own
  subtree, dispatches subtasks to its workers (which may themselves be team
  leads one level further down), and synthesizes its children's results
  into the single result it reports upward. This dual role is why the
  pattern composes recursively, a team lead's implementation is the same
  code as a root supervisor's implementation, parameterized only by which
  goal it received and which cap it was given.
- **Worker (leaf agent).** The node at the bottom of any branch that does
  not further delegate. It holds the actual tool access for its narrow
  domain, search, code execution, a database client, a document editor, and
  it turns a well-scoped subtask directly into a concrete result without
  spawning further subordinates. A worker's prompt is the cheapest to write
  and the cheapest to test in the whole tree, because its scope is narrowest.

Two structural relationships hold across every level regardless of depth.
Delegation flows strictly downward, a parent decides what its children work
on and a child never independently decides to hand work to a peer or to a
node outside its own subtree. Reporting flows strictly upward and is
lossy by design, a parent receives a synthesized result from each child, not
that child's full internal transcript, which is the mechanism that keeps
the root supervisor's own context from growing with the size of the entire
tree rather than merely the number of its direct children. A resource
cap, whether expressed as a token budget, a wall-clock timeout, or a
dollar limit, is set once at the root and propagated downward, with each
parent free to subdivide its own cap across its children in whatever
proportion its own decomposition logic decides, but never free to exceed
the cap its own parent handed it.

## 6. ASCII structure diagram

```
+----------------------+
| Root Supervisor      |
| global goal + budget |
+----------------------+
     | delegates branch goals, propagates a
     | fraction of the global budget
     v
+-----------------------------+
| Team Lead A (research team) |
| local budget = 40%          |
+-----------------------------+
     | workers: search, scraper
     | bounded summary result flows up
     v
(Team Lead A's summary)

Root Supervisor also delegates to a second branch:

+----------------------------+
| Team Lead B (writing team) |
| local budget = 40%         |
+----------------------------+
     | workers: drafting, citation-check
     | bounded summary result flows up
     v
(Team Lead B's summary)

Team Lead A and Team Lead B each report one summary
upward to be synthesized.

+--------------------------+
| Root Supervisor          |
| synthesizes final answer |
+--------------------------+
```

## 7. Dynamics

The system starts when an external request reaches the root supervisor,
which reasons about the request and produces a small ordered or parallel
set of branch goals, one per mid-level team, along with a budget allocation
for each. This is itself a single model call, the same shape of call as how
Anthropic's flat orchestrator plans a research task, "the lead agent
analyzes it, develops a strategy, and spawns subagents to explore different
aspects simultaneously" (Anthropic, multi-agent research system post cited
above), except the entities it spawns here are team leads rather than leaf
workers.

Each team lead receives exactly one branch goal and its own budget, and from
this point forward that team lead behaves as its own independent root for
its own subtree, running the identical decompose-dispatch-collect-synthesize
loop one level down, dispatching to its own workers, some of which may in a
deeper hierarchy be further team leads rather than leaves. Every node at the
leaf level actually executes. It calls a tool, reads a result, and either
returns immediately or performs a further bounded reasoning step before
returning. A worker never dispatches to a peer, and a worker's context is
scoped strictly to the subtask its own parent gave it, it has no visibility
into what any sibling worker is doing, which is both the isolation property
that lets siblings run safely in parallel and the coordination gap that
causes the duplicate-work failure mode discussed in dimension 11.

As results return up each branch, the returning node compresses its own
result before handing it to its parent. A worker compresses its raw tool
output into a short, structured finding. A team lead compresses its own
children's structured findings, plus whatever additional reasoning it did
to reconcile or deduplicate them, into a single branch-level summary. This
compression step happening at every level, rather than only once at the
root, is what keeps token cost from growing with the total size of the
tree, at the cost of information being lost or flattened at every hop, an
explicit trade named in dimension 3.

Failure handling follows the same recursive shape as normal execution. If a
worker fails or times out, its parent team lead decides locally whether to
retry the worker, reassign the subtask to a different worker, or absorb the
gap and report a partial branch result upward with the gap noted. If an
entire branch, meaning a whole team lead's subtree, fails or exceeds its own
budget cap, the failure or partial result propagates to the root the
same way a normal result would, and the root decides whether the overall
task can still be answered from the branches that did succeed or whether the
whole request fails. Anthropic's account of this class of problem in even
their flat system is direct. "Agents can run for long periods of time,
maintaining state across many tool calls... Without effective mitigations,
minor system failures can be catastrophic for agents," which is exactly why
every level's failure-handling logic needs to bound how far a single leaf
failure can propagate rather than letting it silently corrupt or stall the
entire tree.

```text
Request  Root                TeamLead-A            TeamLead-B
  |       |                    |                       |
  |------>| decompose(goal)    |                       |
  |       |------------------->| branch_goal_A, budget  |
  |       |-------------------------------------------->| branch_goal_B, budget
  |       |                    | decompose(branch_A)    |
  |       |                    |----> Worker A1         |
  |       |                    |----> Worker A2         |
  |       |                    |<---- result A1         |
  |       |                    |<---- result A2         |
  |       |                    | synthesize             |
  |       |<-------------------| summary_A               |
  |       |                                             | decompose(branch_B)
  |       |                                             |----> Worker B1
  |       |                                             |<---- result B1
  |       |                                             | synthesize
  |       |<--------------------------------------------| summary_B
  |       | synthesize(summary_A, summary_B)             |
  |<------| final_answer                                 |
```

## 8. Implementation variants

The graph-of-graphs variant, exemplified by LangGraph's own architecture,
composes hierarchy by literal nesting. Each team lead is implemented as a
complete, independently runnable agent graph, and the root supervisor's
graph simply calls that complete subgraph as one of its own nodes. The
mechanism generalizes cleanly to arbitrary depth because a graph node that
happens to itself be an entire graph is not a special case in the framework,
it is another callable like any other node. This is the variant used in the LangChain
Hierarchical Agent Teams tutorial cited in dimension 1.

The nested-conversation variant, exemplified by Microsoft's AutoGen, embeds
the hierarchy inside a single agent's message-handling logic rather than in
a separate graph structure. The mid-level agent, upon receiving a message,
internally spins up and runs an entire private chat with its own team of
subordinate agents, and only once that private chat concludes does the
mid-level agent produce the single reply its own parent conversation sees.
The framework's own description of this, "nested chats allow AutoGen agents
to use other agents as their inner monologue to accomplish tasks," captures
the defining property of this variant well, the entire subtree's activity is
genuinely invisible to the level above unless the mid-level agent chooses to
surface it.

The declarative-role variant, exemplified by MetaGPT, fixes the hierarchy
and the roles in advance rather than deriving them dynamically from the
task. MetaGPT's roles map directly onto a software company's organizational
chart, a Product Manager role, an Architect role, a Project Manager role,
and Engineer roles, connected by Standardized Operating Procedures encoded
directly into the prompt sequence each role follows. "MetaGPT encodes
Standardized Operating Procedures into prompt sequences" and assigns each of
its several agent roles a fixed position in a production-line style division
of labor, one role handing its output to the next. (Hong, Zhuge, Chen, Zheng, Cheng, Zhang, Wang, Wang, Yau,
Lin, Zhou, Ran, Xiao, Wu, Schmidhuber, "MetaGPT. Meta Programming for a
Multi-Agent Collaborative Framework,"
[arxiv.org/abs/2308.00352](https://arxiv.org/abs/2308.00352), verified
2026-08-02). This variant trades the flexibility of a dynamically decomposed
tree for the predictability and testability of a fixed one, every run has
the same shape, only the content flowing through it differs.

The managed-service variant, exemplified by Amazon Bedrock's supervisor and
collaborator agent construct, moves the plumbing of budget propagation,
routing, and result aggregation out of application code and into a
platform-managed configuration. "You can quickly designate an Amazon Bedrock
Agent as the supervisor and then associate one or more collaborator agents
with the supervisor. You can use this hierarchical collaboration model to
synchronously respond to prompts and queries from users in real-time." (AWS
documentation cited in dimension 1). The role and responsibility of each
agent is described in natural language rather than in code, and AWS
explicitly recommends minimizing overlapping responsibilities across
collaborators, a direct platform-level acknowledgment of the duplicate-work
failure mode discussed in dimension 11.

A cross-cutting implementation choice, orthogonal to all four variants
above, is how much of a child's raw output a parent forwards versus
summarizes before passing it further up. A parent that forwards raw
transcripts preserves fidelity but multiplies token cost with tree depth,
because every level above re-reads everything every level below produced. A
parent that aggressively summarizes bounds cost but risks losing the exact
detail a much higher level actually needed, a trade-off with no universal
correct answer, resolved per-application by how much the root supervisor
genuinely needs to see versus merely needs to know happened.

## 9. Known production uses

Amazon Bedrock Agents' multi-agent collaboration feature is a managed cloud
service that implements the supervisor-and-collaborator structure described
above under its own explicit name, "hierarchical collaboration model." AWS
documents a concrete example of an online mortgage assistant staffed with a
routing supervisor and three collaborator agents for existing mortgages, new
mortgages, and general questions, describing this as a team that grows by
adding further collaborator agents as new capabilities are needed. (AWS,
[docs.aws.amazon.com/bedrock/latest/userguide/agents-multi-agent-collaboration.html](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-multi-agent-collaboration.html),
verified 2026-08-02). The same page notes this specific service, Bedrock
Agents Classic, is closed to new customers and directs new work toward
Amazon Bedrock AgentCore, a caution worth carrying into any decision to
build on this exact managed offering today rather than a caution about the
pattern itself.

MetaGPT is an open-source multi-agent framework, published at ICLR 2024,
that hard-codes a software-company hierarchy of roles, Product Manager,
Architect, Project Manager, and Engineer, each following its own
Standardized Operating Procedure, to turn a one-line requirement into a
working codebase with design documents, API specifications, and tests
generated at each layer of the hierarchy before the layer beneath it begins
work. The paper's own framing of the mechanism, "encodes Standardized
Operating Procedures into prompt sequences," and its fixed division of
labor across named roles, documents the pattern operating in a public,
reproducible, peer-reviewed system (Hong et al., cited in dimension 8
above).

Microsoft's AutoGen framework ships nested chats as a first-class primitive
in its public API, letting any developer wrap a private, multi-agent inner
conversation behind a single outward-facing agent, which is precisely the
team-lead role described in dimension 5. The framework's own documentation
states plainly that this lets "AutoGen agents use other agents as their
inner monologue to accomplish tasks," and the feature ships in the general
release of the framework rather than as an experimental extension
(Microsoft, cited in dimension 1 above).

LangGraph, LangChain's agent-orchestration library, ships the graph-of-graphs
variant described in dimension 8 as a documented, reference-implemented
pattern, building a two-team research-and-writing assistant in which a
top-level supervisor coordinates a research team and a writing team, each
with its own internal team-level supervisor and its own worker agents. The
tutorial itself states the exact condition under which the pattern is worth
reaching for over the single-level Agent Supervisor pattern it names as its
own prerequisite reading, quoted in full in dimension 1 (LangChain,
"Hierarchical Agent Teams," cited in dimension 1 above, archived but
resolvable, its content now folded into LangChain's consolidated
documentation).

Claude Code, Anthropic's own coding agent product, exposes both a flat
subagent facility and a distinct, deeper facility it calls agent teams for
sessions that need to communicate with each other, alongside a further
distinct facility for many independent background sessions monitored from
one place. Its own documentation describes the base subagent mechanism in
terms directly relevant to why any level of a hierarchy isolates context at
all. "Each subagent runs in its own context window with a custom system
prompt, specific tool access, and independent permissions... use one when a
side task would flood your main conversation with search results, logs, or
file contents you won't reference again." (Anthropic, "Create custom
subagents,"
[code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents),
verified 2026-08-02). This entry cites the product's own subagent facility
for its treatment of context isolation, the property every level of a
hierarchy relies on, while noting that a genuine multi-level hierarchy
within this specific product is the separate agent-teams facility rather
than the base subagent mechanism.

## 10. Consequences

The positive consequences of the pattern are concentrated where the forces
in dimension 3 favor it. It bounds the span of control at every level of
the tree to a small, human-comprehensible number of direct reports, which
keeps any single prompt, whether the root's or a team lead's, focused on a
decomposition problem of manageable size rather than growing linearly with
the total worker count of the whole system. It confines a failing branch's
blast radius to that branch's own subtree by default, because a team lead's
budget cap and error handling only govern its own children, so a
misbehaving worker under Team Lead A cannot silently consume Team Lead B's
budget or corrupt Team Lead B's state. It enables genuine nested parallelism,
every team lead's workers can run concurrently with each other, and every
team lead itself can be invoked concurrently with its sibling team leads by
the root, which is strictly more parallelism than a flat coordinator
managing the same total leaf count sequentially or with a single flat pool
of concurrent calls can achieve once coordination overhead is counted. It
maps cleanly onto organizational structures that already exist for the
underlying business process, which keeps individual prompts aligned with a
role a domain expert could review and correct without needing to understand
the whole tree.

The negative consequences are equally concentrated and are the direct
mirror image of the benefits above. Cost multiplies with depth because
every level performs its own planning, dispatch, and synthesis step on top
of whatever the levels below it already spent, compounding the fifteen-fold
overhead Anthropic measured even for a single-level system. Information is
lost by design at every hop, because a parent only ever sees a compressed
summary of what a child actually did, and if a child compresses away a
detail a much higher level genuinely needed, there is no path for that
higher level to recover it short of re-running the branch. Debugging
difficulty grows multiplicatively with tree depth rather than additively,
because a wrong final answer could originate at any leaf, be correctly
reported and then mis-synthesized by its team lead, or be correctly
synthesized by every level and still mis-synthesized by the root, and
distinguishing these cases requires tracing across every level rather than
only the one nearest the observed symptom. Latency at the tail is bounded by the
single slowest full branch through the tree, so one team lead whose own
workers run slowly, or which itself further delegates to a deep subtree,
sets the fastest the whole system can possibly respond, regardless of how
fast every other branch finished.

## 11. Failure modes and misuse

Symptom. Two branches of the tree independently produce the same
finding, or the final synthesized answer repeats the same fact under two
different phrasings.
Cause. Sibling workers and sibling team leads have no visibility into
each other's activity by design, so when a task's decomposition has
overlapping scope, for example two research subtasks that both plausibly
lead to the same source, nothing in the architecture prevents both branches
from independently discovering and reporting it. Anthropic's own account of
this exact failure in their flat system generalizes directly. "Subagents
misinterpreted the task or performed the exact same searches as other
agents," and more broadly, "subagents duplicate work, leave gaps, or fail to
find necessary information."
Fix. Write branch goals that are mutually exclusive in scope wherever
possible, have each parent's synthesis step explicitly deduplicate before
reporting upward rather than merely concatenating children's outputs, and
where genuine overlap is unavoidable, assign one branch the tie-breaking
authority over the shared area rather than letting both branches report
independently.

Symptom. The system takes far longer, or costs far more, than a flat
version of the same task would, and the extra time is not obviously spent on
useful work.
Cause. Every level of the tree performs its own full decompose-plan
step even when the branch goal it received was already narrow enough not to
need further decomposition, so a hierarchy applied to a task that is
secretly flat pays the coordination tax at every level for zero additional
benefit.
Fix. Before building a mid-level layer, confirm the decomposition
genuinely needs two independent grouping decisions, not one. If a single
flat decomposition already produces a manageable worker count, per
dimension 4, use Orchestrator-Worker instead and remove the mid-level layer
entirely, per the refactor described in dimension 14.

Symptom. A worker several levels deep fails or hangs, and the whole
request either fails outright with no explanation the user can act on, or
appears to hang indefinitely with no partial answer ever returned.
Cause. Failure handling was implemented only at the root, or only at
one level, rather than at every level independently, so a leaf failure has
no local containment and propagates unbounded until it reaches whichever
level does have handling, if any does. Anthropic's framing of the
underlying risk applies at every level of a hierarchy, well beyond the
single level they studied directly. "Agents can run for long periods of time,
maintaining state across many tool calls... without effective mitigations,
minor system failures can be catastrophic for agents."
Fix. Give every level, not only the root, its own timeout, its own
retry policy for its direct children, and its own explicit rule for what to
report upward when a child fails, whether that is a partial result with the
gap flagged, a retry with a different child, or an escalation that lets the
level above decide.

Symptom. A team lead's final summary omits a detail that turns out to
matter, and by the time this is discovered, re-deriving it requires
re-running the whole branch from scratch.
Cause. Compression at each level is lossy by construction, per dimension
7, and the compression logic was tuned only for average-case brevity rather
than for preserving whatever a much higher level might specifically need,
which nothing at the compressing level can know in advance.
Fix. Persist each level's full uncompressed output to durable storage
even though only the compressed summary is forwarded up the tree in the
live request path, so a human or a higher-level agent can retrieve the
original detail on demand without re-running the branch, and design the
summary format to include explicit pointers into that stored detail rather
than only prose.

Symptom. The system behaves unpredictably from run to run on what looks
like the same input, and engineers cannot reproduce a reported failure.
Cause. Every level of the tree is an independent, non-deterministic
model call, so the total number of independent points of variation across
a multi-level tree is the product, not the sum, of the variation at each
level, and Anthropic notes this holds even for their much shallower system.
"Agents make dynamic decisions and are non-deterministic between runs, even
with identical prompts," and without instrumentation, "users would report
agents 'not finding obvious information,' but we couldn't see why."
Fix. Instrument every level, not only the entry point, with full
production tracing that records each node's inputs, tool calls, and outputs,
per dimension 16, before the system reaches production, because retrofitting
tracing after a failure has already been reported has no way to explain a
run that already happened and was not captured.

Symptom. A mid-level team lead's own subtree keeps growing another level
deeper as engineers keep adding specialization, until the tree is five or
six levels deep and nobody can hold the whole shape in their head.
Cause. There is no natural stopping point forcing hierarchy depth to
match the actual organizational or domain structure of the task, so each
individual addition of one more level looks locally reasonable while the
aggregate result drifts arbitrarily far from what the task actually needs,
directly contradicting the simplest-solution-first principle from dimension
3.
Fix. Set an explicit maximum depth as a design constraint before
building, derived from the real organizational chart the system mirrors,
and treat any proposal to add a level beyond that maximum as a signal that
the task's decomposition, not the architecture, needs re-examining.

## 12. Trade-off matrix

| Force | Hierarchical Agents (this pattern) | Orchestrator-Worker (flat, single level) | Blackboard (shared workspace, no fixed delegation graph) |
|---|---|---|---|
| Span of control per node | Small and bounded at every level regardless of total system size | Bounded at the coordinator only, grows unbounded as workers are added | Not applicable, no fixed coordinator, any agent may read or write the shared space |
| Token and dollar cost | Highest, compounds with tree depth on top of the flat overhead | High, roughly fifteen times a plain chat interaction per Anthropic's measurement | Variable, depends on how many agents poll or react to each blackboard change |
| Debuggability | Hardest, failure could originate or be mis-synthesized at any of several levels | Moderate, only two levels to trace, coordinator and worker | Hard in a different way, no fixed call graph to trace, only a shared state history |
| Parallelism achievable | Highest, nested parallelism across both branches and each branch's own workers | Good, parallel workers under one coordinator | Good, any number of agents can act concurrently on the shared space |
| Fit for organizationally deep tasks | Best fit, mirrors a real multi-level team directly | Poor fit if the real process has genuine sub-teams, forces them flat | Poor fit, blackboard has no concept of team boundaries at all |
| Fit for genuinely flat tasks | Poor fit, imposes an unneeded layer and its full cost | Best fit | Overkill unless agents also need opportunistic, non-hierarchical collaboration |
| Coordination model | Strict, delegation down and reporting up only | Strict, coordinator to worker and back only | Loose, any agent can act on any relevant blackboard entry from any other agent |

## 13. Related and incompatible patterns

Orchestrator-Worker is the direct ancestor and the pattern this entry
generalizes. Every Hierarchical Agent tree is, at each individual level,
literally an instance of Orchestrator-Worker, and the two patterns are best
understood as one recursive definition rather than as fully separate
patterns, the sole difference being whether any worker is itself a
coordinator. A team choosing between them should default to
Orchestrator-Worker and only add a level, converting one worker into a team
lead, once dimension 4's applicability conditions are actually met at that
specific point in the tree.

Sub-Agent Isolation is the mechanism, not the shape, that makes hierarchy
safe at any depth. Every level's ability to run its children concurrently
without their contexts interfering depends on each child having its own
isolated context window, tool access, and permission set, exactly the
property Claude Code's own subagent documentation describes as the reason
subagents exist at all. A hierarchy without this isolation at every level
degrades into a single enormous shared context with extra bookkeeping,
losing the pattern's entire benefit while keeping all of its cost.

Blackboard is a genuine architectural alternative for the same underlying
problem, coordinating many specialized agents toward one goal, but it
solves it with the opposite topology. Instead of a fixed delegation tree, a
Blackboard system gives every agent read and write access to one shared
workspace and lets each agent act opportunistically whenever it sees a
change relevant to its own specialty. The two patterns are largely
incompatible as a direct substitution within one branch, because a
Blackboard's value comes from removing the fixed delegation structure that
a hierarchy's value comes from imposing, though a system can legitimately
use a hierarchy for one part of its workflow and a Blackboard for another.

Chain of Responsibility and Composite from the classical object-oriented
catalog are the structural, non-agentic ancestors worth naming for a reader
coming from that background. Composite's recursive part-whole structure,
where a composite node's children may themselves be composites, is
the same recursive shape as how a team lead is simultaneously a worker and a
supervisor in this pattern, the LLM-agentic form simply replaces a fixed
method call with a model-driven decomposition decision at every node.

Evaluator-Optimizer composes naturally as a refinement loop inserted at any
single level of a hierarchy, most commonly at a team lead reviewing its own
children's aggregated output before passing a synthesis upward, without
requiring any change to the levels above or below that team lead.

Mediator is worth distinguishing precisely because it is often confused
with the supervisor role at any one level of a hierarchy. A Mediator
coordinates communication among a fixed, flat set of peer objects that
would otherwise reference each other directly, and it does not itself
further decompose the task or dispatch to sub-mediators. A team lead in a
Hierarchical Agent system does decompose and does dispatch, and the
authority relationship is asymmetric (parent to child) rather than the
peer-to-peer relationship a Mediator manages.

## 14. Refactoring path in and out

Introducing hierarchy into a system that started as a single flat
Orchestrator-Worker is a narrow, mechanical refactor once the trigger
condition from dimension 4 is actually observed, usually a coordinator
prompt whose worker roster or routing logic has grown noticeably long or
error-prone. Group the existing flat worker list by the natural domain each
worker already belongs to, without changing any worker's own implementation
yet. For each group with more than one worker, introduce a new team-lead
node whose only job, at first, is to receive the group's share of the
original coordinator's work and forward each subtask to exactly the workers
that group already had, unchanged, then pass their results back up largely
unmodified. Only after this pass-through team lead is running correctly
should its own decomposition and synthesis logic be built out to add real
value, for example deduplication across its own workers or its own retry
policy, rather than merely forwarding. Finally, update the original flat
coordinator, now the root, to route to the new team leads instead of to
individual workers directly, and reduce its own prompt accordingly, since
routing logic for a handful of team leads is substantially shorter than
routing logic for every individual worker across every domain.

Removing hierarchy that has stopped earning its place, the corrective move
for the depth-creep failure mode in dimension 11, follows the reverse steps
and is worth doing decisively rather than partially, since a half-flattened
tree combines the cost of both shapes. Identify any team lead whose own
decomposition has degenerated into forwarding every subtask to a single
worker, or whose branch never actually runs in parallel with any sibling
branch in practice, both signals that the level is adding process without
adding value. Inline that team lead's remaining useful logic, usually a
small amount of formatting or validation, directly into its parent's
synthesis step, and reattach its former direct workers to the parent as
direct workers of the parent instead. Repeat this collapsing at every level
where it applies, remeasure the resulting system's token cost and latency
against the pre-collapse baseline, and only stop collapsing once further
removal would genuinely reintroduce the coordination-complexity or
information-loss failure the original hierarchy existed to solve.

## 15. Testing and verification

Test every worker in complete isolation first, exactly as a flat
Orchestrator-Worker system would be tested, because a worker's contract, a
well-specified subtask in, a well-structured finding out, does not change
when that worker happens to sit under a team lead rather than directly
under a root. Mock the worker's own tool calls and assert on the shape and
correctness of its returned finding, independent of anything above it in
the tree.

Test each team lead's decomposition and synthesis logic against a fixed,
scripted set of worker responses, injected through mocked children rather
than real ones, so the team lead's own logic, how it splits a branch goal,
how it handles a child that returns an error, how it deduplicates or
reconciles overlapping children's findings, can be verified deterministically
without the non-determinism of an actual model call at the worker level
contaminating the assertion. This isolates exactly the coordination logic
that dimension 11's failure modes live in, separately from the leaf-level
correctness dimension 15's first paragraph already covers.

Test the whole tree's shape with a small number of true full-tree runs
against representative real inputs, primarily to catch integration failures
the two isolated test layers above cannot see by construction. A budget
cap that a parent forgets to actually propagate to a child, a message
format one level expects that the level below does not actually produce, or
a genuinely emergent duplicate-work case that only appears once real,
non-scripted model outputs from two different branches happen to converge
on the same finding. Keep this layer small relative to the isolated-layer
tests above it, because a full run through a multi-level
hierarchy is exactly the slow, expensive, non-deterministic test a team
cannot afford to run on every change, per the cost economics in dimension 3.

Test the budget-propagation logic specifically and separately from
functional correctness, using a fault-injection technique. Force a
mid-level team lead's children to consume its entire allocated budget
before finishing their work, and assert that the team lead correctly
truncates, reports a partial result, and does not silently exceed the
cap its own parent gave it. This category of test is the one most
catalogs of agentic patterns omit entirely, and it is exactly the test that
would have caught the budget-cap class of bug the deterministic code
example in dimension 8's TypeScript and Python listings both defend against
explicitly.

## 16. Observability signals

At the root level, log the full branch-goal decomposition the root
produced for every request, the budget allocation across branches, and the
final synthesized answer alongside every branch summary that fed it, so a
reviewer can reconstruct exactly what the root saw and why it produced the
answer it did without needing to separately query every lower level.

At every mid-level team lead, log its own received branch goal and budget,
its own decomposition into subtasks for its children, each child's raw
returned result before compression, and the compressed summary it actually
forwarded upward, explicitly logged as two separate artifacts rather than
only the final compressed form, because dimension 11's information-loss
failure mode is otherwise invisible after the fact, with no way to tell
whether a missing detail was ever produced by a child and merely dropped in
compression, or never produced at all.

At every worker, log the exact subtask it received, every tool call it
made with that tool's raw response, and its final returned finding, mapped
by a single trace identifier that threads through every level of the tree
for a given request, matching the concrete recommendation from Anthropic's
own account. "Adding full production tracing let us diagnose why agents
failed and fix issues systematically." Without this shared trace identifier
propagated to every node regardless of depth, a failure investigation
degenerates into manually correlating timestamps across log files from
different levels, which does not reliably work once two branches are
actually running concurrently.

A healthy tree, viewed on a dashboard aggregating these signals across many
requests, shows total token cost per request scaling with task complexity
rather than being flat or unpredictable, branch latencies for sibling
branches roughly balanced rather than one branch consistently the
longest share of total request time, and a low, stable rate of budget-cap truncations. A
failing tree shows the inverse of each of these. Cost spiking on requests
that should be routine, one branch consistently the tail-latency bottleneck
across many requests, which points at a specific mid-level node worth
investigating directly, or a rising rate of budget truncations, which
signals either that the caps were set too tight for the real workload or
that dimension 11's depth-creep or duplicate-work failure modes are
consuming budget on unproductive work.

## 17. Security and privacy implications

Each level of a hierarchy is a genuine trust boundary and should be treated
as one deliberately, not as an implementation detail. A worker whose only
job is to search public documentation has no legitimate reason to hold
credentials or tool access scoped to, for example, sending email or writing
to a production database, and Claude Code's own subagent facility is built
explicitly around this principle, giving each subagent "specific tool
access, and independent permissions" distinct from its parent's own tool
access, a design choice worth carrying into every level of a hierarchy, not
merely into the leaf level.

Prompt injection risk compounds with tree depth in a direction that is easy
to overlook. A malicious instruction embedded in content a leaf worker
retrieves, for example inside a scraped web page, does not need to fool the
leaf worker's own model call directly to do damage, it only needs to survive
being summarized upward through however many team-lead compression steps
sit between that leaf and the root before it reaches a level with broader
tool access or broader authority. A team lead's compression step is
therefore a genuine security control, not merely a cost optimization, and
compression logic that faithfully preserves an untrusted instruction's
imperative phrasing while dropping its surrounding context is a real,
concrete way this pattern's own cost-saving mechanism becomes an attack
vector rather than a mitigation.

Data residency and cross-branch data leakage are a direct consequence of
this entry's own claimed benefit, information isolation between branches.
A system handling data with different sensitivity levels across different
branches, for example a customer-facing branch and an internal-operations
branch under the same root, should confirm that a shared root supervisor
does not itself become an unintended aggregation point that combines
sensitivity levels a compliance boundary intended to keep separate, since
the root sees a summary from every branch by construction even though no
single branch sees any other branch's data directly.

Where this entry is silent, it makes no claim about any specific
authentication or authorization protocol between levels, because that
choice depends entirely on the underlying platform (a managed service like
Bedrock's IAM-scoped collaborator agents, or a self-hosted framework where
the application itself must implement per-level access control), and no
single answer generalizes across the implementation variants in dimension
8.

## 18. References

- Erol, Hendler, Nau, "HTN Planning. Complexity and Expressivity," AAAI 1994,
  pages 1123 to 1128,
  [dblp.org/rec/conf/aaai/ErolHN94](https://dblp.org/rec/conf/aaai/ErolHN94),
  verified 2026-08-02.
- Wu, Bansal, Zhang, Wu, Li, Zhu, Jiang, Zhang, Zhang, Liu, Awadallah, White,
  Burger, Wang, "AutoGen. Enabling Next-Gen LLM Applications via Multi-Agent
  Conversation," 2023, [arxiv.org/abs/2308.08155](https://arxiv.org/abs/2308.08155),
  verified 2026-08-02.
- Hong, Zhuge, Chen, Zheng, Cheng, Zhang, Wang, Wang, Yau, Lin, Zhou, Ran,
  Xiao, Wu, Schmidhuber, "MetaGPT. Meta Programming for a Multi-Agent
  Collaborative Framework," ICLR 2024,
  [arxiv.org/abs/2308.00352](https://arxiv.org/abs/2308.00352), verified
  2026-08-02.
- Anthropic, "Building Effective Agents,"
  [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents),
  verified 2026-08-02.
- Anthropic, "How we built our multi-agent research system,"
  [anthropic.com/engineering/multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system),
  verified 2026-08-02.
- Anthropic, "Create custom subagents,"
  [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents),
  verified 2026-08-02.
- AWS, "Use multi-agent collaboration with Amazon Bedrock Agents,"
  [docs.aws.amazon.com/bedrock/latest/userguide/agents-multi-agent-collaboration.html](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-multi-agent-collaboration.html),
  verified 2026-08-02.
- Microsoft, AutoGen 0.2 documentation, "Nested Chats,"
  [microsoft.github.io/autogen/0.2/docs/notebooks/agentchat_nestedchat/](https://microsoft.github.io/autogen/0.2/docs/notebooks/agentchat_nestedchat/),
  verified 2026-08-02.
- LangChain, "Hierarchical Agent Teams" tutorial notebook, archived commit,
  [github.com/langchain-ai/langgraph/blob/23961cff61a42b52525f3b20b4094d8d2fba1744/docs/docs/tutorials/multi_agent/hierarchical_agent_teams.ipynb](https://github.com/langchain-ai/langgraph/blob/23961cff61a42b52525f3b20b4094d8d2fba1744/docs/docs/tutorials/multi_agent/hierarchical_agent_teams.ipynb),
  verified 2026-08-02, content since moved to LangChain's consolidated
  documentation.

## Code examples

Working code in three languages, Python, TypeScript, and Go. Each example
implements the identical structure, a Root Supervisor with two Team Leads,
each Team Lead owning two Workers, and each level enforcing its own local
token-budget cap independent of the levels above and below it, the exact
mechanism dimension 15 recommends fault-injection testing against. Java,
Rust, and Swift are omitted because the pattern's defining property, a
node's dual role as both a worker and a supervisor depending on which
direction it faces in the tree, is expressed identically as ordinary
recursive object composition in every general-purpose language, and a
fourth or fifth translation of the same composition adds no additional
insight into the pattern itself. All three examples below were compiled or
run directly against the toolchain on the authoring machine.

Python 3, run with `python3 hierarchical_agents.py`.

```python
"""Three-level hierarchical agents: Root Supervisor -> Team Leads -> Workers.
Deterministic handlers stand in for model calls so this runs offline."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable


@dataclass
class TaskResult:
    worker: str
    output: str
    tokens_used: int


@dataclass
class Worker:
    name: str
    skill: str
    handler: Callable[[str], str]

    def run(self, subtask: str) -> TaskResult:
        output = self.handler(subtask)
        return TaskResult(self.name, output, len(subtask.split()) * 12)


@dataclass
class TeamLead:
    # Owns a fixed pool of workers and a token cap for its own subtree.
    name: str
    workers: list[Worker]
    token_ceiling: int = 20000

    def decompose(self, goal: str) -> list[tuple[Worker, str]]:
        return [(w, f"{goal} :: focus={w.skill}") for w in self.workers]

    def execute(self, goal: str) -> tuple[str, int]:
        assignments = self.decompose(goal)
        results: list[TaskResult] = []
        spent = 0
        for worker, subtask in assignments:
            if spent >= self.token_ceiling:
                break
            result = worker.run(subtask)
            spent += result.tokens_used
            results.append(result)
        summary = " | ".join(f"{r.worker}: {r.output}" for r in results)
        return f"[{self.name}] {summary}", spent


@dataclass
class RootSupervisor:
    leads: list[TeamLead]
    global_ceiling: int = 100000

    def route(self, goal: str) -> str:
        # Real systems use a model call to pick a subset of leads.
        return goal

    def run(self, goal: str) -> str:
        total_spent = 0
        outputs = []
        for lead in self.leads:
            if total_spent >= self.global_ceiling:
                outputs.append(f"[root] budget exhausted, {lead.name} skipped")
                continue
            summary, spent = lead.execute(self.route(goal))
            total_spent += spent
            outputs.append(summary)
        outputs.append(f"[root] total_tokens={total_spent}")
        return "\n".join(outputs)


def make_research_hierarchy() -> RootSupervisor:
    market_lead = TeamLead(
        "market-lead",
        [
            Worker("competitor-scan", "competitors", lambda t: f"found 5 rivals for '{t}'"),
            Worker("pricing-scan", "pricing", lambda t: f"median price band for '{t}'"),
        ],
    )
    tech_lead = TeamLead(
        "tech-lead",
        [
            Worker("codebase-scan", "architecture", lambda t: f"3 services touch '{t}'"),
            Worker("dependency-scan", "dependencies", lambda t: f"2 stale deps near '{t}'"),
        ],
    )
    return RootSupervisor([market_lead, tech_lead])


if __name__ == "__main__":
    supervisor = make_research_hierarchy()
    print(supervisor.run("checkout-flow redesign"))
```

Compiled and run directly. Output.

```text
[market-lead] competitor-scan: found 5 rivals for 'checkout-flow redesign :: focus=competitors' | pricing-scan: median price band for 'checkout-flow redesign :: focus=pricing'
[tech-lead] codebase-scan: 3 services touch 'checkout-flow redesign :: focus=architecture' | dependency-scan: 2 stale deps near 'checkout-flow redesign :: focus=dependencies'
[root] total_tokens=192
```

TypeScript, compiled with `tsc` targeting es2020 and run with `node`.

```typescript
type Handler = (subtask: string) => string;

interface TaskResult {
  worker: string;
  output: string;
  tokensUsed: number;
}

class AgentWorker {
  constructor(
    public readonly name: string,
    public readonly skill: string,
    private readonly handler: Handler,
  ) {}

  run(subtask: string): TaskResult {
    const output = this.handler(subtask);
    return { worker: this.name, output, tokensUsed: subtask.split(" ").length * 12 };
  }
}

class TeamLead {
  constructor(
    public readonly name: string,
    private readonly workers: AgentWorker[],
    private readonly tokenCeiling: number = 20_000,
  ) {}

  private decompose(goal: string): Array<[AgentWorker, string]> {
    return this.workers.map((w) => [w, `${goal} :: focus=${w.skill}`]);
  }

  execute(goal: string): { summary: string; spent: number } {
    let spent = 0;
    const results: TaskResult[] = [];
    for (const [worker, subtask] of this.decompose(goal)) {
      if (spent >= this.tokenCeiling) break;
      const result = worker.run(subtask);
      spent += result.tokensUsed;
      results.push(result);
    }
    const summary = results.map((r) => `${r.worker}: ${r.output}`).join(" | ");
    return { summary: `[${this.name}] ${summary}`, spent };
  }
}

class RootSupervisor {
  constructor(
    private readonly leads: TeamLead[],
    private readonly globalCeiling: number = 100_000,
  ) {}

  run(goal: string): string {
    let totalSpent = 0;
    const lines: string[] = [];
    for (const lead of this.leads) {
      if (totalSpent >= this.globalCeiling) {
        lines.push(`[root] budget exhausted, ${lead.name} skipped`);
        continue;
      }
      const { summary, spent } = lead.execute(goal);
      totalSpent += spent;
      lines.push(summary);
    }
    lines.push(`[root] total_tokens=${totalSpent}`);
    return lines.join("\n");
  }
}

function makeResearchHierarchy(): RootSupervisor {
  const marketLead = new TeamLead("market-lead", [
    new AgentWorker("competitor-scan", "competitors", (t) => `found 5 rivals for '${t}'`),
    new AgentWorker("pricing-scan", "pricing", (t) => `median price band for '${t}'`),
  ]);
  const techLead = new TeamLead("tech-lead", [
    new AgentWorker("codebase-scan", "architecture", (t) => `3 services touch '${t}'`),
    new AgentWorker("dependency-scan", "dependencies", (t) => `2 stale deps near '${t}'`),
  ]);
  return new RootSupervisor([marketLead, techLead]);
}

const supervisor = makeResearchHierarchy();
console.log(supervisor.run("checkout-flow redesign"));
```

Compiled with `tsc --target es2020 --lib es2020,dom` and run with `node`,
zero type errors, output identical in shape to the Python listing above.

Go, run with `go run hierarchical_agents.go`.

```go
package main

import (
	"fmt"
	"strings"
	"sync"
)

type Handler func(subtask string) string

type Worker struct {
	Name    string
	Skill   string
	Handler Handler
}

type TaskResult struct {
	Worker string
	Output string
	Tokens int
}

func (w Worker) Run(subtask string) TaskResult {
	output := w.Handler(subtask)
	tokens := len(strings.Fields(subtask)) * 12
	return TaskResult{w.Name, output, tokens}
}

type TeamLead struct {
	Name         string
	Workers      []Worker
	TokenCeiling int
}

func (l TeamLead) Execute(goal string) (string, int) {
	results := make([]TaskResult, len(l.Workers))
	var wg sync.WaitGroup
	for i, w := range l.Workers {
		wg.Add(1)
		go func(idx int, worker Worker) {
			defer wg.Done()
			subtask := fmt.Sprintf("%s :: focus=%s", goal, worker.Skill)
			results[idx] = worker.Run(subtask)
		}(i, w)
	}
	wg.Wait()

	spent := 0
	parts := make([]string, 0, len(results))
	for _, r := range results {
		if spent+r.Tokens > l.TokenCeiling {
			break
		}
		spent += r.Tokens
		parts = append(parts, fmt.Sprintf("%s: %s", r.Worker, r.Output))
	}
	return fmt.Sprintf("[%s] %s", l.Name, strings.Join(parts, " | ")), spent
}

type RootSupervisor struct {
	Leads         []TeamLead
	GlobalCeiling int
}

func (s RootSupervisor) Run(goal string) string {
	total := 0
	var lines []string
	for _, lead := range s.Leads {
		if total >= s.GlobalCeiling {
			lines = append(lines, fmt.Sprintf("[root] budget exhausted, %s skipped", lead.Name))
			continue
		}
		summary, spent := lead.Execute(goal)
		total += spent
		lines = append(lines, summary)
	}
	lines = append(lines, fmt.Sprintf("[root] total_tokens=%d", total))
	return strings.Join(lines, "\n")
}

func makeResearchHierarchy() RootSupervisor {
	marketLead := TeamLead{
		Name: "market-lead",
		Workers: []Worker{
			{"competitor-scan", "competitors", func(t string) string { return fmt.Sprintf("found 5 rivals for '%s'", t) }},
			{"pricing-scan", "pricing", func(t string) string { return fmt.Sprintf("median price band for '%s'", t) }},
		},
		TokenCeiling: 20000,
	}
	techLead := TeamLead{
		Name: "tech-lead",
		Workers: []Worker{
			{"codebase-scan", "architecture", func(t string) string { return fmt.Sprintf("3 services touch '%s'", t) }},
			{"dependency-scan", "dependencies", func(t string) string { return fmt.Sprintf("2 stale deps near '%s'", t) }},
		},
		TokenCeiling: 20000,
	}
	return RootSupervisor{Leads: []TeamLead{marketLead, techLead}, GlobalCeiling: 100000}
}

func main() {
	supervisor := makeResearchHierarchy()
	fmt.Println(supervisor.Run("checkout-flow redesign"))
}
```

The Go listing runs each Team Lead's workers concurrently through a
`sync.WaitGroup`. The deterministic-index write into `results[idx]` keeps
the output stable across runs regardless of goroutine completion order,
verified by running it repeatedly. Compiled and run directly with
`go run`, output identical in shape to the other two listings.
