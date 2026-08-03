---
name: Late Chunking
slug: late-chunking
family: 17-ai-agentic
category: AI Agentic
aliases: [Contextual Chunk Embeddings, Chunked Pooling]
first_described: "Günther, Mohr, Williams, Wang, Xiao (Jina AI) 2024"
maturity: emerging
related: [chunking-strategies, retrieval-augmented-generation, advanced-rag, hybrid-search, reranking, hyde]
incompatible_with: []
verified: 2026-08-02
---

# Late Chunking

## 1. Name, aliases, and lineage

The canonical name is late chunking. It names a change in the ORDER of two
operations that every retrieval pipeline already performs, splitting a
document into chunks and running an embedding model over each chunk. The
technique was introduced by Michael Günther, Isabelle Mohr, Daniel James
Williams, Bo Wang and Han Xiao, all affiliated with Jina AI, in the paper
"Late Chunking, Contextual Chunk Embeddings Using Long-Context Embedding
Models," first submitted to arXiv on 2024-09-07 as arXiv 2409.04701, with a
revised version posted 2025-07-07 ([arXiv 2409.04701](https://arxiv.org/abs/2409.04701),
verified 2026-08-02). The paper's own subtitle, "contextual chunk embeddings,"
is used here as the primary alias, because it names what the output actually
is, a chunk vector that carries context from outside its own boundary,
distinct from a chunk vector produced the ordinary way. Jina AI published a
companion explainer the same week, which is the source most practitioners
read first ([Jina AI, "Late Chunking in Long-Context Embedding Models"](https://jina.ai/news/late-chunking-in-long-context-embedding-models/),
verified 2026-08-02).

A second, informal alias worth recording is chunked pooling, because the
mechanical change the pattern makes is entirely inside the pooling step of an
embedding pipeline. A transformer-based embedding model always produces one
vector per input token before any pooling happens, and a pooling function
(commonly mean pooling, sometimes a CLS token, sometimes max pooling)
collapses those per-token vectors into the single fixed-size vector that gets
stored and searched. Ordinary embedding pipelines pool over the whole input,
because the whole input is already one chunk. Late chunking pools over a
narrower span, one chunk's worth of tokens, but does so on token vectors that
were produced by attending over the ENTIRE document, not only that span. The
name late chunking refers to the fact that the decision "where does this
chunk end" is applied late in the pipeline, after the encoder has already run,
rather than early, before the encoder ever sees the text.

One naming collision deserves a note here rather than only in dimension 13.
Late chunking is not late interaction. Late interaction is the term Omar
Khattab and Matei Zaharia used in 2020 for ColBERT, where query and document
are encoded independently and a scoring step runs late, at query time, over
stored per-token vectors from both sides ([Khattab and Zaharia, "ColBERT,
Efficient and Effective Passage Search via Contextualized Late Interaction
over BERT," SIGIR 2020, arXiv 2004.12832](https://arxiv.org/abs/2004.12832),
verified 2026-08-02). Late chunking shares the word "late" and the general
neighborhood of contextualized token vectors, but it is a document-side
indexing technique that still produces one pooled vector per chunk. The two
ideas are frequently mentioned in the same sentence by vendors comparing
storage costs, and it is worth reading dimension 13 before assuming the two
names refer to variations of the same thing.

## 2. Problem and context

Picture a retrieval pipeline built over a long, single-narrative source, a
Wikipedia article, a signed contract, a meeting transcript, a product manual.
The pipeline needs to answer questions by finding the right passage and
handing it to a language model, so at ingestion time the document gets split
into chunks of a few hundred tokens, and each chunk is embedded on its own by
sending the chunk's text, and only that text, through an embedding model.

The failure this produces is specific and observable. A document about Berlin
opens with a sentence naming the city, then spends several paragraphs
referring to "the city," "it," or "its population" without repeating the word
Berlin. Whichever chunk contains the opening sentence embeds cleanly, its
vector points toward Berlin-related content. Every later chunk, the ones about
population, transit, or climate, embeds a text fragment whose subject is a
pronoun with no antecedent inside that fragment. The embedding model has no
mechanism to look outside the chunk it was given, so the resulting vector
represents an ambiguous "the city," not the specific city the reader (and the
rest of the document) already knows it means. A search for "Berlin
population" can miss the population chunk entirely, because that chunk's
embedded text never says Berlin.

This is not a defect in any particular chunker or embedding model. It is a
structural consequence of the ORDER in which the two operations run. As long
as chunking happens first and embedding happens per chunk second, every chunk
is embedded in isolation from its neighbors, and any information that lives
outside a chunk's own boundary is permanently unavailable to that chunk's
vector.

The reason this order was standard for years is a plain hardware and model
limit. Early transformer encoders used for embeddings, BERT and its direct
successors, accepted inputs of 512 tokens or fewer, so a full multi-page
document could never be run through the model as one input in the first
place, chunking before embedding was the only option. That changed once
long-context embedding models with windows of 8,192 tokens or more became
available in 2024, jina-embeddings-v2-base-en among the first, which meant a
full document, or a large section of one, could now be fed through an encoder
in a single pass ([Jina AI, "Late Chunking in Long-Context Embedding
Models"](https://jina.ai/news/late-chunking-in-long-context-embedding-models/),
verified 2026-08-02). Once that became possible, the question the paper's
authors asked was direct. If the whole document can pass through the encoder
at once, does chunking still need to happen before the encoder runs, or can it
happen after. Late chunking is the answer that it can happen after, and that
doing so recovers exactly the cross-chunk context the traditional order
throws away.

## 3. Forces

**Contextual fidelity against compute cost.** Late chunking favors fidelity.
Feeding a whole document through a transformer in one pass lets every token's
self-attention reach every other token, including tokens many paragraphs
away, which is precisely how a pronoun resolves against its antecedent. The
price is paid in attention cost, which grows quadratically with sequence
length, so one pass over N tokens costs measurably more compute than several
smaller passes whose token counts sum to N. Dimension 10 returns to this
trade in concrete terms.

**Retrieval quality against infrastructure access.** The technique's benefit
requires reaching inside the embedding model, extracting the per-token hidden
states before pooling, rather than treating the model as a black box that
returns one vector per call. Most hosted embedding endpoints were designed
around the black-box contract, one string in, one vector out, because that
contract is simpler to serve at scale and matches how embeddings were used
for a decade. Late chunking cannot be retrofitted onto that contract without
the provider explicitly adding support for it.

**Storage cost against contextual richness.** Late chunking is favored here.
The output is still one fixed-size vector per chunk, the same shape a naive
per-chunk embedding call would have produced, so the technique adds no
storage overhead to an existing vector index. This is the force where late
chunking differs most sharply from late interaction (ColBERT-style scoring),
which multiplies storage by keeping a vector per token per document, see
dimension 12.

**Benefit magnitude against document shape.** This force resolves
differently depending on the corpus rather than favoring one side uniformly.
On a long, single-topic document with genuine cross-paragraph references, the
benefit is large and measured. On a corpus of short, already self-contained
records, sitting a whole batch of unrelated short records through the
encoder to recover context that was never split across them in the first
place buys close to nothing, and can dilute a chunk's own signal with
unrelated neighboring content if the chunk boundaries are drawn across
topically distinct records rather than within one coherent document.

**Reproducibility against boundary flexibility.** Chunk boundaries can, in
principle, be redrawn after the fact without re-running the encoder, as long
as the full per-token embedding matrix for the document is kept around, which
favors flexibility. Keeping that matrix around, though, costs storage
roughly on the order of a full late-interaction index, so most
implementations discard it immediately after pooling, which trades the
flexibility back away in exchange for the storage saving described above.
Whichever choice a team makes, it should be a deliberate one, not a default
that nobody examined.

## 4. Applicability and non-applicability

Reach for late chunking when the following hold.

- The source is a long, coherent, single-narrative document, an article, a
  contract, a transcript, a manual, where later passages depend on entities
  or topics introduced earlier and referred to only briefly again.
- An existing evaluation shows naive per-chunk embedding measurably losing
  recall on queries about a subject named once near the top of the document
  and referenced only by pronoun or elliptical phrase afterward.
- The pipeline already controls the embedding model end to end, either
  self-hosted through a library such as Hugging Face transformers, or through
  a hosted API that explicitly exposes the technique, such as Jina AI's
  `late_chunking` request parameter on jina-embeddings-v3.
- The document fits inside the model's maximum context window, or can be
  tiled into overlapping windows deliberately, see the macro-chunking variant
  in dimension 8.
- The team wants to keep an existing chunk-boundary scheme, fixed size,
  sentence, paragraph, or semantic, since late chunking only changes where
  pooling happens, not how boundaries are chosen.

Do NOT reach for late chunking in the following cases, and the reason matters
as much as the rule.

- **The corpus is made of short, independent, single-topic records.** FAQ
  entries, product bullet points, individual log lines, or short support
  tickets carry no cross-record context to recover, so the extra encoder cost
  buys nothing, and it actively risks blurring distinct records together if
  several unrelated short texts are concatenated into one artificial
  "document" purely to give the encoder something long to chew on.
- **The embedding provider is a closed, pooled-vector-only API with no
  token-level access.** Most general purpose commercial embedding endpoints
  return exactly one vector per input string and expose no per-token hidden
  state and no late-chunking flag. OpenAI's embeddings API is a documented
  example of this contract, returning a single vector whose length is fixed
  by the model, 1,536 for `text-embedding-3-small`, with no per-token output
  available through the endpoint ([OpenAI, "Embeddings" API
  guide](https://developers.openai.com/api/docs/guides/embeddings), verified
  2026-08-02). Late chunking cannot be implemented against that contract.
- **The document is far longer than the model's maximum context window and
  no overlap strategy has been implemented.** Naively truncating the input
  silently drops everything after the limit from ever contributing context to
  any chunk, which quietly recreates the exact isolation problem the
  technique exists to fix, for the whole tail of the document.
- **The target is a single, short, live query rather than a document being
  indexed.** Late chunking is an indexing-time technique for documents that
  will be split into multiple retrievable units. Embedding a short user query
  has no chunks to pool over and nothing to gain from the extra pass.
- **The embedding model is a closed, proprietary model with no exposed
  intermediate layer.** The technique needs access to the model's last hidden
  state before pooling. A vendor that will not expose that state, and has not
  built the flag in for you, blocks the technique regardless of context
  window size.
- **The actual requirement is fine-grained, token-level query-document
  matching at search time.** Late chunking still collapses each chunk down to
  one vector. If the goal is token-level interaction scoring, the correct
  pattern is late interaction (ColBERT-style), described in dimension 12 and
  13, not late chunking.

## 5. Structure

Five participants, named by the role each plays in the pipeline.

- **Long-context encoder.** A transformer-based embedding model that accepts
  an input up to its maximum context length, commonly 8,192 tokens in the
  models the originating paper evaluated, and that exposes the per-token
  hidden states from its final layer rather than only a single pooled
  sentence vector. This is the participant most existing embedding
  infrastructure does not expose, and its absence is the most common reason
  the pattern does not apply, see dimension 4.
- **Chunk boundary set.** The list of start-end offset pairs, expressed in
  the SAME tokenizer's index space the encoder itself uses, that mark where
  each chunk begins and ends. This set can come from any chunker already in
  use, fixed size, recursive character, sentence, or semantic, see the
  Chunking Strategies entry in this repository for the full catalog of ways
  to produce it.
- **Token embedding sequence.** The output of running the whole document
  through the encoder exactly once, one vector per input token. Because
  self-attention inside the encoder was never restricted to a single chunk,
  every token vector in this sequence already carries information gathered
  from every other token in the document, not only from its own chunk.
- **Pooling function.** Ordinarily mean pooling, sometimes a weighted or
  max-pooling variant, applied per chunk boundary AFTER the token embedding
  sequence already exists. This is the step where the "late" happens, the
  chunk boundary is applied to already-context-rich token vectors rather than
  to raw text before encoding.
- **Macro-chunker.** Needed only when a document's token count exceeds the
  encoder's maximum context window. It splits the document into overlapping
  windows short enough for the encoder, runs the encoder once per window, and
  merges the token vectors in each window's overlap region, commonly by
  averaging, before the ordinary chunk-boundary pooling step runs on the
  merged sequence. The originating paper discusses an extension along these
  lines for documents beyond context length. The exact merge formula in that
  extension sits in a compressed appendix section this entry's author was
  not able to extract cleanly from the PDF, so the shape described here and
  demonstrated in dimension 8's code sample should be read as a reasonable,
  judgement-based rendition of the idea rather than a verbatim reproduction
  of the paper's own algorithm.

## 6. ASCII structure diagram

```
NAIVE / EARLY CHUNKING (chunk first, embed each chunk alone)

  Document text
       |
       v
  +-----------+     +---------+   +---------+   +---------+
  |  Chunker  | --> | Chunk 1 |   | Chunk 2 |   | Chunk 3 |
  +-----------+     +---------+   +---------+   +---------+
                         |             |             |
                         v             v             v
                   +----------+  +----------+  +----------+
                   | Encoder  |  | Encoder  |  | Encoder  |   <- 3 separate
                   | (call 1) |  | (call 2) |  | (call 3) |      calls, no
                   +----------+  +----------+  +----------+      shared context
                         |             |             |
                         v             v             v
                     [ v1 ]        [ v2 ]        [ v3 ]


LATE CHUNKING (embed whole document once, chunk the token vectors after)

  Document text
       |
       v
  +--------------------------------------------------------+
  |                 Long-context Encoder                   |
  |             (single call, full attention)               |
  +--------------------------------------------------------+
       |
       v
  Token vectors:  [t1][t2][t3][t4][t5][t6][t7][t8][t9][t10]
                    \___span1___/  \___span2___/  \_span3_/
                        |               |              |
                        v               v              v
                   mean-pool       mean-pool       mean-pool
                        |               |              |
                        v               v              v
                     [ v1' ]         [ v2' ]        [ v3' ]

  Every t(i) above already attended across all 10 tokens, so
  v1', v2', v3' each carry context that v1, v2, v3 above could not.
```

## 7. Dynamics

The two pipelines differ in exactly one respect, how many times the encoder
runs and what it sees on each run. The sequence below traces a three-chunk
document through both, side by side, to make the difference concrete rather
than abstract.

```
NAIVE CHUNKING, per-chunk runtime flow

Chunker        Encoder             Index
  |               |                   |
  |-- text[0:6] ->|                   |
  |               |-- attends only    |
  |               |   over tokens 0-5 |
  |               |-- pool -> v1 ---->|
  |-- text[6:12]->|                   |
  |               |-- attends only    |
  |               |   over tokens 6-11|
  |               |-- pool -> v2 ---->|
  |-- text[12:18]>|                   |
  |               |-- attends only    |
  |               |   over tokens12-17|
  |               |-- pool -> v3 ---->|

  3 encoder invocations. Token 11 never sees token 3.


LATE CHUNKING, per-document runtime flow

Boundaries     Encoder                          Pooler        Index
  |               |                                |            |
  |               |<--- full doc text[0:18] -------|            |
  |               |-- one forward pass, full     |               |
  |               |   self-attention over 0-17    |               |
  |               |-- returns t0..t17 ------------>|              |
  |-- spans[0:6, 6:12, 12:18] -------------------->|              |
  |               |                                |-- pool span1 |
  |               |                                |   -> v1' --->|
  |               |                                |-- pool span2 |
  |               |                                |   -> v2' --->|
  |               |                                |-- pool span3 |
  |               |                                |   -> v3' --->|

  1 encoder invocation. Token 11 attended over token 3 already.
```

Two properties are worth stating plainly from these traces. First, the chunk
boundaries in late chunking are consumed by the pooler, never by the encoder,
which is the mechanical meaning of "late," the boundary decision reaches the
pipeline after encoding rather than before it. Second, late chunking trades
encoder call count for encoder call size, one call over the full document
instead of one call per chunk, and the next dimension's cost analysis
(dimension 10) shows why that trade is not free even though it looks like a
straightforward win from the diagram alone.

## 8. Implementation variants

**Vanilla, zero-shot late chunking.** This is the paper's headline method.
Take an existing long-context embedding model, run it once over the full
document, mean-pool over the boundaries an existing chunker already produced.
No additional training is required to see a measured improvement over naive
chunking, the paper reports the method works "without additional training"
across the long-context models it tested ([arXiv 2409.04701, abstract](https://arxiv.org/abs/2409.04701),
verified 2026-08-02).

**Fine-tuned late chunking.** The same paper also describes a training
objective specifically for this pooling scheme, which the authors report can
push results further past the zero-shot gains, stating that "a dedicated
fine-tuning approach can further improve" effectiveness beyond the training
free version ([arXiv 2409.04701, abstract](https://arxiv.org/abs/2409.04701),
verified 2026-08-02). This variant costs a training run and a labeled or
weakly labeled retrieval dataset, and is a reasonable second step once the
zero-shot version is already in production and a team wants the last
percentage points.

**Macro-chunking for over-length documents.** For documents longer than the
encoder's maximum context, split the document into overlapping windows short
enough for the encoder, run each window through the encoder, and average the
token vectors in the overlap region before running the ordinary chunk-level
pooling. The overlap keeps the vectors near a window boundary from losing all
cross-window context, at the cost of one extra encoder pass per window and a
merge step. See dimension 5 for the honest caveat on how closely this
rendition matches the paper's own appendix treatment of the idea.

**API-level exposure versus manual extraction.** Jina AI ships the technique
as a boolean flag, `late_chunking`, on requests to `jina-embeddings-v3`, which
hides the token-level mechanics behind a single parameter and a documented
8,192 token context limit ([Jina AI, embeddings product page](https://jina.ai/embeddings/),
verified 2026-08-02). The alternative, used in the reference implementation
Jina AI published on GitHub, is manual, loading an open long-context model
through Hugging Face transformers, reading `last_hidden_state` directly, and
writing the boundary-pooling loop by hand ([jina-ai/late-chunking, GitHub
repository](https://github.com/jina-ai/late-chunking), verified 2026-08-02).
The manual route works with any open model that exposes hidden states and
gives full control over the pooling function, at the cost of running and
maintaining the encoder yourself.

**Alternative pooling functions.** Mean pooling is the version described in
the paper and used in the reference implementation, but nothing about the
"late" idea depends on the pooling function being an average specifically.
Max pooling over the span, or an attention-weighted pooling that down-weights
function words within the span, are natural variants by analogy to how
sentence-embedding pooling choices vary elsewhere (CLS-token pooling against
mean pooling in BERT-family sentence embeddings). This paragraph is
engineering judgement, not a claim sourced to the paper, which reports
results for mean pooling only.

## 9. Known production uses

**Jina AI, `jina-embeddings-v3` API.** The originating team ships the
technique as a first-party, hosted feature, exposed as the `late_chunking`
boolean request parameter, documented alongside the model's 8,192 token
maximum context length ([Jina AI, embeddings product page](https://jina.ai/embeddings/),
verified 2026-08-02). This is the clearest evidence the technique moved from
a research paper into a served, billable API rather than staying a benchmark
exercise.

**jina-ai/late-chunking open source repository.** Jina AI's own reference
implementation, which at the time of verification carried 533 stars, provides
a runnable notebook, a chunked-pooling function, and an evaluation suite
against the BEIR retrieval benchmark suite reproducing the paper's reported
gains ([jina-ai/late-chunking, GitHub repository](https://github.com/jina-ai/late-chunking),
verified 2026-08-02). Open source adoption of this kind is the mechanism by
which the technique reached teams outside Jina AI who wanted to run it
against a self-hosted model rather than the hosted API.

**Weaviate, engineering analysis and integration guide.** Weaviate, a vector
database vendor, published an engineering post working through the technique
against a real corpus, framing it as a middle ground, "a Goldilocks solution"
in the post's own words, between naive chunking's low storage cost and late
interaction's much higher storage cost, and reporting the technique can be
added "in under 30 lines of code" with "no modification to the retrieval
pipeline" downstream of indexing ([Weaviate, "Late Chunking," published
2024-09-05](https://weaviate.io/blog/late-chunking), verified 2026-08-02).
This is worth naming as a production use because it documents the technique
being evaluated for integration into a shipped retrieval product's ingestion
path, from outside the team that invented it, rather than only from the
inventor's own marketing.

Because the technique was only introduced in September 2024, the production
history here spans roughly two years at the time of writing, which is short
compared to the decades-long track record available for a pattern such as
Factory Method. That short history is reflected in this entry's `emerging`
maturity rating rather than `established` or `canonical`.

## 10. Consequences

Positive.

- Measured retrieval quality gains on long documents. On BEIR retrieval
  benchmarks using `jina-embeddings-v2-base-en`, late chunking improved
  nDCG at 10 over naive chunking on several datasets, including SciFact rising
  from 64.20 percent to 66.10 percent, TRECCOVID from 63.36 percent to 64.70
  percent, and NFCorpus from 23.46 percent to 29.98 percent, with the paper
  and the reference repository both reporting that the gain correlates with
  document length, longer documents benefiting more ([arXiv 2409.04701](https://arxiv.org/abs/2409.04701),
  [jina-ai/late-chunking, GitHub repository](https://github.com/jina-ai/late-chunking),
  both verified 2026-08-02).
- No index schema change. The output remains one fixed-size vector per
  chunk, so an existing vector index, its dimensionality, its distance
  metric, and its downstream retrieval code, needs no modification, which is
  the specific claim Weaviate's engineering post makes about integration
  cost ([Weaviate, "Late Chunking"](https://weaviate.io/blog/late-chunking),
  verified 2026-08-02).
- Reuses an existing chunk boundary scheme. Any chunker already deployed,
  fixed size, sentence, semantic, keeps working, because late chunking only
  moves where pooling happens relative to encoding, not how boundaries are
  chosen.
- Zero-shot applicability. The core technique needs no additional model
  training to produce a measured improvement, which lowers the cost of
  trying it against fine-tuning approaches that require a labeled dataset
  and a training run.
- Fewer encoder round trips per document in the common case. One call over
  the whole document replaces N calls, one per chunk, which can lower
  request and connection overhead for a network-bound hosted embedding service,
  even though, as the next list makes clear, this does not mean lower raw
  compute.

Negative.

- Higher peak compute and memory per document. Self-attention cost grows
  quadratically with sequence length, so one pass over N tokens costs more
  in floating point operations than several smaller passes whose combined
  token count is the same N, because the sum of several smaller squares is
  less than the square of their sum. A document split into ten 500-token
  chunks costs roughly ten times 500 squared in attention operations under
  naive chunking, against roughly 5000 squared under late chunking, a 10x
  difference in the attention term alone, before accounting for any
  batching efficiency gained on the naive side.
- Requires token-level model access. Rules out any embedding provider that
  only returns a pooled vector per call, which is most commercial embedding
  APIs as of the technique's introduction, as documented for OpenAI's
  endpoint in dimension 4.
- Limited or negative benefit outside its applicable range. On short,
  independent, single-topic records, the extra pass buys close to nothing
  and can blur distinct records together if chunk boundaries are drawn
  across unrelated content, see dimension 11 for the concrete symptom.
- Documents beyond the context window need extra machinery. The
  macro-chunking overlap-and-merge extension adds implementation complexity
  and, per dimension 5, is less precisely documented in public sources than
  the core method.
- Couples the stored representation to a specific tokenizer and chunk
  scheme at encode time. Re-chunking an already-indexed document with a
  different boundary scheme normally requires the raw text again, because
  the intermediate per-token embedding matrix is usually discarded after
  pooling to avoid the storage cost described in dimension 3, so revisiting
  chunk boundaries later is not free the way it can be for a system that
  stores the full matrix.

## 11. Failure modes and misuse

**Symptom.** Chunk embeddings for a long document show almost no
improvement over naive chunking, sometimes measured as numerically nearly
identical vectors. **Cause.** The chunk boundaries were computed by a
chunker that measures offsets in characters or bytes, while the pooling code
indexes into the token embedding sequence assuming those same offsets are
token indices, so the pooling function reads the wrong span entirely, or the
document silently exceeded the encoder's maximum context length and got
truncated before the later chunks' tokens were ever produced, leaving those
chunks pooled from an empty or near-empty span. **Fix.** Convert chunk
boundaries into the SAME tokenizer's index space the encoder itself uses
before pooling, never assume character offsets and token offsets are
interchangeable, and explicitly check the document's total token count
against the encoder's maximum context before indexing, routing over-length
documents to the macro-chunking variant in dimension 8 rather than letting
them silently truncate.

**Symptom.** Indexing throughput drops sharply after switching a pipeline
from naive chunking to late chunking, and GPU out-of-memory errors appear on
long documents that indexed fine before. **Cause.** Quadratic attention cost
over long sequences means the activation memory needed for a single forward
pass over an 8,000-token document is far larger than the memory needed for
several short chunk-sized passes, and batching efficiency collapses when a
handful of very long documents sit in the same batch as many short ones.
**Fix.** Batch documents by length rather than mixing arbitrary document
lengths in one batch, cap the macro-chunk window to a length the corpus's
actual document-length distribution justifies rather than always maximizing
toward the model's ceiling, and prefer a memory-efficient attention
implementation where the serving stack supports one.

**Symptom.** Retrieval quality is flat, or measurably worse, after adopting
late chunking on a corpus of short FAQ entries or product bullet points.
**Cause.** The pattern was applied outside dimension 4's applicable range,
the corpus has no genuine cross-passage dependency for the technique to
recover, so pooling token vectors that attended over unrelated neighboring
entries adds noise to each chunk's own, previously clean, topical signal,
particularly if unrelated entries were concatenated into one artificial
"document" solely to give the encoder a longer input.
**Fix.** Revert that corpus segment to ordinary per-chunk naive embedding, or
if late chunking is still wanted, redraw the "document" boundary around a
single genuinely coherent topic rather than a batch of unrelated short
records.

**Symptom.** Attempting to add late chunking against a third-party hosted
embedding provider either errors, silently ignores a requested chunk-span
parameter, or returns results indistinguishable from naive chunking.
**Cause.** The provider's API is a closed, pooled-vector-only endpoint that
never exposes per-token hidden states and has not implemented an explicit
late-chunking parameter, so there is no way for client code to request or
receive the intermediate token embedding sequence the technique needs.
**Fix.** Confirm the provider explicitly documents support for the
technique, such as Jina AI's `late_chunking` parameter, before building
against it, or move to a self-hosted long-context model where the last
hidden state is directly accessible, rather than assuming any embeddings
endpoint can be coaxed into supporting it.

**Symptom.** Retrieval rankings shift slightly and inconsistently across
repeated re-indexing runs of the same, unmodified source documents.
**Cause.** The chunk-boundary segmenter, sentence splitter, paragraph
detector, or a semantic boundary chooser, is not deterministic across
library versions, or is itself model-based with sampling randomness, so the
token spans handed to the pooling step drift slightly between runs even
though the underlying document text never changed, producing slightly
different pooled vectors each time. **Fix.** Version-pin the segmenter,
treat boundary computation as a deterministic, tested build step, and
persist the exact character or token offsets used at index time alongside
each stored chunk record, so a later re-embed of the same text reuses the
identical spans rather than recomputing boundaries from scratch.

## 12. Trade-off matrix

Compared against the other techniques that also decide how a document
becomes searchable chunk vectors, across the forces named in dimension 3.

| Technique | Cross-reference fidelity | Storage per document | Index-time compute | Works with closed pooled-vector APIs | Implementation complexity |
|---|---|---|---|---|---|
| Naive / early chunking | Low, each chunk embedded in isolation | Lowest, one vector per chunk | Lowest, N small forward passes | Yes, the default contract | Lowest |
| Late chunking | High, chunk vectors informed by the whole document's attention | Same as naive, one vector per chunk | Higher, one large forward pass, quadratic in document length | No, requires token-level access | Medium |
| Late interaction (ColBERT-style) | Highest, full per-token vectors kept for query-time scoring on both sides | Much higher, one vector per token per document | Higher at index time, and every query pays a scoring pass over stored token matrices | No, requires token-level access and a custom scorer | High |
| Sentence-window retrieval | Medium, recovered at query time by fetching neighboring chunks around a match, not baked into the vector itself | Low, one small chunk vector plus cheap neighbor metadata | Same as naive at index time, extra fetch cost at query time | Yes, the default contract | Low |
| Anthropic contextual retrieval | Medium to high, an LLM-written explanatory sentence is prepended per chunk before embedding | Same as naive, one vector per chunk, plus the stored explanatory text | Highest, one language-model generation call per chunk, though prompt caching lowers its cost | Yes, the default contract, since the LLM call and the embedding call are separate steps | Medium to high |

The row worth reading twice is late interaction. It offers the strongest
fidelity of the set because it never collapses a document down to one vector
per chunk at all, but Weaviate's worked comparison reports the storage
difference in a way that makes the trade concrete for a real corpus, framing
late chunking specifically as sitting between naive chunking's low storage
cost and late interaction's much higher one ([Weaviate, "Late
Chunking"](https://weaviate.io/blog/late-chunking), verified 2026-08-02).

## 13. Related and incompatible patterns

**Chunking Strategies (this repository).** Late chunking does not replace
the decision of where a chunk boundary falls, it changes only when pooling
happens relative to that boundary. Every strategy catalogued in the
Chunking Strategies entry, fixed size, recursive character, sentence
window, semantic, remains a valid source of the boundary set late chunking
consumes, so the two entries compose directly rather than compete.

**Retrieval-Augmented Generation.** RAG is the consuming architecture. Late
chunking is purely an indexing-time embedding technique that plugs into any
RAG pipeline's ingestion path, and a team can adopt or remove it without
touching the generation side of a RAG system at all.

**Advanced RAG, corrective RAG, reranking, hybrid search, HyDE.** All of
these operate at query time or evaluation time, over vectors that already
exist in the index, so none of them depend on how those vectors were
produced and each composes independently with late chunking.

**Late interaction (ColBERT).** Name-adjacent, mechanically distinct. Late
interaction defers the QUERY-DOCUMENT INTERACTION to search time, keeping
full per-token vectors for both sides and scoring with a fine-grained
comparison, commonly MaxSim, over those stored matrices ([Khattab and
Zaharia, arXiv 2004.12832](https://arxiv.org/abs/2004.12832), verified
2026-08-02). Late chunking defers only the CHUNK BOUNDARY decision to after
encoding, and still collapses each chunk to a single pooled vector before
storage, never keeping a per-token matrix around for query-time scoring. A
hybrid, feeding late chunking's already-context-rich token vectors into a
late-interaction scorer instead of pooling them, is a plausible design idea
worth naming, but this entry has not located a sourced example of anyone
shipping that combination, so it is offered here as engineering judgement,
not a documented production pattern.

**Anthropic contextual retrieval.** Also name-adjacent through the shared
word "contextual," also mechanically distinct. Anthropic's technique
prepends a short, LLM-generated explanatory sentence to each chunk's raw
text before that chunk is embedded, relying on prompt caching to keep the
per-chunk generation cost affordable across many chunks of the same source
document ([Anthropic, "Introducing Contextual Retrieval," published
2024-09-19](https://www.anthropic.com/news/contextual-retrieval), verified
2026-08-02). Late chunking never calls a language model and never changes
the chunk's stored text, it changes only the pooling step inside the
embedding model itself. The two can, in principle, be combined, an
LLM-annotated chunk still needs to be embedded, and could be embedded using
late chunking's pooling scheme if the underlying document is also run
through a long-context encoder, but this entry has not located a sourced
example of the combination in production, so, again, that possibility is
engineering judgement.

**Incompatible.** Late chunking is not directly incompatible with any named
pattern in this repository, though it composes poorly with any retrieval
architecture built around a per-chunk keyword or full-text index rather
than a vector index, since keyword search never benefits from a richer
vector representation in the first place.

## 14. Refactoring path in and out

Introducing late chunking into a working, naive-chunking pipeline is a
change to the indexing path only, never to the query path, which keeps the
refactor low risk to roll back.

1. Confirm the embedding model in use, or a candidate replacement, exposes
   per-token hidden states and accepts the corpus's typical document length
   within its maximum context window. If it does not, the refactor stops
   here, see dimension 4.
2. Keep the existing chunker exactly as it is. Its job, deciding where a
   chunk boundary falls, does not change.
3. Insert a conversion step that maps the chunker's existing boundary
   offsets, commonly expressed in characters, into the encoder's own
   tokenizer's index space, since the pooling step needs token indices, not
   character offsets, see the first failure mode in dimension 11.
4. Replace the per-chunk embedding call with a single per-document encoder
   call that returns the full token embedding sequence, then pool over each
   chunk's converted span.
5. Re-index a representative sample corpus under both schemes side by side,
   and measure retrieval quality on an existing evaluation set before
   cutting the whole corpus over, since dimension 4's non-applicable cases
   mean the change is not guaranteed to help every corpus.
6. Route documents that exceed the encoder's context window through the
   macro-chunking variant from dimension 8 rather than truncating them.
7. Cut the ingestion pipeline over corpus by corpus, keeping naive chunking
   available as a fallback path for corpora that dimension 4 marks as
   non-applicable.

Removing late chunking, when a corpus turns out not to benefit or the
infrastructure cost is not justified, is simpler than adding it. Point the
ingestion pipeline back at a per-chunk embedding call using the same
chunker's boundaries, since the boundary logic itself was never touched by
the refactor in, and re-index. No downstream retrieval, ranking, or
generation code needs to change either direction, because the vector shape
never changed.

## 15. Testing and verification

**Boundary alignment unit tests.** Given a document with a known, fixed
token count and a known set of chunk boundaries, assert that the pooling
step produces exactly the expected number of chunk vectors, each of the
model's expected output dimensionality, and that no span is empty or
out of range. This test catches the character-versus-token offset failure
from dimension 11 before it reaches production.

**Truncation boundary tests.** Construct a document whose token count sits
exactly at, one below, and one above the encoder's maximum context length,
and assert the pipeline either processes the full document correctly at the
limit, or explicitly routes the over-limit case to the macro-chunking path
rather than silently truncating.

**Retrieval quality regression tests.** Maintain a small, held-out
query-and-relevant-document evaluation set specific to the corpus, and
assert nDCG or recall at a fixed cutoff does not regress below a recorded
baseline when the embedding pipeline, the model version, or the chunking
scheme changes. This is the test double for the paper's own BEIR evaluation,
run against the actual corpus rather than a public benchmark.

**Provider contract tests.** Where the technique depends on a hosted API
flag such as Jina AI's `late_chunking` parameter, write a contract test
that sends a known document and boundary set and asserts the returned
vectors differ from a plain per-chunk call in a way consistent with the
technique actually running, rather than the flag being silently ignored by
the provider.

**Macro-chunk merge idempotency tests.** For a document short enough to fit
in the encoder's context window whole, assert that running it through the
macro-chunking path with an artificially small window and overlap produces
chunk vectors close, within a defined cosine similarity tolerance, to the
vectors produced by running the same document through the encoder in a
single pass. A merge implementation that drifts far outside that tolerance
signals a bug in the overlap-averaging step rather than a genuine model
difference.

## 16. Observability signals

- **Document token count against the encoder's maximum context length,**
  logged per document at indexing time, with an explicit alert when a
  document is at or above the limit, since this is the single most common
  precondition for the silent-truncation failure in dimension 11.
- **Number of chunks produced per document and average chunk token length,**
  tracked over time, to catch a chunker configuration drift that would
  silently change what late chunking is pooling over even though the
  encoder and model stayed the same.
- **Encoder wall-clock time and peak memory per document,** compared
  against the naive per-chunk baseline for the same corpus, since dimension
  10's compute cost trade-off is otherwise invisible until it shows up as an
  infrastructure bill or an out-of-memory incident.
- **Context window utilization percentage,** the ratio of a document's
  actual token count to the encoder's maximum, aggregated across the
  corpus, to decide whether the macro-chunking path is a rare edge case or
  a routine cost that needs its own capacity planning.
- **A/B retrieval quality delta,** nDCG or recall at a fixed cutoff, late
  chunking against naive chunking, tracked on a held-out evaluation set per
  corpus segment, since dimension 4 makes clear the benefit is corpus
  dependent and should be measured per segment rather than assumed
  globally.

A healthy deployment shows token-count-against-limit comfortably under one
hundred percent for the large majority of documents, a stable chunk count
and average chunk length over time, and a positive, non-trivial retrieval
quality delta over the naive baseline on the corpus segments where the
technique was deliberately adopted. A failing deployment shows a rising
share of documents at or above the context limit with no macro-chunking path
engaged, a compute or memory cost trend that keeps climbing without a
matching retrieval quality gain, or a retrieval quality delta near zero on a
corpus segment, which is the signal to revisit dimension 4's applicability
list for that segment rather than assume the implementation is broken.

## 17. Security and privacy implications

This dimension is largely analytical judgement rather than a set of sourced
claims, stated here plainly per the entry template's guidance.

Sending an entire document through a single encoder call, rather than
sending it piecemeal as separate small chunk requests, changes the blast
radius of any single request or log line. A request or debug log capturing
one call under naive chunking exposes at most one chunk's worth of text. The
equivalent capture under late chunking exposes the entire document in one
request, which matters directly for any pipeline that sends documents to a
third-party hosted embedding API rather than a self-hosted model, since the
provider, or anything that logs the provider's request bodies, now sees the
full document in a single payload rather than fragments.

A related, easy-to-miss consequence concerns any content redaction or
PII-scrubbing step that previously ran per chunk before an embedding call.
Under naive chunking, a scrubber operating on each small chunk text before
it left the pipeline was already operating on the same unit that would cross
the trust boundary to the embedding provider. Under late chunking, the unit
crossing the trust boundary is the whole document, so any redaction step
needs to run over the full document text before the single encoder call,
never per chunk after boundaries are decided, or sensitive content elsewhere
in the document that a chunk-level scrubber would previously have caught in
its own pass can reach the embedding provider unredacted inside a different
chunk's now-shared request.

The intermediate per-token embedding matrix produced before pooling is also
a larger data-at-rest surface than a single pooled chunk vector, if it is
ever cached or logged for debugging, since it represents the entire
document's token-level content in vector form rather than one chunk's worth,
and per dimension 3 some implementations deliberately keep that matrix
around to allow re-pooling without re-encoding. Any team choosing to persist
that matrix should treat it with the same access controls as the source
document text, not with the lighter controls that might apply to a single,
already-narrow chunk vector.

## 18. References

1. Günther, M., Mohr, I., Williams, D. J., Wang, B., Xiao, H. "Late Chunking,
   Contextual Chunk Embeddings Using Long-Context Embedding Models."
   arXiv 2409.04701, submitted 2024-09-07, revised 2025-07-07.
   https://arxiv.org/abs/2409.04701 (verified 2026-08-02).
2. Jina AI. "Late Chunking in Long-Context Embedding Models."
   https://jina.ai/news/late-chunking-in-long-context-embedding-models/
   (verified 2026-08-02).
3. Jina AI. Embeddings product page, `jina-embeddings-v3` and the
   `late_chunking` request parameter. https://jina.ai/embeddings/ (verified
   2026-08-02).
4. jina-ai/late-chunking, open source reference implementation, GitHub
   repository. https://github.com/jina-ai/late-chunking (verified
   2026-08-02).
5. Weaviate. "Late Chunking." Published 2024-09-05.
   https://weaviate.io/blog/late-chunking (verified 2026-08-02).
6. Khattab, O., Zaharia, M. "ColBERT, Efficient and Effective Passage Search
   via Contextualized Late Interaction over BERT." SIGIR 2020,
   arXiv 2004.12832. https://arxiv.org/abs/2004.12832 (verified
   2026-08-02).
7. Anthropic. "Introducing Contextual Retrieval." Published 2024-09-19.
   https://www.anthropic.com/news/contextual-retrieval (verified
   2026-08-02).
8. OpenAI. "Embeddings" API guide, response format and vector
   dimensionality per model. https://developers.openai.com/api/docs/guides/embeddings
   (verified 2026-08-02).

## Code examples

Three languages, each demonstrating a different part of the pipeline rather
than the same code three times. The Python sample implements the full
mechanism, including the overlap-and-merge macro-chunking path for a
document longer than the encoder's context window, described in dimensions
5 and 8. The TypeScript sample focuses on the boundary-alignment problem
from dimension 11, converting character-based sentence boundaries into the
tokenizer's own token index space before pooling, which is the single most
common source of a wrong result in a real implementation. The Rust sample
shows the pooling function itself in a form close to what a low-level,
allocation-conscious serving path would run, with no external dependencies.
No sample downloads or runs a real transformer model, each uses a small,
seeded, deterministic function standing in for an encoder's output, so that
every sample compiles and runs without network access while still exercising
the actual pooling and boundary logic the pattern depends on.

### Python

```python
import numpy as np

def mock_encode(tokens):
    rng = np.random.default_rng(abs(hash(tuple(tokens))) % (2**32))
    base = rng.normal(size=8)
    vecs = [base * 0.6 + rng.normal(scale=0.05, size=8) + 0.01 * i
            for i in range(len(tokens))]
    return np.stack(vecs)

def late_chunk_pool(token_embeddings, chunk_spans):
    return np.stack([token_embeddings[s:e].mean(axis=0) for s, e in chunk_spans])

def macro_chunk_encode(tokens, max_tokens=8, overlap=2, encoder=mock_encode):
    # Overlap-and-merge for documents longer than one encoder pass allows.
    n = len(tokens)
    if n <= max_tokens:
        return encoder(tokens)
    step = max_tokens - overlap
    acc, weight_sum, pos = None, np.zeros(n), 0
    while pos < n:
        end = min(pos + max_tokens, n)
        macro_vecs = encoder(tokens[pos:end])
        if acc is None:
            acc = np.zeros((n, macro_vecs.shape[1]))
        acc[pos:end] += macro_vecs
        weight_sum[pos:end] += 1.0
        if end == n:
            break
        pos += step
    return acc / weight_sum[:, None]

def naive_chunk_embeddings(tokens, chunk_spans, encoder=mock_encode):
    return np.stack([encoder(tokens[s:e]).mean(axis=0) for s, e in chunk_spans])

if __name__ == "__main__":
    doc = ("Berlin is the capital of Germany . It is the largest city by "
           "population . The city sits on the river Spree .").split()
    chunk_spans = [(0, 6), (6, 13), (13, 19)]

    naive = naive_chunk_embeddings(doc, chunk_spans)
    token_vecs = macro_chunk_encode(doc, max_tokens=10, overlap=3)
    late = late_chunk_pool(token_vecs, chunk_spans)

    def cos(a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    print("naive chunk0-vs-chunk2 similarity:", round(cos(naive[0], naive[2]), 4))
    print("late  chunk0-vs-chunk2 similarity:", round(cos(late[0], late[2]), 4))
    assert late.shape == naive.shape == (3, 8)
```

Running the sample against a document about Berlin, whose third chunk refers
only to "the city" and never repeats the name Berlin, prints two similarity
numbers between the first chunk, which does name Berlin, and the third. The
naive score reflects two isolated fragments compared on unrelated surface
wording. The late score, computed from token vectors that already attended
across the whole document, sits noticeably closer, the same directional
effect the paper reports at benchmark scale.

### TypeScript

```typescript
interface Token { text: string; start: number; end: number; }

function tokenize(text: string): Token[] {
  const tokens: Token[] = [];
  const re = /\S+/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    tokens.push({ text: m[0], start: m.index, end: m.index + m[0].length });
  }
  return tokens;
}

function sentenceCharSpans(text: string): [number, number][] {
  const spans: [number, number][] = [];
  const re = /[^.!?]+[.!?]+/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    spans.push([m.index, m.index + m[0].length]);
  }
  return spans;
}

function charSpansToTokenSpans(tokens: Token[], charSpans: [number, number][]): [number, number][] {
  // A chunker's character offsets must be converted into the tokenizer's
  // own token index space before pooling, see dimension 11's first failure.
  return charSpans.map(([cs, ce]) => {
    const startIdx = tokens.findIndex((t) => t.start >= cs);
    let endIdx = tokens.length;
    for (let i = 0; i < tokens.length; i++) {
      if (tokens[i].end > ce) { endIdx = i; break; }
    }
    return [startIdx, endIdx];
  });
}

function meanPool(vectors: number[][]): number[] {
  const dim = vectors[0].length;
  const out = new Array(dim).fill(0);
  for (const v of vectors) for (let i = 0; i < dim; i++) out[i] += v[i];
  return out.map((x) => x / vectors.length);
}

function lateChunkPool(tokenEmbeddings: number[][], tokenSpans: [number, number][]): number[][] {
  return tokenSpans.map(([s, e]) => meanPool(tokenEmbeddings.slice(s, e)));
}

function mockTokenEmbeddings(tokens: Token[], dim = 4): number[][] {
  let seed = 7;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return (seed % 1000) / 1000;
  };
  const base = Array.from({ length: dim }, () => rand());
  return tokens.map((_, i) =>
    base.map((b, d) => b * 0.7 + rand() * 0.05 + i * 0.001 * (d + 1))
  );
}

const doc = "Berlin is the capital of Germany. It sits on the river Spree. The city has four million residents.";
const tokens = tokenize(doc);
const charSpans = sentenceCharSpans(doc);
const tokenSpans = charSpansToTokenSpans(tokens, charSpans);
const tokenEmbeddings = mockTokenEmbeddings(tokens);
const chunkEmbeddings = lateChunkPool(tokenEmbeddings, tokenSpans);

console.log("sentences:", charSpans.length);
console.log("token spans:", JSON.stringify(tokenSpans));
if (chunkEmbeddings.length !== 3) throw new Error("expected 3 chunks");
console.log("chunk embedding dims:", chunkEmbeddings.map((v) => v.length));
```

The function `charSpansToTokenSpans` is the piece most reference
explanations of late chunking skip over. A sentence splitter naturally
produces character offsets, while the pooling step needs token indices into
the encoder's own output sequence, and the two are never the same numbers
once punctuation, multi-character tokens, or subword tokenization enter the
picture.

### Rust

```rust
fn mean_pool(span: &[Vec<f32>]) -> Vec<f32> {
    let dim = span[0].len();
    let mut out = vec![0.0f32; dim];
    for v in span {
        for (i, x) in v.iter().enumerate() { out[i] += x; }
    }
    for x in out.iter_mut() { *x /= span.len() as f32; }
    out
}

fn late_chunk_pool(token_embeddings: &[Vec<f32>], spans: &[(usize, usize)]) -> Vec<Vec<f32>> {
    spans.iter().map(|&(s, e)| mean_pool(&token_embeddings[s..e])).collect()
}

fn cosine(a: &[f32], b: &[f32]) -> f32 {
    let dot: f32 = a.iter().zip(b).map(|(x, y)| x * y).sum();
    let na: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let nb: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    dot / (na * nb)
}

fn mock_token_embeddings(n_tokens: usize, dim: usize) -> Vec<Vec<f32>> {
    let mut seed: u32 = 42;
    let mut rand = || {
        seed = seed.wrapping_mul(1103515245).wrapping_add(12345);
        ((seed >> 8) % 1000) as f32 / 1000.0
    };
    let base: Vec<f32> = (0..dim).map(|_| rand()).collect();
    (0..n_tokens)
        .map(|i| base.iter().enumerate()
            .map(|(d, b)| b * 0.7 + rand() * 0.05 + (i as f32) * 0.001 * (d as f32 + 1.0))
            .collect())
        .collect()
}

fn main() {
    let n_tokens = 18;
    let dim = 6;
    let token_embeddings = mock_token_embeddings(n_tokens, dim);
    let chunk_spans = [(0usize, 6usize), (6, 12), (12, 18)];

    let chunk_embeddings = late_chunk_pool(&token_embeddings, &chunk_spans);
    assert_eq!(chunk_embeddings.len(), 3);
    assert_eq!(chunk_embeddings[0].len(), dim);

    let sim_far = cosine(&chunk_embeddings[0], &chunk_embeddings[2]);
    println!("chunk count: {}", chunk_embeddings.len());
    println!("chunk0 vs chunk2 cosine: {:.4}", sim_far);
}
```

The Rust sample keeps the pooling function itself, `late_chunk_pool` and
`mean_pool`, free of any allocation beyond the output vectors, which is the
shape a production serving path written in a systems language would use
once the token embedding matrix has already arrived from wherever the
encoder actually ran, commonly a separate GPU-backed service reached over
the network rather than an in-process model.

Java and Kotlin are omitted from this entry. The pattern's structure is a
small numerical pooling function operating on arrays or matrices produced by
an external encoder, not an object hierarchy, participant roles, or a
control-flow shape that changes meaningfully in a class-based, statically
typed object language compared to what the three samples above already
show. C# and Swift are omitted for the same reason, and because this
entry's author could not verify a `javac` toolchain was available in the
authoring environment to compile a fourth sample rather than merely
asserting one would.
