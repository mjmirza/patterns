---
name: Tool Result Caching
slug: tool-result-caching
family: 17-ai-agentic
category: AI Agentic
aliases: [Tool Call Caching, Function Result Memoization, Action Caching]
first_described: "General memoization traces to Donald Michie 1968 (Nature); applied specifically to LLM agent tool and function calls by practitioner tooling from 2023 onward, for example GPTCache (Zilliz, March 2023) and the LangGraph node CachePolicy"
maturity: established
related: [function-calling, react, orchestrator-worker, plan-execute, reflexion]
incompatible_with: []
verified: 2026-08-02
---

# Tool Result Caching

## 1. Name, aliases, and lineage

The canonical name in this catalog is Tool Result Caching, chosen because it
names the artifact being stored, the output of a tool invocation, rather than
the mechanism doing the storing. Three aliases circulate for the same idea.
Tool Call Caching emphasizes the call site rather than the artifact. Function
Result Memoization borrows the older programming-languages term directly.
Action Caching appears in agent frameworks that call a tool invocation an
action, most visibly in reinforcement-learning-adjacent agent literature.

The underlying mechanism is memoization, a term coined by Donald Michie in
"'Memo' Functions and Machine Learning", Nature, volume 218, issue 5136,
pages 19 to 22, 1968. Michie described a function that records each input
and output pair it computes and consults that record before repeating the
computation, and the Wikipedia summary of the paper's history confirms the
coinage and the citation
(https://en.wikipedia.org/wiki/Memoization, verified 2026-08-02). Michie's
memo functions targeted pure mathematical functions computed by a single
process. Tool Result Caching applies the same idea to a different unit of
work, an agent's call to an external tool through a model's function-calling
or tool-use interface, and it inherits every one of memoization's classical
concerns, purity, key stability, and eviction, while adding concerns
memoization never had to face, network calls, side effects on a live
external system, multi-agent concurrency, and a language model deciding at
runtime, non-deterministically, whether to make the call again.

No single paper or vendor announcement names this pattern for agents the way
Anthropic named Contextual Retrieval or the way the Toolformer paper named
function calling's academic precursor. It exists today as convergent
practitioner engineering, visible in named, sourced framework features
rather than in one canonical publication. GPTCache, a semantic caching
library from the Zilliz team, was created on 2023-03-24 according to its
GitHub repository metadata (https://github.com/zilliztech/GPTCache, verified
2026-08-02) and is described in its own repository as a semantic cache
"fully integrated with LangChain and llama_index". LangGraph, LangChain's
graph-based agent runtime, ships a node-level `CachePolicy` that the
documentation describes as caching "of tasks/nodes based on the input to the
node" (LangChain, "Graph API", https://docs.langchain.com/oss/python/langgraph/graph-api,
verified 2026-08-02), and a node in that runtime is commonly a tool call.
This entry treats the pattern as established rather than canonical for
exactly this reason, real and widely implemented, but without one
foundational citation the whole field points back to.

Mainstream agent SDKs frequently leave this concern to the application
layer rather than shipping it by default. The Vercel AI SDK's own
tool-calling documentation describes execution callbacks, error handling,
and multi-step tool calls in detail, and separate direct review of that
documentation confirmed it offers no caching, memoization, or repeated-call
avoidance mechanism for a tool's `execute` function (Vercel, "Tools and
Tool Calling", AI SDK Core documentation,
https://ai-sdk.dev/docs/ai-sdk-core/tools-and-tool-calling, verified
2026-08-02). That gap is a large part of why this pattern belongs in a
catalog at all, it is something a team builds on top of a tool-calling SDK
rather than a switch the SDK turns on for them.

A naming trap worth flagging immediately, because it recurs through every
dimension below. "Caching" in an LLM agent context is used for at least two
unrelated mechanisms that share a word and nothing else. Prompt caching, also
called context caching, stores the tokenized prefix of a model request so the
model provider skips reprocessing tokens it has seen before. Tool Result
Caching stores the return value of an external call so the agent's own
process skips making that call again. Dimension 4 and dimension 13 draw the
line between them precisely, because conflating the two is the most common
error a reader carries into this pattern from adjacent reading.

## 2. Problem and context

An agent built on a tool-calling loop, the mechanism the Function Calling
entry in this family describes, asks a model to decide, turn by turn,
whether to answer directly or invoke a named tool with structured arguments.
Nothing in that loop remembers what happened on a previous turn beyond the
transcript the model can read. If the model decides on turn three to call
`search_web(query="EU AI Act enforcement date")`, and on turn seven, after a
detour through two other tools, decides it needs that same fact again, the
loop calls the search API a second time. It pays a second network round
trip, a second dollar cost if the tool is metered, and a second window of
latency the person waiting on the answer has to sit through.

This is not a hypothetical corner case, it is the default behavior of the
pattern the loop is built on. A ReAct-style reasoning-and-acting loop (the
React entry in this family) revisits earlier subgoals when it backtracks
from a dead end, and a multi-agent orchestrator-worker system routinely
dispatches near-identical sub-queries to more than one worker because the
orchestrator does not track what any worker has already asked. A
plan-and-execute agent that replans after a step fails often reissues the
steps that already succeeded, because the plan is regenerated rather than
resumed. Reflexion-style self-critique loops explicitly retry a failed
approach, which for a tool call frequently means calling the exact same
tool with the exact same arguments a second time expecting nothing to have
changed, because nothing did, the tool failed for a reason unrelated to its
inputs.

The context that creates the need has three ingredients present together.
First, the tool has a real cost to invoke, in latency, in money, in rate
limit budget, or in load placed on a system that was not built to answer
the same question from an LLM a dozen times a minute. A local, pure,
sub-millisecond calculator tool does not create this problem regardless of
how often it is called. A web search API, a vector database query, a paid
enrichment lookup, or a slow legacy SOAP endpoint does. Second, the same
tool is plausibly called more than once with the same arguments inside a
bounded window, whether within one agent trajectory, across sibling workers
in one orchestration, or across independent users asking a shared support
bot the same frequently asked question. Third, the tool's answer is stable
enough over that window that a stored answer is still true when it is
reused, which is a claim about the tool's semantics, not about the caching
mechanism, and is the subject of dimension 4.

## 3. Forces

Freshness against cost. A cached answer is by definition a past answer, and
every tool has some rate at which the world changes underneath it. A
company's registered address changes rarely. A stock price changes by the
second. The pattern only pays off when the tool's own freshness requirement
is looser than the caching window chosen for it, and choosing that window
wrong in either direction either serves stale data or throws away savings
that were available.

