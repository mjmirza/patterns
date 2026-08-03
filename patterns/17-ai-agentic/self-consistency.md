---
name: Self-Consistency
slug: self-consistency
family: 17-ai-agentic
category: AI Agentic
aliases: [Self-Consistency Decoding, Majority Vote Reasoning, Sample-and-Marginalize, Self-Consistency Chain-of-Thought, SC-CoT]
first_described: "Wang, Wei, Schuurmans, Le, Chi, Narang, Chowdhery, Zhou 2022"
maturity: established
related: [chain-of-thought, tree-of-thoughts, react, reflection, ensemble-of-agents, best-of-n-sampling, llm-as-judge, majority-voting]
incompatible_with: []
verified: 2026-08-03
---

# Self-Consistency

## 1. Name, aliases, and lineage

The canonical name is Self-Consistency, sometimes written Self-Consistency
Decoding to distinguish it from a self-consistency check inside a single
reasoning chain. It was introduced by Xuezhi Wang, Jason Wei, Dale Schuurmans,
Quoc Le, Ed Chi, Sharan Narang, Aakanksha Chowdhery, and Denny Zhou in "Self-
Consistency Improves Chain of Thought Reasoning in Language Models," posted to
arXiv on March 21, 2022, with a revised version on March 7, 2023, arXiv
2203.11171, https://arxiv.org/abs/2203.11171, verified 2026-08-03. The paper
frames the method as a decoding strategy that replaces the greedy decoding
used in chain-of-thought prompting.

In the surrounding literature the same core idea appears under several names.
Sample-and-marginalize describes the mechanics precisely, sample many
reasoning paths, then marginalize over them to find the answer that the
distribution actually favors, rather than trusting one greedily decoded path.
Majority Vote Reasoning is the informal name used when the aggregation step is
literally a plurality vote over final answers. In agentic engineering
practice, teams frequently shorten it to "sampling with majority vote" or
just "N-sample voting," and it is often confused with Best-of-N sampling,
covered under Non-Applicability below, because both involve drawing multiple
completions from one model.

The method sits inside a family of test-time compute scaling techniques that
became prominent from 2022 onward. Give the model more inference-time
computation, in the form of more samples, more search, or more deliberation,
instead of a larger or better-trained model, and turn that extra computation
into a measurable accuracy gain. Self-consistency was one of the first
techniques in this family to show a large, benchmark-verified lift from pure
sampling and voting, with no additional training and no external tools.

## 2. Problem and context

A large language model generating a chain-of-thought answer with standard
greedy decoding commits to one path through the reasoning space, token by
token, and never reconsiders. If that path takes a wrong turn early, for
example mis-parsing a word problem or skipping a case in an enumeration, every
downstream token compounds the error, and the final answer is wrong even
though the model, sampled differently, might have reasoned correctly.

The context in which this problem is sharpest is exactly the context in which
chain-of-thought prompting itself is used, multi-step arithmetic, commonsense
reasoning with several dependent facts, and any task where there is a single,
checkable final answer but many valid ways to reach it. A grade-school word
problem can be solved by setting up the equation directly, or by working
backward from the question, or by breaking it into two smaller sub-problems.
A capable model that is uncertain between these approaches will, across many
independent samples, sometimes take one path and sometimes another. The
insight the method exploits is that correct paths tend to agree on the final
answer even when they disagree on the intermediate reasoning, while incorrect
paths tend to scatter. A mis-parsed problem produces a different wrong answer
almost every time it is mis-parsed differently. So the answer that recurs most
often across independently sampled reasoning paths is, empirically, far more
likely to be correct than the answer from any single greedily decoded path.

The problem does not exist in this form for a task with no verifiable final
answer, and it does not exist for a task the model solves correctly and
consistently on the first try. It exists specifically where reasoning is
noisy, where the model's competence is real but its execution is inconsistent,
and where the final answer can be extracted and compared across samples in a
mechanical way.

## 3. Forces

Latency and cost pull directly against accuracy. Sampling N reasoning chains
and aggregating them costs roughly N times the inference compute and,
absent parallel dispatch, N times the wall-clock latency of a single greedy
decode. The original paper reports its largest gains at 40 samples per
question on some tasks, a cost multiplier that is trivial for an offline
benchmark run and can be prohibitive for a latency-sensitive user-facing
endpoint. This is a genuine trade, not a free win. Every additional sample
narrows the gap to the ceiling accuracy of the underlying model while linearly
increasing spend.

Answer extractability is a hard constraint the method depends on rather than
merely prefers. The aggregation step needs a well-defined equivalence
relation over final answers, two completions must be comparable as the same
answer or as different answers for a vote to mean anything. This favors
tasks with short, structured final answers (a number, a multiple-choice
letter, a boolean) and disfavors open-ended generation, where "the same
answer" is not a well-formed question. This is judgement, not a sourced
claim. The method's authors evaluate it on arithmetic and commonsense QA
benchmarks precisely because those tasks have this property, and the paper
does not claim the method transfers to free-form generation without a
redefinition of consistency.

