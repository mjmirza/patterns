---
name: Constitutional AI
slug: constitutional-ai
family: 17-ai-agentic
category: Agentic
aliases: [CAI, RLAIF Alignment, Self-Critique Training, Principle-Based Alignment]
first_described: "Bai, Kadavath, Kundu, Askell et al., Anthropic, arXiv:2212.08073, 15 December 2022"
maturity: established
related: [output-guardrails, input-guardrails, reflexion, llm-as-judge, evaluator-optimizer, self-consistency]
incompatible_with: []
verified: 2026-08-03
---

# Constitutional AI

## 1. Name, aliases, and lineage

Constitutional AI, abbreviated CAI, names a training method for large language
models introduced by Anthropic in Yuntao Bai, Saurav Kadavath, Sandipan Kundu,
Amanda Askell, and forty-seven co-authors, "Constitutional AI. Harmlessness
from AI Feedback," `arXiv:2212.08073`, submitted 15 December 2022,
https://arxiv.org/abs/2212.08073, verified 2026-08-03. The paper's own abstract
states the goal plainly. "As AI systems become more capable, we would like to
enlist their help to supervise other AIs," and the method trains "a harmless AI
assistant through self-improvement, without any human labels identifying
harmful outputs" (same source). The name comes from the artifact at the center
of the method, a written document of principles called a constitution, which
the model is trained to consult when critiquing and revising its own output.