Safety against savings. The single most consequential force in this pattern,
because it is the one that turns a performance optimization into a
correctness bug or a financial incident. Caching a read is close to free to
get wrong, the worst case is a stale answer. Caching a write, or treating a
call with side effects as if repeating it were harmless, can duplicate a
charge, send a second email, or place a second order. The pattern must
therefore sacrifice generality, it applies cleanly only to a bounded class
of tool calls, in exchange for the safety of never silently duplicating an
effect.

Key precision against hit rate. An exact-match cache, keyed on a canonical
serialization of the tool name and its arguments, never returns a wrong
answer for a call it has genuinely seen before, but it also never matches a
call that differs from a previous one by only a word, `"EU AI Act
enforcement date"` against `"when does the EU AI Act take effect"`. A
semantic cache, keyed on the meaning of the call rather than its literal
text, catches that second case and raises the hit rate, at the cost of an
embedding computation on every lookup and a similarity threshold that is
itself a tunable, fallible judgment call. GPTCache's own architecture
documents this trade directly by shipping a pluggable similarity evaluator
rather than a single fixed comparison
(https://github.com/zilliztech/GPTCache, verified 2026-08-02).

Storage cost against retrieval speed. An in-process map is nearly free to
read and vanishes the moment the process restarts. A shared store such as
Redis survives restarts and lets every agent instance in a fleet share one
cache, at the cost of a network hop on every lookup and a real operational
dependency that itself needs to be up.

Isolation against reuse. A cache shared across users multiplies the hit rate
of a frequently asked query, but a cache that stores one user's tool result
and serves it to a different user is a data leak the moment the tool's
output contains anything scoped to the caller, an account balance, a
personalized recommendation, a private document.

Complexity against transparency. Every layer added, a key function, an
eviction policy, an invalidation hook, a semantic threshold, is a layer that
can itself be wrong, and a wrong cache is a defect a debugging session has
to first discover is even in play before it can be diagnosed. A team that
adds this pattern takes on a second surface, the cache's own correctness, in
exchange for the first surface's, the tool's, reduced load.

## 4. Applicability and non-applicability

Reach for Tool Result Caching when these hold together.

- The tool call carries a real cost, latency measured in the hundreds of
  milliseconds or more, a metered dollar price, a rate-limited quota, or
  heavy load on a downstream system.
- The tool is read-only or safely repeatable, meaning calling it twice with
  the same arguments produces the same answer and changes nothing in the
  world by being called again. This maps directly onto the Model Context
  Protocol's own tool annotation fields, `readOnlyHint`, "If true, the tool
  does not modify its environment", and `idempotentHint`, "If true, calling
  the tool repeatedly with the same arguments will have no additional
  effect on the its environment" (Model Context Protocol, `ToolAnnotations`
  interface, schema.ts, 2025-06-18 revision,
  https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/schema/2025-06-18/schema.ts,
  verified 2026-08-02). A tool a server author has marked with either hint
  is a strong candidate. A tool with no annotation at all needs a human
  judgment call before it is cached, per the spec's own warning that
  clients must treat annotations from untrusted servers with suspicion.
- The same arguments are plausibly repeated inside a window where the
  underlying data has not changed enough to matter, whether within one agent
  trajectory's backtracking, across sibling workers in a fan-out
  orchestration, or across independent requests to a shared service.
- A small amount of staleness is acceptable for the specific data the tool
  returns, and that acceptable staleness window can be named as a concrete
  number, not left implicit.

Do NOT reach for this pattern in the following cases, and the reason matters
as much as the rule.

- **The tool mutates state and has no idempotency key.** Sending an email,
  placing an order, writing a database row, or calling a payment API a
  second time because a cache layer decided the first call's arguments
  looked familiar is not a caching bug, it is a duplicated real-world
  effect. The MCP annotation model marks this explicitly, `idempotentHint`
  and `destructiveHint` apply "only when `readOnlyHint == false`",
  meaning the protocol authors themselves treat non-read-only tools as a
  distinct, riskier class that needs its own reasoning, not a blanket cache.
  Where repetition safety is genuinely needed for a write, the correct tool
  is an idempotency key baked into the write path itself, not a cache in
  front of it, see dimension 12 and dimension 13.
- **The tool's output depends on hidden, ambient, or per-caller state.** A
  tool that returns "the current user's remaining quota", "the contents of
  the session the caller is authenticated as", or "a personalized
  recommendation" cannot be safely keyed on its visible arguments alone,
  because the same visible arguments produce a different true answer for a
  different caller or a different moment in that caller's session. Caching
  it either serves the wrong person's data to the wrong person, a privacy
  failure, or serves a correct-looking but stale personalization, a quieter
  correctness failure.
- **The tool is deliberately stochastic and the randomness is the point.**
  A dice-roll tool, a random-sample generator, or a tool whose entire job is
  to introduce variety into an agent's output should never be memoized, a
  cached "random" number is not random, and caching it defeats the tool's
  purpose rather than optimizing it.
- **The data changes faster than any workable cache window.** A live stock
  quote, a real-time sensor reading, or an in-flight auction price has a
  staleness tolerance measured in single-digit seconds or less, and by the
  time a workable TTL is chosen it has shrunk the hit rate to near zero
  anyway, at which point the caching layer adds complexity for savings that
  do not materialize.
- **The call happens exactly once per unit of work with no plausible
  repeat.** A one-shot batch job that touches each input record a single
  time creates no repetition for a cache to exploit. Adding one anyway pays
  the storage and key-computation cost on every call while the hit rate
  stays at zero.
- **The need is actually prompt or context caching, not tool result
  caching.** This is the most common confusion in practice. Anthropic's
  prompt caching stores prompt prefix tokens up to a specified breakpoint,
  including, by design, the tool use and tool result content blocks that
  already sit inside a conversation transcript, one of the content types
  Anthropic's own documentation lists as cacheable (Anthropic, "Prompt
  caching",
  https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching,
  verified 2026-08-02). That mechanism saves the provider from
  reprocessing tokens the model has already seen. It does nothing to stop
  the agent from calling the tool a second time to produce a fresh result
  that then gets tokenized and sent again. The two mechanisms solve
  adjacent but distinct problems, one saves token processing on a request
  the agent has already decided to make, the other saves the agent from
  making the request at all, and reaching for prompt caching when the
  actual waste is a redundant network call leaves the real cost untouched.
  Likewise LangChain's `BaseCache` abstraction, keyed on "a prompt string
  combined with an `llm_string`", is scoped to language model generations,
  not arbitrary tool invocations, and using it as a substitute for
  tool-level caching silently misses every non-LLM tool call in an agent's
  loop.
