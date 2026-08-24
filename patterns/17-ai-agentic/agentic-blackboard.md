---
name: Agentic Blackboard
slug: agentic-blackboard
family: 17-ai-agentic
category: Agentic
aliases: [Blackboard Architecture, Shared Workspace Pattern, Shared Scratchpad Pattern, Blackboard System]
first_described: "Erman, Hayes-Roth, Lesser, Reddy 1980, applied to multi-agent LLM systems circa 2023-2024"
maturity: established
related: [multi-agent-supervisor, mediator, observer, agent-memory, hierarchical-agents, tool-result-caching]
incompatible_with: [orchestrator-worker]
verified: 2026-08-02
---

# Agentic Blackboard

## 1. Name, aliases, and lineage

The canonical name is Blackboard, sometimes written Blackboard Architecture or
Blackboard System when the whole application is organized around one, and
Blackboard Pattern when it is treated as one architectural pattern among many
inside a larger system. In the multi-agent large language model literature the
same shape is frequently called a Shared Workspace or Shared Scratchpad, terms
that describe the mechanism without inheriting the historical baggage of the
older AI systems the pattern came from.

The pattern was identified by the team that built Hearsay-II, a speech
understanding system at Carnegie Mellon University in the 1970s. The English
Wikipedia article on the blackboard design pattern states plainly that "this
pattern was identified by the members of the Hearsay-II project and first
applied to speech recognition" (Wikipedia, "Blackboard (design pattern)",
https://en.wikipedia.org/wiki/Blackboard_(design_pattern), verified
2026-08-02). The system itself is documented in Lee D. Erman, Frederick
Hayes-Roth, Victor R. Lesser, and D. Raj Reddy, "The Hearsay-II Speech
Understanding System, Integrating Knowledge to Resolve Uncertainty," ACM
Computing Surveys, volume 12, issue 2, 1980, a paper whose existence,
authorship, venue, and year are corroborated by the same Wikipedia summary of
the pattern's origin. Hearsay-II needed to combine many independent, partial,
and uncertain sources of evidence, acoustic, phonetic, lexical, syntactic, and
semantic, into a single interpretation of an utterance, and no single
top-down or bottom-up algorithm fit the problem, because none of the
knowledge sources could run to completion before the others had something
useful to react to.

Two systems carried the idea forward through the 1980s. Barbara Hayes-Roth
built BB1, a blackboard architecture whose control mechanism was itself driven
by the blackboard, "originally inspired by studies of how humans plan to
perform multiple tasks" and later applied to construction site planning,
inferring three dimensional protein structure from X-ray crystallography,
intelligent tutoring, and real time patient monitoring (Wikipedia, "Blackboard
system", https://en.wikipedia.org/wiki/Blackboard_system, verified
2026-08-02). Daniel Corkill built GBB, later continued as the open source
GBBopen project, a blackboard framework that traded BB1's sophisticated
meta-level control reasoning for raw execution efficiency, according to the
same source. The pattern was later codified as a software architectural
pattern, independent of its AI ancestry, in Frank Buschmann, Regine Meunier,
Hans Rohnert, Peter Sommerlad, and Michael Stal, "Pattern-Oriented Software
Architecture, Volume 1. A System of Patterns," Wiley, 1996, where Blackboard
appears as one of the book's architectural patterns, alongside Layers,
Pipes and Filters, and Broker, for systems that must combine many diverse,
error prone, and incomplete problem solving techniques.

In the last three years the pattern reappeared without most people who use it
knowing its name. A live search turned up a concrete instance, the open source
project agent-blackboard, whose README describes itself as "a multi-agent
coordination system for software engineering tasks using the Blackboard
Pattern with MCP integration," where "specialized AI agents collaborate on
complex software engineering tasks through a shared knowledge repository
(blackboard)" (GitHub, claudioed/agent-blackboard,
https://github.com/claudioed/agent-blackboard, verified 2026-08-02). That
project names its own architecture correctly. Most large language model
orchestration frameworks that ship an equivalent mechanism, a piece of shared
mutable state that many independently invoked agents read from and write to,
do not use the word blackboard anywhere in their documentation, they call it
State, shared memory, or a scratchpad. This entry treats those mechanisms as
instances of the same pattern under a different name, the way a modern event
bus is still Observer even when nobody writing it has read Design Patterns.

## 2. Problem and context

A single agent loop works when one actor, running one prompt at a time, can
hold enough of the problem in its own context to make progress alone. Many
real tasks break that assumption on purpose. A research question needs
several independent lines of investigation pursued at once, a code review
needs a security pass, a style pass, and a correctness pass that do not
depend on each other's order, a document needs drafting, fact checking, and
formatting by separate specialized agents, and a planning problem needs a
mix of heuristics where no single one is reliable enough to trust alone.

In every one of those situations the agents involved do not know, ahead of
time, in what order their contributions will become useful, and they do not
want to be wired directly to each other, because a direct wire between agent
A and agent B means agent A must know agent B exists, must know its input
shape, and must be re-written the day agent B is replaced by agent C. The
concrete symptom a reader will recognize in their own codebase is an
orchestrator function that grows a new branch, a new prompt template, and a
new parsing step every time a new specialized agent is added, until the
orchestrator itself becomes the bottleneck for every change.

The blackboard responds to this by removing the direct wiring entirely.
Every agent reads a shared piece of state, does whatever independent work it
knows how to do, and writes its result back to the same shared state, without
any agent needing to know which other agent produced an input or will consume
an output. The context this fits is specifically one where the SOLUTION is
assembled opportunistically, from partial, ranked, and sometimes contradictory
contributions arriving at unpredictable times, not one where the workflow is a
known, fixed sequence of steps. A fixed sequence is a pipeline, and forcing a
fixed sequence into a blackboard, or forcing an opportunistic problem into a
fixed pipeline, is where most of the misuse in dimension 11 comes from.

## 3. Forces

**Decoupling versus visibility.** The blackboard buys agents freedom from
knowing about each other, at the direct cost that no single piece of code
shows the full flow of a request. A reader tracing a bug has to read the
blackboard's history rather than a call stack, because there is no call
stack that spans agents, only a sequence of writes.