Diversity of sampling competes with fidelity to the model's true belief.
Self-consistency depends on temperature or nucleus sampling to produce varied
reasoning paths. At temperature zero every sample is identical and the vote
degenerates to N copies of one greedy answer, contributing nothing. Push
temperature too high and the model starts producing low-quality, off-topic
reasoning chains that add noise to the vote rather than diverse but valid
alternative paths. The method sacrifices the determinism of greedy decoding
in exchange for this diversity, and getting the sampling temperature wrong in
either direction destroys the benefit.

Interpretability is a further force the method quietly sacrifices. A single
greedily decoded chain of thought is, for better or worse, inspectable. A
person can read the model's stated reasoning and judge whether it makes
sense. A self-consistency vote across forty samples produces a distribution
over answers with forty different reasoning traces behind it, and the
reported answer is a statistical artifact of that distribution rather than
the conclusion of any one legible argument. Teams that need an audit trail
for a specific decision, not just an accurate one, pay for this with reduced
transparency unless they separately retain and surface the majority-cluster
reasoning traces.

## 4. Applicability and non-applicability

Reach for self-consistency when the task has a chain-of-thought-amenable
structure, meaning the model benefits from working through intermediate
steps before answering. Also reach for it when the final answer is
extractable and comparable across samples with a simple parser, a number, a
label, a short span, a boolean, and when accuracy matters more than latency
and cost for this call, which usually means an offline evaluation, a batch
pipeline, a high-stakes single decision, or a workflow where the user has
already accepted a multi-second wait in exchange for a better answer. The
underlying model must be capable enough to sometimes reach the correct
answer, because self-consistency amplifies an existing but inconsistent
competence; it cannot manufacture competence a model does not have.

Do not reach for it when the task produces long-form free text with no
natural notion of "the same answer," such as a summary, an essay, or an open
creative brief. Majority voting under a strict equality relation over
paragraph-length text almost never finds agreement, and a looser semantic
similarity check reintroduces the exact judgement problem the method exists
to avoid.

Do not reach for it when a single call already saturates the task, meaning
the model is correct essentially every time at temperature zero. The extra
sampling cost buys nothing measurable and only adds latency.

Do not reach for it as a substitute for retrieval or tool use when the model
is missing a fact, not reasoning about one. Self-consistency amplifies
reasoning that the model is capable of but executes noisily; it cannot
recover a fact the model never knew, and running the same knowledge gap
through forty samples produces forty confidently wrong or evasive answers
rather than one honestly uncertain one.

Do not reach for it under a hard real-time latency budget, such as an
interactive chat turn where the user expects a response within roughly a
second, unless the deployment can afford genuinely parallel dispatch of every
sample and the aggregation step itself is near-instant.

Do not reach for it when the task is adversarial or the model's errors are
systematic rather than random, for example a model that has memorized one
specific wrong answer to a common trick question. Systematic errors recur
identically across samples and a vote over identical wrong answers still
returns the wrong answer. The method's benefit comes specifically from
random, uncorrelated noise in reasoning execution, and it provides no defense
against a bias the model exhibits consistently.

## 5. Structure

The pattern has four participants.

The Prompt Template is the fixed chain-of-thought prompt, typically a small
set of few-shot exemplars each showing a question, a worked intermediate
reasoning, and a final answer, followed by the new question. This is the same
prompt structure used for ordinary chain-of-thought prompting; self-
consistency changes nothing about the prompt itself.

The Sampler is the component that issues N independent generation requests
against the prompt with stochastic decoding enabled, most commonly nucleus
sampling with a fixed temperature and top-p, producing N distinct completions
that each carry their own reasoning trace and a stated final answer.

The Answer Extractor is a task-specific parser that pulls the final answer
out of each completion's free-text reasoning trace and normalizes it into a
comparable canonical form, for example parsing "So the answer is 42." into
the integer 42, or parsing "The correct choice is (C)." into the label C.

The Aggregator is the component that counts occurrences of each canonical
answer across the N extracted answers and returns the plurality answer as
the pattern's output, optionally along with the vote count as a confidence
signal. The original paper's formal framing is that the aggregator
marginalizes out the sampled reasoning paths to find the answer that
maximizes the marginal probability under the model's own sampling
distribution, which the plurality vote approximates.

## 6. ASCII structure diagram

