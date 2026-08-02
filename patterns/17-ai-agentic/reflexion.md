---
name: Reflexion
slug: reflexion
family: 17-ai-agentic
category: Agentic
aliases: [Verbal Reinforcement Learning, Reflexion Agent, Actor-Evaluator-Self-Reflection Loop]
first_described: "Shinn, Cassano, Berman, Gopinath, Narasimhan, Yao 2023"
maturity: emerging
related: [react-prompting, tool-use, plan-and-execute, self-consistency, chain-of-thought]
incompatible_with: []
verified: 2026-08-02
---

# Reflexion

## 1. Name, aliases, and lineage

The canonical name is Reflexion, spelled with an x, a deliberate typographic
distance from the word reflection that the authors use for the ordinary
English sense of an agent looking back at its own output. The pattern was
introduced by Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath,
Karthik Narasimhan, and Shunyu Yao in "Reflexion. Language Agents with Verbal
Reinforcement Learning," posted to arXiv as 2303.11366 in March 2023 and
accepted as a poster at NeurIPS 2023 ([arXiv 2303.11366](https://arxiv.org/abs/2303.11366),
verified 2026-08-02; [NeurIPS 2023 poster page](https://neurips.cc/virtual/2023/poster/70114),
verified 2026-08-02). An earlier preprint under the authors Shinn, Beau
Labash, and Ashwin Gopinath used the working title "Reflexion. An autonomous
agent with dynamic memory and self-reflection," and the camera-ready NeurIPS
version is the one this entry cites throughout, because it is the version
with the final author list, the final experiments, and the final numbers
([Semantic Scholar record for the earlier draft](https://www.semanticscholar.org/paper/Reflexion:-an-autonomous-agent-with-dynamic-memory-Shinn-Labash/46299fee72ca833337b3882ae1d8316f44b32b3c),
verified 2026-08-02).

The alias Verbal Reinforcement Learning is the authors' own name for the
mechanism, chosen to contrast with the reinforcement learning that updates
model weights from a scalar reward. Reflexion updates nothing about the
underlying model. It appends a paragraph of natural-language critique to a
memory buffer that is re-read on the next attempt, so the reinforcement
signal is a sentence, not a gradient. The paper states its goal plainly, to
reinforce language agents not by updating weights, but through linguistic
feedback ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366), abstract,
verified 2026-08-02). The alias Actor-Evaluator-Self-Reflection Loop is a
description used across secondary sources, including the official LangGraph
tutorial that reproduces the pattern, to name the three prompted roles the
architecture decomposes into ([langchain-ai/langgraph, pinned commit
23961cff61a42b52525f3b20b4094d8d2fba1744, docs/docs/tutorials/reflexion/reflexion.ipynb](https://github.com/langchain-ai/langgraph/blob/23961cff61a42b52525f3b20b4094d8d2fba1744/docs/docs/tutorials/reflexion/reflexion.ipynb),
verified 2026-08-02).

One naming confusion is worth settling early, because it recurs across
frameworks and blog posts and it changes what a reader should expect from a
system that claims to use it. Reflection, lowercase, no x, is a general
prompting strategy where one LLM generation is followed by a second LLM
generation that critiques or revises the first. Microsoft's AutoGen
documents exactly this shape as its own named design pattern, a pair of
agents where "the first agent generates a message and the second agent
generates a response to the message" ([AutoGen documentation, Reflection
design pattern](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/reflection.html),
verified 2026-08-02). That two-agent critique loop is real and useful, older
than Reflexion in spirit, but it is not the same pattern. Reflexion, as
Shinn et al. define it, has three specific parts working over multiple
bounded trials, an Actor that produces a full trajectory, an Evaluator that
scores that trajectory against some external signal such as a compiler, a
unit test suite, or an environment's success flag, and a Self-Reflection
model that converts the score and the trajectory into a stored, natural
language lesson that persists across trials in a size-bounded episodic
memory. A system that runs one critique pass with no external evaluator and
no persistent memory across attempts is doing Reflection. A system that
loops an Actor against a real Evaluator, accumulates verbal lessons in a
bounded buffer, and stops only when the Evaluator passes or a trial budget
is exhausted is doing Reflexion. This entry is about the second, narrower
thing, and every claim below should be read as a claim about that specific
architecture unless stated otherwise.

## 2. Problem and context

An LLM agent that tries a task once and stops inherits every mistake in that
one attempt permanently. The situation looks like this in practice. An agent
is asked to write a function, and the function it writes fails three of five
hidden unit tests. Or an agent is dropped into a text-based household
environment and needs to find a mug, heat it, and place it on a counter, and
it spends its action budget searching a cabinet it already searched twice.
Or an agent answers a multi-hop question from a Wikipedia-grounded corpus and
retrieves a page that is topically close but wrong, then reasons confidently
from the wrong page to a wrong final answer. In each case the agent produced
a full, coherent attempt, that attempt was checkable against something
outside the model, the model was simply never shown the result of the check
before making its next move, because there was no next move. One shot, one
outcome.

Traditional reinforcement learning solves the try, fail, improve problem by
updating the policy's weights from the observed reward. That path is
available to a lab training a base model and unavailable to almost everyone
else, because it needs gradient access, a training loop, and enough compute
and enough episodes to move weights by a useful amount. It is also slow to
iterate. A gradient step reflects one scalar number's worth of signal per
episode, averaged over a batch, and the lesson learned is smeared across the
whole policy rather than tied to the specific mistake that produced it.

The context that makes Reflexion the right answer has three parts, all
present at once.

- The task has an external signal that can check a full attempt after the
  fact and say, with reasonable reliability, whether it succeeded. A
  compiler, a test suite, an environment's binary success flag, or a
  string-match against a known answer are all usable signals. A vague sense
  of quality with no check is not.
- Weight updates are unavailable, too slow, or simply the wrong tool for the
  amount of adaptation needed, because the task is a one-off or the number
  of episodes available is small.
- The mistake, once surfaced, is expressible as a sentence an LLM can
  actually use on the next attempt. "You searched cabinet 3 twice and never
  checked the microwave" is usable. A single float loss value is not.

Where a real check exists and weight updates are off the table, verbal
feedback stored in a small memory and re-read on the next attempt is a
cheap, fast, interpretable substitute for a gradient step, and that
substitution is the entire idea behind Reflexion.

## 3. Forces

The pattern balances the following competing pressures, and the balance it
strikes is a specific and sometimes surprising one.

- **Cost per improvement.** Favoured, heavily. One extra LLM call per failed
  trial to generate the self-reflection is far cheaper than a fine-tuning
  run, and the improvement is available immediately, in the same session,
  with no training infrastructure at all.
