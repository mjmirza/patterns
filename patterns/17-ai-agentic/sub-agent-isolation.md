---
name: Sub-Agent Isolation
slug: sub-agent-isolation
family: 17-ai-agentic
category: Multi-Agent Coordination
aliases: [Context Isolation, Isolated Subagent Context, Agent Sandbox Boundary, Bulkhead Agent]
first_described: "Anthropic, Building Effective Agents and How we built our multi-agent research system, 2024-2025 (informal engineering description); Carl Hewitt, Peter Bishop, Richard Steiger 1973 (actor-model isolation ancestor)"
maturity: established
related: [orchestrator-worker, parallelization, routing, model-context-protocol, function-calling]
incompatible_with: []
verified: 2026-08-02
---

# Sub-Agent Isolation

## 1. Name, aliases, and lineage

The name in current use is Sub-Agent Isolation, sometimes written as Subagent
Isolation or Context Isolation. Unlike Factory Method or Orchestrator-Worker,
this pattern has no single paper of origin. It crystallized between 2024 and
2025 as several vendors independently arrived at the same shape while building
production agent frameworks, and each vendor named it differently.

Anthropic's engineering team calls the mechanism a fresh context window per
delegated worker. "Each subagent operates independently in parallel with its
own context window" (Anthropic, "How we built our multi-agent research
system," [anthropic.com/engineering/multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system),
verified 2026-08-02). Claude Code, Anthropic's own coding agent, documents the
same mechanism at the tool level. "Each subagent runs in its own context
window with a custom system prompt, specific tool access, and independent
permissions" (Anthropic, "Create custom subagents,"
[code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents),
verified 2026-08-02). OpenAI's Agents SDK calls the isolated variant
Agent.as_tool, and contrasts it explicitly with its non-isolated sibling,
handoffs, where "it's as though the new agent takes over the conversation, and
gets to see the entire previous conversation history" (OpenAI, "Handoffs,"
[openai.github.io/openai-agents-python/handoffs](https://openai.github.io/openai-agents-python/handoffs/),
verified 2026-08-02). No community has settled on one term, so a reader
searching only for "subagent isolation" will miss production code documented
under context window, agent-as-tool, or agent sandbox.

Three different technical claims travel under the word isolation in agent
system discussions, and confusing them is the most common source of a broken
mental model when reasoning about this pattern.

- **Context isolation.** The subagent's conversation history, its accumulated
  tool outputs, and its reasoning trace live in a separate token budget from
  the caller's. This is the meaning this entry is about, and it is a property
  of the conversation object a framework maintains, not a property of the
  operating system.
- **Permission isolation.** The subagent's tool allowlist is a subset of, and
  possibly disjoint from, the caller's. A subagent scoped to read-only file
  tools cannot send an email even if the caller could. This is orthogonal to
  context isolation. A framework can isolate context while leaving permissions
  wide open, and the two must be reasoned about separately, see dimension 17.
- **Process or sandbox isolation.** The subagent's code runs in a distinct
  operating-system process, container, or virtual machine, with its own
  filesystem view and network policy. This is a security boundary enforced by
  the operating system or a hypervisor, unrelated to which tokens are in which
  conversation array. A chat framework that gives two agents separate message
  histories inside the same Python process has context isolation and zero
  process isolation.

This entry's structural and dynamic dimensions describe context isolation, the
form every LLM agent framework implements by default. Dimension 8 covers the
process-level variant as one implementation choice among several, and
dimension 17 is explicit about where context isolation stops providing a
security guarantee and process isolation would be needed instead.

