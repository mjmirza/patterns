---
name: Self-Discover
slug: self-discover
family: 17-ai-agentic
category: AI Agentic
aliases: [SELF-DISCOVER, Self-Composed Reasoning Structures]
first_described: "Zhou, Pujara, Ren, Chen, Cheng, Le, Chi, Zhou, Mishra, Zheng, arXiv 2402.03620"
maturity: established
related: []
incompatible_with: []
verified: 2026-08-23
---

# Self-Discover

## 1. Name, aliases, and lineage

Self-Discover has a language model select, adapt, and compose a small set
of named reasoning modules into an explicit, task-specific reasoning
structure before it attempts to solve a problem, rather than applying one
fixed prompting strategy to every task.

This entry sources it directly from the paper's own text, fetched live.
"we introduce SELF-DISCOVER, a general framework for LLMs to self-discover
the task-intrinsic reasoning structures to tackle complex reasoning
problems that are challenging for typical prompting methods" (Pei Zhou,
Jay Pujara, Xiang Ren, Xinyun Chen, Heng-Tze Cheng, Quoc V. Le, Ed H. Chi,
Denny Zhou, Swaroop Mishra, Huaixiu Steven Zheng, "Self-Discover: Large
Language Models Self-Compose Reasoning Structures," arXiv 2402.03620,
https://arxiv.org/abs/2402.03620, verified 2026-08-23).

## 2. Problem and context

The paper's own text states directly what a fixed, one-size-fits-all
prompting method misses, already implied in dimension 1, a single
reasoning strategy applied uniformly is not tailored to what a specific
task actually needs. "core to the framework is a self-discovery process
where LLMs select multiple atomic reasoning modules such as critical
thinking and step-by-step thinking, and compose them into an explicit
reasoning structure for LLMs to follow during decoding" (Zhou et al.,
"Self-Discover," verified 2026-08-23), naming the gap directly, a generic
prompt is not composed for the task in front of it.

## 3. Forces

The direct tension is between the improvement a task-tailored reasoning
structure provides and the extra inference cost of discovering that
structure in the first place, per dimension 4. the paper's own text names
the specific improvement, "Self-Discover substantially improves GPT-4 and
PaLM 2's performance on challenging reasoning benchmarks such as
BigBench-Hard, grounded agent reasoning, and MATH, by as much as 32%
compared to Chain of Thought" (Zhou et al., "Self-Discover," verified
2026-08-23), against the cost trade named directly in dimension 4.

## 4. Applicability and non-applicability

The paper's own text names an explicit cost caveat that bounds when the
method is worth its own overhead. "Self-Discover input and output are
longer than CoT and Direct prompting, increasing cost" (Zhou et al.,
"Self-Discover," verified 2026-08-23). the paper also reports where its
own gains do NOT come from, an explicit, self-critical finding. "error
analysis reveals that 74.7% of failures stem from computational errors
rather than flawed reasoning structures," meaning the method's own
discovered structure is often correct while the model's own arithmetic
or execution inside that structure is the actual point of failure, a
distinct non-applicability boundary from the cost caveat.

## 5. Structure

The paper's own text names the three stages directly, quoted verbatim.
"SELECT. relevant reasoning modules for task-solving are chosen from the
set of reasoning module descriptions." "ADAPT. descriptions of selected
reasoning modules are rephrased to be more specific to the task at hand."
"IMPLEMENT. the adapted reasoning descriptions are implemented into a
structured actionable plan so that the task can be solved by following the
structure" (Zhou et al., "Self-Discover," verified 2026-08-23). the paper
names a fixed set of 39 atomic reasoning modules the SELECT stage draws
from, including "critical thinking," "break the problem into
sub-problems," "step by step" thinking, "creative thinking," "reflective
thinking," and "systems thinking" (same source).

## 6. ASCII structure diagram

