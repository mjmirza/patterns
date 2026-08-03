---
name: Corrective RAG
slug: corrective-rag
family: 17-ai-agentic
category: AI Agentic
aliases: [CRAG, Corrective Retrieval Augmented Generation]
first_described: "Yan, Gu, Zhu, Ling 2024"
maturity: emerging
related: [retrieval-augmented-generation, advanced-rag, agentic-rag, routing, evaluator-optimizer, reflexion, circuit-breaker]
incompatible_with: []
verified: 2026-08-02
---

# Corrective RAG

## 1. Name, aliases, and lineage

The canonical name is Corrective Retrieval Augmented Generation, universally
shortened to CRAG in both the originating paper and every downstream
implementation examined for this entry. The pattern was introduced in Shi-Qi
Yan, Jia-Chen Gu, Yun Zhu, and Zhen-Hua Ling, "Corrective Retrieval Augmented
Generation," arXiv:2401.15884, 2024,
https://arxiv.org/abs/2401.15884, verified 2026-08-02. The paper opens by
stating the motivation plainly. "Large language models (LLMs) inevitably
exhibit hallucinations," and while retrieval augmented generation is a
practical complement, it "relies heavily on the relevance of retrieved
documents, raising concerns about how the model behaves if retrieval goes
wrong." CRAG is the authors' answer to that second sentence, a mechanism that
watches its own retrieval step and reacts when that step has gone wrong.

CRAG is not a synonym for retrieval augmented generation itself, and the two
names get conflated often enough that the distinction is worth stating up
front. Retrieval Augmented Generation (RAG), described in Patrick Lewis,
Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman
Goyal, Heinrich Kuttler, Mike Lewis, Wen-tau Yih, Tim Rocktaschel, Sebastian
Riedel, and Douwe Kiela, "Retrieval-Augmented Generation for
Knowledge-Intensive NLP Tasks," NeurIPS 2020, arXiv:2005.11401,
https://arxiv.org/abs/2005.11401, verified 2026-08-02, pairs "pre-trained
parametric and non-parametric memory for language generation," retrieving
once per query and conditioning generation on whatever came back, with no
step that asks whether what came back was any good. CRAG is a layer added on
top of that base pattern, not a replacement for it. Every CRAG pipeline still
has a retriever and a generator underneath, and what CRAG adds is a small
evaluator sitting between them that scores the retrieval and picks one of
three corrective actions before generation happens.

The paper's own name for the scoring component is the Retrieval Evaluator,
and its own names for the three actions are Correct, Incorrect, and
Ambiguous, all three used verbatim across every implementation this entry
cites. No alternate names for the pattern itself were found in wide use.
Where practitioners shorten anything, they shorten Corrective RAG to CRAG,
never the reverse.

## 2. Problem and context

A support bot answers questions by retrieving from a company's help center
index and handing the top few documents to a generator. Most of the time this
works, because the index was built from the same domain the questions come
from. But three ordinary things happen to any index over time. A page gets
renamed and the old content drifts out of relevance for the query that used
to match it. A customer asks about a feature that shipped after the index
was last built, so nothing in the index actually answers the question, only
something adjacent to it. A query uses vocabulary that overlaps a document's
vocabulary without overlapping its meaning, so the retriever's similarity
score is high while the actual relevance is low.

In every one of these cases the base RAG pipeline does not know anything went
wrong. The retriever returns its top-k documents regardless of how good they
are, because top-k is a ranking, not a quality gate, and the generator
conditions on whatever it is handed because generating fluent text from a
weak context is exactly the failure mode language models are prone to. The
result a user sees is not an error message. It is a confident, well-written,
wrong answer, built on a document that was the best available match without
being a good match. This is the specific problem CRAG addresses. Base RAG has
no feedback path between what the retriever actually found and how much the
downstream generator should trust it.

The context in which this problem is worth solving has three parts, all
present in the support bot example. First, the retrieval corpus is finite and
changes on its own schedule, independent of the query stream, so it will
sometimes simply lack the answer. Second, a plausible fallback source of
knowledge exists somewhere else, whether that is a broader internal index or
the open web, so when the corpus comes up short there is somewhere else to
look. Third, the cost of a confidently wrong answer, a support ticket
escalates, a fact-check downstream catches the pipeline in an error, a user
loses trust in the assistant, is higher than the cost of a slightly slower
answer that checked its own work first. Where any of those three does not
hold, the case for CRAG weakens, and dimension 4 below states exactly which
situations that is.

## 3. Forces

**Latency and cost against faithfulness.** Every corrective action beyond the
plain Correct path adds at least one more model call, the evaluator itself
runs unconditionally, and the Ambiguous and Incorrect paths add a rewrite
call and a search call on top. CRAG deliberately spends that extra time and
money to reduce the rate of unsupported answers, and the pattern only earns
its keep where that trade is worth making.

**Training investment against a purely inference-time wrapper.** The paper's
own evaluator is a fine-tuned model, which means someone has to produce
labeled relevance data and retrain it when the retriever or the domain
changes. Several production ports examined below skip that investment
entirely by prompting a general-purpose LLM as the evaluator instead, trading
evaluator accuracy and per-call cost for zero training overhead. Neither
choice dominates. It is a real trade this pattern forces a team to make.

**External trust and freshness against auditability.** Falling back to a web
search extends coverage to anything the search engine can reach, at the price
of pulling unreviewed, unaudited third-party content directly into a
generated answer. A closed corpus is fully auditable and fully bounded. A web
fallback is neither.

**Simplicity of a fixed pipeline against adaptive branching.** Base RAG is one
straight-line pipeline, retrieve, then generate. CRAG is a three-way branch
whose taken path differs per query, which means testing, tracing, and
debugging all have to account for path-dependent behavior that a
straight-line pipeline never had. Dimension 15 and dimension 16 describe how
to keep that complexity observable rather than opaque.

**Coupling to a search provider against portability.** Every implementation
in dimension 9 wires a specific search provider into the Incorrect and
Ambiguous branches. Swapping providers later means re-tuning the query
rewrite step and re-validating result quality, a cost a plain RAG pipeline
never carries because it has no such dependency.

## 4. Applicability and non-applicability

