---
name: Reranking
slug: reranking
family: 17-ai-agentic
category: AI Agentic
aliases: [Two-Stage Retrieval, Cross-Encoder Reranking, Rerank]
first_described: "Nogueira, Cho 2019 (passage re-ranking with BERT); the retrieve-then-rerank shape as a general IR technique predates it"
maturity: canonical
related: [retrieval-augmented-generation, advanced-rag, hyde, agentic-rag, self-rag, corrective-rag]
incompatible_with: []
verified: 2026-08-03
---

## 1. Name, aliases, and lineage

The pattern is called Reranking, sometimes Two-Stage Retrieval, sometimes
Cross-Encoder Reranking when the second stage is specifically a cross-encoder
model. The name describes the mechanism precisely. a first retrieval stage
produces a candidate set, and a second stage reorders that set by a more
accurate but more expensive relevance judgment.

The retrieve-then-rerank shape is older than large language models. Classical
information retrieval systems used a cheap term-based first pass (BM25, TF-IDF)
followed by a learned ranking model, a family of techniques generally called
"learning to rank" going back to work at Microsoft Research and Yahoo in the
2000s. The specific technique that dominates today's reranking stage, applying
a BERT-style transformer as a cross-encoder scorer over query-document pairs,
was demonstrated by Rodrigo Nogueira and Kyunghyun Cho in "Passage Re-ranking
with BERT," submitted January 2019, which reported the approach topped the MS
MARCO passage retrieval leaderboard, outperforming the prior state of the art
by 27 percent relative in MRR at 10 (verified https://arxiv.org/abs/1901.04085,
2026-08-03). That paper is the lineage point most current documentation and
vendor pages cite when explaining why a cross-encoder second stage exists.

The pattern entered mainstream RAG (retrieval-augmented generation) vocabulary
once vector-database and embedding-provider vendors began shipping hosted
rerank endpoints as a standard pipeline stage, roughly 2023 onward, discussed
further in dimension 9.

## 2. Problem and context

A reader who has never heard the word reranking has still hit the problem it
solves. You build a search feature backed by embeddings. A user query comes
in, you embed it, you do a nearest-neighbor lookup against a vector index, and
you get back the top 20 or top 50 chunks by cosine similarity. Some of those
chunks are genuinely relevant. Several are near-misses, topically adjacent
text that shares vocabulary with the query but does not actually answer it.
You feed the top handful into a language model as context and the model's
answer quality degrades because irrelevant context crowds out the relevant
passage, or because the truly best passage sat at rank eight instead of rank
one and never made it into a token-limited context window.

The context in which this problem arises is any retrieval system where the
first-pass retrieval mechanism is cheap and approximate by design. Embedding
similarity search (dimension 8 of Retrieval-Augmented Generation) is fast
because it reduces a document to a single fixed-size vector and compares
vectors with a dot product or cosine similarity, an operation that high volumes to
millions of documents with approximate nearest neighbor indexes. That speed
comes at a cost. a single vector cannot capture every nuance of how a specific
query relates to a specific document, because the vector was computed for the
document alone, independent of any particular query. Term-based retrieval
(BM25) has the same limitation from a different direction. it counts word
overlap and cannot reason about paraphrase, negation, or the actual semantic
relationship between query and passage.

The problem reranking addresses is a mismatch between what the first-pass
retriever can afford to compute (cheap, per-document, independent of the
query) and what actually determines relevance (expensive, joint, query and
document read together). Reranking exists because you cannot afford the
expensive joint computation over the whole corpus, but you can afford it over
a small candidate set the cheap stage already narrowed down.

## 3. Forces

Latency versus accuracy. The cross-encoder or listwise reranker used in
stage two is dramatically more expensive per document than a vector similarity
lookup, because it must read the query and each document together through a
transformer rather than comparing precomputed vectors. Running it over an
entire corpus is infeasible for anything beyond a tiny document set. Running
it over the top 20 to 100 candidates a fast first stage already produced is
affordable and adds tens to a few hundred milliseconds. The pattern exists
specifically because this tradeoff is favorable at small N and unfavorable at
corpus scale.

Recall versus precision. The first-stage retriever's job is recall,
casting a wide enough net that the actually relevant documents are somewhere
in the candidate set, even if their rank within that set is poor. The
reranker's job is precision, sorting that candidate set so the truly relevant
documents rise to the top few positions that will actually be shown to a user
or fed to a language model. A reranker cannot rescue a document the first
stage failed to retrieve at all. this is the pattern's most important boundary
condition and is treated at length in dimension 4.

Coupling to the first-stage retriever. A reranker is only as good as the
candidate pool it receives. If the embedding model and the reranker were
trained on different notions of relevance, or if the first stage's candidate
count (top-k before reranking) is too small, the reranker optimizes over a
biased or incomplete sample. This creates an operational coupling. changing
the embedding model, chunking strategy, or top-k can silently change reranker
effectiveness even though the reranker itself did not change.

Cost and vendor dependency. Hosted rerankers (Cohere and comparable hosted providers) are billed per document scored or per query, adding a
recurring operational cost and a dependency on an external API's availability
and latency profile. Self-hosted cross-encoders (sentence-transformers models)
trade that operational dependency for GPU or CPU compute cost and the
maintenance burden of running inference infrastructure.

Cognitive load and pipeline complexity. Adding a reranking stage means
another component to monitor, another model to version, another point of
failure between "the answer existed in the corpus" and "the answer reached the
language model." Teams building a minimum viable RAG pipeline reasonably defer
reranking until they can show, with a concrete evaluation, that it moves the
metric that matters.

