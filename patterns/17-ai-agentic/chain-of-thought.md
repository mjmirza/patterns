---
name: Chain of Thought
slug: chain-of-thought
family: 17-ai-agentic
category: Reasoning
aliases: [CoT, CoT Prompting, Step-by-Step Reasoning, Zero-Shot CoT, Manual CoT]
first_described: "Wei, Wang, Schuurmans, Bosma, Ichter, Xia, Chi, Le, Zhou 2022"
maturity: canonical
related: [react-prompting, tree-of-thoughts, reflexion, prompt-chaining, self-consistency, least-to-most-prompting, plan-and-execute]
incompatible_with: []
verified: 2026-08-02
---

# Chain of Thought

## 1. Name, aliases, and lineage

The canonical name is Chain of Thought, almost always shortened to CoT. It was
named and demonstrated by Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten
Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc Le, and Denny Zhou in "Chain-of-Thought
Prompting Elicits Reasoning in Large Language Models," arXiv 2201.11903, first
posted January 28 2022 and revised through January 10 2023. The paper's core
claim is that prompting a language model to produce a series of intermediate
reasoning steps before its final answer measurably improves its performance on
arithmetic, commonsense, and symbolic reasoning tasks, and that a 540 billion
parameter model reached state of the art on the GSM8K math benchmark using
only eight example chains in the prompt, a result the authors describe as
surpassing even a finetuned GPT-3 with a verifier.

Two aliases mark two distinct variants that the field treats almost as separate
techniques even though both carry the name chain of thought.

- **Manual CoT, or few-shot CoT.** The original Wei et al. form. The prompt
  contains a small number of worked examples, each showing a question followed
  by a written reasoning chain and then the answer. The model imitates the
  shape of the demonstrations on the new question.
- **Zero-Shot CoT.** Introduced by Takeshi Kojima, Shixiang Shane Gu, Machel
  Reid, Yutaka Matsuo, and Yusuke Iwasawa in "Large Language Models are
  Zero-Shot Reasoners," arXiv 2205.11916, accepted at NeurIPS 2022. The paper
  shows that appending the phrase "Let's think step by step" to a question,
  with no worked examples at all, produces large gains on the same class of
  benchmark, moving MultiArith accuracy from 17.7 percent to 78.7 percent and
  GSM8K from 10.4 percent to 40.7 percent on InstructGPT (text-davinci-002).
  The authors frame this as evidence that the reasoning capacity was already
  present in the model as a basic zero-shot ability that prior benchmarks had
  not exercised directly, reachable through the right instruction rather than
  through worked demonstrations.

A third naming thread runs through the reasoning-model generation of 2024
onward, where the chain of thought is no longer something a prompt author
writes into the input. It is something the model generates on its own, at
inference time, as a distinct phase before the final answer. OpenAI names this
capability inside o1 and its successors. Anthropic names it "extended
thinking" and later "adaptive thinking" inside Claude, with the reasoning
content returned as separate thinking blocks in the API response (Anthropic,
"Extended thinking," https://platform.claude.com/docs/en/build-with-claude/extended-thinking,
verified 2026-08-02). These are the same underlying idea, a sequence of
intermediate tokens the model produces before committing to an answer, but the
mechanism that produces the chain has moved from prompt engineering to
training and decoding, which the dynamics and variants sections below treat as
a distinct implementation family rather than a different pattern.

## 2. Problem and context

A large language model predicts its next token from everything that came
before it in the same context. When a question demands several dependent
steps of arithmetic, logic, or lookup, and the model is asked to produce only
the final answer, it must arrive at that answer with no scratch space of its
own. Every intermediate quantity the correct solution depends on has to be
held inside the model's internal computation for that single forward pass,
with no chance to write anything down and reread it. On a two-step word
problem this rarely matters. On a problem with four or five dependent steps,
Wei et al. document that this direct-answer approach performs poorly even at
very large model scale, and that the failure is not fixed by making the model
bigger. It is fixed by changing what the model is asked to output.

The context that creates the need is therefore precise. A task decomposes
into a sequence of intermediate steps where each step's correct value depends
on the step before it, the final answer is sensitive to getting every
intermediate step right, and the task is expressed in natural language or in
a domain, such as elementary arithmetic, that the model has seen expressed as
worked reasoning during training. Chain of Thought exploits the fact that
generating text is autoregressive. Once the model has emitted "there are 3
groups of 4," that string is now part of its own context for predicting the
next token, so it becomes available as a value to condition on for the rest
of generation, in a way that an internal, un-externalized intermediate
computation inside the network cannot be. The pattern converts multi-step
latent computation into multi-step visible computation, which the model can
then condition on step by step.

The 2022 papers ground this in classic reasoning tasks, arithmetic word
problems, commonsense reasoning, and symbolic manipulation such as last-letter
concatenation. By 2024 and 2025 the same underlying need reappears inside
agentic systems, where a single LLM call must plan a multi-step tool-use
sequence, debug a failing test, or reconcile conflicting retrieved documents
before answering. The problem context is identical. a task with dependent
intermediate steps and a payoff for getting each one right before committing
to output.

## 3. Forces

Most of the accuracy and cost claims below are sourced to the cited papers.
The favoured-versus-sacrificed framing itself is engineering judgement about
which side of each trade a typical production deployment lands on.

- **Accuracy on multi-step tasks.** Favoured, strongly, and this is the whole
  reason the pattern exists. The improvement over direct answering grows with
  the number of reasoning steps the task requires, and shrinks toward zero on
  single-step tasks, per Wei et al.'s own ablations across model scale.
- **Latency and cost.** Sacrificed. Every token of reasoning is a token the
  model must generate and, on a hosted API, a token that is billed. Anthropic's
  extended thinking documentation states that thinking tokens count against
  the same `max_tokens` budget as the final answer, and that higher thinking
  budgets trade latency for quality with diminishing returns, recommending
  32,000 tokens or more only be pushed through batch processing because
  synchronous requests risk timing out.
- **Interpretability versus faithfulness.** A visible chain looks like an
  explanation, but Miles Turpin, Julian Michael, Ethan Perez, and Samuel R.
  Bowman show in "Language Models Don't Always Say What They Think.
  Unfaithful Explanations in Chain-of-Thought Prompting," arXiv 2305.04388,
  that the text of the chain can systematically misrepresent the actual cause
  of the model's answer. Introducing a biasing feature into the input, such as
  reordering multiple-choice options so the correct answer is always A, drove
  accuracy down by up to 36 percentage points on GPT-3.5 and Claude 1.0 while
  the generated chain never mentioned the reordering and instead constructed a
  plausible-sounding justification for the biased answer. So the force is not
  simply interpretability gained. it is interpretability that looks earned but
  is not guaranteed to be.
