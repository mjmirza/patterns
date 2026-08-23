---
name: Incident-to-Eval Synthesis
slug: incident-to-eval-synthesis
family: 17-ai-agentic
category: AI Agentic
aliases: [Production-to-Eval Loop, Golden Dataset Curation, Failure-Driven Dataset Growth]
first_described: "Braintrust's own Human Review documentation, plus LangSmith's own annotation queue documentation, both current"
maturity: established
related: [golden-dataset, evaluation-suite, llm-as-judge]
incompatible_with: []
verified: 2026-08-23
---

# Incident-to-Eval Synthesis

## 1. Name, aliases, and lineage

Incident-to-eval synthesis is the practice of turning a specific, real
production failure into a permanent, reusable evaluation test case, so the
same mistake is caught automatically the next time a change to the system
risks reintroducing it.

This entry sources it directly from two current, live, independently
operated vendor implementations. Braintrust's own text names the loop
directly. "reviewed production failures become test cases, scorers turn
those cases into metrics, and experiments and CI runs tell you whether a
change improved things or broke something" (Ornella Altunyan, "How to
improve your golden datasets with human review," Braintrust blog,
https://www.braintrust.dev/blog/human-review-golden-datasets, published 21
May 2026, verified 2026-08-23). LangSmith's own text names the same
underlying mechanic from a different product surface. a reviewer can "edit
the run's input and output to create a corrected reference example and
click Add to Dataset" (LangChain, "Use annotation queues," LangSmith
documentation, https://docs.langchain.com/langsmith/annotation-queues,
verified 2026-08-23). Neither vendor's text cites the other, this entry
reports that as a convergently discovered practice rather than one
invented once and copied, the same framing this catalogue's own already
published Golden Dataset entry uses for its own vendor convergence.

## 2. Problem and context

An eval suite built once, at project start, from imagined or synthetic
inputs drifts away from what a system actually gets wrong in production,
and a real failure a user or an operator notices is easy to fix once and
forget, so the exact same class of mistake resurfaces on a later change.
Braintrust's own text names the underlying justification for closing that
gap directly. "if you don't have some validation of what good looks like
for your AI product, then it's impossible to judge whether quality
improved or regressed" (Braintrust, "How to improve your golden datasets
with human review," verified 2026-08-23), and a dataset seeded only from
synthetic cases cannot validate against a failure mode nobody imagined in
advance.

## 3. Forces

Braintrust's own text names the central operational tension directly. "at
any real production scale, you can't get to the labeling step by browsing
every trace yourself" (Braintrust, "How to improve your golden datasets
with human review," verified 2026-08-23), so an automated pre-filtering
step, the same source names a tool called Topics that categorizes traces
"by failure mode, intent, sentiment" before a human ever looks at them, is
required to make the human review step tractable at all. A second named
tension sits inside the review step itself, rubric depth versus
throughput. "long rubrics reduce throughput and increase inconsistency"
(same source), so the reviewer's own judgment quality trades directly
against how many incidents can realistically be triaged.

## 4. Applicability and non-applicability

Braintrust's own text names two concrete non-applicability and misuse
cases directly. "copying traces into a dataset but leaving expected blank"
produces a saved example with no ground truth, which cannot power a
reliable regression test, and mixing "reference material, context, or
rationale directly into expected" "makes comparison across reviewers
difficult and causes noisy scoring" (Braintrust, "How to improve your
golden datasets with human review," verified 2026-08-23). LangSmith's own
text names a structural non-applicability case directly, "thread items do
not support adding to datasets," only individual run items do (LangChain,
"Use annotation queues," verified 2026-08-23), so the mechanism as these
two vendors ship it does not apply to a multi-turn conversation reviewed
as a whole.

## 5. Structure

Braintrust's own text names the pipeline shape directly. "capture behavior
to label with expertise to score in evals to ship, fix, or block"
(Braintrust, "How to improve your golden datasets with human review,"
verified 2026-08-23), and for production scale, the same source names a
three-stage queue structure, a triage queue deciding "ignore vs. needs
review vs. duplicate," a subject-matter-expert queue filling in the ground
truth fields, and a calibration queue where reviewers periodically score
identical items to check agreement.

## 6. ASCII structure diagram

```
  production traffic
        |
        v
  +------------------+
  | automatic         |   grouped by failure mode, intent,
  | trace clustering  |   sentiment, per dimension 3
  +------------------+
        |
        v
  +------------------+
  | triage queue      |   ignore, needs review, or duplicate
  +------------------+
        |
        v
  +------------------+
  | SME review queue  |   fills in the expected ground truth
  +------------------+
        |
        v
  +------------------+
  | golden dataset     |   this catalogue's own separate entry
  +------------------+
        |
        v
  +------------------+
  | scorers and CI     |   ship, fix, or block, per dimension 5
  +------------------+
```

