---
name: HyDE (Hypothetical Document Embeddings)
slug: hyde
family: 17-ai-agentic
category: Retrieval
aliases: [Hypothetical Document Embeddings, Query-to-Document Expansion]
first_described: "Gao, Ma, Lin, Callan 2022"
maturity: established
related: [retrieval-augmented-generation, advanced-rag, agentic-rag, graphrag, self-consistency]
incompatible_with: []
verified: 2026-08-02
---

# HyDE (Hypothetical Document Embeddings)

## 1. Name, aliases, and lineage

HyDE stands for Hypothetical Document Embeddings. It was introduced by Luyu
Gao, Xueguang Ma, Jimmy Lin, and Jamie Callan in the paper "Precise Zero-Shot
Dense Retrieval without Relevance Labels," first posted to arXiv in December
2022 and later published at ACL 2023
(https://arxiv.org/abs/2212.10496, verified 2026-08-02). The paper's own
abstract states the method plainly. Given a query, an instruction tuned
language model is asked to write a hypothetical document that answers it, and
an unsupervised contrastively trained encoder embeds that document, and the
embedding is used to search a real corpus by vector similarity. The authors
named the technique "HyDE" for Hypothetical Document Embeddings, and that
name has not been contested or renamed in the years since. The paper appears
in the ACL Anthology as Gao et al., "Precise Zero-Shot Dense Retrieval
without Relevance Labels," Proceedings of the 61st Annual Meeting of the
Association for Computational Linguistics (Volume 1, Long Papers), 2023,
pages 1762 to 1777 (https://aclanthology.org/2023.acl-long.99/, verified
2026-08-02).

The paper also names the encoder used in the reported experiments. Contriever,
an unsupervised dense retriever, and mContriever for the multilingual
setting, both from Gautier Izacard et al. The generator used across the main
experiments was InstructGPT (text-davinci-003 at the time of writing), used
zero-shot with no retrieval-specific fine-tuning of either the generator or
the encoder.

"Query-to-Document Expansion" is not a name the original authors use, but it
is the description found in later retrieval surveys and blog write-ups when
they place HyDE inside the older family of query expansion techniques,
expanding what is searched for rather than expanding a document. The
technique's own closest historical ancestor is pseudo-relevance feedback, a
sparse-retrieval method from classical information retrieval where a first
round of retrieved documents is used to reformulate the query. Sean
MacAvaney, Nicola Tonellotto, and Craig Macdonald discuss this ancestry in
"Reproducibility, Replicability, and Insights into Dense Multi-Representation
Retrieval Models. from ColBERT to Col*" (https://arxiv.org/abs/2110.06051,
verified 2026-08-02), and the HyDE paper itself cites Rocchio's 1971
relevance feedback formulation and Lavrenko and Croft's 2001 relevance-based
language model as the classical precedent it extends into the zero-shot
dense setting.

## 2. Problem and context

Dense retrieval works by embedding a query into the same vector space as a
corpus of documents and finding the nearest neighbors by cosine similarity or
inner product. The entire mechanism depends on one assumption holding. The
query embedding must land close, in that vector space, to the embeddings of
the documents that actually answer it. That assumption is fragile in exactly
the situations where retrieval matters most.