The pattern's conceptual ancestor in distributed systems is the actor model,
first described by Carl Hewitt, Peter Bishop, and Richard Steiger in "A
Universal Modular Actor Formalism for Artificial Intelligence," presented at
IJCAI in 1973, and summarized on the actor model's own reference page as
having actors that "may modify their own private state, but can only affect
each other indirectly through messaging," with no shared memory between actors
(Wikipedia contributors, "Actor model,"
[en.wikipedia.org/wiki/Actor_model](https://en.wikipedia.org/wiki/Actor_model),
verified 2026-08-02, used only to confirm the attribution and the isolation
properties, not as a source of the pattern's LLM-specific shape). A second
ancestor is the Bulkhead pattern from reliability engineering, which
partitions resource pools so a failure in one partition cannot exhaust
resources that a different partition depends on (Microsoft, "Bulkhead
pattern," [learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
verified 2026-08-02). Sub-Agent Isolation borrows the private-state and
message-only-communication property from the actor model and the
failure-containment property from Bulkhead, and applies both to a specific
resource that neither ancestor had to reason about, a bounded token budget
that degrades in quality, not only in throughput, as it fills.

## 2. Problem and context

An agent delegates a subtask to another agent, and the subtask involves work
whose intermediate output the delegating agent will never need again. A
subagent reads a dozen files to answer one question. A subagent searches the
web across six queries to check one fact. A subagent runs a test suite and
produces four thousand lines of log output to confirm one pass or fail
verdict. In every one of these cases, only a small fraction of what the
subagent touched is relevant to the caller. The caller needs the verdict, the
fact, or the summary, not the search results, the file contents, or the raw
log.

The failure this pattern prevents is what happens when that intermediate
output is not isolated. If every file the subagent reads and every tool result
it receives is appended directly into the same conversation the caller is
reasoning in, three problems compound. First, the caller's context window
fills with content it will not reference again, which directly reduces how
much of the caller's own actual task remains addressable within a fixed
budget. Second, model quality on long-context tasks degrades unevenly as the
input grows. Nelson Liu and coauthors found that language model performance
"is often highest when relevant information occurs at the beginning or end of
the input context" and drops when the needed fact sits in the middle of a long
input, a result that held even for models built for long context (Nelson F.
Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio
Petroni, Percy Liang, "Lost in the Middle. How Language Models Use Long
Contexts," [arxiv.org/abs/2307.03172](https://arxiv.org/abs/2307.03172),
verified 2026-08-02). A caller whose context is padded with a subagent's raw
exploration is exactly the setup that result warns against, because the
caller's own instructions and the user's actual request now sit somewhere in
the middle of a much longer input. Third, if the subagent's exploration
touches untrusted content, such as a fetched web page or an attacker-supplied
document, and that content is copied verbatim into the caller's own
conversation, any injected instruction hidden inside it is now sitting in the
same context the caller reasons over next turn, rather than contained inside a
subagent whose only channel back to the caller is a validated, structured
result.

The context this pattern requires to be worth adopting has three parts,
matching the same shape the closely related Orchestrator-Worker pattern needs,
because the two are usually deployed together, see dimension 13. There must be
a genuine subtask boundary, meaning the caller can state what it wants back
without walking through every step of how to get there. The subtask's own
working set, the files, search results, and tool calls it needs, must be large
relative to the answer it produces, or isolation buys nothing. And the caller
must be willing to pay a fixed setup cost per delegation, because a fresh
context means reloading a system prompt, shared configuration, and a tool
schema before any of the subtask's own work begins, a cost made concrete in
dimension 3.

## 3. Forces

Some of the weighing below is engineering judgement rather than a sourced
claim, and is presented as reasoning, not as an established fact.

- **Token budget quality versus setup overhead.** Isolation is favored when
  the work discarded from the caller's context is large. It is disfavored when
  the fixed cost of spinning up a fresh context, a new system prompt, a
  reloaded shared configuration file, and a tool schema, is itself comparable
  to the work being delegated. Anthropic's own measurement puts multi-agent
  systems at roughly fifteen times the token usage of a single conversational
  agent for the same task class, which is the price paid for running that
  setup cost once per subagent instead of once per session (Anthropic, "How we
  built our multi-agent research system," verified 2026-08-02).
- **Isolation versus shared ambient context.** Favors isolation for security
  and for context cleanliness, sacrifices whatever the caller already knew
  that it does not think to restate. A subagent that starts from zero cannot
  ask a clarifying question about something the caller took for granted. The
  task descriptor becomes the only channel that context can travel through,
  and an incomplete descriptor produces a subagent that confidently does the
  wrong thing rather than one that pauses to ask.
- **Coordination versus parallel throughput.** Isolation is what makes safe
  parallel fan-out possible at all, because two subagents writing into one
  shared conversation would race and interleave. The price is that isolated
  siblings cannot see each other's findings unless the caller explicitly
  merges them, which is exactly the failure Anthropic documented in early
  versions of its system, where "agents would sometimes duplicate work, leave
  gaps, or fail to find necessary information" until task descriptions were
  written with explicit non-overlapping boundaries (Anthropic, "How we built
  our multi-agent research system," verified 2026-08-02).
- **Least privilege versus subagent capability.** Scoping a subagent's tool
  allowlist down to only what its task needs favors security and limits the
  blast radius of a subagent that reads something adversarial. It sacrifices
  flexibility, since a subagent that discovers it needs one more tool
  mid-task, one that was not granted, has no path to request it inside a
  single synchronous run.
- **Fault containment versus latency.** A subagent that fails, times out, or
  returns malformed output can be caught at the boundary and turned into a
  clearly labeled failed result rather than a crash, matching the Bulkhead
  pattern's own claim that partitioning "helps isolate failures" so "you can
  sustain service functionality for some consumers, even during a failure"
  (Microsoft, "Bulkhead pattern," verified 2026-08-02). The price is that a
  caller waiting synchronously for several isolated subagents to finish is
  bottlenecked by the slowest one, and Anthropic notes its own system runs
  "the lead agent... waiting for each set of subagents to complete" before it
  can proceed, with real-time steering of a running subagent left unsolved
  (Anthropic, "How we built our multi-agent research system," verified
  2026-08-02).
- **Auditability versus boundary opacity.** A single continuous transcript is
  simple to read end to end. Splitting work across isolation boundaries means
  the trace that matters is scattered across several separate conversations
  that a debugging tool must stitch back together, see dimension 16.

## 4. Applicability and non-applicability

Reach for Sub-Agent Isolation when the following hold.

- The delegated work produces a large amount of intermediate output relative
  to the answer the caller needs, such as multi-file research, broad web
  search, or a long-running test or build log.
- The subtask can be stated as a bounded, self-contained instruction. The
  caller can write down what it wants without needing the subagent to ask
  follow-up questions mid-run.
- Several independent subtasks can run in parallel and their combined
  intermediate output would otherwise interleave inside one shared
  conversation, making that conversation unreadable and racy.
- The work touches untrusted or unpredictable content, a fetched document, a
  user upload, an external API response, and the caller wants a validated
  boundary between that content and its own next reasoning step rather than
  raw exposure to it.
- A different, cheaper, or faster model is a better fit for the subtask than
  the model driving the overall conversation, and routing to it is easier to
  reason about as a separate call than as a mid-conversation model switch.
- The subtask's own tool needs are narrower than the caller's, and scoping
  them down at the boundary reduces what could go wrong if the subtask
  misbehaves.

Do not reach for Sub-Agent Isolation in these cases, and the reason for each
one matters more than the rule itself.

- **The subtask is small.** If a fix is two lines and the caller already has
  the file open, the fixed cost of a fresh system prompt, reloaded shared
  configuration, and a new tool schema exceeds any tokens saved by isolating a
  trivial amount of work. Isolation pays for itself only once the discarded
  work outweighs the setup cost.
- **The task is a continuation of the same conversation, not a delegated
  subtask.** When the goal is for a different specialization to take over
  ownership of an ongoing dialogue with the user, a handoff that inherits full
  history is the correct primitive, not isolation. OpenAI's own SDK documents
  handoffs as inheriting "the entire previous conversation history" by design,
  precisely because the receiving agent is meant to continue the same
  conversation rather than answer one bounded question (OpenAI, "Handoffs,"
  verified 2026-08-02).
- **The subagent needs to ask a clarifying question mid-task.** Isolation as
  commonly implemented is a synchronous request and response. There is no path
  for the subagent to pause and ask the caller something it was not told, so a
  task whose correct execution depends on interactive back-and-forth belongs
  inline, not delegated.
- **A single, unbroken audit trail is a compliance requirement.** Isolation
  fragments the record of what happened across several separate contexts.
  Where the requirement is one continuous, gapless transcript, isolation adds
  a reconstruction burden that a single-context flow does not have.
- **The caller's own accumulated context is exactly what the subtask needs.**
  A request like continue editing the file we were just discussing depends on
  state the caller already holds. Forcing that state through an isolated task
  descriptor means re-deriving or restating something the caller already has
  cheap access to, which is wasted work and a place for the restatement to
  drift from the truth.
- **The subagent would need the same delegation tool the caller has.** Giving
  an isolated subagent the ability to spawn further isolated subagents with no
  depth limit opens a runaway recursive-spawn failure mode, covered in
  dimension 11. The correct default is to exclude the spawn tool from a
  subagent's own allowlist unless recursion depth is explicitly bounded.

## 5. Structure

Six participants, named by the role each plays at the boundary.

- **Caller.** The agent that decides to delegate. It holds the full ongoing
  conversation, composes the Task Descriptor, and is the only participant that
  ever sees a Result.
- **Task Descriptor.** The explicit, self-contained input that crosses into
  the subagent. It states the instructions, the output contract the caller
  expects back, and the subagent's Tool Allowlist. Nothing implicit, such as
  as discussed above, is valid inside a Task Descriptor, because the subagent
  has no other source of context.
- **Isolation Boundary.** Not a participant with behavior of its own, but the
  seam the pattern is named after. Everything on the Subagent side of the
  boundary is invisible to the Caller unless it crosses out through a Result,
  and everything the Caller holds is invisible to the Subagent unless it
  crosses in through the Task Descriptor.
- **Subagent.** Runs independently once spawned. It begins with its own
  system prompt, its own copy of any shared configuration the framework
  reloads per agent, and the Task Descriptor, and nothing else. Its own
  working memory, its tool call history, and its reasoning trace are private
  to it for the duration of the run.
- **Tool Allowlist.** A scoped subset of the tools the Caller itself could
  call, attached to the Subagent at spawn time. By default it excludes the
  delegation tool itself, so a Subagent cannot spawn further Subagents unless
  a framework explicitly opts a task into bounded recursion.
- **Result Extractor.** The function or return path inside the Subagent that
  converts its internal, possibly large working state into the small,
  validated object that is allowed to cross back. A well-formed pattern
  instance never lets the Subagent's raw scratch memory cross the boundary
  directly, only what the Result Extractor explicitly produces.

The dependency direction is one-way per crossing. A Task Descriptor flows
Caller to Subagent and is never mutated afterward by either side. A Result
flows Subagent to Caller and is the only thing the Subagent contributes back.
Unlike Factory Method's Creator-to-Product relationship, there is no ongoing
reference held across the boundary once the Subagent finishes. The
relationship is transactional, not structural.

## 6. ASCII structure diagram

```
                          ISOLATION BOUNDARY
                                  |
   +------------------------+    |    +------------------------+
   |         Caller         |    |    |        Subagent        |
   |------------------------|    |    |------------------------|
   | full conversation      |    |    | fresh system prompt     |
   | history (private)      |    |    | own scratch memory      |
   | own tool set (private) |    |    | own Tool Allowlist       |
   |                        |    |    | (spawn tool excluded)    |
   | compose                | -->|--> | receive Task Descriptor  |
   |   Task Descriptor      | in |    |                          |
   |                        |    |    |  tool call 1  (private)  |
   | receive Result         | <--|<-- |  tool call 2  (private)  |
   |   (validated, compact) |out |    |  tool call N  (private)  |
   +------------------------+    |    |  Result Extractor        |
                                  |    +------------------------+

   Only the Task Descriptor and the Result cross the boundary.
   Everything else stays private to its own side, permanently.
```

## 7. Dynamics

The runtime flow has one property worth stating plainly, the same property
that separates it from a handoff. The Subagent never sees the Caller's
conversation history unless that history is explicitly folded into the Task
Descriptor's own text, and the Caller never sees the Subagent's tool calls
unless they are explicitly summarized into the Result.

```
Caller               Boundary          Subagent A       Subagent B
  |                      |                  |                |
  |-- compose Task A --->|                  |                |
  |-- compose Task B --->|                  |                |
  |                      |-- spawn A ------>|                |
  |                      |     (fresh ctx)  |                |
  |                      |-- spawn B ----------------------->|
  |                      |                  |    (fresh ctx) |
  |                      |                  |                |
  |                      |   (private tool calls, invisible  |
  |                      |    to the caller and to the        |
  |                      |    sibling subagent, on both sides)|
  |                      |                  |                |
  |                      |<-- Result A -----|                |
  |                      |<-- panic / throw ----------------|
  |                      |   caught at the boundary, wrapped  |
  |                      |   as a failed Result, never raised |
  |                      |   into the caller's own context    |
  |<-- [okA, failB] -----|                  |                |
  |                      |                  |                |
  |  caller's context grows by two small Result objects,      |
  |  never by A's or B's private tool logs or scratch state   |
```

Two timing properties are worth naming. First, the fixed setup cost, loading a
system prompt and any shared configuration file into the fresh context, is
paid once per spawn, before the subtask's own work begins, and this is where
most of the fifteen-times token multiplier Anthropic reports comes from when a
task is decomposed into many small subagents rather than a few large ones
(Anthropic, "How we built our multi-agent research system," verified
2026-08-02). Second, the join at the end is synchronous in the common
implementation, meaning the caller cannot proceed, and cannot redirect a
running subagent, until every subagent it is waiting on has either returned or
been caught as a failure. Concurrent execution across independent subagents is
supported, mid-run steering of one subagent by the caller is not, in every
production system this entry could verify.

## 8. Implementation variants

**In-process conversation array isolation.** The simplest and most common
form. A single process holds two or more separate message-list objects, one
per agent, and a spawn function creates a new list rather than appending to
the existing one. Claude Code's subagent facility works this way, with the
framework noting that a spawned subagent "loads CLAUDE.md and the same MCP and
skill setup, but starts without your conversation history or the main
session's auto memory" (Anthropic, "Explore the context window,"
[code.claude.com/docs/en/context-window](https://code.claude.com/docs/en/context-window),
verified 2026-08-02). This variant provides context isolation only, with no
process or permission isolation unless combined with the variants below.

**Tool-call boundary, agents-as-tools.** The subagent is invoked the same way
any function tool is invoked, with a defined JSON input schema and a defined
output schema, and the calling model never sees anything beyond that contract.
OpenAI's Agents SDK documents this directly. "The state options configure the
nested agent run started by the tool call; the parent run's conversation state
is not inherited automatically," unless the same session object is explicitly
shared across both agents (OpenAI, "Tools,"
[openai.github.io/openai-agents-python/tools](https://openai.github.io/openai-agents-python/tools/),
verified 2026-08-02). This is the variant that most cleanly matches this
entry's structure, because the Task Descriptor and Result are literally a
typed function signature.

**Handoff with an opt-in isolation filter.** The opposite default, full
history inheritance, can be dialed toward isolation without switching
primitives entirely. The same SDK supports an input_filter function on a
handoff that receives the full HandoffInputData and returns a trimmed version,
plus a nested-history mode that compacts prior turns into a summarized
wrapper rather than dropping or forwarding them verbatim (OpenAI, "Handoffs,"
verified 2026-08-02). This variant is useful when the choice between
continuation and isolation is not binary in a given application, but it is
worth naming as a distinct implementation path rather than assuming handoffs
and isolation are interchangeable, since the default behavior of a handoff is
the opposite of isolation.

**Actor-style message-passing isolation.** Each subagent is modeled as an
actor, a unit of private state that communicates only through discrete
asynchronous messages, with no shared mutable memory reachable from outside
it, matching Hewitt's original formulation where actors "can only affect each
other indirectly through messaging" (Wikipedia contributors, "Actor model,"
verified 2026-08-02). Goroutines communicating over channels, Erlang or
Elixir processes, and Akka actors are all concrete instances of this variant,
and it is the natural implementation choice in a language with first-class
concurrency primitives and no shared-memory default, see the Go example in
this entry's code section.

**Process, container, or sandbox isolation.** The subagent's own tool
execution, not just its conversation state, runs inside a distinct operating
system process, container, or restricted execution environment, so a
compromised or misbehaving subagent cannot read the caller's environment
variables, filesystem, or credentials even if it wanted to. This is the
variant to reach for when the subagent executes model-authored code or
touches genuinely untrusted input, and it composes with, rather than replaces,
context isolation, see dimension 17.

**Permission-scoped tool registries.** Independent of how conversation state
is isolated, a framework maintains a separate allowlist of callable tools per
agent instance, checked at call time. This is the variant demonstrated in
every code example in this entry, where a subagent that attempts a tool
outside its allowlist is denied rather than silently permitted, and it is the
mechanism that turns context isolation into a security boundary rather than
only a token-budget optimization.

**Shared-session opt-in.** Several frameworks default to isolation but expose
an explicit knob to share memory selectively, such as passing the same
session object to both a parent and a nested agent run. Treating this as a
dial rather than a binary switch matters, because a caller can isolate a
subagent's tool exploration while still sharing a narrow slice of state, such
as a running total or a user identifier, without collapsing the boundary
entirely.

## 9. Known production uses

**Claude Code subagents, Anthropic.** Every subagent spawned inside a Claude
Code session receives its own context window, its own system prompt, and an
independently configured tool allowlist, and by default cannot spawn further
subagents, preventing unbounded recursion. The framework's own documentation
states subagents "help you preserve context by keeping exploration and
implementation out of your main conversation" and "enforce constraints by
limiting which tools a subagent can use" (Anthropic, "Create custom
subagents," [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents),
verified 2026-08-02). A worked numeric example in Anthropic's own context
window documentation shows a subagent reading roughly six thousand one hundred
tokens of files across several tool calls, none of which touch the caller's
context, and returning a four hundred and twenty token summary, described in
the documentation as "the context savings" (Anthropic, "Explore the context
window," verified 2026-08-02).

**Anthropic's multi-agent research system.** The system behind Claude's
research feature runs a lead agent that spawns several subagents in parallel,
each with an independent context window exploring a different facet of a
research question before results are condensed back to the lead agent.
Anthropic reports a ninety point two percent improvement over a single-agent
baseline on an internal research evaluation, attributing the gain to
subagents that "facilitate compression by operating in parallel... exploring
different aspects of the question simultaneously before condensing the most
important tokens for the lead research agent," at a measured cost of roughly
fifteen times the token usage of a single-agent chat (Anthropic, "How we
built our multi-agent research system," verified 2026-08-02).

**OpenAI Agents SDK, agents-as-tools.** Applications built on the SDK's
Agent.as_tool primitive run a specialist agent as a nested, isolated run
invoked the same way any other tool is invoked from the calling agent's
model. The SDK's own documentation is explicit that this nested run's
conversation state "is not inherited automatically" from the parent, and
supports a custom_output_extractor argument so a developer can transform or
validate what crosses back to the caller before it is trusted (OpenAI,
"Tools," verified 2026-08-02). This is the pattern's tool-call-boundary
variant in production use across applications built on the SDK.

## 10. Consequences

Positive.

- The caller's context budget is preserved for the parts of a conversation it
  will actually reason over again, rather than being consumed by intermediate
  exploration it will never reference.
- Parallel subagents can explore independent parts of a problem without
  racing or interleaving inside one shared conversation, which is what makes
  safe concurrent delegation possible at all.
- A subagent's failure, whether a thrown exception, a timeout, or malformed
  output, can be caught at the boundary and turned into a labeled failed
  result, so the caller degrades rather than crashing or absorbing corrupted
  state, matching the Bulkhead pattern's own containment guarantee.
- Least-privilege tool scoping becomes natural at the boundary, since a Task
  Descriptor's Tool Allowlist is a deliberate, reviewable decision made once
  per delegation rather than an implicit inheritance of everything the caller
  could do.
- Subagents can be specialized, reused across different callers, and routed
  to a different, cheaper, or faster model than the one driving the overall
  conversation.

Negative.

- The fixed cost of a fresh context, a reloaded system prompt, and shared
  configuration is paid once per spawn, and Anthropic's own measurement puts
  the resulting overhead at roughly fifteen times a single-agent baseline for
  the same task class, which is not free and must be weighed against the
  work saved.
- Ambient context the caller already held must be explicitly restated into
  the Task Descriptor, and anything the caller forgets to restate is simply
  unavailable to the subagent, producing confidently wrong output rather than
  a clarifying question.
- Synchronous joins on parallel subagents bottleneck the caller on the
  slowest one, and mid-run steering of a running subagent is unsolved in
  every production system this entry could verify.
- Isolated siblings cannot see each other's findings, which without explicit,
  non-overlapping task scoping produces duplicated work or coverage gaps, a
  failure Anthropic documents as an early production issue in its own system.
- A single continuous debugging trace becomes several fragmented traces that
  must be stitched back together across the boundary, see dimension 16.

## 11. Failure modes and misuse

**The confidently wrong subagent.** Symptom, a subagent asked to fix the bug
we discussed returns a plausible-sounding but incorrect answer, or asks what
bug, rather than producing an error. Cause, the caller assumed conversational
continuity that isolation does not provide, and the Task Descriptor never
restated what the bug actually was. Fix, treat the Task Descriptor as the only
channel of context and audit it as if the subagent has read nothing else,
because it has not.

**Duplicated work between parallel siblings.** Symptom, two subagents run in
parallel and independently perform the same file read, the same web search, or
the same computation, wasting the token budget isolation was meant to
preserve. Cause, task boundaries were not made explicitly non-overlapping, and
isolated siblings have no visibility into each other's progress to notice the
overlap themselves. Fix, write each Task Descriptor with an explicit scope
boundary, matching Anthropic's own documented remedy of giving "each subagent
an objective, an output format, guidance on the tools and sources to use, and
clear task boundaries" (Anthropic, "How we built our multi-agent research
system," verified 2026-08-02).

**Delegation overhead exceeding the work delegated.** Symptom, a small,
cheap fix costs more in tokens and latency when routed through a subagent
than it would have cost handled inline by the caller. Cause, the fixed setup
cost of a fresh context and reloaded configuration is comparable to or larger
than the work being delegated. Fix, reserve isolation for subtasks whose
discarded intermediate output outweighs the setup cost, and batch several
small related subtasks into one subagent call rather than spawning one
subagent per trivial step.

**Permission leakage through a shared tool allowlist.** Symptom, a subagent
that reads an adversarial web page or document goes on to call a sensitive
tool it should never have had access to, such as sending an email or writing
to a database, because a prompt injected inside the untrusted content steered
it. Cause, context isolation was implemented without permission isolation, so
the subagent inherited the same broad tool allowlist as its caller. Fix, scope
the Tool Allowlist independently of, and more restrictively than, context
isolation, granting only what the specific task needs, matching the general
guidance against granting unchecked autonomy described under Excessive Agency
in the OWASP Top 10 for LLM applications (OWASP Foundation, "OWASP Top 10 for
Large Language Model Applications,"
[owasp.org/www-project-top-10-for-large-language-model-applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/),
verified 2026-08-02).

**Unhandled fault crossing the boundary.** Symptom, a subagent that throws an
exception, times out, or returns a malformed result silently corrupts the
caller's downstream state, either by crashing the caller outright or by the
caller trusting an empty or partial result as if it were a valid one. Cause,
the boundary was not implemented with explicit fault handling, so a failure
propagated as if it were success. Fix, wrap every subagent invocation in
explicit failure handling, such as a settled-promise collection or a recover
guard at the spawn point, and validate a returned Result against its expected
shape before the caller acts on it, matching the failure-containment intent
of the Bulkhead pattern.

**Isolation and continuation confused for one another.** Symptom, a
developer reaches for a full-history handoff when isolation was wanted, and a
supposedly fresh reviewer agent starts referencing details from earlier in
the conversation that the developer intended to keep hidden from it, or the
reverse, an isolated subagent is used where the user expected a specialist to
simply continue the same conversation and it instead starts from nothing.
Cause, the two primitives, full-history handoff and isolated tool-call
delegation, were treated as interchangeable when their default behaviors are
opposites. Fix, choose the primitive that matches intent explicitly, a
handoff when a specialist should take over ownership of the ongoing
conversation, an isolated call when a bounded subtask should be answered
without exposing everything that came before it.

**Runaway recursive spawning.** Symptom, token or cost usage grows
unexpectedly, or the system appears to hang, because a subagent was granted
the same delegation tool as its caller and began spawning its own subagents,
which spawned further subagents. Cause, no recursion guard or depth limit was
applied to the delegation tool itself when it was included in a subagent's
Tool Allowlist. Fix, exclude the delegation tool from a subagent's default
allowlist, matching the default behavior Claude Code documents for its own
built-in subagents, and where recursion is genuinely needed, bound it with an
explicit, enforced depth counter passed through the Task Descriptor.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Sub-Agent Isolation | Full-history Handoff | Shared session or shared memory | Naive shared-transcript delegation | Process or container sandbox |
|---|---|---|---|---|---|
| Caller context growth | Low. Only a compact Result is appended | High. Full history is inherited by design | Medium. Grows by whatever both sides choose to share | High. All subagent tool output lands in the shared transcript | Low, same as isolation, plus stronger security |
| Fixed setup cost per delegation | High. Fresh system prompt and configuration reload every spawn | Low. The receiving agent reuses the existing conversation state | Medium. Some reload, plus shared-state synchronization | Low. No separate context to spin up | High. Isolation cost plus process or container startup |
| Continuity of ambient context | Poor. Must be explicitly restated in the Task Descriptor | Strong. That is its purpose | Medium. Only the explicitly shared slice carries over | Strong, at the cost of everything else in this table | Poor, same as isolation |
| Safe parallel fan-out | Strong. Isolated siblings cannot race each other | Not addressed. Handoffs are sequential, one owner at a time | Risky. Concurrent writers to shared state need explicit locking | Poor. Concurrent writers race in the same transcript | Strong, plus resistant to a compromised subagent |
| Fault containment | Strong. A failure is caught and returned as a labeled result | Weak. A failing specialist's failure is now the conversation's failure | Weak. A crash mid-write can leave shared state partially updated | Weak. A crash pollutes the one shared transcript everyone reads | Strong, plus contains a compromised process, not only a thrown error |
| Least-privilege tool scoping | Natural. A Tool Allowlist is attached per delegation | Not addressed. The receiving agent typically keeps the same tool access | Possible but not automatic | Not addressed. Every participant shares one tool surface | Strongest. Enforced at the operating-system boundary, not only in the framework |
| Auditability of one continuous trace | Poor. The record is split across boundaries | Strong. One conversation, one trace | Medium. Shared-state changes are traceable, private state is not | Strong, one transcript, at the cost of everything above | Poor, same as isolation |
| Mid-task interactive steering | Poor. The common implementation is synchronous request and response | Strong. The user is talking to the active agent directly | Medium, depends on how shared state is exposed | Medium, the user can technically read the shared transcript | Poor, same as isolation |

Reading of the table. Sub-Agent Isolation wins wherever context cleanliness,
safe parallelism, and fault containment matter more than continuity and setup
cost. Full-history Handoff wins wherever the goal is a specialist taking over
one continuous conversation with a person. Shared session or shared memory
is the middle ground for the cases where isolation is too strict and a
handoff's full inheritance is too loose. Naive shared-transcript delegation,
appending everything into one conversation with no boundary at all, is the
default a team falls into by not choosing a pattern, and this table is the
argument for not staying there once subagents run in parallel or touch
untrusted content. Process or container sandboxing is what isolation upgrades
to when the concern is not only token budget but a genuinely compromised or
untrusted subagent.

## 13. Related and incompatible patterns

- **Orchestrator-Worker.** The topology this mechanism most often implements.
  Orchestrator-Worker describes who decomposes a task and delegates it. Sub-
  Agent Isolation describes what crosses the boundary once that delegation
  happens. A system can use the orchestrator-worker topology with a shared
  transcript instead of isolation, which is the naive-delegation column in
  dimension 12, so the two patterns are related but not the same claim.
- **Parallelization.** Isolation is the precondition that makes safe parallel
  fan-out possible, because concurrent workers writing into one shared
  conversation would race. Any pattern that runs several LLM calls
  concurrently and expects correct results needs isolation, an explicit merge
  step, or both.
- **Routing.** A router selects exactly one specialist to handle a request.
  Routing itself does not decide whether the selected specialist receives
  full history or a bounded task, that choice is the handoff-versus-isolation
  decision layered on top of routing, and the two compose rather than one
  implying the other.
- **Function Calling.** The tool-call boundary variant of this pattern, see
  dimension 8, is literally an application of function calling, where the
  function being called happens to be another agent rather than a
  deterministic tool. The input schema and output schema disciplines that
  apply to function calling apply directly to a Task Descriptor and a Result.
- **Model Context Protocol.** MCP standardizes how a tool is described and
  invoked across different agent frameworks. Isolation decides who is allowed
  to invoke which tool and with what conversational context behind them. The
  two are orthogonal and compose cleanly, an MCP-described tool can sit
  inside one subagent's allowlist and be entirely absent from another's.
- **Actor model.** The concurrency ancestor this pattern's message-passing
  implementation variant draws from directly, see dimension 8. Where the
  actor model reasons about arbitrary concurrent computation, this pattern
  narrows the same private-state, message-only discipline to one specific
  resource, a bounded and quality-sensitive token budget.
- **Bulkhead.** The reliability ancestor this pattern's fault-containment
  property draws from. Bulkhead partitions resource pools so one consumer's
  failure cannot exhaust resources a different consumer depends on. This
  pattern applies the same partitioning discipline to context and to failure
  propagation between a caller and a subagent.
- **Full-history Handoff, at the same delegation point.** Not incompatible
  across a system, since a real application often uses both, an isolated call
  for a bounded research step and a handoff for transferring ownership of an
  ongoing dialogue to a specialist. But the two are alternate choices for the
  same single delegation decision, never both at once for the same crossing,
  because a Task Descriptor that also somehow contains the full prior
  conversation history has stopped being isolated.
- **Unscoped shared mutable state.** Directly conflicts with the isolation
  guarantee. Passing a live, mutable reference to a caller's own object into
  a subagent instead of a copy defeats the boundary, since a mutation inside
  the subagent then silently bleeds back into the caller's state without
  crossing through a validated Result. This is a real implementation bug
  class, demonstrated as a leak test in this entry's Python example, not only
  a theoretical concern.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently does everything inline
in one conversation.

1. Find a point in the caller's own flow where it performs exploratory or
   tool-heavy work whose intermediate output it never references again once
   the task is answered, such as reading several files to answer one
   question.
2. Write down what the caller actually needs back from that work as an
   explicit, structured Result shape, before touching how the work is done.
3. Extract the exploratory work into a function that accepts a self-contained
   Task Descriptor rather than reaching into the caller's own state, and
   returns only the Result shape from step 2. At this point the code is
   already isolated even if it still runs in-process and synchronously.
4. Attach a Tool Allowlist to the extracted function's own tool access,
   scoped to only what that specific work needs, narrower than whatever the
   caller itself is permitted.
5. Wrap the call site in explicit fault handling, so a thrown exception or a
   malformed return becomes a labeled failed Result instead of propagating
   into the caller's own error path unexamined.
6. If the same extracted function is called for several independent inputs,
   run those calls concurrently and collect results with a settled-style
   collection rather than sequential awaits, since the isolation already in
   place from step 3 is what makes that concurrency safe.
7. Add the leak test and the contract test from dimension 15 so that a future
   change cannot silently reintroduce a shared mutable reference across the
   boundary or a Result shape the caller does not actually validate.

Removing the pattern when it stops earning its place. The signal is usually
that the fixed setup cost per delegation now dominates the actual work being
delegated, or that the caller keeps needing to restate so much ambient
context into the Task Descriptor that the restatement itself has become the
bulk of the cost.

1. Confirm the subtask is genuinely small relative to the setup overhead
   before collapsing the boundary, not merely that it feels like overhead.
2. Inline the extracted function's body back into the caller's own flow,
   replacing the Task Descriptor parameter with direct access to the caller's
   already-available state.
3. Fold the Tool Allowlist scoping into the caller's own tool set if the
   narrower scoping is no longer providing a security benefit worth
   maintaining separately, or keep it as an inline permission check if it
   still is, since permission scoping and context isolation are separable, see
   dimension 1.
4. Remove the now-redundant fault-handling wrapper only if the caller's own
   error handling already covers the same failure modes the boundary was
   catching, never remove it purely to simplify the code.
5. Delete the Result shape's validation only after confirming nothing else in
   the system still depends on that shape as a contract, since other callers
   sometimes accumulate around a well-defined Result type even after the
   original caller stops needing isolation.

## 15. Testing and verification

Some of the guidance below is drawn from engineering practice rather than a
sourced specification, and is presented as practice, not as an established
fact.

Easier because of the pattern.

- The boundary is a natural seam for a test double. A caller's own logic can
  be tested against a stub subagent that returns a fixed Result, with no
  network call and no model invocation, because the contract between the two
  sides is already an explicit, typed interface rather than an implicit
  shared conversation.
- A subagent's own internal logic can be tested in isolation from the caller
  entirely, since by construction it never reaches into the caller's state.

Harder because of the pattern.

- An end-to-end trace of what actually happened requires stitching together
  the caller's transcript and each subagent's separate transcript, since no
  single log captures the whole run, see dimension 16.
- A bug caused by an incomplete Task Descriptor, where the subagent was
  simply never told something it needed, does not surface as a crash, it
  surfaces as a plausible but wrong answer, which unit tests catch only if
  they specifically assert on content rather than on success or failure.

Techniques that apply.

- **Contract test on the Task Descriptor and Result shapes.** Assert that a
  fixed, self-contained Task Descriptor produces a Result matching the
  expected schema, independent of whatever model or tool implementation
  backs the subagent, so the contract itself is pinned down before the
  implementation behind it changes.
- **Fault injection at the boundary.** Force the subagent path to throw, time
  out, or return a malformed value, and assert the caller degrades to a
  labeled failed Result rather than crashing or silently proceeding with
  corrupted state. This is the direct test of the Bulkhead-style guarantee
  described in dimension 10.
- **Leak test on mutable inputs.** Assert that any mutable object passed into
  a subagent is not the same reference the caller continues to hold, and that
  a mutation performed inside the subagent's own scope is not observable on
  the caller's side afterward. This entry's Python example demonstrates
  exactly this assertion using a deep copy and an identity check.
- **Tool allowlist enforcement test.** Assert that a subagent attempting a
  tool outside its granted allowlist is denied rather than silently permitted,
  and that the denial is what crosses back as a failed Result rather than the
  tool call succeeding regardless of scope.
- **Concurrency correctness test for parallel fan-out.** When several
  subagents run concurrently, assert there is no data race and no shared
  mutable state being written by more than one subagent at a time, which
  matters most in the actor-style implementation variant, see the Go example
  in this entry, where the language's own race detector can be run against
  the test.

## 16. Observability signals

What to record at the boundary itself, since neither the caller's own logs
nor the subagent's own logs alone tell the full story.

- On every spawn, a log line or span attribute recording the Task Descriptor
  size, in tokens or characters, and the granted Tool Allowlist, so it is
  possible to audit what a subagent was told and what it was permitted to do
  after the fact.
- On every return, the tokens consumed inside the subagent's own private
  context against the size of the Result that actually crossed back. This
  compression ratio is the single most direct signal that isolation is
  paying for itself. Anthropic's own documented example shows roughly six
  thousand one hundred tokens read inside a subagent against a four hundred
  and twenty token Result returned, a ratio worth tracking as a baseline
  (Anthropic, "Explore the context window," verified 2026-08-02).
- A counter of tool calls made inside each subagent, labeled by tool name,
  which is the only place that count is visible, since none of it appears in
  the caller's own trace.
- A counter of denied tool calls, where a subagent attempted something
  outside its allowlist, labeled by the denied tool. A rising count here
  points either at a misconfigured allowlist or at a subagent being steered
  toward tools it should not want, which is itself a security signal, see
  dimension 17.
- A counter and a duration histogram of failed Results, labeled by failure
  cause, timeout, thrown exception, or malformed output, so a fault
  containment pattern that is silently failing often does not read as a
  healthy system just because the caller never crashes.
- For any recursive-spawn-capable configuration, a live gauge of current
  spawn depth, so a runaway recursion, described in dimension 11, is visible
  before it exhausts a budget rather than only after.

A healthy instance on a dashboard shows a compression ratio well above one,
meaning subagents genuinely discard far more than they return, a low and
stable denied-tool-call rate, and a failed-Result rate that tracks the
underlying task's real difficulty rather than climbing on its own. A failing
instance shows a compression ratio near one, meaning isolation is not
providing a benefit and everything explored inside the subagent is being
funneled straight back through anyway, or shows a duration outlier
concentrated on one particular subagent type, which usually localizes a slow
or looping tool inside that specific subtask without needing to read any of
its private transcript directly.

## 17. Security and privacy implications

Context isolation on its own is a token-budget and cleanliness mechanism, not
a security boundary, and treating it as one is the most common analytical
mistake made about this pattern. Three genuine implications follow once tool
access and untrusted content enter the picture.

**Blast radius of a manipulated subagent.** A subagent that reads untrusted
content, a fetched web page, a document a user uploaded, an API response from
an external service, can be steered by an instruction hidden inside that
content, a risk the OWASP Top 10 for Large Language Model Applications
describes under Excessive Agency, warning that "granting LLMs unchecked
autonomy to take action can lead to unintended consequences, jeopardizing
reliability, privacy, and trust" (OWASP Foundation, "OWASP Top 10 for Large
Language Model Applications," verified 2026-08-02). A Tool Allowlist scoped
to the minimum a specific subtask needs, separate from and narrower than
whatever the caller itself could do, is what actually limits what a
manipulated subagent can achieve, not the mere fact that its conversation is
in a separate context object.

**The Result still needs to be treated as data, not as a command.** Isolation
prevents a manipulated subagent's raw tool output and reasoning trace from
reaching the caller directly, but the caller still receives and acts on the
subagent's final Result. If an injected instruction inside untrusted content
manages to influence what the subagent writes into its own Result, and the
caller trusts that Result uncritically, the injection has crossed the
boundary anyway, only later and in a smaller, more targeted form. The same
discipline applied to any other tool output, treating returned content as
untrusted data to be validated against an expected shape rather than as an
instruction to follow, applies to a subagent's Result.

**Context isolation does not imply process isolation.** A subagent whose
conversation is a separate object inside the same process still shares that
process's ambient execution environment, its filesystem access, its
environment variables, and any credentials reachable from within it, unless
process or container isolation, dimension 8's heaviest variant, is applied on
top. Where a subagent executes model-authored code, or where the untrusted
content it handles could plausibly attempt to escape the conversational
boundary and act directly on the underlying system, context isolation and
process isolation are complementary controls, not substitutes for one
another, and relying on the former where the latter is actually required
leaves a real gap.

On privacy the pattern is largely neutral by construction, since it exists to
reduce what a caller sees, not to expand it, with one practical caveat worth
naming. The observability guidance in dimension 16 recommends recording Task
Descriptor size and tool call counts. Where a Task Descriptor or a tool call
argument carries personal or otherwise sensitive data, that logging surface
should be treated with the same retention and access controls as any other
record containing that data, rather than assumed to be safe simply because it
sits at an internal system boundary rather than in a user-facing transcript.

## Code examples

Three languages where the pattern's mechanics are demonstrated in genuinely
different ways. TypeScript shows the tool-call boundary variant with a
concurrent, fault-tolerant caller. Python adds an explicit leak test proving
a subagent cannot mutate the caller's own live state, and runs its
concurrent dispatch through asyncio. Go shows the actor-style variant
directly, with each subagent as its own goroutine communicating only over a
channel and a panic recovered at the boundary rather than crashing the
caller. Java, Rust, and Swift are omitted, not because the pattern does not
translate, but because none of them adds a materially different isolation
mechanic beyond what these three already cover, actor-style channel
isolation in Go, structural typed contracts in TypeScript, and explicit copy
discipline in Python.

### TypeScript

```typescript
interface TaskDescriptor {
  readonly id: string;
  readonly instructions: string;
  readonly allowedTools: ReadonlySet<string>;
}

interface Result {
  readonly taskId: string;
  readonly status: "ok" | "failed";
  readonly summary: string;
  readonly toolCallCount: number;
}

class ToolDeniedError extends Error {
  constructor(tool: string) {
    super(`tool '${tool}' is not in this subagent's allowlist`);
  }
}

// A subagent's own scratch state. Never exposed to the caller and never
// initialized from the caller's conversation history.
class SubagentContext {
  private readonly scratch: string[] = [];
  private toolCalls = 0;

  callTool(name: string, allowed: ReadonlySet<string>): string {
    if (!allowed.has(name)) throw new ToolDeniedError(name);
    this.toolCalls++;
    const output = `${name}() -> found 400 tokens of raw data`;
    this.scratch.push(output);
    return output;
  }

  toolCallCount(): number {
    return this.toolCalls;
  }
}

// The isolation boundary. Only the TaskDescriptor crosses in and only a
// Result crosses out; the SubagentContext never leaves this function.
async function runIsolated(task: TaskDescriptor): Promise<Result> {
  const ctx = new SubagentContext();
  try {
    if (task.instructions.includes("send_email")) {
      ctx.callTool("send_email", task.allowedTools);
    }
    ctx.callTool("search_files", task.allowedTools);
    ctx.callTool("read_file", task.allowedTools);
    return {
      taskId: task.id,
      status: "ok",
      summary: `[${task.id}] resolved: ${task.instructions.slice(0, 40)}`,
      toolCallCount: ctx.toolCallCount(),
    };
  } catch (err) {
    return {
      taskId: task.id,
      status: "failed",
      summary: (err as Error).message,
      toolCallCount: ctx.toolCallCount(),
    };
  }
}

async function orchestrate(tasks: TaskDescriptor[]): Promise<Result[]> {
  // Fault containment: one rejected settle never aborts the others.
  const settled = await Promise.allSettled(tasks.map(runIsolated));
  return settled.map((s, i) =>
    s.status === "fulfilled"
      ? s.value
      : { taskId: tasks[i].id, status: "failed", summary: String(s.reason), toolCallCount: 0 },
  );
}

async function main(): Promise<void> {
  const readOnly = new Set(["search_files", "read_file"]);
  const tasks: TaskDescriptor[] = [
    { id: "A", instructions: "summarize src/auth.ts", allowedTools: readOnly },
    // Task B tries to escalate past its allowlist; the boundary denies it
    // instead of letting a broad tool set leak into an isolated subtask.
    { id: "B", instructions: "send_email the summary to finance", allowedTools: readOnly },
  ];
  const results = await orchestrate(tasks);
  for (const r of results) {
    console.log(`${r.taskId}: ${r.status} (${r.toolCallCount} tool calls) - ${r.summary}`);
  }
}

void main();
```

Verified with tsc --noEmit --strict --target es2022 --lib es2022
--moduleResolution bundler --module esnext --types node against TypeScript 5,
zero errors, and run under tsx, producing an ok line for task A with two
tool calls and a short summary of the auth file, followed by a failed Result
for task B naming the denied tool.

### Python

```python
import asyncio
import copy
from dataclasses import dataclass


@dataclass(frozen=True)
class TaskDescriptor:
    task_id: str
    instructions: str
    allowed_tools: frozenset[str]


@dataclass
class Result:
    task_id: str
    status: str
    summary: str
    tool_call_count: int


class ToolDeniedError(Exception):
    pass


class SubagentContext:
    # Fresh per call. Never constructed from the caller's own state.
    def __init__(self) -> None:
        self.scratch: list[str] = []
        self.tool_calls = 0

    def call_tool(self, name: str, allowed: frozenset[str]) -> str:
        if name not in allowed:
            raise ToolDeniedError(f"tool '{name}' is not in this subagent's allowlist")
        self.tool_calls += 1
        output = f"{name}() -> found 400 tokens of raw data"
        self.scratch.append(output)
        return output


async def run_isolated(task: TaskDescriptor) -> Result:
    ctx = SubagentContext()
    try:
        if "send_email" in task.instructions:
            ctx.call_tool("send_email", task.allowed_tools)
        ctx.call_tool("search_files", task.allowed_tools)
        ctx.call_tool("read_file", task.allowed_tools)
        return Result(task.task_id, "ok", f"[{task.task_id}] resolved: {task.instructions[:40]}", ctx.tool_calls)
    except ToolDeniedError as exc:
        return Result(task.task_id, "failed", str(exc), ctx.tool_calls)


async def orchestrate(tasks: list[TaskDescriptor]) -> list[Result]:
    raw = await asyncio.gather(*(run_isolated(t) for t in tasks), return_exceptions=True)
    out: list[Result] = []
    for task, r in zip(tasks, raw):
        out.append(r if isinstance(r, Result) else Result(task.task_id, "failed", str(r), 0))
    return out


def leak_test(shared_input: list[str]) -> list[str]:
    # A subagent must receive a copy, never the caller's own live object,
    # so its mutations cannot bleed back across the boundary.
    private_copy = copy.deepcopy(shared_input)
    private_copy.append("subagent-only note")
    return private_copy


async def main() -> None:
    read_only = frozenset({"search_files", "read_file"})
    tasks = [
        TaskDescriptor("A", "summarize src/auth.py", read_only),
        TaskDescriptor("B", "send_email the summary to finance", read_only),
    ]
    for r in await orchestrate(tasks):
        print(f"{r.task_id}: {r.status} ({r.tool_call_count} tool calls) - {r.summary}")

    caller_notes = ["draft v1"]
    subagent_notes = leak_test(caller_notes)
    assert subagent_notes is not caller_notes
    assert "subagent-only note" not in caller_notes
    print(f"caller notes untouched: {caller_notes}")


if __name__ == "__main__":
    asyncio.run(main())
```

Compiled with python3 -m py_compile and run directly under Python 3.14,
producing the same two Result lines as the TypeScript example plus a third
line confirming the caller's notes list still holds only its original entry,
proving the leak test passes.

### Go

```go
package main

import (
	"fmt"
	"strings"
)

// TaskDescriptor is the only input that crosses into a subagent.
type TaskDescriptor struct {
	ID           string
	Instructions string
	AllowedTools map[string]bool
}

// Result is the only output that crosses back out.
type Result struct {
	TaskID        string
	Status        string
	Summary       string
	ToolCallCount int
}

// subagentContext is private to one goroutine. It is never shared and
// never touched by the caller or by any sibling subagent.
type subagentContext struct {
	scratch   []string
	toolCalls int
}

func (c *subagentContext) callTool(name string, allowed map[string]bool) string {
	if !allowed[name] {
		panic(fmt.Sprintf("tool %q is not in this subagent's allowlist", name))
	}
	c.toolCalls++
	out := fmt.Sprintf("%s() -> found 400 tokens of raw data", name)
	c.scratch = append(c.scratch, out)
	return out
}

// runIsolated is the boundary. It recovers a panic instead of letting it
// crash the caller, turning it into a failed Result on the channel.
func runIsolated(task TaskDescriptor, out chan<- Result) {
	ctx := &subagentContext{}
	defer func() {
		if r := recover(); r != nil {
			out <- Result{task.ID, "failed", fmt.Sprint(r), ctx.toolCalls}
		}
	}()
	if strings.Contains(task.Instructions, "send_email") {
		ctx.callTool("send_email", task.AllowedTools)
	}
	ctx.callTool("search_files", task.AllowedTools)
	ctx.callTool("read_file", task.AllowedTools)
	out <- Result{task.ID, "ok", fmt.Sprintf("[%s] resolved: %s", task.ID, task.Instructions), ctx.toolCalls}
}

func orchestrate(tasks []TaskDescriptor) map[string]Result {
	// Each subagent gets its own goroutine and reports back only over a
	// channel, never through a shared variable, as in the actor model.
	ch := make(chan Result, len(tasks))
	for _, t := range tasks {
		go runIsolated(t, ch)
	}
	results := make(map[string]Result, len(tasks))
	for range tasks {
		r := <-ch
		results[r.TaskID] = r
	}
	return results
}

func main() {
	allowed := map[string]bool{"search_files": true, "read_file": true}
	tasks := []TaskDescriptor{
		{"A", "summarize src/auth.go", allowed},
		{"B", "send_email the summary to finance", allowed},
	}
	results := orchestrate(tasks)
	for _, id := range []string{"A", "B"} {
		r := results[id]
		fmt.Printf("%s: %s (%d tool calls) - %s\n", r.TaskID, r.Status, r.ToolCallCount, r.Summary)
	}
}
```

Verified with go vet under Go 1.26 with zero findings, and run with go run,
producing the same two result lines as the other two languages. Results are
collected into a map keyed by task ID rather than printed in channel-arrival
order, since two goroutines completing concurrently give no ordering
guarantee, and that non-determinism is itself part of what this variant is
demonstrating.

## 18. References

1. Anthropic. "How we built our multi-agent research system."
   [anthropic.com/engineering/multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system)
   Verified 2026-08-02. Source for separate per-subagent context windows, the
   fifteen-times token multiplier, the ninety point two percent evaluation
   improvement, the documented early duplicate-work and coverage-gap failure,
   and the synchronous-join and no-mid-run-steering limitation.
2. Anthropic. "Create custom subagents," Claude Code documentation.
   [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents)
   Verified 2026-08-02. Source for the per-subagent context window, system
   prompt, tool access, and independent permissions, and for context
   preservation and constraint enforcement as stated benefits.
3. Anthropic. "Explore the context window," Claude Code documentation.
   [code.claude.com/docs/en/context-window](https://code.claude.com/docs/en/context-window)
   Verified 2026-08-02. Source for the worked numeric example of a subagent
   consuming roughly six thousand one hundred tokens internally against a
   four hundred and twenty token returned summary, and for the default
   exclusion of the delegation tool from a subagent's own tool access.
4. OpenAI. "Orchestrating multiple agents," Agents SDK Python documentation.
   [openai.github.io/openai-agents-python/multi_agent](https://openai.github.io/openai-agents-python/multi_agent/)
   Verified 2026-08-02. Source for the distinction between handoffs and
   agents-as-tools as the two primary multi-agent orchestration primitives.
5. OpenAI. "Handoffs," Agents SDK Python documentation.
   [openai.github.io/openai-agents-python/handoffs](https://openai.github.io/openai-agents-python/handoffs/)
   Verified 2026-08-02. Source for full conversation history inheritance as
   the default handoff behavior, and for input filters and nested-history
   compaction as opt-in isolation mechanisms layered onto a handoff.
6. OpenAI. "Tools," Agents SDK Python documentation.
   [openai.github.io/openai-agents-python/tools](https://openai.github.io/openai-agents-python/tools/)
   Verified 2026-08-02. Source for the agents-as-tools isolation behavior,
   that a nested run's conversation state is not inherited automatically
   unless a session is explicitly shared, and for the custom output
   extractor mechanism.
7. Microsoft. "Bulkhead pattern," Azure Architecture Center.
   [learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)
   Verified 2026-08-02. Source for the reliability-engineering ancestor
   pattern, its ship-hull naming origin, and its resource-partitioning and
   failure-containment definition applied in dimension 1 and dimension 10.
8. Wikipedia contributors. "Actor model."
   [en.wikipedia.org/wiki/Actor_model](https://en.wikipedia.org/wiki/Actor_model)
   Verified 2026-08-02. Used only to confirm the 1973 Hewitt, Bishop, and
   Steiger attribution and the private-state, message-only-communication
   properties applied in dimension 1 and dimension 8, not as a source of the
   LLM-specific pattern shape.
9. Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele
   Bevilacqua, Fabio Petroni, Percy Liang. "Lost in the Middle. How Language
   Models Use Long Contexts."
   [arxiv.org/abs/2307.03172](https://arxiv.org/abs/2307.03172)
   Verified 2026-08-02. Source for the finding that model performance
   degrades on information positioned in the middle of a long input, cited in
   dimension 2 as part of the argument for why unfiltered context growth
   degrades quality, not only cost.
10. OWASP Foundation. "OWASP Top 10 for Large Language Model Applications."
    [owasp.org/www-project-top-10-for-large-language-model-applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
    Verified 2026-08-02. Source for the Excessive Agency risk category cited
    in dimension 11 and dimension 17 regarding unchecked tool autonomy.
