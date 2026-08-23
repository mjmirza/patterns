---
name: Language Agent Tree Search
slug: language-agent-tree-search
family: 17-ai-agentic
category: AI Agentic
aliases: [LATS, MCTS for LLM Agents]
first_described: "Zhou, Yan, Shlapentokh-Rothman, Wang, Wang, arXiv 2310.04406"
maturity: established
related: [tree-of-thoughts]
incompatible_with: []
verified: 2026-08-23
---

# Language Agent Tree Search

## 1. Name, aliases, and lineage

Language Agent Tree Search, LATS, expands an LLM agent's single reasoning
and acting trajectory into a tree, searched with Monte Carlo Tree Search,
so the agent can compare several candidate action sequences and back up
from a dead end instead of committing to the first plausible one.

This entry sources it directly from the paper's own text, fetched live.
"LATS synergizes LM reasoning, acting, and planning strategies by
expanding ReAct into a search over a combinatorial space of possible
reasoning and acting steps" (Andy Zhou, Kai Yan, Michal
Shlapentokh-Rothman, Haohan Wang, Yu-Xiong Wang, "Language Agent Tree
Search Unifies Reasoning Acting and Planning in Language Models," arXiv
2310.04406, https://arxiv.org/abs/2310.04406, verified 2026-08-23).

## 2. Problem and context

The paper's own text names the specific limitation of the prior baseline
directly, ReAct. "existing methods like ReAct are reflexive and fall short
of humans' deliberate and thoughtful decision-making characteristics" and
cannot "consider multiple reasoning paths or plan ahead" (Zhou et al.,
"LATS," verified 2026-08-23). a single, linear reasoning-acting trajectory
commits to its first choice at every step, with no mechanism to compare it
against an alternative or recover once a step turns out to be a mistake.

## 3. Forces

The direct tension the paper names is search breadth against inference
cost, already stated in dimension 1, expanding one trajectory into a
searched tree of many candidate trajectories buys deliberate,
multi-path decision-making, at a computational price the paper states
plainly under dimension 4.

## 4. Applicability and non-applicability

The paper's own text states an explicit cost trade-off that bounds when
LATS is worth using. "LATS has a higher computational cost compared to
simpler prompting methods like ReAct or Reflexion, which may limit its
practicality in certain situations" (Zhou et al., "LATS," verified
2026-08-23), a direct, self-stated non-applicability boundary, tasks where
the extra search budget is not affordable are better served by a cheaper,
single-trajectory method.

## 5. Structure

The paper's own text names six distinct operations that make up the
algorithm, quoted directly. "selection. starting from the root node,
denoted as the initial state, a child node is selected at each tree level
until a leaf node is reached." "expansion. the second operation expands the
tree by sampling n actions... and the environment receives each action and
returns corresponding feedback." "evaluation. the third operation assigns
a scalar value to each new child node for selection and backpropagation."
"simulation. the fourth operation expands the currently selected node
until a terminal state is reached." "backpropagation. this operation
updates the values of the tree based on the outcome of a trajectory."
"reflection. upon encountering an unsuccessful terminal node, the model is
prompted with the trajectory and final reward to provide a verbal
self-reflection" (Zhou et al., "LATS," verified 2026-08-23).

## 6. ASCII structure diagram

```
                     root (initial state)
                          |
              +-----------+-----------+
              |                       |
         selection                selection
        (walk down to a leaf via the tree policy)
              |                       |
         expansion               expansion
        (sample n candidate actions per leaf)
              |                       |
        evaluation              evaluation
       (scalar value per new child node)
              |                       |
        simulation              simulation
       (roll out to a terminal state)
              |                       |
      backpropagation         backpropagation
     (push the outcome back up the tree)
              |                       |
       reflection on            reflection on
       an unsuccessful          an unsuccessful
       terminal node            terminal node
       (verbal self-critique fed into the next round)
```

## 7. Dynamics

