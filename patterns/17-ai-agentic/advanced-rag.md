---
name: Advanced RAG
slug: advanced-rag
family: 17-ai-agentic
category: AI Agentic
aliases: [Modular RAG, Multi-Stage RAG, RAG Pipeline Pattern]
first_described: "Gao, Xiong, Gao, Jia, Pan, Bi, Dai, Sun, Wang, Wang 2023"
maturity: established
related: [retrieval-augmented-generation, routing, evaluator-optimizer, reflexion, react, chain-of-responsibility, orchestrator-worker]
incompatible_with: []
verified: 2026-08-02
---

# Advanced RAG

## 1. Name, aliases, and lineage

The canonical name is Advanced RAG. It is defined, alongside Naive RAG and
Modular RAG, in Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan,
Yuxi Bi, Yi Dai, Jiawei Sun, Meng Wang, and Haofen Wang, "Retrieval-Augmented
Generation for Large Language Models. A Survey," first submitted 18 December
2023 with a final revision 27 March 2024, https://arxiv.org/abs/2312.10997
(verified 2026-08-02). The abstract states that the paper "offers a detailed
examination of the progression of RAG paradigms, encompassing the Naive RAG,
the Advanced RAG, and the Modular RAG."

The survey's own three-stage taxonomy is the reference point for the name.

- **Naive RAG.** Embed, index, retrieve top-k by vector similarity, stuff the
  chunks into a prompt, generate. One retrieval call, no query transformation,
  no reranking. This is the base pattern, documented separately in this
  catalog as Retrieval Augmented Generation.
- **Advanced RAG.** The survey's own framing is retrieval quality improved by
  operating on the pipeline before and after the retrieval call itself, what
  it calls pre-retrieval and post-retrieval processes, without changing the
  fundamental retrieve-then-generate shape.
- **Modular RAG.** Further decomposition into interchangeable, independently
  swappable modules (routing modules, memory modules, fusion modules), often
  arranged as a graph rather than a fixed pipeline. Advanced RAG is the
  intermediate rung, and in practice the modules the survey assigns to
  Modular RAG (query routing, iterative retrieval, adaptive retrieval) are
  the same techniques most production teams describe when they say "advanced
  RAG," so this entry treats the pipeline-of-stages shape as the defining
  structure and treats the individual techniques as implementation variants
  rather than forcing a hard line between the survey's second and third
  categories. Where a technique requires a genuinely dynamic, agent-directed
  control flow rather than a fixed sequence of stages, that is Agentic RAG,
  covered as a variant below and cross-referenced against the ReAct and
  Orchestrator-Worker entries in this catalog.

No single earlier paper claims the name. The pattern is a convergence of five
separately published techniques (query rewriting, hybrid search, reranking,
iterative or corrective retrieval, and hierarchical indexing) that practitioner
literature and the Gao et al. survey then collected under one label once teams
running Naive RAG in production hit the same wall at the same time, roughly
mid-2023 to early 2024.

## 2. Problem and context

Naive RAG treats "find the k nearest vectors to this query's embedding" as if
it were the same question as "find the passages that actually let the model
answer this question correctly." The two questions diverge in five specific,
observable ways once a system leaves a demo and meets a real corpus and real
queries.

