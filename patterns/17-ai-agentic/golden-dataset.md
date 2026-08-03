---
name: Golden Dataset
slug: golden-dataset
family: 17-ai-agentic
category: AI Agentic
aliases: [Golden Set, Golden Test Set, Ground Truth Dataset, Reference Dataset, Eval Set]
first_described: "No single origin paper. The word golden traces to golden master or characterization testing (Michael Feathers, Working Effectively with Legacy Code, Prentice Hall, 2004, ISBN 0-13-117705-2), re-purposed for model and agent evaluation by the ML testing and LLM eval tooling community from roughly 2018 to 2023"
maturity: established
related: [llm-as-judge, evaluator-optimizer, reflexion, self-consistency, human-in-the-loop, output-guardrails, input-guardrails, cost-guard]
incompatible_with: []
verified: 2026-08-02
---

# Golden Dataset

## 1. Name, aliases, and lineage

The canonical name in this catalog is Golden Dataset. The same idea is called
a golden set, a golden test set, a ground truth dataset, a reference dataset,
or an eval set, depending on which tool's documentation a team read first.
Braintrust's own product documentation defines a dataset as a "versioned
collection of test cases that power repeatable evaluations and capture real
production behavior as your application evolves" ([Braintrust, Datasets guide](https://www.braintrust.dev/docs/guides/datasets),
verified 2026-08-02), and DeepEval's documentation uses the word golden
directly, describing an `expected_output` field as "the ideal answer for a
given input" inside what it calls a golden dataset ([Confident AI, DeepEval repository](https://github.com/confident-ai/deepeval),
verified 2026-08-02). LangSmith's terminology is closer to plain testing
language, an example is "an individual test case with inputs and reference
outputs" and a dataset is a named collection of examples ([LangChain, LangSmith evaluation concepts](https://docs.langchain.com/langsmith/evaluation),
verified 2026-08-02). None of the three vendors cites a shared origin, which
is itself informative. this is a convergently discovered pattern, not one
invented once and copied.

The word golden did not start in AI. It comes from golden master testing,
also called characterization testing, a technique Michael Feathers named and
described for legacy code that has no adequate test suite. Feathers'
"Working Effectively with Legacy Code" frames a characterization test as a
way to "describe the actual behavior of an existing piece of software" so
that behavior is "protected against unintended changes" by an automated test
([Wikipedia summary of Feathers' characterization testing](https://en.wikipedia.org/wiki/Characterization_test),
verified 2026-08-02, citing Feathers, Prentice Hall, 2004, ISBN 0-13-117705-2).
The mechanism is exactly the one this entry describes for AI systems. observe
what the system currently outputs for a fixed set of inputs, record that
output as the golden master, and write a test that fails the moment a future
change produces a different output. The Wikipedia summary is explicit that
such a test is "essentially a change detector," not a correctness oracle,
because "it is up to the person analyzing the results to determine if the
detected change was expected and desirable, or unexpected and undesirable."
That single sentence, written years before large language models existed, is
the most precise statement of what a golden dataset for an LLM system does
and does not prove, and it is why this entry treats change detection and
correctness verification as two separate jobs throughout.

The term crossed into machine learning testing sometime around 2018 to 2020,
when teams shipping classical ML models (fraud scoring, recommendation
ranking, search relevance) needed the same change-detector discipline for
model retraining as software teams had for refactoring. A golden set in that
era was usually a fixed sample of labeled production data held aside so a
retrained model's predictions could be diffed against the previous model's
predictions and against human labels before a rollout. When instruction
tuned and chat-oriented LLMs made non-deterministic, open-ended generation
the normal output shape rather than the exception, the same golden-set idea
had to absorb fuzzy grading, because two correct answers to "summarize this
support ticket" are rarely byte identical. OpenAI Evals, released as an open
source framework in 2023, generalized the format to JSON records that a
grader function or a model-graded rubric consumes, and its own README states
that "quality evals are hard" and that a private eval can "represent the
common LLM patterns in your workflow without exposing any of that data
publicly" ([OpenAI, Evals repository README](https://github.com/openai/evals),
verified 2026-08-02), which is the point at which golden dataset tooling
became a distinct, separately maintained artifact rather than a folder of
ad hoc test fixtures.

Two names are worth separating even though they overlap heavily in casual
use. A benchmark is a golden dataset published for the whole field to compare
models against (MMLU, HumanEval, GSM8K). A golden dataset in the sense this
entry covers is almost always private, owned by one team, scoped to one
application's actual task distribution, and updated as that application's
task distribution shifts. A public benchmark that never changes and that
every lab has seen thousands of times during training is a much weaker
change detector for a specific product than a hundred hand-checked examples
drawn from that product's own support queue, precisely because the public
benchmark is contaminated and the private set is not, a distinction the
Failure modes dimension returns to in detail.

## 2. Problem and context

An engineer changes a system prompt, swaps a retrieval step, upgrades from
one model version to another, or adjusts a temperature setting, and then has
to answer one question honestly. did that change make the system better,
worse, or merely different. For deterministic software this question is
answered by a green or red test suite. For an LLM-backed agent the same
question is much harder to answer, for three reasons that compound.

First, the output space is enormous and rarely has one correct string. Ask a
support agent to answer "how do I cancel my subscription" and there are
hundreds of phrasings that are all acceptable, and a handful that look
plausible but are subtly wrong, for example telling a customer they can
cancel from a screen that was removed in the last redesign. A raw string
comparison against one reference answer fails on every acceptable
paraphrase, which trains engineers to stop testing string output at all, and
they lose the only mechanism that would have caught the wrong-screen error.

Second, manual review does not scale to the rate of change an LLM
application actually experiences. A team iterating on a prompt might try
fifteen variants in an afternoon. Reading every response by hand for even a
modest set of test inputs, at that cadence, consumes the afternoon instead
of the iteration. Anthropic's own guidance on building evaluations names this
tension directly, recommending engineers "design evals that mirror your
real-world task distribution" and explicitly warning not to "forget to
factor in edge cases," while also stating a volume preference. more test
cases with an automated, slightly noisier grading signal beat fewer test
cases graded by hand at high fidelity, because the larger sample size is what
lets a small regression surface statistically ([Anthropic, Test and evaluate, Developing test cases](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests),
verified 2026-08-02).

