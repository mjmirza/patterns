---
name: Token Budget
slug: token-budget
family: 17-ai-agentic
category: AI/Agentic
aliases: [Context Budget, Context Window Budget, Token Allocation, Prompt Budget]
first_described: "no single publication, an engineering practice that matured alongside per-token LLM billing and finite context windows, 2020 to 2024"
maturity: established
related: [agent-memory, react, reflexion, chunking-strategies, hybrid-search, graphrag, model-context-protocol]
incompatible_with: []
verified: 2026-08-03
---

# Token Budget

## 1. Name, aliases, and lineage

Token Budget is the name this catalog uses for the practice of treating the
tokens a language model call can hold, and the tokens an account is allowed to
spend over time, as a finite resource that is allocated on purpose rather than
filled until the provider rejects the request. A budget has three parts that
get confused with each other constantly and need separating on sight. The
per-request context budget is the number of tokens a single call can carry
before the model's maximum input size is reached. The per-minute throughput
budget is the number of tokens an account or workspace may send and receive
across all requests inside a rolling window, enforced by the provider as a
rate limit rather than a context limit. The per-period spend budget is a
dollar limit, independent of both, because a request can be well inside its
context window and its rate limit and still be expensive. Pattern catalogs
that only discuss the first of these describe half the problem.

The pattern has no single inventor and no founding paper in the way a Gang of
Four pattern does, because it is not an algorithm someone named once. It grew
out of two hard constraints arriving together. Transformer self-attention has
quadratic cost in sequence length, which is why context windows started small
and grew slowly rather than being unbounded from day one (Ashish Vaswani,
Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez,
Lukasz Kaiser, Illia Polosukhin, "Attention Is All You Need," arXiv paper
number 1706.03762, June 2017, section 3.2.1, verified 2026-08-03,
[arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762)). And commercial
LLM APIs began billing per token rather than per request, which turned every
extra token in a prompt into a line item rather than a rounding error. Once
agent loops started calling a model many times in a single task, a tool
result from step three could push step seven over the model's maximum input
size, and the same conversation could burn an account's entire hour of
rate-limit headroom on one debugging session. Engineers building agent
frameworks converged on the same shape of fix from different directions
within roughly the same two years, which is why the practice reads as
established rather than invented.

**Context Budget** and **Context Window Budget** are the names used when the
discussion is scoped to a single request's input size. **Token Allocation**
is used when the emphasis is on splitting a fixed capacity across competing
sections, the way an operating system allocates memory pages. **Prompt
Budget** appears in agent framework documentation where the whole assembled
prompt, not only the conversation history, is the thing being sized. This
catalog uses Token Budget because the pattern spans all three axes, request,
throughput, and spend, and no narrower alias covers all three without
qualification.

## 2. Problem and context

An agent loop calls a model repeatedly, and every call carries a system
prompt, a set of tool definitions, some retrieved documents, and the
conversation so far. None of those four pieces has a natural limit on its
own. A tool can return a ten thousand line log file. A retrieval step can
surface forty candidate chunks. A conversation can run for hours. Left alone,
each of these grows without bound, and the model's maximum input size is a
wall the code hits without warning rather than a boundary the code plans
around.

The failure that motivates this pattern is not the outright rejection,
though that happens too. It is the slow version. A team ships an agent that
works well in every demo, because demos are short. In production the same
agent runs for an afternoon, its conversation history accretes every tool
call and every tool result, and by the third hour most of the input tokens
on every single call are old context that no longer bears on the current
question, while the part that actually matters, the system framing and the
last two turns, gets squeezed into whatever headroom is left. The team also
discovers, usually from a billing alert rather than from a design review,
that a request comfortably inside the model's context window can still be
rejected with a rate-limit error, because the account's tokens-per-minute
limit is a separate number enforced by a separate mechanism at the provider
edge, not by anything the application code decided.

The context in which this pattern earns its place has three properties. The
system makes more than one model call per task, so token usage compounds
rather than staying flat. The inputs to a call vary in size at runtime,
driven by tool output, retrieved documents, or conversation length, so no
fixed prompt template can be hand-sized once and left alone. And the system
runs long enough, or at enough concurrency, that provider-side throughput or
cost limits become a real constraint rather than a theoretical one. Outside
that context, see the non-applicability list in dimension 4, an explicit
allocator is overhead a fixed-size prompt does not need.

## 3. Forces

The pattern balances the following competing pressures.

- **Cost predictability.** Favoured. An enforced limit on each call, and a
  governor on tokens per minute, turns an open-ended bill into a bounded one.
  The trade is that a task which genuinely needs more context than the budget
  allows now fails or degrades instead of simply costing more.
- **Answer quality.** Sacrificed at the margin. Every token evicted to stay
  inside a limit is a token the model cannot see. A well-designed eviction
  order sacrifices the least useful tokens first, but the sacrifice is real,
  and a poorly ordered eviction policy can remove exactly the fact the answer
  depends on.
- **Latency.** Favoured, usually. A smaller assembled prompt is cheaper to
  process on the provider side and returns sooner. This is sacrificed locally
  by any compaction step that itself calls the model to summarize, because
  that call adds a round trip before the real request goes out.
- **Determinism and testability.** Favoured when the eviction policy is a
  pure function of its inputs, ordered by an explicit priority, sacrificed
  when the policy depends on wall-clock timing, a non-deterministic model
  call for summarization, or insertion order that happens to differ between
  runs.
- **Operability.** Favoured. A named, measured budget per section gives an
  operator a concrete number to look at when a task behaves oddly, rather
  than a single opaque prompt string.
- **Implementation complexity.** Sacrificed. An allocator, a counter, an
  eviction policy, and a throughput governor are four pieces of code that a
  single unbudgeted prompt string did not need.
- **Coupling to the tokenizer.** Sacrificed. Correct budgeting at the edge of
  a hard limit requires knowing how the target model counts tokens, which
  ties the code to a specific tokenizer, and that tokenizer can change when
  the model is upgraded underneath the application.
- **Fairness across tenants or callers.** Favoured, when the throughput axis
  is implemented as a per-tenant sub-budget rather than one shared pool. A
  system that only budgets the per-request context axis and skips this one
  lets a single heavy caller starve every other caller sharing the account.
- **Team topology.** Favoured. A budget allocator with named sections gives
  separate teams, the one that owns retrieval, the one that owns tool
  integrations, the one that owns conversation memory, a shared contract to
  negotiate against instead of an unowned string.

A pattern that sacrificed nothing would be a bigger context window, not a
pattern. The price paid here is code that must exist purely to say no to
content the system would otherwise send.

## 4. Applicability and non-applicability

Reach for an explicit Token Budget when the following hold.

