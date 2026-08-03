---
name: Evaluator-Optimizer
slug: evaluator-optimizer
family: 17-ai-agentic
category: Workflow
aliases: [Generator-Critic Loop, Generate-Evaluate-Refine, Self-Refine Loop, Actor-Critic Workflow (LLM form), Generate-and-Test Loop]
first_described: "Anthropic, Building Effective Agents, Dec 19 2024"
maturity: established
related: [prompt-chaining, orchestrator-worker, routing, reflexion, self-consistency, tree-of-thoughts, chain-of-responsibility]
incompatible_with: []
verified: 2026-08-02
---

# Evaluator-Optimizer

## 1. Name, aliases, and lineage

The name in current use for this workflow is Evaluator-Optimizer. Anthropic
named and defined it in that exact form in the engineering post "Building
Effective Agents," published December 19, 2024, as one of five workflow
patterns the post catalogs alongside one autonomous agent pattern. The post
states the definition directly. "In the evaluator-optimizer workflow, one
LLM call generates a response while another provides evaluation and feedback
in a loop" (Anthropic, "Building Effective Agents,"
[anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents),
verified 2026-08-02). The post compares the shape directly to how a human
writer works. "This workflow is particularly effective when we have clear
evaluation criteria, and when iterative refinement provides measurable
value," and it names two concrete use cases, literary translation where
nuance is missed on a first pass, and complex search tasks where the
evaluator decides whether another round of searching is warranted (same
source, verified 2026-08-02).

LangGraph, the graph-based agent orchestration library from LangChain,
adopted the identical name and shape as one of its documented workflow
recipes. Its own definition reads. "In evaluator-optimizer workflows, one
LLM call creates a response and the other evaluates that response. If the
evaluator or a human-in-the-loop determines the response needs refinement,
feedback is provided and the response is recreated"
([docs.langchain.com/oss/python/langgraph/workflows-agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents),
verified 2026-08-02). That a second, independently maintained orchestration
library shipped the same name with the same two-role shape within roughly a
year of Anthropic's post is why this entry marks the pattern established
rather than merely emerging, the vocabulary is no longer confined to one
company's blog.

The core mechanism, one model produces a candidate and a second evaluation
step judges and revises it, predates Anthropic's naming. Aman Madaan and
sixteen coauthors described the same loop under a different name a year and
a half earlier in "Self-Refine. Iterative Refinement with Self-Feedback,"
where a single LLM plays generator, critic, and reviser in sequence. The
paper's own framing is explicit about the difference from later work. "The
same LLM provides feedback for its output and uses it to refine itself,
iteratively," using "a single LLM as the generator, refiner, and feedback
provider" (Madaan et al., "Self-Refine. Iterative Refinement with
Self-Feedback,"
[arxiv.org/abs/2303.17651](https://arxiv.org/abs/2303.17651), verified
2026-08-02). Self-Refine is the same control-flow shape as Evaluator-
Optimizer with one structural restriction, generator and evaluator are
always the identical model instance rather than two independently
configurable roles, so this entry treats Self-Refine as the direct academic
predecessor and same-model special case, not a separate pattern.

A closely related but distinct line of work is Reflexion, published two
months before Self-Refine by Noah Shinn, Federico Cassano, Edward Berman,
Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao. "Reflexion agents
verbally reflect on task feedback signals, then maintain their own
reflective text in an episodic memory buffer to induce better
decision-making in subsequent trials" (Shinn et al., "Reflexion. Language
Agents with Verbal Reinforcement Learning,"
[arxiv.org/abs/2303.11366](https://arxiv.org/abs/2303.11366), verified
2026-08-02). Reflexion's evaluator step is grounded in an external
environment signal across a whole episode, not a single conversation turn,
and its distinguishing move is persisting the resulting reflection across
trials as an explicit memory object, which this repository documents in a
sibling entry, [`reflexion`](reflexion.md). Evaluator-Optimizer, as this
entry treats it, is the more general shape, one lineage of candidate and
feedback within a single conversation or a single request, with or without
cross-request memory. Reflexion is one specialized way to build the
optimizer half when the task is a multi-step environment episode rather
than a single generate-and-judge turn.

Two more names are worth recording because they appear in production code
without ever using the word optimizer. The generator side is sometimes
called the Actor, following the actor-critic vocabulary borrowed loosely
from reinforcement learning, and the evaluator side is sometimes called the
Critic or the Judge, the last of these overlapping with the separate
"LLM-as-a-judge" evaluation literature. One caution belongs here plainly.
the word optimizer in this pattern's name does not refer to gradient-based
numerical optimization such as Adam or SGD. No weights are updated inside
the loop described in this entry. The optimization is entirely in-context,
a natural-language critique changing what the next natural-language draft looks like. The
one place weight updates genuinely enter a generate-critique-revise loop is
training time, not inference time, and this entry covers that boundary in
dimension 8.

## 2. Problem and context

A single LLM call is a single roll of the dice against a task that has more
than one way to go wrong. For a large share of real generation tasks that is
enough, the model's first draft already satisfies the brief. For a smaller
but consequential share, a lone pass plateaus below an acceptable quality
bar even though the model, given the actual defect spelled out, could fix
it in a second pass. The recognizable shape in a codebase or a product is a
generation step whose output is manually reviewed by a person before it is
used, a translated paragraph an editor still has to touch, a generated SQL
query an analyst still has to read before running, a piece of generated
code a developer still has to run through the test suite before merging.
Wherever a human is already doing that second pass by hand, an automated
generate-then-judge-then-revise loop is a candidate to remove that manual
step, or at minimum to catch the cases that would otherwise need it before
they reach the person.

The context that makes this pattern the right tool, rather than a more
elaborate prompt, has two parts, and Anthropic states both directly as
preconditions rather than as generic advice. First, there must be a way to
articulate what "better" means for this task, a rubric, a schema, a test
suite, a style guide, something a second pass can check the first pass
against. Second, that articulation must be something an evaluator, human or
model, can act on to produce output that measurably improves, "when we have
clear evaluation criteria, and when iterative refinement provides
measurable value" (Anthropic, "Building Effective Agents," verified
2026-08-02). A task with no way to say what "better" looks like cannot be
put through this loop honestly, the evaluator would only be a second,
equally uninformed guess.

The situation often has a draft-then-polish shape a person would
recognize from their own writing process. A literary translator produces a
first pass, then rereads it against the source text looking specifically
for missed connotation and register, then revises. A developer writes code,
then runs it against tests, reads the failure, and edits the specific line
that failed, rather than rewriting from scratch. A researcher runs a
search, reads what came back, notices a gap, and runs a second, more
targeted search. In each case the second and later passes are cheaper and
more targeted than the first because they are informed by a concrete,
localized signal about what was wrong, not a blind repeat of the same
attempt. Evaluator-Optimizer automates exactly that shape, a directed,
feedback-informed second attempt, in place of either a single unguided
attempt or an unguided repeat of the first attempt.

## 3. Forces