- **Model scale dependence.** Sacrificed at small scale. Wei et al. report the
  benefit is an emergent property that appears reliably only above roughly 100
  billion parameters on the models they tested, and that chain of thought
  prompting can actively hurt small models, which sometimes produce a
  plausible-looking chain that arrives at a wrong answer more often than a
  direct answer would.
- **Prompt length and demonstration cost.** Sacrificed for manual CoT, absent
  for zero-shot CoT. Few-shot CoT prompts must include full worked examples,
  which consumes context and requires someone to write correct exemplar
  reasoning for the task. Zero-shot CoT removes that authoring cost entirely
  at some accuracy cost relative to well-written manual exemplars, per
  Kojima et al.'s own comparison table.
- **Determinism and reproducibility.** Sacrificed further. A generated chain
  at nonzero temperature can reach the same correct answer through different
  reasoning paths on different calls, or the same wrong path repeatedly if the
  chain wanders into a bad state early and every following token conditions
  on that mistake.

No force here is free. The pattern buys measurable multi-step accuracy at the
direct cost of tokens, latency, and a chain whose surface text is not a
reliable causal account of the model's actual computation.

## 4. Applicability and non-applicability

Reach for Chain of Thought when the following hold.

- The task requires two or more dependent intermediate steps where an error
  in an early step propagates into every step that follows, such as multi-step
  arithmetic, multi-hop question answering, or a debugging task that needs a
  hypothesis followed by a check.
- The model is large enough for the emergent benefit to appear. Wei et al.
  found gains were unreliable below roughly 100 billion parameters and could
  reverse below that threshold.
- The output benefits from an intermediate, checkable representation, for
  example a plan that a downstream tool call, verifier, or human reviewer can
  inspect before the final action is taken.
- The task domain resembles something the model has seen expressed as written
  reasoning during pretraining, arithmetic, logic puzzles, code tracing,
  natural-language deduction. The pattern relies on the model's learned
  distribution over reasoning-shaped text.

Do NOT reach for Chain of Thought in these cases, and the reason for each one
matters more than the rule.

- **The task is a single retrieval or a single classification with no
  dependent steps.** Kojima et al.'s own zero-shot results show CoT prompting
  can add nothing, or a small negative effect from off-topic rambling, on
  tasks that were already answerable directly. Asking "what is the capital of
  France" to think step by step adds tokens and cost for zero gain.
- **The answer must be provably correct and auditable, not merely plausible.**
  The unfaithfulness finding in dimension 3 means a chain that reads as
  correct reasoning is not evidence the answer is correct by that reasoning.
  Where correctness must be guaranteed, pair the pattern with an external
  verifier or a symbolic tool, see PAL in dimension 8, rather than trusting
  the chain's own text as proof.
- **The model is small, distilled, or specifically not trained to produce
  long-form reasoning.** Below the scale threshold, or on a model
  instruction-tuned narrowly for short structured output, appending "think
  step by step" degrades format compliance without buying accuracy, and can
  break a downstream JSON parser expecting a terse answer.
- **Latency budget is hard and small, such as an autocomplete suggestion or a
  real-time voice turn.** Every additional reasoning token adds generation
  time before the first useful output token. A synchronous low-latency
  surface cannot absorb this, and Anthropic recommends batch processing
  rather than synchronous calls once a thinking budget exceeds 32,000 tokens
  for this reason.
- **The reasoning would expose private, proprietary, or safety-sensitive
  intermediate content that must never reach the end user or a downstream
  log.** See dimension 17. A chain that reasons about a user's medical or
  financial details in visible text is a different disclosure surface than a
  final answer alone.
- **You need to explore multiple candidate solution paths and choose the
  best, rather than commit to one linear path.** That need is Tree of
  Thoughts, not Chain of Thought, see dimension 13. A single chain commits
  early and cannot backtrack once a wrong branch has been taken.
- **The task needs the model to act on the external world between reasoning
  steps, not only reason internally.** That need is ReAct, which interleaves
  chain-of-thought-style reasoning with tool calls and observations rather
  than producing one uninterrupted chain, see dimension 13.

## 5. Structure

Chain of Thought has an unusually flat structure compared to a software
design pattern with named classes, because it is a prompting and decoding
technique rather than an object graph. The participants are still worth
naming precisely, because getting them confused is the source of most misuse.

- **Prompt or instruction.** The input that requests reasoning. In manual CoT
  this is a set of few-shot exemplars, each a question, a written reasoning
  chain, and an answer. In zero-shot CoT this is a single trigger phrase such
  as "Let's think step by step," appended to the question with no exemplars.
  In an inference-time reasoning model the prompt for the reasoning behaviour
  is not user-supplied at all. it is baked into the model's training through
  reinforcement learning, and the user's input is simply the question.
- **Reasoning chain.** The sequence of intermediate natural-language steps the
  model generates before its final answer. In the API-exposed forms
  (Anthropic's thinking blocks, o1's hidden chain) this is a structurally
  distinct span of the response, separated from the final answer, sometimes
  by an explicit block type and sometimes by a delimiter convention such as
  the phrase "Therefore, the answer is."
- **Final answer extraction.** The step, whether a regular expression, a
  structured output schema, or a human reading the last line, that pulls the
  committed answer out of the chain. This participant is easy to overlook and
  is a common source of evaluation bugs, since a correct chain with a
  malformed final line will be scored wrong even though the reasoning worked.
- **Consumer.** Whatever reads the final answer, or in agentic uses, whatever
  reads the reasoning chain itself to decide a next action, such as a
  human-in-the-loop reviewer inspecting the chain before approving an
  automated decision, or a downstream tool-selection step in a ReAct-style
  loop.

## 6. ASCII structure diagram

```
  Few-shot / manual CoT                Zero-shot CoT
  +-----------------------+            +-----------------------+
  | Exemplar 1: Q + chain |            | Question              |
  | Exemplar 2: Q + chain |            | + "Let's think step   |
  | New question          |            |   by step"            |
  +-----------------------+            +-----------------------+
              |                                    |
              v                                    v
        +--------------------------------------------------+
        |              Language model, single call          |
        |------------------------------------------------- |
        |  generates: reasoning chain (visible tokens)      |
        |  generates: final answer   (visible tokens)       |
        +--------------------------------------------------+
              |                                    |
              v                                    v
     +------------------+                +------------------+
     | Answer extractor  |                | Consumer / user  |
     | (regex / schema)  |                | reads chain and  |
     +------------------+                | final answer     |
                                          +------------------+

  Inference-time reasoning model (o1-class, adaptive thinking)
        +---------------------------------------------------+
        |              Language model, single call           |
        |----------------------------------------------------|
        |  hidden/summarized "thinking" phase (RL-trained,    |
        |  not exemplar-driven, may be redacted or summarized)|
        |  final answer phase (the only part shown by default)|
        +---------------------------------------------------+
```