Reach for Corrective RAG when retrieval quality is uneven and the
consequence of trusting bad retrieval is worse than the added latency of
checking it first. A knowledge base that only partially covers the query
distribution, a corpus that updates slower than the world it describes, a
generation task, support answers, internal documentation Q&A, research
assistance, where an unsupported but fluent answer is a real cost, all fit.
It fits best on top of a RAG pipeline that already exists and already works
most of the time, because CRAG's entire design is a correction layer bolted
onto an existing retrieve-then-generate flow rather than a replacement for
one, and it fits best where a genuine second knowledge source, whether a web
search API or a broader secondary index, is reachable and permitted to use.

Do not reach for it in the following situations, each with the reason the
pattern's own mechanism stops paying for itself.

- **No fallback source exists.** If there is no web search, no secondary
  index, and no alternate retriever to escalate to, the Incorrect and
  Ambiguous branches have nowhere productive to send a query. CRAG then
  degenerates into an expensive way of noticing failure without a way of
  recovering from it. A plain abstention policy that says "insufficient
  context" achieves the same honesty at a fraction of the cost.
- **Hard sub-second latency budgets.** Interactive autocomplete, voice
  turn-taking, and similar surfaces cannot absorb an evaluator call plus a
  conditional rewrite-and-search round trip inside their response budget.
  A cheaper strategy, such as always retrieving a wider top-k and letting the
  generator itself hedge, fits those budgets better.
- **Closed, already-high-trust corpora.** A vetted internal legal database or
  a validated compliance knowledge base where retrieval is close to always
  correct gains little from an evaluator, and a web-search fallback on such a
  corpus is actively undesirable. It would introduce content the
  organization has neither reviewed nor is contractually permitted to cite.
- **No labeled data and no budget to produce it.** An evaluator trained or
  prompted with no calibration against the target domain is a coin flip with
  extra latency attached. An uncalibrated evaluator is worse than no
  evaluator, because it adds cost while its accuracy is unmeasured, and
  dimension 11 below describes exactly how that failure surfaces in
  production.
- **Regulated domains where sourcing must be pre-approved.** Medical,
  financial, or legal contexts under strict sourcing rules need every source
  cleared before use, not decided at run time by a scoring model. A runtime
  evaluator choosing to escalate to an open web search is precisely the
  behavior such domains need to prevent, not enable.
- **Multi-hop or compositional questions.** CRAG's evaluator scores each
  retrieved document's relevance in isolation. It has no mechanism for
  judging whether a set of individually relevant documents jointly answers a
  question that needs several of them combined. That is a different problem,
  closer to what an iterative agent loop (dimension 13, Agentic RAG) or a
  model trained end to end on the retrieve-and-reason task (dimension 13,
  Self-RAG) is built to handle.

## 5. Structure

**Query.** The incoming user question or generation goal, unchanged from the
base RAG pattern.

**Retriever.** The existing dense or sparse retriever, unmodified by CRAG. It
returns its usual top-k documents. CRAG does not change how retrieval itself
works, only what happens to the result.

**Retrieval Evaluator.** A scoring component, a fine-tuned T5-large model in
the originating paper, a prompted LLM grader in most production ports
examined in dimension 9, that assigns each retrieved document an independent
relevance score.

**Action Router.** Compares the evaluator's scores against a threshold policy
and selects one of the paper's three named actions, Correct, Ambiguous, or
Incorrect. Several production ports collapse this to a two-way choice. The
paper's own three-way design and the collapsed variant are both documented in
dimension 8.

**Knowledge Refiner.** Runs the paper's decompose-then-recompose algorithm on
documents entering the Correct path. Split each document into fine-grained
knowledge strips, score each strip with the same evaluator, discard the
low-scoring strips, and concatenate the survivors back into a single refined
passage. The same refiner also runs on whatever a web search returns, so the
Incorrect and Ambiguous paths get refined external knowledge rather than raw
search snippets.

**Query Rewriter.** For the Incorrect and Ambiguous paths, an LLM turns the
natural-language question into a short, keyword-oriented query better suited
to a web search engine than the original phrasing.

**Web Search Client.** An external search API, the Google Search API in the
originating paper's implementation, Tavily's search API in the two
open-source community ports examined in dimension 9, that returns documents
for the rewritten query.

**Generator.** The same downstream language model the base RAG pipeline
already used. CRAG does not change the generator's role. It changes what
knowledge the generator is handed by the time it runs.

## 6. ASCII structure diagram

```
                       +----------------------+
                       |        Query          |
                       +-----------+----------+
                                   |
                                   v
                       +----------------------+
                       |      Retriever         |
                       |  (unchanged from RAG)  |
                       +-----------+----------+
                                   |
                                   v
                       +----------------------+
                       | Retrieval Evaluator    |
                       | (scores each document) |
                       +-----------+----------+
                                   |
                   compare scores to upper/lower
                          threshold policy
                                   |
              +--------------------+--------------------+
              |                    |                     |
              v                    v                     v
         Correct              Ambiguous              Incorrect
              |                    |                     |
              v                    |                     v
    +------------------+           |          +--------------------+
    | Knowledge Refiner |          |          |   Query Rewriter     |
    | (decompose,filter,|          |          +----------+---------+
    |    recompose)     |          |                     |
    +--------+---------+           |                     v
             |                     |          +--------------------+
             |          +----------+-------+  |   Web Search Client  |
             |          | Knowledge Refiner |  +----------+---------+
             |          |   (both sources)  |             |
             |          +----------+-------+             |
             |                     |<---------------------+
             |                     |
             +----------+----------+
                        |
                        v
              +--------------------+
              |      Generator       |
              +----------+---------+
                         |
                         v
                    +---------+
                    | Answer  |
                    +---------+
```

## 7. Dynamics

1. The user query reaches the pipeline and is passed unmodified to the
   retriever, exactly as in base RAG.
2. The retriever returns its top-k documents. Nothing has changed yet
   compared to a plain RAG pipeline.
3. The Retrieval Evaluator scores every returned document independently,
   producing one confidence value per document.
4. The Action Router compares those scores against its threshold policy.
   The paper's released configuration uses two thresholds. If any document's
   score clears the upper threshold, reported near 0.59 in the paper's own
   configuration, the action is Correct. If every document's score falls
   beneath the lower threshold, reported near -0.99, the action is
   Incorrect. Anything else, at least one document present but none clearing
   the upper bound, falls into Ambiguous.
5. On Correct, the Knowledge Refiner runs the decompose-then-recompose
   algorithm on the retrieved documents. Split into knowledge strips, score
   each strip with the evaluator again, keep strips whose score clears a
   filter threshold, reported near -0.5 in the released implementation, and
   concatenate the survivors in their original order into one refined
   knowledge string.
