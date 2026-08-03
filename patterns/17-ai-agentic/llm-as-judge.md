---
name: LLM as Judge
slug: llm-as-judge
family: 17-ai-agentic
category: AI Agentic
aliases: [LLM-as-a-Judge, Model-Graded Evaluation, AI Judge, Autorater]
first_described: "Zheng, Chiang, Sheng, Zhuang, Wu, Zhuang, Lin, Li, Li, Xing, Zhang, Gonzalez, Stoica 2023"
maturity: established
related: [reflexion, evaluator-optimizer, self-consistency, self-rag, input-guardrails, output-guardrails, chain-of-thought, react]
incompatible_with: []
verified: 2026-08-02
---

# LLM as Judge

## 1. Name, aliases, and lineage

The canonical name in this catalog is LLM as Judge, matching the term the
industry settled on, LLM-as-a-Judge. The technique is a language model,
prompted with a rubric, that produces a score, a label, or a preference over
one or more candidate outputs, in place of a human rater or a fixed metric.

The term was coined and systematically studied in Lianmin Zheng, Wei-Lin
Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin,
Zhuohan Li, Dacheng Li, Eric P. Xing, Hao Zhang, Joseph E. Gonzalez, and Ion
Stoica, "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena," submitted
9 June 2023, revised 24 December 2023, https://arxiv.org/abs/2306.05685
(verified 2026-08-02). The paper introduces MT-Bench, a multi-turn question
set, and analyzes preference data from Chatbot Arena, a crowdsourced
head-to-head voting platform, to test whether a strong LLM (GPT-4 at the
time) agrees with human raters closely enough to stand in for them. It
reports that GPT-4 reaches over 80 percent agreement with human preferences,
the same level at which humans agree with each other, and it names the three
biases that recur through the rest of this entry, position bias, verbosity bias,
and self-enhancement bias.

The technique itself predates the name. Yang Liu, Dan Iter, Yichong Xu,
Shuohang Wang, Ruochen Xu, and Chenguang Zhu, "G-Eval, NLG Evaluation using
GPT-4 with Better Human Alignment," submitted 29 March 2023, revised 23 May
2023, https://arxiv.org/abs/2303.16634 (verified 2026-08-02), used GPT-4 with
chain-of-thought prompting and a form-filling scoring template to grade
summaries and dialogue months before the Zheng paper's terminology existed,
and reported a Spearman correlation of 0.514 with human judgment on
summarization, ahead of the prior automatic metrics it compared against.
Earlier still, Yuntao Bai and 50 co-authors at Anthropic, "Constitutional AI,
Harmlessness from AI Feedback," submitted 15 December 2022,
https://arxiv.org/abs/2212.08073 (verified 2026-08-02), used a model to
compare pairs of responses against a written set of principles and trained a
reward model on the resulting preferences, a technique the paper names
Reinforcement Learning from AI Feedback, RLAIF. RLAIF is a training-time
sibling of LLM-as-judge, not the same thing, see the distinction below.

Three roles get called "judge" in practice and confusing them produces
mismatched designs.

An **evaluation-time judge** grades finished outputs after generation, for a
test report, a CI gate, or an online guardrail. It never touches the weights
of the model it grades. This entry is about that role.

A **training-time reward model** is a judge whose verdicts, usually pairwise
preferences, are distilled into a scalar-output model used as the reward
signal inside reinforcement learning, as in the Constitutional AI paper
above. Once trained, a reward model is usually a small classifier, not a
prompted LLM, though the preference labels that trained it came from one.

A **self-critique judge** sits inside generation itself, grading a draft and
feeding the critique back to the same generation loop before the human ever
sees an output. That shape is the Reflexion and Evaluator-Optimizer patterns,
which reuse an LLM-as-judge call as their internal evaluator step rather than
being a distinct technique.

## 2. Problem and context

A team ships a feature whose output is open-ended text, a chat reply, a
document summary, a retrieval-augmented answer, or an autonomous agent's
final report. They need a repeatable answer to whether an output is good, on
every pull request, every prompt change, and every model upgrade, across
hundreds or thousands of test cases at once.

Exact-match and n-gram metrics such as BLEU or ROUGE fail this job because
the target text is not a single correct string. Two paraphrases with the same
meaning score differently, and a lexically similar but factually wrong answer
can score well. Rule-based checks, a regex, a JSON schema validator, a
numeric tolerance, only apply where the correctness criterion is mechanical,
and most of what makes a chat reply or a summary good, helpfulness, tone,
faithfulness to a source document, coherence, is not mechanical.

Human review does grade these dimensions well, but it does not fit inside a
build pipeline. A person reading a hundred summaries takes hours, costs real
money per review, and produces raters who disagree with each other on
subjective calls, so the "ground truth" itself has noise. A team that wants a
result on every commit within minutes, at a cost measured in cents rather
than analyst-hours, needs something faster than a person and better than a
string metric.

The context in which LLM-as-judge becomes the right tool has this shape. The
quality dimension is genuinely subjective or requires reasoning over meaning
rather than surface form, a reference answer either does not exist or is only
one of many acceptable answers, and the team can tolerate a probabilistic,
occasionally wrong verdict in exchange for coverage across far more test
cases than a human budget allows. Outside that context, a cheaper and more
reliable check usually exists, and dimension 4 names when to reach for it
instead.

## 3. Forces

**Cost against coverage.** A human reviewer is the highest-fidelity signal
available and the most expensive per sample. A rule-based metric is nearly
free and covers unlimited samples but only for mechanical criteria. An LLM
judge sits between the two, one model call per graded sample, cheap enough to
run on a full regression suite, not free enough to run on every user request
without thought.

**Correlation with human judgment against determinism.** The reason to use a
judge at all is that it tracks human preference on open-ended text far better
than a string metric does, GPT-4 reaching over 80 percent agreement with
human raters and G-Eval reaching a 0.514 Spearman correlation on
summarization, both cited in dimension 1. That correlation is not perfect and
is not stable, the same prompt and rubric can return a different score after
a silent model version change, which a deterministic rule-based check never
does.