- The system makes more than one model call per user-visible task, so a
  request's input size is a function of prior steps rather than a fixed
  template.
- Any input to a call is unbounded at design time, a tool result, a
  retrieved document set, or a conversation history that can grow across
  many turns.
- The system runs at a concurrency or duration where a provider's
  tokens-per-minute or requests-per-minute limit is a real operating
  constraint, not a number that will never be approached.
- Cost needs to be predictable per task or per tenant, for example a SaaS
  product pricing a feature by usage, or an internal tool with a monthly
  spend cap.
- The system serves more than one caller against a shared account or
  workspace, so one caller's usage can affect another's if nothing separates
  their share of the throughput budget.
- The target model's context window is comparable in size to, or smaller
  than, the largest input the system can realistically produce, so overflow
  is a real event rather than a mathematical impossibility.

Do NOT reach for an explicit allocator, counter, and eviction policy when any
of the following hold, because the machinery costs more than the problem it
solves.

- The system makes a single, one-shot call per task, with a fixed prompt
  template and an input whose maximum size is known and small relative to
  the model's context window, for example a structured extraction call over
  one short form field. A single guard clause asserting the input is under a
  constant is enough; a full allocator is unwarranted engineering for a
  problem that cannot occur.
- The system is an offline batch job with no interactive latency requirement
  and a generous time-to-completion SLA, and each item processed is
  independently small. Rate-limit-aware retry with backoff still applies,
  but a per-request context allocator with named sections and an eviction
  order is disproportionate to the risk.
- The deployment is self-hosted against a model with no per-token billing
  and a context window that is provably larger than the largest input the
  application can generate, and there is no multi-tenant fairness concern,
  because two of the three budget axes, spend and throughput fairness,
  simply do not apply, and the third, context overflow, cannot occur.
- The task is genuinely a single unstructured conversation with one user and
  no tool calls, no retrieval, and a session length short enough that the
  full transcript will never approach the model's context window inside a
  realistic session. Adding an eviction policy here is speculative
  generality against a limit the session will not reach.
- The model in use has such a large context window relative to typical
  inputs that overflow is not the binding concern, and the only real
  constraint is cost. In that narrower case a spend cap and a throughput
  governor are still worth having, but a full multi-section context
  allocator with priority-ordered eviction is more mechanism than the
  problem needs; a periodic cost check is enough.

## 5. Structure

The participants, named by the role each plays rather than by a generic
class name.

- **Budget Ledger.** Holds the model's total context window, subtracts a
  fixed reservation for the tokens the model is allowed to generate as
  output, and subtracts any fixed protocol overhead, leaving a disposable
  budget available for the request's actual content.
- **Producers.** Named sections that each want a share of the disposable
  budget. The canonical four are the system prompt, tool definitions,
  retrieved or memory-sourced context, and conversation history, but a given
  system can define its own set. Each producer carries a priority.
- **Token Counter.** Converts a candidate section's raw content into a token
  count, either exactly, by calling the same tokenizer the target model
  uses, or approximately, by a cheap heuristic, with the trade-off named in
  dimension 8.
- **Allocation Policy.** Decides how the disposable budget is divided among
  producers, either by a fixed proportion per section or by filling
  producers in priority order until the budget is exhausted.
- **Eviction and Compaction Policy.** The behaviour invoked when a producer's
  candidate content exceeds its share. Ranges from dropping the lowest
  priority content outright, through truncating from one end of a sequence,
  to replacing older content with a model-generated summary.
- **Prompt Assembler.** Combines the (possibly evicted) producer outputs into
  the final request body in a fixed, deterministic order, and asserts the
  combined token count is inside the disposable budget before the request is
  sent.
- **Throughput Governor.** A separate component, not part of the assembler,
  that tracks tokens and requests consumed across a rolling time window per
  account or per tenant, and either queues, rejects, or backs off a request
  that would exceed the provider's rate limit, independent of whether that
  same request is comfortably inside its own context budget.
- **Telemetry Sink.** Records allocated versus used tokens per section, per
  eviction event, and per throughput check, so the health of the whole
  system is visible without reading raw prompt text, see dimension 16.

## 6. ASCII structure diagram

```
+---------------------------------------------------------------------+
|                        Budget Ledger                                |
|  context window  -  reserved output  -  overhead = disposable       |
+---------------------------------------------------------------------+
        |               |               |               |
        v               v               v               v
  +----------+    +----------+    +----------+    +----------+
  | System   |    | Tool     |    | Retrieved|    | Convers. |
  | Prompt   |    | Schemas  |    | Context  |    | History  |
  | producer |    | producer |    | producer |    | producer |
  +----------+    +----------+    +----------+    +----------+
        |               |               |               |
        +-------+-------+-------+-------+-------+-------+
                |                               |
                v                               v
        +---------------+              +--------------------+
        | Token Counter |              | Eviction/Compaction |
        | exact/approx  |              | Policy              |
        +---------------+              +--------------------+
                |                               ^
                v                               |
        +-------------------------------------------+
        |             Allocation Policy              |
        |  fixed proportion  or  priority-ordered fill|
        +-------------------------------------------+
                                |
                                v
                     +--------------------+
                     | Prompt Assembler   |  <- asserts hard limit
                     +--------------------+
                                |
                                v
        +---------------------------------------------+
        |            Throughput Governor               |
        |  tokens/minute, requests/minute, per tenant   |
        +---------------------------------------------+
                                |
                                v
                     +--------------------+
                     |     Model API      |
                     +--------------------+
                                |
                                v
                     +--------------------+
                     |  Telemetry Sink    |
                     +--------------------+
```

## 7. Dynamics

The context-budget axis and the throughput-budget axis run at different
points in the flow, and conflating them is the most common structural
mistake, see dimension 11. The context axis runs once per request, inside
the assembler. The throughput axis runs across many requests, outside the
assembler entirely, wrapping the transport call.

```
Caller       Producers      Allocator      Counter    Governor    Model API
  |              |              |             |           |           |
  |--gather----->|              |             |           |           |
  |              |--candidates->|             |           |           |
  |              |              |--count each->|          |           |
  |              |              |<--counts-----|          |           |
  |              |              |             |           |           |
  |              |    over budget for a producer?          |           |
  |              |<---invoke eviction/compaction----        |           |
  |              |--reduced content------------>|          |           |
  |              |              |--recount----->|          |           |
  |              |              |<--fits--------|          |           |
  |              |              |             |           |           |
  |<--assembled prompt (asserted <= disposable budget)------|           |
  |              |              |             |           |           |
  |--send-------------------------------------------------->|          |
  |              |              |             |  check throughput ---->|
  |              |              |             |  budget for this call  |
  |              |              |             |  under limit? proceed  |
  |              |              |             |  over limit? queue or  |
  |              |              |             |  429/backoff           |
  |              |              |             |           |--request-->|
  |              |              |             |           |<--response-|
  |<-------------------------------------------------------|-usage-----|
  |              |              |             |           |           |
  |--record actual usage, calibrate counter drift, update  |           |
  |  throughput governor's remaining window------------------------->  |
```