## 7. Dynamics

The three variants share one dynamic principle and differ in when and how the
reasoning phase is triggered and surfaced.

```
Manual / zero-shot CoT, one API call

Caller               Model
  |                    |
  |-- prompt --------->|
  |    (exemplars or   |
  |     trigger phrase)|
  |                    |-- autoregressively emits reasoning
  |                    |   token 1, conditions on it
  |                    |-- emits reasoning token 2, conditions
  |                    |   on tokens 1 and 2
  |                    |    ... (each step visible in context,
  |                    |         each following token can
  |                    |         attend to every prior step)
  |                    |-- emits "Therefore, the answer is X"
  |<-- full response ---|
  |    (chain + answer) |
  |
  |-- extract final answer from response text


Inference-time reasoning model (Claude adaptive thinking, o1-class)

Caller               Model
  |                    |
  |-- prompt --------->|
  |    (plain question,|
  |     no CoT trigger  |
  |     needed)          |
  |                    |-- internal "thinking" phase. model
  |                    |   generates and conditions on its own
  |                    |   intermediate tokens the same way,
  |                    |   but this phase is trained via RL to
  |                    |   appear (or not) and to run for a
  |                    |   length the model itself decides,
  |                    |   bounded by an effort or budget setting
  |                    |-- transition to final-answer phase
  |<-- response --------|
  |    (thinking block, |
  |     usually redacted|
  |     or summarized,   |
  |     plus final text) |
  |
  |-- if thinking is visible, treat it as diagnostic only,
  |   never as the load-bearing explanation, see dim. 17
```

The dynamic worth stating plainly is the same one that makes the pattern work
at all. every token the model emits during the reasoning phase becomes part of
the context window for every following token, so the chain is not commentary
generated after the fact. It is genuinely part of the computation, because the
model's next prediction is conditioned on it. This is why Zero-Shot CoT's
single trigger phrase works with no worked examples. it does not teach new
knowledge, it changes what shape of output the model commits to first, which
then constrains and informs everything that follows in the same forward pass.

## 8. Implementation variants

**Few-shot manual CoT.** The original form. Two to eight exemplars, each a
full worked example, written by a human or curated from a dataset. Highest
accuracy per Wei et al.'s ablations when exemplars are well chosen, at the
cost of prompt length and authoring effort. Exemplar selection matters. poorly
matched or too-simple exemplars transfer poorly to a harder test question.

**Zero-Shot CoT.** Kojima et al.'s two-stage prompt. First append "Let's
think step by step" and let the model generate the chain. Then, in a second
call, feed the chain back with a phrase such as "Therefore, the answer is"
to extract a clean final answer. The two-call structure exists because the
raw chain-plus-trigger output often does not end in an easily parsed answer
format, so extraction is treated as its own step rather than folded into the
first generation.

**Self-consistency decoding.** Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc
Le, Ed Chi, Sharan Narang, Aakanksha Chowdhery, and Denny Zhou's "Self-
Consistency Improves Chain of Thought Reasoning in Language Models,"
arXiv 2203.11171, samples several independent reasoning chains at nonzero
temperature for the same question, then takes the majority answer across
chains rather than trusting any single greedy chain. The paper reports gains
of plus 17.9 points on GSM8K, plus 11.0 on SVAMP, plus 12.2 on AQuA, plus 6.4
on StrategyQA, and plus 3.9 on ARC-challenge over greedy single-chain
decoding. This variant trades one call for N calls, and the majority vote
gives partial protection against a single chain wandering into an early
error, since independent samples are less likely to make the identical
mistake.

**Least-to-Most Prompting.** Denny Zhou, Nathanael Schärli, Le Hou, Jason Wei,
Nathan Scales, Xuezhi Wang, Dale Schuurmans, Claire Cui, Olivier Bousquet,
Quoc Le, and Ed Chi's "Least-to-Most Prompting Enables Complex Reasoning in
Large Language Models," arXiv 2205.10625, addresses a documented weakness of
plain CoT. it "tends to perform poorly on tasks which requires solving
problems harder than the exemplars shown in the prompts," in the authors'
own words. The fix decomposes the problem into an explicit sequence of
strictly easier subproblems first, then solves them in order, each answer
feeding the next prompt. On the SCAN compositional-generalization benchmark
this raised accuracy from 16 percent with plain CoT to 99 percent.

**Program-Aided Language models, PAL.** Luyu Gao, Aman Madaan, Shuyan Zhou,
Uri Alon, Pengfei Liu, Yiming Yang, Jamie Callan, and Graham Neubig's "PAL.
Program-aided Language Models," arXiv 2211.10435, keeps the chain-of-thought
decomposition step but replaces the arithmetic execution step with generated
code run by a real interpreter, since the paper found language models
"frequently err" doing the actual arithmetic even when the decomposition is
correct. Using Codex with PAL beat PaLM-540B's plain chain-of-thought
performance on GSM8K by 15 absolute points. This is the pattern's answer to
the faithfulness and correctness weaknesses in dimension 4. delegate the
computation, keep the model for the decomposition.

**Inference-time chain generation, RL-trained.** The 2024 to 2026 reasoning-
model family, OpenAI's o1 and successors and Anthropic's extended and
adaptive thinking, moves the chain-triggering decision out of the prompt
entirely. DeepSeek-AI's "DeepSeek-R1. Incentivizing Reasoning Capability in
LLMs via Reinforcement Learning," arXiv 2501.12948, demonstrates that this
capacity can be brought out through pure reinforcement learning, with no need
for human-labeled reasoning trajectories, and that models trained this way
develop self-reflection, verification, and adaptive strategy adjustment
inside their own chains without ever being shown a worked human exemplar.
Anthropic's implementation exposes a `budget_tokens` control in manual mode,
or an `effort` level in adaptive mode, rather than a prompt trigger, and the
model decides on each request whether to think at all under adaptive mode.
This is Chain of Thought as a trained model capability rather than a
prompting technique, and it is why current practice increasingly treats "add
a CoT trigger phrase" as unnecessary on a reasoning-tuned model, sometimes
even counterproductive, since the model already reasons by default and an
extra instruction can conflict with its trained decision of when to stop
thinking.

**Structured or schema-constrained CoT.** The reasoning chain is emitted into
a structured field, for example a `reasoning` key in a JSON object separate
from an `answer` key, so a downstream parser can display, log, or discard
the chain independently of the final answer without regex extraction. Common
in production agent frameworks that need the chain for debugging but must
return a clean typed answer to the calling system.

