---
name: Agentic RAG
slug: agentic-rag
family: 17-ai-agentic
category: AI Agentic
aliases: [Agent-Driven RAG, Adaptive RAG, RAG Agent, Agentic Retrieval]
first_described: "Term and taxonomy formalized in Singh, Ehtesham, Kumar, Khoei, Vasilakos 2025; the retrieval-plus-reasoning mechanism traces to Lewis et al. 2020 (RAG), Yao et al. 2022 (ReAct), and Asai et al. 2023 (Self-RAG)"
maturity: emerging
related: [retrieval-augmented-generation, react-prompting, reflexion, orchestrator-worker, routing, circuit-breaker]
incompatible_with: []
verified: 2026-08-02
---

# Agentic RAG

## 1. Name, aliases, and lineage

The canonical name in current practitioner and academic usage is Agentic RAG,
written as two words joined. "Agentic" describes the model's own capacity to
decide when and how to act, and "RAG" names the retrieval-augmented generation
technique it extends. The pattern has no single paper of origin the way many
entries in this catalog do. It is a composite of two separately published
ideas that practitioners fused together between 2023 and 2025, and the name
itself was only formalized as a taxonomy in Aditi Singh, Abul Ehtesham, Saket
Kumar, Tala Talaei Khoei, and Athanasios V. Vasilakos, "Agentic
Retrieval-Augmented Generation. A Survey on Agentic RAG," arXiv 2501.09136,
2025, verified 2026-08-02. The survey's abstract states that "Agentic
Retrieval-Augmented Generation (Agentic RAG) transcends these limitations by
embedding autonomous AI agents into the RAG pipeline," and classifies the
resulting systems along agent cardinality, control structure, autonomy, and
knowledge representation.

The base pattern Agentic RAG extends is Retrieval Augmented Generation itself,
described in Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni,
Vladimir Karpukhin, Naman Goyal, Heinrich Kuttler, Mike Lewis, Wen-tau Yih, Tim
Rocktaschel, Sebastian Riedel, and Douwe Kiela, "Retrieval-Augmented
Generation for Knowledge-Intensive NLP Tasks," accepted at NeurIPS 2020,
arXiv 2005.11401, verified 2026-08-02, which pairs a pre-trained seq2seq
model as parametric memory with a dense vector index accessed through a
pre-trained neural retriever as non-parametric memory. The retrieval step in
that original paper is fixed, one retrieval call per generation, chosen by
the pipeline author at design time, never by the model at run time.

The word "agentic" attached to that pipeline traces to two mechanisms
published two and three years later. Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan
Du, Izhak Shafran, Karthik Narasimhan, and Yuan Cao, "ReAct. Synergizing
Reasoning and Acting in Language Models," arXiv 2210.03629, 2022, verified
2026-08-02, describes generating both reasoning traces and task-specific
actions in an interleaved manner, giving a model a visible chain of thought
interspersed with tool calls it chooses to issue. Once a retriever is exposed
to a ReAct-style loop as one tool among several, the model decides for itself
whether, when, and how many times to call it, which is the behavioral
definition of Agentic RAG used across the sources gathered for this entry.

The second contributing mechanism is Akari Asai, Zeqiu Wu, Yizhong Wang,
Avirup Sil, and Hannaneh Hajishirzi, "Self-RAG. Learning to Retrieve,
Generate, and Critique through Self-Reflection," arXiv 2310.11511, 2023,
verified 2026-08-02, which trains the retrieval decision directly into a
model's weights through special reflection tokens rather than prompting a
general-purpose agent to reason about it. The paper reports that the model
"learns when retrieval is actually needed, retrieving on-demand based on the
specific query and generation context," and that it reflects on both the
retrieved passages and its own draft output before finalizing an answer.
Self-RAG and the prompted-agent variant of Agentic RAG are two different
implementation routes to the same behavioral goal, covered fully in dimension
8.

A third widely used alias, Adaptive RAG, names the specific variant that
routes a query to no retrieval, a single retrieval step, or a multi-step
agentic loop based on an estimate of the query's difficulty, and it appears
in several of the production references in dimension 9 as a cost-control
mechanism rather than a distinct pattern of its own.

Anthropic's engineering team supplies the general vocabulary this entry uses
to separate a fixed retrieval pipeline from an agentic one. "Workflows are
systems where LLMs and tools are orchestrated through predefined code paths.
Agents, on the other hand, are systems where LLMs dynamically direct their own
processes and tool usage, maintaining control over how they accomplish
tasks," and the same source lists retrieval explicitly as one of the
augmentations an agent is built from (Anthropic, "Building Effective Agents,"
https://www.anthropic.com/engineering/building-effective-agents, verified
2026-08-02). Under that vocabulary, plain RAG is a workflow with retrieval as
a fixed step, and Agentic RAG is what results once the retrieval step is
handed to the agent's own control loop.

Because the taxonomy is only months old at the time of writing, and different
vendors use the phrase to name different specific mechanisms, ranging from a
single tool-calling agent to a multi-agent hierarchy to a managed cloud
service that hides the loop entirely, this entry sets maturity to emerging
rather than established. What is settled is that the model decides whether
and how to retrieve, rather than a pipeline author deciding for it at design
time. What is not settled is which of the named variants in dimension 8
counts as the reference implementation, and whether Self-RAG's trained-in
behavior and a prompted ReAct loop over a retriever tool should be treated as
the same pattern or as two related ones.

## 2. Problem and context

Naive RAG performs exactly one retrieval and exactly one generation per user
turn, embed the query, fetch the top-k nearest chunks from a single index,
paste them into the prompt, generate. That single fixed pass is fast and
cheap, and it fails in four predictable, observable ways once a system moves
past a small, single-source demo.

First, a multi-hop question needs facts that live in more than one document,
and a single top-k search over the raw question rarely retrieves all of them
at once. A question like "did the vendor who missed the March deadline also
cause the April incident" needs one lookup for the March deadline and a
second, dependent lookup for the vendor's name against the April incident
record. A single-pass retriever searches the two clauses smashed into one
embedding and returns chunks that partially match both and fully match
neither.

Second, the corpus is heterogeneous. A real enterprise assistant answers
questions against a vector index of PDFs, a SQL table of order records, and a
live web search for anything published after the index was last built. A
single fixed retrieval step names exactly one of those sources at design
time, and a query that needs a different one returns nothing useful, so the
model, holding an empty or irrelevant context window, generates a fluent but
ungrounded answer.

Third, retrieval itself is not always successful even against the right
source. Chunking splits paragraphs across boundaries, embeddings drift on
domain-specific vocabulary, and the top-k cutoff sometimes excludes the one
chunk that actually answers the question while including several that merely
share vocabulary with it. A naive pipeline has no way to notice this
happened. It hands the model whatever came back and asks it to answer
regardless of quality.

Fourth, conversation state matters. "What about the Q2 numbers" only makes
sense with the previous turn's subject in view, and a fixed retrieval step
that only ever embeds the latest message loses that reference.

The observable symptom when these failures happen in production is confident,
well-formatted, factually wrong output, the model states an answer with the
same tone whether the retrieved context supports it or not, because nothing
in a naive pipeline distinguishes a retrieved chunk that answers the question
from one that is only noise. Agentic RAG exists to give the system a place to
notice that distinction and act on it, by moving the decisions of whether to
retrieve, from where, how to phrase the query, and whether the result is good
enough, out of the pipeline author's hands and into the model's own reasoning
loop, where they can be revisited turn by turn against the actual content
that came back.

## 3. Forces

