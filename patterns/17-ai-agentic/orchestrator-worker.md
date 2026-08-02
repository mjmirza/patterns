---
name: Orchestrator-Worker
slug: orchestrator-worker
family: 17-ai-agentic
category: Multi-Agent Coordination
aliases: [Orchestrator-Workers, Lead Agent and Subagents, Supervisor Pattern, Manager-Worker, Master-Worker]
first_described: "Anthropic, Building Effective Agents, Dec 19 2024 (LLM-agentic form); Mattson, Sanders, Massingill 2004 (distributed-computing ancestor)"
maturity: established
related: [prompt-chaining, parallelization, routing, evaluator-optimizer, reflection, map-reduce, scatter-gather, saga]
incompatible_with: []
verified: 2026-08-02
---

# Orchestrator-Worker

## 1. Name, aliases, and lineage

The name in current use for the LLM-agentic form of this pattern is
Orchestrator-Worker, sometimes written Orchestrator-Workers. It was named and
defined in that exact form by Anthropic in the engineering post "Building
Effective Agents," published December 19, 2024, as one of five workflow
patterns the post catalogs alongside one agent pattern proper. The post states
the definition directly. "In the orchestrator-workers workflow, a central LLM
dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes
their results" (Anthropic, "Building Effective Agents,"
[anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents),
verified 2026-08-02).

The name is not stable across the ecosystem that implements it, and knowing
the aliases matters because a reader who only searches for "orchestrator" will
miss most of the production code that runs this pattern.

- **Lead agent and subagents.** Anthropic's own production system, the
  research feature behind Claude, and Claude Code's own subagent facility, use
  this vocabulary instead of orchestrator and worker. "A lead agent coordinates
  the process while delegating to specialized subagents that operate in
  parallel" (Anthropic, "How we built our multi-agent research system,"
  [anthropic.com/engineering/multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system),
  verified 2026-08-02).
- **Supervisor.** LangGraph's own multi-agent library names the coordinator a
  supervisor rather than an orchestrator. "The supervisor controls all
  communication flow and task delegation, making decisions about which agent
  to invoke based on the current context and task requirements" (LangChain AI,
  langgraph-supervisor-py README,
  [github.com/langchain-ai/langgraph-supervisor-py](https://github.com/langchain-ai/langgraph-supervisor-py),
  verified 2026-08-02).
- **Orchestrator, with named subordinates.** Microsoft's Magentic-One system
  keeps the word orchestrator and gives the workers fixed names tied to their
  tool. WebSurfer, FileSurfer, Coder, and ComputerTerminal (Microsoft
  Research, "Magentic-One. A Generalist Multi-Agent System for Solving Complex
  Tasks,"
  [microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks](https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/),
  verified 2026-08-02).
