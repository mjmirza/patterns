---
name: Golden Dataset Leakage
slug: golden-dataset-leakage
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Golden Set Leakage, Eval Set Leakage, Holdout Leakage, Benchmark Contamination, Test Set Contamination, Answer Key Leakage]
first_described: "No single catalog origin. The lineage runs through data leakage in data mining, adaptive holdout reuse, public leaderboard overfitting, and benchmark contamination in language model evaluation"
maturity: established
related: [golden-dataset, evaluation-suite, llm-as-judge, data-leakage, golden-master, differential-testing, metamorphic-testing]
incompatible_with: [training-on-the-test-set, public-answer-key-feedback]
verified: 2026-08-02
---

# Golden Dataset Leakage

## 1. Name, aliases, and lineage

Golden Dataset Leakage is the anti-pattern in which cases reserved for
evaluation, or their labels, rubrics, gold patches, expected outputs, or
derived signals, become inputs to the system being evaluated. The name in this
catalog is deliberately narrower than data leakage. Data leakage covers any
information unavailable at prediction time that enters model building. Golden
Dataset Leakage covers the specific failure where the artifact trusted as an
independent change detector stops being independent.

The common aliases come from different communities. Classical machine learning
teams call it test set leakage, holdout leakage, or train test contamination.
Benchmark teams call it benchmark contamination. Competition communities often
talk about public leaderboard overfitting. LLM product teams often say eval set
leakage, golden set leakage, answer key leakage, or prompt contamination when
the examples appear in prompts, fine tuning records, retrieval corpora, or
developer notes.