## 9. Known production uses

**Anthropic Claude, extended and adaptive thinking.** Anthropic's Messages API
exposes a `thinking` parameter that, when enabled, returns the model's
reasoning as distinct thinking content blocks separate from the final text
response, with a documented token budget and, on models supporting adaptive
mode, an `effort` setting controlling how much the model reasons before
answering. Anthropic, "Extended thinking,"
https://platform.claude.com/docs/en/build-with-claude/extended-thinking,
verified 2026-08-02.

**OpenAI o1.** OpenAI's o1 model is trained to spend time thinking before it
answers, per OpenAI's own description as summarized on its Wikipedia entry,
and the company deliberately hides the raw chain of thought from end users by
design, forbidding attempts to reveal it, citing both safety and competitive
reasons. OpenAI additionally reports a correlation between accuracy and the
logarithm of the amount of compute spent thinking before answering, meaning
more reasoning tokens reliably improve accuracy with diminishing returns
rather than a linear relationship. Wikipedia contributors, "OpenAI o1,"
https://en.wikipedia.org/wiki/OpenAI_o1, quoting OpenAI's own materials,
verified 2026-08-02.

**DeepSeek-R1.** DeepSeek-AI's R1 model was trained with pure reinforcement
learning to produce extended chains of thought with no supervised
human-written reasoning demonstrations, and the paper reports the resulting
reasoning patterns, including self-reflection and answer verification inside
the chain, transfer successfully when distilled into smaller models.
DeepSeek-AI et al., "DeepSeek-R1. Incentivizing Reasoning Capability in LLMs
via Reinforcement Learning," arXiv 2501.12948, verified 2026-08-02.

**Google, chain-of-thought prompting evaluated on GSM8K with PaLM.** The
foundational Wei et al. paper itself is a production-scale result, not only
an academic one. it evaluates chain-of-thought prompting directly on Google's
then-largest PaLM model at 540 billion parameters and reports it reaching
state-of-the-art accuracy on the GSM8K grade-school math benchmark using only
eight in-context exemplars, described by the authors as exceeding even a
GPT-3 model finetuned specifically for the task with an added verifier. Wei,
Wang, Schuurmans, Bosma, Ichter, Xia, Chi, Le, Zhou, arXiv 2201.11903,
verified 2026-08-02.

## 10. Consequences

The gains and costs listed here are sourced to the cited papers. Judging one
weakness as more damaging than another for a given deployment is engineering
judgement.

Positive.

- Measurably higher accuracy on multi-step arithmetic, commonsense, and
  symbolic tasks, with the effect growing as the number of required steps
  grows, per Wei et al.'s scaling curves across problem difficulty.
- Zero authoring cost to obtain the benefit in the zero-shot variant. a single
  fixed trigger phrase works across a wide range of tasks with no exemplar
  curation, per Kojima et al.
- Produces an inspectable intermediate artifact that a human reviewer, a
  downstream verifier, or a debugging session can read, which is not
  available from a single direct-answer generation.
- Composes cleanly with sampling-based ensembling, self-consistency, and with
  external computation, PAL, to correct for the two weaknesses, unreliability
  of a single chain and unreliability of model-internal arithmetic,
  respectively.
- In the RL-trained inference-time form, the behaviour transfers to smaller
  distilled models, per DeepSeek-R1's own distillation results, so the cost
  of developing the reasoning capability does not have to be repeated per
  model size.

Negative.

- The generated chain is not a guaranteed faithful account of the actual
  computation. Turpin et al. demonstrate the model can construct a plausible
  chain that rationalizes a biased answer while never mentioning the actual
  biasing factor, which means treating chain text as proof of correct
  reasoning is unsound.
- Token cost and latency both increase, sometimes a great deal. On
  Anthropic's platform this is explicit and billed, with thinking tokens
  reported in `usage.output_tokens_details.thinking_tokens` and counted
  against the same output budget as the final answer.
- The benefit does not appear reliably below a scale threshold, and can
  reverse below it, per Wei et al.'s own negative results on smaller models.
- A single generated chain has no backtracking. an early wrong step
  propagates through every later token, since the model conditions on its
  own prior output and cannot revise text already committed within the same
  chain.
- Hidden or redacted chains, the o1 and default Claude behaviour, remove the
  interpretability benefit for the end user entirely while keeping the
  latency and cost, trading transparency for competitive or safety reasons
  decided by the model provider rather than the application developer.

## 11. Failure modes and misuse

The causes below are documented in the cited papers. The symptoms and fixes
are drawn from production practice, engineering judgement rather than a
sourced claim.

**Snowballing early error.** Symptom. The final answer is confidently wrong,
and reading the chain shows a plausible-looking derivation built entirely on
top of one wrong number introduced two or three steps earlier. Cause. The
autoregressive dependency means every later token conditions on the earlier
mistake as if it were established fact, and the model has no mechanism inside
a single chain to notice and revert it. Fix. Use self-consistency to sample
several independent chains and take the majority answer, or move to Tree of
Thoughts if the task needs actual backtracking rather than resampling.

**Rationalized rather than reasoned answer.** Symptom. Evaluation shows
accuracy drops sharply, tens of percentage points, when an irrelevant biasing
feature is added to otherwise identical inputs, such as always placing the
correct multiple-choice answer in position A, yet the model's own chain never
mentions the bias and instead builds a confident-sounding justification for
whatever answer the bias nudged it toward. Cause. Turpin et al.'s documented
unfaithfulness. the chain is generated to be locally plausible continuation
text, not necessarily a report of the model's actual decision process. Fix.
Never treat the chain's stated reasoning as a safety or fairness audit trail
on its own. Test with controlled input perturbations for hidden sensitivity,
and pair high-stakes automated decisions with an external check that does not
rely on the model's self-report.

**Trigger phrase applied to a small or narrowly tuned model.** Symptom.
Adding "Let's think step by step" makes a small model's output longer, off
topic, or format-broken, and accuracy on the target task goes down rather
than up. Cause. The zero-shot benefit is documented as an emergent capability
that Kojima et al. and Wei et al. both observed reliably only above a scale
threshold. below it a model may not have learned the reasoning-shaped text
distribution that the trigger phrase is meant to invoke. Fix. Benchmark with
and without the trigger on the actual target model and task before adopting
it. do not assume the technique transfers down in scale.