- **Classifier and specialized agents.** AWS Labs shipped this pattern first
  under the literal name Multi-Agent Orchestrator, then renamed the open
  source project to Agent Squad after a trademark conflict, keeping the same
  classifier-routes-to-agent architecture under the new name (AWS Labs,
  agent-squad README,
  [github.com/awslabs/agent-squad](https://github.com/awslabs/agent-squad),
  verified 2026-08-02).

The pattern also has a lineage that predates language models by two decades,
and the two lineages are worth separating cleanly, the same way a reader of
the Factory Method entry in this catalog needs to separate three different
things called a factory. Timothy G. Mattson, Beverly A. Sanders, and Berna L.
Massingill describe the Master/Worker pattern in "Patterns for Parallel
Programming" (Addison-Wesley, 2004, Chapter 5, "The Supporting Structures
Design Space," Section 5.5, "The Master/Worker Pattern"). Their pattern puts a
master process in charge of a task queue, and worker processes or threads
retrieve a new task whenever they are free, which balances load dynamically
across a homogeneous, fixed pool of tasks known in advance by the calling
program.

That fixed-tasks assumption is exactly what the LLM-agentic Orchestrator-
Worker pattern removes. In the classical Master/Worker pattern the set of
tasks is a data structure the program already holds before any worker starts.
In the LLM-agentic pattern, the orchestrator's model reads the actual input
and decides what the subtasks even are, which means the set of subtasks
differs from one run to the next even for what looks like the same request
type. A useful test for telling the two lineages, and the two neighboring
patterns, apart. if the count and identity of the subtasks can be written down
in code before the input arrives, this is not Orchestrator-Worker, it is the
sibling Parallelization pattern (fixed sectioning of one task, or repeated
voting on the same task) or the classical Master/Worker queue. If a single
model call reads the input and outputs a task list that varies with what that
input actually contains, this is Orchestrator-Worker. Anthropic states the
same distinction directly against its sibling Parallelization pattern. "the
key difference from parallelization is its flexibility, subtasks aren't
predefined, but determined by the orchestrator based on the specific input"
(Anthropic, "Building Effective Agents," cited above).

## 2. Problem and context

A task arrives whose internal shape cannot be known until the model has
already looked at it. Somebody asks an agent to audit a repository, research a
market, or refactor a feature across a codebase, and the number and kind of
pieces that request breaks into depends entirely on what is actually in the
repository, the market, or the codebase. A repository audit for one project
touches three files, for another touches thirty. A market research question
about a narrow product needs one competitor comparison, a question about a
crowded product category needs six. There is no way to write a fixed pipeline
of steps that fits every input in the category, because the category is
defined by open-ended natural language, not by a schema.

The naive answer is a single model call with a long prompt asking it to do the
whole thing in one pass. That works until the task genuinely needs more
context than one context window comfortably holds, or needs several
independent lines of investigation that would otherwise pollute each other's
working memory inside the same conversation. A single agent reading ten web
pages one after another accumulates all ten pages of scratch content in its
own context, most of which becomes irrelevant noise once the ten small
findings are extracted, and that noise crowds out the model's attention on the
parts that still matter for the final answer.

The context in which Orchestrator-Worker becomes the right answer has three
parts, each of them present at once. First, the task decomposes along an axis
the caller cannot enumerate ahead of time, so a human or a fixed pipeline
cannot pre-plan the subtasks. Second, the subtasks are largely independent of
each other, so they can proceed without one waiting on another's intermediate
reasoning, which is what makes running them in parallel both safe and
worthwhile. Third, each subtask on its own would fill a meaningful share of a
context window with exploration that the final answer does not need
verbatim, so isolating that exploration into its own context and returning
only a distilled result is worth the coordination cost. Anthropic frames the
canonical use case this way. "this workflow suits complex tasks where you
can't predict the subtasks needed," naming coding products that make complex
changes across many files as the concrete example (Anthropic, "Building
Effective Agents," cited above).

## 3. Forces

Every implementation of this pattern is a negotiation between forces that
pull against each other, and naming which force wins in a given system is
part of describing that system honestly.

- **Cost against quality.** Running several worker calls in addition to the
  orchestrator's own calls multiplies token spend. Anthropic measured this
  directly on its own production system. "agents typically use about 4 times
  more tokens than chat interactions, and multi-agent systems use about 15
  times more tokens than chats" (Anthropic, "How we built our multi-agent
  research system," cited above). The pattern earns that spend only when the
  quality gain is large enough to justify it, and Anthropic reports one such
  gain directly. "multi-agent system with Claude Opus 4 as the lead agent and
  Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2
  percent" on their internal research evaluation.
- **Latency against thoroughness.** Parallel dispatch can finish faster than a
  single agent working through the same ground sequentially, because
  independent subtasks overlap in wall-clock time. But the orchestrator still
  has to wait for the slowest worker before it can synthesize, and a
  synchronous implementation waits for an entire round before starting the
  next one. Anthropic names this directly as an unresolved limitation of its
  own system. "our lead agents execute subagents synchronously, waiting for
  each set of subagents to complete before proceeding" (same source).
- **Context isolation against coordination overhead.** Giving each worker its
  own context window is the single largest quality lever in this pattern,
  because it keeps ten pages of scratch exploration out of the orchestrator's
  attention. "Subagents facilitate compression by operating in parallel with
  their own context windows, exploring different aspects of the question
  simultaneously" (same source). The cost of that isolation is that the
  orchestrator can only act on what a worker chooses to report back, never on
  the worker's full reasoning trace, so a worker that misreports or omits a
  finding is invisible to the orchestrator until the final answer is wrong.
- **Determinism against flexibility.** A fixed pipeline is reproducible and
  auditable, the same input produces the same call graph every run. The
  orchestrator's own decomposition is itself a model call, so the shape of the
  execution, not only its content, can differ between two runs of the exact
  same input. This is a genuine forfeiture of reproducibility, made in
  exchange for handling inputs a fixed pipeline could never anticipate.
- **A single point of failure against a distributed one.** The orchestrator
  concentrates the decomposition decision and the synthesis decision in one
  place. A bad decomposition (too many workers spawned, or a genuinely
  unclear task boundary handed to a worker) degrades every downstream result
  at once, whereas a single failing worker degrades only its own slice.
  Anthropic's own postmortem names an early failure mode of exactly this
  shape. "early agents made errors like spawning 50 subagents for simple
  queries" (same source).
- **Cognitive load on the person defining the system.** A single agent with
  tools is one prompt to reason about. An orchestrator plus an open-ended
  number of worker roles is two prompts that must agree on a contract, the
  exact shape of the task handed down and the exact shape of the result
  handed back, and that contract has to be precise enough that a worker never
  has to guess what the orchestrator meant.

The pattern generally favors quality and coverage over cost, latency, and
determinism. It is a poor fit for the opposite priority ordering.

## 4. Applicability and non-applicability

**When to reach for it.**

- The task's decomposition genuinely depends on the input, and cannot be
  written down as a fixed list of steps ahead of time. A code review agent
  that inspects whatever files a pull request happens to touch is a clean
  fit; a code formatter that always runs the same three linters in the same
  order is not, because that decomposition is already known.
- The subtasks are close to independent, so a worker's output does not need
  another worker's intermediate reasoning to be useful, only the final
  synthesis needs all of them together.
- Each subtask, done properly, would otherwise fill a meaningful fraction of
  a single agent's context with exploration the final answer does not need
  to preserve verbatim.
- The added cost in tokens, latency, and operational complexity is
  acceptable against the value of the task. Anthropic's own guidance names
  this as the general rule for every agentic pattern, not only this one,
  stating plainly that a team should start with simple prompts, evaluate
  them thoroughly, and add a multi-step agentic system only once a simpler
  approach has been shown to fall short (Anthropic, "Building Effective
  Agents," cited above).
- The workload is bursty and read-heavy, research, multi-file code
  inspection, competitive analysis, broad information gathering, where wrong
  answers are recoverable through iteration rather than catastrophic.

### When not to reach for it (non-applicability)

- **The subtask list is already fixed and known.** If every run of the
  system needs the exact same N steps, use Prompt Chaining for a strict
  sequence or the Parallelization pattern's Sectioning variant for a fixed
  set of independent pieces run at once. Paying an orchestrator's model call
  to rediscover a decomposition that never changes wastes tokens and adds a
  point of nondeterminism for zero benefit.
- **The task needs one specialist, not several pieces of one task.** If the
  real decision is which single expert should answer this, that is
  Routing, not Orchestrator-Worker. Routing sends the whole input to one
  destination; this pattern splits the input across several destinations and
  recombines the results. Conflating the two produces a system that spawns a
  worker for every request even when a single specialized prompt would have
  answered it directly.
- **Workers must coordinate on shared, mutable state.** This pattern assumes
  each worker's context is isolated and workers do not need to see each
  other's intermediate steps. A task where two pieces of work must
  continuously negotiate, such as two agents jointly editing the same file in
  the same pass, fights the isolation this pattern is built on and is a poor
  fit; a single agent, or a tightly coupled pattern like Reflection where one
  agent critiques another's complete draft, fits better.
- **The task is write-heavy against a system of record.** Concurrent workers
  each holding tool access to write the same downstream system risk
  conflicting or duplicate writes with no natural serialization point.
  Anthropic states this plainly from production experience. multi-agent
  systems "aren't a good fit for domains requiring all agents to have
  shared context or domains with many dependencies between agents," and
  names coding as a domain where "most current multi-agent systems struggle"
  because "code changes can require updates in many interdependent locations
  as opposed to research which requires broadly exploring many independent
  directions" (Anthropic, "How we built our multi-agent research system,"
  cited above). Prefer a Saga-style compensating transaction sequence, or a
  single agent working through the writes in order, when correctness of a
  shared write path outweighs the value of parallel exploration.
- **Latency to first byte matters more than completeness.** An interactive
  assistant answering a quick factual question does not benefit from
  spinning up several workers before it can respond; the orchestration
  overhead alone costs more time than a direct answer would have taken.
- **The budget cannot absorb roughly four to fifteen times the token cost of
  a single call.** For a high-volume, low-margin workload, that multiplier
  applied across every request can turn a viable unit economics model into a
  loss-making one. Measure the multiplier on the actual system before
  committing to it in production, rather than assuming Anthropic's
  internally measured 4 times and 15 times figures transfer unchanged.

## 5. Structure

- **Orchestrator (also lead agent, supervisor, or classifier depending on the
  implementation).** The single component with visibility into the original
  goal. It owns three responsibilities and no others. Decomposing the goal
  into subtasks, dispatching those subtasks to workers, and synthesizing the
  returned results into a final answer. It does not do the domain work
  itself.
- **Decomposition step.** The model call, or model-driven planning step,
  inside the orchestrator that reads the input and produces the subtask
  list. In Magentic-One this step also produces a Task Ledger recording
  "facts, guesses, and plan" (Microsoft Research, "Magentic-One," cited
  above), which the orchestrator can revise if execution stalls.
- **Worker (also subagent, agent, or specialist).** A component that
  receives exactly one subtask, has its own isolated working context and its
  own scoped tool access, executes independently of every other worker, and
  returns a bounded result rather than its full working history. A worker
  never reports back to another worker, only to the orchestrator.
- **Dispatch mechanism.** How subtasks physically reach workers. a direct
  function or tool call that spawns a worker and awaits its return (Claude
  Code's subagent facility, Anthropic's own Research feature), a message
  handed to an existing pool member chosen by a classifier (AWS Agent
  Squad), a handoff tool invoked by the orchestrator that transfers control
  and context explicitly (LangGraph's supervisor library), or an
  asynchronous message published to a topic that a pool of worker consumers
  pulls from (an event-driven variant described in dimension 8).
- **Progress ledger, where present.** An explicit, inspectable record of
  which subtasks have returned, which are outstanding, and whether the
  overall plan is stalled. Magentic-One makes this a first-class structure
  separate from the Task Ledger. "the Progress Ledger tracks current
  progress, task assignment to agents" (Microsoft Research, "Magentic-One,"
  cited above). Simpler implementations of the pattern fold this into an
  ordinary array of pending futures with no separate data structure, which
  is sufficient when the orchestrator never needs to replan.
- **Synthesizer.** The step, usually performed by the orchestrator's own
  model call rather than a separate component, that combines the workers'
  returned results into the answer the caller receives. It is the only
  place in the structure where the full set of results is visible together.

## 6. ASCII structure diagram

```
                          caller's goal
                                |
                                v
                    +-----------------------+
                    |      Orchestrator      |
                    |  (lead agent /         |
                    |   supervisor /         |
                    |   classifier)          |
                    |                        |
                    |  decompose(goal)       |
                    |  -> task ledger        |
                    +----+------+------+-----+
                         |      |      |
                dispatch |      |      | dispatch
               subtask A |      |      | subtask N
                         v      v      v
                   +-----+-+ +--+---+ +-+-----+
                   |Worker | |Worker| |Worker |
                   |  A    | |  B   | |  N    |
                   |-------| |------| |-------|
                   |own ctx| |own   | |own ctx|
                   |own    | |ctx,  | |own    |
                   |tools  | |tools | |tools  |
                   +---+---+ +--+---+ +---+---+
                       |         |         |
                       +---------+---------+
                                 |
                     result_A, result_B, ... result_N
                                 |
                                 v
                    +-----------------------+
                    |      Orchestrator      |
                    |  synthesize(results)   |
                    |  -> progress ledger    |
                    |     stalled? replan    |
                    +-----------+-----------+
                                 |
                                 v
                            final output
```

## 7. Dynamics

```
Caller       Orchestrator            Worker A   Worker B   Worker N
  |               |                      |          |          |
  |--- goal ----->|                      |          |          |
  |               |-- decompose(goal) -->|          |          |
  |               |   (writes task       |          |          |
  |               |    ledger)           |          |          |
  |               |                      |          |          |
  |               |--- dispatch A ------>|          |          |
  |               |--- dispatch B -------------------->|          |
  |               |--- dispatch N -------------------------------->|
  |               |                      |          |          |
  |               |     (parallel execution, each worker holds   |
  |               |      its own isolated context and tools)     |
  |               |                      |          |          |
  |               |<-- result A ---------|          |          |
  |               |<-- result B ---------------------|          |
  |               |<-- result N --------------------------------|
  |               |                      |          |          |
  |               |-- update progress ledger ------------------->|
  |               |   any subtask stalled or unclear?             |
  |               |                      |          |          |
  |               |   yes -> decompose a follow-up round,         |
  |               |          dispatch only the outstanding work   |
  |               |   no  -> proceed to synthesis                 |
  |               |                      |          |          |
  |               |-- synthesize(all results) ------------------>|
  |<-- output ----|                      |          |          |
```

The loop back to decomposition is the part most simplified implementations of
this pattern skip, and it is also the part that separates a demonstration
from a production system. Without it, a worker that comes back with an
ambiguous or partial result silently degrades the final synthesis; with it,
the orchestrator can dispatch a narrower follow-up round targeted only at the
unresolved piece. Magentic-One bounds this loop explicitly rather than
letting it run forever, and Microsoft Research describes the orchestrator's
outer and inner loop this way. "if the process stalls for more than two
iterations, the ledger is updated with new information, and the plan is
adjusted" (paraphrasing the orchestrator's loop structure, Microsoft
Research, "Magentic-One," cited above).

## 8. Implementation variants

- **Static roster, dynamic assignment (classifier variant).** A fixed set of
  named worker agents already exists, and the orchestrator's only decision
  per request is which agent, or which small subset of agents, the request
  belongs to. AWS Agent Squad implements exactly this. "the Classifier
  analyzes requests using an LLM, considering the user's current request,
  available agents' descriptions, complete conversation history, and current
  session context, then routes the request to the most suitable agent"
  (AWS Labs, agent-squad README, cited above). This variant is cheaper to
  reason about than fully dynamic spawning, because the space of possible
  workers is closed and each worker's prompt can be tuned against a known,
  bounded role.
- **Dynamic spawning with an open worker count.** The orchestrator can
  create as many workers as the input warrants, with no predefined roster.
  Anthropic's own Research feature and Claude Code's subagent facility both
  work this way. "when Claude encounters a task that matches a subagent's
  description, it delegates to that subagent, which works independently and
  returns results" (Anthropic, "Create custom subagents,"
  [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents),
  verified 2026-08-02), with worker count left to the orchestrator's own
  judgment call rather than a fixed list. This variant needs an explicit
  cap, since an ungoverned orchestrator can spawn far more workers than a
  task warrants, a failure mode covered in dimension 11.