**Bias against low deployment cost.** The judge is favored because setting up
a prompt and a rubric is far cheaper than training a purpose-built classifier
or recruiting a rater pool. What it sacrifices is independence from the biases of
the underlying model, position bias, verbosity bias, and self-enhancement
bias, discussed at length in dimension 11.

**Explainability against latency.** A chain-of-thought judge produces a
written rationale alongside its score, which a plain classifier or a reward
model does not, useful for debugging why a case failed. Producing that
rationale costs additional tokens and time on every graded sample, and a
rationale is itself text a downstream reader can be misled by, see the
prompt-injection failure mode in dimension 11.

**Team topology.** A judge turns evaluation criteria into a natural-language
rubric that a product manager or a domain expert can read and edit directly,
rather than a metric implementation only an engineer can change. That
accessibility is also the risk, a rubric nobody calibrates against real human
labels can drift from what users actually want while its dashboard stays
green.

**Gameability against optimization power.** Used as a training or
prompt-optimization signal, a judge is powerful because it grades along
dimensions no cheap metric reaches. It is dangerous for the same reason, an
optimization loop that targets the judge's score can learn to satisfy the
judge's specific weaknesses instead of the underlying quality it stands in
for, a failure OpenAI's evaluation documentation names "grader hacking,"
https://developers.openai.com/api/docs/guides/graders (verified 2026-08-02).

## 4. Applicability and non-applicability

Reach for LLM-as-judge when the following hold.

- The output is open-ended text and no single reference answer captures every
  acceptable response, a chat reply, a summary, a retrieval-augmented answer,
  or an agent's final report.
- The quality dimension is subjective or requires reasoning over meaning,
  tone, helpfulness, faithfulness to a source, coherence, or adherence to a
  specific instruction that a regex or schema cannot express.
- The team needs a result across hundreds or thousands of test cases inside a
  build pipeline, faster and cheaper than a human review pass would allow.
- Two model versions, two prompts, or two system configurations need a
  pairwise preference comparison rather than an absolute score, the Chatbot
  Arena and MT-Bench style of evaluation.
- The output needs to feed a self-critique or refinement loop, Reflexion or
  Evaluator-Optimizer, where the judge's verdict drives another attempt in
  the same session.
- A specific, narrow, mostly binary property needs an online check at request
  time, such as a toxicity or personal-data classifier gating a response
  before it reaches a user, where the low-latency guardrail specialization
  of this pattern applies.

Do NOT reach for LLM-as-judge in these cases, and the reason matters more
than the rule.

- **A deterministic check already exists for the criterion.** If the answer
  can be graded by exact match, a numeric tolerance, a schema validator, or a
  unit test passing, use that. A judge is strictly worse here, slower, more
  expensive, and non-deterministic where a rule-based check is instant and
  reproducible.
- **The decision carries legal, medical, or financial liability with no
  human sign-off.** A judge's verdict is a probabilistic estimate from a
  language model, not a certified expert opinion, and treating it as the
  final arbiter in a domain requiring accountable human judgment creates
  liability exposure the pattern cannot discharge.
- **The action is high-consequence and irreversible, and the judge would be
  the sole gate.** Self-enhancement bias and grader hacking, both discussed
  below, mean a judge alone is not a safe final check before an
  irreversible production action, a financial transfer, a destructive
  database migration, or an autonomous agent's write access to a live
  system. Pair it with a deterministic guardrail or a human approval step.
- **Request-time latency and cost cannot absorb an extra full model call.**
  An LLM judge in the hot path of every user request adds one or more model
  calls to that request's latency and bill. Put general-purpose judging in
  an offline batch pipeline, and reserve online, per-request judging for the
  narrowest guardrail case that specifically needs it.
- **The available judge model is not more reliable than the model being
  graded, for this task.** A judge that reasons worse than the system under
  test on the criterion in question cannot discriminate a good answer from a
  bad one and will produce noise that looks like signal.
- **The system under test can see and manipulate the judge's own prompt.**
  In an adversarial setting, untrusted content the judge reads becomes an
  injection surface, discussed under prompt injection in dimensions 11 and
  17. A judge deployed without treating graded content as untrusted input is
  not safe in that setting.
- **A flake-free regression suite is the goal.** Where a test must produce
  the exact same pass or fail on every run, a snapshot test or a fixed rule
  is the honest tool. A judge's non-determinism, even at low sampling
  temperature and even pinned to one model version, is a poor fit for a gate
  that must never flap.

## 5. Structure

Six participants, named by the role each plays in the evaluation, not by a
generic class name.

- **Subject.** The system under test that produced the output being graded,
  a chat model, a RAG pipeline, or an agent. The Subject is external to the
  judging apparatus and the judge never has write access back into it.
- **Candidate.** One or more outputs produced by the Subject for a given
  input, the thing under evaluation. In pairwise mode there are exactly two
  candidates, Candidate A and Candidate B.
- **Reference.** An optional gold answer or supporting context used to
  ground the verdict. Present in reference-based grading, absent in
  reference-free grading, where the judge reasons from the input and its own
  knowledge alone.
- **Rubric.** The explicit evaluation instructions given to the judge, a
  scoring scale, a set of named criteria, or a pass and fail definition. The
  rubric is the one artifact a non-engineer can read and edit, and the one
  most responsible for whether the judge's verdicts mean anything.
- **Judge.** A language model prompted with the Rubric, the Candidate, and
  optionally the Reference, that returns a Verdict. The Judge is usually,
  though not necessarily, a different model instance or a different model
  family than the Subject, for reasons covered under self-enhancement bias.
- **Verdict.** The structured result of one judge call, a score, a label, a
  ranking, or a pairwise winner, ideally accompanied by a written rationale
  when chain-of-thought grading is used.

Two supporting participants sit around the core five.

- **Runner.** The surrounding evaluation framework that iterates the test
  dataset, invokes the Subject to obtain Candidates, builds the judge prompt
  from the Rubric and Reference, dispatches the Judge call, parses the
  Verdict, and aggregates Verdicts into a report or a metric.