Dimension 5 already names the six-step runtime cycle in full, selection,
expansion, evaluation, simulation, backpropagation, reflection. the
reflection step is the mechanism that distinguishes an unsuccessful
branch's failure from a random one, since the model is explicitly prompted
with its own trajectory and the final reward to produce a verbal
self-critique before the next search iteration begins, per the paper's
own text quoted in full under dimension 5.

## 8. Implementation variants

This entry explicitly checked the paper's own fetched text for a second,
independently maintained implementation of this exact six-step algorithm
and did not find one described. the paper positions LATS as a synthesis
of two named prior directions instead, tree search (Monte Carlo Tree
Search) and the ReAct reasoning-acting loop, per dimension 1, rather than
naming a competing implementation of its own specific combination.

## 9. Known production uses

The paper's own text names two concrete benchmark results as its evidence
of real capability, not a production deployment. "state-of-the-art pass@1
accuracy (92.7%) for programming on HumanEval with GPT-4" and competitive
performance on web navigation tasks with GPT-3.5 (Zhou et al., "LATS,"
verified 2026-08-23). this entry explicitly checked for a named,
deployed production system built on LATS and did not find one in the
fetched material, and reports that absence directly.

## 10. Consequences

The benefit is the search itself, already stated in dimension 1 and 2, a
deliberate comparison across multiple candidate trajectories rather than
committing to the first one. the cost is stated directly and plainly,
already quoted in full under dimension 4, a higher computational cost
than ReAct or Reflexion.

## 11. Failure modes and misuse

The paper's own text names the direct misuse case as applying LATS where
its own cost trade-off, per dimension 4, is not worth paying, "in certain
situations" the higher computational cost "may limit its practicality"
(Zhou et al., "LATS," verified 2026-08-23). this entry reports that as the
named failure mode rather than inventing a more elaborate one the paper
does not state.

## 12. Trade-off matrix

| Dimension | Language Agent Tree Search | A single linear ReAct trajectory |
|---|---|---|
| Number of candidate trajectories compared | Many, searched via MCTS, dimension 5 | One |
| Recovery from a bad step | Backpropagation and reflection, dimension 5 and 7 | None, commits to the first choice |
| Computational cost | Higher, explicitly stated, dimension 4 | Lower |
| Benchmark result named | 92.7% pass@1 on HumanEval with GPT-4, dimension 9 | Not the comparison point in the fetched material |
| Practicality for a cheap, simple task | Limited, per the paper's own caveat, dimension 4 | Better fit |

## 13. Related and incompatible patterns

The paper's own text names its two direct lineage inputs by name, already
quoted in dimension 1, ReAct (the reasoning-and-acting loop it expands
into a search) and Monte Carlo Tree Search (the search algorithm it
applies over that expanded space). Reflexion is named directly as one of
the two simpler, cheaper baselines the paper's own cost trade-off in
dimension 4 is measured against. Tree of Thoughts, already published as
its own entry in this catalogue, is named directly as the paper's own
closest prior work, with an explicit, self-stated distinction. "tree-of-
thought (ToT) prompting extends CoT prompting by exploring multiple
reasoning paths over thoughts... our key distinction from ToT is that we
obtain this value after obtaining the environmental feedback, improving
value assignment" (Zhou et al., "LATS," full text, verified 2026-08-23),
naming environment feedback, and unifying reasoning, acting, and planning
together, as what LATS adds on top of ToT's own multi-path search.

## 14. Refactoring path in and out

This entry explicitly checked the paper's own fetched text for a
documented, staged migration from a plain ReAct agent to a LATS-searched
one, or an explicit path back, and did not find either described as a
formal process. the paper frames LATS as expanding ReAct's own single
trajectory into a searched tree, per dimension 1, which structurally
implies the six named operations in dimension 5 are added on top of an
existing reasoning-acting loop rather than replacing it outright, though
the paper itself does not narrate this as a staged migration.

## 15. Testing and verification