There is no single origin paper for the name. The closest older lineage is
Kaufman, Rosset, Perlich, and Stitelman's 2012 paper "Leakage in Data Mining.
Formulation, Detection, and Avoidance", which defines leakage as target
information that is not legitimately available to learn from, and gives
"learn predict separation" as a data management response
(https://cir.nii.ac.jp/crid/1361699995332168704, verified 2026-08-02).
The holdout reuse lineage is Dwork, Feldman, Hardt, Pitassi, Reingold, and
Roth's 2015 work on adaptive data analysis, which states that repeated
adaptive reuse of a holdout set can lead to overfitting to that holdout
(https://arxiv.org/abs/1506.02629, verified 2026-08-02).

The LLM lineage is newer but now central. Brown et al.'s GPT-3 paper identifies
methodological issues for language models trained on broad web corpora and
discusses overlap between pretraining data and benchmark development or test
sets (https://arxiv.org/abs/2005.14165, verified 2026-08-02). HELM keeps a
static contamination file that marks model and benchmark group combinations
where contamination is known or suspected
(https://github.com/stanford-crfm/helm/blob/main/src/helm/benchmark/static/contamination.yaml,
verified 2026-08-02). Li and Flanigan's 2024 AAAI paper studies task
contamination across language model evaluation and reports evidence that older
datasets can score differently from post cutoff datasets after controlling for
difficulty (https://ojs.aaai.org/index.php/AAAI/article/view/29808, verified
2026-08-02).

Engineering judgement. The word golden is useful because it names the thing
that lost its authority. The model may still be correct on the cases. The
damage is that the score no longer estimates behavior on unseen work.

## 2. Problem and context

A team builds a golden dataset to make model, prompt, ranking, or agent changes
measurable. The dataset has inputs and expected outputs, labels, reference
documents, test patches, rubrics, or human decisions. The runner holds the
system constant, changes one candidate, and compares outcomes. That design
only works when the candidate has not learned the evaluation cases in advance.

The problem appears once the golden set becomes valuable enough to influence
behavior. Engineers inspect failing cases and paste them into tickets. Prompt
authors add examples from failures into few-shot prompts. A fine tuning job
uses traces exported from the same evaluation store. A retrieval index contains
the answer key. A benchmark is public, so future models train on web pages,
repositories, blog posts, release notes, discussion threads, or code examples
that contain the benchmark items. A competition exposes a public score often
enough that participants adapt to the feedback rather than the hidden task.

scikit-learn's documentation describes the classical form: data leakage occurs
when information unavailable at prediction time is used while building the
model, creating optimistic estimates and worse behavior on novel data
(https://scikit-learn.org/stable/common_pitfalls.html, verified 2026-08-02).
Golden Dataset Leakage is the same shape with a higher organizational cost.
The leaked artifact is not an incidental feature column. It is the team's
release gate, public claim, or model selection signal.

The context is any system where an evaluation set influences model selection,
prompt selection, release approval, or public claims. The anti-pattern is not
limited to gradient training. A hand-tuned prompt can overfit a fixed set
through repeated inspection. A routing policy can be edited until the golden
suite passes. A code agent can pass if the gold patch or hidden tests appear in
context. OpenAI's 2026 SWE-bench Verified analysis says the benchmark became
increasingly contaminated because the problems and repositories are open
source, broadly used, and discussed, and that frontier models were able to
reproduce gold patches or task specifics for some tasks
(https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/,
verified 2026-08-02).

The failure is attractive because each local action looks helpful. A failed
golden case is useful training material. A public benchmark improves
reproducibility. A leaderboard creates feedback. A notebook that mixes train
and test data is shorter. The anti-pattern is the unchecked combination of
those actions, which turns the evaluator into part of the training loop.

The most common product setting is a model or agent that changes weekly. A
team upgrades a hosted model, edits a system prompt, changes a retrieval
filter, or adds a tool. The release owner runs the golden suite and sees a
score. If the score is low, the team reads failures. If the failure cases are
then copied into the next prompt, included in a fine tuning file, or indexed as
documentation, the next score is partly a memory check. The test still runs.
The report still has numbers. The missing property is independence.

This is why Golden Dataset Leakage is more subtle than a bad train test split
in a notebook. In the notebook case, the defect is often visible in code: a
call to `fit` happens before a split, or a transformer learns from all rows.
In the product case, the leak may cross tools and weeks. The case starts in an
eval database, appears in a Slack thread, becomes a Jira acceptance example,
gets pasted into a prompt playground, lands in a checked-in prompt template,
then appears inside the next model card as evidence of improvement. No single
developer thinks they trained on the test set. The organization did.

## 3. Forces

Engineering judgement. These forces explain why careful teams still leak their
own golden sets.

- **Latency of iteration.** Leakage favors speed. Using the failing golden case
  as the next prompt example or fine tuning row gives fast local improvement.
  The cost is a score that no longer predicts unseen cases.
- **Coupling.** Leakage couples development to the evaluator. The system learns
  the quirks of the fixed set instead of the real task distribution.
- **Consistency.** A fixed golden set favors repeatable release gates. The same
  stability also makes it easier to memorize.
- **Operability.** A leaked set gives green dashboards while user complaints
  rise. Operators lose a trusted alarm.
- **Cost.** Fresh human labels and private holdouts are expensive. Reusing the
  same set is cheap, so budget pressure pushes toward reuse.
- **Team topology.** A single team owning prompts, training data, and evals can
  move fast, but there is no natural custody boundary. Separate eval ownership
  slows changes and improves independence.
- **Cognitive load.** Keeping separate train, dev, public test, private test,
  canary, and incident replay sets is mentally heavy. Collapsing them is simple
  and wrong.
- **Privacy.** Keeping private cases private protects eval validity and can
  reduce exposure. It also means fewer people can debug failures directly.

The anti-pattern favors short feedback loops and visible progress. It
sacrifices measurement validity, long term trust, and the ability to compare
systems across time.

## 4. Applicability and non-applicability

Reach for this anti-pattern name when these conditions appear.

- A golden dataset, benchmark, holdout, private test set, public leaderboard,
  hidden unit test suite, or eval rubric is used to select or approve a model,
  prompt, agent, retriever, ranker, or policy.
- The evaluated system can access the cases, labels, answers, rubrics, gold
  patches, expected outputs, or closely derived summaries during training,
  tuning, prompting, retrieval, tool use, or repeated manual edits.
- The reported score is treated as evidence about unseen production behavior,
  not only as a score on that exact fixed artifact.
- The same people or automation own both the optimizer and the evaluator with
  no custody barrier, audit trail, or fresh holdout.
- A public benchmark is used as the release claim for a private application
  whose real task distribution differs from the benchmark.

Non-applicability list.

- **Training examples that are explicitly not evaluation cases.** A labeled
  corpus used for supervised fine tuning is not leaked because it is used for
  training. It becomes leakage when the same cases, or labels derived from
  them, are later presented as independent evaluation.
- **Developer inspection after a failed release gate, followed by case
  retirement.** Reading a failed case is normal debugging. It becomes leakage
  if the case remains in the official score after the system was tuned against
  it.
- **Public benchmark score reported as a public benchmark score.** There is no
  deception if the claim is limited to that artifact. The anti-pattern starts
  when the score is treated as proof of unseen application quality.
- **Golden master tests for deterministic refactoring.** A golden master file
  is allowed to be known to the code under test when it is a change detector for
  deterministic code. The risk here concerns systems that can learn, retrieve,
  or be tuned to answer the evaluation cases.
- **A small hand-check list used only as a smoke test.** If nobody treats it as
  a generalization estimate, leakage is less harmful. It may still be a weak
  test suite, but it is not this anti-pattern.
- **A training serving skew issue with no evaluation set involved.**
  TensorFlow Transform exists partly to keep training and serving transforms
  consistent (https://www.tensorflow.org/tfx/guide/transform, verified
  2026-08-02). That is adjacent, not the same failure.
- **A benchmark retired after contamination is found.** Once the team stops
  using the contaminated score for claims or release gates, the active
  anti-pattern has been removed.

## 5. Structure

The anti-pattern has six recurring participants.

- **Golden artifact.** The reserved evaluation material. It may be a table of
  labeled examples, a hidden solution file, a benchmark test split, an answer
  key, a set of gold patches, a judge rubric, or a collection of private canary
  prompts.
- **Optimizer.** The process that changes the system. It may be gradient
  training, fine tuning, prompt editing, retrieval corpus construction, model
  selection, hyperparameter search, human patching, or a leaderboard feedback
  loop.
- **System under evaluation.** The candidate model, prompt, agent, retriever,
  ranker, classifier, or code generator.
- **Evaluation runner.** The program that executes cases, computes metrics,
  and records a score.
- **Leakage path.** The path by which the golden artifact reaches the
  optimizer or system. Common paths are shared storage, copied tickets, prompt
  examples, fine tuning exports, RAG indexes, public web publication, cached
  traces, test names, release notes, and repeated score feedback.
- **Decision maker.** The human or automation that trusts the score for merge,
  deploy, model selection, procurement, public reporting, or risk assessment.

The harmful relationship is not that the golden artifact exists. The harmful
relationship is a backward edge from the evaluator into the optimizer. Once that
edge is present, the score measures a closed loop.

## 6. ASCII structure diagram

```
        allowed path                         decision path
  +-------------------+   run cases    +--------------------+
  | Golden artifact   |--------------->| Evaluation runner  |
  | cases, labels,    |                | metrics, reports   |
  | answers, rubrics  |                +---------+----------+
  +-------------------+                          |
           |                                      v
           | forbidden path             +-------------------+
           | labels, answers, cases     | Decision maker    |
           v                            | merge, deploy,    |
  +-------------------+   produces      | public claim      |
  | Optimizer         |---------------> +-------------------+
  | train, tune, edit |
  +---------+---------+
            |
            v
  +-------------------+
  | System under eval |
  | model, prompt,    |
  | agent, retriever  |
  +-------------------+

  The lower left edge is the leak. The evaluator has become a trainer.
```

## 7. Dynamics

The runtime story has two forms. The first is direct leakage, where material
from the set enters the candidate before evaluation. The second is adaptive
leakage, where repeated scores steer changes until the candidate specializes to
the set.

```
Direct leakage

Golden store       Export job       Training or prompt job       Candidate
    |                 |                      |                       |
    |-- cases+labels->|                      |                       |
    |                 |-- mixed with train ->|                       |
    |                 |                      |-- builds candidate -->|
    |                 |                      |                       |
    |-- evaluation cases ------------------------------------------->|
    |<-------------------------- score looks high -------------------|


Adaptive leakage

Engineer        Runner        Golden set        Candidate
   |              |               |                 |
   |-- run A ---->|-- cases ----->|                 |
   |              |-------------->|-- prompts ----->|
   |<-- failures -|               |                 |
   |-- edit prompt for failed case ---------------->|
   |-- run B ---->|-- same cases ------------------>|
   |<-- better ---|                                 |
   |-- repeat until score is high ----------------->|

   The candidate may never see labels directly. The loop still trains on
   evaluation feedback.
```

OpenAI's SWE-bench Verified article illustrates the direct form at benchmark
scale: open source tasks and gold patches became broadly present in the
training ecosystem, and models could recover task-specific details
(https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/,
verified 2026-08-02). Kaggle's public and private leaderboard design
illustrates a mitigation for the adaptive form: the public leaderboard gives
feedback on a sample, while final ranking uses hidden private data
(https://www.kaggle.com/docs/competitions, verified 2026-08-02).

## 8. Implementation variants

**Direct train test merge.** The simplest form. Evaluation rows are included in
training or fine tuning. scikit-learn's pitfall guide warns against fitting
preprocessing or selection on all data before splitting, because test data then
influences the model (https://scikit-learn.org/stable/common_pitfalls.html,
verified 2026-08-02). In golden dataset work, the same mistake happens when an
export job says "all labeled cases" and includes heldout cases.

**Answer key in prompt context.** The model does not receive gradients, but it
receives exemplars, rubrics, hidden tests, gold patches, or expected outputs in
the prompt. For agents, this often occurs through task instructions, few-shot
examples, scratchpad imports, or developer notes copied from failure analysis.

**Retrieval corpus contamination.** RAG systems can ingest support tickets,
evaluation reports, judge explanations, benchmark solutions, or public writeups
that contain answers. The generator appears to solve the case, but the retriever
handed it the solution.

**Adaptive manual overfitting.** Engineers run the same fixed set after every
prompt edit, read the failures, and edit until those failures pass. This is not
malicious. It is ordinary test driven work applied to an artifact whose purpose
was to estimate unseen performance. Dwork et al.'s holdout reuse work gives the
statistical shape of this danger for adaptive analysis
(https://arxiv.org/abs/1506.02629, verified 2026-08-02).

**Public benchmark contamination.** The benchmark is published, discussed, and
mirrored. Future training corpora pick up the cases or near duplicates. Brown
et al. discuss overlap checks for GPT-3 benchmarks
(https://arxiv.org/abs/2005.14165, verified 2026-08-02), and HELM records
known contamination relationships in a machine readable file
(https://github.com/stanford-crfm/helm/blob/main/src/helm/benchmark/static/contamination.yaml,
verified 2026-08-02).

**Leaderboard probing.** Participants submit many variants and adapt to the
visible score. Kaggle's documentation separates public feedback from private
ranking and warns that a high public score does not guarantee a high private
score (https://www.kaggle.com/docs/competitions, verified 2026-08-02).

**Judge rubric leakage.** In LLM evaluation, the expected answer may stay
hidden while the rubric leaks. A model trained or prompted on the rubric can
learn phrases the judge rewards rather than the underlying task. The result is
a high score under that judge and weak behavior under a fresh human review.

**Metadata leakage.** Case IDs, filenames, issue URLs, timestamps, or branch
names reveal the answer. SWE-bench style tasks contain repository and pull
request metadata by design, and their dataset documentation includes fields
such as issue URL, PR URL, patch, and test patch
(https://www.swebench.com/SWE-bench/guides/datasets/, verified 2026-08-02).
Those fields are useful for research, but they must not enter the context of a
solver being scored as if it lacks the solution.

**Exposure through explanations.** Many eval tools store judge rationales,
human reviewer notes, or issue triage comments next to each case. Those notes
can be more revealing than the reference answer because they say why one answer
is accepted and another is rejected. A prompt author who reads the notes can
tune to the evaluator's private preferences. A retrieval indexer that ingests
the notes can give the model the decision rule. Treat explanations as part of
the golden artifact, not as harmless metadata.

**Exposure through synthetic expansion.** A team may ask a model to generate
variants of failed golden cases and then use the variants for training. This
is safer than copying the original cases only if the variants are separated
from blind scoring and if they do not include answer text or identifiers from
the blind set. Otherwise the synthetic set is a paraphrased leak. Exact hash
scans will miss it, so the process needs lineage fields that record which
source case produced each synthetic case.

## 9. Known production uses

This is an anti-pattern, so the useful production evidence is named systems
that either suffer the failure or build guardrails around it.

**Kaggle competitions.** Kaggle prediction competitions use public and private
leaderboards. The documentation says the public leaderboard is visible during a
competition and based on a sample of test data, while private ranking uses the
remainder, and warns against chasing the public leaderboard
(https://www.kaggle.com/docs/competitions, verified 2026-08-02). This is a
production mitigation for adaptive leakage through score feedback.

**scikit-learn Pipeline.** scikit-learn documents data leakage as an
overoptimistic estimate caused by information unavailable at prediction time
entering model building, and recommends splitting first, never fitting on the
test data, and using `Pipeline` so fit and transform calls happen on the
correct subsets (https://scikit-learn.org/stable/common_pitfalls.html,
verified 2026-08-02). The library pattern is a production countermeasure for
preprocessing leakage.

**TensorFlow Transform in TFX.** TensorFlow Transform computes full pass feature
engineering values during training and emits a graph used consistently at
training and serving time. The TFX guide says this helps avoid training serving
skew and is meant for transformations that need a full pass over training data
(https://www.tensorflow.org/tfx/guide/transform, verified 2026-08-02). It is
not a golden set leakage detector, but it is a named production mechanism for
keeping learned preprocessing out of ad hoc data paths.

**HELM.** Stanford CRFM's HELM evaluation framework maintains contamination
metadata for model and benchmark group combinations
(https://github.com/stanford-crfm/helm/blob/main/src/helm/benchmark/static/contamination.yaml,
verified 2026-08-02). That file is production evaluation infrastructure:
contamination is represented as data the evaluator can account for, not as a
footnote.

**SWE-bench Verified.** OpenAI introduced SWE-bench Verified in 2024 as a
human-validated subset of SWE-bench, built by screening original test samples
with professional developers and filtering problematic cases
(https://openai.com/index/introducing-swe-bench-verified/, verified
2026-08-02). In 2026, OpenAI said it no longer uses SWE-bench Verified for
frontier coding capability claims because contamination and remaining test
issues had weakened the signal
(https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/,
verified 2026-08-02). This is a named lifecycle example: a useful benchmark can
age into an invalid release metric.

## 10. Consequences

Positive local consequences.

- Development appears faster because known failures can be made green quickly.
- Release gates become less noisy in the short term because the candidate has
  been specialized to the gate.
- Public benchmark numbers rise, which can help comparison against other teams
  using the same flawed benchmark.
- Debugging feels easier because engineers can inspect exact examples and tune
  against them.

Negative system consequences.

- The score no longer estimates behavior on unseen inputs.
- Regressions escape to users while dashboards stay green.
- Model selection favors memorization, benchmark familiarity, or prompt
  tailoring over task competence.
- The team loses the ability to compare old and new candidates fairly.
- Public claims become brittle once a fresh private set is introduced.
- Security review becomes harder because the system may contain hidden copies
  of sensitive golden cases.
- The organization may continue investing in a model, prompt, or benchmark
  after its main evidence has lost meaning.

Engineering judgement. The worst consequence is not one bad release. It is loss
of trust in measurement. Once engineers believe the gate can be gamed, every
future green score needs a second conversation.

## 11. Failure modes and misuse

Engineering judgement. These triples are written as operational symptoms, not
as a taxonomy from a single source.

**Symptom.** Offline score rises release after release, while live complaint
rate, human escalation rate, refund rate, or manual override rate also rises.
**Cause.** The golden set leaked into prompt tuning or training, so the model
learned the test distribution better than the production distribution.
**Fix.** Retire the exposed cases from the official score, sample a fresh blind
set from recent production traffic, and block train or prompt jobs from reading
the blind set.

**Symptom.** A candidate performs much better on public benchmark cases than on
fresh cases written in the same style by an independent reviewer.
**Cause.** Public benchmark contamination or repeated benchmark tuning.
**Fix.** Report the public score as public benchmark performance only, then use
a private benchmark for release decisions.

**Symptom.** A RAG trace shows the expected answer, judge explanation, or gold
patch in retrieved context.
**Cause.** Evaluation reports, case files, issue solutions, or benchmark
writeups were indexed with ordinary product documents.
**Fix.** Put evaluation artifacts in a storage class excluded from retrieval
indexing, and add an index audit that searches for case IDs and answer hashes.

**Symptom.** A code agent passes hidden tests only when the task ID or issue URL
is present, and fails a semantically equivalent task with renamed metadata.
**Cause.** Metadata leakage. The model or retriever maps identifiers to known
solutions.
**Fix.** Evaluate with redacted IDs, shuffled filenames where possible, and
fresh tasks that postdate the training cutoff.

**Symptom.** A prompt contains examples that are byte-for-byte identical to
official eval cases.
**Cause.** Failed cases were copied into few-shot examples without retiring
them from the gate.
**Fix.** Maintain a case registry with states such as blind, debug, train, and
retired. A case may move from blind to debug or train, but not back to blind.

**Symptom.** Cross validation, public leaderboard, or dev set scores improve
with every tiny tuning pass, while final hidden set score drops.
**Cause.** Adaptive overfitting to visible feedback. Kaggle's public private
leaderboard design exists to reduce this problem
(https://www.kaggle.com/docs/competitions, verified 2026-08-02).
**Fix.** Limit visible submissions, choose models using local validation with a
predeclared protocol, and reserve a hidden final set.

**Symptom.** A judge gives high scores to verbose answers that repeat rubric
keywords, while human reviewers reject them.
**Cause.** Rubric leakage or judge gaming.
**Fix.** Keep judge rubrics narrow and private when the judge is part of a
competitive score, then calibrate against human labels on a blind sample.

**Symptom.** An eval store export named "all labeled data" feeds fine tuning,
and no one can reconstruct which rows were blind at the time.
**Cause.** Dataset custody was not versioned.
**Fix.** Version every case with purpose, owner, creation time, exposure state,
and content hash. Make training exports require an allowlist query.

## 12. Trade-off matrix

| Force | Golden Dataset Leakage | Strict Blind Holdout | Public Benchmark Only | Rotating Private Canary | K-fold Cross Validation | Human Review Board |
|---|---|---|---|---|---|---|
| Latency of iteration | Fast locally | Slower, fewer visible failures | Fast, easy to run | Medium, refresh cost | Medium | Slow |
| Coupling | Optimizer coupled to evaluator | Low coupling | High to public artifact | Low if private | Medium, folds influence tuning | Low to data, high to reviewers |
| Consistency across time | Score stable but invalid | Stable until retirement | Stable but may age | Less stable by design | Stable per run protocol | Reviewer drift risk |
| Operability | Green dashboards can lie | Trusted release alarm | Weak app signal | Strong drift signal | Good training estimate | Good qualitative signal |
| Cost | Cheap until failure | Labeling and custody cost | Low direct cost | Ongoing sampling cost | Compute cost | High human cost |
| Team topology | One team can own all paths | Requires custody split | External owner | Requires eval owner | ML team owned | Cross functional |
| Cognitive load | Low at first | Higher process load | Low | Medium | Medium | High scheduling load |
| Privacy | Often poor, artifacts copied | Stronger access control | Public by definition | Strong if redacted | Depends on fold storage | Strong if governed |
| Best use | Never as evidence | Release gate | Background comparison | Production drift check | Model development | High risk final review |

Reading of the table. Leakage wins only on local speed and short term
simplicity. Strict blind holdouts and rotating private canaries cost more, but
they preserve the reason the golden set exists.

## 13. Related and incompatible patterns

**Golden Dataset.** Golden Dataset is the positive pattern. Golden Dataset
Leakage is its most damaging failure mode. A team that adopts a golden set
without custody rules has built half the pattern.

**Evaluation Suite.** An evaluation suite composes many checks: unit tests,
golden datasets, fuzz tests, judge evaluations, latency gates, and safety
checks. Leakage can affect one component while the rest remain valid. The suite
should label which scores are blind and which are debug scores.

**LLM as Judge.** A judge can grade golden cases, but the judge itself can be
gamed if its rubric or training data overlaps with the cases. Calibrate the
judge on a private human-labeled sample.

**Differential Testing.** Differential testing compares candidates against each
other. It can reduce reliance on one answer key, but if the same leaked cases
drive candidate selection, the differential score is still contaminated.

**Metamorphic Testing.** Metamorphic tests check relations among transformed
inputs. They compose well with private golden sets because paraphrases,
renamings, and perturbations can reveal memorization.

**Data Leakage.** Data Leakage is the wider ML anti-pattern. Golden Dataset
Leakage is the release-gate version with governance and trust consequences.

**Golden Master.** Golden master tests intentionally expose the reference
output to test code through source control. That is acceptable for deterministic
change detection, but dangerous when the system can learn from, retrieve, or
adapt to the reference.

**Training on the test set.** This is the direct incompatible pattern. If a case
is used for training, it cannot also be blind evidence.

**Service Locator.** A global data access layer can hide eval artifacts inside
ordinary retrieval or feature paths. The pattern is not causal, but it often
makes leakage harder to audit.

## 14. Refactoring path in and out

Introducing controls when leakage is suspected.

1. Inventory every dataset, prompt example store, retrieval corpus, fine tuning
   file, benchmark export, evaluation report, and issue tracker attachment that
   contains golden case material.
2. Assign each case one state: blind, debug, train, public, retired, or
   quarantined. If the case has ever been shown to an optimizer, it cannot be
   blind.
3. Add immutable content hashes for inputs, labels, rubrics, expected outputs,
   and solution artifacts. Use those hashes to scan training and retrieval
   inputs.
4. Split current scores into historical scores and valid blind scores. Do not
   compare them as if they were the same metric.
5. Create a fresh blind holdout sampled from recent production or newly written
   tasks. Restrict access to the minimum set of owners.
6. Move exposed cases into a debug set. They remain valuable for regression
   testing, but the report must label them as exposed.
7. Update training, prompt, and retrieval export jobs so they can read only
   allowlisted states.
8. Add a pre-run audit to the evaluation runner that checks candidate prompts,
   train files, and retrieved context for case IDs and content hashes.
9. Change release policy. A debug score may block a merge, but it may not be the
   only positive evidence for a model upgrade.

Refactoring out when a contaminated benchmark no longer earns its place.

1. Freeze the benchmark version for archival comparison only.
2. Remove it from release approval and public capability claims.
3. Keep a small compatibility run if external customers still ask for the
   number, but label it as contaminated or public.
4. Replace it with a private or newer evaluation whose creation date postdates
   the candidate's training cutoff where possible.
5. Preserve old reports so trend lines are not silently rewritten.
6. Delete train and retrieval copies of retired blind artifacts if privacy rules
   require deletion, but keep non-sensitive hashes for future scans.

## 15. Testing and verification

Engineering judgement. The testing target is the evaluation process, not the
model alone.

Test the custody boundary first. A unit test should prove that a training
export cannot select blind cases. A retrieval build test should prove that eval
artifact paths are excluded. A prompt assembly test should prove that official
eval IDs are absent from few-shot blocks. These tests are ordinary software
tests and should run in CI.

Test content overlap second. Exact hashes catch byte-for-byte leakage. Token
shingles catch near copies. Case ID scans catch metadata leakage. For public LLM
benchmarks, corpus access is often unavailable, so papers and tools use indirect
signals such as n-gram overlap, chronological comparison, prompted recall, or
fresh benchmark replication. Brown et al. discuss overlap checks in GPT-3
(https://arxiv.org/abs/2005.14165, verified 2026-08-02), and Sainz et al. call
for benchmark-level contamination measurement in NLP evaluation
(https://aclanthology.org/2023.findings-emnlp.722/, verified 2026-08-02).

Test the metric by replication. Create a small fresh set drawn from the same
task distribution and compare score gaps. If the model is far better on the old
golden set than on the fresh set, treat the old set as exposed until proven
otherwise.

Test temporal separation when dates are available. If a benchmark item, issue,
document, or answer key was public before the candidate's training cutoff, the
burden of proof moves to the team claiming the score is clean. A new benchmark
written after the cutoff is not automatically valid, since prompt tuning and
retrieval can still leak it, but it removes one large pretraining path. Li and
Flanigan's task contamination study uses chronological comparison as one line
of evidence for contamination risk
(https://ojs.aaai.org/index.php/AAAI/article/view/29808, verified
2026-08-02).

Test the human process. Review a random sample of failed and passed blind cases
after each release. The aim is not to tune the candidate directly, but to
detect case defects, stale labels, and rubric drift. If a case is discussed in
enough detail to influence tuning, move it out of blind status.

Useful test doubles are fake dataset stores, fake retrieval indexes, and
in-memory training manifests. Avoid mocks that hide the actual query filter,
because the most common bug is an export path that ignores the case state.

Verification should produce an artifact. A release should record the blind set
version, the candidate digest, the training manifest digest, the retrieval
index digest, the prompt digest, and the audit result. Without that record, a
team cannot later answer a direct question: did this model have access to these
cases before this score was reported. The artifact also changes incentives.
Engineers become less likely to paste blind cases into broad stores when they
know the release audit will scan those stores.

## 16. Observability signals

Engineering judgement. A healthy evaluation program measures the evaluator as a
production system.

Record the case state distribution for every run: blind, debug, train, public,
retired, and quarantined. A release report with no blind cases should be treated
as a smoke test, not a quality estimate. Record the dataset version, content
hash manifest, prompt version, model version, retrieval corpus version, and
training data manifest for every score.

Track overlap signals. Count exact case hash hits in training files, prompt
templates, retrieved context, and indexed documents. Count near duplicate
shingles above a declared threshold. Count case ID hits. For public benchmarks,
record whether the candidate's training cutoff and data policy make overlap
plausible.

Track score divergence. A healthy dashboard shows debug scores higher than or
equal to blind scores by a small, explainable margin, because debug cases are
known. A failing dashboard shows the debug score climbing while blind score is
flat or falling. Another failing signal is a sudden high score on old public
benchmarks paired with poor score on newly created private canaries.

Track human disagreement. If human reviewers disagree with judge labels more
often on blind cases than debug cases, the debug set may have taught the judge
or prompt writer its preferred wording. If reviewer disagreement rises across
both, the rubric is stale.

Track access. Log reads of blind artifacts, not only writes. A blind case read
by a training job, notebook, prompt export, or retrieval indexer is an incident.

## 17. Security and privacy implications

Golden Dataset Leakage is both a measurement problem and a data handling
problem. Golden cases often come from production traces, support tickets,
medical notes, legal documents, codebases, security reports, or customer
messages. If they leak into training data, prompts, logs, or retrieval indexes,
the team may have copied sensitive data into places with broader retention and
access than the original system allowed.

The attack surface is real. A vendor, competitor, or participant who can infer
or obtain the evaluation cases can specialize to them. Kaggle rules for some
competitions describe public and private test sets and state that private data
membership is not revealed to participants
(https://www.kaggle.com/competitions/repss/rules, verified 2026-08-02). The
same principle applies to internal evals: case membership is sensitive when the
score controls money, access, launch approval, or public claims.

Private golden sets also create insider risk. Engineers need enough visibility
to debug, but unrestricted read access lets any notebook, export job, or prompt
experiment contaminate the set. Use role-based access, redaction, and state
transitions. Record who viewed blind labels. Make bulk export of blind labels a
reviewed operation.

The pattern is silent on model safety by itself. A non-leaked golden set does
not prove a model is safe. It proves only that a particular evaluation signal
has a valid custody story. Safety evaluation still needs its own threat model,
red team cases, monitoring, and incident review.

Privacy review should treat movement from blind eval storage to training or
retrieval as a new data use. A support ticket that was allowed for quality
review may not be allowed for model training. A medical summary used by three
reviewers may not be allowed in a vendor hosted judge call. A codebase issue
with a private patch may not be allowed in an external benchmark transcript.
Those are policy questions outside the pattern, but the anti-pattern makes them
easy to miss because the data already feels internal.

Security review should also examine prompt injection paths. If an attacker can
write content into a corpus that later becomes both training data and eval data,
they can create cases the model learns to answer and then point to the score as
evidence. If an attacker can read blind case IDs, they can probe a model for
memorized answers. Controls that look bureaucratic in ordinary testing, such as
state labels, access logs, and export reviews, become security controls when
the score affects deployment or public trust.

## 18. References

1. Shachar Kaufman, Saharon Rosset, Claudia Perlich, Ori Stitelman. "Leakage in
   Data Mining. Formulation, Detection, and Avoidance." *ACM Transactions on
   Knowledge Discovery from Data*, 6(4), article 15, 2012. DOI
   10.1145/2382577.2382579. Metadata and abstract verified through CiNii
   Research, https://cir.nii.ac.jp/crid/1361699995332168704, verified
   2026-08-02.
2. Cynthia Dwork, Vitaly Feldman, Moritz Hardt, Toniann Pitassi, Omer
   Reingold, Aaron Roth. "Generalization in Adaptive Data Analysis and Holdout
   Reuse." arXiv:1506.02629, 2015. https://arxiv.org/abs/1506.02629, verified
   2026-08-02.
3. scikit-learn developers. "12. Common pitfalls and recommended practices."
   scikit-learn documentation. https://scikit-learn.org/stable/common_pitfalls.html,
   verified 2026-08-02.
4. Google. "The Transform TFX Pipeline Component." TensorFlow documentation.
   https://www.tensorflow.org/tfx/guide/transform, verified 2026-08-02.
5. Kaggle. "Competitions Documentation." https://www.kaggle.com/docs/competitions,
   verified 2026-08-02.
6. Kaggle. "The 3rd RePSS, Competition Rules." Section 9, determining
   leaderboard. https://www.kaggle.com/competitions/repss/rules, verified
   2026-08-02.
7. Tom B. Brown et al. "Language Models are Few-Shot Learners."
   arXiv:2005.14165, 2020. https://arxiv.org/abs/2005.14165, verified
   2026-08-02.
8. Percy Liang et al. "Holistic Evaluation of Language Models."
   arXiv:2211.09110, 2022, revised 2023. https://arxiv.org/abs/2211.09110,
   verified 2026-08-02.
9. Stanford CRFM. HELM contamination metadata,
   `src/helm/benchmark/static/contamination.yaml`.
   https://github.com/stanford-crfm/helm/blob/main/src/helm/benchmark/static/contamination.yaml,
   verified 2026-08-02.
10. Changmao Li, Jeffrey Flanigan. "Task Contamination. Language Models May Not
   Be Few-Shot Anymore." *Proceedings of the AAAI Conference on Artificial
   Intelligence*, 38(16), 18471-18480, 2024.
   https://ojs.aaai.org/index.php/AAAI/article/view/29808, verified
   2026-08-02.
11. Oscar Sainz, Jon Ander Campos, Iker Garcia-Ferrero, Julen Etxaniz, Oier
   Lopez de Lacalle, Eneko Agirre. "NLP Evaluation in trouble. On the Need to
   Measure LLM Data Contamination for each Benchmark." Findings of ACL EMNLP
   2023, pages 10776-10787.
   https://aclanthology.org/2023.findings-emnlp.722/, verified 2026-08-02.
12. OpenAI. "Introducing SWE-bench Verified." August 13, 2024.
   https://openai.com/index/introducing-swe-bench-verified/, verified
   2026-08-02.
13. OpenAI. "Why SWE-bench Verified no longer measures frontier coding
   capabilities." February 23, 2026.
   https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/,
   verified 2026-08-02.
14. SWE-bench. "Datasets." https://www.swebench.com/SWE-bench/guides/datasets/,
   verified 2026-08-02.

## Code examples

The examples implement the same small guard in three languages. They reject a
training manifest that overlaps a blind golden manifest by ID or answer hash.
This does not catch every near duplicate, but it catches the direct leak that
causes many real failures. All three samples were run or compiled locally.

### Python

```python
from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class Case:
    case_id: str
    answer: str


def digest(text: str) -> str:
    return sha256(text.strip().lower().encode("utf-8")).hexdigest()


def find_leaks(training: list[Case], blind: list[Case]) -> list[str]:
    blind_ids = {case.case_id for case in blind}
    blind_answers = {digest(case.answer) for case in blind}
    leaks: list[str] = []
    for case in training:
        if case.case_id in blind_ids:
            leaks.append(f"id:{case.case_id}")
        if digest(case.answer) in blind_answers:
            leaks.append(f"answer:{case.case_id}")
    return leaks


if __name__ == "__main__":
    train = [Case("debug-1", "refund from billing page")]
    holdout = [Case("blind-9", "cancel from account page")]
    found = find_leaks(train, holdout)
    if found:
        raise SystemExit("leakage blocked: " + ", ".join(found))
    print("no leakage found")
```

### TypeScript

```typescript
type EvalCase = {
  id: string;
  answer: string;
};

function digest(text: string): string {
  let hash = 2166136261;
  for (const char of text.trim().toLowerCase()) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16);
}

function findLeaks(training: EvalCase[], blind: EvalCase[]): string[] {
  const blindIds = new Set(blind.map((item) => item.id));
  const blindAnswers = new Set(blind.map((item) => digest(item.answer)));
  const leaks: string[] = [];

  for (const item of training) {
    if (blindIds.has(item.id)) leaks.push(`id:${item.id}`);
    if (blindAnswers.has(digest(item.answer))) {
      leaks.push(`answer:${item.id}`);
    }
  }

  return leaks;
}

const training = [{ id: "debug-1", answer: "ship in two days" }];
const blind = [{ id: "blind-7", answer: "refund to card" }];
const leaks = findLeaks(training, blind);
if (leaks.length > 0) {
  throw new Error(`leakage blocked: ${leaks.join(", ")}`);
}
console.log("no leakage found");
```

### Go

```go
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"strings"
)

type EvalCase struct {
	ID     string
	Answer string
}

func digest(text string) string {
	sum := sha256.Sum256([]byte(strings.ToLower(strings.TrimSpace(text))))
	return hex.EncodeToString(sum[:])
}

func findLeaks(training []EvalCase, blind []EvalCase) []string {
	blindIDs := map[string]bool{}
	blindAnswers := map[string]bool{}
	for _, item := range blind {
		blindIDs[item.ID] = true
		blindAnswers[digest(item.Answer)] = true
	}

	var leaks []string
	for _, item := range training {
		if blindIDs[item.ID] {
			leaks = append(leaks, "id:"+item.ID)
		}
		if blindAnswers[digest(item.Answer)] {
			leaks = append(leaks, "answer:"+item.ID)
		}
	}
	return leaks
}

func main() {
	training := []EvalCase{{ID: "debug-1", Answer: "route to tier two"}}
	blind := []EvalCase{{ID: "blind-3", Answer: "close as billing"}}
	leaks := findLeaks(training, blind)
	if len(leaks) > 0 {
		fmt.Println("leakage blocked:", strings.Join(leaks, ", "))
		os.Exit(1)
	}
	fmt.Println("no leakage found")
}
```
