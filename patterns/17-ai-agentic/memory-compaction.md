---
name: Memory Compaction
slug: memory-compaction
family: 17-ai-agentic
category: AI Agentic
aliases: [Context Compaction, Conversation Summarization, Sliding-Window Summarization, History Compaction]
first_described: "The underlying idea traces to hierarchical memory paging in operating systems; applied specifically to LLM agent context windows by Packer, Wooders, Lin, Fang, Patil, Stoica, and Gonzalez, 'MemGPT. Towards LLMs as Operating Systems', arXiv 2310.08560, October 2023, and later named 'compaction' directly by Anthropic's engineering team in 'Effective context engineering for AI agents', 2026"
maturity: established
related: [react, orchestrator-worker, plan-execute, tool-result-caching, reflexion, retrieval-augmented-generation]
incompatible_with: []
verified: 2026-08-02
---

# Memory Compaction

## 1. Name, aliases, and lineage

The canonical name in this catalog is Memory Compaction, chosen because it
names both halves of the mechanism at once. It is a memory management
operation, deciding what an agent keeps in mind, that acts by shrinking a
data structure, the same operation database engineers already call
compaction when they mean merging and reclaiming space in a log-structured
store. The name in most active use in coding-agent tooling today is the
shorter Context Compaction, because the thing being compacted is
specifically the model's context window rather than memory in a general
sense. Anthropic's own engineering guidance uses this exact word. "Compaction
is the practice of taking a conversation nearing the context window limit,
summarizing its contents, and reinitiating a new context window with the
summary" (Anthropic, "Effective context engineering for AI agents",
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents,
verified 2026-08-02). Claude Code, Anthropic's own coding agent, exposes the
identical word as a first-class command, `/compact`, and as a background
behavior called auto-compaction (Anthropic, Claude Code docs, "Manage costs
effectively", https://code.claude.com/docs/en/costs, verified 2026-08-02).

Conversation Summarization is the older and more generic alias, inherited
from the pre-agent chatbot memory literature, where LangChain's
`ConversationSummaryBufferMemory` and its descendants replaced growing
message logs with a running natural-language summary years before "agent"
was the operative word. Sliding-Window Summarization names one specific
strategy within the pattern, summarize everything outside a fixed-size
trailing window, rather than the pattern as a whole, but the term appears
verbatim as a named strategy in production agent memory frameworks, for
example Letta's `sliding_window` compaction strategy, which "preserves
recent messages and summarizes older ones using a separate summarizer call"
(Letta documentation, "Compaction",
https://docs.letta.com/v1-sdk/messages/compaction, verified 2026-08-02).
History Compaction is used interchangeably with Context Compaction in
several agent frameworks and is included here as a search alias rather than
a distinct concept.

The lineage runs through two separate research threads that converged on the
same mechanism. The first is systems research on hierarchical memory. Packer
et al. proposed treating an LLM's context window the way an operating system
treats RAM, a small, fast, expensive resource that must be virtualized
against a larger, slower store, with data paged in and out under program
control. Their paper describes "virtual context management, a technique
drawing inspiration from hierarchical memory systems in traditional
operating systems that provide the appearance of large memory resources
through data movement between fast and slow memory" (Packer, Wooders, Lin,
Fang, Patil, Stoica, Gonzalez, "MemGPT. Towards LLMs as Operating Systems",
arXiv 2310.08560, October 2023, revised February 2024,
https://arxiv.org/abs/2310.08560, verified 2026-08-02). The second thread is
purely practical. As autonomous coding and research agents started running
for hours instead of minutes, the conversation transcript itself grew past
what any context window could hold, and every serious agent framework had to
invent some version of throwing away the old stuff without forgetting what
the agent had already decided. Cognition's Devin team, building a
long-horizon software engineering agent, independently arrived at the same
shape and gave it a memorable framing. "We introduce a new LLM model whose
key purpose is to compress a history of actions and conversation into key
details, events, and decisions. This is hard to get right" (Walden Yan,
Cognition, "Don't Build Multi-Agents",
https://cognition.com/blog/dont-build-multi-agents, verified 2026-08-02).
Memory Compaction, as documented in this entry, is the pattern that both
threads converge on. A periodic, triggered operation that replaces a
verbatim record of past interaction with a shorter, synthesized
representation, so that an unbounded interaction history can run inside a
bounded context window without simply forgetting everything past a fixed
horizon.

MemGPT's own vocabulary is worth distinguishing from compaction proper,
because the two are frequently conflated and the distinction matters for
correctness. MemGPT's core operation is paging, moving a whole message
verbatim out of the active context and into an addressable external store,
called archival memory, from which the agent can later retrieve it by an
explicit tool call, unmodified. Compaction, by contrast, is lossy by
construction. The content that leaves the active window is not preserved
verbatim anywhere, it is rewritten into a shorter summary and the original
text is gone. A system can do both, page some things out untouched and
summarize others, and Letta, MemGPT's successor project, exposes exactly
that combination. A `Compaction` mechanism for the active message window and
a separate `Archival Memory` system, described as an "external (out-of-
context) memory store," for content the agent explicitly chooses to keep
verbatim (Letta documentation, "Memory", https://docs.letta.com/memory,
verified 2026-08-02). This entry treats compaction, the lossy
summarize-and-replace operation, as the pattern. Paging to an external store
without summarization is closer to a cache-eviction or tiered-storage
pattern and is covered under Tool Result Caching and, for retrieval-based
recall of the paged content, Retrieval-Augmented Generation.

## 2. Problem and context

An agent that runs for a long time accumulates a conversation. Every user
message, every model response, every tool call and its result, every
observation from the environment, gets appended to a single growing list
that is resent to the model on the very next turn. Nothing in that list is
free. An LLM API charges by the token, whether that token is fresh
instruction or a stale log line from forty turns ago, and every provider
imposes a hard ceiling on how many tokens fit in one request. A short
question-and-answer session never hits either constraint. A coding agent
working through a multi-file refactor, an autonomous research agent chasing
a citation graph, or a customer-support agent handling a single ticket
across twenty back-and-forth messages absolutely does, usually within the
first hour of continuous work.

The naive response, doing nothing and letting the request fail once the
context window overflows, is not survivable for any agent meant to run
unattended past a few dozen turns. The next naive response, silently
truncating the oldest messages once a limit is hit, degrades in a way that
is worse than an outright failure because it fails silently. The agent
keeps answering confidently, but it has lost the instruction that was given
at minute two, or the bug it already diagnosed and fixed once, and it may
repeat work, contradict an earlier decision, or violate a constraint it was
told about but no longer "remembers," because that message simply does not
exist in the request anymore. This failure mode is well documented outside
the agentic literature too. Chroma's technical report on long-context
retrieval found that "model performance varies significantly as input
length changes, even on simple tasks," and that models "do not maintain
consistent performance across input lengths," a phenomenon its authors named
context rot (Hong, Troynikov, Huber, "Context Rot. How Increasing Input
Tokens Impacts LLM Performance", Chroma Technical Report, July 14, 2025,
https://www.trychroma.com/research/context-rot, verified 2026-08-02).
Context rot means that even when a context window is nominally large enough
to hold the whole history, stuffing it full is itself a cost. The model's
ability to locate and use the one instruction that matters, buried among
thousands of tokens of tool output and small talk, degrades measurably as
the haystack grows, independent of whether the window technically overflows.

The context in which Memory Compaction becomes the right answer, rather than
a workaround for a problem better solved another way, has three ingredients.
First, the interaction is genuinely long-running, minutes to hours of
continuous agentic work in one logical session, not a single request-
response pair. Second, the agent needs continuity of decisions and
constraints across that whole span, so simple truncation (drop the oldest N
messages, keep nothing of them) is unacceptable, because an early
architectural decision or a user's stated constraint is exactly the kind of
thing that must survive to turn two hundred even though the sentence that
stated it will not. Third, most of what accumulates in the transcript is
not, in fact, information the agent needs verbatim going forward. A passing
test's full stdout, a file that was read and already summarized in a later
message, a tool call that succeeded uneventfully. Compaction exists to
exploit that asymmetry, throwing away the bulk that carries no
forward-looking value while keeping a distilled record of the part that
does, and doing this repeatedly and automatically as the conversation keeps
growing, rather than once at a fixed point.

## 3. Forces

**Continuity versus cost.** Every token of history preserved verbatim is a
token that must be paid for and re-processed on the next request. The
opposing pull is losing the ability to justify a past decision, honor an
earlier constraint, or avoid re-doing work. Compaction is explicitly a bet
that a shorter, synthesized record preserves enough continuity at a fraction
of the cost, and the entire difficulty of building one well is calibrating
how aggressively to make that trade.

**Fidelity versus size.** A summary that keeps everything is not a summary,
it is a longer transcript with extra steps. A summary aggressive enough to
matter necessarily discards information, and the discarded information is,
by definition, information the summarizer judged unimportant at the moment
of compaction, a judgment that can turn out wrong two hundred turns later
when exactly that detail becomes load-bearing. Anthropic's own guidance
names this directly, warning that compaction "requires careful attention to
what gets kept versus discarded, since overly aggressive compaction can lose
important context" (Anthropic, "Effective context engineering for AI
agents", verified 2026-08-02).

**Latency and determinism versus quality.** A high-quality summary usually
means invoking a second model call, adding real wall-clock latency and a
second source of non-determinism into a pipeline that is already
non-deterministic. A cheap, rule-based summarizer, one that drops everything
but the last assistant message, or keeps only lines matching a regex, is
fast and predictable but produces markedly lower-fidelity summaries. This is
the same fidelity-versus-size force restated at the implementation layer,
and most production systems land on a hybrid, cheap heuristics for
structural elements such as dropping tool output past a size threshold and
deduplicating repeated observations, plus a model call for the genuinely
narrative parts, what was decided and why.

**Operability versus opacity.** A compacted history is, by construction, no
longer a faithful log of what actually happened. Debugging an agent that
misbehaved after several rounds of compaction means reasoning about a
summary of a summary, which is strictly harder than reading a raw
transcript, and any audit or compliance requirement that needs the original
interaction verbatim is directly opposed to the storage and cost savings
compaction provides. Systems that need both usually keep the raw transcript
in cold storage, never sent to the model again but retained for audit,
while the compacted version is what actually rides in the context window,
which is a distinct decision from whether to compact at all.

**Automation versus control.** A fully automatic trigger that compacts
whenever the token count crosses a set point removes the risk of forgetting
to compact and hitting a hard failure, but it also means compaction can fire
at an arbitrarily bad moment, mid-way through a delicate multi-step tool
sequence, where the summarizer has an incomplete picture of what is actually
in progress. A manually or explicitly triggered compaction, a `/compact`
command, or a compaction step only inserted at a clean checkpoint between
subtasks, avoids that but reintroduces the risk that nobody triggers it in
time and the request simply fails.

## 4. Applicability and non-applicability

Reach for Memory Compaction when.

- The agent runs for long enough, in wall-clock time or in number of turns,
  that its accumulated transcript will exceed the model's context window
  before the task naturally ends. This is the load-bearing condition, every
  other reason to compact is secondary to this one.
- The task genuinely needs continuity of earlier decisions, constraints, or
  facts across the whole span, so a plain drop-the-oldest-messages
  truncation would break correctness, not just tidiness.
- A meaningful fraction of the transcript is disposable in the specific
  sense that its exact wording does not matter going forward, only its
  gist. Successful tool output, exploratory reads, resolved sub-questions,
  small talk.
- The system already has, or can cheaply add, a mechanism to invoke a
  second, smaller model call, or a deterministic summarizer, without
  materially harming the user-visible latency of the primary interaction.
- The interaction is a single logical session with one active thread of
  reasoning, or at most a small, bounded number of parallel threads each
  managed independently. Compaction is a within-session technique.

Do NOT reach for Memory Compaction when.

- The session is short enough that it will never approach the context
  window limit in practice. Adding a compaction subsystem to a chatbot that
  answers three questions and ends is unjustified complexity with no
  corresponding benefit; a fixed-size sliding window with no summarization
  step, or nothing at all, is sufficient.
- The task legally or contractually requires the verbatim history to remain
  available to the model itself, not just in cold storage for humans, for
  example a regulated financial advisory conversation where the model must
  be able to quote its own earlier statement exactly. Compaction is lossy
  by design and cannot guarantee verbatim recall of anything it has folded
  away; if verbatim recall is a hard requirement, use paging to an external
  store, as in MemGPT's archival memory, or Retrieval-Augmented Generation
  against an unmodified log instead.
- The information that needs to persist is naturally structured data rather
  than narrative history, such as user preferences, entity facts, or a
  running task list. Writing that data directly into a structured memory
  store or a scratchpad file, the note-taking pattern Anthropic names as
  compaction's sibling technique, is both cheaper and more reliable than
  round-tripping it through a natural-language summarizer, because it never
  depends on the summarizer correctly identifying that fact as worth
  keeping.
- The workload is naturally parallel and decomposable into independent
  subtasks with small, bounded context each. Anthropic explicitly frames
  multi-agent orchestration as the better fit here. "Complex research and
  analysis where parallel exploration pays dividends" is handled by
  splitting work across sub-agents with fresh, small context windows rather
  than by growing and repeatedly compacting one shared context (Anthropic,
  "Effective context engineering for AI agents", verified 2026-08-02). See
  Orchestrator-Worker.
- The system cannot tolerate the added latency, cost, or non-determinism of
  a summarization call, and a simpler bounded strategy, a fixed sliding
  window with hard truncation, or Tool Result Caching to shrink the largest
  contributors before they ever enter history, would keep the token count
  under control without a summarization step at all.

## 5. Structure

**History store.** The ordered sequence of messages, tool calls, and
observations that make up the agent's working memory. This is the thing
being compacted. It is typically a simple append-only list before
compaction is applied, and a two-part structure after, a running summary
plus a trailing window of verbatim recent entries.

**Trigger.** The condition that decides when compaction runs. Common
triggers are a token-count threshold measured against the model's context
window, the dominant approach in production systems, used by both Claude
Code's auto-compaction and Letta's default compaction strategy, a
message-count threshold, an explicit user or developer command, or a
checkpoint boundary the orchestrating code inserts between logical
subtasks.

**Window boundary.** The line that separates recent content kept verbatim
from older content eligible for folding into the summary. Most systems keep
a small trailing window of the N most recent messages untouched, both
because recent content is the most likely to be immediately relevant and
because summarizing content that is still mid-use, an in-progress tool call
sequence, risks corrupting it.

**Summarizer.** The component that turns the folded portion of the history
into a shorter representation. Ranges from a single prompted LLM call
instructed to preserve architectural decisions, unresolved issues, and
outstanding constraints, to a rule-based extractor that keeps only messages
matching a pattern, to a hierarchical summarizer that folds a prior summary
together with newly-foldable messages into an updated summary, a shape
required for repeated compaction across a very long session, since
otherwise each compaction only sees the raw messages and the previous
summary is discarded rather than merged forward.

**Pinning mechanism.** An escape hatch that marks specific messages,
typically system prompts, hard constraints, and safety-relevant
instructions, as never eligible for folding, regardless of age. Without
this, a sufficiently aggressive summarizer can eventually drop the very
instruction that governs its own behavior.

**Reinsertion point.** Where the summary lands in the reconstituted context.
Nearly universally, the summary is reinserted at the position the folded
messages occupied, typically as a single system or assistant message near
the top of the window, immediately followed by the retained verbatim
window, so the model sees the background of what already happened, then the
current state actually in front of it.

## 6. ASCII structure diagram

```
+-------------------------------------------------------------+
|                    Agent Runtime / Orchestrator              |
|                                                               |
|   +----------------------+       token count / turn count    |
|   |    History Store     |------------------+                |
|   |  m1 m2 m3 ... mN     |                  v                |
|   +----------------------+          +----------------+       |
|              |                      |    Trigger     |       |
|              | eligible for fold    +----------------+       |
|              v                              |                |
|   +----------------------+                  | fires          |
|   | Window Boundary Split |<-----------------+                |
|   +----------------------+                                   |
|      |                |                                      |
|      v                v                                      |
|  +--------+      +-----------+                                |
|  | Folded |      |  Kept     |  (pinned + trailing window)    |
|  | (head) |      | (verbatim)|                                |
|  +--------+      +-----------+                                |
|      |                                                        |
|      v                                                        |
|  +-------------------+     previous summary, if any           |
|  |    Summarizer     |<---------------------------------+     |
|  +-------------------+                                  |     |
|      |                                                   |     |
|      v                                                   |     |
|  +-------------------+  running summary  +-----------+   |     |
|  |  Updated Summary  |------------------->| Persisted |---+     |
|  +-------------------+                    +-----------+         |
|      |                                                        |
+------+--------------------------------------------------------+
       |
       v
+-------------------------------------------------------------+
|            Reconstituted Context Sent to the Model           |
|  [system: pinned instructions]                               |
|  [system: compacted summary]                                 |
|  [kept verbatim tail: m(N-k) ... mN]                          |
+-------------------------------------------------------------+
```

## 7. Dynamics

```
turn 1..k:   append(message) -> history grows, no trigger fires
             model called with full history each turn

turn k+1:    append(message) -> estimateTokens() > tokenBudget
             |
             v
        compact() invoked
             |
             +--> split history at (len - keepRecent)
             |        head = older messages
             |        tail = most recent `keepRecent` messages
             |
             +--> partition head by pinned flag
             |        toFold  = head where pinned == false
             |        toKeep  = head where pinned == true
             |
             +--> if toFold is empty, return, nothing to compact
             |
             +--> summary_fresh = summarizer(toFold)
             |
             +--> summary = merge(summary_prior, summary_fresh)
             |        (concatenation, or a second LLM call that
             |         folds the old summary and the new material
             |         into one coherent updated summary)
             |
             +--> history = toKeep ++ tail
             |        (toFold messages are now gone from history;
             |         only summary text represents them)
             |
             v
        model called next turn with.
             [pinned system messages]
             [summary message]
             [tail, recent verbatim messages]

turn k+2..:  cycle repeats, grow, trigger, compact, shrink, grow again
             each compaction may re-fold a growing summary, so summary
             length itself must be bounded (max_summary_tokens) or the
             pattern degenerates into the same overflow it prevents
```

The critical property visible in this flow is that compaction is not a
one-time event but a recurring cycle, history grows until the trigger
fires, shrinks sharply, then grows again. A system under sustained load will
compact repeatedly across a single session, and each compaction after the
first must fold the previous summary together with newly-eligible messages
rather than discard it, or information from early compactions is silently
lost on the second pass. Letta's documentation names this constraint
directly by exposing both a `max_tokens_before_summary` trigger and a
`max_summary_tokens` cap on the output, preventing the summary itself from
becoming the next thing that needs summarizing (Letta documentation,
"Compaction", verified 2026-08-02; LangGraph "Add memory" guide,
`langmem.short_term.SummarizationNode` parameters `max_tokens_before_summary`
and `max_summary_tokens`, https://docs.langchain.com/oss/python/langgraph/add-memory,
verified 2026-08-02).

## 8. Implementation variants

**Threshold-triggered sliding window, the dominant production shape.** Keep
the last N messages, or the last N tokens' worth of messages, verbatim.
When the estimated token count of the whole history crosses a configured
budget, fold everything outside the window into the running summary. This
is Letta's default `sliding_window` strategy and the shape implemented in
this entry's code samples. Simple to reason about, cheap to implement, and
the failure mode of losing something just outside the window is at least
predictable. It is always the oldest non-pinned content that goes first.

**Turn-count or message-count triggered, rather than token-count.** Instead
of estimating tokens, compact every K turns regardless of message size.
Cheaper to compute, no tokenizer call needed, but a poor proxy when message
sizes vary widely, for example an agent whose tool calls sometimes return a
one-line result and sometimes a ten-thousand-line log dump; a token-based
trigger reacts to the actual cost, a turn-based one does not.

**Explicit command, developer-triggered.** No automatic trigger at all,
compaction runs only when a human or an orchestrating script explicitly
calls it, as with Claude Code's `/compact` command, which also accepts
free-text instructions steering what to preserve, for example
`/compact Focus on code samples and API usage` (Claude Code docs, "Manage
costs effectively", verified 2026-08-02). This trades the risk of a
surprise context overflow, nobody ran the command in time, for the benefit
of compacting only at moments a human judges safe, and for letting the
human supply task-specific guidance about what matters, something an
automatic trigger cannot do without additional signal.

**Checkpoint-boundary triggered.** In an orchestrator that already
decomposes work into discrete subtasks, see Plan-Execute and
Orchestrator-Worker, compaction is invoked only at the transition between
subtasks, never mid-subtask. This avoids the specific risk of summarizing
away an in-progress multi-step tool sequence, at the cost of sometimes
delaying compaction longer than a pure token-threshold approach would.

**Single-shot summarization versus hierarchical, recursive, summarization.**
A single-shot summarizer sees the full set of foldable messages once per
compaction and produces one summary. A hierarchical summarizer, needed once
a session compacts more than a handful of times, instead feeds the previous
summary plus the newly foldable messages back into the summarizer together,
producing an updated summary that supersedes rather than appends to the
old one. Without this, repeated compaction either drops earlier summaries
entirely, losing continuity from before the second compaction, or
concatenates them without bound, recreating the very overflow problem
compaction exists to solve.

**Structured extraction instead of, or alongside, free-text summary.** Some
systems do not produce prose at all; instead the summarizer is a structured
extraction step that writes specific facts, decisions made, files touched,
open questions, into typed fields, which are then rendered back into the
prompt as a short bulleted block. This is closer to Anthropic's separately-
named note-taking technique than to prose compaction, but production
systems frequently blend the two, a structured scratchpad for durable
facts, plus prose compaction for everything else, because pure structured
extraction misses nuance a free-text summary captures more naturally, and
pure prose summarization is unreliable at preserving a specific fact
exactly, a file path, a numeric threshold, the way a typed field is.

**Paging to an addressable store instead of, or alongside, summarizing.**
MemGPT's original design pages folded content verbatim into an external
archival store that the agent can query back with an explicit tool call,
rather than compressing it. This preserves fidelity completely at the cost
of the agent needing to know, or guess, that it should go look, and it adds
a retrieval step, effectively Retrieval-Augmented Generation over the
agent's own history, as a dependency. Systems that need both continuity and
occasional verbatim recall combine paging for anything that might need
exact recall with compaction for everything that only needs gist.

## 9. Known production uses

**Claude Code, Anthropic.** Ships both an explicit `/compact` command,
which "summarizes older history to free space" and accepts free-text
steering instructions, and an automatic background behavior called
auto-compaction, triggered when the conversation "has grown close to the
model's maximum input size." The tool also supports resuming a very large
prior session by loading only a summary of it rather than the full
transcript, described in the docs as offering "to resume from a summary" so
that later requests do not have to carry the full history (Anthropic,
Claude Code docs, "Manage costs effectively",
https://code.claude.com/docs/en/costs, verified 2026-08-02).

**Letta, formerly MemGPT, Letta AI.** Exposes compaction as a first-class,
named platform feature with a documented default strategy. "When an agent's
conversation history grows too long to fit in its context window, Letta
automatically compacts (summarizes) older messages to make room for new
ones," implemented by default as a `sliding_window` strategy that "preserves
recent messages and summarizes older ones using a separate summarizer
call," alongside an explicit `Compact` API endpoint for manually triggering
the same operation on demand (Letta documentation, "Compaction",
https://docs.letta.com/v1-sdk/messages/compaction, verified 2026-08-02).

**LangGraph and LangMem, LangChain.** Ships `langmem.short_term
.SummarizationNode` as a documented building block for LangGraph agents,
described in LangChain's own guide as producing "running summaries of
conversations" that replace "older messages with condensed versions,"
configured with `max_tokens_before_summary` and `max_summary_tokens`
parameters so the summarization trigger and the summary's own size are both
explicit and bounded (LangChain, "Add memory",
https://docs.langchain.com/oss/python/langgraph/add-memory, verified
2026-08-02).

**Devin, Cognition.** Cognition's long-horizon coding agent uses a
dedicated model whose only job is to compress an agent's action-and-
conversation history into "key details, events, and decisions" once a task
runs long enough that the raw trace no longer fits, a technique the team's
own writing acknowledges is "hard to get right" precisely because deciding
what to keep versus discard is where quality is won or lost (Walden Yan,
Cognition, "Don't Build Multi-Agents",
https://cognition.com/blog/dont-build-multi-agents, verified 2026-08-02).

**MemGPT research prototype, Packer et al., UC Berkeley.** The original
academic system that established the pattern's vocabulary for the field.
Its virtual context management performs both paging, moving whole messages
to an addressable archival store, and, in its function-calling loop,
summarization of the working context when the agent's own self-editing
memory functions choose to compress rather than page, framed explicitly as
an operating-system-style memory hierarchy applied to LLM context windows
(Packer, Wooders, Lin, Fang, Patil, Stoica, Gonzalez, "MemGPT. Towards LLMs
as Operating Systems", arXiv 2310.08560, verified 2026-08-02).

## 10. Consequences

Positive.

- Unbounded-length sessions become possible within a fixed context window,
  which is the entire reason the pattern exists. Without it, any agent that
  runs long enough simply hits a hard request failure.
- Per-turn token cost stops growing linearly with session length. A
  session that would otherwise resend an ever-larger transcript on every
  turn instead resends a summary plus a small trailing window, which keeps
  marginal cost roughly flat rather than accumulating without bound.
- Model attention is concentrated on what remains relevant. Given the
  documented context-rot effect, where retrieval and instruction-following
  degrade as irrelevant tokens accumulate, a shorter, curated context can
  produce measurably better task performance than a longer one stuffed with
  stale material, even when the longer one would technically still fit.
- The pattern composes cleanly with session resumption. A compacted summary
  is a natural, cheap artifact to persist and reload when a session is
  paused and later resumed, as opposed to reloading and re-paying for an
  entire raw transcript.

Negative.

- The pattern is lossy by construction, and the loss is invisible at the
  moment it happens. Nothing in a typical compaction pipeline flags that a
  detail was discarded and might matter later; the agent simply no longer
  has access to it, and the first symptom is usually a wrong answer or a
  repeated mistake many turns downstream, at a point where the connection
  back to the compaction event is not obvious.
- Debuggability drops. A raw transcript is a faithful record an engineer
  can read to understand exactly what happened. A compacted history is a
  summary of a summary after enough cycles, and reconstructing the actual
  sequence of events from it, if the raw log was not separately retained,
  is often impossible.
- The summarizer becomes a single point of failure for correctness. If it
  hallucinates a decision that was never made, or misattributes a
  constraint, that fabricated content now sits in the context with the same
  apparent authority as anything the model actually said, and there is no
  longer a verbatim record to check it against unless one was kept
  separately.
- Added latency and cost from the summarization call itself, which is
  particularly noticeable in systems that compact synchronously and
  frequently. Anthropic's own cost documentation notes that compacting a
  large context is itself "a large request" because the summarization step
  has to read the entire conversation it is about to shrink (Anthropic,
  Claude Code docs, "Manage costs effectively", verified 2026-08-02).

## 11. Failure modes and misuse

**Symptom.** The agent confidently contradicts a constraint the user stated
early in the session, or re-asks a question it was already answered.
**Cause.** Overly aggressive compaction folded the message carrying that
constraint into a summary that omitted it, either because the summarizer's
instructions did not prioritize constraints specifically, or because the
constraint was phrased casually enough that a generic summarizer judged it
low-value. **Fix.** Pin messages carrying explicit constraints, system
instructions, and safety-relevant statements so they are never eligible for
folding regardless of age, and instruct the summarizer explicitly to
prioritize unresolved constraints and open commitments as a named category
to preserve, not just important things in general.

**Symptom.** The context window keeps overflowing even though compaction is
configured and firing. **Cause.** The running summary itself grows without
bound across repeated compactions, because each compaction appends a fresh
summary onto the previous one instead of merging them, so the compacted
portion eventually becomes as large as an uncompacted transcript would have
been. **Fix.** Cap the summary's own size with a hard token limit, as
Letta's `max_summary_tokens` and LangMem's `max_summary_tokens` both do, and
use a hierarchical summarizer that folds the old summary together with new
material into one updated summary of bounded size, never a simple
append.

**Symptom.** Compaction fires in the middle of a multi-step tool call
sequence and the agent's next action is nonsensical, referencing a tool
result that is no longer in context. **Cause.** The trigger is purely
token-count based with no awareness of whether the agent is mid-sequence
in a tool loop, so a compaction can land between the call to a search tool
and the arrival of its result, folding the call away from its own result
or vice versa. **Fix.** Either restrict the window boundary to always fall
on a message-role boundary that respects tool-call and tool-result
pairing, never splitting a call from its result across the fold line, or
move to a checkpoint-triggered strategy that only compacts between logical
subtasks rather than at an arbitrary token threshold.

**Symptom.** Two different compaction runs on the same underlying history
produce noticeably different summaries, and downstream behavior becomes
harder to reproduce or debug. **Cause.** The summarizer is itself an LLM
call, which is non-deterministic even at low sampling temperature, and no
part of the pipeline records which exact summary was produced for which
exact input. **Fix.** Log the pre-compaction message set and the resulting
summary together, even if only in a side channel never resent to the model,
so a given session's behavior can be traced back to the exact summary that
was in effect at the time, and consider a deterministic or rule-based
summarizer for the parts of the pipeline where reproducibility matters more
than summary quality.

**Symptom.** The agent behaves as though it has completely forgotten the
task's original goal after several hours of work, even though compaction
appears to be working correctly on recent history. **Cause.** The very
first message, which usually states the overall goal, was itself folded
away in an early compaction cycle and never re-surfaced, because nothing
in the pipeline treated the original task statement as a pinned category
distinct from an old message that happens to be early. **Fix.** Pin the
original task or goal statement explicitly and permanently, separate from
the generic recency-based window, so it survives every compaction cycle
regardless of how many times the history has been folded since.

**Symptom.** A team adds compaction to a short-lived session, a handful of
turns, well within the context window, and sees no measurable benefit but
does see new bugs traceable to lost detail. **Cause.** Misuse of the
pattern outside its applicability. Compaction was added reflexively as a
best practice for agents rather than in response to an actual context
budget problem, so all of its costs, latency, lossiness, added complexity,
were paid with none of its benefit realized. **Fix.** Apply the
applicability test from dimension 4 before adopting the pattern at all; if
the session never approaches the context window, remove compaction rather
than tune it.

## 12. Trade-off matrix

| Concern | Memory Compaction | Fixed sliding window, no summary | Tool Result Caching | Retrieval-Augmented Generation over history | Note-taking / structured scratchpad |
|---|---|---|---|---|---|
| Preserves continuity beyond the window | Yes, lossily, via summary | No, dropped entirely | Only for the cached results themselves | Yes, but only what is explicitly retrieved | Yes, for facts explicitly written down |
| Verbatim fidelity of retained detail | Low, paraphrased | Not applicable, nothing kept | High for the cached value | High for what is retrieved, but retrieval can miss | High for whatever was written |
| Added latency per compaction event | A summarization call, medium | None | None beyond a lookup | A retrieval call, low to medium | None if written inline, low if a separate write step |
| Handles session of arbitrary length | Yes, by design | No, older context simply lost | Only shrinks specific outputs, not the whole history | Yes, if the retrieval index itself is unbounded | Bounded by scratchpad size, usually small and curated |
| Risk if the mechanism is wrong | Silent, hard-to-trace loss of context | Explicit and predictable loss | Stale or wrong cached value reused | Missed retrieval, silent gap | Missed write, silent gap |
| Best suited for | Long single-thread sessions needing narrative continuity | Short sessions where old context genuinely does not matter | Repeated identical tool calls within a session | Long sessions where exact past facts must be recoverable on demand | Sessions with a small number of durable, structured facts to track |

## 13. Related and incompatible patterns

**Tool Result Caching** addresses a different but adjacent cost problem,
avoiding redundant tool invocations by remembering a result already
computed. It shrinks what enters history in the first place, whereas
compaction shrinks what is already there. The two compose directly, caching
reduces how often large tool outputs get appended to history at all,
which in turn reduces how often and how aggressively compaction needs to
fire.

**Retrieval-Augmented Generation** is compaction's natural complement for
the case a pure summary cannot serve, needing an exact past detail back on
demand. A system can compact its working history for the common case while
also indexing the raw, uncompacted transcript for retrieval, so a specific
fact lost from the summary can still be recovered by an explicit query
rather than being gone forever.

**Reflexion** relies on a distilled record of past attempts and their
outcomes to inform future ones, which is structurally the same operation as
compaction, turning a raw trace into a compressed lesson, applied
specifically to self-critique rather than to general conversation history.
A long-running Reflexion loop is itself a candidate for compaction if its
own accumulated reflections grow past a useful size.

**Orchestrator-Worker** and **Plan-Execute** are the structural alternative
Anthropic names alongside compaction. Instead of growing one shared context
and periodically shrinking it, decompose the task so that most of the work
happens in small, independent, disposable contexts, sub-agent calls, that
never need to grow large in the first place, and only a small amount of
coordination state accumulates in the orchestrator's own context. The two
are not mutually exclusive; a long-running orchestrator can itself compact
its own coordination history even while delegating heavy work to workers
with fresh contexts.

**ReAct** is frequently the loop generating the very history that
compaction operates on. A ReAct agent's alternating thought, action, and
observation steps are exactly the append-only sequence that grows without
bound in a long-running session and becomes the input to a compaction
trigger.

No pattern in this catalog is flagged as strictly incompatible with Memory
Compaction, though it is redundant, not merely unnecessary, in combination
with a pattern that already bounds context size structurally, such as an
orchestrator-worker decomposition where no single context ever grows large
enough to need it.

## 14. Refactoring path in and out

Introducing compaction into a system that currently just appends to an
unbounded history, in order.

1. Instrument the existing history with a token-count estimator so the
   system can observe, before anything else changes, how close to the
   context window limit real sessions actually get and how quickly. Ship
   this as a pure observability change with no behavior modification.
2. Introduce a pinning concept and mark the system prompt and any hard
   constraints as pinned, even before any compaction logic exists, so the
   eventual compactor has a category to respect from day one rather than
   retrofitting it after a real information-loss incident.
3. Add a fixed trailing window, keep the last N messages verbatim, do
   nothing to anything older yet, and confirm the rest of the system
   tolerates a bounded context without functional regression, isolating
   whether truncation alone is survivable before adding the more complex
   summarization step.
4. Introduce the summarizer as a single-shot operation triggered manually
   or in a test script, not yet wired into the live token-threshold
   trigger, and evaluate its output quality against real session
   transcripts before it is allowed to run automatically.
5. Wire the summarizer to the trigger from step 1, starting with a
   conservative, high, token budget so compaction fires rarely at first,
   and widen it only after confirming the summary quality holds up under
   real production traffic.
6. Add the hierarchical merge step, folding old summary plus newly eligible
   messages together, once a session is observed compacting more than
   once, since a single-shot summarizer with no merge step will silently
   drop earlier summaries the moment a second compaction fires.

Removing compaction from a system that has it, when the applicability test
in dimension 4 no longer holds, for example the task was redesigned to be
naturally short, or restructured into an orchestrator-worker decomposition
that never grows a large single context, in order.

1. Confirm via the token-count instrumentation from step 1 above that
   sessions genuinely no longer approach the context limit under the new
   design, rather than assuming it from the redesign alone.
2. Disable the automatic trigger first, leaving the pinning and window
   mechanisms in place as a safety net, so a session that unexpectedly
   grows large still degrades gracefully to a fixed window rather than
   failing outright.
3. Remove the summarizer call path once a full observation period confirms
   the trigger genuinely never fires under real traffic, and simplify the
   history store back to a plain append-only list.
4. Retain the pinning concept even after removal, since pinned messages,
   the system prompt and hard constraints, are useful metadata independent
   of whether compaction is active, and re-adding compaction later is
   cheaper if that scaffolding was never torn out.

## 15. Testing and verification

Testing a compaction implementation is easier than testing the summarizer's
judgment and harder than testing ordinary business logic, because the two
concerns are genuinely separable and should be tested separately.

The mechanical half, trigger evaluation, window boundary math, pinning
respect, and history reconstruction, is fully deterministic and should be
tested with ordinary unit tests against a fake summarizer that returns a
fixed, predictable string. Assert that a session below the token budget
never triggers compaction, that a session at or above the budget triggers
exactly once per append that crosses it and not repeatedly, that pinned
messages are never present in the folded set passed to the summarizer under
any ordering, that the reconstructed context after compaction is exactly
the pinned messages plus the summary plus the kept tail with no duplication
or dropped entries, and that running compaction twice in a row on an
already-below-budget history is a no-op.

The summarizer's judgment quality is a different kind of test and does not
reduce to a pass or fail assertion the way the mechanical half does. Build a
small, curated set of realistic session transcripts, each annotated with the
specific facts, decisions, and constraints a correct summary must preserve,
and score real summarizer output against that annotation, either with an
LLM-as-judge rubric or a simpler keyword or entity-presence check for the
annotated must-keep items. Treat a drop below a chosen recall threshold on
this fixture set as a regression, the same way a lint failure blocks a
merge, because summarizer quality silently degrading is exactly the failure
mode dimension 11 describes as hardest to catch in production.

A third test that is easy to skip and important not to is an end-to-end
test that runs a synthetic long session, enough turns to trigger compaction
multiple times, and asserts the agent's final answer is still correct on a
question whose answer depended on information from early in the session,
now several compactions in the past. This is the test that actually
exercises the property compaction claims to provide, continuity across an
arbitrarily long session, and unit tests on the mechanical half alone
cannot substitute for it.

## 16. Observability signals

Log, at minimum, every compaction event with the timestamp, the token count
immediately before and immediately after, the number of messages folded,
the number of messages pinned and therefore excluded from folding, and
either the full summarizer output or a hash of it if storing the full text
is undesirable for size or privacy reasons. This is the single most
valuable signal for diagnosing the failure modes in dimension 11, since
knowing what the summary said at the moment something went wrong is almost
always the first question in a post-incident review of an agent that
misbehaved after a long session.

Track compaction frequency per session as a metric over time. A healthy
system shows a roughly stable compaction rate proportional to session
activity; a compaction rate that climbs steadily within a single session
signals the summary-growth failure mode from dimension 11, where the
summary itself is not being bounded and is approaching the trigger
threshold on its own.

Track summarizer latency and cost as separate line items from the primary
agent turn's latency and cost, since compaction is easy to bury inside
generic LLM-call metrics and then invisible when it becomes the dominant
cost driver in a long-running session, exactly the pattern Claude Code's own
documentation flags when it notes that compacting a large context is itself
a large, and therefore costly, request.

Alert on the specific condition where a token-count trigger fires but the
subsequent compaction produces no reduction, because the folded set was
empty as everything eligible happened to be pinned, or the summarizer
returned an empty or near-empty string, since this indicates compaction is
about to fail to prevent the very overflow it exists to prevent, and the
next few turns are at real risk of a hard context-window failure with no
further recourse.

## 17. Security and privacy implications

A compaction summarizer call is, itself, an additional LLM invocation that
receives the full content of every message it is asked to fold, including
anything sensitive the user or the environment provided earlier in the
session, such as credentials accidentally pasted into a tool output,
personal data surfaced by a search, or proprietary source code. If the
summarizer runs on a different model, a different provider, or a different
trust boundary than the primary agent, this data now crosses that boundary
a second time, independent of and in addition to whatever data governance
policy already governs the primary model call, and that second exposure is
easy to overlook because it is not a new feature request, it is an internal
implementation detail of an existing feature.

Because compaction is lossy and irreversible in the live context, the
original text is gone once folded, unless a raw log is separately retained,
it can also work against, rather than for, data minimization and
right-to-erasure requirements, depending on how the raw pre-compaction
transcript is or is not retained elsewhere. A system that retains the full
raw transcript in a separate audit log purely to make compaction
debuggable, as recommended in dimension 15 and dimension 16, has
reintroduced exactly the long-term storage of sensitive conversational
content that compaction's in-context shrinking was never meant to solve,
and that retained log needs its own access controls, retention limits, and
deletion path, entirely separate from the compaction mechanism itself.

A summarizer that is prompt-injectable, if any part of the folded content
originated from an untrusted source such as a scraped web page or a third
party's tool output, is a fresh attack surface distinct from the primary
agent's own prompt-injection exposure. An attacker who can plant text in
content the agent will later read has a second opportunity to influence
behavior at the moment that text gets folded into a persistent summary that
will keep re-entering every future turn of the session, potentially long
after the original malicious content itself has scrolled out of the window
and would otherwise have aged out naturally.

## 18. References

1. Anthropic. "Effective context engineering for AI agents."
   https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents,
   verified 2026-08-02.
2. Anthropic. Claude Code documentation, "Manage costs effectively."
   https://code.claude.com/docs/en/costs, verified 2026-08-02.
3. Packer, Charles; Wooders, Sarah; Lin, Kevin; Fang, Vivian; Patil, Shishir
   G.; Stoica, Ion; Gonzalez, Joseph E. "MemGPT. Towards LLMs as Operating
   Systems." arXiv 2310.08560, October 2023, revised February 2024.
   https://arxiv.org/abs/2310.08560, verified 2026-08-02.
4. Letta AI. "Compaction." Letta documentation.
   https://docs.letta.com/v1-sdk/messages/compaction, verified 2026-08-02.
5. Letta AI. "Memory." Letta documentation.
   https://docs.letta.com/memory, verified 2026-08-02.
6. LangChain. "Add memory." LangGraph documentation.
   https://docs.langchain.com/oss/python/langgraph/add-memory, verified
   2026-08-02.
7. Yan, Walden. Cognition. "Don't Build Multi-Agents."
   https://cognition.com/blog/dont-build-multi-agents, verified 2026-08-02.
8. Hong, Kelly; Troynikov, Anton; Huber, Jeff. "Context Rot. How Increasing
   Input Tokens Impacts LLM Performance." Chroma Technical Report, July 14,
   2025. https://www.trychroma.com/research/context-rot, verified
   2026-08-02.

## Code

The three samples below implement the same threshold-triggered sliding
window strategy described in dimension 8. A token budget estimated from
character count, a small trailing window kept verbatim, a pinning flag that
exempts messages from folding, and a pluggable summarizer callback. Each was
compiled or run directly against the toolchain listed for it, and all three
produce identical output for the identical scripted session, which is
included as the final lines of output in each case.

### TypeScript

Compiled with `npx tsc --target es2020 --module commonjs --strict` (tsc
7.0.2) and executed with `node`.

```typescript
interface Msg {
  role: string;
  content: string;
  pinned?: boolean;
}

type Summarizer = (msgs: Msg[]) => string;

class CompactingHistory {
  private messages: Msg[] = [];
  private summary: string | null = null;

  constructor(
    private summarizer: Summarizer,
    private tokenBudget = 400,
    private keepRecent = 4,
    private charsPerToken = 4
  ) {}

  private estimateTokens(): number {
    let body = this.summary ?? "";
    for (const m of this.messages) body += m.content;
    return Math.floor(body.length / this.charsPerToken);
  }

  append(role: string, content: string, pinned = false): void {
    this.messages.push({ role, content, pinned });
    if (this.estimateTokens() > this.tokenBudget) this.compact();
  }

  private compact(): void {
    if (this.messages.length <= this.keepRecent) return;
    const boundary = this.messages.length - this.keepRecent;
    const head = this.messages.slice(0, boundary);
    const tail = this.messages.slice(boundary);
    const toFold = head.filter((m) => !m.pinned);
    const toKeep = head.filter((m) => m.pinned);
    if (toFold.length === 0) return;
    const fresh = this.summarizer(toFold);
    this.summary = this.summary ? `${this.summary}\n${fresh}` : fresh;
    this.messages = [...toKeep, ...tail];
  }

  context(): Msg[] {
    const out: Msg[] = [];
    if (this.summary) {
      out.push({ role: "system", content: `[compacted summary]\n${this.summary}` });
    }
    return out.concat(this.messages);
  }

  tokens(): number {
    return this.estimateTokens();
  }
}

function naiveSummarizer(msgs: Msg[]): string {
  const decisions = msgs
    .filter((m) => m.content.toLowerCase().includes("decided"))
    .map((m) => `- ${m.content}`);
  const bullet = decisions.length ? decisions.join("\n") : "- no decisions recorded";
  return `Folded ${msgs.length} messages. Key decisions:\n${bullet}`;
}

const h = new CompactingHistory(naiveSummarizer, 60, 2);
h.append("system", "You are a build agent for a payments service.", true);
h.append("user", "Investigate why checkout latency doubled yesterday.");
h.append("assistant", "Traced it to a new retry loop. Decided to cap retries at 3.");
h.append("tool", "test suite output: 42 passed, 0 failed, coverage 91 percent");
h.append("assistant", "Decided to ship the retry cap behind a feature flag.");
h.append("user", "Good, now add a metric for retry count.");
for (const m of h.context()) {
  console.log(`[${m.role}] ${m.content.slice(0, 70)}`);
}
console.log("estimated tokens:", h.tokens());
```

### Python

Executed with `python3` (no external dependencies).

```python
from dataclasses import dataclass
from typing import Callable, List


@dataclass
class Message:
    role: str
    content: str
    pinned: bool = False


Summarizer = Callable[[List[Message]], str]


class CompactingHistory:
    """Keeps a sliding window of recent messages verbatim and replaces
    older messages with a single running summary once the estimated
    token budget is exceeded. Pinned messages are never summarized away."""

    def __init__(
        self,
        summarizer: Summarizer,
        token_budget: int = 400,
        keep_recent: int = 4,
        chars_per_token: int = 4,
    ) -> None:
        self.summarizer = summarizer
        self.token_budget = token_budget
        self.keep_recent = keep_recent
        self.chars_per_token = chars_per_token
        self.messages: List[Message] = []
        self.summary: str | None = None

    def _estimate_tokens(self) -> int:
        body = self.summary or ""
        for m in self.messages:
            body += m.content
        return len(body) // self.chars_per_token

    def append(self, role: str, content: str, pinned: bool = False) -> None:
        self.messages.append(Message(role, content, pinned))
        if self._estimate_tokens() > self.token_budget:
            self._compact()

    def _compact(self) -> None:
        if len(self.messages) <= self.keep_recent:
            return
        boundary = len(self.messages) - self.keep_recent
        head = self.messages[:boundary]
        tail = self.messages[boundary:]
        to_fold, to_keep = [], []
        for m in head:
            (to_keep if m.pinned else to_fold).append(m)
        if not to_fold:
            return
        new_summary = self.summarizer(to_fold)
        self.summary = (
            f"{self.summary}\n{new_summary}" if self.summary else new_summary
        )
        self.messages = to_keep + tail

    def context(self) -> List[Message]:
        out: List[Message] = []
        if self.summary:
            out.append(Message("system", f"[compacted summary]\n{self.summary}"))
        out.extend(self.messages)
        return out


def naive_summarizer(msgs: List[Message]) -> str:
    decisions = [m.content for m in msgs if "decided" in m.content.lower()]
    bullet = "\n".join(f"- {d}" for d in decisions) or "- no decisions recorded"
    return f"Folded {len(msgs)} messages. Key decisions:\n{bullet}"


if __name__ == "__main__":
    h = CompactingHistory(naive_summarizer, token_budget=60, keep_recent=2)
    h.append("system", "You are a build agent for a payments service.", pinned=True)
    h.append("user", "Investigate why checkout latency doubled yesterday.")
    h.append("assistant", "Traced it to a new retry loop. Decided to cap retries at 3.")
    h.append("tool", "test suite output: 42 passed, 0 failed, coverage 91 percent")
    h.append("assistant", "Decided to ship the retry cap behind a feature flag.")
    h.append("user", "Good, now add a metric for retry count.")
    for m in h.context():
        print(f"[{m.role}] {m.content[:70]}")
    print("estimated tokens:", h._estimate_tokens())
```

### Go

Executed with `go run` (Go toolchain present locally, no external
dependencies).

```go
package main

import (
	"fmt"
	"strings"
)

type Msg struct {
	Role    string
	Content string
	Pinned  bool
}

type Summarizer func(msgs []Msg) string

type CompactingHistory struct {
	summarizer  Summarizer
	tokenBudget int
	keepRecent  int
	charsPerTok int
	messages    []Msg
	summary     string
	hasSummary  bool
}

func NewCompactingHistory(s Summarizer, budget, keep int) *CompactingHistory {
	return &CompactingHistory{summarizer: s, tokenBudget: budget, keepRecent: keep, charsPerTok: 4}
}

func (h *CompactingHistory) estimateTokens() int {
	body := h.summary
	for _, m := range h.messages {
		body += m.Content
	}
	return len(body) / h.charsPerTok
}

func (h *CompactingHistory) Append(role, content string, pinned bool) {
	h.messages = append(h.messages, Msg{role, content, pinned})
	if h.estimateTokens() > h.tokenBudget {
		h.compact()
	}
}

func (h *CompactingHistory) compact() {
	if len(h.messages) <= h.keepRecent {
		return
	}
	boundary := len(h.messages) - h.keepRecent
	head := h.messages[:boundary]
	tail := h.messages[boundary:]
	var toFold, toKeep []Msg
	for _, m := range head {
		if m.Pinned {
			toKeep = append(toKeep, m)
		} else {
			toFold = append(toFold, m)
		}
	}
	if len(toFold) == 0 {
		return
	}
	fresh := h.summarizer(toFold)
	if h.hasSummary {
		h.summary = h.summary + "\n" + fresh
	} else {
		h.summary = fresh
		h.hasSummary = true
	}
	h.messages = append(toKeep, tail...)
}

func (h *CompactingHistory) Context() []Msg {
	out := []Msg{}
	if h.hasSummary {
		out = append(out, Msg{"system", "[compacted summary]\n" + h.summary, false})
	}
	return append(out, h.messages...)
}

func naiveSummarizer(msgs []Msg) string {
	var decisions []string
	for _, m := range msgs {
		if strings.Contains(strings.ToLower(m.Content), "decided") {
			decisions = append(decisions, "- "+m.Content)
		}
	}
	bullet := "- no decisions recorded"
	if len(decisions) > 0 {
		bullet = strings.Join(decisions, "\n")
	}
	return fmt.Sprintf("Folded %d messages. Key decisions:\n%s", len(msgs), bullet)
}

func main() {
	h := NewCompactingHistory(naiveSummarizer, 60, 2)
	h.Append("system", "You are a build agent for a payments service.", true)
	h.Append("user", "Investigate why checkout latency doubled yesterday.", false)
	h.Append("assistant", "Traced it to a new retry loop. Decided to cap retries at 3.", false)
	h.Append("tool", "test suite output: 42 passed, 0 failed, coverage 91 percent", false)
	h.Append("assistant", "Decided to ship the retry cap behind a feature flag.", false)
	h.Append("user", "Good, now add a metric for retry count.", false)
	for _, m := range h.Context() {
		c := m.Content
		if len(c) > 70 {
			c = c[:70]
		}
		fmt.Printf("[%s] %s\n", m.Role, c)
	}
	fmt.Println("estimated tokens:", h.estimateTokens())
}
```

Output, identical across all three, TypeScript, Python, Go.

```text
[system] [compacted summary]
Folded 2 messages. Key decisions:
- Traced it to a
[system] You are a build agent for a payments service.
[assistant] Decided to ship the retry cap behind a feature flag.
[user] Good, now add a metric for retry count.
estimated tokens: 72
```

Java and Rust were not attempted for this entry. The pattern is a plain
data-structure and control-flow exercise with no class-hierarchy or
ownership subtlety specific to either language that would make its
inclusion demonstrate anything the three samples above do not already
show; the three chosen languages, a typed scripting language, a dynamic
scripting language, and a systems language with manual memory layout,
already span the idiomatic range this pattern needs.