Third, and most damaging in practice, silent regression is the default
failure mode of an LLM system, not the exception. A regular software bug
usually throws an exception, returns a wrong HTTP status, or fails an
assertion, and a build pipeline stops. A prompt change that quietly makes the
agent 8 percent worse at extracting a date field from an invoice produces no
exception. It produces a wrong number in a downstream report three weeks
later, discovered by a customer, not by CI. The golden dataset exists to
convert that silent, delayed, customer-facing failure into a loud, immediate,
pre-merge failure, the same transformation a conventional regression test
suite already performs for deterministic code. Hamel Husain's widely
circulated guidance on evaluation-driven LLM development frames the whole
practice around exactly this speed of feedback, arguing that iteration speed
is what separates a team that ships a reliable product from one that does
not, and recommending engineers "examine as much data as possible" early,
reading through both synthetic and real production traces before writing the
first formal test ([Hamel Husain, "Your AI product needs evals"](https://hamel.dev/blog/posts/evals/),
verified 2026-08-02).

The context in which a golden dataset is the right tool, rather than a
public benchmark, a single smoke test, or trust in vibes, is any system where
generation is non-deterministic, where a wrong answer has a real cost
(a support answer that loses a customer, a code agent that merges a broken
diff, a medical or legal summarizer that misses a caveat), and where the
system is expected to change over time through prompt edits, retrieval
changes, or model upgrades. A one-off script run once and thrown away does
not need this pattern. A system that will be touched again next week does.

## 3. Forces

**Coverage versus curation cost.** A golden dataset is only a useful change
detector for the parts of the task distribution it actually samples. Wide
coverage catches more regressions, but every additional labeled example
costs human time to write and, worse, human time to keep correct as the
product's own definition of correct drifts. A team that tries to hand-label
a thousand examples to perfect fidelity before shipping anything will ship
nothing. Anthropic's own bias, stated plainly, is to trade some grading
precision for a larger sample rather than the reverse, on the reasoning that
statistical signal from volume beats hand-graded precision on a handful of
cases ([Anthropic, Developing test cases](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests),
verified 2026-08-02).

**Determinism of the grader versus fidelity of the judgment.** An exact
string match is fast, free, deterministic, and reproducible in CI, but it
rejects every acceptable paraphrase, which forces teams toward narrower
output formats (single labels, numbers, JSON with fixed keys) than the
product might otherwise want. A semantic or LLM-graded judgment tolerates
paraphrase and captures nuance a string match cannot, but it costs money per
run, is itself imperfect, and introduces the exact non-determinism the
golden set was built to control for in the first place. Every real
implementation of this pattern sits somewhere on this spectrum, usually
with several graders of different strictness applied to different fields of
the same case.

**Stability versus staleness.** A golden dataset needs a stable reference so
that a diff between two runs means something. But an application's real
task distribution moves, new product features create new question types,
old features are deprecated and their golden cases become misleading, and a
model that used to answer a question one way now answers it a different, also
correct, way after a provider-side model update. A golden set frozen forever
becomes an anchor to a stale product; a golden set edited too freely stops
being a stable baseline and turns any comparison across time into noise.

**Ownership and the incentive to game the metric.** Whoever writes the golden
cases decides, implicitly, what the system is optimized to be good at. If the
same engineer who tunes the prompt also writes and owns the golden set, there
is a structural incentive, usually unconscious, to write cases the current
prompt already handles well and to avoid writing cases that expose its known
weaknesses. This is the LLM-era instance of Goodhart's law, a metric that
becomes a target stops being a good measure, and it is one of the two most
common reasons a golden dataset stops earning its keep in production, covered
in depth under Failure modes.

**Cost and latency of running the suite.** A golden set of five hundred
cases, each graded by a second model call, is not free to run on every pull
request. The forces above push toward larger, richer, more semantically
graded sets; this force pushes back toward smaller, cheaper, faster ones,
and most teams end up running a small fast subset on every commit and a
large slow superset nightly or before a release, a structure covered under
Implementation variants.

## 4. Applicability and non-applicability

Reach for a golden dataset when all of the following hold. the system's
output is not deterministic given the same input, meaning a plain unit test
comparing one fixed string cannot serve as the regression check; the system
is expected to change repeatedly over its life, through prompt edits, model
version upgrades, retrieval or tool changes, or fine tuning, so a one-time
manual check at launch is not sufficient; a wrong output carries a real cost
to a user or the business, high enough to justify the ongoing cost of
maintaining a labeled set; and the team can identify, even approximately, the
actual distribution of inputs the system will see in production, because a
golden set built from guesses about usage rather than observed usage tests
the wrong thing.

The following list is deliberately concrete rather than a restatement of the
first paragraph in the negative, because knowing when not to build a golden
dataset saves more engineering time than knowing when to build one.

Non-applicability list.

- **A single, throwaway script or one-off analysis.** If the code will never
  run a second time, there is no future change for the golden set to protect
  against, and building one is pure sunk cost.
- **A fully deterministic function with a small, enumerable output space.**
  If a function classifies an input into one of three fixed labels with no
  model call involved, or the LLM call always returns highly structured,
  narrow output that a conventional unit test can assert on exactly, an
  ordinary unit test is cheaper to write and maintain and gives an
  unambiguous pass or fail with no grading step required.
- **As a substitute for monitoring live production traffic.** A golden
  dataset, however large, is a fixed sample frozen at some point in time. It
  cannot tell a team that a new class of adversarial input started arriving
  yesterday, or that latency degraded under real load, or that a downstream
  API started returning malformed data. Those are observability and
  production monitoring concerns, and a team that treats a green golden-set
  run as proof the system is healthy in production is making the same
  mistake as a team that treats passing unit tests as proof there are no bugs
  in production.
- **As a fine-tuning training corpus.** A golden dataset's job is
  measurement, not training. Reusing the exact same examples for
  fine-tuning contaminates the evaluation, because the system will now
  score artificially well on the very cases meant to detect regression,
  and it will look healthy while it has actually lost the ability to
  generalize beyond the set it memorized. Keep a strict split, the same
  discipline classical machine learning has enforced between training and
  test data for decades, and treat any leakage as a defect, not an
  optimization.
- **When the task distribution is still unknown.** A team building the very
  first version of a product feature, before any real usage exists, has
  nothing yet to sample a golden set from. The right move at that stage is a
  small smoke-test set built from the team's own best guesses, explicitly
  labeled as provisional, replaced by a distribution-representative set
  once real usage data exists. Treating the guessed set as authoritative
  past that point is the applicability mistake, not the existence of a
  provisional set itself.
- **As the sole grading mechanism for open-ended creative generation with no
  meaningful notion of correctness**, for example a brainstorming assistant
  where the useful signal is user preference among several plausible ideas
  rather than agreement with one reference idea. A golden set built for
  this case degenerates into grading style rather than substance and gives
  a false sense of rigor. Preference-based or pairwise comparison
  evaluation fits this situation better than a reference-answer golden set.

## 5. Structure

A golden dataset implementation has five participants, and confusing their
responsibilities is the single most common design mistake teams make when
building one for the first time.

- **The golden case.** The atomic unit. Minimally an identifier, an input,
  and an expected output or a rubric describing what a correct output looks
  like. Real implementations add tags for filtering (by feature area, by
  difficulty, by whether the case is a known edge case), a tolerance or
  passing threshold when grading is not exact match, and provenance metadata
  recording whether the case came from a real production trace, a synthetic
  generation pass, or a hand-written adversarial probe. Braintrust's schema
  is representative. an input field holding "the data needed to recreate the
  example" and an expected field holding the "ideal output or ground truth,
  optional but recommended" ([Braintrust, Datasets guide](https://www.braintrust.dev/docs/guides/datasets),
  verified 2026-08-02).