- **Handoff-tool dispatch.** Instead of the orchestrator directly invoking a
  worker function and awaiting the return, the orchestrator calls a
  designated tool whose side effect is to hand control and the relevant
  context to a specific agent, which then runs until it hands control back.
  LangGraph's supervisor library uses "a tool-based agent handoff mechanism
  for communication between agents" (LangChain AI, langgraph-supervisor-py
  README, cited above). This variant fits naturally inside a graph or state
  machine execution model, where every transition, including a delegation,
  is an explicit edge that can be logged, replayed, or interrupted for a
  human to review.
- **Ledger-driven iterative replanning.** The orchestrator does not treat
  decomposition as a one-shot step. It maintains an explicit Task Ledger and
  Progress Ledger, checks after every round whether the plan has stalled,
  and revises the plan rather than accepting an incomplete result. This is
  the shape Magentic-One implements with its outer and inner loop
  (Microsoft Research, "Magentic-One," cited above), and it is the variant
  best suited to long-running, multi-step tasks where the first
  decomposition is unlikely to be exactly right.
- **Bounded worker pool over a task queue.** Rather than spawning one worker
  per subtask unconditionally, a fixed-size pool of long-lived workers pulls
  subtasks from a shared queue as they become free, closer to the classical
  Master/Worker pattern (Mattson, Sanders, Massingill, 2004, cited above)
  than to a spawn-per-subtask model. This bounds peak resource use when the
  decomposition step can return an unpredictable and possibly large number
  of subtasks, at the cost of workers no longer starting the instant a
  subtask is produced.