**Latency against answer quality.** Every additional retrieval round, grading
pass, or query rewrite adds a full model call before the user sees a token.
Azure AI Search states this plainly about its own agentic retrieval feature,
"Agentic retrieval adds latency compared to a single-query pipeline, but it
handles query complexity that a single query can't" (Microsoft Learn,
"Agentic Retrieval Overview,"
https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview,
verified 2026-08-02). A system that needs a sub-second response cannot afford
an unbounded number of loop iterations no matter how much accuracy each round
would add.

**Cost, and specifically variable cost.** A fixed pipeline costs one
embedding call plus one generation call, a number a finance team can multiply
and forecast without difficulty. An agentic loop's cost depends on how many
subqueries the planner issues and how many correction rounds the grader
triggers, which changes per query. Azure's own documented cost model bills
separately for query-planning tokens and per-subquery reranking tokens, and
its own worked example prices a batch of 2,000 agentic retrievals, at three
subqueries each, at roughly $4.32 combined across the search and the planning
model, a figure that rises or falls directly with how aggressively the
reasoning-effort setting is dialed (same Microsoft Learn source).

**Determinism and testability.** A fixed pipeline is simple to write a
golden-answer regression test against, same input, same retrieval call, same
output shape. An agentic loop's path length, and the exact subqueries it
issues, can change between runs of the identical question if the planning
model samples at a nonzero temperature, which makes exact-match regression
testing brittle and pushes verification toward the rubric-based and
replay-based techniques covered in dimension 15.

**Coupling to a decision-making model.** The pipeline now depends on a
second model call, the planner or grader, in addition to the generator, and
that second call's judgment bounds the whole system's accuracy. A weak or
miscalibrated grader becomes the new bottleneck even when the underlying
retriever and generator are both strong, a failure mode detailed in
dimension 11.

**Operability and runaway loops.** A loop that decides for itself when it is
done needs an externally imposed stop condition, or a corpus with no answer
for a given query turns into a maximally expensive sequence of retries. This
is the same operational pressure that motivates the Circuit Breaker pattern
in distributed systems, and it recurs as the first entry in the failure-modes
table.

**Cognitive load for the team operating it.** A fixed pipeline has one code
path a new engineer can read start to end. An agentic loop has a branch tree
whose shape depends on runtime content, and reasoning about why it decided to
retrieve twice on a given request during an incident review takes materially
longer than reading a straight-line function. This particular observation is
reported here as a judgement call drawn from direct experience building and
operating loop-based retrieval systems, not from a cited source.

The pattern favors answer quality on hard, multi-hop, or ambiguous queries
over predictable latency, predictable cost, and ease of testing, and it is a
poor trade when the query population is mostly simple and the corpus is
mostly well organized, which leads directly into the applicability list in
dimension 4.

## 4. Applicability and non-applicability

### Applicability

Reach for Agentic RAG when at least one of these holds.

- The question population regularly includes multi-hop or compound questions
  that need facts stitched from more than one document or more than one
  source, the exact case described in dimension 2.
- The system has more than one knowledge source with different shapes, for
  example a vector index, a structured database, and a live web search, and
  the right source varies by question. This is exactly what Azure AI
  Search's agentic retrieval and the NVIDIA NeMo Retriever router both exist
  to route between, both cited fully in dimension 9.
- Retrieval quality on the corpus is uneven enough that a fixed top-k pass
  sometimes returns irrelevant chunks, and the team can tolerate paying for a
  second pass to check and correct that, which is the exact justification
  Yan et al. give for CRAG's retrieval evaluator.
- The conversation carries state, and a later turn depends on an earlier one,
  so query rewriting against conversation history genuinely changes what
  should be retrieved. Azure's documentation lists this as one of the query
  types agentic retrieval is built to handle, "questions that depend on
  earlier context in the conversation."
- The team is willing to trade predictable latency and predictable cost for a
  measurable reduction in ungrounded or incomplete answers, and has the
  observability described in dimension 16 in place to confirm that trade is
  actually paying off.

### Non-applicability

Do not reach for Agentic RAG, and prefer plain single-pass RAG or an even
simpler lookup instead, when any of these hold.

- The corpus is small, single-source, and well curated, for example a single
  product's FAQ or a single well-chunked manual. A grading and rewriting loop
  over a corpus that already retrieves well on the first pass adds cost and
  latency for no measurable accuracy gain, because there is nothing for the
  correction step to correct.
- The application has a hard, low latency budget, for example autocomplete
  suggestions or a real-time voice interface where a user notices a
  half-second delay. Azure's own documentation states its multi-query
  pipeline adds latency relative to a single query, and that added latency is
  disqualifying below a certain response-time budget regardless of the
  accuracy gain.
- The answer must be exactly reproducible for audit or regulatory reasons,
  and the organization cannot accept a planning model choosing a different
  subquery decomposition for the identical input on two different days. A
  fixed pipeline with a deterministic retrieval call is the only shape that
  satisfies bit-for-bit reproducibility. An agentic loop, even with
  temperature pinned to zero, still depends on model version and index
  snapshot in ways a deterministic pipeline does not.
- The cost model must be a fixed, uniform per-query number rather than a
  variable, token-metered one. Azure's own pricing table draws exactly this
  distinction, the classic single-query pipeline bills a uniform cost per
  query, while agentic retrieval bills a variable cost per token that depends
  on reasoning effort, and a variable bill is a real non-starter for some
  procurement and budgeting processes independent of the accuracy the feature
  buys.
- The retrieval step is a simple, exact, structured lookup, for example
  fetching a customer's order by ID. There is no ambiguity for an agent to
  reason about and no decomposition to perform, so a direct database read is
  faster, cheaper, and more reliable than routing the same lookup through an
  LLM-driven planner.

## 5. Structure

Agentic RAG names a family of participants that recur across every variant in
dimension 8, with different orchestration between them, but the same six
roles.

- **Orchestrator, the agent's control loop.** The model, or the graph node
  containing the model, that decides on every turn whether to call a
  retrieval tool, which tool, with what argument, and when the process is
  finished. In a ReAct-style implementation this is the same model that
  eventually writes the answer. In a managed platform such as Azure AI
  Search's agentic retrieval it is a dedicated planning call separate from
  the answer-synthesis call.
- **Query planner or decomposer.** Turns the user's raw question, plus any
  conversation history, into one or more concrete subqueries suited to the
  available retrieval tools. Azure names this step explicitly, stating that
  "the knowledge base sends your query and conversation history to an LLM,
  which generates focused subqueries."
- **Retriever, or a set of retrievers.** One callable per knowledge source,
  exposed to the orchestrator the same way any tool is exposed to a
  tool-calling model, a name, an argument schema, and a return type. A
  system can have several, for example a vector search retriever, a keyword
  retriever, a SQL retriever, and a web-search retriever, and the
  orchestrator's routing decision is which one a given subquery goes to.
- **Grader, or retrieval evaluator.** Scores whether the documents that came
  back actually answer the subquery. Yan et al. describe it as a lightweight
  component that "assesses retrieved document quality and assigns a
  confidence score, triggering different retrieval actions based on
  performance levels."
- **Rewriter.** Reformulates a subquery that scored poorly, either by adding
  context the first attempt lacked or by simplifying an overly specific
  phrasing, and hands the new query back to the retriever for another pass.
- **Synthesizer.** The final generation call that reads whatever context the
  loop assembled, from one pass or several, and writes the answer the user
  sees, along with, where the platform supports it, source references back
  to the specific documents used.
- **Scratchpad, or working memory.** The accumulating record of what has
  been tried, which subqueries were issued, what came back, what the grader
  said about each, and how many iterations have elapsed. This is what lets
  the loop notice it is repeating itself, the failure mode covered as
  symptom six in dimension 11, and what Azure exposes externally as an
  optional activity log alongside the merged content.