```
+-----------------------------------------------------------+
|                  Self-Consistency Pipeline                |
+-----------------------------------------------------------+

  +----------------+
  | Prompt Template|   fixed few-shot chain-of-thought
  | (question + Q) |   exemplars, then the target question
  +--------+-------+
           |
           v
     +-----------+
     |  Sampler  |  temperature/top-p > 0, N independent calls
     +-----+-----+
           |
   +-------+-------+-------+-------+
   v       v       v       v       v
 +----+  +----+  +----+  +----+  +----+
 |Path|  |Path|  |Path|  |Path|  |Path|   N reasoning
 | 1  |  | 2  |  | 3  |  | 4  |  | N  |   chains, each with
 +--+-+  +--+-+  +--+-+  +--+-+  +--+-+   its own final answer
    |       |       |       |       |
    v       v       v       v       v
 +----------------------------------------+
 |          Answer Extractor              |
 |  (task-specific parser, normalizes     |
 |   free text -> canonical answer form)  |
 +--------------------+-------------------+
                       |
                       v
             +-------------------+
             |    Aggregator     |
             |  (count votes,    |
             |   return plurality|
             |   answer + count) |
             +---------+---------+
                        |
                        v
                +----------------+
                | Final Answer   |
                | + confidence   |
                | (vote share)   |
                +----------------+
```

## 7. Dynamics

```
Client                Sampler              Model API           Extractor/Aggregator
  |                       |                       |                        |
  |--request(question)--->|                       |                        |
  |                       |--sample #1 (T>0)------>|                        |
  |                       |<--completion #1--------|                        |
  |                       |--sample #2 (T>0)------>|                        |
  |                       |<--completion #2--------|                        |
  |                       |         ...  (up to N, dispatched serially      |
  |                       |               or in parallel; parallel is       |
  |                       |               strongly preferred for latency)   |
  |                       |--sample #N (T>0)------>|                        |
  |                       |<--completion #N--------|                        |
  |                       |------------------------------------------------>|
  |                       |          N completions, each with reasoning     |
  |                       |          + a stated final answer                |
  |                       |                       |    extract answer from  |
  |                       |                       |    each completion      |
  |                       |                       |    (a1, a2, ..., aN)    |
  |                       |                       |         |               |
  |                       |                       |         v               |
  |                       |                       |  count occurrences of   |
  |                       |                       |  each distinct answer   |
  |                       |                       |         |               |
  |                       |                       |         v               |
  |                       |                       |  select plurality       |
  |                       |                       |  answer + vote share    |
  |<---------------------------------------------------------final answer---|
  |                       |                       |                        |
```

A confidence-gated variant inserts an early-exit check after a small number of
samples, for example after the first 5 of a planned 40. If one answer already
holds an overwhelming majority, for example 5 of 5, the aggregator can stop
sampling early and skip the remaining calls, trading a small amount of
statistical rigor for a large reduction in expected cost on the easy
majority of questions where the model is already consistent. This is an
engineering optimization on top of the base pattern, not part of the original
paper's formal method, and is labeled here as such.

## 8. Implementation variants

The canonical variant, as published, is unweighted majority vote over the
final answer only. Every sampled completion counts as exactly one vote
regardless of how confident or how long its reasoning trace was, and the
intermediate reasoning is discarded once the final answer is extracted.

A confidence-weighted variant weights each vote by the model's own reported
or computed log-probability for that completion, so a high-confidence
completion counts for more than one drawn from a low-probability tail of the
sampling distribution. This trades the pattern's simplicity for a signal that
can help when the vote is close, at the cost of needing access to token-level
log-probabilities, which not every API surface exposes.

A universal self-consistency variant, used when the final answer cannot be
mechanically parsed into a strict equality class, replaces the exact-match
vote with a second model call that is shown all N completions at once and
asked to select or synthesize the most consistent answer among them, turning
the plurality vote into an LLM-as-judge aggregation step. This variant is
closely related to and often confused with an ensemble-of-agents pattern; the
distinguishing feature that keeps it a self-consistency variant rather than a
distinct ensemble is that all N completions come from one model sampled
independently against one fixed prompt, not from distinct agents with
distinct prompts or roles.

An early-stopping variant, described in dynamics above, checks running vote
agreement after a small batch and halts sampling once a statistically
sufficient majority has formed, reducing the average-case sample count well
below the fixed N used in the paper's benchmark evaluation.

A structured-output variant constrains each sampled completion's final
answer to a machine-parseable format, for example a JSON object with an
`answer` field, specifically to make the extraction step in dimension 5
dependable and eliminate the failure mode where free-text parsing
mis-extracts a correct answer as a vote for the wrong canonical form. The
Stanford DSPy framework's `MultiChainComparison` module is a concrete,
maintained implementation of this shape. It takes a fixed number, M, of
completion attempts as structured inputs, each supplying a reasoning field
and an answer field, and produces a single synthesized rationale and answer
from comparing them, per the DSPy API reference for `dspy.MultiChainComparison`,
https://dspy.ai/api/modules/MultiChainComparison/, verified 2026-08-03.

## 9. Known production uses