6. On Incorrect, the retrieved documents are discarded outright. The Query
   Rewriter turns the question into a search-engine-style query, the Web
   Search Client fetches external results for it, and the same Knowledge
   Refiner runs against those results in place of the internal documents.
7. On Ambiguous, both paths run. The retrieved documents are refined exactly
   as in the Correct path, a web search is issued exactly as in the
   Incorrect path, and the two refined knowledge strings are combined before
   generation, so the generator sees internal and external knowledge
   together.
8. Whichever knowledge string results, internal only, external only, or
   blended, is handed to the Generator, which produces the answer exactly as
   it would in base RAG, conditioned on the corrected knowledge rather than
   the raw retrieval.
9. The answer is returned. A production deployment typically also logs the
   action taken and the evaluator's scores alongside the answer, which is
   what dimension 16 builds the observability plan around.

```
query --> retrieve --> evaluate each document
                              |
              +---------------+---------------+
              |               |               |
         (>= upper)      (between)       (<= lower, all)
              |               |               |
              v               v               v
          correct         ambiguous        incorrect
              |               |               |
              v               |               v
       refine(internal)       |        rewrite query
              |                \              |
              |                 \             v
              |                  \      search web
              |                   \           |
              |                    \          v
              |                 refine(internal)  refine(web)
              |                       \___________/
              |                             |
              +-------------+---------------+
                            |
                            v
                        generate
                            |
                            v
                          answer
```

## 8. Implementation variants

**Faithful three-way, paper implementation.** A fine-tuned T5-large evaluator
scoring each document on a continuous scale, two thresholds splitting the
action space into Correct, Ambiguous, and Incorrect, the decompose-then-
recompose refinement applied to both internal and external knowledge, a
keyword-extracting rewrite step, and the Google Search API for the fallback.
This is the shape the arXiv:2401.15884 paper actually benchmarks, and it is
the most expensive of the variants below to build, since it requires
producing labeled relevance data to fine-tune the evaluator.

**Binary LLM-as-grader port.** The community implementation shipped as an
official LangGraph tutorial in the langchain-ai/langgraph repository,
`examples/rag/langgraph_crag.ipynb`,
https://github.com/langchain-ai/langgraph/blob/main/examples/rag/langgraph_crag.ipynb,
verified 2026-08-02, replaces the trained evaluator with a zero-shot LLM
grader, the notebook uses `gpt-4o-mini` through a structured-output call
returning a binary yes-or-no relevance label per document, and, in the
notebook's own words, states its plan up front. "Let's skip the knowledge
refinement phase as a first pass," and, "If any documents are irrelevant,
let's opt to supplement retrieval with web search," collapsing the paper's
three-way Correct-Ambiguous-Incorrect split into a single rule. Generate
directly if every document is graded relevant, otherwise rewrite the query
and search. The LlamaIndex `CorrectiveRAGPack`, present in the
run-llama/llama_index repository's own command-line pack registry as
`"CorrectiveRAGPack": "llama_index.packs.corrective_rag"` in
`llama-index-core/llama_index/core/command_line/mappings.json`, verified
2026-08-02, follows the same shape. A GPT-4 binary relevance grader per
document, a query transform step, and Tavily's `TavilyToolSpec` invoked when
any document is graded not relevant. Both community ports trade the paper's
measured accuracy behavior, which depends on the strip-level filtering and
the graded confidence zones, for a build that needs no fine-tuning at all.

**Managed-platform port.** The aws-samples/simplified-corrective-rag
repository, https://github.com/aws-samples/simplified-corrective-rag,
verified 2026-08-02, pushes retrieval and correction onto Amazon Bedrock
managed services. A Bedrock Knowledge Base performs retrieval, and the
correction decision is reduced to two scenarios stated directly in the
repository's own README, "A document that closely matches the specified
query is located in the Knowledge Base," or it is not, in which case an
Agent for Amazon Bedrock invokes a Lambda-backed Wikipedia search action.
The README cites the same paper this entry cites and repeats its own
paraphrase of the retrieval evaluator's purpose. This variant trades the
paper's graded scoring for operational simplicity built on a managed
retrieval-and-agent stack, using Anthropic's Claude 3 as the generator and
Titan Embeddings G1 for the underlying vector search.

**Cross-encoder evaluator variant.** Rather than a trained T5-large
classifier or a prompted LLM, a cross-encoder relevance model of the kind
already deployed for re-ranking scores each query-document pair directly,
with a threshold applied on top of its output. Where a re-ranker already
sits in the pipeline for a different reason, repurposing it as the CRAG
evaluator removes an extra LLM call from the scoring step entirely. The
trade is that a re-ranker's score distribution and a purpose-built
evaluator's score distribution are not the same thing, so the thresholds
still need calibrating against the re-ranker's actual output range.

**Abstention variant with no external fallback.** Where dimension 4's "no
fallback source" non-applicability applies but the evaluate-then-branch
structure is still wanted for its ability to catch unsupported answers, the
Incorrect action is replaced with an explicit refusal rather than a web
search. This keeps the evaluator's benefit, catching bad retrieval before it
reaches the generator, while dropping the half of the pattern that depends
on an external knowledge source.

## 9. Known production uses

**LangGraph's official Corrective RAG tutorial.** The langchain-ai/langgraph
repository ships `examples/rag/langgraph_crag.ipynb` as a worked reference
implementation, its own graph wiring the nodes `retrieve`,
`grade_documents`, `transform_query`, and `web_search_node` through a
`decide_to_generate` conditional edge, using `TavilySearchResults(k=3)` as
its web search tool and a structured-output `GradeDocuments` model run
through `gpt-4o-mini` as its evaluator. The notebook file itself carries a
banner noting the directory "is retained purely for archival purposes and is
no longer updated," pointing readers to LangGraph's consolidated
documentation, which is worth stating plainly rather than glossing over. The
example is real, verified live in the repository, and it is also an
acknowledged historical artifact rather than the framework's current
front-door documentation. Source. langchain-ai/langgraph repository,
`examples/rag/langgraph_crag.ipynb`,
https://github.com/langchain-ai/langgraph/blob/main/examples/rag/langgraph_crag.ipynb,
verified 2026-08-02.