Two timing notes matter in practice. First, the disposable budget must be
computed before any producer runs, because the reserved-output figure and
any fixed overhead are constants that do not depend on what the producers
return, and computing them late leads to code that discovers the limit
only after content has already been gathered, wasting the work spent
gathering it. Second, the throughput governor's decision to proceed, queue,
or reject happens after the prompt is assembled but before the network call,
and its outcome is independent of whether the assembled prompt is small.
Ten well-budgeted small requests in the same minute can still exceed a
tokens-per-minute limit that no single request came near.

## 8. Implementation variants

**Fixed percentage allocation.** The disposable budget is split by a
constant ratio decided at design time, for example ten percent system
prompt, twenty percent tool schemas, thirty percent retrieved context, forty
percent history. Simple to reason about and to test, because the split never
changes at runtime. Costs adaptivity, a task shape the ratios were not tuned
for, a single huge document instead of a long chat, gets starved even though
the total budget was never exhausted, see failure mode 8 in dimension 11.

**Priority-ordered greedy fill.** Producers are ranked by priority once, and
the allocator fills the highest-priority producer's full request first, then
the next, until the disposable budget runs out, at which point the remaining
producers get nothing or get evicted content. Adapts to whatever shape a
given task happens to have, at the cost of a lower-priority producer
sometimes receiving zero tokens on a task that needed it, which is a
starvation risk that must be designed against explicitly rather than
discovered in production.

**Sliding window truncation.** Applied to conversation history specifically.
Keep the most recent N messages or the most recent N tokens, and drop
everything older. LangChain's `trim_messages` implements this directly,
exposing a `strategy` of `"first"` or `"last"`, a pluggable `token_counter`,
and `start_on` and `end_on` message-type boundaries so a caller can, for
example, always keep the system message and only ever trim from the tail of
human and AI message pairs (verified against source 2026-08-03,
[raw.githubusercontent.com](https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/messages/utils.py)).