- **Calibration set.** A small, human-labeled dataset held separate from the
  main test dataset, used once before trusting a Judge in production and
  periodically afterward, to measure how well the Judge's verdicts agree with
  real human judgment. Without this participant, a Judge is an unvalidated
  assumption wearing a green dashboard.

## 6. ASCII structure diagram

```
   +----------------------+
   |     Calibration      |   human-labeled, used to
   |          set         |   validate the Judge once,
   +----------------------+   re-checked periodically
              |
              v measures agreement
   +----------------------+          +----------------------+
   |        Runner        | grades  |        Judge         |
   |----------------------|--------->|----------------------|
   | iterate dataset       |          | reads Rubric +       |
   | call Subject           |          | Candidate(s) +       |
   | build judge prompt     |          | Reference (opt.)     |
   | parse + aggregate      |<---------| returns Verdict       |
   +----------------------+ Verdict  +----------------------+
        |            ^                          ^
        | invokes    | Candidate(s)             |
        v            |                          |
   +----------------------+          +----------------------+
   |        Subject       |          |        Rubric        |
   | (system under test)  |          | (scale, criteria,    |
   +----------------------+          |  pass/fail def.)     |
                                      +----------------------+
                                                 ^
                                                 |
                                      +----------------------+
                                      |       Reference       |
                                      |   (optional, grounds   |
                                      |    reference-based)    |
                                      +----------------------+
```

## 7. Dynamics

Pointwise grading is the simplest flow. The Runner pulls a test case, calls
the Subject to obtain a single Candidate, builds a prompt from the Rubric
plus Candidate plus optional Reference, calls the Judge, and parses a scalar
score or label back into the report.

Pairwise grading, the shape MT-Bench and Chatbot Arena popularized, compares
two Candidates and asks the Judge to choose a winner or declare a tie. Because
position bias means the same pair can score differently depending on which
Candidate sits in slot A, a careful Runner runs the comparison twice with
the Candidates swapped and only keeps a winner when both orderings agree,
falling back to a tie otherwise. That swap-and-confirm step is the mechanic
the code examples in this entry implement directly.

```
Runner               Subject            Judge (Rubric, Reference)
  |                     |                        |
  |-- generate(input) ->|                        |
  |<-- Candidate A ------|                        |
  |-- generate(input) ->|                        |
  |<-- Candidate B ------|                        |
  |                     |                        |
  |-- compare(A, B) --------------------------->  |
  |<-- Verdict(winner=A, rationale) -------------|
  |                     |                        |
  |-- compare(B, A) --------------------------->  |  (position swapped)
  |<-- Verdict(winner=B, rationale) -------------|  (B in slot A now
  |                     |                        |   means original A won)
  |                     |                        |
  |-- normalize + compare orderings               |
  |     agree  -> keep winner                     |
  |     differ -> record as tie, flag bias         |
  |                     |                        |
  |-- aggregate into report / metric               |
```

A third shape, listwise ranking, sends several Candidates in one call and
asks the Judge to order them, trading one larger call for N pairwise calls,
at the cost of a harder-to-parse response and a bigger position-bias surface
across more than two slots.

## 8. Implementation variants

**Pointwise scalar.** The Judge returns a number on a fixed scale, commonly
a 1 to 5 Likert scale for subjective qualities such as tone or empathy.
Anthropic's evaluation documentation gives exactly this shape as a worked
example, https://platform.claude.com/docs/en/test-and-evaluate/eval-tool
(verified 2026-08-02), and states explicitly that it is generally best
practice to use a different model to evaluate than the model used to
generate the output being evaluated.

**Pointwise binary or classification.** The Judge returns a label rather
than a number, pass or fail, or whether a response contains a named
property such as personal data. Cheapest to parse and to calibrate, because
agreement with a human label is a simple match rate rather than a
correlation.

**Pairwise preference.** The Judge compares two Candidates and returns a
winner or a tie, the MT-Bench and Chatbot Arena shape from dimension 1. Best
suited to A and B testing between two model versions or two prompt
revisions where an absolute score is less informative than which one is
better.

**Reference-based grading.** The Judge is given a gold answer alongside the
Candidate and grades similarity or correctness against it. Stronger when a
reference genuinely captures the target, weaker when the reference is only
one of several acceptable answers, where the Judge can start rewarding
surface resemblance to the reference instead of correctness, the reference
leakage failure mode in dimension 11.

**Reference-free grading.** The Judge grades from the input and the
Candidate alone, with no gold answer. LangSmith documents both modes and
recommends reference-free LLM-as-judge specifically for grading live
production traffic where no reference exists ahead of time,
https://docs.langchain.com/langsmith/evaluation (verified 2026-08-02).

**Rubric decomposition, form-filling.** Rather than one combined score, the
Judge fills in several named sub-criteria fields in one structured response,
the approach G-Eval uses, and the Runner combines the sub-scores. This
produces a more auditable Verdict at the cost of a longer prompt and
response.

**Claim decomposition.** The Judge, or a first pass of it, breaks the
Candidate into atomic factual claims, then verifies each claim against
supporting context independently, aggregating the fraction of supported
claims into one score. Ragas implements exactly this for its faithfulness
metric in retrieval-augmented generation evaluation,
https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/
(verified 2026-08-02), where an answer is scored as the number of claims
supported by retrieved context divided by the total number of claims.

**Chain-of-thought grading.** The Judge is instructed to reason in writing
before producing a score, which both G-Eval and the OpenAI score-model
grader use, https://developers.openai.com/api/docs/guides/graders (verified
2026-08-02). The written reasoning improves grading reliability and gives a
human reviewer something to audit, at the cost of extra tokens and a
rationale field that itself becomes an injection surface if left untrusted.

**Ensemble or jury of judges.** Multiple, ideally heterogeneous, judge
models each grade the same Candidate and their Verdicts are combined by
majority vote or averaging, reducing the influence of any single model's
self-enhancement bias, since a model favoring its own family's style is
outvoted by judges from other families.

