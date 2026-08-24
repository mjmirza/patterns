---
name: Parallelization
slug: parallelization
family: 17-ai-agentic
category: AI Agentic
aliases: [Sectioning, Voting, Parallel Subagents, Fan-out Fan-in for LLMs, Map-Reduce Agent Pattern]
first_described: "Anthropic engineering team, Building Effective Agents, December 2024"
maturity: established
related: [orchestrator-worker, prompt-chaining, routing, self-consistency, plan-execute]
incompatible_with: []
verified: 2026-08-02
---

# Parallelization

## 1. Name, aliases, and lineage

The canonical name in current agentic-systems literature is Parallelization. It
was named and given a fixed shape by Anthropic's engineering team in the essay
"Building Effective Agents," published on the Anthropic engineering blog in
December 2024, as one of five named workflow patterns sitting between a single
augmented LLM call and a fully autonomous agent loop (Anthropic, "Building
Effective Agents," anthropic.com/engineering/building-effective-agents,
verified 2026-08-02). The essay states the core mechanism plainly, that "LLMs
can sometimes work simultaneously on a task and have their outputs aggregated
programmatically" (same source, verified 2026-08-02).

The name itself is older than the essay. Fan-out fan-in as a distributed
systems term predates LLM agents by decades and describes the identical
topology, one dispatcher splitting work across N workers followed by a
collector that joins the results, most visibly formalized in AWS Step
Functions as the `Parallel` state type in the Amazon States Language (AWS,
"Parallel state," docs.aws.amazon.com/step-functions/latest/dg/
amazon-states-language-parallel-state.html, verified 2026-08-02). What the
Anthropic essay adds is not the topology, it is the vocabulary for the two
distinct reasons an agentic system reaches for that topology when the workers
are LLM calls rather than deterministic functions, and it names those two
reasons Sectioning and Voting.

**Sectioning** is decomposition. A single task is broken into subtasks that are
independent of one another, each subtask is handed to its own LLM call, and
the outputs are combined. The essay's example is a content-moderation system
where "one model instance processes user queries while another screens them
for inappropriate content or requests," and it states this "tends to perform
better than having the same LLM call handle both tasks" (same source, verified
2026-08-02). The subtasks in Sectioning are different in kind. Each branch
answers a different question about the same input.

**Voting** is redundancy. The identical task is run more than once, usually
with the same prompt against the same input, and the outputs are reconciled by
a vote, a majority, or a consensus rule rather than a merge. The essay's
examples are code review, where "multiple different prompts to review code for
vulnerabilities" catch different classes of bug that a single pass misses, and
content moderation with "different vote thresholds to balance false positives
and negatives" (same source, verified 2026-08-02). The branches in Voting are
identical in kind and differ only in the sample of the model's output
distribution, or in a small prompt perturbation designed to elicit a different
angle on the same question.

Two related names appear in adjacent literature and describe the same shape
under a different label rather than a different pattern.

**Parallel Subagents** is the term Anthropic's own multi-agent research system
uses for a large-scale instance of Sectioning, where a lead agent "spins up
3-5 subagents in parallel" and each subagent "uses 3+ tools in parallel"
(Anthropic, "How we built our multi-agent research system,"
anthropic.com/engineering/multi-agent-research-system, verified 2026-08-02).
This is Parallelization one level up, the branches are not LLM calls, they are
entire agent loops running concurrently, each with its own tool budget and its
own sub-conversation, and the aggregation step is a synthesis pass rather than
a simple merge function.

**Self-Consistency**, described in Wang et al., "Self-Consistency Improves
Chain of Thought Reasoning in Language Models," ICLR 2023
(arxiv.org/abs/2203.11171, verified 2026-08-02), is the reasoning-research
name for Voting applied specifically to chain-of-thought sampling, where
multiple independent reasoning paths are sampled at nonzero temperature and
the final answer is the most common one. It predates the Anthropic essay by
roughly two years and is treated here as a specialization of Voting, covered
in depth in its own entry, `self-consistency`, cross-referenced below. Where
this entry stops is the boundary at which the vote itself becomes the
research contribution rather than an engineering choice, which is why
Self-Consistency earns a separate entry while Voting stays a named variant of
Parallelization.

## 2. Problem and context

An agentic pipeline built as a single sequential chain of LLM calls has one
throughput limit, the wall-clock latency of the slowest single call
multiplied by the number of calls, and one quality limit, whatever a single
sample from the model produces on a single attempt. Both limits are
avoidable in the specific case where the work either splits cleanly into
independent pieces, or benefits from being attempted more than once.