- **The tool requires a human confirmation gate regardless of repetition
  safety.** The Model Context Protocol's own guidance states there
  "SHOULD always be a human in the loop with the ability to deny tool
  invocations" for trust and safety
  (https://modelcontextprotocol.io/specification/2025-06-18/server/tools,
  verified 2026-08-02). Silently serving a cached result to skip that
  confirmation step defeats the safeguard even when the underlying call
  would have been idempotent, because the person never sees that the
  action, cached or not, is about to be attributed to them again.

## 5. Structure

Six participants, named by the role each plays in the loop.

- **Agent Loop.** The model-driven controller that decides, turn by turn,
  which tool to call with which arguments, per the Function Calling entry
  in this family. It is the consumer of the cache and has no awareness that
  caching is happening beneath it, which is the point, caching is
  transparent to the reasoning above it.
- **Tool Dispatcher.** The piece of infrastructure code, often called a
  tool executor, an action runner, or an MCP client in a Model Context
  Protocol deployment, that receives the model's chosen tool name and
  arguments and routes the call to either the cache or the real tool. This
  is where the pattern's logic actually lives.
- **Cache Key Function.** A deterministic function from the tool's name,
  its arguments, and any context that legitimately changes the answer, such
  as a tenant identifier, to a stable lookup key. Getting this function
  wrong, most often by serializing arguments in a way that varies across
  calls that should be treated as identical, is dimension 11's single most
  common failure.