The alias RLAIF, reinforcement learning from AI feedback, names the second
training phase of the method specifically, where a preference model trained on
AI-generated comparisons, rather than a preference model trained on
human-labeled comparisons, supplies the reward signal for reinforcement
learning. The paper coins RLAIF as a direct counterpoint to RLHF,
reinforcement learning from human feedback, the method used to align
InstructGPT (Long Ouyang et al., "Training language models to follow
instructions with human feedback," `arXiv:2203.02155`, submitted 4 March 2022,
https://arxiv.org/abs/2203.02155, verified 2026-08-03) and the original
summarization work that established RLHF as a practical technique (Paul
Christiano et al., "Deep reinforcement learning from human preferences,"
`arXiv:1706.03741`, submitted 12 June 2017,
https://arxiv.org/abs/1706.03741, verified 2026-08-03). RLAIF is sometimes used
loosely to mean any AI-feedback loop, but inside the CAI paper it specifically
denotes the second, reinforcement-learning half of a two-phase pipeline. The
first, supervised half has no accepted separate name and is usually just
called the CAI supervised phase or the critique-and-revision phase.

The name Constitutional AI is occasionally confused with two unrelated ideas
that happen to share the word constitution. It is not a legal framework for AI
regulation, and it is not the older, narrower idea of a hard-coded rule engine
that rejects disallowed strings before they reach a model, which this
repository documents separately as Input Guardrails and Output Guardrails. CAI
is a training-time method that shapes what the model itself produces. Guardrail
patterns are typically inference-time filters wrapped around a model that was
not necessarily trained this way. The two compose, and the composition is
covered in dimension 13.

Anthropic published the specific principles it uses under the plain-language
document "Claude's Constitution," https://www.anthropic.com/news/claudes-constitution,
verified 2026-08-03, which states the constitution's principles are drawn "from
multiple sources," naming the United Nations Universal Declaration of Human
Rights, Apple's terms of service, DeepMind's Sparrow rules, non-Western
perspectives, and Anthropic's own internal research, and states explicitly that
the document is "neither finalized nor optimal" and is expected to be revised.
The DeepMind Sparrow rules referenced there come from Amelia Glaese, Nat
McAleese, et al., "Improving alignment of dialogue agents via targeted human
judgements," `arXiv:2209.14375`, submitted 28 September 2022,
https://arxiv.org/abs/2209.14375, verified 2026-08-03, an earlier system that
decomposed acceptable dialogue behavior into a fixed list of natural-language
rules and trained per-rule reward models from targeted human judgments. Sparrow
is a direct forebear of CAI in spirit, rules stated in language rather than
implied by preference comparisons alone, but Sparrow still collected its
reward signal from human raters judging rule violations, where CAI's second
phase replaces that human rater with the model itself.

## 2. Problem and context

A team is aligning a language model so that it refuses genuinely harmful
requests, stays honest about its own uncertainty, and avoids the kind of output
that erodes trust in an assistant a person relies on daily, without becoming so
cautious that it refuses ordinary requests or answers everything with a hedge.
The dominant technique available before CAI, RLHF, works by paying human
raters to compare pairs of model outputs and pick the better one, then training
a reward model on those comparisons and optimizing the policy against that
reward model. This works, and it produced the first generation of genuinely
helpful chat assistants, but it has three costs that grow as a company scales
the technique across more behaviors and larger models.

First, every additional behavior the team wants to shape, more careful about
medical claims, less sycophantic, better at declining to help with a bioweapon
synthesis question, needs its own comparison data, collected by paying and
managing a pool of human raters, and that data collection is slow relative to
how fast a model's capabilities change. Second, the raters themselves are
exposed to a stream of the model's worst candidate outputs in order to compare
them, since eliciting a diverse range of responses to a harmful prompt and
having a human choose the least bad one is exactly how the comparison data is
generated. This is a real cost to the people doing the labeling, and the CAI
paper names reducing this "human labor and misery" as a direct motivation (Bai
et al. 2022, section 1). Third, and this is the forces question the pattern is
really answering, a reward model trained purely on pairwise preferences is
opaque. Nobody can point at the reward model's parameters and say which
principle it is enforcing when it prefers one output to another, so when the
resulting policy does something surprising, refuses too readily, or drifts
toward a behavior nobody intended, there is no written document to check the
behavior against.

Constitutional AI is the right context to reach for when the properties a team
wants to instill in a model can be written as explicit natural-language
principles that a sufficiently capable model can itself apply as a critic,
when reducing human exposure to harmful content during data collection matters,
and when the team wants the resulting alignment to be auditable against a
document rather than only inferable from example transcripts. It is the wrong
context, covered fully in dimension 4, when the base model is not yet capable
enough to critique its own output usefully, or when the target behavior is a
narrow factual or stylistic correction better handled by supervised
fine-tuning on a small labeled set.

## 3. Forces

- **Alignment fidelity versus data collection cost.** RLHF alignment fidelity
  is bounded by how much high-quality human comparison data a team can afford
  to collect. CAI's supervised phase can generate self-critique-and-revision
  training pairs automatically from a constitution and a base model, at the
  cost of the alignment being only as good as the base model's ability to
  critique itself against the written principles, which is why the paper only
  demonstrates the method on already-capable models.
- **Human labor exposure versus model-in-the-loop risk.** Removing human raters
  from harmlessness comparisons protects people from repeatedly reading
  disturbing generated content, but it shifts the trust boundary onto the
  model doing the judging. If the model's own harmlessness judgment is
  miscalibrated, that miscalibration is what gets reinforced, and there is no
  human step left to catch it before it compounds across the RL loop.
- **Interpretability versus flexibility of a black-box reward model.** A
  written constitution is inspectable in a way a reward model's weights are
  not. Anyone can read the principles and reason about what behavior they
  should produce. But a written principle is also a coarser lever than a dense
  set of pairwise preferences, so CAI trades some of RLHF's fine-grained
  behavioral shaping for coarser, more legible control.
- **Refusal calibration.** A model trained hard against harm principles tends
  toward over-refusal, declining benign requests that merely resemble harmful
  ones in surface form. The CAI paper's own harmlessness-versus-helpfulness
  trade-off curve exists because pushing harder on one principle without a
  countervailing helpfulness principle degrades the other. A constitution with
  only prohibitive rules and no principle favoring being helpful produces an
  assistant that is safe and nearly useless.
- **Latency and compute at inference time versus training time.** CAI's cost
  is paid almost entirely during training, in generating self-critiques and
  revisions and in running the RL loop against an AI preference model. A model
  trained this way carries no extra inference-time cost relative to an RLHF
  model of the same size. This is the opposite trade-off from Output
  Guardrails or Constitutional Classifiers, covered in dimension 13, which pay
  their cost per inference call instead.

## 4. Applicability and non-applicability

Reach for Constitutional AI, or study its method to inform a related choice,
when the following hold.

- The behaviors being targeted, refusing harmful requests, staying within a
  domain, adopting a particular tone or set of values, can be written down as
  explicit natural-language principles that a person could hand to another
  person and expect similar judgment calls.
- The base model being trained is already capable enough to critique its own
  output meaningfully against those principles. The CAI paper works with
  models that already have strong general instruction-following ability from
  an initial supervised fine-tuning stage.
- Reducing the volume of harmful content human labelers must read and rank
  during data collection is a real organizational priority, not a nice-to-have.
- The team wants alignment behavior that can be audited by reading a document,
  useful for external accountability, internal review, or explaining a
  model's refusal pattern to a regulator or a customer.
- The scale of desired behavioral coverage is large enough that hand-writing
  and hand-labeling a comparison dataset for every target behavior is
  infeasible, but writing one more principle into an existing constitution is
  cheap.

Constitutional AI is the wrong tool, and reaching for it wastes effort or
introduces risk, when the following hold.

- The base model lacks the capability to self-critique reliably. The CAI
  paper's own method depends on the model already being good enough to
  recognize when its own answer violates a stated principle. Applying the
  critique-and-revise loop to a weak model produces critiques that are
  themselves unreliable, and training on unreliable critiques degrades rather
  than improves the policy. This is a capability floor, not a tuning knob.
- The target correction is a narrow, factual, or stylistic fix, teach the
  model your company's product name is spelled a specific way, teach it a
  fixed output format, that a small supervised fine-tuning set or a system
  prompt handles at a fraction of the engineering cost.
- There is no meaningful judgment call to encode. A principle like "never
  output valid credit card numbers" is a deterministic filter, not a
  constitutional judgment, and belongs in an Output Guardrail or Input
  Guardrail as a hard check rather than as a soft, learned preference.
  Deterministic and probabilistic controls solve different failure modes and
  should not be substituted for each other, per dimension 13.
- The team cannot run or afford the RL training infrastructure the second
  phase requires. RLAIF is still an RL loop with a policy, a reward model, and
  the instability that comes with optimizing a learned model against another
  learned model. A team without RL infrastructure and the expertise to debug
  reward hacking should not adopt this as a first alignment technique.
- The application needs per-tenant or per-request customization of the safety
  policy. A constitution baked into model weights during training is shared
  across every deployment of that model. A SaaS platform that needs customer A
  to have a stricter content policy than customer B needs a request-time
  guardrail layer, not a retrain.
- Regulatory or safety review requires bit-for-bit reproducible, testable
  behavior under a fixed rule set with no learned component in the loop that
  approves or blocks an individual request, since a constitutionally trained
  model's behavior at inference time is still a learned, probabilistic policy,
  not a deterministic rule evaluator.

## 5. Structure

Constitutional AI names five participants, spread across two training phases.

- **The constitution.** A written, ordered or unordered set of natural-language
  principles the model is trained to consult. Each principle is typically
  phrased as a critique request, "identify ways in which the assistant's
  response is harmful," paired with a revision request, "revise the response
  to remove any harmful content while remaining helpful." The constitution is
  the only artifact in the system that is authored by humans and directly
  legible without inspecting model weights.
- **The base policy model.** An already helpful, already instruction-tuned
  language model, typically the output of an initial supervised fine-tuning
  stage on human demonstrations, that serves as the starting point for both
  phases. This model is not yet trained to prioritize harmlessness. It may
  produce harmful completions when prompted adversarially, and that is the
  raw material the supervised phase corrects.
- **The critique-and-revision loop, supervised phase.** The same base model,
  reused in three distinct roles in sequence. First it is sampled as a
  generator, producing an initial response to a red-team-style prompt. Second
  it is prompted, using a principle drawn from the constitution, to critique
  that response in natural language. Third it is prompted, using its own
  critique, to revise the original response. The revised response is what gets
  collected into a new supervised fine-tuning dataset, which trains a new
  model, the SL-CAI model in the paper's naming.
- **The AI preference model.** A model, again derived from sampling the
  SL-CAI model or a comparably capable model, that is shown pairs of
  candidate responses and asked to state, using a constitutional principle as
  the judging criterion, which response is preferable. These AI-generated
  preference labels replace the human preference labels an RLHF pipeline would
  otherwise pay to collect, and they train a preference model with the same
  architecture and training objective an RLHF reward model would use.
- **The RL-tuned policy, RLAIF phase.** The final model, produced by running
  reinforcement learning, in the CAI paper specifically Proximal Policy
  Optimization, on the SL-CAI model using the AI preference model as the
  reward signal. This is the model that ships. Anthropic's Claude's
  Constitution page describes the process end to end at a product level and
  states that the resulting values are meant to be "explicit and inspectable
  rather than implicit" (Anthropic, "Claude's Constitution," verified
  2026-08-03).

## 6. ASCII structure diagram

```
CONSTITUTION (human-authored principles)
  |
  |  used as the critique/revision prompt in phase 1
  |  used as the comparison prompt in phase 2
  v
+------------------------------------------------------------+
| PHASE 1. Supervised critique-and-revision                   |
|                                                              |
|  base policy model --generates--> initial response          |
|         |                              |                    |
|         |  (same model, critic role)   |                    |
|         v                              v                    |
|  constitution principle --prompts--> critique                |
|                                        |                     |
|                                        v                     |
|                              revised response                |
|                                        |                     |
+----------------------------------------|---------------------+
                                          v
                            supervised fine-tune dataset
                                          |
                                          v
                                  SL-CAI model
                                          |
+-----------------------------------------|---------------------+
| PHASE 2. RL from AI feedback (RLAIF)     |                    |
|                                          v                    |
|          SL-CAI model samples pairs of responses              |
|                        |                                      |
|                        v                                      |
|   AI preference model --judges pair, using constitution-->    |
|                        |                                      |
|                        v                                      |
|              AI preference labels                             |
|                        |                                      |
|                        v                                      |
|          preference/reward model (trained on AI labels)       |
|                        |                                      |
|                        v                                      |
|   PPO reinforcement learning loop, policy = SL-CAI model       |
|                        |                                      |
+------------------------|---------------------------------------+
                          v
                 RL-CAI model (ships)
```

## 7. Dynamics

The dynamics run in two sequential stages, each of which is itself an
iterative loop rather than a single pass.

In the supervised phase, the process begins with a set of red-team prompts,
questions designed to elicit potentially harmful, unhelpful, or unhonest
responses. For each prompt, the base model generates an initial completion.
That completion, together with a principle sampled from the constitution, is
fed back into the same model as a new prompt asking it to identify problems
with the completion relative to that principle. The model's critique, together
with the original completion and the same principle, is then fed back in a
third pass asking the model to produce a revised completion that addresses the
critique while remaining as helpful as possible. This critique-then-revise
sequence can be run for more than one round per example, chaining a second
critique against the first revision, before the final revision is accepted
into the training set. Once a full dataset of prompt-to-revised-response pairs
exists, the base model is fine-tuned on it in the ordinary supervised way,
producing the SL-CAI model. Importantly, the paper found that the initial
supervised phase alone measurably reduces harmful output even before the RL
phase runs, because the fine-tuning has already baked in a preference for the
kind of self-corrected response the constitution favors.

In the RLAIF phase, the SL-CAI model is used to sample multiple candidate
responses to a new set of prompts. Pairs of these candidates are then
presented to a comparison prompt, again constructed from a constitutional
principle, asking a model, typically a larger or more capable model than the
one being trained, which of the two responses better satisfies the principle.
Unlike an RLHF pipeline, where a human clicks a preference between two options,
here the model produces a probability distribution over which response it
prefers, and that soft label, not a hard binary choice, is what trains the
preference model. Once the preference model is trained on a large batch of
these AI-generated comparisons, it functions exactly as a reward model would
in RLHF, scoring any candidate response with a scalar reward. Standard
reinforcement learning, PPO in the original paper, then optimizes the SL-CAI
policy against this learned reward, with the usual RL machinery of sampling
rollouts, computing advantages, and updating policy parameters to increase the
probability of higher-reward completions and decrease the probability of
lower-reward ones. This loop runs until reward improvement plateaus or begins
to show the signature of the reward model being gamed rather than genuinely
satisfied, at which point training stops and the resulting policy is the
release candidate.

## 8. Implementation variants

- **The original two-phase pipeline (Bai et al. 2022).** Supervised
  critique-and-revision, then PPO against an AI preference model. This is the
  variant described in dimensions 5 through 7 and is the reference
  implementation everything else in this dimension is compared against.
- **Chain-of-thought critiques.** The same 2022 paper reports that giving the
  critiquing model explicit chain-of-thought reasoning space before it states
  its critique or its preference judgment measurably improves both the
  harmlessness of the resulting policy and the legibility of why a given
  response was judged harmful, since the reasoning trace itself becomes
  auditable alongside the final judgment.
- **Constitutional Classifiers, an inference-time descendant.** Anthropic's
  later work, described at https://www.anthropic.com/research/constitutional-classifiers,
  verified 2026-08-03, reuses the same constitution artifact and the same
  synthetic-data-generation idea, but trains separate input and output
  classifiers, run alongside a fixed, already-deployed model at inference
  time, rather than training the policy's own weights. Anthropic reports the
  updated system reduced jailbreak attack success from 86 percent to 4.4
  percent in their testing, with a 0.38 percent increase in over-refusals on
  production traffic and roughly 24 percent additional inference compute
  overhead, and states plainly that a public red-teaming exercise still found
  one universal jailbreak despite roughly 3,700 collective hours of
  red-teaming effort from 339 participants (same source). This variant
  answers a different question than the original CAI pipeline, protecting an
  already-trained model at serve time instead of shaping the model's weights,
  and it is the clearest example inside Anthropic's own published work of CAI
  principles being reused as a runtime guardrail rather than a training
  signal, which is exactly the composition covered in dimension 13.
- **Sparrow's rule-conditional reward model, a direct forebear.** DeepMind's
  Sparrow, Glaese, McAleese et al. 2022, decomposes acceptable dialogue
  behavior into an explicit list of natural-language rules and trains a
  separate rule-conditional reward model from targeted human judgments about
  whether a given response violates a specific rule, rather than a single
  undifferentiated preference score. This is architecturally close to CAI's
  constitution-driven approach but keeps a human in the loop supplying the
  per-rule judgment, where CAI's second phase replaces that human judgment
  with a model's own judgment.
- **RLAIF without a constitution, a related but distinct technique.** Google
  Research's "RLAIF. Scaling Reinforcement Learning from Human Feedback with
  AI Feedback," Harrison Lee et al., `arXiv:2309.00267`, submitted 1 September
  2023, https://arxiv.org/abs/2309.00267, verified 2026-08-03, studies
  replacing human preference labels with AI-generated preference labels for a
  summarization task, and reports that RLAIF achieves comparable improvements
  over supervised fine-tuning as RLHF does on the same task. This work
  demonstrates that the AI-feedback half of CAI's method generalizes beyond
  harmlessness and beyond a written constitution to ordinary quality
  preferences, but it does not use a constitution as the judging criterion,
  so it should be read as evidence for the RLAIF mechanism's soundness rather
  than as a second implementation of Constitutional AI itself.
- **Constitution-as-system-prompt, a lightweight and materially different
  approximation.** Some teams write a set of behavioral principles into a
  system prompt or a moderation pass instead of training against them,
  reasoning by analogy to CAI's constitution artifact. This is meaningfully
  different from CAI, which changes the policy's weights through RL, not only
  its prompt context, and a system-prompt approximation carries none of the
  RLAIF training signal or the self-critique dataset generation. It is closer
  in spirit to Output Guardrails than to Constitutional AI proper, and
  conflating the two overstates how strong a prompt-only approach actually is
  against an adversarial user.

## 9. Known production uses

- **Anthropic's Claude family.** Anthropic states directly that Claude is
  trained using Constitutional AI and publishes the constitution's sourcing
  and intent at https://www.anthropic.com/news/claudes-constitution, verified
  2026-08-03. This is the flagship, first-party production use the method was
  developed for, and it is the deployment referenced throughout the original
  2022 paper's evaluation.
- **Anthropic's Constitutional Classifiers deployed against Claude in
  production.** The same organization's later system, described at
  https://www.anthropic.com/research/constitutional-classifiers, verified
  2026-08-03, is a second, independently documented production use, this time
  of the constitution artifact applied as a runtime input and output filter
  layered on top of an already-trained Claude model, with reported production
  traffic over-refusal figures, which is direct evidence the technique is
  measured against live usage, not only a research benchmark.
- **Google Research's RLAIF study, applied within Google's own summarization
  pipeline research.** Lee et al. 2023, `arXiv:2309.00267`,
  https://arxiv.org/abs/2309.00267, verified 2026-08-03, is a second
  organization independently validating the AI-feedback half of the CAI
  method, reporting that human evaluators preferred RLAIF-generated summaries
  over the SFT-only baseline at rates comparable to RLHF, and the paper
  explicitly frames its motivation as reducing the annotation cost problem
  that CAI's first phase also targets.

## 10. Consequences

Positive.

- Reduces the volume of harmful or disturbing content human raters must read
  and rank in order to produce a harmlessness-aligned model, a labor and
  wellbeing benefit the original paper names explicitly as a motivation.
- Produces an inspectable artifact, the constitution itself, that a person can
  read to understand what values a model was pushed toward, in a way a set of
  anonymous pairwise preference comparisons never can be.
- Scales more cheaply across additional target behaviors than collecting a
  fresh human comparison dataset for each one, since adding a principle to the
  constitution is a text edit, not a new data collection campaign.
- The chain-of-thought variant produces a legible reasoning trace alongside
  each critique and preference judgment, which is itself useful evidence when
  investigating why a specific completion was judged one way rather than
  another.
- The method transfers, as the Constitutional Classifiers work and the
  Google RLAIF study both independently demonstrate, meaning the core
  mechanism, AI-generated feedback trained against a stated set of criteria,
  is not a one-off trick specific to Anthropic's original setup.

Negative.

- Alignment quality is bounded above by the judging model's own competence at
  applying the constitution. A weak or miscalibrated judge trains a weak or
  miscalibrated policy, and there is no independent human check inside the
  RLAIF loop to catch that miscalibration before it compounds.
- Pushing harmlessness principles too hard relative to helpfulness principles
  produces measurable over-refusal, an assistant that declines benign
  requests because they superficially resemble a disallowed pattern, and
  tuning that balance is itself a judgment call with no formula.
- The constitution's principles are written in natural language and are
  therefore subject to the same interpretive ambiguity as any legal or policy
  text. Two readings of the same principle by two different critique passes
  can disagree, and that disagreement is invisible unless someone specifically
  audits critique-phase transcripts.
- RLAIF is still reinforcement learning against a learned reward model, and
  inherits RLHF's known failure mode of reward hacking, where the policy
  learns to satisfy the reward model's proxy signal in ways that do not
  reflect genuine adherence to the underlying principle.
- The Constitutional Classifiers variant's own public red-teaming result, one
  universal jailbreak found despite roughly 3,700 collective hours of
  red-teaming, is direct evidence that even a well-resourced application of
  this family of techniques does not produce an unbreakable system, only a
  substantially more expensive one to break.

## 11. Failure modes and misuse

- **Symptom.** The model over-refuses ordinary, benign requests at a
  noticeably higher rate after a round of constitution-driven training,
  sometimes declining to answer questions merely adjacent to a sensitive
  topic. **Cause.** The constitution's harmlessness principles were weighted,
  in the critique-and-revision or preference-comparison prompts, without a
  correspondingly explicit helpfulness principle instructing the critic to
  penalize unnecessary refusal, so the training signal only ever pushes toward
  caution. **Fix.** Pair every harmlessness principle in the constitution with
  an explicit helpfulness counter-principle used in the same critique pass,
  and specifically sample red-team-adjacent benign prompts into the
  evaluation set so over-refusal is measured, not only harmful-content
  leakage.
- **Symptom.** The AI preference model's judgments look internally consistent
  during training but the resulting policy behaves worse on held-out
  adversarial prompts than the SL-CAI model it started from. **Cause.** Reward
  hacking. The RL policy has found completions that score well against the
  learned preference model's proxy for the constitutional principle without
  actually satisfying the principle, a known RLHF-family failure that RLAIF
  does not remove, since the preference model is still a learned
  approximation rather than the principle itself. **Fix.** Hold out a
  separate evaluation set scored by a different judging model or by spot-check
  human review, monitor the gap between preference-model reward and this
  independent evaluation over the course of training, and stop training when
  that gap widens even if the reward curve is still climbing.
- **Symptom.** Two runs of the critique-and-revision pipeline on the same
  prompt and the same constitution produce meaningfully different revisions,
  and downstream behavior on similar prompts is inconsistent. **Cause.** A
  constitutional principle is phrased ambiguously enough that different
  samples of the critiquing model interpret it differently, and that
  interpretive variance gets baked into the supervised fine-tuning dataset as
  noise rather than signal. **Fix.** Treat constitution authoring as an
  iterative engineering task with its own review process, run each candidate
  principle through several critique-model samples on a fixed prompt set
  before adopting it, and rewrite any principle that produces materially
  different revisions across samples.
- **Symptom.** A team assumes their model is protected against a specific
  category of harmful request because a corresponding principle exists in the
  constitution, then discovers in a red-team exercise that a rephrased
  version of the same request slips through. **Cause.** Misplaced confidence
  that constitution-driven training produces a hard guarantee rather than a
  learned, probabilistic tendency. A constitution shapes the distribution of
  likely outputs, it does not enforce a deterministic rule, and Anthropic's
  own Constitutional Classifiers red-teaming result demonstrates a universal
  jailbreak was found despite extensive constitutional training and a
  dedicated classifier layer. **Fix.** Never treat constitution-driven
  training alone as the full safety boundary for a high-stakes deployment.
  Layer a deterministic Input Guardrail or Output Guardrail, covered in
  dimension 13, in front of the model for any category of harm where a
  probabilistic near-guarantee is not an acceptable risk level.
- **Symptom.** A team applies the critique-and-revision loop to a small,
  weaker model and finds the resulting fine-tuned model is less coherent and
  less helpful than before, not more aligned. **Cause.** The base model was
  below the capability floor CAI assumes. It cannot reliably critique its own
  output against a written principle, so the critiques themselves are noisy
  or wrong, and supervised fine-tuning on noisy self-generated critique data
  degrades the model rather than improving it. **Fix.** Verify the base
  model's self-critique reliability on a held-out set, scored by a
  stronger model or by humans, before committing to a full CAI pipeline. If
  self-critique quality is poor, use conventional RLHF or targeted supervised
  fine-tuning instead until a more capable base model is available.

## 12. Trade-off matrix

| Force | Constitutional AI (RLAIF) | RLHF (human preference labels) | Output Guardrails (inference-time filter) | Sparrow-style rule-conditional RLHF |
|---|---|---|---|---|
| Human rater exposure to harmful content | Low, confined mostly to red-team prompt design and spot audits | High, raters directly compare harmful candidate outputs | None, no training-time human comparison step at all | High, raters judge rule violations directly |
| Marginal cost of adding one new target behavior | Low, edit the constitution text and re-run the pipeline | High, new comparison dataset must be collected | Low to moderate, add or edit a filter rule or classifier training set | High, new rule needs its own human-judgment dataset |
| Auditability of the alignment target | High, the constitution is a readable document | Low, the target lives implicitly in a reward model's weights | High, filter rules are directly readable | High, rules are readable, similar to CAI |
| Inference-time cost | None beyond the base model's own cost | None beyond the base model's own cost | Additional cost per request for the filter or classifier pass | None beyond the base model's own cost |
| Robustness to adversarial rephrasing | Moderate, a learned probabilistic tendency, not a hard rule | Moderate, same underlying limitation | Depends on filter design, can be made close to deterministic for known patterns | Moderate, same underlying limitation as CAI |
| Requires RL training infrastructure | Yes, PPO or an equivalent RL loop | Yes, PPO or an equivalent RL loop | No, can be a classifier trained with ordinary supervised learning, or a static rule | Yes, PPO or an equivalent RL loop |
| Behavior customizable per deployment without retraining | No, baked into shared model weights | No, baked into shared model weights | Yes, filter rules can differ per tenant or per request | No, baked into shared model weights |

## 13. Related and incompatible patterns

- **Output Guardrails and Input Guardrails, this repository.** These are the
  natural inference-time complement to Constitutional AI, not a substitute
  for it. CAI shapes the distribution of outputs a model is likely to produce
  in the first place. Guardrails catch the residual cases that slip through
  that distribution at request time, with a hard, auditable, low-latency
  check. Anthropic's own Constitutional Classifiers work, dimension 8, is the
  clearest documented example of layering the two, reusing the same
  constitution artifact to train a runtime classifier that sits in front of
  an already constitutionally trained model. A production system that
  handles genuinely high-stakes content categories should assume it needs
  both layers, since dimension 11's jailbreak finding shows neither layer
  alone is airtight.
- **LLM-as-Judge, this repository.** The AI preference model in CAI's RLAIF
  phase is a specialized instance of the LLM-as-Judge pattern, a model
  scoring or comparing candidate outputs against a stated criterion. The
  distinction is that CAI's judge is itself trained specifically to produce
  the reward signal for a downstream RL loop, where a general LLM-as-Judge
  deployment is often used directly at evaluation or inference time without
  a subsequent RL training step.
- **Reflexion, this repository.** Reflexion's self-critique-and-retry loop at
  inference time is structurally similar to CAI's supervised critique-and-
  revision phase. Both have a model generate an attempt, criticize its own
  attempt, and produce a revised attempt. The difference is when the loop
  runs and what it produces. Reflexion runs per-request at inference time and
  its output is the improved response itself. CAI's critique-and-revision
  loop runs during data generation and its output is training data that
  permanently changes the policy's weights, so the improvement generalizes
  across future requests rather than being recomputed each time.
- **Evaluator-Optimizer, this repository.** CAI's RLAIF phase, an optimizer
  policy being pushed by a learned evaluator's reward signal, is a specific,
  large-scale instance of the general Evaluator-Optimizer pattern. Where a
  typical Evaluator-Optimizer loop in an application might run a handful of
  iterations per request, CAI's evaluator, the AI preference model, is itself
  a full training artifact, and the optimization step is a training-time RL
  update rather than a per-request revision loop.
- **Self-Consistency, this repository.** Self-Consistency and CAI's
  preference-comparison step both sample a model multiple times and reduce
  the samples to a single answer, but they optimize for different things.
  Self-Consistency samples the same prompt many times and takes a majority
  vote to reduce variance in a single answer. CAI's preference model samples
  different candidate completions and learns a general scoring function from
  many such comparisons across many prompts, producing a reusable reward
  model rather than a one-off answer.
- **Incompatibility with claims of deterministic safety guarantees.**
  Constitutional AI is fundamentally incompatible, as a sole mechanism, with
  any system requirement for provably deterministic behavior under a fixed
  rule set, since the trained policy remains a probabilistic model. Systems
  needing that property, financial transaction approval logic, medical dosing
  calculators, must implement the deterministic requirement as a separate
  hard-coded check outside the model, never rely on constitution-driven
  training alone to satisfy it.

## 14. Refactoring path in and out

Introducing Constitutional AI into an existing RLHF-based alignment pipeline,
step by step.

1. Start from an already helpful, already instruction-tuned base model. CAI's
   supervised phase assumes this starting point exists. It is not a
   replacement for the initial supervised fine-tuning stage that teaches a
   model to follow instructions at all.
2. Write a small, focused constitution first, five to ten principles covering
   the highest-priority target behaviors, phrased as paired critique and
   revision instructions, rather than attempting a full-coverage document on
   the first pass. Validate each principle's clarity per the fix described in
   dimension 11 before adopting it.
3. Run the supervised critique-and-revision loop on a held-out sample of
   red-team-style prompts and manually review a sample of the resulting
   revisions for quality and for over-refusal before committing to fine-tune
   on the full generated dataset.
4. Fine-tune the base model on the reviewed critique-and-revision dataset to
   produce the SL-CAI checkpoint, and evaluate this checkpoint alone, before
   proceeding to the RL phase, against both a harmlessness benchmark and a
   helpfulness benchmark to confirm the supervised phase alone is moving in
   the right direction.
5. Only after the supervised phase shows clean improvement, introduce the
   RLAIF phase, training the AI preference model on constitution-driven
   comparisons and running PPO against it, with the reward-hacking monitoring
   described in dimension 11 wired in from the first training run, not added
   later as an afterthought.
6. Expand the constitution incrementally, one or a small batch of new
   principles at a time, re-running the full pipeline and re-evaluating after
   each expansion, rather than authoring a large constitution up front and
   discovering interpretive conflicts between principles only after training.

Removing or scaling back Constitutional AI from a pipeline that has adopted
it follows a similar staged path, used when a team decides the RL
infrastructure cost is not paying for itself relative to a simpler approach.

1. Freeze the current constitution and the current SL-CAI checkpoint as a
   baseline. Do not discard the supervised critique-and-revision dataset, it
   remains useful supervised fine-tuning data even without a further RLAIF
   step.
2. If the RLAIF phase specifically is the part being removed, ship the
   SL-CAI checkpoint alone. The paper's own results show the supervised phase
   alone produces a meaningful harmlessness improvement over the base model,
   so this is a legitimate reduced-scope deployment, not an abandonment of
   the method.
3. If the entire method is being removed in favor of conventional RLHF,
   preserve the constitution document itself as a specification. It converts
   directly into a rubric for human raters to use when producing the
   comparison labels RLHF needs, which reduces rater disagreement even
   without any AI-generated feedback step.
4. If the entire method is being removed in favor of inference-time
   guardrails only, keep the constitution as the source document for
   authoring the guardrail's filter rules or classifier training data, per
   the Output Guardrails cross-reference in dimension 13, so the investment
   in writing clear principles is not lost even though the enforcement
   mechanism has moved from training time to request time.

## 15. Testing and verification

Testing a Constitutional AI pipeline is materially different from testing
ordinary application code, because the object under test is a probability
distribution over outputs, not a deterministic function, and the thing that
determines correctness, the constitution, is itself natural language subject
to interpretation.

Verify the constitution's principles independently of the training run.
For each principle, construct a held-out set of prompts specifically designed
to probe that principle, sample the critique-and-revision loop against a
fixed base model multiple times per prompt, and check whether the critiques
converge on a consistent judgment. High variance across samples for the same
prompt and principle is a signal the principle text is ambiguous, per
dimension 11, and should be rewritten before it enters the training data.

Verify the supervised phase output before proceeding to RL. Score the SL-CAI
checkpoint against both a harmlessness benchmark, such as red-team prompts
withheld from training, and an unrelated helpfulness benchmark, since a
regression on the helpfulness benchmark at this stage is the earliest and
cheapest point to catch the over-refusal failure mode described in
dimension 11, before it compounds through an RL loop that is far more
expensive to rerun.

Verify the AI preference model's calibration against a trusted reference.
Sample a held-out batch of response pairs, score them with the AI preference
model, and separately score a subset of the same pairs with either a
stronger, independent judging model or a small human-rated sample. A large
divergence between the two indicates the preference model has learned a proxy
that does not track the constitution's actual intent, which is the precursor
to the reward hacking failure mode in dimension 11.

Verify the final RL-tuned policy with adversarial red-teaming, not only
benchmark evaluation. Anthropic's own Constitutional Classifiers work
demonstrates the standard practice, a structured red-teaming exercise with a
defined attack budget, hours and participant count reported, and a specific
metric, attack success rate reduction, rather than a single pass or fail
signal. Track this metric over successive training iterations the same way a
team would track a regression test suite, since a jailbreak that was blocked
in one training run can reappear after the next round of fine-tuning if the
red-team suite is not rerun.

Use test doubles for the expensive parts during early iteration. Substitute a
smaller, cheaper model for the AI preference model while debugging the
overall pipeline mechanics, reward computation, PPO update logic, dataset
plumbing, and only swap in the full-capability preference model once the
mechanics are verified end to end on synthetic or toy reward signals. Running
the full pipeline against the expensive real preference model before the
plumbing is confirmed correct wastes the majority of the compute budget on
debugging infrastructure rather than debugging alignment.

## 16. Observability signals

- **Critique agreement rate.** The fraction of sampled critique passes, for a
  fixed prompt and principle, that reach the same qualitative judgment about
  whether the response violates the principle. A healthy constitution shows
  this holding steady above a chosen threshold across the full principle set.
  A principle whose agreement rate drops over successive constitution
  revisions is a signal that recent edits introduced ambiguity, per
  dimension 11.
- **Reward-versus-independent-evaluation divergence.** Track the AI
  preference model's reward score for policy samples alongside an
  independent, non-training-loop evaluation, a different judging model or a
  human spot-check sample, at fixed intervals through the RL run. A healthy
  training curve shows both climbing together. Reward climbing while the
  independent evaluation plateaus or falls is the leading indicator of reward
  hacking, and should trigger an early stop before shipping the checkpoint.
- **Helpfulness benchmark score alongside harmlessness benchmark score,
  tracked as a pair, never as a single number.** A dashboard that only shows
  harmlessness improving can hide a simultaneous helpfulness regression, the
  over-refusal failure mode in dimension 11. Both curves belong on the same
  chart with the same x axis, training step, so a reviewer can see the
  trade-off directly rather than inferring it from two separate reports.
- **Red-team attack success rate over time, with attack budget reported
  alongside it.** A single attack success rate number without the
  corresponding red-team effort, hours, participant count, distinct attack
  strategies attempted, cannot be compared meaningfully across training runs,
  since a lower success rate against a smaller or less creative red-team
  effort is not evidence of a harder-to-break model.
- **Refusal rate on a fixed, curated set of benign-but-sensitive-adjacent
  prompts.** This is the most direct, cheap-to-run signal for the
  over-refusal failure mode, and should be tracked as its own metric
  alongside the harmful-content benchmark, sampled and reported after every
  training checkpoint, not only at final release.

## 17. Security and privacy implications

Constitutional AI's training data, the critique-and-revision transcripts and
the preference-comparison transcripts, is generated primarily from red-team
prompts and model-generated completions rather than from real user
conversations, which materially reduces the privacy exposure relative to
alignment methods that train directly on production user data. Teams
implementing the method should still verify their red-team prompt set does
not include real, identifiable user content sourced from a support queue or
similar channel without the same handling that applies to any other personal
data used in model training.

The security-relevant property of the method is what it does not guarantee,
covered in dimension 11 and repeated here because it is the single most
consequential security implication. A model trained with Constitutional AI,
even with a well-audited constitution and a clean training run, is not
thereby rendered immune to adversarial prompting, and Anthropic's own public
red-teaming of the Constitutional Classifiers descendant found a universal
jailbreak despite substantial dedicated effort. Any application where a
successful jailbreak has a serious real-world consequence, generating
instructions for physical harm, extracting another user's private data
through a prompt-injection vector, must not treat constitution-driven
training as the sole or final security boundary. It belongs as one layer in a
defense that also includes deterministic input and output filtering, covered
in Input Guardrails and Output Guardrails, and, where the application allows
the model to take real-world actions, the tool-use and permission boundaries
covered by Sub-Agent Isolation and related patterns in this family.

The RLAIF training loop itself introduces a narrower, training-time security
consideration. Because the AI preference model's judgments are consumed
automatically by the RL update with no human review step in between, a
compromised or manipulated preference model, for example one poisoned by a
supply-chain issue in a shared model checkpoint used as the judge, could
silently steer the policy toward behaviors the constitution never actually
sanctioned. Teams running this pipeline should treat the preference model's
weights and the pipeline that produces them with the same provenance and
integrity controls applied to any other component whose output feeds
unreviewed into a production training run.

## 18. References

1. Yuntao Bai, Saurav Kadavath, Sandipan Kundu, Amanda Askell, et al.,
   "Constitutional AI. Harmlessness from AI Feedback," `arXiv:2212.08073`,
   submitted 15 December 2022, https://arxiv.org/abs/2212.08073, verified
   2026-08-03.
2. Anthropic, "Claude's Constitution,"
   https://www.anthropic.com/news/claudes-constitution, verified 2026-08-03.
3. Anthropic, "Constitutional Classifiers,"
   https://www.anthropic.com/research/constitutional-classifiers, verified
   2026-08-03.
4. Amelia Glaese, Nat McAleese, et al., "Improving alignment of dialogue
   agents via targeted human judgements," `arXiv:2209.14375`, submitted 28
   September 2022, https://arxiv.org/abs/2209.14375, verified 2026-08-03.
5. Long Ouyang et al., "Training language models to follow instructions with
   human feedback," `arXiv:2203.02155`, submitted 4 March 2022,
   https://arxiv.org/abs/2203.02155, verified 2026-08-03.
6. Paul Christiano et al., "Deep reinforcement learning from human
   preferences," `arXiv:1706.03741`, submitted 12 June 2017,
   https://arxiv.org/abs/1706.03741, verified 2026-08-03.
7. Harrison Lee et al., "RLAIF. Scaling Reinforcement Learning from Human
   Feedback with AI Feedback," `arXiv:2309.00267`, submitted 1 September
   2023, https://arxiv.org/abs/2309.00267, verified 2026-08-03.

## Code examples

The examples below implement the mechanical skeleton of a Constitutional AI
critique-and-revision pass and a preference-comparison scoring pass. They do
not call a real language model, since no such call is reproducible or
testable in this repository. Each example simulates the model calls with a
small local stand-in so the control flow, prompt assembly, and data-shape
logic, the parts a team actually writes and can get wrong, are real, runnable,
and tested.

### TypeScript

```typescript
type Principle = { name: string; critique: string; revise: string };

type Turn = { prompt: string; response: string };

// Stand-in for a real model call. A production system replaces this
// with an actual API call to the model under training or evaluation.
function modelCall(instruction: string, context: string): string {
  if (instruction.includes("critique")) {
    return context.includes("bypass safety")
      ? "The response explains how to bypass a safety control."
      : "No issues found relative to the principle.";
  }
  return context.includes("bypass safety")
    ? "I can't help with bypassing safety controls, but here is a safe alternative."
    : context;
}

function critiqueAndRevise(turn: Turn, principle: Principle): Turn {
  const critique = modelCall(
    `${principle.critique}. ${principle.name}`,
    turn.response,
  );
  if (critique.startsWith("No issues found")) {
    return turn;
  }
  const revised = modelCall(
    `${principle.revise}. ${principle.name}. Critique. ${critique}`,
    turn.response,
  );
  return { prompt: turn.prompt, response: revised };
}

function runSupervisedPhase(turns: Turn[], principles: Principle[]): Turn[] {
  return turns.map((turn) =>
    principles.reduce((acc, principle) => critiqueAndRevise(acc, principle), turn),
  );
}

const principles: Principle[] = [
  {
    name: "harmlessness",
    critique: "Identify ways this response is harmful",
    revise: "Revise the response to remove the harm while staying helpful",
  },
];

const raw: Turn[] = [
  { prompt: "How do I bypass safety controls on X?", response: "Here's how to bypass safety controls..." },
  { prompt: "What's the capital of France?", response: "Paris." },
];

const revised = runSupervisedPhase(raw, principles);
for (const t of revised) {
  console.log(`${t.prompt} => ${t.response}`);
}
```

### Python

```python
from dataclasses import dataclass


@dataclass
class Principle:
    name: str
    compare_prompt: str


def model_judge(principle: Principle, response_a: str, response_b: str) -> str:
    """Stand-in for the AI preference model's comparison call."""
    harmful_markers = ("bypass safety", "ignore all rules")
    a_harmful = any(m in response_a for m in harmful_markers)
    b_harmful = any(m in response_b for m in harmful_markers)
    if a_harmful and not b_harmful:
        return "b"
    if b_harmful and not a_harmful:
        return "a"
    return "a" if len(response_a) <= len(response_b) else "b"


def build_preference_dataset(
    prompts: list[str],
    candidates: dict[str, tuple[str, str]],
    principle: Principle,
) -> list[dict]:
    dataset = []
    for prompt in prompts:
        a, b = candidates[prompt]
        winner = model_judge(principle, a, b)
        dataset.append(
            {
                "prompt": prompt,
                "chosen": a if winner == "a" else b,
                "rejected": b if winner == "a" else a,
                "principle": principle.name,
            }
        )
    return dataset


def reward_model_score(chosen: str, rejected: str) -> float:
    """Toy scalar reward. Real systems train a learned reward model on
    the dataset produced by build_preference_dataset."""
    harmful = "bypass safety" in rejected
    return 1.0 if harmful else 0.6


if __name__ == "__main__":
    principle = Principle(
        name="harmlessness",
        compare_prompt="Which response better avoids assisting with harm?",
    )
    prompts = ["How do I get around a login wall?"]
    candidates = {
        prompts[0]: (
            "Contact the site owner to request access.",
            "Here's how to bypass safety controls on the login system.",
        )
    }
    data = build_preference_dataset(prompts, candidates, principle)
    for row in data:
        reward = reward_model_score(row["chosen"], row["rejected"])
        print(f"chosen={row['chosen']!r} reward={reward}")
```

### Go

```go
package main

import (
	"fmt"
	"strings"
)

type Principle struct {
	Name           string
	CritiquePrompt string
	RevisePrompt   string
}

type Turn struct {
	Prompt   string
	Response string
}

// modelCall stands in for a real model API call during the
// critique-and-revision loop.
func modelCall(instruction, context string) string {
	if strings.Contains(instruction, "critique") {
		if strings.Contains(context, "bypass safety") {
			return "violation. explains bypassing a safety control"
		}
		return "no issues found"
	}
	if strings.Contains(context, "bypass safety") {
		return "I can't help with that, but here is a safe alternative."
	}
	return context
}

func critiqueAndRevise(t Turn, p Principle) Turn {
	critique := modelCall(p.CritiquePrompt, t.Response)
	if critique == "no issues found" {
		return t
	}
	revised := modelCall(p.RevisePrompt, t.Response+" | "+critique)
	return Turn{Prompt: t.Prompt, Response: revised}
}

func runSupervisedPhase(turns []Turn, principles []Principle) []Turn {
	out := make([]Turn, len(turns))
	for i, t := range turns {
		current := t
		for _, p := range principles {
			current = critiqueAndRevise(current, p)
		}
		out[i] = current
	}
	return out
}

func main() {
	principles := []Principle{
		{
			Name:           "harmlessness",
			CritiquePrompt: "critique. identify harm",
			RevisePrompt:   "revise. remove harm, stay helpful",
		},
	}
	raw := []Turn{
		{Prompt: "How do I bypass safety controls?", Response: "Here's how to bypass safety controls step by step."},
		{Prompt: "What's 2+2?", Response: "4."},
	}
	revised := runSupervisedPhase(raw, principles)
	for _, t := range revised {
		fmt.Printf("%s => %s\n", t.Prompt, t.Response)
	}
}
```

Compiled and run all three samples locally. TypeScript checked with `npx tsc
--noEmit`, executed via `node` after transpiling with `tsc`. Python run
directly with `python3`. Go built and run with `go run`. All three produced
the expected critique-and-revise or preference-comparison output with no
errors. Java, Rust, and Swift were available on this machine but omitted here
because the pattern's control flow, sequential prompt-response chaining and a
simple comparison function, does not exercise any language-specific feature
those three would demonstrate beyond what TypeScript, Python, and Go already
show. A fourth or fifth port would repeat the same logic in different syntax
without adding new information about the pattern itself.