The situation that creates the need for Sectioning looks like this in a real
system. A pipeline needs to answer several questions about the same input, is
this email spam, what is its sentiment, does it contain PII, and each question
is answered by its own prompt because a single combined prompt performs worse
on each sub-question than a specialized prompt does (this is the exact
degradation Anthropic's content-moderation example names, verified above). Run
sequentially, three prompts against the same 2,000-token email at, say, 800ms
median latency each, costs 2.4 seconds of wall clock for work that has zero
data dependency between the three questions. There is nothing the sentiment
classifier needs from the PII classifier's output. Running them concurrently
collapses the 2.4 seconds to roughly the slowest single call, because the
three requests share no state and can be dispatched at the same instant.

The situation that creates the need for Voting is different in shape even
though it produces the same fan-out topology. A single LLM call for a
judgment task, does this code have a SQL injection vulnerability, is not
perfectly reliable on any one sample, because the model's output for a given
prompt is a draw from a probability distribution over completions, not a
deterministic function of the input. One sample can miss a vulnerability that
a second sample, run at the same temperature against the same prompt, catches.
Voting treats the model as a noisy classifier and asks the noisy classifier the
same question multiple times, then reduces the sample of answers to a single
decision by majority vote, unanimous agreement, or a tunable threshold. The
context that makes Voting worth its extra cost is a task where a wrong answer
is expensive and the marginal cost of an extra model call is cheap relative to
that risk, security review, medical-adjacent triage, high-value content
moderation, exactly the domains the Anthropic essay names.

Both situations share the same structural precondition. The branches, whether
distinct subtasks under Sectioning or repeated identical tasks under Voting,
must not need to see each other's output before they can start. The moment
branch B needs the result of branch A to formulate its own prompt, the shape
is no longer Parallelization, it is Prompt Chaining (see `prompt-chaining`),
and forcing it into a parallel fan-out either produces wrong output because a
branch ran on stale or missing context, or forces an artificial second round
that erases the latency win the pattern exists to deliver.

## 3. Forces

**Latency versus cost.** This is the main trade the pattern makes, and it
makes it in one direction only. N branches running concurrently against the
same or different endpoints reduce total wall-clock time toward the
latency of the single slowest branch, but they multiply token spend and
concurrent-request count by roughly N. A system with a tight cost budget and a
loose latency budget should prefer sequential Prompt Chaining or a single
larger call over Parallelization, because the pattern's entire reason to exist
is spending more to get results faster or more reliably, never the reverse.

**Quality via ensemble versus quality via a single stronger call.** Voting buys
reliability by sampling the same question multiple times and reducing the
variance of the answer through aggregation, the same statistical logic behind
ensemble methods in classical machine learning. The competing force is that a
single call to a stronger, more expensive model, or a single call with a
better engineered prompt, can sometimes close the same reliability gap for
less total cost than three calls to a weaker model. The pattern favors ensemble
diversity over that alternative. It sacrifices the possibility that a single better call
would have been the cheaper fix.

**Independence versus completeness.** Sectioning trades completeness of shared
context for the ability to run concurrently. Each branch sees only the slice of
input relevant to its subtask, not the full context every other branch has, so
a branch can miss a signal that would have been obvious with the full picture
in view. A content-moderation branch that only sees the message text, not the
sender's history, misses a pattern a single combined reviewer with both signals
would have caught. This is a real, not merely theoretical, quality cost that
the pattern accepts in exchange for the speedup, and it is the reason
Sectioning is applied to genuinely separable sub-questions, never to a task
whose parts interact.

**Coordination cost versus dispatcher simplicity.** Aggregating N branch
outputs into one result is itself a piece of logic, and its complexity is
proportional to how heterogeneous the branch outputs are. A simple majority
vote over identical-shape yes or no answers is nearly free to write. A
synthesis pass that must reconcile five different subagents' free-text
research findings into one coherent report, as in Anthropic's research system
(verified above), is itself an LLM call with its own prompt-engineering
surface, its own possibility of dropping a branch's finding, and its own
latency and cost. The pattern favors simple, uniformly shaped branch
outputs, and it punishes systems that fan out into heterogeneous free text and
hope the aggregation step will sort it out.

**Operability under partial failure.** A sequential chain fails at one known
point. A parallel fan-out of N branches can fail in any of N places
independently, and a system that treats "all branches must succeed" as the only
acceptable outcome inherits the reliability of the weakest branch raised to the
Nth power of exposure, not improved by it. The pattern favors an aggregation
step that has an explicit policy for a partial failure, proceed with a
majority of successful votes, fall back to a default on total branch failure,
degrade gracefully, rather than one that assumes every branch always returns.

**Cognitive load on the operator.** A sequential pipeline is easy to reason
about from a log, request one, response one, request two, response two. A
fan-out of five concurrent branches interleaves in a trace, and a debugging
session has to reconstruct which branch produced which output and how the
aggregator combined them. The pattern trades this legibility for throughput,
and it is the reason observability signals, dimension 16 below, matter more
here than in a sequential chain.

## 4. Applicability and non-applicability

Reach for Parallelization when the following hold.

- The task decomposes into subtasks that are genuinely independent of one
  another's output, the Sectioning case, and each subtask benefits from its
  own focused prompt rather than a single combined one.
- A single LLM call's answer to a judgment question is unreliable enough that
  running it more than once and reconciling the answers measurably raises
  accuracy, the Voting case, and the cost of an extra call is smaller than the
  cost of a wrong single-call answer.
- Wall-clock latency is the binding constraint and the work has no sequential
  data dependency between the pieces that would be run in parallel.
- The number of branches is known or boundable ahead of time, or can be
  computed cheaply before dispatch (a fixed set of checks, a bounded fan-out
  over a list whose length is known), so the dispatcher does not itself need an
  LLM call to decide how many branches to create.
- The aggregation function is simple in shape, a merge of disjoint fields
  for Sectioning, a vote or threshold for Voting, so that the aggregation step
  does not become a bottleneck or a new source of unreliability.

Do NOT reach for Parallelization in these cases, and the reason matters more
than the rule.

- A later branch needs the output of an earlier one to formulate its own
  prompt or decide whether to run at all. That data dependency makes this
  Prompt Chaining or Plan-and-Execute, not Parallelization, and forcing it into
  a fan-out either produces wrong answers from branches missing context they
  needed, or requires a second sequential round that erases the latency win.
- The task requires choosing which single path to take based on the nature of
  the input, rather than running multiple paths and combining them. That is
  Routing (see `routing`), a genuinely different control-flow shape, one
  branch selected, not several branches run and merged.
- Cost is the binding constraint and latency is not, and a single, better
  prompted, or higher-capability call can plausibly close the reliability gap
  Voting exists to close. Spending three times the tokens on redundant calls
  is not automatically cheaper than spending 1.5 times the tokens on a
  stronger model or a more carefully engineered prompt against the same base
  model.
- The branches share mutable state or write to the same resource, a shared
  file, a single customer record, a rate-limited external API with a strict
  per-second cap that N concurrent branches would collectively exceed. Shared
  mutable state under concurrent write reintroduces the exact race-condition
  and lost-update hazards that any concurrent system carries, and an LLM
  branch is no more safe from them than a thread is.
- The aggregation logic itself would need to be more sophisticated than the
  original single-call task it replaced, at which point the pattern has traded
  one hard problem, get a reliable answer from one call, for two hard
  problems, get reliable answers from N calls and then reliably combine them.
- Determinism and exact reproducibility of the full trace matter more than
  speed, for example a regulated audit trail that must show one deterministic
  linear sequence of steps. Concurrent dispatch introduces nondeterministic
  interleaving in logs and, if any branch's prompt depends on wall-clock timing
  or a shared counter, nondeterministic output as well.

## 5. Structure

**Dispatcher (orchestrator, splitter, fan-out node).** The component that
receives the original task and decides how to split it. For Sectioning, the
dispatcher's job is decomposition, it maps the single input to a fixed or
computed set of distinct subtask prompts, each targeting a different question
or slice of the input. For Voting, the dispatcher's job is replication, it
takes the single task and issues it N times, usually identically, sometimes
with N small prompt perturbations designed to diversify the sample. The
dispatcher owns the fan-out count, N, and it owns the decision of whether N is
fixed at design time or computed per request from the size of the input, for
example one branch per item in a list of unknown length.

**Branch (worker, section, vote member).** An independent unit of execution,
almost always a single LLM call in the simplest instances of this pattern and,
in Anthropic's own multi-agent research system, an entire tool-using subagent
running its own inner loop (verified above). Every branch receives its own
slice of context, produces its own output, and has no visibility into any
sibling branch's execution or output while it runs. This last property,
statelessness with respect to siblings, is what makes the branches safe to run
concurrently, there is no shared mutable state between them for a race
condition to corrupt.

**Aggregator (collector, reducer, join point, synthesis step).** The component
that waits for the branches to complete, or for a bounded subset of them under
a partial-failure policy, and combines their outputs into the single result the
caller of the whole pattern expects. Under Sectioning the aggregator is
usually a structural merge, take field A from branch one, field B from
branch two, assemble the combined record. Under Voting the aggregator is a
statistical reduction, majority rule, unanimous agreement requirement, or a
weighted or thresholded vote count. In large multi-agent instances the
aggregator can itself be an LLM call whose job is synthesis, writing a single
coherent narrative from N independent research findings, as Anthropic's lead
agent does after its subagents return (verified above, "spawns subagents to
explore different aspects simultaneously" then synthesizes the findings).

**Concurrency substrate.** The runtime mechanism actually dispatching the N
branches at the same time rather than one after another. This is `asyncio.
gather` or a `ThreadPoolExecutor` in Python, `Promise.all` in JavaScript and
TypeScript, a `sync.WaitGroup` with goroutines in Go, `withTaskGroup` in Swift
structured concurrency, or a platform-level primitive like the AWS Step
Functions `Parallel` state's `Branches` array, which the Amazon States
Language documentation states causes the service to execute each branch, in
its own words, "as concurrently as possible, and wait until all branches
terminate... before processing the Parallel state's Next field" (AWS,
"Parallel state," verified 2026-08-02, quoted in full above). This substrate
is not a detail, it is a structural participant, because its failure
semantics, does one branch's exception cancel the others, does the substrate
impose a global timeout, directly determine the pattern's operability under
partial failure, dimension 3 above.

## 6. ASCII structure diagram

```
                         Sectioning
                 (different questions, same input)

        +------------------+
        |   Dispatcher     |
        |  (decomposer)    |
        +--------+---------+
                 |
     splits into three independent slices
                 |
        +--------+--------+--------+
        |                 |        |
        v                 v        v
  +-----------+     +-----------+  +-----------+
  | Branch A  |     | Branch B  |  | Branch C  |
  | spam?     |     | sentiment |  | PII?      |
  +-----+-----+     +-----+-----+  +-----+-----+
        |                 |              |
        +--------+--------+--------------+
                 |
                 v
        +------------------+
        |    Aggregator    |
        |  (field merge)   |
        +--------+---------+
                 |
                 v
            single result
```

```
                          Voting
                (same question, repeated)

        +------------------+
        |   Dispatcher     |
        |  (replicator)    |
        +--------+---------+
                 |
    issues the SAME prompt N times, temp > 0
                 |
        +--------+--------+--------+
        |                 |        |
        v                 v        v
  +-----------+     +-----------+  +-----------+
  |  Vote 1   |     |  Vote 2   |  |  Vote 3   |
  | vuln=yes  |     | vuln=no   |  | vuln=yes  |
  +-----+-----+     +-----+-----+  +-----+-----+
        |                 |              |
        +--------+--------+--------------+
                 |
                 v
        +------------------+
        |    Aggregator    |
        | (majority / vote |
        |    threshold)    |
        +--------+---------+
                 |
                 v
        vuln=yes  (2 of 3)
```

## 7. Dynamics

```
Dispatcher                Branch A    Branch B    Branch C    Aggregator
    |                         |           |           |            |
    | receive task            |           |           |            |
    |------------------------>|           |           |            |
    |   dispatch A            |           |           |            |
    |------------------------>|           |           |            |
    |   dispatch B            |------------------------------------>|(no)
    |------------------------------------->|           |            |
    |   dispatch C                                                  |
    |--------------------------------------------------->|          |
    |   (returns immediately, does not block on any branch)         |
    |                         |           |           |            |
    |                         | LLM call  | LLM call  | LLM call   |
    |                         | (~800ms)  | (~650ms)  | (~900ms)   |
    |                         |           |           |            |
    |                         |<--result--|           |            |
    |                         |           |<--result--|            |
    |                         |           |           |<--result---|
    |                         |           |           |            |
    |   all branches settle by t = max(800, 650, 900) = 900ms       |
    |                         |           |           |            |
    |----------------- results forwarded on completion ------------>|
    |                                                                |
    |                                             +------------------+
    |                                             | aggregate,       |
    |                                             |  merge or vote    |
    |                                             +------------------+
    |                                                                |
    |<---------------------- final result --------------------------|
    |                                                                v
    caller receives one combined answer at t ~= 900ms,
    not t ~= 800 + 650 + 900 = 2350ms as a sequential chain would take
```

The key timing property visible in the diagram is that total latency
converges toward `max(branch latencies)` under full concurrency rather than
`sum(branch latencies)` under sequential execution, provided the underlying
transport, HTTP connections to the model provider, an internal message bus,
actually supports concurrent in-flight requests and is not itself a serialized
bottleneck, for example a single-connection HTTP client reused across calls
without connection pooling, which would silently collapse the pattern back to
sequential timing while still appearing to be "parallel" in the code's control
flow.

## 8. Implementation variants

**Fixed-N fan-out, structural concurrency.** The dispatcher knows the exact
branch count at compile time or at the start of the request, for example
always exactly three sectioning branches, or always exactly five vote
members. This is implemented directly with structured concurrency primitives,
`asyncio.gather(*coros)` in Python, `Promise.all([...])` in TypeScript, a
`WaitGroup` of a known size in Go, or a `TaskGroup` in Swift, none of which
need a dynamic loop over an unknown-length collection. This is the simplest
and most common variant and the one used for the great majority of Sectioning
and Voting instances in production systems today.

**Dynamic map-reduce fan-out.** The branch count is not known until the
dispatcher inspects the input, for example one branch per item in a list
returned by an earlier step whose length varies per request. The concurrency
substrate must support spawning a variable number of concurrent tasks from a
runtime-determined list, which most languages' native primitives handle
directly, `asyncio.gather(*[handle(x) for x in items])`, or which graph-based
orchestration frameworks expose as a first-class primitive for exactly this
case, dynamically creating N parallel edges out of a single node based on the
runtime size of a list. This variant carries the added operational risk that
an unexpectedly large input silently multiplies concurrent load and cost, so
production implementations bound N with an explicit cap and a policy for what
happens when the natural fan-out would exceed it, batching, truncation, or an
explicit rejection.

**Weighted or thresholded voting.** Rather than simple majority, the
aggregator applies a domain-specific decision rule, require unanimous
agreement before flagging content, require only two of five votes for a
lower-severity classification but require four of five for a
higher-severity one, or weight each vote by a confidence score the branch
itself returns rather than treating every vote as equal. This variant keeps
the fan-out structure identical to plain Voting and changes only the
aggregation function, which is the correct place to localize this
complexity, the branches themselves stay simple and uninstructed about the
threshold policy.

**Multi-agent subagent fan-out with LLM-driven synthesis.** The heaviest
variant, where each branch is not a single LLM call but a complete tool-using
agent loop given its own objective, its own tool budget, and its own
sub-conversation, exactly as described for Anthropic's lead agent, which
"spawns subagents to explore different aspects simultaneously," each
receiving "an objective, an output format, guidance on the tools and sources
to use, and clear task boundaries" (verified above). The aggregator in this
variant is itself an LLM call whose job is synthesis rather than a structural
merge or a vote count, because the branch outputs are free-text findings that
must be woven into one coherent answer rather than combined by a mechanical
rule. This variant pays the highest coordination cost named in dimension 3 and
is reserved for tasks, open research, broad codebase audits, where the value
of true multi-perspective exploration clearly outweighs that cost.

**Provider-native parallel tool calling.** A narrower but extremely common
instance of Sectioning that does not require the calling application to build
any dispatcher or aggregator at all, because the model itself performs both
roles inside a single turn. When an LLM call is given multiple tool
definitions and the provider supports it, the model can emit several tool
calls in one response, which the calling application then executes
concurrently and feeds back as multiple tool results in the next turn. OpenAI
documents this directly, "the model may choose to call multiple functions in
a single turn," with an explicit `parallel_tool_calls` flag to disable it
(OpenAI, "Function calling," developers.openai.com/api/docs/guides/
function-calling, verified 2026-08-02). This is Sectioning collapsed into the
model's own decision boundary, the dispatcher role is the model choosing
which tools to call together, and the calling application supplies only the
concurrency substrate that actually executes them.

## 9. Known production uses

Anthropic's own multi-agent research feature in Claude, publicly described in
"How we built our multi-agent research system," runs a lead agent that spins
up three to five subagents concurrently for complex research queries, each
exploring a different facet of the question with its own tool budget, and the
company reports this cut research time by up to 90% for complex queries and
that the multi-agent configuration outperformed a single Opus 4 agent by
90.2% on Anthropic's internal research evaluation (Anthropic,
"How we built our multi-agent research system," anthropic.com/engineering/
multi-agent-research-system, verified 2026-08-02).

