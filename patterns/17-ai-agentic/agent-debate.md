---
name: Agent Debate
slug: agent-debate
family: 17-ai-agentic
category: Workflow
aliases: [Multi-Agent Debate, MAD, LLM Debate, Society of Minds Debate, ChatEval-style Debate]
first_described: "Irving, Christiano, Amodei, AI Safety via Debate, May 2018"
maturity: established
related: [multi-agent-supervisor, evaluator-optimizer, orchestrator-worker, self-consistency, reflexion, tree-of-thoughts, hierarchical-agents]
incompatible_with: []
verified: 2026-08-02
---

# Agent Debate

## 1. Name, aliases, and lineage

The name in current use is Agent Debate, sometimes written Multi-Agent Debate
or shortened to the acronym MAD in the research literature. The idea traces
to Geoffrey Irving, Paul Christiano, and Dario Amodei, "AI Safety via
Debate," OpenAI, May 2018, arXiv 1805.00899
(https://arxiv.org/abs/1805.00899, verified 2026-08-02). That paper frames
debate as a training and evaluation protocol rather than an inference-time
workflow. two agents "take turns making short statements up to a limit,
then a human judges which of the agents gave the most true, useful
information," and the authors show empirically on MNIST that debate between
two agents raises a judge's classification accuracy from 59.4 percent to
88.9 percent using six revealed pixels (same source, verified 2026-08-02).
The theoretical motivation given is a complexity-class argument, that debate
with optimal play can in principle resolve questions in PSPACE using a
judge that only needs to verify a polynomial-time argument, where direct
judgment is limited to NP-style questions (same source, verified 2026-08-02).

The pattern reappeared as an inference-time technique, without any training
step, in Yilun Du, Shuang Li, Antonio Torralba, Joshua B. Tenenbaum, and
Igor Mordatch, "Improving Factuality and Reasoning in Language Models
through Multiagent Debate," May 2023, arXiv 2305.14325
(https://arxiv.org/abs/2305.14325, verified 2026-08-02). This is the paper
most people mean today when they say agent debate in an LLM context. it
proposes that "multiple language model instances propose and debate their
individual responses and reasoning processes over multiple rounds to arrive
at a common final answer," and reports gains in mathematical reasoning,
strategic reasoning, and factual question answering, plus a reduction in
hallucinated statements, using off-the-shelf models with no fine-tuning
(same source, verified 2026-08-02).

A closely related line of work is Tian Liang, Zhiwei He, Wenxiang Jiao,
Xing Wang, Yan Wang, Rui Wang, Yujiu Yang, Zhaopeng Tu, and Shuming Shi,
"Encouraging Divergent Thinking in Large Language Models through
Multi-Agent Debate," May 2023, arXiv 2305.19118, with reference
implementation at github.com/Skytliang/Multi-Agents-Debate (verified
2026-08-02). That paper coins the term MAD as an acronym and names the
failure mode it targets directly, Degeneration-of-Thought, the tendency of
a single model doing iterative self-reflection to converge prematurely on
one answer and stop revising it even when that answer is wrong. It assigns
one agent an affirmative stance and one a negative stance, with a third
judge agent moderating, so the debate is adversarial by construction rather
than cooperative (same source, verified 2026-08-02).

A fourth thread applies the same shape to evaluation rather than generation.
Chi-Min Chan, Weize Chen, Yusheng Su, Jianxuan Yu, Wei Xue, Shanghang
Zhang, Jie Fu, and Zhiyuan Liu, "ChatEval, Towards Better LLM-based
Evaluators through Multi-Agent Debate," August 2023, arXiv 2308.07201,
reference implementation at github.com/chanchimin/ChatEval, maintained by
the Tsinghua University NLP lab, THUNLP (verified 2026-08-02). ChatEval
assigns each debating agent a persona, for example Critic or General
Public, so the debate covers more evaluation criteria than a single judge
would surface on its own (same source, verified 2026-08-02).

Two names are used loosely enough to cause confusion and are worth pulling
apart here. Debate is not the same as a panel of independent evaluators
voting without communication, which the self-consistency and LLM-as-jury
literature calls ensembling or majority voting, and it is not the same as a
single generator being critiqued by a single fixed critic in one pass,
which this catalog treats separately as Evaluator-Optimizer. Debate
requires at least one exchange where an agent's output is conditioned on
what an opposing agent argued in a prior round. Remove that back-and-forth
and the mechanism degrades into one of those simpler patterns.

## 2. Problem and context

A single model call, even a large capable one, has three structural
weaknesses that a reader can observe directly. It is confidently wrong on a
non-trivial fraction of factual and multi-step reasoning questions and does
not reliably signal which fraction that is. Sampling the same prompt
repeatedly at nonzero temperature usually returns variants of the same
answer rather than genuinely independent attempts, because the model's own
prior dominates every draw. And when asked to check its own work in a
second pass, it tends to rubber-stamp the first answer, a documented failure
Liang et al. name Degeneration-of-Thought, because a model correcting itself
starts from, and is anchored to, the very reasoning that produced the
mistake (Liang et al. 2023, arXiv 2305.19118, verified 2026-08-02).

Agent debate exists for the situation where a task has no cheap ground
truth to check against, so a static rubric or an automated test cannot
settle whether an answer is right, and the cost of a wrong answer is high
enough to justify spending several model calls to reduce it. Typical
contexts are open-ended factual claims, contested reasoning chains in math
or logic word problems, subjective quality judgments such as which of two
generated summaries reads better, and any evaluation task where a single
LLM-as-judge call is known to carry position bias or verbosity bias that a
second model with an opposing incentive can be structured to expose.

The context that makes debate the right choice rather than a cheaper
alternative is specific. the problem must be genuinely hard to verify
directly but comparatively cheap to verify given a candidate answer and a
rebuttal to it, mirroring the complexity-theoretic argument in the original
Irving, Christiano, and Amodei paper that a judge who cannot solve a
PSPACE problem outright can still adjudicate a debate about it (arXiv 1805.00899,
verified 2026-08-02). Outside that shape, for example a task with a
deterministic checker such as a unit test or a compiler, debate is the
wrong tool. run the checker instead.

## 3. Forces

Judgement. this section weighs which pressure dominates and is not fully
sourced.

Debate spends latency and cost to buy accuracy and calibration. A two-agent,
two-round debate with a judge is a minimum of five model calls where a
single-shot answer is one, and each of those five calls is on the critical
path unless the rounds are pipelined across independent questions, so
end-user latency multiplies by roughly the round count even when spend is
parallelised across agents within a round. The pattern therefore favours
correctness and hallucination reduction over responsiveness and over raw
dollar cost per query, which is why it shows up in offline evaluation
pipelines and high-stakes decision support far more often than in a
live chat turn.

It also trades determinism for robustness. because each agent samples from
an LLM, the same debate re-run twice can reach different conclusions, so a
system built on debate needs its own idempotency and caching discipline
around the debate transcript if the caller expects a stable answer for a
given input. Coupling is intentionally loose between the debating agents,
who see only the current transcript and never share internal state, which
keeps the system easy to reason about and easy to add a third or fourth
debater to, at the cost of every agent re-deriving context the others
already worked out.

Team topology and cognitive load favour debate when the organisation
already has a clean interface for calling one model multiple times with
different system prompts, because the pattern needs no new infrastructure
beyond an orchestrator and a transcript store. It disfavours debate when the
team has no budget to build the failure handling a multi-call pipeline
needs, because an agent debate has more moving parts to monitor than a
single call, and a stuck or looping debate is a harder incident to diagnose
than a single slow request.

## 4. Applicability and non-applicability

Reach for agent debate when the task is a factual claim, a multi-step
reasoning chain, or a comparative quality judgment with no cheap automated
checker, when the cost of an undetected wrong answer materially exceeds the
cost of several extra model calls, when a single LLM-as-judge call has
already been observed to carry a bias the team wants to counter
structurally, for example position bias where the judge favours whichever
answer appears first, or when the goal is specifically to surface a
model's own reasoning error before it reaches a person, which is the
scalable-oversight motivation behind the original Irving, Christiano, and
Amodei framing (arXiv 1805.00899, verified 2026-08-02).

Do NOT reach for agent debate in the following situations, and the reason
matters more than the list.

- **The task has a deterministic checker.** A unit test, a type checker, a
  compiler, a schema validator, or a numeric assertion settles the question
  for free. Debate spends five calls to approximate what one deterministic
  check answers exactly. Use the checker and reserve debate for the
  remainder the checker cannot cover.
- **The task is latency-sensitive and user-facing in real time.** A chat
  turn, an autocomplete suggestion, or a search-result ranking cannot
  absorb the multi-round, multi-call latency debate requires without the
  person perceiving a stall. Use a single well-prompted call or an
  Evaluator-Optimizer loop bounded to one revision instead.
- **The debating agents are not meaningfully independent.** Two calls to
  the same model with the same system prompt and the same context tend to
  agree with each other for the same reason a single model rubber-stamps
  its own first draft, because they share the same prior. Liang et al.
  name this risk directly and address it by assigning explicitly opposed
  stances rather than symmetric prompts (arXiv 2305.19118, verified
  2026-08-02). Debate without engineered disagreement, whether from
  opposing personas, different underlying models, or different retrieved
  evidence, degenerates into expensive self-consistency sampling.
- **The disagreement has no resolution criterion.** If the judge, whether a
  human, a rubric, or a third model, has no principled way to prefer one
  side's argument over the other, the debate produces a transcript but not
  a decision, and the extra calls buy nothing over a coin flip.
- **The system cannot tolerate non-termination.** Debate rounds can
  oscillate, with each agent restating its position rather than converging,
  and a system with no round cap or timeout can spend unbounded cost
  without ever reaching an answer. This is a design defect covered in
  dimension 11, but it means the pattern is inapplicable as-is to any
  environment where an unbounded retry budget is not acceptable.
- **Regulatory or compliance auditability requires a single named
  reasoning chain.** A debate transcript with two adversarial voices and a
  judge is harder to present as "the model's reasoning" in an audit than
  one chain-of-thought trace, because a reviewer must additionally justify
  why the judge's synthesis, rather than either debater's raw position, is
  the system of record.

## 5. Structure

- **Debater agents.** Two or more independent LLM instances, each holding
  its own system prompt, its own stance or persona where the variant calls
  for one, and its own copy of the running transcript. A debater's
  responsibility is narrow. produce an answer and a supporting argument
  given the question and, from the second round onward, the prior round's
  transcript from every other debater.
- **Transcript.** The shared, append-only record of every debater's
  statement in every round. It is the only channel debaters use to see each
  other's positions. no debater reads another debater's hidden state.
- **Round controller.** The orchestration logic that decides how many
  rounds run, what each debater receives as input for the next round, and
  when the debate terminates, whether by a fixed round count, an early-stop
  rule when debaters converge, or a timeout.
- **Judge.** A separate LLM call, a human, or a deterministic rule that
  reads the full transcript after the final round and produces the single
  output the caller receives. In some variants the judge participates every
  round rather than only at the end. Irving, Christiano, and Amodei's
  original formulation puts a human in this role by design, because the
  whole point is to let a judge who cannot solve the underlying problem
  directly still adjudicate a bounded exchange about it (arXiv 1805.00899,
  verified 2026-08-02). Du et al.'s formulation instead aggregates by
  majority vote or a synthesising model call rather than a distinct
  adversarial judge (arXiv 2305.14325, verified 2026-08-02).
- **Caller.** The upstream code or person that submits the question and
  consumes the judge's final output plus, optionally, the full transcript
  for audit.

## 6. ASCII structure diagram

```
                         +----------------+
                         |     Caller     |
                         +----------------+
                                 |
                                 v  question
                      +-----------------------+
                      |   Round Controller     |
                      | (round count, timeout, |
                      |  convergence check)    |
                      +-----------------------+
                        |          |          |
              round N   v          v          v
                 +-----------+ +-----------+ +-----------+
                 | Debater A | | Debater B | | Debater C |
                 | (stance/  | | (stance/  | | (stance/  |
                 |  persona) | |  persona) | |  persona) |
                 +-----------+ +-----------+ +-----------+
                        |          |          |
                        v          v          v
                 +---------------------------------+
                 |          Transcript              |
                 |  (append only, every debater     |
                 |   reads it before next round)    |
                 +---------------------------------+
                                 |
                    after final round or convergence
                                 v
                         +----------------+
                         |     Judge      |
                         | (LLM, rule, or |
                         |  human)        |
                         +----------------+
                                 |
                                 v  final answer + transcript
                         +----------------+
                         |     Caller     |
                         +----------------+
```

## 7. Dynamics

```
Round 0
  Controller sends question to A, B, C independently, no transcript yet.
  A -> answer_A_0 (with reasoning)
  B -> answer_B_0 (with reasoning)
  C -> answer_C_0 (with reasoning)
  Controller appends round-0 statements to transcript.

Round 1..N-1
  For each debater X:
    Controller sends the question and the current transcript to X.
    X reads what every OTHER debater argued last round.
    X produces answer_X_k, which may revise, may hold position, and
      must respond to the strongest opposing point per the variant's
      prompt contract.
  Controller appends round-k statements to transcript.
  Controller checks the stop condition.
    fixed round count reached, or
    all debaters' answers match this round (convergence), or
    timeout exceeded.

Final round N
  Judge receives the full transcript.
  Judge produces the final answer plus a confidence or rationale.
  Controller returns the final answer and transcript to the caller.

Failure branch (any round)
  If a debater call errors or times out, the controller marks that
    debater absent for the round, proceeds with the remaining
    debaters, and logs the gap into the transcript so the judge can
    discount it.
  If no debaters remain, the controller aborts and returns an error
    to the caller. it never fabricates a debater response.
```

## 8. Implementation variants

The two-round, two-debater, separate-judge shape from Du et al. is the
baseline most implementations start from, where each of two or more agents
answers independently in round zero, then in each subsequent round every
agent receives the other agents' prior-round answers and reasoning and is
asked to update or defend its position, and after a fixed number of rounds
either a majority vote or a separate synthesising LLM call produces the
final answer (arXiv 2305.14325, verified 2026-08-02).

The adversarial-stance variant from Liang et al. fixes the
same-prior-agreement problem by assigning explicitly opposed roles rather
than symmetric prompts, one agent instructed to argue the affirmative case
and one the negative case regardless of what either genuinely believes the
answer to be, with a third judge agent reading both arguments and
adjudicating, which the authors report reduces premature convergence
compared to symmetric self-reflection (arXiv 2305.19118, verified
2026-08-02).

The persona-panel variant from ChatEval assigns each debater a distinct
evaluation persona, for example a strict critic persona and a lay-reader
persona, so that the debate's value comes from covering different
evaluation criteria rather than from opposing a single claim, which the
authors describe as roles that "autonomously debate the nuances and
disparities, drawing upon their assigned personas" (Chan et al. 2023,
arXiv 2308.07201, verified 2026-08-02).

A model-diversity variant, common in production deployments where cost
allows it, replaces "same model, different prompt" with genuinely different
underlying models, for example one debater backed by a large frontier model
and another by a different vendor's model, on the reasoning that models
trained on different data and objectives are less likely to share the same
blind spot than two calls to the identical checkpoint. This addresses the
same-prior weakness named in dimension 4 more directly than prompt-level
persona assignment alone, at higher operational cost from managing two
provider integrations instead of one.

A bounded-cost variant caps the round count at one or two rather than
running to convergence, trading some of the accuracy gain for a fixed,
predictable latency and cost budget, which is the shape most viable for
anything closer to interactive use than a fully offline batch job.

Language-idiomatic notes. in every language observed, the pattern is
implemented as plain orchestration code around ordinary LLM client calls.
there is no language feature, such as a coroutine primitive or an actor
model, that changes the shape of the pattern itself, though async and
await constructs in TypeScript, goroutines and channels in Go, and asyncio
tasks in Python are the natural way to run same-round debater calls
concurrently rather than sequentially.

## 9. Known production uses

- **AI Safety via Debate, OpenAI.** The originating protocol, empirically
  validated on an MNIST sparse-pixel classification task where a human
  judge's accuracy rose from 59.4 percent with a single untrusted agent to
  88.9 percent when two agents debated over six revealed pixels. Geoffrey
  Irving, Paul Christiano, Dario Amodei, "AI Safety via Debate," May 2018,
  arXiv 1805.00899 (https://arxiv.org/abs/1805.00899, verified 2026-08-02).
- **Multiagent Debate for factuality and reasoning, Du et al.** The
  reference inference-time implementation, evaluating the debate protocol
  across arithmetic reasoning, the game of 24, biography generation for
  factual accuracy, and chess-move prediction, using off-the-shelf language
  models with no fine-tuning. Yilun Du, Shuang Li, Antonio Torralba,
  Joshua B. Tenenbaum, Igor Mordatch, "Improving Factuality and Reasoning
  in Language Models through Multiagent Debate," May 2023,
  arXiv 2305.14325 (https://arxiv.org/abs/2305.14325, verified 2026-08-02).
- **ChatEval, THUNLP.** A maintained open-source evaluator that uses
  persona-based multi-agent debate to score generated text on open-ended
  questions, adopted as a reference LLM-as-judge evaluator by researchers
  building evaluation pipelines for their own generation systems. Chi-Min
  Chan et al., "ChatEval, Towards Better LLM-based Evaluators through
  Multi-Agent Debate," August 2023, arXiv 2308.07201, code at
  github.com/chanchimin/ChatEval, maintained by Tsinghua University NLP
  lab, THUNLP (verified 2026-08-02).
- **MAD, Multi-Agent Debate, Tencent AI Lab and collaborators.** A
  reference implementation assigning affirmative and negative debating
  roles with a moderating judge, targeted specifically at correcting the
  Degeneration-of-Thought failure of single-agent self-reflection on
  Common MT and counter-intuitive arithmetic reasoning benchmarks. Tian
  Liang et al., "Encouraging Divergent Thinking in Large Language Models
  through Multi-Agent Debate," May 2023, arXiv 2305.19118, code at
  github.com/Skytliang/Multi-Agents-Debate (verified 2026-08-02).

## 10. Consequences

Positive.

- Measured reduction in factual hallucination and improved multi-step
  reasoning accuracy compared to single-shot generation from the same
  underlying model, as reported across arithmetic, game-of-24, and
  biography-generation benchmarks (Du et al. 2023, arXiv 2305.14325,
  verified 2026-08-02).
- Structurally counters the self-reflection failure where a model
  correcting its own output stays anchored to its first answer, because an
  opposing agent's argument is an external input the debater must actually
  respond to rather than a self-generated critique it can dismiss (Liang
  et al. 2023, arXiv 2305.19118, verified 2026-08-02).
- Produces an auditable transcript, not just a final answer, which is
  useful evidence when a person needs to understand why a system reached a
  conclusion, beyond what a single chain-of-thought trace shows.
- Composable with existing evaluation and generation pipelines as a
  drop-in step, because every debater and the judge are ordinary LLM calls
  with no special infrastructure requirement beyond an orchestrator.

Negative.

- Multiplies cost and latency by roughly the number of debaters times the
  number of rounds plus one judge call, which the original safety-via-debate
  framing accepts deliberately in exchange for enabling a judge who could
  not otherwise verify the answer directly, but which is a real and
  sometimes prohibitive tax in a cost-sensitive production system.
- Two debaters drawn from the same model with only prompt-level variation
  can converge to agreement for the wrong reason, sharing the same blind
  spot rather than independently confirming a correct answer, unless the
  variant deliberately engineers disagreement through opposed stances or
  different underlying models (dimension 4 and dimension 8).
- Non-deterministic by construction, since every debater and the judge
  sample from an LLM, so the same input can legitimately produce different
  transcripts and different final answers on separate runs, which
  complicates caching, regression testing, and any downstream expectation
  of stability.
- Adds an operational surface with more failure points than a single call,
  including stalled or looping debates, a debater agent producing an
  off-format response the controller cannot parse, and a judge that is
  itself wrong, none of which a single-call system needs to handle.

## 11. Failure modes and misuse

- **Symptom.** The two debaters' answers are near-identical every round and
  the transcript shows no genuine engagement with the opposing argument,
  the debate agrees with itself. **Cause.** Both debaters are the same
  model with the same or near-identical system prompt, so they share the
  same prior and reach the same conclusion independently rather than
  through debate. **Fix.** Assign explicitly opposed stances or personas
  as in the MAD and ChatEval variants, or use genuinely different
  underlying models for the debaters, per dimension 8.

- **Symptom.** Rounds continue without the final answer ever stabilising,
  and the system either times out with no answer or runs to a budget cap
  with the last round's disagreement unresolved. **Cause.** No convergence
  criterion or round cap was set, or the judge step was omitted entirely
  and the controller expects the debaters themselves to agree, which they
  are not guaranteed to do. **Fix.** Always terminate on a fixed round
  count or an explicit timeout regardless of convergence, and always route
  through a distinct judge or aggregation step rather than requiring
  debater consensus as the termination condition.

- **Symptom.** The judge's final answer consistently favours whichever
  debater's argument appears first or last in the transcript, independent
  of argument quality, when the same debate content is fed to the judge
  with the debater order swapped. **Cause.** Position bias in the judge
  model, a documented weakness of LLM-as-judge evaluation generally.
  **Fix.** Run the judge twice with debater order swapped and require
  agreement, or randomise and log the presentation order so the bias is at
  least measurable, or use a rubric-constrained judge prompt that scores
  arguments independently before comparing them.

- **Symptom.** The debate produces a confident, well-argued, and wrong
  final answer, more confident than the single-shot baseline was on the
  same question. **Cause.** Debate improves calibration and correctness on
  average across many questions, but on any individual question it can
  produce false confidence when both debaters and the judge share a
  systematic error, for example a widely-held but wrong fact absorbed by
  every model from similar training data. Debate corrects for a single
  model's noise, not for shared bias across models trained similarly.
  **Fix.** Do not treat debate as a certainty upgrade on a per-question
  basis. use it to raise average accuracy across a population of
  questions, and pair it with retrieval grounding or a deterministic
  checker wherever one is available, rather than trusting debate alone on
  a single high-stakes claim.

- **Symptom.** Cost balloons unpredictably in production, with some
  requests costing five times the expected budget. **Cause.** The round
  controller was implemented with an unbounded or very high round cap,
  intended as a safety margin, and a subset of real questions consistently
  hit that cap because the debate genuinely does not converge on them.
  **Fix.** Set the round cap low, typically one or two rounds, based on
  measured marginal accuracy gain per additional round on a held-out
  sample, not on an arbitrary safety margin, and monitor the fraction of
  requests that hit the cap as an operational signal per dimension 16.

## 12. Trade-off matrix

| Force | Agent Debate | Self-Consistency (majority vote over N samples) | Evaluator-Optimizer (single generator, single fixed critic) | Multi-Agent Supervisor (one agent delegates to specialised workers) |
|---|---|---|---|---|
| Latency | Highest, multiple sequential rounds each needing every agent's call | Medium, N samples can run fully in parallel with no round dependency | Medium, typically one to a few sequential revise passes | Medium to high, depends on supervisor's fan-out depth, but no adversarial rounds |
| Cost | Highest, agents times rounds plus a judge call | Proportional to N, no separate judge call needed | Two calls per revision cycle, generator plus critic | Proportional to number of delegated subtasks |
| Hallucination reduction | Strong when debaters are genuinely independent, weak otherwise | Reduces variance-driven errors, not shared systematic bias | Reduces errors the fixed critic is prompted to catch, blind to what it is not asked about | Not primarily a correctness mechanism, reduces scope error by routing |
| Determinism | Lowest, transcript and outcome both vary run to run | Low, but aggregation by majority is somewhat stabilising | Low, but bounded by a fixed number of revision passes | Depends on the supervisor's routing logic, can be made largely deterministic |
| Suited to real-time interactive use | Rarely, latency too high for most chat-turn budgets | Sometimes, if N is small and samples run in parallel | Often, one bounded revision pass is tolerable | Often, this is its typical deployment context |
| Requires an explicit resolution step | Yes, a judge or aggregation rule is mandatory | Yes, majority vote or another aggregator | Not always, the critic's approval can itself be the resolution | Yes, the supervisor's final synthesis |
| Best suited to | Contested factual or reasoning questions with no cheap checker | Questions where independent resampling reduces noise | Tasks with a clear, statable evaluation rubric | Tasks that decompose cleanly into independent subtasks |

## 13. Related and incompatible patterns

Agent debate composes with Evaluator-Optimizer by using the debate's judge
step as the evaluator half of that pattern, feeding the judge's verdict back
as revision guidance to one or more debaters for another round, rather than
treating the judge's output as terminal. It composes with Multi-Agent
Supervisor when a supervisor agent is the one that decides a subtask is
contested enough to warrant spawning a debate among its worker agents
rather than delegating the subtask to a single worker, making debate one of
several strategies a supervisor can select. It composes with
Self-Consistency at the aggregation step, where instead of a single LLM
judge, the transcript's per-agent final answers are combined by majority
vote, which is exactly the aggregation Du et al. use in their baseline
configuration (arXiv 2305.14325, verified 2026-08-02).

It is a natural alternative to, and should not be run alongside, plain
Reflexion-style single-agent self-critique on the same question, because
running both simultaneously spends the reflection budget without addressing
the shared-prior weakness that motivated moving to debate in the first
place, per dimension 11's first failure mode. It is incompatible in
intent, though not in mechanism, with Chain of Responsibility. debate
requires every agent to see the full transcript and respond to opposing
arguments, whereas Chain of Responsibility deliberately isolates each
handler from the others, so an implementation that tries to be both at once
either collapses debate down to sequential independent opinions with no
real engagement, or breaks the handler isolation Chain of Responsibility
exists to provide.

## 14. Refactoring path in and out

Introducing debate into an existing single-call or Evaluator-Optimizer
system starts by identifying the specific failure the team has actually
observed, not by wrapping every call in debate speculatively. Instrument
the current system to log cases where a human later corrected the model's
output, and check whether those cases cluster around contested factual
claims or multi-step reasoning rather than around tasks with a
deterministic checker, per dimension 4's non-applicability list. If they
do cluster there, introduce a second debater agent using the exact same
prompt and context the first agent already receives, run both independently
for round zero, and measure whether their answers disagree often enough to
be worth resolving, before building the multi-round exchange at all. only
after confirming genuine, frequent disagreement does adding a second and
third round, and a dedicated judge, earn its cost. Cap the round count low
from the start and raise it only if measurement on held-out data shows a
later round changes the final answer often enough to matter, per the last
failure mode in dimension 11.

Removing debate, when it stops earning its place, most often because the
task gained a deterministic checker or because measured accuracy gain per
extra round dropped below the cost it adds, is a matter of first checking
whether a single round with no rebuttal, effectively a one-shot ensemble
plus majority vote, retains most of the accuracy gain at a fraction of the
cost, and stepping down to that Self-Consistency shape before removing
multi-agent structure entirely. If accuracy holds with a single call once a
deterministic checker exists, remove the remaining debater and judge calls
and route the checker's output directly to the caller.

## 15. Testing and verification

Debate is genuinely harder to test than a single-call system because the
correctness of an individual run is not deterministic and the interesting
failure modes, such as premature convergence or position bias, only appear
across a population of runs, not on any single input. The practical
approach is to build a held-out evaluation set with known-correct answers,
run the full debate pipeline against it repeatedly, and track accuracy,
round-to-convergence, and cost as distributions rather than as a single
pass or fail number for any individual test case.

What becomes easier to test as a direct result of the pattern's structure
is the judge step in isolation, because it is a pure function from a fixed
transcript to a verdict and can be unit tested with hand-written fixture
transcripts, including adversarial fixtures that deliberately swap the
order of the two debaters' arguments to check for position bias per
dimension 11. The round controller's termination logic, its round cap,
timeout, and convergence check, is similarly a pure function over
transcript state and is straightforward to unit test with synthetic
transcripts that simulate agreement, disagreement, and a debater erroring
out mid-round.

What becomes harder is asserting anything about an individual debater's
output, since it is an LLM call producing free text conditioned on a
transcript that itself came from other LLM calls, so integration tests
should assert on aggregate properties across many runs, for example
disagreement rate between debaters is at least some threshold on a fixed
benchmark, or judge accuracy on the held-out set is at least some
threshold, rather than asserting a specific transcript for a specific
input. Mocking the debater LLM calls with fixed canned responses is the
correct technique for testing the round controller and judge in isolation
without incurring real inference cost or nondeterminism, reserving
live-model runs for the periodic accuracy-tracking evaluation described
above.

## 16. Observability signals

Log every round's full transcript, including which debater produced which
statement and the wall-clock latency of that specific call, so a slow or
stuck debate can be diagnosed after the fact rather than only observed as a
timeout. Track the disagreement rate between debaters at round zero as a
leading health signal, because a system where debaters agree on nearly
every question is not benefiting from debate and is only paying its cost,
which is the first thing to check when accuracy gains from the pattern seem
smaller than expected. Track the fraction of debates that hit the round cap
without converging, since a rising trend there signals either that the cap
is set too low for the current question mix or that the underlying task has
drifted toward genuinely harder, less resolvable questions. Track judge
verdict agreement when the same transcript is presented with debater order
swapped, as a direct, ongoing measurement of position bias rather than a
one-time test. A healthy dashboard shows disagreement rate meaningfully
above zero, round-cap-hit rate low and stable, and order-swap agreement
close to one hundred percent. a failing instance shows disagreement rate
near zero, indicating wasted cost, or order-swap agreement dropping,
indicating the judge cannot be trusted.

## 17. Security and privacy implications

Every debater agent and the judge receive the full transcript, so any
sensitive data present in the original question or in an earlier debater's
reasoning propagates to every subsequent call and to whichever model
providers back those calls, which multiplies the number of parties that see
the data compared to a single-call system, and matters directly when
debaters are deliberately drawn from different vendors' models as described
in dimension 8's model-diversity variant, since that variant sends the same
sensitive content to multiple external providers rather than one. A debate
transcript is also a larger and more detailed record than a single
response, so if transcripts are logged for audit per dimension 16, the
retention and access-control policy for those logs needs to account for
transcripts containing the same sensitive content the original question
did, repeated across every round.

The pattern is silent on prompt injection risk beyond what any LLM call
already carries. it neither worsens nor mitigates it directly, though a
debate transcript containing content quoted from an earlier round does give
an adversarial input embedded in one debater's early statement a second
chance to influence a later round's other debaters, which a single-call
system's prompt-injection defenses would need to be re-checked against in a
multi-round context rather than assumed to still hold.

## 18. References

1. Geoffrey Irving, Paul Christiano, Dario Amodei, "AI Safety via Debate,"
   OpenAI, May 2018, arXiv 1805.00899.
   https://arxiv.org/abs/1805.00899, verified 2026-08-02.
2. Yilun Du, Shuang Li, Antonio Torralba, Joshua B. Tenenbaum, Igor
   Mordatch, "Improving Factuality and Reasoning in Language Models
   through Multiagent Debate," May 2023, arXiv 2305.14325.
   https://arxiv.org/abs/2305.14325, verified 2026-08-02.
3. Tian Liang, Zhiwei He, Wenxiang Jiao, Xing Wang, Yan Wang, Rui Wang,
   Yujiu Yang, Zhaopeng Tu, Shuming Shi, "Encouraging Divergent Thinking
   in Large Language Models through Multi-Agent Debate," May 2023,
   arXiv 2305.19118. https://arxiv.org/abs/2305.19118, verified
   2026-08-02. Code, https://github.com/Skytliang/Multi-Agents-Debate,
   verified 2026-08-02.
4. Chi-Min Chan, Weize Chen, Yusheng Su, Jianxuan Yu, Wei Xue, Shanghang
   Zhang, Jie Fu, Zhiyuan Liu, "ChatEval, Towards Better LLM-based
   Evaluators through Multi-Agent Debate," August 2023, arXiv 2308.07201.
   https://arxiv.org/abs/2308.07201, verified 2026-08-02. Code,
   https://github.com/chanchimin/ChatEval, verified 2026-08-02.

## Code examples

The debate loop is orchestration around ordinary LLM client calls, so the
samples below model the round controller, transcript, and judge logic with
a stub debater function a real LLM SDK call would implement, rather than
depending on a live network call, which keeps the samples runnable and
their behaviour deterministic for verification. Each language's sample
prints a resolved verdict from a scripted two-round, two-debater debate.

### Python

```python
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Statement:
    debater: str
    round_no: int
    text: str


@dataclass
class Transcript:
    statements: list[Statement] = field(default_factory=list)

    def for_round(self, round_no: int) -> list[Statement]:
        return [s for s in self.statements if s.round_no == round_no]

    def append(self, statement: Statement) -> None:
        self.statements.append(statement)


DebaterFn = Callable[[str, Transcript, int], str]


def run_debate(
    question: str,
    debaters: dict[str, DebaterFn],
    judge: Callable[[str, Transcript], str],
    max_rounds: int = 2,
) -> tuple[str, Transcript]:
    transcript = Transcript()
    for round_no in range(max_rounds):
        round_answers: dict[str, str] = {}
        for name, debate_fn in debaters.items():
            answer = debate_fn(question, transcript, round_no)
            round_answers[name] = answer
        for name, answer in round_answers.items():
            transcript.append(Statement(name, round_no, answer))
        if round_no > 0:
            prev = transcript.for_round(round_no - 1)
            curr = transcript.for_round(round_no)
            if {s.text for s in prev} == {s.text for s in curr}:
                break
    verdict = judge(question, transcript)
    return verdict, transcript


def make_affirmative(claim: str) -> DebaterFn:
    def debate_fn(question: str, transcript: Transcript, round_no: int) -> str:
        if round_no == 0:
            return f"I argue {claim}"
        opposing = [
            s.text for s in transcript.for_round(round_no - 1)
            if claim not in s.text
        ]
        if opposing:
            return f"Holding position, {claim}, unconvinced by {opposing[0]}"
        return f"I argue {claim}"
    return debate_fn


def make_negative(counter_claim: str) -> DebaterFn:
    def debate_fn(question: str, transcript: Transcript, round_no: int) -> str:
        if round_no == 0:
            return f"I argue {counter_claim}"
        return f"Holding position, {counter_claim}"
    return debate_fn


def simple_judge(question: str, transcript: Transcript) -> str:
    last_round = max(s.round_no for s in transcript.statements)
    final_statements = transcript.for_round(last_round)
    return f"Verdict after {last_round + 1} rounds. {final_statements[0].text}"


if __name__ == "__main__":
    debaters = {
        "affirmative": make_affirmative("Paris is the capital of France"),
        "negative": make_negative("Lyon is the capital of France"),
    }
    verdict, transcript = run_debate(
        "What is the capital of France?", debaters, simple_judge, max_rounds=2
    )
    print(verdict)
    print(f"transcript length. {len(transcript.statements)}")
```

### TypeScript

```typescript
interface Statement {
  debater: string;
  roundNo: number;
  text: string;
}

class Transcript {
  private statements: Statement[] = [];

  append(statement: Statement): void {
    this.statements.push(statement);
  }

  forRound(roundNo: number): Statement[] {
    return this.statements.filter((s) => s.roundNo === roundNo);
  }

  all(): Statement[] {
    return this.statements;
  }
}

type DebaterFn = (question: string, transcript: Transcript, roundNo: number) => string;
type JudgeFn = (question: string, transcript: Transcript) => string;

function runDebate(
  question: string,
  debaters: Record<string, DebaterFn>,
  judge: JudgeFn,
  maxRounds: number = 2
): { verdict: string; transcript: Transcript } {
  const transcript = new Transcript();
  for (let roundNo = 0; roundNo < maxRounds; roundNo++) {
    const roundAnswers: Record<string, string> = {};
    for (const [name, debateFn] of Object.entries(debaters)) {
      roundAnswers[name] = debateFn(question, transcript, roundNo);
    }
    for (const [name, answer] of Object.entries(roundAnswers)) {
      transcript.append({ debater: name, roundNo, text: answer });
    }
    if (roundNo > 0) {
      const prevTexts = new Set(transcript.forRound(roundNo - 1).map((s) => s.text));
      const currTexts = new Set(transcript.forRound(roundNo).map((s) => s.text));
      const sameSize = prevTexts.size === currTexts.size;
      const sameMembers = [...prevTexts].every((t) => currTexts.has(t));
      if (sameSize && sameMembers) break;
    }
  }
  const verdict = judge(question, transcript);
  return { verdict, transcript };
}

function makeAffirmative(claim: string): DebaterFn {
  return (_question, transcript, roundNo) => {
    if (roundNo === 0) return `I argue ${claim}`;
    const opposing = transcript
      .forRound(roundNo - 1)
      .map((s) => s.text)
      .filter((t) => !t.includes(claim));
    if (opposing.length > 0) {
      return `Holding position, ${claim}, unconvinced by ${opposing[0]}`;
    }
    return `I argue ${claim}`;
  };
}

function makeNegative(counterClaim: string): DebaterFn {
  return (_question, _transcript, roundNo) => {
    if (roundNo === 0) return `I argue ${counterClaim}`;
    return `Holding position, ${counterClaim}`;
  };
}

function simpleJudge(_question: string, transcript: Transcript): string {
  const allStatements = transcript.all();
  const lastRound = Math.max(...allStatements.map((s) => s.roundNo));
  const finalStatements = transcript.forRound(lastRound);
  return `Verdict after ${lastRound + 1} rounds. ${finalStatements[0].text}`;
}

const debaters: Record<string, DebaterFn> = {
  affirmative: makeAffirmative("Paris is the capital of France"),
  negative: makeNegative("Lyon is the capital of France"),
};

const { verdict, transcript } = runDebate(
  "What is the capital of France?",
  debaters,
  simpleJudge,
  2
);

console.log(verdict);
console.log(`transcript length. ${transcript.all().length}`);
```

### Go

```go
package main

import "fmt"

type Statement struct {
	Debater string
	RoundNo int
	Text    string
}

type Transcript struct {
	Statements []Statement
}

func (t *Transcript) Append(s Statement) {
	t.Statements = append(t.Statements, s)
}

func (t *Transcript) ForRound(roundNo int) []Statement {
	var out []Statement
	for _, s := range t.Statements {
		if s.RoundNo == roundNo {
			out = append(out, s)
		}
	}
	return out
}

type DebaterFn func(question string, transcript *Transcript, roundNo int) string
type JudgeFn func(question string, transcript *Transcript) string

func runDebate(question string, debaters map[string]DebaterFn, judge JudgeFn, maxRounds int) (string, *Transcript) {
	transcript := &Transcript{}
	for roundNo := 0; roundNo < maxRounds; roundNo++ {
		roundAnswers := map[string]string{}
		for name, debateFn := range debaters {
			roundAnswers[name] = debateFn(question, transcript, roundNo)
		}
		for name, answer := range roundAnswers {
			transcript.Append(Statement{Debater: name, RoundNo: roundNo, Text: answer})
		}
		if roundNo > 0 {
			prev := transcript.ForRound(roundNo - 1)
			curr := transcript.ForRound(roundNo)
			if sameStatementSet(prev, curr) {
				break
			}
		}
	}
	verdict := judge(question, transcript)
	return verdict, transcript
}

func sameStatementSet(a, b []Statement) bool {
	if len(a) != len(b) {
		return false
	}
	seen := map[string]bool{}
	for _, s := range a {
		seen[s.Text] = true
	}
	for _, s := range b {
		if !seen[s.Text] {
			return false
		}
	}
	return true
}

func makeAffirmative(claim string) DebaterFn {
	return func(_ string, transcript *Transcript, roundNo int) string {
		if roundNo == 0 {
			return "I argue " + claim
		}
		for _, s := range transcript.ForRound(roundNo - 1) {
			if s.Text != "I argue "+claim {
				return "Holding position, " + claim + ", unconvinced by " + s.Text
			}
		}
		return "I argue " + claim
	}
}

func makeNegative(counterClaim string) DebaterFn {
	return func(_ string, _ *Transcript, roundNo int) string {
		if roundNo == 0 {
			return "I argue " + counterClaim
		}
		return "Holding position, " + counterClaim
	}
}

func simpleJudge(_ string, transcript *Transcript) string {
	lastRound := 0
	for _, s := range transcript.Statements {
		if s.RoundNo > lastRound {
			lastRound = s.RoundNo
		}
	}
	final := transcript.ForRound(lastRound)
	return fmt.Sprintf("Verdict after %d rounds. %s", lastRound+1, final[0].Text)
}

func main() {
	debaters := map[string]DebaterFn{
		"affirmative": makeAffirmative("Paris is the capital of France"),
		"negative":    makeNegative("Lyon is the capital of France"),
	}
	verdict, transcript := runDebate("What is the capital of France?", debaters, simpleJudge, 2)
	fmt.Println(verdict)
	fmt.Printf("transcript length. %d\n", len(transcript.Statements))
}
```