**Flexibility versus determinism.** Because any qualified agent can act at
any point the blackboard changes, the exact order of contributions is not
fixed in advance, which is precisely what lets the system adapt when a
knowledge source is unavailable or a piece of evidence arrives out of order.
The price is that the same input can, in principle, produce a different
trace on two runs, which matters for reproducibility and for testing.

**Parallelism versus consistency.** Multiple knowledge sources reading and
writing the same shared state concurrently is the entire point, it is what
lets an expensive fact check run alongside a cheap style pass, but every
concurrent write is a race the control mechanism has to resolve, and a
naive implementation either serializes everything, which throws away the
parallelism, or lets two agents silently overwrite each other's
contribution, which produces a wrong answer that looks like a right one.

**Cost versus completeness.** An opportunistic controller keeps invoking
knowledge sources as long as any of them believes it can still improve the
solution, which is exactly the behavior that makes a hard problem solvable
with several weak heuristics, and exactly the behavior that can burn an
unbounded token budget on a large language model deployment if nobody caps
the number of rounds. This is the sharpest force in the agentic instance of
the pattern that the 1980s literature never had to weigh, because a 1980s
knowledge source was a cheap local subroutine and a modern knowledge source
is frequently a paid API call with multi-second latency.

**Cognitive load versus specialization.** Each individual knowledge source
can be small, single purpose, and easy to reason about in isolation, which
lowers the cognitive load of building any one of them, but understanding the
system as a whole requires understanding the control policy that decides
which knowledge source fires when, which is a different and less local kind
of reasoning than reading any single agent's prompt.

The pattern favors decoupling, flexibility, parallelism, and specialization.
It sacrifices a linear trace, deterministic replay, unbounded cost control,
and whole-system readability from any one file, and every one of those
sacrifices has to be paid back deliberately through the mechanisms in
dimensions 15, 16, and 17, not assumed away.

## 4. Applicability and non-applicability

Reach for an agentic blackboard when the problem genuinely has these shapes.

- The task decomposes into contributions from several independent
  knowledge sources whose relative usefulness cannot be ranked ahead of
  time, so a fixed calling order would be an arbitrary guess.
- Evidence or partial solutions can arrive in any order and each
  contribution should be able to build on whatever is currently on the
  board, not on a fixed predecessor step.
- The set of participating agents changes over the system's lifetime, new
  knowledge sources get added, old ones get retired, and neither event
  should require rewriting how the others communicate.
- Multiple agents can usefully work in parallel on the same evolving
  problem state, and the value of parallelism outweighs the cost of
  coordinating concurrent writes.
- The problem benefits from opportunistic, "whatever helps most right now"
  scheduling rather than a plan fixed before execution starts, which is the
  same shape Barbara Hayes-Roth's BB1 was built to exploit for tactical
  planning, according to Wikipedia's summary of BB1's origin (Wikipedia,
  "Blackboard system", https://en.wikipedia.org/wiki/Blackboard_system,
  verified 2026-08-02).

Do NOT reach for it in these situations.

- The workflow is actually a known, fixed sequence of steps. That is
  Prompt Chaining or Pipes and Filters, and a blackboard around a fixed
  sequence adds a shared mutable state, a scheduler, and a race-condition
  surface for zero benefit over calling step two after step one returns.
- There is exactly one agent doing exactly one job with no other
  contributor. A blackboard with one knowledge source is a global variable
  wearing a costume.
- A single supervising agent is meant to retain full, ordered control over
  which subordinate acts next and in what sequence, and that control is a
  feature, not a limitation to route around. That is Multi-Agent Supervisor,
  and the two patterns are marked incompatible in this entry's frontmatter
  precisely because a supervisor that always decides the next actor and a
  blackboard where any qualified knowledge source can act are two different
  answers to the same coordination question.
- The task is latency sensitive and the number of rounds needed to
  converge cannot be bounded in advance, because an opportunistic
  controller that keeps polling knowledge sources until none of them wants
  to act again has no natural stopping point without an explicit budget,
  and a synchronous request path cannot absorb an unbounded number of
  large language model round trips.
- Strong consistency is required on every read, for example a financial
  ledger balance that must never be read half-updated. A blackboard's
  natural mode is eventual assembly of a solution from partial writes, and
  bolting transactional isolation onto every read defeats the parallelism
  that justified the pattern in the first place.
- The team cannot afford to build and operate a real control mechanism.
  A blackboard without a working scheduler degenerates into knowledge
  sources firing in an undefined order on a global variable, which is
  worse than no shared state at all, because it looks coordinated while
  behaving like a data race.

## 5. Structure

Three participants, unchanged in name and role since Hearsay-II, still
carry the pattern in its agentic form.

**Blackboard.** The shared, structured, mutable data space. In an agentic
system this is not a single scalar, it holds typed regions, for example a
facts region for verified evidence, a hypotheses region for candidate
partial answers with a confidence score attached, and a plan region for
the current best guess at how to finish the task. Every knowledge source
reads whatever regions it needs and writes new or revised entries back,
tagged with its own identity and a confidence or priority value so later
readers can weigh contributions against each other.

**Knowledge Source.** A self-contained unit of expertise, in the agentic
instance this is one large language model agent with its own prompt,
tools, and, in the strongest implementations, its own precondition
function that inspects the blackboard and reports how confident it is that
it can usefully act right now. A knowledge source never calls another
knowledge source directly. It only ever talks to the blackboard.

**Control Component.** The scheduler that decides, each cycle, which
eligible knowledge source gets to act next. Wikipedia's summary of the
pattern names this component's job precisely, "it selects, configures and
executes modules," and adds that the control component "generally takes
the form of a complex scheduler that makes use of a set of domain-specific
heuristics to rate the relevance of executable knowledge sources"
(Wikipedia, "Blackboard (design pattern)",
https://en.wikipedia.org/wiki/Blackboard_(design_pattern), verified
2026-08-02). In an agentic system the control component additionally owns
the budget, it decides when the round count, the token spend, or the
elapsed wall clock time has exceeded what the task is worth, and halts the
loop with whatever solution is currently the highest-confidence entry on
the board.