AWS Step Functions ships Parallelization as a first-class, named state type in
the Amazon States Language, the `Parallel` state, whose `Branches` field
accepts an array of independent sub-state-machines that the service executes,
in the documentation's own words, "as concurrently as possible," waiting for
every branch to terminate before advancing, with an explicit error-handling
contract for what happens when one branch fails while its siblings are still
running (AWS, "Parallel state," Amazon States Language reference,
docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-parallel-
state.html, verified 2026-08-02). This is not an LLM-specific feature, it
predates the current wave of agentic tooling, and its presence as a
foundational primitive of a widely used serverless orchestration service is
the reason Sectioning and Voting graph naturally onto workflow engines built
for entirely non-AI distributed systems, the topology was already there
waiting for LLM calls to be dropped into it as the branch bodies.

OpenAI's Chat Completions and Responses APIs support parallel tool calling as
a documented, named capability, where a single model turn can emit multiple
independent tool calls that the calling application is expected to execute
concurrently, controllable via the `parallel_tool_calls` parameter, and OpenAI
documents platform-specific behavior differences, for example that on models
beginning with GPT-5, "functions can be called in parallel when built-in
tools are also available" but "built-in tools cannot be included in a
parallel function-call batch" (OpenAI, "Function calling,"
developers.openai.com/api/docs/guides/function-calling, verified
2026-08-02). This is the provider-native parallel tool calling variant from
dimension 8, in wide production use across every application built on the
OpenAI tool-calling interface, from customer-support bots issuing a lookup
and a calendar check in the same turn to coding agents that read several
files at once.