**Fine-tuned specialist judge.** Rather than prompting a general-purpose
model, an open model is fine-tuned specifically on rubric-plus-response-to-
score pairs to act as a judge. Seungone Kim and 10 co-authors, "Prometheus,
Inducing Fine-grained Evaluation Capability in Language Models," submitted
12 October 2023, revised 9 March 2024, accepted at ICLR 2024,
https://arxiv.org/abs/2310.08491 (verified 2026-08-02), report a 13-billion
parameter open model reaching a Pearson correlation of 0.897 with human
evaluators against GPT-4's 0.882, removing dependence on a closed API's
cost and versioning while accepting custom rubrics at inference time.

**Programmatic pre-filter.** A cheap, deterministic check runs first, a
schema validator, a length check, a keyword filter, and only the subset that
passes, or that specifically needs subjective judgment, is sent to the LLM
Judge. This bounds the per-sample cost of the pattern to the cases where a
rule genuinely cannot answer the question.

## 9. Known production uses

**LMSYS Chatbot Arena and MT-Bench.** The foundational study of the pattern
itself, Zheng et al. 2023, cited in dimension 1, ran GPT-4 as a judge against
tens of thousands of human votes collected through the Chatbot Arena
crowdsourced comparison platform and established the technique's viability
by measuring its agreement with those human votes directly.

**OpenAI Evals, the score_model grader.** OpenAI's evaluation product
ships a grader type that sends a custom prompt to a chosen model, receives a
structured response with a numeric result and a reasoning trace, and
truncates the result to a configured range, documented at
https://developers.openai.com/api/docs/guides/graders (verified
2026-08-02), which also names the "grader hacking" risk discussed in
dimension 3.

**Anthropic's evaluation documentation.** Anthropic documents LLM-based
grading for tone, empathy, context utilization, and binary classification of
sensitive content such as protected health information, recommending a
different model for grading than for generation,
https://platform.claude.com/docs/en/test-and-evaluate/eval-tool (verified
2026-08-02).

**LangSmith's LLM-as-judge evaluators.** LangChain's evaluation product
names the technique directly, "LLM-as-judge," as one of its offline and
online evaluator types, distinguishing reference-based offline grading
against a labeled dataset from reference-free online grading of live
production traces, https://docs.langchain.com/langsmith/evaluation (verified
2026-08-02).

**Ragas faithfulness metric.** The open-source retrieval-augmented
generation evaluation library Ragas uses an LLM judge to decompose a
generated answer into claims and verify each against retrieved context,
scoring faithfulness as the supported fraction,
https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/
(verified 2026-08-02).

**Constitutional AI, RLAIF.** Anthropic's Constitutional AI paper, cited in
dimension 1, uses a model to compare pairs of responses against written
principles and trains a reward model on the resulting AI-generated
preferences, the training-time sibling of the evaluation-time pattern this
entry covers, https://arxiv.org/abs/2212.08073 (verified 2026-08-02).

**AlpacaEval, and its length-controlled correction.** Stanford's AlpacaEval
benchmark uses an LLM judge for automatic pairwise preference measurement
against a reference model. Yann Dubois, Balazs Galambosi, Percy Liang, and
Tatsunori B. Hashimoto, "Length-Controlled AlpacaEval, A Simple Way to Debias
Automatic Evaluators," submitted 6 April 2024, revised 10 March 2025,
https://arxiv.org/abs/2404.04475 (verified 2026-08-02), documents the
benchmark's own verbosity bias and corrects it with a regression that
controls for response length, raising the benchmark's Spearman correlation
with Chatbot Arena from 0.94 to 0.98.

## 10. Consequences

Positive.

- Scales subjective evaluation from a small human-reviewed sample to
  thousands of test cases run automatically on every prompt or model change,
  turning a manual review pass into a build-pipeline gate.
- Correlates with human judgment on open-ended text far better than n-gram
  metrics, GPT-4 reaching over 80 percent agreement with human raters in the
  MT-Bench study, and G-Eval reaching a 0.514 Spearman correlation on
  summarization, both cited in dimension 1.
- Produces an inspectable, written rationale when chain-of-thought grading
  is used, giving a reviewer something concrete to read when a case fails,
  rather than a bare number.
- Reaches quality dimensions no deterministic check can, faithfulness to a
  source document, tone, coherence, and adherence to a detailed instruction.
- Enables online guardrails at request time when scoped narrowly, letting a
  system reject a harmful or off-policy output before it reaches a user.

Negative.

- Inherits the underlying model's biases, position bias, verbosity bias, and
  self-enhancement bias, and can make them worse if left uncorrected, with the
  self-enhancement effect measured at roughly 10 percent for GPT-4 grading
  its own outputs and 25 percent for Claude-v1 grading its own outputs in
  one independent bias analysis, https://eugeneyan.com/writing/llm-evaluators/
  (verified 2026-08-02).
- Non-deterministic even at a low sampling temperature, and a silent
  provider-side model version change can shift the grading distribution
  without any change to the rubric or the code, invalidating historical
  score comparisons, a failure named judge drift in dimension 11.
- Gameable when used as an optimization target, "grader hacking" per
  OpenAI's own documentation, where a system optimized against a judge
  learns to exploit the judge's specific weaknesses rather than genuinely
  improve.
- Costs real money and latency per graded sample, one additional model call
  at minimum, more when chain-of-thought, self-consistency sampling, or an
  ensemble of judges is used.
- Adds an unaudited trust layer when shipped without a calibration step, a
  dashboard that looks green while its agreement with actual users is
  unknown and untested.

## 11. Failure modes and misuse

**Position flip.** Symptom. A pairwise comparison declares Candidate A the
winner, and swapping only the order the two Candidates are presented in,
with no change to their content, flips the verdict to Candidate B. Cause.
Position bias in the underlying judge model, which favors whichever slot it
tends to prefer regardless of content, documented at roughly 50 percent bias
rate for one model and 70 percent for another in the independent analysis
cited above. Fix. Run every pairwise comparison twice with the Candidates
swapped, and only keep a winner when both orderings agree, treating a
disagreement as a tie, the mechanic implemented in the code examples below.