Not every variant instantiates all six as separate model calls. Self-RAG
collapses the orchestrator, grader, and rewriter into a single fine-tuned
model that emits reflection tokens inline with its own generation, rather
than running them as separate tool calls. The roles above still exist
conceptually inside that one model's forward pass. They are simply not
architecturally separate components.

## 6. ASCII structure diagram

```
                       +------------------------+
                       |      Orchestrator      |
                       |   (agent control loop) |
                       +-----------+------------+
                                   |
                                   v
                       +------------------------+
                       |    Query planner /     |
                       |      decomposer        |
                       +-----------+------------+
                                   |
                     +-------------+--------------+
                     |             |               |
                     v             v               v
              +-----------+ +-----------+   +-------------+
              |  Vector   | |   SQL /   |   |    Web      |
              | retriever | | structured|   |  search     |
              |           | | retriever |   |  retriever  |
              +-----+-----+ +-----+-----+   +------+------+
                    |             |                 |
                    +------+------+--------+---------+
                           |
                           v
                     +-----------+
                     |  Grader / |
                     | evaluator |
                     +-----+-----+
                           |
                low score  |  high score
              +------------+------------+
              |                         |
              v                         v
        +-----------+           +---------------+
        | Rewriter  |           |  Scratchpad   |
        | (new sub- |---------->|  (memory of   |
        |  query)   |  loop     |  tried queries|
        +-----------+  back     |  and results) |
                                +-------+-------+
                                        |
                                        v
                                 +-------------+
                                 | Synthesizer |
                                 | (final gen) |
                                 +-------------+
```

## 7. Dynamics

At run time the loop follows the same rough shape whether it is a hand
written ReAct agent or a managed platform such as Azure AI Search's knowledge
base, though the exact steps and their names differ by implementation.

1. The user sends a query, optionally with conversation history attached.
2. The orchestrator decides whether retrieval is needed at all. Self-RAG
   makes this an explicit, trained decision emitted as a reflection token
   before any retrieval happens. A prompted ReAct agent makes the same
   decision implicitly by choosing whether to emit a tool call. If the
   question can be answered from the conversation alone, the loop can skip
   straight to synthesis.
3. If retrieval is needed, the planner decomposes the query into one or more
   subqueries. Azure's own architecture description states this step is
   skipped entirely at its lowest reasoning-effort setting, where "queries
   are issued directly to knowledge sources," and only runs at its low and
   medium settings.
4. Subqueries run against their retrievers. Azure states these "run
   simultaneously," which is the common shape, independent subqueries fan
   out in parallel rather than one after another, since none depends on the
   others' results within a single planning round.
5. Retrieved documents are scored by the grader. CRAG's paper frames the
   grader's output as a small, bounded action set rather than a raw
   continuous number, correct, ambiguous, or incorrect, each triggering a
   different downstream branch, which gives the loop a bounded number of
   paths to reason about rather than an open-ended one.
6. On a low score, the rewriter reformulates the query and the loop returns
   to step 4 with the new query, subject to the iteration cap discussed in
   dimension 11. CRAG's alternative branch, rather than only rewriting,
   escalates to a web search when the local corpus itself is judged
   insufficient, which the NVIDIA NeMo Retriever blueprint implements as an
   explicit router branch that resorts to searching the web when local
   retrieval falls short.
7. Once a round scores acceptably, or the iteration cap is reached and the
   loop falls back to its last-resort branch, the accumulated context,
   everything retrieved and kept across every round, is handed to the
   synthesizer.
8. The synthesizer writes the final answer. In implementations that carry
   Self-RAG-style reflection all the way through, the model also
   critiques its own draft against the retrieved evidence before returning
   it, checking that generations are supported by the source material.
9. The answer is returned, optionally with source references and the full
   activity log of what was retrieved and why, which Azure exposes as an
   explicit, separately billed optional output.

```
User query
   |
   v
[decide: retrieve?] --no--> [synthesize] --> answer
   | yes
   v
[decompose into subqueries]
   |
   v
[run subqueries in parallel] <----------------+
   |                                          |
   v                                          |
[grade results]                               |
   |                                          |
   +--correct-------> [synthesize] --> answer |
   |                                          |
   +--ambiguous /                             |
   |  incorrect---> [rewrite query] ----------+
   |                (bounded by max_iterations)
   +--cap reached--> [web search fallback] --> [synthesize] --> answer
```

## 8. Implementation variants

**Single-agent tool-calling loop, the ReAct baseline.** The most common hand
rolled shape, a single model exposed to a retriever as one callable tool
among however many others the application needs, following the interleaved
reasoning-then-acting loop Yao et al. describe. LangChain's own reference
implementation frames this directly as flow engineering, describing a state
machine that lets a team "define a set of steps, for example retrieval, grade
documents, re-write query, and set the transitions options between them"
(LangChain, "Agentic RAG With LangGraph,"
https://www.langchain.com/blog/agentic-rag-with-langgraph, verified
2026-08-02). This variant is easy to reason about because every state and
transition is explicit code, and it is the variant most teams build first
because it needs no fine-tuning, only prompt design and tool schemas.

**Corrective RAG, CRAG.** Adds a dedicated retrieval evaluator between the
retriever and the generator, and a defined fallback when local retrieval
fails, escalate to web search rather than merely retrying the same index.
Yan, Gu, Zhu, and Ling describe this as a plug-and-play module compatible
with various RAG implementations, meaning it can wrap an existing naive RAG
pipeline without replacing the retriever or the generator, only inserting the
grading and correction step between them.

**Self-RAG.** Instead of prompting a general model to reason about
retrieval, this variant fine-tunes a model to emit special reflection tokens
as part of its own token stream, whether to retrieve, whether a retrieved
passage is relevant, whether the generation is supported by that passage, and
how useful the overall response is. Asai et al. report that this trained-in
behavior demonstrated improvements over ChatGPT and retrieval-augmented
Llama2-chat on question-answering, reasoning, and fact verification tasks, at
7B and 13B parameter scales. The trade this variant makes against the
prompted-agent variant is that it needs training data and a fine-tuning run,
and in exchange it needs no separate grader model call at inference time,
since the judgment is baked into the same forward pass that generates the
answer.

**Adaptive RAG.** Adds a classifier, sometimes a small model and sometimes
the same LLM asked a cheap preliminary question, that routes an incoming
query to one of several tracks before any retrieval happens, answer directly
with no retrieval, run one fixed retrieval pass, or hand the query to the
full agentic loop. This variant exists specifically to control the cost force
named in dimension 3. Azure's own reasoning-effort setting implements the
same idea at the platform level, stating that at minimal effort "this step
is skipped and queries are issued directly to knowledge sources," reserving
the LLM-driven decomposition for queries where low or medium effort is
explicitly configured.

**Multi-agent or hierarchical Agentic RAG.** A planner or supervisor agent
delegates subqueries to specialist retriever agents rather than calling
retriever tools directly itself, one specialist per domain or per source, and
merges their individual answers. Singh et al.'s survey names this as one axis
of its taxonomy, agent cardinality, distinguishing single-agent architectures
from multi-agent ones where retrieval responsibility is distributed across
cooperating agents rather than concentrated in one control loop. This variant
trades a simpler single loop for the ability to scale specialist knowledge
and access control per source independently, at the cost of coordination
overhead between the agents.