## 7. Dynamics

Braintrust's own text names the runtime consequence of a fed-back dataset
directly, closing the loop through "experiments and CI runs" that "tell
you whether a change improved things or broke something" (Braintrust, "How
to improve your golden datasets with human review," verified 2026-08-23),
so each newly reviewed incident, once labeled, becomes a live regression
check against every future change, not only a record of what once went
wrong. LangSmith's own dynamic runs through the same annotation surface,
"attaching feedback to specific runs or threads" and, for a run item,
promoting that reviewed and corrected example directly into a dataset via
its own named "Add to Dataset" action (LangChain, "Use annotation queues,"
verified 2026-08-23).

## 8. Implementation variants

This entry confirmed two genuinely distinct implementation variants
directly. Braintrust's own Human Review feature, built around named
scorer types, "heuristic scorers" for exact match and regex and schema
checks, and "LLM-as-judge scorers," per dimension 5's pipeline (Braintrust,
"How to improve your golden datasets with human review," verified
2026-08-23), which this catalogue's own already published LLM-as-Judge
entry names as one of its own scoring mechanisms too. LangSmith's own
annotation queue feature, a focused review surface a reviewer works
through item by item, with a distinct rule that only run items, not
threads, support the direct add-to-dataset action, per dimension 4.

## 9. Known production uses

Braintrust's own Human Review and LangSmith's own annotation queues are
each real, currently shipping, actively documented features of two
independently operated, competing eval and observability platforms,
confirmed directly against each vendor's own live documentation under
dimensions 1, 5, and 8.

## 10. Consequences

The benefit is stated directly, already implied under dimension 2 and 7. a
production failure that has been through this loop once becomes a
permanent regression check, so a later change that reintroduces the same
mistake is caught automatically rather than needing to be rediscovered by
another user. the cost is the named structural discipline under dimension
3 and 4, review does not scale to every trace, so a pre-filtering step is
required, and a reviewed example is only as useful as the honesty and
consistency of its filled-in ground truth field, which the same source
names as a real, named failure mode when skipped or polluted.

## 11. Failure modes and misuse

Braintrust's own text names its own sharpest, most directly sourced
failure modes verbatim, already quoted in full under dimension 4, an
expected field left blank produces a saved trace with no usable ground
truth, and an expected field polluted with "reference material, context,
or rationale" rather than the answer itself makes cross-reviewer
comparison noisy. A third named failure mode sits earlier in the process.
"deferred workflow design," waiting to define "the rubric, ownership, and
review cadence" before starting, which the same source names as leading to
"accumulated traces without consistent labeling processes."

## 12. Trade-off matrix

| Dimension | Incident-to-eval synthesis | Synthetic-only upfront eval set |
|---|---|---|
| Coverage of real failure modes | Grows directly from what actually broke, dimension 2 | Limited to what was imagined in advance |
| Scaling to production volume | Needs pre-filtering, dimension 3 | Not applicable, fixed set size |
| Reviewer effort per incident | Bounded rubric, throughput trade-off, dimension 3 | One-time authoring effort |
| Ground truth quality risk | Depends on reviewer discipline, dimension 4 and 11 | Author controls quality directly |
| Freshness over time | Continuously updated, dimension 7 | Static unless manually revisited |

## 13. Related and incompatible patterns

This entry cross-references this catalogue's own already published Golden
Dataset entry directly, per dimension 1 and 6, as the artifact this
pattern's own review pipeline produces and continuously grows, this
catalogue's own already published Evaluation Suite entry, per dimension 7,
as the runner that actually executes the resulting cases against a change,
and this catalogue's own already published LLM-as-Judge entry, per
dimension 8, as one of the named scorer types Braintrust's own pipeline
applies to a reviewed case.

## 14. Refactoring path in and out

Braintrust's own text names the concrete lever for adopting this pattern
directly, already quoted in dimension 5, wiring automatic trace
clustering, a triage queue, and an SME review queue in front of an
existing golden dataset. LangSmith's own equivalent lever, per dimension 6
and 7, is enabling an annotation queue over existing production runs and
using its own named Add to Dataset action on a reviewed run, neither of
which the fetched sources describe as a staged migration, both are direct
feature adoptions on top of an eval pipeline that already exists.

## 15. Testing and verification