**Verbosity inflation.** Symptom. A longer, padded response consistently
outscores a shorter, equally correct one across many test cases. Cause.
Verbosity bias, the judge correlates response length with thoroughness or
effort, documented as a systematic confound in the AlpacaEval benchmark
before its length-controlled correction, cited in dimension 9. Fix. Apply a
length-regression correction to the raw scores, instruct the judge
explicitly to penalize unnecessary length in the rubric, or cap response
length before candidates ever reach the judge.

**Self-preference, rubber-stamping.** Symptom. A model scores measurably
higher when the judge is an instance of the same model or model family than
when the judge is an independent model, on identical outputs. Cause.
Self-enhancement bias, shared stylistic and lexical priors between generator
and judge that the judge mistakes for quality. Fix. Use a judge from a
different model family than the system under test, and where budget allows,
use a jury of heterogeneous judges and combine their verdicts.

**Judge drift after a silent model update.** Symptom. A score history that
tracked steadily for weeks shows a step change on a specific date, with no
corresponding code, prompt, or rubric change on that date. Cause. The
judge model was served through an API alias that the provider silently
upgraded, and the same rubric now produces a different score distribution
from the same underlying quality of candidates. Fix. Pin the judge to an
explicit, dated model snapshot rather than a rolling alias, and re-run a
fixed calibration set whenever that pin changes, before trusting any new
score as comparable to the history before it.

**Grader hacking during optimization.** Symptom. A metric a training or
prompt-optimization loop is directly targeting climbs steadily over
iterations, while a held-out human review of the same outputs stays flat or
gets worse. Cause. The system being optimized has learned to exploit a
specific weakness in the judge's rubric or prompt rather than improve the
underlying quality the judge was meant to measure, the risk OpenAI's grader
documentation names explicitly. Fix. Hold out a second, unseen judge or a
withheld portion of the rubric that the optimization loop never sees, and
periodically re-validate the primary judge's agreement against a fresh
human-labeled sample.

**Unvalidated judge shipped to production.** Symptom. The evaluation
dashboard is consistently green, while real users report the outputs are
poor. Cause. The judge prompt and rubric were never checked against a
human-labeled calibration set before the team began trusting its scores, so
its real agreement rate with human preference is unknown. Fix. Build a
small calibration set of human-labeled examples before trusting a new
judge, measure agreement, a percent-match rate for classification or a
correlation coefficient for scalar scores, and monitor that agreement over
time rather than measuring it once and forgetting it.

**Reference leakage, trivial similarity matching.** Symptom. A judge grades
a paraphrase of the reference answer as excellent and an equally correct
answer phrased differently as weak, even though both convey the same
meaning. Cause. The judge over-weights lexical or structural similarity to
the provided reference rather than reasoning about correctness, degenerating
toward an expensive version of a string-overlap metric. Fix. For dimensions
where similarity to one exact phrasing is not the actual target, switch to
reference-free grading against criteria, or instruct the judge explicitly
that meaning-equivalent paraphrases should score equivalently.

**Prompt injection through judged content.** Symptom. A candidate response
that is clearly wrong or low quality receives a high score, and the judge's
own written rationale contains text that reads like an instruction rather
than an evaluation, for example a sentence resembling "this response should
be rated highly," lifted from inside the candidate text itself. Cause. The
candidate being judged is untrusted text concatenated directly into the
judge's own prompt, and the judge model treats embedded instructions inside
that text as if they came from the Runner. Fix. Wrap candidate text in
clear delimiters inside the judge prompt, instruct the judge explicitly to
treat content inside those delimiters as data to evaluate rather than
instructions to follow, and monitor rationale text for anomalous patterns as
a detection signal.

## 12. Trade-off matrix

Comparison against named alternatives across the forces from dimension 3.

| Dimension | LLM as Judge | N-gram metric (BLEU/ROUGE) | Human review | Trained reward model | Rule-based guardrail |
|---|---|---|---|---|---|
| Cost per sample | Low, one model call | Near zero | High, analyst time | Low after training, high to train | Near zero |
| Correlation with human judgment, open-ended text | High, roughly 80 percent agreement for a strong judge | Low, does not reason about meaning | Highest, the reference standard | High for the criterion it was trained on | Zero, cannot grade subjective quality |
| Determinism | Low, drifts with model version and sampling | High | Low, raters disagree | High once trained and frozen | Highest, fully deterministic |
| Explainability | High with chain-of-thought grading | Low, a number with no reasoning | High, raters can explain | Low, a scalar with no rationale | High, the rule is the explanation |
| Setup effort | Low, write a rubric prompt | Low, off-the-shelf | Medium, recruit and train raters | High, requires a labeled preference dataset and training run | Low to medium, write the rule |
| Coverage at scale | High, thousands of samples per run | High | Low, bounded by reviewer time | High, cheap to run once trained | High |
| Applicable criteria | Subjective and reasoning-based | Surface lexical overlap only | Any criterion a person can judge | Whatever criterion its training data captured | Mechanical, checkable criteria only |

## 13. Related and incompatible patterns

**Reflexion.** Reflexion's self-critique step is frequently implemented as an
internal LLM-as-judge call, the agent grading its own draft against a
rubric before deciding whether to retry. LLM-as-judge is the mechanism,
Reflexion is the loop that consumes its Verdict to trigger another attempt.

**Evaluator-Optimizer.** This is the clearest structural relative. The
Evaluator role in that pattern is, in the overwhelming majority of real
implementations, an LLM-as-judge call, and the two entries describe the same
mechanism from different angles, this one focused on the judging technique
itself, that one focused on the generate-evaluate-refine loop it sits
inside.

**Self-Consistency.** A distinct technique that reduces variance by
sampling multiple generations from one model and taking a majority vote over
the answers themselves, with no separate judge model involved. It composes
with LLM-as-judge rather than replacing it, a judge can itself be run with
self-consistency, sampling several judge verdicts and taking the majority,
to reduce the judge's own variance.