**LlamaIndex's CorrectiveRAGPack.** LlamaIndex ships a named, installable
pack for this exact pattern, registered in the framework's own command-line
pack mapping as `"CorrectiveRAGPack": "llama_index.packs.corrective_rag"`.
Its documentation page describes a workflow with an `eval_relevance` step
scoring retrieved documents with GPT-4 and a Tavily-backed web search branch
triggered when documents are graded not relevant, matching the same
evaluate-then-branch shape examined across every implementation in this
entry. Sources. run-llama/llama_index repository,
`llama-index-core/llama_index/core/command_line/mappings.json`, verified
2026-08-02, and https://developers.llamaindex.ai/python/examples/workflow/corrective_rag_pack/,
verified 2026-08-02.

**AWS's simplified Corrective RAG sample on Amazon Bedrock.** The
aws-samples organization, AWS's own repository namespace for reference
architectures, publishes `simplified-corrective-rag`, a deployable
CloudFormation stack that builds a CRAG-based assistant on Amazon Bedrock
Knowledge Bases and Agents for Amazon Bedrock, with a Lambda function
performing the web search fallback. The repository's own README quotes the
originating paper directly to explain why the sample exists, then documents
its two-scenario simplification of the pattern. Source.
aws-samples/simplified-corrective-rag repository,
https://github.com/aws-samples/simplified-corrective-rag, verified
2026-08-02.

## 10. Consequences

Positive.

- Converts an all-or-nothing trust in the retriever into a graded signal
  the pipeline can act on, closing the feedback gap that plain RAG lacks
  entirely, as described in dimension 2.
- Recovers from a coverage gap in a static or slow-changing corpus by
  falling back to a broader source, without re-indexing or retraining
  anything in the base retrieval pipeline itself.
- The knowledge refinement step improves even already-relevant retrieval by
  discarding the off-topic sections of a mostly-relevant passage, tightening
  what the generator actually sees.
- Because only a small evaluator needs training, or in the community ports
  in dimension 8 no training at all, CRAG plugs onto an existing RAG
  pipeline without touching the retriever or the generator.
- The three-way, or two-way, action label is a small, discrete, loggable
  signal, considerably easier to monitor and test in isolation than
  end-to-end answer quality, which dimension 15 and dimension 16 both build
  on.

Negative.

- Adds at least one, and in the faithful three-way variant several, extra
  model or classifier calls to every query's critical path, directly
  increasing latency and cost over plain RAG.
- Introduces a hard dependency on an external web search provider for the
  correction path, with that provider's own rate limits, cost structure, and
  reliability profile now part of the pipeline's failure surface.
- The evaluator becomes a new single point of failure whose own errors are
  invisible unless deliberately logged and audited. Dimension 11 describes
  exactly how a miscalibrated evaluator makes outcomes worse than doing
  nothing at all.
- Thresholds and the evaluator itself are tuned against a specific
  retriever, embedding model, and corpus combination, and none of that
  tuning transfers automatically to a different domain, adding an ongoing
  maintenance cost the base pipeline never carried.
- Blending internal and external knowledge on the Ambiguous path can
  produce answers that merge two sources of very different trust levels
  with no signal to the generator, or the end user, that a blend even
  happened.

## 11. Failure modes and misuse

**The evaluator overrides good retrieval silently.** Symptom. A query that
would have answered correctly from base RAG instead routes to web search,
and the answer gets noisier or actively worse than the unmodified pipeline
would have produced. Cause. The lightweight evaluator, whether a fine-tuned
classifier or a prompted LLM, is itself imperfectly calibrated for the
specific domain, and its misjudgment silently overrides an otherwise sound
retrieval. Fix. Log the evaluator's score and action on every query, sample
and compare cases where CRAG's action disagreed with what a human reviewer
would have judged, and treat evaluator accuracy as a monitored production
metric rather than an assumed constant.

**Thresholds miscalibrated for the deployed domain.** Symptom. After moving
the pipeline to a new corpus or a new retriever, either nearly every query
routes to the Incorrect branch, driving up latency and search cost, or
nearly none does, and irrelevant retrieval sails through unchecked. Cause.
The upper and lower thresholds reported in the originating paper were tuned
against its own benchmark datasets and retriever, and threshold values do
not transfer between retrievers, embedding spaces, or corpora. Fix.
Calibrate thresholds against a held-out labeled sample drawn from the actual
target domain and the actual deployed retriever before shipping, and re-run
that calibration whenever either changes.

**Untrusted web content reaches the generator unfiltered.** Symptom. A
generated answer contains an instruction the user never gave, a claim traced
back to an unreliable page, or content the model appears to be reacting to
rather than answering from. Cause. The Incorrect and Ambiguous branches
insert live, unmoderated third-party content directly into the generation
context, and that content is adversarially controllable in a way a fixed
internal corpus never is. Fix. Treat everything the web search branch
returns as untrusted tool output, sanitize and strip instruction-like text
from it before it enters the context, and apply the same input handling
discipline used for any other externally-sourced tool result in the
pipeline.

**Latency multiplies exactly on the hardest queries.** Symptom. Aggregate
p95 latency dashboards look acceptable, but the specific queries that trip
the Incorrect action, frequently the most out-of-distribution or hardest
queries, take several times longer than typical, because they now pay for
retrieval, evaluation, rewrite, search, refinement, and generation in
sequence. Cause. The corrective branches are additive on top of base RAG's
existing cost, and they activate precisely for the queries where the base
retriever already struggled, correlating the highest-latency path with the
highest-difficulty queries. Fix. Bound the web search branch with its own
timeout separate from the rest of the pipeline, degrade gracefully to a
caveated answer from the best available internal knowledge on timeout, and
track branch-specific latency as its own metric rather than only an
aggregate figure.

**Knowledge refinement discards a fact the generator needed.** Symptom. An
answer that used to be correct and complete when the full retrieved passage
was passed through becomes incomplete or wrong after the refinement step
runs, even though the original passage contained everything necessary.
Cause. Heuristic strip segmentation can cut a fact across two adjacent
strips, one graded relevant and one graded irrelevant, or a strip that reads
as irrelevant once separated from its surrounding sentence actually depended
on that context for its meaning. Fix. Retain a small window of surrounding
text with each surviving strip rather than discarding boundary context
outright, and log refined-versus-original passage pairs on any query where
downstream answer confidence is low, so information loss from refinement is
detectable rather than silent.