## 10. Consequences

**Positive.**

- Wall-clock latency for genuinely independent subtasks converges toward the
  slowest single branch rather than the sum of every branch, which is the
  pattern's headline benefit and the reason Anthropic reports a 90% research
  time reduction for its multi-agent configuration (verified above).
- Voting measurably raises accuracy on judgment tasks where a single sample is
  an unreliable draw from the model's output distribution, by converting a
  single noisy classification into an ensemble decision, the same statistical
  logic that underlies bagging and majority-vote ensembles in classical
  machine learning.
- Sectioning lets each branch use a narrower, more specialized prompt focused
  on exactly one sub-question, which Anthropic's own content-moderation
  example states performs better than one combined prompt handling both
  concerns at once (verified above), because the model is not being asked to
  context-switch between unrelated framings within a single completion.
- The pattern composes cleanly with existing distributed-systems tooling.
  Concurrency substrates, orchestration engines, and observability stacks built
  for non-AI parallel workloads apply directly, the branches happen to be LLM
  calls rather than database queries or microservice calls, but the fan-out
  and fan-in mechanics are unchanged.

**Negative.**

- Token cost and concurrent API load scale roughly linearly with the branch
  count N, so Parallelization is strictly more expensive per request than the
  sequential or single-call alternative it replaces, and that cost must be
  justified by the latency or reliability gain, never assumed to be free.
- Sectioning branches that lack shared context can each miss a signal that
  would have been visible with the full picture in view, a real quality cost
  that is easy to overlook because each individual branch's output looks
  correct in isolation, the failure only shows up as a gap in the aggregated
  result.
- The aggregation step becomes a new, substantial piece of logic whose own
  correctness the pattern depends on, and a bug or bias in a merge function or
  a vote-counting rule silently corrupts every request that passes through the
  pattern, in a way that is harder to spot than a bug in a single sequential
  call because the individual branch outputs, examined one at a time, can each
  look correct.
- Debugging and tracing a fan-out is harder by its nature than debugging a
  sequential chain, because the log interleaving of N concurrent branches does
  not read top to bottom the way a sequential trace does, and correlating
  which branch produced which output, and how the aggregator combined them,
  requires deliberate trace-ID propagation rather than falling out of the
  natural order of a linear log.