**Self-RAG.** Uses reflection tokens the generating model produces about its
own retrieval and generation decisions, a lightweight, inline cousin of an
external judge, deciding whether to retrieve or to critique without a
separate judge call.

**Input Guardrails and Output Guardrails.** These are the online, usually
binary, low-latency specialization of LLM-as-judge, running per-request
rather than in offline batch evaluation, most often as a pointwise
classifier judging one narrow property, toxicity, personal data, policy
violation, rather than a general-purpose quality score.

**Chain-of-Thought.** The judge itself usually uses chain-of-thought
reasoning internally before producing a score, as both G-Eval and the
OpenAI score-model grader do, making CoT a technique the judge is built on
rather than a pattern the judge composes with externally.

**ReAct.** Agent trajectories, sequences of reasoning and tool calls, are
commonly evaluated after the fact by an LLM judge assessing whether the
tool-use sequence was correct and efficient, an offline evaluation use of
this pattern applied to the ReAct pattern's output.

No pattern in this catalog is incompatible with LLM-as-judge in its structure.
The tension worth stating plainly is scope, not incompatibility, the pattern
should not be the sole safety gate for an irreversible, high-consequence
action, where a deterministic guardrail or a human approval step belongs
alongside it rather than being replaced by it, per dimension 4.

## 14. Refactoring path in and out

Introducing the pattern into a codebase that has none of it follows this
path. Start from whatever exists, manual spot-checking or no evaluation at
all. Identify one subjective quality dimension no rule-based check can grade.
Write a minimal rubric prompt for that one dimension and run it against a
handful of examples by hand to sanity-check the wording. Build a small
human-labeled calibration set, ten to thirty examples is enough to start, and
measure the judge's agreement with those labels before trusting it further.
Add chain-of-thought reasoning to the judge prompt if the raw score alone is
hard to audit. For any pairwise use, add the position-swap-and-confirm step
from dimension 7 before trusting a single ordering. Wire the calibrated
judge into the offline batch evaluation pipeline as a CI-speed gate. Only
after that offline use is stable should a narrow, binary slice of the same
judgment graduate to an online, request-time guardrail, and only for the
specific property that genuinely needs a real-time check. If bias or cost
becomes a problem at that scale, move to a jury of heterogeneous judges or a
fine-tuned specialist judge such as the Prometheus approach in dimension 8.

Removing or scaling back the pattern follows the reverse logic. The moment a
deterministic rule becomes available for a dimension that used to need a
judge, for example a criterion narrows enough that an exact-match or schema
check now captures it, replace the judge with that rule for that slice and
keep the judge only for whatever genuinely subjective remainder is left. A
judge whose calibration has drifted below an agreed agreement threshold, per
dimension 15, should be retired or replaced through a versioned, side-by-side
comparison against its replacement on the same calibration set, never
swapped silently, because a silent swap makes every score before and after
the swap incomparable without anyone noticing why.

## 15. Testing and verification

The judge itself is a component that needs regression testing, not a piece
of test infrastructure exempt from being tested. Build a human-labeled
calibration set first and treat it as a fixture, running the judge against
it on a schedule and alerting when its agreement with the human labels, a
percent-match rate for classification tasks or a Cohen's kappa or Spearman
correlation for scalar scores, drops below an agreed threshold.

Pin determinism where the design allows it. Set the judge's sampling
temperature to zero or as close to zero as the model permits, pin the judge
to an explicit dated model version rather than a rolling alias, and use a
fixed, deterministic ordering for any position-swap logic so pairwise test fixtures
reproduce exactly across CI runs.

Separate the two things being tested. The Runner logic, prompt assembly,
Verdict parsing, position-swap aggregation, tie handling, is ordinary
software and should be unit tested with a stub judge that returns canned
Verdicts, exactly the FakeJudge and FirstSlotBiasedJudge test doubles used in
the code examples below, which let the position-swap-and-confirm logic be
tested deterministically without spending any real judge-call budget. The
judge model's actual correlation with human judgment is a different question,
answered only by the calibration set, never by a unit test against a stub.

Add a schema or contract test that asserts the real judge's structured
output, the score field and the rationale field, actually parses under the
live API, run this in CI before the Runner is trusted to consume its
output, catching a provider-side response-shape change before it silently
corrupts every downstream aggregation.

## 16. Observability signals

Log every judge call with enough detail to reconstruct why a Verdict
happened, the candidate identifier, the rubric version, the judge model and
its pinned version, the raw response, the parsed score, the rationale text
when present, the call latency, and the token cost.

Track the score distribution over time per rubric as a histogram or a
control chart. A sudden shift in that distribution with no corresponding
code or prompt change is the first sign of judge drift from a silent
provider-side model update, discussed in dimension 11.

Track the judge's agreement rate against periodic human spot-checks as a
continuously monitored metric rather than a one-time calibration result, so
a slow drift in real-world agreement is caught before the dashboard's other
numbers make the team assume everything is fine.

Track the parse-failure rate, the fraction of judge responses that do not
match the expected structured-output schema. A rising parse-failure rate
often precedes a behavior change in the underlying model before that change
shows up anywhere else.

For pairwise judges, track the position-agreement rate, the fraction of
comparisons where both the original and the swapped ordering agree on a
winner. A dropping position-agreement rate is a direct, cheap signal of
worsening position bias, and every comparison that fails to agree becomes a
tie rather than a silently wrong verdict.

Track cost per evaluation run as its own dashboard line. Judge calls are
frequently the largest single cost line item in an evaluation pipeline once
chain-of-thought reasoning, self-consistency sampling, or a jury of judges
is in use, and that cost tends to grow unnoticed as coverage expands.

## 17. Security and privacy implications

The judge prompt concatenates the candidate output, and often the input that
produced it, directly into a language model's context, which makes any
untrusted content inside that candidate an injection surface against the
judge itself, the prompt-injection failure mode described in dimension 11.
Treat candidate text exactly as any other untrusted content embedded in a
prompt would be treated, with clear delimiters and an explicit instruction
that content inside those delimiters is data, not instructions.