**Blended knowledge produces an unacknowledged contradiction.** Symptom. A
generated answer states two conflicting facts, one traceable to the internal
corpus and one to the web search fallback, without flagging that the two
disagree. Cause. When the Ambiguous action fires, internal refined
knowledge and external search results are concatenated into one context with
no signal distinguishing their source or reliability, and a generator
trained without such a distinction treats both as equally trustworthy
evidence. Fix. Tag each knowledge block with its source and, where
available, its recency, and prompt or train the generator to surface a
disagreement between sources rather than silently merging them into one
answer.

## 12. Trade-off matrix

Compared against named alternatives that address the same underlying problem
of getting a language model to reason reliably over retrieved or generated
content, across the forces from dimension 3.

| Force | Corrective RAG | Standard RAG (Lewis et al.) | Self-RAG (Asai et al.) | Agentic RAG | Reflexion | Routing |
|---|---|---|---|---|---|---|
| Extra training required | Small evaluator only, or none in prompted ports | None | Yes, the generator itself is fine-tuned | None beyond prompting | None | None |
| Inference-time cost added | One evaluator call always, more on non-Correct paths | None beyond retrieval | Reflection tokens add generation-time overhead, no separate call | Variable, an unbounded number of tool calls per turn | An extra generation pass per critique cycle | One routing decision per request |
| Corrects retrieval per document | Yes, that is its whole function | No | Indirectly, via the model's own retrieval-decision tokens | Yes, if the agent's loop includes a grading step | No, it critiques the final answer, not the retrieval | No, it selects which source to query, not whether the result is good |
| Requires an external fallback source | Yes, for the Incorrect and Ambiguous paths to add value | No | No | Optional, depends on the agent's tool set | No | No, it dispatches to one of several existing sources |
| Behavior deterministic given identical inputs | Deterministic once the evaluator and thresholds are fixed | Fully deterministic | Deterministic given a fixed fine-tuned model | Often non-deterministic, loop length varies | Non-deterministic, critique cycles vary | Deterministic given a fixed routing policy |
| Portable across an existing RAG pipeline | Yes, wraps an existing retriever and generator unchanged | Is the base pipeline | No, requires retraining the generator itself | Partial, requires restructuring into an agent loop | Partial, requires an outer critique loop | Yes, wraps an existing set of retrievers |

## 13. Related and incompatible patterns

**Retrieval Augmented Generation.** CRAG is a correction layer wrapped
around this base pattern, never a substitute for it. Every implementation
examined in dimension 9 still has an ordinary retriever and an ordinary
generator underneath. The evaluator, router, and refiner sit strictly
between the two, added to a pipeline that already exists rather than
replacing that pipeline's core.

**Routing.** The Action Router that picks Correct, Ambiguous, or Incorrect
is itself an instance of the Routing pattern, applied to knowledge-source
selection instead of the more familiar case of request dispatch across
services. Where the general Routing pattern typically routes on the
request's own content before any work happens, CRAG's router runs after a
first attempt at retrieval, using the outcome of that attempt as its routing
signal.

**Evaluator-Optimizer.** The family's own generic shape, generate, judge, and
regenerate on a bad judgment, is the pattern CRAG specializes for a single
concern, judging retrieval quality specifically, in a single pass, rather
than iterating an open-ended generate-judge-regenerate loop. CRAG never
re-runs its evaluator on the same document twice within one query. It scores
once, routes once, and moves on.

**Reflexion.** Reflexion's verbal self-feedback loop critiques a completed
generation and retries, operating strictly after the fact. CRAG's evaluator
scores retrieval strictly before generation happens. The two compose rather
than compete. A pipeline can run CRAG to correct bad retrieval and Reflexion
to catch a bad final answer, each addressing a different point in the
pipeline.

**Agentic RAG.** This repository's own Agentic RAG entry already discusses
CRAG's three-way grader as one design an agent's retrieval loop can adopt at
a single step of an otherwise open-ended, iteration-capped process. Read
CRAG as a specific, fixed-shape, single-pass instance of the same underlying
idea. It evaluates once and branches once per query, with no iteration cap
to configure because there is no iteration to bound. Agentic RAG is the more
general pattern. CRAG is a disciplined special case of it that a team can
adopt without building a full agent loop.

**Circuit Breaker.** The classical resilience pattern trips when a
downstream call is failing and reroutes around it. CRAG's Incorrect action
is a domain-specific circuit breaker that trips on a semantic judgment, this
retrieval is not good enough, rather than an operational one, this call is
erroring or timing out, and both share the identical evaluate-then-reroute
shape even though what each evaluates is entirely different.

**GraphRAG.** An orthogonal concern about how the underlying retrieval
traverses a knowledge graph rather than a flat vector index. CRAG's
evaluator can sit on top of either a flat retriever or a graph-based one
without caring which. The two patterns compose cleanly because neither
constrains the other's retrieval mechanism.

Nothing in this catalog is architecturally incompatible with CRAG in the
sense of the two mechanisms conflicting. The one genuine incompatibility is
of value rather than mechanism, described fully in dimension 4. Pairing CRAG
with a retriever that is already close to always correct on its target
domain makes the correction layer's expected value approach zero while its
cost stays fixed.

## 14. Refactoring path in and out

Introducing CRAG into a working base RAG pipeline.

1. Add an evaluator call that scores each retrieved document, in shadow
   mode, logging scores without acting on them yet. This produces the data
   needed to calibrate thresholds against real production traffic before any
   user-facing behavior changes.
2. Wire only the Incorrect branch first, the highest-value and lowest-risk
   piece. When every document scores below the lower threshold, discard the
   retrieval entirely and either fall back to an explicit "insufficient
   context" response or, if a fallback source is available, a web search.
   Verify this does not regress queries that were already answering
   correctly, since this branch by construction only fires on retrieval the
   base pipeline had no business trusting anyway.
3. Add the query-rewrite and web-search branch behind a feature flag, and
   monitor its latency and search-provider cost in isolation before
   widening the rollout, per dimension 16.
4. Add the Correct-path knowledge refinement, decompose-then-recompose,
   once the router itself is stable in production. This is deliberately the
   last piece added, because it improves already-good retrieval rather than
   catching bad retrieval, making it the lowest-urgency and hardest-to-tune
   part of the pattern, and dimension 11's refinement failure mode is worth
   revisiting before enabling it.
5. Split the Ambiguous action out from Incorrect once enough evaluator-score
   data has accumulated to justify placing a second threshold rather than
   the single-threshold Incorrect-only router most teams start with.

Removing CRAG, or simplifying it back toward plain RAG.