- **The golden set (or dataset).** A named, versioned collection of golden
  cases. Versioning matters because the set changes over time and a
  regression run needs to say precisely which version of the set it ran
  against, so that a later investigation into "why did the score drop" can
  rule in or rule out a change to the set itself as the cause, separate from
  a change to the system under test.
- **The system under test.** The application, agent, or model call being
  evaluated. Structurally, this participant is a black box to the runner. it
  is invoked once per case with the case's input and returns an output; the
  runner never inspects or modifies its internals.
- **The judge, or grader.** A function that compares the system's actual
  output to the case's expected output or rubric and produces a score, most
  simply a boolean pass or fail, more commonly a numeric score in a fixed
  range. The judge is itself pluggable, and the most consequential design
  decision in the whole pattern, covered in depth under Implementation
  variants, is which kind of judge a given case uses. exact match, structural
  or schema match, a deterministic similarity metric, or an LLM-as-judge call
  calibrated against this same golden set.
- **The runner and reporter.** The controller that iterates the golden set,
  invokes the system under test for each case, invokes the judge, aggregates
  the per-case results into a summary (pass rate, mean score, score by tag,
  a diff against the previous run), and surfaces that summary somewhere a
  human or a CI pipeline can act on it, typically as a pass or fail exit code
  plus a human-readable report of exactly which cases regressed and how.

The participants compose in one direction only, from case through system
under test through judge to report, which is what makes the pattern
straightforward to implement correctly and also what makes it easy to
implement incorrectly by collapsing two participants into one, most often by
letting the same call that produces the actual output also decide, without a
separate judge, whether that output is correct. Keeping the judge structurally
separate from the system under test is what makes the runner trustworthy,
because a system that grades its own homework has no external check on it at
all.

## 6. ASCII structure diagram

```
+-------------------+        +----------------------+
|  Golden Set        |        |  System Under Test    |
|  (versioned)        |        |  (the agent, prompt,  |
|                      |        |   or pipeline being   |
|  +----------------+  |        |   regression tested)  |
|  | Golden Case #1 |  |        +----------------------+
|  | input, expected |  |                 ^
|  | tags, tolerance |  |                 | input
|  +----------------+  |                 |
|  | Golden Case #2 |  |----invoke------->|
|  +----------------+  |                 |
|  |      ...        |  |                 | actual output
|  +----------------+  |                 v
|                      |        +----------------------+
+----------+-----------+        |       Judge           |
           |                    |  exact match, schema   |
           | expected           |  match, similarity,     |
           +------------------->|  or calibrated LLM      |
                                 |  judge                  |
                                 +----------+-------------+
                                            |
                                            | per-case score
                                            v
                                 +----------------------+
                                 |  Runner and Reporter   |
                                 |  aggregate pass rate,   |
                                 |  diff vs prior run,     |
                                 |  fail CI on threshold   |
                                 +----------------------+
```

The diagram deliberately keeps the judge as a separate box from both the
golden set and the system under test, because collapsing that separation, for
example by letting the system under test self-report whether it succeeded,
removes the one independent check the whole structure exists to provide.

## 7. Dynamics

A golden-set run has two distinct execution modes that share the same
structure but different triggers and different consequences on failure.

The first mode is the pre-merge or pre-deploy regression check. A developer
changes a prompt, a retrieval step, or a model version pin, opens a pull
request, and a CI job runs the fast subset of the golden set (see
Implementation variants for why a fast subset, not the full set, usually runs
here) against the new code path. If the pass rate or mean score drops below a
configured threshold relative to the last known-good run, the CI job fails
and the merge is blocked, the same mechanism a conventional test suite uses,
with the difference that a small drop within noise tolerance is expected and
tolerated rather than treated as an automatic failure, because the judge
itself, especially an LLM judge, is not perfectly deterministic across runs.

The second mode is the scheduled or release-gate full run, typically executed
nightly or immediately before a production deploy, against the entire golden
set including the slower, more expensive, more thoroughly graded cases that
are too costly to run on every commit. This run produces the artifact a team
actually trusts for a go or no-go release decision, and it is the run whose
results get archived for longitudinal tracking, so that a slow three-week
drift in quality, invisible in any single day's noise, becomes visible as a
trend line.

```
   developer         CI (fast subset)         golden set store
       |                    |                        |
       | open PR            |                        |
       |------------------->|                        |
       |                    | fetch pinned version    |
       |                    |----------------------->|
       |                    |<-----------------------|
       |                    | for each case:          |
       |                    |   run system under test |
       |                    |   run judge              |
       |                    |   record score           |
       |                    | compare to baseline run  |
       |                    |------------------------>|
       |                    |         (score history)  |
       |    pass / fail     |<------------------------|
       |<-------------------|
       |
   [merge blocked on fail, or annotated warning on marginal drop]

   ---------------------------------------------------------------

   scheduler          full runner            report + longitudinal store
       |                    |                        |
       | nightly trigger    |                        |
       |------------------->|                         |
       |                    | run ALL cases,          |
       |                    | expensive judges too     |
       |                    | (may take minutes)        |
       |                    |------------------------->|
       |                    |                          | store, trend,
       |                    |                          | alert on drift
       |                    |<-------------------------|
```

A third, less structural but frequently observed dynamic worth naming
explicitly is dataset growth. every real production failure a team
investigates by hand, once diagnosed, is a candidate to become a new golden
case, appended to the set with the correct expected output attached, so the
same regression can never silently reappear undetected. This closes the loop
between production monitoring and the golden set, and teams that skip it
watch the same class of bug recur every few months because nothing ever
turned the incident into a permanent test.

## 8. Implementation variants

**Exact match.** The judge is a byte-for-byte or, more forgivingly, a
whitespace-normalized string comparison. Cheapest, fastest, fully
deterministic, and the correct choice whenever the system's contract is a
narrow, structured output, a classification label, a fixed enum, a single
number. Wrong for open-ended natural language generation, where it produces
a wall of false failures on acceptable paraphrases and trains the team to
stop trusting or reading the report.

**Structural or schema match.** The judge parses the actual output (most
commonly JSON) and checks specific fields, key presence, types, and value
ranges, rather than the full string. This tolerates variation in fields that
do not matter (a natural-language explanation field, a timestamp) while
staying exact on the fields that do (a routed queue name, a numeric total, a
boolean approval decision). This is the workhorse variant for agents whose
final action is a structured tool call or a decision, and it composes
naturally with the Structured Output and Function Calling patterns in this
catalog, since both already constrain the model to emit a schema the judge
can parse deterministically.