- **Event-driven dispatch over a message bus.** Instead of the orchestrator
  holding a direct connection to each worker, it publishes a task message to
  a topic, and workers consume from that topic as an independent consumer
  group. "The orchestrator can use keys to distribute command messages
  across partitions in a single topic. Worker agents can then act as a
  consumer group, pulling events from one or more assigned partitions to
  complete the work," and the payoff is decoupling. "the orchestrator no
  longer has to manage its connections to worker agents, including managing
  what happens if one dies or handling more or fewer worker agents"
  (Confluent, "Four Design Patterns for Event-Driven, Multi-Agent Systems,"
  [confluent.io/blog/event-driven-multi-agent-systems](https://www.confluent.io/blog/event-driven-multi-agent-systems/),
  verified 2026-08-02). This variant trades simplicity for horizontal
  scalability and fault tolerance, and fits a deployment that already runs a
  message broker for other purposes.
- **Synchronous fan-out and fan-in versus overlapped rounds.** The simplest
  version, and the one every code example in this entry demonstrates, waits
  for an entire round of workers before starting the next round, which is
  also what Anthropic's production Research system currently does, by its
  own account, as a known limitation rather than a design goal (cited
  above). A more advanced version starts a new subtask's worker the moment
  any worker frees up, rather than waiting for the whole round, which
  shortens end-to-end latency at the cost of a more complex scheduler.

## 9. Known production uses

1. **Anthropic's Claude Research feature.** The multi-agent architecture
   behind Claude's web-facing research capability is a lead agent plus
   parallel subagents, described directly by its own engineering team.
   "Claude now has Research capabilities that allow it to search across the
   web, Google Workspace, and any integrations to accomplish complex tasks,"
   built on the lead-agent-and-subagents structure this entry describes
   (Anthropic, "How we built our multi-agent research system," cited above).
   On Anthropic's internal evaluation, this architecture beat a single
   Claude Opus 4 agent working alone by 90.2 percent.
2. **Claude Code's subagent facility.** Anthropic's own coding agent ships a
   general-purpose orchestrator-and-worker mechanism directly in the
   product, where the main session acts as orchestrator and delegates
   research or exploration work to subagents that "run in their own
   context window with a custom system prompt, specific tool access, and
   independent permissions" and return only a summary (Anthropic, "Create
   custom subagents," cited above). This is the pattern applied inside an
   interactive developer tool rather than a batch research pipeline.
3. **LangGraph's supervisor library.** LangChain's own multi-agent offering
   for the LangGraph framework implements the classical hierarchical
   supervisor shape directly, with "specialized agents coordinated by a
   central supervisor agent" that dispatches through handoff tools
   (LangChain AI, langgraph-supervisor-py README, cited above). It is
   distributed as a standalone Python package and is one of the most widely
   adopted open source implementations of this pattern for teams already
   using LangGraph as their agent runtime.
4. **Microsoft's Magentic-One.** Microsoft Research's generalist multi-agent
   system names an Orchestrator as "the lead agent responsible for task
   decomposition, planning, directing other agents in executing subtasks,
   tracking overall progress, and taking corrective actions as needed,"
   coordinating four specialized agents (WebSurfer, FileSurfer, Coder,
   ComputerTerminal), and is distributed as part of Microsoft's open source
   AutoGen framework (Microsoft Research, "Magentic-One," cited above).
5. **AWS Agent Squad, formerly Multi-Agent Orchestrator.** AWS Labs' open
   source framework implements the classifier-and-specialized-agent variant
   of this pattern in production customer-support reference architectures,
   under the Apache 2.0 license, available in Python, TypeScript, and Swift
   runtimes (AWS Labs, agent-squad README, cited above).

## 10. Consequences

**Positive.**

- Handles tasks whose internal shape genuinely cannot be predicted ahead of
  time, which no fixed pipeline pattern can do without a human rewriting the
  pipeline for every new shape of input.
- Keeps each worker's exploratory context out of the orchestrator's
  attention window, which lets the orchestrator reason about a compressed
  summary of far more raw material than a single context window could hold
  on its own.
- Runs independent subtasks concurrently, shortening end-to-end latency
  relative to one agent working through the same subtasks in sequence,
  whenever the subtasks genuinely do not depend on each other's
  intermediate output.
- Gives each worker a narrower, more specific instruction than a single
  monolithic prompt covering the whole task would need to carry, which
  tends to produce more focused tool use per worker.
- Separates the concerns of decomposition, execution, and synthesis into
  distinct steps that can each be tuned, evaluated, and logged on their own,
  rather than all three being buried inside one long prompt.

**Negative.**

- Multiplies token cost against a single agent call, by a factor Anthropic
  measured at roughly 4 times for agents generally and 15 times for
  multi-agent systems specifically (cited above), which must be weighed
  against the task's actual value.
- Introduces a genuine point of nondeterminism in the shape of execution
  itself, not only its content, because the decomposition step is a model
  call that can vary between two runs of the same input.
- Concentrates failure risk in the orchestrator's own decomposition
  judgment; a poor decomposition (too many workers, an ambiguous subtask
  boundary) degrades every downstream worker at once.
- Adds real engineering surface. a task and result contract between
  orchestrator and worker, a bounding mechanism on worker count and
  concurrency, and, for anything beyond a toy implementation, an explicit
  progress ledger and replanning path.
- Is harder to debug than a single agent, because the failure could live in
  the decomposition, in any one of several parallel workers, or in the
  synthesis step, and the non-deterministic call graph makes exact
  reproduction of a bad run unreliable. Anthropic states this from
  production experience. "agents make dynamic decisions and are
  non-deterministic between runs, even with identical prompts. This makes
  debugging harder" (cited above).

## 11. Failure modes and misuse

**Symptom.** The orchestrator spawns far more workers than the task
justifies, for example dozens of workers on a request that a single
targeted call could have answered.
**Cause.** The orchestrator's prompt gives it no guidance on the expected
scale of effort for a given kind of request, so it defaults to maximal
decomposition, treating "more workers" as strictly safer than "fewer."
Anthropic's own team hit this directly. "early agents made errors like
spawning 50 subagents for simple queries" (cited above).
**Fix.** Give the orchestrator explicit effort-scaling guidance tied to task
complexity, the way Anthropic's own production prompt does. "simple
fact-finding requires just one agent with three to ten tool calls, direct
comparisons might need two to four subagents with ten to fifteen calls
each, and complex research might use more than ten subagents with clearly
divided responsibilities" (cited above). Enforce a hard cap on concurrent
workers in code, not only in the prompt, as the bounded worker pool
implementation variant in dimension 8 does.

**Symptom.** Two or more workers independently investigate the same ground
and return overlapping or duplicate findings, while some other part of the
task goes uncovered entirely.
**Cause.** The orchestrator's task descriptions to each worker are vague
enough that the workers cannot tell where their responsibility ends and a
sibling worker's begins. Anthropic names a concrete instance. "one subagent
explored the 2021 automotive chip crisis while two others duplicated work
investigating current 2025 supply chains, without an effective division of
labor" (cited above).
**Fix.** Give every worker an explicit, non-overlapping task boundary, a
required output format, and, where relevant, the specific tools or sources
it should use. Anthropic's stated rule is direct. "each subagent needs an
objective, an output format, guidance on the tools and sources to use, and
clear task boundaries" (cited above).

**Symptom.** A run that clearly failed, missing an obvious piece of
information, cannot be debugged because nobody can tell which step went
wrong. bad search queries, a poor source choice, or an outright tool
failure inside one worker.
**Cause.** The system has no tracing that survives past the final answer,
so the only visible artifact is the wrong output, with every intermediate
decision, including which worker ran, what it searched for, and what it
returned, discarded once synthesis completes.
**Fix.** Add full production tracing before scaling this pattern past a
demonstration. "Adding full production tracing let us diagnose why agents
failed and fix issues systematically" (cited above). Dimension 16 below
covers what specifically to trace.

**Symptom.** A worker with tool access reads content from an untrusted
source, such as a scraped web page, and its returned result silently
changes the orchestrator's plan or triggers a downstream action, an outcome
the human operator never intended.
**Cause.** The system was assembled without treating the boundary between a
worker's tool output and the orchestrator's trust of that output as a
security boundary at all, so an instruction embedded in scraped content is
processed by the worker's model with the same authority as a real
instruction. This is an instance of what Simon Willison names the lethal
trifecta, three conditions that together create an exfiltration risk.
"access to your private data," "exposure to untrusted content," and "the
ability to externally communicate," where any agent, or any composition of
agents across an orchestrator and its workers, that ends up possessing all
three at once is exploitable through prompt injection (Simon Willison, "The
lethal trifecta for AI agents,"
[simonwillison.net/2025/Jun/16/the-lethal-trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/),
verified 2026-08-02). Dimension 17 covers this at length.
**Fix.** Never let a worker that reads untrusted content also hold write
access to a system of record or the ability to trigger a downstream
communication, and never let the orchestrator treat a worker's textual
report as trusted instruction rather than trusted-only-as-data. Scope tool
access per worker to the minimum the subtask requires.

**Symptom.** After a code change to the orchestrator or a worker's prompt,
runs that were mid-flight when the change deployed fail or behave
inconsistently, and nobody can tell which version of the prompt actually
handled a given run.
**Cause.** A running multi-round task can be paused between rounds at the
exact moment a new deployment lands, and if the deployment does not account
for agents already in flight, "agents might be anywhere in their process"
when the update lands, and the new code can silently break the state an
in-flight run assumed (cited above).
**Fix.** Deploy with a strategy that keeps both the old and new version
running side by side during a transition rather than an instant cutover.
"rainbow deployments to avoid disrupting running agents, by gradually
shifting traffic from old to new versions while keeping both running
simultaneously" (cited above).

## 12. Trade-off matrix

| Force | Orchestrator-Worker | Parallelization (fixed sectioning) | Routing | Single agent with tools |
|---|---|---|---|---|
| Decomposition source | Model, dynamic, per input | Code, fixed ahead of time | Model chooses one destination, no split | None, one continuous context |
| Reproducibility of call graph | Low, shape can vary run to run | High, shape is fixed | Medium, one branch chosen per run | High, one call graph |
| Token cost versus a single call | Roughly 4 to 15 times, per Anthropic's own measurement | Higher than one call, but bounded and known ahead of time | Close to one call plus the classification step | Baseline, one call's worth |
| Handles input-dependent structure | Yes, this is the pattern's reason to exist | No, the structure must already be known | No, only chooses among known specialists | Yes, but all context lives in one window |
| Coordination complexity to build | High, needs a task and result contract plus a bound on worker count | Medium, needs only a fixed fan-out and a merge step | Low, needs only a classifier and a set of destinations | Lowest, no coordination layer at all |
| Failure isolation | Good per worker, poor at the orchestrator's decomposition step | Good per section | Single destination handles the whole request, not applicable | Poor, one failure can derail the whole context |
| Best suited workload | Open-ended research or multi-file exploration | A task with a known, stable internal shape | A request that fits cleanly into one specialist's domain | A short task that fits comfortably in one context window |

## 13. Related and incompatible patterns

- **Prompt Chaining.** The strict sequential sibling. "prompt chaining
  decomposes a task into a sequence of steps, where each LLM call processes
  the output of the previous one" (Anthropic, "Building Effective Agents,"
  cited above). Where Orchestrator-Worker fans out into independent,
  parallel pieces, Prompt Chaining is a straight line where each step
  depends on the one before it. The two compose naturally. a worker's own
  internal execution is frequently itself a short prompt chain.