**Managed-platform variant.** Rather than writing the loop as application
code, the team configures a declarative knowledge base and lets the vendor's
own implementation run the loop. Azure AI Search's agentic retrieval is the
clearest example. The application "calls a knowledge base with a retrieve
action that provides a query and conversation history," and everything from
query planning through parallel subquery execution to reranking and merging
happens inside the managed service, configurable only through a small number
of parameters such as the reasoning-effort level and which knowledge sources
are attached. This variant trades control over the exact loop logic for
materially less code to write and operate, and it is the variant most likely
to appear first inside an organization that already runs its search
infrastructure on a managed cloud service rather than a self-hosted vector
database.

**Graph-based Agentic RAG.** Rather than, or in addition to, a vector or
keyword index, the retriever traverses a knowledge graph, following entity
relationships rather than embedding similarity, and the agent's decomposition
step decides which relationships to traverse for a given subquery. This is
the least standardized of the variants at the time of writing, and no single
production reference gathered for this entry implements it as its primary
retrieval mechanism, so it is named here as a documented direction in Singh
et al.'s taxonomy rather than illustrated with a running example.

## 9. Known production uses

**Microsoft Azure AI Search, agentic retrieval.** A shipped product feature,
not a research prototype. "Some agentic retrieval features are generally
available in the 2026-04-01 REST API via programmatic access," while the
Azure portal and Microsoft Foundry portal remain preview-only for the full
feature set (Microsoft Learn, "Agentic Retrieval Overview,"
https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview,
verified 2026-08-02). It powers Foundry IQ, described on the same page as
"the managed knowledge layer that transforms enterprise content into
reusable, permission-aware knowledge bases for agents in the Microsoft
Foundry portal," and it is directly usable as the retrieval backend for any
application built against Azure OpenAI, with the vendor publishing its own
token-based billing model for the feature, including a worked cost estimate
for a batch of 2,000 retrievals.

**NVIDIA, agentic RAG pipeline with Llama 3.1 and NeMo Retriever NIMs.** A
published reference architecture combining Meta's Llama 3.1 tool-calling
models with NVIDIA's NeMo Retriever embedding and reranking microservices,
described as pairing "structured outputs and multi-step reasoning" from
Llama 3.1 with enterprise-grade retrieval services from NeMo Retriever
(NVIDIA Developer Blog, "Build an Agentic RAG Pipeline with Llama 3.1 and
NVIDIA NeMo Retriever NIMs,"
https://developer.nvidia.com/blog/build-an-agentic-rag-pipeline-with-llama-3-1-and-nvidia-nemo-retriever-nims/,
verified 2026-08-02). The blueprint's router node makes the same
retrieve-or-fallback decision CRAG describes, deciding whether to answer from
local documents, resort to searching the web, or return an explicit "I don't
know" when neither source is sufficient.