If candidate responses, references, or inputs contain personal data or
customer information, every judge call is an additional point where that
data leaves the system toward whichever provider serves the judge model.
The same data-processing agreement, residency, and retention requirements
that apply to the primary generation model apply to the judge, and a team
that has cleared its generation model for a data category has not
automatically cleared a separate judge model for the same category if the
judge runs through a different provider or a different contract.

A judge's rationale text is itself an output that downstream automation may
consume unreviewed, for example an automated gate that reads a judge's
written explanation and acts on phrases inside it. A candidate crafted to
manipulate the judge into writing a favorable-sounding rationale can smuggle
an instruction into automation that trusts that rationale text without
sanitizing it, so no automated action should be driven directly by
unreviewed rationale text.

A rubric encodes an organization's evaluation criteria, sometimes
proprietary ones, and sending that rubric to a third-party judge API on
every call is an exposure of that intellectual property equivalent to
sending any other proprietary prompt to that provider. A self-hosted or
open judge, such as the Prometheus approach in dimension 8, removes this
exposure at the cost of running and maintaining that model.

## Code examples

Three languages, all implementing the same position-swap-and-confirm
mechanic from dimension 7, the direct fix for the position-bias failure
mode in dimension 11. Each example defines a Judge abstraction, two stub
judges standing in for real model calls, a ReasonPreferringJudge that
grades honestly and a FirstSlotBiasedJudge that always favors the first
slot regardless of content, and a runner function that runs each
comparison twice with the order swapped and only trusts a winner both
orderings agree on. A real judge would replace the stub with a call to a
language model API. The runner logic around it, the part worth testing
without spending API budget, is what these examples show.

### Python

```python
"""LLM-as-Judge: pairwise position-swap runner."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Verdict:
    winner: str
    rationale: str


class Judge(Protocol):
    def compare(self, prompt: str, response_a: str, response_b: str) -> Verdict:
        ...


class ReasonPreferringJudge:
    """Stub judge. prefers whichever response contains 'because'."""

    def compare(self, prompt: str, response_a: str, response_b: str) -> Verdict:
        a_has = "because" in response_a.lower()
        b_has = "because" in response_b.lower()
        if a_has and not b_has:
            return Verdict("A", "A gives a reason, B does not.")
        if b_has and not a_has:
            return Verdict("B", "B gives a reason, A does not.")
        return Verdict("tie", "Both or neither give a reason.")


class FirstSlotBiasedJudge:
    """Stub judge exhibiting position bias. always favours the first slot."""

    def compare(self, prompt: str, response_a: str, response_b: str) -> Verdict:
        return Verdict("A", "First response chosen regardless of content.")


def position_swapped_compare(judge: Judge, prompt: str, response_a: str, response_b: str) -> Verdict:
    """Run the comparison twice with swapped order. keep a winner only on agreement."""
    first = judge.compare(prompt, response_a, response_b)
    second = judge.compare(prompt, response_b, response_a)
    normalize = {"A": "B", "B": "A", "tie": "tie"}
    second_in_first_frame = normalize[second.winner]
    if first.winner == second_in_first_frame:
        return first
    return Verdict(
        "tie",
        f"Order-dependent verdict (first={first.winner}, second={second.winner}); treated as tie.",
    )


def main() -> None:
    prompt = "Why does ice float on water?"
    response_a = "Ice floats because it is less dense than liquid water."
    response_b = "Ice floats on water."

    reasoned = position_swapped_compare(ReasonPreferringJudge(), prompt, response_a, response_b)
    print(f"reasoned judge -> winner={reasoned.winner} rationale={reasoned.rationale}")
    assert reasoned.winner == "A"

    biased = position_swapped_compare(FirstSlotBiasedJudge(), prompt, response_a, response_b)
    print(f"biased judge   -> winner={biased.winner} rationale={biased.rationale}")
    assert biased.winner == "tie"


if __name__ == "__main__":
    main()
```

### TypeScript

```typescript
interface Verdict {
  winner: "A" | "B" | "tie";
  rationale: string;
}

interface Judge {
  compare(prompt: string, responseA: string, responseB: string): Verdict;
}

class ReasonPreferringJudge implements Judge {
  compare(prompt: string, responseA: string, responseB: string): Verdict {
    const aHas = responseA.toLowerCase().includes("because");
    const bHas = responseB.toLowerCase().includes("because");
    if (aHas && !bHas) return { winner: "A", rationale: "A gives a reason, B does not." };
    if (bHas && !aHas) return { winner: "B", rationale: "B gives a reason, A does not." };
    return { winner: "tie", rationale: "Both or neither give a reason." };
  }
}

class FirstSlotBiasedJudge implements Judge {
  compare(_prompt: string, _responseA: string, _responseB: string): Verdict {
    return { winner: "A", rationale: "First response chosen regardless of content." };
  }
}

function positionSwappedCompare(
  judge: Judge,
  prompt: string,
  responseA: string,
  responseB: string,
): Verdict {
  const first = judge.compare(prompt, responseA, responseB);
  const second = judge.compare(prompt, responseB, responseA);
  const normalize: Record<Verdict["winner"], Verdict["winner"]> = { A: "B", B: "A", tie: "tie" };
  const secondInFirstFrame = normalize[second.winner];
  if (first.winner === secondInFirstFrame) return first;
  return {
    winner: "tie",
    rationale: `Order-dependent verdict (first=${first.winner}, second=${second.winner}); treated as tie.`,
  };
}

function assertEqual(actual: string, expected: string, label: string): void {
  if (actual !== expected) {
    throw new Error(`${label}: expected ${expected}, got ${actual}`);
  }
}

function main(): void {
  const prompt = "Why does ice float on water?";
  const responseA = "Ice floats because it is less dense than liquid water.";
  const responseB = "Ice floats on water.";

  const reasoned = positionSwappedCompare(new ReasonPreferringJudge(), prompt, responseA, responseB);
  console.log(`reasoned judge -> winner=${reasoned.winner} rationale=${reasoned.rationale}`);
  assertEqual(reasoned.winner, "A", "reasoned judge");

  const biased = positionSwappedCompare(new FirstSlotBiasedJudge(), prompt, responseA, responseB);
  console.log(`biased judge   -> winner=${biased.winner} rationale=${biased.rationale}`);
  assertEqual(biased.winner, "tie", "biased judge");
}

main();
```