- Under a naive "wait for all branches, no timeout, no partial-failure policy"
  implementation, the pattern's overall reliability is the product of every
  branch's individual reliability, which is lower than any single branch's
  reliability alone, the opposite of the intended effect, and is a trap teams
  fall into when they treat Parallelization as a pure speed optimization
  without also designing for partial failure.

## 11. Failure modes and misuse

**Symptom.** The parallel version of a pipeline is not measurably faster than
the sequential version it replaced, despite branches running concurrently in
the code.
**Cause.** The concurrency substrate is not actually concurrent at the
transport layer, a shared single connection to the model provider, a
connection pool sized to one, or a global rate limiter that serializes
outbound requests regardless of how the calling code issues them, so `gather`
or `Promise.all` correctly schedules the calls concurrently in application
code while the network layer beneath still processes them one at a time.
**Fix.** Verify the HTTP client used for the branch calls is configured with a
connection pool sized to at least N, check for any shared semaphore or rate
limiter wrapping the branch calls, and confirm via request-level timing traces
that the branches' network round trips actually overlap in wall-clock time
rather than merely being scheduled concurrently in the event loop.

**Symptom.** Sectioning branches individually look correct when inspected one
at a time, but the aggregated result is missing or contradicts information a
human reviewer would have caught immediately.
**Cause.** A signal relevant to more than one branch's judgment was present in
the shared input but was only forwarded to one branch, or was dropped
entirely by the dispatcher's decomposition step, so no single branch had the
full context needed to catch the issue, and the aggregator has no mechanism to
detect a gap between branches because each branch reported successfully within
its own narrow scope.
**Fix.** Audit the dispatcher's decomposition logic for which fields of the
original input reach which branch, and deliberately duplicate any
cross-cutting signal, sender reputation, account history, prior flags, into
every branch that could plausibly need it rather than assuming a single
branch owns it, accepting the small extra token cost of duplicated context
over the correctness risk of an under-informed branch.

**Symptom.** A Voting-based decision flips between runs on effectively
identical input, producing inconsistent results for what should be a stable
classification.
**Cause.** N is too small relative to the model's actual variance on the task,
so the vote outcome is driven mainly by sampling noise rather than by a
genuine convergent signal, three votes at temperature 1.0 on a genuinely
ambiguous case will not reliably produce the same 2-1 or 3-0 split across
repeated invocations.
**Fix.** Either lower the sampling temperature for the vote members to reduce
per-branch variance, increase N until the vote outcome stabilizes across
repeated test runs on the same input, or, if the underlying task is genuinely
ambiguous rather than the model being unreliable, surface the ambiguity itself
as part of the result rather than forcing a false binary decision out of a
close vote.

**Symptom.** A single slow or hung branch blocks the entire pattern from
returning, and the whole request times out even though every other branch
finished quickly.
**Cause.** The aggregator, or the concurrency substrate underneath it, waits
with no condition for all N branches to settle, no per-branch timeout, and
no partial-failure policy, so the pattern inherits the worst-case latency of
its single slowest or hung branch rather than a bounded latency budget.
**Fix.** Apply a per-branch timeout independent of the others, and design the
aggregator with an explicit policy for a branch that does not return in time,
proceed with the votes or sections that did complete, mark the missing branch
as abstained rather than as a hard failure of the whole request, and log the
timeout as an observability signal (dimension 16) rather than letting it
silently degrade to the worst case every time it occurs.

**Symptom.** Cost per request has grown far beyond what the latency or
accuracy gain justifies, and the fan-out is spending far more than a single
well-engineered call would have cost.
**Cause.** Parallelization was applied reflexively to a task that did not
actually need decomposition or redundancy, most commonly a task that was
mistaken for Sectioning when it was actually a single coherent question being
artificially split, or a Voting configuration with N set far higher than the
accuracy curve justifies, adding a sixth or seventh vote member when the
marginal accuracy gain from vote four to vote seven is near zero.
**Fix.** Measure the accuracy-versus-N curve empirically on a held-out sample
before locking in a vote count, most Voting configurations show diminishing
returns past three to five members, and for Sectioning, verify the
sub-questions are truly independent rather than artificially separated pieces
of what was really one coherent judgment that a single well-prompted call
could have answered directly.

## 12. Trade-off matrix

| Force | Parallelization (Sectioning / Voting) | Prompt Chaining | Routing | Orchestrator-Worker |
|---|---|---|---|---|
| Latency for independent subtasks | Converges to slowest branch | Sum of every step's latency | Latency of the one chosen path only | Similar to Sectioning, plus a synthesis pass |
| Cost relative to a single call | Roughly N times a single call | Roughly (number of steps) times a single call | Roughly one call, whichever path is chosen | Roughly N times a single call, plus synthesis |
| Handles data dependency between subtasks | No, branches must be independent | Yes, this is its whole purpose | N/A, only one path runs | Worker branches must still be independent |
| Improves reliability of a single judgment | Yes, via Voting's ensemble effect | No inherent reliability boost | No inherent reliability boost | Not directly, workers do distinct subtasks |
| Aggregation complexity | Merge (Sectioning) or vote (Voting), can be simple | None needed, output flows step to step | None needed, one path's output is the answer | Often an LLM synthesis call, can be complex |
| Debuggability from a linear log | Harder, interleaved concurrent traces | Easy, reads top to bottom | Easy, one path is active | Hardest, concurrent subagents each with sub-loops |
| Best suited task shape | Independent sub-questions or repeatable judgments | Sequential steps each depending on the last | Distinct input categories needing distinct handling | Open-ended exploration needing diverse specialist angles |

## 13. Related and incompatible patterns

**Orchestrator-Worker** (`orchestrator-worker`) is the closest relative and the
two are frequently confused. Parallelization's branches are usually
predetermined at dispatch time, a fixed or input-derived set of sub-questions
or vote replicas known before any branch starts. Orchestrator-Worker's central
LLM dynamically decides what subtasks exist and assigns them to workers as
part of its own reasoning, the decomposition itself is a model decision made
at runtime rather than a structural property the dispatcher already knows.
Anthropic's own multi-agent research system sits at the boundary of both, the
lead agent dynamically decides how many subagents to spawn and what each
should investigate, an Orchestrator-Worker decision, but then dispatches them
to run concurrently, a Parallelization mechanic, which is why that system is
correctly described as composing both patterns rather than being a pure
instance of either.

