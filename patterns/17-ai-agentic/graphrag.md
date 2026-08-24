---
name: GraphRAG
slug: graphrag
family: 17-ai-agentic
category: AI Agentic
aliases: [Graph RAG, Graph-based Retrieval Augmented Generation, Knowledge Graph RAG]
first_described: "Edge, Trinh, Cheng, Bradley, Chao, Mody, Truitt, Metropolitansky, Ness, Larson 2024"
maturity: emerging
related: [retrieval-augmented-generation, orchestrator-worker, map-reduce, cache-aside, strategy]
incompatible_with: []
verified: 2026-08-02
---

# GraphRAG

## 1. Name, aliases, and lineage

The canonical name is GraphRAG. It was introduced by a Microsoft Research team,
Darren Edge, Ha Trinh, Newman Cheng, Joshua Bradley, Alex Chao, Apurva Mody,
Steven Truitt, Dasha Metropolitansky, Robert Osazuwa Ness, and Jonathan
Larson, in the paper "From Local to Global. A Graph RAG Approach to
Query-Focused Summarization", published as arXiv preprint 2404.16130 in April
2024 ([arxiv.org/abs/2404.16130](https://arxiv.org/abs/2404.16130), verified
2026-08-02). The paper's own abstract, as summarized on the arXiv listing
page, frames the method as building a knowledge graph from a text corpus with
an LLM, clustering closely related entities into communities, and
pregenerating a summary for each community before any question is asked, so
that broad questions about the whole corpus can be answered by combining
community summaries instead of retrieving individual passages.

Microsoft released an open source reference implementation of the method at
github.com/microsoft/graphrag under the MIT license
([github.com/microsoft/graphrag](https://github.com/microsoft/graphrag),
verified 2026-08-02, 35.2k stars at verification time). The term GraphRAG has
since been used more loosely in the wider RAG community for any retrieval
system that stores a knowledge graph and queries it as part of answering a
question, not only the specific community-summarization method the original
paper describes. This entry treats the two together, the general shape
(retrieve from a graph rather than, or in addition to, a vector index) and the
specific method (LLM-built graph, hierarchical community clustering,
pregenerated community summaries, map-reduce query-time aggregation), and
names which claims apply to which. Because the term is applied broadly and
inconsistently across vendors as of 2026, this entry is marked `emerging`
rather than `canonical`, unlike the base Retrieval Augmented Generation
pattern it extends.

## 2. Problem and context

A team has a large private corpus, contracts, incident postmortems, research
notes, support transcripts, and wants an LLM to answer questions grounded in
that corpus. The team already has a working Retrieval Augmented Generation
pipeline (see the `retrieval-augmented-generation` entry in this family). Chunk
the documents, embed the chunks, store the embeddings in a vector index, and
at query time retrieve the k nearest chunks by cosine similarity, then stuff
them into the LLM's context window.

That pipeline answers a narrow, fact-lookup question well. "What was the
resolution for incident INC-4471." A single chunk usually contains the
answer, and it is usually one of the top few nearest neighbors of the
question's embedding.

It answers a broad, corpus-spanning question badly, sometimes by returning
nothing useful. "What are the recurring root causes across all incidents this
quarter." No single chunk contains that answer, because the answer is a
synthesis across dozens or hundreds of chunks that individually only describe
one incident each. A vector search returns some fixed number of chunks near
the query embedding, and a question phrased at the corpus level does not have
a small number of embedding neighbors that happen to contain the aggregate
answer, because the aggregate answer does not exist as a contiguous span of
text anywhere in the corpus. This is the exact gap the original paper
targets, describing it as a query-focused summarization task that plain RAG
was not designed to solve, per the paper's abstract as summarized above.

The context that creates this problem is specific. The corpus is large enough
that no single LLM call can read all of it, private enough that a general
purpose model has no prior knowledge of the entities involved, and the
questions the team actually asks are a mix of narrow lookups and broad
sensemaking questions, so a system tuned only for one kind of question fails
the other kind.

## 3. Forces

This entry states engineering judgement in this section rather than a sourced
claim, drawn from the shape of the mechanism the source paper describes.

Latency and cost at index time versus latency and cost at query time pull in
opposite directions. Building the graph and the community summaries requires
one LLM call per text chunk for entity and relationship extraction, and one
LLM call per community for summarization. For a corpus of ten thousand chunks
that clusters into a few hundred communities, indexing is on the order of
eleven thousand LLM calls before a single question is answered. Plain vector
RAG has no equivalent indexing cost beyond embedding, which is far cheaper
per chunk than an extraction call. In exchange, GraphRAG's query-time cost for
a broad question is bounded and predictable, a fixed number of community
summaries read in a map-reduce pass, where plain vector RAG has no reliable
query-time path to a broad answer at any cost.

Answer breadth versus answer precision is the second force. Community
summaries are, by construction, lossy compressions of the source chunks, so a
narrow factual question answered from a community summary risks a less
precise answer than the same question answered from the original chunk text.
GraphRAG's local search mode exists specifically to route narrow questions
back to entity-level detail rather than through the lossy community summary,
trading the system's simplicity (one retrieval path) for accuracy on the
narrow case.

Extraction quality versus corpus noise is the third force. The entity and
relationship graph is only as good as the LLM's extraction on each chunk. A
corpus with inconsistent naming, for example the same person referred to as
"Bob Smith", "B. Smith", and "the VP of engineering" across different
documents, produces a graph with duplicate entity nodes that should have been
merged, which fragments communities and degrades both local and global
search. Vector RAG has no equivalent failure mode, because it never asks
whether two chunks refer to the "same" entity.

Coupling to a specific graph store versus portability is the fourth force.
A production GraphRAG deployment commits to a graph storage layer, whether
that is an in-memory NetworkX graph for a small corpus, or Neo4j, Amazon
Neptune, or a purpose-built store for a large one. That storage choice is a
new operational dependency a plain vector-index RAG system does not carry.

## 4. Applicability and non-applicability

Reach for GraphRAG when the corpus is large enough that no single retrieval
call can surface an aggregate answer, when a meaningful fraction of real user
questions are broad sensemaking questions rather than narrow lookups ("what
are the themes", "how does X relate to Y across the whole dataset"), when the
corpus describes a dense web of named entities and their relationships
(people, organizations, incidents, products) rather than largely independent
documents, and when the cost and latency of a one-time (or periodically
refreshed) indexing pass is acceptable given how often the corpus changes.

Do not reach for GraphRAG in the following cases, and prefer plain
Retrieval Augmented Generation instead.

The corpus is small enough, on the order of a few hundred chunks or fewer,
that stuffing a meaningful fraction of it directly into the LLM's context
window is itself an option, per the general RAG applicability trade-off
described in this repository's `retrieval-augmented-generation` entry. The
extraction and community-summarization overhead buys nothing a bigger context
window would not buy more simply.

The workload consists mostly of narrow, single-fact lookups with no
aggregate or relational questions in practice. If nobody ever asks "what are
the common threads across these documents," the machinery that exists
specifically to answer that question is pure cost with no corresponding
benefit.

The corpus updates continuously and cheaply re-running the full extraction
and community-detection pipeline is not viable. The original pipeline as
released is a batch indexing process, not an incremental one. A corpus that
changes every few minutes needs either a system built for incremental graph
updates or accepts a stale graph, and that staleness must be an explicit,
accepted trade rather than a surprise.

The domain has few named entities and little relational structure, for
example a corpus of independent product FAQ answers where each answer stands
alone. There is no graph worth building because there is little relationship
between the pieces of the corpus.

The team has no budget, financial or engineering, for the extra operational
surface of a graph store, a community-detection step, and a second class of
LLM call (summarization) beyond the generation call every RAG system already
makes. This is a genuine cost that a small team should weigh honestly against
the value of better answers to broad questions.

## 5. Structure

The structure below follows the shape the original paper and its reference
implementation describe, per the sources cited in section 1 and section 6.

**Source Documents.** The raw private corpus, unstructured text.

**Text Units.** Fixed-size, possibly overlapping chunks the source documents
are split into. This is the same chunking step plain RAG performs, and it
plays the same role, a unit small enough for a single LLM call to process.

**Entity Extractor.** An LLM prompted, per text unit, to identify named
entities (people, organizations, locations, and any domain-specific entity
type the deployment configures) and the relationships between entities
mentioned in that unit, along with a short description of each. The
documentation for the reference implementation describes this step
supporting multiple extraction passes, or "gleanings", over the same chunk to
catch entities the first pass missed, per the indexing dataflow page
referenced in section 6.

**Knowledge Graph.** The accumulated output of the entity extractor across
every text unit, entities as nodes, extracted relationships as edges, with
edge weight typically derived from how often two entities co-occur or are
described as related across the corpus.

**Community Detector.** A graph clustering algorithm run over the knowledge
graph to partition it into communities, hierarchically, so that a coarse
level of the hierarchy has few, large communities and a fine level has many,
small ones. The reference implementation's documentation states this step
uses the Leiden algorithm
([microsoft.github.io/graphrag](https://microsoft.github.io/graphrag/),
verified 2026-08-02, "Hierarchical Clustering. Uses the Leiden technique to
organize the graph into communities"). The Leiden algorithm itself was
described by Vincent Traag, Ludo Waltman, and Nees Jan van Eck in "From
Louvain to Leiden. Guaranteeing well-connected communities", Scientific
Reports volume 9, article 5233, 2019, as an improvement on the earlier
Louvain method that guarantees every detected community is internally
connected, a property Louvain does not guarantee.

**Community Reports.** A second LLM pass, one call per community, that reads
the entities, relationships, and their descriptions within that community and
writes a natural-language summary of what the community is about. This is
the pregenerated, query-independent summarization step that makes broad
questions answerable without a fresh full-corpus pass at query time.

**Query Orchestrator.** The component that, given a user question, chooses a
search mode (see section 7 for the modes) and, for global search, runs the
map-reduce process over community reports. For local search, it walks
outward from a small number of seed entities matched to the question.

## 6. ASCII structure diagram

```
+------------------+
| Source Documents |
+------------------+
           v
+------------+
| Text Units |
+------------+
           v
+------------------+
| Entity Extractor |
| (LLM, per unit)  |
+------------------+
           v
+----------------------+
| Knowledge Graph      |
| entities + relations |
+----------------------+
           v
+---------------------+
| Community Detector  |
| (Leiden clustering) |
+---------------------+
           v
+----------------------+
| Community Reports    |
| (LLM, per community) |
+----------------------+
           |
     +-----+-----+
     |           |
+----------------------+ +----------------------+
| Global Search        | | Local Search         |
| map communities      | | walk from seed       |
| reduce to answer     | | entity neighbors     |
+----------------------+ +----------------------+
```

## 7. Dynamics

There are two distinct runtime paths, corresponding to the two search modes
the reference implementation documentation names as its primary modes (a
third and fourth mode, DRIFT search and basic search, are described in
section 8).

Global search, used for broad questions, runs a map-reduce pass over
community reports at a chosen level of the community hierarchy. The reference
documentation describes the map stage as splitting each community report
into text chunks and generating an intermediate response per chunk with
points rated by how well they answer the question, and the reduce stage as
filtering the highest-rated points across every intermediate response and
using that filtered set as the context for one final LLM call that produces
the answer
([microsoft.github.io/graphrag query/global_search](https://microsoft.github.io/graphrag/),
verified 2026-08-02, "each text chunk is then used to produce an intermediate
response" and "a filtered set of the most important points from the
intermediate responses are aggregated and used as the context to generate
the final response"). The same page states that choosing a lower, more
granular level of the community hierarchy for this pass increases answer
detail but also increases the time and LLM cost of the pass, because there
are more, smaller community reports to map over, an explicit operator-facing
trade-off exposed as a configurable hierarchy level and a `max_data_tokens`
budget parameter.

```
Global search, per question.
  1. select community-hierarchy level L
  2. for each community report at level L (MAP, parallel).
       split report into chunks
       LLM. rate each chunk's relevance, extract points
     -> list of (point, rating) per report
  3. REDUCE.
       pool all points across all reports
       keep the highest-rated points up to token budget
  4. LLM. one final call over the pooled points -> answer
```

Local search, used for narrow, entity-centered questions, resolves the
entities named or implied in the question against the knowledge graph, then
gathers the immediate neighborhood of those entities (directly related
entities, the text units that mention them, and any community report that
covers them) as context for a single generation call, closer in shape to
plain RAG's retrieve-then-generate flow but retrieving graph neighborhood
instead of, or in addition to, nearest-neighbor chunks.

```
Local search, per question.
  1. resolve question -> seed entity or entities in the graph
  2. gather. seed entity's direct relationships,
             text units that mention the seed entity,
             community report(s) covering the seed entity
  3. LLM. one call over the gathered context -> answer
```

## 8. Implementation variants

**Reference implementation (Microsoft GraphRAG).** The open source pipeline
released alongside the paper, described in section 1 and section 5, runs the
full extract, cluster, summarize pipeline and exposes global search, local
search, and, per its documentation, two further modes. DRIFT search, which
the documentation describes as extending local search with additional
community context to answer questions that sit between narrowly local and
fully global, and basic search, described as a fallback to plain vector
similarity search when the graph-based modes are not warranted for a given
query
([microsoft.github.io/graphrag](https://microsoft.github.io/graphrag/),
verified 2026-08-02).

**Framework integrations that reuse an existing graph store.** Rather than
Microsoft's own pipeline and file-based indexes, some integrations wire the
same extract-cluster-summarize shape onto an existing graph database. The
LlamaIndex GraphRAG cookbook, for example, extracts entity-relationship
triplets with an LLM, stores them in a Neo4j graph, runs a community
detection algorithm over that graph, generates a summary per community, and
at query time retrieves the communities relevant to the question and
aggregates their summaries into the final answer, per the cookbook's own
description, fetched 2026-08-02
([developers.llamaindex.ai python/examples/cookbooks/graphrag_v2](https://web.archive.org/web/20260511030531/https://developers.llamaindex.ai/python/examples/cookbooks/graphrag_v2/)).
This variant trades the reference implementation's file-based storage for a
persistent graph database that other systems (a graph explorer UI, a
separate analytics pipeline) can also query directly.

**Connected-components clustering as a cheaper stand-in for Leiden.** For a
small corpus, or for a first implementation before adopting a full graph
library, some teams substitute a simpler clustering step, connected
components via union-find, for the Leiden algorithm the reference
implementation uses. This is a genuine simplification, not merely an
implementation detail. Connected components produces one giant community
whenever the graph is a single connected blob, which is common on a small,
richly interlinked corpus, whereas Leiden's modularity-based optimization
finds internally dense subgroups even within a single connected component.
This variant is appropriate only for small corpora or as a scaffold to
validate the rest of the pipeline before adopting real community detection.
This is the variant demonstrated in section 20's code samples, chosen so the
samples run with no external graph library dependency, and it is explicitly
flagged in the code as a simplification, not a substitute claimed to be
equivalent to Leiden.

**Incremental and streaming graph maintenance.** A variant, not part of the
original paper, where new documents update the existing graph and only the
affected communities are re-summarized rather than re-running the full
pipeline. This addresses the non-applicability case in section 4 about
continuously updating corpora, at the cost of additional bookkeeping to track
which communities a given update actually touches.

## 9. Known production uses

**Microsoft GraphRAG (github.com/microsoft/graphrag).** Microsoft's own
open source, MIT-licensed reference implementation, maintained by the same
team that published the paper, is itself a production system in the sense
that it is the deployed artifact organizations install and run against their
own corpora rather than a research prototype that was never released. The
repository was at 35.2k GitHub stars at the time of verification
([github.com/microsoft/graphrag](https://github.com/microsoft/graphrag),
verified 2026-08-02).

**The original research team's own evaluation.** The paper that introduced
GraphRAG evaluated it against a conventional RAG baseline on global,
corpus-wide sensemaking questions over datasets of roughly one million
tokens, and reported substantial improvements in both the comprehensiveness
and the diversity of generated answers compared to that baseline, per the
paper's abstract as summarized on the arXiv listing page
([arxiv.org/abs/2404.16130](https://arxiv.org/abs/2404.16130), verified
2026-08-02, cited fully in section 1). This is the specific evidence the
pattern's community-summarization method outperforms plain retrieval on the
exact class of question, broad and corpus-spanning, described in section 2.

**LlamaIndex's GraphRAG cookbook integration.** LlamaIndex, a widely used
open source LLM application framework, ships a documented GraphRAG
implementation that follows the same extract-cluster-summarize-query shape
as the original method but built on Neo4j as the graph store rather than
Microsoft's reference pipeline, per the cookbook's own description fetched
2026-08-02
([developers.llamaindex.ai python/examples/cookbooks/graphrag_v2](https://web.archive.org/web/20260511030531/https://developers.llamaindex.ai/python/examples/cookbooks/graphrag_v2/)).
This is evidence the pattern generalizes beyond the original authors'
tooling into at least one other widely adopted RAG framework.

## 10. Consequences

Positive. Broad, corpus-spanning questions become answerable at all, where
plain vector RAG has no reliable path to an answer for them, because the
map-reduce pass over pregenerated community summaries synthesizes across the
whole indexed corpus rather than a fixed small number of nearest-neighbor
chunks. Answers can carry source provenance back through the graph, entity to
relationship to originating text unit, which supports the kind of "show your
work" citation a plain vector RAG answer built from a single retrieved chunk
also supports, but GraphRAG additionally supports it for a synthesized,
multi-source answer. Query-time cost for a broad question becomes bounded
and predictable, a fixed map-reduce pass over a fixed number of community
reports, rather than unbounded (there is no bound on how many chunks would
actually need to be read to answer a truly corpus-wide question with plain
RAG).

Negative. Indexing cost is substantial and front-loaded, one LLM call per
text unit for extraction and one per community for summarization, which for
a large corpus is thousands of additional LLM calls compared to a plain
embedding-only indexing pass, as described under forces in section 3. The
system commits to an additional class of infrastructure, a graph store, that
a plain vector-RAG deployment does not need. Freshness is a real operational
concern, because the reference pipeline is a batch process and a corpus that
changes frequently either accepts a stale graph or needs the incremental
variant described in section 8, which the original release does not provide
out of the box. Narrow, single-fact questions can, in the worst case, be
answered slightly worse than plain RAG if the system routes them through a
lossy community summary instead of the original chunk, which is exactly why
local search exists as a separate mode rather than always using global
search, per section 7.

## 11. Failure modes and misuse

**Entity fragmentation from inconsistent naming.** Symptom. The community
detector produces many small, disconnected communities for what should
logically be one topic, and global search answers about that topic come back
thin or missing obvious connections. Cause. The extraction LLM emitted
distinct entity nodes for what is really one entity, referred to differently
across chunks, for example "Bob Smith" in one document and "B. Smith" in
another, and nothing merged them. Fix. Add an entity resolution or canonical-
name normalization pass after extraction and before graph construction, or
prompt the extractor with a list of known canonical entity names for the
domain to bias it toward consistent naming.

**Answering a narrow question through global search.** Symptom. A
straightforward factual question gets a vague or subtly wrong answer, when
the same question against a plain RAG chunk retrieval would have answered it
precisely. Cause. The query orchestrator, or a developer who wired only one
search mode into the application, routed the question through the lossy,
pregenerated community summary path instead of local search or direct chunk
lookup. Fix. Implement query routing that distinguishes narrow, entity-
specific questions from broad, corpus-wide questions before choosing global
versus local search, rather than defaulting every question to one mode.

**Stale graph after the corpus changes.** Symptom. Newly added documents are
never reflected in answers, even though a plain vector index over the same
corpus would surface them immediately after re-embedding. Cause. The graph,
communities, and community reports were built once and the pipeline was
never rerun, because rerunning the full extraction and summarization pass is
expensive, as described in section 3 and section 10. Fix. Schedule periodic
full reindexing at a cadence the corpus's real rate of change and the
team's budget can bear, or adopt an incremental update variant, per section
8, that only reprocesses the parts of the graph a given update actually
touches.

**Indexing cost surprise at scale.** Symptom. A proof of concept on a small
sample corpus works well and is inexpensive, and the same pipeline run
against the full production corpus produces an LLM bill an order of
magnitude larger than anticipated. Cause. Indexing cost scales with the
number of text units (extraction calls) and the number of communities
(summarization calls), and both of those can grow faster than the raw
document count as the corpus grows, since a denser corpus produces a denser
graph and more, or larger, communities. Fix. Measure indexing cost on a
representative sample at the target chunk size before committing to indexing
the full corpus, and treat the corpus's rate of ongoing growth as a
recurring operating cost, not a one-time cost.

**Treating GraphRAG as a strict upgrade over plain RAG.** Symptom. A team
migrates an entire RAG system to GraphRAG and query latency, infrastructure
cost, and operational surface all increase, without a corresponding increase
in answer quality that users actually notice. Cause. The workload already
consisted mostly of narrow lookup questions, the exact non-applicability
case in section 4, so the machinery that exists to answer broad questions
paid for itself in engineering effort and cost with no matching payoff in
practice. Fix. Instrument the existing RAG system's real query traffic
before migrating, classify what fraction of real questions are broad versus
narrow, and only adopt GraphRAG when that fraction justifies the added cost.

## 12. Trade-off matrix

| Force | GraphRAG | Retrieval Augmented Generation (plain vector RAG) | Orchestrator-Worker over sub-summaries |
|---|---|---|---|
| Answers broad, corpus-wide questions | Strong, purpose built for this via pregenerated community summaries | Weak, no reliable path to a synthesized answer | Possible, but no reusable community structure, resummarizes from scratch per query |
| Answers narrow, single-fact questions | Good via local search, slightly indirect versus a direct chunk hit | Strong, this is the case plain RAG is built for | Weak, ad hoc orchestration is not tuned for single-fact lookup |
| Indexing cost | High, one extraction call per chunk plus one summarization call per community | Low, embedding only | Low at index time, cost deferred to query time |
| Query-time cost for a broad question | Bounded, fixed map-reduce pass over communities | Effectively unbounded, no reliable bound on chunks needed | High, an orchestrator dispatches many worker calls fresh per query |
| Extra infrastructure | Graph store plus community-report store | Vector index only | Whatever the orchestrator's own worker fleet needs, no persistent index required |
| Freshness on a changing corpus | Poor without incremental updates, batch reindex needed | Good, re-embed new chunks incrementally | Good, no persistent structure to go stale |

## 13. Related and incompatible patterns

GraphRAG is an elaboration of Retrieval Augmented Generation (see the
`retrieval-augmented-generation` entry in this family), not a replacement for
it. Every GraphRAG deployment still performs the retrieve-then-generate loop
plain RAG describes. GraphRAG changes what gets retrieved (graph
neighborhoods and pregenerated community summaries) and adds an indexing
stage plain RAG does not have (entity extraction, community detection,
community summarization). A production system commonly runs both, plain
vector retrieval for narrow lookups (GraphRAG's own basic search mode is
exactly this) and GraphRAG's graph-based modes for broad questions, choosing
between them with a router.

GraphRAG's global search stage composes with the Map-Reduce pattern, applying
the map stage per community report and the reduce stage to aggregate the
highest-rated points into a final answer, per section 7. It also composes
with Orchestrator-Worker (see the `orchestrator-worker` entry in this family)
in systems that treat "produce one community report" or "produce one
intermediate map-stage response" as an independently dispatched worker task
coordinated by an orchestrator, rather than a hand-rolled loop.

The Cache-Aside pattern applies naturally to community reports, since they
are expensive to produce and, until the underlying graph changes, do not
change themselves, making them a natural candidate for a cache that is
populated once at index time and invalidated only on reindexing.

The Strategy pattern is a natural fit for the query orchestrator's choice
between global search, local search, DRIFT search, and basic search, per
section 5 and section 8, each a different retrieval strategy selected at
query time based on the shape of the question.

GraphRAG is not incompatible with any pattern in this repository in the
sense of actively conflicting, but it is a poor fit layered directly on top
of a system already using Retrieval Augmented Generation's simplest form
purely for narrow lookups with no broad-question workload, per the
non-applicability list in section 4, where the added graph infrastructure
earns nothing.

## 14. Refactoring path in and out

Refactoring a plain vector-RAG system into GraphRAG. Start by instrumenting
real user query traffic against the existing system to measure what fraction
of questions are broad versus narrow, per the closing failure mode in section
11, so the decision to add GraphRAG is evidence based rather than
speculative. If that fraction justifies it, add the extraction stage first
and validate the resulting knowledge graph in isolation, spot-checking that
entities look correctly resolved and relationships look correct, before
building anything downstream of it. Add community detection next and inspect
a sample of the resulting communities for sanity, whether they group entities
a domain expert would actually consider related. Add community summarization
last, and only then wire a global search mode into the application behind a
router that keeps sending narrow questions through the existing vector
retrieval path unchanged. This staged rollout means each stage can be
validated before the next is built on top of it, and the existing narrow-
question path never regresses during the migration.

Refactoring GraphRAG back out. If the broad-question workload that justified
adopting GraphRAG turns out to be small in practice, or the indexing cost
proves unsustainable, the narrow-question path (local search, or GraphRAG's
own basic search fallback, which is already plain vector search) can be kept
as the sole retrieval path and the graph-building and community-summarization
stages can be retired without touching the generation step at all, because
those stages are purely upstream of retrieval and the generation call itself
is identical to plain RAG's. The graph store and community reports can be
decommissioned once no query mode reads from them.

## 15. Testing and verification

Test the extraction stage in isolation with a small, hand-labeled corpus
where the correct entities and relationships are known in advance, and assert
the extractor's output against that ground truth, treating extraction
accuracy (entities found, relationships found, false entities not present in
the source) as a measurable quality gate independent of the rest of the
pipeline. This is easier to test than plain RAG's retrieval step in one
respect, there is a concrete, checkable structured output (a list of entities
and relationships) rather than only a ranked list of retrieved chunks to
evaluate.

Test community detection by asserting on graph-structural properties that do
not depend on LLM output at all, for example that every entity ends up in
exactly one community at a given hierarchy level, and that a hand-constructed
graph with an obvious two-cluster structure (two dense subgraphs joined by
one weak edge) is actually partitioned into two communities by the clustering
step, which is a deterministic, non-LLM assertion and therefore cheap and
reliable to run in CI on every change to the clustering code.

Test community summarization the way any single LLM-call step is tested,
with a small set of fixed community inputs and either an LLM-as-judge
evaluation of the resulting summary's faithfulness to the input entities and
relationships, or, more cheaply, an assertion that every entity name present
in the community actually appears somewhere in its summary, which catches
the common failure of a summary that drops entities entirely.

Test the query orchestrator's mode selection with a labeled set of example
questions, each tagged as narrow or broad by a human reviewer, and assert the
router sends narrow questions to local or basic search and broad questions to
global search, since a misrouted question is a silent quality regression
rather than a crash and is exactly the failure mode named in section 11.

What became harder to test compared to plain RAG. End-to-end answer quality
now depends on the correctness of two upstream, LLM-driven stages
(extraction and summarization) rather than one (retrieval), so a wrong final
answer requires isolating which of three stages (extraction, summarization,
or generation) introduced the error, which needs the per-stage tests above
rather than only end-to-end evaluation.

## 16. Observability signals

At indexing time, log and track per-run entity count, relationship count,
community count at each hierarchy level, and the wall-clock time and LLM
token cost of the extraction pass and the summarization pass separately, so a
sudden change in any of these on a routine reindex (a spike in entity count
with no corresponding change in document count, for example) surfaces the
kind of naming-inconsistency failure described in section 11 before it
reaches production queries.

At query time, log which search mode a question was routed to (global,
local, DRIFT, or basic, per section 8), the number of community reports read
in a global search's map stage, and the end-to-end latency broken down by the
map stage and the reduce stage separately, since the map stage is the one
whose cost is directly proportional to the chosen community-hierarchy level,
per section 7.

A healthy dashboard shows indexing cost and community count roughly
proportional to corpus size over time, query latency for global search
bounded within a narrow band regardless of which broad question was asked
(because the map-reduce pass reads a fixed set of community reports rather
than a variable amount of the corpus), and a mode-routing distribution that
roughly matches the narrow-versus-broad question mix measured during the
refactoring path in section 14.

A failing instance shows entity or relationship counts growing much faster
than document count on routine reindexes (naming fragmentation), global
search latency growing unboundedly as the corpus grows rather than staying
bounded by the configured hierarchy level and token budget, or a rising rate
of narrow-looking questions being routed to global search, which is the
misrouting failure from section 11 becoming visible in aggregate metrics
before any single user complaint pinpoints it.

## 17. Security and privacy implications

This dimension is largely engineering judgement drawn from the mechanism's
shape rather than a sourced claim about a specific product's security
posture.

The knowledge graph is a second, structured copy of information present in
the source corpus, and every entity, relationship, and community summary
derived from a sensitive source document is itself sensitive and needs the
same access controls the source document has. A system that enforces
document-level access control on the vector index but not on the graph store
or the community reports has a real exfiltration path, a user without access
to a specific source document could still learn its contents indirectly
through a community summary that synthesizes across that document and
others the user does have access to. This is a materially different risk
than plain vector RAG, where a retrieved chunk maps directly back to one
source document and existing document-level access control is comparatively
straightforward to apply at retrieval time.

Community summaries can also aggregate information across many source
documents in a way that makes it easier to re-identify or infer sensitive
facts about an individual than any single source document does on its own,
the same aggregation-inference risk long recognized in statistical
disclosure control for tabular data, now applying to a natural-language
summary instead of a table. A deployment handling personal data should treat
the community-summary generation step as a point where redaction or
differential-privacy-style controls, not merely access control, may be
warranted before a summary is persisted and made queryable.

The extraction and summarization LLM calls send full chunk text, and later
full community content, to whichever LLM provider performs those calls. A
deployment using a third-party hosted LLM for extraction is exposing the
entire corpus, not only the parts a given user's query would have retrieved
under plain RAG, to that provider during the one-time indexing pass, which is
a materially larger data-sharing surface at index time than plain RAG's
query-time-only exposure of retrieved chunks.

## 18. References

- Darren Edge, Ha Trinh, Newman Cheng, Joshua Bradley, Alex Chao, Apurva
  Mody, Steven Truitt, Dasha Metropolitansky, Robert Osazuwa Ness, Jonathan
  Larson, "From Local to Global. A Graph RAG Approach to Query-Focused
  Summarization", arXiv preprint 2404.16130, April 2024.
  `https://arxiv.org/abs/2404.16130`, verified 2026-08-02.
- Microsoft, GraphRAG documentation, indexing and query pages.
  `https://microsoft.github.io/graphrag/`, verified 2026-08-02.
- Microsoft, graphrag repository, GitHub. MIT license, 35.2k stars at
  verification time. `https://github.com/microsoft/graphrag`, verified
  2026-08-02.
- LlamaIndex, GraphRAG v2 cookbook.
  `https://web.archive.org/web/20260511030531/https://developers.llamaindex.ai/python/examples/cookbooks/graphrag_v2/`,
  verified 2026-08-02.
- Vincent A. Traag, Ludo Waltman, Nees Jan van Eck, "From Louvain to
  Leiden. Guaranteeing well-connected communities", Scientific Reports,
  volume 9, article 5233, 2019. Cited for the Leiden community-detection
  algorithm the reference GraphRAG implementation uses, per the
  microsoft.github.io/graphrag documentation cited above.
- Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir
  Karpukhin, Naman Goyal, Heinrich Kuttler, Mike Lewis, Wen-tau Yih, Tim
  Rocktaschel, Sebastian Riedel, Douwe Kiela, "Retrieval-Augmented
  Generation for Knowledge-Intensive NLP Tasks", NeurIPS 2020. Cited as the
  origin of the base Retrieval Augmented Generation pattern GraphRAG
  extends, per this repository's `retrieval-augmented-generation` entry.

## 19. Dynamics addendum, non-applicability list

See section 4 for the full non-applicability list with reasoning. In
summary, do not use GraphRAG for a small corpus that fits in context, a
workload with no broad or aggregate questions in practice, a corpus that
changes faster than a batch reindex can track, a corpus with little
relational structure between its pieces, or a team with no budget for the
added graph and community-summarization infrastructure.

## 20. Code examples

All three samples below build the same small graph from the same four-
sentence corpus, using a regex-based capitalized-word entity extractor and
connected-components clustering as deterministic, offline stand-ins for the
LLM-based extraction and Leiden-based clustering a production GraphRAG
pipeline uses, per the implementation variant described in section 8. Every
sample was executed against the toolchain listed and its output is shown
below the code.

### Python

```python
"""Minimal GraphRAG indexing and global search, no network calls.

Real GraphRAG calls an LLM twice: once per text chunk to extract
entities and relationships, once per community to write a summary.
This demo replaces both LLM calls with deterministic stand-ins so the
example runs offline and its output is reproducible. Swap
extract_entities and summarize_community for real LLM calls in
production and the rest of the pipeline is unchanged.
"""
from __future__ import annotations

import itertools
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field


@dataclass
class Graph:
    entities: set[str] = field(default_factory=set)
    edges: Counter = field(default_factory=Counter)
    mentions: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))

    def add(self, source_id: str, ents: list[str]) -> None:
        for e in ents:
            self.entities.add(e)
            self.mentions[e].append(source_id)
        for a, b in itertools.combinations(sorted(set(ents)), 2):
            self.edges[(a, b)] += 1


def extract_entities(chunk_id: str, text: str) -> list[str]:
    return sorted(set(re.findall(r"\b[A-Z][a-zA-Z]+\b", text)))


def build_graph(chunks: dict[str, str]) -> Graph:
    g = Graph()
    for chunk_id, text in chunks.items():
        g.add(chunk_id, extract_entities(chunk_id, text))
    return g


def detect_communities(g: Graph) -> list[set[str]]:
    """Connected components as a stand-in for Leiden clustering, per
    section 8's discussion of this simplification's limits."""
    parent: dict[str, str] = {e: e for e in g.entities}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for (a, b) in g.edges:
        union(a, b)

    groups: dict[str, set[str]] = defaultdict(set)
    for e in g.entities:
        groups[find(e)].add(e)
    return [members for members in groups.values() if members]


def summarize_community(members: set[str], g: Graph) -> str:
    weight = sum(
        g.edges[p]
        for p in itertools.combinations(sorted(members), 2)
        if p in g.edges
    )
    return f"{len(members)} entities ({', '.join(sorted(members))}), internal weight {weight}"


def global_search(question: str, community_summaries: list[str]) -> str:
    """Map-reduce over community summaries, per section 7."""
    q_terms = set(re.findall(r"\b[A-Za-z]+\b", question.lower()))
    scored = []
    for s in community_summaries:
        s_terms = set(re.findall(r"\b[A-Za-z]+\b", s.lower()))
        score = len(q_terms & s_terms)
        if score > 0:
            scored.append((score, s))
    scored.sort(reverse=True)
    if not scored:
        return "no relevant community found"
    return " | ".join(s for _, s in scored[:3])


if __name__ == "__main__":
    corpus = {
        "c1": "Alice founded Acme in Berlin with Bob as cofounder.",
        "c2": "Bob later left Acme to start Nimbus with Carol.",
        "c3": "Nimbus raised funding from Zeta Capital in Berlin.",
        "c4": "Zeta Capital also backed Orbit, a company unrelated to Acme.",
    }
    graph = build_graph(corpus)
    communities = detect_communities(graph)
    summaries = [summarize_community(m, graph) for m in communities]
    print(f"entities={len(graph.entities)} edges={len(graph.edges)} communities={len(communities)}")
    for s in summaries:
        print(" -", s)
    print(global_search("who funded Nimbus", summaries))
```

Run with `python3 graphrag.py`. Actual output on this machine, python3.

```
entities=9 edges=22 communities=1
 - 9 entities (Acme, Alice, Berlin, Bob, Capital, Carol, Nimbus, Orbit, Zeta), internal weight 24
9 entities (Acme, Alice, Berlin, Bob, Capital, Carol, Nimbus, Orbit, Zeta), internal weight 24
```

The corpus is small and densely interconnected through the shared entity
Berlin and the shared entity Zeta Capital, so connected components collapses
it into a single community. A real Leiden pass over the same graph, weighted
by co-occurrence strength, would likely still split Acme's founding story
from Zeta Capital's separate backing of Orbit, because Leiden optimizes for
internal density rather than mere connectivity. This is the exact limitation
of the connected-components stand-in named in section 8, shown rather than
hidden.

### TypeScript

```typescript
// Minimal GraphRAG indexing and local search, no network calls.
// extractEntities and summarizeCommunity stand in for LLM calls so
// the sample runs offline. Swap them for real LLM prompts to build a
// production pipeline; the graph and query logic below stays the same.

type Graph = {
  entities: Set<string>;
  edges: Map<string, number>;
  mentions: Map<string, string[]>;
};

function edgeKey(a: string, b: string): string {
  return a < b ? `${a}|${b}` : `${b}|${a}`;
}

function extractEntities(text: string): string[] {
  const matches = text.match(/\b[A-Z][a-zA-Z]+\b/g) ?? [];
  return Array.from(new Set(matches)).sort();
}

function buildGraph(chunks: Record<string, string>): Graph {
  const g: Graph = { entities: new Set(), edges: new Map(), mentions: new Map() };
  for (const [chunkId, text] of Object.entries(chunks)) {
    const ents = extractEntities(text);
    for (const e of ents) {
      g.entities.add(e);
      const list = g.mentions.get(e) ?? [];
      list.push(chunkId);
      g.mentions.set(e, list);
    }
    for (let i = 0; i < ents.length; i++) {
      for (let j = i + 1; j < ents.length; j++) {
        const key = edgeKey(ents[i], ents[j]);
        g.edges.set(key, (g.edges.get(key) ?? 0) + 1);
      }
    }
  }
  return g;
}

// Connected components stand in for the Leiden clustering GraphRAG
// runs in production, per section 8.
function detectCommunities(g: Graph): Set<string>[] {
  const parent = new Map<string, string>();
  for (const e of g.entities) parent.set(e, e);
  const find = (x: string): string => {
    let r = x;
    while (parent.get(r) !== r) r = parent.get(r)!;
    let cur = x;
    while (parent.get(cur) !== r) {
      const next = parent.get(cur)!;
      parent.set(cur, r);
      cur = next;
    }
    return r;
  };
  const union = (a: string, b: string) => {
    const ra = find(a);
    const rb = find(b);
    if (ra !== rb) parent.set(ra, rb);
  };
  for (const key of g.edges.keys()) {
    const [a, b] = key.split("|");
    union(a, b);
  }
  const groups = new Map<string, Set<string>>();
  for (const e of g.entities) {
    const root = find(e);
    if (!groups.has(root)) groups.set(root, new Set());
    groups.get(root)!.add(e);
  }
  return Array.from(groups.values());
}

function summarizeCommunity(members: Set<string>, g: Graph): string {
  const arr = Array.from(members).sort();
  let weight = 0;
  for (let i = 0; i < arr.length; i++) {
    for (let j = i + 1; j < arr.length; j++) {
      weight += g.edges.get(edgeKey(arr[i], arr[j])) ?? 0;
    }
  }
  return `${arr.length} entities (${arr.join(", ")}), internal weight ${weight}`;
}

// Local search: start from an entity the question names, walk its
// direct neighbors in the graph, return the neighborhood as context.
function localSearch(question: string, g: Graph): string {
  const named = extractEntities(question).filter((e) => g.entities.has(e));
  if (named.length === 0) return "no named entity found in question";
  const neighbors = new Set<string>();
  for (const key of g.edges.keys()) {
    const [a, b] = key.split("|");
    if (named.includes(a)) neighbors.add(b);
    if (named.includes(b)) neighbors.add(a);
  }
  return `seed=${named.join(",")} neighbors=${Array.from(neighbors).sort().join(",")}`;
}

const corpus: Record<string, string> = {
  c1: "Alice founded Acme in Berlin with Bob as cofounder.",
  c2: "Bob later left Acme to start Nimbus with Carol.",
  c3: "Nimbus raised funding from Zeta Capital in Berlin.",
  c4: "Zeta Capital also backed Orbit, a company unrelated to Acme.",
};

const graph = buildGraph(corpus);
const communities = detectCommunities(graph);
const summaries = communities.map((m) => summarizeCommunity(m, graph));
console.log(`entities=${graph.entities.size} edges=${graph.edges.size} communities=${communities.length}`);
for (const s of summaries) console.log(" -", s);
console.log(localSearch("What did Bob start after Acme?", graph));
```

Compiled with `tsc --strict --target es2020 --module commonjs` and run with
`node`. Actual output on this machine.

```
entities=9 edges=22 communities=1
 - 9 entities (Acme, Alice, Berlin, Bob, Capital, Carol, Nimbus, Orbit, Zeta), internal weight 24
seed=Acme,Bob neighbors=Acme,Alice,Berlin,Bob,Capital,Carol,Nimbus,Orbit,Zeta
```

This sample shows local search, which walks outward from the seed entities
named in the question (Acme and Bob, both capitalized words the extractor
recognizes) rather than reading the whole graph, the narrow-question path
described in section 7 and contrasted with global search's map-reduce pass
over every community.

### Go

```go
// Minimal GraphRAG indexing and global search, no network calls.
// extractEntities and summarizeCommunity stand in for LLM calls so
// this example runs offline. Replace them with real LLM prompts for
// production; the graph, clustering, and query logic stay the same.
package main

import (
	"fmt"
	"regexp"
	"sort"
	"strings"
)

var entityRe = regexp.MustCompile(`\b[A-Z][a-zA-Z]+\b`)

type Graph struct {
	Entities map[string]bool
	Edges    map[[2]string]int
}

func newGraph() *Graph {
	return &Graph{Entities: map[string]bool{}, Edges: map[[2]string]int{}}
}

func edgeKey(a, b string) [2]string {
	if a < b {
		return [2]string{a, b}
	}
	return [2]string{b, a}
}

func extractEntities(text string) []string {
	seen := map[string]bool{}
	var out []string
	for _, m := range entityRe.FindAllString(text, -1) {
		if !seen[m] {
			seen[m] = true
			out = append(out, m)
		}
	}
	sort.Strings(out)
	return out
}

func buildGraph(chunks map[string]string) *Graph {
	g := newGraph()
	for _, text := range chunks {
		ents := extractEntities(text)
		for _, e := range ents {
			g.Entities[e] = true
		}
		for i := 0; i < len(ents); i++ {
			for j := i + 1; j < len(ents); j++ {
				g.Edges[edgeKey(ents[i], ents[j])]++
			}
		}
	}
	return g
}

// detectCommunities uses union-find connected components as a stand
// in for the Leiden clustering GraphRAG runs in production, per
// section 8's discussion of this simplification's limits.
func detectCommunities(g *Graph) [][]string {
	parent := map[string]string{}
	for e := range g.Entities {
		parent[e] = e
	}
	var find func(string) string
	find = func(x string) string {
		if parent[x] != x {
			parent[x] = find(parent[x])
		}
		return parent[x]
	}
	union := func(a, b string) {
		ra, rb := find(a), find(b)
		if ra != rb {
			parent[ra] = rb
		}
	}
	for k := range g.Edges {
		union(k[0], k[1])
	}
	groups := map[string][]string{}
	for e := range g.Entities {
		root := find(e)
		groups[root] = append(groups[root], e)
	}
	var out [][]string
	for _, members := range groups {
		sort.Strings(members)
		out = append(out, members)
	}
	return out
}

func summarizeCommunity(members []string, g *Graph) string {
	weight := 0
	for i := 0; i < len(members); i++ {
		for j := i + 1; j < len(members); j++ {
			weight += g.Edges[edgeKey(members[i], members[j])]
		}
	}
	return fmt.Sprintf("%d entities (%s), internal weight %d", len(members), strings.Join(members, ", "), weight)
}

func globalSearch(question string, summaries []string) string {
	qTerms := map[string]bool{}
	for _, w := range strings.Fields(strings.ToLower(question)) {
		qTerms[w] = true
	}
	type scored struct {
		score int
		text  string
	}
	var results []scored
	for _, s := range summaries {
		score := 0
		for _, w := range strings.Fields(strings.ToLower(s)) {
			w = strings.Trim(w, ",()")
			if qTerms[w] {
				score++
			}
		}
		if score > 0 {
			results = append(results, scored{score, s})
		}
	}
	sort.Slice(results, func(i, j int) bool { return results[i].score > results[j].score })
	if len(results) == 0 {
		return "no relevant community found"
	}
	var parts []string
	for i, r := range results {
		if i >= 3 {
			break
		}
		parts = append(parts, r.text)
	}
	return strings.Join(parts, " | ")
}

func main() {
	corpus := map[string]string{
		"c1": "Alice founded Acme in Berlin with Bob as cofounder.",
		"c2": "Bob later left Acme to start Nimbus with Carol.",
		"c3": "Nimbus raised funding from Zeta Capital in Berlin.",
		"c4": "Zeta Capital also backed Orbit, a company unrelated to Acme.",
	}
	g := buildGraph(corpus)
	communities := detectCommunities(g)
	var summaries []string
	for _, m := range communities {
		summaries = append(summaries, summarizeCommunity(m, g))
	}
	fmt.Printf("entities=%d edges=%d communities=%d\n", len(g.Entities), len(g.Edges), len(communities))
	for _, s := range summaries {
		fmt.Println(" -", s)
	}
	fmt.Println(globalSearch("who funded Nimbus", summaries))
}
```

Run with `go run main.go`. Actual output on this machine.

```
entities=9 edges=22 communities=1
 - 9 entities (Acme, Alice, Berlin, Bob, Capital, Carol, Nimbus, Orbit, Zeta), internal weight 24
9 entities (Acme, Alice, Berlin, Bob, Capital, Carol, Nimbus, Orbit, Zeta), internal weight 24
```

Java, Rust, and Swift samples were not written for this entry. The pattern's
essential mechanics, per section 5 through section 8, are a data pipeline
(chunk, extract, cluster, summarize) followed by a query-time retrieval
strategy, and that shape does not idiomatically change across a general
purpose language the way, for example, a Visitor pattern's double dispatch
changes shape between a language with pattern matching and one without.
Python, TypeScript, and Go were chosen because they are the three languages
most GraphRAG tooling in the wild is actually written in, per the reference
implementation (Python) and the framework integration named in section 9
(TypeScript and Python are both common in that ecosystem, and Go is common
for the graph-serving infrastructure layer underneath).