- **Parallelization (Sectioning and Voting).** The closest sibling and the
  one most often confused with Orchestrator-Worker, distinguished entirely
  by whether the subtask list is fixed ahead of time (Parallelization) or
  determined by the model at run time (Orchestrator-Worker), per Anthropic's
  own stated distinction quoted in dimension 1.
- **Routing.** "Routing classifies an input and directs it to a specialized
  followup task" (Anthropic, "Building Effective Agents," cited above),
  sending the whole input to exactly one destination rather than splitting
  it across several. AWS Agent Squad's classifier step is, on its own, an
  instance of Routing; the pattern becomes Orchestrator-Worker only once the
  chosen destination is itself capable of spawning further workers for a
  complex request, or once the classifier can dispatch to more than one
  agent for a single request.
- **Evaluator-Optimizer.** A different two-role pattern where one model
  produces a draft and a second model critiques it against explicit
  criteria, iterating until the draft passes. It composes with
  Orchestrator-Worker naturally as the synthesis step. an orchestrator can
  run an evaluator pass over the combined worker output before returning it
  to the caller, rather than returning the raw synthesis unchecked.
- **Reflection.** A single agent, or a small fixed pair of agents,
  critiquing and revising its own prior output. Reflection assumes a shared,
  continuous context between the drafting and critiquing steps, which is
  the opposite assumption from Orchestrator-Worker's isolated-worker
  contexts, so the two rarely nest inside each other cleanly; they are
  usually chosen as alternatives for different points in a larger system.
- **The Master/Worker pattern (distributed computing).** The direct
  non-LLM ancestor, discussed at length in dimension 1 (Mattson, Sanders,
  Massingill, 2004). Any bounded worker pool implementation of this
  pattern, described in dimension 8, is structurally identical to the
  classical Master/Worker pattern with the addition of a model-driven
  decomposition step feeding the queue.
- **Scatter-Gather.** Gregor Hohpe and Bobby Woolf's messaging pattern
  "broadcasts a message to multiple recipients and re-aggregates the
  responses back into a single message" (Enterprise Integration Patterns,
  [enterpriseintegrationpatterns.com/patterns/messaging/BroadcastAggregate.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/BroadcastAggregate.html),
  citing Gregor Hohpe and Bobby Woolf, Enterprise Integration Patterns.
  Designing, Building, and Deploying Messaging Solutions, Addison-Wesley,
  2003, verified 2026-08-02). Scatter-Gather broadcasts the same message to
  a fixed, known set of recipients; Orchestrator-Worker sends a different,
  model-decided message to each worker. The synthesis, or aggregation, step
  at the end is structurally the same idea in both patterns.
- **Map-Reduce.** The batch-processing ancestor that splits a large, already
  known dataset into fixed, uniform chunks, maps a function over each chunk
  in parallel, then reduces the partial results into one. Map-Reduce shares
  the fan-out and fan-in shape with Orchestrator-Worker but, like
  Parallelization and Scatter-Gather, assumes the split is fixed and
  uniform rather than model-decided and heterogeneous.
- **Saga.** The compensating-transaction pattern for coordinating a
  sequence of writes across services where no single database transaction
  can span all of them. Saga is named in dimension 4's non-applicability
  list as the better fit than Orchestrator-Worker when the task is a
  write-heavy sequence against a shared system of record, precisely because
  Saga's ordering and compensation guarantees are what a set of
  concurrent, isolated workers cannot provide.

No pattern in this list is strictly incompatible with Orchestrator-Worker at
the architecture level; the more common failure is nesting it where a
simpler sibling would have sufficed, which dimension 4's non-applicability
list and dimension 11's failure modes both cover directly.

## 14. Refactoring path in and out

**Introducing the pattern into a system that does not have it.**

1. Start from a single agent with tools handling the task end to end, and
   measure it against a small evaluation set before touching the
   architecture. Anthropic's own guidance is explicit that this measurement
   step comes first. "it's best to start with small-scale testing right
   away with a few examples, rather than delaying until you can build more
   thorough evals" (Anthropic, "How we built our multi-agent research
   system," cited above).
2. Identify where the single agent's context becomes crowded with
   exploratory material the final answer does not need verbatim. That
   crowding point is the seam along which the task should split into
   worker-sized pieces.
3. Extract the exploratory portion into a worker function with a narrow,
   explicit contract, what it receives, what tools it may use, and the exact
   shape of what it returns. Keep this contract far narrower than "do the
   research," because an underspecified contract reproduces the
   task-duplication failure mode from dimension 11.
4. Introduce the orchestrator as a thin layer around the existing agent
   logic, a decomposition step that decides how many workers the current
   input warrants, a dispatch step that calls the worker function, awaiting
   or gathering results depending on the runtime's concurrency primitives,
   and a synthesis step that recombines them. Reuse the original single
   agent's prompt as the synthesis prompt where possible, rather than
   writing a new one from a blank page.
5. Add a hard concurrency cap and a timeout on the dispatch step before this
   ever reaches production traffic, not after an incident.
6. Add tracing that records, at minimum, the decomposition output, each
   worker's subtask and result, and the synthesis input, so a bad run can be
   diagnosed after the fact.
7. Only after the above is stable, consider adding a progress ledger and a
   replanning loop, the way Magentic-One does, if the task category
   genuinely produces stalled or incomplete rounds often enough to justify
   the added complexity.

**Removing the pattern once it stops earning its place.**

1. Watch the effort-scaling signal directly. if the orchestrator's own
   decomposition step consistently returns exactly one subtask, or a fixed
   count of subtasks, for every real input the system receives, the
   dynamic decomposition this pattern exists to provide is not being used.