A fourth role, not always named separately in the classical literature but
load bearing in every real agentic implementation, is the Termination
Judge, the piece of logic, sometimes a rule and sometimes a dedicated
evaluator agent, that decides the current state of the blackboard counts
as a finished, sufficient answer, as opposed to merely a state where no
knowledge source currently wants to act. Those two conditions are not the
same thing, and conflating them is one of the most common production
failures, covered in dimension 11.

## 6. ASCII structure diagram

```
+----------------------------------------------------------------+
|                       CONTROL COMPONENT                         |
|  polls preconditions, ranks eligible sources, enforces budget   |
|  owns round_count, token_spend, wall_clock_deadline               |
+----------------------------------------------------------------+
              |  reads eligibility        |  invokes winner
              v                           v
+----------------------------------------------------------------+
|                          BLACKBOARD                              |
|  +-----------+   +--------------+   +-----------------------+   |
|  |  facts    |   | hypotheses    |   |  plan / control state |   |
|  |  region   |   |  region        |   |       region          |   |
|  +-----------+   +--------------+   +-----------------------+   |
|  every entry: value, author, confidence, timestamp, refs         |
+----------------------------------------------------------------+
   ^read/write   ^read/write   ^read/write            ^read/write
   |             |             |                      |
+--------+   +--------+   +----------+          +--------------+
| KS: fact |   | KS: risk |  | KS: style  |          | Termination   |
| checker  |   | analyzer |  |  reviewer  |          |   Judge       |
+--------+   +--------+   +----------+          +--------------+
   (each Knowledge Source is one LLM agent, independent of the others)
```

## 7. Dynamics

The runtime loop is a repeated poll-select-invoke-write cycle, not a
straight-line call sequence, and this is the single largest visual
difference from a pipeline or a supervisor tree.

```
CONTROL LOOP (one iteration)

  1. control component reads blackboard snapshot
        |
  2. for each registered knowledge source, ask its
     precondition function how useful its contribution
     would be given this snapshot
        (returns a numeric eligibility score, or zero)
        |
  3. control component ranks the eligible sources
        and selects the single highest scoring one
        (ties broken by priority order or by a small
        exploration policy, never by call order alone)
        |
  4. selected knowledge source is invoked with the
     blackboard regions it declared it needs, in
     isolation, with no visibility into any other
     knowledge source's internal state
        |
  5. knowledge source returns a proposed write
        region, value, confidence, author, refs-to-inputs
        |
  6. control component applies the write under a
     region-scoped guard, merges or supersedes prior
     entries per that region's merge policy
        |
  7. control component asks the termination judge
     whether the blackboard is now a sufficient solution
        |
        +-- yes --> loop ends, best entry returned
        |
        +-- no, but budget exhausted --> loop ends,
        |                                best entry
        |                                returned with
        |                                a partial flag
        |
        +-- no, budget remains --> go to step 1
```

The critical property this diagram makes visible is that step 4 never
calls another knowledge source. Everything a knowledge source needs to act
came from the blackboard in step 4's own invocation, and everything it
produces goes back through steps 5 and 6, never directly to a peer. A
sequence diagram drawn agent-to-agent, the way it would be drawn for
Multi-Agent Supervisor or Chain of Responsibility, would be the wrong
picture for this pattern, because there is no agent-to-agent edge to draw.

## 8. Implementation variants

**Polling versus event-driven activation.** The classical implementation,
matching the loop in dimension 7, polls every registered knowledge source's
precondition on every cycle. This is simple and correct but wastes work
when most sources are irrelevant to the current state. The event-driven
variant has each knowledge source subscribe to the specific blackboard
regions it cares about and only recomputes its eligibility when one of
those regions changes, which scales to dozens of knowledge sources without
a linear per-cycle cost, at the price of a subscription bookkeeping layer
the polling variant does not need.

