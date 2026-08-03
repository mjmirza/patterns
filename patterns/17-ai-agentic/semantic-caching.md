---
name: Semantic Caching
slug: semantic-caching
family: 17-ai-agentic
category: AI Agentic
aliases: [Embedding Cache, Similarity Cache, LLM Semantic Cache, Prompt Cache (informal, ambiguous)]
first_described: "Shaul Dar, Michael J. Franklin, Bjorn Thor Jonsson, Divesh Srivastava, Michael Tan, VLDB 1996 (database query caching); applied to LLM prompt and completion caching by GPTCache (Zilliz, March 2023)"
maturity: established
related: [tool-result-caching, cost-guard, llm-circuit-breaker, rate-limiting, retrieval-augmented-generation, hybrid-search, reranking, input-guardrails]
incompatible_with: []
verified: 2026-08-03
---

# Semantic Caching

## 1. Name, aliases, and lineage

The canonical name in current practice is Semantic Caching. The concept has two
distinct lineages that share a name and a shape but not an implementation, and
conflating them is the first mistake most write-ups make.

The name itself was coined in the database systems literature. Shaul Dar,
Michael J. Franklin, Bjorn Thor Jonsson, Divesh Srivastava, and Michael Tan,
"Semantic Data Caching and Replacement," Proceedings of the 22nd International
Conference on Very Large Data Bases (VLDB), 1996, pages 330 to 341, indexed at
https://dblp.org/rec/conf/vldb/DarFJST96.html (verified 2026-08-03). That paper
defines a semantic cache as one that organizes cached content around the
semantics of a query, typically a predicate over a relation, rather than around
physical pages or byte ranges. A new query is split into a portion answerable
from what the cache already holds, called the semantic region, and a remainder
query sent to the backing store for the missing part. This is the ancestor of
the idea, not the pattern documented in this entry. A predicate-based semantic
cache reasons over structured SQL-like conditions and can answer a query
exactly from a partial cache hit. Nothing in this entry's variant does that.

The pattern this entry documents is the LLM-era descendant, and it borrows the
name because it shares one property with the 1996 idea. A cache lookup that is
not exact-key matching, but is instead matching by meaning. The mechanism is
different in kind. An incoming prompt is converted to a vector embedding, and
that vector is compared by a distance metric, almost always cosine similarity,
against the embeddings of previously seen prompts. If the closest match clears
a similarity threshold, the cached response for that prior prompt is returned
without calling the language model. If nothing clears the threshold, the
request goes to the model and, on a successful response, both the prompt's
embedding and the response text are written into the cache for future lookups.
GPTCache, released by Zilliz (the company behind the Milvus vector database) in
March 2023, is widely cited in practitioner literature as the first broadly
adopted open source implementation of this LLM-specific variant, described
further in dimension 9. The GPTCache project itself describes its purpose as
reducing large language model API cost and latency by recognizing when a new
query is semantically close enough to a prior one to reuse the prior answer
(GPTCache repository, https://github.com/zilliztech/GPTCache, verified
2026-08-03).

"Prompt caching" is a related but different term used by some model providers
for a server-side mechanism that caches the token-level KV state of a repeated
prefix (a system prompt, a long document) to skip recomputation on an exact or
near-exact prefix match. That is an optimization inside a single provider's
inference stack, keyed on token prefixes, not on semantic distance between
distinct prompts, and it is out of scope for this entry. Where a source uses
"prompt cache" to mean embedding-similarity caching of full request and
response pairs, this entry treats it as a synonym for semantic caching and
notes the ambiguity in the aliases list above.

## 2. Problem and context

A production system built on a hosted large language model pays for every
call, in latency and in metered tokens, and a meaningful share of real traffic
is not novel. The same handful of questions get asked by many users in
slightly different words. A customer support bot answers "how do I reset my
password" and "I forgot my password, what do I do" as two API calls that
should have been one. A documentation assistant answers "what is your refund
policy" and "can I get my money back" the same way twice. A retrieval pipeline
re-embeds and re-summarizes the same handful of frequently asked questions
across thousands of sessions. Exact-match caching, keyed on the literal prompt
string, catches almost none of this traffic, because the literal text rarely
repeats even when the intent does.

The context in which semantic caching is the right answer has a specific
shape. There is a real, measurable rate of semantically repeated queries in
the traffic. This is not automatic. A system where every prompt genuinely
differs in what it is asking, a code generation tool operating on a unique
file each time, a data analysis agent summarizing a different document per
call, sees no repetition to exploit, and adding a semantic cache there adds
cost and risk with no offsetting benefit. The pattern also assumes that a
degree of staleness in the cached answer is acceptable for the affected
traffic. A cached response was correct for a prior prompt at a prior moment,
and returning it for a semantically close but not identical new prompt is a
bet that the two intents share an answer, and that bet is wrong often enough
to need active management, covered in dimensions 10 and 11.