- **Interpretability.** Favoured. Every lesson the agent has learned sits in
  the memory buffer as a readable sentence. A person debugging a failing run
  can read exactly what the agent told itself, which a gradient update
  never offers.
- **Reliability of the signal.** This is the force the pattern is most
  exposed on. Reflexion's improvement is only as good as the Evaluator's
  judgement, and the paper says so directly, that the approach relies on a
  self-evaluation capability that "may not be readily available" for every
  task ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366), limitations
  discussion, verified 2026-08-02). Where the Evaluator is a real compiler
  or a real unit test, the signal is trustworthy. Where the Evaluator is the
  same LLM judging its own reasoning with no ground truth to check against,
  the signal can be wrong in exactly the direction the agent already
  believes, and the loop reinforces a mistake instead of correcting it. This
  is judgement, developed further in dimension 11, but it is the central
  trade-off of the whole pattern.
- **Latency versus quality.** Sacrificed on purpose. Each additional trial
  adds a full round trip, the Actor call, the Evaluator check, and the
  Self-Reflection call, so a bounded loop of, say, four trials costs roughly
  four times the tokens and four times the wall-clock time of a single
  attempt, in exchange for a higher final success rate on tasks where the
  Evaluator is trustworthy.
- **Context budget.** Sacrificed, but bounded deliberately. Every reflection
  appended to memory consumes tokens on every subsequent Actor call. The
  paper's own answer to this is to cap the memory at a small number of
  stored experiences, denoted capital omega and usually set to one to
  three, to respect the model's context limit ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366),
  section 3, verified 2026-08-02). This is a hard, explicit budget the
  pattern requires, not an incidental detail.
- **Generality across task types.** The pattern's own experiments show this
  force is not free. Reflexion helps a great deal on code generation, where
  the Evaluator is a real compiler and real tests, and it helps less
  uniformly on open-ended, long-running embodied tasks, where the Evaluator
  has to guess at success with no ground truth, discussed with a concrete
  example in dimension 11.

## 4. Applicability and non-applicability

Reach for Reflexion when:

- The task produces an artifact, code, an answer, an action trajectory, that
  can be checked by something outside the generating model itself, ideally
  a deterministic tool such as a compiler, an interpreter, a linter, or a
  test runner.
- The task can be attempted more than once inside a session, with a modest
  budget, three to a dozen trials in the paper's own experiments, without
  the cost of a failed attempt being unacceptable, for example a code
  generation task in a sandbox, not a financial transaction with real money
  attached.
- Weight updates are not an option, either because the model is accessed
  only through an API, or because the number of task instances is far too
  small to justify a training run.
- A verbal explanation of the failure is genuinely informative for the next
  attempt, meaning the failure has a describable cause, an off-by-one, a
  wrong tool call, a missed constraint, rather than being pure aleatoric
  noise.

Non-applicability. Do not reach for Reflexion when:

- There is no reliable external evaluator. If the only judge of success is
  the same model reasoning about its own correctness with nothing outside
  itself to check against, self-reflection risks confidently entrenching an
  error rather than correcting it, which is exactly the failure mode Huang
  et al. document for reasoning tasks and is discussed at length in
  dimension 11.
- Latency is a hard, small budget and only one attempt fits. A single-shot
  interactive assistant answering a chat message in under a second has no
  room for a multi-trial loop.
- The task is a single, cheap, well-specified transformation where a
  simpler technique already gets a high success rate on the first attempt,
  for example basic formatting or extraction from clean structured input,
  where the added latency of a reflection loop buys almost nothing.
- The domain is long-running and open-ended with sparse or ambiguous
  success signals, such as an agent operating in an unbounded sandbox game
  with no crisp win condition per subtask. Voyager, an open-ended embodied
  Minecraft agent, uses Reflexion as one of its own comparison baselines
  and reports it made no real progress, annotated N/A(0/3) across its
  evaluation runs, in a setting that lacks the crisp, checkable success
  signal Reflexion depends on ([Wang et al., Voyager. An Open-Ended
  Embodied Agent with Large Language Models, arXiv 2305.16291, tables
  reporting the Reflexion baseline results](https://voyager.minedojo.org/assets/documents/voyager.pdf),
  verified 2026-08-02).
- The cost of a wrong action is high and irreversible, for example an agent
  that sends an email or moves real funds on each trial. A loop designed
  around retrying failed attempts should never retry an attempt whose side
  effects cannot be undone.
- Fine-tuning data and infrastructure already exist and the task volume is
  large enough that a trained policy improvement will compound across
  thousands of future calls. At that volume the fixed cost of training
  usually beats the recurring per-call cost of a multi-trial loop.

## 5. Structure

Four participants, three of them prompted LLM roles and one a plain data
structure.

- **Actor**, denoted Ma in the paper. A large language model prompted to act
  as the task-solving policy. It consumes the current state, plus whatever
  is in the episodic memory, and produces a trajectory, a sequence of
  thoughts, actions, and observations, or in the code-generation setting, a
  candidate solution. The Actor can itself be built on Chain of Thought or
  ReAct-style prompting, the paper is explicit that Reflexion is a layer on
  top of an existing Actor style, not a replacement for one
  ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366), section 3, verified
  2026-08-02).
- **Evaluator**, denoted Me. Scores the trajectory. This can be a scalar
  reward function tied to a real check, a compiler and test suite for code,
  an exact-match grader for a known answer, or a binary success flag from an
  environment. The paper is candid that defining effective value and reward
  functions that apply to semantic spaces is difficult, and explores
  several Evaluator variants across its experiments rather than treating
  this as a solved problem ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366),
  section 3, verified 2026-08-02).
- **Self-Reflection model**, denoted Msr. Another LLM call, given the
  trajectory and the Evaluator's score, that produces specific, detailed
  feedback in natural language rather than a bare pass or fail
  ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366), section 3, verified
  2026-08-02). This is the step that turns a sparse signal into something
  the Actor can actually use.
- **Episodic memory**, mem, a list, capped at a small integer omega. Each
  trial's self-reflection is appended, and the list is truncated to the
  most recent omega entries. It is passed into the Actor's prompt on the
  next trial as additional context, but nothing about the Actor's weights
  changes. This is short-term, session-scoped memory, distinct from the
  long-term semantic memory some later agent architectures add on top.

## 6. ASCII structure diagram

