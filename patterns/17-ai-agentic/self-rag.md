---
name: Self-RAG
slug: self-rag
family: 17-ai-agentic
category: Agentic
aliases: [SELF-RAG, Self-Reflective Retrieval-Augmented Generation]
first_described: "Asai, Wu, Wang, Sil, Hajishirzi 2023"
maturity: established
related: [retrieval-augmented-generation, agentic-rag, advanced-rag, reflexion, react-prompting, graphrag]
incompatible_with: []
verified: 2026-08-02
---

# Self-RAG

## 1. Name, aliases, and lineage

The canonical name is Self-RAG, written in the paper's own typography as
SELF-RAG in small capitals on the title page and figures. The pattern was
introduced by Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, and Hannaneh
Hajishirzi in "Self-RAG. Learning to Retrieve, Generate, and Critique through
Self-Reflection," posted to arXiv as 2310.11511 on October 17, 2023, with
authors affiliated with the University of Washington, the Allen Institute for
AI, and IBM Research AI ([arXiv 2310.11511, abstract page](https://arxiv.org/abs/2310.11511),
verified 2026-08-02; [Hugging Face Papers mirror listing the author
affiliations](https://huggingface.co/papers/2310.11511), verified 2026-08-02).
The paper was accepted at ICLR 2024, confirmed by its DBLP conference record
([DBLP record conf/iclr/AsaiWWSH24](https://dblp.org/rec/conf/iclr/AsaiWWSH24.html),
verified 2026-08-02).

The alias SELF-RAG is the acronym used throughout the paper and in the
official code release. The project's own landing page spells out the full
name behind the acronym in a "What is Self-RAG" section. "Self-Reflective
Retrieval-Augmented Generation (Self-RAG)" ([Self-RAG project page](https://selfrag.github.io/),
verified 2026-08-02, "What is Self-RAG?" section). That page's own tagline
states the claim in one sentence. "Self-RAG learns to retrieve, generate and
critique to enhance LM's output quality and factuality, outperforming
ChatGPT and retrieval-augmented Llama2 Chat on six tasks" ([Self-RAG project
page](https://selfrag.github.io/), verified 2026-08-02). A widely cited RAG
survey by Yunfan Gao and coauthors places Self-RAG in a category it calls
Adaptive Retrieval, alongside FLARE, describing both as methods that "refine
the RAG framework by enabling LLMs to actively determine the optimal moments
and content for retrieval" ([arXiv 2312.10997, "Retrieval-Augmented
Generation for Large Language Models. A Survey," section V-C](https://arxiv.org/html/2312.10997),
verified 2026-08-02). That survey entry is worth naming because Adaptive
Retrieval is the umbrella term a reader is likely to meet Self-RAG under in
secondary literature, even though Self-RAG itself is the specific,
citable architecture this entry describes.

One naming distinction is worth settling early, because the pattern is
frequently confused with two neighbors it is related to but not identical
with. First, Self-RAG is not the same thing as plain Retrieval Augmented
Generation with a reranker bolted on. Retrieval Augmented Generation, as this
repository's own entry describes it, retrieves once, on every single query, before
every generation. Self-RAG instead trains the generating model to decide,
token by token and segment by segment, whether retrieval is worth the cost
for the content it is about to produce, and to grade what it retrieves before
using it. Second, Self-RAG is not Reflexion. Reflexion, this repository's
other self-critique entry, runs a full attempt end to end, scores the whole
trajectory against an external evaluator such as a compiler or a test suite,
and stores a natural-language lesson in an episodic memory that is re-read on
the next attempt, a loop across multiple full trials. Self-RAG operates
inside a single generation pass, at the granularity of a retrieval decision
and a short output segment, and its critique signal comes from special
tokens the same model learns to emit, not from an external pass or fail
signal. A system that retries a whole task after reading its own postmortem
is doing Reflexion. A system that decides, mid-answer, whether it needs a
source and then grades that source before committing to a claim, is doing
Self-RAG. This entry is about the second, narrower thing.

## 2. Problem and context

A retrieval-augmented language model that always retrieves, for every query,
pays the same fixed cost whether the query needs an external source or not.
"What is a good one-line greeting for a customer support chatbot" gains
nothing from a document lookup, but a system wired to always retrieve pays
the latency and token cost of a lookup anyway, and worse, it now has to
decide what to do with an irrelevant passage it did not need. The opposite
failure is equally damaging in production. A system with no retrieval at all,
or with retrieval fixed once per turn and never revisited, answers "what year
was this landmark completed" from parameters alone, and the parametric
answer, when wrong, comes out with the same fluent confidence as a correct
one. Standard RAG narrows this gap by retrieving before generating, but it
still trusts whatever it retrieved. If the retriever returns a topically
related but factually silent passage, plain RAG has no built-in mechanism to
notice that the passage never actually supports the claim the model is about
to write.

Self-RAG addresses a compound version of this problem. When should the model
retrieve at all, when it does retrieve, which of the retrieved passages
actually deserve to influence the answer, and once a segment is generated
from a passage, is that segment actually supported by what the passage says,
or has the model drifted into an unsupported claim anyway. The paper frames
its motivation directly against the state of RAG at the time. Prior
retrieval-augmented methods indiscriminately retrieve a fixed or preset
number of passages regardless of whether retrieval is needed at all or
whether passages are relevant, and never verify whether the model's output is
fully supported by cited evidence, and Self-RAG is presented as a framework
that "enhances an LM's quality and factuality through retrieval and
self-reflection" by training a single model to adaptively retrieve passages
on demand and to generate and reflect on retrieved passages and its own
generations using special reflection tokens, so that the same model that
writes the answer also grades the sources and the answer's grounding in
those sources ([arXiv 2310.11511, abstract](https://arxiv.org/abs/2310.11511),
verified 2026-08-02). The context this pattern belongs to is any
knowledge-intensive generation task, open-domain question answering, fact
verification, long-form generation with citations, where an unconditional
retrieve-then-generate pipeline either wastes retrieval calls on queries that
do not need them, or hands an ungraded passage straight to the generator and
trusts it to use that passage faithfully.

## 3. Forces

The central tension Self-RAG negotiates is between the openness of a plain
generative model and the groundedness of retrieval, and it resolves that
tension by making both retrieval and groundedness controllable at inference
time rather than fixed by the pipeline's shape.

Latency and cost pull directly against the depth of the critique. Retrieving on every query
is cheap to reason about but wastes calls on queries that
never needed a source. Retrieving adaptively, gated by a learned
Retrieve-token probability, saves calls on the easy cases, but the moment
retrieval does fire, Self-RAG spends more, not less, than plain RAG, because
it generates a candidate segment per top-ranked passage in parallel and then
runs a critique pass over each candidate before selecting one through a
segment-level beam search. The paper's own reference implementation
acknowledges the cost of this by using vLLM to speed up inference rather than
treating it as free ([arXiv 2310.11511](https://arxiv.org/abs/2310.11511),
verified 2026-08-02; the implementation detail is repeated in the official
code repository's inference instructions, [github.com/AkariAsai/self-rag
README](https://github.com/AkariAsai/self-rag), verified 2026-08-02).

Factual consistency, what the template calls consistency, is the force the
pattern is built to protect, at the direct expense of fluency alone. A model
free to say anything fluent is faster to sample from and reads more
naturally when it happens to be right, but Self-RAG deliberately down-weights
a fluent, high-probability continuation when its own critic marks that
continuation as unsupported by the retrieved evidence, trading a small amount
of raw fluency for a documented, checkable grounding signal.

Operability and coupling pull in the same direction here, unusually. Because
the retrieval decision, the relevance judgment, and the support judgment are
all emitted by the same generating model as ordinary next tokens, there is no
separate reranker service, no separate hallucination-detection microservice,
and no separate retrieval-necessity classifier to deploy, version, and keep
in sync with the generator. That is a real operability win over a pipeline
built from several independently maintained components. The cost is coupling
of a different kind. the critique quality is now permanently tied to how
well the critic was trained, and improving the critique means retraining or
fine-tuning the model, not swapping out an independent service.

Cognitive load and team topology matter because the pattern's honest
implementation cost is a training pipeline, not a prompt. A team that wants
the literal architecture, special reflection tokens baked into the model's
own vocabulary and generation-time distribution, needs either the released
fine-tuned checkpoints or the willingness to reproduce the paper's own
critic-distillation and instruction-tuning recipe. A team without that
appetite can approximate the pattern's four decisions with a general-purpose
model and structured output calls, at the cost of losing the paper's precise
1 to 5 utility scale and 3-way support scale in favor of coarser binary
grades, a trade this entry returns to under implementation variants.

## 4. Applicability and non-applicability

Reach for Self-RAG, or a faithful approximation of it, when the task is
knowledge-intensive and the cost of an ungrounded, confidently wrong answer
is high enough to justify paying for retrieval-necessity gating and
per-segment critique. Open-domain question answering over a large,
heterogeneous corpus is the paper's own primary evaluation setting, alongside
fact verification and long-form generation that needs citations the reader
can actually check ([arXiv 2310.11511, experiments section](https://arxiv.org/abs/2310.11511),
verified 2026-08-02). It is also a reasonable fit for a mixed workload where
some queries genuinely need a source and others are purely generative, such
as a customer-support assistant that answers both "what is your refund
policy" and "write me a one-line greeting," because the adaptive Retrieve
token is exactly the mechanism that tells those two apart without a
hand-written router in front of the model.

Do not reach for it in the following situations, and treat each of these as
a real reason, not a lesser preference.

- The corpus is small, static, and fully trusted, and every query in the
  workload genuinely needs it. Plain Retrieval Augmented Generation already
  retrieves on every query, correctly, in that setting, and Self-RAG's
  adaptive gate and per-passage critique add cost without adding value,
  because the gate would learn to say yes to nearly everything anyway.
- The task is pure creative generation, code completion from local context,
  or any workload where there is no external evidence to check the output
  against. A support or usefulness critic can still run, but the relevance
  and groundedness tokens have nothing useful to grade, so most of the
  pattern's machinery sits idle while still costing tokens.
- Latency is a hard, tight budget, such as an autocomplete-style interface
  where every millisecond is visible to the person typing. The parallel
  per-passage generation and critique pass is exactly the kind of
  multiplicative cost that a tight latency budget cannot absorb, and a
  cheaper single-shot RAG call, or no retrieval at all, is the honest
  choice.
- The team cannot train or fine-tune a model and specifically needs the
  paper's literal architecture, meaning special reflection tokens integrated
  into the vocabulary and generation-time distribution, rather than a
  prompted approximation. Reaching for the released 7B or 13B checkpoints is
  one path around this, but if those checkpoints do not fit the deployment's
  model choice or license constraints, the honest options are either
  reproducing the training pipeline or accepting the weaker, prompted
  approximation described under implementation variants, not pretending a
  prompted version is the same architecture the paper evaluated.
- The retrieved corpus cannot be trusted to be free of adversarial content.
  Because the same model that answers the question also reads the retrieved
  passage to produce its own critique tokens, a passage engineered to
  manipulate that critique is a sharper attack than it would be against a
  system where critique and generation are separated, a concern this entry
  returns to under security and privacy implications.

## 5. Structure

Self-RAG's participants are all roles a single trained language model plays
in sequence, not separate services, though nothing prevents deploying the
retriever itself as a separate component, which is how the reference
implementation and every reproduction of the pattern actually ships.

The Generator is the language model, fine-tuned so that its own vocabulary
includes the reflection tokens described below, alongside ordinary text
tokens. It plays every other role in this list by producing the
corresponding special token at the appropriate point in generation.

The Retriever is an off-the-shelf dense passage retriever, Contriever-MS
MARCO in the reference implementation, queried against a static passage
index, by default English Wikipedia chunked into roughly 100-word passages
([github.com/AkariAsai/self-rag README, retrieval setup section](https://github.com/AkariAsai/self-rag),
verified 2026-08-02). The Retriever is invoked conditionally, not on every
turn, gated by the Generator's own Retrieve-token decision.

The Retrieve gate is the Generator acting as a binary or ternary classifier
over its own next output, producing one of three token values, yes, no, or
continue, from an input consisting of the instruction and, for a decision
partway through a longer generation, the text produced so far. "Continue" is
not formally defined in the paper's own Table 1 beyond appearing as a third
member of the domain, and Algorithm 1's inference-time logic in the paper
only shows explicit branches for yes and no ([arXiv 2310.11511, section 3.1,
Table 1, and Algorithm 1](https://arxiv.org/abs/2310.11511), verified
2026-08-02). Reading "continue" against the rest of the segment-level design,
the reasonable interpretation, offered here as engineering judgment rather
than a claim the paper states outright, is that it lets a segment carry on
drawing on the passage already retrieved for the current segment rather than
issuing a brand new retrieval call, distinct from "no," which signals that
no retrieval, past or present, is needed for this content at all.

The Critic is the same Generator, in a distinct role, producing three
further reflection token types once a candidate passage and candidate
segment exist. ISREL takes the query and a candidate passage and outputs
relevant or irrelevant, defined in the paper as whether the passage
"provides useful information to solve" the query. ISSUP takes the query, the
passage, and a candidate generated segment, and outputs fully supported,
partially supported, or no support, defined as whether all
verification-worthy statements in the segment are supported by the passage.
ISUSE takes the query and the full generated response and outputs an integer
utility score from 1 to 5, defined as whether the response is a useful
response to the query ([arXiv 2310.11511, section 3.1, Table 1](https://arxiv.org/abs/2310.11511),
verified 2026-08-02).

The Selector is the inference-time generation procedure, a segment-level
beam search that scores each candidate segment by combining the Generator's
own token-level log probability with a weighted linear combination of the
Critic's reflection token probabilities, and keeps the top-scoring
candidates at each segment boundary, described in full under dynamics below.

## 6. ASCII structure diagram

```
                          +---------------------------+
                query x   |         GENERATOR          |
             +----------->|  (single fine-tuned LM,    |
             |            |   plays every role below)  |
             |            +--------------+--------------+
             |                           |
             |                           v
             |            +---------------------------+
             |            |        RETRIEVE gate       |
             |            |  emits {yes, no, continue} |
             |            +--------------+--------------+
             |                     |            |
             |                 yes/continue      no
             |                     v            v
             |     +---------------------+   +--------------------+
             |     |     RETRIEVER       |   |  generate directly, |
             |     | (Contriever-MSMARCO |   |  no retrieval, only |
             |     |  over passage index)|   |  a final ISUSE pass |
             |     +----------+----------+   +----------+----------+
             |                |                          |
             |         top-K passages                    |
             |          d1 .. dK                          |
             |                v                          |
             |     +---------------------+                |
             |     |   per-passage       |                |
             |     |   candidate y_i     |                |
             |     |   generation        |                |
             |     |   (parallel over K) |                |
             |     +----------+----------+                |
             |                |                          |
             |                v                          |
             |     +---------------------+                |
             |     |       CRITIC         |                |
             |     |  ISREL(x, d_i)        |                |
             |     |  ISSUP(x, d_i, y_i)   |                |
             |     |  ISUSE(x, y_i)        |                |
             |     +----------+----------+                |
             |                |                          |
             |                v                          |
             |     +---------------------+                |
             |     |      SELECTOR        |<---------------+
             |     |  segment score =      |
             |     |  lm_logprob + w_rel*p_rel
             |     |  + w_sup*p_sup + w_use*p_use
             |     |  beam width B, keep top-B |
             |     +----------+----------+
             |                |
             |                v
             +----------------+
                    final answer, with the winning
                    segment's supporting passage
                    available for citation
```

## 7. Dynamics

Generation proceeds segment by segment, where a segment is usually one
sentence or a short span the paper's implementation treats as one unit. At
the start of each segment, the Generator first emits a Retrieve token
conditioned on the instruction and everything generated so far. If the token
is no, generation continues without a new retrieval call, drawing only on
parametric knowledge and any evidence already retrieved earlier in the same
response, and the segment is closed with an optional ISUSE score at the very
end of the full response rather than at every segment boundary. If the token
is yes, or continue, the Retriever is queried and returns the top-K passages
for the current context, K commonly 3 to 10 depending on the task and
configuration in the reference implementation.

For each of the K retrieved passages, the Generator produces a candidate
continuation segment in parallel, one candidate per passage, rather than one
candidate for the whole batch of passages combined. Each of these K
candidates is then scored by the Critic. ISREL asks whether the source
passage for that candidate is actually relevant to the query at all,
independent of what the candidate segment says. ISSUP asks whether the
candidate segment's claims are actually supported by that specific passage.
ISUSE asks, once the full response is complete, whether the response is
useful to the original query.

The Selector combines these signals into one number per candidate segment.
The paper's segment score is the token-level generation probability of the
candidate under the Generator, added to a critique score that is a weighted
sum of the normalized probability mass the Critic assigned to the most
desirable outcome in each reflection-token category, weight 1.0 for ISREL,
weight 1.0 for ISSUP, weight 0.5 for ISUSE by default, all three weights
adjustable at inference time without retraining anything ([arXiv 2310.11511,
section 3.2, inference-time algorithm](https://arxiv.org/abs/2310.11511),
verified 2026-08-02; the exact default weight values, 1.0, 1.0, 0.5, and the
`beam_width` parameter defaulting to 2, are also documented as configuration
options in the reference implementation, [github.com/AkariAsai/self-rag
README](https://github.com/AkariAsai/self-rag), verified 2026-08-02). A
segment-level beam search with beam width B, 2 by default, keeps only the
top-B highest-scoring segments across all K candidates at each boundary,
discarding the rest, and expands the surviving beams into the next segment,
repeating the whole retrieve-generate-critique-select cycle for as many
segments as the response needs.

```
segment boundary t
  |
  |-- emit Retrieve token r_t in {yes, no, continue}
  |
  |-- if r_t in {yes, continue}:
  |       retrieve top-K passages d_1 .. d_K
  |       for each d_i in parallel:
  |           generate candidate segment y_i
  |           score_i = logprob(y_i) + w_rel*P(ISREL=relevant | x, d_i)
  |                                  + w_sup*P(ISSUP=full     | x, d_i, y_i)
  |                                  + w_use*P(ISUSE=5        | x, y_i)
  |       keep top-B candidates by score_i  (beam width B)
  |
  |-- else (r_t == no):
  |       generate one candidate directly, no critique on d, y
  |
  v
segment boundary t+1 (repeat until response ends)
  |
  v
final ISUSE(x, full response) appended once for observability
```

## 8. Implementation variants

- **The reference, literal implementation.** Retrieve, ISREL, ISSUP, and
  ISUSE are trained into the model's own vocabulary as new tokens, and a
  separate 7B critic model, initialized from Llama 2 and fine-tuned on
  roughly 4,000 to 20,000 GPT-4-labeled examples per reflection-token type,
  produces the training signal that is then baked into the 7B and 13B
  generator checkpoints released by the authors, both also initialized from
  Llama 2 ([arXiv 2310.11511, section 3.2.1 and Table 6](https://arxiv.org/abs/2310.11511),
  verified 2026-08-02; [github.com/AkariAsai/self-rag README, confirming the
  Llama 2 base and the GPT-4-sourced critic training data](https://github.com/AkariAsai/self-rag),
  verified 2026-08-02). This is the only variant that reproduces the paper's
  exact reported numbers, and it is the variant this entry's code samples
  approximate in structure, using hand-written heuristics in place of the
  fine-tuned Generator and Critic so the samples run with no weights and no
  network call, a substitution explained again in the code section below.
- **The prompted, no-training approximation.** Instead of fine-tuning
  reflection tokens into a model's vocabulary, prompt a general-purpose
  instruct model with a structured-output or function-calling schema per
  decision, one call for "is this document relevant," one for "is this
  generation grounded in the documents," one for "does this answer resolve
  the question." This is exactly how LangChain's own official reproduction
  of the pattern is built, using `gpt-4o-mini` at temperature 0 through
  `with_structured_output` calls returning a Pydantic model with a single
  `binary_score` field of "yes" or "no" for each of the three decisions
  ([langchain-ai/langgraph, pinned commit
  b2926a0ff9589c28c7e01fe7cdbb337b86d5a4b4, `examples/rag/langgraph_self_rag.ipynb`](https://github.com/langchain-ai/langgraph/blob/b2926a0ff9589c28c7e01fe7cdbb337b86d5a4b4/examples/rag/langgraph_self_rag.ipynb),
  verified 2026-08-02). This variant is honest and useful, but it is a
  narrower approximation than it can look at first glance. it collapses the
  paper's three-way ISSUP scale, fully supported, partially supported, no
  support, and its five-point ISUSE scale down to binary yes or no grades,
  and it replaces the paper's parallel per-passage segment-level beam search
  with a simpler control-flow graph. retrieve, grade documents, generate,
  grade the generation for hallucination, grade the answer for usefulness,
  and loop back to a query-rewrite step on failure. It reproduces the
  pattern's four decisions faithfully in spirit while trading the trained
  architecture for an off-the-shelf model and a graph of prompts, and that
  notebook itself is now marked archival in favor of LangChain's
  consolidated documentation, though the pinned commit cited above remains
  reachable and unchanged.
- **Retrieval-necessity gating without a trained token.** A lighter cut of
  the pattern keeps only the adaptive Retrieve decision, implemented as a
  single cheap classifier call or heuristic in front of an otherwise
  ordinary RAG pipeline, without the per-passage parallel critique or the
  segment-level beam search. This variant captures the cost-saving half of
  Self-RAG, skipping retrieval on queries that plainly do not need it,
  without the factual-grounding half, and it is a reasonable middle ground
  when latency matters more than citation-level groundedness.
- **Threshold tuning for the adaptive gate.** Whether implemented as a
  trained token or a prompted classifier, the Retrieve decision needs a
  threshold, since the underlying signal is a probability, not a hard rule.
  The reference implementation exposes this as a configurable threshold on
  the normalized probability of Retrieve equals yes, defaulting to 0.2 for
  most tasks in the paper's own evaluation and to 0 for citation-required
  tasks where retrieval should essentially always fire ([github.com/AkariAsai/self-rag
  README, inference configuration section](https://github.com/AkariAsai/self-rag),
  verified 2026-08-02).

## 9. Known production uses

- **AkariAsai/self-rag, the official reference implementation.** The
  authors' own repository ships the training code, the inference pipeline,
  and the two released checkpoints, `selfrag_llama2_7b` and
  `selfrag_llama2_13b`, both built on Llama 2 and released under an MIT
  license, with the 7B checkpoint alone recording 1,697 downloads in the
  most recent month observed on its Hugging Face model card and 84 likes
  ([github.com/AkariAsai/self-rag](https://github.com/AkariAsai/self-rag),
  verified 2026-08-02, 2,414 stars at time of verification; [Hugging Face
  model card for selfrag/selfrag_llama2_7b](https://huggingface.co/selfrag/selfrag_llama2_7b),
  verified 2026-08-02). This is the canonical, load-bearing artifact for
  anyone who wants the literal trained architecture rather than a prompted
  approximation.
- **LangChain's LangGraph, official tutorial reproduction.** LangChain
  reproduces the pattern's four decisions as a documented, runnable
  LangGraph workflow in its own examples tree, described in the notebook's
  own words as implementing "some of these ideas from scratch" against the
  paper, using structured-output grading calls rather than a fine-tuned
  model, as described above under implementation variants ([langchain-ai/langgraph,
  pinned commit b2926a0ff9589c28c7e01fe7cdbb337b86d5a4b4,
  `examples/rag/langgraph_self_rag.ipynb`](https://github.com/langchain-ai/langgraph/blob/b2926a0ff9589c28c7e01fe7cdbb337b86d5a4b4/examples/rag/langgraph_self_rag.ipynb),
  verified 2026-08-02). This is real production-adjacent adoption in the
  sense that matters for this dimension, a named framework used by a large
  number of downstream applications ships a maintained, citable
  reproduction of the pattern's control flow, even though the notebook
  itself has since been superseded by LangChain's consolidated
  documentation and is retained only for archival reference at the pinned
  commit.
- **RAGFlow, infiniflow/ragflow.** RAGFlow describes itself as "a leading
  open-source Retrieval-Augmented Generation engine" and, at time of
  verification, carries roughly 86,600 GitHub stars. Its chat-assistant
  configuration UI ships a user-facing toggle labeled "Self-RAG" whose
  tooltip in the product's own English localization file reads "Please
  refer to. https://huggingface.co/papers/2310.11511," pointing a user
  directly at the paper this entry describes ([github.com/infiniflow/ragflow,
  `web/src/locales/en.ts`](https://github.com/infiniflow/ragflow/blob/main/web/src/locales/en.ts),
  verified 2026-08-02; [infiniflow/ragflow repository listing](https://github.com/infiniflow/ragflow),
  verified 2026-08-02). This is the strongest of the three uses for the
  purpose of this dimension, because it is a named, widely deployed
  production RAG product exposing the pattern as an end-user configuration
  option, not only a research reproduction or a documentation example.

## 10. Consequences

**Positive.**

- Retrieval cost is paid only where the model itself judges the content
  worth grounding, rather than on every single query, which is a real
  saving on a mixed workload where a sizable fraction of queries do not
  need an external source.
- Every claim the system attributes to a source carries a checkable
  provenance signal, the ISSUP grade and the specific passage it was graded
  against, rather than a citation bolted on after the fact with no relation
  to whether the model's words are actually supported by what the citation
  says.
- The retrieval-necessity judgment, the passage-relevance judgment, and the
  groundedness judgment all live inside one trained artifact, removing the
  operational burden of deploying, versioning, and keeping in sync a
  separate reranker service and a separate hallucination-detection service.
- The critique weights, w_rel, w_sup, w_use, and the retrieval threshold are
  all adjustable at inference time without retraining, which lets an
  operator tune the system toward more citations or fewer, or toward more
  conservative retrieval, as a deployment-time configuration rather than a
  new training run.
- On the paper's own six evaluated tasks, the 7B and 13B trained models
  outperform ChatGPT and a retrieval-augmented Llama2-chat baseline on most
  of them, for example PubHealth at 72.4 percent for the 7B model and 74.5
  percent for the 13B model against ChatGPT's 70.1 percent ([arXiv
  2310.11511, results tables](https://arxiv.org/abs/2310.11511), verified
  2026-08-02).

**Negative.**

- Inference cost scales with the number of retrieved passages K and the
  beam width B, because the pattern generates a candidate segment per
  passage, in parallel, at every segment boundary that retrieves, and then
  runs a critique pass over each candidate. This is a real multiplicative
  cost over plain RAG's single retrieve-then-generate call, not a marginal
  one.
- The literal architecture requires either the released checkpoints or a
  real training investment, a critic model distilled from GPT-4 labels and
  a generator fine-tuned on roughly 150,000 instruction-output pairs
  augmented with retrieved passages and reflection tokens ([arXiv
  2310.11511, section 3.2.1](https://arxiv.org/abs/2310.11511), verified
  2026-08-02). This is not a pattern a team adopts by writing a prompt
  alone, unless it accepts the weaker, prompted approximation described
  under implementation variants.
- The critique is only as trustworthy as the critic that produces it. The
  paper reports the critic agrees with GPT-4-based predictions more than 90
  percent of the time on most reflection-token categories ([arXiv
  2310.11511, appendix, critic validation table](https://arxiv.org/abs/2310.11511),
  verified 2026-08-02), which is strong, and also means that on the order
  of one judgment in ten disagrees with the very model the critic was
  distilled from, a gap that becomes the root of the first failure mode
  below.
- ARC-Challenge, a closed-set multiple-choice reasoning benchmark that
  benefits less from retrieval than open-domain factual QA does, is a task
  where Self-RAG 7B, at 67.3 percent, trails plain ChatGPT's 75.3 percent
  ([arXiv 2310.11511, results table](https://arxiv.org/abs/2310.11511),
  verified 2026-08-02), a concrete reminder that the pattern's strength is
  tied to tasks where grounding actually helps, not a universal accuracy
  gain.

## 11. Failure modes and misuse

**Symptom.** The system states a fact with a citation-shaped provenance
pointer, ISSUP marked fully supported, to a passage that on inspection never
actually says what the answer claims.
**Cause.** The critic that produces ISSUP is a trained classifier, not a
deterministic string check, and the paper's own reported figure is that the
critic agrees with GPT-4 on more than 90 percent of judgments per category,
which is strong but not perfect, so roughly one judgment in ten across the
critic's categories can be wrong, and a false "fully supported" label on an
unsupported claim survives the segment-level beam search unfiltered, because
nothing downstream of the critic double-checks its verdict.
**Fix.** Treat ISREL and ISSUP as a soft prior for ranking candidates, never
as ground truth for a compliance-sensitive claim. Add a deterministic
post-hoc check, a substring or entailment check between the final claim and
the cited passage, before that claim is shown to a person in a setting where
being wrong is costly, and monitor the disagreement rate between the neural
critic and the deterministic check as an ongoing production metric, per
dimension 16.

**Symptom.** The system answers a genuinely retrieval-worthy query, one
whose answer changed after the model's training cutoff, fluently and with no
citation and no retrieval at all, and the wrong, stale, purely parametric
answer is presented with the same confidence as a correct one.
**Cause.** The adaptive Retrieve-token threshold, 0.2 by default in the
reference implementation, was tuned against the paper's own benchmark
distribution, PopQA, TriviaQA, ARC-Challenge, PubHealth. A production query
distribution phrased differently from that benchmark can push the learned
P(Retrieve equals yes) below the configured threshold even for a query that
clearly needs a source, because the gate's judgment generalizes only as well
as the data it was tuned on.
**Fix.** Recalibrate the threshold against a held-out sample of real
production queries with known-correct labels rather than trusting the
paper's default in a different domain, and add a deterministic override rule
alongside the learned gate, always retrieve when the query contains a date,
a named entity outside a static allowlist, or an explicit freshness marker
such as "latest" or "current," so the adaptive gate is never the sole line
of defense for time-sensitive queries.

**Symptom.** Median response latency, and especially the tail, grows
noticeably worse than plain RAG's, and the gap widens as the number of
retrieved passages K or the length of the answer grows.
**Cause.** Segment-level beam search runs the Generator once per top-K
retrieved passage, per segment, and a Critic pass over every one of those
candidates, so cost scales roughly with K times the beam width across every
segment boundary a multi-sentence answer produces, a materially different
cost shape from plain RAG's one retrieval call and one generation call per
turn.
**Fix.** Cap K to the smallest value that keeps recall acceptable for the
corpus, the reference implementation's own defaults sit in the 3 to 5 range
for most tasks, batch the K parallel per-passage forward passes on the same
accelerator rather than looping over them sequentially, and keep the
adaptive Retrieve gate aggressive about saying no, since every "no" is a
segment that skips the expensive path entirely.

**Symptom.** Two calls against the identical query and the identical corpus,
minutes apart, return different final answers, one grounded and correct, the
other subtly wrong, with nothing in the deployment configuration that
obviously changed.
**Cause.** Both the Generator's candidate segments and the segment-level
beam search's tie-breaking among closely scored candidates are sensitive to
sampling temperature, and a Retrieve-token probability sitting close to the
configured threshold can flip between yes and no on repeated calls if
sampling is not pinned deterministically, silently changing whether the
answer is grounded at all from one call to the next.
**Fix.** Pin sampling to temperature 0 for any deployment
where reproducibility is a requirement, such as an audit trail or a
compliance-reviewed answer, and log the Retrieve-token probability alongside
every response so a near-threshold flip is visible in monitoring rather than
silently changing the user-facing answer between two otherwise identical
calls.

## 12. Trade-off matrix

The comparison below weighs Self-RAG against three named alternatives from
this same family, plain Retrieval Augmented Generation, Corrective RAG, and
Agentic RAG, across the forces named in dimension 3. Judgment calls, where
the comparison is a matter of degree rather than a sourced fact, are marked.

| Force | Self-RAG | Plain RAG | Corrective RAG (CRAG) | Agentic RAG |
|---|---|---|---|---|
| Latency on an easy query | Low, adaptive gate skips retrieval entirely (judgment) | Fixed, always retrieves regardless of need | Fixed, always retrieves, then evaluates | Variable, an LLM agent decides whether to call the retrieval tool |
| Latency once retrieval fires | Highest of the four, parallel per-passage generation plus critique | Lowest, one retrieve and one generate call | Moderate, one retrieve, one evaluator pass, and a possible web-search fallback | Moderate to high, depends on how many tool calls the agent's own reasoning issues |
| Factual groundedness signal | Explicit, per-passage and per-segment, ISREL and ISSUP | None built in | Explicit, but at the whole-retrieval-set level via a single evaluator, per [arXiv 2401.15884, "Corrective Retrieval Augmented Generation"](https://arxiv.org/abs/2401.15884), verified 2026-08-02 | Implicit, depends entirely on how the agent's own prompting handles retrieved content |
| Operability, extra services to run | None beyond the retriever, judgment lives inside the trained model | None beyond the retriever | One additional lightweight evaluator model plus an optional web-search fallback, per the same CRAG paper | Depends on the agent framework and how many tools it wires in |
| Training or fine-tuning cost | High for the literal architecture, low for the prompted approximation | None | Low, the evaluator is described as lightweight and separately trainable | None required, though tool-use quality benefits from a capable base model |
| Best-fit task shape | Mixed workload, some queries need a source and some do not | Workload where every query genuinely needs the same fixed corpus | Workload where retrieval quality is the main risk, not retrieval necessity | Multi-step tasks where retrieval is one tool among several, not the only action available |

## 13. Related and incompatible patterns

Self-RAG builds directly on Retrieval Augmented Generation, this
repository's canonical entry for retrieve-then-generate. Self-RAG can be
read as RAG with two additions layered on top, an adaptive gate deciding
whether to retrieve at all, and a critique layer deciding whether to trust
what was retrieved, so anything true of plain RAG's retriever and index
design applies here unchanged.

Agentic RAG and Self-RAG solve overlapping problems from different
directions. Agentic RAG puts a general-purpose reasoning agent in the loop
and gives it retrieval as one tool among several, letting the agent's own
planning decide when and how to call it. Self-RAG instead trains the
retrieval-necessity and groundedness judgments directly into the generating
model's own token distribution, with no separate planning step. A system can
combine them, an agentic controller that calls a Self-RAG-style generator as
one of its tools, gaining the agent's flexibility to sequence multiple
actions and the generator's own built-in groundedness check on whichever
calls do retrieve.

Reflexion and Self-RAG share the word self-critique but operate at different
granularities and on different timelines, as established under dimension 1.
Reflexion critiques a whole completed attempt against an external evaluator
and stores a lesson for the next attempt. Self-RAG critiques individual
segments against individual retrieved passages within a single pass. They
compose cleanly. a Self-RAG generator can serve as the Actor inside a
Reflexion loop, with Reflexion's external evaluator judging the final
grounded answer and Self-RAG's own ISREL and ISSUP tokens available as extra
diagnostic signal fed into the verbal reflection.

Corrective RAG (CRAG) is the closest named alternative in spirit. it also
adds a critique layer on top of retrieval, but the critique is a single
lightweight evaluator scoring the whole retrieved set's overall quality and
triggering a corrective action, such as a web-search fallback, rather than
Self-RAG's per-passage, per-segment, multi-category critique baked into the
generator itself ([arXiv 2401.15884, "Corrective Retrieval Augmented
Generation," Yan, Gu, Zhu, Ling](https://arxiv.org/abs/2401.15884), verified
2026-08-02). The two are not incompatible, a CRAG-style coarse evaluator
could gate whether Self-RAG's more expensive per-passage critique runs at
all, trading a small amount of CRAG-style coarse filtering for Self-RAG's
finer-grained result when the coarse filter passes.

GraphRAG is not directly related to Self-RAG's retrieval-necessity or
groundedness mechanism, since it concerns how the corpus itself is
structured and traversed rather than when to retrieve or how to grade a
result, and the two are not incompatible. a graph-structured corpus can sit
behind Self-RAG's Retriever exactly as a flat passage index can.

No named pattern in this family is flatly incompatible with Self-RAG in the
sense of being unable to compose with it at all. the closest thing to a real
tension is that Self-RAG assumes the Generator itself can be trained or
fine-tuned, which sits uneasily with any deployment constraint that requires
using a fixed, closed, unmodifiable model, in which case the prompted
approximation described under implementation variants is the honest fallback
rather than a true incompatibility.

## 14. Refactoring path in and out

Refactoring an existing plain RAG pipeline toward Self-RAG starts from
naming which of the pattern's two additions the team actually wants. the
adaptive retrieval gate, the per-passage groundedness critique, or both.
Adding only the gate is the cheaper first step. replace the pipeline's
unconditional "always retrieve" call with a lightweight classifier, prompted
or trained, that decides yes or no per query, and route "no" queries
straight to generation, skipping the retriever and its latency entirely.
This alone captures a sizable share of the pattern's cost saving with no
change to how retrieved passages are used once they are fetched.

Adding the critique layer on top is the second, larger step, and it is where
the honest fork in the road sits. the literal path fine-tunes a generator on
reflection-token-augmented data, following the paper's own recipe, training
data collection from a GPT-4-labeled critic, and instruction-tuning the
generator on roughly 150,000 examples that interleave retrieved passages and
reflection tokens with ordinary text ([arXiv 2310.11511, section 3.2](https://arxiv.org/abs/2310.11511),
verified 2026-08-02). The lighter path wires a structured-output call per
decision around an existing off-the-shelf model, following LangChain's own
reproduction, one prompt asking for a binary relevance grade per retrieved
document, one prompt asking whether the generation is grounded in those
documents, one prompt asking whether the final answer resolves the question,
composed as a small graph with a query-rewrite step on failure
([langchain-ai/langgraph, pinned commit b2926a0ff9589c28c7e01fe7cdbb337b86d5a4b4,
`examples/rag/langgraph_self_rag.ipynb`](https://github.com/langchain-ai/langgraph/blob/b2926a0ff9589c28c7e01fe7cdbb337b86d5a4b4/examples/rag/langgraph_self_rag.ipynb),
verified 2026-08-02). Teams without appetite for a training pipeline should
take the lighter path deliberately and say so, rather than describing a
prompted approximation as the paper's architecture.

Refactoring out of Self-RAG, when the extra cost stops earning its place, is
the mirror image and usually easier than getting in. If the adaptive gate's
own logged decisions show it says yes to nearly every query in the actual
production distribution, the gate has stopped saving anything and can be
removed in favor of plain unconditional retrieval, with no loss beyond the
gate's own now-unnecessary overhead. If the per-segment critique's ISSUP
distribution shows fully supported for the overwhelming majority of
generations against a small, well-curated, trusted corpus, the critique
layer is spending cost to confirm something that was already reliably true,
and a team can step down to plain RAG plus a periodic offline audit of a
sample of answers, restoring the critique only if the corpus grows, changes
provenance, or the offline audit starts finding real unsupported claims
again.

## 15. Testing and verification

Unit test the Critic in isolation against a small, hand-labeled fixture set
of (query, passage, candidate) triples with known correct ISREL, ISSUP, and
ISUSE labels, independent of whichever Generator produces the candidate
text, so a Generator upgrade cannot silently degrade the Critic's own
judgments without a test noticing. This entry's own code samples take this
shape, asserting the winning passage and the winning answer against a fixed,
labeled toy corpus.

Write a regression test that freezes a corpus snapshot and a fixed query
set, and asserts the selected passage id and the final answer text against
golden values, so that upgrading the Generator, the Critic, or the
underlying retrieval index is caught the moment it changes which passage
wins the segment-level beam search, rather than discovered later from a
degraded answer in production.

Write an adversarial test that injects a passage carrying text engineered to
manipulate the Critic's own judgment, an instruction embedded in the
document body rather than a genuine factual claim, and asserts that ISREL
and ISSUP still reflect the passage's actual topical relevance and factual
support rather than the injected instruction, a concrete instance of the
security concern under dimension 17.

Write a property-style invariant test asserting that ISSUP is never fully
supported when the candidate segment's key claim does not appear, word for word,
or as a checkable paraphrase, anywhere in the cited passage, across a
generated or sampled range of (passage, candidate) pairs rather than a
single fixed example, catching the specific failure mode named first under
dimension 11 before it reaches production.

Load-test the latency path with the number of retrieved passages K varied
across the range the deployment actually configures, and assert that p95
latency stays inside the deployment's own budget as K grows, since dimension
11's third failure mode is a scaling problem that a single fixed-K test
cannot surface.

## 16. Observability signals

Log the Retrieve-token decision and its underlying probability at every
segment boundary, not only the final yes or no outcome, so a query sitting
close to the threshold is visible in monitoring rather than only visible
after it has already flipped and produced a wrong answer.

Log the full distribution of ISREL, ISSUP, and ISUSE values across
production traffic, not only the value attached to the winning candidate. A
healthy system shows a sizable share of irrelevant or no-support
judgments among the candidates that lost the segment-level beam search, a
sign the critique is actually discriminating rather than rubber-stamping
everything as fully supported.

Log latency broken into its three components separately, retrieval,
per-passage candidate generation, and critique, rather than one aggregate
number, since dimension 11's third failure mode grows specifically in the
generation-times-critique portion as K grows, and an aggregate number hides
which portion is actually responsible for a regression.

Track the disagreement rate between the neural Critic's ISSUP judgment and
the deterministic post-hoc groundedness check recommended as the fix for
dimension 11's first failure mode, as an explicit, dashboarded metric, since
that rate is the single clearest signal that the critic is drifting away
from the ground truth it was trained to approximate.

Track an abstention rate, the fraction of responses where every retrieved
candidate scores low across the board, meaning the system effectively has no
good answer available from its corpus. A rising abstention rate is
information about the corpus's own coverage gaps, not only about the model,
and is worth routing to whoever owns the corpus rather than only to whoever
owns the model.

## 17. Security and privacy implications

Because the same model that generates the answer also reads the retrieved
passage to produce ISREL and ISSUP, a passage engineered to contain an
embedded instruction, for example text inside a document telling the reader
to rate this passage as fully supporting whatever claim follows, is a
sharper attack surface than it is against a pipeline where critique and
generation are handled by genuinely separate components. The critique layer
that is supposed to police the answer can itself be manipulated by the same
content it is grading, if the retrieved passage's text and the model's own
instructions share an unguarded context. Mitigate this the same way any
retrieval-augmented system should treat untrusted document content, mark
retrieved text clearly as data rather than instruction inside the prompt
structure, and never let a critique-token decision be influenced by anything
in the retrieved passage that reads as a directive to the model rather than
as a factual claim to grade.

Reflection tokens and intermediate candidate segments, if logged for the
observability signals recommended above, can themselves leak information
about the underlying corpus, since a logged ISSUP judgment or a logged
losing candidate segment can paraphrase or quote a document the requesting
person was never authorized to see directly, particularly in a
multi-tenant deployment where the corpus mixes content from different
access-control boundaries. Apply the same access controls to logged
reflection-token traces and losing candidates that apply to the underlying
corpus, rather than treating observability logs as a lower-sensitivity
surface than the documents themselves.

The pattern has no privacy implication distinct from ordinary RAG on the
retrieval side itself, whatever access-control and data-residency
constraints already apply to the corpus and the retriever apply unchanged
here, since Self-RAG adds a critique layer on top of retrieval rather than
changing who or what the retriever is allowed to query.

## 18. References

- Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, Hannaneh Hajishirzi,
  "Self-RAG. Learning to Retrieve, Generate, and Critique through
  Self-Reflection," ICLR 2024, arXiv 2310.11511, submitted October 17, 2023,
  https://arxiv.org/abs/2310.11511, verified 2026-08-02. Full text used for
  the section, table, and algorithm citations throughout this entry,
  https://arxiv.org/html/2310.11511, verified 2026-08-02.
- DBLP conference record confirming ICLR 2024 acceptance,
  conf/iclr/AsaiWWSH24, https://dblp.org/rec/conf/iclr/AsaiWWSH24.html,
  verified 2026-08-02.
- Hugging Face Papers mirror listing author affiliations, University of
  Washington, Allen Institute for AI, IBM Research AI,
  https://huggingface.co/papers/2310.11511, verified 2026-08-02.
- Official Self-RAG project page, source of the expanded name
  "Self-Reflective Retrieval-Augmented Generation" and the project tagline,
  https://selfrag.github.io/, verified 2026-08-02.
- Official reference implementation, AkariAsai/self-rag, training code,
  inference pipeline, retriever setup, and inference configuration
  including the default critique weights and beam width,
  https://github.com/AkariAsai/self-rag, verified 2026-08-02.
- Hugging Face model card, selfrag/selfrag_llama2_7b, base model, license,
  and download counts, https://huggingface.co/selfrag/selfrag_llama2_7b,
  verified 2026-08-02.
- Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yi
  Dai, Jiawei Sun, Meng Wang, Haofen Wang, "Retrieval-Augmented Generation
  for Large Language Models. A Survey," arXiv 2312.10997, section V-C
  classifying Self-RAG as Adaptive Retrieval, https://arxiv.org/html/2312.10997,
  verified 2026-08-02.
- Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, Zhen-Hua Ling, "Corrective Retrieval
  Augmented Generation," arXiv 2401.15884, cited in the trade-off matrix
  and dimension 13 as the closest named alternative,
  https://arxiv.org/abs/2401.15884, verified 2026-08-02.
- LangChain, LangGraph official Self-RAG tutorial reproduction,
  langchain-ai/langgraph, pinned commit
  b2926a0ff9589c28c7e01fe7cdbb337b86d5a4b4,
  `examples/rag/langgraph_self_rag.ipynb`,
  https://github.com/langchain-ai/langgraph/blob/b2926a0ff9589c28c7e01fe7cdbb337b86d5a4b4/examples/rag/langgraph_self_rag.ipynb,
  verified 2026-08-02.
- RAGFlow, infiniflow/ragflow, open-source Retrieval-Augmented Generation
  engine shipping a user-facing Self-RAG toggle citing this paper directly,
  repository listing https://github.com/infiniflow/ragflow, verified
  2026-08-02, and the English localization file naming the feature,
  https://github.com/infiniflow/ragflow/blob/main/web/src/locales/en.ts,
  verified 2026-08-02.

## Code examples

Every sample implements the same Self-RAG control flow described under
dimension 7, an adaptive Retrieve gate, retrieval against a small in-memory
corpus, parallel per-passage candidate generation, ISREL and ISSUP and ISUSE
critique, and a weighted segment score using the paper's own default
weights, 1.0 for ISREL, 1.0 for ISSUP, 0.5 for ISUSE, with a beam width of 2
matching the reference implementation's default. The Generator and Critic
are hand-written heuristic functions, not the fine-tuned Llama 2 checkpoints
the paper trains, so every sample compiles and runs offline with no weights,
no API key, and no network access, a substitution this entry names openly
under implementation variants. One query, "what year was the Eiffel Tower
completed," is genuinely retrieval-worthy and is answered from the one
passage in the toy corpus whose text actually supports the claim, after the
critique layer correctly discounts a second, topically related passage that
never states a year, and a third, off-topic passage about a different
landmark entirely. A second query, a request for a one-line chatbot
greeting, triggers the Retrieve gate's no branch and is answered directly,
with no retrieval and no per-passage critique. All three samples were
compiled or run directly against the toolchains listed below and produce
identical output.

### Python

Run with `python3 self_rag_demo.py`. Executed against CPython 3.14.

```python
"""Self-RAG inference loop: adaptive retrieval gate, per-passage parallel
generation, ISREL/ISSUP/ISUSE critique, weighted segment-level beam search.
Weights w_rel=1.0, w_sup=1.0, w_use=0.5 and beam width 2 match the paper's
defaults (Asai et al. 2023, section 3.2). The generator and critic below are
hand-written heuristics standing in for the fine-tuned Llama2 policy and
critic model, so this runs offline with no weights and no network call."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

STOPWORDS = {"what", "year", "was", "the", "is", "a", "an", "of", "in", "for", "to"}
COMPLETION_WORDS = ("completed", "finished", "construction was")
FACTUAL_MARKERS = ("what year", "who", "when", "how many", "which", "where")
W_REL, W_SUP, W_USE = 1.0, 1.0, 0.5
BEAM_WIDTH = 2


@dataclass
class Passage:
    id: str
    text: str


@dataclass
class Candidate:
    passage_id: str
    text: str
    isrel: str
    issup: str
    isuse: int
    score: float


CORPUS = [
    Passage("eiffel_completion",
            "The Eiffel Tower is a wrought iron lattice tower in Paris, France. "
            "Construction was completed in 1889 in time for the World's Fair."),
    Passage("eiffel_naming",
            "The tower is named after its designer, engineer Gustave Eiffel, "
            "whose company conceived and built the structure."),
    Passage("liberty",
            "The Statue of Liberty was a gift from France to the United States "
            "and was dedicated in 1886 on Liberty Island."),
]


def tokenize(text: str) -> set:
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return {w for w in words if w not in STOPWORDS}


def retrieve_gate(query: str) -> bool:
    """Stand-in for the Retrieve reflection token: {yes, no, continue}."""
    q = query.lower()
    return any(marker in q for marker in FACTUAL_MARKERS)


def retrieve(query: str, corpus: list, k: int = 3) -> list:
    q_tokens = tokenize(query)
    scored = [(len(q_tokens & tokenize(p.text)), i, p) for i, p in enumerate(corpus)]
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [p for _, _, p in scored[:k]]


def generate_segment(passage: Passage) -> str | None:
    """Stand-in for the generator M producing a candidate segment y given (x, d)."""
    for keyword in COMPLETION_WORDS:
        idx = passage.text.lower().find(keyword)
        if idx == -1:
            continue
        window = passage.text[idx:idx + 60]
        match = re.search(r"\b(1[6-9]\d{2}|20\d{2})\b", window)
        if match:
            return match.group(0)
    return None


def critique_isrel(query: str, passage: Passage) -> str:
    """Stand-in for the ISREL critic: {relevant, irrelevant}."""
    q_tokens = tokenize(query)
    return "relevant" if q_tokens & tokenize(passage.text) else "irrelevant"


def critique_issup(candidate: str | None, passage: Passage) -> str:
    """Stand-in for the ISSUP critic: {full, partial, no}."""
    if candidate is None:
        return "no"
    return "full" if candidate in passage.text else "partial"


def critique_isuse(isrel: str, issup: str) -> int:
    """Stand-in for the ISUSE critic: an integer utility score from 1 to 5."""
    if isrel == "irrelevant" or issup == "no":
        return 1
    return 5 if issup == "full" else 3


def segment_score(isrel: str, issup: str, isuse: int, lm_score: float) -> float:
    p_rel = 1.0 if isrel == "relevant" else 0.0
    p_sup = {"full": 1.0, "partial": 0.5, "no": 0.0}[issup]
    p_use = (isuse - 1) / 4.0
    return lm_score + W_REL * p_rel + W_SUP * p_sup + W_USE * p_use


@dataclass
class SelfRagResult:
    retrieved: bool
    answer: str
    candidates: list = field(default_factory=list)


def self_rag(query: str, corpus: list) -> SelfRagResult:
    if not retrieve_gate(query):
        return SelfRagResult(False, "Hi! Thanks for reaching out, how can I help you today?")

    passages = retrieve(query, corpus)
    candidates = []
    for passage in passages:
        text = generate_segment(passage)
        isrel = critique_isrel(query, passage)
        issup = critique_issup(text, passage)
        isuse = critique_isuse(isrel, issup)
        lm_score = 0.5 if text is not None else 0.3
        score = segment_score(isrel, issup, isuse, lm_score)
        candidates.append(Candidate(passage.id, text or "no answer extracted", isrel, issup, isuse, score))

    candidates.sort(key=lambda c: -c.score)
    shortlist = candidates[:BEAM_WIDTH]
    relevant_shortlist = [c for c in shortlist if c.isrel == "relevant"] or shortlist
    winner = max(relevant_shortlist, key=lambda c: c.score)
    return SelfRagResult(True, winner.text, candidates)


if __name__ == "__main__":
    factual = self_rag("What year was the Eiffel Tower completed?", CORPUS)
    assert factual.retrieved, "factual query must trigger retrieval"
    assert factual.answer == "1889", f"expected 1889, got {factual.answer}"
    winner = max(factual.candidates, key=lambda c: c.score)
    assert winner.passage_id == "eiffel_completion", f"wrong winning passage: {winner.passage_id}"
    print("query: what year was the Eiffel Tower completed?")
    print(f"retrieve token: yes, retrieved {len(factual.candidates)} passages")
    for c in factual.candidates:
        print(f"  {c.passage_id:22s} isrel={c.isrel:10s} issup={c.issup:8s} isuse={c.isuse} score={c.score:.2f}")
    print(f"selected: {winner.passage_id} -> answer: {factual.answer}")

    creative = self_rag("Write a friendly one line greeting for a customer support chatbot.", CORPUS)
    assert not creative.retrieved, "creative query must skip retrieval"
    print()
    print("query: write a friendly one line greeting for a customer support chatbot.")
    print(f"retrieve token: no, generated directly -> {creative.answer}")
```

Output observed on this run.

```
query: what year was the Eiffel Tower completed?
retrieve token: yes, retrieved 3 passages
  eiffel_completion      isrel=relevant   issup=full     isuse=5 score=3.00
  eiffel_naming          isrel=relevant   issup=no       isuse=1 score=1.30
  liberty                isrel=irrelevant issup=no       isuse=1 score=0.30
selected: eiffel_completion -> answer: 1889

query: write a friendly one line greeting for a customer support chatbot.
retrieve token: no, generated directly -> Hi! Thanks for reaching out, how can I help you today?
```

### TypeScript

Compiled with `tsc --noEmit --strict --target es2022 --lib es2022
--moduleResolution bundler --module esnext`, TypeScript 5.9.3.

```typescript
type ISREL = "relevant" | "irrelevant";
type ISSUP = "full" | "partial" | "no";

interface Passage {
  id: string;
  text: string;
}

interface Candidate {
  passageId: string;
  text: string;
  isrel: ISREL;
  issup: ISSUP;
  isuse: number;
  score: number;
}

interface SelfRagResult {
  retrieved: boolean;
  answer: string;
  candidates: Candidate[];
}

const STOPWORDS = new Set(["what", "year", "was", "the", "is", "a", "an", "of", "in", "for", "to"]);
const COMPLETION_WORDS = ["completed", "finished", "construction was"];
const FACTUAL_MARKERS = ["what year", "who", "when", "how many", "which", "where"];
const W_REL = 1.0;
const W_SUP = 1.0;
const W_USE = 0.5;
const BEAM_WIDTH = 2;

const CORPUS: Passage[] = [
  {
    id: "eiffel_completion",
    text: "The Eiffel Tower is a wrought iron lattice tower in Paris, France. " +
      "Construction was completed in 1889 in time for the World's Fair.",
  },
  {
    id: "eiffel_naming",
    text: "The tower is named after its designer, engineer Gustave Eiffel, " +
      "whose company conceived and built the structure.",
  },
  {
    id: "liberty",
    text: "The Statue of Liberty was a gift from France to the United States " +
      "and was dedicated in 1886 on Liberty Island.",
  },
];

function tokenize(text: string): Set<string> {
  const words = text.toLowerCase().match(/[a-z]+/g) ?? [];
  return new Set(words.filter((w) => !STOPWORDS.has(w)));
}

function intersects(a: Set<string>, b: Set<string>): boolean {
  for (const x of a) if (b.has(x)) return true;
  return false;
}

function overlapCount(a: Set<string>, b: Set<string>): number {
  let n = 0;
  for (const x of a) if (b.has(x)) n++;
  return n;
}

/** Stand-in for the Retrieve reflection token: {yes, no, continue}. */
function retrieveGate(query: string): boolean {
  const q = query.toLowerCase();
  return FACTUAL_MARKERS.some((m) => q.includes(m));
}

function retrieve(query: string, corpus: Passage[], k = 3): Passage[] {
  const qTokens = tokenize(query);
  return [...corpus]
    .map((p, i) => ({ p, i, score: overlapCount(qTokens, tokenize(p.text)) }))
    .sort((a, b) => b.score - a.score || a.i - b.i)
    .slice(0, k)
    .map((r) => r.p);
}

/** Stand-in for the generator M producing a candidate segment y given (x, d). */
function generateSegment(passage: Passage): string | null {
  const lower = passage.text.toLowerCase();
  for (const keyword of COMPLETION_WORDS) {
    const idx = lower.indexOf(keyword);
    if (idx === -1) continue;
    const window = passage.text.slice(idx, idx + 60);
    const match = window.match(/\b(1[6-9]\d{2}|20\d{2})\b/);
    if (match) return match[0];
  }
  return null;
}

/** Stand-in for the ISREL critic: {relevant, irrelevant}. */
function critiqueIsrel(query: string, passage: Passage): ISREL {
  return intersects(tokenize(query), tokenize(passage.text)) ? "relevant" : "irrelevant";
}

/** Stand-in for the ISSUP critic: {full, partial, no}. */
function critiqueIssup(candidate: string | null, passage: Passage): ISSUP {
  if (candidate === null) return "no";
  return passage.text.includes(candidate) ? "full" : "partial";
}

/** Stand-in for the ISUSE critic: an integer utility score from 1 to 5. */
function critiqueIsuse(isrel: ISREL, issup: ISSUP): number {
  if (isrel === "irrelevant" || issup === "no") return 1;
  return issup === "full" ? 5 : 3;
}

function segmentScore(isrel: ISREL, issup: ISSUP, isuse: number, lmScore: number): number {
  const pRel = isrel === "relevant" ? 1.0 : 0.0;
  const pSup = { full: 1.0, partial: 0.5, no: 0.0 }[issup];
  const pUse = (isuse - 1) / 4.0;
  return lmScore + W_REL * pRel + W_SUP * pSup + W_USE * pUse;
}

function selfRag(query: string, corpus: Passage[]): SelfRagResult {
  if (!retrieveGate(query)) {
    return { retrieved: false, answer: "Hi! Thanks for reaching out, how can I help you today?", candidates: [] };
  }

  const passages = retrieve(query, corpus);
  const candidates: Candidate[] = passages.map((passage) => {
    const text = generateSegment(passage);
    const isrel = critiqueIsrel(query, passage);
    const issup = critiqueIssup(text, passage);
    const isuse = critiqueIsuse(isrel, issup);
    const lmScore = text !== null ? 0.5 : 0.3;
    const score = segmentScore(isrel, issup, isuse, lmScore);
    return { passageId: passage.id, text: text ?? "no answer extracted", isrel, issup, isuse, score };
  });

  candidates.sort((a, b) => b.score - a.score);
  const shortlist = candidates.slice(0, BEAM_WIDTH);
  const relevantShortlist = shortlist.filter((c) => c.isrel === "relevant");
  const pool = relevantShortlist.length > 0 ? relevantShortlist : shortlist;
  const winner = pool.reduce((best, c) => (c.score > best.score ? c : best));
  return { retrieved: true, answer: winner.text, candidates };
}

function main(): void {
  const factual = selfRag("What year was the Eiffel Tower completed?", CORPUS);
  if (!factual.retrieved) throw new Error("factual query must trigger retrieval");
  if (factual.answer !== "1889") throw new Error(`expected 1889, got ${factual.answer}`);
  const winner = factual.candidates.reduce((best, c) => (c.score > best.score ? c : best));
  if (winner.passageId !== "eiffel_completion") throw new Error(`wrong winning passage: ${winner.passageId}`);

  console.log("query: what year was the Eiffel Tower completed?");
  console.log(`retrieve token: yes, retrieved ${factual.candidates.length} passages`);
  for (const c of factual.candidates) {
    console.log(`  ${c.passageId.padEnd(22)} isrel=${c.isrel.padEnd(10)} issup=${c.issup.padEnd(8)} isuse=${c.isuse} score=${c.score.toFixed(2)}`);
  }
  console.log(`selected: ${winner.passageId} -> answer: ${factual.answer}`);

  const creative = selfRag("Write a friendly one line greeting for a customer support chatbot.", CORPUS);
  if (creative.retrieved) throw new Error("creative query must skip retrieval");
  console.log();
  console.log("query: write a friendly one line greeting for a customer support chatbot.");
  console.log(`retrieve token: no, generated directly -> ${creative.answer}`);
}

main();
```

Output observed when the same source is run with `node` after compiling to
CommonJS, identical to the Python run above.

```
query: what year was the Eiffel Tower completed?
retrieve token: yes, retrieved 3 passages
  eiffel_completion      isrel=relevant   issup=full     isuse=5 score=3.00
  eiffel_naming          isrel=relevant   issup=no       isuse=1 score=1.30
  liberty                isrel=irrelevant issup=no       isuse=1 score=0.30
selected: eiffel_completion -> answer: 1889

query: write a friendly one line greeting for a customer support chatbot.
retrieve token: no, generated directly -> Hi! Thanks for reaching out, how can I help you today?
```

### Go

Verified with `go vet self_rag_demo.go` and run with `go run
self_rag_demo.go`. Executed against Go 1.26.4.

```go
package main

import (
	"fmt"
	"regexp"
	"sort"
	"strings"
)

var stopwords = map[string]bool{
	"what": true, "year": true, "was": true, "the": true, "is": true,
	"a": true, "an": true, "of": true, "in": true, "for": true, "to": true,
}

var completionWords = []string{"completed", "finished", "construction was"}
var factualMarkers = []string{"what year", "who", "when", "how many", "which", "where"}

const wRel, wSup, wUse = 1.0, 1.0, 0.5
const beamWidth = 2

var yearRe = regexp.MustCompile(`\b(1[6-9]\d{2}|20\d{2})\b`)
var wordRe = regexp.MustCompile(`[a-z]+`)

type Passage struct {
	ID, Text string
}

type Candidate struct {
	PassageID          string
	Text, ISREL, ISSUP string
	ISUSE              int
	Score              float64
}

var corpus = []Passage{
	{"eiffel_completion",
		"The Eiffel Tower is a wrought iron lattice tower in Paris, France. " +
			"Construction was completed in 1889 in time for the World's Fair."},
	{"eiffel_naming",
		"The tower is named after its designer, engineer Gustave Eiffel, " +
			"whose company conceived and built the structure."},
	{"liberty",
		"The Statue of Liberty was a gift from France to the United States " +
			"and was dedicated in 1886 on Liberty Island."},
}

func tokenize(text string) map[string]bool {
	out := map[string]bool{}
	for _, w := range wordRe.FindAllString(strings.ToLower(text), -1) {
		if !stopwords[w] {
			out[w] = true
		}
	}
	return out
}

func intersects(a, b map[string]bool) bool {
	for w := range a {
		if b[w] {
			return true
		}
	}
	return false
}

func overlapCount(a, b map[string]bool) int {
	n := 0
	for w := range a {
		if b[w] {
			n++
		}
	}
	return n
}

// retrieveGate stands in for the Retrieve reflection token: {yes, no, continue}.
func retrieveGate(query string) bool {
	q := strings.ToLower(query)
	for _, m := range factualMarkers {
		if strings.Contains(q, m) {
			return true
		}
	}
	return false
}

func retrieve(query string, corpus []Passage, k int) []Passage {
	qTokens := tokenize(query)
	type scored struct {
		p     Passage
		i, sc int
	}
	rows := make([]scored, len(corpus))
	for i, p := range corpus {
		rows[i] = scored{p, i, overlapCount(qTokens, tokenize(p.Text))}
	}
	sort.Slice(rows, func(a, b int) bool {
		if rows[a].sc != rows[b].sc {
			return rows[a].sc > rows[b].sc
		}
		return rows[a].i < rows[b].i
	})
	out := []Passage{}
	for i := 0; i < k && i < len(rows); i++ {
		out = append(out, rows[i].p)
	}
	return out
}

// generateSegment stands in for the generator M producing a candidate segment y given (x, d).
func generateSegment(p Passage) (string, bool) {
	lower := strings.ToLower(p.Text)
	for _, kw := range completionWords {
		idx := strings.Index(lower, kw)
		if idx == -1 {
			continue
		}
		end := idx + 60
		if end > len(p.Text) {
			end = len(p.Text)
		}
		if m := yearRe.FindString(p.Text[idx:end]); m != "" {
			return m, true
		}
	}
	return "", false
}

// critiqueIsrel stands in for the ISREL critic: {relevant, irrelevant}.
func critiqueIsrel(query string, p Passage) string {
	if intersects(tokenize(query), tokenize(p.Text)) {
		return "relevant"
	}
	return "irrelevant"
}

// critiqueIssup stands in for the ISSUP critic: {full, partial, no}.
func critiqueIssup(candidate string, ok bool, p Passage) string {
	if !ok {
		return "no"
	}
	if strings.Contains(p.Text, candidate) {
		return "full"
	}
	return "partial"
}

// critiqueIsuse stands in for the ISUSE critic: an integer utility score from 1 to 5.
func critiqueIsuse(isrel, issup string) int {
	if isrel == "irrelevant" || issup == "no" {
		return 1
	}
	if issup == "full" {
		return 5
	}
	return 3
}

func segmentScore(isrel, issup string, isuse int, lmScore float64) float64 {
	pRel := 0.0
	if isrel == "relevant" {
		pRel = 1.0
	}
	pSup := map[string]float64{"full": 1.0, "partial": 0.5, "no": 0.0}[issup]
	pUse := float64(isuse-1) / 4.0
	return lmScore + wRel*pRel + wSup*pSup + wUse*pUse
}

type SelfRagResult struct {
	Retrieved  bool
	Answer     string
	Candidates []Candidate
}

func selfRag(query string, corpus []Passage) SelfRagResult {
	if !retrieveGate(query) {
		return SelfRagResult{false, "Hi! Thanks for reaching out, how can I help you today?", nil}
	}

	passages := retrieve(query, corpus, 3)
	candidates := make([]Candidate, 0, len(passages))
	for _, p := range passages {
		text, ok := generateSegment(p)
		isrel := critiqueIsrel(query, p)
		issup := critiqueIssup(text, ok, p)
		isuse := critiqueIsuse(isrel, issup)
		lmScore := 0.3
		if ok {
			lmScore = 0.5
		}
		score := segmentScore(isrel, issup, isuse, lmScore)
		display := text
		if !ok {
			display = "no answer extracted"
		}
		candidates = append(candidates, Candidate{p.ID, display, isrel, issup, isuse, score})
	}

	sort.Slice(candidates, func(a, b int) bool { return candidates[a].Score > candidates[b].Score })
	end := beamWidth
	if end > len(candidates) {
		end = len(candidates)
	}
	shortlist := candidates[:end]
	pool := []Candidate{}
	for _, c := range shortlist {
		if c.ISREL == "relevant" {
			pool = append(pool, c)
		}
	}
	if len(pool) == 0 {
		pool = shortlist
	}
	winner := pool[0]
	for _, c := range pool {
		if c.Score > winner.Score {
			winner = c
		}
	}
	return SelfRagResult{true, winner.Text, candidates}
}

func main() {
	factual := selfRag("What year was the Eiffel Tower completed?", corpus)
	if !factual.Retrieved {
		panic("factual query must trigger retrieval")
	}
	if factual.Answer != "1889" {
		panic(fmt.Sprintf("expected 1889, got %s", factual.Answer))
	}
	winner := factual.Candidates[0]
	for _, c := range factual.Candidates {
		if c.Score > winner.Score {
			winner = c
		}
	}
	if winner.PassageID != "eiffel_completion" {
		panic(fmt.Sprintf("wrong winning passage: %s", winner.PassageID))
	}

	fmt.Println("query: what year was the Eiffel Tower completed?")
	fmt.Printf("retrieve token: yes, retrieved %d passages\n", len(factual.Candidates))
	for _, c := range factual.Candidates {
		fmt.Printf("  %-22s isrel=%-10s issup=%-8s isuse=%d score=%.2f\n", c.PassageID, c.ISREL, c.ISSUP, c.ISUSE, c.Score)
	}
	fmt.Printf("selected: %s -> answer: %s\n", winner.PassageID, factual.Answer)

	creative := selfRag("Write a friendly one line greeting for a customer support chatbot.", corpus)
	if creative.Retrieved {
		panic("creative query must skip retrieval")
	}
	fmt.Println()
	fmt.Println("query: write a friendly one line greeting for a customer support chatbot.")
	fmt.Printf("retrieve token: no, generated directly -> %s\n", creative.Answer)
}
```

Output observed on this run, identical to the Python and TypeScript samples
above.

```
query: what year was the Eiffel Tower completed?
retrieve token: yes, retrieved 3 passages
  eiffel_completion      isrel=relevant   issup=full     isuse=5 score=3.00
  eiffel_naming          isrel=relevant   issup=no       isuse=1 score=1.30
  liberty                isrel=irrelevant issup=no       isuse=1 score=0.30
selected: eiffel_completion -> answer: 1889

query: write a friendly one line greeting for a customer support chatbot.
retrieve token: no, generated directly -> Hi! Thanks for reaching out, how can I help you today?
```