Audit the evaluator's own decisions against real traffic periodically. If
the audit shows the router routing to Correct on essentially all traffic
because the underlying retriever or embedding index has since been
upgraded and reliably returns relevant documents, the correction layer has
stopped earning its cost. Retire the evaluator, refiner, and web-search
branches back to plain retrieve-then-generate, keeping only a lightweight,
low-frequency sampling of evaluator scores as a canary in case retrieval
quality regresses again later. Removing an unused corrective layer removes
both its added latency on every query and its ongoing web-search provider
cost.

## 15. Testing and verification

Unit-test the router's threshold logic in isolation with a stub scorer
returning fixed values. Given a score at or above the upper threshold the
action must be Correct, given every score at or below the lower threshold
the action must be Incorrect, and anything in between must be Ambiguous.
This is exactly the property the runnable code examples in this entry
exercise, and it needs zero network access or a real model to verify.

Build a golden-set regression suite, a fixed collection of query, retrieved-
documents, and expected-action triples pulled from real production traffic,
re-run whenever the evaluator's model, prompt, or thresholds change. Because
the action is a small discrete label rather than free-form generated text,
this regression suite is far more tractable to maintain than an end-to-end
answer-quality suite, and it catches threshold drift before it reaches
production.

Inject the web search client and the evaluator as swappable dependencies,
exactly as the code examples in this entry do through the `Scorer`,
`Searcher`, and `Rewriter` types, so the routing and refinement logic can be
exercised with zero network calls and deterministic, hand-written stub
responses standing in for both the model and the search provider.

Run task-level evaluation against the same metrics the originating paper
used, exact-match accuracy for short-form factoid answers, a faithfulness
metric such as FactScore for long-form generation, on a held-out labeled
set, comparing CRAG's answers against plain RAG's answers on identical
queries so any lift or regression can be attributed to the correction layer
specifically rather than to noise elsewhere in the pipeline.

Adversarially test the web search branch on its own. Feed the search client
stub content containing instruction-like text and assert the generator's
final output does not follow it. This test doubles as a permanent regression
test for the untrusted-content failure mode described in dimension 11.

What became harder to test compared to plain RAG. Mocking now requires two
cooperating fakes, the evaluator and the search client, instead of one, and
because the pipeline's output depends on which action fired, snapshot or
golden-answer testing needs at least one fixture per branch rather than one
per query type, since the same query phrased two different ways can land on
different branches depending on what the evaluator sees.

## 16. Observability signals

Log the evaluator's score for every retrieved document alongside the action
that fired, as its own timeseries. The distribution across Correct,
Ambiguous, and Incorrect over a rolling window is the earliest, cheapest
signal available that either query traffic has shifted or the underlying
retriever has degraded, well before any downstream answer-quality metric
would notice.

Trace each branch as a distinct span, evaluate, route, then refine, or
rewrite-plus-search, then generate, so p50 and p95 latency are visible
per branch rather than only in aggregate. Dimension 11's latency failure
mode hides behind an aggregate dashboard specifically because the slowest
queries are a minority of total traffic. A per-branch view surfaces it
immediately.

Track the web-search branch's activation rate as a first-class metric on
its own dashboard. A sudden rise is either a genuine drop in retrieval
quality, an ingestion job broke or an index went stale, or a shift in query
topics toward something outside the corpus's coverage, and distinguishing
the two needs a dashboard correlating branch-activation rate against query
topic or cluster, not the activation rate alone.

Track web search provider cost and remaining rate-limit headroom
explicitly. A corrective layer with no cap turns what was previously a
fixed-cost RAG deployment into a variable, traffic-shaped cost, and the
provider's rate limit becomes a new availability dependency the base
pipeline never had.

A healthy instance shows a mostly-stable Correct rate with occasional,
explainable spikes in Incorrect or Ambiguous correlated to known, named
corpus gaps. A failing instance shows either branch rates flat-lined at one
extreme, the evaluator itself silently failing and defaulting to a single
branch, or thresholds badly miscalibrated, or an Incorrect rate climbing
steadily with no corresponding change to the corpus, which is the earliest
production signal of a genuine retriever regression.

## 17. Security and privacy implications

The web search branch is the pattern's primary new attack surface. It
inserts live, third-party content directly into the generation context, and
should be treated exactly like any other untrusted tool output, per
dimension 11's untrusted-content failure mode, with the same input
sanitization and instruction-stripping discipline applied to any external
tool result elsewhere in the pipeline.

Sending a query, whether verbatim or in its keyword-rewritten form, to an
external search provider is itself a data disclosure event. Whatever the
user asked, or a compressed version of it, leaves the organization's
boundary to a third-party API. For confidential or regulated queries this
matters independently of anything the search results themselves contain,
and is a reason dimension 4 lists regulated domains under strict sourcing
requirements as a non-applicability case rather than a variant to build
carefully.

Where the evaluator itself is a fine-tuned model, whatever internal
query-document pairs it was trained on can be memorized or leaked from the
model the same way any fine-tuned model can leak training data, so the same
data-handling review a fine-tuning pipeline receives elsewhere in an
organization applies here without exception.

The query-rewrite step is a place where an attacker-crafted input could be
transformed by the rewriting model into a search query engineered to
surface something the original query alone would not have, a risk one step
removed from the generator itself but still worth the same input-scrubbing
discipline applied to any LLM-mediated text transformation in the pipeline.

On privacy the pattern is otherwise neutral, with one practical control
worth adding rather than assuming exists by default. Where the base
retriever operates over access-controlled or sensitive internal documents,
gate whether the Incorrect and Ambiguous branches are even permitted to fire
based on the sensitivity classification of the query, so that a restricted
question never silently falls through to an open web search simply because
the internal retriever came up short.

## 18. References

1. Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, and Zhen-Hua Ling, "Corrective
   Retrieval Augmented Generation," arXiv:2401.15884, 2024,
   https://arxiv.org/abs/2401.15884, verified 2026-08-02.
2. Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir
   Karpukhin, Naman Goyal, Heinrich Kuttler, Mike Lewis, Wen-tau Yih, Tim
   Rocktaschel, Sebastian Riedel, and Douwe Kiela,
   "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,"
   NeurIPS 2020, arXiv:2005.11401, https://arxiv.org/abs/2005.11401,
   verified 2026-08-02.
3. Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, and Hannaneh Hajishirzi,
   "Self-RAG. Learning to Retrieve, Generate, and Critique through
   Self-Reflection," arXiv:2310.11511, 2023,
   https://arxiv.org/abs/2310.11511, verified 2026-08-02.