**Latency against quality.** Every rejected candidate adds one full
generator round trip and one full evaluator round trip to the critical
path. A task that would take one model call now takes N, where N is
whatever it takes to reach acceptance or exhaust the budget. For a
synchronous, user-facing turn this is directly felt as added wait time, and
it is the single force most likely to rule the pattern out for a chat
reply, even when the quality upside is genuine.

**Cost against quality.** Cost scales the same way latency does, roughly
linearly in the number of iterations, and both the generator and evaluator
calls consume tokens on every pass. The AlphaCodium result, discussed with
its source in dimension 9, is the sharpest quantified example of this
trade actually paying for itself, moving GPT-4's pass rate on a coding
benchmark from 19 percent to 44 percent at the cost of a multi-stage,
test-driven iterative flow rather than one prompt. Whether that trade is
worth it in a given product depends entirely on what a failed first attempt
costs downstream, a wasted customer-support reply is cheap to redo, a
shipped and later reverted database migration is not.

**Verifiable against subjective criteria.** This is the force that most
strongly predicts whether the loop is trustworthy. When the evaluator's
verdict is objectively checkable, a compiler that either accepts the code
or reports a specific error, a schema validator, a test suite, the
acceptance signal is close to ground truth and a false accept is rare and
usually catchable downstream. When the evaluator's verdict is a subjective
judgment call, tone, persuasiveness, elegance, the evaluator is itself an
LLM call with its own error rate, and there is no external check on
whether that judgment was correct. Zheng et al. document this directly for
LLM judges in general. models used as automated evaluators show "position,
verbosity, and self-enhancement biases, as well as limited reasoning
ability" (Zheng et al., NeurIPS 2023 Datasets and Benchmarks Track study of
LLM judges,
[arxiv.org/abs/2306.05685](https://arxiv.org/abs/2306.05685), verified
2026-08-02). A loop built on a
subjective evaluator inherits that error rate on every accept decision, not
only on the visible rejects.

**Correlated blind spots when generator and evaluator share a model.**
Self-Refine's own framing is that the "same LLM" fills both roles, which is
cheap and simple to wire up, but it means a mistake the model's training
made it systematically unable to see is equally invisible to it in the
evaluator role. This is the same self-enhancement bias Zheng et al. name,
sharpened to its limit when generator and evaluator are literally the same
weights. Using a different model, a different persona, or a deterministic
external checker as the evaluator trades setup complexity for a genuinely
independent second opinion, and dimension 8 covers that variant.

**Goodhart pressure on the rubric.** Once a rubric exists as an explicit
target the generator is steering toward within the conversation, the
generator can satisfy the letter of the rubric without satisfying its
intent, adding the required keyword without making the sentence actually
better, padding a response to clear a minimum length requirement. This is the same
reward-hacking dynamic familiar from reinforcement learning applied to an
in-context feedback loop rather than a trained reward model, and it means
the rubric itself needs periodic review against real outcomes, not only
against whether candidates pass it.

**An explicit halting condition is mandatory, not optional.** Nothing in
the two-role shape itself terminates a loop whose evaluator never accepts.
A budget, either a hard iteration cap, a wall-clock deadline, or a cost
cap, has to be imposed by something outside the generator-evaluator
pair, because neither role has an intrinsic reason to stop asking for one
more revision. Every implementation shown in this entry treats this as a
required parameter, not a default the caller can silently omit.

## 4. Applicability and non-applicability

**Reach for Evaluator-Optimizer when**

- A concrete rubric, schema, test suite, or style guide already exists, or
  can be written down, that states what a passing candidate looks like.
- Feedback demonstrably improves the output. Anthropic frames this as an
  experiment to run before committing to the pattern in production, "the
  LLM can articulate useful feedback ... similar to how a human writer
  might go through multiple drafts" (Anthropic, "Building Effective
  Agents," verified 2026-08-02), and the honest way to know this holds for
  a specific task is to try the loop offline against a sample first.
- The task has a natural draft-then-polish shape, literary or technical
  translation, long-form writing against a style guide, code generation
  paired with a real test suite, structured extraction against a schema, a
  generated database query that must satisfy a correctness or performance
  check.
- The cost of one extra round trip is small relative to the cost of a
  wrong first answer reaching a person or a downstream system, a generated
  report an analyst would otherwise have hand-corrected, a piece of code
  that would otherwise fail review and bounce back for a manual fix.
- An objective or semi-objective verifier already exists in the pipeline, a
  compiler, a linter, a schema validator, a retrieval-grounding check, that
  can serve as the evaluator or gate the LLM evaluator's verdict.

**Do not reach for it when**

- The interaction is on a real-time or tightly latency-budgeted path, live
  chat turns, autocomplete, a voice assistant's spoken turn, where even one
  extra round trip breaks the interaction's felt responsiveness. A single
  well-crafted prompt or a prompt-chaining pipeline with no loop-back edge
  fits the latency budget better.
- No stable rubric exists and the task is genuinely a matter of taste with
  no consensus available even among human reviewers, "make this pitch
  punchier" with no agreed definition of punchier. Two unreliable
  judgments, the generator's draft and the evaluator's opinion of it, do
  not average out to a reliable one, and self-consistency's independent
  sampling and majority vote is a better fit for that uncertainty than a
  serial critique loop.
- The task is a single, unambiguous, deterministic transformation, a
  well-defined format conversion, a lookup, a parse of a fixed grammar. A
  rules engine or one prompt call is cheaper, faster, and exactly as
  correct, and wrapping it in a generate-and-critique loop adds cost with
  nothing to critique.
- Verification itself is more expensive, slower, or more manual than
  generation, and cannot be automated inside the request's lifetime, a
  claim that can only be checked by a multi-day laboratory experiment, for
  instance. Run evaluation as an offline batch process against sampled
  outputs instead of inside a synchronous serving loop.
- The requirement is a hard constraint that must never be violated rather
  than a quality gradient to climb, a safety or compliance rule with zero
  tolerance for exceptions. A probabilistic LLM evaluator has a nonzero
  false-accept rate even when well calibrated, so a hard constraint needs a
  deterministic guardrail or validator in addition to, never instead of,
  an LLM-based evaluator step.

## 5. Structure

- **Generator (Optimizer, Actor, Drafter).** Produces a candidate from a
  task specification. On the first pass it works from the task alone. On
  every later pass it works from the task, the prior candidate, and the
  evaluator's feedback on that candidate, and its job on that pass is
  narrowly to address the stated feedback, not to restart from scratch.
- **Evaluator (Critic, Judge, Grader).** Inspects one candidate against the
  task's rubric or acceptance criteria and returns a verdict. A useful
  evaluator returns three things together, an accept-or-reject decision, a
  score usable for comparing candidates across iterations, and specific,
  concrete feedback naming what is wrong and what to change, not merely
  that something is wrong.
- **Loop Controller.** Owns the parts of the system that neither the
  generator nor the evaluator has any incentive to enforce on its own, the
  halting condition. It tracks the iteration count against a hard maximum,
  optionally a cost or wall-clock budget, and the best candidate seen so
  far by score, and it decides after each verdict whether to stop and
  return or to loop back with the new candidate and feedback.