**LangChain and LangGraph.** The open-source orchestration framework that
popularized flow engineering as the name for building CRAG and Self-RAG style
loops as explicit graphs of nodes and conditional edges, rather than as a
single monolithic prompt. LangChain's own documentation states its Deep
Agents primitives give developers "custom retrieval tools, a filesystem
backend, subagents, skills, and grading rubrics" specifically for building
retrieval-driven agents (LangChain docs, "RAG,"
https://docs.langchain.com/oss/python/langchain/rag, verified 2026-08-02),
and the framework is the most commonly cited reference implementation across
the other sources gathered for this entry, including NVIDIA's own blueprint,
which builds its router and grading nodes as a LangGraph state machine.

**LlamaIndex.** Ships agentic RAG as a first-class documented use case,
framed as building "a context-augmented research assistant over your data
that not only answers simple questions, but complex research tasks"
(LlamaIndex docs, "Agents,"
https://developers.llamaindex.ai/python/framework/use_cases/agents/, verified
2026-08-02), implemented by wrapping a query engine as a callable tool and
handing it to a function-calling or ReAct agent, the same tool-exposure
mechanism described in dimension 5.

Across these four, the pattern that recurs is a small number of frameworks
and one major cloud vendor supplying the orchestration and grading machinery
as a library or managed service, while the specific corpus, retrieval
evaluator thresholds, and fallback policy remain application-specific
configuration, consistent with CRAG's own description of itself as a
plug-and-play module compatible with various RAG implementations rather than
a complete standalone product.

## 10. Consequences

### Positive

- Materially better accuracy on multi-hop and ambiguous questions than a
  single fixed retrieval pass, because the loop can notice a first attempt
  was insufficient and try again with a different query or a different
  source rather than generating from whatever came back once.
- Retrieval happens only when the model judges it necessary rather than on
  every turn regardless of need. Asai et al. report Self-RAG's model "learns
  when retrieval is actually needed, retrieving on-demand based on the
  specific query and generation context," which for a large share of turns,
  greetings, clarifying follow-ups, questions already answered earlier in
  the conversation, avoids a retrieval call a fixed pipeline would pay for
  unconditionally.
- Answers can carry source references and a machine-readable trail of what
  was retrieved and why, which several of the production systems in
  dimension 9 expose as an optional output alongside the merged answer,
  giving a downstream reviewer something concrete to check the answer
  against.
- Handles heterogeneous corpora naturally, since the routing decision of
  which retriever to call for a given subquery is part of the same loop that
  decides whether to retrieve at all, rather than needing a separate,
  hand-maintained routing layer bolted in front of a fixed pipeline.

### Negative

- Latency rises with every additional round. Microsoft states its own
  agentic retrieval feature adds latency compared to a single-query
  pipeline, and that added latency is unavoidable in any variant that runs a
  planning call, retrieval, and grading before generation even starts, let
  alone one that loops.
- Cost becomes variable and harder to forecast. Azure's documented billing
  model charges separately for query-planning tokens and per-subquery
  reranking tokens, so the same application can cost noticeably more on a
  day its users happen to ask harder, more decomposition-heavy questions, a
  property a fixed, uniform-cost pipeline does not have.
- Debugging and regression testing are harder, because the exact path a
  query takes through the loop, how many subqueries, how many correction
  rounds, can differ between otherwise identical requests, which pushes
  verification toward the rubric-based and replay-based techniques in
  dimension 15 rather than simple exact-match assertions.
- The system's accuracy ceiling is bounded by the weakest link in a chain of
  two or more model calls, planner, grader, and generator, rather than by
  the generator alone, so a cheap or poorly calibrated grader can silently
  cap the whole pipeline's quality even when the generator itself is strong,
  the mechanism detailed as symptom three in dimension 11.

## 11. Failure modes and misuse

**Symptom.** Cost or latency spikes without warning, sometimes to the point
of a request timing out.
**Cause.** The retrieve-grade-rewrite cycle has no upper bound on how many
times it can loop, so a query the grader never scores as acceptable retries
repeatedly, bounded only by whatever ambient request timeout the surrounding
infrastructure imposes rather than a deliberate limit.
**Fix.** Cap the loop with an explicit maximum iteration count, and give the
loop a defined terminal fallback, CRAG's escalate-to-web-search branch or a
plain insufficient-information response, that always fires once the cap is
hit, so the loop's worst case is bounded and known in advance.

**Symptom.** The model still gives an ungrounded, hallucinated answer even
though a working retriever is available to it.
**Cause.** A prompted agent, unlike a model fine-tuned the way Self-RAG's is,
can simply choose not to call the retrieval tool on a question where it
should have, because its own parametric confidence about the answer
outweighs its prompted instinct to check. This is the gap Self-RAG's training
closes and a system prompt alone cannot fully close.
**Fix.** For high-stakes query classes, force a retrieval call rather than
leaving the decision entirely to the model's judgment, add an explicit
retrieval-necessity classifier ahead of the agent as in the Adaptive RAG
variant, or move to a model fine-tuned the way Self-RAG's is for domains
where this failure mode recurs often enough to justify the training cost.

**Symptom.** A document that would have answered the question correctly
exists in the corpus, but the final answer omits it or contradicts it.
**Cause.** The grader is the bottleneck rather than the retriever. If the
grading model is smaller, cheaper, or simply less capable than the
generator, it can misjudge a genuinely relevant document as irrelevant, or
the reverse, and its verdict decides whether that document ever reaches the
synthesizer at all.
**Fix.** Use a grading model at least as capable as the generator for
high-stakes applications, validate the grader's confidence threshold against
a held-out labeled set rather than an arbitrary default, and log every
grading decision, per dimension 16, so a wrong verdict is visible in review
rather than silently absorbed.

**Symptom.** The same question, asked twice, produces two different
answers, or two different sets of retrieved sources, on two separate runs.
**Cause.** The query planner samples at a nonzero temperature, so its
decomposition of an ambiguous question is not deterministic, and parallel
subqueries executing against an index that is itself changing between the
two runs compounds the effect.
**Fix.** Pin temperature to zero, or as near to it as the model API allows,
for the planning and grading calls specifically, even where the final
synthesis call keeps a higher temperature for prose quality, and cache a
query's decomposition against a normalized version of that exact query so
repeated identical questions reuse the same subqueries rather than
re-planning from scratch.

**Symptom.** The production bill is far higher than the team expected once
the system reaches real users.
**Cause.** The reasoning-effort or decomposition setting is configured
uniformly high for every query, so a simple, single-fact lookup pays the
same planning and multi-subquery reranking cost as a genuinely complex,
multi-hop one, which Azure's own worked cost example illustrates directly by
pricing query-planning and reranking tokens per subquery, with cost scaling
directly with subquery count.
**Fix.** Adopt the Adaptive RAG variant, routing simple queries to a cheap
single-retrieval or no-retrieval path and reserving the full agentic
decomposition, and its higher reasoning-effort setting, for queries a
lightweight upstream classifier flags as genuinely needing it.

**Symptom.** The loop keeps rewriting and re-retrieving without making
progress, eventually exhausting its iteration budget on a question it never
actually answers.
**Cause.** The rewriter has no memory of what it already tried, so it can
produce a semantically identical reformulation of a query that already
failed, sending the loop back to the same retriever with effectively the
same input and predictably the same poor result.
**Fix.** Keep a running record of every query variant already attempted this
turn, the scratchpad role described in dimension 5, and check a new rewrite
against it before issuing another retrieval call. If the rewriter would
produce a duplicate, skip straight to the terminal fallback rather than
consuming another iteration on a rewrite that cannot help.

## 12. Trade-off matrix

The comparison below is against four named alternatives. Plain Retrieval
Augmented Generation, the fixed single-pass pipeline Agentic RAG extends, the
general-purpose ReAct agent loop with retrieval as only one of several tools
and no RAG-specific grading step, the Orchestrator-Worker pattern applied
broadly rather than specifically to retrieval, and fine-tuning a model on
domain data instead of retrieving at query time at all.

| Force | Plain RAG | Agentic RAG | General ReAct loop | Orchestrator-Worker | Fine-tuning, no retrieval |
|---|---|---|---|---|---|
| Latency | Lowest, one retrieval and one generation call | Higher, scales with loop iterations | Similar to Agentic RAG when a retriever is one of its tools | Similar to Agentic RAG, plus worker coordination overhead | Lowest at inference, no retrieval call at all |
| Cost predictability | Fixed, uniform per query | Variable, token metered, scales with query complexity | Variable, same driver as Agentic RAG | Variable, plus per-worker call cost | Fixed inference cost, but a large upfront training cost |
| Accuracy on multi-hop questions | Low, a single pass cannot stitch facts across sources | High, this is the case it is built for | Comparable to Agentic RAG if the tool set and prompting are equivalent | High, if workers specialize by source | Depends entirely on training data coverage, worst on facts learned after the training cutoff |
| Freshness of knowledge | As fresh as the last index build | As fresh as the last index build, plus optional live web fallback | As fresh as the last index build | As fresh as the last index build | Frozen at training time, cannot see new facts without retraining |
| Determinism, testability | Easy, exact-match regression testing | Hard, needs rubric-based and replay-based testing per dimension 15 | Same difficulty as Agentic RAG | Same difficulty as Agentic RAG | Easy at inference, since there is no runtime retrieval decision to vary |
| Operational complexity | Low, one component to run | Moderate to high, a grader, a rewriter, and an iteration cap to maintain | Moderate, similar loop machinery, less RAG-specific tooling | High, multiple cooperating agents to deploy and monitor | Low at inference, but a real training and evaluation pipeline to operate |

Agentic RAG earns its place in the accuracy-on-hard-questions and
freshness-of-knowledge cells, where plain RAG and fine-tuning are both
weakest, and it pays for that gain in the cells where a fixed pipeline is
strongest, latency, cost predictability, and testability, which is the
direct restatement of the forces named in dimension 3.

## 13. Related and incompatible patterns

**Retrieval Augmented Generation.** The base pattern. Agentic RAG is best
read as RAG with its single fixed retrieval step replaced by a loop the
model itself controls. Every component named in dimension 5 exists in some
form inside plain RAG too, only collapsed into one non-branching sequence
rather than a loop with a grader and a rewriter.

**ReAct.** Agentic RAG is, in its most common single-agent implementation
variant, a specialization of the ReAct loop where the retriever is one
particular tool among the model's available tools, and the model's decision
of whether and how to call it follows the same interleaved
reasoning-then-acting mechanism Yao et al. describe generically for any
tool, not only a retriever.

**Reflexion.** Reflexion adds a self-critique and retry loop over an agent's
own past attempts at a task, learning from a failed attempt before trying
again. Self-RAG's reflection-token mechanism, described in dimension 8, is a
narrower, retrieval-specific instance of the same self-critique idea. Rather
than critiquing an entire task attempt, it critiques specifically whether a
retrieved passage was relevant and whether the generation it produced is
supported by that passage.

**Orchestrator-Worker.** The multi-agent variant of Agentic RAG described in
dimension 8 is a direct application of Orchestrator-Worker with the workers
specialized as retrieval agents over different sources, one worker per
domain or per knowledge source, coordinated by a planning orchestrator that
decomposes the incoming query and merges the workers' individual results.

**Routing.** Adaptive RAG, the variant that classifies a query's difficulty
before deciding how much of the agentic machinery to invoke, is a direct
application of the Routing pattern, with the router's destinations being
answer directly, single retrieval pass, and full agentic loop, rather than
the model-selection routing that pattern most commonly names.

**Circuit Breaker.** Not a data-flow relationship but a structural one
borrowed from resilience engineering. The iteration cap that bounds the
retrieve-grade-rewrite loop, described as the fix for the first failure mode
in dimension 11, plays the same operational role a circuit breaker plays in
a distributed system, tripping a hard limit once a call keeps failing rather
than allowing an unbounded number of retries against a dependency that is
not going to succeed.

**Tension with strict low-latency request-response systems.** Agentic RAG is
not incompatible with any other named pattern in this catalog in the sense of
the two conflicting structurally, but it is in real tension with any system
design committed to a hard, sub-second response budget, since every variant
in dimension 8 adds at least one extra model call, planning, grading, or
both, before generation even begins, the same latency force named in
dimension 3 and the same disqualifying condition named in the
non-applicability list in dimension 4.

## 14. Refactoring path in and out

### Introducing Agentic RAG into a naive RAG pipeline

1. Start from the working naive pipeline, one retrieval call, one generation
   call, no branching. Confirm it has a passing regression suite of golden
   questions and expected answers before touching anything, so later steps
   have a baseline to compare against.
2. Wrap the existing retriever behind a callable tool schema, a name, a
   description, and an argument shape the orchestrator model can invoke,
   rather than calling it directly from application code. This step alone
   changes nothing about behavior. It only makes the retriever addressable
   by a model.
3. Replace the fixed always-call-the-retriever-once logic with an
   orchestrator model given the tool from step 2 and instructed, ReAct
   style, to decide for itself whether and when to call it. Confirm on the
   regression suite that answers on simple questions are unchanged. This is
   the point where the loop becomes agentic in the behavioral sense used
   throughout this entry.
4. Add a grading step, the CRAG-style retrieval evaluator, immediately after
   retrieval, scoring whether what came back actually answers the current
   subquery. Confirm on the same regression suite, plus a new set of
   deliberately hard, multi-hop questions, that the grader correctly
   distinguishes good and bad retrievals before wiring its verdict to any
   downstream behavior.
5. Wire the grader's low-confidence branch to a query rewriter, and the
   rewriter's output back into another retrieval call, closing the loop.
   This is also the point at which the iteration cap from the first fix in
   dimension 11 must be added. Do not close the loop without it.
6. Add the terminal fallback, web search escalation, a plain
   insufficient-information response, or both, for the case where the cap is
   reached without the grader ever scoring the result as acceptable.
7. Only after steps 1 through 6 are stable, if the corpus genuinely spans
   multiple heterogeneous sources with different access patterns, consider
   splitting the single orchestrator into a planner plus specialist worker
   agents per source, the multi-agent variant from dimension 8. This step is
   optional and adds real coordination overhead. Do not take it unless step
   2's single retriever tool has already become several retriever tools the
   one orchestrator is struggling to route between well.

### Removing Agentic RAG once it stops earning its place

The loop is a cost worth paying only while its branches are actually
exercised in ways that change the answer. Two concrete signals justify
collapsing it back toward a simpler pipeline.

- The observability data from dimension 16 shows the loop settles into the
  same small number of paths for the overwhelming majority of real queries,
  for example always exactly one retrieval, always graded acceptable on the
  first pass, for most production traffic. When that is true, the loop's
  decision-making adds latency and cost without changing the outcome for
  most requests, and the stable common path can be hard-coded back into a
  fixed pipeline, keeping only the grading step as a lightweight sanity
  check on the now-fixed retrieval call rather than as the entry point to a
  full rewrite loop. This is the same instinct behind compiling a hot path
  into a specialized fast case once profiling shows which branch actually
  runs in practice, the general principle this catalog covers under inline
  caching and hot-path specialization in the performance pattern families.
- The corpus has been consolidated or re-indexed well enough that the
  failure modes motivating the grader in the first place, poor chunking,
  uneven embedding quality, missing sources, no longer occur often enough to
  justify a second model call on every request. When retrieval quality
  genuinely improves at the source, the correction step it was compensating
  for can be removed rather than kept as permanent overhead.

## 15. Testing and verification

**Golden-query regression sets with expected retrieved sources.** Build a
fixed set of representative questions, each with the specific document IDs
or source references a correct answer should be grounded in, and assert the
loop's final answer cites at least those references, rather than asserting
an exact string match on the generated prose, since the exact wording can
vary between runs even when the grounding is correct. LlamaIndex's own
agentic RAG documentation names grading rubrics as one of the primitives it
ships specifically for this kind of evaluation.

**Deterministic replay against a frozen snapshot.** Log the full activity
trail, every subquery issued, every document retrieved, every grading
verdict, the same optional output several production systems in dimension 9
expose, and replay a captured production request against a frozen index
snapshot in a test environment to confirm the loop reaches the same
conclusion offline that it reached live. This is the practical way to
reproduce and diagnose a specific reported failure without needing the loop
to be fully deterministic in general.

**Mock the retriever, not the model, when testing the loop's decision
logic.** Replace the real vector index or web search tool with a stub that
returns fixed, hand-authored documents, and use it to test whether the
orchestrator, grader, and rewriter make the right decisions given a known
input, independent of whatever the real index happens to return on a given
day. This isolates whether the loop's decision logic works from whether the
index is any good today, two genuinely separate questions that a test suite
calling the real retriever conflates.

**Adversarial never-satisfied grader test.** Configure a test double for the
grader that always reports low confidence no matter what it is given, and
confirm the loop still terminates within its configured iteration cap and
returns the defined fallback response rather than hanging or erroring. This
is a direct test of the fix for the first failure mode in dimension 11, and
it should be part of every agentic loop's test suite regardless of how
unlikely a genuinely unanswerable query is expected to be in real traffic.

**Property-based checks on the loop's own invariants.** Rather than only
checking specific input-output pairs, assert properties that must hold
across the whole space of possible queries. The number of retrieval calls
issued for any single request never exceeds the configured maximum, the
planner and grader are idempotent at temperature zero, given the identical
query and identical index state, the same subqueries are issued twice in a
row, and the rewriter never issues a subquery that exactly duplicates one
already in the scratchpad from dimension 5, the direct test of the fix for
the sixth failure mode.

## 16. Observability signals

**Iterations per request.** A histogram of how many retrieve-grade-rewrite
rounds each request actually took before terminating, whether by an
acceptable grade or by hitting the cap. A distribution heavily skewed toward
the maximum allowed value is the first sign the corpus, the grader's
threshold, or both need attention, since it means most requests are
exhausting the loop's full budget rather than resolving early.

**Grader score distribution.** Track the confidence or relevance score the
grader assigns on every pass, not only the pass or fail outcome. A
distribution clustered near the pass or fail threshold, rather than cleanly
bimodal, is a direct sign the threshold itself is poorly calibrated for the
actual traffic, one of the causes named in the third failure mode in
dimension 11.

**Fallback and escalation rate.** How often requests fall all the way
through to the terminal branch, whichever variant that is in the specific
system, a web search escalation, an insufficient-information response, or
both. Azure's own architecture explicitly logs this kind of routing decision
in its optional activity log, and a rising escalation rate over time, for
otherwise similar query traffic, is a leading indicator that the primary
corpus has drifted out of date or coverage relative to what users are now
asking.

**Cost per request, broken down by stage.** Since planning, retrieval
reranking, and generation are billed separately under a token-metered
model, per Azure's documented pricing structure, tracking cost per stage
rather than only total cost per request makes it possible to see which
stage is actually driving a cost increase. A spike in planning-token cost
from harder decomposition and a spike in reranking-token cost from more
documents being retrieved per subquery are two different problems with two
different fixes.

**Latency broken down by stage.** The same stage-level breakdown applied to
time rather than tokens, since Microsoft's own documentation is explicit
that agentic retrieval's added latency, relative to a single-query pipeline,
comes specifically from the planning and multi-subquery reranking stages,
and a team optimizing the wrong stage will not move the number that actually
matters to users.

**Citation or source coverage.** The proportion of claims in a generated
answer that trace back to a specific retrieved reference, versus claims the
model appears to have generated without a grounding source. A dropping trend
in this metric over time, holding query difficulty roughly constant, is the
clearest available leading indicator that the loop is drifting back toward
the exact ungrounded-answer symptom named as the core problem in dimension
2, even while the pipeline's other metrics look healthy.

## 17. Security and privacy implications

**Indirect prompt injection through retrieved content.** Because the
orchestrator reads whatever a retriever returns as part of its own reasoning
context, and because an agentic loop, unlike naive RAG, can go on to take
further actions, another retrieval call, a query rewrite, or possibly
another tool entirely, based on content it has read a moment earlier, a malicious instruction
embedded inside a retrieved document has a materially larger attack surface
to exploit than it would in a single-pass pipeline that only ever generates
one answer from the retrieved text. Kai Greshake, Sahar Abdelnabi, Shailesh
Mishra, Christoph Endres, Thorsten Holz, and Mario Fritz demonstrate exactly
this attack class against real LLM-integrated applications, describing
adversaries able to "remotely, without a direct interface, exploit
LLM-integrated applications by strategically injecting prompts into data
likely to be retrieved" (Greshake et al., "Not what you've signed up for.
Compromising Real-World LLM-Integrated Applications with Indirect Prompt
Injection," arXiv 2302.12173, 2023, verified 2026-08-02), and report the
attack succeeding against real systems including a Bing-integrated GPT-4
chat product. Any corpus that includes untrusted or externally editable
content, a shared document store, ticket text a customer wrote, a web page a
fallback search retrieved, is a genuine injection surface for an agentic
loop specifically, not only for naive RAG.

**Permission-aware retrieval.** A multi-source agentic loop that routes a
subquery to whichever retriever seems relevant needs to confirm the
requesting user actually has access to that source before the subquery is
issued, not only before the final answer is shown, since an intermediate
retrieval call can itself leak the existence or content of a restricted
document into the loop's scratchpad even if the final synthesized answer is
later filtered. Microsoft names this concern directly in describing Foundry
IQ's knowledge bases as permission-aware knowledge bases, which is the
explicit design response to exactly this risk in a managed multi-source
retrieval product.

**Data residency and third-party exposure through the fallback branch.** The
web-search escalation branch named in dimension 8, used by both CRAG and the
NVIDIA NeMo Retriever blueprint when local retrieval is judged insufficient,
sends the query, and by construction some amount of the internal context
that produced it, to a third-party search service outside the
organization's own infrastructure. A query that itself contains sensitive
internal information, a customer's account details, an internal project
codename, an unreleased product's name, can leak through that fallback path
even when the organization's primary corpus and vector index are fully under
its own control, a risk that does not exist in a naive pipeline with no
external escalation branch at all.

**Excessive agency.** The retriever is, structurally, only one tool among
however many the orchestrator has access to, and a system that starts as a
narrowly scoped Agentic RAG assistant and later gains additional tools,
sending email, writing to a database, calling an external API, inherits the
full general risk surface of any tool-calling agent once those tools are
added, not only the retrieval-specific risks named above. Keeping the set of
tools available to a retrieval-focused agent narrow, and auditing any
addition to that set with the same scrutiny given to the retrieval tool
itself, keeps the security surface proportional to what the system is
actually meant to do.

## Code examples

Three languages, each a bounded, single-agent corrective loop, retrieve,
grade, rewrite on a low score, escalate to a web-search fallback if a
rewrite would repeat a query already tried, and always terminate within a
fixed maximum number of iterations. Java and Rust are omitted here in favor
of showing the identical control-flow shape across a dynamically typed
language, a statically typed transpiled language, and a compiled language
with static typing and no garbage collector, which together cover the three
shapes this loop is most often deployed in. All three were compiled or run
against the toolchain versions listed in the references.

### Python

```python
"""Minimal agentic RAG loop: retrieve, grade, rewrite, bounded retry, generate."""
from dataclasses import dataclass
from typing import Callable

MAX_ITERATIONS = 3
RELEVANCE_THRESHOLD = 0.6


@dataclass
class Document:
    text: str
    score: float


def vector_retrieve(query: str, corpus: list[Document]) -> list[Document]:
    return sorted(
        (d for d in corpus if any(w in d.text.lower() for w in query.lower().split())),
        key=lambda d: d.score,
        reverse=True,
    )[:3]


def web_search_fallback(query: str) -> list[Document]:
    return [Document(text=f"web result for: {query}", score=0.9)]


def grade(docs: list[Document]) -> float:
    if not docs:
        return 0.0
    return sum(d.score for d in docs) / len(docs)


def rewrite_query(query: str, attempt: int) -> str:
    return f"{query} (context clarified, attempt {attempt})"


def synthesize(query: str, docs: list[Document]) -> str:
    sources = "; ".join(d.text for d in docs)
    return f"answer to '{query}' grounded in: {sources}"


def agentic_rag(
    query: str,
    corpus: list[Document],
    retrieve: Callable[[str, list[Document]], list[Document]] = vector_retrieve,
) -> tuple[str, int]:
    current_query = query
    tried_queries: set[str] = set()
    for attempt in range(1, MAX_ITERATIONS + 1):
        tried_queries.add(current_query)
        docs = retrieve(current_query, corpus)
        confidence = grade(docs)
        if confidence >= RELEVANCE_THRESHOLD:
            return synthesize(current_query, docs), attempt
        next_query = rewrite_query(query, attempt)
        if next_query in tried_queries:
            return synthesize(query, web_search_fallback(query)), attempt
        current_query = next_query
    return synthesize(query, web_search_fallback(query)), MAX_ITERATIONS


if __name__ == "__main__":
    corpus = [
        Document(text="refund policy allows returns within 30 days", score=0.9),
        Document(text="shipping takes 3 to 5 business days", score=0.7),
    ]
    answer, iterations = agentic_rag("refund policy", corpus)
    print(f"iterations={iterations}")
    print(answer)

    answer2, iterations2 = agentic_rag("warranty claim process", corpus)
    print(f"iterations={iterations2}")
    print(answer2)
```

Run with `python3 agentic_rag.py`. First call resolves on the first pass,
`iterations=1`, since "refund policy" matches the corpus directly. Second
call exhausts the loop, `iterations=3`, since no document mentions
warranties, and returns the web-search fallback answer.

### TypeScript

```typescript
interface Doc {
  text: string;
  score: number;
}

const MAX_ITERATIONS = 3;
const RELEVANCE_THRESHOLD = 0.6;

function vectorRetrieve(query: string, corpus: Doc[]): Doc[] {
  const words = query.toLowerCase().split(" ");
  return corpus
    .filter((d) => words.some((w) => d.text.toLowerCase().includes(w)))
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);
}

function webSearchFallback(query: string): Doc[] {
  return [{ text: `web result for: ${query}`, score: 0.9 }];
}

function grade(docs: Doc[]): number {
  if (docs.length === 0) return 0;
  return docs.reduce((sum, d) => sum + d.score, 0) / docs.length;
}

function rewriteQuery(query: string, attempt: number): string {
  return `${query} (context clarified, attempt ${attempt})`;
}

function synthesize(query: string, docs: Doc[]): string {
  const sources = docs.map((d) => d.text).join("; ");
  return `answer to '${query}' grounded in: ${sources}`;
}

function agenticRag(query: string, corpus: Doc[]): [string, number] {
  let currentQuery = query;
  const tried = new Set<string>();
  for (let attempt = 1; attempt <= MAX_ITERATIONS; attempt++) {
    tried.add(currentQuery);
    const docs = vectorRetrieve(currentQuery, corpus);
    const confidence = grade(docs);
    if (confidence >= RELEVANCE_THRESHOLD) {
      return [synthesize(currentQuery, docs), attempt];
    }
    const nextQuery = rewriteQuery(query, attempt);
    if (tried.has(nextQuery)) {
      return [synthesize(query, webSearchFallback(query)), attempt];
    }
    currentQuery = nextQuery;
  }
  return [synthesize(query, webSearchFallback(query)), MAX_ITERATIONS];
}

const corpus: Doc[] = [
  { text: "refund policy allows returns within 30 days", score: 0.9 },
  { text: "shipping takes 3 to 5 business days", score: 0.7 },
];

const [answer, iterations] = agenticRag("refund policy", corpus);
console.log(`iterations=${iterations}`);
console.log(answer);

const [answer2, iterations2] = agenticRag("warranty claim process", corpus);
console.log(`iterations=${iterations2}`);
console.log(answer2);
```

Compiled with `tsc --target es2020 --module commonjs --strict` under
TypeScript 5, then run with `node`, producing the same two results as the
Python version.

### Go

```go
package main

import (
	"fmt"
	"sort"
	"strings"
)

const maxIterations = 3
const relevanceThreshold = 0.6

type Doc struct {
	Text  string
	Score float64
}

func vectorRetrieve(query string, corpus []Doc) []Doc {
	words := strings.Fields(strings.ToLower(query))
	var matched []Doc
	for _, d := range corpus {
		lower := strings.ToLower(d.Text)
		for _, w := range words {
			if strings.Contains(lower, w) {
				matched = append(matched, d)
				break
			}
		}
	}
	sort.Slice(matched, func(i, j int) bool { return matched[i].Score > matched[j].Score })
	if len(matched) > 3 {
		matched = matched[:3]
	}
	return matched
}

func webSearchFallback(query string) []Doc {
	return []Doc{{Text: "web result for: " + query, Score: 0.9}}
}

func grade(docs []Doc) float64 {
	if len(docs) == 0 {
		return 0
	}
	total := 0.0
	for _, d := range docs {
		total += d.Score
	}
	return total / float64(len(docs))
}

func rewriteQuery(query string, attempt int) string {
	return fmt.Sprintf("%s (context clarified, attempt %d)", query, attempt)
}

func synthesize(query string, docs []Doc) string {
	parts := make([]string, len(docs))
	for i, d := range docs {
		parts[i] = d.Text
	}
	return fmt.Sprintf("answer to '%s' grounded in: %s", query, strings.Join(parts, "; "))
}

func agenticRAG(query string, corpus []Doc) (string, int) {
	currentQuery := query
	tried := map[string]bool{}
	for attempt := 1; attempt <= maxIterations; attempt++ {
		tried[currentQuery] = true
		docs := vectorRetrieve(currentQuery, corpus)
		confidence := grade(docs)
		if confidence >= relevanceThreshold {
			return synthesize(currentQuery, docs), attempt
		}
		nextQuery := rewriteQuery(query, attempt)
		if tried[nextQuery] {
			return synthesize(query, webSearchFallback(query)), attempt
		}
		currentQuery = nextQuery
	}
	return synthesize(query, webSearchFallback(query)), maxIterations
}

func main() {
	corpus := []Doc{
		{Text: "refund policy allows returns within 30 days", Score: 0.9},
		{Text: "shipping takes 3 to 5 business days", Score: 0.7},
	}
	answer, iterations := agenticRAG("refund policy", corpus)
	fmt.Printf("iterations=%d\n%s\n", iterations, answer)

	answer2, iterations2 := agenticRAG("warranty claim process", corpus)
	fmt.Printf("iterations=%d\n%s\n", iterations2, answer2)
}
```

Run with `go run agentic_rag.go`, producing the identical two results and
iteration counts as the Python and TypeScript versions. Java was not
compiled for this entry because no JDK was present on the authoring machine
at write time, so this entry omits it rather than presenting an unverified
sample.

## 18. References

1. Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir
   Karpukhin, Naman Goyal, Heinrich Kuttler, Mike Lewis, Wen-tau Yih, Tim
   Rocktaschel, Sebastian Riedel, Douwe Kiela. "Retrieval-Augmented
   Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020, arXiv 2005.11401.
   https://arxiv.org/abs/2005.11401
   Verified 2026-08-02. Source of the base RAG architecture Agentic RAG
   extends, dimension 1.
2. Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik
   Narasimhan, Yuan Cao. "ReAct. Synergizing Reasoning and Acting in
   Language Models." 2022, arXiv 2210.03629.
   https://arxiv.org/abs/2210.03629
   Verified 2026-08-02. Source of the interleaved reasoning-and-acting loop,
   dimensions 1, 8, and 13.
3. Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, Hannaneh Hajishirzi.
   "Self-RAG. Learning to Retrieve, Generate, and Critique through
   Self-Reflection." 2023, arXiv 2310.11511.
   https://arxiv.org/abs/2310.11511
   Verified 2026-08-02. Source of the reflection-token, trained-in retrieval
   decision variant, dimensions 1, 8, 10, and 11.
4. Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, Zhen-Hua Ling. "Corrective Retrieval
   Augmented Generation." 2024, arXiv 2401.15884.
   https://arxiv.org/abs/2401.15884
   Verified 2026-08-02. Source of the CRAG retrieval evaluator and web-search
   fallback mechanism, dimensions 5, 7, 8, and 9.
5. Aditi Singh, Abul Ehtesham, Saket Kumar, Tala Talaei Khoei, Athanasios V.
   Vasilakos. "Agentic Retrieval-Augmented Generation. A Survey on Agentic
   RAG." 2025, arXiv 2501.09136.
   https://arxiv.org/abs/2501.09136
   Verified 2026-08-02. Source of the term's formal taxonomy and the
   multi-agent and graph-based variants, dimensions 1 and 8.
6. Kai Greshake, Sahar Abdelnabi, Shailesh Mishra, Christoph Endres, Thorsten
   Holz, Mario Fritz. "Not what you've signed up for. Compromising
   Real-World LLM-Integrated Applications with Indirect Prompt Injection."
   2023, arXiv 2302.12173.
   https://arxiv.org/abs/2302.12173
   Verified 2026-08-02. Source of the indirect prompt injection attack
   class, dimension 17.
7. Anthropic. "Building Effective Agents."
   https://www.anthropic.com/engineering/building-effective-agents
   Verified 2026-08-02. Source of the workflow versus agent distinction used
   in dimension 1 and the problem framing in dimension 2.
8. Anthropic. "Introducing Contextual Retrieval."
   https://www.anthropic.com/news/contextual-retrieval
   Verified 2026-08-02. Background source on retrieval-quality techniques
   that compose with, but are distinct from, the agentic decision loop, used
   only for context in dimension 2, not for any specific claim about
   Agentic RAG.
9. Weaviate. "What is Agentic RAG."
   https://weaviate.io/blog/what-is-agentic-rag
   Verified 2026-08-02. Source of the plain definition contrasting vanilla
   and agentic RAG, dimension 1.
10. LangChain. "Agentic RAG With LangGraph."
    https://www.langchain.com/blog/agentic-rag-with-langgraph
    Verified 2026-08-02. Source of the flow-engineering framing and the
    CRAG and Self-RAG graph implementations, dimensions 7, 8, and 9.
11. LangChain. "RAG."
    https://docs.langchain.com/oss/python/langchain/rag
    Verified 2026-08-02. Source of the Deep Agents retrieval-tool primitives
    and grading rubrics, dimensions 9 and 15.
12. LlamaIndex. "Agents."
    https://developers.llamaindex.ai/python/framework/use_cases/agents/
    Verified 2026-08-02. Source of the LlamaIndex agentic RAG production use,
    dimension 9.
13. Microsoft. "Agentic Retrieval Overview." Azure AI Search documentation,
    Microsoft Learn.
    https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview
    Verified 2026-08-02. Source of the Azure AI Search production use,
    architecture, and billing figures cited throughout dimensions 3, 4, 7, 9,
    10, 11, 16, and 17.
14. NVIDIA. "Build an Agentic RAG Pipeline with Llama 3.1 and NVIDIA NeMo
    Retriever NIMs." NVIDIA Developer Blog.
    https://developer.nvidia.com/blog/build-an-agentic-rag-pipeline-with-llama-3-1-and-nvidia-nemo-retriever-nims/
    Verified 2026-08-02. Source of the NeMo Retriever production reference
    architecture and router-node fallback behavior, dimensions 7, 8, and 9.