```
  39 named atomic reasoning modules (a fixed library):

  critical thinking | step-by-step | creative thinking |
  reflective thinking | systems thinking | ... (39 total)
                          |
                          v
  +--------------------------------------+
  | SELECT                                |
  | choose the relevant modules for       |
  | THIS task from the library above       |
  +--------------------------------------+
                          |
                          v
  +--------------------------------------+
  | ADAPT                                 |
  | rephrase the chosen modules to be     |
  | specific to THIS task                  |
  +--------------------------------------+
                          |
                          v
  +--------------------------------------+
  | IMPLEMENT                             |
  | compose the adapted modules into an   |
  | explicit, structured, actionable plan |
  +--------------------------------------+
                          |
                          v
             the model follows this
             task-specific structure
             to solve the actual problem
```

## 7. Dynamics

The paper's own text states the runtime cost of the SELECT, ADAPT,
IMPLEMENT sequence directly, in terms of the number of model calls it
needs, already partially quoted in dimension 3. "Self-Discover only
requires one call per instance and three more inference calls on the
task-level, CoT-self-consistency requires 10 times more" (Zhou et al.,
"Self-Discover," verified 2026-08-23), meaning the three-stage discovery
process is a small, fixed, task-level overhead paid once, not repeated
per instance.

## 8. Implementation variants

This entry explicitly checked the paper's own fetched text for a second,
independently maintained implementation of the exact SELECT, ADAPT,
IMPLEMENT sequence and did not find one described. the paper positions
its own method against a named alternative directly, per dimension 3,
CoT-Self-Consistency, as the inference-intensive baseline its own
three-stage discovery process is compared against, rather than naming a
competing implementation of the same self-discovery idea.

## 9. Known production uses

The paper's own text names its evidence as benchmark results, not a
production deployment, already quoted in dimension 3, gains on
BigBench-Hard, grounded agent reasoning, and MATH, tested on GPT-4 and
PaLM 2 and shown to transfer, "the self-discovered reasoning structures
are universally applicable across model families, from PaLM 2-L to GPT-4,
and from GPT-4 to Llama2" (Zhou et al., "Self-Discover," verified
2026-08-23). this entry explicitly checked for a named, deployed
production system and did not find one in the fetched material.

## 10. Consequences

The benefit is stated directly, already quoted in full under dimension 3,
up to a 32 percent improvement over Chain of Thought on the named
benchmarks. the cost is stated with equal directness under dimension 4,
longer input and output than CoT or Direct prompting, and the paper's own
error analysis, also under dimension 4, shows the majority of remaining
failures are computational rather than structural, a second, distinct
consequence, the method narrows one failure class without eliminating
execution errors.

## 11. Failure modes and misuse

The paper's own error analysis, already quoted in full under dimension 4,
is the most directly sourced failure-mode finding, 74.7% of failures are
computational errors rather than a flawed discovered structure. this
entry reports that as the named failure mode, a person expecting
Self-Discover to fix arithmetic or execution mistakes is misapplying what
the paper's own evidence shows it actually improves.

## 12. Trade-off matrix

| Dimension | Self-Discover | Chain-of-Thought-Self-Consistency |
|---|---|---|
| Reasoning structure | Task-tailored, composed from 39 modules, dimension 5 | Fixed, uniform across tasks |
| Inference calls | One per instance plus three task-level, dimension 7 | 10 times more, dimension 7 |
| Reported accuracy gain | Up to 32% over CoT, dimension 3 | The comparison baseline |
| Input and output length | Longer than CoT or Direct, dimension 4 | Shorter per call |
| Remaining failure class | Mostly computational, 74.7%, dimension 4 and 11 | Not the comparison point in the fetched material |

## 13. Related and incompatible patterns

The paper's own text names Chain of Thought and CoT-Self-Consistency as
the two direct comparison baselines throughout, already quoted in
dimensions 3, 7, and 9. this entry explicitly checked the fetched material
for a comparison to a general meta-prompting or prompt-engineering
framework by name beyond these two and did not find one, and reports that
absence directly rather than asserting a broader bridge the paper does
not state.

## 14. Refactoring path in and out

This entry explicitly checked the paper's own fetched text for a
documented, staged migration from a fixed CoT prompt to a Self-Discover
pipeline, or an explicit path back, and did not find either described as
a formal process. the three named stages in dimension 5, SELECT, ADAPT,
IMPLEMENT, are the method's own structure rather than a migration
procedure, and this entry reports that directly.