- **Shared context or state.** The task specification and rubric, plus, on
  each pass, the prior candidate and the evaluator's feedback on it. This
  accumulation across turns within one lineage is what separates this
  pattern from parallel independent sampling, in self-consistency each
  sample is generated with no knowledge of the others, here each candidate
  is generated with explicit knowledge of exactly what was wrong with its
  predecessor.
- **External verifier (optional).** A compiler, a test runner, a JSON
  schema validator, a retrieval-grounding check, or any other deterministic
  checker that can replace or gate the LLM evaluator for any criterion that
  is objectively checkable. This is what separates AlphaCodium and CRITIC,
  covered in dimensions 8 and 9, from a purely subjective LLM-judging-LLM
  loop.

## 6. ASCII structure diagram

```
+----------------------------------------------------------+
|  Task spec + rubric                                       |
|  (what a passing candidate must satisfy)                  |
+----------------------------+-------------------------------+
                             |
                             v
              +---------------------------+
              |      Loop Controller       |
              |  owns: max_iterations,     |
              |  budget, best-so-far       |
              +-------------+---------------+
                   |                     ^
      candidate,   |                     |  verdict
      prior,       v                     |  (accept/reject,
      feedback  +--------------+   candidate  score, feedback)
                |   Generator   |------------->+---------------+
                | (Optimizer /  |               |   Evaluator   |
                |    Actor)     |               | (Critic/Judge)|
                +--------------+               +-------+-------+
                                                        |
                                                optional gate/replace
                                                        v
                                              +-----------------------+
                                              |  External Verifier(s)  |
                                              |  compiler / tests /    |
                                              |  schema / retrieval    |
                                              +-----------------------+
```

## 7. Dynamics

```
task, rubric
     |
     v
[iteration 1] Generator.generate(task, prior=None, feedback=None)
     |
     v
  candidate_1
     |
     v
Evaluator.evaluate(task, candidate_1) --> verdict_1
     |
     +-- accepted -----------------------------> return candidate_1
     |
     +-- rejected, budget remains
              |
              v
     [iteration 2] Generator.generate(task, prior=candidate_1,
                                        feedback=verdict_1.feedback)
              |
              v
        candidate_2
              |
              v
     Evaluator.evaluate(task, candidate_2) --> verdict_2
              |
              +-- accepted --------------------> return candidate_2
              |
              +-- rejected, budget remains -----> iteration 3, ...
              |
              +-- rejected, budget exhausted ---> return best_so_far
```

State transitions for the loop as a whole, independent of iteration count,
read as five states, named here without a colon so the list stays plain
prose. DRAFTING, the generator is producing a candidate. EVALUATING, the
evaluator is judging the latest candidate. ACCEPTED, a candidate satisfied
the rubric and the loop exits successfully. REVISING, a rejection with
budget remaining is feeding the next DRAFTING state. BUDGET_EXHAUSTED, the
maximum iteration count, cost cap, or deadline was reached with no
acceptance, and the loop exits returning the best-scoring candidate seen
along with an explicit unmet-criteria signal for the caller. Every
implementation in this entry keeps ACCEPTED and BUDGET_EXHAUSTED as two
distinct exits in code, because a caller that cannot tell the two
apart will silently treat an unfinished draft as a finished one.

## 8. Implementation variants

**Same-model self-refine.** Generator and evaluator are the identical
model, distinguished only by which system prompt or role instruction is
active for that call. This is the cheapest to stand up, requiring only two
prompts against one model endpoint, and it is exactly the shape Madaan et
al. describe (Self-Refine, verified 2026-08-02). Its structural weakness is
the correlated-blind-spot force from dimension 3, the evaluator cannot
catch a class of error the same weights are prone to make as a generator.

**Heterogeneous-model evaluator.** Generator and evaluator are two
different models, or the same model family run with a materially different
persona and a much lower temperature for the judge role. This directly
addresses the self-enhancement bias Zheng et al. measured, at the cost of
maintaining two prompt surfaces against potentially two different
providers, and it is common in production to pair a cheaper, faster model
as the generator with a stronger, more expensive model reserved for the
judge call, since the judge runs once per candidate while the generator may
run several times.

**Deterministic or tool-based evaluator.** The evaluator step is replaced,
in whole or in part, by a non-probabilistic checker, a compiler, a test
runner, a schema validator, a retrieval-grounding lookup. This is the
variant with the strongest correctness guarantee, because the accept
decision is not itself a judgment call with an error rate, and it is the
shape behind both AlphaCodium and CRITIC, covered with sources in dimension
9. A common hybrid keeps an LLM step only to translate a raw tool failure,
a stack trace, a diff, a validation error, into feedback the generator's
next prompt can act on, while the accept-or-reject decision itself stays
deterministic.

**Structured, multi-dimension scoring.** Rather than a single accept-or-
reject bit, the evaluator returns a small set of named scores, accuracy,
tone, length, grounding, each independently checkable, often produced with
a structured-output schema so the score is a typed value rather than free
text the controller has to parse. LangGraph's own reference implementation
of this pattern defines a `Feedback` schema with structured output
specifically for this purpose (docs.langchain.com/oss/python/langgraph/
workflows-agents, verified 2026-08-02). A candidate can then be accepted
when every dimension clears its own threshold rather than on one blended
score, which makes a rejection's feedback naturally specific, "grounding
failed" rather than "score was 6 out of 10."

**Best-of-N with evaluator selection.** Instead of a serial lineage of one
candidate revised repeatedly, N candidates are generated independently and
in parallel, following the parallelization pattern, and the evaluator's job
changes from accept-or-reject to rank-and-select the strongest of the N.
This trades the added latency of serial iterations for the added cost of N
parallel generations, useful when wall-clock time is scarcer than compute
budget, and it composes cleanly with self-consistency's independent-
sampling structure while still using an evaluator rather than a majority
vote to choose the winner.

**Human-in-the-loop evaluator.** The evaluator role is filled by a person
rather than a model call, and only the generator is automated, regenerating
on the person's stated feedback. LangGraph's own definition names this
explicitly as an alternative to the automated evaluator, "If the evaluator
or a human-in-the-loop determines the response needs refinement" (same
source, verified 2026-08-02). The control flow, generate, judge, loop back
with feedback or stop, is unchanged, only the implementation of the judge
role differs, which is the clearest evidence that this pattern's essential
content is the loop's control flow, not any particular claim about who or
what fills the evaluator seat.

**Training-time self-critique, distinct from the inference-time loop.**
Anthropic's own Constitutional AI method applies the same shape of
generate-critique-revise loop, but as a data-generation step for
fine-tuning rather than as a step inside a live request. "In the supervised
phase we sample from an initial model, then generate self-critiques and
revisions, and then finetune the original model on revised responses" (Bai
et al., "Constitutional AI. Harmlessness from AI Feedback,"
[arxiv.org/abs/2212.08073](https://arxiv.org/abs/2212.08073), verified
2026-08-02). The loop here produces training examples once, offline, rather
than gating any single production response, and this entry keeps it as a
named variant rather than a production use because it does not run inside
a serving path.

## 9. Known production uses