**The original Google Research evaluation across five models and five
benchmarks.** Wang, Wei, Schuurmans, Le, Chi, Narang, Chowdhery, and Zhou
evaluate self-consistency against UL2-20B, GPT-3-175B, LaMDA-137B,
PaLM-540B, and Codex, reporting absolute accuracy gains from adding
self-consistency on top of chain-of-thought prompting of plus 17.9 points on
GSM8K, plus 11.0 on SVAMP, plus 12.2 on AQuA, plus 6.4 on StrategyQA, and
plus 3.9 on ARC-challenge. "Self-Consistency Improves Chain of Thought
Reasoning in Language Models," arXiv 2203.11171,
https://arxiv.org/abs/2203.11171, verified 2026-08-03.

**AlphaCode's massive sampling, filtering, and clustering pipeline for
competitive programming.** DeepMind's AlphaCode system generates, in the
authors' own words, "a massive amount of C++ and Python programs for each
problem, orders of magnitude larger than previous work," and then "filter,
cluster, and rerank those solutions to a small set of 10 candidate programs
that we submit for external assessment." This is a close structural cousin
of self-consistency at production scale. Rather than voting over a short
final answer, it clusters behaviorally-equivalent program outputs and
selects the largest cluster as the most probable correct solution, applying
the same sample-many-and-aggregate-by-agreement principle to a domain where
the final answer is a program's runtime behavior rather than a number.
DeepMind, "Competitive programming with AlphaCode,"
https://deepmind.google/blog/competitive-programming-with-alphacode/,
verified 2026-08-03.

**DSPy's `MultiChainComparison` module.** Stanford's DSPy framework, used to
programmatically compose and optimize LLM pipelines, ships a maintained
module that accepts M independent completion attempts, each with its own
reasoning and answer fields, and synthesizes a single corrected rationale
and answer by comparing them, implementing the aggregation half of the
self-consistency pattern as a reusable, typed module rather than a one-off
notebook script. DSPy API reference, `dspy.MultiChainComparison`,
https://dspy.ai/api/modules/MultiChainComparison/, verified 2026-08-03.

## 10. Consequences

Positive. Self-consistency produces a measured, reproducible accuracy gain
on reasoning benchmarks using only sampling and voting, with no additional
model training, no fine-tuning data, and no external tool or retrieval
system, which the source paper demonstrates across five different base
models and five different benchmark families. It degrades gracefully. At
the limit of a single sample, N equals 1, it reduces exactly to plain
chain-of-thought prompting, so there is no regime in which adding the
pattern actively hurts accuracy relative to the single-sample baseline, only
regimes where it does not help enough to justify its cost. The vote count
or vote share is a usable, cheap confidence signal that a plain single-shot
completion does not provide. A near-unanimous vote is a meaningfully
different situation from a narrow plurality, and downstream systems can
route on that difference, for example escalating narrow-plurality answers
to a human reviewer.

Negative. Cost and latency scale linearly with the sample count N in the
straightforward implementation, and the paper's own strongest results use
sample counts as high as 40, which is an expensive multiplier to carry into
a cost-sensitive production path. The aggregation step depends on a
well-defined, mechanically checkable notion of answer equivalence, and
building or maintaining that extractor is nontrivial engineering work in
its own right for any answer format beyond a short label or number. Get the
normalization wrong, for example failing to treat "42" and "forty-two" as
the same answer, and the vote is silently corrupted. The pattern discards
almost all of the information in each sampled reasoning trace, keeping only
the final answer, which both wastes the useful diagnostic content of the
traces and removes the interpretability that a single chain-of-thought
answer would otherwise offer. Finally, the method provides no protection
against a systematic bias the model holds consistently across samples; it
only cancels random, uncorrelated noise in reasoning execution.

## 11. Failure modes and misuse

**Symptom.** The self-consistency vote is completely flat, no plurality
forms, or the top answer wins by only one or two votes out of forty, and
accuracy is no better than a single greedy sample.
**Cause.** Sampling temperature is set too low, so the N completions are
nearly identical copies of the same greedy path and contribute no genuine
diversity, meaning the vote is an illusion of ensemble diversity over what
is functionally a single sample repeated N times.
**Fix.** Raise temperature or top-p until the completions demonstrably
diverge in their intermediate reasoning steps on a held-out set of easy
questions where the correct chain-of-thought path is known, and verify
diversity empirically rather than assuming a default sampling configuration
is adequate.

**Symptom.** Vote counts look reasonable but the majority answer is
frequently wrong on questions the model demonstrably can answer correctly in
isolation with careful prompting.
**Cause.** The answer extractor mis-parses a correct answer's free-text
representation into the wrong canonical bucket, for example splitting
"$3.50" and "3.5" into two different vote buckets that should have been one,
which silently fragments the true majority into several minority buckets
and lets an unrelated wrong answer win the plurality.
**Fix.** Test the extractor against a labeled sample of real completions
before trusting the pipeline in production, specifically checking for
formatting variants. Currency symbols, units, trailing punctuation, letter
case in multiple-choice labels, and numeric versus written-out numbers.