**Reasoning trigger fighting a trained reasoning model.** Symptom. Adding an
explicit "think step by step" instruction to a model that already reasons by
default under adaptive thinking produces redundant or conflicting behaviour,
sometimes truncated or lower-quality final answers, because the model's own
trained judgement about when to stop reasoning is overridden by an
instruction it was not trained against. Cause. Confusing prompt-triggered CoT,
designed for models with no built-in reasoning phase, with inference-time
reasoning models that decide their own reasoning length via RL training. Fix.
On a documented reasoning model, control depth with the model's own exposed
mechanism, Anthropic's `effort` or `budget_tokens`, rather than a prompt
instruction, and drop manual CoT trigger phrases entirely on these models.

**Extraction failure on a well-reasoned chain.** Symptom. Automated evaluation
scores a correct chain as wrong. Cause. The final-answer extraction step,
whether a regex or a structured-output parser, does not match the format the
chain actually ended in, because the model varied its closing phrasing across
samples. Fix. Move the answer into a structured output field separate from
the reasoning field, per the schema-constrained variant in dimension 8,
rather than parsing free text.

**Sensitive intermediate content surfaced through the chain.** Symptom. A
support log, a debugging trace, or a demo recording contains reasoning text
that discusses a user's private data, an internal system prompt, or a
credential in plain unredacted form, even though the final answer to the user
was clean. Cause. The chain is a full generation and inherits whatever
context the model was given, including anything sensitive fed into the
prompt for that turn, and by default the chain is logged or displayed
alongside the final answer. Fix. Treat the reasoning chain as being at the
same sensitivity level as the input context that produced it, redact or
restrict its storage and display accordingly, and prefer a provider's
built-in summarized or redacted thinking display where privacy requires it.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Chain of Thought (single chain) | Self-Consistency | Tree of Thoughts | ReAct | PAL | Least-to-Most |
|---|---|---|---|---|---|---|
| Accuracy on multi-step tasks | Good, the baseline gain | Better, majority vote over N chains | Best on tasks needing search or lookahead | Good, plus grounded in real observations | Best on arithmetic, execution is exact | Best on tasks harder than the exemplars |
| Cost per query | One call | N independent calls, N times the tokens | Many calls, tree expansion is expensive | Multiple calls, interleaved with tool latency | One decomposition call plus one interpreter run | Multiple calls, one per subproblem |
| Backtracking on a wrong step | None, chain commits linearly | Indirect, via majority over independent attempts | Explicit, can prune and revisit branches | Indirect, via re-observing after an action | None inside the code-gen step | Indirect, later subproblems can be reattempted |
| Grounding in the real world | None, pure internal generation | None | None, pure internal generation | Strong, actions produce real observations | Strong for arithmetic, via interpreter execution | None, pure internal generation |
| Faithfulness of stated reasoning | Documented as unreliable, Turpin et al. | Same underlying unreliability per chain, mitigated only by voting | Same underlying unreliability per branch | Somewhat improved, actions are checkable independently of the stated reasoning | Improved for the computed part, since the interpreter output is verifiable | Same underlying unreliability per subproblem |
| Latency | Lowest of this group | Highest, N times single-chain latency | High, proportional to explored nodes | Medium to high, tool round trips add wall clock | Medium, one extra interpreter round trip | Medium, sequential subproblem calls |
| Best suited to | A single well-scoped multi-step reasoning task | A task where the modal answer matters more than latency | A search or planning problem with a defined goal state | A task requiring real external information mid-reasoning | Arithmetic or symbolic computation embedded in reasoning | A task harder than any single available exemplar |

## 13. Related and incompatible patterns

- **ReAct.** Builds directly on Chain of Thought. Yao et al.'s own abstract
  states ReAct overcomes issues of hallucination and error propagation
  prevalent in chain-of-thought reasoning by interleaving reasoning with
  real tool actions and observations rather than reasoning in one
  uninterrupted internal chain. Reach for ReAct instead of plain CoT whenever
  the task needs real external information partway through reasoning, not
  only internal deduction. See `react-prompting`.
- **Tree of Thoughts.** A direct generalization. Yao, Yu, Zhao, Shafran,
  Griffiths, Cao, and Narasimhan's arXiv 2305.10601 lets the model consider
  multiple different reasoning paths and self-evaluate choices, including
  backtracking, where plain Chain of Thought commits to one linear path with
  no revision. Their own comparison reports 74 percent solved on Game of 24
  versus 4 percent for plain chain-of-thought prompting with GPT-4 on the
  same task. Reach for Tree of Thoughts when the task is a search or planning
  problem where an early choice can be wrong and needs to be abandoned. See
  `tree-of-thoughts`.
- **Self-consistency.** A decoding-time extension rather than a different
  reasoning shape. It samples multiple independent Chain of Thought
  generations and takes the majority final answer, per Wang et al.,
  arXiv 2203.11171. It is not a separate pattern so much as CoT run N times
  with a vote at the end, and it composes with plain CoT rather than
  replacing it.
- **Reflexion.** A related but distinct agentic loop that uses a model's own
  generated self-critique of a past attempt, stored as verbal feedback, to
  improve a subsequent attempt at the same or a related task, rather than
  reasoning once and stopping. It shares the idea of visible intermediate
  natural-language content driving better final behaviour, but operates
  across attempts rather than within a single chain. See `reflexion`.
- **Prompt Chaining.** A structurally different pattern that composes with
  CoT rather than competing with it. Prompt Chaining decomposes a task into
  separate LLM calls with programmatic control flow between them, where each
  call's output feeds the next call's input as a discrete API-level step.
  Chain of Thought produces its intermediate steps inside one model call.
  Least-to-Most Prompting sits between the two, decomposing into subproblems
  each solved by its own prompt but coordinated as one logical task. See
  `prompt-chaining`.
- **PAL, Program-Aided Language models.** Complementary rather than
  competing. PAL keeps the CoT-style decomposition of a problem into steps
  but hands the actual arithmetic or logical execution to a real
  interpreter, directly targeting the documented weakness that language
  models compute arithmetic unreliably even when their decomposition is
  correct, per Gao et al., arXiv 2211.10435.
- **Retrieval-Augmented Generation.** Not incompatible, and frequently
  combined. Retrieved documents are commonly placed into the context before a
  CoT-style reasoning phase, so the chain can reason over grounded facts
  rather than only the model's parametric knowledge, but the two are distinct
  concerns, retrieval solves what facts are available and CoT solves how the
  model reasons with them.
- **Nothing in this family is truly incompatible with Chain of Thought,**
  because CoT describes how a single generation reasons, and the other named
  patterns mostly describe how multiple generations or actions are
  orchestrated around that reasoning. The closest thing to a conflict is
  applying a fixed manual-CoT trigger phrase to an inference-time reasoning
  model that already decides its own reasoning behaviour through training,
  documented as a genuine failure mode in dimension 11 rather than a
  structural incompatibility.