**AlphaCodium.** Tal Ridnik, Dedy Kredo, and Itamar Friedman of CodiumAI
built a "test-based, multi-stage, code-oriented iterative flow" for
competitive-programming code generation, published as "Code Generation with
AlphaCodium. From Prompt Engineering to Flow Engineering"
([arxiv.org/abs/2401.08500](https://arxiv.org/abs/2401.08500), verified
2026-08-02) and released as open source at
[github.com/Codium-ai/AlphaCodium](https://github.com/Codium-ai/AlphaCodium)
(verified 2026-08-02). The result is one of the few quantified,
apples-to-apples measurements of this pattern's payoff. "On the validation
set, for example, GPT-4 accuracy (pass@5) increased from 19% with a single
well-designed direct prompt to 44% with the AlphaCodium flow" (same GitHub
source, verified 2026-08-02), using a deterministic evaluator, the target
programming language's own test runner, in place of a subjective LLM
judge.

**DSPy Assertions.** DSPy, from Omar Khattab, Arnav Singhvi, and coauthors
at Stanford ("DSPy. Compiling Declarative Language Model Calls into
Self-Improving Pipelines,"
[arxiv.org/abs/2310.03714](https://arxiv.org/abs/2310.03714), verified
2026-08-02, GitHub organization `stanfordnlp/dspy`), ships `dspy.Assert` and
`dspy.Suggest` as first-class constructs implementing this exact loop
against programmatic constraints. Its own documentation describes the
mechanism plainly. "An under-the-hood backtracking is initiated, offering
the model a chance to self-refine and proceed," where the module's next
prompt is dynamically extended with the past failed output plus
"user-defined feedback about what went wrong"
([dspy.ai/learn/programming/7-assertions](https://dspy.ai/learn/programming/7-assertions/),
verified 2026-08-02). This is a production use inside a widely adopted open
source framework rather than a bespoke internal pipeline, so its correctness
is exercised by every downstream project that relies on it.

**CRITIC.** Zhibin Gou, Zhihong Shao, and five coauthors published
"CRITIC. Large Language Models Can Self-Correct with Tool-Interactive
Critiquing" at ICLR 2024
([arxiv.org/abs/2305.11738](https://arxiv.org/abs/2305.11738), verified
2026-08-02). CRITIC's evaluator step is deliberately not a second LLM
opinion. "Starting with an initial output, CRITIC interacts with
appropriate tools to evaluate certain aspects of the text, and then revises
the output based on the feedback obtained during this validation process"
(same source, verified 2026-08-02), demonstrated across question answering
with a search tool, code generation against an interpreter, and toxicity
reduction against a classifier, three separate task families using the same
generate-verify-revise control flow with three different external
verifiers.

**Anthropic's own production workloads.** The pattern's naming source
states its own internal use directly rather than only as a hypothetical.
Anthropic names literary translation, where an evaluator catches nuance a
first draft misses, and multi-round research and search, where the
evaluator decides whether an additional search pass is warranted, as the
two concrete workloads the pattern was written up to describe (Anthropic,
"Building Effective Agents," verified 2026-08-02).

## 10. Consequences

**Positive.**

- On tasks with checkable criteria, measured quality gains can be large,
  AlphaCodium's move from 19 percent to 44 percent pass@5 on a coding
  benchmark is a directly cited, reproducible figure rather than an
  informal estimate.
- The loop targets systematic error directly, in a way independent
  parallel sampling does not. Self-consistency's majority vote reduces
  variance across several attempts drawn from the same distribution, but a
  bias every sample shares survives the vote unchanged, whereas a
  well-designed evaluator step is specifically built to name and correct
  exactly that kind of shared defect when it is checkable.
- The rubric or evaluation criteria become an explicit, inspectable,
  versionable artifact rather than an implicit standard that only lived in
  a person's head during manual review, which makes the acceptance bar
  auditable and reviewable on its own, separate from any individual
  generated output.
- Generator and evaluator can be developed, swapped, and improved somewhat
  independently, a stronger judge model can be substituted without
  touching the generator's prompt, and a deterministic verifier can replace
  an LLM judge for any criterion that turns out to be objectively
  checkable, without restructuring the surrounding loop.
- The pattern degrades gracefully to a documented failure state, budget
  exhaustion with a best-so-far candidate and an explicit unmet-criteria
  signal, rather than to a silent wrong answer indistinguishable from a
  right one, provided the Loop Controller is built to surface that state
  rather than swallow it.

**Negative.**

- Cost and latency scale with iteration count, and a task that would need
  one model call under a single-shot prompt now needs at minimum two, and
  in the worst case as many as the iteration budget allows, on every
  request that does not accept on the first pass.
- A same-model or same-family generator and evaluator share blind spots, so
  a category of mistake the model cannot recognize as a generator is
  equally invisible to it as an evaluator, and Zheng et al.'s documented
  self-enhancement bias is the general form of exactly this failure.
- A rubric that becomes an explicit in-context target invites the
  generator to satisfy its letter without satisfying its intent, the same
  reward-hacking dynamic familiar from trained reward models, now playing
  out inside a single conversation's context window instead of across a
  training run.
- An LLM evaluator is fallible in both directions, but a false accept is
  the more expensive failure mode of the two, because it is silent, the
  loop reports success and ships the flawed candidate, whereas a false
  reject only costs one extra, harmless iteration.
- Quality across iterations is not guaranteed to be monotonic. Evaluator
  feedback that is inconsistent from one call to the next, or a generator
  that overcorrects on a piece of feedback, can produce a candidate at
  iteration three that scores worse than the candidate at iteration one, so
  a controller that simply returns whatever the last iteration produced
  can hand back a regression.
- Two coupled prompt surfaces, the generator's and the evaluator's, now
  need to be maintained, versioned, and tested together, roughly doubling
  the prompt-engineering and regression-testing surface area of the
  feature compared to a single-shot prompt.

## 11. Failure modes and misuse

**Symptom.** The loop runs to the maximum iteration count on nearly every
request, and quality visibly plateaus after the first revision regardless
of how many further iterations run.
**Cause.** The evaluator's feedback is generic rather than specific,
"improve this" or "make it better" instead of a concrete, addressable
delta, so the generator has nothing localized to act on and effectively
regenerates a similar draft each time.
**Fix.** Require the evaluator's feedback field to name a specific,
checkable defect, tied to a rubric dimension, a line, or a field, and
reject vague verdicts at the Loop Controller level, treating a
non-specific feedback string as an evaluator bug to log and fix, not as a
valid verdict to act on.

**Symptom.** Cost or latency for a feature climbs after this pattern ships,
with no corresponding improvement visible in the feature's own quality
metrics.
**Cause.** No cheap early-exit path exists for high-confidence passes, or
the acceptance threshold was set stricter than the task's realistically
achievable pass rate, so most requests burn their full iteration budget
without ever reaching acceptance.
**Fix.** Calibrate the acceptance threshold against a held-out labeled
sample before shipping, exactly the offline "does feedback help this task"
experiment Anthropic recommends before committing to the pattern at all,
and log the per-iteration score delta so a plateau after iteration one is
visible in observability rather than discovered by a cost review months
later.

**Symptom.** The loop confidently ships an output that is wrong in a way a
person notices immediately on inspection, a hallucinated fact, a fabricated
citation, a subtly incorrect claim, and the acceptance verdict looked
entirely reasonable.
**Cause.** Generator and evaluator share the same underlying model or
training data, so a fact the model cannot verify as a generator it also
cannot detect as false in the evaluator role, the correlated-blind-spot
force from dimension 3 manifesting directly in production.
**Fix.** Route any objectively checkable claim through a deterministic or
tool-based verifier instead of, or in addition to, the LLM evaluator, a
retrieval-grounding check, a citation lookup, a schema validation, and use
a heterogeneous model or a materially different evaluator persona for the
remaining subjective judgments.

**Symptom.** Output quality gets measurably worse across iterations on some
fraction of requests, the final candidate scores lower than an earlier one
in the same lineage.
**Cause.** The evaluator's judgments are noisy or internally inconsistent
run to run, often from a temperature setting too high for a judging role,
and the generator overcorrects on a piece of feedback that contradicted an
earlier round's feedback.
**Fix.** Track the highest-scoring candidate across the whole trace and
return that one rather than automatically returning the final iteration,
lower the evaluator's sampling temperature toward zero, and periodically
audit the evaluator against a fixed golden set to catch drift in its own
consistency.

**Symptom.** A request hangs, times out, or runs far longer than expected
in production, well past any latency budget the surrounding system assumed.
**Cause.** The halting condition depends only on the evaluator's subjective
accept decision with no independent hard cap, so a task the evaluator never
judges acceptable loops until an unrelated external timeout finally kills
it.
**Fix.** Give the Loop Controller a mandatory hard maximum iteration count
and a wall-clock or cost budget that is independent of the evaluator's
verdict, defense in depth against exactly this failure, matching the
mandatory-parameter design in every code sample in this entry.

**Symptom.** The pass rate on a feature that has run unchanged for months
starts drifting, either accepting candidates it used to reject or rejecting
ones it used to accept, with no code change anyone can point to.
**Cause.** The evaluator prompt or rubric was edited informally over time,
in response to individual complaints, with no version control and no
regression test protecting the earlier behavior the rest of the system was
tuned against.
**Fix.** Version the evaluator's rubric as a first-class artifact and
protect it with a fixed golden set of known-good and known-bad candidates
it must classify correctly before a rubric change ships, the same
discipline dimension 15 applies to testing the evaluator itself.

## 12. Trade-off matrix

| Force | Evaluator-Optimizer | Self-Consistency | Prompt Chaining | Tree of Thoughts |
|---|---|---|---|---|
| Latency per request | Grows with rejected iterations, at least two calls | Fixed, N samples run in parallel | Fixed, one call per chain stage | Grows with search breadth and depth explored |
| Cost per request | Grows with iterations, generator plus evaluator each pass | N times a single call's cost | Sum of the chain's fixed stage count | Can exceed either, branching multiplies calls |
| Needs a checkable rubric | Required for a trustworthy result | Not required, only needs a way to compare or vote on samples | Not required for the chain itself | Needs a state evaluator, similar requirement to this pattern's evaluator |
| Catches a systematic, shared bias | Yes, if the evaluator is independent of the generator's blind spot | No, a shared bias survives the vote unchanged | No, chaining does not add a critique step | Partially, if the state evaluator does not share the same bias |
| Halting complexity | Requires an explicit budget, no natural stopping point | Trivial, stop after N samples | Trivial, stop after the fixed chain length | Requires a search budget and a pruning rule, comparable complexity |
| Best fit | Draft-then-polish tasks with a rubric and value in iteration | Tasks with many independent reasoning paths and a cheap way to pick the best one | A task that decomposes cleanly into fixed, ordered sub-steps | Tasks needing exploration of multiple candidate solution paths with backtracking |

## 13. Related and incompatible patterns

**Prompt Chaining.** Chaining is a linear, fixed-length sequence of LLM
calls where each stage's output feeds the next stage's input, with no
loop-back edge. Evaluator-Optimizer can be described as a chain with
exactly one conditional loop-back edge added between its last two stages,
generator to evaluator, evaluator to generator again on rejection, so a
reader who already understands `prompt-chaining` can treat this pattern as
that same idea plus a bounded retry loop.

**Orchestrator-Worker.** The two patterns compose rather than compete. An
orchestrator can dispatch a subtask to a worker, and before returning that
worker's result upward, run it through an evaluator-optimizer loop to
harden a single worker's output before it is folded back into the
orchestrator's synthesis, giving each individually delegated piece of work
its own quality gate.

**Routing.** A router can send only the requests that genuinely need this
loop's cost, high-stakes or historically error-prone categories, into an
evaluator-optimizer path, while routing simpler, low-risk categories to a
cheaper single-shot generator, keeping the added latency and cost
concentrated where it earns its keep.

**Reflexion.** Reflexion, documented in the sibling entry
[`reflexion`](reflexion.md), is a specialization of this same
generate-judge-revise shape for multi-step environment episodes, where the
evaluator's signal comes from an external environment across a whole
trial rather than a single LLM judging a single response, and where the
resulting lesson is explicitly persisted as episodic memory across trials
rather than only carried forward as the next prompt's context.

**Self-Consistency.** The two patterns are orthogonal in structure rather
than substitutes for one another. Self-consistency samples N independent candidates with no
feedback between them and combines them by majority vote or a similar
aggregation, while Evaluator-Optimizer produces one directed lineage
shaped by explicit feedback at each step. The best-of-N evaluator-selection
variant in dimension 8 is where the two compose directly, generate N
candidates independently, then use an evaluator rather than a vote to pick
or synthesize the winner.

**Tree of Thoughts.** Tree of Thoughts explores multiple branching
candidate solution paths with lookahead and backtracking across a search
tree, whereas Evaluator-Optimizer refines a single lineage serially in
place with no branching. The two combine when a Tree of Thoughts search
uses an evaluator's score, rather than a hand-tuned heuristic, as the value
function that decides which branch of the tree to expand next.

**Chain of Responsibility.** When an evaluator's single verdict is
decomposed into a sequence of independent, specialized checks, a schema
checker, then a safety checker, then a factuality checker, each able to
reject and hand off to the next, that decomposition is a direct application
of the classical [`chain-of-responsibility`](../01-gof/chain-of-responsibility.md)
pattern to the evaluator role specifically, one named GoF pattern
implementing one participant of this one.

No pattern in this repository conflicts with
Evaluator-Optimizer at the structural level, in the sense the `incompatible_with` field is meant to
capture. The practical tension worth naming plainly is that an unbounded or
loosely bounded loop and a hard real-time service-level agreement do not
coexist, which is a deployment constraint on the halting condition
described in dimension 3, not an incompatibility between two named
patterns.

## 14. Refactoring path in and out

**Introducing the pattern.** Start from the single generator prompt already
in production and leave it untouched. Add an evaluator as a pure offline
measurement first, run it in shadow mode against a sample of the
generator's real outputs, logging what verdict it would have given, without
letting that verdict change what is served. This answers the precondition
question from dimension 4 with real data before any user-facing behavior
changes, does feedback from this specific evaluator actually correlate
with quality humans agree on. Once the evaluator's agreement with a human
or ground-truth judgment is measured and acceptable, wire the loop behind a
feature flag with a conservative iteration cap, one or two, and a strict
cost or latency budget, and only widen the iteration cap once production
data shows the extra iterations are earning their cost.

**Retiring the pattern.** When production logs show the evaluator accepting
the generator's very first candidate on close to every request, the loop
has stopped earning its added latency and cost, and the accumulated rubric
knowledge can usually be folded directly into the generator's own prompt as
explicit instructions, collapsing two coupled calls back into one, the same
intuition behind why a human writer's mental checklist eventually becomes
part of how they draft rather than something checked only after the fact.
Separately, once production data has identified which specific failure
modes actually recur, an LLM evaluator step can often be narrowed to a
cheaper deterministic check for those specific, now-understood failure
modes, keeping the LLM evaluator only for the residual cases that remain
genuinely subjective.

## 15. Testing and verification

Generator and evaluator are each unit-testable in isolation as pure
functions of an input given a mocked or injected model client, exactly the
seam the `Drafter`, `Evaluator`, and `Verdict` interfaces in this entry's
code samples expose, a test can substitute a fixed, scripted response for
either role without invoking a real model, and assert the Loop Controller's
behavior, does it stop on acceptance, does it stop at the iteration cap,
does it return the best-scoring candidate rather than the last one,
entirely deterministically.

The evaluator itself needs its own golden-set regression tests, a small,
fixed, labeled set of known-good and known-bad candidates it must classify
correctly, treated with the same seriousness as a classifier's precision
and recall would be, since the evaluator's verdict is what the whole loop's
correctness rests on and it is the component most likely to drift silently
if left untested.

A property worth asserting directly rather than only observing informally
is termination, for any sequence of feedback the evaluator could plausibly
produce, including a fuzzed evaluator that always rejects, the loop must
still terminate within the configured maximum iteration count. This is a
cheap test to write against the Loop Controller alone, independent of
whether the generator or evaluator are real or mocked, and it directly
covers the halting-condition failure mode from dimension 11.

Full transcript snapshot testing, recording the sequence of candidates and
verdicts for a fixed set of inputs and diffing that sequence on future
runs, catches regressions introduced when either the generator's or the
evaluator's prompt is edited, since the two prompts are coupled and a
change to one can silently change how the other behaves across the loop as
a whole, not only in isolation.

For tests that need determinism, pin the evaluator's sampling temperature
near zero, since a stochastic evaluator makes test assertions flaky by
construction, while remembering that the production temperature choice for
the evaluator is itself a parameter worth its own testing, too low a
temperature can make the evaluator rigidly reject valid stylistic variation
it should accept, and this is a case where the test environment's need for
determinism and production's need for calibrated judgment genuinely pull in
different directions.

## 16. Observability signals

- **Iterations-to-accept, as a distribution, not only an average.** A
  rising p95 or p99 while the mean stays flat is often the first visible
  sign of either rubric drift or a harder-than-usual mix of incoming tasks,
  well before it shows up in any aggregate cost or latency number.
- **Per-iteration score trend within a lineage.** Whether the score is
  trending upward on average across iterations, or oscillating, is the
  direct signal for the non-monotonic-quality failure mode from dimension
  11, and it is cheap to compute since the score is already produced on
  every verdict.
- **Rejection reason distribution, tagged by rubric dimension.** Which
  specific rubric dimension fails most often across rejected candidates is
  the single signal most directly pointing at what to fix, it points
  directly at what to fix in the generator's prompt, rather than only
  telling you that something, unspecified, is failing.
- **Cost per accepted output.** Total tokens or dollars spent across
  generator and evaluator calls, summed across every iteration in a
  lineage, divided by whether that lineage ended in acceptance, is the
  number that answers whether the pattern's cost is still justified by its
  outcome.
- **Budget-exhausted rate.** The fraction of requests that hit the maximum
  iteration count without ever reaching acceptance deserves its own alert
  threshold, since a rising rate silently degrades the user-visible outcome,
  a best-effort, never-accepted candidate is shipped instead of a properly
  vetted one, without necessarily showing up as an error anywhere else in
  the system.
- **Evaluator-human agreement, sampled continuously.** Periodically routing
  a small sample of the evaluator's verdicts to a human reviewer and
  measuring agreement is the ongoing calibration check that answers whether
  the automated judge is still trustworthy, the production analogue of the
  golden-set test from dimension 15, run continuously rather than only at
  deploy time.

## 17. Security and privacy implications

Adding an evaluator step doubles the surface area exposed to prompt
injection, not merely shifts it. The evaluator reads model-generated text,
and in the tool-based variant it may also read external tool output, so an
adversarial instruction embedded in a document, a search result, or a
generated candidate that reaches the evaluator's context can attempt to
manipulate the evaluator into an accept decision for content that should
have been rejected, exactly as the same instruction could try to manipulate
the generator directly. Evaluator input needs the same untrusted-input
treatment as generator input, never an implicit trust boundary only because
it is the second call in the pipeline rather than the first.

The evaluator's feedback text and reasoning are a second place sensitive
content from the candidate can leak into logs or downstream systems, a
candidate that happened to echo personal data or a secret does not stop
carrying it only because it was rejected, the rejected candidate and the
evaluator's commentary on it both need the same redaction and retention
rules applied to the final, accepted output.

A weaker or cheaper model used as the evaluator is also a weaker security
and safety backstop, and relying on it as the sole content or safety filter
inherits whatever blind spots that weaker model has. The same defense in
depth argument from dimension 4's non-applicability list applies here for
safety specifically, a dedicated, deterministic filter belongs in addition
to an LLM-based evaluator for any hard safety or compliance constraint, not
as a replacement for one.

If an evaluator doubles as a safety gate and its verdicts, or the specific
reasoning behind them, are exposed back to an untrusted caller, an attacker
who can submit many attempts and observe the evaluator's responses gains an
iterative signal to probe and adapt against, effectively an oracle for
attacking the evaluator itself. Raw evaluator reasoning used for safety
purposes should not be surfaced word for word to an untrusted caller, and the
number of attempts a single untrusted caller can run against the loop is
worth rate-limiting independently of the iteration budget applied for cost
reasons.

In a multi-tenant system, the accumulating candidate-and-feedback history
that this pattern's structure depends on, dimension 5's shared context, is
exactly the kind of state that needs to be strictly scoped per request or
per session. A context object that leaks across tenants, even
accidentally, in this pattern carries not only the final output but also
every intermediate rejected draft and every piece of evaluator feedback
about what was wrong with it, a wider blast radius than a single final
response would be on its own.

## 18. References

1. Anthropic. "Building Effective Agents." Published December 19, 2024.
   [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents),
   verified 2026-08-02.
2. LangChain. "Workflows and agents." LangGraph documentation.
   [docs.langchain.com/oss/python/langgraph/workflows-agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents),
   verified 2026-08-02.
3. Madaan, Aman, Niket Tandon, Prakhar Gupta, and 14 coauthors.
   "Self-Refine. Iterative Refinement with Self-Feedback." arXiv preprint,
   2023. [arxiv.org/abs/2303.17651](https://arxiv.org/abs/2303.17651),
   verified 2026-08-02.
4. Shinn, Noah, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik
   Narasimhan, and Shunyu Yao. "Reflexion. Language Agents with Verbal
   Reinforcement Learning." arXiv preprint, 2023.
   [arxiv.org/abs/2303.11366](https://arxiv.org/abs/2303.11366), verified
   2026-08-02.
5. Ridnik, Tal, Dedy Kredo, and Itamar Friedman. "Code Generation with
   AlphaCodium. From Prompt Engineering to Flow Engineering." arXiv
   preprint, 2024. CodiumAI.
   [arxiv.org/abs/2401.08500](https://arxiv.org/abs/2401.08500), verified
   2026-08-02.
6. Codium-ai. "AlphaCodium" GitHub repository, README.
   [github.com/Codium-ai/AlphaCodium](https://github.com/Codium-ai/AlphaCodium),
   verified 2026-08-02.
7. Khattab, Omar, Arnav Singhvi, Paridhi Maheshwari, and 10 coauthors.
   "DSPy. Compiling Declarative Language Model Calls into Self-Improving
   Pipelines." arXiv preprint, 2023. Stanford NLP.
   [arxiv.org/abs/2310.03714](https://arxiv.org/abs/2310.03714), verified
   2026-08-02.
8. Stanford NLP. "Assertions." DSPy documentation.
   [dspy.ai/learn/programming/7-assertions](https://dspy.ai/learn/programming/7-assertions/),
   verified 2026-08-02.
9. Gou, Zhibin, Zhihong Shao, Yeyun Gong, Yelong Shen, Yujiu Yang, Nan
   Duan, and Weizhu Chen. "CRITIC. Large Language Models Can Self-Correct
   with Tool-Interactive Critiquing." ICLR 2024.
   [arxiv.org/abs/2305.11738](https://arxiv.org/abs/2305.11738), verified
   2026-08-02.
10. Bai, Yuntao, Saurav Kadavath, Sandipan Kundu, and 46 coauthors.
    "Constitutional AI. Harmlessness from AI Feedback." arXiv preprint,
    2022. Anthropic.
    [arxiv.org/abs/2212.08073](https://arxiv.org/abs/2212.08073), verified
    2026-08-02.
11. Zheng, Lianmin, Wei-Lin Chiang, Ying Sheng, and 10 coauthors. Study of
    LLM-as-a-judge evaluation and its known biases. NeurIPS 2023 Datasets
    and Benchmarks Track.
    [arxiv.org/abs/2306.05685](https://arxiv.org/abs/2306.05685), verified
    2026-08-02.

## Code

Every sample implements the same minimal Evaluator-Optimizer loop against a
`Drafter`, the generator, and an `Evaluator` interface, driven by a Loop
Controller that enforces a mandatory iteration budget and always returns
the highest-scoring candidate seen, never merely the last one produced, per
the failure mode covered in dimension 11. The generator and evaluator in
each worked example are deterministic, scripted stand-ins for what a live
model call would do, so every sample compiles and runs offline with no
network access and no API key, while the interface shapes are exactly what
a live model-backed implementation would plug into. All three samples were
run directly against the toolchains listed below.

### Python

Run with `python3 evaluator_optimizer.py`. Executed against CPython 3.13.

```python
"""Evaluator-Optimizer loop: generate a candidate, evaluate it, refine on
rejection, stop on acceptance or when the iteration budget is exhausted.
Returns the highest-scoring candidate seen, not merely the last one produced."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Verdict:
    accepted: bool
    score: float
    feedback: str


class Generator(Protocol):
    def generate(self, brief: str, prior: str | None, feedback: str | None) -> str:
        ...


class Evaluator(Protocol):
    def evaluate(self, brief: str, candidate: str) -> Verdict:
        ...


@dataclass
class Attempt:
    candidate: str
    verdict: Verdict


@dataclass
class LoopResult:
    best: Attempt
    accepted: bool
    iterations: int
    trace: list[Attempt] = field(default_factory=list)


def refine(
    brief: str,
    generator: Generator,
    evaluator: Evaluator,
    max_iterations: int = 4,
) -> LoopResult:
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")

    trace: list[Attempt] = []
    feedback: str | None = None
    prior: str | None = None
    best: Attempt | None = None

    for i in range(1, max_iterations + 1):
        candidate = generator.generate(brief, prior, feedback)
        verdict = evaluator.evaluate(brief, candidate)
        attempt = Attempt(candidate, verdict)
        trace.append(attempt)
        if best is None or verdict.score > best.verdict.score:
            best = attempt
        if verdict.accepted:
            return LoopResult(best, True, i, trace)
        prior, feedback = candidate, verdict.feedback

    assert best is not None
    return LoopResult(best, False, max_iterations, trace)


class KeywordLengthGenerator:
    """Simulates an LLM that drafts a product blurb and edits it toward feedback."""

    def __init__(self, keyword: str) -> None:
        self.keyword = keyword

    def generate(self, brief: str, prior: str | None, feedback: str | None) -> str:
        if prior is None:
            return "A fast, lightweight tool for developers."
        if feedback and "keyword" in feedback:
            prior = prior.rstrip(".") + f", built around {self.keyword}."
        if feedback and "shorter" in feedback:
            prior = prior.split(",")[0] + "."
        return prior


class KeywordLengthEvaluator:
    def __init__(self, keyword: str, max_words: int = 14) -> None:
        self.keyword = keyword
        self.max_words = max_words

    def evaluate(self, brief: str, candidate: str) -> Verdict:
        words = candidate.split()
        has_keyword = self.keyword.lower() in candidate.lower()
        within_length = len(words) <= self.max_words
        score = (1.0 if has_keyword else 0.0) + (1.0 if within_length else 0.0)
        if has_keyword and within_length:
            return Verdict(True, score, "meets rubric")
        missing = []
        if not has_keyword:
            missing.append(f"missing required keyword '{self.keyword}'")
        if not within_length:
            missing.append(f"make it shorter, at most {self.max_words} words")
        return Verdict(False, score, "; ".join(missing))


def main() -> None:
    keyword = "evaluator-optimizer"
    result = refine(
        brief="Write a one-sentence product blurb.",
        generator=KeywordLengthGenerator(keyword),
        evaluator=KeywordLengthEvaluator(keyword),
        max_iterations=4,
    )
    for i, attempt in enumerate(result.trace, start=1):
        status = "ACCEPT" if attempt.verdict.accepted else "REJECT"
        print(f"iteration {i}: {status} score={attempt.verdict.score} -> {attempt.candidate!r}")
    print(f"final: accepted={result.accepted} after {result.iterations} iteration(s)")
    print(f"best candidate: {result.best.candidate!r}")


if __name__ == "__main__":
    main()
```

### TypeScript

Type-checked with `tsc --noEmit --strict` against TypeScript 5. The
built-in DOM/lib generator type is already named `Generator`, so this
sample calls the role `Drafter` to avoid the name collision, a naming
lesson worth carrying into any real codebase implementing this pattern in
TypeScript.

```typescript
interface Verdict {
  readonly accepted: boolean;
  readonly score: number;
  readonly feedback: string;
}

interface Drafter<TInput, TCandidate> {
  generate(input: TInput, prior: TCandidate | null, feedback: string | null): TCandidate;
}

interface Evaluator<TInput, TCandidate> {
  evaluate(input: TInput, candidate: TCandidate): Verdict;
}

interface Attempt<TCandidate> {
  readonly candidate: TCandidate;
  readonly verdict: Verdict;
}

interface LoopResult<TCandidate> {
  readonly best: Attempt<TCandidate>;
  readonly accepted: boolean;
  readonly iterations: number;
  readonly trace: ReadonlyArray<Attempt<TCandidate>>;
}

function refine<TInput, TCandidate>(
  input: TInput,
  drafter: Drafter<TInput, TCandidate>,
  evaluator: Evaluator<TInput, TCandidate>,
  maxIterations: number,
): LoopResult<TCandidate> {
  if (maxIterations < 1) {
    throw new RangeError("maxIterations must be at least 1");
  }

  const trace: Attempt<TCandidate>[] = [];
  let best: Attempt<TCandidate> | null = null;
  let prior: TCandidate | null = null;
  let feedback: string | null = null;

  for (let i = 1; i <= maxIterations; i++) {
    const candidate = drafter.generate(input, prior, feedback);
    const verdict = evaluator.evaluate(input, candidate);
    const attempt: Attempt<TCandidate> = { candidate, verdict };
    trace.push(attempt);

    if (best === null || verdict.score > best.verdict.score) {
      best = attempt;
    }
    if (verdict.accepted) {
      return { best, accepted: true, iterations: i, trace };
    }
    prior = candidate;
    feedback = verdict.feedback;
  }

  return { best: best as Attempt<TCandidate>, accepted: false, iterations: maxIterations, trace };
}

interface SqlQuery {
  readonly text: string;
}

class SqlDraftGenerator implements Drafter<string, SqlQuery> {
  constructor(private readonly requiredColumn: string) {}

  generate(_brief: string, prior: SqlQuery | null, feedback: string | null): SqlQuery {
    if (prior === null) {
      return { text: "SELECT * FROM orders" };
    }
    if (feedback !== null && feedback.includes(this.requiredColumn)) {
      return { text: `SELECT id, ${this.requiredColumn} FROM orders` };
    }
    return prior;
  }
}

class NoSelectStarEvaluator implements Evaluator<string, SqlQuery> {
  constructor(private readonly requiredColumn: string) {}

  evaluate(_brief: string, candidate: SqlQuery): Verdict {
    const usesStar = candidate.text.includes("SELECT *");
    const hasColumn = candidate.text.includes(this.requiredColumn);
    if (!usesStar && hasColumn) {
      return { accepted: true, score: 1, feedback: "meets rubric" };
    }
    const reasons: string[] = [];
    if (usesStar) reasons.push("do not select *, list columns explicitly");
    if (!hasColumn) reasons.push(`must project ${this.requiredColumn}`);
    return { accepted: false, score: 0, feedback: reasons.join("; ") };
  }
}

function main(): void {
  const result = refine<string, SqlQuery>(
    "draft a query that reports order totals",
    new SqlDraftGenerator("total_cents"),
    new NoSelectStarEvaluator("total_cents"),
    4,
  );
  result.trace.forEach((attempt, index) => {
    const status = attempt.verdict.accepted ? "ACCEPT" : "REJECT";
    console.log(`iteration ${index + 1}: ${status} -> ${attempt.candidate.text}`);
  });
  console.log(`accepted=${result.accepted} after ${result.iterations} iteration(s)`);
}

main();
```

### Go

Run with `go run evaluator_optimizer.go`, and `go vet` reports no issues.
Executed against Go 1.24.

```go
package main

import (
	"fmt"
	"strings"
)

// Verdict is the evaluator's judgment of a single candidate.
type Verdict struct {
	Accepted bool
	Score    int
	Feedback string
}

// Generator produces a candidate from a brief, the prior candidate, and feedback.
type Generator interface {
	Generate(brief, prior, feedback string) string
}

// Evaluator judges a candidate against a brief and returns a Verdict.
type Evaluator interface {
	Evaluate(brief, candidate string) Verdict
}

// Attempt pairs a candidate with the verdict it received.
type Attempt struct {
	Candidate string
	Verdict   Verdict
}

// LoopResult is the outcome of running the evaluator-optimizer loop.
type LoopResult struct {
	Best       Attempt
	Accepted   bool
	Iterations int
	Trace      []Attempt
}

// ErrBudgetTooSmall signals a caller-supplied iteration budget below one.
var ErrBudgetTooSmall = fmt.Errorf("max iterations must be at least 1")

// Refine runs generate, evaluate, refine until acceptance or budget exhaustion.
// It always returns the highest-scoring candidate seen, never merely the last one.
func Refine(brief string, gen Generator, eval Evaluator, maxIterations int) (LoopResult, error) {
	if maxIterations < 1 {
		return LoopResult{}, ErrBudgetTooSmall
	}

	var trace []Attempt
	var best *Attempt
	prior, feedback := "", ""

	for i := 1; i <= maxIterations; i++ {
		candidate := gen.Generate(brief, prior, feedback)
		verdict := eval.Evaluate(brief, candidate)
		attempt := Attempt{Candidate: candidate, Verdict: verdict}
		trace = append(trace, attempt)

		if best == nil || verdict.Score > best.Verdict.Score {
			b := attempt
			best = &b
		}
		if verdict.Accepted {
			return LoopResult{Best: *best, Accepted: true, Iterations: i, Trace: trace}, nil
		}
		prior, feedback = candidate, verdict.Feedback
	}
	return LoopResult{Best: *best, Accepted: false, Iterations: maxIterations, Trace: trace}, nil
}

// configGenerator drafts a minimal config and edits it toward evaluator feedback.
type configGenerator struct{ requiredKey string }

func (g configGenerator) Generate(brief, prior, feedback string) string {
	if prior == "" {
		return "timeout=30"
	}
	if feedback != "" {
		return prior + " " + g.requiredKey + "=true"
	}
	return prior
}

// configEvaluator rejects a candidate missing a required key.
type configEvaluator struct{ requiredKey string }

func (e configEvaluator) Evaluate(brief, candidate string) Verdict {
	for _, field := range strings.Fields(candidate) {
		if strings.HasPrefix(field, e.requiredKey+"=") {
			return Verdict{Accepted: true, Score: 1, Feedback: "meets rubric"}
		}
	}
	return Verdict{Accepted: false, Score: 0, Feedback: "missing required key " + e.requiredKey}
}

func main() {
	result, err := Refine(
		"draft a minimal service config",
		configGenerator{requiredKey: "retries"},
		configEvaluator{requiredKey: "retries"},
		3,
	)
	if err != nil {
		panic(err)
	}
	for i, attempt := range result.Trace {
		status := "REJECT"
		if attempt.Verdict.Accepted {
			status = "ACCEPT"
		}
		fmt.Printf("iteration %d: %s -> %q\n", i+1, status, attempt.Candidate)
	}
	fmt.Printf("accepted=%v after %d iteration(s), best=%q\n", result.Accepted, result.Iterations, result.Best.Candidate)
}
```