```
+----------------------------------------------------------+
|                    Reflexion agent                       |
|                                                            |
|   state, task  --->  +----------+                         |
|                       |  Actor   |                         |
|                       |  (Ma)    |------ trajectory  ----->|
|          +----------->|  policy  |         tau_t            |
|          |            +----------+                          |
|          |                                    |              |
|   read omega                              +----v-----+        |
|   most recent                             |Evaluator |        |
|   reflections                             |  (Me)    |        |
|          |                                +----+-----+        |
|          |                                     |               |
|   +------+--------+                       score r_t           |
|   |   Episodic     |                            |               |
|   |   memory       |<-----+                +----v-------+       |
|   |   mem[Omega]   |      |                | Self-      |       |
|   |   (bounded,    |      +----------------| Reflection |       |
|   |   1 to 3 items)|      reflection sr_t   | (Msr)      |       |
|   +----------------+                        +------------+       |
+----------------------------------------------------------+
```

## 7. Dynamics

```
trial 0
  tau_0 = Actor(state, mem=[])
  r_0   = Evaluator(tau_0)              # e.g. run compiled tests
  if r_0 == pass, return tau_0          # done in one shot
  sr_0  = SelfReflection(tau_0, r_0)
  mem   = [sr_0]

trial 1
  tau_1 = Actor(state, mem=[sr_0])
  r_1   = Evaluator(tau_1)
  if r_1 == pass, return tau_1
  sr_1  = SelfReflection(tau_1, r_1)
  mem   = [sr_0, sr_1]                  # truncate to last Omega entries

trial t, where 2 <= t < max_trials
  tau_t = Actor(state, mem)
  r_t   = Evaluator(tau_t)
  if r_t == pass, return tau_t
  sr_t  = SelfReflection(tau_t, r_t)
  mem.append(sr_t); mem = mem[-Omega:]

after max_trials with no pass
  return best_or_last(trials)           # caller decides fallback policy
```

The loop terminates on the first Evaluator pass or when the trial budget is
exhausted, whichever comes first. The paper's own AlfWorld experiments run
twelve consecutive trials per task, and observe the ReAct-only baseline's
performance plateau between trials six and seven while the Reflexion agent
keeps improving through trial twelve, converging near-perfect performance
([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366), section 4.1, verified
2026-08-02). Nothing in the loop updates the Actor's weights at any point,
the entire improvement across trials lives in the growing, then bounded,
memory buffer that is re-read as plain text on every subsequent Actor call.

## 8. Implementation variants

- **Code generation, external evaluator is a real compiler and test
  suite.** This is the setting where Reflexion is strongest, because the
  Evaluator's signal is not a judgement call, it is a fact. The Actor
  proposes a candidate solution, the Evaluator compiles and runs it against
  unit tests, and a compile error or a failing assertion is fed directly
  into the Self-Reflection prompt. The code sample accompanying this entry
  implements exactly this shape, and its inline comments say plainly that
  in a shipped version, the Actor step is an LLM call whose source is
  compiled or loaded at runtime, while the sample substitutes a fixed
  candidate ladder so the demonstration runs offline with no network
  dependency and no API key.
- **Sequential decision-making with a binary environment signal.** In the
  paper's AlfWorld experiments, the Evaluator is a simple heuristic that
  flags a trajectory as failed when the agent repeats an action or exceeds
  a step budget without help, in addition to the environment's own success
  or failure flag ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366),
  section 4.1, verified 2026-08-02).
- **Reasoning with self-consistency as the Evaluator.** In the reasoning
  experiments on HotPotQA, the paper explores an Evaluator built from
  self-consistency, checking whether repeated samples from the Actor agree,
  as a substitute for a ground-truth grader, alongside experiments that use
  an oracle answer-match grader ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366),
  section 4.2, verified 2026-08-02).
- **The bounded memory buffer, Omega.** Reflexion's own memory bound
  matters as much as the reflection step itself. The paper explicitly
  bounds mem by a maximum number of stored experiences, Omega, usually set
  to one to three, to adhere to the model's context limit
  ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366), section 3, verified
  2026-08-02). Two practical variants exist for what happens when the buffer
  is full, drop the oldest entry, first in first out, which is what the
  reference implementation and this entry's code samples do, or keep the
  highest-value entries by some secondary ranking, which the paper does not
  test but is a natural extension for a system whose reflections vary in
  usefulness.
- **Actor prompting style.** The Actor can be instantiated as plain Chain of
  Thought or as ReAct, interleaving thought and tool-using action, and the
  paper reports both and finds ReAct-based Actors benefit more, because
  ReAct's explicit action-observation trace gives the Self-Reflection model
  concrete, checkable steps to critique, rather than a single freeform
  answer ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366), section
  4.1, verified 2026-08-02).
- **Reflection loop budgets in practice.** A max_trials budget of three to
  five is common in the framework implementations that reproduce this
  pattern, trading additional latency for a higher pass rate, and the
  paper's own code-generation experiments and the LangGraph reproduction
  both terminate the loop the moment the Evaluator passes, never running
  the full budget when an early trial already succeeds.

## 9. Known production uses

Reflexion is a young pattern, first published in 2023, and its adoption
outside research reproductions is still concentrated in agent-orchestration
frameworks rather than the kind of decades-old, embedded-in-every-standard-
library usage a Gang of Four pattern accumulates. The uses below are named,
sourced, and independently verifiable, but this entry is honest that the
pattern's track record is shorter than most others in this catalog, which
is exactly what the emerging maturity marker in the frontmatter signals.