The paper's own text names its evidence directly, already quoted in
dimension 9, benchmark accuracy on HumanEval and web navigation tasks.
this entry reports that benchmark result as the paper's own verification
method, a held-out task suite with a scored outcome, rather than a testing
methodology for a specific deployed implementation, since the paper is
reporting a research result, not a shipped tool.

## 16. Observability signals

This entry explicitly checked the paper's own fetched text for a named
runtime metric or dashboard and did not find one described, consistent
with the paper being a research contribution rather than a documented
production system. the closest directly sourced signal is the scalar
value each node receives during the evaluation step, per dimension 5,
which is an internal search signal rather than an external observability
surface.

## 17. Security and privacy implications

This entry explicitly checked the paper's own fetched text for a security
or privacy discussion and did not find one addressed in the fetched
material. this entry reports that absence directly rather than asserting
a security property the paper does not state.

## 18. References

1. Andy Zhou, Kai Yan, Michal Shlapentokh-Rothman, Haohan Wang, Yu-Xiong
   Wang, "Language Agent Tree Search Unifies Reasoning Acting and
   Planning in Language Models," arXiv 2310.04406,
   https://arxiv.org/abs/2310.04406, verified 2026-08-23.
2. Andy Zhou, Kai Yan, Michal Shlapentokh-Rothman, Haohan Wang, Yu-Xiong
   Wang, "Language Agent Tree Search Unifies Reasoning Acting and
   Planning in Language Models," full text, arXiv 2310.04406,
   https://ar5iv.labs.arxiv.org/html/2310.04406, verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of the six-step LATS cycle
following the mechanism from dimension 5, a minimal tree search over
candidate actions with a scalar evaluation and a backpropagated value.

```typescript
interface TreeNode {
  state: string;
  value: number;
  visits: number;
  children: TreeNode[];
  parent: TreeNode | null;
}

function select(node: TreeNode): TreeNode {
  let current = node;
  while (current.children.length > 0) {
    current = current.children.reduce((best, child) =>
      child.value / (child.visits || 1) > best.value / (best.visits || 1) ? child : best
    );
  }
  return current;
}

function expand(node: TreeNode, actions: string[]): void {
  for (const action of actions) {
    node.children.push({ state: action, value: 0, visits: 0, children: [], parent: node });
  }
}

function backpropagate(node: TreeNode, reward: number): void {
  let current: TreeNode | null = node;
  while (current !== null) {
    current.visits += 1;
    current.value += reward;
    current = current.parent;
  }
}
```

```python
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TreeNode:
    state: str
    value: float = 0.0
    visits: int = 0
    children: List["TreeNode"] = field(default_factory=list)
    parent: Optional["TreeNode"] = None


def select(node: TreeNode) -> TreeNode:
    current = node
    while current.children:
        current = max(current.children, key=lambda c: c.value / (c.visits or 1))
    return current


def expand(node: TreeNode, actions: List[str]) -> None:
    for action in actions:
        node.children.append(TreeNode(state=action, parent=node))


def backpropagate(node: TreeNode, reward: float) -> None:
    current: Optional[TreeNode] = node
    while current is not None:
        current.visits += 1
        current.value += reward
        current = current.parent
```

```go
package lats

type TreeNode struct {
	State    string
	Value    float64
	Visits   int
	Children []*TreeNode
	Parent   *TreeNode
}

func Select(node *TreeNode) *TreeNode {
	current := node
	for len(current.Children) > 0 {
		best := current.Children[0]
		bestScore := best.Value / float64(max(best.Visits, 1))
		for _, child := range current.Children[1:] {
			score := child.Value / float64(max(child.Visits, 1))
			if score > bestScore {
				best = child
				bestScore = score
			}
		}
		current = best
	}
	return current
}

func Expand(node *TreeNode, actions []string) {
	for _, action := range actions {
		node.Children = append(node.Children, &TreeNode{State: action, Parent: node})
	}
}

func Backpropagate(node *TreeNode, reward float64) {
	current := node
	for current != nil {
		current.Visits++
		current.Value += reward
		current = current.Parent
	}
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
```