**Prompt Chaining** (`prompt-chaining`) is the pattern Parallelization is not.
Where Parallelization requires branch independence, Prompt Chaining requires
sequential dependency, each step's prompt is built from the previous step's
output. The two compose at the pipeline level, a chain can contain a
parallelization stage as one of its steps, gather three independent facts
concurrently, then chain into a synthesis step that depends on all three, and
this composition is common and sound, the incompatibility is only between
treating a single stage as both patterns at once.

**Routing** (`routing`) shares the fan-out shape at the code level, a
dispatcher and multiple possible destinations, but differs in how many paths
actually run. Routing selects exactly one path to run based on a
classification of the input, the unchosen paths never execute. Parallelization
runs every branch. A system that appears to route but is actually running
every branch and discarding all but one output is a Parallelization
implementation being used, wastefully, to simulate Routing, and should be
refactored to classify first and dispatch to a single handler.

**Self-Consistency** (`self-consistency`) is the reasoning-research
specialization of Voting, sampling multiple independent chain-of-thought
reasoning paths for the same problem and taking the majority final answer,
formalized by Wang et al. (verified above). Every Self-Consistency instance is
a Voting instance of Parallelization, but not every Voting instance rises to
the level of a distinct research contribution, most production Voting
configurations are an engineering choice about how many times to sample a
judgment call, not a novel reasoning technique, which is why the two are kept
as related but separate entries.

**Plan-and-Execute** (`plan-execute`) can incorporate a Parallelization stage
inside its execute phase, once a plan identifies a set of independent steps,
those steps can be dispatched concurrently rather than one at a time, but the
planning phase itself, deciding what the independent steps are, is not part of
Parallelization, it belongs to Plan-and-Execute or to Orchestrator-Worker.

There is no pattern in this catalog that Parallelization is unable to compose
with. Its incompatibility with a given situation is contextual, not built into
the shape of the pattern, it is the wrong tool whenever the
concrete task at hand has a sequential data dependency between the would-be
branches, which is a property of the task, not a conflict with another named
pattern.

## 14. Refactoring path in and out

**Introducing Parallelization into an existing sequential pipeline.** Start by
identifying, among the sequential steps, which pairs or groups genuinely have
no data dependency on each other, trace each step's prompt construction and
confirm it does not reference any prior step's output before deciding two
steps are independent, a step that merely happens not to use a prior output
today can still be silently dependent on execution order for a side effect,
logging, a shared counter, that concurrent execution would break. Once a
genuinely independent group is identified, replace the sequential calls to
that group with a single concurrent dispatch using the language's native
concurrency primitive, `asyncio.gather`, `Promise.all`, a bounded goroutine
group, and add an explicit aggregation function immediately after the
dispatch point that the rest of the pipeline consumes exactly as it consumed
the sequential steps' combined output before. Add a per-branch timeout and a
partial-failure policy at the same time the fan-out is introduced, not as a
follow-up, because the failure mode named in dimension 11, one hung branch
blocking everything, appears the first time any branch experiences real-world
latency variance, which is usually the first production traffic spike after
launch, not during development.

For introducing Voting specifically, start from a single existing judgment
call, measure its accuracy on a held-out labeled sample, then wrap it to run N
times at a nonzero temperature and add a majority-vote aggregator, and compare
accuracy on the same held-out sample at N equals three, five, and seven before
committing to a value, since dimension 11 names an over-provisioned N as a
real and common cost-inflation failure.

**Removing Parallelization when it stops earning its place.** The signal that
a Sectioning fan-out should be collapsed back into a single call is that the
branches have grown to require so much shared context, duplicated into every
branch to fix the missing-signal failure mode from dimension 11, that the
combined token cost of running N branches, each carrying nearly the full
shared context, now exceeds the cost of one well-prompted single call handling
every sub-question at once, at which point the pattern is paying for
concurrency it is no longer using to reduce actual work, only to reduce
latency, and if latency has also stopped being the binding constraint, the
fan-out should be flattened back into one call with a single, carefully
structured prompt covering every sub-question, verified against the same
held-out sample used to validate the original split.

The signal that a Voting fan-out should be removed is a measured accuracy plot
showing the marginal gain from N to N plus one has flattened to
indistinguishable from noise on the held-out sample, at which point the extra
vote members are pure cost with no offsetting benefit, and N should be reduced
to the smallest value where the accuracy curve was still measurably rising,
re-verified periodically as the underlying model is upgraded, since a stronger
model can shift the point of diminishing returns to a lower N than an older,
noisier model required.

## 15. Testing and verification

Test each branch's logic in complete isolation first, exactly as a unit test
for a single LLM call would be written, holding the branch's prompt template
and input construction fixed and asserting on its output shape independent of
any concurrency concern, since a bug in one branch's prompt is not a
concurrency bug and testing it inside a full concurrent fan-out only adds
noise to the failure signal.

Test the dispatcher's decomposition logic separately from execution, given a
fixed input, assert on the exact set of branch prompts or branch inputs it
produces, without actually invoking any model, this catches the missing-signal
failure mode from dimension 11 at the cheapest possible point, a pure
input-to-input assertion with no network call and no nondeterminism.

Test the aggregator with hand-constructed branch outputs rather than real
model calls, feed it a fixed set of Sectioning outputs and assert on the
merged result, or feed it a fixed distribution of Voting outcomes, two yes one
no, and assert the majority rule produces the expected decision, including the
edge cases of a perfect tie under an even N and of a partial-failure scenario
where fewer than N branches returned. This isolates aggregation-logic bugs
from LLM output variance entirely, which matters because aggregation bugs are
deterministic code bugs that should be caught by deterministic tests, not
buried inside flaky model-dependent integration tests.

Test the concurrency substrate's timing behavior with a fake branch function
that sleeps for a controlled duration rather than a real model call, assert
that the total wall-clock time of the fan-out is close to the maximum sleep
duration among the fake branches rather than their sum, which is a fast,
deterministic, network-free test that directly catches the transport-layer
serialization failure mode from dimension 11, and it should be a permanent
regression test, not a one-time manual check, since a connection-pool
misconfiguration introduced months later by an unrelated change is exactly the
kind of regression this test exists to catch.

Test the partial-failure and timeout policy explicitly, using a fake branch
that raises an exception or never resolves, and assert the aggregator still
returns a usable result under the documented degradation policy rather than
propagating an unhandled exception or hanging indefinitely, this is the single
most valuable test in the suite because it is the failure mode most likely to
first surface in production traffic rather than in development.