The pattern favors precision and answer quality at the cost of latency,
operational surface area, and either a recurring API bill or self-hosted
inference infrastructure. It sacrifices simplicity for a measurable lift in
the relevance of what ultimately reaches the consumer of the retrieval,
whether that consumer is a human reading search results or a language model
reading retrieved context.

## 4. Applicability and non-applicability

Reach for reranking when:

- The first-stage retriever (vector search, BM25, or a hybrid of the two)
  reliably places the correct answer somewhere in its top 20 to 100 results,
  but not reliably in the top 3 to 5 that will actually be surfaced or passed
  to a language model. This recall-good, precision-poor signature is the
  textbook indication.
- The downstream consumer is sensitive to result order, for example a
  language model context window that can only hold a handful of passages, or
  a search UI where users rarely scroll past the first few results.
- The corpus mixes documents of varying quality or specificity, so a
  query-independent vector similarity score is not discriminating enough,
  such as a support knowledge base where many articles mention the same
  product name but only one actually addresses the user's specific issue.
- You have hybrid retrieval (combining BM25 and vector search) and need a
  single, query-aware score to merge and reorder the two result sets rather
  than relying on a heuristic score-fusion formula like reciprocal rank
  fusion alone.
- Latency budget allows an additional 50 to 300 milliseconds per query,
  which is the realistic added latency of scoring 20 to 100 candidates with a
  cross-encoder or a hosted rerank API, per Cohere's documented parameters
  including per-document token truncation defaults
  (verified https://docs.cohere.com/reference/rerank, 2026-08-03).

Do not reach for reranking when:

- The first-stage retriever's recall is the actual problem. If the
  correct document is not even in the top 50 candidates the first stage
  returns, no reranker can fix that, because a reranker only reorders what it
  is given. Diagnose recall failures (chunking, embedding model choice,
  query reformulation such as HyDE) before adding a reranking stage. Adding a
  reranker over a broken retriever wastes latency and cost while masking the
  real defect.
- The corpus is small enough to score exhaustively with the expensive
  model in the first place. If you have a few hundred documents, running a
  cross-encoder over the full corpus for every query may be cheaper in
  engineering complexity than standing up a two-stage pipeline, even if it
  costs somewhat more compute.
- The application is latency-critical below roughly 100 milliseconds total
  budget, such as an autocomplete-adjacent feature, where the added
  reranking round trip is not affordable regardless of the quality gain.
- Result order genuinely does not matter to the consumer, for example a
  batch job that ingests every retrieved candidate regardless of rank, or an
  aggregation that sums over all results rather than reading a ranked list.
- You have not yet measured whether the first-stage results are actually
  the bottleneck. Adding a reranker without an evaluation rig that
  measures answer quality or ranking quality before and after is adding
  complexity on faith. This is the single most commonly skipped check before
  teams adopt this pattern.
- The domain has no reranking model trained on data anywhere near its
  distribution, and licensing, latency, or privacy constraints rule out
  fine-tuning one. A general-purpose reranker applied to a highly
  specialized, jargon-dense domain (certain legal or medical corpora) may add
  latency without adding accuracy, and should be evaluated, not assumed.

## 5. Structure

Query. The user's or agent's information need, expressed as text, that
both retrieval stages will be scored against.

First-stage retriever. A cheap, high-recall mechanism, usually a vector
similarity search over an embedding index, a lexical search such as BM25, or
a hybrid of the two combined with reciprocal rank fusion. Its responsibility
is casting a wide net over the full corpus and returning a candidate set,
commonly the top 20 to 200 documents by its own score.

Candidate set. The output of the first stage. an ordered but
imperfectly-ordered list of document identifiers or chunks that the reranker
will now reconsider.

Reranker. A model, usually a cross-encoder transformer or a hosted
listwise reranking API, that reads the query and each candidate document
jointly and produces a relevance score per document. Unlike the first-stage
retriever, the reranker's score is computed fresh for this specific
query-document pairing rather than retrieved from a precomputed index.

Reranked result set. The candidate set reordered by the reranker's
scores, usually truncated to a smaller top-n, for example the top 3 to 10
results, which is what gets passed downstream.

Downstream consumer. The component that actually uses the reranked
results, most often a language model's context window in a RAG pipeline, or a
search results UI presented to a human.

## 6. ASCII structure diagram

```
                         +-----------------------+
      Query  ----------->|   First-stage          |
                         |   retriever            |
                         |  (vector / BM25 / both) |
                         +-----------+------------+
                                     |
                                     v
                         +-----------------------+
                         |   Candidate set        |
                         |   (top 20 to 200,      |
                         |    cheaply ranked)      |
                         +-----------+------------+
                                     |
                    query + each candidate, read jointly
                                     |
                                     v
                         +-----------------------+
                         |   Reranker              |
                         |  (cross-encoder or       |
                         |   hosted rerank API)     |
                         +-----------+------------+
                                     |
                                     v
                         +-----------------------+
                         |   Reranked top-n        |
                         |   (e.g. top 3 to 10)     |
                         +-----------+------------+
                                     |
                                     v
                         +-----------------------+
                         |   Downstream consumer    |
                         |  (LLM context / UI)       |
                         +-----------------------+
```

## 7. Dynamics

At query time, the flow is strictly sequential and synchronous in the common
case. the second stage cannot begin until the first stage's candidate set is
available, because the reranker needs the actual document text to score
against the query.

```
Client            First-stage         Reranker           Consumer
  |    query          retriever           |                  |
  |------------------>   |                |                  |
  |                      | ANN or BM25    |                  |
  |                      | lookup over    |                  |
  |                      | full corpus    |                  |
  |                      |                |                  |
  |                candidate set (N docs) |                  |
  |                      |--------------->|                  |
  |                      |                | score(query, d)  |
  |                      |                | for each d in N  |
  |                      |                | (batched, joint  |
  |                      |                |  encoding)        |
  |                      |                |                  |
  |                      |         reranked top-n            |
  |                      |                |----------------->|
  |                      |                |                  | build prompt
  |                      |                |                  | or render UI
  |<----------------------------------------------------------|
  |                     final response                        |
```

A key runtime detail. the reranker does not score documents independently the
way the first stage's embeddings were precomputed independently. Each score is
computed at request time, for that specific query-document pair, which is
exactly what makes the score more accurate and exactly what makes it too
expensive to run over the whole corpus. Batching the N candidate documents
into a single request to a hosted API, or a single forward pass on a
self-hosted cross-encoder, is standard practice to keep this second stage's
latency bounded. Cohere's Rerank API, for instance, accepts an array of
documents and an optional `top_n` parameter to cap how many reordered results
are returned (verified https://docs.cohere.com/reference/rerank, 2026-08-03).

In an agentic retrieval loop, such as Agentic RAG or Corrective RAG, the
reranked result set is often what the agent inspects before deciding whether
to answer, reformulate the query, or retrieve again, making the reranker's
output the actual decision input for the next step in the loop rather than a
purely cosmetic reordering.

## 8. Implementation variants

Cross-encoder scoring. The dominant approach for self-hosted or
open-model reranking. The query and each candidate document are concatenated
(usually as a CLS token, the query, a SEP token, the document, and a final
SEP token) and passed through a single transformer, which outputs a single
relevance score. This is what sentence-transformers' CrossEncoder class
implements, and the library's own documentation frames the standard workflow
as retrieving roughly 100 candidates cheaply with a bi-encoder, then
rescoring them with a cross-encoder (verified
https://sbert.net/examples/cross_encoder/applications/README.html,
2026-08-03). The cost of this joint encoding, one full transformer pass per
query-document pair, is exactly why it cannot run over an entire corpus.

Hosted listwise or pointwise rerank APIs. Cohere Rerank and comparable hosted rerank providers expose the same conceptual API. Send a query and a
list of documents, receive back relevance scores or a reordered list, without
managing model weights or inference infrastructure. Cohere's v2 API accepts a
model name, a query string, and a documents array, and returns relevance
scores normalized to the range zero to one, per its own reference
documentation (verified https://docs.cohere.com/reference/rerank,
2026-08-03), and includes an optional per-document token truncation setting
that defaults to 4096 tokens, an important operational detail because long
documents that overflow the model's effective context silently degrade
scoring quality.

Late-interaction models, the ColBERT family. A middle ground between
bi-encoders and full cross-encoders. instead of a single vector per document,
a late-interaction model produces token-level embeddings and computes
relevance via a MaxSim operation between query and document token vectors at
query time. This can approach cross-encoder accuracy at lower latency than a
full joint transformer pass, at the cost of a heavier index that stores
per-token rather than per-document vectors.

LLM-as-reranker, listwise prompting. Instead of a purpose-trained
reranking model, a general-purpose large language model is prompted with the
query and a list of candidate documents and asked to output a ranked order or
per-document relevance judgment. This trades a dedicated reranker's speed and
cost predictability for the flexibility and reasoning capacity of a general
model, useful when relevance depends on multi-hop reasoning the reranker
model was never trained for, but is materially slower and more expensive per
query than a purpose-built cross-encoder.

Multi-vector or hybrid fusion reranking. Rather than a single learned
reranker, some pipelines rerank by fusing scores from multiple first-stage
signals, for example combining a BM25 score and a vector similarity score via
reciprocal rank fusion, sometimes followed by a lightweight learned reranker
on top of the fused list. Elasticsearch's text_similarity_reranker retriever
is explicitly designed to compose with reciprocal rank fusion and other
retrievers inside a single declarative search request (verified
https://www.elastic.co/guide/en/elasticsearch/reference/current/semantic-reranking.html,
2026-08-03).

Integrated versus standalone reranking. Some vector database vendors
distinguish between reranking that happens automatically as part of a query
call, called integrated, and reranking invoked as a separate, explicit
operation on an already-retrieved set, called standalone. Pinecone documents
both modes, alongside four hosted reranking models spanning a paid Cohere
model, an open multilingual BGE model, and its own first-party reranker
(verified https://docs.pinecone.io/guides/search/rerank-results,
2026-08-03), which illustrates that the choice of variant is increasingly a
configuration decision rather than an architectural one when using a managed
vector database.

## 9. Known production uses

Cohere Rerank, used across enterprise search and RAG deployments. Cohere
ships a dedicated Rerank API, currently at model version rerank-v4.0-pro per
its own reference documentation, as a second-stage component explicitly
positioned to be dropped into an existing retrieval pipeline regardless of
which first-stage retriever produced the candidates (verified
https://docs.cohere.com/reference/rerank, 2026-08-03).

Pinecone's hosted reranking, integrated into its vector database query
path. Pinecone documents reranking as one of the simplest methods for
improving quality in retrieval augmented generation pipelines and hosts four
rerank models directly, including Cohere's cohere-rerank-4-fast and an open
bge-reranker-v2-m3 multilingual cross-encoder, exposed as both an integrated
query-time option and a standalone API call (verified
https://docs.pinecone.io/guides/search/rerank-results, 2026-08-03).

Elasticsearch's text_similarity_reranker retriever and its RERANK
command in the ES piped query language. Elastic ships semantic reranking as
a first-class retriever type composable inside its own query DSL, noting
that in current versions Elasticsearch only supports cross-encoder models
for semantic reranking, with preconfigured options spanning a Jina AI
endpoint, Elastic's own first-party cross-encoder, and Cohere and Google
Vertex AI inference endpoints (verified
https://www.elastic.co/guide/en/elasticsearch/reference/current/semantic-reranking.html,
2026-08-03).

The MS MARCO passage retrieval leaderboard, the benchmark that
established cross-encoder reranking as state of the art. Nogueira and Cho's
BERT-based passage reranker topped the MS MARCO passage retrieval
leaderboard, outperforming the previous state of the art by 27 percent
relative in MRR at 10, per the paper's own abstract (verified
https://arxiv.org/abs/1901.04085, 2026-08-03), a result widely cited as the
reason cross-encoders became the default architecture for the reranking stage
of modern retrieval pipelines rather than an academic curiosity.

The sentence-transformers CrossEncoder class, used broadly across
open-source RAG tooling. The sentence-transformers library, one of the most
widely adopted open-source embedding and reranking toolkits, ships a
dedicated CrossEncoder class and documents the canonical retrieve-then-rerank
workflow directly, describing the pattern as retrieving about 100 candidates
with a bi-encoder and reranking with a cross-encoder before returning final
results (verified
https://sbert.net/examples/cross_encoder/applications/README.html,
2026-08-03), and this class is the reranking building block many open-source
RAG frameworks wrap rather than reimplementing cross-encoder inference
themselves.

## 10. Consequences

Positive:

- Measurably improves the precision of what a language model or user
  actually sees, by reordering an already-good candidate set with a
  query-aware model rather than a query-independent one.
- Decouples first-stage retrieval speed from final ranking accuracy. the
  corpus-scale search stays cheap and approximate, while the expensive,
  accurate judgment is applied only to a small candidate set.
- Composes cleanly with hybrid retrieval. a reranker gives you a single,
  principled way to merge and reorder results from multiple first-stage
  signals (lexical and vector) rather than hand-tuning a fusion formula.
- Many production rerankers are drop-in as a hosted API call, meaning teams
  can adopt the pattern without training or hosting a model themselves.
- Provides a natural place to enforce business rules or freshness signals
  alongside pure semantic relevance, since the reranking stage already
  reorders a small candidate set and can be composed with additional
  scoring logic.

Negative:

- Adds latency to every query, usually tens to a few hundred
  milliseconds, which compounds in multi-hop agentic pipelines that call
  retrieval more than once.
- Adds cost, either a per-document or per-query fee for a hosted API, or
  GPU or CPU inference infrastructure to self-host.
- Cannot repair poor first-stage recall. a reranker over a bad candidate
  set produces a well-ordered bad answer, which can be more dangerous than
  an obviously bad one because it looks confident.
- Introduces a second model to version, monitor, and evaluate, along with
  a second point of external dependency when the reranker is a hosted API.
- Long documents can silently exceed a reranker's effective input length
  and get truncated, an easy failure mode to miss because it degrades
  quality gradually rather than failing loudly.

## 11. Failure modes and misuse

Symptom. Reranking is added and end-to-end answer quality does not
improve, or the team cannot tell whether it improved.
Cause. No evaluation rig existed before the reranker was added, so
there is no before-and-after baseline to compare against. the team is
reasoning from the general reputation of reranking rather than a measurement
on their own corpus and query distribution.
Fix. Build a small labeled evaluation set of query and relevant document
pairs before adding a reranker, measure a ranking metric such as MRR or
NDCG at the relevant cutoff with and without the reranking stage, and only
keep the stage if it moves the metric on that specific corpus.

Symptom. Correct documents never appear in the final reranked results,
even though the corpus definitely contains them.
Cause. The first-stage retriever's top-k before reranking was set too
small, for example retrieving only the top 5 candidates and reranking those
5, so the correct document was never in the candidate pool the reranker saw.
Fix. Widen the first-stage candidate count, commonly to 20 to 100
documents depending on latency budget, so the reranker has enough recall
headroom to actually find and promote the correct answer.

Symptom. Reranking scores look reasonable in isolation but the final
answers still cite irrelevant passages.
Cause. Long documents were silently truncated by the reranker's per-
document token limit before scoring, so the relevant sentence sat past the
truncation point and the reranker scored an incomplete document.
Fix. Chunk documents to a size well within the reranker's stated per-
document limit before sending them for reranking, rather than relying on the
reranker's own truncation, and verify chunk boundaries do not split the most
relevant sentence away from its surrounding context.

Symptom. Latency spikes intermittently, and the spikes correlate with
larger result sets.
Cause. The reranking stage is scoring the full first-stage candidate set
on every query, even when the query is simple and a smaller candidate count
would have sufficed, and the reranker's per-document cost is being paid
linearly across an unnecessarily large batch.
Fix. Cap the number of candidates sent to the reranker to the smallest
count that maintains acceptable recall in evaluation, and consider caching
reranked results for repeated or near-duplicate queries.

Symptom. The reranker performs worse than the raw first-stage ranking on
a specific class of queries, such as highly technical or jargon-dense
questions.
Cause. The reranking model was trained on a general-domain relevance
distribution that does not match the target domain's vocabulary or notion of
relevance, and no fine-tuning or domain adaptation was applied.
Fix. Evaluate the reranker specifically on the problematic query class
before deploying it broadly, and either select a domain-appropriate reranker,
fine-tune one on domain-labeled data, or exclude that query class from
reranking and fall back to the first-stage ranking for it.

Symptom. The reranking stage becomes a single point of failure. when the
hosted rerank API is slow or unavailable, the whole retrieval pipeline stalls
or errors.
Cause. No fallback path exists if the reranker call fails or times out,
so an external dependency became a hard dependency for the entire pipeline.
Fix. Treat the reranking call like any other external service call. set
a timeout, and on failure or timeout fall back to returning the first-stage
ranking unreranked rather than failing the whole request.

## 12. Trade-off matrix

| Dimension | Reranking (two-stage) | Cross-encoder over the full corpus | RAG without reranking | HyDE (query rewriting) alone |
|---|---|---|---|---|
| Query latency at high volume | Moderate, bounded by candidate count not corpus size | Prohibitive beyond a small corpus | Lowest, single retrieval pass | Adds one extra LLM call before retrieval, no second scoring pass |
| Precision of top results | High, query-aware joint scoring on the shortlist | Highest possible, but usually infeasible to run | Bounded by embedding similarity alone | Improves recall for vague queries, does not reorder the candidate set itself |
| Corpus scalability | Scales to large corpora, cost grows only with candidate count | Does not scale past small corpora | Scales well, standard ANN index | Scales as well as the underlying retriever |
| Operational surface | Adds a second model or API to run and monitor | Not applicable, generally impractical | Lowest, one retrieval component | Adds one LLM call, no new scoring infrastructure |
| Failure mode if misused | Well-ordered wrong answers if first-stage recall is broken | Not applicable | Relevant document buried at a low rank | Reformulated query can drift from user intent |
| Best combined with | Hybrid retrieval, agentic loops that re-query on low confidence | Rarely used alone in production | Any first-stage retriever as the baseline it upgrades | Reranking, as a recall booster feeding a reranked shortlist |

## 13. Related and incompatible patterns

Retrieval-Augmented Generation. Reranking is almost always a stage
inside a larger RAG pipeline, sitting between the retrieval step and the
generation step, improving the relevance of the context the generation step
receives.

Advanced RAG. Treats reranking as one of several standard optimization
stages, alongside query rewriting and chunk optimization, layered onto a
baseline RAG pipeline. reranking is usually the stage advanced RAG
architectures add first because it composes with almost any first-stage
retriever without changing the retriever itself.

HyDE, Hypothetical Document Embeddings. Solves a different half of the
same overall problem. HyDE improves first-stage recall by generating a
hypothetical answer to embed and search with, so that vague or
underspecified queries retrieve better candidates in the first place.
Reranking then improves precision on whatever candidate set the first stage,
HyDE-assisted or not, produces. The two compose naturally. HyDE widens what
gets retrieved, reranking sharpens the order of what was retrieved.

Agentic RAG and Corrective RAG. Both build a decision loop on top of
retrieval, often inspecting reranked scores to decide whether the retrieved
context is good enough to answer with, needs a broader search, or needs the
query reformulated. Reranking's output confidence scores are frequently the
concrete signal these agentic loops branch on.

Self-RAG. Uses reflection tokens generated by the language model itself
to judge retrieval relevance and answer support, which is a related but
distinct mechanism from an external reranker model. the two are not
mutually exclusive. a system can use an external reranker for the
first-pass reordering and still have the language model self-critique the
final selection.

Reranking has no genuinely incompatible pattern in this family. it is
additive to essentially any retrieval architecture, because it operates
strictly on the output of whatever retrieval mechanism precedes it and does
not require changes to that mechanism's internals.

## 14. Refactoring path in and out

Introducing reranking into an existing retrieval pipeline.

1. Establish a labeled evaluation set of representative queries with known
   relevant documents, and measure the current first-stage-only ranking
   quality (MRR, NDCG, or a task-specific answer-quality metric) as a
   baseline. Do this before writing any reranking code.
2. Widen the first-stage retriever's top-k to a candidate count large
   enough to give a reranker recall headroom, commonly 20 to 100, and
   confirm this widening alone does not already solve the problem by
   simply presenting more candidates downstream.
3. Add the reranking call as a discrete stage between retrieval and
   generation, initially behind a feature flag so it can be toggled off
   without a redeploy.
4. Cap the reranker's output to the top-n that will actually be passed
   downstream, tuned to the consumer's context budget.
5. Re-measure the evaluation metric with reranking enabled. keep the stage
   only if it demonstrably improves the metric. if it does not, the
   likely cause is insufficient first-stage recall, per dimension 11, and
   the fix belongs in the first stage, not in choosing a different
   reranker.
6. Add a timeout and fallback path so a reranker failure degrades to the
   unranked first-stage results rather than failing the request.

Removing a reranking stage once it stops earning its place.

1. Confirm with the same evaluation rig used to introduce it that the
   quality delta the reranker was providing has genuinely disappeared, for
   example because the underlying embedding model was upgraded and now
   provides comparably precise first-stage ordering on its own.
2. Remove the reranking call and its feature flag, but keep the widened
   first-stage top-k if downstream logic, such as an agentic loop, still
   benefits from a larger candidate pool for its own reasoning, even
   without a dedicated reranking pass.
3. Re-measure after removal to confirm no regression, since removing a
   component that was providing an unmeasured but real benefit is exactly
   the kind of quiet regression this pattern's own dimension 11 warns
   against for the opposite direction.

## 15. Testing and verification

Testing a reranking stage is easier in one specific way and harder in
another. it is easier because the reranker is a pure function from a query
and a document list to a scored, reordered list, which makes it
straightforward to unit test with fixed inputs and golden expected orderings
for a small, hand-curated set of query-document pairs. It is harder because
the metric that actually matters, whether the reordering improves real
answer quality or user satisfaction, requires a labeled relevance evaluation
set and an information-retrieval metric, not a simple assertion.

Concretely test:

- Unit level. Given a fixed query and a small fixed candidate list with
  a known most-relevant document, assert the reranker places that document
  at or near rank one. This catches integration bugs, such as a wrong model,
  a malformed request, or a wrong field mapping, without needing a large
  evaluation set.
- Contract level. Assert the reranker's response shape matches what
  downstream code expects, including handling an empty candidate list, a
  single-candidate list, and a list exceeding the reranker's stated
  maximum document count or per-document token limit, since a common
  production bug is an unhandled edge case at the input boundary rather
  than a scoring quality problem.
- Ranking quality level. Maintain a labeled evaluation set of query and
  relevant document id pairs representative of production traffic
  and compute MRR or NDCG at a fixed cutoff, both with and without
  reranking enabled, as part of CI or a scheduled evaluation job, so a
  model version upgrade or configuration change that silently degrades
  quality is caught before it reaches production.
- Resilience level. Test that a reranker timeout or error response
  falls back to the unranked first-stage results rather than propagating
  the failure to the end user, per the fix described in dimension 11.
- Latency level. Include the reranking stage in load and latency
  testing with realistic candidate-set sizes, since reranker latency
  scales with the number of candidates and this is easy to miss when
  testing with small development-scale candidate lists.

The technique that becomes easier to test because of this pattern is
isolating relevance quality from generation quality. a RAG pipeline without
a distinct reranking stage conflates whether retrieval found the right
document with whether the language model wrote a good answer into a single
end-to-end metric, whereas a reranking stage gives you an intermediate,
independently testable checkpoint.

## 16. Observability signals

Log and measure, at minimum:

- The reranker's latency per query, separated from first-stage retrieval
  latency and from generation latency, so a regression can be attributed
  to the correct stage rather than showing up only as a vague end-to-end
  slowdown.
- The candidate count sent into the reranker and the count returned, to
  catch silent misconfiguration such as an accidentally small top-k that
  starves the reranker of recall headroom.
- The distribution of relevance scores the reranker returns, watched over
  time. a sudden shift in the score distribution, for example scores
  clustering near zero across most queries, is a strong signal something
  upstream changed, such as a chunking strategy or embedding model swap
  that broke the assumptions the reranker or its integration were tuned
  against.
- The rank position of any document a downstream evaluation or user
  feedback signal marks as correct, tracked over time as a ranking
  quality metric such as MRR at the served cutoff, rather than only as a
  binary hit or miss.
- Reranker error and timeout rates, and whether the fallback path, serving
  unranked first-stage results, was triggered, since a silently
  degrading fallback that never gets fixed is worse than a loud failure.
- Per-document token truncation counts, when the reranker or its API
  reports them, since silent truncation, per dimension 8's note on
  Cohere's default 4096-token per-document cap, is a common source of
  quality degradation that produces no error and no obvious log signal
  unless it is specifically instrumented.

A healthy instance on a dashboard looks like stable latency within budget,
a relevance-score distribution consistent with historical baselines, a
fallback trigger rate near zero, and a ranking quality metric that is flat
or improving over time. A failing instance shows either a latency spike
correlated with candidate-set size growth, a relevance-score distribution
collapsing toward a narrow band, or a rising fallback trigger rate
indicating the reranker dependency is degrading.

## 17. Security and privacy implications

The reranking stage's most direct privacy implication is data exposure to a
third party when using a hosted rerank API. the full text of every candidate
document, not only the query, is sent to the reranking service to be scored,
which means any sensitive or regulated content present in retrieval
candidates, such as personal data, proprietary text, or confidential
business documents, leaves the boundary of the system and is processed by
the reranker vendor. This is a materially larger data-exposure surface than
a first-stage vector search alone, because vector search sends only a query
embedding externally if using a hosted vector database, whereas reranking
sends the actual document text of every candidate for every query. Teams
operating under data residency, confidentiality, or regulatory constraints
should evaluate whether a self-hosted cross-encoder is required rather than
a hosted API, and confirm the hosted vendor's data retention and processing
terms if a hosted option is used regardless.

A secondary implication is prompt injection surface in agentic pipelines
that feed reranked results directly into further LLM reasoning without
sanitization. because reranking does not filter or sanitize document
content, a malicious or adversarial document in the corpus that scores
highly could carry injected instructions into a downstream language model
step. this risk exists in the underlying retrieval pipeline regardless of
reranking, but reranking's job of promoting the most convincingly relevant
content to the top can make an adversarial document more likely to be
selected if the attacker crafted it to score well against likely queries.
This is an analytical concern rather than a documented incident in the
sources reviewed for this entry, and is stated here as engineering
judgment, not as a sourced claim.

Where reranking is silent. it introduces no new authentication, encryption,
or access-control mechanism of its own, and relies entirely on whatever
access controls already govern which documents reach the first-stage
candidate set. Reranking does not filter documents a user should not have
access to. that access control must happen before or alongside retrieval,
not as a side effect of reranking.

## 18. References

1. Rodrigo Nogueira and Kyunghyun Cho. "Passage Re-ranking with BERT."
   arXiv preprint 1901.04085, submitted January 13, 2019.
   https://arxiv.org/abs/1901.04085. Verified 2026-08-03.
2. Cohere. "Rerank API v2 reference documentation."
   https://docs.cohere.com/reference/rerank. Verified 2026-08-03.
3. UKP Lab. "Cross-Encoders, applications and the retrieve and re-rank
   workflow." sentence-transformers documentation.
   https://sbert.net/examples/cross_encoder/applications/README.html.
   Verified 2026-08-03.
4. Pinecone. "Rerank results guide, hosted rerank models."
   https://docs.pinecone.io/guides/search/rerank-results. Verified
   2026-08-03.
5. Elastic. "Semantic reranking, the text_similarity_reranker retriever and
   the ES|QL RERANK command."
   https://www.elastic.co/guide/en/elasticsearch/reference/current/semantic-reranking.html.
   Verified 2026-08-03.

## Code

Working reranking pipelines in four languages. Each implements the same
shape, a cheap first-stage retriever narrows a corpus, then a reranker
scores the narrowed candidates jointly with the query and returns the
top-n. The scoring function is a stand-in for a real cross-encoder or a
hosted rerank API call, isolating the pipeline shape from any specific
model. All four compile and run as shown.

### Python

```python
"""Two-stage retrieval. a cheap first-stage retriever narrows a corpus,
then a reranker scores the candidates jointly with the query."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Sequence


@dataclass(frozen=True)
class Document:
    doc_id: str
    text: str


@dataclass(frozen=True)
class ScoredDocument:
    doc_id: str
    score: float


def first_stage_retrieve(
    query: str, corpus: Sequence[Document], top_k: int
) -> list[Document]:
    """Cheap lexical overlap stand-in for a vector similarity search."""
    query_terms = set(query.lower().split())

    def overlap(doc: Document) -> float:
        doc_terms = set(doc.text.lower().split())
        if not doc_terms:
            return 0.0
        return len(query_terms & doc_terms) / len(doc_terms | query_terms)

    ranked = sorted(corpus, key=overlap, reverse=True)
    return ranked[:top_k]


def rerank(
    query: str,
    candidates: Sequence[Document],
    score_fn: Callable[[str, str], float],
    top_n: int,
) -> list[ScoredDocument]:
    """Score each candidate jointly with the query, then sort by score.

    score_fn stands in for a cross-encoder or a hosted rerank API call.
    It reads the query and one document together, unlike the first-stage
    retriever which never sees the two together.
    """
    scored = [
        ScoredDocument(doc_id=c.doc_id, score=score_fn(query, c.text))
        for c in candidates
    ]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored[:top_n]


def cross_encoder_stub(query: str, document: str) -> float:
    """A joint query-document scorer standing in for a real cross-encoder.

    A real implementation would run the concatenated pair through a
    transformer. This stub rewards exact phrase containment, which a
    query-independent vector score cannot express.
    """
    q = query.lower()
    d = document.lower()
    if q in d:
        return 1.0
    shared = set(q.split()) & set(d.split())
    return len(shared) / max(len(q.split()), 1)


def search(query: str, corpus: Sequence[Document]) -> list[ScoredDocument]:
    candidates = first_stage_retrieve(query, corpus, top_k=20)
    return rerank(query, candidates, cross_encoder_stub, top_n=3)


if __name__ == "__main__":
    corpus = [
        Document("d1", "reranking improves precision of retrieved passages"),
        Document("d2", "vector databases store embeddings for similarity search"),
        Document("d3", "cross encoder models score a query and document jointly"),
        Document("d4", "reranking sorts candidates by a query aware relevance score"),
    ]
    results = search("reranking sorts candidates by relevance", corpus)
    for r in results:
        print(r.doc_id, round(r.score, 3))
```

### TypeScript

```typescript
// Two-stage retrieval with a bounded, timeout-guarded rerank call.
// A failed or slow reranker falls back to the first-stage order,
// per the resilience failure mode in this entry's dimension 11.

interface CandidateDoc {
  id: string;
  text: string;
}

interface ScoredDoc {
  id: string;
  score: number;
}

async function withTimeout<T>(p: Promise<T>, ms: number, fallback: T): Promise<T> {
  return Promise.race([
    p,
    new Promise<T>((resolve) => setTimeout(() => resolve(fallback), ms)),
  ]);
}

type RerankFn = (query: string, docs: CandidateDoc[]) => Promise<ScoredDoc[]>;

async function rerankWithFallback(
  query: string,
  candidates: CandidateDoc[],
  rerankFn: RerankFn,
  topN: number,
  timeoutMs: number
): Promise<ScoredDoc[]> {
  const unranked: ScoredDoc[] = candidates.map((c, i) => ({
    id: c.id,
    score: 1 - i / candidates.length,
  }));

  const reranked = await withTimeout(
    rerankFn(query, candidates).catch(() => unranked),
    timeoutMs,
    unranked
  );

  return reranked.slice(0, topN);
}

async function stubRerankApi(query: string, docs: CandidateDoc[]): Promise<ScoredDoc[]> {
  const q = query.toLowerCase();
  const scored = docs.map((d) => {
    const text = d.text.toLowerCase();
    const overlap = text.includes(q) ? 1 : 0.2;
    return { id: d.id, score: overlap };
  });
  return scored.sort((a, b) => b.score - a.score);
}

async function main(): Promise<void> {
  const query = "reranking improves precision";
  const candidates: CandidateDoc[] = [
    { id: "d1", text: "vector search returns approximate neighbors" },
    { id: "d2", text: "reranking improves precision of the top results" },
    { id: "d3", text: "bm25 counts term overlap between query and document" },
  ];

  const results = await rerankWithFallback(query, candidates, stubRerankApi, 2, 250);
  for (const r of results) {
    console.log(r.id, r.score.toFixed(3));
  }
}

main();
```

### Go

```go
// Package main shows a batched rerank call over a first-stage candidate
// set, scoring every candidate in one round trip the way a hosted rerank
// API batches documents into a single request.
package main

import (
	"fmt"
	"sort"
	"strings"
)

type document struct {
	id   string
	text string
}

type scoredDoc struct {
	id    string
	score float64
}

func firstStageRetrieve(query string, corpus []document, topK int) []document {
	queryTerms := termSet(query)
	scored := make([]scoredDoc, len(corpus))
	for i, d := range corpus {
		scored[i] = scoredDoc{id: d.id, score: overlap(queryTerms, termSet(d.text))}
	}
	sort.Slice(scored, func(a, b int) bool { return scored[a].score > scored[b].score })

	byID := make(map[string]document, len(corpus))
	for _, d := range corpus {
		byID[d.id] = d
	}
	out := make([]document, 0, topK)
	for _, s := range scored {
		if len(out) == topK {
			break
		}
		out = append(out, byID[s.id])
	}
	return out
}

func rerank(query string, candidates []document, scoreFn func(string, string) float64, topN int) []scoredDoc {
	scored := make([]scoredDoc, len(candidates))
	for i, c := range candidates {
		scored[i] = scoredDoc{id: c.id, score: scoreFn(query, c.text)}
	}
	sort.Slice(scored, func(a, b int) bool { return scored[a].score > scored[b].score })
	if topN > len(scored) {
		topN = len(scored)
	}
	return scored[:topN]
}

func crossEncoderStub(query, doc string) float64 {
	q := strings.ToLower(query)
	d := strings.ToLower(doc)
	if strings.Contains(d, q) {
		return 1.0
	}
	shared := len(termSet(q).intersect(termSet(d)))
	total := len(query)
	if total == 0 {
		return 0
	}
	return float64(shared) / float64(total)
}

type set map[string]struct{}

func termSet(s string) set {
	out := set{}
	for _, t := range strings.Fields(strings.ToLower(s)) {
		out[t] = struct{}{}
	}
	return out
}

func (a set) intersect(b set) set {
	out := set{}
	for k := range a {
		if _, ok := b[k]; ok {
			out[k] = struct{}{}
		}
	}
	return out
}

func overlap(a, b set) float64 {
	inter := len(a.intersect(b))
	if len(b) == 0 {
		return 0
	}
	return float64(inter) / float64(len(b))
}

func main() {
	corpus := []document{
		{"d1", "vector search returns approximate neighbors quickly"},
		{"d2", "reranking scores each candidate jointly with the query"},
		{"d3", "bm25 counts term overlap between a query and a document"},
	}
	query := "reranking scores each candidate jointly"

	candidates := firstStageRetrieve(query, corpus, 3)
	results := rerank(query, candidates, crossEncoderStub, 2)
	for _, r := range results {
		fmt.Printf("%s %.3f\n", r.id, r.score)
	}
}
```

### Rust

```rust
// A reranker trait lets the scoring implementation vary (a local
// cross-encoder, a hosted API client, a test double) while the pipeline
// shape, retrieve then rerank, stays fixed.
use std::collections::HashSet;

#[derive(Clone)]
struct DocumentRec {
    id: String,
    text: String,
}

#[derive(Debug)]
struct ScoredDoc {
    id: String,
    score: f64,
}

trait Reranker {
    fn score(&self, query: &str, document: &str) -> f64;
}

struct CrossEncoderStub;

impl Reranker for CrossEncoderStub {
    fn score(&self, query: &str, document: &str) -> f64 {
        let q = query.to_lowercase();
        let d = document.to_lowercase();
        if d.contains(&q) {
            return 1.0;
        }
        let q_terms: HashSet<&str> = q.split_whitespace().collect();
        let d_terms: HashSet<&str> = d.split_whitespace().collect();
        let shared = q_terms.intersection(&d_terms).count();
        shared as f64 / q_terms.len().max(1) as f64
    }
}

fn first_stage_retrieve(query: &str, corpus: &[DocumentRec], top_k: usize) -> Vec<DocumentRec> {
    let query_lower = query.to_lowercase();
    let q_terms: HashSet<&str> = query_lower.split_whitespace().collect();
    let mut scored: Vec<(f64, &DocumentRec)> = corpus
        .iter()
        .map(|d| {
            let text_lower = d.text.to_lowercase();
            let owned: HashSet<&str> = text_lower.split_whitespace().collect();
            let overlap = q_terms.iter().filter(|t| owned.contains(*t)).count();
            (overlap as f64 / owned.len().max(1) as f64, d)
        })
        .collect();
    scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());
    scored.into_iter().take(top_k).map(|(_, d)| d.clone()).collect()
}

fn rerank(
    query: &str,
    candidates: &[DocumentRec],
    reranker: &dyn Reranker,
    top_n: usize,
) -> Vec<ScoredDoc> {
    let mut scored: Vec<ScoredDoc> = candidates
        .iter()
        .map(|c| ScoredDoc {
            id: c.id.clone(),
            score: reranker.score(query, &c.text),
        })
        .collect();
    scored.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
    scored.truncate(top_n);
    scored
}

fn main() {
    let corpus = vec![
        DocumentRec { id: "d1".into(), text: "vector search returns approximate neighbors".into() },
        DocumentRec { id: "d2".into(), text: "reranking scores each candidate with the query".into() },
        DocumentRec { id: "d3".into(), text: "bm25 counts term overlap in a document".into() },
    ];
    let query = "reranking scores each candidate";

    let candidates = first_stage_retrieve(query, &corpus, 3);
    let reranker = CrossEncoderStub;
    let results = rerank(query, &candidates, &reranker, 2);

    for r in &results {
        println!("{} {:.3}", r.id, r.score);
    }
}
```