### Go

```go
package main

import (
	"fmt"
	"strings"
)

type Verdict struct {
	Winner    string
	Rationale string
}

type Judge interface {
	Compare(prompt, responseA, responseB string) Verdict
}

type ReasonPreferringJudge struct{}

func (ReasonPreferringJudge) Compare(prompt, responseA, responseB string) Verdict {
	aHas := strings.Contains(strings.ToLower(responseA), "because")
	bHas := strings.Contains(strings.ToLower(responseB), "because")
	if aHas && !bHas {
		return Verdict{"A", "A gives a reason, B does not."}
	}
	if bHas && !aHas {
		return Verdict{"B", "B gives a reason, A does not."}
	}
	return Verdict{"tie", "Both or neither give a reason."}
}

type FirstSlotBiasedJudge struct{}

func (FirstSlotBiasedJudge) Compare(prompt, responseA, responseB string) Verdict {
	return Verdict{"A", "First response chosen regardless of content."}
}

func positionSwappedCompare(judge Judge, prompt, responseA, responseB string) Verdict {
	first := judge.Compare(prompt, responseA, responseB)
	second := judge.Compare(prompt, responseB, responseA)
	normalize := map[string]string{"A": "B", "B": "A", "tie": "tie"}
	if first.Winner == normalize[second.Winner] {
		return first
	}
	return Verdict{
		"tie",
		fmt.Sprintf("Order-dependent verdict (first=%s, second=%s); treated as tie.", first.Winner, second.Winner),
	}
}

func main() {
	prompt := "Why does ice float on water?"
	responseA := "Ice floats because it is less dense than liquid water."
	responseB := "Ice floats on water."

	reasoned := positionSwappedCompare(ReasonPreferringJudge{}, prompt, responseA, responseB)
	fmt.Printf("reasoned judge -> winner=%s rationale=%s\n", reasoned.Winner, reasoned.Rationale)
	if reasoned.Winner != "A" {
		panic("expected reasoned judge to pick A")
	}

	biased := positionSwappedCompare(FirstSlotBiasedJudge{}, prompt, responseA, responseB)
	fmt.Printf("biased judge   -> winner=%s rationale=%s\n", biased.Winner, biased.Rationale)
	if biased.Winner != "tie" {
		panic("expected biased judge run to normalize to tie")
	}
}
```

## 18. References

1. Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu,
   Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric P. Xing, Hao Zhang,
   Joseph E. Gonzalez, Ion Stoica. "Judging LLM-as-a-Judge with MT-Bench and
   Chatbot Arena." Submitted 9 June 2023, revised 24 December 2023.
   https://arxiv.org/abs/2306.05685
   Verified 2026-08-02. Source of the term, MT-Bench, the Chatbot Arena
   preference dataset, the 80 percent human-agreement figure, and the
   position, verbosity, and self-enhancement bias taxonomy.
2. Yang Liu, Dan Iter, Yichong Xu, Shuohang Wang, Ruochen Xu, Chenguang Zhu.
   "G-Eval, NLG Evaluation using GPT-4 with Better Human Alignment."
   Submitted 29 March 2023, revised 23 May 2023.
   https://arxiv.org/abs/2303.16634
   Verified 2026-08-02. Source of the chain-of-thought, form-filling
   grading method and the 0.514 Spearman correlation figure.
3. Yuntao Bai et al. "Constitutional AI, Harmlessness from AI Feedback."
   Submitted 15 December 2022. https://arxiv.org/abs/2212.08073
   Verified 2026-08-02. Source of Reinforcement Learning from AI Feedback,
   RLAIF, the training-time sibling distinguished in dimension 1.
4. OpenAI. "Graders." Developer documentation.
   https://developers.openai.com/api/docs/guides/graders
   Verified 2026-08-02. Source of the score_model grader description and
   the "grader hacking" terminology used in dimensions 3, 9, and 11.
5. Anthropic. "Using the evaluation tool." Claude Developer Platform
   documentation.
   https://platform.claude.com/docs/en/test-and-evaluate/eval-tool
   Verified 2026-08-02. Source of the Likert-scale grading example and the
   recommendation to use a different model to grade than to generate.
6. LangChain. "Evaluation." LangSmith documentation.
   https://docs.langchain.com/langsmith/evaluation
   Verified 2026-08-02. Source of the offline reference-based versus online
   reference-free LLM-as-judge distinction.
7. Ragas. "Faithfulness." Metrics documentation.
   https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/
   Verified 2026-08-02. Source of the claim-decomposition judge variant and
   the Ragas production use.
8. Yann Dubois, Balazs Galambosi, Percy Liang, Tatsunori B. Hashimoto.
   "Length-Controlled AlpacaEval, A Simple Way to Debias Automatic
   Evaluators." Submitted 6 April 2024, revised 10 March 2025.
   https://arxiv.org/abs/2404.04475
   Verified 2026-08-02. Source of the AlpacaEval production use, the
   verbosity bias correction, and the 0.94 to 0.98 correlation improvement.
9. Seungone Kim et al. "Prometheus, Inducing Fine-grained Evaluation
   Capability in Language Models." Submitted 12 October 2023, revised
   9 March 2024, accepted ICLR 2024.
   https://arxiv.org/abs/2310.08491
   Verified 2026-08-02. Source of the fine-tuned specialist judge variant
   and its correlation figures against GPT-4.
10. Eugene Yan. "Evaluating the Effectiveness of LLM-Evaluators."
    https://eugeneyan.com/writing/llm-evaluators/
    Verified 2026-08-02. Source of the specific position-bias and
    self-enhancement-bias percentage figures cited in dimensions 10 and 11.