**Symptom.** Production cost or latency on the reasoning endpoint spikes
unexpectedly after enabling self-consistency, and the team cannot explain
the multiplier from the accuracy gain alone.
**Cause.** N was set by copying the paper's benchmark configuration, for
example 40 samples, without re-deriving an N appropriate to the production
task's actual difficulty and latency budget. The paper's high sample counts
are chosen to maximize benchmark accuracy for a research evaluation, not to
minimize cost for a live endpoint.
**Fix.** Run a sweep of accuracy versus N on a representative validation
set and pick the smallest N on the accuracy-cost curve's knee, and pair it
with the early-stopping variant from dimension 8 so easy questions consume
far fewer than the worst-case N samples.

**Symptom.** The pattern is applied to an open-ended writing or
summarization task and the team reports that "self-consistency does
nothing," or that it non-deterministically returns different outputs on
successive runs with the same votes tied.
**Cause.** There is no well-defined equivalence relation over the task's
outputs, so no two completions are ever counted as the same answer, and the
aggregator effectively falls back to an arbitrary tie-break, which is
indistinguishable from picking one of the N samples at random. This is the
core non-applicability case from dimension 4 being violated in practice.
**Fix.** Either redefine the task to have a checkable, structured final
answer that the model states explicitly, separate from its prose reasoning,
or replace the exact-match vote with the LLM-as-judge aggregation variant
from dimension 8, and evaluate that judge's own reliability before trusting
its verdicts.

**Symptom.** The model confidently produces the same specific wrong answer
across almost all N samples, giving a high-confidence vote share for an
answer that is factually incorrect.
**Cause.** The error is a systematic bias or a knowledge gap the model holds
consistently, not random noise in its reasoning execution. Self-consistency
has no mechanism to correct an error the model makes the same way every
time, and a confident majority vote can make the wrong answer look more
trustworthy than a single uncertain sample would have.
**Fix.** Treat unusually high, near-unanimous confidence on a
knowledge-dependent question as a signal to check the model's underlying
knowledge separately, for example with a retrieval step or an external
fact check, rather than treating vote unanimity as proof of correctness. Do
not use this pattern as a substitute for grounding when the failure mode is
missing knowledge rather than noisy reasoning.

## 12. Trade-off matrix

| Force | Self-Consistency | Chain-of-Thought (single sample) | Best-of-N Sampling (reward-model scored) | Tree of Thoughts |
|---|---|---|---|---|
| Inference cost | High, linear in N | Lowest, one sample | High, linear in N plus a scorer call per sample | Highest, branches explored and often pruned with extra evaluation calls |
| Latency (parallel dispatch) | Moderate, one round of N parallel calls | Lowest | Moderate, one round of N parallel calls plus scoring | High, multiple sequential rounds of exploration |
| Needs task with checkable final answer | Yes, required | No | No, reward model can score open-ended text | Not strictly, but benefits from a step-evaluable structure |
| Needs an external verifier or reward model | No, votes are self-scored by agreement | No | Yes, a separate reward or preference model is required | Optional, a value function or self-evaluation prompt improves it |
| Interpretability of final answer | Low, reasoning traces discarded after voting | High, one legible trace | Moderate, one trace is kept but selection logic is opaque | Low to moderate, exploration tree can be logged but is large |
| Corrects systematic model bias | No | No | Sometimes, if the reward model is unbiased where the policy is not | No |
| Implementation complexity | Low, sampling plus a vote | Lowest, no aggregation | Moderate, requires training or acquiring a scorer | High, requires a search strategy and pruning policy |

## 13. Related and incompatible patterns

Chain-of-thought prompting is the direct prerequisite this pattern builds on.
Self-consistency has no meaning without a chain-of-thought-style prompt to
sample multiple reasoning traces from in the first place, and the two are
described in the same 2022 paper as a pairing rather than as separate
inventions.

Tree of Thoughts generalizes the same test-time-compute-scaling idea from a
flat set of N independent samples into a branching search over partial
reasoning states, with pruning and backtracking at each branch point. The
two patterns compose. A Tree of Thoughts implementation can use a
self-consistency-style vote as its leaf-node evaluation step rather than a
learned value function.

ReAct and Reflection are complementary rather than substitutable. ReAct
interleaves reasoning with tool calls to fix knowledge gaps, and Reflection
has the model critique and revise its own single answer across turns.
Neither pattern addresses the specific failure mode self-consistency targets,
which is variance across independently sampled reasoning paths on a single
turn, and a real system frequently uses self-consistency for the final
answer-selection step while ReAct handles tool-grounded fact retrieval
earlier in the same pipeline.