**Deterministic similarity metrics.** Token overlap, edit distance, ROUGE or
BLEU-style n-gram overlap, or embedding cosine similarity against the
expected output, compared to a numeric threshold rather than requiring
identity. Cheaper and faster than an LLM judge, fully reproducible run to
run, but a comparatively weak proxy for actual correctness, since a
high-overlap answer can still be factually wrong in the one detail that
matters, and a low-overlap answer can still be correct if it is a valid
paraphrase that happens to share few surface tokens with the reference. Best
used as a fast pre-filter, cheap enough to run on every commit, ahead of a
slower and more accurate judge reserved for the nightly run.

**LLM-as-judge, calibrated against the golden set.** The judge is itself
another model call, given the input, the expected output or rubric, and the
system's actual output, and asked to score or classify the match. This is
the most flexible variant and the only one that scales to genuinely
open-ended natural language grading, but it introduces a new and important
obligation. the judge itself must be validated against human judgment before
it is trusted, and the golden set is exactly the mechanism used to do that
validation, by comparing the judge's verdicts on a sample of cases against
human-labeled verdicts on the same cases. Zheng et al.'s study of LLM judges
found that a strong model used as a judge achieved "over 80 percent agreement"
with human preference judgments, "the same level of agreement between
humans" themselves ([Zheng, Chiang, Sheng, Zhuang, Wu, Zhuang, Lin, Li, Li,
Xing, Zhang, Gonzalez, Stoica, "Judging LLM-as-a-Judge with MT-Bench and
Chatbot Arena," 2023, https://arxiv.org/abs/2306.05685](https://arxiv.org/abs/2306.05685),
verified 2026-08-02), which is a strong result but also, read carefully,
an admission that roughly one case in five will disagree with what a human
reviewer would have said, a rate that matters when the judge is deciding
whether a release ships.