The cost pressure that makes this worth building is concrete and dated. Model
provider pricing in 2026 charges per input and output token, and a cache hit
avoids both the input tokens of the prompt and the output tokens of the
generation, along with the round trip latency of the model call itself. A
managed vendor in this space, Redis LangCache, states in its own marketing
material that a reported customer case achieved a 70 percent cache hit rate
and a corresponding 70 percent reduction in LLM spend, alongside a claim of up
to 90 percent API cost savings and 4 times faster response for a cache hit
compared to a full model call (Redis, LangCache product page,
https://redis.io/langcache/, verified 2026-08-03). These are vendor-reported
figures for a specific customer's traffic mix and should be read as an upper
bound achievable when the hit rate is genuinely high, not as a general
expectation for every workload, a distinction elaborated in dimension 3.

## 3. Forces

The pattern balances a small number of forces, and the balance point moves a
great deal depending on the traffic shape, which is why this pattern is one of
the more workload-sensitive entries in this catalog.

Cost and latency are favored, and favored strongly, when the hit rate is high.
A cache hit is close to free next to a model call. An embedding lookup against
a vector index costs microseconds to low milliseconds, versus hundreds of
milliseconds to several seconds for a generation call plus the metered cost of
the tokens. The entire value of the pattern is concentrated in this one force,
and it scales linearly with hit rate. A 5 percent hit rate saves a real but
modest amount. A 60 to 70 percent hit rate, achievable in narrow, high-repeat
domains such as FAQ-style support bots, changes the unit economics of the
system.

Correctness is sacrificed, and this is the central engineering trade of the
whole pattern. A semantic match is a similarity score, not an equality test.
Returning a cached answer to a prompt that is close in embedding space but
different in what it actually asks produces a wrong answer delivered with the
same confidence as a correct one, and the failure is silent. Nothing in the
system signals that a substitution occurred unless it is explicitly logged and
surfaced, covered in dimension 16.

Freshness is sacrificed in proportion to the cache time-to-live. A cached
answer reflects the state of the world, and the state of the model's
knowledge, at the moment it was written. A support answer about a pricing
tier, a policy, or a product feature can go stale the moment the underlying
fact changes, and a semantic cache has no native mechanism to know that its
answer is now wrong, it only knows when the entry expires by TTL. This is why
this pattern is applied selectively rather than as a blanket wrapper around
every model call, discussed further in dimension 4.

Operability is a mixed force. A well-instrumented semantic cache adds a clean,
observable signal, the hit rate itself, that is genuinely useful for capacity
planning and cost forecasting. It also adds a second failure surface. An
embedding model outage or a vector index outage should degrade to calling the
underlying model directly, not to serving stale or wrong answers, and building
that fallback correctly is nontrivial, covered in dimension 11.

Cognitive load rises for anyone reasoning about correctness of the system as a
whole, because "the response for this request" is no longer a pure function of
"the request and the model," it is now a function of "the request, the model,
and the historical population of prior requests that happen to embed nearby."
Debugging a wrong answer now requires checking whether it was generated fresh
or served from cache, and if served from cache, what the original prompt was.

Consistency across near-duplicate requests is favored by design, and this can
be a genuine benefit rather than only a cost. Two users asking the same
underlying question in different words receive the identical, previously
reviewed answer, which is valuable in regulated or brand-sensitive domains
where consistent phrasing matters, provided the underlying question really is
the same.

## 4. Applicability and non-applicability

Reach for semantic caching when the following hold together.

- Traffic has a measurable, meaningfully repeated intent distribution.
  Customer support, internal documentation Q&A, FAQ bots, common code-review
  comment generation, or any assistant answering a bounded set of recurring
  questions phrased in varied natural language.
- The cost or latency of the underlying model call is high enough, relative to
  traffic volume, that even a modest hit rate produces a measurable saving.
  Large or reasoning-tier models, high request volume, or latency-sensitive
  user-facing paths where a cache hit's few-millisecond round trip is a
  materially better user experience than a multi-second generation.
- A bounded degree of staleness is acceptable for the cached content, and a
  time-to-live can be chosen that keeps the risk of serving outdated
  information within the domain's tolerance.
- The system already has, or can cheaply add, an embedding model and a vector
  index or vector-capable key-value store, so the marginal infrastructure cost
  of the cache is small next to the model call it is protecting.
- Wrong-but-plausible answers are recoverable, not catastrophic, for the
  domain. A customer support miss that gets corrected in a follow-up message
  is a bad experience, the same miss inside an autonomous agent authorizing a
  financial transaction is a different category of problem.

Do NOT reach for semantic caching in these cases, and the reason is the point.

- **The traffic is genuinely novel per request.** Code generation against a
  unique file, summarization of a unique document, or any task where two
  requests being "similar" in embedding space does not imply they should share
  an answer. A cache built here adds latency (the lookup itself), cost (the
  embedding call), and risk (wrong substitutions) with no offsetting hit rate.
  This is the single most common misapplication reported in practitioner
  write-ups, wrapping every model call in a semantic cache regardless of
  whether the traffic actually repeats.
- **Correctness-critical or high-stakes answers with no tolerance for a
  near-match substitution.** Medical, legal, or financial guidance where two
  differently worded questions can have materially different correct answers
  ("can I deduct this expense" versus "can I deduct this specific expense
  under this specific circumstance") is exactly the shape a similarity
  threshold cannot reliably distinguish. Azure API Management's own policy
  documentation states this plainly. Because semantic caching returns
  responses based on similarity rather than exact match, it can surface
  responses that are incorrect, outdated, or unsafe for the current request,
  and recommends evaluating the feature carefully and including safeguards
  (Microsoft Learn, "Azure API Management policy reference,
  llm-semantic-cache-lookup,"
  https://learn.microsoft.com/en-us/azure/api-management/llm-semantic-cache-lookup-policy,
  verified 2026-08-03).
- **The prompt legitimately encodes state that changes the correct answer
  even when the surface text looks similar.** "What is my account balance"
  asked by two different users, or by the same user at two different times,
  must never share a cached answer. The cache key needs to be partitioned by
  user, session, or another identity dimension (the `vary-by` mechanism in
  dimension 8), and a cache with no partitioning is a data leakage bug waiting
  to happen, not a caching bug.
- **Facts that change frequently or on a schedule the cache cannot observe.**
  Live pricing, inventory, or time-sensitive information should not sit behind
  a semantic cache with a TTL long enough to be worth the infrastructure, and
  is often better served by the underlying data source directly or by cache
  invalidation tied to the data change event rather than to elapsed time.
- **Low volume, low per-call cost.** If the underlying model call is cheap and
  infrequent, the fixed cost of running an embedding model and a vector index
  is not repaid. This is the same non-applicability shape any cache carries.
  A cache with a near-zero hit rate is pure overhead.
- **The desired behavior is exact-match, high-fidelity tool result reuse**, for
  example memoizing a deterministic function call an agent makes with the same
  arguments. That is Tool Result Caching, a distinct, exact-key pattern
  documented separately in this catalog and cross-referenced in dimension 13.
  Conflating the two produces a system that is either too loose (semantic
  matching applied to something that needs exact equality) or too strict
  (exact matching applied to natural language that never repeats verbatim).

## 5. Structure

Five participants, named by role.

- **Client or Application.** Issues the natural-language request that would
  otherwise go straight to the language model.
- **Embedding Model.** Converts a prompt (or a normalized version of it) into a
  fixed-length dense vector. This is a separate model from the generation
  model, chosen for retrieval quality and speed, not for generation ability.
- **Vector Index (or vector-capable store).** Holds the embeddings of
  previously seen prompts alongside pointers to their cached responses, and
  supports an approximate or exact nearest-neighbor query. In production this
  is typically a dedicated vector database, a vector-search extension of a
  general-purpose store such as Redis, or an in-memory index for small caches.
- **Similarity Evaluator.** Computes a distance or similarity score between the
  query embedding and the nearest cached embedding, and applies the configured
  threshold to decide hit or miss. This is a deliberately separated
  responsibility from the index itself, because the threshold, the distance
  metric, and any secondary evaluation (an optional smaller model that
  double-checks a borderline match, as GPTCache supports) are policy that
  changes independently of the storage engine.
- **Underlying Language Model.** Called only on a cache miss. Its response
  becomes the value written into the cache alongside the query's embedding.

The client never distinguishes a hit from a miss at the call site, which is
what makes it adoptable as a drop-in layer, whether that layer is a library
import, an API gateway policy, or a managed proxy service, covered as
implementation variants in dimension 8. The cache sits transparently between
the client and the model.

## 6. ASCII structure diagram

```
      +-------------+
      |   Client    |
      +------+------+
             |
             | prompt
             v
   +---------------------+
   |   Semantic Cache     |
   |   (gateway / library)|
   +----------+-----------+
              |
     +--------+---------+
     |                  |
     v                  v
+-----------+     +----------------+
| Embedding |     | Similarity     |
| Model     |     | Evaluator      |
+-----+-----+     | (threshold,    |
      |           |  distance      |
      | vector    |  metric)       |
      v           +--------+-------+
+-----------+              ^
| Vector    |  nearest      |
| Index     |--------------+
| (prompt   |  neighbor +
|  -> resp) |  score
+-----------+
      |
      | miss (score < threshold)
      v
+---------------------+
| Underlying LLM       |
| (generation model)   |
+----------+-----------+
           |
           | response
           v
   write embedding + response
   back into Vector Index
```

## 7. Dynamics

Two distinct flows exist. The lookup on request, and the write on a miss that
resolved.

```
Client          Semantic Cache      Embedding Model   Vector Index    LLM
  |                    |                    |               |          |
  |-- prompt --------->|                    |               |          |
  |                    |-- embed(prompt) -->|               |          |
  |                    |<-- vector ---------|               |          |
  |                    |-- nearest(vector) ------------------>|         |
  |                    |<-- (bestVec, resp, score) -----------|         |
  |                    |                    |               |          |
  |                    | if score >= threshold, return       |         |
  |                    | cached response                     |         |
  |<-- cached response |                    |               |          |
  |                    |                    |               |          |
  |                    | else (miss)                         |         |
  |                    |-- prompt -------------------------------------->|
  |                    |<-- generated response --------------------------|
  |<-- fresh response  |                    |               |          |
  |                    |-- store(vector, response, ttl) ----->|         |
  |                    |                    |               |          |
```

Two timing details matter in practice. First, the embedding call on the
lookup path is on the critical path of every single request, hit or miss, so
its latency is added to every call, and a slow or overloaded embedding service
degrades the cache into a net latency cost even on a hit. This is why the
embedding model chosen for this role is usually a small, fast, purpose-built
embedding model rather than a large general-purpose one. Second, the write on
a miss happens after the model response returns, so a burst of near-identical
requests arriving within the model's response latency window, a "thundering
herd" of the same question hitting the system in the same second before the
first one has finished and been cached, all miss and all call the model,
because none of them yet has anything to find. Some production implementations
address this with request coalescing, where a first request "locks" the
semantic region and concurrent duplicates wait on it, though this is not
universal.

## 8. Implementation variants

**Library, embedded in the application process.** GPTCache is the reference
example. A Python library that sits between the application and the model
provider's SDK, with pluggable embedding backends (its own ONNX models, OpenAI
embeddings, Hugging Face models) and pluggable vector stores (FAISS, Milvus,
Chroma, and others), configured by the application developer directly in code
(GPTCache repository, https://github.com/zilliztech/GPTCache, verified
2026-08-03). This variant gives the most control and the least operational
overhead to adopt at small scale, and pushes the operational burden (running
the vector index, choosing the embedding model, tuning the threshold) onto the
application team.

**API gateway policy.** Azure API Management implements semantic caching as a
pair of inbound and outbound policies, `llm-semantic-cache-lookup` and
`llm-semantic-cache-store`, applied to any LLM API the gateway proxies
(currently the OpenAI Chat Completions or Responses API shape, the Anthropic
Messages API shape on v2 tiers, and the Google Vertex AI API shape). The
lookup policy takes a `score-threshold` from 0.0 to 1.0, a reference to a
configured embeddings backend, and an optional `vary-by` expression used to
partition the cache, for example by subscription ID so that one caller can
never receive another caller's cached answer (Microsoft Learn,
"llm-semantic-cache-lookup policy reference,"
https://learn.microsoft.com/en-us/azure/api-management/llm-semantic-cache-lookup-policy,
verified 2026-08-03). This variant requires no code change in the calling
application, since the gateway intercepts the HTTP call, and centralizes cache
policy for every team behind that gateway, at the cost of coupling every
caller to the gateway's chosen embedding model and threshold.

