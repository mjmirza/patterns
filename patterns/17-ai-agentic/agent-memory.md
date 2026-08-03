---
name: Agent Memory
slug: agent-memory
family: 17-ai-agentic
category: AI/Agentic
aliases: [Long-Term Memory, Stateful Agent Memory, Self-Editing Memory, Persistent Agent Memory]
first_described: "Packer, Wooders, Lin, Fang, Patil, Stoica, Gonzalez 2023 (MemGPT)"
maturity: established
related: [react, reflexion, chunking-strategies, model-context-protocol, hybrid-search, graphrag]
incompatible_with: []
verified: 2026-08-03
---

# Agent Memory

## 1. Name, aliases, and lineage

Agent Memory is the name this catalog uses for the family of designs that give
a language model agent state that survives past a single context window. The
model itself is stateless between calls. Every fact it appears to remember is
either still sitting in the prompt, or it was written somewhere outside the
prompt and read back in. Agent Memory is the discipline of deciding what gets
written, where it lives, and when it comes back.

The pattern has no single inventor in the way a Gang of Four pattern does,
because it grew out of a practical problem rather than a single publication.
Still, one paper gave it a name and a working shape that the field converged
on. Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G. Patil,
Ion Stoica, and Joseph E. Gonzalez, "MemGPT. Towards LLMs as Operating
Systems," arXiv paper number 2310.08560, October 2023, proposed treating the
context window as a scarce resource the way an operating system treats
physical RAM, with a paged "virtual context" that moves data between an
in-context tier and an out-of-context tier under the model's own control
(verified 2026-08-03, [arxiv.org/abs/2310.08560](https://arxiv.org/abs/2310.08560)).
The MemGPT team later split the name in two. MemGPT now refers to the design
pattern itself, an LLM given tools to edit its own memory, while Letta is the
company and open source agent framework that implements it in production
(verified 2026-08-03, [letta.com/blog/memgpt-and-letta](https://www.letta.com/blog/memgpt-and-letta)).

Aliases in circulation, each emphasizing a different facet of the same idea.

- **Long-Term Memory.** The framing used by LangGraph, which draws a hard line
  between short-term memory (the message history of one thread, held by a
  checkpointer) and long-term memory (facts that persist and are retrievable
  across threads, held by a store). LangGraph further splits long-term memory
  into semantic, episodic, and procedural memory, a taxonomy borrowed from
  cognitive science research on human memory and adapted for agents (verified
  2026-08-03,
  [docs.langchain.com/oss/python/langgraph/memory](https://docs.langchain.com/oss/python/langgraph/memory)).
- **Self-Editing Memory.** The framing Letta uses for its core memory blocks,
  strings of context that live inside the prompt and that the agent modifies
  through its own tool calls rather than through code the developer writes
  (verified 2026-08-03,
  [docs.letta.com/guides/agents/memory](https://docs.letta.com/guides/agents/memory)).
- **Persistent Agent Memory** and **Stateful Agent Memory.** Generic framing
  used across the wider agent-framework literature (mem0, and similar
  systems) to distinguish an agent that persists facts about a user or a task
  from one that starts every conversation from a blank prompt.

This entry treats these as one pattern family with several implementation
variants (dimension 8), because every one of them answers the same three
questions. What survives the end of a context window. Where does it live
while it is not in the prompt. What decides when it comes back into the
prompt.

## 2. Problem and context

An agent that runs a single request and returns an answer does not need this
pattern. The problem shows up the moment an agent is expected to behave as
though it has a past.

Concretely, the situation looks like one of these.

- A customer support agent talks to the same account across many separate
  sessions, spread over weeks, and is expected to remember that this customer
  already tried the standard fix, prefers email over phone, and has an open
  refund case.
- A coding agent works across many separate invocations on the same
  repository, is interrupted and resumed (a laptop sleeps, a session times
  out, a human ends the call for the day), and is expected to pick up from
  where it left off rather than re-discover the codebase from scratch each
  time.
- An agent processes a document, a log file, or a conversation that is larger
  than the model's context window can hold at once, and needs to reason over
  facts it read many turns ago without re-reading the entire source every
  time.
- An agent is meant to improve at a recurring task over repeated attempts, by
  writing down what worked and what failed, the way Reflexion-style agents
  keep an episodic buffer of past trajectories to condition future attempts
  (see the `reflexion` entry in this family for the mechanism this pattern
  supplies the input for).

The context that makes Agent Memory the right tool, rather than simply
padding the prompt, has three parts.

- The information the agent needs will not fit, or will not stay relevant, in
  a single context window across the full lifetime of the task.
- The agent's usefulness depends on continuity across calls, sessions, or
  threads that the underlying model has no native mechanism for.
- Some subset of the information is expensive to reconstruct (a long
  exploration of a codebase, a hard-won debugging trace, a customer's stated
  preference), so re-deriving it from scratch on every turn is wasteful or
  outright wrong when the source of truth (a conversation, an event) no
  longer exists to re-derive it from.

Outside that context, adding a memory system is adding infrastructure,
latency, and a second place for state to drift from the truth, for no
benefit. Dimension 4 makes this explicit.

## 3. Forces

Judgement statement. The costs and benefits below vary by workload; the
weighting here reflects general agent-building practice, not a single
authoritative source.

- **Context budget versus recall.** Favoring memory reduces the tokens spent
  re-explaining context every turn, and Anthropic's own framing of the memory
  tool leads with exactly this. Memory supports on-demand context
  retrieval, "reading files back on demand instead of loading everything up
  front," which "matters for long-running sessions that would otherwise
  overwhelm the context window" (verified 2026-08-03,
  [platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)).
  The cost is recall risk. Anything not written down, or written down badly,
  is gone, and a memory system can silently fail to retrieve something that
  was in fact stored.
- **Latency versus completeness.** LangGraph names this directly. An agent
  can write memories synchronously "in the hot path" (the user waits, but the
  memory is guaranteed to exist before the next turn) or asynchronously in
  the background (no added latency, but a race exists where the next turn
  can run before the memory write lands) (verified 2026-08-03, same
  LangGraph memory page). There is no configuration that removes this
  trade-off, it can only be moved.
- **Autonomy versus control.** A self-editing scheme (MemGPT, Letta core
  memory, the Claude memory tool) lets the model decide what is worth
  keeping, which scales to novel situations the developer did not
  anticipate, at the cost of the model sometimes keeping the wrong thing,
  forgetting to write something important, or (per Anthropic's own security
  note) attempting to write something sensitive that should never have been
  persisted at all (dimension 17). A developer-controlled extraction
  pipeline (mem0's model, dimension 8) is more predictable and auditable, at
  the cost of missing whatever the pipeline's extraction rules did not
  anticipate.
- **Cost and operability.** Every memory write is a database write, a vector
  upsert, or a file operation, and every memory read at the start of a task
  is an extra round trip before the agent can begin. mem0 states this
  pressure explicitly as the reason its "Memory Compression Engine" exists,
  to "automatically condense chat history into compact memories that cut
  tokens and latency while keeping the right context" (verified 2026-08-03,
  [mem0.ai](https://mem0.ai)). A memory store that is never pruned becomes
  an ever-growing retrieval problem in its own right.
- **Consistency versus staleness.** A fact written to memory today can become
  wrong tomorrow (a customer's preference changes, code that was described
  as "not yet implemented" gets implemented by someone else). Memory systems
  that never expire or re-verify facts favor consistency of the interface
  (memory is always there) over correctness of the content (memory can lie).

## 4. Applicability and non-applicability

### When to reach for it

- The agent runs across multiple sessions or invocations that must feel
  continuous to the person or system on the other end (support tooling,
  personal assistants, long-running coding agents).
- The task's working set exceeds the model's context window and cannot be
  reduced by better prompting alone (large document analysis, log
  investigation, a codebase too large to paste in full).
- The agent is expected to improve at a repeated or recurring task using
  evidence of what it tried before, rather than repeating the same failed
  approach every time.
- A human explicitly asks the agent to "remember" something across a session
  boundary, which is a direct signal that the interaction model requires
  persistence the base model does not provide.
- The agent operates unattended for long stretches and may be interrupted at
  any point (a crash, a timeout, a deliberate pause). Memory becomes the
  recovery mechanism, which is exactly how Anthropic frames the multisession
  software development pattern for the memory tool. an initializer session
  writes a progress log and feature checklist that later sessions read back
  to resume from the same state (verified 2026-08-03, same memory tool
  documentation page, "Multisession software development pattern" section).

### When not to reach for it

- The task is a single request-response exchange with no expectation of
  continuation. Adding a memory store here is pure overhead. a write that
  nothing will ever read.
- The information genuinely fits in the context window for the task's entire
  lifetime, and the task's lifetime is short. Prefer putting it directly in
  the prompt, or for retrieval over a fixed corpus reach for a plain
  retrieval pipeline (see the `hybrid-search` entry in this family for the
  retrieval mechanics), over standing up a stateful memory system for
  something that never changes and never grows.
- The information is safety-critical or compliance-sensitive (medical
  history, legal admissions, financial account numbers) and the application
  cannot guarantee an audit trail, access control, or a deletion path for
  the memory store. A self-editing memory tool with no oversight is the
  wrong place to let a model decide what to keep about a person under this
  condition. Use a developer-controlled write path with explicit validation
  instead (dimension 17).
- The "memory" being requested is actually a request for a longer context
  window, not for persistence across sessions. If the whole conversation
  still fits and there is no session boundary to cross, a model provider's
  larger context window or server-side compaction (Anthropic's compaction
  feature, which "automatically summarizes older conversation context
  server-side," verified 2026-08-03, same memory tool documentation page,
  "Using with compaction" section) solves the immediate problem with less
  moving infrastructure than a memory tool.
- Multiple independent agents or processes need the same memory guaranteed
  to be internally consistent at every instant (a shared ledger, an
  inventory count). Agent memory systems are built for retrieval quality and
  recall, not for the kind of atomic, linearizable guarantees a
  transactional database gives. Do not repurpose one as a system of record.

## 5. Structure

Every implementation in this family is built from the same six
participants, though a given system may collapse several of them into one
component or omit one entirely.

- **The Agent.** The language model plus its control loop. It decides, at
  each step, whether to read from memory, whether to write to memory, and
  what to do with what memory returns. In self-editing designs (MemGPT,
  Letta, Claude's memory tool) the Agent issues explicit tool calls to
  manage its own memory. In extraction-pipeline designs (mem0) the Agent's
  raw output is a side channel a separate process reads, and the Agent
  itself never calls a memory tool directly.
- **The Working Context.** What is actually inside the model's context
  window on a given call. system prompt, recent messages, and whatever
  memory content has been pulled in. This is the scarce resource the whole
  pattern exists to manage.
- **The Memory Store.** Durable storage outside the context window. a file
  system directory (the Claude memory tool), a key-value or vector database
  (mem0, Letta's archival memory), or a checkpoint database keyed by thread
  ID (LangGraph's short-term memory). This is where facts live between
  calls.
- **The Write Path.** The mechanism that moves a fact from a conversation
  into the Memory Store. This can be the model itself issuing a `create` or
  `str_replace` call (self-editing), or a separate extraction step, often
  another LLM call, that reads a transcript and decides what is worth
  keeping (mem0's "extracts and updates memories" step, verified 2026-08-03,
  same mem0.ai page).
- **The Retrieval Path.** The mechanism that decides what subset of the
  Memory Store re-enters the Working Context on a given call, and how. This
  ranges from "the agent explicitly reads a named file" (the Claude memory
  tool's `view` command) to "a background process runs semantic search over
  a vector index and injects the top results before the model sees the
  prompt" (mem0's "multi-signal retrieval").
- **The Scope Boundary.** The unit across which memory is shared or
  isolated. per-user, per-thread, per-agent, or shared across a whole team
  of agents (Letta's "shared blocks," where one memory block is attached to
  multiple agents at once, verified 2026-08-03, same Letta docs page).
  Getting scope wrong is the most common structural bug. leaking one user's
  memory into another user's context, or failing to share a fact that
  genuinely should be shared across an agent's sub-agents.

## 6. ASCII structure diagram

```
                    +-----------------------------------+
                    |              THE AGENT             |
                    |  (LLM + control loop)              |
                    +-----------------------------------+
                         |                    ^
                write    |                    | read
                (tool     |                    | (tool
                 call)    v                    | result)
                    +-----------------------------------+
                    |         WORKING CONTEXT            |
                    |  system prompt + recent turns +    |
                    |  memory content pulled in this call|
                    +-----------------------------------+
                         |                    ^
              WRITE PATH |                    | RETRIEVAL PATH
        (self-edit call, |                    | (explicit read,
         or async extract|                    |  semantic search,
         by a side agent)|                    |  or checkpoint load)
                         v                    |
                    +-----------------------------------+
                    |           MEMORY STORE             |
                    |  files / KV / vector index /       |
                    |  checkpoint DB, partitioned by      |
                    |  SCOPE BOUNDARY (user, thread,      |
                    |  agent, or shared block)            |
                    +-----------------------------------+
```

## 7. Dynamics

The interaction sequence below traces one turn of a self-editing scheme, the
shape Anthropic documents for the Claude memory tool, followed by the async
extraction variant used by mem0-style systems.

```
Self-editing sequence (Claude memory tool style):

  User            Agent (LLM)         App / Handler        Memory Store
   |  "help with     |                     |                    |
   |   this ticket"  |                     |                    |
   |---------------->|                     |                    |
   |                 |  tool_use: view     |                    |
   |                 |   "/memories"       |                    |
   |                 |-------------------->|                    |
   |                 |                     |  list directory    |
   |                 |                     |------------------->|
   |                 |                     |<--------------------
   |                 |<--------------------|  (listing)         |
   |                 |  tool_use: view     |                    |
   |                 |   "/memories/x.xml" |                    |
   |                 |-------------------->|                    |
   |                 |                     |  read file         |
   |                 |                     |------------------->|
   |                 |                     |<--------------------
   |                 |<--------------------|  (file content)    |
   |                 |  [uses memory to    |                    |
   |                 |   compose a reply]  |                    |
   |<----------------|                     |                    |
   |                 |  tool_use:          |                    |
   |                 |   str_replace       |                    |
   |                 |   (records a new    |                    |
   |                 |   fact learned)     |                    |
   |                 |-------------------->|                    |
   |                 |                     |  write file        |
   |                 |                     |------------------->|
   |                 |                     |<--------------------
   |                 |<--------------------|  "edit applied"    |
   v                 v                     v                    v

Async extraction sequence (mem0 style):

  Conversation turn completes
        |
        v
  raw transcript --------> Extraction pass (separate LLM or rules)
                                    |
                                    v
                          candidate facts, deduplicated
                          and merged against existing
                          memories for this user/scope
                                    |
                                    v
                          write to Memory Store
                          (does not block the reply
                           the user already received)

  Next conversation turn begins
        |
        v
  Retrieval pass queries Memory Store (semantic + keyword,
  "multi-signal retrieval") before the Agent's first LLM call,
  injects the top-k matching memories into the Working Context
```

The two sequences illustrate the latency versus completeness force from
dimension 3 directly. the self-editing sequence blocks the reply on memory
operations that happen inline as tool calls, while the async sequence
returns the reply first and lets memory catch up afterward, at the cost of
the very next turn possibly running before that write has landed.

## 8. Implementation variants

- **File-based self-editing memory (Claude memory tool).** The model is
  given one Anthropic-provided tool, `memory` (tool type `memory_20250818`),
  with six commands. `view`, `create`, `str_replace`, `insert`, `delete`,
  and `rename`, operating on files under a `/memories` prefix. The tool is
  client-side. the model only requests operations, and the calling
  application executes them against storage it controls (a local
  filesystem, a database, encrypted cloud storage) (verified 2026-08-03,
  same memory tool documentation page). The application is fully
  responsible for path validation, size limits, and expiration. The API
  sends no storage engine of its own. Trade-off. maximum control over where
  data lives and how it is secured, at the cost of writing and maintaining
  the handler yourself (though Anthropic ships reference handlers,
  `BetaLocalFilesystemMemoryTool`, in the Python and TypeScript SDKs).
- **Tiered core, archival, and recall memory (MemGPT / Letta).** Memory is
  split into at least two tiers. core memory, short strings organized into
  named blocks (a persona block, a human block) that are always present in
  context and editable by the model's own tools, and out-of-context storage
  that persists everything (state, messages, reasoning, tool calls) in a
  database "so they are never lost, even once evicted from the context
  window" (verified 2026-08-03, same Letta docs page). The original MemGPT
  paper frames this as "virtual context management" modeled on OS memory
  paging, moving data between tiers under an LLM-driven controller rather
  than a fixed algorithm (verified 2026-08-03, same arXiv abstract page).
  Trade-off. the tiering gives the model a clear mental model of "what is
  always visible" versus "what I have to go fetch," at the cost of needing
  the model to correctly judge what belongs in the scarce always-visible
  tier.
- **Extraction-pipeline memory (mem0 style).** A separate process, not the
  model's own tool calls, watches conversation turns, extracts candidate
  facts, deduplicates and merges them against what is already stored, and
  writes the result. Retrieval is likewise a separate, developer-controlled
  step ("multi-signal retrieval") that runs before the agent's LLM call
  rather than as an in-loop tool the model invokes on demand (verified
  2026-08-03, same mem0.ai page). Trade-off. the model never has to be
  prompted to remember things correctly, because a dedicated component owns
  that job, at the cost of an extra LLM call (or a rules engine) in the
  write path and less agent-driven flexibility about what counts as worth
  remembering.
- **Checkpointer plus store split (LangGraph).** Short-term memory (the
  message history of the current thread) is handled by a checkpointer that
  persists the graph's state automatically between steps of the same
  thread. Long-term memory (facts that must survive across threads) is
  handled by a separate store with custom namespaces, explicitly not the
  same mechanism as the checkpointer (verified 2026-08-03, same LangGraph
  memory concepts page). Trade-off. this variant is the most explicit about
  the semantic, episodic, and procedural memory taxonomy and gives the
  developer full control over when memories are written (synchronously in
  the hot path, or in a background task), at the cost of requiring the
  developer to design the retrieval and namespace scheme by hand rather
  than getting one out of the box.
- **Temporal knowledge graph memory.** Rather than storing memories as flat
  text blocks or vector embeddings alone, facts are stored as a graph with
  validity intervals, so a memory system can answer not only "what do we
  know about X" but "what did we know about X as of last Tuesday, and when
  did that change." This is the approach taken by knowledge-graph-based
  memory systems across the wider agent-framework field and shares its
  underlying retrieval substrate with the `graphrag` pattern in this
  family, applied to conversational facts rather than a static document
  corpus. Trade-off. this variant is the only one of the five that can
  correctly answer questions about how a fact changed over time, at the
  cost of a heavier storage and query engine than a flat key-value or
  vector store.

## 9. Known production uses

- **Claude memory tool, Anthropic API (Claude 4 and later models).** Shipped
  as a generally available, non-beta tool on the Messages API (tool type
  `memory_20250818`). Anthropic's own documentation names customer service
  ticket handling and multisession software development as reference use
  cases, and pairs the tool with a separate compaction feature for
  long-running agent sessions (verified 2026-08-03,
  [platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)).
- **Letta (formerly the MemGPT project), commercial agent framework.** Built
  directly on the MemGPT research design, Letta offers core memory blocks,
  shared blocks attachable across multiple agents at once, and persistent
  out-of-context storage of all agent state as a production service and
  open source framework (verified 2026-08-03,
  [docs.letta.com/guides/agents/memory](https://docs.letta.com/guides/agents/memory)
  and
  [letta.com/blog/memgpt-and-letta](https://www.letta.com/blog/memgpt-and-letta)).
- **mem0, memory infrastructure platform.** Described by its own team as
  "drop-in memory infrastructure for AI agents and apps," with a stated
  user base of over 90,000 developers, benchmarked memory retrieval
  performance against the LoCoMo, LongMemEval, and BEAM evaluation
  frameworks, and named use cases in healthcare, education, e-commerce, and
  customer support, including patient care assistants and therapy progress
  trackers (verified 2026-08-03, [mem0.ai](https://mem0.ai)). mem0 also
  states SOC 2 and HIPAA compliance features (governance controls, audit
  logging) as part of its enterprise offering, an explicit acknowledgment of
  the security concerns raised in dimension 17.
- **LangGraph, LangChain's agent orchestration framework.** Ships built-in
  short-term memory (checkpointer, thread-scoped) and long-term memory
  (store, cross-thread) as first-class primitives, with a documented
  semantic, episodic, and procedural memory taxonomy and explicit guidance
  on synchronous versus background memory writes (verified 2026-08-03,
  [docs.langchain.com/oss/python/langgraph/memory](https://docs.langchain.com/oss/python/langgraph/memory)).

## 10. Consequences

### Positive

- Agents can maintain continuity across sessions that would otherwise have
  to restart from a blank state every time, which is the entire reason the
  MemGPT paper frames LLMs as needing an operating-system-style memory
  hierarchy in the first place.
- Working-context token spend drops for long-running or repeat-visit tasks,
  because facts are fetched on demand rather than re-included in full on
  every turn, exactly the on-demand retrieval property Anthropic cites as
  the memory tool's reason to exist.
- Interrupted work becomes recoverable. A crashed or paused agent session
  can resume from a written progress log instead of losing all prior
  exploration, which Anthropic documents explicitly as the multisession
  development pattern's purpose.
- Memory that is written once and read many times amortizes the cost of
  expensive derivation (a long codebase exploration, a hard debugging
  trace) across every future session that benefits from it.

### Negative

- A second source of truth now exists alongside the underlying data the
  memory describes, and the two can drift apart. A memory that says "this
  feature is not yet implemented" is wrong the moment someone else
  implements it, and nothing forces the memory to update.
- Retrieval failure is silent by default. If the retrieval path does not
  surface a relevant memory (a bad query, an outdated index, a scope
  mismatch between where the fact was written and where it is being looked
  up), the agent behaves as if it never knew the fact, with no error raised
  anywhere.
- Self-editing designs hand the model discretion over what to keep, and a
  model can write low-value clutter into memory, or write something
  sensitive it should not persist (dimension 17), with no code-level gate
  on either outcome unless the developer adds one.
- Every additional memory tier (core, archival, recall, or checkpoint versus
  store) is an additional operational surface. a database to back up, a
  retrieval index to keep warm, an expiration policy to define and enforce.
  A memory store nobody prunes grows without bound.

## 11. Failure modes and misuse

Judgement statement. The symptom, cause, and fix triples below are drawn
from practitioner experience with agent memory systems rather than a single
cited incident report. Treat the specific numbers as illustrative, not
universal.

| Symptom | Cause | Fix |
|---|---|---|
| The agent repeats a question the user already answered earlier in the same day | The write path never fired (the model forgot to call the memory tool, or an async extraction job has not run yet) or the retrieval path queried the wrong scope | Add an explicit "check memory before asking" instruction (Anthropic's own memory tool auto-injects exactly this system prompt); verify write and read use the same scope key |
| The agent confidently states something that used to be true but no longer is | A memory was written once and never re-verified or expired; the underlying fact changed and nothing invalidated the stored copy | Add a memory expiration policy (Anthropic explicitly recommends periodically deleting memory files that have not been accessed in a long time); prefer re-deriving volatile facts over trusting a stale memory for anything time-sensitive |
| A user reports seeing information from another user's account | Memory was written or read under the wrong scope boundary, most often a missing or incorrect per-user namespace in the store | Enforce scope at the storage layer, not only in the prompt; every write and read must carry and validate a scope key, never rely on the model to remember whose data it is |
| The memory store balloons and retrieval latency climbs over months of use | No pruning, deduplication, or compression policy exists; every extracted fact is appended forever | Add deduplication and merge logic on write (mem0's stated approach), or a compression pass that condenses old memories, and set explicit size caps per scope |
| The agent's memory directory fills with duplicate or near-duplicate files that make later view calls noisy | The model was never told to keep memory organized, or it was told once and the instruction fell out of a compacted context | Reinforce organization in the system prompt on every call where the memory tool is present, not only in an initial instruction; Anthropic's documented guidance is to explicitly tell the model it may rename or delete stale files |
| An attacker's crafted input causes the agent to write or read a file outside the intended memory directory | The handler trusts the path string from the model without validating it, so a path such as /memories/../../secrets.env escapes the sandbox | Validate every path against a canonical, resolved form that must remain inside the memory root before executing any command; reject traversal sequences and their URL-encoded equivalents (Anthropic documents this exact attack under Path traversal protection) |
| The agent writes a customer's card number or password into a memory file | No validation layer sits between the model's create call and the storage write; the model's own judgement is the only safeguard | Add an explicit sensitive-data filter in the handler that strips or blocks known-sensitive patterns before the write reaches storage, rather than relying on the model to refuse on its own |

## 12. Trade-off matrix

Comparing Agent Memory against three named alternatives it is commonly
confused with or chosen over. plain RAG (retrieval over a static corpus,
the pattern this family covers separately for corpus-backed question
answering), a longer context window with no external store, and
server-side conversation compaction.

| Force | Agent Memory | RAG over static corpus | Longer context window alone | Server-side compaction |
|---|---|---|---|---|
| Persists across sessions | Yes, by design | No, corpus is not conversation-specific | No, ends when the window is exhausted or the session ends | Partially, summarized history persists within the session, not necessarily across a hard session boundary |
| Handles facts that change over time | Only if the design includes expiration or a temporal store (dimension 8, knowledge-graph variant) | Yes, as long as the corpus itself is kept current | Not applicable, nothing persists past the session | No, a summary is only as current as the moment it was generated |
| Developer effort to stand up | Moderate to high, storage, write path, retrieval path, scope design | Moderate, indexing pipeline, no write-back needed | Low, no infrastructure, only a model choice | Low, usually a provider feature flag |
| Risk of silent staleness or drift | High, unless actively managed (dimension 11) | Low if corpus refresh is scheduled | None, nothing to go stale | Low, but a summary can lose detail the original context had |
| Best fit | Multi-session agents, long-running tasks, personalization | Question answering over a fixed knowledge base | Single-session tasks that genuinely fit the model's window | Single long session that needs to survive its own length, not multiple sessions |

## 13. Related and incompatible patterns

- **RAG (corpus-backed retrieval).** RAG retrieves from a corpus the agent
  did not write; Agent Memory retrieves from a store the agent (or a
  process acting for it) did write. The retrieval mechanics, semantic
  search, hybrid search (`hybrid-search`), reranking, are frequently shared
  infrastructure between the two, and a memory store's retrieval path is
  often implemented as a corpus-retrieval pipeline pointed at
  conversation-derived facts instead of documents.
- **Reflexion** (`reflexion`). Reflexion depends on an episodic buffer of
  past attempts and their outcomes to condition future attempts; that
  buffer is a narrow, task-scoped instance of Agent Memory. Agent Memory as
  described in this entry is the general-purpose infrastructure; Reflexion
  is one specific consumer of the episodic-memory variant.
- **Chunking Strategies** (`chunking-strategies`). When a memory system
  stores long documents or transcripts rather than short discrete facts,
  the same chunking concerns that apply to a corpus-retrieval pipeline
  apply to memory content, particularly for the archival and
  knowledge-graph variants in dimension 8.
- **Model Context Protocol** (`model-context-protocol`). MCP standardizes
  how a model's tools are described and invoked; a memory store can be, and
  frequently is, exposed to a model as an MCP server rather than as a
  provider-specific tool like Anthropic's `memory_20250818`. The pattern
  (Agent Memory) is independent of the transport (MCP) that carries its
  tool calls.
- **ReAct** (`react`). ReAct's reasoning-then-acting loop is where memory
  read and write calls usually get interleaved with other tool use. an
  agent reasons, decides to check memory, acts on the result, and
  continues. Agent Memory supplies the state ReAct's loop reasons over
  across turns; ReAct supplies the control flow that decides when memory
  operations happen.
- **Not incompatible with any other pattern in this catalog on structural
  grounds**, but actively conflicting with strict statelessness
  requirements. an API contract or a regulatory boundary that requires a
  service to retain no information about a caller between requests is
  directly incompatible with any variant of Agent Memory that persists
  user-identifying facts, and the two cannot be reconciled by
  configuration alone.

## 14. Refactoring path in and out

### Introducing memory into a stateless agent

1. Identify the smallest unit of information that genuinely needs to
   survive a session boundary. Resist storing everything; start with one or
   two concrete facts a real user interaction demonstrated a need for (a
   stated preference, a decision already made, a piece of context that took
   real work to establish).
2. Pick a scope boundary before writing any code. per-user, per-thread, or
   shared. Getting this wrong later means migrating every stored record,
   not only changing a setting.
3. Choose a write path. If the agent already reasons in a tool-use loop
   (ReAct-shaped), a self-editing tool (dimension 8, file-based or tiered
   variant) is the smaller addition. If the agent's output is largely
   free-form text with no existing tool loop, an async extraction pass
   (dimension 8, extraction-pipeline variant) that runs after the response
   is sent is the smaller addition.
4. Add retrieval before the agent's first LLM call in a session, not after.
   Anthropic's own auto-injected system prompt for the memory tool states
   the protocol plainly. "ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING
   ANYTHING ELSE" (verified 2026-08-03, same memory tool documentation
   page). A retrieval step bolted on partway through a session finds
   nothing useful for the turns that already happened.
5. Add an expiration or pruning policy in the same change that introduces
   the write path, not as a follow-up. An unbounded memory store is the
   single most common operational failure in this pattern (dimension 11).
6. Add path or scope validation at the handler layer before the first
   write ever executes in production. Retrofitting validation after a
   memory tool has been live is retrofitting security onto data that may
   already be compromised.

### Removing memory when it stops earning its place

1. Confirm the usage pattern that justified memory has actually gone away
   (the product moved to single-session interactions, or the underlying
   data is now served fresh from a system of record instead of a stale
   copy).
2. Export or archive the existing memory store rather than deleting it
   outright; a memory system holds facts a user may still expect the agent
   to know, and losing them silently is a worse failure than the
   maintenance cost of keeping the pattern.
3. Remove the write path first, leaving retrieval in place, so no new
   stale data accumulates while the removal is evaluated.
4. Remove the retrieval path and the scope-checking code last, once
   confidence is high that nothing downstream still depends on memory
   being present.
5. Delete the storage infrastructure only after a full retention or backup
   window has passed with no incidents, consistent with the general
   practice of not tearing down state before its recovery window closes.

## 15. Testing and verification

Judgement statement. The following practices reflect general good practice
for testing stateful systems, adapted to this pattern; they are not drawn
from a single authoritative testing guide for agent memory specifically.

What becomes easier to test. the write path and retrieval path can be unit
tested independently of the language model, because both are deterministic
code once the model's tool call or extracted fact is treated as a fixture
input. A test can assert "given this create call, the resulting file has
this content" or "given this stored memory and this query, retrieval
returns this record" without invoking the model at all.

What becomes harder to test. whether the model reliably decides to write or
read memory at the right moments is a behavioral property of the model and
the prompt, not of the code, and is not deterministic. This is the same
class of testing problem as any other agentic tool-use behavior (see the
`function-calling` entry for the underlying mechanism), and the mitigation
is the same. evaluate over a fixed set of scenarios and measure a pass
rate, not a single pass or fail assertion.

Specific techniques that apply to this pattern.

- **Golden-transcript tests for the write path.** Feed a fixed conversation
  transcript through the extraction or self-edit logic and assert the exact
  memory content produced, independent of the live model, by mocking the
  model's tool call or extraction output as a fixture.
- **Scope isolation tests.** Write memory under one scope key, then assert
  that a read under a different scope key returns nothing. This is the
  single highest-value test in the whole pattern given how common scope
  leakage is as a failure mode (dimension 11).
- **Path traversal fuzzing.** For any file-based memory handler, run a
  fixed list of known traversal payloads (parent-directory sequences and
  their URL-encoded equivalents) against every command and assert every
  one is rejected. Anthropic documents this exact attack surface and lists
  these exact payload shapes as the ones to defend against (verified
  2026-08-03, same memory tool documentation page, "Path traversal
  protection" section).
- **Expiration and pruning tests.** Populate a store with records at known
  ages relative to a fixed clock, run the pruning job, and assert exactly
  the expected subset survives.
- **Staleness scenario tests.** Write a memory, then simulate the
  underlying fact changing, and assert the agent either re-verifies before
  relying on the stale memory or the memory itself carries a recorded write
  time the agent's prompt is instructed to weigh.

## 16. Observability signals

A healthy memory system shows a small, roughly stable set of writes per
session (spikes suggest either genuinely eventful sessions or a runaway
write loop) and a retrieval hit rate that stays consistent over time for
recurring users or threads (a sudden drop in hit rate for a returning user
usually means a scope key changed, an index was rebuilt without a
backfill, or storage was silently truncated).

What to log or trace on every memory operation.

- The scope key used for the operation (user, thread, or shared-block
  identifier), so a leak can be traced to exactly which write introduced
  it.
- Whether the write was synchronous (in the hot path, blocking the reply)
  or asynchronous (background), so latency regressions can be attributed
  correctly rather than blamed on the model call itself.
- The size of the memory store per scope over time, to catch unbounded
  growth before it becomes a retrieval latency problem.
- Retrieval query and the set of records it returned, at minimum in a
  sampled fashion, so an "the agent did not know something it should have"
  bug report can be root-caused to a bad query rather than a missing write.
- Rejected operations from path or scope validation, counted and alerted
  on, since a spike in rejections is either an attack in progress or a bug
  in the code that generates paths.

What a failing instance looks like on a dashboard. retrieval hit rate
trending toward zero for a cohort of users while write volume stays flat (a
retrieval bug, not a write bug), or store size per scope growing without
bound while read latency for that scope climbs in lockstep (a missing
pruning policy).

## 17. Security and privacy implications

This dimension is not silent for this pattern; the security surface is
substantial and every source consulted for this entry addresses it
directly, which is itself a signal of how central the concern is.

- **Path traversal.** Anthropic's own documentation names this as the
  primary attack against a file-based memory handler. a crafted path such
  as a parent-directory sequence reaching outside the intended prefix can
  escape the memory directory if the handler does not resolve and validate
  every path against the memory root before acting on it (verified
  2026-08-03, same memory tool documentation page). This applies to any
  file-based variant of the pattern, not only Anthropic's specific tool.
- **Sensitive data persistence.** A self-editing memory system can be
  asked, directly or through a crafted conversation, to write sensitive
  information (credentials, health details, financial data) into a store
  that then persists it indefinitely. Anthropic states that the model
  "usually refuses" to write sensitive information, then immediately
  qualifies that a production system needs its own validation layer for
  "stronger guarantees" (verified 2026-08-03, same memory tool
  documentation page), which is an explicit statement that model judgement
  alone is not a sufficient control.
- **Cross-scope leakage.** A memory store shared across users or threads
  without correct scope enforcement is a direct privacy violation. one
  person's stated preferences, account details, or conversation history
  becoming visible to another. This is not a hypothetical; it is the most
  cited failure mode across the sources consulted for this entry
  (dimension 11).
- **Compliance posture.** mem0's enterprise offering explicitly targets
  SOC 2 and HIPAA compliance with "governance controls" and "complete audit
  logging of all data access" as named features (verified 2026-08-03, same
  mem0.ai page), which indicates the market for this pattern treats
  compliance tooling (access control, audit trail, data portability) as a
  first-class requirement rather than an afterthought, particularly for the
  healthcare and financial use cases the pattern is commonly applied to.
- **Retention and the right to be forgotten.** A memory system that never
  expires records is, by construction, a permanent record of everything a
  user ever told the agent. Anthropic's explicit guidance to periodically
  delete memory files that have not been accessed in a long time (verified
  2026-08-03, same memory tool documentation page) is as much a privacy
  control as it is a storage-cost control, and any production deployment in
  a jurisdiction with data-deletion rights needs an explicit, testable
  deletion path, not only a pruning-for-cost job.

## 18. References

1. Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G. Patil,
   Ion Stoica, and Joseph E. Gonzalez. "MemGPT. Towards LLMs as Operating
   Systems." arXiv paper number 2310.08560, October 2023.
   [arxiv.org/abs/2310.08560](https://arxiv.org/abs/2310.08560), verified
   2026-08-03.
2. Letta. "MemGPT and Letta."
   [letta.com/blog/memgpt-and-letta](https://www.letta.com/blog/memgpt-and-letta),
   verified 2026-08-03.
3. Letta. "Agent Memory" (developer guide).
   [docs.letta.com/guides/agents/memory](https://docs.letta.com/guides/agents/memory),
   verified 2026-08-03.
4. Anthropic. "Memory tool," Claude Developer Platform documentation.
   [platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool),
   verified 2026-08-03.
5. mem0. Product and architecture overview.
   [mem0.ai](https://mem0.ai), verified 2026-08-03.
6. LangChain. "Memory," LangGraph concepts documentation.
   [docs.langchain.com/oss/python/langgraph/memory](https://docs.langchain.com/oss/python/langgraph/memory),
   verified 2026-08-03.

## Code examples

Three languages were run for this entry. Python, Go, and Rust. Java was not
available on the machine used to write this entry (no Java runtime
installed) and TypeScript and Swift were skipped in favor of showing three
distinct implementation variants of the pattern rather than the same
variant three times.

### Python. tiered core and archival memory, self-edited by tool calls

This mirrors the MemGPT and Letta shape from dimension 8, a small always-in
context "core" block the agent edits directly, and a larger "archival"
store the agent searches on demand rather than holding in context. No
network calls; the "agent" here is a stand-in loop that issues the same
tool calls a real model would issue, so the memory manager itself can be
exercised and tested in isolation, per dimension 15.

```python
"""Tiered agent memory. core (always in context) and archival (searched on demand)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


class AgentMemoryError(Exception):
    pass


@dataclass
class CoreBlock:
    name: str
    content: str
    max_chars: int = 200

    def replace(self, new_content: str) -> None:
        if len(new_content) > self.max_chars:
            raise AgentMemoryError(
                f"core block '{self.name}' exceeds {self.max_chars} chars"
            )
        self.content = new_content


@dataclass
class ArchivalRecord:
    scope: str
    text: str
    tags: tuple[str, ...] = field(default_factory=tuple)


class TieredMemory:
    """Core blocks live in-context; archival records are searched, not loaded."""

    def __init__(self) -> None:
        self._core: dict[str, CoreBlock] = {}
        self._archival: list[ArchivalRecord] = []

    def core_view(self) -> str:
        return "\n".join(f"[{b.name}] {b.content}" for b in self._core.values())

    def core_write(self, scope: str, name: str, content: str) -> None:
        key = f"{scope}:{name}"
        block = self._core.setdefault(key, CoreBlock(name=name, content=""))
        block.replace(content)

    def archival_insert(self, scope: str, text: str, tags: tuple[str, ...] = ()) -> None:
        self._archival.append(ArchivalRecord(scope=scope, text=text, tags=tags))

    def archival_search(self, scope: str, query: str, top_k: int = 3) -> list[str]:
        # Deliberately simple keyword overlap, standing in for a real
        # vector or hybrid search backend (see the hybrid-search entry).
        query_terms = set(query.lower().split())
        scored: list[tuple[int, str]] = []
        for record in self._archival:
            if record.scope != scope:
                continue  # scope boundary enforced at the storage layer
            overlap = len(query_terms & set(record.text.lower().split()))
            if overlap:
                scored.append((overlap, record.text))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [text for _, text in scored[:top_k]]


def run_session(memory: TieredMemory, scope: str) -> None:
    # Session 1. the agent learns a preference and records it in core memory
    # because it will need it on every future turn for this customer.
    memory.core_write(scope, "customer", "Acme Corp; prefers email follow-ups")

    # A one-off fact that does not need to sit in the always-visible core
    # block goes to archival memory instead, retrieved only when relevant.
    memory.archival_insert(
        scope,
        "Acme Corp escalated a billing dispute on their March invoice.",
        tags=("billing", "escalation"),
    )
    memory.archival_insert(
        scope,
        "Acme Corp's primary contact changed to Dana Reyes in April.",
        tags=("contact",),
    )

    # Session 2 (a later, separate call). the agent reads core memory first,
    # exactly as the memory tool's auto-injected protocol instructs.
    print("core memory at start of next session:")
    print(memory.core_view())

    hits = memory.archival_search(scope, "billing dispute invoice")
    print("archival hits for 'billing dispute invoice':", hits)


if __name__ == "__main__":
    store = TieredMemory()
    run_session(store, scope="user:acme-corp")

    # Scope isolation test, per dimension 15. a different scope sees nothing.
    other_scope_hits = store.archival_search("user:other-customer", "billing")
    assert other_scope_hits == [], "scope leakage: memory crossed a scope boundary"
    print("scope isolation check passed")
```

Ran with `python3 tiered_memory.py`.

```
core memory at start of next session:
[customer] Acme Corp; prefers email follow-ups
archival hits for 'billing dispute invoice': ['Acme Corp escalated a billing dispute on their March invoice.']
scope isolation check passed
```

### Go. checkpointer plus store split, synchronous versus background writes

This mirrors the LangGraph shape from dimension 8, short-term memory scoped
to a single thread (a `Checkpointer`), and long-term memory scoped across
threads (a `Store`), with an explicit choice at write time between a
synchronous write (blocks, guaranteed visible next turn) and a background
write (does not block, but a race can leave the next turn without it, per
dimension 3). Mutual exclusion is a small channel-based gate rather than
the standard library mutex type, purely so this example reads cleanly
standing alone.

```go
package main

import (
	"fmt"
	"time"
)

// gate is a channel-based mutual-exclusion latch: receiving from it
// acquires exclusive access, sending back to it releases that access.
type gate chan struct{}

func newGate() gate {
	g := make(gate, 1)
	g <- struct{}{}
	return g
}

func (g gate) acquire() { <-g }
func (g gate) release() { g <- struct{}{} }

// Checkpointer holds short-term, thread-scoped memory. the message
// history of one conversation, gone once the thread is done with it.
type Checkpointer struct {
	g        gate
	byThread map[string][]string
}

func NewCheckpointer() *Checkpointer {
	return &Checkpointer{g: newGate(), byThread: make(map[string][]string)}
}

func (c *Checkpointer) Append(threadID, message string) {
	c.g.acquire()
	defer c.g.release()
	c.byThread[threadID] = append(c.byThread[threadID], message)
}

func (c *Checkpointer) History(threadID string) []string {
	c.g.acquire()
	defer c.g.release()
	out := make([]string, len(c.byThread[threadID]))
	copy(out, c.byThread[threadID])
	return out
}

// Store holds long-term, cross-thread memory, namespaced by scope
// (usually a user, not a single conversation thread).
type Store struct {
	g    gate
	byNS map[string]map[string]string
}

func NewStore() *Store {
	return &Store{g: newGate(), byNS: make(map[string]map[string]string)}
}

func (s *Store) writeSync(namespace, key, value string) {
	s.g.acquire()
	defer s.g.release()
	if s.byNS[namespace] == nil {
		s.byNS[namespace] = make(map[string]string)
	}
	s.byNS[namespace][key] = value
}

// writeAsync returns immediately; the write lands on its own goroutine.
// This is the latency-versus-completeness trade-off from dimension 3.
// the caller's turn is not blocked, but a read immediately after this
// call can race the write and miss it.
func (s *Store) writeAsync(namespace, key, value string) <-chan struct{} {
	done := make(chan struct{})
	go func() {
		time.Sleep(5 * time.Millisecond) // stand-in for real write latency
		s.writeSync(namespace, key, value)
		close(done)
	}()
	return done
}

func (s *Store) read(namespace, key string) (string, bool) {
	s.g.acquire()
	defer s.g.release()
	v, ok := s.byNS[namespace][key]
	return v, ok
}

func main() {
	checkpointer := NewCheckpointer()
	store := NewStore()

	threadID := "thread-42"
	userNamespace := "user:jordan"

	checkpointer.Append(threadID, "user: I only ever want dark roast recommendations.")
	checkpointer.Append(threadID, "agent: noted, dark roast only.")
	fmt.Println("short-term history for this thread:", checkpointer.History(threadID))

	// A fact worth keeping past this one thread goes to the long-term
	// store under the user's namespace, synchronously, because the very
	// next turn in this same thread needs to see it.
	store.writeSync(userNamespace, "roast_preference", "dark roast only")
	if v, ok := store.read(userNamespace, "roast_preference"); ok {
		fmt.Println("long-term memory available immediately:", v)
	}

	// A lower-priority fact is written in the background instead.
	done := store.writeAsync(userNamespace, "last_seen_topic", "coffee preferences")
	<-done // for this example only, wait to make the race deterministic
	if v, ok := store.read(userNamespace, "last_seen_topic"); ok {
		fmt.Println("background write landed:", v)
	}

	// Scope isolation, same check as the Python example. a different
	// namespace never sees another user's long-term memory.
	if _, ok := store.read("user:someone-else", "roast_preference"); ok {
		panic("scope leakage: memory crossed a namespace boundary")
	}
	fmt.Println("scope isolation check passed")
}
```

Ran with `go run checkpointer_store.go`.

```
short-term history for this thread: [user: I only ever want dark roast recommendations. agent: noted, dark roast only.]
long-term memory available immediately: dark roast only
background write landed: coffee preferences
scope isolation check passed
```

### Rust. file-based memory handler with path traversal protection

This mirrors the Claude memory tool shape from dimension 8 and dimension 17
directly, a client-side handler for `view`, `create`, and `delete` commands
against a `/memories` root, with the path validation Anthropic's own
documentation names as mandatory before executing any command.

```rust
use std::collections::HashMap;
use std::path::{Component, Path, PathBuf};

const MEMORY_ROOT: &str = "/memories";

#[derive(Debug)]
enum MemoryError {
    PathTraversal(String),
    NotFound(String),
    AlreadyExists(String),
}

impl std::fmt::Display for MemoryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            MemoryError::PathTraversal(p) => write!(f, "rejected path outside memory root, {p}"),
            MemoryError::NotFound(p) => write!(f, "The path {p} does not exist."),
            MemoryError::AlreadyExists(p) => write!(f, "Error, file {p} already exists"),
        }
    }
}

/// Resolves a requested path to a canonical form and rejects anything
/// that would escape MEMORY_ROOT, without touching the real filesystem,
/// so it can be unit tested with fabricated paths (dimension 15).
fn validate_path(requested: &str) -> Result<PathBuf, MemoryError> {
    let candidate = Path::new(requested);
    let mut normalized = PathBuf::new();
    for component in candidate.components() {
        match component {
            Component::ParentDir => {
                return Err(MemoryError::PathTraversal(requested.to_string()));
            }
            Component::CurDir => {}
            Component::Normal(part) => normalized.push(part),
            Component::RootDir => normalized.push("/"),
            Component::Prefix(_) => {
                return Err(MemoryError::PathTraversal(requested.to_string()));
            }
        }
    }
    let root = Path::new(MEMORY_ROOT);
    if !normalized.starts_with(root) {
        return Err(MemoryError::PathTraversal(requested.to_string()));
    }
    Ok(normalized)
}

struct FileMemoryHandler {
    // An in-memory stand-in for real storage on disk or in a database.
    files: HashMap<PathBuf, String>,
}

impl FileMemoryHandler {
    fn new() -> Self {
        Self { files: HashMap::new() }
    }

    fn view(&self, requested: &str) -> Result<String, MemoryError> {
        let path = validate_path(requested)?;
        self.files
            .get(&path)
            .cloned()
            .ok_or_else(|| MemoryError::NotFound(requested.to_string()))
    }

    fn create(&mut self, requested: &str, content: &str) -> Result<(), MemoryError> {
        let path = validate_path(requested)?;
        if self.files.contains_key(&path) {
            return Err(MemoryError::AlreadyExists(requested.to_string()));
        }
        self.files.insert(path, content.to_string());
        Ok(())
    }

    fn delete(&mut self, requested: &str) -> Result<(), MemoryError> {
        let path = validate_path(requested)?;
        self.files
            .remove(&path)
            .map(|_| ())
            .ok_or_else(|| MemoryError::NotFound(requested.to_string()))
    }
}

fn main() {
    let mut memory = FileMemoryHandler::new();

    memory
        .create("/memories/customer.txt", "Acme Corp; prefers email follow-ups")
        .expect("create should succeed on a fresh path");
    println!("view: {}", memory.view("/memories/customer.txt").unwrap());

    // The exact attack Anthropic's documentation names. a crafted path
    // attempting to escape the memory root.
    match memory.view("/memories/../../secrets.env") {
        Err(MemoryError::PathTraversal(p)) => {
            println!("path traversal correctly rejected, {p}")
        }
        other => panic!("expected a rejected traversal, got {other:?}"),
    }

    match memory.create("/memories/customer.txt", "duplicate") {
        Err(MemoryError::AlreadyExists(p)) => {
            println!("duplicate create correctly rejected, {p}")
        }
        other => panic!("expected AlreadyExists, got {other:?}"),
    }

    memory.delete("/memories/customer.txt").expect("delete should succeed");
    match memory.view("/memories/customer.txt") {
        Err(MemoryError::NotFound(p)) => println!("deleted file correctly reports not found, {p}"),
        other => panic!("expected NotFound after delete, got {other:?}"),
    }
}
```

Compiled and ran with `rustc memory_handler.rs -o memory_handler && ./memory_handler`.

```
view: Acme Corp; prefers email follow-ups
path traversal correctly rejected, /memories/../../secrets.env
duplicate create correctly rejected, /memories/customer.txt
deleted file correctly reports not found, /memories/customer.txt
```
