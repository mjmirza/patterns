---
name: Tree of Thoughts
slug: tree-of-thoughts
family: 17-ai-agentic
category: AI and Agentic
aliases: [ToT, Deliberate Problem Solving, LLM-Guided Tree-of-Thought]
first_described: "Yao, Yu, Zhao, Shafran, Griffiths, Cao, Narasimhan 2023 (concurrently, Long 2023)"
maturity: established
related: [chain-of-thought, self-consistency, react-pattern, reflection, plan-and-solve, monte-carlo-tree-search, beam-search, retry-with-backoff]
incompatible_with: []
verified: 2026-08-02
---

# Tree of Thoughts

## 1. Name, aliases, and lineage

The canonical name is Tree of Thoughts, abbreviated ToT. It names a family of
inference-time methods that let a language model explore more than one line
of reasoning before committing to an answer, evaluate the partial lines it
has explored, and backtrack away from the ones that look unpromising.

The pattern has an unusually contested origin for something this young. Two
papers with almost the same title reached arXiv within two days of each
other in May 2023, proposing systems that differ in shape.

The paper most people cite is Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak
Shafran, Thomas L. Griffiths, Yuan Cao, and Karthik Narasimhan, "Tree of
Thoughts. Deliberate Problem Solving with Large Language Models," submitted
17 May 2023, arXiv 2305.10601, later published at NeurIPS 2023
(https://proceedings.neurips.cc/paper_files/paper/2023/hash/271db9922b8d1f4dd7aaef84ed5ac703-Abstract-Conference.html,
verified 2026-08-02). It frames ToT as a search algorithm with four explicit
design axes, thought decomposition, thought generation, state evaluation,
and a search algorithm, and reports the headline result that GPT-4 solves
the Game of 24 arithmetic puzzle 4 percent of the time with chain-of-thought
prompting and 74 percent of the time with ToT
(https://arxiv.org/abs/2305.10601, verified 2026-08-02).

Two days earlier, Jieyi Long submitted "Large Language Model Guided
Tree-of-Thought," arXiv 2305.08291, 15 May 2023
(https://arxiv.org/abs/2305.08291, verified 2026-08-02). Long's paper
proposes a different, more stateful architecture, an LLM extended with a
prompter agent, a checker module, a memory module, and a ToT controller that
runs a multi-round conversation with the model, using the controller to
decide when to backtrack. It does not cite or reference Yao's paper, and the
two groups developed the idea independently in the same week.

This double origin is not a footnote. It explains why two genuinely
different shapes both go by the name Tree of Thoughts in production code.
The Yao lineage is stateless and functional, a driver program outside the
model repeatedly calls generate, evaluate, and search over a data structure
it owns. The Long lineage is stateful and conversational, the tree lives
inside a running multi-turn dialogue with the model, and the controller
module decides when to prompt the model to backtrack. LangChain's
`langchain_experimental.tot.base.ToTChain` implemented Long's architecture
specifically, with its own docstring citing arXiv 2305.08291 rather than
Yao's paper (verified against the module source at
https://raw.githubusercontent.com/langchain-ai/langchain/v0.1.0/libs/experimental/langchain_experimental/tot/base.py,
retrieved 2026-08-02). A reader who only knows the Yao paper and then opens
that source file will be confused about why the class talks about a checker
and a controller rather than a beam width. Both are Tree of Thoughts. They
solve the same problem with a different division of labor between the
driver and the model.

This entry follows the Yao formulation as the primary structure, because it
is the one every later paper in this space, Graph of Thoughts, Language
Agent Tree Search, and the various open source reimplementations, treats as
the reference point to extend or to beat. Where the Long lineage differs in
a way that matters for a reader choosing between them, that difference is
called out explicitly rather than folded silently into one description.

## 2. Problem and context

A language model produces its answer as a single left-to-right token
stream. Chain-of-thought prompting, Jason Wei, Xuezhi Wang, Dale Schuurmans,
Maarten Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc V. Le, and Denny Zhou,
"Chain-of-Thought Prompting Elicits Reasoning in Large Language Models,"
arXiv 2201.11903, NeurIPS 2022
(https://arxiv.org/abs/2201.11903, verified 2026-08-02), improved on a bare
answer by asking the model to write intermediate steps before the final
answer, and that alone produced large gains on arithmetic and commonsense
benchmarks. But a chain is still one path. Once the model commits to a
wrong early step, a greedy generation pass never reconsiders it, and the whole
downstream chain inherits the mistake. A person solving the same problem on
paper does not work this way. They try a step, notice it leads nowhere,
cross it out, and try a different step from the same starting point. That
crossing out and retrying is exactly what a single autoregressive pass
cannot do on its own, because token generation is a one-way street.

The concrete situation looks like this in practice. A task decomposes
naturally into a short sequence of intermediate decisions, and getting any
one of those decisions wrong early on makes the rest of the sequence
unsalvageable, no matter how carefully the model reasons afterward. The
task also has a way, even an imperfect one, to tell a promising partial
answer from a doomed one before the full answer is complete, because
without that signal there is nothing to search on and no way to prune
anything. And the task is valuable enough, or high stakes enough, that
spending many times the tokens of a single pass to raise the success rate
is worth the cost. Game of 24, where four numbers must combine via
arithmetic to reach 24 and a wrong first combination throws away one of the
four numbers, is the paper's own flagship example precisely because it satisfies
all three conditions cleanly, decomposition is obvious, mid-solution
progress is checkable, and one greedy pass finds a working sequence of
operations only 4 percent of the time.

Outside that context the extra cost buys nothing. If a task is answerable
in one clean deductive line with no real branch point, ToT explores a
tree that has effectively one path anyway, and the overhead is pure waste.
See the full non-applicability list in dimension 4.

## 3. Forces

Tree of Thoughts is not a free improvement over Chain-of-Thought. It trades
one resource for another, deliberately.

- **Sample quality versus token and latency cost.** Favors quality,
  sacrifices cost. Every additional branch explored is one more full or
  partial completion from the model. A ToT run with breadth b and depth d
  can issue on the order of b times d separate generation calls plus a
  comparable number of evaluation calls, against one call for a plain
  chain. This is the central, unavoidable trade the whole pattern turns on,
  and it is the reason ToT is rare in latency-sensitive production paths
  and common in offline, batch, or human-supervised ones.
- **Robustness to an early wrong step versus determinism.** Favors
  robustness. A wrong early token in plain, single-pass generation is permanent. A wrong
  early thought in ToT is one branch among several, and the search can
  route around it. The engineering judgment worth stating plainly here,
  this is the single force the pattern exists to buy, and every other force
  below is a cost paid for it.
- **Evaluator reliability versus search effectiveness.** This is the
  hidden coupling most explanations skip. ToT's search is only as good as
  its evaluator. A search algorithm with a perfect frontier-expansion
  strategy and a bad evaluator prunes correct branches with the same confidence
  as it prunes bad ones, because the search cannot tell the difference
  between a thought that scores low because it is wrong and one that scores
  low because the evaluator is a poor judge of promise at that intermediate
  state. This is engineering judgment grounded in the mechanics of the
  algorithm, not a claim the source paper states in these words, and it is
  demonstrated directly in the runnable example in dimension 8.
- **Interpretability versus opacity.** Favors interpretability, mildly. The
  explored tree, kept in full, is a legible audit trail of alternatives
  tried and rejected, which a single chain does not offer. This is a real
  but secondary benefit next to the accuracy gain.
- **Statelessness versus conversational memory.** The Yao formulation
  favors a stateless, externally driven search where the tree lives in the
  calling program. The Long formulation favors keeping the tree inside a
  running conversation with the model, so the model itself remembers prior
  branches through the dialogue. Statelessness is easier to parallelize,
  checkpoint, and unit test. Conversational memory is easier to build with
  a plain chat completion API and no external tree data structure. Neither
  is strictly better, and picking one over the other is a real
  architectural decision, not a detail.
- **Determinism and reproducibility versus exploration.** Favors
  exploration. Sampling multiple candidate thoughts at temperature above
  zero is what makes the branches different from each other. A
  deterministic, temperature-zero ToT run degenerates toward a single path
  unless the generation prompt itself is varied per branch, which weakens
  the guarantee that repeated runs on the same input produce the same
  answer, a property many production systems otherwise want.

## 4. Applicability and non-applicability

Reach for Tree of Thoughts when all of the following hold together, not any
one alone.

- The task decomposes into a short sequence of intermediate decisions,
  usually two to six steps, where an early choice materially constrains
  or forecloses later ones.
- A cheap, even approximate, signal exists to judge whether a partial
  solution looks promising before it is complete, whether that signal comes
  from the same model, a smaller model, or a symbolic checker.
  Constraint-satisfaction puzzles, code that must pass a test suite at each
  checkpoint, and multi-step planning with checkable sub-goals all carry
  this signal naturally.
- The task is valuable, ambiguous, or high stakes enough to justify several
  times the token cost of one pass, and the calling system can tolerate the
  added latency, either because it runs offline, in a batch, or with a
  human in the loop rather than in a live chat turn a person is staring at.
- A single greedy pass has a measurably poor success rate on the task, so
  there is real headroom for search to close. If chain-of-thought already
  solves the task close to reliably, the tree collapses to one useful
  branch and the rest of the exploration is wasted spend.

Do not reach for it under these conditions. This list is deliberately as
long as the applicability list, because it is the one most catalogs skip
and it is the one that actually prevents wasted engineering effort.

- **Latency-sensitive, synchronous, user-facing turns.** A chat reply, an
  autocomplete suggestion, or any interaction where a person is watching a
  spinner cannot absorb five to twenty times the generation calls of a
  plain response. Use Chain-of-Thought or a single well-prompted pass
  instead, and reserve search for a background or asynchronous path if the
  accuracy gain is worth it there.
- **Tasks with no usable intermediate evaluation signal.** Open-ended
  creative tasks with no objective mid-point quality signal, free-form
  summarization, casual conversation, offer nothing for the evaluator to
  score, and self-evaluation on such tasks degrades into the model rating
  its own fluency, which correlates poorly with actual task success. The
  paper's own Creative Writing benchmark works only because it substitutes
  a coherence vote for a hard correctness signal, and the authors are
  explicit that this evaluation is softer than the Game of 24 case.
- **Single-shot factual lookup or retrieval.** If the correct answer is
  either in the model's weights or in a retrieved document and there is no
  multi-step derivation to search over, tree search adds calls without
  adding accuracy. RAG, retrieving external documents to ground the
  answer, or a plain factual prompt is the right tool.
- **Tasks with an exact, cheap, non-LLM solver already available.** Game of
  24 itself has a five-line brute-force solution in Python that runs in
  microseconds. Applying ToT to a problem class that already has a
  polynomial-time deterministic algorithm burns tokens to approximate what
  a for loop already computes exactly. ToT earns its place only where no
  such solver exists, or where the task is a language problem with no
  symbolic solver at all.
- **Cost-capped or rate-limited API budgets with no room for a
  multiplier.** A production system already near its per-request token
  budget or its requests-per-minute limit cannot absorb a five-to-twenty
  times multiplier on any endpoint that adopts ToT, and the failure mode is
  not a slower answer, it is a hard rate-limit error partway through a
  search that has already spent most of its budget.
- **Streaming or partial-output requirements.** Because ToT withholds a
  final answer until the search concludes, it is a poor fit for any
  interface contract that expects tokens to stream to the user as they are
  produced.

## 5. Structure

Yao's formulation names four design axes, each independently substitutable
by an implementer without touching the rest.

- **Thought decomposer.** The function or prompt that defines what counts
  as one node in the tree, a "thought." For Game of 24 a thought is one
  arithmetic step combining two of the remaining numbers. For Creative
  Writing a thought is one full passage plan. The decomposer is a design
  choice made once per task, not something the search algorithm derives on
  its own.
- **Thought generator.** Given a partial state, produces one or more
  candidate next thoughts. The paper names two concrete strategies, sample
  independently and identically distributed thoughts from the model at
  temperature above zero when the thought space is broad and unstructured,
  or propose thoughts sequentially in one completion using a structured
  prompt when the space is narrow enough that duplicate or overlapping
  proposals waste budget.
- **State evaluator.** Given a partial state, or a small batch of them,
  produces a judgment of promise. The paper names two strategies, a value
  score per state where the model outputs a numeric or categorical rating
  such as sure, likely, or impossible, and a vote across states where the
  model is shown several candidates at once and asked to pick the best,
  which is often more reliable than asking the model to score each state in
  isolation because comparison is an easier judgment for a language model
  than absolute scoring.
- **Search algorithm.** The procedure that decides which frontier nodes to
  expand next and when to stop, most often breadth-first search keeping a
  fixed number of top-scoring states per level, or depth-first search with
  backtracking that abandons a branch once its evaluator score drops below
  a threshold.
- **Driver.** The external program, not the model, that owns the tree data
  structure, calls the generator and evaluator in a loop, and applies the
  search algorithm's decisions. In the Yao lineage the model has no memory
  of rejected branches unless the driver explicitly re-includes them in a
  later prompt. In the Long lineage this role is folded into a
  conversational controller that lives partly inside the model's own
  context window across turns.

## 6. ASCII structure diagram

```
                         +-----------------------+
                         |        Driver         |
                         |  (owns the tree, runs  |
                         |   the search loop)     |
                         +-----------------------+
                          |          |          |
                calls     |  calls   |   calls  |
                          v          v          v
              +------------+  +------------+  +-----------+
              |  Thought   |  |   Thought  |  |   State   |
              | Decomposer |  |  Generator |  | Evaluator |
              +------------+  +------------+  +-----------+
                    |               |               |
                    +-------+-------+-------+-------+
                            |
                            v
                     +-------------+
                     |   Search    |
                     |  Algorithm  |
                     | (BFS / DFS) |
                     +-------------+
                            |
                            v
                    the Thought Tree

                            (root: start state)
                                   |
                    +--------------+--------------+
                    |              |               |
               thought A      thought B        thought C
              score 0.7       score 0.2        score 0.9
                    |                               |
              +-----+-----+                   +-----+-----+
              |           |                   |           |
        thought A1   thought A2          thought C1   thought C2
        (kept, top-  (pruned, low        score 0.95   score 0.4
         2 beam)       score)            (expanded    (pruned)
                                          further)
```

## 7. Dynamics

```
Driver              Generator            Evaluator            Tree
  |                     |                    |                  |
  |-- start state ----->|                    |                  |
  |                     |-- N candidate ---->|                  |
  |                     |   thoughts         |                  |
  |<-- N thoughts ------|                    |                  |
  |-- score each ------------------------->  |                  |
  |<-- scores ------------------------------ |                  |
  |-- keep top-b, discard the rest -------------------------->  |
  |                     |                    |            (record kept
  |                     |                    |             + discarded)
  |-- for each kept state, repeat --->|      |                  |
  |    (generate, score, prune)       |      |                  |
  |                                   |      |                  |
  |-- goal state reached OR depth limit hit -----------------> STOP
  |                                                              |
  |-- return best complete path (or backtrack if DFS and        |
  |   the frontier is exhausted before a goal is found)          |
```

The dynamics differ by search strategy in a way worth naming explicitly.
Breadth-first Tree of Thoughts advances the whole frontier one level at a
time and keeps a fixed beam width at every level, so it never truly
backtracks, it only ever narrows. Depth-first Tree of Thoughts commits to
one branch, follows it to a leaf or to a failure, and only then unwinds the
call stack to try a sibling, which is what the original paper's Mini
Crosswords task uses because the state space there is too large for a wide
beam to cover and pruning a whole subtree early, on a clearly failing
partial fill, is cheaper than scoring every sibling at every level.

## 8. Implementation variants

- **Reference BFS with beam width.** The default in the paper for Game of
  24 and Creative Writing. Expand the entire frontier one level, score
  every child, keep the top b, discard the rest permanently. Simple, easy
  to parallelize, since every state at a given level can be generated and
  scored concurrently, but commits to discarding a state the moment its
  level's beam is full, even if a later level would have revealed it as the
  only correct branch.
- **DFS with pruning and backtracking.** Used for Mini Crosswords, where
  the branching factor per level is too large for BFS's per-level full
  expansion to be affordable. Follow one branch as deep as it will go,
  abandon it the instant the evaluator marks it impossible, and backtrack
  to the most recent unexplored sibling. Cheaper per branch explored, worse
  at exploiting parallel hardware, because siblings are explored one at a
  time rather than all at once.
- **Value-guided best-first search, closer to A\*.** Rather than expanding
  a fixed beam per level, maintain a single priority queue across the whole
  frontier, ranked by evaluator score, and always expand the single
  highest-scoring open state next, regardless of depth. This trades a
  guaranteed per-level parallel batch for a search that can go arbitrarily
  deep down one very promising path before returning to shallower
  alternatives, which the runnable example in this dimension demonstrates.
- **Monte Carlo Tree Search over language model thoughts.** Replace the
  deterministic evaluator with repeated random rollouts to a terminal state
  and back-propagate the rollout outcome as the node's estimated value,
  the approach Language Agent Tree Search takes, see dimension 9. This
  buys a statistically grounded value estimate at the cost of many more
  generation calls per node, since each rollout is itself a full or partial
  completion.
- **Self-consistency as a degenerate one-level tree.** Sampling k
  independent full chains and majority-voting the final answer, described
  in dimension 12, is, in shape, a Tree of Thoughts with depth 1, a
  single generation step that produces k siblings, and an evaluator that is
  simply exact-match voting on the final answer rather than the model
  scoring an intermediate thought. Naming this connection explicitly
  clarifies why Self-Consistency is cheaper and why it cannot recover from
  an early wrong step the way a deeper tree can, it never gets more than
  one level to search.
- **Conversational controller, the Long lineage.** Instead of an external
  driver holding tree nodes as data, keep the entire explored history in
  the model's own context window across conversational turns, and use a
  checker module, itself either a rule-based validator or a second model
  call, to decide whether the current turn's proposal is valid, and a ToT
  controller to decide whether to accept, ask the model to try again, or
  roll the conversation back to a marked earlier point. This variant is
  simpler to bolt onto a plain chat completion loop with no external graph
  library, and harder to parallelize, since a conversation runs one turn
  after another by construction.

The runnable example below implements the reference BFS variant with a
one-ply lookahead evaluator, in three languages, on the paper's own Game of
24 benchmark. Every implementation was executed locally for this entry.

```python
from dataclasses import dataclass
from itertools import combinations
from typing import Optional


@dataclass(frozen=True)
class State:
    values: tuple
    trace: str


def generate(state: State) -> list:
    """Thought decomposition and generation. one arithmetic step per node."""
    thoughts = []
    ops = [
        ("+", lambda a, b: a + b, False),
        ("-", lambda a, b: a - b, True),
        ("*", lambda a, b: a * b, False),
        ("/", lambda a, b: a / b if b != 0 else float("nan"), True),
    ]
    for i, j in combinations(range(len(state.values)), 2):
        rest = [v for k, v in enumerate(state.values) if k not in (i, j)]
        a, b = state.values[i], state.values[j]
        for sym, fn, non_commutative in ops:
            orderings = [(a, b, f"{a}{sym}{b}")]
            if non_commutative:
                orderings.append((b, a, f"{b}{sym}{a}"))
            for x, y, label in orderings:
                result = fn(x, y)
                if result != result:
                    continue
                thoughts.append(State(tuple(rest + [result]), f"{state.trace}; {label}={result}"))
    return thoughts


def evaluate(state: State, target: float) -> float:
    """Stands in for an LLM evaluator voting sure, likely, or impossible.
    A one-ply lookahead over the child states, deterministic and cheap."""
    if len(state.values) == 1:
        return 1.0 if abs(state.values[0] - target) < 1e-6 else 0.0
    best = min(
        min(abs(v - target) for v in child.values)
        for child in generate(state)
    )
    return 1.0 / (1.0 + best)


def tree_of_thoughts(start: tuple, target: float, beam: int, depth: int) -> Optional[State]:
    """Breadth-first search over the thought tree, keeping the top beam
    states per level by evaluator score. This is the search step."""
    frontier = [State(tuple(start), "start")]
    for _ in range(depth):
        candidates = []
        for state in frontier:
            candidates.extend(generate(state))
        if not candidates:
            return None
        for state in candidates:
            if len(state.values) == 1 and abs(state.values[0] - target) < 1e-6:
                return state
        candidates.sort(key=lambda s: (-evaluate(s, target), s.trace))
        frontier = candidates[:beam]
    return None


if __name__ == "__main__":
    puzzle, target = (4.0, 9.0, 10.0, 13.0), 24.0
    for beam in (5, 10):
        found = tree_of_thoughts(puzzle, target, beam=beam, depth=3)
        status = found.trace if found else "no solution within this beam"
        print(f"beam={beam}: {status}")

# Output, run locally with python3:
#   beam=5: no solution within this beam
#   beam=10: start; 9.0+10.0=19.0; 19.0-13.0=6.0; 4.0*6.0=24.0
```

```typescript
interface State {
  values: number[];
  trace: string;
}

type Op = [string, (a: number, b: number) => number, boolean];

const OPS: Op[] = [
  ["+", (a, b) => a + b, false],
  ["-", (a, b) => a - b, true],
  ["*", (a, b) => a * b, false],
  ["/", (a, b) => (b !== 0 ? a / b : NaN), true],
];

function generate(state: State): State[] {
  const thoughts: State[] = [];
  const n = state.values.length;
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const rest = state.values.filter((_, k) => k !== i && k !== j);
      const a = state.values[i];
      const b = state.values[j];
      for (const [sym, fn, nonCommutative] of OPS) {
        const orderings: [number, number, string][] = [[a, b, `${a}${sym}${b}`]];
        if (nonCommutative) orderings.push([b, a, `${b}${sym}${a}`]);
        for (const [x, y, label] of orderings) {
          const result = fn(x, y);
          if (Number.isNaN(result)) continue;
          thoughts.push({
            values: [...rest, result],
            trace: `${state.trace}; ${label}=${result}`,
          });
        }
      }
    }
  }
  return thoughts;
}

function evaluate(state: State, target: number): number {
  if (state.values.length === 1) {
    return Math.abs(state.values[0] - target) < 1e-6 ? 1 : 0;
  }
  const best = Math.min(
    ...generate(state).map((child) =>
      Math.min(...child.values.map((v) => Math.abs(v - target)))
    )
  );
  return 1 / (1 + best);
}

function treeOfThoughts(
  start: number[],
  target: number,
  beam: number,
  depth: number
): State | null {
  let frontier: State[] = [{ values: start, trace: "start" }];
  for (let step = 0; step < depth; step++) {
    let candidates: State[] = [];
    for (const state of frontier) candidates = candidates.concat(generate(state));
    if (candidates.length === 0) return null;
    for (const state of candidates) {
      if (state.values.length === 1 && Math.abs(state.values[0] - target) < 1e-6) {
        return state;
      }
    }
    candidates.sort(
      (a, b) => evaluate(b, target) - evaluate(a, target) || a.trace.localeCompare(b.trace)
    );
    frontier = candidates.slice(0, beam);
  }
  return null;
}

const puzzle = [4, 9, 10, 13];
const target = 24;
for (const beam of [5, 10]) {
  const found = treeOfThoughts(puzzle, target, beam, 3);
  console.log(`beam=${beam}: ${found ? found.trace : "no solution within this beam"}`);
}

// Compiled with: npx tsc --target es2020 --module commonjs --strict tot.ts
// Output, run with node:
//   beam=5: no solution within this beam
//   beam=10: start; 9+10=19; 19-13=6; 4*6=24
```

```go
package main

import (
	"fmt"
	"math"
	"sort"
)

type State struct {
	values []float64
	trace  string
}

type op struct {
	sym            string
	fn             func(a, b float64) float64
	nonCommutative bool
}

var ops = []op{
	{"+", func(a, b float64) float64 { return a + b }, false},
	{"-", func(a, b float64) float64 { return a - b }, true},
	{"*", func(a, b float64) float64 { return a * b }, false},
	{"/", func(a, b float64) float64 {
		if b == 0 {
			return math.NaN()
		}
		return a / b
	}, true},
}

func generate(s State) []State {
	var thoughts []State
	n := len(s.values)
	for i := 0; i < n; i++ {
		for j := i + 1; j < n; j++ {
			rest := make([]float64, 0, n-2)
			for k, v := range s.values {
				if k != i && k != j {
					rest = append(rest, v)
				}
			}
			a, b := s.values[i], s.values[j]
			for _, o := range ops {
				type pair struct {
					x, y  float64
					label string
				}
				orderings := []pair{{a, b, fmt.Sprintf("%g%s%g", a, o.sym, b)}}
				if o.nonCommutative {
					orderings = append(orderings, pair{b, a, fmt.Sprintf("%g%s%g", b, o.sym, a)})
				}
				for _, ord := range orderings {
					result := o.fn(ord.x, ord.y)
					if math.IsNaN(result) {
						continue
					}
					values := append(append([]float64{}, rest...), result)
					thoughts = append(thoughts, State{values, fmt.Sprintf("%s; %s=%g", s.trace, ord.label, result)})
				}
			}
		}
	}
	return thoughts
}

func evaluate(s State, target float64) float64 {
	if len(s.values) == 1 {
		if math.Abs(s.values[0]-target) < 1e-6 {
			return 1.0
		}
		return 0.0
	}
	best := math.Inf(1)
	for _, child := range generate(s) {
		for _, v := range child.values {
			d := math.Abs(v - target)
			if d < best {
				best = d
			}
		}
	}
	return 1.0 / (1.0 + best)
}

func treeOfThoughts(start []float64, target float64, beam, depth int) *State {
	frontier := []State{{append([]float64{}, start...), "start"}}
	for step := 0; step < depth; step++ {
		var candidates []State
		for _, s := range frontier {
			candidates = append(candidates, generate(s)...)
		}
		if len(candidates) == 0 {
			return nil
		}
		for _, s := range candidates {
			if len(s.values) == 1 && math.Abs(s.values[0]-target) < 1e-6 {
				return &s
			}
		}
		sort.Slice(candidates, func(i, j int) bool {
			si, sj := evaluate(candidates[i], target), evaluate(candidates[j], target)
			if si != sj {
				return si > sj
			}
			return candidates[i].trace < candidates[j].trace
		})
		if len(candidates) > beam {
			candidates = candidates[:beam]
		}
		frontier = candidates
	}
	return nil
}

func main() {
	puzzle := []float64{4, 9, 10, 13}
	target := 24.0
	for _, beam := range []int{5, 10} {
		found := treeOfThoughts(puzzle, target, beam, 3)
		if found != nil {
			fmt.Printf("beam=%d: %s\n", beam, found.trace)
		} else {
			fmt.Printf("beam=%d: no solution within this beam\n", beam)
		}
	}
}

// Run with: go run tot.go
// Output:
//   beam=5: no solution within this beam
//   beam=10: start; 9+10=19; 19-13=6; 4*6=24
```

This is the puzzle from the paper's own Game of 24 task, four, nine, ten,
thirteen combined to make twenty four. All three implementations were
compiled or run locally and produce identical results, `beam=5` fails to
find the correct sequence and `beam=10` finds `9+10=19, 19-13=6, 4*6=24`.
The failure at beam width five is not a bug, it is the pattern's central
force made visible in code, a narrower beam prunes the exact branch that
contains the only correct path, because the one-ply lookahead evaluator
cannot yet see that a state three moves away from a solution is any more
promising than a state that merely looks numerically closer to the target
right now. This is precisely the evaluator-reliability force named in
dimension 3, an evaluator that is not myopic enough to be cheap and not
farsighted enough to be reliable is the central engineering tension of the
whole pattern, and no amount of clever search algorithm design compensates
for a bad evaluator on its own.

## 9. Known production uses

- **LangChain's experimental Tree of Thought chain.**
  `langchain_experimental.tot.base.ToTChain`, together with its
  `ToTChecker`, `ToTController`, `ToTDFSMemory`, and
  `ProposePromptStrategy` classes, shipped as part of the widely used
  LangChain framework and implemented Long's checker-and-controller
  architecture as a runnable chain with a configurable branching factor `c`
  and round budget `k`
  (source verified at
  https://raw.githubusercontent.com/langchain-ai/langchain/v0.1.0/libs/experimental/langchain_experimental/tot/base.py,
  retrieved 2026-08-02). The `langchain-experimental` package that housed it
  is being sunset by its maintainers as of the version current on PyPI at
  time of writing, 0.4.2, dated 22 May 2026
  (https://pypi.org/project/langchain-experimental/, verified 2026-08-02),
  which is itself a useful, honest data point about the pattern, ToT never
  crossed from an experimental integration into LangChain's stable core in
  the way Chain-of-Thought prompting and ReAct-style tool calling did,
  because its per-call cost multiplier makes it a poor default for the
  general-purpose chat-completion use case the core library targets.
- **Language Agent Tree Search, ICML 2024.** Andy Zhou, Kai Yan, Michal
  Shlapentokh-Rothman, Haohan Wang, and Yu-Xiong Wang, "Language Agent Tree
  Search Unifies Reasoning, Acting, and Planning in Language Models,"
  arXiv 2310.04406, accepted at ICML 2024
  (https://arxiv.org/abs/2310.04406, verified 2026-08-02, official
  implementation at https://github.com/lapisrocks/LanguageAgentTreeSearch,
  verified 2026-08-02). LATS extends ToT's search-plus-evaluate loop with
  ReAct-style environment actions and self-reflection on failed rollouts,
  scored via Monte Carlo Tree Search value estimates rather than a single
  evaluator call per node. With GPT-4 it reports a pass at one accuracy of
  94.4 percent on HumanEval, and an exact-match score up to 0.61 on
  HotPotQA question answering, both reported as state of the art among
  prompting and search-based methods at time of publication (results
  reported via https://www.emergentmind.com/papers/2310.04406 summarizing
  the paper's own tables, cross-checked against the arXiv abstract page,
  both verified 2026-08-02).
- **Graph of Thoughts, AAAI 2024.** Maciej Besta, Nils Blach, Ales Kubicek,
  Robert Gerstenberger, and co-authors, "Graph of Thoughts, Solving
  Elaborate Problems with Large Language Models," Proceedings of the AAAI
  Conference on Artificial Intelligence, volume 38, number 16, pages
  17682 through 17690, 2024, DOI 10.1609/aaai.v38i16.29720. The open source
  implementation ships on PyPI as `graph_of_thoughts` and on GitHub at
  https://github.com/spcl/graph-of-thoughts from ETH Zurich, with roughly
  2,800 stars and 217 forks at
  time of writing (verified 2026-08-02). The paper explicitly generalizes
  ToT from a tree to an arbitrary graph of thoughts, and reports the
  framework increases sorting task quality by 62 percent over ToT while
  reducing cost by more than 31 percent, using its own operations-graph
  execution model rather than ToT's fixed tree shape (verified against the
  paper's own abstract, 2026-08-02).

Beyond these three, the Yao paper's own reference implementation,
https://github.com/princeton-nlp/tree-of-thought-llm, is MIT licensed and
carries roughly 6,000 stars at time of writing (verified 2026-08-02). It is
better described as the canonical reference for reproducing the paper's
benchmarks than as a production deployment, but its scale of adoption as a
starting point for derivative work, LATS and Graph of Thoughts both cite it
directly, is itself evidence of the pattern's real, if narrow, footprint.
The honest summary, stated once plainly rather than implied, ToT as Yao
originally formulated it is rare as a shipped, unmodified end-user feature
because of the cost multiplier named in dimension 3, its production
footprint is overwhelmingly as the direct ancestor of, and a named baseline
inside, the newer search-based agent frameworks above, which is a
legitimate but different kind of real-world use than a consumer-facing
chatbot feature.

## 10. Consequences

Positive.

- Materially higher success rate on tasks where an early wrong step is
  otherwise unrecoverable, the paper's own headline number, 4 percent to
  74 percent on Game of 24 with GPT-4, is not a modest improvement, it
  changes a task from mostly failing to mostly succeeding.
- Produces an inspectable trace of alternatives considered and rejected,
  which is useful for debugging why a model reached a particular answer and
  for building trust with a reviewer who wants to see the road not taken,
  not only the road taken.
- Composes cleanly with tool use and external validators, because the
  evaluator step is a first-class extension point, a symbolic checker, a
  unit test runner, or a rule engine can replace or supplement a language
  model's self-judgment, which chain-of-thought's single pass has no
  equivalent slot for.
- Decouples the search strategy from the generation and evaluation
  strategies, so a team can swap breadth-first for depth-first, or a
  scoring evaluator for a voting evaluator, without touching the other two,
  which is a genuine software-engineering benefit over hand-rolled
  multi-step prompting scripts that entangle all three concerns.

Negative.

- A cost multiplier of many times a single pass, several times to over
  twenty times depending on breadth and depth, in both tokens and wall
  clock latency, which rules the pattern out for most synchronous
  user-facing paths, as covered in dimension 4.
- The pattern's benefit is entirely contingent on evaluator quality, and a
  bad evaluator does not merely reduce the gain, it can make the search
  actively worse than a plain greedy chain by confidently discarding the
  correct branch early, exactly as demonstrated in the beam width five run
  in dimension 8.
- Backtracking and re-exploration add real implementation and
  observability surface, a driver, a tree or graph data structure, retry
  and timeout handling around every generation and evaluation call, that a
  single prompt-response call does not need at all.
- Non-determinism across runs is structural, not incidental, temperature
  above zero is required to make sibling thoughts differ from each other,
  which means the same input can legitimately explore a different tree and
  reach a different final answer on repeated runs, a property that is
  awkward to reconcile with reproducibility or regression-testing
  expectations elsewhere in a codebase.

## 11. Failure modes and misuse

- **Symptom.** The system spends far more tokens than a plain chain and
  the success rate does not measurably improve, sometimes it is worse.
  **Cause.** The task does not actually have a checkable intermediate
  signal, so the evaluator is scoring something uncorrelated with true
  progress, essentially adding random noise to the search's pruning
  decisions. **Fix.** Verify the applicability conditions in dimension 4
  before adopting the pattern, and if no genuine mid-solution signal
  exists, fall back to Chain-of-Thought or Self-Consistency, both of which
  do not depend on an intermediate evaluator at all.

- **Symptom.** The search consistently converges on the same wrong answer
  every run despite exploring a tree, as if the tree exploration were not
  happening at all. **Cause.** Generation temperature is set too low, or
  the same prompt template is reused unchanged for every sibling thought
  with no explicit instruction to diversify, so the "different" branches
  are near-duplicates of each other and the search is exploring one path
  many times rather than many paths once. **Fix.** Raise sampling
  temperature for the generation step specifically, distinct from any
  temperature used elsewhere in the pipeline, and, where the model
  supports it, explicitly instruct the generation prompt to avoid repeating
  a previously proposed thought, or pass the already-generated siblings
  back into the prompt as things to differ from.

- **Symptom.** A correct branch is generated early in the search but is
  pruned before it reaches the depth where its correctness becomes visible,
  exactly the beam width five failure reproduced in dimension 8. **Cause.**
  The evaluator judges partial states by comparing them directly against
  the target rather than by their capacity to reach the target, a
  category error, since an intermediate state in a multi-step problem is
  not supposed to resemble the final answer. **Fix.** Give the evaluator
  either a wider lookahead, as the runnable example's one-ply evaluator
  demonstrates only partially fixes the problem, or widen the beam and
  accept the added cost, or replace the deterministic heuristic with the
  model's own judgment of feasibility, which is what the source paper
  actually does, and what a hand-rolled numeric heuristic in a from-scratch
  reimplementation often fails to reproduce faithfully.

- **Symptom.** Runaway cost, a single request triggers what looks like an
  unbounded number of API calls, sometimes discovered only when a billing
  alert fires. **Cause.** No hard limit on total generation or evaluation
  calls, only a per-level beam width or per-branch depth limit, so a task
  with an unexpectedly deep or wide natural decomposition, or a bug that
  produces duplicate thoughts that are never deduplicated, multiplies calls
  beyond what the original sizing anticipated. **Fix.** Enforce a hard cap
  on total calls per search, independent of beam width and depth, that
  aborts and returns the best-so-far state once exceeded, and deduplicate
  generated thoughts by their resulting state, not merely by trace text,
  before they enter the evaluator queue.

- **Symptom.** The pattern is used, but an ablation shows a much cheaper
  method reaches the same accuracy. **Cause.** The task's failure mode
  under plain prompting was actually arithmetic or logical noise across
  independent attempts, not an early wrong step the task's own shape makes unrecoverable,
  which is exactly the case Self-Consistency was designed for and is far
  cheaper to run since it needs no evaluator at all. **Fix.** Before
  committing to a full tree search architecture, benchmark Self-Consistency
  first, per dimension 12, since it is strictly cheaper to build and to run
  and frequently captures most of the available gain on noise-heavy
  tasks.

## 12. Trade-off matrix

| Force | Chain-of-Thought | Self-Consistency | Tree of Thoughts |
|---|---|---|---|
| Recovers from an early wrong step | No, a single committed path | No, votes across independent full paths, cannot fix a shared early error common to most samples | Yes, the reason the pattern exists |
| Relative token cost vs one plain call | About one times | k times, commonly five to forty independent samples | b times d times, commonly five to over twenty, and separate evaluator calls on top |
| Requires an intermediate evaluation signal | No | No | Yes, and the whole pattern degrades without a good one |
| Determinism across repeated runs | High at temperature zero | Low, needs sampling diversity to have any effect | Lowest, needs sampling diversity at every branch point |
| Implementation complexity | One prompt, no external state | One prompt, sample k times, majority vote, no tree | An external driver, a tree or graph structure, a search algorithm, retry and cap logic |
| Best fit | Any task with a linear reasoning path and no real branch point | Tasks where the model is right on the majority of independent tries but noisy on any single try | Tasks where the model is systematically wrong on a fraction of tries because of one identifiable bad decision point that a checkable signal can catch early |
| Reported gain, GPT-4, Game of 24 | 4 percent (https://arxiv.org/abs/2305.10601) | 19 percent, self-consistency with k equal 100 samples, reported in the ToT paper's own ablation table alongside the other two figures cited here (https://arxiv.org/abs/2305.10601) | 45 to 74 percent depending on search configuration, headline figure 74 percent (https://arxiv.org/abs/2305.10601) |

Self-Consistency's own source, Xuezhi Wang, Jason Wei, Dale Schuurmans,
Quoc Le, Ed Chi, Sharan Narang, Aakanksha Chowdhery, and Denny Zhou,
"Self-Consistency Improves Chain of Thought Reasoning in Language Models,"
arXiv 2203.11171, ICLR 2023
(https://arxiv.org/abs/2203.11171, verified 2026-08-02), reports gains of
17.9 points on GSM8K, 11.0 on SVAMP, 12.2 on AQuA, 6.4 on StrategyQA, and
3.9 on ARC-challenge over plain Chain-of-Thought, all on tasks with a much
shallower and noisier failure profile than Game of 24's structural
branch-point failure, which is why the two methods are complementary rather
than strictly ordered, the right first question when a Chain-of-Thought
baseline is failing is whether the errors look like noise, in which case
Self-Consistency is the cheaper fix, or like a specific unrecoverable wrong
turn, in which case Tree of Thoughts is the one that actually addresses the
mechanism.

## 13. Related and incompatible patterns

- **Chain-of-Thought.** ToT's own baseline and, in shape, ToT with
  breadth one, depth equal to the number of reasoning steps, and no
  evaluator or pruning at all. Every ToT implementation needs a working
  Chain-of-Thought prompt for the thought generator step to produce, so the
  two are not alternatives so much as one being an ingredient of the other.
- **Self-Consistency.** A depth-one special case of the tree, as argued in
  dimension 8, sampling k full chains and voting rather than exploring
  intermediate branches. The two compose, a ToT implementation can use
  self-consistency voting, sampling several independent evaluations of the
  same candidate thought and taking the majority, as its evaluator, rather
  than a single evaluator call per node, trading extra evaluation cost for
  a less noisy promise signal.
- **ReAct pattern.** Interleaves reasoning traces with external tool
  actions and their observations in a single linear sequence. ReAct has no
  tree and no backtracking on its own, but Language Agent Tree Search,
  dimension 9, composes ReAct's action-observation loop with ToT's search
  and evaluation machinery, using ReAct actions as the thought-generation
  step and Monte Carlo Tree Search as the search algorithm.
- **Reflection or Self-Refine style patterns.** Iteratively critique and
  revise a single answer rather than exploring parallel alternatives.
  Reflection is linear self-correction on one committed path, ToT is
  parallel exploration of many uncommitted paths, and LATS again shows they
  compose, using reflection on a failed rollout to inform the value
  estimate fed back into the next round of tree search.
- **Monte Carlo Tree Search.** The classical game-tree search algorithm ToT
  borrows its structure from, most directly in the LATS variant. Plain
  Yao-style ToT uses a single evaluator call as its node value, MCTS
  estimates node value via repeated random rollouts to a terminal state,
  which is more statistically grounded and considerably more expensive per
  node.
- **Beam Search.** The token-generation ancestor of ToT's own default search
  strategy. Ordinary beam search operates at the token level within one
  generation call, keeping the top-scoring token sequences as it runs.
  ToT's breadth-first variant applies the identical keep-the-top-b idea one
  level up, at the level of whole thoughts rather than individual tokens,
  which is why the paper's own authors describe ToT as generalizing classic
  search algorithms to operate over language model "thoughts" instead of
  low-level tokens or moves.
- **Plan-and-Solve prompting.** Produces one upfront plan and then executes
  it linearly, with no branching or evaluation of alternative plans. It is
  a cheaper, less reliable neighbor of ToT for tasks whose decomposition is
  usually correct on the first attempt, and a reasonable fallback when
  ToT's cost is not justified but bare Chain-of-Thought under-decomposes
  the task.
- **No hard incompatibilities.** ToT does not conflict mechanically with
  any of the above, its cost is the reason to avoid combining several of
  these simultaneously in one call path, not a structural incompatibility.
  Stacking Self-Consistency voting inside a ToT evaluator inside a
  Reflection loop is architecturally possible and is exactly what several
  of the derivative papers in dimension 9 do, at a cost that compounds
  multiplicatively across every layer added.

## 14. Refactoring path in and out

**Introducing Tree of Thoughts into an existing Chain-of-Thought
pipeline.**

1. Confirm the applicability conditions in dimension 4 hold, in particular
   that a genuine intermediate evaluation signal exists, before writing any
   code. This is the step most implementations skip and it is the single
   biggest predictor of whether the refactor pays off.
2. Identify the thought decomposition already implicit in the existing
   chain-of-thought prompt, the reasoning steps a good chain-of-thought
   response already writes out are almost always the natural thought
   boundaries, so this step is closer to extraction than invention.
3. Extract the single generation call into a `generate(state)` function
   that can be called with different partial states, and make it return
   more than one candidate per call, either by sampling k times at
   temperature above zero or by asking the model to propose several
   options in one structured response.
4. Add an `evaluate(state)` function, starting from the cheapest option
   that could plausibly work, a symbolic checker if the domain has one, or
   a single model call asking for a sure, likely, or impossible rating,
   before reaching for a more elaborate scoring scheme.
5. Wrap the two in a driver loop implementing breadth-first search with a
   small beam width first, two to five is a reasonable starting point,
   before tuning wider. A wider beam is a tuning knob, not an architectural
   decision, and it is far cheaper to widen a working beam-five search than
   to debug a beam-twenty search from scratch.
6. Add a hard cap on total generation and evaluation calls per top-level
   request, from the first version, not as a later hardening pass, per the
   runaway-cost failure mode in dimension 11.
7. Benchmark against the original Chain-of-Thought pipeline and against
   Self-Consistency on the same task and the same held-out set before
   shipping, because dimension 12's trade-off table only tells you which
   method wins in general, not which one wins on this specific task, and
   the source paper's own numbers make clear the gap between methods is
   task-dependent, not universal.

**Removing Tree of Thoughts once it stops earning its place.**

1. Look at the actual explored trees from recent production runs. If the
   overwhelming majority of searches settle on the first or second branch
   generated, at any beam width, the search is not doing useful work
   and the added cost is not buying anything, which is the strongest signal
   that removal is warranted.
2. Collapse the search to Chain-of-Thought first, using the surviving
   winning branch's prompt shape as the new single-pass prompt, as a cheap
   intermediate step and an easy rollback point if evaluation later shows a
   regression.
3. If the earlier benchmark against Self-Consistency in step 7 above showed
   it captured most of the gain at lower cost, land there instead of
   falling all the way back to plain Chain-of-Thought.
4. Remove the driver, the tree data structure, and the evaluator prompt
   only after the simplified pipeline has run in production, side by side
   with the old one behind a flag, long enough to confirm the accuracy
   drop is within the tolerance the team accepted going in, not merely
   within tolerance on the benchmark set used to make the decision.

## 15. Testing and verification

Testing a Tree of Thoughts implementation splits cleanly into testing the
deterministic scaffolding, which is ordinary software, and testing the
model-dependent behavior, which is not.

- **Unit test the generator, evaluator, and search algorithm in isolation,
  with the model call replaced by a stub.** Because the driver, tree
  structure, beam selection, and stopping condition are all plain code with
  no inherent randomness, they are straightforwardly unit-testable exactly
  like the runnable example in dimension 8, feed a fixed set of candidate
  thoughts with fixed evaluator scores and assert the search returns the
  expected surviving branch. This is the highest-value and cheapest test
  layer, and a team that skips it in favor of only testing against a live
  model is testing the flakiest, most expensive part of the system first.
- **Golden-trace regression tests on a small fixed benchmark, at
  temperature zero where the model API allows it.** Even though production
  runs use nonzero temperature for diversity, per dimension 10's
  determinism cost, a temperature-zero regression suite against a handful
  of known-solvable puzzles catches structural regressions, a change to the
  prompt template that breaks parsing, a change to the search algorithm
  that silently changes which branch wins, without depending on sampling
  luck.
- **Property-based tests on the search algorithm's invariants.** The
  frontier after a beam-width prune should never exceed the configured
  beam, the tree should never contain a cycle if the state space is a true
  tree rather than a graph, and the total number of generation calls should
  never exceed the configured hard cap from dimension 11's fix. These
  properties hold regardless of what the model returns, which makes them
  ideal candidates for property-based generation of many random synthetic
  evaluator score distributions.
- **A/B or held-out benchmark comparison against the baseline being
  replaced, on real model calls, before ship.** Because the model-dependent
  behavior cannot be usefully unit tested, the actual accuracy claim
  the pattern is adopted for needs a real evaluation run on a held-out set
  disjoint from any prompt-engineering development set, exactly as
  dimension 14's introduction path requires at step 7, reported as a
  success rate with a sample size large enough that the difference from
  the baseline is not attributable to noise.
- **What ToT makes easier to test, and what it makes harder.** The explicit
  tree of intermediate states, kept as data rather than discarded after use,
  makes it possible to write regression tests against a specific
  intermediate decision point, "given this partial state, the evaluator
  should score branch A above branch B," which a monolithic single-pass
  chain has no equivalent seam for. What it makes harder is overall
  determinism, a full test suite that expects bit-for-bit reproducible
  final answers across runs is fighting the pattern's own sampling
  requirement, and teams that need that guarantee should pin every
  generation call's temperature to zero for the test environment
  specifically, accepting that this configuration does not exercise the
  diversity the production configuration relies on.

## 16. Observability signals

- **Calls per search, broken down by generation calls and evaluation calls
  separately.** This is the single most important metric to graph, because
  it is the direct dollar and latency cost the pattern trades for accuracy,
  and a sudden jump in this number for a fixed beam width and depth
  configuration is the first sign of the runaway-cost failure mode in
  dimension 11, commonly caused by a deduplication regression or a change
  in how many candidates the generation step returns per call.
- **Tree shape per search, depth reached and branching factor actually
  realized at each level.** A healthy search reaches the configured
  maximum depth on most requests and shows genuine variance in the surviving
  branch across similar inputs. A search that consistently reaches only a
  shallow depth before every branch is pruned as impossible, or that always
  collapses to the same single surviving branch regardless of input, is the
  low-diversity failure mode from dimension 11 showing up in aggregate
  telemetry before anyone notices it in an individual trace.
- **Evaluator score distribution across pruned versus kept branches.** If
  pruned and kept branches show heavily overlapping score distributions,
  the evaluator is not discriminating in any useful way between good and bad
  states, which is the leading indicator for the pruned-correct-branch
  failure mode in dimension 11, well before it shows up as a drop in the
  overall success rate metric.
- **Overall success rate against a fixed, versioned benchmark set,
  tracked over time.** Because both the underlying model and the prompt
  templates change over a system's lifetime, a fixed benchmark tracked
  longitudinally is what catches silent regressions that a single point-in
  time evaluation, run once at ship time and never repeated, would miss
  entirely.
- **Wall clock latency per search, and its variance.** DFS-style searches
  in particular have latency that depends heavily on how quickly a losing
  branch is recognized as losing, so latency variance, not merely the
  average, is diagnostic. A search whose ninety-fifth percentile latency
  is many times its median is a search whose evaluator is failing to prune
  bad branches early on a sizable fraction of requests.
- **A healthy dashboard, described plainly.** Calls per search sitting
  close to the configured budget rather than spiking above it, tree depth
  distribution centered near the configured maximum, evaluator score
  distributions for kept versus pruned branches visibly separated rather
  than overlapping, and overall success rate on the fixed benchmark flat
  or improving over time. A failing one shows any of the inverse, calls
  spiking, depth collapsing, score distributions merging, or benchmark
  accuracy drifting down release over release with nobody having changed
  the search configuration on purpose.

## 17. Security and privacy implications

Tree of Thoughts is largely orthogonal to security in the way input
validation or authentication patterns are not, but it does open two
concrete surfaces worth naming rather than leaving silent.

- **Cost-based denial of service.** Because the pattern's own cost is
  variable and driven by how many branches the search chooses to explore,
  an attacker who can influence the input to a ToT-driven endpoint,
  directly or by crafting a prompt injection that convinces the generation
  step to keep proposing plausible-looking but unproductive thoughts, can
  drive up token spend well beyond what a fixed hard cap alone might catch
  if that cap is generous. The mitigation is the same hard call cap named
  in dimension 11's fix, set conservatively per request rather than
  generously, plus rate limiting at the endpoint level independent of the
  search's own internal budget.
- **Prompt injection surface multiplies with the number of generation and
  evaluation calls.** Every additional call to the model on attacker
  influenced content is one more opportunity for an injected instruction
  embedded in a data source the model reads mid-search, a tool result fed
  back into a later thought's prompt in the LATS-style variant, to alter
  the evaluator's judgment or the generator's next proposal. Standard
  prompt-injection mitigations, treating tool and retrieval output as data
  rather than instructions and never concatenating it unescaped into a
  prompt that also carries system-level instructions, apply with more
  force here precisely because there are more injection points per request
  than in a single-pass chain.
- **The explored tree itself can retain sensitive intermediate reasoning
  that never reaches the final answer.** Because the pattern's own
  interpretability benefit, dimension 10, depends on keeping the full tree
  of explored and rejected branches around for inspection, any personal or
  confidential detail the model surfaces in a rejected branch, one that
  would never have appeared in a single committed chain's final output, is
  now sitting in a log or a trace store. Data retention and redaction
  policy for the full tree needs to be considered explicitly rather than
  assumed to inherit the policy already in place for final answers alone.
- **No new implication for data handling at rest or in transit beyond the
  above.** Where the pattern does not open new surface, worth stating
  plainly, it does not change how the model itself was trained, does not
  affect model weight security, and does not introduce a new class of
  data-exfiltration channel beyond the general prompt-injection surface
  named above.

## 18. References

- Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L. Griffiths,
  Yuan Cao, and Karthik Narasimhan, "Tree of Thoughts. Deliberate Problem
  Solving with Large Language Models," arXiv 2305.10601, submitted 17 May
  2023, https://arxiv.org/abs/2305.10601, verified 2026-08-02.
- The same paper's NeurIPS 2023 proceedings record,
  https://proceedings.neurips.cc/paper_files/paper/2023/hash/271db9922b8d1f4dd7aaef84ed5ac703-Abstract-Conference.html,
  verified 2026-08-02.
- Jieyi Long, "Large Language Model Guided Tree-of-Thought,"
  arXiv 2305.08291, submitted 15 May 2023,
  https://arxiv.org/abs/2305.08291, verified 2026-08-02.
- Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei
  Xia, Ed Chi, Quoc V. Le, and Denny Zhou, "Chain-of-Thought Prompting
  Elicits Reasoning in Large Language Models," arXiv 2201.11903, NeurIPS
  2022, https://arxiv.org/abs/2201.11903, verified 2026-08-02.
- Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc Le, Ed Chi, Sharan Narang,
  Aakanksha Chowdhery, and Denny Zhou, "Self-Consistency Improves Chain of
  Thought Reasoning in Language Models," arXiv 2203.11171, ICLR 2023,
  https://arxiv.org/abs/2203.11171, verified 2026-08-02.
- Andy Zhou, Kai Yan, Michal Shlapentokh-Rothman, Haohan Wang, and Yu-Xiong
  Wang, "Language Agent Tree Search Unifies Reasoning, Acting, and Planning
  in Language Models," arXiv 2310.04406, ICML 2024,
  https://arxiv.org/abs/2310.04406, verified 2026-08-02.
- LATS official implementation,
  https://github.com/lapisrocks/LanguageAgentTreeSearch, verified
  2026-08-02.
- Maciej Besta, Nils Blach, Ales Kubicek, Robert Gerstenberger, and
  co-authors, "Graph of Thoughts. Solving Elaborate Problems with Large
  Language Models," Proceedings of the AAAI Conference on Artificial
  Intelligence, volume 38, number 16, 2024, pages 17682 through 17690, DOI
  10.1609/aaai.v38i16.29720, verified against the paper's abstract
  2026-08-02.
- Graph of Thoughts official implementation,
  https://github.com/spcl/graph-of-thoughts, verified 2026-08-02, package
  distributed on PyPI as `graph_of_thoughts`.
- Princeton NLP reference implementation of Tree of Thoughts,
  https://github.com/princeton-nlp/tree-of-thought-llm, MIT licensed,
  verified 2026-08-02.
- LangChain experimental Tree of Thought chain source,
  https://raw.githubusercontent.com/langchain-ai/langchain/v0.1.0/libs/experimental/langchain_experimental/tot/base.py,
  retrieved 2026-08-02.
- `langchain-experimental` package page on PyPI, version 0.4.2, dated 22
  May 2026, noting the package is being sunset,
  https://pypi.org/project/langchain-experimental/, verified 2026-08-02.