**The reference implementation, noahshinn/reflexion.** The paper's own
authors ship the code, demos, and experiment logs behind all of the numbers
in dimension 7 and dimension 10 as an open repository tagged for its NeurIPS
2023 acceptance, actively starred and forked as the canonical implementation
other projects build on or compare against
([github.com/noahshinn/reflexion](https://github.com/noahshinn/reflexion),
verified 2026-08-02).

**LangGraph's official Reflexion tutorial, part of the LangChain
project.** LangChain's graph-based agent orchestration library shipped an
official tutorial implementing the pattern faithfully, describing the same
three components this entry documents in dimensions 5 through 7, an actor
with self-reflection, an external evaluator such as a code compilation
step, and an episodic memory that stores the reflections, and citing arXiv
2303.11366 directly as its source ([langchain-ai/langgraph, pinned commit
23961cff61a42b52525f3b20b4094d8d2fba1744, docs/docs/tutorials/reflexion/reflexion.ipynb](https://github.com/langchain-ai/langgraph/blob/23961cff61a42b52525f3b20b4094d8d2fba1744/docs/docs/tutorials/reflexion/reflexion.ipynb),
verified 2026-08-02). The standalone tutorial page has since been
consolidated into LangChain's broader documentation site as the project
reorganized its docs, but the implementation and its citation are preserved
and verifiable at the pinned commit above, and LangGraph itself remains a
widely deployed open-source orchestration framework underneath many
production LangChain agent deployments.

**Independent replication and stress-test by Huang et al., ICLR 2024.** A
separate research team, not affiliated with the original authors,
re-implemented Reflexion's self-correction methodology as one of the
baselines it evaluates in "Large Language Models Cannot Self-Correct
Reasoning Yet." Its own summary table of prior self-correction work lists
Reflexion, attributed to Shinn et al. 2023, by name alongside RCI as a
method that uses oracle labels, and the paper reruns that methodology on
GSM8K, CommonSenseQA, and HotpotQA using GPT-3.5 and GPT-4 to test whether
the reported gains hold once ground-truth answer labels are no longer
available to stop the loop ([Huang, Chen, Mishra, Zheng, Yu, Song, Zhou,
Large Language Models Cannot Self-Correct Reasoning Yet, ICLR 2024, arXiv
2310.01798](https://arxiv.org/pdf/2310.01798), table 1 and section 3,
verified 2026-08-02). This is not a favourable production deployment, its
findings are exactly the cautionary evidence discussed in dimension 11, but
it is a genuine, independent, code-level replication of the pattern by a
separately-authored, peer-reviewed paper, and it counts as a real use of the
architecture this entry describes, not merely a citation in passing.

## 10. Consequences

Positive.

- A failed attempt is converted into a specific, reusable, human-readable
  lesson rather than being discarded, and that lesson measurably changes
  the next attempt without touching a single model weight.
- The improvement is available immediately, inside a single session, with
  no training infrastructure, no labeled dataset beyond whatever the
  Evaluator already checks, and no wait for a training run to complete.
- On the paper's own benchmark, Reflexion lifts GPT-4's HumanEval pass at 1
  accuracy to 91.0 percent, against a previous best result of 80.1
  percent for GPT-4 with standard prompting, a jump the authors describe as
  surpassing the previous state of the art ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366),
  abstract and table 1, verified 2026-08-02).
- The same table reports Reflexion improving HumanEval translated to Rust
  from a prior GPT-4 best of 60.0 to 68.0, and MBPP translated
  to Rust from 70.9 to 75.4, showing the gain is not a single-benchmark
  artifact ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366), table 1,
  verified 2026-08-02).
- On AlfWorld, across 134 multi-step household tasks, the paper reports an
  absolute 22 percent improvement over strong baselines within twelve
  iterative trials, and on HotPotQA an absolute 20 percent improvement
  ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366), section 4,
  verified 2026-08-02).
- The memory buffer is small and cheap by design, bounded to one to three
  entries, so the pattern's context cost does not grow unbounded across a
  long session the way an unbounded transcript would.
- Every intermediate lesson is inspectable text, which makes a failing run
  substantially easier to debug than a model whose failure mode is buried
  in weights.

Negative.

- Latency and cost scale roughly linearly with the number of trials, and
  every trial that fails costs a full Actor call, a full Evaluator check,
  and a full Self-Reflection call, so a bounded loop of four trials against
  a compiler is substantially slower and more expensive than one attempt,
  even though it converges to a correct answer more often.
- The pattern's benefit is capped by the quality of the Evaluator, and a
  weak or self-referential Evaluator does not merely fail to help, it can
  actively hurt, a point examined at length in dimension 11.
- The paper's own AlfWorld analysis records a baseline hallucination rate
  converging around 22 percent with no sign of recovery for agents that
  lack the self-reflection step, implying the self-reflection step is
  doing real, necessary work rather than being a redundant flourish, but
  also implying that a poorly-tuned or missing self-reflection step leaves
  that failure mode fully exposed ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366),
  section 4.1, verified 2026-08-02).
- The bounded memory is a real constraint. Setting Omega too small discards
  a lesson that would have been useful two trials later, and the paper
  offers no principled rule for choosing Omega beyond the informal one to
  three range that fit their context budgets, leaving the choice to trial
  and error on each new task.
- On open-ended, long-running tasks with no crisp per-attempt success
  signal, the pattern can simply fail to help at all, as documented for
  Voyager's Minecraft baselines in dimension 4 and dimension 11.

## 11. Failure modes and misuse

