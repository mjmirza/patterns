---
name: Evaluation Suite
slug: evaluation-suite
family: 17-ai-agentic
category: AI Agentic
aliases: [Eval Suite, Eval Runner, LLM Eval Pipeline, Golden Dataset Testing, Regression Eval Set]
first_described: "Wang, Singh, Michael, Hill, Levy, Bowman 2018 (GLUE benchmark); formalized as an application-development practice by OpenAI 2023 (Evals)"
maturity: established
related: [llm-as-judge, input-guardrails, output-guardrails, prompt-injection-defense, self-consistency, evaluator-optimizer, cost-guard, structured-output, react]
incompatible_with: []
verified: 2026-08-02
---

# Evaluation Suite

## 1. Name, aliases, and lineage

The canonical name in this catalog is Evaluation Suite. It names the standing
collection of test cases, a scoring method for each case, and a runner that
executes the collection against a system built on a language model, so that a
change to a prompt, a model version, a retrieval index, or an agent's tool set
produces a number instead of an impression. The industry also calls the same
thing an Eval Suite, an Eval Pipeline, a Golden Dataset, or, informally, "the
evals". This entry treats those as one pattern because they share the same
four participants regardless of the word chosen. a fixed dataset of cases, a
scorer, a runner, and a report that a team acts on.

The pattern has two lineages that met around 2023. The older one is standard
machine learning practice, splitting data into training, validation, and test
sets and reporting accuracy on the held-out set, a discipline that predates
large language models by decades. The newer, and the one this entry follows
most closely, is the benchmark-suite tradition in natural language processing.
Alex Wang, Amanpreet Singh, Julian Michael, Felix Hill, Omer Levy, and Samuel
R. Bowman published "GLUE. A Multi-Task Benchmark and Analysis Platform for
Natural Language Understanding" in 2018, introducing the General Language
Understanding Evaluation benchmark, a fixed collection of nine tasks with a
single leaderboard score, explicitly built so that a model's claim of
understanding language could be checked against a standardized suite rather
than a single cherry-picked example (Alex Wang et al., "GLUE. A Multi-Task
Benchmark and Analysis Platform for Natural Language Understanding," submitted
20 April 2018, published at ICLR 2019, https://arxiv.org/abs/1804.07461,
verified 2026-08-02). GLUE fixed the shape that every later suite reuses. a
frozen set of labeled examples, a scoring function per task, and a single
comparable number.

That shape moved from academic benchmarking into everyday application
development once teams started shipping products on top of instruction-tuned
models rather than fine-tuning a model for one narrow task. OpenAI released
Evals, an open-source framework and registry of test suites for checking model
and application behavior, describing the creation of a good eval as one of the
most effective things a team building on language models can do, because
without it, testing a prompt change is left to hand-checking a handful of
outputs (OpenAI, "openai/evals" repository, https://github.com/openai/evals,
verified 2026-08-02). Evals popularized two ideas that now define the pattern
in application contexts rather than research contexts. first, that a suite
should mix cheap deterministic scorers (an exact string match, a substring
check, a fuzzy match) with model-graded scorers for anything a fixed rule
cannot judge. second, that the suite belongs in the same place as unit tests,
run on every change, not as a research artifact produced once before a paper
is submitted.

The word "evaluation" is used elsewhere in this catalog for a single scored
judgment (see llm-as-judge). Evaluation Suite is the container. it is the
standing test collection and its running discipline, not any one scoring
method inside it.

## 2. Problem and context

A function built from deterministic code either compiles or it does not, and
a passing unit test today keeps passing tomorrow unless the code under test
changes. A system built around a language model call has neither guarantee.
The same prompt against the same model can return a different answer on two
consecutive calls, a model provider can silently update the weights behind a
version string, a retrieval index can shift what documents are returned for
the same query as new content is indexed, and a one-line change to a system
prompt intended to fix one failure can quietly break three others that nobody
happened to try by hand before shipping. The team building the feature has no
compiler, and no fixed oracle, to tell them whether the change they made
left the product better or worse.

The context in which this becomes a real problem, not a theoretical one, is
any product surface where the language model's output reaches a person or
another automated system and the team intends to keep changing the prompt,
the model, the retrieved context, or the available tools over time. A single
demo of a chatbot answering three questions correctly says nothing about the
thousand slightly different phrasings a real user will type, and a developer
manually re-checking those three questions after every prompt edit does not
scale past the first release. The problem sharpens further once more than one
person can edit the prompt or the pipeline, because a change one engineer
believes is an improvement for their test case can be a regression for a case
they never tried, and without a suite nobody discovers the regression until a
support ticket arrives.

Evaluation Suite exists to give this class of change the same guarantee a
compiler gives deterministic code. not a proof of correctness, because
language model output is not provably correct in the way a type system is
provably sound, but a repeatable, numeric, comparable answer to the question
"did this change make the suite of things we already know matter better,
worse, or unchanged."

## 3. Forces

**Coverage against cost.** Every additional case in the suite adds a small
amount of confidence and a real, recurring dollar and time cost, because each
case is at minimum one call to a model, and a model-graded case is at least
two. A suite of five cases run on every commit is nearly free and catches
almost nothing. A suite of five thousand cases run on every commit catches
much more and can turn a two-minute pull request check into a twenty-minute,
non-trivial bill. The pattern is designed for a team to tier this trade-off
deliberately rather than resolve it once and leave it fixed.

**Determinism against realism.** A case scored with an exact string match is
cheap, fast, and produces the same verdict every run, but most interesting
model behavior, an answer's tone, whether it correctly declined an unsafe
request, whether a summary preserved the right facts, cannot be reduced to a
string match. Scoring those cases with another model call (see llm-as-judge)
restores the ability to judge open-ended output at the cost of introducing a
second source of nondeterminism and a second model's own blind spots into the
measurement.

**Automatability against subjective quality.** Some qualities a team cares
about, whether a response would embarrass the brand, whether a support
answer would satisfy an actual frustrated customer, resist both a fixed rule
and a model-graded rubric, and only a human reading transcripts catches them
reliably. A suite that automates everything it can and routes the remainder
to periodic human review balances signal against the throughput a human
review process can sustain.

**Signal against noise.** A flaky case, one whose pass or fail flips between
identical runs because of model nondeterminism or a scorer with a fragile
matching rule, erodes trust in the whole suite faster than a genuinely
missing case does, because a team that has been burned by false alarms stops
reading the report at all. Keeping the signal-to-noise ratio high, by fixing
temperature, retrying transport failures without silently retrying content
failures, and separating brittle exploratory cases from the must-pass core,
is a standing cost of running the pattern well.

**Iteration speed against statistical confidence.** A developer wants a
verdict on their change in seconds so they can keep iterating on a prompt.
A statistically meaningful verdict, especially on a case scored by a
nondeterministic judge, needs enough repeated trials or enough independent
cases to say the observed difference is not noise. Tiering the suite into a
fast smoke subset and a slower, larger nightly or pre-release run is the
common resolution, trading immediate feedback for a smaller, faster-changing
signal and periodic, slower, higher-confidence signal.