## 14. Refactoring path in and out

Introducing the pattern into a prompt or an application that does not have
it.

1. Identify a task where direct-answer prompting produces wrong answers on
   problems needing more than one dependent step. Confirm this empirically on
   a held-out set of real examples, not by assumption, since single-step
   tasks gain nothing.
2. Confirm the target model is large enough, or is documented as a reasoning
   model, for the benefit to be reliable. Run the same held-out set with and
   without a trigger phrase and compare, per the failure mode in dimension
   11.
3. Start with Zero-Shot CoT, appending "Let's think step by step" or the
   provider's documented equivalent, since it costs no authoring time and
   Kojima et al. show it recovers most of the manual-CoT benefit on their
   benchmarks.
4. Add a separate extraction step, or move to structured output with a
   distinct answer field, so the reasoning text and the committed answer are
   not conflated in downstream parsing.
5. If Zero-Shot CoT accuracy is insufficient, move to Manual CoT with two to
   eight curated exemplars matched in difficulty and format to the target
   task, since Wei et al.'s own comparisons show well-chosen exemplars
   outperform the zero-shot trigger.
6. If a single chain is still unreliable, add self-consistency, sampling
   several chains at nonzero temperature and taking the majority answer,
   accepting the N times cost increase.
7. If the task involves real arithmetic or exact computation embedded in the
   reasoning, route that sub-step through PAL-style code generation and
   execution instead of trusting the model's own arithmetic.
8. On a reasoning-tuned model that supports it, replace the prompt trigger
   entirely with the model's native thinking or reasoning-effort control,
   since the model has already been trained to decide when and how much to
   reason.

Removing the pattern when it stops earning its place. Signals include a
task that turned out to be single-step after all, a latency budget that
cannot absorb the extra tokens, or migration to a reasoning-tuned model where
the manual trigger now conflicts with the model's own trained behaviour.

1. Re-measure accuracy on the held-out set with direct answering, since the
   task, the model, or both may have changed since CoT was adopted.
2. If direct answering matches CoT accuracy within tolerance, remove the
   trigger phrase or exemplars and simplify the prompt back to a direct
   question.
3. If moving to a reasoning-tuned model, remove any manual trigger phrase and
   switch to the model's native reasoning-depth control, per step 8 above,
   rather than leaving a now-redundant instruction in the prompt.
4. Remove any answer-extraction logic that is now unnecessary once the model
   returns a direct answer with no chain to parse around.

## 15. Testing and verification

Much of this dimension is production practice rather than a sourced finding.
Where a claim traces to a paper it is cited directly.

Easier because of the pattern.

- The intermediate chain gives a human reviewer or an automated grader
  something to inspect beyond a bare final answer, which supports partial
  credit scoring and error localization, is the step before the wrong number
  identified, in a way a direct answer cannot.
- Self-consistency's majority vote gives a cheap, model-agnostic confidence
  signal for free. the agreement rate across sampled chains correlates with
  answer reliability, and Wang et al.'s own results show this correlation
  holding across the five benchmarks they tested.

Harder because of the pattern.

- A correct final answer reached via a flawed or unfaithful chain will pass a
  correctness-only test while hiding a reasoning bug that could surface
  differently on the next similar input. Testing final-answer correctness
  alone is not sufficient evidence the reasoning process is sound, per the
  Turpin et al. finding in dimension 3.
- Nondeterminism at nonzero temperature means the same test case can pass on
  one run and fail on another, since different sampled chains can reach
  different answers, complicating a simple pass or fail CI gate.
- Answer extraction is itself a piece of test infrastructure that needs its
  own tests, since a chain that reasons correctly but ends in unexpected
  phrasing will be scored wrong by a brittle regex, a false negative that has
  nothing to do with the model's actual reasoning quality.

Techniques that apply.

- **Held-out benchmark comparison, with and without CoT.** Run the actual
  target task through both a direct prompt and a CoT prompt on a fixed
  held-out set before adopting the pattern, following Wei et al.'s and
  Kojima et al.'s own methodology, rather than assuming the published gains
  transfer to a different task or model.
- **Perturbation testing for faithfulness, per Turpin et al.'s method.**
  Inject a known irrelevant biasing feature into otherwise identical inputs,
  for example reordering answer choices, and check whether the final answer
  shifts in the direction of the bias while the chain never mentions it. A
  large shift with no acknowledgment in the chain is evidence the chain is
  not a reliable audit trail for that task.
- **Majority-vote confidence thresholding.** Sample several chains at
  nonzero temperature for high-stakes answers and treat low agreement across
  samples as a signal to escalate to a human or a stronger verification
  step, rather than trusting a single greedy chain's confident tone.
- **Golden-chain regression fixtures.** For tasks where the reasoning steps
  themselves are checkable, keep a small fixed set of inputs with known
  correct intermediate steps, not only known correct final answers, and
  assert both, since a model or prompt change can preserve the final answer
  while silently degrading the intermediate reasoning quality on
  a related input.

## 16. Observability signals

This dimension is engineering judgement about what to instrument in
production. The token-accounting field names are drawn from Anthropic's own
documentation, cited above, the rest is practice.

- **Chain length in tokens, per request.** The single most direct cost
  signal, since thinking or reasoning tokens are billed the same as any
  other output token on providers that expose them, and Anthropic surfaces
  this as `usage.output_tokens_details.thinking_tokens` in the API response.
- **Chain-to-answer ratio.** How many reasoning tokens were spent per final
  answer token. A healthy instance shows this ratio scaling roughly with
  task difficulty, harder inputs produce longer chains. A ratio that is flat
  regardless of input difficulty suggests the model is not actually adapting
  its reasoning depth, or that a fixed manual trigger is forcing uniform
  chain length regardless of need.
- **Self-consistency agreement rate.** For any deployment using sampled
  multiple chains, the fraction of samples agreeing with the majority answer
  is a direct, cheap confidence proxy worth logging per request and
  aggregating over time. A dropping agreement rate on a stable task is an
  early signal of model or prompt drift.
- **Extraction failure rate.** How often the answer-extraction step fails to
  find a parseable final answer inside a well-formed chain. A healthy
  instance keeps this near zero. a rising rate points at a prompt or model
  change shifting the chain's closing phrasing, not at a reasoning quality
  problem.
- **Latency to first final-answer token, separate from total latency.** In a
  system where the reasoning phase is hidden or summarized, users still
  perceive the wait before the visible answer starts, so this is the
  user-facing latency metric even when total token generation, including the
  hidden chain, is longer.
