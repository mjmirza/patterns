---
name: Prompt Chaining
slug: prompt-chaining
family: 17-ai-agentic
category: Agentic Workflow
aliases: [Sequential Chain, LLM Pipeline, Chained Prompting, Prompt Pipelining]
first_described: "Anthropic 2024, Building Effective Agents"
maturity: established
related: [pipeline-processing, chain-of-responsibility, pipes-and-filters, retry, orchestrator-workers, routing-workflow]
incompatible_with: []
verified: 2026-08-02
---

# Prompt Chaining

## 1. Name, aliases, and lineage

The name used across the industry today is Prompt Chaining, and the clearest
canonical description of it as a named workflow pattern for LLM applications
comes from Anthropic's engineering post "Building Effective Agents," which
lists it first among the five workflow patterns the article distinguishes from
autonomous agents. The post defines it plainly: "Prompt chaining decomposes a
task into a sequence of steps, where each LLM call processes the output of the
previous one" ([Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents),
verified 2026-08-02). The same post names the programmatic checks placed
between steps as gates, a term this entry keeps because it is the one the
pattern's own primary source uses.

The idea itself predates the name. Practitioners working with GPT-3 in 2021
and 2022 were already splitting a task across two or three completion calls
because a single prompt produced worse results than a short pipeline of
smaller prompts, and the technique circulated under informal names such as
sequential prompting or multi-step prompting before any vendor wrote it down
as a pattern with a diagram. LangChain shipped a class named `SequentialChain`
in its earliest releases specifically to codify this shape in code, and its
own documentation still frames the class as running a series of chains, one
after another ([LangChain, migrating SequentialChain to LCEL](https://python.langchain.com/docs/versions/migrating_chains/sequential_chain/),
verified 2026-08-02). OpenAI's Cookbook independently arrived at a version of
the same idea under the heading "split complex tasks into simpler subtasks,"
demonstrating a Clue-style logic puzzle that a single prompt gets wrong but
that a three-step chain (evaluate relevant clues, combine clues, map to an
answer) gets right ([OpenAI Cookbook, Techniques to improve reliability](https://developers.openai.com/cookbook/articles/techniques_to_improve_reliability),
verified 2026-08-02). Three independent groups, a foundation-model vendor
writing about agent design, an open-source orchestration library, and a
different foundation-model vendor writing a reliability guide, converged on
the identical shape without a shared academic paper to cite, which is part of
why this entry treats the pattern as established rather than canonical in the
Gang of Four sense. There is no single 1994-style text that named it first.
There is a cluster of practitioners who kept rediscovering the same fix for
the same failure.

A separate and much older lineage sits underneath the name and deserves to be
named honestly, because a reviewer who knows classical software architecture
will recognize the shape instantly. Prompt Chaining is the Pipes and Filters
architectural style, described in Frank Buschmann, Regine Meunier, Hans
Rohnert, Peter Sommerlad, and Michael Stal, *Pattern-Oriented Software
Architecture, Volume 1. A System of Patterns*, Wiley, 1996, chapter 2, applied
to a filter whose transformation function is an LLM call instead of a
deterministic subroutine. Every structural property of Pipes and Filters
holds here. A filter reads from one input and writes to one output, filters
are composed by connecting an output to the next input, and the pipeline can
be reasoned about one stage at a time. The one property that stops holding is
the one that made Pipes and Filters cheap to compose in the first place. A
classical filter is a pure, deterministic function, and an LLM call is
neither. That single difference is why this entry exists separately from the
Pipes and Filters entry rather than as a footnote inside it, and dimension 3
below returns to exactly this point.

## 2. Problem and context

A task is handed to a single LLM call, and the call is asked to do everything
at once, understand a long or ambiguous instruction, apply several unrelated
rules, transform the input, format the output, and self-check its own work,
all inside one generation. As the number of things the model must hold in mind
at once grows, quality drops in a way that is not linear. A prompt asking for
one clear transformation is close to reliable. The same prompt with three more
requirements bolted onto it starts skipping steps, blending two rules
together, or drifting format halfway through the response, and the failure is
often silent. The output looks plausible and passes a casual read while
containing a step that was never actually performed.

The context in which this problem shows up has a specific shape. The task
decomposes cleanly into an ordered sequence of subtasks, where subtask two
genuinely needs the finished output of subtask one rather than merely
benefiting from it, and each subtask is small enough that a model doing only
that one thing, at a smaller temperature and with a narrower instruction, gets
it right close to every time. Anthropic's own two worked examples are useful
because they show two different reasons the decomposition helps. Generating
marketing copy and then translating it into another language separates two
skills that interfere with each other when asked for simultaneously, tone and
persuasion on one side, faithful translation on the other. Writing a document
outline, checking that outline against a rubric, then writing the full
document from the checked outline inserts a verification point the model
cannot skip, because the outline literally does not exist yet when the check
runs, and the check has a concrete, bounded artifact to grade instead of an
entire document ([Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents),
verified 2026-08-02).

The problem Prompt Chaining solves is therefore not "the model is not smart
enough." It is "the model is being asked to do too many things in one
undivided act of generation, and dividing the act recovers accuracy that the
model already has." This is a load-shedding move, not a capability upgrade. It
trades one expensive, wide, error-compounding call for several cheap, narrow
calls plus the latency of running them in order.

## 3. Forces

**Latency versus accuracy.** Every added step is at minimum one more network
round trip to the model provider. A three-step chain at roughly two seconds a
call costs six seconds before the user sees the final answer, against perhaps
three or four seconds for one larger call. Anthropic states the trade
explicitly. This pattern trades latency for higher accuracy by making each LLM
call an easier task ([Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents),
verified 2026-08-02). The pattern favors accuracy and is only worth adopting
when the accuracy gain is real and measured, not assumed.

**Coupling between steps versus independence.** A chain couples step N+1 to
the exact output shape step N happens to produce. If step N's output format
drifts, for example the model starts wrapping a JSON object in a markdown
fence it did not use before, every downstream step that parses that output
breaks at once. The coupling is implicit unless the interface between steps is
made explicit with a schema, which is exactly why dimension 8 treats
structured intermediate output as a variant worth calling out on its own.

**Cost versus reliability.** More calls means more billed tokens, and it also
means more opportunities to add a cheap non-LLM check between two expensive
LLM calls, which the gate mechanism exploits. A well-placed gate can be a
regex, a JSON schema validation, or a single boolean function that costs
effectively nothing next to the token bill of the calls around it, so the
pattern can raise reliability without raising cost proportionally, as long as
the gates are doing real work and are not simply another LLM call graded by
another LLM call.

**Error compounding versus error containment.** This is the sharpest force in
the pattern and the one most catalogs skip. Chaining N steps where each step
independently succeeds with probability p produces a chain that succeeds end
to end with probability roughly p raised to the power N, if the steps'
failures are close to independent. At p equal to 0.95 and N equal to 3 the
naive product is about 0.857, and at N equal to 6 it drops to about 0.735. The
pattern's whole promise, narrower calls are more accurate, is bought at the
cost of stacking that accuracy N times, and the gain per step has to outrun
the multiplication or the chain nets out worse than the single wide call it
replaced. This is exactly what gates exist to fight, because a gate that
catches and repairs a bad intermediate output breaks the naive multiplication
by converting a silent failure into a caught one that can retry, and
dimension 11 below returns to the arithmetic in more depth. This is
engineering judgement, not a sourced result, and the exact factorization
depends on how correlated the steps' failures actually are in a given system.

**Determinism versus flexibility.** The sequence of steps and their order is
fixed at design time by a human, which is the opposite of an autonomous agent
that decides its own next step. This is a force the pattern deliberately
resolves in one direction, and dimension 4 spells out exactly where that
resolution stops being appropriate.

## 4. Applicability and non-applicability

**Reach for Prompt Chaining when.**

- The task decomposes into a fixed, known sequence of subtasks that does not
  change from one run to the next, so the same three or four steps apply every
  time regardless of the specific input.
- A later subtask genuinely depends on the finished output of an earlier one,
  not merely on the same input data, so there is a real data dependency to
  express as a pipe.
- A single wide prompt has been tried and measurably underperforms the same
  task split into narrower calls, ideally shown with an evaluation set rather
  than a hunch.
- There is a natural point in the middle of the task where a cheap,
  deterministic check can catch a mistake before it propagates, for example
  validating that a generated outline actually contains the required
  sections before spending tokens writing the full document from it.
- The extra latency of two, three, or four sequential calls is acceptable for
  the product surface, for example a background job, an editorial workflow,
  or a batch pipeline, rather than a chat interface where every added second
  is directly felt by a waiting user.

**Do NOT reach for Prompt Chaining when.**

- The task cannot be decomposed into a fixed sequence at all, because the
  right next step depends on what an earlier step discovered in an
  open-ended way. That is Orchestrator-Workers or a full agent loop, not
  Prompt Chaining, and forcing a dynamic problem into a static chain produces
  a chain with a branch bolted onto every step, which is a worse design than
  either pure pattern.
- Latency is the dominant constraint and a single well-crafted prompt already
  clears the accuracy bar the product needs. Adding steps here buys nothing
  and costs the user real waiting time.
- The subtasks are independent of each other and do not need each other's
  output, only the same input. That is parallelization, not chaining, and
  running independent calls concurrently instead of in sequence removes the
  added latency entirely.
- The team cannot or will not add a real, cheap gate between steps. A chain
  with no gates has every one of the coupling and error-compounding costs
  from dimension 3 and none of the benefit gates are supposed to buy back,
  and is close to strictly worse than one call with a careful prompt.
- The task is a single, narrow transformation to begin with. Chaining a task
  that already fits comfortably in one prompt only adds latency, cost, and a
  new class of intermediate-format bugs for no accuracy gain.
- Steps must complete inside a hard latency budget measured in low hundreds
  of milliseconds, for example an autocomplete suggestion or a real-time
  voice turn. Sequential network round trips to a model provider cannot meet
  that budget regardless of how narrow each individual call is.

## 5. Structure

The pattern has three kinds of participant, and confusing the second with the
third is the most common structural mistake seen in real chains.

- **Step (a filter).** A unit of work that accepts the previous step's output,
  or the original task input for the first step, calls an LLM with a prompt
  built from that input, and produces one output value. A step owns exactly
  one prompt template and exactly one responsibility. A step that internally
  branches on the content of its own output is no longer one step. It is two
  steps wearing one name.
- **Gate (a programmatic check).** A deterministic, non-LLM function that
  inspects an intermediate output and returns pass or fail, optionally with a
  reason. A gate never calls a model. The moment a "gate" is implemented by
  asking a second LLM to grade the first LLM's output, it has stopped being a
  gate in Anthropic's sense and has become an evaluator step, which is a
  legitimate design on its own but pays the token cost and unreliability of an
  ordinary step rather than the near-free cost of a real gate.
- **Chain Runner (the orchestrating context).** The code that holds the fixed
  sequence of steps and gates, threads the output of one into the input of
  the next, decides what happens when a gate fails (retry the step, abort the
  chain, or fall back to a default), and returns the final artifact to the
  caller. The chain runner is deliberately dumb. It has no judgement of its
  own about what step comes next. It only executes the sequence a human wrote
  down in advance.

The relationship between these three is strictly linear for the base pattern,
step, optional gate, step, optional gate, step, in the order a human fixed at
design time. Branching, retries with modified prompts, and loops are all real
things production chains do, and dimension 8 covers them as variants, but the
base structure this entry names is the straight line.

## 6. ASCII structure diagram

```
                          CHAIN RUNNER
        (fixed sequence, defined at design time, not by the model)

  task input
      |
      v
  +---------+     +------+     +---------+     +------+     +---------+
  | STEP 1  | --> | GATE | --> | STEP 2  | --> | GATE | --> | STEP 3  |
  | LLM call|     |check |     | LLM call|     |check |     | LLM call|
  +---------+     +------+     +---------+     +------+     +---------+
      |               |            |               |             |
      | output_1      | pass/fail  | output_2       | pass/fail   | final
      |               |            |                |             | output
      v               v            v                v             v
   (consumed      abort or      (consumed        abort or     returned
    by gate 1     retry step 1   by gate 2        retry step 2  to caller
    and step 2)   on fail)       and step 3)       on fail)

  Each step reads only the previous step's output plus the fixed prompt
  template it owns. No step can see the original task input unless the
  chain runner explicitly threads it forward. Each gate is a plain function,
  never a model call.
```

## 7. Dynamics

```
CALLER                CHAIN RUNNER            STEP 1 (LLM)   GATE 1   STEP 2 (LLM)
  |                        |                        |           |          |
  | run(task_input)        |                        |           |          |
  |----------------------->|                        |           |          |
  |                        | build_prompt(task_input)|          |          |
  |                        |----------------------->|           |          |
  |                        |                        | (model    |          |
  |                        |                        |  call)    |          |
  |                        |<-----------------------|           |          |
  |                        | output_1               |           |          |
  |                        |----------------------->|           |          |
  |                        |                        | check(output_1)      |
  |                        |                        |---------->|          |
  |                        |<---------------------------------- |          |
  |                        | pass                    |           |          |
  |                        |------------------------------------------->|
  |                        |          build_prompt(output_1)     |          |
  |                        |                                     | (model   |
  |                        |                                     |  call)   |
  |                        |<------------------------------------------- |
  |                        | output_2                            |          |
  |<-----------------------|                                     |          |
  | final_output            |                                     |          |

FAILURE PATH at GATE 1:
  ...                     | check(output_1)        |           |
  |                        |----------------------->|           |
  |                        |<-----------------------|           |
  |                        | fail, reason            |           |
  |                        | retry Step 1 with       |           |
  |                        | reason appended to      |           |
  |                        | prompt (bounded by a    |           |
  |                        | max-retry count)        |           |
  |                        |----------------------->|           |
  |                        |         ... or abort the chain      |
  |                        |         and surface the failure     |
  |                        |         to the caller instead       |
```

The one behavior a reader must not assume is that a failed gate always
retries. Retrying is the common default because it is cheap and the failure is
often transient (a malformed field, a missing section), but a production
chain almost always caps the retry count and falls through to an explicit
abort or a degraded default response, because an unbounded retry loop on a
gate that fails deterministically, for example because the prompt itself asks
for something the model structurally cannot produce, becomes an availability
bug rather than a reliability fix.

## 8. Implementation variants

- **Bare sequential calls, no gates.** The minimal version, step calls step
  calls step with no check in between. Cheapest to build, and the version
  most tutorials show. Carries the full error-compounding cost from dimension
  3 with none of the mitigation, and should be treated as a starting point to
  harden, not a shipping design, for anything beyond a demo.
- **Gated chain with programmatic checks.** Anthropic's own recommended
  shape. A plain function, a JSON schema validator, a regex, or a length or
  content-presence check sits between steps and can abort or trigger a retry
  before the next expensive call runs ([Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents),
  verified 2026-08-02). This is the variant this entry treats as the default,
  named production shape.
- **Structured intermediate output.** Instead of passing raw prose between
  steps, each step is asked to emit a typed object, most commonly JSON
  validated against a schema, so the coupling described in dimension 3
  becomes explicit and checkable rather than an implicit prose contract two
  prompts happen to agree on. This variant composes directly with the gate
  variant, because a schema validation is one of the cheapest, most reliable
  gates available.
- **Chain of thought as an in-call chain.** A single call that reasons step
  by step inside one generation is sometimes described loosely as chaining,
  but it is a different pattern living inside one LLM call rather than across
  several, first described in Jason Wei et al., "Chain-of-Thought Prompting
  Elicits Reasoning in Large Language Models," NeurIPS 2022. It shares the
  decompose-and-verify spirit with Prompt Chaining but shares none of the
  structural properties. There is no separate step boundary a gate can sit
  at, and this entry treats it as a related but distinct technique rather
  than a variant.
- **LangChain SequentialChain and LangGraph edges.** LangChain's early
  `SequentialChain` class codified the base pattern directly in a library
  primitive, and the project's newer LangGraph framework represents the same
  fixed sequence as a directed graph with an edge from each node to the next,
  which is structurally identical to this entry's chain runner but drawn as a
  graph instead of a list ([LangChain, migrating SequentialChain to LCEL](https://python.langchain.com/docs/versions/migrating_chains/sequential_chain/),
  verified 2026-08-02).
- **Language-idiomatic variants.** In a functional language, or a language
  with first-class function composition, the chain is often written as a
  right-to-left or left-to-right composition of async functions rather than
  an explicit loop over a list of step objects, which is the shape the code
  examples in this entry lean toward for TypeScript and Go, and Python's
  `functools.reduce` over a list of coroutines produces the same effect with
  less ceremony than a hand-written loop.

## 9. Known production uses

- **GitHub Copilot Workspace.** Copilot Workspace's documented flow moves a
  task through three staged phases, specification, plan, and implementation,
  where the plan is generated from the finished specification and the code is
  generated from the finished, user-editable plan rather than from the
  original task text directly. GitHub's own guidance frames the flow as
  specification and brainstorming, then planning, then implementation, each
  editable before the next stage runs ([GitHub Blog, 5 tips and tricks when using GitHub Copilot Workspace](https://github.blog/ai-and-ml/github-copilot/5-tips-and-tricks-when-using-github-copilot-workspace/),
  verified 2026-08-02), and a maintainer discussion on GitHub's own community
  forum describes the underlying system as orchestrating GPT-4o and related
  models to understand a codebase, then create and refine specs and plans,
  and only then generate or modify files ([GitHub community discussion #142971, How GitHub Next took Copilot Workspace from concept to code](https://github.com/orgs/community/discussions/142971),
  verified 2026-08-02).
- **Intercom Fin AI Engine.** Intercom's own help documentation describes
  Fin's answer pipeline as staged phases rather than one generation, a phase
  that refines the query sent to the model, a phase that retrieves and
  augments context before generating the answer, and a validation phase that
  checks the generated response for safety and accuracy before it reaches the
  customer ([Intercom Help, The Fin AI Engine](https://www.intercom.com/help/en/articles/9929230-the-fin-ai-engine),
  verified 2026-08-02). The refine, generate, validate staging is the same
  step, gate, step shape this entry describes, applied to a customer-support
  answer instead of a document.
- **Anthropic's own internal usage, as the primary source describes it.**
  The article that names the pattern also describes it being used inside
  Anthropic's own workflow examples rather than only as a theoretical
  illustration, generating marketing copy in one call and translating it in a
  second, and separately, generating a document outline, running a
  programmatic check against defined criteria, then generating the full
  document only after the outline passes the check ([Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents),
  verified 2026-08-02). This entry lists it as a named production use because
  the source presents the outline-check-document flow as a real applied
  example of the pattern the article is itself documenting, not as a
  contrived tutorial case.

## 10. Consequences

**Positive.**

- Each individual LLM call handles a narrower, better-specified task, which
  measurably raises the per-step success rate compared to the same subtask
  bundled inside a larger prompt, per the reliability argument Anthropic and
  OpenAI both make independently.
- Gates give the system a concrete point to catch a mistake before it
  propagates and gets more expensive to fix, converting a silent downstream
  failure into a caught, nameable, and often automatically retryable one.
- The prompt for each step is small, focused, and independently testable, so
  a team can version, evaluate, and tune one step's prompt without touching
  the others, which is a real engineering win over one enormous prompt that
  every change risks destabilizing in an unrelated place.
- The intermediate outputs are inspectable. A failure can be traced to the
  exact step that produced the bad value, which is a debugging advantage a
  single opaque generation does not offer.

**Negative.**

- Latency is additive across steps, and for a chat-facing product this cost
  is felt directly by a waiting person, not absorbed invisibly the way it can
  be in a background job.
- Cost is additive across steps, both in the literal token bill for N calls
  instead of one, and in the fixed per-request overhead each provider call
  carries regardless of how small the prompt is.
- Errors compound multiplicatively across the chain unless gates are actively
  fighting that multiplication, and a chain with no gates is close to
  strictly worse than the single wide call it was built to improve on, once
  the arithmetic in dimension 3 is taken seriously.
- The interface between steps is an implicit contract unless it is made
  explicit with a schema, and that contract can silently drift the moment
  either step's prompt is edited, breaking the chain in a way no compiler or
  type checker will ever catch.

## 11. Failure modes and misuse

**Symptom.** The final output is confidently wrong in a way that would have
been obvious from looking at an intermediate step, but nobody looked.
**Cause.** No gate exists between the step that produced the bad intermediate
value and the step that consumed it, so the error propagated silently and got
dressed up in fluent language by every step downstream.
**Fix.** Add a real, non-LLM gate at the point where the bad value first
appeared, even a minimal presence or shape check, and log every intermediate
output during development so a human can actually see where the chain went
wrong the first time it happens.

**Symptom.** The chain works reliably in testing on a handful of examples and
then degrades noticeably once it is exposed to real, varied input, with the
failure rate rising faster than any single step's own error rate would
predict.
**Cause.** The team estimated end-to-end reliability from one step's accuracy
in isolation and never multiplied it across the whole chain, so a system built
from three steps each individually correct nineteen times out of twenty was
expected to be correct essentially always, when the actual end-to-end rate is
close to 0.95 cubed, roughly 0.857, before accounting for any correlation
between the steps' failures.
**Fix.** Measure end-to-end accuracy on a held-out evaluation set for the
chain as a whole, not per step, before shipping, and treat the per-step
multiplication as the honest baseline expectation rather than a worst case
that will not actually happen.

**Symptom.** A prompt change to step 2, made to fix an unrelated complaint,
breaks step 3 in a way that took a long debugging session to trace back to
step 2.
**Cause.** Step 3's prompt was written assuming a specific, undocumented shape
for step 2's output, most often a specific prose format or field ordering
that was never a contract anyone wrote down, so a change that looks purely
local to step 2 silently violates an assumption step 3 depended on.
**Fix.** Make the interface between steps explicit, ideally a validated
schema rather than free prose, so a shape change fails loudly at the gate
immediately after the step that produced it rather than silently at whatever
downstream step happens to choke on it.

**Symptom.** A gate keeps failing on the same input, and the retry logic
keeps calling the same step with the same prompt, burning tokens and time
without ever succeeding.
**Cause.** The step's prompt is asking the model for something it cannot
structurally produce for that input, for example a fact the model was never
given and cannot infer, so every retry regenerates a different wrong answer
rather than converging toward a right one, and an unbounded or high retry
cap turns a deterministic failure into a slow, expensive failure instead of a
fast, cheap one.
**Fix.** Cap retries at a small fixed number, feed the gate's specific
failure reason back into the retry prompt rather than repeating the identical
prompt, and define an explicit fallback path (an abort with a clear error, a
default value, or escalation to a human) for when the cap is hit.

**Symptom.** The team calls their design Prompt Chaining, but the system
routinely does things the described pattern does not, changing which step
runs next based on a step's content, looping back to an earlier step, or
spawning multiple parallel branches from one intermediate result.
**Cause.** The task actually needed Orchestrator-Workers or a full agent loop
from the start, and the team built a chain first because it is the simpler
pattern to reach for, then kept adding conditional branches to the chain
runner as new requirements surfaced instead of stepping back and reaching for
the pattern the task actually calls for.
**Fix.** Recognize the branching itself as the signal, not a defect to patch
around. Once the chain runner needs to decide which step runs next based on
what an earlier step returned, the design has crossed into
Orchestrator-Workers territory, and it is cheaper to make that switch
deliberately than to keep bolting conditionals onto a runner that was
designed to be dumb.

## 12. Trade-off matrix

| Force | Prompt Chaining | Single large prompt | Autonomous agent loop |
|---|---|---|---|
| Sequence of steps | Fixed at design time by a human | No explicit steps, one generation | Decided at runtime by the model itself |
| Latency for a fixed task | Additive across N calls, higher | Lowest, one call | Highly variable, often highest |
| Per-subtask accuracy | Higher, each call is narrow | Lower under load of many requirements | Depends entirely on the model's own planning |
| Predictability of cost | Bounded, N calls known in advance | Bounded, one call | Unbounded in the general case, loop can run long |
| Debuggability | High, each intermediate output is inspectable | Low, one opaque generation | Low to medium, depends on trace tooling |
| Handles novel, unforeseen subtasks | No, the sequence cannot adapt itself | No | Yes, this is its reason to exist |
| Error compounding | Present and multiplicative across steps | Not applicable, only one step | Present, and harder to bound than a fixed chain |
| Engineering effort to build | Medium, N prompts plus gates plus a runner | Low, one prompt | High, needs planning, tool use, and stop conditions |

## 13. Related and incompatible patterns

**Pipes and Filters.** The classical architectural ancestor described in
dimension 1. Prompt Chaining is Pipes and Filters with one defining property
removed, the filter is no longer a pure deterministic function, and every
design decision that differs between the two, notably the need for gates,
follows directly from that one change.

**Chain of Responsibility.** A superficially similar name and a genuinely
different intent. Chain of Responsibility passes a request along a chain
until exactly one handler decides to handle it and the rest are skipped,
described in Gamma, Helm, Johnson, and Vlissides, *Design Patterns.
Elements of Reusable Object-Oriented Software*, Addison-Wesley, 1994, chapter
5. Prompt Chaining runs every step, in order, every time, and the steps are
cooperating stages of one pipeline rather than competing candidate handlers
for one request. Confusing the two leads a reader to expect early-exit
behavior that Prompt Chaining does not have by default.

**Retry.** Composes directly, at the gate level. The retry pattern described
in cloud and distributed systems catalogs, retrying a failed operation with
backoff, is exactly what a gate failure typically triggers on the single step
that failed, never on the whole chain from the start, and the two patterns
work well nested together as long as the retry is scoped to the failing step.

**Orchestrator-Workers.** The pattern to reach for the moment the fixed
sequence stops being fixed, when a step's output needs to determine what
happens next rather than merely feeding the next step's input. Anthropic
frames this pair as adjacent points on the same spectrum, and it is the
single most common escalation path when a Prompt Chain outgrows itself
([Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents),
verified 2026-08-02).

**Routing Workflow.** A pattern that classifies input first and sends it down
one of several distinct paths, rather than running every input through the
same fixed sequence. A chain can begin with a router step that picks which
downstream chain to run, which composes the two rather than conflicting.

**Incompatible with.** Nothing in this pattern is structurally incompatible
with another named pattern. Its failure mode, described in dimension 11, is
not a clash with a different pattern but a slow drift into needing one, most
often Orchestrator-Workers, while still being described as this one.

## 14. Refactoring path in and out

**Introducing a chain into a single, overloaded prompt.**

1. List every distinct requirement the current prompt asks the model to
   satisfy in one generation, and group them into an ordered list of
   subtasks where later subtasks genuinely need earlier subtasks' output.
2. Write one focused prompt per subtask, each with its own explicit success
   criteria, and run them by hand against a handful of real inputs to
   confirm each one, in isolation, does its narrow job well.
3. Wire the steps together with the simplest possible runner, a linear
   function calling step one, then step two, then step three, passing each
   step's output as the next step's input, with no gates yet.
4. Compare end-to-end output quality against the original single-prompt
   baseline on a real evaluation set. If quality has not measurably
   improved, stop here. The added latency and cost were not worth it, and
   the honest outcome is to revert to the single prompt.
5. If quality did improve, identify the point in the chain where a bad
   intermediate value would be cheapest to catch, and add a real
   programmatic gate there first, before adding gates everywhere.
6. Add a bounded retry with a feedback loop, the gate's failure reason fed
   back into the retry prompt, and an explicit fallback for when the retry
   budget is exhausted.

**Removing a chain that has stopped earning its place.**

1. Confirm the chain's steps genuinely run in the same fixed order on every
   real input in production traffic, not merely in the test cases that were
   written for it. If branching has already crept in, this is not a
   removal, it is the escalation to Orchestrator-Workers described in
   dimension 11, and the chain should be redesigned rather than collapsed.
2. If the order really is always fixed and the accuracy gain that justified
   the chain has not held up under real traffic, or a newer model handles
   the whole task correctly in one call, merge the step prompts back into a
   single, carefully written prompt.
3. Re-run the same evaluation set used when the chain was introduced against
   the merged prompt, and only ship the collapse once the merged prompt
   matches or beats the chain's measured accuracy, not before.
4. Remove the now-orphaned gates and the chain runner, keeping their logic
   as a regression test asserting the merged prompt still passes the checks
   the gates used to enforce.

## 15. Testing and verification

Testing a chain happens at two levels that must both be covered, and testing
only the second one is the most common gap seen in real codebases. This
dimension is largely engineering judgement drawn from practice, not a single
sourced methodology.

**Per-step testing.** Each step is a pure enough function of its input and
its prompt template that it can be tested in isolation with a small, curated
set of realistic intermediate inputs, asserting the step's output satisfies
its own gate's criteria on each one. This is where prompt regressions are
caught cheaply, because a single step's test suite runs fast and pinpoints
exactly which stage broke.

**End-to-end testing.** The full chain is run against real or realistic task
inputs and the final output is graded against the actual product requirement,
not against any one step's local criteria. This is the only level that can
catch the compounding-error problem from dimension 3, because a chain where
every step passes its own local test can still fail end to end if the steps'
individually acceptable outputs interact badly.

**Deterministic doubles for the model call.** For fast, hermetic tests, the
model call inside a step is replaced with a stub returning a fixed, known
output, which lets the chain runner's wiring, gate logic, and retry and
fallback behavior be tested without any network call or nondeterminism. This
mirrors the classic test-double technique for any external dependency,
described broadly in Gerard Meszaros, *xUnit Test Patterns. Refactoring Test
Code*, Addison-Wesley, 2007, applied here to an LLM provider instead of a
database or a network service.

**Golden-output regression tests.** A small, fixed set of real task inputs
paired with a manually reviewed, accepted output for the whole chain is kept
as a regression suite. Every prompt change to any step in the chain is run
against this set before shipping, and a difference from the accepted output
is a signal a human reviews, not necessarily a bug, because the model's
non-determinism means a perfect byte-for-byte match is the wrong bar. What
matters is whether the difference still satisfies the same acceptance
criteria.

**Statistical accuracy testing.** Because LLM outputs vary run to run, a
single pass or fail on one input is a weak signal. Running the full chain N
times, commonly ten to fifty, against the same evaluation set and reporting a
pass rate is closer to the truth than a single boolean result, and it is the
only way to observe the compounding-error arithmetic from dimension 3
directly rather than reasoning about it from individual step accuracy.

## 16. Observability signals

A healthy chain in production shows a stable per-step latency distribution, a
gate failure rate low enough that retries are rare rather than routine, and
an end-to-end success rate that tracks the product's stated accuracy target
over a rolling window rather than drifting downward. This dimension is
practice-derived judgement, not a sourced specification.

What to log and trace per step, at minimum. The step's name and position in
the chain, the input it received (truncated if large), the output it
produced, the model and parameters used for that specific call, the latency
of that one call, the token counts for that call, and, if a gate ran
immediately after, the gate's pass or fail result and its reason on failure.
Tracing this per step, rather than only logging the chain's final input and
output, is what makes the debugging advantage from dimension 10 real rather
than theoretical.

A failing chain typically shows one of two distinct signatures on a
dashboard. Either the failure rate is concentrated at one specific step and
its gate, which points directly at that step's prompt or the upstream data
feeding it, or the failure rate is spread thinly across every step at once,
which more often points at a shared cause outside any individual step, a
model version change from the provider, a shift in the distribution of real
task inputs, or a change to a shared piece of context every step's prompt
includes. Distinguishing these two signatures quickly is the main practical
reason to instrument per step rather than only at the chain's boundary.

Token spend and latency should be tracked per step and summed for the chain,
because a cost regression is often localized to one step whose prompt grew
unexpectedly verbose or whose output length crept up over time, and that
localization is invisible if only the chain's total cost is measured.

## 17. Security and privacy implications

Each step in a chain is a separate point where the model's output can be
influenced by content an earlier step pulled in, which matters directly when
any step's input includes untrusted external content, a document a user
uploaded, a web page fetched during an earlier step, or free text a customer
typed. A prompt injection payload sitting in that untrusted content can
influence not only the step that directly reads it but every downstream step
that consumes its output, because the chain has no inherent notion of trust
boundaries between stages, only a data pipe. A gate that validates shape, for
example a schema check, does not by itself validate intent, so a maliciously
crafted but schema-valid intermediate output can still pass a naive gate and
continue propagating through the chain.

Because a chain often persists and logs every intermediate output for the
debuggability reasons described in dimension 16, any personal or sensitive
data present in the original task input is now present in N separate log
entries instead of one, at the boundary of every step, which multiplies the
data-retention and access-control surface a privacy review has to cover
compared with a single-call design. Retention policies and redaction rules
written for a single-generation system's logs frequently do not account for
this multiplication and need to be revisited when a single call is refactored
into a chain.

A gate that performs an authorization or content-safety check should never be
the last line of defense on its own, precisely because a gate is a plain
function inspecting text, and text-based checks are pattern-matchable and can
be evaded by content specifically crafted to satisfy the pattern while still
carrying the disallowed payload. This is an analytical implication rather
than a sourced finding, and it argues for layering a programmatic check with
a model-based check on any safety-critical gate rather than relying on
either alone.

## 18. References

- Anthropic, "Building Effective Agents." https://www.anthropic.com/research/building-effective-agents, verified 2026-08-02.
- LangChain, "Migrating from SequentialChain." https://python.langchain.com/docs/versions/migrating_chains/sequential_chain/, verified 2026-08-02.
- OpenAI, "Techniques to improve reliability," OpenAI Cookbook. https://developers.openai.com/cookbook/articles/techniques_to_improve_reliability, verified 2026-08-02.
- GitHub Blog, "5 tips and tricks when using GitHub Copilot Workspace." https://github.blog/ai-and-ml/github-copilot/5-tips-and-tricks-when-using-github-copilot-workspace/, verified 2026-08-02.
- GitHub, community discussion #142971, "How GitHub Next took Copilot Workspace from concept to code." https://github.com/orgs/community/discussions/142971, verified 2026-08-02.
- Intercom Help, "The Fin AI Engine." https://www.intercom.com/help/en/articles/9929230-the-fin-ai-engine, verified 2026-08-02.
- Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, and Michael Stal, *Pattern-Oriented Software Architecture, Volume 1. A System of Patterns*, Wiley, 1996, chapter 2, Pipes and Filters.
- Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides, *Design Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley, 1994, chapter 5, Chain of Responsibility.
- Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc Le, and Denny Zhou, "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models," Advances in Neural Information Processing Systems 35, NeurIPS 2022.
- Gerard Meszaros, *xUnit Test Patterns. Refactoring Test Code*, Addison-Wesley, 2007.

## Code examples

Three languages are shown because Prompt Chaining is idiomatic wherever a
language has a clean way to compose sequential async operations. TypeScript
and Python are the two languages the pattern is overwhelmingly built in
today, given how much LLM tooling lives in those ecosystems, and Go is shown
because its explicit error handling makes the gate-and-abort control flow
unusually visible, which is useful for a reader who has not seen the pattern
before. Java, Rust, and Swift are omitted from the runnable examples for this
entry, not because the pattern does not translate (it does), but because the
pattern's essential complexity lives in the sequencing and gating logic
rather than in any language-specific mechanism, and three languages already
show every structural idea this entry describes without repeating the same
shape three more times.

Every example below models the LLM call with a small stub function rather
than a real network call, so the examples run offline and deterministically
while keeping the chain runner, the gate, and the retry logic real and
exercised.

### TypeScript

```typescript
type StepFn<I, O> = (input: I) => Promise<O>;
type GateFn<O> = (output: O) => { pass: boolean; reason?: string };

async function runGatedStep<I, O>(
  name: string,
  step: StepFn<I, O>,
  gate: GateFn<O> | null,
  input: I,
  maxRetries = 2
): Promise<O> {
  let lastReason = "";
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const output = await step(input);
    if (!gate) return output;
    const result = gate(output);
    if (result.pass) return output;
    lastReason = result.reason ?? "gate failed";
  }
  throw new Error(`step "${name}" failed its gate after retries. ${lastReason}`);
}

// stubbed LLM calls, deterministic for the example
async function writeOutline(topic: string): Promise<string> {
  return `Outline for ${topic}\n1. Intro\n2. Body\n3. Conclusion`;
}

async function checkOutline(outline: string): Promise<string> {
  return outline; // step passthrough, gate below does the real check
}

async function writeDocument(outline: string): Promise<string> {
  return `Document written from.\n${outline}`;
}

const outlineHasThreeSections: GateFn<string> = (outline) => {
  const sectionCount = (outline.match(/^\d+\./gm) || []).length;
  return sectionCount >= 3
    ? { pass: true }
    : { pass: false, reason: `only ${sectionCount} sections, need 3` };
};

async function outlineThenDocumentChain(topic: string): Promise<string> {
  const outline = await runGatedStep("write-outline", writeOutline, outlineHasThreeSections, topic);
  const checked = await runGatedStep("check-outline", checkOutline, null, outline);
  const document = await runGatedStep("write-document", writeDocument, null, checked);
  return document;
}

async function main() {
  const result = await outlineThenDocumentChain("Prompt Chaining");
  console.log(result);
}

main();
```

Run in this session with `npx tsx` after confirming `npx tsc --version`
resolved a working TypeScript install. The chain executed and printed the
three-section outline followed by the document text with no errors.

### Python

```python
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class GateResult:
    passed: bool
    reason: str = ""


def run_gated_step(name, step, gate, value, max_retries=2):
    last_reason = ""
    for _ in range(max_retries + 1):
        output = step(value)
        if gate is None:
            return output
        result = gate(output)
        if result.passed:
            return output
        last_reason = result.reason
    raise RuntimeError(f'step "{name}" failed its gate after retries. {last_reason}')


# stubbed LLM calls, deterministic for the example
def write_outline(topic: str) -> str:
    return f"Outline for {topic}\n1. Intro\n2. Body\n3. Conclusion"


def check_outline(outline: str) -> str:
    return outline  # passthrough step, the gate below does the real check


def write_document(outline: str) -> str:
    return f"Document written from.\n{outline}"


def outline_has_three_sections(outline: str) -> GateResult:
    count = len(re.findall(r"^\d+\.", outline, re.MULTILINE))
    if count >= 3:
        return GateResult(passed=True)
    return GateResult(passed=False, reason=f"only {count} sections, need 3")


def outline_then_document_chain(topic: str) -> str:
    outline = run_gated_step("write-outline", write_outline, outline_has_three_sections, topic)
    checked = run_gated_step("check-outline", check_outline, None, outline)
    document = run_gated_step("write-document", write_document, None, checked)
    return document


if __name__ == "__main__":
    print(outline_then_document_chain("Prompt Chaining"))
```

Run directly with `python3 prompt_chaining.py` in this session and produced
the expected outline and document output with no errors or exceptions.

### Go

```go
package main

import (
	"fmt"
	"regexp"
)

type GateResult struct {
	Pass   bool
	Reason string
}

type StepFn func(string) (string, error)
type GateFn func(string) GateResult

func runGatedStep(name string, step StepFn, gate GateFn, input string, maxRetries int) (string, error) {
	lastReason := ""
	for attempt := 0; attempt <= maxRetries; attempt++ {
		output, err := step(input)
		if err != nil {
			return "", err
		}
		if gate == nil {
			return output, nil
		}
		result := gate(output)
		if result.Pass {
			return output, nil
		}
		lastReason = result.Reason
	}
	return "", fmt.Errorf("step %q failed its gate after retries. %s", name, lastReason)
}

// stubbed LLM calls, deterministic for the example
func writeOutline(topic string) (string, error) {
	return fmt.Sprintf("Outline for %s\n1. Intro\n2. Body\n3. Conclusion", topic), nil
}

func checkOutline(outline string) (string, error) {
	return outline, nil // passthrough, the gate below does the real check
}

func writeDocument(outline string) (string, error) {
	return fmt.Sprintf("Document written from.\n%s", outline), nil
}

var sectionPattern = regexp.MustCompile(`(?m)^\d+\.`)

func outlineHasThreeSections(outline string) GateResult {
	matches := sectionPattern.FindAllString(outline, -1)
	if len(matches) >= 3 {
		return GateResult{Pass: true}
	}
	return GateResult{Pass: false, Reason: fmt.Sprintf("only %d sections, need 3", len(matches))}
}

func outlineThenDocumentChain(topic string) (string, error) {
	outline, err := runGatedStep("write-outline", writeOutline, outlineHasThreeSections, topic, 2)
	if err != nil {
		return "", err
	}
	checked, err := runGatedStep("check-outline", checkOutline, nil, outline, 0)
	if err != nil {
		return "", err
	}
	document, err := runGatedStep("write-document", writeDocument, nil, checked, 0)
	if err != nil {
		return "", err
	}
	return document, nil
}

func main() {
	result, err := outlineThenDocumentChain("Prompt Chaining")
	if err != nil {
		fmt.Println("chain failed.", err)
		return
	}
	fmt.Println(result)
}
```

Run with `go run prompt_chaining.go` in this session and produced the
expected outline and document output with no errors.
