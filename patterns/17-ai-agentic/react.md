---
name: ReAct
slug: react-prompting
family: 17-ai-agentic
category: Agentic
aliases: [Reasoning and Acting, Thought-Action-Observation Loop, ReAct Prompting]
first_described: "Yao, Zhao, Yu, Du, Shafran, Narasimhan, Cao 2022"
maturity: canonical
related: [reflexion, tool-use, plan-and-execute, chain-of-thought, orchestrator-worker]
incompatible_with: []
verified: 2026-08-02
---

# ReAct

## 1. Name, aliases, and lineage

The canonical name is ReAct, a compression of Reasoning and Acting, chosen so
the word itself reads as a verb, because the pattern is defined by a language
model doing something in the world rather than only describing something. It
was introduced by Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran,
Karthik Narasimhan, and Yuan Cao in the paper "ReAct. Synergizing Reasoning
and Acting in Language Models," first posted to arXiv as 2210.03629 on 6
October 2022, with a revised version 3 posted 10 March 2023
([arXiv 2210.03629](https://arxiv.org/abs/2210.03629), verified 2026-08-02).
The paper was accepted at ICLR 2023.

The pattern also circulates under two working names in engineering
conversation rather than in the paper itself. Thought-Action-Observation Loop
describes the literal three-part structure of each turn, and Reasoning and
Acting is the unabbreviated form of the acronym, used interchangeably with
ReAct in blog posts and vendor documentation that avoid the bare acronym on
first mention. Neither is a competing name from a different research
lineage, both are restatements of the same paper's contribution, so this
entry treats them as aliases rather than as related but distinct patterns.

ReAct did not invent either of its two halves on its own. Chain-of-thought
prompting, the practice of asking a model to produce intermediate reasoning
steps before a final answer, had already been documented by Jason Wei and
coauthors at Google Research the same year
([Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in Large
Language Models," arXiv 2201.11903](https://arxiv.org/abs/2201.11903),
verified 2026-08-02). Tool-augmented language models, where a model's output
triggers a call to an external API and the result is fed back into the
context, existed in various forms before ReAct too, including WebGPT's
browser-mediated question answering. The specific contribution the ReAct
paper makes, and the reason it is treated as its own named pattern rather
than a footnote to chain-of-thought, is the claim and the demonstrated
result that interleaving the two, reasoning traces and actions, in a single
generation stream produces behaviour that reasoning-only prompting and
acting-only prompting cannot each produce alone. The paper states this
directly in its abstract, that reasoning traces help the model "induce,
track, and update action plans as well as handle exceptions," while actions
let the model "interface with external sources, such as knowledge bases or
environments, to gather additional information" (arXiv 2210.03629, verified
2026-08-02).

## 2. Problem and context

A language model asked to answer a multi-hop factual question, or to
complete a task that spans several tool calls, has two failure modes when it
is prompted with only one of the two capabilities. Ask it to reason with
chain-of-thought alone, with no tools, and it will produce a plausible chain
of intermediate statements that can drift from any grounded fact, because
every step is generated from the model's own parameters and nothing external
checks it along the way. This is the well-documented hallucination and error
propagation problem, a wrong fact stated at step two is treated as true at
step five, and the final answer inherits the error with no mechanism to
notice it happened. Ask the same model to only act, calling tools and
reading their results with no interleaved reasoning, and the opposite
failure appears. The model has no visible record of why it called a
particular tool, cannot recover cleanly from an unexpected or empty result,
and produces action sequences that a human reviewing the transcript cannot
follow or trust, because the "why" was never written down. The paper's own
framing states that acting-only prompting struggles particularly with
"the model's inability to reason to induce, track, and update action plans
and handle exceptions" (arXiv 2210.03629, verified 2026-08-02).

The context in which this problem is sharpest is any task that is both
knowledge-intensive and requires more than one lookup or action to complete,
of the kind found in open-domain question answering over a corpus larger
than the model's context window, or in interactive decision-making
environments where the agent's own past actions change the state it is
reasoning about. In both cases the model cannot simply be told the answer in
its prompt, because the answer depends on information not present until an
action retrieves it, and the model cannot simply be told what to do next in
a fixed script, because the right next action depends on what the previous
action returned. A static prompt or a static plan written before execution
starts cannot adapt to a piece of information discovered mid-task.
Recognising this problem in a real codebase looks like an agent loop that
calls a search API and immediately feeds the raw JSON result into the next
prompt with no space for the model to say what it is looking for or why the
result does or does not answer the question, or the mirror-image case, a
chain-of-thought prompt that produces a long, confident, and entirely
un-grounded multi-step answer with zero calls to any external system.

## 3. Forces

The dominant force ReAct trades against is token cost and latency against
grounding and interpretability. Every reasoning step the model is asked to
produce before an action is tokens generated that do not themselves change
any external state, and every observation appended to the context is tokens
the model must re-read on the next turn, so a ReAct trajectory is
systematically longer and slower, and therefore more expensive at
inference time, than an acting-only loop that skips the "Thought" lines
entirely. What that cost buys is a model whose intermediate steps are
readable by a person and, more importantly, by the model itself on the next
turn, which is the mechanism that lets it notice an action failed or
returned something unexpected and change course rather than continuing on
a stale plan. This is a genuine trade, not a free lunch, and the paper is
explicit that on some tasks, for example WebShop, "the ReAct trajectory is often
more efficient in finding a satisficing item" while on ALFWorld the gains
come specifically from being able to "recover from an unsuccessful action"
mid-episode, both effects being paid for in additional generated tokens
(arXiv 2210.03629, verified 2026-08-02).

A second force is faithfulness against fluency. Chain-of-thought reasoning
that is never checked against anything external can be extremely fluent and
extremely wrong, a phenomenon separately studied as unfaithful reasoning,
where the stated chain of thought does not actually correspond to the
process that produced the answer. Interleaving actions gives the reasoning
something to be checked against at every step, an observation the model did
not write and cannot silently make up, which is what the paper means when
it reports that ReAct trajectories are "more interpretable" and reduce
hallucination relative to a reasoning-only baseline on HotpotQA and Fever
(arXiv 2210.03629, verified 2026-08-02). The cost of this force is that the
pattern only helps to the degree the tools it calls are themselves
trustworthy. An observation from a broken or adversarial tool is treated
with the same weight as a real one, so ReAct does not remove the need to
validate what a tool returns, it only gives the model a place to notice a
suspicious result if the surrounding prompt teaches it to look.

A third force, coupling against composability, plays out in how tightly the
reasoning format is bound to a particular action schema. The original paper
uses a small, fixed set of Wikipedia API actions, search, lookup, and
finish, and gets strong results with only one or two in-context examples
per task family (arXiv 2210.03629, verified 2026-08-02). Widening the action
space to dozens of arbitrary tools, as most production agent frameworks do,
increases the chance the model picks the wrong tool or malforms an action
argument, which is a cost the pattern's original evaluation setting did not
have to pay. Teams building on ReAct therefore trade a smaller, curated tool
surface for reliability against a larger, more capable tool surface for
reach, and the pattern itself gives no guidance on where to draw that line,
it is an operational decision made per deployment.

## 4. Applicability and non-applicability

Reach for ReAct when the task requires the model to gather information it
does not already have and to decide what to gather next based on what it
has already found, when a human or an automated evaluator needs to audit
why the agent took a given action rather than only what it produced, when
the environment can return an unexpected or empty result that the agent
must be able to notice and recover from without a human in the loop, and
when the number of steps to completion is not known in advance so a fixed
pipeline of tool calls cannot be pre-scripted.

Do not use ReAct in these situations.

- The task is answerable from the model's own parametric knowledge with no
  external lookup and no risk that matters if the answer is wrong. Adding a
  reasoning-and-acting loop to a single closed-book question adds latency
  and cost for no measurable gain, a plain completion or a single
  chain-of-thought pass is sufficient.
- The sequence of actions is fully known ahead of time and does not depend
  on any intermediate result. A deterministic, ordered pipeline, for
  example resize an image then upload it then send a notification, gains
  nothing from letting the model re-derive that order at every step, and a
  plain orchestrated workflow is both cheaper and more reliable, because it
  cannot be talked out of the correct sequence by a confusing observation.
- Latency budget is fixed and tight, for example a sub-second autocomplete
  suggestion, where the multi-turn think-act-observe cycle cannot fit
  regardless of how much it would help accuracy.
- The action space is unbounded and unvetted, for example letting the model
  freely execute arbitrary shell commands with no allowlist. ReAct's
  reasoning trace can explain a dangerous action as fluently as a safe
  one, the pattern provides visibility, not a permission boundary, and
  substituting it for a real authorization layer is a category error.
- The task benefits more from generating and comparing several complete
  candidate solutions than from taking one path and correcting it along the
  way. Self-consistency or tree-of-thoughts style exploration, which sample
  multiple independent reasoning paths and pick the best, are a better fit
  when the failure mode is "the first idea was mediocre" rather than "the
  first idea depended on external information the model did not have yet."

## 5. Structure

The participants in a ReAct loop, using the paper's own vocabulary
throughout, are the following.

**Agent, the language model.** The single component that produces both the
Thought and the Action at every step. It is not two separate models, the
reasoning and the acting come from one generation call, which is the
structural fact that makes the two capabilities inseparable rather than
merely sequential.

**Thought.** A free-text reasoning trace the model writes before choosing an
action. Its role is to decompose the task, note what has been learned so
far, decide what is still missing, and plan the next step. The paper treats
Thoughts as an unconstrained, task-specific language space the model can use
flexibly rather than a fixed schema (arXiv 2210.03629, verified 2026-08-02).

**Action.** A structured or semi-structured call into a fixed, task-specific
action space, for example `search[entity]`, `lookup[string]`, and
`finish[answer]` in the paper's Wikipedia-API setting. The action is what
actually changes or queries external state.

**Environment.** The external system the action addresses, a search API, a
database, a simulated household in ALFWorld, or an online shopping site in
WebShop. It is passive between actions and only responds when called.

**Observation.** The environment's response to the most recent action,
appended verbatim to the growing context so the next Thought can reference
it. This is the feedback channel that closes the loop, without it the
pattern degenerates into acting blind.

**Trajectory, or scratchpad.** The full, append-only sequence of
Thought/Action/Observation triples accumulated so far in the episode. It is
both the agent's working memory for the current task and, after the fact,
the artifact a human or evaluator reads to audit the run.

## 6. ASCII structure diagram

```
+----------------------------------------------------------+
|                     ReAct Agent Loop                      |
|                                                            |
|   +----------------+        generates       +----------+  |
|   |   Trajectory   |<----------------------- | Agent    |  |
|   |  (Thought /    |                         | (LLM)    |  |
|   |   Action /     | ----------------------->|          |  |
|   |   Observation  |    reads as context     +----------+  |
|   |   history)     |                              |        |
|   +----------------+                              |        |
|          ^                                        | emits  |
|          |                                        v        |
|          |  appends Observation           +-----------------+
|          |                                 |     Action      |
|          |                                 | search[query]   |
|          |                                 | lookup[string]  |
|          |                                 | finish[answer]  |
|          |                                 +-----------------+
|          |                                        |          |
|          |                                        | invokes  |
|          |                                        v          |
|          |                                 +-----------------+
|          +-------------------------------- |   Environment   |
|             returns Observation            | (search API,    |
|                                             |  DB, game world)|
|                                             +-----------------+
+------------------------------------------------------------+
```

## 7. Dynamics

At episode start the agent receives a task description and, in the
few-shot setting the paper uses, a small number of complete
Thought/Action/Observation example trajectories for tasks of the same kind,
prepended to the prompt as demonstrations. The loop then runs as follows,
repeated until the model emits a terminal action or a step budget is
exhausted.

```
step 0. context = [task, few-shot examples]

loop
  1. model reads context, emits
       Thought_i  (free text. what is known, what is missing, what to do)
       Action_i   (structured call, e.g. search["Colorado orogeny"])
  2. runtime parses Action_i, dispatches to the environment
  3. environment executes, returns
       Observation_i  (raw or lightly formatted result, e.g. search snippet,
                        "Nothing Found", tool error, game state delta)
  4. runtime appends [Thought_i, Action_i, Observation_i] to context
  5. if Action_i is a terminal action (finish[...])
       return the answer, exit loop
     else
       goto step 1 with the extended context
```

Two dynamics are worth calling out because they are the specific
behaviours the paper attributes to interleaving reasoning with acting
rather than to either half alone. First, error recovery. On ALFWorld, when
an action like `open cabinet 1` returns an observation indicating the
cabinet is already open or the wrong object, the reasoning-carrying agent
can produce a Thought that explicitly revises its plan, for example
deciding to check a different cabinet, whereas an act-only agent with no
place to reason about the anomaly tends to repeat the failing action or
proceed on a plan that is now inconsistent with the observed state
(arXiv 2210.03629, verified 2026-08-02). Second, exploiting internal
knowledge for efficient search. On HotpotQA-style multi-hop questions, the
Thought steps let the model reformulate its next search query using facts
already surfaced in earlier observations, closing in on the answer entity
faster than an unguided keyword search would, while still checking each
guess against a real lookup rather than asserting it from memory
(arXiv 2210.03629, verified 2026-08-02).

## 8. Implementation variants

**Fixed few-shot action-space ReAct, the paper's original setting.** A
small, hand-written set of legal actions, typically two to four verbs,
paired with a handful of complete demonstration trajectories inserted into
the prompt. This is the cheapest to implement, the easiest to audit, and
the variant with the strongest published grounding, but it does not scale
to an open-ended tool catalogue without rewriting the demonstrations for
every new action added.

**Native function-calling ReAct.** Instead of writing the Action as free
text the runtime parses with a regular expression, the model is given a
tool schema through the provider's native function-calling interface, the
mechanism generalised across model vendors since late 2023, and the
runtime reads a structured tool-call object rather than parsing text. The
Thought still appears as free text preceding or alongside the call. This
variant is what most current agent frameworks default to because it
removes an entire class of parsing failures, at the cost of losing the
exact token-level control the original text-based action format gave the
prompt author.

**ReAct with a hard step budget or a self-consistency wrapper.** A fixed
maximum number of Thought/Action/Observation cycles is imposed to bound
cost and latency, and either the runtime forces a `finish` action once the
budget is hit, or several independent trajectories are sampled and the
majority or best-scored answer is kept, borrowing the self-consistency
idea to reduce the variance any single stochastic trajectory carries.

**Memory-augmented ReAct.** The trajectory is not the only state carried
between episodes, a separate long-term memory store, often the Reflexion
pattern's verbal self-critique buffer, is consulted at the start of a new
attempt so that a failure in one episode changes the Thoughts produced in
the next. This variant is the one the Reflexion paper itself builds on top
of, describing its own actor as built on top of the ReAct formulation, see
the Reflexion entry in this repository for the full citation.

**Guarded or sandboxed ReAct.** The Action step is routed through an
authorization or allowlist layer before it reaches the real environment,
addressing the non-applicability point above about ReAct not itself being
a security boundary. This is an operational addition, not a change to the
core pattern, but it is close to universal in any production deployment
that exposes actions with real side effects.

## 9. Known production uses

**LangChain and LangGraph's `create_react_agent`.** LangChain's agent
framework ships a prebuilt constructor literally named `create_react_agent`
in the `langgraph.prebuilt` module, which builds an agent graph that calls
tools in a loop until a stopping condition is met, the same
think-then-call-a-tool-then-observe loop the ReAct paper describes, exposed
as a first-class, documented building block for production agents
([langgraph-ai/langgraph, `libs/prebuilt/langgraph/prebuilt/chat_agent_executor.py`](https://github.com/langchain-ai/langgraph),
verified 2026-08-02).

**Amazon Bedrock Agents.** AWS's managed agent orchestration service
documents its runtime loop in terms that directly mirror the ReAct
structure without using the acronym. "The agent interprets the input with a
foundation model and generates a rationale that lays out the logic for the
next step," then "predicts which action in an action group it should
invoke," then "generates an output, known as an observation, from invoking
an action," and "this loop continues until the agent returns a response to
the user"
([AWS documentation, "How Amazon Bedrock Agents works"](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-how.html),
verified 2026-08-02). The rationale, action, and observation vocabulary and
the iterate-until-terminal-response control flow are the ReAct loop by
another name, running as a managed cloud service.

**Microsoft Semantic Kernel's Stepwise Planner, historical.** Semantic
Kernel shipped a Stepwise Planner that built a Thought/Action/Observation
loop over registered plugin functions to let a model decide its next
action based on the result of its previous one. Microsoft's own current
documentation confirms the planner existed and has since been deprecated
and removed in favour of native function calling across Python, .NET, and
Java, directing developers to a migration guide
([Microsoft Learn, "What are Planners in Semantic Kernel"](https://learn.microsoft.com/en-us/semantic-kernel/concepts/planning),
verified 2026-08-02). This is cited as a real, shipped production use of the
pattern, and honestly labelled as no longer the recommended path in that
particular framework, which illustrates the broader industry shift toward
native function calling described in implementation variant two above.

## 10. Consequences

**Positive.**

- Grounds intermediate reasoning in real, checkable observations rather
  than letting a multi-step chain of thought run entirely on the model's
  own possibly wrong prior beliefs, which the paper reports as a reduction
  in hallucination and error propagation relative to a reasoning-only
  baseline on HotpotQA and Fever (arXiv 2210.03629, verified 2026-08-02).
- Produces a human-readable audit trail of why each action was taken, not
  only what the final answer was, because the Thought preceding every
  Action is stored verbatim in the trajectory.
- Lets the agent recover mid-episode from an unexpected or failed action
  by reasoning about the observation and revising its plan, rather than
  either failing silently or continuing on a stale plan, which the paper
  attributes its 34 absolute-percentage-point success-rate improvement over
  imitation and reinforcement-learning baselines on ALFWorld to
  (arXiv 2210.03629, verified 2026-08-02).
- Needs very little task-specific demonstration data to work. The paper
  reports strong results from one or two in-context examples per task type
  on WebShop, where it "outperforms imitation and reinforcement learning
  methods by an absolute success rate of 10 percent" with far less labeled
  data than those baselines required (arXiv 2210.03629, verified
  2026-08-02).

**Negative.**

- Every Thought is additional generated tokens spent on something other
  than the final answer, which raises per-episode latency and inference
  cost compared to an acting-only loop with no reasoning step, a cost that
  compounds across long episodes.
- The pattern gives the model a channel to state reasoning, it does not
  guarantee that stated reasoning caused the following action, so a
  ReAct trajectory can still exhibit unfaithful reasoning where the
  Thought reads as a plausible justification for an action the model would
  have taken regardless.
- A malformed Action, one the runtime cannot parse or that the environment
  rejects, produces an Observation that is itself confusing, and a model
  that has not been shown examples of recovering from a malformed-action
  observation can spiral into repeating the same invalid call.
- The pattern is silent on authorization. Nothing about the
  Thought/Action/Observation structure prevents a fluent, well-reasoned
  Thought from preceding a destructive or unauthorized Action, so treating
  a readable trace as a safety mechanism rather than an observability
  mechanism is a common and dangerous misreading.

## 11. Failure modes and misuse

**Thought-action mismatch, silently ignored.** Symptom, the trajectory log
shows a Thought that plans one thing, for example "I should check the
publication date of the second source," followed by an Action that does
something unrelated, for example a repeated search on the first entity.
Cause, nothing in the base pattern enforces consistency between the
free-text Thought and the structured Action that follows it, the two are
independently sampled continuations of the same context and can diverge,
especially under aggressive sampling temperature or when the action schema
cannot actually express what the Thought proposed. Fix, constrain the
Action generation to be conditioned tightly on the immediately preceding
Thought, for example by structuring the prompt so the action-parsing step
rejects an Action that does not reference an entity or value named in the
Thought, and log a mismatch as a first-class event to catch drift instead
of only reading transcripts after the fact.

**Infinite or near-infinite action loops.** Symptom, the same Action, or a
narrow cycle of two or three actions, repeats many times with no progress,
consuming the step or token budget without reaching a terminal action.
Cause, an Observation the model has already seen once, for example
"Nothing Found" from a failed search, is not distinguished from a fresh
Observation, so the model has no signal that it is repeating itself,
particularly likely when the action space offers no graceful way to say
"I am stuck." Fix, track a rolling window of recent Action/Observation
pairs and inject an explicit note into the context when a near-duplicate
is detected, or enforce a hard step ceiling that forces a terminal
`finish` action with a best-effort answer once the ceiling is reached,
rather than letting the loop run out the clock silently.

**Malformed action parsing failures compounding.** Symptom, the agent
emits an action string the runtime's parser cannot resolve to a real
function or API call, the runtime returns a generic error observation, and
the next Thought and Action are visibly confused, sometimes retrying the
same malformed syntax. Cause, the action grammar the model was shown in
its few-shot examples does not match the runtime's actual parser exactly,
often because the demonstrations were hand-written before a tool's
argument schema changed, or because the model is free-generating an action
name that resembles but does not exactly match a registered tool. Fix,
validate every emitted action against the live tool registry before
dispatch, return a specific, actionable error observation naming the
closest valid tool or the exact expected argument shape rather than a bare
exception string, and keep the few-shot demonstrations under the same
version control and test coverage as the tool schema itself.

**Prompt injection through observation content.** Symptom, the agent's
Thought after a particular Observation starts following instructions that
were embedded in the returned content of a search result or webpage
rather than the original task, and subsequent Actions serve an attacker's
goal rather than the user's. Cause, the Observation channel is, by design,
untrusted external content inserted directly into the model's context with
no separation from the user's original task instructions, so any
adversarial text an action retrieves is read by the model with the same
authority as the system prompt unless the surrounding scaffolding
explicitly marks it otherwise. Fix, wrap every Observation in an explicit,
consistently applied delimiter that the system prompt teaches the model to
treat as data rather than instruction, strip or flag known instruction-like
patterns in tool output before it reaches the context, and, where the
action's blast radius is meaningful, gate the next Action through a
separate authorization check that does not itself trust the Thought that
requested it.

**Runaway cost from unbounded episode length.** Symptom, a small
percentage of episodes consume an order of magnitude more tokens or wall
time than the median episode, and the aggregate bill is dominated by this
long tail rather than by the typical case. Cause, the pattern has no
built-in step limit, an agent that keeps finding plausible-looking next
actions can keep going indefinitely, particularly on genuinely
open-ended or ambiguous tasks where no single Observation clearly signals
completion. Fix, enforce a hard maximum step count and a hard maximum
token budget per episode at the runtime level, not as a suggestion inside
the prompt, and alert or fail closed when either limit is hit rather than
silently truncating the trajectory mid-thought.

## 12. Trade-off matrix

| Force | ReAct | Chain-of-thought only | Plan-and-execute | Reflexion |
|---|---|---|---|---|
| Grounding in external state | High, every step can check an Observation | None, reasoning runs entirely on parametric knowledge | Medium, executes a plan against real tools but the plan itself is fixed before any observation arrives | High, inherits ReAct's grounding and adds cross-episode critique |
| Cost per successful task | Medium to high, pays for a Thought at every step | Low, single generation pass | Low per attempt, but a bad upfront plan can waste an entire execution | Highest, ReAct's cost multiplied across several attempts |
| Mid-task recovery from a bad step | Strong, the next Thought can react to an unexpected Observation | None, there is no external step to fail | Weak, an error mid-plan generally requires re-planning from outside the loop | Strong within an episode, plus explicit cross-episode learning from failure |
| Auditability of intermediate reasoning | High, Thought/Action/Observation is a readable transcript | High for the reasoning, but disconnected from any real-world check | Medium, the plan is visible but the executor's step-by-step reasoning may not be | High, includes the self-critique as an additional artifact |
| Best fit | Multi-hop lookup and interactive tasks with uncertain step count | Closed-book reasoning with no external dependency | Tasks where the full action sequence is knowable in advance and stability matters more than adaptivity | Tasks where a single ReAct attempt is not reliable enough and repeated attempts are affordable |

## 13. Related and incompatible patterns

**Reflexion** builds directly on top of ReAct. The Reflexion paper's actor
role is explicitly a ReAct-style agent, and Reflexion adds a second,
cross-episode loop on top. After a ReAct episode ends, an evaluator scores
the outcome, a self-reflection model writes a natural-language critique of
what went wrong, and that critique is stored in memory and re-read at the
start of the next attempt. The two patterns compose cleanly because
Reflexion does not change anything about a single episode's
Thought/Action/Observation loop, it only wraps that loop in an outer
retry-and-learn structure. See the Reflexion entry in this repository for
the full mechanism.

**Tool use** is the more general pattern ReAct is a specific instance of.
Any pattern where a model calls an external function and reads back a
result is tool use, ReAct's distinguishing addition is the requirement
that a reasoning Thought precede and interleave with every such call,
rather than the model calling tools with no visible justification.

**Plan-and-execute** is the pattern most often proposed as an alternative
rather than a composition partner, and the two are frequently mixed in
practice. An outer planner produces a coarse sequence of subtasks, and
each subtask is then executed by an inner ReAct loop that can adapt within
its own narrower scope. This hybrid keeps the stability of having an
overall plan while retaining ReAct's mid-task recovery ability at the
level of individual steps.

**Chain-of-thought prompting** is a strict subset of ReAct's reasoning
half. A ReAct Thought is chain-of-thought reasoning, the pattern's novelty
is only in interleaving that reasoning with real actions rather than
letting it run to a final answer unchecked. Nothing about ReAct is
incompatible with chain-of-thought, ReAct is better understood as
chain-of-thought plus a grounding mechanism than as a competing pattern.

**Orchestrator-worker** is compatible at a different granularity. An
orchestrator can dispatch subtasks to multiple parallel workers, and each
worker can itself be implemented as a ReAct loop, exactly as one subtask
inside a plan-and-execute pipeline might be. There is no structural
conflict, ReAct describes the internal control flow of a single reasoning
agent, orchestrator-worker describes how multiple agents or subtasks are
coordinated.

No pattern in this family is incompatible with ReAct in the sense of being
unable to be composed with it, the closest thing to an incompatibility is
that a fixed, non-adaptive pipeline defeats the purpose of paying ReAct's
extra reasoning cost, so combining ReAct with a genuinely static,
fully-known sequence of steps is wasteful rather than structurally broken.

## 14. Refactoring path in and out

**Introducing ReAct into an existing tool-calling agent that currently
calls tools blind, with no reasoning step.** First, insert a single
free-text field into the agent's output schema, generated before the tool
call, and have the prompt explicitly ask the model to state what it knows,
what it still needs, and which tool call addresses that gap. Second, make
sure the Observation returned from each tool is appended back into the
context verbatim, not summarised or discarded, because the next Thought
depends on being able to read the actual result. Third, add a small
number, two or three, of complete worked-example trajectories to the
system prompt, matching the paper's own finding that few-shot
demonstrations of the full Thought/Action/Observation shape are sufficient
to establish the pattern reliably (arXiv 2210.03629, verified 2026-08-02).
Fourth, once the loop is running, add the failure-mode guards from
dimension 11 above, in particular a step ceiling and repeated-action
detection, before any production traffic reaches it.

**Introducing ReAct into an existing single-pass chain-of-thought prompt
that has no tools at all.** First, identify the specific claims in the
existing chain-of-thought output that are checkable against an external
source, for example a factual assertion that could be verified by a
search call. Second, define a minimal action space, often as small as one
search action and one finish action, matching the paper's own minimal
Wikipedia-API setting rather than over-building a large tool catalogue on
day one. Third, restructure the prompt so the model alternates a Thought
with an Action rather than producing one long uninterrupted chain, and
wire the runtime to actually execute the Action and feed back a real
Observation rather than letting the model hallucinate what the tool would
have returned.

**Removing ReAct when it stops earning its place.** This is the right move
when telemetry shows the action space in practice never actually adapts
based on an Observation, that is, the sequence of tool calls made is
effectively identical across most episodes regardless of what any
individual Observation contained. That is the signal the task has turned
out to be closer to plan-and-execute than to genuinely interactive
decision-making, and the fix is to replace the per-step reasoning loop
with a fixed pipeline of the tool calls that were actually always made,
removing the Thought-generation cost entirely, and reserving a ReAct-style
loop only for the specific subtask, if any, that genuinely still needs
mid-task adaptation.

## 15. Testing and verification

Testing is a matter of judgement about what to check and how, informed by
practice rather than by a single canonical source.

Unit-level testing separates cleanly into two concerns. The action parser
and dispatcher can be tested exactly like any other piece of code, with
fixed input strings mapped to expected parsed actions, malformed strings
mapped to expected, specific error observations, and no language model
involved at all, which is the cheapest and fastest layer of the test suite
and should carry the bulk of the coverage. The tool implementations
themselves, the functions an Action ultimately calls, are ordinary
functions or API clients and should be tested the same way any external
integration is tested, with the real dependency mocked at the boundary so
the test suite does not depend on live network access or live API state.

Trajectory-level testing is where ReAct differs from testing a
deterministic pipeline, because the sequence of Thoughts and Actions the
model produces is not fixed given the same input, and running the same
prompt twice can legitimately produce two different but both-correct
trajectories. The useful test double here is a scripted or replayed
environment. Record a real trajectory once, including every Observation
the environment actually returned, and replay those fixed Observations
against a fresh model call so the test asserts on the model's behaviour
given a known, controlled sequence of inputs rather than on the
non-deterministic combination of model output and live environment
response. This isolates whether a regression is in the prompt or model
behaviour versus a change in the environment's own responses.

End-to-end evaluation, matching the paper's own methodology, uses labelled
benchmark tasks with a known correct final answer or a known success
condition, for example exact-match on a HotpotQA answer or task
completion in an ALFWorld episode, and measures success rate across a
held-out set rather than eyeballing individual transcripts
(arXiv 2210.03629, verified 2026-08-02). For a production agent without a
labelled benchmark, the closest practical analogue is a fixed regression
suite of representative real task inputs with a human-verified expected
outcome or an automated evaluator model scoring against a rubric, run on
every change to the prompt, the action schema, or the underlying model
version, since any of the three can silently change the trajectories
produced.

## 16. Observability signals

A healthy ReAct deployment should surface, per episode, the number of
Thought/Action/Observation steps taken before termination, with a
distribution tracked over time rather than a single average, because a
shift in the tail, a growing share of episodes hitting the step ceiling,
is the earliest signal of the runaway-loop failure mode described in
dimension 11. Track the rate of malformed or rejected actions as a
fraction of total actions emitted, a rising rate points either at a drift
between the prompt's demonstrated action grammar and the live tool schema,
or at a change in the underlying model's instruction-following behaviour
after a version upgrade. Track a repeated-action rate, the fraction of
episodes where the same action, or a short cycle of actions, is emitted
more than a small threshold number of times, as a direct proxy for the
infinite-loop failure mode. Track token and dollar cost per successfully
completed episode, not only per episode overall, because a cheap-looking
average can hide a bimodal distribution where most episodes are efficient
and a minority are extremely expensive.

A failing instance looks like a widening gap between the step-count
distribution's median and its 95th or 99th percentile, a rising malformed-
action rate correlated with a recent prompt or tool-schema deployment, and
episodes whose final Observation before termination is an error or an
empty result rather than a genuine completion signal, which indicates the
agent is being forced to a `finish` action by the step ceiling rather than
reaching one on its own judgement. Logging the full trajectory, every
Thought, Action, and Observation, for a sampled percentage of production
episodes, not only the failing ones, is what makes it possible to notice a
new failure pattern before it becomes common enough to show up clearly in
the aggregate metrics.

## 17. Security and privacy implications

The Observation channel is the pattern's primary attack surface. Any
content an Action retrieves, a search result, a scraped webpage, a
database row written by a different, less trusted user, is inserted
directly into the model's context and read with the same generative
authority as the original task instructions unless the surrounding
scaffolding actively separates the two, which is the mechanism behind the
prompt injection failure mode described in dimension 11. This is an
analytical implication rather than a sourced finding specific to this
paper, it follows from the general property that a large language model
does not have a built-in, cryptographically enforced separation between
instructions and data in its context window, and ReAct's design, which
deliberately feeds untrusted external content back into that same context
at every step, makes this property directly load-bearing rather than
incidental.

The Action channel is the pattern's primary authorization surface, and the
key implication is a negative one. Nothing in the ReAct structure itself
authenticates or authorizes an Action before it executes, a fluent,
well-reasoned Thought carries no more actual permission than a terse one.
Any production deployment where an Action has a real side effect, writing
data, sending a message, spending money, must implement authorization as a
layer the runtime enforces independently of the model's own stated
reasoning, never as something inferred from the Thought text. Logging full
trajectories for observability, as recommended in dimension 16, also means
logging whatever sensitive content passed through an Observation, so
trajectory logs containing personal data, credentials accidentally
returned by a tool, or other regulated content need the same retention,
access-control, and redaction discipline as any other system log that can
contain sensitive user data, which is an ordinary data-handling
requirement rather than something specific to this pattern, but one that
is easy to overlook because a trajectory log looks like debug output
rather than like a system that stores user data.

## 18. References

- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y.
  (2022). "ReAct. Synergizing Reasoning and Acting in Language Models."
  arXiv 2210.03629. [https://arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629),
  verified 2026-08-02.
- Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi,
  E., Le, Q., & Zhou, D. (2022). "Chain-of-Thought Prompting Elicits
  Reasoning in Large Language Models." arXiv 2201.11903.
  [https://arxiv.org/abs/2201.11903](https://arxiv.org/abs/2201.11903),
  verified 2026-08-02.
- Shinn, N., Cassano, F., Berman, E., Gopinath, A., Narasimhan, K., & Yao,
  S. (2023). "Reflexion. Language Agents with Verbal Reinforcement
  Learning." arXiv 2303.11366.
  [https://arxiv.org/abs/2303.11366](https://arxiv.org/abs/2303.11366),
  verified 2026-08-02, cited for the Reflexion pattern's explicit
  dependency on a ReAct-style actor, discussed in dimensions 8 and 13.
- LangChain AI. `create_react_agent`, `libs/prebuilt/langgraph/prebuilt/chat_agent_executor.py`,
  langgraph-ai/langgraph repository.
  [https://github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph),
  verified 2026-08-02.
- Amazon Web Services. "How Amazon Bedrock Agents works," AWS Bedrock user
  guide.
  [https://docs.aws.amazon.com/bedrock/latest/userguide/agents-how.html](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-how.html),
  verified 2026-08-02.
- Microsoft. "What are Planners in Semantic Kernel," Microsoft Learn.
  [https://learn.microsoft.com/en-us/semantic-kernel/concepts/planning](https://learn.microsoft.com/en-us/semantic-kernel/concepts/planning),
  verified 2026-08-02.

## Code examples

The three implementations below are a minimal, dependency-free ReAct loop.
A fixed two-action space, `search` and `finish`, a stub environment that
stands in for a real API so the sample is runnable with no network access
and no API key, and the Thought/Action/Observation trajectory printed as it
grows. The "model" in each sample is a small deterministic function rather
than a live LLM call, so the sample demonstrates the control flow the
pattern requires without depending on any external service or credential.
A real deployment replaces only that one function with an actual model
call.

### TypeScript

```typescript
type Observation = string;

interface Step {
  thought: string;
  action: string;
  observation: Observation;
}

// Stand-in for a real search API. A production build replaces this with
// an HTTP call to a search index or knowledge base.
function environmentSearch(query: string): Observation {
  const knowledgeBase: Record<string, string> = {
    "colorado orogeny": "The Colorado orogeny was an episode of mountain building in Colorado and surrounding areas, active roughly 1780 to 1650 million years ago.",
    "colorado orogeny elevation": "The eastern sector of the Colorado orogeny extends into the High Plains and is called the Central Plains orogeny.",
  };
  const key = query.trim().toLowerCase();
  return knowledgeBase[key] ?? "Nothing Found";
}

// Stand-in for a language model call. Given the trajectory so far, decide
// the next Thought and Action. A production build replaces this with a
// call to an LLM provider, passing the trajectory as context.
function decideNextStep(task: string, history: Step[]): { thought: string; action: string } {
  if (history.length === 0) {
    return {
      thought: "I need to find out what the Colorado orogeny is before I can answer.",
      action: "search[colorado orogeny]",
    };
  }
  const last = history[history.length - 1];
  if (last.observation !== "Nothing Found" && history.length === 1) {
    return {
      thought: "I have a definition. The question also asks about elevation range, I should search that specifically.",
      action: "search[colorado orogeny elevation]",
    };
  }
  return {
    thought: "I now have enough information to answer the question.",
    action: `finish[${last.observation}]`,
  };
}

function parseAction(action: string): { name: string; arg: string } {
  const match = action.match(/^(\w+)\[(.*)\]$/);
  if (!match) {
    throw new Error(`Malformed action. ${action}`);
  }
  return { name: match[1], arg: match[2] };
}

function runReActLoop(task: string, maxSteps: number): { answer: string; trajectory: Step[] } {
  const trajectory: Step[] = [];

  for (let stepIndex = 0; stepIndex < maxSteps; stepIndex++) {
    const { thought, action } = decideNextStep(task, trajectory);
    const parsed = parseAction(action);

    if (parsed.name === "finish") {
      trajectory.push({ thought, action, observation: parsed.arg });
      return { answer: parsed.arg, trajectory };
    }

    if (parsed.name !== "search") {
      throw new Error(`Unknown action. ${parsed.name}`);
    }

    const observation = environmentSearch(parsed.arg);
    trajectory.push({ thought, action, observation });
  }

  throw new Error("Step budget exhausted without reaching finish[...]");
}

const result = runReActLoop("What years was the Colorado orogeny active?", 5);
for (const step of result.trajectory) {
  console.log(`Thought. ${step.thought}`);
  console.log(`Action. ${step.action}`);
  console.log(`Observation. ${step.observation}`);
}
console.log(`Answer. ${result.answer}`);
```

### Python

```python
from dataclasses import dataclass


@dataclass
class Step:
    thought: str
    action: str
    observation: str


# Stand-in for a real search API. A production build replaces this with a
# call to a search index or knowledge base.
def environment_search(query: str) -> str:
    knowledge_base = {
        "colorado orogeny": (
            "The Colorado orogeny was an episode of mountain building in "
            "Colorado and surrounding areas, active roughly 1780 to 1650 "
            "million years ago."
        ),
        "colorado orogeny elevation": (
            "The eastern sector of the Colorado orogeny extends into the "
            "High Plains and is called the Central Plains orogeny."
        ),
    }
    return knowledge_base.get(query.strip().lower(), "Nothing Found")


# Stand-in for a language model call. Given the trajectory so far, decide
# the next Thought and Action. A production build replaces this with a
# call to an LLM provider, passing the trajectory as context.
def decide_next_step(task: str, history: list[Step]) -> tuple[str, str]:
    if not history:
        return (
            "I need to find out what the Colorado orogeny is before I "
            "can answer.",
            "search[colorado orogeny]",
        )
    last = history[-1]
    if last.observation != "Nothing Found" and len(history) == 1:
        return (
            "I have a definition. The question also asks about elevation "
            "range, I should search that specifically.",
            "search[colorado orogeny elevation]",
        )
    return (
        "I now have enough information to answer the question.",
        f"finish[{last.observation}]",
    )


def parse_action(action: str) -> tuple[str, str]:
    if "[" not in action or not action.endswith("]"):
        raise ValueError(f"Malformed action. {action}")
    name, _, rest = action.partition("[")
    return name, rest[:-1]


def run_react_loop(task: str, max_steps: int) -> tuple[str, list[Step]]:
    trajectory: list[Step] = []

    for _ in range(max_steps):
        thought, action = decide_next_step(task, trajectory)
        name, arg = parse_action(action)

        if name == "finish":
            trajectory.append(Step(thought, action, arg))
            return arg, trajectory

        if name != "search":
            raise ValueError(f"Unknown action. {name}")

        observation = environment_search(arg)
        trajectory.append(Step(thought, action, observation))

    raise RuntimeError("Step budget exhausted without reaching finish[...]")


if __name__ == "__main__":
    answer, trajectory = run_react_loop(
        "What years was the Colorado orogeny active?", max_steps=5
    )
    for step in trajectory:
        print(f"Thought. {step.thought}")
        print(f"Action. {step.action}")
        print(f"Observation. {step.observation}")
    print(f"Answer. {answer}")
```

### Go

```go
package main

import (
	"fmt"
	"regexp"
	"strings"
)

type Step struct {
	Thought     string
	Action      string
	Observation string
}

// environmentSearch stands in for a real search API. A production build
// replaces this with a call to a search index or knowledge base.
func environmentSearch(query string) string {
	knowledgeBase := map[string]string{
		"colorado orogeny": "The Colorado orogeny was an episode of mountain building in Colorado and surrounding areas, active roughly 1780 to 1650 million years ago.",
		"colorado orogeny elevation": "The eastern sector of the Colorado orogeny extends into the High Plains and is called the Central Plains orogeny.",
	}
	key := strings.ToLower(strings.TrimSpace(query))
	if v, ok := knowledgeBase[key]; ok {
		return v
	}
	return "Nothing Found"
}

// decideNextStep stands in for a language model call. Given the trajectory
// so far, decide the next Thought and Action. A production build replaces
// this with a call to an LLM provider, passing the trajectory as context.
func decideNextStep(history []Step) (thought string, action string) {
	if len(history) == 0 {
		return "I need to find out what the Colorado orogeny is before I can answer.",
			"search[colorado orogeny]"
	}
	last := history[len(history)-1]
	if last.Observation != "Nothing Found" && len(history) == 1 {
		return "I have a definition. The question also asks about elevation range, I should search that specifically.",
			"search[colorado orogeny elevation]"
	}
	return "I now have enough information to answer the question.",
		fmt.Sprintf("finish[%s]", last.Observation)
}

var actionPattern = regexp.MustCompile(`^(\w+)\[(.*)\]$`)

func parseAction(action string) (name string, arg string, err error) {
	m := actionPattern.FindStringSubmatch(action)
	if m == nil {
		return "", "", fmt.Errorf("malformed action. %s", action)
	}
	return m[1], m[2], nil
}

func runReActLoop(maxSteps int) (answer string, trajectory []Step, err error) {
	for i := 0; i < maxSteps; i++ {
		thought, action := decideNextStep(trajectory)
		name, arg, parseErr := parseAction(action)
		if parseErr != nil {
			return "", trajectory, parseErr
		}

		if name == "finish" {
			trajectory = append(trajectory, Step{thought, action, arg})
			return arg, trajectory, nil
		}

		if name != "search" {
			return "", trajectory, fmt.Errorf("unknown action. %s", name)
		}

		observation := environmentSearch(arg)
		trajectory = append(trajectory, Step{thought, action, observation})
	}
	return "", trajectory, fmt.Errorf("step budget exhausted without reaching finish[...]")
}

func main() {
	answer, trajectory, err := runReActLoop(5)
	if err != nil {
		fmt.Println("error.", err)
		return
	}
	for _, step := range trajectory {
		fmt.Println("Thought.", step.Thought)
		fmt.Println("Action.", step.Action)
		fmt.Println("Observation.", step.Observation)
	}
	fmt.Println("Answer.", answer)
}
```

Java, Rust, Swift, and Kotlin are omitted from this entry. The pattern is a
control-flow and prompt-structuring technique rather than a language
feature, and the loop above translates directly and without idiomatic loss
into any of them, the three languages shown are sufficient to demonstrate
that directness across a dynamically typed, a statically typed with
structural regex parsing, and a compiled systems-language shape.