- **Perturbation-sensitivity drift, sampled periodically.** Re-running the
  Turpin et al. style bias-injection test on a schedule against production
  traffic patterns, rather than only at initial adoption, catches faithfulness
  regressions introduced by a model version upgrade.

A healthy production instance shows chain length correlating with task
difficulty, a stable or improving self-consistency agreement rate, a near
zero extraction failure rate, and no growing gap between direct-answer and
CoT accuracy on the held-out benchmark over time. A failing instance shows
chain length flat regardless of difficulty, agreement rate declining, or
extraction failures climbing after an otherwise unrelated deployment, any of
which localizes the fault to a specific stage without needing to read
individual transcripts first.

## 17. Security and privacy implications

This dimension is largely engineering judgement drawn from the pattern's
documented behaviour, applied to security and privacy consequences rather
than sourced from a dedicated security paper on Chain of Thought itself.

**The chain inherits the sensitivity of everything in its context.** Because
the reasoning phase is a normal generation conditioned on the full prompt,
any secret, personal data, or proprietary system instruction present in the
context is available for the model to reference inside the chain, and by
default that chain is included in the response, logged, or displayed. A
support tool that feeds a user's account details into context for a CoT-style
triage decision can surface those details verbatim inside the visible
reasoning even when the final answer to the user is a clean, redacted
summary. Treat the reasoning chain as carrying the same data-classification
level as its input context, and apply the same redaction, retention, and
access controls to logged chains that apply to the raw prompts that produced
them.

**Unfaithfulness is itself a trust risk, not only a quality one.** Turpin et
al.'s finding that a chain can construct a plausible justification for a
biased answer while never disclosing the actual bias means a system that
displays the chain to a user, an auditor, or a compliance reviewer as
evidence of sound reasoning is making an implicit and potentially false
safety claim. The paper states this directly. plausible chain text can
mislead a reader into trusting a model's answer without any actual guarantee
about its safety. Where a chain is shown as justification for a consequential
automated decision, such as a loan denial or a moderation action, an
external, independently verifiable check should back the decision, never the
chain's self-report alone.

**Hidden or redacted chains shift the trust boundary to the provider.**
OpenAI's o1 deliberately withholds the raw chain from the end user and
prohibits attempts to extract it, per its documented policy summarized
earlier in dimension 9, citing both safety, preventing a bad actor from
learning to circumvent the model's own safety reasoning by reading it, and
competitive reasons. This means an application built on such a model cannot
audit, log, or inspect the model's actual reasoning at all, only its
summarized or final form, which is a meaningful constraint for any regulated
domain requiring an inspectable decision trail.

**Prompt injection through content the model reasons over.** If retrieved
documents, tool outputs, or other externally sourced content enters the
context before the reasoning phase, that content can influence the chain the
same way it can influence a direct answer, and a chain that reasons about
untrusted content is not inherently safer against injection than a direct
answer would be. The visibility of the chain can help a reviewer notice an
injection attempt after the fact, but the pattern provides no built-in
protection against it during generation.

On the positive side, the pattern's visible intermediate representation is
occasionally a genuine security asset. an inspectable chain can be the
mechanism by which a suspicious decision is caught before it is acted on, in
a human-in-the-loop review step, precisely because the reasoning is
externalized rather than opaque. The caveat from the unfaithfulness finding
above still applies. that review catches what the chain happens to disclose,
not necessarily the true cause of the model's answer.

## Code examples

Chain of Thought is a prompting and orchestration technique rather than a
type-system construct, so the idiomatic form in every language is largely
identical, build the prompt, call the model, parse the response. The three
examples below show the same underlying pattern at increasing depth. a
minimal zero-shot trigger in Python, a self-consistency majority vote in
TypeScript, and a structured-output variant with a separate reasoning field
in Go, which avoids brittle text extraction entirely. Go is chosen over Rust
and Swift here because its explicit error handling and lack of exceptions
make the two-call extraction flow, generate the chain, then parse the
answer, unusually clear to read, and because a structured-output CoT client
is a realistic Go use case in a backend service. Rust and Swift are omitted
because neither adds a genuinely different idiomatic shape for this pattern
beyond what Python and TypeScript already show, an HTTP call and a text or
JSON parse, and three languages already satisfy the repository's minimum.

### Python, Zero-Shot CoT with two-stage extraction

```python
import re


def build_reasoning_prompt(question: str) -> str:
    return f"{question}\nLet's think step by step."


def build_extraction_prompt(question: str, chain: str) -> str:
    return f"{question}\n{chain}\nTherefore, the answer is"


def parse_final_answer(extraction_response: str) -> str:
    match = re.search(r"answer is[:\s]*(.+)", extraction_response, re.IGNORECASE)
    if not match:
        raise ValueError("could not extract a final answer from the response")
    return match.group(1).strip().rstrip(".")


def solve_with_zero_shot_cot(question: str, call_model) -> tuple[str, str]:
    reasoning_prompt = build_reasoning_prompt(question)
    chain = call_model(reasoning_prompt)
    extraction_prompt = build_extraction_prompt(question, chain)
    extraction_response = call_model(extraction_prompt)
    answer = parse_final_answer(extraction_response)
    return chain, answer


def fake_model(prompt: str) -> str:
    if "step by step" in prompt:
        return (
            "There are 3 boxes with 4 apples each, so 3 times 4 is 12. "
            "Then 2 apples are removed, so 12 minus 2 is 10."
        )
    return "the answer is 10"


if __name__ == "__main__":
    question = "There are 3 boxes with 4 apples each. 2 apples are removed. How many apples remain?"
    chain, answer = solve_with_zero_shot_cot(question, fake_model)
    print("chain", chain)
    print("answer", answer)
```

### TypeScript, self-consistency majority vote over sampled chains

```typescript
interface ModelCall {
  (prompt: string, temperature: number): Promise<string>;
}

function extractAnswer(chainResponse: string): string | null {
  const match = chainResponse.match(/answer is[:\s]*([^.]+)/i);
  return match ? match[1].trim() : null;
}

async function selfConsistencyAnswer(
  question: string,
  sampleCount: number,
  callModel: ModelCall
): Promise<{ answer: string; agreement: number; samples: number }> {
  const prompt = `${question}\nLet's think step by step, then state "the answer is X".`;
  const calls: Promise<string>[] = [];
  for (let i = 0; i < sampleCount; i++) {
    calls.push(callModel(prompt, 0.7));
  }
  const chains = await Promise.all(calls);

  const tally = new Map<string, number>();
  for (const chain of chains) {
    const answer = extractAnswer(chain);
    if (answer === null) continue;
    tally.set(answer, (tally.get(answer) ?? 0) + 1);
  }

  let bestAnswer = "";
  let bestCount = 0;
  for (const [answer, count] of tally) {
    if (count > bestCount) {
      bestAnswer = answer;
      bestCount = count;
    }
  }

  return {
    answer: bestAnswer,
    agreement: bestCount / sampleCount,
    samples: sampleCount,
  };
}