Ensemble-of-agents is the closest incompatible-by-definition neighbor. An
ensemble draws its diversity from distinct models, distinct prompts, or
distinct roles, while self-consistency draws its diversity purely from
stochastic re-sampling of one model against one fixed prompt. A system that
mixes both, for example three different models each sampled N times with a
combined vote, is a hybrid and should be documented as such rather than
labeled as pure self-consistency, because the failure-mode analysis in
dimension 11 no longer fully applies once systematic per-model bias becomes
part of the mix.

Best-of-N sampling scored by a reward model is frequently confused with
self-consistency because both draw N samples from one model, but the
selection mechanism is incompatible in spirit. Best-of-N needs an external
scorer and works on tasks with no checkable ground-truth answer, while
self-consistency needs no external scorer and specifically requires a
checkable, votable final answer. See dimension 4's non-applicability list
for the practical consequence of confusing the two.

LLM-as-judge composes with self-consistency in the universal self-consistency
variant from dimension 8, where a judge call replaces the exact-match vote.
It is incompatible with the pattern's core cost-efficiency claim, because it
reintroduces a full additional model call and the judge's own reliability
becomes a new dependency the plain vote never had.

## 14. Refactoring path in and out

To introduce self-consistency into an existing single-shot chain-of-thought
call, first confirm the task's final answer is mechanically extractable and
comparable, per dimension 4, before writing any sampling code. A task that
fails this check should not receive this refactor at all. Second, change the
decoding configuration from greedy or near-zero temperature to a temperature
and top-p known to produce genuine reasoning diversity, verified against a
small held-out set as described in dimension 11's first failure mode. Third,
wrap the existing single call in a loop, or better, a parallel fan-out, that
issues N independent calls against the unchanged prompt. Fourth, write and
unit-test the answer extractor against real sampled completions, not
synthetic ones, specifically probing the formatting-variant failure mode
from dimension 11. Fifth, add the aggregator and, if the endpoint is latency
or cost sensitive, the early-stopping optimization from dimension 6 before
shipping. At every step, keep the N equals 1 path working and measurable, so
the team can directly quantify the marginal accuracy gained per additional
sample against its cost.

To remove self-consistency once a task no longer needs it, most commonly
because the underlying model has become reliably accurate on the first
sample after a model upgrade, or because the accuracy gain was never
measured to be worth its cost, first re-run the accuracy-versus-N sweep from
dimension 11's third failure mode fix to confirm the marginal gain from N
greater than 1 has actually collapsed toward zero, rather than assuming it
based on a general sense that the model has improved. Then reduce N to 1,
remove the now-dead aggregation and extraction code, and restore
deterministic or near-deterministic decoding if the interpretability and
latency benefits of a single legible reasoning trace are wanted back. Keep
the extractor's test suite, if it has broader reuse as a general answer
normalizer for the task, rather than deleting it along with the vote logic.

## 15. Testing and verification

Self-consistency is genuinely easier to test at the aggregation layer and
genuinely harder to test at the sampling layer than a plain single-shot
call. The aggregator itself is pure, deterministic logic over a list of
canonical answers, a straightforward unit-testing target. Feed it fixed
lists such as `[42, 42, 41, 42, 7]` and assert it returns 42 with a vote
share of 3 out of 5, with no need to touch a live model at all.

The answer extractor needs a labeled corpus of real, messy model
completions, not hand-written synthetic examples, because the failure mode
that matters, formatting-variant fragmentation from dimension 11, only shows
up in the actual variety of ways a model phrases its final answer. Build this
corpus by running the sampler against a fixed set of benchmark questions
with known correct answers and hand-labeling each completion's true intended
answer, then asserting the extractor recovers that label.

What became harder to test is the end-to-end sampling and diversity
behavior, because it is inherently stochastic. A single test run at a fixed
temperature can pass or fail by chance. Test this statistically rather than
with a single assertion, for example by running the full N-sample pipeline
many times over a fixed benchmark question set and asserting that aggregate
accuracy across runs falls within an expected confidence interval, rather
than asserting any single run's exact vote outcome. Seed the sampler's
random number generator for reproducibility in CI wherever the underlying
model API supports a deterministic seed parameter, and treat any API that
does not support seeding as a source of intrinsic test flakiness that must
be budgeted for with wider tolerance bands, not eliminated.

## 16. Observability signals

Log the raw vote distribution for every self-consistency call, not just the
winning answer. The full multiset of extracted canonical answers and their
counts. A healthy instance shows most votes concentrating into one or two
clusters with a clear plurality; a system trending unhealthy shows votes
fragmenting across many distinct singleton answers, which is the
observable signature of either the sampling-diversity failure mode or the
extractor-fragmentation failure mode from dimension 11, and the vote
distribution shape alone usually tells you which. Many near-identical
answers differing only in surface formatting points at the extractor, while
wildly different substantive answers with no near-duplicates points at
genuine reasoning inconsistency in the model.