**Fully managed service.** Redis LangCache exposes semantic caching as a REST
API. The application sends the prompt to LangCache's endpoint instead of the
model provider, LangCache performs the embedding, similarity search, and
threshold decision internally against a managed Redis Cloud backend, and
either returns a cached response or proxies to the model and caches the
result. Redis's own product page frames this explicitly as an alternative to
building the same thing in-house, offering a default embedding model or the
option to bring a custom one (Redis, LangCache product page,
https://redis.io/langcache/, verified 2026-08-03). This variant removes
essentially all infrastructure ownership from the adopting team, at the cost
of a per-request dependency on a third-party service and, for most
deployments, its pricing model.

**Threshold tuning strategy.** Every variant exposes a single knob that
dominates the pattern's behavior, how close is close enough. Azure's own
documentation recommends starting at a low value such as 0.05 (note that
Azure's score is a distance-like value where lower means more similar, the
opposite convention from a cosine-similarity score where higher means more
similar, and the exact convention differs by implementation and must be read
from that implementation's own documentation rather than assumed) and warns
that a threshold above roughly 0.2 in their scale risks returning mismatched
responses, recommending an even lower value for sensitive use cases
(Microsoft Learn, llm-semantic-cache-lookup policy reference, verified
2026-08-03). GPTCache instead runs on a cosine-similarity-style score where
higher means more similar, and supports pluggable similarity evaluation,
including using a second, typically smaller and cheaper model to double-check
a borderline nearest-neighbor match before committing to a cache hit, trading
a small amount of extra latency and cost for a lower false-hit rate.

**Cache key normalization.** Several implementations preprocess the prompt
before embedding it, stripping system messages (`ignore-system-messages` in
Azure's policy) or truncating to a maximum message count, on the reasoning
that a long, mostly-identical system prompt with a short varying user message
otherwise dominates the embedding and makes every request look similar to
every other request regardless of what the user actually asked.

**Partitioned or scoped caching.** Production deployments almost always
partition the cache by a dimension outside the prompt text itself, per
tenant, per user, per API key, or per conversation, using a `vary-by`-style
mechanism. An unpartitioned cache shared across all callers is the default
configuration in a toy example and close to a data-leakage bug in a real
multi-tenant system, discussed in dimension 17.

## 9. Known production uses

**GPTCache, Zilliz.** An open source Python library, first released March
2023, purpose-built to wrap LLM API calls (its adapters cover OpenAI's Chat
Completions API among others, with community integrations for LangChain and
LlamaIndex) with an embedding-and-vector-similarity cache in front of them.
Zilliz is the company that also maintains Milvus, an open source vector
database, and GPTCache is designed to plug into Milvus, FAISS, Chroma, and
other vector stores as its backing index. The project states its purpose is
reducing expenses through fewer API calls and improving latency through
cached retrieval rather than live generation (GPTCache repository,
https://github.com/zilliztech/GPTCache, verified 2026-08-03).

**Redis LangCache.** A fully managed semantic caching service offered through
Redis Cloud, exposed as a REST API that an application calls in place of, or
in front of, a direct model provider call. Redis's own product materials
report a customer case, described on the product page as Mangoes.ai, achieving
a 70 percent cache hit rate and a corresponding 70 percent reduction in LLM
spend, and claim up to 90 percent API cost savings and roughly 4 times faster
responses on a cache hit compared to a full model call (Redis, LangCache
product page, https://redis.io/langcache/, verified 2026-08-03). As with any
vendor-published customer figure, treat the specific percentages as evidence
of achievable upside for a favorable traffic mix, not as a guaranteed outcome.

**Azure API Management, `llm-semantic-cache-lookup` and
`llm-semantic-cache-store` policies.** A pair of gateway-level policies,
generally available for use across API Management's tiers, that add semantic
caching to any proxied LLM API without changing the calling application's
code. The policy reference documents the supported model API shapes (OpenAI,
Anthropic Messages on v2 tiers, Google Vertex AI), the `score-threshold` and
`embeddings-backend-id` configuration, the `ignore-system-messages` and
`max-message-count` tuning options, and the `vary-by` partitioning mechanism,
and explicitly documents the correctness risk of similarity-based responses
in its own usage notes (Microsoft Learn, "Azure API Management policy
reference, llm-semantic-cache-lookup,"
https://learn.microsoft.com/en-us/azure/api-management/llm-semantic-cache-lookup-policy,
verified 2026-08-03). This is a named, documented instance of the pattern
running inside a general-purpose, first-party cloud API gateway product,
distinct from the specialist vendor and open source library implementations
above.

## 10. Consequences

Positive.

- A cache hit removes the entire cost and most of the latency of a model
  call, and that saving compounds directly with the traffic's repeat rate.
- The pattern is adoptable incrementally and non-invasively, as a library
  wrapper, a gateway policy, or a managed proxy, none of which requires
  redesigning the application's request flow.
- It smooths tail latency for popular, repeated questions, which matters
  disproportionately for user-facing latency percentiles even at a modest
  average hit rate, because the highest-traffic questions are exactly the
  ones most likely to be cached.
- It produces a consistent, previously reviewed answer for near-duplicate
  intents, which is a genuine correctness and brand-consistency benefit in
  domains where consistent phrasing across users matters.
- The hit rate itself is a clean, cheap, continuously available signal for
  capacity planning, cost forecasting, and traffic-shape monitoring.

Negative.

- Every cache hit is a bet that semantic proximity implies answer identity,
  and that bet is sometimes wrong. The failure mode is a wrong answer
  delivered with full confidence and no visible indication that a
  substitution happened, unless the system explicitly surfaces it.
- The threshold is a single scalar trying to capture a genuinely
  multidimensional notion of "close enough," and no fixed threshold performs
  equally well across every query shape in a diverse traffic mix. It needs
  ongoing tuning against measured false-hit and false-miss rates.
- Adds a second, independent failure surface. The embedding model and the
  vector index both need their own availability, latency, and correctness
  monitoring, and a naive integration that fails the whole request on cache
  infrastructure trouble turns a caching optimization into a new outage
  cause.
- Introduces a staleness window bounded only by the configured time-to-live,
  and nothing in the base pattern detects that the underlying fact behind a
  cached answer has changed. Invalidation has to be handled separately.
- Without deliberate partitioning, the cache is a cross-tenant or cross-user
  data exposure risk, since one user's cached answer, and by extension a
  paraphrase of that user's original prompt content embedded in the response,
  can be served to a different user whose prompt merely embeds nearby.

## 11. Failure modes and misuse

**The over-eager threshold.** Symptom. Users report receiving answers that are
close to what they asked but not actually correct for their specific
question, often traced to two prompts that share most of their words but
differ in one clause that changes the correct answer ("can I return this
item" versus "can I return this item without a receipt"). Cause. A similarity
threshold set too permissively, frequently the result of tuning the threshold
against a handful of manually chosen example pairs rather than a measured
false-hit rate on real traffic. Fix. Tighten the threshold incrementally while
tracking the ratio of hits to misses and a sampled human or model-judged
correctness rate on the hits, per Azure's own guidance to start at a strict
value and loosen deliberately rather than the reverse (Microsoft Learn,
llm-semantic-cache-lookup policy reference, verified 2026-08-03).

**The unpartitioned cache leak.** Symptom. A user reports seeing a response
that references details from a different user's conversation, or an internal
security review finds that one API key's traffic populates a cache that
another API key's traffic can read from. Cause. The cache key is built from
the prompt embedding alone, with no tenant, user, or session dimension
included, so any two callers whose prompts embed near each other share a
cache entry regardless of who they are. Fix. Add an explicit partitioning
dimension to every cache key, the `vary-by` mechanism in the gateway variant
or an equivalent namespace prefix in a library or managed-service variant,
and treat an unpartitioned cache as a default-insecure configuration rather
than a convenience.

**Silent staleness.** Symptom. A support bot keeps stating an old pricing
tier, discount policy, or product capability well after it changed, and the
team cannot immediately tell whether the model itself is out of date or the
cache is serving a pre-change answer. Cause. A TTL set too long relative to
how often the underlying facts change, with no invalidation hook tied to the
actual data change event. Fix. Set the TTL to match the volatility of the
domain the cache serves, and where the underlying facts live in a system that
can emit a change event (a CMS publish, a pricing table update), wire an
explicit cache-flush or cache-key-versioning step into that event rather than
relying on elapsed time alone.

**The thundering herd on a popular new question.** Symptom. A sudden spike in
model provider calls and cost immediately following a product announcement or
an incident, even though the questions being asked are highly repetitive.
Cause. A burst of near-identical requests arrives within the window between
the first request's cache miss and its write-back completing, so every
request in that window also misses and calls the model, because the cache
entry does not exist yet. Fix. Add request coalescing, or in-flight request
deduplication, so that concurrent requests recognized as targeting the same
semantic region wait on the first in-flight generation rather than each
independently calling the model.

**Cache used where exact reuse was actually needed.** Symptom. A tool-calling
agent behaves inconsistently. Identical function calls with identical
arguments sometimes return different results, or a deterministic
computation's cached result is substituted for a semantically similar but
argument-different call. Cause. A semantic cache, built for natural-language
prompt reuse, was applied to structured tool or function call caching, where
exact-key equality on the arguments is the correct and available mechanism
and embedding-based similarity introduces unnecessary risk and unnecessary
infrastructure. Fix. Use exact-key caching (Tool Result Caching, documented
separately in this catalog) for deterministic, argument-keyed calls, and
reserve semantic caching for genuinely free-text, natural-language prompts.

**Fail-closed on cache infrastructure trouble.** Symptom. A vector index or
embedding service outage takes down the entire user-facing feature, even
though the underlying language model is healthy and reachable. Cause. The
cache lookup was implemented as a hard dependency on the request path, with
no fallback to bypass the cache and call the model directly on a cache-layer
error. Fix. Treat the cache as an optimization the request can proceed
without. Wrap the lookup and the store calls in a timeout and a
fail-open path that calls the underlying model directly on any cache-layer
failure, the same discipline documented for any resilience-critical call in
this catalog's Circuit Breaker and related entries.

## 12. Trade-off matrix

| Force | Semantic Caching | Exact-key (Tool Result) Caching | No caching, direct call every time |
|---|---|---|---|
| Cost on repeated intent | Low, scales with hit rate | Low, but only for byte-identical repeats | Full cost every call |
| Correctness risk | Present, similarity is a bet | Near zero, equality is exact | None from caching itself |
| Applies to free-text prompts | Yes, this is the point | No, needs identical arguments | N/A |
| Applies to deterministic tool calls | Poorly, unnecessary risk | Yes, this is the point | N/A |
| Freshness | Bounded by TTL, no native invalidation on fact change | Bounded by TTL, same limitation | Always current |
| Infrastructure added | Embedding model, vector index | Simple key-value store | None |
| Multi-tenant safety | Requires explicit partitioning or leaks | Requires explicit partitioning or leaks | N/A |
| Latency on a hit | Very low (embedding plus vector lookup) | Lowest (hash lookup) | Full model latency every time |
| Latency on a miss | Model latency plus embedding overhead | Model latency plus hash overhead | Model latency only |

## 13. Related and incompatible patterns

**Tool Result Caching** is the exact-key sibling of this pattern, documented
separately in this catalog. Where semantic caching matches free-text prompts
by embedding similarity because the same intent is rarely phrased identically
twice, Tool Result Caching matches deterministic function or tool calls by
exact argument equality because the same call with the same arguments should
always mean the same thing. A production system frequently runs both at
once, on different layers of the same agent, semantic caching in front of the
user-facing conversational turn, exact-key caching in front of the agent's
internal tool calls.

**Cost Guard** and **LLM Circuit Breaker**, both documented elsewhere in this
family, compose naturally with semantic caching rather than replacing it.
Cost Guard enforces a hard spend ceiling regardless of hit rate. Semantic
caching reduces how often that ceiling is approached. Circuit Breaker protects
against a failing underlying model provider. A well-built semantic cache
should fail open to the direct model call rather than depend on the circuit
breaker being closed, but the two mechanisms sit on the same request path and
their ordering, cache lookup, then circuit breaker, then model call, matters
for correct behavior during a provider outage.

**Rate Limiting** and semantic caching pull in different directions on the
same axis. Rate limiting rejects excess traffic, semantic caching absorbs
excess traffic by serving it from cache instead of the backend. A `vary-by`
partitioned semantic cache paired with a rate limit configured after the
cache lookup, as Azure's own documented example does, protects the backend
from load that the cache did not absorb.

**Retrieval Augmented Generation**, **Hybrid Search**, and **Reranking** solve
a different problem that looks superficially similar, finding the most
relevant document chunk for a query, versus finding whether a query has
already been answered before. The embedding, vector index, and similarity
scoring machinery is often the same underlying infrastructure and can be
shared operationally, but the retrieved object is different (source documents
to feed a generation, versus a previously generated answer to substitute for
generation), and conflating the two responsibilities inside one index without
separating them by namespace or metadata is a common source of confusing
cross-contamination between "documents I can cite from" and "answers I can
return verbatim."

**Input Guardrails** should generally run before a semantic cache lookup, not
after, so that a prompt injection or a policy-violating request is rejected
before it can populate the cache with a poisoned entry that a later,
legitimate user's semantically similar prompt might then retrieve.

No pattern in this catalog is flagged as strictly incompatible with semantic
caching. Its risks are managed by careful configuration and layering rather
than by avoiding certain co-occurring patterns entirely.

## 14. Refactoring path in and out

**Introducing semantic caching into a system with none.** Start by measuring,
not building. Log a representative sample of real prompts over a period long
enough to see genuine repetition (days to weeks, depending on traffic
volume), embed them offline, and cluster or nearest-neighbor them to estimate
the actual semantic repeat rate before writing any caching code. A traffic
mix with a low measured repeat rate does not justify the pattern regardless
of how appealing the idea sounds, per dimension 4. Once a meaningful repeat
rate is confirmed, introduce the cache in shadow mode first. Perform the
lookup and the similarity scoring on every request, log what would have been
a hit and at what score, but always call the model and always return the
fresh response. This produces a real distribution of near-miss scores against
real traffic, which is the only reliable basis for choosing a threshold,
rather than guessing at a threshold and discovering its false-hit rate from
user complaints. Only after a threshold has been chosen against that
distribution should the cache be switched from shadow mode to live mode,
starting with a strict, low false-hit, threshold and loosening it gradually
while watching a sampled correctness metric on the hits.

**Removing semantic caching, or scoping it down.** The signal that a semantic
cache has stopped earning its place, or was never earning it, is a low or
declining hit rate combined with support or quality complaints traceable to
wrong-but-plausible answers. The safe removal path is the reverse of
introduction. First tighten the threshold toward strictness to reduce the
false-hit rate while measuring whether the hit rate that remains still
justifies the infrastructure. If the remaining justified hit rate is small,
remove the cache lookup from the request path entirely rather than leaving
an underused cache running, since an underused cache is pure operational
liability with no offsetting benefit. Where only part of the traffic
justifies caching (a narrow FAQ subset inside a broader, more varied
assistant), scope the cache down to that subset explicitly by routing (see
the Routing pattern in this catalog) rather than running one cache tuned for
the whole mixed traffic, since a threshold tuned to be safe for varied
traffic is typically too strict to capture much of the FAQ subset's real
repeat rate, and a threshold tuned for the FAQ subset is typically too loose
for the varied traffic.

## 15. Testing and verification

A semantic cache is easy to test for the mechanical parts and hard to test
for the part that actually matters, and both need explicit attention.

The mechanical parts, a stored entry with a given embedding is retrievable
when queried with a sufficiently close vector, a stored entry expires after
its TTL, a partitioned entry is invisible to a query from a different
partition, a below-threshold nearest neighbor produces a documented miss
rather than a false hit, are ordinary unit tests against the cache
implementation directly, using a fixed, hand-constructed embedding function
so the test does not depend on a real model's nondeterminism or a live
network call, exactly the shape used in this entry's own code samples below.

The part that actually matters, whether the threshold produces correct
substitutions on real language, cannot be unit tested against a fixed
embedding function, because the whole risk lives in how a real embedding
model actually distributes real language in vector space. This needs an
evaluation set, a curated list of prompt pairs labeled by a human as "should
share an answer" and "should not share an answer despite superficial
similarity," ideally including deliberately adversarial near-miss pairs
(differ by one clause that changes the correct answer, differ by a negation,
differ by a named entity). Running this evaluation set through the real
embedding model and threshold, and tracking precision (of the pairs the cache
would treat as a hit, how many were actually correct to treat as a hit) and
recall (of the pairs that should have been a hit, how many the threshold
actually caught), gives a concrete, trackable signal for threshold tuning
that a live-traffic shadow-mode measurement, described in dimension 14,
should be reconciled against. Regression-test this evaluation set on every
change to the embedding model or the threshold, since either change can shift
the whole distance distribution and silently move the effective precision and
recall.

For integration testing, explicitly test the fail-open path. Simulate the
vector index or embedding service being unreachable or timing out, and assert
that the request still succeeds by falling through to a direct model call
rather than failing the request or hanging on the cache dependency, per the
failure mode in dimension 11.

## 16. Observability signals

Hit rate is the headline metric and the first thing to put on a dashboard.
The fraction of requests served from cache versus routed to the underlying
model, tracked over time and, where the traffic is heterogeneous, broken down
per route or per intent category, since a blended hit rate can hide a healthy
subset and an unhealthy subset averaging out to a misleadingly moderate
number.

The similarity score distribution of near-misses, not just hits, is the
second most useful signal. Logging the best-match score for every lookup,
whether or not it cleared the threshold, produces a live histogram that shows
whether the chosen threshold sits in a clean gap between "clearly the same
question" and "clearly a different question," or whether it sits in a dense,
ambiguous region where small threshold changes will swing the hit rate and
the error rate together, which is the signal that the traffic genuinely needs
a smarter matching strategy (a secondary evaluator model, a stricter
normalization step) rather than a threshold tweak.

A sampled correctness audit on cache hits, reviewed by a human or by a
separate model-as-judge pass, should run continuously at a low sampling rate
in production, not only during the initial threshold-tuning phase, because
the traffic distribution drifts over time and a threshold correct on
yesterday's mix can quietly become wrong on today's.

Cache write volume and cache size growth over time indicate whether TTL and
eviction policy are keeping the index at a manageable size, and a sudden
change in write volume, many more misses than usual, is often the earliest
available signal that either the traffic mix has shifted or the threshold was
just tightened enough to reduce hits without anyone yet noticing.

Latency should be measured separately for the embedding-and-lookup path and
for the full model-call path, so that a slow embedding service degrading the
hit path is visible before it erases the pattern's entire latency benefit,
and a health check or heartbeat on the vector index and embedding service
should feed the same alerting as any other dependency on the critical path.

## 17. Security and privacy implications

The unpartitioned-cache-as-data-leak failure mode described in dimension 11
is the primary security concern specific to this pattern. Because the cache
stores and later replays prior responses, including whatever content those
responses derived from the original prompt, a cache with no tenant, user, or
session partitioning is a mechanism by which one party's data can reach
another party who happens to phrase a request similarly. This is materially
different from, and more severe than, an ordinary key-value cache leak,
because the "key" here is not an opaque identifier chosen by the application
but a semantic distance computed over user-controlled natural language, which
means an attacker who wants to probe what another user asked can do so by
submitting many differently phrased guesses and watching for a cache hit,
turning the cache into a limited oracle over other users' prompt content if
partitioning is absent.

Prompt injection interacts with this pattern in a specific way. A malicious
prompt that succeeds in eliciting a harmful, policy-violating, or manipulated
response from the underlying model gets written into the cache exactly like
any other successful generation, and will then be replayed verbatim to any
future legitimate user whose unrelated, innocent prompt happens to embed
close enough to the malicious one. This is why input guardrails, documented
elsewhere in this catalog, are best placed before the cache lookup rather
than only before the model call. A request that would be rejected by content
policy should never be allowed to populate a cache that other users' traffic
can subsequently hit.

Data retention and right-to-erasure obligations extend to the cache. If a
user requests deletion of their data and their original prompt or its
response is sitting in the semantic cache, indexed by an embedding that
still reflects the content of that prompt, the deletion has to reach the
cache as well as any primary data store, which is easy to overlook because
the cache is often treated as disposable, low-stakes infrastructure rather
than as a store of retained personal content. Where the underlying prompts or
responses can contain personal or sensitive information, the cache inherits
the same encryption-at-rest, access control, and audit requirements as any
other store of that information, and a managed third-party semantic caching
service, per the vendor variant in dimension 8, means that content is now
also flowing through and resting on that vendor's infrastructure, which is a
data processing relationship that needs the same scrutiny as sending prompts
to the underlying model provider itself.

## 18. References

1. Shaul Dar, Michael J. Franklin, Bjorn Thor Jonsson, Divesh Srivastava,
   Michael Tan, "Semantic Data Caching and Replacement," Proceedings of the
   22nd International Conference on Very Large Data Bases (VLDB), 1996,
   pages 330 to 341. Bibliographic record: https://dblp.org/rec/conf/vldb/DarFJST96.html
   (verified 2026-08-03).
2. GPTCache repository (Zilliz), "A Library for Creating Semantic Cache for
   LLM Queries," https://github.com/zilliztech/GPTCache (verified 2026-08-03).
3. Redis, "LangCache, Fully Managed Semantic Caching," product page,
   https://redis.io/langcache/ (verified 2026-08-03).
4. Microsoft Learn, "Azure API Management policy reference,
   llm-semantic-cache-lookup," https://learn.microsoft.com/en-us/azure/api-management/llm-semantic-cache-lookup-policy
   (verified 2026-08-03).
5. This catalog, Tool Result Caching entry, family 17-ai-agentic, for the
   exact-key sibling pattern distinguished throughout dimensions 4, 11, and
   13 of this entry.

## Code examples

Three languages, chosen because a semantic cache is most often built as a
service-layer or gateway component, where Python (the dominant language for
the reference open source implementation, GPTCache), TypeScript (the
dominant language for Node-based API gateways and edge middleware), and Go
(a common choice for a standalone caching proxy or sidecar) are each
genuinely idiomatic. Each sample implements the same minimal shape, an
injectable embedding function, a cosine-similarity nearest-neighbor lookup
against an in-memory store with TTL-based expiry, a configurable similarity
threshold, and a store step on a cache write. The embedding function in each
sample is a small deterministic stand-in for a real model (such as
`text-embedding-3-small` or a self-hosted sentence encoder), used so the
example is runnable and testable with no network dependency or API key. A
production system replaces only that one function.

### Python

```python
"""Minimal semantic cache: embed, search by cosine similarity, threshold-gate a hit."""
from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class CacheEntry:
    prompt: str
    embedding: list[float]
    response: str
    created_at: float
    ttl_seconds: float
    hits: int = 0


@dataclass
class SemanticCache:
    embed: Callable[[str], list[float]]
    similarity_threshold: float = 0.92
    default_ttl_seconds: float = 3600.0
    entries: list[CacheEntry] = field(default_factory=list)

    def lookup(self, prompt: str) -> Optional[str]:
        now = time.time()
        query_vec = self.embed(prompt)
        self.entries = [e for e in self.entries if e.created_at + e.ttl_seconds > now]
        best_entry: Optional[CacheEntry] = None
        best_score = -1.0
        for entry in self.entries:
            score = cosine_similarity(query_vec, entry.embedding)
            if score > best_score:
                best_score = score
                best_entry = entry
        if best_entry is not None and best_score >= self.similarity_threshold:
            best_entry.hits += 1
            return best_entry.response
        return None

    def store(self, prompt: str, response: str, ttl_seconds: Optional[float] = None) -> None:
        self.entries.append(
            CacheEntry(
                prompt=prompt,
                embedding=self.embed(prompt),
                response=response,
                created_at=time.time(),
                ttl_seconds=ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds,
            )
        )


def fake_embed(text: str) -> list[float]:
    # Deterministic stand-in for a real embedding model, e.g. text-embedding-3-small.
    buckets = [0.0] * 8
    for i, ch in enumerate(text.lower()):
        buckets[i % 8] += (ord(ch) % 13) / 13.0
    return buckets


def demo() -> None:
    cache = SemanticCache(embed=fake_embed, similarity_threshold=0.999)
    assert cache.lookup("What is the capital of France?") is None
    cache.store("What is the capital of France?", "Paris.")
    hit = cache.lookup("What is the capital of France?")
    assert hit == "Paris.", f"expected exact hit, got {hit!r}"
    print("semantic_cache.py: exact-key hit and cold miss both verified")


if __name__ == "__main__":
    demo()
```

Ran successfully with `python3 semantic_cache.py`, printing the verification
line with no assertion failures.

### TypeScript

```typescript
// Minimal semantic cache: embed, search by cosine similarity, threshold-gate a hit.

type Embed = (text: string) => number[];

interface CacheEntry {
  prompt: string;
  embedding: number[];
  response: string;
  createdAt: number;
  ttlMs: number;
  hits: number;
}

function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  if (normA === 0 || normB === 0) return 0;
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

class SemanticCache {
  private entries: CacheEntry[] = [];

  constructor(
    private embed: Embed,
    private similarityThreshold = 0.92,
    private defaultTtlMs = 3600_000,
  ) {}

  lookup(prompt: string): string | null {
    const now = Date.now();
    this.entries = this.entries.filter((e) => e.createdAt + e.ttlMs > now);
    const queryVec = this.embed(prompt);
    let best: CacheEntry | null = null;
    let bestScore = -1;
    for (const entry of this.entries) {
      const score = cosineSimilarity(queryVec, entry.embedding);
      if (score > bestScore) {
        bestScore = score;
        best = entry;
      }
    }
    if (best !== null && bestScore >= this.similarityThreshold) {
      best.hits += 1;
      return best.response;
    }
    return null;
  }

  store(prompt: string, response: string, ttlMs?: number): void {
    this.entries.push({
      prompt,
      embedding: this.embed(prompt),
      response,
      createdAt: Date.now(),
      ttlMs: ttlMs ?? this.defaultTtlMs,
      hits: 0,
    });
  }
}

function fakeEmbed(text: string): number[] {
  const buckets = new Array(8).fill(0);
  const lower = text.toLowerCase();
  for (let i = 0; i < lower.length; i++) {
    buckets[i % 8] += (lower.charCodeAt(i) % 13) / 13;
  }
  return buckets;
}

function demo(): void {
  const cache = new SemanticCache(fakeEmbed, 0.999);
  const miss = cache.lookup("What is the capital of France?");
  if (miss !== null) throw new Error("expected cold miss");
  cache.store("What is the capital of France?", "Paris.");
  const hit = cache.lookup("What is the capital of France?");
  if (hit !== "Paris.") throw new Error(`expected exact hit, got ${hit}`);
  console.log("semantic-cache.ts: exact-key hit and cold miss both verified");
}

demo();
```

Compiled with `npx tsc --target es2020 --module commonjs --strict
semantic-cache.ts` and ran with `node semantic-cache.js`, printing the
verification line with no thrown errors.

### Go

```go
package main

import (
	"fmt"
	"math"
	"time"
)

type Embedder func(text string) []float64

type cacheEntry struct {
	prompt    string
	embedding []float64
	response  string
	createdAt time.Time
	ttl       time.Duration
	hits      int
}

type SemanticCache struct {
	embed      Embedder
	threshold  float64
	defaultTTL time.Duration
	entries    []*cacheEntry
}

func NewSemanticCache(embed Embedder, threshold float64, defaultTTL time.Duration) *SemanticCache {
	return &SemanticCache{embed: embed, threshold: threshold, defaultTTL: defaultTTL}
}

func cosineSimilarity(a, b []float64) float64 {
	var dot, normA, normB float64
	for i := range a {
		dot += a[i] * b[i]
		normA += a[i] * a[i]
		normB += b[i] * b[i]
	}
	if normA == 0 || normB == 0 {
		return 0
	}
	return dot / (math.Sqrt(normA) * math.Sqrt(normB))
}

func (c *SemanticCache) Lookup(prompt string) (string, bool) {
	now := time.Now()
	live := c.entries[:0]
	for _, e := range c.entries {
		if e.createdAt.Add(e.ttl).After(now) {
			live = append(live, e)
		}
	}
	c.entries = live

	queryVec := c.embed(prompt)
	var best *cacheEntry
	bestScore := -1.0
	for _, e := range c.entries {
		score := cosineSimilarity(queryVec, e.embedding)
		if score > bestScore {
			bestScore = score
			best = e
		}
	}
	if best != nil && bestScore >= c.threshold {
		best.hits++
		return best.response, true
	}
	return "", false
}

func (c *SemanticCache) Store(prompt, response string, ttl time.Duration) {
	if ttl <= 0 {
		ttl = c.defaultTTL
	}
	c.entries = append(c.entries, &cacheEntry{
		prompt:    prompt,
		embedding: c.embed(prompt),
		response:  response,
		createdAt: time.Now(),
		ttl:       ttl,
	})
}

func fakeEmbed(text string) []float64 {
	buckets := make([]float64, 8)
	for i, r := range []byte(text) {
		buckets[i%8] += float64(int(r)%13) / 13.0
	}
	return buckets
}

func main() {
	cache := NewSemanticCache(fakeEmbed, 0.999, time.Hour)
	if _, ok := cache.Lookup("What is the capital of France?"); ok {
		panic("expected cold miss")
	}
	cache.Store("What is the capital of France?", "Paris.", 0)
	resp, ok := cache.Lookup("What is the capital of France?")
	if !ok || resp != "Paris." {
		panic(fmt.Sprintf("expected exact hit, got %q ok=%v", resp, ok))
	}
	fmt.Println("main.go: exact-key hit and cold miss both verified")
}
```

Ran with `go run main.go`, printing the verification line with no panic.

Java and Rust are omitted from this entry's code samples. A Java Runtime was
not available on the machine that authored this entry (`javac` could not
locate a JRE), so a Java sample could not be compiled or run and is not
included rather than included unverified. Rust's toolchain was present but
was not exercised for this entry, since three verified, idiomatic, runnable
languages already satisfy this catalog's minimum, and the shape of the
pattern (a struct holding a vector, a linear or index-backed nearest-neighbor
scan, a threshold compare) does not surface anything additionally idiomatic
in Rust beyond what the Go sample already demonstrates for a systems-level
implementation.