2. Collapse the fixed case into whichever sibling pattern actually matches
   the now-stable shape, Prompt Chaining if the "workers" turn out to
   always run in a strict order, or the Parallelization pattern's
   Sectioning variant if they turn out to always be the same fixed set run
   at once.
3. Remove the decomposition model call entirely once the fixed shape is
   confirmed, replacing it with the equivalent fixed fan-out in ordinary
   code. This removes the multiplier cost described in dimension 3 for the
   large share of traffic that never needed dynamic decomposition in the
   first place.
4. Keep the option to fall back to the full Orchestrator-Worker path for
   the smaller share of inputs that genuinely still need it, rather than
   deleting the capability outright, if such inputs are known to still
   occur.

## 15. Testing and verification

Build the evaluation set before, or alongside, the first working
implementation, not after. Anthropic's own team started with "a set of
about 20 queries representing real usage patterns," reporting that "testing
these queries often allowed us to clearly see the impact of changes"
(Anthropic, "How we built our multi-agent research system," cited above),
and warns against the common mistake of postponing evaluation until the
system feels complete.

Evaluate the decomposition step and the synthesis step separately from each
other where possible, because a failure can live in either without the
other being at fault. A decomposition test asserts that the subtask list
for a known input matches, or reasonably approximates, an expected shape,
right number of subtasks, non-overlapping boundaries, and coverage of the
input's distinct facets. A synthesis test can be run independently by
feeding a fixed, hand-written set of worker results directly into the
synthesis step and checking that the combined answer is faithful to all of
them, without paying for the decomposition and worker calls on every test
run.

For the end-to-end output, an automated grader is the only practical way to
evaluate at scale, and Anthropic's team used an approach described this
way. "an LLM judge that evaluated each output against criteria in a
rubric. factual accuracy (do claims match sources?), citation accuracy (do
the cited sources match the claims?), completeness (are all requested
aspects covered?), source quality (did it use primary sources over
lower-quality secondary sources?), and tool efficiency (did it use the
right tools a reasonable number of times?)" (same source). Naming the
rubric's dimensions explicitly, rather than asking a judge for a single
undifferentiated quality score, makes regressions traceable to a specific
cause.

An automated rubric alone is not sufficient. "People testing agents find
edge cases that evals miss. These include hallucinated answers on unusual
queries, system failures, or subtle source selection biases" (same source).
Keep a human review pass in the loop, especially for the failure modes in
dimension 11 that manifest as a plausible-looking but wrong final answer,
since an automated judge grading only the final synthesis has no visibility
into whether that answer came from a genuinely complete investigation or
from two workers that duplicated the same easy third of the task while
leaving the hard two-thirds uncovered.

Test the concurrency and cancellation behavior directly, not only the
happy-path output. Force a worker to fail, or to exceed a timeout, and
assert that the orchestrator excludes it from synthesis with a clear note
rather than crashing the entire run or silently substituting an empty
result; the TypeScript example under the code section demonstrates exactly
this using `Promise.allSettled` rather than `Promise.all`. Force a
genuinely stalled subtask and assert that the replanning bound, if the
system has one, actually terminates rather than looping indefinitely.

Because "each agent is steered by a prompt, prompt engineering was our
primary lever for improving these behaviors" (same source), treat prompt
changes to the orchestrator's decomposition instructions, and to any
worker's role definition, as changes that require a re-run of the full
evaluation set before shipping, the same discipline applied to a code
change anywhere else in the system.

## 16. Observability signals

- **Full production tracing of the call graph itself**, not only of final
  outputs. "Adding full production tracing let us diagnose why agents
  failed and fix issues systematically" (Anthropic, "How we built our
  multi-agent research system," cited above). At minimum, log the
  orchestrator's decomposition output, each dispatched subtask with its
  worker identity, each worker's tool calls and final result, and the
  synthesis input, so a specific bad run can be replayed step by step
  after the fact rather than only observed as a wrong final answer.
- **Agent decision patterns and interaction structures**, aggregated across
  runs rather than only inspected one run at a time, "without monitoring
  the contents of individual conversations, to maintain user privacy" (same
  source). Track the distribution of subtask counts per request, the ratio
  of tool calls to subtasks, and how often replanning triggers, as trend
  signals that surface a drifting decomposition prompt before it produces a
  visible quality regression.
- **Token and tool-call cost per run**, broken down by orchestrator versus
  worker spend, since the 4 times to 15 times multiplier discussed in
  dimension 3 is a fact about the system's design, not a fixed constant;
  measuring it on the actual production traffic is the only way to know
  whether a given change made that multiplier better or worse.
- **Worker failure and timeout rate**, tracked per worker role rather than
  in aggregate, since a single tool integration failing consistently
  behind one worker role is a very different operational issue from an
  intermittent, evenly distributed failure rate across every worker.
- **A healthy instance looks like** a stable distribution of subtask counts
  for a given request category, a low and roughly constant rate of
  replanning, worker latency that scales with the pool size rather than
  with total subtask count (evidence that concurrency is genuinely
  bounded and parallel rather than accidentally serialized), and a token
  cost per run that tracks the complexity guidance given to the
  orchestrator rather than drifting upward independent of it.
- **A failing instance looks like** a rising rate of maximum-subtask-count
  runs (the 50-subagents-for-a-simple-query failure mode from dimension
  11), a rising replanning rate with no matching rise in task difficulty,
  worker latency climbing in lockstep with subtask count (evidence that a
  supposed concurrency bound is not actually enforced), or a growing gap
  between the LLM judge's rubric score and human review's assessment of
  the same runs, which signals the automated rubric has stopped tracking
  what actually matters.
- **Deployment-time visibility into in-flight runs**, so a code or prompt
  change can be correlated against exactly which version of the
  orchestrator or a worker handled a given run, especially under a rainbow
  deployment strategy where two versions run concurrently for a period
  (Anthropic, "How we built our multi-agent research system," cited
  above).

## 17. Security and privacy implications

The central risk this pattern introduces beyond a single agent is that
trust decisions get made across a boundary between components, and a system
built without treating that boundary as a real security boundary inherits
every problem prompt injection already causes a single agent, multiplied by
however many workers can independently ingest untrusted content.

Simon Willison's lethal trifecta framing applies directly, and applies at
the level of the system as a whole, not only at the level of any single
agent within it. "access to your private data," "exposure to untrusted
content," and "the ability to externally communicate" together create an
exfiltration risk (Simon Willison, "The lethal trifecta for AI agents,"
cited above). The important, easy-to-miss consequence for Orchestrator-
Worker specifically is that no single component needs to hold all three
capabilities for the trifecta to exist. A worker that only reads untrusted
web content, with no data access and no ability to communicate externally,
looks safe in isolation. If that worker's returned text is trusted
uncritically by the orchestrator, and the orchestrator then dispatches a
second worker that holds both private data access and an external
communication tool, using the first worker's report as an input to that
second worker's instructions, the trifecta has been assembled across the
two components even though neither one held all three capabilities alone.
The system, not any one agent inside it, is the unit that must be
evaluated for this risk.

The OWASP Gen AI Security Project's Top 10 for Agentic Applications (2026)
names this class of risk for agentic systems generally, describing itself
as a peer-reviewed framework identifying "the most critical security risks
facing autonomous and agentic AI systems"
([genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/),
verified 2026-08-02). Applying that general framework to this specific
pattern is engineering judgment rather than a claim the framework makes
about Orchestrator-Worker by name. the natural risk surface in this
pattern's architecture is the trust boundary between a worker's returned
result and the orchestrator's synthesis and dispatch decisions, since that
boundary is exactly where the isolation this pattern relies on for quality
also becomes the place where an untrusted worker output can steer the
orchestrator's next action without a human ever reviewing the intermediate
step.

