---
name: Graph of Thoughts
slug: graph-of-thoughts
family: 17-ai-agentic
category: AI and Agentic
aliases: [GoT, Graph of Operations, Thought Graph Prompting]
first_described: "Besta, Blach, Kubicek, Gerstenberger, Podstawski, Gianinazzi, Gajda, Lehmann, Niewiadomski, Nyczyk, Hoefler 2023 (arXiv preprint), AAAI 2024"
maturity: established
related: [tree-of-thoughts, chain-of-thought, self-consistency, reflexion, plan-execute, multi-agent-supervisor, orchestrator-worker, evaluator-optimizer]
incompatible_with: []
verified: 2026-08-02
---

# Graph of Thoughts

## 1. Name, aliases, and lineage

The canonical name is Graph of Thoughts, abbreviated GoT in every paper and
implementation that follows it. It was introduced in Maciej Besta, Nils
Blach, Ales Kubicek, Robert Gerstenberger, Michal Podstawski, Lukas
Gianinazzi, Joanna Gajda, Tomasz Lehmann, Hubert Niewiadomski, Piotr Nyczyk,
and Torsten Hoefler, "Graph of Thoughts. Solving Elaborate Problems with
Large Language Models," first posted to arXiv in August 2023 (arXiv 2308.09687)
and later published in the Proceedings of the AAAI Conference on Artificial
Intelligence, volume 38, issue 16, 2024, pages 17682 to 17690, DOI
10.1609/aaai.v38i16.29720
(https://ojs.aaai.org/index.php/AAAI/article/view/29720, verified 2026-08-02).
The abstract states the framework's purpose directly. "We introduce Graph of
Thoughts (GoT), a framework that advances prompting capabilities in large
language models (LLMs) beyond those offered by paradigms such as
Chain-of-Thought or Tree of Thoughts (ToT)" (same source, verified
2026-08-02).