**Maintenance against product drift.** A golden dataset frozen at the moment
a feature shipped slowly stops representing what real users actually ask as
the product, its users, and their expectations change, and an unmaintained
suite gives a false sense of safety exactly when the product has moved
furthest from what the suite tests. Feeding real production failures back
into the suite is what keeps this force from winning by default (see
dimension 7, the authoring loop).

## 4. Applicability and non-applicability

Reach for an Evaluation Suite when:

- A feature's core behavior comes from a language model call, and the team
  expects to keep editing the prompt, swapping the model, or changing the
  retrieved context after the first release.
- More than one person can change the prompt, the pipeline, or the model
  configuration, so an individual change needs a check against behavior other
  people rely on, not only the author's own manual spot-check.
- The team is deciding whether to upgrade a model version, switch providers,
  or change a retrieval or tool-use strategy, and needs an objective before
  and after comparison rather than a subjective impression from a handful of
  tries.
- A production incident or a support ticket has already revealed one wrong
  answer, and the team wants that specific failure to be caught automatically
  if it ever recurs, rather than relying on someone remembering to re-test it
  by hand.
- The system is agentic, meaning it plans, calls tools, or takes multiple
  steps, and a change to one step's prompt can alter the trajectory the whole
  agent takes, which a single-turn manual check will not reveal (see
  dimension 8, agent trajectory evals).
- A regulated or safety-sensitive surface (content moderation, medical or
  legal information, financial guidance) needs a documented, repeatable,
  auditable record that specific known-bad behaviors are checked before every
  release, not asserted from memory after the fact.

Do NOT reach for an Evaluation Suite when:

- The system under test is a one-off exploratory prototype the team expects
  to throw away before it reaches a second user, where the cost of writing
  and maintaining cases exceeds any value returned before the code is
  discarded.
- The behavior in question is fully deterministic and already covered by
  ordinary unit tests, an eval scorer designed for model nondeterminism adds
  overhead and a second source of flakiness to something a plain assertion
  already checks exactly.
- The team is treating a suite's pass rate as a formal correctness proof
  rather than a statistical sample. an evaluation suite estimates behavior
  over the cases it contains, it does not verify behavior over every possible
  input the way a type checker or a formal specification does, and presenting
  a ninety-eight percent pass rate as "the feature is correct" misstates what
  was measured.
- There is no labeled data and no way to construct even a small rubric for
  what a correct answer looks like, meaning the team cannot yet say, even in
  principle, what "better" means for this task. Writing cases against an
  undefined notion of correctness produces numbers that look precise and mean
  nothing; the prerequisite work is agreeing on the rubric first.
- The plan is to replace all human review of a high-stakes, low-volume
  decision (an individual medical, legal, or safety determination) with suite
  pass rate alone. A suite is a regression net across the population of known
  cases, not a substitute for a qualified reviewer looking at the one decision
  in front of them.
- Every case in the suite requires a live, paid call to a proprietary model
  and the team's iteration loop needs sub-second feedback, in which case the
  right move is a small, offline, deterministic smoke subset first, with the
  full model-graded suite reserved for a slower gate, rather than abandoning
  the pattern.

## 5. Structure

**Case.** A single input plus everything needed to judge the output. an
input prompt or conversation, optionally an expected output or a set of
acceptable outputs, optionally a rubric description for a model-graded scorer,
and metadata (an identifier, tags for filtering, the source of the case, for
example "production incident 2026-04-11"). A case is the unit of the suite;
everything else exists to run and judge cases at scale.

**Case Registry.** The versioned collection of cases, stored so that adding,
removing, or editing a case is itself a reviewable change, most commonly a
file or a small set of files under version control alongside the code, or a
database with its own change history for suites large enough to need one.

**Target, or System Under Test.** The thing being evaluated. a single prompt
template plus a model call, a full retrieval-augmented pipeline, a multi-step
agent, or an entire product endpoint. The suite treats the target as a
function from a case's input to an output, regardless of how many internal
steps produced that output.

**Scorer, or Grader.** A function that takes a case and the target's output
and returns a pass or fail, or a numeric score, or both. A suite commonly
mixes several scorer kinds across its cases. deterministic scorers (exact
match, substring, regular expression, JSON schema validation, a unit-test
style assertion against structured output), reference-based metrics (a
similarity score against a known-good answer), and model-graded scorers that
delegate the judgment to a separate language model call (see llm-as-judge for
the internal structure of that call).

**Runner, or Orchestrator.** The component that iterates the registry,
invokes the target for each case, applies the matching scorer, collects
timing and cost, and handles retries for transport failures (a timeout, a
rate limit) without silently retrying a case whose failure is a genuine wrong
answer. The runner is also where concurrency and per-run cost limits live,
because running thousands of cases serially against a live model is slow, and
running them all in parallel with no limit can trip a provider's rate limit
or run past a budget.

**Reporter, or Aggregator.** The component that turns a list of per-case
results into suite-level numbers. a pass rate, an average score, a cost
total, a latency distribution, and a list of the specific cases that failed
this run, so a person reading the report can go straight to the failing
examples rather than re-deriving them from raw logs.