For Voting configurations specifically, run a batch evaluation against a
held-out labeled dataset at each candidate N and record accuracy, this is not
a unit test in the conventional sense, it is an empirical measurement that
should be re-run whenever the underlying model changes, and its output, the
accuracy-versus-N curve, is the artifact that justifies the chosen N in
dimension 14's tuning process rather than a one-time guess.

## 16. Observability signals

Log a single trace or correlation ID at the dispatcher and propagate it into
every branch's own logging context, so a single request's fan-out can be
reconstructed from an interleaved log by filtering on that one ID, this is the
minimum viable fix for the debuggability cost named in dimension 10, without
it a concurrent fan-out's log output is effectively unreadable once request
volume is more than a handful of requests per minute.

Record, per branch, its own latency, token count, and success or failure
status as a structured log line, distinct from the aggregator's own summary
line, so a slow-branch or a systematically-failing-branch pattern is visible
by branch identity rather than only as an aggregate latency number that
obscures which specific branch is the outlier.

For Sectioning, monitor the rate at which the aggregator's merge step
encounters a conflict, two branches disagreeing about a field that should be
consistent between them, or a gap, an expected field absent from every branch's
output, as a first-class metric, a rising conflict or gap rate is the earliest
observable signal of the missing-signal failure mode from dimension 11, well
before it surfaces as a user-visible wrong answer.

For Voting, monitor the vote-split distribution itself, not only the final
decision, a system that is consistently landing exactly at the majority
threshold, two of three, three of five, rather than showing strong
unanimous-or-near-unanimous agreement, is telling you either that N is too
small for the task's actual ambiguity or that the underlying judgment task is
genuinely ambiguous and the binary decision the vote is forcing may not be the
right output shape for it.

Track total wall-clock time for the full pattern, dispatch through
aggregation, as a dedicated metric distinct from any individual branch's
latency, and alert when it drifts materially above the theoretical
`max(branch latencies)` minimum, since that drift is the direct observable
signature of the transport-layer serialization failure mode from dimension
11, and it is far cheaper to catch via a latency-shape alert than to
rediscover by manually inspecting traces after a user complaint.

Track cost per completed request as a first-class metric alongside latency and
accuracy, since Parallelization's entire trade is spending more for speed or
reliability, and a cost regression, N silently growing, a branch retrying more
than expected, an aggregator making an unplanned extra synthesis call, is
exactly the kind of change that a latency or correctness metric alone will not
surface.

## 17. Security and privacy implications

Each branch under Sectioning usually receives only a slice of the original
input, and where that slice includes personally identifiable information or
other sensitive data, the pattern multiplies the number of distinct places
that data is transmitted to and processed by, from one call in a
non-parallelized design to N calls, which is a real increase in exposure
surface, more log lines, more provider-side request records, more places a
data-retention or data-residency policy must be verified to hold, and a
system handling sensitive data through Sectioning should audit each branch's
actual input for the minimum necessary slice of the sensitive data rather than
forwarding the full original payload to every branch by default.

Voting's replication of the identical prompt across N calls does not
meaningfully change the sensitivity profile of the data itself, since it is
the same data sent N times rather than a wider slice sent once, but it does
proportionally multiply the request volume against whatever data-processing
agreement or provider-side logging policy governs the underlying model calls,
which matters for compliance accounting even where it does not change the
substance of what is being sent.

Concurrent dispatch to an external tool or API inside a Sectioning or
provider-native parallel-tool-calling branch, dimension 8, can trigger a
burst against that external system's own rate limits at a moment the caller
did not anticipate, since N branches issuing tool calls at effectively the
same instant is a very different load profile from N sequential calls spaced
out by the model's own generation latency, and a system integrating
Parallelization with external tool calls should apply its own outbound rate
limiting independent of whatever limit the external system enforces, so a
burst is smoothed on the calling side rather than discovered as a 429 response
storm from the external service.

The aggregator, where it is itself an LLM synthesis call over N branches'
free-text outputs, inherits the general prompt-injection surface of any LLM
call that consumes untrusted or semi-trusted text, and where any branch's
output could itself contain adversarial content, a tool result scraped from
an external source, user-supplied text passed through a branch relatively
unfiltered, the synthesis step should apply the same input-sanitization and
prompt-injection defenses that any single LLM call consuming external content
would need, the fan-out does not reduce this risk and, by increasing the
number of distinct upstream sources feeding into one synthesis call, arguably
widens it.

## 18. References

- Anthropic engineering team, "Building Effective Agents," Anthropic, December
  2024, https://www.anthropic.com/engineering/building-effective-agents,
  verified 2026-08-02. Source for the Parallelization pattern's naming,
  Sectioning and Voting as its two named variants, and the content-moderation
  and code-review examples cited in dimensions 1, 2, and 10.
- Anthropic engineering team, "How we built our multi-agent research system,"
  Anthropic, https://www.anthropic.com/engineering/multi-agent-research-system,
  verified 2026-08-02. Source for the parallel-subagent production system,
  the 3-5 subagent fan-out, the 90% research-time reduction, and the 90.2%
  accuracy improvement figures cited in dimensions 1, 9, and 10.
- Amazon Web Services, "Parallel state," AWS Step Functions Developer Guide,
  Amazon States Language reference,
  https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-parallel-state.html,
  verified 2026-08-02. Source for the
  Parallel state's `Branches` field, its concurrent execution semantics, and
  its branch-level error-handling contract, cited in dimensions 1, 5, and 9.
- OpenAI, "Function calling," OpenAI Platform documentation,
  https://developers.openai.com/api/docs/guides/function-calling, verified
  2026-08-02. Source for parallel tool calling as a provider-native
  Sectioning variant, the `parallel_tool_calls` parameter, and the GPT-5
  built-in-tools restriction, cited in dimensions 8 and 9.
- Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc Le, Ed Chi, Sharan Narang,
  Aakanksha Chowdhery, Denny Zhou, "Self-Consistency Improves Chain of
  Thought Reasoning in Language Models," Proceedings of the International
  Conference on Learning Representations (ICLR) 2023,
  https://arxiv.org/abs/2203.11171, verified 2026-08-02. Source for
  Self-Consistency as the reasoning-research specialization of Voting, cited
  in dimensions 1 and 13.

## Code examples