## 15. Testing and verification

The paper's own text names its evidence directly, already quoted in
dimension 3 and 9, benchmark accuracy on BigBench-Hard, grounded agent
reasoning, and MATH, tested across model families. this entry reports
that benchmark evaluation as the paper's own verification method, a
research result on held-out task suites, rather than a testing
methodology for a specific deployed implementation.

## 16. Observability signals

This entry explicitly checked the paper's own fetched text for a named
runtime metric or dashboard and did not find one described, consistent
with the paper being a research contribution rather than a documented
production system. the closest directly sourced signal is the paper's own
error-attribution breakdown, per dimension 4 and 11, the 74.7% figure,
which is an evaluation artifact rather than an operational observability
surface.

## 17. Security and privacy implications

This entry explicitly checked the paper's own fetched text for a security
or privacy discussion and did not find one addressed in the fetched
material. this entry reports that absence directly rather than asserting
a security property the paper does not state.

## 18. References

1. Pei Zhou, Jay Pujara, Xiang Ren, Xinyun Chen, Heng-Tze Cheng, Quoc V.
   Le, Ed H. Chi, Denny Zhou, Swaroop Mishra, Huaixiu Steven Zheng,
   "Self-Discover: Large Language Models Self-Compose Reasoning
   Structures," arXiv 2402.03620, https://arxiv.org/abs/2402.03620,
   verified 2026-08-23.
2. Pei Zhou et al., "Self-Discover: Large Language Models Self-Compose
   Reasoning Structures," full text, arXiv 2402.03620,
   https://ar5iv.labs.arxiv.org/html/2402.03620, verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of the three-stage SELECT,
ADAPT, IMPLEMENT pipeline following the mechanism from dimension 5,
choosing modules from a fixed library, adapting their descriptions to a
task, and composing them into a structured plan.

```typescript
interface ReasoningModule {
  name: string;
  description: string;
}

function selectModules(task: string, library: ReasoningModule[]): ReasoningModule[] {
  return library.filter((m) => task.toLowerCase().includes(m.name.toLowerCase()));
}

function adaptModules(task: string, selected: ReasoningModule[]): ReasoningModule[] {
  return selected.map((m) => ({ name: m.name, description: m.description + " applied to: " + task }));
}

function implementStructure(adapted: ReasoningModule[]): string {
  return adapted.map((m, i) => (i + 1) + ". " + m.description).join(" ");
}
```

```python
from dataclasses import dataclass
from typing import List


@dataclass
class ReasoningModule:
    name: str
    description: str


def select_modules(task: str, library: List[ReasoningModule]) -> List[ReasoningModule]:
    return [m for m in library if m.name.lower() in task.lower()]


def adapt_modules(task: str, selected: List[ReasoningModule]) -> List[ReasoningModule]:
    return [
        ReasoningModule(name=m.name, description=m.description + " applied to: " + task)
        for m in selected
    ]


def implement_structure(adapted: List[ReasoningModule]) -> str:
    steps = [str(i + 1) + ". " + m.description for i, m in enumerate(adapted)]
    return " ".join(steps)
```

```go
package selfdiscover

import (
	"fmt"
	"strings"
)

type ReasoningModule struct {
	Name        string
	Description string
}

func SelectModules(task string, library []ReasoningModule) []ReasoningModule {
	var selected []ReasoningModule
	for _, m := range library {
		if strings.Contains(strings.ToLower(task), strings.ToLower(m.Name)) {
			selected = append(selected, m)
		}
	}
	return selected
}

func AdaptModules(task string, selected []ReasoningModule) []ReasoningModule {
	adapted := make([]ReasoningModule, len(selected))
	for i, m := range selected {
		adapted[i] = ReasoningModule{Name: m.Name, Description: m.Description + " applied to: " + task}
	}
	return adapted
}

func ImplementStructure(adapted []ReasoningModule) string {
	var steps []string
	for i, m := range adapted {
		steps = append(steps, fmt.Sprintf("%d. %s", i+1, m.Description))
	}
	return strings.Join(steps, " ")
}
```