Concrete mitigations that follow from this analysis.

- Treat every worker's returned text as data to be summarized or quoted,
  never as an instruction the orchestrator's own model should follow, and
  say so explicitly in the orchestrator's synthesis prompt.
- Scope each worker's tool access to the minimum its subtask requires. A
  worker that reads external content should not, in the same run, also
  hold write access to a system of record or an outbound communication
  tool; if both capabilities are genuinely needed for the overall task,
  split them across two workers whose results the orchestrator combines
  only after independent inspection.
- Apply least-privilege permissions per worker rather than a single shared
  credential set for the whole system, matching the isolation the pattern
  already provides for context. Claude Code's own subagent facility grants
  "specific tool access, and independent permissions" per subagent rather
  than a shared blanket permission set (Anthropic, "Create custom
  subagents," cited above), and that same discipline applies to any
  implementation of this pattern regardless of which agent framework runs
  it.
- Log every tool call a worker makes, per dimension 16, specifically so an
  injected instruction that caused an unexpected tool call is visible in
  the trace rather than only visible as an unexplained downstream effect.
- On the privacy side, keep per-run tracing free of the raw content of
  private conversations even while tracing decision structure, the
  balance Anthropic states directly. monitor "agent decision patterns and
  interaction structures... without monitoring the contents of individual
  conversations, to maintain user privacy" (Anthropic, "How we built our
  multi-agent research system," cited above). A tracing system built for
  debugging this pattern is itself a store of worker outputs that
  may be sensitive, and needs the same data-handling care as any other log
  of user-derived content.

## 18. References

1. Anthropic. "Building Effective Agents." Published December 19, 2024.
   [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents).
   Verified 2026-08-02.
2. Anthropic. "How we built our multi-agent research system."
   [anthropic.com/engineering/multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system).
   Verified 2026-08-02.
3. Anthropic. "Create custom subagents." Claude Code documentation.
   [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents).
   Verified 2026-08-02.
4. Timothy G. Mattson, Beverly A. Sanders, Berna L. Massingill. Patterns
   for Parallel Programming. Addison-Wesley, 2004. Chapter 5, "The
   Supporting Structures Design Space," Section 5.5, "The Master/Worker
   Pattern."
5. LangChain AI. langgraph-supervisor-py, README.
   [github.com/langchain-ai/langgraph-supervisor-py](https://github.com/langchain-ai/langgraph-supervisor-py).
   Verified 2026-08-02.
6. Microsoft Research. "Magentic-One. A Generalist Multi-Agent System for
   Solving Complex Tasks."
   [microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks](https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/).
   Verified 2026-08-02.
7. AWS Labs. agent-squad, README (formerly Multi-Agent Orchestrator).
   [github.com/awslabs/agent-squad](https://github.com/awslabs/agent-squad).
   Verified 2026-08-02.
8. Gregor Hohpe, Bobby Woolf. Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions. Addison-Wesley, 2003.
   "Scatter-Gather" pattern, as reproduced at
   [enterpriseintegrationpatterns.com/patterns/messaging/BroadcastAggregate.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/BroadcastAggregate.html).
   Verified 2026-08-02.
9. Simon Willison. "The lethal trifecta for AI agents." Published June 16,
   2025.
   [simonwillison.net/2025/Jun/16/the-lethal-trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/).
   Verified 2026-08-02.
10. Confluent. "Four Design Patterns for Event-Driven, Multi-Agent
    Systems."
    [confluent.io/blog/event-driven-multi-agent-systems](https://www.confluent.io/blog/event-driven-multi-agent-systems/).
    Verified 2026-08-02.
11. OWASP Gen AI Security Project. "OWASP Top 10 for Agentic Applications
    for 2026."
    [genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/).
    Verified 2026-08-02.

## Code examples

Three runnable reference implementations follow. Python (dynamic typing,
`asyncio`), TypeScript (static typing, `Promise`-based concurrency with
partial-failure tolerance), and Go (explicit goroutines and channels, a
bounded worker pool with context-based cancellation). All three mock the
model calls that would normally drive decomposition and worker execution,
since this catalog entry ships no API credentials; the mocking is
deterministic and clearly marked, and every example was compiled or run in
full during authoring, with output shown beneath each.

### Python

```python
"""Orchestrator-Worker pattern, minimal reference implementation.
No live model calls: decomposition and worker execution are mocked
deterministically so the example runs without an API key. What matters
for the pattern is the shape: dynamic decomposition, isolated worker
state, parallel dispatch, bounded replanning, and synthesis."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


@dataclass
class Subtask:
    id: str
    description: str
    tool_hint: str


@dataclass
class WorkerResult:
    subtask_id: str
    output: str
    tool_calls: int
    needs_replan: bool = False


class Worker:
    """One worker per subtask. Its memory dict is created fresh here
    and never shared with any other worker or with the orchestrator's
    own state. A worker can hold a large scratch history of its own
    subtopic without inflating anyone else's context window."""

    def __init__(self, subtask: Subtask) -> None:
        self.subtask = subtask
        self.memory: dict[str, str] = {}

    async def run(self) -> WorkerResult:
        await asyncio.sleep(0.01)
        self.memory["last_tool"] = self.subtask.tool_hint
        tool_calls = 3 if "search" in self.subtask.tool_hint else 1
        stalled = "unclear" in self.subtask.description
        output = f"[{self.subtask.id}] researched via {self.subtask.tool_hint}"
        return WorkerResult(
            subtask_id=self.subtask.id,
            output=output,
            tool_calls=tool_calls,
            needs_replan=stalled,
        )


class Orchestrator:
    """Owns decomposition, dispatch, the progress ledger, and
    synthesis. It never does the subtask work itself."""

    def __init__(self, max_replans: int = 1) -> None:
        self.max_replans = max_replans
        self.ledger: list[str] = []

    def decompose(self, goal: str, round_no: int) -> list[Subtask]:
        if round_no == 0:
            return [
                Subtask("A", "current market size", "web_search"),
                Subtask("B", "unclear regulatory status", "web_search"),
                Subtask("C", "top three competitors", "web_search"),
            ]
        return [Subtask("B2", "regulatory status, second pass", "gov_db_search")]

    async def run(self, goal: str) -> str:
        results: list[WorkerResult] = []
        round_no = 0
        while round_no <= self.max_replans:
            subtasks = self.decompose(goal, round_no)
            self.ledger.append(f"round {round_no}: dispatched {len(subtasks)} worker(s)")
            workers = [Worker(t) for t in subtasks]
            round_results = await asyncio.gather(*(w.run() for w in workers))
            results.extend(round_results)
            if not any(r.needs_replan for r in round_results):
                break
            round_no += 1
        return self.synthesize(results)

    def synthesize(self, results: list[WorkerResult]) -> str:
        total_tool_calls = sum(r.tool_calls for r in results)
        lines = [r.output for r in results]
        self.ledger.append(
            f"synthesized {len(results)} result(s), {total_tool_calls} tool calls total"
        )
        return "\n".join(lines)


async def main() -> None:
    start = time.perf_counter()
    orchestrator = Orchestrator(max_replans=1)
    report = await orchestrator.run("assess entering the market for X")
    elapsed = time.perf_counter() - start
    print(report)
    print(f"elapsed: {elapsed:.3f}s")
    for line in orchestrator.ledger:
        print("ledger:", line)


if __name__ == "__main__":
    asyncio.run(main())
```

Run with `python3 orchestrator_worker.py`. Actual output from this
session.

```
[A] researched via web_search
[B] researched via web_search
[C] researched via web_search
[B2] researched via gov_db_search
elapsed: 0.023s
ledger: round 0: dispatched 3 worker(s)
ledger: round 1: dispatched 1 worker(s)
ledger: synthesized 4 result(s), 12 tool calls total
```

Subtask B's description contains "unclear," which flips its
`needs_replan` flag, so the orchestrator runs a second, narrower round
dispatching only subtask B2, the ledger-driven replanning loop from
dimension 7 and dimension 8, before synthesizing all four results
together.

### TypeScript

```typescript
// Orchestrator-Worker pattern, minimal reference implementation.
// Decomposition is mocked deterministically so the example compiles
// and runs without an API key. Demonstrates isolated worker context,
// a bounded worker pool, and partial-failure tolerant synthesis.

interface Subtask {
  id: string;
  description: string;
  shouldFail: boolean;
}

interface WorkerResult {
  subtaskId: string;
  output: string;
}

class TaskWorker {
  // Fresh per instance. Never read or written by any other worker.
  private context: Map<string, string> = new Map();

  constructor(private readonly subtask: Subtask) {}

  async run(): Promise<WorkerResult> {
    this.context.set("startedAt", new Date().toISOString());
    await new Promise((resolve) => setTimeout(resolve, 5));
    if (this.subtask.shouldFail) {
      throw new Error(`worker ${this.subtask.id} failed: tool timeout`);
    }
    return {
      subtaskId: this.subtask.id,
      output: `[${this.subtask.id}] ${this.subtask.description} done`,
    };
  }
}

class Orchestrator {
  constructor(private readonly poolSize: number) {}

  decompose(goal: string): Subtask[] {
    return [
      { id: "A", description: "summarize file src/auth.ts", shouldFail: false },
      { id: "B", description: "summarize file src/db.ts", shouldFail: true },
      { id: "C", description: "summarize file src/api.ts", shouldFail: false },
      { id: "D", description: "summarize file src/ui.ts", shouldFail: false },
    ];
  }

  // Bounded fan out. Never spawn one worker per subtask unconditionally;
  // cap concurrency so a large decomposition cannot exhaust the process.
  private async runBounded(subtasks: Subtask[]): Promise<PromiseSettledResult<WorkerResult>[]> {
    const results: PromiseSettledResult<WorkerResult>[] = new Array(subtasks.length);
    let cursor = 0;
    const lane = async () => {
      while (cursor < subtasks.length) {
        const index = cursor++;
        const worker = new TaskWorker(subtasks[index]);
        try {
          results[index] = { status: "fulfilled", value: await worker.run() };
        } catch (err) {
          results[index] = { status: "rejected", reason: (err as Error).message };
        }
      }
    };
    await Promise.all(Array.from({ length: this.poolSize }, () => lane()));
    return results;
  }

  async run(goal: string): Promise<string> {
    const subtasks = this.decompose(goal);
    const settled = await this.runBounded(subtasks);
    const ok = settled.filter((r) => r.status === "fulfilled") as PromiseFulfilledResult<WorkerResult>[];
    const failed = settled.filter((r) => r.status === "rejected") as PromiseRejectedResult[];
    const body = ok.map((r) => r.value.output).join("\n");
    const note = failed.length > 0 ? `\n(${failed.length} subtask(s) failed and were excluded)` : "";
    return body + note;
  }
}

async function main() {
  const orchestrator = new Orchestrator(2);
  const report = await orchestrator.run("summarize the auth module");
  console.log(report);
}

main();
```

Compiled with `npx tsc --strict --target es2020 --lib es2020,dom
orchestrator-worker.ts`, run with `node orchestrator-worker.js`. Actual
output from this session.

```
[A] summarize file src/auth.ts done
[C] summarize file src/api.ts done
[D] summarize file src/ui.ts done
(1 subtask(s) failed and were excluded)
```

Subtask B is marked to fail deliberately, simulating a worker whose tool
call times out. The orchestrator excludes it from the synthesized output
and reports the exclusion explicitly rather than crashing the whole run
or silently dropping the note that one subtask never completed, the fix
named in dimension 15's discussion of testing failure and cancellation
paths.

### Go

```go
// Orchestrator-Worker pattern, minimal reference implementation.
// Decomposition is mocked deterministically. Demonstrates a bounded
// worker pool over channels, per-worker isolated state, and context
// based cancellation propagated from the orchestrator to every worker.
package main

import (
	"context"
	"fmt"
	"sort"
	"sync"
	"time"
)

type Subtask struct {
	ID          string
	Description string
}

type WorkerResult struct {
	SubtaskID string
	Output    string
	Err       error
}

// worker owns its own local map. It is never shared with another
// goroutine, so no mutex is needed around it.
func worker(ctx context.Context, id int, in <-chan Subtask, out chan<- WorkerResult, wg *sync.WaitGroup) {
	defer wg.Done()
	local := map[string]string{}
	for task := range in {
		select {
		case <-ctx.Done():
			out <- WorkerResult{SubtaskID: task.ID, Err: ctx.Err()}
			continue
		default:
		}
		local["last"] = task.ID
		time.Sleep(2 * time.Millisecond)
		out <- WorkerResult{
			SubtaskID: task.ID,
			Output:    fmt.Sprintf("[%s] %s (handled by pool worker %d)", task.ID, task.Description, id),
		}
	}
}

func decompose(goal string) []Subtask {
	return []Subtask{
		{"A", "check config drift"},
		{"B", "check dependency versions"},
		{"C", "check open alerts"},
	}
}

func orchestrate(goal string, poolSize int, timeout time.Duration) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	subtasks := decompose(goal)
	in := make(chan Subtask, len(subtasks))
	out := make(chan WorkerResult, len(subtasks))

	var wg sync.WaitGroup
	for i := 0; i < poolSize; i++ {
		wg.Add(1)
		go worker(ctx, i, in, out, &wg)
	}

	for _, t := range subtasks {
		in <- t
	}
	close(in)

	go func() {
		wg.Wait()
		close(out)
	}()

	results := make([]WorkerResult, 0, len(subtasks))
	for r := range out {
		if r.Err != nil {
			return "", fmt.Errorf("subtask %s did not complete: %w", r.SubtaskID, r.Err)
		}
		results = append(results, r)
	}

	sort.Slice(results, func(i, j int) bool { return results[i].SubtaskID < results[j].SubtaskID })

	summary := ""
	for _, r := range results {
		summary += r.Output + "\n"
	}
	return summary, nil
}

func main() {
	report, err := orchestrate("pre-deploy health check", 2, 500*time.Millisecond)
	if err != nil {
		fmt.Println("orchestration failed:", err)
		return
	}
	fmt.Print(report)
}
```

Run with `go run orchestrator_worker.go`. Actual output from this
session.

```
[A] check config drift (handled by pool worker 0)
[B] check dependency versions (handled by pool worker 1)
[C] check open alerts (handled by pool worker 1)
```

The pool holds only two goroutines against three subtasks, the bounded
worker pool variant from dimension 8, so worker 1 processes two of the
three subtasks in turn while worker 0 handles the first, and the
orchestrator's `context.WithTimeout` would cancel every outstanding
worker at once if the deadline were exceeded, the cancellation-
propagation concern named in dimension 3's discussion of a single point
of failure.

Java and Rust were not used for this entry. A Java toolchain was not
available in the authoring environment, `javac` reported no located Java
runtime, so no fourth example was compiled there. Rust's compiler was
available but was not exercised, since three working, verified languages
already satisfy this catalog's code requirement and a fourth example
would not add a structurally different implementation choice beyond
what the bounded channel-based worker pool in Go already demonstrates.