**Summarization or compaction.** Once history crosses a threshold, older
turns are replaced by a model-generated summary rather than dropped outright,
trading a token cost and a latency cost now for headroom later. Claude Code's
auto-compaction is a production instance of this, triggered when the
conversation approaches the active model's maximum input size, with an
optional custom instruction telling the compactor what to preserve (verified
2026-08-03, [code.claude.com/docs/en/costs](https://code.claude.com/docs/en/costs)).
This variant composes closely with Agent Memory's tiered storage, see
dimension 13, because the summary is frequently a promotion of detail from an
in-context tier to an out-of-context store rather than a pure deletion.

**Relevance-ranked selection.** Applied to retrieved context specifically.
Rather than a first-in-first-out or fixed-size cut, candidate chunks are
ranked by a relevance score, usually embedding similarity or a reranker
score, and the allocator fills the retrieved-context producer's share by
taking the highest-ranked chunks until the budget for that section is spent,
dropping the lowest-ranked candidates first regardless of retrieval order.

**Reservation-based headroom.** The allocator reserves not only the tokens
for the model's expected output, but an additional fixed safety margin below
the model's maximum input size, because an approximate token counter is
rarely exact at the boundary. Budgeting to the literal limit with an
approximate counter is the direct cause of failure mode 1 in dimension 11.

**Delegation to an isolated context.** A token-heavy sub-task, running a
full test suite and reading its output, fetching a long document, is handed
to a subagent that runs in its own, separate context window, and only a
compact summary of the outcome returns to the caller's budget. Claude Code
documents this explicitly as a way to keep verbose tool output out of the
main conversation's budget (verified 2026-08-03,
[code.claude.com/docs/en/costs](https://code.claude.com/docs/en/costs)).

**Lazy or deferred loading.** Tool and resource definitions that are not
currently in use are represented in the budget by name only, with their full
schema loaded, and charged against the budget, only at the moment the model
actually invokes them. Claude Code's MCP tool search defers full tool
definitions this way by default, so a session configured with many tool
servers pays only for the names until one is called (verified 2026-08-03,
[code.claude.com/docs/en/costs](https://code.claude.com/docs/en/costs)).

**Caching-aware budgeting.** The budget is split into a stable, cacheable
prefix and a dynamic suffix, and the two are tracked separately because they
have different prices and, on some providers, different rate-limit treatment.
Anthropic's prompt caching bills a cache write at a premium over the base
input rate and a cache read at a tenth of it, and for most Claude models
cache-read tokens do not count against the tokens-per-minute rate limit at
all, which means the effective throughput budget of an account grows with
its cache hit rate rather than staying fixed (verified 2026-08-03,
[platform.claude.com/docs/en/build-with-claude/prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
and [platform.claude.com/docs/en/api/rate-limits](https://platform.claude.com/docs/en/api/rate-limits)).
Google's Gemini API implements a parallel mechanism, implicit caching enabled
by default on Gemini 2.5 and newer models, with a per-model minimum token
count, 2,048 tokens on Gemini 2.5 models and 4,096 tokens on newer ones,
before a request becomes cache-eligible at all (verified 2026-08-03,
[ai.google.dev/gemini-api/docs/caching](https://ai.google.dev/gemini-api/docs/caching)).

**Approximate versus exact counting.** A cheap heuristic, such as a length
based estimate tuned per language and content type, is fast enough to run on
every candidate section during assembly but drifts from the true count near
the model's actual tokenizer boundaries. The exact count, from the same
tokenizer the model uses, such as OpenAI's tiktoken library for
OpenAI-compatible models, is authoritative but costs a real computation per
call (verified 2026-08-03, [github.com/openai/tiktoken](https://github.com/openai/tiktoken)).
Production systems commonly use the approximate counter for the bulk of the
allocation decision and fall back to the exact counter only for the section
sitting closest to the limit, see the refactoring path in dimension 14.

## 9. Known production uses

- **Anthropic's Claude API prompt caching and rate limits.** The API prices
  cache-write tokens at 1.25 times the base input rate for a five-minute
  cache and 2 times for a one-hour cache, prices cache-read tokens at a tenth
  of the base rate, and for most models exempts cache-read tokens from the
  input-tokens-per-minute rate limit entirely, which is a direct,
  provider-level implementation of caching-aware budgeting (verified
  2026-08-03, [platform.claude.com/docs/en/build-with-claude/prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)).
  The rate-limit page separately documents a token-bucket throughput budget,
  measured in requests per minute, input tokens per minute, and output
  tokens per minute per model class, plus workspace-level sub-budgets an
  organization can set below its own account limit to protect one
  workspace from another's usage (verified 2026-08-03,
  [platform.claude.com/docs/en/api/rate-limits](https://platform.claude.com/docs/en/api/rate-limits)).
- **Claude Code.** Anthropic's own coding agent documents its token budget
  practice in full. It recommends keeping the project's CLAUDE.md file, which
  is loaded into every session's context at start, under two hundred lines
  so it does not consume budget that unrelated tasks never need; it defers
  MCP tool definitions to names only until a tool is actually invoked; it
  runs auto-compaction that summarizes older conversation history once the
  session approaches the active model's maximum input size, with a
  user-configurable instruction for what the compactor should keep; and it
  recommends delegating verbose operations, running tests, fetching
  documentation, reading log files, to subagents so the bulk output stays in
  the subagent's own context window and only a summary returns to the main
  session (verified 2026-08-03, [code.claude.com/docs/en/costs](https://code.claude.com/docs/en/costs)).
- **LangChain's `trim_messages`.** A message-history trimming utility built
  directly around the fixed-percentage-versus-priority-fill distinction in
  dimension 8, taking a `max_tokens` limit, a `strategy` of `"first"` or
  `"last"`, a pluggable `token_counter` that can be an exact model-backed
  counter or an approximate one, and `include_system` and `start_on` and
  `end_on` parameters that let a caller pin the system message outside the
  evictable window, which is the direct fix for failure mode 2 in dimension
  11 (verified against source 2026-08-03,
  [raw.githubusercontent.com/langchain-ai/langchain](https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/messages/utils.py)).
- **OpenAI's tiktoken.** The open source byte-pair-encoding tokenizer OpenAI
  publishes so applications can count tokens against the same vocabulary the
  model itself uses, before sending a request, which is the exact-counting
  half of the approximate-versus-exact trade-off in dimension 8, and the
  primitive most Python agent frameworks build their own token counters on
  top of (verified 2026-08-03, [github.com/openai/tiktoken](https://github.com/openai/tiktoken)).
- **Google Gemini's implicit context caching.** Enabled by default for
  Gemini 2.5 and newer models, with per-model minimum token thresholds
  before a request qualifies, and automatic cost pass-through reported to
  the caller through a `usage.total_cached_tokens` field on the response,
  which mirrors the caching-aware budgeting variant across a second provider
  rather than being unique to Anthropic's API (verified 2026-08-03,
  [ai.google.dev/gemini-api/docs/caching](https://ai.google.dev/gemini-api/docs/caching)).

## 10. Consequences

Positive.

- Cost and latency become bounded per call, converting an open-ended risk
  into a number a team can plan around and alert on.
- Overflow becomes a handled condition, an eviction event with a log line,
  rather than an unhandled provider rejection that surfaces as a raw error
  to a user.
- Graceful degradation becomes possible. A task that cannot fit its ideal
  amount of context can still run with a reduced amount, rather than failing
  outright.
- A stable, prioritized assembly order makes prompt caching effective,
  because the cache boundary depends on a byte-identical prefix across
  requests, and an allocator that always places the same content in the same
  order is what makes that prefix stable.
- Multi-tenant capacity sharing becomes fair when the throughput axis is
  implemented per tenant, protecting every caller from any one caller's
  usage spike.
- The act of assigning priorities forces an explicit decision about what
  matters when everything cannot fit, a decision that an unbudgeted system
  defers until the moment it actually runs out of room, which is the worst
  possible time to make it.
- The composed prompt's size becomes a testable property, asserted in a unit
  test rather than discovered by a customer.

Negative.

- Four new components exist that a single unbudgeted prompt string did not
  need, an allocator, a counter, an eviction policy, and a throughput
  governor, each with its own bugs to have.
- An approximate counter is, by definition, sometimes wrong, and being wrong
  near a hard limit produces the exact overflow error the pattern exists
  to prevent, see failure mode 1.
- Eviction and summarization remove information from what the model sees,
  and a wrongly ordered priority, or a summarization step that introduces an
  error, can silently damage answer quality in a way that is much harder to
  notice than an outright failure.
- A compaction step that itself calls the model adds real cost and latency
  before the request the user is actually waiting on goes out.
- A fixed allocation ratio tuned for one task shape starves a different task
  shape that arrives later, and the fix requires either per-route
  configuration or a more adaptive allocation policy, both of which add
  complexity back in.
- Running two budgets at once, the per-request context budget and the
  per-minute throughput budget, and reconciling their independent failure
  modes, is more operational surface than running either alone.

## 11. Failure modes and misuse

**Symptom.** A request is rejected with a context-length error even though
the application's own accounting believed it stayed under the limit.
**Cause.** The token counter is an approximation that undercounts against
the model's real tokenizer for certain content; non-English text, code, or
JSON with many short punctuation-heavy tokens commonly diverge the most from
a character-count heuristic. **Fix.** Use the provider's exact tokenizer for
any section sitting close to the limit, and reserve a fixed safety margin
below the hard limit rather than budgeting to the literal number, per the
reservation-based headroom variant in dimension 8.

**Symptom.** In a long-running agent session, the agent appears to forget an
instruction that was given early in the conversation, even though nothing
in the code explicitly removed it. **Cause.** Sliding-window truncation is
trimming from the oldest messages, and the original task framing was one of
those oldest messages, because the system message and the initial task were
never pinned outside the evictable window. **Fix.** Configure the eviction
policy's boundary parameters, LangChain's `include_system` and `start_on`
are the direct example, so foundational messages that carry the task itself are excluded from
the window that gets trimmed, and only conversational turns are eligible for
eviction.

**Symptom.** Cost on a session that "did not do much" spikes unexpectedly
compared to a similar session run earlier the same day. **Cause.** A large
static context sits below the cache time-to-live, and the pacing of
requests exceeded that window, so every request re-writes the cache at the
higher write price instead of reading it at the discounted rate; this is a
timing problem in the request pattern, not a bug in the budget arithmetic.
**Fix.** Batch or pace requests to stay inside the cache TTL, or move to a
longer TTL tier if the traffic pattern's gaps are wider than the default
window and the amortized cost still comes out ahead.

**Symptom.** Two sections repeatedly evict each other across successive
runs of what should be the same task, and the agent's behaviour is not
reproducible run to run. **Cause.** The eviction policy has no strict total
order among producers; two sections are both marked high priority, and which
one gets trimmed depends on insertion order or iteration order rather than
an explicit rule. **Fix.** Assign a strict, documented priority order across
every producer, make the allocator a pure function of its inputs, and cover
it with a golden test that asserts the same inputs always produce the same
assembled output, per dimension 15.

**Symptom.** The system works in staging and fails under production load
with rate-limit errors, even though every individual request is comfortably
inside its own context-window budget. **Cause.** The context-budget axis was
implemented and the throughput-budget axis was not; many small,
well-budgeted requests running concurrently exceed the account's
tokens-per-minute limit, which is enforced independently of any single
request's size. **Fix.** Add a throughput governor as a distinct component
wrapping the transport client, tracking the same units the provider enforces,
uncached input tokens and output tokens separately where the provider
distinguishes them, and route rate-limit responses through a backoff that
honours the provider's retry-after value.

**Symptom.** A summarization step introduced to free budget produces a
fact that later turns treat as ground truth, and the fact is subtly wrong.
**Cause.** The summarizer is itself a model call and carries the same
hallucination risk as any other generation, and the summary silently
replaces the verifiable source text rather than sitting alongside it, so an
error compounds instead of being checkable against the original.
**Fix.** Keep the un-summarized source in an out-of-band store, a retrieval
index or an external memory tier as in Agent Memory, so the in-context
summary is a cache of the source rather than the only remaining copy, and
periodically re-verify high-stakes summarized claims against it.

**Symptom.** In a multi-tenant deployment, one tenant's very large documents
degrade response time and increase rate-limit errors for every other tenant
sharing the same account. **Cause.** The throughput governor tracks one pool
at the account level with no per-tenant sub-budget, so a single heavy caller
consumes the shared headroom that every other caller was relying on.
**Fix.** Set per-workspace or per-tenant rate limits below the account
limit, the pattern Anthropic's own API exposes as workspace-level limits,
so one caller's usage cannot exhaust another's share.

**Symptom.** A feature launched after the initial system ships gets starved
of budget on nearly every call, even though the account's total usage is
nowhere near its cost or throughput limits. **Cause.** The allocation policy
is a fixed percentage split tuned for the original task shape, usually a
chat history, and the new feature's task shape, a single very large input,
does not fit any of the existing sections' fixed proportions.
**Fix.** Make the allocation policy pluggable per route or per task type
rather than a single global constant, or move from fixed percentages to
priority-ordered greedy fill so the split adapts to whatever shape a given
task actually has.

## 12. Trade-off matrix

Compared against named alternatives, not against an unbudgeted baseline.

| Concern | Token Budget (this pattern) | No budgeting, let the API reject | Character-count truncation only | Agent Memory (MemGPT-style paging) | Model routing to a larger context window |
|---|---|---|---|---|---|
| Cost predictability | High, limits enforced per call and per minute | None, cost is whatever the accreting prompt happens to cost | Partial, bounds size but not token cost precisely | High for what stays resident, but paging itself has a cost | Low, a bigger window costs more per token on most pricing tiers |
| Handles overflow gracefully | Yes, by design | No, surfaces as a hard error | Sometimes, but can cut mid-token or mid-sentence | Yes, via deliberate promotion and eviction between tiers | Delays the problem rather than solving it |
| Implementation complexity | Moderate, four components | Lowest, none of this exists | Low, one truncation function | High, needs a full memory-tier design | Low code complexity, but couples to model choice |
| Adapts to varying task shape | Yes, with priority-fill or per-route policy | N/A | No, one fixed cut length for everything | Yes, that adaptivity is the point of the tiering | Only as far as the largest available window allows |
| Fairness across tenants | Yes, if throughput axis is per-tenant | No | No | Not addressed by the pattern itself | No |
| Determinism, testability | High, if eviction order is explicit | High, trivially, but only because nothing is decided | High | Lower, tier promotion decisions are often model-driven | High |
| Solves the throughput-budget axis | Yes, as a distinct governor | No | No | No, orthogonal concern | No, larger windows do not change per-minute rate limits |

Character-count truncation is the naive predecessor most systems reach for
first, cutting a string to N characters without regard to where a token
boundary actually falls. It is included here rather than treated as a
strawman because it is the real, commonly shipped alternative this pattern
replaces, not a hypothetical worst case invented to make the comparison
favourable. Agent Memory and model routing are genuine architectural
alternatives for specific slices of the same problem, tiered persistence for
memory and simply avoiding the limit for context size, and the matrix makes
clear that neither one addresses the throughput-budget axis, which is why
production systems, Claude Code among them, run Token Budget alongside
these rather than instead of them.

## 13. Related and incompatible patterns

**Agent Memory.** The closest relationship in the catalog. Agent Memory
answers what content should exist outside the model's context at all, and in
what tier, in-context, a fast external store, an archival store. Token
Budget answers, given a fixed amount of room inside the context right now,
which of the candidates that could be in-context actually get to be. A
compaction step that promotes older conversation detail into an external
memory store while replacing it in-context with a short summary is Agent
Memory's paging mechanism implemented using Token Budget's eviction
machinery; the two patterns compose rather than compete.

**ReAct and Reflexion.** Both are agent-loop patterns where the loop itself
is the thing consuming budget, one model call and one or more tool results
per iteration. A loop pattern with no token budgeting behind it accretes
tool output turn after turn with nothing deciding when enough is enough;
Token Budget is the resource-accounting layer these loop patterns need
underneath them to run for more than a handful of iterations without either
overflowing or silently degrading.

**Chunking Strategies, Hybrid Search, GraphRAG.** These retrieval-side
patterns decide what candidate content exists and how it is ranked before
budgeting ever sees it. The relevance-ranked selection variant in dimension
8 depends directly on a ranking signal these patterns supply; Token Budget
takes their ranked output and decides how much of it actually fits.

**Model Context Protocol.** Tool and resource definitions exposed through
MCP are themselves a producer competing for budget, and the lazy or deferred
loading variant in dimension 8 exists specifically because a session with
many configured MCP servers can otherwise spend a large share of its budget
on tool schemas the model never ends up calling.

**Circuit Breaker and retry-with-backoff.** Not part of this catalog's
current entries but worth naming because the throughput governor in
dimension 5 is, in its shape, a circuit breaker keyed on tokens and requests
per minute rather than on error rate, and the standard response to a 429
from a provider is the standard retry-with-backoff shape, honouring the
provider's retry-after signal rather than retrying immediately.

Nothing in the catalog is directly incompatible with Token Budget, though
one philosophical tension is worth naming rather than hiding. As context
windows grow toward and past a million tokens on some providers, an
argument circulates that budgeting matters less because sending everything
and letting the model find what it needs becomes affordable. That argument
addresses the context-budget axis only. It does not touch the
throughput-budget or spend-budget axes, which are enforced independently of
window size, so the pattern's relevance narrows as windows grow rather than
disappearing.

## 14. Refactoring path in and out

Introducing budgeting into a system that currently assembles an unbudgeted
prompt string.

1. Instrument the current, unbudgeted prompt assembly with a token counter
   before changing any behaviour, and log the actual token usage the
   provider reports back for a representative sample of real tasks. This
   establishes a baseline and reveals how far a cheap approximate counter's
   estimate would have been from reality, which decides how large a safety
   margin the next step needs.
2. Name the producers explicitly. Whatever pieces of content the current
   string concatenates, system instructions, tool schemas, retrieved
   context, history, give each one a name and a place in the code, even
   before any budgeting logic exists.
3. Assign an explicit priority order across the named producers, written
   down, not implied by the order the code happens to concatenate them in.
4. Introduce a hard limit check using the cheap approximate counter first,
   with the safety margin sized from step one's drift measurement, and fail
   loudly, not silently, when the check trips, so the gap between the
   approximate estimate and reality is visible during rollout rather than
   discovered later.
5. Add an eviction policy for the lowest-priority producer only, starting
   with the crudest strategy that solves the immediate overflow, usually
   dropping the oldest history, before graduating to a ranked or
   summarization-based strategy once the crude version is proven stable.
6. Add the throughput governor as a component wrapping the transport client,
   separate from the assembler, because it is a different axis measured
   over a different unit of time, per dimension 5.
7. Add the telemetry described in dimension 16 before declaring the
   migration complete, because a budget with no visibility into its own
   eviction rate and estimate drift will rot silently the next time the
   target model, and therefore its tokenizer and its context window, changes
   underneath the code.

Removing an explicit allocator when it has stopped earning its place.

A budget allocator that has, in practice, always computed the same fixed
split for every call at a given call site, because that call site's inputs
turned out to be bounded and homogeneous after all, has degenerated into a
constant. At that point the allocator adds indirection without adding a
decision, and it is a candidate for collapsing into a simple guard clause
that asserts the input is under a fixed limit, the extract-guard-clause
shape this catalog's refactoring family covers for the general case of
replacing conditional machinery with a direct check once the condition it
guards has become effectively constant. The throughput governor almost never
goes away in this collapse, because it protects an account-level constraint
that exists independent of any one call site's shape.

## 15. Testing and verification

- **Boundary assertion tests.** Assert the assembled prompt's exact token
  count is inside the configured limit across a matrix of representative
  and adversarial inputs, an empty history, a very long single history, a
  non-English input, and a JSON-heavy tool result, because these are exactly
  the shapes that diverge most from an approximate counter's estimate.
- **Golden tests for the eviction policy.** With a deterministic priority
  order, per failure mode 4 in dimension 11, a fixed input history plus a
  fixed budget must produce an exact expected output. This is only possible
  because the eviction policy is written as a pure function; a
  non-deterministic policy cannot be golden-tested at all, which is itself a
  reason to prefer determinism.
- **Counter drift contract tests.** Run a corpus of representative texts
  through both the approximate counter and the exact, provider-backed
  counter, assert the error stays under the safety margin configured in
  dimension 8's reservation-based headroom variant, and alert when the drift
  grows, which is the earliest signal that a model or tokenizer upgrade has
  silently changed the assumptions the approximate counter was tuned
  against.
- **Fuzz tests at the boundary.** Generate inputs sized at exactly the
  limit, one under, and one over, and assert the allocator's behaviour at
  each is the intended one, an off-by-one at this specific boundary is the
  single most common bug in hand-written budget arithmetic.
- **Fairness load tests for the throughput governor.** Simulate several
  concurrent callers whose combined usage exceeds the tokens-per-minute
  limit, and assert that no single caller is starved indefinitely while
  others proceed, which is a property a naive first-come-first-served queue
  does not guarantee under sustained pressure from one heavy caller.
- **Test doubles for compaction.** A unit test exercising the eviction path
  should use a fake summarizer that returns a fixed marker string rather
  than a real model call, both so the test is fast and deterministic and so
  it does not carry the real cost of an LLM call every time the suite runs;
  a separate, smaller set of integration tests exercises the real
  summarizer against real inputs to catch quality regressions the unit
  tests by design cannot see.

## 16. Observability signals

- **Allocated versus used tokens per producer, per request**, as a
  histogram. A healthy producer tracks its allocation closely over time; a
  producer that is consistently allocated far more than it uses is a
  candidate for a smaller fixed share, and one consistently pinned at its
  limit is a candidate for eviction tuning or a larger share.
- **Eviction and truncation events**, counted by producer and by reason
  (over-budget, priority preemption, hard limit). A rising eviction rate
  on a high-priority producer, the system prompt or the current task
  framing, is a leading indicator of the quality degradation described in
  failure mode 2, and should alert well before a user notices anything.
- **Counter estimate error**, the absolute difference between the
  approximate counter's prediction and the actual token count the provider
  reports, tracked as a trend rather than a single value. A sudden jump
  after a model version change is the signal that the approximate counter's
  tuning no longer matches the new tokenizer.
- **Cache hit ratio**, cache-read tokens divided by total input tokens on
  providers that expose this, a proxy for effective throughput headroom
  rather than only a cost metric, since cache-read tokens can be exempt from
  a provider's per-minute rate limit, per dimension 8's caching-aware
  variant.
- **Rate-limit headroom**, sampled from the provider's own response headers
  on every request rather than inferred only from a 429, giving a real-time
  gauge of remaining throughput budget rather than a binary signal that
  arrives only after the budget is already exhausted.
- **A structured log line on every eviction**, naming which producer was
  trimmed, by how many tokens, and by which policy, so a debugging session
  can reconstruct precisely what the model did not see for a given request,
  which is the fastest path to diagnosing an answer that looks confidently
  wrong for no obvious reason.

A healthy instance shows allocation utilization near, but under, one hundred
percent of the disposable budget, a low and stable eviction rate on
low-priority producers only, counter drift close to zero, and a cache hit
ratio that rises as a session gets longer. A failing instance shows sustained
eviction of a high-priority producer, a drift spike coinciding with a
provider-side model change nobody on the team was told about, or rate-limit
headroom sitting near zero continuously rather than only spiking under load.

## 17. Security and privacy implications

Eviction is a capacity decision, not a redaction control, and treating it as
one is a real mistake to guard against. A sensitive fragment that a
compaction step summarizes away is still present in the un-summarized
original that the summarizer read, and if that original is retained in an
external memory store, as dimension 14's fix for failure mode 6
recommends, the sensitive content has not been removed from the system, it
has moved. A system with a data-retention or right-to-deletion obligation
must track sensitive content through every tier a Token Budget or Agent
Memory implementation moves it into, not only the in-context window the
budget is actively managing.

A shared cache prefix across requests, the mechanism behind the
caching-aware budgeting variant in dimension 8, must never be assembled by
concatenating content from more than one tenant merely to reach a provider's
cache-eligible minimum token threshold, because cached content persists on
the provider's infrastructure for the cache's time-to-live, and a shared
prefix built across tenant boundaries risks one tenant's content becoming
part of a cache another tenant's request could, under some implementation
mistakes, end up reading.

The telemetry described in dimension 16, particularly the structured log
line naming what was evicted, is itself a place sensitive content can end
up if the logged fragment is not scrubbed, because a log built to help
diagnose what the model did not see can, by construction, capture exactly
the content a security or compliance policy wanted removed from the system's
visible surface. Redact or hash sensitive spans before they land in an
eviction log, the same way any other application log handling personal data
would be scrubbed.

Finally, any policy that inspects request content to decide priority, for
example routing a request detected to contain personal data to a stricter,
smaller budget so less of it is retained in-context, is itself processing
that sensitive content to make the routing decision, and the code performing
that inspection falls under the same data-handling policy as the model call
it is deciding budget for, not a lesser one because it runs before the model
sees anything.

## 18. References

1. Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones,
   Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin, "Attention Is All You
   Need," arXiv 1706.03762, June 2017, section 3.2.1, verified 2026-08-03,
   [arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762).
2. Anthropic, "Prompt caching," Claude Platform documentation, verified
   2026-08-03, [platform.claude.com/docs/en/build-with-claude/prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).
3. Anthropic, "Rate limits," Claude Platform API documentation, verified
   2026-08-03, [platform.claude.com/docs/en/api/rate-limits](https://platform.claude.com/docs/en/api/rate-limits).
4. Anthropic, "Manage costs effectively," Claude Code documentation,
   verified 2026-08-03, [code.claude.com/docs/en/costs](https://code.claude.com/docs/en/costs).
5. LangChain, `trim_messages` implementation, `langchain_core.messages.utils`,
   verified against source 2026-08-03,
   [raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/messages/utils.py](https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/messages/utils.py).
6. OpenAI, tiktoken repository README, verified 2026-08-03,
   [github.com/openai/tiktoken](https://github.com/openai/tiktoken).
7. Google, "Context caching," Gemini API documentation, verified 2026-08-03,
   [ai.google.dev/gemini-api/docs/caching](https://ai.google.dev/gemini-api/docs/caching).

## Code examples

### TypeScript

```typescript
interface Producer {
  name: string;
  priority: number;
  content: string;
}

interface AllocatorResult {
  assembled: string;
  evicted: { name: string; tokensDropped: number }[];
}

function countTokens(text: string): number {
  // A cheap approximation, calibrated against the real tokenizer per
  // dimension 8. Never used at the hard limit without a safety margin.
  return Math.ceil(text.length / 4);
}

function truncateToTokens(text: string, maxTokens: number): string {
  const maxChars = maxTokens * 4;
  if (text.length <= maxChars) return text;
  return text.slice(text.length - maxChars);
}

class TokenBudgetAllocator {
  private readonly disposableBudget: number;

  constructor(contextWindow: number, reservedOutput: number, overhead = 0) {
    this.disposableBudget = contextWindow - reservedOutput - overhead;
    if (this.disposableBudget <= 0) {
      throw new Error("reserved output and overhead exceed context window");
    }
  }

  assemble(producers: Producer[]): AllocatorResult {
    const ordered = [...producers].sort((a, b) => b.priority - a.priority);
    const evicted: { name: string; tokensDropped: number }[] = [];
    let remaining = this.disposableBudget;
    const kept: Producer[] = [];

    for (const producer of ordered) {
      const needed = countTokens(producer.content);
      if (needed <= remaining) {
        kept.push(producer);
        remaining -= needed;
        continue;
      }
      if (remaining <= 0) {
        evicted.push({ name: producer.name, tokensDropped: needed });
        continue;
      }
      const trimmed = truncateToTokens(producer.content, remaining);
      kept.push({ ...producer, content: trimmed });
      evicted.push({
        name: producer.name,
        tokensDropped: needed - countTokens(trimmed),
      });
      remaining = 0;
    }

    // Reassemble in the ORIGINAL section order, not priority order, so a
    // stable prefix is produced across calls and prompt caching stays
    // effective.
    const byName = new Map(kept.map((p) => [p.name, p]));
    const assembled = producers
      .map((p) => byName.get(p.name)?.content ?? "")
      .filter((c) => c.length > 0)
      .join("\n\n");

    return { assembled, evicted };
  }
}

class ThroughputGovernor {
  private tokensUsedInWindow = 0;
  private windowStart = Date.now();
  private readonly windowMs: number;

  constructor(
    private readonly tokensPerMinute: number,
    windowMs = 60_000
  ) {
    this.windowMs = windowMs;
  }

  private rollWindowIfExpired(now: number): void {
    if (now - this.windowStart >= this.windowMs) {
      this.windowStart = now;
      this.tokensUsedInWindow = 0;
    }
  }

  tryConsume(tokens: number): { allowed: boolean; retryAfterMs: number } {
    const now = Date.now();
    this.rollWindowIfExpired(now);
    if (this.tokensUsedInWindow + tokens > this.tokensPerMinute) {
      const retryAfterMs = this.windowMs - (now - this.windowStart);
      return { allowed: false, retryAfterMs };
    }
    this.tokensUsedInWindow += tokens;
    return { allowed: true, retryAfterMs: 0 };
  }
}

const allocator = new TokenBudgetAllocator(32_000, 2_000, 200);
const governor = new ThroughputGovernor(120_000);

const result = allocator.assemble([
  { name: "system", priority: 100, content: "You are a support agent." },
  { name: "tools", priority: 80, content: "{ tool schemas }" },
  { name: "history", priority: 40, content: "very long chat transcript" },
]);

const decision = governor.tryConsume(countTokens(result.assembled));
if (!decision.allowed) {
  throw new Error(`throughput budget exceeded, retry after ${decision.retryAfterMs}ms`);
}
```

### Python

```python
from dataclasses import dataclass, replace
from typing import Callable


def approximate_token_count(text: str) -> int:
    # Calibrated placeholder. Swap for a real tokenizer near a hard limit.
    return max(1, len(text) // 4)


@dataclass(frozen=True)
class Producer:
    name: str
    priority: int
    content: str


@dataclass(frozen=True)
class EvictionRecord:
    name: str
    tokens_dropped: int


@dataclass(frozen=True)
class AllocationResult:
    assembled: str
    evictions: tuple[EvictionRecord, ...]


class TokenBudgetAllocator:
    def __init__(
        self,
        context_window: int,
        reserved_output: int,
        overhead: int = 0,
        counter: Callable[[str], int] = approximate_token_count,
    ) -> None:
        self.disposable = context_window - reserved_output - overhead
        if self.disposable <= 0:
            raise ValueError("reserved output and overhead exceed context window")
        self.counter = counter

    def _truncate(self, text: str, max_tokens: int) -> str:
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[-max_chars:]

    def assemble(self, producers: list[Producer]) -> AllocationResult:
        ordered = sorted(producers, key=lambda p: p.priority, reverse=True)
        remaining = self.disposable
        evictions: list[EvictionRecord] = []
        kept: dict[str, Producer] = {}

        for producer in ordered:
            needed = self.counter(producer.content)
            if needed <= remaining:
                kept[producer.name] = producer
                remaining -= needed
                continue
            if remaining <= 0:
                evictions.append(EvictionRecord(producer.name, needed))
                continue
            trimmed_content = self._truncate(producer.content, remaining)
            kept[producer.name] = replace(producer, content=trimmed_content)
            evictions.append(
                EvictionRecord(
                    producer.name, needed - self.counter(trimmed_content)
                )
            )
            remaining = 0

        # Original order preserved so the assembled prefix stays stable
        # across calls, which is what keeps a caching layer effective.
        pieces = [
            kept[p.name].content for p in producers if p.name in kept
        ]
        return AllocationResult("\n\n".join(pieces), tuple(evictions))


class ThroughputGovernor:
    def __init__(self, tokens_per_minute: int, window_seconds: float = 60.0) -> None:
        self.tokens_per_minute = tokens_per_minute
        self.window_seconds = window_seconds
        self._used = 0
        self._window_start: float | None = None

    def try_consume(self, tokens: int, now: float) -> tuple[bool, float]:
        if self._window_start is None or now - self._window_start >= self.window_seconds:
            self._window_start = now
            self._used = 0
        if self._used + tokens > self.tokens_per_minute:
            retry_after = self.window_seconds - (now - self._window_start)
            return False, retry_after
        self._used += tokens
        return True, 0.0


if __name__ == "__main__":
    allocator = TokenBudgetAllocator(context_window=32_000, reserved_output=2_000)
    result = allocator.assemble(
        [
            Producer("system", 100, "You are a support agent."),
            Producer("tools", 80, "{ tool schemas }"),
            Producer("history", 40, "very long chat transcript " * 50),
        ]
    )
    governor = ThroughputGovernor(tokens_per_minute=120_000)
    allowed, retry_after = governor.try_consume(
        approximate_token_count(result.assembled), now=0.0
    )
    if not allowed:
        raise RuntimeError(f"throughput budget exceeded, retry after {retry_after}s")
```

### Go

```go
package main

import (
	"errors"
	"fmt"
	"sort"
	"strings"
	"time"
)

// approximateTokenCount is a calibrated placeholder heuristic. Swap for the
// provider's real tokenizer for any section sitting close to the limit.
func approximateTokenCount(text string) int {
	n := len(text) / 4
	if n < 1 {
		n = 1
	}
	return n
}

type Producer struct {
	Name     string
	Priority int
	Content  string
}

type EvictionRecord struct {
	Name          string
	TokensDropped int
}

type AllocationResult struct {
	Assembled string
	Evictions []EvictionRecord
}

type TokenBudgetAllocator struct {
	disposable int
	counter    func(string) int
}

func NewTokenBudgetAllocator(contextWindow, reservedOutput, overhead int) (*TokenBudgetAllocator, error) {
	disposable := contextWindow - reservedOutput - overhead
	if disposable <= 0 {
		return nil, errors.New("reserved output and overhead exceed context window")
	}
	return &TokenBudgetAllocator{disposable: disposable, counter: approximateTokenCount}, nil
}

func truncateToTokens(text string, maxTokens int) string {
	maxChars := maxTokens * 4
	if len(text) <= maxChars {
		return text
	}
	return text[len(text)-maxChars:]
}

func (a *TokenBudgetAllocator) Assemble(producers []Producer) AllocationResult {
	ordered := make([]Producer, len(producers))
	copy(ordered, producers)
	sort.Slice(ordered, func(i, j int) bool { return ordered[i].Priority > ordered[j].Priority })

	remaining := a.disposable
	var evictions []EvictionRecord
	kept := make(map[string]Producer)

	for _, p := range ordered {
		needed := a.counter(p.Content)
		switch {
		case needed <= remaining:
			kept[p.Name] = p
			remaining -= needed
		case remaining <= 0:
			evictions = append(evictions, EvictionRecord{p.Name, needed})
		default:
			trimmed := truncateToTokens(p.Content, remaining)
			kept[p.Name] = Producer{p.Name, p.Priority, trimmed}
			evictions = append(evictions, EvictionRecord{
				Name:          p.Name,
				TokensDropped: needed - a.counter(trimmed),
			})
			remaining = 0
		}
	}

	// Original order preserved so the assembled prefix stays stable across
	// calls, which is what keeps a caching layer effective.
	var pieces []string
	for _, p := range producers {
		if kp, ok := kept[p.Name]; ok {
			pieces = append(pieces, kp.Content)
		}
	}
	return AllocationResult{Assembled: strings.Join(pieces, "\n\n"), Evictions: evictions}
}

type ThroughputGovernor struct {
	tokensPerMinute int
	windowStart     time.Time
	used            int
	window          time.Duration
}

func NewThroughputGovernor(tokensPerMinute int) *ThroughputGovernor {
	return &ThroughputGovernor{tokensPerMinute: tokensPerMinute, window: time.Minute}
}

func (g *ThroughputGovernor) TryConsume(tokens int, now time.Time) (bool, time.Duration) {
	if g.windowStart.IsZero() || now.Sub(g.windowStart) >= g.window {
		g.windowStart = now
		g.used = 0
	}
	if g.used+tokens > g.tokensPerMinute {
		return false, g.window - now.Sub(g.windowStart)
	}
	g.used += tokens
	return true, 0
}

func main() {
	allocator, err := NewTokenBudgetAllocator(32000, 2000, 200)
	if err != nil {
		panic(err)
	}
	result := allocator.Assemble([]Producer{
		{Name: "system", Priority: 100, Content: "You are a support agent."},
		{Name: "tools", Priority: 80, Content: "{ tool schemas }"},
		{Name: "history", Priority: 40, Content: strings.Repeat("very long chat transcript ", 50)},
	})
	governor := NewThroughputGovernor(120000)
	allowed, retryAfter := governor.TryConsume(approximateTokenCount(result.Assembled), time.Now())
	if !allowed {
		panic(fmt.Sprintf("throughput budget exceeded, retry after %v", retryAfter))
	}
}
```