Three languages, each showing a different variant from dimension 8. Python
shows the Fixed-N Sectioning fan-out with a per-branch timeout and a
structural aggregator. TypeScript shows Voting with a majority-rule
aggregator and a per-branch race against a timeout. Go shows the Dynamic
map-reduce fan-out, one goroutine per runtime-length input item, collected
through a buffered channel. Java, Rust, and Swift are omitted here because
none of the three add a genuinely different concurrency idiom for this
pattern beyond what `asyncio.gather`, `Promise.all`, and a `WaitGroup`
already demonstrate, they would repeat the same fan-out shape in a fourth
syntax rather than showing a new implementation variant.

### Python (Sectioning, fixed N, per-branch timeout)

```python
"""Sectioning fan-out. Three independent LLM-shaped branches run concurrently,
each answering a different question about the same input, then a structural
aggregator merges their outputs into one record. A per-branch timeout keeps a
single hung branch from blocking the whole request, and the aggregator marks
a timed-out branch as abstained rather than failing the entire call."""

import asyncio
from dataclasses import dataclass


@dataclass
class BranchResult:
    name: str
    ok: bool
    value: str


async def call_model(branch_name: str, prompt: str, latency_s: float) -> str:
    """Stands in for a real LLM call. A production branch would call the
    model provider's API here instead of sleeping."""
    await asyncio.sleep(latency_s)
    return f"{branch_name}:{prompt[:12]}"


async def run_branch(name: str, prompt: str, latency_s: float, timeout_s: float) -> BranchResult:
    try:
        value = await asyncio.wait_for(call_model(name, prompt, latency_s), timeout_s)
        return BranchResult(name=name, ok=True, value=value)
    except asyncio.TimeoutError:
        return BranchResult(name=name, ok=False, value="")


def aggregate(results: list[BranchResult]) -> dict[str, str]:
    """Structural merge for Sectioning. Missing or timed-out branches are
    recorded as abstained rather than crashing the whole aggregation."""
    merged: dict[str, str] = {}
    for r in results:
        merged[r.name] = r.value if r.ok else "abstained"
    return merged


async def sectioning(email_text: str) -> dict[str, str]:
    branches = [
        ("spam_check", email_text, 0.05, 1.0),
        ("sentiment", email_text, 0.03, 1.0),
        ("pii_check", email_text, 0.07, 1.0),
    ]
    results = await asyncio.gather(
        *[run_branch(name, prompt, lat, to) for name, prompt, lat, to in branches]
    )
    return aggregate(list(results))


if __name__ == "__main__":
    merged = asyncio.run(sectioning("hello there this is a test email body"))
    assert set(merged.keys()) == {"spam_check", "sentiment", "pii_check"}
    for name, value in merged.items():
        print(name, value)
```

Compiled with `python3 -m py_compile` and run directly, verified 2026-08-02.

### TypeScript (Voting, majority aggregator, per-branch race)

```typescript
// Voting fan-out. The same judgment prompt is issued N times, and the
// aggregator reduces the sample of answers to a single decision by simple
// majority, treating a rejected or timed-out promise as an abstention rather
// than letting one bad branch fail the whole vote.

type Vote = "yes" | "no";

interface VoteResult {
  index: number;
  vote: Vote | "abstain";
}

async function callModel(index: number, prompt: string): Promise<Vote> {
  // Stands in for a real LLM call at nonzero temperature. A production
  // branch would call the model provider's API here instead of computing
  // a fixed answer.
  await new Promise((resolve) => setTimeout(resolve, 5 + index));
  return index % 3 === 0 ? "no" : "yes";
}

async function runVoteMember(index: number, prompt: string, timeoutMs: number): Promise<VoteResult> {
  const timeout = new Promise<VoteResult>((resolve) =>
    setTimeout(() => resolve({ index, vote: "abstain" }), timeoutMs)
  );
  const call = callModel(index, prompt).then((vote): VoteResult => ({ index, vote }));
  return Promise.race([call, timeout]);
}

function majority(results: VoteResult[]): Vote | "tie" {
  const counts: Record<Vote, number> = { yes: 0, no: 0 };
  for (const r of results) {
    if (r.vote !== "abstain") counts[r.vote] += 1;
  }
  if (counts.yes === counts.no) return "tie";
  return counts.yes > counts.no ? "yes" : "no";
}

async function voting(prompt: string, n: number, timeoutMs: number): Promise<Vote | "tie"> {
  const branches = Array.from({ length: n }, (_, i) => runVoteMember(i, prompt, timeoutMs));
  const results = await Promise.all(branches);
  return majority(results);
}

async function main() {
  const decision = await voting("does this code have a SQL injection vulnerability", 5, 200);
  console.log("decision:", decision);
  if (decision !== "yes" && decision !== "no" && decision !== "tie") {
    throw new Error("unexpected decision shape");
  }
}

main();
```

Type-checked with `tsc --noEmit --target es2020 --lib es2020,dom`, verified
2026-08-02.

### Go (dynamic map-reduce fan-out)

```go
// Package main demonstrates a dynamic map-reduce fan-out. One branch is
// spawned per item in a runtime-length slice, each branch runs a bounded
// unit of work concurrently via a WaitGroup, and results are collected on a
// buffered channel so no branch blocks waiting for a slot to report into.
package main

import (
	"fmt"
	"sort"
	"sync"
	"time"
)

type branchResult struct {
	index int
	value string
	ok    bool
}

func runBranch(index int, item string, timeout time.Duration) branchResult {
	done := make(chan string, 1)
	go func() {
		time.Sleep(2 * time.Millisecond)
		done <- fmt.Sprintf("section-%d:%s", index, item)
	}()
	select {
	case v := <-done:
		return branchResult{index: index, value: v, ok: true}
	case <-time.After(timeout):
		return branchResult{index: index, ok: false}
	}
}

func sectioning(items []string, timeout time.Duration) []branchResult {
	var wg sync.WaitGroup
	out := make(chan branchResult, len(items))
	for i, item := range items {
		wg.Add(1)
		go func(i int, item string) {
			defer wg.Done()
			out <- runBranch(i, item, timeout)
		}(i, item)
	}
	go func() {
		wg.Wait()
		close(out)
	}()

	results := make([]branchResult, 0, len(items))
	for r := range out {
		results = append(results, r)
	}
	sort.Slice(results, func(a, b int) bool { return results[a].index < results[b].index })
	return results
}

func main() {
	items := []string{"spam?", "sentiment", "PII?"}
	results := sectioning(items, 50*time.Millisecond)
	if len(results) != len(items) {
		panic("expected one result per branch")
	}
	for _, r := range results {
		fmt.Println(r.index, r.value, r.ok)
	}
}
```

Compiled and run with `go build` and `go run`, verified 2026-08-02.