A query is short. A document is long. A query is often a question, and the
answer is a statement. "What is the boiling point of methane at standard
pressure" and "Methane boils at negative 161.5 degrees Celsius at one
atmosphere" share almost no surface vocabulary and, depending on the encoder,
can sit meaningfully apart in embedding space even though one is the exact
answer to the other. Dense encoders trained with contrastive objectives on
query-passage pairs, such as DPR (Karpukhin et al., "Dense Passage Retrieval
for Open-Domain Question Answering," EMNLP 2020,
https://arxiv.org/abs/2004.04906, verified 2026-08-02), learn this
query-to-passage alignment from labeled pairs. When there are no labels for a
new domain, a new language, or a rare task, the encoder has never seen
examples of what a query in that space should be close to, and retrieval
quality collapses. The HyDE paper's own framing, in its abstract, is that
building an effective dense retriever "still requires relevance labels" and
that this is a genuine barrier to zero-shot use.

Sparse retrieval (BM25 and its relatives) does not have this exact problem,
because it matches on literal terms and their statistical weight rather than
on a learned embedding geometry, but it has the opposite weakness. It cannot
bridge vocabulary gaps at all. A user who searches for "car" will not find a
document that only ever says "automobile," and BM25 has no notion of
paraphrase.

HyDE addresses the mismatch by changing what gets embedded on the query
side. Instead of embedding the short question, it first asks a generator to
write a fake answer to the question, in the style and register of the target
corpus, and embeds that. A fabricated answer, wrong in its specific facts but
right in its topic, vocabulary, and rhetorical shape, sits much closer in
embedding space to a real correct answer than the original question ever
did, because the encoder was trained to place similar-style, similar-topic
text near each other, and a hypothetical answer is stylistically much closer
to a real answer than a question is.

The context in which this problem shows up concretely covers several
recurring shapes. A support search system launched for a brand-new product
line with zero historical query logs. A legal or medical retrieval system
where the corpus's register, dense, formal, jargon-heavy, is far from how a
layperson would phrase a search. A multilingual retrieval system where
labeled query-document pairs exist for one language but not others. Or any
retrieval-augmented generation pipeline being stood up for a new domain
where nobody has yet collected the relevance-labeled training data a
supervised dense retriever needs.

## 3. Forces

- **Retrieval precision versus label availability.** Supervised dense
  retrievers such as DPR beat BM25 on in-domain benchmarks, but that quality
  is purchased with relevance-labeled query-document pairs. HyDE trades some
  of that precision ceiling for the ability to work with zero labeled pairs
  at all.
- **Latency and cost versus recall quality.** Every query now costs one
  additional generation call before the embedding and search step even
  starts. That call adds real wall-clock latency (typically hundreds of
  milliseconds to a few seconds depending on the generator and the length of
  the hypothetical document) and a real per-query dollar cost if the
  generator is a hosted API model.
- **Vocabulary bridging versus factual grounding.** The entire mechanism
  relies on the generator producing plausible, on-topic prose even when it
  does not know the true answer. That is a deliberate acceptance of
  hallucination as a feature at the embedding stage, which is an unusual
  posture for anything built on top of a language model, and it must be
  explicitly separated from hallucination at the answer-generation stage,
  where it remains a defect.
- **Domain and register transfer versus generator capability.** HyDE's
  benefit is largest exactly when the generator is capable enough to imitate
  the target corpus's register, a clinical note, a legal brief, a Wikipedia
  paragraph, without being fine-tuned on it. A weak or heavily
  instruction-averse generator narrows the benefit.
- **Consistency versus stochasticity.** Because the hypothetical document is
  sampled from a language model, two runs of the same query at nonzero
  temperature can produce different hypothetical documents and, downstream,
  different rankings. The original paper handles this with an averaging
  step (see Dimension 5) rather than pretending the sampling variance does
  not exist.
- **Simplicity of a single embedding lookup versus multi-stage retrieval
  architecture.** HyDE preserves the operational simplicity of a single
  nearest-neighbor search against a vector index. It sacrifices nothing of
  that shape. The added complexity is entirely upstream, in what gets
  embedded, not in the retrieval infrastructure itself.

The pattern favors recall and zero-shot generalization at the cost of an
extra network hop, added latency, and generator-dependent variance. It does
not attempt to improve factual grounding of the final answer. That remains
the responsibility of whatever consumes the retrieved documents.

## 4. Applicability and non-applicability

Reach for HyDE when the following hold.

- There is no labeled query-document pair data for the target corpus or
  domain, and building that labeled set is not feasible in the current
  timeline.
- The corpus's writing register is far from how users phrase their queries.
  A support knowledge base of terse how-to articles searched with
  conversational questions is a strong fit.
- The retrieval task is being stood up for a new language or a new vertical
  (legal, biomedical, financial filings) where an off-the-shelf dense
  encoder has not seen labeled pairs in that register.
- Query volume is low to moderate and the added latency and cost of one
  extra generation call per query is acceptable, or the query stream can
  tolerate caching of hypothetical documents for repeated or near-duplicate
  queries.
- The pipeline already has access to a capable instruction-following
  generator, because HyDE's quality is bounded by the generator's ability to
  imitate the corpus register.

Do not reach for HyDE when any of the following hold.

- Labeled query-document pairs already exist in sufficient quantity to
  fine-tune a supervised dense retriever. The HyDE paper's own results show
  a fine-tuned encoder such as a fine-tuned DPR or Contriever variant
  matching or beating HyDE on in-domain benchmarks where labels are
  available. HyDE is a zero-shot substitute, not a universal upgrade over
  supervised retrieval.
- Query-time latency budget is tight (sub-100-millisecond retrieval SLAs),
  because the generation step alone commonly costs more than that.
- Per-query cost must be near zero. An extra LLM call on every search
  multiplies the marginal cost of retrieval by whatever the generator
  charges per call, which can dominate the cost of the vector search itself.
- The domain requires exact, literal term matching, such as searching legal
  citation numbers, part numbers, or SKUs, where a fabricated hypothetical
  document introduces noise rather than useful paraphrase, and BM25 or exact
  string matching already solves the problem directly.
- The generator available to the system is weak, refuses to speculate about
  answers it does not know, or is prone to short, low-information
  completions, because HyDE's gain is proportional to how well the
  hypothetical document imitates the real corpus.
- The application already has strong query logs or click-through data that
  could train a supervised or weakly supervised retriever. That data is a
  more reliable signal than a model's guess.
- Adversarial or safety-sensitive input is expected, since asking a model to
  generate a plausible answer to any query, including a manipulative or
  disallowed one, can itself be a prompt-injection surface
  (see Dimension 17).

## 5. Structure

- **Query.** The original short user question or search string, unchanged
  and never itself embedded for the final search step.
- **Instruction-following generator.** A language model, zero-shot or
  few-shot prompted, that is asked to write a hypothetical passage
  answering the query as if it were drawn from the target corpus. In the
  original paper this is InstructGPT. In current implementations it is
  commonly a chat-tuned model such as a Claude, GPT, or open-weight
  instruction model, invoked with a short prompt template rather than a
  fine-tuned generation head.
- **Hypothetical document, or documents.** The generator's output. The
  original paper samples multiple hypothetical documents per query. The
  paper's main configuration uses eight.
- **Contrastive dense encoder.** An unsupervised or weakly supervised
  encoder, trained with a contrastive objective, that maps text to a fixed
  dimensional vector. The paper uses Contriever for English and mContriever
  for multilingual retrieval. Production systems commonly substitute
  whatever embedding model already indexes their corpus.
- **Embedding averaging step.** Each sampled hypothetical document is
  encoded separately, and the resulting vectors are averaged into a single
  query vector before search. The paper frames this as implicitly filtering
  out any one hallucinated detail that would otherwise dominate a single
  embedding, since averaging over several independently sampled documents
  pulls the vector toward the shared topical and stylistic signal and away
  from any single document's specific, likely-wrong, claims.
- **Vector index or corpus.** The real document collection, pre-embedded with
  the same contrastive encoder used to embed the hypothetical documents.
  This is the collection the averaged hypothetical embedding is compared
  against, using standard nearest-neighbor search.
- **Ranked real documents.** The output. The top-k real, factually grounded
  documents from the corpus, ranked by similarity to the averaged
  hypothetical embedding. Nothing hypothetical is returned to the caller.
  The hypothetical documents exist only to steer the search vector.

## 6. ASCII structure diagram

```
+------------------+
|      Query       |   "What is the boiling point of methane?"
+---------+--------+
          |
          v
+--------------------------------+
|  Instruction-Following          |
|  Generator (zero-shot prompt)   |
+---------+------------------------+
          |  sample N hypothetical
          |  documents (paper uses N=8)
          v
+--------------------------------+
| Hyp Doc 1 | Hyp Doc 2 | ... N   |
+-----+-----+-----+-----+----+----+
      |           |           |
      v           v           v
+--------------------------------+
|  Contrastive Dense Encoder      |
|  (same encoder as the corpus)   |
+-----+-----+-----+-----+----+----+
      |           |           |
      v           v           v
   vec_1        vec_2  ...   vec_N
      \           |           /
       \          |          /
        v         v         v
       +-----------------------+
       |   Average embedding    |
       +-----------+-------------+
                   |
                   v
       +-----------------------+
       |   Nearest-neighbor      |
       |   search over Vector    |
       |   Index (real corpus,   |
       |   same encoder space)   |
       +-----------+-------------+
                   |
                   v
       +-----------------------+
       |  Ranked real documents  |
       |  (returned to caller,   |
       |   never the hyp docs)   |
       +-----------------------+
```

## 7. Dynamics

```
1. Caller submits Query Q.
2. Generator is prompted with a template such as
     "Write a passage that answers the question. {Q}"
   and produces N samples D_1 .. D_N at nonzero temperature.
3. Each D_i is independently ENCODED with the same contrastive
   encoder used to embed the real corpus, producing vectors
   e_1 .. e_N.
4. The vectors are averaged.
     v_HyDE = (1/N) * sum(e_1 .. e_N)
   The original query Q is NOT embedded and NOT part of this
   average. Only the hypothetical documents are averaged.
5. v_HyDE is used as the search vector against the pre-built
   vector index of the real corpus (dot product or cosine
   similarity, same as any dense retriever).
6. The top-k real documents by similarity to v_HyDE are
   returned. If a downstream RAG generation step exists, these
   k real documents, not the hypothetical ones, are what is
   passed into the generation prompt as retrieved context.
7. Steps 2 through 6 repeat independently per query. There is
   no session state or caching required by the pattern itself,
   though production systems commonly cache the hypothetical
   documents, or their embeddings, for repeated or near-
   duplicate queries to amortize the generator cost.
```

The critical ordering fact, easy to get backward when implementing this from
memory, is this. The hypothetical document is generated first, embedded
second, and only that embedding is ever searched against the real index. The
generator never sees the corpus, and the corpus's own documents are never
re-embedded per query. Only the standard, one-time corpus embedding is
reused, exactly as in any dense retrieval system.

## 8. Implementation variants

- **Single-sample HyDE.** N=1. Cheapest and lowest-latency variant, at the
  cost of full exposure to whatever one sample the generator happened to
  produce, including any hallucinated detail that pulls the embedding away
  from the true topic. Common in latency-sensitive production deployments
  that accept the variance trade-off.
- **Multi-sample averaged HyDE, the paper's configuration.** N=8
  hypothetical documents sampled at nonzero temperature, encoded
  independently, and averaged before search. The paper reports this
  averaging step measurably improves and stabilizes retrieval quality over
  single-sample generation, framing the average as implicitly canceling out
  document-specific hallucinated details while reinforcing shared topical
  signal.
- **Query-plus-hypothetical hybrid.** Some implementations concatenate the
  original query with the generated hypothetical passage before encoding, or
  average the query's own embedding into the final vector alongside the
  hypothetical document embeddings, trading some of the pure vocabulary
  bridging benefit for a guard against the generator drifting off-topic. This
  is a documented community variant, not part of the original paper's main
  method, and should be evaluated per corpus rather than assumed superior.
- **HyDE with reranking.** HyDE's output feeds a first-stage retrieval, and
  a separate cross-encoder reranker (see the reranking pattern used
  throughout the Advanced RAG family) reorders the top-k results using the
  original query, not the hypothetical document, as the reranker's query
  input. This combination separates the vocabulary-bridging job, HyDE, from
  the precision-refinement job, reranking.
- **Multilingual and cross-lingual HyDE.** The paper's own multilingual
  experiment uses mContriever and generates the hypothetical document in
  the target language, or in a pivot language, to bridge cross-lingual
  retrieval where labeled pairs across the language pair do not exist.
- **HyDE as a fallback tier, not the default path.** Given the added cost
  per query, several production systems run HyDE only when a first-pass
  standard dense or sparse retrieval returns low-confidence results
  (measured by score threshold or by an empty top-k above a similarity
  floor), reserving the generation call for the queries that actually need
  it.

## 9. Known production uses

- **LlamaIndex** ships HyDE as a first-class query transform, `HyDEQueryTransform`,
  documented in the framework's example notebook that wraps a retriever with
  the HyDE transform before running vector search
  (https://developers.llamaindex.ai/python/examples/query_transformations/hydequerytransformdemo/,
  verified 2026-08-02), directly citing the Gao et al. paper as the source of
  the technique.
- **LangChain** ships a `HypotheticalDocumentEmbedder` chain in its
  `langchain_classic` package, whose source implements the
  generate-then-embed-then-average flow from the original paper and names it
  "HyDE" from the Gao et al. paper
  (https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain_classic/chains/hyde/base.py,
  verified 2026-08-02).
- **Haystack** (deepset) documents HyDE as a retrieval-augmentation
  component in its cookbook, "Boosting Retrieval Performance with
  Hypothetical Document Embeddings (HyDE)"
  (https://haystack.deepset.ai/cookbook/using_hyde_for_improved_retrieval,
  verified 2026-08-02), implemented as a pipeline component that generates
  hypothetical answers with an LLM node before the embedding retriever node.
- The original paper's own evaluation, which counts as the first
  production-adjacent evidence of the technique's effect, reports results
  on TREC DL19, DL20, and the BEIR benchmark suite of eleven diverse
  retrieval datasets (covering domains from biomedical to financial to
  argument retrieval), plus a multilingual Mr.TyDi evaluation across eleven
  languages, and reports that HyDE using an unsupervised Contriever encoder
  matches or exceeds the fine-tuned DPR baseline's performance on several of
  those out-of-domain datasets without HyDE ever seeing a single relevance
  label from any of them (Gao et al., ACL 2023, Table 1 and Table 3,
  https://aclanthology.org/2023.acl-long.99/, verified 2026-08-02).

## 10. Consequences

Positive consequences observed and reported.

- Enables usable dense retrieval quality in genuinely zero-shot settings,
  with no labeled query-document pairs required for the target domain.
- Bridges vocabulary and register gaps between how users phrase questions
  and how a corpus states answers, in a way sparse retrieval structurally
  cannot.
- Requires no fine-tuning of the encoder, the generator, or any new model
  weights. It is a query-time technique layered on top of infrastructure
  most retrieval systems already have, a vector index and an LLM API.
- Composable with reranking, hybrid sparse-plus-dense retrieval, and
  standard RAG generation without architectural changes to those
  components.
- Multi-sample averaging reduces the practical impact of any single
  hallucinated or off-topic generation, which is the pattern's own answer
  to its central risk.

Negative consequences observed and reported.

- Adds one generator call, and with the paper's own multi-sample
  configuration, up to eight generator calls, on the critical path of every
  query, directly increasing latency and per-query dollar cost.
- Retrieval quality is bounded above by generator quality. A weak generator
  or a generator that refuses to speculate produces poor hypothetical
  documents and, downstream, poor retrieval.
- Introduces nondeterminism into retrieval results at nonzero sampling
  temperature, which complicates reproducibility, caching, and debugging
  compared to a standard deterministic dense retrieval lookup.
- On tasks that genuinely benefit from a fine-tuned in-domain encoder with
  available labels, HyDE is not a strict upgrade and can underperform a
  properly supervised retriever.
- Widens the prompt-injection surface, because the generator now processes
  and elaborates on arbitrary user-submitted queries as if answering them,
  which is a different trust boundary than a generator that only summarizes
  already-retrieved, vetted content (see Dimension 17).

## 11. Failure modes and misuse

**Fabricated specifics dominate the embedding.** Symptom. Retrieval returns
confidently wrong or off-topic documents for narrow factual queries, dates,
numeric values, part numbers. Cause. The hypothetical document fabricates a
specific wrong fact, a wrong date or a wrong number, and because contrastive
dense encoders often weight topical and lexical similarity more than exact
numeric correctness, the fabricated wrong value pulls the embedding toward
documents discussing that wrong value's topic rather than the query's actual
topic. Fix. Route queries that look like they need exact-match retrieval
(detected by regex for identifiers, part numbers, citation formats) around
HyDE entirely, straight to BM25 or exact-match lookup, and reserve HyDE for
genuinely open-ended natural-language queries.

**Uniform application without gating.** Symptom. Retrieval latency spikes
and cost grows without a matching quality gain that justifies it. Cause.
HyDE is applied uniformly to every query, including queries a standard dense
or sparse retriever would already answer well, so the extra generation call
is pure overhead on the majority of traffic. Fix. Gate HyDE behind a
confidence check on a first-pass standard retrieval, low top-k similarity
score or empty results, so the generation call fires only on the queries
that actually need vocabulary bridging.

**Nondeterministic results.** Symptom. Retrieval results are inconsistent
between identical repeated queries, and support or QA teams cannot reproduce
a reported bad result. Cause. Nonzero sampling temperature on the generator
means the hypothetical document, and therefore the search vector, differs
run to run. Fix. Cache the hypothetical document, or its averaged embedding,
keyed by the normalized query text, with an explicit time-to-live, so
repeated queries within the TTL window are deterministic and reproducible,
and log the generated hypothetical document alongside the ranked results so
a reported bad result can be diagnosed after the fact.

**Generator refuses to speculate.** Symptom. The generator refuses to
produce a hypothetical document, or produces a hedge such as "I don't have
enough information to answer this," instead of a plausible passage, and
retrieval quality on those queries is no better than embedding the raw
query. Cause. Many chat-tuned models are trained with safety and honesty
objectives that discourage confidently answering questions the model does
not actually know the answer to, which directly conflicts with what HyDE
needs the generator to do, produce a confident, on-topic, possibly wrong
answer. Fix. Use an explicit prompt instruction that tells the model this is
a retrieval aid, not a final answer, and that a plausible but potentially
inaccurate passage is expected and required, and fall back to the raw query
embedding when the generator's output is a refusal or is suspiciously short.

**Encoder mismatch between corpus and hypothetical document.** Symptom. The
corpus and the hypothetical documents are embedded with different models,
and retrieval quality is worse than the raw query baseline. Cause. HyDE's
mechanism depends entirely on the hypothetical document and the real corpus
sharing one embedding space. If a team upgrades the corpus's embedding model
but the HyDE pipeline still calls the old encoder, the averaged hypothetical
vector and the corpus vectors are no longer comparable, and results degrade
silently rather than erroring. Fix. Pin the encoder used for hypothetical
document embedding to the exact same model and version used to build the
corpus index, and treat any corpus re-embedding migration as requiring a
corresponding update to the HyDE embedding call in the same deployment.

## 12. Trade-off matrix

| Force | HyDE | Supervised Dense (DPR-style) | BM25 (sparse) | Multi-query expansion |
|---|---|---|---|---|
| Requires labeled training data | No | Yes | No | No |
| Bridges vocabulary/register gap | Strong | Strong, but only where labels exist | None | Moderate |
| Latency per query | High, one or more generation calls | Low, single embed | Very low | Moderate, multiple embeds, no generation |
| Cost per query | High, LLM call | Low | Very low | Moderate |
| Result determinism | Low, unless cached | High | High | High |
| Exact-term matching | Poor | Poor | Strong | Poor |
| Out-of-domain generalization | Strong | Weak without fine-tuning | Moderate, lexical only | Moderate |
| Requires an LLM at query time | Yes | No | No | Depends on expansion method |

Multi-query expansion, asking the same generator for several rephrasings of
the query, then embedding and searching each rephrasing separately or
merging their results, is the nearest sibling technique and the most useful
direct comparison, because it also uses a generator to bridge vocabulary,
but it expands the query side rather than manufacturing an answer, and so it
does not close the query-versus-document register gap that motivated HyDE in
the first place.

## 13. Related and incompatible patterns

- **Retrieval-Augmented Generation.** HyDE is a retrieval-stage technique
  that sits inside the retrieval component of a larger RAG pipeline. It
  changes how the retrieval query is formed. It does not change how
  retrieved documents are used in the generation step downstream. HyDE is
  never a replacement for RAG. It is an optional retrieval-quality upgrade
  inside one.
- **Advanced RAG, reranking and hybrid search.** HyDE composes naturally
  with a reranking stage. HyDE improves first-stage recall, and a
  cross-encoder reranker improves final precision on the smaller candidate
  set HyDE surfaces. It also composes with hybrid sparse-plus-dense search,
  where HyDE's dense-side query vector is combined with a standard BM25
  score on the same query.
- **Agentic RAG.** In an agentic retrieval loop where an agent decides
  when and how to retrieve, HyDE can be exposed as one of several retrieval
  strategies the agent selects based on query characteristics, invoked only
  when the agent judges the query needs vocabulary bridging.
- **GraphRAG.** HyDE and GraphRAG address different weaknesses in
  retrieval. HyDE bridges vocabulary and register mismatch in vector
  search, while GraphRAG addresses multi-hop and relational queries that no
  single embedded document can answer. They are not mutually exclusive. A
  hypothetical document could in principle be used to seed an initial
  entity or subgraph lookup in a graph-based retriever, though this
  combination is not part of either original paper and would need its own
  evaluation.
- **Self-Consistency.** HyDE's multi-sample averaging step is structurally
  similar in spirit to self-consistency's practice of sampling multiple
  reasoning paths and aggregating them, though self-consistency aggregates
  at the level of final answers via majority vote, while HyDE aggregates at
  the level of embedding vectors via arithmetic mean. The two patterns are
  not the same mechanism but share the underlying intuition that averaging
  over several independent samples cancels idiosyncratic error while
  reinforcing shared signal.
- **Incompatible with exact-match or citation-lookup retrieval.** Any
  retrieval task whose correctness depends on exact literal matching, legal
  citations, part numbers, SKUs, hash values, is actively harmed by HyDE,
  because the hypothetical document introduces paraphrase and fabricated
  specifics exactly where the task needs literal fidelity. No documented
  combination reconciles this. The correct answer is to route such queries
  around HyDE entirely.

## 14. Refactoring path in and out

Introducing HyDE into an existing dense-retrieval system follows this path.

1. Confirm the existing retrieval pipeline already has a working vector
   index built from a contrastive dense encoder, with real documents
   pre-embedded. HyDE requires this infrastructure to already exist. It
   adds a step before search, not a new index.
2. Add a generation step ahead of the existing embed-and-search call. Start
   with a single hypothetical document, N=1, and a plain instruction
   prompt, "Write a passage that answers the following question." Verify
   the plumbing end to end before adding multi-sample averaging.
3. Confirm the encoder used to embed the hypothetical document is
   identical, including model version, to the encoder that built the
   corpus index. This is the single most common integration bug (see
   Dimension 11).
4. Measure retrieval quality, recall at k, or a task-specific metric, on a
   held-out set of representative queries, comparing raw-query embedding
   against single-sample HyDE, before deciding whether the added latency is
   justified.
5. If the single-sample result is promising but noisy, add multi-sample
   generation and the averaging step, tuning N against the latency and cost
   budget. The paper's own N=8 default is a starting point, not a fixed
   requirement.
6. Add a caching layer keyed on normalized query text, and a fallback to
   raw-query embedding when the generator returns a refusal, an empty
   string, or an error, so the retrieval path degrades gracefully rather
   than failing outright.
7. Consider gating HyDE behind a confidence check on a first-pass standard
   retrieval, rather than running it on every query, once production
   traffic patterns show which queries actually need it.

Removing HyDE once it stops earning its place follows this path.

1. This most commonly happens once enough real query-document interaction
   data accumulates to fine-tune a supervised or weakly supervised in-domain
   encoder, at which point the fine-tuned encoder's in-domain precision can
   exceed what HyDE's zero-shot vocabulary bridging achieves, per the
   original paper's own comparison against fine-tuned DPR.
2. Before removing HyDE, run the same held-out query set used at
   introduction time against the candidate replacement, so the removal
   decision is based on a measured regression risk, not an assumption that
   the new encoder is automatically better on every query type HyDE was
   covering.
3. Remove the generation call and the averaging step, restoring the direct
   raw-query-to-embedding path, and remove the hypothetical-document cache
   once traffic confirms no fallback dependency remains on it.
4. Keep the confidence-gating logic if it exists. A fallback path for
   low-confidence queries remains useful even after swapping in a stronger
   default retriever, and can be repointed at the new encoder's own
   fallback strategy rather than being deleted outright.

## 15. Testing and verification

HyDE is easier to test than it looks, because its two stages, generation and
embedding-plus-search, can be tested independently before being tested
together.

- **Test the generator prompt in isolation.** Assert that, for a
  representative sample of queries, the generator returns a non-empty,
  on-topic passage rather than a refusal or a meta-commentary such as
  "As an AI, I cannot." This is a pure prompt-engineering test and does not
  require the retrieval infrastructure at all.
- **Test encoder consistency.** Assert, as a unit test, that the encoder
  instance and model version used to embed hypothetical documents is
  identical to the one used to build the corpus index. This directly
  guards against the most common production failure mode (Dimension 11).
- **Test the averaging math independently of the model.** Given a fixed set
  of N mock embedding vectors, no LLM call involved, assert that the
  averaging step produces the arithmetic mean, and that the resulting
  vector is used, unmodified, as the search query. This makes the
  aggregation logic testable without any network call or model
  nondeterminism.
- **Test end-to-end retrieval quality on a golden query set, not just
  wiring.** Build a small held-out set of representative queries with known
  relevant documents, even ten to twenty queries is useful, and track
  recall at k for raw-query retrieval versus HyDE retrieval as a regression
  metric, so a prompt change, a generator swap, or an encoder upgrade that
  degrades HyDE's benefit is caught before it reaches production.
- **Use a fixed seed or a mocked generator for deterministic CI runs.**
  Because the generator is nondeterministic at nonzero temperature, CI
  tests that need to be reproducible should mock the generator call with a
  fixed set of canned hypothetical documents rather than calling a live,
  temperature-sampled model in the test suite. Live-model evaluation
  belongs in a separate, periodically-run quality benchmark, not in the
  fast unit test path.
- **Test the fallback path explicitly.** Simulate a generator refusal,
  timeout, and empty response, and assert the system falls back to raw
  query embedding rather than sending an empty or malformed vector into
  the search index.

## 16. Observability signals

- **Generation latency and error rate, tracked separately from search
  latency.** Because HyDE adds a distinct network hop before the existing
  search call, dashboards should break out hypothetical document generation
  time as its own span, distinct from vector search time, so a latency
  regression can be attributed to the correct stage.
- **Generator refusal or fallback rate.** The fraction of queries where the
  generator returned a refusal, an empty response, or an error and the
  system fell back to raw-query embedding. A rising trend here signals a
  generator, prompt, or model-version regression worth investigating before
  it silently erodes retrieval quality.
- **Per-query cost, attributed to the generation call.** Since the
  generation call is billed per token by most hosted model providers, cost
  dashboards should track the marginal cost HyDE adds per search, separate
  from embedding and vector-index infrastructure cost, so the trade-off
  named in Dimension 3 stays visible to whoever owns the budget.
- **Retrieval quality metric, recall at k or click-through on top-k
  results, broken out by whether HyDE fired or the query fell back to
  raw-query embedding.** This is the signal that answers whether HyDE is
  actually earning its cost, and it should be tracked continuously, not
  only at introduction time, because corpus drift or generator model
  changes can erode the benefit silently.
- **Cache hit rate, if hypothetical document caching is in place.** A low
  hit rate on a high-repeat query stream suggests the cache key
  normalization is too strict, for example not normalizing whitespace or
  casing, and the system is paying for redundant generation calls.
- **Sampled logging of the generated hypothetical document alongside the
  final ranked results, for a percentage of production queries.** This is
  the single most useful debugging artifact when a user or support team
  reports an unexpected retrieval result, because it lets an engineer see
  exactly what fabricated passage steered the search.

## 17. Security and privacy implications

HyDE asks a generator to produce a plausible, confident passage in response
to arbitrary user-submitted query text, which changes the trust posture of
that generation call compared to a generator that only summarizes
already-retrieved, vetted content.

**Prompt injection surface.** A user query is, by construction, fed directly
into a generation prompt whose entire purpose is to have the model elaborate
on it. A malicious query crafted to manipulate the generator into producing
harmful, biased, or policy-violating content is a more direct injection
vector here than in a pipeline where the generator only ever sees
already-filtered retrieved documents. Prompt templates used for HyDE should
be reviewed under the same threat model as any other user-input-to-generator
boundary, and the same input sanitization and output filtering that would be
applied to a user-facing chat completion should be applied to the
hypothetical document generation call, since that generated text, while not
shown directly to the user, does influence what real documents the user
ultimately sees.

**Data leakage through the generator, if the generator is a hosted
third-party API.** Every query sent to the generator for hypothetical
document generation is, by definition, sent to whatever model provider
hosts that generator, which is an additional egress point for potentially
sensitive query text beyond whatever egress already exists for the corpus's
own embedding calls. In regulated domains, health records, legal discovery,
financial queries, this means HyDE introduces a second third-party
data-processing relationship, the generator provider, in addition to the
encoder provider, and both need to be covered by the same data-processing
agreements and residency requirements that already govern the retrieval
system.

**Fabricated content is never surfaced to the end user, which limits but
does not eliminate risk.** Because the hypothetical document is used only to
steer the search vector and the final response returns real, retrieved
documents, HyDE does not directly put hallucinated text in front of users
the way an ungrounded chatbot answer would. The residual risk is indirect. A
fabricated hypothetical document that happens to align with an unintended or
sensitive topic can shift retrieval toward documents on that topic, which is
a subtler and harder-to-audit failure mode than a directly visible
hallucination, and is the reason sampled logging of hypothetical documents
(Dimension 16) matters as a security and quality auditing tool, not only a
debugging one.

**No new data is written to the corpus.** HyDE does not persist the
hypothetical documents into the searchable index. They exist only for the
duration of a single query's embedding step, unless a team explicitly adds
caching (Dimension 8), in which case the cache itself becomes a new data
store holding model-generated text keyed by user query, and should be
subject to the same retention and access-control policy as any other store
of derived user query data.

## Code examples

Three languages, chosen to cover the shapes HyDE actually gets built in.
Python and TypeScript are the two languages the reference implementations
(LlamaIndex and LangChain, Dimension 9) ship in, and Go represents a
lower-level, dependency-free service implementation, the shape a team
reaches for when building a bespoke retrieval microservice rather than
using a framework. Every example replaces the real generator and the real
contrastive encoder with small, deterministic, dependency-free stand-ins,
so the code runs with no network access and no API key while preserving
the exact data flow of the pattern. generate N hypothetical documents,
encode each one with the same encoder used to build the corpus index,
average the vectors, then search the corpus with the averaged vector. Swap
`generateHypotheticalDocuments` (or its Python and Go equivalents) for a
real call to an instruction-following model, and swap `encode` for a real
call to a contrastive dense encoder such as Contriever or OpenAI's text
embedding API, and the shape is a production HyDE pipeline.

### Python

```python
"""A runnable simulation of the HyDE retrieval flow.
The generator and encoder here are deterministic stand-ins for a real LLM
and a real contrastive encoder, so the example runs with no network access
and no API key, while preserving the exact shape of the pattern. generate,
encode each hypothetical document, average the vectors, then search a real
corpus with the averaged vector."""

import hashlib
import math
import re
from collections import Counter

CORPUS = {
    "doc_methane": "Methane boils at negative 161.5 degrees Celsius at one atmosphere of pressure.",
    "doc_ethane": "Ethane boils at negative 88.5 degrees Celsius at standard pressure.",
    "doc_recipe": "Preheat the oven to 200 degrees and bake the bread for 40 minutes.",
}


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def encode(text, dims=64):
    """A deterministic bag-of-words hashing encoder, standing in for a
    real contrastive dense encoder such as Contriever. Every call with the
    same text produces the same vector, and the corpus and the
    hypothetical documents share this exact function, which is the one
    invariant HyDE depends on."""
    vector = [0.0] * dims
    counts = Counter(tokenize(text))
    for token, count in counts.items():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = digest[0] % dims
        vector[index] += float(count)
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def generate_hypothetical_documents(query, n=3):
    """A deterministic stand-in for an instruction-following generator.
    A real system replaces this with a call to a language model prompted
    to write a passage that answers the query. Each of the n samples here
    is a plausible but not necessarily correct paraphrase of the query,
    matching the register of the target corpus."""
    templates = [
        "The substance boils at some number of degrees Celsius at one atmosphere of pressure.",
        "At standard pressure, the boiling point is measured in degrees Celsius below zero.",
        "This compound boils at a low temperature in degrees Celsius under one atmosphere.",
    ]
    return [templates[i % len(templates)] for i in range(n)]


def average(vectors):
    dims = len(vectors[0])
    summed = [0.0] * dims
    for vector in vectors:
        for i, value in enumerate(vector):
            summed[i] += value
    return [value / len(vectors) for value in summed]


def hyde_search(query, corpus, top_k=1, n_samples=3):
    hypothetical_documents = generate_hypothetical_documents(query, n_samples)
    hypothetical_vectors = [encode(doc) for doc in hypothetical_documents]
    query_vector = average(hypothetical_vectors)

    scored = []
    for doc_id, text in corpus.items():
        score = cosine(query_vector, encode(text))
        scored.append((score, doc_id))
    scored.sort(reverse=True)
    return scored[:top_k]


def raw_query_search(query, corpus, top_k=1):
    """The baseline the pattern is compared against. embed the raw query
    directly, with no generation step."""
    query_vector = encode(query)
    scored = []
    for doc_id, text in corpus.items():
        score = cosine(query_vector, encode(text))
        scored.append((score, doc_id))
    scored.sort(reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    query = "What is the boiling point of methane?"

    hyde_result = hyde_search(query, CORPUS, top_k=2)
    raw_result = raw_query_search(query, CORPUS, top_k=2)

    print("HyDE top results:", hyde_result)
    print("Raw query top results:", raw_result)

    assert hyde_result[0][1] == "doc_methane", "HyDE should rank the methane document first"
    print("HyDE ranked the correct document first, as expected.")
```

### TypeScript

```typescript
// A runnable simulation of the HyDE retrieval flow. The generator and
// encoder here are deterministic stand-ins for a real LLM and a real
// contrastive encoder, so the example runs with no network access and no
// API key, while preserving the exact shape of the pattern.

type Vector = number[];

const CORPUS: Record<string, string> = {
  doc_methane:
    "Methane boils at negative 161.5 degrees Celsius at one atmosphere of pressure.",
  doc_ethane:
    "Ethane boils at negative 88.5 degrees Celsius at standard pressure.",
  doc_recipe:
    "Preheat the oven to 200 degrees and bake the bread for 40 minutes.",
};

const DIMS = 64;

function tokenize(text: string): string[] {
  return text.toLowerCase().match(/[a-z0-9]+/g) ?? [];
}

function hashToken(token: string): number {
  // A small FNV-1a style hash. Deterministic across runs, no external
  // dependency, and good enough to spread tokens across DIMS buckets.
  let hash = 2166136261;
  for (let i = 0; i < token.length; i++) {
    hash ^= token.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return Math.abs(hash) % DIMS;
}

function encode(text: string): Vector {
  const vector = new Array<number>(DIMS).fill(0);
  for (const token of tokenize(text)) {
    vector[hashToken(token)] += 1;
  }
  const norm = Math.sqrt(vector.reduce((sum, v) => sum + v * v, 0)) || 1;
  return vector.map((v) => v / norm);
}

function cosine(a: Vector, b: Vector): number {
  return a.reduce((sum, value, i) => sum + value * b[i], 0);
}

function average(vectors: Vector[]): Vector {
  const dims = vectors[0].length;
  const summed = new Array<number>(dims).fill(0);
  for (const vector of vectors) {
    for (let i = 0; i < dims; i++) {
      summed[i] += vector[i];
    }
  }
  return summed.map((value) => value / vectors.length);
}

function generateHypotheticalDocuments(_query: string, n = 3): string[] {
  // A deterministic stand-in for an instruction-following generator. A
  // real system replaces this with a call to a language model prompted
  // to write a passage that answers the query, matching the register of
  // the target corpus.
  const templates = [
    "The substance boils at some number of degrees Celsius at one atmosphere of pressure.",
    "At standard pressure, the boiling point is measured in degrees Celsius below zero.",
    "This compound boils at a low temperature in degrees Celsius under one atmosphere.",
  ];
  return Array.from({ length: n }, (_, i) => templates[i % templates.length]);
}

function hydeSearch(
  query: string,
  corpus: Record<string, string>,
  topK = 2,
  nSamples = 3
): [number, string][] {
  const hypotheticalDocuments = generateHypotheticalDocuments(query, nSamples);
  const hypotheticalVectors = hypotheticalDocuments.map(encode);
  const queryVector = average(hypotheticalVectors);

  const scored: [number, string][] = Object.entries(corpus).map(
    ([docId, text]) => [cosine(queryVector, encode(text)), docId]
  );
  scored.sort((a, b) => b[0] - a[0]);
  return scored.slice(0, topK);
}

function rawQuerySearch(
  query: string,
  corpus: Record<string, string>,
  topK = 2
): [number, string][] {
  // The baseline the pattern is compared against. Embed the raw query
  // directly, with no generation step.
  const queryVector = encode(query);
  const scored: [number, string][] = Object.entries(corpus).map(
    ([docId, text]) => [cosine(queryVector, encode(text)), docId]
  );
  scored.sort((a, b) => b[0] - a[0]);
  return scored.slice(0, topK);
}

function main(): void {
  const query = "What is the boiling point of methane?";

  const hydeResult = hydeSearch(query, CORPUS);
  const rawResult = rawQuerySearch(query, CORPUS);

  console.log("HyDE top results:", hydeResult);
  console.log("Raw query top results:", rawResult);

  if (hydeResult[0][1] !== "doc_methane") {
    throw new Error("HyDE should rank the methane document first");
  }
  console.log("HyDE ranked the correct document first, as expected.");
}

main();
```

### Go

```go
// Package main is a runnable simulation of the HyDE retrieval flow. The
// generator and encoder here are deterministic stand-ins for a real LLM
// and a real contrastive encoder, so the example runs with no network
// access and no API key, while preserving the exact shape of the pattern.
package main

import (
	"fmt"
	"hash/fnv"
	"math"
	"regexp"
	"sort"
	"strings"
)

const dims = 64

var corpus = map[string]string{
	"doc_methane": "Methane boils at negative 161.5 degrees Celsius at one atmosphere of pressure.",
	"doc_ethane":  "Ethane boils at negative 88.5 degrees Celsius at standard pressure.",
	"doc_recipe":  "Preheat the oven to 200 degrees and bake the bread for 40 minutes.",
}

var tokenPattern = regexp.MustCompile(`[a-z0-9]+`)

func tokenize(text string) []string {
	return tokenPattern.FindAllString(strings.ToLower(text), -1)
}

func encode(text string) []float64 {
	vector := make([]float64, dims)
	for _, token := range tokenize(text) {
		h := fnv.New32a()
		h.Write([]byte(token))
		vector[h.Sum32()%dims]++
	}
	var sumSquares float64
	for _, v := range vector {
		sumSquares += v * v
	}
	norm := math.Sqrt(sumSquares)
	if norm == 0 {
		norm = 1
	}
	for i := range vector {
		vector[i] /= norm
	}
	return vector
}

func cosine(a, b []float64) float64 {
	var sum float64
	for i := range a {
		sum += a[i] * b[i]
	}
	return sum
}

func average(vectors [][]float64) []float64 {
	result := make([]float64, len(vectors[0]))
	for _, vector := range vectors {
		for i, v := range vector {
			result[i] += v
		}
	}
	for i := range result {
		result[i] /= float64(len(vectors))
	}
	return result
}

// generateHypotheticalDocuments is a deterministic stand-in for an
// instruction-following generator. A real system replaces this with a
// call to a language model prompted to write a passage that answers the
// query, matching the register of the target corpus.
func generateHypotheticalDocuments(query string, n int) []string {
	_ = query
	templates := []string{
		"The substance boils at some number of degrees Celsius at one atmosphere of pressure.",
		"At standard pressure, the boiling point is measured in degrees Celsius below zero.",
		"This compound boils at a low temperature in degrees Celsius under one atmosphere.",
	}
	docs := make([]string, n)
	for i := 0; i < n; i++ {
		docs[i] = templates[i%len(templates)]
	}
	return docs
}

type scoredDoc struct {
	score float64
	docID string
}

func hydeSearch(query string, corpus map[string]string, topK int, nSamples int) []scoredDoc {
	hypotheticalDocs := generateHypotheticalDocuments(query, nSamples)
	vectors := make([][]float64, len(hypotheticalDocs))
	for i, doc := range hypotheticalDocs {
		vectors[i] = encode(doc)
	}
	queryVector := average(vectors)

	var scored []scoredDoc
	for docID, text := range corpus {
		scored = append(scored, scoredDoc{cosine(queryVector, encode(text)), docID})
	}
	sort.Slice(scored, func(i, j int) bool { return scored[i].score > scored[j].score })
	if len(scored) > topK {
		scored = scored[:topK]
	}
	return scored
}

// rawQuerySearch is the baseline the pattern is compared against. Embed
// the raw query directly, with no generation step.
func rawQuerySearch(query string, corpus map[string]string, topK int) []scoredDoc {
	queryVector := encode(query)
	var scored []scoredDoc
	for docID, text := range corpus {
		scored = append(scored, scoredDoc{cosine(queryVector, encode(text)), docID})
	}
	sort.Slice(scored, func(i, j int) bool { return scored[i].score > scored[j].score })
	if len(scored) > topK {
		scored = scored[:topK]
	}
	return scored
}

func main() {
	query := "What is the boiling point of methane?"

	hydeResult := hydeSearch(query, corpus, 2, 3)
	rawResult := rawQuerySearch(query, corpus, 2)

	fmt.Println("HyDE top results:", hydeResult)
	fmt.Println("Raw query top results:", rawResult)

	if hydeResult[0].docID != "doc_methane" {
		panic("HyDE should rank the methane document first")
	}
	fmt.Println("HyDE ranked the correct document first, as expected.")
}
```

## 18. References

1. Luyu Gao, Xueguang Ma, Jimmy Lin, and Jamie Callan. "Precise Zero-Shot
   Dense Retrieval without Relevance Labels". Proceedings of the 61st
   Annual Meeting of the Association for Computational Linguistics (Volume
   1, Long Papers), 2023, pages 1762 to 1777.
   https://aclanthology.org/2023.acl-long.99/ (verified 2026-08-02)
2. Luyu Gao, Xueguang Ma, Jimmy Lin, and Jamie Callan. "Precise Zero-Shot
   Dense Retrieval without Relevance Labels". arXiv preprint, first posted
   December 2022. https://arxiv.org/abs/2212.10496 (verified 2026-08-02)
3. Vladimir Karpukhin, Barlas Oguz, Sewon Min, Patrick Lewis, Ledell Wu,
   Sergey Edunov, Danqi Chen, and Wen-tau Yih. "Dense Passage Retrieval for
   Open-Domain Question Answering". Proceedings of EMNLP 2020.
   https://arxiv.org/abs/2004.04906 (verified 2026-08-02)
4. Gautier Izacard, Mathilde Caron, Lucas Hosseini, Sebastian Riedel,
   Piotr Bojanowski, Armand Joulin, and Edouard Grave. "Unsupervised Dense
   Information Retrieval with Contrastive Learning" (the Contriever paper).
   https://arxiv.org/abs/2112.09118 (verified 2026-08-02)
5. LlamaIndex. `HyDEQueryTransform` example notebook, query transformations
   documentation. https://developers.llamaindex.ai/python/examples/query_transformations/hydequerytransformdemo/
   (verified 2026-08-02)
6. LangChain. `HypotheticalDocumentEmbedder` chain source, `langchain_classic`
   package. https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain_classic/chains/hyde/base.py
   (verified 2026-08-02)
7. Haystack (deepset). "Boosting Retrieval Performance with Hypothetical
   Document Embeddings (HyDE)". Cookbook.
   https://haystack.deepset.ai/cookbook/using_hyde_for_improved_retrieval
   (verified 2026-08-02)
8. Sean MacAvaney, Nicola Tonellotto, and Craig Macdonald. "Reproducibility,
   Replicability, and Insights into Dense Multi-Representation Retrieval
   Models. from ColBERT to Col*". Discussing the lineage from classical
   pseudo-relevance feedback into dense retrieval query expansion.
   https://arxiv.org/abs/2110.06051 (verified 2026-08-02)