async function fakeModel(prompt: string, _temperature: number): Promise<string> {
  const answers = ["10", "10", "9", "10", "10"];
  const index = Math.floor(Math.random() * answers.length);
  return `Working through it step by step, the answer is ${answers[index]}.`;
}

selfConsistencyAnswer(
  "There are 3 boxes with 4 apples each. 2 apples are removed. How many apples remain?",
  5,
  fakeModel
).then((result) => {
  console.log(`majority answer ${result.answer}, agreement ${result.agreement}`);
});
```

### Go, structured output with a separate reasoning field

```go
package main

import (
	"encoding/json"
	"fmt"
)

// ReasonedAnswer separates the chain from the committed answer so no
// text extraction is needed downstream.
type ReasonedAnswer struct {
	Reasoning string `json:"reasoning"`
	Answer    string `json:"answer"`
}

type ModelCall func(prompt string) (string, error)

func buildStructuredCoTPrompt(question string) string {
	return fmt.Sprintf(
		"%s\nThink step by step, then respond with JSON matching "+
			"{\"reasoning\": string, \"answer\": string}.",
		question,
	)
}

func solveWithStructuredCoT(question string, call ModelCall) (ReasonedAnswer, error) {
	raw, err := call(buildStructuredCoTPrompt(question))
	if err != nil {
		return ReasonedAnswer{}, fmt.Errorf("model call failed. %w", err)
	}

	var result ReasonedAnswer
	if err := json.Unmarshal([]byte(raw), &result); err != nil {
		return ReasonedAnswer{}, fmt.Errorf("could not parse structured response. %w", err)
	}
	if result.Answer == "" {
		return ReasonedAnswer{}, fmt.Errorf("model returned no answer field")
	}
	return result, nil
}

func fakeModel(prompt string) (string, error) {
	return `{"reasoning": "3 boxes of 4 apples is 12, minus 2 removed is 10.", "answer": "10"}`, nil
}

func main() {
	question := "There are 3 boxes with 4 apples each. 2 apples are removed. How many apples remain?"
	result, err := solveWithStructuredCoT(question, fakeModel)
	if err != nil {
		fmt.Println("error", err)
		return
	}
	fmt.Println("reasoning", result.Reasoning)
	fmt.Println("answer", result.Answer)
}
```

## 18. References

1. Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei
   Xia, Ed Chi, Quoc Le, Denny Zhou. "Chain-of-Thought Prompting Elicits
   Reasoning in Large Language Models." arXiv 2201.11903, first posted 2022,
   revised 2023. https://arxiv.org/abs/2201.11903 Verified 2026-08-02. Source
   of the pattern's name, the original manual few-shot form, the GSM8K and
   PaLM-540B production evaluation, and the scale-dependence finding.
2. Takeshi Kojima, Shixiang Shane Gu, Machel Reid, Yutaka Matsuo, Yusuke
   Iwasawa. "Large Language Models are Zero-Shot Reasoners." arXiv 2205.11916,
   NeurIPS 2022. https://arxiv.org/abs/2205.11916 Verified 2026-08-02. Source
   of the Zero-Shot CoT variant, the trigger phrase, and the two-stage
   extraction method.
3. Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc Le, Ed Chi, Sharan Narang,
   Aakanksha Chowdhery, Denny Zhou. "Self-Consistency Improves Chain of
   Thought Reasoning in Language Models." arXiv 2203.11171.
   https://arxiv.org/abs/2203.11171 Verified 2026-08-02. Source of the
   self-consistency decoding variant and its benchmark gains.
4. Miles Turpin, Julian Michael, Ethan Perez, Samuel R. Bowman. "Language
   Models Don't Always Say What They Think. Unfaithful Explanations in
   Chain-of-Thought Prompting." arXiv 2305.04388.
   https://arxiv.org/abs/2305.04388 Verified 2026-08-02. Source of the
   unfaithfulness finding used across dimensions 3, 11, 15, and 17.
5. Denny Zhou, Nathanael Schärli, Le Hou, Jason Wei, Nathan Scales, Xuezhi
   Wang, Dale Schuurmans, Claire Cui, Olivier Bousquet, Quoc Le, Ed Chi.
   "Least-to-Most Prompting Enables Complex Reasoning in Large Language
   Models." arXiv 2205.10625. https://arxiv.org/abs/2205.10625 Verified
   2026-08-02. Source of the least-to-most decomposition variant.
6. Luyu Gao, Aman Madaan, Shuyan Zhou, Uri Alon, Pengfei Liu, Yiming Yang,
   Jamie Callan, Graham Neubig. "PAL. Program-aided Language Models."
   arXiv 2211.10435. https://arxiv.org/abs/2211.10435 Verified 2026-08-02.
   Source of the program-aided execution variant and the GSM8K comparison
   against PaLM-540B CoT.
7. Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik
   Narasimhan, Yuan Cao. "ReAct. Synergizing Reasoning and Acting in
   Language Models." arXiv 2210.03629, ICLR 2023.
   https://arxiv.org/abs/2210.03629 Verified 2026-08-02. Source of the
   ReAct relationship described in dimension 13.
8. Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L. Griffiths,
   Yuan Cao, Karthik Narasimhan. "Tree of Thoughts. Deliberate Problem
   Solving with Large Language Models." arXiv 2305.10601.
   https://arxiv.org/abs/2305.10601 Verified 2026-08-02. Source of the Tree
   of Thoughts relationship and the Game of 24 comparison figures.
9. DeepSeek-AI, Daya Guo, Dejian Yang, et al. "DeepSeek-R1. Incentivizing
   Reasoning Capability in LLMs via Reinforcement Learning."
   arXiv 2501.12948. https://arxiv.org/abs/2501.12948 Verified 2026-08-02.
   Source of the RL-trained inference-time chain generation description and
   the distillation transfer finding.
10. Anthropic. "Extended thinking."
    https://platform.claude.com/docs/en/build-with-claude/extended-thinking
    Verified 2026-08-02. Source of the Claude thinking-block behaviour, the
    `budget_tokens` and `effort` mechanisms, and the batch-processing latency
    guidance.
11. Wikipedia contributors. "OpenAI o1."
    https://en.wikipedia.org/wiki/OpenAI_o1 Verified 2026-08-02. Used only
    to confirm the wording of OpenAI's own quoted statements about o1's
    hidden chain-of-thought policy and the accuracy-versus-compute
    correlation, not as a source of independent explanation.