Braintrust's own text names the verification mechanic directly, already
quoted in dimension 5 and 7, an experiment or CI run replays the growing
dataset against a candidate change and reports whether it improved things
or broke something. the same source's own named calibration queue, per
dimension 5, is itself a test of the review process rather than of the
system under eval, checking that independent reviewers score an identical
item consistently before that item's label is trusted.

## 16. Observability signals

This entry explicitly checked the fetched sources for a named metric or
dashboard specific to this pattern's own health and did not find one
described on the specific pages fetched. the closest directly sourced
signal is the triage queue's own three-way classification named in
dimension 5, ignore versus needs review versus duplicate, which an
operator could track as a queue-depth and time-to-review signal, and
whether a reviewed item's expected field is populated and unpolluted, per
dimension 4 and 11.

## 17. Security and privacy implications

This entry explicitly checked the fetched sources for a security or
privacy discussion specific to this pattern and did not find one addressed
on the specific pages fetched. this entry reports that absence directly
rather than asserting a security property neither source states. a real
production trace routed into a shared review queue and a durable dataset
does carry whatever sensitive content the original request or response
contained, so the same data-handling discipline that applies to the
production system itself applies to wherever the resulting dataset is
stored.

## 18. References

1. Ornella Altunyan, "How to improve your golden datasets with human
   review," Braintrust blog,
   https://www.braintrust.dev/blog/human-review-golden-datasets, published
   21 May 2026, verified 2026-08-23.
2. LangChain, "Use annotation queues," LangSmith documentation,
   https://docs.langchain.com/langsmith/annotation-queues, verified
   2026-08-23.

## Code

TypeScript, Python, and Go implementations of a minimal incident-triage
queue following the mechanism from dimensions 5 and 6, accepting a flagged
production trace, classifying it as duplicate or needs-review against
already-seen traces, and promoting a filled-in reviewed case into a
growing dataset.

```typescript
interface Trace {
  id: string;
  input: string;
  output: string;
}

interface ReviewedCase extends Trace {
  expected: string;
}

class IncidentTriageQueue {
  private seenInputs: Set<string> = new Set();
  private dataset: ReviewedCase[] = [];

  classify(trace: Trace): "duplicate" | "needs-review" {
    if (this.seenInputs.has(trace.input)) {
      return "duplicate";
    }
    this.seenInputs.add(trace.input);
    return "needs-review";
  }

  promote(trace: Trace, expected: string): void {
    if (expected.trim().length === 0) {
      throw new Error("expected must not be blank, per dimension 4 and 11");
    }
    this.dataset.push({ ...trace, expected });
  }

  datasetSize(): number {
    return this.dataset.length;
  }
}
```

```python
from dataclasses import dataclass
from typing import List, Set


@dataclass
class Trace:
    id: str
    input: str
    output: str


@dataclass
class ReviewedCase(Trace):
    expected: str


class IncidentTriageQueue:
    def __init__(self) -> None:
        self._seen_inputs: Set[str] = set()
        self._dataset: List[ReviewedCase] = []

    def classify(self, trace: Trace) -> str:
        if trace.input in self._seen_inputs:
            return "duplicate"
        self._seen_inputs.add(trace.input)
        return "needs-review"

    def promote(self, trace: Trace, expected: str) -> None:
        if not expected.strip():
            raise ValueError("expected must not be blank, per dimension 4 and 11")
        self._dataset.append(
            ReviewedCase(id=trace.id, input=trace.input, output=trace.output, expected=expected)
        )

    def dataset_size(self) -> int:
        return len(self._dataset)
```

```go
package incidenttriage

import "errors"

type Trace struct {
	ID     string
	Input  string
	Output string
}

type ReviewedCase struct {
	Trace
	Expected string
}

type IncidentTriageQueue struct {
	seenInputs map[string]bool
	dataset    []ReviewedCase
}

func NewIncidentTriageQueue() *IncidentTriageQueue {
	return &IncidentTriageQueue{seenInputs: make(map[string]bool)}
}

func (q *IncidentTriageQueue) Classify(trace Trace) string {
	if q.seenInputs[trace.Input] {
		return "duplicate"
	}
	q.seenInputs[trace.Input] = true
	return "needs-review"
}

func (q *IncidentTriageQueue) Promote(trace Trace, expected string) error {
	if expected == "" {
		return errors.New("expected must not be blank, per dimension 4 and 11")
	}
	q.dataset = append(q.dataset, ReviewedCase{Trace: trace, Expected: expected})
	return nil
}

func (q *IncidentTriageQueue) DatasetSize() int {
	return len(q.dataset)
}
```