- **Cache Store.** The place cached entries live, ranging from a plain
  in-process map to a shared key-value store such as Redis to a
  vector-indexed semantic store such as the one GPTCache builds on top of
  Milvus, FAISS, or a similar embedding index
  (https://github.com/zilliztech/GPTCache, verified 2026-08-02).
- **Policy Layer.** The rules that decide whether a given tool call is
  eligible for caching at all, and for how long a cached entry stays valid.
  This is where a `readOnlyHint` or `idempotentHint` annotation, a
  per-tool TTL, and an explicit deny-list for tools such as
  `send_payment` all live together.
- **Tool Executor.** The code that performs the real call against the
  external system when the cache reports a miss, and that writes the fresh
  result back into the Cache Store before returning it upward.

Relationships. The Agent Loop calls the Tool Dispatcher exactly the way it
would call the real tool, with the same name and arguments, and receives
back a result in the same shape either way. The Tool Dispatcher consults the
Policy Layer first, before touching the Cache Store, because a tool the
policy has marked as unsafe to cache must never reach the key function at
all. Only a call the policy allows flows to the Cache Key Function, then to
a lookup against the Cache Store. A hit returns directly. A miss falls
through to the Tool Executor, which performs the real call and writes the
result back through the same key before returning it.

## 6. ASCII structure diagram

```
+-----------------+   call(name, args)   +--------------------+
|                 | --------------------> |                    |
|   Agent Loop    |                       |  Tool Dispatcher   |
|  (LLM decides   | <-------------------- |                    |
|   which tool)   |   tool_result/error   +--------------------+
+-----------------+                          |
                                              | 1. check
                                              v
                                       +--------------------+
                                       |   Policy Layer     |
                                       | readOnlyHint,      |
                                       | idempotentHint,    |
                                       | per-tool TTL/deny  |
                                       +--------------------+
                                              |
                                cacheable?    | yes
                                              v
                                       +--------------------+
                                       | Cache Key Function |
                                       | hash(name, args,   |
                                       |      tenant)       |
                                       +--------------------+
                                              |
                                              v
                                       +--------------------+       hit
                                       |    Cache Store     | ------------+
                                       | key -> (value, ts, |             |
                                       |         ttl)       |             |
                                       +--------------------+             |
                                              | miss                      |
                                              v                           |
                                       +--------------------+             |
                                       |   Tool Executor    |             |
                                       +--------------------+             |
                                              |                           |
                                              v                           |
                                       +--------------------+             |
                                       |  External System   |             |
                                       |  (API, DB, search)  |             |
                                       +--------------------+             |
                                              |                           |
                                              +---- write result back ----+
```

## 7. Dynamics

The first call for a given tool and argument pair is a miss, the second call
for the same pair, inside the TTL window, is a hit and never leaves the
process boundary of the Tool Dispatcher.

```
Agent Loop     Tool Dispatcher   Cache Store    Tool Executor  External Sys
    |                |                |               |             |
    |-- call(A) ---->|                |               |             |
    |                |-- lookup(A) -->|               |             |
    |                |<-- miss -------|               |             |
    |                |-- execute(A) ------------------>|             |
    |                |                |               |-- call ---->|
    |                |                |               |<-- answer --|
    |                |<-- result -----------------------|             |
    |                |-- write(A,result) ------------->|             |
    |<-- result -----|                |               |             |
    |                |                |               |             |
    |  (turn 5, backtracked, calls A again with identical args)      |
    |                |                |               |             |
    |-- call(A) ---->|                |               |             |
    |                |-- lookup(A) -->|               |             |
    |                |<-- hit(result)-|               |             |
    |<-- result -----|                |               |             |
    |                |                |               |             |
```

Two timing details worth stating plainly. First, the write into the Cache
Store must complete, or at minimum be initiated, before the Tool Dispatcher
returns the fresh result upward, or a rapid second call arriving before the
write lands sees a false miss and pays the external cost twice. This is the
thundering-herd failure named in dimension 11, and the fix is the in-flight
request coalescing shown in dimension 8's TypeScript variant. Second, when a
TTL expires between the lookup and the moment the entry would have been
used, the correct behavior is to treat it as a miss and refresh, never to
return an expired value, a distinction some naive implementations get wrong
by checking freshness only at write time rather than at read time.

## 8. Implementation variants

**Exact-match key cache.** The Cache Key Function hashes the tool name and a
canonical serialization of its arguments, often JSON with sorted object
keys so that argument order never causes a false miss. This is the cheapest
variant to build and reason about, and the one shown in the Python and Go
samples below. Its weakness is that it only ever matches calls that are
byte-for-byte identical after normalization, so `{"city": "Berlin"}` and
`{"city": "berlin"}` are different keys unless the dispatcher normalizes
case itself.

**Semantic similarity cache.** Instead of hashing the literal arguments, the
dispatcher embeds a natural-language representation of the call and looks
up the nearest neighbor in a vector index, returning a cached result when
the similarity score clears a threshold. GPTCache implements exactly this
shape with a pluggable "Similarity Evaluator" that can use "distance
metrics, exact matching, or BM25" against embeddings produced by "OpenAI,
ONNX, Hugging Face, Cohere, SentenceTransformers"
(https://github.com/zilliztech/GPTCache, verified 2026-08-02). This variant
raises the hit rate for natural-language tool arguments such as search
queries at the cost of an embedding call on every lookup and a threshold
that trades false positives, a wrong cached answer served for a
close-but-different query, against false negatives, a real duplicate that
the threshold rejected.

**TTL-based expiry.** Every cached entry carries a fixed lifetime after
which it is treated as absent regardless of whether anything has actually
changed. LangGraph's node `CachePolicy` exposes this directly as `ttl`,
described in its documentation as "the time to live for the cache in
seconds", noting that "If not specified, the cache will never expire"
(https://docs.langchain.com/oss/python/langgraph/graph-api, verified
2026-08-02). Simple to reason about, and the right default when the tool
has no reliable event that marks its data stale.

**Event-based or generation-tagged invalidation.** Instead of, or alongside,
a TTL, the cache is explicitly cleared or a specific key is evicted the
moment an upstream event makes it stale, a document is re-indexed, a price
changes, a write to the same resource the read tool exposes succeeds. This
variant needs a real invalidation signal to exist and be wired correctly, a
cost TTL-based expiry avoids, in exchange for a cache that is never
staler than the event delivery latency rather than staler by up to a full
TTL window.

**Per-tool policy driven by protocol annotations.** Rather than a single
global cache-everything or cache-nothing switch, the Policy Layer reads
each tool's own `readOnlyHint`, `idempotentHint`, and `destructiveHint`
where the server providing the tool declares them, and derives a default
cacheability and TTL from that declaration, falling back to an explicit
allow-list for tools the server has not annotated. This keeps the caching
decision close to the tool's own stated contract rather than to a
dispatcher-wide guess.

**In-flight request coalescing.** A second call for a key that is already
being computed, but has not yet written its result, joins the first call's
in-progress future rather than triggering a duplicate external call. This
is not memoization on its own, since nothing persists once the in-flight
future resolves, but it composes directly with a TTL-based store, as shown
in the TypeScript sample, and it is the fix for the thundering-herd
scenario in dimension 11.

**Write-through cache for expensive read-heavy tools.** For a tool backed
by a slow index, a full-text search over a large corpus, a code search over
a large repository, the dispatcher can eagerly populate common or
predictable queries into the cache ahead of an agent asking for them, a
variant sometimes called cache warming, trading a background cost for a
guaranteed hit on the first real request.

**Language-idiomatic notes.** Python and TypeScript, both used pervasively
to wrap LLM tool interfaces, most often implement this as a decorator or a
higher-order function wrapping the tool's own call, which keeps the
caching concern separate from the tool's business logic. Go, with no
decorators, implements the same separation as a wrapping function value
held in a struct field, shown in the Go sample below, or as a
middleware-style function composition when the dispatcher already uses that
shape for other cross-cutting concerns such as timeouts and retries.

## 9. Known production uses

**LangGraph node caching, `CachePolicy`.** LangGraph, LangChain's
graph-based runtime for building agents, lets a developer attach a
`CachePolicy` to any node when building the graph, and its documentation
states plainly, "LangGraph supports caching of tasks/nodes based on the
input to the node," configured with "`key_func` used to generate a cache
key based on the input to a node, which defaults to a `hash` of the input
with pickle" and an optional "`ttl`, the time to live for the cache in
seconds. If not specified, the cache will never expire." A node in this
runtime frequently wraps a tool call, so a node-level cache policy applied
to such a node is Tool Result Caching applied at the graph-execution layer
(LangChain, "Graph API",
https://docs.langchain.com/oss/python/langgraph/graph-api, verified
2026-08-02).

**GPTCache, semantic caching for LLM and tool queries.** GPTCache is an
open-source, MIT-licensed library from the Zilliz team, created on
2023-03-24 per its repository's own creation timestamp, describing itself
as a "Semantic cache for LLMs. Fully integrated with LangChain and
llama_index" (https://github.com/zilliztech/GPTCache, verified 2026-08-02).
Its documented architecture, an embedding generator, a vector-store-backed
similarity search, and a pluggable cache manager supporting "LRU, FIFO,
LFU" eviction, is designed to sit in front of repeated LLM calls and
repeated tool-style lookups alike, and its own stated goal is reducing "API
costs by up to 10x" and improving response speed by "100x" on a cache hit
by avoiding a redundant external call entirely.

**Redis LangCache, managed semantic caching for AI agents.** Redis offers
LangCache as a "fully managed semantic caching solution" that intercepts
repeated queries before they reach an expensive backend and returns a
previously computed answer when a semantically similar one already exists
in the cache (Redis, "LangCache", https://redis.io/langcache/, verified
2026-08-02). Redis's own published case study states that Mangoes.ai
"achieved 70% cache hit rate, saving 70% of LLM spend" and reported "4x
faster response times" after adopting the service, and the same page notes
that agentic workloads are a specific target because agents "use 4x more
tokens than chat applications", making the redundant-call problem this
pattern addresses proportionally larger for agents than for a simple
single-turn chatbot.

## 10. Consequences

Positive.

- Redundant, expensive external calls made twice inside one agent
  trajectory, or repeated across trajectories asking the same question,
  cost only once, which lowers both dollar spend on metered tools and the
  wall-clock latency the person waiting on the agent experiences.
- Rate-limited external systems see fewer calls, which reduces the odds of
  the agent tripping a limit and having to back off or fail mid-task.
- A cache hit removes an entire network round trip from the critical path,
  which is frequently the largest single latency contributor in an
  otherwise fast reasoning loop.
- Repeated sub-queries across a fan-out multi-agent system, where several
  workers independently arrive at the same lookup, collapse to one real
  call the first worker pays for and the rest reuse.
- The optimization is transparent to the reasoning layer above it. The
  model's decision-making is unaffected, it still decides to call a tool,
  it simply sometimes gets its answer faster.

Negative.

- A cached answer can be wrong the moment the world changes faster than the
  chosen TTL, and the failure is silent, the agent has no signal that its
  answer is stale unless the caching layer is instrumented to say so.
- A tool wrongly classified as safe to cache turns a caching optimization
  into a correctness or safety incident, most severely when the tool has
  side effects.
- The cache itself is new state that must be operated, sized, and secured,
  and a shared cache across tenants or users is a new place private data
  can leak if isolation is implemented incorrectly.
- Debugging becomes one layer harder, because a wrong answer now has two
  possible causes to rule out, a wrong tool call or a stale cached one, and
  distinguishing them needs the cache's own hit and miss telemetry to
  exist, see dimension 16.
- A cache with no eviction policy or an unbounded key space grows without
  limit in a long-running process, turning a latency optimization into a
  memory leak, see dimension 11.

## 11. Failure modes and misuse

**Stale data served as fresh.** Symptom. An agent confidently reports a
price, a status, or a fact that was true when it was cached and is false
now, with no error and no indication anything is wrong. Cause. A TTL set
longer than the tool's actual data-change rate, or a tool cached with no
TTL at all because the developer assumed the underlying data never
changes. Fix. Set the TTL to the tool's real freshness contract, not to a
convenient round number, and where the tool exposes a last-updated or
version field, key the cache on it instead of on wall-clock time alone.

**Duplicated side effect from caching a non-idempotent call.** Symptom. A
customer receives two identical emails, or a downstream ledger shows two
charges for one purchase, traced back to the agent calling the same tool
twice with the same arguments. Cause. A cache applied indiscriminately to
every tool call rather than gated on the tool's `readOnlyHint` or
`idempotentHint` annotation, or applied to a tool whose annotation was
missing and never checked by a human before caching was turned on. Fix.
Default new tools to uncached until explicitly reviewed, and never treat
the absence of a `destructiveHint` as evidence the tool is safe, per the
Model Context Protocol's own instruction that clients "MUST consider tool
annotations to be untrusted unless they come from trusted servers."

**Unstable key causing silent zero hit rate.** Symptom. Cache hit and miss
counters show every call as a miss even though the agent is visibly asking
the same question repeatedly, and the caching layer appears to do nothing
despite being enabled. Cause. The Cache Key Function serializes arguments
without a stable order, most commonly by hashing a dictionary or object
whose key ordering is not guaranteed identical across two logically
identical calls, or by including a field that varies incidentally, a
timestamp, a request identifier, a session token, that has no bearing on
the tool's actual answer. Fix. Serialize arguments with explicitly sorted
keys, and audit the argument set for any field that should be excluded
from the key before hashing, per the sample implementations in dimension
15's contract test.

**Thundering herd on a cold key.** Symptom. A burst of near-simultaneous
identical calls, from parallel agent workers or from many independent user
sessions hitting the same query at once, all arrive as misses at the same
moment and all fan out to the real tool simultaneously, spiking load on
the external system precisely when the cache was supposed to protect it.
Cause. The cache only writes a result after the real call completes, so
every concurrent caller sees a miss before the first caller's write lands.
Fix. Add in-flight request coalescing, shown in the TypeScript sample in
dimension 8, so the second and later concurrent callers for the same key
join the first call's pending result instead of issuing their own.

**Unbounded cache growth.** Symptom. A long-running agent process's memory
climbs steadily over days with no plateau, traced to a cache holding
entries for a growing set of distinct argument combinations that never
repeat often enough to be evicted by a size-bounded policy, or that were
never given a TTL at all. Cause. A cache built for correctness during
development, when call volume and key diversity were small, deployed
without an eviction policy sized for production traffic. Fix. Bound the
cache by entry count or memory footprint with an LRU or similar eviction
policy, the same class of policy GPTCache exposes as "LRU, FIFO, LFU", and
alarm on cache size independent of hit rate so growth is caught before it
becomes an incident.

**Cross-tenant data leak through a shared cache.** Symptom. One customer's
support agent surfaces a fact that belongs to a different customer's
account, and the leak is intermittent and hard to reproduce because it
depends on cache timing rather than on a consistent code path. Cause. The
Cache Key Function omits the tenant or user identifier from the key for a
tool whose answer is genuinely scoped to the caller, collapsing two
different people's distinct questions into one shared cache slot. Fix. Any
tool whose output is caller-scoped must include the caller's identity in
the key, and a security review of every cached tool should explicitly ask
whether its output is global or scoped before the tool is added to the
cacheable list, see dimension 17.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Tool Result Caching | Prompt/context caching (Anthropic-style) | No caching, always call | Request coalescing only, no persistence | Idempotency key on the write path | Precomputed materialized view |
|---|---|---|---|---|---|---|
| What it saves | The external call itself | Reprocessing already-seen prompt tokens | Nothing, is the baseline | A duplicate concurrent external call | Nothing on cost, prevents duplicate effect | The call, computed ahead of demand |
| Applies to writes/mutations | No, unsafe without an idempotency key | Yes, caches the tokens regardless of side effects already performed | Trivially safe, always current | Yes, safely, since it only dedupes in-flight identical requests | Yes, its entire purpose | No, a view is only ever a read |
| Correctness risk | Staleness within the TTL window | None on tool correctness, only saves tokens | None, always fresh | None, does not persist a result | None, prevents duplication rather than serving old data | Staleness at the refresh interval |
| Latency saved on a hit | Full external round trip | Token reprocessing time only, the call itself may still happen | None | Full round trip, only for concurrent duplicates | None | Full round trip, always, once built |
| Cost model | Storage plus key computation | Provider-side token discount, a documented 90 percent discount on cache reads | Full price every call | Storage of in-flight futures only | No cost saving, a correctness mechanism | Build and refresh cost paid upfront |
| Complexity added | Key function, store, TTL, policy | Placement of `cache_control` breakpoints | None | A pending-futures map | A key generation and dedup-check step in the write path | A refresh pipeline and staleness monitor |
| Where it is implemented | Around the tool dispatcher | Inside the model provider's request handling | Nowhere, is the null option | Around the tool dispatcher, alongside caching | Inside the tool's own write handler | Ahead of the agent, in a batch job |
| Multi-tenant isolation needed | Yes, when output is caller-scoped | Provider-isolated per API key or workspace already | Not applicable | Yes, same as full caching | Yes, keys must be scoped per caller | Yes, per-tenant views or filtering |

Reading of the table. Tool Result Caching and prompt caching solve adjacent
but non-overlapping problems and are frequently used together rather than
as alternatives, dimension 4 covers why they are not substitutes for each
other. Request coalescing is a strict subset of this pattern's behavior,
useful on its own when persistence is unwanted but concurrent duplication
still needs to be prevented. Idempotency keys solve the safety problem this
pattern deliberately avoids taking on for writes, and the two compose,
caching reads while making writes idempotent covers both halves of an
agent's tool surface. Precomputed views win when the query space is small
and known ahead of time, and lose the moment the agent's questions are open
ended, which is the common case for a tool driven by natural-language
arguments.

## 13. Related and incompatible patterns

- **Function Calling.** The pattern this one wraps. Tool Result Caching
  never exists without a function-calling or tool-use interface generating
  the calls it caches, and the annotation model, `readOnlyHint`,
  `idempotentHint`, that this pattern's policy layer depends on is defined
  as part of that interface's own tool metadata.
- **ReAct.** The reasoning-and-acting loop that most commonly produces the
  repeated, backtracking tool calls this pattern exists to catch. A ReAct
  agent that revisits an earlier subgoal after a dead end is the canonical
  scenario for a cache hit inside a single trajectory.
- **Orchestrator-Worker.** Composes cleanly above this pattern. When
  several workers dispatched by an orchestrator independently need the
  same underlying fact, a shared Cache Store lets the first worker's call
  serve every sibling worker's identical request, which is the
  multi-agent instance of the thundering-herd concern in dimension 11 and
  the reason request coalescing matters most in exactly this pattern's
  presence.
- **Plan-and-Execute.** A replanning cycle that regenerates a plan after a
  step fails frequently reissues steps that already succeeded. Caching the
  tool calls behind those already-successful steps means a replan pays
  only for the steps that are genuinely new, not for re-deriving
  everything from scratch.
- **Reflexion.** A self-critique retry loop that decides to try the same
  approach again after a failure is, for a caching layer, indistinguishable
  from any other repeated call, and the two must be told apart explicitly.
  A tool call that failed should never be cached as if it had succeeded, so
  a caching implementation must key its writes on successful results only
  and let a Reflexion-driven retry reach the real tool again after a
  genuine failure, never serve a cached failure as if retrying were
  pointless.
- **Prompt caching, as an adjacent but distinct mechanism.** The two are
  frequently deployed side by side in the same agent, one reducing token
  reprocessing cost on the model side, the other reducing redundant call
  volume on the tool side, and neither substitutes for the other, per
  dimension 4's detailed distinction.
- **Idempotency keys, as the safety mechanism for the class this pattern
  excludes.** Where a write genuinely needs repetition safety, for example
  a payment tool an agent might retry after an ambiguous timeout, the
  correct composition is an idempotency key generated once per logical
  intent and passed through to the external system, which then guarantees
  a repeated call with the same key has no additional effect, a guarantee
  the caching layer in this pattern explicitly does not attempt to provide
  for writes.
- **Service Locator and hidden global state, as an active conflict.** A
  tool implementation that silently reads mutable global or ambient state,
  the current time, a session-scoped variable, a value set by a previous
  unrelated call, and returns a different answer for the same visible
  arguments depending on that hidden state, breaks the purity assumption
  this pattern depends on, and caching such a tool produces answers that
  were correct once and wrong the moment the hidden state moved.

## 14. Refactoring path in and out

Introducing the pattern into a tool dispatcher that does not have it yet.

1. Enumerate every tool the agent can call and classify each one against
   its `readOnlyHint`, `idempotentHint`, and `destructiveHint` annotation
   where the tool declares them, or against a manual review of its
   implementation where it does not. Produce an explicit allow-list of
   tools eligible for caching. Do not start from a deny-list, since the
   safer default is uncached until reviewed.
2. For each allowed tool, write down the freshness contract in plain
   language, "this data changes at most once per hour", "this data changes
   rarely enough that a 24-hour TTL is acceptable", and convert that
   sentence into the tool's TTL setting.
3. Introduce the Cache Key Function first, in isolation, with a unit test
   asserting that two logically identical calls produce the same key
   regardless of argument object key order, and that two calls differing
   in a field that should matter produce different keys, per the contract
   test in dimension 15.
4. Wrap the Tool Dispatcher's call path with a lookup before the real call
   and a write after it, behind a feature flag that defaults off, so the
   change can ship without altering behavior until enabled.
5. Instrument hit and miss counters, per tool, before turning the flag on
   in production, per dimension 16, so the very first rollout produces
   measurable evidence rather than a silent change in behavior.
6. Enable caching for the allow-listed tools one at a time, watching the
   hit rate and, where the tool's answer is checkable, spot-checking a
   sample of cache hits against a fresh call to confirm no staleness
   surprise appeared.
7. Add in-flight request coalescing once concurrent duplicate calls are
   observed in the hit and miss telemetry, rather than pre-emptively,
   since the added complexity is only worth paying where the concurrency
   pattern actually occurs.

Removing the pattern when it stops earning its place.

1. Confirm the removal reason. A tool the caching layer keeps serving
   stale answers for, despite TTL tuning, has a freshness contract too
   tight for any workable cache window and should be pulled from the
   allow-list rather than have its TTL driven toward zero, which is the
   same as no caching with extra code in the path.
2. Remove the tool from the allow-list first, leaving the dispatcher's
   caching machinery intact for the remaining allowed tools, so the
   removal is scoped to the one tool rather than to the whole mechanism.
3. If every tool has been removed from the allow-list, delete the Policy
   Layer's check, the Cache Key Function, and the Cache Store wiring
   together, and confirm with the hit and miss counters from dimension 16
   that the hit rate had already fallen to a level that no longer
   justified the operational cost of running the store.
4. Where a shared external store such as Redis was dedicated to this
   cache, decommission it last, after confirming no other caching use of
   the same store depends on entries this removal leaves behind.

## 15. Testing and verification

Easier because of the pattern.

- The Cache Key Function is a pure function from arguments to a string,
  and is trivially unit-testable in complete isolation from the tool it
  will eventually key, with no network, no mock, and no external
  dependency.
- Because the Tool Dispatcher's cached path and uncached path share one
  return shape, a test can assert the two paths are behaviorally
  indistinguishable to the caller, which is exactly the transparency
  property dimension 5 describes.
- Hit and miss behavior is independently and deterministically testable by
  calling the dispatcher twice with identical arguments and asserting the
  underlying executor, a test double, was invoked exactly once.

Harder because of the pattern.

- A stale-data bug is, by construction, invisible to a test that only
  checks the cached value against itself, since the cached value is
  self-consistent even when it disagrees with reality. Verifying freshness
  needs a test that advances a fake clock past the TTL and asserts a fresh
  call is made, not merely that the cache eventually returns something.
- Whether a specific tool is safe to cache is a judgment call about its
  side effects and data scope, and no unit test can prove that judgment
  correct on its own, it needs the manual classification step from
  dimension 14 to have been done honestly.

Techniques that apply.

- **Key-stability contract test.** One test asserting that two calls built
  from the same logical arguments, constructed via different code paths
  or with different key insertion order, produce the same cache key, and a
  second assertion that a call differing in a field the tool actually
  cares about produces a different key. This is the single highest-value
  test for this pattern, because dimension 11's most common real failure,
  an unstable key, is entirely preventable by this one test.
- **Executor call-count spy.** A test-only executor that increments a
  counter on every invocation, wrapped by the real dispatcher, asserting
  the counter after two identical calls equals one and after two
  differently-argued calls equals two. This is the direct verification
  that caching, and not accidental request deduplication elsewhere in the
  stack, is what produced an observed hit.
- **Fake clock for TTL boundary testing.** Inject a controllable clock into
  the Cache Store rather than reading wall-clock time directly, and assert
  the boundary behavior explicitly, a call one tick before expiry is a
  hit, a call one tick after expiry is a miss and triggers a fresh
  executor call, per the classic boundary-condition discipline any
  time-based system needs.
- **Concurrent-caller test for coalescing.** Where in-flight request
  coalescing is implemented, a test that fires several concurrent calls
  for one key and asserts the executor was invoked exactly once, verifying
  the thundering-herd fix from dimension 11 actually holds under real
  concurrency rather than only in the sequential case the simpler tests
  above cover.
- **Never mock the boundary the pattern exists to protect.** A test that
  mocks the Cache Store itself, rather than the external tool call behind
  it, proves nothing about whether the caching logic actually prevents a
  real duplicate call, and the executor call-count spy above is the
  correct substitute.

## 16. Observability signals

The pattern's entire value proposition, fewer external calls, is invisible
unless it is measured directly, so telemetry here is not optional polish.

What to record.

- A hit and miss counter, labeled by tool name, incremented on every cache
  lookup regardless of outcome. This single pair of counters answers
  whether the cache is doing anything at all.
- A cache-write counter and a cache-eviction counter, labeled by tool name
  and, where relevant, by eviction reason, TTL expiry against size-based
  eviction, so the operator can distinguish a cache that is simply small
  from one whose entries are churning out before they have a chance to be
  reused.
- A histogram of external call latency, labeled by whether the call was a
  cache hit or a cache miss, which is the direct evidence of the latency
  saving the pattern claims to deliver, rather than an assumption.
- A gauge of current cache size, in entry count or memory footprint,
  compared against the configured bound, to catch the unbounded-growth
  failure from dimension 11 before it becomes an incident rather than
  after.
- For a semantic cache variant, a histogram of similarity scores on hits,
  which lets an operator see whether the threshold is producing
  comfortably-above-threshold matches or borderline ones worth tightening.

A healthy instance on a dashboard. The hit rate for each cacheable tool
sits at a level consistent with how often that tool's arguments genuinely
repeat, stable over time except when a real change in traffic pattern
explains a shift. Cache-hit latency sits close to zero and cache-miss
latency matches the tool's known real-world round trip. The size gauge sits
below its configured bound with headroom, and evictions come mostly from
TTL expiry rather than from size pressure, which would indicate the bound
is too tight for the working set.

A failing instance. A hit rate that sits at or near zero despite the agent
visibly repeating the same questions points directly at the unstable-key
failure from dimension 11. A size gauge that climbs without a matching rise
in eviction count points at the unbounded-growth failure. A latency
histogram where the "hit" label shows latency indistinguishable from the
"miss" label means the lookup path itself has a cost nearly as large as the
call it was meant to avoid, worth investigating before trusting the pattern
is delivering any real saving at all.

## 17. Security and privacy implications

This pattern's security surface is real and specific, unlike a purely
structural pattern such as Factory Method whose classical form is close to
silent on the topic.

**Cross-tenant and cross-user data exposure.** A cache is, by construction,
a place that stores an answer and hands it to whoever asks the matching
question next, and it has no inherent concept of who is allowed to see
what. A tool whose output is scoped to the calling user or tenant must
carry that scope inside the cache key, per dimension 11's cross-tenant
failure mode, or the cache becomes a mechanism for leaking one caller's
private answer to a different caller who happens to ask a similarly keyed
question.

**Caching sensitive data at rest.** A Cache Store that persists to disk or
to a shared service such as Redis is a new place personal data, financial
figures, or confidential business information now sits, possibly
outliving the request that produced it by hours if the TTL is long. Where
a tool's output includes data subject to retention or deletion
requirements, the cache's own TTL and eviction behavior becomes part of
that data's actual retention policy, whether or not anyone designed it
that way, and it needs the same access controls, encryption at rest, and
audit logging as the primary data store the tool reads from.

**Cache poisoning through a compromised or malicious server.** In an MCP
deployment specifically, the specification warns that clients "MUST
consider tool annotations to be untrusted unless they come from trusted
servers", which matters directly here because a malicious or compromised
server could mark a genuinely mutating or sensitive tool with a
`readOnlyHint` of true to trick a naive dispatcher into caching, and
therefore reusing, an answer the server controls, or into treating a
destructive call as safe to skip re-confirming. A caching Policy Layer
should treat annotation-derived cacheability as advisory for a trusted,
first-party tool and as untrusted, requiring explicit human or
configuration-driven allow-listing, for a third-party or dynamically
discovered one.

**Denial of service through cache-key manipulation.** An attacker who can
influence a tool's arguments, directly through user input passed into a
tool call, can craft a flood of distinct argument values that each produce
a unique cache key, filling the Cache Store with entries that will never
be reused and starving out entries that would have been. Bound the cache
by size with a real eviction policy, per dimension 11, and where arguments
originate from untrusted input, consider a rate limit on the number of
distinct new keys accepted from one caller in a given window, independent
of the tool's own rate limit.

On the positive side, this pattern can also reduce security surface where
it lowers the total call volume against a rate-limited or metered external
system, since fewer real calls mean fewer opportunities for a call to be
logged, intercepted, or to leak arguments in transit, though this is a side
effect of reduced volume, not a designed security property, and should not
be relied on as one.

## Code examples

Three languages, each demonstrating a distinct facet of the pattern rather
than the same logic three times. Python shows the baseline exact-match
cache with explicit TTL checking at read time, the shape most tool
dispatchers start from. Go shows the same mechanism made safe for
concurrent callers using `sync.Map` and atomic counters, the shape a
production agent runtime running many goroutines needs. TypeScript shows
in-flight request coalescing layered on top of the cache, the fix for the
thundering-herd failure from dimension 11, in the async style most
JavaScript and TypeScript agent frameworks are already written in. Java,
Rust, and Swift are omitted here because the pattern's substance is
entirely in the key-and-TTL logic shown below, and a fourth or fifth
rendering of the same map-plus-timestamp shape would repeat the pattern
rather than add a new implementation facet, contrary to this template's
own instruction to prefer languages where a pattern is genuinely idiomatic
in a different way.

### Python

```python
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CacheEntry:
    value: Any
    written_at: float
    ttl_seconds: float


class ToolResultCache:
    # Exact-match cache keyed on tool name plus a stable serialization
    # of its arguments. Only read-only, idempotent tools may be cached.
    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0

    def _key(self, tool_name: str, args: dict[str, Any]) -> str:
        canonical = json.dumps(args, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(f"{tool_name}:{canonical}".encode()).hexdigest()

    def call(
        self,
        tool_name: str,
        args: dict[str, Any],
        executor: Callable[[dict[str, Any]], Any],
        ttl_seconds: float,
        read_only: bool,
    ) -> Any:
        if not read_only:
            return executor(args)

        key = self._key(tool_name, args)
        now = time.monotonic()
        entry = self._store.get(key)
        if entry is not None and now - entry.written_at < entry.ttl_seconds:
            self.hits += 1
            return entry.value

        self.misses += 1
        result = executor(args)
        self._store[key] = CacheEntry(result, now, ttl_seconds)
        return result


def fetch_weather(args: dict[str, Any]) -> dict[str, Any]:
    return {"city": args["city"], "temp_c": 21}


if __name__ == "__main__":
    cache = ToolResultCache()
    first = cache.call(
        "get_weather", {"city": "Berlin"}, fetch_weather,
        ttl_seconds=60, read_only=True,
    )
    second = cache.call(
        "get_weather", {"city": "Berlin"}, fetch_weather,
        ttl_seconds=60, read_only=True,
    )
    assert first == second
    assert cache.hits == 1 and cache.misses == 1
    print(f"hits={cache.hits} misses={cache.misses}")
```

### Go

```go
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

type cacheEntry struct {
	value     string
	writtenAt time.Time
	ttl       time.Duration
}

// ToolResultCache memoizes read-only tool calls by a stable hash of
// the tool name plus its arguments, safe for concurrent callers.
type ToolResultCache struct {
	store  sync.Map
	Hits   atomic.Int64
	Misses atomic.Int64
}

func (c *ToolResultCache) key(tool string, args map[string]string) string {
	canonical, _ := json.Marshal(args)
	sum := sha256.Sum256([]byte(tool + "|" + string(canonical)))
	return hex.EncodeToString(sum[:])
}

func (c *ToolResultCache) Call(
	tool string,
	args map[string]string,
	ttl time.Duration,
	readOnly bool,
	executor func(map[string]string) string,
) string {
	if !readOnly {
		return executor(args)
	}

	key := c.key(tool, args)
	if raw, found := c.store.Load(key); found {
		entry := raw.(cacheEntry)
		if time.Since(entry.writtenAt) < entry.ttl {
			c.Hits.Add(1)
			return entry.value
		}
	}

	result := executor(args)
	c.Misses.Add(1)
	c.store.Store(key, cacheEntry{value: result, writtenAt: time.Now(), ttl: ttl})
	return result
}

func main() {
	cache := &ToolResultCache{}
	fetch := func(args map[string]string) string {
		return "tempC=21 city=" + args["city"]
	}

	first := cache.Call("get_weather", map[string]string{"city": "Berlin"}, time.Minute, true, fetch)
	second := cache.Call("get_weather", map[string]string{"city": "Berlin"}, time.Minute, true, fetch)

	if first != second {
		panic("cache returned inconsistent values")
	}
	fmt.Printf("hits=%d misses=%d\n", cache.Hits.Load(), cache.Misses.Load())
}
```

### TypeScript

```typescript
type ToolExecutor<A, R> = (args: A) => Promise<R>;

interface CacheEntry<R> {
  value: R;
  writtenAt: number;
  ttlMs: number;
}

// Caches read-only tool calls and coalesces concurrent duplicate
// requests so two callers awaiting the same key share one execution.
class ToolResultCache {
  private store = new Map<string, CacheEntry<unknown>>();
  private inFlight = new Map<string, Promise<unknown>>();
  hits = 0;
  misses = 0;

  private key(toolName: string, args: unknown): string {
    return `${toolName}|${JSON.stringify(args)}`;
  }

  async call<A, R>(
    toolName: string,
    args: A,
    ttlMs: number,
    executor: ToolExecutor<A, R>,
  ): Promise<R> {
    const key = this.key(toolName, args);
    const cached = this.store.get(key) as CacheEntry<R> | undefined;
    if (cached && Date.now() - cached.writtenAt < cached.ttlMs) {
      this.hits++;
      return cached.value;
    }

    const running = this.inFlight.get(key) as Promise<R> | undefined;
    if (running) {
      this.hits++;
      return running;
    }

    this.misses++;
    const promise = executor(args).then((value) => {
      this.store.set(key, { value, writtenAt: Date.now(), ttlMs });
      this.inFlight.delete(key);
      return value;
    });
    this.inFlight.set(key, promise);
    return promise;
  }
}

async function fetchWeather(args: { city: string }): Promise<{ tempC: number }> {
  return { tempC: 21 };
}

async function main(): Promise<void> {
  const cache = new ToolResultCache();
  const [a, b] = await Promise.all([
    cache.call("get_weather", { city: "Berlin" }, 60_000, fetchWeather),
    cache.call("get_weather", { city: "Berlin" }, 60_000, fetchWeather),
  ]);
  if (a.tempC !== b.tempC) {
    throw new Error("inconsistent cached values");
  }
  console.log(`hits=${cache.hits} misses=${cache.misses}`);
}

main();
```

## 18. References

- Donald Michie, "'Memo' Functions and Machine Learning", Nature, volume
  218, issue 5136, pages 19 to 22, 1968, as summarized in the "History"
  section of the Wikipedia article on memoization,
  https://en.wikipedia.org/wiki/Memoization, verified 2026-08-02.
- Model Context Protocol, "Tools", server specification, revision
  2025-06-18, https://modelcontextprotocol.io/specification/2025-06-18/server/tools,
  verified 2026-08-02.
- Model Context Protocol, `ToolAnnotations` interface, `schema.ts`,
  revision 2025-06-18,
  https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/schema/2025-06-18/schema.ts,
  verified 2026-08-02.
- Anthropic, "Prompt caching",
  https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching,
  verified 2026-08-02.
- LangChain, `BaseCache`, `langchain_core.caches`,
  https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/caches.py,
  verified 2026-08-02.
- LangChain, "Graph API", LangGraph documentation, node `CachePolicy`
  section, https://docs.langchain.com/oss/python/langgraph/graph-api,
  verified 2026-08-02.
- Zilliz, `GPTCache` repository, README and repository metadata,
  https://github.com/zilliztech/GPTCache, verified 2026-08-02.
- Redis, "LangCache", https://redis.io/langcache/, verified 2026-08-02.
- Vercel, "Tools and Tool Calling", AI SDK Core documentation,
  https://ai-sdk.dev/docs/ai-sdk-core/tools-and-tool-calling, verified
  2026-08-02.
- Anthropic, "Building Effective Agents",
  https://www.anthropic.com/engineering/building-effective-agents, verified
  2026-08-02, consulted directly and confirmed to contain no guidance on
  tool result caching, cited here to support the honest claim in dimension
  1 that no single canonical publication names this pattern for agents.