4. langchain-ai/langgraph repository, `examples/rag/langgraph_crag.ipynb`,
   https://github.com/langchain-ai/langgraph/blob/main/examples/rag/langgraph_crag.ipynb,
   verified 2026-08-02.
5. run-llama/llama_index repository,
   `llama-index-core/llama_index/core/command_line/mappings.json`,
   verified 2026-08-02.
6. LlamaIndex documentation, "Corrective RAG Workflow,"
   https://developers.llamaindex.ai/python/examples/workflow/corrective_rag_pack/,
   verified 2026-08-02.
7. aws-samples/simplified-corrective-rag repository,
   https://github.com/aws-samples/simplified-corrective-rag, verified
   2026-08-02.
8. Tavily, https://tavily.com, verified 2026-08-02.

## Code examples

Three languages, each implementing the same evaluate-then-branch control
flow, with the evaluator, the query rewriter, and the web search client
injected as plain functions so the routing and refinement logic can be
exercised with no network access and no real model, matching the testing
approach described in dimension 15.

### Python

```python
"""Corrective RAG: score retrieved documents, then branch on the
resulting confidence into refine, blend, or replace-with-search."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Sequence


class Action(Enum):
    CORRECT = "correct"
    AMBIGUOUS = "ambiguous"
    INCORRECT = "incorrect"


@dataclass(frozen=True)
class Document:
    text: str
    score: float = 0.0


Scorer = Callable[[str, str], float]
Searcher = Callable[[str], Sequence[str]]
Rewriter = Callable[[str], str]


@dataclass
class Thresholds:
    upper: float = 0.59
    lower: float = -0.99


def evaluate(query: str, docs: Sequence[str], scorer: Scorer) -> list[Document]:
    return [Document(text=d, score=scorer(query, d)) for d in docs]


def decide(scored: Sequence[Document], t: Thresholds) -> Action:
    if any(d.score >= t.upper for d in scored):
        return Action.CORRECT
    if all(d.score <= t.lower for d in scored):
        return Action.INCORRECT
    return Action.AMBIGUOUS


def split_strips(text: str, chunk: int = 8) -> list[str]:
    words = text.split()
    out = [" ".join(words[i : i + chunk]) for i in range(0, len(words), chunk)]
    return out or [text]


def refine(query: str, docs: Sequence[Document], scorer: Scorer,
           filter_at: float = -0.5) -> str:
    kept: list[str] = []
    for doc in docs:
        for strip in split_strips(doc.text):
            if scorer(query, strip) > filter_at:
                kept.append(strip)
    return " ".join(kept)


@dataclass
class CorrectiveRag:
    scorer: Scorer
    rewriter: Rewriter
    searcher: Searcher
    thresholds: Thresholds = field(default_factory=Thresholds)

    def answer(self, query: str, retrieved: Sequence[str]) -> tuple[Action, str]:
        scored = evaluate(query, retrieved, self.scorer)
        action = decide(scored, self.thresholds)

        if action is Action.CORRECT:
            knowledge = refine(query, scored, self.scorer)
        elif action is Action.INCORRECT:
            web_docs = self._search(query)
            knowledge = refine(query, web_docs, self.scorer)
        else:
            web_docs = self._search(query)
            internal = refine(query, scored, self.scorer)
            external = refine(query, web_docs, self.scorer)
            knowledge = f"{internal} {external}".strip()

        return action, knowledge

    def _search(self, query: str) -> list[Document]:
        search_query = self.rewriter(query)
        return [Document(text=t, score=1.0) for t in self.searcher(search_query)]


def _demo() -> None:
    def scorer(query: str, doc: str) -> float:
        keywords = {w.lower() for w in query.split() if len(w) > 3}
        return 0.8 if any(k in doc.lower() for k in keywords) else -1.0

    def rewriter(query: str) -> str:
        return " ".join(w for w in query.split() if len(w) > 3)

    def searcher(query: str) -> list[str]:
        return [f"web result about {query}"]

    rag = CorrectiveRag(scorer=scorer, rewriter=rewriter, searcher=searcher)

    action, knowledge = rag.answer(
        "what is python used for", ["Python is a general purpose language."]
    )
    print(action, "->", knowledge)

    action, knowledge = rag.answer(
        "what is the airspeed of a swallow", ["Unrelated travel brochure text."]
    )
    print(action, "->", knowledge)


if __name__ == "__main__":
    _demo()
```

Running this prints `Action.CORRECT -> Python is a general purpose
language.` for the first query, where a document overlapping the query's
keywords clears the upper threshold, and `Action.INCORRECT -> web result
about what airspeed swallow` for the second, where the unrelated retrieved
document falls beneath the lower threshold, the router discards it entirely,
and the refined web search result becomes the only surviving knowledge.

### TypeScript

```typescript
type Action = "correct" | "ambiguous" | "incorrect";

interface Passage {
  text: string;
  score: number;
}

interface Thresholds {
  upper: number;
  lower: number;
}

type Scorer = (query: string, doc: string) => number;
type Rewriter = (query: string) => string;
type Searcher = (query: string) => string[];

function evaluateDocs(query: string, docs: string[], scorer: Scorer): Passage[] {
  return docs.map((text) => ({ text, score: scorer(query, text) }));
}

function decide(scored: Passage[], t: Thresholds): Action {
  if (scored.some((d) => d.score >= t.upper)) return "correct";
  if (scored.every((d) => d.score <= t.lower)) return "incorrect";
  return "ambiguous";
}

function splitStrips(text: string, chunk = 8): string[] {
  const words = text.split(" ");
  const out: string[] = [];
  for (let i = 0; i < words.length; i += chunk) {
    out.push(words.slice(i, i + chunk).join(" "));
  }
  return out.length > 0 ? out : [text];
}

function refine(query: string, docs: Passage[], scorer: Scorer, filterAt = -0.5): string {
  const kept: string[] = [];
  for (const doc of docs) {
    for (const strip of splitStrips(doc.text)) {
      if (scorer(query, strip) > filterAt) kept.push(strip);
    }
  }
  return kept.join(" ");
}

class CorrectiveRag {
  private thresholds: Thresholds = { upper: 0.59, lower: -0.99 };

  constructor(
    private scorer: Scorer,
    private rewriter: Rewriter,
    private searcher: Searcher
  ) {}

  answer(query: string, retrieved: string[]): [Action, string] {
    const scored = evaluateDocs(query, retrieved, this.scorer);
    const action = decide(scored, this.thresholds);

    if (action === "correct") {
      return [action, refine(query, scored, this.scorer)];
    }

    const webDocs = this.search(query);

    if (action === "incorrect") {
      return [action, refine(query, webDocs, this.scorer)];
    }

    const internal = refine(query, scored, this.scorer);
    const external = refine(query, webDocs, this.scorer);
    return [action, `${internal} ${external}`.trim()];
  }

  private search(query: string): Passage[] {
    const rewritten = this.rewriter(query);
    return this.searcher(rewritten).map((text) => ({ text, score: 1 }));
  }
}

function demo(): void {
  const scorer: Scorer = (query, doc) => {
    const keywords = query
      .split(" ")
      .filter((w) => w.length > 3)
      .map((w) => w.toLowerCase());
    const lower = doc.toLowerCase();
    return keywords.some((k) => lower.includes(k)) ? 0.8 : -1.0;
  };

  const rewriter: Rewriter = (query) =>
    query
      .split(" ")
      .filter((w) => w.length > 3)
      .join(" ");

  const searcher: Searcher = (query) => [`web result about ${query}`];

  const rag = new CorrectiveRag(scorer, rewriter, searcher);

  const [action1, knowledge1] = rag.answer("what is python used for", [
    "Python is a general purpose language.",
  ]);
  console.log(action1, "->", knowledge1);

  const [action2, knowledge2] = rag.answer("what is the airspeed of a swallow", [
    "Unrelated travel brochure text.",
  ]);
  console.log(action2, "->", knowledge2);
}

demo();
```