**Baseline Store.** A saved copy of a prior run's report, kept so a new run
can be diffed against it. The baseline is what turns a single number ("eighty
seven percent passed") into a decision ("this is two points worse than the
version currently in production, block the merge").

**CI Gate.** The policy that consumes the diff against the baseline and
decides whether the change proceeds. a hard block on any drop past a
threshold, a soft warning that requires a human sign-off, or, for
non-blocking monitoring cases, no gate at all, only a dashboard entry.

## 6. ASCII structure diagram

```
+------------------+     +----------------+     +-----------------+
|  Case Registry    |---->|     Runner      |---->|  Target (SUT)    |
|  (golden dataset) |     | (orchestrator)  |<----|  prompt / agent  |
+------------------+     +--------+---------+     +-----------------+
                                   |
                                   v
                          +-----------------+
                          |    Scorer(s)     |
                          |  exact / rubric  |
                          |  / model judge   |
                          +--------+---------+
                                   |
                                   v
                          +-----------------+     +-----------------+
                          |    Reporter      |<--->|  Baseline Store  |
                          | pass rate, cost   |     | prior report     |
                          +--------+---------+     +-----------------+
                                   |
                                   v
                          +-----------------+
                          |     CI Gate       |
                          | block / warn / ok  |
                          +-----------------+
```

## 7. Dynamics

Two distinct flows make the pattern work. the execution flow, which runs on
every change, and the authoring flow, which grows the case registry over
time. A suite with a strong execution flow but no authoring flow measures the
same fixed set of cases forever and slowly stops representing reality, which
is the drift force named in dimension 3.

```
Execution flow, one suite run
------------------------------
CI trigger --> Runner: load Case Registry
Runner --> Target: send case[i].input
Target --> Runner: return output
Runner --> Scorer: score(output, case[i])
Scorer --> Runner: pass/fail, score, cost
   ... repeat for every case, with bounded concurrency ...
Runner --> Reporter: all per-case results
Reporter --> Baseline Store: fetch prior report
Reporter --> Reporter: diff current vs baseline
Reporter --> CI Gate: pass rate, delta, failing case ids
CI Gate --> pull request: block / warn / allow merge

Authoring flow, ongoing
------------------------
Production traffic --> Monitoring: sampled or user-flagged output
Monitoring --> Human review: is this output actually wrong
Human review --> Case Registry: add case with the real input
                                  and the correct expected output
Case Registry --> next Execution flow run: regression now caught
```

The authoring flow is the mechanism OpenAI's Evals framework was built
around, treating a good eval as the artifact worth the most engineering time
on a language-model project precisely because each case added closes off one
specific way the system has already been observed to fail (OpenAI,
"openai/evals" repository, https://github.com/openai/evals, verified
2026-08-02). A team that only writes cases speculatively, before shipping,
and never feeds real failures back in, gets a suite that reflects what the
team imagined users would do rather than what users actually did.

## 8. Implementation variants

**Deterministic, code-graded evals.** The cheapest and most reliable variant.
exact string match, substring or keyword containment, regular expression
match, JSON schema validation against a structured output contract (see
structured-output), and ordinary code assertions run against parsed fields.
Anthropic's own guidance for building evaluations of Claude-based
applications recommends starting here whenever the task has a clear-cut
answer, citing sentiment classification scored by exact match as a
representative case, and treats this as the default before reaching for a
model-graded scorer (Anthropic, "Develop test cases," Claude Docs,
https://platform.claude.com/docs/en/test-and-evaluate/develop-tests, verified
2026-08-02).

**Reference-based metrics.** A code-graded variant for cases where an exact
match is too strict but a fixed reference answer still exists. ROUGE-L for
summarization, comparing the longest common subsequence against a reference
summary, and embedding cosine similarity, comparing the meaning of an output
against a reference answer's embedding rather than its exact wording. The
same Anthropic guidance shows ROUGE-L used this way for summarization tasks
and cosine similarity used to check that semantically similar inputs produce
consistent outputs (Anthropic, "Develop test cases," Claude Docs,
https://platform.claude.com/docs/en/test-and-evaluate/develop-tests, verified
2026-08-02).

**Model-graded, LLM-as-judge evals.** For anything a fixed rule cannot
capture, tone, whether a response is unhelpfully evasive, whether a generated
explanation is faithful to a source document, a separate model call scores
the output against a rubric, either as a Likert-style numeric rating or a
binary classification (does this response contain protected health
information, yes or no). The same Anthropic guidance recommends grading with
a different model than the one being evaluated, to reduce the risk that a
model favors its own style of answer (Anthropic, "Develop test cases," Claude
Docs, https://platform.claude.com/docs/en/test-and-evaluate/develop-tests,
verified 2026-08-02). See llm-as-judge for the internal mechanics of this
scorer.

**RAG-specific suites.** Retrieval-augmented pipelines need scorers that
separate retrieval quality from generation quality, because a wrong final
answer can come from bad retrieval, a good retrieval fed to a model that
ignored it, or a model that hallucinated past both. Es, James, Espinosa-Anke,
and Schockaert introduced Ragas, a framework for reference-free evaluation of
retrieval-augmented generation pipelines, providing a suite of metrics for
evaluating retrieval and generation quality without requiring
human-annotated ground truth for every case (Shahul Es, Jithin James, Luis
Espinosa-Anke, Steven Schockaert, "RAGAS. Automated Evaluation of Retrieval
Augmented Generation," submitted September 2023,
https://arxiv.org/abs/2309.15217, verified 2026-08-02). Its faithfulness
metric extracts the individual factual claims in a generated response and
checks each one against the retrieved context, reporting the fraction of
claims that are actually supported, which is a concrete, checkable definition
of "did this answer make something up" rather than a vague human impression
(Ragas documentation, "Faithfulness,"
https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/,
verified 2026-08-02). See retrieval-augmented-generation and contextual-retrieval
for the pipelines these metrics are built to check.

**Agent and tool-use trajectory evals.** For a multi-step agent, scoring only
the final answer misses whether it got there safely, efficiently, or by
calling the wrong tool and getting lucky on the recovery. A trajectory-scored
case checks the sequence of tool calls, the arguments passed to each one, and
whether the number of steps stayed within a reasonable bound, in addition to
the final output. This variant composes directly with react and function-calling,
which describe the step shape being scored.

**Red-team and adversarial suites.** A specialized case set built from known
attack strings, jailbreak attempts, and prompt-injection payloads, scored not
on whether the model gave a good answer but on whether it refused, redacted,
or otherwise resisted the attack. promptfoo, an open-source command-line tool
and library for evaluating and red-teaming applications built on language
models, ships this as a first-class mode alongside its ordinary correctness
evals (Promptfoo, "Getting Started," https://www.promptfoo.dev/docs/intro/,
verified 2026-08-02). This variant is the systematic-testing counterpart to
prompt-injection-defense, which describes the runtime mitigation the red-team
suite is checking.

**CI-gated regression suites.** The variant most teams mean by "our evals".
a suite wired into the pull-request pipeline the same way unit tests are,
using either a general-purpose evaluation tool or a testing-framework-shaped
one. DeepEval, an open-source evaluation framework for language-model
systems, is built explicitly in the shape of a familiar test runner rather
than a bespoke tool, so that evaluating an application reads like writing
ordinary unit tests, and it ships pre-built metrics for hallucination, answer
relevancy, and a general-purpose model-graded metric called G-Eval for custom
rubrics (Confident AI, "deepeval" repository,
https://github.com/confident-ai/deepeval, verified 2026-08-02).

**Online and shadow evals.** Rather than a fixed offline dataset, the suite
runs continuously against a sample of live production traffic, scoring
real requests without changing what the user sees, and surfacing drift the
moment real usage patterns shift instead of waiting for the next release's
offline run. This variant trades a controlled, repeatable dataset for
coverage of exactly what users are doing today, and is typically layered on
top of, not instead of, an offline CI-gated suite.

## 9. Known production uses

- **OpenAI Evals.** An open-source framework and public registry of
  evaluations used both internally at OpenAI and by the community to check
  model and application behavior, built around a template system so that most
  evals need no custom code, only a dataset and a YAML configuration choosing
  a match, includes, or fuzzy-match template, with model-graded evals
  available through a custom YAML configuration for anything a fixed template
  cannot judge (OpenAI, "openai/evals" repository,
  https://github.com/openai/evals, verified 2026-08-02).
- **Stanford HELM.** Holistic Evaluation of Language Models, led by Percy
  Liang and forty nine collaborators at Stanford's Center for Research on
  Foundation Models, evaluates models across a taxonomy of scenarios crossed
  with metrics rather than a single accuracy number, covering forty two
  evaluation scenarios and measuring accuracy, calibration, robustness,
  fairness, bias, toxicity, and efficiency, achieving ninety six percent
  scenario coverage across thirty evaluated models against seventeen point
  nine percent for prior published evaluations (Percy Liang et al., "Holistic
  Evaluation of Language Models," Transactions on Machine Learning Research,
  submitted November 2022, https://arxiv.org/abs/2211.09110, verified
  2026-08-02).
- **promptfoo.** An open-source command-line tool and library for evaluating
  and red-teaming applications built on language models, run locally with no
  external dependency required, originally built for applications serving
  over ten million users in production and now carrying industry-specific
  test packs for financial services, insurance, telecommunications, and real
  estate (Promptfoo, "Getting Started,"
  https://www.promptfoo.dev/docs/intro/, verified 2026-08-02).
- **DeepEval.** An open-source, Apache 2.0 licensed evaluation framework
  maintained by the team at Confident AI, built to feel like a familiar unit
  test runner for language-model applications, agents, retrieval pipelines,
  and chatbots, shipping metrics for hallucination, answer relevancy, task
  completion, tool correctness, and a general-purpose model-graded G-Eval
  metric for custom criteria (Confident AI, "deepeval" repository,
  https://github.com/confident-ai/deepeval, verified 2026-08-02).
- **Ragas.** A framework for reference-free evaluation of retrieval-augmented
  generation pipelines, providing a documented suite of metrics, including
  faithfulness, answer relevancy, and context precision and recall, that a
  team can wire into a CI-gated regression suite for a RAG pipeline without
  hand-labeling ground-truth answers for every case (Shahul Es, Jithin James,
  Luis Espinosa-Anke, Steven Schockaert, "RAGAS. Automated Evaluation of
  Retrieval Augmented Generation," https://arxiv.org/abs/2309.15217, verified
  2026-08-02; Ragas documentation, "Faithfulness,"
  https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/,
  verified 2026-08-02).
- **Anthropic's own documented evaluation methodology.** Anthropic's public
  developer documentation for Claude-based applications lays out the full
  pattern for its own customers as standing practice, code-based, reference-
  based, and model-graded scorer types, a recommendation to prioritize a
  larger volume of automatically graded cases over a smaller set of
  hand-graded ones, held-out test sets, and multidimensional success criteria
  spanning task accuracy, safety, and latency together (Anthropic, "Develop
  test cases," Claude Docs,
  https://platform.claude.com/docs/en/test-and-evaluate/develop-tests,
  verified 2026-08-02).

## 10. Consequences

Positive.

- A change to a prompt, a model, or a retrieval strategy gets an objective
  before-and-after comparison instead of a subjective read on a handful of
  manual tries, turning "I think this is better" into a number a team can
  disagree about and settle with more cases rather than more opinions.
- A specific production failure, once it is added to the registry as a case,
  can never silently regress again without the suite catching it, converting
  each incident into a permanent, standing test the way a regression test
  does for ordinary software (see dimension 7, the authoring flow).
- A model or provider upgrade can be evaluated against the existing suite
  before it reaches users, giving a team the confidence to adopt a cheaper or
  faster model, or to hold off, based on measured behavior rather than a
  vendor's benchmark claims alone.
- The registry becomes institutional memory of every edge case the team has
  already learned about, readable by a new team member the same way a test
  suite documents expected behavior for a codebase they have never touched.

Negative.

- Every run costs real money and real time, because each case is at minimum
  one model call and a model-graded case is at least two, so a suite grown
  without discipline can turn a routine pull request check into a slow,
  expensive gate that teams start trying to route around.
- A golden dataset frozen at launch drifts away from what real users
  actually ask as the product changes, and an unmaintained suite gives a
  false sense of safety at exactly the moment it has stopped representing
  reality (see dimension 3, maintenance against product drift, and dimension
  11 for the specific failure this produces).
- A model-graded scorer imports its judge model's own biases and its own
  nondeterminism into the measurement, so the suite's reported quality can
  move because the judge changed, not because the system under test changed,
  unless the judge itself is calibrated and monitored (see dimension 11).
- A suite that a team has stopped trusting, because it is flaky or because
  thresholds have been quietly loosened to keep it green, becomes theater
  rather than a control, and a theater control is worse than no control
  because it consumes engineering time while providing no real signal.
- Optimizing a prompt directly against the suite's own cases, rather than
  against the underlying task the cases sample from, produces a version that
  scores better on the suite while performing no better, or worse, for real
  users, the same overfitting risk a held-out test set exists to catch in
  ordinary machine learning.

## 11. Failure modes and misuse

Judgement. the following symptom, cause, and fix triples are drawn from
common experience running this pattern in application teams, not from a
single cited source, and the specific numeric thresholds are illustrative
starting points, not universal constants.

**Symptom.** The suite reports green on every pull request, yet real users
report a broken or degraded experience shortly after a release.
**Cause.** The case registry was frozen near launch and never grew from
production traffic, so it no longer samples the distribution of inputs real
users actually send, a form of the maintenance-against-drift force in
dimension 3 winning by default.
**Fix.** Wire a channel from production, either sampled traffic with
consent and anonymization or user-flagged failures, back into the case
registry on a standing cadence, converting each newly discovered failure
into a case, as described in the authoring flow in dimension 7.

**Symptom.** The suite's pass rate stays flat and reassuring release after
release, but a spot check of recent transcripts shows visibly worse answers
than the team remembers from a year earlier.
**Cause.** The model-graded scorer's judge model is the same family as, or
weaker than, the model under test, and it is grading leniently in a way
that tracks the model family's own style rather than actual quality, or the
pass threshold has crept down through small, individually reasonable-looking
adjustments.
**Fix.** Use a distinct, typically stronger, judge model than the system
under test, the practice Anthropic's own guidance recommends (Anthropic,
"Develop test cases," Claude Docs,
https://platform.claude.com/docs/en/test-and-evaluate/develop-tests, verified
2026-08-02), and periodically audit the judge's verdicts against a small
human-labeled subset to confirm it still agrees with a person.

**Symptom.** The same commit produces a different pass count on two
consecutive CI runs with no code change in between.
**Cause.** The target, the judge, or both are called at a nonzero
temperature with no fixed seed, so the same input legitimately produces
different output on different calls, and the scorer treats each run's result
as ground truth rather than as one noisy sample.
**Fix.** Set temperature to zero and a fixed seed wherever the provider
supports it for both the target and the judge, retry only on genuine
transport failures (a timeout or a rate-limit response) rather than on a
content-level fail, and for any case that remains genuinely sensitive to
sampling, score it with several repeated trials and report a rate rather
than a single pass or fail.

**Symptom.** The evaluation bill grows every month, and pull requests are
visibly slower to merge because the check itself takes longer than the code
review does.
**Cause.** Every push runs the entire suite, including every slow,
expensive model-graded case, against a live paid model, with no tiering
between what needs to run in seconds and what can run overnight.
**Fix.** Split the suite into a small, fast, mostly deterministic smoke
subset that runs on every push, and a full suite, including the expensive
model-graded and red-team cases, that runs nightly or immediately before a
release, gating the merge on the fast subset and the release on the full
run.

**Symptom.** Engineers stop reading the evaluation report, merge past red
builds routinely, and treat a suite failure as noise to be dismissed rather
than a signal to investigate.
**Cause.** High-signal, must-pass regression cases are mixed in the same
report with exploratory or genuinely ambiguous cases that fail intermittently
for reasons unrelated to real quality, so the team has learned that a red
build usually means nothing, the same alert-fatigue failure mode that
degrades any monitoring system with too many low-value alerts.
**Fix.** Separate the suite into a small, curated, blocking set of cases the
team has verified are reliable and important, and a larger, non-blocking,
dashboard-only set for exploration and trend-watching, mirroring the
distinction GLUE itself drew between its main tasks and its separate
diagnostic test suite (Alex Wang et al., "GLUE. A Multi-Task Benchmark and
Analysis Platform for Natural Language Understanding,"
https://arxiv.org/abs/1804.07461, verified 2026-08-02).

**Symptom.** The suite's numbers steadily improve across several prompt
iterations, but a fresh set of real user conversations, never used to tune
the prompt, still shows the same failure pattern the suite was supposed to
have fixed.
**Cause.** The prompt was tuned directly against the visible cases in the
suite rather than against the underlying task, so it learned to satisfy the
specific examples rather than the general behavior they were meant to sample,
the same overfitting risk named in dimension 10.
**Fix.** Hold out a portion of the case registry that is never used for
prompt tuning, only for a final gating check, and rotate which cases sit in
the held-out portion periodically so a team cannot learn the held-out set by
repeated exposure over time.

## 12. Trade-off matrix

Compared against named alternatives on the forces from dimension 3. every row
is a way to gain confidence that a change to a language-model-backed system
did not make it worse; none of them is strictly better on every force.

| Approach | Coverage cost | Determinism | Handles open-ended output | Feedback latency | Blast radius if skipped |
|---|---|---|---|---|---|
| Evaluation Suite (this pattern) | Scales with case count, tunable by tiering | Deterministic scorers are stable, model-graded scorers are not without fixed sampling | Yes, through model-graded scorers | Seconds to minutes for a smoke subset, longer for a full run | A change ships without a regression check, silent until reported |
| LLM as Judge alone, no suite | Low per call, but ungoverned without a fixed case set to apply it to | Not deterministic unless controlled | Yes, this is its purpose | Seconds, per single judged output | No standing regression memory, each judgment is isolated |
| Human-in-the-loop review | High per case, bounded by reviewer throughput | Human judgment is consistent per reviewer but varies across reviewers | Best available for genuinely subjective quality | Hours to days | Slow enough that regressions can ship before review catches them |
| A/B testing in production | Low direct cost, real business metric as the signal | Reflects real usage, not a fixed sample | Yes, implicitly, through the business outcome | Days to weeks, needs enough traffic for significance | Real users are exposed to the regression during the test |
| Self-consistency (single-output technique) | One extra model call per output, not a standing suite | Reduces variance on a single answer, does not test the system over time | Improves reliability of one output, not a coverage tool | Seconds | Not applicable, it operates within a single response, not as a regression gate |
| Classic software regression test suite | Very low, deterministic code executes fast | Fully deterministic | No, designed for deterministic logic only | Seconds | A deterministic bug ships, but the failure mode this suite exists to catch, model output drift, is out of its scope entirely |

## 13. Related and incompatible patterns

**llm-as-judge.** The scorer used inside a suite for any case a fixed rule
cannot grade. Evaluation Suite is the container, the registry, the runner,
the reporter, and the gate; llm-as-judge is one of several scorer
implementations that plug into it, alongside exact match and reference-based
metrics (see dimension 8).

**input-guardrails and output-guardrails.** Runtime checks that block or
transform a request or a response as it flows through production, distinct
from an evaluation suite in when they run. a guardrail runs on every live
request, an evaluation suite runs offline against a fixed case set before a
change ships. A team commonly writes cases in the suite that specifically
check a guardrail is still triggering on known-bad inputs, making the suite
the pre-ship verification for the guardrail's runtime behavior.

**prompt-injection-defense.** The runtime mitigations for adversarial input.
The red-team variant of an evaluation suite (dimension 8) is the systematic,
regression-tested way to confirm those mitigations still hold as the prompt
and the model change, turning a one-time security review into a standing,
automatically re-run check.

**self-consistency.** A technique for improving a single output's reliability
by sampling several reasoning paths and taking the majority answer. It
composes with an evaluation suite in two directions. it can be used inside
the target being evaluated, to make the system under test itself more
reliable, and it can be used inside a scorer, to reduce the noise of a
nondeterministic model-graded judgment by taking a majority vote across
several judge calls rather than trusting a single one.

**evaluator-optimizer.** A generation-time loop where a model produces a
candidate, a second model critiques it, and the first model revises, run
inline to improve one output before it is returned. It shares the two-model
shape with llm-as-judge grading, but it runs at generation time to improve
a single result, where an evaluation suite runs offline to measure many
results against a standing bar, and the two are commonly built by the same
team without conflict, one improving output quality, the other measuring
whether that improvement generalizes.

**cost-guard.** A runtime control on how much a system is allowed to spend
per request or per period. An evaluation suite has the identical cost
concern applied to its own execution, since a large suite run against a
paid model is itself a real, recurring expense, which is why dimension 3
and dimension 11 both treat suite cost as a force to manage deliberately
rather than a fixed price to accept.

**structured-output and function-calling.** Common shapes for the target
under test. a suite that checks a structured-output contract can use a cheap
deterministic JSON-schema scorer rather than a model-graded one (dimension
8), and a suite testing an agent built on function-calling needs the
trajectory-scoring variant described in dimension 8, since the final answer
alone can look correct while the tool calls that produced it were wrong.

**react.** The reasoning-and-acting loop an agent commonly follows. When the
target under test is a ReAct-style agent, the suite's cases need to capture,
and its scorers need to check, not only the final answer but the sequence of
thought and action steps the loop produced, which is the same trajectory
concern named for tool-use evals in dimension 8.

No pattern in this catalog is structurally incompatible with Evaluation
Suite. The only real tension is with relying exclusively on ungraded, ad-hoc
human review at the volume and cadence a CI gate requires, because nothing
about human review scales to running on every pull request the way an
automated suite does, which is a throughput mismatch rather than a technical
incompatibility, and it is exactly the trade-off named in the human-in-the-loop
row of dimension 12.

## 14. Refactoring path in and out

Introducing an evaluation suite into a system that has none.

1. Collect ten to twenty real failures the team already knows about, from
   support tickets, from manual testing, or from a developer's own trial and
   error, and write each one down as a case with its exact input and the
   correct expected output.
2. Score the simplest cases with a deterministic scorer, exact match or
   substring containment, before reaching for a model-graded scorer for
   anything genuinely open-ended, following the order Anthropic's own
   guidance recommends (Anthropic, "Develop test cases," Claude Docs,
   https://platform.claude.com/docs/en/test-and-evaluate/develop-tests,
   verified 2026-08-02).
3. Wire the runner into the pull-request pipeline as advisory only, reporting
   the pass rate without blocking a merge, so the team can see how noisy or
   stable the suite is before anyone's work depends on it passing.
4. Once the pass rate has been stable across several unrelated changes, add
   a baseline diff and promote the suite from advisory to blocking on a drop
   past a defined threshold.
5. Add a model-graded scorer, using a distinct judge model, for the cases a
   fixed rule cannot capture, and calibrate it against a small human-labeled
   subset before trusting its verdicts in the gate.
6. Tier the suite into a fast smoke subset that runs on every push and a
   full run, including red-team and expensive model-graded cases, that runs
   nightly or immediately before a release, resolving the cost-against-
   coverage force from dimension 3 explicitly rather than by accident.
7. Wire the authoring flow from dimension 7 as a standing habit. every new
   confirmed production failure becomes a case in the same pull request that
   fixes it, so the fix and its regression test land together.

Removing or downsizing an evaluation suite that has outlived part of its
scope.

1. When a feature, a prompt path, or a model provider is deprecated, retire
   the cases that exist only to check it, moving them to an archived file
   rather than deleting the history outright, so a team can recover the
   context if the feature returns.
2. Consolidate near-duplicate cases that exercise the same underlying
   behavior with only cosmetic differences in wording, since each duplicate
   adds cost without adding coverage, the direct cost side of the coverage
   force in dimension 3.
3. Downgrade a case from blocking to advisory, rather than deleting it
   outright, when its failure mode has become a known, accepted limitation
   rather than a regression the team intends to act on, keeping the
   historical signal visible without letting it block unrelated work.
4. If the whole pattern is being removed because the team is reverting to a
   fully deterministic feature with no language-model component left, the
   removal is complete only once the case registry, the runner wiring, and
   the CI gate configuration are all removed together, so a stale, unused
   gate does not linger and silently pass on an empty registry.

## 15. Testing and verification

Judgement. verifying an evaluation suite is meta-testing, checking that the
thing meant to catch regressions in the product actually catches
regressions, and the practices below are drawn from general test-engineering
discipline applied to this pattern rather than from a single source.

The most direct verification is to deliberately break the target and confirm
the suite reports the break, the same mutation-testing idea used to verify
an ordinary test suite is not merely present but effective. the working code
example in this entry does exactly this. it defines a baseline target that
answers correctly, a deliberately regressed second target that gives a
plausible-sounding wrong answer to one case, and confirms the suite's
reported pass rate actually drops and the specific failing case is named in
the report, rather than only asserting that "the suite ran".

A scorer function is itself ordinary deterministic code once its inputs are
fixed strings, so it should be unit tested the same way any other function
is, with synthetic outputs chosen to be unambiguously correct and
unambiguously incorrect, checked against the scorer directly, with no live
model call involved.

A model-graded scorer needs an additional verification step a deterministic
scorer does not. its agreement with a human judgment on a small labeled
subset. A team building a Likert-scale or binary model-graded scorer should
hold out a handful of cases with a human-assigned correct verdict, run the
scorer against them, and measure how often the model's verdict matches the
human's, treating a large disagreement rate as a signal the rubric prompt
needs rework before the scorer is trusted inside a blocking gate.

During development of the runner and reporter code itself, the target should
be replaced with a deterministic stub function rather than a live model call,
so that iterating on the orchestration logic does not cost tokens or
introduce model nondeterminism into what should be a fast, repeatable check
of the plumbing rather than of the model.

## 16. Observability signals

**Pass rate over time, per suite and per tag.** The primary trend line. A
healthy suite shows a stable or improving pass rate across releases, with
any drop investigated the same day it appears rather than accumulating.
Tagging cases by feature area lets the trend be read per area, since a
single suite-wide number can hide a real regression in one area offset by
improvement in another.

**Per-case latency, p50 and p95.** Both the target's response time and the
scorer's, especially for a model-graded scorer, since a judge call adds its
own latency to every scored case. A healthy suite's p95 stays within the
budget the CI pipeline allows; a growing p95 with no change in case count
signals a provider slowdown or a runner concurrency regression.

**Cost per run, in the provider's billed unit.** A healthy suite's cost
tracks case count and stays within a set budget; an unexplained jump signals
either a case count increase nobody reviewed, a model version change with a
different price, or a retry loop firing more than intended.

**Score distribution, not only the pass or fail count.** A histogram of
raw scores shows whether cases are clustering near the pass threshold, which
is a warning that the threshold itself, not the underlying behavior, is
driving the reported pass rate, and that a small model or prompt change
could flip many cases at once.

**Judge and human agreement rate.** For any model-graded scorer used in a
blocking gate, a periodically re-measured agreement rate against a small
human-labeled subset (see dimension 15). A healthy suite keeps this above a
team-set threshold; a falling agreement rate is the earliest warning that a
judge has drifted, without waiting for the failure to show up as a wrong
release decision.

**Flake rate.** The fraction of cases whose pass or fail verdict changes
across repeated runs of the identical commit with no code change. A healthy
suite keeps this near zero for its blocking subset; a rising flake rate is
the direct symptom named in dimension 11's third failure mode and should
trigger an investigation into sampling settings before the team starts
ignoring red builds.

**Time to first regression detected.** Measured from when a bad change
merges to when the suite first reports it, whether that is the very next
run for a smoke-subset case or up to a day later for a nightly-only case.
A healthy suite keeps this short for anything the team considers
high-severity; a long gap for a severe class of failure is a signal to move
its cases into the fast, blocking subset.

## 17. Security and privacy implications

A case registry built from real production traffic or real user complaints
carries the same personal data risk as any stored transcript, and needs the
same redaction, consent, and retention discipline described in
pii-redaction before a raw user input is committed to the registry, since a
version-controlled test file is otherwise a durable, widely-readable copy of
whatever personal information the original request contained.

A red-team subset (dimension 8) intentionally stores working attack strings,
jailbreak prompts, and prompt-injection payloads, which is exactly the kind
of content that should not sit in a place with the same broad read access as
ordinary application code, since publishing a working attack against the
team's own system hands the same attack to anyone who can read the
repository. Access to this subset should be restricted the same way an
internal security team restricts access to a vulnerability tracker.

A model-graded scorer sends the case's input and the target's output to a
third-party model provider as part of grading, which means any sensitive
content inside a case is exposed to that provider's own data handling terms
a second time, in addition to whatever exposure the target's own call to a
model already created. In a regulated environment, this can require a
separate data-processing agreement covering the judge call, or running the
judge model on infrastructure the team controls rather than a hosted API, a
concern that applies with the same force to the judge-model call described
in llm-as-judge.

Where a suite's pass rate is cited as evidence of a compliance or safety
claim, for example "this system was tested for bias before release," the
suite itself becomes an artifact subject to audit, and the team should be
able to show what cases were included, who can add or remove a case, and
whether the reported number reflects the full registry or a subset chosen
after the fact, because a suite whose cases or thresholds can be quietly
adjusted to produce a favorable number is not a control a regulator or an
internal audit team can rely on.

## Code examples

Three languages, chosen because a case registry, a scorer, a runner, and a
report are ordinary application-level constructs rather than anything
language-specific, so the same shape is shown once in a dynamically typed
language and twice in statically typed languages to show how the interfaces
tighten. Each sample builds a small suite with two cases, runs it against a
correct target and against a deliberately regressed target, and shows the
report catching the regression, which is the verification practice described
in dimension 15, not only a demonstration of the shape. Rust and Swift are
omitted because neither changes the pattern's shape from what Go already
shows; a fourth mechanical translation would add length without adding a new
idea.

### Python

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional
import json
import time


@dataclass
class Case:
    id: str
    input: str
    expected: str
    tags: list[str] = field(default_factory=list)


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    score: float
    latency_ms: float
    output: str


Scorer = Callable[[str, str], tuple[bool, float]]


def contains(output: str, expected: str) -> tuple[bool, float]:
    ok = expected.lower() in output.lower()
    return ok, 1.0 if ok else 0.0


class EvalSuite:
    def __init__(self, name: str, scorer: Scorer, threshold: float = 1.0):
        self.name = name
        self.scorer = scorer
        self.threshold = threshold
        self.cases: list[Case] = []

    def add(self, case: Case) -> None:
        self.cases.append(case)

    def run(self, target: Callable[[str], str]) -> list[CaseResult]:
        results: list[CaseResult] = []
        for case in self.cases:
            start = time.perf_counter()
            output = target(case.input)
            elapsed = (time.perf_counter() - start) * 1000
            passed, score = self.scorer(output, case.expected)
            results.append(
                CaseResult(case.id, passed and score >= self.threshold, score, elapsed, output)
            )
        return results

    def report(self, results: list[CaseResult]) -> dict:
        n = len(results)
        passed = sum(1 for r in results if r.passed)
        avg_score = sum(r.score for r in results) / n if n else 0.0
        return {
            "suite": self.name,
            "n": n,
            "pass_rate": round(passed / n, 4) if n else 0.0,
            "avg_score": round(avg_score, 4),
            "failures": [r.case_id for r in results if not r.passed],
        }


def diff_against_baseline(current: dict, baseline: dict, max_drop: float = 0.02) -> Optional[str]:
    delta = current["pass_rate"] - baseline["pass_rate"]
    if delta < -max_drop:
        return (
            f"regression in {current['suite']}: pass_rate "
            f"{baseline['pass_rate']:.3f} -> {current['pass_rate']:.3f}"
        )
    return None


def router_v1(prompt: str) -> str:
    if "capital of france" in prompt.lower():
        return "The capital of France is Paris."
    if "refund policy" in prompt.lower():
        return "Refunds are issued within 30 days of purchase, minus shipping."
    return "I am not sure."


def router_v2_regressed(prompt: str) -> str:
    if "capital of france" in prompt.lower():
        return "France's capital city is a major European hub."
    return router_v1(prompt)


if __name__ == "__main__":
    suite = EvalSuite("support-bot-smoke", contains, threshold=1.0)
    suite.add(Case("geo-1", "What is the capital of France?", "Paris"))
    suite.add(Case("policy-1", "What is your refund policy?", "30 days"))

    baseline_report = suite.report(suite.run(router_v1))
    print("baseline:", json.dumps(baseline_report))

    candidate_report = suite.report(suite.run(router_v2_regressed))
    print("candidate:", json.dumps(candidate_report))

    regression = diff_against_baseline(candidate_report, baseline_report)
    print(regression or "no regression detected")
```

Run with `python3 eval_suite.py`. The output prints a full pass baseline
report, a candidate report showing one failing case after the regressed
target is substituted, and a regression line naming the exact drop, which was
executed against Python 3 during authoring and produced that output.

### TypeScript

```typescript
type Scorer = (output: string, expected: string) => { passed: boolean; score: number };

interface Case {
  id: string;
  input: string;
  expected: string;
}

interface CaseResult {
  caseId: string;
  passed: boolean;
  score: number;
  output: string;
}

interface Report {
  suite: string;
  n: number;
  passRate: number;
  avgScore: number;
  failures: string[];
}

const contains: Scorer = (output, expected) => {
  const passed = output.toLowerCase().includes(expected.toLowerCase());
  return { passed, score: passed ? 1 : 0 };
};

class EvalSuite {
  private cases: Case[] = [];

  constructor(private name: string, private scorer: Scorer) {}

  add(c: Case): this {
    this.cases.push(c);
    return this;
  }

  run(target: (input: string) => string): CaseResult[] {
    return this.cases.map((c) => {
      const output = target(c.input);
      const { passed, score } = this.scorer(output, c.expected);
      return { caseId: c.id, passed, score, output };
    });
  }

  report(results: CaseResult[]): Report {
    const n = results.length;
    const passed = results.filter((r) => r.passed).length;
    const avgScore = n === 0 ? 0 : results.reduce((sum, r) => sum + r.score, 0) / n;
    return {
      suite: this.name,
      n,
      passRate: n === 0 ? 0 : passed / n,
      avgScore,
      failures: results.filter((r) => !r.passed).map((r) => r.caseId),
    };
  }
}

function diffAgainstBaseline(current: Report, baseline: Report, maxDrop = 0.02): string | null {
  const delta = current.passRate - baseline.passRate;
  if (delta < -maxDrop) {
    return `regression in ${current.suite}: passRate ${baseline.passRate.toFixed(
      3
    )} -> ${current.passRate.toFixed(3)}`;
  }
  return null;
}

function routerV1(prompt: string): string {
  if (prompt.toLowerCase().includes("capital of france")) {
    return "The capital of France is Paris.";
  }
  if (prompt.toLowerCase().includes("refund policy")) {
    return "Refunds are issued within 30 days of purchase, minus shipping.";
  }
  return "I am not sure.";
}

function routerV2Regressed(prompt: string): string {
  if (prompt.toLowerCase().includes("capital of france")) {
    return "France's capital city is a major European hub.";
  }
  return routerV1(prompt);
}

const suite = new EvalSuite("support-bot-smoke", contains)
  .add({ id: "geo-1", input: "What is the capital of France?", expected: "Paris" })
  .add({ id: "policy-1", input: "What is your refund policy?", expected: "30 days" });

const baselineReport = suite.report(suite.run(routerV1));
console.log("baseline:", JSON.stringify(baselineReport));

const candidateReport = suite.report(suite.run(routerV2Regressed));
console.log("candidate:", JSON.stringify(candidateReport));

console.log(diffAgainstBaseline(candidateReport, baselineReport) ?? "no regression detected");
```

Compiled with `tsc --strict --target ES2020 --module commonjs` and run with
`node`, producing the same shape of output as the Python sample, a full-pass
baseline, a one-failure candidate, and a printed regression line, confirming
the strict TypeScript compiler accepts the code with no type errors.

### Go

```go
package main

import (
	"fmt"
	"strings"
)

type Case struct {
	ID       string
	Input    string
	Expected string
}

type CaseResult struct {
	CaseID string
	Passed bool
	Score  float64
	Output string
}

type Report struct {
	Suite    string
	N        int
	PassRate float64
	AvgScore float64
	Failures []string
}

type Scorer func(output, expected string) (bool, float64)

func contains(output, expected string) (bool, float64) {
	ok := strings.Contains(strings.ToLower(output), strings.ToLower(expected))
	if ok {
		return true, 1.0
	}
	return false, 0.0
}

type EvalSuite struct {
	Name   string
	Scorer Scorer
	Cases  []Case
}

func NewEvalSuite(name string, scorer Scorer) *EvalSuite {
	return &EvalSuite{Name: name, Scorer: scorer}
}

func (s *EvalSuite) Add(c Case) *EvalSuite {
	s.Cases = append(s.Cases, c)
	return s
}

func (s *EvalSuite) Run(target func(string) string) []CaseResult {
	results := make([]CaseResult, 0, len(s.Cases))
	for _, c := range s.Cases {
		output := target(c.Input)
		passed, score := s.Scorer(output, c.Expected)
		results = append(results, CaseResult{c.ID, passed, score, output})
	}
	return results
}

func (s *EvalSuite) Report(results []CaseResult) Report {
	n := len(results)
	passed := 0
	var scoreSum float64
	var failures []string
	for _, r := range results {
		if r.Passed {
			passed++
		} else {
			failures = append(failures, r.CaseID)
		}
		scoreSum += r.Score
	}
	report := Report{Suite: s.Name, N: n}
	if n > 0 {
		report.PassRate = float64(passed) / float64(n)
		report.AvgScore = scoreSum / float64(n)
	}
	report.Failures = failures
	return report
}

func diffAgainstBaseline(current, baseline Report, maxDrop float64) string {
	delta := current.PassRate - baseline.PassRate
	if delta < -maxDrop {
		return fmt.Sprintf(
			"regression in %s: pass_rate %.3f -> %.3f",
			current.Suite, baseline.PassRate, current.PassRate,
		)
	}
	return "no regression detected"
}

func routerV1(prompt string) string {
	lower := strings.ToLower(prompt)
	if strings.Contains(lower, "capital of france") {
		return "The capital of France is Paris."
	}
	if strings.Contains(lower, "refund policy") {
		return "Refunds are issued within 30 days of purchase, minus shipping."
	}
	return "I am not sure."
}

func routerV2Regressed(prompt string) string {
	lower := strings.ToLower(prompt)
	if strings.Contains(lower, "capital of france") {
		return "France's capital city is a major European hub."
	}
	return routerV1(prompt)
}

func main() {
	suite := NewEvalSuite("support-bot-smoke", contains)
	suite.Add(Case{"geo-1", "What is the capital of France?", "Paris"})
	suite.Add(Case{"policy-1", "What is your refund policy?", "30 days"})

	baseline := suite.Report(suite.Run(routerV1))
	fmt.Printf("baseline: %+v\n", baseline)

	candidate := suite.Report(suite.Run(routerV2Regressed))
	fmt.Printf("candidate: %+v\n", candidate)

	fmt.Println(diffAgainstBaseline(candidate, baseline, 0.02))
}
```

Run with `go run main.go` and checked with `go vet`, producing the same
baseline, candidate, and regression report shape as the other two languages,
with `go vet` reporting no issues.

## 18. References

1. Alex Wang, Amanpreet Singh, Julian Michael, Felix Hill, Omer Levy, Samuel
   R. Bowman. "GLUE. A Multi-Task Benchmark and Analysis Platform for Natural
   Language Understanding." Submitted 20 April 2018, published at ICLR 2019.
   https://arxiv.org/abs/1804.07461 Verified 2026-08-02. Source for the
   lineage in dimension 1 and the main-tasks-versus-diagnostic-suite split
   cited in dimension 11.
2. OpenAI. "openai/evals" repository. https://github.com/openai/evals
   Verified 2026-08-02. Source for the framework's template and model-graded
   eval concepts in dimension 1, the authoring-loop framing in dimension 7,
   the implementation variants in dimension 8, and the production use in
   dimension 9.
3. Percy Liang et al. "Holistic Evaluation of Language Models." Transactions
   on Machine Learning Research, submitted November 2022.
   https://arxiv.org/abs/2211.09110 Verified 2026-08-02. Source for the HELM
   production use and the scenarios-crossed-with-metrics taxonomy in
   dimension 9.
4. Promptfoo. "Getting Started" documentation.
   https://www.promptfoo.dev/docs/intro/ Verified 2026-08-02. Source for the
   red-team implementation variant in dimension 8 and the production-scale
   use in dimension 9.
5. Confident AI. "deepeval" repository.
   https://github.com/confident-ai/deepeval Verified 2026-08-02. Source for
   the test-runner-shaped implementation variant in dimension 8 and the
   production use in dimension 9.
6. Shahul Es, Jithin James, Luis Espinosa-Anke, Steven Schockaert. "RAGAS.
   Automated Evaluation of Retrieval Augmented Generation." Submitted
   September 2023. https://arxiv.org/abs/2309.15217 Verified 2026-08-02.
   Source for the RAG-specific implementation variant in dimension 8 and the
   production use in dimension 9.
7. Ragas project. "Faithfulness" metric documentation.
   https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/
   Verified 2026-08-02. Source for the faithfulness metric definition in
   dimension 8.
8. Anthropic. "Develop test cases." Claude Docs.
   https://platform.claude.com/docs/en/test-and-evaluate/develop-tests
   Verified 2026-08-02. Source for the scorer taxonomy, the different-judge-
   model recommendation, and the multidimensional success criteria cited in
   dimensions 8, 9, 11, and 14.
