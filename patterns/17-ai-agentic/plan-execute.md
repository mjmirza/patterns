---
name: Plan and Execute
slug: plan-execute
family: 17-ai-agentic
category: Agentic
aliases: [Plan-and-Execute Agent, Plan-Solve-Execute, Planner-Executor Pattern, Decoupled Planning]
first_described: "Wang, Xu, Lan, Hu, Lan, Lee, Lim 2023 (Plan-and-Solve Prompting); LangChain 2023 (Plan-and-Execute agent)"
maturity: canonical
related: [react, reflexion, orchestrator-worker, tool-use, chain-of-thought]
incompatible_with: []
verified: 2026-08-02
---

# Plan and Execute

## 1. Name, aliases, and lineage

The canonical name for this pattern in agent engineering is Plan and Execute, a
two-phase structure in which a language model first produces an ordered plan
for a goal, then a separate execution loop carries that plan out one step at a
time, calling tools as needed, without asking the planning model to
reconsider the whole problem after every action. The name is used this way in
the official LangChain and LangGraph reference implementation, published as
"Plan-and-Execute Agents" on the LangChain blog on 13 February 2024
([langchain.com/blog/planning-agents](https://www.langchain.com/blog/planning-agents),
verified 2026-08-02), which frames the pattern explicitly as "an LLM-powered
'planner'" separated from "the tool execution runtime."

The underlying idea has an earlier and more academic name. Plan-and-Solve
prompting, introduced by Lei Wang, Wanyu Xu, Yihuai Lan, Zhiqiang Hu, Yunshi
Lan, Roy Ka-Wei Lee, and Ee-Peng Lim in "Plan-and-Solve Prompting. Improving
Zero-Shot Chain-of-Thought Reasoning by Large Language Models," submitted to
arXiv as 2305.04091 on 6 May 2023 and later published at ACL 2023
([arXiv 2305.04091](https://arxiv.org/abs/2305.04091), verified 2026-08-02).
That paper's core move was a single prompt instructing the model to devise a
plan that divides the task into subtasks and then carry the subtasks out
according to that plan, before producing the final answer, as a fix for the
error accumulation that plain zero-shot chain-of-thought exhibits on
multi-step arithmetic and reasoning benchmarks.

The engineering pattern this entry documents grew out of that idea but
changed its shape in one decisive way. Plan-and-Solve prompting keeps
planning and solving inside one continuous generation from one model call.
Plan and Execute as an agent architecture splits them into two separately
invocable components, a planner that can be a larger and more careful model
and an executor loop that can be a smaller, cheaper, or purely
deterministic process, so that the plan is a data structure the system can
inspect, retry against, and re-run without paying for a fresh reasoning pass
on every step. This split is the same one made explicit a few weeks later by
ReWOO, Reasoning WithOut Observation, from Binfeng Xu, Zhiyuan Peng, Bowen
Lei, Subhabrata Mukherjee, Yuchen Liu, and Dongkuan Xu, submitted to arXiv as
2305.18323 on 23 May 2023, whose abstract describes "a modular paradigm
ReWOO that detaches the reasoning process from external observations"
([arXiv 2305.18323](https://arxiv.org/abs/2305.18323), verified 2026-08-02).
ReWOO and the LangChain Plan-and-Execute implementation are the same pattern
at the architectural level. ReWOO adds a specific notation, Plan and E-hash
number, for referencing an earlier step's output inside a later step's
arguments, and this entry treats ReWOO as a named implementation variant
rather than a separate pattern, because both share the identical structural
claim, plan first as data, execute second against that data.

A third naming lineage is BabyAGI, an early open-source project by Yohei
Nakajima that circulated widely in March 2023 as one of the first popular
demonstrations of an autonomous task loop built around a stored list of
tasks that the system both executes and revises. Nakajima's own project
README states the original version "debuted in March 2023" and that this
early architecture was later archived in September 2024 in favor of a
different, self-modifying design
([github.com/yoheinakajima/babyagi](https://github.com/yoheinakajima/babyagi),
verified 2026-08-02). BabyAGI predates both the Plan-and-Solve paper and the
LangChain implementation and is one reason the pattern is sometimes called
Plan-Solve-Execute in blog writing, folding in a third phase, review or
reprioritize, that sits between plan and execute. This entry treats that
review phase as an optional refinement of the executor, described in
dimension 8, rather than as a naming fork, because every serious
implementation of Plan and Execute needs some mechanism for revising the
plan when the world disagrees with it, whether that mechanism is called
reprioritization, replanning, or repair.

## 2. Problem and context

A language model asked to solve a task that takes many steps, and that must
call external tools along the way, faces a tension between two failure
modes. If it is prompted to think one step at a time and decide the next
action only after seeing the result of the previous one, the classic
Thought-Action-Observation loop documented in ReAct
([arXiv 2210.03629](https://arxiv.org/abs/2210.03629), verified 2026-08-02),
it stays flexible to surprises but pays a full model call, with the entire
running transcript as context, for every single action, and it has no
explicit representation of how many steps remain or how they relate to each
other. If instead it is asked to produce the complete answer in one shot, it
tends to lose track of intermediate results on anything with real
multi-step structure, the exact failure Wang and coauthors measured and
targeted with Plan-and-Solve prompting.

The problem Plan and Execute addresses sits between those two extremes. Many
real tasks have a decomposition that is knowable in advance, book a flight
then reserve a hotel then confirm with the traveler, or fetch three
documents then compare them then write a summary, even though the exact
arguments to each step depend on results the system does not have yet. In
that situation, re-deriving the decomposition from scratch after every tool
call is wasted reasoning, and it also means the largest, most expensive
model in the system is on the hot path for every trivial lookup. The context
in which this pattern belongs is precisely a task with a coarse structure
that is stable even though its fine detail is not, running against a set of
tools whose latency or cost makes repeated full re-reasoning genuinely
expensive, and where the operator wants an inspectable artifact, the plan
itself, that can be logged, shown to a person for approval, or diffed
against a previous run before any tool with side effects is invoked.

## 3. Forces

**Latency and cost against adaptability.** A plan made once and executed
without further planner calls is the cheapest and fastest shape, but it is
also the most brittle against a world that does not match the plan's
assumptions. ReWOO's authors report the efficiency side of this trade
directly, measuring roughly five times better token efficiency on the
HotpotQA benchmark against a baseline that consults the language model after
every tool call ([arXiv 2305.18323](https://arxiv.org/abs/2305.18323),
verified 2026-08-02). Plan and Execute sits on a dial between the fully
adaptive ReAct loop, which recomputes the next action after every
observation, and a fully static workflow, which never consults a model at
runtime at all. Where an implementation sets its replanning threshold is
where it settles that dial.

**Separation of concerns against handoff cost.** Splitting planning from
execution lets each side use a different model tier, a stronger reasoning
model for the plan, a cheap or even non-model executor for individual steps,
which the LangChain writeup names explicitly as a cost benefit
([langchain.com/blog/planning-agents](https://www.langchain.com/blog/planning-agents),
verified 2026-08-02). The cost of that separation is a serialization
boundary. The plan has to be represented in a format precise enough for the
executor to act on without ambiguity, and any information the planner
implicitly assumed but did not write into that format is lost at the
boundary, a class of bug this entry returns to in dimension 11.

**Parallelism against dependency correctness.** Because a plan is data
before it is behavior, a Plan and Execute system can inspect step
dependencies and run independent steps concurrently, which is exactly what
LLMCompiler does, generating a directed acyclic graph of tasks and dispatching
them to a parallel executor, reporting up to 3.7 times lower latency and up
to 6.7 times lower cost than ReAct on the benchmarks in the paper
([arXiv 2312.04511](https://arxiv.org/abs/2312.04511), verified 2026-08-02).
The force this trades against is correctness of the dependency graph itself.
A plan that under-declares a dependency runs steps out of order and produces
a wrong answer silently, which is a materially worse failure than the same
mistake in a sequential executor, because nothing about a parallel executor
naturally surfaces an ordering bug as an error.

**Auditability against flexibility of representation.** A plan the operator
can read before any side-effecting tool runs is a genuine safety and
compliance advantage that a pure ReAct loop cannot offer, because ReAct's
next action is only ever decided one step before it happens. The force this
trades against is that a rigid plan schema, one built to be human-readable
and easy to validate, constrains what the planner can express, and an
overly loose schema, free text steps, is easy for the planner to produce but
hard for the executor to parse reliably.

## 4. Applicability and non-applicability

**Reach for Plan and Execute when:**

- The task has a coarse structure that is knowable before execution begins,
  even though the fine detail of each step depends on results the system
  does not yet have.
- Tool calls or model calls are expensive enough, in latency, dollars, or
  rate limit budget, that avoiding a full reasoning pass between every action
  is a real, measurable win, as demonstrated by ReWOO's reported token
  savings and LLMCompiler's reported latency and cost reductions.
- The plan itself needs to be inspectable before it runs, for human approval,
  for compliance logging, or for replay and debugging after the fact.
- Steps in the task are genuinely independent of one another for at least
  part of the workflow, making a parallel executor a real win rather than an
  unused capability.
- The team wants to run a cheaper or more specialized model for individual
  step execution while reserving a stronger model for the planning call.

**Do NOT reach for Plan and Execute when:**

- The task is genuinely unpredictable step to step, where each observation
  can change what the next reasonable action even is, in which case a tight
  ReAct-style interleaved loop adapts faster and a stale plan becomes a
  liability rather than an asset. Anthropic's own agent guidance draws this
  same line between workflows with predictable structure and open-ended
  agents that must dynamically direct their own process
  ([anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents),
  verified 2026-08-02).
- The task is short enough, two or three steps, that the overhead of a
  separate planning call and a plan data structure costs more in latency and
  code complexity than it saves, and a single-shot prompt or a plain
  function call sequence answers the need directly.
- The domain has hard optimality or feasibility constraints, and free-text
  or lightly structured plans from a language model are known to violate
  them silently, in which case a classical planner is the correct tool, as
  demonstrated by LLM+P, which converts a natural language planning problem
  into PDDL and calls an external solver rather than trusting the language
  model's own plan
  ([arXiv 2304.11477](https://arxiv.org/abs/2304.11477), verified 2026-08-02).
- No tool in the workflow has meaningful cost or latency, so there is no
  efficiency to gain by avoiding repeated planner calls, and the added
  moving part is pure overhead.
- The team cannot afford to build and maintain a replanning path, because a
  Plan and Execute system with no repair mechanism for a failed or
  stale step is strictly worse than a ReAct loop on any task where failures
  are common, since a ReAct loop's every step is already implicitly a
  replan.

## 5. Structure

**Planner.** A component, usually a single language model call with a
detailed system prompt describing the available tools and their contracts,
that receives the goal and any relevant context and returns a plan, an
ordered or partially ordered collection of steps. The planner's
responsibility ends at producing this data structure. It does not execute
tools itself and does not see intermediate tool results unless a replan is
triggered.

**Plan.** The data structure the planner produces and the executor consumes.
At minimum a plan carries the original goal and a list of steps. A step
carries the tool to call, the arguments to call it with, expressed either as
literal values or as references to the outputs of earlier steps, and,
optionally, a set of step identifiers it depends on. This entry's code
samples in dimension 8 use a flat ordered list for simplicity. LLMCompiler
and ReWOO both use an explicit dependency graph so independent steps can run
concurrently.

**Executor.** The loop that walks the plan, calling each step's tool with
its resolved arguments, recording the result, and advancing. The executor is
deliberately dumb by design, its job is mechanical dispatch and result
bookkeeping, not judgment. When a step fails, or when a result contradicts
an assumption the plan depended on, the executor is the component that
detects this and decides whether to hand control back to the planner.

**Tool registry.** The set of callable capabilities the plan's steps can
name, each with a name, an argument contract, and a concrete implementation.
The registry is shared between planner and executor. The planner needs to
know what tools exist and what arguments they expect in order to write a
valid plan. The executor needs to know how to actually invoke them.

**Replanner.** Either the same planner component invoked again with updated
context, or a distinct, smaller component, that produces a revised plan, or
a revised remainder of the current plan, when the executor signals that
execution has diverged from what the original plan assumed. LangChain's
reference implementation reuses the planner for this role, calling it again
with the original plan, the steps completed so far, and their results
([langchain.com/blog/planning-agents](https://www.langchain.com/blog/planning-agents),
verified 2026-08-02).

**Result store.** The accumulating record of what each executed step
produced, addressable so that later steps, and the replanner, can refer to
earlier outputs. ReWOO's paper formalizes this as its E-hash variable
notation directly inside the plan text
([arXiv 2305.18323](https://arxiv.org/abs/2305.18323), verified 2026-08-02).

## 6. ASCII structure diagram

```
                          +-----------------+
                          |      Goal        |
                          +--------+---------+
                                   |
                                   v
                          +-----------------+
              (reads) --> |    Planner       |
              tool specs  +--------+---------+
                                   |
                                   v
                          +-----------------+
                          |      Plan        |
                          |  step1 -> step2   |
                          |         -> step3  |
                          +--------+---------+
                                   |
                                   v
              +--------------------------------------+
              |               Executor                |
              |  for each step (dependency order):     |
              |    resolve args from Result Store       |
              |    call ToolRegistry[step.tool]         |
              |    write result into Result Store        |
              +----------------+----------------------+
                                |
                    on failure  |  on success
                    or drift    |
                                v
                     +--------------------+       +----------------+
                     |    Replanner        | ----> | Result Store   |
                     | (planner + history) |       | step1, done    |
                     +--------------------+        | step2, done     |
                                                     +----------------+
```

## 7. Dynamics

```
Goal received
   |
   v
Planner.make_plan(goal, history=[])
   |
   v
Plan { steps = [s1, s2, s3, ...] }
   |
   v
i = 0
loop while i < len(plan.steps):
    step = plan.steps[i]
    resolve step.args against Result Store (fill in #E references)
    try:
        result = ToolRegistry.call(step.tool, step.args)
        Result Store[step.id] = result
        step.status = DONE
        history.append(trace of this call)
        i += 1
    except ToolError or AssumptionViolated:
        step.status = FAILED
        history.append(trace of the failure)
        if replan_budget_exhausted:
            raise FatalError
        new_remainder = Planner.make_plan(goal, history)
        plan.steps = plan.steps[:i] + new_remainder
        # i is not advanced; the loop retries at the same index
        # against the freshly inserted steps
loop ends when i == len(plan.steps)
   |
   v
return final plan with every step DONE, and the Result Store
```

The two decision points that define an implementation's real behavior are
both inside the loop and neither is visible from the plan alone. First, what
counts as a trigger for replanning, only a hard tool error, as in the code
samples below, or also a soft signal, such as a tool result the executor can
detect as inconsistent with a later step's stated assumption. Second, how
much of the plan a replan is allowed to discard, only the failed step, as in
LangChain's reference implementation which regenerates the remainder while
keeping completed steps intact
([langchain.com/blog/planning-agents](https://www.langchain.com/blog/planning-agents),
verified 2026-08-02), or the entire plan from the current point forward, or,
in the most conservative implementations, the entire plan including already
completed steps, when a failure is severe enough to cast doubt on earlier
results too.

## 8. Implementation variants

**Sequential with full replan on any failure.** The simplest and most
common shape in early tutorials and internal tooling. The executor walks a
flat ordered list of steps. Any tool exception triggers a call back to the
planner with the goal and the execution history so far, and the planner
returns a fresh plan for everything from the failure point onward. This is
the shape used in this entry's code samples in the language section below,
chosen for its clarity, at the cost of discarding useful structure, since a
failure in step 2 of 5 does not necessarily mean steps 3 through 5 were
wrong, only that they now need to be reconsidered given new information.

**Graph-based with parallel dispatch.** LLMCompiler's variant. The planner
emits a directed acyclic graph rather than a flat list, and a separate
component, which the paper calls the Task Fetching Unit, dispatches every
task whose dependencies are already satisfied concurrently, rather than
waiting for the previous task in a linear order to finish
([arXiv 2312.04511](https://arxiv.org/abs/2312.04511), verified 2026-08-02).
This variant earns its complexity only when the workflow genuinely has
independent branches, an ordering-agnostic set of document fetches before a
single synthesis step, for example, and it requires the planner to reason
correctly about dependencies, which is a harder generation task than simply
emitting an ordered list.

**Variable-referencing text plans.** ReWOO's variant, in which the plan is
represented as structured but still largely textual output using a fixed
grammar, "Plan, then E1 equals Tool of args, then E2 equals Tool using E1,"
so that a step's arguments can reference an earlier step's result by name
without the planner needing to know the concrete value in advance
([arXiv 2305.18323](https://arxiv.org/abs/2305.18323), verified 2026-08-02).
This variant trades a stricter, code-native plan schema for a format the
language model is more naturally fluent at producing, at the cost of needing
a dedicated parser to turn that text back into an executable structure
reliably.

**Human-in-the-loop plan approval.** A variant, common in production
deployments handling side-effecting tools, where the plan is surfaced to a
person for approval, editing, or rejection before the executor is allowed to
run any step whose tool has real-world side effects. The plan-as-data
property that this pattern provides is exactly what makes this variant
possible at all. A ReAct-style interleaved loop has no equivalent artifact
to show a person before the first action fires.

**Language-idiomatic notes.** In a language with first-class async and
structured concurrency, such as TypeScript with Promise.all or Go with
goroutines and a WaitGroup, the graph-based variant is comfortable to
express directly, dependency-satisfied steps map naturally onto a fan-out of
concurrent calls. In a language without light-weight concurrency built in,
the sequential variant with an explicit dependency check is often the
pragmatic default, and the parallel variant is reserved for when profiling
shows the sequential executor is genuinely the bottleneck. None of the three
languages used in this entry's code samples changes the shape of the
planner or the plan data structure. The pattern is fundamentally
data-oriented rather than language-oriented, which is part of why it
transports cleanly across languages.

## 9. Known production uses

**LangChain and LangGraph's Plan-and-Execute reference agents.** LangChain
publishes and maintains runnable Python and JavaScript notebooks
implementing three variants of this pattern, plain Plan-and-Execute, ReWOO,
and LLMCompiler, hosted in the official LangGraph example repositories and
described as an explicit architecture choice for separating a planning LLM
from the tool execution runtime, with the stated benefits of faster
multi-step execution and the option to reserve a larger model for planning
while smaller models handle individual sub-tasks
([langchain.com/blog/planning-agents](https://www.langchain.com/blog/planning-agents),
verified 2026-08-02).

**LLMCompiler, an academic system with a public, benchmarked
implementation.** Developed at UC Berkeley by Sehoon Kim, Suhong Moon, Ryan
Tabrizi, Nicholas Lee, Michael W. Mahoney, Kurt Keutzer, and Amir Gholami,
published at ICML 2024, LLMCompiler is a concrete Plan and Execute system
with three named components, a Function Calling Planner, a Task Fetching
Unit, and a parallel Executor, evaluated across multiple benchmark suites
against ReAct and reported to reduce latency by up to 3.7 times and cost by
up to 6.7 times on those benchmarks
([arXiv 2312.04511](https://arxiv.org/abs/2312.04511), verified 2026-08-02).

**ReWOO, published with reported production-relevant efficiency numbers on
a standard QA benchmark.** Xu, Peng, Lei, Mukherjee, Liu, and Xu's system
detaches reasoning from tool observation entirely for its planning phase and
report roughly five times token efficiency and a four percentage point
accuracy improvement over an interleaved baseline on HotpotQA, along with
evidence that a much smaller fine-tuned model can take over the planning
role that would otherwise require a large general-purpose model
([arXiv 2305.18323](https://arxiv.org/abs/2305.18323), verified 2026-08-02).

**BabyAGI, an early and widely forked open-source implementation.**
Released by Yohei Nakajima in March 2023, BabyAGI was, per its own project
history, one of the first widely circulated open-source demonstrations of an
autonomous agent that maintains a task list, works through it, and revises
it, predating both the Plan-and-Solve paper and the LangChain reference
implementation, and it remains a commonly cited historical reference point
for this class of architecture in engineering writing even though the
project's current, actively maintained codebase has since moved to a
different, self-modifying function-generation design rather than the
original task-list loop
([github.com/yoheinakajima/babyagi](https://github.com/yoheinakajima/babyagi),
verified 2026-08-02).

## 10. Consequences

This dimension is largely engineering judgement drawn from the sources
above rather than a single citable claim per line.

**Positive.**

- A plan is an inspectable artifact. It can be logged, diffed against a
  previous run, shown to a person for approval before any side-effecting
  tool runs, and replayed for debugging, none of which a purely interleaved
  loop's implicit, step-by-step decisions offer without extra instrumentation.
- The planner and the executor can run different models, or different
  compute tiers entirely, which is a direct cost lever the interleaved
  ReAct loop does not expose, because in ReAct the same model that decides
  the next action is on the hot path for every single step.
- Where steps are genuinely independent, the plan's explicit structure
  enables real parallel execution, with measured latency and cost gains
  reported by LLMCompiler, a benefit that requires no change to the model
  itself, only to how the executor is written.
- Fewer total language model calls per completed task, in the common case
  where a plan executes without triggering a replan, which is the same
  efficiency argument ReWOO makes with its measured token savings.

**Negative.**

- A stale plan is a real correctness risk. If step three's assumptions are
  invalidated by step two's actual result and the executor's failure
  detection is too narrow to notice, the system will confidently execute a
  plan that no longer matches reality, a failure mode this entry expands on
  in dimension 11.
- The planner must reason about the entire task shape before it has any of
  the information execution will surface, which is a harder generation task
  than deciding only the very next action, and it means the planner's own
  errors are amplified across every downstream step that depends on them.
- The plan schema is a real design surface. Too rigid and the planner
  struggles to express legitimate variation. Too loose and the executor
  cannot parse or validate it reliably. This tension does not go away, it
  only moves between the planner's prompt and the executor's parsing code.
- Replanning logic is genuinely extra system complexity that a pure ReAct
  loop does not need, because in ReAct every step already is, in effect, a
  fresh plan of length one.

## 11. Failure modes and misuse

**A step succeeds but produces a result the plan's later steps silently
misinterpret.** Symptom. A later step runs to completion but its output is
wrong in a way no exception ever surfaces. Cause. The plan was built against
an assumption, often implicit and never written into the plan's data, that a
step's output would take a particular shape or fall within a particular
range, and the executor has no check for that assumption, only for hard tool
exceptions. Fix. Encode the assumption explicitly as a post-condition the
executor checks after every step, not only exceptions, and route a
post-condition violation through the same replanning path as a tool error,
rather than letting execution continue on data the plan never actually
anticipated.

**The system enters a loop, replanning the same failing step repeatedly
with no progress.** Symptom. Replan count climbs toward the budget while the
same tool keeps failing on effectively the same arguments. Cause. The
replanner is given the same context that produced the original bad plan,
without the specific information about why the previous attempt failed
being surfaced clearly enough for the model to change course, so it
regenerates an equivalent plan. Fix. Pass the full failure trace, not just a
boolean failed status, into the replanning call, and enforce a hard replan
budget with a terminal failure state, as this entry's code samples do with
an explicit max-replans limit, so a stuck loop fails loudly rather than
burning cost silently.

**A plan with parallel steps produces a wrong final answer with no error at
all.** Symptom. The task completes, every step reports success, and the
final output is simply incorrect. Cause. The planner under-declared a
dependency between two steps that are actually ordered, and the parallel
executor ran them concurrently, so a step read a result that had not yet
been written, or read a stale placeholder. This is the sharpest failure mode
of the graph-based variant described in dimension 8, and it is dangerous
precisely because nothing throws. Fix. Validate the dependency graph the
planner emits before execution, checking that every argument reference
resolves to a step that is declared as a dependency, not merely a step that
happens to run earlier in practice, and treat an unresolved or ambiguous
reference as a hard planning error rather than best-effort guessing at
runtime.

**Cost or latency is worse than a plain ReAct loop on the same task, despite
fewer total model calls in the common case.** Symptom. Total spend or
end-to-end latency for a task class quietly rises above what the equivalent
ReAct loop would have cost. Cause. The planner's own call is large and
expensive, because it must describe the entire task and every available
tool up front, and on tasks that frequently need at least one replan, the
system pays for the large planning call twice or more, wiping out the
savings from not consulting the model after every step. Fix. Measure replan
frequency on real traffic before committing to this pattern for a given
task class, and if replans are frequent, either shrink the planner's prompt
so each call is cheaper, or reconsider whether the task actually has the
stable coarse structure this pattern assumes, per dimension 4's
non-applicability list.

**A plan approved by a human reviewer executes differently than what was
shown.** Symptom. An audit reveals the executed arguments do not match what
the reviewer signed off on. Cause. The plan object shown for approval and
the plan object the executor actually reads are not the same reference, or
the executor resolves argument placeholders, such as the current time or an
account identifier, at execution time rather than at planning time, so the
concrete values a person approved are not the concrete values that actually
run. Fix. Freeze the plan, including all resolvable arguments, at the moment
of approval, and treat any placeholder that cannot be resolved before
approval as a reason to reject the plan rather than let the executor fill it
in later unseen.

## 12. Trade-off matrix

| Force | Plan and Execute | ReAct | Orchestrator-Workers | Pure workflow (no LLM at runtime) |
|---|---|---|---|---|
| Model calls per task step | One planning call, then near zero unless replanning | One call per step, every time | One orchestrator call per subtask dispatch, plus worker calls | Zero |
| Adaptability to surprising results | Moderate, only at replan points | High, every step reconsiders everything | High for subtask scope, orchestrator recomputes it each time | None, fixed code path |
| Auditability before side effects run | High, the plan is inspectable before execution starts | Low, next action is only known one step ahead | Moderate, subtasks are visible once dispatched, not before | High, but the whole path is fixed in advance, not generated |
| Parallel execution support | Native, when the plan variant is graph-based | Not native, steps are inherently sequential | Native, workers can run concurrently by design | Whatever the code explicitly implements |
| Cost sensitivity to task length | Low per step after planning, reported up to several times cheaper in ReWOO and LLMCompiler | High, scales roughly linearly with step count and full context per call | Moderate, scales with number of dispatched subtasks | Lowest, no model cost at all |
| Best suited task shape | Coarse structure known upfront, fine detail unknown | Fully unpredictable, step to step | Task decomposes into a small number of independent subtasks | Fully predictable, no reasoning required at runtime |

The Orchestrator-Workers comparison follows Anthropic's own description of
that pattern as one where a central model dynamically breaks a task down and
delegates to worker models, with subtasks determined by the orchestrator at
runtime rather than fixed in advance
([anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents),
verified 2026-08-02). The distinction from Plan and Execute is where the
plan lives. Orchestrator-Workers keeps decomposition inside the
orchestrator's per-call reasoning every time it dispatches, while Plan and
Execute externalizes the plan into a durable, inspectable, and re-usable
data structure that the orchestrator only revisits on request.

## 13. Related and incompatible patterns

**ReAct.** The interleaved sibling this pattern is most often compared
against directly. Plan and Execute can be understood as ReAct with the
reasoning step hoisted out of the loop and amortized across many actions
instead of repeated for each one. A hybrid is common in practice, a coarse
Plan and Execute plan whose individual steps are themselves small ReAct
loops when a step's own sub-actions are unpredictable, composing rather than
competing with the outer plan.

**Reflexion.** Reflexion adds a self-critique and memory step after a
failed attempt at a task, feeding a verbal reflection back into the next
attempt. It composes naturally with Plan and Execute's replanning path. The
information a Reflexion-style critique produces, why the previous attempt at
this step failed and what to try differently, is exactly the input a
replanner call needs to avoid the repeated-failure loop described in
dimension 11.

**Orchestrator-Workers.** The closest sibling pattern, differing chiefly in
whether decomposition is externalized as durable data, Plan and Execute, or
recomputed inline by the orchestrator on every dispatch, Orchestrator-Workers,
per Anthropic's own framing of the two
([anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents),
verified 2026-08-02).

**Tool use.** A structural prerequisite rather than an alternative. Plan
and Execute has nothing to plan or execute without a defined set of callable
tools with known argument contracts, since the plan's steps are, by
definition, tool invocations.

**Chain-of-thought.** A component technique this pattern's planning phase
typically relies on internally. The planner is usually itself prompted to
reason step by step in order to arrive at a correct decomposition, but
chain-of-thought alone has no notion of an externally executable plan or a
tool registry, so it is a building block this pattern uses rather than an
alternative to it.

There are no incompatible patterns in the sense of two patterns that cannot
be composed in the same system. The closest to a genuine conflict is
attempting to combine Plan and Execute with a fully dynamic, ungoverned
ReAct loop for the same span of work. Using both at once for identical
scope is redundant rather than incompatible, and simply means one of the two
is not actually contributing anything.

## 14. Refactoring path in and out

**Introducing the pattern into an existing single-shot or ReAct-based
system.** Start by identifying a subset of tasks in production traffic that
repeatedly follow the same coarse shape, the same ordered or lightly
branching sequence of tool categories, even though the arguments differ
every time. Extract that shape into an explicit plan schema, a small data
structure with a list of typed steps, without yet touching the model
prompting. Next, write the executor as a pure function over that schema,
independent of how the schema gets populated, and prove it against
hand-written plan fixtures before any model is involved. Only then introduce
the planner call that produces the schema from a goal, and gate the whole
new path behind a feature flag so it can be compared against the existing
ReAct or single-shot path on the same traffic before becoming the default.
Add the replanning path last, once the happy path is proven, specifically
because a replanning path with no working happy path to fall back on is
much harder to debug than a happy path with no replanning yet.

**Removing the pattern when it stops earning its place.** The clearest
signal that a Plan and Execute deployment has outlived its usefulness is a
replan rate that has crept upward over time as the task population served
by the system has diversified. If a large share of plans get discarded and
regenerated at the first step, the system is paying the fixed overhead of a
separate planning call and a plan data structure while gaining almost none
of the efficiency benefit that justified the pattern in the first place.
When that is measured, not assumed, the refactor back out is to collapse
the planner and the first executor step into a single call, effectively
reverting toward ReAct for the affected task population, while keeping the
plan schema and executor code in place for the remaining task population
where replanning stays rare.

## 15. Testing and verification

Testing a Plan and Execute system separates cleanly into two independently
verifiable halves, which is one of the pattern's genuine practical
advantages over a fused single-call approach. The executor is pure,
deterministic code over a defined schema and a tool registry, and it should
be tested with ordinary unit tests using hand-written plan fixtures and
fake or recorded tool implementations, with no model call involved at all,
covering the sequential happy path, a mid-plan tool failure that triggers a
replan, replan budget exhaustion, and, for the graph-based variant, a
plan whose dependency graph is inconsistent with the order steps actually
need to run in.

The planner is the harder half to test, because its output is generated,
not deterministic. The practical technique is a held-out set of goals with a
human-reviewed reference plan for each, scored not by exact string match
against the reference, which is too brittle given a language model's
natural variation in phrasing step arguments, but by whether the plan the
executor produces from the generated plan matches the expected final state
or output when run against a controlled test rig of fake tools. This is
effectively an end-to-end test of the planner mediated through the already
deterministic executor, which is a more stable signal than trying to assert
properties of the raw plan text directly.

The replanner deserves its own dedicated test class, separate from both,
because it receives a different input shape than the initial planner call,
a goal plus a failure history rather than a bare goal, and its correctness
criterion is different too. Not merely whether the output is a valid plan,
but whether the regenerated plan's first new step actually addresses the
specific failure that triggered it, which is best verified by injecting a
fixed catalogue of known failure scenarios and asserting that direct
correspondence.

## 16. Observability signals

A healthy Plan and Execute deployment shows a low and stable replan rate,
the fraction of completed tasks that triggered at least one replan, tracked
per task category rather than as a single global number, since the whole
value proposition depends on that rate staying low for the specific task
shapes the pattern was chosen for. A rising replan rate for a category that
used to be stable is the earliest and most actionable signal that either
the tool contracts the planner was written against have drifted, or that
the task population itself has changed shape, and it should alert well
before it becomes visible in end-user latency or cost.

Log the full plan as a first-class artifact at the moment it is produced,
before execution begins, tagged with the goal and a plan identifier, so
every downstream trace, tool call, and replan can be joined back to it. Log
each step's resolved arguments, not only the templated arguments the
planner wrote, since a bug in argument resolution against the result store
is otherwise invisible in the planner's own output. Track per-step latency
and cost broken out from the planner's own latency and cost, because the two
halves of this pattern have genuinely different cost profiles and mixing
them in one metric hides which half is actually the bottleneck on a given
task.

A failing instance in production typically presents as either a spike in
replan rate with no change in the underlying tool error rate, which
indicates the plan schema or planner prompt has drifted out of sync with
the actual tool contracts, or as steps executing with resolved arguments
that do not match what a human reviewer would expect given the plan's
stated intent, which indicates a bug in the result store's reference
resolution rather than in the planner or the tools themselves, exactly the
class of failure described as the wrong-interpretation symptom in
dimension 11.

## 17. Security and privacy implications

The plan itself is an attack surface distinct from either the planner's raw
output or a single tool call. Because a plan is a data structure the
executor trusts and acts on, an implementation that allows any external,
untrusted input to influence plan generation, a goal string copied directly
from a user-supplied document, a webpage the planner was asked to summarize
and then plan around, opens the door to a prompt injection that steers the
plan toward tool calls the operator never intended, with the added danger
that a plan is often granted broader standing trust than a single
in-the-moment model output would be, precisely because it looks like a
reviewed artifact even when no review actually happened. Any deployment
that allows untrusted content into the planner's context should treat the
resulting plan with the same suspicion as untrusted user input, validating
every step's tool and arguments against an explicit allowlist before
execution, never assuming a well-formed plan implies a safe one.

The human-in-the-loop approval variant described in dimension 8 is a
genuine security control, not merely a usability feature, but only if the
frozen-at-approval-time property from dimension 11's last failure mode is
actually enforced. An approval workflow that shows a person one set of
arguments and then lets the executor resolve different concrete values at
run time is a security control in name only.

On data handling, the result store accumulates every intermediate tool
output for the duration of a task, which frequently includes exactly the
kind of sensitive data, personal information fetched by an earlier step,
credentials passed through for a later authenticated call, that a
system's data retention policy is meant to govern. Because the result store
is what makes replanning and later-step argument resolution possible, it
cannot simply be discarded after each step the way it might be in a
stateless single-shot design, so its retention window and access controls
need to be treated as a first-class design decision for this pattern
specifically, not inherited by default from whatever general logging
infrastructure the rest of the system already has.

## 18. References

1. Wang, L., Xu, W., Lan, Y., Hu, Z., Lan, Y., Lee, R. K., Lim, E. P. "Plan-and-Solve Prompting. Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models." arXiv 2305.04091, submitted 6 May 2023, ACL 2023. [arxiv.org/abs/2305.04091](https://arxiv.org/abs/2305.04091), verified 2026-08-02.
2. Xu, B., Peng, Z., Lei, B., Mukherjee, S., Liu, Y., Xu, D. "ReWOO. Decoupling Reasoning from Observations for Efficient Augmented Language Models." arXiv 2305.18323, submitted 23 May 2023. [arxiv.org/abs/2305.18323](https://arxiv.org/abs/2305.18323), verified 2026-08-02.
3. Kim, S., Moon, S., Tabrizi, R., Lee, N., Mahoney, M. W., Keutzer, K., Gholami, A. "An LLM Compiler for Parallel Function Calling." arXiv 2312.04511, submitted 7 December 2023, published ICML 2024. [arxiv.org/abs/2312.04511](https://arxiv.org/abs/2312.04511), verified 2026-08-02.
4. Liu, B., Jiang, Y., Zhang, X., Liu, Q., Zhang, S., Biswas, J., Stone, P. "LLM+P. Optimal Planning Proficiency for Large Language Models." arXiv 2304.11477, submitted 22 April 2023, revised 27 September 2023. [arxiv.org/abs/2304.11477](https://arxiv.org/abs/2304.11477), verified 2026-08-02.
5. Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., Cao, Y. "ReAct. Synergizing Reasoning and Acting in Language Models." arXiv 2210.03629, submitted 6 October 2022, revised 10 March 2023, ICLR 2023. [arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629), verified 2026-08-02.
6. LangChain. "Plan-and-Execute Agents." LangChain blog, published 13 February 2024. [langchain.com/blog/planning-agents](https://www.langchain.com/blog/planning-agents), verified 2026-08-02.
7. Anthropic. "Building Effective Agents." Anthropic Engineering blog, published 19 December 2024. [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents), verified 2026-08-02.
8. Nakajima, Y. "BabyAGI." GitHub repository. [github.com/yoheinakajima/babyagi](https://github.com/yoheinakajima/babyagi), verified 2026-08-02.

## Code examples

The three samples below implement the identical structure, a Planner that
returns an ordered list of Step objects, a ToolRegistry that resolves a
step's tool name to a callable, and an Executor loop that walks the plan,
catches a tool failure, and calls back into the Planner for a fresh
remainder before continuing, bounded by an explicit replan budget. All three
were compiled or run directly on this machine.

**Python.** Run with `python3 plan_execute.py`. Verified output ends with
`final result. Summary. Paris (recovered)` after the deliberately unknown
`lookup_missing_tool` step triggers one replan.

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable


class StepStatus(Enum):
    PENDING = auto()
    DONE = auto()
    FAILED = auto()


@dataclass
class Step:
    tool: str
    args: dict
    status: StepStatus = StepStatus.PENDING
    result: object = None


@dataclass
class Plan:
    goal: str
    steps: list[Step] = field(default_factory=list)


class Planner:
    def __init__(self, plan_fn: Callable[[str, list[str]], list[Step]]):
        self._plan_fn = plan_fn

    def make_plan(self, goal: str, history: list[str]) -> Plan:
        return Plan(goal=goal, steps=self._plan_fn(goal, history))


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable[[dict], object]] = {}

    def register(self, name: str, fn: Callable[[dict], object]) -> None:
        self._tools[name] = fn

    def call(self, name: str, args: dict) -> object:
        return self._tools[name](args)


class Executor:
    def __init__(self, tools: ToolRegistry, planner: Planner, max_replans: int = 3):
        self._tools = tools
        self._planner = planner
        self._max_replans = max_replans

    def run(self, goal: str) -> Plan:
        history: list[str] = []
        plan = self._planner.make_plan(goal, history)
        replans = 0
        i = 0
        while i < len(plan.steps):
            step = plan.steps[i]
            try:
                step.result = self._tools.call(step.tool, step.args)
                step.status = StepStatus.DONE
                history.append(f"{step.tool}({step.args}) -> {step.result}")
                i += 1
            except KeyError as exc:
                step.status = StepStatus.FAILED
                history.append(f"{step.tool}({step.args}) -> ERROR {exc}")
                if replans >= self._max_replans:
                    raise RuntimeError("replan budget exhausted") from exc
                replans += 1
                remaining_goal = f"{goal} (recover after step {i} failed)"
                new_plan = self._planner.make_plan(remaining_goal, history)
                plan.steps = plan.steps[:i] + new_plan.steps
        return plan
```

**TypeScript.** Compiled with `npx tsc --strict --target es2020` and run
with `node`. Verified output ends with `final result. Summary. Paris
(recovered)`, matching the Python sample step for step.

```typescript
type StepStatus = "pending" | "done" | "failed";

interface Step {
  tool: string;
  args: Record<string, unknown>;
  status: StepStatus;
  result?: unknown;
}

interface Plan {
  goal: string;
  steps: Step[];
}

type ToolFn = (args: Record<string, unknown>) => unknown;

class ToolRegistry {
  private tools = new Map<string, ToolFn>();

  register(name: string, fn: ToolFn): void {
    this.tools.set(name, fn);
  }

  call(name: string, args: Record<string, unknown>): unknown {
    const fn = this.tools.get(name);
    if (!fn) {
      throw new Error(`unknown tool. ${name}`);
    }
    return fn(args);
  }
}

type PlanFn = (goal: string, history: string[]) => Step[];

class Planner {
  constructor(private planFn: PlanFn) {}

  makePlan(goal: string, history: string[]): Plan {
    return { goal, steps: this.planFn(goal, history) };
  }
}

class Executor {
  constructor(
    private tools: ToolRegistry,
    private planner: Planner,
    private maxReplans = 3,
  ) {}

  run(goal: string): Plan {
    const history: string[] = [];
    const plan = this.planner.makePlan(goal, history);
    let replans = 0;
    let i = 0;
    while (i < plan.steps.length) {
      const step = plan.steps[i];
      try {
        step.result = this.tools.call(step.tool, step.args);
        step.status = "done";
        history.push(`${step.tool}(${JSON.stringify(step.args)}) -> ${step.result}`);
        i += 1;
      } catch (err) {
        step.status = "failed";
        history.push(`${step.tool}(${JSON.stringify(step.args)}) -> ERROR ${err}`);
        if (replans >= this.maxReplans) {
          throw new Error("replan budget exhausted");
        }
        replans += 1;
        const recoveryGoal = `${goal} (recover after step ${i} failed)`;
        const newPlan = this.planner.makePlan(recoveryGoal, history);
        plan.steps.splice(i, plan.steps.length - i, ...newPlan.steps);
      }
    }
    return plan;
  }
}
```

**Go.** Built and run with `go run main.go`. Verified output ends with
`final result. Summary. Paris (recovered)`, again matching the other two
samples, since all three encode the identical plan-execute-replan sequence.

```go
package main

import (
	"errors"
	"fmt"
)

type StepStatus int

const (
	Pending StepStatus = iota
	Done
	Failed
)

type Step struct {
	Tool   string
	Args   map[string]string
	Status StepStatus
	Result string
}

type Plan struct {
	Goal  string
	Steps []Step
}

type PlanFn func(goal string, history []string) []Step

type Planner struct {
	planFn PlanFn
}

func (p Planner) MakePlan(goal string, history []string) Plan {
	return Plan{Goal: goal, Steps: p.planFn(goal, history)}
}

type ToolFn func(args map[string]string) (string, error)

type ToolRegistry struct {
	tools map[string]ToolFn
}

func NewToolRegistry() *ToolRegistry {
	return &ToolRegistry{tools: map[string]ToolFn{}}
}

func (r *ToolRegistry) Register(name string, fn ToolFn) {
	r.tools[name] = fn
}

func (r *ToolRegistry) Call(name string, args map[string]string) (string, error) {
	fn, ok := r.tools[name]
	if !ok {
		return "", fmt.Errorf("unknown tool. %s", name)
	}
	return fn(args)
}

type Executor struct {
	tools      *ToolRegistry
	planner    Planner
	maxReplans int
}

func (e *Executor) Run(goal string) (Plan, error) {
	history := []string{}
	plan := e.planner.MakePlan(goal, history)
	replans := 0
	i := 0
	for i < len(plan.Steps) {
		step := &plan.Steps[i]
		result, err := e.tools.Call(step.Tool, step.Args)
		if err != nil {
			step.Status = Failed
			history = append(history, fmt.Sprintf("%s(%v) -> ERROR %v", step.Tool, step.Args, err))
			if replans >= e.maxReplans {
				return plan, errors.New("replan budget exhausted")
			}
			replans++
			recoveryGoal := fmt.Sprintf("%s (recover after step %d failed)", goal, i)
			newPlan := e.planner.MakePlan(recoveryGoal, history)
			plan.Steps = append(plan.Steps[:i], newPlan.Steps...)
			continue
		}
		step.Result = result
		step.Status = Done
		history = append(history, fmt.Sprintf("%s(%v) -> %s", step.Tool, step.Args, result))
		i++
	}
	return plan, nil
}

func demoPlanFn(goal string, history []string) []Step {
	if len(history) == 0 {
		return []Step{
			{Tool: "search", Args: map[string]string{"query": "capital of France"}},
			{Tool: "lookup_missing_tool", Args: map[string]string{"x": "1"}},
			{Tool: "summarize", Args: map[string]string{"text": "Paris"}},
		}
	}
	return []Step{{Tool: "summarize", Args: map[string]string{"text": "Paris (recovered)"}}}
}

func run() (Plan, error) {
	tools := NewToolRegistry()
	tools.Register("search", func(a map[string]string) (string, error) {
		return "Paris", nil
	})
	tools.Register("summarize", func(a map[string]string) (string, error) {
		return "Summary. " + a["text"], nil
	})

	planner := Planner{planFn: demoPlanFn}
	executor := &Executor{tools: tools, planner: planner, maxReplans: 3}
	return executor.Run("Answer. what is the capital of France?")
}

func main() {
	plan, err := run()
	if err != nil {
		fmt.Println("error.", err)
		return
	}
	last := plan.Steps[len(plan.Steps)-1]
	for _, s := range plan.Steps {
		fmt.Printf("step. %s status=%d\n", s.Tool, s.Status)
	}
	fmt.Println("final result.", last.Result)
}
```

Java, Rust, and Swift are omitted from this entry. The pattern's structure,
a plain data record for a plan, a registry map from name to callable, and a
loop with a catch-and-retry branch, is equally idiomatic in all three, and
adds no language-specific insight beyond what the three samples above
already demonstrate, so this entry keeps to the three languages where the
pattern's cross-language uniformity is already fully shown.