The interface is named `Passage` rather than `Document` deliberately. A
top-level `interface Document` in a non-module TypeScript file merges by
declaration with the DOM library's ambient global `Document` type rather
than shadowing it, which produces a confusing type error at the call sites
below the declaration, worth knowing before reaching for the more obvious
name in any browser-adjacent TypeScript codebase.

### Go

```go
package main

import (
	"fmt"
	"strings"
)

type Action int

const (
	Correct Action = iota
	Ambiguous
	Incorrect
)

func (a Action) String() string {
	switch a {
	case Correct:
		return "correct"
	case Incorrect:
		return "incorrect"
	default:
		return "ambiguous"
	}
}

type Passage struct {
	Text  string
	Score float64
}

type Thresholds struct {
	Upper float64
	Lower float64
}

type Scorer func(query, doc string) float64
type Rewriter func(query string) string
type Searcher func(query string) []string

func evaluate(query string, docs []string, score Scorer) []Passage {
	out := make([]Passage, len(docs))
	for i, d := range docs {
		out[i] = Passage{Text: d, Score: score(query, d)}
	}
	return out
}

func decide(scored []Passage, t Thresholds) Action {
	allBelowLower := true
	for _, p := range scored {
		if p.Score >= t.Upper {
			return Correct
		}
		if p.Score > t.Lower {
			allBelowLower = false
		}
	}
	if allBelowLower {
		return Incorrect
	}
	return Ambiguous
}

func splitStrips(text string, chunk int) []string {
	words := strings.Fields(text)
	var out []string
	for i := 0; i < len(words); i += chunk {
		end := i + chunk
		if end > len(words) {
			end = len(words)
		}
		out = append(out, strings.Join(words[i:end], " "))
	}
	if len(out) == 0 {
		out = append(out, text)
	}
	return out
}

func refine(query string, docs []Passage, score Scorer, filterAt float64) string {
	var kept []string
	for _, doc := range docs {
		for _, strip := range splitStrips(doc.Text, 8) {
			if score(query, strip) > filterAt {
				kept = append(kept, strip)
			}
		}
	}
	return strings.Join(kept, " ")
}

type correctiveRag struct {
	score      Scorer
	rewrite    Rewriter
	search     Searcher
	thresholds Thresholds
}

func newCorrectiveRag(score Scorer, rewrite Rewriter, search Searcher) *correctiveRag {
	return &correctiveRag{
		score:      score,
		rewrite:    rewrite,
		search:     search,
		thresholds: Thresholds{Upper: 0.59, Lower: -0.99},
	}
}

func (c *correctiveRag) answer(query string, retrieved []string) (Action, string) {
	scored := evaluate(query, retrieved, c.score)
	action := decide(scored, c.thresholds)

	switch action {
	case Correct:
		return action, refine(query, scored, c.score, -0.5)
	case Incorrect:
		return action, refine(query, c.webSearch(query), c.score, -0.5)
	default:
		internal := refine(query, scored, c.score, -0.5)
		external := refine(query, c.webSearch(query), c.score, -0.5)
		return action, strings.TrimSpace(internal + " " + external)
	}
}

func (c *correctiveRag) webSearch(query string) []Passage {
	texts := c.search(c.rewrite(query))
	docs := make([]Passage, len(texts))
	for i, t := range texts {
		docs[i] = Passage{Text: t, Score: 1.0}
	}
	return docs
}

func main() {
	score := func(query, doc string) float64 {
		lower := strings.ToLower(doc)
		for _, w := range strings.Fields(query) {
			if len(w) > 3 && strings.Contains(lower, strings.ToLower(w)) {
				return 0.8
			}
		}
		return -1.0
	}

	rewrite := func(query string) string {
		var kept []string
		for _, w := range strings.Fields(query) {
			if len(w) > 3 {
				kept = append(kept, w)
			}
		}
		return strings.Join(kept, " ")
	}

	search := func(query string) []string {
		return []string{fmt.Sprintf("web result about %s", query)}
	}

	rag := newCorrectiveRag(score, rewrite, search)

	action, knowledge := rag.answer(
		"what is python used for",
		[]string{"Python is a general purpose language."},
	)
	fmt.Println(action, "->", knowledge)

	action, knowledge = rag.answer(
		"what is the airspeed of a swallow",
		[]string{"Unrelated travel brochure text."},
	)
	fmt.Println(action, "->", knowledge)
}
```

All three samples were compiled and executed directly, `python3`,
`npx tsc --strict` against a scratch project with `@types/node`, and
`go vet` followed by `go run`, and produce the identical two-line output
described above, letter for letter across all three languages. Java, Rust,
and Swift are omitted here. The pattern's substance is a decision-and-branch
control flow around pluggable model and search dependencies, which those
three languages express with the same shape as the ones shown, without a
language-specific idiom, an ownership constraint, a protocol-witness
dispatch, or the like, that changes how the pattern itself is structured.