First, a user's literal question is frequently a poor embedding target. "What
changed in the Q3 pricing" embeds close to other sentences that mention
pricing and Q3, not necessarily close to the paragraph that states the actual
delta, because the delta paragraph might read "the enterprise tier moved from
forty to fifty five dollars per seat" with no restatement of the word
"changed." Second, a single query vector cannot cover a multi-part or
multi-hop question. "Which supplier missed the deadline that caused the
March recall" needs one retrieval for the recall record and a second
retrieval for the supplier record it names, and a single top-k dense lookup
returns neither reliably because the query embedding is a blend that is close
to nothing. Third, dense retrieval alone is weak on exact terms, product
codes, error strings, legal citations, person names. A dense encoder trained
on semantic similarity routinely ranks a paraphrase above the literal string
match a lawyer or an engineer actually needs, because the embedding space was
never optimized to distinguish "invoice number 48291" from "invoice number
48219." Fourth, cosine similarity to a query is not the same signal as
usefulness for answering that query, so the top-k list frequently contains
near-duplicates and only-tangentially-relevant chunks crowding out the one
chunk that matters, and the generator then either dilutes its answer across
all of them or, per the well documented "lost in the middle" effect,
under-weights the correct passage because it sits in the middle of a long
context (Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele
Bevilacqua, Fabio Petroni, Percy Liang, "Lost in the Middle. How Language
Models Use Long Contexts," Transactions of the Association for Computational
Linguistics, 2024, https://arxiv.org/abs/2307.03172, verified 2026-08-02).
Fifth, and cheapest to fix but most commonly skipped, a fixed-size chunker
severs a chunk from the surrounding text that gave it meaning, so a chunk
that says "the company reduced headcount by twelve percent in that division"
retrieves perfectly on a vector search but answers nothing once it is
isolated from the sentence three chunks earlier that names which company and
which division.

The context in which Advanced RAG is the right answer, rather than a bigger
context window or a fine-tuned model, is this. The corpus is large enough, or
changes often enough, that stuffing it whole into a context window is not
viable, retrieval precision measurably degrades answer quality (hallucination,
missed facts, wrong citations), and the team can afford the added latency and
engineering surface of a multi-stage pipeline in exchange for that quality.

## 3. Forces

Judgement. The weighting below reflects how these forces trade against each
other in production RAG systems rather than a formula from a paper.

- **Retrieval precision versus recall.** A reranker sharply improves
  precision at the top of the list, at the cost of first casting a wider net
  (retrieving more candidates than will be shown) which raises the recall
  floor the reranker depends on. Advanced RAG almost always widens first-pass
  recall and narrows it back down with a second stage, rather than trying to
  get precision right in one shot.
- **Latency versus answer quality.** Every added stage, query rewriting,
  hybrid fusion, reranking, a corrective retry loop, is an additional
  sequential hop, and several of them (HyDE, query decomposition, corrective
  retrieval) are themselves an additional LLM call before the generation
  call. A pipeline that improves accuracy by two points at four times the
  p50 latency is frequently the wrong trade for a chat product and the right
  trade for an overnight batch job or a compliance research tool.
- **Cost versus quality.** Cross-encoder reranking, HyDE's hypothetical
  document generation, and contextual chunk annotation each spend model
  tokens or a dedicated model call per query or per document. Anthropic's own
  published numbers on Contextual Retrieval show the annotation cost at
  roughly one dollar and two cents per million document tokens once prompt
  caching is used (Anthropic, "Introducing Contextual Retrieval," 19
  September 2024, https://www.anthropic.com/news/contextual-retrieval,
  verified 2026-08-02), which is a real, budgetable cost that a naive
  per-chunk call without caching would multiply.
- **Index build complexity versus query-time simplicity.** RAPTOR and
  GraphRAG push cost into an offline indexing phase (clustering and
  summarizing, or extracting an entity graph and pregenerating community
  summaries) so that query time stays close to a single lookup. This is a
  real trade, not a free lunch. The index build is itself an LLM-heavy batch
  job that has to be rerun, in whole or in part, as the corpus changes.
- **Determinism and debuggability versus adaptiveness.** A fixed five-stage
  pipeline is easy to test stage by stage. A corrective or self-reflective
  loop (CRAG, Self-RAG) that decides at runtime whether to retry, retrieve
  more broadly, or fall back to web search is harder to reason about and
  harder to bound. It needs an explicit retry cap or it degrades into
  unbounded added latency on hard queries.
- **Freshness versus pre-computation.** Query rewriting and reranking operate
  per query and see fresh data immediately. RAPTOR's tree and GraphRAG's
  entity graph are computed ahead of time and go stale as the corpus grows,
  which forces a decision between expensive full reindexing and accepting a
  staleness window.

## 4. Applicability and non-applicability

When to reach for Advanced RAG.

- The corpus is large or heterogeneous enough (multiple document types, mixed
  structured and unstructured content, or more than roughly a few hundred
  thousand tokens) that a single dense top-k retrieval measurably misses
  relevant passages.
- Queries are frequently multi-hop, comparative, or aggregative, requiring
  information assembled from more than one location in the corpus.
- The corpus contains exact identifiers, codes, names, or numbers that a
  purely dense embedding space ranks unreliably against.
- Answer correctness and citation accuracy are load-bearing (legal, medical,
  financial, compliance, internal knowledge base for support agents) and the
  cost of a wrong or unsupported answer exceeds the cost of the extra
  pipeline stages.
- The team already operates Naive RAG in production and has a labelled or
  even lightly labelled evaluation set that shows a specific, measured
  retrieval failure mode (low recall, low precision, multi-hop misses) that
  a specific advanced technique addresses.

When NOT to reach for it, with the reason.

- The corpus fits comfortably in the model's context window and the whole
  document, or the whole relevant subset, can simply be included every
  request. Modern long-context models make this competitive with retrieval
  for small-to-medium corpora, and it removes the entire retrieval failure
  surface at the cost of per-request token spend. Measure both before
  choosing.
- The application is latency-sensitive (sub-second, conversational) and Naive
  RAG's single retrieval call already meets the accuracy bar on the actual
  evaluation set. Adding stages to fix a problem that has not been measured
  is engineering for its own sake.
- The task does not need external knowledge at all. Pure reasoning,
  arithmetic, code generation from a fully specified spec, or creative
  writing gain nothing from retrieval and only inherit its latency and
  failure modes.
- The corpus is small (a handful of documents, a single FAQ) where a linear
  keyword or grep-style search already achieves near-perfect recall and
  precision, and a vector index plus reranker is added complexity with no
  measurable gain.
- The team has no evaluation set at all. Adding query rewriting, hybrid search,
  and reranking without a way to measure whether each stage helps is a
  guaranteed source of unaccountable regressions, because these stages
  interact and a change to one can silently degrade another.
- The requirement is a live, single, authoritative fact that changes
  constantly (today's stock price, current weather) rather than a durable
  document corpus. That is a tool call or a direct API lookup, not a
  retrieval pipeline over an index.

## 5. Structure

Advanced RAG generalises the Naive RAG participant list into three phases,
each with participants that Naive RAG omits.

Pre-retrieval participants.

- **Query Transformer.** Rewrites, expands, decomposes, or hallucinates
  around the raw user query before it is used for retrieval. Concrete
  variants, HyDE (generates a hypothetical answer document and embeds that
  instead of the query), multi-query expansion (generates several
  reformulations and retrieves for each), and query decomposition (splits a
  multi-hop question into sub-questions retrieved independently).
- **Router.** Decides which index, retriever, or knowledge source a given
  query should go to, when the system has more than one (a vector index, a
  keyword index, a SQL database, a graph index). This role is identical to
  the Routing pattern documented elsewhere in this catalog, specialised to
  retrieval sources.

Retrieval participants.

- **Sparse Retriever.** A lexical index (BM25 or a learned sparse method)
  that scores exact and near-exact term overlap. Strong on identifiers,
  codes, and rare terms, weak on paraphrase and synonymy.
- **Dense Retriever.** A vector index over embeddings, strong on semantic
  and paraphrase similarity, weak on exact string and rare-term matching.
- **Fusion module.** Combines the ranked lists from multiple retrievers,
  typically with Reciprocal Rank Fusion, into one candidate list before
  reranking.
- **Graph or hierarchical index.** In GraphRAG and RAPTOR variants, an
  offline-built structure (an entity graph with community summaries, or a
  cluster tree with recursive summaries) that the retrieval step queries
  instead of, or in addition to, a flat chunk index.

Post-retrieval participants.

- **Reranker.** A cross-encoder or LLM-based scorer that re-orders the fused
  candidate list by relevance to the original query, at a cost per candidate
  that a first-pass bi-encoder retriever does not pay, because it scores the
  query and each candidate jointly rather than comparing precomputed vectors.
- **Context Compressor or Selector.** Trims, deduplicates, or summarizes the
  reranked candidates down to what actually fits the generation budget,
  removing near-duplicates and irrelevant spans the reranker still let
  through.
- **Critic or Corrective Evaluator.** Present in CRAG and Self-RAG variants.
  Scores whether the retrieved set is actually sufficient and either
  triggers a broader retrieval, a web search fallback, or a retry with a
  rewritten query, before generation proceeds.

Generation participant.

- **Generator.** The language model that consumes the final selected context
  and the (possibly transformed) query and produces the answer, ideally with
  citations back to the specific chunks used.

## 6. ASCII structure diagram

```
                    +-------------------+
   user query ----->|  Query            |
                    |  Transformer      |   HyDE / decompose / expand
                    +---------+---------+
                              |
                    +---------v---------+
                    |     Router        |   which index(es) to hit
                    +----+---------+----+
                         |         |
              +----------v--+   +--v----------+
              |   Sparse    |   |   Dense     |
              |   Retriever |   |   Retriever |   (or Graph / RAPTOR index)
              +----------+--+   +--+----------+
                         |         |
                    +----v---------v----+
                    |   Fusion (RRF)    |
                    +---------+---------+
                              |
                    +---------v---------+
                    |     Reranker      |   cross-encoder / LLM scorer
                    +---------+---------+
                              |
                    +---------v---------+
                    | Context Compressor|
                    +---------+---------+
                              |
                    +---------v---------+
                    |  Critic / CRAG    |---- insufficient --> web search
                    |  (optional)       |             or broader retrieval
                    +---------+---------+
                              | sufficient
                    +---------v---------+
                    |    Generator      |----> answer + citations
                    +-------------------+
```

## 7. Dynamics

The default sequential run, no corrective branch taken.

```
User query
  -> Query Transformer produces one or more retrieval queries
  -> Router selects retriever(s) (sparse, dense, graph, or a mix)
  -> Sparse and Dense retrievers each return a ranked candidate list
  -> Fusion module merges the lists (Reciprocal Rank Fusion)
  -> Reranker re-scores the merged list against the ORIGINAL user query
  -> Context Compressor trims to the generation token budget
  -> Generator produces the answer, cited against surviving chunks
  -> Answer returned to user
```

The corrective (CRAG-style) branch, taken when the Critic scores retrieval
quality as low.

```
... Fusion module merges the lists
  -> Critic scores the merged list: correct / ambiguous / incorrect

  if correct:
     -> proceed to Reranker as above

  if ambiguous:
     -> Critic's decompose-then-recompose step strips irrelevant spans
        from the retrieved chunks, keeps the salvageable strips
     -> proceed to Reranker with the trimmed set

  if incorrect:
     -> Query Transformer rewrites the query for a web search
     -> a live web search retriever is invoked as a fallback source
     -> results replace, or are merged with, the original candidate set
     -> proceed to Reranker with the new set
```

The Self-RAG variant differs in where the decision lives. Rather than a
separate Critic module scoring a batch of retrieved documents, the Generator
itself is trained to emit reflection tokens (Asai, Wu, Wang, Sil, Hajishirzi,
"Self-RAG. Learning to Retrieve, Generate, and Critique through
Self-Reflection," submitted 17 October 2023, https://arxiv.org/abs/2310.11511,
verified 2026-08-02) inline in its own decoding stream that mark whether
retrieval is needed at all for the current segment, whether a retrieved
passage is relevant, and whether the generated segment is supported by it,
turning the fixed pipeline into a per-segment decision the model makes as it
writes rather than a separate upstream stage.

## 8. Implementation variants

**Hybrid search with Reciprocal Rank Fusion.** Run BM25 and a dense vector
retriever independently against the same query, then combine the two ranked
lists with RRF, which scores each document as the sum of one divided by (a
constant plus its rank) across the lists it appears in, rather than trying to
normalise and compare raw similarity scores from two incompatible scales.
This directly compensates for the exact-match weakness dense retrieval has by
construction, at the cost of running two retrieval systems and maintaining
two indexes over the same corpus.

**Query rewriting and expansion.** The Query Transformer generates one or
more alternative phrasings of the user's question, retrieves for each, and
merges the results, on the premise that a single embedding is a fragile,
single point-of-failure representation of intent. Multi-query expansion is
the cheap version of this (no extra retrieval structure, just more retrieval
calls). Query decomposition is the version aimed specifically at multi-hop
questions, splitting "who reported to the person who signed the March
contract" into "who signed the March contract" then "who reported to that
person" as two dependent retrieval steps.

**HyDE, Hypothetical Document Embeddings.** Gao, Ma, Lin, Callan, "Precise
Zero-Shot Dense Retrieval without Relevance Labels,"
https://arxiv.org/abs/2212.10496 (verified 2026-08-02). Instead of embedding
the user's query directly, an LLM is zero-shot instructed to write a
plausible, possibly entirely fabricated, answer document to the query, and
that hypothetical document's embedding is used to search the real corpus.
The insight the paper states directly is that an answer-shaped piece of text
is closer in embedding space to real answer documents than a question-shaped
query is, and the dense encoder's own compression discards the fabricated
specifics while retaining the topical and stylistic signal that drives
retrieval. This variant fails predictably on queries where the model's
hallucinated hypothetical document is confidently wrong in a way that steers
retrieval toward the wrong topic entirely, covered in dimension 11.

**Reranking with a cross-encoder.** A first-pass retriever (BM25, dense, or
their fusion) returns a wide candidate set, typically fifty to two hundred
documents, cheaply. A cross-encoder or an LLM-based reranker then scores each
query-candidate pair jointly, which is far more accurate than a bi-encoder's
precomputed, independently-embedded comparison but too slow to run over an
entire corpus, so it only ever scores the narrowed candidate set. Cohere's
Rerank API documents this exact placement. Rerank models "sort text inputs by
semantic relevance to a specified query" and "are often used to sort search
results returned from an existing search solution" (Cohere, Rerank
documentation, https://docs.cohere.com/docs/rerank, verified 2026-08-02),
which is the production framing of the reranker's role as a second stage,
never a replacement for first-pass retrieval.

**Corrective RAG, CRAG.** Yan, Gu, Zhu, Ling, "Corrective Retrieval
Augmented Generation," https://arxiv.org/abs/2401.15884 (verified 2026-08-02).
A lightweight evaluator scores retrieved documents as correct, ambiguous, or
incorrect. On ambiguous it runs a decompose-then-recompose step that strips
noise from otherwise partially useful chunks. On incorrect it discards the
retrieval and triggers a large-scale web search as a fallback knowledge
source. This is the variant that makes retrieval quality itself an explicit,
inspectable, and correctable step rather than a silent assumption.

**Self-RAG.** Covered above in dimension 7. The distinguishing engineering
property is that the retrieval decision and the relevance and support
judgements are made by the same model that is generating, inline, via
trained special tokens, rather than by a separate pipeline stage, which
removes one hop of latency at the cost of requiring a model fine-tuned to
emit those tokens rather than any off-the-shelf generator.

**RAPTOR, hierarchical tree retrieval.** Sarthi, Abdullah, Tuli, Khanna,
Goldie, Manning, "RAPTOR. Recursive Abstractive Processing for Tree-Organized
Retrieval," https://arxiv.org/abs/2401.18059 (verified 2026-08-02). Offline,
chunks are recursively embedded, clustered, and summarized bottom-up into a
tree with multiple levels of abstraction, from raw chunks at the leaves to
whole-document summaries at the root. At query time, retrieval pulls from
multiple levels of the tree simultaneously, so a query asking for a
high-level theme can be answered from a summary node while a query asking for
a specific fact is answered from a leaf, without the query author needing to
know in advance which granularity the answer lives at. The paper reports a
twenty percentage point absolute accuracy improvement on the QuALITY
benchmark when RAPTOR retrieval is combined with GPT-4, specifically on
multi-step reasoning questions.

**GraphRAG.** Edge, Trinh, Cheng, Bradley, Chao, Mody, Truitt, Metropolitansky,
Ness, Larson, "From Local to Global. A Graph RAG Approach to Query-Focused
Summarization," https://arxiv.org/abs/2404.16130 (verified 2026-08-02),
implemented as the open-source Microsoft GraphRAG project
(https://github.com/microsoft/graphrag, verified 2026-08-02). Offline, an
LLM extracts an entity knowledge graph from the source documents, then
pregenerates summaries for communities of closely related entities detected
in that graph. At query time, for corpus-wide or thematic questions that
Naive RAG's chunk-level retrieval systematically fails (the paper's stated
target is "query-focused summarization" of an entire corpus, not point
lookups), each relevant community summary produces a partial answer and the
partial answers are consolidated into a final response, giving the system a
form of retrieval that operates over relationships between entities rather
than only over chunk similarity. The GitHub repository states plainly that
"the provided code serves as a demonstration and is not an officially
supported Microsoft offering," which matters for anyone evaluating it for a
production commitment rather than a research prototype.

**Contextual Retrieval.** Anthropic, "Introducing Contextual Retrieval," 19
September 2024, https://www.anthropic.com/news/contextual-retrieval (verified
2026-08-02). Before chunks are embedded or indexed for BM25, an LLM (Claude,
in Anthropic's own implementation) is used to prepend a short, fifty to one
hundred token explanatory annotation to each chunk describing its place in
the source document, directly fixing the context-severing problem named in
dimension 2. Anthropic's own measured numbers, Contextual Embeddings alone
cut retrieval failure from 5.7 percent to 3.7 percent, a 35 percent relative
reduction. Adding Contextual BM25 alongside it brought failure down to 2.9
percent, a 49 percent relative reduction. Adding a reranking stage on top of
both brought failure down to 1.9 percent, a 67 percent relative reduction.
Prompt caching is used to make the per-chunk annotation cost tractable,
quoted at roughly one dollar and two cents per million document tokens
processed.

**Agentic RAG.** Rather than a fixed pipeline, retrieval is exposed to a
language model as one or more callable tools inside an agent loop (see the
ReAct entry in this catalog), and the model decides at each step whether to
retrieve, which query to issue, whether to retrieve again with a refined
query, or whether it already has enough information to answer. This trades
the predictability of a fixed pipeline for the ability to handle queries
whose retrieval needs cannot be known ahead of time, and it composes
naturally with the Orchestrator-Worker pattern when different sub-questions
are dispatched to different retrieval tools or sources.

## 9. Known production uses

- **Anthropic's own Contextual Retrieval implementation**, published with
  the method itself and used as the reference implementation teams building
  on Claude adopt directly, including the specific numeric improvement over
  a Naive RAG baseline described in dimension 8 (Anthropic, "Introducing
  Contextual Retrieval," 19 September 2024,
  https://www.anthropic.com/news/contextual-retrieval, verified 2026-08-02).
- **Microsoft GraphRAG**, an open-source data pipeline maintained by
  Microsoft Research and paired with the published paper cited in dimension
  8, described in its own repository as "a data pipeline and transformation
  suite that is designed to extract meaningful, structured data from
  unstructured text using the power of LLMs" for improving reasoning over
  private, narrative corpora (https://github.com/microsoft/graphrag, verified
  2026-08-02, README and linked Microsoft Research blog post).
- **Cohere's Rerank API**, a standalone commercial reranking endpoint whose
  own documentation frames it explicitly as a second-stage component sitting
  after an existing search or retrieval system, the production packaging of
  the reranker participant described in dimension 5
  (https://docs.cohere.com/docs/rerank, verified 2026-08-02).
- **The RAGAS evaluation framework**, Es, James, Espinosa-Anke, Schockaert,
  "Ragas. Automated Evaluation of Retrieval Augmented Generation," first
  submitted 26 September 2023, https://arxiv.org/abs/2309.15217 (verified
  2026-08-02), a reference-free evaluation library adopted widely enough in
  the RAG tooling ecosystem (integrated into LangChain and LlamaIndex
  evaluation workflows, per the paper's own stated purpose of evaluating
  "the ability of the retrieval system to identify relevant and focused
  context passages") to function as a de facto standard for measuring the
  effect of each Advanced RAG stage described in this entry, which is why it
  is the tool named in dimension 15 rather than an ad hoc metric.

## 10. Consequences

Positive.

- Measurably higher retrieval precision at the top of the candidate list,
  directly reducing the rate at which the generator is handed irrelevant
  context to reason over or hallucinate around.
- Multi-hop and comparative questions become answerable at all, where Naive
  RAG's single top-k lookup structurally cannot assemble information that
  lives in more than one location.
- Exact-match failure on identifiers, codes, and rare terms is largely
  eliminated by adding a sparse retriever to the fusion step, closing a gap
  dense-only retrieval cannot close by tuning k.
- Citation quality improves because the context handed to the generator is
  smaller, more relevant, and less redundant, which makes it easier for the
  model to attribute claims to a specific source chunk.
- Corrective and self-reflective variants add a bounded fallback path (broader
  retrieval, web search) so a genuinely under-covered query degrades to "we
  searched more broadly" instead of a silent, confident wrong answer.

Negative.

- Added latency, compounding across stages. Query transformation, dual
  retrieval, fusion, reranking, and an optional corrective retry each add a
  sequential hop, and several of them are themselves an LLM call rather than
  a cheap lookup.
- Added cost, both in extra model calls per query (HyDE, query rewriting,
  LLM-based reranking) and in offline index build cost (RAPTOR's clustering
  and summarization pass, GraphRAG's entity extraction and community
  summarization pass, both of which reprocess the corpus with an LLM rather
  than a cheap embedding call).
- Substantially more moving parts to test, monitor, and debug. A regression
  can originate in the query transformer, either retriever, the fusion
  weights, the reranker, the compressor, or their interaction, and Naive RAG
  gives none of those a chance to go wrong because there is only one stage.
- Index staleness in the hierarchical and graph variants. RAPTOR's tree and
  GraphRAG's entity graph are computed ahead of time, and a corpus that
  changes daily either needs an expensive full reindex on a schedule or
  accepts answers drawn from a stale index between rebuilds.
- A false sense of correctness. Because the pipeline looks and performs more
  sophisticated, teams sometimes treat its output as more trustworthy than
  Naive RAG's, without the evaluation apparatus in dimension 15 that would
  actually confirm that trust is earned on their specific corpus and query
  distribution.

## 11. Failure modes and misuse

**Symptom.** Retrieval returns confidently plausible but topically wrong
documents after adding HyDE.
**Cause.** The hypothetical document the LLM generated for an out-of-domain
or adversarial query was itself wrong in a specific, confident direction (for
example inventing a plausible-sounding but incorrect technical explanation),
and its embedding pulled real documents from that wrong direction rather than
the right one, because HyDE has no mechanism to detect that its own
hypothetical answer was fabricated nonsense.
**Fix.** Run HyDE's hypothetical-document retrieval in parallel with a direct
query embedding (or a sparse retriever) and fuse the two, rather than
replacing direct retrieval outright, so a bad hypothetical document is
diluted by a parallel retrieval path instead of solely determining the
result.

**Symptom.** p95 latency triples after adding a cross-encoder reranker, with
no complaints about answer quality before the change.
**Cause.** The reranker is scoring too wide a candidate set. Cross-encoder
cost scales linearly with the number of query-candidate pairs scored, and a
first-pass retriever returning five hundred candidates "to be safe" turns an
intentionally cheap first stage into the pipeline's actual bottleneck.
**Fix.** Cap the first-pass candidate count to what the reranker's latency
budget actually allows (commonly twenty to one hundred), measured against
the real p95 target, and tune the first-pass retriever's recall at that
specific k rather than assuming a wider net is free.

**Symptom.** The corrective (CRAG-style) loop occasionally never returns, or
returns after tens of seconds on an unlucky query.
**Cause.** No retry cap. A critic that repeatedly scores retrieval as
insufficient, rewrites the query, retrieves again, and re-scores, with no
maximum iteration count, degrades into unbounded latency on genuinely
under-covered topics, exactly the queries where users are least willing to
wait.
**Fix.** Hard-cap corrective retries (one or two) and define an explicit,
user-visible fallback ("limited information was found on this topic" plus
whatever partial answer is available) rather than letting the loop run until
it happens to succeed.

**Symptom.** Chunks retrieve with high similarity scores but the generator's
answer is wrong or unsupported by the retrieved text when a human reads it.
**Cause.** Fixed-size chunking severed the retrieved span from the context
that gave it meaning (the entity, the date, the qualifying clause) in a
different chunk, exactly the context-severing failure named in dimension 2,
and no contextual annotation step was added to repair it.
**Fix.** Add a contextual annotation pass (per dimension 8) before indexing,
or chunk along semantic boundaries (section, paragraph) rather than a fixed
token count, and verify with an evaluation set that specifically probes for
this failure (a question whose answer depends on an antecedent outside the
retrieved chunk).

**Symptom.** GraphRAG or RAPTOR answers a broad, thematic question well but
a specific, narrow factual question poorly, or the reverse.
**Cause.** The query was routed to the wrong level of the hierarchy or the
wrong graph granularity. A specific factual query answered from a
community-level summary loses the precision that lives only at the leaf or
entity level, and a thematic query answered only from leaf chunks never sees
the cross-document pattern the summarization levels exist to surface.
**Fix.** Route or retrieve across multiple levels simultaneously (as RAPTOR's
own design does) rather than picking one level per query type by a fixed
rule, and evaluate the two query classes (specific-fact versus thematic)
separately, because a single aggregate accuracy number hides this failure.

**Symptom.** Hybrid search with RRF performs worse than dense-only retrieval
did before the change.
**Cause.** The sparse index was built on the same fixed-size chunks as the
dense index, but BM25 needs the literal terms present in a chunk to match,
and a chunking strategy tuned for dense retrieval's semantic coherence can
split an identifier or a compound term across a chunk boundary, silently
breaking the sparse side that hybrid search was added to strengthen.
**Fix.** Verify the sparse retriever's standalone recall on a set of
exact-match queries after any chunking change, not only the fused pipeline's
aggregate score, because RRF can mask a broken sparse leg by relying on the
dense leg to compensate on average.

## 12. Trade-off matrix

| Force | Advanced RAG (multi-stage) | Naive RAG (single retrieval) | Long-context stuffing (no retrieval) | Fine-tuning on the corpus |
|---|---|---|---|---|
| Retrieval precision on multi-hop queries | High, purpose-built for this | Low, structurally single-hop | Not applicable, model sees everything | Depends on training data coverage, not query-time adaptive |
| Latency | Higher, multiple sequential stages | Lowest of the retrieval-based options | High per-request token cost dominates | Lowest at inference, cost paid upfront in training |
| Cost per query | Higher, extra model calls (rewrite, rerank) | Lower | Highest, full corpus tokens billed every request | Lowest per query, high one-time training cost |
| Freshness | Query-time stages fresh, graph and tree indexes stale between rebuilds | Fresh if index updated incrementally | Always fresh if source docs updated | Stale until retrained, model must be retrained for new facts |
| Exact-term and identifier accuracy | High, via sparse retriever and reranker | Weak, dense-only | High if the term is literally in context | Weak, fine-tuning does not reliably memorize exact rare strings |
| Engineering surface | Large, many interacting stages to test | Small, one stage | Small, but bounded by context window and cost | Large, requires a training and evaluation pipeline of its own |
| Debuggability | Harder, failure can originate in several stages | Easy, one place to look | Easy, but opaque why the model missed something in a huge context | Hard, opaque why the model answers as it does |
| Best fit | Large or heterogeneous corpus, multi-hop queries, precision-critical | Small corpus, single-hop factual queries, low-latency needs | Small to medium corpus that fits budget, simplicity valued over cost | Stable, narrow domain where behavior (not fresh facts) needs to change |

## 13. Related and incompatible patterns

- **Retrieval Augmented Generation (this catalog).** Advanced RAG is a
  direct extension of the base pattern's retrieve-then-generate structure.
  Every Advanced RAG variant in dimension 8 is Naive RAG with one or more
  additional stages inserted before or after the single retrieval call, and
  none of them replace the fundamental structure.
- **Routing (this catalog).** The Router participant in dimension 5 is a
  direct application of the Routing pattern, specialised to choosing among
  retrieval sources rather than among general request handlers.
- **Chain of Responsibility (GoF, this catalog).** The sequential pipeline in
  dimension 6, where each stage either passes its output forward or (in the
  corrective branch) redirects the flow, is structurally the same shape as a
  responsibility chain, with the difference that Advanced RAG's stages
  transform and filter a candidate list rather than deciding whether to
  handle a request at all.
- **ReAct (this catalog).** Agentic RAG, the variant in dimension 8 where
  retrieval is exposed as a callable tool rather than a fixed pipeline stage,
  is a direct application of the ReAct reasoning-and-acting loop with
  retrieval as one of the available actions.
- **Orchestrator-Worker (this catalog).** Query decomposition, where a
  multi-hop question is split into independent sub-questions each requiring
  its own retrieval, composes naturally with Orchestrator-Worker when those
  sub-questions are dispatched to separate retrieval workers and their
  results are synthesized by an orchestrating step.
- **Evaluator-Optimizer (this catalog).** The Critic role in CRAG is a
  specialised instance of the evaluator-optimizer loop, with the "optimizer"
  step being a broader retrieval or a web search fallback rather than a
  rewritten generation.
- **Reflexion (this catalog).** Self-RAG's inline reflection tokens are the
  retrieval-specific expression of the same self-critique-then-adjust idea
  Reflexion describes at the level of an agent's full task trajectory.
- **Incompatible with nothing structurally**, but in practice Advanced RAG's
  added latency is in direct tension with any product requirement for
  sub-second response time, and its added engineering surface is in tension
  with a team that has no capacity to build or maintain the evaluation
  apparatus dimension 15 depends on. Neither is a hard incompatibility, but
  both are reasons to stay with Naive RAG rather than adopt Advanced RAG.

## 14. Refactoring path in and out

Introducing Advanced RAG into a system that already runs Naive RAG, one stage
at a time, each verified against the evaluation set in dimension 15 before
the next is added.

1. Build or acquire a golden evaluation set of realistic queries with known
   correct answers and, ideally, known correct source chunks, before
   changing anything. Without this, every later step is unmeasurable.
2. Add a sparse (BM25) index alongside the existing dense index and fuse the
   two with Reciprocal Rank Fusion. This is the highest-value, lowest-risk
   first step because it directly closes the exact-match gap named in
   dimension 2 without touching the generation path at all.
3. Add a reranker over the fused candidate list, tuned to the latency budget
   as described in dimension 11's second failure mode. Measure precision at
   the final k before and after.
4. Add contextual chunk annotation (or re-chunk along semantic boundaries) if
   the evaluation set shows context-severing failures specifically, rather
   than as a blanket first step, because it is the step with the highest
   reindexing cost.
5. Add query transformation (HyDE or multi-query expansion) only if the
   evaluation set shows queries where the literal user phrasing is
   structurally far from the answer's phrasing, and validate it in parallel
   with, not instead of, direct query retrieval per dimension 11's first
   failure mode.
6. Add a corrective or self-reflective loop last, with an explicit retry cap,
   once the earlier stages have already reduced the rate of genuinely bad
   retrievals to the point where the loop is a rare fallback rather than the
   common case, because a corrective loop papering over a systematically bad
   first-pass retriever just makes every query slow instead of fixing the
   underlying problem.

Removing a stage, when a later evaluation shows it is not earning its cost.

1. Disable the stage behind a feature flag rather than deleting it outright,
   and re-run the evaluation set with it off.
2. If aggregate accuracy is statistically unchanged and latency or cost
   drops, remove the stage. If accuracy drops for a specific query subclass,
   keep the stage but consider routing only that subclass through it
   (per-query-type routing) rather than running it unconditionally for
   every query.
3. For the offline hierarchical and graph indexes specifically, confirm the
   reindexing cadence is still funded before removing the pipeline stages
   that route into them. An index nobody maintains going stale is a worse
   failure mode than never having built it.

## 15. Testing and verification

Test each stage of the pipeline independently before testing the assembled
whole, because a pipeline-level accuracy number cannot tell you which stage
regressed.

- **Retrieval-stage tests.** Standard information retrieval metrics against
  the golden evaluation set, recall at k and precision at k for the
  first-pass retriever (sparse, dense, and fused, measured separately so a
  regression in one leg is visible even when RRF masks it in the fused
  score, per dimension 11), and normalized discounted cumulative gain or
  mean reciprocal rank for the reranked list, since reranking is
  specifically about ordering quality at the top of the list rather than
  raw recall.
- **RAGAS-style reference-free metrics.** Es, James, Espinosa-Anke,
  Schockaert's RAGAS framework (dimension 9) defines faithfulness (do the
  generated answer's claims trace back to the retrieved context), answer
  relevancy (does the answer address the actual question), context
  precision (how much of the retrieved context was actually used), and
  context recall (was the necessary information retrieved at all) as four
  metrics computable without human-labelled ground truth, which makes them
  practical to run on every pull request rather than only on a periodic
  manual review.
- **Contract tests per stage, with mocked neighbours.** Test the Query
  Transformer against a fixed set of input queries and assert its output
  shape and that it does not silently drop the original query. Test the
  Reranker against a fixed candidate list with a known correct ordering.
  Test the fusion module's RRF math directly with synthetic ranked lists
  where the correct fused order is known by construction, independent of
  any real retriever.
- **Failure-injection tests.** Feed the pipeline a query engineered to
  trigger each failure mode in dimension 11 (an out-of-domain query for HyDE,
  a genuinely uncovered topic for the corrective loop, an identifier-only
  query for hybrid search) and assert the system degrades the way it is
  designed to (a bounded retry, a fallback message, a correct exact-match
  hit) rather than silently returning a confident wrong answer.
- **A/B or shadow evaluation before shipping a new stage.** Because stages
  interact, run the golden evaluation set through both the old and the
  candidate pipeline and diff the results at the level of individual queries,
  not only the aggregate score, since an aggregate improvement can hide a
  regression on a specific, important query subclass.

## 16. Observability signals

- **Per-stage latency, logged separately.** Query transformation time,
  sparse retrieval time, dense retrieval time, fusion time, reranking time,
  generation time, and, when triggered, the corrective loop's retry count
  and its added latency. A single end-to-end latency number cannot show
  which stage is the actual bottleneck as the corpus or traffic pattern
  shifts.
- **Retrieved document identifiers and scores, per query.** Logging which
  chunk IDs were retrieved, their fused rank, and their reranker score
  (not only the final answer) is what makes the failure modes in dimension
  11 diagnosable after the fact rather than only reproducible by guesswork.
- **Reranker score distribution.** A healthy system shows a reranker score
  distribution with clear separation between the top few candidates and the
  rest. A distribution that is flat, with no strong top candidate, is an
  early signal that first-pass retrieval is returning a genuinely poor
  candidate set for that query, worth surfacing before the answer quality
  visibly degrades.
- **Corrective loop trigger rate.** The fraction of queries that hit the
  CRAG-style "ambiguous" or "incorrect" branch is a direct, real-time proxy
  for first-pass retrieval health. A rising trigger rate over time, without
  a change in query distribution, points at index staleness or corpus drift.
- **Faithfulness and context-precision sampling.** Running RAGAS-style
  metrics on a sampled fraction of live traffic, not only the offline
  evaluation set, catches drift the static golden set will not, because
  real query distributions shift after launch in ways a fixed evaluation set
  cannot anticipate.
- **Index freshness lag.** For RAPTOR and GraphRAG specifically, the elapsed
  time since the last full or incremental index rebuild, alerted on a
  threshold, since a stale hierarchical or graph index degrades silently
  (queries still return answers, just against older facts) rather than
  failing loudly.

## 17. Security and privacy implications

- **Indirect prompt injection via retrieved content.** Because Advanced RAG
  retrieves and inserts external text directly into the generation prompt,
  any document in the corpus that contains adversarial instructions ("ignore
  previous instructions and...") is a live injection vector the moment it is
  retrieved, and the added stages in this pattern (query rewriting,
  reranking) do not filter for this by default. A system handling untrusted
  or user-contributed source documents needs an explicit
  instruction-injection filter on retrieved content before it reaches the
  generator, treating retrieved text as untrusted input rather than trusted
  context.
- **Cross-tenant data leakage in a shared index.** A single vector or graph
  index serving multiple tenants must filter retrieval by tenant at the
  query layer (metadata filtering enforced before or during the similarity
  search, not only after), because a fused or reranked candidate list that
  silently mixes chunks from another tenant's documents is a data leak that
  a superficial functional test will not catch, since the wrong-tenant
  chunk may simply be reranked low rather than visibly appearing in the
  final answer while still having been read and processed by the model.
- **The right-to-be-forgotten problem in vector and hierarchical indexes.**
  Deleting a document from a flat vector index is a straightforward removal.
  Deleting it from a RAPTOR tree or a GraphRAG entity graph is not, because
  the deleted content may have contributed to a cluster summary or a
  community summary that other, still-valid documents also fed into. A
  correct deletion requires reprocessing the affected summaries, not merely
  removing the source chunk, which is a real operational cost that has to be
  designed for up front in any system handling personal data subject to
  deletion requests.
- **PII embedded in generated intermediate artifacts.** Contextual
  Retrieval's per-chunk annotations, RAPTOR's cluster summaries, and
  GraphRAG's entity and community summaries are themselves LLM-generated
  text derived from the source corpus, and if the source corpus contains
  personal data, these derived artifacts can restate or aggregate that data
  in a new location (a summary node) that the original data governance and
  redaction process for the raw documents was never designed to cover.
- **Citation as an attack surface for copyright and licensing exposure.**
  Because Advanced RAG is specifically built to surface and cite exact
  retrieved passages more precisely than Naive RAG, a system indexing
  licensed or copyrighted third-party content is more likely, not less, to
  reproduce a verbatim passage in its output, which is a licensing and
  copyright concern layered directly on top of the accuracy concern this
  pattern is otherwise optimizing for.

## 18. References

1. Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yi
   Dai, Jiawei Sun, Meng Wang, Haofen Wang, "Retrieval-Augmented Generation
   for Large Language Models. A Survey," submitted 18 December 2023, revised
   27 March 2024. https://arxiv.org/abs/2312.10997 (verified 2026-08-02).
2. Luyu Gao, Xueguang Ma, Jimmy Lin, Jamie Callan, "Precise Zero-Shot Dense
   Retrieval without Relevance Labels."
   https://arxiv.org/abs/2212.10496 (verified 2026-08-02).
3. Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, Hannaneh Hajishirzi,
   "Self-RAG. Learning to Retrieve, Generate, and Critique through
   Self-Reflection," submitted 17 October 2023.
   https://arxiv.org/abs/2310.11511 (verified 2026-08-02).
4. Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, Zhen-Hua Ling, "Corrective Retrieval
   Augmented Generation." https://arxiv.org/abs/2401.15884 (verified
   2026-08-02).
5. Parth Sarthi, Salman Abdullah, Aditi Tuli, Shubh Khanna, Anna Goldie,
   Christopher D. Manning, "RAPTOR. Recursive Abstractive Processing for
   Tree-Organized Retrieval." https://arxiv.org/abs/2401.18059 (verified
   2026-08-02).
6. Darren Edge, Ha Trinh, Newman Cheng, Joshua Bradley, Alex Chao, Apurva
   Mody, Steven Truitt, Dasha Metropolitansky, Robert Osazuwa Ness, Jonathan
   Larson, "From Local to Global. A Graph RAG Approach to Query-Focused
   Summarization." https://arxiv.org/abs/2404.16130 (verified 2026-08-02).
7. Microsoft, GraphRAG repository, README and linked Microsoft Research blog
   post. https://github.com/microsoft/graphrag (verified 2026-08-02).
8. Anthropic, "Introducing Contextual Retrieval," 19 September 2024.
   https://www.anthropic.com/news/contextual-retrieval (verified 2026-08-02).
9. Cohere, Rerank documentation. https://docs.cohere.com/docs/rerank
   (verified 2026-08-02).
10. Shahul Es, Jithin James, Luis Espinosa-Anke, Steven Schockaert, "Ragas.
    Automated Evaluation of Retrieval Augmented Generation," submitted 26
    September 2023. https://arxiv.org/abs/2309.15217 (verified 2026-08-02).
11. Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele
    Bevilacqua, Fabio Petroni, Percy Liang, "Lost in the Middle. How Language
    Models Use Long Contexts," Transactions of the Association for
    Computational Linguistics, 2024. https://arxiv.org/abs/2307.03172
    (verified 2026-08-02).

## Code examples

The three samples below implement the fusion and reranking core of an
Advanced RAG pipeline, sparse (BM25) scoring, dense cosine-similarity
scoring, Reciprocal Rank Fusion, and a lexical-overlap stand-in for a
cross-encoder reranker, using only each language's standard library so the
examples compile and run without network access or an API key. A production
system replaces the toy BM25, the toy embeddings, and the toy reranker with a
real search index, a real embedding model, and a real cross-encoder or LLM
call, but the fusion and ordering logic shown here is the actual production
shape.

### Python

```python
import math
from collections import Counter


def tokenize(text):
    return text.lower().split()


def bm25_scores(query, docs, k1=1.5, b=0.75):
    doc_tokens = [tokenize(d) for d in docs]
    doc_lens = [len(t) for t in doc_tokens]
    avg_len = sum(doc_lens) / len(doc_lens)
    df = Counter()
    for tokens in doc_tokens:
        for term in set(tokens):
            df[term] += 1
    n = len(docs)
    query_terms = tokenize(query)
    scores = []
    for tokens, dl in zip(doc_tokens, doc_lens):
        tf = Counter(tokens)
        score = 0.0
        for term in query_terms:
            if df[term] == 0:
                continue
            idf = math.log((n - df[term] + 0.5) / (df[term] + 0.5) + 1)
            freq = tf[term]
            denom = freq + k1 * (1 - b + b * dl / avg_len)
            score += idf * (freq * (k1 + 1)) / denom
        scores.append(score)
    return scores


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def dense_scores(query_vec, doc_vecs):
    return [cosine(query_vec, v) for v in doc_vecs]


def reciprocal_rank_fusion(ranked_lists, k=60):
    fused = Counter()
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            fused[doc_id] += 1.0 / (k + rank)
    return [doc_id for doc_id, _ in fused.most_common()]


def rank_by_score(doc_ids, scores):
    return [d for d, _ in sorted(zip(doc_ids, scores), key=lambda p: -p[1])]


def lexical_rerank(query, docs, doc_ids):
    query_set = set(tokenize(query))
    overlaps = []
    for doc_id, text in zip(doc_ids, docs):
        overlap = len(query_set & set(tokenize(text)))
        overlaps.append((doc_id, overlap))
    overlaps.sort(key=lambda p: -p[1])
    return [d for d, _ in overlaps]


def run_pipeline(query, docs, doc_ids, doc_vecs, query_vec):
    sparse_ranked = rank_by_score(doc_ids, bm25_scores(query, docs))
    dense_ranked = rank_by_score(doc_ids, dense_scores(query_vec, doc_vecs))
    fused = reciprocal_rank_fusion([sparse_ranked, dense_ranked])
    top_candidates = fused[:5]
    candidate_docs = [docs[doc_ids.index(d)] for d in top_candidates]
    reranked = lexical_rerank(query, candidate_docs, top_candidates)
    return reranked


if __name__ == "__main__":
    doc_ids = ["d1", "d2", "d3", "d4"]
    docs = [
        "invoice 48291 was paid on march third by the enterprise tier customer",
        "the enterprise tier price changed from forty to fifty five dollars",
        "quarterly revenue grew twelve percent across every region",
        "invoice 48219 remains unpaid past the sixty day deadline",
    ]
    doc_vecs = [
        [0.9, 0.1, 0.0],
        [0.1, 0.9, 0.0],
        [0.0, 0.0, 0.9],
        [0.8, 0.2, 0.0],
    ]
    query = "invoice 48291 payment status"
    query_vec = [0.85, 0.15, 0.0]

    result = run_pipeline(query, docs, doc_ids, doc_vecs, query_vec)
    print("final ranking", result)
    assert result[0] == "d1", "exact identifier match should rank first"
    print("ok")
```

Run with `python3 advanced_rag.py`. Verified output is `final ranking ['d1',
'd4', 'd2', 'd3']` then `ok`, confirming the sparse BM25 leg's exact-match
signal for "48291" surfaces the correct invoice at rank one even though a
purely dense cosine ranking alone (tried separately) would rank d1 and d4
closer together without the lexical tie-break the fusion and rerank stages
provide.

### TypeScript

```typescript
function tokenize(text: string): string[] {
  return text.toLowerCase().split(/\s+/).filter(Boolean);
}

function bm25Scores(query: string, docs: string[], k1 = 1.5, b = 0.75): number[] {
  const docTokens = docs.map(tokenize);
  const docLens = docTokens.map((t) => t.length);
  const avgLen = docLens.reduce((a, c) => a + c, 0) / docLens.length;
  const df = new Map<string, number>();
  for (const tokens of docTokens) {
    for (const term of new Set(tokens)) {
      df.set(term, (df.get(term) ?? 0) + 1);
    }
  }
  const n = docs.length;
  const queryTerms = tokenize(query);
  return docTokens.map((tokens, i) => {
    const dl = docLens[i];
    const tf = new Map<string, number>();
    for (const t of tokens) tf.set(t, (tf.get(t) ?? 0) + 1);
    let score = 0;
    for (const term of queryTerms) {
      const termDf = df.get(term) ?? 0;
      if (termDf === 0) continue;
      const idf = Math.log((n - termDf + 0.5) / (termDf + 0.5) + 1);
      const freq = tf.get(term) ?? 0;
      const denom = freq + k1 * (1 - b + (b * dl) / avgLen);
      score += (idf * (freq * (k1 + 1))) / denom;
    }
    return score;
  });
}

function cosine(a: number[], b: number[]): number {
  const dot = a.reduce((sum, v, i) => sum + v * b[i], 0);
  const na = Math.sqrt(a.reduce((sum, v) => sum + v * v, 0));
  const nb = Math.sqrt(b.reduce((sum, v) => sum + v * v, 0));
  if (na === 0 || nb === 0) return 0;
  return dot / (na * nb);
}

function rankByScore(ids: string[], scores: number[]): string[] {
  return ids
    .map((id, i) => ({ id, score: scores[i] }))
    .sort((a, b) => b.score - a.score)
    .map((p) => p.id);
}

function reciprocalRankFusion(rankedLists: string[][], k = 60): string[] {
  const fused = new Map<string, number>();
  for (const ranked of rankedLists) {
    ranked.forEach((id, idx) => {
      const rank = idx + 1;
      fused.set(id, (fused.get(id) ?? 0) + 1 / (k + rank));
    });
  }
  return [...fused.entries()].sort((a, b) => b[1] - a[1]).map(([id]) => id);
}

function lexicalRerank(query: string, ids: string[], docs: string[]): string[] {
  const queryTerms = new Set(tokenize(query));
  const overlaps = ids.map((id, i) => {
    const overlap = tokenize(docs[i]).filter((t) => queryTerms.has(t)).length;
    return { id, overlap };
  });
  overlaps.sort((a, b) => b.overlap - a.overlap);
  return overlaps.map((o) => o.id);
}

function runPipeline(
  query: string,
  docs: string[],
  docIds: string[],
  docVecs: number[][],
  queryVec: number[],
): string[] {
  const sparseRanked = rankByScore(docIds, bm25Scores(query, docs));
  const denseRanked = rankByScore(
    docIds,
    docVecs.map((v) => cosine(queryVec, v)),
  );
  const fused = reciprocalRankFusion([sparseRanked, denseRanked]);
  const topCandidates = fused.slice(0, 5);
  const candidateDocs = topCandidates.map((id) => docs[docIds.indexOf(id)]);
  return lexicalRerank(query, topCandidates, candidateDocs);
}

const docIds = ["d1", "d2", "d3", "d4"];
const docs = [
  "invoice 48291 was paid on march third by the enterprise tier customer",
  "the enterprise tier price changed from forty to fifty five dollars",
  "quarterly revenue grew twelve percent across every region",
  "invoice 48219 remains unpaid past the sixty day deadline",
];
const docVecs = [
  [0.9, 0.1, 0.0],
  [0.1, 0.9, 0.0],
  [0.0, 0.0, 0.9],
  [0.8, 0.2, 0.0],
];
const query = "invoice 48291 payment status";
const queryVec = [0.85, 0.15, 0.0];

const result = runPipeline(query, docs, docIds, docVecs, queryVec);
console.log("final ranking", result);
if (result[0] !== "d1") {
  throw new Error("exact identifier match should rank first");
}
console.log("ok");
```

Compiled with `npx tsc --strict --target es2020 --module commonjs
advanced_rag.ts` then run with `node advanced_rag.js`. Verified output
matches the Python sample, `final ranking [ 'd1', 'd4', 'd2', 'd3' ]` then
`ok`.

### Go

```go
package main

import (
	"fmt"
	"math"
	"sort"
	"strings"
)

func tokenize(text string) []string {
	return strings.Fields(strings.ToLower(text))
}

func bm25Scores(query string, docs []string, k1, b float64) []float64 {
	docTokens := make([][]string, len(docs))
	docLens := make([]int, len(docs))
	total := 0
	for i, d := range docs {
		docTokens[i] = tokenize(d)
		docLens[i] = len(docTokens[i])
		total += docLens[i]
	}
	avgLen := float64(total) / float64(len(docs))

	df := map[string]int{}
	for _, tokens := range docTokens {
		seen := map[string]bool{}
		for _, t := range tokens {
			if !seen[t] {
				df[t]++
				seen[t] = true
			}
		}
	}
	n := float64(len(docs))
	queryTerms := tokenize(query)

	scores := make([]float64, len(docs))
	for i, tokens := range docTokens {
		tf := map[string]int{}
		for _, t := range tokens {
			tf[t]++
		}
		dl := float64(docLens[i])
		score := 0.0
		for _, term := range queryTerms {
			termDf := float64(df[term])
			if termDf == 0 {
				continue
			}
			idf := math.Log((n-termDf+0.5)/(termDf+0.5) + 1)
			freq := float64(tf[term])
			denom := freq + k1*(1-b+b*dl/avgLen)
			score += idf * (freq * (k1 + 1)) / denom
		}
		scores[i] = score
	}
	return scores
}

func cosine(a, b []float64) float64 {
	dot, na, nb := 0.0, 0.0, 0.0
	for i := range a {
		dot += a[i] * b[i]
		na += a[i] * a[i]
		nb += b[i] * b[i]
	}
	if na == 0 || nb == 0 {
		return 0
	}
	return dot / (math.Sqrt(na) * math.Sqrt(nb))
}

type scored struct {
	id    string
	score float64
}

func rankByScore(ids []string, scores []float64) []string {
	pairs := make([]scored, len(ids))
	for i, id := range ids {
		pairs[i] = scored{id, scores[i]}
	}
	sort.Slice(pairs, func(i, j int) bool { return pairs[i].score > pairs[j].score })
	out := make([]string, len(pairs))
	for i, p := range pairs {
		out[i] = p.id
	}
	return out
}

func reciprocalRankFusion(rankedLists [][]string, k float64) []string {
	fused := map[string]float64{}
	for _, ranked := range rankedLists {
		for idx, id := range ranked {
			rank := float64(idx + 1)
			fused[id] += 1.0 / (k + rank)
		}
	}
	ids := make([]string, 0, len(fused))
	for id := range fused {
		ids = append(ids, id)
	}
	sort.Slice(ids, func(i, j int) bool { return fused[ids[i]] > fused[ids[j]] })
	return ids
}

func lexicalRerank(query string, ids []string, docs []string) []string {
	queryTerms := map[string]bool{}
	for _, t := range tokenize(query) {
		queryTerms[t] = true
	}
	type ov struct {
		id      string
		overlap int
	}
	ovs := make([]ov, len(ids))
	for i, id := range ids {
		count := 0
		for _, t := range tokenize(docs[i]) {
			if queryTerms[t] {
				count++
			}
		}
		ovs[i] = ov{id, count}
	}
	sort.Slice(ovs, func(i, j int) bool { return ovs[i].overlap > ovs[j].overlap })
	out := make([]string, len(ovs))
	for i, o := range ovs {
		out[i] = o.id
	}
	return out
}

func indexOf(ids []string, target string) int {
	for i, id := range ids {
		if id == target {
			return i
		}
	}
	return -1
}

func runPipeline(query string, docs []string, docIds []string, docVecs [][]float64, queryVec []float64) []string {
	sparseScores := bm25Scores(query, docs, 1.5, 0.75)
	sparseRanked := rankByScore(docIds, sparseScores)

	denseScores := make([]float64, len(docVecs))
	for i, v := range docVecs {
		denseScores[i] = cosine(queryVec, v)
	}
	denseRanked := rankByScore(docIds, denseScores)

	fused := reciprocalRankFusion([][]string{sparseRanked, denseRanked}, 60)
	top := fused
	if len(top) > 5 {
		top = top[:5]
	}
	candidateDocs := make([]string, len(top))
	for i, id := range top {
		candidateDocs[i] = docs[indexOf(docIds, id)]
	}
	return lexicalRerank(query, top, candidateDocs)
}

func main() {
	docIds := []string{"d1", "d2", "d3", "d4"}
	docs := []string{
		"invoice 48291 was paid on march third by the enterprise tier customer",
		"the enterprise tier price changed from forty to fifty five dollars",
		"quarterly revenue grew twelve percent across every region",
		"invoice 48219 remains unpaid past the sixty day deadline",
	}
	docVecs := [][]float64{
		{0.9, 0.1, 0.0},
		{0.1, 0.9, 0.0},
		{0.0, 0.0, 0.9},
		{0.8, 0.2, 0.0},
	}
	query := "invoice 48291 payment status"
	queryVec := []float64{0.85, 0.15, 0.0}

	result := runPipeline(query, docs, docIds, docVecs, queryVec)
	fmt.Println("final ranking", result)
	if result[0] != "d1" {
		panic("exact identifier match should rank first")
	}
	fmt.Println("ok")
}
```

Run with `go run advanced_rag.go`. Verified output is `final ranking [d1 d4
d2 d3]` then `ok`, the same ranking as the Python and TypeScript samples,
because all three implement the identical BM25, cosine, RRF, and
lexical-overlap-rerank algorithm over the identical toy corpus.

Java, Rust, and Swift are omitted from this entry. Java and Rust would repeat
the same numeric algorithm shown three times above with no idiomatic
difference the pattern depends on (this is arithmetic and sorting, not a
language-specific control-flow shape), and the production interest for this
pattern in Java and Rust is almost entirely in calling an external vector
database or search service's client library rather than in implementing BM25
or RRF by hand, which this entry cannot demonstrate without a network
dependency. Swift is omitted for the same reason and because Advanced RAG
pipelines in the surveyed production uses (dimension 9) run server-side, not
in an Apple-platform client, making an idiomatic Swift server-side example
less representative of how the pattern is actually deployed.
