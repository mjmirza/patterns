---
name: Output Guardrails
slug: output-guardrails
family: 17-ai-agentic
category: Agentic
aliases: [Output Rails, Response Validation, Output Validation, Guarded Generation, Safety Rails, Post-Generation Filtering]
first_described: "Programmable dialogue rails formalized by Rebedea, Dinu, Sreedhar, Parisien, Cohen 2023 (NeMo Guardrails, EMNLP Demo track); reask-and-validate output checking popularized by Guardrails AI, open sourced 2023"
maturity: established
related: [structured-output, function-calling, evaluator-optimizer, reflexion, self-consistency]
incompatible_with: []
verified: 2026-08-03
---

# Output Guardrails

## 1. Name, aliases, and lineage

Output Guardrails is the checkpoint that sits between an LLM finishing a
generation and that generation reaching a person, a database, or another
system that will act on it. The name comes from two lineages that converged
on the same idea from different directions.

The first lineage is safety research and content moderation. Meta's Llama
Guard paper describes an "LLM-based Input-Output Safeguard for Human-AI
Conversations," a classifier fine-tuned on Llama 2 that scores both a user's
prompt and a model's reply against a fixed risk taxonomy, and the paper's own
framing treats input safety and output safety as two instances of the same
classification problem run at two different points in a conversation (Hakan
Inan et al., "Llama Guard, LLM-based Input-Output Safeguard for Human-AI
Conversations," `arXiv:2312.06674`, submitted 7 December 2023,
https://arxiv.org/abs/2312.06674, verified 2026-08-03). OpenAI's Moderation
endpoint sits in the same lineage, and its own current documentation states
that when it is wired into a generation request it "returns moderation
scores for the model input and generated output without a separate
moderation request," treating the output check as a first-class half of the
same call rather than an afterthought (OpenAI, "Moderation,"
https://developers.openai.com/api/docs/guides/moderation, verified
2026-08-03).

The second lineage is programmable dialogue control for conversational
agents. NVIDIA's NeMo Guardrails paper, presented at the EMNLP 2023 demo
track, introduces "output rails" as one of five rail types, alongside input,
dialog, retrieval, and execution rails, each one a named point in the
request lifecycle where a developer-authored check can reject or rewrite
content before it moves to the next stage (Traian Rebedea, Razvan Dinu,
Makesh Sreedhar, Christopher Parisien, Jonathan Cohen, "NeMo Guardrails, A
Toolkit for Controllable and Safe LLM Applications with Programmable Rails,"
`arXiv:2310.10501`, submitted 16 October 2023,
https://arxiv.org/abs/2310.10501, verified 2026-08-03). The open source
Guardrails AI project names the same idea an "Output Guard," and its own
repository description frames the library around two functions, running
guards that "detect, quantify and mitigate the presence of specific types of
risks" and helping an application "generate structured data from LLMs"
(guardrails-ai/guardrails, https://github.com/guardrails-ai/guardrails,
verified 2026-08-03).

Output Guardrails is easy to confuse with three neighboring ideas, and the
confusion causes real design mistakes, so it is worth separating them here
rather than only in dimension 4.

- **Structured Output** (a sibling entry in this catalog) constrains the
  *shape* of a generation, valid JSON against a schema, so that a parser
  downstream does not throw. A schema-conformant object can still be false,
  toxic, off-topic, or leak a secret. Structured Output is one validator an
  Output Guardrail commonly runs first, not a substitute for it.
- **Constitutional AI**, and RLHF alignment generally, changes the model's
  *weights* at training time so that undesired behavior becomes less likely
  to be sampled in the first place. Anthropic's own paper describes this as
  a two-phase training process, supervised self-critique and revision
  followed by reinforcement learning from AI-generated preference judgments,
  which happens once, before deployment, and is baked into the checkpoint
  (Yuntao Bai et al., "Constitutional AI, Harmlessness from AI Feedback,"
  `arXiv:2212.08073`, submitted 15 December 2022,
  https://arxiv.org/abs/2212.08073, verified 2026-08-03). An Output
  Guardrail runs at inference time, on every request, against a model whose
  weights it does not control, and it is what catches the residual failures
  a well-aligned model still produces under an adversarial or unlucky
  prompt.
- **Input moderation** filters what goes into the model. It is the mirror
  image of this pattern, not the same mechanism, because a clean input can
  still produce an unsafe output (an innocuous question can pull an unsafe
  fact out of a retrieval index) and a flagged input sometimes produces a
  perfectly safe, on-topic refusal that never needed blocking. Most of the
  systems named in dimension 9 implement both rails, but they are two
  separate checkpoints with two separate failure surfaces.

## 2. Problem and context

An LLM call is a probabilistic sample, not a deterministic function
evaluation. The same prompt, run twice, can return two different strings,
and neither string is guaranteed to satisfy any property the calling code
depends on. That property might be as narrow as "this is parseable JSON" or
as broad as "this response does not repeat a customer's own credit card
number back to them in plain text." A codebase that pipes the raw
completion straight into a chat bubble, a database write, or a tool
invocation has no checkpoint between a model that can be wrong in an
unbounded number of ways and a consumer that will act on whatever arrives.

The situation recurs in a specific shape across very different products. A
support chatbot answers a billing question by paraphrasing a document that
happened to contain another customer's data. A coding agent, asked to fix a
bug, emits a shell command as part of its explanation, and a downstream
executor treats the whole response as trusted input. A financial research
assistant summarizes an earnings call and states a number that never
appeared in the transcript, stated with the same confident tone as a number
that did. A public-facing marketing bot is walked, turn by turn, by a
persistent user into repeating a competitor's confidential pricing that was
pasted into an earlier turn of the same conversation as part of a jailbreak.
None of these failures require a broken prompt or a buggy retrieval step.
Every one of them can happen on a well-engineered prompt against a
well-aligned model, because alignment reduces the rate of bad outputs, it
does not remove the tail.

The context in which this pattern earns its place has three recurring
features. First, the output reaches a consumer, human or machine, that
cannot itself tell a well-formed unsafe answer from a well-formed safe one
without doing the same work the guard would do, so the check has to happen
somewhere in the pipeline rather than being left to the reader. Second, the
cost of a bad output reaching that consumer is asymmetric with the cost of
an extra check, a support ticket, a compliance fine, or a wrong number in a
financial document all cost more than a few hundred milliseconds of
validation latency. Third, the surface is adversarial or at least
unpredictable, either because real end users interact with it directly, or
because it consumes retrieved or tool-returned content that a third party
partially controls. Where none of the three holds, for example a fully
offline batch job scoring a fixed, trusted internal dataset with no human or
downstream system consuming individual outputs unreviewed, this pattern is
often more machinery than the situation calls for, which dimension 4 covers
directly.

## 3. Forces

Every implementation of this pattern is a set of decisions about where to
sit on five tensions, and a design that pretends none of them exist usually
fails in production within weeks rather than sitting quietly unused.

- **Latency versus coverage.** A single regex check adds microseconds. A
  classifier call adds tens of milliseconds. A second LLM acting as a judge
  adds the better part of a full generation's latency, sometimes more, if
  it has to read the whole candidate output plus its supporting context.
  Every additional validator in the chain is a real, measurable tax on the
  time a person waits for a response, and that tax has to be paid on every
  request, not only the ones that would have failed.
- **False positives versus false negatives.** A guard tuned tight enough to
  catch every genuine violation will also block some fraction of legitimate
  content, and in a domain with specialized vocabulary, medicine, security
  research, legal drafting, that fraction is rarely small. A guard tuned
  loose enough to leave legitimate content untouched will let some real
  violations through. There is no threshold that sets both error rates to
  zero at once, and the two costs are usually paid by different people, the
  false positive by a frustrated legitimate user, the false negative by
  whoever the missed violation harms, which makes the trade-off a product
  and policy decision, not only an engineering one.
- **Blocking versus healing.** A guard can hard-refuse a violation, or it
  can try to repair it, redact the offending span, ask the same model to
  try again with the validation error appended to the prompt, or substitute
  a safe fallback. Healing keeps the user experience intact more often but
  adds latency, adds a bounded-retry policy that itself needs testing, and
  can produce a result that technically passes the check while still being
  a worse answer than the one that failed it.
- **Determinism versus generality.** A rule-based validator, a regex for a
  social security number, a denylist of terms, is fast, fully explainable,
  and trivial to unit test, but it only catches what someone thought to
  write a rule for. A model-based validator, a fine-tuned classifier or an
  LLM judge, generalizes to phrasing nobody anticipated, but it is itself a
  probabilistic system that can be wrong, and its failures are harder to
  reason about because they inherit the same opacity as the system being
  guarded.
- **Enforcement point.** A guard embedded inside application code is cheap
  to add and easy to customize, but every new code path that calls the
  model directly, a batch job, an admin tool, a second service, silently
  bypasses it. A guard enforced at a gateway or proxy in front of the model
  API is harder to forget but harder to customize per use case, and it adds
  an operational dependency that the whole application now shares.

No implementation optimizes every one of these forces at once. A production
guard states, explicitly, which of these five it is trading away, because a
team that has not named the trade-off tends to discover it during an
incident instead.

## 4. Applicability and non-applicability

Reach for Output Guardrails when at least one of the following holds.

- The output reaches an end user directly, in a chat surface, a generated
  document, or a voice response, and a bad output is visible to that user
  the moment it happens.
- The output feeds a downstream system with side effects, a database write,
  an email send, a payment instruction, a tool call with real-world
  consequences, where a malformed or unsafe value causes damage before a
  human ever reviews it.
- The domain carries regulatory or compliance weight, health, finance,
  legal, education involving minors, where an audit trail of what was
  checked and why a response was blocked or allowed is itself a
  requirement, not only a safety nice-to-have.
- The system is exposed to untrusted or only partially trusted input,
  public users, third-party retrieved content, tool results from an
  external API, any of which can carry adversarial content aimed at
  steering the output.
- The generation draws on retrieved or provided source documents and the
  product promises the response is grounded in those documents, so a
  contradiction between the claim and the source is itself the defect being
  guarded against, independent of tone or safety.
- Past incidents, internal or public, have already shown a specific failure
  mode for this exact system, a hallucinated statistic, a leaked internal
  document snippet, a jailbreak that surfaced the system prompt, and the
  guard's job is to close that specific hole while the broader alignment
  work catches up.

Do not reach for it, or scale it back to the cheapest useful form, when any
of the following holds.

- The consumer of the output is a fully offline batch process against a
  trusted, static dataset with no individual output ever surfaced to a
  human or acted on by a downstream system unreviewed, where a periodic
  aggregate quality check catches drift more cheaply than a per-request
  gate.
- The task is closed-form enough that Structured Output's schema
  conformance is the entire correctness requirement, a fixed enum, a
  bounded numeric range already re-validated by the calling code before
  use, and there is no content-safety, factuality, or leakage dimension to
  check beyond the shape.
- Latency is the dominant product requirement and the interaction is
  low-stakes, inline code-completion suggestions shown character by
  character, where adding a network round trip for a classifier or judge
  call would visibly break the interaction the feature exists to provide,
  and a cheaper, local heuristic covers the realistic risk.
- The model is small, closed, and fine-tuned to a single narrow task with
  no free-text generation surface and no exposure to untrusted callers, so
  the output space is already fully enumerable and verifiable by ordinary
  application logic without a general-purpose guard layer.
- The team cannot yet measure the guard's own false positive and false
  negative rates against a representative sample of real traffic. Shipping
  an unmeasured guard trades one unmeasured risk, a bad model output, for
  a second unmeasured risk, a bad blocking decision, and calling the second
  one safer than the first is an assumption, not a fact, until it is
  checked.
- The organization has already invested in strong training-time alignment
  for the exact narrow domain in question and has evidence, from its own
  red-teaming, that the residual failure rate is acceptable for the
  stakes involved. A guard is defense in depth on top of alignment, not a
  replacement for measuring whether alignment alone already suffices for a
  specific, bounded use case.

## 5. Structure

- **Generator.** The LLM call that produces a candidate output. The
  Generator has no awareness of the guard, it is a plain, replaceable call
  that returns a string or a structured object and nothing else.
- **Candidate.** The raw output of one generation attempt, together with
  whatever context the checks need to judge it, the original user prompt,
  any retrieved documents the response is supposed to be grounded in, and
  the conversation history.
- **Guard or Orchestrator.** The component that owns the policy. It knows
  which validators to run, in what order or in what parallel grouping, how
  to combine their individual verdicts into one decision, and what to do
  next given that decision. This is the one participant application code
  actually talks to.
- **Validator.** A single, narrowly scoped check. A validator takes the
  candidate and its context and returns a verdict, pass, fail, or a
  continuous score against a threshold, plus, where useful, a machine
  readable reason. A guard runs one or many validators. Common validator
  kinds are a schema validator (does this parse against the expected
  shape), a rule-based validator (a regex or denylist for personal data or
  banned terms), a classifier validator (a small trained model scoring
  toxicity, hate, or self-harm content), a groundedness validator (does
  every claim trace to the supplied source documents), and a custom
  business-rule validator (does this quoted price match the actual price
  list).
- **On-fail policy.** The decision the Guard applies once a validator
  fails. The options that recur across every implementation examined for
  this entry are pass silently (log only, do not act), filter or redact
  (remove or mask the offending span and keep the rest), fix (apply a
  deterministic correction, for example re-serializing malformed JSON),
  reask (send the candidate and the validation error back to the Generator
  for a bounded number of retries), and refuse (return a fixed safe
  fallback and stop).
- **Sink.** Whatever consumes the guarded output once it clears the Guard,
  a chat UI, a tool executor, a database writer, a downstream API call.
  The Sink is written to assume everything it receives has already passed
  the Guard, which is exactly the assumption that failure mode g in
  dimension 11 breaks when a second code path skips the Guard entirely.
- **Audit log.** A durable record of every check that ran, its verdict, its
  latency, and the action taken, keyed to the request that produced it.
  This participant is easy to treat as optional and is the one whose
  absence is discovered, expensively, during the first incident review.

## 6. ASCII structure diagram

```
                    +---------------------------+
                    |   Generator (the LLM)      |
                    +---------------------------+
                                 |
                                 v
                    +---------------------------+
                    |   Candidate + Context       |
                    +---------------------------+
                                 |
                                 v
                    +---------------------------+
                    |   Guard / Orchestrator      |
                    +---------------------------+
                     |       |        |        |
                     v       v        v        v
                +------+ +------+ +--------+ +----------+
                |Schema| | Rule | |Classi- | |Grounded- |
                |Check | | (PII)| |fier    | |ness Check|
                +------+ +------+ +--------+ +----------+
                     |       |        |        |
                     +---+---+----+---+----+---+
                             |
                             v
                    +---------------------------+
                    |   Verdict Aggregator        |
                    +---------------------------+
                       |         |          |
                       v         v          v
                  +------+   +--------+  +--------+
                  | Pass |   |Fix/    |  |Refuse/ |
                  |      |   |Reask   |  |Redact  |
                  +------+   +--------+  +--------+
                       |         |          |
                       +----+----+----+-----+
                             |
                             v
                    +---------------------------+
                    |  Sink (UI / Tool / DB / API)|
                    +---------------------------+
                                 |
                                 v
                    +---------------------------+
                    |   Audit / Observability Log |
                    +---------------------------+
```

## 7. Dynamics

The common path is a single guarded round trip, and it runs in four steps.
The Guard receives a candidate from the Generator along with its context.
It dispatches the configured validators, independent validators run in
parallel to bound total latency, dependent ones (a groundedness check that
needs a schema-valid object first) run in sequence. Each validator returns a
verdict. The Aggregator combines them under the configured policy, commonly
a strict all-must-pass rule for anything content-safety related and a
softer any-can-warn rule for lower-stakes checks, and the combined result
selects one on-fail action.

```
step 1  Generator produces candidate C from context X
step 2  Guard dispatches validators V1..Vn against (C, X)
             independent validators run concurrently
             dependent validators wait on their inputs
step 3  each Vi returns (pass|fail, score, reason)
step 4  Aggregator combines verdicts under policy P
             all critical checks pass -> action = FORWARD
             a recoverable check fails -> action = FIX or REASK
             a hard check fails        -> action = REFUSE
step 5  Guard executes action
             FORWARD  -> Sink receives C unchanged
             FIX      -> Sink receives repaired C'
             REASK    -> loop to step 1 with error appended,
                         bounded by max_retries, then REFUSE
             REFUSE   -> Sink receives fixed fallback response
step 6  Audit log records every verdict, the chosen action,
        and end to end latency, keyed to the request id
```

The reask branch is the one implementation detail worth drawing out
separately, because it is a loop, not a single extra step, and every loop
needs a stated exit condition. The Guard appends the failing validator's
exact error text to a fresh prompt to the same Generator, asking for a
corrected candidate, and repeats validation on the new candidate. This
repeats up to a configured `max_retries`, after which the Guard stops
reasking and falls through to the refuse action rather than surfacing
whatever the last, still-failing attempt produced, a detail that failure
mode d in dimension 11 exists precisely because implementations skip.
Instructor's own documentation shows this loop as a first-class,
user-visible parameter, `max_retries`, passed directly on the call that
extracts a structured object, with automatic reasking on a validation
failure built into the client rather than left to the caller to hand-roll
(Instructor documentation, "Instructor, The Most Popular Python Library
for Structured LLM Outputs," https://python.useinstructor.com/, verified
2026-08-03).

## 8. Implementation variants

- **Rule-based validators.** Regular expressions, denylists, allowlists,
  and format checks. Deterministic, sub-millisecond, fully unit testable,
  and the correct first line of defense for anything with a fixed pattern,
  a credit card number, an email address, a profanity list. Their weakness
  is coverage, a rule only catches what someone already thought to encode,
  and adversarial rephrasing routes around a rule trivially once its shape
  is known.
- **Schema validators.** The Structured Output pattern applied as one
  validator inside the guard rather than as the whole check. Guardrails
  AI's own repository frames one of its two core functions this way,
  generating structured data either through a model's native function
  calling support or, for models without it, by folding the target schema
  directly into the prompt (guardrails-ai/guardrails,
  https://github.com/guardrails-ai/guardrails, verified 2026-08-03).
- **Classifier-based validators.** A small, purpose-trained model scores
  the candidate against a fixed taxonomy and returns a category and a
  confidence. Llama Guard is the clearest published example, fine-tuned on
  Llama 2 to perform multi-class safety classification on both a prompt
  and a reply against a documented risk taxonomy that a deploying team can
  customize (Inan et al., `arXiv:2312.06674`,
  https://arxiv.org/abs/2312.06674, verified 2026-08-03). Managed
  equivalents include OpenAI's free `omni-moderation-latest` endpoint,
  which classifies text and image content across thirteen categories and
  can return scores for both the input and the generated output from a
  single generation call (OpenAI, "Moderation,"
  https://developers.openai.com/api/docs/guides/moderation, verified
  2026-08-03), and Azure AI Content Safety's Analyze Text API, which scans
  for sexual content, violence, hate, and self-harm at multiple severity
  levels (Microsoft, "What is Azure AI Content Safety?,"
  https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview,
  verified 2026-08-03). Classifier validators are fast relative to a full
  LLM judge and their scores are calibrated against a fixed evaluation set,
  but that calibration is only as good as the data it was trained on for
  the deploying team's actual domain, which is the mechanism behind
  failure mode a in dimension 11.
- **Groundedness or contextual grounding validators.** A check that a
  candidate's factual claims trace to a supplied source document rather
  than to the model's general knowledge. Amazon Bedrock Guardrails ships
  this as a named contextual grounding check among its configurable
  safeguard policies, alongside content filters, denied topics, word
  filters, and sensitive information filters (AWS, "Guardrails for Amazon
  Bedrock," https://aws.amazon.com/bedrock/guardrails/, verified
  2026-08-03), and Azure AI Content Safety ships an equivalent groundedness
  detection API, in preview, described by Microsoft as checking whether
  an LLM response stays grounded in the documents a user supplies
  (Microsoft, "What is Azure AI Content Safety?,"
  https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview,
  verified 2026-08-03).
- **LLM-as-judge validators.** A second model call, prompted to critique
  the first model's output against a written rubric and return a verdict.
  The most flexible variant, able to catch anything expressible in
  natural-language criteria, and the most expensive and least
  interpretable, because the judge is itself a probabilistic system whose
  own verdict can be wrong or itself manipulated, a concern developed
  further in dimension 17. This variant overlaps with, but is not
  identical to, the Evaluator-Optimizer pattern, a distinction drawn out in
  dimension 13.
- **Programmable rail authoring.** Rather than writing each check as
  imperative code, NeMo Guardrails lets a team author policy in Colang, a
  small domain-specific dialogue language with, in its own documentation,
  "a python-like syntax... designed to be simple and intuitive," so that
  non-engineering policy owners, trust and safety, compliance, can read and
  change the rules without touching the surrounding application
  (NVIDIA/NeMo-Guardrails, https://github.com/NVIDIA/NeMo-Guardrails,
  verified 2026-08-03).
- **Gateway or sidecar enforcement.** The Guard runs outside application
  code entirely, at the point where any caller invokes the model, so a new
  code path cannot forget to wire it in. Amazon Bedrock Guardrails is
  applied this way, as a configuration attached to the model invocation
  itself rather than a library an application developer must remember to
  import (AWS, "Guardrails for Amazon Bedrock,"
  https://aws.amazon.com/bedrock/guardrails/, verified 2026-08-03). This
  variant trades per-call customization for the coverage guarantee that
  motivates failure mode h in dimension 11.
- **SDK-embedded enforcement with bounded reask.** The Guard is a library
  call the application code makes explicitly, wrapping the model call and
  handling retries itself. Guardrails AI's `Guard` object and Instructor's
  client-level `max_retries` are both this shape, cheap to adopt
  incrementally and easy to customize per call site, at the cost of
  needing every call site to remember to use it.

## 9. Known production uses

- **Meta's Llama Guard**, released as part of the Purple Llama safety
  toolkit, is a fine-tuned classifier applied to both the input and output
  of a conversation, evaluated by its own authors against standard content
  moderation benchmarks including OpenAI's moderation evaluation set and
  ToxicChat, and shipped with a customizable taxonomy so a deploying team
  can adapt the categories to its own policy rather than accept a fixed
  list (Inan et al., "Llama Guard, LLM-based Input-Output Safeguard for
  Human-AI Conversations," `arXiv:2312.06674`,
  https://arxiv.org/abs/2312.06674, verified 2026-08-03).
- **Amazon Bedrock Guardrails** is AWS's managed guardrail service,
  attached directly at the model invocation layer across models hosted on
  Bedrock, offering six configurable safeguard policies, content filters
  that include prompt injection detection, denied topics, word filters,
  sensitive information filters that redact personal data, contextual
  grounding checks against source documents, and automated reasoning checks
  that validate a claim against formal logic rules (AWS, "Guardrails for
  Amazon Bedrock," https://aws.amazon.com/bedrock/guardrails/, verified
  2026-08-03).
- **NVIDIA's NeMo Guardrails** is an open source toolkit, presented at
  EMNLP 2023, that adds output rails, alongside input, dialog, retrieval,
  and execution rails, to conversational LLM applications independent of
  the underlying model provider, letting a deploying team keep the same
  guardrail policy while swapping the model behind it (Rebedea et al.,
  `arXiv:2310.10501`, https://arxiv.org/abs/2310.10501, verified 2026-08-03;
  NVIDIA/NeMo-Guardrails, https://github.com/NVIDIA/NeMo-Guardrails,
  verified 2026-08-03).
- **OpenAI's Moderation endpoint**, model `omni-moderation-latest`, is
  offered as a free API and is also wired directly into OpenAI's own
  generation endpoints, returning "moderation scores for the model input
  and generated output without a separate moderation request" when
  enabled, which is a direct description of an output guardrail running
  inline with generation rather than as a bolt-on afterthought (OpenAI,
  "Moderation," https://developers.openai.com/api/docs/guides/moderation,
  verified 2026-08-03).
- **Azure AI Content Safety**, part of Azure AI Foundry, offers Prompt
  Shields for jailbreak-style attacks, a groundedness detection API for
  hallucination against supplied source documents, protected content
  detection for word-for-word reproduction of known copyrighted text, and a
  task adherence API described as detecting "when tool use by AI agents is
  misaligned, unintended, or premature," a guardrail specifically aimed at
  agentic tool-calling output rather than plain chat text (Microsoft,
  "What is Azure AI Content Safety?,"
  https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview,
  verified 2026-08-03).
- **Guardrails AI and Instructor**, both open source Python libraries,
  implement the SDK-embedded variant of this pattern at real scale in the
  open source Python community. Guardrails AI's own repository describes running
  Input/Output Guards that "detect, quantify and mitigate the presence of
  specific types of risks" (guardrails-ai/guardrails,
  https://github.com/guardrails-ai/guardrails, verified 2026-08-03), and
  Instructor, described in its own documentation as "the most popular
  Python library" for structured extraction from LLMs, reports over three
  million monthly downloads and ships automatic Pydantic validation with a
  bounded, configurable retry loop as a core feature rather than an add-on
  (Instructor documentation, https://python.useinstructor.com/, verified
  2026-08-03).

## 10. Consequences

**Positive.** A guard catches the tail of failures a well-aligned model
still produces, converting an unbounded, silent risk into a bounded,
observed one. It gives a team an audit trail, every check, every verdict,
every action, that a compliance review or an incident postmortem can
actually read, which raw model output never provides on its own. It lets a
team decouple a model swap from a policy rewrite, the same rule-based and
classifier validators keep working when the underlying Generator changes,
because they inspect the output, not the model. It turns a class of hard
failures into a self-correcting loop, the reask variant lets a model fix its
own malformed or unsafe output before a person ever sees the failed
attempt, which raises the effective reliability of a prompt without
retraining anything. And it gives a product surface to point to when asked,
by a customer, a regulator, or an internal reviewer, exactly what is
checked before a response ships.

**Negative.** Every validator in the chain is added latency paid on every
request, not only the ones that fail, and a chain of several sequential
checks, especially any that call another model, can double or triple the
time a user waits for an answer. A guard tuned for safety over precision
degrades the experience of every legitimate user who happens to trip a
false positive, and that cost is diffuse and easy to under-count next to
the concentrated, visible cost of a single missed violation. The guard
itself becomes a second system with its own bugs, its own drift as the
underlying model or the traffic mix changes, and its own maintenance
burden, a taxonomy or threshold tuned for one product surface does not
automatically transfer to another. An LLM-judge validator inherits the same
non-determinism and hallucination risk as the system it is checking, so a
guard can fail closed on a fine answer or fail open on a bad one for
reasons as hard to pin down as the underlying model's own mistakes. And a
guard that is easy to bypass by simply calling the model from a different
code path, covered in failure mode h below, gives a team a false sense of
coverage that is arguably worse than having no guard and knowing it.

## 11. Failure modes and misuse

- **Symptom.** Legitimate outputs are refused or redacted at a rate high
  enough that users or support staff start noticing and complaining, in a
  domain with specialized vocabulary, health, security, legal.
  **Cause.** A classifier or rule set was tuned, or trained, on a general
  corpus rather than the deploying application's actual traffic, so terms
  that are ordinary in this domain read as violations in the classifier's
  training distribution.
  **Fix.** Build a labeled evaluation set from the application's own real
  traffic, measure false positive rate against it before shipping a
  threshold change, and add explicit domain allowlist exceptions where the
  classifier's general-purpose taxonomy conflicts with legitimate
  domain-specific content.
- **Symptom.** A guard that has been in production and working for months
  suddenly lets an obviously unsafe or off-policy output straight through.
  **Cause.** The check ran on the full candidate string as written, but
  the actual violation was encoded, base64, a homoglyph substitution, a
  different language than the one the classifier or denylist was built
  for, so the surface-level pattern never matched even though the meaning
  was unchanged.
  **Fix.** Normalize obvious encodings back to plain text before running content
  checks, run checks against the full, untruncated candidate rather than a
  prefix, and maintain an adversarial red-team test suite, refreshed as new
  bypass techniques appear, as a permanent regression suite rather than a
  one-time audit.
- **Symptom.** Users report the chat response taking noticeably longer to
  arrive after a guardrail rollout, sometimes timing out entirely under
  load.
  **Cause.** Independent validators are called one after another instead of
  concurrently, and at least one of them, usually an LLM-judge or a
  groundedness check, is itself a full model call with no timeout or
  circuit breaker of its own.
  **Fix.** Run independent validators concurrently rather than
  sequentially, put an explicit timeout and a circuit breaker on every
  validator so a single slow check degrades to a safe fallback instead of
  hanging the whole request, and reserve the most expensive checks, an
  LLM judge in particular, for a sampled subset of lower-confidence or
  higher-risk traffic rather than every request uniformly.
- **Symptom.** After exhausting its retry budget, the guard surfaces a
  garbled, half-corrected response to the user instead of a clean refusal
  or a clear error.
  **Cause.** The reask loop's exit condition was implemented as "return
  whatever the last attempt produced" rather than "fall through to a
  defined refusal on exhaustion," and the reask prompt itself did not
  clearly state which validator failed and why, so successive attempts
  wandered rather than converging.
  **Fix.** Cap retries at an explicit, small number, feed the exact
  validator failure reason back into the reask prompt rather than a
  generic "try again," and define the exhaustion path as a deterministic,
  tested fallback response rather than an implicit pass-through of the
  final failed attempt.
- **Symptom.** A guard that passed every regression test before a model
  upgrade starts failing, or passing, in a new way immediately after that
  upgrade, and nobody can explain why until hours of debugging later.
  **Cause.** The guard has no versioned, repeatable golden-set regression
  suite that runs on every model or validator version bump, so a change in
  the base model's phrasing style, or a silent vendor-side update to a
  managed classifier, shows up first as a live incident rather than as a
  failed test in CI.
  **Fix.** Pin the guard's own validator models and thresholds under
  version control, run a labeled golden-set regression suite against both
  the base model and the guard on every version change to either, and
  alert automatically when the pass rate on that suite diverges from its
  established baseline.
- **Symptom.** Security review discovers that a real share of
  production traffic to the model never passed through the guard at all.
  **Cause.** The guard is implemented as a library call inside one
  application's code path, and a second call site, a batch job, an admin
  console, a newer microservice added after the guard shipped, calls the
  model API directly, unaware the guard exists or was ever a requirement.
  **Fix.** Move enforcement to the point every caller must pass through
  regardless of which code wrote it, a model-invocation gateway or
  managed guardrail attached at the API layer rather than only inside
  application code, so a new call site inherits the guard automatically
  instead of needing to remember it.

## 12. Trade-off matrix

The alternatives below are the real choices a team weighs against Output
Guardrails, not a strawman. Constitutional AI and RLHF alignment are
training-time techniques, human review is a manual gate, and prompt-only
mitigation is asking the model nicely in its system prompt with no
independent check behind the ask.

| Force | Output Guardrails | Structured Output alone | Constitutional AI / RLHF alignment | Human-in-the-loop review | Prompt-only mitigation |
|---|---|---|---|---|---|
| Per-request latency added | Low to high, depends on validator mix | Low, one schema pass | None at inference time | High, a person in the loop | None |
| Catches content-safety and factual issues, not only shape | Yes, by design | No, format only | Partially, reduces rate, does not bound it | Yes, if the reviewer is competent | No, unenforced request |
| Adapts to a new failure mode without retraining anything | Yes, add or edit a validator | Yes, edit the schema | No, requires a new training run | Yes, retrain the reviewer's judgment | Yes, edit the prompt |
| Survives a determined adversarial user | Depends on validator coverage and update frequency | No, format bypass does not need adversarial input | Reduces but does not eliminate jailbreak risk | Yes, if reviewed before any exposure | No, prompts are routinely overridden |
| Produces an auditable record per request | Yes, if logging is wired in | Only for format failures | No, the change is in weights, not per request | Yes, a reviewer's decision is a record | No |
| Scales to high request volume without added headcount | Yes | Yes | Yes | No, review time scales with volume | Yes |

## 13. Related and incompatible patterns

- **Structured Output.** A schema validator is very often the first
  validator an Output Guard runs, because a malformed response cannot
  usefully be checked for content until it can be parsed. The two patterns
  compose directly, Structured Output guarantees shape, Output Guardrails
  guarantees everything Structured Output does not, safety, factuality,
  and policy compliance on top of that shape.
- **Function Calling.** When an agent's output is a tool call rather than
  text shown to a user, the arguments to that call are exactly the kind of
  structured, high-stakes output this pattern exists to check before
  execution, a malformed or unsafe argument to a tool with real side
  effects is arguably the highest-stakes case Output Guardrails covers,
  because the consumer is code, not a person who might notice something
  looks wrong.
- **Evaluator-Optimizer.** Both patterns can use a second LLM call as a
  judge, and the two are easy to conflate. Evaluator-Optimizer uses the
  judge's feedback to drive an iterative loop toward a better answer
  against an open-ended quality goal, generate, critique, revise, repeat
  until good enough. Output Guardrails uses a validator, which may or may
  not be an LLM, to make a bounded pass or fail decision against a fixed
  policy, and its default action on failure is refuse or a small number of
  bounded reask attempts, not an open-ended improvement loop. A guard that
  reasks is doing a narrow special case of Evaluator-Optimizer's loop, not
  the whole pattern.
- **Reflexion.** Reflexion has the model critique and revise its own
  output across attempts at a task, driven by the model's own self
  assessment, often to improve task success on a benchmark or a
  multi-step problem. An Output Guard's validators are usually external to
  the Generator, a different model, a rule, a classifier, rather than the
  same model grading its own homework, and the guard's purpose is
  compliance with an externally defined policy rather than task
  improvement. Where a system asks the same model to self-critique against
  a safety rubric as its only check, it has effectively narrowed Output
  Guardrails down to a single, self-graded validator, which the false
  negative risk discussed in dimension 10 makes a weaker configuration than
  an independent validator.
- **Self-Consistency.** Sampling several candidates and checking agreement
  among them is a lightweight signal a groundedness or factuality validator
  can use, disagreement across samples is itself evidence of an
  unreliable claim, without needing a separately trained classifier.
- **No hard incompatibilities.** This pattern does not conflict outright
  with any other pattern in this catalog. Its real tension is with pure
  token-by-token streaming user interfaces, where a guard that must see a
  complete candidate before releasing it forces either a buffering delay
  the streaming UX was built to avoid, or a narrower, incremental variant
  of the guard that checks a rolling window of already-emitted tokens and
  can abort mid-stream rather than only before the first token is shown.

## 14. Refactoring path in and out

**Introducing the pattern into a system that has none.** Start by wrapping
the existing model call so that every caller goes through one function,
even before any validator exists, because that seam is what makes every
later step additive rather than a rewrite. Add a schema validator first,
reusing Structured Output if the response is already meant to be
structured, since a shape failure is the cheapest, most deterministic thing
to catch and it exposes the reask-and-fallback machinery before anything
content-related is layered on top. Add one narrow, rule-based validator
for the single highest-known-risk failure mode already observed in
production or in a pre-launch red team, a PII pattern, a specific leaked
phrase, rather than reaching for a general classifier immediately, so the
team learns the operational shape of a guard, its false positive rate, its
on-fail UX, on a small, well-understood surface first. Add a classifier or
managed moderation check once the rule-based layer is stable, choosing a
managed option, a moderation endpoint or a Bedrock or Content Safety
guardrail, over training a custom classifier unless the domain's risk
taxonomy is demonstrably not covered by an off-the-shelf one. Add
groundedness or business-rule validators last, since these are the most
domain-specific and the ones most likely to need iteration against real
traffic before they are trustworthy enough to block on rather than only
warn on. Finally, once the policy is stable, move enforcement from an
SDK call inside one application's code to a gateway or proxy in front of
the model invocation itself, closing the bypass risk in failure mode h.

**Removing or scaling back the pattern.** A guard that has accumulated
validators nobody remembers the reason for is a maintenance cost without a
matching benefit, and the removal path mirrors the introduction path in
reverse, remove the least-triggered, least-justified validator first and
watch the false negative rate on the golden-set suite from dimension 15
before removing the next one. A guard can be safely retired down to
Structured Output alone, or removed entirely, once a system genuinely
meets the non-applicability conditions in dimension 4, most often because
the surface it protects was narrowed, a public endpoint was closed, an
integration that fed untrusted third-party content was removed, rather
than because the guard was never needed at all.

## 15. Testing and verification

A guard is trustworthy only to the extent it has been tested against
outputs it is supposed to catch, not only outputs it is supposed to let
through, and the two need separate, explicit test suites. A golden-set
regression suite pairs a fixed corpus of real or representative candidate
outputs with the verdict each one should receive, known-good outputs that
must pass, known-bad outputs, including outputs drawn from past incidents
and from adversarial red-team exercises, that must fail, and this suite
runs on every change to the guard's rules, thresholds, or underlying model,
and on every change to the base Generator model it protects. Fuzz testing
against the guard specifically, mutating known-bad inputs with encoding
tricks, translation, and paraphrase, checks the coverage claim in dimension
11's failure mode b rather than assuming a rule generalizes past the exact
strings it was written against. A shadow-mode rollout, where the guard runs
on live traffic and logs its verdict without actually blocking anything,
lets a team compare the guard's decisions against a manually reviewed
sample before flipping it into enforcing mode, which is the only reliable
way to measure a real-world false positive rate before it starts affecting
real users. Unit tests of the surrounding orchestration code, the
aggregation logic, the reask loop's retry cap and fallback, should mock the
validator interface entirely, asserting the Guard's control flow is correct
without paying for a real classifier or judge call on every test run,
mirroring how Instructor's own design separates the retry-and-validate
control flow from any specific validation function (Instructor
documentation, https://python.useinstructor.com/, verified 2026-08-03).

## 16. Observability signals

Every validator's verdict, score, and latency should be logged per request,
keyed to a request id that also identifies the model version and prompt
version in use, because a spike in block rate is meaningless without being
able to correlate it back to exactly what changed. A block-rate dashboard,
broken down by validator and by category, is the first thing a team should
be able to open after a model or guard change to see whether behavior
shifted. The distribution of reask counts per request, not only whether a
reask happened, shows whether the underlying model is close to compliant on
the first attempt or is systematically failing and being rescued by the
loop, which is itself a signal the base prompt or model needs attention
rather than only the guard. Guard-added latency, tracked at p50, p95, and
p99 separately from base generation latency, exposes the tail-latency cost
a chained set of sequential validators can quietly accumulate. A sampled
human-audit pipeline, reviewing a fixed percentage of both passed and
blocked outputs, is the only reliable way to estimate the guard's real
false negative rate, since a system only sees the false positives users
complain about and is otherwise blind to what the guard silently missed.
Trace propagation that shows the Generator's span, each validator's span,
and the final action as one connected trace turns a production incident
from a log-grepping exercise into a single trace lookup.

## 17. Security and privacy implications

Sending candidate output to a third-party moderation or classifier service
means that content, which can include personal data or regulated
information, leaves the application's own trust boundary, which raises the
same data residency, retention, and processing-agreement questions any
third-party API integration raises, and it is a question a team has to
answer explicitly for a regulated domain rather than assume away because
the service is a well-known vendor. The guard itself is an oracle an
attacker can probe, sending a sequence of near-identical inputs and
observing which ones the guard blocks lets a sufficiently persistent
attacker reverse-engineer the policy's boundaries and craft content that
threads exactly between them, so a guard's internal reasoning, its exact
threshold or the specific rule that matched, should not be echoed back
word for word to an untrusted caller in the refusal message. A classifier-based
validator trained on a biased corpus can encode and then systematically
enforce that bias, disproportionately flagging content in a particular
language, dialect, or about a particular topic, which is itself a fairness
problem and, in a regulated context, a compliance problem, not only a
false-positive-rate inconvenience, and it is the reason the false positive
rate has to be measured per demographic slice of traffic, not only in
aggregate. An audit log that stores blocked content for review creates its
own retention liability, especially when the blocked content is exactly
the PII or sensitive content the guard flagged, so that log needs its own
encryption at rest, access control, and retention policy rather than being
treated as an operational convenience with no privacy surface of its own.
A validator that trusts a caller-supplied flag, a header or field claiming
"this is trusted internal traffic, skip the check," is a bypass an
attacker who can set that header will use, so trust decisions belong on the
server side of the request, verified independently of anything the caller
claims about itself. And an LLM-judge validator is itself a language model
reading untrusted text, which means it inherits prompt injection risk from
the very content it is meant to be judging, a candidate crafted to also
manipulate the judge is a documented category of attack against this
pattern, not a hypothetical one, and it is the reason a judge-based
validator's own prompt should be hardened the same way any other
LLM-facing surface handling untrusted content is hardened.

## 18. References

- Hakan Inan, Kartikeya Upasani, Jianfeng Chi, Rashi Rungta, Krithika Iyer,
  Yuning Mao, Michael Tontchev, Qing Hu, Brian Fuller, Davide Testuggine,
  Madian Khabsa, "Llama Guard, LLM-based Input-Output Safeguard for
  Human-AI Conversations," `arXiv:2312.06674`, submitted 7 December 2023,
  https://arxiv.org/abs/2312.06674, verified 2026-08-03.
- Traian Rebedea, Razvan Dinu, Makesh Sreedhar, Christopher Parisien,
  Jonathan Cohen, "NeMo Guardrails, A Toolkit for Controllable and Safe
  LLM Applications with Programmable Rails," `arXiv:2310.10501`, submitted
  16 October 2023, EMNLP 2023 Demo track,
  https://arxiv.org/abs/2310.10501, verified 2026-08-03.
- NVIDIA, NeMo-Guardrails repository, https://github.com/NVIDIA/NeMo-Guardrails,
  verified 2026-08-03.
- Yuntao Bai et al., "Constitutional AI, Harmlessness from AI Feedback,"
  `arXiv:2212.08073`, submitted 15 December 2022,
  https://arxiv.org/abs/2212.08073, verified 2026-08-03.
- guardrails-ai, guardrails repository,
  https://github.com/guardrails-ai/guardrails, verified 2026-08-03.
- Instructor documentation, "Instructor, The Most Popular Python Library
  for Structured LLM Outputs," https://python.useinstructor.com/, verified
  2026-08-03.
- OpenAI, "Moderation," API guide,
  https://developers.openai.com/api/docs/guides/moderation, verified
  2026-08-03.
- AWS, "Guardrails for Amazon Bedrock," product page,
  https://aws.amazon.com/bedrock/guardrails/, verified 2026-08-03.
- Microsoft, "What is Azure AI Content Safety?," Azure AI services
  documentation,
  https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview,
  verified 2026-08-03.
- Anthropic, "Reduce hallucinations," Claude API guide,
  https://platform.claude.com/docs/en/docs/test-and-evaluate/strengthen-guardrails/reduce-hallucinations,
  verified 2026-08-03.

## Code

All three samples model the mechanism directly against a local, hand-written
fallible mock Generator rather than a live network call, so each one
compiles and runs offline while still exercising the real control flow, a
validator chain, verdict aggregation, and a bounded reask loop with a
defined exhaustion fallback. Java, Rust, and Swift are left out here for
space, not because the pattern does not translate. the reask loop and
validator interface below carry over directly to a sealed-interface or
protocol-based validator chain in either language.

### Python, a schema and PII guard with a bounded reask loop

Two validators run in sequence, a schema check and a regex-based PII
check, and a failing candidate is repaired by reasking the mock Generator
with the exact validation error, up to a small retry cap, before falling
through to a fixed refusal.

```python
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class Verdict:
    passed: bool
    reason: str = ""


@dataclass
class Candidate:
    text: str
    order_total: Optional[float] = None


SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def schema_validator(c: Candidate) -> Verdict:
    if c.order_total is None or c.order_total < 0:
        return Verdict(False, "order_total must be a non-negative number")
    return Verdict(True)


def pii_validator(c: Candidate) -> Verdict:
    if SSN_PATTERN.search(c.text):
        return Verdict(False, "response contains a social security number")
    return Verdict(True)


VALIDATORS: list[Callable[[Candidate], Verdict]] = [
    schema_validator,
    pii_validator,
]


class Guard:
    def __init__(self, generate: Callable[[str, Optional[str]], Candidate],
                 max_retries: int = 2) -> None:
        self._generate = generate
        self._max_retries = max_retries

    def run(self, prompt: str) -> Candidate:
        error: Optional[str] = None
        for attempt in range(self._max_retries + 1):
            candidate = self._generate(prompt, error)
            for validator in VALIDATORS:
                verdict = validator(candidate)
                if not verdict.passed:
                    error = verdict.reason
                    break
            else:
                return candidate
        return Candidate(text="Sorry, I could not produce a safe answer.",
                          order_total=0.0)


def flaky_mock_generator(prompt: str, error: Optional[str]) -> Candidate:
    # The mock fails once on purpose to exercise the reask branch of Guard.
    if error is None:
        return Candidate(text="Your SSN on file is 123-45-6789.",
                          order_total=42.50)
    return Candidate(text="Your order total is confirmed.",
                      order_total=42.50)


def main() -> None:
    guard = Guard(flaky_mock_generator, max_retries=2)
    result = guard.run("What is my order total?")
    print(result.text, result.order_total)


if __name__ == "__main__":
    main()
```

### TypeScript, a concurrent validator chain with an aggregator

The three validators run concurrently through `Promise.all`, matching the
independent-validators-in-parallel branch of dimension 7's dynamics, and
the aggregator applies an all-must-pass policy before choosing an action.

```typescript
type Verdict = { passed: boolean; reason?: string };

type Candidate = { text: string; totalCents: number };

type Validator = (c: Candidate) => Promise<Verdict>;

async function schemaValidator(c: Candidate): Promise<Verdict> {
  if (!Number.isInteger(c.totalCents) || c.totalCents < 0) {
    return { passed: false, reason: "totalCents must be a non-negative integer" };
  }
  return { passed: true };
}

async function profanityValidator(c: Candidate): Promise<Verdict> {
  const banned = ["badword"];
  const hit = banned.find((w) => c.text.toLowerCase().includes(w));
  return hit
    ? { passed: false, reason: `banned term detected: ${hit}` }
    : { passed: true };
}

async function lengthValidator(c: Candidate): Promise<Verdict> {
  return c.text.length > 500
    ? { passed: false, reason: "response exceeds the length policy" }
    : { passed: true };
}

type Action =
  | { kind: "forward"; candidate: Candidate }
  | { kind: "refuse"; reason: string };

async function runGuard(
  candidate: Candidate,
  validators: Validator[]
): Promise<Action> {
  const verdicts = await Promise.all(validators.map((v) => v(candidate)));
  const failure = verdicts.find((v) => !v.passed);
  if (failure) {
    return { kind: "refuse", reason: failure.reason ?? "validation failed" };
  }
  return { kind: "forward", candidate };
}

async function main(): Promise<void> {
  const candidate: Candidate = { text: "Your total is confirmed.", totalCents: 4250 };
  const action = await runGuard(candidate, [
    schemaValidator,
    profanityValidator,
    lengthValidator,
  ]);
  if (action.kind === "forward") {
    console.log("forwarded:", action.candidate.text);
  } else {
    console.log("refused:", action.reason);
  }
}

main();
```

### Go, a rule-based validator with a circuit-breaker fallback

A validator that times out or errors degrades to a safe refusal rather than
hanging the caller, matching the fix for the latency failure mode in
dimension 11.

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"regexp"
	"time"
)

type Candidate struct {
	Text string
}

type Verdict struct {
	Passed bool
	Reason string
}

var ssnPattern = regexp.MustCompile(`\b\d{3}-\d{2}-\d{4}\b`)

func piiValidator(c Candidate) Verdict {
	if ssnPattern.MatchString(c.Text) {
		return Verdict{Passed: false, Reason: "contains a social security number"}
	}
	return Verdict{Passed: true}
}

func slowClassifier(c Candidate) Verdict {
	time.Sleep(50 * time.Millisecond)
	return Verdict{Passed: true}
}

func runWithTimeout(ctx context.Context, c Candidate, check func(Candidate) Verdict) (Verdict, error) {
	done := make(chan Verdict, 1)
	go func() { done <- check(c) }()
	select {
	case v := <-done:
		return v, nil
	case <-ctx.Done():
		return Verdict{}, errors.New("validator timed out")
	}
}

func guard(c Candidate) (Candidate, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	if v := piiValidator(c); !v.Passed {
		return Candidate{Text: "Sorry, that response was blocked."}, nil
	}

	v, err := runWithTimeout(ctx, c, slowClassifier)
	if err != nil {
		return Candidate{Text: "Sorry, please try again."}, fmt.Errorf("guard degraded: %w", err)
	}
	if !v.Passed {
		return Candidate{Text: "Sorry, that response was blocked."}, nil
	}
	return c, nil
}

func main() {
	out, err := guard(Candidate{Text: "Your order total is confirmed."})
	if err != nil {
		fmt.Println("degraded fallback:", out.Text, err)
		return
	}
	fmt.Println("forwarded:", out.Text)
}
```