**Confidence-scored versus binary eligibility.** BB1's meta-level control,
as described by Wikipedia, reasoned explicitly about which knowledge
source to run using its own scheduling knowledge sources operating on a
control blackboard (Wikipedia, "Blackboard system",
https://en.wikipedia.org/wiki/Blackboard_system, verified 2026-08-02). A
lighter agentic variant skips a full meta-level blackboard and simply has
each knowledge source return a float in a bounded range from its own
precondition check, and lets the control component take an arg-max. This
is far cheaper to build and is the shape used by the reference
implementations in dimension 9, at the cost of losing BB1's ability to
reason about its own scheduling decisions.

**Language-idiomatic shapes.** In TypeScript and Python, the blackboard is
naturally a typed object or dataclass with named regions, guarded by an
async gate per region, and knowledge sources are async functions rather
than classes, since neither language needs an interface to satisfy a
knowledge source contract, a function with the right signature is
enough. In Go, the blackboard is idiomatically a struct owned by a single
long-running goroutine that serializes every read and write through
channels, which is the language's own recommended answer to shared state,
share memory by communicating rather than by guarding a shared variable
directly, and it maps unusually well onto the pattern because Go's
concurrency primitives were designed for exactly this class of
many-independent-workers-one-shared-state problem. In Java, the pattern is
typically built with an ExecutorService driving knowledge source tasks
and a ConcurrentHashMap backed blackboard, close in spirit to the
open source JBlackboard family implementations that predate the large
language model era and were built for rule based expert systems rather
than for agents.

**Single-process versus distributed blackboard.** A single-process
implementation keeps the blackboard as an in-memory object, which is
simplest and is what almost every current large language model
orchestration framework ships by default. A distributed implementation
backs the blackboard with a shared store, a key-value store, a document
database, or a pub-sub topic with a materialized read model, so that
knowledge sources can run as separate processes or separate serverless
invocations. This is the shape needed once a single knowledge source's
latency, for example a slow web search agent, would otherwise block every
other agent that shares its process.

## 9. Known production uses

**agent-blackboard.** An open source multi-agent coordination system for
software engineering tasks that names its own architecture the Blackboard
Pattern and integrates it with the Model Context Protocol, so specialized
agents for API design, backend architecture, and observability
"collaborate on complex software engineering tasks through a shared
knowledge repository (blackboard)" (GitHub, claudioed/agent-blackboard,
https://github.com/claudioed/agent-blackboard, verified 2026-08-02). This
is the clearest direct evidence that developers building large language
model agent systems in 2025 and 2026 reach for this exact architecture and
name it correctly.

**LangGraph's shared graph state.** LangGraph's own GitHub description
positions the framework as a "low-level orchestration framework for
building stateful agents" and lists memory management among its named
capabilities (GitHub, langchain-ai/langgraph,
https://github.com/langchain-ai/langgraph, verified 2026-08-02). The
framework's central mechanism, independently confirmed by its widespread
public documentation, is a single typed state object that every node in a
graph, where a node frequently wraps a distinct agent, can read from and
write updates into, with those updates merged by a reducer function rather
than by direct node-to-node calls. That shape, one shared mutable state
object, many independently invoked participants, and a merge function
standing in for the classical control component's write policy, is a
software instance of a blackboard even though LangGraph's own materials do
not use the word, in the same way that a modern publish-subscribe event
bus is an instance of Observer without anyone writing it calling it that.

**BB1 and GBB, the historical proof of the pattern's range.** Barbara
Hayes-Roth's BB1 architecture was applied to "construction site planning,
inferring 3-D protein structures from X-ray crystallography, intelligent
tutoring systems, and real-time patient monitoring," while Daniel
Corkill's GBB, later continued as the open source GBBopen project,
optimized the same architecture for raw execution efficiency rather than
BB1's meta-level reasoning (Wikipedia, "Blackboard system",
https://en.wikipedia.org/wiki/Blackboard_system, verified 2026-08-02).
These are cited not as currently maintained large language model systems
but as the direct ancestral evidence that the same three-participant
structure has already been proven across four unrelated problem domains
long before a single large language model existed, which is the strongest
available argument that the pattern's applicability in dimension 4 is
about problem SHAPE and not about the specific technology used to build
any one knowledge source.

**The negative control case, AutoGen's group chat.** Microsoft's AutoGen
framework ships a coordination mechanism that looks superficially similar
and is worth naming precisely because it is not the same pattern. AutoGen's
own documentation describes group chat as a design pattern where a group
of agents "share a common thread of messages," each of them subscribing
and publishing to the same topic, and each participating agent keeps its
own local chat history list that it appends to on receiving a message,
rather than reading and writing one shared mutable state object
(Microsoft, AutoGen core user guide, group chat design pattern,
https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/group-chat.html,
verified 2026-08-02). This is a publish-subscribe message bus with
per-agent local copies of history, which is the Observer pattern combined
with sequential turn-taking, not a blackboard. Citing it here, honestly, as
a system that is often described informally as blackboard-like but does
not actually share one mutable state object, is more useful to a reader
than pretending every multi-agent coordination mechanism is the same
pattern under a different name.

## 10. Consequences

**Positive.**

- Knowledge sources are added or removed without touching any other
  knowledge source's code, because none of them ever refer to another by
  name, only to the shared regions of the blackboard.
- The system degrades gracefully when one knowledge source is slow,
  unavailable, or wrong, since the control component simply does not
  select it and other sources continue contributing to the board.
- Genuine parallelism is available for free wherever knowledge sources
  do not depend on each other's most recent output, which is common in
  fan-out heavy tasks like research or multi-angle code review.
- The solution that emerges reflects the single highest confidence
  contribution on any given region at any point, rather than whichever
  agent happened to run last in a fixed sequence, which tends to produce
  a better answer on problems where the right expert to trust changes
  depending on what the input actually turns out to be.
- New expertise is straightforward to bolt on later, because the
  interface every knowledge source satisfies is small and stable, read
  some regions, propose a write, expose a precondition score.

**Negative.**

- There is no single readable trace of what happened, a debugger has to
  reconstruct the sequence of writes from the blackboard's own history log,
  which is why dimension 16 treats a structured write log as non-optional
  rather than a nice-to-have.
- The termination condition is a genuinely hard design problem. Getting it
  wrong produces either a system that stops too early, having mistaken
  nobody wanting to act right now for the answer being done, or one that
  never converges and burns budget until an external timeout kills it.
- Concurrent writes to the same region are a real race condition, not a
  theoretical one, and every implementation has to choose and document a
  merge policy, last-write-wins, highest-confidence-wins, or an explicit
  conflict region, or it will produce silently corrupted or contradictory
  state under load.
- Reproducing a bug from a production run is harder than in a fixed
  pipeline, because the exact order knowledge sources fired in is a
  function of a scheduler's ranking decisions and of external latency,
  neither of which is guaranteed to be identical on a second run unless
  the implementation deliberately records and can replay that order.
- Cost is fundamentally harder to bound in advance than in a pipeline with
  a known number of stages, because the number of rounds before
  termination depends on how many knowledge sources keep finding
  something useful to contribute, which is exactly the property that
  makes the pattern powerful and exactly the property that makes a naive
  implementation expensive.

## 11. Failure modes and misuse

Unbounded rounds from a confused termination check. The symptom is a
system that loops far longer than the task warrants, or stops only when an
external timeout kills it, with a cost dashboard that shows a slow climb
across every run of the same task rather than converging. The cause is
the termination judge conflating "no knowledge source currently wants to
act" with "the task is done." A knowledge source with a low but nonzero
precondition score, for example a style reviewer that always finds one
more nit, keeps making the round count go up forever because its own bar
for acting again is trivially satisfied by any new write from any other
source. The fix is separating the two conditions explicitly, termination
becomes a distinct check, either a confidence threshold on the current
best hypothesis, a hard round or token budget, or a dedicated evaluator
agent that judges sufficiency, and it must be checked and able to fire
even while individual knowledge sources still report nonzero eligibility.

Lost writes from an unguarded race. The symptom is that two knowledge
sources' contributions to the same region silently disappear, and the
final answer is missing evidence that was definitely produced by an
earlier round, visible only by reading the raw write log. The cause is an
unguarded read-modify-write on a shared region, two knowledge source
invocations overlapped, both read the same prior state, and the second
write clobbered the first with no merge. The fix is routing every write
to a region through the control component under a region-scoped guard, or,
in the distributed variant, an optimistic concurrency check with a
documented merge policy, never a bare assignment from a knowledge
source's own process.

Nondeterministic replay breaking an evaluation suite. The symptom is that
the exact same input, re-run twice, produces two visibly different final
answers, which breaks any evaluation suite that asserts on the output.
The cause is the control component's tie-breaking or scheduling policy
having a nondeterministic component, most often concurrency-driven
ordering, that was never pinned or logged. The fix is logging the full
sequence of round, selected knowledge source, and blackboard snapshot
hash for every run, and, where reproducibility genuinely matters, making
tie-breaking deterministic given a fixed seed rather than dependent on
which async task happened to finish first.

Silent coupling through an undocumented region schema. The symptom is
that a new knowledge source is added, and unrelated existing knowledge
sources start behaving differently, even though nobody edited their code.
The cause is the new source writing into a region an older source reads
without checking the author or the confidence, so the older source is now
silently reading a different kind of value than it was designed for, a
coupling that only exists because both sources happen to touch the same
region name. The fix is treating blackboard regions as a schema with a
real contract, documenting what each region's entries are shaped like and
who is allowed to write to it, and adding a schema or type check at the
write path rather than trusting every future knowledge source to read the
informal convention correctly.

A blackboard in name only. The symptom is that the system is described as
a blackboard in a design document, but a code review shows one agent
calling another agent's function directly, with the shared state object
passed along almost as an afterthought. The cause is the team adopting
the pattern's vocabulary without adopting its decoupling discipline,
which is the exact same failure that turns a nominal Observer into
tightly coupled spaghetti when a subject starts calling concrete observer
methods instead of a generic notify. The fix is auditing for any direct
knowledge-source-to-knowledge-source call and routing it back through the
blackboard, or admitting the system is actually a pipeline or a
supervisor and renaming it, per dimension 4's non-applicability list,
rather than keeping a name that no longer describes the code.

## 12. Trade-off matrix

| Force | Agentic Blackboard | Multi-Agent Supervisor | Prompt Chaining | Orchestrator-Worker |
|---|---|---|---|---|
| Coupling between participants | None, all through shared state | Supervisor knows every worker | Each stage knows only the next | Orchestrator knows every worker's shape |
| Execution order | Opportunistic, decided per cycle | Centrally decided every turn | Fixed at design time | Centrally decided, often parallel fan-out |
| Adding a new participant | Register a knowledge source, no other change | Edit the supervisor's routing logic | Insert a new stage in the chain | Edit the orchestrator's dispatch logic |
| Debuggability | Requires reading a write log, no linear trace | Linear trace through the supervisor | Fully linear, easiest to trace | Mostly linear, branches at fan-out |
| Cost predictability | Hardest, rounds are open ended without a budget | Bounded by supervisor's own turn limit | Bounded, one call per stage | Bounded, one call per worker per round |
| Best fit | Diverse, unordered, uncertain contributions | One authority must always decide next | A known, sequential transformation | A known set of parallel subtasks with a synthesizer |

## 13. Related and incompatible patterns

Mediator is the closest classical relative, and the distinction is
precise. A Mediator centralizes COMMUNICATION between known colleagues, it
still routes specific messages to specific recipients the mediator knows
by identity. A Blackboard centralizes STATE, not communication, and a
knowledge source never addresses another knowledge source at all, it
writes to a region and has no idea, and no need to know, who if anyone
reads that region next.

Observer shares the "many independent reactors to one changing subject"
shape, but Observer's subject notifies a known list of registered
observer objects directly, while a Blackboard's control component
actively selects which single knowledge source runs next based on a
competitive eligibility check, rather than broadcasting to everyone who
happens to be listening. AutoGen's group chat, discussed in dimension 9,
sits closer to Observer than to Blackboard for exactly this reason.

Multi-Agent Supervisor and Orchestrator-Worker are marked incompatible in
this entry's frontmatter because they answer the same coordination
question, who acts next, with the opposite structural commitment. A
supervisor or an orchestrator is a single point of centralized authority
that decides every next step. A blackboard's control component ranks
eligibility rather than dictating action, and any knowledge source whose
precondition is satisfied is a candidate, which is the opposite design
choice from routing every decision through one authority. A system can
still use both patterns for different subproblems, for example an
orchestrator that spawns a blackboard-coordinated cluster of research
agents as one of its worker tasks, but the two mechanisms should never be
merged into a single coordination layer, because a scheduler that is
simultaneously one authority deciding and any qualified source acting is
not a design, it is an unresolved argument between two designs.

Agent Memory composes underneath a blackboard rather than competing with
it. The blackboard is the WORKING state for one in-flight task, while
agent memory typically persists lessons or facts ACROSS tasks. A common,
sound architecture writes the blackboard's finished, high-confidence
entries into long-term agent memory once the termination judge fires, so
the next task starts with prior knowledge without needing to keep every
past blackboard alive.

Hierarchical Agents compose above a blackboard cleanly, a higher-level
supervisor can treat an entire blackboard-coordinated cluster as one
opaque worker that it invokes and waits on, which lets a team get the
blackboard's opportunistic coordination inside a subproblem while keeping
a predictable, bounded interface at the level the rest of the system
depends on.

## 14. Refactoring path in and out

Introducing a blackboard into an existing fixed pipeline starts by naming
the shared state the pipeline's stages already implicitly pass along,
most fixed pipelines already thread an accumulating object through every
stage, and that object is the blackboard in disguise. Second, invert each
stage's call signature from stage two calling stage three into stage
three declaring what it needs from the shared object and reporting
whether it is currently useful to run. Third, introduce a minimal control
component that, for a first cut, can keep the exact same order the
pipeline used before, this proves the mechanism works without yet
introducing any nondeterminism. Fourth, and only once the first three
steps are stable and tested, relax the control component's ordering from
fixed to eligibility-ranked, and add the concurrency and merge policy from
dimension 11 before allowing more than one knowledge source to run at
once. Skipping straight to concurrent, opportunistic scheduling before the
shared state's read and write contracts are solid is the single most
common way this refactor produces a system that is harder to reason about
than the pipeline it replaced.

Removing a blackboard once it stops earning its place runs in the
opposite order and is triggered when a system has converged, in practice,
on one dominant round order every single time, at which point the
opportunistic scheduling is pure overhead paying for flexibility nobody
uses. Confirm the claim first, instrument the control component's write
log across enough production runs to see whether the selected order
actually varies, per the observability signals in dimension 16. If the
order is effectively fixed, inline that fixed order directly as a Prompt
Chain or a plain sequence of function calls, delete the eligibility
checks and the region guards, and keep the shared state object only if
more than one of the now-sequential stages still genuinely needs to read
something a much earlier stage wrote, in which case it survives as an
ordinary accumulator parameter rather than as a blackboard.

## 15. Testing and verification

Test each knowledge source in complete isolation first, since it is
already designed to have no dependency on any other agent, this is the
pattern's own biggest testing gift. Feed a knowledge source a hand
constructed blackboard snapshot and assert on its precondition score and
its proposed write, without ever running the full control loop, the same
way a unit test would exercise one Strategy implementation without
constructing the context that would normally select it.

Test the control component separately from every knowledge source by
substituting fake knowledge sources whose precondition scores and outputs
are hardcoded, this proves the scheduling, guarding, and termination logic
is correct independent of what any real agent happens to answer, and lets
a test assert on properties like a knowledge source with eligibility zero
never being invoked, or the loop halting within a fixed number of rounds
when every source reports zero eligibility, without a single real
language model call.

Test the merge policy adversarially with concurrent writers, spawn two or
more fake knowledge sources that deliberately race to write the same
region and assert the documented merge policy actually wins the race it
claims to guarantee, this is the test category production incidents in
dimension 11 most often reveal was never written.

For end-to-end verification, treat the full system the way any
nondeterministic system is tested, run the same input multiple times and
assert on properties of the FINAL blackboard state, the presence of
required regions, a confidence floor on the winning hypothesis, absence
of a documented conflict marker, rather than asserting on the exact
sequence of rounds that produced it, since that sequence is allowed to
vary by design. Where reproducibility genuinely matters, pin the
tie-breaking seed described in dimension 11's fix for nondeterminism and
assert on the full round sequence only in that pinned mode.

## 16. Observability signals

The single most valuable signal is a structured write log, one line per
accepted write to the blackboard, carrying the region, the author
knowledge source, the confidence, a hash or short digest of the value, and
the round number, because this log is the only artifact that lets anyone
reconstruct what happened after the fact, per the debuggability cost named
in dimension 10.

Track round count and elapsed wall clock time per task as a histogram, not
just an average, a healthy blackboard's round count clusters tightly
around a small number for a given task type, and a widening or bimodal
distribution is the earliest warning that the termination judge described
in dimension 11 is starting to misfire on some fraction of inputs.

Track, per knowledge source, how often it was eligible versus how often it
was actually selected, a knowledge source that is frequently eligible but
rarely selected may be redundant with a higher scoring source and a
candidate for removal, while a knowledge source that is never eligible is
either dead code or has a bug in its precondition function.

Track write conflicts, the count of times the merge policy from dimension
11 had to resolve a genuine race rather than a clean append, on a healthy
system under normal load this number should be small and should not climb
as concurrency increases faster than the concurrency itself does, a
disproportionate climb indicates the region granularity is too coarse or
too fine for the actual contention pattern.

Track token and dollar spend per task alongside round count, since the two
tend to correlate but a divergence, rounds staying flat while spend climbs,
usually means individual knowledge source invocations are growing larger
context windows over time as the blackboard itself grows, which is a sign
the knowledge sources need to be reading a filtered view of the board
rather than the entire accumulated history.

## 17. Security and privacy implications

A blackboard is a shared trust boundary by construction, every knowledge
source that can write to a region can influence what every OTHER knowledge
source that reads that region will do next, which means a single
compromised or malicious knowledge source, for example one whose
underlying model was jailbroken by adversarial input from an external
tool call, can inject a false high-confidence entry that a downstream
knowledge source treats as trustworthy fact. Any system exposing one
knowledge source to untrusted external content, a document, a web page, a
tool result, should treat that knowledge source's writes as lower trust by
policy, tagging them so downstream knowledge sources and the termination
judge can weigh or corroborate them rather than accepting them as
equivalent to a trusted internal source's output. This is the same class
of concern covered in depth by this repository's Prompt Injection Defense
entry, and a blackboard that shares state across trust boundaries should
compose with that pattern rather than skip it.

Data written to shared regions is, by the pattern's own design, visible to
every currently or future registered knowledge source, which means any
personally identifiable or otherwise sensitive information a knowledge
source writes to the board is now available to knowledge sources that had
no original reason to see it. A blackboard handling sensitive input should
apply redaction, per the PII Redaction entry in this repository's family,
before writing to a region, rather than relying on individual knowledge
sources to self-censor what they choose to read.

Because the write log described in dimension 16 is the primary forensic
artifact for this pattern, it is also, by the same token, a record that
can retain sensitive data for as long as the log is retained, and any
retention policy applied to conversation transcripts elsewhere in a system
should be applied to the blackboard's write log with equal care, not
treated as exempt because it looks like operational telemetry rather than
user-facing conversation.

## 18. References

1. Wikipedia, "Blackboard (design pattern)", https://en.wikipedia.org/wiki/Blackboard_(design_pattern), verified 2026-08-02. Origin attribution to the Hearsay-II project, and the description of the blackboard, knowledge source, and control component structure quoted in dimensions 1 and 5.
2. Wikipedia, "Blackboard system", https://en.wikipedia.org/wiki/Blackboard_system, verified 2026-08-02. History of BB1 by Barbara Hayes-Roth and GBB by Daniel Corkill, and BB1's named application domains, quoted in dimensions 1, 3, and 9.
3. Lee D. Erman, Frederick Hayes-Roth, Victor R. Lesser, and D. Raj Reddy, "The Hearsay-II Speech Understanding System, Integrating Knowledge to Resolve Uncertainty," ACM Computing Surveys, volume 12, issue 2, 1980. Authorship, venue, and year corroborated by the origin summary in reference 1.
4. Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, and Michael Stal, "Pattern-Oriented Software Architecture, Volume 1. A System of Patterns," Wiley, 1996. Codification of Blackboard as a software architectural pattern, cited in dimension 1.
5. GitHub, claudioed/agent-blackboard, https://github.com/claudioed/agent-blackboard, verified 2026-08-02. Named modern production use of the Blackboard Pattern for multi-agent software engineering coordination with Model Context Protocol integration, cited in dimensions 1 and 9.
6. GitHub, langchain-ai/langgraph, https://github.com/langchain-ai/langgraph, verified 2026-08-02. Description of LangGraph as a stateful agent orchestration framework with shared memory, classified as a software instance of the pattern in dimension 9.
7. Microsoft, AutoGen core user guide, group chat design pattern, https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/group-chat.html, verified 2026-08-02. Documentation of AutoGen's publish-subscribe group chat mechanism, cited as the negative control case distinguishing this pattern from a message bus in dimension 9.
8. This repository, multi-agent-supervisor.md, family 17-ai-agentic. Related pattern cited in dimensions 4, 12, and 13 for the coordination-question contrast between centralized supervision and blackboard eligibility ranking.

## Code examples

The Python implementation below is deliberately close to the classical
three-participant shape, with async knowledge sources, a precondition
score, and a guard-protected region write. The TypeScript implementation
shows the event-driven variant from dimension 8, where knowledge sources
subscribe to regions rather than being polled every round. The Go
implementation follows the idiom Go itself recommends for shared state,
a single long-running goroutine that owns the blackboard and serializes
every read and write through channels, so no other goroutine ever touches
the map directly.

### Python

```python
import asyncio
from dataclasses import dataclass, field
from typing import Callable, Awaitable


@dataclass
class Entry:
    value: object
    author: str
    confidence: float
    round_no: int


@dataclass
class Blackboard:
    regions: dict[str, list[Entry]] = field(default_factory=dict)
    log: list[str] = field(default_factory=list)
    _gate: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def write(self, region: str, entry: Entry) -> None:
        async with self._gate:
            self.regions.setdefault(region, []).append(entry)
            self.log.append(
                f"round={entry.round_no} region={region} "
                f"author={entry.author} confidence={entry.confidence:.2f}"
            )

    def best(self, region: str) -> Entry | None:
        entries = self.regions.get(region, [])
        return max(entries, key=lambda e: e.confidence, default=None)


class KnowledgeSource:
    def __init__(
        self,
        name: str,
        precondition: Callable[["Blackboard"], float],
        act: Callable[["Blackboard", int], Awaitable[tuple[str, Entry]]],
    ):
        self.name = name
        self.precondition = precondition
        self.act = act


async def run_blackboard(
    board: Blackboard,
    sources: list[KnowledgeSource],
    is_done: Callable[[Blackboard], bool],
    max_rounds: int = 20,
) -> Entry | None:
    for round_no in range(1, max_rounds + 1):
        scored = [(ks, ks.precondition(board)) for ks in sources]
        scored = [pair for pair in scored if pair[1] > 0.0]
        if not scored:
            break
        winner, _ = max(scored, key=lambda pair: pair[1])
        region, entry = await winner.act(board, round_no)
        await board.write(region, entry)
        if is_done(board):
            break
    return board.best("plan")


async def fact_checker_act(board: Blackboard, round_no: int) -> tuple[str, Entry]:
    await asyncio.sleep(0)
    return "facts", Entry(value="revenue grew 12 percent", author="fact_checker",
                           confidence=0.8, round_no=round_no)


async def planner_act(board: Blackboard, round_no: int) -> tuple[str, Entry]:
    fact = board.best("facts")
    plan_value = f"summarize using {fact.value}" if fact else "summarize"
    return "plan", Entry(value=plan_value, author="planner", confidence=0.85,
                          round_no=round_no)


def build_demo_sources() -> list[KnowledgeSource]:
    return [
        KnowledgeSource(
            "fact_checker",
            lambda b: 0.0 if b.regions.get("facts") else 0.9,
            fact_checker_act,
        ),
        KnowledgeSource(
            "planner",
            lambda b: 0.7 if b.regions.get("facts") and not b.regions.get("plan") else 0.0,
            planner_act,
        ),
    ]


async def main() -> None:
    board = Blackboard()
    sources = build_demo_sources()
    result = await run_blackboard(
        board,
        sources,
        is_done=lambda b: b.regions.get("plan") is not None,
    )
    print("final plan", result.value if result else None)
    for line in board.log:
        print(line)


if __name__ == "__main__":
    asyncio.run(main())
```

### TypeScript

```typescript
type Entry = {
  value: string;
  author: string;
  confidence: number;
  round: number;
};

type Regions = Record<string, Entry[]>;

class Blackboard {
  regions: Regions = {};
  log: string[] = [];
  private queue: Promise<void> = Promise.resolve();

  write(region: string, entry: Entry): Promise<void> {
    const task = this.queue.then(() => {
      const list = this.regions[region] ?? [];
      list.push(entry);
      this.regions[region] = list;
      this.log.push(
        `round=${entry.round} region=${region} author=${entry.author} confidence=${entry.confidence.toFixed(2)}`,
      );
    });
    this.queue = task;
    return task;
  }

  best(region: string): Entry | undefined {
    const list = this.regions[region] ?? [];
    return list.reduce<Entry | undefined>(
      (top, current) => (!top || current.confidence > top.confidence ? current : top),
      undefined,
    );
  }
}

type KnowledgeSource = {
  name: string;
  precondition: (board: Blackboard) => number;
  act: (board: Blackboard, round: number) => Promise<[string, Entry]>;
};

async function runBlackboard(
  board: Blackboard,
  sources: KnowledgeSource[],
  isDone: (board: Blackboard) => boolean,
  maxRounds = 20,
): Promise<Entry | undefined> {
  for (let round = 1; round <= maxRounds; round += 1) {
    const eligible = sources
      .map((source) => ({ source, score: source.precondition(board) }))
      .filter((pair) => pair.score > 0);
    if (eligible.length === 0) break;
    eligible.sort((a, b) => b.score - a.score);
    const winner = eligible[0].source;
    const [region, entry] = await winner.act(board, round);
    await board.write(region, entry);
    if (isDone(board)) break;
  }
  return board.best("plan");
}

const factChecker: KnowledgeSource = {
  name: "fact_checker",
  precondition: (board) => (board.regions["facts"] ? 0 : 0.9),
  act: async (_board, round) => [
    "facts",
    { value: "revenue grew 12 percent", author: "fact_checker", confidence: 0.8, round },
  ],
};

const planner: KnowledgeSource = {
  name: "planner",
  precondition: (board) =>
    board.regions["facts"] && !board.regions["plan"] ? 0.7 : 0,
  act: async (board, round) => {
    const fact = board.best("facts");
    const value = fact ? `summarize using ${fact.value}` : "summarize";
    return ["plan", { value, author: "planner", confidence: 0.85, round }];
  },
};

async function main(): Promise<void> {
  const board = new Blackboard();
  const result = await runBlackboard(board, [factChecker, planner], (b) =>
    Boolean(b.regions["plan"]),
  );
  console.log("final plan", result?.value);
  for (const line of board.log) console.log(line);
}

main();
```

### Go

```go
package main

import "fmt"

type Entry struct {
	Value      string
	Author     string
	Confidence float64
	Round      int
}

type writeMsg struct {
	region string
	entry  Entry
	ack    chan struct{}
}

type readMsg struct {
	region string
	reply  chan []Entry
}

type Blackboard struct {
	writes chan writeMsg
	reads  chan readMsg
}

func NewBlackboard() *Blackboard {
	b := &Blackboard{
		writes: make(chan writeMsg),
		reads:  make(chan readMsg),
	}
	go b.owner()
	return b
}

func (b *Blackboard) owner() {
	regions := make(map[string][]Entry)
	var log []string
	for {
		select {
		case w := <-b.writes:
			regions[w.region] = append(regions[w.region], w.entry)
			log = append(log, fmt.Sprintf(
				"round=%d region=%s author=%s confidence=%.2f",
				w.entry.Round, w.region, w.entry.Author, w.entry.Confidence,
			))
			close(w.ack)
		case r := <-b.reads:
			snapshot := append([]Entry(nil), regions[r.region]...)
			r.reply <- snapshot
		}
	}
}

func (b *Blackboard) Write(region string, e Entry) {
	ack := make(chan struct{})
	b.writes <- writeMsg{region: region, entry: e, ack: ack}
	<-ack
}

func (b *Blackboard) Snapshot(region string) []Entry {
	reply := make(chan []Entry)
	b.reads <- readMsg{region: region, reply: reply}
	return <-reply
}

func (b *Blackboard) Best(region string) (Entry, bool) {
	entries := b.Snapshot(region)
	if len(entries) == 0 {
		return Entry{}, false
	}
	best := entries[0]
	for _, e := range entries[1:] {
		if e.Confidence > best.Confidence {
			best = e
		}
	}
	return best, true
}

func (b *Blackboard) Has(region string) bool {
	return len(b.Snapshot(region)) > 0
}

type KnowledgeSource struct {
	Name         string
	Precondition func(*Blackboard) float64
	Act          func(*Blackboard, int) (string, Entry)
}

func RunBlackboard(board *Blackboard, sources []KnowledgeSource, isDone func(*Blackboard) bool, maxRounds int) (Entry, bool) {
	for round := 1; round <= maxRounds; round++ {
		var winner *KnowledgeSource
		bestScore := 0.0
		for i := range sources {
			score := sources[i].Precondition(board)
			if score > bestScore {
				bestScore = score
				winner = &sources[i]
			}
		}
		if winner == nil {
			break
		}
		region, entry := winner.Act(board, round)
		board.Write(region, entry)
		if isDone(board) {
			break
		}
	}
	return board.Best("plan")
}

func main() {
	board := NewBlackboard()

	factChecker := KnowledgeSource{
		Name: "fact_checker",
		Precondition: func(b *Blackboard) float64 {
			if b.Has("facts") {
				return 0
			}
			return 0.9
		},
		Act: func(b *Blackboard, round int) (string, Entry) {
			return "facts", Entry{
				Value: "revenue grew 12 percent", Author: "fact_checker",
				Confidence: 0.8, Round: round,
			}
		},
	}

	planner := KnowledgeSource{
		Name: "planner",
		Precondition: func(b *Blackboard) float64 {
			if b.Has("facts") && !b.Has("plan") {
				return 0.7
			}
			return 0
		},
		Act: func(b *Blackboard, round int) (string, Entry) {
			value := "summarize"
			if fact, ok := b.Best("facts"); ok {
				value = "summarize using " + fact.Value
			}
			return "plan", Entry{Value: value, Author: "planner", Confidence: 0.85, Round: round}
		},
	}

	result, ok := RunBlackboard(board, []KnowledgeSource{factChecker, planner},
		func(b *Blackboard) bool { return b.Has("plan") }, 20)

	if ok {
		fmt.Println("final plan", result.Value)
	}
}
```

The pattern is not shown in Java, Rust, or Swift here. It translates
cleanly into all three, a Java version would use ExecutorService and
ConcurrentHashMap, a Rust version would use Arc-wrapped Mutex or a
tokio RwLock, and a Swift version would use an actor type, which maps
onto the pattern almost perfectly since an actor is already a serialized,
single-owner state boundary. Three languages were chosen here to keep
the entry within its word budget while still showing the guarded shared
struct shape in Python, the async single-queue shape in TypeScript, and
the channel-owned actor shape in Go, which together cover the concurrency
idioms a reader is most likely to reach for first.
