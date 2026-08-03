---
name: Least to Most
slug: least-to-most
family: 17-ai-agentic
category: AI and Agentic
aliases: [Least-to-Most Prompting, LtM, LtM Prompting, Decompose-then-Solve Prompting]
first_described: "Zhou, Schärli, Hou, Wei, Scales, Wang, Schuurmans, Cui, Bousquet, Le, Chi 2022"
maturity: established
related: [chain-of-thought, self-consistency, tree-of-thoughts, plan-execute, prompt-chaining, react, orchestrator-worker]
incompatible_with: []
verified: 2026-08-02
---

# Least to Most

## 1. Name, aliases, and lineage

The canonical name is Least-to-Most Prompting, commonly shortened to LtM. It
names a two-stage prompting strategy for large language models that first
breaks a hard problem into an ordered list of easier subproblems, from the
least demanding to the most demanding, and then answers each subproblem in
that order, feeding every prior question and answer into the prompt for the
next one.

The pattern was introduced in Denny Zhou, Nathanael Schärli, Le Hou, Jason
Wei, Nathan Scales, Xuezhi Wang, Dale Schuurmans, Claire Cui, Olivier
Bousquet, Quoc Le, and Ed Chi, "Least-to-Most Prompting Enables Complex
Reasoning in Large Language Models," submitted to arXiv on 21 May 2022 as
arXiv 2205.10625, with revisions carried through 16 April 2023
(https://arxiv.org/abs/2205.10625, verified 2026-08-02). The paper states its
central idea plainly, quoted directly from the abstract fetched at the URL
above. "The key idea in this strategy is to break down a complex problem into
a series of simpler subproblems and then solve them in sequence." All eleven
authors were, at the time of publication, affiliated with Google Research,
which places the paper alongside Chain-of-Thought prompting (Wei and
colleagues, discussed in dimension 2 below) as one of a cluster of prompting
papers that came out of the same lab in 2022.

No competing name has taken hold in the literature the way it has for some
other prompting techniques. Some secondary sources refer to it as
"decompose-then-solve prompting" as a descriptive paraphrase rather than a
name the original authors used, and this entry lists it as an alias only
because a reader may encounter that phrase in a survey paper and need to know
it points at the same technique. There is no evidence of a contested or
disputed origin here, unlike the near-simultaneous double discovery that
produced Tree of Thoughts a year later. Least-to-Most has one paper, one
author group, and one accepted account of where it came from.

The name itself is worth explaining because it is easy to misread. "Least to
most" does not describe the subproblems' topic order or their position in the
original sentence. It describes their difficulty order. The first subproblem
solved is the one requiring the least reasoning, and each subsequent
subproblem is at least as hard, usually strictly harder, than the one before
it, because each later subproblem is allowed to assume the answers already
produced. The name is a curriculum ordering claim, not a decomposition
strategy in itself, and the two are frequently confused by readers who see
only the words "least" and "most" without the difficulty framing behind them.

## 2. Problem and context

A single large language model call answers a question by producing one
continuous span of tokens, and that span has to carry the entire reasoning
chain the model needs to get the answer right, in the order the model
generates it, left to right, with no ability to revisit an earlier token and
correct it once later tokens have already committed to a path. Chain-of-Thought
prompting, described in Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten
Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc Le, and Denny Zhou, "Chain-of-Thought
Prompting Elicits Reasoning in Large Language Models," submitted 28 January
2022, arXiv 2201.11903 (https://arxiv.org/abs/2201.11903, verified 2026-08-02),
made single-call reasoning far stronger by asking the model to write out
intermediate steps instead of jumping straight to a final answer, and it
remains the load-bearing baseline every later reasoning-prompting paper is
measured against, including the paper this entry describes.

Chain-of-Thought has a limit, though, and the limit is set by how far the
easy examples shown in the prompt generalize to the hard problem actually
being asked. If the few-shot demonstrations in a Chain-of-Thought prompt show
three-step reasoning chains and the real question needs eight steps, the model
has no guarantee it will keep producing correct steps five, six, and seven, or
that it will stop generating and commit to an answer at the right point. This
is the specific failure the Least-to-Most paper targets, described directly
in its abstract, again from the same fetched source. The method "can
generalize to more difficult problems than those seen in the prompts," in
contrast to Chain-of-Thought where "the accuracy dramatically decreases as
the required number of reasoning steps increases."

The context in which Least-to-Most earns its complexity has three concrete
properties, each of which shows up repeatedly across the paper's benchmark
suite.

- **The problem is compositional.** It decomposes cleanly into an ordered
  chain of subproblems where each subproblem's correct answer is a genuine
  precondition for the next one. Arithmetic word problems, symbolic string
  manipulation, and compositional generalization tasks like the SCAN
  benchmark are the canonical examples.
- **The hardest test-time instances outstrip the few-shot demonstrations
  available.** A handful of easy worked examples in the prompt cannot, by
  themselves, teach a length-generalizing skill through Chain-of-Thought
  alone, because the model has never seen a demonstration that long. This is
  precisely the length-generalization gap the SCAN results in dimension 9
  below make numerically explicit.
- **Each subproblem is individually easy for the model, even when the whole
  problem is not.** Least-to-Most does not make the model smarter at any
  single reasoning step. It restructures a hard problem into a sequence of
  steps the model was already capable of, each solved with its own prior
  answers visible as scaffolding.

Outside that context, the extra API calls and the decomposition step buy
little. A single-hop factual question, a problem whose subproblems do not
have a natural dependency order, or a task where decomposition prompts do
not transfer across the domain, are all situations where the pattern's
overhead is not repaid, and dimension 4 makes the non-applicable cases
explicit.

## 3. Forces

This dimension states engineering judgement about which pressure the pattern
favours and which it costs, reasoned from the pattern's mechanics rather than
independently sourced.

- **Correctness on compositional, length-varying problems, favoured, at the
  cost of latency.** Splitting a problem into two or more sequential model
  calls multiplies wall-clock time by roughly the number of subproblems,
  because each solve step depends on the previous one's output and cannot
  start before it finishes. A single Chain-of-Thought call that would take
  two seconds becomes four sequential calls each taking two seconds, an
  eight-second total, for a problem the paper's own benchmarks show
  Chain-of-Thought getting materially wrong past a handful of steps. The
  trade is explicit. Pay more time to buy correctness on the instances that
  matter most, the hard tail of the distribution.
- **Interpretability, favoured, largely as a side effect.** Because each
  subquestion and its answer are separate, visible turns rather than buried
  inside one long generation, a person debugging a wrong final answer can
  see exactly which subquestion first went astray, in a way that is far
  harder to do from a single dense Chain-of-Thought paragraph where an error
  in step four of seven is easy to miss on a skim.
- **Prompt engineering effort and per-domain brittleness, cost, not
  favoured.** The paper's own limitations discussion is direct about this
  cost, stating that a decomposition prompt built for one problem domain does
  not carry over well to a different domain. A team adopting this pattern for
  a new task family should expect to author and tune a fresh decomposition
  demonstration set for that family, not reuse an arithmetic decomposition
  prompt for a symbolic manipulation task.
- **Token cost, cost, not favoured.** Every subsequent subproblem's prompt
  repeats the constant few-shot demonstrations plus every prior subquestion
  and its answer, so the total tokens processed across a k-step decomposition
  grow roughly quadratically in k for the accumulated history alone, on top
  of the constant demonstration cost paid k times over. A four-step
  decomposition can plausibly run three to five times the total token volume
  of a single Chain-of-Thought call on the same question, and this is the
  single most common reason teams reach for it selectively rather than as a
  default reasoning strategy.
- **Coupling between the decomposition step and the solving step, a real but
  manageable cost.** The two stages share no learned parameters and can, in
  principle, use two different models or two different prompt styles, but a
  bad decomposition irrecoverably caps everything that follows it, because
  the solving stage has no mechanism to notice the decomposition was wrong
  and go back to fix it. This one-directional dependency is a genuine
  architectural weakness the pattern accepts in exchange for its
  simplicity, and dimension 11 covers what it looks like when it breaks.

## 4. Applicability and non-applicability

Reach for Least-to-Most prompting when most of the following hold at once.

- The target problem decomposes into an ordered chain of subproblems where a
  later subproblem's correct solution genuinely depends on an earlier one's
  answer, not merely on the same topic.
- The hardest instances at test time require more reasoning steps, or a
  longer input, than the few-shot demonstrations available to show the model.
- Each individual subproblem, once isolated, is well within a single
  reasoning step or a short Chain-of-Thought chain for the model in use.
- The domain is stable enough, or important enough, to justify authoring and
  maintaining a dedicated decomposition prompt for it.
- Wrong final answers are expensive enough that the added latency and token
  cost of a multi-call pipeline is worth paying to raise accuracy on the hard
  tail of the input distribution.
- The task benefits from an auditable, per-step trace, for debugging,
  compliance, or explaining a result to a person who is not going to read a
  raw chain-of-thought paragraph.

Do NOT reach for it in the following situations, listed here with the reason
each one disqualifies the pattern, per the template's requirement that the
non-applicability list carry its own weight rather than restate the
applicability list in reverse.

- **The problem is a single fact lookup or a single-hop question with no
  internal dependency chain.** There is nothing to decompose, and forcing an
  artificial decomposition step only adds a model call and a chance for the
  decomposition itself to be wrong for no accuracy gain.
- **The subproblems do not have a genuine dependency order.** If subquestion
  two does not actually need subquestion one's answer, the sequencing buys
  nothing and a simple parallel decomposition, closer to the orchestrator
  worker pattern, is both faster and easier to reason about, because the
  independent subtasks can run concurrently instead of waiting on each other.
- **Latency is on the critical path of an interactive experience and cannot
  absorb k sequential model calls.** A user-facing autocomplete or a
  low-latency voice assistant turn cannot usually afford a four-step
  sequential pipeline where a single well-crafted Chain-of-Thought or
  few-shot prompt gets acceptable accuracy in one call.
- **The team cannot invest in a domain-specific decomposition prompt.** The
  paper's own limitations discussion states that decomposition prompts do
  not carry over well from one problem domain to another. Applying an
  arithmetic decomposition prompt to a legal reasoning task, unmodified, is
  a known failure shape, not a hypothetical one.
- **The underlying model is weak enough that even the individual subproblems
  are unreliable.** Least-to-Most does not add reasoning capability the base
  model lacks. It restructures existing capability. If a model gets simple
  arithmetic wrong in isolation, chaining four of those calls together
  compounds the error rate rather than fixing it.
- **The task is naturally iterative and re-plannable rather than strictly
  compositional**, for example an agent that needs to observe an environment
  and change its plan based on what it finds. That shape is closer to the
  ReAct or Plan-and-Execute patterns, which interleave acting and observing,
  than to Least-to-Most's fixed, precomputed subquestion list.

## 5. Structure

Least-to-Most has three participants, and the paper's own description of the
two stages maps directly onto them.

- **The Decomposer.** A single language-model call, guided by a small,
  fixed set of few-shot demonstrations that show how to break a problem of
  the target type into an ordered list of subquestions. Given the original
  question, it returns an ordered list of subquestions, and only that list.
  It never attempts to answer any of them.
- **The Solver.** A language-model call invoked once per subquestion, in
  the Decomposer's stated order. Each invocation receives a prompt built
  from three parts, matched directly to the paper's own description
  verified in dimension 9. Constant few-shot solving demonstrations, a
  potentially empty list of previously answered subquestions paired with
  the answers already generated for them, and the current subquestion to
  answer. The Solver produces one answer per call and appends it, together
  with its subquestion, to the running history the next Solver call will see.
- **The Trace, or running history.** The accumulating record of
  subquestion-answer pairs, in order. It is not a separate model call, but
  it is a first-class structural element, because it is the mechanism that
  actually carries the least-to-most ordering forward. Without it, each
  Solver call would be an independent, context-free answer to an isolated
  subquestion, and the "solve them in sequence" claim in the paper's
  abstract would have no teeth.

The Decomposer and the Solver can be the same underlying model with two
different prompt templates, and in the original paper's main experiments
they are, both built on OpenAI's code-davinci-002. Nothing in the pattern's
structure requires this. A production implementation is free to route the
decomposition call to a cheaper or faster model, since decomposing a problem
into subquestions is, in practice, an easier task than solving the hardest
of those subquestions, and to reserve a stronger model for the Solver's
later, harder calls.

## 6. ASCII structure diagram

```text
+----------------------------------------------------------------+
|                        Least-to-Most                            |
+----------------------------------------------------------------+

  Original question
       |
       v
  +-----------------+     few-shot decomposition
  |   Decomposer    | <-- demonstrations (constant,
  |  (one LLM call) |     domain-specific prompt)
  +-----------------+
       |
       | ordered subquestion list
       | [q1, q2, ..., qk]  (least demanding first)
       v
  +------------------------------------------------------+
  |                       Trace                            |
  |  (empty at start, grows one pair per Solver call)      |
  +------------------------------------------------------+
       |
       v
  +-----------------+   few-shot solving demonstrations
  |     Solver      | + Trace so far (q1..qi-1, a1..ai-1)
  |  (call i of k)  | + current subquestion qi
  +-----------------+
       |
       | answer ai
       v
  append (qi, ai) to Trace  -----> loop back to Solver for qi+1
       |
       | after qk is answered
       v
  final answer = ak  (or a designated final subquestion's answer)
```

## 7. Dynamics

```text
Sequence for a 3-subproblem decomposition, time flowing downward.

Caller               Decomposer               Solver                Trace
  |                       |                       |                    |
  |-- original question ->|                       |                    |
  |                       |                       |                    |
  |<-- [q1, q2, q3] ------|                       |                    |
  |                       |                       |                    |
  |----------------------------- solve q1 -------->|                    |
  |                       |               (demos + q1, no history)     |
  |<---------------------------------------------- a1 --------------- |
  |                                                                     |
  |                                                append (q1, a1) --->|
  |                                                                     |
  |----------------------------- solve q2 -------->|                    |
  |                       |               (demos + q1,a1 + q2)         |
  |<---------------------------------------------- a2 --------------- |
  |                                                                     |
  |                                                append (q2, a2) --->|
  |                                                                     |
  |----------------------------- solve q3 -------->|                    |
  |                       |               (demos + q1,a1,q2,a2 + q3)   |
  |<---------------------------------------------- a3 --------------- |
  |                                                                     |
  |<================ final answer = a3 (or derived from it) ==========|

Key property: solving qi never begins until (q1,a1) .. (qi-1,ai-1) exist.
The chain is strictly sequential. There is no branching and no backtracking
in the base pattern. A failure at step i propagates unmodified into every
later prompt, because the Solver has no way to detect that ai is wrong.
```

## 8. Implementation variants

- **Two-prompt, single model, as in the original paper.** One prompt
  template for decomposition, one for solving, both served by the same
  model. This is the variant benchmarked in the source paper across
  code-davinci-002, text-davinci-002, and code-davinci-001, and it is the
  simplest correct implementation to start from.
- **Fixed-cost final-answer extraction.** Some implementations treat the
  last subquestion's answer as the final answer directly, matching the
  paper's own SCAN and last-letter-concatenation experiments where the final
  subquestion is deliberately constructed to equal the original question.
  Others add a dedicated final "answer synthesis" call that reads the whole
  trace and produces a final answer distinct from any single subanswer, which
  is useful when the original question does not map cleanly onto the final
  subquestion in the decomposition, for example a question asking for a
  count or a comparison across several of the earlier subanswers.
- **Model-split decomposition and solving.** Route the Decomposer call to a
  smaller or cheaper model and reserve a larger model for the Solver calls,
  since decomposition is, in practice, an easier task than solving the
  hardest subproblem in the chain. This is not benchmarked in the original
  paper, which used one model throughout, but it follows directly from
  treating Decomposer and Solver as structurally independent participants,
  per dimension 5, and it is the natural cost-optimization move once a team
  productionizes the pattern.
- **Trained decomposer instead of a prompted one.** Dheeru Dua, Shivanshu
  Gupta, Sameer Singh, and Matt Gardner, "Successive Prompting for
  Decomposing Complex Questions," Proceedings of the 2022 Conference on
  Empirical Methods in Natural Language Processing, pages 1251 through 1265
  (https://aclanthology.org/2022.emnlp-main.81/, verified 2026-08-02),
  independently arrive at the same iterative decompose-then-solve shape but
  train a dedicated question-decomposition model rather than relying on
  few-shot prompting for that stage, and interleave decomposition and
  solving one step at a time rather than decomposing the entire chain up
  front. This is a genuine structural variant, not a mere reimplementation,
  because it removes the one-shot, all-at-once decomposition step that the
  original Least-to-Most structure treats as a single call.
- **Modular, tool-augmented subquestion solving.** Tushar Khot, Harsh
  Trivedi, Matthew Finlayson, Yao Fu, Kyle Richardson, Peter Clark, and
  Ashish Sabharwal, "Decomposed Prompting. A Modular Approach for Solving
  Complex Tasks," submitted 5 October 2022, arXiv 2210.02406
  (https://arxiv.org/abs/2210.02406, verified 2026-08-02), generalize the
  same decompose-then-solve shape so that each subtask is handled by its own
  dedicated sub-prompt, and any of those sub-prompts can in turn be a
  symbolic function, a retrieval call, or a further recursive decomposition
  rather than always another plain LLM call. This variant matters for
  production systems because it is the natural bridge between Least-to-Most
  and tool-using agent patterns, letting a "subquestion" resolve to a
  calculator call or a database query instead of another generation.
- **Recursive, tree-shaped decomposition.** Where a subquestion is itself
  compositional, some implementations allow the Decomposer to be invoked
  recursively on that subquestion rather than requiring a single flat list
  up front. This trades the pattern's strict linear chain, shown in
  dimension 7, for a tree, and moves the implementation toward the
  structural territory of Tree of Thoughts, though without that pattern's
  explicit search-and-backtrack machinery.

## 9. Known production uses

- **The original evaluation itself, run against a production language-model
  API, over the full published benchmark suite.** The source paper's
  headline results, all quoted directly from the fetched abstract and paper
  text and re-checked against https://arxiv.org/abs/2205.10625, verified
  2026-08-02, are the clearest demonstration that this is a technique
  deployed against a real, publicly served model rather than a purely
  theoretical proposal. On the SCAN length-generalization split, GPT-3's
  code-davinci-002 model reaches "at least 99% accuracy" using 14
  exemplars, against 16 percent accuracy for Chain-of-Thought prompting on
  the same split, and the paper is explicit that specialized
  neural-symbolic architectures previously needed more than 15,000 training
  examples to reach comparable performance on that benchmark. On GSM8K
  grade-school math word problems, code-davinci-002 with Least-to-Most
  reaches 62.39 percent overall accuracy against 60.87 percent for
  Chain-of-Thought, and the gap widens specifically on the harder subset of
  problems requiring five or more reasoning steps, 45.23 percent against
  39.07 percent. On the DROP reading-comprehension benchmark's non-football
  subset, it reaches 82.45 percent, and on a synthetic
  last-letter-concatenation task at length 12, it reaches 74.0 percent
  against 31.8 percent for Chain-of-Thought.
- **Decomposed Prompting, ICLR 2023, Allen Institute for AI, open source
  release.** Khot and colleagues, cited fully in dimension 8, built a
  modular decompose-then-solve architecture in the same family and shipped
  it as the `DecomP` project on GitHub at
  https://github.com/allenai/DecomP, verified 2026-08-02, carrying
  approximately 100 stars at the time of this verification. The repository
  ships working code for letter concatenation, list reversal, CommaQA, and
  multi-hop open-domain question answering, each implemented as a library
  of dedicated sub-prompts orchestrated by a controller, which is the same
  decompose-then-sequentially-solve shape as Least-to-Most generalized into
  a reusable, extensible library rather than a fixed two-stage pipeline.
- **Successive Prompting, EMNLP 2022, Allen Institute for AI and University
  of Pennsylvania.** Dua and colleagues, cited fully in dimension 8, built
  and evaluated a system on the DROP multi-hop question-answering benchmark
  that decouples question decomposition from answer generation into two
  separately trainable components and iterates them one step at a time,
  reporting an improvement of approximately five F1 points over comparable
  baselines on DROP, per the paper's own abstract fetched from
  https://aclanthology.org/2022.emnlp-main.81/, verified 2026-08-02. The
  paper arrives at this design independently rather than citing the
  Least-to-Most paper directly, which this entry states honestly rather
  than overstating a lineage the paper itself does not assert. What it does
  demonstrate, with a real named academic system and a measured benchmark
  result, is that the same decompose-and-solve-in-sequence architecture was
  found valuable enough to be reinvented and deployed against a standard
  benchmark independently within the same publication year.

A note on absence, in the interest of the entry's own honesty standard.
Unlike Tree of Thoughts, which has a maintained integration inside the
`langchain-experimental` package described in that entry, this author found
no equivalent named, general-purpose open source library that ships
"Least-to-Most" as an off-the-shelf, install-and-call chain under that name.
The technique's core idea, decompose a hard problem into an ordered sequence
of easier subproblems solved with growing context, appears to have been
absorbed into the broader, less specifically named vocabulary of "task
decomposition" and "planning" used by general agent frameworks, rather than
staying attached to the paper's original name as a distinct, branded library
component the way ReAct-style tool calling has. This is itself a useful,
honest data point about the pattern's maturity level. established and
well-cited in research, but not standardized as a single reusable
off-the-shelf software component the way some sibling patterns in this
family are.

## 10. Consequences

Positive.

- Materially higher accuracy on problems whose hardest test-time instances
  exceed the reasoning length shown in the few-shot demonstrations, with the
  SCAN, GSM8K, and last-letter-concatenation results in dimension 9 as
  concrete, sourced evidence rather than an assumed benefit.
- A per-step, auditable trace of subquestions and their answers, which
  makes it possible to locate exactly where a wrong final answer first went
  wrong, rather than searching a single dense paragraph for the mistaken
  step.
- Graceful decoupling of decomposition and solving, letting an
  implementation route each stage to a different model, prompt style, or
  even a non-LLM tool, per the modular variant described in dimension 8.
- A structure that composes cleanly with retrieval and tool use, because
  each Solver call is just another prompt that can, in a straightforward
  extension, be given access to a calculator, a search index, or a database
  query rather than being restricted to pure generation.

Negative.

- Latency scales with the number of subproblems, because each Solver call
  strictly depends on the previous one's output and the calls cannot be
  parallelized, unlike genuinely independent subtasks in an
  orchestrator-worker split.
- Token cost per solved problem is materially higher than a single
  Chain-of-Thought call, because the constant few-shot demonstrations and
  the growing subquestion-answer history are both repeated in full on every
  Solver call.
- The Decomposer is a single point of failure with no self-correction
  mechanism inside the base pattern. A wrong or incomplete subquestion list
  caps the correctness of everything downstream, and the Solver stage has
  no visibility into whether the decomposition itself was sound.
- Decomposition prompts are domain-specific and do not carry over well from
  one problem domain to another, a limitation the source paper states
  directly, which means adopting this pattern for a new task family carries
  a real, recurring authoring cost rather than a one-time setup cost.

## 11. Failure modes and misuse

Each entry below follows the symptom, cause, fix shape required by the
template, with the symptom stated as something an engineer would actually
observe while debugging a run, not the abstract underlying mistake alone.

- **Symptom.** The final answer is confidently wrong, and every individual
  subquestion in the trace, read in isolation, looks like it was answered
  correctly. **Cause.** The Decomposer produced a subquestion list that
  omits a genuinely necessary subproblem, or orders two subproblems
  incorrectly so that a later one is asked before the fact it depends on
  has actually been established, and the Solver, having no way to detect a
  missing precondition, answers the malformed subquestion as best it can
  using whatever partial context is available. **Fix.** Add an explicit
  decomposition-validation step, either a second model call that checks
  the subquestion list against the original question before any Solver
  call runs, or a small set of structural assertions, for example
  confirming that the final subquestion's wording plausibly maps back onto
  the original question, before spending the sequential Solver budget on a
  decomposition that was never going to reach the right answer.
- **Symptom.** Accuracy on a new task domain is far below the numbers
  reported for arithmetic or symbolic-manipulation tasks, even though the
  same prompt template structure was reused. **Cause.** The decomposition
  few-shot demonstrations were carried over from a different domain without
  being rewritten for the new one, which is exactly the transfer failure
  the source paper names directly in its limitations discussion, stating
  that a decomposition prompt built for one domain does not carry over well
  to another. **Fix.** Author a fresh, small set of decomposition
  demonstrations specific to the new domain rather than reusing an existing
  set, treating decomposition-prompt authoring as a per-domain cost the
  same way a team would treat writing new Chain-of-Thought exemplars for a
  new task.
- **Symptom.** A specific class of question reliably produces a trace with
  a plausible-looking numeric answer that is off by a small, consistent
  amount, for example one extra or one missing character in a concatenation
  task. **Cause.** This matches the specific failure mode the source paper
  itself reports for its last-letter-concatenation experiments, where
  concatenation errors, dropping or adding a letter, make up most of the
  observed failures, rather than the model failing to identify the correct
  letters to concatenate in the first place. In practice this class of
  error tends to be a Solver-stage generation slip on a mechanical,
  low-level subtask, not a decomposition-stage reasoning failure. **Fix.**
  Isolate the mechanical subtask, string concatenation, arithmetic, unit
  conversion, and route it to a deterministic tool call inside the Solver
  step rather than free-form generation, following the modular,
  tool-augmented variant described in dimension 8, since a calculator or a
  string operation does not make the kind of off-by-one slip a language
  model occasionally does.
- **Symptom.** The pipeline works correctly on the demonstrated examples
  during development, then degrades sharply once real user questions start
  arriving that involve idiomatic or figurative phrasing. **Cause.** This
  matches a failure the source paper's own SCAN error analysis calls out
  directly, misreading the word "twice" or "thrice" when it appears after
  "around," and confusing "after" with "and" in compositional instructions,
  both of which are decomposition-stage misreadings of the original
  question's structure rather than solving-stage errors. **Fix.** Expand
  the decomposition few-shot set to include the specific idiomatic or
  ambiguous phrasings observed in production traffic, since this is a
  prompt-coverage gap in the Decomposer's demonstrations rather than a
  capability limit, and the fix is closer to targeted prompt-example
  authoring than to a structural change in the pattern.
- **Symptom.** The system is technically correct on every benchmark
  question tried, but the team is surprised by how slow and expensive it
  is once real traffic volume arrives, and starts asking whether the
  pattern was the right choice at all. **Cause.** This is a misuse of the
  pattern rather than a defect in it, applying Least-to-Most as a default
  reasoning strategy for every incoming question instead of routing only
  the genuinely compositional, hard-tail questions through it, which is the
  exact overhead cost named as a negative consequence in dimension 10.
  **Fix.** Add a lightweight upstream classifier or a simple heuristic,
  question length, presence of multiple clauses, detected arithmetic or
  multi-hop structure, that routes only the subset of questions likely to
  benefit through the full decompose-then-solve pipeline, and answers the
  remainder with a single cheaper call, following the same routing
  discipline described in this family's own routing pattern.

## 12. Trade-off matrix

Compared against three named alternatives from this same pattern family, on
the forces named in dimension 3. Ratings are relative within this table, not
absolute scores.

| Force | Least-to-Most | Chain-of-Thought (single call) | Tree of Thoughts | Successive Prompting (Dua et al. 2022) |
|---|---|---|---|---|
| Accuracy on long, compositional reasoning chains beyond the demonstrated length | High, this is the pattern's specific reported strength | Degrades sharply past the demonstrated chain length, per the paper's own comparison numbers in dimension 9 | High, but via branching search rather than curriculum ordering, at materially higher per-call cost | High, comparable design, with the decomposition step trained rather than prompted |
| Latency per solved problem | Multiplied by number of subproblems, strictly sequential | Lowest, one call | Highest of the four, multiple candidate branches evaluated per step | Similar to Least-to-Most, sequential, but with a lighter trained decomposer call |
| Token cost per solved problem | High, repeats growing history each call | Lowest | Highest, evaluates multiple candidates per node | Comparable to Least-to-Most |
| Interpretability of the reasoning trace | High, discrete subquestion and answer pairs | Lower, one dense generated block | High, but the full search tree can be large to review by hand | High, similar discrete trace |
| Engineering cost to adopt for a new domain | Requires authoring domain-specific decomposition demonstrations | Requires only reasoning demonstrations, generally cheaper to author | Requires an evaluator function or evaluator prompt in addition to generation, generally the most setup work of the four | Requires training or fine-tuning a decomposition component, the highest fixed cost of the four but the lowest per-query prompt-engineering cost |
| Resilience to a single bad reasoning step | Low, an early wrong subanswer propagates unmodified downstream, per dimension 11 | Low, an early wrong token in the chain can derail everything after it | Higher, a search-and-evaluate loop can discard a bad branch and try another | Low to moderate, similar propagation risk as Least-to-Most, mitigated somewhat by the trained decomposer being more consistent than a prompted one |
| Best fit | Fixed, precomputable, strictly ordered subproblem chains | Simple to moderately complex single-hop or short-chain reasoning | Problems with multiple plausible solution paths where backtracking has real value | Multi-hop question answering at scale, where training data for a decomposer is available |

## 13. Related and incompatible patterns

- **Chain-of-Thought (this family).** Least-to-Most is best understood as
  Chain-of-Thought's answer to the length-generalization gap. Every Solver
  call inside a Least-to-Most pipeline can itself use Chain-of-Thought
  reasoning to answer its one subquestion, which means the two patterns
  compose rather than compete. Chain-of-Thought is the reasoning mechanism
  inside a single step. Least-to-Most is the control structure across
  steps.
- **Self-Consistency (this family).** Because each Solver call is a single
  model generation, it is subject to the same sampling variance any single
  LLM call has. Self-Consistency's majority-vote-over-samples idea applies
  cleanly at the level of an individual subquestion, sampling several
  candidate answers to a hard subquestion and taking the majority before
  appending it to the trace, which raises the reliability of the weakest
  link in the chain named in dimension 11 without changing the overall
  decompose-then-solve structure.
- **Tree of Thoughts (this family).** Both patterns break a hard problem
  into smaller pieces, but they diverge sharply on structure. Least-to-Most
  commits to one flat, linear, precomputed subquestion order and never
  revisits it. Tree of Thoughts explores multiple candidate continuations
  at each step and can backtrack away from ones that look unpromising.
  Where a problem's decomposition is genuinely ambiguous or benefits from
  exploring more than one ordering, Tree of Thoughts is the pattern to
  reach for instead, and the recursive decomposition variant in dimension
  8 is the natural bridge between the two.
- **Decomposed Prompting and Successive Prompting (both discussed in full
  in dimensions 8 and 9).** These are direct structural siblings, sharing
  the decompose-then-solve shape while varying how the decomposition step
  itself is produced, prompted versus trained, and whether it is a single
  upfront call or interleaved one step at a time with solving.
- **Plan-and-Execute and Orchestrator-Worker (this family).** These share
  the general shape of breaking a task into pieces handled by separate
  calls, but they typically assume independence or loose coupling between
  subtasks, letting them run in parallel. Least-to-Most's defining feature
  is exactly the opposite, a strict sequential dependency where each step
  needs the previous step's answer, which is why the two patterns are
  related rather than interchangeable, and why forcing an independent-task
  decomposition into a Least-to-Most-style sequential pipeline, or the
  reverse, is a structural mismatch rather than a stylistic choice.
- **Retrieval-Augmented Generation (this family).** RAG solves a different
  problem, supplying external factual context to a single generation call,
  and is compatible with Least-to-Most rather than competing with it. A
  Solver call answering a factual subquestion can itself be RAG-backed, an
  explicit combination the modular variant in dimension 8 makes natural.
- **Incompatible with nothing in a hard sense.** There is no pattern in
  this family this entry treats as structurally incompatible with
  Least-to-Most, because the pattern is a control-flow shape around
  ordinary model calls, and any pattern that governs the content of a
  single call, retrieval, tool use, self-consistency sampling, can be
  nested inside a Solver step without contradiction. The `incompatible_with`
  frontmatter field is left empty for this reason.

## 14. Refactoring path in and out

Introducing Least-to-Most into a system that currently answers a class of
question with a single Chain-of-Thought call.

1. Collect a sample of the hardest real failures the single-call system
   currently produces, and confirm, by hand, that the errors follow the
   shape named in dimension 2, correct handling of short chains, degrading
   accuracy as the required chain length grows past what the demonstrations
   show. If the failures are not shaped this way, stop here, per the
   non-applicability list in dimension 4, because introducing this pattern
   will not address the actual problem.
2. Author a small decomposition few-shot set, three to five worked examples
   showing the target question type broken into an ordered subquestion
   list, following the paper's own two-part prompt shape, demonstrations
   followed by the target question.
3. Author a matching solving few-shot set, showing how a subquestion is
   answered given a, possibly empty, history of prior subquestions and
   answers, matching the three-part prompt shape verified in dimension 9,
   demonstrations, prior history, current subquestion.
4. Wire the Decomposer call, feeding it the original question and returning
   the ordered subquestion list, with a hard fallback to the existing
   single-call path if the Decomposer's output cannot be parsed into a
   well-formed list, so a malformed decomposition degrades gracefully
   instead of feeding garbage into the sequential Solver loop.
5. Wire the Solver loop, appending each subquestion-answer pair to the
   running trace before the next call, exactly as shown in the dynamics
   diagram in dimension 7.
6. Run the new pipeline against the same hard-failure sample collected in
   step 1, and confirm the specific failures that motivated the change are
   now resolved, before rolling the change out more broadly. Measure token
   and latency cost against the single-call baseline at the same time, so
   the accuracy gain is weighed against its real, quantified cost rather
   than assumed to be free.
7. Add the routing heuristic described in dimension 11's last failure mode
   before the change reaches full production traffic, so only the subset
   of questions likely to be compositional and hard-tail actually pay the
   pattern's overhead.

Removing Least-to-Most once it stops earning its place, for example after a
newer base model closes the length-generalization gap that motivated the
adoption in the first place.

1. Confirm the removal candidate empirically rather than by assumption. Run
   the same hard-failure sample from step 1 above through a single-call
   Chain-of-Thought prompt on the current model, and check whether the gap
   that originally justified the multi-step pipeline has actually narrowed.
2. If it has, replace the Decomposer-plus-Solver-loop call sequence with a
   single Chain-of-Thought call using the solving few-shot demonstrations,
   adapted to show the full reasoning inline rather than split across
   subquestions.
3. Keep the decomposition and solving prompt sets in version control even
   after removal, rather than deleting them, since a future model
   regression or a shift to a harder problem distribution may make the
   pattern worth reintroducing, and rebuilding a domain-specific
   decomposition prompt from nothing is the single largest cost named in
   dimension 10.
4. Re-run the full hard-failure sample after removal as a regression check,
   not just the subset expected to improve, since removing the sequential
   structure can reintroduce failures on cases the team has stopped
   actively watching for.

## 15. Testing and verification

Testing a Least-to-Most pipeline is testing two separable components plus
their composition, and each deserves its own test strategy rather than only
end-to-end assertions on the final answer.

- **Test the Decomposer in isolation.** Give it a fixed set of known
  questions and assert properties of the returned subquestion list rather
  than a single golden list, since two differently ordered but logically
  equivalent decompositions can both be correct. Useful properties to
  assert include that the list is non-empty, that no subquestion is
  identical to the original question except possibly the last one, and
  that the subquestions, read in order, plausibly build toward the
  original question, checked either by a rule-based heuristic for a narrow
  domain or by a separate model-graded check for a broader one.
- **Test the Solver in isolation, with synthetic history.** Because the
  Solver's prompt is built from three explicit parts, demonstrations,
  history, current subquestion, per dimension 5, it is straightforward to
  unit-test with a hand-constructed history rather than requiring a real
  Decomposer call first. This is the technique used in the runnable code
  samples in this entry, where `solveStub` and its Go and Python
  counterparts are exercised directly against a fixed, known trace prefix,
  and it lets a test suite check that the Solver correctly refuses to
  answer a subquestion whose precondition is not yet present in the
  history, the exact defect named in dimension 11's first failure mode.
- **Test double for the Solver stage.** When testing code that consumes
  the Solver's output, for example the code that appends to the trace and
  decides when the chain is complete, replace the real model-backed Solver
  with a deterministic stub that returns a scripted answer for a known
  subquestion, exactly as the code samples in dimension 8 already do,
  rather than letting a real, non-deterministic model call sit inside a
  unit test.
- **Golden-trace regression tests.** Maintain a small, hand-verified set of
  full traces, original question, expected subquestion list, expected
  answer at each step, and the expected final answer, and run the full
  pipeline against them on every change to either prompt template. This is
  the most direct analogue, inside a test suite, to the paper's own
  benchmark evaluation methodology, and it is the test class most likely to
  catch a prompt-template edit that silently degrades a domain the team is
  not actively watching.
- **Adversarial coverage for the transfer failure named in dimension 11.**
  Deliberately include a handful of idiomatic or ambiguous phrasings, "how
  many apples in total, twice as many as she started with," in the golden
  trace set, since the source paper's own SCAN error analysis names exactly
  this class of phrasing as a recurring decomposition-stage error, and a
  test suite that never exercises it will not catch a regression on it.
- **Cost and latency budget assertions, not only correctness.** Given the
  real, quantified cost named in dimension 10, a test or a lightweight
  production check that asserts the total token count or call count for a
  representative trace stays within a set budget catches a silent
  regression, for example a prompt-template edit that accidentally starts
  including a fourth few-shot demonstration on every Solver call, before
  it shows up as a surprise cost line item.

## 16. Observability signals

- **Per-stage latency, split by Decomposer and each Solver call.** A
  healthy pipeline shows the Decomposer call taking a roughly constant
  time regardless of the question, and each Solver call taking a time
  proportional to how far along the trace it is, since later calls carry
  more history tokens. A pipeline where Solver call latency is flat
  regardless of position in the chain is a sign the history is not
  actually being appended and passed forward, silently degrading the
  pattern into k independent, context-free calls, which is a serious
  correctness bug rather than only a performance concern.
- **Subquestion count distribution.** Track the distribution of how many
  subquestions the Decomposer produces per real question. A healthy
  distribution is stable and matches the shape of the underlying problem
  domain. A sudden shift toward very long subquestion lists is a sign the
  Decomposer is either over-decomposing simple questions, driving up cost
  for no accuracy benefit, or is starting to loop, and a shift toward very
  short lists on questions the team knows to be compositional is a sign
  the domain-specific decomposition demonstrations have drifted out of
  coverage, the same failure named in dimension 11.
- **Per-step disagreement rate under Self-Consistency sampling.** For teams
  that combine this pattern with Self-Consistency at the Solver stage, per
  dimension 13, track how often the sampled answers to a given subquestion
  disagree with each other. A subquestion position in the chain with a
  persistently high disagreement rate is a strong, cheap signal pointing
  at exactly which step in the decomposition is the weak link, without
  needing to inspect individual traces by hand.
- **Trace-level error attribution.** Because the pattern produces a
  discrete, per-step trace rather than one dense generation, log the full
  trace, not just the final answer, and build tooling that lets an
  engineer or an automated evaluator mark which specific subquestion first
  went wrong on a failed final answer. Aggregating this attribution over
  time is the most direct way to see whether failures cluster at the
  Decomposer stage, per the first failure mode in dimension 11, or at a
  specific position in the Solver chain, per the third and fourth failure
  modes.
- **Total token cost per solved problem, tracked against the single-call
  baseline it replaced.** Since dimension 10 names token cost as the
  pattern's most direct and unavoidable negative consequence, a dashboard
  that tracks this ratio over time is the concrete instrument that answers
  the misuse question named in dimension 11's last failure mode, whether
  the pattern is still earning back its overhead on the traffic it is
  actually being applied to.

## 17. Security and privacy implications

The Decomposer and every Solver call are, individually, ordinary language
model calls, so the pattern inherits the standard prompt-injection and data
handling considerations of any LLM pipeline rather than introducing an
entirely new attack class of its own. Two implications are specific enough
to this pattern's structure to name directly, stated here as engineering
analysis rather than as sourced claims, per the template's guidance on
judgement in this dimension.

- **The growing trace is a growing attack surface for prompt injection.**
  Because every Solver call includes the full accumulated history of prior
  subquestions and answers, per dimension 5, any untrusted content that
  makes its way into an earlier subanswer, for example if a subquestion is
  answered using retrieved external text rather than pure model reasoning,
  is carried forward, verbatim, into every subsequent Solver prompt for the
  rest of the chain. This is a materially larger injected-content surface
  than a single-call pattern has, and a system that combines Least-to-Most
  with retrieval, per the composition noted in dimension 13, should treat
  each retrieved subanswer as untrusted input requiring the same sanitizing
  discipline any RAG pipeline applies, rather than exempting it because it
  is one step among several in a larger chain.
- **The trace is a sensitive audit log by construction.** The same
  interpretability property named as a positive consequence in dimension
  10, a discrete, readable record of every subquestion and answer, means
  that logging a full trace for observability, per dimension 16, is also
  logging a detailed record of exactly how a person's original question
  was reasoned about, step by step. Where the original question contains
  personal or sensitive information, that information is now duplicated
  across every subsequent Solver prompt in the trace and potentially across
  every logged step, not just the single original input, which is a real
  and specific data-minimization concern this pattern's structure
  introduces relative to a single-call baseline, and it should factor into
  retention policy for any logged traces.

Neither implication is unique to this pattern in kind, prompt injection and
log retention are general LLM system concerns, but both are larger in
degree, for this pattern than for a single-call baseline, because of the
pattern's defining structural feature, an accumulating, sequentially
propagated history, and a team adopting this pattern should budget review
time for both rather than assuming the pattern's simplicity implies a
correspondingly simple security posture.

## 18. References

- Denny Zhou, Nathanael Schärli, Le Hou, Jason Wei, Nathan Scales, Xuezhi
  Wang, Dale Schuurmans, Claire Cui, Olivier Bousquet, Quoc Le, and Ed Chi,
  "Least-to-Most Prompting Enables Complex Reasoning in Large Language
  Models," arXiv 2205.10625, submitted 21 May 2022, revised through 16
  April 2023, https://arxiv.org/abs/2205.10625, verified 2026-08-02.
- Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei
  Xia, Ed Chi, Quoc Le, and Denny Zhou, "Chain-of-Thought Prompting Elicits
  Reasoning in Large Language Models," arXiv 2201.11903, submitted 28
  January 2022, https://arxiv.org/abs/2201.11903, verified 2026-08-02.
- Tushar Khot, Harsh Trivedi, Matthew Finlayson, Yao Fu, Kyle Richardson,
  Peter Clark, and Ashish Sabharwal, "Decomposed Prompting. A Modular
  Approach for Solving Complex Tasks," arXiv 2210.02406, submitted 5
  October 2022, revised through 11 April 2023,
  https://arxiv.org/abs/2210.02406, verified 2026-08-02.
- Allen Institute for AI, `DecomP` reference implementation, GitHub
  repository, https://github.com/allenai/DecomP, verified 2026-08-02,
  approximately 100 stars at time of verification.
- Dheeru Dua, Shivanshu Gupta, Sameer Singh, and Matt Gardner, "Successive
  Prompting for Decomposing Complex Questions," Proceedings of the 2022
  Conference on Empirical Methods in Natural Language Processing, pages
  1251 through 1265, https://aclanthology.org/2022.emnlp-main.81/, verified
  2026-08-02.
- Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L. Griffiths,
  Yuan Cao, and Karthik Narasimhan, "Tree of Thoughts. Deliberate Problem
  Solving with Large Language Models," arXiv 2305.10601, submitted 17 May
  2023, https://arxiv.org/abs/2305.10601, verified 2026-08-02, cross
  referenced against this repository's own `tree-of-thoughts.md` entry for
  the trade-off comparison in dimension 12.

## Code examples

Three runnable implementations follow the same worked example, a compositional
arithmetic word problem, "Amy has 3 baskets of 4 apples each. She gives away
5 apples. How many apples does she have left?" decomposed into two ordered
subquestions. In each language, `decompose` returns the fixed subquestion
list for this question, and `solveStub` stands in for a real language-model
Solver call, implemented as a small deterministic rule set instead of a live
API call, so the sample compiles and runs without network access or an API
key while still exercising the pattern's real structural property, that the
second subquestion's solver refuses to run until the first subquestion's
answer is present in the trace, exactly the precondition-checking behaviour
named as the fix for the first failure mode in dimension 11. Python,
TypeScript, and Go are used because they are the three languages in this
repository's available toolchain where the pattern's control flow, an
ordered list of calls threading a growing history forward, is written the
same direct, imperative way a production LLM orchestration layer would
write it. Swift, Java, and Rust are not included here because none of them
would show a different structural idiom for this specific pattern beyond
syntax, and three languages already carry the point being made, that this
is a plain control-flow shape rather than a language-specific idiom.

```python
from dataclasses import dataclass, field


@dataclass
class SubStep:
    question: str
    answer: str


@dataclass
class Trace:
    steps: list = field(default_factory=list)

    def render_prefix(self):
        lines = []
        for step in self.steps:
            lines.append(f"Q: {step.question}")
            lines.append(f"A: {step.answer}")
        return "\n".join(lines)


def decompose(question):
    target = (
        "Amy has 3 baskets of 4 apples each. She gives away 5 apples. "
        "How many apples does she have left?"
    )
    if question == target:
        return [
            "How many apples does Amy have in total, before giving any away?",
            "How many apples does Amy have left after giving away 5?",
        ]
    raise ValueError("decomposition table has no entry for this question")


def solve_stub(subquestion, prefix):
    if "in total" in subquestion:
        return "3 baskets of 4 apples each is 3 times 4, which is 12 apples."
    if "left after giving away" in subquestion:
        if "12 apples" not in prefix:
            raise ValueError("solver called before the total was established")
        return "12 apples minus 5 apples leaves 7 apples."
    raise ValueError(f"no solver rule for: {subquestion}")


def least_to_most(question):
    trace = Trace()
    for subquestion in decompose(question):
        prefix = trace.render_prefix()
        answer = solve_stub(subquestion, prefix)
        trace.steps.append(SubStep(question=subquestion, answer=answer))
    return trace


if __name__ == "__main__":
    q = (
        "Amy has 3 baskets of 4 apples each. She gives away 5 apples. "
        "How many apples does she have left?"
    )
    result = least_to_most(q)
    for step in result.steps:
        print(f"Q: {step.question}")
        print(f"A: {step.answer}")
    assert "7 apples" in result.steps[-1].answer
    print("OK: final subanswer resolves the original question.")
```

```typescript
interface SubStep {
  question: string;
  answer: string;
}

class Trace {
  steps: SubStep[] = [];

  renderPrefix(): string {
    return this.steps.map((s) => `Q: ${s.question}\nA: ${s.answer}`).join("\n");
  }
}

function decompose(question: string): string[] {
  const target =
    "Amy has 3 baskets of 4 apples each. She gives away 5 apples. " +
    "How many apples does she have left?";
  if (question === target) {
    return [
      "How many apples does Amy have in total, before giving any away?",
      "How many apples does Amy have left after giving away 5?",
    ];
  }
  throw new Error("decomposition table has no entry for this question");
}

function solveStub(subquestion: string, prefix: string): string {
  if (subquestion.includes("in total")) {
    return "3 baskets of 4 apples each is 3 times 4, which is 12 apples.";
  }
  if (subquestion.includes("left after giving away")) {
    if (!prefix.includes("12 apples")) {
      throw new Error("solver called before the total was established");
    }
    return "12 apples minus 5 apples leaves 7 apples.";
  }
  throw new Error(`no solver rule for: ${subquestion}`);
}

function leastToMost(question: string): Trace {
  const trace = new Trace();
  for (const subquestion of decompose(question)) {
    const prefix = trace.renderPrefix();
    const answer = solveStub(subquestion, prefix);
    trace.steps.push({ question: subquestion, answer });
  }
  return trace;
}

const q =
  "Amy has 3 baskets of 4 apples each. She gives away 5 apples. " +
  "How many apples does she have left?";
const result = leastToMost(q);
for (const step of result.steps) {
  console.log(`Q: ${step.question}`);
  console.log(`A: ${step.answer}`);
}
const last = result.steps[result.steps.length - 1].answer;
if (!last.includes("7 apples")) {
  throw new Error("final subanswer does not resolve the original question");
}
console.log("OK: final subanswer resolves the original question.");
```

```go
package main

import (
	"fmt"
	"strings"
)

type subStep struct {
	question string
	answer   string
}

type trace struct {
	steps []subStep
}

func (t *trace) renderPrefix() string {
	var b strings.Builder
	for _, s := range t.steps {
		fmt.Fprintf(&b, "Q: %s\nA: %s\n", s.question, s.answer)
	}
	return b.String()
}

func decompose(question string) ([]string, error) {
	target := "Amy has 3 baskets of 4 apples each. She gives away 5 apples. " +
		"How many apples does she have left?"
	if question == target {
		return []string{
			"How many apples does Amy have in total, before giving any away?",
			"How many apples does Amy have left after giving away 5?",
		}, nil
	}
	return nil, fmt.Errorf("decomposition table has no entry for this question")
}

func solveStub(subquestion, prefix string) (string, error) {
	switch {
	case strings.Contains(subquestion, "in total"):
		return "3 baskets of 4 apples each is 3 times 4, which is 12 apples.", nil
	case strings.Contains(subquestion, "left after giving away"):
		if !strings.Contains(prefix, "12 apples") {
			return "", fmt.Errorf("solver called before the total was established")
		}
		return "12 apples minus 5 apples leaves 7 apples.", nil
	default:
		return "", fmt.Errorf("no solver rule for: %s", subquestion)
	}
}

func leastToMost(question string) (*trace, error) {
	t := &trace{}
	subqs, err := decompose(question)
	if err != nil {
		return nil, err
	}
	for _, sq := range subqs {
		prefix := t.renderPrefix()
		answer, err := solveStub(sq, prefix)
		if err != nil {
			return nil, err
		}
		t.steps = append(t.steps, subStep{question: sq, answer: answer})
	}
	return t, nil
}

func main() {
	q := "Amy has 3 baskets of 4 apples each. She gives away 5 apples. " +
		"How many apples does she have left?"
	result, err := leastToMost(q)
	if err != nil {
		panic(err)
	}
	for _, s := range result.steps {
		fmt.Printf("Q: %s\nA: %s\n", s.question, s.answer)
	}
	last := result.steps[len(result.steps)-1].answer
	if !strings.Contains(last, "7 apples") {
		panic("final subanswer does not resolve the original question")
	}
	fmt.Println("OK: final subanswer resolves the original question.")
}
```

All three samples were compiled or run directly against this repository's
available toolchain during authoring. The Python sample was executed with
`python3` and printed the expected two-step trace plus its final assertion.
The TypeScript sample was type-checked and compiled with `npx tsc --strict`
and then executed with `node`, producing the same trace. The Go sample was
built and run with `go run` and separately re-verified with `go vet`,
producing the same trace. None required a network call or an API key,
consistent with the note above that `solveStub` is a deterministic stand-in
for a real Solver call, not a live model invocation.