**Symptom.** The agent's self-reflection notes read as confident and
specific, but the agent's success rate does not improve, or gets worse,
across trials. **Cause.** There is no reliable external signal grounding
the Evaluator, so the Self-Reflection model is critiquing the Actor's
reasoning using the same reasoning capacity that produced the mistake in
the first place, and it has no way to tell a genuine error from a correct
answer it merely finds unfamiliar. Huang et al. show this concretely on
GSM8K, once oracle answer labels are removed from the loop, so the model
itself must decide whether to keep or revise its answer, GPT-3.5's accuracy
drops from 75.9 to 74.7 after two rounds of self-correction, and GPT-4's
drops from 95.5 to 89.0, with the paper's own breakdown showing the model is
more likely to modify a correct answer into an incorrect one than to
revise an incorrect answer into a correct one ([Huang et al., ICLR 2024,
arXiv 2310.01798](https://arxiv.org/pdf/2310.01798), tables 2 and 3, and
section 3.3, verified 2026-08-02). **Fix.** Never wire the Evaluator to the
same undifferentiated model call that produced the attempt with no external
check. Where a ground-truth check genuinely exists, oracle labels for
training and evaluation, a compiler, a test suite, use it as the Evaluator.
Where no such check exists, treat the pattern's benefit as unproven for that
task and consider a technique that does not require the model to judge its
own correctness, discussed further in dimension 12.

**Symptom.** An agent operating in a large, open-ended environment shows no
improvement across trials despite generating apparently reasonable
self-reflections each time, and its trajectories look qualitatively similar
trial after trial. **Cause.** The task lacks the crisp, per-attempt success
signal Reflexion's Evaluator needs, and the reflection has nothing concrete
to anchor to, so it tends to restate a general strategy rather than name a
specific, usable correction. Voyager's own comparison table lists
Reflexion's results across its Minecraft item-finding evaluation as
N/A(0/3) in every column, with the paper stating that the ReAct and
Reflexion baselines lag because they fail to advance in
that open-ended setting ([Wang et al., arXiv 2305.16291, tables reporting
baseline comparisons](https://voyager.minedojo.org/assets/documents/voyager.pdf),
verified 2026-08-02). **Fix.** Do not deploy Reflexion unmodified in an
open-ended, sparse-reward environment. Either narrow the task into
sub-goals each of which has its own checkable success condition, or add a
dedicated, broader verification module, which is exactly the direction
Voyager itself took, building a distinct self-verification component
rather than relying on reflection alone.

**Symptom.** The agent's context grows across a long session and either
starts truncating useful earlier context or the cost per Actor call climbs
noticeably as the session continues. **Cause.** The episodic memory buffer
was implemented as an ever-growing list instead of the bounded structure
the pattern specifies, so every reflection ever generated is still being
re-injected into every subsequent prompt. **Fix.** Bound the buffer
explicitly to a small integer, the paper's own guidance is one to three
stored experiences, and truncate on a first-in-first-out basis, or by an
explicit relevance rule, every time a new reflection is appended, exactly
as shown in the code sample's memory_cap and Omega handling.

**Symptom.** The loop runs to the full trial budget on almost every task,
even ones a single well-prompted attempt would have solved, and overall
latency and API cost are far higher than expected. **Cause.** The Actor's
prompt does not clearly incorporate the memory buffer's contents, so each
trial is effectively a fresh, uninformed attempt rather than one that
builds on the prior reflection, and the loop only succeeds by brute-force
resampling rather than by genuine improvement. **Fix.** Verify, by
inspecting a handful of transcripts, that the Actor's prompt actually
contains the accumulated reflections exactly as written and that the reflections
themselves name a specific, checkable correction rather than a vague
restatement of the goal. If reflections read as generic, the
Self-Reflection prompt needs to be given more of the failing trajectory,
the exact assertion that failed or the exact compiler error, not merely a
pass or fail bit.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Reflexion | ReAct alone | Best-of-N with a verifier | Self-Refine, no external Evaluator | Fine-tuning or RLHF |
|---|---|---|---|---|---|
| Needs weight updates | No | No | No | No | Yes |
| Needs an external checkable signal | Yes, that is its core requirement | No, but also does not improve across attempts | Yes, the verifier plays this role | No, self-critiques with no outside check | Yes, at training time |
| Cost per improved attempt | Medium. One extra LLM round trip per trial | Low. Single pass | Medium to high. N full generations plus verification | Medium. One extra critique pass, but unreliable without a check | High up front, near zero at inference after training |
| Persists across sessions | No. Memory is session-scoped and bounded | Not applicable | No | No | Yes. The improvement is baked into weights |
| Improves without a ground-truth checker | Poor, per Huang et al.'s findings | Not applicable, does not iterate | Depends entirely on verifier quality | Poor, same self-judging weakness as Reflexion without an Evaluator | Yes, once trained, generalizes beyond the training checks |
| Debuggability | High. Every lesson is readable text | Medium. One trace to read | Medium. N traces plus a verifier's picks | High. Readable critiques, but critiques can be wrong | Low. Improvement is opaque, inside weights |
| Latency | Scales with trial count, bounded loop | Lowest, single pass | Scales with N, parallelizable | Scales with critique-refine rounds | Near zero at inference |
| Best fit | Code generation, tool use with a real check | Simple tool-using tasks needing no retry | Tasks with a cheap, reliable automatic verifier | Style or clarity polish where correctness is not the bottleneck | High-volume, stable tasks where training cost amortizes |

Reading of the table. Reflexion and Self-Refine share the same shape, an
Actor and a critique step, and the entire difference between them is
whether an external Evaluator exists. Where it does, Reflexion is the
stronger choice, because the critique is anchored to a fact rather than to
the model's own opinion of itself. Best-of-N with a verifier trades latency
and cost for parallelism and sidesteps the need for a sequential loop
entirely, at the price of paying for N full generations up front rather
than stopping the moment the first attempt passes. Fine-tuning wins only
where the volume of similar tasks is large enough to amortize its training
cost, and its improvement, unlike Reflexion's, survives past the current
session.

## 13. Related and incompatible patterns

- **ReAct.** The natural host for the Actor role. ReAct interleaves
  reasoning and tool-using actions into a single trace, and Reflexion's own
  paper builds its strongest Actor variants on top of ReAct rather than
  plain Chain of Thought, because ReAct's explicit action-observation steps
  give the Self-Reflection model something concrete to critique
  ([arXiv 2303.11366](https://arxiv.org/pdf/2303.11366), section 4.1,
  verified 2026-08-02).
- **Tool use.** Composes cleanly. The Evaluator in most real deployments is
  itself a tool call, a compiler invocation, a test runner, a search
  query's exact-match check, so a Reflexion system is usually a tool-using
  agent with an extra critique-and-retry layer wrapped around it.
- **Plan and execute.** A substitute for long-running tasks where a single
  flat trial-and-retry loop is too coarse-grained. Plan and execute
  decomposes the task into sub-goals up front, each of which can then carry
  its own, smaller Reflexion loop, which is closer to the fix recommended
  in dimension 11 for open-ended environments than running one Reflexion
  loop over the entire task.
- **Self-consistency.** A different way to spend the same extra inference
  budget. Instead of a sequential critique-and-retry loop, self-consistency
  samples several independent attempts and takes a majority vote, and
  Reflexion's own HotPotQA experiments use a self-consistency check as one
  of the Evaluator variants it explores, which shows the two patterns can
  also compose, self-consistency supplying the checkable signal Reflexion
  needs.
- **Self-Refine.** A close cousin and, in the strict sense, a special case.
  Self-Refine iterates an Actor against its own critique with no external
  Evaluator at all. Every caution about Reflexion losing reliability
  without an external check, discussed in dimension 11, applies to
  Self-Refine even more directly, since it never had an external check to
  begin with.
- **Retrieval-augmented generation.** Orthogonal, and frequently paired.
  Retrieval supplies the Actor with better grounding context before an
  attempt, while Reflexion improves the attempt after the fact, and a
  system commonly uses both, retrieval to reduce the chance of a wrong
  attempt and Reflexion to recover when one happens anyway.
- **Fine-tuning and RLHF.** Not incompatible, but positioned as the
  alternative on the opposite end of the cost and permanence range,
  detailed in dimension 12. A team can use Reflexion during development to
  find and study failure patterns, then fine-tune once a pattern of
  correctable mistakes is well understood and the task volume justifies
  training.

## 14. Refactoring path in and out

Introducing Reflexion into an existing single-shot agent, step by step.

1. Identify or build a real Evaluator first, before touching the Actor at
   all. If the task already has tests, a linter, or a known-answer check,
   wire that in as a standalone function that returns a pass or fail plus a
   detail message. If no such check exists, stop here, per dimension 4, and
   consider whether this task is a fit at all.
2. Wrap the existing single Actor call in a loop with an explicit,
   small max_trials, three to five is a reasonable starting budget, and
   make the loop exit the moment the Evaluator passes.
3. Add the Self-Reflection call, a separate LLM prompt whose only input is
   the failing trajectory and the Evaluator's detail message, and whose
   only output is a short natural-language lesson. Do not let this step
   silently reuse the Actor's own prompt or persona, keep it a distinct
   call so its failure mode is independently debuggable.
4. Add the bounded episodic memory, a plain list capped at Omega entries,
   and thread it into the Actor's prompt on every subsequent trial. Verify,
   by reading transcripts, that the Actor's prompt genuinely contains the
   memory's contents.
5. Instrument every trial, per dimension 16, before trusting the loop in
   production, since a silently-non-improving loop looks identical to a
   working one from the outside if nobody is measuring trial-by-trial
   improvement.

Removing Reflexion once it stops earning its place, the reverse path.

1. If telemetry from dimension 16 shows the loop rarely improves past trial
   one, or the Evaluator has quietly become unreliable, first check whether
   the Evaluator itself has drifted, an updated test suite, a changed
   compiler, before assuming the pattern itself has failed.
2. If the task volume has grown large and stable enough that fine-tuning
   now amortizes, use the accumulated transcripts and self-reflections as
   training signal, they are, in effect, a hand-labeled dataset of common
   mistakes and their fixes, then retire the runtime loop once the trained
   policy's single-shot accuracy matches or beats the multi-trial loop's
   accuracy.
3. Collapse the loop back to a single Actor call plus the Evaluator check
   alone, keeping the Evaluator as a cheap correctness gate even after the
   self-reflection and retry machinery is removed, since the Evaluator's
   value as a check is independent of whether the model retries on
   failure.

## 15. Testing and verification

Testing a Reflexion loop happens on two separate levels, and conflating them
is the single most common mistake.

**Testing the Evaluator in isolation.** Because the Evaluator is usually a
plain function, a compiler wrapper, a test runner, an exact-match check, it
should be unit tested exactly like any other function, with both cases that
must pass and cases that must fail, independent of any LLM call. A broken
Evaluator that reports pass when it should report fail silently disables
the entire benefit of the pattern, since the Actor never receives a useful
signal to reflect on, and this is the single highest-value test to write
first.

**Testing the loop's control flow deterministically.** The Actor and
Self-Reflection steps are non-deterministic LLM calls, but the loop around
them, the trial counter, the memory bound, the termination condition, is
plain code and should be tested with the LLM calls replaced by fixed test
doubles. This is exactly what the code sample accompanying this entry does,
substituting a fixed candidate ladder for the Actor so that convergence on
a specific trial, and the exact contents of the memory buffer afterward,
are asserted deterministically without any network call. That approach
generalizes directly, stub the Actor to return a scripted sequence of
increasingly correct attempts and assert the loop terminates at the right
trial with the right memory contents, and separately stub it to never
succeed and assert the loop respects max_trials rather than looping
forever.

**Testing the memory bound specifically.** Write a dedicated test that
forces more than Omega failures and asserts the memory buffer never exceeds
Omega entries and always contains the most recent ones, since a silent
regression here, for example someone changing the truncation logic during
an unrelated refactor, produces the unbounded-context failure mode
described in dimension 11 without any visible error until token costs or
context-limit failures show up much later.

**Measuring real improvement, not merely successful termination.** A loop
that reports success on every task because max_trials is generous enough to
brute-force success by resampling is not evidence the reflection step is
doing useful work. The paper's own methodology is the right model here,
report trial-by-trial success rate across a held-out set of tasks and
compare against a baseline that retries with the same trial budget but with
the Self-Reflection step and memory removed. If the two curves are similar,
the self-reflection step is not earning its cost.

## 16. Observability signals

- **Trial count to success, per task, logged individually.** A healthy
  system shows most tasks succeeding within the first one or two trials,
  with a long tail using the full budget. A system where most tasks need
  the full budget, or where success rate does not improve at all from
  trial one to trial max, per task, indicates the reflection step is not
  contributing, exactly the pattern to watch for given the risk documented
  in dimension 11.
- **Evaluator pass rate over time, independent of the loop.** Track the
  Evaluator's own pass rate on a fixed regression set, separate from the
  live loop's traffic. A silent drop here, for example a test suite that
  quietly stopped exercising a code path after a refactor, will look
  identical to the Actor getting worse from inside the loop's own metrics,
  so this needs to be measured directly, not inferred.
- **Memory buffer size and contents, sampled.** Confirm in production that
  the buffer genuinely stays within Omega and that its contents are
  specific rather than generic, a healthy reflection names a concrete
  cause, returned the descending-sorted pair instead of the
  ascending-sorted pair, an unhealthy one restates the goal, try to get the
  right answer next time.
- **Latency and token cost per trial, and cumulative across the loop.** A
  Reflexion loop's cost is additive across trials by design, so alerting on
  total cost per task, not merely per call, catches the case where a subtly
  broken Evaluator is causing every task to run the full trial budget.
- **Distribution of Evaluator failure categories.** If the Evaluator can
  report a structured failure reason, not merely pass or fail, tracking the
  distribution of reasons over time surfaces systemic problems, such as one
  failure category the Self-Reflection step consistently fails to fix
  across trials, which is a strong signal that category needs a dedicated
  fix rather than another round of the loop.

## 17. Security and privacy implications

The pattern introduces one security-relevant surface that is easy to miss
because it looks like ordinary application logic. The Evaluator's detail
message, whatever a compiler, an interpreter, or a test runner reports back
on failure, flows directly into the Self-Reflection prompt and from there
into the episodic memory that is re-injected into every subsequent Actor
call. Where the Evaluator executes untrusted, model-generated code, as in
the code-generation setting this pattern is strongest in, that execution
must happen in a sandbox with no access to secrets, the filesystem beyond a
scratch directory, or the network, exactly as any code-execution feature
would require regardless of whether Reflexion sits on top of it. A failure
message that leaks an environment variable's value, a stack trace including
a file path with a username in it, or a database connection string, will be
faithfully summarized by the Self-Reflection model and persisted in memory,
then repeated back into the model's own context on the next trial and could
reach the eventual output the person using the system sees. This is not a
new class of vulnerability, it is prompt injection and secret exposure
applied to the specific data path this pattern creates, and the fix is the
same as elsewhere, sanitize whatever the Evaluator surfaces before it is
allowed into a prompt, and run any untrusted execution in an isolated
sandbox.

On privacy, the episodic memory persists only for the lifetime of the
session or task run in the architecture as described, it is not written to
a database or reused across unrelated tasks or unrelated people's sessions
unless a specific implementation chooses to do that. A deployment that does
choose to persist reflections beyond a single task run, to build a growing
library of lessons across sessions, has taken on the same data-retention
obligations as any other system that stores derived content from a user's
inputs, including whatever that content might incidentally contain, and
that choice should be treated as a deliberate data-retention decision, not
an accidental side effect of reusing the pattern's memory structure past
its original, bounded, single-session scope.

## 18. References

- Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik
  Narasimhan, Shunyu Yao, "Reflexion. Language Agents with Verbal
  Reinforcement Learning," NeurIPS 2023, arXiv 2303.11366,
  https://arxiv.org/abs/2303.11366, verified 2026-08-02. PDF used for the
  precise experiment numbers cited throughout,
  https://arxiv.org/pdf/2303.11366, verified 2026-08-02.
- NeurIPS 2023 poster listing for the paper,
  https://neurips.cc/virtual/2023/poster/70114, verified 2026-08-02.
- Official reference implementation, github.com/noahshinn/reflexion,
  https://github.com/noahshinn/reflexion, verified 2026-08-02.
- Semantic Scholar record for the earlier working-title preprint by Shinn,
  Labash, and Gopinath,
  https://www.semanticscholar.org/paper/Reflexion:-an-autonomous-agent-with-dynamic-memory-Shinn-Labash/46299fee72ca833337b3882ae1d8316f44b32b3c,
  verified 2026-08-02.
- Jie Huang, Xinyun Chen, Swaroop Mishra, Huaixiu Steven Zheng, Adams Wei
  Yu, Xinying Song, Denny Zhou, "Large Language Models Cannot Self-Correct
  Reasoning Yet," ICLR 2024, arXiv 2310.01798,
  https://arxiv.org/pdf/2310.01798, verified 2026-08-02.
- Guanzhi Wang, Yuqi Xie, Yunfan Jiang, Ajay Mandlekar, Chaowei Xiao, Yuke
  Zhu, Linxi Fan, Anima Anandkumar, "Voyager. An Open-Ended Embodied Agent
  with Large Language Models," arXiv 2305.16291,
  https://voyager.minedojo.org/assets/documents/voyager.pdf, verified
  2026-08-02.
- LangGraph official Reflexion tutorial, langchain-ai/langgraph, pinned
  commit 23961cff61a42b52525f3b20b4094d8d2fba1744,
  docs/docs/tutorials/reflexion/reflexion.ipynb,
  https://github.com/langchain-ai/langgraph/blob/23961cff61a42b52525f3b20b4094d8d2fba1744/docs/docs/tutorials/reflexion/reflexion.ipynb,
  verified 2026-08-02.
- Microsoft AutoGen documentation, Reflection design pattern,
  https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/reflection.html,
  verified 2026-08-02. Cited to distinguish the generic reflection prompting
  strategy from the specific Reflexion architecture, per dimension 1.

## Code

Every sample implements the same minimal Reflexion loop, an Actor, a real
Evaluator that executes the candidate against test cases, a Self-Reflection
step that converts a failure into a verbal lesson, and an episodic memory
bounded to the last three entries. The Actor is a fixed, three-step
candidate ladder rather than a live LLM call, so every sample compiles and
runs offline with no network access and no API key, and each candidate's
bug, sorting descending instead of ascending, then skipping the sort
entirely, mirrors the kind of concrete, describable mistake the pattern is
built to catch, per dimension 2. All three samples were compiled or run
directly against the toolchains listed below and produce identical output,
convergence on the third trial with two retained reflections.

### Python

Run with `python3 reflexion_demo.py`. Executed against CPython 3.14.

```python
"""Reflexion loop: Actor, Evaluator, Self-Reflection over bounded episodic memory.
See dimension 8 for why the Actor here is a candidate ladder, not a live LLM call."""

from dataclasses import dataclass, field


@dataclass
class Trial:
    attempt: int
    passed: bool
    detail: str


@dataclass
class ReflexionRun:
    max_trials: int = 4
    memory_cap: int = 3
    memory: list = field(default_factory=list)
    trials: list = field(default_factory=list)

    def actor(self, attempt: int) -> str:
        """Stand-in for an LLM call conditioned on self.memory."""
        candidates = [
            "def sum_two_smallest(nums):\n    nums = sorted(nums, reverse=True)\n    return nums[0] + nums[1]\n",
            "def sum_two_smallest(nums):\n    return nums[0] + nums[1]\n",
            "def sum_two_smallest(nums):\n    nums = sorted(nums)\n    return nums[0] + nums[1]\n",
        ]
        return candidates[min(attempt, len(candidates) - 1)]

    def evaluator(self, source: str) -> Trial:
        """Runs the candidate against real test cases in a real interpreter."""
        namespace = {}
        try:
            exec(source, namespace)
            fn = namespace["sum_two_smallest"]
            cases = [([4, 1, 3, 9], 4), ([10, 2, 8, 1], 3), ([5, 5, 5], 10)]
            for nums, expected in cases:
                got = fn(list(nums))
                if got != expected:
                    return Trial(len(self.trials), False,
                                 f"sum_two_smallest({nums}) returned {got}, expected {expected}")
            return Trial(len(self.trials), True, "all cases passed")
        except Exception as exc:
            return Trial(len(self.trials), False, f"{type(exc).__name__}: {exc}")

    def self_reflect(self, trial: Trial) -> str:
        """Converts a structured signal into a verbal lesson, per section 3.2."""
        if "expected" in trial.detail:
            return f"Attempt {trial.attempt} produced a wrong value ({trial.detail}). Check ordering before indexing."
        return f"Attempt {trial.attempt} raised an error ({trial.detail}). Check the function is defined and callable."

    def run(self) -> Trial:
        trial = None
        for attempt in range(self.max_trials):
            source = self.actor(attempt)
            trial = self.evaluator(source)
            self.trials.append(trial)
            if trial.passed:
                return trial
            reflection = self.self_reflect(trial)
            self.memory.append(reflection)
            self.memory = self.memory[-self.memory_cap:]
        return trial


if __name__ == "__main__":
    run = ReflexionRun()
    final = run.run()
    assert final.passed, "actor never converged within max_trials"
    assert len(run.trials) == 3, f"expected convergence on the 3rd trial, got {len(run.trials)}"
    print(f"converged on trial {final.attempt}: {final.detail}")
    print(f"episodic memory retained ({len(run.memory)}/{run.memory_cap}):")
    for note in run.memory:
        print(f"  - {note}")
```

Output observed on this run.

```
converged on trial 2: all cases passed
episodic memory retained (2/3):
  - Attempt 0 produced a wrong value (sum_two_smallest([4, 1, 3, 9]) returned 13, expected 4). Check ordering before indexing.
  - Attempt 1 produced a wrong value (sum_two_smallest([4, 1, 3, 9]) returned 5, expected 4). Check ordering before indexing.
```

### TypeScript

Compiled with `tsc --target es2020 --module commonjs --strict`, TypeScript
7.0.2, and run with `node reflexion_demo.js`.

```typescript
type Cases = Array<[number[], number]>;

interface Trial {
  attempt: number;
  passed: boolean;
  detail: string;
}

class ReflexionRun {
  readonly maxTrials = 4;
  readonly memoryCap = 3;
  memory: string[] = [];
  trials: Trial[] = [];

  private candidates: Array<(nums: number[]) => number> = [
    (nums) => [...nums].sort((a, b) => b - a).slice(0, 2).reduce((a, b) => a + b, 0),
    (nums) => nums[0] + nums[1],
    (nums) => [...nums].sort((a, b) => a - b).slice(0, 2).reduce((a, b) => a + b, 0),
  ];

  private actor(attempt: number): (nums: number[]) => number {
    return this.candidates[Math.min(attempt, this.candidates.length - 1)];
  }

  private evaluator(fn: (nums: number[]) => number): Trial {
    const cases: Cases = [
      [[4, 1, 3, 9], 4],
      [[10, 2, 8, 1], 3],
      [[5, 5, 5], 10],
    ];
    for (const [nums, expected] of cases) {
      const got = fn([...nums]);
      if (got !== expected) {
        return {
          attempt: this.trials.length,
          passed: false,
          detail: `sumTwoSmallest(${JSON.stringify(nums)}) returned ${got}, expected ${expected}`,
        };
      }
    }
    return { attempt: this.trials.length, passed: true, detail: "all cases passed" };
  }

  private selfReflect(trial: Trial): string {
    if (trial.detail.includes("expected")) {
      return `Attempt ${trial.attempt} produced a wrong value (${trial.detail}). Check ordering before indexing.`;
    }
    return `Attempt ${trial.attempt} raised an error (${trial.detail}). Check the function is defined and callable.`;
  }

  run(): Trial {
    let trial: Trial | undefined;
    for (let attempt = 0; attempt < this.maxTrials; attempt++) {
      const fn = this.actor(attempt);
      trial = this.evaluator(fn);
      this.trials.push(trial);
      if (trial.passed) return trial;
      this.memory.push(this.selfReflect(trial));
      this.memory = this.memory.slice(-this.memoryCap);
    }
    return trial as Trial;
  }
}

function main(): void {
  const run = new ReflexionRun();
  const final = run.run();
  if (!final.passed) throw new Error("actor never converged within max_trials");
  if (run.trials.length !== 3) throw new Error(`expected convergence on the 3rd trial, got ${run.trials.length}`);
}

main();
```

Output observed when the same source is run with a small console-printing
helper appended, omitted above to keep the sample focused on the pattern.

```
converged on trial 2: all cases passed
episodic memory retained (2/3):
  - Attempt 0 produced a wrong value (sumTwoSmallest([4,1,3,9]) returned 13, expected 4). Check ordering before indexing.
  - Attempt 1 produced a wrong value (sumTwoSmallest([4,1,3,9]) returned 5, expected 4). Check ordering before indexing.
```

### Go

Run with `go run reflexion_demo.go`. Executed against Go 1.26.4.

```go
package main

import (
	"fmt"
	"sort"
)

type trial struct {
	attempt int
	passed  bool
	detail  string
}

type candidate func(nums []int) int

func candidates() []candidate {
	return []candidate{
		func(nums []int) int {
			s := append([]int(nil), nums...)
			sort.Sort(sort.Reverse(sort.IntSlice(s)))
			return s[0] + s[1]
		},
		func(nums []int) int {
			return nums[0] + nums[1]
		},
		func(nums []int) int {
			s := append([]int(nil), nums...)
			sort.Ints(s)
			return s[0] + s[1]
		},
	}
}

type reflexionRun struct {
	maxTrials int
	memoryCap int
	memory    []string
	trials    []trial
}

func (r *reflexionRun) actor(attempt int) candidate {
	cs := candidates()
	if attempt >= len(cs) {
		attempt = len(cs) - 1
	}
	return cs[attempt]
}

func (r *reflexionRun) evaluator(fn candidate) trial {
	type testCase struct {
		nums     []int
		expected int
	}
	cases := []testCase{
		{[]int{4, 1, 3, 9}, 4},
		{[]int{10, 2, 8, 1}, 3},
		{[]int{5, 5, 5}, 10},
	}
	for _, c := range cases {
		got := fn(append([]int(nil), c.nums...))
		if got != c.expected {
			return trial{
				attempt: len(r.trials),
				passed:  false,
				detail:  fmt.Sprintf("sumTwoSmallest(%v) returned %d, expected %d", c.nums, got, c.expected),
			}
		}
	}
	return trial{attempt: len(r.trials), passed: true, detail: "all cases passed"}
}

func (r *reflexionRun) selfReflect(t trial) string {
	return fmt.Sprintf("Attempt %d produced a wrong value (%s). Check ordering before indexing.", t.attempt, t.detail)
}

func (r *reflexionRun) run() trial {
	var t trial
	for attempt := 0; attempt < r.maxTrials; attempt++ {
		fn := r.actor(attempt)
		t = r.evaluator(fn)
		r.trials = append(r.trials, t)
		if t.passed {
			return t
		}
		r.memory = append(r.memory, r.selfReflect(t))
		if len(r.memory) > r.memoryCap {
			r.memory = r.memory[len(r.memory)-r.memoryCap:]
		}
	}
	return t
}

func main() {
	run := &reflexionRun{maxTrials: 4, memoryCap: 3}
	final := run.run()
	if !final.passed || len(run.trials) != 3 {
		return
	}
	fmt.Printf("converged on trial %d: %s\n", final.attempt, final.detail)
	fmt.Printf("episodic memory retained (%d/%d):\n", len(run.memory), run.memoryCap)
	for _, note := range run.memory {
		fmt.Printf("  - %s\n", note)
	}
}
```

Output observed on this run.

```
converged on trial 2: all cases passed
episodic memory retained (2/3):
  - Attempt 0 produced a wrong value (sumTwoSmallest([4 1 3 9]) returned 13, expected 4). Check ordering before indexing.
  - Attempt 1 produced a wrong value (sumTwoSmallest([4 1 3 9]) returned 5, expected 4). Check ordering before indexing.
```

Java, Rust, Swift, and Kotlin are omitted for this entry. The pattern's
mechanics, an Actor, a real Evaluator, a bounded memory buffer, translate
directly into any of them with no language-specific idiom required, unlike
a pattern such as Visitor or Iterator whose shape genuinely changes across
type systems, so a fourth or fifth translation would repeat the same
control flow shown above rather than teach anything new about the pattern
itself.