**Synthetically generated golden sets.** Rather than hand-writing every
case, a separate model call generates candidate cases (a question, a
grounding context, and an expected answer derived from that context), which
a human then spot-checks and corrects rather than authors from scratch. Ragas
built dedicated tooling around exactly this workflow for retrieval-augmented
pipelines, stating that curating a high quality test dataset matters greatly
for evaluating an AI application, and offering automated generation because
manual curation is "time-consuming and expensive"
([Ragas documentation, Test data generation](https://docs.ragas.io/en/stable/concepts/test_data_generation/),
verified 2026-08-02). This variant trades authoring cost for review cost, and
it works best when the source corpus used to generate cases from is itself
representative of the real task distribution, since a generator conditioned
on the wrong corpus will produce a golden set that is fluent but
distributionally wrong.

**Two-tier fast and slow sets.** Nearly every production implementation of
this pattern in practice ends up as two sets rather than one. a small (tens
to low hundreds of cases), cheap, fast-graded set that runs on every pull
request within a minute or two, and a large (hundreds to low thousands of
cases), more thoroughly graded set that runs nightly or before a release.
promptfoo's own tooling encodes this split directly, supporting both
hand-authored test cases stored as YAML or CSV and a `promptfoo generate
dataset` command that its own documentation describes as extending an
existing set of cases into a wider and more varied one, suited to the
larger, slower tier ([promptfoo documentation, Datasets](https://www.promptfoo.dev/docs/configuration/datasets/),
verified 2026-08-02).

## 9. Known production uses

**OpenAI Evals.** OpenAI's open source evaluation framework, publicly
released in 2023, ships both a runner and a registry of pre-built
evaluations, and its documentation frames the goal explicitly as letting
teams build "private evals which represent the common LLM patterns in your
workflow without exposing any of that data publicly," using data provided in
JSON or JSONL with a specified grading template ([OpenAI, Evals repository](https://github.com/openai/evals),
verified 2026-08-02). This is one of the earliest widely adopted, purpose-
built golden dataset systems for LLM applications specifically, as distinct
from general ML testing tooling repurposed for LLMs.

**LangSmith (LangChain).** LangSmith's evaluation product stores golden data
as named datasets composed of examples, each holding "inputs and reference
outputs," and runs an application against a dataset to produce what
LangSmith calls an experiment, "the results of evaluating a specific
application version on a dataset," explicitly supporting regression detection
by comparing experiments across application versions run against the same
fixed dataset ([LangChain, LangSmith evaluation concepts](https://docs.langchain.com/langsmith/evaluation),
verified 2026-08-02).

**Braintrust.** Braintrust's evaluation platform defines a dataset as a
"versioned collection of test cases" with input and expected fields, where
"every change is tracked, so experiments can pin to specific versions," and
datasets are consumed directly by the platform's `Eval()` function or
populated automatically from captured production traffic ([Braintrust,
Datasets guide](https://www.braintrust.dev/docs/guides/datasets), verified
2026-08-02). The explicit versioning and pinning behavior is a direct
production answer to the stability-versus-staleness force described in
dimension 3.

**DeepEval (Confident AI).** DeepEval is a pytest-integrated testing
framework for LLM applications that uses the term golden dataset directly,
building `LLMTestCase` objects around an `expected_output` field described in
its own documentation as "the ideal answer for a given input," run through
standard `deepeval test run` invocations that integrate with existing CI
pipelines the same way a conventional pytest suite would ([Confident AI,
DeepEval repository](https://github.com/confident-ai/deepeval), verified
2026-08-02).

**Ragas.** Ragas is a purpose-built evaluation library for retrieval-
augmented generation pipelines that both consumes and, distinctively,
generates golden test sets. its documentation states that a high quality
test dataset must "cover wide variety of scenarios as observed in real
world" and provides tooling to synthesize such a set automatically from a
source corpus rather than requiring every case to be hand-written ([Ragas
documentation, Test data generation](https://docs.ragas.io/en/stable/concepts/test_data_generation/),
verified 2026-08-02).

**promptfoo.** promptfoo is an open source CLI and CI tool for testing
prompts and LLM configurations against a stored set of test cases, supporting
YAML, CSV, and file-referenced datasets, plus a dataset-expansion command its
own documentation describes as growing an existing set of cases into a wider
and more varied one ([promptfoo documentation, Datasets](https://www.promptfoo.dev/docs/configuration/datasets/),
verified 2026-08-02), commonly wired into a pull request CI gate so a prompt
change that regresses the golden set fails the build before merge.

Across all six, the recurring structural agreement is notable given the
tools were built independently by different companies. every one separates a
versioned collection of input and expected-output pairs from the system
being tested, every one supports a grading step that is pluggable rather than
hard-coded to exact match, and every one is designed to run inside a CI or
CI-adjacent pipeline rather than as an ad hoc manual script.

## 10. Consequences

Positive.

- Converts a class of failure that is otherwise silent and delayed, a
  quality regression discovered by a customer weeks later, into a failure
  that is loud and immediate, caught before merge or before a release ships.
- Gives a team a concrete, falsifiable answer to "is this change better or
  worse," replacing subjective impressions formed from reading a handful of
  examples by hand with a reproducible, comparable number.
- Creates a durable institutional record of what the system is actually
  expected to do, which is valuable independent of testing, as living
  documentation for new engineers and as a specification a product manager
  can review and dispute in plain language rather than in code.
- Enables safe, fast iteration. a team with a trustworthy golden set can try
  many prompt or configuration variants quickly, because each variant gets a
  cheap, automatic verdict instead of an expensive manual review cycle.
- Gives the LLM-as-judge variant, in particular, a way to be calibrated and
  trusted at all. without a human-labeled golden set to check judge
  agreement against, there is no way to know whether the judge itself is
  reliable.

Negative.

- Ongoing maintenance cost that does not shrink over time and, if anything,
  grows as the product surface grows, since every new feature area that
  needs regression protection needs its own golden cases written and kept
  current.
- A false sense of safety when the set's coverage does not actually match
  the real task distribution, which is worse than no golden set at all,
  because a team with a passing golden set stops looking for problems that
  the set was never built to catch.
- Grading cost, in dollars and latency, when the judge is itself an LLM
  call, which scales linearly with set size and can become a meaningful
  recurring expense for large, frequently run sets.
- Risk of Goodhart's law style overfitting, where the system, and sometimes
  the humans maintaining it, optimize specifically for the cases in the set
  rather than for the underlying task, a failure mode explored in depth in
  dimension 11.
- A brittle sense of stability that a frozen set provides, which becomes a
  liability the moment the product itself changes and the set is not updated
  to match, silently testing a version of the product that no longer exists.

## 11. Failure modes and misuse

Symptom. The golden set stays green for months while real users
increasingly complain about answer quality.
Cause. The set was never updated as the product's features and language
evolved, so it is measuring fidelity to a snapshot of the product that no
longer matches what users actually ask or what the system is now supposed to
do; this is dataset staleness, the most common failure of this pattern in
practice.
Fix. Treat the golden set itself as a living artifact with an owner and a
review cadence, feed real production traces (with review, and with any
personal data stripped or synthetic-replaced) into it regularly, and retire
cases whose scenario no longer exists in the current product rather than
leaving them to pass trivially forever.

Symptom. A prompt change scores perfectly against the golden set, then
performs visibly worse in production the same week.
Cause. The set does not represent the real distribution of production
inputs, most often because it was written from the engineering team's own
guesses about how the product is used rather than sampled from actual usage,
or because it over-represents easy cases and under-represents the messy,
ambiguous, or adversarial inputs that make up the tail of real traffic.
Fix. Sample the golden set, or at minimum audit it, against a real
distribution of production inputs, deliberately over-representing edge cases
and known failure categories rather than aiming for a naive uniform sample,
and treat any production incident, once diagnosed, as a mandatory addition
to the set.

Symptom. A model, agent, or the team maintaining a prompt scores
extremely well on the golden set specifically, but a fresh, independently
written set of similar cases exposes the same weaknesses the golden set was
supposed to catch.
Cause. Goodhart's law in its LLM-testing form. the golden set became the
optimization target rather than a sample of the real target, either because
prompt iteration was repeatedly tuned against the same fixed set until it
specifically overfit that set's phrasing and edge cases, or, in the more
severe case, because the golden set's own examples leaked into a fine-tuning
or few-shot prompt corpus, letting the system effectively memorize the
answers rather than generalize the underlying skill. This mirrors the
statistical finding that adaptively reusing a fixed holdout set repeatedly
"can easily lead to overfitting to the holdout set itself" ([Dwork, Feldman,
Hardt, Pitassi, Reingold, Roth, "Generalization in Adaptive Data Analysis and
Reusable Holdout," 2015, https://arxiv.org/abs/1506.02629](https://arxiv.org/abs/1506.02629),
verified 2026-08-02), a result originally about classical statistics and
Kaggle-style leaderboards that transfers directly to LLM golden sets.
Fix. Keep a strict wall between the golden set and any training or
few-shot data, rotate in a periodically refreshed holdout slice that is
never shown during development, and treat a large gap between golden-set
score and score on a genuinely fresh sample as the specific signal that
overfitting has happened.

Symptom. A published benchmark reports near-perfect scores for a model
that then performs poorly on private, task-specific golden cases covering
the same nominal skill.
Cause. Benchmark contamination. the benchmark's own questions, or close
paraphrases of them, ended up inside the model's pretraining corpus, so the
model is recalling answers it has effectively seen rather than demonstrating
the underlying capability. Yang et al. showed that even simple paraphrasing
or translation of contaminated test data "can easily bypass" standard
string-matching decontamination checks, and that a comparatively small model
"can easily overfit a test benchmark and achieve drastically high
performance, on par with" a much larger, genuinely capable model once
contaminated data has leaked in ([Yang, Chiang, Zheng, Gonzalez, Stoica,
"Rethinking Benchmark and Contamination for Language Models with Rephrased
Samples," 2023, https://arxiv.org/abs/2311.04850](https://arxiv.org/abs/2311.04850),
verified 2026-08-02), with contamination overlap measured at 8 to 18 percent
even for a widely used coding benchmark.
Fix. Never rely on a public benchmark as the primary evidence a specific
application will work well. build a private golden set from that
application's own real task distribution, kept unpublished specifically so
it cannot be scraped into any future model's pretraining data, and treat a
public benchmark score as background context, not as a substitute for
task-specific evaluation.

Symptom. The judge disagrees with a human reviewer on a meaningful
fraction of cases, and nobody notices for months because the judge's own
output was never checked against a human baseline.
Cause. An LLM-as-judge was deployed without calibration, the exact
failure the golden set is supposed to prevent, applied recursively to the
judge itself; even a strong judge model in the best-documented study still
disagreed with human judgment on a meaningful minority of cases, roughly one
in five, when measured directly against human raters ([Zheng et al.,
2023](https://arxiv.org/abs/2306.05685), verified 2026-08-02).
Fix. Periodically sample the judge's verdicts, have a human independently
grade the same sample, and measure agreement explicitly rather than assuming
it; if agreement drops below an acceptable threshold, tighten the grading
rubric, switch to a stronger judge model, or fall back to a stricter
deterministic grader for the affected case categories.

## 12. Trade-off matrix

| Concern | Golden Dataset | Public Benchmark Alone | LLM-as-Judge with No Golden Calibration | Manual Spot-Check Review |
|---|---|---|---|---|
| Catches task-specific regressions | Strong, by construction sampled from the real task | Weak, measures general capability, not this application's behavior | Moderate, depends entirely on judge quality, which is unverified | Strong on the cases reviewed, weak everywhere else |
| Resistant to contamination | Strong if kept private and unpublished | Weak, public sets are frequently leaked into pretraining data | Neutral, contamination risk lives in the underlying judge model | Strong, no training-data overlap is possible |
| Reproducible and CI friendly | Strong, deterministic grading variants run identically every time | Strong for the score itself, but score is often unrelated to the app | Weak to moderate, LLM judge output can vary run to run | Not automatable at all |
| Ongoing maintenance cost | High, needs regular curation and review | Low, maintained by the benchmark's publisher | Low to build, hidden cost in undetected judge drift | High, does not scale with iteration speed |
| Cost per run | Low to moderate, scales with set size and judge type | Usually free or a fixed published cost | Moderate to high, per-call model cost every run | High in human time, effectively unbounded |
| Detects silent, gradual quality drift | Strong, especially with longitudinal score tracking | Weak, snapshot in time, rarely re-run per application | Weak without periodic recalibration | Weak, humans do not review consistently over time |
| Speed of iteration it enables | Fast once built, minutes per run | Fast but low signal for a specific product | Fast, but confidence in the result is unverified | Slow, bottlenecked on human availability |

## 13. Related and incompatible patterns

**LLM as Judge.** The single most consequential grading variant of this
pattern, and the pattern most dependent on it in the reverse direction too. a
golden dataset with known-correct human labels is the only reliable way to
calibrate and validate an LLM judge's agreement rate before trusting it, and
an uncalibrated judge is one of the failure modes documented above. The two
patterns are usually implemented together rather than in isolation.

**Evaluator-Optimizer.** Evaluator-Optimizer is the runtime loop in which a
generation is critiqued and revised by a second model call before the final
output is returned to the user. A golden dataset is the offline, pre-deploy
counterpart. it measures whether the evaluator-optimizer loop, as a whole
system, is actually improving output quality over time, and it is the tool a
team uses to decide whether the extra latency and cost of running that loop
at all is earning its keep.

**Reflexion.** Reflexion has the agent self-critique and retry within a
single episode based on its own reasoning about a failure. A golden dataset
supplies the external, offline signal of whether that self-critique loop is
producing genuinely better final answers across many episodes, something the
agent's own internal self-assessment cannot verify on its own, since a
self-critiquing system grading its own work has no independent check.

**Self-Consistency.** Self-Consistency samples multiple reasoning paths at
inference time and takes a majority or aggregated answer to raise
correctness on any single query. A golden dataset is what proves this
technique is actually raising correctness for a given task rather than only
raising confidence, by comparing single-sample and self-consistency-sampled
accuracy against the same fixed set of labeled cases.

**Human in the Loop.** The two patterns divide the same underlying question,
is this output correct, across two different timeframes. Human in the Loop
answers it live, per request, for cases the system is not trusted to handle
alone. A golden dataset answers a related but distinct question offline and
in aggregate, is the system, as currently configured, trustworthy across a
representative sample of the whole task, which is exactly the evidence a
team needs to decide where to draw the human-in-the-loop boundary in the
first place.

**Output Guardrails and Input Guardrails.** Guardrails are runtime checks
that block or rewrite a bad output or a bad input as it happens, in
production, on every single request. A golden dataset is the pre-deploy test
that measures whether a change to those guardrails, or to the system they
protect, is working as intended, before it ever reaches a real request.

**Cost Guard.** A golden dataset that includes cost or token-count fields per
case, alongside correctness, is the input a Cost Guard budget policy is
tuned against. teams that measure only correctness and never cost per case in
the same golden run routinely discover, only after a bill arrives, that a
quality improvement they shipped tripled the per-request cost.

No pattern in this catalog is genuinely incompatible with a golden dataset;
the pattern is a measurement discipline that sits alongside, rather than in
competition with, the runtime patterns it evaluates.

## 14. Refactoring path in and out

Introducing a golden dataset into a system that has none. Start by
reading real interaction logs or traces, not by guessing at test cases from
first principles, echoing the explicit advice to "examine as much data as
possible" before writing formal tests ([Husain, "Your AI product needs
evals"](https://hamel.dev/blog/posts/evals/), verified 2026-08-02). Pull a
sample of twenty five to fifty real inputs, hand-label the correct or
acceptable output for each, and start with the crudest grader that could
plausibly work, exact match or a simple structural check, rather than
building an LLM judge on day one. Wire that small set into CI as a
non-blocking, informational check first, so the team can see how noisy the
signal is before making it a merge gate. Once the small set is trusted,
grow it in two directions at once. add more cases sampled from a wider slice
of real traffic, and, separately, add a slower, more accurate grading tier
for cases the fast exact-match grader cannot handle. Every production
incident diagnosed from this point forward becomes a mandatory new case, with
its correct expected output recorded at the moment it is fixed, while
memory of the failure is still fresh and precise.

Removing or retiring a golden dataset. A golden set earns retirement,
partially or entirely, when one of three conditions holds. the feature area
it covers has been permanently removed from the product, so the cases no
longer describe anything real and are pure dead weight; the cases have been
superseded by a newer, better-calibrated set covering the same ground, in
which case the old set should be archived rather than silently deleted, so
its history remains available for later investigation; or the system under
test has become so stable, and changes to it so rare, that the ongoing
maintenance cost of the set exceeds the value of the regression protection
it provides, a genuine but uncommon case that is worth naming explicitly
rather than pretending every golden set must live forever. Retirement should
never mean simply deleting the CI check and hoping nobody notices; it should
be a deliberate, documented decision, because the absence of a regression
check is itself a fact worth recording for the next engineer who touches
this code.

## 15. Testing and verification

Testing a golden dataset system itself, as distinct from testing the system
it is used to evaluate, has two layers that are frequently conflated.

The first layer is testing the runner code, the loader, the aggregator, and
the CI integration, using ordinary unit tests exactly like any other piece
of software. Does the loader correctly parse a malformed JSONL line and fail
loudly rather than silently skipping it. Does the aggregator compute the
pass rate correctly when a case is skipped versus when it fails. Does the CI
exit code correctly reflect a threshold breach. This layer is fully
deterministic and needs no special technique beyond conventional software
testing discipline, which is precisely what the code samples in dimension 8
and the appendix demonstrate.

The second, harder layer is testing the grader itself for accuracy,
sometimes called meta-evaluation. an exact-match or schema-match grader is
self-verifying by construction, its correctness is a property of the code,
not a statistical claim. A similarity-metric or LLM-as-judge grader is not
self-verifying, and needs its own held-out sample of cases where a human has
independently produced the correct verdict, against which the grader's
agreement rate is measured directly, the same technique Zheng et al. used to
validate an LLM judge against human preference data before trusting it at
scale ([Zheng et al., 2023](https://arxiv.org/abs/2306.05685), verified
2026-08-02). A team should be able to state a specific number, this grader
agrees with human judgment on roughly this percentage of cases, and should
re-measure that number whenever the underlying judge model changes, rather
than assuming agreement holds forever once measured once.

A third, easily forgotten check is a test for the golden set's own internal
consistency. two cases that appear near-duplicates but carry contradictory
expected outputs, an expected output that has silently become factually
wrong because the underlying product changed, or a case whose input no
longer parses under the system's current input schema. A lightweight linter
that flags exact or near-duplicate inputs, and a periodic manual audit pass
of a random sample of existing cases, catches this class of rot before it
silently degrades trust in the whole set.

## 16. Observability signals

A healthy golden dataset practice produces a small number of signals worth
tracking on a dashboard rather than only reading at the moment CI passes or
fails.

- Pass rate and mean score over time, per golden-set version. A flat or
  improving trend line is healthy. A slow downward drift, even one still
  above the CI threshold, is the earliest possible warning of the staleness
  or overfitting failure modes described above, and it is invisible if the
  only thing tracked is a binary pass or fail per run.
- Score broken down by tag or category, not only in aggregate. An
  aggregate pass rate can stay flat while one category, for example a
  specific feature area or a specific edge case tag, quietly worsens,
  masked by improvement elsewhere. Tracking per-tag score is what surfaces
  this before an aggregate number does.
- Judge-versus-human agreement rate, re-measured periodically, for any
  LLM-as-judge grader. This is the meta-evaluation signal from dimension
  15, tracked over time rather than measured once, because model upgrades
  and prompt changes to the judge itself can silently shift its calibration.
- Set size and case age, tracked as its own metric. A golden set that
  has not grown or had cases refreshed in months, while the underlying
  product has shipped several features in the same period, is a leading
  indicator of the coverage-gap failure mode, visible before it produces an
  actual missed regression.
- Grading cost and latency per run. Especially for LLM-as-judge graders,
  a slow creeping increase in per-run cost, often caused by a growing set
  combined with a more expensive judge model swapped in without a
  deliberate decision, is worth alerting on independently of correctness
  metrics.
- Time-to-detect for known incidents. When a production regression is
  eventually diagnosed, checking whether the golden set would have caught
  it, and if not, why not, closes the loop and is the single most useful
  retrospective question a team can ask about its own evaluation practice.

## 17. Security and privacy implications

A golden dataset built from real production traces necessarily contains real
user data, or close derivatives of it, unless deliberate steps are taken to
prevent that. The most direct implication is that any personal, confidential,
or regulated data present in a source trace, a customer's name, an account
number, a health detail, a legal matter, carries forward into the golden
case, into whatever storage and version control system holds the set, and
into any third-party evaluation platform the set is uploaded to for grading.
Treat construction of a golden set from production data as a data handling
decision subject to the same review, redaction, and retention policy as
production data itself, not as an exempt engineering artifact, because it is
frequently stored with weaker access controls than the production database
it was sampled from.

A second, less obvious implication is exposure through the grading path
itself. when the judge is a third-party hosted LLM call, every golden case,
including its expected output, is sent to that third party on every run,
which for a case built from sensitive production data means sensitive data
leaves the organization's boundary on a recurring, automated schedule,
frequently more often than the original production data itself was ever
transmitted externally. Redaction or synthetic substitution of identifying
details before a case enters the golden set, kept functionally equivalent
for grading purposes, is the standard mitigation, and it should happen once
at case-authoring time rather than being left to whoever runs the suite to
remember on every invocation.

A third implication is specific to public benchmarks used as a stand-in for
a private golden set, and it runs in the opposite direction from the first
two. a benchmark published openly on the internet is not a privacy risk to
the organization that publishes it, but it is a security and validity risk
to everyone downstream who relies on it, precisely because a public set is
the one most likely to leak into a future model's pretraining corpus and
silently stop measuring what it once measured, the contamination failure
mode documented in dimension 11 with a measured overlap of 8 to 18 percent
for at least one widely used benchmark ([Yang et al., 2023](https://arxiv.org/abs/2311.04850),
verified 2026-08-02). A private, unpublished golden dataset is, among its
other benefits, a defense against this specific and largely unfixable class
of validity decay.

## 18. References

- Michael Feathers, *Working Effectively with Legacy Code*, Prentice Hall,
  2004, ISBN 0-13-117705-2. Golden master and characterization testing, the
  software-testing origin of the term golden applied to a fixed reference
  output.
- Wikipedia, "Characterization test," summary of Feathers' technique,
  https://en.wikipedia.org/wiki/Characterization_test, verified 2026-08-02.
- OpenAI, Evals repository README, https://github.com/openai/evals, verified
  2026-08-02.
- LangChain, "LangSmith evaluation," https://docs.langchain.com/langsmith/evaluation,
  verified 2026-08-02.
- Braintrust, "Datasets guide," https://www.braintrust.dev/docs/guides/datasets,
  verified 2026-08-02.
- Confident AI, DeepEval repository, https://github.com/confident-ai/deepeval,
  verified 2026-08-02.
- Ragas documentation, "Test data generation,"
  https://docs.ragas.io/en/stable/concepts/test_data_generation/, verified
  2026-08-02.
- Ragas documentation, "Metrics overview,"
  https://docs.ragas.io/en/stable/concepts/metrics/overview/, verified
  2026-08-02.
- promptfoo documentation, "Datasets,"
  https://www.promptfoo.dev/docs/configuration/datasets/, verified
  2026-08-02.
- Anthropic, "Test and evaluate, Developing test cases,"
  https://platform.claude.com/docs/en/test-and-evaluate/develop-tests,
  verified 2026-08-02.
- Hamel Husain, "Your AI product needs evals," https://hamel.dev/blog/posts/evals/,
  verified 2026-08-02.
- Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu,
  Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric P. Xing, Hao Zhang,
  Joseph E. Gonzalez, Ion Stoica, "Judging LLM-as-a-Judge with MT-Bench and
  Chatbot Arena," 2023, https://arxiv.org/abs/2306.05685, verified
  2026-08-02.
- Shuo Yang, Wei-Lin Chiang, Lianmin Zheng, Joseph E. Gonzalez, Ion Stoica,
  "Rethinking Benchmark and Contamination for Language Models with Rephrased
  Samples," 2023, https://arxiv.org/abs/2311.04850, verified 2026-08-02.
- Cynthia Dwork, Vitaly Feldman, Moritz Hardt, Toniann Pitassi, Omer
  Reingold, Aaron Roth, "Generalization in Adaptive Data Analysis and
  Reusable Holdout," 2015, https://arxiv.org/abs/1506.02629, verified
  2026-08-02.

## Appendix. Reference implementations

The three samples below implement the same structure, a golden case record,
a system under test, a pluggable judge, and a runner that fails loudly on
regression, in three languages. Each was compiled or run directly before
inclusion here.

### Python. JSONL-backed runner with exact-match grading and a unified diff

```python
"""Golden dataset regression runner. Runs a fixed set of input and expected
pairs against a system under test and reports drift, never correctness."""

from __future__ import annotations

import dataclasses
import difflib
import json
from pathlib import Path
from typing import Callable


@dataclasses.dataclass(frozen=True)
class GoldenCase:
    id: str
    input: dict
    expected: str
    tags: tuple[str, ...] = ()


@dataclasses.dataclass
class CaseResult:
    case_id: str
    passed: bool
    actual: str
    diff: str


def load_golden_set(path: Path) -> list[GoldenCase]:
    cases: list[GoldenCase] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            cases.append(
                GoldenCase(
                    id=record["id"],
                    input=record["input"],
                    expected=record["expected"],
                    tags=tuple(record.get("tags", [])),
                )
            )
    return cases


def run_golden_set(
    cases: list[GoldenCase],
    system_under_test: Callable[[dict], str],
    judge: Callable[[str, str], bool],
) -> list[CaseResult]:
    results = []
    for case in cases:
        actual = system_under_test(case.input)
        passed = judge(case.expected, actual)
        diff = ""
        if not passed:
            diff = "\n".join(
                difflib.unified_diff(
                    case.expected.splitlines(),
                    actual.splitlines(),
                    lineterm="",
                )
            )
        results.append(CaseResult(case.id, passed, actual, diff))
    return results


def exact_match_judge(expected: str, actual: str) -> bool:
    return expected.strip() == actual.strip()


def _demo_system(payload: dict) -> str:
    order_total = sum(item["price"] * item["qty"] for item in payload["items"])
    return f"total={order_total:.2f}"


if __name__ == "__main__":
    demo_cases = [
        GoldenCase(
            id="single-item",
            input={"items": [{"price": 9.5, "qty": 2}]},
            expected="total=19.00",
            tags=("pricing",),
        ),
        GoldenCase(
            id="empty-cart",
            input={"items": []},
            expected="total=0.00",
            tags=("edge-case",),
        ),
    ]
    outcomes = run_golden_set(demo_cases, _demo_system, exact_match_judge)
    failed = [r for r in outcomes if not r.passed]
    for r in outcomes:
        status = "PASS" if r.passed else "FAIL"
        print(f"{status} {r.case_id}")
    if failed:
        raise SystemExit(f"{len(failed)} golden case(s) regressed")
```

Compiled with `python3 -m py_compile` and run directly. output was
`PASS single-item` and `PASS empty-cart`, exit code 0.

### Go. Similarity-graded runner for open-ended text output

```go
package main

import (
	"fmt"
	"os"
	"strings"
)

type GoldenCase struct {
	ID       string
	Prompt   string
	Expected string
	Tags     []string
}

type CaseResult struct {
	CaseID     string
	Similarity float64
	Passed     bool
}

// SystemUnderTest is the agent or pipeline being regression tested.
type SystemUnderTest func(prompt string) string

func runGoldenSet(cases []GoldenCase, sut SystemUnderTest, threshold float64) []CaseResult {
	results := make([]CaseResult, 0, len(cases))
	for _, c := range cases {
		actual := sut(c.Prompt)
		sim := tokenOverlap(c.Expected, actual)
		results = append(results, CaseResult{
			CaseID:     c.ID,
			Similarity: sim,
			Passed:     sim >= threshold,
		})
	}
	return results
}

// tokenOverlap stands in for a real semantic similarity metric. A production
// runner calls an embedding model or an LLM judge instead of this.
func tokenOverlap(expected, actual string) float64 {
	expTokens := strings.Fields(strings.ToLower(expected))
	actTokens := make(map[string]bool)
	for _, t := range strings.Fields(strings.ToLower(actual)) {
		actTokens[t] = true
	}
	if len(expTokens) == 0 {
		return 1.0
	}
	hit := 0
	for _, t := range expTokens {
		if actTokens[t] {
			hit++
		}
	}
	return float64(hit) / float64(len(expTokens))
}

func main() {
	cases := []GoldenCase{
		{
			ID:       "refund-policy",
			Prompt:   "What is the refund window?",
			Expected: "refund window is thirty days",
			Tags:     []string{"policy"},
		},
	}
	sut := func(prompt string) string {
		return "our refund window is thirty days from purchase"
	}
	results := runGoldenSet(cases, sut, 0.6)
	failed := 0
	for _, r := range results {
		status := "PASS"
		if !r.Passed {
			status = "FAIL"
			failed++
		}
		fmt.Printf("%s %s similarity=%.2f\n", status, r.CaseID, r.Similarity)
	}
	if failed > 0 {
		os.Exit(1)
	}
}
```

Checked with `go vet` and executed with `go run`. output was `PASS
refund-policy similarity=1.00`, exit code 0.

### TypeScript. Typed, generic runner for a structured agent decision

```typescript
interface GoldenCase<TInput, TOutput> {
  id: string;
  input: TInput;
  expected: TOutput;
  tolerance?: number;
}

interface CaseReport {
  id: string;
  passed: boolean;
  score: number;
}

type Judge<TOutput> = (expected: TOutput, actual: TOutput) => number;
type SystemUnderTest<TInput, TOutput> = (input: TInput) => TOutput;

function runGoldenSet<TInput, TOutput>(
  cases: ReadonlyArray<GoldenCase<TInput, TOutput>>,
  sut: SystemUnderTest<TInput, TOutput>,
  judge: Judge<TOutput>
): CaseReport[] {
  return cases.map((c) => {
    const actual = sut(c.input);
    const score = judge(c.expected, actual);
    const threshold = c.tolerance ?? 1.0;
    return { id: c.id, passed: score >= threshold, score };
  });
}

function exactMatchJudge<T>(expected: T, actual: T): number {
  return JSON.stringify(expected) === JSON.stringify(actual) ? 1 : 0;
}

interface RoutingInput {
  ticketText: string;
}

interface RoutingOutput {
  queue: "billing" | "technical" | "sales";
}

function classifyTicket(input: RoutingInput): RoutingOutput {
  if (input.ticketText.toLowerCase().includes("invoice")) {
    return { queue: "billing" };
  }
  return { queue: "technical" };
}

const goldenSet: GoldenCase<RoutingInput, RoutingOutput>[] = [
  { id: "billing-1", input: { ticketText: "my invoice is wrong" }, expected: { queue: "billing" } },
  { id: "tech-1", input: { ticketText: "the app crashes on launch" }, expected: { queue: "technical" } },
];

const reports = runGoldenSet(goldenSet, classifyTicket, exactMatchJudge);
const regressed = reports.filter((r) => !r.passed);

if (regressed.length > 0) {
  console.error(`${regressed.length} golden case(s) regressed`, regressed);
  process.exitCode = 1;
} else {
  console.log(`golden set green: ${reports.length} cases`);
}
```

Type-checked with `tsc --noEmit --strict` and run with `tsx`. output was
`golden set green: 2 cases`, exit code 0.