The paper's own implementation uses two names for the same underlying idea
depending on which layer of the system is being discussed. **Graph of
Thoughts** names the general prompting paradigm, the claim that an LLM's
intermediate reasoning steps should be modeled as an arbitrary directed
graph rather than a chain or a tree. **Graph of Operations**, abbreviated
GoO, names the concrete, problem-specific execution plan a developer writes
before running the pipeline, a static description of which operations run
in which order and how their outputs feed one another. The reference
implementation at the SPCL (Scalable Parallel Computing Laboratory, ETH
Zurich) organization on GitHub exposes `GraphOfOperations` as the primary
class a caller constructs, together with a `Controller` that walks it, a
`Prompter` and a `Parser` that translate between the graph and raw LLM
text, and `Operation` subclasses named `Generate`, `Score`, `Aggregate`, and
`KeepBest` (https://github.com/spcl/graph-of-thoughts, verified 2026-08-02).
This entry treats Graph of Thoughts as the pattern name and Graph of
Operations as its concrete authoring artifact, the way a state machine
diagram is the artifact for the State pattern.

Two lineage claims matter for placing GoT correctly among its neighbors.
First, the paper is explicit that it generalizes, rather than replaces,
Chain-of-Thought (Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma,
Brian Ichter, Fei Xia, Ed Chi, Quoc Le, and Denny Zhou, "Chain-of-Thought
Prompting Elicits Reasoning in Large Language Models," arXiv 2201.11903,
2022, https://arxiv.org/abs/2201.11903, verified 2026-08-02) and Tree of
Thoughts (Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L.
Griffiths, Yuan Cao, and Karthik Narasimhan, "Tree of Thoughts. Deliberate
Problem Solving with Large Language Models," NeurIPS 2023, arXiv 2305.10601,
https://arxiv.org/abs/2305.10601, verified 2026-08-02). Chain-of-Thought
represents reasoning as a single linear sequence of intermediate steps. Tree
of Thoughts widens that to a tree, where a node can branch into several
candidate continuations that are explored and pruned, but a discarded branch
is gone for good and two branches can never be recombined into one. Graph of
Thoughts drops the tree's acyclic, single-parent constraint. A node in a GoT
graph can have more than one parent, which lets an **aggregation** operation
fold several independent thoughts into one improved thought, and a node can
feed back into an earlier stage of computation, which lets a **refinement**
loop revisit and repair a thought using feedback derived from a later step.
Second, this is what the paper's own headline numbers are built on. On a
64-element sorting task the authors report GoT improving output quality by
62 percent over Tree of Thoughts while reducing inference cost by more than
31 percent (same AAAI source, verified 2026-08-02), a result attributed
directly to the ability to merge partially-sorted sub-lists through
aggregation rather than regenerating a full solution from scratch after
every failed branch.

## 2. Problem and context

Chain-of-Thought and Tree of Thoughts both encode an assumption about the
shape of reasoning that holds for some problems and actively fights others.
Chain-of-Thought assumes the correct solution can be reached by a single
sequence of forward steps, which fits arithmetic word problems and short
logical deductions well, because those problems have one causal thread.
Tree of Thoughts loosens that to allow branching exploration with
backtracking, which fits search problems like Game of 24 or Mini Crosswords,
where the model needs to try several next moves and abandon the ones that
dead-end. Neither shape fits a class of problem that shows up constantly in
practice once an LLM is used for anything beyond a single self-contained
question, a class of problem whose solution is naturally built by combining
several independently-produced partial results into one, or by sending a
flawed result back for repair using feedback that only exists after the
flaw was observed.

Concretely, the situation looks like this in a real pipeline. A document
needs to be summarized, but it is too long for one context window, so it is
split into chunks, each chunk is summarized independently, and the chunk
summaries must then be merged into one coherent summary that a reader would
not be able to tell was assembled from parts. A sorting or set-deduplication
task on a large list is faster and more accurate if the list is split,
each part is processed, and the processed parts are merged, mirroring how a
merge sort or a map-reduce job would attack the same problem outside an LLM
context. A piece of generated code fails a test, the failing test's output
is fed back to the model along with the original draft, and the model
produces a repaired version, an operation that is neither a fresh branch
(Tree of Thoughts) nor the next link in a single chain (Chain-of-Thought)
but a loop back onto an earlier node with new information attached. Multiple
independent drafts of the same essay or argument are generated by different
prompting strategies, and the strongest paragraphs from each are combined
into a single final draft rather than one draft simply winning outright.

Each of these cases has the same underlying shape, more than one
intermediate result contributes to a later result, and, in the repair case,
information flows backward as well as forward. A tree structure cannot
represent the idea that a final answer depends on three earlier drafts at
once, because a tree node has exactly one parent by definition. Modeling
the same situation as a tree forces the developer to either pick one draft
and discard the others, losing information that was expensive to produce,
or to flatten the merge into a single oversized prompt that concatenates
every draft and asks the model to reconcile them in one shot, which
reintroduces the context-length and attention-dilution problems that
chunking existed to avoid in the first place. Graph of Thoughts exists to
give the aggregation and the feedback loop a first-class representation, so
the developer can write down exactly which prior thoughts a later thought
depends on and let the LLM operate on that explicit dependency structure
instead of on an undifferentiated wall of prior context.

## 3. Forces

The pattern balances several pressures that pull in different directions,
and naming which side each favors is what separates an honest account from a
sales pitch for the pattern.

- **Solution quality on combinable problems.** Favored, this is the
  pattern's whole reason to exist. When a correct answer genuinely requires
  synthesizing several partial results, GoT lets the model do that synthesis
  as its own explicit operation with its own prompt, rather than hoping a
  single long prompt implicitly performs the synthesis as a side effect of
  attention over a wall of text.
- **Token and dollar cost.** Mixed, and this is where intuition misleads
  people. Cost falls relative to Tree of Thoughts on problems where
  aggregation replaces a from-scratch regeneration, because merging two
  half-correct partial results is cheaper than throwing both away and
  generating a third candidate from nothing, which is the mechanism behind
  the paper's reported 31 percent cost reduction on sorting. Cost rises
  relative to Chain-of-Thought on any problem simple enough not to need
  branching or merging at all, because every GoT pipeline pays for a
  Controller loop, a graph traversal, and typically several parallel
  Generate calls that a single chain never pays for.
- **Structural complexity and authoring cost.** Sacrificed, and sharply.
  Writing a Graph of Operations means deciding, ahead of time, exactly which
  operations exist, how many branches each Generate step should produce, how
  many candidates Aggregate combines and in what grouping, and how many
  Score-then-refine cycles the pipeline is allowed before it gives up. That
  is a real engineering artifact with its own bugs, not a prompt string.
- **Latency.** Depends entirely on parallelism inside a level of the graph
  and is otherwise unfavorable. Independent Generate branches at the same
  graph depth can be issued concurrently and this is where a well-built GoT
  pipeline recovers wall-clock time, but a Refine loop that must wait on
  Score before it can decide whether another pass is needed is inherently
  sequential, and a deep graph with many sequential refine cycles is slower
  end to end than a single well-crafted chain prompt.
- **Debuggability and observability.** Favored compared to a single giant
  prompt, sacrificed compared to Chain-of-Thought. Every thought is a
  distinct, inspectable artifact with a distinct prompt and a distinct
  response, so a developer can look at exactly which intermediate merge
  produced a wrong answer. Against that, the graph itself, its shape, its
  branching factors, its refine-loop termination condition, is an extra
  moving part that a plain chain simply does not have to reason about.
- **Determinism and reproducibility.** Sacrificed. The same input can walk a
  different path through the graph on two runs if scoring or sampling has
  any stochastic component, and a graph with a refine loop bounded by
  stopping once the score passes a threshold or after N rounds can
  legitimately terminate at different nodes on different runs even with an
  identical prompt and an identical model, because the model's own sampling
  temperature affects which thoughts get generated at each Generate step.
- **Applicability breadth.** Sacrificed relative to Chain-of-Thought, which
  applies to essentially anything. GoT earns its cost only on problems that
  actually decompose into combinable or feedback-correctable sub-parts, and
  forcing an ill-fitting problem into a graph shape produces overhead with
  no corresponding benefit, which is why dimension 4 below is unusually
  important for this pattern.

## 4. Applicability and non-applicability

Reach for Graph of Thoughts when the following hold together.

- The problem naturally decomposes into sub-parts whose partial results
  must later be combined, merged, deduplicated, or reconciled into a single
  output, rather than the correct output emerging from picking exactly one
  of several candidates.
- Multiple independently-generated candidates for the same sub-problem are
  each individually of higher quality when they can draw on information the
  others do not have, so combining their best elements plausibly beats any
  single one of them on its own.
- The task benefits from a feedback loop where a later evaluation, a test
  failure, a scoring function, a validation error, needs to flow back into
  an earlier generation step to produce a repaired version, and that repair
  is cheaper or more reliable than regenerating from a blank prompt.
- The problem is large enough, or repeated often enough, that the
  engineering cost of authoring an explicit Graph of Operations is repaid by
  the quality or cost improvement over many invocations, not a one-off
  question asked a single time.
- There is a way to score or evaluate a thought, even approximately, because
  every operation that keeps the best of several candidates or decides
  whether a refine loop should run again depends on some notion of quality
  comparison between thoughts.

Do not reach for Graph of Thoughts, and the reasons matter as much as the
list itself.

- **The problem is a single linear derivation with no natural branch or
  merge point**, such as a short arithmetic word problem or a one-step
  classification. Chain-of-Thought answers this at a fraction of the cost
  and with none of the graph-authoring overhead, because there is nothing
  to aggregate and nothing to send backward.
- **The problem needs exploration and backtracking but never needs to merge
  two branches back together**, such as Game of 24 or a puzzle solved by
  trying candidate moves and abandoning dead ends. Tree of Thoughts is the
  correct fit here and is measurably simpler to implement, since it never
  needs the multi-parent aggregation machinery GoT exists to provide.
- **There is no reliable scoring function, even a rough one, for a thought.**
  Every keep-best and every refine-loop termination decision in GoT depends
  on comparing thoughts, and without a scorer the pipeline degenerates into
  either an arbitrary pick or an unbounded loop, neither of which is better
  than a simpler pattern would give for free.
- **Latency budget is tight and the task cannot exploit parallel Generate
  branches**, for instance an interactive chat turn where a user is waiting
  synchronously. A sequential refine loop or a deep graph adds latency a
  single well-tuned prompt or a bounded Tree of Thoughts search would not.
- **The task is a one-off, run once and never repeated**, where the fixed
  cost of authoring and testing a Graph of Operations, and of building the
  scoring and parsing logic each operation depends on, is larger than the
  entire value of running the task a single time.
- **The domain has no notion of combining two partial answers into a
  better answer than either alone.** Aggregation only helps when the
  domain's structure supports genuine synthesis. combining two guesses at a
  single fixed numeric answer, for example, does not produce a better guess
  the way combining two half-sorted lists produces a more-sorted list.

## 5. Structure

A Graph of Thoughts pipeline has five participants, each with a distinct
job, drawn directly from the roles the reference implementation assigns
(https://github.com/spcl/graph-of-thoughts, verified 2026-08-02).

- **Thought.** The unit of state in the graph. A thought carries a piece of
  content, which can be raw text, a parsed data structure, or a partial
  solution, plus a numeric score once it has been evaluated, plus a list of
  the thought ids that were its inputs. A thought is immutable once created,
  the same discipline event sourcing and persistent data structures use, so
  the whole graph forms an auditable derivation history rather than a set of
  mutable cells that overwrite their own history.
- **Graph of Operations (GoO).** The static execution plan, authored ahead
  of time by the developer, describing which operations run, in what order,
  and how each operation's inputs are drawn from earlier operations' output
  thoughts. This is analogous to a build system's DAG file or a workflow
  engine's pipeline definition, not to anything the LLM itself decides at
  runtime.
- **Operations.** The verbs of the pattern. **Generate** takes zero or more
  parent thoughts and produces one or more new candidate thoughts by
  prompting the LLM. **Score** evaluates one thought and attaches a numeric
  or categorical quality value to it, either by another LLM call acting as a
  judge or by a deterministic scoring function when the domain allows one.
  **Aggregate** takes two or more parent thoughts and produces a single
  merged child thought, the operation that makes the structure a graph
  rather than a tree, because that child now has more than one parent.
  **KeepBest** selects the top-k thoughts from a set by score and discards
  the rest, functioning as the pruning step that keeps the graph's frontier
  bounded. **Refine**, sometimes implemented as a Generate operation whose
  prompt includes a prior thought and its score or evaluation feedback,
  produces an improved version of an existing thought and typically
  introduces the cycle-back edge that a tree cannot represent.
- **Controller.** The runtime component that walks the Graph of Operations
  in dependency order, invoking each operation, feeding it the thoughts its
  declared parents produced, and recording every new thought into the
  Thought Graph as it is created.
- **Prompter and Parser.** A pair of translation components at the boundary
  between the graph and the LLM. The Prompter renders a thought or set of
  thoughts into the concrete prompt text a given operation sends to the
  model, and the Parser extracts structured thought content back out of the
  model's raw text response. Both are necessarily task-specific, since the
  shape of a prompt and parser for sorting a list bears no resemblance to
  the shape of a prompt and parser for summarizing a document, even though
  both run through the same Controller and the same Generate operation
  class.

## 6. ASCII structure diagram

```
                         +-----------------------+
                         |       Controller       |
                         |  walks the GoO in       |
                         |  dependency order       |
                         +-----------+-------------+
                                     |
                reads next Operation |  writes new Thought
                                     v
    +------------+           +--------------+           +------------+
    |  Prompter  | <-------- |  Operation   | --------> |   Parser   |
    | renders    |  prompt   |  Generate    |  raw text | extracts   |
    | template   |  text     |  Score       |           | thought    |
    | from       |           |  Aggregate   |           | content    |
    | thought(s) |           |  KeepBest    |           | from reply |
    +------------+           |  Refine      |           +------------+
                              +------+-------+
                                     |
                                     v
                          +----------------------+
                          |     LanguageModel      |
                          |    (LLM API call)      |
                          +-----------+------------+
                                      |
                                      v
                        +--------------------------+
                        |       Thought Graph        |
                        |  nodes = thoughts (state)   |
                        |  edges = parent references  |
                        |  a child may cite MORE than  |
                        |  one parent (Aggregate),      |
                        |  and a node may be revisited   |
                        |  by a later Refine (cycle)      |
                        +--------------------------+
```

## 7. Dynamics

The following sequence traces a document-merging pipeline. two chunk
summaries are generated independently, scored, and then aggregated into one
merged summary, which is scored again and sent through one refine pass
before being returned. It shows the two moves a tree cannot express, the
Aggregate step drawing on two parents and the Refine step looping back onto
a single node with new feedback attached.

```
Controller        Generate(A)    Generate(B)    Score        Aggregate     Refine
    |                  |              |            |              |           |
    |-- run op A ----->|              |            |              |           |
    |<-- thought T1 ---|              |            |              |           |
    |-- run op B --------------------->|            |              |           |
    |<-- thought T2 -------------------|            |              |           |
    |-- score T1, T2 --------------------------------->|              |           |
    |<-- scores(T1=0.6, T2=0.7) --------------------- |              |           |
    |-- aggregate(T1, T2) ---------------------------------------->|           |
    |<-- thought T3 (parents=[T1, T2]) -----------------------------|           |
    |-- score T3 -------------------------------------->|              |           |
    |<-- score(T3=0.75) ------------------------------ |              |           |
    |-- score below threshold, refine(T3, feedback) --------------------------->|
    |<-- thought T4 (parents=[T3]) -------------------------------------------- |
    |-- score T4 -------------------------------------->|              |           |
    |<-- score(T4=0.92) ------------------------------ |              |           |
    |-- 0.92 above threshold, STOP, return T4                                    |
```

Two properties of this trace are worth naming because they are the entire
value proposition of the pattern relative to Tree of Thoughts. T3 has two
parents, T1 and T2, an edge shape a tree's single-parent invariant forbids
outright. And T4's Refine step consumes T3's score as an input to its own
Generate prompt, meaning information produced downstream of T3 flows
backward into producing T4, which is a feedback edge, not a forward
expansion edge, and it is exactly the mechanism the original paper's authors
use to describe why GoT enhances thoughts using feedback loops (AAAI 2024
source, verified 2026-08-02).

## 8. Implementation variants

- **Reference Graph of Operations, one static plan per task family.** The
  spcl implementation's own pattern, where a developer writes a Python
  object describing the exact sequence of Generate, Score, Aggregate, and
  KeepBest calls for a specific task shape, for example splitting a list
  into k chunks, sorting each independently, and merging pairs of sorted
  chunks in a binary-tree-of-merges shape (https://github.com/spcl/graph-of-thoughts,
  verified 2026-08-02). This is the most predictable variant because the
  graph's shape is fixed at authoring time and does not depend on runtime
  data, which makes it straightforward to test and to reason about cost
  ahead of running it.
- **Dynamic graph construction, shape decided at runtime.** Instead of a
  fixed GoO, the Controller decides how many Generate branches to spawn, or
  whether to run another Aggregate pass, based on the scores it observes as
  it goes, for example spawning additional candidate branches only when the
  current best score is below a threshold. This trades predictability for
  the ability to spend more compute exactly where the problem is hard and
  less where an early candidate already scores well, at the cost of a
  Controller that is itself harder to test because its behavior is now
  data-dependent rather than fixed.
- **General-purpose orchestration frameworks used as a graph substrate.**
  Rather than the paper's own bespoke Controller, a general agent
  orchestration library that already models workflows as directed graphs
  with cyclic control flow is used to host the same Generate, Score,
  Aggregate shape. LangGraph (LangChain Inc.) is the clearest example, since
  its own documentation describes agent workflows as nodes, edges, shared
  state, and explicitly supported cycles for iterative reasoning
  (https://www.langchain.com/langgraph, verified 2026-08-02), and Microsoft's
  AutoGen exposes an equivalent capability through its `GraphFlow` team type
  and `DiGraphBuilder`, described in its own documentation as executing
  multi-agent workflows using directed graphs, with support for sequential
  chains, parallel fan-outs, fan-in joins, conditional branching, and loops
  with exit conditions
  (https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/graph-flow.html,
  verified 2026-08-02, and noted there as an experimental, evolving API).
  Using one of these frameworks means inheriting its state persistence,
  retry, and human-in-the-loop machinery for free, at the cost of coupling
  the GoT-shaped reasoning logic to that framework's own execution model and
  versioning cadence.
- **Bounded refine loop with an explicit termination clause.** Because a
  cycle in the graph has no natural stopping point the way a tree's finite
  depth does, every production implementation needs an explicit termination
  rule attached to any Refine edge, typically a maximum number of rounds, a
  score threshold, a wall-clock timeout, or some combination of the three.
  Omitting this is not a stylistic choice, it is the single most common
  defect in a hand-rolled GoT pipeline and is covered under dimension 11.
- **Deterministic scorer versus LLM-as-judge scorer.** When the domain
  supplies an objective measure, for instance counting inversions to score
  how sorted a list is, or running a generated program's test suite to score
  correctness, the Score operation is a plain function with no LLM call,
  which is faster, cheaper, and fully deterministic. When no such measure
  exists, for instance judging which of two prose summaries reads more
  coherently, Score becomes another LLM call structured as a judge, which
  reintroduces every reliability concern the llm-as-judge pattern in this
  same family carries, including the judge's own inconsistency across
  repeated calls on the identical input.
- **Aggregation grouping strategy.** How Aggregate chooses which thoughts to
  combine is itself a design decision with several concrete shapes, among
  them pairwise merges arranged as a binary tree of aggregations, which is
  what the sorting example uses to merge sorted chunks two at a time, an
  all-at-once merge that hands every surviving candidate to a single
  Aggregate call, which is cheaper in call count but degrades once the
  number of candidates grows large enough to strain the model's context and
  attention, and a top-k merge that first runs KeepBest to prune the
  candidate set before aggregating only the survivors, trading a small risk
  of discarding a candidate that would have contributed something useful for
  a materially smaller and cheaper aggregation prompt.
- **Volatile in-process graph versus a persisted graph store.** The
  reference implementation and most hand-rolled GoT pipelines keep the
  thought graph as an in-memory object for the duration of one pipeline run
  and discard it afterward, which is adequate for a request-scoped task. A
  long-running or auditable pipeline, for example a compliance workflow
  where every intermediate reasoning step must be inspectable after the
  fact, instead persists each thought as a row in a database or an event in
  an event log as it is created, turning the thought graph into durable,
  queryable evidence rather than a value that exists only inside one
  process's memory.

## 9. Known production uses

- **spcl/graph-of-thoughts, ETH Zurich Scalable Parallel Computing
  Laboratory.** The paper authors' own open-source reference implementation,
  which exposes `GraphOfOperations`, `Controller`, `Prompter`, and `Parser`
  as public classes and ships worked examples for sorting 32-element and
  64-element lists, keyword counting, set operations, and document merging.
  The repository is maintained under the SPCL GitHub organization and had
  reported roughly 2.8 thousand stars and 217 forks at the time this entry
  was verified (https://github.com/spcl/graph-of-thoughts, verified
  2026-08-02). This is the canonical, citable instance of the pattern rather
  than an inference from the paper's prose alone, because it is the exact
  code the paper's reported sorting and merging benchmarks were run against.
- **LangGraph, LangChain Inc.** A general-purpose agent orchestration
  library, described in its own product documentation as an agent runtime
  and low-level orchestration framework that models workflows through
  nodes, edges, shared state, and explicitly supported cycles for iterative
  reasoning and multi-agent control flow. LangChain's own product page lists
  a substantial roster of companies running LangGraph in production,
  including Klarna, Uber, LinkedIn, Cisco, Elastic, Coinbase, and Replit
  (https://www.langchain.com/langgraph, verified 2026-08-02). LangGraph does
  not implement the spcl `GraphOfOperations` API, but it is a real production
  substrate for the identical structural idea GoT formalizes, an explicit
  directed graph of reasoning or agent steps with cycles and multi-parent
  merge points, cited here as evidence the underlying graph-of-reasoning
  shape has been adopted well beyond the original research artifact.
- **Microsoft AutoGen, GraphFlow and DiGraphBuilder.** AutoGen's stable
  documentation describes `GraphFlow` as a team implementation designed for
  scenarios where strict control over the order in which agents act is
  needed, or when different outcomes must lead to different next steps,
  with agents represented as graph nodes, edges carrying optional
  conditions on message content, and explicit support for parallel
  fan-out, fan-in joins, conditional branching, and loops with exit
  conditions, authored through the `DiGraphBuilder` fluent utility
  (https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/graph-flow.html,
  verified 2026-08-02). The same documentation labels GraphFlow an
  experimental feature whose API is subject to change, which is recorded
  here plainly rather than smoothed over, since a reader evaluating this as
  a production dependency needs that caveat as much as the capability
  description.

## 10. Consequences

Positive.

- Aggregation lets the pipeline recover value from every branch it
  generates, instead of throwing away every candidate but one the way Tree
  of Thoughts' pruning does, which the paper's own sorting benchmark ties
  directly to both a quality improvement and a cost reduction relative to
  ToT.
- A feedback-driven Refine loop gives the pipeline a way to correct a
  specific, identified flaw in an existing thought, which is typically
  cheaper in tokens than regenerating an entire solution from a blank
  prompt and discarding whatever was salvageable in the flawed draft.
- Every thought is a discrete, independently inspectable artifact with an
  explicit list of its parent thoughts, which turns the reasoning process
  into an auditable derivation graph rather than a single undifferentiated
  block of text a developer must reverse-engineer after the fact.
- Independent Generate branches at the same graph depth can be dispatched
  concurrently, recovering wall-clock latency that a strictly sequential
  chain of prompts cannot.

Negative.

- The Graph of Operations is a real piece of software the developer must
  design, test, and maintain, with its own bugs, its own versioning
  concerns as the underlying task evolves, and its own review burden
  distinct from prompt-string maintenance.
- A refine loop with no explicit, bounded termination condition has no
  natural stopping point the way a tree's fixed depth or a chain's fixed
  step count does, and an unbounded loop is a direct cost and latency risk.
- Determinism is weaker than a single chain prompt, because scoring
  variance and sampling variance can steer two runs of the identical input
  down different graph paths and to different final answers.
- The pattern's cost and quality advantage is conditional on the problem
  genuinely decomposing into combinable or feedback-correctable parts. On a
  problem that does not decompose this way, the pattern adds authoring and
  runtime overhead with no offsetting benefit, which is why the
  non-applicability list in dimension 4 carries real engineering weight and
  is not boilerplate.

## 11. Failure modes and misuse

- **Symptom.** The pipeline runs to completion but its cost, measured in
  tokens or dollars, is higher than a single chain prompt would have been,
  and quality is no better. **Cause.** The task was forced into a GoT shape
  even though it had no genuine decomposition or aggregation opportunity, so
  every extra Generate and Score call added cost without adding information
  the model could not already produce in one pass. **Fix.** Re-evaluate the
  problem against the non-applicability list in dimension 4 before building
  the pipeline, and if there is no real merge or feedback opportunity, drop
  back to Chain-of-Thought or a single well-crafted prompt.
- **Symptom.** A refine loop that occasionally never returns, or returns
  only after an operator manually kills the job, with logs showing dozens of
  Refine and Score calls against the same thought lineage. **Cause.** The
  loop's termination condition was written to stop once the score is good
  enough with no maximum round count and no wall-clock timeout, and on a
  hard input the score oscillates around the threshold or improves too
  slowly to cross it. **Fix.** Attach both a hard maximum round count and a
  wall-clock timeout to every Refine edge, in addition to any score
  threshold, and treat exhausting the round budget as a defined, expected
  outcome the caller handles rather than an unexpected hang.
- **Symptom.** Two runs of the exact same input produce materially
  different final answers, and a stakeholder loses confidence in the
  pipeline because it appears inconsistent. **Cause.** Non-zero sampling
  temperature on Generate calls, combined with an LLM-as-judge Score
  operation whose own output varies between calls, compounds across several
  graph levels, so small per-call variance accumulates into a visibly
  different final path through the graph. **Fix.** Lower or zero the
  sampling temperature on Generate calls where the task tolerates it, and
  where a deterministic scoring function is available for the domain,
  prefer it over an LLM judge for Score, reserving the judge variant for
  domains that genuinely have no deterministic measure.
- **Symptom.** Aggregate calls that combine more than a handful of parent
  thoughts silently drop content from some of the parents, and the merged
  thought reads as though only two or three of the five inputs were
  actually considered. **Cause.** The Aggregate prompt concatenates every
  parent thought's full text into a single prompt, and the model's
  attention over a long, undifferentiated input degrades the same way it
  does in any long-context summarization task, an effect distinct from the
  graph structure itself but triggered by an aggregation grouping strategy
  that scales the merge fan-in without bound. **Fix.** Bound the fan-in of
  any single Aggregate call, for example merging no more than two or three
  parents per call and arranging larger merges as a binary tree of pairwise
  aggregations, the same strategy the reference implementation uses for
  sorting large lists.
- **Symptom.** The pipeline reliably produces a good final answer in
  development against a handful of hand-picked test cases, then produces
  clearly worse answers once real, more varied production inputs start
  arriving, with no code change between the two. **Cause.** The Graph of
  Operations was authored and tuned, branching factors, aggregation
  grouping, refine round limits, against the shape of the small test set,
  and those fixed structural choices do not generalize to inputs whose
  natural decomposition differs, for example a document-merging pipeline
  tuned against three-chunk documents receiving an eight-chunk document in
  production. **Fix.** Treat the Graph of Operations itself as a tunable
  artifact validated against a representative range of input shapes and
  sizes, not a one-time design decision, and add a golden-dataset style
  regression check, see the golden-dataset pattern elsewhere in this
  family, that specifically covers the range of decomposition sizes the
  pipeline will see in production.

## 12. Trade-off matrix

| Force | Graph of Thoughts | Tree of Thoughts | Chain-of-Thought | Self-Consistency |
|---|---|---|---|---|
| Merges independent partial results | Native, first-class Aggregate operation | Not supported, a discarded branch cannot be recombined | Not applicable, single thread has nothing to merge | Combines final answers by majority vote only, not intermediate reasoning |
| Feedback-driven repair of a prior step | Native, Refine edges cycle back onto earlier nodes | Not supported, only forward expansion and pruning | Not supported, no branch or revisit point exists | Not supported |
| Authoring cost | High, an explicit Graph of Operations must be designed and tested | Moderate, a search strategy and beam width must be chosen | Low, a single prompt template | Low, one prompt template plus a vote aggregator |
| Determinism | Weakest of the four, cumulative variance across graph levels | Weak, search path can vary run to run | Strongest, one linear path | Moderate, variance averages out across N samples |
| Cost on a simple, single-thread problem | Highest, pays for graph machinery it does not need | Higher than Chain-of-Thought, pays for branching it does not need | Lowest | Higher than Chain-of-Thought, pays for N samples |
| Cost on a decomposable, mergeable problem | Lowest of the four per the paper's sorting benchmark, more than 31 percent below Tree of Thoughts | Higher, regenerates whole candidates instead of merging partial ones | Not competitive in quality on this problem shape | Not applicable, nothing to decompose into a vote |

## 13. Related and incompatible patterns

Graph of Thoughts sits directly above Tree of Thoughts and Chain-of-Thought
in a strict generalization relationship, every chain is a graph with no
branches and no merges, and every tree is a graph whose nodes happen to have
exactly one parent each, so a GoT-capable Controller can execute a
Chain-of-Thought or Tree of Thoughts plan by simply never using the
Aggregate operation and never adding a cycle-back edge. This is why the
`related` list in this entry's frontmatter includes both `chain-of-thought`
and `tree-of-thoughts` rather than treating them as competitors, they are
the degenerate special cases GoT contains.

Self-Consistency (see `self-consistency` in this same family) is a narrower,
cheaper cousin worth distinguishing carefully. Self-Consistency samples N
independent full chains and takes a majority vote over their final answers,
which superficially resembles GoT's Generate-then-Aggregate shape but
differs in an important way. Self-Consistency's vote only ever looks at
final answers, never at intermediate reasoning content, and it cannot merge
partial solutions, only pick the most common one. GoT's Aggregate operation
genuinely synthesizes a new thought from the content of its parents, which
is why GoT can improve on a problem, like sorting, where no single candidate
among several independent attempts is actually correct on its own, but the
correct answer emerges from combining pieces of several of them.

Reflexion (see `reflexion` in this same family) shares GoT's feedback-loop
idea closely, an agent that reflects on a prior failure and produces an
improved attempt. The distinction is structural rather than conceptual.
Reflexion is typically implemented as a single linear episodic memory that
an agent appends to and re-reads on its next attempt, not as an explicit
multi-node graph with named Score and Refine operations and inspectable
parent references. A GoT pipeline can implement a Reflexion-style loop as
one specific instance of a Refine edge, but Reflexion itself does not
require, and usually does not have, the broader graph machinery of
multi-parent Aggregate nodes.

Plan-and-Execute and Orchestrator-Worker (see `plan-execute` and
`orchestrator-worker` in this same family) compose naturally above GoT
rather than competing with it, since a Plan-and-Execute planner or an
Orchestrator can decide, at a coarse level, that a particular sub-task
warrants a full Graph of Thoughts pipeline, invoke it as a single step in
its own plan, and treat the pipeline's final kept-best thought as that
step's result, the same way a build orchestrator invokes a specialized
compiler as one step in a larger pipeline without needing to understand the
compiler's own internal graph.

Evaluator-Optimizer (see `evaluator-optimizer` in this same family) is
close enough to a GoT Score-then-Refine pair that the two are frequently
confused. Evaluator-Optimizer names the general two-role loop of one
component judging output and another improving it based on that judgment,
independent of any graph structure. GoT's Score and Refine operations are
one concrete way to implement an Evaluator-Optimizer loop inside a larger
graph that also does other things, aggregation among them, that a bare
Evaluator-Optimizer loop does not by itself provide.

No pattern in this family is flatly incompatible with Graph of Thoughts in
the sense of being impossible to combine, which is why the frontmatter's
`incompatible_with` list is empty. The practical tension is not
incompatibility but redundancy, building a full GoT pipeline around a
problem that Chain-of-Thought or a bounded Tree of Thoughts search already
solves adequately is wasted engineering effort, covered as the first failure
mode in dimension 11.

## 14. Refactoring path in and out

Introducing Graph of Thoughts into an existing pipeline that currently uses
a single chain prompt, or a hand-rolled ad hoc branching prompt, follows a
sequence that keeps every intermediate step independently testable.

1. Identify the specific sub-task that actually needs decomposition,
   aggregation, or a feedback loop, rather than converting the entire
   pipeline at once. A document-summarization pipeline, for instance, might
   only need GoT for the chunk-merging step, while the initial per-chunk
   summarization stays a plain Chain-of-Thought call.
2. Define the Thought shape for that sub-task, the concrete data the
   pipeline will pass between operations, before writing any prompts. For
   the merging example this might be a plain string containing a summary
   draft plus an attached numeric coherence score.
3. Write the Score function first, in isolation, and unit test it against
   known-good and known-bad examples before any Generate or Aggregate
   prompt exists, because every later operation's correctness depends on
   Score being trustworthy, and a scorer that is itself wrong will silently
   corrupt everything downstream of it.
4. Write and independently test the Generate operation, verifying that its
   Prompter renders a correct prompt from a given input and its Parser
   correctly extracts a Thought from a range of realistic model responses,
   including malformed ones, before wiring it into any larger graph.
5. Write and independently test the Aggregate operation the same way,
   feeding it a small, fixed pair of parent thoughts and asserting the
   merged result is plausible, before connecting it to live Generate output.
6. Assemble the Graph of Operations, initially with fixed, conservative
   branching and fan-in numbers, for example two Generate branches and
   pairwise Aggregate merges, and run it end to end against a small
   representative sample before tuning those numbers upward.
7. Add explicit bounds to any Refine edge, a maximum round count and a
   timeout, before that edge is allowed to run against real traffic, per
   the second failure mode in dimension 11.
8. Only after the fixed-shape pipeline is validated should a team consider
   the dynamic-graph-construction variant from dimension 8, where the
   Controller decides branching at runtime, since that variant is strictly
   harder to test and should not be the starting point.

Removing Graph of Thoughts, once a pipeline no longer needs it, most often
because the underlying task turned out not to decompose the way it was
expected to, or because a simpler pattern was proven sufficient once real
production data arrived, follows the reverse path.

1. Confirm which specific operation, usually a single Aggregate or Refine
   edge, is providing negligible measured value relative to its cost, using
   the same scoring function the pipeline already has rather than a fresh
   subjective judgment.
2. Collapse the smallest removable sub-graph first, cutting the round
   limit on a Refine loop to one before removing the loop outright when its
   score rarely improves after the first round, to confirm the hypothesis
   incrementally rather than deleting the whole mechanism in one step.
3. Once a sub-graph has been proven unnecessary, replace it with a direct
   call to whichever single operation remains, typically collapsing a
   Generate-Score-Aggregate-Score sequence down to a single Generate call
   with a slightly richer prompt, effectively refactoring the pipeline back
   toward Chain-of-Thought.
4. Delete the now-unused Prompter and Parser code for the removed
   operations rather than leaving them dormant in the codebase, since dead
   prompt-rendering logic is exactly the kind of code that silently drifts
   out of sync with the model or the domain and becomes a liability the next
   time someone reads it expecting it to be live.

## 15. Testing and verification

A Graph of Thoughts pipeline decomposes cleanly into independently testable
layers, which is one of the pattern's real practical advantages over a
single monolithic prompt, and each layer calls for a different testing
technique.

The Controller and the Graph of Operations traversal logic are ordinary
deterministic code with no LLM involved, and should be tested exactly like
any graph-traversal or workflow-engine code, with unit tests that construct
a small fixed GoO, feed the Controller fake operations that return
predetermined thoughts, and assert the Controller invokes each operation in
the correct dependency order with the correct parent thoughts as input. This
layer needs zero LLM calls to test thoroughly, and a test suite that
exercises the Controller only against a live model is testing the wrong
layer for the wrong reason.

Score functions, when deterministic, are tested with plain unit tests
against known inputs and expected scores, the same as any pure function.
When Score is implemented as an LLM-as-judge call, it inherits every testing
concern the llm-as-judge pattern documents elsewhere in this family,
principally that a small, hand-labeled golden set of thought examples paired
with expected relative rankings is needed to detect judge drift over time,
because a judge's absolute score values are rarely stable across model
versions even when its relative rankings remain useful.

Prompter and Parser components are tested with fixture-based tests that do
not call a live model at all. a fixed input thought is rendered through the
Prompter and the resulting prompt text is asserted against an expected
template, and a fixed range of realistic and adversarial raw model
responses, including truncated, malformed, or off-format ones, is fed
through the Parser to assert it either extracts the expected thought or
raises a clear, typed error rather than silently returning corrupted or
partial content.

Generate and Aggregate operations, because they call a live model, are best
tested at two separate levels. A cheap, fast, deterministic test suite runs
against a recorded, replayed set of model responses, verifying the
operation's own logic, how many candidate thoughts it produces, how it wires
parent references, without incurring live API cost or flakiness on every
test run. A smaller, slower live-model evaluation suite, run less frequently
and treated as an integration test rather than a unit test, exercises the
same operations against the real model on a fixed, versioned set of inputs
and checks aggregate quality metrics have not regressed, following the same
golden-dataset discipline the pattern of that name in this family describes.

The graph's cycle-bound termination logic, the maximum round count and
timeout on any Refine edge from dimension 8 and dimension 11, needs its own
explicit test that constructs a mock Score function which always returns a
value just below the improvement threshold, forcing the loop to run to its
configured maximum, and asserts the pipeline terminates at that maximum
rather than hanging, which is the single most important safety property to
verify before this pattern reaches production traffic.

## 16. Observability signals

A healthy Graph of Thoughts pipeline in production shows a small number of
consistent, predictable signals, and the absence of any one of them is
usually the earliest warning of one of the failure modes in dimension 11.

Every thought created should be logged or traced with, at minimum, its
operation type, its parent thought ids, its score once scored, and the
graph-level depth at which it was produced, forming a durable derivation
record for the run. A distributed tracing span per operation invocation,
with the Graph of Operations run itself as the parent span and each
Generate, Score, and Aggregate call as a child span, makes the shape of a
specific run visible at a glance, and a dashboard built on that tracing data
should show, per pipeline, the median and p99 number of Generate calls per
run, the median and p99 number of Refine rounds per run, and the
distribution of scores at each KeepBest cut point.

A rising trend in the number of Refine rounds a typical run consumes,
without a corresponding rise in final score, is the clearest leading
indicator of the second failure mode in dimension 11, a refine loop that is
grinding without converging, and should alert well before it produces
outright timeouts. A rising trend in per-run token cost with a flat or
declining final quality score, tracked against the same golden-dataset
baseline mentioned in dimension 15, is the clearest leading indicator of the
first failure mode, a task that no longer benefits from the graph structure
it is paying for.

Per-operation latency should be tracked separately for Generate, Score, and
Aggregate calls, because the three have materially different expected cost
profiles, and a spike isolated to Aggregate specifically, while Generate and
Score stay flat, points at the fourth failure mode, an unbounded aggregation
fan-in degrading with prompt length rather than a general model slowdown.
Alerting thresholds should be set per operation type for exactly this
reason, a single blended latency alert across all operation types in the
pipeline hides which specific operation is the actual source of a
regression.

## 17. Security and privacy implications

The attack surface a Graph of Thoughts pipeline opens is largely the same
prompt-injection surface any multi-step LLM pipeline carries, but the
Aggregate operation concentrates a specific version of it worth naming
directly. because Aggregate's prompt is constructed from the content of
several prior thoughts, and each of those prior thoughts may itself
originate, directly or indirectly, from untrusted user input or from
external retrieved content earlier in the pipeline, an Aggregate call is a
point where instructions embedded in one branch's output can influence how
the model treats a different branch's content when the two are combined.
This is a structural version of the general prompt-injection concern
covered by the prompt-injection-defense pattern in this same family, and the
same input-sanitization and output-guardrail disciplines that pattern
documents apply directly to every Generate and Aggregate boundary in a GoT
pipeline, not only to the pipeline's single external entry point.

Because every thought persists as a node in an inspectable graph, and
because a persisted graph, per the storage variant in dimension 8, may
retain every intermediate draft rather than only the final answer, any
sensitive content that entered the pipeline through an early Generate call
propagates into every later thought whose lineage includes it, and that
lineage can be several Aggregate steps removed from the point where the
sensitive content first entered. A data-retention or right-to-deletion
policy that only scrubs a pipeline's final output, while leaving intermediate
thoughts in a persisted store, misses this propagation entirely, so any
persisted thought graph in a regulated domain needs the same retention and
deletion discipline applied to every node, not only the terminal one.

The Refine loop's feedback channel is worth a specific note because it is
the pattern's one genuinely novel security-relevant surface relative to
Chain-of-Thought or Tree of Thoughts. Feedback fed into a Refine prompt,
for instance a test failure's stack trace in a code-repair pipeline, may
itself contain untrusted content, such as user-supplied test input that
produced the failure, and that feedback is deliberately being fed back into
a generation step specifically so the model treats it as instructive
context, which is precisely the condition under which prompt injection is
most effective. Any Refine pipeline whose feedback source includes content
an external party can influence should treat that feedback with the same
suspicion and sanitization the pipeline's original entry point receives, not
as an internal, implicitly trusted signal.

This entry does not identify a cryptographic or authentication-specific
concern beyond the general one any networked LLM API call carries, and says
so plainly rather than inventing one.

## 18. References

- Maciej Besta, Nils Blach, Ales Kubicek, Robert Gerstenberger, Michal
  Podstawski, Lukas Gianinazzi, Joanna Gajda, Tomasz Lehmann, Hubert
  Niewiadomski, Piotr Nyczyk, Torsten Hoefler, "Graph of Thoughts. Solving
  Elaborate Problems with Large Language Models," Proceedings of the AAAI
  Conference on Artificial Intelligence, volume 38, issue 16, 2024, pages
  17682 to 17690, DOI 10.1609/aaai.v38i16.29720.
  https://ojs.aaai.org/index.php/AAAI/article/view/29720, verified
  2026-08-02.
- Maciej Besta et al., "Graph of Thoughts. Solving Elaborate Problems with
  Large Language Models," arXiv preprint arXiv 2308.09687, 2023.
  https://arxiv.org/abs/2308.09687, verified 2026-08-02.
- spcl (Scalable Parallel Computing Laboratory, ETH Zurich),
  graph-of-thoughts reference implementation, GitHub repository.
  https://github.com/spcl/graph-of-thoughts, verified 2026-08-02.
- Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L. Griffiths,
  Yuan Cao, Karthik Narasimhan, "Tree of Thoughts. Deliberate Problem
  Solving with Large Language Models," Advances in Neural Information
  Processing Systems 36, NeurIPS 2023.
  https://arxiv.org/abs/2305.10601, verified 2026-08-02.
- Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei
  Xia, Ed Chi, Quoc Le, Denny Zhou, "Chain-of-Thought Prompting Elicits
  Reasoning in Large Language Models," arXiv preprint arXiv 2201.11903,
  2022. https://arxiv.org/abs/2201.11903, verified 2026-08-02.
- LangChain Inc., "LangGraph," product documentation page.
  https://www.langchain.com/langgraph, verified 2026-08-02.
- Microsoft, "GraphFlow (Experimental)," AutoGen AgentChat user guide.
  https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/graph-flow.html,
  verified 2026-08-02.

## Code examples

The three implementations below share one worked problem to keep the
comparison honest across languages, a subset-sum search where several
independent candidate subsets are generated (the Generate operation), the
two highest-scoring candidates are merged into a new candidate that draws
elements from both (the Aggregate operation, the move a tree cannot
express), and the best thought across the whole graph, not merely the final
frontier, is returned. In a production pipeline the `generate` and
`aggregate` functions shown here would call an LLM and parse its response
through a Prompter and Parser as described in dimension 5. here they are
implemented as plain deterministic search so the samples run with no
network access and no API key, which keeps them honest examples of the
pattern's graph structure and operation shape rather than a demonstration of
prompting a specific model.

```python
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations

Numbers = tuple[int, ...]


@dataclass
class Thought:
    id: int
    subset: Numbers
    parents: tuple[int, ...]
    op: str


class ThoughtGraph:
    def __init__(self) -> None:
        self._next_id = 1
        self.nodes: dict[int, Thought] = {}

    def add(self, subset: Numbers, parents: tuple[int, ...], op: str) -> Thought:
        node = Thought(self._next_id, subset, parents, op)
        self.nodes[node.id] = node
        self._next_id += 1
        return node


def score(subset: Numbers, target: int) -> int:
    return -abs(target - sum(subset))


def generate(pool: Numbers, k: int, count: int) -> list[Numbers]:
    return list(combinations(pool, k))[:count]


def aggregate(a: Numbers, b: Numbers, target: int) -> Numbers:
    merged = tuple(sorted(set(a) | set(b)))
    best, best_gap = merged, abs(target - sum(merged))
    for size in range(1, len(merged) + 1):
        for combo in combinations(merged, size):
            gap = abs(target - sum(combo))
            if gap < best_gap:
                best, best_gap = combo, gap
    return best


def solve(pool: Numbers, target: int, refine_rounds: int = 2) -> tuple[Thought, ThoughtGraph]:
    graph = ThoughtGraph()
    frontier = [graph.add(s, (), "generate") for s in generate(pool, k=3, count=4)]

    for _ in range(refine_rounds):
        frontier.sort(key=lambda t: score(t.subset, target), reverse=True)
        top = frontier[:2]
        if len(top) < 2:
            break
        merged = aggregate(top[0].subset, top[1].subset, target)
        frontier.append(graph.add(merged, (top[0].id, top[1].id), "aggregate"))

    best = max(graph.nodes.values(), key=lambda t: score(t.subset, target))
    return best, graph


if __name__ == "__main__":
    pool = (2, 5, 9, 11, 14, 20)
    best, graph = solve(pool, target=25)
    print(
        f"nodes={len(graph.nodes)} best_subset={best.subset} "
        f"sum={sum(best.subset)} op={best.op} parents={best.parents}"
    )
```

Running the Python sample prints, on one line, that the graph holds six
nodes, the best subset is (5, 20), its sum is 25, and its op is aggregate
with parents (4, 3), showing the best thought was produced by an Aggregate
call whose parents were two independently generated candidates, neither of
which alone summed to the target.

```typescript
type Thought = { id: number; subset: number[]; parents: number[]; op: string };

class ThoughtGraph {
  nodes = new Map<number, Thought>();
  private next = 1;
  add(subset: number[], parents: number[], op: string): Thought {
    const t: Thought = { id: this.next++, subset, parents, op };
    this.nodes.set(t.id, t);
    return t;
  }
}

function score(subset: number[], target: number): number {
  return -Math.abs(target - subset.reduce((a, b) => a + b, 0));
}

function combinations(pool: number[], k: number): number[][] {
  const out: number[][] = [];
  const pick = (start: number, chosen: number[]) => {
    if (chosen.length === k) {
      out.push([...chosen]);
      return;
    }
    for (let i = start; i < pool.length; i++) {
      chosen.push(pool[i]);
      pick(i + 1, chosen);
      chosen.pop();
    }
  };
  pick(0, []);
  return out;
}

function generate(pool: number[], k: number, count: number): number[][] {
  return combinations(pool, k).slice(0, count);
}

function aggregate(a: number[], b: number[], target: number): number[] {
  const merged = [...new Set([...a, ...b])].sort((x, y) => x - y);
  let best = merged;
  let bestGap = Math.abs(target - merged.reduce((s, x) => s + x, 0));
  for (let size = 1; size <= merged.length; size++) {
    for (const combo of combinations(merged, size)) {
      const gap = Math.abs(target - combo.reduce((s, x) => s + x, 0));
      if (gap < bestGap) {
        bestGap = gap;
        best = combo;
      }
    }
  }
  return best;
}

function solve(pool: number[], target: number, refineRounds = 2): [Thought, ThoughtGraph] {
  const graph = new ThoughtGraph();
  const frontier = generate(pool, 3, 4).map((s) => graph.add(s, [], "generate"));

  for (let round = 0; round < refineRounds; round++) {
    frontier.sort((a, b) => score(b.subset, target) - score(a.subset, target));
    const top = frontier.slice(0, 2);
    if (top.length < 2) break;
    const merged = aggregate(top[0].subset, top[1].subset, target);
    frontier.push(graph.add(merged, [top[0].id, top[1].id], "aggregate"));
  }

  let best = [...graph.nodes.values()][0];
  for (const t of graph.nodes.values()) {
    if (score(t.subset, target) > score(best.subset, target)) best = t;
  }
  return [best, graph];
}

const pool = [2, 5, 9, 11, 14, 20];
const [best, graph] = solve(pool, 25);
console.log(
  `nodes=${graph.nodes.size} best_subset=[${best.subset}] ` +
    `sum=${best.subset.reduce((a, b) => a + b, 0)} op=${best.op} parents=[${best.parents}]`
);
```

The TypeScript sample compiles under `tsc --strict` and, run with `node`,
prints the same result as the Python sample, six nodes, best subset [5,20],
sum 25, op aggregate, parents [4,3].

```go
package main

import "fmt"

type Thought struct {
	id      int
	subset  []int
	parents []int
	op      string
}

type ThoughtGraph struct {
	nodes map[int]*Thought
	next  int
}

func newGraph() *ThoughtGraph {
	return &ThoughtGraph{nodes: map[int]*Thought{}, next: 1}
}

func (g *ThoughtGraph) add(subset []int, parents []int, op string) *Thought {
	t := &Thought{id: g.next, subset: subset, parents: parents, op: op}
	g.nodes[t.id] = t
	g.next++
	return t
}

func sum(xs []int) int {
	total := 0
	for _, x := range xs {
		total += x
	}
	return total
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

func score(subset []int, target int) int {
	return -abs(target - sum(subset))
}

func combinations(pool []int, k int) [][]int {
	var out [][]int
	var pick func(start int, chosen []int)
	pick = func(start int, chosen []int) {
		if len(chosen) == k {
			cp := append([]int(nil), chosen...)
			out = append(out, cp)
			return
		}
		for i := start; i < len(pool); i++ {
			pick(i+1, append(chosen, pool[i]))
		}
	}
	pick(0, []int{})
	return out
}

func generate(pool []int, k, count int) [][]int {
	combos := combinations(pool, k)
	if len(combos) > count {
		combos = combos[:count]
	}
	return combos
}

func aggregate(a, b []int, target int) []int {
	seen := map[int]bool{}
	var merged []int
	for _, x := range append(append([]int{}, a...), b...) {
		if !seen[x] {
			seen[x] = true
			merged = append(merged, x)
		}
	}
	best := merged
	bestGap := abs(target - sum(merged))
	n := len(merged)
	for size := 1; size <= n; size++ {
		for _, combo := range combinations(merged, size) {
			gap := abs(target - sum(combo))
			if gap < bestGap {
				bestGap = gap
				best = combo
			}
		}
	}
	return best
}

func solve(pool []int, target, refineRounds int) (*Thought, *ThoughtGraph) {
	graph := newGraph()
	var frontier []*Thought
	for _, s := range generate(pool, 3, 4) {
		frontier = append(frontier, graph.add(s, nil, "generate"))
	}

	for r := 0; r < refineRounds; r++ {
		if len(frontier) < 2 {
			break
		}
		best0, best1 := frontier[0], frontier[1]
		if score(best1.subset, target) > score(best0.subset, target) {
			best0, best1 = best1, best0
		}
		for _, t := range frontier[2:] {
			if score(t.subset, target) > score(best0.subset, target) {
				best0, best1 = t, best0
			} else if score(t.subset, target) > score(best1.subset, target) {
				best1 = t
			}
		}
		merged := aggregate(best0.subset, best1.subset, target)
		frontier = append(frontier, graph.add(merged, []int{best0.id, best1.id}, "aggregate"))
	}

	var best *Thought
	for _, t := range graph.nodes {
		if best == nil || score(t.subset, target) > score(best.subset, target) {
			best = t
		}
	}
	return best, graph
}

func main() {
	pool := []int{2, 5, 9, 11, 14, 20}
	best, graph := solve(pool, 25, 2)
	fmt.Printf("nodes=%d best_subset=%v sum=%d op=%s parents=%v\n",
		len(graph.nodes), best.subset, sum(best.subset), best.op, best.parents)
}
```

The Go sample passes `go vet` cleanly and, run with `go run`, prints the
same result, six nodes, best subset [5 20], sum 25, op aggregate, parents
[4 3].