Track vote share of the winning answer as a time series, not just its
average. A dashboard should show the distribution of vote shares across
recent calls, because a system whose typical winning vote share drifts down
over time, for example from a 35-of-40 average toward a 21-of-40 average,
is a leading indicator of either a model regression after a provider-side
update or a task distribution shift toward harder questions than the system
was tuned for, and this drift is visible well before raw accuracy metrics
would catch it if ground-truth labels are delayed or unavailable in
production.

Track sample count actually consumed per call, separate from the configured
maximum N, when the early-stopping variant is in use, and alert if the
average consumed sample count creeps up toward the configured maximum,
which signals that the task distribution has grown harder to reach
consensus on and that either the maximum N or the early-stopping threshold
needs to be revisited.

Track cost and latency per call as first-class metrics alongside accuracy,
because this pattern's entire value proposition is a specific trade between
these three, and a dashboard that reports accuracy in isolation makes it
impossible to tell whether the pattern is still earning its cost multiplier
over the single-sample baseline.

## 17. Security and privacy implications

This dimension is largely analytical judgement rather than a set of sourced
facts, because the original paper does not address deployment security.

The pattern multiplies the number of model calls made per user request by a
factor of N, which multiplies the surface area for prompt injection or
data-leakage incidents in exact proportion. If the underlying prompt or
retrieved context is compromised, the compromise is now sampled and voted
on N times rather than surfacing once, and in the universal self-consistency
variant that uses an LLM-as-judge aggregation, an injected instruction that
successfully manipulates one sampled completion could plausibly manipulate
several, biasing the vote toward an attacker-controlled answer rather than
diluting it, since the injected instruction is present in the fixed prompt
template shared by every sample rather than being an independent per-sample
variable.

Logging the full vote distribution, as recommended in dimension 16, means
retaining N times as much raw model output per user interaction as a
single-shot call would, which is a proportional increase in the amount of
potentially sensitive generated content at rest. Any data-retention or
redaction policy applied to single-shot completions should be applied
identically to every one of the N completions gathered for a vote, not just
to the winning answer that gets surfaced to the user.

There is no meaningful new confidentiality boundary introduced by the
pattern itself. All N samples are drawn against the identical prompt and
context that a single-shot call would have used, so the pattern does not by
itself expose any input data to any party that a single-shot call would not
already have exposed. The risk it adds is entirely about the multiplied
volume and multiplied injection surface described above, not about a new
category of exposure.

## 18. References

1. Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc Le, Ed Chi, Sharan Narang,
   Aakanksha Chowdhery, Denny Zhou. "Self-Consistency Improves Chain of
   Thought Reasoning in Language Models." arXiv 2203.11171.
   https://arxiv.org/abs/2203.11171. Verified 2026-08-03.
2. DeepMind. "Competitive programming with AlphaCode."
   https://deepmind.google/blog/competitive-programming-with-alphacode/.
   Verified 2026-08-03.
3. DSPy documentation. "MultiChainComparison" module API reference.
   https://dspy.ai/api/modules/MultiChainComparison/. Verified 2026-08-03.
4. Prompting Guide. "Self-Consistency."
   https://www.promptingguide.ai/techniques/consistency. Verified 2026-08-03.
   Cited for its description of self-consistency as replacing the naive
   greedy decoding used in chain-of-thought prompting; the page identifies
   no named production systems and is used here only as a corroborating
   description of the technique, not as a production-use citation.

## Code examples

### TypeScript

```typescript
type Sampler = (prompt: string, temperature: number) => Promise<string>;

interface VoteResult {
  answer: string;
  voteShare: number;
  distribution: Record<string, number>;
}

function extractAnswer(completion: string): string | null {
  const match = completion.match(/answer is:?\s*([^\n.]+)/i);
  if (!match) return null;
  return match[1].trim().toLowerCase().replace(/[.$,]/g, "");
}

async function selfConsistency(
  prompt: string,
  sample: Sampler,
  n: number,
  temperature = 0.7
): Promise<VoteResult> {
  const completions = await Promise.all(
    Array.from({ length: n }, () => sample(prompt, temperature))
  );

  const votes: Record<string, number> = {};
  for (const completion of completions) {
    const answer = extractAnswer(completion);
    if (answer === null) continue;
    votes[answer] = (votes[answer] ?? 0) + 1;
  }

  const totalVotes = Object.values(votes).reduce((a, b) => a + b, 0);
  if (totalVotes === 0) {
    throw new Error("no completion produced an extractable answer");
  }

  const [winner, count] = Object.entries(votes).sort((a, b) => b[1] - a[1])[0];
  return { answer: winner, voteShare: count / totalVotes, distribution: votes };
}

async function fakeSampler(prompt: string, _t: number): Promise<string> {
  const paths = [
    "First 3 apples then 4 more. The answer is: 7",
    "3 plus 4 equals seven. The answer is: 7",
    "Miscounted, got 6. The answer is: 6",
    "3 + 4 = 7. The answer is: 7",
  ];
  return paths[Math.floor(Math.random() * paths.length)];
}

selfConsistency("How many apples in total?", fakeSampler, 20).then((result) => {
  console.log(`winner=${result.answer} share=${result.voteShare.toFixed(2)}`);
  console.log(result.distribution);
});
```

### Python

```python
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class VoteResult:
    answer: str
    vote_share: float
    distribution: Counter


def extract_answer(completion: str) -> Optional[str]:
    match = re.search(r"answer is:?\s*([^\n.]+)", completion, re.IGNORECASE)
    if not match:
        return None
    return re.sub(r"[.$,]", "", match.group(1).strip().lower())


def self_consistency(
    prompt: str,
    sample: Callable[[str, float], str],
    n: int,
    temperature: float = 0.7,
) -> VoteResult:
    with ThreadPoolExecutor(max_workers=n) as pool:
        completions = list(pool.map(lambda _: sample(prompt, temperature), range(n)))

    votes: Counter = Counter()
    for completion in completions:
        answer = extract_answer(completion)
        if answer is not None:
            votes[answer] += 1

    if not votes:
        raise ValueError("no completion produced an extractable answer")

    winner, count = votes.most_common(1)[0]
    total = sum(votes.values())
    return VoteResult(answer=winner, vote_share=count / total, distribution=votes)


if __name__ == "__main__":
    import random

    def fake_sampler(prompt: str, temperature: float) -> str:
        paths = [
            "First 3 apples then 4 more. The answer is: 7",
            "3 plus 4 equals seven. The answer is: 7",
            "Miscounted, got 6. The answer is: 6",
            "3 + 4 = 7. The answer is: 7",
        ]
        return random.choice(paths)

    result = self_consistency("How many apples in total?", fake_sampler, 20)
    print(f"winner={result.answer} share={result.vote_share:.2f}")
    print(dict(result.distribution))
```

### Go

```go
package main

import (
	"fmt"
	"math/rand"
	"regexp"
	"strings"
	"sync"
)

type VoteResult struct {
	Answer       string
	VoteShare    float64
	Distribution map[string]int
}

var answerPattern = regexp.MustCompile(`(?i)answer is:?\s*([^\n.]+)`)

func extractAnswer(completion string) (string, bool) {
	match := answerPattern.FindStringSubmatch(completion)
	if match == nil {
		return "", false
	}
	cleaned := strings.ToLower(strings.TrimSpace(match[1]))
	cleaned = strings.NewReplacer(".", "", "$", "", ",", "").Replace(cleaned)
	return cleaned, true
}

func selfConsistency(prompt string, sample func(string, float64) string, n int, temperature float64) (VoteResult, error) {
	completions := make([]string, n)
	var wg sync.WaitGroup
	for i := 0; i < n; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			completions[idx] = sample(prompt, temperature)
		}(i)
	}
	wg.Wait()

	votes := map[string]int{}
	for _, completion := range completions {
		if answer, ok := extractAnswer(completion); ok {
			votes[answer]++
		}
	}

	total := 0
	for _, c := range votes {
		total += c
	}
	if total == 0 {
		return VoteResult{}, fmt.Errorf("no completion produced an extractable answer")
	}

	winner, best := "", -1
	for answer, count := range votes {
		if count > best {
			winner, best = answer, count
		}
	}

	return VoteResult{
		Answer:       winner,
		VoteShare:    float64(best) / float64(total),
		Distribution: votes,
	}, nil
}

func fakeSampler(prompt string, temperature float64) string {
	paths := []string{
		"First 3 apples then 4 more. The answer is: 7",
		"3 plus 4 equals seven. The answer is: 7",
		"Miscounted, got 6. The answer is: 6",
		"3 + 4 = 7. The answer is: 7",
	}
	return paths[rand.Intn(len(paths))]
}

func main() {
	result, err := selfConsistency("How many apples in total?", fakeSampler, 20, 0.7)
	if err != nil {
		panic(err)
	}
	fmt.Printf("winner=%s share=%.2f\n", result.Answer, result.VoteShare)
	fmt.Println(result.Distribution)
}
```

Java, Rust, and Swift are omitted here by choice, not oversight. The pattern
is a thin orchestration layer over any model API's completion call plus a
counting map, and it carries no language-specific idiom the way, for
example, a Visitor pattern carries a double-dispatch idiom that differs
sharply between a language with pattern matching and one without. The three
languages above demonstrate the pattern's one genuinely variable
implementation concern, concurrent fan-out of the N sampling calls, across
a callback-based runtime, a thread-pool-based runtime, and a goroutine-based
runtime respectively, and a fourth or fifth language would repeat the same
shape with different concurrency primitives rather than reveal a new
structural idea.
